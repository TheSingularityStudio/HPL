#!/usr/bin/env python3
"""
HPL Crypto 标准库测试

测试加密相关功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest

try:
    from hpl_runtime.stdlib.crypto_mod import module as crypto_module
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class TestCryptoStdlib(unittest.TestCase):
    """测试 crypto 标准库"""

    def setUp(self):
        if not CRYPTO_AVAILABLE:
            self.skipTest("Crypto module not available")

    def test_md5_hash(self):
        """测试 MD5 哈希"""
        if not CRYPTO_AVAILABLE:
            return
        
        result = crypto_module.call_function("md5", ["hello"])
        self.assertEqual(result, "5d41402abc4b2a76b9719d911017c592")

    def test_sha1_hash(self):
        """测试 SHA1 哈希"""
        if not CRYPTO_AVAILABLE:
            return
        
        result = crypto_module.call_function("sha1", ["hello"])
        self.assertEqual(result, "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d")

    def test_sha256_hash(self):
        """测试 SHA256 哈希"""
        if not CRYPTO_AVAILABLE:
            return
        
        result = crypto_module.call_function("sha256", ["hello"])
        self.assertEqual(
            result,
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        )

    def test_base64_encode(self):
        """测试 Base64 编码"""
        if not CRYPTO_AVAILABLE:
            return
        
        result = crypto_module.call_function("base64_encode", ["hello"])
        self.assertEqual(result, "aGVsbG8=")

    def test_base64_decode(self):
        """测试 Base64 解码"""
        if not CRYPTO_AVAILABLE:
            return
        
        result = crypto_module.call_function("base64_decode", ["aGVsbG8="])
        self.assertEqual(result, "hello")

    def test_base64_roundtrip(self):
        """测试 Base64 往返编码解码"""
        if not CRYPTO_AVAILABLE:
            return
        
        original = "Hello, World! 你好世界"
        encoded = crypto_module.call_function("base64_encode", [original])
        decoded = crypto_module.call_function("base64_decode", [encoded])
        self.assertEqual(decoded, original)

    def test_hash_empty_string(self):
        """测试空字符串哈希"""
        if not CRYPTO_AVAILABLE:
            return
        
        md5_result = crypto_module.call_function("md5", [""])
        self.assertEqual(md5_result, "d41d8cd98f00b204e9800998ecf8427e")

    def test_hash_unicode(self):
        """测试 Unicode 字符串哈希"""
        if not CRYPTO_AVAILABLE:
            return
        
        result = crypto_module.call_function("md5", ["你好世界"])
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 32)  # MD5 长度

    def test_base64_binary_data(self):
        """测试二进制数据 Base64 编码"""
        if not CRYPTO_AVAILABLE:
            return
        
        # 测试包含特殊字符的字符串
        binary_data = bytes([0, 1, 2, 255]).decode('latin-1')
        result = crypto_module.call_function("base64_encode", [binary_data])
        self.assertIsInstance(result, str)

    def test_module_has_required_functions(self):
        """测试模块包含必需的函数"""
        if not CRYPTO_AVAILABLE:
            return
        
        required_functions = ['md5', 'sha1', 'sha256', 'base64_encode', 'base64_decode']
        available_functions = crypto_module.list_functions()
        
        for func in required_functions:
            self.assertIn(func, available_functions, f"Missing function: {func}")


if __name__ == '__main__':
    unittest.main()
