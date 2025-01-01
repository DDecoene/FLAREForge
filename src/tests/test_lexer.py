import pytest
from prism.lexer import Lexer, Token, TokenType

def test_empty_source():
    lexer = Lexer("")
    tokens = lexer.scan_tokens()
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF
