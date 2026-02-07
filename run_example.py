#!/usr/bin/env python3
"""
Script to run the HPL interpreter on the example file.
"""

import sys
import os

# 将 src 添加到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from interpreter import main as interpreter_main

if __name__ == "__main__":
    # 支持命令行参数指定要运行的文件
    if len(sys.argv) > 1:
        # 使用提供的文件路径
        hpl_file = sys.argv[1]
    else:
        # 默认运行示例文件
        hpl_file = 'examples/example.hpl'
    
    sys.argv = ['interpreter.py', hpl_file]
    interpreter_main()
