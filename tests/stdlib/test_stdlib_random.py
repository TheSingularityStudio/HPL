#!/usr/bin/env python3
"""
HPL Random 标准库测试

测试随机数生成功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

try:
    from hpl_runtime.stdlib.random_mod import module as random_module
    RANDOM_AVAILABLE = True
except ImportError:
    RANDOM_AVAILABLE = False


class TestRandomStdlib(unittest.TestCase):
    """测试 random 标准库"""

    def setUp(self):
        if not RANDOM_AVAILABLE:
            self.skipTest("Random module not available")

    def test_random_float(self):
        """测试随机浮点数"""
        if not RANDOM_AVAILABLE:
            return
        
        result = random_module.call_function("random", [])
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.assertLess(result, 1.0)

    def test_random_range(self):
        """测试范围内随机数"""
        if not RANDOM_AVAILABLE:
            return
        
        result = random_module.call_function("random_int", [1, 10])
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 1)
        self.assertLessEqual(result, 10)


    def test_random_choice(self):
        """测试随机选择"""
        if not RANDOM_AVAILABLE:
            return
        
        items = ["a", "b", "c", "d", "e"]
        result = random_module.call_function("choice", [items])
        self.assertIn(result, items)

    def test_random_shuffle(self):
        """测试随机打乱"""
        if not RANDOM_AVAILABLE:
            return
        
        original = [1, 2, 3, 4, 5]
        items = original.copy()
        random_module.call_function("shuffle", [items])
        
        # 打乱后应该包含相同元素
        self.assertEqual(sorted(items), sorted(original))
        # 顺序可能不同（概率极低会相同，但测试可能偶尔失败）
        # 所以只检查元素相同

    def test_random_seed(self):
        """测试随机种子"""
        if not RANDOM_AVAILABLE:
            return
        
        # 设置种子
        random_module.call_function("seed", [42])
        val1 = random_module.call_function("random", [])
        
        # 重置种子
        random_module.call_function("seed", [42])
        val2 = random_module.call_function("random", [])
        
        # 相同种子应该产生相同结果
        self.assertEqual(val1, val2)

    def test_random_uniform(self):
        """测试均匀分布随机数"""
        if not RANDOM_AVAILABLE:
            return
        
        result = random_module.call_function("random_float", [10.0, 20.0])
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 10.0)
        self.assertLessEqual(result, 20.0)


    def test_random_multiple_calls(self):
        """测试多次调用产生不同值"""
        if not RANDOM_AVAILABLE:
            return
        
        # 设置种子以确保可重复性
        random_module.call_function("seed", [123])
        
        results = []
        for _ in range(10):
            results.append(random_module.call_function("random", []))
        
        # 检查所有值不全相同
        unique_values = set(results)
        self.assertGreater(len(unique_values), 1, "Random should produce varied results")

    def test_module_has_required_functions(self):
        """测试模块包含必需的函数"""
        if not RANDOM_AVAILABLE:
            return
        
        required_functions = ['random', 'random_int', 'choice', 'shuffle', 'seed', 'random_float']
        available_functions = random_module.list_functions()
        
        for func in required_functions:
            self.assertIn(func, available_functions, f"Missing function: {func}")



if __name__ == '__main__':
    unittest.main()
