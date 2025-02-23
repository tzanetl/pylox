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

    def ancestor(self, distance: int) -> "Environment":
        environment = self
        for _ in range(distance):
            enclosing = environment.enclosing
            if enclosing is None:
                raise RuntimeError(
                    "Corrupted interpreter state, enclosing environemnt was not found"
                )
            environment = enclosing
        return environment

    def get(self, name: Token) -> Any:
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise error.LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def get_at(self, distance: int, name: str) -> Any:
        return self.ancestor(distance).values.get(name)

    def assign(self, name: Token, value: Any) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            return self.enclosing.assign(name, value)

        raise error.LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def assign_at(self, distance: int, name: Token, value: Any) -> None:
        self.ancestor(distance).values[name.lexeme] = value
