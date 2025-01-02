from dataclasses import dataclass
from typing import List, Optional

from .lexer import Token, TokenType


# AST Node definitions
@dataclass
class Expression:
    pass


@dataclass
class Statement:
    pass


@dataclass
class BinaryExpr(Expression):
    left: Expression
    operator: Token
    right: Expression


@dataclass
class LiteralExpr(Expression):
    value: object


@dataclass
class UnaryExpr(Expression):
    operator: Token
    right: Expression


@dataclass
class GroupingExpr(Expression):
    expression: Expression


@dataclass
class VariableExpr(Expression):
    name: Token


@dataclass
class CallExpr(Expression):
    callee: Expression
    paren: Token
    arguments: List[Expression]


@dataclass
class AssignExpr(Expression):
    name: Token
    value: Expression


@dataclass
class FunctionStmt(Statement):
    name: Token
    params: List[Token]
    body: List[Statement]


@dataclass
class ReturnStmt(Statement):
    keyword: Token
    value: Optional[Expression]


@dataclass
class IfStmt(Statement):
    condition: Expression
    then_branch: Statement
    else_branch: Optional[Statement]


@dataclass
class ExpressionStmt(Statement):
    expression: Expression


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> List[Statement]:
        statements = []
        while not self.is_at_end():
            try:
                statement = self.declaration()
                if statement:
                    statements.append(statement)
            except ParseError as e:
                print(f"Parse error: {e}")
                self.synchronize()
        return statements

    def declaration(self) -> Optional[Statement]:
        # Skip any whitespace tokens at the start
        while self.match(TokenType.EOF):
            pass

        # Now look for a function declaration
        if self.check(TokenType.DEF):
            return self.function_declaration()
        return self.statement()

    def function_declaration(self) -> FunctionStmt:
        self.consume(TokenType.DEF, "Expected 'def' keyword")
        name = self.consume(TokenType.IDENTIFIER, "Expect function name")

        self.consume(TokenType.LPAREN, "Expect '(' after function name")
        parameters = []

        # Parse parameters
        if not self.check(TokenType.RPAREN):
            while True:
                parameters.append(
                    self.consume(TokenType.IDENTIFIER, "Expect parameter name")
                )
                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RPAREN, "Expect ')' after parameters")
        self.consume(TokenType.COLON, "Expect ':' after function declaration")

        # Parse function body
        body = []
        while not self.is_at_end() and not self.check(TokenType.DEF):
            stmt = self.statement()
            if stmt:
                body.append(stmt)

        return FunctionStmt(name, parameters, body)

    def statement(self) -> Statement:
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        return self.expression_statement()

    def if_statement(self) -> Statement:
        condition = self.expression()
        self.consume(TokenType.COLON, "Expect ':' after if condition")

        then_branch = self.statement()
        else_branch = None

        if self.match(TokenType.ELSE):
            self.consume(TokenType.COLON, "Expect ':' after else")
            else_branch = self.statement()

        return IfStmt(condition, then_branch, else_branch)

    def return_statement(self) -> Statement:
        keyword = self.previous()
        value = None

        if not self.is_at_end():
            value = self.expression()

        return ReturnStmt(keyword, value)

    def expression_statement(self) -> Statement:
        expr = self.expression()
        return ExpressionStmt(expr)

    def expression(self) -> Expression:
        return self.equality()

    def equality(self) -> Expression:
        expr = self.term()

        while self.match(TokenType.EQUALS):
            operator = self.previous()
            right = self.term()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def term(self) -> Expression:
        expr = self.factor()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.factor()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def factor(self) -> Expression:
        expr = self.unary()

        while self.match(TokenType.STAR, TokenType.SLASH):
            operator = self.previous()
            right = self.unary()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def unary(self) -> Expression:
        if self.match(TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return UnaryExpr(operator, right)

        return self.primary()

    def primary(self) -> Expression:
        if self.match(TokenType.INTEGER, TokenType.FLOAT, TokenType.STRING):
            return LiteralExpr(self.previous().literal)

        if self.match(TokenType.IDENTIFIER):
            expr = VariableExpr(self.previous())
            if self.match(TokenType.LPAREN):
                arguments = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        arguments.append(self.expression())
                        if not self.match(TokenType.COMMA):
                            break
                paren = self.consume(TokenType.RPAREN, "Expect ')' after arguments")
                return CallExpr(expr, paren, arguments)
            return expr

        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expect ')' after expression")
            return GroupingExpr(expr)

    def match(self, *types: TokenType) -> bool:
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def check(self, type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def consume(self, type: TokenType, message: str) -> Token:
        if self.check(type):
            return self.advance()
        raise self.error(self.peek(), message)

    def error(self, token: Token, message: str) -> ParseError:
        return ParseError(f"Error at '{token.lexeme}': {message}")

    def synchronize(self):
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.COLON:
                return

            if self.peek().type in {
                TokenType.DEF,
                TokenType.IF,
                TokenType.RETURN,
            }:
                return

            self.advance()
