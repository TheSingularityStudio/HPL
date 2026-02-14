#!/usr/bin/env python3
"""
HPL AST 模型单元测试

测试核心 AST 模型类：
- HPLClass, HPLFunction, HPLObject
- 各种 Statement 和 Expression 类
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
from hpl_runtime.core.models import (
    # 基础模型
    HPLClass, HPLFunction, HPLObject,
    # 语句
    AssignmentStatement, ArrayAssignmentStatement, ReturnStatement,
    IfStatement, ForInStatement, WhileStatement, TryCatchStatement,
    BreakStatement, ContinueStatement, ThrowStatement, EchoStatement,
    IncrementStatement, ImportStatement, BlockStatement, CatchClause,
    # 表达式
    IntegerLiteral, FloatLiteral, StringLiteral, BooleanLiteral, NullLiteral,
    Variable, BinaryOp, UnaryOp, FunctionCall, MethodCall,
    ArrayLiteral, ArrayAccess, DictionaryLiteral, ArrowFunction, PostfixIncrement
)


class TestHPLClass(unittest.TestCase):
    """测试 HPLClass 类"""

    def test_class_creation(self):
        """测试类创建"""
        cls = HPLClass("TestClass", {"method1": None}, "ParentClass")
        self.assertEqual(cls.name, "TestClass")
        self.assertEqual(cls.parent, "ParentClass")
        self.assertIn("method1", cls.methods)

    def test_class_without_parent(self):
        """测试无父类的类"""
        cls = HPLClass("SimpleClass", {})
        self.assertIsNone(cls.parent)

    def test_class_methods_access(self):
        """测试类方法访问"""
        methods = {
            "init": HPLFunction(["self"], BlockStatement([])),
            "greet": HPLFunction([], BlockStatement([]))
        }
        cls = HPLClass("Person", methods)
        self.assertEqual(len(cls.methods), 2)
        self.assertIn("init", cls.methods)
        self.assertIn("greet", cls.methods)



class TestHPLFunction(unittest.TestCase):
    """测试 HPLFunction 类"""

    def test_function_creation(self):
        """测试函数创建"""
        body = BlockStatement([ReturnStatement(IntegerLiteral(42))])
        func = HPLFunction(["a", "b"], body)
        self.assertEqual(func.params, ["a", "b"])
        self.assertIs(func.body, body)


    def test_function_no_params(self):
        """测试无参数函数"""
        body = BlockStatement([])
        func = HPLFunction([], body)
        self.assertEqual(func.params, [])


    def test_function_repr(self):
        """测试函数字符串表示"""
        body = BlockStatement([])
        func = HPLFunction(["x"], body)
        repr_str = repr(func)
        self.assertIn("HPLFunction", repr_str)



class TestHPLObject(unittest.TestCase):
    """测试 HPLObject 类"""

    def test_object_creation(self):
        """测试对象创建"""
        cls = HPLClass("TestClass", {})
        obj = HPLObject("test_obj", cls)
        self.assertEqual(obj.name, "test_obj")
        self.assertIs(obj.hpl_class, cls)
        self.assertEqual(obj.attributes, {})

    def test_object_with_attributes(self):
        """测试带属性的对象"""
        cls = HPLClass("Person", {})
        obj = HPLObject("person1", cls)
        obj.attributes["name"] = "Alice"
        obj.attributes["age"] = 25
        self.assertEqual(obj.attributes["name"], "Alice")
        self.assertEqual(obj.attributes["age"], 25)

    def test_object_attribute_access(self):
        """测试对象属性访问"""
        cls = HPLClass("Counter", {})
        obj = HPLObject("counter", cls)
        obj.attributes["count"] = 0
        # 修改属性
        obj.attributes["count"] += 1
        self.assertEqual(obj.attributes["count"], 1)


class TestLiterals(unittest.TestCase):
    """测试字面量类"""

    def test_integer_literal(self):
        """测试整数字面量"""
        lit = IntegerLiteral(42, line=1, column=0)
        self.assertEqual(lit.value, 42)
        self.assertEqual(lit.line, 1)
        self.assertEqual(lit.column, 0)

    def test_float_literal(self):
        """测试浮点数字面量"""
        lit = FloatLiteral(3.14, line=2, column=5)
        self.assertEqual(lit.value, 3.14)
        self.assertEqual(lit.line, 2)
        self.assertEqual(lit.column, 5)

    def test_string_literal(self):
        """测试字符串字面量"""
        lit = StringLiteral("hello", line=3, column=10)
        self.assertEqual(lit.value, "hello")
        self.assertEqual(lit.line, 3)

    def test_boolean_literal(self):
        """测试布尔字面量"""
        lit_true = BooleanLiteral(True, line=1, column=0)
        lit_false = BooleanLiteral(False, line=2, column=0)
        self.assertTrue(lit_true.value)
        self.assertFalse(lit_false.value)

    def test_null_literal(self):
        """测试 null 字面量"""
        lit = NullLiteral(line=5, column=0)
        # NullLiteral doesn't have a value attribute, it represents null directly
        self.assertIsNotNone(lit)
        self.assertEqual(lit.line, 5)
        self.assertEqual(lit.column, 0)



class TestVariable(unittest.TestCase):
    """测试 Variable 类"""

    def test_variable_creation(self):
        """测试变量创建"""
        var = Variable("x", line=1, column=0)
        self.assertEqual(var.name, "x")
        self.assertEqual(var.line, 1)
        self.assertEqual(var.column, 0)

    def test_variable_with_position(self):
        """测试带位置的变量"""
        var = Variable("myVar", line=10, column=5)
        self.assertEqual(var.name, "myVar")
        self.assertEqual(var.line, 10)
        self.assertEqual(var.column, 5)


class TestBinaryOp(unittest.TestCase):
    """测试 BinaryOp 类"""

    def test_binary_op_creation(self):
        """测试二元运算创建"""
        left = IntegerLiteral(1)
        right = IntegerLiteral(2)
        op = BinaryOp(left, "+", right, line=1, column=0)
        self.assertEqual(op.op, "+")
        self.assertIs(op.left, left)
        self.assertIs(op.right, right)

    def test_binary_op_operators(self):
        """测试各种运算符"""
        left = IntegerLiteral(1)
        right = IntegerLiteral(2)
        operators = ["+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=", "&&", "||"]
        for op_str in operators:
            op = BinaryOp(left, op_str, right)
            self.assertEqual(op.op, op_str)


class TestUnaryOp(unittest.TestCase):
    """测试 UnaryOp 类"""

    def test_unary_op_creation(self):
        """测试一元运算创建"""
        operand = BooleanLiteral(True)
        op = UnaryOp("!", operand, line=1, column=0)
        self.assertEqual(op.op, "!")
        self.assertIs(op.operand, operand)


class TestFunctionCall(unittest.TestCase):
    """测试 FunctionCall 类"""

    def test_function_call_with_name(self):
        """测试字符串函数名调用"""
        args = [IntegerLiteral(1), IntegerLiteral(2)]
        call = FunctionCall("add", args, line=1, column=0)
        self.assertEqual(call.func_name, "add")
        self.assertEqual(len(call.args), 2)

    def test_function_call_with_variable(self):
        """测试变量函数名调用"""
        var = Variable("myFunc")
        args = [StringLiteral("test")]
        call = FunctionCall(var, args)
        self.assertIsInstance(call.func_name, Variable)


class TestMethodCall(unittest.TestCase):
    """测试 MethodCall 类"""

    def test_method_call(self):
        """测试方法调用"""
        obj = Variable("obj")
        args = [IntegerLiteral(42)]
        call = MethodCall(obj, "method", args, line=1, column=0)
        self.assertIs(call.obj_name, obj)
        self.assertEqual(call.method_name, "method")
        self.assertEqual(len(call.args), 1)


class TestArrayLiteral(unittest.TestCase):
    """测试 ArrayLiteral 类"""

    def test_empty_array(self):
        """测试空数组"""
        arr = ArrayLiteral([])
        self.assertEqual(arr.elements, [])

    def test_array_with_elements(self):
        """测试带元素的数组"""
        elements = [IntegerLiteral(1), IntegerLiteral(2), IntegerLiteral(3)]
        arr = ArrayLiteral(elements)
        self.assertEqual(len(arr.elements), 3)


class TestArrayAccess(unittest.TestCase):
    """测试 ArrayAccess 类"""

    def test_array_access(self):
        """测试数组访问"""
        arr = Variable("myArray")
        index = IntegerLiteral(0)
        access = ArrayAccess(arr, index, line=1, column=0)
        self.assertIs(access.array, arr)
        self.assertIs(access.index, index)


class TestDictionaryLiteral(unittest.TestCase):
    """测试 DictionaryLiteral 类"""

    def test_empty_dictionary(self):
        """测试空字典"""
        dic = DictionaryLiteral({})
        self.assertEqual(dic.pairs, {})

    def test_dictionary_with_pairs(self):
        """测试带键值对的字典"""
        pairs = {
            "name": StringLiteral("Alice"),
            "age": IntegerLiteral(25)
        }
        dic = DictionaryLiteral(pairs)
        self.assertEqual(len(dic.pairs), 2)
        self.assertIn("name", dic.pairs)
        self.assertIn("age", dic.pairs)


class TestArrowFunction(unittest.TestCase):
    """测试 ArrowFunction 类"""

    def test_arrow_function_no_params(self):
        """测试无参数箭头函数"""
        body = BlockStatement([ReturnStatement(IntegerLiteral(42))])
        arrow = ArrowFunction([], body, line=1, column=0)
        self.assertEqual(arrow.params, [])
        self.assertIs(arrow.body, body)

    def test_arrow_function_with_params(self):
        """测试带参数箭头函数"""
        body = BlockStatement([ReturnStatement(Variable("x"))])
        arrow = ArrowFunction(["x", "y"], body, line=1, column=0)
        self.assertEqual(arrow.params, ["x", "y"])


class TestPostfixIncrement(unittest.TestCase):
    """测试 PostfixIncrement 类"""

    def test_postfix_increment(self):
        """测试后缀自增"""
        var = Variable("x")
        inc = PostfixIncrement(var, line=1, column=0)
        self.assertIs(inc.var, var)


class TestStatements(unittest.TestCase):
    """测试语句类"""

    def test_assignment_statement(self):
        """测试赋值语句"""
        expr = IntegerLiteral(42)
        stmt = AssignmentStatement("x", expr, line=1, column=0)
        self.assertEqual(stmt.var_name, "x")
        self.assertIs(stmt.expr, expr)

    def test_array_assignment_statement(self):
        """测试数组赋值语句"""
        index = IntegerLiteral(0)
        value = StringLiteral("test")
        stmt = ArrayAssignmentStatement("arr", index, value, line=1, column=0)
        self.assertEqual(stmt.array_name, "arr")
        self.assertIs(stmt.index_expr, index)
        self.assertIs(stmt.value_expr, value)

    def test_return_statement_with_value(self):
        """测试带返回值的 return 语句"""
        expr = IntegerLiteral(42)
        stmt = ReturnStatement(expr, line=1, column=0)
        self.assertIs(stmt.expr, expr)

    def test_return_statement_without_value(self):
        """测试无返回值的 return 语句"""
        stmt = ReturnStatement(None, line=1, column=0)
        self.assertIsNone(stmt.expr)

    def test_if_statement(self):
        """测试 if 语句"""
        condition = BooleanLiteral(True)
        then_block = BlockStatement([AssignmentStatement("x", IntegerLiteral(1))])
        else_block = BlockStatement([AssignmentStatement("x", IntegerLiteral(2))])
        stmt = IfStatement(condition, then_block, else_block, line=1, column=0)
        self.assertIs(stmt.condition, condition)
        self.assertIs(stmt.then_block, then_block)
        self.assertIs(stmt.else_block, else_block)

    def test_while_statement(self):
        """测试 while 语句"""
        condition = BinaryOp(Variable("i"), "<", IntegerLiteral(10))
        body = BlockStatement([IncrementStatement("i")])
        stmt = WhileStatement(condition, body, line=1, column=0)
        self.assertIs(stmt.condition, condition)
        self.assertIs(stmt.body, body)

    def test_for_in_statement(self):
        """测试 for-in 语句"""
        iterable = FunctionCall("range", [IntegerLiteral(10)])
        body = BlockStatement([EchoStatement(Variable("i"))])
        stmt = ForInStatement("i", iterable, body, line=1, column=0)
        self.assertEqual(stmt.var_name, "i")
        self.assertIs(stmt.iterable_expr, iterable)
        self.assertIs(stmt.body, body)

    def test_break_statement(self):
        """测试 break 语句"""
        stmt = BreakStatement(line=1, column=0)
        self.assertEqual(stmt.line, 1)

    def test_continue_statement(self):
        """测试 continue 语句"""
        stmt = ContinueStatement(line=1, column=0)
        self.assertEqual(stmt.line, 1)

    def test_throw_statement(self):
        """测试 throw 语句"""
        expr = StringLiteral("error message")
        stmt = ThrowStatement(expr, line=1, column=0)
        self.assertIs(stmt.expr, expr)

    def test_throw_statement_without_expr(self):
        """测试无表达式的 throw 语句"""
        stmt = ThrowStatement(None, line=1, column=0)
        self.assertIsNone(stmt.expr)

    def test_echo_statement(self):
        """测试 echo 语句"""
        expr = StringLiteral("hello")
        stmt = EchoStatement(expr, line=1, column=0)
        self.assertIs(stmt.expr, expr)

    def test_increment_statement(self):
        """测试自增语句"""
        stmt = IncrementStatement("x", line=1, column=0)
        self.assertEqual(stmt.var_name, "x")

    def test_import_statement(self):
        """测试 import 语句"""
        stmt = ImportStatement("math", None, line=1, column=0)
        self.assertEqual(stmt.module_name, "math")
        self.assertIsNone(stmt.alias)

    def test_import_statement_with_alias(self):
        """测试带别名的 import 语句"""
        stmt = ImportStatement("math", "m", line=1, column=0)
        self.assertEqual(stmt.module_name, "math")
        self.assertEqual(stmt.alias, "m")

    def test_block_statement(self):
        """测试块语句"""
        stmts = [
            AssignmentStatement("x", IntegerLiteral(1)),
            AssignmentStatement("y", IntegerLiteral(2))
        ]
        block = BlockStatement(stmts)
        self.assertEqual(len(block.statements), 2)

    def test_empty_block_statement(self):
        """测试空块语句"""
        block = BlockStatement([])
        self.assertEqual(block.statements, [])

    def test_catch_clause(self):
        """测试 catch 子句"""
        block = BlockStatement([EchoStatement(StringLiteral("error"))])
        clause = CatchClause("TypeError", "e", block)
        self.assertEqual(clause.error_type, "TypeError")
        self.assertEqual(clause.var_name, "e")
        self.assertIs(clause.block, block)

    def test_catch_clause_without_type(self):
        """测试无错误类型的 catch 子句"""
        block = BlockStatement([])
        clause = CatchClause(None, "err", block)
        self.assertIsNone(clause.error_type)
        self.assertEqual(clause.var_name, "err")


class TestTryCatchStatement(unittest.TestCase):
    """测试 TryCatchStatement 类"""

    def test_try_catch_basic(self):
        """测试基本 try-catch"""
        try_block = BlockStatement([AssignmentStatement("x", IntegerLiteral(1))])
        catch_block = BlockStatement([EchoStatement(StringLiteral("error"))])
        catch_clause = CatchClause(None, "e", catch_block)
        stmt = TryCatchStatement(try_block, [catch_clause], None, line=1, column=0)
        self.assertIs(stmt.try_block, try_block)
        self.assertEqual(len(stmt.catch_clauses), 1)
        self.assertIsNone(stmt.finally_block)

    def test_try_catch_finally(self):
        """测试带 finally 的 try-catch"""
        try_block = BlockStatement([])
        catch_block = BlockStatement([])
        catch_clause = CatchClause(None, "e", catch_block)
        finally_block = BlockStatement([EchoStatement(StringLiteral("finally"))])
        stmt = TryCatchStatement(try_block, [catch_clause], finally_block, line=1, column=0)
        self.assertIs(stmt.finally_block, finally_block)

    def test_try_catch_multiple_clauses(self):
        """测试多 catch 子句"""
        try_block = BlockStatement([])
        catch1 = CatchClause("TypeError", "e1", BlockStatement([]))
        catch2 = CatchClause("ValueError", "e2", BlockStatement([]))
        stmt = TryCatchStatement(try_block, [catch1, catch2], None, line=1, column=0)
        self.assertEqual(len(stmt.catch_clauses), 2)


if __name__ == '__main__':
    unittest.main()
