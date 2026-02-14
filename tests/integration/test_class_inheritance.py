#!/usr/bin/env python3
"""
HPL 类继承深度测试

测试类继承、多态、parent调用等高级特性
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import tempfile
import shutil
from pathlib import Path

from hpl_runtime.core.parser import HPLParser
from hpl_runtime.core.evaluator import HPLEvaluator
from hpl_runtime.core.models import HPLClass, HPLObject, HPLFunction, BlockStatement, ReturnStatement, IntegerLiteral, StringLiteral, Variable, BinaryOp, EchoStatement, AssignmentStatement, MethodCall
from hpl_runtime.modules.loader import _parse_hpl_module, clear_cache, add_module_path


class TestClassInheritance(unittest.TestCase):
    """测试类继承功能"""

    def setUp(self):
        """测试前准备"""
        clear_cache()
        self.temp_dirs = []

    def tearDown(self):
        """清理临时目录"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def create_temp_hpl_file(self, content, filename="test.hpl"):
        """创建临时 HPL 文件"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        file_path = Path(temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path), temp_dir

    def test_basic_inheritance(self):
        """测试基本继承"""
        hpl_content = """classes:
  Animal:
    init: (name) => {
      this.name = name
    }
    speak: () => {
      return "Some sound"
    }

  Dog:
    extends: Animal
    speak: () => {
      return "Woof!"
    }

objects:
  myDog: Dog("Buddy")
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_basic", file_path)
        
        self.assertIsNotNone(module)
        self.assertIn("myDog", module.list_constants())
        
        dog = module.get_constant("myDog")
        self.assertIsInstance(dog, HPLObject)
        self.assertEqual(dog.hpl_class.name, "Dog")
        # 继承的属性
        self.assertEqual(dog.attributes.get("name"), "Buddy")

    def test_parent_constructor_call(self):
        """测试父类构造函数调用"""
        hpl_content = """classes:
  Person:
    init: (name) => {
      this.name = name
    }

  Employee:
    extends: Person
    init: (name, id) => {
      this.parent.init(name)
      this.id = id
    }

objects:
  emp: Employee("Alice", "E001")
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_parent_ctor", file_path)
        
        self.assertIsNotNone(module)
        emp = module.get_constant("emp")
        self.assertIsInstance(emp, HPLObject)
        self.assertEqual(emp.attributes.get("name"), "Alice")
        self.assertEqual(emp.attributes.get("id"), "E001")

    def test_multi_level_inheritance(self):
        """测试多级继承"""
        hpl_content = """classes:
  GrandParent:
    init: () => {
      this.level = 1
    }
    getLevel: () => {
      return this.level
    }

  Parent:
    extends: GrandParent
    init: () => {
      this.parent.init()
      this.level = 2
    }

  Child:
    extends: Parent
    init: () => {
      this.parent.init()
      this.level = 3
    }

objects:
  child: Child()
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_multi", file_path)
        
        self.assertIsNotNone(module)
        child = module.get_constant("child")
        self.assertIsInstance(child, HPLObject)
        self.assertEqual(child.attributes.get("level"), 3)

    def test_method_override(self):
        """测试方法重写"""
        hpl_content = """classes:
  Shape:
    area: () => {
      return 0
    }

  Circle:
    extends: Shape
    init: (radius) => {
      this.radius = radius
    }
    area: () => {
      return 3.14 * this.radius * this.radius
    }

  Rectangle:
    extends: Shape
    init: (width, height) => {
      this.width = width
      this.height = height
    }
    area: () => {
      return this.width * this.height
    }

functions:
  testArea: () => {
    circle = Circle(5)
    rect = Rectangle(4, 5)
    return circle.area() + rect.area()
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_override", file_path)
        
        self.assertIsNotNone(module)
        self.assertIn("testArea", module.list_functions())
        
        result = module.call_function("testArea", [])
        # 3.14 * 25 + 20 = 98.5
        self.assertAlmostEqual(result, 98.5, places=1)

    def test_parent_method_call(self):
        """测试父类方法调用"""
        hpl_content = """classes:
  Base:
    init: (value) => {
      this.value = value
    }
    getValue: () => {
      return this.value
    }
    calculate: (x) => {
      return this.value + x
    }

  Derived:
    extends: Base
    calculate: (x) => {
      baseResult = this.parent.calculate(x)
      return baseResult * 2
    }

functions:
  testParentCall: () => {
    obj = Derived(10)
    return obj.calculate(5)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_parent", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testParentCall", [])
        # (10 + 5) * 2 = 30
        self.assertEqual(result, 30)

    def test_polymorphism(self):
        """测试多态"""
        hpl_content = """classes:
  Animal:
    speak: () => {
      return "Unknown"
    }

  Cat:
    extends: Animal
    speak: () => {
      return "Meow"
    }

  Dog:
    extends: Animal
    speak: () => {
      return "Woof"
    }

functions:
  makeSpeak: (animal) => {
    return animal.speak()
  }

  testPolymorphism: () => {
    cat = Cat()
    dog = Dog()
    return makeSpeak(cat) + " " + makeSpeak(dog)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_poly", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testPolymorphism", [])
        self.assertEqual(result, "Meow Woof")

    def test_inheritance_chain_lookup(self):
        """测试继承链方法查找"""
        hpl_content = """classes:
  A:
    methodA: () => {
      return "A"
    }

  B:
    extends: A
    methodB: () => {
      return "B"
    }

  C:
    extends: B
    methodC: () => {
      return "C"
    }

