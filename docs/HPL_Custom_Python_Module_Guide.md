# HPL 自定义 Python 模块开发指南

## 目录
1. [概述](#概述)
2. [快速开始](#快速开始)
3. [显式接口](#显式接口)
4. [API 参考](#api-参考)
5. [错误处理](#错误处理)
6. [完整示例](#完整示例)
7. [在 HPL 中使用](#在-hpl-中使用)
8. [最佳实践](#最佳实践)
9. [故障排除](#故障排除)
10. [高级主题](#高级主题)

---

## 概述

HPL（High-level Programming Language）支持通过自定义 Python 模块来扩展其功能。这让您能够：

- **利用 Python 生态**：使用 Python 丰富的第三方库
- **性能优化**：用 Python 实现计算密集型操作
- **系统交互**：访问操作系统功能、文件系统、网络等
- **自定义业务逻辑**：封装特定领域的算法和功能

### 两种接口方式

| 方式 | 描述 | 适用场景 |
|------|------|----------|
| **自动接口** | 自动暴露所有非下划线开头的函数和变量 | 快速原型、简单模块 |
| **显式接口** | 使用 `HPLModule` 精确控制暴露的 API | 生产环境、公共模块 |

---

## 快速开始

### 最简单的模块（自动接口）

创建一个 Python 文件 `my_module.py`：

```python
# my_module.py
# 自动接口 - 所有非下划线开头的函数和变量都会暴露给 HPL

def greet(name):
    """向用户问好"""
    return f"Hello, {name}!"

def add(a, b):
    """两数相加"""
    return a + b

# 常量也会自动暴露
APP_VERSION = "1.0.0"
MAX_COUNT = 100
```

### 在 HPL 中使用

```hpl
imports:
  - my_module

main: () => {
  # 调用函数
  message = my_module.greet("HPL")
  echo(message)  # 输出: Hello, HPL!
  
  # 使用常量
  echo(my_module.APP_VERSION)  # 输出: 1.0.0
  
  # 数学运算
  result = my_module.add(10, 20)
  echo(result)  # 输出: 30
}
```

### 模块搜索路径

HPL 按以下顺序查找模块：

1. **当前 HPL 文件所在目录**（用于相对导入）
2. **当前工作目录**（运行 HPL 的目录）
3. **HPL_MODULE_PATHS**（全局模块路径列表）
4. **~/.hpl/packages**（HPL 包目录）

---

## 显式接口

对于需要精确控制 API 的模块，使用 `HPLModule` 类：

```python
# advanced_module.py
from hpl_runtime.modules.base import HPLModule
from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError

# 创建模块实例
HPL_MODULE = HPLModule("advanced_module", "高级数学工具模块")

# 定义函数
def factorial(n):
    """计算阶乘"""
    if not isinstance(n, int):
        raise HPLTypeError(f"factorial() requires int, got {type(n).__name__}")
    if n < 0:
        raise HPLValueError("factorial() requires non-negative integer")
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def fibonacci(n):
    """计算斐波那契数列第 n 项"""
    if not isinstance(n, int):
        raise HPLTypeError(f"fibonacci() requires int, got {type(n).__name__}")
    if n < 0:
        raise HPLValueError("fibonacci() requires non-negative integer")
    
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

# 显式注册函数（带参数数量检查）
HPL_MODULE.register_function('factorial', factorial, 1, 'Calculate factorial')
HPL_MODULE.register_function('fibonacci', fibonacci, 1, 'Calculate Fibonacci number')

# 显式注册常量
HPL_MODULE.register_constant('PHI', 1.618033988749895, 'Golden ratio')
HPL_MODULE.register_constant('E', 2.718281828459045, 'Euler\'s number')
```

### 显式接口的优势

- ✅ **参数验证**：自动检查参数数量
- ✅ **精确控制**：只暴露需要的函数
- ✅ **更好的文档**：每个函数和常量都有描述
- ✅ **错误处理**：使用 HPL 原生异常类型

---

## API 参考

### HPLModule 类

```python
class HPLModule:
    def __init__(self, name, description="")
    def register_function(self, name, func, param_count=None, description="")
    def register_constant(self, name, value, description="")
    def call_function(self, func_name, args)
    def get_constant(self, name)
    def list_functions(self)
    def list_constants(self)
```

#### 构造函数

```python
HPLModule(name, description="")
```

- **name**: 模块名称（在 HPL 中使用）
- **description**: 模块描述（用于文档）

#### 注册函数

```python
register_function(name, func, param_count=None, description="")
```

- **name**: 函数在 HPL 中的名称
- **func**: Python 函数对象
- **param_count**: 参数数量（None 表示不检查）
- **description**: 函数描述

**参数数量检查示例：**

```python
# 严格检查 2 个参数
HPL_MODULE.register_function('add', add, 2, 'Add two numbers')

# 可选参数（不检查数量）
HPL_MODULE.register_function('log', log, None, 'Log with optional base')

# 可变参数（不检查数量）
HPL_MODULE.register_function('sum_all', sum_all, None, 'Sum all arguments')
```

#### 注册常量

```python
register_constant(name, value, description="")
```

- **name**: 常量名称
- **value**: 常量值（任何 Python 对象）
- **description**: 常量描述

### 辅助函数

```python
# 添加模块搜索路径
from hpl_runtime.modules.loader import add_module_path
add_module_path("/path/to/your/modules")

# 获取模块加载器上下文
from hpl_runtime.modules.loader import get_loader_context
context = get_loader_context()
current_dir = context.get_current_file_dir()
```

---

## 错误处理

### HPL 异常类型

| 异常 | 用途 | 示例 |
|------|------|------|
| `HPLTypeError` | 类型错误 | 期望数字但获得字符串 |
| `HPLValueError` | 值错误 | 负数开平方 |
| `HPLNameError` | 名称错误 | 函数不存在 |
| `HPLAttributeError` | 属性错误 | 常量不存在 |
| `HPLImportError` | 导入错误 | 模块未找到 |

### 导入异常类

```python
try:
    from hpl_runtime.utils.exceptions import (
        HPLTypeError, 
        HPLValueError,
        HPLNameError,
        HPLAttributeError,
        HPLImportError
    )
except ImportError:
    # 备用导入方式
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from hpl_runtime.utils.exceptions import (
        HPLTypeError, 
        HPLValueError,
        HPLNameError,
        HPLAttributeError,
        HPLImportError
    )
```

### 错误处理最佳实践

```python
def divide(a, b):
    """安全除法"""
    # 类型检查
    if not isinstance(a, (int, float)):
        raise HPLTypeError(f"divide() requires number for a, got {type(a).__name__}")
    if not isinstance(b, (int, float)):
        raise HPLTypeError(f"divide() requires number for b, got {type(b).__name__}")
    
    # 值检查
    if b == 0:
        raise HPLValueError("divide() cannot divide by zero")
    
    return a / b

def get_element(lst, index):
    """安全获取列表元素"""
    if not isinstance(lst, list):
        raise HPLTypeError(f"get_element() requires list, got {type(lst).__name__}")
    if not isinstance(index, int):
        raise HPLTypeError(f"get_element() requires int for index, got {type(index).__name__}")
    
    if index < 0 or index >= len(lst):
        raise HPLValueError(f"get_element() index {index} out of range for list of length {len(lst)}")
    
    return lst[index]
```

---

## 完整示例

### 示例 1：数据处理模块

```python
# data_utils.py
"""HPL 数据处理工具模块"""

try:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError
except ImportError:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError

HPL_MODULE = HPLModule("data_utils", "数据处理工具")

# ============ 列表操作 ============

def filter_list(items, predicate_value):
    """过滤列表 - 保留等于 predicate_value 的元素"""
    if not isinstance(items, list):
        raise HPLTypeError(f"filter_list() requires list, got {type(items).__name__}")
    return [item for item in items if item == predicate_value]

def map_list(items, operation):
    """映射列表 - 对每个元素执行操作"""
    if not isinstance(items, list):
        raise HPLTypeError(f"map_list() requires list, got {type(items).__name__}")
    
    if operation == "double":
        return [x * 2 for x in items]
    elif operation == "square":
        return [x * x for x in items]
    elif operation == "str":
        return [str(x) for x in items]
    else:
        raise HPLValueError(f"Unknown operation: {operation}")

def reduce_list(items, operation):
    """归约列表"""
    if not isinstance(items, list):
        raise HPLTypeError(f"reduce_list() requires list, got {type(items).__name__}")
    if len(items) == 0:
        raise HPLValueError("reduce_list() cannot reduce empty list")
    
    if operation == "sum":
        return sum(items)
    elif operation == "product":
        result = 1
        for item in items:
            result *= item
        return result
    elif operation == "max":
        return max(items)
    elif operation == "min":
        return min(items)
    else:
        raise HPLValueError(f"Unknown operation: {operation}")

def unique(items):
    """去重（保持顺序）"""
    if not isinstance(items, list):
        raise HPLTypeError(f"unique() requires list, got {type(items).__name__}")
    
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

# ============ 统计函数 ============

def mean(items):
    """计算平均值"""
    if not isinstance(items, list):
        raise HPLTypeError(f"mean() requires list, got {type(items).__name__}")
    if len(items) == 0:
        raise HPLValueError("mean() cannot calculate mean of empty list")
    
    return sum(items) / len(items)

def median(items):
    """计算中位数"""
    if not isinstance(items, list):
        raise HPLTypeError(f"median() requires list, got {type(items).__name__}")
    if len(items) == 0:
        raise HPLValueError("median() cannot calculate median of empty list")
    
    sorted_items = sorted(items)
    n = len(sorted_items)
    mid = n // 2
    
    if n % 2 == 0:
        return (sorted_items[mid - 1] + sorted_items[mid]) / 2
    else:
        return sorted_items[mid]

def std_dev(items):
    """计算标准差"""
    if not isinstance(items, list):
        raise HPLTypeError(f"std_dev() requires list, got {type(items).__name__}")
    if len(items) < 2:
        raise HPLValueError("std_dev() requires at least 2 elements")
    
    avg = sum(items) / len(items)
    variance = sum((x - avg) ** 2 for x in items) / len(items)
    return variance ** 0.5

# ============ 注册函数 ============

HPL_MODULE.register_function('filter', filter_list, 2, 'Filter list by value')
HPL_MODULE.register_function('map', map_list, 2, 'Map operation over list')
HPL_MODULE.register_function('reduce', reduce_list, 2, 'Reduce list to single value')
HPL_MODULE.register_function('unique', unique, 1, 'Remove duplicates from list')
HPL_MODULE.register_function('mean', mean, 1, 'Calculate mean')
HPL_MODULE.register_function('median', median, 1, 'Calculate median')
HPL_MODULE.register_function('std_dev', std_dev, 1, 'Calculate standard deviation')

# ============ 注册常量 ============

HPL_MODULE.register_constant('PI', 3.14159265359, 'Pi constant')
HPL_MODULE.register_constant('E', 2.71828182846, 'Euler\'s number')
```

**在 HPL 中使用：**

```hpl
imports:
  - data_utils

main: () => {
  numbers = [1, 2, 3, 4, 5, 2, 3, 2]
  
  # 过滤
  twos = data_utils.filter(numbers, 2)
  echo("Filter 2: " + twos)  # [2, 2, 2]
  
  # 去重
  unique_nums = data_utils.unique(numbers)
  echo("Unique: " + unique_nums)  # [1, 2, 3, 4, 5]
  
  # 统计
  echo("Mean: " + data_utils.mean(numbers))
  echo("Median: " + data_utils.median(numbers))
  
  # 映射
  doubled = data_utils.map(numbers, "double")
  echo("Doubled: " + doubled)
}
```

### 示例 2：文件处理模块

```python
# file_tools.py
"""HPL 文件处理工具"""

import os
import json
import csv
from pathlib import Path

try:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError, HPLRuntimeError
except ImportError:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError, HPLRuntimeError

HPL_MODULE = HPLModule("file_tools", "文件处理工具")

# ============ 路径操作 ============

def join_path(*parts):
    """连接路径"""
    return str(Path(*parts))

def get_extension(filename):
    """获取文件扩展名"""
    if not isinstance(filename, str):
        raise HPLTypeError(f"get_extension() requires string, got {type(filename).__name__}")
    return Path(filename).suffix

def get_filename(path):
    """获取文件名（不含路径）"""
    if not isinstance(path, str):
        raise HPLTypeError(f"get_filename() requires string, got {type(path).__name__}")
    return Path(path).name

def get_dirname(path):
    """获取目录名"""
    if not isinstance(path, str):
        raise HplTypeError(f"get_dirname() requires string, got {type(path).__name__}")
    return str(Path(path).parent)

# ============ JSON 文件 ============

def read_json(filepath):
    """读取 JSON 文件"""
    if not isinstance(filepath, str):
        raise HPLTypeError(f"read_json() requires string, got {type(filepath).__name__}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HPLRuntimeError(f"File not found: {filepath}")
    except json.JSONDecodeError as e:
        raise HPLValueError(f"Invalid JSON in {filepath}: {e}")

def write_json(filepath, data, indent=2):
    """写入 JSON 文件"""
    if not isinstance(filepath, str):
        raise HPLTypeError(f"write_json() requires string for filepath, got {type(filepath).__name__}")
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        raise HPLRuntimeError(f"Failed to write JSON: {e}")

# ============ CSV 文件 ============

def read_csv(filepath, has_header=True):
    """读取 CSV 文件"""
    if not isinstance(filepath, str):
        raise HPLTypeError(f"read_csv() requires string, got {type(filepath).__name__}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            if has_header and len(rows) > 0:
                header = rows[0]
                data = rows[1:]
                return {"header": header, "data": data}
            else:
                return {"header": None, "data": rows}
    except FileNotFoundError:
        raise HPLRuntimeError(f"File not found: {filepath}")

def write_csv(filepath, data, header=None):
    """写入 CSV 文件"""
    if not isinstance(filepath, str):
        raise HPLTypeError(f"write_csv() requires string, got {type(filepath).__name__}")
    if not isinstance(data, list):
        raise HPLTypeError(f"write_csv() requires list for data, got {type(data).__name__}")
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(header)
            writer.writerows(data)
        return True
    except Exception as e:
        raise HPLRuntimeError(f"Failed to write CSV: {e}")

# ============ 目录操作 ============

def list_files(directory, pattern="*"):
    """列出目录中的文件"""
    if not isinstance(directory, str):
        raise HPLTypeError(f"list_files() requires string, got {type(directory).__name__}")
    
    try:
        path = Path(directory)
        return [str(f) for f in path.glob(pattern) if f.is_file()]
    except Exception as e:
        raise HPLRuntimeError(f"Failed to list files: {e}")

def ensure_dir(directory):
    """确保目录存在（不存在则创建）"""
    if not isinstance(directory, str):
        raise HPLTypeError(f"ensure_dir() requires string, got {type(directory).__name__}")
    
    Path(directory).mkdir(parents=True, exist_ok=True)
    return True

# ============ 注册 ============

HPL_MODULE.register_function('join_path', join_path, None, 'Join path components')
HPL_MODULE.register_function('get_extension', get_extension, 1, 'Get file extension')
HPL_MODULE.register_function('get_filename', get_filename, 1, 'Get filename from path')
HPL_MODULE.register_function('get_dirname', get_dirname, 1, 'Get directory from path')
HPL_MODULE.register_function('read_json', read_json, 1, 'Read JSON file')
HPL_MODULE.register_function('write_json', write_json, None, 'Write JSON file')
HPL_MODULE.register_function('read_csv', read_csv, None, 'Read CSV file')
HPL_MODULE.register_function('write_csv', write_csv, None, 'Write CSV file')
HPL_MODULE.register_function('list_files', list_files, None, 'List files in directory')
HPL_MODULE.register_function('ensure_dir', ensure_dir, 1, 'Ensure directory exists')
```

### 示例 3：网络请求模块

```python
# web_utils.py
"""HPL 网络工具模块"""

import urllib.request
import urllib.parse
import json

try:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLRuntimeError
except ImportError:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLRuntimeError

HPL_MODULE = HPLModule("web_utils", "网络请求工具")

def http_get(url, headers=None):
    """发送 HTTP GET 请求"""
    if not isinstance(url, str):
        raise HPLTypeError(f"http_get() requires string, got {type(url).__name__}")
    
    try:
        req = urllib.request.Request(url)
        if headers and isinstance(headers, dict):
            for key, value in headers.items():
                req.add_header(key, value)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return {
                "status": response.status,
                "body": response.read().decode('utf-8')
            }
    except Exception as e:
        raise HPLRuntimeError(f"HTTP GET failed: {e}")

def http_post(url, data, headers=None):
    """发送 HTTP POST 请求"""
    if not isinstance(url, str):
        raise HPLTypeError(f"http_post() requires string for url, got {type(url).__name__}")
    
    try:
        if isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
            default_headers = {"Content-Type": "application/json"}
        else:
            data = str(data).encode('utf-8')
            default_headers = {}
        
        req = urllib.request.Request(url, data=data, method='POST')
        
        # 添加默认头部
        for key, value in default_headers.items():
            req.add_header(key, value)
        
        # 添加自定义头部
        if headers and isinstance(headers, dict):
            for key, value in headers.items():
                req.add_header(key, value)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return {
                "status": response.status,
                "body": response.read().decode('utf-8')
            }
    except Exception as e:
        raise HPLRuntimeError(f"HTTP POST failed: {e}")

def url_encode(text):
    """URL 编码"""
    if not isinstance(text, str):
        raise HPLTypeError(f"url_encode() requires string, got {type(text).__name__}")
    return urllib.parse.quote(text)

def url_decode(text):
    """URL 解码"""
    if not isinstance(text, str):
        raise HPLTypeError(f"url_decode() requires string, got {type(text).__name__}")
    return urllib.parse.unquote(text)

HPL_MODULE.register_function('http_get', http_get, None, 'HTTP GET request')
HPL_MODULE.register_function('http_post', http_post, None, 'HTTP POST request')
HPL_MODULE.register_function('url_encode', url_encode, 1, 'URL encode string')
HPL_MODULE.register_function('url_decode', url_decode, 1, 'URL decode string')
```

---

## 在 HPL 中使用

### 基本导入语法

```hpl
imports:
  - my_module
  - math: m        # 使用别名
  - io
```

### 调用函数

```hpl
# 直接调用
result = my_module.calculate(10, 20)

# 使用别名
result = m.sqrt(16)

# 链式调用
data = my_module.process(my_module.load_data())
```

### 访问常量

```hpl
echo(my_module.APP_VERSION)
echo(m.PI)
```

### 处理返回值

```hpl
# 简单值
sum = math.add(1, 2)

# 列表
items = data_utils.filter(my_list, "active")

# 字典（映射为 HPL 的键值对列表）
response = web_utils.http_get("https://api.example.com/data")
status = response["status"]
body = response["body"]
```

---

## 最佳实践

### 1. 命名规范

```python
# ✅ 好的命名
def calculate_area()
def process_data()
MAX_RETRY_COUNT = 3

# ❌ 避免
def calc()          # 太简短
def processData()   # 驼峰命名（HPL 使用下划线）
__private_func()   # 双下划线开头（不会暴露，但单下划线即可）
```

### 2. 文档字符串

```python
def complex_operation(data, threshold, options):
    """
    执行复杂数据处理操作
    
    Args:
        data: 输入数据列表
        threshold: 阈值（数值）
        options: 配置选项（字典）
    
    Returns:
        处理后的结果列表
    
    Raises:
        HPLTypeError: 参数类型错误
        HPLValueError: 参数值无效
    """
    pass
```

### 3. 版本管理

```python
# 在模块中定义版本信息
__version__ = "1.2.3"
__author__ = "Your Name"
__description__ = "Module description"

# 注册为常量
HPL_MODULE.register_constant('VERSION', __version__, 'Module version')
HPL_MODULE.register_constant('AUTHOR', __author__, 'Module author')
```

### 4. 输入验证

```python
def safe_divide(a, b):
    """安全除法 - 完整的输入验证示例"""
    # 类型检查
    if not isinstance(a, (int, float)):
        raise HPLTypeError(f"Expected number for a, got {type(a).__name__}")
    if not isinstance(b, (int, float)):
        raise HPLTypeError(f"Expected number for b, got {type(b).__name__}")
    
    # 值检查
    if b == 0:
        raise HPLValueError("Cannot divide by zero")
    
    # 范围检查（可选）
    if abs(b) < 1e-10:
        raise HPLValueError("Divisor too small, may cause overflow")
    
    return a / b
```

### 5. 性能优化

```python
# 缓存计算结果
_cache = {}

def expensive_operation(n):
    if n in _cache:
        return _cache[n]
    
    result = _compute_expensively(n)
    _cache[n] = result
    return result

# 批量处理
def process_batch(items):
    """批量处理比逐个处理更高效"""
    return [process_item(item) for item in items]
```

### 6. 模块结构

```python
"""
模块标题
========

简要描述模块功能。

详细说明...
"""

# ============ 导入 ============
try:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import ...
except ImportError:
    # 备用导入
    ...

# ============ 配置 ============
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# ============ 内部函数 ============
def _helper_function():
    """内部辅助函数（单下划线开头，不会暴露）"""
    pass

# ============ 公共函数 ============
def public_function():
    """公共 API"""
    pass

# ============ 模块注册 ============
HPL_MODULE = HPLModule("module_name", "Description")
# ... 注册函数和常量 ...
```

---

## 故障排除

### 常见问题

#### 1. 模块未找到

**症状：**
```
Error: Module 'my_module' not found
```

**解决方案：**
```python
# 检查模块文件位置
# 1. 与 HPL 文件同一目录
# 2. 当前工作目录
# 3. 添加到模块路径

from hpl_runtime.modules.loader import add_module_path
add_module_path("/path/to/your/modules")
```

#### 2. 函数未找到

**症状：**
```
Error: Function 'foo' not found in module 'my_module'
```

**解决方案：**
```python
# 检查函数名拼写
# 检查是否使用了显式接口但未注册
# 检查是否使用了双下划线（__）开头

# ✅ 会被暴露
def public_func(): pass
def _private_func(): pass  # 单下划线，自动接口中不会暴露

# ❌ 不会被暴露
def __private_func(): pass  # 双下划线，名称修饰
```

#### 3. 参数数量错误

**症状：**
```
Error: Function 'add' expects 2 arguments, got 3
```

**解决方案：**
```python
# 检查 param_count 设置
HPL_MODULE.register_function('add', add, 2, 'Add two numbers')

# 或使用 None 表示可变参数
HPL_MODULE.register_function('sum_all', sum_all, None, 'Sum all arguments')
```

#### 4. 类型错误

**症状：**
```
Error: sqrt() requires number, got str
```

**解决方案：**
```python
# 在 HPL 中确保传递正确类型
# 或在 Python 中进行类型转换

def flexible_add(a, b):
    try:
        return float(a) + float(b)
    except (ValueError, TypeError):
        raise HPLTypeError(f"Cannot convert arguments to numbers")
```

#### 5. 循环导入

**症状：**
```
Error: Circular import detected: 'module_a' is already being loaded
```

**解决方案：**
- 重构模块结构，避免循环依赖
- 将共享代码提取到第三个模块
- 延迟导入（在函数内部导入）

#### 6. Python 导入错误

**症状：**
```
ImportError: cannot import name 'HPLModule'
```

**解决方案：**
```python
# 使用备用导入方式
try:
    from hpl_runtime.modules.base import HPLModule
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from hpl_runtime.modules.base import HPLModule
```

### 调试技巧

```python
# 添加日志
import logging
logger = logging.getLogger('my_module')

def my_function():
    logger.debug("Entering my_function")
    # ... 代码 ...
    logger.debug(f"Result: {result}")
    return result

# 在 HPL 中测试
# test.hpl:
# imports:
#   - my_module
# main: () => {
#   result = my_module.my_function()
#   echo(result)
# }
```

---

## 高级主题

### 1. 状态管理

```python
# stateful_module.py
"""有状态模块示例"""

HPL_MODULE = HPLModule("stateful", "有状态模块")

# 模块级状态
_state = {
    "counter": 0,
    "cache": {}
}

def get_counter():
    """获取计数器值"""
    return _state["counter"]

def increment():
    """增加计数器"""
    _state["counter"] += 1
    return _state["counter"]

def reset_counter():
    """重置计数器"""
    _state["counter"] = 0
    return 0

def get_from_cache(key):
    """从缓存获取"""
    return _state["cache"].get(key)

def set_in_cache(key, value):
    """设置缓存"""
    _state["cache"][key] = value
    return True

HPL_MODULE.register_function('get_counter', get_counter, 0, 'Get counter value')
HPL_MODULE.register_function('increment', increment, 0, 'Increment counter')
HPL_MODULE.register_function('reset_counter', reset_counter, 0, 'Reset counter')
HPL_MODULE.register_function('get_from_cache', get_from_cache, 1, 'Get from cache')
HPL_MODULE.register_function('set_in_cache', set_in_cache, 2, 'Set in cache')
```

### 2. 配置管理

```python
# configurable_module.py
"""可配置模块示例"""

# 默认配置
_config = {
    "timeout": 30,
    "retries": 3,
    "debug": False
}

def configure(options):
    """配置模块"""
    global _config
    if isinstance(options, dict):
        _config.update(options)
        return True
    return False

def get_config():
    """获取当前配置"""
    return _config.copy()

def set_timeout(seconds):
    """设置超时"""
    _config["timeout"] = seconds
    return True

# 使用配置的函数
def make_request(url):
    """发送请求（使用配置的超时）"""
    timeout = _config["timeout"]
    # ... 使用 timeout ...
    return result

HPL_MODULE = HPLModule("configurable", "可配置模块")
HPL_MODULE.register_function('configure', configure, 1, 'Configure module')
HPL_MODULE.register_function('get_config', get_config, 0, 'Get configuration')
HPL_MODULE.register_function('set_timeout', set_timeout, 1, 'Set timeout')
HPL_MODULE.register_function('make_request', make_request, 1, 'Make HTTP request')
```

### 3. 异步操作（高级）

```python
# async_module.py
"""异步操作示例（需要 HPL 支持）"""

import asyncio

async def async_fetch(url):
    """异步获取数据"""
    # 异步操作
    await asyncio.sleep(1)
    return f"Data from {url}"

def fetch_sync(url):
    """同步包装"""
    return asyncio.run(async_fetch(url))

HPL_MODULE = HPLModule("async_utils", "异步工具")
HPL_MODULE.register_function('fetch', fetch_sync, 1, 'Fetch data asynchronously')
```

### 4. 类封装

```python
# class_module.py
"""将 Python 类暴露给 HPL"""

class DataProcessor:
    """数据处理类"""
    def __init__(self, name):
        self.name = name
        self.data = []
    
    def add(self, item):
        self.data.append(item)
        return len(self.data)
    
    def process(self):
        return [x * 2 for x in self.data]
    
    def clear(self):
        self.data = []
        return True

# 存储实例
_instances = {}
_instance_counter = 0

def create_processor(name):
    """创建处理器实例"""
    global _instance_counter
    _instance_counter += 1
    instance_id = f"processor_{_instance_counter}"
    _instances[instance_id] = DataProcessor(name)
    return instance_id

def add_data(instance_id, item):
    """添加数据"""
    if instance_id not in _instances:
        raise HPLValueError(f"Instance {instance_id} not found")
    return _instances[instance_id].add(item)

def process_data(instance_id):
    """处理数据"""
    if instance_id not in _instances:
        raise HPLValueError(f"Instance {instance_id} not found")
    return _instances[instance_id].process()

def destroy_processor(instance_id):
    """销毁处理器"""
    if instance_id in _instances:
        del _instances[instance_id]
        return True
    return False

HPL_MODULE = HPLModule("class_wrapper", "类封装示例")
HPL_MODULE.register_function('create_processor', create_processor, 1, 'Create processor')
HPL_MODULE.register_function('add_data', add_data, 2, 'Add data to processor')
HPL_MODULE.register_function('process_data', process_data, 1, 'Process data')
HPL_MODULE.register_function('destroy_processor', destroy_processor, 1, 'Destroy processor')
```

### 5. 性能分析

```python
# profiled_module.py
"""带性能分析的模块"""

import time

def timed_function(func):
    """装饰器：记录函数执行时间"""
    def wrapper(*args):
        start = time.time()
        result = func(*args)
        elapsed = time.time() - start
        print(f"[PROFILE] {func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timed_function
def heavy_computation(n):
    """计算密集型函数"""
    total = 0
    for i in range(n):
        total += i * i
    return total

HPL_MODULE = HPLModule("profiled", "性能分析模块")
HPL_MODULE.register_function('heavy_computation', heavy_computation, 1, 'Heavy computation')
```

---

## 附录

### A. 完整模块模板

```python
#!/usr/bin/env python3
"""
模块名称
========

简要描述模块功能。

详细说明...

作者: Your Name
版本: 1.0.0
"""

# ============ 导入 ============
try:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import (
        HPLTypeError, 
        HPLValueError,
        HPLRuntimeError
    )
except ImportError:
    # 备用导入（当模块在 HPL 运行时目录外时）
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import (
        HPLTypeError, 
        HPLValueError,
        HPLRuntimeError
    )

# ============ 配置 ============
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# ============ 内部函数 ============
def _helper_function():
    """内部辅助函数（单下划线开头，不会暴露）"""
    pass

# ============ 公共函数 ============
def public_function():
    """公共 API"""
    pass

# ============ 模块注册 ============
HPL_MODULE = HPLModule("module_name", "Description")
HPL_MODULE.register_function('public_function', public_function, 0, 'Public function')

# ============ 版本信息 ============
__version__ = "1.0.0"
__author__ = "Your Name"
HPL_MODULE.register_constant('VERSION', __version__, 'Module version')
HPL_MODULE.register_constant('AUTHOR', __author__, 'Module author')
```

### B. 快速参考卡片

```python
# ===== 基本结构 =====
from hpl_runtime.modules.base import HPLModule
from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError

HPL_MODULE = HPLModule("my_module", "Description")

def my_func(arg):
    """函数文档"""
    if not isinstance(arg, int):
        raise HPLTypeError(f"Expected int, got {type(arg).__name__}")
    return arg * 2

HPL_MODULE.register_function('my_func', my_func, 1, 'Double a number')
HPL_MODULE.register_constant('PI', 3.14, 'Pi constant')

# ===== 自动接口（简单方式）=====
def greet(name):
    return f"Hello, {name}!"

APP_VERSION = "1.0.0"
# 无需 HPL_MODULE 定义，自动暴露所有非下划线开头的函数和变量
```

### C. 相关资源

- **HPL 标准库源码**: `hpl_runtime/stdlib/`
- **模块基类**: `hpl_runtime/modules/base.py`
- **模块加载器**: `hpl_runtime/modules/loader.py`
- **示例模块**: `examples/tests/my_python_module.py`

---

## 总结

本指南涵盖了 HPL 自定义 Python 模块开发的完整流程：

1. **自动接口** - 适合快速开发，自动暴露函数和常量
2. **显式接口** - 使用 `HPLModule` 精确控制 API
3. **错误处理** - 使用 HPL 原生异常类型
4. **实际示例** - 数据处理、文件操作、网络请求等
5. **最佳实践** - 命名规范、文档、版本管理
6. **故障排除** - 常见问题及解决方案
7. **高级主题** - 状态管理、配置、类封装等

通过自定义 Python 模块，您可以无限扩展 HPL 的功能，利用 Python 丰富的生态系统，同时保持 HPL 简洁的语法和易用性。

---

*文档版本: 1.0.0*
*最后更新: 2026年*
