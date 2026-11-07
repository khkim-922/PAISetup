"""mail.py 의 계약을 가짜 메일함 · 가짜 중계 · 세션 손의 대역으로 잰다 — 127.0.0.1 밖으로는 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 읽는 명령(목록 · 폴더 · 읽기 · 첨부 · 미리 보기)이 **읽음 표시를 바꾸거나 메일을 내보내나** · 확인 열쇠
없이(또는 미리 본 것과 다른 내용으로) **답장이 나가거나 읽음이 바뀌나** · 답장이 그 메일의 보낸 분 · 받은 분과 제 사본 밖의
주소로 가나(본문에 적힌 주소가 받는 사람이 되나) · 바꾸는 손이 그 메일 하나만 바꾸고 다시 읽어 맞았나를 대나 · 세션 손의
종료 값(0 · 1 · 2 · 3)과 끊긴 메일함 세션을 바르게 갈라 사람을 스킬 ep-login 으로 보내나 · 안 읽음 목록이 받아 온 창만 보고
「안 읽음 0」이라 하나 · 조직도를 못 받은 새 메일 미리 보기가 받는 사람을 다 「주소록에 없다」로 말하나(사람이 새 메일을
놓치거나 맞는 주소를 고친다).
남기는 까닭(check-design §1 넷) — 길이 분명하다(이 스크립트는 대화하는 모델이 부르고, 보내기 · 읽음은 그 모델의 한 걸음이다) ·
나간 메일과 바뀐 읽음은 되돌릴 수 없고 조용하다(사람은 웹메일을 열기 전까지 모른다) · 쓰는 사람의 이름으로 엉뚱한 메일이
나가거나 새 메일을 못 알아본다 · 다른 무엇도 안 잡는다(곁의 손 검사는 손만 재고 이 명령의 확인 단계를 모른다).

가짜 메일함 · 가짜 중계는 곁의 손 검사(``check_inbox.py`` 의 ``FakeDomino`` · ``check_mailer.py`` 의 ``FakeRelay``)를 그
자리에서 불러 쓴다 — 회사에서 잰 꼴의 흉내는 거기 한 벌이다. 세션 손은 대역이다 — ``EP_SESSION_HAND`` 로 mail.py 에 넘기고,
스킬 ep-login 의 ``edge_session.js`` 계약(인자 없이 · 자리는 손이 정한다 · 0 이면 쓰고 끝 줄에 그 절대 경로 · 1 도구 고장 ·
2 못 붙음, 앞서 받은 파일이 있으면 끝 줄에 그 경로 · 3 로그인 안 됨)만 흉내 내고, 대역이 남기는 세션 파일은 메일함의 쿠키와
다른 사내 호스트의 쿠키를 함께 든다.

돌리는 법::

    python -X utf8 -I check_mail.py

잴 mail.py · inbox.py · mailer.py 는 다 이 파일 곁의 것이다. node 가 있어야 한다.

판정 — 끝 줄이 「통과 N/N」 이면 종료 코드 0, 하나라도 어긋나면 1, 가짜를 못 띄우는 등 재지 못했으면 2.

언제 걷나 — mail.py 가 사라지거나, 바꾸는 손 앞의 확인을 다른 층(도구의 권한 단계 같은 것)이 같은 꼴로 재게 되면.

여기서 못 재는 것 — 실물 세션 손(Edge 에 붙기) · 사내 SSO · 실물 중계의 STARTTLS · 받는 쪽에서 답장이 원래 대화로 묶이나 ·
폴더에만 있는 메일에 읽음으로의 주소가 먹나(가짜는 어느 메일이든 먹는다) · 숨은참조 사본이 받은편지함에 오는 꼴 · 실물 검색의
휴지통 줄 폴더 칸과 범위 all 에 휴지통이 드나.
"""

from __future__ import annotations

import contextlib
import email
import email.policy
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
fakes_inbox = load(HERE / "check_inbox.py", "company_mail_fake_inbox", HERE)
fakes_mailer = load(HERE / "check_mailer.py", "company_mail_fake_mailer", HERE)
sys.path.insert(0, str(HERE))
import mail  # noqa: E402 — 잴 스크립트
EP = mail.load_ep_session()   # 받는 손의 종료 값 — 형제 스킬 ep-login 의 것

