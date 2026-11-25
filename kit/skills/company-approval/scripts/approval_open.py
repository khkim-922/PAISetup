"""전자결재 스킬의 창 띄우기 손 — open. 문서 하나의 창 주소를 짓고 사람의 평소 Edge 에 새 탭으로 연다. 누르지 않는다 — 결재 · 반려 ·
상신 · 접수는 사람이 그 창에서 한다.

부르는 꼴 — 입구(approval.py)가 ``run(app, args, start)`` 하나를 부른다: app 은 세션을 쥔 ``iams.App``, args 는 입구의 argparse 값,
start 는 None. 답은 dict(JSON 하나로 찍힌다). 멈출 때는 ``ep_command.Stop``.

짜임 — 손(``open_doc``)이 손가락을 엮는다: 함 고르기(``box_for``) → 창 주소(``window``) → 띄우기(바탕 ``iams`` 의 ``browser`` · ``launch``).
문서 열쇠의 꼴 · 앱 안의 주소 · 결재함의 기간 · SSO 넘김 주소 · Edge 띄우기는 바탕 ``iams`` 가 든다 — 쓰기 손이 저장한 뒤 같은 길로 창을 연다.

- 창의 단추는 주소의 ``_MENU_ACTION_`` 이 가른다 — 그 줄이 온 함의 화면이 여는 값 그대로(표 ``approval_table.BOXES`` 의 ``menu`` · ``by_type``).
  결재하기 함은 APPROVAL(참조 줄이면 REFERENCE), 배포받은 문서는 DISTRIBUTION, 임시저장은 고치는 창(``/iams/request.ex`` · SAVE),
  나머지는 보기만 하는 창이다. ``--box`` 를 안 주면 결재하기 함 · 배포받은 문서 함(기본 기간 — 오늘까지 한 달)에 그 열쇠(넷 다)의 줄이 있나를
  먼저 보고, 없으면 문서의 상태로 고른다(임시저장이면 고치는 창 · 아니면 보기 창). 어디까지 봤나는 답의 ``looked`` 가 댄다
- 사람의 브라우저에는 앱의 세션 쿠키가 없다 — 앱 주소를 SSO 넘김 화면의 ``redir_url`` 로 싸서 연다. 이 꼴로 띄워 본 적은 없다
  (WRITE-MAP 9 절 — 못 잰 것). 답의 ``unmeasured`` 가 그렇다고 댄다
"""

from __future__ import annotations

import urllib.parse
from datetime import date

from ep_command import EXIT_ARGS, Stop

import approval_table as table   # 표(BOXES) — 입구를 싣지 않는다
import iams            # 바탕 — 문서 열쇠 · 앱 안의 주소 · 결재함의 기간 · SSO 넘김 주소 · Edge 띄우기
DRAFTS = "drafts"
TODO = "todo"
RECEIVED = "received"
LOOK = (TODO, RECEIVED)                   # --box 없이 열 때 그 문서가 있나 보는 함 — 창에 사람이 누를 단추가 서는 함
UNMEASURED = "SSO 넘김 주소로 사람의 Edge 에 문서 창을 띄우는 꼴은 아직 못 쟀다 — 창에 로그인 화면이나 오류가 뜨면 그 말을 받아 알린다"


# ── 함 고르기 ─────────────────────────────────────────────────────────────
def row_in(app, box_name: str, key: dict) -> tuple[dict | None, str]:
    """함 하나의 목록에서 그 문서(열쇠 넷이 다 같은 줄)의 줄과 어디까지 봤나의 말 — 없으면 (None, 말). 기간을 꼭 받는 함은 그 함의 기본 기간만 본다."""
    one = table.BOXES[box_name]
    span = iams.period(one, None, None, date.today())
    want = iams.key_of(key)
    seen = f"{box_name}({span[0]} ~ {span[1]})" if span else box_name
    for row in app.tx(one["path"], {"paramMap": iams.box_query(one, span, None)}).get("DS_RESULT") or []:
        if iams.key_of(row) == want:
            return row, seen
    return None, seen


