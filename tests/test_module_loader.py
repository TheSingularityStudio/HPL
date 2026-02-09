#!/usr/bin/env python3
"""
HPL 模块加载器单元测试

测试内容包括：
1. 类构造函数调用（带 __init__）
2. 顶层函数注册和调用
3. 对象实例化（带 __init_args__）
4. 模块导入处理
5. 错误处理（参数数量验证等）
6. 标准库模块加载
7. 缓存管理
"""

import sys
import os
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from hpl_runtime.modules.loader import (
        _parse_hpl_module, load_module, clear_cache, add_module_path,
        register_module, get_module, install_package, uninstall_package,
        list_installed_packages, _module_cache, _stdlib_modules
    )
    from hpl_runtime.core.models import HPLObject, HPLClass, HPLFunction
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLImportError
except ImportError:
    from module_loader import (
        _parse_hpl_module, load_module, clear_cache, add_module_path,
        register_module, get_module, install_package, uninstall_package,
        list_installed_packages, _module_cache, _stdlib_modules
    )
    from models import HPLObject, HPLClass, HPLFunction
    from module_base import HPLModule
    from exceptions import HPLImportError



class TestParseHPLModule(unittest.TestCase):
    """测试 _parse_hpl_module 函数的各个功能"""
    
    def setUp(self):
        """每个测试方法前清除缓存"""
        clear_cache()
        self.temp_dirs = []
    
    def tearDown(self):
        """清理临时目录"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def create_temp_hpl_file(self, content, filename="test_module.hpl"):
        """创建临时 HPL 文件"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        file_path = Path(temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path), temp_dir
    
    def test_class_constructor_with_init(self):
        """测试带 __init__ 的类构造函数"""
        hpl_content = """classes:
  Person:
    __init__: (name, age) => {
      this.name = name
      this.age = age
    }
    greet: () => {
      echo "Hello, I'm " + this.name
    }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        
        module = _parse_hpl_module("test_person", file_path)
        self.assertIsNotNone(module, "模块解析失败")
        
        # 检查类是否注册为函数
        self.assertIn("Person", module.list_functions(), "Person 类未注册为函数")
        
        # 获取构造函数信息
        func_info = module.functions["Person"]
        self.assertEqual(func_info["param_count"], 2, f"构造函数参数数量应为 2，实际为 {func_info['param_count']}")
        
        # 调用构造函数创建对象
        obj = module.call_function("Person", ["Alice", 25])
        self.assertIsInstance(obj, HPLObject, "返回值应为 HPLObject 实例")
        self.assertEqual(obj.hpl_class.name, "Person", "对象类名应为 Person")
        
        # 检查属性是否正确设置
        self.assertEqual(obj.attributes.get("name"), "Alice", f"name 属性应为 'Alice'，实际为 {obj.attributes.get('name')}")
        self.assertEqual(obj.attributes.get("age"), 25, f"age 属性应为 25，实际为 {obj.attributes.get('age')}")
    
    def test_class_constructor_wrong_args(self):
        """测试构造函数参数数量错误"""
        hpl_content = """classes:
  Point:
    __init__: (x, y) => {
      this.x = x
      this.y = y
    }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        
        module = _parse_hpl_module("test_point", file_path)
        self.assertIsNotNone(module)
        
        # 尝试用错误数量的参数调用
        with self.assertRaises(ValueError) as context:
            module.call_function("Point", [1])  # 只传1个参数，需要2个
        
        self.assertIn("expects 2 arguments, got 1", str(context.exception))
    
    def test_top_level_functions(self):
        """测试顶层函数注册和调用"""
        hpl_content = """add: (a, b) => {
  return a + b
}

multiply: (x, y) => {
  return x * y
}

main: () => {
  echo "Hello from main"
}
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        
        module = _parse_hpl_module("test_funcs", file_path)
        self.assertIsNotNone(module)
        
        # 检查函数是否注册
        self.assertIn("add", module.list_functions(), "add 函数未注册")
        self.assertIn("multiply", module.list_functions(), "multiply 函数未注册")
        self.assertIn("main", module.list_functions(), "main 函数未注册")
        
        # 调用 add 函数
        result = module.call_function("add", [3, 5])
        self.assertEqual(result, 8, f"add(3, 5) 应返回 8，实际返回 {result}")
        
        # 调用 multiply 函数
        result = module.call_function("multiply", [4, 7])
        self.assertEqual(result, 28, f"multiply(4, 7) 应返回 28，实际返回 {result}")
        
        # 测试参数数量错误
        with self.assertRaises(ValueError) as context:
            module.call_function("add", [1])
        
        self.assertIn("expects 2 arguments, got 1", str(context.exception))
    
    def test_object_with_init_args(self):
        """测试带 __init_args__ 的对象实例化"""
        hpl_content = """classes:
  Rectangle:
    __init__: (width, height) => {
      this.width = width
      this.height = height
    }
    area: () => {
      return this.width * this.height
    }

