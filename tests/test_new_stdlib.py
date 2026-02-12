#!/usr/bin/env python3
"""
HPL 新标准库单元测试

测试新增的标准库模块：
- string: 字符串处理
- random: 随机数生成
- crypto: 加密哈希和编码
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hpl_runtime'))

try:
    from hpl_runtime.modules.loader import get_module, register_module
    from hpl_runtime.modules.base import HPLModule
except ImportError:
    from module_loader import get_module, register_module
    from module_base import HPLModule


class TestStringStdlib(unittest.TestCase):
    """测试 string 标准库模块"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.string_module = get_module('string')
        if cls.string_module is None:
            try:
                from hpl_runtime.stdlib import string_mod
                cls.string_module = string_mod.module
                register_module('string', cls.string_module)
            except ImportError:
                from stdlib import string_mod
                cls.string_module = string_mod.module
                register_module('string', cls.string_module)

    def test_length(self):
        """测试字符串长度"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('length', ["Hello"])
        self.assertEqual(result, 5)

    def test_split(self):
        """测试字符串分割"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('split', ["a,b,c", ","])
        self.assertEqual(result, ["a", "b", "c"])

    def test_join(self):
        """测试字符串连接"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('join', [["a", "b", "c"], "-"])
        self.assertEqual(result, "a-b-c")

    def test_replace(self):
        """测试字符串替换"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('replace', ["Hello World", "World", "HPL"])
        self.assertEqual(result, "Hello HPL")

    def test_trim(self):
        """测试字符串修剪"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('trim', ["  Hello  "])
        self.assertEqual(result, "Hello")

    def test_to_upper(self):
        """测试转大写"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('to_upper', ["hello"])
        self.assertEqual(result, "HELLO")

    def test_to_lower(self):
        """测试转小写"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('to_lower', ["HELLO"])
        self.assertEqual(result, "hello")

    def test_substring(self):
        """测试子字符串"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('substring', ["Hello HPL", 0, 5])
        self.assertEqual(result, "Hello")

    def test_index_of(self):
        """测试查找索引"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('index_of', ["Hello HPL", "HPL"])
        self.assertEqual(result, 6)

    def test_starts_with(self):
        """测试前缀检查"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('starts_with', ["Hello HPL", "Hello"])
        self.assertTrue(result)

    def test_ends_with(self):
        """测试后缀检查"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('ends_with', ["Hello HPL", "HPL"])
        self.assertTrue(result)

    def test_contains(self):
        """测试包含检查"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('contains', ["Hello HPL", "HPL"])
        self.assertTrue(result)

    def test_reverse(self):
        """测试字符串反转"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('reverse', ["HPL"])
        self.assertEqual(result, "LPH")

    def test_repeat(self):
        """测试字符串重复"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('repeat', ["HPL", 3])
        self.assertEqual(result, "HPLHPLHPL")

    def test_pad_start(self):
        """测试左侧填充"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('pad_start', ["42", 5, "0"])
        self.assertEqual(result, "00042")

    def test_pad_end(self):
        """测试右侧填充"""
        if self.string_module is None:
            self.skipTest("String module not available")
        
        result = self.string_module.call_function('pad_end', ["42", 5, "0"])
        self.assertEqual(result, "42000")


class TestRandomStdlib(unittest.TestCase):
    """测试 random 标准库模块"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.random_module = get_module('random')
        if cls.random_module is None:
            try:
                from hpl_runtime.stdlib import random_mod
                cls.random_module = random_mod.module
                register_module('random', cls.random_module)
            except ImportError:
                from stdlib import random_mod
                cls.random_module = random_mod.module
                register_module('random', cls.random_module)

    def test_random(self):
        """测试随机浮点数"""
        if self.random_module is None:
            self.skipTest("Random module not available")
        
        result = self.random_module.call_function('random', [])
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.assertLess(result, 1.0)

    def test_random_int(self):
        """测试随机整数"""
        if self.random_module is None:
            self.skipTest("Random module not available")
        
        result = self.random_module.call_function('random_int', [1, 100])
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 100)

    def test_random_float(self):
        """测试随机浮点数范围"""
        if self.random_module is None:
            self.skipTest("Random module not available")
        
        result = self.random_module.call_function('random_float', [0, 10])
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.assertLess(result, 10.0)

    def test_choice(self):
        """测试随机选择"""
        if self.random_module is None:
            self.skipTest("Random module not available")
        
        items = ["a", "b", "c"]
        result = self.random_module.call_function('choice', [items])
        self.assertIn(result, items)

    def test_shuffle(self):
        """测试数组打乱"""
        if self.random_module is None:
            self.skipTest("Random module not available")
        
        items = [1, 2, 3, 4, 5]
        result = self.random_module.call_function('shuffle', [items])
        self.assertEqual(len(result), 5)
        self.assertEqual(sorted(result), [1, 2, 3, 4, 5])

    def test_sample(self):
        """测试抽样"""
        if self.random_module is None:
            self.skipTest("Random module not available")
        
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = self.random_module.call_function('sample', [items, 3])
        self.assertEqual(len(result), 3)
        # 确保没有重复
        self.assertEqual(len(set(result)), 3)

    def test_uuid(self):
        """测试UUID生成"""
        if self.random_module is None:
            self.skipTest("Random module not available")
        
        result = self.random_module.call_function('uuid', [])
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 36)  # UUID v4 长度

    def test_random_hex(self):
        """测试随机十六进制"""
        if self.random_module is None:
            self.skipTest("Random module not available")
        
        result = self.random_module.call_function('random_hex', [16])
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 32)  # 16 bytes = 32 hex chars


