#!/usr/bin/env python3
"""
HPL 文本处理工具模块单元测试

测试 text_utils.py 中的所有文本处理函数
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
from hpl_runtime.utils.text_utils import (
    skip_whitespace, skip_comment, strip_inline_comment,
    preprocess_functions, parse_call_expression, extract_function_info
)


class TestSkipWhitespace(unittest.TestCase):
    """测试跳过空白字符函数"""

    def test_skip_whitespace_basic(self):
        """测试基本空白跳过"""
        text = "   hello"
        result = skip_whitespace(text, 0)
        self.assertEqual(result, 3)

    def test_skip_whitespace_with_newline(self):
        """测试不跳过换行符"""
        text = "   \nhello"
        result = skip_whitespace(text, 0, skip_newline=False)
        self.assertEqual(result, 3)  # 停在换行符前

    def test_skip_whitespace_skip_newline(self):
        """测试跳过换行符"""
        text = "   \nhello"
        result = skip_whitespace(text, 0, skip_newline=True)
        self.assertEqual(result, 4)  # 跳过换行符

    def test_skip_whitespace_no_whitespace(self):
        """测试无空白字符"""
        text = "hello"
        result = skip_whitespace(text, 0)
        self.assertEqual(result, 0)

    def test_skip_whitespace_end_of_string(self):
        """测试字符串末尾"""
        text = "   "
        result = skip_whitespace(text, 0)
        self.assertEqual(result, 3)

    def test_skip_whitespace_from_middle(self):
        """测试从中间位置开始"""
        text = "hello   world"
        result = skip_whitespace(text, 5)
        self.assertEqual(result, 8)


class TestSkipComment(unittest.TestCase):
    """测试跳过注释函数"""

    def test_skip_comment_basic(self):
        """测试基本注释跳过"""
        text = "# this is a comment\nnext line"
        result = skip_comment(text, 0)
        self.assertEqual(result, 19)  # 停在换行符位置


    def test_skip_comment_end_of_string(self):
        """测试字符串末尾的注释"""
        text = "# this is a comment"
        result = skip_comment(text, 0)
        self.assertEqual(result, 19)  # 停在字符串末尾

    def test_skip_comment_empty_comment(self):
        """测试空注释"""
        text = "#\nnext line"
        result = skip_comment(text, 0)
        self.assertEqual(result, 1)

    def test_skip_comment_custom_char(self):
        """测试自定义注释字符"""
        text = "// this is a comment\nnext line"
        result = skip_comment(text, 0, comment_char='/')
        self.assertEqual(result, 20)



class TestStripInlineComment(unittest.TestCase):
    """测试移除内联注释函数"""

    def test_strip_inline_comment_basic(self):
        """测试基本内联注释移除"""
        line = "x = 5  # this is a comment"
        result = strip_inline_comment(line)
        self.assertEqual(result, "x = 5")

    def test_strip_inline_comment_no_comment(self):
        """测试无注释的行"""
        line = "x = 5"
        result = strip_inline_comment(line)
        self.assertEqual(result, "x = 5")

    def test_strip_inline_comment_in_string(self):
        """测试字符串中的#不被视为注释"""
        line = 'x = "hello # world"  # real comment'
        result = strip_inline_comment(line)
        self.assertEqual(result, 'x = "hello # world"')

    def test_strip_inline_comment_only_comment(self):
        """测试只有注释的行"""
        line = "# only comment"
        result = strip_inline_comment(line)
        self.assertEqual(result, "")

    def test_strip_inline_comment_empty_string(self):
        """测试空字符串"""
        line = ""
        result = strip_inline_comment(line)
        self.assertEqual(result, "")

    def test_strip_inline_comment_escaped_quote(self):
        """测试转义引号"""
        line = r'x = "say \"hello\""  # comment'
        result = strip_inline_comment(line)
        self.assertEqual(result, r'x = "say \"hello\""')

    def test_strip_inline_comment_single_quotes(self):
        """测试单引号字符串"""
        line = "x = 'hello # world'  # comment"
        result = strip_inline_comment(line)
        self.assertEqual(result, "x = 'hello # world'")


