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
```

### ExecutionLogger - 执行流程记录器

```python
from hpl_runtime.debug import ExecutionLogger

logger = ExecutionLogger()

# 记录函数调用
logger.log_function_call('main', [], line=1)

# 记录变量赋值
logger.log_variable_assign('x', 42, line=2)

# 获取执行跟踪
trace = logger.get_trace()
print(logger.format_trace())
```

### VariableInspector - 变量检查器

```python
from hpl_runtime.debug import VariableInspector

inspector = VariableInspector()

# 捕获变量状态
snapshot = inspector.capture(local_scope, global_scope, line=10)

# 格式化输出
print(inspector.format_variables(snapshot))
```

### CallStackAnalyzer - 调用栈分析器

```python
from hpl_runtime.debug import CallStackAnalyzer

analyzer = CallStackAnalyzer()

# 压入栈帧
analyzer.push_frame('main()', 'test.hpl', 1, {})

# 格式化输出
print(analyzer.format_stack())
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
from hpl_runtime.utils.exceptions import HPLRuntimeError, HPLSyntaxError

analyzer = ErrorAnalyzer()

# 分析多个错误
errors = [
    HPLSyntaxError("Unexpected token", line=5, file="test1.hpl"),
    HPLRuntimeError("Undefined variable", line=10, file="test2.hpl"),
]

for error in errors:
    analyzer.analyze_error(error)

# 获取摘要
summary = analyzer.get_summary()
print(f"总错误数: {summary['total_errors']}")
print(f"错误类型: {summary['error_types']}")
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

## 注意事项

1. 调试工具会增加一些运行时开销，建议在开发调试时使用
2. 生产环境可以禁用调试模式以提高性能
3. 敏感信息（如变量值）会被记录在调试报告中，注意保护
