#!/usr/bin/env python3
"""
HPL Runtime Local Package Installer

This script installs the HPL runtime package locally from built distributions,
without uploading to PyPI. Useful for testing before release.

Usage:
    python install_local.py              # Install from existing dist/
    python install_local.py --build      # Build first, then install
    python install_local.py --force      # Force reinstall
    python install_local.py --editable   # Editable/development mode
    python install_local.py --user       # Install to user site-packages

Requirements:
    pip (comes with Python)
    build (optional, for --build flag: pip install build)
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def get_package_info():
    """Extract package name and version from pyproject.toml."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # Python < 3.11
        except ImportError:
            # Fallback: simple parsing
            return _parse_pyproject_simple()
    
    try:
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
            project = config.get("project", {})
            name = project.get("name", "hpl-runtime")
            version = project.get("version", "unknown")
            return name, version
    except Exception:
        return _parse_pyproject_simple()


def _parse_pyproject_simple():
    """Simple fallback parser for pyproject.toml."""
    name = "hpl-runtime"
    version = "unknown"
    
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("name") and "=" in line:
                    name = line.split("=")[-1].strip().strip('"').strip("'")
                elif line.startswith("version") and "=" in line:
                    version = line.split("=")[-1].strip().strip('"').strip("'")
    except Exception:
        pass
    
    return name, version


def check_dist_directory():
    """Check if dist/ directory exists and has packages."""
    dist_path = Path("dist")
    
    if not dist_path.exists():
        return None, "dist/ directory not found"
    
    wheels = list(dist_path.glob("*.whl"))
    tarballs = list(dist_path.glob("*.tar.gz"))
    
    if not wheels and not tarballs:
        return None, "No distribution files found in dist/"
    
    files = sorted(wheels + tarballs, key=lambda p: p.stat().st_mtime, reverse=True)
    return files, None


def list_distributions():
    """List all available distribution files."""
    dist_path = Path("dist")
    
    if not dist_path.exists():
        return []
    
    files = []
    for file in sorted(dist_path.iterdir()):
        if file.suffix in (".whl", ".gz"):
            size = file.stat().st_size
            size_kb = size / 1024
            mtime = file.stat().st_mtime
            from datetime import datetime
            time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            files.append({
                "path": file,
                "name": file.name,
                "size_kb": size_kb,
                "modified": time_str,
                "is_wheel": file.suffix == ".whl"
            })
    
    return sorted(files, key=lambda x: x["path"].stat().st_mtime, reverse=True)


