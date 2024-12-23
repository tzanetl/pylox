import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import SupportsWrite


def generate_ast(output_dir: Path | None) -> None:
    expr_types = [
        "Binary   : Expr left, Token operator, Expr right",
        "Grouping : Expr expression",
        "Literal  : Any value",
        "Unary    : Token operator, Expr right",
    ]
    base_name = "Expr"
    if output_dir is None:
        define_ast(
            sys.stdout,
            base_name,
            expr_types,
        )
    else:
        with open(output_dir.joinpath("expr.py"), "w") as fs:
            define_ast(
                fs,
                base_name,
                expr_types,
            )


def define_ast(file: "SupportsWrite[str]", base_name: str, types: list[str]) -> None:
    # Imports
    print("from abc import ABC", file=file)
    print("from typing import Any", file=file)
    print("", file=file)
    print("from pylox.scanner import Token", file=file)
    print("\n", file=file)
    # Base Class
    print(f"class {base_name}(ABC):", file=file)
    print("    pass", file=file)
    print("", file=file)

    # AST classes
    for t in types:
        print("", file=file)
        class_name, fields = map(lambda s: s.strip(), t.split(":"))
        define_type(file, base_name, class_name, fields)


def define_type(file: "SupportsWrite[str]", base_name: str, class_name: str, fields: str) -> None:
    # (type, name)
    variables = [tuple(i.split(" ")) for i in fields.split(", ")]
    print(f"class {class_name}({base_name}):", file=file)
    slots = ", ".join(f'"{var_name}"' for (_, var_name) in variables)
    print(f"    __slots___ = ({slots})", file=file)
    print("", file=file)
    init_header = ", ".join(f"{va_name}: {var_type}" for (var_type, va_name) in variables)
    print(f"    def __init__(self, {init_header}) -> None:", file=file)
    print("        super().__init__()", file=file)
    for _, i_n in variables:
        print(f"        self.{i_n} = {i_n}", file=file)
    print("", file=file)


def cli() -> None:
    parser = argparse.ArgumentParser("generate_ast")
    parser.add_argument(
        "output_dir", type=lambda i: Path(i) if i is not None else None, default=None, nargs="?"
    )
    parsed_args = parser.parse_args()

    generate_ast(parsed_args.output_dir)


if __name__ == "__main__":
    cli()
