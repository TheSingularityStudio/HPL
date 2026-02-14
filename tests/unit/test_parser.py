#!/usr/bin/env python3
"""
HPL 解析器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest

from hpl_runtime.core.parser import HPLParser
from hpl_runtime.core.lexer import HPLLexer
from hpl_runtime.core.ast_parser import HPLASTParser
from hpl_runtime.core.models import WhileStatement, BinaryOp, Variable, IntegerLiteral, ImportStatement, BreakStatement, ContinueStatement
from hpl_runtime.utils.text_utils import preprocess_functions



class TestHPLParser(unittest.TestCase):
    """测试 HPLParser 类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时测试文件
        self.test_dir = os.path.dirname(__file__)
        self.examples_dir = os.path.join(os.path.dirname(__file__), '..', 'examples')
    
    def test_parse_example_file(self):
        """测试解析主示例文件"""
        example_file = os.path.join(self.examples_dir, 'example.hpl')
        if os.path.exists(example_file):
            parser = HPLParser(example_file)
            classes, objects, functions, main_func, call_target, call_args, imports = parser.parse()

            
            # 验证解析结果

            self.assertIn('MessagePrinter', classes)
            self.assertIn('printer', objects)
            self.assertIsNotNone(main_func)
            self.assertEqual(call_target, 'main')
    
    def test_parse_base_file(self):
        """测试解析基础类文件"""
        base_file = os.path.join(self.examples_dir, 'base.hpl')
        if os.path.exists(base_file):
            parser = HPLParser(base_file)
            classes, objects, functions, main_func, call_target, call_args, imports = parser.parse()

            
            # 验证 BasePrinter 类

            self.assertIn('BasePrinter', classes)
            base_printer = classes['BasePrinter']
            self.assertIn('print', base_printer.methods)
    
    def test_class_inheritance(self):
        """测试类继承解析"""
        example_file = os.path.join(self.examples_dir, 'example.hpl')
        if os.path.exists(example_file):
            parser = HPLParser(example_file)
            classes, _, _, _, _, _, _ = parser.parse()


            
            if 'MessagePrinter' in classes:
                message_printer = classes['MessagePrinter']
                self.assertEqual(message_printer.parent, 'BasePrinter')
    
    def test_function_parsing(self):
        """测试函数解析"""
        example_file = os.path.join(self.examples_dir, 'example.hpl')
        if os.path.exists(example_file):
            parser = HPLParser(example_file)
            classes, _, _, main_func, _, _, _ = parser.parse()


            
            # 验证 main 函数
            self.assertIsNotNone(main_func)
            self.assertIsInstance(main_func.params, list)
            self.assertIsNotNone(main_func.body)
    
    def test_object_instantiation(self):
        """测试对象实例化解析"""
        example_file = os.path.join(self.examples_dir, 'example.hpl')
        if os.path.exists(example_file):
            parser = HPLParser(example_file)
            _, objects, _, _, _, _, _ = parser.parse()


            
            # 验证 printer 对象
            self.assertIn('printer', objects)
            printer = objects['printer']
            self.assertEqual(printer.hpl_class.name, 'MessagePrinter')


class TestPreprocessor(unittest.TestCase):
    """测试预处理器功能"""
    
    def test_preprocess_functions(self):
        """测试函数预处理"""
        # 创建临时测试内容
        content = """main: () => {
    x = 1
  }"""
        
        # 测试预处理 - 使用导入的函数
        result = preprocess_functions(content)
        
        # 验证预处理结果包含字面量块标记
        self.assertIn('|', result)


class TestNewParsingFeatures(unittest.TestCase):
    """测试新的解析功能"""
    
    def test_parse_while_statement(self):
        """测试 while 语句解析"""
        # 解析 while (i < 10) { i++ }
        code = "while (i < 10) : i++"
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        ast_parser = HPLASTParser(tokens)
        
        stmt = ast_parser.parse_statement()
        
        # 验证是 while 语句 - 使用类型名称比较避免导入路径问题
        self.assertEqual(type(stmt).__name__, 'WhileStatement')
        # 验证条件
        self.assertEqual(type(stmt.condition).__name__, 'BinaryOp')
        self.assertEqual(stmt.condition.op, '<')
        # 验证循环体
        self.assertIsNotNone(stmt.body)
    
    def test_parse_import_statement(self):
        """测试 import 语句解析"""
        # 测试简单导入: import math
        code = "import math"
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        ast_parser = HPLASTParser(tokens)
        
        stmt = ast_parser.parse_statement()
        
        # 使用类型名称比较避免导入路径问题
        self.assertEqual(type(stmt).__name__, 'ImportStatement')
        self.assertEqual(stmt.module_name, 'math')
        self.assertIsNone(stmt.alias)
        
        # 注意: 带别名的导入 (import math as m) 需要 'as' 作为关键字
        # 当前 lexer 未将 'as' 识别为关键字，此功能待实现

    
    def test_parse_break_continue(self):
        """测试 break 和 continue 语句解析"""
        # 测试 break
        code_break = "break"
        lexer_break = HPLLexer(code_break)
        tokens_break = lexer_break.tokenize()
        ast_parser_break = HPLASTParser(tokens_break)
        
        stmt_break = ast_parser_break.parse_statement()
        # 使用类型名称比较避免导入路径问题
        self.assertEqual(type(stmt_break).__name__, 'BreakStatement')
        
        # 测试 continue
        code_continue = "continue"
        lexer_continue = HPLLexer(code_continue)
        tokens_continue = lexer_continue.tokenize()
        ast_parser_continue = HPLASTParser(tokens_continue)
        
        stmt_continue = ast_parser_continue.parse_statement()
        # 使用类型名称比较避免导入路径问题
        self.assertEqual(type(stmt_continue).__name__, 'ContinueStatement')



if __name__ == '__main__':
    unittest.main()

