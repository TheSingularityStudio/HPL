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

from __future__ import annotations
from typing import Any, Optional, Union


class HPLClass:
    def __init__(self, name: str, methods: dict[str, HPLFunction], parent: Optional[str] = None) -> None:

        self.name: str = name
        self.methods: dict[str, HPLFunction] = methods  # 字典：方法名 -> HPLFunction
        self.parent: Optional[str] = parent

class HPLObject:
    def __init__(self, name: str, hpl_class: HPLClass, attributes: Optional[dict[str, Any]] = None) -> None:
        self.name: str = name
        self.hpl_class: HPLClass = hpl_class
        self.attributes: dict[str, Any] = attributes if attributes is not None else {}  # 用于实例变量

class HPLFunction:
    def __init__(self, params: list[str], body: BlockStatement) -> None:
        self.params: list[str] = params  # 参数名列表
        self.body: BlockStatement = body  # 语句列表（待进一步解析）

# 表达式和语句的基类

class Expression:
    def __init__(self, line: Optional[int] = None, column: Optional[int] = None) -> None:
        self.line: Optional[int] = line
        self.column: Optional[int] = column

class Statement:
    def __init__(self, line: Optional[int] = None, column: Optional[int] = None) -> None:
        self.line: Optional[int] = line
        self.column: Optional[int] = column

class ArrowFunction(Expression):
    """箭头函数表达式: () => { ... } 或 (params) => { ... }"""
    def __init__(self, params: list[str], body: BlockStatement, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.params: list[str] = params  # 参数名列表
        self.body: BlockStatement = body  # 函数体（BlockStatement）

# 字面量

class IntegerLiteral(Expression):
    def __init__(self, value: int, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.value: int = value

class FloatLiteral(Expression):
    def __init__(self, value: float, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.value: float = value

class StringLiteral(Expression):
    def __init__(self, value: str, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.value: str = value

class BooleanLiteral(Expression):
    def __init__(self, value: bool, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.value: bool = value

class NullLiteral(Expression):
    def __init__(self, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)

# 表达式

class BinaryOp(Expression):
    def __init__(self, left: Expression, op: str, right: Expression, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.left: Expression = left
        self.op: str = op
        self.right: Expression = right

class Variable(Expression):
    def __init__(self, name: str, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.name: str = name

class FunctionCall(Expression):
    def __init__(self, func_name: Union[str, Variable, Expression], args: list[Expression], line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.func_name: Union[str, Variable, Expression] = func_name
        self.args: list[Expression] = args

class MethodCall(Expression):
    def __init__(self, obj_name: Union[str, Variable, Expression], method_name: str, args: list[Expression], line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.obj_name: Union[str, Variable, Expression] = obj_name
        self.method_name: str = method_name
        self.args: list[Expression] = args

class PropertyAccess(Expression):
    """属性访问表达式: obj.property（不带括号的方法调用）"""
    def __init__(self, obj: Expression, property_name: str, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.obj: Expression = obj  # 对象表达式
        self.property_name: str = property_name  # 属性名

class PostfixIncrement(Expression):
    def __init__(self, var: Union[Variable, ArrayAccess], line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.var: Union[Variable, ArrayAccess] = var

class PrefixIncrement(Expression):
    """前缀自增表达式: ++var"""
    def __init__(self, var: Union[Variable, ArrayAccess], line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.var: Union[Variable, ArrayAccess] = var

class UnaryOp(Expression):

    def __init__(self, op: str, operand: Expression, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.op: str = op
        self.operand: Expression = operand

class ArrayLiteral(Expression):
    def __init__(self, elements: list[Expression], line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.elements: list[Expression] = elements

class ArrayAccess(Expression):
    def __init__(self, array: Expression, index: Expression, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.array: Expression = array
        self.index: Expression = index

class DictionaryLiteral(Expression):
    def __init__(self, pairs: dict[str, Expression], line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.pairs: dict[str, Expression] = pairs  # 字典：键 -> 值表达式

# 语句

class AssignmentStatement(Statement):
    def __init__(self, var_name: str, expr: Expression, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.var_name: str = var_name
        self.expr: Expression = expr

class ArrayAssignmentStatement(Statement):
    def __init__(self, array_name: str, index_expr: Expression, value_expr: Expression, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.array_name: str = array_name
        self.index_expr: Expression = index_expr
        self.value_expr: Expression = value_expr

class ReturnStatement(Statement):
    def __init__(self, expr: Optional[Expression] = None, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.expr: Optional[Expression] = expr

class BlockStatement(Statement):
    def __init__(self, statements: list[Statement], line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.statements: list[Statement] = statements

class ElifClause:
    """elif 子句：条件 + 代码块"""
    def __init__(self, condition: Expression, block: BlockStatement, line: Optional[int] = None, column: Optional[int] = None) -> None:
        self.condition: Expression = condition
        self.block: BlockStatement = block
        self.line: Optional[int] = line
        self.column: Optional[int] = column

class IfStatement(Statement):
    def __init__(self, condition: Expression, then_block: BlockStatement, elif_clauses: Optional[list[ElifClause]] = None, else_block: Optional[BlockStatement] = None, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.condition: Expression = condition
        self.then_block: BlockStatement = then_block
        self.elif_clauses: list[ElifClause] = elif_clauses if elif_clauses is not None else []
        self.else_block: Optional[BlockStatement] = else_block


class ForInStatement(Statement):
    def __init__(self, var_name: str, iterable_expr: Expression, body: BlockStatement, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.var_name: str = var_name      # 循环变量名
        self.iterable_expr: Expression = iterable_expr  # 可迭代对象表达式
        self.body: BlockStatement = body              # 循环体

class WhileStatement(Statement):
    def __init__(self, condition: Expression, body: BlockStatement, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.condition: Expression = condition
        self.body: BlockStatement = body

class CatchClause:
    """单个 catch 子句"""
    def __init__(self, error_type: Optional[str], var_name: str, block: BlockStatement, line: Optional[int] = None, column: Optional[int] = None) -> None:
        self.error_type: Optional[str] = error_type  # 特定错误类型或 None（捕获所有）
        self.var_name: str = var_name      # 异常变量名
        self.block: BlockStatement = block            # catch 块
        self.line: Optional[int] = line
        self.column: Optional[int] = column

class TryCatchStatement(Statement):
    def __init__(self, try_block: BlockStatement, catch_clauses: list[CatchClause], finally_block: Optional[BlockStatement] = None, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.try_block: BlockStatement = try_block
        self.catch_clauses: list[CatchClause] = catch_clauses  # CatchClause 列表
        self.finally_block: Optional[BlockStatement] = finally_block  # 可选的 finally 块

class EchoStatement(Statement):
    def __init__(self, expr: Expression, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.expr: Expression = expr

class IncrementStatement(Statement):
    def __init__(self, var_name: str, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.var_name: str = var_name

class ImportStatement(Statement):
    def __init__(self, module_name: str, alias: Optional[str] = None, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.module_name: str = module_name  # 模块名
        self.alias: Optional[str] = alias  # 别名（可选）

# BreakStatement 和 ContinueStatement 定义在这里，供 ast_parser 使用
class BreakStatement(Statement):
    def __init__(self, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)

class ContinueStatement(Statement):
    def __init__(self, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)

class ThrowStatement(Statement):
    def __init__(self, expr: Optional[Expression] = None, line: Optional[int] = None, column: Optional[int] = None) -> None:
        super().__init__(line, column)
        self.expr: Optional[Expression] = expr  # 要抛出的异常表达式
