from abc import ABC, abstractmethod
from typing import Optional

from pylox import expr
from pylox.scanner import Token


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: "StmtVisitor"):  # noqa: U100
        raise NotImplementedError()


class Block(Stmt):
    """Block statement"""

    __slots___ = ("statements",)

    def __init__(self, statements: list[Stmt]) -> None:
        super().__init__()
        self.statements = statements

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_block_stmt(self)


class Class(Stmt):
    """Class statement"""

    __slots___ = ("name", "superclass", "methods")

    def __init__(self, name: Token, superclass: "expr.Variable" | None, methods: list["Function"]) -> None:
        super().__init__()
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_class_stmt(self)


class Break(Stmt):
    """Break statement"""

    __slots___ = ()

    def __init__(self) -> None:
        super().__init__()

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_break_stmt(self)


class Expression(Stmt):
    """Expression statement"""

    __slots___ = ("expression",)

    def __init__(self, expression: "expr.Expr") -> None:
        super().__init__()
        self.expression = expression

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_expression_stmt(self)


class Function(Stmt):
    """Function statement"""

    __slots___ = ("name", "function")

    def __init__(self, name: Token, function: "expr.Lambda") -> None:
        super().__init__()
        self.name = name
        self.function = function

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_function_stmt(self)


class If(Stmt):
    """If statement"""

    __slots___ = ("condition", "then_branch", "else_branch")

    def __init__(self, condition: "expr.Expr", then_branch: Stmt, else_branch: Stmt | None) -> None:
        super().__init__()
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_if_stmt(self)


class Print(Stmt):
    """Print statement"""

    __slots___ = ("expression",)

    def __init__(self, expression: "expr.Expr") -> None:
        super().__init__()
        self.expression = expression

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_print_stmt(self)


class Return(Stmt):
    """Return statement"""

    __slots___ = ("keyword", "value")

    def __init__(self, keyword: Token, value: Optional["expr.Expr"]) -> None:
        super().__init__()
        self.keyword = keyword
        self.value = value

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_return_stmt(self)


class Var(Stmt):
    """Var statement"""

    __slots___ = ("name", "initializer")

    def __init__(self, name: Token, initializer: Optional["expr.Expr"]) -> None:
        super().__init__()
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_var_stmt(self)


class While(Stmt):
    """While statement"""

    __slots___ = ("condition", "body")

    def __init__(self, condition: "expr.Expr", body: Stmt) -> None:
        super().__init__()
        self.condition = condition
        self.body = body

    def accept(self, visitor: "StmtVisitor"):
        return visitor.visit_while_stmt(self)


class StmtVisitor(ABC):
    @abstractmethod
    def visit_block_stmt(self, stmt: Block):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_class_stmt(self, stmt: Class):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_break_stmt(self, stmt: Break):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_expression_stmt(self, stmt: Expression):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_function_stmt(self, stmt: Function):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_if_stmt(self, stmt: If):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_print_stmt(self, stmt: Print):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_return_stmt(self, stmt: Return):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_var_stmt(self, stmt: Var):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_while_stmt(self, stmt: While):  # noqa: U100
        raise NotImplementedError()