class TestCryptoStdlib(unittest.TestCase):
    """测试 crypto 标准库模块"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.crypto_module = get_module('crypto')
        if cls.crypto_module is None:
            try:
                from hpl_runtime.stdlib import crypto_mod
                cls.crypto_module = crypto_mod.module
                register_module('crypto', cls.crypto_module)
            except ImportError:
                from stdlib import crypto_mod
                cls.crypto_module = crypto_mod.module
                register_module('crypto', cls.crypto_module)

    def test_md5(self):
        """测试MD5哈希"""
        if self.crypto_module is None:
            self.skipTest("Crypto module not available")
        
        result = self.crypto_module.call_function('md5', ["Hello"])
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 32)  # MD5 hex length

    def test_sha256(self):
        """测试SHA256哈希"""
        if self.crypto_module is None:
            self.skipTest("Crypto module not available")
        
        result = self.crypto_module.call_function('sha256', ["Hello"])
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)  # SHA256 hex length

    def test_hash(self):
        """测试通用哈希"""
        if self.crypto_module is None:
            self.skipTest("Crypto module not available")
        
        result = self.crypto_module.call_function('hash', ["Hello", "sha256"])
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)

    def test_hmac(self):
        """测试HMAC"""
        if self.crypto_module is None:
            self.skipTest("Crypto module not available")
        
        result = self.crypto_module.call_function('hmac', ["Hello", "secret", "sha256"])
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)

    def test_base64_encode(self):
        """测试Base64编码"""
        if self.crypto_module is None:
            self.skipTest("Crypto module not available")
        
        result = self.crypto_module.call_function('base64_encode', ["Hello"])
        self.assertIsInstance(result, str)
        # "Hello" base64 encoded is "SGVsbG8="
        self.assertEqual(result, "SGVsbG8=")

    def test_base64_decode(self):
        """测试Base64解码"""
        if self.crypto_module is None:
            self.skipTest("Crypto module not available")
        
        result = self.crypto_module.call_function('base64_decode', ["SGVsbG8="])
        self.assertEqual(result, "Hello")

    def test_url_encode(self):
        """测试URL编码"""
        if self.crypto_module is None:
            self.skipTest("Crypto module not available")
        
        result = self.crypto_module.call_function('url_encode', ["Hello World!"])
        self.assertIsInstance(result, str)
        self.assertIn("%20", result)  # Space should be encoded

    def test_url_decode(self):
        """测试URL解码"""
        if self.crypto_module is None:
            self.skipTest("Crypto module not available")
        
        result = self.crypto_module.call_function('url_decode', ["Hello%20World"])
        self.assertEqual(result, "Hello World")

    def test_secure_random_hex(self):
        """测试安全随机十六进制"""
        if self.crypto_module is None:
            self.skipTest("Crypto module not available")
        
        result = self.crypto_module.call_function('secure_random_hex', [16])
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 32)


class TestNewStdlibRegistration(unittest.TestCase):
    """测试新标准库模块注册"""

    def test_new_stdlib_modules_registered(self):
        """测试所有新标准库模块已注册"""
        new_modules = ['string', 'random', 'crypto']
        
        for name in new_modules:
            module = get_module(name)
            self.assertIsNotNone(module, f"Module '{name}' should be registered")
            self.assertIsInstance(module, HPLModule)

    def test_string_has_functions(self):
        """测试string模块包含函数"""
        string_module = get_module('string')
        if string_module:
            self.assertGreater(len(string_module.functions), 0)

    def test_random_has_functions(self):
        """测试random模块包含函数"""
        random_module = get_module('random')
        if random_module:
            self.assertGreater(len(random_module.functions), 0)

    def test_crypto_has_functions(self):
        """测试crypto模块包含函数"""
        crypto_module = get_module('crypto')
        if crypto_module:
            self.assertGreater(len(crypto_module.functions), 0)


if __name__ == '__main__':
    unittest.main()

