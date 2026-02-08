#!/usr/bin/env python3
"""
HPL 测试运行器
运行所有单元测试和集成测试
"""

import sys
import os
import unittest

# 添加 hpl_runtime 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hpl_runtime'))

def run_tests():
    """运行所有测试"""
    # 发现所有测试
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
