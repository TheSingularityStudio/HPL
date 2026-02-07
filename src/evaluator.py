from src.models import *

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

    def execute_function(self, func, local_scope):
        # 执行语句块并返回结果
        return self.execute_block(func.body, local_scope)


    def execute_block(self, block, local_scope):
        for stmt in block.statements:
            result = self.execute_statement(stmt, local_scope)
            # 如果语句返回了值（如return语句），则传播该值
            if result is not None:
                return result
        return None


    def execute_statement(self, stmt, local_scope):
        if isinstance(stmt, AssignmentStatement):
            value = self.evaluate_expression(stmt.expr, local_scope)
            local_scope[stmt.var_name] = value
        elif isinstance(stmt, ReturnStatement):
            # 评估表达式并返回结果
            if stmt.expr:
                return self.evaluate_expression(stmt.expr, local_scope)
            return None

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
        elif isinstance(stmt, EchoStatement):
            message = self.evaluate_expression(stmt.expr, local_scope)
            self.echo(message)
        # 暂时忽略其他类型

    def evaluate_expression(self, expr, local_scope):
        if isinstance(expr, IntegerLiteral):
            return expr.value
        elif isinstance(expr, StringLiteral):
            return expr.value
        elif isinstance(expr, Variable):
            if expr.name in local_scope:
                return local_scope[expr.name]
            elif expr.name in self.global_scope:
                return self.global_scope[expr.name]
            elif expr.name == 'this':
                return self.current_obj
            else:
                raise ValueError(f"Undefined variable {expr.name}")
        elif isinstance(expr, BinaryOp):
            left = self.evaluate_expression(expr.left, local_scope)
            right = self.evaluate_expression(expr.right, local_scope)
            if expr.op == '+':
                # 如果两边都是数字，执行数值加法；否则执行字符串拼接
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left + right
                return str(left) + str(right)

            elif expr.op == '-':
                return left - right
            elif expr.op == '*':
                return left * right
            elif expr.op == '/':
                return left / right
            elif expr.op == '%':
                return left % right
            elif expr.op == '==':
                return left == right
            elif expr.op == '!=':
                return left != right
            elif expr.op == '<':
                return left < right
            elif expr.op == '<=':
                return left <= right
            elif expr.op == '>':
                return left > right
            elif expr.op == '>=':
                return left >= right
            else:
                raise ValueError(f"Unknown operator {expr.op}")
        elif isinstance(expr, FunctionCall):
            if expr.func_name == 'echo':
                message = self.evaluate_expression(expr.args[0], local_scope)
                self.echo(message)
                return None
            else:
                raise ValueError(f"Unknown function {expr.func_name}")
        elif isinstance(expr, MethodCall):
            obj = self.evaluate_expression(expr.obj_name, local_scope)
            if isinstance(obj, HPLObject):
                self.call_method_on_obj(obj, expr.method_name, [self.evaluate_expression(arg, local_scope) for arg in expr.args])
            else:
                raise ValueError(f"Cannot call method on {obj}")
        elif isinstance(expr, PostfixIncrement):
            var_name = expr.var.name
            if var_name in local_scope:
                value = local_scope[var_name]
                local_scope[var_name] = value + 1
                return value
            elif var_name in self.global_scope:
                value = self.global_scope[var_name]
                self.global_scope[var_name] = value + 1
                return value
            else:
                raise ValueError(f"Undefined variable {var_name}")

        else:
            raise ValueError(f"Unknown expression type {type(expr)}")

    def call_method_on_obj(self, obj, method_name, args):
        hpl_class = obj.hpl_class
        if method_name in hpl_class.methods:
            method = hpl_class.methods[method_name]
        elif hpl_class.parent and method_name in self.classes[hpl_class.parent].methods:
            method = self.classes[hpl_class.parent].methods[method_name]
        else:
            raise ValueError(f"Method {method_name} not found")
        # 为'this'设置current_obj
        prev_obj = self.current_obj
        self.current_obj = obj
        self.execute_function(method, {param: args[i] for i, param in enumerate(method.params)})
        self.current_obj = prev_obj

    # 内置函数
    def echo(self, message):
        print(message)
