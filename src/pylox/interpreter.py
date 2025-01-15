from typing import Any

import pylox.error as error
from pylox.environment import Environment
from pylox.expr import (
    Assign,
    Binary,
    Conditional,
    Expr,
    ExprVisitor,
    Grouping,
    Literal,
    Unary,
    Variable,
)
from pylox.scanner import Token, TokenType
from pylox.stmt import Block, Expression, Print, Stmt, StmtVisitor, Var


class Unassigned:
    """Type for unassigned variables"""


UNASSIGNED = Unassigned()


class Interpreter(ExprVisitor, StmtVisitor):
    __slots__ = ("environment", "is_repl")

    def __init__(self) -> None:
        super().__init__()
        self.environment = Environment()
        self.is_repl = False

    def interpret(self, statements: list[Stmt]) -> None:
        try:
            for stmt in statements:
                self.execute(stmt)
        except error.LoxRuntimeError as exc:
            error.runtime_error(exc)

    def execute(self, stmt: Stmt) -> None:
        stmt.accept(self)

    def execute_block(self, statements: list[Stmt], environment: Environment) -> None:
        previous = self.environment
        try:
            self.environment = environment
            for stmt in statements:
                self.execute(stmt)
        finally:
            self.environment = previous

    def evaluate(self, expr: Expr) -> Any:
        return expr.accept(self)

    def visit_literal_expr(self, expr: Literal) -> Any:
        return expr.value

    def visit_grouping_expr(self, expr: Grouping) -> Any:
        return self.evaluate(expr.expression)

    def visit_unary_expr(self, expr: Unary) -> float | bool:
        right = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.MINUS:
                check_number_operand(expr.operator, right)
                return -float(right)
            case TokenType.BANG:
                return not is_truthy(right)

        raise NotImplementedError("unreachable")

    def visit_binary_expr(self, expr: Binary) -> float | str | bool:
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.GREATER:
                check_number_operand2(expr.operator, left, right)
                return float(left) > float(right)
            case TokenType.GREATER_EQUAL:
                check_number_operand2(expr.operator, left, right)
                return float(left) >= float(right)
            case TokenType.LESS:
                check_number_operand2(expr.operator, left, right)
                return float(left) < float(right)
            case TokenType.LESS_EQUAL:
                check_number_operand2(expr.operator, left, right)
                return float(left) <= float(right)
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return float(left) + float(right)
                if isinstance(left, str) or isinstance(right, str):
                    return stringify(left) + stringify(right)
                raise error.LoxRuntimeError(
                    expr.operator, "Operands must be two numbers or two strings."
                )
            case TokenType.MINUS:
                check_number_operand2(expr.operator, left, right)
                return float(left) - float(right)
            case TokenType.SLASH:
                check_number_operand2(expr.operator, left, right)
                try:
                    return float(left) / float(right)
                except ZeroDivisionError:
                    raise error.LoxRuntimeError(expr.operator, "Cannot divide by zero.")
            case TokenType.STAR:
                check_number_operand2(expr.operator, left, right)
                return float(left) * float(right)
            case TokenType.BANG_EQUAL:
                return not is_equal(left, right)
            case TokenType.EQUAL_EQUAL:
                return is_equal(left, right)
            case TokenType.COMMA:
                # From Wikipedia https://en.wikipedia.org/wiki/Comma_operator:
                # ... the comma operator is a binary operator that evaluates its first operand and
                # discards the result, and then evaluates the second operand and returns this value
                return right

        raise NotImplementedError("unreachable")

    def visit_conditional_expr(self, expr: Conditional) -> Any:
        condition = self.evaluate(expr.condition)
        if is_truthy(condition):
            return self.evaluate(expr.if_true)
        return self.evaluate(expr.if_false)

    def visit_variable_expr(self, expr: Variable) -> Any:
        value = self.environment.get(expr.name)
        if value is UNASSIGNED:
            raise error.LoxRuntimeError(expr.name, f"Variable '{expr.name.lexeme}' is unassigned.")
        return value

    def visit_assign_expr(self, expr: Assign) -> Any:
        value = self.evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    def visit_expression_stmt(self, stmt: Expression) -> None:
        value = self.evaluate(stmt.expression)
        # Chapter 8 challenge 1
        if self.is_repl:
            print(stringify(value))

    def visit_print_stmt(self, stmt: Print) -> None:
        value = self.evaluate(stmt.expression)
        print(stringify(value))

    def visit_var_stmt(self, stmt: Var) -> None:
        value = UNASSIGNED
        if stmt.initializer is not None:
            value = self.evaluate(stmt.initializer)
        self.environment.define(stmt.name.lexeme, value)

    def visit_block_stmt(self, stmt: Block) -> None:
        self.execute_block(stmt.statements, Environment(self.environment))


def is_truthy(value: Any) -> bool:
    """false and nill are falsey, everything else is truthy"""
    if value is None:
        return False
    if isinstance(value, bool):
        return bool(value)
    return True


def is_equal(a: Any, b: Any) -> bool:
    # None is only equal to None
    return a == b


def check_number_operand(operator: Token, operand: Any) -> None:
    if isinstance(operand, float):
        return
    raise error.LoxRuntimeError(operator, "Operand must be a number.")


def check_number_operand2(operator: Token, left: Any, right: Any) -> None:
    if isinstance(left, float) and isinstance(right, float):
        return
    raise error.LoxRuntimeError(operator, "Operands must be numbers.")


def stringify(value: Any) -> str:
    if value is None:
        return "nil"

    if isinstance(value, float):
        text = str(value)
        if text.endswith(".0"):
            text = text[:-2]
        return text

    if isinstance(value, bool):
        return str(value).lower()

    return str(value)
