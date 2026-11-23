"""두 지금 모습을 견주어 바뀜을 짓고, 그 바뀜을 누가 했나(사람 · 비서 · 모름)를 정리 스킬의 기록에 대어 가른다.

부르는 꼴::

    journal = Journal.load(scan_store.home())          # 정리 스킬의 기록 · 잡아 둔 바꿈
    mails, events = compare(prev_mails, prev_started, seen, read_at, paged, at, last_look, gone, journal)

견주는 법과 「누가」를 가르는 자는 `references/DESIGN.md` 「바뀜을 견주는 법」이 든다.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import scan_store as st
import scan_time as tm
from scan_const import TIDY_HELD_FILE, TIDY_LOG_FILE

USER, SECRETARY, UNKNOWN = "user", "secretary", "unknown"
INBOX, SENT, FOLDER = "inbox", "sent", "folder"
# 정리 스킬 기록의 종류 · 결과(그 스킬 journal_const.py 의 KINDS · DONE · UNKNOWN)
MOVE, TRASH, RESTORE = "move", "trash", "restore"
FOLDER_CREATE, FOLDER_DELETE = "folder-create", "folder-delete"
RULE_ADD, RULE_EDIT, RULE_DELETE = "rule-add", "rule-edit", "rule-delete"
DONE = "done"

# 바뀜의 종류 — 읽는 명령이 사람 말로 옮긴다
NEW, OPENED, READ, UNREAD, MOVED, GONE, BACK = "new", "opened", "read", "unread", "moved", "gone", "back"
FOLDER_ADDED, FOLDER_REMOVED = "folder-added", "folder-removed"
RULE_ADDED, RULE_REMOVED, RULE_CHANGED = "rule-added", "rule-removed", "rule-changed"


def box_key(box: str, folder: str = "") -> str:
    """상자의 열쇠 — 폴더면 「folder:<경로>」, 아니면 상자 이름."""
    return f"{FOLDER}:{folder}" if box == FOLDER else box


def place(mail: dict[str, Any]) -> tuple[str, str]:
    """메일 한 통의 자리 — (상자, 폴더 경로)."""
    return mail.get("box") or INBOX, mail.get("folder") or ""


def head(mail: dict[str, Any]) -> dict[str, Any]:
    """바뀜에 실어 두는 메일 머리 — 사라진 뒤에도 읽는 명령이 그 메일을 말할 수 있게."""
    keep = ("unid", "box", "folder", "date", "name", "addr", "to", "subject", "unread", "files")
    return {k: mail[k] for k in keep if k in mail}


# ── 정리 스킬의 기록 — 누가 바꿨나 ──────────────────────────────────────────────

@dataclass
class Journal:
    """정리 스킬의 기록(`rows` · 옛것부터)과 잡아 둔 채인 바꿈(`held`). 묻는 쪽이 그 바뀜이 일어났을 수 있는 때의 처음(`since`)을 준다 —
    그 뒤의 기록만 댄다."""
    rows: list[dict[str, Any]] = field(default_factory=list)
    held: dict[str, Any] | None = None

    @classmethod
    def load(cls, home: pathlib.Path) -> Journal:
        """정리 스킬의 기록을 읽는다 — 있는데 못 읽으면 `st.Unreadable` 이 그대로 나간다(판이 멈춘다): 잡아 둔 바꿈을 빈 것으로 읽으면 비서가
        하는 중인 옮김을 사람이 한 일로 바뀜 기록에 굳힌다. 글이 깨진 잡아 둔 바꿈은 없는 것으로 본다(기다려도 안 바뀐다)."""
        rows, _ = st.read_jsonl(home / TIDY_LOG_FILE)
        try:
            held = st.read_json(home / TIDY_HELD_FILE)
        except st.Unreadable as exc:
            if not exc.broken:
                raise
            held = None
        return cls(rows, held)

    def _within(self, since: datetime | None) -> list[dict[str, Any]]:
        """`since` 뒤의 기록 — 때를 못 읽은 기록은 남긴다(사람 탓으로 안 돌린다). `since` 가 없으면 다."""
        return [r for r in self.rows if since is None or (tm.parse(r.get("at")) or since) >= since]

    @staticmethod
    def _target(entry: dict[str, Any]) -> tuple[str, str] | None:
        """그 바꿈이 메일을 보낸 자리 — 옮기기는 받은편지함이나 그 폴더, 휴지통으로는 None(목록에서 사라진다)."""
        if entry.get("kind") == MOVE:
            to = entry.get("to") or ""
            return (FOLDER, to) if to else (INBOX, "")
        return None

    def _touches(self, entry: dict[str, Any], unid: str) -> bool:
        """정리 기록 한 줄이 그 메일에 닿았나."""
        return any((m or {}).get("unid", "").upper() == unid for m in entry.get("mails") or ())

    def mail_by(self, unid: str, kind: str, to: tuple[str, str] | None, since: datetime | None) -> str:
        """메일 한 통의 바뀜(옮겨짐 `to` · 사라짐 `to=None` · 다시 나타남)을 누가 했나."""
        if self.held and self._touches(self.held, unid):
            return UNKNOWN
        for entry in reversed(self._within(since)):
            if not self._touches(entry, unid):
                continue
            k = entry.get("kind")
            fits = ((kind == MOVED and k == MOVE and self._target(entry) == to) or (kind == GONE and k == TRASH)
                    or (kind in (BACK, MOVED) and k == RESTORE))
            if fits:
                return SECRETARY if entry.get("outcome") == DONE else UNKNOWN
            break
        return USER

    def folder_by(self, path: str, added: bool, since: datetime | None) -> str:
        """폴더 하나의 생김 · 없어짐을 누가 했나."""
        kind = FOLDER_CREATE if added else FOLDER_DELETE
        for entry in [*([self.held] if self.held else []), *reversed(self._within(since))]:
            if entry.get("kind") == kind and entry.get("path") == path:
                return SECRETARY if entry.get("outcome") == DONE else UNKNOWN
        return USER

    def rule_by(self, unid: str, before: str, after: str, since: datetime | None) -> str:
        """규칙 하나의 생김 · 바뀜 · 없어짐을 누가 했나."""
        for entry in [*([self.held] if self.held else []), *reversed(self._within(since))]:
            rule = entry.get("rule") or {}
            k = entry.get("kind")
            fits = ((k in (RULE_ADD, RULE_EDIT) and (rule.get("unid", "").upper() == unid or (after and rule.get("after") == after)))
                    or (k == RULE_DELETE and before and rule.get("before") == before))
            if fits:
                return SECRETARY if entry.get("outcome") == DONE else UNKNOWN
        return USER


# ── 견주기 ─────────────────────────────────────────────────────────────────────

def opened_before_seen(mail: dict[str, Any], last_look: datetime | None) -> bool:
    """처음 보는 받은 메일이 이미 읽음이고, 지난번 본 때 뒤에 온 메일인가 — 사람이 스캔보다 먼저 연 것이다."""
    if mail.get("box") == SENT or mail.get("unread") is not False or last_look is None:
        return False
    when = tm.mail_time(mail.get("date"))
    return when is not None and when >= last_look


def new_mail(mail: dict[str, Any], at: str, last_look: datetime | None, gone: dict[str, Any],
             journal: Journal | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """처음 보는 메일 하나 → (지금 모습에 넣을 줄, 바뀜). 사라졌다고 적은 메일이면 「다시 나타남」이다."""
    unid = mail["unid"]
    entry = {**mail, "first_seen": at}
    if unid in gone:
        was = gone.pop(unid)
        entry["first_seen"] = (was.get("mail") or {}).get("first_seen")
        by = journal.mail_by(unid, BACK, place(mail), tm.parse(was.get("at"))) if journal else USER
        return entry, [{"at": at, "kind": BACK, "unid": unid, "to": list(place(mail)), "by": by, "mail": head(mail)}]
    events = [{"at": at, "kind": NEW, "unid": unid, "mail": head(mail)}]
    if opened_before_seen(mail, last_look):
        events.append({"at": at, "kind": OPENED, "unid": unid, "by": USER, "mail": head(mail)})
    return entry, events


def compare(prev: dict[str, dict[str, Any]], prev_started: str, seen: dict[str, dict[str, Any]], read_at: dict[str, str],
            paged: set[str], at: str,
            last_look: datetime | None, gone: dict[str, Any], journal: Journal) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """앞 모습(`prev` · 그 판을 보기 시작한 때 `prev_started`)과 이번에 다 본 상자들(`seen` — 메일 번호 → 머리 · `read_at[상자 열쇠]`)을
    견준다. `paged` 는 한 번에 다 못 받은 상자의 열쇠다. 내는 것 — (새 지금 모습의 메일들, 바뀜). 부작용 — 사라진 메일의 기억 `gone` 을 고친다."""
    events: list[dict[str, Any]] = []
    out: dict[str, dict[str, Any]] = {}
    first_box = min(read_at, key=lambda k: read_at[k]) if read_at else ""
    for unid, mail in seen.items():
        old = prev.get(unid)
        if old is None:
            out[unid], made = new_mail(mail, at, last_look, gone, journal)
            events += made
            continue
        since = tm.parse(old.get("seen_until") or prev_started)
        out[unid] = {**mail, "first_seen": old.get("first_seen")}
        if place(old) != place(mail):
            events.append({"at": at, "kind": MOVED, "unid": unid, "from": list(place(old)), "to": list(place(mail)),
                           "by": journal.mail_by(unid, MOVED, place(mail), since), "mail": head(mail)})
        if mail.get("box") != SENT and old.get("box") != SENT and old.get("unread") is not None \
                and mail.get("unread") is not None and old["unread"] != mail["unread"]:
            events.append({"at": at, "kind": UNREAD if mail["unread"] else READ, "unid": unid, "by": USER, "mail": head(mail)})
    for unid, old in prev.items():
        if unid in seen:
            continue
        # 가장 먼저 읽은 상자라도 한 번에 다 못 받았으면 미룬다 — 쪽을 받는 사이 앞쪽 메일이 빠지면 뒤 쪽의 첫 줄이 당겨져 안 보인다
        settled = old.get("missing_since") or (box_key(*place(old)) == first_box and first_box not in paged)
        if not settled:
            out[unid] = {**old, "missing_since": at, "seen_until": prev_started}
            continue
        since = tm.parse(old.get("seen_until") or prev_started)
        last = {k: v for k, v in old.items() if k not in ("missing_since", "seen_until")}
        events.append({"at": at, "kind": GONE, "unid": unid, "from": list(place(old)), "by": journal.mail_by(unid, GONE, None, since),
                       "mail": head(last)})
        gone[unid] = {"at": at, "mail": last}
    return out, events


def compare_folders(prev: list[str], now: list[str], at: str, journal: Journal, since: datetime | None) -> list[dict[str, Any]]:
    """폴더 목록의 바뀜(생김 · 없어짐)과 바꾼 이를 낸다."""
    events = [{"at": at, "kind": FOLDER_ADDED, "path": p, "by": journal.folder_by(p, True, since)} for p in now if p not in prev]
    events += [{"at": at, "kind": FOLDER_REMOVED, "path": p, "by": journal.folder_by(p, False, since)} for p in prev if p not in now]
    return events


def compare_rules(prev: list[dict[str, str]], now: list[dict[str, str]], at: str, journal: Journal,
                  since: datetime | None) -> list[dict[str, Any]]:
    """메일 규칙의 바뀜(생김 · 바뀜 · 없어짐)과 바꾼 이를 낸다."""
    before = {r["unid"]: r["text"] for r in prev}
    after = {r["unid"]: r["text"] for r in now}
    events = []
    for unid, text in after.items():
        if unid not in before:
            events.append({"at": at, "kind": RULE_ADDED, "unid": unid, "text": text, "by": journal.rule_by(unid, "", text, since)})
        elif before[unid] != text:
            events.append({"at": at, "kind": RULE_CHANGED, "unid": unid, "text": text, "was": before[unid],
                           "by": journal.rule_by(unid, before[unid], text, since)})
    for unid, text in before.items():
        if unid not in after:
            events.append({"at": at, "kind": RULE_REMOVED, "unid": unid, "text": text, "by": journal.rule_by(unid, text, "", since)})
    return events
