#!/usr/bin/env python3
"""
HPL 回归测试套件

确保已修复的问题不会再次出现
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
from hpl_runtime.core.models import (
    HPLClass, HPLFunction, HPLObject, BlockStatement, ReturnStatement,
    IntegerLiteral, StringLiteral, Variable, BinaryOp, IfStatement,
    AssignmentStatement, EchoStatement, FunctionCall
)
from hpl_runtime.modules.loader import _parse_hpl_module, clear_cache
from hpl_runtime.utils.exceptions import (
    HPLSyntaxError, HPLRuntimeError, HPLTypeError, HPLNameError,
    HPLDivisionError, HPLIndexError, HPLImportError
)


class TestRegressionIssues(unittest.TestCase):
    """测试已修复的问题"""

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

    def test_division_by_zero_error(self):
        """测试除零错误处理"""
        hpl_content = """divide: (a, b) => {
  return a / b
}

testDivide: () => {
  return divide(10, 0)
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_div", file_path)
        
        with self.assertRaises(HPLDivisionError) as context:
            module.call_function("testDivide", [])
        
        self.assertIn("zero", str(context.exception).lower())

    def test_array_index_out_of_bounds(self):
        """测试数组越界错误"""
        hpl_content = """getElement: (arr, index) => {
  return arr[index]
}

testOutOfBounds: () => {
  arr = [1, 2, 3]
  return getElement(arr, 5)
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_bounds", file_path)
        
        with self.assertRaises(HPLIndexError) as context:
            module.call_function("testOutOfBounds", [])
        
        self.assertIn("bounds", str(context.exception).lower())

    def test_undefined_variable_error(self):
        """测试未定义变量错误"""
        hpl_content = """testUndefined: () => {
  return undefined_var
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_undef", file_path)
        
        with self.assertRaises(HPLNameError) as context:
            module.call_function("testUndefined", [])
        
        self.assertIn("undefined", str(context.exception).lower())

    def test_type_error_on_invalid_operation(self):
        """测试无效操作的类型错误"""
        hpl_content = """testTypeError: () => {
  return "string" - 5
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_type", file_path)
        
        with self.assertRaises(HPLTypeError) as context:
            module.call_function("testTypeError", [])

    def test_import_error_handling(self):
        """测试导入错误处理"""
        hpl_content = """imports:
  - nonexistent_module_xyz

testImport: () => {
  return 0
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        
        with self.assertRaises(HPLImportError) as context:
            _parse_hpl_module("test_import", file_path)

    def test_nested_try_catch(self):
        """测试嵌套 try-catch"""
        hpl_content = """nestedTry: () => {
  try {
    try {
      throw "inner"
    } catch (e1) {
      return "caught inner"
    }
  } catch (e2) {
    return "caught outer"
  }
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_nested", file_path)
        
        result = module.call_function("nestedTry", [])
        self.assertEqual(result, "caught inner")

    def test_finally_always_executes(self):
        """测试 finally 总是执行"""
        hpl_content = """testFinally: () => {
  result = "before"
  try {
    result = "try"
    throw "error"
  } catch (e) {
    result = "catch"
  } finally {
    result = "finally"
  }
  return result
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_finally", file_path)
        
        result = module.call_function("testFinally", [])
        self.assertEqual(result, "finally")

    def test_return_in_finally(self):
        """测试 finally 中的 return"""
        hpl_content = """returnInFinally: () => {
  try {
    return "try"
  } finally {
    return "finally"
  }
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_return_finally", file_path)
        
        result = module.call_function("returnInFinally", [])
        # finally 中的 return 应该覆盖 try 中的 return
        self.assertEqual(result, "finally")

    def test_break_in_try_catch(self):
        """测试 try-catch 中的 break"""
        hpl_content = """breakInTry: () => {
  i = 0
  while (i < 10) {
    try {
      if (i == 5) {
        break
      }
    } catch (e) {
      # 不应该执行
    }
    i = i + 1
  }
  return i
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_break", file_path)
        
        result = module.call_function("breakInTry", [])
        self.assertEqual(result, 5)

    def test_continue_in_try_catch(self):
        """测试 try-catch 中的 continue"""
        hpl_content = """continueInTry: () => {
  sum = 0
  i = 0
  while (i < 5) {
    i = i + 1
    try {
      if (i == 3) {
        continue
      }
    } catch (e) {
      # 不应该执行
    }
    sum = sum + i
  }
  return sum
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_continue", file_path)
        
        result = module.call_function("continueInTry", [])
        # 1 + 2 + 4 + 5 = 12 (跳过了 3)
        self.assertEqual(result, 12)

    def test_method_call_on_null(self):
        """测试 null 上的方法调用"""
        hpl_content = """nullMethodCall: () => {
  x = null
  return x.method()
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_null", file_path)
        
        with self.assertRaises(HPLRuntimeError):
            module.call_function("nullMethodCall", [])

    def test_recursive_function_with_return(self):
        """测试带返回值的递归函数"""
        hpl_content = """factorial: (n) => {
  if (n <= 1) {
    return 1
  }
  return n * factorial(n - 1)
}

testFactorial: () => {
  return factorial(5)
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_recursion", file_path)
        
        result = module.call_function("testFactorial", [])
        self.assertEqual(result, 120)

    def test_string_concatenation_with_numbers(self):
        """测试字符串与数字拼接"""
        hpl_content = """concatTest: () => {
  return "Result: " + 42
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_concat", file_path)
        
        result = module.call_function("concatTest", [])
        self.assertEqual(result, "Result: 42")

    def test_array_concatenation(self):
        """测试数组合并"""
        hpl_content = """arrayConcat: () => {
  arr1 = [1, 2]
  arr2 = [3, 4]
  return arr1 + arr2
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_array_concat", file_path)
        
        result = module.call_function("arrayConcat", [])
        self.assertEqual(result, [1, 2, 3, 4])

    def test_dictionary_key_access(self):
        """测试字典键访问"""
        hpl_content = """dictAccess: () => {
  d = {"name": "Alice", "age": 25}
  return d["name"]
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_dict", file_path)
        
        result = module.call_function("dictAccess", [])
        self.assertEqual(result, "Alice")

    def test_dictionary_key_not_found(self):
        """测试字典键不存在"""
        hpl_content = """dictKeyNotFound: () => {
  d = {"name": "Alice"}
  return d["nonexistent"]
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_dict_key", file_path)
        
        with self.assertRaises(HPLRuntimeError):
            module.call_function("dictKeyNotFound", [])

    def test_for_in_loop_with_break(self):
        """测试带 break 的 for-in 循环"""
        hpl_content = """forInBreak: () => {
  sum = 0
  for (i in [1, 2, 3, 4, 5]) {
    if (i == 3) {
      break
    }
    sum = sum + i
  }
  return sum
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_for_break", file_path)
        
        result = module.call_function("forInBreak", [])
        self.assertEqual(result, 3)  # 1 + 2

    def test_for_in_loop_with_continue(self):
        """测试带 continue 的 for-in 循环"""
        hpl_content = """forInContinue: () => {
  sum = 0
  for (i in [1, 2, 3, 4, 5]) {
    if (i == 3) {
      continue
    }
    sum = sum + i
  }
  return sum
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_for_continue", file_path)
        
        result = module.call_function("forInContinue", [])
        self.assertEqual(result, 12)  # 1 + 2 + 4 + 5

    def test_while_loop_with_complex_condition(self):
        """测试复杂条件的 while 循环"""
        hpl_content = """whileComplex: () => {
  i = 0
  j = 10
  while (i < 5 && j > 5) {
    i = i + 1
    j = j - 1
  }
  return i + j
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_while", file_path)
        
        result = module.call_function("whileComplex", [])
        self.assertEqual(result, 10)  # i=5, j=5

    def test_logical_operators_short_circuit(self):
        """测试逻辑运算符短路求值"""
        # 测试 && 运算符短路：如果左操作数为false，右操作数不应被求值
        # 使用类来跟踪副作用，避免全局变量问题
        hpl_content = """classes:
  Tracker:
    init: () => {
      this.value = 0
    }
    set: (v) => {
      this.value = v
      return v
    }
    get: () => {
      return this.value
    }

shortCircuitAnd: () => {
  t = Tracker()
  result = false && t.set(1)
  return [result, t.get()]
}

shortCircuitOr: () => {
  t = Tracker()
  result = true || t.set(1)
  return [result, t.get()]
}

noShortCircuitAnd: () => {
  t = Tracker()
  result = true && t.set(1)
  return [result, t.get()]
}

noShortCircuitOr: () => {
  t = Tracker()
  result = false || t.set(1)
  return [result, t.get()]
}
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_short_circuit", file_path)
        
        # && 短路：false && ... 不会执行右侧
        result = module.call_function("shortCircuitAnd", [])
        self.assertEqual(result, [False, 0])  # value保持为0，说明右侧未执行
        
        # || 短路：true || ... 不会执行右侧
        result = module.call_function("shortCircuitOr", [])
        self.assertEqual(result, [True, 0])  # value保持为0，说明右侧未执行
        
        # && 不短路：true && ... 会执行右侧
        result = module.call_function("noShortCircuitAnd", [])
        self.assertEqual(result, [1, 1])  # value变为1，说明右侧执行了
        
        # || 不短路：false || ... 会执行右侧
        result = module.call_function("noShortCircuitOr", [])
        self.assertEqual(result, [1, 1])  # value变为1，说明右侧执行了





    def test_postfix_increment_return_value(self):
        """测试后缀自增返回值"""
        hpl_content = """postfixTest: () => {
  x = 5
  y = x++
  return [x, y]
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_postfix", file_path)
        
        result = module.call_function("postfixTest", [])
        self.assertEqual(result, [6, 5])  # x=6, y=5 (返回旧值)

    def test_prefix_increment(self):
        """测试前缀自增"""
        hpl_content = """prefixTest: () => {
  x = 5
  y = ++x
  return [x, y]
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_prefix", file_path)
        
        result = module.call_function("prefixTest", [])
        self.assertEqual(result, [6, 6])  # x=6, y=6 (返回新值)

    def test_multiple_catch_clauses(self):
        """测试多个 catch 子句 - 简化版本"""
        hpl_content = """multiCatch: (errorType) => {
  try {
    if (errorType == "type") {
      throw "TypeError"
    } else {
      throw "OtherError"
    }
  } catch (e) {
    return "caught: " + e
  }
}

testMultiCatch: () => {
  return multiCatch("type")
}
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_multi_catch", file_path)
        
        result = module.call_function("testMultiCatch", [])
        # 验证捕获到了错误，错误消息中包含 TypeError
        self.assertIn("TypeError", str(result))
        self.assertTrue(str(result).startswith("caught:"))



    def test_arrow_function_closure(self):
        """测试箭头函数闭包"""
        hpl_content = """closureTest: () => {
  x = 10
  addX = (y) => {
    return x + y
  }
  return addX(5)
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_closure", file_path)
        
        result = module.call_function("closureTest", [])
        self.assertEqual(result, 15)

    def test_class_method_with_this(self):
        """测试类方法中的 this"""
        hpl_content = """classes:
  Counter:
    init: () => {
      this.count = 0
    }
    increment: () => {
      this.count = this.count + 1
      return this.count
    }

classThisTest: () => {
  c = Counter()
  c.increment()
  c.increment()
  return c.increment()
}
"""

        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_this", file_path)
        
        result = module.call_function("classThisTest", [])
        self.assertEqual(result, 3)


if __name__ == '__main__':
    unittest.main()
