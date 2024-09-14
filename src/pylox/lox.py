from .scanner import Scanner


def run(source: str):
    scanner = Scanner(source)
    for token in scanner.scan_tokens():
        print(token)
