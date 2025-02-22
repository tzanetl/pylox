from collections import deque
from typing import overload

from pylox import error
from pylox.expr import Assign, Expr, ExprVisitor, Variable
from pylox.interpreter import Interpreter
from pylox.scanner import Token
from pylox.stmt import Block, Stmt, StmtVisitor, Var


class Resolver(ExprVisitor, StmtVisitor):
    def __init__(self, interpreter: Interpreter):
        super().__init__()
        self.interpreter = interpreter
        # dict[<variable name>: <is defined>]
        self.scopes: deque[dict[str, bool]] = deque()

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

    def begin_scope(self) -> None:
        self.scopes.append({})

    def end_scope(self) -> None:
        self.scopes.pop()

    def declare(self, name: Token) -> None:
        if not len(self.scopes):
            return
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

    def visit_variable_expr(self, expr: Variable) -> None:
        if len(self.scopes) and self.scopes[-1][expr.name.lexeme] is False:
            error.error(expr.name, "Can't read local variable in its own initializer.")
        self.resolve_local(expr, expr.name)

    def visit_assign_expr(self, expr: Assign) -> None:
        self.resolve(expr.value)
        self.resolve_local(expr, expr.name)
