"""
HPL 文本处理工具模块

该模块提供文本处理和字符串操作相关的通用工具函数。
"""

import re


def skip_whitespace(text, pos, skip_newline=False):
    """
    跳过空白字符
    
    Args:
        text: 文本字符串
        pos: 当前位置
        skip_newline: 是否跳过换行符
    
    Returns:
        int: 跳过空白后的新位置
    """
    while pos < len(text) and text[pos].isspace():
        if not skip_newline and text[pos] == '\n':
            break
        pos += 1
    return pos


def skip_comment(text, pos, comment_char='#'):
    """
    跳过从当前位置到行尾的注释
    
    Args:
        text: 文本字符串
        pos: 当前位置
        comment_char: 注释起始字符
    
    Returns:
        int: 跳过注释后的新位置（行尾或字符串结尾）
    """
    while pos < len(text) and text[pos] != '\n':
        pos += 1
    return pos


def strip_inline_comment(line):
    """
    从代码行中移除内联注释（但保留字符串中的#）
    
    Args:
        line: 代码行字符串
    
    Returns:
        str: 移除内联注释后的行
    """
    result = []
    in_string = False
    string_char = None
    i = 0
    
    while i < len(line):
        char = line[i]
        
        # 处理字符串
        if char in ('"', "'"):
            if not in_string:
                in_string = True
                string_char = char
            elif string_char == char:
                # 检查是否是转义（前面有奇数个反斜杠）
                backslash_count = 0
                j = i - 1
                while j >= 0 and line[j] == '\\':
                    backslash_count += 1
                    j -= 1
                if backslash_count % 2 == 0:  # 不是转义
                    in_string = False
                    string_char = None
        
        # 如果在字符串外遇到#，这是注释开始
        if not in_string and char == '#':
            break
        
        result.append(char)
        i += 1
    
    return ''.join(result).rstrip()


def preprocess_functions(content):
    """
    预处理函数定义，将其转换为 YAML 字面量块格式
    这样 YAML 就不会解析函数体内部的语法
    
    Args:
        content: HPL源代码内容
    
    Returns:
        str: 预处理后的内容
    """
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检测函数定义行（包含 =>）
        # 匹配模式：methodName: (params) => {
        # 支持任意缩进（用于类方法和顶层函数）
        # 排除 YAML 列表项（以 - 开头的行）
        func_pattern = r'^(\s*)(?!-)(\w+):\s*\(.*\)\s*=>.*\{'

        match = re.match(func_pattern, line)
        
        if match:
            indent = match.group(1)
            key = match.group(2)
            
            # 收集完整的函数体
            func_lines = [line]
            brace_count = line.count('{') - line.count('}')
            j = i + 1
            
            while brace_count > 0 and j < len(lines):
                next_line = lines[j]
                func_lines.append(next_line)
                brace_count += next_line.count('{') - next_line.count('}')
                j += 1
            
            # 合并函数定义
            full_func = '\n'.join(func_lines)
            
            # 提取 key 和 value
            # 找到第一个冒号的位置（在key后面）
            key_end_pos = len(indent) + len(key)
            colon_pos = full_func.find(':', key_end_pos)
            key_part = full_func[:colon_pos].rstrip()
            value_part = full_func[colon_pos+1:].strip()
            
            # 转换为 YAML 字面量块格式
            # 使用 | 表示保留换行符的字面量块
            # 注意：| 后面要直接跟内容，不能有空行
            result.append(f'{key_part}: |')
            for func_line in value_part.split('\n'):
                # 移除内联注释，避免YAML解析错误
                cleaned_line = strip_inline_comment(func_line)
                result.append(f'{indent}  {cleaned_line}')
            
            i = j
        else:
            result.append(line)
            i += 1
    
    return '\n'.join(result)




def parse_call_expression(call_str):
    """
    解析 call 表达式，提取函数名和参数
    
    Args:
        call_str: 调用表达式字符串，如 "add(5, 3)" 或 "main"
    
    Returns:
        tuple: (函数名, 参数列表)
    """
    call_str = call_str.strip()
    
    # 查找左括号
    if '(' in call_str:
        func_name = call_str[:call_str.find('(')].strip()
        args_str = call_str[call_str.find('(')+1:call_str.rfind(')')].strip()
        
        # 解析参数
        args = []
        if args_str:
            # 按逗号分割参数
            for arg in args_str.split(','):
                arg = arg.strip()
                # 尝试解析为整数
                try:
                    args.append(int(arg))
                except ValueError:
                    # 尝试解析为浮点数
                    try:
                        args.append(float(arg))
                    except ValueError:
                        # 作为字符串处理（去掉引号）
                        if (arg.startswith('"') and arg.endswith('"')) or \
                           (arg.startswith("'") and arg.endswith("'")):
                            args.append(arg[1:-1])
                        else:
                            args.append(arg)  # 变量名或其他
        
        return func_name, args
    else:
        # 没有括号，如 call: main
        return call_str, []


def extract_function_info(func_str):
    """
    从函数定义字符串中提取参数和函数体
    
    Args:
        func_str: 函数定义字符串，如 "(x, y) => { return x + y }"
    
    Returns:
        tuple: (参数列表, 函数体字符串)
    """
    func_str = func_str.strip()
    
    # 新语法: (params) => { body }
    start = func_str.find('(')
    end = func_str.find(')')
    params_str = func_str[start+1:end]
    params = [p.strip() for p in params_str.split(',')] if params_str else []
    
    # 找到箭头 =>
    arrow_pos = func_str.find('=>', end)
    if arrow_pos == -1:
        raise ValueError("Arrow function syntax error: => not found")
    
    # 找到函数体
    body_start = func_str.find('{', arrow_pos)
    body_end = func_str.rfind('}')
    if body_start == -1 or body_end == -1:
        raise ValueError("Arrow function syntax error: braces not found")
    
    body_str = func_str[body_start+1:body_end].strip()
    
    return params, body_str
