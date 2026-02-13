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
    icon_path = os.path.join(current_dir, "HPL128.ico")
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
        # 基础模块
        "--hidden-import", "yaml",
        "--hidden-import", "platform",
        "--hidden-import", "difflib",
        "--hidden-import", "json",
        "--hidden-import", "logging",
        "--hidden-import", "pathlib",
        "--hidden-import", "importlib",
        "--hidden-import", "importlib.util",
        "--hidden-import", "subprocess",
        "--hidden-import", "shutil",
        "--hidden-import", "traceback",
        "--hidden-import", "re",
        "--hidden-import", "urllib",
        "--hidden-import", "urllib.request",
        "--hidden-import", "urllib.parse",
        "--hidden-import", "urllib.error",
        "--hidden-import", "http.client",
        "--hidden-import", "ssl",
        "--hidden-import", "hashlib",
        "--hidden-import", "base64",
        "--hidden-import", "secrets",
        "--hidden-import", "random",
        "--hidden-import", "string",
        "--hidden-import", "datetime",
        "--hidden-import", "time",
        "--hidden-import", "math",
        "--hidden-import", "os",
        "--hidden-import", "sys",
        "--hidden-import", "uuid",
        "--hidden-import", "hmac",
        # HPL运行时核心模块 - 确保打包后能找到
        "--hidden-import", "hpl_runtime",
        "--hidden-import", "hpl_runtime.core",
        "--hidden-import", "hpl_runtime.core.parser",
        "--hidden-import", "hpl_runtime.core.evaluator",
        "--hidden-import", "hpl_runtime.core.lexer",
        "--hidden-import", "hpl_runtime.core.models",
        "--hidden-import", "hpl_runtime.core.ast_parser",
        "--hidden-import", "hpl_runtime.utils.exceptions",
        "--hidden-import", "hpl_runtime.utils.error_handler",
        "--hidden-import", "hpl_runtime.utils.path_utils",
        "--hidden-import", "hpl_runtime.utils.io_utils",
        "--hidden-import", "hpl_runtime.utils.type_utils",
        "--hidden-import", "hpl_runtime.utils.text_utils",
        "--hidden-import", "hpl_runtime.utils.parse_utils",
        "--hidden-import", "hpl_runtime.modules.loader",
        "--hidden-import", "hpl_runtime.modules.base",
        "--hidden-import", "hpl_runtime.stdlib",
        "--hidden-import", "hpl_runtime.stdlib.io",
        "--hidden-import", "hpl_runtime.stdlib.math",
        "--hidden-import", "hpl_runtime.stdlib.string_mod",
        "--hidden-import", "hpl_runtime.stdlib.time_mod",
        "--hidden-import", "hpl_runtime.stdlib.random_mod",
        "--hidden-import", "hpl_runtime.stdlib.json_mod",
        "--hidden-import", "hpl_runtime.stdlib.os_mod",
        "--hidden-import", "hpl_runtime.stdlib.re_mod",
        "--hidden-import", "hpl_runtime.stdlib.net_mod",
        "--hidden-import", "hpl_runtime.stdlib.crypto_mod",
        # 排除不需要的模块
        "--exclude-module", "tests",
        "--exclude-module", "docs",
        "--exclude-module", "examples",
        "--exclude-module", "src",
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
    # 打印命令，但隐藏导入可以简化显示
    display_cmd = cmd.copy()
    print(" ".join(display_cmd[:15]) + " ... (更多参数)")
    print(f"总共 {len(cmd)} 个参数")
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
        print("调试模式:")
        print("  设置环境变量 HPL_DEBUG=1 可启用调试输出")
        print("  例如: set HPL_DEBUG=1 && HPL.exe example.hpl")
        print()
        print("提示: 可以将HPL.exe添加到系统PATH中")

        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
