"""창을 여는 손(`window.py`)이 사람에게 하는 말 — 멈춘 까닭 · 경고 · 띄운 곳 · 끝 줄과 「다음:」. 받은 수와 이름만 말로 옮긴다 — 파일 ·
프로세스 · 망을 읽지 않는다.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_tasks.py · task_kinds.py — `-I` 로 돌아도 싣는다
from brief_tasks import TOP_MARK  # noqa: E402
from task_kinds import CAL, DO_FIELD, PUT_FIELD, TALK_FIELD  # noqa: E402

# ── 멈춘 까닭 ────────────────────────────────────────────────────────────
SHEET_NOT_BRIEF = "메일 한 장을 짓지 않았다 — 보고 글의 이름이 아니다: {name}"
SHEET_UNREAD = "메일 한 장을 짓지 않았다 — 보고 글을 못 읽었다({name}: {why})"
SHEET_NO_TITLE = "메일 한 장을 짓지 않았다 — 보고 글에 제목이 없다"
LATEST_NO_FOLDER = "보고 글을 못 찾았다 — 폴더가 없다: {folder}"
READ_FAIL = "보고 글을 못 읽었다({src}: {exc}). 다음: 보고 글 파일의 자리를 확인하고 다시 부른다"
NO_TITLE = "보고 창을 짓지 않았다 — 보고 글에 제목(맨 위 「# …」 한 줄)이 없다. 다음: 제목 줄을 더해 다시 부른다"
NO_FOLDER = "보고 창을 짓지 않았다 — 폴더가 없다: {folder}. 다음: 업무 파일(work.md)이 있는 사용자 폴더를 --dir 로 준다"
PREV_UNREAD = ("보고 창을 짓지 않았다 — 지난 보고 글을 못 읽었다({exc}). 그 글의 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」을 잇지 못한 새 글이 그 "
               "자리를 덮으면 사용자가 정하신 것이 사라진다. 다음: 그 파일을 확인하고 다시 부른다")
PAGE_FAIL = "보고 창을 못 썼다({out}: {exc}). 다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다"
KEPT_FAIL = ("보고 창은 지었지만 보고 글을 못 남겼다({kept}: {exc}) — 다음 보고는 이 보고를 모른 채 그 앞 보고에서 잇는다. "
             "다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다")

# ── 띄운 곳 ─────────────────────────────────────────────────────────────
NOT_OPENED = "띄우지 않았다(--no-open)"
IN_EDGE = "띄웠다(로그인된 Edge 의 새 탭)"
IN_EDGE_WITH = "띄웠다(로그인된 Edge 의 새 탭 · {said})"
HAND_SAID = {True: "곁에 누름을 바로 거두는 손을 띄웠다", False: "누름을 바로 거두는 손이 이미 돈다",
             None: "누름을 바로 거두는 손을 못 띄웠다 — 누르신 것은 메일함 스캔이 받는다"}
IN_BROWSER = "띄웠다(기본 브라우저 — 메일 링크가 로그인을 물을 수 있다)"
NOWHERE = "못 띄웠다 — 이 파일을 사용자께 알려 드린다"


def edge_words(hand: bool | None, wanted: bool) -> str:
    """로그인 Edge 의 새 탭에 띄운 말 — 창 곁의 손을 띄울 창이면(`wanted`) 그 끝(`presses.start_hand` 의 답)도 단다."""
    return IN_EDGE_WITH.format(said=HAND_SAID[hand]) if wanted else IN_EDGE


# ── 경고 · 끝 줄 ─────────────────────────────────────────────────────────
def warn_lines(finished: list[str], extra_titles: int, sections: int, bad_refs: int, urls: int, ends: list[str], bad_puts: int,
               bad_tasks: list[str], tops: int, bad_people: list[str]) -> list[str]:
    """끝 줄 앞에 설 경고 · 알림 — 마무리가 낸 경고, 그리고 그린 글의 수마다 한 줄(0 이면 안 선다)."""
    out = list(finished)
    if extra_titles:
        out.append(f"경고: 제목(# …)이 {extra_titles + 1}개라 둘째부터는 절로 세웠다")
    if sections == 0:
        out.append("경고: 절(## …)이 하나도 없다 — 왼쪽 절 목록이 빈다")
    if bad_refs:
        out.append(f"경고: 메일 번호(32자리)가 아닌 mail: 링크 {bad_refs}개는 쓴 그대로 글자로 두었다")
    if urls:
        out.append(f"알림: 글에 쓴 주소 {urls}개는 링크로 짓지 않고 글자로 두었다 — 링크는 메일 번호에서만 선다")
    out += [f"경고: 끝에 「{end}」 절이 없다 — 다음 보고는 남은 이 글만 읽고 잇는다" for end in ends]
    if bad_puts:
        out.append(f"경고: 「{PUT_FIELD}」 칸 {bad_puts}곳의 꼴이 틀려 「일정에 넣기」를 안 달았다 — 「{DO_FIELD}: {CAL.name} | …」 줄에 일정 손 preview 답의 "
                   "start · end · title · (곳) · visibility 를 「 | 」로 그대로 잇는다 — 열쇠는 적지 않는다(lane.md 「보고 글의 꼴」)")
    if bad_tasks:
        out.append(f"경고: 맡길 일의 칸 {len(bad_tasks)}곳의 꼴이 틀려 단추를 안 달았다(lane.md 「보고 글의 꼴」) — " + " / ".join(bad_tasks))
    if tops > 1:
        out.append(f"경고: 「{TOP_MARK}」이 붙은 「{TALK_FIELD}」이 {tops}곳이라 창 머리의 칸에 아무것도 안 올렸다 — 보고 하나에 하나만 붙인다")
    if bad_people:
        out.append(f"경고: 사람을 댄 칸 {len(bad_people)}곳의 꼴이 틀려 사람별에 세우지 않았다 — 사람마다 「[이름 직함](person:<주소>)」 를 「 · 」로 "
                   "잇는다(lane.md 「보고 글의 꼴」): " + " / ".join(bad_people))
    return out


def end_lines(out: pathlib.Path, kept: pathlib.Path, sections: int, lines: int, links: int, tasks: int, shown: str, ends: list[str],
              unlinked: int, mailbox_given: bool) -> list[str]:
    """끝 줄과 그 뒤의 「다음:」 — 지은 두 파일 · 절 · 줄 · 메일 링크 · 맡길 일의 수 · 띄운 곳, 빠진 끝의 절, 링크 없이 세운 메일."""
    puts = f" · 맡길 일 {tasks}" if tasks else ""
    got = [f"보고 창을 지었다: {out} · 남긴 보고 글: {kept} — 절 {sections} · 줄 {lines} · 메일 링크 {links}{puts} · {shown}"]
    if ends:
        got.append(f"다음: 남긴 보고 글 끝에 {' · '.join(f'「## {e}」' for e in ends)} 절을 더한다(파일을 쓸 도구가 없는 실행이면 그 절을 넣은 글로 다시 부른다) — 다음 보고가 그 글에서 어디부터 읽을지와 "
                   "다시 올리지 않을 것을 찾는다")
    if unlinked:
        why = "메일함 주소가 없어" if not mailbox_given else "메일함 주소가 꼴(http(s)://<호스트>/…/<이름>.nsf)에 안 맞아"
        got.append(f"다음: {why} 메일 {unlinked}곳을 링크 없이 번호로 세웠다 — 회사 메일 스킬의 session 이 낸 메일함 주소를 --mailbox 로 주고 "
                   "다시 부른다")
    return got
