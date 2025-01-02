from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Dict

class TokenType(Enum):
    # Keywords
    DEF = auto()
    IF = auto()
    ELSE = auto()
    RETURN = auto()
    
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
        
        # Define keywords
        self.keywords: Dict[str, TokenType] = {
            "def": TokenType.DEF,
            "if": TokenType.IF,
            "else": TokenType.ELSE,
            "return": TokenType.RETURN,
        }

    def scan_tokens(self) -> List[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
            
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def scan_token(self):
        c = self.advance()
        
        match c:
            case '(': self.add_token(TokenType.LPAREN)
            case ')': self.add_token(TokenType.RPAREN)
            case '{': self.add_token(TokenType.LBRACE)
            case '}': self.add_token(TokenType.RBRACE)
            case ':': self.add_token(TokenType.COLON)
            case ',': self.add_token(TokenType.COMMA)
            case '+': self.add_token(TokenType.PLUS)
            case '-': self.add_token(TokenType.MINUS)
            case '*': self.add_token(TokenType.STAR)
            case '/': self.add_token(TokenType.SLASH)
            case '=': self.add_token(TokenType.EQUALS)
            case ' ' | '\r' | '\t': pass  # Ignore whitespace
            case '\n': self.line += 1
            case '"': self.string()
            case _:
                if self.is_digit(c):
                    self.number()
                elif self.is_alpha(c):
                    self.identifier()
                else:
                    self.add_token(TokenType.ERROR)

    def identifier(self):
        while not self.is_at_end() and self.is_alphanumeric(self.peek()):
            self.advance()

        text = self.source[self.start:self.current]
        type = self.keywords.get(text, TokenType.IDENTIFIER)
        self.add_token(type)

    def number(self):
        while not self.is_at_end() and self.is_digit(self.peek()):
            self.advance()

        # Look for fractional part
        if not self.is_at_end() and self.peek() == '.' and self.is_digit(self.peek_next()):
            # Consume the "."
            self.advance()

            while not self.is_at_end() and self.is_digit(self.peek()):
                self.advance()

            self.add_token(TokenType.FLOAT, float(self.source[self.start:self.current]))
        else:
            self.add_token(TokenType.INTEGER, int(self.source[self.start:self.current]))

    def string(self):
        while not self.is_at_end() and self.peek() != '"':
            if self.peek() == '\n':
                self.line += 1
            self.advance()

        if self.is_at_end():
            # Unterminated string
            self.add_token(TokenType.ERROR)
            return

        # The closing "
        self.advance()

        # Trim the surrounding quotes
        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING, value)

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        self.current += 1
        return self.source[self.current - 1]

    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def add_token(self, type: TokenType, literal: Optional[object] = None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type, text, literal, self.line))

    @staticmethod
    def is_digit(c: str) -> bool:
        return c.isdigit()

    @staticmethod
    def is_alpha(c: str) -> bool:
        return c.isalpha() or c == '_'

    def is_alphanumeric(self, c: str) -> bool:
        return self.is_alpha(c) or self.is_digit(c)