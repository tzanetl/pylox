from enum import Enum, auto

from . import error


class TokenType(Enum):
    # Single-character tokens
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()

    # One or two character tokens
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords.
    AND = auto()
    CLASS = auto()
    ELSE = auto()
    FALSE = auto()
    FUN = auto()
    FOR = auto()
    IF = auto()
    NIL = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    VAR = auto()
    WHILE = auto()

    EOF = auto()


type LiteralValue = str | float | None


class Token:
    __slots__ = ("type", "lexeme", "literal", "line")

    def __init__(self, type: TokenType, lexeme: str, literal: LiteralValue, line: int) -> None:
        self.type = type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __str__(self) -> str:
        return f"{self.type} {self.lexeme} {self.literal}"

    def __repr__(self) -> str:
        return str(self)


class Scanner:
    __slots__ = ("source", "tokens", "start", "current", "line")

    def __init__(self, source: str) -> None:
        self.source = source

        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        return char

    def add_token(self, type: TokenType, literal: LiteralValue = None) -> None:
        text = self.source[self.start : self.current]
        self.tokens.append(Token(type, text, literal, self.line))

    def match(self, expected: str) -> bool:
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def peek(self) -> str:
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def string(self) -> None:
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == "\n":
                self.line += 1
            self.advance()

        if self.is_at_end():
            error.error(self.line, "Unterminated string.")
            return

        # The closing ".
        self.advance()

        # Trim surrounding quotes
        value = self.source[self.start + 1 : self.current - 1]
        self.add_token(TokenType.STRING, value)

    def is_digit(self, char: str) -> bool:
        return char.isdigit()

    def number(self) -> None:
        while self.is_digit(self.peek()):
            self.advance()

        if self.peek() == "." and self.is_digit(self.peek_next()):
            self.advance()
            while self.is_digit(self.peek()):
                self.advance()

        self.add_token(TokenType.NUMBER, float(self.source[self.start : self.current]))

    def scan_single_token(self) -> None:
        char = self.advance()
        match char:
            # Single-character tokens
            case "(":
                self.add_token(TokenType.LEFT_PAREN)
            case ")":
                self.add_token(TokenType.RIGHT_PAREN)
            case "{":
                self.add_token(TokenType.LEFT_BRACE)
            case "}":
                self.add_token(TokenType.RIGHT_BRACE)
            case ",":
                self.add_token(TokenType.COMMA)
            case ".":
                self.add_token(TokenType.DOT)
            case "-":
                self.add_token(TokenType.MINUS)
            case "+":
                self.add_token(TokenType.PLUS)
            case ";":
                self.add_token(TokenType.SEMICOLON)
            case "*":
                self.add_token(TokenType.STAR)
            # One or two character tokens
            case "!":
                self.add_token(TokenType.BANG_EQUAL if self.match("=") else TokenType.BANG)
            case "=":
                self.add_token(TokenType.EQUAL_EQUAL if self.match("=") else TokenType.EQUAL)
            case "<":
                self.add_token(TokenType.LESS_EQUAL if self.match("=") else TokenType.LESS)
            case ">":
                self.add_token(TokenType.GREATER_EQUAL if self.match("=") else TokenType.GREATER)
            case "/":
                if self.match("/"):
                    while self.peek() != "\n" and not self.is_at_end():
                        self.advance()
                else:
                    self.add_token(TokenType.SLASH)
            # "Meaningless" characters
            case " " | "\r" | "\t":
                pass
            case "\n":
                self.line += 1
            # Literals
            case '"':
                self.string()
            case _:
                if self.is_digit(char):
                    self.number()
                else:
                    error.error(self.line, "Unexpected character.")

    def scan_tokens(self) -> list[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_single_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)
