import enum
from collections import deque
from typing import overload

from pylox import error
from pylox.expr import (
    Assign,
    Binary,
    Call,
    Conditional,
    Expr,
    ExprVisitor,
    Grouping,
    Lambda,
    Literal,
    Logical,
    Unary,
    Variable,
)
from pylox.interpreter import Interpreter
from pylox.scanner import Token
from pylox.stmt import (
    Block,
    Break,
    Expression,
    Function,
    If,
    Print,
    Return,
    Stmt,
    StmtVisitor,
    Var,
    While,
)


class FunctionType(enum.Enum):
    NONE = enum.auto()
    FUNCTION = enum.auto()


class Resolver(ExprVisitor, StmtVisitor):
    __slots__ = (
        "interpreter",
        "scopes",
        "currect_function",
    )

    def __init__(self, interpreter: Interpreter):
        super().__init__()
        self.interpreter = interpreter
        # dict[<variable name>: <is defined>]
        self.scopes: deque[dict[str, bool]] = deque()
        self.currect_function = FunctionType.NONE

    @overload
    def resolve(self, target: list[Stmt]) -> None:  # noqa: U100
        pass

    @overload
    def resolve(self, target: Stmt) -> None:  # noqa: U100
        pass

    @overload
    def resolve(self, target: Expr) -> None:  # noqa: U100
        pass

    def resolve(self, target: list[Stmt] | Stmt | Expr) -> None:
        if isinstance(target, Expr):
            target.accept(self)
        elif isinstance(target, Stmt):
            target.accept(self)
        else:
            for stmt in target:
                self.resolve(stmt)

    def resolve_local(self, expr: Expr, name: Token) -> None:
        for i, scope in enumerate(self.scopes):
            if name.lexeme in scope:
                self.interpreter.resolve(expr, len(self.scopes) - 1 - i)
                return

    def resolve_function(self, function: Lambda, ftype: FunctionType) -> None:
        enclosing_function = self.currect_function
        self.currect_function = ftype

        self.begin_scope()
        for p in function.params:
            self.declare(p)
            self.define(p)
        self.resolve(function.body)
        self.end_scope()

        self.currect_function = enclosing_function

    def begin_scope(self) -> None:
        self.scopes.append({})

    def end_scope(self) -> None:
        self.scopes.pop()

    def declare(self, name: Token) -> None:
        if not len(self.scopes):
            return
        if name.lexeme in self.scopes[-1]:
            error.error(name, "Already a variable with this name in this scope.")
        self.scopes[-1][name.lexeme] = False

    def define(self, name: Token) -> None:
        if not len(self.scopes):
            return
        self.scopes[-1][name.lexeme] = True

    def visit_block_stmt(self, stmt: Block) -> None:
        self.begin_scope()
        self.resolve(stmt.statements)
        self.end_scope()

    def visit_var_stmt(self, stmt: Var) -> None:
        self.declare(stmt.name)
        if stmt.initializer is not None:
            self.resolve(stmt.initializer)
        self.define(stmt.name)

    def visit_function_stmt(self, stmt: Function) -> None:
        self.declare(stmt.name)
        self.define(stmt.name)
        self.resolve_function(stmt.function, FunctionType.FUNCTION)

    def visit_expression_stmt(self, stmt: Expression) -> None:
        self.resolve(stmt.expression)

    def visit_if_stmt(self, stmt: If) -> None:
        self.resolve(stmt.condition)
        self.resolve(stmt.then_branch)
        if stmt.else_branch is not None:
            self.resolve(stmt.else_branch)

    def visit_print_stmt(self, stmt: Print) -> None:
        self.resolve(stmt.expression)

    def visit_return_stmt(self, stmt: Return) -> None:
        if self.currect_function == FunctionType.NONE:
            error.error(stmt.keyword, "Can't return from top-level code.")

        if stmt.value is not None:
            self.resolve(stmt.value)

    def visit_while_stmt(self, stmt: While) -> None:
        self.resolve(stmt.condition)
        self.resolve(stmt.body)

    def visit_break_stmt(self, stmt: Break) -> None:  # noqa: U100
        pass

    def visit_variable_expr(self, expr: Variable) -> None:
        if len(self.scopes) and self.scopes[-1][expr.name.lexeme] is False:
            error.error(expr.name, "Can't read local variable in its own initializer.")
        self.resolve_local(expr, expr.name)

    def visit_assign_expr(self, expr: Assign) -> None:
        self.resolve(expr.value)
        self.resolve_local(expr, expr.name)

    def visit_lambda_expr(self, expr: Lambda) -> None:
        self.resolve_function(expr, FunctionType.FUNCTION)

    def visit_binary_expr(self, expr: Binary) -> None:
        self.resolve(expr.left)
        self.resolve(expr.right)

    def visit_call_expr(self, expr: Call) -> None:
        self.resolve(expr.callee)
        for a in expr.arguments:
            self.resolve(a)

    def visit_grouping_expr(self, expr: Grouping) -> None:
        self.resolve(expr.expression)

    def visit_literal_expr(self, expr: Literal) -> None:  # noqa: U100
        pass

    def visit_logical_expr(self, expr: Logical) -> None:
        self.resolve(expr.left)
        self.resolve(expr.right)

    def visit_unary_expr(self, expr: Unary) -> None:
        self.resolve(expr.right)

    def visit_conditional_expr(self, expr: Conditional) -> None:
        self.resolve(expr.condition)
        self.resolve(expr.if_true)
        self.resolve(expr.if_false)
