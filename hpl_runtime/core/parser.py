"""
HPL 顶层解析器模块

该模块负责处理 HPL 源文件的顶层解析，包括 YAML 结构解析、
文件包含处理、函数定义的预处理，以及协调词法分析器和 AST 解析器。
是连接 HPL 配置文件与解释器执行引擎的桥梁。

关键类：
- HPLParser: 顶层解析器，处理 HPL 文件的完整解析流程

主要功能：
- 加载和解析 HPL 文件（YAML 格式）
- 预处理函数定义（箭头函数语法转换）
- 处理文件包含（includes）
- 解析类、对象、函数定义
- 协调 lexer 和 ast_parser 生成最终 AST
"""

from __future__ import annotations
from typing import Any, Optional, Union

import yaml
import os
import re
from pathlib import Path

from hpl_runtime.core.models import HPLClass, HPLObject, HPLFunction, BlockStatement
from hpl_runtime.core.lexer import HPLLexer, Token
from hpl_runtime.core.ast_parser import HPLASTParser
from hpl_runtime.modules.loader import HPL_MODULE_PATHS
from hpl_runtime.utils.exceptions import HPLSyntaxError, HPLImportError
from hpl_runtime.utils.path_utils import resolve_include_path
from hpl_runtime.utils.text_utils import preprocess_functions, parse_call_expression



