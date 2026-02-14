# HPL 调试工具

该调试工具用于分析 HPL 脚本运行出错时的内部处理过程，提供详细的错误诊断信息。

## 功能特性

1. **错误传播跟踪** - 显示错误如何通过调用栈向上冒泡
2. **调用栈可视化** - 显示详细的调用栈和行号
3. **变量状态捕获** - 显示错误发生时的变量值
4. **执行流程分析** - 跟踪导致错误的执行路径
5. **错误上下文增强** - 用调试信息丰富错误消息
6. **Python Traceback** - 提供底层 traceback 用于深度调试

## 快速开始

### 命令行使用

```bash
# 使用调试模式运行 HPL 脚本
python -m hpl_runtime.debug your_script.hpl

# 详细模式
python -m hpl_runtime.debug your_script.hpl --verbose
```

### 程序化使用

```python
from hpl_runtime.debug import DebugInterpreter

# 创建调试解释器
interpreter = DebugInterpreter(debug_mode=True)

# 运行脚本
result = interpreter.run('your_script.hpl')

# 如果出错，打印调试报告
if not result['success']:
    interpreter.print_debug_report()
```

## 核心组件

### ErrorAnalyzer - 错误分析器

```python
from hpl_runtime.debug import ErrorAnalyzer

analyzer = ErrorAnalyzer()

# 分析错误
context = analyzer.analyze_error(error, source_code=code)

# 生成报告
report = analyzer.generate_report(context)
print(report)

# 获取错误摘要
summary = analyzer.get_summary()
print(f"总错误数: {summary['total_errors']}")

# 清除分析数据
analyzer.clear()
```

### ErrorTracer - 错误传播跟踪器

```python
from hpl_runtime.debug import ErrorTracer

tracer = ErrorTracer()

# 跟踪错误
context = tracer.trace_error(error, source_code=code, evaluator=evaluator)

# 添加传播步骤
tracer.add_propagation_step("divide()", "抛出除零错误")
tracer.add_propagation_step("calculate()", "未捕获错误，向上传播")

# 格式化传播路径
print(tracer.format_propagation_path())
```

### ErrorContext - 错误上下文

```python
from hpl_runtime.debug import ErrorContext

# ErrorContext 是错误分析的数据容器
context = ErrorContext(
    error=error,
    error_type="HPLRuntimeError",
    message="Undefined variable",
    line=10,
    column=5,
    file="test.hpl"
)

# 转换为字典格式
data = context.to_dict()
```

### ExecutionLogger - 执行流程记录器

```python
from hpl_runtime.debug import ExecutionLogger

# 创建记录器（可选配置最大条目数）
logger = ExecutionLogger(max_entries=1000)

# 启用/禁用记录
logger.enable()
logger.disable()

# 记录函数调用
logger.log_function_call('main', [], line=1)

# 记录函数返回
logger.log_function_return('add', 8, line=5)

# 记录变量赋值
logger.log_variable_assign('x', 42, line=2)

# 记录错误捕获
logger.log_error_catch('RuntimeError', line=10)

# 获取执行跟踪
trace = logger.get_trace(last_n=50)  # 获取最近50条
print(logger.format_trace())

# 清除记录
logger.clear()
```

### VariableInspector - 变量检查器

```python
from hpl_runtime.debug import VariableInspector

inspector = VariableInspector()

# 捕获变量状态
snapshot = inspector.capture(local_scope, global_scope, line=10)

# 获取最后一次快照
last = inspector.get_last_snapshot()

# 格式化输出
print(inspector.format_variables(snapshot))
# 或直接使用最后一次快照
print(inspector.format_variables())
```

### CallStackAnalyzer - 调用栈分析器

```python
from hpl_runtime.debug import CallStackAnalyzer

analyzer = CallStackAnalyzer()

# 压入栈帧
analyzer.push_frame('main()', 'test.hpl', 1, {'arg': 5})

# 弹出栈帧
frame = analyzer.pop_frame()

# 获取当前调用栈
stack = analyzer.get_current_stack()

# 格式化输出
print(analyzer.format_stack())
```

