"""
HPL 解释器包

HPL (H Programming Language) 是一种基于 YAML 格式的面向对象编程语言。
"""

__version__ = "1.0.0"
__author__ = "奇点工作室"

# 导出主要类，方便外部使用
try:
    from .interpreter import main
    from .core.lexer import HPLLexer, Token
    from .core.parser import HPLParser
    from .core.evaluator import HPLEvaluator
    from .core.models import (
        HPLClass, HPLObject, HPLFunction,
        AssignmentStatement, ReturnStatement, IfStatement,
        ForStatement, WhileStatement, TryCatchStatement,
        EchoStatement, ImportStatement, BreakStatement, ContinueStatement,
        ArrayAssignmentStatement
    )
except ImportError:
    # 如果相对导入失败，使用绝对导入
    pass
