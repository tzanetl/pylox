# type: ignore

from pylox.expr import Binary, Conditional, Expr, ExprVisitor, Grouping, Literal, Unary
from pylox.scanner import Token, TokenType


class AstPrinter(ExprVisitor):
    def print(self, expr: Expr) -> str:
        return expr.accept(self)

    def visit_binary_expr(self, expr: Binary) -> str:
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_grouping_expr(self, expr: Grouping) -> str:
        return self.parenthesize("group", expr.expression)

    def visit_literal_expr(self, expr: Literal) -> str:
        if expr.value is None:
            return "nil"
        return str(expr.value)

    def visit_unary_expr(self, expr: Unary) -> str:
        return self.parenthesize(expr.operator.lexeme, expr.right)

    def visit_conditional_expr(self, expr: Conditional) -> str:
        return self.parenthesize("conditional", expr.condition, expr.if_true, expr.if_false)

    def parenthesize(self, name: str, *exprs: Expr) -> str:
        expr_str = " ".join(str(e.accept(self)) for e in exprs)
        return f"({name} {expr_str})"


# Just a sample main from 5.4
def main() -> None:
    expressions = Binary(
        Unary(
            Token(TokenType.MINUS, "-", None, 1),
            Literal(123),
        ),
        Token(TokenType.STAR, "*", None, 1),
        Grouping(Literal(45.67)),
    )
    print(AstPrinter().print(expressions))


if __name__ == "__main__":
    main()
