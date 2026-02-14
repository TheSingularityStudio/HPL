"""
HPL错误处理传播测试模块

测试错误传播改进的各项功能：
1. 调用栈一致性
2. 位置信息准确性
3. 错误上下文完整性
"""

import sys
import os
import unittest

# 确保hpl_runtime在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from hpl_runtime.core.evaluator import HPLEvaluator
from hpl_runtime.core.models import (
    BinaryOp, IntegerLiteral, FunctionCall, Variable,
    AssignmentStatement, TryCatchStatement, BlockStatement,
    ThrowStatement, CatchClause
)

from hpl_runtime.utils.exceptions import (
    HPLRuntimeError, HPLDivisionError, HPLNameError,
    HPLTypeError, HPLControlFlowException
)


class TestErrorPropagation(unittest.TestCase):
    """测试错误传播机制"""
    
    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None
    
    def test_division_by_zero_has_location(self):
        """测试除零错误包含位置信息"""
        # 创建除法表达式: 10 / 0
        left = IntegerLiteral(10, line=5, column=1)
        right = IntegerLiteral(0, line=5, column=6)
        div_expr = BinaryOp(left, '/', right, line=5, column=4)

        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions)
        
        try:
            evaluator.evaluate_expression(div_expr, {})
            self.fail("应该抛出HPLDivisionError")
        except HPLDivisionError as e:
            # 验证错误包含位置信息
            self.assertIsNotNone(e.line, "错误应该包含行号")
            self.assertEqual(e.line, 5, "行号应该是5")
            self.assertIsNotNone(e.call_stack, "错误应该包含调用栈")
    
    def test_call_stack_captured_in_error(self):
        """测试错误包含完整的调用栈"""
        # 创建一个会抛出错误的函数
        throw_stmt = ThrowStatement(
            BinaryOp(IntegerLiteral(1), '/', IntegerLiteral(0), line=10, column=5),
            line=10, column=1
        )
        func_body = BlockStatement([throw_stmt])

        func = type('Function', (), {
            'body': func_body,
            'params': []
        })()
        
        evaluator = HPLEvaluator(self.classes, self.objects, {'test_func': func})
        
        try:
            evaluator.execute_function(func, {}, 'test_func')
            self.fail("应该抛出HPLRuntimeError")
        except HPLRuntimeError as e:
            # 验证调用栈包含函数名
            self.assertTrue(len(e.call_stack) > 0, "调用栈不应该为空")
            self.assertIn('test_func()', e.call_stack, "调用栈应该包含test_func")
    
    def test_error_context_enriched_in_try_catch(self):
        """测试try-catch中未捕获错误的上下文增强"""
        # 创建try块中的错误
        throw_stmt = ThrowStatement(
            BinaryOp(IntegerLiteral(1), '/', IntegerLiteral(0), line=20, column=5),
            line=20, column=1
        )
        try_block = BlockStatement([throw_stmt])
        try_block.line = 15  # 设置try块行号
        
        # 创建只捕获特定类型错误的catch子句
        catch_clause = CatchClause('HPLTypeError', 'e', BlockStatement([]))

        try_catch = TryCatchStatement(try_block, [catch_clause], None)
        
        evaluator = HPLEvaluator(self.classes, self.objects)
        
        try:
            evaluator.execute_statement(try_catch, {})
            self.fail("应该抛出HPLRuntimeError")
        except HPLRuntimeError as e:
            # 验证错误位置信息被保留
            self.assertEqual(e.line, 20, "错误行号应该是20")
    
    def test_control_flow_exception_propagation(self):
        """测试控制流异常正确传播"""
        from hpl_runtime.utils.exceptions import HPLBreakException
        
        # 创建包含break的try块
        from hpl_runtime.core.models import BreakStatement
        break_stmt = BreakStatement(line=30, column=5)
        try_block = BlockStatement([break_stmt])

        
        try_catch = TryCatchStatement(try_block, [], None)
        
        evaluator = HPLEvaluator(self.classes, self.objects)
        
        # 验证break异常能正确传播
        with self.assertRaises(HPLBreakException):
            evaluator.execute_statement(try_catch, {})
    
    def test_nested_function_call_stack(self):
        """测试嵌套函数调用的调用栈"""
        # 创建嵌套函数
        inner_throw = ThrowStatement(
            BinaryOp(IntegerLiteral(1), '/', IntegerLiteral(0), line=40, column=5),
            line=40, column=1
        )
        inner_body = BlockStatement([inner_throw])
        inner_func = type('Function', (), {
            'body': inner_body,
            'params': []
        })()
        
        # 外层函数调用内层函数
        outer_call = FunctionCall('inner_func', [])

        outer_body = BlockStatement([outer_call])
        outer_func = type('Function', (), {
            'body': outer_body,
            'params': []
        })()

        
        functions = {
            'outer_func': outer_func,
            'inner_func': inner_func
        }
        
        evaluator = HPLEvaluator(self.classes, self.objects, functions)
        
        try:
            evaluator.execute_function(outer_func, {}, 'outer_func')
            self.fail("应该抛出HPLRuntimeError")
        except HPLRuntimeError as e:
            # 验证调用栈包含两个函数
            self.assertTrue(len(e.call_stack) >= 2, "调用栈应该包含至少2个帧")
            self.assertIn('outer_func()', e.call_stack, "调用栈应该包含outer_func")
            self.assertIn('inner_func()', e.call_stack, "调用栈应该包含inner_func")
    
    def test_error_handler_no_duplicate_enhancement(self):
        """测试错误处理器不会重复增强错误"""
        from hpl_runtime.utils.error_handler import HPLErrorHandler
        
        # 创建模拟错误
        error = HPLRuntimeError(
            "Test error",
            line=50,
            column=10,
            call_stack=['func1()', 'func2()']
        )
        
        handler = HPLErrorHandler()
        
        # 模拟处理错误（不退出）
        report = handler.handle(error, exit_on_error=False)
        
        # 验证调用栈没有被修改
        self.assertEqual(len(error.call_stack), 2, "调用栈不应该被重复增强")
        self.assertIn('func1()', error.call_stack)
        self.assertIn('func2()', error.call_stack)