def box_for(app, args, key: dict) -> tuple[str, dict | None, list]:
    """창을 고를 함 · 그 함의 줄 · 어디까지 봤나(함과 기간). ``--box`` 를 줬으면 그 함 — 함의 줄에 따라 창이 갈리는 함(``by_type`` — 결재하기의
    참조 줄)이면 그 줄을 찾아 함께 낸다. 안 줬으면 창이 갈리는 함(``LOOK`` 의 차례 — 결재하기 · 배포받은)에 그 문서가 있나 보고, 없으면 문서
    보기 화면의 상태로 고른다(임시저장 → drafts · 그 밖 → 보기 창, 함 이름 빈 글자)."""
    if args.box:
        if not table.BOXES[args.box].get("by_type"):
            return args.box, None, []
        row, seen = row_in(app, args.box, key)
        return args.box, row, [seen]
    looked = []
    for name in LOOK:
        row, seen = row_in(app, name, key)
        looked.append(seen)
        if row is not None:
            return name, row, looked
    seed = iams.doc_row(app.page(iams.at(iams.VIEW, key)))
    if seed is None:
        raise Stop(EXIT_ARGS, "args", f"앱이 문서 {args.doc} 을 안 냈다 — 없거나 이 사람이 못 여는 것이다. 다음: box 의 id 를 다시 본다", stepped=True)
    return (DRAFTS if seed.get("RESULT_STATUS") == "SAVED" else ""), None, looked


# ── 창 주소 ──────────────────────────────────────────────────────────────
def window(box_name: str, key: dict, row: dict | None) -> str:
    """함 · 문서 열쇠 · 그 줄 → 앱의 문서 창 주소(앱 안 경로). 함이 없으면 보기만 하는 창."""
    if not box_name:
        return iams.at(iams.VIEW, key)
    one = table.BOXES[box_name]
    menu = (one.get("by_type") or {}).get((row or {}).get("APPR_TYPE"), one["menu"])
    query = {"apprDocId": key["APPR_DOC_ID"], "avn": key["AVN"], "ovn": key["OVN"], "apvn": key["APVN"]}
    if one.get("menu_id"):
        query["_MENU_ID_"] = one["menu_id"]
    query["_MENU_ACTION_"] = menu
    return f"{one['screen']}?{urllib.parse.urlencode(query)}"


# ── 손 ───────────────────────────────────────────────────────────────────
PRESS = {TODO: "결재 · 반려(참조 줄이면 참조 의견)는 사람이 그 창에서 누른다", DRAFTS: "고치고 상신하는 일은 사람이 그 창에서 한다",
         RECEIVED: "접수는 사람이 그 창에서 누른다"}
VIEW_ONLY = "이 창은 보기만 한다 — 결재 · 참조 의견이면 --box todo, 배포받은 문서의 접수면 --box received, 임시저장 고치기면 --box drafts 로 다시 띄운다"


def open_doc(app, args) -> dict:
    """open — 문서 하나의 창. 열쇠 → 함 고르기 → 창 주소 → SSO 넘김 주소 → 띄우기."""
    key = iams.doc_of(args.doc)
    box_name, row, looked = box_for(app, args, key)
    path = window(box_name, key, row)
    url = iams.browser(path)
    where = iams.launch(url)
    out = {"state": "opened", "id": iams.key_of(key), "box": box_name or None, "window": iams.APP_ROOT + path, "url": url,
           "where": where, "press": PRESS.get(box_name, VIEW_ONLY), "unmeasured": UNMEASURED}
    if looked:
        out["looked"] = f"그 열쇠의 줄을 본 함: {' · '.join(looked)}" + ("" if row is not None else
                                                                   " — 없었다. 그보다 오래된 줄이면 --box 로 함을 짚어 다시 띄운다")
    return out


def run(app, args, start) -> dict:
    """명령 하나 — open 의 손."""
    return open_doc(app, args)
