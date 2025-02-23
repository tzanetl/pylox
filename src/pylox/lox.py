from pylox.error import HadError
from pylox.interpreter import Interpreter
from pylox.parser import Parser
from pylox.resolver import Resolver
from pylox.scanner import Scanner

INTERPRETER = Interpreter()


def run(source: str) -> None:
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    statements = parser.parse()

    # Stop of there was a syntax error
    if HadError.had_error:
        return

    # Stop if there was a resolution error.
    resolver = Resolver(INTERPRETER)
    resolver.resolve(statements)
    if HadError.had_error:
        return

    INTERPRETER.interpret(statements)
