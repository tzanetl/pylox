import sys
from typing import overload

from pylox.scanner import Token, TokenType


class PyloxError(Exception):
    """Base Exception"""


class ParseError(PyloxError):
    """Parser encountered an invalid token"""


class HadError:
    had_error = False


def report(line: int, where: str, message: str) -> None:
    print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
    HadError.had_error = True


@overload
def error(item: int, message: str) -> None:  # noqa: U100
    pass


@overload
def error(item: Token, message: str) -> None:  # noqa: U100
    pass


def error(item: int | Token, message: str) -> None:
    if isinstance(item, int):
        return _error_line(item, message)
    if isinstance(item, Token):
        return _error_token(item, message)
    raise ValueError(f"unknown item type {type(item)}")


def _error_line(line: int, message: str) -> None:
    report(line, "", message)


def _error_token(token: Token, message: str) -> None:
    if token.type == TokenType.EOF:
        report(token.line, " at end", message)
    else:
        report(token.line, f" at '{token.lexeme}'", message)
