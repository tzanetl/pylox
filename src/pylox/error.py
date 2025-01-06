import sys
from typing import overload

import pylox.scanner as scanner


class PyloxError(Exception):
    """Base Exception"""


class ParseError(PyloxError):
    """Parser encountered an invalid token"""


class LoxRuntimeError(PyloxError):
    def __init__(self, token: scanner.Token, message: str) -> None:
        super().__init__(message)
        self.token = token


class HadError:
    had_error = False
    had_runtime_error = False


def report(line: int, where: str, message: str) -> None:
    print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
    HadError.had_error = True


@overload
def error(item: int, message: str) -> None:  # noqa: U100
    pass


@overload
def error(item: scanner.Token, message: str) -> None:  # noqa: U100
    pass


def error(item: int | scanner.Token, message: str) -> None:
    if isinstance(item, int):
        return _error_line(item, message)
    if isinstance(item, scanner.Token):
        return _error_token(item, message)
    raise ValueError(f"unknown item type {type(item)}")


def _error_line(line: int, message: str) -> None:
    report(line, "", message)


def _error_token(token: scanner.Token, message: str) -> None:
    if token.type == scanner.TokenType.EOF:
        report(token.line, " at end", message)
    else:
        report(token.line, f" at '{token.lexeme}'", message)


def runtime_error(exc: LoxRuntimeError) -> None:
    print(f"{exc}\n[line {exc.token.line}]")
    HadError.had_runtime_error = True
