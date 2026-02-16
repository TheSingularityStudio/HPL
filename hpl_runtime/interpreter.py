"""
HPL 解释器主入口模块

该模块是 HPL 解释器的命令行入口点，负责协调整个解释流程。
它解析命令行参数，调用解析器加载和解析 HPL 文件，然后使用
执行器运行解析后的代码。

主要功能：
- 命令行参数处理
- 协调 parser 和 evaluator 完成解释执行
- 作为 HPL 解释器的启动入口

使用方法：
    python interpreter.py <hpl_file>
"""

import sys
import os

# 导入yaml以捕获YAML解析错误
try:
    import yaml
except ImportError:
    yaml = None

# 导入版本信息
from hpl_runtime import __version__

# 确保 hpl_runtime 目录在 Python 路径中

script_dir = os.path.dirname(os.path.abspath(__file__))

# 获取父目录（项目根目录）以便正确导入
project_dir = os.path.dirname(script_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from hpl_runtime.core.parser import HPLParser
from hpl_runtime.core.evaluator import HPLEvaluator
from hpl_runtime.core.models import ImportStatement, HPLObject
from hpl_runtime.modules.loader import set_current_hpl_file
from hpl_runtime.utils.exceptions import (
    HPLError, HPLSyntaxError, HPLRuntimeError, HPLImportError,
    format_error_for_user
)
from hpl_runtime.utils.error_handler import HPLErrorHandler, create_error_handler


def _instantiate_objects(evaluator, handler):
    """
    实例化所有对象并调用构造函数
    将对象实例化逻辑提取为独立函数，便于错误处理
    """
    for obj_name, obj in list(evaluator.objects.items()):
        if isinstance(obj, HPLObject) and '__init_args__' in obj.attributes:
            init_args = obj.attributes.pop('__init_args__')
            # 将参数字符串转换为实际值（数字或字符串）
            parsed_args = []
            for arg in init_args:
                arg = arg.strip()
                # 尝试解析为整数
                try:
                    parsed_args.append(int(arg))
                except ValueError:
                    # 尝试解析为浮点数
                    try:
                        parsed_args.append(float(arg))
                    except ValueError:
                        # 作为字符串处理（去掉引号）
                        if (arg.startswith('"') and arg.endswith('"')) or \
                           (arg.startswith("'") and arg.endswith("'")):
                            parsed_args.append(arg[1:-1])
                        else:
                            parsed_args.append(arg)  # 变量名或其他
            
            # 调用构造函数，添加错误上下文
            try:
                evaluator._call_constructor(obj, parsed_args)
            except HPLRuntimeError as e:
                # 增强错误信息，添加对象实例化上下文
                if e.line is None:
                    e.line = 1  # 默认行号
                raise

def main():
    # 处理命令行选项
    if len(sys.argv) == 1:
        # 没有提供参数，显示用法并返回错误码
        print("Usage: hpl <hpl_file>")
        print("       hpl --version")
        print("       hpl --help")
        sys.exit(1)
    
    if sys.argv[1] in ('--help', '-h'):
        print(f"HPL Runtime {__version__}")
        print("Usage: hpl <hpl_file>")
        print("       hpl --version")
        print("       hpl --help")
        print()
        print("Options:")
        print("  --version, -v    Show version information")
        print("  --help, -h       Show this help message")
        sys.exit(0)

    
    if sys.argv[1] in ('--version', '-v'):
        print(f"HPL Runtime {__version__}")
        sys.exit(0)
    
    if len(sys.argv) != 2:
        print("Usage: hpl <hpl_file>")
        print("       hpl --version")
        print("       hpl --help")
        sys.exit(1)

    hpl_file = sys.argv[1]

    
    # 设置当前 HPL 文件路径，用于相对导入
    set_current_hpl_file(hpl_file)
    
    # 创建错误处理器
    handler = create_error_handler(hpl_file, debug_mode=os.environ.get('HPL_DEBUG'))
    
    try:
        # 读取源代码用于错误显示
        with open(hpl_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # 更新处理器的源代码
        handler.source_code = source_code
        
        parser = HPLParser(hpl_file)
        handler.set_parser(parser)

        (classes, objects, functions, main_func, call_target, call_args, imports,
         user_data) = parser.parse()



        # 检查是否有 main 函数
        if main_func is None:
            print("[ERROR] No main function found in the HPL file")
            sys.exit(1)

        evaluator = HPLEvaluator(classes, objects, functions, main_func, call_target, call_args,
                                  user_data)

        handler.set_evaluator(evaluator)


        # 处理顶层导入（必须在对象实例化之前，以便构造函数可以使用导入的模块）
        for imp in imports:
            module_name = imp['module']
            alias = imp['alias'] or module_name
            # 创建 ImportStatement 并执行
            import_stmt = ImportStatement(module_name, alias)
            evaluator.execute_import(import_stmt, evaluator.global_scope)

        # 实例化所有对象并调用构造函数（在导入之后，以便构造函数可以使用导入的模块）
        _instantiate_objects(evaluator, handler)

        evaluator.run()

    except HPLSyntaxError as e:
        handler.handle_syntax_error(e, parser if 'parser' in locals() else None)

    except HPLRuntimeError as e:
        handler.handle(e)

    except HPLImportError as e:
        handler.handle(e)

    except HPLError as e:
        handler.handle(e)

    except FileNotFoundError as e:
        handler.handle_file_not_found(e)

    except Exception as e:
        # 检查是否是YAML解析错误
        if yaml and hasattr(e, '__class__') and 'yaml' in e.__class__.__module__:
            handler.handle_yaml_error(e, hpl_file)
        
        # 未预期的内部错误
        handler.handle_unexpected_error(e, hpl_file)


if __name__ == "__main__":
    main()
