"""
HPL AST 解析器模块

该模块负责将词法分析器生成的 Token 序列解析为抽象语法树（AST），
是解释器的第二阶段。支持解析各种语句（if、for、while、try-catch、赋值等）
和表达式（二元运算、函数调用、方法调用等）。

关键类：
- HPLASTParser: AST 解析器，将 Token 列表转换为语句块和表达式树

支持的语法结构：
- 控制流：if-else、for 循环、while 循环、try-catch
- 语句：赋值、自增、返回、echo 输出、break、continue
- 表达式：二元运算、函数调用、方法调用、变量、字面量、逻辑运算
"""

try:
    from hpl_runtime.core.models import *
    from hpl_runtime.utils.exceptions import HPLSyntaxError
except ImportError:
    from hpl_runtime.core.models import *
    from hpl_runtime.utils.exceptions import HPLSyntaxError




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

    def _get_position(self):
        """获取当前 token 的位置信息"""
        if self.current_token:
            return self.current_token.line, self.current_token.column
        return None, None


    def _is_block_terminator(self):
        """检查当前 token 是否是块结束标记"""
        if not self.current_token:
            return True
        if self.current_token.type in ['DEDENT', 'RBRACE', 'EOF']:
            return True
        if self.current_token.type == 'KEYWORD' and self.current_token.value in ['else', 'catch']:
            return True
        return False

    def _consume_indent(self):
        """消费 INDENT token（如果存在）"""
        if self.current_token and self.current_token.type == 'INDENT':
            self.expect('INDENT')

    def _parse_statements_until_end(self):
        """解析语句直到遇到块结束标记"""
        statements = []
        while not self._is_block_terminator():
            self._consume_indent()
            if self._is_block_terminator():
                break
            statements.append(self.parse_statement())
        return statements

    def parse_block(self):
        """解析语句块，支持多种语法格式"""
        statements = []
        
        # 情况1: 以 INDENT 开始（函数体等情况）
        if self.current_token and self.current_token.type == 'INDENT':
            self.expect('INDENT')
            statements = self._parse_statements_until_end()
            if self.current_token and self.current_token.type == 'DEDENT':
                self.expect('DEDENT')
        
        # 情况2: 以花括号开始
        elif self.current_token and self.current_token.type == 'LBRACE':
            self.expect('LBRACE')
            # 跳过可能的 INDENT token（花括号内的缩进）
            if self.current_token and self.current_token.type == 'INDENT':
                self.advance()
            while self.current_token and self.current_token.type not in ['RBRACE', 'DEDENT', 'EOF']:
                statements.append(self.parse_statement())
            # 跳过可能的 DEDENT token
            if self.current_token and self.current_token.type == 'DEDENT':
                self.advance()
            if self.current_token and self.current_token.type == 'RBRACE':
                self.expect('RBRACE')


        
        # 情况3: 以冒号开始（缩进敏感语法）
        elif self.current_token and self.current_token.type == 'COLON':
            self.expect('COLON')
            if self.current_token and self.current_token.type == 'INDENT':
                self.expect('INDENT')
                statements = self._parse_statements_until_end()
                if self.current_token and self.current_token.type == 'DEDENT':
                    self.expect('DEDENT')
            else:
                # 单行语句
                while self.current_token and self.current_token.type not in ['RBRACE', 'EOF', 'KEYWORD']:
                    if self.current_token.type == 'KEYWORD' and self.current_token.value in ['else', 'catch']:
                        break
                    statements.append(self.parse_statement())
        
        # 情况4: 没有花括号也没有冒号，直接解析单个语句或语句序列
        else:
            statements = self._parse_statements_until_end()
        
        return BlockStatement(statements)

    def parse_statement(self):
        if not self.current_token:
            return None
        
        # 处理 return 语句
        if self.current_token.type == 'KEYWORD' and self.current_token.value == 'return':
            self.advance()
            expr = None
            if self.current_token and self.current_token.type not in ['SEMICOLON', 'RBRACE', 'EOF']:
                expr = self.parse_expression()
            return ReturnStatement(expr)
        
        # 处理 break 语句
        if self.current_token.type == 'KEYWORD' and self.current_token.value == 'break':
            self.advance()
            return BreakStatement()
        
        # 处理 continue 语句
        if self.current_token.type == 'KEYWORD' and self.current_token.value == 'continue':
            self.advance()
            return ContinueStatement()
        
        # 处理 import 语句
        if self.current_token.type == 'KEYWORD' and self.current_token.value == 'import':
            return self.parse_import_statement()
        
        # 处理 if 语句

        if self.current_token.type == 'KEYWORD' and self.current_token.value == 'if':
            return self.parse_if_statement()
        
        # 处理 for 语句
        if self.current_token.type == 'KEYWORD' and self.current_token.value == 'for':
            return self.parse_for_statement()
        
        # 处理 while 语句
        if self.current_token.type == 'KEYWORD' and self.current_token.value == 'while':
            return self.parse_while_statement()
        
        # 处理 try-catch 语句
        if self.current_token.type == 'KEYWORD' and self.current_token.value == 'try':
            return self.parse_try_catch_statement()
        
        # 处理 echo 语句
        if self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'echo':
            self.advance()
            expr = self.parse_expression()
            return EchoStatement(expr)
        
        # 处理赋值或表达式语句
        if self.current_token.type == 'IDENTIFIER':
            # 先保存当前位置，以便需要时回退
            start_pos = self.pos
            
            name = self.current_token.value
            self.advance()
            
            # 检查是否是数组赋值：arr[index] = value
            if self.current_token and self.current_token.type == 'LBRACKET':
                # 解析数组索引
                self.advance()  # 跳过 '['
                index_expr = self.parse_expression()
                self.expect('RBRACKET')  # 期望 ']'
                
                # 检查是否是赋值
                if self.current_token and self.current_token.type == 'ASSIGN':
                    self.advance()  # 跳过 '='
                    value_expr = self.parse_expression()
                    return ArrayAssignmentStatement(name, index_expr, value_expr)
                else:
                    # 不是赋值，回退并作为数组访问表达式处理
                    self.pos = start_pos
                    self.current_token = self.tokens[self.pos]
                    expr = self.parse_expression()
                    return expr
            
            # 检查是否是属性赋值：obj.property = value
            if self.current_token and self.current_token.type == 'DOT':
                self.advance()  # 跳过 '.'
                prop_name = self.expect('IDENTIFIER').value
                
                # 检查是否是赋值
                if self.current_token and self.current_token.type == 'ASSIGN':
                    self.advance()  # 跳过 '='
                    value_expr = self.parse_expression()
                    # 创建属性赋值语句，使用特殊格式存储
                    # 这里我们使用 ArrayAssignmentStatement 的变体，或者创建新的语句类型
                    # 为了简单，我们使用 MethodCall 作为左值，但需要在 evaluator 中特殊处理
                    return AssignmentStatement(f"{name}.{prop_name}", value_expr)
                else:
                    # 不是赋值，回退并作为方法调用表达式处理
                    self.pos = start_pos
                    self.current_token = self.tokens[self.pos]
                    expr = self.parse_expression()
                    return expr
            
            # 检查是否是自增
            if self.current_token and self.current_token.type == 'INCREMENT':
                self.advance()
                return IncrementStatement(name)
            
            # 检查是否是赋值
            if self.current_token and self.current_token.type == 'ASSIGN':
                self.advance()
                expr = self.parse_expression()
                return AssignmentStatement(name, expr)
            
            # 否则是表达式（如方法调用）
            # 回退并解析为表达式
            self.pos = start_pos
            self.current_token = self.tokens[self.pos]
            expr = self.parse_expression()
            return expr


        
        # 默认解析为表达式
        return self.parse_expression()

    def parse_if_statement(self):
        self.expect_keyword('if')
        self.expect('LPAREN')
        condition = self.parse_expression()
        self.expect('RPAREN')
        
        then_block = self.parse_block()
        
        else_block = None
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'else':
            self.advance()
            else_block = self.parse_block()
        
        return IfStatement(condition, then_block, else_block)

    def parse_for_statement(self):
        self.expect_keyword('for')
        self.expect('LPAREN')
        
        # 解析初始化
        init = self.parse_statement()
        self.expect('SEMICOLON')
        
        # 解析条件
        condition = self.parse_expression()
        self.expect('SEMICOLON')
        
        # 解析增量
        increment_expr = self.parse_expression()
        self.expect('RPAREN')
        
        body = self.parse_block()
        
        return ForStatement(init, condition, increment_expr, body)

    def parse_while_statement(self):
        self.expect_keyword('while')
        self.expect('LPAREN')
        condition = self.parse_expression()
        self.expect('RPAREN')
        
        body = self.parse_block()
        
        return WhileStatement(condition, body)

    def parse_try_catch_statement(self):
        self.expect_keyword('try')
        try_block = self.parse_block()
        
        self.expect_keyword('catch')
        self.expect('LPAREN')
        catch_var = self.expect('IDENTIFIER').value
        self.expect('RPAREN')
        
        catch_block = self.parse_block()
        
        return TryCatchStatement(try_block, catch_var, catch_block)

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        """解析逻辑或 (||)"""
        left = self.parse_and()
        
        while self.current_token and self.current_token.type == 'OR':
            self.advance()
            right = self.parse_and()
            left = BinaryOp(left, '||', right)
        
        return left

    def parse_and(self):
        """解析逻辑与 (&&)"""
        left = self.parse_equality()
        
        while self.current_token and self.current_token.type == 'AND':
            self.advance()
            right = self.parse_equality()
            left = BinaryOp(left, '&&', right)
        
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        
        while self.current_token and self.current_token.type in ['EQ', 'NE']:
            op = '==' if self.current_token.type == 'EQ' else '!='
            self.advance()
            right = self.parse_comparison()
            left = BinaryOp(left, op, right)
        
        return left

    def parse_comparison(self):
        left = self.parse_additive()
        
        while self.current_token and self.current_token.type in ['LT', 'LE', 'GT', 'GE']:
            op_map = {
                'LT': '<',
                'LE': '<=',
                'GT': '>',
                'GE': '>='
            }
            op = op_map[self.current_token.type]
            self.advance()
            right = self.parse_additive()
            left = BinaryOp(left, op, right)
        
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        
        while self.current_token and self.current_token.type in ['PLUS', 'MINUS']:
            op = '+' if self.current_token.type == 'PLUS' else '-'
            self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(left, op, right)
        
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        
        while self.current_token and self.current_token.type in ['MUL', 'DIV', 'MOD']:
            op_map = {
                'MUL': '*',
                'DIV': '/',
                'MOD': '%'
            }
            op = op_map[self.current_token.type]
            self.advance()
            right = self.parse_unary()
            left = BinaryOp(left, op, right)
        
        return left

    def parse_unary(self):
        # 处理一元运算符：! 和 -
        if self.current_token and self.current_token.type == 'NOT':
            self.advance()
            operand = self.parse_unary()
            return UnaryOp('!', operand)
        
        if self.current_token and self.current_token.type == 'MINUS':
            self.advance()
            operand = self.parse_unary()
            # 将 -x 转换为 0 - x
            return BinaryOp(IntegerLiteral(0), '-', operand)
        
        return self.parse_primary()

    def parse_primary(self):
        if not self.current_token:
            line, column = self._get_position()
            raise HPLSyntaxError(
                "Unexpected end of input",
                line=line,
                column=column
            )

        
        # 处理布尔值
        if self.current_token.type == 'BOOLEAN':
            value = self.current_token.value
            self.advance()
            return BooleanLiteral(value)
        
        # 处理数字（整数或浮点数）
        if self.current_token.type == 'NUMBER':
            value = self.current_token.value
            self.advance()
            if isinstance(value, int):
                return IntegerLiteral(value)
            else:
                return FloatLiteral(value)
        
        # 处理字符串
        if self.current_token.type == 'STRING':
            value = self.current_token.value
            self.advance()
            return StringLiteral(value)
        
        # 处理标识符（变量、函数调用、方法调用）
        if self.current_token.type == 'IDENTIFIER':
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
                # 方法调用或模块函数调用
                # 支持链式调用：this.parent.init("矩形")
                current_expr = Variable(name)
                
                while self.current_token and self.current_token.type == 'DOT':
                    self.advance()
                    member_name = self.expect('IDENTIFIER').value
                    
                    # 检查是否是函数调用（带括号）
                    if self.current_token and self.current_token.type == 'LPAREN':
                        self.advance()
                        args = []
                        if self.current_token and self.current_token.type != 'RPAREN':
                            args.append(self.parse_expression())
                            while self.current_token and self.current_token.type == 'COMMA':
                                self.advance()
                                args.append(self.parse_expression())
                        self.expect('RPAREN')
                        current_expr = MethodCall(current_expr, member_name, args)
                    else:
                        # 模块常量访问或属性访问，如 math.PI
                        # 作为属性访问处理，在运行时解析
                        current_expr = MethodCall(current_expr, member_name, [])
                
                return current_expr


            
            elif self.current_token and self.current_token.type == 'INCREMENT':
                # 后缀递增
                self.advance()
                return PostfixIncrement(Variable(name))
            
            elif self.current_token and self.current_token.type == 'LBRACKET':
                # 数组访问
                self.advance()
                index = self.parse_expression()
                self.expect('RBRACKET')
                return ArrayAccess(Variable(name), index)
            
            else:
                return Variable(name)
        
        # 处理括号表达式
        if self.current_token.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr
        
        # 处理数组字面量
        if self.current_token.type == 'LBRACKET':
            self.advance()
            elements = []
            if self.current_token and self.current_token.type != 'RBRACKET':
                elements.append(self.parse_expression())
                while self.current_token and self.current_token.type == 'COMMA':
                    self.advance()
                    elements.append(self.parse_expression())
            self.expect('RBRACKET')
            return ArrayLiteral(elements)
        
        # 处理字典/对象字面量
        if self.current_token.type == 'LBRACE':
            self.advance()
            # 跳过可能的 INDENT token
            if self.current_token and self.current_token.type == 'INDENT':
                self.advance()
            pairs = {}
            if self.current_token and self.current_token.type != 'RBRACE':
                # 解析第一个键值对
                key = self.expect('STRING').value
                self.expect('COLON')
                value = self.parse_expression()
                pairs[key] = value
                # 解析后续的键值对
                while self.current_token and self.current_token.type == 'COMMA':
                    self.advance()
                    # 跳过可能的 INDENT token
                    if self.current_token and self.current_token.type == 'INDENT':
                        self.advance()
                    if self.current_token and self.current_token.type == 'RBRACE':
                        break
                    key = self.expect('STRING').value
                    self.expect('COLON')
                    value = self.parse_expression()
                    pairs[key] = value
            # 跳过可能的 DEDENT token
            if self.current_token and self.current_token.type == 'DEDENT':
                self.advance()
            self.expect('RBRACE')
            return DictionaryLiteral(pairs)
        
        line, column = self._get_position()
        raise HPLSyntaxError(
            f"Unexpected token {self.current_token}",
            line=line,
            column=column
        )



    def expect(self, type):
        if not self.current_token or self.current_token.type != type:
            line, column = self._get_position()
            raise HPLSyntaxError(
                f"Expected {type}, got {self.current_token}",
                line=line,
                column=column
            )
        token = self.current_token
        self.advance()
        return token


    def expect_keyword(self, value):
        if not self.current_token or self.current_token.type != 'KEYWORD' or self.current_token.value != value:
            line, column = self._get_position()
            raise HPLSyntaxError(
                f"Expected keyword '{value}', got {self.current_token}",
                line=line,
                column=column
            )
        self.advance()


    def parse_import_statement(self):
        """解析 import 语句: import module_name [as alias]"""
        self.expect_keyword('import')
        
        # 获取模块名
        if not self.current_token or self.current_token.type != 'IDENTIFIER':
            line, column = self._get_position()
            raise HPLSyntaxError(
                f"Expected module name after 'import', got {self.current_token}",
                line=line,
                column=column
            )
        
        module_name = self.current_token.value
        self.advance()
        
        # 检查是否有别名
        alias = None
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'as':
            self.advance()
            if not self.current_token or self.current_token.type != 'IDENTIFIER':
                line, column = self._get_position()
                raise HPLSyntaxError(
                    f"Expected alias name after 'as', got {self.current_token}",
                    line=line,
                    column=column
                )
            alias = self.current_token.value
            self.advance()
        
        return ImportStatement(module_name, alias)



# BreakStatement 和 ContinueStatement 类已在 models.py 中定义
