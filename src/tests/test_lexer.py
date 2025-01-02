import pytest
from FLAREcore.lexer import Lexer, Token, TokenType

def test_empty_source():
    lexer = Lexer("")
    tokens = lexer.scan_tokens()
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF

def test_basic_tokens():
    source = "def main():"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    
    expected = [
        Token(TokenType.DEF, "def", None, 1),
        Token(TokenType.IDENTIFIER, "main", None, 1),
        Token(TokenType.LPAREN, "(", None, 1),
        Token(TokenType.RPAREN, ")", None, 1),
        Token(TokenType.COLON, ":", None, 1),
        Token(TokenType.EOF, "", None, 1),
    ]
    
    assert len(tokens) == len(expected)
    for actual, expected in zip(tokens, expected):
        assert actual.type == expected.type
        assert actual.lexeme == expected.lexeme

def test_simple_expression():
    source = "x = 42 + y"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    
    expected = [
        Token(TokenType.IDENTIFIER, "x", None, 1),
        Token(TokenType.EQUALS, "=", None, 1),
        Token(TokenType.INTEGER, "42", 42, 1),
        Token(TokenType.PLUS, "+", None, 1),
        Token(TokenType.IDENTIFIER, "y", None, 1),
        Token(TokenType.EOF, "", None, 1),
    ]
    
    assert len(tokens) == len(expected)
    for actual, expected in zip(tokens, expected):
        assert actual.type == expected.type
        assert actual.lexeme == expected.lexeme

def test_multiline_input():
    source = """
    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)
    """
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    
    # Verify we got some basic tokens we expect
    token_types = [token.type for token in tokens]
    assert TokenType.DEF in token_types
    assert TokenType.IDENTIFIER in token_types
    assert TokenType.LPAREN in token_types
    assert TokenType.RPAREN in token_types
    assert TokenType.COLON in token_types
    
    # Verify line numbers are tracked
    line_numbers = set(token.line for token in tokens)
    assert len(line_numbers) > 1  # Should have multiple lines

def test_invalid_character():
    source = "x = @"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    
    # Check that we got an error token
    assert any(token.type == TokenType.ERROR for token in tokens)
