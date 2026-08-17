from __future__ import annotations

import json
import threading
import queue
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
import webbrowser
from tkinter import (
    BOTH,
    BOTTOM,
    END,
    HORIZONTAL,
    LEFT,
    RIGHT,
    TOP,
    VERTICAL,
    X,
    Y,
    BooleanVar,
    filedialog,
    font,
    messagebox,
    simpledialog,
    ttk,
)


APP_DIR = Path(__file__).resolve().parent
DEFAULT_HAN_ROOT = APP_DIR.parent
SETTINGS_FILE = APP_DIR / "settings.json"

THEMES = {
    "Han Dark": {
        "window": "#181a1f",
        "editor": "#20232a",
        "panel": "#242730",
        "panel2": "#2c303a",
        "line": "#373b46",
        "fg": "#eef0f4",
        "muted": "#a9b0bd",
        "select": "#334966",
        "accent": "#4d9cff",
        "keyword": "#ffd166",
        "string": "#9be28f",
        "number": "#ff9f7a",
        "comment": "#8892a0",
        "operator": "#75d7ff",
        "boolean": "#d6a2ff",
        "error": "#ff6b7a",
        "console": "#15171c",
    },
    "Han Light": {
        "window": "#f4f6fb",
        "editor": "#ffffff",
        "panel": "#eef1f7",
        "panel2": "#ffffff",
        "line": "#d8deea",
        "fg": "#1d2430",
        "muted": "#667085",
        "select": "#d8e9ff",
        "accent": "#1769e0",
        "keyword": "#935c00",
        "string": "#227a3a",
        "number": "#b54708",
        "comment": "#77808f",
        "operator": "#006c8f",
        "boolean": "#6941c6",
        "error": "#c0262d",
        "console": "#ffffff",
    },
}

KEYWORDS = {
    "출력",
    "변수",
    "입력",
    "만약",
    "아니면",
    "반복",
    "끝",
    "참",
    "거짓",
    "그리고",
    "또는",
    "아니다",
    "함수"
}

KEYWORD_PATTERN = re.compile(
    r"(?<![\w가-힣])(" + "|".join(map(re.escape, sorted(KEYWORDS, key=len, reverse=True))) + r")(?![\w가-힣])"
)
BOOLEAN_PATTERN = re.compile(r"(?<![\w가-힣])(참|거짓)(?![\w가-힣])")
STRING_PATTERN = re.compile(r'"(?:\\.|[^"\\])*"')
NUMBER_PATTERN = re.compile(r"(?<![\w가-힣])\d+(?:\.\d+)?(?![\w가-힣])")
COMMENT_PATTERN = re.compile(r"(#.*|//.*)$")
OPERATOR_PATTERN = re.compile(r"(==|!=|<=|>=|[+\-*/%=<>])")


def choose_font(preferred: list[str]) -> str:
    try:
        installed = set(font.families())
    except tk.TclError:
        return preferred[-1]

    for name in preferred:
        if name in installed:
            return name
    return preferred[-1]


