"""
HPL 调试工具包

该模块提供 HPL 运行时的调试和分析功能，用于：
- 跟踪错误传播路径
- 分析调用栈信息
- 捕获变量状态
- 记录执行流程

主要组件：
- ErrorAnalyzer: 错误分析器主类
- DebugInterpreter: 支持调试的解释器
- ExecutionTracer: 执行跟踪器

使用方法：
    from hpl_runtime.debug import ErrorAnalyzer, DebugInterpreter
    
    # 使用调试解释器运行脚本
    interpreter = DebugInterpreter()
    result = interpreter.run("example.hpl")
    
    # 或者分析已有的错误
    analyzer = ErrorAnalyzer()
    analyzer.analyze_error(error, source_code)
"""

from .error_analyzer import (
    ErrorAnalyzer,
    ErrorTracer,
    CallStackAnalyzer,
    VariableInspector,
    ExecutionLogger,
    ErrorContext
)

from .debug_interpreter import DebugInterpreter

__all__ = [
    'ErrorAnalyzer',
    'ErrorTracer',
    'CallStackAnalyzer',
    'VariableInspector',
    'ExecutionLogger',
    'ErrorContext',
    'DebugInterpreter',
]
