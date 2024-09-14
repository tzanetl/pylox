from collections.abc import Generator


class Token:
    def __init__(self) -> None:
        pass


class Scanner:
    __slots__ = "source"

    def __init__(self, source: str) -> None:
        self.source = source

    def scan_tokens(self) -> Generator[Token, None, None]:
        yield Token()
