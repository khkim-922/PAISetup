"""기록 손의 셈 — 읽어 온 기록 · 안 · 잡아 둔 바꿈에서 명령마다 가를 상태를 낸다. 파일 · 표준 입출력에는 닿지 않는다.

사람에게 할 글은 짓지 않는다 — 상태의 이름(`journal_const.py`)과 값을 내고, 글은 `journal_words.py` 가 짓는다. 값에 드는 다음 걸음의
명령 줄은 `hand_line.py` 로 짓는다. 조각 차례를 어긴 것은 `hand_text.py` 의 꼴 판정처럼 까닭의 이름과 값을 든 `Refused` 로 올린다.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import journal_const as c
from hand_line import hand_args, held_args, preview_command, undo_line
from journal_const import (DONE, DRAFTS, FIRST_PIECE, FOLDER, FOLDER_CREATE, FOLDER_DELETE, FOLDER_KINDS, HELD_KEY, MAIL_KINDS, MOVE, RESTORE,
                           RULE_ADD, RULE_DELETE, RULE_EDIT, SENT, TRASH, Refused)
from journal_words import when_word


# ── 안 적기 ──────────────────────────────────────────────────────────────────

def piece_key(n: int) -> str:
    """보인 안 파일에서 조각 번호의 열쇠 — 글자다(JSON 객체의 열쇠)."""
    return str(n)


def key_number(key: str) -> int:
    """보인 안 파일의 조각 열쇠 → 번호. 숫자가 아닌 열쇠는 0."""
    return int(key) if key.isdigit() else 0


def shown_piece(pieces: dict[str, dict[str, Any]], n: int) -> dict[str, Any] | None:
    """보인 안에서 조각 n — 없으면 None."""
    return pieces.get(piece_key(n))


def is_first_piece(piece: int) -> bool:
    """이 조각이 새 안을 여는 1번인가."""
    return piece == FIRST_PIECE


def next_piece(pieces: dict[str, Any], plan: Any) -> int:
    """지금 안의 다음 조각 번호 — 안이 없으면 1."""
    return max((key_number(k) for k in pieces), default=0) + 1 if isinstance(plan, int) else FIRST_PIECE


def check_piece_order(piece: int, first: bool, pieces: dict[str, Any], plan: Any) -> None:
    """1번(`first`)이 아닌 조각 번호는 지금 안의 다음 차례만 받는다 — 아니면 `Refused`. 다른 안의 옛 번호를 그대로 주면 지금 안에 섞이고 그
    자리의 조각이 plans 에서 덮인다."""
    nxt = next_piece(pieces, plan)
    if not first and piece != nxt:
        raise Refused(c.WHY_IS_PIECE_NEXT, next=nxt)


def opens_plan(first: bool, plan: Any) -> bool:
    """이 조각이 새 안을 여나 — 1번 조각이거나 지금 안이 없다."""
    return first or not isinstance(plan, int)


def new_plan_number(rows: Sequence[dict[str, Any]]) -> int:
    """새 안의 번호 — 적어 둔 안들의 가장 큰 번호 다음."""
    return max((r["plan"] for r in rows), default=0) + 1


def kept_pieces(first: bool, pieces: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], int]:
    """이 조각을 적기 전에 남길 보인 조각과 걷은 수 — 1번 조각(`first`)이면 앞 안을 다 걷는다."""
    if first:
        return {}, len(pieces)
    return pieces, 0


def plan_row(plan: int, n: int, piece: dict[str, Any], at: str, log_from: int, why: str | None) -> dict[str, Any]:
    """안들에 덧붙일 조각 한 줄 — 메일 줄(제목 · 보낸 분)은 안 싣는다. log_from 은 이 조각을 보인 뒤에 붙는 첫 기록 번호(그 뒤 바꾼 것을
    가르는 금)다."""
    row = {"plan": plan, "piece": n, **piece, "at": at, "log_from": log_from}
    if why:
        row["why"] = why.strip()
    return row


def with_piece(pieces: dict[str, dict[str, Any]], n: int, piece: dict[str, Any], body: list[str], at: str) -> dict[str, dict[str, Any]]:
    """보인 안에 조각 n 을 몸(보일 메일 줄)과 적은 때째 더한 것."""
    return {**pieces, piece_key(n): {**piece, "body": body, "at": at}}


def shown_rows(pieces: dict[str, dict[str, Any]]) -> list[tuple[str, dict[str, Any], list[tuple[tuple[str, str] | None, int]], list[str], bool]]:
    """보인 안을 조각 차례로 — (번호, 조각, 원래 자리마다의 수, 보인 메일 줄, 메일 줄이 빠진 메일 조각인가). 메일 줄이 원래 없는 조각(폴더 ·
    규칙)은 머리 줄이 전부다."""
    order = sorted(pieces, key=key_number)
    out = []
    for n in order:
        p = pieces[n]
        body = p.get("body")
        out.append((n, p, counted(p), body if isinstance(body, list) and body else [], p.get("kind") in MAIL_KINDS))
    return out


def at_span(ats: Sequence[Any]) -> tuple[Any, Any]:
    """적은 때들 가운데 처음과 마지막 — 사람에게 보일 때 낱말(`when_word` — 분까지, 없으면 「때 모름」)의 차례로 고른다. 보이는 두 낱말이
    보이는 차례의 처음과 끝이게."""
    return min(ats, key=when_word), max(ats, key=when_word)


def shown_span(pieces: dict[str, dict[str, Any]]) -> tuple[Any, Any]:
    """보인 안의 조각을 처음과 마지막으로 적은 때."""
    return at_span([p.get("at") for p in pieces.values()])


# ── 잡기 · 맺기 ───────────────────────────────────────────────────────────────

def differences(shown: dict[str, Any], fresh: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    """보여 드린 조각과 다시 받은 미리 보기가 다른 점 — (다른 점의 이름, 보인 것, 지금). 손의 확인 열쇠가 대는 것만 견주고 읽음은 안 댄다.
    같으면 빈 목록."""
    kind = fresh["kind"]
    if shown.get("kind") != kind:
        return [(c.DIFF_IS_KIND, shown.get("kind"), kind)]
    out: list[tuple[str, Any, Any]] = []
    if kind == MOVE and (shown.get("to") or "") != (fresh.get("to") or ""):
        out.append((c.DIFF_IS_TARGET, shown.get("to"), fresh.get("to")))
    if kind in MAIL_KINDS:
        def places(e: dict[str, Any]) -> dict[str, tuple[str, str]]:
            return {m["unid"]: (m.get("place", ""), m.get("folder", "")) for m in e.get("mails") or []}
        was, now = places(shown), places(fresh)
        added = [u for u in now if u not in was]
        gone = [u for u in was if u not in now]
        moved = [u for u in now if u in was and now[u] != was[u]]
        if added:
            out.append((c.DIFF_IS_ADDED, None, added))
        if gone:
            out.append((c.DIFF_IS_GONE, None, gone))
        if moved:
            out.append((c.DIFF_IS_MOVED, None, [(u, was[u], now[u]) for u in moved]))
    elif kind in FOLDER_KINDS:
        if shown.get("path") != fresh.get("path"):
            out.append((c.DIFF_IS_PATH, shown.get("path"), fresh.get("path")))
    elif (shown.get("rule") or {}) != (fresh.get("rule") or {}):
        out.append((c.DIFF_IS_RULE, shown.get("rule"), fresh.get("rule")))
    return out


def prior_hold(old: dict[str, Any] | None, new: dict[str, Any]) -> str:
    """잡아 둔 바꿈이 새 미리 보기 앞에 선 꼴 — 없다 · 실행 안 된 같은 미리 보기 · 실행했는지 모른다.
    같은 종류 · 같은 확인 열쇠면 실행되지 않은 것이다 — 열쇠는 그 미리 보기가 본 자리의 지문이라, 실행됐으면 자리가 바뀌어 열쇠가
    달라지거나(옮기기 · 폴더 만들기 · 규칙 고치기) 미리 보기가 안 선다(휴지통 · 되살리기 · 폴더 · 규칙 지우기). 규칙 넣기만 실행 뒤에도
    같은 열쇠가 나와 뺀다 — 그것은 「결과 모름」이다."""
    if old is None:
        return c.PRIOR_NONE
    if old.get("key") and old.get("key") == new.get("key") and old.get("kind") == new["kind"] != RULE_ADD:
        return c.PRIOR_TWIN
    return c.PRIOR_UNKNOWN


def stamped(hold: dict[str, Any], undoes: int | None, at: str) -> dict[str, Any]:
    """잡아 둘 바꿈에 되돌리는 기록 번호와 잡은 때를 붙인 것."""
    return {**hold, "undoes": undoes, "at": at}


def mail_count(hold: dict[str, Any]) -> int | None:
    """잡은 바꿈이 건드리는 메일 수 — 메일을 안 건드리는 바꿈이면 None."""
    return len(hold["mails"]) if "mails" in hold else None


def undone_rule_unid(undone: dict[str, Any]) -> str:
    """되돌리는 기록(`undone` — 없으면 빈 것)이 넣은 규칙이면 그 규칙 열쇠 — 규칙 지우기의 미리 보기에는 열쇠가 없어 기록에서 댄다. 아니면 빈 것."""
    return (undone.get("rule") or {}).get("unid") or "" if undone.get("kind") == RULE_ADD else ""


def closed_entry(hold: dict[str, Any], outcome: str, more: dict[str, Any], at: str) -> dict[str, Any]:
    """잡아 둔 바꿈을 맺을 기록 한 줄 — 결과 · 때, 넣거나 고친 규칙의 열쇠, 받은편지함에 안 돌아온 수."""
    entry = {**hold, "outcome": outcome, "at": at}
    if more.get("rule_unid"):
        entry["rule"] = {**(entry.get("rule") or {}), "unid": more["rule_unid"]}
    if "elsewhere" in more:
        entry["elsewhere"] = more["elsewhere"]
    return entry


# ── 남은 안 ──────────────────────────────────────────────────────────────────

def left_of(row: dict[str, Any], rows: Sequence[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[int, int]]:
    """적어 둔 조각에서 아직 안 바꾼 몫 → (남은 조각 · 다 바꿨으면 None, 그 뒤 메일을 바꾼 기록 번호 → 뺀 통 수).
    조각을 보인 뒤(`log_from` 부터) 「됐다」로 맺은 기록만 바꾼 것으로 센다 — 결과 모름은 남긴다(다시 받는 미리 보기가 지금 자리를 보인다).
    메일 바꿈은 어느 안 · 어느 조각에서 왔든 그 메일 번호를 바꾼 기록이면 뺀다 — 조각 밖에서 따로 잡은 바꿈도 메일함을 바꿨다."""
    later = [r for r in rows if r["id"] >= int(row.get("log_from") or 0) and ending(r) == c.ENDED_DONE]
    kind = row.get("kind")
    if kind in MAIL_KINDS:
        by: dict[str, int] = {}
        for r in later:
            for m in r.get("mails") or []:
                by.setdefault(m.get("unid", ""), r["id"])
        keep = [m for m in row.get("mails") or [] if m.get("unid") not in by]
        cut: dict[int, int] = {}
        for m in row.get("mails") or []:
            if m.get("unid") in by:
                cut[by[m["unid"]]] = cut.get(by[m["unid"]], 0) + 1
        return ({**row, "mails": keep} if keep else None), cut
    if kind in FOLDER_KINDS:
        same = any(r.get("kind") == kind and r.get("path") == row.get("path") for r in later)
    else:
        def plain(rule: Any) -> dict[str, Any]:
            return {k: v for k, v in (rule or {}).items() if k != "unid"}   # 넣은 규칙의 열쇠는 맺을 때 붙는다
        same = any(r.get("kind") == kind and plain(r.get("rule")) == plain(row.get("rule")) for r in later)
    return (None if same else row), {}


def latest_rows(prows: Sequence[dict[str, Any]]) -> dict[int, dict[int, dict[str, Any]]]:
    """적어 둔 안들의 줄 → 안마다 조각마다의 줄 — 같은 안의 같은 조각을 다시 적었으면 나중 줄이 선다."""
    last: dict[int, dict[int, dict[str, Any]]] = {}
    for r in prows:
        last.setdefault(r["plan"], {})[int(r.get("piece") or FIRST_PIECE)] = r
    return last


def plans_left(prows: Sequence[dict[str, Any]], rows: Sequence[dict[str, Any]], most: int) -> list[dict[str, Any]]:
    """안 바꾼 조각이 남은 안들(새것부터 · `most` 개까지 — 0 이면 다) — 안마다 {plan, first(처음 적은 때), total, pieces[(번호, 남은 조각, 뺀 통 수, 미리 보기
    명령 · 규칙 조각은 None)]}. 뺀 통 수는 (그 뒤 바꾼 기록 번호 차례대로, 모두 몇 통). 남은 조각에는 원래 자리마다의 수도 붙는다."""
    last = latest_rows(prows)
    blocks: list[dict[str, Any]] = []
    for plan in sorted(last, reverse=True):
        if most and len(blocks) >= most:
            break
        pieces = last[plan]
        left = []
        for n in sorted(pieces):
            rest, cut = left_of(pieces[n], rows)
            if rest is None:
                continue
            hand = held_args(rest)
            left.append((n, rest, counted(rest), (sorted(cut), sum(cut.values())), preview_command(rest["kind"], hand) if hand is not None
                         else None))
        if left:
            blocks.append({"plan": plan, "first": at_span([p.get("at") for p in pieces.values()])[0], "total": len(pieces), "pieces": left})
    return blocks


# ── 기록 · 바꾼 메일 · 되돌리기 ─────────────────────────────────────────────────

def log_slice(rows: Sequence[dict[str, Any]], most: int) -> list[dict[str, Any]]:
    """보일 기록 — 새것부터 `most` 개(0 이면 다)."""
    return list(reversed(rows[-most:] if most else rows))


def pick_entries(rows: Sequence[dict[str, Any]], ids: Sequence[int]) -> tuple[list[dict[str, Any]], list[int]]:
    """고른 기록 번호의 기록(옛것부터 · 겹친 번호는 한 번)과 없는 번호 — 고른 것이 없으면 다."""
    by_id = {r["id"]: r for r in rows}
    missing = [i for i in ids if i not in by_id]
    return ([by_id[i] for i in sorted(set(ids)) if i in by_id] if ids else list(rows)), missing


def find_entry(rows: Sequence[dict[str, Any]], entry_id: int) -> dict[str, Any] | None:
    """그 번호의 기록 — 없으면 None."""
    return next((r for r in rows if r["id"] == entry_id), None)


def links(rows: Sequence[dict[str, Any]], entry_id: int) -> list[dict[str, Any]]:
    """그 기록을 되돌리려 한 기록들 — 되돌림 하나가 바꿈 여럿일 수 있다. 됐다고 맺은 것만 「되돌렸다」로 센다(부르는 쪽이 결과로 가른다)."""
    return [r for r in rows if r.get("undoes") == entry_id]


def chain_of(rows: Sequence[dict[str, Any]], entry_id: int) -> tuple[int, list[list[tuple[int, str, str]]]]:
    """그 기록이 든 되돌림의 사슬 — (처음 바꿈, 단마다 [(기록 번호, 되돌림 · 다시 함, 맺은 꼴)]). 같은 단의 여럿은 한 단에 선다."""
    by_id = {r["id"]: r for r in rows}
    root, seen = entry_id, {entry_id}
    while (up := by_id.get(root, {}).get("undoes")) in by_id and up not in seen:
        root = up
        seen.add(up)
    tiers, frontier, seen = [], [root], {root}
    while nxt := [r["id"] for r in rows if r.get("undoes") in frontier and r["id"] not in seen]:
        seen.update(nxt)
        tiers.append(nxt)
        frontier = nxt
    return root, [[(i, c.LINK_IS_UNDO if depth % 2 else c.LINK_IS_REDO, ending(by_id[i])) for i in ids] for depth, ids in enumerate(tiers, 1)]


def ending(r: dict[str, Any]) -> str:
    """기록 한 줄이 맺은 꼴 — 잡아 둔 채 · 됐다 · 결과 모름(「됐다」가 아닌 결과는 다 결과 모름이다)."""
    if r.get(HELD_KEY):
        return c.ENDED_HELD
    return c.ENDED_DONE if r.get("outcome") == DONE else c.ENDED_UNKNOWN


def mail_view(rows: Sequence[dict[str, Any]], e: dict[str, Any]) -> tuple[list[tuple[tuple[str, str] | None, list[str]]],
                                                                          list[tuple[dict[str, Any], list[str], str]]]:
    """기록 하나가 바꾼 메일 — (원래 자리마다의 메일 번호 · 되살리기는 자리 None, 뒤의 기록마다 (그 기록, 다시 바꾼 메일 번호, 맺은 꼴)). 폴더 · 규칙
    바꿈이나 메일이 없으면 둘 다 빈 목록."""
    groups = [(key, [m["unid"] for m in mails]) for key, mails in origins(e)]
    if not groups:
        return [], []
    mine = {u for _, unids in groups for u in unids}
    later = []
    for r in rows:
        if r["id"] <= e["id"]:
            continue
        touched = [m["unid"] for m in r.get("mails") or [] if m.get("unid") in mine]
        if touched:
            later.append((r, touched, ending(r)))
    return groups, later


def place_key(m: dict[str, Any]) -> tuple[str, str]:
    """메일 한 통의 원래 자리를 묶는 열쇠 — (자리, 폴더 경로). 폴더가 아닌 자리는 경로를 안 본다 — 사람 말이 같은 자리가 한 묶음이다."""
    place = m.get("place", "")
    return place, m.get("folder", "") if place == FOLDER else ""


def origins(e: dict[str, Any]) -> list[tuple[tuple[str, str] | None, list[dict[str, Any]]]]:
    """기록 하나가 건드린 메일을 원래 자리마다 — (자리 열쇠 · 되살리기는 휴지통이라 None, 그 자리의 메일들) 처음 본 차례. 메일 바꿈이
    아니면 빈 목록."""
    kind = e.get("kind")
    if kind not in MAIL_KINDS:
        return []
    groups: dict[tuple[str, str] | None, list[dict[str, Any]]] = {}
    for m in e.get("mails") or []:
        groups.setdefault(None if kind == RESTORE else place_key(m), []).append(m)
    return list(groups.items())


def counted(e: dict[str, Any]) -> list[tuple[tuple[str, str] | None, int]]:
    """기록 하나가 원래 자리마다 건드린 메일 수 — (자리 열쇠, 수) 처음 본 차례."""
    return [(key, len(mails)) for key, mails in origins(e)]


def undo_tries(rows: Sequence[dict[str, Any]], e: dict[str, Any]) -> tuple[list[int], list[int], list[int]]:
    """그 기록을 되돌리려 한 기록 번호 — (됐다고 맺은 것, 결과를 모르는 것, 잡아 둔 채인 것)."""
    tried = links(rows, e["id"])
    done = [r["id"] for r in tried if ending(r) == c.ENDED_DONE]
    maybe = [r["id"] for r in tried if ending(r) == c.ENDED_UNKNOWN]
    pending = [r["id"] for r in tried if ending(r) == c.ENDED_HELD]
    return done, maybe, pending


def undo_plan(e: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """기록 하나를 되돌리는 차례 — 걸음마다 (걸음의 이름, 값). 값에 칠 명령 줄(손의 미리 보기 → `journal.py hold … --undoes`)을 든다. 값을
    다 모르는 걸음(규칙의 칸)은 잡을 `journal.py` 명령을 지을 종류와 기록 번호만 든다."""
    kind = e.get("kind")
    mails = e.get("mails") or []
    entry_id = str(e.get("id"))

    def line(step_kind: str, **values: Any) -> str:
        return undo_line(step_kind, hand_args(step_kind, **values) or [], entry_id)

    def groups(pick) -> list[tuple[str, str, list[str]]]:
        out: dict[tuple[str, str], list[str]] = {}
        for m in mails:
            if pick(m):
                out.setdefault(place_key(m), []).append(m["unid"])
        return [(p, f, u) for (p, f), u in out.items()]

    def back(n: int, step: str, place: str, folder: str, unids: list[str]) -> tuple[str, dict[str, Any]]:
        return step, {"n": n, "place": place, "folder": folder, "unids": unids, "cmd": line(MOVE, to=folder if place == FOLDER else "", unids=unids)}

    every = [m["unid"] for m in mails]
    steps: list[tuple[str, dict[str, Any]]] = []
    if kind == MOVE:
        n = 0
        for place, folder, unids in groups(lambda m: True):
            n += 1
            steps.append(back(n, c.STEP_IS_NO_HAND if place in (SENT, DRAFTS) else c.STEP_IS_MOVE_BACK, place, folder, unids))
    elif kind == TRASH:
        steps.append((c.STEP_IS_RESTORE, {"n": 1, "unids": every, "cmd": line(RESTORE, unids=every)}))
        n = 1
        for place, folder, unids in groups(lambda m: m.get("place") == FOLDER):
            n += 1
            steps.append(back(n, c.STEP_IS_AFTER_RESTORE, place, folder, unids))
        for place, folder, unids in groups(lambda m: m.get("place") == SENT):
            steps.append((c.STEP_IS_RESTORE_UNKNOWN, {"place": place, "folder": folder, "unids": unids}))
    elif kind == RESTORE:
        steps.append((c.STEP_IS_RETRASH, {"n": 1, "unids": every, "cmd": line(TRASH, unids=every)}))
    elif kind in FOLDER_KINDS:
        path = e.get("path", "")
        if kind == FOLDER_CREATE:
            steps.append((c.STEP_IS_FOLDER_DROP, {"path": path, "cmd": line(FOLDER_DELETE, path=path)}))
        else:
            steps.append((c.STEP_IS_FOLDER_MAKE, {"path": path, "cmd": line(FOLDER_CREATE, path=path)}))
    else:
        rule = e.get("rule") or {}
        key = rule.get("unid") or ""
        if kind == RULE_ADD:
            steps.append((c.STEP_IS_RULE_DROP, {"unid": key, "rule": rule.get("after", ""), "cmd": line(RULE_DELETE, rule_unid=key)}) if key
                         else (c.STEP_IS_RULE_DROP_NOKEY, {"rule": rule.get("after", ""), "hold_kind": RULE_DELETE, "entry_id": entry_id}))
        elif kind == RULE_EDIT:
            steps.append((c.STEP_IS_RULE_BACK if key else c.STEP_IS_RULE_BACK_NOKEY,
                          {"unid": key, "before": rule.get("before", ""), "after": rule.get("after", ""), "hold_kind": RULE_EDIT, "entry_id": entry_id}))
        else:
            steps.append((c.STEP_IS_RULE_READD, {"before": rule.get("before", ""), "hold_kind": RULE_ADD, "entry_id": entry_id}))
    return steps
