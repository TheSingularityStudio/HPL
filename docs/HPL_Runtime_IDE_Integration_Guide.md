# HPL Runtime IDE 集成指南

本文档面向 HPL IDE 开发者，介绍如何使用 `hpl_runtime` 模块实现 HPL 语言的解析、执行和调试功能。

## 目录

1. [架构概述](#架构概述)
2. [快速开始](#快速开始)
3. [核心 API 详解](#核心-api-详解)
4. [IDE 集成要点](#ide-集成要点)
5. [模块系统](#模块系统)
6. [错误处理](#错误处理)
7. [高级调试功能](#高级调试功能)
8. [性能优化建议](#性能优化建议)

---

## 架构概述

HPL Runtime 采用三阶段执行模型：

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  HPL 源文件  │ -> │  解析阶段    │ -> │  执行阶段    │
│  (.hpl)     │    │             │    │             │
└─────────────┘    ├─────────────┤    ├─────────────┤
                   │ HPLParser   │    │ HPLEvaluator │
                   │ - 词法分析   │    │ - 表达式求值 │
                   │ - 语法分析   │    │ - 语句执行   │
                   │ - AST生成   │    │ - 作用域管理 │
                   └─────────────┘    └─────────────┘
```

### 核心组件

| 组件 | 类/函数 | 职责 |
|------|---------|------|
| 词法分析器 | `HPLLexer` | 将源代码转换为 token 流 |
| 顶层解析器 | `HPLParser` | 解析 YAML 结构，提取类/对象/函数定义 |
| AST 解析器 | `HPLASTParser` | 解析函数体内的语句和表达式 |
| 执行器 | `HPLEvaluator` | 执行 AST，管理变量和调用栈 |
| 调试解释器 | `DebugInterpreter` | 提供增强的错误诊断和执行跟踪 |

---

## 快速开始

### 最小化使用示例

```python
from hpl_runtime import HPLParser, HPLEvaluator

# 1. 解析 HPL 文件
parser = HPLParser("example.hpl")
classes, objects, functions, main_func, call_target, call_args, imports = parser.parse()

# 2. 创建执行器
evaluator = HPLEvaluator(classes, objects, functions, main_func)

# 3. 执行
evaluator.run()
```

### 带调试信息的执行

```python
from hpl_runtime import DebugInterpreter

# 使用调试解释器获取详细执行信息
interpreter = DebugInterpreter(debug_mode=True)
result = interpreter.run("example.hpl")

if result['success']:
    print("执行成功")
    print("执行跟踪:", result['debug_info']['execution_trace'])
else:
    print("执行失败:", result['error'])
    print("调试报告:", result['debug_info']['report'])
```

---

## 核心 API 详解

### 1. 解析 API

#### HPLParser

```python
class HPLParser:
    def __init__(self, hpl_file: str)
    def parse(self) -> Tuple[dict, dict, dict, HPLFunction, str, list, list]
```

**返回值说明：**
- `classes`: 类定义字典 `{class_name: HPLClass}`
- `objects`: 对象实例字典 `{obj_name: HPLObject}`
- `functions`: 顶层函数字典 `{func_name: HPLFunction}`
- `main_func`: main 函数对象（HPLFunction 或 None）
- `call_target`: call 键指定的目标函数名（如果存在 call 键）
- `call_args`: call 键的参数列表（如果存在 call 键）
- `imports`: 导入语句列表 `[{'module': str, 'alias': str}]`

**注意：** 如果 HPL 文件中没有 `call` 键，`call_target` 和 `call_args` 将返回 `None` 和空列表 `[]`。


**使用示例：**

```python
parser = HPLParser("example.hpl")

try:
    classes, objects, functions, main_func, target, args, imports = parser.parse()
    
    # 检查是否有 main 函数
    if main_func is None:
        print("错误: 未找到 main 函数")
        
    # 获取源代码（用于错误显示）
    source_code = parser.source_code
    
except HPLSyntaxError as e:
    # 获取详细的语法错误信息
    print(f"语法错误 at line {e.line}, column {e.column}")
    print(f"错误信息: {e.message}")
```

### 2. 执行 API

#### HPLEvaluator

```python
class HPLEvaluator:
    def __init__(self, 
                 classes: dict, 
                 objects: dict, 
                 functions: dict = None,
                 main_func: HPLFunction = None,
                 call_target: str = None,
                 call_args: list = None)
    
    def run(self) -> None
```

**使用示例：**

```python
# 标准执行流程
evaluator = HPLEvaluator(
    classes=classes,
    objects=objects,
    functions=functions,
    main_func=main_func,
    call_target="add",      # 可选：指定要调用的函数
    call_args=[5, 3]        # 可选：调用参数
)

try:
    evaluator.run()
except HPLRuntimeError as e:
    # 获取运行时错误和调用栈
    print(f"运行时错误: {e.message}")
    print(f"调用栈: {e.call_stack}")
```

### 3. 调试 API

#### DebugInterpreter

```python
class DebugInterpreter:
    def __init__(self, debug_mode: bool = True, verbose: bool = False)
    
    def run(self, 
            hpl_file: str,
            call_target: str = None,
            call_args: List[Any] = None) -> Dict[str, Any]
```

**返回值结构：**

```python
{
    'success': bool,           # 执行是否成功
    'file': str,              # 执行的文件路径
    'error': Exception,       # 错误对象（如果有）
    'debug_info': {
        'execution_trace': List[Dict],      # 执行跟踪记录（成功时）
        'variable_snapshots': List[Dict],   # 变量状态快照（成功时）
        'call_stack_history': List[str],    # 调用栈历史（成功时）
        'error_report': str,                # 错误处理器报告（错误时）
        'error_context': Dict,              # 错误分析上下文（错误时）
        'report': str,                      # 完整调试报告（错误时）
        'execution_trace': List[Dict]       # 执行跟踪记录（错误时，如果有）
    }
}
```


---

## IDE 集成要点

### 1. 语法错误获取与显示

HPL Runtime 提供详细的语法错误信息，包含行号和列号：

```python
from hpl_runtime import HPLParser, HPLSyntaxError

def check_syntax(file_path: str) -> Optional[Dict]:
    """检查 HPL 文件语法，返回错误信息"""
    try:
        parser = HPLParser(file_path)
        parser.parse()
        return None  # 无错误
    except HPLSyntaxError as e:
        return {
            'line': e.line,           # 错误行号（1-based）
            'column': e.column,       # 错误列号（1-based）
            'message': e.message,     # 错误描述
            'file': e.file,           # 文件路径
            'error_code': e.error_code  # 错误代码（如 HPL-SYNTAX-101）
        }

```

**IDE 应用：**
- 在编辑器中标记错误行
- 显示错误提示（hover 或诊断面板）
- 跳转到错误位置

### 2. 运行时错误和调用栈获取

```python
from hpl_runtime import HPLEvaluator, HPLRuntimeError

def run_with_error_capture(file_path: str):
    """执行 HPL 文件并捕获运行时错误"""
    parser = HPLParser(file_path)
    classes, objects, functions, main_func, _, _, _ = parser.parse()
    
    evaluator = HPLEvaluator(classes, objects, functions, main_func)
    
    try:
        evaluator.run()
    except HPLRuntimeError as e:
        error_info = {
            'type': e.__class__.__name__,
            'message': e.message,
            'line': e.line,
            'column': e.column,
            'file': e.file,
            'call_stack': e.call_stack,  # 调用栈列表
            'error_code': e.error_code
        }

        
        # 格式化调用栈显示
        print("调用栈:")
        for i, frame in enumerate(e.call_stack):
            print(f"  {i}: {frame}")
            
        return error_info
```

**IDE 应用：**
- 调试器调用栈视图
- 点击调用栈帧跳转到对应代码
- 显示变量值（结合变量监控）

### 3. 变量状态监控

使用 `DebugInterpreter` 获取执行过程中的变量状态：

```python
from hpl_runtime import DebugInterpreter

def monitor_variables(file_path: str):
    """监控变量状态变化"""
    interpreter = DebugInterpreter(debug_mode=True)
    result = interpreter.run(file_path)
    
    if result['debug_info'].get('variable_snapshots'):
        for snapshot in result['debug_info']['variable_snapshots']:
            print(f"Line {snapshot['line']}:")
            print(f"  Local variables: {snapshot['local']}")
            print(f"  Global variables: {snapshot['global']}")
```

**变量快照结构：**

```python
{
    'line': int,                # 代码行号
    'local': Dict[str, Any],    # 局部变量
    'global': Dict[str, Any],   # 全局变量（对象）
    'timestamp': float          # 时间戳
}
```


**IDE 应用：**
- 调试器变量视图
- 监视表达式（Watch）
- 悬停显示变量值

### 4. 执行流程跟踪

```python
def trace_execution(file_path: str):
    """跟踪代码执行流程"""
    interpreter = DebugInterpreter(debug_mode=True)
    result = interpreter.run(file_path)
    
    trace = result['debug_info']['execution_trace']
    
    for entry in trace:
        event_type = entry['type']      # FUNCTION_CALL, FUNCTION_RETURN, 
                                        # VARIABLE_ASSIGN, ERROR_CATCH 等
        details = entry['details']      # 事件详情
        line = entry.get('line')        # 代码行号
        timestamp = entry['timestamp']  # 时间戳
        
        print(f"[{event_type}] Line {line}: {details}")
```

**执行跟踪事件类型：**

| 事件类型 | 说明 | 详情内容 |
|---------|------|---------|
| `FUNCTION_CALL` | 函数调用 | `{'name': str, 'args': list}` |
| `FUNCTION_RETURN` | 函数返回 | `{'name': str, 'value': any}` |
| `VARIABLE_ASSIGN` | 变量赋值 | `{'name': str, 'value': any}` |
| `ERROR_CATCH` | 错误捕获 | `{'type': str, 'line': int}` |

**IDE 应用：**
- 执行历史视图
- 步骤回退/前进
- 性能分析（时间戳）

### 5. 代码补全支持

通过解析获取的类、对象和函数信息，可以实现代码补全：

```python
def get_completion_items(file_path: str, line: int, column: int):
    """获取代码补全项"""
    parser = HPLParser(file_path)
    classes, objects, functions, _, _, _, _ = parser.parse()
    
    items = []
    
    # 类名补全
    for class_name, hpl_class in classes.items():
        items.append({
            'label': class_name,
            'kind': 'Class',
            'detail': f"Class: {class_name}",
            'methods': list(hpl_class.methods.keys())
        })
    
    # 对象补全
    for obj_name, obj in objects.items():
        items.append({
            'label': obj_name,
            'kind': 'Object',
            'detail': f"Object: {obj_name} ({obj.hpl_class.name})"
        })
    
    # 函数补全
    for func_name, func in functions.items():
        items.append({
            'label': func_name,
            'kind': 'Function',
            'detail': f"Function: {func_name}({', '.join(func.params)})",
            'params': func.params
        })
    
    return items
```

---

## 模块系统

### 加载标准库模块

```python
from hpl_runtime.modules.loader import load_module

# 加载标准库模块
math_module = load_module('math')
io_module = load_module('io')
json_module = load_module('json')
os_module = load_module('os')
time_module = load_module('time')
```

### 模块搜索路径管理

```python
from hpl_runtime.modules.loader import add_module_path, get_module_paths

# 添加自定义模块搜索路径
add_module_path("/path/to/custom/modules")

# 查看当前搜索路径
print(get_module_paths())
```


### 模块缓存控制

```python
from hpl_runtime.modules.loader import clear_cache

# 清除模块缓存（开发时有用）
clear_cache()
```

---

## 错误处理

### 异常体系

```
HPLError (基类)
├── HPLSyntaxError      # 语法错误
├── HPLRuntimeError     # 运行时错误
│   ├── HPLTypeError    # 类型错误
│   ├── HPLNameError    # 未定义变量/函数
│   ├── HPLAttributeError   # 属性错误
│   ├── HPLIndexError   # 数组索引错误
│   ├── HPLKeyError     # 字典键错误
│   ├── HPLDivisionError    # 除零错误
│   ├── HPLValueError   # 值错误
│   ├── HPLIOError      # IO 错误
│   └── HPLRecursionError   # 递归错误
├── HPLImportError      # 导入错误
└── HPLControlFlowException  # 控制流异常（内部使用）
    ├── HPLBreakException    # break 语句
    ├── HPLContinueException # continue 语句
    └── HPLReturnValue       # return 语句
```

**注意：** `HPLControlFlowException` 及其子类是内部控制流机制，不是真正的错误，不应被用户代码捕获。

### 错误代码体系

HPL Runtime 使用统一的错误代码格式：`HPL-类别-编号`

| 错误代码 | 说明 |
|---------|------|
| HPL-SYNTAX-101 | 意外的 token |
| HPL-SYNTAX-102 | 缺少括号 |
| HPL-SYNTAX-103 | 缩进错误 |
| HPL-SYNTAX-150 | YAML 语法错误 |
| HPL-RUNTIME-201 | 未定义变量 |
| HPL-RUNTIME-202 | 类型不匹配 |
| HPL-RUNTIME-203 | 数组越界 |
| HPL-RUNTIME-204 | 除零错误 |
| HPL-RUNTIME-205 | 空指针 |
| HPL-RUNTIME-206 | 递归深度超限 |
| HPL-TYPE-301 | 无效操作 |
| HPL-TYPE-302 | 类型转换失败 |
| HPL-TYPE-303 | 缺少属性 |
| HPL-IMPORT-401 | 模块未找到 |
| HPL-IMPORT-402 | 循环导入 |
| HPL-IMPORT-403 | 版本不匹配 |
| HPL-IO-501 | 文件未找到 |
| HPL-IO-502 | 权限不足 |
| HPL-IO-503 | 读取错误 |


### 统一错误处理


```python
from hpl_runtime import (
    HPLSyntaxError, HPLRuntimeError, HPLImportError,
    format_error_for_user
)

def run_hpl_safe(file_path: str):
    """安全执行 HPL 文件，统一处理所有错误"""
    try:
        # 解析和执行...
        pass
        
    except HPLSyntaxError as e:
        # 语法错误
        user_message = format_error_for_user(e)
        show_error_dialog("语法错误", user_message, e.line, e.column)
        
    except HPLRuntimeError as e:
        # 运行时错误
        user_message = format_error_for_user(e)
        show_error_dialog("运行时错误", user_message, e.line, e.column)
        
        # 显示调用栈
        if e.call_stack:
            update_call_stack_view(e.call_stack)
            
    except HPLImportError as e:
        # 导入错误
        show_error_dialog("导入错误", str(e))
        
    except Exception as e:
        # 未预期的错误
        show_error_dialog("内部错误", f"未预期的错误: {str(e)}")
```

### format_error_for_user 函数

```python
from hpl_runtime.utils.exceptions import format_error_for_user

# 基本用法
error_message = format_error_for_user(error)

# 带源代码上下文（显示错误行及前后代码）
error_message = format_error_for_user(error, source_code=source_code)
```

### 错误处理器 (HPLErrorHandler)

```python
from hpl_runtime.utils.error_handler import create_error_handler

# 创建错误处理器
handler = create_error_handler(hpl_file, debug_mode=True)
handler.set_parser(parser)
handler.set_evaluator(evaluator)

# 处理错误
report = handler.handle(error, exit_on_error=False)
```

### 设置当前文件上下文

```python
from hpl_runtime.modules.loader import set_current_hpl_file

# 在执行前设置当前文件路径，用于正确的错误定位
set_current_hpl_file(hpl_file)
```


### 错误上下文获取


```python
from hpl_runtime.debug import ErrorAnalyzer

def analyze_error(error, source_code: str):
    """分析错误并提供上下文"""
    analyzer = ErrorAnalyzer()
    context = analyzer.analyze_error(error, source_code=source_code)
    
    return {
        'error_line': context.error_line,           # 错误行代码
        'surrounding_lines': context.surrounding_lines,  # 上下文行
        'suggestions': context.suggestions,         # 修复建议
        'severity': context.severity                # 严重程度
    }
```

---

## 高级调试功能

### 1. 断点支持（基础版）

虽然当前 DebugInterpreter 不支持真正的断点，但可以通过执行跟踪实现类似功能。注意：`DebugInterpreter` 还支持 `verbose` 参数用于启用详细输出：

```python
# 启用详细调试输出
interpreter = DebugInterpreter(debug_mode=True, verbose=True)
```


```python
class BreakpointDebugger:
    def __init__(self):
        self.breakpoints = set()  # 断点行号集合
        self.current_line = 0
        
    def set_breakpoint(self, line: int):
        self.breakpoints.add(line)
        
    def clear_breakpoint(self, line: int):
        self.breakpoints.discard(line)
        
    def check_breakpoint(self, line: int) -> bool:
        return line in self.breakpoints

# 在执行跟踪中检查断点
def run_with_breakpoints(file_path: str, debugger: BreakpointDebugger):
    interpreter = DebugInterpreter(debug_mode=True)
    result = interpreter.run(file_path)
    
    # 分析执行跟踪，在断点处暂停
    for entry in result['debug_info']['execution_trace']:
        line = entry.get('line')
        if line and debugger.check_breakpoint(line):
            print(f"断点命中: Line {line}")
            # 触发 IDE 断点事件
            trigger_breakpoint_event(line, entry)
```

### 2. 性能分析

```python
def profile_execution(file_path: str):
    """分析代码执行性能"""
    import time
    
    interpreter = DebugInterpreter(debug_mode=True)
    
    start_time = time.time()
    result = interpreter.run(file_path)
    total_time = time.time() - start_time
    
    # 分析执行跟踪
    trace = result['debug_info']['execution_trace']
    
    # 统计函数调用次数和时间
    function_stats = {}
    current_function = None
    function_start_time = None
    
    for entry in trace:
        if entry['type'] == 'FUNCTION_CALL':
            current_function = entry['details']['name']
            function_start_time = entry['timestamp']
        elif entry['type'] == 'FUNCTION_RETURN' and current_function:
            duration = entry['timestamp'] - function_start_time
            if current_function not in function_stats:
                function_stats[current_function] = {
                    'calls': 0,
                    'total_time': 0
                }
            function_stats[current_function]['calls'] += 1
            function_stats[current_function]['total_time'] += duration
    
    return {
        'total_time': total_time,
        'function_stats': function_stats
    }
```

### 3. 代码覆盖率

通过执行跟踪可以实现基础的代码覆盖率分析：

```python
def get_coverage(file_path: str):
    """获取代码覆盖率信息"""
    interpreter = DebugInterpreter(debug_mode=True)
    result = interpreter.run(file_path)
    
    # 获取执行的行号
    executed_lines = set()
    for entry in result['debug_info']['execution_trace']:
        line = entry.get('line')
        if line:
            executed_lines.add(line)
    
    # 对比源代码总行数
    source_lines = len(result['source_code'].split('\n'))
    
    return {
        'executed_lines': executed_lines,
        'total_lines': source_lines,
        'coverage_percent': len(executed_lines) / source_lines * 100
    }
```

---

## 性能优化建议

### 1. 解析缓存

对于大型项目，建议缓存解析结果：

```python
import hashlib
import pickle

class ParseCache:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        
    def _get_cache_key(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()
    
    def get_cached_parse(self, file_path: str):
        cache_key = self._get_cache_key(file_path)
        cache_file = f"{self.cache_dir}/{cache_key}.pickle"
        
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def cache_parse_result(self, file_path: str, parse_result):
        cache_key = self._get_cache_key(file_path)
        cache_file = f"{self.cache_dir}/{cache_key}.pickle"
        
        with open(cache_file, 'wb') as f:
            pickle.dump(parse_result, f)
```

### 2. 增量解析

对于 IDE 的实时编辑场景，考虑实现增量解析：

```python
def incremental_parse(file_path: str, changed_lines: List[int]):
    """增量解析（概念示例）"""
    # 1. 获取上次解析结果
    last_result = get_last_parse_result(file_path)
    
    # 2. 只重新解析变化的函数
    for func_name, func in last_result['functions'].items():
        if func.line_range.intersects(changed_lines):
            # 重新解析该函数
            reparse_function(func_name)
    
    # 3. 更新解析结果
    return updated_result
```

### 3. 延迟加载

对于大型 HPL 文件，考虑延迟加载不常用的类和函数：

```python
class LazyParser:
    """延迟解析器"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._raw_data = None
        self._parsed_functions = {}
        
    def get_function(self, func_name: str):
        """按需解析函数"""
        if func_name not in self._parsed_functions:
            # 只解析需要的函数
            self._parsed_functions[func_name] = self._parse_single_function(func_name)
        return self._parsed_functions[func_name]
```

---

## 附录：完整示例

### 简单的 HPL IDE 后端

```python
#!/usr/bin/env python3
"""
HPL IDE 后端示例
展示如何集成 hpl_runtime 实现完整的 IDE 功能
"""

import sys
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from hpl_runtime import (
    HPLParser, HPLEvaluator, DebugInterpreter,
    HPLSyntaxError, HPLRuntimeError, HPLImportError,
    format_error_for_user
)


@dataclass
class Diagnostic:
    """诊断信息"""
    line: int
    column: int
    severity: str  # 'error', 'warning', 'info'
    message: str
    code: Optional[str] = None


class HPLEngine:
    """HPL IDE 引擎"""
    
    def __init__(self):
        self.current_file: Optional[str] = None
        self.parser: Optional[HPLParser] = None
        self.last_parse_result: Optional[Dict] = None
        
    def open_file(self, file_path: str):
        """打开 HPL 文件"""
        self.current_file = file_path
        self.parser = HPLParser(file_path)
        
    def validate(self) -> List[Diagnostic]:
        """验证文件，返回诊断列表"""
        diagnostics = []
        
        try:
            self.last_parse_result = self.parser.parse()
        except HPLSyntaxError as e:
            diagnostics.append(Diagnostic(
                line=e.line or 1,
                column=e.column or 1,
                severity='error',
                message=e.message,
                code=e.error_code
            ))

        except Exception as e:
            diagnostics.append(Diagnostic(
                line=1, column=1,
                severity='error',
                message=str(e)
            ))
            
        return diagnostics
    
    def get_completions(self, line: int, column: int, prefix: str = "") -> List[Dict]:
        """获取代码补全项"""
        if not self.last_parse_result:
            self.validate()
            
        if not self.last_parse_result:
            return []
            
        items = []
        classes, objects, functions, _, _, _, _ = self.last_parse_result
        
        # 类补全
        for name in classes.keys():
            if name.startswith(prefix):
                items.append({
                    'label': name,
                    'kind': 'Class',
                    'detail': f'Class {name}'
                })
        
        # 对象补全
        for name, obj in objects.items():
            if name.startswith(prefix):
                items.append({
                    'label': name,
                    'kind': 'Object',
                    'detail': f'Object {name} ({obj.hpl_class.name})'
                })
        
        # 函数补全
        for name, func in functions.items():
            if name.startswith(prefix):
                items.append({
                    'label': name,
                    'kind': 'Function',
                    'detail': f'Function {name}({", ".join(func.params)})',
                    'insertText': f'{name}({", ".join(["${" + str(i+1) + ":" + p + "}" for i, p in enumerate(func.params)])})'
                })
        
        return items
    
    def run(self, debug: bool = False) -> Dict[str, Any]:
        """执行代码"""
        if not self.last_parse_result:
            error = self.validate()
            if error:
                return {
                    'success': False,
                    'diagnostics': [vars(d) for d in error]
                }
        
        if debug:
            # 调试模式
            interpreter = DebugInterpreter(debug_mode=True)
            result = interpreter.run(self.current_file)
            return {
                'success': result['success'],
                'error': str(result['error']) if result['error'] else None,
                'trace': result['debug_info'].get('execution_trace', []),
                'variables': result['debug_info'].get('variable_snapshots', [])
            }
        else:
            # 标准模式
            classes, objects, functions, main_func, _, _, _ = self.last_parse_result
            
            if not main_func:
                return {
                    'success': False,
                    'error': 'No main function found'
                }
            
            evaluator = HPLEvaluator(classes, objects, functions, main_func)
            
            try:
                evaluator.run()
                return {'success': True}
            except HPLRuntimeError as e:
                return {
                    'success': False,
                    'error': format_error_for_user(e),
                    'line': e.line,
                    'column': e.column,
                    'call_stack': e.call_stack
                }


# 命令行接口
def main():
    if len(sys.argv) < 2:
        print("Usage: hpl_ide_backend.py <command> [args...]")
        print("Commands:")
        print("  validate <file>           - 验证 HPL 文件")
        print("  complete <file> <line> <col> [prefix] - 代码补全")
        print("  run <file> [--debug]      - 执行 HPL 文件")
        sys.exit(1)
    
    command = sys.argv[1]
    engine = HPLEngine()
    
    if command == 'validate':
        file_path = sys.argv[2]
        engine.open_file(file_path)
        diagnostics = engine.validate()
        print(json.dumps([vars(d) for d in diagnostics], indent=2, ensure_ascii=False))
        
    elif command == 'complete':
        file_path = sys.argv[2]
        line = int(sys.argv[3])
        column = int(sys.argv[4])
        prefix = sys.argv[5] if len(sys.argv) > 5 else ""
        
        engine.open_file(file_path)
        completions = engine.get_completions(line, column, prefix)
        print(json.dumps(completions, indent=2, ensure_ascii=False))
        
    elif command == 'run':
        file_path = sys.argv[2]
        debug_mode = '--debug' in sys.argv
        
        engine.open_file(file_path)
        result = engine.run(debug=debug_mode)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()
```

---

## 版本信息

- 文档版本: 1.0.2
- 对应 HPL Runtime 版本: 1.1.2
- 最后更新: 2026-02-12



## 相关资源

- HPL 语法手册: `docs/HPL语法手册.md`
- HPL 语法概览: `docs/HPL语法概览.md`
- 标准库文档: `hpl_runtime/stdlib/`
- 调试工具文档: `hpl_runtime/debug/README.md`
