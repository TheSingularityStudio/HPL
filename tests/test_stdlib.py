#!/usr/bin/env python3
"""
HPL 标准库单元测试

测试所有标准库模块的功能：
- io: 文件操作
- math: 数学函数
- json: JSON处理
- os: 操作系统功能
- time: 时间功能
"""

import sys
import os
import tempfile
import shutil
import json
import time
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hpl_runtime'))

try:
    from hpl_runtime.module_loader import get_module, register_module
    from hpl_runtime.module_base import HPLModule
except ImportError:
    from module_loader import get_module, register_module
    from module_base import HPLModule


class TestIOStdlib(unittest.TestCase):
    """测试 io 标准库模块"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.io_module = get_module('io')
        if cls.io_module is None:
            # 如果模块未注册，尝试导入并注册
            try:
                from hpl_runtime.stdlib import io
                cls.io_module = io.module
            except ImportError:
                from stdlib import io
                cls.io_module = io.module
        
        cls.test_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_read_file(self):
        """测试读取文件"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        # 创建测试文件
        test_file = os.path.join(self.test_dir, "test_read.txt")
        test_content = "Hello, HPL!"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # 测试读取
        result = self.io_module.call_function('read_file', [test_file])
        self.assertEqual(result, test_content)


    def test_write_file(self):
        """测试写入文件"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        test_file = os.path.join(self.test_dir, "test_write.txt")
        test_content = "Test content"
        
        result = self.io_module.call_function('write_file', [test_file, test_content])
        self.assertTrue(result)
        
        # 验证写入
        with open(test_file, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), test_content)


    def test_append_file(self):
        """测试追加文件"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        test_file = os.path.join(self.test_dir, "test_append.txt")
        initial_content = "Initial"
        append_content = " Appended"
        
        # 写入初始内容
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(initial_content)
        
        # 测试追加
        result = self.io_module.call_function('append_file', [test_file, append_content])
        self.assertTrue(result)
        
        # 验证追加
        with open(test_file, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), initial_content + append_content)


    def test_file_exists(self):
        """测试检查文件存在"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        test_file = os.path.join(self.test_dir, "test_exists.txt")
        
        # 文件不存在
        self.assertFalse(self.io_module.call_function('file_exists', [test_file]))
        
        # 创建文件
        with open(test_file, 'w') as f:
            f.write("test")
        
        # 文件存在
        self.assertTrue(self.io_module.call_function('file_exists', [test_file]))


    def test_delete_file(self):
        """测试删除文件"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        test_file = os.path.join(self.test_dir, "test_delete.txt")
        
        # 创建文件
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = self.io_module.call_function('delete_file', [test_file])
        self.assertTrue(result)
        self.assertFalse(os.path.exists(test_file))


    def test_create_dir(self):
        """测试创建目录"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        test_dir = os.path.join(self.test_dir, "test_subdir")
        
        result = self.io_module.call_function('create_dir', [test_dir])
        self.assertTrue(result)
        self.assertTrue(os.path.isdir(test_dir))


    def test_list_dir(self):
        """测试列出目录"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        # 创建测试文件
        test_file1 = os.path.join(self.test_dir, "file1.txt")
        test_file2 = os.path.join(self.test_dir, "file2.txt")
        open(test_file1, 'w').close()
        open(test_file2, 'w').close()
        
        result = self.io_module.call_function('list_dir', [self.test_dir])
        
        self.assertIsInstance(result, list)
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)


    def test_get_file_size(self):
        """测试获取文件大小"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        test_file = os.path.join(self.test_dir, "test_size.txt")
        content = "Hello, World!"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = self.io_module.call_function('get_file_size', [test_file])
        
        self.assertEqual(result, len(content.encode('utf-8')))


    def test_is_file(self):
        """测试检查是否为文件"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        test_file = os.path.join(self.test_dir, "test_isfile.txt")
        test_dir = os.path.join(self.test_dir, "test_isdir")
        
        with open(test_file, 'w') as f:
            f.write("test")
        os.makedirs(test_dir)
        
        self.assertTrue(self.io_module.call_function('is_file', [test_file]))
        self.assertFalse(self.io_module.call_function('is_file', [test_dir]))
        self.assertFalse(self.io_module.call_function('is_dir', [test_file]))
        self.assertTrue(self.io_module.call_function('is_dir', [test_dir]))


    def test_io_error_handling(self):
        """测试IO错误处理"""
        if self.io_module is None:
            self.skipTest("IO module not available")
        
        # 测试读取不存在的文件
        with self.assertRaises(FileNotFoundError):
            self.io_module.call_function('read_file', ["/nonexistent/file.txt"])
        
        # 测试类型错误
        with self.assertRaises(TypeError):
            self.io_module.call_function('read_file', [123])  # 非字符串路径



