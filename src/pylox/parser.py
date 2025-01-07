from typing import Any, Callable

import pylox.error as error
from pylox.expr import Binary, Conditional, Expr, Grouping, Literal, Unary
from pylox.scanner import Token, TokenType
from pylox.stmt import Expression, Print, Stmt


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

    def parse(self) -> list[Stmt]:
        statements = []
        while not self.is_at_end():
            statements.append(self.statement())
        return statements

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
        return self.peek().type == TokenType.EOF

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

    def error(self, token: Token, message: str) -> error.ParseError:
        error.error(token, message)
        return error.ParseError()

    def consume(self, t: TokenType, message: str) -> Token:
        if self.check(t):
            return self.advance()
        raise self.error(self.peek(), message)

    def expression(self) -> Expr:
        return self.comma()

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

        # Chapter 6 challenge 3
        # Missing left hand expression in binary operator
        if self.match(
            TokenType.BANG_EQUAL,
            TokenType.EQUAL_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.PLUS,
            TokenType.SLASH,
            TokenType.STAR,
        ):
            # Raising an error, unlike the example, since returning None from here causes a lot of
            # problems with type checking
            # https://github.com/munificent/craftinginterpreters/blob/master/note/answers/chapter06_parsing.md
            raise self.error(self.previous(), "Missing left-hand operand.")

        raise self.error(self.peek(), "Expected expression.")

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

    # Chapter 6 challenge 2
    # conditional -> equality ( "?" expression ":" expression )? ;
    def conditional(self) -> Expr:
        expr = self.equality()

        if self.match(TokenType.TERNARY):
            if_true = self.expression()
            self.consume(
                TokenType.COLON, "Expect ':' after if true branch of conditional expression."
            )
            if_false = self.expression()
            return Conditional(expr, if_true, if_false)

        return expr

    # Chapter 6 challenge 1
    # comma -> conditional ("," conditional)* ;
    @lasbo(conditional, TokenType.COMMA)
    def comma(self):
        pass

    def statement(self) -> Stmt:
        if self.match(TokenType.PRINT):
            return self.print_statement()
        return self.expression_statement()

    def print_statement(self) -> Print:
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Print(value)

    def expression_statement(self) -> Expression:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(expr)
