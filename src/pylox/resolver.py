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
    Get,
    Grouping,
    Lambda,
    Literal,
    Logical,
    Set,
    Super,
    This,
    Unary,
    Variable,
)
from pylox.interpreter import Interpreter
from pylox.scanner import Token
from pylox.stmt import (
    Block,
    Break,
    Class,
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


class ClassType(enum.Enum):
    NONE = enum.auto()
    CLASS = enum.auto()
    SUBCLASS = enum.auto()


class FunctionType(enum.Enum):
    NONE = enum.auto()
    FUNCTION = enum.auto()
    INITIALIZER = enum.auto()
    METHOD = enum.auto()


class VariableStatus(enum.Enum):
    DECLARED = enum.auto()
    DEFINED = enum.auto()
    USED = enum.auto()


class Resolver(ExprVisitor, StmtVisitor):
    __slots__ = (
        "interpreter",
        "scopes",
        "current_class",
        "current_function",
    )

    def __init__(self, interpreter: Interpreter):
        super().__init__()
        self.interpreter = interpreter
        # dict[<variable name>: <is defined>]
        self.scopes: deque[dict[str, VariableStatus]] = deque()
        self.current_class = ClassType.NONE
        self.current_function = FunctionType.NONE

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

    def resolve_local(self, expr: Expr, name: Token, is_used: bool = False) -> None:
        for i, scope in enumerate(self.scopes):
            if name.lexeme in scope:
                self.interpreter.resolve(expr, len(self.scopes) - 1 - i)

                if is_used:
                    scope[name.lexeme] = VariableStatus.USED

                return

    def resolve_function(self, function: Lambda, ftype: FunctionType) -> None:
        enclosing_function = self.current_function
        self.current_function = ftype

        self.begin_scope()
        for p in function.params:
            self.declare(p)
            self.define(p)
        self.resolve(function.body)
        self.end_scope()

        self.current_function = enclosing_function

    def begin_scope(self) -> None:
        self.scopes.append({})

    def end_scope(self) -> None:
        self.scopes.pop()

    def declare(self, name: Token) -> None:
        if not len(self.scopes):
            return
        if name.lexeme in self.scopes[-1]:
            error.error(name, "Already a variable with this name in this scope.")
        self.scopes[-1][name.lexeme] = VariableStatus.DECLARED

    def define(self, name: Token) -> None:
        if not len(self.scopes):
            return
        self.scopes[-1][name.lexeme] = VariableStatus.DEFINED

    def visit_block_stmt(self, stmt: Block) -> None:
        self.begin_scope()
        self.resolve(stmt.statements)
        self.end_scope()

    def visit_var_stmt(self, stmt: Var) -> None:
        self.declare(stmt.name)
        if stmt.initializer is not None:
            self.resolve(stmt.initializer)
        self.define(stmt.name)

    def visit_class_stmt(self, stmt: Class) -> None:
        enclosing_class = self.current_class
        self.current_class = ClassType.CLASS

        self.declare(stmt.name)

        if stmt.superclass is not None and stmt.name.lexeme == stmt.superclass.name.lexeme:
            error.error(stmt.superclass.name, "A class can't inherit from itself.")

        if stmt.superclass is not None:
            self.current_class = ClassType.SUBCLASS
            self.resolve(stmt.superclass)

        if stmt.superclass is not None:
            self.begin_scope()
            self.scopes[-1]["super"] = VariableStatus.USED

        self.begin_scope()
        self.scopes[-1]["this"] = VariableStatus.USED

        for method in stmt.methods:
            declaration = FunctionType.METHOD
            if method.name.lexeme == "init":
                declaration = FunctionType.INITIALIZER
            self.resolve_function(method.function, declaration)

        self.define(stmt.name)
        self.end_scope()

        if stmt.superclass is not None:
            self.end_scope()

        self.current_class = enclosing_class

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
        if self.current_function == FunctionType.NONE:
            error.error(stmt.keyword, "Can't return from top-level code.")

        if stmt.value is not None:
            if self.current_function == FunctionType.INITIALIZER:
                error.error(stmt.keyword, "Can't return a value from an initializer.")
            self.resolve(stmt.value)

    def visit_while_stmt(self, stmt: While) -> None:
        self.resolve(stmt.condition)
        self.resolve(stmt.body)

    def visit_break_stmt(self, stmt: Break) -> None:  # noqa: U100
        pass

    def visit_variable_expr(self, expr: Variable) -> None:
        if len(self.scopes) and self.scopes[-1].get(expr.name.lexeme) == VariableStatus.DECLARED:
            error.error(expr.name, "Can't read local variable in its own initializer.")
        self.resolve_local(expr, expr.name, True)

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

    def visit_get_expr(self, expr: Get) -> None:
        self.resolve(expr.object)

    def visit_set_expr(self, expr: Set) -> None:
        self.resolve(expr.value)
        self.resolve(expr.object)

    def visit_super_expr(self, expr: Super) -> None:
        if self.current_class == ClassType.NONE:
            error.error(expr.keyword, "Can't use 'super' outside of a class.")
        elif self.current_class != ClassType.SUBCLASS:
            error.error(expr.keyword, "Can't use 'super' in a class with no superclass.")

        self.resolve_local(expr, expr.keyword)

    def visit_this_expr(self, expr: This) -> None:
        if self.current_class == ClassType.NONE:
            error.error(expr.keyword, "Can't use 'this' outside of a class.")

        self.resolve_local(expr, expr.keyword)
