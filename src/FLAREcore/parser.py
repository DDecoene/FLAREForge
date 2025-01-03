from typing import List, Optional
from .lexer import Token, TokenType
from .ast import (
    Expression, Statement, FunctionStmt, IfStmt,
    ReturnStmt, ExpressionStmt, VariableExpr, CallExpr,
    AssignExpr, BinaryExpr, LiteralExpr, GroupingExpr,
    UnaryExpr, TypeHintExpr, GenericTypeExpr, MultiAssignExpr,
    PatternMatchStmt, PatternCase, ActorStmt, WithStmt,
    ForStmt
)

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

        # Check for decorators
        if self.match(TokenType.AT):
            decorators = [self.decorator()]
            while self.match(TokenType.AT):
                decorators.append(self.decorator())
            stmt = self.declaration()
            if isinstance(stmt, FunctionStmt):
                stmt.decorators = decorators
            return stmt

        # Check for actor declaration
        if self.match(TokenType.ACTOR):
            return self.actor_declaration()

        # Check for function declaration
        if self.check(TokenType.DEF) or self.check(TokenType.ASYNC):
            return self.function_declaration()

        # Check for pattern matching
        if self.match(TokenType.MATCH):
            return self.pattern_match()

        # Check for variable declaration with type hint
        if self.check(TokenType.IDENTIFIER) and self.check_next(TokenType.COLON):
            return self.var_declaration()

        return self.statement()

    def var_declaration(self) -> Statement:
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name")
        type_hint = None
        initializer = None

        # Handle type hint
        if self.match(TokenType.COLON):
            type_hint = self.type_expression()

        # Handle initializer
        if self.match(TokenType.EQUALS):
            initializer = self.expression()

        return ExpressionStmt(TypeHintExpr(name, type_hint, initializer))

    def decorator(self) -> Expression:
        name = self.consume(TokenType.IDENTIFIER, "Expected decorator name")
        if self.match(TokenType.LPAREN):
            arguments = []
            if not self.check(TokenType.RPAREN):
                while True:
                    arguments.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RPAREN, "Expected ')' after decorator arguments")
            return CallExpr(VariableExpr(name), self.previous(), arguments)
        return VariableExpr(name)

    def function_declaration(self) -> FunctionStmt:
        is_async = False
        if self.match(TokenType.ASYNC):
            is_async = True
            self.consume(TokenType.DEF, "Expected 'def' after 'async'")
        else:
            self.consume(TokenType.DEF, "Expected 'def' keyword")

        name = self.consume(TokenType.IDENTIFIER, "Expected function name")

        # Handle generic parameters if present
        generic_params = []
        if self.match(TokenType.LESS):
            while True:
                generic_params.append(
                    self.consume(TokenType.IDENTIFIER, "Expected type parameter name")
                )
                if not self.match(TokenType.COMMA):
                    break
            self.consume(TokenType.GREATER, "Expected '>' after generic parameters")

        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        parameters = []

        # Parse parameters
        if not self.check(TokenType.RPAREN):
            while True:
                param = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
                # Handle parameter type hint
                if self.match(TokenType.COLON):
                    param_type = self.type_expression()
                parameters.append(param)
                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RPAREN, "Expected ')' after parameters")

        # Handle return type annotation
        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.type_expression()

        self.consume(TokenType.COLON, "Expected ':' after function declaration")

        # Parse function body
        body = []
        while not self.is_at_end() and not self.check(TokenType.DEF):
            stmt = self.statement()
            if stmt:
                body.append(stmt)

        return FunctionStmt(name, parameters, body, None, generic_params, return_type, is_async)

    def actor_declaration(self) -> ActorStmt:
        name = self.consume(TokenType.IDENTIFIER, "Expected actor name")
        self.consume(TokenType.COLON, "Expected ':' after actor name")

        state_vars = []
        methods = []

        if self.match(TokenType.STATE):
            self.consume(TokenType.COLON, "Expected ':' after state declaration")
            while not self.check(TokenType.DEF) and not self.is_at_end():
                state_vars.append(self.var_declaration())

        while self.check(TokenType.DEF) and not self.is_at_end():
            methods.append(self.function_declaration())

        return ActorStmt(name, state_vars, methods)

    def pattern_match(self) -> PatternMatchStmt:
        value = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after match expression")

        cases = []
        while self.match(TokenType.CASE):
            pattern = self.pattern()
            guard = None
            binding = None

            if self.match(TokenType.IDENTIFIER) and self.previous().lexeme == "as":
                binding = self.consume(TokenType.IDENTIFIER, "Expected binding name after 'as'")

            if self.match(TokenType.IDENTIFIER) and self.previous().lexeme == "if":
                guard = self.expression()

            self.consume(TokenType.COLON, "Expected ':' after case pattern")
            body = []

            while not self.check(TokenType.CASE) and not self.is_at_end():
                body.append(self.statement())

            cases.append(PatternCase(pattern, guard, binding, body))

        return PatternMatchStmt(value, cases)

    def pattern(self) -> Expression:
        if self.match(TokenType.STRING, TokenType.INTEGER, TokenType.FLOAT):
            return LiteralExpr(self.previous().literal)

        if self.match(TokenType.IDENTIFIER):
            name = self.previous()
            if self.match(TokenType.LPAREN):
                # Type pattern with constructor
                self.consume(TokenType.RPAREN, "Expected ')' after type pattern")
                return CallExpr(VariableExpr(name), self.previous(), [])
            return VariableExpr(name)

        raise ParseError("Expected pattern")

    def statement(self) -> Statement:
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.WITH):
            return self.with_statement()
        return self.expression_statement()

    def if_statement(self) -> Statement:
        condition = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after if condition")

        then_branch = self.statement()
        else_branch = None

        if self.match(TokenType.ELSE):
            self.consume(TokenType.COLON, "Expected ':' after else")
            else_branch = self.statement()

        return IfStmt(condition, then_branch, else_branch)

    def with_statement(self) -> Statement:
        resource = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after with expression")

        body = []
        while not self.is_at_end() and not self.check_dedent():
            stmt = self.statement()
            if stmt:
                body.append(stmt)

        return WithStmt(resource, body)

    def return_statement(self) -> Statement:
        keyword = self.previous()
        value = None

        if not self.is_at_end() and not self.check_newline():
            value = self.expression()

        return ReturnStmt(keyword, value)

    def expression_statement(self) -> Statement:
        expr = self.expression()
        return ExpressionStmt(expr)

    def expression(self) -> Expression:
        # Handle multiple assignments
        if self.is_multiple_assignment():
            return self.multiple_assignment()
        return self.assignment()

    def is_multiple_assignment(self) -> bool:
        if not self.check(TokenType.IDENTIFIER):
            return False
        i = 1
        seen_comma = False
        while True:
            if self.check_n(TokenType.COMMA, i):
                seen_comma = True
                i += 1
            elif self.check_n(TokenType.IDENTIFIER, i):
                i += 1
            elif self.check_n(TokenType.EQUALS, i):
                return seen_comma
            else:
                return False

    def multiple_assignment(self) -> Expression:
        targets = []
        while True:
            targets.append(self.consume(TokenType.IDENTIFIER, "Expected variable name"))
            if not self.match(TokenType.COMMA):
                break

        self.consume(TokenType.EQUALS, "Expected '=' after variables")
        values = []
        while True:
            values.append(self.expression())
            if not self.match(TokenType.COMMA):
                break

        return MultiAssignExpr(targets, values)

    def assignment(self) -> Expression:
        expr = self.or_expr()

        if self.match(TokenType.EQUALS):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expr, VariableExpr):
                return AssignExpr(expr.name, value)

            self.error(equals, "Invalid assignment target.")

        return expr

    def or_expr(self) -> Expression:
        expr = self.and_expr()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.and_expr()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def and_expr(self) -> Expression:
        expr = self.bitwise_or()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.bitwise_or()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def bitwise_or(self) -> Expression:
        expr = self.bitwise_xor()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.bitwise_xor()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def bitwise_xor(self) -> Expression:
        expr = self.bitwise_and()

        while self.match(TokenType.XOR):
            operator = self.previous()
            right = self.bitwise_and()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def bitwise_and(self) -> Expression:
        expr = self.equality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def equality(self) -> Expression:
        expr = self.comparison()

        while self.match(TokenType.DOUBLE_EQUALS):
            operator = self.previous()
            right = self.comparison()
            expr = BinaryExpr(expr, operator, right)

        return expr

    def comparison(self) -> Expression:
        expr = self.term()

        while self.match(TokenType.LESS, TokenType.GREATER):
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
        if self.match(TokenType.MINUS, TokenType.NOT):
            operator = self.previous()
            right = self.unary()
            return UnaryExpr(operator, right)

        return self.type_application()

    def type_application(self) -> Expression:
        expr = self.primary()

        while self.match(TokenType.LBRACKET):
            type_args = []
            while True:
                type_args.append(self.type_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.consume(TokenType.RBRACKET, "Expected ']' after type arguments")
            expr = GenericTypeExpr(expr, type_args)

        return expr

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
                paren = self.consume(TokenType.RPAREN, "Expected ')' after arguments")
                return CallExpr(expr, paren, arguments)
            return expr

        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return GroupingExpr(expr)

        raise ParseError("Expected expression")

    def type_expression(self) -> Expression:
        base = self.consume(TokenType.IDENTIFIER, "Expected type name")

        if self.match(TokenType.LBRACKET):
            params = []
            while True:
                params.append(self.type_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.consume(TokenType.RBRACKET, "Expected ']' after type parameters")
            return GenericTypeExpr(base, params)
            
        return VariableExpr(base)

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

    def check_next(self, type: TokenType) -> bool:
        if self.is_at_end() or self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == type

    def check_n(self, type: TokenType, n: int) -> bool:
        if self.current + n >= len(self.tokens):
            return False
        return self.tokens[self.current + n].type == type

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
        if token.type == TokenType.EOF:
            message = f"Error at end of file: {message}"
        else:
            message = f"Error at '{token.lexeme}': {message}"
        return ParseError(message)

    def synchronize(self):
        """Skip tokens until we reach a synchronization point (like a statement boundary)"""
        self.advance()

        while not self.is_at_end():
            # Stop at statement boundaries
            if self.previous().type == TokenType.COLON:
                return

            if self.peek().type in {
                TokenType.DEF,
                TokenType.IF,
                TokenType.RETURN,
                TokenType.FOR,
                TokenType.WHILE,
                TokenType.MATCH,
                TokenType.WITH,
                TokenType.CLASS,
                TokenType.ACTOR,
            }:
                return

            self.advance()

    def check_dedent(self) -> bool:
        # TODO: Implement proper indentation tracking
        return False

    def check_newline(self) -> bool:
        # TODO: Implement proper newline tracking
        return False