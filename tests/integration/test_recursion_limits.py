#!/usr/bin/env python3
"""
HPL 递归限制测试

测试递归深度限制、栈溢出保护等运行时安全特性
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
import tempfile
import shutil
from pathlib import Path

from hpl_runtime.core.parser import HPLParser
from hpl_runtime.core.evaluator import HPLEvaluator
from hpl_runtime.core.models import HPLClass, HPLFunction, BlockStatement, ReturnStatement, IntegerLiteral, BinaryOp, Variable, IfStatement, AssignmentStatement
from hpl_runtime.modules.loader import _parse_hpl_module, clear_cache
from hpl_runtime.utils.exceptions import HPLRecursionError, HPLRuntimeError


class TestRecursionLimits(unittest.TestCase):
    """测试递归深度限制"""

    def setUp(self):
        """测试前准备"""
        clear_cache()
        self.temp_dirs = []

    def tearDown(self):
        """清理临时目录"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def create_temp_hpl_file(self, content, filename="test.hpl"):
        """创建临时 HPL 文件"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        file_path = Path(temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path), temp_dir

    def test_infinite_recursion_detection(self):
        """测试无限递归检测"""
        hpl_content = """functions:
  infinite: () => {
    return infinite()
  }

  testInfinite: () => {
    return infinite()
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_infinite", file_path)
        
        self.assertIsNotNone(module)
        
        # 应该抛出递归错误
        with self.assertRaises(HPLRecursionError) as context:
            module.call_function("testInfinite", [])
        
        self.assertIn("recursion", str(context.exception).lower())

    def test_deep_recursion_limit(self):
        """测试深层递归限制"""
        hpl_content = """functions:
  deep: (n) => {
    if (n <= 0) {
      return 0
    }
    return deep(n - 1) + 1
  }

  testDeep: () => {
    return deep(10000)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_deep", file_path)
        
        self.assertIsNotNone(module)
        
        # 非常深的递归应该触发限制
        with self.assertRaises(HPLRecursionError):
            module.call_function("testDeep", [])

    def test_mutual_recursion(self):
        """测试相互递归"""
        hpl_content = """functions:
  even: (n) => {
    if (n == 0) {
      return true
    }
    return odd(n - 1)
  }

  odd: (n) => {
    if (n == 0) {
      return false
    }
    return even(n - 1)
  }

  testMutual: () => {
    return even(5)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_mutual", file_path)
        
        self.assertIsNotNone(module)
        
        # 相互递归在合理深度应该工作
        result = module.call_function("testMutual", [])
        self.assertFalse(result)  # 5 是奇数

    def test_safe_recursion_depth(self):
        """测试安全递归深度"""
        hpl_content = """functions:
  factorial: (n) => {
    if (n <= 1) {
      return 1
    }
    return n * factorial(n - 1)
  }

  testFactorial: () => {
    return factorial(10)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_factorial", file_path)
        
        self.assertIsNotNone(module)
        
        # 10层递归应该安全
        result = module.call_function("testFactorial", [])
        self.assertEqual(result, 3628800)  # 10!

    def test_tail_call_recursion(self):
        """测试尾递归（如果优化）"""
        hpl_content = """functions:
  sumHelper: (n, acc) => {
    if (n <= 0) {
      return acc
    }
    return sumHelper(n - 1, acc + n)
  }

  sum: (n) => {
    return sumHelper(n, 0)
  }

  testSum: () => {
    return sum(100)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_tail", file_path)
        
        self.assertIsNotNone(module)
        
        # 尾递归形式应该能处理较大深度
        result = module.call_function("testSum", [])
        self.assertEqual(result, 5050)  # 1+2+...+100

    def test_recursive_method_calls(self):
        """测试递归方法调用"""
        hpl_content = """classes:
  TreeNode:
    init: (value) => {
      this.value = value
      this.left = null
      this.right = null
    }
    
    setLeft: (node) => {
      this.left = node
    }
    
    setRight: (node) => {
      this.right = node
    }
    
    sum: () => {
      total = this.value
      if (this.left != null) {
        total = total + this.left.sum()
      }
      if (this.right != null) {
        total = total + this.right.sum()
      }
      return total
    }

functions:
  testTreeSum: () => {
    root = TreeNode(10)
    left = TreeNode(5)
    right = TreeNode(15)
    root.setLeft(left)
    root.setRight(right)
    return root.sum()
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_tree", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testTreeSum", [])
        self.assertEqual(result, 30)

    def test_nested_function_recursion(self):
        """测试嵌套函数递归"""
        hpl_content = """functions:
  outer: (n) => {
    inner: (m) => {
      if (m <= 0) {
        return 0
      }
      return inner(m - 1) + 1
    }
    return inner(n)
  }

  testNested: () => {
    return outer(5)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_nested", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testNested", [])
        self.assertEqual(result, 5)

    def test_call_stack_tracking(self):
        """测试调用栈跟踪"""
        hpl_content = """functions:
  a: () => {
    return b()
  }
  
  b: () => {
    return c()
  }
  
  c: () => {
    return d()
  }
  
  d: () => {
    return 42
  }

  testStack: () => {
    return a()
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_stack", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testStack", [])
        self.assertEqual(result, 42)

    def test_recursion_with_exception(self):
        """测试递归中的异常处理"""
        hpl_content = """functions:
  risky: (n) => {
    if (n == 0) {
      throw "Base case reached"
    }
    try {
      return risky(n - 1)
    } catch (e) {
      return "caught at " + n
    }
  }

  testRisky: () => {
    return risky(3)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_risky", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testRisky", [])
        self.assertEqual(result, "caught at 1")


class TestStackOverflowPrevention(unittest.TestCase):
    """测试栈溢出预防"""

    def setUp(self):
        clear_cache()
        self.temp_dirs = []

    def tearDown(self):
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def create_temp_hpl_file(self, content, filename="test.hpl"):
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        file_path = Path(temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path), temp_dir

    def test_very_deep_recursion_fails_gracefully(self):
        """测试极深递归优雅失败"""
        hpl_content = """functions:
  deep: (n) => {
    if (n <= 0) {
      return 0
    }
    return 1 + deep(n - 1)
  }

  testVeryDeep: () => {
    return deep(100000)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_very_deep", file_path)
        
        self.assertIsNotNone(module)
        
        # 应该抛出递归错误而不是崩溃
        with self.assertRaises(HPLRecursionError) as context:
            module.call_function("testVeryDeep", [])
        
        error_msg = str(context.exception)
        self.assertIn("recursion", error_msg.lower())
        # 应该包含有用的提示
        self.assertIn("depth", error_msg.lower())

    def test_circular_call_detection(self):
        """测试循环调用检测"""
        hpl_content = """functions:
  a: () => {
    return b()
  }
  
  b: () => {
    return c()
  }
  
  c: () => {
    return a()  # 循环回到 a
  }

  testCircular: () => {
    return a()
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_circular", file_path)
        
        self.assertIsNotNone(module)
        
        with self.assertRaises(HPLRecursionError):
            module.call_function("testCircular", [])


if __name__ == '__main__':
    unittest.main()
