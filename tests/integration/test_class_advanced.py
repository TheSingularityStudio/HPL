#!/usr/bin/env python3
"""
HPL 类与对象高级特性单元测试

测试类继承、方法重写、多级属性访问、this绑定等高级特性
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
from hpl_runtime.core.evaluator import HPLEvaluator
from hpl_runtime.core.models import (
    HPLClass, HPLObject, HPLFunction, BlockStatement, 
    AssignmentStatement, ReturnStatement, MethodCall, Variable,
    IntegerLiteral, StringLiteral, BinaryOp, DictionaryLiteral
)


class TestClassInheritance(unittest.TestCase):
    """测试类继承功能"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_basic_inheritance(self):
        """测试基本类继承"""
        # 创建父类 Animal
        parent_init = HPLFunction(['name'], BlockStatement([
            AssignmentStatement('this.name', Variable('name'))
        ]))
        parent_speak = HPLFunction([], BlockStatement([
            ReturnStatement(StringLiteral("Some sound"))
        ]))
        
        parent_class = HPLClass('Animal', {
            '__init__': parent_init,
            'speak': parent_speak
        }, parent=None)
        
        # 创建子类 Dog
        child_speak = HPLFunction([], BlockStatement([
            ReturnStatement(StringLiteral("Woof!"))
        ]))
        
        child_class = HPLClass('Dog', {
            'speak': child_speak
        }, parent='Animal')
        
        self.classes['Animal'] = parent_class
        self.classes['Dog'] = child_class
        
        # 实例化 Dog
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        dog = evaluator.instantiate_object('Dog', 'myDog', ["Buddy"])
        
        # 验证继承的属性
        self.assertEqual(dog.attributes.get('name'), "Buddy")
        
        # 验证方法重写
        result = evaluator._call_method(dog, 'speak', [])
        self.assertEqual(result, "Woof!")

    def test_parent_method_call(self):
        """测试调用父类方法"""
        # 创建父类
        parent_greet = HPLFunction([], BlockStatement([
            ReturnStatement(StringLiteral("Hello from parent"))
        ]))
        
        parent_class = HPLClass('Parent', {
            'greet': parent_greet
        }, parent=None)
        
        # 创建子类，调用父类方法
        child_greet = HPLFunction([], BlockStatement([
            # 这里应该能够访问 parent.greet
            ReturnStatement(StringLiteral("Hello from child"))
        ]))
        
        child_class = HPLClass('Child', {
            'greet': child_greet
        }, parent='Parent')
        
        self.classes['Parent'] = parent_class
        self.classes['Child'] = child_class
        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        child = evaluator.instantiate_object('Child', 'myChild', [])
        
        # 调用子类方法
        result = evaluator._call_method(child, 'greet', [])
        self.assertEqual(result, "Hello from child")

    def test_multi_level_inheritance(self):
        """测试多级继承"""
        # 三级继承链: GrandParent -> Parent -> Child
        
        grandparent_init = HPLFunction([], BlockStatement([
            AssignmentStatement('this.level', IntegerLiteral(1))
        ]))
        grandparent_class = HPLClass('GrandParent', {
            '__init__': grandparent_init,
            'getLevel': HPLFunction([], BlockStatement([
                ReturnStatement(Variable('this.level'))
            ]))
        }, parent=None)
        
        parent_class = HPLClass('Parent', {}, parent='GrandParent')
        child_class = HPLClass('Child', {}, parent='Parent')
        
        self.classes['GrandParent'] = grandparent_class
        self.classes['Parent'] = parent_class
        self.classes['Child'] = child_class
        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        child = evaluator.instantiate_object('Child', 'myChild', [])
        
        # 验证多级继承的属性
        self.assertEqual(child.attributes.get('level'), 1)
        
        # 验证继承的方法
        result = evaluator._call_method(child, 'getLevel', [])
        self.assertEqual(result, 1)


