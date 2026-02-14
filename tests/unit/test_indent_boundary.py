#!/usr/bin/env python3
"""
HPL 缩进边界处理测试

专门测试缩进边界相关的各种复杂场景，验证修复效果。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import unittest
from hpl_runtime.core.lexer import HPLLexer
from hpl_runtime.core.ast_parser import HPLASTParser
from hpl_runtime.core.models import (
    IntegerLiteral, BooleanLiteral, Variable, BinaryOp,
    AssignmentStatement, IfStatement, ForInStatement, WhileStatement,
    TryCatchStatement, BlockStatement, EchoStatement
)
from hpl_runtime.utils.exceptions import HPLSyntaxError


class TestIndentBoundaryBasic(unittest.TestCase):
    """基本缩进边界测试"""

    def test_simple_indent_dedent(self):
        """测试简单的缩进和反缩进"""
        code = """if (true) :
  x = 1
  y = 2
z = 3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        self.assertIsNotNone(result.then_block)
        # then_block 应该包含2个语句
        self.assertEqual(len(result.then_block.statements), 2)
        # 解析后应该还有 z = 3 语句
        self.assertIsNotNone(parser.current_token)
        self.assertEqual(parser.current_token.type, 'IDENTIFIER')
        self.assertEqual(parser.current_token.value, 'z')

    def test_multiple_dedent_levels(self):
        """测试多层缩进减少"""
        code = """if (true) :
  if (false) :
    x = 1
  y = 2
z = 3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        # 外层 if 的 then_block 应该包含内层 if 和 y = 2
        self.assertEqual(len(result.then_block.statements), 2)
        
        # 内层 if
        inner_if = result.then_block.statements[0]
        self.assertIsInstance(inner_if, IfStatement)
        self.assertEqual(len(inner_if.then_block.statements), 1)

    def test_empty_lines_with_indentation(self):
        """测试带缩进的空行"""
        code = """if (true) :
  x = 1
  
  y = 2
z = 3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        # 空行不应该影响块解析
        self.assertEqual(len(result.then_block.statements), 2)

    def test_mixed_indentation_spaces(self):
        """测试不同数量的空格缩进"""
        code = """if (true) :
    x = 1
    y = 2
z = 3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        self.assertEqual(len(result.then_block.statements), 2)


class TestIndentBoundaryNested(unittest.TestCase):
    """嵌套结构缩进边界测试"""

    def test_nested_if_else(self):
        """测试嵌套的 if-else"""
        code = """if (a) :
  if (b) :
    x = 1
  else :
    x = 2
else :
  x = 3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        self.assertIsNotNone(result.then_block)
        self.assertIsNotNone(result.else_block)
        
        # 外层 then_block 应该包含内层 if-else
        self.assertEqual(len(result.then_block.statements), 1)
        inner_if = result.then_block.statements[0]
        self.assertIsInstance(inner_if, IfStatement)
        self.assertIsNotNone(inner_if.else_block)

    def test_deeply_nested_for_loops(self):
        """测试深度嵌套的 for 循环"""
        code = """for (i in range(3)) :
  for (j in range(3)) :
    for (k in range(3)) :
      sum = i + j + k"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, ForInStatement)
        # 第一层 for
        self.assertEqual(len(result.body.statements), 1)
        # 第二层 for
        inner_for = result.body.statements[0]
        self.assertIsInstance(inner_for, ForInStatement)
        self.assertEqual(len(inner_for.body.statements), 1)
        # 第三层 for
        inner_inner_for = inner_for.body.statements[0]
        self.assertIsInstance(inner_inner_for, ForInStatement)
        self.assertEqual(len(inner_inner_for.body.statements), 1)

    def test_nested_try_catch(self):
        """测试嵌套的 try-catch"""
        code = """try :
  try :
    risky1()
  catch (e1) :
    handle1()
catch (e2) :
  handle2()"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, TryCatchStatement)
        # 外层 try 块应该包含内层 try-catch
        self.assertEqual(len(result.try_block.statements), 1)
        inner_try = result.try_block.statements[0]
        self.assertIsInstance(inner_try, TryCatchStatement)

    def test_mixed_nested_structures(self):
        """测试混合嵌套结构"""
        code = """if (true) :
  for (i in range(5)) :
    if (i > 2) :
      echo i
  x = 10"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        # then_block 应该包含 for 循环和 x = 10
        self.assertEqual(len(result.then_block.statements), 2)
        
        for_stmt = result.then_block.statements[0]
        self.assertIsInstance(for_stmt, ForInStatement)
        # for 循环体应该包含内层 if
        self.assertEqual(len(for_stmt.body.statements), 1)


class TestIndentBoundaryEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_single_statement_block(self):
        """测试单行语句块"""
        code = """if (true) : x = 1
