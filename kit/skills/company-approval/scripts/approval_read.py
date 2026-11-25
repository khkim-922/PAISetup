"""전자결재 스킬의 읽기 손 — forms · form · box · read. 결재 앱에 묻기만 하고 아무것도 바꾸지 않는다.

부르는 꼴 — 입구(approval.py)가 ``run(app, args, start)`` 하나를 부른다: app 은 세션을 쥔 ``iams.App``, args 는 입구의 argparse 값,
start 는 읽기라 None. 답은 dict(JSON 하나로 찍힌다). 멈출 때는 ``ep_command.Stop``.

짜임 — 명령마다 손 하나(``forms`` · ``form`` · ``box`` · ``read``)가 손가락을 엮기만 한다. 손가락은 일 하나씩이고 아래로만 부른다:
앱에 묻는 것은 ``iams.App`` 의 ``tx`` · ``page`` 뿐이고, 줄 꼴 · 본문 풀기 · 답 맞추기는 앱을 모른다.

- 결재함 — 손은 하나다. 함마다 다른 것(거래 · PROG_KIND · NO_WAIT · 기간 칸 · 줄의 요청자 · 때 칸)은 표 ``approval_table.BOXES`` 가 든다
- 문서 열쇠 — 앱의 문서는 ``APPR_DOC_ID`` 와 판 셋(OVN · AVN · APVN)으로 선다. 답의 ``id`` 는 그 넷을 「.」 로 이은 글자다 — 꼴의 주인은
  바탕 ``iams``(``key_of`` · ``doc_of``)이고, read · open · 쓰기의 --from · --draft · --link 가 그대로 받는다. 열쇠 칸이 빠진 줄은 id 를 안 싣는다
- 결재함의 기간 · 조회 칸도 바탕 ``iams``(``period`` · ``box_query``)가 든다 — 창 손이 같은 꼴로 함을 본다
- 본문 — 문서 화면의 ``FORM_TYPE`` 이 가른다. HTML · MIME 은 ``selectApprDetails`` 의 ``contents`` 가 본문 HTML 이라 형제 스킬
  company-mail 의 ``visible`` 이 글자로 푼다(숨긴 글은 걷고 그 수를 ``hidden`` 에). AI(SR 같은 시스템 연계 문서)는 ``contents`` 가 XML 자료라
  칸마다 「이름: 값」 한 줄로 푼다 — 앱의 AI 보기 화면은 글을 스크립트로 그려, 받은 HTML 에는 글이 없다
- 첨부는 이름 · 크기까지 — 받지 않는다
- 내는 것 — 답 하나가 ``OUT_BYTES`` 를 안 넘는다. 넘으면 줄 · 본문을 덜고 ``more`` 가 이어 읽는 인자를 댄다
"""

from __future__ import annotations

import json
import pathlib
import re
import tempfile
import xml.etree.ElementTree as ET
from datetime import date

import ep_command  # 입구가 ep-login 의 자리를 sys.path 에 넣었다
from ep_command import EXIT_ARGS, OUT_BYTES, Stop

import approval_table as table   # 표(BOXES · GRADES) — 입구를 싣지 않는다
import iams        # 바탕 — 앱 안의 주소 · 문서 열쇠 · 결재함의 기간 · 화면의 데이터셋. 묻기는 받은 app 으로

