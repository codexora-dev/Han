from lexer.lexer import Token
from parser.nodes import (
    BinaryOpNode,  ## 이항 연산
    FunctionCallNode, ## 함수 호출
    FunctionNode,  ## 함수 정의
    IdentifierNode,  ## 식별자
    IfNode,  ## 조건문
    InputNode,  ## 입력
    LiteralNode,  ## 리터럴
    PrintNode,
    ProgramNode,
    RepeatNode,
    UnaryOpNode,
    VarAssignNode,
)


class Parser:
    """토큰을 AST(Abstract Syntax Tree)로 변환한다."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.position = 0

    def parse(self) -> ProgramNode:
        return ProgramNode(self.parse_block(stop_tokens={"EOF"}))

    def parse_block(self, stop_tokens: set[str]) -> list:
        statements = []

        self.skip_newlines()
        while self.current().type not in stop_tokens:
            statements.append(self.parse_statement())
            self.consume_statement_end()
            self.skip_newlines()

        return statements

    def parse_statement(self):
        token = self.current()

        if token.type == "PRINT":  ## 출력문을 처리하는 부분
            return self.parse_print()
        if token.type == "VAR":  ## 변수 선언을 처리하는 부분
            return self.parse_var_declaration()
        if token.type == "INPUT":  ## 입력을 처리하는 부분
            return self.parse_input()
        if token.type == "IF":  ## 조건문을 처리하는 부분
            return self.parse_if()
        if token.type == "REPEAT":  ## 반복문을 처리하는 부분
            return self.parse_repeat()
        if token.type == "FUNCTION":  ## 함수 정의를 처리하는 부분
            return self.parse_function()
        if token.type == "IDENTIFIER" and self.peek().type == "EQUAL":
            return self.parse_assignment()
        if token.type == "IDENTIFIER" and self.peek().type == "LPAREN":
            return self.parse_function_call()

        self.error(token, f"예상하지 못한 토큰입니다: {token.value}")

    def parse_print(self) -> PrintNode:
        self.advance()
        return PrintNode(self.parse_expression())

    def parse_var_declaration(self) -> VarAssignNode:
        self.advance()

        name = self.consume(
            "IDENTIFIER",
            "변수 이름이 필요합니다."
        ).value

        self.consume(
            "EQUAL",
            "변수 선언에는 '='이 필요합니다."
        )

        return VarAssignNode(
            name,
            self.parse_expression(),
            declare=True
        )

    def parse_assignment(self) -> VarAssignNode:
        name = self.consume(
            "IDENTIFIER",
            "변수 이름이 필요합니다."
        ).value

        self.consume(
            "EQUAL",
            "값을 대입하려면 '='이 필요합니다."
     )

        return VarAssignNode(
            name,
            self.parse_expression()
        )

    def parse_input(self) -> InputNode:
        self.advance()

        name = self.consume(
            "IDENTIFIER",
            "입력을 저장할 변수 이름이 필요합니다."
        ).value

        if self.current().type in {"NEWLINE", "EOF", "END", "ELSE"}:
            return InputNode(name)

        return InputNode(
            name,
            self.parse_expression()
        )

    def parse_if(self) -> IfNode:
        self.advance()
        condition = self.parse_expression()
        self.consume_statement_end()

        then_body = self.parse_block(stop_tokens={"ELSE", "END", "EOF"})
        else_body = []

        if self.match("ELSE"):
            self.consume_statement_end()
            else_body = self.parse_block(stop_tokens={"END", "EOF"})

        self.consume("END", "만약 문은 '끝'으로 닫아야 합니다.")
        return IfNode(condition, then_body, else_body)

    def parse_repeat(self) -> RepeatNode:
        self.advance()
        count = self.parse_expression()
        self.consume_statement_end()
        body = self.parse_block(stop_tokens={"END", "EOF"})
        self.consume("END", "반복 문은 '끝'으로 닫아야 합니다.")
        return RepeatNode(count, body)

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        expr = self.parse_and()
        while self.match("OR"):
            expr = BinaryOpNode(expr, "또는", self.parse_and())
        return expr

    def parse_and(self):
        expr = self.parse_equality()
        while self.match("AND"):
            expr = BinaryOpNode(expr, "그리고", self.parse_equality())
        return expr

    def parse_equality(self):
        expr = self.parse_comparison()
        while self.current().type in {"EQEQ", "NEQ"}:
            operator = self.advance().value
            expr = BinaryOpNode(expr, operator, self.parse_comparison())
        return expr

    def parse_comparison(self):
        expr = self.parse_term()
        while self.current().type in {"GT", "GTE", "LT", "LTE"}:
            operator = self.advance().value
            expr = BinaryOpNode(expr, operator, self.parse_term())
        return expr

    def parse_term(self):
        expr = self.parse_factor()
        while self.current().type in {"PLUS", "MINUS"}:
            operator = self.advance().value
            expr = BinaryOpNode(expr, operator, self.parse_factor())
        return expr

    def parse_factor(self):
        expr = self.parse_unary()
        while self.current().type in {"STAR", "SLASH", "PERCENT"}:
            operator = self.advance().value
            expr = BinaryOpNode(expr, operator, self.parse_unary())
        return expr

    def parse_unary(self):
        if self.current().type in {"MINUS", "NOT"}:
            operator = self.advance().value
            return UnaryOpNode(operator, self.parse_unary())

        return self.parse_primary()

    def parse_primary(self):
        token = self.current()

        if self.match("NUMBER", "STRING"):
            return LiteralNode(token.value)

        if self.match("TRUE"):
            return LiteralNode(True)

        if self.match("FALSE"):
            return LiteralNode(False)

        if self.current().type == "IDENTIFIER":
            name = self.advance().value

            if self.match("LPAREN"):
                arguments = []

                if self.current().type != "RPAREN":
                    while True:
                        arguments.append(self.parse_expression())

                        if not self.match("COMMA"):
                            break

                self.consume(
                    "RPAREN",
                    "함수 호출에는 ')'가 필요합니다."
                )

                return FunctionCallNode(
                    name,
                    arguments
                )

            return IdentifierNode(name)

        if self.match("LPAREN"):
                expr = self.parse_expression()
                self.consume(
                    "RPAREN",
                    "괄호를 닫으려면 ')'가 필요합니다."
                )
                return expr

        self.error(token, "표현식이 필요합니다.")

    def parse_function_call(self) -> FunctionCallNode:
        name = self.consume(
            "IDENTIFIER",
            "함수 이름이 필요합니다."
        ).value

        self.consume(
            "LPAREN",
            "함수 호출에는 '('가 필요합니다."
        )

        arguments = []

        if self.current().type != "RPAREN":
            while True:
                arguments.append(self.parse_expression())

                if not self.match("COMMA"):
                    break

        self.consume(
            "RPAREN",
            "함수 호출의 ')'가 필요합니다."
        )

        return FunctionCallNode(
            name,
            arguments
        )
            

    def parse_function(self) -> FunctionNode:
        self.advance()

        name = self.consume(
            "IDENTIFIER",
            "함수 이름이 필요합니다."
        ).value

        self.consume(
            "LPAREN",
            "함수 매개변수를 시작하려면 '('가 필요합니다."
        )

        parameters = []

        if self.current().type != "RPAREN":
            while True:
                parameter = self.consume(
                    "IDENTIFIER",
                    "매개변수 이름이 필요합니다."
                ).value

                parameters.append(parameter)

                if not self.match("COMMA"):
                    break

        self.consume(
            "RPAREN",
            "함수 매개변수를 닫으려면 ')'가 필요합니다."
        )

        self.consume_statement_end()

        body = self.parse_block(
            stop_tokens={"END", "EOF"}
        )

        self.consume(
            "END",
            "함수 정의는 '끝'으로 닫아야 합니다."
        )

        return FunctionNode(
            name,
            parameters,
            body
        )

    def consume_statement_end(self) -> None:
        if self.current().type in {"NEWLINE", "EOF", "END", "ELSE"}:
            self.match("NEWLINE")
            return

        self.error(self.current(), "문장 끝에는 줄바꿈이 필요합니다.")

    def skip_newlines(self) -> None:
        while self.match("NEWLINE"):
            pass

    def current(self) -> Token:
        return self.tokens[self.position]

    def peek(self) -> Token:
        if self.position + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.position + 1]

    def advance(self) -> Token:
        token = self.current()
        self.position += 1
        return token

    def match(self, *token_types: str) -> bool:
        if self.current().type in token_types:
            self.advance()
            return True
        return False

    def consume(self, token_type: str, message: str) -> Token:
        if self.current().type == token_type:
            return self.advance()
        self.error(self.current(), message)

    @staticmethod
    def error(token: Token, message: str):
        raise SyntaxError(f"{token.line}행 {token.column}열: {message}")
