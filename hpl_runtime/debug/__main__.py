#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HPL 调试工具模块入口

支持命令行使用方式：
    python -m hpl_runtime.debug <hpl_file> [--verbose]
"""

import sys
import os

# 导入调试解释器
from hpl_runtime.debug import DebugInterpreter


def print_usage():
    print("HPL 调试工具")
    print("用法: python -m hpl_runtime.debug <hpl_file> [选项]")
    print("")
    print("选项:")
    print("  -v, --verbose    显示详细的执行跟踪")
    print("  -h, --help       显示此帮助信息")
    print("")
    print("示例:")
    print("  python -m hpl_runtime.debug examples/debug_demo.hpl")
    print("  python -m hpl_runtime.debug examples/debug_demo.hpl --verbose")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    if sys.argv[1] in ('-h', '--help'):
        print_usage()
        sys.exit(0)
    
    hpl_file = sys.argv[1]
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    
    if not os.path.exists(hpl_file):
        print(f"[错误] 文件不存在: {hpl_file}")
        sys.exit(1)
    
    # 启用调试模式
    os.environ['HPL_DEBUG'] = '1'
    
    print(f"[*] 正在运行: {hpl_file}")
    print(f"[*] 调试模式: 启用")
    if verbose:
        print(f"[*] 详细模式: 启用")
    print("-" * 60)
    
    # 创建调试解释器
    interpreter = DebugInterpreter(debug_mode=True, verbose=verbose)
    
    # 运行脚本
    result = interpreter.run(hpl_file)
    
    print("-" * 60)
    
    if result['success']:
        print("[✓] 脚本执行成功！")
        
        if verbose:
            trace = result['debug_info'].get('execution_trace', [])
            if trace:
                print("\n执行流程摘要:")
                for entry in trace[-5:]:
                    print(f"  {entry['type']}: {entry['details']}")
    else:
        print("[✗] 脚本执行失败")
        print("\n")
        print("=" * 60)
        print("调试报告")
        print("=" * 60)
        interpreter.print_debug_report()
        sys.exit(1)


if __name__ == "__main__":
    main()
