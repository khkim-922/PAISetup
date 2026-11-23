"""보고 창 손의 입구 명령(`window.py` · `ticks.py` · `prefs.py`)이 함께 쓰는 바탕 — 인자 규칙(사람 없는 실행이 연 명령의 꼴 `--dir "<사용자 폴더>"`을
지킨다) · `--help` 의 「프로그램이 부르는 문」 절 · 멈춘 까닭 · 사람에게 할 말 내기."""

from __future__ import annotations

import argparse

# `--help` 에서 모델의 길과 떼어 두는 절 — 이름 · 인자는 다른 프로그램이 굳혀 부르므로 바꾸지 않는다
DOORS_TITLE = "프로그램이 부르는 문"
DOORS_NOTE = "다른 프로그램(이 스킬의 시계 · 창 곁의 손 · 형제 스킬)이 부른다 — 모델이 부를 길이 아니다."


class Once(argparse.Action):
    """두 번째로 오면 인자 오류(종료 2)로 멈춘다 — 줄인 이름(`--di`)이나 `--dir=…` 꼴로 와도 같은 칸이라 함께 걸린다."""

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            parser.error(f"{option_string} 는 한 번만 준다")
        setattr(namespace, self.dest, values)


class Stop(Exception):
    """입구가 그 한 줄(`line`)을 사람에게 하고 그 종료 값(`code` — 기본 1)으로 멈춘다 — 손가락이 멈춘 까닭을 들고 올리고, 손은 한 자리에서 받는다."""

    def __init__(self, line: str, code: int = 1):
        super().__init__(line)
        self.line, self.code = line, code


def say(lines: list[str]) -> None:
    """사람에게 할 말을 줄마다 표준 출력에 낸다."""
    for line in lines:
        print(line)
