#!/usr/bin/env python3
"""
Script to run the HPL interpreter on the example file.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from interpreter import main as interpreter_main

if __name__ == "__main__":
    # Run on the example file
    sys.argv = ['interpreter.py', 'examples/example.hpl']
    interpreter_main()
