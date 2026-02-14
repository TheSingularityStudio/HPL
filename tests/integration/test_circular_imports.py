#!/usr/bin/env python3
"""
HPL 循环导入测试

测试循环导入检测和处理机制
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
import tempfile
import shutil
from pathlib import Path

from hpl_runtime.modules.loader import (
    load_module, _parse_hpl_module, clear_cache, add_module_path,
    _loading_modules, _module_cache
)
from hpl_runtime.utils.exceptions import HPLImportError


class TestCircularImports(unittest.TestCase):
    """测试循环导入检测"""

    def setUp(self):
        """测试前准备"""
        clear_cache()
        self.temp_dirs = []

    def tearDown(self):
        """清理临时目录"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def create_temp_module(self, name, content, temp_dir):
        """创建临时模块文件"""
        file_path = Path(temp_dir) / f"{name}.hpl"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path)

    def test_simple_circular_import(self):
        """测试简单循环导入检测"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        # 模块 A 导入 B
        module_a = """imports:
  - module_b

functions:
  getA: () => {
    return "A"
  }
"""
        # 模块 B 导入 A（形成循环）
        module_b = """imports:
  - module_a

functions:
  getB: () => {
    return "B"
  }
"""
        self.create_temp_module("module_a", module_a, temp_dir)
        self.create_temp_module("module_b", module_b, temp_dir)
        add_module_path(temp_dir)

        # 应该检测到循环导入
        with self.assertRaises(HPLImportError) as context:
            load_module("module_a", [temp_dir])
        
        error_msg = str(context.exception)
        self.assertIn("Circular import", error_msg)

    def test_indirect_circular_import(self):
        """测试间接循环导入检测"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        # A -> B -> C -> A
        module_a = """imports:
  - module_b

functions:
  getA: () => {
    return "A"
  }
"""
        module_b = """imports:
  - module_c

functions:
  getB: () => {
    return "B"
  }
"""
        module_c = """imports:
  - module_a

functions:
  getC: () => {
    return "C"
  }
"""
        self.create_temp_module("module_a", module_a, temp_dir)
        self.create_temp_module("module_b", module_b, temp_dir)
        self.create_temp_module("module_c", module_c, temp_dir)
        add_module_path(temp_dir)

        with self.assertRaises(HPLImportError) as context:
            load_module("module_a", [temp_dir])
        
        self.assertIn("Circular import", str(context.exception))

    def test_self_import(self):
        """测试自导入检测"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        # 模块导入自己
        module_self = """imports:
  - self_module

functions:
  getValue: () => {
    return 42
  }
"""
        self.create_temp_module("self_module", module_self, temp_dir)
        add_module_path(temp_dir)

        with self.assertRaises(HPLImportError) as context:
            load_module("self_module", [temp_dir])
        
        self.assertIn("Circular import", str(context.exception))

    def test_no_false_positive(self):
        """测试无循环导入时不误报"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        # A -> B, A -> C, B -> C（无循环）
        module_a = """imports:
  - module_b2
  - module_c2

functions:
  getA: () => {
    return "A"
  }
"""
        module_b = """imports:
  - module_c2

functions:
  getB: () => {
    return "B"
  }
"""
        module_c = """functions:
  getC: () => {
    return "C"
  }
"""
        self.create_temp_module("module_a2", module_a, temp_dir)
        self.create_temp_module("module_b2", module_b, temp_dir)
        self.create_temp_module("module_c2", module_c, temp_dir)
        add_module_path(temp_dir)

        # 应该成功加载
        module = load_module("module_a2", [temp_dir])
        self.assertIsNotNone(module)

    def test_circular_import_error_message(self):
        """测试循环导入错误信息"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        module_a = """imports:
  - module_b3

functions:
  getA: () => {
    return "A"
  }
"""
        module_b = """imports:
  - module_a3

functions:
  getB: () => {
    return "B"
  }
"""
        self.create_temp_module("module_a3", module_a, temp_dir)
        self.create_temp_module("module_b3", module_b, temp_dir)
        add_module_path(temp_dir)

        with self.assertRaises(HPLImportError) as context:
            load_module("module_a3", [temp_dir])
        
        error_msg = str(context.exception)
        # 应该包含导入链信息
        self.assertIn("->", error_msg)

    def test_loading_modules_set_cleared_on_error(self):
        """测试错误时加载集合被清理"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        module_a = """imports:
  - module_b4

