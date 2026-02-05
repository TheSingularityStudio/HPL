import yaml
from src.models import HPLClass, HPLObject, HPLFunction

class HPLParser:
    def __init__(self, yaml_content):
        self.data = yaml.safe_load(yaml_content)
        self.classes = {}
        self.objects = {}
        self.main_func = None

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
                parent = None
                for key, value in class_def.items():
                    if key == 'parent':  # 假设继承标记不同，但在示例中它是DerivedClass: BaseClass
                        parent = value
                    else:
                        methods[key] = self.parse_function(value)
                self.classes[class_name] = HPLClass(class_name, methods, parent)
            elif isinstance(class_def, str):
                # 继承：DerivedClass: BaseClass
                parent = class_def
                self.classes[class_name] = HPLClass(class_name, {}, parent)

    def parse_objects(self):
        for obj_name, obj_def in self.data['objects'].items():
            # obj_def 类似 "ClassName()"
            class_name = obj_def.rstrip('()')
            if class_name in self.classes:
                self.objects[obj_name] = HPLObject(obj_name, self.classes[class_name])

    def parse_function(self, func_str):
        # 简单解析：func(params){ body; }
        # 现在，只是将主体存储为字符串；真正的解析器会进行标记化
        start = func_str.find('(')
        end = func_str.find(')')
        params_str = func_str[start+1:end]
        params = [p.strip() for p in params_str.split(',')] if params_str else []
        body_start = func_str.find('{')
        body_end = func_str.rfind('}')
        body = func_str[body_start+1:body_end].strip()
        return HPLFunction(params, body)
