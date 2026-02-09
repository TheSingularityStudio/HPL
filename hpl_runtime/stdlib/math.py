"""
HPL 标准库 - math 模块

提供数学函数和常量。
"""

import math as _math

try:
    from hpl_runtime.modules.base import HPLModule
except ImportError:
    try:
        from hpl_runtime.modules.base import HPLModule
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from hpl_runtime.modules.base import HPLModule




# 基本数学函数
def sqrt(x):
    """计算平方根"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"sqrt() requires number, got {type(x).__name__}")
    if x < 0:
        raise ValueError("sqrt() requires non-negative number")
    return _math.sqrt(x)


def pow(base, exp):
    """计算幂"""
    if not isinstance(base, (int, float)):
        raise TypeError(f"pow() requires number for base, got {type(base).__name__}")
    if not isinstance(exp, (int, float)):
        raise TypeError(f"pow() requires number for exponent, got {type(exp).__name__}")
    return _math.pow(base, exp)


def sin(x):
    """计算正弦（弧度）"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"sin() requires number, got {type(x).__name__}")
    return _math.sin(x)


def cos(x):
    """计算余弦（弧度）"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"cos() requires number, got {type(x).__name__}")
    return _math.cos(x)


def tan(x):
    """计算正切（弧度）"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"tan() requires number, got {type(x).__name__}")
    return _math.tan(x)


def asin(x):
    """计算反正弦"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"asin() requires number, got {type(x).__name__}")
    if x < -1 or x > 1:
        raise ValueError("asin() requires value between -1 and 1")
    return _math.asin(x)


def acos(x):
    """计算反余弦"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"acos() requires number, got {type(x).__name__}")
    if x < -1 or x > 1:
        raise ValueError("acos() requires value between -1 and 1")
    return _math.acos(x)


def atan(x):
    """计算反正切"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"atan() requires number, got {type(x).__name__}")
    return _math.atan(x)


def atan2(y, x):
    """计算 atan(y/x)，考虑象限"""
    if not isinstance(y, (int, float)):
        raise TypeError(f"atan2() requires number for y, got {type(y).__name__}")
    if not isinstance(x, (int, float)):
        raise TypeError(f"atan2() requires number for x, got {type(x).__name__}")
    return _math.atan2(y, x)


def log(x, base=None):
    """计算对数"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"log() requires number, got {type(x).__name__}")
    if x <= 0:
        raise ValueError("log() requires positive number")
    
    if base is None:
        return _math.log(x)
    else:
        if not isinstance(base, (int, float)):
            raise TypeError(f"log() requires number for base, got {type(base).__name__}")
        if base <= 0 or base == 1:
            raise ValueError("log() requires positive base not equal to 1")
        return _math.log(x, base)


def log10(x):
    """计算常用对数（以10为底）"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"log10() requires number, got {type(x).__name__}")
    if x <= 0:
        raise ValueError("log10() requires positive number")
    return _math.log10(x)


def exp(x):
    """计算 e^x"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"exp() requires number, got {type(x).__name__}")
    return _math.exp(x)


def floor(x):
    """向下取整"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"floor() requires number, got {type(x).__name__}")
    return _math.floor(x)


def ceil(x):
    """向上取整"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"ceil() requires number, got {type(x).__name__}")
    return _math.ceil(x)


def round_num(x, ndigits=0):
    """四舍五入"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"round() requires number, got {type(x).__name__}")
    if not isinstance(ndigits, int):
        raise TypeError(f"round() requires int for ndigits, got {type(ndigits).__name__}")
    return round(x, ndigits)


def trunc(x):
    """截断小数部分"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"trunc() requires number, got {type(x).__name__}")
    return _math.trunc(x)


def factorial(n):
    """计算阶乘"""
    if not isinstance(n, int):
        raise TypeError(f"factorial() requires int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("factorial() requires non-negative integer")
    return _math.factorial(n)


def gcd(a, b):
    """计算最大公约数"""
    if not isinstance(a, int):
        raise TypeError(f"gcd() requires int for a, got {type(a).__name__}")
    if not isinstance(b, int):
        raise TypeError(f"gcd() requires int for b, got {type(b).__name__}")
    return _math.gcd(a, b)


def degrees(x):
    """弧度转角度"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"degrees() requires number, got {type(x).__name__}")
    return _math.degrees(x)


def radians(x):
    """角度转弧度"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"radians() requires number, got {type(x).__name__}")
    return _math.radians(x)


def pi():
    """返回圆周率"""
    return _math.pi


def e():
    """返回自然常数 e"""
    return _math.e


def tau():
    """返回 2*pi"""
    return _math.tau


def inf():
    """返回正无穷大"""
    return _math.inf


def nan():
    """返回非数字"""
    return _math.nan


def is_nan(x):
    """检查是否为 NaN"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"is_nan() requires number, got {type(x).__name__}")
    return _math.isnan(x)


def is_inf(x):
    """检查是否为无穷大"""
    if not isinstance(x, (int, float)):
        raise TypeError(f"is_inf() requires number, got {type(x).__name__}")
    return _math.isinf(x)


# 创建模块实例
module = HPLModule('math', 'Mathematical functions and constants')

# 注册函数
module.register_function('sqrt', sqrt, 1, 'Square root')
module.register_function('pow', pow, 2, 'Power function')
module.register_function('sin', sin, 1, 'Sine (radians)')
module.register_function('cos', cos, 1, 'Cosine (radians)')
module.register_function('tan', tan, 1, 'Tangent (radians)')
module.register_function('asin', asin, 1, 'Arc sine')
module.register_function('acos', acos, 1, 'Arc cosine')
module.register_function('atan', atan, 1, 'Arc tangent')
module.register_function('atan2', atan2, 2, 'Arc tangent with two arguments')
module.register_function('log', log, None, 'Logarithm (optional base)')
module.register_function('log10', log10, 1, 'Base-10 logarithm')
module.register_function('exp', exp, 1, 'Exponential function')
module.register_function('floor', floor, 1, 'Floor function')
module.register_function('ceil', ceil, 1, 'Ceiling function')
module.register_function('round', round_num, None, 'Round to nearest (optional ndigits)')
module.register_function('trunc', trunc, 1, 'Truncate decimal part')
module.register_function('factorial', factorial, 1, 'Factorial')
module.register_function('gcd', gcd, 2, 'Greatest common divisor')
module.register_function('degrees', degrees, 1, 'Radians to degrees')
module.register_function('radians', radians, 1, 'Degrees to radians')

# 注册常量
module.register_constant('PI', _math.pi, 'Pi constant')
module.register_constant('E', _math.e, 'Euler\'s number')
module.register_constant('TAU', _math.tau, '2*Pi')
module.register_constant('INF', _math.inf, 'Positive infinity')
module.register_constant('NAN', _math.nan, 'Not a number')
