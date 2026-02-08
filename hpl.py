#!/usr/bin/env python3
"""
HPL CLI 入口点

提供 hpl 命令行工具：
- hpl run <file.hpl>     运行 HPL 程序
- hpl install <package>   安装包
- hpl uninstall <package> 卸载包
- hpl list               列出已安装包
- hpl repl               启动交互式解释器
"""

import sys
import os

# 确保 hpl_runtime 在路径中
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

def main():
    """HPL CLI 主入口"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    if command == 'run':
        run_hpl_file(args)
    elif command in ['install', 'uninstall', 'list', 'search', 'update', 'info', 'path']:
        # 包管理命令
        run_package_manager(command, args)
    elif command == 'repl':
        start_repl()
    elif command == 'help' or command == '--help' or command == '-h':
        print_usage()
    else:
        # 尝试直接作为文件运行
        if command.endswith('.hpl') and os.path.exists(command):
            run_hpl_file([command])
        else:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)


def run_hpl_file(args):
    """运行 HPL 文件"""
    if not args:
        print("Usage: hpl run <file.hpl>")
        sys.exit(1)
    
    hpl_file = args[0]
    
    if not os.path.exists(hpl_file):
        print(f"Error: File not found: {hpl_file}")
        sys.exit(1)
    
    try:
        from hpl_runtime.interpreter import main as interpreter_main
        from hpl_runtime.module_loader import set_current_hpl_file
        
        # 设置当前 HPL 文件路径，用于相对导入
        set_current_hpl_file(hpl_file)
        
        # 设置命令行参数
        sys.argv = [sys.argv[0], hpl_file] + args[1:]
        interpreter_main()

        
    except Exception as e:
        print(f"Error running HPL file: {e}")
        sys.exit(1)


def run_package_manager(command, args):
    """运行包管理器命令"""
    try:
        from hpl_runtime.package_manager import main as pm_main
        
        # 构建参数列表
        sys.argv = ['hpl', command] + args
        pm_main()
        
    except Exception as e:
        print(f"Package manager error: {e}")
        sys.exit(1)


def start_repl():
    """启动交互式解释器"""
    print("HPL Interactive Shell (REPL)")
    print("Type 'exit' or 'quit' to exit")
    print("-" * 40)
    
    try:
        from hpl_runtime.evaluator import HPLEvaluator
        from hpl_runtime.models import HPLClass, HPLObject, HPLFunction, BlockStatement
        from hpl_runtime.lexer import HPLLexer
        from hpl_runtime.ast_parser import HPLASTParser
        
        # 创建简单的全局作用域
        classes = {}
        objects = {}
        main_func = HPLFunction([], BlockStatement([]))
        
        evaluator = HPLEvaluator(classes, objects, main_func)
        
        while True:
            try:
                line = input("hpl> ").strip()
                
                if not line:
                    continue
                
                if line in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                # 简单表达式求值
                try:
                    lexer = HPLLexer(line)
                    tokens = lexer.tokenize()
                    parser = HPLASTParser(tokens)
                    expr = parser.parse_expression()
                    
                    result = evaluator.evaluate_expression(expr, {})
                    
                    if result is not None:
                        print(f"=> {result}")
                        
                except Exception as e:
                    print(f"Error: {e}")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                print("\nGoodbye!")
                break
                
    except Exception as e:
        print(f"REPL error: {e}")
        sys.exit(1)


def print_usage():
    """打印使用说明"""
    print("""
HPL Programming Language CLI

Usage:
  hpl run <file.hpl> [args...]     Run HPL program
  hpl install <package>            Install third-party package
  hpl uninstall <package>          Uninstall package
  hpl list                         List installed packages
  hpl search <query>               Search PyPI for packages
  hpl update                       Update all packages
  hpl info <package>               Show package information
  hpl path --add <path>            Add module search path
  hpl path --list                  List module search paths
  hpl repl                         Start interactive shell
  hpl help                         Show this help

Examples:
  hpl run examples/test_stdlib.hpl
  hpl install requests
  hpl install numpy==1.24.0
  hpl list
  hpl search http

For more information: https://github.com/yourusername/hpl
    """)


if __name__ == '__main__':
    main()
