from typing import Any

import pylox.error as error
from pylox.scanner import Token


class Environment:
    __slots__ = ("values",)

    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def get(self, name: Token) -> Any:
        if name.lexeme in self.values:
            return self.values[name.lexeme]
        raise error.LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def assign(self, name: Token, value: Any) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return
        raise error.LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")
