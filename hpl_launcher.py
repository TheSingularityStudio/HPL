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

def run_hpl_file(hpl_file):
    """运行HPL文件"""
    # 检查文件是否存在
    if not os.path.exists(hpl_file):
        print(f"错误: 文件不存在 - {hpl_file}")
        return 1
    
    # 检查文件扩展名
    if not hpl_file.endswith('.hpl'):
        print(f"警告: 文件扩展名不是.hpl - {hpl_file}")
    
    # 获取解释器路径
    script_dir = get_resource_path('hpl_runtime')
    interpreter_path = os.path.join(script_dir, 'interpreter.py')
    
    # 如果hpl_runtime目录不存在（打包后），使用当前目录
    if not os.path.exists(interpreter_path):
        # 尝试从当前工作目录找到hpl_runtime
        interpreter_path = os.path.join(os.getcwd(), 'hpl_runtime', 'interpreter.py')
    
    # 如果还是找不到，尝试使用PYTHONPATH中的模块
    try:
        # 将hpl_runtime添加到Python路径
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        # 导入并运行解释器
        from interpreter import main as interpreter_main
        
        # 设置命令行参数
        sys.argv = ['interpreter.py', os.path.abspath(hpl_file)]
        
        # 运行解释器
        interpreter_main()
        return 0
        
    except SystemExit as e:
        # 捕获解释器调用的sys.exit()，返回退出码
        # 这样可以让上层函数控制何时退出，确保wait_for_exit()能执行
        return e.code if isinstance(e.code, int) else 1
        
    except ImportError as e:
        print(f"错误: 无法加载HPL解释器 - {e}")
        print("请确保hpl_runtime目录在正确的位置")
        return 1
    except Exception as e:
        print(f"运行时错误: {e}")
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
    # 检查命令行参数
    if len(sys.argv) < 2:
        show_usage()
        print("\n错误: 未提供HPL文件路径")
        wait_for_exit()
        return 1

    
    # 获取HPL文件路径（支持多个文件，但只处理第一个）
    hpl_file = sys.argv[1]
    
    # 转换为绝对路径
    hpl_file = os.path.abspath(hpl_file)
    
    print(f"正在运行: {hpl_file}")
    print("-" * 50)
    
    # 运行HPL文件
    result = 0
    try:
        result = run_hpl_file(hpl_file)
    except Exception as e:
        # 捕获任何未处理的异常
        print(f"\n未处理的错误: {e}")
        result = 1
    finally:
        # 确保无论是否出错，都暂停让用户看到输出
        # 这是解决exe窗口自动关闭问题的关键
        wait_for_exit()
    
    return result




if __name__ == "__main__":
    sys.exit(main())
