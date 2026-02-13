"""
HPL 模块基类

定义 HPLModule 基类，供标准库模块使用。
避免循环导入问题。
"""

from hpl_runtime.utils.exceptions import HPLNameError, HPLAttributeError, HPLValueError


class HPLModule:

    """
    HPL 标准库模块基类
    
    每个标准库模块继承此类，提供:
    - 函数注册
    - 命名空间管理
    - 文档说明
    """
    
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.functions = {}  # 函数名 -> 函数
        self.constants = {}  # 常量名 -> 值
    
    def register_function(self, name, func, param_count=None, description=""):
        """注册模块函数"""
        self.functions[name] = {
            'func': func,
            'param_count': param_count,
            'description': description
        }
    
    def register_constant(self, name, value, description=""):
        """注册模块常量"""
        self.constants[name] = {
            'value': value,
            'description': description
        }
    
    def call_function(self, func_name, args):
        """调用模块函数"""
        if func_name not in self.functions:
            raise HPLNameError(f"Function '{func_name}' not found in module '{self.name}'")

        
        func_info = self.functions[func_name]
        func = func_info['func']
        
        # 检查参数数量
        if func_info['param_count'] is not None:
            if len(args) != func_info['param_count']:
                raise HPLValueError(f"Function '{func_name}' expects {func_info['param_count']} arguments, got {len(args)}")

        
        return func(*args)
    
    def get_constant(self, name):
        """获取模块常量"""
        if name not in self.constants:
            raise HPLAttributeError(f"Constant '{name}' not found in module '{self.name}'")
        return self.constants[name]['value']

    
    def list_functions(self):
        """列出模块中所有函数"""
        return list(self.functions.keys())
    
    def list_constants(self):
        """列出模块中所有常量"""
        return list(self.constants.keys())
