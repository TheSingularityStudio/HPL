#!/usr/bin/env python3
"""
HPL Runtime Package Builder

This script builds the HPL runtime package for PyPI distribution.
It creates both wheel (.whl) and source distribution (.tar.gz) files.

Usage:
    python build_package.py

Requirements:
    pip install build twine
"""

import subprocess
import sys
import shutil
import os
from pathlib import Path


def clean_dist():
    """Clean previous build artifacts."""
    print("🧹 Cleaning previous builds...")
    
    # Remove dist directory
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        print("   ✓ Removed dist/ directory")
    
    # Remove build directory
    if os.path.exists("build"):
        shutil.rmtree("build")
        print("   ✓ Removed build/ directory")
    
    # Remove egg-info directories
    for egg_info in Path(".").glob("*.egg-info"):
        shutil.rmtree(egg_info)
        print(f"   ✓ Removed {egg_info}/")
    
    print("✅ Clean complete\n")


def build_package():
    """Build the package using python-build."""
    print("🔨 Building package...")
    print("   - Generating wheel distribution")
    print("   - Generating source distribution")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "build"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✅ Build successful!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Error: 'build' module not found.")
        print("   Install it with: pip install build")
        return False


def check_package():
    """Check the package with twine."""
    print("🔍 Checking package with twine...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "twine", "check", "dist/*"],
            capture_output=True,
            text=True,
            check=True
        )


        print(result.stdout)
        print("✅ Package check passed!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Package check warnings/errors:\n{e.stdout}\n{e.stderr}")
        return False


def list_distributions():
    """List the generated distribution files."""
    print("📦 Generated distributions:")
    
    dist_path = Path("dist")
    if dist_path.exists():
        for file in sorted(dist_path.iterdir()):
            size = file.stat().st_size
            size_kb = size / 1024
            print(f"   - {file.name} ({size_kb:.1f} KB)")
    print()


def main():
    """Main build process."""
    print("=" * 60)
    print("HPL Runtime Package Builder")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"Python version: {sys.version}")
    print()
    
    # Clean previous builds
    clean_dist()
    
    # Build package
    if not build_package():
        sys.exit(1)
    
    # Check package
    check_package()
    
    # List distributions
    list_distributions()
    
    print("=" * 60)
    print("Build complete! 🎉")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Test upload to TestPyPI:")
    print("     python upload_to_pypi.py --test")
    print()
    print("  2. Upload to PyPI:")
    print("     python upload_to_pypi.py")
    print()
    print("  3. Install locally:")
    print("     pip install dist/hpl_runtime-1.0.0-py3-none-any.whl")
    print()


if __name__ == "__main__":
    main()
