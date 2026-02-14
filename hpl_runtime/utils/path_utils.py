"""
HPL 路径工具模块

该模块提供文件路径解析和搜索相关的通用工具函数。
"""

import os
from pathlib import Path


def resolve_include_path(include_file, base_file=None, search_paths=None):
    r"""
    解析include文件路径，支持多种路径格式：
    1. 绝对路径（Unix: /path, Windows: C:\path）
    2. 相对当前文件目录
    3. 相对当前工作目录
    4. 搜索路径列表中的路径

    
    Args:
        include_file: 要解析的包含文件路径
        base_file: 当前基础文件路径（用于相对路径解析）
        search_paths: 额外的搜索路径列表
    
    Returns:
        str: 解析后的绝对路径，如果未找到则返回None
    """
    include_path = Path(include_file)
    search_paths = search_paths or []
    
    # 1. 检查是否为绝对路径
    if include_path.is_absolute():
        if include_path.exists():
            return str(include_path)
        return None
    
    # 2. 相对当前文件目录
    if base_file:
        current_dir = Path(base_file).parent.resolve()
        resolved_path = current_dir / include_path
        if resolved_path.exists():
            return str(resolved_path)
    
    # 3. 相对当前工作目录
    cwd_path = Path.cwd() / include_path
    if cwd_path.exists():
        return str(cwd_path)
    
    # 4. 搜索路径列表中的路径
    for search_path in search_paths:
        module_path = Path(search_path) / include_path
        if module_path.exists():
            return str(module_path)
    
    return None

def get_file_directory(file_path):
    """
    获取文件所在目录
    
    Args:
        file_path: 文件路径
    
    Returns:
        Path: 文件所在目录
    """
    return Path(file_path).parent.resolve()

def ensure_directory_exists(file_path):
    """
    确保文件所在目录存在，如果不存在则创建
    
    Args:
        file_path: 文件路径
    """
    directory = Path(file_path).parent
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
