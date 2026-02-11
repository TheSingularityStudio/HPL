"""
HPL 错误分析器模块

提供详细的错误诊断和分析功能，包括：
- 错误传播路径跟踪
- 调用栈分析
- 变量状态检查
- 执行流程记录
"""

import sys
import traceback
import inspect
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

try:
    from hpl_runtime.utils.exceptions import (
        HPLError, HPLSyntaxError, HPLRuntimeError, 
        HPLControlFlowException, format_error_for_user
    )
    from hpl_runtime.core.evaluator import HPLEvaluator
    from hpl_runtime.core.models import HPLFunction, HPLObject
except ImportError:
    from hpl_runtime.utils.exceptions import (
        HPLError, HPLSyntaxError, HPLRuntimeError,
        HPLControlFlowException, format_error_for_user
    )
    from hpl_runtime.core.evaluator import HPLEvaluator
    from hpl_runtime.core.models import HPLFunction, HPLObject


@dataclass
class ErrorContext:
    """错误上下文信息"""
    error: Exception
    error_type: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    file: Optional[str] = None
    call_stack: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    source_snippet: Optional[str] = None
    execution_trace: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_type': self.error_type,
            'message': self.message,
            'location': {
                'file': self.file,
                'line': self.line,
                'column': self.column
            },
            'call_stack': self.call_stack,
            'variables': {k: str(v) for k, v in self.variables.items()},
            'source_snippet': self.source_snippet,
            'execution_trace': self.execution_trace,
            'timestamp': self.timestamp
        }


class ExecutionLogger:
    """执行流程记录器"""
    
    def __init__(self, max_entries: int = 1000):
        self.trace: List[Dict[str, Any]] = []
        self.max_entries = max_entries
        self._enabled = True
        
    def enable(self):
        self._enabled = True
        
    def disable(self):
        self._enabled = False
        
    def log(self, event_type: str, details: Dict[str, Any], line: int = None):
        """记录执行事件"""
        if not self._enabled:
            return
            
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'line': line,
            'details': details
        }
        
        self.trace.append(entry)
        
        # 限制条目数量
        if len(self.trace) > self.max_entries:
            self.trace.pop(0)
            
    def log_function_call(self, func_name: str, args: List[Any], line: int = None):
        """记录函数调用"""
        self.log('FUNCTION_CALL', {
            'function': func_name,
            'arguments': [str(arg) for arg in args]
        }, line)
        
    def log_function_return(self, func_name: str, value: Any, line: int = None):
        """记录函数返回"""
        self.log('FUNCTION_RETURN', {
            'function': func_name,
            'value': str(value)
        }, line)
        
    def log_variable_assign(self, var_name: str, value: Any, line: int = None):
        """记录变量赋值"""
        self.log('VARIABLE_ASSIGN', {
            'variable': var_name,
            'value': str(value)
        }, line)
        
    def log_error_catch(self, error_type: str, line: int = None):
        """记录错误捕获"""
        self.log('ERROR_CATCH', {
            'error_type': error_type
        }, line)
        
    def get_trace(self, last_n: int = None) -> List[Dict[str, Any]]:
        """获取执行跟踪记录"""
        if last_n:
            return self.trace[-last_n:]
        return self.trace.copy()
        
    def clear(self):
        """清除记录"""
        self.trace.clear()
        
    def format_trace(self) -> str:
        """格式化跟踪记录为字符串"""
        lines = ["=== 执行流程跟踪 ==="]
        for i, entry in enumerate(self.trace, 1):
            line_info = f"Line {entry['line']}" if entry['line'] else "Unknown line"
            lines.append(f"{i}. [{entry['type']}] {line_info}")
            for key, value in entry['details'].items():
                lines.append(f"   {key}: {value}")
        return '\n'.join(lines)


