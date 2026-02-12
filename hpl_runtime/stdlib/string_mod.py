"""
HPL 标准库 - string 模块

提供字符串处理功能。
"""

import re as _re

try:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError
except ImportError:
    try:
        from hpl_runtime.modules.base import HPLModule
        from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from hpl_runtime.modules.base import HPLModule
        from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError


# 基础字符串操作

def length(s):
    """获取字符串长度"""
    if not isinstance(s, str):
        raise HPLTypeError(f"length() requires string, got {type(s).__name__}")
    return len(s)


def split(s, delimiter=None, maxsplit=-1):
    """分割字符串为数组"""
    if not isinstance(s, str):
        raise HPLTypeError(f"split() requires string, got {type(s).__name__}")
    if delimiter is not None and not isinstance(delimiter, str):
        raise HPLTypeError(f"split() requires string delimiter, got {type(delimiter).__name__}")
    if maxsplit is not None and not isinstance(maxsplit, int):
        raise HPLTypeError(f"split() requires int maxsplit, got {type(maxsplit).__name__}")
    
    if delimiter is None:
        return s.split()
    return s.split(delimiter, maxsplit)


def join(array, delimiter=""):
    """使用分隔符连接字符串数组"""
    if not isinstance(array, list):
        raise HPLTypeError(f"join() requires array, got {type(array).__name__}")
    if not isinstance(delimiter, str):
        raise HPLTypeError(f"join() requires string delimiter, got {type(delimiter).__name__}")
    
    # 将所有元素转换为字符串
    str_items = [str(item) for item in array]
    return delimiter.join(str_items)


def replace(s, old, new, count=-1):
    """替换字符串中的子串"""
    if not isinstance(s, str):
        raise HPLTypeError(f"replace() requires string, got {type(s).__name__}")
    if not isinstance(old, str):
        raise HPLTypeError(f"replace() requires string old, got {type(old).__name__}")
    if not isinstance(new, str):
        raise HPLTypeError(f"replace() requires string new, got {type(new).__name__}")
    if not isinstance(count, int):
        raise HPLTypeError(f"replace() requires int count, got {type(count).__name__}")
    
    if count < 0:
        return s.replace(old, new)
    return s.replace(old, new, count)


def trim(s, chars=None):
    """去除字符串首尾空白或指定字符"""
    if not isinstance(s, str):
        raise HPLTypeError(f"trim() requires string, got {type(s).__name__}")
    
    if chars is None:
        return s.strip()
    if not isinstance(chars, str):
        raise HPLTypeError(f"trim() requires string chars, got {type(chars).__name__}")
    return s.strip(chars)


def trim_start(s, chars=None):
    """去除字符串开头空白或指定字符"""
    if not isinstance(s, str):
        raise HPLTypeError(f"trim_start() requires string, got {type(s).__name__}")
    
    if chars is None:
        return s.lstrip()
    if not isinstance(chars, str):
        raise HPLTypeError(f"trim_start() requires string chars, got {type(chars).__name__}")
    return s.lstrip(chars)


def trim_end(s, chars=None):
    """去除字符串结尾空白或指定字符"""
    if not isinstance(s, str):
        raise HPLTypeError(f"trim_end() requires string, got {type(s).__name__}")
    
    if chars is None:
        return s.rstrip()
    if not isinstance(chars, str):
        raise HPLTypeError(f"trim_end() requires string chars, got {type(chars).__name__}")
    return s.rstrip(chars)


def to_upper(s):
    """将字符串转为大写"""
    if not isinstance(s, str):
        raise HPLTypeError(f"to_upper() requires string, got {type(s).__name__}")
    return s.upper()


def to_lower(s):
    """将字符串转为小写"""
    if not isinstance(s, str):
        raise HPLTypeError(f"to_lower() requires string, got {type(s).__name__}")
    return s.lower()


def substring(s, start, end=None):
    """截取子字符串"""
    if not isinstance(s, str):
        raise HPLTypeError(f"substring() requires string, got {type(s).__name__}")
    if not isinstance(start, int):
        raise HPLTypeError(f"substring() requires int start, got {type(start).__name__}")
    
    if end is None:
        return s[start:]
    if not isinstance(end, int):
        raise HPLTypeError(f"substring() requires int end, got {type(end).__name__}")
    return s[start:end]


