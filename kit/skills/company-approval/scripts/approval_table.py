"""전자결재 스킬의 표 — 출발 × 바꿀 것 × 끝(``STARTS`` · ``CHANGES`` · ``NOT_YET`` · ``ENDS``) · 읽기(``READS``) · 결재함(``BOXES``) ·
화면의 코드 값(``GRADES`` · ``KEEPS``). 입구(approval.py)와 손 셋이 함께 읽는 한 자리라 입구 밑 · 손 밑에 산다 — 아무 손도 입구를 싣지 않는다.
이 파일은 표만 든다(칸의 꼴은 ``ep_command`` 의 ``Start`` · ``Change`` · ``NotYet``). 입구가 ep-login 의 자리를 ``sys.path`` 에 넣은 뒤 싣는다.
"""

from __future__ import annotations

from ep_command import Change, NotYet, Start

ON_SCREEN = "그 문서 창에서 사람이 한다 — open <문서> 로 띄운다"
GRADES = {"S": "기밀", "A": "사외비A", "B": "사외비B", "C": "일반"}          # 화면 「보안 등급」(searchOpenGrade) — 앱 기본은 A
KEEPS = ("6M", "1Y", "3Y", "5Y", "10Y", "UNLIMITED")                      # 화면 「보존 기한」(PERIOD 코드) — 앱 기본은 5Y
PEOPLE_META = "people.json"


