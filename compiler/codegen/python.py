from parser.nodes import (
    BinaryOpNode,
    FunctionCallNode,
    FunctionNode,
    IdentifierNode,
    IfNode,
    InputNode,
    LiteralNode,
    PrintNode,
    ProgramNode,
    RepeatNode,
    UnaryOpNode,
    VarAssignNode,
)


class PythonCodeGenerator:
    """Han AST를 실행 가능한 Python 코드로 변환한다."""

    BINARY_OPERATORS = {
        "+": "+",
        "-": "-",
        "*": "*",
        "/": "/",
        "%": "%",
        "==": "==",
        "!=": "!=",
        ">": ">",
        ">=": ">=",
        "<": "<",
        "<=": "<=",
        "그리고": "and",
        "또는": "or",
    }

    UNARY_OPERATORS = {
        "-": "-",
        "아니다": "not",
    }

    def generate(self, program: ProgramNode) -> str:
        lines = []

        for statement in program.statements:
            lines.extend(self.generate_statement(statement, indent=0))

        return "\n".join(lines)

    def generate_statement(self, node, indent: int) -> list[str]:
        prefix = "    " * indent

        if isinstance(node, PrintNode):
            return [f"{prefix}print({self.generate_expression(node.value)})"]

        if isinstance(node, VarAssignNode):
            return [f"{prefix}{node.name} = {self.generate_expression(node.value)}"]

        if isinstance(node, FunctionCallNode):
            args = ", ".join(self.generate_expression(arg) for arg in node.arguments)
            return [f"{prefix}{node.name}({args})"]

        if isinstance(node, InputNode):
            prompt = self.generate_expression(node.prompt) if node.prompt else "''"
            return [f"{prefix}{node.name} = input({prompt})"]

        if isinstance(node, IfNode):
            lines = [f"{prefix}if {self.generate_expression(node.condition)}:"]
            lines.extend(self.generate_body(node.then_body, indent + 1))
            if node.else_body:
                lines.append(f"{prefix}else:")
                lines.extend(self.generate_body(node.else_body, indent + 1))
            return lines

        if isinstance(node, RepeatNode):
            lines = [f"{prefix}for _ in range(int({self.generate_expression(node.count)})):"]
            lines.extend(self.generate_body(node.body, indent + 1))
            return lines

        if isinstance(node, FunctionNode):
            parameters = ", ".join(node.parameters)

            lines = [
                f"{prefix}def {node.name}({parameters}):"
            ]

            lines.extend(
                self.generate_body(
                    node.body,
                    indent + 1
                )
            )

            return lines

        raise TypeError(f"지원하지 않는 AST 노드입니다: {type(node).__name__}")

    def generate_body(self, statements: list, indent: int) -> list[str]:
        if not statements:
            return ["    " * indent + "pass"]

        lines = []
        for statement in statements:
            lines.extend(self.generate_statement(statement, indent))
        return lines

    def generate_expression(self, node) -> str:
        if isinstance(node, LiteralNode):
            return repr(node.value)

        if isinstance(node, IdentifierNode):
            return node.name

        if isinstance(node, FunctionCallNode):
            arguments = ", ".join(
                self.generate_expression(argument)
                for argument in node.arguments
            )

            return f"{node.name}({arguments})"

        if isinstance(node, UnaryOpNode):
            operator = self.UNARY_OPERATORS[node.operator]
            return f"({operator} {self.generate_expression(node.operand)})"

        if isinstance(node, BinaryOpNode):
            operator = self.BINARY_OPERATORS[node.operator]
            left = self.generate_expression(node.left)
            right = self.generate_expression(node.right)
            return f"({left} {operator} {right})"

        raise TypeError(f"지원하지 않는 표현식 노드입니다: {type(node).__name__}")