class TestErrorLocationAccuracy(unittest.TestCase):
    """测试错误位置信息准确性"""
    
    def setUp(self):
        self.classes = {}
        self.objects = {}
        self.functions = {}
    
    def test_binary_op_error_location(self):
        """测试二元运算错误的位置信息"""
        # 测试不同位置的除法错误
        test_cases = [
            (1, 5, 10, 0),   # 第1行，第5列
            (100, 20, 5, 0), # 第100行，第20列
            (50, 1, 8, 0),   # 第50行，第1列
        ]
        
        for line, column, left_val, right_val in test_cases:
            with self.subTest(line=line, column=column):
                left = IntegerLiteral(left_val, line=line, column=column)
                right = IntegerLiteral(right_val, line=line, column=column + 10)
                div_expr = BinaryOp(left, '/', right, line=line, column=column + 5)
                
                evaluator = HPLEvaluator(self.classes, self.objects)
                
                try:
                    evaluator.evaluate_expression(div_expr, {})
                    self.fail("应该抛出HPLDivisionError")
                except HPLDivisionError as e:
                    self.assertEqual(e.line, line, f"行号应该是{line}")
                    self.assertEqual(e.column, column + 5, f"列号应该是{column + 5}")


class TestErrorContextPreservation(unittest.TestCase):
    """测试错误上下文保留"""
    
    def setUp(self):
        self.classes = {}
        self.objects = {}
        self.functions = {}
    
    def test_variable_error_includes_context(self):
        """测试变量错误包含上下文信息"""
        evaluator = HPLEvaluator(self.classes, self.objects)
        
        # 查找不存在的变量
        var = Variable('undefined_var', line=60, column=5)
        
        try:
            evaluator.evaluate_expression(var, {})
            self.fail("应该抛出HPLNameError")
        except HPLNameError as e:
            # 验证错误包含变量名
            self.assertIn('undefined_var', str(e), "错误消息应该包含变量名")
            self.assertEqual(e.line, 60, "行号应该是60")
            self.assertIsNotNone(e.call_stack, "错误应该包含调用栈")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestErrorPropagation))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorLocationAccuracy))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorContextPreservation))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