# ── 손가락의 표 — 출발 × 바꿀 것 × 끝. 손가락을 더하거나 빼는 일은 이 표의 줄과 그 일을 하는 손 하나다(칸의 꼴은 ep_command) ──────
# 출발 — 문서 창 하나. 셋 다 같은 화면(requestApproval)이고 씨앗만 다르다
STARTS = {
    "new": Start("새 문서", "양식 하나의 새 문서 창 — --form 으로 양식을 고른다(자유 품의서는 IA011)"),
    "reuse": Start("지난 문서 다시 쓰기", "완료 · 반려 · 취소 문서의 [재사용] 창 — 제목 · 본문 · 결재선 · 참조 · 배포 · 첨부 · 관련 문서를 이어받는다. "
                   "⚠ 그 창은 여는 순간 임시저장을 하나 세운다 — 그래서 미리 보기도 저장 직전에 다시 열지 않고, 저장이 못 서면 그 임시저장을 지운다",
                   "--from"),
    "draft": Start("임시저장 고치기", "임시저장 문서의 창 — box drafts 줄의 id 그대로", "--draft"),
}
ALL = tuple(STARTS)
PEOPLE = f"사람 파일 — 주소록(스킬 company-directory)의 찾기가 --out 에 쓴 {PEOPLE_META} 그대로(여러 번 준다 · 준 차례가 결재 차례)"
CHANGES = {
    "form": Change((("--form", {"metavar": "FORM_ID"}),), ("new",), "양식 — forms 의 FORM_ID(자유 품의서 IA011 · 결재자 여럿이면 IA037 일반품의서)",
                   "양식은 새 문서에서만 고른다 — 다른 양식으로 쓰려면 --form 으로 새로 짓는다", need=("new",)),
    "subject": Change((("--subject", {}),), ALL, "제목", need=("new",)),
    "body": Change((("--body-file", {"metavar": "HTML"}),), ALL, "본문 — HTML 파일 한 덩이(양식 틀이 있으면 form 이 낸 틀을 고친 것)"),
    "approvers": Change((("--approvers", {"nargs": "+", "metavar": PEOPLE_META}),), ALL,
                        "결재선 — 나 다음의 사람들, 차례대로. 마지막이 결재 · 사이는 같은 부서면 검토 · 남의 부서면 협조. 주면 결재선을 통째로 갈고, "
                        "안 주면 출발의 결재선(새 문서는 앱이 주는 기본선 — 나와 윗사람) 그대로. 다단결재가 아닌 업무(품의서 IA011 · 양식결재 IA02 · 정보보호 IA04)는 "
                        "결재자 한 명. " + PEOPLE, unmeasured=ALL),
    "agree": Change((("--agree", {"nargs": "+", "metavar": PEOPLE_META}),), ALL, "합의 — 결재선 끝 사람 앞에 같은 차례로 선다. 주면 합의를 통째로 간다. " + PEOPLE, unmeasured=ALL),
    "refs": Change((("--refs", {"nargs": "+", "metavar": PEOPLE_META}),), ALL, "참조 — 주면 참조를 통째로 간다. " + PEOPLE, unmeasured=ALL),
    "link": Change((("--link", {"action": "append", "metavar": "문서"}),), ALL, "관련 문서 — 지난 결재 문서의 id(box · read 줄의 id 그대로 · 여러 번). 주면 관련 문서를 통째로 간다", unmeasured=ALL),
    "grade": Change((("--grade", {"choices": list(GRADES)}),), ALL, "보안 등급 — " + " · ".join(f"{k} {v}" for k, v in GRADES.items())),
    "private": Change((("--private", {"choices": ["Y", "N"]}),), ALL, "비공개 — Y 비공개 · N 공개(기본은 양식마다)"),
    "keep": Change((("--keep", {"choices": list(KEEPS)}),), ALL, "보존 기한"),
}
# 아직 없는 손가락 — 회사에서 그 화면 동작을 재 오면 이 줄을 걷고 CHANGES 한 줄과 그 일을 하는 손 하나를 더한다
NOT_YET = {
    "attach": NotYet("첨부 올리기", "임시저장 뒤 그 문서 창에서 사람이 붙인다 — open <문서>", (("--attach", {"action": "append", "metavar": "파일"}),)),
    "dist": NotYet("배포처 지정", "임시저장 뒤 그 문서 창의 [배포처]에서 사람이 고른다 — open <문서>", (("--dist", {"nargs": "+"}),)),
    "submit": NotYet("상신 · 승인 · 반려 · 회수", ON_SCREEN, (("--submit", {"action": "store_true", "default": None}),)),
}
# 끝 — save 는 임시저장까지이고 창을 띄운다. 상신은 끝에 없다(사람이 그 창에서 누른다)
ENDS = {
    "save": (ALL, "임시저장 — 그 문서 창을 사람의 Edge 에 띄운다. 열쇠: --confirm <preview 의 key>", True),
    "discard": (("draft",), "임시저장 지우기 — 이 스킬이 세운 임시저장을 거둘 때만. 열쇠: --confirm <preview --draft 의 key>", False),
}
# 읽기 — 이름 → 사람 말. 인자는 parser 가 단다
READS = {
    "forms": "양식 목록 — 업무마다 FORM_ID · 이름 · 결재자 여럿을 받나(앱에서 받는다)",
    "form": "양식 하나의 틀 — 새 문서 창이 주는 기본 결재선 · 기본값(보안 · 공개 · 보존) · 본문 HTML 틀. 본문 틀은 파일로 남기고 그 경로를 낸다",
    "box": "결재함 하나의 줄 — 제목 · 요청자 · 때 · 상태 · 문서 열쇠. 함마다의 뜻은 box --help",
    "read": "문서 하나 — 머리 · 결재선과 의견 · 참조 · 배포 · 첨부 이름 · 관련 문서 · 본문 글자",
    "open": "문서 하나의 창을 사람의 Edge(사내 세션이 사는 창)에 띄운다 — 결재 · 반려 · 상신은 사람이 그 창에서 누른다",
}
# 결재함 — 이름 → 그 함 화면(list_approval_*.ex)이 부르는 거래와 칸 · 그 줄의 문서 창. 함을 더하는 일은 이 표의 줄 하나다(손은 하나)
#   path 거래 · kind PROG_KIND · no_wait NO_WAIT · legacy LEGACY_ID(비면 안 싣는다) · dates 기간 칸의 머리(APPR → APPR_DT_FR · TO, REQ → REQ_DT_*,
#   None 이면 기간이 없다) · need 화면이 기간을 꼭 받고(안 주면 한 달 전 ~ 오늘) 6 달까지만 묻는다 · 아니면 기간은 줄 때만 싣는다 · who · when 줄의 요청자 · 때 칸(앞에서부터 처음 찬 것 — 잰 답이 없는 함은 화면의 열 이름이 먼저) · screen 창 화면 · menu_id ·
#   menu 창의 _MENU_ACTION_ · by_type 줄의 APPR_TYPE 이 이 값이면 그 _MENU_ACTION_(결재하기 함의 참조 줄)
_DOC = "/iams/document.ex"
BOXES = {
    "todo": {"word": "결재하기 — 내가 결재 · 참조할 차례인 문서", "path": "/iams/commonSearch/documentsDAO/selectApprovalDoc.ex",
             "dates": "APPR", "who": ("USER_NAME_KR",), "when": ("APPR_DT",),
             "screen": _DOC, "menu_id": "_APPROVAL_", "menu": "APPROVAL", "by_type": {"REFERENCE": "REFERENCE"}},
    "progress": {"word": "결재진행 — 내가 거친 문서 가운데 아직 진행 중인 것", "path": "/iams/commonSearch/documentsDAO/selectApprovalCompleteDoc.ex",
                 "kind": "PROGRESS", "no_wait": "Y", "dates": "REQ", "who": ("REQ_USER_NM", "USER_NAME_KR"), "when": ("REQ_APPR_DT", "APPR_DT"),
                 "screen": _DOC, "menu_id": "_APPROVAL_", "menu": "APPROVAL"},
    "done": {"word": "결재완료 — 내가 거친 문서 가운데 끝난 것", "path": "/iams/commonSearch/documentsDAO/selectApprovalCompleteDoc.ex",
             "kind": "RESULT", "dates": "APPR", "need": True, "who": ("REQ_USER_NM", "USER_NAME_KR"), "when": ("APPROVED_DT", "APPR_DT"),
             "screen": _DOC, "menu_id": "_APPROVAL_", "menu": "NONE"},
    "stopped": {"word": "반려 · 취소 — 내가 거친 문서 가운데 반려 · 취소된 것", "path": "/iams/commonSearch/documentsDAO/selectApprovalStoppedDoc.ex",
                "kind": "APPR", "dates": "APPR", "need": True, "who": ("REQ_USER_NM", "USER_NAME_KR"), "when": ("APPR_DT",),
                "screen": _DOC, "menu_id": "_STOPPED_", "menu": "NONE"},
    "received": {"word": "배포받은 문서", "path": "/iams/commonSearch/documentsDAO/selectDistributionDoc.ex",
                 "dates": "APPR", "need": True, "who": ("USER_NAME_KR",), "when": ("APPR_DT",),
                 "screen": _DOC, "menu_id": "_APPROVAL_", "menu": "DISTRIBUTION"},
    "sent": {"word": "내가 올린 결재 — 진행 중(상신함 결재진행)", "path": "/iams/commonSearch/documentsDAO/selectApprovalProgress.ex",
             "kind": "PROGRESS", "dates": "APPR", "who": ("USER_NAME_KR",), "when": ("APPR_DT",),
             "screen": _DOC, "menu_id": "_APPROVAL_", "menu": "NONE"},
    "sent-done": {"word": "내가 올린 결재 — 끝난 것(결재완료함)", "path": "/iams/commonSearch/documentsDAO/selectApprovalRequestDoc.ex",
                  "dates": "APPR", "need": True, "who": ("REQ_USER_NM", "USER_NAME_KR"), "when": ("APPR_DT",),
                  "screen": _DOC, "menu_id": "_APPROVAL_", "menu": "CPLT_NONE"},
    "sent-stopped": {"word": "내가 올린 결재 — 반려 · 취소된 것", "path": "/iams/commonSearch/documentsDAO/selectApprovalStoppedDoc.ex",
                     "kind": "REQ", "dates": "APPR", "need": True, "who": ("REQ_USER_NM", "USER_NAME_KR"), "when": ("APPR_DT",),
                     "screen": _DOC, "menu_id": "_STOPPED_", "menu": "NONE"},
    "drafts": {"word": "임시저장", "path": "/iams/commonSearch/documentsDAO/selectApprovalProgress.ex",
               "kind": "NEW", "legacy": "IAMS", "dates": None, "who": ("USER_NAME_KR",), "when": ("APPR_DT",),
               "screen": "/iams/request.ex", "menu": "SAVE"},
}
