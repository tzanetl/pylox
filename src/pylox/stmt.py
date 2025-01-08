from abc import ABC, abstractmethod

from pylox.expr import Expr
from pylox.scanner import Token


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: "StmtVisitor"):  # noqa: U100
        raise NotImplementedError()


class Expression(Stmt):
    __slots___ = ("expression",)

    def __init__(self, expression: Expr) -> None:
        super().__init__()
        self.expression = expression

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_expression_stmt(self)


class Print(Stmt):
    __slots___ = ("expression",)

    def __init__(self, expression: Expr) -> None:
        super().__init__()
        self.expression = expression

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_print_stmt(self)


class Var(Stmt):
    __slots___ = ("name", "initializer")

    def __init__(self, name: Token, initializer: Expr | None) -> None:
        super().__init__()
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_var_stmt(self)


class StmtVisitor(ABC):
    @abstractmethod
    def visit_expression_stmt(self, stmt: Expression):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_print_stmt(self, stmt: Print):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_var_stmt(self, stmt: Var):  # noqa: U100
        raise NotImplementedError()
