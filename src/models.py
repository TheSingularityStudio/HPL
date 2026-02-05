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

# 示例子类（根据需要扩展）
class BinaryOp(Expression):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Variable(Expression):
    def __init__(self, name):
        self.name = name

class IfStatement(Statement):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class ForStatement(Statement):
    def __init__(self, init, condition, increment, body):
        self.init = init
        self.condition = condition
        self.increment = increment
        self.body = body

class TryCatchStatement(Statement):
    def __init__(self, try_block, catch_var, catch_block):
        self.try_block = try_block
        self.catch_var = catch_var
        self.catch_block = catch_block

class FunctionCall(Expression):
    def __init__(self, func_name, args):
        self.func_name = func_name
        self.args = args

class MethodCall(Expression):
    def __init__(self, obj_name, method_name, args):
        self.obj_name = obj_name
        self.method_name = method_name
        self.args = args
