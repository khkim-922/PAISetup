"""전자결재 스킬의 쓰기 손 — preview · save · discard. 출발 하나(새 문서 · 지난 문서 다시 쓰기 · 임시저장)의 화면 씨앗을 읽고, 바꿀 것을
넣은 판을 지어 보이고(열쇠), 보인 판 그대로일 때만 임시저장한 뒤 임시저장 목록에서 다시 읽어 맺는다. 상신 · 승인 · 반려는 없다.

부르는 꼴 — 입구(approval.py)가 ``run(app, args, start)`` 하나를 부른다: app 은 세션을 쥔 ``iams.App``, args 는 입구의 argparse 값,
start 는 표에 대 본 출발(``STARTS`` 의 열쇠). 답은 dict(JSON 하나로 찍힌다). 멈출 때는 ``ep_command.Stop``.

짜임 — ``run`` 이 손이다: 출발 열기(``opened``) → 씨앗 읽기(``iams.doc_row``) → 칸 바꾸기(``changed`` — 사람 받기 ``people_rows`` · 결재선
짓기 ``built_line``) → 미리 보기와 열쇠(``plan``) → 임시저장(``saved``) → 맺기(``settled``) → 창 띄우기(``iams.launch``) · 지우기(``discarded``).
앱에 묻는 것은 다 ``iams`` 의 ``tx`` · ``page`` · ``save`` 이고, 앱 안의 주소 · 문서 열쇠의 꼴 · 창을 띄우는 길도 ``iams`` 가 든다. 위로는
표 ``approval_table``(``CHANGES`` · ``STARTS`` · ``GRADES``)만 읽는다 — 입구는 안 싣는다.

- 문서 열쇠 — 받는 것(--from · --draft · --link)도 내는 것(답의 ``id`` · ``next``)도 box 줄의 id 꼴(``APPR_DOC_ID.OVN.AVN.APVN``) 하나다
- 다단결재 여부(결재자 여럿을 받나)는 그 양식의 새 문서 창에서 읽는다 — 출발이 무엇이든 같은 자리라 미리 보기와 저장의 열쇠가 같다.
  지난 문서의 보기 창은 그 값을 안 든다

⚠ 지난 문서 다시 쓰기의 화면(``cpltReuse.ex`` · 취소 문서는 ``reuse.ex``)은 여는 순간 서버에 임시저장을 하나 세운다. 그래서 preview 는
그 화면을 안 열고 지난 문서를 읽어 판을 짓고, save 가 그 화면을 연 뒤 새 임시저장으로 판을 다시 지어 열쇠를 견준다. 그 창이 세운
임시저장은 열기 앞뒤의 임시저장 목록을 견줘 가린다. 그 뒤 무엇이 못 서면 그 임시저장을 지우고, 못 지웠거나 섰는지 모르면 답에 그 열쇠를 싣는다
— 말 없이 남기지 않는다.
"""

from __future__ import annotations

import hashlib
import re
import urllib.parse

import ep_command
import iams
from ep_command import EXIT_SESSION, EXIT_STALE, EXIT_TOOL, NEXT_EP_LOGIN, Stop

import approval_table as table   # 표(CHANGES · STARTS · GRADES) — 입구를 싣지 않는다

USER = "/iams/commonSearch/userDAO/selectUser.ex"                    # 결재선 지정 창의 사람 찾기 — 사번은 SEARCH_TYPE DOCUMENT
USER_DEPT = "A100_01"              # 결재선 지정 창의 검색 조건이 심는 DEPT_CODE 그대로 — 사람의 부서와 상관없이 이 값이다
DISCARD = "/iams/comx/documentService/disuse2.ex"                    # 임시저장함의 [삭제] — 문서 창의 폐기(disuse.ex)와 다르다
NO_REUSE_FORMS = ("IA025", "IA40", "IA024", "IA100")              # 화면이 [재사용]을 막는 보안 양식
TYPE_NAMES = {"REQUEST": "요청", "APPROVAL": "결재", "CONFIRM": "검토", "COOPERATION": "협조", "AGREEMENT": "합의", "REFERENCE": "참조"}
PLAIN_RSP = ("외주직", "PCP", "일반/파견운전직", "Senior PCP", "계약직", "Cheif PCP", "외주")   # 화면이 직책 「일반」 으로 읽는 직책
BODY_SHOWN = 300                   # 미리 보기에 싣는 본문 글자 수 — 열쇠는 본문 전체로 짓는다
TAG = re.compile(r"<[^>]+>")
UNMEASURED = "회사에서 안 쟀다"
STATE_WORDS = {
    "ready": "이 판으로 임시저장한다 — 사람에게 보이고 「네」 를 받은 뒤 save 에 같은 값과 --confirm <key> 로 부른다",
    "blocked": "이대로는 임시저장하지 않는다(앱의 화면도 막는다) — 답의 blocks 를 그대로 전하고 고칠 값을 받는다",
    "saved": "임시저장했습니다(임시저장 목록에서 다시 읽어 확인했습니다). 상신은 사람이 그 문서 창에서 누른다",
    "discarded": "임시저장을 지웠습니다(임시저장 목록에서 사라진 것을 확인했습니다)",
    "gone": "그 문서가 없습니다 — id 가 틀렸거나 이미 지워졌습니다. 다음: box drafts 로 임시저장 목록을 읽어 보인다",
    "moved": "보여 드린 뒤 그 사이에 바뀐 것이 있어 하지 않았습니다",
    "unsure": "됐는지 확인하지 못했습니다. 다음: 다시 부르지 말고 box drafts 로 읽어 보인다",
    "refused": "결재 앱이 임시저장을 받지 않았습니다(아무것도 안 섰다) — 답의 blocks 가 앱의 말이다. 고칠 값을 받아 preview 부터 다시 한다",
}


