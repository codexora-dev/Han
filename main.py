import builtins
import ctypes
import os
import sys
from pathlib import Path

from compiler.codegen.python import PythonCodeGenerator
from lexer.lexer import Lexer
from parser.parser import Parser


def _has_interactive_stdin() -> bool:
    if sys.stdin is None or getattr(sys.stdin, "closed", False):
        return False

    try:
        if os.name == "nt":
            import msvcrt

            mode = ctypes.c_uint()
            handle = msvcrt.get_osfhandle(sys.stdin.fileno())
            return bool(ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)))
        return sys.stdin.isatty()
    except (AttributeError, OSError, ValueError):
        return False


def safe_input(prompt: str = "") -> str:
    if sys.stdin is None or getattr(sys.stdin, "closed", False):
        return ""

    if _has_interactive_stdin():
        try:
            return input(prompt)
        except (EOFError, OSError, RuntimeError):
            return ""

    try:
        line = sys.stdin.readline()
    except (EOFError, OSError, RuntimeError):
        return ""

    if line == "":
        return ""

    return line.rstrip("\r\n")


def compile_file(path: str) -> str:
    source = Path(path).read_text(encoding="utf-8")

    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    python_code = PythonCodeGenerator().generate(ast)
    # print("===== GENERATED PYTHON =====")
    # print(python_code)
    # print("============================")

    return python_code


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        print("사용법: python main.py <파일.han> [--실행]")
        return

    source_path = sys.argv[1]
    should_run = len(sys.argv) == 3 and sys.argv[2] == "--실행"

    if not source_path.endswith(".han"):
        print("오류: Han 소스 파일은 .han 확장자를 사용해야 합니다.")
        return

    if len(sys.argv) == 3 and not should_run:
        print("오류: 알 수 없는 옵션입니다. 실행하려면 --실행 을 사용하세요.")
        return

    try:
        python_code = compile_file(source_path)
        if should_run:
            builtins_dict = dict(builtins.__dict__)
            builtins_dict["input"] = safe_input
            ns = {"__name__": "__main__", "__builtins__": builtins_dict}
            exec(python_code, ns)
        else:
            print(python_code)
    except Exception as error:
        print(f"컴파일 오류: {error}")


if __name__ == "__main__":
    main()
