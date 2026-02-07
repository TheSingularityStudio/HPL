#!/usr/bin/env python3
"""
HPL 集成测试 - 测试完整的解释流程
"""

import sys
import os
import io
import contextlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from parser import HPLParser
from evaluator import HPLEvaluator


class TestHPLIntegration(unittest.TestCase):
    """HPL 集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.examples_dir = os.path.join(os.path.dirname(__file__), '..', 'examples')
    
    def run_hpl_file(self, filename):
        """辅助方法：运行 HPL 文件并返回输出"""
        filepath = os.path.join(self.examples_dir, filename)
        if not os.path.exists(filepath):
            self.skipTest(f"文件不存在: {filepath}")
        
        # 解析
        parser = HPLParser(filepath)
        classes, objects, main_func, call_target = parser.parse()
        
        # 执行并捕获输出
        evaluator = HPLEvaluator(classes, objects, main_func, call_target)
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            evaluator.run()
        
        return output.getvalue()
    
    def test_example_hpl(self):
        """测试主示例文件"""
        output = self.run_hpl_file('example.hpl')
        
        # 验证输出包含预期内容
        self.assertIn('Hello World', output)
        self.assertIn('Even: Hello World', output)
        self.assertIn('Odd: Hello World', output)
    
    def test_fixes_hpl(self):
        """测试修复功能文件"""
        output = self.run_hpl_file('test_fixes.hpl')
        
        # 验证返回值
        self.assertIn('Return test: 42', output)
        # 验证算术运算
        self.assertIn('Sum: 30', output)
        # 验证字符串拼接
        self.assertIn('Concat: Hello World', output)
        # 验证逻辑非
        self.assertIn('NOT operator works!', output)
        # 验证自增
        self.assertIn('Counter after increment: 1', output)
    
    def test_for_loop_hpl(self):
        """测试 for 循环文件"""
        output = self.run_hpl_file('test_for_loop.hpl')
        
        # 验证循环输出
        for i in range(5):
            self.assertIn(f'Iteration: {i}', output)
        self.assertIn('Loop finished', output)
    
    def test_comment_comprehensive_hpl(self):
        """测试注释处理文件"""
        output = self.run_hpl_file('test_comment_comprehensive.hpl')
        
        # 验证所有功能正常工作（注释被正确跳过）
        self.assertIn('Result: 30', output)
        self.assertIn('Positive result', output)
        self.assertIn('Try block: 100', output)
        self.assertIn('All tests passed!', output)
    
    def test_low_priority_hpl(self):
        """测试高级特性文件"""
        output = self.run_hpl_file('test_low_priority.hpl')
        
        # 验证浮点数运算
        self.assertIn('Circle area: 19.625', output)
        # 验证负数
        self.assertIn('Negative number: -42', output)
        # 验证数组访问
        self.assertIn('First element: 1', output)
        self.assertIn('Third element: 3', output)
        # 验证动态索引
        self.assertIn('Dynamic index: 2', output)
        # 验证浮点数比较
        self.assertIn('Pi is less than 3.15', output)


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""
    
    def test_file_not_found(self):
        """测试文件不存在错误"""
        with self.assertRaises(FileNotFoundError):
            parser = HPLParser('nonexistent_file.hpl')
            parser.parse()


if __name__ == '__main__':
    unittest.main()