class TestPreprocessFunctions(unittest.TestCase):
    """测试函数预处理函数"""

    def test_preprocess_simple_function(self):
        """测试简单函数预处理"""
        content = """main: () => {
  echo "hello"
}"""
        result = preprocess_functions(content)
        self.assertIn("main: |", result)
        self.assertIn("() => {", result)

    def test_preprocess_function_with_params(self):
        """测试带参数的函数预处理"""
        content = """add: (x, y) => {
  return x + y
}"""
        result = preprocess_functions(content)
        self.assertIn("add: |", result)
        self.assertIn("(x, y) => {", result)

    def test_preprocess_no_function(self):
        """测试无函数定义的内容"""
        content = """x = 5
y = 10"""
        result = preprocess_functions(content)
        self.assertEqual(result, content)

    def test_preprocess_multiple_functions(self):
        """测试多个函数预处理"""
        content = """add: (x, y) => {
  return x + y
}

sub: (x, y) => {
  return x - y
}"""
        result = preprocess_functions(content)
        self.assertIn("add: |", result)
        self.assertIn("sub: |", result)

    def test_preprocess_nested_braces(self):
        """测试嵌套花括号"""
        content = """outer: () => {
  if (true) {
    echo "nested"
  }
}"""
        result = preprocess_functions(content)
        self.assertIn("outer: |", result)


class TestParseCallExpression(unittest.TestCase):
    """测试解析call表达式函数"""

    def test_parse_call_with_no_args(self):
        """测试无参数调用"""
        func_name, args = parse_call_expression("main")
        self.assertEqual(func_name, "main")
        self.assertEqual(args, [])

    def test_parse_call_with_args(self):
        """测试带参数调用"""
        func_name, args = parse_call_expression("add(5, 3)")
        self.assertEqual(func_name, "add")
        self.assertEqual(args, [5, 3])

    def test_parse_call_with_string_args(self):
        """测试字符串参数"""
        func_name, args = parse_call_expression('print("hello")')
        self.assertEqual(func_name, "print")
        self.assertEqual(args, ["hello"])

    def test_parse_call_with_float_args(self):
        """测试浮点数参数"""
        func_name, args = parse_call_expression("calc(3.14, 2.5)")
        self.assertEqual(func_name, "calc")
        self.assertEqual(args, [3.14, 2.5])

    def test_parse_call_with_spaces(self):
        """测试带空格的表达式"""
        func_name, args = parse_call_expression("  add( 5 , 3 )  ")
        self.assertEqual(func_name, "add")
        self.assertEqual(args, [5, 3])

    def test_parse_call_empty_parens(self):
        """测试空括号"""
        func_name, args = parse_call_expression("main()")
        self.assertEqual(func_name, "main")
        self.assertEqual(args, [])


class TestExtractFunctionInfo(unittest.TestCase):
    """测试提取函数信息函数"""

    def test_extract_simple_function(self):
        """测试简单函数"""
        func_str = "(x, y) => { return x + y }"
        params, body = extract_function_info(func_str)
        self.assertEqual(params, ["x", "y"])
        self.assertEqual(body, "return x + y")

    def test_extract_no_params(self):
        """测试无参数函数"""
        func_str = "() => { echo 'hello' }"
        params, body = extract_function_info(func_str)
        self.assertEqual(params, [])
        self.assertEqual(body, "echo 'hello'")

    def test_extract_single_param(self):
        """测试单参数函数"""
        func_str = "(x) => { return x * 2 }"
        params, body = extract_function_info(func_str)
        self.assertEqual(params, ["x"])
        self.assertEqual(body, "return x * 2")

    def test_extract_with_spaces(self):
        """测试带空格的函数定义"""
        func_str = "( x , y ) => { return x + y }"
        params, body = extract_function_info(func_str)
        self.assertEqual(params, ["x", "y"])
        self.assertEqual(body, "return x + y")

    def test_extract_missing_arrow(self):
        """测试缺少箭头抛出异常"""
        func_str = "(x, y) { return x + y }"
        with self.assertRaises(ValueError) as context:
            extract_function_info(func_str)
        self.assertIn("=> not found", str(context.exception))

    def test_extract_missing_braces(self):
        """测试缺少花括号抛出异常"""
        func_str = "(x, y) => return x + y"
        with self.assertRaises(ValueError) as context:
            extract_function_info(func_str)
        self.assertIn("braces not found", str(context.exception))


if __name__ == '__main__':
    unittest.main()
