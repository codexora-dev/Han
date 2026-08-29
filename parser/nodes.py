from dataclasses import dataclass


class Node:
    pass


@dataclass
class ProgramNode(Node):
    statements: list[Node]


@dataclass
class PrintNode(Node):
    value: Node


@dataclass
class VarAssignNode(Node):
    name: str
    value: Node
    declare: bool = False


@dataclass
class InputNode(Node):
    name: str
    prompt: Node | None = None


@dataclass
class IfNode(Node):
    condition: Node
    then_body: list[Node]
    else_body: list[Node]


@dataclass
class RepeatNode(Node):
    count: Node
    body: list[Node]


@dataclass
class LiteralNode(Node):
    value: object


@dataclass
class IdentifierNode(Node):
    name: str

@dataclass
class FunctionCallNode(Node):
    name: str
    arguments: list


@dataclass
class UnaryOpNode(Node):
    operator: str
    operand: Node


@dataclass
class BinaryOpNode(Node):
    left: Node
    operator: str
    right: Node

@dataclass
class FunctionNode(Node):
    name: str
    parameters: list
    body: list