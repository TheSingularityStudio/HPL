#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HPL 调试工具使用示例

演示如何使用 hpl_runtime.debug 模块进行错误分析
"""

import sys
import os

# 确保可以导入 hpl_runtime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hpl_runtime.debug import ErrorAnalyzer, DebugInterpreter


def demo_basic_error_analysis():
    """演示基本的错误分析功能"""
    print("=" * 60)
    print("示例 1: 基本错误分析")
    print("=" * 60)
    
    # 创建一个模拟的 HPL 运行时错误
    from hpl_runtime.utils.exceptions import HPLRuntimeError
    
    error = HPLRuntimeError(
        "Undefined variable: 'x'",
        line=10,
        column=5,
        file="test.hpl",
        call_stack=["main()", "foo()", "bar()"]
    )
    
    # 创建分析器
    analyzer = ErrorAnalyzer()
    
    # 分析错误
    source_code = """
main: () => {
    x = 10
    foo()
}

foo: () => {
    bar()
}

bar: () => {
    y = x + 1  # 这里访问了未定义的变量
}
"""
    
    context = analyzer.analyze_error(error, source_code=source_code)
    
    # 生成并打印报告
    report = analyzer.generate_report(context, include_traceback=False)
    print(report)
    print("\n")


def demo_debug_interpreter():
    """演示调试解释器的使用"""
    print("=" * 60)
    print("示例 2: 使用调试解释器运行脚本")
    print("=" * 60)
    
    # 创建调试解释器
    interpreter = DebugInterpreter(debug_mode=True, verbose=True)
    
    # 运行包含错误的脚本
    script_path = os.path.join(os.path.dirname(__file__), "debug_demo.hpl")
    
    if not os.path.exists(script_path):
        print(f"脚本不存在: {script_path}")
        print("创建测试脚本...")
        
        # 创建一个简单的测试脚本
        test_script = '''main: () => {
    items = [1, 2, 3]
    echo(items[5])  # 索引越界错误
}'''
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(test_script)
    
    print(f"运行脚本: {script_path}")
    print("-" * 40)
    
    # 运行脚本
    result = interpreter.run(script_path)
    
    if result['success']:
        print("脚本执行成功！")
        print(f"调试信息: {result['debug_info']}")
    else:
        print("脚本执行失败（预期行为）")
        print("正在生成调试报告...")
        print("-" * 40)
        interpreter.print_debug_report()
    
    print("\n")
    return result


def demo_execution_tracing():
    """演示执行流程跟踪"""
    print("=" * 60)
    print("示例 3: 执行流程跟踪")
    print("=" * 60)
    
    from hpl_runtime.debug import ExecutionLogger
    
    logger = ExecutionLogger()
    
    # 模拟记录一些执行事件
    logger.log_function_call("main", [], line=1)
    logger.log_variable_assign("x", 10, line=2)
    logger.log_function_call("calculate", [10, 20], line=3)
    logger.log_variable_assign("result", 30, line=5)
    logger.log_function_return("calculate", 30, line=6)
    logger.log_function_return("main", None, line=7)
    
    # 格式化输出
    trace_output = logger.format_trace()
    print(trace_output)
    print("\n")


def demo_variable_inspection():
    """演示变量状态检查"""
    print("=" * 60)
    print("示例 4: 变量状态检查")
    print("=" * 60)
    
    from hpl_runtime.debug import VariableInspector
    
    inspector = VariableInspector()
    
    # 模拟局部变量和全局变量
    local_scope = {
        'x': 42,
        'name': 'test',
        'items': [1, 2, 3, 4, 5]
    }
    
    global_scope = {
        'global_config': {'debug': True},
        'version': '1.0.0'
    }
    
    # 捕获变量状态
    snapshot = inspector.capture(local_scope, global_scope, line=10)
    
    # 格式化输出
    print(inspector.format_variables(snapshot))
    print("\n")


def demo_call_stack_analysis():
    """演示调用栈分析"""
    print("=" * 60)
    print("示例 5: 调用栈分析")
    print("=" * 60)
    
    from hpl_runtime.debug import CallStackAnalyzer
    
    analyzer = CallStackAnalyzer()
    
    # 模拟调用栈
    analyzer.push_frame("main()", "test.hpl", 1, {})
    analyzer.push_frame("calculate(x, y)", "test.hpl", 15, {'x': '10', 'y': '20'})
    analyzer.push_frame("helper(n)", "test.hpl", 25, {'n': '30'})
    
    # 格式化输出
    print(analyzer.format_stack())
    print("\n")


def demo_error_tracing():
    """演示错误传播跟踪"""
    print("=" * 60)
    print("示例 6: 错误传播跟踪")
    print("=" * 60)
    
    from hpl_runtime.debug import ErrorTracer
    from hpl_runtime.utils.exceptions import HPLRuntimeError
    
    tracer = ErrorTracer()
    
    # 创建一个错误
    error = HPLRuntimeError(
        "Division by zero",
        line=20,
        column=10,
        file="math.hpl",
        call_stack=["main()", "calculate()", "divide()"]
    )
    
    # 跟踪错误
    source_code = """