y = 2"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        self.assertEqual(len(result.then_block.statements), 1)

    def test_block_with_trailing_empty_lines(self):
        """测试块末尾有空行"""
        code = """if (true) :
  x = 1
  
y = 2"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        self.assertEqual(len(result.then_block.statements), 1)

    def test_consecutive_blocks_same_level(self):
        """测试同级别的连续块"""
        code = """if (a) :
  x = 1
if (b) :
  y = 2
z = 3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        
        # 解析第一个 if
        result1 = parser.parse_statement()
        self.assertIsInstance(result1, IfStatement)
        self.assertEqual(len(result1.then_block.statements), 1)
        
        # 解析第二个 if
        result2 = parser.parse_statement()
        self.assertIsInstance(result2, IfStatement)
        self.assertEqual(len(result2.then_block.statements), 1)

    def test_dedent_to_different_levels(self):
        """测试缩进减少到不同级别"""
        code = """if (a) :
  if (b) :
    if (c) :
      x = 1
    y = 2
  z = 3
w = 4"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        # 最外层 if 的 then_block 应该包含内层 if 和 z = 3
        self.assertEqual(len(result.then_block.statements), 2)

    def test_comment_between_dedent(self):
        """测试反缩进之间有注释"""
        code = """if (true) :
  x = 1
  # 这是注释
y = 2"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        self.assertEqual(len(result.then_block.statements), 1)


class TestIndentBoundaryWithBraces(unittest.TestCase):
    """花括号与缩进混合测试"""

    def test_brace_block_with_indent(self):
        """测试花括号块内的缩进"""
        code = """if (true) : {
  x = 1
  y = 2
}
z = 3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        self.assertEqual(len(result.then_block.statements), 2)

    def test_mixed_brace_and_indent(self):
        """测试混合使用花括号和缩进"""
        code = """if (a) :
  if (b) : {
    x = 1
  }
  y = 2
z = 3"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        self.assertEqual(len(result.then_block.statements), 2)


class TestIndentBoundaryFileEnd(unittest.TestCase):
    """文件结束时的缩进处理测试"""

    def test_file_ends_with_indented_block(self):
        """测试文件以缩进块结束"""
        code = """if (true) :
  x = 1
  y = 2"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        self.assertEqual(len(result.then_block.statements), 2)
        # 确保正确到达文件末尾
        self.assertTrue(parser.current_token is None or parser.current_token.type == 'EOF')

    def test_file_ends_with_nested_blocks(self):
        """测试文件以嵌套块结束"""
        code = """if (true) :
  if (false) :
    x = 1"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        inner_if = result.then_block.statements[0]
        self.assertIsInstance(inner_if, IfStatement)
        self.assertEqual(len(inner_if.then_block.statements), 1)

    def test_multiple_dedents_at_file_end(self):
        """测试文件结束时的多层反缩进"""
        code = """if (a) :
  if (b) :
    if (c) :
      x = 1"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        # 验证所有嵌套层级都正确解析
        inner_if1 = result.then_block.statements[0]
        self.assertIsInstance(inner_if1, IfStatement)
        inner_if2 = inner_if1.then_block.statements[0]
        self.assertIsInstance(inner_if2, IfStatement)
        self.assertEqual(len(inner_if2.then_block.statements), 1)


class TestIndentBoundaryComplexScenarios(unittest.TestCase):
    """复杂场景测试"""

    def test_complex_nested_with_empty_lines(self):
        """测试复杂嵌套带空行"""
        code = """if (a) :
  x = 1
  
  if (b) :
    y = 2
    
    for (i in range(3)) :
      z = i
      
  w = 3
v = 4"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        # 应该包含 x=1, 内层if, w=3
        self.assertEqual(len(result.then_block.statements), 3)

    def test_rapid_indent_changes(self):
        """测试快速缩进变化"""
        code = """if (a) :
  x = 1
  if (b) :
    y = 2
    if (c) :
      z = 3
    y = 4
  x = 5
w = 6"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, IfStatement)
        # 验证所有层级正确
        self.assertEqual(len(result.then_block.statements), 3)  # x=1, 内层if, x=5

    def test_while_with_internal_if(self):
        """测试 while 循环内部有 if"""
        code = """while (true) :
  if (condition) :
    break
  x = x + 1"""
        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, WhileStatement)
        self.assertEqual(len(result.body.statements), 2)

    def test_for_with_nested_if_else(self):
        """测试 for 循环嵌套 if-else"""
        code = """for (i in range(10)) :
  if (i % 2 == 0) :
    echo "even"
  else :
    echo "odd"
  echo "done"
"""

        lexer = HPLLexer(code)
        tokens = lexer.tokenize()
        parser = HPLASTParser(tokens)
        result = parser.parse_statement()
        
        self.assertIsInstance(result, ForInStatement)
        # for 体应该包含 if-else 和 echo
        self.assertEqual(len(result.body.statements), 2)


if __name__ == '__main__':
    unittest.main()

