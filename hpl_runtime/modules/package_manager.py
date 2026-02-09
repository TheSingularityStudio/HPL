"""
HPL 包管理器

提供命令行工具管理 HPL 第三方包：
- hpl install <package>     安装包
- hpl uninstall <package>   卸载包
- hpl list                  列出已安装包
- hpl search <query>        搜索 PyPI 包
- hpl update                更新所有包
"""

import sys
import argparse
import subprocess
from pathlib import Path

# 导入模块加载器中的包管理功能
try:
    from hpl_runtime.modules.loader import (
        install_package, 
        uninstall_package, 
        list_installed_packages,
        HPL_PACKAGES_DIR,
        add_module_path
    )
except ImportError:
    from hpl_runtime.modules.loader import (
        install_package, 
        uninstall_package, 
        list_installed_packages,
        HPL_PACKAGES_DIR,
        add_module_path
    )


def cmd_install(args):
    """安装包"""
    package_name = args.package
    version = args.version
    
    print(f"📦 Installing '{package_name}'...")
    success = install_package(package_name, version)
    
    if success:
        print(f"\n✅ Package '{package_name}' installed successfully!")
        print(f"   Location: {HPL_PACKAGES_DIR / package_name}")
        print(f"\n   Usage in HPL:")
        print(f"   imports:")
        print(f"     - {package_name.split('[')[0].split('==')[0].split('>=')[0]}")
    else:
        print(f"\n❌ Failed to install '{package_name}'")
        sys.exit(1)


def cmd_uninstall(args):
    """卸载包"""
    package_name = args.package
    
    print(f"🗑️  Uninstalling '{package_name}'...")
    success = uninstall_package(package_name)
    
    if success:
        print(f"\n✅ Package '{package_name}' uninstalled successfully!")
    else:
        print(f"\n❌ Failed to uninstall '{package_name}'")
        sys.exit(1)


def cmd_list(args):
    """列出已安装包"""
    packages = list_installed_packages()
    
    print("📦 Installed HPL Packages:")
    print("=" * 50)
    
    if not packages:
        print("   No packages installed.")
    else:
        for i, pkg in enumerate(packages, 1):
            print(f"   {i}. {pkg}")
    
    print("=" * 50)
    print(f"   Total: {len(packages)} packages")
    print(f"   Package directory: {HPL_PACKAGES_DIR}")


def cmd_search(args):
    """搜索 PyPI 包"""
    query = args.query
    
    print(f"🔍 Searching for '{query}' on PyPI...")
    
    try:
        # 使用 pip search 或 pip index
        cmd = [sys.executable, "-m", "pip", "search", query]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            # pip search 可能被禁用，尝试使用 pip index
            cmd = [sys.executable, "-m", "pip", "index", "versions", query]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
            else:
                print("⚠️  Search failed. You can manually search at:")
                print(f"   https://pypi.org/search/?q={query}")
                
    except Exception as e:
        print(f"❌ Search error: {e}")
        print(f"   You can manually search at: https://pypi.org/search/?q={query}")


def cmd_update(args):
    """更新所有包"""
    print("🔄 Updating all packages...")
    
    packages = list_installed_packages()
    
    if not packages:
        print("   No packages to update.")
        return
    
    updated = 0
    failed = 0
    
    for pkg in packages:
        print(f"\n   Updating {pkg}...")
        # 尝试重新安装最新版本
        success = install_package(pkg)
        if success:
            updated += 1
        else:
            failed += 1
    
    print(f"\n{'=' * 50}")
    print(f"✅ Updated: {updated}")
    if failed > 0:
        print(f"❌ Failed: {failed}")


def cmd_info(args):
    """显示包信息"""
    package_name = args.package
    
    print(f"ℹ️  Package information for '{package_name}':")
    print("=" * 50)
    
    # 检查是否已安装
    packages = list_installed_packages()
    if package_name in packages:
        print(f"   Status: ✅ Installed")
        pkg_path = HPL_PACKAGES_DIR / package_name
        print(f"   Location: {pkg_path}")
        
        # 显示包内容
        if pkg_path.is_dir():
            files = list(pkg_path.iterdir())[:10]  # 最多显示10个
            print(f"   Contents:")
            for f in files:
                print(f"      - {f.name}")
            if len(list(pkg_path.iterdir())) > 10:
                print(f"      ... and more")
    else:
        print(f"   Status: ❌ Not installed")
        print(f"   Install with: hpl install {package_name}")


def cmd_path(args):
    """管理模块搜索路径"""
    if args.add:
        add_module_path(args.add)
        print(f"✅ Added module path: {args.add}")
    elif args.list:
        from hpl_runtime.modules.loader import HPL_MODULE_PATHS
        print("📂 Module Search Paths:")
        print("=" * 50)
        for i, path in enumerate(HPL_MODULE_PATHS, 1):
            exists = "✅" if Path(path).exists() else "❌"
            print(f"   {i}. {exists} {path}")
    else:
        print("Usage:")
        print("   hpl path --add <path>     Add a module search path")
        print("   hpl path --list           List all search paths")


def main():
    """主入口点"""
    parser = argparse.ArgumentParser(
        description="HPL Package Manager - Manage third-party packages for HPL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hpl install requests              Install 'requests' package
  hpl install numpy==1.24.0       Install specific version
  hpl uninstall requests          Remove 'requests' package
  hpl list                        Show installed packages
  hpl search http                 Search PyPI for packages
  hpl update                      Update all packages
  hpl info requests               Show package details
  hpl path --add ./my_modules     Add custom module path

For more help: https://github.com/yourusername/hpl
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # install 命令
    install_parser = subparsers.add_parser('install', help='Install a package')
    install_parser.add_argument('package', help='Package name (e.g., requests, numpy==1.24.0)')
    install_parser.add_argument('--version', '-v', help='Specific version to install')
    install_parser.set_defaults(func=cmd_install)
    
    # uninstall 命令
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall a package')
    uninstall_parser.add_argument('package', help='Package name to uninstall')
    uninstall_parser.set_defaults(func=cmd_uninstall)
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='List installed packages')
    list_parser.set_defaults(func=cmd_list)
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='Search for packages on PyPI')
    search_parser.add_argument('query', help='Search query')
    search_parser.set_defaults(func=cmd_search)
    
    # update 命令
    update_parser = subparsers.add_parser('update', help='Update all packages')
    update_parser.set_defaults(func=cmd_update)
    
    # info 命令
    info_parser = subparsers.add_parser('info', help='Show package information')
    info_parser.add_argument('package', help='Package name')
    info_parser.set_defaults(func=cmd_info)
    
    # path 命令
    path_parser = subparsers.add_parser('path', help='Manage module search paths')
    path_parser.add_argument('--add', help='Add a search path')
    path_parser.add_argument('--list', action='store_true', help='List all paths')
    path_parser.set_defaults(func=cmd_path)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # 执行命令
    args.func(args)


if __name__ == '__main__':
    main()