def opt(args, name: str):
    """부른 명령의 인자 하나 — 그 명령이 안 받는 인자(discard 는 바꿀 것을 안 받는다)는 None."""
    return getattr(args, name, None)


# ── 출발 열기 (A1.3.1) — 출발마다 화면 하나 ─────────────────────────────────────────────────────────
def draft_rows(app) -> list:
    """임시저장 목록의 줄들 — 앱의 답 그대로."""
    got = app.tx(iams.DRAFTS, iams.DRAFTS_QUERY)
    return next((v for v in got.values() if isinstance(v, list)), [])


def draft_row(app, key: str) -> dict | None:
    """임시저장 목록에서 그 열쇠(넷 다 같은)의 줄 — 없으면 None."""
    return next((r for r in draft_rows(app) if iams.key_of(r) == key), None)


def opened(app, args, start: str, *, making: bool) -> str | None:
    """출발의 화면 글자 — 새 문서는 양식의 새 창, 임시저장은 그 다시 열기 창, 지난 문서는 미리 보기면 그 문서의 보기 창 · 저장이면
    [재사용] 창(``making`` — 서버에 임시저장이 선다 · 연 뒤 ``made`` 가 가린다). 문서가 없으면 None."""
    if start == "new":
        return app.page(iams.NEW_DOC.format(form=urllib.parse.quote(opt(args, "form"), safe="")))
    if start == "draft":
        key = iams.doc_of(opt(args, "draft"), "--draft")
        return None if draft_row(app, iams.key_of(key)) is None else app.page(iams.at(iams.DRAFT_DOC, key))
    key = iams.doc_of(opt(args, "from"), "--from")
    view = app.page(iams.at(iams.VIEW, key))
    if not making:
        return view
    old = iams.doc_row(view)
    if old is None or reuse_blocks(old):
        return view if old is not None else None        # 막힌 문서는 [재사용] 창을 안 연다 — 판이 막는 까닭을 댄다
    return app.page(iams.at(iams.CANCELLED_REUSE_DOC if old.get("RESULT_STATUS") == "CANCELED" else iams.REUSE_DOC, key))


# ── 씨앗 읽기 (A1.3.2) — 화면의 문서 한 줄 + 문서 한 건의 거래 ───────────────────────────────────────
def live_dist(app, rows: list) -> tuple[list, list]:
    """지난 문서의 배포처 → (지금 있는 것 · 뺀 부서 이름). [재사용] 창은 결재 앱의 지금 부서 나무에 없는 부서를 배포처에서 뺀다(잰 것 —
    배포 부서 10 곳 가운데 나무에 없는 5 곳이 빠졌다) — 미리 보기가 같은 거르기를 해야 미리 보기와 저장의 열쇠가 같다."""
    live = iams.live_depts(app)
    keep = [r for r in rows if r.get("WDTB_TY") != "DEPARTMENT" or str(r.get("WDTB_TARGET")) in live]
    return keep, [str(r.get("DISP_NAME") or r.get("WDTB_TARGET")) for r in rows if r not in keep]


def cascade_for(app, seed: dict, start: str, page: str | None) -> bool:
    """그 업무가 다단결재를 받나 — 새 문서 · 임시저장은 연 창(request.ex)의 값, 다시 쓰기는 그 양식의 새 문서 창(열어도 안 남는다 ·
    WRITE-MAP 2 절)의 값. 미리 보기와 저장이 같은 자리에서 읽어 열쇠가 같다. 못 읽으면 받지 않는 쪽(결재자 한 명)으로 읽는다."""
    if start == "reuse":
        page = app.page(iams.NEW_DOC.format(form=urllib.parse.quote(str(seed.get("FORM_ID") or ""), safe="")))
    return bool(iams.cascade_of(page))


# ── 칸 바꾸기 (A1.3.3) — 사람 받기 ─────────────────────────────────────────────────────────────
# 결재선 줄이 드는 칸(문서 한 건의 거래가 내는 줄과 같은 이름) — 앱의 사람 찾기 줄에서 이것만 옮긴다
LINE_KEYS = ("DEPT_CODE", "DEPT_NAME_KR", "DEPT_NAME_EN", "APPR_LEVEL", "APPR_LEVEL_NM", "COST_CENTER", "JOB_POSITION_CODE",
             "JOB_POSITION_NM_KR", "JOB_CLASS_CODE", "JOB_CLASS_NM_KR", "JOB_RSP_CODE", "JOB_RSP_NM_KR", "JOB_RSP_NM_EN", "JOB_RSP_SORT_NUM")
NO_EMPNO = "사람 파일의 {who} 에 사번(empno)이 없어 결재 앱에서 찾지 못한다 — 주소록으로 그분을 다시 찾아 사번이 든 사람 파일을 준다"
NOT_IN_APP = "결재 앱의 사람 찾기에 사번 {empno}({who})이 없다 — 퇴직했거나 결재 앱에 없는 분이다. 주소록으로 다시 확인한다"
NAME_DIFFERS = "사번 {empno} 은 결재 앱에서 「{app}」 이다(사람 파일은 「{file}」) — 맞는 분인지 사람에게 확인한다"
RETIRED = "{who} 는 결재 앱에서 퇴직자다 — 결재선 · 참조에 둘 수 없다"


def app_person(app, empno: str, me: str) -> dict | None:
    """사번 하나 → 결재 앱의 사람 줄(결재선 지정 창의 사번 검색 그대로). 없으면 None."""
    got = app.tx(USER, {"paramMap": {"SEARCH_TYPE": "DOCUMENT", "SEARCH_TEXT": empno, "REQUEST_USER_ID": me, "SELF_APPROVAL": "",
                                     "DEPT_CODE": USER_DEPT}})
    return next((r for r in got.get("DS_RESULT") or [] if str(r.get("USER_ID")) == empno), None)


