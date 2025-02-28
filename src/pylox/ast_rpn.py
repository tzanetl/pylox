# type: ignore
"""Reverse Polish Notation for AST

Chapter 5, Challenge 3
"""

from pylox.expr import Binary, ExprVisitor, Expr, Grouping, Literal, Unary
from pylox.scanner import Token, TokenType


class RPNPrinter(ExprVisitor):
    def print(self, expr: Expr) -> str:
        return expr.accept(self)

    def visit_binary_expr(self, expr: Binary) -> str:
        return f"{expr.left.accept(self)} {expr.right.accept(self)} {expr.operator.lexeme}"

    def visit_grouping_expr(self, expr: Grouping) -> str:
        return expr.expression.accept(self)

    def visit_literal_expr(self, expr: Literal) -> str:
        if expr.value is None:
            return "nil"
        return str(expr.value)

    def visit_unary_expr(self, expr: Unary) -> str:
        return f"{expr.operator.lexeme}{expr.right.accept(self)}"


def main() -> None:
    # (1 + 2) * (4 - 3)
    expression = Binary(
        Grouping(Binary(Literal(1), Token(TokenType.PLUS, "+", None, 1), Literal(2))),
        Token(TokenType.STAR, "*", None, 1),
        Grouping(Binary(Literal(4), Token(TokenType.MINUS, "-", None, 1), Literal(3))),
    )
    # 1 2 + 4 3 - *
    print(RPNPrinter().print(expression))


if __name__ == "__main__":
    main()
