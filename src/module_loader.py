"""
HPL 模块加载器

该模块负责加载和管理 HPL 标准库模块。
支持模块缓存、命名空间管理和函数注册。
"""

import os
import sys

# 从 module_base 导入 HPLModule 基类
try:
    from src.module_base import HPLModule
except ImportError:
    from module_base import HPLModule

# 模块缓存
_module_cache = {}

# 标准库模块注册表
_stdlib_modules = {}


def register_module(name, module_instance):
    """注册标准库模块"""
    _stdlib_modules[name] = module_instance


def get_module(name):
    """获取已注册的模块"""
    if name in _stdlib_modules:
        return _stdlib_modules[name]
    return None


def load_module(module_name):
    """
    加载 HPL 模块
    
    支持:
    - 标准库模块 (io, math, json, os, time等)
    - 未来可扩展为文件模块
    """
    # 检查缓存
    if module_name in _module_cache:
        return _module_cache[module_name]
    
    # 尝试加载标准库模块
    module = get_module(module_name)
    if module:
        _module_cache[module_name] = module
        return module
    
    # 模块未找到
    raise ImportError(f"Module '{module_name}' not found. Available modules: {list(_stdlib_modules.keys())}")


def clear_cache():
    """清除模块缓存"""
    _module_cache.clear()


def init_stdlib():
    """初始化所有标准库模块"""
    try:
        # 尝试多种导入方式以适应不同的运行环境
        try:
            # 方式1: 从 src.stdlib 导入（当 src 在 Python 路径中时）
            from src.stdlib import io, math, json_mod, os_mod, time_mod
        except ImportError:
            # 方式2: 直接从 stdlib 导入（当在 src 目录中运行时）
            # 将 src 目录添加到 Python 路径
            src_dir = os.path.dirname(os.path.abspath(__file__))
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            from stdlib import io, math, json_mod, os_mod, time_mod
        
        # 注册模块
        register_module('io', io.module)
        register_module('math', math.module)
        register_module('json', json_mod.module)
        register_module('os', os_mod.module)
        register_module('time', time_mod.module)
        
    except ImportError as e:
        # 如果某些模块导入失败，记录错误但不中断
        print(f"Warning: Some stdlib modules failed to load: {e}")


# 初始化标准库
init_stdlib()
