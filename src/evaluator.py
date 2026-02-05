from src.models import *

class HPLEvaluator:
    def __init__(self, classes, objects, main_func):
        self.classes = classes
        self.objects = objects
        self.main_func = main_func
        self.global_scope = {}  # 全局变量
        self.current_obj = None  # 用于方法中的'this'

    def run(self):
        if self.main_func:
            self.execute_function(self.main_func, {})

    def execute_function(self, func, local_scope):
        # 执行语句块
        self.execute_block(func.body, local_scope)

    def execute_block(self, block, local_scope):
        for stmt in block.statements:
            self.execute_statement(stmt, local_scope)

    def execute_statement(self, stmt, local_scope):
        if isinstance(stmt, AssignmentStatement):
            value = self.evaluate_expression(stmt.expr, local_scope)
            local_scope[stmt.var_name] = value
        elif isinstance(stmt, ReturnStatement):
            # 为简单起见，仅评估并暂时忽略
            if stmt.expr:
                return self.evaluate_expression(stmt.expr, local_scope)
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

    def call_method(self, obj_name, method_name, args):
        # 遗留代码，现在未使用
        pass

    # 内置函数
    def echo(self, message):
        print(message)
