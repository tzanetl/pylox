import sys

from .scanner import Scanner


class LoxException(Exception):
    """Base exception"""

    pass


class ErrorReported(LoxException):
    pass


def report(line: int, where: str, message: str) -> None:
    print(f"[line {line} ] Error{where}: {message}", file=sys.stderr)
    raise ErrorReported()


def error(line: int, message: str) -> None:
    report(line, "", message)


def run(source: str):
    scanner = Scanner(source)
    for token in scanner.scan_tokens():
        print(token)
