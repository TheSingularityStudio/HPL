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
        # 缩进跟踪
        self.indent_stack = [0]  # 缩进级别栈，初始为0
        self.at_line_start = True  # 标记是否在行首


    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def peek(self):
        """查看下一个字符但不移动位置"""
        peek_pos = self.pos + 1
        if peek_pos > len(self.text) - 1:
            return None
        else:
            return self.text[peek_pos]

    def skip_whitespace(self):
        """跳过非换行的空白字符"""
        while self.current_char is not None and self.current_char.isspace() and self.current_char != '\n':
            self.advance()


    def number(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        # 检查小数点
        if self.current_char == '.' and self.peek() is not None and self.peek().isdigit():
            result += self.current_char
            self.advance()
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()
            return float(result)
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

    def skip_comment(self):
        """跳过从当前位置到行尾的注释"""
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    def tokenize(self):
        tokens = []
        while self.current_char is not None:
            # 处理行首的缩进
            if self.at_line_start and self.current_char.isspace():
                # 计算前导空格数
                indent = 0
                while self.current_char is not None and self.current_char.isspace() and self.current_char != '\n':
                    if self.current_char == ' ':
                        indent += 1
                    elif self.current_char == '\t':
                        indent += 4  # 制表符算作4个空格
                    self.advance()
                
                # 跳过空行（只有空白字符的行）
                if self.current_char == '\n' or self.current_char is None:
                    self.at_line_start = True
                    if self.current_char == '\n':
                        self.advance()
                    continue
                
                # 生成 INDENT/DEDENT 标记
                current_indent = self.indent_stack[-1]
                if indent > current_indent:
                    # 缩进增加
                    self.indent_stack.append(indent)
                    tokens.append(Token('INDENT', indent))
                elif indent < current_indent:
                    # 缩进减少，可能弹出多个级别
                    while indent < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        tokens.append(Token('DEDENT', self.indent_stack[-1]))
                
                self.at_line_start = False
                continue
            
            # 处理换行符
            if self.current_char == '\n':
                self.advance()
                self.at_line_start = True
                continue
            
            # 处理注释
            if self.current_char == '#':
                self.skip_comment()
                self.at_line_start = True  # 注释后视为行首
                continue
            
            # 跳过非行首的空白字符
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            # 其他字符，标记不在行首
            self.at_line_start = False

            if self.current_char.isdigit():


                tokens.append(Token('NUMBER', self.number()))
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
            elif self.current_char == '[':
                tokens.append(Token('LBRACKET', '['))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token('RBRACKET', ']'))
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

        # 文件结束时，弹出所有缩进级别
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token('DEDENT', 0))
        
        tokens.append(Token('EOF', None))
        return tokens
