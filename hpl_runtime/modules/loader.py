"""
HPL 模块加载器

该模块负责加载和管理 HPL 模块。
支持:
- 标准库模块 (io, math, json, os, time等)
- Python 第三方包 (PyPI)
- 自定义 HPL 模块文件 (.hpl)
- 自定义 Python 模块 (.py)
"""

import os
import sys
import importlib
import importlib.util
import subprocess
import json
import logging
from pathlib import Path

# 从 module_base 导入 HPLModule 基类
try:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLImportError
except ImportError:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLImportError

# 配置日志
logger = logging.getLogger('hpl.module_loader')


# 模块缓存
_module_cache = {}

# 标准库模块注册表
_stdlib_modules = {}

# HPL 包配置目录
HPL_CONFIG_DIR = Path.home() / '.hpl'
HPL_PACKAGES_DIR = HPL_CONFIG_DIR / 'packages'
HPL_MODULE_PATHS = [HPL_PACKAGES_DIR]

# 确保配置目录存在
HPL_CONFIG_DIR.mkdir(exist_ok=True)
HPL_PACKAGES_DIR.mkdir(exist_ok=True)


class ModuleLoaderContext:
    """
    模块加载器上下文管理类
    
    使用线程本地存储管理当前 HPL 文件路径，支持嵌套导入和并发场景。
    替代原来的全局变量 _current_hpl_file_dir，避免全局状态带来的问题。
    """
    
    def __init__(self):
        self._current_file_dir = None
    
    def set_current_file(self, file_path):
        """设置当前执行的 HPL 文件路径，用于相对导入"""
        if file_path:
            self._current_file_dir = Path(file_path).parent.resolve()
        else:
            self._current_file_dir = None
    
    def get_current_file_dir(self):
        """获取当前 HPL 文件所在目录"""
        return self._current_file_dir
    
    def clear(self):
        """清除当前上下文"""
        self._current_file_dir = None


# 全局上下文实例（单例模式）
_loader_context = ModuleLoaderContext()


def set_current_hpl_file(file_path):
    """
    设置当前执行的 HPL 文件路径，用于相对导入
    
    这是兼容旧 API 的包装函数，实际使用 ModuleLoaderContext 管理状态。
    """
    _loader_context.set_current_file(file_path)


def get_loader_context():
    """获取模块加载器上下文，用于高级用法（如嵌套导入管理）"""
    return _loader_context




def register_module(name, module_instance):
    """注册标准库模块"""
    _stdlib_modules[name] = module_instance


def get_module(name):
    """获取已注册的模块"""
    if name in _stdlib_modules:
        return _stdlib_modules[name]
    return None


def add_module_path(path):
    """添加模块搜索路径"""
    path = Path(path).resolve()
    if path not in HPL_MODULE_PATHS:
        HPL_MODULE_PATHS.insert(0, path)


def load_module(module_name, search_paths=None):
    """
    加载 HPL 模块
    
    支持:
    - 标准库模块 (io, math, json, os, time等)
    - Python 第三方包 (通过 pip 安装)
    - 自定义 HPL 模块文件 (.hpl)
    - 自定义 Python 模块 (.py)
    
    Raises:
        HPLImportError: 当模块无法找到或加载失败时
    """
    # 检查缓存
    if module_name in _module_cache:
        logger.debug(f"Module '{module_name}' found in cache")
        return _module_cache[module_name]
    
    # 1. 尝试加载标准库模块
    module = get_module(module_name)
    if module:
        logger.debug(f"Module '{module_name}' loaded from stdlib")
        _module_cache[module_name] = module
        return module
    
    # 2. 尝试加载 Python 第三方包
    module = _load_python_package(module_name)
    if module:
        logger.debug(f"Module '{module_name}' loaded from Python packages")
        _module_cache[module_name] = module
        return module
    
    # 3. 尝试加载本地 HPL 模块文件
    module = _load_hpl_module(module_name, search_paths)
    if module:
        logger.debug(f"Module '{module_name}' loaded from HPL file")
        _module_cache[module_name] = module
        return module
    
    # 4. 尝试加载本地 Python 模块文件
    module = _load_python_module(module_name, search_paths)
    if module:
        logger.debug(f"Module '{module_name}' loaded from Python file")
        _module_cache[module_name] = module
        return module
    
    # 模块未找到
    available = list(_stdlib_modules.keys())
    raise HPLImportError(
        f"Module '{module_name}' not found. "
        f"Available stdlib modules: {available}. "
        f"Searched paths: {HPL_MODULE_PATHS}"
    )



