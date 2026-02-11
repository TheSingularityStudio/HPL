#!/usr/bin/env python3
"""
HPL 类型检查工具模块单元测试

测试 type_utils.py 中的所有类型检查函数
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from hpl_runtime.utils.type_utils import (
    is_numeric, is_integer, is_string, is_boolean, is_array, is_dictionary,
    check_numeric_operands, is_hpl_module, get_type_name, is_valid_index
)
from hpl_runtime.utils.exceptions import HPLTypeError


class TestTypeCheckFunctions(unittest.TestCase):
    """测试基本类型检查函数"""

    def test_is_numeric_with_int(self):
        """测试整数是数值类型"""
        self.assertTrue(is_numeric(42))
        self.assertTrue(is_numeric(0))
        self.assertTrue(is_numeric(-100))

    def test_is_numeric_with_float(self):
        """测试浮点数是数值类型"""
        self.assertTrue(is_numeric(3.14))
        self.assertTrue(is_numeric(0.0))
        self.assertTrue(is_numeric(-2.5))

    def test_is_numeric_with_non_numeric(self):
        """测试非数值类型返回False"""
        self.assertFalse(is_numeric("42"))
        self.assertFalse(is_numeric([1, 2, 3]))
        self.assertFalse(is_numeric({"key": "value"}))
        # 注意：在Python中bool是int的子类，所以is_numeric(True)返回True
        self.assertTrue(is_numeric(True))
        self.assertFalse(is_numeric(None))


    def test_is_integer(self):
        """测试整数类型检查"""
        self.assertTrue(is_integer(42))
        self.assertTrue(is_integer(0))
        self.assertTrue(is_integer(-100))
        self.assertFalse(is_integer(3.14))
        self.assertFalse(is_integer("42"))
        # 注意：在Python中bool是int的子类，所以is_integer(True)返回True
        self.assertTrue(is_integer(True))


    def test_is_string(self):
        """测试字符串类型检查"""
        self.assertTrue(is_string("hello"))
        self.assertTrue(is_string(""))
        self.assertTrue(is_string("123"))
        self.assertFalse(is_string(123))
        self.assertFalse(is_string(["hello"]))

    def test_is_boolean(self):
        """测试布尔类型检查"""
        self.assertTrue(is_boolean(True))
        self.assertTrue(is_boolean(False))
        self.assertFalse(is_boolean(1))
        self.assertFalse(is_boolean(0))
        self.assertFalse(is_boolean("true"))

    def test_is_array(self):
        """测试数组（列表）类型检查"""
        self.assertTrue(is_array([1, 2, 3]))
        self.assertTrue(is_array([]))
        self.assertTrue(is_array(["a", "b"]))
        self.assertFalse(is_array((1, 2, 3)))  # tuple不是list
        self.assertFalse(is_array("list"))
        self.assertFalse(is_array({"key": "value"}))

    def test_is_dictionary(self):
        """测试字典类型检查"""
        self.assertTrue(is_dictionary({"key": "value"}))
        self.assertTrue(is_dictionary({}))
        self.assertTrue(is_dictionary({"a": 1, "b": 2}))
        self.assertFalse(is_dictionary([("key", "value")]))  # list不是dict
        self.assertFalse(is_dictionary("dict"))


class TestCheckNumericOperands(unittest.TestCase):
    """测试数值操作数检查"""

    def test_check_numeric_operands_with_valid_numbers(self):
        """测试有效的数值操作数不抛出异常"""
        # 应该不抛出异常
        check_numeric_operands(10, 20, '+')
        check_numeric_operands(3.14, 2.0, '*')
        check_numeric_operands(-5, 10, '-')

    def test_check_numeric_operands_with_invalid_left(self):
        """测试左操作数无效时抛出异常"""
        with self.assertRaises(HPLTypeError) as context:
            check_numeric_operands("10", 20, '+')
        self.assertIn("Unsupported operand type", str(context.exception))
        self.assertIn("str", str(context.exception))

    def test_check_numeric_operands_with_invalid_right(self):
        """测试右操作数无效时抛出异常"""
        with self.assertRaises(HPLTypeError) as context:
            check_numeric_operands(10, "20", '+')
        self.assertIn("Unsupported operand type", str(context.exception))
        self.assertIn("str", str(context.exception))

    def test_check_numeric_operands_with_both_invalid(self):
        """测试两个操作数都无效时抛出异常（先检查左操作数）"""
        with self.assertRaises(HPLTypeError) as context:
            check_numeric_operands("10", "20", '+')
        self.assertIn("Unsupported operand type", str(context.exception))


class TestIsHPLModule(unittest.TestCase):
    """测试HPL模块检查"""

    def test_is_hpl_module_with_valid_module(self):
        """测试有效的HPL模块对象"""
        class MockModule:
            def __init__(self):
                self.name = "test_module"
            def call_function(self, name, args):
                pass
            def get_constant(self, name):
                pass
        
        mock = MockModule()
        self.assertTrue(is_hpl_module(mock))

    def test_is_hpl_module_with_missing_attributes(self):
        """测试缺少必要属性的对象"""
        class MissingCallFunction:
            def get_constant(self, name):
                pass
            def name(self):
                return "test"
        
        class MissingGetConstant:
            def call_function(self, name, args):
                pass
        
        class MissingName:
            def call_function(self, name, args):
                pass
            def get_constant(self, name):
                pass
        
        self.assertFalse(is_hpl_module(MissingCallFunction()))
        self.assertFalse(is_hpl_module(MissingGetConstant()))
        self.assertFalse(is_hpl_module(MissingName()))

    def test_is_hpl_module_with_regular_object(self):
        """测试普通对象不是HPL模块"""
        self.assertFalse(is_hpl_module("string"))
        self.assertFalse(is_hpl_module(123))
        self.assertFalse(is_hpl_module({"key": "value"}))
        self.assertFalse(is_hpl_module([1, 2, 3]))


class TestGetTypeName(unittest.TestCase):
    """测试类型名称获取"""

    def test_get_type_name_boolean(self):
        """测试布尔类型名称"""
        self.assertEqual(get_type_name(True), 'boolean')
        self.assertEqual(get_type_name(False), 'boolean')

    def test_get_type_name_integer(self):
        """测试整数类型名称"""
        self.assertEqual(get_type_name(42), 'int')
        self.assertEqual(get_type_name(0), 'int')
        self.assertEqual(get_type_name(-100), 'int')

    def test_get_type_name_float(self):
        """测试浮点数类型名称"""
        self.assertEqual(get_type_name(3.14), 'float')
        self.assertEqual(get_type_name(0.0), 'float')

    def test_get_type_name_string(self):
        """测试字符串类型名称"""
        self.assertEqual(get_type_name("hello"), 'string')
        self.assertEqual(get_type_name(""), 'string')

    def test_get_type_name_array(self):
        """测试数组类型名称"""
        self.assertEqual(get_type_name([1, 2, 3]), 'array')
        self.assertEqual(get_type_name([]), 'array')

    def test_get_type_name_other(self):
        """测试其他类型的名称"""
        self.assertEqual(get_type_name({"key": "value"}), 'dict')
        self.assertEqual(get_type_name((1, 2, 3)), 'tuple')
        self.assertEqual(get_type_name(None), 'NoneType')


class TestIsValidIndex(unittest.TestCase):
    """测试数组索引有效性检查"""

    def test_is_valid_index_with_valid_indices(self):
        """测试有效的索引"""
        arr = [10, 20, 30, 40, 50]
        self.assertTrue(is_valid_index(arr, 0))
        self.assertTrue(is_valid_index(arr, 2))
        self.assertTrue(is_valid_index(arr, 4))

    def test_is_valid_index_with_negative_index(self):
        """测试负索引无效"""
        arr = [10, 20, 30]
        self.assertFalse(is_valid_index(arr, -1))
        self.assertFalse(is_valid_index(arr, -2))

    def test_is_valid_index_with_out_of_range(self):
        """测试超出范围的索引"""
        arr = [10, 20, 30]
        self.assertFalse(is_valid_index(arr, 3))
        self.assertFalse(is_valid_index(arr, 100))

    def test_is_valid_index_with_non_integer(self):
        """测试非整数索引"""
        arr = [10, 20, 30]
        self.assertFalse(is_valid_index(arr, 1.5))
        self.assertFalse(is_valid_index(arr, "1"))
        self.assertFalse(is_valid_index(arr, None))

    def test_is_valid_index_with_empty_array(self):
        """测试空数组"""
        arr = []
        self.assertFalse(is_valid_index(arr, 0))
        self.assertFalse(is_valid_index(arr, -1))


if __name__ == '__main__':
    unittest.main()
