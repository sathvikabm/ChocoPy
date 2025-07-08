# ===== File: run_tests.py =====
"""
Test runner for ChocoPy compiler
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.compiler import ChocoPyCompiler

def run_test(test_file: str):
    """Run a single test file"""
    print(f"\n{'='*50}")
    print(f"Testing: {test_file}")
    print('='*50)
    
    try:
        compiler = ChocoPyCompiler()
        
        # Read test file
        with open(test_file, 'r') as f:
            source = f.read()
        
        print("Source code:")
        print("-" * 30)
        print(source)
        print("-" * 30)
        
        # Compile
        assembly = compiler.compile_string(source)
        
        print("\nGenerated Assembly:")
        print("-" * 30)
        print(assembly[:500] + "..." if len(assembly) > 500 else assembly)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run all tests"""
    test_files = [
        "examples/basic.py",
        "examples/classes.py", 
        "examples/complex.py"
    ]
    
    passed = 0
    total = len(test_files)
    
    for test_file in test_files:
        if os.path.exists(test_file):
            if run_test(test_file):
                passed += 1
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} passed")
    print('='*50)

if __name__ == "__main__":
    main()