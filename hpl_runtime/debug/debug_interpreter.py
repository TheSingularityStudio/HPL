"""
HPL 调试解释器模块

扩展标准解释器，增加调试功能：
- 详细的错误诊断
- 执行流程跟踪
- 变量状态监控
- 断点支持（基础版）
"""

import sys
import os
from typing import Optional, Dict, Any, List, Callable

from hpl_runtime.interpreter import main as standard_main
from hpl_runtime.core.parser import HPLParser
from hpl_runtime.core.evaluator import HPLEvaluator
from hpl_runtime.core.models import ImportStatement, HPLObject
from hpl_runtime.modules.loader import set_current_hpl_file
from hpl_runtime.utils.exceptions import (
    HPLError, HPLSyntaxError, HPLRuntimeError, HPLImportError,
    format_error_for_user
)
from hpl_runtime.utils.error_handler import HPLErrorHandler, create_error_handler
from .error_analyzer import ErrorAnalyzer, ExecutionLogger, VariableInspector


class DebugEvaluator(HPLEvaluator):
    """
    支持调试的 Evaluator
    
    扩展标准 HPLEvaluator，增加：
    - 执行流程记录
    - 变量状态捕获
    - 详细的错误上下文
    """
    
    def __init__(self, *args, debug_mode: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug_mode = debug_mode
        self.exec_logger = ExecutionLogger()
        self.var_inspector = VariableInspector()
        self._current_line: Optional[int] = None
        
    def execute_function(self, func, local_scope, func_name=None):
        """执行函数，带调试跟踪"""
        if self.debug_mode and func_name:
            # 记录函数调用
            self.exec_logger.log_function_call(
                func_name, 
                list(local_scope.values()),
                self._current_line
            )
            
        try:
            result = super().execute_function(func, local_scope, func_name)
            
            if self.debug_mode and func_name:
                # 记录函数返回
                self.exec_logger.log_function_return(
                    func_name,
                    result,
                    self._current_line
                )
                
            return result
            
        except HPLRuntimeError as e:
            # 增强错误信息
            if not e.call_stack and self.call_stack:
                e.call_stack = self.call_stack.copy()
            raise
    
    def execute_statement(self, stmt, local_scope):
        """执行语句，带调试跟踪"""
        # 获取行号（如果语句有 line 属性）
        line = getattr(stmt, 'line', None)
        if line:
            self._current_line = line
            
        if self.debug_mode:
            # 捕获变量状态
            self.var_inspector.capture(local_scope, self.global_scope, line)
            
            # 记录特定类型的语句
            stmt_type = type(stmt).__name__
            if 'Assign' in stmt_type:
                var_name = getattr(stmt, 'var_name', 'unknown')
                self.exec_logger.log_variable_assign(var_name, 'pending', line)
            elif 'Catch' in stmt_type:
                self.exec_logger.log_error_catch('catch block', line)
        
        return super().execute_statement(stmt, local_scope)
    
    def _lookup_variable(self, name, local_scope, line=None, column=None):
        """变量查找，带调试"""
        try:
            return super()._lookup_variable(name, local_scope, line, column)
        except Exception as e:
            if self.debug_mode:
                # 记录变量查找失败
                self.exec_logger.log(
                    'VARIABLE_LOOKUP_FAILED',
                    {'variable': name, 'error': str(e)},
                    line
                )
            raise


class DebugInterpreter:
    """
    HPL 调试解释器
    
    提供增强的错误诊断和调试功能
    """
    
    def __init__(self, debug_mode: bool = True, verbose: bool = False):
        self.debug_mode = debug_mode
        self.verbose = verbose
        self.analyzer = ErrorAnalyzer()
        self.last_result: Optional[Any] = None
        self.last_error: Optional[Exception] = None
        self.source_code: Optional[str] = None
        
    def run(self, hpl_file: str, 
            call_target: str = None, 
            call_args: List[Any] = None) -> Dict[str, Any]:
        """
        运行 HPL 文件，带完整调试支持
        
        Args:
            hpl_file: HPL 文件路径
            call_target: 要调用的函数名（可选）
            call_args: 调用参数（可选）
            
        Returns:
            包含执行结果和调试信息的字典
        """
        if not os.path.exists(hpl_file):
            raise FileNotFoundError(f"HPL file not found: {hpl_file}")
            
        # 设置当前文件路径
        set_current_hpl_file(hpl_file)
        
        result = {
            'success': False,
            'file': hpl_file,
            'error': None,
            'debug_info': {}
        }
        
        parser = None
        evaluator = None
        
        # 创建错误处理器
        handler = create_error_handler(hpl_file, debug_mode=self.debug_mode)
        
        try:
            # 读取源代码
            with open(hpl_file, 'r', encoding='utf-8') as f:
                self.source_code = f.read()
                handler.source_code = self.source_code
                
            # 解析
            parser = HPLParser(hpl_file)
            handler.set_parser(parser)
            
            classes, objects, functions, main_func, _, _, imports = parser.parse()
            
            # 检查 main 函数
            if main_func is None:
                raise HPLRuntimeError("No main function found in the HPL file")
            
            # 创建调试 evaluator
            evaluator = DebugEvaluator(
                classes, objects, functions, main_func,
                call_target, call_args,
                debug_mode=self.debug_mode
            )
            handler.set_evaluator(evaluator)
            
            # 处理导入
            for imp in imports:
                module_name = imp['module']
                alias = imp['alias'] or module_name
                import_stmt = ImportStatement(module_name, alias)
                evaluator.execute_import(import_stmt, evaluator.global_scope)
            
            # 实例化对象
            for obj_name, obj in list(evaluator.objects.items()):
                if isinstance(obj, HPLObject) and '__init_args__' in obj.attributes:
                    init_args = obj.attributes.pop('__init_args__')
                    parsed_args = self._parse_init_args(init_args)
                    evaluator._call_constructor(obj, parsed_args)
            
            # 执行
            evaluator.run()
            
            result['success'] = True
            result['debug_info'] = {
                'execution_trace': evaluator.exec_logger.get_trace(),
                'variable_snapshots': evaluator.var_inspector.snapshots,
                'call_stack_history': evaluator.call_stack
            }
            
        except HPLSyntaxError as e:
            self.last_error = e
            # 使用错误处理器生成报告
            report = handler.handle(e, exit_on_error=False)
            context = self.analyzer.analyze_error(
                e, 
                source_code=getattr(parser, 'source_code', self.source_code)
            )
            result['error'] = e
            result['debug_info'] = {
                'error_report': report,
                'error_context': context.to_dict(),
                'report': self.analyzer.generate_report(context)
            }
            
        except HPLRuntimeError as e:
            self.last_error = e
            # 使用错误处理器
            report = handler.handle(e, exit_on_error=False)
            
            context = self.analyzer.analyze_error(
                e,
                source_code=self.source_code,
                evaluator=evaluator
            )
            result['error'] = e
            result['debug_info'] = {
                'error_report': report,
                'error_context': context.to_dict(),
                'report': self.analyzer.generate_report(context),
                'execution_trace': evaluator.exec_logger.get_trace() if evaluator else []
            }
            
        except HPLImportError as e:
            self.last_error = e
            report = handler.handle(e, exit_on_error=False)
            context = self.analyzer.analyze_error(e, source_code=self.source_code)
            result['error'] = e
            result['debug_info'] = {
                'error_report': report,
                'error_context': context.to_dict(),
                'report': self.analyzer.generate_report(context)
            }
            
        except HPLError as e:
            self.last_error = e
            report = handler.handle(e, exit_on_error=False)
            context = self.analyzer.analyze_error(e, source_code=self.source_code)
            result['error'] = e
            result['debug_info'] = {
                'error_report': report,
                'error_context': context.to_dict(),
                'report': self.analyzer.generate_report(context)
            }
            
        except Exception as e:
            self.last_error = e
            # 使用错误处理器处理未预期错误
            handler.handle_unexpected_error(e, hpl_file)

        
        self.last_result = result
        return result
    
    def _parse_init_args(self, args: List[str]) -> List[Any]:
        """解析构造函数参数"""
        parsed = []
        for arg in args:
            arg = arg.strip()
            # 尝试解析为整数
            try:
                parsed.append(int(arg))
            except ValueError:
                # 尝试解析为浮点数
                try:
                    parsed.append(float(arg))
                except ValueError:
                    # 作为字符串处理
                    if (arg.startswith('"') and arg.endswith('"')) or \
                       (arg.startswith("'") and arg.endswith("'")):
                        parsed.append(arg[1:-1])
                    else:
                        parsed.append(arg)
        return parsed
    
    def print_debug_report(self):
        """打印调试报告"""
        if self.last_result and self.last_result.get('debug_info', {}).get('report'):
            print(self.last_result['debug_info']['report'])
        elif self.last_error:
            print(f"Last error: {self.last_error}")
        else:
            print("No debug information available")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        return self.analyzer.get_summary()
    
    def clear(self):
        """清除调试状态"""
        self.analyzer.clear()
        self.last_result = None
        self.last_error = None
        self.source_code = None


def debug_main():
    """
    调试模式的主入口
    
    用法: python -m hpl_runtime.debug <hpl_file>
    """
    if len(sys.argv) < 2:
        print("Usage: python -m hpl_runtime.debug <hpl_file>")
        print("       python -m hpl_runtime.debug <hpl_file> --verbose")
        sys.exit(1)
    
    hpl_file = sys.argv[1]
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    # 启用调试模式
    os.environ['HPL_DEBUG'] = '1'
    
    interpreter = DebugInterpreter(debug_mode=True, verbose=verbose)
    result = interpreter.run(hpl_file)
    
    if result['success']:
        print(f"[OK] Successfully executed: {hpl_file}")
        if verbose and result['debug_info'].get('execution_trace'):
            print("\nExecution trace:")
            for entry in result['debug_info']['execution_trace'][-10:]:
                print(f"  {entry['type']}: {entry['details']}")
    else:
        print(f"[ERROR] Execution failed: {hpl_file}")
        print("\n" + "=" * 60)
        print("DEBUG REPORT")
        print("=" * 60)
        interpreter.print_debug_report()
        sys.exit(1)


if __name__ == "__main__":
    debug_main()
