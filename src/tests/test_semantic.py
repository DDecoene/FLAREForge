from FLAREcore.lexer import Lexer
from FLAREcore.parser import (
    BinaryExpr,
    CallExpr,
    ExpressionStmt,
    FunctionStmt,
    IfStmt,
    LiteralExpr,
    Parser,
    UnaryExpr,
    TypeHintExpr,
    MultiAssignExpr,
    GenericTypeExpr,
    PatternMatchStmt,
)

def parse_source(source: str):
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    return parser.parse()

def test_type_hints():
    ast = parse_source("x: int = 42")
    assert len(ast) == 1
    stmt = ast[0]
    assert isinstance(stmt, ExpressionStmt)
    expr = stmt.expression
    assert isinstance(expr, TypeHintExpr)
    assert expr.name.lexeme == "x"
    assert expr.type.lexeme == "int"
    assert isinstance(expr.value, LiteralExpr)
    assert expr.value.value == 42

def test_multiple_assignment():
    ast = parse_source("x, y = 1, 2")
    assert len(ast) == 1
    stmt = ast[0]
    assert isinstance(stmt, ExpressionStmt)
    expr = stmt.expression
    assert isinstance(expr, MultiAssignExpr)
    assert len(expr.targets) == 2
    assert len(expr.values) == 2
    assert expr.targets[0].lexeme == "x"
    assert expr.targets[1].lexeme == "y"
    assert isinstance(expr.values[0], LiteralExpr)
    assert isinstance(expr.values[1], LiteralExpr)
    assert expr.values[0].value == 1
    assert expr.values[1].value == 2

def test_generic_function():
    ast = parse_source("""
def first<T>(items: List[T]) -> T:
    return items[0]
""")
    assert len(ast) == 1
    func = ast[0]
    assert isinstance(func, FunctionStmt)
    assert isinstance(func.generic_params, list)
    assert len(func.generic_params) == 1
    assert func.generic_params[0].lexeme == "T"
    param_type = func.params[0].type_hint
    assert isinstance(param_type, GenericTypeExpr)
    assert param_type.base_type.lexeme == "List"
    assert param_type.type_params[0].lexeme == "T"

def test_pattern_matching():
    ast = parse_source("""
match command:
    case "help":
        show_help()
    case "quit":
        exit()
    case str() as cmd if cmd.startswith("run "):
        execute(cmd)
""")
    assert len(ast) == 1
    stmt = ast[0]
    assert isinstance(stmt, PatternMatchStmt)
    assert len(stmt.cases) == 3
    # Test string literal pattern
    assert isinstance(stmt.cases[0].pattern, LiteralExpr)
    assert stmt.cases[0].pattern.value == "help"
    # Test type pattern with guard
    case = stmt.cases[2]
    assert case.pattern.type.lexeme == "str"
    assert case.binding.lexeme == "cmd"
    assert case.guard is not None

def test_decorated_function():
    ast = parse_source("""
@parallel
@vectorize
def process_data(values):
    return [x * 2 for x in values]
""")
    assert len(ast) == 1
    func = ast[0]
    assert isinstance(func, FunctionStmt)
    assert len(func.decorators) == 2
    assert func.decorators[0].name.lexeme == "parallel"
    assert func.decorators[1].name.lexeme == "vectorize"

def test_actor_declaration():
    ast = parse_source("""
actor WebServer:
    state:
        server_state = ServerState()
    
    async def handle_request(self, req):
        return Response.ok()
""")
    assert len(ast) == 1
    actor = ast[0]
    assert isinstance(actor, ActorStmt)
    assert actor.name.lexeme == "WebServer"
    assert len(actor.state_vars) == 1
    assert len(actor.methods) == 1
    method = actor.methods[0]
    assert method.is_async
    assert method.name.lexeme == "handle_request"

def test_bitwise_expressions():
    ast = parse_source("x = (a & b) | (c ^ d)")
    assert len(ast) == 1
    stmt = ast[0]
    expr = stmt.expression
    assert isinstance(expr, BinaryExpr)
    assert expr.operator.type == TokenType.OR
    assert isinstance(expr.left, BinaryExpr)
    assert expr.left.operator.type == TokenType.AND
    assert isinstance(expr.right, BinaryExpr)
    assert expr.right.operator.type == TokenType.XOR

def test_enhanced_for_loop():
    ast = parse_source("""
for x in values if x > 0:
    process(x)
""")
    assert len(ast) == 1
    stmt = ast[0]
    assert isinstance(stmt, ForStmt)
    assert stmt.filter is not None
    assert isinstance(stmt.filter, BinaryExpr)
    assert stmt.filter.operator.type == TokenType.GREATER