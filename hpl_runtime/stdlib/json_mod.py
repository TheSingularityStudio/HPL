"""
HPL 标准库 - json 模块

提供 JSON 解析和生成功能。
"""

import json as _json

try:
    from hpl_runtime.module_base import HPLModule
except ImportError:
    try:
        from module_base import HPLModule
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from module_base import HPLModule




def parse(json_str):
    """解析 JSON 字符串为 HPL 值"""
    if not isinstance(json_str, str):
        raise TypeError(f"parse() requires string, got {type(json_str).__name__}")
    
    try:
        result = _json.loads(json_str)
        # 将 Python 类型转换为 HPL 兼容类型
        return _convert_to_hpl(result)
    except _json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def stringify(value, indent=None):
    """将 HPL 值转换为 JSON 字符串"""
    # 将 HPL 值转换为 Python 值
    py_value = _convert_from_hpl(value)
    
    try:
        if indent is not None:
            if not isinstance(indent, int):
                raise TypeError(f"stringify() indent must be int, got {type(indent).__name__}")
            return _json.dumps(py_value, indent=indent, ensure_ascii=False)
        return _json.dumps(py_value, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot convert to JSON: {e}")


def read_json(path):
    """从文件读取 JSON"""
    if not isinstance(path, str):
        raise TypeError(f"read_json() requires string path, got {type(path).__name__}")
    
    import os
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return parse(content)


def write_json(path, value, indent=None):
    """将值写入 JSON 文件"""
    if not isinstance(path, str):
        raise TypeError(f"write_json() requires string path, got {type(path).__name__}")
    
    json_str = stringify(value, indent)
    
    import os
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    return True


def _convert_to_hpl(value):
    """将 Python 值转换为 HPL 兼容值"""
    if value is None:
        return None
    elif isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return value
    elif isinstance(value, float):
        return value
    elif isinstance(value, str):
        return value
    elif isinstance(value, list):
        return [_convert_to_hpl(item) for item in value]
    elif isinstance(value, dict):
        # HPL 使用数组，将字典转换为键值对数组
        return [[k, _convert_to_hpl(v)] for k, v in value.items()]
    else:
        return str(value)


def _convert_from_hpl(value):
    """将 HPL 值转换为 Python 值"""
    if value is None:
        return None
    elif isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return value
    elif isinstance(value, float):
        return value
    elif isinstance(value, str):
        return value
    elif isinstance(value, list):
        # 检查是否是键值对数组（字典）
        if len(value) > 0 and isinstance(value[0], list) and len(value[0]) == 2:
            try:
                return {k: _convert_from_hpl(v) for k, v in value}
            except (TypeError, ValueError):
                pass
        return [_convert_from_hpl(item) for item in value]
    else:
        return str(value)


def is_valid(json_str):
    """检查字符串是否为有效 JSON"""
    if not isinstance(json_str, str):
        return False
    
    try:
        _json.loads(json_str)
        return True
    except _json.JSONDecodeError:
        return False


# 创建模块实例
module = HPLModule('json', 'JSON parsing and generation')

# 注册函数
module.register_function('parse', parse, 1, 'Parse JSON string to HPL value')
module.register_function('stringify', stringify, None, 'Convert HPL value to JSON string (optional indent)')
module.register_function('read', read_json, 1, 'Read and parse JSON from file')
module.register_function('write', write_json, None, 'Write value to JSON file (optional indent)')
module.register_function('is_valid', is_valid, 1, 'Check if string is valid JSON')