class HPLParser:
    def __init__(self, hpl_file: str) -> None:
        self.hpl_file: str = hpl_file
        self.classes: dict[str, HPLClass] = {}
        self.objects: dict[str, HPLObject] = {}
        self.functions: dict[str, HPLFunction] = {}  # 存储所有顶层函数
        self.main_func: Optional[HPLFunction] = None
        self.call_target: Optional[str] = None
        self.call_args: list[Any] = []  # 存储 call 的参数
        self.imports: list[dict[str, Any]] = []  # 存储导入语句
        self.source_code: Optional[str] = None  # 存储源代码用于错误显示
        self.data: dict[str, Any] = self.load_and_parse()



    def _merge_duplicate_keys(self, content: str) -> str:
        """合并 YAML 中重复的键（如多个 objects 或 classes 段）"""
        # 只合并特定的字典类型键
        keys_to_merge = ['objects', 'classes']
        
        lines = content.split('\n')
        key_contents: dict[str, list[str]] = {}  # 存储每个键的所有内容
        key_order: list[str] = []  # 记录键的出现顺序
        current_key: Optional[str] = None
        current_lines: list[str] = []

        
        for line in lines:
            stripped = line.strip()
            
            # 检查是否是顶级键（无缩进，后跟冒号）
            if stripped and not line.startswith(' ') and not line.startswith('\t') and ':' in stripped:
                key = stripped[:stripped.find(':')].strip()
                
                # 只处理需要合并的键
                if key in keys_to_merge:
                    # 保存之前键的内容
                    if current_key and current_lines and current_key in keys_to_merge:
                        if current_key not in key_contents:
                            key_contents[current_key] = []
                            key_order.append(current_key)
                        key_contents[current_key].extend(current_lines)
                    
                    # 开始新键
                    current_key = key
                    current_lines = []
                else:
                    # 对于不需要合并的键，保存之前的内容并重置
                    if current_key and current_lines and current_key in keys_to_merge:
                        if current_key not in key_contents:
                            key_contents[current_key] = []
                            key_order.append(current_key)
                        key_contents[current_key].extend(current_lines)
                    current_key = None
                    current_lines = []
            elif current_key and current_key in keys_to_merge:
                # 属于当前合并键的内容
                current_lines.append(line)
        
        # 保存最后一个键的内容
        if current_key and current_lines and current_key in keys_to_merge:
            if current_key not in key_contents:
                key_contents[current_key] = []
                key_order.append(current_key)
            key_contents[current_key].extend(current_lines)
        
        # 如果没有需要合并的键，直接返回原内容
        if not key_order:
            return content
        
        # 重建内容，合并重复的键
        result: list[str] = []
        processed_keys: set[str] = set()
        current_key = None
        
        for line in lines:

            stripped = line.strip()
            
            # 检查是否是顶级键
            if stripped and not line.startswith(' ') and not line.startswith('\t') and ':' in stripped:
                key = stripped[:stripped.find(':')].strip()
                
                # 如果是需要合并的键且未处理过
                if key in keys_to_merge and key not in processed_keys:
                    # 输出合并后的键
                    result.append(f"{key}:")
                    result.extend(key_contents[key])
                    processed_keys.add(key)
                    current_key = key
                elif key not in keys_to_merge:
                    # 不需要合并的键，直接输出
                    result.append(line)
                    current_key = None
                # 如果是已处理的合并键，跳过
            elif current_key in processed_keys:
                # 跳过已合并键的原始内容
                continue
            else:
                # 其他内容直接输出
                result.append(line)
        
        return '\n'.join(result)


    def load_and_parse(self) -> dict[str, Any]:
        """加载并解析 HPL 文件"""

        with open(self.hpl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 保存原始源代码用于错误显示
        self.source_code = content
        
        # 预处理：合并重复的 YAML 键
        content = self._merge_duplicate_keys(content)
        
        # 预处理：将函数定义转换为 YAML 字面量块格式
        content = preprocess_functions(content)
       
        # 使用自定义 YAML 解析器
        data = yaml.safe_load(content)
  
        # 如果 YAML 解析返回 None（空文件或只有注释），使用空字典
        if data is None:
            data = {}
        
        # 处理 includes（支持多路径搜索和嵌套include）
        if 'includes' in data:
            for include_file in data['includes']:
                include_path = resolve_include_path(include_file, self.hpl_file, HPL_MODULE_PATHS)
                if include_path:
                    try:
                        with open(include_path, 'r', encoding='utf-8') as f:
                            include_content = f.read()
                        include_content = preprocess_functions(include_content)

                        include_data = yaml.safe_load(include_content)
                        self.merge_data(data, include_data)
                    except yaml.YAMLError as e:
                        # 尝试获取错误行号
                        line = getattr(e, 'problem_mark', None)
                        line_num = line.line + 1 if line else None
                        raise HPLSyntaxError(
                            f"YAML syntax error in included file '{include_file}': {e}",
                            line=line_num,
                            file=include_path,
                            error_key='SYNTAX_YAML_ERROR'
                        ) from e
                    except Exception as e:
                        raise HPLImportError(
                            f"Failed to include '{include_file}': {e}",
                            file=include_path,
                            error_key='IMPORT_MODULE_NOT_FOUND'
                        ) from e
                else:
                    raise HPLImportError(
                        f"Include file '{include_file}' not found in any search path",
                        file=self.hpl_file,
                        error_key='IMPORT_MODULE_NOT_FOUND'
                    )

        
        return data


    def merge_data(self, main_data: dict[str, Any], include_data: dict[str, Any]) -> None:
        """合并include数据到主数据，支持classes、objects、functions、imports"""

        # 预定义的保留键，不是函数
        reserved_keys = {'includes', 'imports', 'classes', 'objects', 'call'}
        
        # 合并字典类型的数据（classes, objects）
        for key in ['classes', 'objects']:
            if key in include_data:
                if key not in main_data:
                    main_data[key] = {}
                if isinstance(include_data[key], dict):
                    main_data[key].update(include_data[key])
        
        # 合并函数定义（HPL中函数是顶层键值对，值包含'=>'）
        for key, value in include_data.items():
            if key not in reserved_keys:
                # 检查是否是函数定义（包含 =>）
                if isinstance(value, str) and '=>' in value:
                    # 只合并主数据中不存在的函数（避免覆盖）
                    if key not in main_data:
                        main_data[key] = value
        
        # 合并imports
        if 'imports' in include_data:
            if 'imports' not in main_data:
                main_data['imports'] = []
            if isinstance(include_data['imports'], list):
                main_data['imports'].extend(include_data['imports'])


    def parse(self) -> tuple[dict[str, HPLClass], dict[str, HPLObject], dict[str, HPLFunction], Optional[HPLFunction], Optional[str], list[Any], list[dict[str, Any]]]:
        # 处理顶层 import 语句
        if 'imports' in self.data:
            self.parse_imports()
        
        if 'classes' in self.data:
            self.parse_classes()
        if 'objects' in self.data:
            self.parse_objects()
        
        # 解析所有顶层函数（包括 main 和其他自定义函数）
        self.parse_top_level_functions()
        
        # 处理 call 键
        self.call_args = []  # 存储 call 的参数
        if 'call' in self.data:
            call_str = self.data['call']
            # 解析函数名和参数，如 add(5, 3) -> 函数名: add, 参数: [5, 3]
            self.call_target, self.call_args = parse_call_expression(call_str)

        return self.classes, self.objects, self.functions, self.main_func, self.call_target, self.call_args, self.imports



    def parse_top_level_functions(self) -> None:
        """解析所有顶层函数定义"""

        # 预定义的保留键，不是函数
        reserved_keys = {'includes', 'imports', 'classes', 'objects', 'call'}
        
        for key, value in self.data.items():
            if key in reserved_keys:
                continue
            
            # 检查值是否是函数定义（包含 =>）
            if isinstance(value, str) and '=>' in value:
                # 找到函数在源代码中的行号和列号
                start_line, start_column = self._find_function_line(key)
                func = self.parse_function(value, start_line, start_column)
                self.functions[key] = func
                
                # 特别处理 main 函数
                if key == 'main':
                    self.main_func = func


    def _find_function_line(self, func_name: str) -> tuple[int, int]:
        """找到函数定义在源代码中的行号"""
        if not self.source_code:
            return 1, 1
        
        lines = self.source_code.split('\n')
        for i, line in enumerate(lines, 1):
            # 匹配函数定义模式：func_name: (...) => {
            stripped = line.strip()
            if stripped.startswith(f"{func_name}:") and '=>' in stripped:
                # 计算列号：找到函数名在行中的位置
                col = line.find(f"{func_name}:") + 1
                return i, col
        return 1, 1



    def parse_imports(self) -> None:
        """解析顶层 import 语句"""

        imports_data = self.data['imports']
        if isinstance(imports_data, list):
            for imp in imports_data:
                if isinstance(imp, str):
                    # 简单格式: module_name
                    self.imports.append({'module': imp, 'alias': None})
                elif isinstance(imp, dict):
                    # 复杂格式: {module: alias}
                    for module, alias in imp.items():
                        self.imports.append({'module': module, 'alias': alias})


    def parse_classes(self) -> None:
        for class_name, class_def in self.data['classes'].items():
            if isinstance(class_def, dict):
                methods: dict[str, HPLFunction] = {}
                parent: Optional[str] = None
                for key, value in class_def.items():
                    if key == 'parent':
                        parent = value
                    else:
                        # 找到类方法在源代码中的行号和列号
                        start_line, start_column = self._find_method_line(class_name, key)
                        methods[key] = self.parse_function(value, start_line, start_column)

                self.classes[class_name] = HPLClass(class_name, methods, parent)



    def _find_method_line(self, class_name: str, method_name: str) -> tuple[int, int]:
        """找到类方法定义在源代码中的行号"""
        if not self.source_code:
            return 1, 1
        
        lines = self.source_code.split('\n')

        in_target_class = False
        class_indent = 0

        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 检查是否是类定义开始
            if stripped.startswith(f"{class_name}:"):
                in_target_class = True
                class_indent = len(line) - len(line.lstrip())
                continue
            
            if in_target_class:
                # 检查是否离开当前类（遇到相同或更少缩进的非空行）
                if stripped and not stripped.startswith('#'):
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= class_indent and not stripped.startswith(f"{method_name}:"):
                        # 离开了当前类
                        in_target_class = False
                        continue
                
                # 在当前类中查找方法
                if stripped.startswith(f"{method_name}:") and '=>' in stripped:
                    # 计算列号：找到方法名在行中的位置
                    col = line.find(f"{method_name}:") + 1
                    return i, col
        
        return 1, 1


    def parse_objects(self) -> None:
        for obj_name, obj_def in self.data['objects'].items():

            # 解析构造函数参数
            if '(' in obj_def and ')' in obj_def:
                class_name = obj_def[:obj_def.find('(')].strip()
                args_str = obj_def[obj_def.find('(')+1:obj_def.find(')')].strip()
                args = [arg.strip() for arg in args_str.split(',')] if args_str else []
            else:
                class_name = obj_def.rstrip('()')
                args = []
            
            if class_name in self.classes:
                hpl_class = self.classes[class_name]
                # 创建对象，稍后由 evaluator 调用构造函数
                self.objects[obj_name] = HPLObject(obj_name, hpl_class, {'__init_args__': args})


    def parse_function(self, func_str: str, start_line: int = 1, start_column: int = 1) -> HPLFunction:

        func_str = func_str.strip()
        
        # 新语法: (params) => { body }
        start = func_str.find('(')
        end = func_str.find(')')
        params_str = func_str[start+1:end]
        params = [p.strip() for p in params_str.split(',')] if params_str else []
        
        # 找到箭头 =>
        arrow_pos = func_str.find('=>', end)
        if arrow_pos == -1:
            raise HPLSyntaxError(
                "Arrow function syntax error: => not found",
                file=self.hpl_file,
                error_key='SYNTAX_MISSING_BRACKET'
            )
        
        # 找到函数体
        body_start = func_str.find('{', arrow_pos)
        body_end = func_str.rfind('}')
        if body_start == -1 or body_end == -1:
            raise HPLSyntaxError(
                "Arrow function syntax error: braces not found",
                file=self.hpl_file,
                error_key='SYNTAX_MISSING_BRACKET'
            )


        body_str = func_str[body_start+1:body_end].strip()
        
        # 计算函数体在原始文件中的起始行号
        # 计算函数定义字符串中，函数体开始位置 '{'' 之前有多少个换行符
        body_start_in_func = func_str.find('{', arrow_pos)
        newlines_before_body = func_str[:body_start_in_func].count('\n')
        # +1 因为函数体内容从开括号 '{' 的下一行开始
        # 在提取的函数字符串中，函数体位于第 2 行（在 '{' 后面的 '\n' 之后）

        actual_start_line = start_line + newlines_before_body + 1
        
        # 计算函数体在原始文件中的起始列号
        # 找到函数体开始位置 '{' 在函数定义字符串中的位置
        brace_pos_in_func = body_start_in_func
        # 计算 '{' 之前的换行符位置，确定 '{' 在其所在行的偏移
        last_newline_pos = func_str.rfind('\n', 0, brace_pos_in_func)
        if last_newline_pos == -1:
            # '{' 在第一行，列号 = 函数定义起始列号 + '{' 在函数定义中的位置
            actual_start_column = start_column + brace_pos_in_func + 1  # +1 因为 '{' 本身占一列
        else:
            # '{' 不在第一行，列号 = '{' 在其所在行的偏移 + 1
            actual_start_column = brace_pos_in_func - last_newline_pos
        
        # 标记化和解析AST，传递起始行号和列号
        lexer = HPLLexer(body_str, start_line=actual_start_line, start_column=actual_start_column)
        tokens = lexer.tokenize()
        ast_parser = HPLASTParser(tokens)
        body_ast = ast_parser.parse_block()
        return HPLFunction(params, body_ast)
