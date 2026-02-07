#!/usr/bin/env python3
"""
HPL 解析器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from parser import HPLParser


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
            classes, objects, main_func, call_target = parser.parse()
            
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
            classes, objects, main_func, call_target = parser.parse()
            
            # 验证 BasePrinter 类
            self.assertIn('BasePrinter', classes)
            base_printer = classes['BasePrinter']
            self.assertIn('print', base_printer.methods)
    
    def test_class_inheritance(self):
        """测试类继承解析"""
        example_file = os.path.join(self.examples_dir, 'example.hpl')
        if os.path.exists(example_file):
            parser = HPLParser(example_file)
            classes, _, _, _ = parser.parse()
            
            if 'MessagePrinter' in classes:
                message_printer = classes['MessagePrinter']
                self.assertEqual(message_printer.parent, 'BasePrinter')
    
    def test_function_parsing(self):
        """测试函数解析"""
        example_file = os.path.join(self.examples_dir, 'example.hpl')
        if os.path.exists(example_file):
            parser = HPLParser(example_file)
            classes, _, main_func, _ = parser.parse()
            
            # 验证 main 函数
            self.assertIsNotNone(main_func)
            self.assertIsInstance(main_func.params, list)
            self.assertIsNotNone(main_func.body)
    
    def test_object_instantiation(self):
        """测试对象实例化解析"""
        example_file = os.path.join(self.examples_dir, 'example.hpl')
        if os.path.exists(example_file):
            parser = HPLParser(example_file)
            _, objects, _, _ = parser.parse()
            
            # 验证 printer 对象
            self.assertIn('printer', objects)
            printer = objects['printer']
            self.assertEqual(printer.hpl_class.name, 'MessagePrinter')


class TestPreprocessor(unittest.TestCase):
    """测试预处理器功能"""
    
    def test_preprocess_functions(self):
        """测试函数预处理"""
        from parser import HPLParser
        
        # 创建临时测试内容
        content = """main: () => {
    x = 1
  }"""
        
        # 测试预处理
        parser = HPLParser.__new__(HPLParser)
        result = parser.preprocess_functions(content)
        
        # 验证预处理结果包含字面量块标记
        self.assertIn('|', result)


if __name__ == '__main__':
    unittest.main()

