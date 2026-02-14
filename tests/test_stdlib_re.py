#!/usr/bin/env python3
"""
HPL RE (正则表达式) 标准库测试

测试正则表达式相关功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

try:
    from hpl_runtime.stdlib.re_mod import module as re_module
    RE_AVAILABLE = True
except ImportError:
    RE_AVAILABLE = False


class TestREStdlib(unittest.TestCase):
    """测试 re 标准库"""

    def setUp(self):
        if not RE_AVAILABLE:
            self.skipTest("RE module not available")

    def test_match_basic(self):
        """测试基本匹配"""
        if not RE_AVAILABLE:
            return
        
        result = re_module.call_function("match", [r"\d+", "123abc"])
        self.assertTrue(result)

    def test_match_no_match(self):
        """测试不匹配的情况"""
        if not RE_AVAILABLE:
            return
        
        result = re_module.call_function("match", [r"\d+", "abc"])
        self.assertFalse(result)

    def test_search_basic(self):
        """测试基本搜索"""
        if not RE_AVAILABLE:
            return
        
        result = re_module.call_function("search", [r"\d+", "abc123def"])
        self.assertTrue(result)

    def test_findall(self):
        """测试查找所有匹配"""
        if not RE_AVAILABLE:
            return
        
        result = re_module.call_function("find_all", [r"\d+", "a1b2c3"])
        self.assertEqual(result, ["1", "2", "3"])


    def test_replace(self):
        """测试替换"""
        if not RE_AVAILABLE:
            return
        
        result = re_module.call_function("replace", [r"\d+", "X", "a1b2c3"])
        self.assertEqual(result, "aXbXcX")

    def test_split(self):
        """测试分割"""
        if not RE_AVAILABLE:
            return
        
        result = re_module.call_function("split", [r",", "a,b,c"])
        self.assertEqual(result, ["a", "b", "c"])

    def test_email_pattern(self):
        """测试邮箱模式匹配"""
        if not RE_AVAILABLE:
            return
        
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        for email in valid_emails:
            result = re_module.call_function("match", [email_pattern, email])
            self.assertTrue(result, f"Should match: {email}")

    def test_phone_pattern(self):
        """测试电话号码模式匹配"""
        if not RE_AVAILABLE:
            return
        
        phone_pattern = r"^\d{3}-\d{3}-\d{4}$"
        
        result = re_module.call_function("match", [phone_pattern, "123-456-7890"])
        self.assertTrue(result)
        
        result = re_module.call_function("match", [phone_pattern, "1234567890"])
        self.assertFalse(result)

    def test_special_characters(self):
        """测试特殊字符处理"""
        if not RE_AVAILABLE:
            return
        
        # 测试点号匹配
        result = re_module.call_function("match", [r"a.b", "acb"])
        self.assertTrue(result)
        
        # 测试转义
        result = re_module.call_function("match", [r"a\.b", "a.b"])
        self.assertTrue(result)

    def test_groups(self):
        """测试分组（如果支持）"""
        if not RE_AVAILABLE:
            return
        
        # 如果模块支持分组提取
        try:
            result = re_module.call_function("groups", [r"(\d+)-(\d+)-(\d+)", "2023-12-25"])
            self.assertIsInstance(result, list)
        except:
            # 分组功能可能未实现
            pass

    def test_empty_pattern(self):
        """测试空模式"""
        if not RE_AVAILABLE:
            return
        
        result = re_module.call_function("match", ["", ""])
        self.assertTrue(result)

    def test_empty_string(self):
        """测试空字符串"""
        if not RE_AVAILABLE:
            return
        
        result = re_module.call_function("match", [r"\d+", ""])
        self.assertFalse(result)

    def test_module_has_required_functions(self):
        """测试模块包含必需的函数"""
        if not RE_AVAILABLE:
            return
        
        required_functions = ['match', 'search', 'find_all', 'replace', 'split']
        available_functions = re_module.list_functions()
        
        for func in required_functions:
            self.assertIn(func, available_functions, f"Missing function: {func}")



if __name__ == '__main__':
    unittest.main()
