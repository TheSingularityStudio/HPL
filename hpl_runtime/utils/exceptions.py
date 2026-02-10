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
    """
    
    def __init__(self, message, line=None, column=None, file=None, context=None):
        super().__init__(message)
        self.line = line
        self.column = column
        self.file = file
        self.context = context
    
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


class HPLSyntaxError(HPLError):
    """
    HPL 语法错误
    
    在词法分析或语法分析阶段发现的错误。
    例如：意外的 token、缺少括号等。
    """
    pass


class HPLRuntimeError(HPLError):
    """
    HPL 运行时错误
    
    在代码执行阶段发生的错误。
    例如：未定义变量、类型不匹配等。
    """
    
    def __init__(self, message, line=None, column=None, file=None, context=None, 
                 call_stack=None):
        super().__init__(message, line, column, file, context)
        self.call_stack = call_stack or []
    
    def __str__(self):
        result = super().__str__()
        
        if self.call_stack:
            result += "\n  Call stack:"
            for i, frame in enumerate(reversed(self.call_stack), 1):
                result += f"\n    {i}. {frame}"
        
        return result


class HPLTypeError(HPLRuntimeError):
    """
    HPL 类型错误
    
    操作数类型不匹配或类型转换失败。
    例如：对字符串进行算术运算。
    """
    pass


class HPLNameError(HPLRuntimeError):
    """
    HPL 名称错误
    
    引用了未定义的变量、函数或类。
    """
    pass


class HPLAttributeError(HPLRuntimeError):
    """
    HPL 属性错误
    
    访问不存在的对象属性或方法。
    """
    pass


class HPLIndexError(HPLRuntimeError):
    """
    HPL 索引错误
    
    数组索引越界或无效的索引操作。
    """
    pass


class HPLImportError(HPLError):
    """
    HPL 导入错误
    
    模块导入失败。
    例如：模块不存在、导入循环等。
    """
    pass


class HPLDivisionError(HPLRuntimeError):
    """
    HPL 除零错误
    
    除法或取模运算中除数为零。
    """
    pass


class HPLValueError(HPLRuntimeError):
    """
    HPL 值错误
    
    数值超出有效范围或无效的值。
    例如：负数开平方。
    """
    pass


class HPLIOError(HPLRuntimeError):
    """
    HPL IO 错误
    
    输入输出操作失败。
    例如：文件不存在、权限不足等。
    """
    pass


class HPLRecursionError(HPLRuntimeError):
    """
    HPL 递归错误
    
    递归调用过深或无限递归。
    """
    pass


class HPLBreakException(HPLError):
    """
    用于跳出循环的内部异常
    
    注意：这是控制流异常，不是错误，不应被用户代码捕获。
    """
    pass


class HPLContinueException(HPLError):
    """
    用于继续下一次循环的内部异常
    
    注意：这是控制流异常，不是错误，不应被用户代码捕获。
    """
    pass


class HPLReturnValue(HPLError):
    """
    用于传递返回值的内部异常
    
    注意：这是控制流异常，不是错误，不应被用户代码捕获。
    """
    def __init__(self, value):
        self.value = value
        super().__init__("Return value wrapper")



def format_error_for_user(error, source_code=None):
    """
    格式化错误信息供用户查看
    
    Args:
        error: HPLError 实例
        source_code: 源代码字符串（可选），用于显示上下文
    
    Returns:
        格式化后的错误字符串
    """
    if not isinstance(error, HPLError):
        # 非 HPL 异常，返回标准格式
        return f"Error: {error}"
    
    lines = []
    lines.append(f"[ERROR] {error.__class__.__name__}: {str(error).split('] ', 1)[-1]}")

    
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
            
            # 显示错误位置指示器
            if error.column is not None:
                indicator = " " * (8 + error.column) + "^"
                lines.append(indicator)
    
    # 显示调用栈
    if isinstance(error, HPLRuntimeError) and error.call_stack:
        lines.append("\n   Call stack (most recent last):")
        for i, frame in enumerate(reversed(error.call_stack), 1):
            lines.append(f"      {i}. {frame}")
    
    return '\n'.join(lines)
