"""
HPL 标准库 - io 模块

提供文件输入输出操作功能。
"""

import os

try:
    from hpl_runtime.modules.base import HPLModule
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from hpl_runtime.modules.base import HPLModule


def read_file(path):
    """读取文件内容"""
    if not isinstance(path, str):
        raise TypeError(f"read_file() requires string path, got {type(path).__name__}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    """写入文件内容"""
    if not isinstance(path, str):
        raise TypeError(f"write_file() requires string path, got {type(path).__name__}")
    if not isinstance(content, str):
        raise TypeError(f"write_file() requires string content, got {type(content).__name__}")
    
    # 确保目录存在
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def append_file(path, content):
    """追加文件内容"""
    if not isinstance(path, str):
        raise TypeError(f"append_file() requires string path, got {type(path).__name__}")
    if not isinstance(content, str):
        raise TypeError(f"append_file() requires string content, got {type(content).__name__}")
    
    # 确保目录存在
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content)
    
    return True

def file_exists(path):
    """检查文件是否存在"""
    if not isinstance(path, str):
        raise TypeError(f"file_exists() requires string path, got {type(path).__name__}")
    return os.path.exists(path)

def delete_file(path):
    """删除文件"""
    if not isinstance(path, str):
        raise TypeError(f"delete_file() requires string path, got {type(path).__name__}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    os.remove(path)
    return True

def create_dir(path):
    """创建目录"""
    if not isinstance(path, str):
        raise TypeError(f"create_dir() requires string path, got {type(path).__name__}")
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    return True

def list_dir(path):
    """列出目录内容"""
    if not isinstance(path, str):
        raise TypeError(f"list_dir() requires string path, got {type(path).__name__}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Not a directory: {path}")
    
    return os.listdir(path)

def get_file_size(path):
    """获取文件大小"""
    if not isinstance(path, str):
        raise TypeError(f"get_file_size() requires string path, got {type(path).__name__}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    return os.path.getsize(path)

def is_file(path):
    """检查路径是否为文件"""
    if not isinstance(path, str):
        raise TypeError(f"is_file() requires string path, got {type(path).__name__}")
    return os.path.isfile(path)

def is_dir(path):
    """检查路径是否为目录"""
    if not isinstance(path, str):
        raise TypeError(f"is_dir() requires string path, got {type(path).__name__}")
    return os.path.isdir(path)

# 创建模块实例
module = HPLModule('io', 'File input/output operations')

# 注册函数
module.register_function('read_file', read_file, 1, 'Read entire file content as string')
module.register_function('write_file', write_file, 2, 'Write string content to file')
module.register_function('append_file', append_file, 2, 'Append string content to file')
module.register_function('file_exists', file_exists, 1, 'Check if file exists')
module.register_function('delete_file', delete_file, 1, 'Delete a file')
module.register_function('create_dir', create_dir, 1, 'Create a directory')
module.register_function('list_dir', list_dir, 1, 'List directory contents')
module.register_function('get_file_size', get_file_size, 1, 'Get file size in bytes')
module.register_function('is_file', is_file, 1, 'Check if path is a file')
module.register_function('is_dir', is_dir, 1, 'Check if path is a directory')
