import sys


class HadError:
    had_error = False


def report(line: int, where: str, message: str) -> None:
    print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
    HadError.had_error = True


def error(line: int, message: str) -> None:
    report(line, "", message)
