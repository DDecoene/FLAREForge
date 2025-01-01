from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

class TokenType(Enum):
    # Keywords
    DEF = auto()
    CLASS = auto()
    IF = auto()
    ELSE = auto()
    RETURN = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    
    # Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQUALS = auto()
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COLON = auto()
    COMMA = auto()
    
    # Special
    EOF = auto()
    ERROR = auto()

@dataclass
class Token:
    type: TokenType
    lexeme: str
    literal: Optional[object]
    line: int

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> List[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)
