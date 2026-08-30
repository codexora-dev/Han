class HanError(Exception):
    def __init__(
        self,
        message,
        line=None,
        column=None,
        source_line=None,
        error_code="H0000",
        error_type="오류",
    ):
        self.message = message
        self.line = line
        self.column = column
        self.source_line = source_line
        self.error_code = error_code
        self.error_type = error_type
        super().__init__(message)

    def format(self):
        lines = [
            "┌────────────────────────────────────────",
            "│ Han 오류",
            "├────────────────────────────────────────",
            f"│ 오류 코드: {self.error_code}",
            f"│ 오류 종류: {self.error_type}",
        ]

        if self.line is not None:
            location = f"{self.line}행"
            if self.column is not None:
                location += f" {self.column}열"
            lines.append(f"│ 위치: {location}")

        if self.source_line:
            lines.append("│")
            lines.append(f"│ {self.line} │ {self.source_line}")

            if self.column is not None:
                pointer = " " * (self.column + 4) + "^"
                lines.append(f"│     {pointer}")

        lines.extend([
            "│",
            f"│ {self.message}",
            "│",
            "│ 이 오류 메시지를 복사하여 Han 커뮤니티에",
            "│ 질문하면 문제 해결에 도움을 받을 수 있습니다.",
            "└────────────────────────────────────────",
        ])

        return "\n".join(lines)


class HanLexerError(HanError):
    def __init__(
        self,
        message,
        line=None,
        column=None,
        source_line=None,
    ):
        super().__init__(
            message,
            line,
            column,
            source_line,
            "H1000",
            "어휘 분석 오류",
        )


class HanParserError(HanError):
    def __init__(
        self,
        message,
        line=None,
        column=None,
        source_line=None,
    ):
        super().__init__(
            message,
            line,
            column,
            source_line,
            "H2000",
            "구문 분석 오류",
        )


class HanCompilerError(HanError):
    def __init__(
        self,
        message,
        line=None,
        column=None,
        source_line=None,
    ):
        super().__init__(
            message,
            line,
            column,
            source_line,
            "H3000",
            "컴파일 오류",
        )

PYTHON_ERROR_MESSAGES = {
    "NameError": (
        "정의되지 않은 이름입니다.",
        "사용하려는 변수나 함수가 정의되어 있는지 확인하세요."
    ),
    "TypeError": (
        "자료형이 올바르지 않습니다.",
        "연산이나 함수에 전달한 값의 자료형을 확인하세요."
    ),
    "ValueError": (
        "값이 올바르지 않습니다.",
        "입력한 값의 형식이나 범위를 확인하세요."
    ),
    "IndexError": (
        "존재하지 않는 위치에 접근했습니다.",
        "사용한 위치가 데이터의 범위 안에 있는지 확인하세요."
    ),
    "KeyError": (
        "존재하지 않는 키에 접근했습니다.",
        "사용한 키가 실제로 존재하는지 확인하세요."
    ),
    "ZeroDivisionError": (
        "0으로 나눌 수 없습니다.",
        "나누는 값이 0인지 확인하세요."
    ),
    "AttributeError": (
        "존재하지 않는 기능이나 속성을 사용했습니다.",
        "사용한 객체가 해당 기능이나 속성을 지원하는지 확인하세요."
    ),
    "FileNotFoundError": (
        "파일을 찾을 수 없습니다.",
        "파일의 경로와 파일 이름을 확인하세요."
    ),
    "ImportError": (
        "필요한 모듈을 불러올 수 없습니다.",
        "사용하려는 모듈이나 기능이 올바르게 연결되어 있는지 확인하세요."
    ),
    "ModuleNotFoundError": (
        "필요한 모듈을 찾을 수 없습니다.",
        "사용하려는 모듈이 설치되어 있는지 확인하세요."
    ),
}

def translate_python_error(error_type, message):
    title, solution = PYTHON_ERROR_MESSAGES.get(
        error_type,
        (
            "프로그램 실행 중 오류가 발생했습니다.",
            "오류가 발생한 코드와 오류 메시지를 확인하세요."
        )
    )

    return title, solution