def _load_python_package(module_name):
    """
    加载 Python 第三方包
    将 Python 模块包装为 HPLModule
    """
    try:
        # 尝试导入 Python 模块
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return None
        
        # 导入模块
        python_module = importlib.import_module(module_name)
        
        # 创建 HPL 包装模块
        hpl_module = HPLModule(module_name, f"Python package: {module_name}")
        
        # 自动注册所有可调用对象为函数
        for attr_name in dir(python_module):
            if not attr_name.startswith('_'):
                attr = getattr(python_module, attr_name)
                if callable(attr):
                    hpl_module.register_function(attr_name, attr, None, f"Python function: {attr_name}")
                else:
                    # 注册为常量
                    hpl_module.register_constant(attr_name, attr, f"Python constant: {attr_name}")
        
        return hpl_module
        
    except ImportError:
        return None
    except Exception as e:
        logger.warning(f"Failed to load Python package '{module_name}': {e}")
        return None



def _load_hpl_module(module_name, search_paths=None):
    """
    加载本地 HPL 模块文件 (.hpl)
    搜索路径: 当前HPL文件目录 -> 当前目录 -> HPL_MODULE_PATHS -> search_paths
    """
    # 构建搜索路径列表
    paths = []
    
    # 首先搜索当前 HPL 文件所在目录（使用上下文管理器替代全局变量）
    current_file_dir = _loader_context.get_current_file_dir()
    if current_file_dir:
        paths.append(current_file_dir)
    
    paths.append(Path.cwd())
    paths.extend(HPL_MODULE_PATHS)
    if search_paths:
        paths.extend([Path(p) for p in search_paths])
    
    # 尝试找到 .hpl 文件
    for path in paths:
        module_file = path / f"{module_name}.hpl"
        if module_file.exists():
            return _parse_hpl_module(module_name, module_file)
        
        # 也尝试目录形式 (module_name/index.hpl)
        module_dir = path / module_name
        if module_dir.is_dir():
            index_file = module_dir / "index.hpl"
            if index_file.exists():
                return _parse_hpl_module(module_name, index_file)
    
    return None


def _load_python_module(module_name, search_paths=None):
    """
    加载本地 Python 模块文件 (.py)
    搜索路径: 当前HPL文件目录 -> 当前目录 -> HPL_MODULE_PATHS -> search_paths
    """
    # 构建搜索路径列表
    paths = []
    
    # 首先搜索当前 HPL 文件所在目录（使用上下文管理器替代全局变量）
    current_file_dir = _loader_context.get_current_file_dir()
    if current_file_dir:
        paths.append(current_file_dir)
    
    paths.append(Path.cwd())
    paths.extend(HPL_MODULE_PATHS)
    if search_paths:
        paths.extend([Path(p) for p in search_paths])
    
    # 尝试找到 .py 文件
    for path in paths:
        module_file = path / f"{module_name}.py"
        if module_file.exists():
            return _parse_python_module_file(module_name, module_file)
        
        # 也尝试目录形式 (module_name/__init__.py)
        module_dir = path / module_name
        if module_dir.is_dir():
            init_file = module_dir / "__init__.py"
            if init_file.exists():
                return _parse_python_module_file(module_name, init_file)
    
    return None


