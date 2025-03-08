import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import pylox.error as error
from pylox.environment import Environment
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
    StmtVisitor,
    Var,
    While,
)


class Unassigned:
    """Type for unassigned variables"""


UNASSIGNED = Unassigned()


class LoxCallable(ABC):
    __slots__ = ("arity",)

    def __init__(self, arity: int) -> None:
        self.arity = arity

    @abstractmethod
    def call(self, interpreter: "Interpreter", arguments: list) -> Any:  # noqa: U100
        raise NotImplementedError()


class LoxFunction(LoxCallable):
    __slots__ = ("declaration", "closure", "is_initializer")

    def __init__(self, declaration: Function, closure: Environment, is_initializer: bool) -> None:
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"

    @property
    def arity(self) -> int:
        return len(self.declaration.function.params)

    @arity.setter
    def arity(self) -> None:
        raise NotImplementedError("unreachable")

    def call(self, interpreter: "Interpreter", arguments: list) -> Any:
        environment = Environment(self.closure)
        for param, arg in zip(self.declaration.function.params, arguments):
            environment.define(param.lexeme, arg)

        try:
            interpreter.execute_block(self.declaration.function.body, environment)
        except error.ReturnError as exc:
            if self.is_initializer:
                return self.closure.get_at(0, "this")
            return exc.value

        if self.is_initializer:
            return self.closure.get_at(0, "this")

    def bind(self, instance: "LoxInstance") -> "LoxFunction":
        environement = Environment(self.closure)
        environement.define("this", instance)
        return LoxFunction(self.declaration, environement, self.is_initializer)


class LoxLambda(LoxCallable):
    __slots__ = ("declaration", "closure")

    def __init__(self, declaration: Lambda, closure: Environment) -> None:
        self.declaration = declaration
        self.closure = closure

    def __str__(self) -> str:
        return "<anonymous fn>"

    @property
    def arity(self) -> int:
        return len(self.declaration.params)

    @arity.setter
    def arity(self) -> None:
        raise NotImplementedError("unreachable")

    def call(self, interpreter: "Interpreter", arguments: list) -> Any:
        environment = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, arg)

        try:
            interpreter.execute_block(self.declaration.body, environment)
        except error.ReturnError as exc:
            return exc.value


# Builtin functions
class Clock(LoxCallable):
    def __str__(self) -> str:
        return "<native fn>"

    def call(self, interpreter: "Interpreter", arguments: list) -> float:  # noqa: U100
        return time.time()


class LoxClass(LoxCallable):
    __slots__ = ("name", "superclass", "methods")

    def __init__(
        self, name: str, superclass: Optional["LoxClass"], methods: dict[str, LoxFunction]
    ) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def __str__(self) -> str:
        return self.name

    @property
    def arity(self) -> int:
        initialiser = self.find_method("init")
        if not initialiser:
            return 0
        return initialiser.arity

    @arity.setter
    def arity(self):
        raise NotImplementedError("unreachable")

    def call(self, interpreter: "Interpreter", arguments: list) -> "LoxInstance":  # noqa: U100
        instance = LoxInstance(self)
        initializer = self.find_method("init")
        if initializer:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    def find_method(self, name: str) -> LoxFunction | None:
        if name in self.methods:
            return self.methods[name]

        if self.superclass is not None:
            return self.superclass.find_method(name)

        return None


class LoxInstance:
    __slots__ = ("klass", "fields")

    def __init__(self, klass: LoxClass) -> None:
        self.klass = klass
        self.fields: dict[str, Any] = {}

    def __str__(self) -> str:
        return f"{self.klass.name} instance"

    def get(self, name: Token) -> Any:
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method = self.klass.find_method(name.lexeme)
        if method:
            return method.bind(self)
        raise error.LoxRuntimeError(name, f"Undefined property {name.lexeme}.")

    def set(self, name: Token, value: Any) -> None:
        self.fields[name.lexeme] = value


