"""
HPL 解释器主入口模块 (HPL Interpreter Main Module)

该模块是 HPL 语言的命令行解释器入口点，负责协调整个解释流程。
它从命令行接收 HPL 源文件路径，调用解析器和求值器执行程序。

主要功能：
    - 命令行参数解析：接收并验证 HPL 源文件路径
    - 文件加载：读取并验证 HPL 源文件存在性
    - 解释流程协调：依次调用解析器和求值器
    - 错误处理：捕获并报告各类运行时错误

使用方式：
    python interpreter.py <hpl_file>
    
    例如：
    python interpreter.py examples/example.hpl

异常处理：
    - FileNotFoundError: 文件不存在
    - yaml.YAMLError: YAML 语法错误
    - ValueError: 语义错误
    - Exception: 其他未预期错误
"""

import sys
import os
import yaml

# 处理模块和直接执行的导入


try:
    from src.parser import HPLParser
    from src.evaluator import HPLEvaluator
except ImportError:
    from parser import HPLParser
    from evaluator import HPLEvaluator



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

def main():
    if len(sys.argv) != 2:
        print("Usage: python interpreter.py <hpl_file>")
        sys.exit(1)

    hpl_file = sys.argv[1]
    
    try:
        parser = HPLParser(hpl_file)
        classes, objects, main_func, call_target = parser.parse()

        evaluator = HPLEvaluator(classes, objects, main_func, call_target)
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
