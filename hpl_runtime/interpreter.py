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
    from hpl_runtime.parser import HPLParser
    from hpl_runtime.evaluator import HPLEvaluator
    from hpl_runtime.models import ImportStatement
    from hpl_runtime.module_loader import set_current_hpl_file
except ImportError:
    from parser import HPLParser
    from evaluator import HPLEvaluator
    from models import ImportStatement
    from module_loader import set_current_hpl_file




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


        
        # 处理顶层导入
        for imp in imports:
            module_name = imp['module']
            alias = imp['alias'] or module_name
            # 创建 ImportStatement 并执行
            import_stmt = ImportStatement(module_name, alias)
            evaluator.execute_import(import_stmt, evaluator.global_scope)


        evaluator.run()
    except FileNotFoundError as e:
        print(f"Error: File not found - {e.filename}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Runtime Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
