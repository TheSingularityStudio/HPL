#!/usr/bin/env python3
"""
HPL 执行器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hpl_runtime'))

import unittest

try:
    from hpl_runtime.core.evaluator import HPLEvaluator
    from hpl_runtime.core.models import *
    from hpl_runtime.utils.exceptions import HPLReturnValue, HPLNameError, HPLTypeError, HPLDivisionError
except ImportError:
    from evaluator import HPLEvaluator
    from models import *
    from exceptions import HPLReturnValue, HPLNameError, HPLTypeError, HPLDivisionError


# 使用正确的 ReturnValue 别名
ReturnValue = HPLReturnValue




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
    
    def test_evaluate_float_literal(self):
        """测试浮点数字面量求值"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        expr = FloatLiteral(3.14)
        result = evaluator.evaluate_expression(expr, {})
        self.assertEqual(result, 3.14)
        
        # 测试负数浮点数
        expr_neg = BinaryOp(IntegerLiteral(0), '-', FloatLiteral(2.5))
        result_neg = evaluator.evaluate_expression(expr_neg, {})
        self.assertEqual(result_neg, -2.5)

    
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
    
    def test_evaluate_modulo_operator(self):
        """测试取模运算符"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # 基本取模
        expr = BinaryOp(IntegerLiteral(17), '%', IntegerLiteral(5))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 2)
        
        # 取模为零的情况
        expr = BinaryOp(IntegerLiteral(15), '%', IntegerLiteral(5))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 0)
        
        # 负数取模 - Python 的取模运算结果总是与除数同号
        # -17 % 5 = 3 (因为 -17 = -4 * 5 + 3)
        expr = BinaryOp(IntegerLiteral(-17), '%', IntegerLiteral(5))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 3)
        
        # 除零错误
        expr = BinaryOp(IntegerLiteral(10), '%', IntegerLiteral(0))
        with self.assertRaises(HPLDivisionError):
            evaluator.evaluate_expression(expr, local_scope)



    
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
        with self.assertRaises(HPLNameError) as context:
            evaluator.evaluate_expression(expr, local_scope)
        
        self.assertIn('Undefined variable', str(context.exception))

    
    def test_division_by_zero(self):
        """测试除零错误"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        expr = BinaryOp(IntegerLiteral(10), '/', IntegerLiteral(0))
        with self.assertRaises(HPLDivisionError) as context:
            evaluator.evaluate_expression(expr, local_scope)
        
        self.assertIn('Division by zero', str(context.exception))

    
    def test_type_error(self):
        """测试类型错误"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # 字符串减法应该报错
        expr = BinaryOp(StringLiteral("hello"), '-', StringLiteral("world"))
        with self.assertRaises(HPLTypeError) as context:
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
    
    def test_complex_logical_expressions(self):
        """测试复杂逻辑表达式"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # 组合逻辑: (true && false) || (true && true)
        left = BinaryOp(BooleanLiteral(True), '&&', BooleanLiteral(False))
        right = BinaryOp(BooleanLiteral(True), '&&', BooleanLiteral(True))
        expr = BinaryOp(left, '||', right)
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, True)
        
        # 组合逻辑: (true || false) && (false || false)
        left = BinaryOp(BooleanLiteral(True), '||', BooleanLiteral(False))
        right = BinaryOp(BooleanLiteral(False), '||', BooleanLiteral(False))
        expr = BinaryOp(left, '&&', right)
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, False)
        
        # 与比较运算符结合: (5 > 3) && (10 < 20)
        left = BinaryOp(IntegerLiteral(5), '>', IntegerLiteral(3))
        right = BinaryOp(IntegerLiteral(10), '<', IntegerLiteral(20))
        expr = BinaryOp(left, '&&', right)
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, True)

    
    def test_break_continue(self):
        """测试 break 和 continue 异常"""
        try:
            from hpl_runtime.utils.exceptions import HPLBreakException, HPLContinueException
        except ImportError:
            from exceptions import HPLBreakException, HPLContinueException
        
        # 测试 BreakException
        with self.assertRaises(HPLBreakException):
            raise HPLBreakException()
        
        # 测试 ContinueException
        with self.assertRaises(HPLContinueException):
            raise HPLContinueException()

    
    def test_postfix_increment(self):
        """测试后缀自增表达式"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {'x': 5}
        
        # 后缀自增返回旧值
        expr = PostfixIncrement(Variable('x'))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 5)  # 返回旧值
        
        # 变量应该被自增
        self.assertEqual(local_scope['x'], 6)
        
        # 再次自增
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 6)  # 返回旧值
        self.assertEqual(local_scope['x'], 7)
    
    def test_for_statement(self):
        """测试 for 语句执行"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # for (i = 0; i < 3; i++) { sum = sum + i }
        init = AssignmentStatement('i', IntegerLiteral(0))
        condition = BinaryOp(Variable('i'), '<', IntegerLiteral(3))
        increment = PostfixIncrement(Variable('i'))
        body = BlockStatement([
            AssignmentStatement('sum', BinaryOp(Variable('sum'), '+', Variable('i')))
        ])
        
        # 初始化 sum
        local_scope['sum'] = 0
        
        for_stmt = ForStatement(init, condition, increment, body)
        evaluator.execute_statement(for_stmt, local_scope)
        
        # 验证结果: 0+1+2 = 3
        self.assertEqual(local_scope['sum'], 3)
        self.assertEqual(local_scope['i'], 3)
    
    def test_for_statement_with_break(self):
        """测试带 break 的 for 语句"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # for (i = 0; i < 10; i++) { if (i == 3) break; sum = sum + i }
        init = AssignmentStatement('i', IntegerLiteral(0))
        condition = BinaryOp(Variable('i'), '<', IntegerLiteral(10))
        increment = PostfixIncrement(Variable('i'))
        
        # 创建 if 语句包含 break
        break_if = IfStatement(
            BinaryOp(Variable('i'), '==', IntegerLiteral(3)),
            BlockStatement([BreakStatement()])
        )
        body = BlockStatement([
            break_if,
            AssignmentStatement('sum', BinaryOp(Variable('sum'), '+', Variable('i')))
        ])
        
        local_scope['sum'] = 0
        for_stmt = ForStatement(init, condition, increment, body)
        evaluator.execute_statement(for_stmt, local_scope)
        
        # 验证结果: 0+1+2 = 3 (在 i=3 时 break)
        self.assertEqual(local_scope['sum'], 3)
    
    def test_for_statement_with_continue(self):
        """测试带 continue 的 for 语句"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # for (i = 0; i < 5; i++) { if (i == 2) continue; sum = sum + i }
        init = AssignmentStatement('i', IntegerLiteral(0))
        condition = BinaryOp(Variable('i'), '<', IntegerLiteral(5))
        increment = PostfixIncrement(Variable('i'))
        
        # 创建 if 语句包含 continue
        continue_if = IfStatement(
            BinaryOp(Variable('i'), '==', IntegerLiteral(2)),
            BlockStatement([ContinueStatement()])
        )
        body = BlockStatement([
            continue_if,
            AssignmentStatement('sum', BinaryOp(Variable('sum'), '+', Variable('i')))
        ])
        
        local_scope['sum'] = 0
        for_stmt = ForStatement(init, condition, increment, body)
        evaluator.execute_statement(for_stmt, local_scope)
        
        # 验证结果: 0+1+3+4 = 8 (跳过了 i=2)
        self.assertEqual(local_scope['sum'], 8)
    
    def test_try_catch_statement(self):
        """测试 try-catch 语句"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # try { x = 1 / 0 } catch (e) { error = e }
        try_block = BlockStatement([
            AssignmentStatement('x', BinaryOp(IntegerLiteral(1), '/', IntegerLiteral(0)))
        ])
        catch_block = BlockStatement([
            AssignmentStatement('error', Variable('e'))
        ])
        
        try_catch = TryCatchStatement(try_block, 'e', catch_block)
        evaluator.execute_statement(try_catch, local_scope)
        
        # 应该捕获除零错误
        self.assertIn('error', local_scope)
        self.assertIn('Division by zero', local_scope['error'])
    
    def test_try_catch_no_exception(self):
        """测试无异常的 try-catch 语句"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)

        local_scope = {}
        
        # try { x = 42 } catch (e) { error = e }
        try_block = BlockStatement([
            AssignmentStatement('x', IntegerLiteral(42))
        ])
        catch_block = BlockStatement([
            AssignmentStatement('error', Variable('e'))
        ])
        
        try_catch = TryCatchStatement(try_block, 'e', catch_block)
        evaluator.execute_statement(try_catch, local_scope)
        
        # 应该正常执行，不进入 catch
        self.assertEqual(local_scope['x'], 42)
        self.assertNotIn('error', local_scope)

    
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
