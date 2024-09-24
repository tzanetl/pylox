from abc import ABC

from pylox.scanner import Token


class Expr(ABC):
    pass


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        super().__init__()
        self.left = left
        self.operator = operator
        self.right = right
