from src.models import HPLClass, HPLObject, HPLFunction

class HPLEvaluator:
    def __init__(self, classes, objects, main_func):
        self.classes = classes
        self.objects = objects
        self.main_func = main_func
        self.global_scope = {}  # 用于变量等

    def run(self):
        if self.main_func:
            self.execute_function(self.main_func, {})

    def execute_function(self, func, local_scope):
        # 占位符：解析并执行主体
        # 现在，只是打印主体
        print(f"Executing function with body: {func.body}")
        # 真正的实现会将主体解析为语句并执行它们

    def call_method(self, obj_name, method_name, args):
        if obj_name in self.objects:
            obj = self.objects[obj_name]
            hpl_class = obj.hpl_class
            if method_name in hpl_class.methods:
                method = hpl_class.methods[method_name]
                self.execute_function(method, {param: args[i] for i, param in enumerate(method.params)})
            elif hpl_class.parent and method_name in self.classes[hpl_class.parent].methods:
                # 继承
                method = self.classes[hpl_class.parent].methods[method_name]
                self.execute_function(method, {param: args[i] for i, param in enumerate(method.params)})
        else:
            raise ValueError(f"Object {obj_name} not found")

    # 内置函数
    def echo(self, message):
        print(message)

    # 其他用于表达式、语句等的评估方法
