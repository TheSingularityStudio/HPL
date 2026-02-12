"""
HPL 代码执行器模块

该模块负责执行解析后的 AST（抽象语法树），是解释器的第三阶段。
包含 HPLEvaluator 类，用于评估表达式、执行语句、管理变量作用域，
以及处理函数调用和方法调用。

关键类：
- HPLEvaluator: 代码执行器，执行 AST 并管理运行时状态

主要功能：
- 表达式评估：二元运算、变量查找、字面量、函数/方法调用
- 语句执行：赋值、条件分支、循环、异常处理、返回
- 作用域管理：局部变量、全局对象、this 绑定
- 内置函数：echo 输出等
"""

import difflib

try:
    from hpl_runtime.core.models import *
    from hpl_runtime.modules.loader import load_module, HPLModule
    from hpl_runtime.utils.exceptions import *
    from hpl_runtime.utils.type_utils import check_numeric_operands, is_hpl_module
    from hpl_runtime.utils.io_utils import echo
except ImportError:
    from hpl_runtime.core.models import *
    from hpl_runtime.modules.loader import load_module, HPLModule
    from hpl_runtime.utils.exceptions import *
    from hpl_runtime.utils.type_utils import check_numeric_operands, is_hpl_module
    from hpl_runtime.utils.io_utils import echo



# 注意：ReturnValue, BreakException, ContinueException 现在从 exceptions 模块导入
# 保留这些别名以保持向后兼容
ReturnValue = HPLReturnValue
BreakException = HPLBreakException
ContinueException = HPLContinueException


