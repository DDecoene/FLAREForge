from dataclasses import dataclass
from typing import List, Optional
from .lexer import Token

# Base classes
@dataclass
class Expression:
    pass

@dataclass
class Statement:
    pass

# Expression nodes
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

# Statement nodes
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