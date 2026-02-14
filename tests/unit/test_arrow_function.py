"""
测试箭头函数功能

验证:
1. 简单箭头函数
2. 带参数的箭头函数
3. 箭头函数作为值传递
4. 闭包功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from hpl_runtime.core.lexer import HPLLexer
from hpl_runtime.core.parser import HPLParser
from hpl_runtime.core.ast_parser import HPLASTParser
from hpl_runtime.core.evaluator import HPLEvaluator, HPLArrowFunction
from hpl_runtime.modules.loader import set_current_hpl_file



def interpret_code(code):
    """解释执行HPL代码并返回main函数的结果"""
    # 创建临时文件
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.hpl', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file = f.name
    
    try:
        set_current_hpl_file(temp_file)
        parser = HPLParser(temp_file)
        classes, objects, functions, main_func, call_target, call_args, imports = parser.parse()
        
        if main_func is None:
            raise ValueError("No main function found")
        
        evaluator = HPLEvaluator(classes, objects, functions, main_func, call_target, call_args)
        
        # 处理导入
        from hpl_runtime.core.models import ImportStatement
        for imp in imports:
            module_name = imp['module']
            alias = imp['alias'] or module_name
            import_stmt = ImportStatement(module_name, alias)
            evaluator.execute_import(import_stmt, evaluator.global_scope)
        
        # 实例化对象
        for obj_name, obj in list(evaluator.objects.items()):
            from hpl_runtime.core.models import HPLObject
            if isinstance(obj, HPLObject) and '__init_args__' in obj.attributes:
                init_args = obj.attributes.pop('__init_args__')
                parsed_args = []
                for arg in init_args:
                    arg = arg.strip()
                    try:
                        parsed_args.append(int(arg))
                    except ValueError:
                        try:
                            parsed_args.append(float(arg))
                        except ValueError:
                            if (arg.startswith('"') and arg.endswith('"')) or \
                               (arg.startswith("'") and arg.endswith("'")):
                                parsed_args.append(arg[1:-1])
                            else:
                                parsed_args.append(arg)
                evaluator._call_constructor(obj, parsed_args)
        
        # 执行main函数并返回结果
        return evaluator.execute_function(main_func, {}, 'main')
    finally:
        os.unlink(temp_file)


class TestArrowFunction:
    """测试箭头函数功能"""
    
    def test_simple_arrow_function(self):
        """测试简单箭头函数: 赋值并调用"""
        code = """
main: () => {
    add = (x, y) => {
        return x + y
    }
    result = add(2, 3)
    return result
}
"""
        result = interpret_code(code)
        assert result == 5, f"Expected 5, got {result}"
        print("✓ 简单箭头函数测试通过")

    
    def test_arrow_function_no_params(self):
        """测试无参数箭头函数"""
        code = """
main: () => {
    greet = () => {
        return "Hello"
    }
    return greet()
}
"""
        result = interpret_code(code)
        assert result == "Hello", f"Expected 'Hello', got {result}"
        print("✓ 无参数箭头函数测试通过")

    
    def test_arrow_function_single_param(self):
        """测试单参数箭头函数"""
        code = """
main: () => {
    double = (x) => {
        return x * 2
    }
    return double(5)
}
"""
        result = interpret_code(code)
        assert result == 10, f"Expected 10, got {result}"
        print("✓ 单参数箭头函数测试通过")

    
    def test_arrow_function_as_value(self):
        """测试箭头函数作为值传递"""
        code = """
apply: (f, x) => {
    return f(x)
}

main: () => {
    triple = (n) => {
        return n * 3
    }
    result = apply(triple, 4)
    return result
}
"""
        result = interpret_code(code)
        assert result == 12, f"Expected 12, got {result}"
        print("✓ 箭头函数作为值传递测试通过")

    
    def test_arrow_function_closure(self):
        """测试箭头函数闭包"""
        code = """
make_adder: (x) => {
    return (y) => {
        return x + y
    }
}

main: () => {
    add5 = make_adder(5)
    result = add5(3)
    return result
}
"""
        result = interpret_code(code)
        assert result == 8, f"Expected 8, got {result}"
        print("✓ 箭头函数闭包测试通过")

    
    def test_arrow_function_closure_multiple(self):
        """测试多个闭包独立工作"""
        code = """
make_multiplier: (factor) => {
    return (n) => {
        return n * factor
    }
}

main: () => {
    double = make_multiplier(2)
    triple = make_multiplier(3)
    
    a = double(5)
    b = triple(5)
    
    return a + b
}
"""
        result = interpret_code(code)
        assert result == 25, f"Expected 25, got {result}"  # 10 + 15
        print("✓ 多个闭包独立工作测试通过")

    
    def test_arrow_function_nested_call(self):
        """测试嵌套箭头函数调用"""
        code = """
main: () => {
    calc = (a, b) => {
        sum_fn = (x, y) => {
            return x + y
        }
        return sum_fn(a, b) * 2
    }
    return calc(3, 4)
}
"""
        result = interpret_code(code)
        assert result == 14, f"Expected 14, got {result}"  # (3+4)*2
        print("✓ 嵌套箭头函数调用测试通过")

    
    def test_arrow_function_return_from_function(self):
        """测试从普通函数返回箭头函数"""
        code = """
get_operation: (op) => {
    if (op == "add") {
        return (a, b) => {
            return a + b
        }
    } else {
        return (a, b) => {
            return a - b
        }
    }
}

main: () => {
    add = get_operation("add")
    sub = get_operation("sub")
    
    return add(10, 5) + sub(10, 5)
}
"""
        result = interpret_code(code)
        assert result == 20, f"Expected 20, got {result}"  # 15 + 5
        print("✓ 从普通函数返回箭头函数测试通过")




def run_tests():
    """运行所有测试"""
    test = TestArrowFunction()
    methods = [m for m in dir(test) if m.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in methods:
        try:
            method = getattr(test, method_name)
            method()
            passed += 1
        except Exception as e:
            print(f"✗ {method_name} 失败: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print(f"{'='*50}")
    
    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
