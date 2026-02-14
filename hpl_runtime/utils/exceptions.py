"""
HPL 异常体系模块

该模块定义了 HPL 解释器使用的所有异常类型，提供统一的错误处理机制。
所有异常都包含位置信息（行号、列号、文件名），便于调试。
"""

class HPLError(Exception):
    """
    HPL 基础异常类
    
    所有 HPL 异常的基类，包含位置信息和上下文。
    
    Attributes:
        message: 错误消息
        line: 源代码行号（可选）
        column: 源代码列号（可选）
        file: 源文件名（可选）
        context: 上下文代码片段（可选）
        error_code: 错误代码（可选）
    """
    
    # 错误代码前缀
    ERROR_CODE_PREFIX = "HPL"
    
    # 错误代码映射表
    ERROR_CODE_MAP = {
        # 语法错误 (1xx)
        'SYNTAX_UNEXPECTED_TOKEN': 'HPL-SYNTAX-101',
        'SYNTAX_MISSING_BRACKET': 'HPL-SYNTAX-102',
        'SYNTAX_INVALID_INDENT': 'HPL-SYNTAX-103',
        'SYNTAX_YAML_ERROR': 'HPL-SYNTAX-150',
        
        # 运行时错误 (2xx)
        'RUNTIME_UNDEFINED_VAR': 'HPL-RUNTIME-201',
        'RUNTIME_TYPE_MISMATCH': 'HPL-RUNTIME-202',
        'RUNTIME_INDEX_OUT_OF_BOUNDS': 'HPL-RUNTIME-203',
        'RUNTIME_DIVISION_BY_ZERO': 'HPL-RUNTIME-204',
        'RUNTIME_NULL_POINTER': 'HPL-RUNTIME-205',
        'RUNTIME_RECURSION_DEPTH': 'HPL-RUNTIME-206',
        
        # 类型错误 (3xx)
        'TYPE_INVALID_OPERATION': 'HPL-TYPE-301',
        'TYPE_CONVERSION_FAILED': 'HPL-TYPE-302',
        'TYPE_MISSING_PROPERTY': 'HPL-TYPE-303',
        
        # 导入错误 (4xx)
        'IMPORT_MODULE_NOT_FOUND': 'HPL-IMPORT-401',
        'IMPORT_CIRCULAR': 'HPL-IMPORT-402',
        'IMPORT_VERSION_MISMATCH': 'HPL-IMPORT-403',
        
        # IO 错误 (5xx)
        'IO_FILE_NOT_FOUND': 'HPL-IO-501',
        'IO_PERMISSION_DENIED': 'HPL-IO-502',
        'IO_READ_ERROR': 'HPL-IO-503',
    }
    
    def __init__(self, message, line=None, column=None, file=None, context=None, 
                 error_code=None, error_key=None):
        # 支持通过 error_key 自动获取错误代码
        if error_key and not error_code:
            error_code = self.ERROR_CODE_MAP.get(error_key)
        
        super().__init__(message)
        self.line = line
        self.column = column
        self.file = file
        self.context = context
        self.error_code = error_code
    
    def __str__(self):
        parts = [self.__class__.__name__]
        
        if self.file:
            parts.append(f"in '{self.file}'")
        
        location = ""
        if self.line is not None:
            location += f"line {self.line}"
            if self.column is not None:
                location += f", column {self.column}"
        
        if location:
            parts.append(f"at {location}")
        
        result = f"[{' '.join(parts)}] {super().__str__()}"
        
        if self.context:
            result += f"\n  Context: {self.context}"
        
        return result
    
    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"message={super().__str__()!r}, "
                f"line={self.line!r}, "
                f"column={self.column!r}, "
                f"file={self.file!r})")
    
    @property
    def error_message(self):
        """获取纯错误消息，不包含位置信息"""
        return super().__str__()
    
    def get_error_code(self):
        """获取错误代码，子类可以覆盖此方法"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-GENERAL"
    
    def get_help_url(self):
        """获取帮助文档链接"""
        error_code = self.get_error_code()
        if error_code and error_code != f"{self.ERROR_CODE_PREFIX}-GENERAL":
            base_url = "https://github.com/TheSingularityStudio/HPL/wiki/help"
            return f"{base_url}#{error_code}"
        return None

class HPLSyntaxError(HPLError):
    """
    HPL 语法错误
    
    在词法分析或语法分析阶段发现的错误。
    例如：意外的 token、缺少括号等。
    """
    
    def get_error_code(self):
        """语法错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-SYNTAX-001"

