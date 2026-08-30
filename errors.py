class HanError(Exception):
    def __init__(
        self,
        message,
        line=None,
        column=None,
        source=None,
        error_code="H0000",
        error_type="오류"
    ):
        self.message = message
        self.line = line
        self.column = column
        self.source = source
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

        if self.source:
            lines.append(f"│ 파일: {self.source}")

        if self.line is not None:
            location = f"{self.line}행"
            if self.column is not None:
                location += f" {self.column}열"
            lines.append(f"│ 위치: {location}")

        lines.append("│")

        if self.source_line:
            lines.append(f"│ {self.line} │ {self.source_line}")

            if self.column is not None:
                pointer = " " * max(0, self.column - 1) + "^"
                lines.append(f"│     │ {pointer}")

        lines.extend([
            "│",
            f"│ {self.message}",
            "│",
            "└────────────────────────────────────────"
        ])

        return "\n".join(lines)

    @property
    def source_line(self):
        return getattr(self, "_source_line", None)

    def set_source_line(self, source_line):
        self._source_line = source_line
        return self


class HanLexerError(HanError):
    def __init__(self, message, line=None, column=None, source=None, source_line=None):
        super().__init__(
            message,
            line,
            column,
            source,
            error_code="H1000",
            error_type="문법 분석 오류"
        )
        self._source_line = source_line


class HanParserError(HanError):
    def __init__(self, message, line=None, column=None, source=None, source_line=None):
        super().__init__(
            message,
            line,
            column,
            source,
            error_code="H2000",
            error_type="구문 오류"
        )
        self._source_line = source_line


class HanCompilerError(HanError):
    def __init__(self, message, line=None, column=None, source=None, source_line=None):
        super().__init__(
            message,
            line,
            column,
            source,
            error_code="H3000",
            error_type="컴파일 오류"
        )
        self._source_line = source_line