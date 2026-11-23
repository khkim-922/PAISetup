"""보고 창의 고름 걸기 — 보고 창에서 고르신 보고 시각을, 창이 보이던 시각에서 더하고 빼신 것만 걸린 시각표 위에 얹는다. 시계 판과 창 곁의
손(`clock.py window-times`)이 함께 쓰는 한 자리.

    said, refused = take_window_times(folder, setting, picked, seen, at_text)   # 그 창에 적을 말 · 걸지 않은 것이 있나
"""

from __future__ import annotations

import pathlib
from typing import Any

import unattended_store as st
import clock as tm
from brief_schedule import load, put, save
from brief_slots import squeezed, times_given
from brief_kinds import AGAIN, APPLY, BAD, STALE, UNREAD
from brief_words import in_force, window_refusal, window_reply


def window_verdict(setting: dict[str, Any], picked: list[str], seen: list[str], at_text: str) -> tuple[Any, ...]:
    """보고 창의 고름을 어떻게 받나 — (AGAIN, 그때의 말, 안 걸었나) 같은 고름을 이미 받았다 · (STALE,) 고른 뒤에 대화에서 시각을 걸었다
    (나중의 말씀이 이긴다) · (BAD, 까닭) 시각의 꼴이 아니다 · (APPLY, 더하신 것, 빼신 것) 창이 보이던 시각(`seen` · 비면 지금 걸린 것)에서
    더하고 빼신 것."""
    before = setting.get("picked")
    if isinstance(before, dict) and before.get("at") == at_text:
        return AGAIN, str(before.get("said") or in_force(setting)), bool(before.get("refused"))
    chosen_at, set_at = tm.parse_chosen(at_text), tm.parse(setting.get("set"))
    times, bad = times_given(picked)
    base, _ = times_given(seen) if seen else (setting["times"], "")
    if chosen_at is None or (set_at is not None and chosen_at <= set_at):
        return (STALE,)
    if bad:
        return BAD, bad
    return APPLY, sorted(set(times) - set(base)), sorted(set(base) - set(times))


def take_window_times(folder: pathlib.Path, setting: dict[str, Any], picked: list[str], seen: list[str], at_text: str) -> tuple[str, bool]:
    """보고 창에서 고르신 보고 시각을 받는다 — 어떻게 받나를 가르고(`window_verdict`), 얹을 것이면 걸고(`apply_window`), 받은 고름의 표지를
    남긴다(두 길이 같은 고름을 함께 받으면 둘째는 첫 끝을 다시 낸다). 내는 것 — (그 창에 적을 말, 걸지 않은 것이 있나)."""
    verdict = window_verdict(setting, picked, seen, at_text)
    if verdict[0] == AGAIN:
        return verdict[1], verdict[2]
    if verdict[0] == STALE:
        said, refused = window_refusal(STALE, setting), True
    elif verdict[0] == BAD:
        said, refused = window_refusal(BAD, setting, verdict[1]), True
    else:
        try:
            said, refused = apply_window(folder, setting, verdict[1], verdict[2])
        except st.Unreadable as exc:
            return window_refusal(UNREAD, setting, str(exc)), True
        try:          # 받은 고름의 표지 — 못 읽은 파일 위에는 안 쓴다. 시각표는 위에서 이미 걸렸다 — 표지가 빠지면 같은 고름을 함께 받은
                      # 다른 길이 「대화에서 바꾸셨다」로 거절할 수 있지만, 빈 것 위에 표지를 써 시각표를 지우는 것보다 낫다
            put(folder, "picked", {"at": at_text, "said": said, "refused": refused})
        except st.Unreadable:
            pass
    return said, refused


def fit_window(old: list[str], added: list[str], removed: list[str]) -> tuple[list[str], list[tuple[str, str | None, int]]]:
    """창에서 더하고 빼신 것을 얹은 시각표 — 창이 보여 드리지 않은 시각은 안 뺀다. 틈을 모자라게 하는 더하신 시각은 하나씩 빼 보고(붙은
    둘이 다 새것이면 늦은 쪽), 더하신 것 말고 다른 데가 모자라면 걸린 것 그대로 둔다. 내는 것 — (걸 시각표, [(뺀 시각, 붙은 다른 시각 ·
    그날 끝이면 None, 틈 분)])."""
    new = sorted((set(old) - set(removed)) | set(added))
    fresh, dropped = set(added) - set(old), []
    while True:
        tight = squeezed(new)
        if not tight:
            break
        t, near, room = tight[0]
        cut = (near if near in fresh else t if t in fresh else None) if near else (t if t in fresh else None)
        if cut is None:                      # 더하신 것 말고 다른 데가 틈이 모자라다 — 그대로 둔다
            new = old
            break
        dropped.append((cut, (t if cut == near else near) if near else None, room))
        new = [x for x in new if x != cut]
        fresh.discard(cut)
    return new, dropped


def apply_window(folder: pathlib.Path, setting: dict[str, Any], added: list[str], removed: list[str]) -> tuple[str, bool]:
    """창에서 더하고 빼신 것을 지금 걸린 시각표 위에 건다 — 맞춘 시각표(`fit_window`)가 다르면 걸고, 건 뒤 다시 읽어 말한다. 내는 것 —
    (창에 적을 말, 걸지 않은 것이 있나)."""
    old = setting["times"]
    new, dropped = fit_window(old, added, removed)
    if new != old:
        save(folder, new, pathlib.Path(setting["claude"]))
    now, _ = load(folder)
    times = (now or {}).get("times", [])
    taken, gone = [t for t in added if t in times], [t for t in removed if t not in times]
    return window_reply(taken, gone, dropped, new == old and bool(added or removed), now), bool(dropped)