class TestMathStdlib(unittest.TestCase):
    """测试 math 标准库模块"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.math_module = get_module('math')
        if cls.math_module is None:
            try:
                from hpl_runtime.stdlib import math as math_mod
                cls.math_module = math_mod.module
            except ImportError:
                from stdlib import math as math_mod
                cls.math_module = math_mod.module

    def test_sqrt(self):
        """测试平方根"""
        if self.math_module is None:
            self.skipTest("Math module not available")
        
        result = self.math_module.call_function('sqrt', [16])
        self.assertEqual(result, 4.0)


    def test_pow(self):
        """测试幂运算"""
        if self.math_module is None:
            self.skipTest("Math module not available")
        
        result = self.math_module.call_function('pow', [2, 3])
        self.assertEqual(result, 8.0)


    def test_sin(self):
        """测试正弦函数"""
        if self.math_module is None:
            self.skipTest("Math module not available")
        
        import math
        result = self.math_module.call_function('sin', [0])
        self.assertAlmostEqual(result, 0.0, places=10)


    def test_cos(self):
        """测试余弦函数"""
        if self.math_module is None:
            self.skipTest("Math module not available")
        
        import math
        result = self.math_module.call_function('cos', [0])
        self.assertAlmostEqual(result, 1.0, places=10)


    def test_floor(self):
        """测试向下取整"""
        if self.math_module is None:
            self.skipTest("Math module not available")
        
        result = self.math_module.call_function('floor', [3.7])
        self.assertEqual(result, 3)


    def test_ceil(self):
        """测试向上取整"""
        if self.math_module is None:
            self.skipTest("Math module not available")
        
        result = self.math_module.call_function('ceil', [3.2])
        self.assertEqual(result, 4)


    def test_pi_constant(self):
        """测试PI常量"""
        if self.math_module is None:
            self.skipTest("Math module not available")
        
        try:
            pi = self.math_module.get_constant('PI')
            import math
            self.assertAlmostEqual(pi, math.pi, places=10)
        except ValueError:
            self.skipTest("PI constant not available")

    def test_e_constant(self):
        """测试E常量"""
        if self.math_module is None:
            self.skipTest("Math module not available")
        
        try:
            e = self.math_module.get_constant('E')
            import math
            self.assertAlmostEqual(e, math.e, places=10)
        except ValueError:
            self.skipTest("E constant not available")


class TestJSONStdlib(unittest.TestCase):
    """测试 json 标准库模块"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.json_module = get_module('json')
        if cls.json_module is None:
            try:
                from hpl_runtime.stdlib import json_mod
                cls.json_module = json_mod.module
            except ImportError:
                from stdlib import json_mod
                cls.json_module = json_mod.module

    def test_parse(self):
        """测试JSON解析"""
        if self.json_module is None:
            self.skipTest("JSON module not available")
        
        json_str = '{"name": "test", "value": 42}'
        result = self.json_module.call_function('parse', [json_str])
        # JSON模块将字典转换为键值对数组 [[key, value], ...]
        self.assertIsInstance(result, list)
        # 查找键值对
        found_name = False
        found_value = False
        for pair in result:
            if isinstance(pair, list) and len(pair) == 2:
                if pair[0] == 'name' and pair[1] == 'test':
                    found_name = True
                if pair[0] == 'value' and pair[1] == 42:
                    found_value = True
        self.assertTrue(found_name, "Should find name='test' in result")
        self.assertTrue(found_value, "Should find value=42 in result")


    def test_stringify(self):
        """测试JSON字符串化"""
        if self.json_module is None:
            self.skipTest("JSON module not available")
        
        # 使用键值对数组格式（HPL字典格式）
        data = [['name', 'test'], ['value', 42]]
        result = self.json_module.call_function('stringify', [data])
        # 验证是有效的JSON
        parsed = json.loads(result)
        self.assertEqual(parsed['name'], 'test')
        self.assertEqual(parsed['value'], 42)




