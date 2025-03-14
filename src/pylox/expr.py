from abc import ABC, abstractmethod
from typing import Any

from pylox import stmt
from pylox.scanner import Token


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: "ExprVisitor"):  # noqa: U100
        raise NotImplementedError()


class Assign(Expr):
    """Assign expression"""

    __slots___ = ("name", "value")

    def __init__(self, name: Token, value: Expr) -> None:
        super().__init__()
        self.name = name
        self.value = value

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_assign_expr(self)


class Binary(Expr):
    """Binary expression"""

    __slots___ = ("left", "operator", "right")

    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        super().__init__()
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_binary_expr(self)


class Call(Expr):
    """Call expression"""

    __slots___ = ("callee", "paren", "arguments")

    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]) -> None:
        super().__init__()
        self.callee = callee
        self.paren = paren
        self.arguments = arguments

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_call_expr(self)


class Get(Expr):
    """Get expression"""

    __slots___ = ("object", "name")

    def __init__(self, object: Expr, name: Token) -> None:
        super().__init__()
        self.object = object
        self.name = name

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_get_expr(self)


class Grouping(Expr):
    """Grouping expression"""

    __slots___ = ("expression",)

    def __init__(self, expression: Expr) -> None:
        super().__init__()
        self.expression = expression

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_grouping_expr(self)


class Lambda(Expr):
    """Lambda expression"""

    __slots___ = ("params", "body")

    def __init__(self, params: list[Token], body: list[stmt.Stmt]) -> None:
        super().__init__()
        self.params = params
        self.body = body

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_lambda_expr(self)


class Literal(Expr):
    """Literal expression"""

    __slots___ = ("value",)

    def __init__(self, value: Any) -> None:
        super().__init__()
        self.value = value

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_literal_expr(self)


class Logical(Expr):
    """Logical expression"""

    __slots___ = ("left", "operator", "right")

    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        super().__init__()
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_logical_expr(self)


class Set(Expr):
    """Set expression"""

    __slots___ = ("object", "name", "value")

    def __init__(self, object: Expr, name: Token, value: Expr) -> None:
        super().__init__()
        self.object = object
        self.name = name
        self.value = value

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_set_expr(self)


class Super(Expr):
    """Super expression"""

    __slots___ = ("keyword", "method")

    def __init__(self, keyword: Token, method: Token) -> None:
        super().__init__()
        self.keyword = keyword
        self.method = method

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_super_expr(self)


class This(Expr):
    """This expression"""

    __slots___ = ("keyword",)

    def __init__(self, keyword: Token) -> None:
        super().__init__()
        self.keyword = keyword

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_this_expr(self)


class Unary(Expr):
    """Unary expression"""

    __slots___ = ("operator", "right")

    def __init__(self, operator: Token, right: Expr) -> None:
        super().__init__()
        self.operator = operator
        self.right = right

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_unary_expr(self)


class Conditional(Expr):
    """Conditional expression"""

    __slots___ = ("condition", "if_true", "if_false")

    def __init__(self, condition: Expr, if_true: Expr, if_false: Expr) -> None:
        super().__init__()
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_conditional_expr(self)


class Variable(Expr):
    """Variable expression"""

    __slots___ = ("name",)

    def __init__(self, name: Token) -> None:
        super().__init__()
        self.name = name

    def accept(self, visitor: "ExprVisitor"):
        return visitor.visit_variable_expr(self)


class ExprVisitor(ABC):
    @abstractmethod
    def visit_assign_expr(self, expr: Assign):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_binary_expr(self, expr: Binary):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_call_expr(self, expr: Call):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_get_expr(self, expr: Get):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_grouping_expr(self, expr: Grouping):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_lambda_expr(self, expr: Lambda):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_literal_expr(self, expr: Literal):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_logical_expr(self, expr: Logical):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_set_expr(self, expr: Set):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_super_expr(self, expr: Super):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_this_expr(self, expr: This):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_unary_expr(self, expr: Unary):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_conditional_expr(self, expr: Conditional):  # noqa: U100
        raise NotImplementedError()

    @abstractmethod
    def visit_variable_expr(self, expr: Variable):  # noqa: U100
        raise NotImplementedError()
