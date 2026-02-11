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
    from hpl_runtime.utils.parse_utils import get_token_position, is_block_terminator, skip_dedents
except ImportError:
    from hpl_runtime.core.models import *
    from hpl_runtime.utils.exceptions import HPLSyntaxError
    from hpl_runtime.utils.parse_utils import get_token_position, is_block_terminator, skip_dedents



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
        return get_token_position(self.current_token)


    def _is_block_terminator(self):
        """检查当前 token 是否是块结束标记"""
        # 使用工具函数，传入peek方法以便检查后续token
        return is_block_terminator(self.current_token, self.peek, self.indent_level)

    def _skip_dedents(self, min_indent_level=None):
        """跳过所有连续的 DEDENT token，但只跳过那些缩进级别大于等于min_indent_level的
        
        Args:
            min_indent_level: 最小缩进级别，只有DEDENT的value大于等于此值时才跳过
                           如果为None，则跳过所有DEDENT（向后兼容）
        """
        while self.current_token and self.current_token.type == 'DEDENT':
            if min_indent_level is not None:
                # 如果DEDENT的value大于等于min_indent_level，说明还在当前块内，可以跳过
                # 如果DEDENT的value小于min_indent_level，说明块已结束，应该停止
                if hasattr(self.current_token, 'value') and self.current_token.value is not None:
                    if self.current_token.value >= min_indent_level:
                        self.advance()
                    else:
                        break
                else:
                    # 没有value属性，保守处理，不跳过
                    break
            else:
                self.advance()


    def _skip_indents(self):
        """跳过所有连续的 INDENT token"""
        while self.current_token and self.current_token.type == 'INDENT':
            self.advance()

    def _consume_indent(self):
        """消费 INDENT token（如果存在）"""
        if self.current_token and self.current_token.type == 'INDENT':
            self.expect('INDENT')

    # ==================== 语句处理方法 ====================
    
    def _parse_return_statement(self):
        """解析 return 语句"""
        line, column = self._get_position()
        self.advance()  # 跳过 'return'
        expr = None
        if self.current_token and self.current_token.type not in ['SEMICOLON', 'RBRACE', 'EOF', 'DEDENT']:
            expr = self.parse_expression()
        return ReturnStatement(expr, line, column)

    
    def _parse_break_statement(self):
        """解析 break 语句"""
        line, column = self._get_position()
        self.advance()  # 跳过 'break'
        return BreakStatement(line, column)

    def _parse_continue_statement(self):
        """解析 continue 语句"""
        line, column = self._get_position()
        self.advance()  # 跳过 'continue'
        return ContinueStatement(line, column)

    def _parse_throw_statement(self):
        """解析 throw 语句"""
        line, column = self._get_position()
        self.advance()  # 跳过 'throw'
        expr = None
        if self.current_token and self.current_token.type not in ['SEMICOLON', 'RBRACE', 'EOF', 'DEDENT']:
            expr = self.parse_expression()
        return ThrowStatement(expr, line, column)

    def _parse_echo_statement(self):
        """解析 echo 语句"""
        line, column = self._get_position()
        self.advance()  # 跳过 'echo'
        expr = self.parse_expression()
        return EchoStatement(expr, line, column)
    
    def _parse_simple_assignment(self, name):
        """解析简单赋值：var = value"""
        self.advance()  # 跳过 '='
        expr = self.parse_expression()
        return AssignmentStatement(name, expr)
    
    def _parse_array_assignment(self, name):
        """解析数组赋值：arr[index] = value"""
        self.advance()  # 跳过 '['
        index_expr = self.parse_expression()
        self.expect('RBRACKET')
        self.advance()  # 跳过 '='
        value_expr = self.parse_expression()
        return ArrayAssignmentStatement(name, index_expr, value_expr)
    
    def _parse_property_assignment(self, name, prop_name):
        """解析属性赋值：obj.prop = value 或 obj.prop[index] = value"""
        self.advance()  # 跳过 '.'
        prop_name = self.expect('IDENTIFIER').value
        
        # 检查是否是属性后的数组索引：obj.prop[index]
        if self.current_token and self.current_token.type == 'LBRACKET':
            self.advance()  # 跳过 '['
            index_expr = self.parse_expression()
            self.expect('RBRACKET')
            self.advance()  # 跳过 '='
            value_expr = self.parse_expression()
            return ArrayAssignmentStatement(f"{name}.{prop_name}", index_expr, value_expr)
        
        # 简单属性赋值：obj.prop = value
        self.advance()  # 跳过 '='
        value_expr = self.parse_expression()
        return AssignmentStatement(f"{name}.{prop_name}", value_expr)
    
    def _parse_identifier_statement(self):
        """
        解析标识符开头的语句（赋值、自增、表达式）
        使用 lookahead 避免回溯
        """
        name = self.current_token.value
        
        # 使用 peek 进行 lookahead，避免保存/恢复位置
        next_token = self.peek(1)
        
        # 检查是否是简单赋值：var = value
        if next_token and next_token.type == 'ASSIGN':
            self.advance()  # 跳过变量名
            return self._parse_simple_assignment(name)
        
        # 检查是否是数组赋值：arr[index] = value
        if next_token and next_token.type == 'LBRACKET':
            # 需要进一步检查后面是否有 '='
            # 先跳过 '[' 和索引表达式，检查是否有 ']='
            # 简化处理：先解析，如果不是赋值再作为表达式
            self.advance()  # 跳过变量名
            self.advance()  # 跳过 '['
            index_expr = self.parse_expression()
            self.expect('RBRACKET')
            
            if self.current_token and self.current_token.type == 'ASSIGN':
                self.advance()  # 跳过 '='
                value_expr = self.parse_expression()
                return ArrayAssignmentStatement(name, index_expr, value_expr)
            else:
                # 不是赋值，构造数组访问表达式
                array_access = ArrayAccess(Variable(name), index_expr)
                # 继续解析可能的后续操作（如方法调用）
                return self._parse_expression_suffix(array_access)
        
        # 检查是否是属性访问：obj.prop...
        if next_token and next_token.type == 'DOT':
            self.advance()  # 跳过变量名
            self.advance()  # 跳过 '.'
            prop_name = self.expect('IDENTIFIER').value
            
            # 检查是否是属性后的数组索引：obj.prop[index]
            if self.current_token and self.current_token.type == 'LBRACKET':
                self.advance()  # 跳过 '['
                index_expr = self.parse_expression()
                self.expect('RBRACKET')
                
                if self.current_token and self.current_token.type == 'ASSIGN':
                    self.advance()  # 跳过 '='
                    value_expr = self.parse_expression()
                    return ArrayAssignmentStatement(f"{name}.{prop_name}", index_expr, value_expr)
                else:
                    # 不是赋值，构造属性数组访问表达式
                    prop_access = MethodCall(Variable(name), prop_name, [])
                    array_access = ArrayAccess(prop_access, index_expr)
                    return self._parse_expression_suffix(array_access)
            
            # 检查是否是属性赋值：obj.prop = value
            if self.current_token and self.current_token.type == 'ASSIGN':
                self.advance()  # 跳过 '='
                value_expr = self.parse_expression()
                return AssignmentStatement(f"{name}.{prop_name}", value_expr)
            
            # 构造属性访问表达式，继续解析可能的链式调用
            prop_access = MethodCall(Variable(name), prop_name, [])
            return self._parse_expression_suffix(prop_access)
        
        # 检查是否是自增：var++
        if next_token and next_token.type == 'INCREMENT':
            self.advance()  # 跳过变量名
            self.advance()  # 跳过 '++'
            return IncrementStatement(name)
        
        # 否则是表达式语句（函数调用、方法调用等）
        return self.parse_expression()
    
    def _parse_expression_suffix(self, expr):
        """解析表达式后缀（方法调用链、数组访问等）"""
        current_expr = expr
        
        while self.current_token:
            # 方法调用链：expr.method() 或 expr.method
            if self.current_token.type == 'DOT':
                self.advance()
                member_name = self.expect('IDENTIFIER').value
                
                if self.current_token and self.current_token.type == 'LPAREN':
                    # 方法调用
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
                    # 属性访问
                    current_expr = MethodCall(current_expr, member_name, [])
            
            # 直接方法调用：expr()
            elif self.current_token.type == 'LPAREN':
                # 方法调用（无点号，直接调用）
                self.advance()
                args = []
                if self.current_token and self.current_token.type != 'RPAREN':
                    args.append(self.parse_expression())
                    while self.current_token and self.current_token.type == 'COMMA':
                        self.advance()
                        args.append(self.parse_expression())
                self.expect('RPAREN')
                # 如果 current_expr 是 MethodCall（属性访问），转换为带参数的方法调用
                if isinstance(current_expr, MethodCall):
                    current_expr = MethodCall(current_expr.obj_name, current_expr.method_name, args)
                else:
                    # 函数调用
                    current_expr = FunctionCall(current_expr, args)
            
            # 数组访问：expr[index]
            elif self.current_token.type == 'LBRACKET':
                self.advance()
                index_expr = self.parse_expression()
                self.expect('RBRACKET')
                current_expr = ArrayAccess(current_expr, index_expr)
            
            # 后缀自增：expr++
            elif self.current_token.type == 'INCREMENT':
                self.advance()
                # 需要确保 expr 是变量或数组访问
                if isinstance(current_expr, Variable):
                    return PostfixIncrement(current_expr)
                elif isinstance(current_expr, ArrayAccess):
                    # 数组元素自增需要特殊处理
                    return PostfixIncrement(current_expr)
                else:
                    # 其他表达式不支持自增，返回原表达式
                    return current_expr  
            else:
                break
        
        return current_expr

    # 关键字分发表：关键字 -> 处理方法
    _STATEMENT_KEYWORDS = {
        'return': '_parse_return_statement',
        'break': '_parse_break_statement',
        'continue': '_parse_continue_statement',
        'throw': '_parse_throw_statement',
        'import': 'parse_import_statement',
        'if': 'parse_if_statement',
        'for': 'parse_for_statement',
        'while': 'parse_while_statement',
        'try': 'parse_try_catch_statement',
    }


    def _parse_statements_until_end(self):
        """解析语句直到遇到块结束标记"""
        statements = []
        # 块终止关键字
        block_terminators = ['else', 'catch', 'elif', 'finally']
        
        while self.current_token and self.current_token.type not in ['RBRACE', 'EOF']:
            # 首先检查是否是块终止关键字
            if self.current_token.type == 'KEYWORD' and self.current_token.value in block_terminators:
                return statements
            
            # 检查是否是DEDENT（缩进减少表示块结束）
            if self.current_token.type == 'DEDENT':
                if hasattr(self.current_token, 'value') and self.current_token.value is not None:
                    # 如果新的缩进级别小于父级块的级别，说明块已结束
                    if self.current_token.value < self.indent_level:
                        return statements
                    # 否则，跳过这个DEDENT（还在当前块内）
                    else:
                        self.advance()
                        continue
                else:
                    # 没有value属性，保守地视为终止符
                    return statements
            
            # 消费INDENT（如果存在）
            self._consume_indent()
            
            # 再次检查块终止符（消费INDENT后可能遇到）
            if self.current_token and self.current_token.type in ['RBRACE', 'EOF']:
                break
            
            # 再次检查DEDENT（消费INDENT后可能遇到）
            if self.current_token and self.current_token.type == 'DEDENT':
                if hasattr(self.current_token, 'value') and self.current_token.value is not None:
                    if self.current_token.value < self.indent_level:
                        break
                    else:
                        self.advance()
                        continue
                else:
                    break
            
            # 再次检查块终止关键字
            if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value in block_terminators:
                break
            
            # 解析语句
            if self.current_token:
                statements.append(self.parse_statement())
        
        return statements    
    
    def parse_block(self):
        """解析语句块，支持多种语法格式"""
        statements = []
        
        # 情况1: 以冒号开始（缩进敏感语法）- 优先检查，因为冒号是明确的块开始标记
        if self.current_token and self.current_token.type == 'COLON':
            self.expect('COLON')
            # 如果冒号后面跟着花括号，处理为花括号块
            if self.current_token and self.current_token.type == 'LBRACE':
                # 情况1b: 冒号后跟花括号 {: ... }
                return self._parse_brace_block()
            elif self.current_token and self.current_token.type == 'INDENT':

                # 保存当前缩进级别并设置新的缩进级别
                saved_indent_level = self.indent_level
                block_indent_level = self.current_token.value
                self.indent_level = block_indent_level
                self.expect('INDENT')
                statements = self._parse_statements_until_end()
                # 恢复之前的缩进级别
                self.indent_level = saved_indent_level
                # 跳过所有连续的 DEDENT token，直到遇到非 DEDENT 或缩进级别小于父级
                while self.current_token and self.current_token.type == 'DEDENT':
                    if hasattr(self.current_token, 'value') and self.current_token.value < saved_indent_level:
                        self.advance()
                    else:
                        break
            else:
                # 单行语句
                # 只在这些特定关键字处停止（块终止符）
                block_terminators = ['else', 'catch', 'elif', 'finally']
                while self.current_token and self.current_token.type not in ['RBRACE', 'EOF']:
                    if self.current_token.type == 'KEYWORD' and self.current_token.value in block_terminators:
                        break
                    # 检查DEDENT作为块终止符 - 使用小于当前缩进级别
                    if self.current_token.type == 'DEDENT':
                        if hasattr(self.current_token, 'value') and self.current_token.value is not None:
                            if self.current_token.value < self.indent_level:
                                break
                        else:
                            break

                    statements.append(self.parse_statement())
                    # 如果已经解析了一个语句，就退出（单行语句块只包含一个语句）
                    if len(statements) >= 1:
                        break
                # 跳过块结束后的DEDENT
                self._skip_dedents(self.indent_level)
        
        # 情况2: 以花括号开始
        elif self.current_token and self.current_token.type == 'LBRACE':
            return self._parse_brace_block()
        
        # 情况3: 以 INDENT 开始（函数体等情况）
        elif self.current_token and self.current_token.type == 'INDENT':
            # 保存当前缩进级别并设置新的缩进级别
            saved_indent_level = self.indent_level
            block_indent_level = self.current_token.value
            self.indent_level = block_indent_level
            self.expect('INDENT')
            statements = self._parse_statements_until_end()
            # 恢复之前的缩进级别
            self.indent_level = saved_indent_level
            # 跳过所有连续的 DEDENT token，直到遇到非 DEDENT 或缩进级别小于父级
            while self.current_token and self.current_token.type == 'DEDENT':
                if hasattr(self.current_token, 'value') and self.current_token.value < saved_indent_level:
                    self.advance()
                else:
                    break

        # 情况4: 没有花括号也没有冒号，直接解析单个语句或语句序列
        else:
            statements = self._parse_statements_until_end()
        
        return BlockStatement(statements)


    def _parse_brace_block(self):
        """解析花括号块"""
        statements = []
        self.expect('LBRACE')
        # 跳过可能的 INDENT token（花括号内的缩进）
        self._skip_indents()
        while self.current_token and self.current_token.type not in ['RBRACE', 'EOF']:
            # 跳过 DEDENT token（处理空行后的缩进变化）
            if self.current_token and self.current_token.type == 'DEDENT':
                self.advance()
                continue
            # 跳过 INDENT token
            self._skip_indents()
            if self.current_token and self.current_token.type in ['RBRACE', 'EOF']:
                break
            # 检查是否是关键字终止符
            if self.current_token.type == 'KEYWORD' and self.current_token.value in ['else', 'catch', 'elif', 'finally']:
                break
            statements.append(self.parse_statement())
        # 跳过可能的 DEDENT token
        self._skip_dedents()
        if self.current_token and self.current_token.type == 'RBRACE':
            self.expect('RBRACE')
        return BlockStatement(statements)


    def parse_statement(self):
        """解析语句 - 使用分发表优化关键字查找"""
        # 跳过行首的 INDENT token
        self._skip_indents()
        
        # 跳过行首的 DEDENT token（处理块结束后的缩进变化）
        # 使用当前缩进级别，避免跳过应该终止块的DEDENT
        self._skip_dedents(self.indent_level)
        
        if not self.current_token:
            return None
        
        # 处理关键字语句（使用分发表 O(1) 查找）

        if self.current_token.type == 'KEYWORD':
            keyword = self.current_token.value
            handler_name = self._STATEMENT_KEYWORDS.get(keyword)
            if handler_name:
                handler = getattr(self, handler_name)
                return handler()
        
        # 处理 echo 语句（特殊标识符）
        if self.current_token.type == 'IDENTIFIER' and self.current_token.value == 'echo':
            return self._parse_echo_statement()
        
        # 处理标识符开头的语句（赋值、自增、表达式）
        if self.current_token.type == 'IDENTIFIER':
            return self._parse_identifier_statement()
        
        # 默认解析为表达式
        return self.parse_expression()


    def parse_if_statement(self):
        self.expect_keyword('if')
        self.expect('LPAREN')
        condition = self.parse_expression()
        self.expect('RPAREN')
        
        # 在解析if块之前，跳过任何DEDENT token（处理空行后的缩进变化）
        # 使用当前缩进级别，避免跳过应该终止块的DEDENT
        self._skip_dedents(self.indent_level)
        
        then_block = self.parse_block()
        
        else_block = None
        # 在检查else之前，可能需要跳过多个DEDENT token
        # 持续检查：如果当前是DEDENT，且后面跟着else，则跳过DEDENT
        while self.current_token and self.current_token.type == 'DEDENT':
            # 查看DEDENT后的token
            next_token = self.peek(1)
            if next_token and next_token.type == 'KEYWORD' and next_token.value == 'else':
                # 这是当前if的else，跳过这个DEDENT并停止
                self.advance()
                break
            # 如果不是通向else的DEDENT，检查是否应该终止
            # 如果DEDENT的value小于当前缩进级别，说明块已结束
            if hasattr(self.current_token, 'value') and self.current_token.value is not None:
                if self.current_token.value < self.indent_level:
                    # 块已结束，停止查找else
                    break

            # 否则跳过这个DEDENT继续检查
            self.advance()
        
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'else':
            self.advance()
            # 跳过else后的DEDENT（如果有）
            if self.current_token and self.current_token.type == 'DEDENT':
                self.advance()
            else_block = self.parse_block()
        
        return IfStatement(condition, then_block, else_block)


    def parse_for_statement(self):
        self.expect_keyword('for')
        self.expect('LPAREN')
        
        # for in 语法: for (var in iterable)
        var_name = self.current_token.value
        self.advance()  # 跳过变量名
        self.expect_keyword('in')
        iterable_expr = self.parse_expression()
        self.expect('RPAREN')
        body = self.parse_block()
        return ForInStatement(var_name, iterable_expr, body)


    def parse_while_statement(self):
        self.expect_keyword('while')
        self.expect('LPAREN')
        condition = self.parse_expression()
        self.expect('RPAREN')
        
        body = self.parse_block()
        
        return WhileStatement(condition, body)

    def parse_try_catch_statement(self):
        line, column = self._get_position()
        self.expect_keyword('try')
        try_block = self.parse_block()
        
        # 解析多个 catch 子句
        catch_clauses = []
        
        while True:
            # 在检查catch之前，可能需要跳过多个DEDENT token
            while self.current_token and self.current_token.type == 'DEDENT':
                next_token = self.peek(1)
                if next_token and next_token.type == 'KEYWORD' and next_token.value in ['catch', 'finally']:
                    self.advance()
                    break
                if hasattr(self.current_token, 'value') and self.current_token.value is not None:
                    if self.current_token.value < self.indent_level:
                        break
                self.advance()
            
            # 检查是否有 catch
            if not (self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'catch'):
                break
            
            self.advance()  # 跳过 'catch'
            
            # 解析可选的错误类型
            error_type = None
            if self.current_token and self.current_token.type == 'IDENTIFIER':
                error_type = self.current_token.value
                self.advance()
            
            self.expect('LPAREN')
            catch_var = self.expect('IDENTIFIER').value
            self.expect('RPAREN')
            
            catch_block = self.parse_block()
            
            catch_clauses.append(CatchClause(error_type, catch_var, catch_block))
        
        # 解析可选的 finally 块
        finally_block = None
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'finally':
            self.advance()  # 跳过 'finally'
            finally_block = self.parse_block()
        
        return TryCatchStatement(try_block, catch_clauses, finally_block, line, column)



    def parse_expression(self):
        # 跳过任何DEDENT token（处理空行后的缩进变化）
        # 使用当前缩进级别，避免跳过应该终止块的DEDENT
        self._skip_dedents(self.indent_level)
        return self.parse_or()


    def parse_or(self):
        """解析逻辑或 (||)"""
        left = self.parse_and()

        while self.current_token and self.current_token.type == 'OR':
            line, column = self._get_position()
            self.advance()
            right = self.parse_and()
            left = BinaryOp(left, '||', right, line, column)

        return left

    def parse_and(self):
        """解析逻辑与 (&&)"""
        left = self.parse_equality()

        while self.current_token and self.current_token.type == 'AND':
            line, column = self._get_position()
            self.advance()
            right = self.parse_equality()
            left = BinaryOp(left, '&&', right, line, column)

        return left

    def parse_equality(self):
        left = self.parse_comparison()

        while self.current_token and self.current_token.type in ['EQ', 'NE']:
            line, column = self._get_position()
            op = '==' if self.current_token.type == 'EQ' else '!='
            self.advance()
            right = self.parse_comparison()
            left = BinaryOp(left, op, right, line, column)

        return left

    def parse_comparison(self):
        left = self.parse_additive()

        while self.current_token and self.current_token.type in ['LT', 'LE', 'GT', 'GE']:
            line, column = self._get_position()
            op_map = {
                'LT': '<',
                'LE': '<=',
                'GT': '>',
                'GE': '>='
            }
            op = op_map[self.current_token.type]
            self.advance()
            right = self.parse_additive()
            left = BinaryOp(left, op, right, line, column)

        return left

    def parse_additive(self):
        left = self.parse_multiplicative()

        while self.current_token and self.current_token.type in ['PLUS', 'MINUS']:
            line, column = self._get_position()
            op = '+' if self.current_token.type == 'PLUS' else '-'
            self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(left, op, right, line, column)

        return left

    def parse_multiplicative(self):
        # 跳过任何DEDENT token
        # 使用当前缩进级别，避免跳过应该终止块的DEDENT
        self._skip_dedents(self.indent_level)
        left = self.parse_unary()

        while self.current_token and self.current_token.type in ['MUL', 'DIV', 'MOD']:
            line, column = self._get_position()
            op_map = {
                'MUL': '*',
                'DIV': '/',
                'MOD': '%'
            }
            op = op_map[self.current_token.type]
            self.advance()
            right = self.parse_unary()
            left = BinaryOp(left, op, right, line, column)

        return left


    def parse_unary(self):
        # 跳过任何DEDENT token
        # 使用当前缩进级别，避免跳过应该终止块的DEDENT
        self._skip_dedents(self.indent_level)
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


    # ==================== 主表达式解析辅助方法 ====================
    
    def _parse_literal(self):
        """解析字面量：布尔值、数字、字符串"""
        token_type = self.current_token.type
        line, column = self._get_position()

        if token_type == 'BOOLEAN':
            value = self.current_token.value
            self.advance()
            return BooleanLiteral(value, line, column)

        if token_type == 'NUMBER':
            value = self.current_token.value
            self.advance()
            if isinstance(value, int):
                return IntegerLiteral(value, line, column)
            else:
                return FloatLiteral(value, line, column)

        if token_type == 'STRING':
            value = self.current_token.value
            self.advance()
            return StringLiteral(value, line, column)

        return None
    
    def _parse_function_call_expr(self, name):
        """解析函数调用表达式"""
        self.advance()  # 跳过 '('
        args = []
        if self.current_token and self.current_token.type != 'RPAREN':
            args.append(self.parse_expression())
            while self.current_token and self.current_token.type == 'COMMA':
                self.advance()
                args.append(self.parse_expression())
        self.expect('RPAREN')
        return FunctionCall(name, args)
    
    def _parse_method_chain_expr(self, name):
        """解析方法调用链：obj.method() 或 obj.prop"""
        line, column = self._get_position()
        current_expr = Variable(name, line, column)
        
        while self.current_token and self.current_token.type == 'DOT':
            self.advance()
            member_name = self.expect('IDENTIFIER').value
            
            if self.current_token and self.current_token.type == 'LPAREN':
                # 方法调用
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
                # 属性访问
                current_expr = MethodCall(current_expr, member_name, [])
        
        return current_expr
    
    def _parse_identifier_primary(self):
        """解析标识符开头的主表达式"""
        name = self.current_token.value
        line, column = self._get_position()
        self.advance()

        if self.current_token and self.current_token.type == 'LPAREN':
            return self._parse_function_call_expr(name)

        if self.current_token and self.current_token.type == 'DOT':
            return self._parse_method_chain_expr(name)

        if self.current_token and self.current_token.type == 'INCREMENT':
            self.advance()
            return PostfixIncrement(Variable(name))

        if self.current_token and self.current_token.type == 'LBRACKET':
            # 数组访问
            self.advance()
            index = self.parse_expression()
            self.expect('RBRACKET')
            return ArrayAccess(Variable(name), index)

        return Variable(name, line, column)
    
    def _parse_paren_expression(self):
        """解析括号表达式"""
        self.advance()  # 跳过 '('
        expr = self.parse_expression()
        self.expect('RPAREN')
        return expr
    
    def _parse_array_literal_expr(self):
        """解析数组字面量"""
        self.advance()  # 跳过 '['
        elements = []
        if self.current_token and self.current_token.type != 'RBRACKET':
            elements.append(self.parse_expression())
            while self.current_token and self.current_token.type == 'COMMA':
                self.advance()
                elements.append(self.parse_expression())
        self.expect('RBRACKET')
        return ArrayLiteral(elements)
    
    def _parse_dict_literal_expr(self):
        """解析字典/对象字面量"""
        self.advance()  # 跳过 '{'
        self._skip_indents()  # 跳过可能的 INDENT token
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
                self._skip_indents()  # 跳过可能的 INDENT token
                if self.current_token and self.current_token.type == 'RBRACE':
                    break
                key = self.expect('STRING').value
                self.expect('COLON')
                value = self.parse_expression()
                pairs[key] = value
        self._skip_dedents()  # 跳过可能的 DEDENT token
        self.expect('RBRACE')
        return DictionaryLiteral(pairs)

    def _parse_null_literal(self):
        """解析 null 字面量"""
        line, column = self._get_position()
        self.advance()
        return NullLiteral(line, column)

    # 主表达式分发表：token 类型 -> 处理方法
    _PRIMARY_HANDLERS = {
        'BOOLEAN': '_parse_literal',
        'NUMBER': '_parse_literal',
        'STRING': '_parse_literal',
        'NULL': '_parse_null_literal',
        'IDENTIFIER': '_parse_identifier_primary',
        'LPAREN': '_parse_paren_expression',
        'LBRACKET': '_parse_array_literal_expr',
        'LBRACE': '_parse_dict_literal_expr',
    }


    def parse_primary(self):
        """解析主表达式 - 使用分发表优化"""
        # 跳过任何DEDENT token
        # 使用当前缩进级别，避免跳过应该终止块的DEDENT
        self._skip_dedents(self.indent_level)
        
        if not self.current_token:
            line, column = self._get_position()
            raise HPLSyntaxError(
                "Unexpected end of input",
                line=line,
                column=column
            )
        
        # 使用分发表查找处理方法（O(1) 查找）
        token_type = self.current_token.type
        handler_name = self._PRIMARY_HANDLERS.get(token_type)
        
        if handler_name:
            handler = getattr(self, handler_name)
            return handler()
        
        # 未识别的 token 类型
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