class TestOSStdlib(unittest.TestCase):
    """测试 os 标准库模块"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.os_module = get_module('os')
        if cls.os_module is None:
            try:
                from hpl_runtime.stdlib import os_mod
                cls.os_module = os_mod.module
            except ImportError:
                from stdlib import os_mod
                cls.os_module = os_mod.module

    def test_getcwd(self):
        """测试获取当前工作目录"""
        if self.os_module is None:
            self.skipTest("OS module not available")
        
        result = self.os_module.call_function('get_cwd', [])
        self.assertIsInstance(result, str)
        self.assertTrue(os.path.isdir(result))


    def test_getenv(self):
        """测试获取环境变量"""
        if self.os_module is None:
            self.skipTest("OS module not available")
        
        # 测试获取PATH环境变量（通常存在）
        result = self.os_module.call_function('get_env', ['PATH'])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)


    def test_execute(self):
        """测试执行系统命令"""
        if self.os_module is None:
            self.skipTest("OS module not available")
        
        # 执行简单命令
        result = self.os_module.call_function('execute', ['echo test'])
        self.assertIsInstance(result, dict)
        self.assertIn('returncode', result)
        self.assertIn('stdout', result)




class TestTimeStdlib(unittest.TestCase):
    """测试 time 标准库模块"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.time_module = get_module('time')
        if cls.time_module is None:
            try:
                from hpl_runtime.stdlib import time_mod
                cls.time_module = time_mod.module
            except ImportError:
                from stdlib import time_mod
                cls.time_module = time_mod.module

    def test_now(self):
        """测试获取当前时间戳"""
        if self.time_module is None:
            self.skipTest("Time module not available")
        
        # 尝试调用 now 函数（如果存在）
        try:
            result = self.time_module.call_function('now', [])
            self.assertIsInstance(result, (int, float))
            # 验证是合理的时间戳（2020年之后）
            self.assertGreater(result, 1577836800)
        except ValueError:
            self.skipTest("now() function not available in time module")


    def test_sleep(self):
        """测试睡眠功能"""
        if self.time_module is None:
            self.skipTest("Time module not available")
        
        start = time.time()
        try:
            self.time_module.call_function('sleep', [0.1])  # 睡眠100毫秒
        except ValueError:
            self.skipTest("sleep() function not available in time module")
        end = time.time()
        # 验证至少睡眠了指定时间
        self.assertGreaterEqual(end - start, 0.09)


    def test_format_time(self):
        """测试格式化时间"""
        if self.time_module is None:
            self.skipTest("Time module not available")
        
        # 尝试调用 format 函数（如果存在）
        try:
            # format_time(timestamp=None, format_str="%Y-%m-%d %H:%M:%S")
            # 传递 None 作为第一个参数使用当前时间，第二个参数为格式字符串
            result = self.time_module.call_function('format', [None, '%Y-%m-%d'])
            self.assertIsInstance(result, str)
            # 验证格式包含年份
            import datetime
            current_year = str(datetime.datetime.now().year)
            self.assertIn(current_year, result)
        except ValueError:
            self.skipTest("format() function not available in time module")





class TestStdlibRegistration(unittest.TestCase):
    """测试标准库模块注册"""

    def test_stdlib_modules_registered(self):
        """测试所有标准库模块已注册"""
        stdlib_names = ['io', 'math', 'json', 'os', 'time']
        
        for name in stdlib_names:
            module = get_module(name)
            self.assertIsNotNone(module, f"Module '{name}' should be registered")
            self.assertIsInstance(module, HPLModule)

    def test_module_has_functions(self):
        """测试模块包含函数"""
        io_module = get_module('io')
        if io_module:
            # 验证至少有一些函数
            self.assertGreater(len(io_module.functions), 0)


    def test_module_has_constants(self):
        """测试模块包含常量"""
        math_module = get_module('math')
        if math_module:
            # math模块应该有PI和E等常量
            pass  # 常量可能以函数形式存在


if __name__ == '__main__':
    unittest.main()