functions:
  testChain: () => {
    obj = C()
    return obj.methodA() + obj.methodB() + obj.methodC()
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_chain", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testChain", [])
        self.assertEqual(result, "ABC")

    def test_missing_parent_class(self):
        """测试缺失父类错误处理"""
        hpl_content = """classes:
  Child:
    extends: NonExistent
    init: () => {
      this.parent.init()
    }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        # 应该能解析，但实例化时会报错
        module = _parse_hpl_module("test_missing", file_path)
        self.assertIsNotNone(module)

    def test_diamond_inheritance(self):
        """测试菱形继承（简化版）"""
        hpl_content = """classes:
  Top:
    init: () => {
      this.value = "top"
    }
    getValue: () => {
      return this.value
    }

  Left:
    extends: Top
    init: () => {
      this.parent.init()
      this.value = "left"
    }

  Right:
    extends: Top
    init: () => {
      this.parent.init()
      this.value = "right"
    }

  Bottom:
    extends: Left
    init: () => {
      this.parent.init()
    }

functions:
  testDiamond: () => {
    obj = Bottom()
    return obj.getValue()
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_diamond", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testDiamond", [])
        # 根据继承链，应该是 "left"
        self.assertEqual(result, "left")

    def test_property_inheritance(self):
        """测试属性继承"""
        hpl_content = """classes:
  Vehicle:
    init: (brand) => {
      this.brand = brand
      this.wheels = 4
    }

  Motorcycle:
    extends: Vehicle
    init: (brand) => {
      this.parent.init(brand)
      this.wheels = 2
    }

objects:
  car: Vehicle("Toyota")
  bike: Motorcycle("Honda")
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_props", file_path)
        
        car = module.get_constant("car")
        bike = module.get_constant("bike")
        
        self.assertEqual(car.attributes.get("brand"), "Toyota")
        self.assertEqual(car.attributes.get("wheels"), 4)
        self.assertEqual(bike.attributes.get("brand"), "Honda")
        self.assertEqual(bike.attributes.get("wheels"), 2)

    def test_abstract_class_pattern(self):
        """测试抽象类模式"""
        hpl_content = """classes:
  AbstractShape:
    area: () => {
      throw "Abstract method must be implemented"
    }

  Square:
    extends: AbstractShape
    init: (side) => {
      this.side = side
    }
    area: () => {
      return this.side * this.side
    }

functions:
  testAbstract: () => {
    s = Square(4)
    return s.area()
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_abstract", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testAbstract", [])
        self.assertEqual(result, 16)


class TestInheritanceEdgeCases(unittest.TestCase):
    """测试继承边界情况"""

    def setUp(self):
        clear_cache()
        self.temp_dirs = []

    def tearDown(self):
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def create_temp_hpl_file(self, content, filename="test.hpl"):
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        file_path = Path(temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path), temp_dir

    def test_self_referential_class(self):
        """测试自引用类（包含自身类型属性）"""
        hpl_content = """classes:
  Node:
    init: (value) => {
      this.value = value
      this.next = null
    }
    setNext: (node) => {
      this.next = node
    }

functions:
  testLinkedList: () => {
    node1 = Node(1)
    node2 = Node(2)
    node1.setNext(node2)
    return node1.next.value
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_node", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testLinkedList", [])
        self.assertEqual(result, 2)

    def test_deep_inheritance_chain(self):
        """测试深层继承链"""
        levels = 10
        classes = []
        for i in range(levels):
            if i == 0:
                classes.append(f"""  Level{i}:
    getLevel: () => {{
      return {i}
    }}""")
            else:
                classes.append(f"""  Level{i}:
    extends: Level{i-1}
    getLevel: () => {{
      return {i}
    }}""")

        hpl_content = f"""classes:
{chr(10).join(classes)}

functions:
  testDeep: () => {{
    obj = Level{levels-1}()
    return obj.getLevel()
  }}
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_deep", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testDeep", [])
        self.assertEqual(result, levels - 1)

    def test_mixin_pattern(self):
        """测试混入模式"""
        hpl_content = """classes:
  Logger:
    log: (message) => {
      return "LOG: " + message
    }

  Calculator:
    add: (a, b) => {
      return a + b
    }

  AdvancedCalc:
    extends: Calculator
    logAndAdd: (a, b) => {
      result = this.add(a, b)
      return this.log("Result: " + result)
    }

functions:
  testMixin: () => {
    calc = AdvancedCalc()
    return calc.add(2, 3)
  }
"""
        file_path, temp_dir = self.create_temp_hpl_file(hpl_content)
        module = _parse_hpl_module("test_mixin", file_path)
        
        self.assertIsNotNone(module)
        result = module.call_function("testMixin", [])
        self.assertEqual(result, 5)


if __name__ == '__main__':
    unittest.main()
