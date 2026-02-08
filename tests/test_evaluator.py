#!/usr/bin/env python3
"""
HPL 执行器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hpl_runtime'))

import unittest
from evaluator import HPLEvaluator, ReturnValue

try:
    from hpl_runtime.models import *
except ImportError:
    from models import *



class TestHPLEvaluator(unittest.TestCase):
    """测试 HPLEvaluator 类"""
    
    def setUp(self):
        """测试前准备"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None
        self.call_target = None
        self.call_args = []

    
    def test_evaluate_integer_literal(self):
        """测试整数字面量求值"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        expr = IntegerLiteral(42)
        result = evaluator.evaluate_expression(expr, {})
        self.assertEqual(result, 42)
    
    def test_evaluate_string_literal(self):
        """测试字符串字面量求值"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        expr = StringLiteral("Hello")
        result = evaluator.evaluate_expression(expr, {})
        self.assertEqual(result, "Hello")
    
    def test_evaluate_boolean_literal(self):
        """测试布尔值字面量求值"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        
        expr_true = BooleanLiteral(True)
        result_true = evaluator.evaluate_expression(expr_true, {})
        self.assertEqual(result_true, True)
        
        expr_false = BooleanLiteral(False)
        result_false = evaluator.evaluate_expression(expr_false, {})
        self.assertEqual(result_false, False)
    
    def test_evaluate_variable(self):
        """测试变量求值"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {'x': 100}
        
        expr = Variable('x')
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 100)
    
    def test_evaluate_binary_op_arithmetic(self):
        """测试二元算术运算"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # 加法
        expr = BinaryOp(IntegerLiteral(10), '+', IntegerLiteral(20))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 30)
        
        # 减法
        expr = BinaryOp(IntegerLiteral(30), '-', IntegerLiteral(10))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 20)
        
        # 乘法
        expr = BinaryOp(IntegerLiteral(5), '*', IntegerLiteral(6))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 30)
        
        # 除法
        expr = BinaryOp(IntegerLiteral(20), '/', IntegerLiteral(4))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 5.0)
    
    def test_evaluate_binary_op_comparison(self):
        """测试二元比较运算"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # 等于
        expr = BinaryOp(IntegerLiteral(10), '==', IntegerLiteral(10))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, True)
        
        # 不等于
        expr = BinaryOp(IntegerLiteral(10), '!=', IntegerLiteral(20))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, True)
        
        # 小于
        expr = BinaryOp(IntegerLiteral(10), '<', IntegerLiteral(20))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, True)
    
    def test_evaluate_string_concatenation(self):
        """测试字符串拼接"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        expr = BinaryOp(StringLiteral("Hello"), '+', StringLiteral("World"))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, "HelloWorld")
        
        # 数字和字符串拼接
        expr = BinaryOp(StringLiteral("Count: "), '+', IntegerLiteral(42))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, "Count: 42")
    
    def test_evaluate_unary_op(self):
        """测试一元运算"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # 逻辑非
        expr = UnaryOp('!', BooleanLiteral(False))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, True)
    
    def test_assignment_statement(self):
        """测试赋值语句"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        stmt = AssignmentStatement('x', IntegerLiteral(42))
        evaluator.execute_statement(stmt, local_scope)
        
        self.assertEqual(local_scope['x'], 42)
    
    def test_if_statement(self):
        """测试 if 语句"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # 条件为真的 if 语句
        condition = BooleanLiteral(True)
        then_block = BlockStatement([AssignmentStatement('x', IntegerLiteral(1))])
        stmt = IfStatement(condition, then_block)
        
        evaluator.execute_statement(stmt, local_scope)
        self.assertEqual(local_scope['x'], 1)
    
    def test_return_statement(self):
        """测试 return 语句"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        stmt = ReturnStatement(IntegerLiteral(42))
        result = evaluator.execute_statement(stmt, local_scope)
        
        self.assertIsInstance(result, ReturnValue)
        self.assertEqual(result.value, 42)
    
    def test_array_literal(self):
        """测试数组字面量"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        expr = ArrayLiteral([IntegerLiteral(1), IntegerLiteral(2), IntegerLiteral(3)])
        result = evaluator.evaluate_expression(expr, local_scope)
        
        self.assertEqual(result, [1, 2, 3])
    
    def test_array_access(self):
        """测试数组访问"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {'arr': [10, 20, 30]}
        
        expr = ArrayAccess(Variable('arr'), IntegerLiteral(1))
        result = evaluator.evaluate_expression(expr, local_scope)
        
        self.assertEqual(result, 20)
    
    def test_undefined_variable(self):
        """测试未定义变量错误"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        expr = Variable('undefined_var')
        with self.assertRaises(ValueError) as context:
            evaluator.evaluate_expression(expr, local_scope)
        
        self.assertIn('Undefined variable', str(context.exception))
    
    def test_division_by_zero(self):
        """测试除零错误"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        expr = BinaryOp(IntegerLiteral(10), '/', IntegerLiteral(0))
        with self.assertRaises(ZeroDivisionError) as context:
            evaluator.evaluate_expression(expr, local_scope)
        
        self.assertIn('Division by zero', str(context.exception))
    
    def test_type_error(self):
        """测试类型错误"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # 字符串减法应该报错
        expr = BinaryOp(StringLiteral("hello"), '-', StringLiteral("world"))
        with self.assertRaises(TypeError) as context:
            evaluator.evaluate_expression(expr, local_scope)
        
        self.assertIn('Unsupported operand type', str(context.exception))
    
    def test_while_statement(self):
        """测试 while 语句执行"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # while (i < 3) { sum = sum + i; i++ }
        init_stmt = AssignmentStatement('i', IntegerLiteral(0))
        evaluator.execute_statement(init_stmt, local_scope)
        init_stmt2 = AssignmentStatement('sum', IntegerLiteral(0))
        evaluator.execute_statement(init_stmt2, local_scope)
        
        condition = BinaryOp(Variable('i'), '<', IntegerLiteral(3))
        body = BlockStatement([
            AssignmentStatement('sum', BinaryOp(Variable('sum'), '+', Variable('i'))),
            IncrementStatement('i')
        ])
        while_stmt = WhileStatement(condition, body)
        
        evaluator.execute_statement(while_stmt, local_scope)
        
        # 验证结果: 0+1+2 = 3
        self.assertEqual(local_scope['sum'], 3)
        self.assertEqual(local_scope['i'], 3)
    
    def test_logical_operators(self):
        """测试逻辑运算符 && 和 ||"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # 测试 && (逻辑与)
        expr_and = BinaryOp(BooleanLiteral(True), '&&', BooleanLiteral(True))
        result = evaluator.evaluate_expression(expr_and, local_scope)
        self.assertEqual(result, True)
        
        expr_and_false = BinaryOp(BooleanLiteral(True), '&&', BooleanLiteral(False))
        result = evaluator.evaluate_expression(expr_and_false, local_scope)
        self.assertEqual(result, False)
        
        # 测试 || (逻辑或)
        expr_or = BinaryOp(BooleanLiteral(False), '||', BooleanLiteral(True))
        result = evaluator.evaluate_expression(expr_or, local_scope)
        self.assertEqual(result, True)
        
        expr_or_false = BinaryOp(BooleanLiteral(False), '||', BooleanLiteral(False))
        result = evaluator.evaluate_expression(expr_or_false, local_scope)
        self.assertEqual(result, False)
    
    def test_break_continue(self):
        """测试 break 和 continue 异常"""
        from evaluator import BreakException, ContinueException
        
        # 测试 BreakException
        with self.assertRaises(BreakException):
            raise BreakException()
        
        # 测试 ContinueException
        with self.assertRaises(ContinueException):
            raise ContinueException()
    
    def test_array_assignment_statement(self):
        """测试数组元素赋值语句"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {'arr': [1, 2, 3, 4, 5]}
        
        # arr[0] = 10
        stmt = ArrayAssignmentStatement('arr', IntegerLiteral(0), IntegerLiteral(10))
        evaluator.execute_statement(stmt, local_scope)
        
        # arr[2] = 30
        stmt2 = ArrayAssignmentStatement('arr', IntegerLiteral(2), IntegerLiteral(30))
        evaluator.execute_statement(stmt2, local_scope)
        
        # 验证结果
        self.assertEqual(local_scope['arr'], [10, 2, 30, 4, 5])


class TestReturnValue(unittest.TestCase):

    """测试 ReturnValue 类"""
    
    def test_return_value_creation(self):
        """测试 ReturnValue 创建"""
        rv = ReturnValue(42)
        self.assertEqual(rv.value, 42)
        
        rv_none = ReturnValue(None)
        self.assertIsNone(rv_none.value)


if __name__ == '__main__':
    unittest.main()
