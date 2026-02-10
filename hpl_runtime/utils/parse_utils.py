"""
HPL 解析辅助工具模块

该模块提供解析器相关的辅助工具函数。
"""


def get_token_position(token):
    """
    获取token的位置信息
    
    Args:
        token: Token对象
    
    Returns:
        tuple: (行号, 列号)，如果token为None则返回(None, None)
    """
    if token:
        return getattr(token, 'line', None), getattr(token, 'column', None)
    return None, None


def is_block_terminator(token, peek_func=None, indent_level=0):
    """
    检查当前token是否是块结束标记
    
    Args:
        token: 当前token
        peek_func: 查看下一个token的函数（可选）
        indent_level: 当前缩进级别
    
    Returns:
        bool: 是否为块终止符
    """
    if not token:
        return True
    
    if token.type in ['RBRACE', 'EOF']:
        return True
    
    # DEDENT 只有在当前缩进级别小于块开始时的级别时才视为终止符
    if token.type == 'DEDENT':
        # 首先检查DEDENT的值是否小于当前缩进级别
        # 注意：DEDENT的value表示新的缩进级别
        if hasattr(token, 'value') and token.value is not None:
            if token.value < indent_level:
                return True
        else:
            # 如果DEDENT没有value属性，保守地视为终止符
            # 因为DEDENT表示缩进减少，可能已退出当前块
            return True
        
        # 检查下一个非DEDENT token是否是RBRACE
        if peek_func:
            offset = 1
            next_token = peek_func(offset)
            while next_token and next_token.type == 'DEDENT':
                offset += 1
                next_token = peek_func(offset)
            # 如果DEDENT后面跟着RBRACE或EOF，则视为终止符
            if next_token and next_token.type in ['RBRACE', 'EOF']:
                return True
            # 如果DEDENT后面跟着else/catch，则视为终止符
            if next_token and next_token.type == 'KEYWORD' and next_token.value in ['else', 'catch']:
                return True
        # 否则，DEDENT只是缩进变化，不是块终止符
        return False


    
    if token.type == 'KEYWORD' and token.value in ['else', 'catch']:
        return True
    
    return False


def consume_indent(tokens, pos):
    """
    消费INDENT token（如果存在）
    
    Args:
        tokens: token列表
        pos: 当前位置
    
    Returns:
        int: 新的位置（如果消费了INDENT则+1，否则不变）
    """
    if pos < len(tokens) and tokens[pos].type == 'INDENT':
        return pos + 1
    return pos


def skip_dedents(tokens, pos):
    """
    跳过连续的DEDENT token
    
    Args:
        tokens: token列表
        pos: 当前位置
    
    Returns:
        int: 跳过DEDENT后的新位置
    """
    while pos < len(tokens) and tokens[pos].type == 'DEDENT':
        pos += 1
    return pos


def find_matching_brace(text, start_pos, open_char='{', close_char='}'):
    """
    查找匹配的闭合括号位置
    
    Args:
        text: 文本字符串
        start_pos: 起始位置（开括号位置）
        open_char: 开括号字符
        close_char: 闭括号字符
    
    Returns:
        int: 闭括号位置，如果未找到则返回-1
    """
    brace_count = 1
    pos = start_pos + 1
    
    while pos < len(text) and brace_count > 0:
        if text[pos] == open_char:
            brace_count += 1
        elif text[pos] == close_char:
            brace_count -= 1
        pos += 1
    
    return pos - 1 if brace_count == 0 else -1


def extract_params_from_signature(sig_str):
    """
    从函数签名中提取参数列表
    
    Args:
        sig_str: 参数字符串，如 "(x, y, z)"
    
    Returns:
        list: 参数名列表
    """
    sig_str = sig_str.strip()
    if sig_str.startswith('(') and sig_str.endswith(')'):
        sig_str = sig_str[1:-1]
    
    if not sig_str:
        return []
    
    return [p.strip() for p in sig_str.split(',') if p.strip()]
