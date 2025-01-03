from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from .parser import (
    Expression, Statement, FunctionStmt, IfStmt,
    ReturnStmt, ExpressionStmt, VariableExpr, CallExpr,
    AssignExpr, BinaryExpr, LiteralExpr
)
from .lexer import Token, TokenType
@dataclass
class SemanticError:
    token: Token
    message: str


class Scope:
    def __init__(self, parent: Optional['Scope'] = None):
        self.parent = parent
        self.variables: Set[str] = set()
        self.defined_variables: Set[str] = set()
        self.functions: Dict[str, List[Token]] = {}

    def declare_variable(self, name: str):
        self.variables.add(name)

    def define_variable(self, name: str):
        self.variables.add(name)
        self.defined_variables.add(name)

    def is_defined(self, name: str) -> bool:
        if name in self.defined_variables:
            return True
        if self.parent:
            return self.parent.is_defined(name)
        return False

    def declare_function(self, name: str, params: List[Token]):
        if name in self.functions:
            raise ValueError(f"Function '{name}' already declared in this scope.")
        self.functions[name] = params

    def is_function_declared(self, name: str) -> bool:
        if name in self.functions:
            return True
        if self.parent:
            return self.parent.is_function_declared(name)
        return False


class SemanticAnalyzer:
    def __init__(self):
        self.errors: List[SemanticError] = []

    def analyze(self, statements: List[Statement]) -> List[SemanticError]:
        self.errors.clear()
        global_scope = Scope()
        self._analyze_statements(statements, global_scope)
        return self.errors

    def _analyze_statements(self, statements: List[Statement], scope: Scope):
        for stmt in statements:
            self._analyze_statement(stmt, scope)

    def _analyze_statement(self, stmt: Statement, scope: Scope):
        if isinstance(stmt, FunctionStmt):
            try:
                scope.declare_function(stmt.name.lexeme, stmt.params)
            except ValueError:
                self.errors.append(SemanticError(stmt.name, f"Function '{stmt.name.lexeme}' already declared."))
            function_scope = Scope(scope)
            for param in stmt.params:
                function_scope.define_variable(param.lexeme)
            self._analyze_statements(stmt.body, function_scope)

        elif isinstance(stmt, IfStmt):
            self._analyze_expression(stmt.condition, scope)
            then_scope = Scope(scope)
            self._analyze_statements(stmt.then_branch.body, then_scope)
            if stmt.else_branch:
                else_scope = Scope(scope)
                self._analyze_statements(stmt.else_branch.body, else_scope)

        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                self._analyze_expression(stmt.value, scope)

        elif isinstance(stmt, ExpressionStmt):
            self._analyze_expression(stmt.expression, scope)

    def _analyze_expression(self, expr: Expression, scope: Scope):
        if isinstance(expr, VariableExpr):
            if not scope.is_defined(expr.name.lexeme):
                self.errors.append(SemanticError(expr.name, f"Undefined variable '{expr.name.lexeme}'"))

        elif isinstance(expr, CallExpr):
            if isinstance(expr.callee, VariableExpr):
                if not scope.is_function_declared(expr.callee.name.lexeme):
                    self.errors.append(SemanticError(expr.callee.name, f"Undefined function '{expr.callee.name.lexeme}'"))
            self._analyze_expression(expr.callee, scope)
            for arg in expr.arguments:
                self._analyze_expression(arg, scope)

        elif isinstance(expr, BinaryExpr):
            self._analyze_expression(expr.left, scope)
            self._analyze_expression(expr.right, scope)

        elif isinstance(expr, AssignExpr):
            if not scope.is_defined(expr.name.lexeme):
                scope.declare_variable(expr.name.lexeme)
            scope.define_variable(expr.name.lexeme)
            self._analyze_expression(expr.value, scope)