def people_rows(app, paths, me: str) -> tuple[list, list, list]:
    """사람 파일들 → (앱의 사람 줄들 · 막는 까닭 · 알릴 것). 한 사람은 한 번, 준 차례 그대로."""
    rows, blocks, notes = [], [], []
    for p in ep_command.distinct(ep_command.people_of(paths)):
        if not p.empno:
            blocks.append(NO_EMPNO.format(who=p.label()))
            continue
        row = app_person(app, p.empno, me)
        if row is None:
            blocks.append(NOT_IN_APP.format(empno=p.empno, who=p.label()))
            continue
        if row.get("RETIRE_DATE"):
            blocks.append(RETIRED.format(who=p.label()))
            continue
        if (row.get("USER_NAME_KR") or "").strip() != p.name:
            notes.append(NAME_DIFFERS.format(empno=p.empno, app=row.get("USER_NAME_KR"), file=p.name))
        rows.append(row)
    return rows, blocks, notes


def person_line(row: dict, kind: str) -> dict:
    """앱의 사람 줄 → 결재선 · 참조 줄 하나(결재형태는 결재선 짓기가 매긴다)."""
    out = {k: row.get(k) for k in LINE_KEYS}
    uid, name = str(row.get("USER_ID")), row.get("USER_NAME_KR")
    out.update({"APPR_USER_ID": uid, "APPR_USER_NAME": name, "USER_NAME_KR": name, "RETIRE_AT": "YES" if row.get("RETIRE_DATE") else "NO",
                "APPR_TYPE": kind, "APPR_TYPE_NAME": TYPE_NAMES[kind]})
    if kind == "REFERENCE":
        out = {**{k: v for k, v in out.items() if not k.startswith("APPR_USER")}, "REFRN_USER_ID": uid, "REFRN_USER_NAME": name}
    return out


# ── 칸 바꾸기 — 결재선 짓기 ──────────────────────────────────────────────────────────────────────
def built_line(requester: dict, approvers: list, agree: list) -> list:
    """요청자 줄 + 결재자들(차례대로) + 합의자들 → 결재선 지정 창이 돌려주는 꼴. 마지막은 결재, 그 사이는 요청자와 같은 부서면 검토 ·
    남의 부서면 협조(창의 getAction 은 요청자의 부서와 견준다). 합의는 마지막 결재 바로 앞에 한 차례(SEQ)로 모여
    선다(마지막이 결재가 아니면 창이 안 받는다). SEQ 는 0 부터, 합의는 같은 SEQ 에 ORDR 0, 1 …(창의 createReturnApprLine)."""
    middle = [dict(r) for r in approvers[:-1]]
    for r in middle:
        r["APPR_TYPE"] = "CONFIRM" if r.get("DEPT_CODE") == requester.get("DEPT_CODE") else "COOPERATION"
    last = [{**approvers[-1], "APPR_TYPE": "APPROVAL"}] if approvers else []
    rows = [dict(requester, APPR_TYPE="REQUEST")] + middle + [{**r, "APPR_TYPE": "AGREEMENT"} for r in agree] + last
    seq, ordr = 0, 0
    for r in rows:
        if r["APPR_TYPE"] == "AGREEMENT":
            r["APPR_LINE_SEQ"], r["APPR_LINE_ORDR"] = seq, ordr
            ordr += 1
        else:
            if ordr:
                seq, ordr = seq + 1, 0
            r["APPR_LINE_SEQ"], r["APPR_LINE_ORDR"] = seq, 0
            seq += 1
        r["APPR_TYPE_NAME"] = TYPE_NAMES[r["APPR_TYPE"]]
    return rows


def requester_line(line: list) -> dict:
    """결재선의 요청자 줄 — 화면이 이름을 「이름[사번]」 으로 바꿔 싣는 꼴(잰 저장이 그렇게 실었다)."""
    first = dict(line[0])
    name = str(first.get("APPR_USER_NAME") or "")
    tag = f"[{first.get('APPR_USER_ID')}]"
    first["APPR_USER_NAME"] = name if name.endswith(tag) else name + tag
    first.update({"ROW_TYPE": "4", "ROW_ID": 1})
    return first


def with_doc(rows: list, seed: dict) -> list:
    """새로 지은 줄에 문서 열쇠(APPR_DOC_ID · OVN · AVN · APVN)를 단다 — 창이 요청자 줄의 값을 그대로 단다."""
    keys = {k: seed.get(k) for k in iams.KEY_FIELDS}
    return [{**r, **keys} for r in rows]


# ── 칸 바꾸기 — 제목 · 본문 · 등급 · 참조 · 관련 문서 ───────────────────────────────────────────────────
def body_of(args, det: dict) -> str:
    """본문 HTML — --body-file 을 주면 그 글, 아니면 출발의 본문(새 양식이면 틀). 화면처럼 「&quot;」 를 「'」 로 바꿔 싣는다."""
    text = ep_command.text_file(opt(args, "body_file"), "--body-file 의 파일") if opt(args, "body_file") else (det.get("contents") or "")
    return text.replace("&quot;", "'")


def link_rows(app, ids, seed: dict) -> tuple[list, list]:
    """관련 문서로 줄 지난 문서들 → (연계문서 줄들 · 막는 까닭). 문서마다 그 보기 창의 씨앗에서 제목과 판을 읽는다."""
    rows, blocks = [], []
    for text in ids or ():
        key = iams.doc_of(text, "--link")
        old = iams.doc_row(app.page(iams.at(iams.VIEW, key)))
        if old is None:
            blocks.append(f"관련 문서 {text} 를 못 찾았다 — box 줄의 id 를 준다")
            continue
        rows.append({"SUBJECT": old.get("SUBJECT"), **{f"REF_{k}": key[k] for k in iams.KEY_FIELDS},
                     **{k: seed.get(k) for k in iams.KEY_FIELDS}})
    return rows, blocks