@dataclass
class Settings:
    theme: str = "Han Dark"
    font_family: str = "맑은 고딕"
    font_size: int = 13
    show_line_numbers: bool = True
    word_wrap: bool = False
    han_root: str = str(DEFAULT_HAN_ROOT)
    first_run: bool = True

    @classmethod
    def load(cls) -> "Settings":
        base = cls()
        if not SETTINGS_FILE.exists():
            return base

        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return base

        settings = cls(**{**base.__dict__, **data})
        if settings.font_family in {"Consolas", "궁서", "Gungsuh", "Batang"}:
            settings.font_family = "맑은 고딕"
        return settings

    def save(self) -> None:
        SETTINGS_FILE.write_text(json.dumps(self.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")


class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget: tk.Text, **kwargs):
        super().__init__(master, width=54, highlightthickness=0, **kwargs)
        self.text_widget = text_widget
        self.fg = "#a9b0bd"

    def redraw(self) -> None:
        self.delete("all")
        if self.text_widget is None:
            return

        index = self.text_widget.index("@0,0")
        while True:
            info = self.text_widget.dlineinfo(index)
            if info is None:
                break
            line = str(index).split(".")[0]
            self.create_text(44, info[1], anchor="ne", text=line, fill=self.fg)
            index = self.text_widget.index(f"{index}+1line")


class EditorTab(ttk.Frame):
    def __init__(self, master, app: "HanIDE", path: Path | None = None, content: str = ""):
        super().__init__(master)
        self.app = app
        self.path = path
        self.dirty = False
        self._highlight_job = None

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.line_numbers = LineNumbers(self, None)
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        self.text = tk.Text(
            self,
            undo=True,
            maxundo=300,
            borderwidth=0,
            highlightthickness=0,
            padx=14,
            pady=10,
            insertwidth=2,
            spacing1=1,
            spacing3=1,
            tabs=("1.6c",),
            wrap="none",
        )
        self.line_numbers.text_widget = self.text
        self.text.grid(row=0, column=1, sticky="nsew")

        y_scroll = ttk.Scrollbar(self, orient=VERTICAL, command=self._scroll_y)
        y_scroll.grid(row=0, column=2, sticky="ns")
        self.text.configure(yscrollcommand=lambda *args: self._text_scrolled(y_scroll, *args))

        x_scroll = ttk.Scrollbar(self, orient=HORIZONTAL, command=self.text.xview)
        x_scroll.grid(row=1, column=1, sticky="ew")
        self.text.configure(xscrollcommand=x_scroll.set)

        self.text.insert("1.0", content)
        self.text.edit_modified(False)
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._schedule_highlight)
        self.text.bind("<ButtonRelease-1>", self._cursor_changed)
        self.text.bind("<MouseWheel>", self._view_changed)
        self.text.bind("<Configure>", self._view_changed)

        self.apply_settings()
        self.highlight()

    @property
    def title(self) -> str:
        name = self.path.name if self.path else "새 파일.han"
        return f"* {name}" if self.dirty else name

    def content(self) -> str:
        return self.text.get("1.0", "end-1c")

    def mark_clean(self) -> None:
        self.dirty = False
        self.text.edit_modified(False)
        self.app.refresh_tab_title(self)

    def apply_settings(self) -> None:
        p = self.app.palette
        editor_font = font.Font(family=self.app.settings.font_family, size=self.app.settings.font_size)
        bold_font = font.Font(family=self.app.settings.font_family, size=self.app.settings.font_size, weight="bold")

        self.configure(style="Editor.TFrame")
        self.text.configure(
            bg=p["editor"],
            fg=p["fg"],
            insertbackground=p["fg"],
            selectbackground=p["select"],
            selectforeground=p["fg"],
            font=editor_font,
            wrap="word" if self.app.settings.word_wrap else "none",
        )
        self.line_numbers.configure(bg=p["panel"])
        self.line_numbers.fg = p["muted"]
        self.line_numbers.grid() if self.app.settings.show_line_numbers else self.line_numbers.grid_remove()

        self.text.tag_configure("keyword", foreground=p["keyword"], font=bold_font)
        self.text.tag_configure("boolean", foreground=p["boolean"], font=bold_font)
        self.text.tag_configure("string", foreground=p["string"])
        self.text.tag_configure("number", foreground=p["number"])
        self.text.tag_configure("comment", foreground=p["comment"])
        self.text.tag_configure("operator", foreground=p["operator"])
        self.text.tag_configure("search", background=p["accent"], foreground="#ffffff")
        self.highlight()

    def highlight(self) -> None:
        for tag in ("keyword", "boolean", "string", "number", "comment", "operator"):
            self.text.tag_remove(tag, "1.0", END)

        source = self.content()
        self._apply(OPERATOR_PATTERN, "operator", source)
        self._apply(NUMBER_PATTERN, "number", source)
        self._apply(KEYWORD_PATTERN, "keyword", source)
        self._apply(BOOLEAN_PATTERN, "boolean", source)
        self._apply(STRING_PATTERN, "string", source)

        offset = 0
        for line in source.splitlines(True):
            match = COMMENT_PATTERN.search(line.rstrip("\n"))
            if match:
                self._tag(offset + match.start(), offset + match.end(), "comment")
            offset += len(line)

        self.line_numbers.redraw()

    def _apply(self, pattern: re.Pattern, tag: str, source: str) -> None:
        for match in pattern.finditer(source):
            self._tag(match.start(), match.end(), tag)

    def _tag(self, start: int, end: int, tag: str) -> None:
        self.text.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

    def _schedule_highlight(self, _event=None) -> None:
        if self._highlight_job is not None:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(120, self.highlight)
        self._cursor_changed()

    def _on_modified(self, _event=None) -> None:
        if self.text.edit_modified():
            self.dirty = True
            self.app.refresh_tab_title(self)
            self.text.edit_modified(False)
        self._cursor_changed()

    def _cursor_changed(self, _event=None) -> None:
        self.app.update_status()
        self.line_numbers.redraw()

    def _view_changed(self, _event=None) -> None:
        self.after_idle(self.line_numbers.redraw)

    def _text_scrolled(self, scrollbar, first, last) -> None:
        scrollbar.set(first, last)
        self.line_numbers.redraw()

    def _scroll_y(self, *args) -> None:
        self.text.yview(*args)
        self.line_numbers.redraw()


