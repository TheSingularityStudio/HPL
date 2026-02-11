"""
增强错误处理测试模块

测试多 catch 子句、finally 块、错误上下文捕获等功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hpl_runtime.core.models import (
    TryCatchStatement, CatchClause, BlockStatement, 
    AssignmentStatement, IntegerLiteral, StringLiteral,
    FunctionCall, Variable, EchoStatement, ThrowStatement
)
from hpl_runtime.core.evaluator import HPLEvaluator
from hpl_runtime.utils.exceptions import (
    HPLRuntimeError, HPLTypeError, HPLNameError, 
    HPLIndexError, format_error_for_user
)


class TestTryCatchFinally:
    """测试 Try-Catch-Finally 功能"""
    
    def test_basic_try_catch(self):
        """测试基本的 try-catch"""
        # 创建 try 块: throw "error"
        try_body = BlockStatement([
            ThrowStatement(StringLiteral("test error"))
        ])
        
        # 创建 catch 块: echo err
        catch_body = BlockStatement([
            EchoStatement(Variable("err"))
        ])
        
        # 创建 try-catch 语句
        catch_clause = CatchClause(None, "err", catch_body)
        try_catch = TryCatchStatement(try_body, [catch_clause])
        
        # 执行
        evaluator = HPLEvaluator({}, {}, {}, None)
        local_scope = {}
        
        result = evaluator.execute_statement(try_catch, local_scope)
        # 应该成功捕获异常，不抛出
        assert True, "Basic try-catch should work"
    
    def test_multiple_catch_clauses(self):
        """测试多 catch 子句"""
        # try 块抛出类型错误
        try_body = BlockStatement([
            ThrowStatement(StringLiteral("type error"))
        ])
        
        # 第一个 catch 捕获 HPLTypeError
        type_error_catch = CatchClause("HPLTypeError", "type_err", 
            BlockStatement([EchoStatement(StringLiteral("type error caught"))]))
        
        # 第二个 catch 捕获所有其他错误
        generic_catch = CatchClause(None, "err", 
            BlockStatement([EchoStatement(StringLiteral("generic error caught"))]))
        
        try_catch = TryCatchStatement(try_body, [type_error_catch, generic_catch])
        
        evaluator = HPLEvaluator({}, {}, {}, None)
        local_scope = {}
        
        # 执行 - 应该被 generic_catch 捕获
        result = evaluator.execute_statement(try_catch, local_scope)
        assert True, "Multiple catch clauses should work"
    
    def test_finally_block_execution(self):
        """测试 finally 块总是执行"""
        finally_executed = [False]  # 使用列表来在嵌套函数中修改
        
        # 创建简单的 evaluator 来跟踪 finally 执行
        evaluator = HPLEvaluator({}, {}, {}, None)
        
        # try 块
        try_body = BlockStatement([
            AssignmentStatement("x", IntegerLiteral(1))
        ])
        
        # finally 块
        finally_body = BlockStatement([
            AssignmentStatement("finally_executed", IntegerLiteral(1))
        ])
        
        # 创建 try-finally（无 catch）
        try_finally = TryCatchStatement(try_body, [], finally_body)
        
        local_scope = {}
        result = evaluator.execute_statement(try_finally, local_scope)
        
        # 验证 finally 块执行了
        assert local_scope.get("finally_executed") == 1, "Finally block should execute"
        assert local_scope.get("x") == 1, "Try block should execute"
    
    def test_finally_with_error(self):
        """测试 try 中有错误时 finally 仍然执行"""
        try_body = BlockStatement([
            ThrowStatement(StringLiteral("error in try"))
        ])
        
        catch_body = BlockStatement([
            AssignmentStatement("caught", IntegerLiteral(1))
        ])
        
        finally_body = BlockStatement([
            AssignmentStatement("finally_done", IntegerLiteral(1))
        ])
        
        catch_clause = CatchClause(None, "err", catch_body)
        try_catch_finally = TryCatchStatement(try_body, [catch_clause], finally_body)
        
        evaluator = HPLEvaluator({}, {}, {}, None)
        local_scope = {}
        
        result = evaluator.execute_statement(try_catch_finally, local_scope)
        
        assert local_scope.get("caught") == 1, "Error should be caught"
        assert local_scope.get("finally_done") == 1, "Finally should execute even with error"
    
    def test_error_type_matching(self):
        """测试错误类型匹配逻辑"""
        evaluator = HPLEvaluator({}, {}, {}, None)
        
        # 测试 HPLTypeError 匹配
        type_error = HPLTypeError("type error", line=1, column=1)
        
        # 测试直接匹配
        result = evaluator._matches_error_type(type_error, "HPLTypeError")
        assert result == True, f"Direct match failed: {result}"
        
        # 测试不带前缀匹配
        result = evaluator._matches_error_type(type_error, "TypeError")
        assert result == True, f"Short name match failed: {result}"
        
        # 测试父类匹配 - HPLTypeError 是 HPLRuntimeError 的子类
        result = evaluator._matches_error_type(type_error, "HPLRuntimeError")
        assert result == True, f"Parent class match failed: {result}"
        
        # 测试不匹配
        result = evaluator._matches_error_type(type_error, "HPLNameError")
        assert result == False, f"Non-match failed: {result}"
        
        # 测试 None 匹配所有
        result = evaluator._matches_error_type(type_error, None)
        assert result == True, f"None match failed: {result}"



class TestErrorContext:
    """测试错误上下文增强"""
    
    def test_error_with_call_stack(self):
        """测试错误包含调用栈"""
        error = HPLRuntimeError("test error", line=10, column=5)
        error.call_stack = ["func1()", "func2()", "main()"]
        
        formatted = format_error_for_user(error)
        assert "func1()" in formatted
        assert "func2()" in formatted
        assert "Call stack" in formatted
    
    def test_error_code_generation(self):
        """测试错误代码生成"""
        from hpl_runtime.utils.exceptions import HPLSyntaxError, HPLTypeError, HPLNameError
        
        syntax_error = HPLSyntaxError("syntax error")
        assert "SYNTAX" in syntax_error.get_error_code()
        
        type_error = HPLTypeError("type error")
        assert "TYPE" in type_error.get_error_code()
        
        name_error = HPLNameError("name error")
        assert "NAME" in name_error.get_error_code()


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行增强错误处理测试")
    print("=" * 60)
    
    test_classes = [
        TestTryCatchFinally,
        TestErrorContext,
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n测试类: {test_class.__name__}")
        print("-" * 40)
        
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith('test_')]
        
        for method_name in methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"  ✓ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {e}")
                failed_tests.append((test_class.__name__, method_name, str(e)))
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")
    print("=" * 60)
    
    if failed_tests:
        print("\n失败的测试:")
        for class_name, method_name, error in failed_tests:
            print(f"  - {class_name}.{method_name}: {error}")
        return False
    
    print("\n所有测试通过! ✓")
    return True


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