def joined(rows: list, key: str) -> str:
    """화면이 보이는 칸(배포처 · 연계문서)에 이어 적는 이름들 — 「, 」 로 잇는다."""
    return ", ".join(str(r.get(key) or "") for r in rows)


def new_line(app, args, line: list, me: str, *, fresh_requester: bool) -> tuple[list, list, list]:
    """결재선을 다시 짓는다 — (줄들 · 막는 까닭 · 알릴 것). --approvers 를 주면 결재자를 통째로 갈고, 안 주면 출발의 결재자들 그대로.
    --agree 를 주면 합의를 갈고, 안 주면 출발의 합의 그대로. ``fresh_requester`` 면 요청자 줄을 결재 앱의 지금 내 줄로 다시 받는다 — 지난
    문서의 결재선은 그때의 부서 · 직급을 든다. 못 받으면 출발의 줄을 두고 알린다."""
    approvers, blocks, notes = people_rows(app, opt(args, "approvers"), me) if opt(args, "approvers") else ([], [], [])
    agree, more_blocks, more_notes = people_rows(app, opt(args, "agree"), me) if opt(args, "agree") else ([], [], [])
    blocks, notes = blocks + more_blocks, notes + more_notes
    requester = dict(line[0])
    if fresh_requester:
        mine = app_person(app, me, me)
        if mine:
            requester = person_line(mine, "REQUEST")
        else:
            notes.append("결재 앱의 사람 찾기가 나를 안 냈다 — 요청자 줄은 지난 문서의 것(그때의 부서 · 직급)이다")
    kept = [dict(r) for r in line[1:]]
    approvers = [person_line(r, "APPROVAL") for r in approvers] if opt(args, "approvers") else [r for r in kept if r.get("APPR_TYPE") != "AGREEMENT"]
    agree = [person_line(r, "AGREEMENT") for r in agree] if opt(args, "agree") else [r for r in kept if r.get("APPR_TYPE") == "AGREEMENT"]
    return built_line(requester, approvers, agree), blocks, notes


# ── 미리 보기와 열쇠 (A1.3.4) — 화면이 [임시저장]도 막는 규칙 ─────────────────────────────────────────
SELF_APPROVAL = "자가결재다 — 요청자({who})가 결재선에 또 있다. 결재권자를 직책을 가진 상위 직급자로 지정한다"
POSITION = "결재선 변경이 필요하다 — {who}: 결재권자를 직책을 가진 상위 직급자로 지정한다(앱의 직급 · 직책 규칙)"
ONE_APPROVER = "이 업무({job})는 다단결재가 아니라 결재자를 한 명만 둔다(합의는 따로 더할 수 있다) — 결재자 여럿이면 --form IA037 일반품의서로 쓴다"
LEVEL_ORDER = "같은 부서에서 {before} 다음의 {after} 는 결재 단계(APPR_LEVEL)가 더 높을 수 없다 — 차례를 바꾼다"
LAST_APPROVAL = "결재선의 마지막은 결재여야 한다"
RETIRED_LINE = "결재선 · 참조에 퇴직자가 있다: {who} — --approvers · --refs 로 지금 사람을 준다"
NO_SUBJECT = "제목이 비었다 — --subject 로 준다"
ALONE = "결재자가 없다 — 이대로 임시저장은 되지만 상신하려면 문서 창에서 결재자를 더하거나 --approvers 로 준다"
REUSE_BLOCKED = "이 양식({form})은 앱이 [재사용]을 막는다(보안부서 검토 양식) — 정보보호업무플랫폼에서 새로 쓴다"
SAVE_UNMEASURED = "「{word}」의 임시저장은 " + UNMEASURED + " — 저장한 뒤 read 로 그대로 섰는지 본다"
SYSTEM_DOC = "시스템 연계문서는 재사용할 수 없다 — 그 업무 시스템에서 다시 올린다"


def grade_code(code) -> tuple[str, int] | None:
    """직급 코드(「P4」 · 「E7」 · 「P10」) → (직군 글자, 숫자). 비었거나 꼴이 아니면 None."""
    m = re.fullmatch(r"([A-Za-z])(\d+)", str(code or "").strip())
    return (m.group(1).upper(), int(m.group(2))) if m else None


def self_approval(line: list) -> list:
    """화면의 selfApproval — 요청자가 결재선 뒤에 또 서면 막는다. 요청자의 직급이 없거나 R3 · E8 이상이면 받는다."""
    me = grade_code(line[0].get("JOB_CLASS_NM_KR"))
    if me is None or (me[0] == "R" and me[1] >= 3) or (me[0] == "E" and me[1] >= 8):
        return []
    mine = line[0].get("APPR_USER_ID")
    return [SELF_APPROVAL.format(who=line[0].get("USER_NAME_KR") or mine)] if any(r.get("APPR_USER_ID") == mine for r in line[1:]) else []


def plain(rsp) -> bool:
    """화면이 직책 없음(「일반」)으로 읽는 직책인가."""
    rsp = str(rsp or "")
    return rsp == "일반" or rsp in PLAIN_RSP


def position_check(line: list) -> list:
    """화면의 positionCodeCheck — 결재(APPROVAL) 줄마다 요청자와 직군 · 직급 · 직책을 견준다. 요청자나 어느 줄의 직급이 비면 받는다
    (화면이 그렇다). R3 · E7 이상 요청자는 받는다."""
    me = grade_code(line[0].get("JOB_CLASS_NM_KR"))
    if me is None or (me[0] == "R" and me[1] >= 3) or (me[0] == "E" and me[1] >= 7):
        return []
    for r in line[1:]:
        them = grade_code(r.get("JOB_CLASS_NM_KR"))
        if them is None:
            return []
        if r.get("APPR_TYPE") != "APPROVAL":
            continue
        same = them[0] == me[0]
        if (same and (me[1] > them[1] or (plain(line[0].get("JOB_RSP_NM_KR")) and plain(r.get("JOB_RSP_NM_KR"))))
                or (not same and them[0] == "E")
                or (not same and plain(r.get("JOB_RSP_NM_KR")))):
            return [POSITION.format(who=f"{r.get('USER_NAME_KR') or r.get('APPR_USER_NAME')} {r.get('JOB_CLASS_NM_KR')} {r.get('JOB_RSP_NM_KR')}")]
    return []


