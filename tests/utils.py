import sys
import os
import subprocess
import tempfile
import shutil
import glob

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "build"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from antlr4 import *
from build.OPLangLexer import OPLangLexer
from build.OPLangParser import OPLangParser
from src.utils.error_listener import NewErrorListener
from src.astgen.ast_generation import ASTGeneration
from src.semantics.static_checker import StaticChecker
from src.utils.nodes import *


class Tokenizer:
    def __init__(self, input_string):
        self.input_stream = InputStream(input_string)
        self.lexer = OPLangLexer(self.input_stream)

    def get_tokens(self):
        tokens = []
        token = self.lexer.nextToken()
        while token.type != Token.EOF:
            tokens.append(token.text)
            try:
                token = self.lexer.nextToken()
            except Exception as e:
                tokens.append(str(e))
                return tokens
        return tokens + ["EOF"]

    def get_tokens_as_string(self):
        tokens = []
        try:
            while True:
                token = self.lexer.nextToken()
                if token.type == Token.EOF:
                    tokens.append("EOF")
                    break
                tokens.append(token.text)
        except Exception as e:
            if tokens:  # If we already have some tokens, append error
                tokens.append(str(e))
            else:  # If no tokens yet, just return error
                return str(e)
        return ",".join(tokens)


class Parser:
    def __init__(self, input_string):
        self.input_stream = InputStream(input_string)
        self.lexer = OPLangLexer(self.input_stream)
        self.token_stream = CommonTokenStream(self.lexer)
        self.parser = OPLangParser(self.token_stream)
        self.parser.removeErrorListeners()
        self.parser.addErrorListener(NewErrorListener.INSTANCE)

    def parse(self):
        try:
            self.parser.program()  # Assuming 'program' is the entry point of your grammar
            return "success"
        except Exception as e:
            return str(e)


class ASTGenerator:
    """Class to generate AST from OPLang source code."""

    def __init__(self, input_string):
        self.input_string = input_string
        self.input_stream = InputStream(input_string)
        self.lexer = OPLangLexer(self.input_stream)
        self.token_stream = CommonTokenStream(self.lexer)
        self.parser = OPLangParser(self.token_stream)
        self.ast_generator = ASTGeneration()

    def generate(self):
        """Generate AST from the input string."""
        try:
            # Parse the program starting from the entry point
            parse_tree = self.parser.program()

            # Generate AST using the visitor
            ast = self.ast_generator.visit(parse_tree)
            return ast
        except Exception as e:
            return f"AST Generation Error: {str(e)}"


class Checker:
    """Class to perform static checking on the AST."""

    def __init__(self, source=None, ast=None):
        self.source = source
        self.ast = ast
        self.checker = StaticChecker()

    def check_from_ast(self):
        """Perform static checking on the AST."""
        try:
            self.checker.check_program(self.ast)
            return "Static checking passed"
        except Exception as e:
            return str(e)

    def check_from_source(self):
        """Perform static checking on the source code."""
        try:
            ast_gen = ASTGenerator(self.source)
            self.ast = ast_gen.generate()
            if isinstance(self.ast, str):  # If AST generation failed
                return self.ast
            self.checker.check_program(self.ast)
            return "Static checking passed"
        except Exception as e:
            return str(e)


class CodeGenerator:
    """Class to generate and run code from AST."""

    def __init__(self):
        from src.codegen.codegen import CodeGenerator as CodeGen
        self.codegen = CodeGen()
        self.runtime_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "runtime")

    def generate_and_run(self, ast):
        """Generate code from AST and run it, return output"""
        try:
            # --- THÊM ĐOẠN NÀY ĐỂ DỌN DẸP ---
            # Xóa sạch các file .j và .class cũ trước khi chạy test mới
            for filename in os.listdir(self.runtime_dir):
                file_path = os.path.join(self.runtime_dir, filename)
                # Chỉ xóa file .j và .class, TRỪ io.class (thư viện)
                if filename.endswith(".j") or (filename.endswith(".class") and filename != "io.class"):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
            # -------------------------------

            # Change to runtime directory and generate code from AST
            original_dir = os.getcwd()
            os.chdir(self.runtime_dir)
            try:
                self.codegen.visit(ast)
            finally:
                os.chdir(original_dir)

            # Find all generated .j files
            j_files = glob.glob(os.path.join(self.runtime_dir, "*.j"))

            if not j_files:
                return "Error: No .j files generated"

            # Assemble all .j files to .class
            try:
                for j_file in j_files:
                    result = subprocess.run(
                        ["java", "-jar", "jasmin.jar", os.path.basename(j_file)],
                        cwd=self.runtime_dir,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if result.returncode != 0:
                        return f"Assembly error for {os.path.basename(j_file)}: {result.stderr}"

                # Find the class with main method
                # In OPLang, any class can have a static main() method
                class_files = glob.glob(os.path.join(self.runtime_dir, "*.class"))
                main_class = None

                # Try to find a class with main method
                # For now, try running the first class found, or look for a specific pattern
                # This is a simplified approach - in practice, you might need to check which class has main
                if class_files:
                    # Try to find main class by checking class files
                    # For simplicity, we'll try the first class file
                    # In a real implementation, you might need to inspect the class files
                    # or maintain a list of classes with main methods

                    # Get class name from .class file (remove .class extension)
                    for class_file in class_files:
                        class_name = os.path.basename(class_file).replace(".class", "")
                        # Skip io.class
                        if class_name == "io":
                            continue
                        main_class = class_name
                        break

                if not main_class:
                    return "Error: No main class found"

                # Run program
                result = subprocess.run(
                    ["java", main_class],
                    cwd=self.runtime_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode != 0:
                    return f"Runtime error: {result.stderr}"

                return result.stdout.strip()

            except subprocess.TimeoutExpired:
                return "Timeout"
            except FileNotFoundError:
                return "Java not found"

        except Exception as e:
            return f"Code generation error: {str(e)}"
