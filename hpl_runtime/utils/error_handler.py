"""
HPL 统一错误处理模块

该模块提供统一的错误处理中间件，简化 interpreter 和 debug_interpreter 的错误处理逻辑。

关键类：
- HPLErrorHandler: 统一的错误处理中间件

主要功能：
- 统一处理所有 HPL 错误类型
- 自动增强错误上下文
- 生成用户友好的错误报告
- 支持调试模式
- 集成智能错误建议
"""

import sys
import os

from hpl_runtime.utils.exceptions import (
    HPLError, HPLSyntaxError, HPLRuntimeError, HPLImportError,
    format_error_for_user, format_error_with_suggestions
)
from hpl_runtime.utils.error_suggestions import ErrorSuggestionEngine


class HPLErrorHandler:
    """
    统一的错误处理中间件
    
    简化错误处理流程，提供一致的错误报告格式。
    """
    
    def __init__(self, source_code=None, debug_mode=False, hpl_file=None, 
                 enable_suggestions=True):
        """
        初始化错误处理器
        
        Args:
            source_code: 源代码字符串（用于显示上下文）
            debug_mode: 是否启用调试模式
            hpl_file: 当前 HPL 文件路径
            enable_suggestions: 是否启用智能错误建议
        """
        self.source_code = source_code
        self.debug_mode = debug_mode
        self.hpl_file = hpl_file
        self.parser = None
        self.evaluator = None
        self.enable_suggestions = enable_suggestions
        self.suggestion_engine = None
        
        # 初始化建议引擎
        if enable_suggestions:
            self.suggestion_engine = ErrorSuggestionEngine()

    
    def set_parser(self, parser):
        """设置解析器引用（用于获取源代码）"""
        self.parser = parser
    
    def set_evaluator(self, evaluator):
        """设置执行器引用（用于获取调用栈）"""
        self.evaluator = evaluator
        # 更新建议引擎的 evaluator 引用
        if self.suggestion_engine:
            self.suggestion_engine.evaluator = evaluator
    
    def update_scope(self, global_scope=None, local_scope=None):
        """
        更新作用域信息用于建议引擎
        
        Args:
            global_scope: 全局变量作用域
            local_scope: 局部变量作用域
        """
        if self.suggestion_engine:
            self.suggestion_engine.set_scopes(
                global_scope or {},
                local_scope or {}
            )

    
    def handle(self, error, exit_on_error=True, local_scope=None):
        """
        统一处理错误

        Args:
            error: 异常对象
            exit_on_error: 是否退出程序（默认为 True）
            local_scope: 当前局部作用域（用于智能建议）

        Returns:
            格式化的错误字符串（如果不退出）
        """
        # 获取源代码
        source = self._get_source_code()

        # 更新作用域信息（如果提供）
        if local_scope and self.suggestion_engine:
            self.suggestion_engine.local_scope = local_scope

        # 生成错误报告（使用智能建议）
        if self.enable_suggestions and self.suggestion_engine:
            # 使用增强的建议引擎分析
            analysis = self.suggestion_engine.analyze_error(error, local_scope)
            report = self._format_error_with_analysis(error, source, analysis)
        else:
            report = format_error_for_user(error, source)

        if exit_on_error:
            print(report)
            sys.exit(1)
        else:
            return report


    
    def handle_syntax_error(self, error, parser=None):
        """
        专门处理语法错误
        
        Args:
            error: HPLSyntaxError 实例
            parser: 可选的解析器实例
        """
        # 优先使用传入的解析器
        if parser:
            self.set_parser(parser)
        
        source = self._get_source_code()
        print(format_error_for_user(error, source))
        sys.exit(1)
    
    def handle_yaml_error(self, error, hpl_file=None):
        """
        处理 YAML 解析错误
        
        Args:
            error: YAML 解析异常
            hpl_file: HPL 文件路径
        """
        # 尝试获取错误位置
        line = getattr(error, 'problem_mark', None)
        line_num = line.line + 1 if line else None
        col_num = line.column if line else None
        
        syntax_error = HPLSyntaxError(
            f"YAML syntax error: {str(error)}",
            line=line_num,
            column=col_num,
            file=hpl_file or self.hpl_file
        )
        
        self.handle_syntax_error(syntax_error)
    
    def handle_unexpected_error(self, error, hpl_file=None):
        """
        处理未预期的内部错误
        
        Args:
            error: 未捕获的异常
            hpl_file: HPL 文件路径
        """
        import traceback
        
        # 包装为 HPLRuntimeError
        wrapped = HPLRuntimeError(
            f"Internal error: {type(error).__name__}: {str(error)}",
            file=hpl_file or self.hpl_file,
            error_key='RUNTIME_INTERNAL'
        )
        
        # 生成错误报告
        report = format_error_for_user(wrapped, self.source_code)
        print(report)
        
        # 在调试模式下显示完整 traceback
        if self.debug_mode or os.environ.get('HPL_DEBUG'):
            print("\n--- Full traceback ---")
            traceback.print_exc()
        
        sys.exit(1)
    
    def handle_file_not_found(self, error):
        """
        处理文件未找到错误
        
        Args:
            error: FileNotFoundError 实例
        """
        print(f"[ERROR] File not found: {error.filename}")
        sys.exit(1)
    
    def _get_source_code(self):
        """获取源代码（优先使用 parser 的源代码）"""
        if self.parser and self.parser.source_code:
            return self.parser.source_code
        return self.source_code
    
    def _format_error_with_analysis(self, error, source, analysis):
        """
        格式化错误信息并整合智能建议分析结果
        
        Args:
            error: 错误对象
            source: 源代码字符串
            analysis: 建议引擎的分析结果字典
        
        Returns:
            格式化后的错误字符串
        """
        # 获取基础错误信息
        result = format_error_for_user(error, source)
        
        # 添加智能建议
        if analysis.get('suggestions'):
            result += "\n\n   [TIP] "

            for i, suggestion in enumerate(analysis['suggestions'], 1):
                # 处理多行建议
                lines = suggestion.split('\n')
                result += f"\n      {i}. {lines[0]}"
                for line in lines[1:]:
                    result += f"\n         {line}"
        
        # 添加快速修复代码
        if analysis.get('quick_fix'):
            result += f"\n\n   [FIX] \n   ```\n   {analysis['quick_fix']}\n   ```"

        
        return result


def create_error_handler(hpl_file, debug_mode=False, enable_suggestions=True):

    """
    创建错误处理器的工厂函数
    
    Args:
        hpl_file: HPL 文件路径
        debug_mode: 是否启用调试模式
        enable_suggestions: 是否启用智能错误建议
    
    Returns:
        HPLErrorHandler 实例
    """
    source_code = None
    
    # 尝试读取源代码
    if hpl_file and os.path.exists(hpl_file):
        try:
            with open(hpl_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except (IOError, OSError, PermissionError, UnicodeDecodeError):
            pass

    
    return HPLErrorHandler(
        source_code=source_code,
        debug_mode=debug_mode,
        hpl_file=hpl_file,
        enable_suggestions=enable_suggestions
    )
