import yaml
import os

# Handle imports for both module and direct execution
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
        return self.classes, self.objects, self.main_func

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
            # obj_def 类似 "ClassName()"
            class_name = obj_def.rstrip('()')
            if class_name in self.classes:
                self.objects[obj_name] = HPLObject(obj_name, self.classes[class_name])

    def parse_function(self, func_str):
        # 解析函数：func(params){ body; }
        start = func_str.find('(')
        end = func_str.find(')')
        params_str = func_str[start+1:end]
        params = [p.strip() for p in params_str.split(',')] if params_str else []
        body_start = func_str.find('{')
        body_end = func_str.rfind('}')
        body_str = func_str[body_start+1:body_end].strip()
        # 标记化和解析AST
        lexer = HPLLexer(body_str)
        tokens = lexer.tokenize()
        ast_parser = HPLASTParser(tokens)
        body_ast = ast_parser.parse_block()
        return HPLFunction(params, body_ast)
