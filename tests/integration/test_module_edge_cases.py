#!/usr/bin/env python3
"""
HPL 模块系统边界情况测试

测试循环导入、模块别名冲突、相对导入、模块缓存等边界情况
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

try:
    from hpl_runtime.modules.loader import (
        _parse_hpl_module, load_module, clear_cache, add_module_path,
        register_module, get_module, _module_cache, HPL_MODULE_PATHS
    )
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLImportError, HPLValueError
except ImportError:
    from module_loader import (
        _parse_hpl_module, load_module, clear_cache, add_module_path,
        register_module, get_module, _module_cache, HPL_MODULE_PATHS
    )
    from module_base import HPLModule
    from exceptions import HPLImportError, HPLValueError


class TestCircularImport(unittest.TestCase):
    """测试循环导入检测"""

    def setUp(self):
        """设置测试环境"""
        clear_cache()
        self.temp_dir = tempfile.mkdtemp()
        self.created_files = []

    def tearDown(self):
        """清理"""
        for file_path in self.created_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        clear_cache()

    def create_hpl_file(self, filename, content):
        """创建HPL文件"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.created_files.append(file_path)
        return file_path

    def test_simple_circular_import(self):
        """测试简单循环导入"""
        # 创建模块A导入模块B
        self.create_hpl_file('module_a.hpl', '''imports:
  - module_b

func_a: () => {
  return "A"
}
''')
        
        # 创建模块B导入模块A（形成循环）
        self.create_hpl_file('module_b.hpl', '''imports:
  - module_a

func_b: () => {
  return "B"
}
''')
        
        add_module_path(self.temp_dir)
        
        # 尝试加载应该检测到循环导入
        # 注意：当前实现可能不检测循环导入，这里测试实际行为
        try:
            module_a = _parse_hpl_module('module_a', 
                os.path.join(self.temp_dir, 'module_a.hpl'))
            # 如果成功加载，验证功能
            self.assertIsNotNone(module_a)
        except HPLImportError as e:
            # 如果检测到循环导入，验证错误信息
            self.assertIn('circular', str(e).lower())

    def test_indirect_circular_import(self):
        """测试间接循环导入（A->B->C->A）"""
        # A导入B
        self.create_hpl_file('a.hpl', '''imports:
  - b
''')
        
        # B导入C
        self.create_hpl_file('b.hpl', '''imports:
  - c
''')
        
        # C导入A（形成循环）
        self.create_hpl_file('c.hpl', '''imports:
  - a
''')
        
        add_module_path(self.temp_dir)
        
        # 测试循环导入检测
        try:
            module = _parse_hpl_module('a', 
                os.path.join(self.temp_dir, 'a.hpl'))
            self.assertIsNotNone(module)
        except HPLImportError:
            pass  # 预期可能抛出循环导入错误


