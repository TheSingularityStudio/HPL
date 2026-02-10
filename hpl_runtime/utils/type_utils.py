"""
HPL 类型检查工具模块

该模块提供类型检查和验证相关的通用工具函数。
"""


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
        TypeError: 如果操作数不是数值类型
    """
    if not is_numeric(left):
        raise TypeError(f"Unsupported operand type for {op}: '{type(left).__name__}' (expected number)")
    if not is_numeric(right):
        raise TypeError(f"Unsupported operand type for {op}: '{type(right).__name__}' (expected number)")


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
