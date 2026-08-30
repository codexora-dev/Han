from __future__ import annotations

import tkinter as tk
from tkinter import END, ttk


LESSONS = [
    {
        "title": "1. 시작하기", "path": "01_hello.han",
        "summary": "프로그램 구조와 출력 명령어를 익힙니다.",
        "goal": "Han 파일을 열고 F5로 첫 결과를 확인합니다.",
        "body": "Han 소스 파일의 확장자는 .han입니다. 프로그램은 위에서 아래 순서로 실행됩니다.\n\n출력 명령어는 뒤의 표현식 값을 터미널에 표시합니다. 문자열은 큰따옴표로 감쌉니다.",
        "syntax": "출력 값\n출력 \"문자열\"",
        "example": "출력 \"안녕하세요, Han!\"\n출력 \"한국어로 프로그램을 작성합니다.\"",
        "output": "안녕하세요, Han!\n한국어로 프로그램을 작성합니다.",
        "notes": "한 줄에 하나의 명령을 작성하면 읽기 쉽습니다.",
    },
    {
        "title": "2. 변수와 값", "path": "02_variables_and_math.han",
        "summary": "값에 이름을 붙이고 산술 표현식으로 계산합니다.",
        "goal": "변수 선언과 +, -, *, /, % 연산을 익힙니다.",
        "body": "변수는 값을 기억해 두는 이름입니다. 변수 이름 = 값으로 선언하고 초기화합니다.\n\n곱셈·나눗셈·나머지가 덧셈·뺄셈보다 먼저 계산됩니다.",
        "syntax": "변수 이름 = 값\n변수 결과 = 왼쪽 * 오른쪽\n이름 = 새 값",
        "example": "변수 가로 = 8\n변수 세로 = 5\n변수 넓이 = 가로 * 세로\n출력 \"넓이: \" + 넓이\n\n변수 나머지 = 17 % 3\n출력 \"나머지: \" + 나머지",
        "output": "넓이: 40\n나머지: 2",
        "notes": "변수를 사용하기 전에 먼저 값을 대입해야 합니다.",
    },
    {
        "title": "3. 입력 받기", "path": "03_input_greeting.han",
        "summary": "터미널 입력을 받고 문자열을 조합합니다.",
        "goal": "입력 프롬프트에 값을 넣고 결과가 바뀌는 것을 확인합니다.",
        "body": "입력 명령어는 사용자가 입력한 한 줄을 변수에 저장합니다. 프롬프트는 선택 사항입니다.\n\n입력값은 문자열로 취급하므로 문자열과 +로 연결할 수 있습니다.",
        "syntax": "입력 이름\n입력 이름 \"질문: \"",
        "example": "입력 이름 \"이름을 입력하세요: \"\n출력 \"반갑습니다, \" + 이름",
        "output": "이름을 입력하세요: 민수\n반갑습니다, 민수",
        "notes": "입력 예제는 실행 후 터미널 창에서 값을 입력합니다.",
    },
    {
        "title": "4. 조건문", "path": "04_condition.han",
        "summary": "비교 결과에 따라 실행 경로를 나눕니다.",
        "goal": "만약·아니면 블록과 비교 연산자를 익힙니다.",
        "body": "만약의 조건이 참이면 첫 블록을 실행하고, 아니면 조건이 거짓일 때의 블록을 실행합니다.\n\n==, !=, <, <=, >, >=로 값을 비교합니다. 블록은 끝으로 닫습니다.",
        "syntax": "만약 조건\n    명령\n아니면\n    명령\n끝",
        "example": "변수 점수 = 80\n만약 점수 >= 60\n    출력 \"합격\"\n아니면\n    출력 \"불합격\"\n끝",
        "output": "합격",
        "notes": "만약과 아니면의 내용은 들여쓰기하고 반드시 끝으로 닫습니다.",
    },
    {
        "title": "5. 반복하기", "path": "05_repeat.han",
        "summary": "같은 블록을 지정한 횟수만큼 실행합니다.",
        "goal": "반복 횟수와 반복 블록의 범위를 이해합니다.",
        "body": "반복 뒤의 숫자나 변수 표현식만큼 블록을 실행합니다. 반복 블록은 끝으로 닫히며, 안에 조건문을 넣을 수 있습니다.",
        "syntax": "반복 횟수\n    명령\n끝",
        "example": "변수 횟수 = 3\n반복 횟수\n    출력 \"Han을 연습합니다.\"\n끝",
        "output": "Han을 연습합니다.\nHan을 연습합니다.\nHan을 연습합니다.",
        "notes": "반복 횟수가 0이면 블록은 실행되지 않습니다.",
    },
    {
        "title": "6. 함수 만들기", "path": "06_function.han",
        "summary": "재사용할 코드를 함수와 매개변수로 구성합니다.",
        "goal": "함수 정의와 호출, 매개변수 전달을 익힙니다.",
        "body": "함수 정의는 함수 이름(매개변수)로 시작하고 끝으로 닫습니다. 정의만으로는 실행되지 않으며 이름과 괄호로 호출해야 합니다.",
        "syntax": "함수 이름(매개변수)\n    명령\n끝\n\n이름(인자)",
        "example": "함수 인사(이름)\n    출력 \"안녕하세요, \" + 이름\n끝\n\n인사(\"Han 개발자\")\n인사(\"학습자\")",
        "output": "안녕하세요, Han 개발자\n안녕하세요, 학습자",
        "notes": "호출 인자 개수는 정의한 매개변수 개수와 맞아야 합니다.",
    },
    {
        "title": "7. 비교와 논리", "path": "07_logic_and_comparison.han",
        "summary": "여러 조건을 그리고·또는·아니다로 조합합니다.",
        "goal": "참·거짓 값과 논리 연산으로 조건을 정교하게 작성합니다.",
        "body": "그리고는 양쪽 조건이 모두 참이어야 참이고, 또는은 하나라도 참이면 참입니다. 아니다는 논리값을 반대로 바꿉니다.",
        "syntax": "조건 그리고 조건\n조건 또는 조건\n아니다 조건",
        "example": "변수 나이 = 20\n변수 학생 = 참\n\n만약 나이 >= 19 그리고 학생\n    출력 \"학생 할인 대상입니다.\"\n아니면\n    출력 \"일반 요금입니다.\"\n끝",
        "output": "학생 할인 대상입니다.",
        "notes": "논리 연산은 만약의 조건이나 비교식과 함께 사용합니다.",
    },
    {
        "title": "8. 작은 프로그램 구성", "path": "08_menu_program.han",
        "summary": "여러 문법을 하나의 실행 흐름으로 조합합니다.",
        "goal": "변수·조건·반복을 함께 설계하고 실행합니다.",
        "body": "실제 프로그램은 하나의 문법만 사용하지 않습니다. 데이터를 변수로 나누고, 흐름을 조건과 반복으로 표현한 뒤 작은 단위로 확인합니다.",
        "syntax": "변수 값 = ...\n반복 횟수\n    만약 조건\n        명령\n    끝\n끝",
        "example": "변수 메뉴 = 2\n\n반복 3\n    만약 메뉴 == 1\n        출력 \"새 게임\"\n    아니면\n        출력 \"설정 메뉴\"\n    끝\n끝",
        "output": "설정 메뉴\n설정 메뉴\n설정 메뉴",
        "notes": "중첩 블록은 들여쓰기를 맞추고 각각 끝으로 닫습니다.",
    },
]