def _parse_hpl_module(module_name, file_path):
    """
    解析 HPL 模块文件
    返回 HPLModule 实例
    """
    try:
        # 延迟导入以避免循环依赖
        try:
            from hpl_runtime.core.parser import HPLParser
            from hpl_runtime.core.evaluator import HPLEvaluator
            from hpl_runtime.core.models import HPLObject
        except ImportError:
            from hpl_runtime.core.parser import HPLParser
            from hpl_runtime.core.evaluator import HPLEvaluator
            from hpl_runtime.core.models import HPLObject
        
        # 解析 HPL 文件
        parser = HPLParser(str(file_path))
        classes, objects, functions, main_func, call_target, call_args, imports = parser.parse()
        
        # 创建 HPL 模块
        hpl_module = HPLModule(module_name, f"HPL module: {module_name}")
        
        # 创建 evaluator 用于执行构造函数和函数
        evaluator = HPLEvaluator(classes, objects, functions, main_func)
        
        # 将类注册为模块函数（构造函数）
        for class_name, hpl_class in classes.items():
            # 计算构造函数参数数量
            init_param_count = 0
            if 'init' in hpl_class.methods:
                init_param_count = len(hpl_class.methods['init'].params)
            elif '__init__' in hpl_class.methods:
                init_param_count = len(hpl_class.methods['__init__'].params)
            
            def make_constructor(cls, eval_ctx):
                def constructor(*args):
                    # 创建对象实例
                    obj = HPLObject("instance", cls)
                    
                    # 调用构造函数 init 或 __init__
                    constructor_name = None
                    if 'init' in cls.methods:
                        constructor_name = 'init'
                    elif '__init__' in cls.methods:
                        constructor_name = '__init__'
                    
                    if constructor_name:
                        init_func = cls.methods[constructor_name]
                        # 验证参数数量
                        if len(args) != len(init_func.params):
                            raise ValueError(
                                f"Constructor '{cls.name}' expects {len(init_func.params)} "
                                f"arguments, got {len(args)}"
                            )
                        # 构建参数作用域
                        func_scope = {'this': obj}
                        for i, param in enumerate(init_func.params):
                            if i < len(args):
                                func_scope[param] = args[i]
                            else:
                                func_scope[param] = None
                        # 执行构造函数
                        eval_ctx.execute_function(init_func, func_scope)
                    
                    return obj
                
                return constructor
            
            hpl_module.register_function(
                class_name, 
                make_constructor(hpl_class, evaluator), 
                init_param_count,
                f"Class constructor: {class_name}"
            )

        
        # 将对象注册为常量（执行构造函数如果存在）
        for obj_name, obj in objects.items():
            # 如果对象有预定义的构造参数，执行构造函数
            if hasattr(obj, 'attributes') and '__init_args__' in obj.attributes:
                init_args = obj.attributes['__init_args__']
                # 解析并转换参数值
                resolved_args = []
                for arg in init_args:
                    if isinstance(arg, (int, float, bool)):
                        resolved_args.append(arg)
                    elif isinstance(arg, str):
                        # 尝试解析为数字
                        try:
                            resolved_args.append(int(arg))
                        except ValueError:
                            try:
                                resolved_args.append(float(arg))
                            except ValueError:
                                resolved_args.append(arg)
                # 执行构造函数
                evaluator._call_constructor(obj, resolved_args)
            
            hpl_module.register_constant(obj_name, obj, f"Object instance: {obj_name}")
        
        # 注册顶层函数到模块
        for func_name, func in functions.items():
            def make_function(fn, eval_ctx, name):
                def wrapper(*args):
                    # 验证参数数量
                    if len(args) != len(fn.params):
                        raise ValueError(
                            f"Function '{name}' expects {len(fn.params)} "
                            f"arguments, got {len(args)}"
                        )
                    # 构建参数作用域
                    func_scope = {}
                    for i, param in enumerate(fn.params):
                        if i < len(args):
                            func_scope[param] = args[i]
                        else:
                            func_scope[param] = None
                    # 执行函数
                    return eval_ctx.execute_function(fn, func_scope)
                return wrapper
            
            hpl_module.register_function(
                func_name,
                make_function(func, evaluator, func_name),
                len(func.params),
                f"Function: {func_name}"
            )
        
        # 处理导入的模块
        for imp in imports:
            module_name_to_import = imp['module']
            alias = imp['alias']
            try:
                imported_module = load_module(module_name_to_import)
                # 使用别名或原始名称注册
                register_name = alias if alias else module_name_to_import
                hpl_module.register_constant(register_name, imported_module, f"Imported module: {module_name_to_import}")
            except ImportError as e:
                print(f"Warning: Failed to import '{module_name_to_import}' in module '{module_name}': {e}")
        
        return hpl_module
        
    except Exception as e:
        logger.error(f"Failed to parse HPL module '{module_name}': {e}")
        import traceback
        traceback.print_exc()
        raise HPLImportError(f"Failed to parse HPL module '{module_name}': {e}") from e