class HPLRuntimeError(HPLError):
    """
    HPL 运行时错误
    
    在代码执行阶段发生的错误。
    例如：未定义变量、类型不匹配等。
    """
    
    def __init__(self, message, line=None, column=None, file=None, context=None, 
                 call_stack=None, error_code=None, **kwargs):
        super().__init__(message, line, column, file, context, error_code)
        self.call_stack = call_stack or []
        # 新增上下文信息
        self.variable_snapshot = kwargs.get('variable_snapshot', {})
        self.execution_trace = kwargs.get('execution_trace', [])
        self.function_args = kwargs.get('function_args', {})
        self.recent_assignments = kwargs.get('recent_assignments', [])
    
    def __str__(self):
        result = super().__str__()
        
        if self.call_stack:
            result += "\n  Call stack:"
            for i, frame in enumerate(self.call_stack, 1):
                result += f"\n    {i}. {frame}"
        
        return result
    
    def get_error_code(self):
        """运行时错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-RUNTIME-001"
    
    def enrich_context(self, evaluator, local_scope):
        """从 evaluator 捕获运行时上下文"""
        if evaluator:
            # 捕获变量状态
            self.variable_snapshot = {
                'local': {k: v for k, v in local_scope.items() if not k.startswith('_')},
                'global_keys': list(evaluator.global_scope.keys()),
                'current_obj': evaluator.current_obj
            }
            # 捕获最近执行轨迹
            if hasattr(evaluator, 'exec_logger'):
                self.execution_trace = evaluator.exec_logger.get_trace(last_n=10)

class HPLTypeError(HPLRuntimeError):
    """
    HPL 类型错误
    
    操作数类型不匹配或类型转换失败。
    例如：对字符串进行算术运算。
    """
    
    def get_error_code(self):
        """类型错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-TYPE-001"

class HPLNameError(HPLRuntimeError):
    """
    HPL 名称错误
    
    引用了未定义的变量、函数或类。
    """
    
    def get_error_code(self):
        """名称错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-NAME-001"

class HPLAttributeError(HPLRuntimeError):
    """
    HPL 属性错误
    
    访问不存在的对象属性或方法。
    """
    
    def get_error_code(self):
        """属性错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-ATTR-001"

class HPLIndexError(HPLRuntimeError):
    """
    HPL 索引错误
    
    数组索引越界或无效的索引操作。
    """
    
    def get_error_code(self):
        """索引错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-INDEX-001"

class HPLKeyError(HPLRuntimeError):
    """
    HPL 键错误
    
    字典中访问不存在的键。
    """
    
    def get_error_code(self):
        """键错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-KEY-001"

class HPLImportError(HPLError):
    """
    HPL 导入错误
    
    模块导入失败。
    例如：模块不存在、导入循环等。
    """
    
    def __init__(self, message, line=None, column=None, file=None, context=None,
                 module_name=None, import_path=None, error_code=None, error_key=None):
        super().__init__(message, line, column, file, context, error_code, error_key)
        self.module_name = module_name
        self.import_path = import_path
    
    def get_error_code(self):
        """导入错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-IMPORT-001"
    
    def __str__(self):
        result = super().__str__()
        if self.module_name:
            result += f"\n  Module: {self.module_name}"
        if self.import_path:
            result += f"\n  Import path: {self.import_path}"
        return result

class HPLDivisionError(HPLRuntimeError):
    """
    HPL 除零错误
    
    除法或取模运算中除数为零。
    """
    
    def get_error_code(self):
        """除零错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-DIV-001"

class HPLValueError(HPLRuntimeError):
    """
    HPL 值错误
    
    数值超出有效范围或无效的值。
    例如：负数开平方。
    """
    
    def get_error_code(self):
        """值错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-VALUE-001"

class HPLIOError(HPLRuntimeError):
    """
    HPL IO 错误
    
    输入输出操作失败。
    例如：文件不存在、权限不足等。
    """
    
    def __init__(self, message, line=None, column=None, file=None, context=None,
                 path=None, operation=None, error_code=None, error_key=None, **kwargs):
        super().__init__(message, line, column, file, context, error_code, **kwargs)
        self.path = path
        self.operation = operation
    
    def get_error_code(self):
        """IO错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-IO-001"
    
    def __str__(self):
        result = super().__str__()
        if self.operation:
            result += f"\n  Operation: {self.operation}"
        if self.path:
            result += f"\n  Path: {self.path}"
        return result

