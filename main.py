from pathlib import Path
import sys

from compiler.codegen.python import PythonCodeGenerator
from lexer.lexer import Lexer
from parser.parser import Parser


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
            exec(python_code, {})
        else:
            print(python_code)
    except Exception as error:
        print(f"컴파일 오류: {error}")


if __name__ == "__main__":
    main()
