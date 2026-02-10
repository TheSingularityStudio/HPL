#!/usr/bin/env python3
"""
HPL 集成测试 - 测试完整的解释流程
"""

import sys
import os
import io
import contextlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hpl_runtime'))

import unittest

try:
    from hpl_runtime.core.parser import HPLParser
    from hpl_runtime.core.evaluator import HPLEvaluator
except ImportError:
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
        
        # 添加 examples 目录到模块搜索路径（用于第三方模块测试）
        try:
            from hpl_runtime.modules.loader import add_module_path, set_current_hpl_file
        except ImportError:
            from module_loader import add_module_path, set_current_hpl_file
        add_module_path(self.examples_dir)
        
        # 设置当前 HPL 文件目录，用于相对导入
        set_current_hpl_file(filepath)
        
        # 添加 examples 目录到 sys.path，以便 importlib 能找到本地 Python 模块
        if self.examples_dir not in sys.path:
            sys.path.insert(0, self.examples_dir)


        
        # 解析
        parser = HPLParser(filepath)
        classes, objects, functions, main_func, call_target, call_args, imports = parser.parse()
        
        # 执行并捕获输出
        evaluator = HPLEvaluator(classes, objects, functions, main_func, call_target, call_args)

        
        # 处理顶层导入
        for imp in imports:
            module_name = imp['module']
            alias = imp['alias'] or module_name
            # 创建 ImportStatement 并执行
            from hpl_runtime.core.models import ImportStatement
            import_stmt = ImportStatement(module_name, alias)
            evaluator.execute_import(import_stmt, evaluator.global_scope)


        
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
    
    def test_new_features_hpl(self):
        """测试新特性：while循环、逻辑运算符、break/continue"""
        output = self.run_hpl_file('test_new_features.hpl')
        
        # 验证while循环
        self.assertIn('While sum: 10', output)
        # 验证逻辑运算符
        self.assertIn('a && c is true', output)
        self.assertIn('b || c is true', output)
        self.assertIn('a && !b is true', output)
        # 验证break/continue
        self.assertIn('Testing continue:', output)
        self.assertIn('Testing break:', output)
        self.assertIn('All tests passed!', output)
    
    def test_array_assignment_hpl(self):
        """测试数组元素赋值"""
        output = self.run_hpl_file('test_array_assignment.hpl')
        
        # 验证数组创建和修改
        self.assertIn('原始数组: [1, 2, 3, 4, 5]', output)
        self.assertIn('修改后数组: [10, 2, 30, 4, 5]', output)
        self.assertIn('第一个元素: 10', output)
        self.assertIn('第三个元素: 30', output)
        # 验证循环中修改数组
        self.assertIn('循环修改后: [0, 10, 20, 30, 40]', output)
    
    def test_builtin_functions_hpl(self):
        """测试内置函数"""
        output = self.run_hpl_file('test_builtin_functions.hpl')
        
        # 验证len()函数
        self.assertIn('Array length: 5', output)
        self.assertIn('String length: 11', output)
        # 验证type()函数
        self.assertIn("Type of 42: int", output)
        self.assertIn("Type of 3.14: float", output)
        self.assertIn("Type of 'hello': string", output)
        self.assertIn("Type of true: boolean", output)
        self.assertIn("Type of [1,2,3]: array", output)
        # 验证int()和str()转换
        self.assertIn('Converted int: 123', output)
        self.assertIn('Converted string: 456', output)
        # 验证abs()、max()、min()
        self.assertIn('Absolute value: 42', output)
        self.assertIn('Max value: 20', output)
        self.assertIn('Min value: 5', output)
        self.assertIn('All built-in function tests passed!', output)
    
    def test_string_features_hpl(self):
        """测试字符串特性：转义序列和索引"""
        output = self.run_hpl_file('test_string_features.hpl')
        
        # 验证转义序列
        self.assertIn('测试换行：', output)
        self.assertIn('第一行', output)
        self.assertIn('第二行', output)
        self.assertIn('测试制表符：', output)
        self.assertIn('列1', output)
        self.assertIn('列2', output)
        self.assertIn('列3', output)
        # 验证字符串索引
        self.assertIn('字符串: Hello', output)
        self.assertIn('第一个字符: H', output)
        self.assertIn('第二个字符: e', output)
        self.assertIn('最后一个字符: o', output)
        self.assertIn('字符串长度: 5', output)
    
    def test_stdlib_hpl(self):
        """测试标准库模块"""
        output = self.run_hpl_file('test_stdlib.hpl')
        
        # 验证math模块
        self.assertIn('=== Math Module Test ===', output)
        self.assertIn('PI = 3.14159', output)
        self.assertIn('sqrt(16) = 4', output)
        self.assertIn('sin(0) = 0', output)
        self.assertIn('pow(2, 10) = 1024', output)
        # 验证time模块
        self.assertIn('=== Time Module Test ===', output)
        self.assertIn('Current timestamp:', output)
        # 验证os模块
        self.assertIn('=== OS Module Test ===', output)
        self.assertIn('Platform:', output)
        self.assertIn('Python version:', output)
        # 验证io模块
        self.assertIn('=== IO Module Test ===', output)
        self.assertIn('File content: Hello from HPL!', output)
        # 验证json模块
        self.assertIn('=== JSON Module Test ===', output)
        self.assertIn('JSON string:', output)
        self.assertIn('All Tests Completed', output)
    
    def test_third_party_hpl(self):
        """测试第三方Python模块"""
        # 此测试需要复杂的模块路径设置，暂时跳过
        # 如需运行此测试，需要确保 my_python_module.py 在模块搜索路径中
        self.skipTest("第三方模块测试需要特殊环境设置")
    
    def test_input_function_hpl(self):
        """测试 input() 函数"""
        # 使用 mock 模拟用户输入
        from unittest.mock import patch
        
        # 模拟输入序列
        inputs = ['Alice', '25', 'Hello World']
        
        with patch('builtins.input', side_effect=inputs):
            output = self.run_hpl_file('test_input_function.hpl')
            
            # 验证输出包含预期内容
            self.assertIn('=== 测试 input() 函数 ===', output)
            self.assertIn('你好, Alice!', output)
            self.assertIn('明年你将 26 岁', output)
            self.assertIn('你输入了: Hello World', output)
            self.assertIn('=== input() 函数测试完成 ===', output)
    
    def test_import_alias_hpl(self):
        """测试模块导入别名功能"""
        output = self.run_hpl_file('test_import_alias.hpl')
        
        # 验证别名导入的模块功能正常
        self.assertIn('=== HPL Import Alias Test (Fixed Format) ===', output)
        self.assertIn('m.PI = 3.14159', output)
        self.assertIn('m.sqrt(16) = 4', output)
        self.assertIn('m.floor(3.14) = 3', output)
        self.assertIn('Hello, Alias Tester!', output)
        # 验证模块常量存在（实际值可能不同）
        self.assertIn('App:', output)
        self.assertIn('Version:', output)
        self.assertIn('20 / 4 = 5', output)
        self.assertIn('=== Alias Test Complete ===', output)

    
    def test_call_any_function_hpl(self):
        """测试 call 调用任意函数功能"""
        output = self.run_hpl_file('test_call_any_function.hpl')
        
        # 验证调用了 add(5, 3) 而不是 main()
        self.assertIn('Adding 5 + 3 = 8', output)
        # 不应该执行 main 函数的内容
        self.assertNotIn('This is the main function', output)



class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""
    
    def test_file_not_found(self):
        """测试文件不存在错误"""
        with self.assertRaises(FileNotFoundError):
            parser = HPLParser('nonexistent_file.hpl')
            parser.parse()
    
    def test_syntax_error_handling(self):
        """测试语法错误处理"""
        import tempfile
        import os
        
        # 创建一个包含语法错误的临时 HPL 文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hpl', delete=False, encoding='utf-8') as f:
            f.write("""main: () => {
    # 缺少闭合括号
    x = (1 + 2
  }""")
            temp_file = f.name
        
        try:
            # 语法错误应该在解析时抛出异常
            with self.assertRaises(Exception):
                parser = HPLParser(temp_file)
                parser.parse()
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
