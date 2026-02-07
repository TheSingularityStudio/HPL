"""
HPL 标准库 - os 模块

提供操作系统接口功能。
"""

import os as _os
import sys as _sys
import platform as _platform

try:
    from src.module_base import HPLModule
except ImportError:
    try:
        from module_base import HPLModule
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from module_base import HPLModule




def get_env(name, default=None):
    """获取环境变量"""
    if not isinstance(name, str):
        raise TypeError(f"get_env() requires string name, got {type(name).__name__}")
    
    if default is not None and not isinstance(default, str):
        raise TypeError(f"get_env() requires string default, got {type(default).__name__}")
    
    return _os.environ.get(name, default)


def set_env(name, value):
    """设置环境变量"""
    if not isinstance(name, str):
        raise TypeError(f"set_env() requires string name, got {type(name).__name__}")
    if not isinstance(value, str):
        raise TypeError(f"set_env() requires string value, got {type(value).__name__}")
    
    _os.environ[name] = value
    return True


def get_cwd():
    """获取当前工作目录"""
    return _os.getcwd()


def change_dir(path):
    """改变当前工作目录"""
    if not isinstance(path, str):
        raise TypeError(f"change_dir() requires string path, got {type(path).__name__}")
    
    if not _os.path.exists(path):
        raise FileNotFoundError(f"Directory not found: {path}")
    
    _os.chdir(path)
    return True


def get_platform():
    """获取操作系统平台"""
    return _platform.system()


def get_python_version():
    """获取 Python 版本"""
    return _platform.python_version()


def get_hpl_version():
    """获取 HPL 版本"""
    return "1.0.0"


def execute_command(command):
    """执行系统命令（谨慎使用）"""
    if not isinstance(command, str):
        raise TypeError(f"execute_command() requires string command, got {type(command).__name__}")
    
    import subprocess
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        raise RuntimeError(f"Command execution failed: {e}")


def exit_code(code=0):
    """退出程序"""
    if not isinstance(code, int):
        raise TypeError(f"exit() requires int code, got {type(code).__name__}")
    
    _sys.exit(code)


def get_args():
    """获取命令行参数"""
    return _sys.argv[1:]  # 排除脚本名


def get_path_sep():
    """获取路径分隔符"""
    return _os.sep


def get_line_sep():
    """获取行分隔符"""
    return _os.linesep


def path_join(*paths):
    """连接路径"""
    if len(paths) == 0:
        raise ValueError("path_join() requires at least one path")
    
    for i, p in enumerate(paths):
        if not isinstance(p, str):
            raise TypeError(f"path_join() requires string paths, got {type(p).__name__} at position {i}")
    
    return _os.path.join(*paths)


def path_abs(path):
    """获取绝对路径"""
    if not isinstance(path, str):
        raise TypeError(f"path_abs() requires string path, got {type(path).__name__}")
    return _os.path.abspath(path)


def path_dir(path):
    """获取目录名"""
    if not isinstance(path, str):
        raise TypeError(f"path_dir() requires string path, got {type(path).__name__}")
    return _os.path.dirname(path)


def path_base(path):
    """获取文件名"""
    if not isinstance(path, str):
        raise TypeError(f"path_base() requires string path, got {type(path).__name__}")
    return _os.path.basename(path)


def path_ext(path):
    """获取文件扩展名"""
    if not isinstance(path, str):
        raise TypeError(f"path_ext() requires string path, got {type(path).__name__}")
    return _os.path.splitext(path)[1]


def path_norm(path):
    """规范化路径"""
    if not isinstance(path, str):
        raise TypeError(f"path_norm() requires string path, got {type(path).__name__}")
    return _os.path.normpath(path)


def cpu_count():
    """获取 CPU 核心数"""
    return _os.cpu_count() or 1


# 创建模块实例
module = HPLModule('os', 'Operating system interface')

# 注册函数
module.register_function('get_env', get_env, None, 'Get environment variable (optional default)')
module.register_function('set_env', set_env, 2, 'Set environment variable')
module.register_function('get_cwd', get_cwd, 0, 'Get current working directory')
module.register_function('change_dir', change_dir, 1, 'Change current directory')
module.register_function('get_platform', get_platform, 0, 'Get OS platform')
module.register_function('get_python_version', get_python_version, 0, 'Get Python version')
module.register_function('get_hpl_version', get_hpl_version, 0, 'Get HPL version')
module.register_function('execute', execute_command, 1, 'Execute system command')
module.register_function('exit', exit_code, None, 'Exit program (optional code)')
module.register_function('get_args', get_args, 0, 'Get command line arguments')
module.register_function('get_path_sep', get_path_sep, 0, 'Get path separator')
module.register_function('get_line_sep', get_line_sep, 0, 'Get line separator')
module.register_function('path_join', path_join, None, 'Join path components')
module.register_function('path_abs', path_abs, 1, 'Get absolute path')
module.register_function('path_dir', path_dir, 1, 'Get directory name')
module.register_function('path_base', path_base, 1, 'Get file name')
module.register_function('path_ext', path_ext, 1, 'Get file extension')
module.register_function('path_norm', path_norm, 1, 'Normalize path')
module.register_function('cpu_count', cpu_count, 0, 'Get CPU count')
