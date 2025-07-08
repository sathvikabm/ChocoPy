"""
Main ChocoPy Compiler Driver
"""

import sys
import os
from pathlib import Path
from lexer import ChocoPyLexer
from parser import ChocoPyParser
from type_checker import ChocoPyTypeChecker
from code_generator import CodeGenerator

class ChocoPyCompiler:
    def __init__(self):
        self.lexer = None
        self.parser = None
        self.type_checker = ChocoPyTypeChecker()
        self.code_generator = CodeGenerator()
        
    def compile_file(self, input_file: str, output_file: str = None):
        """Compile a ChocoPy file to RISC-V assembly"""
        try:
            # Read source file
            with open(input_file, 'r') as f:
                source_code = f.read()
            
            # Determine output file
            if output_file is None:
                base_name = Path(input_file).stem
                output_file = f"{base_name}.s"
            
            # Compile
            assembly = self.compile_string(source_code)
            
            # Write output
            with open(output_file, 'w') as f:
                f.write(assembly)
            
            print(f"Compilation successful!")
            print(f"Input:  {input_file}")
            print(f"Output: {output_file}")
            
        except FileNotFoundError:
            print(f" Error: File '{input_file}' not found")
            sys.exit(1)
        except Exception as e:
            print(f" Compilation failed: {e}")
            sys.exit(1)
    
    def compile_string(self, source_code: str) -> str:
        """Compile ChocoPy source code to RISC-V assembly"""
        print(" Starting compilation...")
        
        # Phase 1: Lexical Analysis
        print("1 Lexical Analysis...")
        self.lexer = ChocoPyLexer(source_code)
        tokens = self.lexer.tokenize()
        print(f"   Generated {len(tokens)} tokens")
        
        # Phase 2: Syntax Analysis
        print("2 Syntax Analysis...")
        self.parser = ChocoPyParser(tokens)
        ast = self.parser.parse()
        print(f"   AST created: {len(ast.declarations)} declarations, {len(ast.statements)} statements")
        
        # Phase 3: Semantic Analysis
        print("3 Semantic Analysis...")
        typed_ast = self.type_checker.check_program(ast)
        print("   Type checking completed")
        
        # Phase 4: Code Generation
        print("4 Code Generation...")
        assembly = self.code_generator.generate(typed_ast)
        print("   RISC-V assembly generated")
        
        return assembly

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python -m src.compiler <input_file> [output_file]")
        print("\nExample:")
        print("  python -m src.compiler examples/basic.py")
        print("  python -m src.compiler examples/basic.py output.s")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    compiler = ChocoPyCompiler()
    compiler.compile_file(input_file, output_file)

if __name__ == "__main__":
    main()
