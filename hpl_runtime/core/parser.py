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

import yaml
import os
import re
from pathlib import Path

try:
    from hpl_runtime.core.models import HPLClass, HPLObject, HPLFunction
    from hpl_runtime.core.lexer import HPLLexer
    from hpl_runtime.core.ast_parser import HPLASTParser
    from hpl_runtime.modules.loader import HPL_MODULE_PATHS
    from hpl_runtime.utils.exceptions import HPLSyntaxError, HPLImportError
except ImportError:
    from hpl_runtime.core.models import HPLClass, HPLObject, HPLFunction
    from hpl_runtime.core.lexer import HPLLexer
    from hpl_runtime.core.ast_parser import HPLASTParser
    from hpl_runtime.modules.loader import HPL_MODULE_PATHS
    from hpl_runtime.utils.exceptions import HPLSyntaxError, HPLImportError




class HPLParser:
    def __init__(self, hpl_file):
        self.hpl_file = hpl_file
        self.classes = {}
        self.objects = {}
        self.functions = {}  # 存储所有顶层函数
        self.main_func = None
        self.call_target = None
        self.imports = []  # 存储导入语句
        self.source_code = None  # 存储源代码用于错误显示
        self.data = self.load_and_parse()




    def load_and_parse(self):
        """加载并解析 HPL 文件"""
        with open(self.hpl_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 保存原始源代码用于错误显示
        self.source_code = content
        
        # 预处理：将函数定义转换为 YAML 字面量块格式
        content = self.preprocess_functions(content)

        
        # 使用自定义 YAML 解析器
        data = yaml.safe_load(content)
        
        # 如果 YAML 解析返回 None（空文件或只有注释），使用空字典
        if data is None:
            data = {}
        
        # 处理 includes（支持多路径搜索和嵌套include）
        if 'includes' in data:
            for include_file in data['includes']:
                include_path = self._resolve_include_path(include_file)
                if include_path:
                    try:
                        with open(include_path, 'r', encoding='utf-8') as f:
                            include_content = f.read()
                        include_content = self.preprocess_functions(include_content)
                        include_data = yaml.safe_load(include_content)
                        self.merge_data(data, include_data)
                    except yaml.YAMLError as e:
                        # 尝试获取错误行号
                        line = getattr(e, 'problem_mark', None)
                        line_num = line.line + 1 if line else None
                        raise HPLSyntaxError(
                            f"YAML syntax error in included file '{include_file}': {e}",
                            line=line_num,
                            file=include_path
                        ) from e
                    except Exception as e:
                        raise HPLImportError(
                            f"Failed to include '{include_file}': {e}",
                            file=include_path
                        ) from e
                else:
                    raise HPLImportError(
                        f"Include file '{include_file}' not found in any search path",
                        file=self.hpl_file
                    )
        
        return data


    def _resolve_include_path(self, include_file):
        """
        解析include文件路径，支持多种路径格式：
        1. 绝对路径（Unix: /path, Windows: C:\path）
        2. 相对当前文件目录
        3. 相对当前工作目录
        4. HPL_MODULE_PATHS中的路径
        """
        include_path = Path(include_file)
        
        # 1. 检查是否为绝对路径
        if include_path.is_absolute():
            if include_path.exists():
                return str(include_path)
            return None
        
        # 获取当前HPL文件所在目录
        current_dir = Path(self.hpl_file).parent.resolve()
        
        # 2. 相对当前文件目录
        resolved_path = current_dir / include_path
        if resolved_path.exists():
            return str(resolved_path)
        
        # 3. 相对当前工作目录
        cwd_path = Path.cwd() / include_path
        if cwd_path.exists():
            return str(cwd_path)
        
        # 4. HPL_MODULE_PATHS中的路径
        for search_path in HPL_MODULE_PATHS:
            module_path = Path(search_path) / include_path
            if module_path.exists():
                return str(module_path)
        
        return None


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





    def parse(self):
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
            self.call_target, self.call_args = self._parse_call_expression(call_str)
        
        return self.classes, self.objects, self.functions, self.main_func, self.call_target, self.call_args, self.imports

    def _parse_call_expression(self, call_str):
        """解析 call 表达式，提取函数名和参数"""
        call_str = call_str.strip()
        
        # 查找左括号
        if '(' in call_str:
            func_name = call_str[:call_str.find('(')].strip()
            args_str = call_str[call_str.find('(')+1:call_str.rfind(')')].strip()
            
            # 解析参数
            args = []
            if args_str:
                # 按逗号分割参数
                for arg in args_str.split(','):
                    arg = arg.strip()
                    # 尝试解析为整数
                    try:
                        args.append(int(arg))
                    except ValueError:
                        # 尝试解析为浮点数
                        try:
                            args.append(float(arg))
                        except ValueError:
                            # 作为字符串处理（去掉引号）
                            if (arg.startswith('"') and arg.endswith('"')) or \
                               (arg.startswith("'") and arg.endswith("'")):
                                args.append(arg[1:-1])
                            else:
                                args.append(arg)  # 变量名或其他
            
            return func_name, args
        else:
            # 没有括号，如 call: main
            return call_str, []


    def parse_top_level_functions(self):
        """解析所有顶层函数定义"""
        # 预定义的保留键，不是函数
        reserved_keys = {'includes', 'imports', 'classes', 'objects', 'call'}
        
        for key, value in self.data.items():
            if key in reserved_keys:
                continue
            
            # 检查值是否是函数定义（包含 =>）
            if isinstance(value, str) and '=>' in value:
                func = self.parse_function(value)
                self.functions[key] = func
                
                # 特别处理 main 函数
                if key == 'main':
                    self.main_func = func




    def parse_imports(self):
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



    def parse_classes(self):
        for class_name, class_def in self.data['classes'].items():
            if isinstance(class_def, dict):
                methods = {}
                parent = None
                for key, value in class_def.items():
                    if key == 'parent':
                        parent = value
                    else:
                        methods[key] = self.parse_function(value)
                self.classes[class_name] = HPLClass(class_name, methods, parent)

    def parse_objects(self):
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
            raise HPLSyntaxError(
                "Arrow function syntax error: => not found",
                file=self.hpl_file
            )
        
        # 找到函数体
        body_start = func_str.find('{', arrow_pos)
        body_end = func_str.rfind('}')
        if body_start == -1 or body_end == -1:
            raise HPLSyntaxError(
                "Arrow function syntax error: braces not found",
                file=self.hpl_file
            )


        body_str = func_str[body_start+1:body_end].strip()
        
        # 标记化和解析AST
        lexer = HPLLexer(body_str)
        tokens = lexer.tokenize()
        ast_parser = HPLASTParser(tokens)
        body_ast = ast_parser.parse_block()
        return HPLFunction(params, body_ast)