functions:
  getA: () => {
    return "A"
  }
"""
        module_b = """imports:
  - module_a4

functions:
  getB: () => {
    return "B"
  }
"""
        self.create_temp_module("module_a4", module_a, temp_dir)
        self.create_temp_module("module_b4", module_b, temp_dir)
        add_module_path(temp_dir)

        # 第一次尝试应该失败
        with self.assertRaises(HPLImportError):
            load_module("module_a4", [temp_dir])
        
        # 加载集合应该被清理
        self.assertEqual(len(_loading_modules), 0)

    def test_complex_circular_dependency(self):
        """测试复杂循环依赖"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        # A -> B -> C -> D -> B (循环)
        module_a = """imports:
  - module_b5

functions:
  getA: () => {
    return "A"
  }
"""
        module_b = """imports:
  - module_c5

functions:
  getB: () => {
    return "B"
  }
"""
        module_c = """imports:
  - module_d5

functions:
  getC: () => {
    return "C"
  }
"""
        module_d = """imports:
  - module_b5

functions:
  getD: () => {
    return "D"
  }
"""
        self.create_temp_module("module_a5", module_a, temp_dir)
        self.create_temp_module("module_b5", module_b, temp_dir)
        self.create_temp_module("module_c5", module_c, temp_dir)
        self.create_temp_module("module_d5", module_d, temp_dir)
        add_module_path(temp_dir)

        with self.assertRaises(HPLImportError) as context:
            load_module("module_a5", [temp_dir])
        
        self.assertIn("Circular import", str(context.exception))


class TestImportEdgeCases(unittest.TestCase):
    """测试导入边界情况"""

    def setUp(self):
        clear_cache()
        self.temp_dirs = []

    def tearDown(self):
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def create_temp_module(self, name, content, temp_dir):
        file_path = Path(temp_dir) / f"{name}.hpl"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path)

    def test_import_with_relative_path(self):
        """测试相对路径导入"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        # 创建子目录
        sub_dir = Path(temp_dir) / "subdir"
        sub_dir.mkdir()

        # 主模块
        main_module = """imports:
  - subdir/helper

functions:
  main: () => {
    return helper.getValue()
  }
"""
        # 子模块
        helper_module = """functions:
  getValue: () => {
    return 42
  }
"""
        self.create_temp_module("main", main_module, temp_dir)
        with open(sub_dir / "helper.hpl", 'w', encoding='utf-8') as f:
            f.write(helper_module)
        add_module_path(temp_dir)

        # 相对路径导入应该工作
        module = load_module("main", [temp_dir])
        self.assertIsNotNone(module)

    def test_import_nonexistent_module(self):
        """测试导入不存在的模块"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        main_module = """imports:
  - nonexistent_module

functions:
  main: () => {
    return 0
  }
"""
        self.create_temp_module("main2", main_module, temp_dir)
        add_module_path(temp_dir)

        with self.assertRaises(HPLImportError) as context:
            load_module("main2", [temp_dir])
        
        self.assertIn("not found", str(context.exception).lower())

    def test_import_with_alias(self):
        """测试带别名的导入"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        helper_module = """functions:
  getValue: () => {
    return 42
  }
"""
        main_module = """imports:
  - helper2: h

functions:
  main: () => {
    return h.getValue()
  }
"""
        self.create_temp_module("helper2", helper_module, temp_dir)
        self.create_temp_module("main3", main_module, temp_dir)
        add_module_path(temp_dir)

        module = load_module("main3", [temp_dir])
        self.assertIsNotNone(module)
        # 别名应该被注册
        self.assertIn("h", module.list_constants())

    def test_multiple_imports_same_module(self):
        """测试多次导入同一模块"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        helper_module = """functions:
  getValue: () => {
    return 42
  }
"""
        main_module = """imports:
  - helper3
  - helper3: h

functions:
  main: () => {
    return helper3.getValue()
  }
"""
        self.create_temp_module("helper3", helper_module, temp_dir)
        self.create_temp_module("main4", main_module, temp_dir)
        add_module_path(temp_dir)

        # 应该能加载，但可能有警告
        module = load_module("main4", [temp_dir])
        self.assertIsNotNone(module)


if __name__ == '__main__':
    unittest.main()
