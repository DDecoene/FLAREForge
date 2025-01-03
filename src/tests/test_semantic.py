from FLAREcore.lexer import Lexer
from FLAREcore.parser import Parser
from FLAREcore.semantic import SemanticAnalyzer

def analyze_source(source: str):
    # Helper function to create tokens and AST
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Analyze semantics
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(ast)

def test_undefined_variable():
    # Should error when variable used before definition
    errors = analyze_source("x = 42")
    assert len(errors) == 1
    assert "Undefined variable 'x'" in errors[0].message

def test_function_scope():
    # Variables in function should be contained in function scope
    errors = analyze_source("""
    def test(x):
        y = x
        return y
    """)
    assert len(errors) == 0

def test_nested_scope():
    # Inner functions should access outer variables
    errors = analyze_source("""
    def outer(x):
        def inner(y):
            return x + y
        return inner(x)
    """)
    assert len(errors) == 0

def test_variable_shadowing():
    # Inner scope can redefine outer names
    errors = analyze_source("""
    def test(x):
        x = 42
        return x
    """)
    assert len(errors) == 0

def test_undefined_function_call():
    # Should error on calling undefined function
    errors = analyze_source("undefined_func()")
    assert len(errors) == 1
    assert "Undefined variable 'undefined_func'" in errors[0].message

def test_if_statement_scope():
    # Variable defined in if block might not be defined on all paths
    errors = analyze_source("""
    def test(x):
        if x:
            y = 42
        return y  # Error: y might not be defined
    """)
    assert len(errors) == 1
    assert "Undefined variable 'y'" in errors[0].message

def test_multiple_function_definitions():
    # Multiple function definitions are allowed
    errors = analyze_source("""
    def func1(): pass
    def func2(): pass
    def func1(): pass
    """)
    assert len(errors) == 0

def test_complex_nested_scopes():
    # Test complex nesting of functions and scopes
    errors = analyze_source("""
    def outer(x):
        def middle(y):
            def inner(z):
                return x + y + z
            return inner
        return middle(x)(x)
    """)
    assert len(errors) == 0