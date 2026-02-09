"""
测试 HPL 模块加载器的 _parse_hpl_module 函数

测试内容包括：
1. 类构造函数调用（带 __init__）
2. 顶层函数注册和调用
3. 对象实例化（带 __init_args__）
4. 模块导入处理
5. 错误处理（参数数量验证等）
"""

import sys
import os
import tempfile
import pytest
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from hpl_runtime.module_loader import _parse_hpl_module, load_module, clear_cache
    from hpl_runtime.models import HPLObject, HPLClass, HPLFunction
except ImportError:
    from module_loader import _parse_hpl_module, load_module, clear_cache
    from models import HPLObject, HPLClass, HPLFunction


class TestParseHPLModule:
    """测试 _parse_hpl_module 函数的各个功能"""
    
    def setup_method(self):
        """每个测试方法前清除缓存"""
        clear_cache()
    
    def create_temp_hpl_file(self, content, filename="test_module.hpl"):
        """创建临时 HPL 文件"""
        temp_dir = tempfile.mkdtemp()
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
        
        try:
            module = _parse_hpl_module("test_person", file_path)
            assert module is not None, "模块解析失败"
            
            # 检查类是否注册为函数
            assert "Person" in module.list_functions(), "Person 类未注册为函数"
            
            # 获取构造函数信息
            func_info = module.functions["Person"]
            assert func_info["param_count"] == 2, f"构造函数参数数量应为 2，实际为 {func_info['param_count']}"
            
            # 调用构造函数创建对象
            obj = module.call_function("Person", ["Alice", 25])
            assert isinstance(obj, HPLObject), "返回值应为 HPLObject 实例"
            assert obj.hpl_class.name == "Person", "对象类名应为 Person"
            
            # 检查属性是否正确设置
            assert obj.attributes.get("name") == "Alice", f"name 属性应为 'Alice'，实际为 {obj.attributes.get('name')}"
            assert obj.attributes.get("age") == 25, f"age 属性应为 25，实际为 {obj.attributes.get('age')}"
            
            print("✅ 类构造函数测试通过")
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
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
        
        try:
            module = _parse_hpl_module("test_point", file_path)
            assert module is not None
            
            # 尝试用错误数量的参数调用
            try:
                module.call_function("Point", [1])  # 只传1个参数，需要2个
                assert False, "应该抛出 ValueError"
            except ValueError as e:
                assert "expects 2 arguments, got 1" in str(e), f"错误信息不正确: {e}"
            
            print("✅ 构造函数参数错误测试通过")
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
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
        
        try:
            module = _parse_hpl_module("test_funcs", file_path)
            assert module is not None
            
            # 检查函数是否注册
            assert "add" in module.list_functions(), "add 函数未注册"
            assert "multiply" in module.list_functions(), "multiply 函数未注册"
            assert "main" in module.list_functions(), "main 函数未注册"
            
            # 调用 add 函数
            result = module.call_function("add", [3, 5])
            assert result == 8, f"add(3, 5) 应返回 8，实际返回 {result}"
            
            # 调用 multiply 函数
            result = module.call_function("multiply", [4, 7])
            assert result == 28, f"multiply(4, 7) 应返回 28，实际返回 {result}"
            
            # 测试参数数量错误
            try:
                module.call_function("add", [1])
                assert False, "应该抛出 ValueError"
            except ValueError as e:
                assert "expects 2 arguments, got 1" in str(e)
            
            print("✅ 顶层函数测试通过")
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
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
        
        try:
            module = _parse_hpl_module("test_objects", file_path)
            assert module is not None
            
            # 检查对象是否注册为常量
            assert "myRect" in module.list_constants(), "myRect 对象未注册为常量"
            
            # 获取对象
            obj = module.get_constant("myRect")
            assert isinstance(obj, HPLObject), "myRect 应为 HPLObject 实例"
            
            # 检查构造函数是否被执行
            assert obj.attributes.get("width") == 10, f"width 应为 10，实际为 {obj.attributes.get('width')}"
            assert obj.attributes.get("height") == 20, f"height 应为 20，实际为 {obj.attributes.get('height')}"
            
            print("✅ 对象实例化测试通过")
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_module_imports(self):
        """测试模块导入处理"""
        # 先创建一个被导入的模块
        math_content = """add: (a, b) => {
  return a + b
}
"""
        temp_dir = tempfile.mkdtemp()
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
        
        try:
            # 添加临时目录到模块搜索路径
            from hpl_runtime.module_loader import add_module_path
            add_module_path(temp_dir)
            
            # 解析主模块
            module = _parse_hpl_module("main_module", str(main_file))
            assert module is not None
            
            # 检查导入的模块是否注册为常量
            assert "math_utils" in module.list_constants(), "math_utils 未注册为常量"
            
            # 获取导入的模块
            imported = module.get_constant("math_utils")
            assert imported is not None, "导入的模块不应为 None"
            
            print("✅ 模块导入测试通过")
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_module_import_with_alias(self):
        """测试带别名的模块导入 - 使用正确的 YAML 字典格式"""
        # 创建被导入的模块
        utils_content = """greet: (name) => {
  return "Hello, " + name
}
"""
        temp_dir = tempfile.mkdtemp()
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
        
        try:
            from hpl_runtime.module_loader import add_module_path
            add_module_path(temp_dir)
            
            module = _parse_hpl_module("alias_module", str(main_file))
            assert module is not None
            
            # 检查别名是否注册
            assert "u" in module.list_constants(), "别名 'u' 未注册"
            assert "utils" not in module.list_constants(), "原始名称不应注册（使用了别名）"
            
            print("✅ 别名导入测试通过")
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_class_without_init(self):
        """测试没有 __init__ 的类"""
        hpl_content = """classes:
  SimpleClass:
    sayHello: () => {
      echo "Hello"
    }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        
        try:
            module = _parse_hpl_module("test_simple", file_path)
            assert module is not None
            
            # 检查构造函数参数数量为 0
            func_info = module.functions["SimpleClass"]
            assert func_info["param_count"] == 0, "无 __init__ 的类参数数量应为 0"
            
            # 调用构造函数（不传参数）
            obj = module.call_function("SimpleClass", [])
            assert isinstance(obj, HPLObject), "应返回 HPLObject 实例"
            
            print("✅ 无 __init__ 类测试通过")
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效文件
        result = _parse_hpl_module("nonexistent", "/path/to/nonexistent.hpl")
        assert result is None, "无效文件应返回 None"
        
        # 测试语法错误
        bad_content = """classes:
  BadClass:
    __init__: (x) => {
      this.x = x
"""
        file_path, temp_dir = self.create_temp_hpl_file(bad_content)
        try:
            result = _parse_hpl_module("bad_module", file_path)
            # 应该返回 None 但不抛出异常
            assert result is None, "语法错误应返回 None"
            print("✅ 错误处理测试通过")
        finally:
            import shutil
            shutil.rmtree(temp_dir)


def run_tests():
    """运行所有测试"""
    test_class = TestParseHPLModule()
    
    print("\n" + "="*60)
    print("开始测试 _parse_hpl_module 函数")
    print("="*60 + "\n")
    
    try:
        test_class.test_class_constructor_with_init()
    except Exception as e:
        print(f"❌ 类构造函数测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_class.test_class_constructor_wrong_args()
    except Exception as e:
        print(f"❌ 构造函数参数错误测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_class.test_top_level_functions()
    except Exception as e:
        print(f"❌ 顶层函数测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_class.test_object_with_init_args()
    except Exception as e:
        print(f"❌ 对象实例化测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_class.test_module_imports()
    except Exception as e:
        print(f"❌ 模块导入测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_class.test_module_import_with_alias()
    except Exception as e:
        print(f"❌ 别名导入测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_class.test_class_without_init()
    except Exception as e:
        print(f"❌ 无 __init__ 类测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_class.test_error_handling()
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_tests()
