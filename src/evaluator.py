"""
HPL 求值器模块 (HPL Evaluator Module)

该模块负责执行 HPL 语言的抽象语法树(AST)，实现语言的运行时语义。
它是 HPL 解释器的核心执行引擎，负责管理变量作用域、执行控制流、
处理函数调用和对象方法调用。

主要功能：
    - 表达式求值：支持算术运算、比较运算、逻辑运算
    - 语句执行：支持赋值、条件、循环、异常处理、返回等语句
    - 函数调用：支持函数定义、参数传递、返回值处理
    - 面向对象：支持类方法调用、继承、super 调用
    - 错误处理：提供类型检查、未定义变量检查、除零检查等
    - 作用域管理：支持局部变量和全局变量

异常类：
    - HPLError: HPL 解释器错误的基类
    - HPLTypeError: 类型错误
    - HPLUndefinedError: 未定义变量或方法错误
    - HPLDivisionByZeroError: 除零错误
    - ReturnValue: 用于处理函数返回值的特殊异常
"""

# 处理模块和直接执行的导入

try:
    from src.models import *
except ImportError:
    from models import *


class HPLError(Exception):

    """HPL解释器错误的基类异常"""

    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self._format_message())
    
    def _format_message(self):
        if self.line is not None and self.column is not None:
            return f"HPL Error at line {self.line}, column {self.column}: {self.message}"
        return f"HPL Error: {self.message}"


class HPLTypeError(HPLError):
    """HPL操作中的类型错误"""
    pass



class HPLUndefinedError(HPLError):
    """未定义变量或方法错误"""
    pass



class HPLDivisionByZeroError(HPLError):
    """除以零错误"""
    pass



class ReturnValue(Exception):
    """用于处理函数调用中返回语句的异常"""
    def __init__(self, value):

        self.value = value
        super().__init__()



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

class HPLEvaluator:

    def __init__(self, classes, objects, main_func, call_target=None):
        self.classes = classes
        self.objects = objects
        self.main_func = main_func
        self.call_target = call_target
        self.global_scope = self.objects  # 全局变量，包括预定义对象
        self.current_obj = None  # 用于方法中的'this'


    def run(self):
        # 如果指定了 call_target，执行对应的函数
        if self.call_target:
            if self.call_target == 'main' and self.main_func:
                self.execute_function(self.main_func, {})
            else:
                raise ValueError(f"Unknown call target: {self.call_target}")
        elif self.main_func:
            self.execute_function(self.main_func, {})

    def execute_call(self):
        """执行 call 指令"""
        func_name = self.call['func_name']
        args = self.call['args']
        
        if func_name == 'main' and self.main_func:
            # 执行 main 函数
            self.execute_function(self.main_func, {})
        else:
            raise HPLError(f"Unknown function to call: {func_name}")


    def execute_function(self, func, local_scope):
        # 执行语句块并返回结果
        return self.execute_block(func.body, local_scope)

    def execute_block(self, block, local_scope):
        for stmt in block.statements:
            result = self.execute_statement(stmt, local_scope)
            # 如果语句返回了值（如 ReturnStatement），向上传播
            if result is not None:
                return result
        return None

    def execute_statement(self, stmt, local_scope):
        if isinstance(stmt, AssignmentStatement):
            value = self.evaluate_expression(stmt.expr, local_scope)
            local_scope[stmt.var_name] = value
        elif isinstance(stmt, ReturnStatement):
            # 抛出 ReturnValue 异常来传递返回值
            if stmt.expr:
                value = self.evaluate_expression(stmt.expr, local_scope)
                raise ReturnValue(value)
            else:
                raise ReturnValue(None)

        elif isinstance(stmt, IfStatement):
            cond = self.evaluate_expression(stmt.condition, local_scope)
            if cond:
                return self.execute_block(stmt.then_block, local_scope)
            elif stmt.else_block:
                return self.execute_block(stmt.else_block, local_scope)
        elif isinstance(stmt, ForStatement):
            # 初始化
            self.execute_statement(stmt.init, local_scope)
            while self.evaluate_expression(stmt.condition, local_scope):
                result = self.execute_block(stmt.body, local_scope)
                if result is not None:
                    return result
                self.evaluate_expression(stmt.increment_expr, local_scope)
        elif isinstance(stmt, TryCatchStatement):
            try:
                return self.execute_block(stmt.try_block, local_scope)
            except Exception as e:
                local_scope[stmt.catch_var] = str(e)
                return self.execute_block(stmt.catch_block, local_scope)
        elif isinstance(stmt, EchoStatement):

            message = self.evaluate_expression(stmt.expr, local_scope)
            self.echo(message)
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

    def _check_numeric_operands(self, left, right, op):
        """检查算术运算的操作数是否都是数值类型"""

        if not isinstance(left, (int, float)):
            raise HPLTypeError(f"Left operand of '{op}' must be numeric, got {type(left).__name__}")
        if not isinstance(right, (int, float)):
            raise HPLTypeError(f"Right operand of '{op}' must be numeric, got {type(right).__name__}")
        return True

    def _check_defined(self, name, local_scope):
        """检查变量是否已定义"""

        if name in local_scope:
            return local_scope[name]
        elif name in self.global_scope:
            return self.global_scope[name]
        elif name == 'this':
            return self.current_obj
        else:
            raise HPLUndefinedError(f"Undefined variable '{name}'")

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
            if expr.func_name == 'echo':
                message = self.evaluate_expression(expr.args[0], local_scope)
                self.echo(message)
                return None
            elif expr.func_name == 'input':
                # 支持可选的提示信息参数
                prompt = None
                if expr.args:
                    prompt = self.evaluate_expression(expr.args[0], local_scope)
                return self.input(prompt)
            else:
                raise ValueError(f"Unknown function {expr.func_name}")

        elif isinstance(expr, MethodCall):
            obj = self.evaluate_expression(expr.obj_name, local_scope)
            if isinstance(obj, HPLObject):
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                return self._call_method(obj, expr.method_name, args)
            else:
                raise HPLTypeError(f"Cannot call method on {type(obj).__name__}, expected HPLObject")

        elif isinstance(expr, SuperCall):
            if self.current_obj:
                method = self.find_super_method(self.current_obj.hpl_class, expr.method_name)
                if method:
                    prev_obj = self.current_obj
                    self.current_obj = self.current_obj  # Keep the same 'this'
                    result = self.execute_function(method, {param: self.evaluate_expression(arg, local_scope) for param, arg in zip(method.params, expr.args)})
                    self.current_obj = prev_obj
                    return result
                else:
                    raise HPLUndefinedError(f"Super method '{expr.method_name}' not found")
            else:
                raise HPLError("Super call outside of method context")
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
            raise HPLError(f"Unknown expression type {type(expr).__name__}")



    def _eval_binary_op(self, left, op, right):
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
        method_scope = {param: args[i] for i, param in enumerate(method.params)}
        method_scope['this'] = obj
        
        result = self.execute_function(method, method_scope)
        self.current_obj = prev_obj
        return result

    def _check_numeric_operands(self, left, right, op):
        """检查操作数是否为数值类型"""
        if not isinstance(left, (int, float)):
            raise TypeError(f"Unsupported operand type for {op}: '{type(left).__name__}' (expected number)")
        if not isinstance(right, (int, float)):
            raise TypeError(f"Unsupported operand type for {op}: '{type(right).__name__}' (expected number)")

    # 内置函数
    def echo(self, message):
        print(message)

    def input(self, prompt=None):
        """获取用户输入，可选提示信息"""
        if prompt is not None:
            return input(prompt)
        return input()
