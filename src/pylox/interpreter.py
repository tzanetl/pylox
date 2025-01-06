from typing import Any

from pylox.expr import Binary, Conditional, Expr, ExprVisitor, Grouping, Literal, Unary
from pylox.scanner import TokenType


class Interpreter(ExprVisitor):
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
                return -float(right)
            case TokenType.BANG:
                return not is_truthy(right)

        raise NotImplementedError("unreachable")

    def visit_binary_expr(self, expr: Binary) -> float | str | bool:
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        match expr.operator.type:
            case TokenType.GREATER:
                return float(left) > float(right)
            case TokenType.GREATER_EQUAL:
                return float(left) >= float(right)
            case TokenType.LESS:
                return float(left) < float(right)
            case TokenType.LESS_EQUAL:
                return float(left) <= float(right)
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return float(left) + float(right)
                if isinstance(left, str) and isinstance(right, str):
                    return str(left) + str(right)
            case TokenType.MINUS:
                return float(left) - float(right)
            case TokenType.SLASH:
                return float(left) / float(right)
            case TokenType.STAR:
                return float(left) * float(right)
            case TokenType.BANG_EQUAL:
                return not is_equal(left, right)
            case TokenType.EQUAL_EQUAL:
                return is_equal(left, right)

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
