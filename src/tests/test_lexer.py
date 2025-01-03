from FLAREcore.lexer import Lexer, Token, TokenType

def test_empty_source():
    lexer = Lexer("")
    tokens = lexer.scan_tokens()
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF

def test_basic_tokens():
    source = "def main() -> int:"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected = [
        Token(TokenType.DEF, "def", None, 1),
        Token(TokenType.IDENTIFIER, "main", None, 1),
        Token(TokenType.LPAREN, "(", None, 1),
        Token(TokenType.RPAREN, ")", None, 1),
        Token(TokenType.ARROW, "->", None, 1),
        Token(TokenType.IDENTIFIER, "int", None, 1),
        Token(TokenType.COLON, ":", None, 1),
        Token(TokenType.EOF, "", None, 1),
    ]

    assert len(tokens) == len(expected)
    for actual, expected in zip(tokens, expected):
        assert actual.type == expected.type
        assert actual.lexeme == expected.lexeme

def test_multiple_assignment():
    source = "x, y = 1, 2"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected = [
        Token(TokenType.IDENTIFIER, "x", None, 1),
        Token(TokenType.COMMA, ",", None, 1),
        Token(TokenType.IDENTIFIER, "y", None, 1),
        Token(TokenType.EQUALS, "=", None, 1),
        Token(TokenType.INTEGER, "1", 1, 1),
        Token(TokenType.COMMA, ",", None, 1),
        Token(TokenType.INTEGER, "2", 2, 1),
        Token(TokenType.EOF, "", None, 1),
    ]

    assert len(tokens) == len(expected)
    for actual, expected in zip(tokens, expected):
        assert actual.type == expected.type
        assert actual.lexeme == expected.lexeme

def test_type_hints():
    source = "name: str = 'Alice'"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected = [
        Token(TokenType.IDENTIFIER, "name", None, 1),
        Token(TokenType.COLON, ":", None, 1),
        Token(TokenType.IDENTIFIER, "str", None, 1),
        Token(TokenType.EQUALS, "=", None, 1),
        Token(TokenType.STRING, "'Alice'", "Alice", 1),
        Token(TokenType.EOF, "", None, 1),
    ]

    assert len(tokens) == len(expected)
    for actual, expected in zip(tokens, expected):
        assert actual.type == expected.type
        assert actual.lexeme == expected.lexeme

def test_generic_types():
    source = "def first<T>(items: List[T]) -> T:"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected = [
        Token(TokenType.DEF, "def", None, 1),
        Token(TokenType.IDENTIFIER, "first", None, 1),
        Token(TokenType.LESS, "<", None, 1),
        Token(TokenType.IDENTIFIER, "T", None, 1),
        Token(TokenType.GREATER, ">", None, 1),
        Token(TokenType.LPAREN, "(", None, 1),
        Token(TokenType.IDENTIFIER, "items", None, 1),
        Token(TokenType.COLON, ":", None, 1),
        Token(TokenType.IDENTIFIER, "List", None, 1),
        Token(TokenType.LBRACKET, "[", None, 1),
        Token(TokenType.IDENTIFIER, "T", None, 1),
        Token(TokenType.RBRACKET, "]", None, 1),
        Token(TokenType.RPAREN, ")", None, 1),
        Token(TokenType.ARROW, "->", None, 1),
        Token(TokenType.IDENTIFIER, "T", None, 1),
        Token(TokenType.COLON, ":", None, 1),
        Token(TokenType.EOF, "", None, 1),
    ]

    assert len(tokens) == len(expected)
    for actual, expected in zip(tokens, expected):
        assert actual.type == expected.type
        assert actual.lexeme == expected.lexeme

def test_bitwise_operators():
    source = "x = a & b | c ^ d << 2 >> 1"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected_types = [
        TokenType.IDENTIFIER,  # x
        TokenType.EQUALS,      # =
        TokenType.IDENTIFIER,  # a
        TokenType.AND,         # &
        TokenType.IDENTIFIER,  # b
        TokenType.OR,          # |
        TokenType.IDENTIFIER,  # c
        TokenType.XOR,         # ^
        TokenType.IDENTIFIER,  # d
        TokenType.LSHIFT,      # <<
        TokenType.INTEGER,     # 2
        TokenType.RSHIFT,      # >>
        TokenType.INTEGER,     # 1
        TokenType.EOF,
    ]

    assert len(tokens) == len(expected_types)
    for token, expected_type in zip(tokens, expected_types):
        assert token.type == expected_type

def test_boolean_operators():
    source = "if a and b or not c:"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected_types = [
        TokenType.IF,
        TokenType.IDENTIFIER,  # a
        TokenType.AND,         # and
        TokenType.IDENTIFIER,  # b
        TokenType.OR,          # or
        TokenType.NOT,         # not
        TokenType.IDENTIFIER,  # c
        TokenType.COLON,
        TokenType.EOF,
    ]

    assert len(tokens) == len(expected_types)
    for token, expected_type in zip(tokens, expected_types):
        assert token.type == expected_type

def test_decorators():
    source = "@parallel\ndef process_data():"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected = [
        Token(TokenType.AT, "@", None, 1),
        Token(TokenType.IDENTIFIER, "parallel", None, 1),
        Token(TokenType.DEF, "def", None, 2),
        Token(TokenType.IDENTIFIER, "process_data", None, 2),
        Token(TokenType.LPAREN, "(", None, 2),
        Token(TokenType.RPAREN, ")", None, 2),
        Token(TokenType.COLON, ":", None, 2),
        Token(TokenType.EOF, "", None, 2),
    ]

    assert len(tokens) == len(expected)
    for actual, expected in zip(tokens, expected):
        assert actual.type == expected.type
        assert actual.lexeme == expected.lexeme