def level_order(line: list) -> list:
    """결재선 지정 창의 checkApprovalLevel — 같은 부서의 앞줄보다 뒷줄의 결재 단계 숫자가 크면 막는다(단계가 빈 줄은 안 본다)."""
    for before, after in zip(line, line[1:]):
        a, b = before.get("APPR_LEVEL"), after.get("APPR_LEVEL")
        if before.get("DEPT_CODE") == after.get("DEPT_CODE") and level(a) is not None and level(b) is not None and level(a) < level(b):
            return [LEVEL_ORDER.format(before=before.get("USER_NAME_KR"), after=after.get("USER_NAME_KR"))]
    return []


def level(value) -> float | None:
    """결재 단계 — 숫자가 아니거나 비었으면 None(화면도 그 줄은 안 본다)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def line_blocks(line: list, refs: list, cascade: bool, job: str) -> tuple[list, list]:
    """결재선이 화면의 규칙에 걸리나 — (막는 까닭 · 알릴 것)."""
    blocks = self_approval(line) + position_check(line) + level_order(line)
    deciders = [r for r in line if r.get("APPR_TYPE") != "AGREEMENT"]
    if not cascade and len(deciders) > 2:
        blocks.append(ONE_APPROVER.format(job=job))
    if len(line) > 1 and line[-1].get("APPR_TYPE") != "APPROVAL":
        blocks.append(LAST_APPROVAL)
    gone = [r.get("USER_NAME_KR") or r.get("REFRN_USER_NAME") for r in line + refs if r.get("RETIRE_AT") == "YES" or r.get("RETIRE_DATE")]
    if gone:
        blocks.append(RETIRED_LINE.format(who=" · ".join(map(str, gone))))
    return blocks, ([ALONE] if len(line) < 2 else [])


def reuse_blocks(seed: dict) -> list:
    """지난 문서를 다시 쓸 수 있나 — 화면의 [재사용]이 막는 문서."""
    if seed.get("APPR_CLASS") == "SYSTEM":
        return [SYSTEM_DOC]
    return [REUSE_BLOCKED.format(form=seed.get("FORM_ID"))] if seed.get("FORM_ID") in NO_REUSE_FORMS else []


def unmeasured_notes(args, start: str) -> list:
    """받되 회사에서 안 잰 손가락을 받았으면 그렇다고 알린다 — 표(``approval_table.CHANGES``)의 △ 그대로."""
    return [f"「{c.name}」 바꾸기는 {UNMEASURED} — 임시저장한 뒤 read 로 그대로 섰는지 보고, 아니면 문서 창에서 사람이 고친다"
            for c in table.CHANGES.values() if start in c.unmeasured and ep_command.given(args, c)]


def body_text(html_text: str) -> str:
    """본문 HTML 의 앞 글자 — 사람에게 보일 만큼만, 태그를 걷고 빈칸을 접는다."""
    import html
    return " ".join(html.unescape(TAG.sub(" ", html_text)).split())[:BODY_SHOWN]


def who(r: dict) -> str:
    """결재선 · 참조 줄 하나의 사람 말 — 결재형태 · 이름 · 부서 · 직급 · 직책."""
    name = r.get("USER_NAME_KR") or r.get("REFRN_USER_NAME") or r.get("APPR_USER_NAME")
    rsp = r.get("JOB_RSP_NM_KR")
    return " · ".join(str(x) for x in (TYPE_NAMES.get(r.get("APPR_TYPE"), r.get("APPR_TYPE_NAME")), name, r.get("DEPT_NAME_KR"),
                                       r.get("JOB_POSITION_NM_KR"), None if plain(rsp) else rsp) if x)


def plan(app, args, start: str, page: str | None) -> dict:
    """출발의 화면(``opened`` 가 연 것)에 바꿀 것을 넣은 문서 한 건의 꼴 · 막는 까닭 · 알릴 것 · 열쇠, 그리고 앱에 보낼 짐(``payload``).
    바꾸지 않는다."""
    seed = iams.doc_row(page)
    if seed is None:
        return {"state": "gone"}
    det = iams.details(app, seed)
    me = str((seed.get("SESSION_USER") or {}).get("USER_ID") or seed.get("REQUEST_USER_ID") or "")   # 지난 문서는 남이 쓴 것일 수 있다
    blocks, notes = (reuse_blocks(seed) if start == "reuse" else []), unmeasured_notes(args, start)
    line = [dict(r) for r in det.get("apprLineList") or []]
    if line and (opt(args, "approvers") or opt(args, "agree") or start == "reuse"):
        line, more_blocks, more_notes = new_line(app, args, line, me, fresh_requester=start == "reuse")
        blocks, notes = blocks + more_blocks, notes + more_notes
    refs = [dict(r) for r in det.get("refrnList") or []]
    if opt(args, "refs"):
        got, more_blocks, more_notes = people_rows(app, opt(args, "refs"), me)
        refs, blocks, notes = [person_line(r, "REFERENCE") for r in got], blocks + more_blocks, notes + more_notes
    links = [dict(r) for r in det.get("refDocList") or []]
    if opt(args, "link"):
        links, more_blocks = link_rows(app, opt(args, "link"), seed)
        blocks += more_blocks
    wdtb, attach = det.get("wdtbList") or [], det.get("attachList") or []
    if start == "reuse" and any(r.get("WDTB_TY") == "DEPARTMENT" for r in wdtb):
        wdtb, gone_depts = live_dist(app, wdtb)
        if gone_depts:
            notes.append(f"배포처에서 지금 없는 부서 {len(gone_depts)} 곳은 뺀다(다시 쓰기 창이 빼는 그대로): " + " · ".join(gone_depts))
    subject = opt(args, "subject") if opt(args, "subject") is not None else ("" if seed.get("RESULT_STATUS") == "NONE" else seed.get("SUBJECT") or "")
    body = body_of(args, det)
    doc = {**seed, "SUBJECT": subject.strip(), "CONTENTS": body, "OPEN_GRADE": opt(args, "grade") or seed.get("OPEN_GRADE"),
           "READNG_LIMIT_AT": opt(args, "private") or seed.get("READNG_LIMIT_AT"), "PRSRV_PERIOD": opt(args, "keep") or seed.get("PRSRV_PERIOD"),
           "TMP_WDTB_DISP_NAME": joined(wdtb, "DISP_NAME"), "TMP_SUBJECT_NAME": joined(links, "SUBJECT"), "ROW_TYPE": "4", "ROW_ID": 1}
    if not doc["SUBJECT"]:
        blocks.append(NO_SUBJECT)
    if line:
        more_blocks, more_notes = line_blocks(line, refs, cascade_for(app, seed, start, page), str(seed.get("LEGACY_JOB_NAME_KR") or seed.get("LEGACY_JOB_ID")))
        blocks, notes = blocks + more_blocks, notes + more_notes
    else:
        blocks.append("결재선이 비었다 — 앱이 요청자 줄을 안 줬다. 문서 창에서 쓴다")
    if start != "new":
        notes.append(SAVE_UNMEASURED.format(word=table.STARTS[start].word))
    if start == "reuse":
        notes.append("save 는 지난 문서의 [재사용] 창을 연다 — 그 순간 서버에 임시저장이 하나 서고, 저장이 못 서면 그것을 지운다")
    payload = {"apprDocVO": doc}
    if line:
        payload["apprLineVO"] = with_doc([requester_line(line)] + line[1:], seed)
    for name, rows in (("refrnVO", with_doc(refs, seed)), ("wdtbVO", wdtb), ("refDocumentVO", with_doc(links, seed))):
        if rows:                        # 화면도 줄이 없는 데이터셋은 안 싣는다
            payload[name] = rows
    view = {"state": "blocked" if blocks else "ready", "from": start, "source": source_of(args, start),
            "form": f"{seed.get('FORM_ID')} {seed.get('LEGACY_JOB_NAME_KR') or ''}".strip(), "subject": doc["SUBJECT"],
            "body": {"chars": len(body), "start": body_text(body)}, "line": [who(r) for r in line], "refs": [who(r) for r in refs],
            "distribution": [r.get("DISP_NAME") for r in wdtb], "attachments": [r.get("ORGINL_FILE_NM") or r.get("DISP_FILE_NM") or r.get("FILE_NM") for r in attach],
            "links": [r.get("SUBJECT") for r in links],
            "grade": f"{doc['OPEN_GRADE']} {table.GRADES.get(doc['OPEN_GRADE'], '')}".strip(),
            "private": "비공개" if doc["READNG_LIMIT_AT"] == "Y" else "공개", "keep": doc["PRSRV_PERIOD"], "blocks": blocks, "notes": notes}
    # 열쇠는 보낼 문서의 값으로만 짓는다 — 알림(notes)은 그 판을 어떻게 지었나의 말이라 미리 보기와 저장에서 달라도 된다(다시 쓰기의
    # 배포처 거르기는 미리 보기만 알린다 — [재사용] 창이 이미 걸러 저장 쪽에는 뺄 것이 없다)
    view["key"] = ep_command.fingerprint([{k: v for k, v in view.items() if k != "notes"}, hashlib.sha256(body.encode("utf-8")).hexdigest(),
                                          [[r.get("APPR_USER_ID") or r.get("REFRN_USER_ID"), r.get("APPR_TYPE")] for r in line + refs],
                                          [r.get("REF_APPR_DOC_ID") for r in links]])
    view["state_word"] = STATE_WORDS[view["state"]]
    return {**view, "payload": payload}


def source_of(args, start: str) -> str:
    """출발을 고른 값 — 양식 · 지난 문서 · 임시저장의 id(사람이 준 그대로)."""
    return {"new": opt(args, "form"), "reuse": opt(args, "from"), "draft": opt(args, "draft")}[start] or ""


def shown(p: dict) -> dict:
    """사람에게 보일 판 — 앱에 보낼 짐과 지은 임시저장 표시는 뺀다. 빈 칸도 뺀다."""
    return {k: v for k, v in p.items() if k != "payload" and v not in (None, [], "")}


# ── 임시저장 (A1.3.5) · 맺기 (A1.3.6) ────────────────────────────────────────────────────────────
def saved(app, payload: dict) -> dict:
    """짐 하나를 임시저장한다 — 답 화면의 문서 줄(새 APPR_DOC_ID · 판). 앱이 안 받았다고 말하면 ``iams.Rejected``, 답 화면에 열쇠가 없으면
    ``iams.AppError``(섰는지 모른다)."""
    got = iams.doc_row(app.save(payload))
    if not got or iams.key_of(got) is None:
        raise iams.AppError("결재 앱의 임시저장 답 화면에 문서 열쇠가 없다")
    return got


def settled(app, key: str) -> dict:
    """저장한 뒤의 끝 — 임시저장 목록에서 그 문서를 다시 읽는다. 다시 읽기가 무엇으로 지든 「모른다」다(앱이 받은 뒤라 다시 부르면 두 번 선다)."""
    try:
        row = draft_row(app, key)
    except Exception:  # noqa: BLE001 — 저장한 뒤라 어떤 실패도 다시 부를 까닭이 아니다
        row = None
    if row is None:
        return {"state": "unsure", "state_word": STATE_WORDS["unsure"], "id": key}
    return {"state": "saved", "state_word": STATE_WORDS["saved"], "id": key, "subject": row.get("SUBJECT"), "doc_no": row.get("APPR_DOC_NO")}


def shown_window(key: str) -> dict:
    """임시저장한 문서의 고치는 창을 사람의 Edge 에 띄운다(open --box drafts 와 같은 창) — 창 주소 · 사람의 Edge 가 여는 주소 · 어디에 열었나.
    못 띄우면 그 까닭과 주소만 낸다 — 저장은 이미 섰다."""
    path = iams.at(iams.DRAFT_DOC, iams.doc_of(key))
    url = iams.browser(path)
    try:
        where = iams.launch(url)
    except Stop as exc:
        where = str(exc)
    return {"address": iams.APP_ROOT + path, "browser": url, "where": where}


# ── 지우기 (A1.3.7) ───────────────────────────────────────────────────────────────────────────
def discarded(app, row: dict) -> bool:
    """임시저장 한 건을 지운다 — 목록 줄 그대로에 지움 표시를 달아 보내고, 목록에서 사라졌나를 낸다."""
    app.tx(DISCARD, {"apprDocVO": {**row, "ROW_CHECK": True, "ROW_TYPE": "8", "ROW_ID": 1}})
    return draft_row(app, iams.key_of(row)) is None


def made_by(before: set | None, app, page: str | None, source: str) -> tuple[list, list]:
    """[재사용] 창이 세운 임시저장 — (거둘 줄 · 거두지 않고 알릴 열쇠). 거둘 줄은 창의 씨앗(``page`` 의 문서 줄 — 지난 문서 ``source`` 와 다른
    열쇠)과 같은 열쇠의 목록 줄 하나뿐이다. 창을 열기 앞의 목록(``before``)에 없던 다른 줄은 사람이 같은 때 세웠을 수도 있어 안 거두고 열쇠만
    알린다 — 창이 열렸는데 씨앗을 못 읽었을 때만(막혀 창을 안 연 판은 알릴 것도 없다). 목록을 못 읽으면 씨앗의 열쇠를 알릴 열쇠로 낸다."""
    seed = iams.key_of(iams.doc_row(page) or {})
    opened_reuse = page is not None and seed != source
    if before is None or not opened_reuse:
        return [], []
    try:
        new = [r for r in draft_rows(app) if iams.key_of(r) not in before]
    except Exception:  # noqa: BLE001 — 목록을 못 읽은 판(끊긴 세션)에서도 창이 세운 열쇠는 사람에게 댄다
        return [], [seed] if seed else []
    mine = [r for r in new if iams.key_of(r) == seed]
    return mine, ([] if mine or seed else [iams.key_of(r) for r in new])


def undo_made(app, made: list, unknown: list = ()) -> dict:
    """다시 쓰기 창이 세운 임시저장을 거둔다 — 사람에게 할 말(``cleanup``)과 남은 열쇠(``left`` — 못 지웠거나 거두지 않고 알린 것). 거둘 것도 알릴 것도
    없으면 빈 dict. 목록에서 이미 사라진 줄은 지웠다고 하지 않는다."""
    gone_keys, done, left = [], [], list(unknown)
    for row in made:
        key = iams.key_of(row)
        try:
            listed = draft_row(app, key)
            if listed is None:
                gone_keys.append(key)
            elif discarded(app, listed):
                done.append(key)
            else:
                left.append(key)
        except Exception:  # noqa: BLE001 — 거두기는 마지막 걸음이라 무엇으로 지든 사람에게 알린다
            left.append(key)
    said = []
    if done:
        said.append(f"다시 쓰기 창이 세운 임시저장({' · '.join(done)})은 지웠다")
    if gone_keys:
        said.append(f"다시 쓰기 창이 세운 임시저장({' · '.join(gone_keys)})은 목록에 이미 없었다")
    if left:
        said.append(f"다시 쓰기 창이 세웠을 수 있는 임시저장({' · '.join(left)})이 남았다 — box drafts 에서 보고 사람이 지운다")
    out = {"cleanup": " · ".join(said)} if said else {}
    return {**out, "left": left} if left else out


# ── 손 ────────────────────────────────────────────────────────────────────────────────────
def run(app, args, start) -> dict:
    """명령 하나 — preview 는 판을 보이고, save 는 보인 판 그대로일 때만 임시저장해 맺고 창을 띄우고, discard 는 보인 임시저장을 지운다."""
    if args.command == "discard":
        return discard(app, args)
    if args.command == "preview":
        p = plan(app, args, start, opened(app, args, start, making=False))
        return gone() if p["state"] == "gone" else shown(p)
    return save(app, args, start)


def save(app, args, start) -> dict:
    """save — 출발 열기(다시 쓰기는 연 창의 씨앗과 그 앞뒤 임시저장 목록으로 창이 세운 것을 가린다) → 판 → 열쇠 견주기 → 임시저장 → 맺기 → 창.
    창이 세운 임시저장은 저장이 서지 않은 모든 길(멈춤 · 끊김 포함)에서 거두고, 못 거뒀거나 섰는지 모르면 그 열쇠를 답에 싣는다."""
    source = iams.key_of(iams.doc_of(opt(args, "from"), "--from")) if start == "reuse" else None
    before = {iams.key_of(r) for r in draft_rows(app)} if start == "reuse" else None
    page, made, unknown, swept = None, [], [], False
    try:
        page = opened(app, args, start, making=True)
        made, unknown = made_by(before, app, page, source)
        p = plan(app, args, start, page)
        if p["state"] == "gone":
            return {**gone(), **undo_made(app, made, unknown)}
        if p["key"] != args.confirm:
            swept = True
            raise stale(p, undo_made(app, made, unknown).get("cleanup", ""))
        if p["blocks"]:
            return {"state": "blocked", "state_word": STATE_WORDS["blocked"], "blocks": p["blocks"], **undo_made(app, made, unknown)}
    except BaseException as exc:
        if swept:
            raise                           # 열쇠가 다른 멈춤은 이미 거뒀다
        if before is not None and page is not None and not (made or unknown):
            made, unknown = made_by(before, app, page, source)
        undone = undo_made(app, made, unknown)
        if undone:
            raise left_behind(exc, undone) from exc
        raise
    return after_save(app, p["payload"], made, unknown)


def left_behind(exc: BaseException, undone: dict) -> Stop:
    """저장 앞에서 멈췄는데 다시 쓰기 창이 세운 임시저장을 거뒀거나 못 거뒀다 — 그 말을 덧붙인 멈춤. 멈춤(``Stop``)은 그 값 그대로,
    세션이 끊겼으면 종료 3, 그 밖은 도구 고장(종료 1)."""
    if isinstance(exc, Stop):
        return Stop(exc.code, exc.kind, f"{exc} — {undone['cleanup']}.", stepped=exc.stepped)
    ended = isinstance(exc, (iams.SessionExpired, iams.SessionMissing))
    code, kind = (EXIT_SESSION, "session") if ended else (EXIT_TOOL, "tool")
    tail = NEXT_EP_LOGIN if ended else "다음: 그 임시저장을 box drafts 로 읽어 보인다"
    return Stop(code, kind, f"{exc} — {undone['cleanup']}. {tail}", stepped=True)


def after_save(app, payload: dict, made: list, unknown: list = ()) -> dict:
    """임시저장을 보내고 맺고 창을 띄운다. 아무것도 안 선 실패는 둘이다 — 앱이 안 받았다고 말했다(``Rejected`` → blocked 와 앱의 말) · 짐을
    보내기 전에 졌다(``sent`` 거짓 — 세션이 끊겨 토큰을 못 받았다). 둘 다 창이 세운 임시저장을 거둔다. 그 밖(보낸 뒤 세션이 끊겼다 — 앱이 짐을
    읽기 전에 돌려보냈는지는 못 쟀다 · 답이 꼴이 아니다 · 못 닿았다)은 들어갔을 수 있어 「모른다」로 내고 창이 세운 임시저장도 안 지운다(저장이 그 문서에 들었을 수 있다) — 그 열쇠를 답의
    ``made`` 에 싣는다. 저장이 다른 문서로 섰으면 창이 세운 임시저장을 지운다(같은 문서의 다음 판으로 섰으면 안 지운다). 창이 세웠는지
    가리지 못한 열쇠(``unknown``)는 어느 길에서도 지우지 않고 답에 싣는다."""
    keys = [iams.key_of(r) for r in made] + list(unknown)
    try:
        got = saved(app, payload)
    except iams.Rejected as exc:
        return {"state": "blocked", "state_word": STATE_WORDS["refused"], "blocks": [str(exc)], **undo_made(app, made, unknown)}
    except Exception as exc:
        if not getattr(exc, "sent", True):
            undone = undo_made(app, made, unknown)
            if undone:
                raise left_behind(exc, undone) from exc
            raise
        out = {"state": "unsure", "state_word": STATE_WORDS["unsure"], "said": f"{type(exc).__name__}: {exc}"}   # 보낸 뒤라 다시 부르면 두 번 선다
        return {**out, "made": keys} if keys else out
    key = iams.key_of(got)
    out = settled(app, key)
    out.update(undo_made(app, [r for r in made if r.get("APPR_DOC_ID") != got.get("APPR_DOC_ID")], unknown))
    if out["state"] == "saved":
        out["window"] = shown_window(key)
        out["next"] = f"다음: 상신은 사람이 띄운 창에서 누른다. 창을 다시 띄우려면 open {key} --box drafts"
    return out


def stale(p: dict, cleanup: str) -> Stop:
    """보인 판과 지금 판이 다르다는 멈춤(종료 4) — 지금 판의 열쇠와 막는 까닭을 말에 싣는다. 사람에게는 preview 를 다시 불러 보인다."""
    more = f" 막는 까닭: {' / '.join(p['blocks'])}." if p.get("blocks") else ""
    tail = f" {cleanup}." if cleanup else ""
    return Stop(EXIT_STALE, "stale", f"{STATE_WORDS['moved']} — 지금 판의 key 는 {p['key']}.{more}{tail} 다음: 같은 값으로 preview 를 다시 불러 "
                                     "사람에게 보이고 「네」 를 받은 뒤 그 key 로 부른다", stepped=True)


def gone() -> dict:
    """그 문서가 없다는 답."""
    return {"state": "gone", "state_word": STATE_WORDS["gone"]}


def said(text: str) -> dict:
    """사람에게 덧붙일 말 한 칸 — 없으면 빈 dict."""
    return {"cleanup": text} if text else {}


def discard(app, args) -> dict:
    """임시저장 지우기 — 목록에서 그 줄을 읽어 preview --draft 와 같은 판의 열쇠를 견주고, 같을 때만 지운다."""
    key = iams.key_of(iams.doc_of(opt(args, "draft"), "--draft"))
    if draft_row(app, key) is None:
        return gone()
    p = plan(app, args, "draft", opened(app, args, "draft", making=False))
    if p["state"] == "gone":
        return gone()
    if p["key"] != args.confirm:
        raise stale(p, "")
    row = draft_row(app, key)
    if row is None:
        return gone()
    try:
        done = discarded(app, row)
    except iams.SessionExpired:
        raise
    except iams.AppError:
        done = False
    return {"state": "discarded" if done else "unsure", "state_word": STATE_WORDS["discarded" if done else "unsure"], "id": key,
            "subject": row.get("SUBJECT")}
