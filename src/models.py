"""
HPL 数据模型模块 (HPL Models Module)

该模块定义了 HPL 语言解释器中使用的所有数据模型和 AST 节点类。
这些类构成了 HPL 语言的抽象语法树和运行时对象表示。

主要类别：

1. 运行时对象模型：
    - HPLClass: 表示 HPL 类定义，包含类名、方法和父类
    - HPLObject: 表示 HPL 对象实例，包含对象名、所属类和属性
    - HPLFunction: 表示 HPL 函数，包含参数列表和函数体

2. 表达式节点（AST）：
    - Expression: 表达式基类
    - IntegerLiteral: 整数字面量
    - StringLiteral: 字符串字面量
    - BinaryOp: 二元运算表达式
    - Variable: 变量引用
    - FunctionCall: 函数调用
    - MethodCall: 方法调用
    - SuperCall: 父类方法调用
    - PostfixIncrement: 后缀自增表达式

3. 语句节点（AST）：
    - Statement: 语句基类
    - AssignmentStatement: 赋值语句
    - ReturnStatement: 返回语句
    - BlockStatement: 语句块
    - IfStatement: 条件语句
    - ForStatement: 循环语句
    - TryCatchStatement: 异常处理语句
    - EchoStatement: 输出语句
    - IncrementStatement: 自增语句
"""

class HPLClass:

    def __init__(self, name, methods, parents=None):
        self.name = name
        self.methods = methods  # 字典：方法名 -> HPLFunction
        self.parents = parents or []  # 列表：父类名列表

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

class SuperCall(Expression):
    def __init__(self, method_name, args):
        self.method_name = method_name
        self.args = args

class PostfixIncrement(Expression):
    def __init__(self, var):
        self.var = var

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