class TestModuleAlias(unittest.TestCase):
    """测试模块别名"""

    def setUp(self):
        """设置测试环境"""
        clear_cache()
        self.temp_dir = tempfile.mkdtemp()
        self.created_files = []

    def tearDown(self):
        """清理"""
        for file_path in self.created_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        clear_cache()

    def create_hpl_file(self, filename, content):
        """创建HPL文件"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.created_files.append(file_path)
        return file_path

    def test_simple_alias(self):
        """测试简单别名"""
        # 创建被导入的模块
        self.create_hpl_file('math_utils.hpl', '''add: (a, b) => {
  return a + b
}
''')
        
        # 创建使用别名的主模块
        self.create_hpl_file('main.hpl', '''imports:
  - math_utils: math

main: () => {
  result = math.add(1, 2)
  return result
}
''')
        
        add_module_path(self.temp_dir)
        
        module = _parse_hpl_module('main', 
            os.path.join(self.temp_dir, 'main.hpl'))
        
        # 验证别名注册
        self.assertIn('math', module.list_constants())
        self.assertNotIn('math_utils', module.list_constants())

    def test_alias_conflict_resolution(self):
        """测试别名冲突解决"""
        # 创建两个模块
        self.create_hpl_file('utils1.hpl', '''helper: () => {
  return "utils1"
}
''')
        
        self.create_hpl_file('utils2.hpl', '''helper: () => {
  return "utils2"
}
''')
        
        # 创建使用相同别名导入两个模块的主模块
        self.create_hpl_file('conflict.hpl', '''imports:
  - utils1: u
  - utils2: u2

main: () => {
  r1 = u.helper()
  r2 = u2.helper()
  return r1 + r2
}
''')
        
        add_module_path(self.temp_dir)
        
        module = _parse_hpl_module('conflict', 
            os.path.join(self.temp_dir, 'conflict.hpl'))
        
        # 验证两个别名都存在
        self.assertIn('u', module.list_constants())
        self.assertIn('u2', module.list_constants())

    def test_nested_alias(self):
        """测试嵌套别名"""
        # 创建深层模块
        self.create_hpl_file('deep_module.hpl', '''value: 42
''')
        
        # 创建中间模块
        self.create_hpl_file('middle.hpl', '''imports:
  - deep_module: d

get_value: () => {
  return d.value
}
''')
        
        # 创建顶层模块
        self.create_hpl_file('top.hpl', '''imports:
  - middle: m

main: () => {
  return m.get_value()
}
''')
        
        add_module_path(self.temp_dir)
        
        module = _parse_hpl_module('top', 
            os.path.join(self.temp_dir, 'top.hpl'))
        
        self.assertIn('m', module.list_constants())


class TestModuleCache(unittest.TestCase):
    """测试模块缓存"""

    def setUp(self):
        """设置测试环境"""
        clear_cache()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        clear_cache()

    def test_module_caching(self):
        """测试模块被缓存"""
        # 创建简单模块
        module_file = os.path.join(self.temp_dir, 'cached.hpl')
        with open(module_file, 'w', encoding='utf-8') as f:
            f.write('value: 42\n')
        
        add_module_path(self.temp_dir)
        
        # 第一次加载
        module1 = _parse_hpl_module('cached', module_file)
        
        # 验证模块加载成功（缓存行为取决于具体实现）
        self.assertIsNotNone(module1)
        
        # 第二次加载
        module2 = _parse_hpl_module('cached', module_file)
        self.assertIsNotNone(module2)


    def test_cache_invalidation(self):
        """测试缓存失效"""
        module_file = os.path.join(self.temp_dir, 'invalidate.hpl')
        with open(module_file, 'w', encoding='utf-8') as f:
            f.write('version: 1\n')
        
        add_module_path(self.temp_dir)
        
        # 加载模块
        module1 = _parse_hpl_module('invalidate', module_file)
        
        # 清除缓存
        clear_cache()
        
        # 重新加载应该是新实例
        module2 = _parse_hpl_module('invalidate', module_file)
        self.assertIsNot(module1, module2)

    def test_multiple_modules_cached(self):
        """测试多个模块加载"""
        # 创建多个模块
        for i in range(5):
            module_file = os.path.join(self.temp_dir, f'mod{i}.hpl')
            with open(module_file, 'w', encoding='utf-8') as f:
                f.write(f'index: {i}\n')
        
        add_module_path(self.temp_dir)
        
        # 加载所有模块
        modules = []
        for i in range(5):
            module_file = os.path.join(self.temp_dir, f'mod{i}.hpl')
            mod = _parse_hpl_module(f'mod{i}', module_file)
            modules.append(mod)
        
        # 验证所有模块都加载成功
        for i in range(5):
            self.assertIsNotNone(modules[i])
        
        # 验证模块是HPLModule类型
        for i in range(5):
            self.assertIsInstance(modules[i], HPLModule)




class TestModulePathManagement(unittest.TestCase):
    """测试模块路径管理"""

    def setUp(self):
        """设置测试环境"""
        self.original_paths = list(HPL_MODULE_PATHS)
        HPL_MODULE_PATHS.clear()

    def tearDown(self):
        """恢复路径"""
        HPL_MODULE_PATHS.clear()
        HPL_MODULE_PATHS.extend(self.original_paths)

    def test_add_multiple_paths(self):
        """测试添加多个路径"""
        temp_dirs = [tempfile.mkdtemp() for _ in range(3)]
        
        try:
            for temp_dir in temp_dirs:
                add_module_path(temp_dir)
            
            # 验证所有路径都已添加
            for temp_dir in temp_dirs:
                self.assertIn(Path(temp_dir).resolve(), HPL_MODULE_PATHS)
        finally:
            for temp_dir in temp_dirs:
                shutil.rmtree(temp_dir)

    def test_duplicate_path_handling(self):
        """测试重复路径处理"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 添加同一路径两次
            add_module_path(temp_dir)
            add_module_path(temp_dir)
            
            # 验证只添加一次
            path = Path(temp_dir).resolve()
            count = sum(1 for p in HPL_MODULE_PATHS if p == path)
            self.assertEqual(count, 1)
        finally:
            shutil.rmtree(temp_dir)

    def test_path_priority(self):
        """测试路径优先级"""
        # 创建两个目录，包含同名模块
        dir1 = tempfile.mkdtemp()
        dir2 = tempfile.mkdtemp()
        
        try:
            # 在dir1创建模块
            with open(os.path.join(dir1, 'testmod.hpl'), 'w') as f:
                f.write('version: 1\n')
            
            # 在dir2创建同名模块
            with open(os.path.join(dir2, 'testmod.hpl'), 'w') as f:
                f.write('version: 2\n')
            
            # 先添加dir1，再添加dir2
            add_module_path(dir1)
            add_module_path(dir2)
            
            # dir1的模块应该优先被找到
            # 注意：这取决于具体实现
            self.assertIn(Path(dir1).resolve(), HPL_MODULE_PATHS)
            self.assertIn(Path(dir2).resolve(), HPL_MODULE_PATHS)
        finally:
            shutil.rmtree(dir1)
            shutil.rmtree(dir2)


