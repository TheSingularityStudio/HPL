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

# 处理模块和直接执行的导入


try:
    from src.models import HPLClass, HPLObject, HPLFunction
    from src.lexer import HPLLexer
    from src.ast_parser import HPLASTParser
except ImportError:
    from models import HPLClass, HPLObject, HPLFunction
    from lexer import HPLLexer
    from ast_parser import HPLASTParser


class HPLParser:
    def __init__(self, hpl_file):
        self.hpl_file = hpl_file
        self.classes = {}
        self.objects = {}
        self.main_func = None
        self.call = None  # 存储 call 指令
        self.data = self.load_data()


    def load_data(self):
        with open(self.hpl_file, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        data = yaml.safe_load(yaml_content)
        if 'includes' in data:
            for include_file in data['includes']:
                include_path = os.path.join(os.path.dirname(self.hpl_file), include_file)
                with open(include_path, 'r', encoding='utf-8') as f:
                    include_content = f.read()
                include_data = yaml.safe_load(include_content)
                self.merge_data(data, include_data)
        return data

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
        if 'call' in self.data:
            self.call = self.parse_call(self.data['call'])
        return self.classes, self.objects, self.main_func, self.call

    def parse_call(self, call_str):
        # 解析 call 指令: funcName(args)
        start = call_str.find('(')
        end = call_str.find(')')
        func_name = call_str[:start].strip()
        params_str = call_str[start+1:end]
        args = [p.strip() for p in params_str.split(',')] if params_str else []
        return {'func_name': func_name, 'args': args}


    def parse_classes(self):
        for class_name, class_def in self.data['classes'].items():
            if isinstance(class_def, dict):
                methods = {}
                parents = []
                for key, value in class_def.items():
                    if key == 'parent':
                        if isinstance(value, list):
                            parents = value
                        else:
                            parents = [value]
                    else:
                        methods[key] = self.parse_function(value)
                self.classes[class_name] = HPLClass(class_name, methods, parents)
            else:
                raise ValueError(f"Invalid class definition for {class_name}. Use dict with 'parent' key.")

    def parse_objects(self):
        for obj_name, obj_def in self.data['objects'].items():
            # obj_def 类似 "ClassName()" 或 "ClassName(arg1, arg2)"
            # 解析类名和构造函数参数
            start = obj_def.find('(')
            end = obj_def.find(')')
            if start == -1 or end == -1:
                raise ValueError(f"Invalid object definition for {obj_name}: {obj_def}")
            
            class_name = obj_def[:start].strip()
            args_str = obj_def[start+1:end].strip()
            
            # 解析参数
            args = []
            if args_str:
                # 支持字符串参数（带引号）和数字参数
                i = 0
                current_arg = ''
                in_string = False
                string_char = None
                while i < len(args_str):
                    char = args_str[i]
                    if char in ['"', "'"] and not in_string:
                        in_string = True
                        string_char = char
                        current_arg += char
                    elif char == string_char and in_string:
                        in_string = False
                        string_char = None
                        current_arg += char
                    elif char == ',' and not in_string:
                        args.append(self._parse_arg(current_arg.strip()))
                        current_arg = ''
                    else:
                        current_arg += char
                    i += 1
                if current_arg.strip():
                    args.append(self._parse_arg(current_arg.strip()))
            
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
        # 解析函数：func(params){ body; }
        start = func_str.find('(')
        end = func_str.find(')')
        params_str = func_str[start+1:end]
        params = [p.strip() for p in params_str.split(',')] if params_str else []
        
        # 改进的函数体解析：正确处理嵌套大括号
        body_start = func_str.find('{', end)  # 从参数结束后开始找第一个 {
        if body_start == -1:
            raise ValueError("Function body must start with '{'")
        
        # 使用计数器找到匹配的 }
        brace_count = 1
        body_end = body_start + 1
        while brace_count > 0 and body_end < len(func_str):
            if func_str[body_end] == '{':
                brace_count += 1
            elif func_str[body_end] == '}':
                brace_count -= 1
            body_end += 1
        
        if brace_count != 0:
            raise ValueError("Unmatched braces in function body")
        
        # body_end 现在指向匹配 } 的下一个位置
        body_str = func_str[body_start+1:body_end-1].strip()
        
        # 标记化和解析AST
        lexer = HPLLexer(body_str)
        tokens = lexer.tokenize()
        ast_parser = HPLASTParser(tokens)
        body_ast = ast_parser.parse_block()
        return HPLFunction(params, body_ast)