HERE = pathlib.Path(__file__).resolve().parent
MAIL_SCRIPTS = HERE.parents[1] / "company-mail" / "scripts"     # 형제 스킬 — 본문 HTML 을 푸는 손(``visible``)이 사는 자리
JOBS = "/iams/commonSearch/documentsDAO/selectNewDocPopupJobList.ex"    # 새 문서 창의 업무 목록
FORMS = "/iams/commonSearch/documentsDAO/selectNewDocPopupFormList.ex"  # 업무 하나의 양식 목록
FORM_ID = re.compile(r"[0-9A-Za-z_]+")                         # 양식 id 의 꼴 — 주소 · 파일 이름에 그대로 들어간다
FORM_DIR = "company-approval"      # form 이 본문 틀을 남기는 자리 — 임시 폴더 아래
READ_FIRST = 6000                  # read 가 한 번에 싣는 본문 글자 수의 위 — 한글 본문은 OUT_BYTES 가 먼저 끊는다
HIDDEN_XML = ("_IP",)              # AI 자료에서 안 내는 칸 이름의 끝 — 사람 PC 의 주소
TEXT_TYPES = ("HTML", "MIME")      # 본문이 HTML 인 양식 꼴 — 문서 화면의 _FORM_TYPE_ 가 이 둘이면 selectApprDetails 의 contents 가 본문 HTML
AI_TYPE = "AI"                     # 시스템 연계 문서의 양식 꼴 — contents 가 XML 자료
HTML_VALUE = re.compile(r"<[a-zA-Z][^>]*>")   # 남이 쓴 값이 HTML 조각인가
XML_DECL = re.compile(r"^\s*<\?xml[^>]*\?>")   # XML 선언 — 글자로 읽을 때 뗀다
CDATA = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.S)
# 줄에 상태 말(RESULT_STATUS_NM)이 없는 함(결재완료함 · 기안 함)의 상태 코드 → 말 — 말을 싣는 함의 답이 든 짝 그대로(잰 것). 표에 없는 코드는 그대로 낸다
STATE_WORD = {"APPROVED": "결재승인", "CANCELED": "결재취소", "RETURNED": "결재반려", "REMOVED": "폐기", "SAVED": "저장완료",
              "NONE": "새 문서"}


# ── 결재함 ───────────────────────────────────────────────────────────────
def first(row: dict, keys) -> str | None:
    """줄에서 ``keys`` 의 차례로 처음 찬 칸의 값."""
    return next((row[k] for k in keys if row.get(k) not in (None, "")), None)


def box_line(box: dict, row: dict) -> dict:
    """앱의 목록 줄 → 답의 줄 — 문서 열쇠 · 제목 · 요청자와 부서 · 때 · 상태 · 시스템과 업무 · 문서 번호. 빈 칸은 안 싣는다."""
    line = {"id": iams.key_of(row), "subject": row.get("SUBJECT"), "who": first(row, box["who"]),
            "dept": first(row, ("REQ_DEPT_NM_KR", "DEPT_NM_KR")), "when": first(row, box["when"]),
            "state": row.get("RESULT_STATUS_NM") or STATE_WORD.get(row.get("RESULT_STATUS"), row.get("RESULT_STATUS")),
            "system": row.get("LEGACY_NAME_KR"), "job": row.get("LEGACY_JOB_NAME_KR"), "no": row.get("APPR_DOC_NO")}
    if row.get("APPR_TYPE") in (box.get("by_type") or {}):
        line["as"] = row.get("APPR_TYPE_NM") or row["APPR_TYPE"]   # 결재하기 함의 참조 줄 — 창이 참조 의견 창으로 열린다
    return {k: v for k, v in line.items() if v not in (None, "")}


