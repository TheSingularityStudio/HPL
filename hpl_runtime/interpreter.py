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

# 确保 hpl_runtime 目录在 Python 路径中
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from hpl_runtime.core.parser import HPLParser
    from hpl_runtime.core.evaluator import HPLEvaluator
    from hpl_runtime.core.models import ImportStatement, HPLObject
    from hpl_runtime.modules.loader import set_current_hpl_file
    from hpl_runtime.utils.exceptions import (
        HPLError, HPLSyntaxError, HPLRuntimeError, HPLImportError,
        format_error_for_user
    )
except ImportError:
    from hpl_runtime.core.parser import HPLParser
    from hpl_runtime.core.evaluator import HPLEvaluator
    from hpl_runtime.core.models import ImportStatement, HPLObject
    from hpl_runtime.modules.loader import set_current_hpl_file
    from hpl_runtime.utils.exceptions import (
        HPLError, HPLSyntaxError, HPLRuntimeError, HPLImportError,
        format_error_for_user
    )






def main():
    if len(sys.argv) != 2:
        print("Usage: python interpreter.py <hpl_file>")
        sys.exit(1)

    hpl_file = sys.argv[1]
    
    # 设置当前 HPL 文件路径，用于相对导入
    set_current_hpl_file(hpl_file)
    
    try:
        parser = HPLParser(hpl_file)

        classes, objects, functions, main_func, call_target, call_args, imports = parser.parse()

        evaluator = HPLEvaluator(classes, objects, functions, main_func, call_target, call_args)

        # 处理顶层导入（必须在对象实例化之前，以便构造函数可以使用导入的模块）
        for imp in imports:


            module_name = imp['module']
            alias = imp['alias'] or module_name
            # 创建 ImportStatement 并执行
            import_stmt = ImportStatement(module_name, alias)
            evaluator.execute_import(import_stmt, evaluator.global_scope)

        # 实例化所有对象并调用构造函数（在导入之后，以便构造函数可以使用导入的模块）
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
                evaluator._call_constructor(obj, parsed_args)

        evaluator.run()

    except HPLSyntaxError as e:
        print(format_error_for_user(e))
        sys.exit(1)
    except HPLRuntimeError as e:
        print(format_error_for_user(e))
        sys.exit(1)
    except HPLImportError as e:
        print(format_error_for_user(e))
        sys.exit(1)
    except HPLError as e:
        print(format_error_for_user(e))
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ File not found: {e.filename}")
        sys.exit(1)
    except Exception as e:
        # 未预期的内部错误，显示完整信息
        import traceback
        print(f"❌ Internal Error: {e}")
        print("\n--- Full traceback ---")
        traceback.print_exc()
        sys.exit(1)



if __name__ == "__main__":
    main()