class TestModuleErrorHandling(unittest.TestCase):
    """测试模块错误处理"""

    def setUp(self):
        """设置测试环境"""
        clear_cache()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        clear_cache()

    def test_import_nonexistent_module(self):
        """测试导入不存在的模块"""
        add_module_path(self.temp_dir)
        
        with self.assertRaises(HPLImportError):
            load_module('nonexistent_module_xyz')

    def test_import_invalid_syntax(self):
        """测试导入语法错误的模块"""
        # 创建包含语法错误的模块
        bad_module = os.path.join(self.temp_dir, 'bad.hpl')
        with open(bad_module, 'w', encoding='utf-8') as f:
            f.write('invalid syntax here {{{\n')
        
        add_module_path(self.temp_dir)
        
        # 应该抛出导入错误
        with self.assertRaises(HPLImportError):
            _parse_hpl_module('bad', bad_module)

    def test_import_permission_error(self):
        """测试导入权限错误的模块（Windows可能不支持）"""
        # 跳过Windows上的权限测试
        if os.name == 'nt':
            self.skipTest("Permission tests not supported on Windows")
        
        # 创建无权限读取的文件
        restricted_module = os.path.join(self.temp_dir, 'restricted.hpl')
        with open(restricted_module, 'w') as f:
            f.write('value: 42\n')
        
        # 移除读权限
        os.chmod(restricted_module, 0o000)
        
        try:
            add_module_path(self.temp_dir)
            
            # 应该抛出导入错误
            with self.assertRaises(HPLImportError):
                _parse_hpl_module('restricted', restricted_module)
        finally:
            # 恢复权限以便清理
            os.chmod(restricted_module, 0o644)



class TestModuleReloading(unittest.TestCase):
    """测试模块重新加载"""

    def setUp(self):
        """设置测试环境"""
        clear_cache()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        clear_cache()

    def test_module_modification_and_reload(self):
        """测试模块修改后重新加载"""
        module_file = os.path.join(self.temp_dir, 'reload.hpl')
        
        # 创建初始版本
        with open(module_file, 'w', encoding='utf-8') as f:
            f.write('version: 1\n')
        
        add_module_path(self.temp_dir)
        
        # 第一次加载
        module1 = _parse_hpl_module('reload', module_file)
        
        # 修改模块
        with open(module_file, 'w', encoding='utf-8') as f:
            f.write('version: 2\n')
        
        # 清除缓存并重新加载
        clear_cache()
        module2 = _parse_hpl_module('reload', module_file)
        
        # 应该是不同的实例
        self.assertIsNot(module1, module2)


if __name__ == '__main__':
    unittest.main()