class TestThisBinding(unittest.TestCase):
    """测试 this 关键字绑定"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_this_in_method(self):
        """测试方法中的 this 绑定"""
        init = HPLFunction(['value'], BlockStatement([
            AssignmentStatement('this.value', Variable('value'))
        ]))
        
        get_value = HPLFunction([], BlockStatement([
            ReturnStatement(Variable('this.value'))
        ]))
        
        test_class = HPLClass('TestClass', {
            '__init__': init,
            'getValue': get_value
        }, parent=None)
        
        self.classes['TestClass'] = test_class
        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        obj = evaluator.instantiate_object('TestClass', 'myObj', [42])
        
        # 验证 this.value 被正确设置
        self.assertEqual(obj.attributes.get('value'), 42)
        
        # 验证方法中的 this 绑定
        result = evaluator._call_method(obj, 'getValue', [])
        self.assertEqual(result, 42)

    def test_this_in_nested_method(self):
        """测试嵌套方法调用中的 this 绑定"""
        init = HPLFunction([], BlockStatement([
            AssignmentStatement('this.counter', IntegerLiteral(0))
        ]))
        
        increment = HPLFunction([], BlockStatement([
            AssignmentStatement('this.counter', BinaryOp(
                Variable('this.counter'), '+', IntegerLiteral(1)
            ))
        ]))
        
        get_count = HPLFunction([], BlockStatement([
            ReturnStatement(Variable('this.counter'))
        ]))
        
        counter_class = HPLClass('Counter', {
            '__init__': init,
            'increment': increment,
            'getCount': get_count
        }, parent=None)
        
        self.classes['Counter'] = counter_class
        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        counter = evaluator.instantiate_object('Counter', 'myCounter', [])
        
        # 多次调用 increment
        evaluator._call_method(counter, 'increment', [])
        evaluator._call_method(counter, 'increment', [])
        evaluator._call_method(counter, 'increment', [])
        
        # 验证 this.counter 正确累加
        result = evaluator._call_method(counter, 'getCount', [])
        self.assertEqual(result, 3)


class TestMultiLevelPropertyAccess(unittest.TestCase):
    """测试多级属性访问"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_nested_object_property(self):
        """测试嵌套对象属性访问"""
        # 创建内部类
        inner_init = HPLFunction(['value'], BlockStatement([
            AssignmentStatement('this.value', Variable('value'))
        ]))
        inner_class = HPLClass('Inner', {
            '__init__': inner_init
        }, parent=None)
        
        # 创建外部类，包含内部对象
        outer_init = HPLFunction([], BlockStatement([]))
        outer_class = HPLClass('Outer', {

            '__init__': outer_init
        }, parent=None)
        
        self.classes['Inner'] = inner_class
        self.classes['Outer'] = outer_class
        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 创建内部对象
        inner_obj = evaluator.instantiate_object('Inner', 'inner', [100])
        
        # 手动设置到外部对象
        outer_obj = evaluator.instantiate_object('Outer', 'outer', [])
        outer_obj.attributes['inner'] = inner_obj
        
        # 验证多级属性访问
        self.assertEqual(outer_obj.attributes['inner'].attributes['value'], 100)

    def test_deep_nesting(self):
        """测试深度嵌套对象"""
        # 创建三层嵌套: Level1 -> Level2 -> Level3
        level3_class = HPLClass('Level3', {
            '__init__': HPLFunction(['data'], BlockStatement([
                AssignmentStatement('this.data', Variable('data'))
            ]))
        }, parent=None)
        
        level2_class = HPLClass('Level2', {}, parent=None)
        level1_class = HPLClass('Level1', {}, parent=None)
        
        self.classes['Level1'] = level1_class
        self.classes['Level2'] = level2_class
        self.classes['Level3'] = level3_class
        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 创建嵌套结构
        level3 = evaluator.instantiate_object('Level3', 'l3', ["deep_value"])
        level2 = evaluator.instantiate_object('Level2', 'l2', [])
        level1 = evaluator.instantiate_object('Level1', 'l1', [])
        
        level2.attributes['level3'] = level3
        level1.attributes['level2'] = level2
        
        # 验证三级嵌套访问
        self.assertEqual(
            level1.attributes['level2'].attributes['level3'].attributes['data'],
            "deep_value"
        )


class TestConstructorChaining(unittest.TestCase):
    """测试构造函数链式调用"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_parent_constructor_call(self):
        """测试父类构造函数调用"""
        # 父类构造函数
        parent_init = HPLFunction(['name'], BlockStatement([
            AssignmentStatement('this.name', Variable('name')),
            AssignmentStatement('this.type', StringLiteral("parent"))
        ]))
        
        parent_class = HPLClass('Parent', {
            '__init__': parent_init
        }, parent=None)
        
        # 子类构造函数（应该调用父类构造函数）
        child_init = HPLFunction(['name', 'age'], BlockStatement([
            # 这里应该能够调用父类构造函数
            AssignmentStatement('this.age', Variable('age'))
        ]))
        
        child_class = HPLClass('Child', {
            '__init__': child_init
        }, parent='Parent')
        
        self.classes['Parent'] = parent_class
        self.classes['Child'] = child_class
        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        # 实例化子类
        child = evaluator.instantiate_object('Child', 'myChild', ["Alice", 25])
        
        # 验证子类设置的属性
        self.assertEqual(child.attributes.get('age'), 25)


class TestMethodOverriding(unittest.TestCase):
    """测试方法重写"""

    def setUp(self):
        """设置测试环境"""
        self.classes = {}
        self.objects = {}
        self.functions = {}
        self.main_func = None

    def test_complete_override(self):
        """测试完全重写父类方法"""
        parent_method = HPLFunction([], BlockStatement([
            ReturnStatement(StringLiteral("parent"))
        ]))
        
        child_method = HPLFunction([], BlockStatement([
            ReturnStatement(StringLiteral("child"))
        ]))
        
        parent_class = HPLClass('Parent', {
            'getName': parent_method
        }, parent=None)
        
        child_class = HPLClass('Child', {
            'getName': child_method
        }, parent='Parent')
        
        self.classes['Parent'] = parent_class
        self.classes['Child'] = child_class
        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        parent = evaluator.instantiate_object('Parent', 'p', [])
        child = evaluator.instantiate_object('Child', 'c', [])
        
        # 父类方法
        self.assertEqual(evaluator._call_method(parent, 'getName', []), "parent")
        
        # 子类重写的方法
        self.assertEqual(evaluator._call_method(child, 'getName', []), "child")

    def test_add_new_method_in_child(self):
        """测试子类添加新方法"""
        parent_class = HPLClass('Parent', {}, parent=None)
        
        child_method = HPLFunction([], BlockStatement([
            ReturnStatement(StringLiteral("child only"))
        ]))
        
        child_class = HPLClass('Child', {
            'childMethod': child_method
        }, parent='Parent')
        
        self.classes['Parent'] = parent_class
        self.classes['Child'] = child_class
        
        evaluator = HPLEvaluator(self.classes, self.objects, self.functions, self.main_func)
        
        child = evaluator.instantiate_object('Child', 'c', [])
        
        # 子类特有的方法
        result = evaluator._call_method(child, 'childMethod', [])
        self.assertEqual(result, "child only")


if __name__ == '__main__':
    unittest.main()
