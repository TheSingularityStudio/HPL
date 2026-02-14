#!/usr/bin/env python3
"""
HPL 边界情况测试

测试空值、极大数值、深层嵌套、异常输入等边界情况
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from hpl_runtime.core.evaluator import HPLEvaluator
from hpl_runtime.core.models import (
    IntegerLiteral, FloatLiteral, StringLiteral, BooleanLiteral, NullLiteral,
    ArrayLiteral, DictionaryLiteral, Variable, BinaryOp, UnaryOp,
    AssignmentStatement, BlockStatement, IfStatement, WhileStatement,
    ForInStatement, ReturnStatement, FunctionCall, ArrayAccess,
    ArrayAssignmentStatement
)
from hpl_runtime.utils.exceptions import (
    HPLTypeError, HPLIndexError, HPLNameError, HPLDivisionError, HPLValueError
)


class TestEmptyValues(unittest.TestCase):
    """测试空值处理"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_null_literal(self):
        """测试 null 字面量"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        null_expr = NullLiteral()
        result = evaluator.evaluate_expression(null_expr, {})
        
        self.assertIsNone(result)

    def test_null_in_variable(self):
        """测试变量中的 null"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        local_scope = {'empty': None}
        var = Variable('empty')
        result = evaluator.evaluate_expression(var, local_scope)
        
        self.assertIsNone(result)

    def test_null_in_array(self):
        """测试数组中的 null"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        arr_expr = ArrayLiteral([
            IntegerLiteral(1),
            NullLiteral(),
            StringLiteral('test')
        ])
        result = evaluator.evaluate_expression(arr_expr, {})
        
        self.assertEqual(result, [1, None, 'test'])

    def test_null_in_dictionary(self):
        """测试字典中的 null"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        dict_expr = DictionaryLiteral({
            'value': NullLiteral(),
            'name': StringLiteral('test')
        })
        result = evaluator.evaluate_expression(dict_expr, {})
        
        self.assertIsNone(result['value'])
        self.assertEqual(result['name'], 'test')

    def test_empty_array(self):
        """测试空数组"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        empty_arr = ArrayLiteral([])
        result = evaluator.evaluate_expression(empty_arr, {})
        
        self.assertEqual(result, [])
        self.assertEqual(len(result), 0)

    def test_empty_string(self):
        """测试空字符串"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        empty_str = StringLiteral('')
        result = evaluator.evaluate_expression(empty_str, {})
        
        self.assertEqual(result, '')
        self.assertEqual(len(result), 0)


class TestLargeNumbers(unittest.TestCase):
    """测试大数值处理"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_large_integer(self):
        """测试大整数"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        large_int = IntegerLiteral(999999999999999999)
        result = evaluator.evaluate_expression(large_int, {})
        
        self.assertEqual(result, 999999999999999999)

    def test_very_large_integer(self):
        """测试超大整数"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        very_large = IntegerLiteral(10**20)
        result = evaluator.evaluate_expression(very_large, {})
        
        self.assertEqual(result, 10**20)

    def test_large_float(self):
        """测试大浮点数"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        large_float = FloatLiteral(1.7976931348623157e+308)  # 接近最大值
        result = evaluator.evaluate_expression(large_float, {})
        
        self.assertEqual(result, 1.7976931348623157e+308)

    def test_very_small_float(self):
        """测试极小浮点数"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        small_float = FloatLiteral(5e-324)  # 接近最小正值
        result = evaluator.evaluate_expression(small_float, {})
        
        self.assertEqual(result, 5e-324)

    def test_large_number_arithmetic(self):
        """测试大数运算"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 大数加法
        left = IntegerLiteral(10**15)
        right = IntegerLiteral(10**15)
        add_expr = BinaryOp(left, '+', right)
        result = evaluator.evaluate_expression(add_expr, {})
        
        self.assertEqual(result, 2 * 10**15)


