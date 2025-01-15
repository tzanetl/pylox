import builtins
from inspect import getframeinfo, stack
from pathlib import Path
from typing import Any


def dbg(*messages: Any, sep: str = " ") -> None:
    caller = getframeinfo(stack()[1][0])
    file_name = str(Path(caller.filename).resolve()).replace(
        str(Path(__file__).parents[2].resolve()), ""
    )
    print(f"[{file_name[1:]}:{caller.lineno}] {sep.join(map(str, messages))}")


builtins.dbg = dbg  # type: ignore [attr-defined]
