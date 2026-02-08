#!/usr/bin/env python3
"""
HPL Runtime PyPI Upload Script

This script uploads the HPL runtime package to PyPI or TestPyPI.

Usage:
    python upload_to_pypi.py           # Upload to production PyPI
    python upload_to_pypi.py --test    # Upload to TestPyPI (recommended first)

Requirements:
    pip install twine
    
Setup:
    1. Create PyPI account at https://pypi.org/account/register/
    2. Create API token at https://pypi.org/manage/account/token/
    3. Configure ~/.pypirc or use environment variables
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def check_distributions():
    """Check if distribution files exist."""
    dist_path = Path("dist")
    
    if not dist_path.exists():
        print("❌ Error: dist/ directory not found!")
        print("   Run 'python build_package.py' first to build the package.")
        return False
    
    files = list(dist_path.iterdir())
    if not files:
        print("❌ Error: No distribution files found in dist/")
        print("   Run 'python build_package.py' first to build the package.")
        return False
    
    print("📦 Found distribution files:")
    for f in files:
        print(f"   - {f.name}")
    print()
    return True


def upload_to_pypi(test=False):
    """Upload package to PyPI or TestPyPI."""
    repository = "testpypi" if test else "pypi"
    
    if test:
        print("🧪 Uploading to TestPyPI (testing environment)...")
        print("   URL: https://test.pypi.org/project/hpl-runtime/")
    else:
        print("🚀 Uploading to PyPI (production)...")
        print("   URL: https://pypi.org/project/hpl-runtime/")
    
    print()
    
    # Build command
    cmd = [sys.executable, "-m", "twine", "upload", "--disable-progress-bar"]
    if test:
        cmd.extend(["--repository", "testpypi"])
    cmd.append("dist/*")
    
    try:
        # Use interactive mode to allow password prompt
        result = subprocess.run(cmd, check=True)
        
        if test:
            print("✅ Successfully uploaded to TestPyPI!")
            print()
            print("Test installation:")
            print("  pip install --index-url https://test.pypi.org/simple/ hpl-runtime")
        else:
            print("✅ Successfully uploaded to PyPI!")
            print()
            print("Installation:")
            print("  pip install hpl-runtime")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Upload failed with return code: {e.returncode}")
        print()
        
        if test:
            print("🔐 TestPyPI Authentication Issue:")
            print()
            print("TestPyPI and PyPI are SEPARATE servers with different accounts!")
            print()
            print("To fix this, you need to:")
            print()
            print("1. Create a TestPyPI account at https://test.pypi.org/account/register/")
            print("2. Create a TestPyPI API token at https://test.pypi.org/manage/account/token/")
            print("3. Use one of these methods:")
            print()
            print("   Method A - Environment variables:")
            print("     set TWINE_USERNAME=__token__")
            print("     set TWINE_PASSWORD=pypi-your-testpypi-token-here")
            print()
            print("   Method B - .pypirc file with [testpypi] section:")
            print("     [testpypi]")
            print("     repository = https://test.pypi.org/legacy/")
            print("     username = __token__")
            print("     password = pypi-your-testpypi-token-here")
        else:
            print("🔐 PyPI Authentication Issue:")
            print()
            print("To fix this, you need to:")
            print()
            print("1. Create a PyPI account at https://pypi.org/account/register/")
            print("2. Create a PyPI API token at https://pypi.org/manage/account/token/")
            print("3. Use one of these methods:")
            print()
            print("   Method A - Environment variables:")
            print("     set TWINE_USERNAME=__token__")
            print("     password = pypi-your-pypi-token-here")
            print()
            print("   Method B - .pypirc file with [pypi] section:")
            print("     [pypi]")
            print("     username = __token__")
            print("     password = pypi-your-pypi-token-here")
        
        print()
        print("For detailed instructions, run:")
        print("  python upload_to_pypi.py --instructions")
        
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return False


def show_instructions():
    """Show detailed setup instructions."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    PyPI Upload Instructions                       ║
╚══════════════════════════════════════════════════════════════════╝

📋 Prerequisites:

1. Create PyPI Account:
   - Go to https://pypi.org/account/register/
   - Verify your email address

2. Create API Token:
   - Go to https://pypi.org/manage/account/token/
   - Click "Add API token"
   - Name: "hpl-runtime-upload"
   - Scope: "Entire account" or project-specific
   - Copy the token (starts with 'pypi-')

3. Configure Credentials (choose one method):

   Method A - Environment Variables (Recommended for CI/CD):
   
     set TWINE_USERNAME=__token__
     set TWINE_PASSWORD=pypi-your-api-token-here
   
   Method B - %USERPROFILE%\\.pypirc file:
   
     [distutils]
     index-servers = pypi testpypi
     
     [pypi]
     username = __token__
     password = pypi-your-pypi-token-here
     
     [testpypi]
     repository = https://test.pypi.org/legacy/
     username = __token__
     password = pypi-your-testpypi-token-here

🚀 Upload Process:

1. Build the package:
   
     python build_package.py

2. Test upload to TestPyPI first:
   
     python upload_to_pypi.py --test
   
   Then verify:
   
     pip install --index-url https://test.pypi.org/simple/ hpl-runtime

3. Upload to production PyPI:
   
     python upload_to_pypi.py

4. Verify on PyPI:
   
   Visit: https://pypi.org/project/hpl-runtime/

⚠️  Important Notes:

- TestPyPI and PyPI are SEPARATE servers with different accounts!
  You need to create accounts and API tokens on BOTH sites.

- Version numbers cannot be reused! Once uploaded, you cannot
  upload the same version again. Bump version in pyproject.toml
  and hpl_runtime/__init__.py if needed.

- Always test on TestPyPI before uploading to production PyPI.

═══════════════════════════════════════════════════════════════════
""")


def main():
    """Main upload process."""
    parser = argparse.ArgumentParser(
        description="Upload HPL Runtime to PyPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upload_to_pypi.py --help      Show this help message
  python upload_to_pypi.py --instructions  Show detailed setup instructions
  python upload_to_pypi.py --test        Upload to TestPyPI
  python upload_to_pypi.py               Upload to production PyPI
        """
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Upload to TestPyPI instead of production PyPI"
    )
    parser.add_argument(
        "--instructions",
        action="store_true",
        help="Show detailed setup instructions"
    )
    
    args = parser.parse_args()
    
    if args.instructions:
        show_instructions()
        return
    
    print("=" * 70)
    print("HPL Runtime PyPI Uploader")
    print("=" * 70)
    print()
    
    # Check for distributions
    if not check_distributions():
        sys.exit(1)
    
    # Confirm upload
    if args.test:
        print("⚠️  You are about to upload to TestPyPI (testing environment)")
    else:
        print("⚠️  You are about to upload to PRODUCTION PyPI")
        print("   This cannot be undone! Version numbers cannot be reused.")
    
    print()
    response = input("Continue? [y/N]: ").strip().lower()
    
    if response not in ('y', 'yes'):
        print("Upload cancelled.")
        sys.exit(0)
    
    print()
    
    # Perform upload
    if upload_to_pypi(test=args.test):
        print()
        print("=" * 70)
        print("Upload complete! 🎉")
        print("=" * 70)
    else:
        print()
        print("=" * 70)
        print("Upload failed. See errors above.")
        print("=" * 70)
        print()
        print("Need help? Run: python upload_to_pypi.py --instructions")
        sys.exit(1)


if __name__ == "__main__":
    main()
