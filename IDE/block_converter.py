from __future__ import annotations

from block_model import (
    Block,
    BlockDocument,
    create_block
)


class BlockConverter:
    @staticmethod
    def to_han(
        document: BlockDocument
    ) -> str:
        lines = []

        for block in document.blocks:
            lines.extend(
                BlockConverter._to_han_block(
                    block,
                    0
                )
            )

        return "\n".join(lines)

    @staticmethod
    def _to_han_block(
        block: Block,
        indent: int
    ) -> list[str]:
        prefix = "    " * indent
        f = block.fields

        if block.type == "print":
            return [
                prefix +
                f"출력 {f.get('value', '')}"
            ]

        if block.type == "var":
            return [
                prefix +
                f"변수 {f.get('name', '')} = "
                f"{f.get('value', '')}"
            ]

        if block.type == "assign":
            return [
                prefix +
                f"{f.get('name', '')} = "
                f"{f.get('value', '')}"
            ]

        if block.type == "input":
            return [
                prefix +
                f"입력 {f.get('name', '')} "
                f"{f.get('prompt', '')}".rstrip()
            ]

        if block.type == "if":
            lines = [
                prefix +
                f"만약 {f.get('condition', '')}"
            ]

            for child in block.children:
                lines.extend(
                    BlockConverter._to_han_block(
                        child,
                        indent + 1
                    )
                )

            lines.append(
                prefix + "끝"
            )

            return lines

        if block.type == "repeat":
            lines = [
                prefix +
                f"반복 {f.get('count', '')}"
            ]

            for child in block.children:
                lines.extend(
                    BlockConverter._to_han_block(
                        child,
                        indent + 1
                    )
                )

            lines.append(
                prefix + "끝"
            )

            return lines

        if block.type == "function":
            parameters = f.get(
                "parameters",
                ""
            )

            lines = [
                prefix +
                f"함수 {f.get('name', '')}"
                f"({parameters})"
            ]

            for child in block.children:
                lines.extend(
                    BlockConverter._to_han_block(
                        child,
                        indent + 1
                    )
                )

            lines.append(
                prefix + "끝"
            )

            return lines

        return []

    @staticmethod
    def from_han(
        source: str
    ) -> BlockDocument:
        document = BlockDocument()

        stack = [
            document.blocks
        ]

        for raw_line in source.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if line == "끝":
                if len(stack) > 1:
                    stack.pop()
                continue

            if line == "아니면":
                continue

            block = BlockConverter._parse_line(
                line
            )

            if block is None:
                continue

            stack[-1].append(block)

            if block.type in {
                "if",
                "repeat",
                "function"
            }:
                stack.append(
                    block.children
                )

        return document

    @staticmethod
    def _parse_line(
        line: str
    ) -> Block | None:
        if line.startswith("출력 "):
            block = create_block("print")
            block.fields["value"] = line[3:].strip()
            return block

        if line.startswith("변수 "):
            value = line[3:].strip()

            if "=" not in value:
                return None

            name, expression = value.split(
                "=",
                1
            )

            block = create_block("var")
            block.fields["name"] = name.strip()
            block.fields["value"] = expression.strip()

            return block

        if line.startswith("입력 "):
            value = line[3:].strip()
            parts = value.split(
                maxsplit=1
            )

            block = create_block("input")
            block.fields["name"] = parts[0]

            if len(parts) > 1:
                block.fields["prompt"] = parts[1]

            return block

        if line.startswith("만약 "):
            block = create_block("if")
            block.fields["condition"] = line[3:].strip()
            return block

        if line.startswith("반복 "):
            block = create_block("repeat")
            block.fields["count"] = line[3:].strip()
            return block

        if line.startswith("함수 "):
            value = line[3:].strip()

            block = create_block("function")

            if "(" in value and value.endswith(")"):
                name, parameters = value.split(
                    "(",
                    1
                )

                block.fields["name"] = name.strip()
                block.fields["parameters"] = parameters[:-1]

            else:
                block.fields["name"] = value

            return block

        if "=" in line:
            name, expression = line.split(
                "=",
                1
            )

            block = create_block("assign")
            block.fields["name"] = name.strip()
            block.fields["value"] = expression.strip()

            return block

        return None