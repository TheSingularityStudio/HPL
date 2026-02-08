#!/usr/bin/env python3
"""
HPL启动器打包脚本

使用PyInstaller将hpl_launcher.py打包成exe文件
"""

import os
import sys
import subprocess
import shutil

def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装PyInstaller失败: {e}")
        return False

def build_exe():
    """构建exe文件"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 图标路径
    icon_path = os.path.join(current_dir, "HPL.jpeg")
    if not os.path.exists(icon_path):
        print(f"警告: 图标文件不存在 - {icon_path}")
        icon_path = None
    
    # 启动器路径
    launcher_path = os.path.join(current_dir, "hpl_launcher.py")
    if not os.path.exists(launcher_path):
        print(f"错误: 启动器文件不存在 - {launcher_path}")
        return False
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # 单文件模式
        "--name", "HPL",  # 输出文件名
        "--clean",  # 清理临时文件
        "--hidden-import", "yaml",  # 显式包含yaml模块
        "--hidden-import", "platform",  # 显式包含platform模块
        "--hidden-import", "json",  # 显式包含json模块

    ]


    
    # 添加图标（如果存在）

    if icon_path:
        cmd.extend(["--icon", icon_path])
    
    # 添加数据文件（hpl_runtime目录）
    hpl_runtime_path = os.path.join(current_dir, "hpl_runtime")
    if os.path.exists(hpl_runtime_path):
        # 在Windows上使用;作为分隔符，Linux/Mac使用:
        separator = ";" if sys.platform == "win32" else ":"
        cmd.extend(["--add-data", f"hpl_runtime{separator}hpl_runtime"])
    
    # 添加入口文件
    cmd.append(launcher_path)
    
    print("执行命令:")
    print(" ".join(cmd))
    print()
    
    try:
        # 执行打包命令
        subprocess.check_call(cmd)
        print("\n打包成功!")
        
        # 显示输出路径
        dist_path = os.path.join(current_dir, "dist", "HPL.exe")
        if os.path.exists(dist_path):
            print(f"输出文件: {dist_path}")
            print(f"文件大小: {os.path.getsize(dist_path) / 1024 / 1024:.2f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        return False

def clean_build():
    """清理构建文件"""
    dirs_to_remove = ["build", "__pycache__"]
    files_to_remove = ["HPL.spec"]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"已删除: {dir_name}")
            except Exception as e:
                print(f"删除失败 {dir_name}: {e}")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"已删除: {file_name}")
            except Exception as e:
                print(f"删除失败 {file_name}: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("HPL启动器打包工具")
    print("=" * 50)
    print()
    
    # 检查PyInstaller
    if not check_pyinstaller():
        if not install_pyinstaller():
            print("无法继续，请手动安装PyInstaller")
            return 1
    
    # 构建exe
    if build_exe():
        # 询问是否清理
        print()
        response = input("是否清理构建临时文件? (y/n): ").strip().lower()
        if response == 'y':
            clean_build()
            print("清理完成")
        
        print()
        print("=" * 50)
        print("打包完成!")
        print("=" * 50)
        print()
        print("使用方法:")
        print("  1. 在dist目录中找到HPL.exe")
        print("  2. 将.hpl文件拖放到HPL.exe上运行")
        print("  3. 或在命令行中: HPL.exe <hpl_file>")
        print()
        print("提示: 可以将HPL.exe添加到系统PATH中")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
