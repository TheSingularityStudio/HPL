#!/usr/bin/env python3
"""
HPL 文件启动器

该程序作为HPL解释器的启动入口，用于运行.hpl文件。
支持命令行参数和文件拖放。

使用方法:
    HPL.exe <hpl_file>
    或将.hpl文件拖放到exe上
"""

import sys
import os
import subprocess
import time
import traceback


def wait_for_exit(message="\n按回车键退出..."):
    """
    安全地等待用户按键退出
    在无控制台模式下（如PyInstaller --noconsole），stdin可能不可用，
    此时使用time.sleep作为替代方案
    """
    try:
        # 尝试检测stdin是否可用
        if sys.stdin is not None and sys.stdin.isatty():
            input(message)
        else:
            # stdin不可用，等待几秒后自动退出
            print("\n程序将在3秒后自动退出...")
            time.sleep(3)
    except (RuntimeError, AttributeError, EOFError):
        # 处理lost sys.stdin等错误
        print("\n程序将在3秒后自动退出...")
        time.sleep(3)

def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持打包后的exe）"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def find_hpl_runtime():
    """查找hpl_runtime目录的多种方法"""
    # 方法1: 打包后的资源路径
    if hasattr(sys, '_MEIPASS'):
        runtime_path = os.path.join(sys._MEIPASS, 'hpl_runtime')
        if os.path.exists(runtime_path):
            return runtime_path
    
    # 方法2: 当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    runtime_path = os.path.join(script_dir, 'hpl_runtime')
    if os.path.exists(runtime_path):
        return runtime_path
    
    # 方法3: 当前工作目录
    runtime_path = os.path.join(os.getcwd(), 'hpl_runtime')
    if os.path.exists(runtime_path):
        return runtime_path
    
    # 方法4: 从sys.path中查找
    for path in sys.path:
        runtime_path = os.path.join(path, 'hpl_runtime')
        if os.path.exists(runtime_path):
            return runtime_path
    
    return None


def run_hpl_file(hpl_file):
    """运行HPL文件"""
    # 调试信息
    debug_mode = os.environ.get('HPL_DEBUG', '0') == '1'
    
    if debug_mode:
        print(f"[DEBUG] 尝试运行文件: {hpl_file}")
        print(f"[DEBUG] 当前工作目录: {os.getcwd()}")
        print(f"[DEBUG] sys.path: {sys.path[:3]}...")
    
    # 检查文件是否存在
    if not os.path.exists(hpl_file):
        print(f"错误: 文件不存在 - {hpl_file}")
        return 1
    
    # 检查文件扩展名
    if not hpl_file.endswith('.hpl'):
        print(f"警告: 文件扩展名不是.hpl - {hpl_file}")
    
    # 查找hpl_runtime目录
    runtime_dir = find_hpl_runtime()
    if runtime_dir is None:
        print("错误: 无法找到hpl_runtime目录")
        print("请确保hpl_runtime目录与HPL.exe在同一目录下")
        return 1
    
    if debug_mode:
        print(f"[DEBUG] 找到hpl_runtime目录: {runtime_dir}")
    
    # 尝试运行解释器
    try:
        # 将hpl_runtime添加到Python路径
        if runtime_dir not in sys.path:
            sys.path.insert(0, runtime_dir)
            if debug_mode:
                print(f"[DEBUG] 已添加路径: {runtime_dir}")
        
        # 导入并运行解释器
        from interpreter import main as interpreter_main
        
        # 设置命令行参数
        sys.argv = ['interpreter.py', os.path.abspath(hpl_file)]
        
        if debug_mode:
            print(f"[DEBUG] 调用解释器: sys.argv = {sys.argv}")
        
        # 运行解释器
        interpreter_main()
        return 0
        
    except SystemExit as e:
        # 捕获解释器调用的sys.exit()，返回退出码
        return e.code if isinstance(e.code, int) else 1
        
    except ImportError as e:
        print(f"错误: 无法加载HPL解释器 - {e}")
        print(f"请确保hpl_runtime目录在正确的位置: {runtime_dir}")
        if debug_mode:
            traceback.print_exc()
        return 1
    except Exception as e:
        print(f"运行时错误: {e}")
        if debug_mode:
            traceback.print_exc()
        return 1



def show_usage():
    """显示使用说明"""
    print("=" * 50)
    print("HPL 文件启动器")
    print("=" * 50)
    print()
    print("用法:")
    print("  HPL.exe <hpl_file>")
    print()
    print("示例:")
    print("  HPL.exe examples/example.hpl")
    print("  HPL.exe C:\\path\\to\\your\\file.hpl")
    print()
    print("提示:")
    print("  - 可以将.hpl文件拖放到此exe上运行")
    print("  - 支持相对路径和绝对路径")
    print("=" * 50)

def main():
    """主函数"""
    # 调试模式检测
    debug_mode = os.environ.get('HPL_DEBUG', '0') == '1'
    
    if debug_mode:
        print(f"[DEBUG] sys.argv = {sys.argv}")
        print(f"[DEBUG] 参数数量: {len(sys.argv)}")
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        show_usage()
        print("\n错误: 未提供HPL文件路径")
        print(f"调试信息: sys.argv = {sys.argv}")
        wait_for_exit()
        return 1
    
    # 获取HPL文件路径（支持多个文件，但只处理第一个）
    # 注意：拖放文件时，Windows会自动处理带空格的路径
    hpl_file = sys.argv[1]
    
    # 清理路径（去除可能的引号）
    hpl_file = hpl_file.strip('"\'')
    
    # 转换为绝对路径
    if not os.path.isabs(hpl_file):
        hpl_file = os.path.abspath(hpl_file)
    
    if debug_mode:
        print(f"[DEBUG] 处理后的文件路径: {hpl_file}")
        print(f"[DEBUG] 文件是否存在: {os.path.exists(hpl_file)}")
    
    # 再次检查文件是否存在（处理拖放时的路径问题）
    if not os.path.exists(hpl_file):
        # 尝试从当前工作目录解析
        alt_path = os.path.join(os.getcwd(), os.path.basename(hpl_file))
        if os.path.exists(alt_path):
            hpl_file = alt_path
            if debug_mode:
                print(f"[DEBUG] 使用替代路径: {hpl_file}")
        else:
            print(f"错误: 无法找到文件 - {hpl_file}")
            print(f"当前工作目录: {os.getcwd()}")
            wait_for_exit()
            return 1
    
    print(f"正在运行: {hpl_file}")
    print("-" * 50)
    
    # 运行HPL文件
    result = 0
    try:
        result = run_hpl_file(hpl_file)
    except Exception as e:
        # 捕获任何未处理的异常
        print(f"\n未处理的错误: {e}")
        if debug_mode:
            traceback.print_exc()
        result = 1
    finally:
        # 确保无论是否出错，都暂停让用户看到输出
        wait_for_exit()
    
    return result



if __name__ == "__main__":
    sys.exit(main())
