from typing import Any, Optional

import pylox.error as error
from pylox.scanner import Token


class Environment:
    __slots__ = ("values", "enclosing")

    def __init__(self, enclosing: Optional["Environment"] = None) -> None:
        self.values: dict[str, Any] = {}
        self.enclosing = enclosing

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def get(self, name: Token) -> Any:
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise error.LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def assign(self, name: Token, value: Any) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return
        raise error.LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")
