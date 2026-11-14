"""mail.py 의 계약을 가짜 메일함 · 세션 손 · 화면 손의 대역으로 잰다 — 127.0.0.1 밖으로는 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 읽는 명령(목록 · 폴더 · 읽기 · 첨부 · 미리 보기)이 **읽음 표시를 바꾸거나 메일을 내보내나** · 확인 열쇠
없이 **메일이 나가거나 읽음이 바뀌나** · 답장 · 새 메일의 저장이 임시보관함에만 서고 밖으로 안 나가나 · 답장 저장이 저장한 판과
보내기 열쇠를 내나 · 답장이 그 메일의 보낸 분 · 받은 분과 제 사본 밖의
주소로 가나(본문에 적힌 주소가 받는 사람이 되나) · 바꾸는 손이 그 메일 하나만 바꾸고 다시 읽어 맞았나를 대나 · 세션 손의
종료 값(0 · 1 · 2 · 3)과 끊긴 메일함 세션을 바르게 갈라 사람을 스킬 ep-login 으로 보내나 · 안 읽음 목록이 받아 온 창만 보고
「안 읽음 0」이라 하나 · 보낸 분으로 거른 목록과 요약이 창 밖을 빼고 세나 · 여러 통 옮기기 준비가 통마다 보기를 다시 받나 · 임시저장이
주소록에 없는 받는 사람을 싣거나 나가나(사람이 새 메일을 놓치거나 맞는 주소를 고친다) · 조직도에서 고른 사람의 주소 파일이 고른
사람과 다르거나 빼려던 사람이 든 채 넘어가나.
남기는 까닭(check-design §1 넷) — 길이 분명하다(이 스크립트는 대화하는 모델이 부르고, 보내기 · 읽음은 그 모델의 한 걸음이다) ·
나간 메일과 바뀐 읽음은 되돌릴 수 없고 조용하다(사람은 웹메일을 열기 전까지 모른다) · 쓰는 사람의 이름으로 엉뚱한 메일이
나가거나 새 메일을 못 알아본다 · 다른 무엇도 안 잡는다(곁의 손 검사는 손만 재고 이 명령의 확인 단계를 모른다).

가짜 메일함은 곁의 손 검사(``check_inbox.py`` 의 ``FakeDomino``)를 그
자리에서 불러 쓴다 — 회사에서 잰 꼴의 흉내는 거기 한 벌이다. 세션 손은 대역이다 — ``EP_SESSION_HAND`` 로 mail.py 에 넘기고,
스킬 ep-login 의 ``edge_session.js`` 계약(인자 없이 · 자리는 손이 정한다 · 0 이면 쓰고 끝 줄에 그 절대 경로 · 1 도구 고장 ·
2 못 붙음, 앞서 받은 파일이 있으면 끝 줄에 그 경로 · 3 로그인 안 됨)만 흉내 내고, 대역이 남기는 세션 파일은 메일함의 쿠키와
다른 사내 호스트의 쿠키를 함께 든다.

돌리는 법::

    python -X utf8 -I check_mail.py

잴 mail.py · inbox.py 는 다 이 파일 곁의 것이다. node 가 있어야 한다.

판정 — 끝 줄이 「통과 N/N」 이면 종료 코드 0, 하나라도 어긋나면 1, 가짜를 못 띄우는 등 재지 못했으면 2.

언제 걷나 — mail.py 가 사라지거나, 바꾸는 손 앞의 확인을 다른 층(도구의 권한 단계 같은 것)이 같은 꼴로 재게 되면.

여기서 못 재는 것 — 실물 세션 손(Edge 에 붙기) · 사내 SSO · 받는 쪽에서 답장이 원래 대화로 묶이나 ·
폴더에만 있는 메일에 읽음으로의 주소가 먹나(가짜는 어느 메일이든 먹는다) · 숨은참조 사본이 받은편지함에 오는 꼴 · 실물 검색의
휴지통 줄 폴더 칸과 범위 all 에 휴지통이 드나 · preview-send · send-draft · 답장 저장과 임시메일 고치기의 화면 쪽(곁의 손이 Edge 에서 실물 화면을 다룬다 — 회사 PC 에서 한 판으로 잰다).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import traceback

HERE = pathlib.Path(__file__).resolve().parent

# 세션 손의 대역 — edge_session.js 의 계약: 인자 없이 불린다 · 자리는 손이 정한다(여기서는 STANDIN_PATH) · 0 이면 그 자리에 쓰고
# 끝 줄에 그 절대 경로를 낸다 · 2 면 앞서 받은 파일이 있을 때만 끝 줄에 그 경로를 낸다. 3 도 있으면 경로를 내 둔다 — 3 에서
# 그 줄을 읽는 쪽을 가려내려고. STANDIN_BAD 면 0 인데 없는 경로를 낸다.
STANDIN = r"""
const fs = require('fs');
const code = Number(process.env.STANDIN_EXIT || '0');
const at = process.env.STANDIN_PATH;
fs.appendFileSync(process.env.STANDIN_LOG, `called args=${process.argv.length - 2}\n`);
console.log('세션 손: 시작');
if (code === 0) {
  fs.writeFileSync(at, JSON.stringify({cookies: JSON.parse(process.env.STANDIN_COOKIES)}));
  console.log(process.env.STANDIN_BAD ? at + '.none' : at);
} else if ((code === 2 || code === 3) && fs.existsSync(at)) {
  console.log(at);
} else if (code === 1) {
  console.error('playwright 를 못 실었다');
}
process.exit(code);
"""


class Unmeasured(Exception):
    """잴 판을 못 세웠다 — 어긋남이 아니라 「못 쟀다」다."""


def load(path: pathlib.Path, name: str, tree: pathlib.Path):
    """곁의 손 검사 파일을 모듈로 싣는다 — 그 파일은 ``sys.argv[1]`` 의 나무를 잰다."""
    saved = sys.argv
    sys.argv = [str(path), str(tree)]
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.argv = saved


if shutil.which("node") is None:
    print("못 쟀다 — node 가 없다")
    sys.exit(2)
WORK = pathlib.Path(tempfile.mkdtemp(prefix="company-mail-check-"))
HAND = WORK / "edge_session.js"
HAND.write_text(STANDIN, encoding="utf-8")
# 임시메일 보내는 손(draft_send.js)의 대역 — 실물은 Edge 가 있어야 돈다. 계약만 흉내 낸다: 끝 줄에 JSON 한 줄 · 종료 값은
# DRAFT_STANDIN_EXIT · 그 줄은 DRAFT_STANDIN_OUT. 메일이 어디 섰나는 이 대역이 안 바꾼다 — 판을 세우는 쪽이 가짜 메일함에서 바꾼다
DRAFT_HAND = WORK / "draft_send.js"
DRAFT_HAND.write_text("console.log(process.env.DRAFT_STANDIN_OUT || '{}'); process.exit(Number(process.env.DRAFT_STANDIN_EXIT || '0'));",
                      encoding="utf-8")
fakes_inbox = load(HERE / "check_inbox.py", "company_mail_fake_inbox", HERE)
sys.path.insert(0, str(HERE))
import mail  # noqa: E402 — 잴 스크립트
EP = mail.load_ep_session()   # 받는 손의 종료 값 — 형제 스킬 ep-login 의 것

U, OWNER, PEER = fakes_inbox.U, fakes_inbox.OWNER, fakes_inbox.PEER
PEER_KEY = fakes_inbox.COLLEAGUE["key"]
COOKIES = WORK / "session.json"
CALLS = WORK / "standin.log"


def session_cookies(value: str) -> list[dict]:
    """대역이 남길 쿠키 — 메일함(127.0.0.1)의 것과, 같은 이름의 다른 사내 호스트 쿠키 둘."""
    name = fakes_inbox.COOKIE[0]
    return [{"name": name, "value": "other-app", "domain": ".posco.net", "path": "/", "expires": -1},
            {"name": "JSESSIONID", "value": "ecm", "domain": "swpecm.posco.net", "path": "/", "expires": -1},
            {"name": name, "value": value, "domain": "127.0.0.1", "path": "/", "expires": -1}]


@contextlib.contextmanager
def stage(*, exit_code: int = 0, cookie: str = fakes_inbox.COOKIE[1], left_over: str | None = None,
          bad_path: bool = False, **fake):
    """가짜 메일함 · 세션 대역 · 화면 손 대역을 세운다. 내는 것 — (메일함 흉내, 명령을 부르는 손).

    ``left_over`` 를 주면 앞 판의 세션 파일을 그 쿠키 값으로 남겨 둔 채 시작한다 — 메일함의 값이면 아직 받아 주는 세션,
    다른 값이면 메일함이 거절하는 세션이다. ``MAILBOX_COOKIES`` 는 없는 자리를 가리킨다 — 스크립트가 그 값에 기대면 진다.
    """
    try:
        box = fakes_inbox.FakeDomino(**fake)
    except Exception as exc:  # noqa: BLE001 — 무엇으로 지든 판을 못 세운 것이다
        raise Unmeasured(f"가짜를 못 띄웠다: {exc}") from exc
    COOKIES.unlink(missing_ok=True)
    if left_over is not None:
        COOKIES.write_text(json.dumps({"cookies": session_cookies(left_over)}), encoding="utf-8")
    CALLS.write_text("", encoding="utf-8")
    env = {"MAILBOX_URL": box.url, "MAILBOX_COOKIES": str(WORK / "decoy" / "not-here.json"),
           "MAIL_ORG_CACHE_DIR": str(WORK / "org"), "NODE_PATH": str(WORK),
           "DRAFT_SEND_HAND": str(DRAFT_HAND),   # 판마다 화면 손은 대역이다 — 저장 뒤 창 띄우기가 이 PC 의 Edge 에 닿지 않게
           "EP_SESSION_HAND": str(HAND), "STANDIN_EXIT": str(exit_code), "STANDIN_LOG": str(CALLS), "STANDIN_PATH": str(COOKIES),
           "STANDIN_BAD": "1" if bad_path else "", "STANDIN_COOKIES": json.dumps(session_cookies(cookie))}
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)

    def run(*argv) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            try:
                code = mail.main(list(argv))
            except SystemExit as exc:   # argparse 가 모르는 명령 · 인자를 거절했다 — 그 판의 종료 값으로 읽는다
                code = exc.code if isinstance(exc.code, int) else 2
        return code, out.getvalue()

    try:
        yield box, run
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        box.close()


def body_file(text: str) -> str:
    path = WORK / "reply.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def key(output: str) -> str:
    line = next((x for x in output.splitlines() if x.startswith("확인 열쇠: ")), "")
    assert line, f"미리 보기가 확인 열쇠를 안 냈다:\n{output}"
    return line.split(": ", 1)[1].strip()


def changing(paths) -> list[str]:
    return [p for p in paths if any(m in p.lower() for m in ("opendocument", "editdocument", "ag_read_cancel"))]


# ── 읽는 명령은 아무것도 안 바꾼다 ───────────────────────────────────────

def check_reading_commands_change_nothing():
    C = fakes_inbox.COMPANY
    with stage() as (box, run):
        box.mails[U["ecm"]].attachments += ("보고.docx", "평문.pdf")
        box.mails[U["ecm"]].files.update({"보고.docx": b"DRMONE\x00\x01wrapped", "평문.pdf": b"%PDF-1.7\n"})
        before = box.unread()
        steps = [("session",), ("folders",), ("list",), ("list", "--unread"), ("list", "--sent"), ("list", "--drafts"),
                 ("list", "--folder", fakes_inbox.FOLDER_CHILD), ("list", "--from", PEER[0]), ("summary",),
                 ("summary", "--folder", fakes_inbox.FOLDER_TOP), ("search", "시험"), ("search", "초안", "--field", "body"),
                 ("read", U["draft"]), ("read", U["draft"], "--folder", mail.DRAFTS),
                 ("read", U["alone"]), ("read", U["f_child"]), ("read", U["ecm"]),
                 ("attachment", U["ecm"], "--save", "all", "--out", str(WORK / "got")),
                 ("preview-reply", U["alone"], "all", "--body-file", body_file("확인했습니다.")),
                 ("preview-mark", U["alone"], "--read"),
                 ("people", PEER[1]), ("people", PEER[0], "--exact"), ("org", "소재사업부", "--company", C), ("org", "--tree", "--company", C),
                 ("org", "소재", "--grade", "차장", "--company", C), ("org-groups", "jobtitle", "--company", C),
                 ("org-groups", "jobtitle", "일반", "--company", C),
                 ("people", PEER[1], "--raw")]
        for argv in steps:
            code, out = run(*argv)
            assert code == 0, f"{argv} 가 종료 값 {code}:\n{out}"
        assert box.unread() == before, f"읽기만 했는데 안 읽음이 바뀌었다: {sorted(before ^ box.unread())}"
        assert not box.changes and not changing(box.paths), f"메일함을 바꾸는 주소를 불렀다: {changing(box.paths)}"
        assert not box.sent_now, f"읽기만 했는데 메일이 나갔다: {box.sent_now}"


def check_attachments_point_to_the_right_reader():
    with stage() as (box, run):
        box.mails[U["ecm"]].attachments += ("보고.docx", "평문.pdf")
        box.mails[U["ecm"]].files.update({"보고.docx": b"DRMONE\x00\x01wrapped", "평문.pdf": b"%PDF-1.7\n"})
        code, out = run("attachment", U["ecm"], "--save", "all", "--out", str(WORK / "got"))
        assert code == 0, out
        lines = out.splitlines()
        key = fakes_inbox.ECM_KEY
        assert any("분기 실적.pptx" in x and f"read {key}" in x and "company-ecm" in x for x in lines), \
            f"ECM 첨부의 열쇠를 company-ecm 의 read 로 안 넘겼다:\n{out}"
        assert not any(p.name.startswith("분기 실적") for p in (WORK / "got").iterdir()), "ECM 쪽지를 파일로 남겼다"
        assert any("보고.docx" in x and "drm-office-read" in x for x in lines), f"감긴 첨부를 drm-office-read 로 안 보냈다:\n{out}"
        assert any("평문.pdf" in x and "평문" in x and "drm-office-read" not in x for x in lines), out
        assert (WORK / "got" / "보고.docx").read_bytes() == b"DRMONE\x00\x01wrapped", "받은 첨부 바이트가 다르다"
        code, out = run("attachment", U["ecm"], "--save", "1")
        assert code == 0 and f"read {key}" in out and "받았다" not in out, f"ECM 첨부 하나를 고른 판이 열쇠만 내지 않았다:\n{out}"
        code, out = run("attachment", U["ecm"])
        assert code == 0 and "--save 1" in out and "company-ecm" in out, f"목록이 ECM 첨부의 열쇠 꺼내는 길을 안 댔다:\n{out}"


# ── 찾기 — 메일함 주소는 세션이 대고 · 검색은 임시보관함까지 ─────────────────

def check_mailbox_comes_from_the_session_not_the_person():
    """메일함 주소는 세션이 댄다 — 사람에게 안 묻고 · 같은 로그인 동안은 받아 둔 것을 써 서버에 다시 안 묻고 · 다른 로그인의 지문에는 안 낸다 ·
    끊긴 세션은 ep-login 으로 보낸다."""
    with stage() as (box, run):
        os.environ.pop("MAILBOX_URL", None)
        os.environ["MAIL_SERVER"] = box.url[:-len(fakes_inbox.DB)]
        try:
            code, out = run("session")
            assert code == 0 and box.url in out, f"세션으로 메일함 주소를 안 받았다:\n{out}"
            before = len(box.paths)
            code, out = run("list")
            assert code == 0 and box.paths[before:], out
            assert "/" not in box.paths[before:], f"같은 세션인데 메일함 주소를 서버에 다시 물었다: {box.paths[before:]}"
            server, other = os.environ["MAIL_SERVER"], WORK / "other-session.json"
            other.write_text(json.dumps({"cookies": session_cookies("someone-else")}), encoding="utf-8")
            assert mail.kept_mailbox(mail.session_mark(server, COOKIES)) == box.url, "받아 둔 주소가 그 세션의 지문으로 안 선다"
            assert not mail.kept_mailbox(mail.session_mark(server, other)), "다른 로그인의 지문에 받아 둔 메일함 주소를 냈다"
            box.session = "login"
            code, out = run("list")
            assert code == mail.EXIT_SESSION and "ep-login" in out, f"끊긴 세션의 첫 화면을 ep-login 으로 안 보냈다:\n{out}"
        finally:
            os.environ.pop("MAIL_SERVER", None)


def check_search_all_includes_drafts_and_points_to_read():
    with stage() as (box, run):
        code, out = run("search", "시험")
        assert code == 0, out
        rows = [x for x in out.splitlines() if x.startswith("[")]
        unids = [next(w for w in x.split(" · ") if len(w.split()[0]) == 32).split()[0] for x in rows]
        assert unids == [U["alone"], U["f_child"], U["draft"]], f"전체 검색이 받은편지함 · 폴더 · 임시보관함을 안 들었다:\n{out}"
        assert f'--folder "{fakes_inbox.FOLDER_CHILD}"' in rows[1] and f'--folder "{mail.DRAFTS}"' in rows[2], \
            f"하위 폴더 줄이 검색 손의 끝 이름이 아니라 폴더 경로를 안 댔다:\n{out}"
        assert "all 2건" in out and "임시보관함 1건" in out, out
        for line, unid in zip(rows, unids):    # 줄 끝의 안내를 그대로 붙여 읽힌다 — 첫 판(--scan 1) 밖의 옛 메일도
            hint = line.split(unid, 1)[1].strip()
            folder = ["--folder", hint.split('"')[1]] if hint else []
            code, got = run("read", unid, *folder, "--scan", "1")
            assert code == 0 and "--- 본문 시작" in got, f"검색 줄의 안내대로 read 가 못 열었다({unid} {folder}):\n{got}"
        code, out = run("search", "시험", "--in", "inbox")
        assert code == 0 and U["f_child"] not in out and U["draft"] not in out, out
        code, out = run("search", "시험", "--count", "1")
        assert "--page 2" in out, f"다음 쪽이 있는데 안 알렸다:\n{out}"
        code, out = run("read", U["draft"], "--folder", mail.DRAFTS)
        assert code == 0 and "초안 본문" in out and "임시보관함" in out, out
        # 받은편지함 · 보낸편지함 줄은 웹메일의 시스템 표지(${INBOX} · ${SENT})가 아니라 그 편지함 이름을 들고, 보낸 메일도 안내대로 열린다
        code, out = run("search", "주간")
        assert code == 0 and "${" not in out, f"시스템 표지를 날것으로 냈다:\n{out}"
        line = next(x for x in out.splitlines() if U["sent_1"] in x)
        assert "· 보낸편지함 ·" in line and f'--folder "{mail.SENT}"' in line, line
        code, got = run("read", U["sent_1"], "--folder", mail.SENT, "--scan", "1")
        assert code == 0 and "받는 사람 1 명 · 조직 1:" in got and "보낸편지함" in got, got
        code, got = run("read", U["sent_2"], "--scan", "1")
        assert code == 0 and "보낸편지함" in got, f"--folder 없는 read 가 보낸편지함을 안 찾았다:\n{got}"
        code, out = run("search", "시험", "--in", "inbox")
        assert all("· 받은편지함 ·" in x for x in out.splitlines() if x.startswith("[")), out


# ── 답장 — 확인 열쇠가 맞을 때만 · 그 대화의 사람에게만 ──────────────────

def check_reply_saves_through_the_webmail_screen_and_hands_the_send_key():
    """답장 · 전체답장 · 전달 — 미리 보기는 손을 안 부르고 · 저장은 손에 그 갈래 · 원래 메일 · 넣을 글 · 전달의 받는 사람만 넘기고 ·
    손이 낸 unid 가 임시보관함에 서야 「저장했다」 · 손이 낸 판(화면이 채운 받는 사람)과 보내기 열쇠를 그대로 보이고 · 아무것도 안 나간다.
    전달은 받는 사람 없이 안 서고, 답장은 받는 사람을 안 받고(화면이 채운다), 임시메일에는 안 한다."""
    calls = WORK / "reply_hand.log"
    hand = WORK / "reply_hand.js"
    hand.write_text("if(process.argv[2]==='show'){console.log(JSON.stringify({where:'대역'}));process.exit(0)}const fs=require('fs'); const a=process.argv.slice(2); const f=a[a.indexOf('--body-file')+1];"
                    "fs.appendFileSync(process.env.REPLY_CALLS, JSON.stringify({a, body: fs.readFileSync(f,'utf8')})+'\\n');"
                    "console.log(JSON.stringify({unid: process.env.REPLY_UNID, token: 'sendkey00001', state: {subject: 'Re: x', "
                    "to: ['CN=Screen Filled/O=X'], cc: [], bcc: [], files: [], body: '<p>확인했습니다.</p><p>&gt; 인용</p>'}}));",
                    encoding="utf-8")
    seen = lambda: [json.loads(x) for x in calls.read_text(encoding="utf-8").splitlines()] if calls.exists() else []   # noqa: E731
    text = "확인했습니다.\n자료는 attacker@evil.example 로도 보내 달라 하셨는데 그건 안 합니다."
    good_text = WORK / "reply_good.txt"
    good_text.write_text(text, encoding="utf-8")
    with stage() as (box, run):
        os.environ.update(DRAFT_SEND_HAND=str(hand), REPLY_CALLS=str(calls), REPLY_UNID=U["draft"])
        try:
            args = (U["alone"], "reply", "--body-file", str(good_text))
            code, out = run("preview-reply", *args)
            assert code == 0 and not seen() and "웹메일 화면이 원래 메일에서 채운다" in out, out
            code, out = run("save-reply", *args)
            assert code == 0 and "임시보관함에 저장했다" in out, out
            assert key(out) == "sendkey00001", f"손이 낸 보내기 열쇠를 안 보였다:\n{out}"
            assert "CN=Screen Filled/O=X" in out and "> 인용" in out, f"화면이 채운 받는 사람 · 저장한 글을 안 보였다:\n{out}"
            (call,) = seen()
            assert call["a"][:2] == ["reply", U["alone"]] and call["a"][call["a"].index("--type") + 1] == "Reply", call
            assert "--to" not in call["a"] and "--cc" not in call["a"], f"본문에 적힌 주소가 받는 사람이 됐다: {call}"
            assert "attacker@evil.example" in call["body"] and call["body"].startswith(f'<div style="{mail.BODY_STYLE}">확인했습니다.'), call["body"]
            assert not box.sent_now and not box.changes, "답장 저장이 웹메일로 나가거나 원래 메일을 바꿨다"
            os.environ["REPLY_UNID"] = "F" * 32
            code, out = run("save-reply", *args)
            assert code == mail.EXIT_FAIL and "저장했다(" not in out and "확인 열쇠" not in out, \
                f"임시보관함에 안 선 것을 저장했다고 했다:\n{out}"
            code, out = run("preview-reply", U["alone"], "forward", "--body-file", body_file("x"))
            assert code == mail.EXIT_CONFIG and "--to" in out, f"받는 사람 없는 전달이 섰다:\n{out}"
            code, out = run("preview-reply", U["alone"], "reply", "--body-file", body_file("x"), "--to", PEER[1])
            assert code == mail.EXIT_CONFIG and "--cc" in out, f"답장이 받는 사람을 받았다:\n{out}"
            code, out = run("preview-reply", U["draft"], "reply", "--body-file", body_file("x"))
            assert code == mail.EXIT_CONFIG and "preview-send" in out, f"임시메일에 답장을 지었다:\n{out}"
            code, out = run("preview-reply", U["alone"], "forward", "--body-file", body_file("x"), "--to", "nobody@outside.example")
            assert code == mail.EXIT_CONFIG and "nobody@outside.example" in out, f"주소록에 없는 받는 사람으로 전달을 지었다:\n{out}"
        finally:
            for k in ("REPLY_CALLS", "REPLY_UNID"):
                os.environ.pop(k, None)
            os.environ["DRAFT_SEND_HAND"] = str(DRAFT_HAND)   # 판의 대역으로 — 지우면 뒤의 저장이 진짜 손을 부른다


def check_new_mail_goes_only_through_the_drafts():
    """새 메일 미리 보기 — 저장 · 내보내기 없이 주소 파일의 같은 주소 · 주석을 걸러 받는 사람을 다
    이름과 보이고 · 받는 사람이 없으면 안 선다."""
    team = WORK / "team.txt"
    team.write_text(f"{PEER[1]}\n# 주석 줄\n{PEER[1]}\n", encoding="utf-8")
    with stage() as (box, run):
        args = ("--subject", "주간 회의 안내", "--body-file", body_file("금요일 10시입니다."), "--to-file", str(team),
                "--company", fakes_inbox.COMPANY)
        code, out = run("preview-draft", *args)
        assert code == 0 and not box.saved_forms and not box.sent_now, out
        assert "받는 사람 1 명" in out, f"주소 파일의 같은 주소 · 주석을 못 걸렀다:\n{out}"
        assert f"{PEER[0]} · {PEER[1]}" in out, f"받는 사람에 주소록 이름이 안 붙었다:\n{out}"
        code, out = run("preview-draft", "--subject", "x", "--body-file", body_file("x"))
        assert code == mail.EXIT_CONFIG, f"받는 사람 없이 미리 보기가 섰다:\n{out}"


def check_draft_attachment_is_shown_and_uploaded():
    """첨부 — 미리 보기 · 저장한 판에 이름이 서고 · 저장할 때의 그 파일 바이트가 올라간다."""
    sheet = WORK / "보고서.html"
    sheet.write_text("<p>첫 판</p>", encoding="utf-8")
    with stage() as (box, run):
        args = ("--subject", "주간 보고", "--body-file", body_file("보고서를 붙입니다."), "--attach", str(sheet), "--to", PEER[1])
        code, out = run("preview-draft", *args)
        assert code == 0 and not box.saved_forms, out
        assert "첨부 1 개" in out and "보고서.html" in out, f"첨부 이름을 미리 보기에 안 세웠다:\n{out}"
        code, out = run("save-draft", *args)
        assert code == 0 and len(box.saved_forms) == 1 and not box.sent_now, out
        assert "첨부 1 개" in out and "보고서.html" in out, f"저장한 판에 첨부 이름을 안 세웠다:\n{out}"
        assert box.saved_forms[0]["am_attachment"] == "보고서.html", box.saved_forms[0]
        assert sheet.read_bytes() in box.uploads[-1][1], "올라간 첨부가 그 파일의 바이트가 아니다"


def check_draft_recipients_come_from_the_kept_org_chart():
    """임시메일의 받는 사람 — 받아 둔 조직도가 있으면 주소록에 안 묻고 거기서 잇는다 · 없으면 조직도를 새로 받지 않고 주소록에 묻는다."""
    shutil.rmtree(WORK / "org", ignore_errors=True)
    asked = lambda box, before: [p for p in box.paths[before:] if "ag_org_search_json" in p]   # noqa: E731
    walked = lambda box, before: [p for p in box.paths[before:] if "ag_tree_" in p]   # noqa: E731
    with stage() as (box, run):
        args = ("--subject", "x", "--body-file", body_file("x"), "--to", PEER[1], "--company", fakes_inbox.COMPANY)
        before = len(box.paths)
        code, out = run("preview-draft", *args)
        assert code == 0 and asked(box, before) and not walked(box, before), \
            f"받아 둔 판이 없을 때 주소록에 안 묻거나 조직도를 받으러 갔다:\n{out}"
        code, out = run("org", "--company", fakes_inbox.COMPANY)
        assert code == 0, out
        before = len(box.paths)
        code, out = run("preview-draft", *args)
        assert code == 0 and PEER[0] in out, out
        assert not asked(box, before), f"받아 둔 조직도에 있는 주소를 주소록에 또 물었다: {asked(box, before)}"


def check_org_lists_the_department_alone_unless_asked():
    """조직 하나를 물으면 그 부서에 바로 든 사람만 · --sub 를 줄 때만 하위 조직까지."""
    with stage() as (_, run):
        C = fakes_inbox.COMPANY
        code, out = run("org", "소재사업부", "--company", C)
        assert code == 0 and fakes_inbox.OWNER["email"] in out and PEER[1] not in out, f"하위 조직 사람이 기본으로 들었다:\n{out}"
        code, out = run("org", "소재사업부", "--sub", "--company", C)
        assert code == 0 and PEER[1] in out and fakes_inbox.OWNER["email"] in out, f"--sub 가 하위 조직을 안 넣었다:\n{out}"


def check_org_hands_the_picked_people_as_an_address_file():
    """조직도에서 고른 사람의 주소 파일 — 고른 사람의 주소만 들고 뺀 사람은 안 든다 · 명단에 없는 사람을 빼라면 멈춘다(못 뺀 채
    넘기면 빼려던 사람에게 메일이 간다)."""
    with stage() as (_, run):
        C = fakes_inbox.COMPANY
        to_file = WORK / "org-to.txt"
        code, out = run("org", "소재사업부", "--sub", "--except", PEER[1], "--emails-file", str(to_file), "--company", C)
        assert code == 0, out
        lines = [x for x in to_file.read_text(encoding="utf-8").splitlines() if x and not x.startswith("#")]
        assert fakes_inbox.OWNER["email"] in lines and PEER[1] not in lines, f"주소 파일이 고른 사람과 다르다: {lines}\n{out}"
        listed = [x for x in out.splitlines() if re.match(r"\d+\. ", x)]
        assert len(listed) == len(lines) and all(a in out for a in lines), f"주소 파일과 보인 명단이 다르다: {lines}\n{out}"
        code, out = run("org", "소재사업부", "--sub", "--except", "nobody@example.com", "--company", C)
        assert code != 0 and "명단에 없다" in out, f"명단에 없는 사람을 빼라는데 멈추지 않았다:\n{out}"
        code, out = run("org", "소재사업부", "--sub", "--match", fakes_inbox.OWNER["user_name"], "--emails-file", str(to_file),
                        "--company", C)
        lines = [x for x in to_file.read_text(encoding="utf-8").splitlines() if x and not x.startswith("#")]
        assert code == 0 and lines == [fakes_inbox.OWNER["email"]], f"--match 가 그 말이 든 사람만 고르지 않았다: {lines}\n{out}"


def check_long_bodies_fit_the_tool_limit_and_keep_the_send_key():
    """긴 본문 — 읽기는 쪽마다 몫(바이트) 밑이고 이으면 빠짐도 겹침도 없다 · 긴 인용이 든 판을 보여도 뒤에 찍는 확인 열쇠가 대화
    도구의 출력 한도(30 KB · 잰 것) 안에 든다(열쇠가 잘리면 보내기가 그 자리에서 안 선다)."""
    text = "".join(f"{n} 째 줄이다. 납기와 수량을 다시 확인한다.\n" for n in range(3000))
    got, start = "", 0
    for _ in range(200):
        end = mail.fit_body(text, start, mail.DEFAULT_MAX_CHARS, 20000)
        assert end > start and len(text[start:end].encode("utf-8")) <= 20000, f"한 쪽이 몫을 넘었다: {start}–{end}"
        got, start = got + text[start:end], end
        if start >= len(text):
            break
    assert got == text, "쪽을 이은 본문이 원래 본문과 다르다"
    state = {"to": [f"CN=사람{n}/OU=X/O=Y" for n in range(60)], "cc": [], "bcc": [], "subject": "Re: 긴 인용",
             "body": "<p>" + text.replace("\n", "<br>") + "</p>", "files": ["a.xlsx:20480"]}
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        mail.show_draft_state(state, mail.load_inbox(), fakes_inbox.COMPANY)
        print("확인 열쇠: 0123456789abcdef")
    shown = out.getvalue()
    assert len(shown.encode("utf-8")) < 30000 - 1000, f"긴 인용이 든 판이 {len(shown.encode('utf-8'))} 바이트다 — 열쇠 뒤의 줄이 잘린다"
    assert "그 뒤는" in shown, f"본문을 끊고도 끊었다고 말하지 않았다:\n{shown[-300:]}"


def check_same_as_last_time_keeps_the_org_as_one_org():
    """「지난번과 같이」 — recipients 가 보낸 메일의 칸마다 주소 파일을 쓰고, save-draft 가 그 파일로 사람은 사람으로 · 조직은 부서원으로
    안 풀고 조직 하나로(SendTo 에 부서 코드) 칸을 그대로 싣는다. 틀리면 다른 사람에게 메일이 간다(넷 가운데 「조용히 넓게」)."""
    C, dept = fakes_inbox.COMPANY, "dept_n320_00(07)@nuri.example"
    files = {f: WORK / f"last-{f}.txt" for f in ("to", "cc", "bcc")}
    with stage() as (box, run):
        code, out = run("recipients", U["sent_1"], *[x for f, p in files.items() for x in (f"--{f}-file", str(p))])
        assert code == 0 and "소재시험그룹(조직)" in out and "숨은참조 1 명" in out, out
        lines = {f: [x for x in p.read_text(encoding="utf-8").splitlines() if x and not x.startswith("#")] for f, p in files.items()}
        assert lines == {"to": [PEER[1], dept], "cc": [], "bcc": [fakes_inbox.TRAINEE["email"]]}, lines
        # 사외 주소는 임시보관함 길이 못 싣는다 — 파일에 주석으로만 들고 답이 그 주소를 댄다. 세 칸의 파일을 그대로 줘도 저장이 선다
        assert fakes_inbox.EXTERNAL in files["cc"].read_text(encoding="utf-8") and fakes_inbox.EXTERNAL in out, \
            f"사외 주소를 말없이 버렸다:\n{out}"
        code, out = run("save-draft", "--subject", "x", "--body-file", body_file("x"), "--to-file", str(files["to"]),
                        "--cc-file", str(files["cc"]), "--bcc-file", str(files["bcc"]), "--company", C)
        assert code == 0 and len(box.saved_forms) == 1 and not box.sent_now, out
        form = box.saved_forms[0]
        assert form["SendTo"] == f"{PEER_KEY}; n320_00(07)", form["SendTo"]
        assert form["BlindCopyTo"] == fakes_inbox.TRAINEE["key"], form["BlindCopyTo"]
        assert fakes_inbox.HOMONYM["key"] not in form["SendTo"], "조직을 부서원으로 풀었다"
        assert "소재시험그룹(조직)" in out, out


def check_draft_saves_to_the_drafts_and_never_sends():
    """임시저장 — 미리 보기는 저장 안 하고 · 주소록에 없는 받는 사람이면 저장 안 하고 · 저장은 임시보관함에만 들고 보내기 칸으로
    안 나가고 · 저장한 명단을 다 보이고 보내기는 preview-send 로 이른다."""
    with stage() as (box, run):
        code, out = run("preview-draft", "--subject", "x", "--body-file", body_file("x"), "--to", "nobody@outside.example")
        assert code == mail.EXIT_CONFIG and "nobody@outside.example" in out, f"주소록에 없는 받는 사람을 받았다:\n{out}"
        args = ("--subject", "주간 보고", "--body-file", body_file("임시저장 시험"), "--to", PEER[1])
        code, out = run("preview-draft", *args)
        assert code == 0 and not box.saved_forms, f"미리 보기가 저장했다:\n{out}"
        assert PEER[0] in out, f"받는 사람 이름을 안 보였다:\n{out}"
        code, out = run("save-draft", "--subject", "x", "--body-file", body_file("x"), "--to", "nobody@outside.example")
        assert code == mail.EXIT_CONFIG and not box.saved_forms, f"주소록에 없는 받는 사람으로 저장했다:\n{out}"
        code, out = run("save-draft", *args)
        assert code == 0 and len(box.saved_forms) == 1, out
        assert PEER[0] in out and "preview-send" in out and "확인 열쇠" not in out, f"저장한 명단 · 다음 걸음을 안 보였다:\n{out}"
        assert box.saved_forms[0]["SaveAgent"] == "wSave" and not box.sent_now, "임시저장이 나갔다"
        assert any(k == "draft" for k, _ in box.changes), box.changes


def check_draft_send_is_judged_by_where_the_mail_stands():
    """임시메일 보내기의 「보냈다」는 손의 말이 아니라 메일이 선 자리다 — 손이 「눌렀다」 해도 보낸편지함에 없으면 「보냈다」를 안 내고 ·
    손이 멈췄다 해도 보낸편지함에 섰으면 「나갔다 · 다시 보내지 않는다」를 내고 · 임시보관함 밖의 unid 는 손을 부르지도 않는다."""
    pressed = json.dumps({"pressed": True, "where": "대역", "asked": [], "subject": "s", "to": 1, "cc": 0, "bcc": 0})
    with stage() as (box, run):
        os.environ.update(DRAFT_SEND_HAND=str(DRAFT_HAND), DRAFT_STANDIN_EXIT="0", DRAFT_STANDIN_OUT=pressed)
        try:
            code, out = run("send-draft", U["draft"], "--confirm", "k")
            assert code == mail.EXIT_FAIL and "보냈다(" not in out, f"보낸편지함에 없는데 보냈다고 했다:\n{out}"
            draft = box.mails.pop(U["draft"])
            box.sent.append(fakes_inbox.FakeSent(draft.unid, draft.subject, draft.stamp, PEER[1]))
            box.mails[draft.unid] = draft
            os.environ.update(DRAFT_STANDIN_EXIT="5", DRAFT_STANDIN_OUT=json.dumps({"error": "다른 물음"}))
            code, out = run("send-draft", U["draft"], "--confirm", "k")
            assert code == mail.EXIT_FAIL and "다시 보내지 않는다" in out, f"나간 메일을 안 나갔다고 했다:\n{out}"
            os.environ.update(DRAFT_STANDIN_EXIT="0", DRAFT_STANDIN_OUT=pressed)
            code, out = run("preview-send", U["sent_1"])
            assert code == mail.EXIT_CONFIG and "임시보관함에 그 메일이 없다" in out, f"임시메일 아닌 것을 열려 했다:\n{out}"
        finally:
            for k in ("DRAFT_STANDIN_EXIT", "DRAFT_STANDIN_OUT"):
                os.environ.pop(k, None)
            os.environ["DRAFT_SEND_HAND"] = str(DRAFT_HAND)   # 판의 대역으로 — 지우면 뒤의 저장이 진짜 손을 부른다


def check_revise_touches_only_the_given_parts_of_a_draft():
    """임시메일 고치기 — 임시보관함 밖의 메일 · 고칠 것 없는 부름 · 주소록에 없는 받는 사람이면 손을 안 부르고 · 손에는 준 칸만 넘기고
    (빈 참조는 빈 값으로) · 손이 낸 고친 판과 보내기 열쇠를 보이고 · 아무것도 안 나가고 다른 메일을 안 바꾼다. 새 메일의 저장은 넣은
    글에 표지를 달아 이 고치기가 그 자리를 찾게 한다."""
    calls = WORK / "revise_hand.log"
    hand = WORK / "revise_hand.js"
    hand.write_text("if(process.argv[2]==='show'){console.log(JSON.stringify({where:'대역'}));process.exit(0)}const fs=require('fs'); const a=process.argv.slice(2); const i=a.indexOf('--body-file');"
                    "fs.appendFileSync(process.env.REVISE_CALLS, JSON.stringify({a, body: i<0 ? null : fs.readFileSync(a[i+1],'utf8')})+'\\n');"
                    "console.log(JSON.stringify({unid: a[1], where: '대역', token: 'revisekey001', state: {subject: '고친 제목', "
                    "to: ['CN=Kept/O=X'], cc: [], bcc: [], files: [], body: '<p>고친 글</p>'}}));", encoding="utf-8")
    calls.unlink(missing_ok=True)
    seen = lambda: [json.loads(x) for x in calls.read_text(encoding="utf-8").splitlines()] if calls.exists() else []   # noqa: E731
    with stage() as (box, run):
        os.environ.update(DRAFT_SEND_HAND=str(hand), REVISE_CALLS=str(calls))
        try:
            code, out = run("revise-draft", U["alone"], "--subject", "x")
            assert code == mail.EXIT_CONFIG and not seen(), f"임시보관함 밖의 메일을 고치려 했다:\n{out}"
            code, out = run("revise-draft", U["draft"])
            assert code == mail.EXIT_CONFIG and not seen(), f"고칠 것 없이 손을 불렀다:\n{out}"
            code, out = run("revise-draft", U["draft"], "--to", "nobody@outside.example")
            assert code == mail.EXIT_CONFIG and "nobody@outside.example" in out and not seen(), f"주소록에 없는 받는 사람을 받았다:\n{out}"
            code, out = run("revise-draft", U["draft"], "--subject", "고친 제목")
            assert code == 0 and "고쳐 저장했다" in out and key(out) == "revisekey001" and "CN=Kept/O=X" in out, out
            assert seen()[-1]["a"] == ["revise", U["draft"], "--subject", "고친 제목"], f"안 준 칸을 손에 넘겼다: {seen()[-1]}"
            code, out = run("revise-draft", U["draft"], "--body-file", body_file("고친 글"), "--cc", "")
            assert code == 0, out
            call = seen()[-1]
            assert call["a"][2:4] == ["--cc", ""] and "--to" not in call["a"] and "--subject" not in call["a"], call
            assert call["body"] == f'<div style="{mail.BODY_STYLE}">고친 글</div>', call
            assert not box.sent_now and not box.changes and not box.saved_forms, "임시메일 고치기가 메일을 내보내거나 다른 것을 바꿨다"
        finally:
            for k in ("REVISE_CALLS",):
                os.environ.pop(k, None)
            os.environ["DRAFT_SEND_HAND"] = str(DRAFT_HAND)   # 판의 대역으로 — 지우면 뒤의 저장이 진짜 손을 부른다
        code, out = run("save-draft", "--subject", "x", "--body-file", body_file("본문"), "--to", PEER[1])
        assert code == 0 and f'<div id="{mail.TEXT_MARK}' in box.saved_forms[0]["MIMEBody"], \
            f"새 메일의 넣은 글에 표지를 안 달았다: {box.saved_forms and box.saved_forms[0]['MIMEBody'][-200:]}"
        page = "<html><head><style>body > table {width: 600px}</style></head><body><table><tr><td>지면</td></tr></table></body></html>"
        assert mail.marked_text(page) == page, "문서 꼴 HTML 의 body 를 감쌌다 — 그 문서의 배치 규칙이 어긋난다"


def check_unread_list_looks_past_the_window():
    """안 읽음 목록 — 받아 온 창 밖의 안 읽음도 세고 훑은 줄 수를 댄다 · 보낸편지함 · 임시보관함과는 안 받는다."""
    with stage() as (box, run):
        mails = box.in_inbox()
        assert not mails[0].unread, "대역의 가장 새 메일이 안 읽음이라 창 하나로도 맞아 이 판이 안 문다"
        want = [m.unid for m in mails if m.unread]
        code, out = run("list", "--unread", "--count", "1")
        assert code == 0, out
        said = re.search(r"(\d+)통을 훑어 안 읽음 (\d+)통", out)
        assert said and "끝까지" in out and said.groups() == (str(len(mails)), str(len(want))), \
            f"받은편지함 {len(mails)}통 · 안 읽음 {len(want)}통을 창 하나만 보고 말했다:\n{out}"
        rows = [x for x in out.splitlines() if x.startswith("[")]
        assert len(rows) == 1 and want[0] in rows[0], f"가장 새 안 읽음 한 통을 안 보였다:\n{out}"
        for flag in ("--drafts", "--sent"):
            for sieve in (("--unread",), ("--from", PEER[0])):
                code, out = run("list", flag, *sieve)
                assert code == mail.EXIT_CONFIG, f"{flag} 에 준 {sieve[0]} 를 말없이 버렸다:\n{out}"


def check_sender_counts_cover_the_whole_view():
    """보낸 분으로 거르기 · 요약 — 받아 온 창 밖까지 세고, 요약의 통 수가 그 보낸 분의 메일 수와 같다(틀린 수로 정리안이 선다)."""
    with stage() as (box, run):
        mails = box.in_inbox()
        peers = [m for m in mails if PEER[1] in m.sender]
        assert mails[1:] and 1 < len(peers) < len(mails), "대역의 받은편지함이 한 사람 것뿐이라 이 판이 안 문다"
        code, out = run("list", "--from", PEER[1].split("@")[0].upper(), "--count", "1")
        assert code == 0 and f"{len(mails)}통을 훑어" in out and f"{len(peers)}통" in out.splitlines()[-1], \
            f"보낸 분 {len(peers)}통을 창 하나만 보고 말했다:\n{out}"
        assert len([x for x in out.splitlines() if x.startswith("[")]) == 1, out
        code, out = run("summary")
        assert code == 0 and f"끝까지 {len(mails)}통" in out, out
        line = next((x for x in out.splitlines() if PEER[1] in x), "")
        unread = sum(m.unread for m in peers)
        assert line.strip().startswith(f"{len(peers)}통(안 읽음 {unread})"), f"{PEER[1]} 는 {len(peers)}통 · 안 읽음 {unread} 이다:\n{out}"


def check_moving_many_sweeps_the_views_once():
    """옮기기 준비 — 여러 통을 찾는 요청 수가 한 통과 같다(통마다 보기를 다시 받으면 큰 정리가 통 수만큼 느려진다) · 자리가 다른 통도 다 찾는다."""
    with stage(folders=(fakes_inbox.FOLDER_EMPTY,)) as (box, run):
        def asked(*unids) -> tuple[int, str]:
            before = len(box.paths)
            code, out = run("preview-move", *unids, "--to", fakes_inbox.FOLDER_EMPTY)
            assert code == 0, out
            return len(box.paths) - before, out
        four = (U["f_child"], U["alone"], U["f_top"], U["read_one"])
        alone = max(asked(u)[0] for u in four)   # 가장 깊이 든 한 통을 찾는 요청 수
        many, out = asked(*four)
        assert "옮길 메일 4통" in out and all(w in out for w in ("소재 시험 결과", "시험 일정 검토 요청", "협력사 납기 확인", "이미 읽은 메일")), out
        assert many <= alone, f"네 통을 찾는 데 요청 {many} 번 — 가장 깊은 한 통은 {alone} 번이다"
        code, out = run("preview-move", U["alone"], "F" * 32, "--to", fakes_inbox.FOLDER_EMPTY)
        assert code == mail.EXIT_CONFIG and "F" * 32 in out and U["alone"] not in out, f"없는 통을 짚어 말하지 않았다:\n{out}"


# ── 읽음 표시 — 확인 열쇠가 맞을 때만 · 그 한 통만 · 다시 읽어 댄다 ────────

def check_mark_changes_only_that_mail_with_the_key():
    with stage() as (box, run):
        before = box.unread()
        code, out = run("preview-mark", U["alone"], "--read")
        assert code == 0 and not box.changes, out
        good = key(out)
        code, out = run("apply-mark", U["alone"], "--read", "--confirm", "f" * 12)
        assert code == mail.EXIT_STALE and not box.changes, f"틀린 열쇠로 바꿨다:\n{out}"
        code, out = run("apply-mark", U["alone"], "--unread", "--confirm", good)
        assert not box.changes, f"다른 쪽(안 읽음으로)을 읽음의 열쇠로 바꿨다:\n{out}"
        code, out = run("apply-mark", U["alone"], "--read", "--confirm", good)
        assert code == 0 and "다시 읽어 맞았다" in out, out
        assert box.changes == [("read", U["alone"])] and box.unread() == before - {U["alone"]}, box.changes
        code, out = run("apply-mark", U["alone"], "--read", "--confirm", good)
        assert code == 0 and box.changes == [("read", U["alone"])], f"이미 읽은 메일을 다시 바꿨다:\n{out}"
        code, out = run("preview-mark", U["alone"], "--unread")
        code, out = run("apply-mark", U["alone"], "--unread", "--confirm", key(out))
        assert code == 0 and box.unread() == before, out


def check_organizing_commands_change_only_with_the_previewed_key():
    """폴더 · 옮기기 · 규칙 — 미리 보기는 아무것도 안 바꾸고, 틀린 열쇠 · 미리 본 뒤 달라진 인자로는 안 바꾼다. 맞는 열쇠면 그것만."""
    with stage() as (box, run):
        code, out = run("preview-folder", "--create", "검토")
        assert code == 0 and not box.changes, out
        good = key(out)
        assert run("apply-folder", "--create", "검토", "--confirm", "f" * 12)[0] == mail.EXIT_STALE and not box.changes
        assert run("apply-folder", "--create", "검토2", "--confirm", good)[0] == mail.EXIT_STALE and not box.changes
        code, out = run("apply-folder", "--create", "검토", "--confirm", good)
        assert code == 0 and [c[0] for c in box.changes] == ["folder+"], out
        code, out = run("preview-move", U["alone"], "--to", "검토")
        assert code == 0 and len(box.changes) == 1 and "안읽음" in out, out
        moving = key(out)
        assert run("apply-move", U["alone"], U["cc"], "--to", "검토", "--confirm", moving)[0] == mail.EXIT_STALE
        code, out = run("apply-move", U["alone"], "--to", "검토", "--confirm", moving)
        assert code == 0 and box.mails[U["alone"]].folder == "검토" and box.mails[U["alone"]].unread, out
        n = len(box.changes)
        code, out = run("preview-trash", U["alone"])
        assert code == 0 and len(box.changes) == n and "안읽음" in out and "검토" in out, out
        trashing = key(out)
        assert run("apply-trash", U["alone"], U["cc"], "--confirm", trashing)[0] == mail.EXIT_STALE and len(box.changes) == n
        code, out = run("apply-trash", U["alone"], "--confirm", trashing)
        assert code == 0 and box.mails[U["alone"]].folder == "($Trash)" and box.mails[U["alone"]].unread, out
        n = len(box.changes)
        code, out = run("preview-restore", U["alone"])
        assert code == 0 and len(box.changes) == n and "안읽음" in out, out
        restoring = key(out)
        assert run("apply-restore", U["alone"], U["f_trash"], "--confirm", restoring)[0] == mail.EXIT_STALE and len(box.changes) == n
        assert run("preview-restore", U["cc"])[0] == mail.EXIT_CONFIG, "휴지통에 없는 메일을 되살릴 것으로 보였다"
        code, out = run("apply-restore", U["alone"], "--confirm", restoring)
        assert code == 0 and box.mails[U["alone"]].folder == "" and box.mails[U["alone"]].unread and "받은편지함 1통" in out, out
        box.restore_to[U["f_trash"]] = "(Sent)"
        code, out = run("preview-restore", U["f_trash"])
        code, out = run("apply-restore", U["f_trash"], "--confirm", key(out))
        assert code == 0 and "받은편지함 0통" in out and "받은편지함에 없다" in out and "지운 메일" in out, out
        code, out = run("preview-rule", "--folder", "검토", "--subject", "[주간]")
        assert code == 0 and not box.rules, out
        assert run("apply-rule", "--folder", "검토", "--subject", "[월간]", "--confirm", key(out))[0] == mail.EXIT_STALE
        code, out = run("apply-rule", "--folder", "검토", "--subject", "[주간]", "--confirm", key(out))
        assert code == 0 and len(box.rules) == 1, out
        code, out = run("rules")
        assert code == 0 and "제목∋[주간]" in out and "→ 검토" in out, out
        assert not changing(p for p in box.paths if "?EditDocument" not in p), "정리 명령이 메일을 여는 주소를 불렀다"


def check_rule_change_keeps_what_is_not_given():
    """규칙 고치기 — 준 칸만 바꾸고 안 준 칸(받은 · 보낸 · 갈래 · 다른 조건 · 일치)은 지금 값을 둔다. 조건에 빈 값을 주면 그 조건을
    지우고, 「포함」으로 되돌리는 인자가 있다. 안 준 칸을 넣기의 기본값으로 채우면 보낸 메일 규칙이 받은 메일 규칙이 되고 다른
    조건이 사라진 채 서버가 곧바로 새 메일에 쓴다."""
    with stage() as (box, run):
        made = ("--box", "sent", "--action", "move_trash", "--from", "a@nuri.example", "--exact-from", "--subject", "[주간]")
        code, out = run("preview-rule", *made)
        code, out = run("apply-rule", *made, "--confirm", key(out))
        assert code == 0 and len(box.rules) == 1, out
        (unid,) = box.rules

        def change(*given):
            code, out = run("preview-rule", "--unid", unid, *given)
            assert code == 0, out
            code, out = run("apply-rule", "--unid", unid, *given, "--confirm", key(out))
            assert code == 0, out
            return box.rules[unid]

        f = change("--subject", "[월간]")
        assert (f["expRule"], f["rules"], f["rule_from"], f["rule_fromType2"], f["rule_subject"]) == \
            ("sent", "move_trash", "a@nuri.example", "1", "[월간]"), f
        f = change("--from", "", "--cc", "b@nuri.example")
        assert (f["rule_from"], f["rule_cc"], f["rule_subject"], f["expRule"]) == ("", "b@nuri.example", "[월간]", "sent"), f
        f = change("--from", "c@nuri.example", "--contains-from")
        assert (f["rule_from"], f["rule_fromType2"], f["rules"]) == ("c@nuri.example", "0", "move_trash"), f
        code, out = run("preview-rule", "--unid", unid, "--exact-from", "--contains-from")
        assert code != 0, "「일치」와 「포함」을 함께 받았다"


# ── 세션 — 손의 종료 값과 끊긴 메일함을 가른다 ───────────────────────────

def check_session_hand_exits_route_the_person():
    good, stale = fakes_inbox.COOKIE[1], "expired-session"
    # 0 — 손은 인자 없이 불리고, 끝 줄이 가리키는 파일로 연다(MAILBOX_COOKIES 는 없는 자리라 기대면 진다)
    with stage() as (box, run):
        code, out = run("list")
        assert code == 0 and box.paths, out
        assert CALLS.read_text(encoding="utf-8").split() == ["called", "args=0"], \
            f"세션 손을 인자 없이 한 번 안 불렀다: {CALLS.read_text(encoding='utf-8')!r}"
    with stage(bad_path=True) as (box, run):
        code, out = run("list")
        assert code == mail.EXIT_FAIL and "도구 고장" in out and not box.paths, f"0 인데 끝 줄이 없는 파일:\n{out}"
    # 2 — 앞서 받은 파일이 있으면 그것으로 열고, 메일함이 거절할 때만 ep-login · 없으면 바로 ep-login
    with stage(exit_code=EP.NO_EDGE, left_over=good) as (box, run):
        code, out = run("list")
        assert code == 0 and box.paths, f"Edge 에 못 붙었지만 살아 있는 앞 세션으로 안 열었다:\n{out}"
    with stage(exit_code=EP.NO_EDGE, left_over=stale) as (box, run):
        code, out = run("list")
        assert code == mail.EXIT_SESSION and "ep-login" in out, f"메일함이 거절한 앞 세션을 ep-login 으로 안 보냈다:\n{out}"
    with stage(exit_code=EP.NO_EDGE) as (box, run):
        code, out = run("list")
        assert code == mail.EXIT_SESSION and "ep-login" in out and not box.paths, f"앞 세션이 없는 2:\n{out}"
    # 3 — 앞서 받은 파일이 있어도 바로 ep-login 이다
    for left_over in (None, good):
        with stage(exit_code=EP.NOT_LOGGED_IN, left_over=left_over) as (box, run):
            code, out = run("list")
            assert code == mail.EXIT_SESSION and "ep-login" in out, f"세션 손 3:\n{out}"
            assert not box.paths, f"세션 손이 3 인데 메일함에 물었다(앞 세션 {left_over}): {box.paths}"
    with stage(exit_code=EP.TOOL) as (box, run):
        code, out = run("list")
        assert code == mail.EXIT_FAIL and "도구 고장" in out and "playwright" in out and "ep-login" not in out, out
        assert not box.paths, box.paths
    with stage(session="login") as (box, run):
        code, out = run("list")
        assert code == mail.EXIT_SESSION and "ep-login" in out, f"0 뒤 로그인 화면을 ep-login 으로 안 보냈다:\n{out}"
    with stage(session="redirect") as (_, run):
        code, out = run("read", U["alone"])
        assert code == mail.EXIT_SESSION and "ep-login" in out, out


def check_read_drops_text_the_reader_cannot_see():
    """받는 사람 눈에 안 보이는 글은 대화로 안 넘어간다 — 숨긴 요소 · 바탕색 글 · 스크립트는 본문에서, 폭 없는 문자는 제목에서도
    걷히고, 걷었다는 사실은 한 줄로 선다. 보이는 글은 다 남는다."""
    zw = "​"
    with stage() as (box, run):
        m = box.mails[U["alone"]]
        m.subject = f"시험{zw} 일정 검토 요청"
        m.text = None
        m.html = ('<p>보이는 첫 줄</p><div style="display:none">숨긴지시하나</div>'
                  '<p><span style="color:#ffffff">흰글자둘</span>보이는 둘째 줄</p><script>스크립트셋</script>')
        code, out = run("read", U["alone"])
        assert code == 0, out
        for gone in ("숨긴지시하나", "흰글자둘", "스크립트셋", zw):
            assert gone not in out, f"안 보이는 글 {gone!r} 이 나왔다:\n{out}"
        for kept in ("보이는 첫 줄", "보이는 둘째 줄", "시험 일정 검토 요청"):
            assert kept in out, f"보이는 글 {kept!r} 이 빠졌다:\n{out}"
        assert "숨긴 글 3덩이를 걷었다" in out, f"걷었다는 줄이 없다:\n{out}"
        code, out = run("list")
        assert code == 0 and zw not in out and "시험 일정 검토 요청" in out, f"목록에 폭 없는 문자가 남았다:\n{out}"


CHECKS = [value for name, value in sorted(globals().items()) if name.startswith("check_")]


def main() -> int:
    print(f"잰다: {HERE / 'mail.py'} · 곁의 메일 손 {HERE / 'inbox.py'}")
    passed = unmeasured = 0
    for check in CHECKS:
        try:
            check()
        except Unmeasured as exc:
            unmeasured += 1
            print(f"? {check.__name__}: 못 쟀다 — {exc}")
        except AssertionError as exc:
            print(f"✗ {check.__name__}: {exc}")
        except Exception:
            print(f"✗ {check.__name__}: 예상 못 한 예외\n{traceback.format_exc()}")
        else:
            passed += 1
            print(f"✓ {check.__name__}")
    print(f"통과 {passed}/{len(CHECKS)}" + (f" · 못 잼 {unmeasured}" if unmeasured else ""))
    if passed == len(CHECKS):
        return 0
    return 1 if passed + unmeasured < len(CHECKS) else 2


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        traceback.print_exc()
        print("못 쟀다")
        code = 2
    finally:
        shutil.rmtree(WORK, ignore_errors=True)
    sys.exit(code)