objects:
  myRect: Rectangle(10, 20)
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        
        module = _parse_hpl_module("test_objects", file_path)
        self.assertIsNotNone(module)
        
        # 检查对象是否注册为常量
        self.assertIn("myRect", module.list_constants(), "myRect 对象未注册为常量")
        
        # 获取对象
        obj = module.get_constant("myRect")
        self.assertIsInstance(obj, HPLObject, "myRect 应为 HPLObject 实例")
        
        # 检查构造函数是否被执行
        self.assertEqual(obj.attributes.get("width"), 10, f"width 应为 10，实际为 {obj.attributes.get('width')}")
        self.assertEqual(obj.attributes.get("height"), 20, f"height 应为 20，实际为 {obj.attributes.get('height')}")
    
    def test_module_imports(self):
        """测试模块导入处理"""
        # 先创建一个被导入的模块
        math_content = """add: (a, b) => {
  return a + b
}
"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        math_file = Path(temp_dir) / "math_utils.hpl"
        with open(math_file, 'w', encoding='utf-8') as f:
            f.write(math_content)
        
        # 创建主模块，导入 math_utils
        main_content = f"""imports:
  - math_utils

useAdd: (x, y) => {{
  return math_utils.add(x, y)
}}
"""
        main_file = Path(temp_dir) / "main_module.hpl"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        # 添加临时目录到模块搜索路径
        add_module_path(temp_dir)
        
        # 解析主模块
        module = _parse_hpl_module("main_module", str(main_file))
        self.assertIsNotNone(module)
        
        # 检查导入的模块是否注册为常量
        self.assertIn("math_utils", module.list_constants(), "math_utils 未注册为常量")
        
        # 获取导入的模块
        imported = module.get_constant("math_utils")
        self.assertIsNotNone(imported, "导入的模块不应为 None")
    
    def test_module_import_with_alias(self):
        """测试带别名的模块导入 - 使用正确的 YAML 字典格式"""
        # 创建被导入的模块
        utils_content = """greet: (name) => {
  return "Hello, " + name
}
"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        utils_file = Path(temp_dir) / "utils.hpl"
        with open(utils_file, 'w', encoding='utf-8') as f:
            f.write(utils_content)
        
        # 创建主模块，使用别名导入 - 使用正确的 YAML 字典格式
        main_content = f"""imports:
  - utils: u

test: () => {{
  return u.greet("World")
}}
"""
        main_file = Path(temp_dir) / "alias_module.hpl"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        add_module_path(temp_dir)
        
        module = _parse_hpl_module("alias_module", str(main_file))
        self.assertIsNotNone(module)
        
        # 检查别名是否注册
        self.assertIn("u", module.list_constants(), "别名 'u' 未注册")
        self.assertNotIn("utils", module.list_constants(), "原始名称不应注册（使用了别名）")
    
    def test_class_without_init(self):
        """测试没有 __init__ 的类"""
        hpl_content = """classes:
  SimpleClass:
    sayHello: () => {
      echo "Hello"
    }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        
        module = _parse_hpl_module("test_simple", file_path)
        self.assertIsNotNone(module)
        
        # 检查构造函数参数数量为 0
        func_info = module.functions["SimpleClass"]
        self.assertEqual(func_info["param_count"], 0, "无 __init__ 的类参数数量应为 0")
        
        # 调用构造函数（不传参数）
        obj = module.call_function("SimpleClass", [])
        self.assertIsInstance(obj, HPLObject, "应返回 HPLObject 实例")
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效文件 - 应该抛出 HPLImportError
        with self.assertRaises(HPLImportError):
            _parse_hpl_module("nonexistent", "/path/to/nonexistent.hpl")



class TestModuleCache(unittest.TestCase):
    """测试模块缓存功能"""
    
    def setUp(self):
        """清除缓存"""
        clear_cache()
    
    def test_clear_cache(self):
        """测试清除缓存功能"""
        # 先添加一些内容到缓存
        _module_cache["test_module"] = MagicMock()
        
        # 清除缓存
        clear_cache()
        
        # 验证缓存已清空
        self.assertEqual(len(_module_cache), 0, "缓存应该被清空")
    
    def test_module_caching(self):
        """测试模块被缓存"""
        hpl_content = """test: () => {
  return 42
}
"""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "cached.hpl"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(hpl_content)
        
        try:
            # 添加临时目录到模块路径
            add_module_path(temp_dir)
            
            # 使用 load_module 加载（会触发缓存）
            module1 = load_module("cached", [temp_dir])
            self.assertIsNotNone(module1)
            
            # 验证模块已被缓存
            self.assertIn("cached", _module_cache)
            
            # 第二次加载应该返回缓存的版本
            module2 = load_module("cached", [temp_dir])
            self.assertIs(module1, module2, "应该返回相同的缓存对象")
        finally:
            shutil.rmtree(temp_dir)
            # 清理缓存
            if "cached" in _module_cache:
                del _module_cache["cached"]



class TestStandardLibrary(unittest.TestCase):
    """测试标准库模块"""
    
    def test_get_registered_modules(self):
        """测试获取已注册的标准库模块"""
        # 标准库模块应该在初始化时注册
        stdlib_names = ['io', 'math', 'json', 'os', 'time']
        
        for name in stdlib_names:
            module = get_module(name)
            # 注意：某些模块可能加载失败，但至少应该能获取
            if module is not None:
                self.assertIsInstance(module, HPLModule, f"{name} 应该是 HPLModule 实例")
    
    def test_module_has_functions_and_constants(self):
        """测试标准库模块包含函数和常量"""
        math_module = get_module('math')
        if math_module:
            # math 模块应该有 PI 常量
            self.assertIn('PI', math_module.list_constants(), "math 模块应该有 PI 常量")
            
            # math 模块应该有 sqrt 函数
            self.assertIn('sqrt', math_module.list_functions(), "math 模块应该有 sqrt 函数")


class TestModulePathManagement(unittest.TestCase):
    """测试模块路径管理"""
    
    def setUp(self):
        """保存原始路径"""
        try:
            from hpl_runtime.modules.loader import HPL_MODULE_PATHS
        except ImportError:
            from module_loader import HPL_MODULE_PATHS
        self.original_paths = HPL_MODULE_PATHS.copy()
    
    def tearDown(self):
        """恢复原始路径"""
        try:
            from hpl_runtime.modules.loader import HPL_MODULE_PATHS
        except ImportError:
            from module_loader import HPL_MODULE_PATHS
        HPL_MODULE_PATHS.clear()
        HPL_MODULE_PATHS.extend(self.original_paths)
    
    def test_add_module_path(self):
        """测试添加模块搜索路径"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            add_module_path(temp_dir)
            
            # 验证路径已添加
            from hpl_runtime.modules.loader import HPL_MODULE_PATHS
            self.assertIn(Path(temp_dir).resolve(), HPL_MODULE_PATHS)
        finally:
            shutil.rmtree(temp_dir)


