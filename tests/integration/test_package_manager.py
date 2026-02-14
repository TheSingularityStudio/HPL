#!/usr/bin/env python3
"""
HPL 包管理器单元测试

测试包管理器模块的主要功能：
1. 命令行参数解析
2. 包安装和卸载
3. 包列表和搜索
4. 模块路径管理
"""

import sys
import os
import tempfile
import shutil
import io
import contextlib
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call


# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from hpl_runtime.modules.package_manager import (
        main, cmd_install, cmd_uninstall, cmd_list, 
        cmd_search, cmd_update, cmd_info, cmd_path
    )
    from hpl_runtime.modules.loader import HPL_PACKAGES_DIR
except ImportError:
    from package_manager import (
        main, cmd_install, cmd_uninstall, cmd_list, 
        cmd_search, cmd_update, cmd_info, cmd_path
    )
    from module_loader import HPL_PACKAGES_DIR


class TestPackageManagerCommands(unittest.TestCase):
    """测试包管理器命令"""
    
    def setUp(self):
        """测试前准备"""
        self.original_argv = sys.argv.copy()
    
    def tearDown(self):
        """清理"""
        sys.argv = self.original_argv
    
    @patch('hpl_runtime.modules.package_manager.install_package')
    def test_cmd_install(self, mock_install):

        """测试安装命令"""
        mock_install.return_value = True
        
        # 创建模拟参数
        args = MagicMock()
        args.package = 'requests'
        args.version = None
        
        # 捕获输出
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_install(args)
        
        # 验证 install_package 被调用
        mock_install.assert_called_once_with('requests', None)
        
        # 验证输出包含成功信息
        result = output.getvalue()
        self.assertIn("Installing 'requests'", result)
        self.assertIn("installed successfully", result)
    
    @patch('hpl_runtime.modules.package_manager.install_package')
    def test_cmd_install_with_version(self, mock_install):

        """测试带版本号的安装命令"""
        mock_install.return_value = True
        
        args = MagicMock()
        args.package = 'numpy'
        args.version = '1.24.0'
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_install(args)
        
        mock_install.assert_called_once_with('numpy', '1.24.0')
    
    @patch('hpl_runtime.modules.package_manager.install_package')
    def test_cmd_install_failure(self, mock_install):

        """测试安装失败"""
        mock_install.return_value = False
        
        args = MagicMock()
        args.package = 'nonexistent'
        args.version = None
        
        with self.assertRaises(SystemExit) as context:
            cmd_install(args)
        
        self.assertEqual(context.exception.code, 1)
    
    @patch('hpl_runtime.modules.package_manager.uninstall_package')
    def test_cmd_uninstall(self, mock_uninstall):

        """测试卸载命令"""
        mock_uninstall.return_value = True
        
        args = MagicMock()
        args.package = 'requests'
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_uninstall(args)
        
        mock_uninstall.assert_called_once_with('requests')
        
        result = output.getvalue()
        self.assertIn("Uninstalling 'requests'", result)
        self.assertIn("uninstalled successfully", result)
    
    @patch('hpl_runtime.modules.package_manager.list_installed_packages')
    def test_cmd_list(self, mock_list):

        """测试列表命令"""
        mock_list.return_value = ['requests', 'numpy', 'pandas']
        
        args = MagicMock()
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_list(args)
        
        result = output.getvalue()
        self.assertIn("Installed HPL Packages", result)
        self.assertIn("requests", result)
        self.assertIn("numpy", result)
        self.assertIn("pandas", result)
        self.assertIn("Total: 3 packages", result)
    
    @patch('hpl_runtime.modules.package_manager.list_installed_packages')
    def test_cmd_list_empty(self, mock_list):

        """测试空列表命令"""
        mock_list.return_value = []
        
        args = MagicMock()
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_list(args)
        
        result = output.getvalue()
        self.assertIn("No packages installed", result)
        self.assertIn("Total: 0 packages", result)
    
    @patch('subprocess.run')
    def test_cmd_search_success(self, mock_run):
        """测试搜索命令成功"""
        mock_run.return_value = MagicMock(returncode=0, stdout='Package: requests\nVersion: 2.28.0')
        
        args = MagicMock()
        args.query = 'http'
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_search(args)
        
        result = output.getvalue()
        self.assertIn("Searching for 'http'", result)
    
    @patch('subprocess.run')
    def test_cmd_search_failure(self, mock_run):
        """测试搜索命令失败"""
        mock_run.return_value = MagicMock(returncode=1, stderr='Search failed')
        
        args = MagicMock()
        args.query = 'http'
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_search(args)
        
        result = output.getvalue()
        self.assertIn("Search failed", result)
    
    @patch('hpl_runtime.modules.package_manager.list_installed_packages')
    @patch('hpl_runtime.modules.package_manager.install_package')
    def test_cmd_update(self, mock_install, mock_list):

        """测试更新命令"""
        mock_list.return_value = ['requests', 'numpy']
        mock_install.return_value = True
        
        args = MagicMock()
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_update(args)
        
        # 验证每个包都被更新
        self.assertEqual(mock_install.call_count, 2)
        self.assertIn("Updated: 2", output.getvalue())
    
    @patch('hpl_runtime.modules.package_manager.list_installed_packages')
    def test_cmd_info_installed(self, mock_list):
        mock_list.return_value = ['requests']

        # 创建临时包目录
        temp_dir = tempfile.mkdtemp()
        try:
            with patch('hpl_runtime.modules.package_manager.HPL_PACKAGES_DIR', Path(temp_dir)):

                # 创建包目录
                pkg_dir = Path(temp_dir) / 'requests'
                pkg_dir.mkdir()

                args = MagicMock()
                args.package = 'requests'

                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    cmd_info(args)

                result = output.getvalue()
                self.assertIn("Package information for 'requests'", result)
                self.assertIn("Installed", result)
        finally:
            shutil.rmtree(temp_dir)

    
    @patch('hpl_runtime.modules.package_manager.list_installed_packages')
    def test_cmd_info_not_installed(self, mock_list):

        """测试显示未安装包信息"""
        mock_list.return_value = []
        
        args = MagicMock()
        args.package = 'nonexistent'
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_info(args)
        
        result = output.getvalue()
        self.assertIn("Not installed", result)
    
    @patch('hpl_runtime.modules.package_manager.add_module_path')
    def test_cmd_path_add(self, mock_add):

        """测试添加模块路径"""
        args = MagicMock()
        args.add = '/new/path'
        args.list = False
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_path(args)
        
        mock_add.assert_called_once_with('/new/path')
        self.assertIn("Added module path", output.getvalue())
    
    def test_cmd_path_list(self):
        """测试列出模块路径"""
        args = MagicMock()
        args.add = None
        args.list = True
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_path(args)
        
        result = output.getvalue()
        self.assertIn("Module Search Paths", result)