### DebugEvaluator - 调试执行器

```python
from hpl_runtime.debug import DebugEvaluator

# 创建调试执行器（通常在 DebugInterpreter 内部使用）
evaluator = DebugEvaluator(
    classes, objects, functions, main_func,
    debug_mode=True
)

# 调试模式会自动记录：
# - 函数调用和返回
# - 变量赋值
# - 错误捕获
# - 变量状态快照
```


## 示例

### 示例 1: 分析运行时错误

```python
from hpl_runtime.debug import DebugInterpreter

interpreter = DebugInterpreter()

# 运行包含错误的脚本
result = interpreter.run('examples/debug_demo.hpl')

# 查看执行结果
if result['success']:
    print("执行成功！")
    print("调试信息:", result['debug_info'])
else:
    print("执行失败")
    print("错误报告:", result['debug_info']['report'])
```

### 示例 2: 批量分析多个错误

```python
from hpl_runtime.debug import ErrorAnalyzer
from hpl_runtime.utils.exceptions import (
    HPLRuntimeError, HPLSyntaxError, 
    HPLTypeError, HPLNameError
)

analyzer = ErrorAnalyzer()

# 分析多个错误
errors = [
    HPLSyntaxError("Unexpected token: '}'", line=5, file="test1.hpl"),
    HPLRuntimeError("Undefined variable: 'x'", line=10, file="test2.hpl"),
    HPLTypeError("Cannot add string and number", line=15, file="test3.hpl"),
    HPLNameError("Function 'foo' not found", line=20, file="test4.hpl"),
]

for error in errors:
    analyzer.analyze_error(error)

# 获取摘要
summary = analyzer.get_summary()
print(f"总错误数: {summary['total_errors']}")
print(f"错误类型分布: {summary['error_types']}")
print(f"受影响的文件: {summary['files_affected']}")
```

### 示例 3: 错误传播跟踪

```python
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
print(f"位置: {context.file}:{context.line}:{context.column}")
print("\n源代码片段:")
print(context.source_snippet)
print("\n错误传播路径:")
print(tracer.format_propagation_path())
```

### 示例 4: 执行流程跟踪

```python
from hpl_runtime.debug import ExecutionLogger

logger = ExecutionLogger(max_entries=500)

# 模拟记录执行事件
logger.log_function_call("main", [], line=1)
logger.log_variable_assign("x", 10, line=2)
logger.log_function_call("calculate", [10, 20], line=3)
logger.log_variable_assign("result", 30, line=5)
logger.log_function_return("calculate", 30, line=6)
logger.log_function_return("main", None, line=7)

# 获取最近10条记录
recent = logger.get_trace(last_n=10)

# 格式化输出
print(logger.format_trace())
```

### 示例 5: 变量状态检查

```python
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

# 获取最后一次快照
last = inspector.get_last_snapshot()

# 格式化输出
print(inspector.format_variables(snapshot))
```


## 调试报告内容

调试报告包含以下信息：

1. **基本信息**
   - 错误类型
   - 错误消息
   - 发生时间

2. **位置信息**
   - 文件名
   - 行号
   - 列号

3. **源代码片段**
   - 错误行及上下文
   - 错误位置指示器

4. **调用栈**
   - 函数调用链
   - 最近调用在前

5. **运行时状态**
   - 调用栈深度
   - 全局对象
   - 导入的模块

6. **执行流程**
   - 函数调用记录
   - 变量赋值记录
   - 错误捕获记录

7. **Python Traceback**（调试模式）
   - 完整的 Python 调用栈
   - 用于深度调试

## 环境变量

- `HPL_DEBUG=1` - 启用调试模式，显示详细错误信息

## 文件结构

