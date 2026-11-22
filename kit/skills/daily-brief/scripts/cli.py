"""보고 창 손의 입구 명령(`window.py` · `ticks.py`)이 함께 쓰는 인자 규칙 — 사람 없는 실행이 연 명령의 꼴(`--dir "<사용자 폴더>"`)을 지킨다."""

from __future__ import annotations

import argparse


class Once(argparse.Action):
    """두 번째로 오면 인자 오류(종료 2)로 멈춘다 — 줄인 이름(`--di`)이나 `--dir=…` 꼴로 와도 같은 칸이라 함께 걸린다."""

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            parser.error(f"{option_string} 는 한 번만 준다")
        setattr(namespace, self.dest, values)