class TestPackageManagement(unittest.TestCase):
    """测试包管理功能（使用 mock）"""
    
    @patch('subprocess.run')
    def test_install_package_success(self, mock_run):
        """测试安装包成功"""
        mock_run.return_value = MagicMock(returncode=0, stderr='')
        
        result = install_package('requests', '2.28.0')
        
        self.assertTrue(result)
        mock_run.assert_called_once()
        # 验证命令包含正确的参数
        call_args = mock_run.call_args[0][0]
        self.assertIn('pip', call_args)
        self.assertIn('requests==2.28.0', call_args)
    
    @patch('subprocess.run')
    def test_install_package_failure(self, mock_run):
        """测试安装包失败"""
        mock_run.return_value = MagicMock(returncode=1, stderr='Package not found')
        
        result = install_package('nonexistent-package')
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    @patch('shutil.rmtree')
    def test_uninstall_package_from_directory(self, mock_rmtree, mock_run):
        """测试从目录卸载包"""
        # 创建一个临时目录模拟包
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 模拟包目录存在
            package_dir = Path(temp_dir) / 'test_package'
            package_dir.mkdir()
            
            with patch('hpl_runtime.module_loader.HPL_PACKAGES_DIR', Path(temp_dir)):
                result = uninstall_package('test_package')
                self.assertTrue(result)
                mock_rmtree.assert_called_once_with(package_dir)
        finally:
            shutil.rmtree(temp_dir)

    
    @patch('subprocess.run')
    def test_uninstall_package_with_pip(self, mock_run):
        """测试使用 pip 卸载包"""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = uninstall_package('requests')
        
        self.assertTrue(result)
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn('uninstall', call_args)
        self.assertIn('requests', call_args)


class TestLoadModule(unittest.TestCase):
    """测试 load_module 函数"""
    
    def setUp(self):
        """清除缓存"""
        clear_cache()
    
    def test_load_nonexistent_module(self):
        """测试加载不存在的模块"""
        with self.assertRaises(HPLImportError):
            load_module('nonexistent_module_xyz')

    
    def test_load_stdlib_module(self):
        """测试加载标准库模块"""
        # 尝试加载 math 标准库模块
        try:
            module = load_module('math')
            self.assertIsNotNone(module)
            self.assertIsInstance(module, HPLModule)
        except ImportError:
            # 如果标准库未初始化，跳过
            self.skipTest("标准库未初始化")


if __name__ == '__main__':
    unittest.main()
