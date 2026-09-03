from __future__ import annotations

import base64
import sys
import traceback


try:
    source = base64.b64decode(sys.argv[2]).decode("utf-8")
    exec(compile(source, "<han>", "exec"), {"__name__": "__main__"})
except BaseException:
    traceback.print_exc()
finally:
    try:
        input("\n실행이 종료되었습니다. Enter 키를 누르면 창이 닫힙니다.")
    except (EOFError, OSError, RuntimeError):
        pass