```
hpl_runtime/debug/
├── __init__.py           # 包接口
├── error_analyzer.py     # 错误分析核心
├── debug_interpreter.py  # 调试解释器
└── README.md            # 使用说明
```

## 运行示例

```bash
# 运行演示脚本
python examples/debug_tool_demo.py

# 使用调试模式运行示例
python -m hpl_runtime.debug examples/debug_demo.hpl
```

## 高级用法

### 与错误处理器集成

```python
from hpl_runtime.debug import DebugInterpreter
from hpl_runtime.utils.error_handler import create_error_handler

# 创建带错误处理的调试解释器
interpreter = DebugInterpreter(debug_mode=True)

# 错误处理器会自动生成用户友好的错误报告
result = interpreter.run('script.hpl')
if not result['success']:
    # 打印详细的调试报告
    interpreter.print_debug_report()
    
    # 获取错误摘要
    summary = interpreter.get_error_summary()
    print(f"错误统计: {summary}")
```

### 程序化调试工作流

```python
from hpl_runtime.debug import (
    DebugInterpreter, ErrorAnalyzer, 
    ExecutionLogger, VariableInspector
)

# 1. 创建调试解释器
interpreter = DebugInterpreter(debug_mode=True, verbose=True)

# 2. 运行脚本
result = interpreter.run('your_script.hpl')

# 3. 检查结果
if result['success']:
    # 获取执行跟踪
    trace = result['debug_info']['execution_trace']
    print(f"执行了 {len(trace)} 个步骤")
else:
    # 4. 分析错误
    error = result['error']
    debug_info = result['debug_info']
    
    # 5. 打印详细报告
    print(debug_info['report'])
    
    # 6. 获取执行跟踪（如果有）
    if 'execution_trace' in debug_info:
        print("执行跟踪:")
        for entry in debug_info['execution_trace'][-10:]:
            print(f"  {entry['type']}: {entry['details']}")

# 7. 清理资源
interpreter.clear()
```

## 故障排除

### 常见问题

**Q: 调试报告没有显示变量值？**
A: 确保 `debug_mode=True`，并且错误发生在变量赋值之后。检查 `VariableInspector` 的快照是否被正确捕获。

**Q: 执行跟踪记录太多，影响性能？**
A: 使用 `ExecutionLogger(max_entries=500)` 限制记录数量，或在关键代码段使用 `logger.enable()` / `logger.disable()` 控制记录。

**Q: 如何查看特定函数的调用情况？**
A: 使用 `CallStackAnalyzer` 手动跟踪，或检查调试报告中的调用栈部分。

**Q: 生产环境如何完全禁用调试？**
A: 设置 `HPL_DEBUG=0` 或不设置该环境变量，并使用 `DebugInterpreter(debug_mode=False)`。

## 性能考虑

| 功能 | 性能开销 | 建议 |
|------|---------|------|
| 基本错误分析 | 低 | 生产环境可用 |
| 执行流程记录 | 中 | 开发环境使用 |
| 变量状态捕获 | 中 | 开发环境使用 |
| 完整调试模式 | 高 | 仅调试时使用 |

## 最佳实践

1. **开发阶段**: 启用完整调试模式 (`debug_mode=True, verbose=True`)
2. **测试阶段**: 使用批量错误分析捕获所有问题
3. **生产阶段**: 禁用调试模式，仅保留基本错误报告
4. **敏感数据**: 注意变量快照可能包含敏感信息，妥善保护调试报告
5. **内存管理**: 长时间运行的脚本应定期清理或限制日志条目数

## 注意事项

1. 调试工具会增加一些运行时开销，建议在开发调试时使用
2. 生产环境可以禁用调试模式以提高性能
3. 敏感信息（如变量值）会被记录在调试报告中，注意保护
4. 大量执行跟踪记录会消耗内存，建议设置合理的 `max_entries`
5. 调试报告中的 Python Traceback 仅用于深度调试，普通用户无需关注
