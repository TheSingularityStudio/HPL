"""
HPL Runtime module entry point

Allows running HPL files via: python -m hpl_runtime <file.hpl>
"""

from hpl_runtime.interpreter import main

if __name__ == "__main__":
    main()