def page_rows(out: dict, rows: list, start: int, more) -> dict:
    """답 ``out`` 의 ``rows`` 칸에 ``start`` 째 줄부터 ``OUT_BYTES`` 안에 드는 만큼 싣고, 남으면 ``more(다음 자리)`` 를 단다."""
    most = max(0, len(rows) - start)
    while True:
        out["rows"] = rows[start:start + most]
        out.pop("more", None)
        if start + most < len(rows):
            out["more"] = more(start + most)
        if most <= 1 or ep_command.size(out, 1) <= OUT_BYTES:
            return out
        most -= max(1, most // 8)


def box(app, args) -> dict:
    """box — 함 하나의 줄. 표에서 함을 고르고 → 기간 · 조회 칸 → 거래 하나 → 줄 꼴 → 답 크기에 맞춘다."""
    one = table.BOXES[args.box]
    span = iams.period(one, args.since, args.until, date.today())
    rows = [box_line(one, r) for r in app.tx(one["path"], {"paramMap": iams.box_query(one, span, args.words)}).get("DS_RESULT") or []]
    out = {"box": args.box, "word": one["word"], "count": len(rows)}
    for word, day in zip(("since", "until"), span or ()):
        if day:
            out[word] = day.isoformat()
    again = again_args(args.box, span, args.words)
    return page_rows(out, rows, max(0, args.start or 0), lambda end: f"다음: box {again} --from {end} 로 이어 본다")


def again_args(name: str, span, words: str | None) -> str:
    """이어 보는 부름의 인자 — 같은 함 · 같은 기간(기본 기간도 그날로 박는다 — 날이 바뀌어도 같은 줄이 이어진다 · 안 준 쪽은 안 싣는다) · 같은 제목 말."""
    parts = [name]
    for flag, day in zip(("--since", "--until"), span or ()):
        if day:
            parts.append(f"{flag} {day.isoformat()}")
    if words:
        parts.append(f"--subject {json.dumps(words, ensure_ascii=False)}")
    return " ".join(parts)


# ── 양식 ─────────────────────────────────────────────────────────────────
def jobs(app) -> list[dict]:
    """새 문서 창의 업무들 — 「전체」(열쇠 없는 줄)는 뺀다."""
    return [j for j in app.tx(JOBS, {"paramMap": {}}).get("DS_RESULT") or [] if j.get("LEGACY_JOB_ID")]


def job_forms(app, job: dict) -> list[dict]:
    """업무 하나의 양식 줄 — FORM_ID · 이름 · 비고."""
    rows = app.tx(FORMS, {"paramMap": {"LEGACY_JOB_ID": job["LEGACY_JOB_ID"]}}).get("DS_RESULT") or []
    return [{k: v for k, v in (("id", r.get("FORM_ID")), ("title", (r.get("TITLE") or "").strip()), ("note", r.get("REMARK"))) if v} for r in rows]


def forms(app, args) -> dict:
    """forms — 업무마다 양식. 업무 목록 → 업무마다 양식 목록(새 문서 창의 두 칸과 같은 차례)."""
    out = [{"job": j["LEGACY_JOB_ID"], "word": j.get("LEGACY_JOB_NAME_KR"), "forms": job_forms(app, j)} for j in jobs(app)]
    return {"jobs": out, "count": sum(len(j["forms"]) for j in out),
            "next": "다음: form <FORM_ID> 로 그 양식의 기본 결재선 · 기본값 · 본문 틀을 본다(결재자 여럿을 받나도 거기서)"}


def seed_of(page: str, what: str) -> dict:
    """화면에 박힌 문서 한 줄(``iams.doc_row``) — 없거나 양식(FORM_ID)이 비면 Stop(인자). ``what`` 은 무엇을 열었나(멈추는 말)."""
    row = iams.doc_row(page)
    if row is None or not row.get("FORM_ID"):
        raise Stop(EXIT_ARGS, "args", f"앱이 {what}을 안 냈다 — 없거나 이 사람이 못 여는 것이다. 다음: forms · box 의 id 를 다시 본다", stepped=True)
    return row


def person(row: dict, name_keys, comment_key: str, when_key: str) -> dict:
    """결재선 · 참조의 한 사람 — 이름 · 부서 · 직책 · 구분 · 상태 · 때 · 의견 · 퇴직. 빈 칸은 안 싣는다. 의견은 남이 쓴 글이라 ``plain_value`` 가
    푼다 — 걷은 숨긴 덩이는 ``hidden`` 칸이 센다."""
    said, hidden = plain_value(row.get(comment_key))
    one = {"name": first(row, name_keys), "dept": row.get("DEPT_NAME_KR"), "title": first(row, ("JOB_RSP_NM_KR", "JOB_POSITION_NM_KR")),
           "as": row.get("APPR_TYPE_NAME"), "state": row.get("APPR_STATUS_NAME"), "when": row.get(when_key), "opinion": said,
           "retired": True if row.get("RETIRE_AT") == "YES" else None, "hidden": hidden or None}
    return {k: v for k, v in one.items() if v not in (None, "")}


def line_of(got: dict) -> list[dict]:
    """결재선 — 차례(APPR_LINE_SEQ · 합의는 같은 차례의 APPR_LINE_ORDR)대로."""
    rows = sorted(got.get("apprLineList") or [], key=lambda r: (r.get("APPR_LINE_SEQ") or 0, r.get("APPR_LINE_ORDR") or 0))
    return [person(r, ("USER_NAME_KR", "APPR_USER_NAME"), "APPR_COMMENT", "APPR_DT") for r in rows]


def defaults_of(seed: dict) -> dict:
    """문서 줄의 보안 등급 · 공개 · 보존 기한 — 코드와 사람 말."""
    grade = seed.get("OPEN_GRADE")
    return {"grade": grade, "grade_word": seed.get("OPEN_GRADE_NM") or table.GRADES.get(grade), "private": seed.get("READNG_LIMIT_AT"),
            "keep": seed.get("PRSRV_PERIOD"), "keep_word": seed.get("PRSRV_PERIOD_NM")}


def template_path(form_id: str) -> pathlib.Path:
    """양식 틀을 남기는 파일 — 임시 폴더 아래 ``FORM_DIR/form_<FORM_ID>.html``."""
    return pathlib.Path(tempfile.gettempdir()) / FORM_DIR / f"form_{form_id}.html"


def save_template(form_id: str, html: str) -> str:
    """양식 틀 HTML 을 파일로 남기고 그 경로 — 쓰기 명령의 ``--body-file`` 은 이 파일을 고친 사본을 받는다."""
    path = template_path(form_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return str(path)


def form(app, args) -> dict:
    """form — 양식 하나의 틀. 새 문서 창(열어도 서버에 안 남는다) → 씨앗 · 다단 → 그 씨앗의 기본 결재선 · 본문 틀 → 틀을 파일로."""
    form_id = args.form_id.strip()
    if not FORM_ID.fullmatch(form_id):
        raise Stop(EXIT_ARGS, "args", f"양식 id 가 꼴이 아니다: {args.form_id!r}. 다음: forms 의 FORM_ID(IA011 꼴)를 그대로 준다", stepped=True)
    page = app.page(iams.NEW_DOC.format(form=form_id))
    seed = seed_of(page, f"양식 {form_id} 의 새 문서 창")
    got = iams.details(app, seed)
    cascade = iams.cascade_of(page)
    out = {"form": seed["FORM_ID"], "title": seed.get("SUBJECT"), "job": seed.get("LEGACY_JOB_ID"), "job_word": seed.get("LEGACY_JOB_NAME_KR"),
           "many_approvers": cascade, **defaults_of(seed), "line": line_of(got)}
    html = got.get("contents")
    if html and html.strip():
        out["template"] = save_template(seed["FORM_ID"], html)
        out["template_chars"] = len(html)
        out["template_text"] = fit_preview(reader().body(html).text)
    else:
        out["template"] = None
    out["next"] = ("다음: 본문은 template 파일을 고친 사본을 --body-file 로 준다(입력 칸이 없는 HTML 표다 — 본보기 글을 고쳐 쓴다)" if out["template"]
                   else "다음: 본문 틀이 없는 양식이다 — 본문 HTML 을 지어 --body-file 로 준다")
    if out["many_approvers"] is False:
        out["next"] += ". 이 업무는 결재자가 한 명이다 — 여럿이면 IA037 일반품의서로 쓴다"
    return {k: v for k, v in out.items() if v is not None or k in ("template", "many_approvers")}


TEMPLATE_TEXT = 1500               # form 답에 싣는 틀의 글자 — 무엇이 든 양식인지 보는 몫(통째는 template 파일)


def fit_preview(text: str) -> str:
    """틀의 글자 앞 ``TEMPLATE_TEXT`` 자 — 넘으면 줄임표를 단다."""
    return text if len(text) <= TEMPLATE_TEXT else text[:TEMPLATE_TEXT] + " …"


# ── 문서 읽기 ─────────────────────────────────────────────────────────────
def reader():
    """형제 스킬 company-mail 의 ``visible`` — 본문 HTML 을 글자로 푸는 한 손(숨긴 글 · 스크립트 · 보이지 않는 문자를 걷고 표는 한 행 한 줄)."""
    return ep_command.load("visible", MAIL_SCRIPTS)


def head_of(seed: dict) -> dict:
    """문서 화면의 문서 줄 → 답의 머리 — 열쇠 · 제목 · 상태 · 문서 번호 · 시스템과 업무 · 양식 · 보안 · 공개 · 보존."""
    one = {"id": iams.key_of(seed), "subject": seed.get("SUBJECT"), "state": seed.get("RESULT_STATUS"), "no": seed.get("APPR_DOC_NO"),
           "system": seed.get("LEGACY_NAME_KR"), "job": seed.get("LEGACY_JOB_NAME_KR"), "class": seed.get("APPR_CLASS_NAME_KR"),
           "form": seed.get("FORM_ID"), **defaults_of(seed)}
    return {k: v for k, v in one.items() if v not in (None, "")}


def ai_text(xml: str) -> tuple[str, int]:
    """시스템 연계 문서의 XML 자료 → (「이름: 값」 줄, 숨긴 덩이 수). 값을 든 잎 칸마다 한 줄이고, 그 위 묶음(DS_…)이 바뀌면 머리 줄 하나 ·
    같은 묶음의 줄(row)마다 빈 줄로 가른다(깊이는 안 가린다). PC 주소 칸은 안 낸다. 값은 ``plain_value`` 가 푼다. XML 이 깨졌으면 CDATA 를
    벗긴 글을 통째로 ``visible`` 이 푼다 — HTML 풀이는 CDATA 안의 글을 버린다."""
    try:
        root = ET.fromstring(XML_DECL.sub("", xml, count=1))      # 글자로 읽는다 — 선언의 인코딩(EUC-KR 따위)은 바이트일 때만 뜻이 있다
    except (ET.ParseError, ValueError):
        got = reader().body(CDATA.sub(lambda m: m.group(1), xml))
        return got.text, got.hidden
    lines, hidden, last_row, last_group = [], 0, None, None
    parents = {child: parent for parent in root.iter() for child in parent}
    for cell in root.iter():
        if len(cell) or cell is root:
            continue                                   # 값을 든 잎 칸만
        row = parents[cell]
        group = parents.get(row)
        if group is not None and group is not root and group is not last_group:
            lines += ["", f"[{group.tag}]"]
        elif row is not last_row and last_row is not None:
            lines.append("")
        last_row, last_group = row, group
        value, got = plain_value(cell.text)
        hidden += got
        if value and not cell.tag.endswith(HIDDEN_XML):
            lines.append(f"{cell.tag}: {value}")
    return "\n".join(lines).strip(), hidden


def plain_value(text: str | None) -> tuple[str, int]:
    """남이 쓴 값 하나(XML 자료의 칸 · 결재 의견) → (보이는 글, 숨긴 덩이 수). HTML 조각이면 ``visible`` 이 풀고, 아니면 보이지 않는 문자만 걷는다."""
    value = (text or "").strip()
    if HTML_VALUE.search(value):
        got = reader().body(value)
        return got.text.strip(), got.hidden
    return reader().invisible(value)[0].strip(), 0


def body_of(form_type: str | None, contents: str | None):
    """본문 → (글자, 숨긴 덩이 수). HTML · MIME 은 ``visible`` 이 풀고, AI 는 XML 자료를 줄로 푼다. 비었으면 ("", 0)."""
    if not contents or not contents.strip():
        return "", 0
    if form_type == AI_TYPE or contents.lstrip().startswith("<?xml"):
        text, hidden = ai_text(contents)
        return reader().invisible(text)[0], hidden
    got = reader().body(contents)
    return got.text, got.hidden


def attach_of(got: dict) -> list[dict]:
    """첨부 — 이름 · 확장자 · 크기만(받지 않는다)."""
    out = []
    for a in got.get("attachList") or []:
        one = {"name": first(a, ("ORGINL_FILE_NM", "DISP_FILE_NM", "FILE_NM")), "ext": a.get("FILE_EXT"), "size": a.get("FILE_SIZE"),
               "link": True if (a.get("ATTACH_TYPE") or "").upper() == "LINK" else None}
        out.append({k: v for k, v in one.items() if v not in (None, "")})
    return out


def refs_of(got: dict) -> list[dict]:
    """참조 — 사람마다 이름 · 부서 · 직책 · 상태 · 때 · 참조 의견."""
    return [person(r, ("REFRN_USER_NAME",), "REFRN_COMMENT", "REFRN_DT") for r in got.get("refrnList") or []]


def dist_of(got: dict) -> list[dict]:
    """배포 — 부서 · 사람의 이름과 꼴."""
    kinds = {"DEPARTMENT": "부서", "INDIVIDUAL": "사람"}
    return [{k: v for k, v in (("name", w.get("DISP_NAME")), ("kind", kinds.get(w.get("WDTB_TY"), w.get("WDTB_TY")))) if v}
            for w in got.get("wdtbList") or []]


def related_of(got: dict) -> list[dict]:
    """관련 문서 — 열쇠 · 제목 · 문서 번호 · 상태. 열쇠는 read · open 이 그대로 받는다."""
    out = []
    for r in got.get("refDocList") or []:
        one = {"id": iams.ref_key_of(r),               # 열쇠 칸이 빠진 줄은 id 를 안 짓는다 — 못 여는 열쇠를 안 낸다
               "subject": r.get("SUBJECT"), "no": r.get("APPR_DOC_NO"), "state": r.get("RESULT_STATUS")}
        out.append({k: v for k, v in one.items() if v not in (None, "")})
    return out


def read(app, args) -> dict:
    """read — 문서 하나. 보기 창 화면(_MENU_ACTION_ NONE — 단추를 안 세우는 보기)에서 머리 → 결재선 · 의견 · 참조 · 배포 · 첨부 · 관련 문서
    · 본문(거래 하나) → 본문을 글자로 → 답 크기에 맞춘다."""
    key = iams.doc_of(args.doc)
    seed = seed_of(app.page(iams.at(iams.VIEW, key)), f"문서 {args.doc}")
    got = iams.details(app, seed)
    text, hidden = body_of(seed.get("FORM_TYPE"), got.get("contents"))
    out = {**head_of(seed), "line": line_of(got), "refs": refs_of(got), "dist": dist_of(got), "attach": attach_of(got),
           "related": related_of(got)}
    out = {k: v for k, v in out.items() if v != []}
    if got.get("retireInfo"):
        out["warn"] = " ".join(got["retireInfo"].split())          # 결재선에 퇴직자 · 미사용자가 섰다는 앱의 말
    if hidden:
        out["hidden"] = hidden
    out["length"] = len(text)
    out["next"] = f"다음: 결재 · 반려 · 상신은 open {out['id']} 로 그 문서 창을 띄워 사람이 누른다"
    start = max(0, args.start or 0)
    ep_command.fit_text(out, "body", text, start, READ_FIRST, lambda end: f"다음: read {args.doc} --from {end} 로 본문을 이어 읽는다",
                        OUT_BYTES, indent=1)
    return out


# ── 판 ───────────────────────────────────────────────────────────────────
HANDS = {"forms": forms, "form": form, "box": box, "read": read}


def run(app, args, start) -> dict:
    """명령 하나 — 그 명령의 손에 넘긴다(나눔만)."""
    return HANDS[args.command](app, args)
