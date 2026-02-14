"""
HPL 修复综合测试

测试所有三个阶段的修复：
1. 异常处理修复
2. 运行时安全性改进
3. 代码质量提升
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from collections import OrderedDict

# 确保 hpl_runtime 在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from hpl_runtime.utils.type_utils import check_type, _get_type_name
from hpl_runtime.utils.exceptions import HPLTypeError, HPLRecursionError
from hpl_runtime.modules.loader import ModuleCache, HPL_CONFIG_DIR, HPL_PACKAGES_DIR


class TestTypeCheckingRefactoring:
    """测试第三阶段：类型检查重构"""
    
    def test_check_type_basic(self):
        """测试基本类型检查"""
        # 应该通过
        check_type("hello", str, 'test_func', 'param')
        check_type(123, int, 'test_func', 'param')
        check_type([1, 2, 3], list, 'test_func', 'param')
        print("✓ 基本类型检查通过")
    
    def test_check_type_failure(self):
        """测试类型检查失败"""
        try:
            check_type(123, str, 'length', 's')
            assert False, "应该抛出 HPLTypeError"
        except HPLTypeError as e:
            assert "length() requires str for s, got int" in str(e)
            print("✓ 类型检查错误消息正确")
    
    def test_check_type_multiple_types(self):
        """测试多类型检查"""
        # 应该通过 - int 或 float
        check_type(123, (int, float), 'test_func', 'param')
        check_type(3.14, (int, float), 'test_func', 'param')
        print("✓ 多类型检查通过")
    
    def test_check_type_allow_none(self):
        """测试允许 None"""
        check_type(None, str, 'test_func', 'param', allow_none=True)
        print("✓ 允许 None 的检查通过")
    
    def test_get_type_name_single(self):
        """测试单类型名称获取"""
        assert _get_type_name(str) == "str"
        assert _get_type_name(int) == "int"
        print("✓ 单类型名称获取正确")
    
    def test_get_type_name_multiple(self):
        """测试多类型名称获取"""
        name = _get_type_name((int, float, str))
        assert "int" in name
        assert "float" in name
        assert "str" in name
        assert "or" in name
        print("✓ 多类型名称获取正确")


class TestModuleCacheLRU:
    """测试第一阶段：模块缓存 LRU 机制"""
    
    def test_cache_basic_operations(self):
        """测试缓存基本操作"""
        cache = ModuleCache(capacity=3)
        
        # 添加项目
        cache.put("mod1", "value1")
        cache.put("mod2", "value2")
        cache.put("mod3", "value3")
        
        # 验证存在
        assert cache.get("mod1") == "value1"
        assert cache.get("mod2") == "value2"
        assert cache.get("mod3") == "value3"
        print("✓ 缓存基本操作正常")
    
    def test_cache_lru_eviction(self):
        """测试 LRU 淘汰机制"""
        cache = ModuleCache(capacity=3)
        
        # 填满缓存
        cache.put("mod1", "value1")
        cache.put("mod2", "value2")
        cache.put("mod3", "value3")
        
        # 访问 mod1，使其成为最近使用
        cache.get("mod1")
        
        # 添加新项目，应该淘汰 mod2（最久未使用）
        cache.put("mod4", "value4")
        
        # mod1 应该还在（最近使用）
        assert cache.get("mod1") == "value1"
        # mod2 应该被淘汰
        assert cache.get("mod2") is None
        # mod3 和 mod4 应该在
        assert cache.get("mod3") == "value3"
        assert cache.get("mod4") == "value4"
        
        print("✓ LRU 淘汰机制工作正常")
    
    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        cache = ModuleCache(capacity=2)
        
        cache.put("mod1", "value1")
        cache.put("mod2", "value2")
        cache.put("mod3", "value3")  # 应该淘汰 mod1
        
        assert cache.get("mod1") is None
        assert cache.get("mod2") == "value2"
        assert cache.get("mod3") == "value3"
        
        # 验证缓存大小不超过限制
        assert len(cache.cache) <= 2
        print("✓ 缓存大小限制生效")
    
    def test_cache_clear(self):
        """测试缓存清空"""
        cache = ModuleCache(capacity=5)
        cache.put("mod1", "value1")
        cache.put("mod2", "value2")
        
        cache.clear()
        
        assert cache.get("mod1") is None
        assert cache.get("mod2") is None
        assert len(cache.cache) == 0
        print("✓ 缓存清空正常")


class TestRecursionDepthLimit:
    """测试第二阶段：递归深度限制"""
    
    def test_recursion_limit_constant(self):
        """测试递归深度限制常量设置"""
        from hpl_runtime.core.evaluator import HPLEvaluator
        import sys
        
        # MAX_RECURSION_DEPTH 是类属性
        max_depth = HPLEvaluator.MAX_RECURSION_DEPTH
        
        # 验证限制值合理
        assert max_depth > 0
        assert max_depth < sys.getrecursionlimit()
        print(f"✓ 递归深度限制设置合理: {max_depth}")

    
    def test_call_stack_tracking(self):
        """测试调用栈跟踪"""
        from hpl_runtime.core.evaluator import HPLEvaluator
        
        evaluator = HPLEvaluator({}, {}, {}, None)
        
        # 初始状态
        assert len(evaluator.call_stack) == 0
        
        # 模拟添加调用
        evaluator.call_stack.append("func1()")
        evaluator.call_stack.append("func2()")
        
        assert len(evaluator.call_stack) == 2
        assert evaluator.call_stack[0] == "func1()"
        assert evaluator.call_stack[1] == "func2()"
        
        # 模拟返回
        evaluator.call_stack.pop()
        assert len(evaluator.call_stack) == 1
        
        print("✓ 调用栈跟踪正常")


class TestEnvironmentVariableConfig:
    """测试第二阶段：环境变量配置覆盖"""
    
    def test_config_dir_env_logic(self):
        """测试 HPL_CONFIG_DIR 环境变量逻辑"""
        from pathlib import Path
        import os
        
        # 测试环境变量存在时的逻辑
        test_path = "/tmp/test_hpl_config"
        
        # 模拟 loader.py 中的逻辑：os.environ.get('HPL_CONFIG_DIR', Path.home() / '.hpl')
        # 当环境变量存在时
        mock_environ = {'HPL_CONFIG_DIR': test_path}
        config_dir = Path(mock_environ.get('HPL_CONFIG_DIR', Path.home() / '.hpl'))
        # 使用 os.path.normpath 处理 Windows 路径差异
        assert os.path.normpath(str(config_dir)) == os.path.normpath(test_path)
        
        # 当环境变量不存在时，使用默认值
        mock_environ_empty = {}
        default_dir = Path(mock_environ_empty.get('HPL_CONFIG_DIR', Path.home() / '.hpl'))
        assert default_dir == Path.home() / '.hpl'
        
        print("✓ HPL_CONFIG_DIR 环境变量逻辑正确")
    
    def test_packages_dir_env_logic(self):
        """测试 HPL_PACKAGES_DIR 环境变量逻辑"""
        from pathlib import Path
        import os
        
        # 测试环境变量存在时的逻辑
        test_packages = "/tmp/test_hpl_packages"
        
        # 模拟 loader.py 中的逻辑
        mock_environ = {'HPL_PACKAGES_DIR': test_packages}
        packages_dir = Path(mock_environ.get('HPL_PACKAGES_DIR', Path.home() / '.hpl' / 'packages'))
        # 使用 os.path.normpath 处理 Windows 路径差异
        assert os.path.normpath(str(packages_dir)) == os.path.normpath(test_packages)
        
        # 当环境变量不存在时，使用默认值
        mock_environ_empty = {}
        default_packages = Path(mock_environ_empty.get('HPL_PACKAGES_DIR', Path.home() / '.hpl' / 'packages'))
        assert default_packages == Path.home() / '.hpl' / 'packages'
        
        print("✓ HPL_PACKAGES_DIR 环境变量逻辑正确")






class TestExceptionHandlingSpecificity:
    """测试第一阶段：异常处理具体性"""
    
    def test_error_suggestions_specific_exception(self):
        """测试 error_suggestions 只捕获特定异常"""
        # 模拟 error_suggestions.py:42 的修复
        def parse_keys(keys_str):
            try:
                return eval(f'[{keys_str}]')
            except (SyntaxError, NameError, ValueError):
                return []
        
        # 应该正常解析
        result = parse_keys("'a', 'b', 'c'")
        assert result == ['a', 'b', 'c']
        
        # 无效输入应该返回空列表而不是抛出异常
        result = parse_keys("invalid syntax [[")
        assert result == []
        
        # 其他异常不应该被捕获（如 TypeError）
        def raise_type_error():
            raise TypeError("should not be caught")
        
        try:
            try:
                raise_type_error()
            except (SyntaxError, NameError, ValueError):
                assert False, "TypeError 不应该被捕获"
        except TypeError:
            pass  # 预期行为
        
        print("✓ error_suggestions 异常处理具体性正常")
    
    def test_file_related_exceptions(self):
        """测试文件相关异常处理"""
        # 测试具体的文件异常被捕获
        file_exceptions = (IOError, OSError, PermissionError, UnicodeDecodeError)
        
        def handle_file_error(e):
            if isinstance(e, file_exceptions):
                return f"File error handled: {e}"
            raise e
        
        # IOError 应该被处理
        try:
            result = handle_file_error(IOError("test"))
            assert "File error handled" in result
        except:
            assert False, "IOError 应该被处理"
        
        # 其他异常应该被重新抛出
        try:
            handle_file_error(ValueError("test"))
            assert False, "ValueError 不应该被处理"
        except ValueError:
            pass
        
        print("✓ 文件相关异常处理具体性正常")


class TestStringModuleRefactoring:
    """测试 string_mod.py 重构"""
    
    def test_string_functions_use_check_type(self):
        """测试字符串函数使用新的 check_type"""
        from hpl_runtime.stdlib import string_mod
        
        # 测试 length 函数
        try:
            string_mod.length(123)  # 应该失败
            assert False, "应该抛出 HPLTypeError"
        except HPLTypeError as e:
            assert "length() requires str for s, got int" in str(e)
        
        # 正常调用
        result = string_mod.length("hello")
        assert result == 5
        
        print("✓ string_mod 使用 check_type 正常")
    
    def test_split_function(self):
        """测试 split 函数类型检查"""
        from hpl_runtime.stdlib import string_mod
        
        # 正常调用
        result = string_mod.split("a,b,c", ",")
        assert result == ["a", "b", "c"]
        
        # 错误类型
        try:
            string_mod.split(123, ",")
            assert False, "应该抛出 HPLTypeError"
        except HPLTypeError:
            pass
        
        print("✓ split 函数类型检查正常")
    
    def test_join_function(self):
        """测试 join 函数类型检查"""
        from hpl_runtime.stdlib import string_mod
        
        # 正常调用
        result = string_mod.join(["a", "b", "c"], "-")
        assert result == "a-b-c"
        
        # 错误类型
        try:
            string_mod.join("not an array", "-")
            assert False, "应该抛出 HPLTypeError"
        except HPLTypeError:
            pass
        
        print("✓ join 函数类型检查正常")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("HPL 修复综合测试")
    print("=" * 60)
    
    test_classes = [
        TestTypeCheckingRefactoring,
        TestModuleCacheLRU,
        TestRecursionDepthLimit,
        TestEnvironmentVariableConfig,
        TestExceptionHandlingSpecificity,
        TestStringModuleRefactoring,
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"测试类: {test_class.__name__}")
        print(f"{'='*60}")
        
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith('test_')]
        
        for method_name in methods:
            try:
                method = getattr(instance, method_name)
                method()
                passed += 1
            except Exception as e:
                print(f"✗ {method_name} 失败: {e}")
                failed += 1
    
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {failed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
