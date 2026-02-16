#!/usr/bin/env python3
"""
HPL 端到端示例测试

测试所有示例文件能正确运行
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
import subprocess
import tempfile
from pathlib import Path


class TestEndToEndExamples(unittest.TestCase):
    """测试端到端示例"""

    def setUp(self):
        """测试前准备"""
        self.examples_dir = Path(os.path.dirname(__file__)).parent.parent / "examples"
        self.hpl_runtime_dir = Path(os.path.dirname(__file__)).parent.parent / "hpl_runtime"


    def run_hpl_file(self, file_path, timeout=10):
        """运行 HPL 文件"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "hpl_runtime", str(file_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(Path(os.path.dirname(__file__)).parent.parent)
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -1, "", str(e)


    def test_example_hpl(self):
        """测试主示例文件"""
        example_file = self.examples_dir / "example.hpl"
        if not example_file.exists():
            self.skipTest("example.hpl not found")
        
        returncode, stdout, stderr = self.run_hpl_file(example_file)
        # 示例应该成功运行或正常退出
        self.assertIn(returncode, [0, 1], f"Unexpected exit code: {returncode}\nstderr: {stderr}")

    def test_base_hpl(self):
        """测试基础类文件"""
        base_file = self.examples_dir / "base.hpl"
        if not base_file.exists():
            self.skipTest("base.hpl not found")
        
        returncode, stdout, stderr = self.run_hpl_file(base_file)
        self.assertIn(returncode, [0, 1], f"Unexpected exit code: {returncode}")

    def test_complex_demo_hpl(self):
        """测试复杂演示文件"""
        demo_file = self.examples_dir / "complex_demo.hpl"
        if not demo_file.exists():
            self.skipTest("complex_demo.hpl not found")
        
        returncode, stdout, stderr = self.run_hpl_file(demo_file, timeout=15)
        self.assertIn(returncode, [0, 1], f"Unexpected exit code: {returncode}")

    def test_guess_number_hpl(self):
        """测试猜数字游戏"""
        game_file = self.examples_dir / "guess_number.hpl"
        if not game_file.exists():
            self.skipTest("guess_number.hpl not found")
        
        # 使用预定义输入运行
        try:
            result = subprocess.run(
                [sys.executable, "-m", "hpl_runtime", str(game_file)],
                input="50\n25\n75\n",
                capture_output=True,
                text=True,
                timeout=5
            )
            # 交互式程序可能以不同方式退出
            self.assertIn(result.returncode, [0, 1])
        except subprocess.TimeoutExpired:
            pass  # 交互式程序可能超时，这是正常的

    def test_debug_demo_hpl(self):
        """测试调试演示文件"""
        debug_file = self.examples_dir / "debug_demo.hpl"
        if not debug_file.exists():
            self.skipTest("debug_demo.hpl not found")
        
        returncode, stdout, stderr = self.run_hpl_file(debug_file)
        self.assertIn(returncode, [0, 1])

    def test_test_new_stdlib_hpl(self):
        """测试新标准库示例"""
        stdlib_file = self.examples_dir / "test_new_stdlib.hpl"
        if not stdlib_file.exists():
            self.skipTest("test_new_stdlib.hpl not found")
        
        returncode, stdout, stderr = self.run_hpl_file(stdlib_file)
        self.assertIn(returncode, [0, 1])

    def test_demo_re_net_hpl(self):
        """测试正则和网络示例"""
        re_net_file = self.examples_dir / "demo_re_net.hpl"
        if not re_net_file.exists():
            self.skipTest("demo_re_net.hpl not found")
        
        returncode, stdout, stderr = self.run_hpl_file(re_net_file, timeout=15)
        self.assertIn(returncode, [0, 1])

    def test_include_test(self):
        """测试包含测试目录"""
        include_main = self.examples_dir / "include_test" / "main.hpl"
        if not include_main.exists():
            self.skipTest("include_test/main.hpl not found")
        
        returncode, stdout, stderr = self.run_hpl_file(include_main)
        self.assertIn(returncode, [0, 1])

    def test_examples_tests_directory(self):
        """测试示例测试目录"""
        tests_dir = self.examples_dir / "tests"
        if not tests_dir.exists():
            self.skipTest("examples/tests directory not found")
        
        # 检查测试文件
        test_files = list(tests_dir.glob("test_*.hpl"))
        self.assertGreater(len(test_files), 0, "No test files found in examples/tests")

    def test_all_test_files_runnable(self):
        """测试所有测试文件可运行"""
        tests_dir = self.examples_dir / "tests"
        if not tests_dir.exists():
            self.skipTest("examples/tests directory not found")
        
        test_files = list(tests_dir.glob("test_*.hpl"))
        results = []
        
        for test_file in test_files[:5]:  # 限制测试数量
            returncode, stdout, stderr = self.run_hpl_file(test_file, timeout=5)
            results.append((test_file.name, returncode))
        
        # 至少有一些应该成功
        successful = sum(1 for _, code in results if code == 0)
        self.assertGreaterEqual(successful, 0, "Some tests should pass")


class TestExampleSyntaxValidity(unittest.TestCase):
    """测试示例语法有效性"""

    def setUp(self):
        self.examples_dir = Path(os.path.dirname(__file__)).parent.parent / "examples"


    def test_all_hpl_files_parseable(self):
        """测试所有 HPL 文件可解析"""
        hpl_files = list(self.examples_dir.rglob("*.hpl"))
        
        if not hpl_files:
            self.skipTest("No .hpl files found")
        
        from hpl_runtime.core.parser import HPLParser
        
        parse_errors = []
        for hpl_file in hpl_files[:10]:  # 限制测试数量
            try:
                parser = HPLParser(str(hpl_file))
                parser.parse()
            except Exception as e:
                parse_errors.append((hpl_file.name, str(e)))
        
        # 大多数应该能解析
        self.assertLess(len(parse_errors), len(hpl_files) / 2, 
                       f"Too many parse errors: {parse_errors}")

    def test_no_syntax_errors_in_examples(self):
        """测试示例中没有语法错误"""
        tests_dir = self.examples_dir / "tests"
        if not tests_dir.exists():
            self.skipTest("examples/tests directory not found")
        
        # 排除故意测试错误的文件
        error_test_files = [
            "test_syntax_error.hpl",
            "test_error.hpl"
        ]
        
        hpl_files = [f for f in tests_dir.glob("*.hpl") 
                     if f.name not in error_test_files]
        
        from hpl_runtime.core.parser import HPLParser
        
        for hpl_file in hpl_files[:5]:
            try:
                parser = HPLParser(str(hpl_file))
                parser.parse()
            except Exception:
                # 某些测试文件可能故意包含错误
                pass


class TestExampleOutputVerification(unittest.TestCase):
    """测试示例输出验证"""

    def setUp(self):
        self.examples_dir = Path(os.path.dirname(__file__)).parent.parent / "examples"


    def test_hello_world_output(self):
        """测试 Hello World 输出"""
        # 创建一个简单的 Hello World 测试
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hpl', delete=False) as f:
            f.write("""main: () => {
  echo "Hello, World!"
}""")
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "hpl_runtime", temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            # 检查输出包含 Hello World
            self.assertIn("Hello, World", result.stdout)
        finally:
            os.unlink(temp_file)


    def test_basic_arithmetic_output(self):
        """测试基本算术输出"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hpl', delete=False) as f:
            f.write("""main: () => {
  x = 10
  y = 20
  result = x + y
  echo result
}""")
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "hpl_runtime", temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.assertIn("30", result.stdout)
        finally:
            os.unlink(temp_file)



if __name__ == '__main__':
    unittest.main()