class TestDeepNesting(unittest.TestCase):
    """测试深层嵌套"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_deeply_nested_arrays(self):
        """测试深度嵌套数组（5层）"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 创建5层嵌套数组
        level5 = ArrayLiteral([IntegerLiteral(1)])
        level4 = ArrayLiteral([level5])
        level3 = ArrayLiteral([level4])
        level2 = ArrayLiteral([level3])
        level1 = ArrayLiteral([level2])
        
        result = evaluator.evaluate_expression(level1, {})
        
        # 验证嵌套结构
        self.assertEqual(result[0][0][0][0][0], 1)

    def test_deeply_nested_dictionaries(self):
        """测试深度嵌套字典（5层）"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 创建5层嵌套字典
        level5 = DictionaryLiteral({'value': IntegerLiteral(42)})
        level4 = DictionaryLiteral({'next': level5})
        level3 = DictionaryLiteral({'next': level4})
        level2 = DictionaryLiteral({'next': level3})
        level1 = DictionaryLiteral({'next': level2})
        
        result = evaluator.evaluate_expression(level1, {})
        
        # 验证嵌套结构
        self.assertEqual(result['next']['next']['next']['next']['value'], 42)

    def test_deeply_nested_mixed(self):
        """测试深度混合嵌套"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 数组包含字典，字典包含数组，多层嵌套
        inner_arr = ArrayLiteral([IntegerLiteral(1), IntegerLiteral(2)])
        inner_dict = DictionaryLiteral({'items': inner_arr})
        middle_arr = ArrayLiteral([inner_dict, inner_dict])
        outer_dict = DictionaryLiteral({'data': middle_arr})
        
        result = evaluator.evaluate_expression(outer_dict, {})
        
        # 验证结构
        self.assertEqual(result['data'][0]['items'][1], 2)

    def test_deep_block_nesting(self):
        """测试深层代码块嵌套"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 创建5层嵌套的if语句
        inner = BlockStatement([AssignmentStatement('x', IntegerLiteral(5))])
        for _ in range(4):
            inner = BlockStatement([
                IfStatement(BooleanLiteral(True), inner)
            ])
        
        local_scope = {}
        evaluator.execute_block(inner, local_scope)
        
        self.assertEqual(local_scope['x'], 5)


class TestStringEdgeCases(unittest.TestCase):
    """测试字符串边界情况"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_very_long_string(self):
        """测试超长字符串"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        long_string = 'a' * 10000
        str_expr = StringLiteral(long_string)
        result = evaluator.evaluate_expression(str_expr, {})
        
        self.assertEqual(len(result), 10000)
        self.assertEqual(result[0], 'a')
        self.assertEqual(result[-1], 'a')

    def test_string_with_all_escapes(self):
        """测试包含所有转义字符的字符串"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 注意：当前实现可能不处理转义序列，直接返回原始字符串
        # 测试原始字符串保留
        test_cases = [
            ('Hello\\nWorld', 'Hello\\nWorld'),  # 当前实现不处理转义
            ('Tab\\tHere', 'Tab\\tHere'),
            ('Quote\\"Test\\"', 'Quote\\"Test\\"'),
            ('Backslash\\\\Test', 'Backslash\\\\Test'),
        ]
        
        for input_str, expected in test_cases:
            str_expr = StringLiteral(input_str)
            result = evaluator.evaluate_expression(str_expr, {})
            self.assertEqual(result, expected)


    def test_unicode_string(self):
        """测试Unicode字符串"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        unicode_str = StringLiteral('你好世界🌍')
        result = evaluator.evaluate_expression(unicode_str, {})
        
        self.assertEqual(result, '你好世界🌍')

    def test_string_index_edge_cases(self):
        """测试字符串索引边界"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        local_scope = {'s': 'Hello'}
        
        # 有效索引
        access = ArrayAccess(Variable('s'), IntegerLiteral(0))
        access.line = 1
        access.column = 0
        result = evaluator.evaluate_expression(access, local_scope)
        self.assertEqual(result, 'H')
        
        access = ArrayAccess(Variable('s'), IntegerLiteral(4))
        access.line = 1
        access.column = 0
        result = evaluator.evaluate_expression(access, local_scope)
        self.assertEqual(result, 'o')
        
        # 越界索引应该报错
        with self.assertRaises(HPLIndexError):
            access = ArrayAccess(Variable('s'), IntegerLiteral(5))
            access.line = 1
            access.column = 0
            evaluator.evaluate_expression(access, local_scope)