def test_class_definition():
    source = "class User:\n    def __init__(self, name: str, age: int):"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected_types = [
        TokenType.CLASS,
        TokenType.IDENTIFIER,     # User
        TokenType.COLON,
        TokenType.DEF,
        TokenType.IDENTIFIER,     # __init__
        TokenType.LPAREN,
        TokenType.IDENTIFIER,     # self
        TokenType.COMMA,
        TokenType.IDENTIFIER,     # name
        TokenType.COLON,
        TokenType.IDENTIFIER,     # str
        TokenType.COMMA,
        TokenType.IDENTIFIER,     # age
        TokenType.COLON,
        TokenType.IDENTIFIER,     # int
        TokenType.RPAREN,
        TokenType.COLON,
        TokenType.EOF
    ]

    assert len(tokens) == len(expected_types)
    for token, expected_type in zip(tokens, expected_types):
        assert token.type == expected_type

def test_variable_type_annotations():
    source = "user_id: int = 100\nnames: List[str] = []"
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected_types = [
        TokenType.IDENTIFIER,     # user_id
        TokenType.COLON,
        TokenType.IDENTIFIER,     # int
        TokenType.EQUALS,
        TokenType.INTEGER,        # 100
        TokenType.IDENTIFIER,     # names
        TokenType.COLON,
        TokenType.IDENTIFIER,     # List
        TokenType.LBRACKET,
        TokenType.IDENTIFIER,     # str
        TokenType.RBRACKET,
        TokenType.EQUALS,
        TokenType.LBRACKET,
        TokenType.RBRACKET,
        TokenType.EOF
    ]

    assert len(tokens) == len(expected_types)
    for token, expected_type in zip(tokens, expected_types):
        assert token.type == expected_type

def test_pattern_matching_with_guards():
    source = """match event:
        case MouseClick(x, y):
            handle_click()
        case KeyPress(key) if key.isalpha():
            handle_key()"""
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected_types = [
        TokenType.MATCH,
        TokenType.IDENTIFIER,     # event
        TokenType.COLON,
        TokenType.CASE,
        TokenType.IDENTIFIER,     # MouseClick
        TokenType.LPAREN,
        TokenType.IDENTIFIER,     # x
        TokenType.COMMA,
        TokenType.IDENTIFIER,     # y
        TokenType.RPAREN,
        TokenType.COLON,
        TokenType.IDENTIFIER,     # handle_click
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.CASE,
        TokenType.IDENTIFIER,     # KeyPress
        TokenType.LPAREN,
        TokenType.IDENTIFIER,     # key
        TokenType.RPAREN,
        TokenType.IF,
        TokenType.IDENTIFIER,     # key
        TokenType.IDENTIFIER,     # isalpha
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.COLON,
        TokenType.IDENTIFIER,     # handle_key
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.EOF
    ]


    print_actual_vs_expected_tokens(tokens,expected_types)

    assert len(tokens) == len(expected_types)
    for token, expected_type in zip(tokens, expected_types):
        assert token.type == expected_type

def test_decorator_with_arguments():
    source = '@target(device="cuda:0")\ndef train_model():'
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected_types = [
        TokenType.AT,
        TokenType.IDENTIFIER,     # target
        TokenType.LPAREN,
        TokenType.IDENTIFIER,     # device
        TokenType.EQUALS,
        TokenType.STRING,         # "cuda:0"
        TokenType.RPAREN,
        TokenType.DEF,
        TokenType.IDENTIFIER,     # train_model
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.COLON,
        TokenType.EOF
    ]

    assert len(tokens) == len(expected_types)
    for token, expected_type in zip(tokens, expected_types):
        assert token.type == expected_type

def test_actor_declaration():
    source = """actor WebServer:
        state:
            server_state = ServerState()
        
        async def handle_request(self, req):
            return Response.ok()"""
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    expected_types = [
        TokenType.ACTOR,
        TokenType.IDENTIFIER,     # WebServer
        TokenType.COLON,
        TokenType.STATE,
        TokenType.COLON,
        TokenType.IDENTIFIER,     # server_state
        TokenType.EQUALS,
        TokenType.IDENTIFIER,     # ServerState
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.ASYNC,
        TokenType.DEF,
        TokenType.IDENTIFIER,     # handle_request
        TokenType.LPAREN,
        TokenType.IDENTIFIER,     # self
        TokenType.COMMA,
        TokenType.IDENTIFIER,     # req
        TokenType.RPAREN,
        TokenType.COLON,
        TokenType.RETURN,
        TokenType.IDENTIFIER,     # Response
        TokenType.IDENTIFIER,     # ok
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.EOF
    ]

    assert len(tokens) == len(expected_types)
    for token, expected_type in zip(tokens, expected_types):
        assert token.type == expected_type

def print_actual_vs_expected_tokens(_tokens:list[Token],_expected:list[TokenType]):

    # Print actual tokens for debugging
    print("\nActual tokens:")
    for i, token in enumerate(_tokens):
        print(f"{i}: {token.type} - '{token.lexeme}' (line {token.line}) expected: {_expected[i]}")