class Interpreter(ExprVisitor, StmtVisitor):
    __slots__ = ("environment", "is_repl", "globals", "locals")

    def __init__(self) -> None:
        super().__init__()
        self.globals = Environment()
        self.locals: dict[Expr, int] = {}
        self.environment = self.globals
        self.is_repl = False

        # Builtin functions
        self.globals.define("clock", Clock(0))

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

    def resolve(self, expr: Expr, depth: int) -> None:
        self.locals[expr] = depth

    def look_up_variable(self, name: Token, expr: Expr) -> Any:
        distance = self.locals.get(expr)
        if distance is not None:
            return self.environment.get_at(distance, name.lexeme)
        return self.globals.get(name)

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
        return self.look_up_variable(expr.name, expr)

    def visit_assign_expr(self, expr: Assign) -> Any:
        value = self.evaluate(expr.value)
        distance = self.locals.get(expr)
        if distance is not None:
            self.environment.assign_at(distance, expr.name, value)
        else:
            self.globals.assign(expr.name, value)
        return value

    def visit_logical_expr(self, expr: Logical) -> Any:
        left = self.evaluate(expr.left)

        if expr.operator.type == TokenType.OR:
            if is_truthy(left):
                return left
        else:
            if not is_truthy(left):
                return left

        return self.evaluate(expr.right)

    def visit_call_expr(self, expr: Call) -> Any:
        callee = self.evaluate(expr.callee)
        arguments = [self.evaluate(arg) for arg in expr.arguments]
        if not isinstance(callee, LoxCallable):
            raise error.LoxRuntimeError(expr.paren, "Can only call functions and classes.")
        if len(arguments) != callee.arity:
            raise error.LoxRuntimeError(
                expr.paren, f"Expected {callee.arity} but got {len(arguments)}."
            )
        return callee.call(self, arguments)

    def visit_get_expr(self, expr: Get) -> Any:
        obj = self.evaluate(expr.object)
        if isinstance(obj, LoxInstance):
            return obj.get(expr.name)
        raise error.LoxRuntimeError(expr.name, "Only instances have properties.")

    def visit_set_expr(self, expr: Set) -> Any:
        obj = self.evaluate(expr.object)
        if not isinstance(obj, LoxInstance):
            raise error.LoxRuntimeError(expr.name, "Only instances have fields.")
        value = self.evaluate(expr.value)
        obj.set(expr.name, value)
        return value

    def visit_this_expr(self, expr: This) -> Any:
        return self.look_up_variable(expr.keyword, expr)

    def visit_lambda_expr(self, expr: Lambda) -> LoxLambda:
        return LoxLambda(expr, self.environment)

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

    def visit_class_stmt(self, stmt: Class) -> None:
        superclass = None
        if stmt.superclass is not None:
            superclass = self.evaluate(stmt.superclass)
            if not isinstance(superclass, LoxClass):
                raise error.LoxRuntimeError(stmt.superclass.name, "Superclass must be a class.")

        self.environment.define(stmt.name.lexeme, None)

        methods = {}
        for method in stmt.methods:
            methods[method.name.lexeme] = LoxFunction(
                method, self.environment, method.name.lexeme == "init"
            )

        lox_class = LoxClass(stmt.name.lexeme, superclass, methods)
        self.environment.assign(stmt.name, lox_class)

    def visit_if_stmt(self, stmt: If) -> None:
        if is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self.execute(stmt.else_branch)

    def visit_while_stmt(self, stmt: While) -> None:
        while is_truthy(self.evaluate(stmt.condition)):
            try:
                self.execute(stmt.body)
            except error.BreakWhileError:
                break

    def visit_break_stmt(self, _stmt: Break) -> None:  # noqa: U101
        raise error.BreakWhileError()

    def visit_function_stmt(self, stmt: Function) -> None:
        func = LoxFunction(stmt, self.environment, False)
        self.environment.define(stmt.name.lexeme, func)

    def visit_return_stmt(self, stmt: Return) -> None:
        value = None
        if stmt.value is not None:
            value = self.evaluate(stmt.value)
        raise error.ReturnError(value)


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
