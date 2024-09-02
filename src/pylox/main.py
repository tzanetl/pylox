import argparse
import sys
import os

import pylox.version

type path_like = str | bytes | os.PathLike


def run(source: str):
    raise NotImplementedError()


def run_file(path: path_like):
    with open(path, "r") as fs:
        source = fs.read()
    run(source)


def run_prompt():
    raise NotImplementedError()


def main(argv: list[str]):
    arg_parser = argparse.ArgumentParser("pylox", description=pylox.version.__desc__)
    arg_parser.add_argument("script", action="append", nargs="+")
    arg_parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {pylox.version.__version__}",
    )

    parsed = arg_parser.parse_args(argv)

    if len(parsed.script) == 1:
        run_file(parsed.script[1])
    else:
        run_prompt()


def cli():
    main(sys.argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
