from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


def new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class Block:
    type: str
    fields: dict[str, Any] = field(default_factory=dict)
    children: list["Block"] = field(default_factory=list)
    id: str = field(default_factory=new_id)
    parent: "Block | None" = field(
        default=None,
        repr=False
    )

    def add_child(
        self,
        block: "Block"
    ) -> None:
        block.parent = self
        self.children.append(block)

    def insert_child(
        self,
        index: int,
        block: "Block"
    ) -> None:
        block.parent = self
        self.children.insert(
            index,
            block
        )

    def remove_child(
        self,
        block: "Block"
    ) -> None:
        if block in self.children:
            self.children.remove(block)
            block.parent = None

    def clone(self) -> "Block":
        copied = Block(
            type=self.type,
            fields=dict(self.fields)
        )

        for child in self.children:
            copied.add_child(
                child.clone()
            )

        return copied


class BlockDocument:
    def __init__(self):
        self.blocks: list[Block] = []

    def add(
        self,
        block: Block,
        index: int | None = None
    ) -> None:
        block.parent = None

        if index is None:
            self.blocks.append(block)
        else:
            self.blocks.insert(
                index,
                block
            )

    def remove(
        self,
        block: Block
    ) -> None:
        if block in self.blocks:
            self.blocks.remove(block)
            block.parent = None

    def clear(self) -> None:
        self.blocks.clear()

    def find(
        self,
        block_id: str
    ) -> Block | None:
        for block in self.walk():
            if block.id == block_id:
                return block

        return None

    def walk(self):
        for block in self.blocks:
            yield from self._walk(block)

    def _walk(
        self,
        block: Block
    ):
        yield block

        for child in block.children:
            yield from self._walk(child)

    def index_of(
        self,
        block: Block
    ) -> int:
        if block.parent is not None:
            return block.parent.children.index(
                block
            )

        return self.blocks.index(block)

    def move(
        self,
        block: Block,
        index: int
    ) -> None:
        if block.parent is not None:
            siblings = block.parent.children
        else:
            siblings = self.blocks

        if block not in siblings:
            return

        siblings.remove(block)

        index = max(
            0,
            min(
                index,
                len(siblings)
            )
        )

        siblings.insert(
            index,
            block
        )

    def to_dict(self) -> list[dict]:
        return [
            self._block_to_dict(block)
            for block in self.blocks
        ]

    def _block_to_dict(
        self,
        block: Block
    ) -> dict:
        return {
            "id": block.id,
            "type": block.type,
            "fields": dict(block.fields),
            "children": [
                self._block_to_dict(child)
                for child in block.children
            ]
        }

    @classmethod
    def from_dict(
        cls,
        data: list[dict]
    ) -> "BlockDocument":
        document = cls()

        for item in data:
            document.add(
                cls._block_from_dict(item)
            )

        return document

    @classmethod
    def _block_from_dict(
        cls,
        data: dict
    ) -> Block:
        block = Block(
            type=data.get(
                "type",
                "print"
            ),
            fields=dict(
                data.get(
                    "fields",
                    {}
                )
            ),
            id=data.get(
                "id",
                new_id()
            )
        )

        for child_data in data.get(
            "children",
            []
        ):
            block.add_child(
                cls._block_from_dict(
                    child_data
                )
            )

        return block


# ---------------------------------------------------------
# Han 블록 정의
# ---------------------------------------------------------

BLOCK_DEFINITIONS = {
    "print": {
        "name": "출력",
        "category": "표시",
        "color": "accent",
        "fields": {
            "value": '"안녕하세요"'
        }
    },

    "var": {
        "name": "변수",
        "category": "변수",
        "color": "keyword",
        "fields": {
            "name": "이름",
            "value": "0"
        }
    },

    "assign": {
        "name": "변수 바꾸기",
        "category": "변수",
        "color": "keyword",
        "fields": {
            "name": "이름",
            "value": "0"
        }
    },

    "input": {
        "name": "입력",
        "category": "입력",
        "color": "string",
        "fields": {
            "name": "입력값",
            "prompt": '"입력하세요: "'
        }
    },

    "if": {
        "name": "만약",
        "category": "흐름",
        "color": "operator",
        "fields": {
            "condition": "참"
        },
        "container": True
    },

    "else": {
        "name": "아니면",
        "category": "흐름",
        "color": "operator",
        "fields": {},
        "container": True
    },

    "repeat": {
        "name": "반복",
        "category": "흐름",
        "color": "operator",
        "fields": {
            "count": "10"
        },
        "container": True
    },

    "function": {
        "name": "함수",
        "category": "함수",
        "color": "boolean",
        "fields": {
            "name": "함수",
            "parameters": ""
        },
        "container": True
    }
}


def create_block(
    block_type: str
) -> Block:
    definition = BLOCK_DEFINITIONS.get(
        block_type
    )

    if definition is None:
        raise ValueError(
            f"알 수 없는 블록입니다: {block_type}"
        )

    return Block(
        type=block_type,
        fields=dict(
            definition.get(
                "fields",
                {}
            )
        )
    )