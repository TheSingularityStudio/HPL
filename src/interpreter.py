import sys
from src.parser import HPLParser
from src.evaluator import HPLEvaluator

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
    parser = HPLParser(hpl_file)
    classes, objects, main_func, call_target = parser.parse()

    evaluator = HPLEvaluator(classes, objects, main_func, call_target)
    evaluator.run()

if __name__ == "__main__":
    main()
