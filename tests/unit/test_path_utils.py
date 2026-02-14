#!/usr/bin/env python3
"""
HPL 路径工具模块单元测试

测试 path_utils.py 中的所有路径处理函数
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
from pathlib import Path
from hpl_runtime.utils.path_utils import (
    resolve_include_path, get_file_directory, ensure_directory_exists
)


class TestResolveIncludePath(unittest.TestCase):
    """测试解析include路径函数"""

    def setUp(self):
        """创建临时目录结构"""
        self.temp_dir = tempfile.mkdtemp()
        self.base_file = os.path.join(self.temp_dir, "base.hpl")
        
        # 创建基础文件
        with open(self.base_file, 'w') as f:
            f.write("# base file")
        
        # 创建子目录和文件
        self.subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(self.subdir)
        self.subdir_file = os.path.join(self.subdir, "module.hpl")
        with open(self.subdir_file, 'w') as f:
            f.write("# module file")
        
        # 创建搜索路径目录
        self.search_dir = os.path.join(self.temp_dir, "search")
        os.makedirs(self.search_dir)
        self.search_file = os.path.join(self.search_dir, "search_module.hpl")
        with open(self.search_file, 'w') as f:
            f.write("# search module")

    def tearDown(self):
        """清理临时目录"""
        shutil.rmtree(self.temp_dir)

    def test_resolve_absolute_path(self):
        """测试绝对路径解析"""
        result = resolve_include_path(self.subdir_file)
        self.assertEqual(result, self.subdir_file)

    def test_resolve_absolute_path_not_exists(self):
        """测试不存在的绝对路径"""
        non_existent = os.path.join(self.temp_dir, "non_existent.hpl")
        result = resolve_include_path(non_existent)
        self.assertIsNone(result)

    def test_resolve_relative_to_base_file(self):
        """测试相对于基础文件目录的路径"""
        # 从 base.hpl 目录解析 subdir/module.hpl
        result = resolve_include_path("subdir/module.hpl", self.base_file)
        self.assertEqual(result, self.subdir_file)

    def test_resolve_relative_to_cwd(self):
        """测试相对于当前工作目录的路径"""
        # 保存原始cwd
        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            result = resolve_include_path("base.hpl")
            self.assertEqual(result, self.base_file)
        finally:
            os.chdir(original_cwd)

    def test_resolve_from_search_paths(self):
        """测试从搜索路径列表解析"""
        result = resolve_include_path(
            "search_module.hpl", 
            self.base_file, 
            [self.search_dir]
        )
        self.assertEqual(result, self.search_file)

    def test_resolve_not_found(self):
        """测试未找到文件"""
        result = resolve_include_path("non_existent.hpl", self.base_file)
        self.assertIsNone(result)

    def test_resolve_priority(self):
        """测试路径解析优先级：相对基础文件 > 相对cwd > 搜索路径"""
        # 在cwd和搜索路径中都创建同名文件，应该优先找到相对基础文件的
        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            # 创建同名文件在cwd
            cwd_file = os.path.join(self.temp_dir, "priority_test.hpl")
            with open(cwd_file, 'w') as f:
                f.write("# cwd file")
            
            # 创建同名文件在子目录（相对于base_file）
            sub_file = os.path.join(self.subdir, "priority_test.hpl")
            with open(sub_file, 'w') as f:
                f.write("# sub file")
            
            # 应该优先找到相对于base_file的（base_file在temp_dir，所以找到的是cwd_file）
            result = resolve_include_path("priority_test.hpl", self.base_file)
            # base_file的目录是temp_dir，所以优先找到cwd_file
            self.assertEqual(result, cwd_file)
        finally:
            os.chdir(original_cwd)



class TestGetFileDirectory(unittest.TestCase):
    """测试获取文件目录函数"""

    def test_get_file_directory_absolute(self):
        """测试绝对路径"""
        file_path = "/home/user/project/file.hpl"
        result = get_file_directory(file_path)
        # 在Windows上，Path.resolve()会将Unix路径转换为Windows路径
        # 所以结果可能是 "D:\\home\\user\\project" 或 "/home/user/project"
        self.assertIn("home", str(result).lower())
        self.assertIn("project", str(result).lower())


    def test_get_file_directory_relative(self):
        """测试相对路径"""
        file_path = "project/file.hpl"
        result = get_file_directory(file_path)
        # 应该解析为绝对路径
        self.assertTrue(result.is_absolute())

    def test_get_file_directory_with_spaces(self):
        """测试带空格的路径"""
        file_path = "/home/user/my project/file.hpl"
        result = get_file_directory(file_path)
        # 在Windows上，Path.resolve()会将Unix路径转换为Windows路径
        self.assertIn("home", str(result).lower())
        self.assertIn("my project", str(result).lower())



class TestEnsureDirectoryExists(unittest.TestCase):
    """测试确保目录存在函数"""

    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时目录"""
        shutil.rmtree(self.temp_dir)

    def test_ensure_directory_exists_create(self):
        """测试创建不存在的目录"""
        new_dir = os.path.join(self.temp_dir, "new", "nested", "dir")
        file_path = os.path.join(new_dir, "file.hpl")
        
        # 目录不应该存在
        self.assertFalse(os.path.exists(new_dir))
        
        ensure_directory_exists(file_path)
        
        # 目录应该被创建
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))

    def test_ensure_directory_exists_already_exists(self):
        """测试目录已存在的情况"""
        existing_dir = os.path.join(self.temp_dir, "existing")
        os.makedirs(existing_dir)
        file_path = os.path.join(existing_dir, "file.hpl")
        
        # 不应该抛出异常
        ensure_directory_exists(file_path)
        
        # 目录仍然存在
        self.assertTrue(os.path.exists(existing_dir))

    def test_ensure_directory_exists_file_in_root(self):
        """测试根目录下的文件"""
        # 使用临时目录作为根
        file_path = os.path.join(self.temp_dir, "file.hpl")
        
        # 不应该抛出异常，也不需要创建目录
        ensure_directory_exists(file_path)
        
        # 临时目录应该仍然存在
        self.assertTrue(os.path.exists(self.temp_dir))


if __name__ == '__main__':
    unittest.main()
