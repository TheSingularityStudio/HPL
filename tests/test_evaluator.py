import unittest
import sys
import os
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.evaluator import HPLEvaluator
from src.models import HPLClass, HPLObject, HPLFunction, IntegerLiteral, StringLiteral, Variable, BinaryOp, AssignmentStatement, EchoStatement, BlockStatement, IfStatement, ForStatement, TryCatchStatement, FunctionCall, MethodCall, SuperCall, PostfixIncrement, IncrementStatement


class TestHPLEvaluator(unittest.TestCase):

    def setUp(self):
        self.classes = {}
        self.objects = {}

    def create_simple_class(self):
        # Create a simple class for testing
        method_body = BlockStatement([
            EchoStatement(StringLiteral("test"))
        ])
        method = HPLFunction([], method_body)
        hpl_class = HPLClass('TestClass', {'test_method': method})
        self.classes['TestClass'] = hpl_class
        self.objects['test_obj'] = HPLObject('test_obj', hpl_class)

    def test_evaluate_integer_literal(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = IntegerLiteral(42)
        result = evaluator.evaluate_expression(expr, {})
        self.assertEqual(result, 42)

    def test_evaluate_string_literal(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = StringLiteral("hello")
        result = evaluator.evaluate_expression(expr, {})
        self.assertEqual(result, "hello")

    def test_evaluate_variable(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        local_scope = {'x': 10}
        expr = Variable('x')
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 10)

    def test_evaluate_binary_op_addition(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = BinaryOp(IntegerLiteral(5), '+', IntegerLiteral(3))
        result = evaluator.evaluate_expression(expr, {})
        self.assertEqual(result, 8)  # Numeric addition for integers

    def test_evaluate_binary_op_string_concatenation(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        # String + String = concatenation
        expr = BinaryOp(StringLiteral("Hello"), '+', StringLiteral(" World"))
        result = evaluator.evaluate_expression(expr, {})
        self.assertEqual(result, "Hello World")
        # Number + String = concatenation
        expr2 = BinaryOp(IntegerLiteral(5), '+', StringLiteral(" items"))
        result2 = evaluator.evaluate_expression(expr2, {})
        self.assertEqual(result2, "5 items")

    def test_evaluate_binary_op_subtraction(self):

        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = BinaryOp(IntegerLiteral(5), '-', IntegerLiteral(3))
        result = evaluator.evaluate_expression(expr, {})
        self.assertEqual(result, 2)

    def test_evaluate_binary_op_comparison(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = BinaryOp(IntegerLiteral(5), '==', IntegerLiteral(5))
        result = evaluator.evaluate_expression(expr, {})
        self.assertTrue(result)

    def test_execute_assignment_statement(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        stmt = AssignmentStatement('x', IntegerLiteral(42))
        local_scope = {}
        evaluator.execute_statement(stmt, local_scope)
        self.assertEqual(local_scope['x'], 42)

    def test_execute_echo_statement(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            stmt = EchoStatement(StringLiteral("test message"))
            evaluator.execute_statement(stmt, {})
            output = captured_output.getvalue()
            self.assertEqual(output.strip(), "test message")
        finally:
            sys.stdout = sys.__stdout__

    def test_execute_if_statement_true(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            condition = BinaryOp(IntegerLiteral(1), '==', IntegerLiteral(1))
            then_block = BlockStatement([EchoStatement(StringLiteral("true"))])
            stmt = IfStatement(condition, then_block)
            evaluator.execute_statement(stmt, {})
            output = captured_output.getvalue()
            self.assertEqual(output.strip(), "true")
        finally:
            sys.stdout = sys.__stdout__

    def test_execute_if_statement_false(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            condition = BinaryOp(IntegerLiteral(1), '==', IntegerLiteral(2))
            then_block = BlockStatement([EchoStatement(StringLiteral("true"))])
            else_block = BlockStatement([EchoStatement(StringLiteral("false"))])
            stmt = IfStatement(condition, then_block, else_block)
            evaluator.execute_statement(stmt, {})
            output = captured_output.getvalue()
            self.assertEqual(output.strip(), "false")
        finally:
            sys.stdout = sys.__stdout__

    def test_execute_for_statement(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            init = AssignmentStatement('i', IntegerLiteral(0))
            condition = BinaryOp(Variable('i'), '<', IntegerLiteral(3))
            increment = PostfixIncrement(Variable('i'))
            body = BlockStatement([EchoStatement(Variable('i'))])
            stmt = ForStatement(init, condition, increment, body)
            evaluator.execute_statement(stmt, {})
            output = captured_output.getvalue()
            expected = "0\n1\n2"
            self.assertEqual(output.strip(), expected)
        finally:
            sys.stdout = sys.__stdout__

    def test_execute_try_catch_no_exception(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            try_block = BlockStatement([EchoStatement(StringLiteral("try"))])
            catch_block = BlockStatement([EchoStatement(StringLiteral("catch"))])
            stmt = TryCatchStatement(try_block, 'e', catch_block)
            evaluator.execute_statement(stmt, {})
            output = captured_output.getvalue()
            self.assertEqual(output.strip(), "try")
        finally:
            sys.stdout = sys.__stdout__

    def test_evaluate_postfix_increment(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        local_scope = {'x': 5}
        expr = PostfixIncrement(Variable('x'))
        result = evaluator.evaluate_expression(expr, local_scope)
        self.assertEqual(result, 5)
        self.assertEqual(local_scope['x'], 6)

    def test_execute_increment_statement(self):
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        stmt = IncrementStatement('x')
        local_scope = {'x': 5}
        evaluator.execute_statement(stmt, local_scope)
        self.assertEqual(local_scope['x'], 6)

    def test_call_method_on_object(self):
        self.create_simple_class()
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            method_call = MethodCall(Variable('test_obj'), 'test_method', [])
            evaluator.evaluate_expression(method_call, {})
            output = captured_output.getvalue()
            self.assertEqual(output.strip(), "test")
        finally:
            sys.stdout = sys.__stdout__

    def test_return_statement(self):
        # Test that return statements properly return values from functions
        from src.models import ReturnStatement
        
        # Create a function body with a return statement
        return_stmt = ReturnStatement(IntegerLiteral(42))
        body = BlockStatement([return_stmt])
        func = HPLFunction([], body)
        
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        result = evaluator.execute_function(func, {})
        self.assertEqual(result, 42)

    def test_return_statement_with_expression(self):
        # Test return with a more complex expression
        from src.models import ReturnStatement
        
        return_stmt = ReturnStatement(BinaryOp(IntegerLiteral(10), '+', IntegerLiteral(5)))
        body = BlockStatement([return_stmt])
        func = HPLFunction([], body)
        
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        result = evaluator.execute_function(func, {})
        self.assertEqual(result, 15)

    def test_type_error_on_string_subtraction(self):
        # Test that subtracting strings raises HPLTypeError
        from src.evaluator import HPLTypeError
        
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = BinaryOp(StringLiteral("hello"), '-', StringLiteral("world"))
        with self.assertRaises(HPLTypeError):
            evaluator.evaluate_expression(expr, {})

    def test_type_error_on_string_multiplication(self):
        # Test that multiplying strings raises HPLTypeError
        from src.evaluator import HPLTypeError
        
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = BinaryOp(StringLiteral("hello"), '*', IntegerLiteral(3))
        with self.assertRaises(HPLTypeError):
            evaluator.evaluate_expression(expr, {})

    def test_undefined_variable_error(self):
        # Test that accessing undefined variable raises HPLUndefinedError
        from src.evaluator import HPLUndefinedError
        
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = Variable('undefined_var')
        with self.assertRaises(HPLUndefinedError):
            evaluator.evaluate_expression(expr, {})

    def test_division_by_zero_error(self):
        # Test that division by zero raises HPLDivisionByZeroError
        from src.evaluator import HPLDivisionByZeroError
        
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = BinaryOp(IntegerLiteral(10), '/', IntegerLiteral(0))
        with self.assertRaises(HPLDivisionByZeroError):
            evaluator.evaluate_expression(expr, {})

    def test_modulo_by_zero_error(self):
        # Test that modulo by zero raises HPLDivisionByZeroError
        from src.evaluator import HPLDivisionByZeroError
        
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        expr = BinaryOp(IntegerLiteral(10), '%', IntegerLiteral(0))
        with self.assertRaises(HPLDivisionByZeroError):
            evaluator.evaluate_expression(expr, {})

    def test_type_error_on_non_numeric_increment(self):
        # Test that incrementing non-numeric value raises HPLTypeError
        from src.evaluator import HPLTypeError
        
        evaluator = HPLEvaluator(self.classes, self.objects, None)
        local_scope = {'x': "string_value"}
        expr = PostfixIncrement(Variable('x'))
        with self.assertRaises(HPLTypeError):
            evaluator.evaluate_expression(expr, local_scope)

if __name__ == '__main__':
    unittest.main()
