from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Type
from .ast import (
    Expression, Statement, FunctionStmt, IfStmt,
    ReturnStmt, ExpressionStmt, VariableExpr, CallExpr,
    AssignExpr, BinaryExpr, LiteralExpr, TypeHintExpr,
    GenericTypeExpr, MultiAssignExpr, PatternMatchStmt,
    ActorStmt, WithStmt, ForStmt, UnaryExpr, GroupingExpr,
    PatternCase
)
from .lexer import Token, TokenType

@dataclass
class SemanticError:
    token: Token
    message: str

class Type:
    """Represents a type in the FLARE type system"""
    def __init__(self, name: str, type_params: List['Type'] = None):
        self.name = name
        self.type_params = type_params or []
        
    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        return (self.name == other.name and 
                len(self.type_params) == len(other.type_params) and
                all(a == b for a, b in zip(self.type_params, other.type_params)))
    
    def is_subtype_of(self, other: 'Type') -> bool:
        if self == other:
            return True
        # TODO: Implement full type hierarchy
        return False

class TypeEnvironment:
    """Manages built-in types and type constructors"""
    def __init__(self):
        self.types = {
            "int": Type("int"),
            "float": Type("float"),
            "str": Type("str"),
            "bool": Type("bool"),
            "List": Type("List"),  # Generic type constructor
            "Optional": Type("Optional"),
            "Future": Type("Future"),
            "Comparable": Type("Comparable"),  # Type constraint
        }
    
    def get_type(self, name: str) -> Optional[Type]:
        return self.types.get(name)
    
    def is_generic(self, name: str) -> bool:
        return name in {"List", "Optional", "Future"}

class Scope:
    def __init__(self, parent=None):
        self.parent: Optional[Scope] = parent
        self.variables: Dict[str, Type] = {}
        self.functions: Dict[str, FunctionType] = {}
        self.types: Dict[str, Type] = {}
        self.in_actor = False
        self.in_async = False
        self.in_vectorized = False
        self.loop_depth = 0

    def define_variable(self, name: str, type_: Optional[Type] = None):
        """Define a variable in the current scope"""
        self.variables[name] = type_

    def get_variable_type(self, name: str) -> Optional[Type]:
        """Get the type of a variable, including from parent scopes"""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get_variable_type(name)
        return None

    def declare_function(self, name: str, func_type: 'FunctionType'):
        """Declare a function with its type"""
        self.functions[name] = func_type

    def get_function_type(self, name: str) -> Optional['FunctionType']:
        """Get a function's type, including from parent scopes"""
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function_type(name)
        return None

    def define_type(self, name: str, type_: Type):
        """Define a type in the current scope"""
        self.types[name] = type_

    def get_type(self, name: str) -> Optional[Type]:
        """Get a type by name, including from parent scopes"""
        if name in self.types:
            return self.types[name]
        if self.parent:
            return self.parent.get_type(name)
        return None

@dataclass
class FunctionType:
    """Represents the type of a function"""
    param_types: List[Type]
    return_type: Type
    is_async: bool = False
    generic_params: List[str] = None