def build_package():
    """Build the package using build_package.py or python -m build."""
    print("🔨 Building package...")
    
    # Try build_package.py first (has better output)
    if Path("build_package.py").exists():
        try:
            result = subprocess.run(
                [sys.executable, "build_package.py"],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  build_package.py failed: {e.stderr}")
    
    # Fallback to python -m build
    try:
        result = subprocess.run(
            [sys.executable, "-m", "build"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Error: 'build' module not found.")
        print("   Install it with: pip install build")
        return False


def install_package(files, force=False, editable=False, user=False, 
                    wheel_only=False, no_deps=False, upgrade=False):
    """Install the package using pip."""
    
    if editable:
        print("📦 Installing in editable/development mode...")
        cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
    else:
        # Select file to install
        if wheel_only:
            wheels = [f for f in files if f.suffix == ".whl"]
            if wheels:
                target = wheels[0]
                print(f"📦 Installing wheel: {target.name}")
            else:
                print("⚠️  No wheel found, using source distribution")
                target = files[0]
        else:
            # Prefer wheel, but use whatever is available
            wheels = [f for f in files if f.suffix == ".whl"]
            if wheels:
                target = wheels[0]
                print(f"📦 Installing: {target.name}")
            else:
                target = files[0]
                print(f"📦 Installing source: {target.name}")
        
        cmd = [sys.executable, "-m", "pip", "install", str(target)]

    
    # Add flags
    if force or upgrade:
        cmd.append("--force-reinstall")
    if user:
        cmd.append("--user")
    if no_deps:
        cmd.append("--no-deps")
    
    print(f"   Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed with return code: {e.returncode}")
        return False


def verify_installation(package_name):
    """Verify that the package was installed correctly."""
    print("\n🔍 Verifying installation...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output
        info = {}
        for line in result.stdout.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                info[key.strip()] = value.strip()
        
        print(f"   ✓ Package: {info.get('Name', package_name)}")
        print(f"   ✓ Version: {info.get('Version', 'unknown')}")
        print(f"   ✓ Location: {info.get('Location', 'unknown')}")
        
        # Check if hpl command is available
        result = subprocess.run(
            [sys.executable, "-m", "hpl_runtime", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✓ CLI command 'hpl' is available")
        
        return True
        
    except subprocess.CalledProcessError:
        print(f"   ⚠️  Could not verify installation")
        return False


def uninstall_package(package_name):
    """Uninstall the package."""
    print(f"🗑️  Uninstalling {package_name}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"   ✓ {package_name} uninstalled")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Uninstall failed: {e.stderr}")
        return False


def main():
    """Main installation process."""
    parser = argparse.ArgumentParser(
        description="Install HPL Runtime locally from built distributions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install_local.py              # Install from existing dist/
  python install_local.py --build      # Build first, then install
  python install_local.py --force      # Force reinstall
  python install_local.py --editable   # Editable/development mode
  python install_local.py --user       # Install to user site-packages
  python install_local.py --list       # List available distributions
  python install_local.py --uninstall  # Uninstall the package
        """
    )
    
    parser.add_argument(
        "--build", "-b",
        action="store_true",
        help="Build package before installing"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force reinstall (same as --upgrade)"
    )
    parser.add_argument(
        "--upgrade", "-U",
        action="store_true",
        help="Upgrade/reinstall the package"
    )
    parser.add_argument(
        "--editable", "-e",
        action="store_true",
        help="Install in editable/development mode"
    )
    parser.add_argument(
        "--user", "-u",
        action="store_true",
        help="Install to user site-packages"
    )
    parser.add_argument(
        "--wheel-only", "-w",
        action="store_true",
        help="Install wheel only (faster, no build from source)"
    )
    parser.add_argument(
        "--no-deps",
        action="store_true",
        help="Skip installing dependencies"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available distributions and exit"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall the package"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Get package info
    package_name, version = get_package_info()
    
    print("=" * 60)
    print("HPL Runtime Local Package Installer")
    print("=" * 60)
    print(f"Package: {package_name}")
    print(f"Version: {version}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    print()
    
    # Handle list command
    if args.list:
        files = list_distributions()
        if files:
            print("📦 Available distributions:")
            print()
            for i, f in enumerate(files, 1):
                file_type = "wheel" if f["is_wheel"] else "source"
                print(f"  {i}. {f['name']}")
                print(f"     Type: {file_type}, Size: {f['size_kb']:.1f} KB")
                print(f"     Built: {f['modified']}")
                print()
        else:
            print("❌ No distributions found in dist/")
            print("   Run: python install_local.py --build")
        return
    
    # Handle uninstall command
    if args.uninstall:
        uninstall_package(package_name)
        return
    
    # Build if requested
    if args.build:
        if not build_package():
            print("❌ Build failed, aborting installation")
            sys.exit(1)
        print()
    
    # Check for distributions (skip if editable mode)
    if not args.editable:
        files, error = check_dist_directory()
        
        if error:
            print(f"❌ {error}")
            print()
            print("Options:")
            print("  1. Build first: python install_local.py --build")
            print("  2. Use editable mode: python install_local.py --editable")
            print("  3. Build manually: python build_package.py")
            sys.exit(1)
        
        # Show available files
        if args.verbose:
            print("📦 Available distributions:")
            for f in list_distributions():
                file_type = "wheel" if f["is_wheel"] else "source"
                print(f"   - {f['name']} ({file_type}, {f['size_kb']:.1f} KB)")
            print()
    else:
        files = []
    
    # Install
    if install_package(
        files,
        force=args.force,
        editable=args.editable,
        user=args.user,
        wheel_only=args.wheel_only,
        no_deps=args.no_deps,
        upgrade=args.upgrade
    ):
        print()
        print("=" * 60)
        print("✅ Installation successful!")
        print("=" * 60)
        
        # Verify
        verify_installation(package_name)
        
        print()
        print("Usage:")
        print("  hpl <file.hpl>     # Run HPL file")
        print("  hpl-run <file.hpl> # Alternative command")
        print("  python -m hpl_runtime <file.hpl>")
        print()
        
        if args.editable:
            print("Note: Editable mode installed. Changes to source code")
            print("      will be immediately available without reinstallation.")
        
    else:
        print()
        print("=" * 60)
        print("❌ Installation failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
