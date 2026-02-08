"""
示例：自定义 Python 模块供 HPL 使用

这个模块展示了如何创建可以在 HPL 中导入的 Python 模块。
有两种方式：
1. 自动接口：直接定义函数和变量，HPL 会自动暴露
2. 显式接口：定义 HPL_MODULE 变量精确控制暴露的接口
"""

# 方式1：自动接口 - 直接定义函数和常量
def greet(name):
    """向用户问好"""
    return f"Hello, {name}! Welcome to HPL with Python modules."

def calculate(a, b, operation="add"):
    """执行数学运算"""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b if b != 0 else float('inf')
    else:
        return None

def process_list(items, operation="upper"):
    """处理列表"""
    if operation == "upper":
        return [str(item).upper() for item in items]
    elif operation == "lower":
        return [str(item).lower() for item in items]
    elif operation == "reverse":
        return list(reversed(items))
    elif operation == "sort":
        return sorted(items)
    else:
        return items

# 常量
APP_NAME = "MyPythonModule"
VERSION = "1.0.0"
MAX_ITEMS = 100

# 方式2：显式接口（可选）
# 如果要精确控制 HPL 中暴露的接口，可以创建 HPL_MODULE
"""
from hpl_runtime.module_base import HPLModule

HPL_MODULE = HPLModule("my_python_module", "Explicit HPL interface")

# 只注册特定的函数
HPL_MODULE.register_function('greet', greet, 1, 'Greet a user')
HPL_MODULE.register_function('calculate', calculate, None, 'Calculate with two numbers')

# 只注册特定的常量
HPL_MODULE.register_constant('APP_NAME', APP_NAME, 'Application name')
HPL_MODULE.register_constant('VERSION', VERSION, 'Version string')
"""
