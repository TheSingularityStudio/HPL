#!/usr/bin/env python3
"""
HPL 解析辅助工具模块单元测试

测试 parse_utils.py 中的所有解析辅助函数
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from hpl_runtime.utils.parse_utils import (
    get_token_position, is_block_terminator, consume_indent, skip_dedents,
    find_matching_brace, extract_params_from_signature
)


class MockToken:
    """模拟Token对象用于测试"""
    def __init__(self, type_, value=None, line=None, column=None):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column


class TestGetTokenPosition(unittest.TestCase):
    """测试获取token位置函数"""

    def test_get_token_position_with_valid_token(self):
        """测试有效token"""
        token = MockToken('IDENTIFIER', 'x', line=10, column=5)
        line, col = get_token_position(token)
        self.assertEqual(line, 10)
        self.assertEqual(col, 5)

    def test_get_token_position_with_none(self):
        """测试None token"""
        line, col = get_token_position(None)
        self.assertIsNone(line)
        self.assertIsNone(col)

    def test_get_token_position_without_position(self):
        """测试没有位置信息的token"""
        token = MockToken('IDENTIFIER', 'x')
        line, col = get_token_position(token)
        self.assertIsNone(line)
        self.assertIsNone(col)


class TestIsBlockTerminator(unittest.TestCase):
    """测试块终止符检查函数"""

    def test_is_block_terminator_with_none(self):
        """测试None token"""
        result = is_block_terminator(None)
        self.assertTrue(result)

    def test_is_block_terminator_with_rbrace(self):
        """测试右花括号"""
        token = MockToken('RBRACE', '}')
        result = is_block_terminator(token)
        self.assertTrue(result)

    def test_is_block_terminator_with_eof(self):
        """测试EOF"""
        token = MockToken('EOF', None)
        result = is_block_terminator(token)
        self.assertTrue(result)

    def test_is_block_terminator_with_dedent_lower_indent(self):
        """测试缩进减少的DEDENT"""
        token = MockToken('DEDENT', 0)  # value表示新的缩进级别
        result = is_block_terminator(token, indent_level=2)
        self.assertTrue(result)

    def test_is_block_terminator_with_dedent_same_indent(self):
        """测试相同缩进级别的DEDENT"""
        token = MockToken('DEDENT', 2)
        result = is_block_terminator(token, indent_level=2)
        self.assertTrue(result)

    def test_is_block_terminator_with_dedent_higher_indent(self):
        """测试更高缩进级别的DEDENT（不应该终止）"""
        token = MockToken('DEDENT', 4)
        result = is_block_terminator(token, indent_level=2)
        # 如果新缩进级别更高，不应该终止
        self.assertFalse(result)

    def test_is_block_terminator_with_dedent_no_value(self):
        """测试没有value的DEDENT"""
        token = MockToken('DEDENT', None)
        result = is_block_terminator(token, indent_level=2)
        # 没有value时保守地视为终止符
        self.assertTrue(result)

    def test_is_block_terminator_with_else(self):
        """测试else关键字"""
        token = MockToken('KEYWORD', 'else')
        result = is_block_terminator(token)
        self.assertTrue(result)

    def test_is_block_terminator_with_catch(self):
        """测试catch关键字"""
        token = MockToken('KEYWORD', 'catch')
        result = is_block_terminator(token)
        self.assertTrue(result)

    def test_is_block_terminator_with_regular_token(self):
        """测试普通token不是终止符"""
        token = MockToken('IDENTIFIER', 'x')
        result = is_block_terminator(token)
        self.assertFalse(result)


class TestConsumeIndent(unittest.TestCase):
    """测试消费INDENT token函数"""

    def test_consume_indent_with_indent(self):
        """测试消费INDENT"""
        tokens = [MockToken('INDENT', None), MockToken('IDENTIFIER', 'x')]
        result = consume_indent(tokens, 0)
        self.assertEqual(result, 1)

    def test_consume_indent_without_indent(self):
        """测试没有INDENT"""
        tokens = [MockToken('IDENTIFIER', 'x'), MockToken('NUMBER', 5)]
        result = consume_indent(tokens, 0)
        self.assertEqual(result, 0)

    def test_consume_indent_at_end(self):
        """测试在列表末尾"""
        tokens = [MockToken('INDENT', None)]
        result = consume_indent(tokens, 0)
        self.assertEqual(result, 1)

    def test_consume_indent_position_not_indent(self):
        """测试当前位置不是INDENT"""
        tokens = [MockToken('IDENTIFIER', 'x'), MockToken('INDENT', None)]
        result = consume_indent(tokens, 0)
        self.assertEqual(result, 0)


class TestSkipDedents(unittest.TestCase):
    """测试跳过DEDENT token函数"""

    def test_skip_dedents_with_multiple(self):
        """测试跳过多个DEDENT"""
        tokens = [
            MockToken('DEDENT', None),
            MockToken('DEDENT', None),
            MockToken('IDENTIFIER', 'x')
        ]
        result = skip_dedents(tokens, 0)
        self.assertEqual(result, 2)

    def test_skip_dedents_with_no_dedent(self):
        """测试没有DEDENT"""
        tokens = [MockToken('IDENTIFIER', 'x'), MockToken('NUMBER', 5)]
        result = skip_dedents(tokens, 0)
        self.assertEqual(result, 0)

    def test_skip_dedents_mixed(self):
        """测试混合token"""
        tokens = [
            MockToken('DEDENT', None),
            MockToken('IDENTIFIER', 'x'),
            MockToken('DEDENT', None)
        ]
        result = skip_dedents(tokens, 0)
        # 只跳过开头的DEDENT
        self.assertEqual(result, 1)

    def test_skip_dedents_all_dedents(self):
        """测试全是DEDENT"""
        tokens = [MockToken('DEDENT', None), MockToken('DEDENT', None)]
        result = skip_dedents(tokens, 0)
        self.assertEqual(result, 2)


class TestFindMatchingBrace(unittest.TestCase):
    """测试查找匹配括号函数"""

    def test_find_matching_brace_simple(self):
        """测试简单匹配"""
        text = "{content}"
        result = find_matching_brace(text, 0)
        self.assertEqual(result, 8)

    def test_find_matching_brace_nested(self):
        """测试嵌套括号"""
        text = "{outer{inner}end}"
        result = find_matching_brace(text, 0)
        self.assertEqual(result, 16)

    def test_find_matching_brace_deeply_nested(self):
        """测试深度嵌套"""
        text = "{a{b{c}d}e}"
        result = find_matching_brace(text, 0)
        self.assertEqual(result, 10)

    def test_find_matching_brace_not_found(self):
        """测试未找到匹配"""
        text = "{content"
        result = find_matching_brace(text, 0)
        self.assertEqual(result, -1)

    def test_find_matching_brace_empty(self):
        """测试空括号"""
        text = "{}"
        result = find_matching_brace(text, 0)
        self.assertEqual(result, 1)

    def test_find_matching_brace_from_middle(self):
        """测试从中间开始"""
        text = "prefix{content}suffix"
        result = find_matching_brace(text, 6)
        self.assertEqual(result, 14)

    def test_find_matching_brace_custom_chars(self):
        """测试自定义括号字符"""
        text = "[item1,item2]"
        result = find_matching_brace(text, 0, open_char='[', close_char=']')
        self.assertEqual(result, 12)


    def test_find_matching_brace_parentheses(self):
        """测试圆括号"""
        text = "(a+b)*c"
        result = find_matching_brace(text, 0, open_char='(', close_char=')')
        self.assertEqual(result, 4)


class TestExtractParamsFromSignature(unittest.TestCase):
    """测试从签名提取参数函数"""

    def test_extract_params_simple(self):
        """测试简单参数"""
        sig = "(x, y, z)"
        result = extract_params_from_signature(sig)
        self.assertEqual(result, ["x", "y", "z"])

    def test_extract_params_no_params(self):
        """测试无参数"""
        sig = "()"
        result = extract_params_from_signature(sig)
        self.assertEqual(result, [])

    def test_extract_params_single(self):
        """测试单参数"""
        sig = "(x)"
        result = extract_params_from_signature(sig)
        self.assertEqual(result, ["x"])

    def test_extract_params_with_spaces(self):
        """测试带空格的参数"""
        sig = "( x , y , z )"
        result = extract_params_from_signature(sig)
        self.assertEqual(result, ["x", "y", "z"])

    def test_extract_params_no_parens(self):
        """测试无括号"""
        sig = "x, y, z"
        result = extract_params_from_signature(sig)
        self.assertEqual(result, ["x", "y", "z"])

    def test_extract_params_empty(self):
        """测试空字符串"""
        sig = ""
        result = extract_params_from_signature(sig)
        self.assertEqual(result, [])

    def test_extract_params_with_whitespace(self):
        """测试带空白字符"""
        sig = "  (  x  ,  y  )  "
        result = extract_params_from_signature(sig)
        self.assertEqual(result, ["x", "y"])


if __name__ == '__main__':
    unittest.main()