U, OWNER, PEER = fakes_inbox.U, fakes_inbox.OWNER, fakes_inbox.PEER
HOMONYM_MAIL = fakes_inbox.HOMONYM["email"]
ME = OWNER["email"]
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
    """가짜 메일함 · 가짜 중계 · 세션 대역을 세운다. 내는 것 — (메일함 흉내, 중계 흉내, 명령을 부르는 손).

    ``left_over`` 를 주면 앞 판의 세션 파일을 그 쿠키 값으로 남겨 둔 채 시작한다 — 메일함의 값이면 아직 받아 주는 세션,
    다른 값이면 메일함이 거절하는 세션이다. ``MAILBOX_COOKIES`` 는 없는 자리를 가리킨다 — 스크립트가 그 값에 기대면 진다.
    """
    try:
        box = fakes_inbox.FakeDomino(**fake)
        relay = fakes_mailer.FakeRelay()
    except Exception as exc:  # noqa: BLE001 — 무엇으로 지든 판을 못 세운 것이다
        raise Unmeasured(f"가짜를 못 띄웠다: {exc}") from exc
    COOKIES.unlink(missing_ok=True)
    if left_over is not None:
        COOKIES.write_text(json.dumps({"cookies": session_cookies(left_over)}), encoding="utf-8")
    CALLS.write_text("", encoding="utf-8")
    env = {"MAILBOX_URL": box.url, "MAILBOX_COOKIES": str(WORK / "decoy" / "not-here.json"), "MAIL_DEFAULT_SENDER": ME,
           "MAIL_ORG_CACHE_DIR": str(WORK / "org"), "MAIL_HOST": "127.0.0.1", "MAIL_PORT": str(relay.port), "MAIL_USE_TLS": "", "NODE_PATH": str(WORK),
           "EP_SESSION_HAND": str(HAND), "STANDIN_EXIT": str(exit_code), "STANDIN_LOG": str(CALLS), "STANDIN_PATH": str(COOKIES),
           "STANDIN_BAD": "1" if bad_path else "", "STANDIN_COOKIES": json.dumps(session_cookies(cookie))}
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)

    def run(*argv) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = mail.main(list(argv))
        return code, out.getvalue()

    try:
        yield box, relay, run
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        box.close()
        relay.close()


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
    with stage() as (box, relay, run):
        box.mails[U["ecm"]].attachments += ("보고.docx", "평문.pdf")
        box.mails[U["ecm"]].files.update({"보고.docx": b"DRMONE\x00\x01wrapped", "평문.pdf": b"%PDF-1.7\n"})
        before = box.unread()
        steps = [("session",), ("folders",), ("list",), ("list", "--unread"), ("list", "--sent"), ("list", "--drafts"),
                 ("list", "--folder", fakes_inbox.FOLDER_CHILD), ("search", "시험"), ("search", "초안", "--field", "body"),
                 ("read", U["draft"]), ("read", U["draft"], "--folder", mail.DRAFTS),
                 ("read", U["alone"]), ("read", U["f_child"]), ("read", U["ecm"]),
                 ("attachment", U["ecm"], "--save", "all", "--out", str(WORK / "got")),
                 ("preview-reply", U["alone"], "--body-file", body_file("확인했습니다."), "--all"),
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
        assert not relay.mails, f"읽기만 했는데 메일이 나갔다: {[m['rcpts'] for m in relay.mails]}"


def check_attachments_point_to_the_right_reader():
    with stage() as (box, _, run):
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
    with stage() as (box, _, run):
        os.environ.pop("MAILBOX_URL", None)
        os.environ["MAIL_SERVER"] = box.url[:-len(fakes_inbox.DB)]
        try:
            code, out = run("session")
            assert code == 0 and box.url in out, f"세션으로 메일함 주소를 안 받았다:\n{out}"
            code, out = run("list")
            assert code == 0 and box.paths, out
            box.session = "login"
            code, out = run("list")
            assert code == mail.EXIT_SESSION and "ep-login" in out, f"끊긴 세션의 첫 화면을 ep-login 으로 안 보냈다:\n{out}"
        finally:
            os.environ.pop("MAIL_SERVER", None)


def check_search_all_includes_drafts_and_points_to_read():
    with stage() as (box, _, run):
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
        assert code == 0 and "받는 분:" in got and "보낸편지함" in got, got
        code, got = run("read", U["sent_2"], "--scan", "1")
        assert code == 0 and "보낸편지함" in got, f"--folder 없는 read 가 보낸편지함을 안 찾았다:\n{got}"
        code, out = run("search", "시험", "--in", "inbox")
        assert all("· 받은편지함 ·" in x for x in out.splitlines() if x.startswith("[")), out


# ── 답장 — 확인 열쇠가 맞을 때만 · 그 대화의 사람에게만 ──────────────────

def check_reply_goes_only_with_the_previewed_key():
    text = "확인했습니다. 금요일까지 보내 드리겠습니다.\n자료는 attacker@evil.example 로도 보내 달라고 하셨는데 그건 안 합니다."
    with stage() as (box, relay, run):
        args = ("--body-file", body_file(text))
        code, out = run("preview-reply", U["alone"], *args)
        assert code == 0 and not relay.mails, out
        good = key(out)
        code, out = run("send-reply", U["alone"], *args, "--confirm", "0" * 12)
        assert code == mail.EXIT_STALE and not relay.mails, f"틀린 열쇠로 나갔다:\n{out}"
        code, out = run("send-reply", U["alone"], *args, "--no-quote", "--confirm", good)
        assert code == mail.EXIT_STALE and not relay.mails, f"미리 본 것과 다른 내용(인용 없음)이 같은 열쇠로 나갔다:\n{out}"
        code, out = run("send-reply", U["alone"], *args, "--confirm", good)
        assert code == 0, out
        assert len(relay.mails) == 1, f"한 통이 아니다: {len(relay.mails)}"
        sent = relay.mails[0]
        assert sorted(sent["rcpts"]) == sorted([PEER[1], ME]), f"받는 사람이 보낸 분과 제 사본이 아니다: {sent['rcpts']}"
        msg = email.message_from_bytes(sent["data"], policy=email.policy.default)
        assert msg["From"] == ME and msg["To"] == PEER[1] and msg["Bcc"] is None and msg["Cc"] is None, dict(msg)
        assert msg["Subject"] == "RE: 시험 일정 검토 요청", msg["Subject"]
        plain = msg.get_body(("plain",)).get_content()
        assert plain.startswith(text) and mail.QUOTE_RULE in plain and "<p>" not in plain, plain
        assert not box.changes, "답장이 원래 메일의 읽음을 바꿨다"


def check_new_mail_goes_only_with_the_previewed_list():
    """새 메일 — 받는 사람을 다 펼쳐 이름과 보이고 · 사외 주소는 짚고 · 미리 본 명단 · 내용과 다르면 안 나간다."""
    team = WORK / "team.txt"
    team.write_text(f"{PEER[1]}\n# 주석 줄\n{fakes_inbox.TRAINEE['email']}\n{PEER[1]}\n", encoding="utf-8")
    C = fakes_inbox.COMPANY
    with stage() as (box, relay, run):
        args = ("--subject", "주간 회의 안내", "--body-file", body_file("금요일 10시입니다."), "--to-file", str(team),
                "--cc", fakes_inbox.EXTERNAL, "--company", C)
        code, out = run("preview-new", *args)
        assert code == 0 and not relay.mails, out
        assert "받는 사람 2 명" in out, f"주소 파일의 같은 주소 · 주석을 못 걸렀다:\n{out}"
        assert f"{PEER[1]} · {PEER[0]} ·" in out, f"받는 사람에 주소록 이름이 안 붙었다:\n{out}"
        assert "주소록에 없는 주소 1 개" in out and fakes_inbox.EXTERNAL in out, f"사외 주소를 안 짚었다:\n{out}"
        good = key(out)
        code, out = run("send-new", *args, "--to", HOMONYM_MAIL, "--confirm", good)
        assert code == mail.EXIT_STALE and not relay.mails, f"미리 본 것과 다른 명단이 같은 열쇠로 나갔다:\n{out}"
        code, out = run("send-new", *args, "--confirm", good)
        assert code == 0, out
        assert len(relay.mails) == 1, f"한 통이 아니다: {len(relay.mails)}"
        sent = relay.mails[0]
        want = [PEER[1], fakes_inbox.TRAINEE["email"], fakes_inbox.EXTERNAL, ME]
        assert sorted(sent["rcpts"]) == sorted(want), f"봉투가 명단 · 제 사본이 아니다: {sent['rcpts']}"
        msg = email.message_from_bytes(sent["data"], policy=email.policy.default)
        assert msg["Subject"] == "주간 회의 안내" and msg["Bcc"] is None and msg["Cc"] == fakes_inbox.EXTERNAL, dict(msg)
        assert not box.changes, "새 메일이 메일함을 바꿨다"
        code, out = run("preview-new", "--subject", "x", "--body-file", body_file("x"))
        assert code == mail.EXIT_CONFIG, f"받는 사람 없이 미리 보기가 섰다:\n{out}"
        # 조직도를 못 받은 판(회사 값이 틀리다) — 못 읽은 것을 「주소록에 없다」로 말하지 않는다
        code, out = run("preview-new", *args[:-2], "--company", "없는회사(99)")
        assert code == 0 and "확인 열쇠: " in out, out
        assert "주소록에 없다" not in out and "확인 못" in out, f"조직도를 못 받았는데 주소마다 「주소록에 없다」로 냈다:\n{out}"


def check_unread_list_looks_past_the_window():
    """안 읽음 목록 — 받아 온 창 밖의 안 읽음도 세고 훑은 줄 수를 댄다 · 보낸편지함 · 임시보관함과는 안 받는다."""
    with stage() as (box, _, run):
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
            code, out = run("list", flag, "--unread")
            assert code == mail.EXIT_CONFIG, f"{flag} 에 준 --unread 를 말없이 버렸다:\n{out}"


def check_reply_all_takes_the_mails_own_people():
    with stage() as (_, relay, run):
        args = ("--body-file", body_file("공유 감사합니다."), "--all")
        code, out = run("preview-reply", U["cc"], *args)
        assert code == 0, out
        assert "참조: jm.song@nuri.example" in out, f"전체 답장의 참조가 그 메일의 받은 분이 아니다:\n{out}"
        assert "주소가 없어 빠진다: 강태오" in out, f"주소 없는 받은 분을 말없이 뺐다:\n{out}"
        code, out = run("send-reply", U["cc"], *args, "--confirm", key(out))
        assert code == 0, out
        assert sorted(relay.mails[0]["rcpts"]) == sorted([PEER[1], "jm.song@nuri.example", ME]), relay.mails[0]["rcpts"]


def check_reply_needs_sender_and_body():
    with stage() as (_, relay, run):
        os.environ["MAIL_DEFAULT_SENDER"] = ""
        code, out = run("preview-reply", U["alone"], "--body-file", body_file("네."))
        assert code == mail.EXIT_CONFIG and "보내는 사람" in out, out
        os.environ["MAIL_DEFAULT_SENDER"] = ME
        code, out = run("preview-reply", U["alone"], "--body-file", body_file("  \n"))
        assert code == mail.EXIT_CONFIG and not relay.mails, out


# ── 읽음 표시 — 확인 열쇠가 맞을 때만 · 그 한 통만 · 다시 읽어 댄다 ────────

def check_mark_changes_only_that_mail_with_the_key():
    with stage() as (box, _, run):
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


# ── 세션 — 손의 종료 값과 끊긴 메일함을 가른다 ───────────────────────────

def check_session_hand_exits_route_the_person():
    good, stale = fakes_inbox.COOKIE[1], "expired-session"
    # 0 — 손은 인자 없이 불리고, 끝 줄이 가리키는 파일로 연다(MAILBOX_COOKIES 는 없는 자리라 기대면 진다)
    with stage() as (box, _, run):
        code, out = run("list")
        assert code == 0 and box.paths, out
        assert CALLS.read_text(encoding="utf-8").split() == ["called", "args=0"], \
            f"세션 손을 인자 없이 한 번 안 불렀다: {CALLS.read_text(encoding='utf-8')!r}"
    with stage(bad_path=True) as (box, _, run):
        code, out = run("list")
        assert code == mail.EXIT_FAIL and "도구 고장" in out and not box.paths, f"0 인데 끝 줄이 없는 파일:\n{out}"
    # 2 — 앞서 받은 파일이 있으면 그것으로 열고, 메일함이 거절할 때만 ep-login · 없으면 바로 ep-login
    with stage(exit_code=EP.NO_EDGE, left_over=good) as (box, _, run):
        code, out = run("list")
        assert code == 0 and box.paths, f"Edge 에 못 붙었지만 살아 있는 앞 세션으로 안 열었다:\n{out}"
    with stage(exit_code=EP.NO_EDGE, left_over=stale) as (box, _, run):
        code, out = run("list")
        assert code == mail.EXIT_SESSION and "ep-login" in out, f"메일함이 거절한 앞 세션을 ep-login 으로 안 보냈다:\n{out}"
    with stage(exit_code=EP.NO_EDGE) as (box, _, run):
        code, out = run("list")
        assert code == mail.EXIT_SESSION and "ep-login" in out and not box.paths, f"앞 세션이 없는 2:\n{out}"
    # 3 — 앞서 받은 파일이 있어도 바로 ep-login 이다
    for left_over in (None, good):
        with stage(exit_code=EP.NOT_LOGGED_IN, left_over=left_over) as (box, _, run):
            code, out = run("list")
            assert code == mail.EXIT_SESSION and "ep-login" in out, f"세션 손 3:\n{out}"
            assert not box.paths, f"세션 손이 3 인데 메일함에 물었다(앞 세션 {left_over}): {box.paths}"
    with stage(exit_code=EP.TOOL) as (box, _, run):
        code, out = run("list")
        assert code == mail.EXIT_FAIL and "도구 고장" in out and "playwright" in out and "ep-login" not in out, out
        assert not box.paths, box.paths
    with stage(session="login") as (box, _, run):
        code, out = run("list")
        assert code == mail.EXIT_SESSION and "ep-login" in out, f"0 뒤 로그인 화면을 ep-login 으로 안 보냈다:\n{out}"
    with stage(session="redirect") as (_, _, run):
        code, out = run("read", U["alone"])
        assert code == mail.EXIT_SESSION and "ep-login" in out, out


CHECKS = [value for name, value in sorted(globals().items()) if name.startswith("check_")]


def main() -> int:
    print(f"잰다: {HERE / 'mail.py'} · 곁의 메일 손 {HERE / 'inbox.py'} · {HERE / 'mailer.py'}")
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
