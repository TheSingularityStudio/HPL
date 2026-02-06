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



class HPLEvaluator:

    def __init__(self, classes, objects, main_func, call=None):
        self.classes = classes
        self.objects = objects
        self.main_func = main_func
        self.call = call  # call 指令
        self.global_scope = self.objects  # 全局变量，包括预定义对象
        self.current_obj = None  # 用于方法中的'this'


    def run(self):
        # 如果有 call 指令，执行指定的函数
        if self.call:
            self.execute_call()
        # 否则执行 main 函数（向后兼容）
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
        # 执行语句块，捕获返回值
        try:
            self.execute_block(func.body, local_scope)
        except ReturnValue as ret:
            return ret.value


    def execute_block(self, block, local_scope):
        for stmt in block.statements:
            self.execute_statement(stmt, local_scope)

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
                self.execute_block(stmt.then_block, local_scope)
            elif stmt.else_block:
                self.execute_block(stmt.else_block, local_scope)
        elif isinstance(stmt, ForStatement):
            # 初始化
            self.execute_statement(stmt.init, local_scope)
            while self.evaluate_expression(stmt.condition, local_scope):
                self.execute_block(stmt.body, local_scope)
                self.evaluate_expression(stmt.increment_expr, local_scope)
        elif isinstance(stmt, TryCatchStatement):
            try:
                self.execute_block(stmt.try_block, local_scope)
            except Exception as e:
                catch_scope = local_scope.copy()
                catch_scope[stmt.catch_var] = str(e)
                self.execute_block(stmt.catch_block, catch_scope)
        elif isinstance(stmt, FunctionCall):
            self.evaluate_expression(stmt, local_scope)
        elif isinstance(stmt, MethodCall):
            self.evaluate_expression(stmt, local_scope)
        elif isinstance(stmt, SuperCall):
            self.evaluate_expression(stmt, local_scope)
        elif isinstance(stmt, EchoStatement):

            message = self.evaluate_expression(stmt.expr, local_scope)
            self.echo(message)
        elif isinstance(stmt, IncrementStatement):
            if stmt.var_name in local_scope:
                local_scope[stmt.var_name] += 1
            else:
                raise ValueError(f"Undefined variable {stmt.var_name}")
        # 暂时忽略其他类型

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
        elif isinstance(expr, StringLiteral):
            return expr.value
        elif isinstance(expr, Variable):
            return self._check_defined(expr.name, local_scope)

        elif isinstance(expr, BinaryOp):
            left = self.evaluate_expression(expr.left, local_scope)
            right = self.evaluate_expression(expr.right, local_scope)
            if expr.op == '+':
                # 如果两个操作数都是数字，则进行数值加法；否则进行字符串拼接

                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left + right
                else:
                    return str(left) + str(right)
            elif expr.op == '-':
                self._check_numeric_operands(left, right, '-')
                return left - right
            elif expr.op == '*':
                self._check_numeric_operands(left, right, '*')
                return left * right
            elif expr.op == '/':
                self._check_numeric_operands(left, right, '/')
                if right == 0:
                    raise HPLDivisionByZeroError("Division by zero")
                return left / right
            elif expr.op == '%':
                self._check_numeric_operands(left, right, '%')
                if right == 0:
                    raise HPLDivisionByZeroError("Modulo by zero")
                return left % right
            elif expr.op == '==':
                return left == right
            elif expr.op == '!=':
                return left != right
            elif expr.op == '<':
                self._check_numeric_operands(left, right, '<')
                return left < right
            elif expr.op == '<=':
                self._check_numeric_operands(left, right, '<=')
                return left <= right
            elif expr.op == '>':
                self._check_numeric_operands(left, right, '>')
                return left > right
            elif expr.op == '>=':
                self._check_numeric_operands(left, right, '>=')
                return left >= right
            else:
                raise HPLError(f"Unknown operator '{expr.op}'")

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
                return self.call_method_on_obj(obj, expr.method_name, [self.evaluate_expression(arg, local_scope) for arg in expr.args])
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
            if var_name in local_scope:
                value = local_scope[var_name]
                if not isinstance(value, (int, float)):
                    raise HPLTypeError(f"Cannot increment non-numeric value of type {type(value).__name__}")
                local_scope[var_name] = value + 1
                return value
            else:
                raise HPLUndefinedError(f"Undefined variable '{var_name}'")
        elif isinstance(expr, PropertyAccess):
            # 属性访问: obj.property
            obj = self.evaluate_expression(expr.obj_name, local_scope)
            if isinstance(obj, HPLObject):
                if expr.property_name in obj.attributes:
                    return obj.attributes[expr.property_name]
                else:
                    raise HPLUndefinedError(f"Property '{expr.property_name}' not found in object '{obj.name}'")
            else:
                raise HPLTypeError(f"Cannot access property on {type(obj).__name__}, expected HPLObject")
        else:
            raise HPLError(f"Unknown expression type {type(expr).__name__}")



    def call_method_on_obj(self, obj, method_name, args):
        hpl_class = obj.hpl_class
        method = self.find_method_in_class(hpl_class, method_name)
        if not method:
            raise HPLUndefinedError(f"Method '{method_name}' not found in class '{hpl_class.name}'")
        # 为'this'设置current_obj
        prev_obj = self.current_obj
        self.current_obj = obj
        result = self.execute_function(method, {param: args[i] for i, param in enumerate(method.params)})
        self.current_obj = prev_obj
        return result



    def find_method_in_class(self, hpl_class, method_name):
        if method_name in hpl_class.methods:
            return hpl_class.methods[method_name]
        for parent_name in hpl_class.parents:
            parent_class = self.classes[parent_name]
            method = self.find_method_in_class(parent_class, method_name)
            if method:
                return method
        return None

    def find_super_method(self, hpl_class, method_name):
        for parent_name in hpl_class.parents:
            parent_class = self.classes[parent_name]
            method = self.find_method_in_class(parent_class, method_name)
            if method:
                return method
        return None

    # 内置函数
    def echo(self, message):
        print(message)

    def input(self, prompt=None):
        """获取用户输入，可选提示信息"""
        if prompt is not None:
            return input(prompt)
        return input()