class HPLRecursionError(HPLRuntimeError):
    """
    HPL 递归错误
    
    递归调用过深或无限递归。
    """
    
    def __init__(self, message, line=None, column=None, file=None, context=None,
                 recursion_depth=None, max_depth=None, error_code=None, error_key=None, **kwargs):
        # 从 kwargs 中提取 call_stack，以避免将其传递给父类时重复
        call_stack = kwargs.pop('call_stack', None)
        super().__init__(message, line, column, file, context, call_stack, error_code, error_key=error_key, **kwargs)
        self.recursion_depth = recursion_depth
        self.max_depth = max_depth
    
    def get_error_code(self):
        """递归错误代码"""
        if self.error_code:
            return self.error_code
        return f"{self.ERROR_CODE_PREFIX}-RECURSION-001"
    
    def __str__(self):
        result = super().__str__()
        if self.recursion_depth is not None:
            result += f"\n  Recursion depth: {self.recursion_depth}"
        if self.max_depth is not None:
            result += f"\n  Maximum allowed depth: {self.max_depth}"
        return result

class HPLControlFlowException(HPLError):
    """
    控制流异常的基类
    
    用于break、continue、return等控制流，不是真正的错误。
    这些异常不应该被错误格式化器处理。
    """
    
    def __init__(self, message=None, line=None, column=None, file=None, context=None):
        super().__init__(message or "Control flow", line, column, file, context)
    
    def get_error_code(self):
        """控制流异常没有错误代码"""
        return None

class HPLBreakException(HPLControlFlowException):
    """
    用于跳出循环的内部异常
    
    注意：这是控制流异常，不是错误，不应被用户代码捕获。
    """
    def __init__(self, message=None, line=None, column=None, file=None, context=None):
        # 控制流异常不需要消息，提供默认值
        super().__init__(message or "Break statement", line, column, file, context)

class HPLContinueException(HPLControlFlowException):
    """
    用于继续下一次循环的内部异常
    
    注意：这是控制流异常，不是错误，不应被用户代码捕获。
    """
    def __init__(self, message=None, line=None, column=None, file=None, context=None):
        # 控制流异常不需要消息，提供默认值
        super().__init__(message or "Continue statement", line, column, file, context)

class HPLReturnValue(HPLControlFlowException):
    """
    用于传递返回值的内部异常
    
    注意：这是控制流异常，不是错误，不应被用户代码捕获。
    """
    def __init__(self, value, line=None, column=None, file=None, context=None):
        self.value = value
        super().__init__("Return value wrapper", line, column, file, context)

