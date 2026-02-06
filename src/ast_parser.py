from src.models import *

class HPLASTParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else None
        self.indent_level = 0

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def peek(self, offset=1):
        peek_pos = self.pos + offset
        if peek_pos < len(self.tokens):
            return self.tokens[peek_pos]
        return None

    def parse_block(self):
        statements = []
        
        # 检查是否有花括号开始
        if self.current_token and self.current_token.type == 'LBRACE':
            self.expect('LBRACE')
            while self.current_token and self.current_token.type not in ['RBRACE', 'EOF']:
                statements.append(self.parse_statement())
            if self.current_token and self.current_token.type == 'RBRACE':
                self.expect('RBRACE')
        # 检查是否有冒号
        elif self.current_token and self.current_token.type == 'COLON':
            self.expect('COLON')
            # 冒号后的语句是缩进的，我们按顺序解析直到遇到结束标记
            while self.current_token and self.current_token.type not in ['RBRACE', 'EOF', 'KEYWORD']:
                # 检查是否是 else 或 catch 等结束当前块的关键字
                if self.current_token.type == 'KEYWORD' and self.current_token.value in ['else', 'catch']:
                    break
                statements.append(self.parse_statement())

        else:
            # 没有花括号也没有冒号，直接解析单个语句或语句序列
            while self.current_token and self.current_token.type not in ['RBRACE', 'EOF']:
                # 检查是否是结束当前块的关键字
                if self.current_token.type == 'KEYWORD' and self.current_token.value in ['else', 'catch']:
                    break
                statements.append(self.parse_statement())
        
        return BlockStatement(statements)

    def parse_statement(self):

        if not self.current_token:
            return None
            
        if self.current_token.type == 'IDENTIFIER':
            if self.current_token.value == 'echo':
                self.advance()  # echo
                expr = self.parse_expression()
                return EchoStatement(expr)
            # 检查下一个标记是否为赋值
            elif self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == 'ASSIGN':
                var_name = self.current_token.value
                self.advance()  # 标识符
                self.advance()  # 赋值
                expr = self.parse_expression()
                return AssignmentStatement(var_name, expr)
            elif self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == 'INCREMENT':
                var_name = self.current_token.value
                self.advance()  # 标识符
                self.advance()  # 自增
                return IncrementStatement(var_name)
            else:
                # 表达式语句（例如，调用）
                expr = self.parse_expression()
                return expr  # 调用是表达式但可以是语句

        elif self.current_token.type == 'KEYWORD':
            if self.current_token.value == 'if':
                return self.parse_if()
            elif self.current_token.value == 'for':
                return self.parse_for()
            elif self.current_token.value == 'try':
                return self.parse_try()
            elif self.current_token.value == 'return':
                return self.parse_return()
            else:
                raise ValueError(f"Unexpected keyword {self.current_token.value}")
        else:
            raise ValueError(f"Unexpected token {self.current_token}")

    def parse_if(self):
        self.advance()  # if
        self.expect('LPAREN')
        condition = self.parse_expression()
        self.expect('RPAREN')
        
        then_block = self.parse_block()
        
        else_block = None

        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'else':
            self.advance()
            else_block = self.parse_block()
        return IfStatement(condition, then_block, else_block)

    def parse_for(self):
        self.advance()  # for
        self.expect('LPAREN')
        
        # 解析初始化
        init = None
        if self.current_token and self.current_token.type == 'IDENTIFIER':
            var_name = self.current_token.value
            self.advance()
            self.expect('ASSIGN')
            expr = self.parse_expression()
            init = AssignmentStatement(var_name, expr)
        
        self.expect('SEMICOLON')
        condition = self.parse_expression()
        self.expect('SEMICOLON')
        
        # 解析增量表达式
        increment_expr = None
        if self.current_token and self.current_token.type == 'IDENTIFIER':
            var_name = self.current_token.value
            self.advance()
            if self.current_token and self.current_token.type == 'INCREMENT':
                self.advance()
                increment_expr = PostfixIncrement(Variable(var_name))
            else:
                # 可能是赋值增量，如 i = i + 1
                increment_expr = self.parse_expression()
        else:
            increment_expr = self.parse_expression()
        
        self.expect('RPAREN')
        body = self.parse_block()
        return ForStatement(init, condition, increment_expr, body)

    def parse_try(self):
        self.advance()  # try
        try_block = self.parse_block()
        
        # 检查 catch
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'catch':
            self.advance()  # catch
            self.expect('LPAREN')
            catch_var = self.expect('IDENTIFIER').value
            self.expect('RPAREN')
            catch_block = self.parse_block()
            return TryCatchStatement(try_block, catch_var, catch_block)
        else:
            raise ValueError("Expected catch after try")

    def parse_return(self):
        self.advance()  # return
        expr = None
        if self.current_token and self.current_token.type != 'SEMICOLON' and self.current_token.type != 'RBRACE' and self.current_token.type != 'EOF':
            expr = self.parse_expression()
        return ReturnStatement(expr)

    def parse_expression(self):
        return self.parse_binary_op()


    def parse_binary_op(self):
        left = self.parse_primary()
        while self.current_token and self.current_token.type in ['PLUS', 'MINUS', 'MUL', 'DIV', 'MOD', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE']:
            op = self.current_token.value
            self.advance()
            right = self.parse_primary()
            left = BinaryOp(left, op, right)
        return left

    def parse_primary(self):
        if self.current_token.type == 'INTEGER':
            value = self.current_token.value
            self.advance()
            return IntegerLiteral(value)
        elif self.current_token.type == 'STRING':
            value = self.current_token.value
            self.advance()
            return StringLiteral(value)
        elif self.current_token.type == 'IDENTIFIER':
            name = self.current_token.value
            self.advance()
            if self.current_token and self.current_token.type == 'LPAREN':
                # 函数调用
                self.advance()
                args = []
                if self.current_token and self.current_token.type != 'RPAREN':
                    args.append(self.parse_expression())
                    while self.current_token and self.current_token.type == 'COMMA':
                        self.advance()
                        args.append(self.parse_expression())
                self.expect('RPAREN')
                return FunctionCall(name, args)
            elif self.current_token and self.current_token.type == 'DOT':
                # 方法调用
                self.advance()
                method_name = self.expect('IDENTIFIER').value
                self.expect('LPAREN')
                args = []
                if self.current_token and self.current_token.type != 'RPAREN':
                    args.append(self.parse_expression())
                    while self.current_token and self.current_token.type == 'COMMA':
                        self.advance()
                        args.append(self.parse_expression())
                self.expect('RPAREN')
                return MethodCall(Variable(name), method_name, args)
            elif self.current_token and self.current_token.type == 'INCREMENT':
                # 后缀递增
                self.advance()
                return PostfixIncrement(Variable(name))
            else:
                return Variable(name)
        else:
            raise ValueError(f"Unexpected token {self.current_token}")

    def expect(self, type):
        if not self.current_token or self.current_token.type != type:
            raise ValueError(f"Expected {type}, got {self.current_token}")
        token = self.current_token
        self.advance()
        return token

    def expect_keyword(self, value):
        if not self.current_token or self.current_token.type != 'KEYWORD' or self.current_token.value != value:
            raise ValueError(f"Expected keyword {value}, got {self.current_token}")
        self.advance()
