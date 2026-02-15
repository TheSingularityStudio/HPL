"""
HPL 模块加载器

该模块负责加载和管理 HPL 模块。
支持:
- 标准库模块 (io, math, json, os, time等)
- Python 第三方包 (PyPI)
- 自定义 HPL 模块文件 (.hpl)
- 自定义 Python 模块 (.py)
- 点号模块名导入 (package.submodule)
- 包初始化文件 (__init__.hpl)
"""

import os
import sys
import importlib
import importlib.util
import subprocess
import json
import logging
from pathlib import Path
from collections import OrderedDict

# 从 module_base 导入 HPLModule 基类
from hpl_runtime.modules.base import HPLModule
from hpl_runtime.utils.exceptions import HPLImportError, HPLValueError, HPLRuntimeError

# 配置日志
logger = logging.getLogger('hpl.module_loader')


# LRU 模块缓存实现
class ModuleCache:
    """
    带 LRU 淘汰机制的模块缓存
    
    限制缓存大小，防止内存无限增长。
    默认最大缓存 100 个模块。
    """
    
    def __init__(self, capacity=100):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key):
        """获取缓存项，并将其移到最近使用"""
        if key not in self.cache:
            return None
        # 移到末尾（最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value):
        """添加缓存项，如果已满则淘汰最久未使用的"""
        if key in self.cache:
            # 更新现有项
            self.cache.move_to_end(key)
            self.cache[key] = value
        else:
            # 添加新项
            if len(self.cache) >= self.capacity:
                # 淘汰最久未使用的（第一个）
                self.cache.popitem(last=False)
            self.cache[key] = value
    
    def __contains__(self, key):
        """支持 'in' 操作符"""
        return key in self.cache
    
    def __setitem__(self, key, value):
        """支持 item assignment: _module_cache[key] = value"""
        self.put(key, value)
    
    def __delitem__(self, key):
        """支持 item deletion: del _module_cache[key]"""
        if key in self.cache:
            del self.cache[key]
    
    def __len__(self):
        """支持 len(_module_cache)"""
        return len(self.cache)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()

# 模块缓存（使用 LRU 机制，默认最大 100 个模块）
_module_cache = ModuleCache(capacity=100)


# 标准库模块注册表
_stdlib_modules = {}

# HPL 包配置目录（支持环境变量覆盖）
HPL_CONFIG_DIR = Path(os.environ.get('HPL_CONFIG_DIR', Path.home() / '.hpl'))
HPL_PACKAGES_DIR = Path(os.environ.get('HPL_PACKAGES_DIR', HPL_CONFIG_DIR / 'packages'))
HPL_MODULE_PATHS = [HPL_PACKAGES_DIR]

# 确保配置目录存在
HPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
HPL_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)

# 循环导入检测 - 正在加载中的模块集合
_loading_modules = set()


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

def _is_file_path(module_name):
    """检查模块名是否是文件路径（包含 / 或 \，或以 ./ 或 ../ 开头）"""
    return '/' in module_name or '\\' in module_name or module_name.startswith(('./', '../'))

def _is_dot_notation(module_name):
    """检查模块名是否使用点号表示法（如 package.submodule）"""
    # 排除文件路径和相对路径
    if _is_file_path(module_name):
        return False
    # 检查是否包含点号，且不是以点号开头或结尾
    return '.' in module_name and not module_name.startswith('.') and not module_name.endswith('.')

def _convert_dot_to_path(module_name):
    """将点号表示法转换为文件路径（如 mathlib.basic.add -> mathlib/basic/add）"""
    return module_name.replace('.', '/')

def _get_module_file_name(module_name):
    """从模块名中获取模块文件名（如 mathlib.basic.add -> add, ../basic/add -> add）"""
    # 首先检查是否是文件路径
    if '/' in module_name or '\\' in module_name:
        # 文件路径，提取最后一部分
        parts = module_name.replace('\\', '/').split('/')
        return parts[-1] if parts else module_name
    
    # 点号表示法
    parts = module_name.split('.')
    return parts[-1] if parts else module_name

def _get_package_path(module_name):
    """从点号表示法中获取包路径（如 mathlib.basic.add -> mathlib/basic）"""
    parts = module_name.split('.')
    return '/'.join(parts[:-1]) if len(parts) > 1 else ''