def index_of(s, substr, start=0):
    """查找子串位置，未找到返回-1"""
    if not isinstance(s, str):
        raise HPLTypeError(f"index_of() requires string, got {type(s).__name__}")
    if not isinstance(substr, str):
        raise HPLTypeError(f"index_of() requires string substr, got {type(substr).__name__}")
    if not isinstance(start, int):
        raise HPLTypeError(f"index_of() requires int start, got {type(start).__name__}")
    
    return s.find(substr, start)


def last_index_of(s, substr, start=0):
    """从后往前查找子串位置，未找到返回-1"""
    if not isinstance(s, str):
        raise HPLTypeError(f"last_index_of() requires string, got {type(s).__name__}")
    if not isinstance(substr, str):
        raise HPLTypeError(f"last_index_of() requires string substr, got {type(substr).__name__}")
    if not isinstance(start, int):
        raise HPLTypeError(f"last_index_of() requires int start, got {type(start).__name__}")
    
    return s.rfind(substr, start)


def starts_with(s, prefix):
    """检查字符串是否以指定前缀开头"""
    if not isinstance(s, str):
        raise HPLTypeError(f"starts_with() requires string, got {type(s).__name__}")
    if not isinstance(prefix, str):
        raise HPLTypeError(f"starts_with() requires string prefix, got {type(prefix).__name__}")
    
    return s.startswith(prefix)


def ends_with(s, suffix):
    """检查字符串是否以指定后缀结尾"""
    if not isinstance(s, str):
        raise HPLTypeError(f"ends_with() requires string, got {type(s).__name__}")
    if not isinstance(suffix, str):
        raise HPLTypeError(f"ends_with() requires string suffix, got {type(suffix).__name__}")
    
    return s.endswith(suffix)


def contains(s, substr):
    """检查字符串是否包含子串"""
    if not isinstance(s, str):
        raise HPLTypeError(f"contains() requires string, got {type(s).__name__}")
    if not isinstance(substr, str):
        raise HPLTypeError(f"contains() requires string substr, got {type(substr).__name__}")
    
    return substr in s


def reverse(s):
    """反转字符串"""
    if not isinstance(s, str):
        raise HPLTypeError(f"reverse() requires string, got {type(s).__name__}")
    return s[::-1]


def repeat(s, count):
    """重复字符串指定次数"""
    if not isinstance(s, str):
        raise HPLTypeError(f"repeat() requires string, got {type(s).__name__}")
    if not isinstance(count, int):
        raise HPLTypeError(f"repeat() requires int count, got {type(count).__name__}")
    if count < 0:
        raise HPLValueError("repeat() requires non-negative count")
    
    return s * count