class LearningWindow(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.lesson_index = 0
        self.title("Han 배우기")
        self.geometry("980x700")
        self.minsize(780, 540)
        self.transient(parent)
        self._build_layout()
        self._show_lesson(0)

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        sidebar = ttk.Frame(self, padding=12)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.rowconfigure(1, weight=1)
        ttk.Label(sidebar, text="Han 개발자 문서", font=("맑은 고딕", 16, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 12))
        self.lesson_list = tk.Listbox(sidebar, width=25, activestyle="none", exportselection=False)
        self.lesson_list.grid(row=1, column=0, sticky="nsew")
        self.lesson_list.bind("<<ListboxSelect>>", self._lesson_selected)
        for lesson in LESSONS:
            self.lesson_list.insert(END, lesson["title"])

        content = ttk.Frame(self, padding=(8, 16, 18, 12))
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)
        self.title_label = ttk.Label(content, text="", font=("맑은 고딕", 20, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w")
        self.summary_label = ttk.Label(content, text="", wraplength=700)
        self.summary_label.grid(row=1, column=0, sticky="w", pady=(6, 14))
        main = ttk.Frame(content)
        main.grid(row=2, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)
        self.body = self._text(main, 0, 9, True)
        ttk.Label(main, text="문법", font=("맑은 고딕", 11, "bold")).grid(row=1, column=0, sticky="w", pady=(12, 4))
        self.syntax = self._text(main, 2, 4, False)
        ttk.Label(main, text="실습 예제", font=("맑은 고딕", 11, "bold")).grid(row=3, column=0, sticky="w", pady=(12, 4))
        self.example = self._text(main, 4, 9, False)
        buttons = ttk.Frame(content)
        buttons.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        buttons.columnconfigure(1, weight=1)
        self.previous_button = ttk.Button(buttons, text="이전", command=self._previous)
        self.previous_button.grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="예제를 편집기로 열기", command=self._open_example).grid(row=0, column=1)
        self.next_button = ttk.Button(buttons, text="다음", command=self._next)
        self.next_button.grid(row=0, column=2, sticky="e")

    def _text(self, parent, row, height, expands):
        widget = tk.Text(parent, height=height, wrap="word" if expands else "none", state="disabled", borderwidth=0)
        widget.grid(row=row, column=0, sticky="nsew" if expands else "ew")
        return widget

    def _set_text(self, widget, value):
        widget.configure(state="normal")
        widget.delete("1.0", END)
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _show_lesson(self, index):
        self.lesson_index = index
        lesson = LESSONS[index]
        self.title_label.configure(text=lesson["title"])
        self.summary_label.configure(text=lesson["summary"])
        self._set_text(self.body, f"학습 목표\n{lesson['goal']}\n\n설명\n{lesson['body']}\n\n실행 결과\n{lesson['output']}\n\n주의사항\n{lesson['notes']}")
        self._set_text(self.syntax, lesson["syntax"])
        self._set_text(self.example, lesson["example"])
        self.lesson_list.selection_clear(0, END)
        self.lesson_list.selection_set(index)
        self.lesson_list.see(index)
        self.previous_button.configure(state="normal" if index else "disabled")
        self.next_button.configure(state="normal" if index < len(LESSONS) - 1 else "disabled")

    def _lesson_selected(self, _event=None):
        selected = self.lesson_list.curselection()
        if selected:
            self._show_lesson(selected[0])

    def _previous(self):
        if self.lesson_index:
            self._show_lesson(self.lesson_index - 1)

    def _next(self):
        if self.lesson_index < len(LESSONS) - 1:
            self._show_lesson(self.lesson_index + 1)

    def _open_example(self):
        path = self.app.workspace / "examples" / LESSONS[self.lesson_index]["path"]
        if path.exists():
            self.app.open_file(path)
        self.app.root.lift()
        self.app.root.focus_force()


def open_learning_window(app):
    return LearningWindow(app.root, app)
