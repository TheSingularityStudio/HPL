import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lexer import HPLLexer, Token

class TestHPLLexer(unittest.TestCase):

    def test_integer_tokenization(self):
        lexer = HPLLexer("123")
        tokens = lexer.tokenize()
        self.assertEqual(len(tokens), 2)  # INTEGER and EOF
        self.assertEqual(tokens[0].type, 'INTEGER')
        self.assertEqual(tokens[0].value, 123)

    def test_string_tokenization(self):
        lexer = HPLLexer('"hello"')
        tokens = lexer.tokenize()
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, 'STRING')
        self.assertEqual(tokens[0].value, 'hello')

    def test_identifier_tokenization(self):
        lexer = HPLLexer("variable")
        tokens = lexer.tokenize()
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, 'IDENTIFIER')
        self.assertEqual(tokens[0].value, 'variable')

    def test_keyword_tokenization(self):
        lexer = HPLLexer("if else for try catch func")
        tokens = lexer.tokenize()
        expected = ['if', 'else', 'for', 'try', 'catch', 'func']
        for i, kw in enumerate(expected):
            self.assertEqual(tokens[i].type, 'KEYWORD')
            self.assertEqual(tokens[i].value, kw)

    def test_operator_tokenization(self):
        lexer = HPLLexer("++ + - * / % == = != < <= > >=")
        tokens = lexer.tokenize()
        expected_types = ['INCREMENT', 'PLUS', 'MINUS', 'MUL', 'DIV', 'MOD', 'EQ', 'ASSIGN', 'NE', 'LT', 'LE', 'GT', 'GE']
        for i, typ in enumerate(expected_types):
            self.assertEqual(tokens[i].type, typ)

    def test_parentheses_and_braces(self):
        lexer = HPLLexer("() {}")
        tokens = lexer.tokenize()
        expected = ['LPAREN', 'RPAREN', 'LBRACE', 'RBRACE']
        for i, typ in enumerate(expected):
            self.assertEqual(tokens[i].type, typ)

    def test_semicolon_and_comma(self):
        lexer = HPLLexer("; , .")
        tokens = lexer.tokenize()
        expected = ['SEMICOLON', 'COMMA', 'DOT']
        for i, typ in enumerate(expected):
            self.assertEqual(tokens[i].type, typ)

    def test_whitespace_skipping(self):
        lexer = HPLLexer("  123   ")
        tokens = lexer.tokenize()
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, 'INTEGER')

    def test_invalid_character(self):
        lexer = HPLLexer("@")
        with self.assertRaises(ValueError):
            lexer.tokenize()

    def test_increment_operator(self):
        lexer = HPLLexer("i++")
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'IDENTIFIER')
        self.assertEqual(tokens[1].type, 'INCREMENT')

if __name__ == '__main__':
    unittest.main()
