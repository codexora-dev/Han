from __future__ import annotations

import tkinter as tk

from block_model import (
    BLOCK_DEFINITIONS,
    Block
)


class BlockRenderer:
    def __init__(self, canvas, editor):
        self.canvas = canvas
        self.editor = editor
        self.items = {}

    # =========================================================
    # 기본
    # =========================================================

    def clear(self):
        self.canvas.delete("all")
        self.items.clear()

    def render(
        self,
        blocks,
        selected_block=None
    ):
        self.clear()

        y = 30

        for block in blocks:
            height = self.draw_block(
                block,
                35,
                y,
                selected_block
            )

            y += height + 10

        self.canvas.configure(
            scrollregion=(
                0,
                0,
                max(
                    self.canvas.winfo_width(),
                    900
                ),
                max(
                    y + 50,
                    self.canvas.winfo_height()
                )
            )
        )

    # =========================================================
    # 블록
    # =========================================================

    def draw_block(
        self,
        block: Block,
        x: int,
        y: int,
        selected_block=None,
        width: int = 340
    ) -> int:

        definition = BLOCK_DEFINITIONS[
            block.type
        ]

        color = self.get_color(
            definition["color"]
        )

        height = self.get_height(
            block
        )

        selected = (
            selected_block is block
        )

        # -----------------------------------------------------
        # 외곽선
        # -----------------------------------------------------

        outline = (
            self.get_color("fg")
            if selected
            else color
        )

        outline_width = (
            3
            if selected
            else 2
        )

        body = self.canvas.create_polygon(
            self._shape(
                x,
                y,
                width,
                height,
                block.type
            ),
            fill=self.get_color("panel2"),
            outline=outline,
            width=outline_width,
            tags=("block", block.id)
        )

        # -----------------------------------------------------
        # 헤더
        # -----------------------------------------------------

        header = self.canvas.create_polygon(
            self._header_shape(
                x,
                y,
                width,
                38
            ),
            fill=color,
            outline=color,
            tags=("block", block.id)
        )

        # -----------------------------------------------------
        # 제목
        # -----------------------------------------------------

        title = self.canvas.create_text(
            x + 15,
            y + 19,
            text=definition["name"],
            anchor="w",
            fill="#ffffff",
            font=("맑은 고딕", 10, "bold"),
            tags=("block", block.id)
        )

        # -----------------------------------------------------
        # 삭제
        # -----------------------------------------------------

        delete = self.canvas.create_text(
            x + width - 18,
            y + 19,
            text="×",
            anchor="center",
            fill="#ffffff",
            font=("맑은 고딕", 13, "bold"),
            tags=("delete", block.id)
        )

        self.items[block.id] = {
            "body": body,
            "header": header,
            "title": title,
            "delete": delete
        }

        self._bind_block(
            block
        )

        # -----------------------------------------------------
        # 필드
        # -----------------------------------------------------

        self.draw_fields(
            block,
            x,
            y,
            width
        )

        # -----------------------------------------------------
        # 내부 블록
        # -----------------------------------------------------

        if definition.get(
            "container",
            False
        ):
            self.draw_container(
                block,
                x,
                y,
                width,
                height,
                selected_block
            )

        return height

    # =========================================================
    # 필드
    # =========================================================

    def draw_fields(
        self,
        block,
        x,
        y,
        width
    ):
        fields = block.fields

        if block.type == "print":

            self.field(
                block,
                x + 16,
                y + 58,
                fields.get(
                    "value",
                    ""
                ),
                "value"
            )

        elif block.type in {
            "var",
            "assign"
        }:

            self.label(
                x + 16,
                y + 58,
                "이름"
            )

            self.field(
                block,
                x + 60,
                y + 58,
                fields.get(
                    "name",
                    ""
                ),
                "name"
            )

            self.label(
                x + 165,
                y + 58,
                "="
            )

            self.field(
                block,
                x + 185,
                y + 58,
                fields.get(
                    "value",
                    "0"
                ),
                "value"
            )

        elif block.type == "input":

            self.label(
                x + 16,
                y + 58,
                "변수"
            )

            self.field(
                block,
                x + 60,
                y + 58,
                fields.get(
                    "name",
                    ""
                ),
                "name"
            )

            self.label(
                x + 165,
                y + 58,
                "안내"
            )

            self.field(
                block,
                x + 200,
                y + 58,
                fields.get(
                    "prompt",
                    ""
                ),
                "prompt"
            )

        elif block.type == "if":

            self.label(
                x + 16,
                y + 58,
                "조건"
            )

            self.field(
                block,
                x + 55,
                y + 58,
                fields.get(
                    "condition",
                    "참"
                ),
                "condition"
            )

        elif block.type == "repeat":

            self.label(
                x + 16,
                y + 58,
                "반복"
            )

            self.field(
                block,
                x + 55,
                y + 58,
                fields.get(
                    "count",
                    "10"
                ),
                "count"
            )

            self.label(
                x + 150,
                y + 58,
                "회"
            )

        elif block.type == "function":

            self.label(
                x + 16,
                y + 58,
                "이름"
            )

            self.field(
                block,
                x + 55,
                y + 58,
                fields.get(
                    "name",
                    "함수"
                ),
                "name"
            )

            self.label(
                x + 170,
                y + 58,
                "매개변수"
            )

            self.field(
                block,
                x + 235,
                y + 58,
                fields.get(
                    "parameters",
                    ""
                ),
                "parameters"
            )

    def field(
        self,
        block,
        x,
        y,
        value,
        key
    ):
        width = max(
            70,
            min(
                210,
                len(str(value)) * 8 + 25
            )
        )

        rect = self.canvas.create_rectangle(
            x,
            y - 13,
            x + width,
            y + 13,
            fill=self.get_color("field"),
            outline=self.get_color("line"),
            tags=("field", block.id)
        )

        text = self.canvas.create_text(
            x + 8,
            y,
            text=str(value),
            anchor="w",
            fill=self.get_color("fg"),
            font=("맑은 고딕", 9),
            tags=("field", block.id)
        )

        self.canvas.tag_bind(
            rect,
            "<Double-Button-1>",
            lambda event, b=block, k=key:
            self.edit_field(
                b,
                k,
                event
            )
        )

        self.canvas.tag_bind(
            text,
            "<Double-Button-1>",
            lambda event, b=block, k=key:
            self.edit_field(
                b,
                k,
                event
            )
        )

    def label(
        self,
        x,
        y,
        text
    ):
        self.canvas.create_text(
            x,
            y,
            text=text,
            anchor="w",
            fill=self.get_color("fg"),
            font=("맑은 고딕", 9)
        )

    # =========================================================
    # 컨테이너
    # =========================================================

    def draw_container(
        self,
        block,
        x,
        y,
        width,
        height,
        selected_block=None
    ):
        top = y + 90

        self.canvas.create_line(
            x + 12,
            top - 12,
            x + width - 12,
            top - 12,
            fill=self.get_color("line"),
            width=1,
            tags=("block", block.id)
        )

        self.canvas.create_text(
            x + 16,
            top - 1,
            text="블록을 여기에 넣으세요",
            anchor="w",
            fill=self.get_color("muted"),
            font=("맑은 고딕", 8),
            tags=("block", block.id)
        )

        child_y = top + 15

        for child in block.children:
            child_height = self.draw_block(
                child,
                x + 22,
                child_y,
                selected_block,
                width - 44
            )

            child_y += (
                child_height + 7
            )

    # =========================================================
    # 블록 모양
    # =========================================================

    def _shape(
        self,
        x,
        y,
        width,
        height,
        block_type
    ):
        if block_type in {
            "if",
            "repeat",
            "function"
        }:
            return [
                x,
                y,
                x + width,
                y,
                x + width,
                y + height,
                x + 18,
                y + height,
                x + 18,
                y + height - 12,
                x,
                y + height - 12
            ]

        return [
            x,
            y,
            x + width,
            y,
            x + width,
            y + height,
            x,
            y + height
        ]

    def _header_shape(
        self,
        x,
        y,
        width,
        height
    ):
        return [
            x,
            y,
            x + width,
            y,
            x + width,
            y + height,
            x + 18,
            y + height,
            x + 10,
            y + height + 8,
            x,
            y + height
        ]

    # =========================================================
    # 크기
    # =========================================================

    def get_height(self, block):
        base = 105

        if block.type in {
            "if",
            "repeat",
            "function"
        }:
            base = 120

            for child in block.children:
                base += (
                    self.get_height(child)
                    + 7
                )

        return base

    # =========================================================
    # 이벤트
    # =========================================================

    def _bind_block(self, block):
        items = self.items.get(
            block.id,
            {}
        )

        for name, item in items.items():

            if name == "delete":
                self.canvas.tag_bind(
                    item,
                    "<Button-1>",
                    lambda event, b=block:
                    self.editor.delete_block(b)
                )

                continue

            self.canvas.tag_bind(
                item,
                "<ButtonPress-1>",
                lambda event, b=block:
                self.editor.start_drag(
                    event,
                    b
                )
            )

            self.canvas.tag_bind(
                item,
                "<B1-Motion>",
                lambda event:
                self.editor.drag(
                    event
                )
            )

            self.canvas.tag_bind(
                item,
                "<ButtonRelease-1>",
                lambda event:
                self.editor.end_drag(
                    event
                )
            )

    # =========================================================
    # 블록 영역
    # =========================================================

    def get_block_bbox(
        self,
        block_id
    ):
        items = self.items.get(
            block_id
        )

        if not items:
            return None

        body = items.get(
            "body"
        )

        if body is None:
            return None

        return self.canvas.bbox(
            body
        )

    # =========================================================
    # 필드 편집
    # =========================================================

    def edit_field(
        self,
        block,
        key,
        event
    ):
        bbox = self.canvas.bbox(
            "current"
        )

        if not bbox:
            return

        x1, y1, x2, y2 = bbox

        entry = tk.Entry(
            self.canvas,
            bd=0,
            relief="flat",
            bg=self.get_color("field"),
            fg=self.get_color("fg"),
            insertbackground=self.get_color("fg"),
            font=("맑은 고딕", 9)
        )

        entry.insert(
            0,
            str(
                block.fields.get(
                    key,
                    ""
                )
            )
        )

        window = self.canvas.create_window(
            x1,
            (y1 + y2) // 2,
            anchor="w",
            window=entry,
            width=max(
                100,
                x2 - x1
            )
        )

        entry.focus_set()

        entry.select_range(
            0,
            tk.END
        )

        finished = [False]

        def finish(_event=None):
            if finished[0]:
                return

            finished[0] = True

            block.fields[key] = (
                entry.get()
            )

            self.canvas.delete(
                window
            )

            self.editor.refresh()

        entry.bind(
            "<Return>",
            finish
        )

        entry.bind(
            "<FocusOut>",
            finish
        )

        entry.bind(
            "<Escape>",
            lambda _event:
            self._cancel_field(
                window,
                entry,
                finished
            )
        )

    def _cancel_field(
        self,
        window,
        entry,
        finished
    ):
        if finished[0]:
            return

        finished[0] = True

        self.canvas.delete(
            window
        )

        entry.destroy()

        self.editor.refresh()

    # =========================================================
    # 색상
    # =========================================================

    def get_color(self, key):
        palette = getattr(
            self.editor.app,
            "palette",
            {}
        )

        defaults = {
            "window": "#181a1f",
            "editor": "#181a1f",
            "panel": "#242730",
            "panel2": "#2c303a",
            "field": "#15171c",
            "line": "#414754",
            "fg": "#eef0f4",
            "muted": "#a9b0bd",
            "accent": "#4d9cff",
            "keyword": "#c586c0",
            "string": "#ce9178",
            "operator": "#dcdcaa",
            "boolean": "#569cd6"
        }

        return palette.get(
            key,
            defaults.get(
                key,
                "#ffffff"
            )
        )