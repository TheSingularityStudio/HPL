"""
HPL 数据模型模块

该模块定义了 HPL 解释器使用的所有数据结构和 AST 节点类型。
包含类、对象、函数的表示，以及各种表达式和语句的节点类。

关键组件：
- HPLClass: 表示 HPL 类定义，包含类名、方法和父类
- HPLObject: 表示 HPL 对象实例，包含对象名、所属类和属性
- HPLFunction: 表示 HPL 函数，包含参数列表和函数体 AST
- 表达式类：IntegerLiteral, StringLiteral, BinaryOp, Variable, FunctionCall, MethodCall, PostfixIncrement
- 语句类：AssignmentStatement, ReturnStatement, BlockStatement, IfStatement, ForStatement, TryCatchStatement, EchoStatement, IncrementStatement
"""

class HPLClass:

    def __init__(self, name, methods, parent=None):
        self.name = name
        self.methods = methods  # 字典：方法名 -> HPLFunction
        self.parent = parent

class HPLObject:
    def __init__(self, name, hpl_class):
        self.name = name
        self.hpl_class = hpl_class
        self.attributes = {}  # 用于实例变量

class HPLFunction:
    def __init__(self, params, body):
        self.params = params  # 参数名列表
        self.body = body  # 语句列表（待进一步解析）

# 表达式和语句的占位符
class Expression:
    pass

class Statement:
    pass

# 字面量
class IntegerLiteral(Expression):
    def __init__(self, value):
        self.value = value

class StringLiteral(Expression):
    def __init__(self, value):
        self.value = value

class BooleanLiteral(Expression):
    def __init__(self, value):
        self.value = value

# 表达式

class BinaryOp(Expression):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Variable(Expression):
    def __init__(self, name):
        self.name = name

class FunctionCall(Expression):
    def __init__(self, func_name, args):
        self.func_name = func_name
        self.args = args

class MethodCall(Expression):
    def __init__(self, obj_name, method_name, args):
        self.obj_name = obj_name
        self.method_name = method_name
        self.args = args

class PostfixIncrement(Expression):
    def __init__(self, var):
        self.var = var

class UnaryOp(Expression):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

# 语句

class AssignmentStatement(Statement):
    def __init__(self, var_name, expr):
        self.var_name = var_name
        self.expr = expr

class ReturnStatement(Statement):
    def __init__(self, expr=None):
        self.expr = expr

class BlockStatement(Statement):
    def __init__(self, statements):
        self.statements = statements

class IfStatement(Statement):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class ForStatement(Statement):
    def __init__(self, init, condition, increment_expr, body):
        self.init = init
        self.condition = condition
        self.increment_expr = increment_expr
        self.body = body

class TryCatchStatement(Statement):
    def __init__(self, try_block, catch_var, catch_block):
        self.try_block = try_block
        self.catch_var = catch_var
        self.catch_block = catch_block

class EchoStatement(Statement):
    def __init__(self, expr):
        self.expr = expr

class IncrementStatement(Statement):
    def __init__(self, var_name):
        self.var_name = var_name