class VariableInspector:
    """变量状态检查器"""
    
    def __init__(self):
        self.snapshots: List[Dict[str, Any]] = []
        
    def capture(self, local_scope: Dict[str, Any], 
                global_scope: Dict[str, Any] = None,
                line: int = None) -> Dict[str, Any]:
        """捕获当前变量状态"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'line': line,
            'local': {},
            'global': {},
            'objects': {}
        }
        
        # 捕获局部变量
        for name, value in local_scope.items():
            snapshot['local'][name] = self._format_value(value)
            
        # 捕获全局变量
        if global_scope:
            for name, value in global_scope.items():
                snapshot['global'][name] = self._format_value(value)
                
        self.snapshots.append(snapshot)
        return snapshot
    
    def _format_value(self, value: Any) -> str:
        """格式化变量值"""
        if isinstance(value, HPLObject):
            return f"<Object {value.name} of class {value.hpl_class.name}>"
        elif isinstance(value, HPLFunction):
            return f"<Function with {len(value.params)} params>"
        elif isinstance(value, list):
            return f"<Array with {len(value)} items>"
        elif isinstance(value, dict):
            return f"<Dictionary with {len(value)} keys>"
        elif isinstance(value, str):
            return f'"{value}"'
        else:
            return str(value)
    
    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """获取最后一次快照"""
        if self.snapshots:
            return self.snapshots[-1]
        return None
    
    def format_variables(self, snapshot: Dict[str, Any] = None) -> str:
        """格式化变量状态为字符串"""
        if snapshot is None:
            snapshot = self.get_last_snapshot()
            
        if not snapshot:
            return "No variable snapshot available"
            
        lines = ["=== 变量状态 ==="]
        
        if snapshot.get('local'):
            lines.append("局部变量:")
            for name, value in snapshot['local'].items():
                lines.append(f"  {name} = {value}")
                
        if snapshot.get('global'):
            lines.append("全局变量:")
            for name, value in snapshot['global'].items():
                lines.append(f"  {name} = {value}")
                
        return '\n'.join(lines)


class CallStackAnalyzer:
    """调用栈分析器"""
    
    def __init__(self):
        self.stack_frames: List[Dict[str, Any]] = []
        
    def push_frame(self, func_name: str, file: str = None, 
                   line: int = None, args: Dict[str, Any] = None):
        """压入调用栈帧"""
        frame = {
            'function': func_name,
            'file': file,
            'line': line,
            'arguments': args or {},
            'timestamp': datetime.now().isoformat()
        }
        self.stack_frames.append(frame)
        
    def pop_frame(self) -> Optional[Dict[str, Any]]:
        """弹出调用栈帧"""
        if self.stack_frames:
            return self.stack_frames.pop()
        return None
    
    def get_current_stack(self) -> List[Dict[str, Any]]:
        """获取当前调用栈"""
        return self.stack_frames.copy()
    
    def format_stack(self, stack: List[Dict[str, Any]] = None) -> str:
        """格式化调用栈为字符串"""
        if stack is None:
            stack = self.stack_frames
            
        if not stack:
            return "Call stack is empty"
            
        lines = ["=== 调用栈 (最近调用在前) ==="]
        for i, frame in enumerate(reversed(stack), 1):
            func_info = frame['function']
            location = ""
            if frame.get('file'):
                location += f" in {frame['file']}"
            if frame.get('line'):
                location += f":{frame['line']}"
                
            lines.append(f"{i}. {func_info}{location}")
            
            if frame.get('arguments'):
                for arg_name, arg_value in frame['arguments'].items():
                    lines.append(f"   参数 {arg_name} = {arg_value}")
                    
        return '\n'.join(lines)


class ErrorTracer:
    """错误传播跟踪器"""
    
    def __init__(self):
        self.propagation_path: List[Dict[str, Any]] = []
        self.original_error: Optional[Exception] = None
        
    def trace_error(self, error: Exception, 
                    evaluator: HPLEvaluator = None,
                    source_code: str = None) -> ErrorContext:
        """跟踪并分析错误"""
        self.original_error = error
        
        # 创建错误上下文
        context = ErrorContext(
            error=error,
            error_type=type(error).__name__,
            message=str(error)
        )
        
        # 提取 HPL 错误信息
        if isinstance(error, HPLError):
            context.line = error.line
            context.column = error.column
            context.file = error.file
            
            if isinstance(error, HPLRuntimeError):
                context.call_stack = error.call_stack.copy()
                
        # 获取源代码片段
        if source_code and context.line:
            context.source_snippet = self._extract_source_snippet(
                source_code, context.line, context.column
            )
            
        # 如果提供了 evaluator，获取当前状态
        if evaluator:
            context.variables = self._capture_evaluator_state(evaluator)
            
        return context
    
    def _extract_source_snippet(self, source_code: str, 
                                line: int, column: int = None,
                                context_lines: int = 3) -> str:
        """
        提取源代码片段
        
        特性：
        - 动态行号宽度，适应大文件
        - 准确的列位置指示器
        - 处理长行截断
        - 语法高亮错误行
        - 更好的边界处理
        """
        if not source_code or not isinstance(source_code, str):
            return None
            
        lines = source_code.split('\n')
        total_lines = len(lines)
        
        # 验证行号范围
        if not isinstance(line, int) or line < 1:
            return f"    1    | [无法定位: 无效行号 {line}]"
        
        # 处理行号超出范围的情况
        if line > total_lines:
            return f"    {total_lines:4d} | [错误发生在文件结束后，行号: {line}]"
            
        # 计算上下文范围
        start = max(0, line - context_lines - 1)
        end = min(total_lines, line + context_lines)
        
        # 动态计算行号宽度
        line_num_width = len(str(total_lines))
        
        result = []
        result.append(f"{'─' * (line_num_width + 10)}")
        
        for i in range(start, end):
            line_num = i + 1
            is_error_line = line_num == line
            line_content = lines[i]
            
            # 处理空行显示
            display_content = line_content if line_content.strip() else "[空行]"
            
            # 截断超长行（超过80字符）
            max_line_length = 80
            if len(display_content) > max_line_length:
                display_content = display_content[:max_line_length - 3] + "..."
            
            # 构建前缀：错误行用 >>> 标记，其他用空格
            prefix = ">>> " if is_error_line else "    "
            
            # 格式化行号，右对齐
            line_num_str = f"{line_num:{line_num_width}d}"
            
            # 错误行添加高亮标记
            if is_error_line:
                result.append(f"{prefix}{line_num_str} │ {display_content}")
            else:
                result.append(f"{prefix}{line_num_str} │ {display_content}")
            
            # 添加列位置指示器（仅对错误行）
            if is_error_line and column is not None and isinstance(column, int):
                if column >= 0:
                    # 计算指示器位置：前缀(4) + 行号(line_num_width) + 分隔符(3) = 7 + line_num_width
                    base_offset = 4 + line_num_width + 3
                    # 调整列位置，考虑中文字符宽度
                    adjusted_column = self._calculate_visual_column(line_content, column)
                    indicator_pos = base_offset + adjusted_column
                    
                    # 确保指示器不会超出范围
                    if indicator_pos < base_offset:
                        indicator_pos = base_offset
                    
                    indicator_line = " " * (base_offset - 1) + "│" + " " * adjusted_column + "▲"
                    result.append(indicator_line)
                    
                    # 添加列号提示
                    if column > 0:
                        result.append(f"{' ' * (base_offset - 1)}│ [列 {column}]")
        
        result.append(f"{'─' * (line_num_width + 10)}")
        return '\n'.join(result)
    
    def _calculate_visual_column(self, line: str, byte_column: int) -> int:
        """
        计算视觉列位置，正确处理中文字符和特殊字符
        
        Args:
            line: 行内容
            byte_column: 字节列位置
            
        Returns:
            视觉列位置（考虑字符宽度）
        """
        if not line or byte_column <= 0:
            return 0
            
        visual_col = 0
        char_count = 0
        
        for char in line:
            if char_count >= byte_column:
                break
            # 中文字符和全角字符占2个视觉宽度
            if ord(char) > 127 or char in '，。！？；：""''（）【】《》':
                visual_col += 2
            else:
                visual_col += 1
            char_count += 1
            
        return visual_col

    
    def _capture_evaluator_state(self, evaluator: HPLEvaluator) -> Dict[str, Any]:
        """捕获 evaluator 的当前状态"""
        state = {
            'call_stack_depth': len(evaluator.call_stack),
            'call_stack': evaluator.call_stack.copy(),
            'global_objects': list(evaluator.global_scope.keys()),
            'imported_modules': list(evaluator.imported_modules.keys())
        }
        return state
    
    def add_propagation_step(self, location: str, action: str):
        """添加错误传播步骤"""
        self.propagation_path.append({
            'location': location,
            'action': action,
            'timestamp': datetime.now().isoformat()
        })
    
    def format_propagation_path(self) -> str:
        """格式化错误传播路径"""
        if not self.propagation_path:
            return "No propagation path recorded"
            
        lines = ["=== 错误传播路径 ==="]
        for i, step in enumerate(self.propagation_path, 1):
            lines.append(f"{i}. [{step['location']}] {step['action']}")
        return '\n'.join(lines)


class ErrorAnalyzer:
    """
    HPL 错误分析器主类
    
    整合所有调试功能，提供统一的错误分析接口
    """
    
    def __init__(self):
        self.tracer = ErrorTracer()
        self.stack_analyzer = CallStackAnalyzer()
        self.var_inspector = VariableInspector()
        self.exec_logger = ExecutionLogger()
        self.contexts: List[ErrorContext] = []
        
    def analyze_error(self, error: Exception,
                     source_code: str = None,
                     evaluator: HPLEvaluator = None) -> ErrorContext:
        """
        分析错误并生成详细报告
        
        Args:
            error: 发生的异常
            source_code: 源代码字符串（可选）
            evaluator: HPLEvaluator 实例（可选）
            
        Returns:
            ErrorContext 包含详细的错误信息
        """
        # 跟踪错误
        context = self.tracer.trace_error(error, evaluator, source_code)
        
        # 如果提供了 evaluator，捕获变量状态
        if evaluator:
            self.var_inspector.capture(
                evaluator.global_scope,
                line=context.line
            )
            
        self.contexts.append(context)
        return context
    
    def generate_report(self, context: ErrorContext = None,
                       include_traceback: bool = True) -> str:
        """
        生成完整的错误分析报告
        
        Args:
            context: 错误上下文（默认使用最后一个）
            include_traceback: 是否包含 Python traceback
            
        Returns:
            格式化的错误报告字符串
        """
        if context is None:
            if not self.contexts:
                return "No errors analyzed yet"
            context = self.contexts[-1]
            
        lines = []
        lines.append("=" * 60)
        lines.append("HPL 错误分析报告")
        lines.append("=" * 60)
        lines.append("")
        
        # 基本信息
        lines.append(f"错误类型: {context.error_type}")
        lines.append(f"错误消息: {context.message}")
        lines.append(f"发生时间: {context.timestamp}")
        lines.append("")
        
        # 位置信息
        if context.file or context.line:
            lines.append("-" * 40)
            lines.append("位置信息:")
            if context.file:
                lines.append(f"  文件: {context.file}")
            if context.line:
                lines.append(f"  行号: {context.line}")
            if context.column:
                lines.append(f"  列号: {context.column}")
            lines.append("")
        
        # 源代码片段
        if context.source_snippet:
            lines.append("-" * 40)
            lines.append("源代码片段:")
            lines.append(context.source_snippet)
            lines.append("")
        
        # 调用栈
        if context.call_stack:
            lines.append("-" * 40)
            lines.append(self.stack_analyzer.format_stack([
                {'function': frame} for frame in context.call_stack
            ]))
            lines.append("")
        
        # 变量状态
        if context.variables:
            lines.append("-" * 40)
            lines.append("运行时状态:")
            for key, value in context.variables.items():
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        # 执行流程
        exec_trace = self.exec_logger.format_trace()
        if exec_trace != "=== 执行流程跟踪 ===":
            lines.append("-" * 40)
            lines.append(exec_trace)
            lines.append("")
        
        # Python traceback（调试模式）
        if include_traceback and not isinstance(context.error, HPLControlFlowException):
            lines.append("-" * 40)
            lines.append("Python Traceback (用于调试):")
            tb_lines = traceback.format_exception(
                type(context.error), 
                context.error, 
                context.error.__traceback__
            )
            lines.extend(tb_lines)
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("报告结束")
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def print_report(self, context: ErrorContext = None):
        """打印错误报告"""
        print(self.generate_report(context))
        
    def get_summary(self) -> Dict[str, Any]:
        """获取错误分析摘要"""
        if not self.contexts:
            return {'total_errors': 0}
            
        error_types = {}
        for ctx in self.contexts:
            error_types[ctx.error_type] = error_types.get(ctx.error_type, 0) + 1
            
        return {
            'total_errors': len(self.contexts),
            'error_types': error_types,
            'files_affected': list(set(
                ctx.file for ctx in self.contexts if ctx.file
            )),
            'last_error_time': self.contexts[-1].timestamp if self.contexts else None
        }
    
    def clear(self):
        """清除所有分析数据"""
        self.contexts.clear()
        self.tracer = ErrorTracer()
        self.stack_analyzer = CallStackAnalyzer()
        self.var_inspector = VariableInspector()
        self.exec_logger = ExecutionLogger()