class TestPackageManagerMain(unittest.TestCase):
    """测试包管理器主函数"""
    
    def setUp(self):
        """测试前准备"""
        self.original_argv = sys.argv.copy()
    
    def tearDown(self):
        """清理"""
        sys.argv = self.original_argv
    
    @patch('hpl_runtime.modules.package_manager.cmd_install')
    def test_main_install_command(self, mock_cmd):

        """测试主函数安装命令"""
        with patch.object(sys, 'argv', ['hpl', 'install', 'requests']):
            main()
        
        mock_cmd.assert_called_once()
    
    @patch('hpl_runtime.modules.package_manager.cmd_list')
    def test_main_list_command(self, mock_cmd):

        """测试主函数列表命令"""
        with patch.object(sys, 'argv', ['hpl', 'list']):
            main()
        
        mock_cmd.assert_called_once()
    
    def test_main_no_command(self):
        """测试主函数无命令"""
        with patch.object(sys, 'argv', ['hpl']):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # 应该正常退出（显示帮助）
            self.assertEqual(context.exception.code, 0)
    
    def test_main_help(self):
        """测试主函数帮助"""
        with patch.object(sys, 'argv', ['hpl', '--help']):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # --help 应该返回 0
            self.assertEqual(context.exception.code, 0)


class TestPackageManagerEdgeCases(unittest.TestCase):
    """测试包管理器边界情况"""
    
    @patch('hpl_runtime.modules.package_manager.install_package')
    def test_install_with_complex_package_name(self, mock_install):

        """测试安装复杂包名"""
        mock_install.return_value = True
        
        # 测试带 extras 的包名
        args = MagicMock()
        args.package = 'requests[security]'
        args.version = None
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_install(args)
        
        mock_install.assert_called_once_with('requests[security]', None)
    
    @patch('hpl_runtime.modules.package_manager.list_installed_packages')
    @patch('hpl_runtime.modules.package_manager.install_package')
    def test_update_with_failed_package(self, mock_install, mock_list):

        """测试更新时部分包失败"""
        mock_list.return_value = ['pkg1', 'pkg2']
        mock_install.side_effect = [True, False]  # 第一个成功，第二个失败
        
        args = MagicMock()
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cmd_update(args)
        
        result = output.getvalue()
        self.assertIn("Updated: 1", result)
        self.assertIn("Failed: 1", result)


if __name__ == '__main__':
    unittest.main()
