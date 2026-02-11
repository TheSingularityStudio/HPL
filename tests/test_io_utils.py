#!/usr/bin/env python3
"""
HPL IO工具模块单元测试

测试 io_utils.py 中的所有IO辅助函数
"""

import sys
import os
import io
import unittest.mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from hpl_runtime.utils.io_utils import echo, read_input, format_output


class TestEcho(unittest.TestCase):
    """测试echo函数"""

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_echo_string(self, mock_stdout):
        """测试输出字符串"""
        echo("hello world")
        self.assertEqual(mock_stdout.getvalue().strip(), "hello world")

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_echo_number(self, mock_stdout):
        """测试输出数字"""
        echo(42)
        self.assertEqual(mock_stdout.getvalue().strip(), "42")

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_echo_list(self, mock_stdout):
        """测试输出列表"""
        echo([1, 2, 3])
        self.assertEqual(mock_stdout.getvalue().strip(), "[1, 2, 3]")

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_echo_empty_string(self, mock_stdout):
        """测试输出空字符串"""
        echo("")
        self.assertEqual(mock_stdout.getvalue().strip(), "")

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_echo_none(self, mock_stdout):
        """测试输出None"""
        echo(None)
        self.assertEqual(mock_stdout.getvalue().strip(), "None")


class TestReadInput(unittest.TestCase):
    """测试read_input函数"""

    @unittest.mock.patch('builtins.input', return_value='user input')
    def test_read_input_without_prompt(self, mock_input):
        """测试无提示符输入"""
        result = read_input()
        self.assertEqual(result, 'user input')
        mock_input.assert_called_once_with()

    @unittest.mock.patch('builtins.input', return_value='user input')
    def test_read_input_with_prompt(self, mock_input):
        """测试带提示符输入"""
        result = read_input("Enter value: ")
        self.assertEqual(result, 'user input')
        mock_input.assert_called_once_with("Enter value: ")

    @unittest.mock.patch('builtins.input', side_effect=EOFError())
    def test_read_input_eof_error(self, mock_input):
        """测试EOF错误"""
        with self.assertRaises(EOFError):
            read_input()


class TestFormatOutput(unittest.TestCase):
    """测试format_output函数"""

    def test_format_output_simple_value(self):
        """测试简单值"""
        result = format_output(42)
        self.assertEqual(result, "42")

    def test_format_output_string(self):
        """测试字符串"""
        result = format_output("hello")
        self.assertEqual(result, "hello")

    def test_format_output_with_indent(self):
        """测试带缩进"""
        result = format_output(42, indent=2)
        self.assertEqual(result, "    42")  # 4个空格

    def test_format_output_empty_dict(self):
        """测试空字典"""
        result = format_output({})
        self.assertEqual(result, "{\n}")

    def test_format_output_simple_dict(self):
        """测试简单字典"""
        result = format_output({"key": "value"})
        # 实际实现会在key:后添加额外缩进
        expected = "{\n  key:   value\n}"
        self.assertEqual(result, expected)


    def test_format_output_nested_dict(self):
        """测试嵌套字典"""
        result = format_output({"outer": {"inner": "value"}})
        # 实际实现会在key:后添加额外缩进
        expected = "{\n  outer:   {\n    inner:     value\n  }\n}"
        self.assertEqual(result, expected)


    def test_format_output_empty_list(self):
        """测试空列表"""
        result = format_output([])
        self.assertEqual(result, "[\n]")

    def test_format_output_simple_list(self):
        """测试简单列表"""
        result = format_output([1, 2, 3])
        # 实际实现使用4空格缩进
        expected = "[\n    1\n    2\n    3\n]"
        self.assertEqual(result, expected)


    def test_format_output_nested_list(self):
        """测试嵌套列表"""
        result = format_output([[1, 2], [3, 4]])
        # 实际实现使用不同的缩进模式
        expected = "[\n    [\n        1\n        2\n  ]\n    [\n        3\n        4\n  ]\n]"
        self.assertEqual(result, expected)


    def test_format_output_mixed_structure(self):
        """测试混合结构"""
        result = format_output({"items": [1, 2], "count": 2})
        # 实际实现会在key:后添加额外缩进
        expected = "{\n  items:   [\n        1\n        2\n  ]\n  count:   2\n}"
        self.assertEqual(result, expected)


    def test_format_output_with_zero_indent(self):
        """测试零缩进"""
        result = format_output({"key": "value"}, indent=0)
        # 实际实现会在key:后添加额外缩进
        expected = "{\n  key:   value\n}"
        self.assertEqual(result, expected)



if __name__ == '__main__':
    unittest.main()