main: () => {
    result = calculate(100, 0)
    echo(result)
}

calculate: (a, b) => {
    return divide(a, b)
}

divide: (x, y) => {
    return x / y  # 这里会除零错误
}
"""
    
    context = tracer.trace_error(error, source_code=source_code)
    
    # 添加传播步骤
    tracer.add_propagation_step("divide()", "抛出除零错误")
    tracer.add_propagation_step("calculate()", "未捕获错误，向上传播")
    tracer.add_propagation_step("main()", "未捕获错误，程序终止")
    
    # 输出结果
    print(f"错误类型: {context.error_type}")
    print(f"错误消息: {context.message}")
    print(f"位置: {context.file}:{context.line}:{context.column}")
    print("\n源代码片段:")
    print(context.source_snippet)
    print("\n调用栈:")
    for i, frame in enumerate(context.call_stack, 1):
        print(f"  {i}. {frame}")
    print("\n错误传播路径:")
    print(tracer.format_propagation_path())
    print("\n")


def demo_programmatic_usage():
    """演示程序化使用调试工具"""
    print("=" * 60)
    print("示例 7: 程序化使用 - 批量分析多个错误")
    print("=" * 60)
    
    from hpl_runtime.utils.exceptions import (
        HPLSyntaxError, HPLRuntimeError, HPLTypeError, HPLNameError
    )
    
    analyzer = ErrorAnalyzer()
    
    # 模拟多个错误
    errors = [
        HPLSyntaxError("Unexpected token: '}'", line=5, column=1, file="test1.hpl"),
        HPLRuntimeError("Undefined variable: 'x'", line=10, column=5, file="test2.hpl"),
        HPLTypeError("Cannot add string and number", line=15, column=8, file="test3.hpl"),
        HPLNameError("Function 'foo' not found", line=20, column=3, file="test4.hpl"),
    ]
    
    # 分析所有错误
    for error in errors:
        analyzer.analyze_error(error)
    
    # 获取摘要
    summary = analyzer.get_summary()
    print("错误分析摘要:")
    print(f"  总错误数: {summary['total_errors']}")
    print(f"  错误类型分布:")
    for error_type, count in summary['error_types'].items():
        print(f"    - {error_type}: {count}")
    print(f"  受影响的文件: {', '.join(summary['files_affected'])}")
    print(f"  最后错误时间: {summary['last_error_time']}")
    print("\n")


def main():
    """主函数 - 运行所有示例"""
    print("\n")
    print("=" * 60)
    print("HPL 调试工具使用示例")
    print("=" * 60)
    print("\n")
    
    # 运行所有演示
    demo_basic_error_analysis()
    demo_execution_tracing()
    demo_variable_inspection()
    demo_call_stack_analysis()
    demo_error_tracing()
    demo_programmatic_usage()
    
    # 可选：运行实际的调试解释器
    print("=" * 60)
    print("是否运行实际的调试解释器示例？(y/n)")
    print("=" * 60)
    try:
        response = input("> ").strip().lower()
        if response == 'y':
            demo_debug_interpreter()
    except (EOFError, KeyboardInterrupt):
        print("\n跳过实际运行示例")
    
    print("\n")
    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
    print("\n使用建议:")
    print("1. 在代码中导入: from hpl_runtime.debug import DebugInterpreter")
    print("2. 创建解释器: interpreter = DebugInterpreter()")
    print("3. 运行脚本: result = interpreter.run('your_script.hpl')")
    print("4. 查看报告: interpreter.print_debug_report()")
    print("5. 命令行使用: python -m hpl_runtime.debug your_script.hpl")
    print("=" * 60)


if __name__ == "__main__":
    main()