class SemanticAnalyzer:
    def __init__(self):
        self.errors: List[SemanticError] = []
        self.type_env = TypeEnvironment()
        
    def analyze(self, statements: List[Statement]) -> List[SemanticError]:
        """Analyze a list of statements for semantic errors"""
        self.errors = []
        global_scope = Scope()
        self._analyze_statements(statements, global_scope)
        return self.errors

    def _analyze_statements(self, statements: List[Statement], scope: Scope):
        """Analyze multiple statements"""
        for stmt in statements:
            self._analyze_statement(stmt, scope)

    def _analyze_statement(self, stmt: Statement, scope: Scope):
        """Analyze a single statement"""
        if isinstance(stmt, FunctionStmt):
            self._analyze_function(stmt, scope)
            
        elif isinstance(stmt, IfStmt):
            self._analyze_if(stmt, scope)
            
        elif isinstance(stmt, ReturnStmt):
            self._analyze_return(stmt, scope)
            
        elif isinstance(stmt, ExpressionStmt):
            self._analyze_expression(stmt.expression, scope)
            
        elif isinstance(stmt, WithStmt):
            self._analyze_with(stmt, scope)
            
        elif isinstance(stmt, PatternMatchStmt):
            self._analyze_pattern_match(stmt, scope)
            
        elif isinstance(stmt, ActorStmt):
            self._analyze_actor(stmt, scope)
            
        elif isinstance(stmt, ForStmt):
            self._analyze_for(stmt, scope)

    def _analyze_function(self, stmt: FunctionStmt, scope: Scope):
        """Analyze a function definition"""
        # Create function scope
        function_scope = Scope(scope)
        function_scope.in_async = stmt.is_async
        
        # Handle generic parameters
        if stmt.generic_params:
            for param in stmt.generic_params:
                function_scope.define_type(param.lexeme, Type(param.lexeme))
        
        # Analyze parameter types
        param_types = []
        for param in stmt.params:
            # TODO: Handle parameter type hints
            function_scope.define_variable(param.lexeme)
            param_types.append(Type("Any"))  # Default to Any if no type hint
        
        # Analyze return type
        return_type = Type("Any")
        if stmt.return_type:
            return_type = self._analyze_type_expression(stmt.return_type, function_scope)
        
        # Create and store function type
        func_type = FunctionType(param_types, return_type, stmt.is_async, 
                               [p.lexeme for p in stmt.generic_params] if stmt.generic_params else None)
        scope.declare_function(stmt.name.lexeme, func_type)
        
        # Analyze decorators
        if stmt.decorators:
            self._analyze_decorators(stmt.decorators, function_scope)
        
        # Analyze function body
        self._analyze_statements(stmt.body, function_scope)

    def _analyze_if(self, stmt: IfStmt, scope: Scope):
        """Analyze an if statement"""
        condition_type = self._analyze_expression(stmt.condition, scope)
        if condition_type and condition_type.name != "bool":
            self.errors.append(SemanticError(
                self._get_token(stmt.condition),
                f"Condition must be boolean, got {condition_type.name}"
            ))
        
        then_scope = Scope(scope)
        self._analyze_statement(stmt.then_branch, then_scope)
        
        if stmt.else_branch:
            else_scope = Scope(scope)
            self._analyze_statement(stmt.else_branch, else_scope)

    def _analyze_return(self, stmt: ReturnStmt, scope: Scope):
        """Analyze a return statement"""
        if stmt.value:
            return_type = self._analyze_expression(stmt.value, scope)
            # TODO: Check return type matches function declaration
        
        if scope.in_async and not scope.in_actor:
            # Verify return value is wrapped in Future for async functions
            if stmt.value and not isinstance(return_type, Type) or return_type.name != "Future":
                self.errors.append(SemanticError(
                    stmt.keyword,
                    "Async functions must return Future"
                ))

    def _analyze_with(self, stmt: WithStmt, scope: Scope):
        """Analyze a with statement"""
        resource_type = self._analyze_expression(stmt.resource, scope)
        
        # Create new scope for with body
        with_scope = Scope(scope)
        self._analyze_statements(stmt.body, with_scope)

    def _analyze_pattern_match(self, stmt: PatternMatchStmt, scope: Scope):
        """Analyze a pattern match statement"""
        match_type = self._analyze_expression(stmt.value, scope)
        
        seen_patterns = set()
        for case in stmt.cases:
            pattern_type = self._analyze_expression(case.pattern, scope)
            
            # Check pattern exhaustiveness
            pattern_key = self._get_pattern_key(case.pattern)
            if pattern_key in seen_patterns:
                self.errors.append(SemanticError(
                    self._get_token(case.pattern),
                    "Duplicate pattern in match statement"
                ))
            seen_patterns.add(pattern_key)
            
            # Create scope for case body with binding if present
            case_scope = Scope(scope)
            if case.binding:
                case_scope.define_variable(case.binding.lexeme, pattern_type)
            
            # Analyze guard if present
            if case.guard:
                guard_type = self._analyze_expression(case.guard, case_scope)
                if guard_type.name != "bool":
                    self.errors.append(SemanticError(
                        self._get_token(case.guard),
                        "Pattern guard must be boolean"
                    ))
            
            self._analyze_statements(case.body, case_scope)
        
        # Check for exhaustiveness based on match_type
        self._check_pattern_exhaustiveness(match_type, seen_patterns, stmt.value)

    def _analyze_actor(self, stmt: ActorStmt, scope: Scope):
        """Analyze an actor definition"""
        actor_scope = Scope(scope)
        actor_scope.in_actor = True
        
        # Analyze state variables
        for var in stmt.state_vars:
            self._analyze_statement(var, actor_scope)
        
        # Analyze methods
        for method in stmt.methods:
            self._analyze_function(method, actor_scope)

    def _analyze_for(self, stmt: ForStmt, scope: Scope):
        """Analyze a for loop"""
        iterator_type = self._analyze_expression(stmt.iterator, scope)
        
        # Check if iterator type is iterable
        if not self._is_iterable_type(iterator_type):
            self.errors.append(SemanticError(
                self._get_token(stmt.iterator),
                f"Type {iterator_type.name} is not iterable"
            ))
        
        # Create loop scope
        loop_scope = Scope(scope)
        loop_scope.loop_depth = scope.loop_depth + 1
        
        # Define loop variable
        element_type = self._get_iterator_element_type(iterator_type)
        loop_scope.define_variable(stmt.target.lexeme, element_type)
        
        # Analyze filter if present
        if stmt.filter:
            filter_type = self._analyze_expression(stmt.filter, loop_scope)
            if filter_type.name != "bool":
                self.errors.append(SemanticError(
                    self._get_token(stmt.filter),
                    "Loop filter must be boolean"
                ))
        
        # Analyze loop body
        self._analyze_statements(stmt.body, loop_scope)

    def _analyze_expression(self, expr: Expression, scope: Scope) -> Optional[Type]:
        """Analyze an expression and return its type"""
        if isinstance(expr, BinaryExpr):
            return self._analyze_binary(expr, scope)
            
        elif isinstance(expr, UnaryExpr):
            return self._analyze_unary(expr, scope)
            
        elif isinstance(expr, LiteralExpr):
            return self._get_literal_type(expr.value)
            
        elif isinstance(expr, GroupingExpr):
            return self._analyze_expression(expr.expression, scope)
            
        elif isinstance(expr, VariableExpr):
            return self._analyze_variable(expr, scope)
            
        elif isinstance(expr, CallExpr):
            return self._analyze_call(expr, scope)
            
        elif isinstance(expr, AssignExpr):
            return self._analyze_assignment(expr, scope)
            
        elif isinstance(expr, TypeHintExpr):
            return self._analyze_type_hint(expr, scope)
            
        elif isinstance(expr, MultiAssignExpr):
            return self._analyze_multi_assign(expr, scope)
            
        elif isinstance(expr, GenericTypeExpr):
            return self._analyze_generic_type(expr, scope)
        
        return None

    def _analyze_binary(self, expr: BinaryExpr, scope: Scope) -> Type:
        """Analyze a binary expression"""
        left_type = self._analyze_expression(expr.left, scope)
        right_type = self._analyze_expression(expr.right, scope)
        
        if not left_type or not right_type:
            return Type("Any")
            
        operator = expr.operator.type
        
        # Type checking based on operator
        if operator in {TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH}:
            if left_type.name in {"int", "float"} and right_type.name in {"int", "float"}:
                # Numeric operations
                return Type("float") if "float" in {left_type.name, right_type.name} else Type("int")
            elif operator == TokenType.PLUS and "str" in {left_type.name, right_type.name}:
                # String concatenation
                return Type("str")
                
        elif operator in {TokenType.AND, TokenType.OR, TokenType.XOR}:
            # Bitwise operations require integers
            if left_type.name != "int" or right_type.name != "int":
                self.errors.append(SemanticError(
                    expr.operator,
                    f"Bitwise operations require integers, got {left_type.name} and {right_type.name}"
                ))
            return Type("int")
            
        elif operator in {TokenType.DOUBLE_EQUALS, TokenType.LESS, TokenType.GREATER}:
            # Comparison operations
            return Type("bool")
        
        self.errors.append(SemanticError(
            expr.operator,
            f"Invalid operation between types {left_type.name} and {right_type.name}"
        ))
        return Type("Any")

    def _analyze_unary(self, expr: UnaryExpr, scope: Scope) -> Type:
        """Analyze a unary expression"""
        operand_type = self._analyze_expression(expr.right, scope)
        
        if not operand_type:
            return Type("Any")
            
        if expr.operator.type == TokenType.MINUS:
            if operand_type.name not in {"int", "float"}:
                self.errors.append(SemanticError(
                    expr.operator,
                    f"Unary minus requires numeric type, got {operand_type.name}"
                ))
            return operand_type
            
        elif expr.operator.type == TokenType.NOT:
            return Type("bool")
            
        return Type("Any")

    def _analyze_variable(self, expr: VariableExpr, scope: Scope) -> Optional[Type]:
        """Analyze a variable reference"""
        # Check if it's a type name
        if type_def := scope.get_type(expr.name.lexeme):
            return type_def
            
        # Check if it's a variable
        if var_type := scope.get_variable_type(expr.name.lexeme):
            return var_type
            
        # Check if it's a function
        if func_type := scope.get_function_type(expr.name.lexeme):
            return func_type
            
        self.errors.append(SemanticError(
            expr.name,
            f"Undefined variable '{expr.name.lexeme}'"
        ))
        return None

    def _analyze_call(self, expr: CallExpr, scope: Scope) -> Optional[Type]:
        """Analyze a function call"""
        callee_type = self._analyze_expression(expr.callee, scope)
        
        if not callee_type:
            return None
            
        if not isinstance(callee_type, FunctionType):
            self.errors.append(SemanticError(
                expr.paren,
                f"Cannot call non-function type {callee_type.name}"
            ))
            return None
            
        # Check number of arguments
        if len(expr.arguments) != len(callee_type.param_types):
            self.errors.append(SemanticError(
                expr.paren,
                f"Expected {len(callee_type.param_types)} arguments but got {len(expr.arguments)}"
            ))
            return callee_type.return_type
            
        # Analyze and check each argument
        for arg, expected_type in zip(expr.arguments, callee_type.param_types):
            arg_type = self._analyze_expression(arg, scope)
            if arg_type and not arg_type.is_subtype_of(expected_type):
                self.errors.append(SemanticError(
                    self._get_token(arg),
                    f"Expected argument of type {expected_type.name}, got {arg_type.name}"
                ))
                
        # If async function is called from non-async context, error
        if callee_type.is_async and not scope.in_async:
            self.errors.append(SemanticError(
                expr.paren,
                "Async function must be awaited"
            ))
            
        return callee_type.return_type

    def _analyze_assignment(self, expr: AssignExpr, scope: Scope) -> Optional[Type]:
        """Analyze a single assignment"""
        value_type = self._analyze_expression(expr.value, scope)
        
        if existing_type := scope.get_variable_type(expr.name.lexeme):
            # Check type compatibility for existing variable
            if value_type and not value_type.is_subtype_of(existing_type):
                self.errors.append(SemanticError(
                    expr.name,
                    f"Cannot assign value of type {value_type.name} to variable of type {existing_type.name}"
                ))
            return existing_type
        else:
            # Define new variable with inferred type
            scope.define_variable(expr.name.lexeme, value_type)
            return value_type

    def _analyze_type_hint(self, expr: TypeHintExpr, scope: Scope) -> Optional[Type]:
        """Analyze a type hint expression"""
        hinted_type = self._analyze_type_expression(expr.type_hint, scope)
        
        if expr.value:
            value_type = self._analyze_expression(expr.value, scope)
            if value_type and not value_type.is_subtype_of(hinted_type):
                self.errors.append(SemanticError(
                    self._get_token(expr.value),
                    f"Type hint mismatch: expected {hinted_type.name}, got {value_type.name}"
                ))
                
        scope.define_variable(expr.name.lexeme, hinted_type)
        return hinted_type

    def _analyze_multi_assign(self, expr: MultiAssignExpr, scope: Scope) -> Optional[Type]:
        """Analyze a multiple assignment expression"""
        if len(expr.targets) != len(expr.values):
            self.errors.append(SemanticError(
                expr.targets[0],
                f"Expected {len(expr.targets)} values but got {len(expr.values)}"
            ))
            return None
            
        value_types = [self._analyze_expression(val, scope) for val in expr.values]
        
        for target, value_type in zip(expr.targets, value_types):
            if existing_type := scope.get_variable_type(target.lexeme):
                if value_type and not value_type.is_subtype_of(existing_type):
                    self.errors.append(SemanticError(
                        target,
                        f"Cannot assign value of type {value_type.name} to variable of type {existing_type.name}"
                    ))
            else:
                scope.define_variable(target.lexeme, value_type)
                
        return Type("tuple")  # Multiple assignment expressions return a tuple type

    def _analyze_type_expression(self, expr: Expression, scope: Scope) -> Type:
        """Analyze a type expression (used in hints and annotations)"""
        if isinstance(expr, VariableExpr):
            if type_def := scope.get_type(expr.name.lexeme):
                return type_def
            if builtin_type := self.type_env.get_type(expr.name.lexeme):
                return builtin_type
            self.errors.append(SemanticError(
                expr.name,
                f"Undefined type {expr.name.lexeme}"
            ))
            return Type("Any")
            
        elif isinstance(expr, GenericTypeExpr):
            base_type = self._analyze_type_expression(expr.base_type, scope)
            if not self.type_env.is_generic(base_type.name):
                self.errors.append(SemanticError(
                    self._get_token(expr.base_type),
                    f"Type {base_type.name} is not generic"
                ))
            type_params = [self._analyze_type_expression(param, scope) for param in expr.type_params]
            return Type(base_type.name, type_params)
            
        return Type("Any")

    def _analyze_decorators(self, decorators: List[Expression], scope: Scope):
        """Analyze function decorators"""
        for decorator in decorators:
            if isinstance(decorator, VariableExpr):
                if decorator.name.lexeme == "vectorize":
                    scope.in_vectorized = True
                elif decorator.name.lexeme == "parallel":
                    # Check for vectorize + parallel combination
                    if scope.in_vectorized:
                        self.errors.append(SemanticError(
                            decorator.name,
                            "Cannot combine @vectorize with @parallel"
                        ))

    def _get_literal_type(self, value: object) -> Type:
        """Get the type of a literal value"""
        if isinstance(value, int):
            return Type("int")
        elif isinstance(value, float):
            return Type("float")
        elif isinstance(value, str):
            return Type("str")
        elif isinstance(value, bool):
            return Type("bool")
        elif value is None:
            return Type("None")
        return Type("Any")

    def _is_iterable_type(self, type_: Optional[Type]) -> bool:
        """Check if a type is iterable"""
        if not type_:
            return False
        return type_.name in {"List", "str", "tuple", "set", "dict"}

    def _get_iterator_element_type(self, type_: Type) -> Type:
        """Get the element type of an iterable"""
        if type_.name == "List" and type_.type_params:
            return type_.type_params[0]
        elif type_.name == "str":
            return Type("str")
        elif type_.name == "tuple":
            return Type("Any")  # Could be more specific with tuple types
        return Type("Any")

    def _get_pattern_key(self, pattern: Expression) -> str:
        """Get a unique key for a pattern for exhaustiveness checking"""
        if isinstance(pattern, LiteralExpr):
            return f"literal:{pattern.value}"
        elif isinstance(pattern, VariableExpr):
            return f"type:{pattern.name.lexeme}"
        return "wildcard"

    def _check_pattern_exhaustiveness(self, match_type: Type, seen_patterns: Set[str], match_expr: Expression):
        """Check if pattern matching is exhaustive"""
        if not any(p == "wildcard" for p in seen_patterns):
            all_possible = self._get_possible_patterns(match_type)
            missing = all_possible - seen_patterns
            if missing:
                self.errors.append(SemanticError(
                    self._get_token(match_expr),
                    f"Non-exhaustive pattern matching. Missing cases: {', '.join(missing)}"
                ))

    def _get_possible_patterns(self, type_: Type) -> Set[str]:
        """Get all possible patterns for a type"""
        if type_.name == "bool":
            return {f"literal:True", f"literal:False"}
        # Add more exhaustiveness checking for other types
        return {"wildcard"}

    def _get_token(self, expr: Expression) -> Token:
        """Get a representative token from an expression for error reporting"""
        if isinstance(expr, VariableExpr):
            return expr.name
        elif isinstance(expr, CallExpr):
            return expr.paren
        elif isinstance(expr, BinaryExpr):
            return expr.operator
        elif isinstance(expr, UnaryExpr):
            return expr.operator
        # Add more cases as needed
        return Token(TokenType.ERROR, "", None, 0)  # Fallback token