from __future__ import annotations

import tkinter as tk

from block_model import (
    BlockDocument,
    BLOCK_DEFINITIONS,
    create_block
)
from block_renderer import BlockRenderer
from block_converter import BlockConverter


class BlockEditor(tk.Frame):
    def __init__(self, master, app):
        self.app = app

        super().__init__(
            master,
            bg=self._color("window")
        )

        self.document = BlockDocument()

        self.drag_block = None
        self.selected_block = None
        self.drag_x = 0
        self.drag_y = 0

        self.drop_target = None
        self.drop_mode = None

        self.history = []
        self.future = []

        self._build_ui()

        self.renderer = BlockRenderer(
            self.canvas,
            self
        )

        self.refresh()

    # =========================================================
    # 색상
    # =========================================================

    def _color(self, key):
        palette = getattr(
            self.app,
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

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):
        self.columnconfigure(
            1,
            weight=1
        )

        self.rowconfigure(
            0,
            weight=1
        )

        # -----------------------------------------------------
        # 블록 팔레트
        # -----------------------------------------------------

        self.palette_frame = tk.Frame(
            self,
            width=190,
            bg=self._color("panel")
        )

        self.palette_frame.grid(
            row=0,
            column=0,
            sticky="ns"
        )

        self.palette_frame.grid_propagate(
            False
        )

        title = tk.Label(
            self.palette_frame,
            text="블록",
            anchor="w",
            padx=16,
            pady=13,
            bg=self._color("panel"),
            fg=self._color("fg"),
            font=("맑은 고딕", 11, "bold")
        )

        title.pack(
            fill="x"
        )

        self.palette = tk.Frame(
            self.palette_frame,
            bg=self._color("panel")
        )

        self.palette.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        self._build_palette()

        # -----------------------------------------------------
        # 작업 영역
        # -----------------------------------------------------

        self.workspace = tk.Frame(
            self,
            bg=self._color("editor")
        )

        self.workspace.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.workspace.rowconfigure(
            0,
            weight=1
        )

        self.workspace.columnconfigure(
            0,
            weight=1
        )

        self.canvas = tk.Canvas(
            self.workspace,
            bg=self._color("editor"),
            highlightthickness=0,
            bd=0
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.scrollbar = tk.Scrollbar(
            self.workspace,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.canvas.bind(
            "<Button-1>",
            self._canvas_click
        )

        self.canvas.bind(
            "<Configure>",
            lambda event: self.refresh()
        )

        self.canvas.bind(
            "<Delete>",
            lambda event: self.delete_selected()
        )

        self.canvas.bind(
            "<BackSpace>",
            lambda event: self.delete_selected()
        )

        self.canvas.bind(
            "<Control-z>",
            lambda event: self.undo()
        )

        self.canvas.bind(
            "<Control-y>",
            lambda event: self.redo()
        )

        self.canvas.bind(
            "<Control-c>",
            lambda event: self.copy_selected()
        )

        self.canvas.bind(
            "<Control-v>",
            lambda event: self.paste_block()
        )

        # -----------------------------------------------------
        # 상태 표시
        # -----------------------------------------------------

        self.status = tk.Label(
            self,
            text="블록을 왼쪽에서 작업 영역으로 끌어오세요.",
            anchor="w",
            padx=12,
            pady=6,
            bg=self._color("panel"),
            fg=self._color("muted"),
            font=("맑은 고딕", 9)
        )

        self.status.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew"
        )

    # =========================================================
    # 팔레트
    # =========================================================

    def _build_palette(self):
        categories = []

        for definition in BLOCK_DEFINITIONS.values():
            category = definition["category"]

            if category not in categories:
                categories.append(category)

        for category in categories:
            label = tk.Label(
                self.palette,
                text=category,
                anchor="w",
                bg=self._color("panel"),
                fg=self._color("muted"),
                font=("맑은 고딕", 9, "bold")
            )

            label.pack(
                fill="x",
                pady=(9, 3)
            )

            for block_type, definition in BLOCK_DEFINITIONS.items():
                if definition["category"] != category:
                    continue

                button = tk.Label(
                    self.palette,
                    text=definition["name"],
                    anchor="w",
                    padx=12,
                    pady=7,
                    bg=self._color("panel2"),
                    fg=self._color("fg"),
                    font=("맑은 고딕", 9),
                    cursor="hand2"
                )

                button.pack(
                    fill="x",
                    pady=2
                )

                button.bind(
                    "<ButtonPress-1>",
                    lambda event, t=block_type:
                    self._palette_press(
                        event,
                        t
                    )
                )

                button.bind(
                    "<B1-Motion>",
                    lambda event, t=block_type:
                    self._palette_motion(
                        event,
                        t
                    )
                )

                button.bind(
                    "<ButtonRelease-1>",
                    lambda event, t=block_type:
                    self._palette_release(
                        event,
                        t
                    )
                )

    # =========================================================
    # 팔레트 드래그
    # =========================================================

    def _palette_press(self, event, block_type):
        self.drag_block = create_block(
            block_type
        )

        self.drag_x = event.x_root
        self.drag_y = event.y_root

        self.status.configure(
            text=(
                f"{BLOCK_DEFINITIONS[block_type]['name']} "
                "블록을 작업 영역으로 끌어오세요."
            )
        )

    def _palette_motion(self, event, block_type):
        if self.drag_block is None:
            return

        self._show_drop_preview(
            event.x_root,
            event.y_root
        )

    def _palette_release(self, event, block_type):
        if self.drag_block is None:
            return

        block = self.drag_block
        self.drag_block = None

        x = (
            event.x_root
            - self.canvas.winfo_rootx()
        )

        y = (
            event.y_root
            - self.canvas.winfo_rooty()
        )

        self._clear_preview()

        if not self._inside_canvas(x, y):
            return

        self._save_history()

        self._insert_block_at(
            block,
            x,
            y
        )

        self.selected_block = block

        self.refresh()

        self.status.configure(
            text="블록을 추가했습니다."
        )

    # =========================================================
    # Canvas
    # =========================================================

    def _canvas_click(self, event):
        current = self.canvas.find_withtag(
            "current"
        )

        if not current:
            self.selected_block = None
            self.refresh()

            self.status.configure(
                text="블록을 선택하세요."
            )

    def _inside_canvas(self, x, y):
        return (
            0 <= x <= self.canvas.winfo_width()
            and
            0 <= y <= self.canvas.winfo_height()
        )

    # =========================================================
    # 블록 삽입
    # =========================================================

    def _insert_block_at(self, block, x, y):
        target = self._find_block_at(
            x,
            y,
            exclude=block
        )

        if target is None:
            index = self._calculate_index(y)

            self.document.add(
                block,
                index
            )

            return

        if self._can_contain(target):
            target.add_child(
                block
            )

            return

        parent = target.parent

        if parent is not None:
            siblings = parent.children
            index = siblings.index(target)

            if y > self._block_center_y(target):
                index += 1

            parent.insert_child(
                index,
                block
            )

            return

        index = self.document.blocks.index(
            target
        )

        if y > self._block_center_y(target):
            index += 1

        self.document.add(
            block,
            index
        )

    # =========================================================
    # 위치 계산
    # =========================================================

    def _calculate_index(self, y):
        if not self.document.blocks:
            return 0

        for index, block in enumerate(
            self.document.blocks
        ):
            center = self._block_center_y(
                block
            )

            if y < center:
                return index

        return len(
            self.document.blocks
        )

    def _block_center_y(self, block):
        bbox = self.renderer.get_block_bbox(
            block.id
        )

        if not bbox:
            return 0

        return (
            bbox[1] + bbox[3]
        ) / 2

    # =========================================================
    # 블록 검색
    # =========================================================

    def _find_block_at(
        self,
        x,
        y,
        exclude=None
    ):
        result = None
        distance = float("inf")

        for block in self.document.walk():
            if block is exclude:
                continue

            bbox = self.renderer.get_block_bbox(
                block.id
            )

            if not bbox:
                continue

            x1, y1, x2, y2 = bbox

            if x1 <= x <= x2 and y1 <= y <= y2:
                current_distance = abs(
                    y - ((y1 + y2) / 2)
                )

                if current_distance < distance:
                    result = block
                    distance = current_distance

        return result

    # =========================================================
    # 컨테이너
    # =========================================================

    def _can_contain(self, block):
        definition = BLOCK_DEFINITIONS.get(
            block.type,
            {}
        )

        return definition.get(
            "container",
            False
        )

    # =========================================================
    # 블록 이동
    # =========================================================

    def start_drag(self, event, block):
        self.selected_block = block
        self.drag_block = block

        self.drag_x = event.x_root
        self.drag_y = event.y_root

        self.status.configure(
            text=(
                f"{BLOCK_DEFINITIONS[block.type]['name']} "
                "블록을 이동하세요."
            )
        )

    def drag(self, event):
        if self.drag_block is None:
            return

        self._show_drop_preview(
            event.x_root,
            event.y_root
        )

    def end_drag(self, event):
        block = self.drag_block

        if block is None:
            return

        self.drag_block = None

        x = (
            event.x_root
            - self.canvas.winfo_rootx()
        )

        y = (
            event.y_root
            - self.canvas.winfo_rooty()
        )

        self._clear_preview()

        if not self._inside_canvas(x, y):
            self.refresh()
            return

        if self._is_descendant(
            block,
            self._find_block_at(
                x,
                y,
                exclude=block
            )
        ):
            self.refresh()
            return

        self._save_history()

        self._remove_from_parent(
            block
        )

        self._insert_block_at(
            block,
            x,
            y
        )

        self.selected_block = block

        self.refresh()

        self.status.configure(
            text="블록 순서를 변경했습니다."
        )

    def _is_descendant(self, block, target):
        if target is None:
            return False

        current = target

        while current is not None:
            if current is block:
                return True

            current = current.parent

        return False

    # =========================================================
    # 삭제
    # =========================================================

    def _remove_from_parent(self, block):
        if block.parent is not None:
            block.parent.remove_child(
                block
            )
        else:
            self.document.remove(
                block
            )

    def delete_selected(self):
        if self.selected_block is None:
            return

        self.delete_block(
            self.selected_block
        )

    def delete_block(self, block):
        self._save_history()

        self._remove_from_parent(
            block
        )

        if self.selected_block is block:
            self.selected_block = None

        self.refresh()

        self.status.configure(
            text="블록을 삭제했습니다."
        )

    # =========================================================
    # 드롭 미리보기
    # =========================================================

    def _show_drop_preview(
        self,
        root_x,
        root_y
    ):
        x = (
            root_x
            - self.canvas.winfo_rootx()
        )

        y = (
            root_y
            - self.canvas.winfo_rooty()
        )

        self._clear_preview()

        if not self._inside_canvas(x, y):
            return

        target = self._find_block_at(
            x,
            y,
            exclude=self.drag_block
        )

        if target is None:
            return

        bbox = self.renderer.get_block_bbox(
            target.id
        )

        if not bbox:
            return

        x1, y1, x2, y2 = bbox

        if (
            self._can_contain(target)
            and
            y > y1 + 38
        ):
            self.drop_target = target
            self.drop_mode = "inside"

            self.canvas.create_rectangle(
                x1 + 8,
                y1 + 82,
                x2 - 8,
                y2 - 8,
                outline=self._color("accent"),
                width=3,
                dash=(5, 4),
                tags=("drop_preview",)
            )

        else:
            self.drop_target = target
            self.drop_mode = "between"

            line_y = (
                y1
                if y < (y1 + y2) / 2
                else y2
            )

            self.canvas.create_line(
                x1,
                line_y,
                x2,
                line_y,
                fill=self._color("accent"),
                width=4,
                tags=("drop_preview",)
            )

    def _clear_preview(self):
        self.canvas.delete(
            "drop_preview"
        )

        self.drop_target = None
        self.drop_mode = None

    # =========================================================
    # 새로고침
    # =========================================================

    def refresh(self):
        if not hasattr(
            self,
            "renderer"
        ):
            return

        self.renderer.render(
            self.document.blocks,
            self.selected_block
        )

    # =========================================================
    # Han 코드 변환
    # =========================================================

    def get_source(self):
        return BlockConverter.to_han(
            self.document
        )

    def to_han(self):
        return self.get_source()

    def load_han(self, source):
        self._save_history()

        self.document = (
            BlockConverter.from_han(
                source
            )
        )

        self.selected_block = None

        self.refresh()

        self.status.configure(
            text="Han 코드를 블록으로 변환했습니다."
        )

    # =========================================================
    # 복사 / 붙여넣기
    # =========================================================

    def copy_selected(self):
        if self.selected_block is None:
            return

        self._clipboard = (
            self.selected_block.clone()
        )

        self.status.configure(
            text="블록을 복사했습니다."
        )

    def paste_block(self):
        block = getattr(
            self,
            "_clipboard",
            None
        )

        if block is None:
            return

        self._save_history()

        block = block.clone()

        self.document.add(
            block
        )

        self.selected_block = block

        self.refresh()

        self.status.configure(
            text="블록을 붙여넣었습니다."
        )

    # =========================================================
    # Undo / Redo
    # =========================================================

    def _save_history(self):
        self.history.append(
            self.document.to_dict()
        )

        if len(self.history) > 50:
            self.history.pop(0)

        self.future.clear()

    def undo(self):
        if not self.history:
            return

        self.future.append(
            self.document.to_dict()
        )

        state = self.history.pop()

        self.document = (
            BlockDocument.from_dict(
                state
            )
        )

        self.selected_block = None

        self.refresh()

        self.status.configure(
            text="실행을 취소했습니다."
        )

    def redo(self):
        if not self.future:
            return

        self.history.append(
            self.document.to_dict()
        )

        state = self.future.pop()

        self.document = (
            BlockDocument.from_dict(
                state
            )
        )

        self.selected_block = None

        self.refresh()

        self.status.configure(
            text="다시 실행했습니다."
        )

    # =========================================================
    # 테마
    # =========================================================

    def apply_theme(self):
        self.configure(
            bg=self._color("window")
        )

        self.palette_frame.configure(
            bg=self._color("panel")
        )

        self.palette.configure(
            bg=self._color("panel")
        )

        self.workspace.configure(
            bg=self._color("editor")
        )

        self.canvas.configure(
            bg=self._color("editor")
        )

        self.status.configure(
            bg=self._color("panel"),
            fg=self._color("muted")
        )

        self._rebuild_palette()

        self.refresh()

    def _rebuild_palette(self):
        for widget in self.palette.winfo_children():
            widget.destroy()

        self._build_palette()