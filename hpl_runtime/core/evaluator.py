"""
HPL 代码执行器模块

该模块负责执行解析后的 AST（抽象语法树），是解释器的第三阶段。
包含 HPLEvaluator 类，用于评估表达式、执行语句、管理变量作用域，
以及处理函数调用和方法调用。

关键类：
- HPLEvaluator: 代码执行器，执行 AST 并管理运行时状态

主要功能：
- 表达式评估：二元运算、变量查找、字面量、函数/方法调用
- 语句执行：赋值、条件分支、循环、异常处理、返回
- 作用域管理：局部变量、全局对象、this 绑定
- 内置函数：echo 输出等
"""

from __future__ import annotations

import sys
import difflib
from typing import Any, Callable, Optional, Union

from hpl_runtime.core.models import *
from hpl_runtime.modules.loader import load_module, HPLModule
from hpl_runtime.utils.exceptions import *
from hpl_runtime.utils.type_utils import check_numeric_operands, is_hpl_module
from hpl_runtime.utils.io_utils import echo

# 注意：ReturnValue, BreakException, ContinueException 现在从 exceptions 模块导入
# 保留这些别名以保持向后兼容
ReturnValue = HPLReturnValue
BreakException = HPLBreakException
ContinueException = HPLContinueException


class HPLArrowFunction:
    """HPL 箭头函数（闭包）"""
    def __init__(self, params: list[str], body: BlockStatement, closure_scope: dict[str, Any], evaluator: HPLEvaluator) -> None:
        self.params: list[str] = params  # 参数名列表
        self.body: BlockStatement = body      # 函数体（BlockStatement）
        self.closure_scope: dict[str, Any] = closure_scope.copy()  # 捕获定义时的作用域
        self.evaluator: HPLEvaluator = evaluator  # 执行器引用
    
    def call(self, args: list[Any], func_name: Optional[str] = None) -> Any:
        """调用箭头函数"""

        # 创建新的局部作用域，基于闭包作用域
        func_scope = self.closure_scope.copy()
        
        # 绑定参数
        for i, param in enumerate(self.params):
            if i < len(args):
                func_scope[param] = args[i]
            else:
                func_scope[param] = None  # 默认值为 None
        
        # 支持递归：如果提供了函数名，将自身添加到作用域
        if func_name:
            func_scope[func_name] = self
        
        # 执行函数体
        result = self.evaluator.execute_block(self.body, func_scope)
        
        # 解包返回值（如果是ReturnValue包装器）
        if isinstance(result, HPLReturnValue):
            return result.value
        return result
    
    def __repr__(self) -> str:
        return f"<arrow function ({', '.join(self.params)}) => {{...}}>"

