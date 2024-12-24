from abc import ABC, abstractmethod
from typing import Any

from pylox.scanner import Token


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: "ExprVisitor"):  # noqa: U100
        raise NotImplementedError()


class Binary(Expr):
    __slots___ = ("left", "operator", "right")

    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        super().__init__()
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_binary_expr(self)


class Grouping(Expr):
    __slots___ = ("expression",)

    def __init__(self, expression: Expr) -> None:
        super().__init__()
        self.expression = expression

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_grouping_expr(self)


class Literal(Expr):
    __slots___ = ("value",)

    def __init__(self, value: Any) -> None:
        super().__init__()
        self.value = value

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_literal_expr(self)


class Unary(Expr):
    __slots___ = ("operator", "right")

    def __init__(self, operator: Token, right: Expr) -> None:
        super().__init__()
        self.operator = operator
        self.right = right

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_unary_expr(self)


class ExprVisitor(ABC):
    @abstractmethod
    def visit_binary_expr(self, expr: Binary):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_grouping_expr(self, expr: Grouping):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_literal_expr(self, expr: Literal):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_unary_expr(self, expr: Unary):  # noqa: U100
        raise NotImplementedError()
