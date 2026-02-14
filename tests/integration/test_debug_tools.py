#!/usr/bin/env python3
"""
HPL 调试工具模块单元测试

测试 debug_interpreter.py 和 error_analyzer.py 中的调试功能
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 导入被测试的模块
from hpl_runtime.debug.error_analyzer import (
    ErrorContext, ExecutionLogger, VariableInspector,
    CallStackAnalyzer, ErrorTracer, ErrorAnalyzer
)
from hpl_runtime.debug.debug_interpreter import DebugEvaluator, DebugInterpreter
from hpl_runtime.utils.exceptions import HPLRuntimeError, HPLSyntaxError


class TestErrorContext(unittest.TestCase):
    """测试错误上下文数据类"""

    def test_error_context_creation(self):
        """测试创建错误上下文"""
        error = HPLRuntimeError("Test error", line=10, column=5, file="test.hpl")
        context = ErrorContext(
            error=error,
            error_type="HPLRuntimeError",
            message="Test error",
            line=10,
            column=5,
            file="test.hpl"
        )
        
        self.assertEqual(context.error_type, "HPLRuntimeError")
        self.assertEqual(context.message, "Test error")
        self.assertEqual(context.line, 10)
        self.assertEqual(context.column, 5)
        self.assertEqual(context.file, "test.hpl")

    def test_error_context_to_dict(self):
        """测试转换为字典"""
        error = HPLRuntimeError("Test error")
        context = ErrorContext(
            error=error,
            error_type="HPLRuntimeError",
            message="Test error",
            line=10,
            file="test.hpl"
        )
        
        result = context.to_dict()
        self.assertEqual(result['error_type'], "HPLRuntimeError")
        self.assertEqual(result['message'], "Test error")
        self.assertEqual(result['location']['line'], 10)
        self.assertEqual(result['location']['file'], "test.hpl")


class TestExecutionLogger(unittest.TestCase):
    """测试执行日志记录器"""

    def setUp(self):
        self.logger = ExecutionLogger()

    def test_log_basic(self):
        """测试基本日志记录"""
        self.logger.log('TEST_EVENT', {'key': 'value'}, line=10)
        trace = self.logger.get_trace()
        
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]['type'], 'TEST_EVENT')
        self.assertEqual(trace[0]['line'], 10)
        self.assertEqual(trace[0]['details']['key'], 'value')

    def test_log_function_call(self):
        """测试记录函数调用"""
        self.logger.log_function_call('add', [5, 3], line=20)
        trace = self.logger.get_trace()
        
        self.assertEqual(trace[0]['type'], 'FUNCTION_CALL')
        self.assertEqual(trace[0]['details']['function'], 'add')
        self.assertEqual(trace[0]['details']['arguments'], ['5', '3'])

    def test_log_function_return(self):
        """测试记录函数返回"""
        self.logger.log_function_return('add', 8, line=25)
        trace = self.logger.get_trace()
        
        self.assertEqual(trace[0]['type'], 'FUNCTION_RETURN')
        self.assertEqual(trace[0]['details']['value'], '8')

    def test_log_variable_assign(self):
        """测试记录变量赋值"""
        self.logger.log_variable_assign('x', 42, line=15)
        trace = self.logger.get_trace()
        
        self.assertEqual(trace[0]['type'], 'VARIABLE_ASSIGN')
        self.assertEqual(trace[0]['details']['variable'], 'x')

    def test_log_error_catch(self):
        """测试记录错误捕获"""
        self.logger.log_error_catch('RuntimeError', line=30)
        trace = self.logger.get_trace()
        
        self.assertEqual(trace[0]['type'], 'ERROR_CATCH')
        self.assertEqual(trace[0]['details']['error_type'], 'RuntimeError')

    def test_max_entries_limit(self):
        """测试最大条目限制"""
        logger = ExecutionLogger(max_entries=5)
        for i in range(10):
            logger.log('EVENT', {'index': i})
        
        trace = logger.get_trace()
        self.assertEqual(len(trace), 5)

    def test_disable_enable(self):
        """测试禁用和启用"""
        self.logger.disable()
        self.logger.log('EVENT', {})
        self.assertEqual(len(self.logger.get_trace()), 0)
        
        self.logger.enable()
        self.logger.log('EVENT', {})
        self.assertEqual(len(self.logger.get_trace()), 1)

    def test_clear(self):
        """测试清除记录"""
        self.logger.log('EVENT', {})
        self.assertEqual(len(self.logger.get_trace()), 1)
        
        self.logger.clear()
        self.assertEqual(len(self.logger.get_trace()), 0)

    def test_format_trace(self):
        """测试格式化跟踪"""
        self.logger.log_function_call('test', [], line=1)
        formatted = self.logger.format_trace()
        
        self.assertIn("执行流程跟踪", formatted)
        self.assertIn("FUNCTION_CALL", formatted)


class TestVariableInspector(unittest.TestCase):
    """测试变量检查器"""

    def setUp(self):
        self.inspector = VariableInspector()

    def test_capture_basic(self):
        """测试基本变量捕获"""
        local_scope = {'x': 10, 'y': 20}
        snapshot = self.inspector.capture(local_scope, line=5)
        
        self.assertEqual(snapshot['line'], 5)
        self.assertEqual(snapshot['local']['x'], '10')
        self.assertEqual(snapshot['local']['y'], '20')

    def test_capture_with_global(self):
        """测试带全局变量的捕获"""
        local_scope = {'x': 10}
        global_scope = {'g': 100}
        snapshot = self.inspector.capture(local_scope, global_scope, line=10)
        
        self.assertEqual(snapshot['global']['g'], '100')

    def test_format_value_string(self):
        """测试字符串值格式化"""
        result = self.inspector._format_value("hello")
        self.assertEqual(result, '"hello"')

    def test_format_value_list(self):
        """测试列表值格式化"""
        result = self.inspector._format_value([1, 2, 3])
        self.assertEqual(result, '<Array with 3 items>')

    def test_format_value_dict(self):
        """测试字典值格式化"""
        result = self.inspector._format_value({'a': 1, 'b': 2})
        self.assertEqual(result, '<Dictionary with 2 keys>')

    def test_get_last_snapshot(self):
        """测试获取最后一次快照"""
        self.inspector.capture({'x': 1}, line=1)
        self.inspector.capture({'x': 2}, line=2)
        
        last = self.inspector.get_last_snapshot()
        self.assertEqual(last['local']['x'], '2')

    def test_format_variables(self):
        """测试格式化变量"""
        self.inspector.capture({'x': 10, 'y': 20}, line=5)
        formatted = self.inspector.format_variables()
        
        self.assertIn("变量状态", formatted)
        self.assertIn("x = 10", formatted)
        self.assertIn("y = 20", formatted)


class TestCallStackAnalyzer(unittest.TestCase):
    """测试调用栈分析器"""

    def setUp(self):
        self.analyzer = CallStackAnalyzer()

    def test_push_pop_frame(self):
        """测试压入和弹出栈帧"""
        self.analyzer.push_frame('main', 'test.hpl', 10, {'arg': 5})
        self.assertEqual(len(self.analyzer.stack_frames), 1)
        
        frame = self.analyzer.pop_frame()
        self.assertEqual(frame['function'], 'main')
        self.assertEqual(frame['file'], 'test.hpl')
        self.assertEqual(len(self.analyzer.stack_frames), 0)

    def test_get_current_stack(self):
        """测试获取当前调用栈"""
        self.analyzer.push_frame('func1')
        self.analyzer.push_frame('func2')
        
        stack = self.analyzer.get_current_stack()
        self.assertEqual(len(stack), 2)
        self.assertEqual(stack[0]['function'], 'func1')
        self.assertEqual(stack[1]['function'], 'func2')

    def test_format_stack(self):
        """测试格式化调用栈"""
        self.analyzer.push_frame('main', 'test.hpl', 10)
        self.analyzer.push_frame('add', 'test.hpl', 20, {'x': 5, 'y': 3})
        
        formatted = self.analyzer.format_stack()
        self.assertIn("调用栈", formatted)
        self.assertIn("main", formatted)
        self.assertIn("add", formatted)


class TestErrorTracer(unittest.TestCase):
    """测试错误跟踪器"""

    def setUp(self):
        self.tracer = ErrorTracer()

    def test_trace_error_basic(self):
        """测试基本错误跟踪"""
        error = HPLRuntimeError("Test error", line=10, file="test.hpl")
        context = self.tracer.trace_error(error)
        
        self.assertEqual(context.error_type, "HPLRuntimeError")
        # HPLRuntimeError的message包含完整的错误信息（包括文件和行号）
        self.assertIn("Test error", context.message)
        self.assertEqual(context.line, 10)
        self.assertEqual(context.file, "test.hpl")


    def test_extract_source_snippet(self):
        """测试提取源代码片段"""
        source = "line1\nline2\nline3\nline4\nline5"
        snippet = self.tracer._extract_source_snippet(source, 3)
        
        self.assertIn("line1", snippet)
        self.assertIn("line2", snippet)
        self.assertIn(">>>", snippet)  # 当前行标记
        self.assertIn("line3", snippet)

    def test_add_propagation_step(self):
        """测试添加传播步骤"""
        self.tracer.add_propagation_step("func1", "throw")
        self.tracer.add_propagation_step("func2", "catch")
        
        self.assertEqual(len(self.tracer.propagation_path), 2)

    def test_format_propagation_path(self):
        """测试格式化传播路径"""
        self.tracer.add_propagation_step("main", "call")
        formatted = self.tracer.format_propagation_path()
        
        self.assertIn("错误传播路径", formatted)
        self.assertIn("main", formatted)


class TestErrorAnalyzer(unittest.TestCase):
    """测试错误分析器主类"""

    def setUp(self):
        self.analyzer = ErrorAnalyzer()

    def test_analyze_error(self):
        """测试错误分析"""
        error = HPLRuntimeError("Test error", line=10, file="test.hpl")
        context = self.analyzer.analyze_error(error)
        
        self.assertEqual(len(self.analyzer.contexts), 1)
        self.assertEqual(context.error_type, "HPLRuntimeError")

    def test_generate_report(self):
        """测试生成报告"""
        error = HPLRuntimeError("Test error", line=10, file="test.hpl")
        context = self.analyzer.analyze_error(error)
        report = self.analyzer.generate_report(context)
        
        self.assertIn("错误分析报告", report)
        self.assertIn("HPLRuntimeError", report)
        self.assertIn("Test error", report)

    def test_get_summary(self):
        """测试获取摘要"""
        error1 = HPLRuntimeError("Error 1")
        error2 = HPLSyntaxError("Error 2")
        
        self.analyzer.analyze_error(error1)
        self.analyzer.analyze_error(error2)
        
        summary = self.analyzer.get_summary()
        self.assertEqual(summary['total_errors'], 2)
        self.assertIn('HPLRuntimeError', summary['error_types'])
        self.assertIn('HPLSyntaxError', summary['error_types'])

    def test_clear(self):
        """测试清除数据"""
        error = HPLRuntimeError("Test")
        self.analyzer.analyze_error(error)
        self.assertEqual(len(self.analyzer.contexts), 1)
        
        self.analyzer.clear()
        self.assertEqual(len(self.analyzer.contexts), 0)


class TestDebugEvaluator(unittest.TestCase):
    """测试调试执行器"""

    def setUp(self):
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_debug_evaluator_creation(self):
        """测试创建调试执行器"""
        evaluator = DebugEvaluator(
            self.classes, self.objects, self.functions, self.main_func,
            debug_mode=True
        )
        
        self.assertTrue(evaluator.debug_mode)
        self.assertIsNotNone(evaluator.exec_logger)
        self.assertIsNotNone(evaluator.var_inspector)

    def test_debug_evaluator_disabled(self):
        """测试禁用调试模式"""
        evaluator = DebugEvaluator(
            self.classes, self.objects, self.functions, self.main_func,
            debug_mode=False
        )
        
        self.assertFalse(evaluator.debug_mode)


class TestDebugInterpreter(unittest.TestCase):
    """测试调试解释器"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.hpl")
        
        # 创建一个简单的测试HPL文件
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write('''main: () => {
  x = 5
  echo x
}''')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_debug_interpreter_creation(self):
        """测试创建调试解释器"""
        interpreter = DebugInterpreter(debug_mode=True, verbose=False)
        self.assertTrue(interpreter.debug_mode)
        self.assertFalse(interpreter.verbose)

    def test_run_success(self):
        """测试成功运行"""
        interpreter = DebugInterpreter(debug_mode=True)
        result = interpreter.run(self.test_file)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['file'], self.test_file)
        self.assertIn('debug_info', result)

    def test_run_file_not_found(self):
        """测试文件不存在"""
        interpreter = DebugInterpreter()
        
        with self.assertRaises(FileNotFoundError):
            interpreter.run("nonexistent.hpl")

    def test_parse_init_args(self):
        """测试解析构造函数参数"""
        interpreter = DebugInterpreter()
        
        # 测试整数
        result = interpreter._parse_init_args(['42'])
        self.assertEqual(result, [42])
        
        # 测试浮点数
        result = interpreter._parse_init_args(['3.14'])
        self.assertEqual(result, [3.14])
        
        # 测试字符串
        result = interpreter._parse_init_args(['"hello"'])
        self.assertEqual(result, ['hello'])

    def test_clear(self):
        """测试清除状态"""
        interpreter = DebugInterpreter()
        interpreter.run(self.test_file)
        
        interpreter.clear()
        self.assertIsNone(interpreter.last_result)
        self.assertIsNone(interpreter.last_error)
        self.assertIsNone(interpreter.source_code)

    def test_get_error_summary_no_errors(self):
        """测试无错误时的摘要"""
        interpreter = DebugInterpreter()
        summary = interpreter.get_error_summary()
        
        self.assertEqual(summary['total_errors'], 0)


if __name__ == '__main__':
    unittest.main()
