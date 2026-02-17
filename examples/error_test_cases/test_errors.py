#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HPL 错误测试脚本

用于批量测试 error_test_cases 目录下的所有错误文件，
验证错误位置定位的精准度。
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hpl_runtime.utils.error_handler import create_error_handler
from hpl_runtime.utils.exceptions import HPLSyntaxError, HPLRuntimeError


def test_single_file(file_path, verbose=True):
    """
    测试单个 HPL 错误文件
    
    Args:
        file_path: HPL 文件路径
        verbose: 是否显示详细信息
    
    Returns:
        dict: 测试结果
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"测试文件: {file_path}")
        print(f"{'='*60}")
    
    result = {
        'file': file_path,
        'success': False,
        'error_type': None,
        'line': None,
        'column': None,
        'message': None,
        'has_context': False
    }
    
    try:
        # 尝试运行 HPL 文件
        cmd = [sys.executable, "-m", "hpl_runtime", str(file_path)]
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # 分析输出
        stdout = process.stdout
        stderr = process.stderr
        
        output = stdout + stderr
        
        if verbose:
            print("输出:")
            print(output[:2000] if len(output) > 2000 else output)
            print(f"\n返回码: {process.returncode}")
        
        # 检查是否产生了错误
        if process.returncode != 0 or "ERROR" in output or "Error" in output:
            result['success'] = True  # 成功捕获错误
            
            # 尝试解析错误信息
            if "line" in output.lower():
                # 提取行号
                import re
                line_match = re.search(r'[Ll]ine:?\s*(\d+)', output)
                if line_match:
                    result['line'] = int(line_match.group(1))
                
                col_match = re.search(r'[Cc]olumn:?\s*(\d+)', output)
                if col_match:
                    result['column'] = int(col_match.group(1))
            
            # 确定错误类型
            if "SYNTAX" in output:
                result['error_type'] = "Syntax Error"
            elif "RUNTIME" in output:
                result['error_type'] = "Runtime Error"
            elif "IMPORT" in output:
                result['error_type'] = "Import Error"
            else:
                result['error_type'] = "Unknown Error"
            
            # 检查是否有源代码上下文
            result['has_context'] = "|" in output or "Source context" in output
            
            result['message'] = output.strip().split('\n')[0] if output else "No message"
        
        else:
            result['message'] = "文件执行成功（预期应该失败）"
            if verbose:
                print("警告: 文件执行成功，但预期应该产生错误")
    
    except subprocess.TimeoutExpired:
        result['message'] = "执行超时"
        if verbose:
            print("错误: 执行超时")
    
    except Exception as e:
        result['message'] = f"测试异常: {e}"
        if verbose:
            print(f"测试异常: {e}")
    
    return result


def test_all_files():
    """测试所有错误文件"""
    test_dir = Path(__file__).parent
    hpl_files = sorted(test_dir.glob("*.hpl"))
    
    if not hpl_files:
        print("未找到 .hpl 测试文件")
        return
    
    print(f"找到 {len(hpl_files)} 个测试文件")
    
    results = []
    for hpl_file in hpl_files:
        result = test_single_file(hpl_file, verbose=True)
        results.append(result)
    
    # 打印汇总
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r['success'])
    
    for r in results:
        status = "✓" if r['success'] else "✗"
        line_info = f"行 {r['line']}" if r['line'] else "未知行"
        col_info = f"列 {r['column']}" if r['column'] else ""
        print(f"{status} {r['file'].name:30s} | {r['error_type'] or 'N/A':15s} | {line_info} {col_info}")
    
    print(f"\n总计: {len(results)} 个文件, {success_count} 个成功捕获错误")
    
    return results


def analyze_error_accuracy(file_path, expected_line):
    """
    分析特定文件的错误定位精准度
    
    Args:
        file_path: HPL 文件路径
        expected_line: 预期的错误行号
    
    Returns:
        bool: 是否准确定位
    """
    result = test_single_file(file_path, verbose=False)
    
    if not result['success']:
        return False
    
    actual_line = result['line']
    if actual_line is None:
        return False
    
    # 允许 ±2 行的误差
    return abs(actual_line - expected_line) <= 2


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HPL 错误测试工具")
    parser.add_argument("file", nargs="?", help="测试特定文件")
    parser.add_argument("--all", action="store_true", help="测试所有文件")
    parser.add_argument("--quiet", "-q", action="store_true", help="安静模式")
    
    args = parser.parse_args()
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            # 尝试在 error_test_cases 目录中查找
            file_path = Path(__file__).parent / args.file
        
        if file_path.exists():
            test_single_file(file_path, verbose=not args.quiet)
        else:
            print(f"文件未找到: {args.file}")
            sys.exit(1)
    
    elif args.all:
        test_all_files()
    
    else:
        # 默认测试所有文件
        test_all_files()