def format_error_for_user(error, source_code=None):
    """
    格式化错误信息供用户查看
    
    Args:
        error: HPLError 实例
        source_code: 源代码字符串（可选），用于显示上下文
    
    Returns:
        格式化后的错误字符串
    """
    # 控制流异常不应该被格式化
    if isinstance(error, HPLControlFlowException):
        raise error  # 重新抛出，让上层处理
    
    if not isinstance(error, HPLError):
        # 非 HPL 异常，返回标准格式
        return f"Error: {error}"
    
    lines = []
    
    # 错误类型标签
    if isinstance(error, HPLSyntaxError):
        error_label = "[SYNTAX_ERROR]"
    elif isinstance(error, HPLImportError):
        error_label = "[IMPORT_ERROR]"
    elif isinstance(error, HPLRuntimeError):
        error_label = "[RUNTIME_ERROR]"
    else:
        error_label = "[ERROR]"
    
    # 使用 error_message 属性获取纯消息，避免解析问题
    message = getattr(error, 'error_message', str(error).split('] ', 1)[-1])
    
    # 添加错误代码（如果有）
    error_code = error.get_error_code()
    if error_code:
        lines.append(f"{error_label} [{error_code}] {error.__class__.__name__}: {message}")
    else:
        lines.append(f"{error_label} {error.__class__.__name__}: {message}")
    
    if error.file:
        lines.append(f"   File: {error.file}")
    
    if error.line is not None:
        location = f"   Line: {error.line}"
        if error.column is not None:
            location += f", Column: {error.column}"
        lines.append(location)
    
    # 显示源代码上下文
    if source_code and error.line is not None:
        source_lines = source_code.split('\n')
        if 1 <= error.line <= len(source_lines):
            # 显示错误行及前后各一行
            start = max(0, error.line - 2)
            end = min(len(source_lines), error.line + 1)
            
            lines.append("\n   Source context:")
            for i in range(start, end):
                line_num = i + 1
                prefix = ">>> " if line_num == error.line else "    "
                lines.append(f"{prefix}{line_num:4d} | {source_lines[i]}")
            
            # 显示错误位置指示器（动态计算位置）
            if error.column is not None:
                # 动态计算前缀长度：根据行号的实际位数
                # 格式: ">>> " 或 "    " (4字符) + 行号 (变长) + " | " (3字符)
                line_num_str = str(error.line)
                prefix_len = 4  # ">>> " 或 "    "
                separator_len = 3  # " | "
                base_offset = prefix_len + len(line_num_str) + separator_len
                indicator = " " * (base_offset + error.column - 1) + "^"  # -1因为column从1开始
                lines.append(indicator)

    # 显示调用栈（改为 most recent first）
    if isinstance(error, HPLRuntimeError) and error.call_stack:
        lines.append("\n   Call stack (most recent first):")
        for i, frame in enumerate(error.call_stack, 1):
            lines.append(f"      {i}. {frame}")
    
    # 显示变量快照（如果有）
    if isinstance(error, HPLRuntimeError) and error.variable_snapshot:
        lines.append("\n   Variable snapshot:")
        local_vars = error.variable_snapshot.get('local', {})
        if local_vars:
            lines.append("      Local variables:")
            for name, value in list(local_vars.items())[:5]:  # 最多显示5个
                lines.append(f"        {name} = {value!r}")
    
    # 显示帮助链接
    help_url = error.get_help_url()
    if help_url:
        lines.append(f"\n   [DOC] {help_url}")

    # 显示错误解决建议
    suggestion = get_error_suggestion(error)
    if suggestion:
        lines.append(f"\n   [TIP] {suggestion}")

    return '\n'.join(lines)

def get_error_suggestion(error):
    """根据错误类型提供解决建议"""
    suggestions = {
        'HPLNameError': "检查变量名拼写，或确认变量已在使用前定义",
        'HPLTypeError': "检查操作数的类型，必要时使用类型转换函数 int() 或 str()",
        'HPLIndexError': "检查数组长度和索引值，确保 0 <= index < len(array)",
        'HPLKeyError': "检查字典中是否存在该键，或使用 get() 方法提供默认值",
        'HPLDivisionError': "添加除零检查，如: if (divisor != 0) : result = dividend / divisor",
        'HPLImportError': "检查模块名称拼写，或确认模块已正确安装",
    }
    return suggestions.get(error.__class__.__name__)

def format_error_with_suggestions(error, source_code=None, suggestion_engine=None):
    """
    格式化错误信息并添加智能建议
    
    Args:
        error: HPLError 实例
        source_code: 源代码字符串（可选）
        suggestion_engine: ErrorSuggestionEngine 实例（可选）
    
    Returns:
        格式化后的错误字符串
    """
    # 获取基础错误信息
    result = format_error_for_user(error, source_code)
    
    # 如果没有建议引擎，直接返回基础信息
    if suggestion_engine is None:
        return result
    
    # 获取智能建议
    try:
        analysis = suggestion_engine.analyze_error(error)
        
        # 添加智能建议
        if analysis.get('suggestions'):
            result += "\n\n   [TIP] 智能建议:"

            for i, suggestion in enumerate(analysis['suggestions'], 1):
                # 处理多行建议
                lines = suggestion.split('\n')
                result += f"\n      {i}. {lines[0]}"
                for line in lines[1:]:
                    result += f"\n         {line}"
        
        # 添加快速修复代码
        if analysis.get('quick_fix'):
            result += f"\n\n   [FIX] 快速修复:\n   ```\n   {analysis['quick_fix']}\n   ```"

    except (AttributeError, TypeError, ValueError, KeyError):
        # 如果建议引擎出错，不影响错误显示
        pass

    return result