def _parse_python_module_file(module_name, file_path):
    """
    解析本地 Python 模块文件
    返回 HPLModule 实例
    """
    try:
        # 动态加载 Python 文件
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None
        
        python_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = python_module
        spec.loader.exec_module(python_module)
        
        # 创建 HPL 包装模块
        hpl_module = HPLModule(module_name, f"Python module: {module_name}")
        
        # 检查是否有 HPL_MODULE 定义（显式 HPL 接口）
        if hasattr(python_module, 'HPL_MODULE'):
            hpl_interface = python_module.HPL_MODULE
            if isinstance(hpl_interface, HPLModule):
                return hpl_interface
        
        # 自动注册所有可调用对象
        for attr_name in dir(python_module):
            if not attr_name.startswith('_'):
                attr = getattr(python_module, attr_name)
                if callable(attr):
                    hpl_module.register_function(attr_name, attr, None, f"Python function: {attr_name}")
                else:
                    hpl_module.register_constant(attr_name, attr, f"Python constant: {attr_name}")
        
        return hpl_module
        
    except Exception as e:
        logger.warning(f"Failed to load Python module '{module_name}': {e}")
        return None



def install_package(package_name, version=None):
    """
    安装 Python 包到 HPL 包目录
    使用 pip 安装
    """
    try:
        # 构建 pip 安装命令
        cmd = [sys.executable, "-m", "pip", "install", "--target", str(HPL_PACKAGES_DIR)]
        
        if version:
            package_spec = f"{package_name}=={version}"
        else:
            package_spec = package_name
        
        cmd.append(package_spec)
        
        # 执行安装
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully installed '{package_spec}'")
            return True
        else:
            logger.error(f"Failed to install '{package_spec}': {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error installing package: {e}")
        return False



def uninstall_package(package_name):
    """
    卸载 Python 包
    """
    try:
        # 从 HPL 包目录中删除
        package_dir = HPL_PACKAGES_DIR / package_name
        if package_dir.exists():
            import shutil
            shutil.rmtree(package_dir)
            logger.info(f"Uninstalled '{package_name}'")
            return True
        
        # 尝试用 pip 卸载
        cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Uninstalled '{package_name}'")
            return True
        else:
            logger.error(f"Failed to uninstall '{package_name}'")
            return False
            
    except Exception as e:
        logger.error(f"Error uninstalling package: {e}")
        return False



def list_installed_packages():
    """
    列出已安装的包
    """
    packages = []
    
    # 列出 HPL 包目录中的包
    if HPL_PACKAGES_DIR.exists():
        for item in HPL_PACKAGES_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                packages.append(item.name)
            elif item.suffix == '.py' and not item.name.startswith('_'):
                packages.append(item.stem)
            elif item.suffix == '.hpl' and not item.name.startswith('_'):
                packages.append(item.stem)
    
    return sorted(packages)


def clear_cache():
    """清除模块缓存"""
    _module_cache.clear()


def init_stdlib():
    """初始化所有标准库模块"""
    try:
        # 尝试多种导入方式以适应不同的运行环境
        try:
            # 方式1: 从 hpl_runtime.stdlib 导入（当 hpl_runtime 在 Python 路径中时）
            from hpl_runtime.stdlib import io, math, json_mod, os_mod, time_mod
        except ImportError:
            # 方式2: 直接从 stdlib 导入（当在 hpl_runtime 目录中运行时）
            # 将 hpl_runtime 目录添加到 Python 路径
            hpl_runtime_dir = os.path.dirname(os.path.abspath(__file__))
            if hpl_runtime_dir not in sys.path:
                sys.path.insert(0, hpl_runtime_dir)
            from stdlib import io, math, json_mod, os_mod, time_mod
        
        # 注册模块
        register_module('io', io.module)
        register_module('math', math.module)
        register_module('json', json_mod.module)
        register_module('os', os_mod.module)
        register_module('time', time_mod.module)
        
    except ImportError as e:
        # 如果某些模块导入失败，记录错误但不中断
        logger.warning(f"Some stdlib modules failed to load: {e}")



# 初始化标准库
init_stdlib()
