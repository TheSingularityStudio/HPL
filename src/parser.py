"""
HPL 解析器模块 (HPL Parser Module)

该模块负责解析 HPL 语言的 YAML 格式源文件，将其转换为内部数据结构。
它是 HPL 解释器的入口解析阶段，协调词法分析和语法分析过程。

主要功能：
    - YAML 文件加载：读取并解析 HPL 源文件（YAML 格式）
    - 文件包含处理：支持通过 includes 关键字包含其他文件
    - 类定义解析：解析类名、父类关系和方法定义
    - 对象实例化：根据类定义创建对象实例
    - 主函数解析：解析程序入口点 main 函数
    - 函数体解析：将函数字符串解析为 AST

解析流程：
    1. 加载 YAML 文件
    2. 处理文件包含（includes）
    3. 解析类定义（classes）
    4. 解析对象定义（objects）
    5. 解析主函数（main）
    6. 对每个函数体进行词法分析和 AST 解析
"""

import yaml
import os
import re
from src.models import HPLClass, HPLObject, HPLFunction
from src.lexer import HPLLexer
from src.ast_parser import HPLASTParser

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

class HPLParser:

    def __init__(self, hpl_file):
        self.hpl_file = hpl_file
        self.classes = {}
        self.objects = {}
        self.main_func = None
        self.call_target = None
        self.data = self.load_and_parse()

    def load_and_parse(self):
        """加载并解析 HPL 文件"""
        with open(self.hpl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 预处理：将函数定义转换为 YAML 字面量块格式
        content = self.preprocess_functions(content)
        
        # 使用自定义 YAML 解析器
        data = yaml.safe_load(content)
        
        # 处理 includes
        if 'includes' in data:
            for include_file in data['includes']:
                include_path = os.path.join(os.path.dirname(self.hpl_file), include_file)
                if os.path.exists(include_path):
                    with open(include_path, 'r', encoding='utf-8') as f:
                        include_content = f.read()
                    include_content = self.preprocess_functions(include_content)
                    include_data = yaml.safe_load(include_content)
                    self.merge_data(data, include_data)
        
        return data

    def preprocess_functions(self, content):
        """
        预处理函数定义，将其转换为 YAML 字面量块格式
        这样 YAML 就不会解析函数体内部的语法
        """
        lines = content.split('\n')
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 检测函数定义行（包含 =>）
            # 匹配模式：methodName: (params) => {
            func_pattern = r'^(\s*)(\w+):\s*\(.*\)\s*=>.*\{'


            match = re.match(func_pattern, line)
            
            if match:
                indent = match.group(1)
                key = match.group(2)
                
                # 收集完整的函数体
                func_lines = [line]
                brace_count = line.count('{') - line.count('}')
                j = i + 1
                
                while brace_count > 0 and j < len(lines):
                    next_line = lines[j]
                    func_lines.append(next_line)
                    brace_count += next_line.count('{') - next_line.count('}')
                    j += 1
                
                # 合并函数定义
                full_func = '\n'.join(func_lines)
                
                # 提取 key 和 value
                colon_pos = full_func.find(':')
                key_part = full_func[:colon_pos].rstrip()
                value_part = full_func[colon_pos+1:].strip()
                
                # 转换为 YAML 字面量块格式
                # 使用 | 表示保留换行符的字面量块
                # 注意：| 后面要直接跟内容，不能有空行
                result.append(f'{key_part}: |')
                for func_line in value_part.split('\n'):
                    result.append(f'{indent}  {func_line}')
                
                i = j
            else:
                result.append(line)
                i += 1
        
        return '\n'.join(result)

    def merge_data(self, main_data, include_data):
        for key in ['classes', 'objects']:
            if key in include_data:
                if key not in main_data:
                    main_data[key] = {}
                main_data[key].update(include_data[key])

    def parse(self):
        if 'classes' in self.data:
            self.parse_classes()
        if 'objects' in self.data:
            self.parse_objects()
        if 'main' in self.data:
            self.main_func = self.parse_function(self.data['main'])
        # 处理 call 键
        if 'call' in self.data:
            call_str = self.data['call']
            self.call_target = call_str.rstrip('()').strip()
        
        return self.classes, self.objects, self.main_func, self.call_target

    def parse_classes(self):
        for class_name, class_def in self.data['classes'].items():
            if isinstance(class_def, dict):
                methods = {}
                parents = []
                for key, value in class_def.items():
                    if key == 'parent':
                        parent = value
                    else:
                        methods[key] = self.parse_function(value)
                self.classes[class_name] = HPLClass(class_name, methods, parent)

    def parse_objects(self):
        for obj_name, obj_def in self.data['objects'].items():
            class_name = obj_def.rstrip('()')
            if class_name in self.classes:
                self.objects[obj_name] = HPLObject(obj_name, self.classes[class_name], args)
            else:
                raise ValueError(f"Undefined class '{class_name}' for object '{obj_name}'")

    def _parse_arg(self, arg_str):
        """解析单个参数，支持字符串和数字"""
        arg_str = arg_str.strip()
        if (arg_str.startswith('"') and arg_str.endswith('"')) or \
           (arg_str.startswith("'") and arg_str.endswith("'")):
            # 字符串字面量
            return arg_str[1:-1]
        elif arg_str.isdigit() or (arg_str.startswith('-') and arg_str[1:].isdigit()):
            # 整数
            return int(arg_str)
        else:
            # 其他情况作为字符串返回
            return arg_str


    def parse_function(self, func_str):
        func_str = func_str.strip()
        
        # 新语法: (params) => { body }
        start = func_str.find('(')
        end = func_str.find(')')
        params_str = func_str[start+1:end]
        params = [p.strip() for p in params_str.split(',')] if params_str else []
        
        # 找到箭头 =>
        arrow_pos = func_str.find('=>', end)
        if arrow_pos == -1:
            raise ValueError("Arrow function syntax error: => not found")
        
        # 找到函数体
        body_start = func_str.find('{', arrow_pos)
        body_end = func_str.rfind('}')
        if body_start == -1 or body_end == -1:
            raise ValueError("Arrow function syntax error: braces not found")
        body_str = func_str[body_start+1:body_end].strip()
        
        # 标记化和解析AST
        lexer = HPLLexer(body_str)
        tokens = lexer.tokenize()
        ast_parser = HPLASTParser(tokens)
        body_ast = ast_parser.parse_block()
        return HPLFunction(params, body_ast)
