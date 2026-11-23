"""옮겨 받기 — 메일함 스캔이 보고를 들던 판의 파일(시각표 · 띄운 기록 · 그 출력 · 보내는 중 표지 · 옛 지금 모습 안의 그날 장부)을 이 스킬의
새 이름으로 옮겨 받는 한 자리. `clock.py adopt` 와 시계의 판이 이 하나를 부른다.

    moved = take_over(folder)       # 옮겨 받은 새 파일 이름들 — 옮길 것이 없으면 빈 것

시계가 한 판이라도 돈 사용자 폴더(그날 장부가 섰다)에서는 아무것도 안 옮긴다 — 옮긴 뒤 사람이 내린 시각표 · 판이 맺어 걷은 표지를 옛 것이
다시 세우지 않게. 그 전에는 새 파일이 없고 옛 파일이 있을 때만 읽어 새 이름으로 바꿔 끼워 쓴다.
옛 파일은 지우지 않는다 — 옮겨 받는 손이 도중에 죽어도 다음 판이 다시 읽는다. 꼴은 바꾸지 않고 옮긴다(옛 꼴을 읽는 법이 함께 왔다).
"""

from __future__ import annotations

import pathlib

import store as S
import unattended_const as C
import unattended_store as st


def take_over(folder: pathlib.Path) -> list[str]:
    """옛 파일 짝(`LEGACY_FILES`)과 옛 그날 장부를 옮겨 받는다 — 옮긴 새 이름들. 옛 것을 그 순간 못 읽으면 그것만 이번에 건너뛴다(다음
    판이 다시 본다). 시계가 이미 돈 폴더면 빈 것. 못 쓰면 OSError."""
    if (folder / C.DAY_FILE).exists():
        return []
    moved = [new for old, new in C.LEGACY_FILES if copied(folder / pathlib.Path(*old), folder / new)]
    return moved + ([C.DAY_FILE] if day_taken(folder) else [])


def copied(old: pathlib.Path, new: pathlib.Path) -> bool:
    """새 파일이 없고 옛 파일이 있으면 그 바이트를 새 이름으로 바꿔 끼워 쓴다 — 옮겼으면 True."""
    if new.exists():
        return False
    try:
        raw = S.read_bytes(old)
    except S.Unreadable:
        return False
    if raw is None:
        return False
    S.replace(new, raw)
    return True


def day_taken(folder: pathlib.Path) -> bool:
    """새 그날 장부가 없고 옛 지금 모습에 그날 장부 칸이 있으면 그 칸을 그대로 새 파일로 쓴다 — 옮겼으면 True. 날이 바뀐 장부여도 옮긴다(지난날
    건너뛴 시각의 한 줄은 새 장부를 열 때 선다)."""
    new = folder / C.DAY_FILE
    if new.exists():
        return False
    try:
        old = st.read_json(folder / pathlib.Path(*C.LEGACY_STATE)) or {}
    except st.Unreadable:
        return False
    day = old.get(C.LEGACY_DAY_KEY)
    if not isinstance(day, dict):
        return False
    st.write_json(new, day)
    return True
