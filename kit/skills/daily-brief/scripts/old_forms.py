"""옛 꼴의 말씀을 읽는 한 자리 — 맞춤 파일에 「걸지 않기로 하신 것」 절을 두기 전의 보고 글이 그 말씀을 「이 보고가 본 데」의 한 줄로 들던 꼴.
맞춤 파일을 읽는 손(`prefs_file.read`)이 그 절이 없는 파일일 때만 부르고, 창을 짓는 손의 마무리(`finish.keep_declined`)가 그렇게 읽어 들인
말씀을 맞춤 파일에 한 번 옮긴다. 사용자 폴더의 가장 늦은 보고 글을 읽기만 한다.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 store.py · 보고 글 읽기 — `-I` 로 돌아도 싣는다
import store  # noqa: E402
from brief_files import kept_briefs  # noqa: E402
from brief_sections import END_SECTIONS, starts_named  # noqa: E402

DECLINED_OLD = re.compile(r"걸지\s*않기로\s*하셨")


def declined_old(folder: pathlib.Path) -> bool:
    """가장 늦은 보고 글이 걸지 않기로 하신 말씀을 「이 보고가 본 데」의 줄로 들었나 — 맞춤 파일에 그 절을 두기 전의 꼴. 못 읽으면 False."""
    briefs = kept_briefs(folder) if folder.is_dir() else []
    try:
        raw = store.read_bytes(briefs[-1]) if briefs else None
    except store.Unreadable:
        return False
    rows, inside = [], False
    for row in (raw or b"").decode("utf-8", errors="replace").splitlines():
        if row.startswith("#"):
            inside = starts_named(row.lstrip("#"), END_SECTIONS[0])   # 옛 보고 글의 머리는 적힌 그대로 읽는다 — 굵게 쓴 머리는 그 절로 안 보고 # 층은 다 본다
            continue
        if inside:
            rows.append(row)
    return bool(DECLINED_OLD.search("\n".join(rows)))