def load_module(module_name, search_paths=None):
    """
    加载 HPL 模块
    
    支持:
    - 标准库模块 (io, math, json, os, time等)
    - Python 第三方包 (通过 pip 安装)
    - 自定义 HPL 模块文件 (.hpl)
    - 自定义 Python 模块 (.py)
    - 点号模块名导入 (package.submodule)
    
    Raises:
        HPLImportError: 当模块无法找到或加载失败时
    """
    # 检查循环导入
    if module_name in _loading_modules:
        raise HPLImportError(
            f"Circular import detected: '{module_name}' is already being loaded. "
            f"Import chain: {' -> '.join(sorted(_loading_modules))} -> {module_name}"
        )
    
    # 检查缓存
    cached_module = _module_cache.get(module_name)
    if cached_module is not None:
        logger.debug(f"Module '{module_name}' found in cache")
        return cached_module

    # 1. 尝试加载标准库模块
    module = get_module(module_name)
    if module:
        logger.debug(f"Module '{module_name}' loaded from stdlib")
        _module_cache.put(module_name, module)
        return module

    # 检查是否是文件路径（相对路径或绝对路径）
    is_file_path = _is_file_path(module_name)
    
    # 2. 尝试加载 Python 第三方包（仅对非文件路径的模块名）
    if not is_file_path and not _is_dot_notation(module_name):
        module = _load_python_package(module_name)
        if module:
            logger.debug(f"Module '{module_name}' loaded from Python packages")
            _module_cache.put(module_name, module)
            return module
    
    # 3. 尝试加载本地 HPL 模块文件
    module = _load_hpl_module(module_name, search_paths)
    if module:
        logger.debug(f"Module '{module_name}' loaded from HPL file")
        _module_cache.put(module_name, module)
        return module
    
    # 4. 尝试加载本地 Python 模块文件
    module = _load_python_module(module_name, search_paths)
    if module:
        logger.debug(f"Module '{module_name}' loaded from Python file")
        _module_cache.put(module_name, module)
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
        raise HPLImportError(f"Failed to load Python package '{module_name}': {e}") from e

def _load_hpl_module(module_name, search_paths=None):
    """
    加载本地 HPL 模块文件 (.hpl)
    搜索路径: 当前HPL文件目录 -> 当前目录 -> HPL_MODULE_PATHS -> search_paths
    
    支持:
    - 点号表示法 (package.submodule -> package/submodule.hpl)
    - 文件路径 (./module, ../module, path/to/module)
    - 目录形式 (module/index.hpl 或 module/__init__.hpl)
    """
    # 获取当前 HPL 文件所在目录（使用上下文管理器替代全局变量）
    current_file_dir = _loader_context.get_current_file_dir()
    
    # 检查是否是点号表示法
    is_dot_notation = _is_dot_notation(module_name)
    
    # 检查是否是相对路径或绝对路径
    if _is_file_path(module_name):
        # 这是一个文件路径，直接解析
        if current_file_dir:
            # 相对于当前 HPL 文件目录解析
            module_path = (current_file_dir / module_name).resolve()
        else:
            # 相对于当前工作目录解析
            module_path = Path(module_name).resolve()
        
        # 尝试作为 .hpl 文件
        hpl_file = module_path.with_suffix('.hpl')
        if hpl_file.exists():
            return _parse_hpl_module(module_name, hpl_file)
        
        # 尝试作为目录 (module_name/index.hpl 或 module_name/__init__.hpl)
        if module_path.is_dir():
            # 优先尝试 __init__.hpl，然后是 index.hpl
            init_file = module_path / "__init__.hpl"
            if init_file.exists():
                return _parse_hpl_module(module_name, init_file)
            
            index_file = module_path / "index.hpl"
            if index_file.exists():
                return _parse_hpl_module(module_name, index_file)
        
        return None
    
    # 普通模块名或点号表示法，使用搜索路径
    # 构建搜索路径列表
    paths = []
    
    if current_file_dir:
        paths.append(current_file_dir)
    
    paths.append(Path.cwd())
    paths.extend(HPL_MODULE_PATHS)
    if search_paths:
        paths.extend([Path(p) for p in search_paths])
    
    # 如果是点号表示法，转换为路径
    if is_dot_notation:
        # 将点号转换为路径分隔符
        file_path = _convert_dot_to_path(module_name)
        
        for path in paths:
            # 尝试作为 .hpl 文件
            module_file = path / f"{file_path}.hpl"
            if module_file.exists():
                return _parse_hpl_module(module_name, module_file)
            
            # 尝试作为目录 (package/subpackage/module/index.hpl 或 __init__.hpl)
            module_dir = path / file_path
            if module_dir.is_dir():
                # 优先尝试 __init__.hpl，然后是 index.hpl
                init_file = module_dir / "__init__.hpl"
                if init_file.exists():
                    return _parse_hpl_module(module_name, init_file)
                
                index_file = module_dir / "index.hpl"
                if index_file.exists():
                    return _parse_hpl_module(module_name, index_file)
    else:
        # 普通模块名
        for path in paths:
            module_file = path / f"{module_name}.hpl"
            if module_file.exists():
                return _parse_hpl_module(module_name, module_file)
            
            # 也尝试目录形式 (module_name/index.hpl 或 module_name/__init__.hpl)
            module_dir = path / module_name
            if module_dir.is_dir():
                # 优先尝试 __init__.hpl，然后是 index.hpl
                init_file = module_dir / "__init__.hpl"
                if init_file.exists():
                    return _parse_hpl_module(module_name, init_file)
                
                index_file = module_dir / "index.hpl"
                if index_file.exists():
                    return _parse_hpl_module(module_name, index_file)
    
    return None

