"""
HPL 类型检查工具模块

该模块提供类型检查和验证相关的通用工具函数。
"""

try:
    from hpl_runtime.utils.exceptions import HPLTypeError
except ImportError:
    from exceptions import HPLTypeError


def is_numeric(value):

    """
    检查值是否为数值类型（int或float）
    
    Args:
        value: 要检查的值
    
    Returns:
        bool: 是否为数值类型
    """
    return isinstance(value, (int, float))


def is_integer(value):
    """
    检查值是否为整数类型
    
    Args:
        value: 要检查的值
    
    Returns:
        bool: 是否为整数类型
    """
    return isinstance(value, int)


def is_string(value):
    """
    检查值是否为字符串类型
    
    Args:
        value: 要检查的值
    
    Returns:
        bool: 是否为字符串类型
    """
    return isinstance(value, str)


def is_boolean(value):
    """
    检查值是否为布尔类型
    
    Args:
        value: 要检查的值
    
    Returns:
        bool: 是否为布尔类型
    """
    return isinstance(value, bool)


def is_array(value):
    """
    检查值是否为数组（列表）类型
    
    Args:
        value: 要检查的值
    
    Returns:
        bool: 是否为数组类型
    """
    return isinstance(value, list)


def is_dictionary(value):
    """
    检查值是否为字典类型
    
    Args:
        value: 要检查的值
    
    Returns:
        bool: 是否为字典类型
    """
    return isinstance(value, dict)


def check_numeric_operands(left, right, op):
    """
    检查操作数是否为数值类型
    
    Args:
        left: 左操作数
        right: 右操作数
        op: 操作符（用于错误消息）
    
    Raises:
        HPLTypeError: 如果操作数不是数值类型
    """
    if not is_numeric(left):
        raise HPLTypeError(f"Unsupported operand type for {op}: '{type(left).__name__}' (expected number)")
    if not is_numeric(right):
        raise HPLTypeError(f"Unsupported operand type for {op}: '{type(right).__name__}' (expected number)")



def is_hpl_module(obj):
    """
    检查对象是否是HPLModule（使用鸭子类型检查）
    
    Args:
        obj: 要检查的对象
    
    Returns:
        bool: 是否为HPL模块
    """
    # 使用鸭子类型检查，避免不同导入路径导致的类身份问题
    return hasattr(obj, 'call_function') and hasattr(obj, 'get_constant') and hasattr(obj, 'name')


def get_type_name(value):
    """
    获取值的类型名称（用于HPL类型系统）
    
    Args:
        value: 要检查的值
    
    Returns:
        str: 类型名称
    """
    if isinstance(value, bool):
        return 'boolean'
    elif isinstance(value, int):
        return 'int'
    elif isinstance(value, float):
        return 'float'
    elif isinstance(value, str):
        return 'string'
    elif isinstance(value, list):
        return 'array'
    else:
        return type(value).__name__


def is_valid_index(array, index):
    """
    检查索引是否对数组有效
    
    Args:
        array: 数组（列表）
        index: 索引值
    
    Returns:
        bool: 索引是否有效
    """
    return isinstance(index, int) and 0 <= index < len(array)


def check_type(value, expected_type, func_name, param_name, allow_none=False):
    """
    统一类型检查函数
    
    检查值是否为期望的类型，如果不是则抛出 HPLTypeError。
    这个函数用于统一 stdlib 模块中的类型检查，减少重复代码。
    
    Args:
        value: 要检查的值
        expected_type: 期望的类型（单个类型或类型元组）
        func_name: 函数名称（用于错误消息）
        param_name: 参数名称（用于错误消息）
        allow_none: 是否允许 None 值（默认为 False）
    
    Raises:
        HPLTypeError: 如果类型不匹配
    
    Examples:
        >>> check_type(s, str, 'length', 's')
        >>> check_type(count, (int, float), 'repeat', 'count')
    """
    if allow_none and value is None:
        return
    
    if not isinstance(value, expected_type):
        expected_name = _get_type_name(expected_type)
        actual_name = type(value).__name__
        raise HPLTypeError(
            f"{func_name}() requires {expected_name} for {param_name}, got {actual_name}"
        )


def _get_type_name(expected_type):
    """
    获取类型的友好名称
    
    Args:
        expected_type: 类型或类型元组
    
    Returns:
        str: 类型名称
    """
    if isinstance(expected_type, tuple):
        type_names = []
        for t in expected_type:
            if hasattr(t, '__name__'):
                type_names.append(t.__name__)
            else:
                type_names.append(str(t))
        return ' or '.join(type_names)
    elif hasattr(expected_type, '__name__'):
        return expected_type.__name__
    else:
        return str(expected_type)
