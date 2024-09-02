from pathlib import Path


__version__: str = "0.1.0"
with open(Path(__file__).parent.joinpath("DESCRIPTION")) as fs:
    __desc__: str = fs.read()
