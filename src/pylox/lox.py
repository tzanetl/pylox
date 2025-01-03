from pylox.ast_printer import AstPrinter
from pylox.error import HadError
from pylox.parser import Parser
from pylox.scanner import Scanner


def run(source: str) -> None:
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    expression = parser.parse()

    # Stop of there was a syntax error
    if HadError.had_error:
        return

    assert expression is not None

    print(AstPrinter().print(expression))
