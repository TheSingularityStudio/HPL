import re

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

    def string(self, quote_char):
        result = ''
        self.advance()  # 跳过开始引号
        while self.current_char is not None and self.current_char != quote_char:
            if self.current_char == '\\':
                # 处理转义字符
                self.advance()
                if self.current_char == 'n':
                    result += '\n'
                elif self.current_char == 't':
                    result += '\t'
                elif self.current_char == '\\':
                    result += '\\'
                elif self.current_char == quote_char:
                    result += quote_char
                else:
                    result += self.current_char
            else:
                result += self.current_char
            self.advance()
        self.advance()  # 跳过结束引号
        return result

    def skip_comment(self):
        # 跳过单行注释 //
        if self.current_char == '/' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '/':
            while self.current_char is not None and self.current_char != '\n':
                self.advance()
        # 跳过多行注释 /* */
        elif self.current_char == '/' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '*':
            self.advance()  # skip /
            self.advance()  # skip *
            while self.current_char is not None:
                if self.current_char == '*' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '/':
                    self.advance()  # skip *
                    self.advance()  # skip /
                    break
                self.advance()


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
            # 跳过注释
            if self.current_char == '/' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] in ['/', '*']:
                self.skip_comment()
                continue
            if self.current_char.isdigit():
                tokens.append(Token('INTEGER', self.integer()))
                continue
            if self.current_char == '"':
                tokens.append(Token('STRING', self.string('"')))
                continue
            if self.current_char == "'":
                tokens.append(Token('STRING', self.string("'")))
                continue

            if self.current_char.isalpha() or self.current_char == '_':
                ident = self.identifier()
                if ident in ['if', 'else', 'for', 'try', 'catch', 'func']:
                    tokens.append(Token('KEYWORD', ident))
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
            elif self.current_char == '=':
                self.advance()
                if self.current_char == '=':
                    tokens.append(Token('EQ', '=='))
                    self.advance()
                else:
                    tokens.append(Token('ASSIGN', '='))
            elif self.current_char == '!':
                self.advance()
                if self.current_char == '=':
                    tokens.append(Token('NE', '!='))
                    self.advance()
                else:
                    raise ValueError("Invalid token !")
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
            else:
                # Provide more context about the error
                context_start = max(0, self.pos - 10)
                context_end = min(len(self.text), self.pos + 10)
                context = self.text[context_start:context_end]
                pointer = " " * (self.pos - context_start) + "^"
                raise ValueError(f"Invalid character '{self.current_char}' at position {self.pos}\nContext: ...{context}...\n          {pointer}")

        tokens.append(Token('EOF', None))
        return tokens
