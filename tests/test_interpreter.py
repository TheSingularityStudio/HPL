#!/usr/bin/env python3
"""
HPL 解释器单元测试

测试解释器模块的主要功能：
1. 命令行参数处理
2. 文件执行流程
3. 错误处理
"""

import sys
import os
import tempfile
import shutil
import io
import contextlib
import unittest
from unittest.mock import patch, MagicMock


# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from hpl_runtime.interpreter import main
    from hpl_runtime.parser import HPLParser
    from hpl_runtime.evaluator import HPLEvaluator
except ImportError:
    from interpreter import main
    from parser import HPLParser
    from evaluator import HPLEvaluator


class TestInterpreterMain(unittest.TestCase):
    """测试解释器主函数"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_argv = sys.argv.copy()
    
    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir)
        sys.argv = self.original_argv
    
    def create_test_hpl_file(self, content, filename="test.hpl"):
        """创建临时 HPL 文件"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_main_with_valid_file(self):
        """测试执行有效的 HPL 文件"""
        hpl_content = """main: () => {
    echo "Hello from interpreter test"
    x = 42
    echo "Value: " + x
  }

call: main()
"""
        file_path = self.create_test_hpl_file(hpl_content)
        
        # 捕获输出
        output = io.StringIO()
        
        with patch.object(sys, 'argv', ['interpreter.py', file_path]):
            with contextlib.redirect_stdout(output):
                try:
                    main()
                except SystemExit as e:
                    # 正常执行应该返回 0
                    self.assertEqual(e.code, 0)
        
        result = output.getvalue()
        self.assertIn("Hello from interpreter test", result)
        self.assertIn("Value: 42", result)
    
    def test_main_with_missing_arguments(self):
        """测试缺少命令行参数"""
        with patch.object(sys, 'argv', ['interpreter.py']):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # 应该返回非零退出码
            self.assertEqual(context.exception.code, 1)
    
    def test_main_with_nonexistent_file(self):
        """测试执行不存在的文件"""
        with patch.object(sys, 'argv', ['interpreter.py', '/nonexistent/file.hpl']):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # 应该返回非零退出码
            self.assertEqual(context.exception.code, 1)
    
    def test_main_with_syntax_error(self):
        """测试执行包含语法错误的文件"""
        # 创建包含语法错误的 HPL 文件
        hpl_content = """main: () => {
    # 缺少闭合括号
    x = (1 + 2
  }

call: main()
"""
        file_path = self.create_test_hpl_file(hpl_content, "bad_syntax.hpl")
        
        with patch.object(sys, 'argv', ['interpreter.py', file_path]):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # 语法错误应该返回非零退出码
            self.assertEqual(context.exception.code, 1)
    
    def test_main_with_imports(self):
        """测试执行带导入语句的文件"""
        # 创建被导入的模块
        module_content = """greet: (name) => {
    return "Hello, " + name
}
"""
        module_path = os.path.join(self.temp_dir, "greeting.hpl")
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(module_content)
        
        # 创建主文件
        main_content = f"""imports:
  - greeting

main: () => {{
    message = greeting.greet("World")
    echo message
  }}

call: main()
"""
        main_path = self.create_test_hpl_file(main_content, "main_with_import.hpl")
        
        # 添加临时目录到模块路径
        try:
            from hpl_runtime.module_loader import add_module_path
        except ImportError:
            from module_loader import add_module_path
        add_module_path(self.temp_dir)
        
        # 捕获输出
        output = io.StringIO()
        
        with patch.object(sys, 'argv', ['interpreter.py', main_path]):
            with contextlib.redirect_stdout(output):
                try:
                    main()
                except SystemExit as e:
                    self.assertEqual(e.code, 0)
        
        result = output.getvalue()
        self.assertIn("Hello, World", result)


class TestInterpreterEdgeCases(unittest.TestCase):
    """测试解释器的边界情况"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_argv = sys.argv.copy()
    
    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir)
        sys.argv = self.original_argv
    
    def create_test_hpl_file(self, content, filename="test.hpl"):
        """创建临时 HPL 文件"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_empty_file(self):
        """测试执行空文件"""
        file_path = self.create_test_hpl_file("", "empty.hpl")
        
        with patch.object(sys, 'argv', ['interpreter.py', file_path]):
            # 空文件应该正常退出
            with self.assertRaises(SystemExit) as context:
                main()
            
            # 空文件没有 main 函数，应该报错
            self.assertEqual(context.exception.code, 1)
    
    def test_file_with_only_comments(self):
        """测试执行只有注释的文件"""
        hpl_content = """# 这是一个只有注释的文件
# 没有实际的代码
"""
        file_path = self.create_test_hpl_file(hpl_content, "comments_only.hpl")
        
        with patch.object(sys, 'argv', ['interpreter.py', file_path]):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # 没有 main 函数，应该报错
            self.assertEqual(context.exception.code, 1)
    
    def test_file_with_runtime_error(self):
        """测试执行时发生运行时错误"""
        hpl_content = """main: () => {
    # 除零错误
    x = 10 / 0
    echo x
  }

call: main()
"""
        file_path = self.create_test_hpl_file(hpl_content, "runtime_error.hpl")
        
        with patch.object(sys, 'argv', ['interpreter.py', file_path]):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # 运行时错误应该返回非零退出码
            self.assertEqual(context.exception.code, 1)


class TestInterpreterOutput(unittest.TestCase):
    """测试解释器的输出功能"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_argv = sys.argv.copy()
    
    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir)
        sys.argv = self.original_argv
    
    def create_test_hpl_file(self, content, filename="test.hpl"):
        """创建临时 HPL 文件"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_echo_output(self):
        """测试 echo 输出"""
        hpl_content = """main: () => {
    echo "Line 1"
    echo "Line 2"
    echo 123
    echo true
  }

call: main()
"""
        file_path = self.create_test_hpl_file(hpl_content)
        
        output = io.StringIO()
        
        with patch.object(sys, 'argv', ['interpreter.py', file_path]):
            with contextlib.redirect_stdout(output):
                try:
                    main()
                except SystemExit as e:
                    self.assertEqual(e.code, 0)
        
        result = output.getvalue()
        self.assertIn("Line 1", result)
        self.assertIn("Line 2", result)
        self.assertIn("123", result)
        self.assertIn("True", result)
    
    def test_complex_program_output(self):
        """测试复杂程序的输出"""
        hpl_content = """main: () => {
    # 测试各种数据类型和运算
    arr = [1, 2, 3, 4, 5]
    echo "Array length: " + len(arr)
    
    # 测试条件
    if (len(arr) > 3) :
      echo "Array is long enough"
    
    # 测试循环
    sum = 0
    for (i = 0; i < 5; i++) :
      sum = sum + arr[i]
    
    echo "Sum: " + sum
  }

call: main()
"""
        file_path = self.create_test_hpl_file(hpl_content)
        
        output = io.StringIO()
        
        with patch.object(sys, 'argv', ['interpreter.py', file_path]):
            with contextlib.redirect_stdout(output):
                try:
                    main()
                except SystemExit as e:
                    self.assertEqual(e.code, 0)
        
        result = output.getvalue()
        self.assertIn("Array length: 5", result)
        self.assertIn("Array is long enough", result)
        self.assertIn("Sum: 15", result)


if __name__ == '__main__':
    unittest.main()