class TestArrayEdgeCases(unittest.TestCase):
    """测试数组边界情况"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_very_large_array(self):
        """测试超大数组"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 创建包含1000个元素的数组
        elements = [IntegerLiteral(i) for i in range(1000)]
        large_arr = ArrayLiteral(elements)
        result = evaluator.evaluate_expression(large_arr, {})
        
        self.assertEqual(len(result), 1000)
        self.assertEqual(result[500], 500)

    def test_array_with_mixed_types(self):
        """测试混合类型数组"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        mixed_arr = ArrayLiteral([
            IntegerLiteral(1),
            StringLiteral('two'),
            BooleanLiteral(True),
            NullLiteral(),
            ArrayLiteral([IntegerLiteral(5)])
        ])
        result = evaluator.evaluate_expression(mixed_arr, {})
        
        self.assertEqual(result, [1, 'two', True, None, [5]])

    def test_array_index_edge_cases(self):
        """测试数组索引边界"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        local_scope = {'arr': [10, 20, 30]}
        
        # 有效索引
        access = ArrayAccess(Variable('arr'), IntegerLiteral(0))
        access.line = 1
        access.column = 0
        result = evaluator.evaluate_expression(access, local_scope)
        self.assertEqual(result, 10)
        
        # 越界索引应该报错
        with self.assertRaises(HPLIndexError):
            access = ArrayAccess(Variable('arr'), IntegerLiteral(3))
            access.line = 1
            access.column = 0
            evaluator.evaluate_expression(access, local_scope)
        
        with self.assertRaises(HPLIndexError):
            access = ArrayAccess(Variable('arr'), IntegerLiteral(-1))
            access.line = 1
            access.column = 0
            evaluator.evaluate_expression(access, local_scope)



class TestErrorEdgeCases(unittest.TestCase):
    """测试错误边界情况"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_division_by_zero_variations(self):
        """测试各种除零情况"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 整数除零
        with self.assertRaises(HPLDivisionError):
            expr = BinaryOp(IntegerLiteral(10), '/', IntegerLiteral(0))
            evaluator.evaluate_expression(expr, {})
        
        # 浮点数除零
        with self.assertRaises(HPLDivisionError):
            expr = BinaryOp(FloatLiteral(10.5), '/', IntegerLiteral(0))
            evaluator.evaluate_expression(expr, {})
        
        # 取模零
        with self.assertRaises(HPLDivisionError):
            expr = BinaryOp(IntegerLiteral(10), '%', IntegerLiteral(0))
            evaluator.evaluate_expression(expr, {})

    def test_type_error_variations(self):
        """测试各种类型错误"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 字符串减法
        with self.assertRaises(HPLTypeError):
            expr = BinaryOp(StringLiteral('hello'), '-', StringLiteral('world'))
            evaluator.evaluate_expression(expr, {})
        
        # 数组与数字相加（应该可以，转为字符串拼接）
        expr = BinaryOp(ArrayLiteral([IntegerLiteral(1)]), '+', IntegerLiteral(2))
        result = evaluator.evaluate_expression(expr, {})
        self.assertEqual(result, '[1]2')  # 数组转字符串后拼接

    def test_undefined_variable_variations(self):
        """测试各种未定义变量情况"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 简单未定义变量
        with self.assertRaises(HPLNameError):
            var = Variable('undefined_var')
            evaluator.evaluate_expression(var, {})
        
        # 在表达式中使用未定义变量
        with self.assertRaises(HPLNameError):
            expr = BinaryOp(Variable('x'), '+', IntegerLiteral(5))
            evaluator.evaluate_expression(expr, {})


class TestControlFlowEdgeCases(unittest.TestCase):
    """测试控制流边界情况"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_while_with_false_condition(self):
        """测试条件为假的while循环"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # while (false) 应该一次都不执行
        local_scope = {'count': 0}
        
        while_stmt = WhileStatement(
            BooleanLiteral(False),
            BlockStatement([
                AssignmentStatement('count', IntegerLiteral(999))
            ])
        )
        
        evaluator.execute_statement(while_stmt, local_scope)
        
        # count 应该保持为 0
        self.assertEqual(local_scope['count'], 0)

    def test_for_in_empty_array(self):
        """测试遍历空数组"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        local_scope = {'sum': 0}
        
        for_stmt = ForInStatement(
            'item',
            ArrayLiteral([]),
            BlockStatement([
                AssignmentStatement('sum', BinaryOp(
                    Variable('sum'), '+', Variable('item')
                ))
            ])
        )
        
        evaluator.execute_statement(for_stmt, local_scope)
        
        # sum 应该保持为 0
        self.assertEqual(local_scope['sum'], 0)

    def test_if_with_complex_condition(self):
        """测试复杂条件的if语句"""
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        local_scope = {}
        
        # (true && false) || true
        condition = BinaryOp(
            BinaryOp(BooleanLiteral(True), '&&', BooleanLiteral(False)),
            '||',
            BooleanLiteral(True)
        )
        
        if_stmt = IfStatement(
            condition,
            BlockStatement([AssignmentStatement('result', StringLiteral('executed'))])
        )
        
        evaluator.execute_statement(if_stmt, local_scope)
        
        self.assertEqual(local_scope['result'], 'executed')


if __name__ == '__main__':
    unittest.main()
