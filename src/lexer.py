import re

"""
HPL 词法分析器模块

该模块负责将 HPL 源代码转换为 Token 序列，是解释器的第一阶段。
包含 Token 类和 HPLLexer 类，支持识别关键字、标识符、运算符、
字符串和数字等各种词法单元。

关键类：
- Token: 表示单个词法单元，包含类型和值
- HPLLexer: 词法分析器，将源代码字符串转换为 Token 列表
"""

class Token:

    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f'Token({self.type}, {self.value})'

class HPLLexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if self.text else None

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def string(self):
        result = ''
        self.advance()  # 跳过开始引号
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        self.advance()  # 跳过结束引号
        return result

    def identifier(self):
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        return result

    def tokenize(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            if self.current_char.isdigit():
                tokens.append(Token('INTEGER', self.integer()))
                continue
            if self.current_char == '"':
                tokens.append(Token('STRING', self.string()))
                continue
            if self.current_char.isalpha() or self.current_char == '_':
                ident = self.identifier()
                if ident in ['if', 'else', 'for', 'try', 'catch', 'return']:
                    tokens.append(Token('KEYWORD', ident))

                elif ident in ['true', 'false']:
                    tokens.append(Token('BOOLEAN', ident == 'true'))
                else:
                    tokens.append(Token('IDENTIFIER', ident))
                continue


            if self.current_char == '+':
                self.advance()
                if self.current_char == '+':
                    tokens.append(Token('INCREMENT', '++'))
                    self.advance()
                else:
                    tokens.append(Token('PLUS', '+'))
            elif self.current_char == '-':
                tokens.append(Token('MINUS', '-'))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token('MUL', '*'))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token('DIV', '/'))
                self.advance()
            elif self.current_char == '%':
                tokens.append(Token('MOD', '%'))
                self.advance()
            elif self.current_char == '!':
                self.advance()
                if self.current_char == '=':
                    tokens.append(Token('NE', '!='))
                    self.advance()
                else:
                    tokens.append(Token('NOT', '!'))

            elif self.current_char == '<':
                self.advance()
                if self.current_char == '=':
                    tokens.append(Token('LE', '<='))
                    self.advance()
                else:
                    tokens.append(Token('LT', '<'))
            elif self.current_char == '>':
                self.advance()
                if self.current_char == '=':
                    tokens.append(Token('GE', '>='))
                    self.advance()
                else:
                    tokens.append(Token('GT', '>'))
            elif self.current_char == '(':
                tokens.append(Token('LPAREN', '('))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token('RPAREN', ')'))
                self.advance()
            elif self.current_char == '{':
                tokens.append(Token('LBRACE', '{'))
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token('RBRACE', '}'))
                self.advance()
            elif self.current_char == ';':
                tokens.append(Token('SEMICOLON', ';'))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token('COMMA', ','))
                self.advance()
            elif self.current_char == '.':
                tokens.append(Token('DOT', '.'))
                self.advance()
            elif self.current_char == ':':
                tokens.append(Token('COLON', ':'))
                self.advance()
            elif self.current_char == '=':
                self.advance()
                if self.current_char == '=':
                    tokens.append(Token('EQ', '=='))
                    self.advance()
                elif self.current_char == '>':
                    tokens.append(Token('ARROW', '=>'))
                    self.advance()
                else:
                    tokens.append(Token('ASSIGN', '='))
            else:
                raise ValueError(f"Invalid character: {self.current_char}")

        tokens.append(Token('EOF', None))
        return tokens
