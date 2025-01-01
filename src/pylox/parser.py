from typing import Any, Callable

from pylox.error import ParseError, error
from pylox.expr import Binary, Expr, Grouping, Literal, Unary
from pylox.scanner import Token, TokenType


def lasbo(
    getter: Callable[["Parser"], Expr], *types: TokenType
) -> Callable[[Any], Callable[["Parser"], Expr]]:
    """Generate code for parsing a Left-Associative Series of Binary Operators"""

    def decorator(_func: Callable[["Parser"], Expr]) -> Callable[["Parser"], Expr]:  # noqa: U101

        def inner(self: "Parser") -> Expr:
            expr = getter(self)

            while self.match(*types):
                operator = self.previous()
                right = getter(self)
                expr = Binary(expr, operator, right)

            return expr

        return inner

    return decorator


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def match(self, *types: TokenType) -> bool:
        """
        Check if current token is any of the tokens. Consume it if True and return equality result
        """
        for t in types:
            if self.check(t):
                self.advance()
                return True

        return False

    def check(self, t: TokenType) -> bool:
        """Check if current token is of type t"""
        if self.is_at_end():
            return False
        return self.peek().type == t

    def is_at_end(self) -> bool:
        return self.peek() == TokenType.EOF

    def advance(self) -> Token:
        """Consume current token"""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def peek(self) -> Token:
        return self.tokens[self.current]

    def synchronize(self) -> None:
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return

            match self.peek().type:
                case (
                    TokenType.CLASS
                    | TokenType.FUN
                    | TokenType.VAR
                    | TokenType.FOR
                    | TokenType.IF
                    | TokenType.WHILE
                    | TokenType.PRINT
                    | TokenType.RETURN
                ):
                    return

            self.advance()

    def error(self, token: Token, message: str) -> ParseError:
        error(token, message)
        return ParseError()

    def consume(self, t: TokenType, message: str) -> Token:
        if self.check(t):
            return self.advance()
        raise self.error(self.peek(), message)

    def expression(self) -> Expr:
        return self.equality()

    def primary(self) -> Expr:
        if self.match(TokenType.FALSE):
            return Literal(False)
        if self.match(TokenType.TRUE):
            return Literal(True)
        if self.match(TokenType.NIL):
            return Literal(None)

        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)

        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        raise NotImplementedError("Oh my goodness oh my damn!")

    def unary(self) -> Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)
        return self.primary()

    @lasbo(unary, TokenType.STAR, TokenType.SLASH)
    def factor(self):
        pass

    @lasbo(factor, TokenType.MINUS, TokenType.PLUS)
    def term(self):
        pass

    @lasbo(term, TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL)
    def comparison(self):
        pass

    @lasbo(comparison, TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL)
    def equality(self):
        pass
