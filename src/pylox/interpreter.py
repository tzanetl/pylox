from typing import Any

import pylox.error as error
from pylox.expr import Binary, Conditional, Expr, ExprVisitor, Grouping, Literal, Unary
from pylox.scanner import Token, TokenType


class Interpreter(ExprVisitor):
    def interpret(self, expr: Expr) -> None:
        try:
            value = self.evaluate(expr)
            print(stringify(value))
        except error.LoxRuntimeError as exc:
            error.runtime_error(exc)

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
                if isinstance(left, str) and isinstance(right, str):
                    return str(left) + str(right)
                raise error.LoxRuntimeError(
                    expr.operator, "Operands must be two numbers or two strings."
                )
            case TokenType.MINUS:
                check_number_operand2(expr.operator, left, right)
                return float(left) - float(right)
            case TokenType.SLASH:
                check_number_operand2(expr.operator, left, right)
                return float(left) / float(right)
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