def _load_python_module(module_name, search_paths=None):
    """
    加载本地 Python 模块文件 (.py)
    搜索路径: 当前HPL文件目录 -> 当前目录 -> HPL_MODULE_PATHS -> search_paths
    """
    # 获取当前 HPL 文件所在目录（使用上下文管理器替代全局变量）
    current_file_dir = _loader_context.get_current_file_dir()
    
    # 检查是否是相对路径或绝对路径
    if _is_file_path(module_name):
        # 这是一个文件路径，直接解析
        if current_file_dir:
            # 相对于当前 HPL 文件目录解析
            module_path = (current_file_dir / module_name).resolve()
        else:
            # 相对于当前工作目录解析
            module_path = Path(module_name).resolve()
        
        # 尝试作为 .py 文件
        py_file = module_path.with_suffix('.py')
        if py_file.exists():
            return _parse_python_module_file(module_name, py_file)
        
        # 尝试作为目录 (module_name/__init__.py)
        if module_path.is_dir():
            init_file = module_path / "__init__.py"
            if init_file.exists():
                return _parse_python_module_file(module_name, init_file)
        
        return None
    
    # 普通模块名，使用搜索路径
    # 构建搜索路径列表
    paths = []
    
    if current_file_dir:
        paths.append(current_file_dir)
    
    paths.append(Path.cwd())
    paths.extend(HPL_MODULE_PATHS)
    if search_paths:
        paths.extend([Path(p) for p in search_paths])
    
    # 如果是点号表示法，转换为路径
    if _is_dot_notation(module_name):
        file_path = _convert_dot_to_path(module_name)
        
        for path in paths:
            module_file = path / f"{file_path}.py"
            if module_file.exists():
                return _parse_python_module_file(module_name, module_file)
            
            # 也尝试目录形式 (package/module/__init__.py)
            module_dir = path / file_path
            if module_dir.is_dir():
                init_file = module_dir / "__init__.py"
                if init_file.exists():
                    return _parse_python_module_file(module_name, init_file)
    else:
        # 普通模块名
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
    
    包含循环导入检测机制
    """
    # 检查循环导入
    if module_name in _loading_modules:
        raise HPLImportError(
            f"Circular import detected: '{module_name}' is already being loaded. "
            f"Import chain: {' -> '.join(sorted(_loading_modules))} -> {module_name}"
        )
    
    # 标记模块正在加载中
    _loading_modules.add(module_name)
    
    # 保存当前上下文，并设置新上下文为当前模块所在目录
    previous_context = _loader_context.get_current_file_dir()
    file_path = Path(file_path)
    _loader_context.set_current_file(str(file_path))
    
    try:
        # 延迟导入以避免循环依赖
        from hpl_runtime.core.parser import HPLParser
        from hpl_runtime.core.evaluator import HPLEvaluator
        from hpl_runtime.core.models import HPLObject

        # 检查文件是否存在
        if not file_path.exists():
            raise HPLImportError(f"Module file not found: {file_path}")

        # 解析 HPL 文件
        parser = HPLParser(str(file_path))
        (classes, objects, functions, main_func, call_target, call_args, imports,
         user_data) = parser.parse()

        
        # 创建 HPL 模块
        hpl_module = HPLModule(module_name, f"HPL module: {module_name}")
        
        # 创建 evaluator 用于执行构造函数和函数
        evaluator = HPLEvaluator(classes, objects, functions, main_func)
        
        # 注意：evaluator.global_scope 就是 objects，后续导入的模块需要同时注册到这里
        
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
                            raise HPLValueError(
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
                        # 去除字符串两端的引号（单引号或双引号）
                        stripped_arg = arg.strip()
                        if (stripped_arg.startswith('"') and stripped_arg.endswith('"')) or \
                           (stripped_arg.startswith("'") and stripped_arg.endswith("'")):
                            stripped_arg = stripped_arg[1:-1]
                        # 尝试解析为数字
                        try:
                            resolved_args.append(int(stripped_arg))
                        except ValueError:
                            try:
                                resolved_args.append(float(stripped_arg))
                            except ValueError:
                                resolved_args.append(stripped_arg)
                # 执行构造函数
                evaluator._call_constructor(obj, resolved_args)
 
            hpl_module.register_constant(obj_name, obj, f"Object instance: {obj_name}")
        
        # 注册顶层函数到模块
        for func_name, func in functions.items():
            def make_function(fn, eval_ctx, name):
                def wrapper(*args):
                    # 验证参数数量
                    if len(args) != len(fn.params):
                        raise HPLValueError(
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
        # 注意：此时_loader_context已经设置为当前模块所在目录
        # 所以嵌套导入会正确继承当前模块的搜索路径
        for imp in imports:
            module_name_to_import = imp['module']
            alias = imp['alias']
            try:
                imported_module = load_module(module_name_to_import)
                # 使用别名或原始名称注册
                register_name = alias if alias else _get_module_file_name(module_name_to_import)
                # 注册到 HPLModule，供外部访问
                hpl_module.register_constant(register_name, imported_module, f"Imported module: {module_name_to_import}")
                # 同时注册到 evaluator 的全局作用域，供模块内部函数访问
                evaluator.global_scope[register_name] = imported_module
            except ImportError as e:
                print(f"Warning: Failed to import '{module_name_to_import}' in module '{module_name}': {e}")
                raise HPLImportError(f"Failed to import '{module_name_to_import}' in module '{module_name}': {e}") from e

        return hpl_module
        
    except FileNotFoundError as e:
        raise HPLImportError(f"Module file not found: {file_path}") from e
    except Exception as e:
        logger.error(f"Failed to parse HPL module '{module_name}': {e}")
        import traceback
        traceback.print_exc()
        raise HPLImportError(f"Failed to parse HPL module '{module_name}': {e}") from e
    finally:
        # 无论成功还是失败，都从加载中集合移除
        _loading_modules.discard(module_name)
        # 恢复之前的上下文
        _loader_context._current_file_dir = previous_context

def _parse_python_module_file(module_name, file_path):
    """
    解析本地 Python 模块文件
    返回 HPLModule 实例
    """
    try:
        # 对于包含路径的模块名，创建一个安全的导入名称
        # 将路径分隔符和特殊字符替换为下划线
        safe_module_name = module_name.replace('/', '_').replace('\\', '_').replace('.', '_').replace('-', '_')
        
        # 读取 Python 文件内容
        file_path = Path(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # 处理相对导入：将 from .xxx import 转换为 from absolute_path import
        # 计算当前模块所在目录的父目录（用于解析相对导入）
        current_dir = file_path.parent
        parent_dir = current_dir.parent
        
        # 替换相对导入
        # from .module import ... -> from parent_dir.module import ...
        import re
        
        # 处理 from . import xxx (相对导入当前包)
        source_code = re.sub(
            r'from\s+\.\s+import\s+([^#\n]+)',
            lambda m: f'from {parent_dir.name}.{current_dir.name} import {m.group(1)}',
            source_code
        )
        
        # 处理 from .module import ... (相对导入子模块)
        def replace_relative_import(match):
            dots = match.group(1)
            rel_module = match.group(2)
            imports = match.group(3)
            
            # 计算相对路径
            if dots == '.':
                # 同级目录
                abs_module = f"{parent_dir.name}.{current_dir.name}.{rel_module}"
            elif dots == '..':
                # 上级目录
                abs_module = f"{parent_dir.name}.{rel_module}"
            else:
                # 更多级，暂不处理
                return match.group(0)
            
            return f'from {abs_module} import {imports}'
        
        source_code = re.sub(
            r'from\s+(\.+)([a-zA-Z_][a-zA-Z0-9_]*)\s+import\s+([^#\n]+)',
            replace_relative_import,
            source_code
        )
        
        # 动态编译并执行修改后的代码
        compiled_code = compile(source_code, str(file_path), 'exec')
        
        # 创建模块命名空间
        module_namespace = {
            '__name__': safe_module_name,
            '__file__': str(file_path),
            '__package__': None,
        }
        
        # 执行代码
        exec(compiled_code, module_namespace)
        
        # 创建 HPL 包装模块
        hpl_module = HPLModule(module_name, f"Python module: {module_name}")
        
        # 检查是否有 HPL_MODULE 定义（显式 HPL 接口）
        if 'HPL_MODULE' in module_namespace:
            hpl_interface = module_namespace['HPL_MODULE']
            if isinstance(hpl_interface, HPLModule):
                return hpl_interface
        
        # 自动注册所有可调用对象
        for attr_name, attr in module_namespace.items():
            if not attr_name.startswith('_'):
                if callable(attr):
                    hpl_module.register_function(attr_name, attr, None, f"Python function: {attr_name}")
                else:
                    hpl_module.register_constant(attr_name, attr, f"Python constant: {attr_name}")
        
        return hpl_module
        
    except Exception as e:
        logger.warning(f"Failed to load Python module '{module_name}': {e}")
        raise HPLImportError(f"Failed to load Python module '{module_name}': {e}") from e

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
        raise HPLRuntimeError(f"Error installing package '{package_name}': {e}") from e

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
        raise HPLRuntimeError(f"Error uninstalling package '{package_name}': {e}") from e

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
    _loading_modules.clear()  # 同时清除加载中集合

def init_stdlib():
    """初始化所有标准库模块"""
    try:
        # 尝试多种导入方式以适应不同的运行环境
        try:
            # 方式1: 从 hpl_runtime.stdlib 导入（当 hpl_runtime 在 Python 路径中时）
            from hpl_runtime.stdlib import io, math, json_mod, os_mod, time_mod, string_mod, random_mod, crypto_mod, re_mod, net_mod
        except ImportError:
            # 方式2: 直接从 stdlib 导入（当在 hpl_runtime 目录中运行时）
            # 将 hpl_runtime 目录添加到 Python 路径
            hpl_runtime_dir = os.path.dirname(os.path.abspath(__file__))
            if hpl_runtime_dir not in sys.path:
                sys.path.insert(0, hpl_runtime_dir)
            from stdlib import io, math, json_mod, os_mod, time_mod, string_mod, random_mod, crypto_mod, re_mod, net_mod
        
        # 注册模块
        register_module('io', io.module)
        register_module('math', math.module)
        register_module('json', json_mod.module)
        register_module('os', os_mod.module)
        register_module('time', time_mod.module)
        register_module('string', string_mod.module)
        register_module('random', random_mod.module)
        register_module('crypto', crypto_mod.module)
        register_module('re', re_mod.module)
        register_module('net', net_mod.module)
        
    except ImportError as e:
        # 如果某些模块导入失败，记录错误但不中断
        logger.warning(f"Some stdlib modules failed to load: {e}")

# 初始化标准库
init_stdlib()
