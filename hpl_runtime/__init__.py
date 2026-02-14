"""
HPL 解释器包

HPL (H Programming Language) 是一种基于 YAML 格式的面向对象编程语言。

主要组件:
- 解释器: HPLInterpreter (interpreter.py)
- 词法分析: HPLLexer, Token (core.lexer)
- 语法分析: HPLParser (core.parser), HPLASTParser (core.ast_parser)
- 执行器: HPLEvaluator (core.evaluator)
- 数据模型: HPLClass, HPLObject, HPLFunction 等 (core.models)
- 异常体系: HPLError, HPLSyntaxError, HPLRuntimeError 等 (utils.exceptions)
- 调试工具: ErrorAnalyzer, DebugInterpreter (debug)
- 模块加载: load_module, register_module (modules.loader)

使用方法:
    from hpl_runtime import HPLParser, HPLEvaluator
    from hpl_runtime import HPLError, HPLSyntaxError
"""

__version__ = "1.1.5"
__author__ = "奇点工作室"

# 导出主要类，方便外部使用
try:
    # 核心解释器
    from .interpreter import main
    
    # 词法分析
    from .core.lexer import HPLLexer, Token
    
    # 语法分析
    from .core.parser import HPLParser
    from .core.ast_parser import HPLASTParser
    
    # 执行器
    from .core.evaluator import HPLEvaluator
    
    # 数据模型 - 基础类
    from .core.models import (
        HPLClass, HPLObject, HPLFunction,
        # 表达式基类
        Expression, Statement,
        # 字面量
        IntegerLiteral, FloatLiteral, StringLiteral, BooleanLiteral, NullLiteral,
        # 表达式
        BinaryOp, Variable, FunctionCall, MethodCall, 
        PostfixIncrement, UnaryOp, ArrayLiteral, ArrayAccess, DictionaryLiteral,
        # 语句
        AssignmentStatement, ArrayAssignmentStatement, ReturnStatement, 
        BlockStatement, IfStatement, ForInStatement, WhileStatement, 
        TryCatchStatement, CatchClause,
        EchoStatement, ImportStatement, IncrementStatement,
        BreakStatement, ContinueStatement, ThrowStatement,
    )
    
    # 异常体系
    from .utils.exceptions import (
        HPLError, HPLSyntaxError, HPLRuntimeError, HPLTypeError,
        HPLNameError, HPLAttributeError, HPLIndexError, HPLKeyError,
        HPLImportError, HPLDivisionError, HPLValueError, HPLIOError,
        HPLRecursionError, HPLControlFlowException, HPLBreakException,
        HPLContinueException, HPLReturnValue, format_error_for_user,
    )
    
    # 调试工具
    from .debug import ErrorAnalyzer, DebugInterpreter
    
    # 模块加载
    from .modules.loader import (
        load_module, register_module, get_module, set_current_hpl_file,
        add_module_path, clear_cache,
    )
except ImportError:
    # 如果相对导入失败，使用绝对导入
    pass

# 公开 API 列表
__all__ = [
    # 元信息
    '__version__', '__author__',
    
    # 解释器入口
    'main',
    
    # 词法分析
    'HPLLexer', 'Token',
    
    # 语法分析
    'HPLParser', 'HPLASTParser',
    
    # 执行器
    'HPLEvaluator',
    
    # 数据模型 - 基础类
    'HPLClass', 'HPLObject', 'HPLFunction',
    'Expression', 'Statement',
    
    # 数据模型 - 字面量
    'IntegerLiteral', 'FloatLiteral', 'StringLiteral', 
    'BooleanLiteral', 'NullLiteral',
    
    # 数据模型 - 表达式
    'BinaryOp', 'Variable', 'FunctionCall', 'MethodCall',
    'PostfixIncrement', 'UnaryOp', 'ArrayLiteral', 'ArrayAccess', 
    'DictionaryLiteral',
    
    # 数据模型 - 语句
    'AssignmentStatement', 'ArrayAssignmentStatement', 'ReturnStatement',
    'BlockStatement', 'IfStatement', 'ForInStatement', 'WhileStatement',
    'TryCatchStatement', 'CatchClause', 'EchoStatement', 'ImportStatement',
    'IncrementStatement', 'BreakStatement', 'ContinueStatement', 'ThrowStatement',
    
    # 异常类
    'HPLError', 'HPLSyntaxError', 'HPLRuntimeError', 'HPLTypeError',
    'HPLNameError', 'HPLAttributeError', 'HPLIndexError', 'HPLKeyError',
    'HPLImportError', 'HPLDivisionError', 'HPLValueError', 'HPLIOError',
    'HPLRecursionError', 'HPLControlFlowException', 'HPLBreakException',
    'HPLContinueException', 'HPLReturnValue', 'format_error_for_user',
    
    # 调试工具
    'ErrorAnalyzer', 'DebugInterpreter',
    
    # 模块加载
    'load_module', 'register_module', 'get_module', 'set_current_hpl_file',
    'add_module_path', 'clear_cache',
]
