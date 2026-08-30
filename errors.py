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