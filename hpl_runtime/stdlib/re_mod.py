"""
HPL 标准库 - re 模块 (正则表达式)

提供正则表达式匹配、搜索、替换等功能。
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


# 编译缓存，提高重复使用的性能
_compile_cache = {}


def _get_flags(flags_str=None):
    """将标志字符串转换为正则标志"""
    if flags_str is None:
        return 0
    
    if not isinstance(flags_str, str):
        raise HPLTypeError(f"flags must be string, got {type(flags_str).__name__}")
    
    flags = 0
    flag_map = {
        'i': _re.IGNORECASE,      # 忽略大小写
        'm': _re.MULTILINE,       # 多行模式
        's': _re.DOTALL,          # 点匹配所有字符包括换行
        'x': _re.VERBOSE,         # 详细模式
        'a': _re.ASCII,           # ASCII匹配
        'u': _re.UNICODE,         # Unicode匹配（默认）
        'l': _re.LOCALE,          # 本地化匹配
    }
    
    for char in flags_str.lower():
        if char in flag_map:
            flags |= flag_map[char]
        else:
            raise HPLValueError(f"Unknown flag: '{char}'. Valid flags: i, m, s, x, a, u, l")
    
    return flags


def _compile_pattern(pattern, flags=0):
    """编译正则表达式，使用缓存"""
    cache_key = (pattern, flags)
    if cache_key not in _compile_cache:
        _compile_cache[cache_key] = _re.compile(pattern, flags)
    return _compile_cache[cache_key]


def match(pattern, string, flags=None):
    """
    从字符串开头匹配正则表达式
    
    返回匹配对象或null
    """
    if not isinstance(pattern, str):
        raise HPLTypeError(f"match() requires string pattern, got {type(pattern).__name__}")
    if not isinstance(string, str):
        raise HPLTypeError(f"match() requires string, got {type(string).__name__}")
    
    try:
        flag_val = _get_flags(flags)
        compiled = _compile_pattern(pattern, flag_val)
        m = compiled.match(string)
        if m:
            return {
                'group': m.group(),
                'groups': list(m.groups()),
                'start': m.start(),
                'end': m.end(),
                'span': list(m.span())
            }
        return None
    except _re.error as e:
        raise HPLValueError(f"Invalid regex pattern: {e}")


def search(pattern, string, flags=None):
    """
    在字符串中搜索正则表达式
    
    返回第一个匹配对象或null
    """
    if not isinstance(pattern, str):
        raise HPLTypeError(f"search() requires string pattern, got {type(pattern).__name__}")
    if not isinstance(string, str):
        raise HPLTypeError(f"search() requires string, got {type(string).__name__}")
    
    try:
        flag_val = _get_flags(flags)
        compiled = _compile_pattern(pattern, flag_val)
        m = compiled.search(string)
        if m:
            return {
                'group': m.group(),
                'groups': list(m.groups()),
                'start': m.start(),
                'end': m.end(),
                'span': list(m.span())
            }
        return None
    except _re.error as e:
        raise HPLValueError(f"Invalid regex pattern: {e}")


def find_all(pattern, string, flags=None):
    """
    查找所有匹配项
    
    返回匹配字符串数组
    """
    if not isinstance(pattern, str):
        raise HPLTypeError(f"find_all() requires string pattern, got {type(pattern).__name__}")
    if not isinstance(string, str):
        raise HPLTypeError(f"find_all() requires string, got {type(string).__name__}")
    
    try:
        flag_val = _get_flags(flags)
        compiled = _compile_pattern(pattern, flag_val)
        return compiled.findall(string)
    except _re.error as e:
        raise HPLValueError(f"Invalid regex pattern: {e}")


def find_iter(pattern, string, flags=None):
    """
    查找所有匹配项（返回详细信息）
    
    返回匹配对象数组
    """
    if not isinstance(pattern, str):
        raise HPLTypeError(f"find_iter() requires string pattern, got {type(pattern).__name__}")
    if not isinstance(string, str):
        raise HPLTypeError(f"find_iter() requires string, got {type(string).__name__}")
    
    try:
        flag_val = _get_flags(flags)
        compiled = _compile_pattern(pattern, flag_val)
        results = []
        for m in compiled.finditer(string):
            results.append({
                'group': m.group(),
                'groups': list(m.groups()),
                'start': m.start(),
                'end': m.end(),
                'span': list(m.span())
            })
        return results
    except _re.error as e:
        raise HPLValueError(f"Invalid regex pattern: {e}")


def replace(pattern, repl, string, count=0, flags=None):
    """
    替换匹配项
    
    count=0表示替换所有
    """
    if not isinstance(pattern, str):
        raise HPLTypeError(f"replace() requires string pattern, got {type(pattern).__name__}")
    if not isinstance(repl, str):
        raise HPLTypeError(f"replace() requires string repl, got {type(repl).__name__}")
    if not isinstance(string, str):
        raise HPLTypeError(f"replace() requires string, got {type(string).__name__}")
    if not isinstance(count, int):
        raise HPLTypeError(f"replace() requires int count, got {type(count).__name__}")
    
    try:
        flag_val = _get_flags(flags)
        compiled = _compile_pattern(pattern, flag_val)
        return compiled.sub(repl, string, count)
    except _re.error as e:
        raise HPLValueError(f"Invalid regex pattern: {e}")


def split(pattern, string, maxsplit=0, flags=None):
    """
    使用正则表达式分割字符串
    
    返回分割后的字符串数组
    """
    if not isinstance(pattern, str):
        raise HPLTypeError(f"split() requires string pattern, got {type(pattern).__name__}")
    if not isinstance(string, str):
        raise HPLTypeError(f"split() requires string, got {type(string).__name__}")
    if not isinstance(maxsplit, int):
        raise HPLTypeError(f"split() requires int maxsplit, got {type(maxsplit).__name__}")
    
    try:
        flag_val = _get_flags(flags)
        compiled = _compile_pattern(pattern, flag_val)
        return compiled.split(string, maxsplit)
    except _re.error as e:
        raise HPLValueError(f"Invalid regex pattern: {e}")


def test(pattern, string, flags=None):
    """
    测试字符串是否匹配正则表达式
    
    返回布尔值
    """
    if not isinstance(pattern, str):
        raise HPLTypeError(f"test() requires string pattern, got {type(pattern).__name__}")
    if not isinstance(string, str):
        raise HPLTypeError(f"test() requires string, got {type(string).__name__}")
    
    try:
        flag_val = _get_flags(flags)
        compiled = _compile_pattern(pattern, flag_val)
        return compiled.search(string) is not None
    except _re.error as e:
        raise HPLValueError(f"Invalid regex pattern: {e}")


def escape(string):
    """
    转义字符串中的正则表达式特殊字符
    
    返回转义后的字符串
    """
    if not isinstance(string, str):
        raise HPLTypeError(f"escape() requires string, got {type(string).__name__}")
    
    return _re.escape(string)


def compile_pattern(pattern, flags=None):
    """
    预编译正则表达式（返回可重用的模式对象）
    
    返回模式对象（在HPL中以字典形式表示）
    """
    if not isinstance(pattern, str):
        raise HPLTypeError(f"compile() requires string pattern, got {type(pattern).__name__}")
    
    try:
        flag_val = _get_flags(flags)
        compiled = _compile_pattern(pattern, flag_val)
        # 返回模式信息，实际使用时需要重新编译
        return {
            'pattern': pattern,
            'flags': flags or '',
            'groups': compiled.groups
        }
    except _re.error as e:
        raise HPLValueError(f"Invalid regex pattern: {e}")


# 常用正则表达式模式
PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'url': r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+',
    'ip': r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',
    'phone': r'^1[3-9]\d{9}$',  # 中国大陆手机号
    'id_card': r'^\d{17}[\dXx]$',  # 中国大陆身份证
    'chinese': r'[\u4e00-\u9fa5]',
    'english': r'[a-zA-Z]',
    'number': r'\d+',
    'whitespace': r'\s+',
    'word': r'\w+',
}


def validate(pattern_name, string):
    """
    使用预定义模式验证字符串
    
    支持的pattern_name: email, url, ip, phone, id_card, chinese, english, number, whitespace, word
    """
    if not isinstance(pattern_name, str):
        raise HPLTypeError(f"validate() requires string pattern_name, got {type(pattern_name).__name__}")
    if not isinstance(string, str):
        raise HPLTypeError(f"validate() requires string, got {type(string).__name__}")
    
    if pattern_name not in PATTERNS:
        available = ', '.join(PATTERNS.keys())
        raise HPLValueError(f"Unknown pattern: '{pattern_name}'. Available: {available}")
    
    pattern = PATTERNS[pattern_name]
    return test(pattern, string)


# 创建模块实例
module = HPLModule('re', 'Regular expression operations')

# 注册函数
module.register_function('match', match, None, 'Match pattern at start of string')
module.register_function('search', search, None, 'Search for pattern in string')
module.register_function('find_all', find_all, None, 'Find all matches')
module.register_function('find_iter', find_iter, None, 'Find all matches with details')
module.register_function('replace', replace, None, 'Replace matches (optional count)')
module.register_function('split', split, None, 'Split by pattern (optional maxsplit)')
module.register_function('test', test, None, 'Test if pattern matches')
module.register_function('escape', escape, 1, 'Escape special regex characters')
module.register_function('compile', compile_pattern, None, 'Compile pattern for reuse')

# 注册验证函数
module.register_function('validate', validate, 2, 'Validate with predefined patterns')

# 注册常用模式常量
for name, pattern in PATTERNS.items():
    module.register_constant(f'PATTERN_{name.upper()}', pattern, f'Pattern for matching {name}')