class HPLEvaluator:
    # 最大递归深度限制（保守设置，确保在 Python 递归限制前触发）
    # 每个 HPL 函数调用会使用约 7-8 个 Python 栈帧，Python默认限制1000，因此设为500留出安全余量
    MAX_RECURSION_DEPTH: int = 500

    # 最大表达式求值深度限制（防止深层嵌套表达式导致的栈溢出）
    MAX_EXPR_DEPTH: int = 200
    
    def __init__(self, classes: dict[str, HPLClass], objects: dict[str, HPLObject], 
                 functions: Optional[dict[str, HPLFunction]] = None, 
                 main_func: Optional[HPLFunction] = None, 
                 call_target: Optional[str] = None, 
                 call_args: Optional[list[Any]] = None,
                 user_data: Optional[dict[str, Any]] = None) -> None:
        self.classes: dict[str, HPLClass] = classes
        self.objects: dict[str, HPLObject] = objects
        self.functions: dict[str, HPLFunction] = functions or {}  # 所有顶层函数
        self.main_func: Optional[HPLFunction] = main_func
        self.call_target: Optional[str] = call_target
        self.call_args: list[Any] = call_args or []  # call 调用的参数
        self.user_data: dict[str, Any] = user_data or {}  # 用户声明式数据对象

        self.global_scope: dict[str, Any] = {}  # 全局变量
        self.global_scope.update(self.objects)  # 添加预定义对象
        self.global_scope.update(self.user_data)  # 添加用户数据对象（config, scenes等）
        self.current_obj: Optional[HPLObject] = None  # 用于方法中的'this'
        self.current_class: Optional[HPLClass] = None  # 用于跟踪当前执行的类（支持多级继承）
        self.call_stack: list[str] = []  # 调用栈，用于错误跟踪
        self.imported_modules: dict[str, Any] = {}  # 导入的模块 {alias/name: module}
        self.expr_eval_depth: int = 0  # 表达式求值深度计数器
        
        # 初始化语句处理器映射表
        self._init_statement_handlers()
        # 初始化表达式处理器映射表
        self._init_expression_handlers()


    def run(self) -> None:
        # 如果指定了 call_target，执行对应的函数
        if self.call_target:

            # 首先尝试从 functions 字典中查找
            if self.call_target in self.functions:
                target_func = self.functions[self.call_target]
                # 构建参数作用域
                local_scope = {}
                for i, param in enumerate(target_func.params):
                    if i < len(self.call_args):
                        local_scope[param] = self.call_args[i]
                    else:
                        local_scope[param] = None  # 默认值为 None
                self.execute_function(target_func, local_scope, self.call_target)
            elif self.call_target == 'main' and self.main_func:
                self.execute_function(self.main_func, {}, 'main')
            else:
                raise self._create_error(
                    HPLNameError,
                    f"Unknown call target: '{self.call_target}'",
                    error_key='RUNTIME_UNDEFINED_VAR'
                )

        elif self.main_func:
            self.execute_function(self.main_func, {}, 'main')

    def execute_function(self, func: HPLFunction, local_scope: dict[str, Any], func_name: Optional[str] = None) -> Any:
        # 检查递归深度限制
        if len(self.call_stack) >= self.MAX_RECURSION_DEPTH:

            raise self._create_error(
                HPLRecursionError,
                f"Maximum recursion depth exceeded ({self.MAX_RECURSION_DEPTH}). "
                f"Hint: Check for infinite recursion in function calls.",
                error_key='RUNTIME_RECURSION_DEPTH'
            )
        
        # 执行语句块并返回结果
        # 添加到调用栈（如果提供了函数名）
        if func_name:
            self.call_stack.append(f"{func_name}()")
        
        try:
            result = self.execute_block(func.body, local_scope)
            # 如果是ReturnValue包装器，解包；否则返回原始值（或无返回值）
            if isinstance(result, ReturnValue):
                return result.value
            return result
        except RecursionError:
            # 捕获 Python 的 RecursionError 并转换为 HPLRecursionError
            raise self._create_error(
                HPLRecursionError,
                f"Maximum recursion depth exceeded ({self.MAX_RECURSION_DEPTH}). "
                f"Hint: Check for infinite recursion in function calls.",
                error_key='RUNTIME_RECURSION_DEPTH'
            )
        finally:
            # 从调用栈移除
            if func_name:
                self.call_stack.pop()

    def execute_block(self, block: BlockStatement, local_scope: dict[str, Any]) -> Any:
        for stmt in block.statements:

            result = self.execute_statement(stmt, local_scope)
            # 如果语句返回了ReturnValue，立即向上传播（终止执行）
            if isinstance(result, ReturnValue):
                return result
            # 处理 break 和 continue
            if isinstance(result, BreakException):
                raise result
            if isinstance(result, ContinueException):
                raise result
        return None

    def _init_statement_handlers(self):
        """初始化语句处理器映射表"""
        self._statement_handlers = {
            AssignmentStatement: self._execute_assignment,
            ArrayAssignmentStatement: self._execute_array_assignment,
            ReturnStatement: self._execute_return,
            IfStatement: self._execute_if,
            ForInStatement: self._execute_for_in,
            WhileStatement: self._execute_while,
            BreakStatement: self._execute_break,
            ContinueStatement: self._execute_continue,
            ThrowStatement: self._execute_throw,
            TryCatchStatement: self._execute_try_catch,
            EchoStatement: self._execute_echo,
            ImportStatement: self._execute_import,
            IncrementStatement: self._execute_increment,
            BlockStatement: self._execute_block_statement,
            Expression: self._execute_expression_statement,
            MethodCall: self._execute_method_call_statement,
            FunctionCall: self._execute_function_call_statement,
            ArrayLiteral: self._execute_array_literal_statement,
        }
    
    def execute_statement(self, stmt: Statement, local_scope: dict[str, Any]) -> Any:
        """语句执行主分发器"""
        handler = self._statement_handlers.get(type(stmt))
        if handler:
            return handler(stmt, local_scope)

        raise self._create_error(
            HPLRuntimeError,
            f"Unknown statement type: {type(stmt).__name__}",
            line=stmt.line if hasattr(stmt, 'line') else None,
            column=stmt.column if hasattr(stmt, 'column') else None,
            local_scope=local_scope,
            error_key='RUNTIME_GENERAL'
        )
    
    def _execute_assignment(self, stmt, local_scope):
        """执行赋值语句"""
        value = self.evaluate_expression(stmt.expr, local_scope)
        # 检查是否是属性赋值（如 this.name = value 或 config.title = value）
        if '.' in stmt.var_name:
            obj_name, prop_name = stmt.var_name.split('.', 1)
            # 获取对象
            if obj_name == 'this':
                obj = local_scope.get('this') or self.current_obj
            else:
                obj = self._lookup_variable(obj_name, local_scope, stmt.line, stmt.column)

            if isinstance(obj, HPLObject):
                obj.attributes[prop_name] = value
            elif isinstance(obj, dict):
                # 支持字典属性赋值：config.title = value 等价于 config["title"] = value
                obj[prop_name] = value
            else:
                raise self._create_error(
                    HPLTypeError,
                    f"Cannot set property on non-object value: {type(obj).__name__}",
                    line=stmt.line,
                    column=stmt.column,
                    local_scope=local_scope,
                    error_key='TYPE_MISSING_PROPERTY'
                )

        else:
            local_scope[stmt.var_name] = value

    
    def _execute_array_assignment(self, stmt, local_scope):
        """执行数组元素赋值语句"""
        # 检查是否是复合属性访问（如 this.exits[direction]）
        if '.' in stmt.array_name:
            # 复合属性数组赋值：obj.prop[index] = value
            obj_name, prop_name = stmt.array_name.split('.', 1)
            
            # 获取对象
            if obj_name == 'this':
                obj = local_scope.get('this') or self.current_obj
            else:
                obj = self._lookup_variable(obj_name, local_scope)
            
            if not isinstance(obj, HPLObject):
                raise self._create_error(
                    HPLTypeError,
                    f"Cannot access property on non-object value: {type(obj).__name__}",
                    line=stmt.line if hasattr(stmt, 'line') else None,
                    column=stmt.column if hasattr(stmt, 'column') else None,
                    local_scope=local_scope,
                    error_key='TYPE_INVALID_OPERATION'
                )

            # 获取属性（应该是数组/字典）
            if prop_name not in obj.attributes:
                # 如果属性不存在，创建一个空字典
                obj.attributes[prop_name] = {}
            
            array = obj.attributes[prop_name]
            
            # 计算索引
            index = self.evaluate_expression(stmt.index_expr, local_scope)
            value = self.evaluate_expression(stmt.value_expr, local_scope)
            
            # 支持字典和数组
            if isinstance(array, dict):
                array[index] = value
            elif isinstance(array, list):
                if not isinstance(index, int):
                    raise self._create_error(
                        HPLTypeError,
                        f"Array index must be integer, got {type(index).__name__}",
                        error_key='TYPE_INVALID_OPERATION'
                    )
                if index < 0 or index >= len(array):
                    raise self._create_error(
                        HPLIndexError,
                        f"Array index {index} out of bounds (length: {len(array)})",
                        error_key='RUNTIME_INDEX_OUT_OF_BOUNDS'
                    )
                array[index] = value
            else:
                raise self._create_error(
                    HPLTypeError,
                    f"Cannot index non-array and non-dict value: {type(array).__name__}",
                    line=stmt.line if hasattr(stmt, 'line') else None,
                    column=stmt.column if hasattr(stmt, 'column') else None,
                    local_scope=local_scope,
                    error_key='TYPE_INVALID_OPERATION'
                )

        else:
            # 简单数组赋值
            array = self._lookup_variable(stmt.array_name, local_scope)
            if not isinstance(array, list):
                raise self._create_error(
                    HPLTypeError,
                    f"Cannot assign to non-array value: {type(array).__name__}",
                    line=stmt.line if hasattr(stmt, 'line') else None,
                    column=stmt.column if hasattr(stmt, 'column') else None,
                    local_scope=local_scope,
                    error_key='TYPE_INVALID_OPERATION'
                )
         
            index = self.evaluate_expression(stmt.index_expr, local_scope)
            if not isinstance(index, int):
                raise self._create_error(
                    HPLTypeError,
                    f"Array index must be integer, got {type(index).__name__}",
                    error_key='TYPE_INVALID_OPERATION'
                )
        
            if index < 0 or index >= len(array):
                raise self._create_error(
                    HPLIndexError,
                    f"Array index {index} out of bounds (length: {len(array)})",
                    error_key='RUNTIME_INDEX_OUT_OF_BOUNDS'
                )
     
            value = self.evaluate_expression(stmt.value_expr, local_scope)
            array[index] = value
    
    def _execute_return(self, stmt, local_scope):
        """执行返回语句"""
        value = None
        if stmt.expr:
            value = self.evaluate_expression(stmt.expr, local_scope)
        return HPLReturnValue(value)
    
    def _execute_if(self, stmt, local_scope):
        """执行条件语句"""
        cond = self.evaluate_expression(stmt.condition, local_scope)
        if cond:
            result = self.execute_block(stmt.then_block, local_scope)
            if isinstance(result, HPLReturnValue):
                return result
        elif stmt.else_block:
            result = self.execute_block(stmt.else_block, local_scope)
            if isinstance(result, HPLReturnValue):
                return result
    
    def _execute_for_in(self, stmt, local_scope):
        """执行for-in循环语句"""
        iterable = self.evaluate_expression(stmt.iterable_expr, local_scope)
        
        # 根据类型进行迭代
        if isinstance(iterable, list):
            iterator = iterable
        elif isinstance(iterable, dict):
            iterator = iterable.keys()
        elif isinstance(iterable, str):
            iterator = iterable
        else:
            raise self._create_error(
                HPLTypeError,
                f"'{type(iterable).__name__}' object is not iterable",
                line=stmt.line if hasattr(stmt, 'line') else None,
                column=stmt.column if hasattr(stmt, 'column') else None,
                local_scope=local_scope,
                error_key='TYPE_INVALID_OPERATION'
            )
        
        for item in iterator:
            local_scope[stmt.var_name] = item
            try:
                result = self.execute_block(stmt.body, local_scope)
                if isinstance(result, HPLReturnValue):
                    return result
            except HPLBreakException:
                break
            except HPLContinueException:
                continue
    
    def _execute_while(self, stmt, local_scope):
        """执行while循环语句"""
        while self.evaluate_expression(stmt.condition, local_scope):
            try:
                result = self.execute_block(stmt.body, local_scope)
                if isinstance(result, HPLReturnValue):
                    return result
            except HPLBreakException:
                break
            except HPLContinueException:
                pass
    
    def _execute_break(self, stmt, local_scope):
        """执行break语句"""
        raise HPLBreakException()
    
    def _execute_continue(self, stmt, local_scope):
        """执行continue语句"""
        raise HPLContinueException()
    
    def _execute_throw(self, stmt, local_scope):
        """执行throw语句"""
        value = None
        if stmt.expr:
            value = self.evaluate_expression(stmt.expr, local_scope)
        raise self._create_error(
            HPLRuntimeError,
            str(value) if value is not None else "Exception thrown",
            line=stmt.line if hasattr(stmt, 'line') else None,
            column=stmt.column if hasattr(stmt, 'column') else None,
            local_scope=local_scope,
            error_key='RUNTIME_GENERAL'
        )
    
    def _execute_try_catch(self, stmt, local_scope):
        """执行try-catch-finally语句"""
        caught = False
        error_obj = None
        result = None
        
        try:
            result = self.execute_block(stmt.try_block, local_scope)
            if isinstance(result, HPLReturnValue):
                return result
        except HPLRuntimeError as e:
            error_obj = e
            
            # 尝试匹配特定的 catch 子句
            for catch in stmt.catch_clauses:
                if self._matches_error_type(e, catch.error_type):
                    local_scope[catch.var_name] = error_obj
                    result = self.execute_block(catch.block, local_scope)
                    caught = True
                    if isinstance(result, HPLReturnValue):
                        return result
                    break
            
            if not caught:
                if e.line is None and hasattr(stmt.try_block, 'line'):
                    e.line = stmt.try_block.line
                raise
        except HPLControlFlowException:
            raise
        finally:
            if stmt.finally_block:
                finally_result = self.execute_block(stmt.finally_block, local_scope)
                if isinstance(finally_result, HPLReturnValue):
                    return finally_result
    
    def _execute_echo(self, stmt, local_scope):
        """执行echo语句"""
        message = self.evaluate_expression(stmt.expr, local_scope)
        echo(message)
    
    def _execute_import(self, stmt, local_scope):
        """执行import语句"""
        module_name = stmt.module_name
        alias = stmt.alias or module_name
        
        try:
            # 加载模块
            module = load_module(module_name)
            if module:
                # 存储模块引用
                self.imported_modules[alias] = module
                local_scope[alias] = module
                return None
        except ImportError as e:
            raise self._create_error(
                HPLImportError,
                f"Cannot import module '{module_name}': {e}",
                error_key='IMPORT_MODULE_NOT_FOUND'
            ) from e
        
        raise self._create_error(
            HPLImportError,
            f"Module '{module_name}' not found",
            error_key='IMPORT_MODULE_NOT_FOUND'
        )
    
    def _execute_increment(self, stmt, local_scope):
        """执行自增语句"""
        value = self._lookup_variable(stmt.var_name, local_scope)
        if not isinstance(value, (int, float)):
            raise self._create_error(
                HPLTypeError,
                f"Cannot increment non-numeric value: {type(value).__name__}",
                stmt.line, stmt.column,
                local_scope,
                error_key='TYPE_INVALID_OPERATION'
            )
        new_value = value + 1
        self._update_variable(stmt.var_name, new_value, local_scope)
    
    def _execute_block_statement(self, stmt, local_scope):
        """执行块语句"""
        return self.execute_block(stmt, local_scope)
    
    def _execute_expression_statement(self, stmt, local_scope):
        """执行表达式作为语句"""
        return self.evaluate_expression(stmt, local_scope)
    
    def _execute_method_call_statement(self, stmt, local_scope):
        """执行方法调用语句（作为独立语句使用）"""
        return self._eval_method_call(stmt, local_scope)
    
    def _execute_function_call_statement(self, stmt, local_scope):
        """执行函数调用语句（作为独立语句使用）"""
        return self._eval_function_call(stmt, local_scope)
    
    def _execute_array_literal_statement(self, stmt, local_scope):
        """执行数组字面量语句（作为独立语句使用）"""
        # 评估数组字面量但不返回结果（作为语句使用）
        self._eval_array_literal(stmt, local_scope)
        return None

    def _init_expression_handlers(self):
        """初始化表达式处理器映射表"""
        self._expression_handlers = {
            IntegerLiteral: self._eval_integer_literal,
            FloatLiteral: self._eval_float_literal,
            StringLiteral: self._eval_string_literal,
            BooleanLiteral: self._eval_boolean_literal,
            NullLiteral: self._eval_null_literal,
            Variable: self._eval_variable,
            BinaryOp: self._eval_binary_op_expr,
            UnaryOp: self._eval_unary_op,
            FunctionCall: self._eval_function_call,
            MethodCall: self._eval_method_call,
            PostfixIncrement: self._eval_postfix_increment,
            PrefixIncrement: self._eval_prefix_increment,
            ArrayLiteral: self._eval_array_literal,
            ArrayAccess: self._eval_array_access,
            DictionaryLiteral: self._eval_dictionary_literal,
            ArrowFunction: self._eval_arrow_function,
        }
    
    def evaluate_expression(self, expr: Expression, local_scope: dict[str, Any]) -> Any:
        """表达式评估主分发器"""
        # 检查表达式求值深度，防止深层嵌套导致的栈溢出
        self.expr_eval_depth += 1
        if self.expr_eval_depth > self.MAX_EXPR_DEPTH:
            self.expr_eval_depth -= 1
            raise self._create_error(
                HPLRecursionError,
                f"Maximum expression evaluation depth exceeded ({self.MAX_EXPR_DEPTH}). "
                f"Hint: Check for deeply nested expressions or cyclic references.",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='RUNTIME_RECURSION_DEPTH'
            )
        
        try:
            handler = self._expression_handlers.get(type(expr))
            if handler:
                return handler(expr, local_scope)

            raise self._create_error(
                HPLRuntimeError,
                f"Unknown expression type: {type(expr).__name__}",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='RUNTIME_GENERAL'
            )
        finally:
            self.expr_eval_depth -= 1
    
    # 字面量处理器
    def _eval_integer_literal(self, expr: IntegerLiteral, local_scope: dict[str, Any]) -> int:
        return expr.value
    
    def _eval_float_literal(self, expr: FloatLiteral, local_scope: dict[str, Any]) -> float:
        return expr.value
    
    def _eval_string_literal(self, expr: StringLiteral, local_scope: dict[str, Any]) -> str:
        return expr.value
    
    def _eval_boolean_literal(self, expr: BooleanLiteral, local_scope: dict[str, Any]) -> bool:
        return expr.value
    
    def _eval_null_literal(self, expr: NullLiteral, local_scope: dict[str, Any]) -> None:
        return None
    
    def _eval_variable(self, expr: Variable, local_scope: dict[str, Any]) -> Any:
        return self._lookup_variable(expr.name, local_scope, expr.line, expr.column)
    
    def _eval_binary_op_expr(self, expr: BinaryOp, local_scope: dict[str, Any]) -> Any:
        # 先评估左操作数
        left = self.evaluate_expression(expr.left, local_scope)
        
        # 处理逻辑运算符短路求值
        if expr.op == '&&':
            # 如果左操作数为假，直接返回左操作数（短路）
            if not left:
                return left
            # 否则评估右操作数并返回
            right = self.evaluate_expression(expr.right, local_scope)
            return right
        elif expr.op == '||':
            # 如果左操作数为真，直接返回左操作数（短路）
            if left:
                return left
            # 否则评估右操作数并返回
            right = self.evaluate_expression(expr.right, local_scope)
            return right
        
        # 非逻辑运算符，正常评估两个操作数
        right = self.evaluate_expression(expr.right, local_scope)
        return self._eval_binary_op(left, expr.op, right, expr.line, expr.column)
    
    def _eval_unary_op(self, expr: UnaryOp, local_scope: dict[str, Any]) -> Any:

        operand = self.evaluate_expression(expr.operand, local_scope)
        if expr.op == '!':
            if not isinstance(operand, bool):
                raise self._create_error(
                    HPLTypeError,
                    f"Logical NOT requires boolean operand, got {type(operand).__name__}",
                    expr.line, expr.column,
                    local_scope,
                    error_key='TYPE_INVALID_OPERATION'
                )
            return not operand
        else:
            raise self._create_error(
                HPLRuntimeError,
                f"Unknown unary operator {expr.op}",
                line=expr.line,
                column=expr.column,
                local_scope=local_scope,
                error_key='RUNTIME_GENERAL'
            )
    
    def _eval_function_call(self, expr, local_scope):
        """评估函数调用表达式"""
        # 首先评估函数表达式（可能是变量、箭头函数等）
        func = None
        func_name = None
        
        if isinstance(expr.func_name, str):
            # 字符串函数名
            func_name = expr.func_name
            
            # 检查是否是类实例化
            if func_name in self.classes:
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                obj_name = f"__{func_name}_instance_{id(expr)}__"
                return self.instantiate_object(func_name, obj_name, args)
            
            # 检查是否是用户定义的函数
            if func_name in self.functions:
                func = self.functions[func_name]
            else:
                # 尝试从作用域查找（可能是箭头函数变量）
                try:
                    func = self._lookup_variable(func_name, local_scope)
                except HPLNameError:
                    func = None
        elif isinstance(expr.func_name, Variable):
            # 变量引用，查找变量值
            func_name = expr.func_name.name
            try:
                func = self._lookup_variable(func_name, local_scope)
            except HPLNameError:
                func = None
        else:
            # 其他表达式（如直接是箭头函数字面量）
            func = self.evaluate_expression(expr.func_name, local_scope)
        
        # 内置函数处理
        builtin_handlers = {
            'echo': self._builtin_echo,
            'len': self._builtin_len,
            'int': self._builtin_int,
            'float': self._builtin_float,
            'str': self._builtin_str,
            'type': self._builtin_type,
            'abs': self._builtin_abs,
            'max': self._builtin_max,
            'min': self._builtin_min,
            'range': self._builtin_range,
            'input': self._builtin_input,
        }
        
        if func_name and func_name in builtin_handlers:
            return builtin_handlers[func_name](expr, local_scope)
        
        # 处理用户定义的函数
        if func:
            args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
            
            # 如果是箭头函数
            if isinstance(func, HPLArrowFunction):
                return func.call(args, func_name)

            
            # 普通函数
            func_scope = {}
            for i, param in enumerate(func.params):
                if i < len(args):
                    func_scope[param] = args[i]
                else:
                    func_scope[param] = None
            return self.execute_function(func, func_scope, func_name)
        
        raise self._create_error(
            HPLNameError,
            f"Unknown function '{func_name or expr.func_name}'",
            line=expr.line if hasattr(expr, 'line') else None,
            column=expr.column if hasattr(expr, 'column') else None,
            local_scope=local_scope,
            error_key='RUNTIME_UNDEFINED_VAR'
        )
    
    # 内置函数处理器
    def _builtin_echo(self, expr: FunctionCall, local_scope: dict[str, Any]) -> None:
        message = self.evaluate_expression(expr.args[0], local_scope)
        echo(message)
        return None
    
    def _builtin_len(self, expr: FunctionCall, local_scope: dict[str, Any]) -> int:
        arg = self.evaluate_expression(expr.args[0], local_scope)
        if isinstance(arg, (list, str)):
            return len(arg)
        raise self._create_error(
            HPLTypeError,
            f"len() requires list or string, got {type(arg).__name__}",
            line=expr.line if hasattr(expr, 'line') else None,
            column=expr.column if hasattr(expr, 'column') else None,
            local_scope=local_scope,
            error_key='TYPE_INVALID_OPERATION'
        )
    
    def _builtin_int(self, expr: FunctionCall, local_scope: dict[str, Any]) -> int:
        arg = self.evaluate_expression(expr.args[0], local_scope)
        try:
            return int(arg)
        except (ValueError, TypeError):
            arg_type = type(arg).__name__
            suggestions = {
                'str': " (Ensure string contains only digits, e.g., int(\"42\"))",
                'list': " (Cannot convert array to integer)",
                'dict': " (Cannot convert dictionary to integer)",
                'NoneType': " (Variable not initialized, value is null)",
            }

            suggestion = suggestions.get(arg_type, "")
            raise self._create_error(
                HPLTypeError,
                f"Cannot convert {arg_type} (value: {arg!r}) to int{suggestion}",
                expr.line, expr.column,
                local_scope,
                error_key='TYPE_CONVERSION_FAILED'
            )
    
    def _builtin_float(self, expr: FunctionCall, local_scope: dict[str, Any]) -> float:
        arg = self.evaluate_expression(expr.args[0], local_scope)
        try:
            return float(arg)
        except (ValueError, TypeError):
            arg_type = type(arg).__name__
            suggestions = {
                'str': " (Ensure string is valid numeric format, e.g., float(\"3.14\"))",
                'NoneType': " (Variable not initialized, value is null)",
            }

            suggestion = suggestions.get(arg_type, "")
            raise self._create_error(
                HPLTypeError,
                f"Cannot convert {arg_type} (value: {arg!r}) to float{suggestion}",
                expr.line, expr.column,
                local_scope,
                error_key='TYPE_CONVERSION_FAILED'
            )
    
    def _builtin_str(self, expr: FunctionCall, local_scope: dict[str, Any]) -> str:
        arg = self.evaluate_expression(expr.args[0], local_scope)
        return str(arg)
    
    def _builtin_type(self, expr: FunctionCall, local_scope: dict[str, Any]) -> str:
        arg = self.evaluate_expression(expr.args[0], local_scope)
        type_map = {
            bool: 'boolean',
            int: 'int',
            float: 'float',
            str: 'string',
            list: 'array',
        }
        if type(arg) in type_map:
            return type_map[type(arg)]
        elif isinstance(arg, HPLObject):
            return arg.hpl_class.name
        return type(arg).__name__
    
    def _builtin_abs(self, expr: FunctionCall, local_scope: dict[str, Any]) -> Union[int, float]:
        arg = self.evaluate_expression(expr.args[0], local_scope)
        if not isinstance(arg, (int, float)):
            raise self._create_error(
                HPLTypeError,
                f"abs() requires number, got {type(arg).__name__}",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='TYPE_INVALID_OPERATION'
            )

        return abs(arg)
    
    def _builtin_max(self, expr: FunctionCall, local_scope: dict[str, Any]) -> Any:
        if len(expr.args) < 1:
            raise self._create_error(
                HPLValueError,
                "max() requires at least one argument",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='RUNTIME_GENERAL'
            )

        args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
        return max(args)
    
    def _builtin_min(self, expr: FunctionCall, local_scope: dict[str, Any]) -> Any:
        if len(expr.args) < 1:
            raise self._create_error(
                HPLValueError,
                "min() requires at least one argument",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='RUNTIME_GENERAL'
            )

        args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
        return min(args)
    
    def _builtin_range(self, expr: FunctionCall, local_scope: dict[str, Any]) -> list[int]:
        if len(expr.args) < 1 or len(expr.args) > 3:
            raise self._create_error(
                HPLValueError,
                "range() requires 1 to 3 arguments",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='RUNTIME_GENERAL'
            )

        args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
        for arg in args:
            if not isinstance(arg, int):
                raise self._create_error(
                    HPLTypeError,
                    f"range() arguments must be integers, got {type(arg).__name__}",
                    error_key='TYPE_INVALID_OPERATION'
                )
        if len(args) == 1:
            return list(range(args[0]))
        elif len(args) == 2:
            return list(range(args[0], args[1]))
        else:
            return list(range(args[0], args[1], args[2]))
    
    def _builtin_input(self, expr: FunctionCall, local_scope: dict[str, Any]) -> str:

        if len(expr.args) == 0:
            try:
                return input()
            except EOFError:
                raise self._create_error(
                    HPLIOError,
                    "End of file reached while waiting for input",
                    line=expr.line if hasattr(expr, 'line') else None,
                    column=expr.column if hasattr(expr, 'column') else None,
                    local_scope=local_scope,
                    error_key='IO_READ_ERROR'
                )
        elif len(expr.args) == 1:
            prompt = self.evaluate_expression(expr.args[0], local_scope)
            if not isinstance(prompt, str):
                raise self._create_error(
                    HPLTypeError,
                    f"input() requires string prompt, got {type(prompt).__name__}",
                    line=expr.line if hasattr(expr, 'line') else None,
                    column=expr.column if hasattr(expr, 'column') else None,
                    local_scope=local_scope,
                    error_key='TYPE_INVALID_OPERATION'
                )
            try:
                return input(prompt)
            except EOFError:
                raise self._create_error(
                    HPLIOError,
                    "End of file reached while waiting for input",
                    line=expr.line if hasattr(expr, 'line') else None,
                    column=expr.column if hasattr(expr, 'column') else None,
                    local_scope=local_scope,
                    error_key='IO_READ_ERROR'
                )
        else:
            raise self._create_error(
                HPLValueError,
                f"input() requires 0 or 1 arguments, got {len(expr.args)}",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='RUNTIME_GENERAL'
            )
    
    def _eval_method_call(self, expr, local_scope):
        """评估方法调用表达式"""
        obj = self.evaluate_expression(expr.obj_name, local_scope)
        if isinstance(obj, HPLObject):
            # 处理 parent 特殊属性访问
            if expr.method_name == 'parent':
                # 使用 current_class（当前执行的类）来确定 parent，而不是对象的实际类
                # 这支持多级继承：在 Parent 的方法中调用 this.parent.init() 应该调用 GrandParent 的 init
                reference_class = self.current_class if self.current_class else obj.hpl_class
                if reference_class.parent and reference_class.parent in self.classes:
                    parent_class = self.classes[reference_class.parent]
                    return parent_class
                raise self._create_error(
                    HPLAttributeError,
                    f"Class '{reference_class.name}' has no parent class",
                    line=expr.line if hasattr(expr, 'line') else None,
                    column=expr.column if hasattr(expr, 'column') else None,
                    local_scope=local_scope,
                    error_key='TYPE_MISSING_PROPERTY'
                )

            args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
            return self._call_method(obj, expr.method_name, args)
        elif isinstance(obj, HPLClass):
            args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
            return self._call_method(obj, expr.method_name, args)
        elif isinstance(obj, dict):
            # 支持字典属性访问：config.title 等价于 config["title"]
            if expr.method_name in obj:
                # 如果是属性访问（无参数），返回字典值
                if len(expr.args) == 0:
                    return obj[expr.method_name]
                # 如果带参数，尝试作为方法调用（如字典的get方法）
                else:
                    args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                    # 检查是否是字典的内置方法
                    if hasattr(obj, expr.method_name) and callable(getattr(obj, expr.method_name)):
                        method = getattr(obj, expr.method_name)
                        return method(*args)
                    raise self._create_error(
                        HPLAttributeError,
                        f"Cannot call method '{expr.method_name}' on dictionary",
                        line=expr.line if hasattr(expr, 'line') else None,
                        column=expr.column if hasattr(expr, 'column') else None,
                        local_scope=local_scope,
                        error_key='TYPE_MISSING_PROPERTY'
                    )
            else:
                available_keys = list(obj.keys())[:5]
                hint = f"Available keys: {available_keys}" if available_keys else "Dictionary is empty"
                raise self._create_error(
                    HPLKeyError,
                    f"Key '{expr.method_name}' not found in dictionary. {hint}",
                    line=expr.line if hasattr(expr, 'line') else None,
                    column=expr.column if hasattr(expr, 'column') else None,
                    local_scope=local_scope,
                    error_key='RUNTIME_KEY_NOT_FOUND'
                )
        elif isinstance(obj, list):
            # 支持列表属性访问（如 length）或方法调用
            if expr.method_name == 'length' or expr.method_name == 'size':
                if len(expr.args) == 0:
                    return len(obj)
            # 检查是否是列表的内置方法
            if hasattr(obj, expr.method_name) and callable(getattr(obj, expr.method_name)):
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                method = getattr(obj, expr.method_name)
                return method(*args)
            raise self._create_error(
                HPLTypeError,
                f"Cannot access property '{expr.method_name}' on list. Lists only support 'length' property and standard array methods.",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='TYPE_INVALID_OPERATION'
            )

        elif is_hpl_module(obj):
            if len(expr.args) == 0:
                try:
                    return self.get_module_constant(obj, expr.method_name)
                except HPLAttributeError:
                    return self.call_module_function(obj, expr.method_name, [])
            else:
                args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
                return self.call_module_function(obj, expr.method_name, args)
        raise self._create_error(
            HPLTypeError,
            f"Cannot call method on {type(obj).__name__}",
            line=expr.line if hasattr(expr, 'line') else None,
            column=expr.column if hasattr(expr, 'column') else None,
            local_scope=local_scope,
            error_key='TYPE_INVALID_OPERATION'
        )

    
    def _eval_postfix_increment(self, expr, local_scope):
        var_name = expr.var.name
        value = self._lookup_variable(var_name, local_scope)
        if not isinstance(value, (int, float)):
            raise self._create_error(
                HPLTypeError,
                f"Cannot increment non-numeric value: {type(value).__name__}",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='TYPE_INVALID_OPERATION'
            )

        new_value = value + 1
        self._update_variable(var_name, new_value, local_scope)
        return value
    
    def _eval_prefix_increment(self, expr, local_scope):
        """评估前缀自增表达式 (++x) - 返回新值"""
        var_name = expr.var.name
        value = self._lookup_variable(var_name, local_scope)
        if not isinstance(value, (int, float)):
            raise self._create_error(
                HPLTypeError,
                f"Cannot increment non-numeric value: {type(value).__name__}",
                line=expr.line if hasattr(expr, 'line') else None,
                column=expr.column if hasattr(expr, 'column') else None,
                local_scope=local_scope,
                error_key='TYPE_INVALID_OPERATION'
            )

        new_value = value + 1
        self._update_variable(var_name, new_value, local_scope)
        return new_value  # 前缀自增返回新值
    
    def _eval_array_literal(self, expr, local_scope):
        return [self.evaluate_expression(elem, local_scope) for elem in expr.elements]
    
    def _eval_dictionary_literal(self, expr, local_scope):
        """评估字典字面量"""
        result = {}
        for key, value_expr in expr.pairs.items():
            result[key] = self.evaluate_expression(value_expr, local_scope)
        return result
    
    def _eval_arrow_function(self, expr, local_scope):
        """评估箭头函数表达式，返回可调用对象"""
        return HPLArrowFunction(expr.params, expr.body, local_scope, self)

    def _eval_array_access(self, expr, local_scope):
        """评估数组/字典/字符串索引访问"""
        array = self.evaluate_expression(expr.array, local_scope)
        index = self.evaluate_expression(expr.index, local_scope)
        
        if isinstance(array, dict):
            return self._access_dict(array, index, expr, local_scope)
        elif isinstance(array, str):
            return self._access_string(array, index, expr, local_scope)
        elif isinstance(array, list):
            return self._access_list(array, index, expr, local_scope)
        
        # 类型错误
        actual_type = type(array).__name__
        hints = {
            'dict': " (Dictionary uses key access, e.g., dict[key])",
            'int': " (Number is not indexable)",
            'float': " (Float is not indexable)",
            'NoneType': " (Variable may not be initialized, is null)",
            'HPLObject': " (Object uses property access, e.g., obj.property)",
        }
        hint = hints.get(actual_type, f" (Type {actual_type} does not support indexing)")

        raise self._create_error(
            HPLTypeError,
            f"Cannot index {actual_type} value{hint}",
            expr.line, expr.column,
            local_scope,
            error_key='TYPE_INVALID_OPERATION'
        )
    
    def _access_dict(self, array, index, expr, local_scope):
        """访问字典"""
        if index in array:
            return array[index]
        
        # 构建详细的错误信息
        available_keys = list(array.keys())[:10]
        key_type = type(index).__name__
        
        similar_keys = []
        if available_keys:
            key_strs = [str(k) for k in available_keys]
            similar = difflib.get_close_matches(str(index), key_strs, n=3, cutoff=0.6)
            similar_keys = similar
        
        parts = [f"Key {index!r} (type: {key_type}) not found in dictionary"]
        if available_keys:
            parts.append(f"Available keys: {available_keys}")
        else:
            parts.append("Dictionary is empty")
        
        if similar_keys:
            if len(similar_keys) == 1:
                parts.append(f"Did you mean: '{similar_keys[0]}'?")
            else:
                parts.append(f"Similar keys: {', '.join(similar_keys)}")
        
        # 类型转换建议
        if isinstance(index, int) and str(index) in [str(k) for k in array.keys() if isinstance(k, str)]:
            parts.append(f"Try using string key: '{index}'")
        elif isinstance(index, str) and index.isdigit():
            int_key = int(index)
            if int_key in array:
                parts.append(f"Key exists as integer: {int_key}")
        
        hint = ". ".join(parts)
        raise self._create_error(
            HPLKeyError,
            hint,
            expr.line, expr.column,
            local_scope,
            error_key='RUNTIME_KEY_NOT_FOUND'
        )
    
    def _access_string(self, array, index, expr, local_scope):
        """访问字符串"""
        if not isinstance(index, int):
            index_type = type(index).__name__
            suggestions = []
            if isinstance(index, str) and index.isdigit():
                suggestions.append(f"Use int() to convert: int('{index}')")
            elif isinstance(index, float) and index.is_integer():
                suggestions.append(f"Use int() to convert: int({index})")
            elif index is None:
                suggestions.append("Index cannot be null")
            else:
                suggestions.append(f"String index must be integer, got {index_type}")

            hint = f" ({'; '.join(suggestions)})" if suggestions else ""
            raise self._create_error(
                HPLTypeError,
                f"String index must be integer, got {index_type} (value: {index!r}){hint}",
                expr.line, expr.column,
                local_scope,
                error_key='TYPE_INVALID_OPERATION'
            )
        
        length = len(array)
        if 0 <= index < length:
            return array[index]
        
        # 边界错误
        suggestions = []
        if index < 0 and length > 0:
            reverse_idx = length + index
            if 0 <= reverse_idx < length:
                suggestions.append(f"Use positive index {reverse_idx} to access character at position {abs(index)}")
        if index >= length:
            suggestions.append(f"String length is {length}, max index is {length - 1}")
        if length > 0:
            suggestions.append(f"Valid index range: 0 to {length - 1}")
        else:
            suggestions.append("String is empty")

        
        if length > 0 and index >= 0:
            if index < length:
                char = array[index]
                suggestions.append(f"Character at this position is: '{char}'")
            elif index < length + 5:
                suggestions.append(f"Out of range, string content: '{array}'")
        
        hint = f" ({'; '.join(suggestions)})" if suggestions else ""
        raise self._create_error(
            HPLIndexError,
            f"String index {index} out of bounds (length: {length}){hint}",
            expr.line, expr.column,
            local_scope,
            error_key='RUNTIME_INDEX_OUT_OF_BOUNDS'
        )
    
    def _access_list(self, array, index, expr, local_scope):
        """访问数组"""
        if not isinstance(index, int):
            index_type = type(index).__name__
            suggestions = []
            if isinstance(index, str) and index.isdigit():
                suggestions.append(f"Use int() to convert: int('{index}')")
            elif isinstance(index, float) and index.is_integer():
                suggestions.append(f"Use int() to convert: int({index})")
            elif index is None:
                suggestions.append("Index cannot be null")
            else:
                suggestions.append(f"Array index must be integer, got {index_type}")

            hint = f" ({'; '.join(suggestions)})" if suggestions else ""
            raise self._create_error(
                HPLTypeError,
                f"Array index must be integer, got {index_type} (value: {index!r}){hint}",
                expr.line, expr.column,
                local_scope,
                error_key='TYPE_INVALID_OPERATION'
            )
        
        length = len(array)
        if 0 <= index < length:
            return array[index]
        
        # 边界错误
        suggestions = []
        if index < 0 and length > 0:
            reverse_idx = length + index
            if 0 <= reverse_idx < length:
                suggestions.append(f"Use positive index {reverse_idx} to access element at position {abs(index)} from end")
        if index >= length:
            suggestions.append(f"Array length is {length}, max valid index is {length - 1}")
        if length > 0:
            suggestions.append(f"Valid index range: 0 to {length - 1}")
        else:
            suggestions.append("Array is empty, cannot access any index")
        
        if length > 0 and index >= 0 and index < length + 3:
            if index < length:
                element = array[index]
                element_type = type(element).__name__
                suggestions.append(f"Element at this position is: {element!r} (type: {element_type})")
            else:
                if length <= 5:
                    suggestions.append(f"Array content: {array}")
                else:
                    suggestions.append(f"First 5 elements of array: {array[:5]}")
        
        hint = f" ({'; '.join(suggestions)})" if suggestions else ""
        raise self._create_error(
            HPLIndexError,
            f"Array index {index} out of bounds (length: {length}){hint}",
            expr.line, expr.column,
            local_scope,
            error_key='RUNTIME_INDEX_OUT_OF_BOUNDS'
        )

    def _eval_binary_op(self, left, op, right, line=None, column=None):
        # 逻辑运算符
        if op == '&&':
            return left and right
        if op == '||':
            return left or right
        
        # 加法需要特殊处理（数组拼接、字符串拼接 vs 数值相加）
        if op == '+':
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            # 数组拼接
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            # 字符串拼接
            return str(left) + str(right)
        
        # 算术运算符需要数值操作数
        if op in ('-', '*', '/', '%'):
            check_numeric_operands(left, right, op)
        
        if op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                raise self._create_error(
                    HPLDivisionError,
                    "Division by zero. Hint: Add check if (divisor != 0) : result = dividend / divisor",
                    line, column,
                    error_key='RUNTIME_DIVISION_BY_ZERO'
                )

            return left / right
        elif op == '%':
            if right == 0:
                raise self._create_error(
                    HPLDivisionError,
                    "Modulo by zero. Hint: Add check if (divisor != 0) : result = dividend % divisor",
                    line, column,
                    error_key='RUNTIME_DIVISION_BY_ZERO'
                )

            return left % right

        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            check_numeric_operands(left, right, op)
            return left < right
        elif op == '<=':
            check_numeric_operands(left, right, op)
            return left <= right
        elif op == '>':
            check_numeric_operands(left, right, op)
            return left > right
        elif op == '>=':
            check_numeric_operands(left, right, op)
            return left >= right
        else:
            raise self._create_error(
                HPLRuntimeError,
                f"Unknown operator {op}",
                line, column,
                error_key='RUNTIME_GENERAL'
            )

    def _lookup_variable(self, name, local_scope, line=None, column=None):
        """统一变量查找逻辑"""
        # 处理 this.property 或 dict.key 形式的属性访问
        if '.' in name:
            obj_name, prop_name = name.split('.', 1)
            if obj_name == 'this':
                # 获取 this 对象
                obj = local_scope.get('this') or self.current_obj
                if obj is None:
                    raise self._create_error(
                        HPLNameError,
                        f"'this' is not defined outside of method context",
                        line, column,
                        local_scope,
                        error_key='RUNTIME_UNDEFINED_VAR'
                    )
                # 从对象属性中查找
                if isinstance(obj, HPLObject):
                    if prop_name in obj.attributes:
                        return obj.attributes[prop_name]
                    else:
                        raise self._create_error(
                            HPLAttributeError,
                            f"Property '{prop_name}' not found in object",
                            line, column,
                            local_scope,
                            error_key='TYPE_MISSING_PROPERTY'
                        )
                else:
                    raise self._create_error(
                        HPLTypeError,
                        f"'this' is not an object",
                        line, column,
                        local_scope,
                        error_key='TYPE_INVALID_OPERATION'
                    )
            else:
                # 普通对象或字典属性访问
                obj = self._lookup_variable(obj_name, local_scope, line, column)
                # 支持 HPLObject 属性访问
                if isinstance(obj, HPLObject):
                    if prop_name in obj.attributes:
                        return obj.attributes[prop_name]
                    else:
                        raise self._create_error(
                            HPLAttributeError,
                            f"Property '{prop_name}' not found in object '{obj_name}'",
                            line, column,
                            local_scope,
                            error_key='TYPE_MISSING_PROPERTY'
                        )
                # 支持字典键访问（新增）
                elif isinstance(obj, dict):
                    if prop_name in obj:
                        return obj[prop_name]
                    else:
                        # 尝试将 prop_name 作为变量解析
                        available_keys = list(obj.keys())[:5]
                        hint = f"Available keys: {available_keys}" if available_keys else "Dictionary is empty"
                        raise self._create_error(
                            HPLKeyError,
                            f"Key '{prop_name}' not found in '{obj_name}'. {hint}",
                            line, column,
                            local_scope,
                            error_key='RUNTIME_KEY_NOT_FOUND'
                        )
                else:
                    raise self._create_error(
                        HPLTypeError,
                        f"Cannot access property '{prop_name}' on '{obj_name}' of type {type(obj).__name__}",
                        line, column,
                        local_scope,
                        error_key='TYPE_INVALID_OPERATION'
                    )

        
        if name in local_scope:
            return local_scope[name]
        elif name in self.global_scope:
            return self.global_scope[name]
        else:
            raise self._create_error(
                HPLNameError,
                f"Undefined variable: '{name}'",
                line, column,
                local_scope,
                error_key='RUNTIME_UNDEFINED_VAR'
            )

    def _update_variable(self, name, value, local_scope):
        """统一变量更新逻辑"""
        if name in local_scope:
            local_scope[name] = value
        elif name in self.global_scope:
            self.global_scope[name] = value
        else:
            # 默认创建局部变量
            local_scope[name] = value

    def _find_method_in_class_hierarchy(self, hpl_class, method_name):
        """在类继承层次结构中查找方法"""
        # 支持 init 作为 __init__ 的别名
        if method_name == 'init':
            alt_method_name = '__init__'
        elif method_name == '__init__':
            alt_method_name = 'init'
        else:
            alt_method_name = None
        
        # 当前类中查找
        if method_name in hpl_class.methods:
            return hpl_class.methods[method_name]
        if alt_method_name and alt_method_name in hpl_class.methods:
            return hpl_class.methods[alt_method_name]
        
        # 向上递归查找父类
        if hpl_class.parent:
            parent_class = self.classes.get(hpl_class.parent)
            if parent_class:
                return self._find_method_in_class_hierarchy(parent_class, method_name)
        
        return None

    def _find_method_owner_class(self, hpl_class, method_name):
        """查找方法所属的类（用于确定 current_class）"""
        # 支持 init 作为 __init__ 的别名
        if method_name == 'init':
            alt_method_name = '__init__'
        elif method_name == '__init__':
            alt_method_name = 'init'
        else:
            alt_method_name = None
        
        # 当前类中查找
        if method_name in hpl_class.methods:
            return hpl_class
        if alt_method_name and alt_method_name in hpl_class.methods:
            return hpl_class
        
        # 向上递归查找父类
        if hpl_class.parent:
            parent_class = self.classes.get(hpl_class.parent)
            if parent_class:
                return self._find_method_owner_class(parent_class, method_name)
        
        return None

    def _call_method(self, obj, method_name, args):

        """统一方法调用逻辑"""
        # 处理父类方法调用（当 obj 是 HPLClass 时）
        if isinstance(obj, HPLClass):
            # 支持 init 作为 __init__ 的别名
            actual_method_name = method_name
            if method_name == 'init' and 'init' not in obj.methods and '__init__' in obj.methods:
                actual_method_name = '__init__'
            if method_name in obj.methods or actual_method_name in obj.methods:
                method = obj.methods.get(method_name) or obj.methods.get(actual_method_name)
                # 父类方法调用时，this 仍然指向当前对象
                method_scope = {param: args[i] for i, param in enumerate(method.params) if i < len(args)}
                method_scope['this'] = self.current_obj
                # 设置 current_class 为父类，以支持多级继承中的 this.parent 访问
                prev_class = self.current_class
                self.current_class = obj
                try:
                    return self.execute_function(method, method_scope)
                finally:
                    self.current_class = prev_class
            else:
                raise self._create_error(
                    HPLAttributeError,
                    f"Method '{method_name}' not found in parent class '{obj.name}'",
                    error_key='TYPE_MISSING_PROPERTY'
                )

        hpl_class = obj.hpl_class
        
        # 在类继承层次结构中查找方法
        method = self._find_method_in_class_hierarchy(hpl_class, method_name)
        
        if method is None:
            # 不是方法，尝试作为属性访问
            if method_name in obj.attributes:
                return obj.attributes[method_name]
            raise self._create_error(
                HPLAttributeError,
                f"Method or attribute '{method_name}' not found in class '{hpl_class.name}'",
                error_key='TYPE_MISSING_PROPERTY'
            )

        # 为'this'设置current_obj
        prev_obj = self.current_obj
        self.current_obj = obj
        
        # 确定方法所属的类（用于设置 current_class）
        method_owner_class = self._find_method_owner_class(hpl_class, method_name)
        
        # 设置 current_class 为方法所属的类，以支持多级继承中的 this.parent 访问
        prev_class = self.current_class
        self.current_class = method_owner_class if method_owner_class else hpl_class
        
        # 创建方法调用的局部作用域
        method_scope = {param: args[i] for i, param in enumerate(method.params) if i < len(args)}
        method_scope['this'] = obj
        
        # 添加到调用栈
        obj_name = obj.hpl_class.name if isinstance(obj, HPLObject) else obj.name
        self.call_stack.append(f"{obj_name}.{method_name}()")
        
        try:
            result = self.execute_function(method, method_scope)
        finally:
            # 从调用栈移除
            self.call_stack.pop()
            self.current_obj = prev_obj
            self.current_class = prev_class
        
        return result

    def _call_constructor(self, obj, args):
        """调用对象的构造函数（如果存在）"""
        hpl_class = obj.hpl_class
        
        # 在类继承层次结构中查找构造函数（支持 init 和 __init__）
        # 优先查找 init，然后是 __init__
        constructor = self._find_method_in_class_hierarchy(hpl_class, 'init')
        if constructor is None:
            constructor = self._find_method_in_class_hierarchy(hpl_class, '__init__')
        
        if constructor:
            self._call_method(obj, 'init' if self._find_method_in_class_hierarchy(hpl_class, 'init') else '__init__', args)
    
    def _call_parent_constructors_recursive(self, obj, parent_class, args):
        """递归调用父类构造函数链"""
        # 继续向上查找祖先类的构造函数
        if parent_class.parent:
            grandparent_class = self.classes.get(parent_class.parent)
            if grandparent_class:
                grandparent_constructor_name = None
                if 'init' in grandparent_class.methods:
                    grandparent_constructor_name = 'init'
                elif '__init__' in grandparent_class.methods:
                    grandparent_constructor_name = '__init__'
                
                if grandparent_constructor_name:
                    method = grandparent_class.methods[grandparent_constructor_name]
                    prev_obj = self.current_obj
                    self.current_obj = obj
                    
                    method_scope = {param: args[i] for i, param in enumerate(method.params) if i < len(args)}
                    method_scope['this'] = obj
                    
                    obj_name = obj.hpl_class.name if isinstance(obj, HPLObject) else obj.name
                    self.call_stack.append(f"{obj_name}.{grandparent_constructor_name}()")

                    try:
                        self.execute_function(method, method_scope)
                    finally:
                        self.call_stack.pop()
                        self.current_obj = prev_obj
                
                # 只有当祖父类还有父类时才继续递归向上
                if grandparent_class.parent:
                    self._call_parent_constructors_recursive(obj, grandparent_class, args)

    def instantiate_object(self, class_name: str, obj_name: str, init_args: Optional[list[Any]] = None) -> HPLObject:
        """实例化对象并调用构造函数"""
        if class_name not in self.classes:
            raise self._create_error(
                HPLNameError,
                f"Class '{class_name}' not found",
                error_key='RUNTIME_UNDEFINED_VAR'
            )
        
        hpl_class = self.classes[class_name]

        obj = HPLObject(obj_name, hpl_class)
        
        # 调用构造函数（如果存在）
        if init_args is None:
            init_args = []
        
        # 设置 current_class 为对象的类，以支持构造函数中的 this.parent 访问
        prev_class = self.current_class
        self.current_class = hpl_class
        try:
            self._call_constructor(obj, init_args)
        finally:
            self.current_class = prev_class
        
        return obj

    def execute_import(self, stmt: ImportStatement, local_scope: dict[str, Any]) -> None:
        """执行 import 语句"""
        module_name = stmt.module_name
        alias = stmt.alias or module_name
        
        try:
            # 加载模块
            module = load_module(module_name)
            if module:
                # 存储模块引用
                self.imported_modules[alias] = module
                local_scope[alias] = module
                return None
        except ImportError as e:
            raise self._create_error(
                HPLImportError,
                f"Cannot import module '{module_name}': {e}",
                error_key='IMPORT_MODULE_NOT_FOUND'
            ) from e
        
        raise self._create_error(
            HPLImportError,
            f"Module '{module_name}' not found",
            error_key='IMPORT_MODULE_NOT_FOUND'
        )

    def call_module_function(self, module: Any, func_name: str, args: list[Any]) -> Any:
        """调用模块函数"""
        if is_hpl_module(module):
            return module.call_function(func_name, args)
        raise self._create_error(
            HPLTypeError,
            f"Cannot call function on non-module object",
            error_key='TYPE_INVALID_OPERATION'
        )

    def get_module_constant(self, module: Any, const_name: str) -> Any:
        """获取模块常量"""
        if is_hpl_module(module):
            return module.get_constant(const_name)
        raise self._create_error(
            HPLTypeError,
            f"Cannot get constant from non-module object",
            error_key='TYPE_INVALID_OPERATION'
        )

    def _create_error(self, error_class: type[HPLError], message: str, line: Optional[int] = None, 
                    column: Optional[int] = None, local_scope: Optional[dict[str, Any]] = None, 
                    error_key: Optional[str] = None, **kwargs: Any) -> HPLError:
        """统一创建错误并添加上下文"""
        # 自动捕获当前调用栈（如果尚未设置）
        call_stack = kwargs.pop('call_stack', None) or self.call_stack.copy()
        
        error = error_class(
            message=message,
            line=line,
            column=column,
            file=getattr(self, 'current_file', None),
            call_stack=call_stack,
            error_key=error_key,
            **kwargs
        )
        
        # 自动丰富上下文
        if local_scope is not None and hasattr(error, 'enrich_context'):
            error.enrich_context(self, local_scope)
        
        return error

    def _matches_error_type(self, error: HPLError, error_type: Optional[str]) -> bool:
        """检查错误是否匹配指定的错误类型"""
        if error_type is None:
            return True  # 捕获所有错误
        
        # 获取错误类型的类名
        error_class_name = error.__class__.__name__
        
        # 直接匹配类名
        if error_type == error_class_name:
            return True
        
        # 支持不带 HPL 前缀的匹配
        if error_type == error_class_name.replace('HPL', ''):
            return True
        
        # 检查继承关系 - 使用完整的错误类型映射
        error_type_map: dict[str, type[HPLError]] = {
            # 基础错误
            'HPLError': HPLError,
            'Error': HPLError,
            
            # 语法错误
            'HPLSyntaxError': HPLSyntaxError,
            'SyntaxError': HPLSyntaxError,
            
            # 运行时错误及其子类
            'HPLRuntimeError': HPLRuntimeError,
            'RuntimeError': HPLRuntimeError,
            'HPLTypeError': HPLTypeError,
            'TypeError': HPLTypeError,
            'HPLNameError': HPLNameError,
            'NameError': HPLNameError,
            'HPLAttributeError': HPLAttributeError,
            'AttributeError': HPLAttributeError,
            'HPLIndexError': HPLIndexError,
            'IndexError': HPLIndexError,
            'HPLDivisionError': HPLDivisionError,
            'DivisionError': HPLDivisionError,
            'HPLValueError': HPLValueError,
            'ValueError': HPLValueError,
            'HPLIOError': HPLIOError,
            'IOError': HPLIOError,
            'HPLRecursionError': HPLRecursionError,
            'RecursionError': HPLRecursionError,
            
            # 导入错误
            'HPLImportError': HPLImportError,
            'ImportError': HPLImportError,
        }
        
        target_class = error_type_map.get(error_type)
        if target_class:
            return isinstance(error, target_class)
        
        return False
