from dataclasses import dataclass, field
from typing import List, Optional
from .lexer import Token

# Base classes
@dataclass
class Expression:
    """Base class for all expressions"""
    pass

@dataclass
class Statement:
    """Base class for all statements"""
    pass

# Expression nodes
@dataclass
class BinaryExpr(Expression):
    """Binary expression (e.g., a + b, x == y)"""
    left: Expression
    operator: Token
    right: Expression

@dataclass
class UnaryExpr(Expression):
    """Unary expression (e.g., -x, not y)"""
    operator: Token
    right: Expression

@dataclass
class LiteralExpr(Expression):
    """Literal values (numbers, strings)"""
    value: object

@dataclass
class GroupingExpr(Expression):
    """Parenthesized expressions"""
    expression: Expression

@dataclass
class VariableExpr(Expression):
    """Variable reference"""
    name: Token

@dataclass
class AssignExpr(Expression):
    """Single variable assignment"""
    name: Token
    value: Expression

@dataclass
class CallExpr(Expression):
    """Function/method calls"""
    callee: Expression
    paren: Token
    arguments: List[Expression]

@dataclass
class TypeHintExpr(Expression):
    """Type hint expression (e.g., x: int = 42)"""
    name: Token
    type_hint: Expression
    value: Optional[Expression] = None

@dataclass
class GenericTypeExpr(Expression):
    """Generic type expression (e.g., List[int])"""
    base_type: Token
    type_params: List[Expression]

@dataclass
class MultiAssignExpr(Expression):
    """Multiple assignment (e.g., x, y = 1, 2)"""
    targets: List[Token]
    values: List[Expression]

# Statement nodes
@dataclass
class ExpressionStmt(Statement):
    """Expression statement"""
    expression: Expression

@dataclass
class FunctionStmt(Statement):
    """Function definition"""
    name: Token
    params: List[Token]
    body: List[Statement]
    decorators: List[Expression] = field(default_factory=list)
    generic_params: List[Token] = field(default_factory=list)
    return_type: Optional[Expression] = None
    is_async: bool = False

@dataclass
class ReturnStmt(Statement):
    """Return statement"""
    keyword: Token
    value: Optional[Expression]

@dataclass
class IfStmt(Statement):
    """If statement"""
    condition: Expression
    then_branch: Statement
    else_branch: Optional[Statement]

@dataclass
class WithStmt(Statement):
    """With statement"""
    resource: Expression
    body: List[Statement]

@dataclass
class ForStmt(Statement):
    """For statement"""
    target: Token
    iterator: Expression
    body: List[Statement]
    filter: Optional[Expression] = None

@dataclass
class PatternCase:
    """Individual case in a pattern match"""
    pattern: Expression
    guard: Optional[Expression]
    binding: Optional[Token]
    body: List[Statement]

@dataclass
class PatternMatchStmt(Statement):
    """Pattern match statement"""
    value: Expression
    cases: List[PatternCase]

@dataclass
class ActorStmt(Statement):
    """Actor definition"""
    name: Token
    state_vars: List[Statement]
    methods: List[FunctionStmt]