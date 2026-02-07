import unittest
import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser import HPLParser
from src.models import HPLClass, HPLObject, HPLFunction

class TestHPLParser(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_temp_file(self, filename, content):
        path = os.path.join(self.temp_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def test_parse_simple_class(self):
        content = """
classes:
  SimpleClass:
    method: |
      func(){
        echo "hello";
      }
"""
        file_path = self.create_temp_file('test.hpl', content)
        parser = HPLParser(file_path)
        classes, objects, main_func, call = parser.parse()

        self.assertIn('SimpleClass', classes)
        self.assertIsInstance(classes['SimpleClass'], HPLClass)
        self.assertIn('method', classes['SimpleClass'].methods)
        self.assertIsInstance(classes['SimpleClass'].methods['method'], HPLFunction)

    def test_parse_class_with_parent(self):
        content = """
classes:
  Parent:
    parent_method: |
      func(){
        echo "parent";
      }
  Child:
    parent: Parent
    child_method: |
      func(){
        echo "child";
      }
"""
        file_path = self.create_temp_file('test.hpl', content)
        parser = HPLParser(file_path)
        classes, objects, main_func, call = parser.parse()

        self.assertIn('Child', classes)
        self.assertEqual(classes['Child'].parents, ['Parent'])

    def test_parse_objects(self):
        content = """
classes:
  TestClass:
    test: |
      func(){
        echo "test";
      }
objects:
  test_obj: TestClass()
"""
        file_path = self.create_temp_file('test.hpl', content)
        parser = HPLParser(file_path)
        classes, objects, main_func, call = parser.parse()

        self.assertIn('test_obj', objects)
        self.assertIsInstance(objects['test_obj'], HPLObject)
        self.assertEqual(objects['test_obj'].hpl_class.name, 'TestClass')

    def test_parse_main_function(self):
        content = """
main: |
  func(){
    echo "main";
  }
"""
        file_path = self.create_temp_file('test.hpl', content)
        parser = HPLParser(file_path)
        classes, objects, main_func, call = parser.parse()

        self.assertIsInstance(main_func, HPLFunction)

    def test_parse_includes(self):
        include_content = """
classes:
  IncludedClass:
    included_method: |
      func(){
        echo "included";
      }
"""
        include_path = self.create_temp_file('include.hpl', include_content)

        main_content = f"""
includes:
  - include.hpl
classes:
  MainClass:
    main_method: |
      func(){{
        echo "main";
      }}
"""
        main_path = self.create_temp_file('main.hpl', main_content)
        parser = HPLParser(main_path)
        classes, objects, main_func, call = parser.parse()

        self.assertIn('IncludedClass', classes)
        self.assertIn('MainClass', classes)

    def test_invalid_class_definition(self):
        content = """
classes:
  InvalidClass: "not a dict"
"""
        file_path = self.create_temp_file('test.hpl', content)
        parser = HPLParser(file_path)
        with self.assertRaises(ValueError):
            parser.parse()

    def test_parse_call(self):
        content = """
main: |
  func(){
    echo "main";
  }
call: main();
"""
        file_path = self.create_temp_file('test.hpl', content)
        parser = HPLParser(file_path)
        classes, objects, main_func, call = parser.parse()

        self.assertIsNotNone(call)
        self.assertEqual(call['func_name'], 'main')
        self.assertEqual(call['args'], [])

if __name__ == '__main__':
    unittest.main()