class SettingsDialog(tk.Toplevel):
    def __init__(self, app: "HanIDE"):
        super().__init__(app.root)
        self.app = app
        self.title("설정")
        self.resizable(False, False)
        self.transient(app.root)
        self.grab_set()

        self.theme_var = tk.StringVar(value=app.settings.theme)
        self.font_var = tk.StringVar(value=app.settings.font_family)
        self.size_var = tk.IntVar(value=app.settings.font_size)
        self.line_var = BooleanVar(value=app.settings.show_line_numbers)
        self.wrap_var = BooleanVar(value=app.settings.word_wrap)
        self.root_var = tk.StringVar(value=app.settings.han_root)

        body = ttk.Frame(self, padding=18)
        body.pack(fill=BOTH, expand=True)

        self._label(body, "테마", 0)
        ttk.Combobox(body, textvariable=self.theme_var, values=list(THEMES), state="readonly", width=28).grid(row=0, column=1, sticky="ew", pady=6)

        self._label(body, "글꼴", 1)
        fonts = sorted(font.families())
        ttk.Combobox(body, textvariable=self.font_var, values=fonts, width=28).grid(row=1, column=1, sticky="ew", pady=6)

        self._label(body, "글자 크기", 2)
        ttk.Spinbox(body, textvariable=self.size_var, from_=10, to=24, width=8).grid(row=2, column=1, sticky="w", pady=6)

        ttk.Checkbutton(body, text="줄 번호 표시", variable=self.line_var).grid(row=3, column=1, sticky="w", pady=6)
        ttk.Checkbutton(body, text="자동 줄바꿈", variable=self.wrap_var).grid(row=4, column=1, sticky="w", pady=6)

        self._label(body, "Han 폴더", 5)
        root_row = ttk.Frame(body)
        root_row.grid(row=5, column=1, sticky="ew", pady=6)
        ttk.Entry(root_row, textvariable=self.root_var, width=38).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(root_row, text="찾기", command=self.choose_root).pack(side=RIGHT, padx=(8, 0))

        buttons = ttk.Frame(body)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="취소", command=self.destroy).pack(side=RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="적용", command=self.apply).pack(side=RIGHT)

    def _label(self, parent, text: str, row: int) -> None:
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=6)

    def choose_root(self) -> None:
        path = filedialog.askdirectory(title="Han 프로젝트 폴더 선택", initialdir=self.root_var.get())
        if path:
            self.root_var.set(path)

    def apply(self) -> None:
        self.app.settings.theme = self.theme_var.get()
        self.app.settings.font_family = self.font_var.get()
        self.app.settings.font_size = int(self.size_var.get())
        self.app.settings.show_line_numbers = self.line_var.get()
        self.app.settings.word_wrap = self.wrap_var.get()
        self.app.settings.han_root = self.root_var.get()
        self.app.settings.save()
        self.app.load_workspace(Path(self.app.settings.han_root))
        self.app.apply_settings()
        self.destroy()


