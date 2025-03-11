import enum
from typing import Any, Callable

import pylox.error as error
from pylox.expr import (
    Assign,
    Binary,
    Call,
    Conditional,
    Expr,
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
from pylox.scanner import Token, TokenType
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
    Var,
    While,
)


class InvalidDeclatation(Stmt):
    """Statement returned on invalid variable declaration statement"""

    def accept(self, _visitor: Any) -> None:  # noqa: U101
        # This should never be visited
        raise RuntimeError("cannot visit invalid declaration statement")


class FunctionKind(enum.StrEnum):
    FUNCTION = enum.auto()
    METHOD = enum.auto()
    LAMBDA = enum.auto()


def lasbo(
    getter: Callable[["Parser"], Expr], *types: TokenType
) -> Callable[[Any], Callable[["Parser"], Expr]]:
    """Generate code for parsing a Left-Associative Series of Binary Operators"""

    def decorator(_func: Callable[["Parser"], Expr]) -> Callable[["Parser"], Expr]:  # noqa: U101

        def inner(self: "Parser") -> Expr:
            expr = getter(self)

            while self.match(*types):
                operator = self.previous()
                right = getter(self)
                expr = Binary(expr, operator, right)

            return expr

        return inner

    return decorator


class Parser:
    """
    Expressions
    -----------
    expression      -> comma ;
    comma           -> assignment ( "," assignment )* ;
    assignment      -> ( call "." )? IDENTIFIER "=" assignment
                    | logic_or ;
    logic_or        -> logic_and ( "or" logic_and )* ;
    logic_and       -> conditional ( "and" conditional )* ;
    conditional     -> equality ( "?" expression ":" expression )? ;
    equality        -> comparison ( ( "!=" | "==" ) comparison )* ;
    comparison      -> term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
    term            -> factor ( ( "-" | "+" ) factor )* ;
    factor          -> unary ( ( "/" | "*" ) unary )* ;
    unary           -> ( "!" | "-" ) unary | call | lambda;
    call            -> primary ( "(" arguments? ")" | "." IDENTIFIER )* ;
    arguments       -> equality ( "," equality )* ;
    lambda          -> "fun" "(" parameters? ")" block ;
    primary         -> NUMBER | STRING | "true" | "false" | "nil" | "this"
                    | "(" expression ")"
                    | IDENTIFIER
                    | "super" "." IDENTIFIER ;

    Statements
    ----------
    program         -> declaration* EOF ;
    declaration     -> classDecl
                    | funDecl
                    | varDecl
                    | statement ;
    classDecl       -> "class" IDENTIFIER ( "<" IDENTIFIER )? "{" function* "}" ;
    funDecl         -> "fun" function ;
    function        -> IDENTIFIER "(" parameters? ")" block ;
    parameters      -> IDENTIFIER ( "," IDENTIFIER )* ;
    varDecl         -> "var" IDENTIFIER ( "=" expression )? ";" ;
    statement       -> exprStmt
                    | forStmt
                    | ifStmt
                    | printStmt
                    | returnStmt
                    | whileStmt
                    | breakStmt
                    | block ;
    exprStmt        -> expression ";" ;
    ifStmt          -> "if" "(" expression ")" statement ( "else" statement )? ;
    returnStmt      -> "return" expression? ";" ;
    printStmt       -> "print" expression ";" ;
    whileStmt       -> "while" "(" expression ")" statement ;
    forStmt         -> "for" "(" ( varDecl | exprStmt | ";" ) expression? ";" expression? ")"
                    statement ;
    block           -> "{" declaration* "}" ;
    """

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0
        self.loop_depth = 0

    def parse(self) -> list[Stmt]:
        statements = []
        while not self.is_at_end():
            statements.append(self.declaration())
        return statements

    def match(self, *types: TokenType) -> bool:
        """
        Check if current token is any of the tokens. Consume it if True and return equality result
        """
        for t in types:
            if self.check(t):
                self.advance()
                return True

        return False

    def check(self, t: TokenType) -> bool:
        """Check if current token is of type t"""
        if self.is_at_end():
            return False
        return self.peek().type == t

    def check2(self, t: TokenType, extra: int) -> bool:
        position = self.current + extra
        if not position < len(self.tokens):
            return False
        return self.tokens[position].type == t

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def advance(self) -> Token:
        """Consume current token"""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def peek(self) -> Token:
        return self.tokens[self.current]

    def synchronize(self) -> None:
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return

            match self.peek().type:
                case (
                    TokenType.CLASS
                    | TokenType.FUN
                    | TokenType.VAR
                    | TokenType.FOR
                    | TokenType.IF
                    | TokenType.WHILE
                    | TokenType.PRINT
                    | TokenType.RETURN
                ):
                    return

            self.advance()

    def error(self, token: Token, message: str) -> error.ParseError:
        error.error(token, message)
        return error.ParseError()

    def consume(self, t: TokenType, message: str) -> Token:
        if self.check(t):
            return self.advance()
        raise self.error(self.peek(), message)

    def expression(self) -> Expr:
        return self.comma()

    def assignment(self) -> Expr:
        expr = self.or_expression()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()
            if isinstance(expr, Variable):
                name = expr.name
                return Assign(name, value)
            elif isinstance(expr, Get):
                return Set(expr.object, expr.name, value)
            self.error(equals, "Invalid assignment target.")

        return expr

    def primary(self) -> Expr:
        if self.match(TokenType.FALSE):
            return Literal(False)

        if self.match(TokenType.TRUE):
            return Literal(True)

        if self.match(TokenType.NIL):
            return Literal(None)

        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)

        if self.match(TokenType.SUPER):
            keyword = self.previous()
            self.consume(TokenType.DOT, "Expect '.' after 'super'.")
            method = self.consume(TokenType.IDENTIFIER, "Expect superclass method name.")
            return Super(keyword, method)

        if self.match(TokenType.THIS):
            return This(self.previous())

        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous())

        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        # Chapter 6 challenge 3
        # Missing left hand expression in binary operator
        if self.match(
            TokenType.BANG_EQUAL,
            TokenType.EQUAL_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.PLUS,
            TokenType.SLASH,
            TokenType.STAR,
        ):
            # Raising an error, unlike the example, since returning None from here causes a lot of
            # problems with type checking
            # https://github.com/munificent/craftinginterpreters/blob/master/note/answers/chapter06_parsing.md
            raise self.error(self.previous(), "Missing left-hand operand.")

        raise self.error(self.peek(), "Expected expression.")

    def finish_call(self, callee: Expr) -> Call:
        arguments: list[Expr] = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    self.error(self.peek(), "Can't have more than 255 arguments.")

                # https://github.com/munificent/craftinginterpreters/issues/263#issuecomment-412353276
                arguments.append(self.equality())

                if not self.match(TokenType.COMMA):
                    break
        paren = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        return Call(callee, paren, arguments)

    def call(self) -> Expr:
        expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "Expect property name after '.'.")
                expr = Get(expr, name)
            else:
                break

        return expr

    def unary(self) -> Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)
        if self.match(TokenType.FUN):
            return self.lambda_expression()
        return self.call()

    @lasbo(unary, TokenType.STAR, TokenType.SLASH)
    def factor(self):
        pass

    @lasbo(factor, TokenType.MINUS, TokenType.PLUS)
    def term(self):
        pass

    @lasbo(term, TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL)
    def comparison(self):
        pass

    @lasbo(comparison, TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL)
    def equality(self):
        pass

    # Chapter 6 challenge 2
    def conditional(self) -> Expr:
        expr = self.equality()

        if self.match(TokenType.TERNARY):
            if_true = self.expression()
            self.consume(
                TokenType.COLON, "Expect ':' after if true branch of conditional expression."
            )
            if_false = self.expression()
            return Conditional(expr, if_true, if_false)

        return expr

    # Chapter 6 challenge 1
    @lasbo(assignment, TokenType.COMMA)
    def comma(self):
        pass

    def statement(self) -> Stmt:
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.BREAK):
            return self.break_statement()
        if self.match(TokenType.LEFT_BRACE):
            return Block(self.block())
        return self.expression_statement()

    def print_statement(self) -> Print:
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Print(value)

    def for_statement(self) -> Stmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        initializer: Stmt | None
        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        self.loop_depth += 1
        body = self.statement()
        self.loop_depth -= 1

        if increment is not None:
            body = Block([body, Expression(increment)])

        if condition is None:
            condition = Literal(True)
        body = While(condition, body)

        if initializer is not None:
            body = Block([initializer, body])

        return body

    def while_statement(self) -> While:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")
        self.loop_depth += 1
        body = self.statement()
        self.loop_depth -= 1
        return While(condition, body)

    def break_statement(self) -> Break:
        if self.loop_depth == 0:
            self.error(self.previous(), "Must be inside a loop to use 'break'.")
        self.consume(TokenType.SEMICOLON, "Expected ';' after 'break'.")
        return Break()

    def return_statement(self) -> Return:
        keyword = self.previous()
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Return(keyword, value)

    def expression_statement(self) -> Expression:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(expr)

    def declaration(self) -> Stmt:
        try:
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            if self.check2(TokenType.IDENTIFIER, 1) and self.match(TokenType.FUN):
                return self.function(FunctionKind.FUNCTION)
            if self.match(TokenType.VAR):
                return self.var_declaration()
            return self.statement()
        except error.ParseError:
            self.synchronize()
            return InvalidDeclatation()

    def class_declaration(self) -> Class:
        name = self.consume(TokenType.IDENTIFIER, "Expect class name.")

        superclass = None
        if self.match(TokenType.LESS):
            self.consume(TokenType.IDENTIFIER, "Expext superclass name.")
            superclass = Variable(self.previous())

        self.consume(TokenType.LEFT_BRACE, "Expected '{' before class body.")

        methods: list[Function] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.function(FunctionKind.METHOD))

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")
        return Class(name, superclass, methods)

    def function(self, kind: FunctionKind) -> Function:
        name = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        return Function(name, self.lambda_expression(kind))

    def var_declaration(self) -> Var:
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Var(name, initializer)

    def block(self) -> list[Stmt]:
        statements = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def if_statement(self) -> If:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")
        then_branch = self.statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.statement()
        return If(condition, then_branch, else_branch)

    def or_expression(self) -> Expr:
        expr = self.and_expression()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.and_expression()
            expr = Logical(expr, operator, right)

        return expr

    def and_expression(self) -> Expr:
        # Instead of equality
        expr = self.conditional()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.conditional()
            expr = Logical(expr, operator, right)

        return expr

    def lambda_expression(self, kind: FunctionKind = FunctionKind.LAMBDA) -> Lambda:
        if kind == FunctionKind.LAMBDA:
            self.consume(TokenType.LEFT_PAREN, "Expect '(' after lambda expression.")
        else:
            self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")

        parameters: list[Token] = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(parameters) >= 255:
                    self.error(self.peek(), "Can't have more than 255 parameters.")
                parameters.append(self.consume(TokenType.IDENTIFIER, "Expected parameter name."))
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self.consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self.block()
        return Lambda(parameters, body)
