import argparse
from pathlib import Path
from io import TextIOWrapper


class WriteLn:
    def __init__(self, file: TextIOWrapper):
        self.file = file

    def writeln(self, line: str) -> int:
        return self.file.write(line + "\n")


def generate_ast(output_dir: Path) -> None:
    define_ast(
        output_dir,
        "Expr",
        [
            "Binary   : Expr left, Token operator, Expr right",
            "Grouping : Expr expression",
            "Literal  : Any value",
            "Unary    : Token operator, Expr right",
        ],
    )


def define_ast(output_dir: Path, base_name: str, types: list[str]) -> None:
    with open(output_dir.joinpath(f"{base_name.lower()}.py"), "w") as fs:
        file = WriteLn(fs)
        define_imports(file)
        define_base_class(file, base_name)

        # AST classes
        for t in types:
            file.writeln("")
            class_name, fields = map(lambda s: s.strip(), t.split(":"))
            define_type(file, base_name, class_name, fields)
            file.writeln("")

        file.writeln("")
        define_visitor(file, base_name, types)


def define_imports(file: WriteLn) -> None:
    file.writeln("from abc import ABC, abstractmethod")
    file.writeln("from typing import Any")
    file.writeln("")
    file.writeln("from pylox.scanner import Token")
    file.writeln("\n")


def define_base_class(file: WriteLn, base_name: str) -> None:
    file.writeln(f"class {base_name}(ABC):")
    file.writeln("    @abstractmethod")
    file.writeln(f'    def accept(self, visitor: "{base_name}Visitor"):  # noqa: U100')
    file.writeln("        raise NotImplementedError()")
    file.writeln("")


def define_type(file: WriteLn, base_name: str, class_name: str, fields: str) -> None:
    # (type, name)
    variables = [tuple(i.split(" ")) for i in fields.split(", ")]
    file.writeln(f"class {class_name}({base_name}):")
    slots = ", ".join(f'"{var_name}"' for (_, var_name) in variables)
    if len(variables) == 1:
        slots += ","
    file.writeln(f"    __slots___ = ({slots})")
    file.writeln("")
    init_header = ", ".join(f"{va_name}: {var_type}" for (var_type, va_name) in variables)
    file.writeln(f"    def __init__(self, {init_header}) -> None:")
    file.writeln("        super().__init__()")
    # Fields
    for _, i_n in variables:
        file.writeln(f"        self.{i_n} = {i_n}")
    file.writeln("")
    file.writeln(f'    def accept(self, visitor: "{base_name}Visitor"):')
    file.writeln(f"        return visitor.visit_{class_name.lower()}_{base_name.lower()}(self)")


def define_visitor(file: WriteLn, base_name: str, types: list[str]) -> None:
    file.file.write(f"class {base_name}Visitor(ABC):")
    base_lower = base_name.lower()

    for t in types:
        file.writeln("")
        type_name = t.split(":")[0].strip()
        file.writeln("    @abstractmethod")
        file.writeln(
            f"    def visit_{type_name.lower()}_{base_lower}(self, {base_lower}: {type_name}):"
            "  # noqa: U100"
        )
        file.writeln("        raise NotImplementedError()")


def cli() -> None:
    parser = argparse.ArgumentParser("generate_ast")
    parser.add_argument("output_dir", type=Path)
    parsed_args = parser.parse_args()

    generate_ast(parsed_args.output_dir)


if __name__ == "__main__":
    cli()
