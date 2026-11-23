"""보고 창(.html) · 보고 글(.md)의 이름을 읽는다 — 지은 때(`made_of`) · 보고 창의 이름인가(`is_window`) · 폴더에 남은 보고 글을 그
차례로(`kept_briefs`). 보고 창 · 글 이름의 꼴을 아는 자리는 이 파일이다 — 이름의 원본은 `brief_const.FILE_NAME` 이다.
파일을 읽지 않는다(이름만 본다).
"""

from __future__ import annotations

import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_const.py — `-I` 로 돌아도 싣는다
from brief_const import FILE_NAME  # noqa: E402

WINDOW_SUFFIX = pathlib.PurePath(FILE_NAME).suffix   # 보고 창 — 「.html」
TEXT_SUFFIX = ".md"                                  # 창 곁에 같은 이름으로 남는 보고 글
BRIEF_PREFIX = FILE_NAME.partition("{")[0]           # 「brief-」 — 폴더에서 보고 글을 고를 때 먼저 거른다


def made_of(name: str) -> dt.datetime | None:
    """보고 창(.html) · 보고 글(.md)의 이름에서 지은 때 — 이 PC 의 시각(`FILE_NAME` 이 그렇게 짓는다). 꼴이 아니면 None."""
    shape = FILE_NAME.replace("{:", "").replace("}", "").removesuffix(WINDOW_SUFFIX)
    for suffix in (WINDOW_SUFFIX, TEXT_SUFFIX):
        try:
            return dt.datetime.strptime(name, shape + suffix)
        except ValueError:
            continue
    return None


def is_window(name: str) -> bool:
    """파일 이름이 보고 창의 이름(`FILE_NAME` 꼴 · .html)인가 — 누른 창 · 열린 탭 · 창의 보고 글을 찾는 자리가 이 한 자로 가른다."""
    return name.endswith(WINDOW_SUFFIX) and made_of(name) is not None


def kept_briefs(folder: pathlib.Path) -> list[pathlib.Path]:
    """폴더에 남은 보고 글 — 이름이 `FILE_NAME` 꼴(.md)인 것만, 이름 차례(곧 지은 때의 차례)로. 거르는 꼴은 이 PC 의 파일 이름 규칙을 따른다
    (Windows 는 큰 · 작은 글자를 안 가린다)."""
    return sorted((f for f in folder.glob(f"{BRIEF_PREFIX}*{TEXT_SUFFIX}") if made_of(f.name)), key=lambda f: f.name)