def pad_start(s, length, pad=" "):
    """在字符串开头填充字符至指定长度"""
    if not isinstance(s, str):
        raise HPLTypeError(f"pad_start() requires string, got {type(s).__name__}")
    if not isinstance(length, int):
        raise HPLTypeError(f"pad_start() requires int length, got {type(length).__name__}")
    if not isinstance(pad, str):
        raise HPLTypeError(f"pad_start() requires string pad, got {type(pad).__name__}")
    if len(pad) == 0:
        raise HPLValueError("pad_start() requires non-empty pad string")
    
    if len(s) >= length:
        return s
    padding_needed = length - len(s)
    padding = (pad * ((padding_needed // len(pad)) + 1))[:padding_needed]
    return padding + s


def pad_end(s, length, pad=" "):
    """在字符串结尾填充字符至指定长度"""
    if not isinstance(s, str):
        raise HPLTypeError(f"pad_end() requires string, got {type(s).__name__}")
    if not isinstance(length, int):
        raise HPLTypeError(f"pad_end() requires int length, got {type(length).__name__}")
    if not isinstance(pad, str):
        raise HPLTypeError(f"pad_end() requires string pad, got {type(pad).__name__}")
    if len(pad) == 0:
        raise HPLValueError("pad_end() requires non-empty pad string")
    
    if len(s) >= length:
        return s
    padding_needed = length - len(s)
    padding = (pad * ((padding_needed // len(pad)) + 1))[:padding_needed]
    return s + padding


def count(s, substr):
    """统计子串出现次数"""
    if not isinstance(s, str):
        raise HPLTypeError(f"count() requires string, got {type(s).__name__}")
    if not isinstance(substr, str):
        raise HPLTypeError(f"count() requires string substr, got {type(substr).__name__}")
    if len(substr) == 0:
        raise HPLValueError("count() requires non-empty substr")
    
    return s.count(substr)


def is_empty(s):
    """检查字符串是否为空"""
    if not isinstance(s, str):
        raise HPLTypeError(f"is_empty() requires string, got {type(s).__name__}")
    return len(s) == 0


def is_blank(s):
    """检查字符串是否为空或仅包含空白字符"""
    if not isinstance(s, str):
        raise HPLTypeError(f"is_blank() requires string, got {type(s).__name__}")
    return len(s.strip()) == 0


def capitalize(s):
    """将字符串首字母大写"""
    if not isinstance(s, str):
        raise HPLTypeError(f"capitalize() requires string, got {type(s).__name__}")
    return s.capitalize()


def title_case(s):
    """将字符串每个单词首字母大写"""
    if not isinstance(s, str):
        raise HPLTypeError(f"title_case() requires string, got {type(s).__name__}")
    return s.title()


def swap_case(s):
    """交换字符串大小写"""
    if not isinstance(s, str):
        raise HPLTypeError(f"swap_case() requires string, got {type(s).__name__}")
    return s.swapcase()


def format_template(template, *args, **kwargs):
    """格式化字符串模板"""
    if not isinstance(template, str):
        raise HPLTypeError(f"format() requires string template, got {type(template).__name__}")
    
    # 支持位置参数和命名参数
    try:
        if args:
            return template.format(*args)
        return template.format(**kwargs)
    except (KeyError, IndexError) as e:
        raise HPLValueError(f"Format error: {e}")


# 创建模块实例
module = HPLModule('string', 'String manipulation functions')

# 注册函数
module.register_function('length', length, 1, 'Get string length')
module.register_function('split', split, None, 'Split string by delimiter (optional maxsplit)')
module.register_function('join', join, None, 'Join array with delimiter')
module.register_function('replace', replace, None, 'Replace substring (optional count)')
module.register_function('trim', trim, None, 'Trim whitespace (optional chars)')
module.register_function('trim_start', trim_start, None, 'Trim start whitespace (optional chars)')
module.register_function('trim_end', trim_end, None, 'Trim end whitespace (optional chars)')
module.register_function('to_upper', to_upper, 1, 'Convert to uppercase')
module.register_function('to_lower', to_lower, 1, 'Convert to lowercase')
module.register_function('substring', substring, None, 'Get substring (optional end)')
module.register_function('index_of', index_of, None, 'Find substring index (optional start)')
module.register_function('last_index_of', last_index_of, None, 'Find last substring index (optional start)')
module.register_function('starts_with', starts_with, 2, 'Check if starts with prefix')
module.register_function('ends_with', ends_with, 2, 'Check if ends with suffix')
module.register_function('contains', contains, 2, 'Check if contains substring')
module.register_function('reverse', reverse, 1, 'Reverse string')
module.register_function('repeat', repeat, 2, 'Repeat string count times')
module.register_function('pad_start', pad_start, None, 'Pad string at start (optional pad char)')
module.register_function('pad_end', pad_end, None, 'Pad string at end (optional pad char)')
module.register_function('count', count, 2, 'Count substring occurrences')
module.register_function('is_empty', is_empty, 1, 'Check if string is empty')
module.register_function('is_blank', is_blank, 1, 'Check if string is blank')
module.register_function('capitalize', capitalize, 1, 'Capitalize first letter')
module.register_function('title_case', title_case, 1, 'Title case each word')
module.register_function('swap_case', swap_case, 1, 'Swap case of each letter')

