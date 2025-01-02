import pytest
from FLAREcore.lexer import Lexer, Token, TokenType
from FLAREcore.parser import (
    Parser,
    BinaryExpr,
    LiteralExpr,
    UnaryExpr,
    FunctionStmt,
    IfStmt,
    ExpressionStmt,
    CallExpr,
)


def parse_source(source: str):
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    return parser.parse()


def test_simple_binary_expression():
    ast = parse_source("1 + 2")
    assert len(ast) == 1
    stmt = ast[0]
    assert isinstance(stmt, ExpressionStmt)
    expr = stmt.expression
    assert isinstance(expr, BinaryExpr)
    assert isinstance(expr.left, LiteralExpr)
    assert isinstance(expr.right, LiteralExpr)
    assert expr.left.value == 1
    assert expr.right.value == 2


def test_function_declaration():
    ast = parse_source(
        """
def factorial(n):
    return n
"""
    )
    assert len(ast) == 1
    func = ast[0]
    assert isinstance(func, FunctionStmt)
    assert func.name.lexeme == "factorial"
    assert len(func.params) == 1
    assert func.params[0].lexeme == "n"


def test_if_statement():
    ast = parse_source(
        """
if x:
    return 1
"""
    )
    assert len(ast) == 1
    stmt = ast[0]
    assert isinstance(stmt, IfStmt)


def test_complex_expression():
    ast = parse_source("1 + 2 * 3")
    assert len(ast) == 1
    stmt = ast[0]
    assert isinstance(stmt, ExpressionStmt)
    expr = stmt.expression
    assert isinstance(expr, BinaryExpr)
    assert isinstance(expr.right, BinaryExpr)  # 2 * 3 should be grouped
    assert isinstance(expr.left, LiteralExpr)  # 1
    assert expr.left.value == 1


def test_unary_expression():
    ast = parse_source("-42")
    assert len(ast) == 1
    stmt = ast[0]
    assert isinstance(stmt, ExpressionStmt)
    assert isinstance(stmt.expression, UnaryExpr)
    assert isinstance(stmt.expression.right, LiteralExpr)
    assert stmt.expression.right.value == 42


def test_function_call():
    ast = parse_source("factorial(5)")
    assert len(ast) == 1
    stmt = ast[0]
    assert isinstance(stmt, ExpressionStmt)
    expr = stmt.expression
    assert isinstance(expr, CallExpr)
    assert len(expr.arguments) == 1
    assert isinstance(expr.arguments[0], LiteralExpr)
    assert expr.arguments[0].value == 5


def test_error_recovery():
    """Test that parser can recover from syntax errors"""
    ast = parse_source(
        """
def good_function():
    return 1

def bad_function(
    return 2

def another_good_function():
    return 3
"""
    )
    # Should still parse the good functions
    assert len(ast) >= 2
    assert isinstance(ast[0], FunctionStmt)
    assert isinstance(ast[-1], FunctionStmt)
