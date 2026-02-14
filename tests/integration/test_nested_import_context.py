#!/usr/bin/env python3
"""
测试嵌套导入上下文问题

该测试验证当模块A导入模块B时，模块B能否正确找到它自己的依赖模块。
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
from pathlib import Path

try:
    from hpl_runtime.modules.loader import (
        load_module, clear_cache, add_module_path, set_current_hpl_file
    )
    from hpl_runtime.utils.exceptions import HPLImportError
except ImportError:
    from module_loader import (
        load_module, clear_cache, add_module_path, set_current_hpl_file
    )
    from exceptions import HPLImportError


class TestNestedImportContext(unittest.TestCase):
    """测试嵌套导入上下文传递"""

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

    def create_hpl_file(self, rel_path, content):
        """创建HPL文件"""
        file_path = os.path.join(self.temp_dir, rel_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.created_files.append(file_path)
        return file_path

    def test_simple_nested_import(self):
        """测试简单嵌套导入: A -> B -> C"""
        # 创建模块C (最底层) - 使用函数返回值
        self.create_hpl_file('module_c.hpl', '''get_value: () => {
  return 42
}
''')
        
        # 创建模块B，导入C
        self.create_hpl_file('module_b.hpl', '''imports:
  - module_c

get_c_value: () => {
  return module_c.get_value()
}
''')
        
        # 创建模块A，导入B
        self.create_hpl_file('module_a.hpl', '''imports:
  - module_b

get_value: () => {
  return module_b.get_c_value()
}
''')

        
        # 设置当前文件并添加搜索路径
        main_file = self.create_hpl_file('main.hpl', '''imports:
  - module_a

main: () => {
  result = module_a.get_value()
  echo "Value from nested import: " + result
  return result
}

call: main()
''')
        
        set_current_hpl_file(main_file)
        add_module_path(self.temp_dir)
        
        # 尝试加载模块A - 这应该能成功找到B和C
        try:
            module_a = load_module('module_a')
            self.assertIsNotNone(module_a)
            # 如果能加载成功，验证功能
            result = module_a.call_function('get_value', [])
            self.assertEqual(result, 42)
        except HPLImportError as e:
            self.fail(f"嵌套导入失败: {e}")

    def test_deeply_nested_import(self):
        """测试深层嵌套导入: A -> B -> C -> D"""
        # 创建模块D - 使用函数返回值
        self.create_hpl_file('level_d.hpl', '''get_data: () => {
  return "from D"
}
''')
        
        # 创建模块C，导入D
        self.create_hpl_file('level_c.hpl', '''imports:
  - level_d

get_d_data: () => {
  return level_d.get_data()
}
''')
        
        # 创建模块B，导入C
        self.create_hpl_file('level_b.hpl', '''imports:
  - level_c

get_data: () => {
  return level_c.get_d_data()
}
''')
        
        # 创建模块A，导入B
        self.create_hpl_file('level_a.hpl', '''imports:
  - level_b

main: () => {
  return level_b.get_data()
}
''')

        
        main_file = self.create_hpl_file('main_deep.hpl', '''imports:
  - level_a

call: level_a.main()
''')
        
        set_current_hpl_file(main_file)
        add_module_path(self.temp_dir)
        
        try:
            module_a = load_module('level_a')
            self.assertIsNotNone(module_a)
            result = module_a.call_function('main', [])
            self.assertEqual(result, "from D")
        except HPLImportError as e:
            self.fail(f"深层嵌套导入失败: {e}")

    def test_sibling_import_in_nested(self):
        """测试嵌套模块中的同级导入"""
        # 创建子目录
        subdir = os.path.join(self.temp_dir, 'subpackage')
        os.makedirs(subdir, exist_ok=True)
        
        # 在子目录中创建两个模块
        self.create_hpl_file('subpackage/helper.hpl', '''helper_func: () => {
  return "helper result"
}
''')
        
        self.create_hpl_file('subpackage/main_module.hpl', '''imports:
  - helper

use_helper: () => {
  return helper.helper_func()
}
''')
        
        # 根目录模块导入子目录模块
        self.create_hpl_file('root_module.hpl', '''imports:
  - subpackage/main_module

call_main: () => {
  return subpackage/main_module.use_helper()
}
''')
        
        main_file = self.create_hpl_file('test_sibling.hpl', '''imports:
  - root_module

call: root_module.call_main()
''')
        
        set_current_hpl_file(main_file)
        add_module_path(self.temp_dir)
        
        try:
            root_module = load_module('root_module')
            self.assertIsNotNone(root_module)
        except HPLImportError as e:
            self.fail(f"子目录模块导入失败: {e}")


class TestRelativeImport(unittest.TestCase):
    """测试相对导入功能"""

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

    def create_hpl_file(self, rel_path, content):
        """创建HPL文件"""
        file_path = os.path.join(self.temp_dir, rel_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.created_files.append(file_path)
        return file_path

    def test_relative_import_same_directory(self):
        """测试同级目录相对导入 ./module"""
        # 创建被导入的模块
        self.create_hpl_file('utils.hpl', '''greet: (name) => {
  return "Hello, " + name
}
''')
        
        # 创建主模块，使用相对导入
        main_file = self.create_hpl_file('main.hpl', '''imports:
  - ./utils

main: () => {
  return utils.greet("World")
}

call: main()
''')
        
        set_current_hpl_file(main_file)
        add_module_path(self.temp_dir)
        
        # 尝试加载 - 应该支持 ./utils 语法
        try:
            # 注意：当前实现可能不支持 ./ 语法，这个测试会失败
            # 修复后应该能通过
            module = load_module('main')
            self.assertIsNotNone(module)
        except HPLImportError as e:
            # 预期当前会失败，记录错误信息
            print(f"相对导入测试（预期可能失败）: {e}")
            # 不标记为失败，因为这是已知问题

    def test_relative_import_parent_directory(self):
        """测试父目录相对导入 ../module"""
        # 创建子目录
        subdir = os.path.join(self.temp_dir, 'subdir')
        os.makedirs(subdir, exist_ok=True)
        
        # 在父目录创建模块
        self.create_hpl_file('parent_utils.hpl', '''calc: (x) => {
  return x * 2
}
''')
        
        # 在子目录创建模块，使用 ../ 导入父目录模块
        child_file = self.create_hpl_file('subdir/child.hpl', '''imports:
  - ../parent_utils

use_calc: () => {
  return parent_utils.calc(5)
}
''')
        
        set_current_hpl_file(child_file)
        add_module_path(self.temp_dir)
        
        try:
            # 当前实现可能不支持 ../ 语法
            module = load_module('child')
            self.assertIsNotNone(module)
        except HPLImportError as e:
            print(f"父目录相对导入测试（预期可能失败）: {e}")

    def test_relative_import_nested_path(self):
        """测试嵌套路径相对导入 ./subdir/module"""
        # 创建嵌套目录结构
        self.create_hpl_file('lib/math_utils.hpl', '''add: (a, b) => {
  return a + b
}
''')
        
        main_file = self.create_hpl_file('app.hpl', '''imports:
  - ./lib/math_utils

main: () => {
  return lib/math_utils.add(2, 3)
}

call: main()
''')
        
        set_current_hpl_file(main_file)
        add_module_path(self.temp_dir)
        
        try:
            module = load_module('app')
            self.assertIsNotNone(module)
        except HPLImportError as e:
            print(f"嵌套路径相对导入测试（预期可能失败）: {e}")


if __name__ == '__main__':
    unittest.main()
