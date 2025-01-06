from pylox.error import HadError
from pylox.interpreter import Interpreter
from pylox.parser import Parser
from pylox.scanner import Scanner

INTERPRETER = Interpreter()


def run(source: str) -> None:
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    expression = parser.parse()

    # Stop of there was a syntax error
    if HadError.had_error:
        return

    assert expression is not None

    INTERPRETER.interpret(expression)
