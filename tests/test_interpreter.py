import unittest
import sys
import os
import tempfile
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.interpreter import main as interpreter_main


class TestHPLInterpreter(unittest.TestCase):

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

    def run_interpreter_with_capture(self, hpl_file):
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Set sys.argv to simulate command line
        original_argv = sys.argv
        sys.argv = ['interpreter.py', hpl_file]

        try:
            interpreter_main()
        except SystemExit:
            pass  # Ignore sys.exit(1) for invalid args
        finally:
            # Restore
            sys.stdout = sys.__stdout__
            sys.argv = original_argv

        return captured_output.getvalue()

    def test_simple_echo(self):
        content = """
main: |
  func(){
    echo "Hello from interpreter";
  }
"""
        file_path = self.create_temp_file('simple.hpl', content)
        output = self.run_interpreter_with_capture(file_path)
        self.assertEqual(output.strip(), "Hello from interpreter")

    def test_class_and_object(self):
        content = """
classes:
  Greeter:
    greet: |
      func(){
        echo "Hello from class";
      }
objects:
  greeter: Greeter()
main: |
  func(){
    greeter.greet();
  }
"""
        file_path = self.create_temp_file('class_test.hpl', content)
        output = self.run_interpreter_with_capture(file_path)
        self.assertEqual(output.strip(), "Hello from class")

    def test_inheritance(self):
        base_content = """
classes:
  Base:
    base_method: |
      func(){
        echo "base";
      }
"""
        base_path = self.create_temp_file('base.hpl', base_content)

        main_content = f"""
includes:
  - base.hpl
classes:
  Derived:
    parent: Base
    derived_method: |
      func(){{
        super.base_method();
        echo "derived";
      }}
objects:
  obj: Derived()
main: |
  func(){{
    obj.derived_method();
  }}
"""
        main_path = self.create_temp_file('inheritance.hpl', main_content)
        output = self.run_interpreter_with_capture(main_path)
        expected = "base\nderived"
        self.assertEqual(output.strip(), expected)

    def test_loop_and_conditionals(self):
        content = """
main: |
  func(){
    for (i = 0; i < 3; i++) {
      if (i % 2 == 0) {
        echo "even";
      } else {
        echo "odd";
      }
    }
  }
"""
        file_path = self.create_temp_file('loop_test.hpl', content)
        output = self.run_interpreter_with_capture(file_path)
        expected = "even\nodd\neven"
        self.assertEqual(output.strip(), expected)

    def test_try_catch(self):
        # Since we don't have exceptions yet, this will just execute the try block
        content = """
main: |
  func(){
    try {
      echo "try block";
    } catch (e) {
      echo "catch block";
    }
  }
"""
        file_path = self.create_temp_file('try_catch_test.hpl', content)
        output = self.run_interpreter_with_capture(file_path)
        self.assertEqual(output.strip(), "try block")

    def test_invalid_file(self):
        # Test with a non-existent file
        output = self.run_interpreter_with_capture('nonexistent.hpl')
        # Should show error message about file not found
        self.assertIn("Error: File 'nonexistent.hpl' not found.", output)


if __name__ == '__main__':
    unittest.main()
