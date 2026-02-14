"""
HPL 词法分析器模块

该模块负责将 HPL 源代码转换为 Token 序列，是解释器的第一阶段。
包含 Token 类和 HPLLexer 类，支持识别关键字、标识符、运算符、
字符串和数字等各种词法单元。

关键类：
- Token: 表示单个词法单元，包含类型和值
- HPLLexer: 词法分析器，将源代码字符串转换为 Token 列表
"""

from __future__ import annotations
from typing import Any, Optional, Union

from hpl_runtime.utils.exceptions import HPLSyntaxError
from hpl_runtime.utils.text_utils import skip_whitespace, skip_comment


class Token:
    def __init__(self, type: str, value: Any, line: int = 0, column: int = 0) -> None:
        self.type: str = type
        self.value: Any = value
        self.line: int = line
        self.column: int = column

    def __repr__(self) -> str:
        return f'Token({self.type}, {self.value}, line={self.line}, col={self.column})'


class HPLLexer:
    def __init__(self, text: str, start_line: int = 1, start_column: int = 1) -> None:
        self.text: str = text
        self.pos: int = 0
        self.current_char: Optional[str] = self.text[0] if self.text else None
        # 行号和列号跟踪
        self.line: int = start_line
        self.column: int = start_column - 1  # 减1是因为advance()会先增加column
        # 缩进跟踪
        self.indent_stack: list[int] = [0]  # 缩进级别栈，初始为0
        self.at_line_start: bool = True  # 标记是否在行首

    def advance(self) -> None:
        if self.current_char == '\n':
            self.line += 1
            self.column = 0  # 换行后重置为0，下一个字符会变为1
        else:
            self.column += 1
        
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def peek(self) -> Optional[str]:
        """查看下一个字符但不移动位置"""
        peek_pos = self.pos + 1
        if peek_pos > len(self.text) - 1:
            return None
        else:
            return self.text[peek_pos]

    def skip_whitespace(self) -> None:
        """跳过非换行的空白字符"""
        while self.current_char is not None and self.current_char.isspace() and self.current_char != '\n':
            self.advance()

    def number(self) -> Union[int, float]:
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

    def string(self) -> str:
        result = ''
        self.advance()  # 跳过开始引号
        while self.current_char is not None and self.current_char != '"':
            # 处理转义序列
            if self.current_char == '\\':
                self.advance()  # 跳过反斜杠
                if self.current_char is None:
                    break
                elif self.current_char == 'n':
                    result += '\n'
                elif self.current_char == 't':
                    result += '\t'
                elif self.current_char == 'r':
                    result += '\r'
                elif self.current_char == '\\':
                    result += '\\'
                elif self.current_char == '"':
                    result += '"'
                else:
                    # 未知的转义序列，保留原样
                    result += '\\' + self.current_char
                self.advance()
            else:
                result += self.current_char
                self.advance()
        self.advance()  # 跳过结束引号
        return result

    def identifier(self) -> str:
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        return result

    def _handle_indentation(self, tokens: list[Token]) -> bool:
        """处理行首缩进，生成 INDENT/DEDENT 标记"""
        if not self.current_char.isspace():
            # 行首遇到非空白字符，检查是否需要生成 DEDENT
            current_indent = self.indent_stack[-1]
            if current_indent > 0:
                while 0 < self.indent_stack[-1]:
                    self.indent_stack.pop()
                    tokens.append(Token('DEDENT', self.indent_stack[-1], self.line, self.column))
            self.at_line_start = False
            return True  # 继续处理当前字符
        
        # 计算前导空格数
        indent = 0
        while self.current_char is not None and self.current_char.isspace() and self.current_char != '\n':
            if self.current_char == ' ':
                indent += 1
            elif self.current_char == '\t':
                indent += 4
            self.advance()
        
        # 跳过空行
        if self.current_char == '\n' or self.current_char is None:
            self.at_line_start = True
            if self.current_char == '\n':
                self.advance()
            return False  # 跳过本次循环
        
        # 生成 INDENT/DEDENT 标记
        current_indent = self.indent_stack[-1]
        if indent > current_indent:
            self.indent_stack.append(indent)
            tokens.append(Token('INDENT', indent, self.line, self.column))
        elif indent < current_indent:
            while indent < self.indent_stack[-1]:
                self.indent_stack.pop()
                tokens.append(Token('DEDENT', self.indent_stack[-1], self.line, self.column))
        
        self.at_line_start = False
        return False  # 跳过本次循环

    def _handle_number(self, token_line: int, token_column: int) -> Token:
        """处理数字，返回 NUMBER 标记"""
        return Token('NUMBER', self.number(), token_line, token_column)

    def _handle_string(self, token_line: int, token_column: int) -> Token:
        """处理字符串，返回 STRING 标记"""
        return Token('STRING', self.string(), token_line, token_column)

    def _handle_identifier(self, token_line: int, token_column: int) -> Token:
        """处理标识符和关键字，返回对应标记"""
        ident = self.identifier()
        keywords = {'if', 'else', 'for', 'while', 'try', 'catch', 'finally', 
                   'return', 'break', 'continue', 'import', 'throw', 'in'}
        
        if ident in keywords:
            return Token('KEYWORD', ident, token_line, token_column)
        elif ident in ('true', 'false'):
            return Token('BOOLEAN', ident == 'true', token_line, token_column)
        elif ident == 'null':
            return Token('NULL', None, token_line, token_column)
        else:
            return Token('IDENTIFIER', ident, token_line, token_column)

    # 运算符映射表：字符 -> (单字符标记类型, 双字符标记类型或None, 双字符值或None)
    _OPERATOR_MAP: dict[str, tuple[str, Optional[str], Optional[str]]] = {
        '+': ('PLUS', 'INCREMENT', '+'),
        '-': ('MINUS', None, None),
        '*': ('MUL', None, None),
        '/': ('DIV', None, None),
        '%': ('MOD', None, None),
        '(': ('LPAREN', None, None),
        ')': ('RPAREN', None, None),
        '{': ('LBRACE', None, None),
        '}': ('RBRACE', None, None),
        '[': ('LBRACKET', None, None),
        ']': ('RBRACKET', None, None),
        ';': ('SEMICOLON', None, None),
        ',': ('COMMA', None, None),
        '.': ('DOT', None, None),
        ':': ('COLON', None, None),
    }

    def _handle_operator(self, char: str, token_line: int, token_column: int) -> Token:
        """处理运算符，返回对应标记"""
        # 特殊处理需要检查第二个字符的运算符
        if char == '!':
            self.advance()
            if self.current_char == '=':
                self.advance()
                return Token('NE', '!=', token_line, token_column)
            return Token('NOT', '!', token_line, token_column)
        
        if char == '<':
            self.advance()
            if self.current_char == '=':
                self.advance()
                return Token('LE', '<=', token_line, token_column)
            return Token('LT', '<', token_line, token_column)
        
        if char == '>':
            self.advance()
            if self.current_char == '=':
                self.advance()
                return Token('GE', '>=', token_line, token_column)
            return Token('GT', '>', token_line, token_column)
        
        if char == '=':
            self.advance()
            if self.current_char == '=':
                self.advance()
                return Token('EQ', '==', token_line, token_column)
            elif self.current_char == '>':
                self.advance()
                return Token('ARROW', '=>', token_line, token_column)
            return Token('ASSIGN', '=', token_line, token_column)
        
        if char == '&':
            self.advance()
            if self.current_char == '&':
                self.advance()
                return Token('AND', '&&', token_line, token_column)
            raise HPLSyntaxError(
                f"Invalid character '&'",
                line=self.line,
                column=self.column,
                error_key='SYNTAX_UNEXPECTED_TOKEN'
            )
        
        if char == '|':
            self.advance()
            if self.current_char == '|':
                self.advance()
                return Token('OR', '||', token_line, token_column)
            raise HPLSyntaxError(
                f"Invalid character '|'",
                line=self.line,
                column=self.column,
                error_key='SYNTAX_UNEXPECTED_TOKEN'
            )

        # 使用映射表处理标准运算符
        self.advance()
        single_type, double_type, double_value = self._OPERATOR_MAP[char]
        
        # 检查双字符运算符（目前只有 ++）
        if double_type and self.current_char == char:
            self.advance()
            return Token(double_type, double_value + char, token_line, token_column)
        
        return Token(single_type, char, token_line, token_column)

    def skip_comment(self) -> None:
        """跳过从当前位置到行尾的注释"""
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    def tokenize(self) -> list[Token]:
        """词法分析主函数，将源代码转换为 Token 序列"""
        tokens: list[Token] = []
        
        while self.current_char is not None:
            # 处理行首缩进
            if self.at_line_start:
                if self._handle_indentation(tokens):
                    continue  # 需要继续处理当前字符
                else:
                    continue  # 已处理完缩进，跳过本次循环
            
            # 处理换行符
            if self.current_char == '\n':
                self.advance()
                self.at_line_start = True
                continue
            
            # 处理注释
            if self.current_char == '#':
                self.skip_comment()
                self.at_line_start = True
                continue
            
            # 跳过非行首的空白字符
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            # 记录当前 token 的位置
            token_line = self.line
            token_column = self.column
            self.at_line_start = False
            
            char = self.current_char
            
            # 分发处理不同类型的 token
            if char.isdigit():
                tokens.append(self._handle_number(token_line, token_column))
            elif char == '"':
                tokens.append(self._handle_string(token_line, token_column))
            elif char.isalpha() or char == '_':
                tokens.append(self._handle_identifier(token_line, token_column))
            elif char in self._OPERATOR_MAP or char in '!<>=&|':
                tokens.append(self._handle_operator(char, token_line, token_column))
            else:
                raise HPLSyntaxError(
                    f"Invalid character '{char}'",
                    line=self.line,
                    column=self.column,
                    error_key='SYNTAX_UNEXPECTED_TOKEN'
                )

        # 文件结束时，弹出所有缩进级别
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token('DEDENT', self.indent_stack[-1], self.line, self.column))
        
        tokens.append(Token('EOF', None, self.line, self.column))
        return tokens