class HPLEvaluator:
    def __init__(self, classes, objects, functions=None, main_func=None, call_target=None, call_args=None):
        self.classes = classes
        self.objects = objects
        self.functions = functions or {}  # 所有顶层函数
        self.main_func = main_func
        self.call_target = call_target
        self.call_args = call_args or []  # call 调用的参数

        self.global_scope = self.objects  # 全局变量，包括预定义对象
        self.current_obj = None  # 用于方法中的'this'
        self.call_stack = []  # 调用栈，用于错误跟踪
        self.imported_modules = {}  # 导入的模块 {alias/name: module}


    def run(self):
        # 如果指定了 call_target，执行对应的函数
        if self.call_target:
            # 首先尝试从 functions 字典中查找
            if self.call_target in self.functions:
                target_func = self.functions[self.call_target]
                # 构建参数作用域
                local_scope = {}
                for i, param in enumerate(target_func.params):
                    if i < len(self.call_args):
                        local_scope[param] = self.call_args[i]
                    else:
                        local_scope[param] = None  # 默认值为 None
                self.execute_function(target_func, local_scope, self.call_target)
            elif self.call_target == 'main' and self.main_func:
                self.execute_function(self.main_func, {}, 'main')
            else:
                raise self._create_error(
                    HPLNameError,
                    f"Unknown call target: '{self.call_target}'",
                    error_key='RUNTIME_UNDEFINED_VAR'
                )

        elif self.main_func:
            self.execute_function(self.main_func, {}, 'main')


    def execute_function(self, func, local_scope, func_name=None):
        # 执行语句块并返回结果
        # 添加到调用栈（如果提供了函数名）
        if func_name:
            self.call_stack.append(f"{func_name}()")
        
        try:
            result = self.execute_block(func.body, local_scope)
            # 如果是ReturnValue包装器，解包；否则返回原始值（或无返回值）
            if isinstance(result, ReturnValue):
                return result.value
            return result
        finally:
            # 从调用栈移除
            if func_name:
                self.call_stack.pop()



    def execute_block(self, block, local_scope):
        for stmt in block.statements:
            result = self.execute_statement(stmt, local_scope)
            # 如果语句返回了ReturnValue，立即向上传播（终止执行）
            if isinstance(result, ReturnValue):
                return result
            # 处理 break 和 continue
            if isinstance(result, BreakException):
                raise result
            if isinstance(result, ContinueException):
                raise result
        return None

    def execute_statement(self, stmt, local_scope):
        if isinstance(stmt, AssignmentStatement):
            value = self.evaluate_expression(stmt.expr, local_scope)
            # 检查是否是属性赋值（如 this.name = value）
            if '.' in stmt.var_name:
                obj_name, prop_name = stmt.var_name.split('.', 1)
                # 获取对象
                if obj_name == 'this':
                    obj = local_scope.get('this') or self.current_obj
                else:
                    obj = self._lookup_variable(obj_name, local_scope, stmt.line, stmt.column)

                if isinstance(obj, HPLObject):
                    obj.attributes[prop_name] = value
                else:
                    raise self._create_error(
                        HPLTypeError,
                        f"Cannot set property on non-object value: {type(obj).__name__}",
                        stmt.line, stmt.column,
                        local_scope,
                        error_key='TYPE_MISSING_PROPERTY'
                    )

            else:
                local_scope[stmt.var_name] = value

        elif isinstance(stmt, ArrayAssignmentStatement):
            # 数组元素赋值：arr[index] = value
            # 或者复合赋值：obj.prop[index] = value
            
            # 检查是否是复合属性访问（如 this.exits[direction]）
            if '.' in stmt.array_name:
                # 复合属性数组赋值：obj.prop[index] = value
                obj_name, prop_name = stmt.array_name.split('.', 1)
                
                # 获取对象
                if obj_name == 'this':
                    obj = local_scope.get('this') or self.current_obj
                else:
                    obj = self._lookup_variable(obj_name, local_scope)
                
                if not isinstance(obj, HPLObject):
                    raise self._create_error(
                        HPLTypeError,
                        f"Cannot access property on non-object value: {type(obj).__name__}",
                        error_key='TYPE_MISSING_PROPERTY'
                    )

                
                # 获取属性（应该是数组/字典）
                if prop_name not in obj.attributes:
                    # 如果属性不存在，创建一个空字典
                    obj.attributes[prop_name] = {}
                
                array = obj.attributes[prop_name]
                
                # 计算索引
                index = self.evaluate_expression(stmt.index_expr, local_scope)
                value = self.evaluate_expression(stmt.value_expr, local_scope)
                
                # 支持字典和数组
                if isinstance(array, dict):
                    array[index] = value
                elif isinstance(array, list):
                    if not isinstance(index, int):
                        raise self._create_error(
                            HPLTypeError,
                            f"Array index must be integer, got {type(index).__name__}",
                            error_key='TYPE_INVALID_OPERATION'
                        )
                    if index < 0 or index >= len(array):
                        raise self._create_error(
                            HPLIndexError,
                            f"Array index {index} out of bounds (length: {len(array)})",
                            error_key='RUNTIME_INDEX_OUT_OF_BOUNDS'
                        )

                    array[index] = value
                else:
                    raise self._create_error(
                        HPLTypeError,
                        f"Cannot index non-array and non-dict value: {type(array).__name__}",
                        error_key='TYPE_INVALID_OPERATION'
                    )

            else:
                # 简单数组赋值
                array = self._lookup_variable(stmt.array_name, local_scope)
                if not isinstance(array, list):
                    raise self._create_error(
                        HPLTypeError,
                        f"Cannot assign to non-array value: {type(array).__name__}",
                        error_key='TYPE_INVALID_OPERATION'
                    )

                
                index = self.evaluate_expression(stmt.index_expr, local_scope)
                if not isinstance(index, int):
                    raise self._create_error(
                        HPLTypeError,
                        f"Array index must be integer, got {type(index).__name__}",
                        error_key='TYPE_INVALID_OPERATION'
                    )

                
                if index < 0 or index >= len(array):
                    raise self._create_error(
                        HPLIndexError,
                        f"Array index {index} out of bounds (length: {len(array)})",
                        error_key='RUNTIME_INDEX_OUT_OF_BOUNDS'
                    )

                
                value = self.evaluate_expression(stmt.value_expr, local_scope)
                array[index] = value


        elif isinstance(stmt, ReturnStatement):
            # 评估返回值并用HPLReturnValue包装，以便上层识别
            value = None
            if stmt.expr:
                value = self.evaluate_expression(stmt.expr, local_scope)
            return HPLReturnValue(value)

        elif isinstance(stmt, IfStatement):
            cond = self.evaluate_expression(stmt.condition, local_scope)
            if cond:
                result = self.execute_block(stmt.then_block, local_scope)
                if isinstance(result, HPLReturnValue):
                    return result
            elif stmt.else_block:
                result = self.execute_block(stmt.else_block, local_scope)
                if isinstance(result, HPLReturnValue):
                    return result
        elif isinstance(stmt, ForInStatement):
            # 计算可迭代对象
            iterable = self.evaluate_expression(stmt.iterable_expr, local_scope)
            
            # 根据类型进行迭代
            if isinstance(iterable, list):
                # 数组迭代
                for item in iterable:
                    local_scope[stmt.var_name] = item
                    try:
                        result = self.execute_block(stmt.body, local_scope)
                        if isinstance(result, HPLReturnValue):
                            return result
                    except HPLBreakException:
                        break
                    except HPLContinueException:
                        continue
            elif isinstance(iterable, dict):
                # 字典迭代（遍历键）
                for key in iterable.keys():
                    local_scope[stmt.var_name] = key
                    try:
                        result = self.execute_block(stmt.body, local_scope)
                        if isinstance(result, HPLReturnValue):
                            return result
                    except HPLBreakException:
                        break
                    except HPLContinueException:
                        continue
            elif isinstance(iterable, str):
                # 字符串迭代（遍历字符）
                for char in iterable:
                    local_scope[stmt.var_name] = char
                    try:
                        result = self.execute_block(stmt.body, local_scope)
                        if isinstance(result, HPLReturnValue):
                            return result
                    except HPLBreakException:
                        break
                    except HPLContinueException:
                        continue
            else:
                raise self._create_error(
                    HPLTypeError,
                    f"'{type(iterable).__name__}' object is not iterable",
                    error_key='TYPE_INVALID_OPERATION'
                )



        elif isinstance(stmt, WhileStatement):
            while self.evaluate_expression(stmt.condition, local_scope):
                try:
                    result = self.execute_block(stmt.body, local_scope)
                    # 如果是HPLReturnValue，立即终止循环并向上传播
                    if isinstance(result, HPLReturnValue):
                        return result
                except HPLBreakException:
                    break
                except HPLContinueException:
                    pass

        elif isinstance(stmt, BreakStatement):
            raise HPLBreakException()
        elif isinstance(stmt, ContinueStatement):
            raise HPLContinueException()
        elif isinstance(stmt, ThrowStatement):
            # 评估 throw 表达式并抛出异常
            value = None
            if stmt.expr:
                value = self.evaluate_expression(stmt.expr, local_scope)
            raise self._create_error(
                HPLRuntimeError,
                str(value) if value is not None else "Exception thrown",
                error_key='RUNTIME_GENERAL'
            )

        elif isinstance(stmt, TryCatchStatement):
            caught = False
            error_obj = None
            result = None
            
            try:
                result = self.execute_block(stmt.try_block, local_scope)
                # 如果是HPLReturnValue，向上传播
                if isinstance(result, HPLReturnValue):
                    return result
            except HPLRuntimeError as e:
                error_obj = e
                
                # 尝试匹配特定的 catch 子句
                for catch in stmt.catch_clauses:
                    if self._matches_error_type(e, catch.error_type):
                        # 传递完整错误对象（而不仅是字符串）
                        local_scope[catch.var_name] = error_obj
                        result = self.execute_block(catch.block, local_scope)
                        caught = True
                        if isinstance(result, HPLReturnValue):
                            return result
                        break
                
                if not caught:
                    # 重新抛出未捕获的错误，添加try块位置信息
                    if e.line is None and hasattr(stmt.try_block, 'line'):
                        e.line = stmt.try_block.line
                    raise  # 重新抛出
            except HPLControlFlowException:
                # 控制流异常（break, continue, return）自然传播，不处理
                raise
            finally:
                # 执行 finally 块（如果有）
                if stmt.finally_block:
                    finally_result = self.execute_block(stmt.finally_block, local_scope)
                    # finally 中的 return 会覆盖 try/catch 中的 return
                    if isinstance(finally_result, HPLReturnValue):
                        return finally_result



        elif isinstance(stmt, EchoStatement):
            message = self.evaluate_expression(stmt.expr, local_scope)
            echo(message)

        elif isinstance(stmt, ImportStatement):
            self.execute_import(stmt, local_scope)
        elif isinstance(stmt, IncrementStatement):
            # 前缀自增
            value = self._lookup_variable(stmt.var_name, local_scope)
            if not isinstance(value, (int, float)):
                raise self._create_error(
                    HPLTypeError,
                    f"Cannot increment non-numeric value: {type(value).__name__}",
                    stmt.line, stmt.column,
                    local_scope,
                    error_key='TYPE_INVALID_OPERATION'
                )

            new_value = value + 1
            self._update_variable(stmt.var_name, new_value, local_scope)
        elif isinstance(stmt, BlockStatement):
            return self.execute_block(stmt, local_scope)
        elif isinstance(stmt, Expression):
            # 表达式作为语句
            return self.evaluate_expression(stmt, local_scope)
        return None
    

    def evaluate_expression(self, expr, local_scope):
        if isinstance(expr, IntegerLiteral):
            return expr.value
        elif isinstance(expr, FloatLiteral):
            return expr.value
        elif isinstance(expr, StringLiteral):
            return expr.value
        elif isinstance(expr, BooleanLiteral):
            return expr.value
        elif isinstance(expr, NullLiteral):
            return None

        elif isinstance(expr, Variable):

            return self._lookup_variable(expr.name, local_scope, expr.line, expr.column)
        elif isinstance(expr, BinaryOp):
            left = self.evaluate_expression(expr.left, local_scope)
            right = self.evaluate_expression(expr.right, local_scope)
            return self._eval_binary_op(left, expr.op, right, expr.line, expr.column)

        elif isinstance(expr, UnaryOp):
            operand = self.evaluate_expression(expr.operand, local_scope)
            if expr.op == '!':
                if not isinstance(operand, bool):
                    raise self._create_error(
                        HPLTypeError,
                        f"Logical NOT requires boolean operand, got {type(operand).__name__}",
                        expr.line, expr.column,
                        local_scope,
                        error_key='TYPE_INVALID_OPERATION'
                    )

                return not operand
            else:
                raise self._create_error(
                    HPLRuntimeError,
                    f"Unknown unary operator {expr.op}",
                    expr.line, expr.column,
                    local_scope,
                    error_key='RUNTIME_GENERAL'
                )


        elif isinstance(expr, FunctionCall):
            # 检查是否是类实例化（类名存在于 self.classes 中）
            if expr.func_name in self.classes:
                hpl_class = self.classes[expr.func_name]
                # 实例化对象
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                obj_name = f"__{expr.func_name}_instance_{id(expr)}__"
                return self.instantiate_object(expr.func_name, obj_name, args)
            
            # 内置函数处理
            if expr.func_name == 'echo':


                message = self.evaluate_expression(expr.args[0], local_scope)
                echo(message)
                return None

            elif expr.func_name == 'len':
                arg = self.evaluate_expression(expr.args[0], local_scope)
                if isinstance(arg, (list, str)):
                    return len(arg)
                else:
                    raise self._create_error(
                        HPLTypeError,
                        f"len() requires list or string, got {type(arg).__name__}",
                        error_key='TYPE_INVALID_OPERATION'
                    )


            elif expr.func_name == 'int':
                arg = self.evaluate_expression(expr.args[0], local_scope)
                try:
                    return int(arg)
                except (ValueError, TypeError) as e:
                    arg_type = type(arg).__name__
                    suggestion = ""
                    if arg_type == 'str':
                        suggestion = " (确保字符串只包含数字，如: int(\"42\"))"
                    elif arg_type == 'list':
                        suggestion = " (不能将数组转换为整数)"
                    elif arg_type == 'dict':
                        suggestion = " (不能将字典转换为整数)"
                    elif arg_type == 'NoneType':
                        suggestion = " (变量未初始化，值为 null)"
                    
                    raise self._create_error(
                        HPLTypeError,
                        f"Cannot convert {arg_type} (value: {arg!r}) to int{suggestion}",
                        expr.line, expr.column,
                        local_scope,
                        error_key='TYPE_CONVERSION_FAILED'
                    )



            elif expr.func_name == 'float':
                arg = self.evaluate_expression(expr.args[0], local_scope)
                try:
                    return float(arg)
                except (ValueError, TypeError) as e:
                    arg_type = type(arg).__name__
                    suggestion = ""
                    if arg_type == 'str':
                        suggestion = " (确保字符串是有效的数字格式，如: float(\"3.14\"))"
                    elif arg_type == 'NoneType':
                        suggestion = " (变量未初始化，值为 null)"
                    
                    raise self._create_error(
                        HPLTypeError,
                        f"Cannot convert {arg_type} (value: {arg!r}) to float{suggestion}",
                        expr.line, expr.column,
                        local_scope,
                        error_key='TYPE_CONVERSION_FAILED'
                    )


            elif expr.func_name == 'str':
                arg = self.evaluate_expression(expr.args[0], local_scope)
                return str(arg)

            elif expr.func_name == 'type':
                arg = self.evaluate_expression(expr.args[0], local_scope)
                if isinstance(arg, bool):
                    return 'boolean'
                elif isinstance(arg, int):
                    return 'int'
                elif isinstance(arg, float):
                    return 'float'
                elif isinstance(arg, str):
                    return 'string'
                elif isinstance(arg, list):
                    return 'array'
                elif isinstance(arg, HPLObject):
                    return arg.hpl_class.name
                else:
                    return type(arg).__name__
            elif expr.func_name == 'abs':
                arg = self.evaluate_expression(expr.args[0], local_scope)
                if not isinstance(arg, (int, float)):
                    raise self._create_error(
                        HPLTypeError,
                        f"abs() requires number, got {type(arg).__name__}",
                        error_key='TYPE_INVALID_OPERATION'
                    )

                return abs(arg)

            elif expr.func_name == 'max':
                if len(expr.args) < 1:
                    raise self._create_error(
                        HPLValueError,
                        "max() requires at least one argument",
                        error_key='RUNTIME_GENERAL'
                    )

                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                return max(args)
            elif expr.func_name == 'min':
                if len(expr.args) < 1:
                    raise self._create_error(
                        HPLValueError,
                        "min() requires at least one argument",
                        error_key='RUNTIME_GENERAL'
                    )

                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                return min(args)

            elif expr.func_name == 'range':
                # range 函数实现
                if len(expr.args) < 1 or len(expr.args) > 3:
                    raise self._create_error(
                        HPLValueError,
                        "range() requires 1 to 3 arguments",
                        error_key='RUNTIME_GENERAL'
                    )

                
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                
                # 检查所有参数都是整数
                for arg in args:
                    if not isinstance(arg, int):
                        raise self._create_error(
                            HPLTypeError,
                            f"range() arguments must be integers, got {type(arg).__name__}",
                            error_key='TYPE_INVALID_OPERATION'
                        )

                
                if len(args) == 1:
                    # range(stop) -> 0 到 stop-1
                    return list(range(args[0]))
                elif len(args) == 2:
                    # range(start, stop) -> start 到 stop-1
                    return list(range(args[0], args[1]))
                else:
                    # range(start, stop, step)
                    return list(range(args[0], args[1], args[2]))

            elif expr.func_name == 'input':

                # 获取用户输入
                if len(expr.args) == 0:
                    # 无参数：直接读取输入
                    try:
                        return input()
                    except EOFError:
                        raise self._create_error(
                            HPLIOError,
                            "End of file reached while waiting for input",
                            error_key='IO_READ_ERROR'
                        )

                elif len(expr.args) == 1:
                    # 一个参数：显示提示信息后读取输入
                    prompt = self.evaluate_expression(expr.args[0], local_scope)
                    if not isinstance(prompt, str):
                        raise self._create_error(
                            HPLTypeError,
                            f"input() requires string prompt, got {type(prompt).__name__}",
                            error_key='TYPE_INVALID_OPERATION'
                        )

                    try:
                        return input(prompt)
                    except EOFError:
                        raise self._create_error(
                            HPLIOError,
                            "End of file reached while waiting for input",
                            error_key='IO_READ_ERROR'
                        )

                else:
                    raise self._create_error(
                        HPLValueError,
                        f"input() requires 0 or 1 arguments, got {len(expr.args)}",
                        error_key='RUNTIME_GENERAL'
                    )


            else:
                # 检查是否是用户定义的函数（从include或其他方式导入）
                if expr.func_name in self.functions:
                    # 调用用户定义的函数
                    target_func = self.functions[expr.func_name]
                    args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                    # 构建参数作用域
                    func_scope = {}
                    for i, param in enumerate(target_func.params):
                        if i < len(args):
                            func_scope[param] = args[i]
                        else:
                            func_scope[param] = None  # 默认值为 None
                    return self.execute_function(target_func, func_scope, expr.func_name)
                else:
                    raise self._create_error(
                        HPLNameError,
                        f"Unknown function '{expr.func_name}'",
                        error_key='RUNTIME_UNDEFINED_VAR'
                    )



        elif isinstance(expr, MethodCall):
            obj = self.evaluate_expression(expr.obj_name, local_scope)
            if isinstance(obj, HPLObject):
                # 处理 parent 特殊属性访问
                if expr.method_name == 'parent':
                    if obj.hpl_class.parent and obj.hpl_class.parent in self.classes:
                        parent_class = self.classes[obj.hpl_class.parent]
                        # 如果后面还有调用（如 this.parent.init()），继续处理
                        return parent_class
                    else:
                        raise self._create_error(
                            HPLAttributeError,
                            f"Class '{obj.hpl_class.name}' has no parent class",
                            error_key='TYPE_MISSING_PROPERTY'
                        )

                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                return self._call_method(obj, expr.method_name, args)
            elif isinstance(obj, HPLClass):
                # 处理类方法调用（如父类方法）
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                return self._call_method(obj, expr.method_name, args)
            elif is_hpl_module(obj):

                # 模块函数调用或常量访问
                if len(expr.args) == 0:
                    # 可能是模块常量访问，如 math.PI
                    try:
                        return self.get_module_constant(obj, expr.method_name)
                    except HPLAttributeError:
                        # 不是常量，可能是无参函数调用
                        return self.call_module_function(obj, expr.method_name, [])


                else:
                    # 模块函数调用，如 math.sqrt(16)
                    args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                    return self.call_module_function(obj, expr.method_name, args)
            else:
                raise self._create_error(
                    HPLTypeError,
                    f"Cannot call method on {type(obj).__name__}",
                    error_key='TYPE_INVALID_OPERATION'
                )


        elif isinstance(expr, PostfixIncrement):
            var_name = expr.var.name
            value = self._lookup_variable(var_name, local_scope)
            if not isinstance(value, (int, float)):
                raise self._create_error(
                    HPLTypeError,
                    f"Cannot increment non-numeric value: {type(value).__name__}",
                    error_key='TYPE_INVALID_OPERATION'
                )

            new_value = value + 1
            self._update_variable(var_name, new_value, local_scope)
            return value


        elif isinstance(expr, ArrayLiteral):
            return [self.evaluate_expression(elem, local_scope) for elem in expr.elements]
        elif isinstance(expr, ArrayAccess):
            array = self.evaluate_expression(expr.array, local_scope)
            index = self.evaluate_expression(expr.index, local_scope)

            # 处理字典访问
            if isinstance(array, dict):
                # 字典键检查 - 使用新的 HPLKeyError
                if index not in array:
                    available_keys = list(array.keys())[:10]  # 显示前10个可用键
                    key_type = type(index).__name__

                    # 查找相似键
                    similar_keys = []
                    if available_keys:
                        key_strs = [str(k) for k in available_keys]
                        target_str = str(index)
                        similar = difflib.get_close_matches(target_str, key_strs, n=3, cutoff=0.6)
                        if similar:
                            similar_keys = similar

                    # 构建错误消息
                    parts = [f"Key {index!r} (type: {key_type}) not found in dictionary"]

                    if available_keys:
                        parts.append(f"Available keys: {available_keys}")
                    else:
                        parts.append("Dictionary is empty")

                    if similar_keys:
                        if len(similar_keys) == 1:
                            parts.append(f"Did you mean: '{similar_keys[0]}'?")
                        else:
                            parts.append(f"Similar keys: {', '.join(similar_keys)}")

                    # 键类型建议
                    if isinstance(index, int):
                        str_keys = [k for k in available_keys if isinstance(k, str) and str(index) == k]
                        if str_keys:
                            parts.append(f"Try using string key: '{index}'")
                    elif isinstance(index, str) and index.isdigit():
                        int_keys = [k for k in available_keys if isinstance(k, int) and str(k) == index]
                        if int_keys:
                            parts.append(f"Try using integer key: {int(index)}")

                    # 检查是否是字符串数字的整数键
                    if isinstance(index, str) and index.isdigit():
                        int_key = int(index)
                        if int_key in array:
                            parts.append(f"Key exists as integer: {int_key}")

                    # 检查是否是整数的字符串键
                    if isinstance(index, int):
                        str_key = str(index)
                        if str_key in array:
                            parts.append(f"Key exists as string: '{str_key}'")

                    hint = ". ".join(parts)

                    raise HPLKeyError(
                        hint,
                        line=expr.line,
                        column=expr.column,
                        error_key='RUNTIME_KEY_NOT_FOUND'
                    )

                return array[index]

            # 处理字符串索引访问
            elif isinstance(array, str):
                # 字符串索引类型检查
                if not isinstance(index, int):
                    index_type = type(index).__name__
                    suggestions = []

                    # 智能类型转换建议
                    if isinstance(index, str) and index.isdigit():
                        suggestions.append(f"使用 int() 转换: int('{index}')")
                    elif isinstance(index, float) and index.is_integer():
                        suggestions.append(f"使用 int() 转换: int({index})")
                    elif index is None:
                        suggestions.append("索引不能为 null")
                    else:
                        suggestions.append(f"字符串索引必须是整数，得到的是 {index_type}")

                    hint = f" ({'; '.join(suggestions)})" if suggestions else ""

                    raise self._create_error(
                        HPLTypeError,
                        f"String index must be integer, got {index_type} (value: {index!r}){hint}",
                        expr.line, expr.column,
                        local_scope,
                        error_key='TYPE_INVALID_OPERATION'
                    )

                # 字符串边界检查
                length = len(array)
                if index < 0 or index >= length:
                    suggestions = []

                    if index < 0 and length > 0:
                        reverse_idx = length + index
                        if 0 <= reverse_idx < length:
                            suggestions.append(f"使用正向索引 {reverse_idx} 访问第 {abs(index)} 个字符")

                    if index >= length:
                        suggestions.append(f"字符串长度为 {length}，最大索引是 {length - 1}")

                    if length > 0:
                        suggestions.append(f"有效索引范围: 0 到 {length - 1}")
                    else:
                        suggestions.append("字符串为空")

                    # 字符显示建议
                    if length > 0 and index >= 0:
                        if index < length:
                            char = array[index]
                            suggestions.append(f"该位置的字符是: '{char}'")
                        elif index < length + 5:  # 显示超出范围的字符
                            suggestions.append(f"超出范围，字符串内容: '{array}'")

                    hint = f" ({'; '.join(suggestions)})" if suggestions else ""

                    raise self._create_error(
                        HPLIndexError,
                        f"String index {index} out of bounds (length: {length}){hint}",
                        expr.line, expr.column,
                        local_scope,
                        error_key='RUNTIME_INDEX_OUT_OF_BOUNDS'
                    )

                return array[index]

            # 增强类型检查和错误信息
            if not isinstance(array, list):
                actual_type = type(array).__name__
                hint = ""
                if actual_type == 'dict':
                    hint = " (字典使用键访问，如: dict[key])"
                elif actual_type == 'int':
                    hint = " (数字不可索引)"
                elif actual_type == 'float':
                    hint = " (浮点数不可索引)"
                elif actual_type == 'NoneType':
                    hint = " (变量可能未初始化，为 null)"
                elif actual_type == 'HPLObject':
                    hint = " (对象使用属性访问，如: obj.property)"
                else:
                    hint = f" (类型 {actual_type} 不支持索引操作)"

                raise self._create_error(
                    HPLTypeError,
                    f"Cannot index {actual_type} value{hint}",
                    expr.line, expr.column,
                    local_scope,
                    error_key='TYPE_INVALID_OPERATION'
                )

            # 数组索引类型检查
            if not isinstance(index, int):
                index_type = type(index).__name__
                suggestions = []

                # 智能类型转换建议
                if isinstance(index, str) and index.isdigit():
                    suggestions.append(f"使用 int() 转换: int('{index}')")
                elif isinstance(index, float) and index.is_integer():
                    suggestions.append(f"使用 int() 转换: int({index})")
                elif index is None:
                    suggestions.append("索引不能为 null")
                else:
                    suggestions.append(f"数组索引必须是整数，得到的是 {index_type}")

                hint = f" ({'; '.join(suggestions)})" if suggestions else ""

                raise self._create_error(
                    HPLTypeError,
                    f"Array index must be integer, got {index_type} (value: {index!r}){hint}",
                    expr.line, expr.column,
                    local_scope,
                    error_key='TYPE_INVALID_OPERATION'
                )

            # 增强边界检查
            length = len(array)
            if index < 0 or index >= length:
                suggestions = []

                if index < 0 and length > 0:
                    reverse_idx = length + index
                    if 0 <= reverse_idx < length:
                        suggestions.append(f"使用正向索引 {reverse_idx} 访问倒数第 {abs(index)} 个元素")

                if index >= length:
                    suggestions.append(f"数组长度为 {length}，最大有效索引是 {length - 1}")

                if length > 0:
                    suggestions.append(f"有效索引范围: 0 到 {length - 1}")
                else:
                    suggestions.append("数组为空，无法访问任何索引")

                # 数组内容显示建议
                if length > 0 and index >= 0 and index < length + 3:
                    if index < length:
                        element = array[index]
                        element_type = type(element).__name__
                        suggestions.append(f"该位置的元素是: {element!r} (类型: {element_type})")
                    else:
                        # 显示数组内容
                        if length <= 5:
                            suggestions.append(f"数组内容: {array}")
                        else:
                            suggestions.append(f"数组前5个元素: {array[:5]}")

                hint = f" ({'; '.join(suggestions)})" if suggestions else ""

                raise self._create_error(
                    HPLIndexError,
                    f"Array index {index} out of bounds (length: {length}){hint}",
                    expr.line, expr.column,
                    local_scope,
                    error_key='RUNTIME_INDEX_OUT_OF_BOUNDS'
                )

            return array[index]



        elif isinstance(expr, DictionaryLiteral):
            # 评估字典字面量，计算所有值表达式
            result = {}
            for key, value_expr in expr.pairs.items():
                result[key] = self.evaluate_expression(value_expr, local_scope)
            return result

        else:
            raise self._create_error(
                HPLRuntimeError,
                f"Unknown expression type: {type(expr).__name__}",
                error_key='RUNTIME_GENERAL'
            )




    def _eval_binary_op(self, left, op, right, line=None, column=None):
        # 逻辑运算符
        if op == '&&':
            return left and right
        if op == '||':
            return left or right
        
        # 加法需要特殊处理（数组拼接、字符串拼接 vs 数值相加）
        if op == '+':
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            # 数组拼接
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            # 字符串拼接
            return str(left) + str(right)

        
        # 算术运算符需要数值操作数
        if op in ('-', '*', '/', '%'):
            check_numeric_operands(left, right, op)
        
        if op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                raise self._create_error(
                    HPLDivisionError,
                    "Division by zero. 建议: 添加检查 if (divisor != 0) : result = dividend / divisor",
                    line, column,
                    error_key='RUNTIME_DIVISION_BY_ZERO'
                )

            return left / right
        elif op == '%':
            if right == 0:
                raise self._create_error(
                    HPLDivisionError,
                    "Modulo by zero. 建议: 添加检查 if (divisor != 0) : result = dividend % divisor",
                    line, column,
                    error_key='RUNTIME_DIVISION_BY_ZERO'
                )

            return left % right

        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            check_numeric_operands(left, right, op)
            return left < right
        elif op == '<=':
            check_numeric_operands(left, right, op)
            return left <= right
        elif op == '>':
            check_numeric_operands(left, right, op)
            return left > right
        elif op == '>=':
            check_numeric_operands(left, right, op)
            return left >= right
        else:
            raise self._create_error(
                HPLRuntimeError,
                f"Unknown operator {op}",
                line, column,
                error_key='RUNTIME_GENERAL'
            )






    def _lookup_variable(self, name, local_scope, line=None, column=None):
        """统一变量查找逻辑"""
        if name in local_scope:
            return local_scope[name]
        elif name in self.global_scope:
            return self.global_scope[name]
        else:
            raise self._create_error(
                HPLNameError,
                f"Undefined variable: '{name}'",
                line, column,
                local_scope,
                error_key='RUNTIME_UNDEFINED_VAR'
            )




    def _update_variable(self, name, value, local_scope):
        """统一变量更新逻辑"""
        if name in local_scope:
            local_scope[name] = value
        elif name in self.global_scope:
            self.global_scope[name] = value
        else:
            # 默认创建局部变量
            local_scope[name] = value

    def _call_method(self, obj, method_name, args):
        """统一方法调用逻辑"""
        # 处理父类方法调用（当 obj 是 HPLClass 时）

        if isinstance(obj, HPLClass):
            # 支持 init 作为 __init__ 的别名
            actual_method_name = method_name
            if method_name == 'init' and 'init' not in obj.methods and '__init__' in obj.methods:
                actual_method_name = '__init__'
            if method_name in obj.methods or actual_method_name in obj.methods:
                method = obj.methods.get(method_name) or obj.methods.get(actual_method_name)
                # 父类方法调用时，this 仍然指向当前对象
                method_scope = {param: args[i] for i, param in enumerate(method.params) if i < len(args)}
                method_scope['this'] = self.current_obj
                return self.execute_function(method, method_scope)
            else:
                raise self._create_error(
                    HPLAttributeError,
                    f"Method '{method_name}' not found in parent class '{obj.name}'",
                    error_key='TYPE_MISSING_PROPERTY'
                )

        
        hpl_class = obj.hpl_class
        # 支持 init 作为 __init__ 的别名
        actual_method_name = method_name
        if method_name == 'init' and 'init' not in hpl_class.methods and '__init__' in hpl_class.methods:
            actual_method_name = '__init__'
        
        if method_name in hpl_class.methods:
            method = hpl_class.methods[method_name]
        elif actual_method_name in hpl_class.methods:
            method = hpl_class.methods[actual_method_name]
        elif hpl_class.parent and method_name in self.classes[hpl_class.parent].methods:
            method = self.classes[hpl_class.parent].methods[method_name]
        elif hpl_class.parent and actual_method_name in self.classes[hpl_class.parent].methods:
            method = self.classes[hpl_class.parent].methods[actual_method_name]
        else:
            # 不是方法，尝试作为属性访问
            if method_name in obj.attributes:
                return obj.attributes[method_name]
            raise self._create_error(
                HPLAttributeError,
                f"Method or attribute '{method_name}' not found in class '{hpl_class.name}'",
                error_key='TYPE_MISSING_PROPERTY'
            )



        
        # 为'this'设置current_obj
        prev_obj = self.current_obj
        self.current_obj = obj
        
        # 创建方法调用的局部作用域
        method_scope = {param: args[i] for i, param in enumerate(method.params) if i < len(args)}
        method_scope['this'] = obj
        
        # 添加到调用栈
        # 获取对象名称：HPLObject使用hpl_class.name，HPLClass使用name
        obj_name = obj.hpl_class.name if isinstance(obj, HPLObject) else obj.name
        self.call_stack.append(f"{obj_name}.{method_name}()")
        
        try:
            result = self.execute_function(method, method_scope)
        finally:
            # 从调用栈移除
            self.call_stack.pop()
            self.current_obj = prev_obj
        
        return result


    def _call_constructor(self, obj, args):
        """调用对象的构造函数（如果存在）"""
        hpl_class = obj.hpl_class
        # 支持 init 和 __init__ 作为构造函数名
        constructor_name = None
        if 'init' in hpl_class.methods:
            constructor_name = 'init'
        elif '__init__' in hpl_class.methods:
            constructor_name = '__init__'
        
        if constructor_name:
            self._call_method(obj, constructor_name, args)
        elif hpl_class.parent:
            # 调用父类的构造函数
            parent_class = self.classes[hpl_class.parent]
            parent_constructor_name = None
            if 'init' in parent_class.methods:
                parent_constructor_name = 'init'
            elif '__init__' in parent_class.methods:
                parent_constructor_name = '__init__'
            
            if parent_constructor_name:
                method = parent_class.methods[parent_constructor_name]
                prev_obj = self.current_obj
                self.current_obj = obj
                
                method_scope = {param: args[i] for i, param in enumerate(method.params) if i < len(args)}
                method_scope['this'] = obj
                
                # 获取对象名称
                obj_name = obj.hpl_class.name if isinstance(obj, HPLObject) else obj.name
                self.call_stack.append(f"{obj_name}.{parent_constructor_name}()")


                try:
                    self.execute_function(method, method_scope)
                finally:
                    self.call_stack.pop()
                    self.current_obj = prev_obj


    def instantiate_object(self, class_name, obj_name, init_args=None):
        """实例化对象并调用构造函数"""
        if class_name not in self.classes:
            raise self._create_error(
                HPLNameError,
                f"Class '{class_name}' not found",
                error_key='RUNTIME_UNDEFINED_VAR'
            )
        
        hpl_class = self.classes[class_name]

        obj = HPLObject(obj_name, hpl_class)
        
        # 调用构造函数（如果存在）
        if init_args is None:
            init_args = []
        self._call_constructor(obj, init_args)
        
        return obj




    def execute_import(self, stmt, local_scope):
        """执行 import 语句"""
        module_name = stmt.module_name
        alias = stmt.alias or module_name
        
        try:
            # 加载模块
            module = load_module(module_name)
            if module:
                # 存储模块引用
                self.imported_modules[alias] = module
                local_scope[alias] = module
                return None
        except ImportError as e:
            raise self._create_error(
                HPLImportError,
                f"Cannot import module '{module_name}': {e}",
                error_key='IMPORT_MODULE_NOT_FOUND'
            ) from e
        
        raise self._create_error(
            HPLImportError,
            f"Module '{module_name}' not found",
            error_key='IMPORT_MODULE_NOT_FOUND'
        )




    def call_module_function(self, module, func_name, args):
        """调用模块函数"""
        if is_hpl_module(module):
            return module.call_function(func_name, args)
        raise self._create_error(
            HPLTypeError,
            f"Cannot call function on non-module object",
            error_key='TYPE_INVALID_OPERATION'
        )

    def get_module_constant(self, module, const_name):
        """获取模块常量"""
        if is_hpl_module(module):
            return module.get_constant(const_name)
        raise self._create_error(
            HPLTypeError,
            f"Cannot get constant from non-module object",
            error_key='TYPE_INVALID_OPERATION'
        )



    def _create_error(self, error_class, message, line=None, column=None, 
                    local_scope=None, error_key=None, **kwargs):
        """统一创建错误并添加上下文"""
        # 自动捕获当前调用栈（如果尚未设置）
        call_stack = kwargs.pop('call_stack', None) or self.call_stack.copy()
        
        error = error_class(
            message=message,
            line=line,
            column=column,
            file=getattr(self, 'current_file', None),
            call_stack=call_stack,
            error_key=error_key,
            **kwargs
        )
        
        # 自动丰富上下文
        if local_scope is not None and hasattr(error, 'enrich_context'):
            error.enrich_context(self, local_scope)
        
        return error


    def _matches_error_type(self, error, error_type):
        """检查错误是否匹配指定的错误类型"""

        if error_type is None:
            return True  # 捕获所有错误
        
        # 获取错误类型的类名
        error_class_name = error.__class__.__name__
        
        # 直接匹配类名
        if error_type == error_class_name:
            return True
        
        # 支持不带 HPL 前缀的匹配
        if error_type == error_class_name.replace('HPL', ''):
            return True
        
        # 检查继承关系 - 使用完整的错误类型映射
        error_type_map = {
            # 基础错误
            'HPLError': HPLError,
            'Error': HPLError,
            
            # 语法错误
            'HPLSyntaxError': HPLSyntaxError,
            'SyntaxError': HPLSyntaxError,
            
            # 运行时错误及其子类
            'HPLRuntimeError': HPLRuntimeError,
            'RuntimeError': HPLRuntimeError,
            'HPLTypeError': HPLTypeError,
            'TypeError': HPLTypeError,
            'HPLNameError': HPLNameError,
            'NameError': HPLNameError,
            'HPLAttributeError': HPLAttributeError,
            'AttributeError': HPLAttributeError,
            'HPLIndexError': HPLIndexError,
            'IndexError': HPLIndexError,
            'HPLDivisionError': HPLDivisionError,
            'DivisionError': HPLDivisionError,
            'HPLValueError': HPLValueError,
            'ValueError': HPLValueError,
            'HPLIOError': HPLIOError,
            'IOError': HPLIOError,
            'HPLRecursionError': HPLRecursionError,
            'RecursionError': HPLRecursionError,
            
            # 导入错误
            'HPLImportError': HPLImportError,
            'ImportError': HPLImportError,
        }
        
        target_class = error_type_map.get(error_type)
        if target_class:
            return isinstance(error, target_class)
        
        return False
