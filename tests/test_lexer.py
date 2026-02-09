#!/usr/bin/env python3
"""
HPL 词法分析器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hpl_runtime'))

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
    
    def test_escape_sequences(self):
        """测试字符串转义序列"""
        # 测试换行符
        lexer = HPLLexer('"Hello\\nWorld"')
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'STRING')
        self.assertEqual(tokens[0].value, 'Hello\nWorld')
        
        # 测试制表符
        lexer = HPLLexer('"Col1\\tCol2"')
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].value, 'Col1\tCol2')
        
        # 测试反斜杠
        lexer = HPLLexer('"C:\\\\Users\\\\test"')
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].value, 'C:\\Users\\test')
        
        # 测试引号
        lexer = HPLLexer('"Say \\"Hello\\""')
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].value, 'Say "Hello"')
    
    def test_line_column_tracking(self):
        """测试行号和列号跟踪"""
        code = """line1
line2
  line3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        
        # 找到标识符token并检查位置
        identifiers = [t for t in tokens if t.type == 'IDENTIFIER']
        self.assertEqual(len(identifiers), 3)
        
        # line1 在第1行
        self.assertEqual(identifiers[0].line, 1)
        self.assertEqual(identifiers[0].column, 0)
        
        # line2 在第2行
        self.assertEqual(identifiers[1].line, 2)
        self.assertEqual(identifiers[1].column, 0)
        
        # line3 在第3行，有缩进
        self.assertEqual(identifiers[2].line, 3)
    
    def test_invalid_character_error(self):
        """测试无效字符错误处理"""
        # 测试单个无效字符
        lexer = HPLLexer('@')
        with self.assertRaises(ValueError) as context:
            lexer.tokenize()
        self.assertIn("Invalid character '@'", str(context.exception))
        
        # 测试无效字符在表达式中
        lexer = HPLLexer('x @ y')
        with self.assertRaises(ValueError) as context:
            lexer.tokenize()
        self.assertIn("Invalid character", str(context.exception))
    
    def test_unclosed_string_error(self):
        """测试未闭合字符串错误处理"""
        # lexer 在遇到未闭合字符串时会继续处理直到文件结束
        # 这不会报错，但会返回一个不完整的字符串
        lexer = HPLLexer('"unclosed string')
        tokens = lexer.tokenize()
        # 应该有一个字符串token，值为未闭合的内容
        self.assertEqual(tokens[0].type, 'STRING')
        self.assertEqual(tokens[0].value, 'unclosed string')
    
    def test_logical_operators(self):
        """测试逻辑运算符 && 和 ||"""
        lexer = HPLLexer('a && b || c')
        tokens = lexer.tokenize()
        
        ops = [t.type for t in tokens if t.type in ['AND', 'OR']]
        self.assertEqual(ops, ['AND', 'OR'])
    
    def test_modulo_operator(self):
        """测试取模运算符 %"""
        lexer = HPLLexer('x % 2')
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[1].type, 'MOD')
        self.assertEqual(tokens[1].value, '%')


class TestToken(unittest.TestCase):
    """测试 Token 类"""
    
    def test_token_repr(self):
        """测试 Token 字符串表示"""
        token = Token('NUMBER', 42)
        self.assertEqual(repr(token), 'Token(NUMBER, 42, line=0, col=0)')
    
    def test_token_with_position(self):
        """测试带位置的 Token 创建"""
        token = Token('IDENTIFIER', 'x', line=5, column=10)
        self.assertEqual(token.line, 5)
        self.assertEqual(token.column, 10)
        self.assertEqual(repr(token), 'Token(IDENTIFIER, x, line=5, col=10)')



if __name__ == '__main__':
    unittest.main()
