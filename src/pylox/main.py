import argparse
import sys
import os
from pathlib import Path

import pylox.version
from .scanner import Scanner

type path_like = str | bytes | os.PathLike


def run(source: str):
    scanner = Scanner(source)
    for token in scanner.scan_tokens():
        print(token)


def run_file(path: path_like):
    with open(path, "r") as fs:
        source = fs.read()
    run(source)


def run_prompt():
    while True:
        line = input("> ")
        if not line:
            break
        run(line)


def parse_input(s: str) -> Path | None:
    if not s:
        return None
    p = Path(s)
    if not p.exists():
        raise argparse.ArgumentTypeError(f"input file {s} does not exist")
    if not p.is_file():
        raise argparse.ArgumentTypeError(f"input path {s} is not a file")
    return p


def main(argv: list[str]):
    arg_parser = argparse.ArgumentParser("pylox", description=pylox.version.__desc__)
    arg_parser.add_argument(
        "input", action="store", nargs="?", default="", type=parse_input
    )
    arg_parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {pylox.version.__version__}",
    )

    parsed = arg_parser.parse_args(argv)
    if parsed.input:
        run_file(parsed.input)
    else:
        run_prompt()


def cli():
    main(sys.argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
