#!/usr/bin/env python3
"""
HPL 词法分析器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from lexer import HPLLexer, Token


class TestHPLLexer(unittest.TestCase):
    """测试 HPLLexer 类"""
    
    def test_empty_input(self):
        """测试空输入"""
        lexer = HPLLexer("")
        tokens = lexer.tokenize()
        self.assertEqual(tokens[-1].type, 'EOF')
    
    def test_numbers(self):
        """测试数字识别"""
        # 整数
        lexer = HPLLexer("42")
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'NUMBER')
        self.assertEqual(tokens[0].value, 42)
        
        # 浮点数
        lexer = HPLLexer("3.14")
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'NUMBER')
        self.assertEqual(tokens[0].value, 3.14)
        
        # 负数（通过一元运算符实现）
        lexer = HPLLexer("-42")
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'MINUS')
        self.assertEqual(tokens[1].type, 'NUMBER')
        self.assertEqual(tokens[1].value, 42)
    
    def test_strings(self):
        """测试字符串识别"""
        lexer = HPLLexer('"Hello World"')
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'STRING')
        self.assertEqual(tokens[0].value, 'Hello World')
    
    def test_identifiers_and_keywords(self):
        """测试标识符和关键字"""
        # 关键字
        lexer = HPLLexer('if else for try catch return')
        tokens = lexer.tokenize()
        keyword_values = [t.value for t in tokens if t.type == 'KEYWORD']
        self.assertEqual(keyword_values, ['if', 'else', 'for', 'try', 'catch', 'return'])
        
        # 布尔值
        lexer = HPLLexer('true false')
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'BOOLEAN')
        self.assertEqual(tokens[0].value, True)
        self.assertEqual(tokens[1].type, 'BOOLEAN')
        self.assertEqual(tokens[1].value, False)
        
        # 标识符
        lexer = HPLLexer('myVariable _private var123')
        tokens = lexer.tokenize()
        identifiers = [t for t in tokens if t.type == 'IDENTIFIER']
        self.assertEqual(len(identifiers), 3)
        self.assertEqual(identifiers[0].value, 'myVariable')
        self.assertEqual(identifiers[1].value, '_private')
        self.assertEqual(identifiers[2].value, 'var123')
    
    def test_operators(self):
        """测试运算符"""
        lexer = HPLLexer('+ - * / %')
        tokens = lexer.tokenize()
        ops = [t.type for t in tokens[:-1]]  # 排除 EOF
        self.assertEqual(ops, ['PLUS', 'MINUS', 'MUL', 'DIV', 'MOD'])
        
        # 比较运算符
        lexer = HPLLexer('== != < <= > >=')
        tokens = lexer.tokenize()
        ops = [t.type for t in tokens[:-1]]
        self.assertEqual(ops, ['EQ', 'NE', 'LT', 'LE', 'GT', 'GE'])
        
        # 自增
        lexer = HPLLexer('++')
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'INCREMENT')
    
    def test_comments(self):
        """测试注释处理"""
        lexer = HPLLexer('# 这是注释\n42')
        tokens = lexer.tokenize()
        # 注释应该被跳过，只保留数字
        self.assertEqual(tokens[0].type, 'NUMBER')
        self.assertEqual(tokens[0].value, 42)
    
    def test_indentation(self):
        """测试缩进处理"""
        code = """if (true) :
  x = 1
  y = 2
z = 3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        
        # 检查 INDENT 和 DEDENT
        token_types = [t.type for t in tokens]
        self.assertIn('INDENT', token_types)
        self.assertIn('DEDENT', token_types)
    
    def test_complex_expression(self):
        """测试复杂表达式"""
        code = 'result = (a + b) * 2'
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        
        expected_types = ['IDENTIFIER', 'ASSIGN', 'LPAREN', 'IDENTIFIER', 
                       'PLUS', 'IDENTIFIER', 'RPAREN', 'MUL', 'NUMBER', 'EOF']
        actual_types = [t.type for t in tokens]
        self.assertEqual(actual_types, expected_types)


class TestToken(unittest.TestCase):
    """测试 Token 类"""
    
    def test_token_repr(self):
        """测试 Token 字符串表示"""
        token = Token('NUMBER', 42)
        self.assertEqual(repr(token), 'Token(NUMBER, 42, line=0, col=0)')



if __name__ == '__main__':
    unittest.main()