class HanIDE:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Han IDE")
        self.root.geometry("1220x780")
        self.root.minsize(900, 580)

        icon_path = Path(__file__).parent.parent /"assets"/"icon"/"Han_Logo.ico"

        print("아이콘 경로:", icon_path)
        print("아이콘 존재:", icon_path.exists())

        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))

        self.settings = Settings.load()
        self.settings.font_family = choose_font([self.settings.font_family, "맑은 고딕", "Malgun Gothic", "D2Coding", "Cascadia Mono", "Arial"])
        self.palette = THEMES[self.settings.theme if self.settings.theme in THEMES else "Han Dark"]
        self.workspace = Path(self.settings.han_root)

        self.process: subprocess.Popen | None = None
        self.output_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.console_input_start = "1.0"

        self._build_styles()
        self._build_menu()
        self._build_layout()
        self.apply_settings()
        self.load_workspace(self.workspace)
        self.open_start_file()
        self._bind_shortcuts()

        if self.settings.first_run:
            self.show_welcome_message()
            self.settings.first_run = False


    def _build_styles(self) -> None:
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="새 파일", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="열기", accelerator="Ctrl+O", command=self.open_file_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="저장", accelerator="Ctrl+S", command=self.save_current)
        file_menu.add_command(label="다른 이름으로 저장", accelerator="Ctrl+Shift+S", command=self.save_current_as)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.on_close)
        menubar.add_cascade(label="파일", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="찾기", accelerator="Ctrl+F", command=self.find_text)
        edit_menu.add_command(label="모두 선택", accelerator="Ctrl+A", command=self.select_all)
        menubar.add_cascade(label="편집", menu=edit_menu)

        run_menu = tk.Menu(menubar, tearoff=False)
        run_menu.add_command(label="컴파일", accelerator="F6", command=self.compile_current)
        run_menu.add_command(label="저장 후 실행", accelerator="F5", command=self.run_current)
        run_menu.add_command(label="실행 중지", command=self.stop_process)
        menubar.add_cascade(label="실행", menu=run_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="설정", command=self.open_settings)
        menubar.add_cascade(label="보기", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="보고", command=self.open_report)
        help_menu.add_command(label="Han IDE 정보", command = self.show_about)
        menubar.add_cascade(label="도움말", menu=help_menu)

    def _build_layout(self) -> None:
        self.toolbar = ttk.Frame(self.root, padding = (10,8))
        self.toolbar.pack(side=TOP, fill=X)

        for label, command in [
            ("새 파일", self.new_file),
            ("열기", self.open_file_dialog),
            ("저장", self.save_current),
            ("컴파일", self.compile_current),
            ("실행(F5)", self.run_current),
            ("설정", self.open_settings),
            ("보고", self.open_report),
            ("실행 중지", self.stop_process)
        ]:

            ttk.Button(self.toolbar, text = label, command=command).pack(side=LEFT,padx=(0,6))

        self.main_pane = ttk.PanedWindow(self.root, orient=HORIZONTAL)
        self.main_pane.pack(side=TOP, fill=BOTH, expand=True)

        self.editor_pane = ttk.PanedWindow(self.main_pane, orient=VERTICAL)
        self.main_pane.add(self.editor_pane, weigh=1)

        self.notebook = ttk.Notebook(self.editor_pane)
        self.editor_pane.add(self.notebook, weight=5)

        self.notebook.bind("<<NotebookTabChanged>>", lambda _event: self.update_status())

        self.notebook.bind("<Button-3>", self._notebook_right_click)

        console_frame = ttk.Frame(self.editor_pane)
        self.editor_pane.add(console_frame, weight=1)

        console_top = ttk.Frame(console_frame)
        console_top.pack(side=TOP, fill=X)

        ttk.Label(console_top, text="콘솔", padding=(10,6)).pack(side=LEFT)

        ttk.Button(console_top, text="지우기", command=self.clear_console).pack(side=RIGHT, padx=8, pady=5)

        self.console = tk.Text(console_frame, height=9, state="disabled", borderwidth=0, highlightthickness=0, padx=12,pady=9)
        self.console.pack(side=LEFT, fill=BOTH, expand=True)

        self.console.bind("<Return>", self._console_enter)
        self.console.bind("<BackSpace>", self._console_backspace)
        self.console.bind("<Key>", self._console_key)

        console_scroll = ttk.Scrollbar(console_frame, orient=VERTICAL, command=self.console.yview)
        console_scroll.pack(side=RIGHT, fill=Y)

        self.console.configure(yscrollcommand=console_scroll.set)

        self.status = ttk.Label(self.root,anchor="w",padding=(10,5))
        self.status.pack(side=BOTTOM, fill=X)

    def _bind_shortcuts(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Control-n>", lambda _event: self.new_file())
        self.root.bind("<Control-o>", lambda _event: self.open_file_dialog())
        self.root.bind("<Control-s>", lambda _event: self.save_current())
        self.root.bind("<Control-Shift-S>", lambda _event: self.save_current_as())
        self.root.bind("<Control-f>", lambda _event: self.find_text())
        self.root.bind("<Control-a>", lambda _event: self.select_all())
        self.root.bind("<F5>", lambda _event: self.run_current())
        self.root.bind("<F6>", lambda _event: self.compile_current())

    def apply_settings(self) -> None:
        self.palette = THEMES[self.settings.theme if self.settings.theme in THEMES else "Han Dark"]
        p = self.palette

        self.root.configure(bg=p["window"])
        ui_font = (self.settings.font_family, 10)
        self.style.configure(".", font=ui_font, background=p["panel"], foreground=p["fg"], fieldbackground=p["panel2"], bordercolor=p["line"])
        self.style.configure("TFrame", background=p["panel"])
        self.style.configure("Editor.TFrame", background=p["editor"])
        self.style.configure("TLabel", background=p["panel"], foreground=p["fg"])
        self.style.configure("TButton", background=p["panel2"], foreground=p["fg"], padding=(10, 5), borderwidth=1)
        self.style.map("TButton", background=[("active", p["select"])])
        self.style.configure("Treeview", background=p["panel"], foreground=p["fg"], fieldbackground=p["panel"], rowheight=25, borderwidth=0)
        self.style.map("Treeview", background=[("selected", p["select"])], foreground=[("selected", p["fg"])])
        self.style.configure("TNotebook", background=p["panel"])
        self.style.configure("TNotebook.Tab", background=p["panel2"], foreground=p["fg"], padding=(14, 7))
        self.style.map("TNotebook.Tab", background=[("selected", p["editor"])])

        console_font = (self.settings.font_family, max(10, self.settings.font_size - 1))
        self.console.configure(bg=p["console"], fg=p["fg"], insertbackground=p["fg"], selectbackground=p["select"], font=console_font)
        self.console.tag_configure("ok", foreground=p["string"])
        self.console.tag_configure("error", foreground=p["error"])
        self.console.tag_configure("muted", foreground=p["muted"])

        for tab in self.tabs():
            tab.apply_settings()
        self.update_status()

    def open_start_file(self) -> None:
        start = self.workspace / "examples" / "hello.han"
        if start.exists():
            self.open_file(start)
        else:
            self.new_file()

    def load_workspace(self, path: Path) -> None:
        self.workspace = path
        self.settings.han_root = str(path)

    def new_file(self) -> None:
        tab = EditorTab(self.notebook, self)
        self.notebook.add(tab, text=tab.title)
        self.notebook.select(tab)
        tab.text.focus_set()

    def open_file_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="파일 열기",
            initialdir=self.workspace,
            filetypes=[("Han 파일", "*.han"), ("Python 파일", "*.py"), ("모든 파일", "*.*")],
        )
        if path:
            self.open_file(Path(path))

    def open_file(self, path: Path) -> None:
        for tab in self.tabs():
            if tab.path and tab.path.resolve() == path.resolve():
                self.notebook.select(tab)
                return

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            messagebox.showerror("열기 실패", "UTF-8 텍스트 파일만 열 수 있습니다.")
            return
        except OSError as error:
            messagebox.showerror("열기 실패", str(error))
            return

        tab = EditorTab(self.notebook, self, path, content)
        self.notebook.add(tab, text=tab.title)
        self.notebook.select(tab)
        tab.mark_clean()
        tab.text.focus_set()

    def save_current(self) -> bool:
        tab = self.current_tab()
        if tab is None:
            return False
        if tab.path is None:
            return self.save_current_as()

        try:
            tab.path.write_text(tab.content(), encoding="utf-8")
        except OSError as error:
            messagebox.showerror("저장 실패", str(error))
            return False

        tab.mark_clean()
        self.write_console(f"저장됨: {tab.path}\n", "muted")
        return True

    def save_current_as(self) -> bool:
        tab = self.current_tab()
        if tab is None:
            return False
        path = filedialog.asksaveasfilename(
            title="다른 이름으로 저장",
            initialdir=self.workspace,
            defaultextension=".han",
            filetypes=[("Han 파일", "*.han"), ("Python 파일", "*.py"), ("모든 파일", "*.*")],
        )
        if not path:
            return False
        tab.path = Path(path)
        return self.save_current()

    def compile_current(self) -> None:
        tab = self.current_tab()
        if tab is None or not self.save_before_run(tab):
            return
        if tab.path.suffix.lower() != ".han":
            messagebox.showinfo("컴파일", "Han 파일(.han)만 컴파일할 수 있습니다.")
            return
        self.run_han([str(tab.path)], "컴파일")

    def run_current(self) -> None:
        tab = self.current_tab()
        if tab is None or not self.save_before_run(tab):
            return
        if tab.path.suffix.lower() != ".han":
            messagebox.showinfo("실행", "Han 파일(.han)만 실행할 수 있습니다.")
            return
        self.run_han([str(tab.path), "--실행"], "실행")

    def save_before_run(self, tab: EditorTab) -> bool:
        if tab.path is None:
            return self.save_current_as()
        if tab.dirty:
            return self.save_current()
        return True

    def run_han(
            self,
            args: list[str],
            title: str,
            stdin: str | None = None
        ) -> None:

        if self.process is not None:
            self.write_console(
                "이미 실행 중인 프로그램이 있습니다.\n",
                "error"
            )
            return

        han_main = self.workspace / "main.py"

        if not han_main.exists():
            messagebox.showerror(
                "Han 경로 오류",
                f"Han 프로젝트를 찾을 수 없습니다.\n{self.workspace}"
            )
            return

        command = [
            sys.executable,
            "-u",
            str(han_main),
            *args
        ]

        self.write_console(
            f"\n[{title}] {' '.join(command)}\n",
            "muted"
        )

        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                cwd=self.workspace,
                bufsize=0,
            )

        except OSError as error:
            self.process = None
            self.write_console(
                f"실행 실패: {error}\n",
                "error"
            )
            return

        self.console.configure(state="normal")
        self.console_input_start = self.console.index("end-1c")
        self.console.mark_set("insert", "end-1c")
        self.console.focus_set()

        # 미리 전달할 stdin
        if stdin is not None and self.process.stdin is not None:
            try:
                self.process.stdin.write(stdin)
                self.process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

        # stdout
        threading.Thread(
            target=self._read_process_output,
            args=(self.process.stdout, "stdout"),
            daemon=True
        ).start()

        # stderr
        threading.Thread(
            target=self._read_process_output,
            args=(self.process.stderr, "stderr"),
            daemon=True
        ).start()

        # 프로세스 종료 감시
        threading.Thread(
            target=self._wait_process,
            args=(self.process,),
            daemon=True
        ).start()

        self.root.after(50, self._process_output_loop)


    def find_text(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        query = simpledialog.askstring("찾기", "찾을 문자열을 입력하세요.", parent=self.root)
        if not query:
            return

        tab.text.tag_remove("search", "1.0", END)
        start = "1.0"
        first = None
        while True:
            index = tab.text.search(query, start, stopindex=END)
            if not index:
                break
            end = f"{index}+{len(query)}c"
            tab.text.tag_add("search", index, end)
            first = first or index
            start = end

        if first:
            tab.text.mark_set("insert", first)
            tab.text.see(first)
        else:
            messagebox.showinfo("찾기", "검색 결과가 없습니다.")

    def select_all(self) -> None:
        tab = self.current_tab()
        if tab:
            tab.text.tag_add("sel", "1.0", END)
            tab.text.focus_set()

    def open_settings(self) -> None:
        SettingsDialog(self)

    def clear_console(self) -> None:
        self.console.configure(state="normal")
        self.console.delete("1.0", END)
        self.console.configure(state="disabled")

    def write_console(
            self,
            text: str,
            tag: str | None = None
        ) -> None:

        self.console.configure(state="normal")

        self.console.insert(END, text, tag)
        self.console.see(END)

        if self.process is None:
            self.console.configure(state="disabled")
    
    def update_status(self) -> None:
        tab = self.current_tab()

        if tab is None:
            self.status.configure(
                text=f"Han 폴더: {self.workspace}"
            )
            return

        line, column = tab.text.index("insert").split(".")
        name = str(tab.path) if tab.path else "저장되지 않은 파일"
        state = "수정됨" if tab.dirty else "저장됨"

        self.status.configure(
            text=(
                f"{name}    {state}    "
                f"{line}행 {int(column) + 1}열    "
                f"UTF-8    Han: {self.workspace}"
            )
        )

    def refresh_tab_title(self, tab: EditorTab) -> None:
        try:
            index = self.notebook.index(tab)
        except tk.TclError:
            return
        self.notebook.tab(index, text=tab.title)
        self.update_status()

    def tabs(self) -> list[EditorTab]:
        return [self.notebook.nametowidget(tab_id) for tab_id in self.notebook.tabs()]

    def current_tab(self) -> EditorTab | None:
        selected = self.notebook.select()
        return self.notebook.nametowidget(selected) if selected else None

    def _notebook_right_click(self, event) -> None:
        try:
            # 현재 마우스 위치에 탭이 있는지 확인
            element = self.notebook.identify(event.x, event.y)

            if element not in ("tab", "label"):
                return

            # 마우스 위치에 해당하는 탭의 index
            index = self.notebook.index(f"@{event.x},{event.y}")

            tabs = self.notebook.tabs()

            if index < 0 or index >= len(tabs):
                return

            # 우클릭한 탭을 선택
            tab_id = tabs[index]
            self.notebook.select(tab_id)

            # 우클릭 메뉴
            menu = tk.Menu(
                self.root,
                tearoff=False
            )

            menu.add_command(
                label="닫기",
                command=lambda tab_id=tab_id: self.close_tab_by_id(tab_id)
            )

            menu.tk_popup(
                event.x_root,
                event.y_root
         )

        except tk.TclError:
            return

    def close_tab_by_id(self, tab_id: str) -> None:
        try:
            tab = self.notebook.nametowidget(tab_id)
        except tk.TclError:
            return

        if tab.dirty:
            self.notebook.select(tab)

            answer = messagebox.askyesnocancel(
                "저장 확인",
                f"{tab.title} 파일에 저장되지 않은 변경사항이 있습니다.\n\n"
                "저장하시겠습니까?"
            )

            if answer is None:
                return

            if answer:
                if not self.save_current():
                    return

        self.notebook.forget(tab_id)
        tab.destroy()

        if self.notebook.tabs():
            self.notebook.select(self.notebook.tabs()[0])

        self.update_status()

    def close_tab(self, tab_index: int) -> None:
        try:
            tab_id = self.notebook.tabs()[tab_index]
            tab = self.notebook.nametowidget(tab_id)
        except (IndexError, tk.TclError):
            return

        if tab.dirty:
            self.notebook.select(tab)

            answer = messagebox.askyesnocancel(
                "저장 확인",
                f"{tab.title} 파일에 저장되지 않은 변경사항이 있습니다.\n\n"
                "저장하시겠습니까?"
            )

            # 취소
            if answer is None:
                return

            if answer:
                if not self.save_current():
                    return

        self.notebook.forget(tab_id)
        tab.destroy()

        # 남은 탭이 있다면 첫 번째 탭 선택
        if self.notebook.tabs():
            self.notebook.select(self.notebook.tabs()[0])

        self.update_status()

    def on_close(self) -> None:
        for tab in self.tabs():
            if not tab.dirty:
                continue
            self.notebook.select(tab)
            answer = messagebox.askyesnocancel("저장 확인", f"{tab.title} 파일을 저장할까요?")
            if answer is None:
                return
            if answer and not self.save_current():
                return

        self.settings.save()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

    def show_welcome_message(self) -> None:
        messagebox.showinfo(
            "Han IDE 0.1 Beta",
            (
                "Han IDE에 오신 것을 환영합니다!\n\n"
                "현재 Han IDE는 0.1 Beta 버전입니다.\n"
                "아직 개발 중인 버전이므로 오류가 발생하거나 "
                "문법 및 기능이 변경될 수 있습니다.\n\n"
                "사용하면서 발견한 오류나 개선 의견이 있다면 "
                "보기 메뉴에서 보고를 클릭하여 폼을 작성해 주세요.\n"
                "폼을 작성해 주시면 Han의 발전에 큰 도움이 됩니다.\n\n"
                "Han Programming Language"
            )
        )

    def open_report(self) -> None:
        webbrowser.open("https://naver.me/IgMmQYQa")

    def show_about(self) -> None:
        messagebox.showinfo(
            "Han IDE 정보",
            (
                "Han IDE 0.1 Beta\n\n"
                "한국어 기반 프로그래밍 언어 Han의 개발 환경입니다.\n\n"
                "Han Programming Language\n"
                "Copyright (c) 2026 Han Project"
            )
        )

    def _console_key(self, event):
        if self.process is None:
            return

        try:
            current = self.console.index("insert")
            start = self.console_input_start

            # 프로그램 출력 영역으로 커서가 이동하는 것 방지
            if self.console.compare(current, "<", start):
                self.console.mark_set("insert", start)
                return "break"

            # Home → 입력 시작점
            if event.keysym == "Home":
                self.console.mark_set("insert", start)
                return "break"

            # Backspace로 출력 영역 삭제 방지
            if event.keysym == "BackSpace":
                if self.console.compare(current, "<=", start):
                    return "break"

                previous = self.console.index(f"{current}-1c")

                if self.console.compare(previous, "<", start):
                    return "break"

            # Delete로 출력 영역 삭제 방지
            if event.keysym == "Delete":
                if self.console.compare(current, "<", start):
                    self.console.mark_set("insert", start)
                    return "break"

                next_pos = self.console.index(f"{current}+1c")

                if self.console.compare(next_pos, "<", start):
                    return "break"

        except tk.TclError:
            return "break"

        return None


    def _console_backspace(self, event=None):
        if self.process is None:
            return "break"

        try:
            current = self.console.index("insert")

            if self.console.compare(
                current,
                "<=",
                self.console_input_start
            ):
                return "break"

        except tk.TclError:
            return "break"

        return None

    def _console_enter(self, event=None):
        if self.process is None:
            return "break"

        try:
            user_input = self.console.get(
                self.console_input_start,
                "end-1c"
            )

            # 사용자가 입력한 내용을 확정
            self.console.insert("end", "\n")

            if self.process.stdin is not None:
                self.process.stdin.write(user_input + "\n")
                self.process.stdin.flush()

            self.console_input_start = self.console.index("end-1c")

            self.console.mark_set("insert", self.console_input_start)
            self.console.see("end")

        except (
            BrokenPipeError,
            OSError,
            ValueError
        ):
            pass

        return "break"
                
            
    def _read_process_output(
            self,
            stream,
            stream_type: str
        ) -> None:

        if stream is None:
            return

        try:
            while True:
                char = stream.read(1)

                if char == "":
                    break

                self.output_queue.put(
                    (stream_type, char)
                )

        except (ValueError, OSError):
            pass

        finally:
            try:
                stream.close()
            except Exception:
                pass

    def _process_output_loop(self) -> None:
        try:
            while True:
                stream_type, text = self.output_queue.get_nowait()

                if stream_type == "stderr":
                   self.write_console(text, "error")

                elif stream_type == "stdout":
                    self.write_console(text, "ok")

                    # 프로그램이 출력한 내용은 수정할 수 없도록 하고,
                    # 출력이 끝난 위치부터 사용자가 입력할 수 있게 한다.
                    if self.process is not None:
                        self.console_input_start = self.console.index("end-1c")
                        self.console.mark_set("insert", self.console_input_start)

                elif stream_type == "process":
                    self.write_console(text, "muted")

        except queue.Empty:
            pass

        if self.process is not None or not self.output_queue.empty():
            self.root.after(30, self._process_output_loop)

    def _wait_process(
            self,
            process: subprocess.Popen
    ) -> None:

        returncode = process.wait()

        self.output_queue.put(
            (
                "process",
                f"\n종료 코드: {returncode}\n"
            )
        )

        self.root.after(
            0,
            self._process_finished,
            process
        )

    def _process_finished(
            self,
            process: subprocess.Popen
        ) -> None:

        if self.process is not process:
            return

        returncode = process.returncode

        self.process = None

        self.console.configure(state="disabled")
        self.console_input_start = self.console.index("end-1c")

    def stop_process(self) -> None:
        process = self.process

        if process is None:
            self.write_console(
                "실행 중인 프로그램이 없습니다.\n",
                "muted"
            )
            return

        self.process = None

        try:
            if process.stdin is not None:
                process.stdin.close()
        except OSError:
            pass

        try:
            process.terminate()
        except OSError:
            pass

        self.console.configure(state="disabled")
        self.console_input_start = self.console.index("end-1c")

        self.write_console(
            "\n프로그램을 중지했습니다.\n",
            "error"
        )

    
if __name__ == "__main__":
    HanIDE().run()