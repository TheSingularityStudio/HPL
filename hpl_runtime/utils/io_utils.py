"""
HPL IO工具模块

该模块提供输入输出相关的通用工具函数。
"""


def echo(message):
    """
    输出消息到控制台
    
    Args:
        message: 要输出的消息（会被转换为字符串）
    """
    print(message, flush=True)



def read_input(prompt=None):
    """
    读取用户输入
    
    Args:
        prompt: 提示信息（可选）
    
    Returns:
        str: 用户输入的字符串
    
    Raises:
        EOFError: 当到达文件末尾时
    """
    if prompt is not None:
        return input(prompt)
    return input()


def format_output(value, indent=0):
    """
    格式化输出值（用于调试或显示）
    
    Args:
        value: 要格式化的值
        indent: 缩进级别
    
    Returns:
        str: 格式化后的字符串
    """
    indent_str = "  " * indent
    
    if isinstance(value, dict):
        lines = [f"{indent_str}{{"]
        for k, v in value.items():
            formatted_v = format_output(v, indent + 1)
            lines.append(f"{indent_str}  {k}: {formatted_v}")
        lines.append(f"{indent_str}}}")
        return "\n".join(lines)
    elif isinstance(value, list):
        lines = [f"{indent_str}["]
        for item in value:
            formatted_item = format_output(item, indent + 1)
            lines.append(f"{indent_str}  {formatted_item}")
        lines.append(f"{indent_str}]")
        return "\n".join(lines)
    else:
        return f"{indent_str}{value}"
