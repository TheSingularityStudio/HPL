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

try:
    from src.models import *
    from src.module_loader import load_module, HPLModule
except ImportError:
    from models import *
    from module_loader import load_module, HPLModule



class ReturnValue:
    """包装返回值，用于区分正常执行结果和return语句"""
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    """用于跳出循环"""
    pass


class ContinueException(Exception):
    """用于继续下一次循环"""
    pass


class HPLEvaluator:
    def __init__(self, classes, objects, main_func, call_target=None):
        self.classes = classes
        self.objects = objects
        self.main_func = main_func
        self.call_target = call_target
        self.global_scope = self.objects  # 全局变量，包括预定义对象
        self.current_obj = None  # 用于方法中的'this'
        self.call_stack = []  # 调用栈，用于错误跟踪
        self.imported_modules = {}  # 导入的模块 {alias/name: module}


    def run(self):
        # 如果指定了 call_target，执行对应的函数
        if self.call_target:
            if self.call_target == 'main' and self.main_func:
                self.execute_function(self.main_func, {})
            else:
                raise ValueError(f"Unknown call target: {self.call_target}")
        elif self.main_func:
            self.execute_function(self.main_func, {})

    def execute_function(self, func, local_scope):
        # 执行语句块并返回结果
        result = self.execute_block(func.body, local_scope)
        # 如果是ReturnValue包装器，解包；否则返回原始值（或无返回值）
        if isinstance(result, ReturnValue):
            return result.value
        return result

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
            local_scope[stmt.var_name] = value
        elif isinstance(stmt, ArrayAssignmentStatement):
            # 数组元素赋值：arr[index] = value
            array = self._lookup_variable(stmt.array_name, local_scope)
            if not isinstance(array, list):
                raise TypeError(f"Cannot assign to non-array value: {type(array).__name__}")
            
            index = self.evaluate_expression(stmt.index_expr, local_scope)
            if not isinstance(index, int):
                raise TypeError(f"Array index must be integer, got {type(index).__name__}")
            
            if index < 0 or index >= len(array):
                raise IndexError(f"Array index {index} out of bounds (length: {len(array)})")
            
            value = self.evaluate_expression(stmt.value_expr, local_scope)
            array[index] = value
        elif isinstance(stmt, ReturnStatement):
            # 评估返回值并用ReturnValue包装，以便上层识别
            value = None
            if stmt.expr:
                value = self.evaluate_expression(stmt.expr, local_scope)
            return ReturnValue(value)
        elif isinstance(stmt, IfStatement):
            cond = self.evaluate_expression(stmt.condition, local_scope)
            if cond:
                result = self.execute_block(stmt.then_block, local_scope)
                if isinstance(result, ReturnValue):
                    return result
            elif stmt.else_block:
                result = self.execute_block(stmt.else_block, local_scope)
                if isinstance(result, ReturnValue):
                    return result
        elif isinstance(stmt, ForStatement):
            # 初始化
            self.execute_statement(stmt.init, local_scope)
            while self.evaluate_expression(stmt.condition, local_scope):
                try:
                    result = self.execute_block(stmt.body, local_scope)
                    # 如果是ReturnValue，立即终止循环并向上传播
                    if isinstance(result, ReturnValue):
                        return result
                except BreakException:
                    break
                except ContinueException:
                    pass
                self.evaluate_expression(stmt.increment_expr, local_scope)
        elif isinstance(stmt, WhileStatement):
            while self.evaluate_expression(stmt.condition, local_scope):
                try:
                    result = self.execute_block(stmt.body, local_scope)
                    # 如果是ReturnValue，立即终止循环并向上传播
                    if isinstance(result, ReturnValue):
                        return result
                except BreakException:
                    break
                except ContinueException:
                    pass
        elif isinstance(stmt, BreakStatement):
            raise BreakException()
        elif isinstance(stmt, ContinueStatement):
            raise ContinueException()
        elif isinstance(stmt, TryCatchStatement):
            try:
                result = self.execute_block(stmt.try_block, local_scope)
                # 如果是ReturnValue，向上传播
                if isinstance(result, ReturnValue):
                    return result
            except Exception as e:
                local_scope[stmt.catch_var] = str(e)
                result = self.execute_block(stmt.catch_block, local_scope)
                # 如果是ReturnValue，向上传播
                if isinstance(result, ReturnValue):
                    return result
        elif isinstance(stmt, EchoStatement):
            message = self.evaluate_expression(stmt.expr, local_scope)
            self.echo(message)
        elif isinstance(stmt, ImportStatement):
            self.execute_import(stmt, local_scope)
        elif isinstance(stmt, IncrementStatement):

            # 前缀自增
            value = self._lookup_variable(stmt.var_name, local_scope)
            if not isinstance(value, (int, float)):
                raise TypeError(f"Cannot increment non-numeric value: {type(value).__name__}")
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
        elif isinstance(expr, Variable):
            return self._lookup_variable(expr.name, local_scope)
        elif isinstance(expr, BinaryOp):
            left = self.evaluate_expression(expr.left, local_scope)
            right = self.evaluate_expression(expr.right, local_scope)
            return self._eval_binary_op(left, expr.op, right)
        elif isinstance(expr, UnaryOp):
            operand = self.evaluate_expression(expr.operand, local_scope)
            if expr.op == '!':
                if not isinstance(operand, bool):
                    raise TypeError(f"Logical NOT requires boolean operand, got {type(operand).__name__}")
                return not operand
            else:
                raise ValueError(f"Unknown unary operator {expr.op}")
        elif isinstance(expr, FunctionCall):
            # 内置函数处理
            if expr.func_name == 'echo':
                message = self.evaluate_expression(expr.args[0], local_scope)
                self.echo(message)
                return None
            elif expr.func_name == 'len':
                arg = self.evaluate_expression(expr.args[0], local_scope)
                if isinstance(arg, (list, str)):
                    return len(arg)
                else:
                    raise TypeError(f"len() requires list or string, got {type(arg).__name__}")
            elif expr.func_name == 'int':
                arg = self.evaluate_expression(expr.args[0], local_scope)
                try:
                    return int(arg)
                except (ValueError, TypeError):
                    raise ValueError(f"Cannot convert {arg} to int")
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
                    raise TypeError(f"abs() requires number, got {type(arg).__name__}")
                return abs(arg)
            elif expr.func_name == 'max':
                if len(expr.args) < 1:
                    raise ValueError("max() requires at least one argument")
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                return max(args)
            elif expr.func_name == 'min':
                if len(expr.args) < 1:
                    raise ValueError("min() requires at least one argument")
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                return min(args)
            else:
                raise ValueError(f"Unknown function {expr.func_name}")
        elif isinstance(expr, MethodCall):
            obj = self.evaluate_expression(expr.obj_name, local_scope)
            if isinstance(obj, HPLObject):
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                return self._call_method(obj, expr.method_name, args)
            elif isinstance(obj, HPLModule):
                # 模块函数调用或常量访问
                if len(expr.args) == 0:
                    # 可能是模块常量访问，如 math.PI
                    try:
                        return self.get_module_constant(obj, expr.method_name)
                    except ValueError:
                        # 不是常量，可能是无参函数调用
                        return self.call_module_function(obj, expr.method_name, [])
                else:
                    # 模块函数调用，如 math.sqrt(16)
                    args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                    return self.call_module_function(obj, expr.method_name, args)
            else:
                raise ValueError(f"Cannot call method on {obj}")


        elif isinstance(expr, PostfixIncrement):
            var_name = expr.var.name
            value = self._lookup_variable(var_name, local_scope)
            if not isinstance(value, (int, float)):
                raise TypeError(f"Cannot increment non-numeric value: {type(value).__name__}")
            new_value = value + 1
            self._update_variable(var_name, new_value, local_scope)
            return value
        elif isinstance(expr, ArrayLiteral):
            return [self.evaluate_expression(elem, local_scope) for elem in expr.elements]
        elif isinstance(expr, ArrayAccess):
            array = self.evaluate_expression(expr.array, local_scope)
            index = self.evaluate_expression(expr.index, local_scope)
            if not isinstance(array, list):
                raise TypeError(f"Cannot index non-array value: {type(array).__name__}")
            if not isinstance(index, int):
                raise TypeError(f"Array index must be integer, got {type(index).__name__}")
            if index < 0 or index >= len(array):
                raise IndexError(f"Array index {index} out of bounds (length: {len(array)})")
            return array[index]
        else:
            raise ValueError(f"Unknown expression type {type(expr)}")

    def _eval_binary_op(self, left, op, right):
        # 逻辑运算符
        if op == '&&':
            return left and right
        if op == '||':
            return left or right
        
        # 加法需要特殊处理（字符串拼接 vs 数值相加）
        if op == '+':
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            # 字符串拼接
            return str(left) + str(right)
        
        # 其他算术运算符需要数值操作数
        self._check_numeric_operands(left, right, op)
        
        if op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
        elif op == '%':
            if right == 0:
                raise ZeroDivisionError("Modulo by zero")
            return left % right
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return left < right
        elif op == '<=':
            return left <= right
        elif op == '>':
            return left > right
        elif op == '>=':
            return left >= right
        else:
            raise ValueError(f"Unknown operator {op}")

    def _lookup_variable(self, name, local_scope):
        """统一变量查找逻辑"""
        if name in local_scope:
            return local_scope[name]
        elif name in self.global_scope:
            return self.global_scope[name]
        else:
            raise ValueError(f"Undefined variable: '{name}'")

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
        hpl_class = obj.hpl_class
        if method_name in hpl_class.methods:
            method = hpl_class.methods[method_name]
        elif hpl_class.parent and method_name in self.classes[hpl_class.parent].methods:
            method = self.classes[hpl_class.parent].methods[method_name]
        else:
            raise ValueError(f"Method '{method_name}' not found in class '{hpl_class.name}'")
        
        # 为'this'设置current_obj
        prev_obj = self.current_obj
        self.current_obj = obj
        
        # 创建方法调用的局部作用域
        method_scope = {param: args[i] for i, param in enumerate(method.params) if i < len(args)}
        method_scope['this'] = obj
        
        # 添加到调用栈
        self.call_stack.append(f"{obj.name}.{method_name}()")
        
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
        if '__init__' in hpl_class.methods:
            self._call_method(obj, '__init__', args)
        elif hpl_class.parent and '__init__' in self.classes[hpl_class.parent].methods:
            # 调用父类的构造函数
            parent_class = self.classes[hpl_class.parent]
            if '__init__' in parent_class.methods:
                method = parent_class.methods['__init__']
                prev_obj = self.current_obj
                self.current_obj = obj
                
                method_scope = {param: args[i] for i, param in enumerate(method.params) if i < len(args)}
                method_scope['this'] = obj
                
                self.call_stack.append(f"{obj.name}.__init__()")
                try:
                    self.execute_function(method, method_scope)
                finally:
                    self.call_stack.pop()
                    self.current_obj = prev_obj

    def instantiate_object(self, class_name, obj_name, init_args=None):
        """实例化对象并调用构造函数"""
        if class_name not in self.classes:
            raise ValueError(f"Class '{class_name}' not found")
        
        hpl_class = self.classes[class_name]
        obj = HPLObject(obj_name, hpl_class)
        
        # 调用构造函数（如果存在）
        if init_args is None:
            init_args = []
        self._call_constructor(obj, init_args)
        
        return obj

    def _check_numeric_operands(self, left, right, op):
        """检查操作数是否为数值类型"""
        if not isinstance(left, (int, float)):
            raise TypeError(f"Unsupported operand type for {op}: '{type(left).__name__}' (expected number)")
        if not isinstance(right, (int, float)):
            raise TypeError(f"Unsupported operand type for {op}: '{type(right).__name__}' (expected number)")

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
            raise ImportError(f"Cannot import module '{module_name}': {e}")
        
        raise ImportError(f"Module '{module_name}' not found")

    def call_module_function(self, module, func_name, args):
        """调用模块函数"""
        if isinstance(module, HPLModule):
            return module.call_function(func_name, args)
        raise ValueError(f"Cannot call function on non-module object")

    def get_module_constant(self, module, const_name):
        """获取模块常量"""
        if isinstance(module, HPLModule):
            return module.get_constant(const_name)
        raise ValueError(f"Cannot get constant from non-module object")

    # 内置函数
    def echo(self, message):
        print(message)

