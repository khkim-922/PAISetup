"""ep_session.py 의 바퀴를 잰다 — 세션 파일부터 · 거절되면 손을 한 번 · 같은 낡은 파일이면 생략 · 바꾸는 일은 늘 손부터 · 출력 담기.
세션 손은 대역(node 스크립트)이라 127.0.0.1 밖으로도, Edge 로도 안 나간다.

    python -X utf8 -I check_ep_session.py            # 이 폴더의 ep_session.py 를 잰다
    python -X utf8 -I check_ep_session.py <폴더>     # 다른 폴더의 사본을 잰다

층 · 걷는 조건 — 손으로 도는 검사(README 「돌려 보기」 · ep_session.py 나 부르는 얇은 명령을 고칠 때). check-design 1 절의 넷 — 결함에 실제 길이 있고(세션 파일이 낡은 채
남는 자리는 Edge 를 닫을 때마다 온다) · 틀리면 조용하다(손을 매번 띄우거나 낡은 파일로 두 번 돌아도 답은 온다) · 사람의 시간과 말을
다친다(회사 PC 의 프로세스 값 · 「바꾸지 않았다」는 틀린 말) · 다른 검사는 메일 길만 잰다(check_mail.py).
끝 줄이 「통과 N/N」이면 선 것이다.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent
# 손의 대역 — 종료 값은 STANDIN_EXIT, 0 이면 STANDIN_PATH 에 쿠키를 쓰고 끝 줄에 그 경로, 2 · 3 은 파일이 있으면 그 경로만. 부른 횟수는 STANDIN_LOG
STANDIN = r"""
const fs = require('fs');
const code = Number(process.env.STANDIN_EXIT || '0');
const at = process.env.STANDIN_PATH;
fs.appendFileSync(process.env.STANDIN_LOG, `called ${process.argv.slice(2).join(' ')}\n`);
if (code === 0) {
  fs.writeFileSync(at, JSON.stringify({cookies: [{name: 'fresh', value: String(Date.now())}], origins: []}));
  console.log(at);
} else if ((code === 2 || code === 3) && fs.existsSync(at)) {
  console.log(at);
}
process.exit(code);
"""


class Expired(Exception):
    pass


def load():
    spec = importlib.util.spec_from_file_location("ep_session_under_test", HERE / "ep_session.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module                   # dataclass 가 제 모듈을 sys.modules 에서 찾는다
    spec.loader.exec_module(module)
    return module


if shutil.which("node") is None:
    print("못 쟀다 — node 가 없다")
    sys.exit(2)
WORK = pathlib.Path(tempfile.mkdtemp(prefix="ep-session-check-"))
HAND = WORK / "edge_session.js"
HAND.write_text(STANDIN, encoding="utf-8")
FILE = WORK / "session.json"
CALLS = WORK / "calls.log"
ep = load()
RESULTS: list[tuple[str, bool, str]] = []


def judge(name: str, ok: bool, why: str = "") -> None:
    RESULTS.append((name, ok, why))
    print(("맞다" if ok else "틀리다") + f" — {name}" + (f": {why}" if why and not ok else ""))


@contextlib.contextmanager
def stage(exit_code: int = 0, *, file: str | None = "stale", cookies_env: bool = True):
    """대역과 환경을 세운다 — ``file`` 은 미리 둘 세션 파일의 쿠키 이름(None 이면 없음)."""
    FILE.unlink(missing_ok=True)
    if file is not None:
        FILE.write_text(json.dumps({"cookies": [{"name": file, "value": "1"}], "origins": []}), encoding="utf-8")
    CALLS.write_text("", encoding="utf-8")
    env = {"EP_SESSION_HAND": str(HAND), "STANDIN_EXIT": str(exit_code), "STANDIN_PATH": str(FILE), "STANDIN_LOG": str(CALLS),
           "MAILBOX_COOKIES": str(FILE) if cookies_env else ""}
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update({k: v for k, v in env.items()})
    if not cookies_env:
        os.environ.pop("MAILBOX_COOKIES", None)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def calls() -> list[str]:
    return [line for line in CALLS.read_text(encoding="utf-8").splitlines() if line]


def cookie_name(path: pathlib.Path) -> str:
    return json.loads(path.read_text(encoding="utf-8"))["cookies"][0]["name"]


def run(fn, **kw):
    """session_first 를 돌려 (결과, 예외, 표준 출력) 을 낸다."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            return fn(**kw), None, out.getvalue()
        except BaseException as exc:  # noqa: BLE001 — 예외도 판정 재료다
            return None, exc, out.getvalue()


def check_known_file_reads_the_hands_default():
    real = HERE / "edge_session.js"
    found = ep.DEFAULT_FILE_RE.search(real.read_text(encoding="utf-8")) if real.is_file() else None
    judge("known_file 의 정규식이 진짜 손의 DEFAULT_FILE 줄을 찾는다", bool(found and found.group(1).startswith("~")),
          "없음" if real.is_file() else "곁에 edge_session.js 가 없다")
    with stage(file="live"):
        judge("MAILBOX_COOKIES 가 가리키는 파일이 있으면 그것이다", ep.known_file() == FILE)
    with stage(file=None):
        judge("파일이 없으면 None", ep.known_file() is None)
    with stage(file="live", cookies_env=False):
        judge("환경변수 없이 대역 손(DEFAULT_FILE 줄 없음)이면 None — 손부터 간다", ep.known_file() is None)


def check_file_first_skips_the_hand():
    seen = []

    def use(file):
        seen.append(cookie_name(file))
        print("찍었다")
        return "ok"

    with stage(exit_code=3, file="live"):
        result, exc, out = run(ep.session_first, use=use, expired=(Expired,))
        judge("산 파일이면 손을 안 띄우고 한 번 돈다", result == "ok" and exc is None and seen == ["live"] and calls() == [], f"{seen} {calls()} {exc}")
        judge("첫 판의 출력은 한 번 나온다", out.count("찍었다") == 1, out)


def check_expired_file_then_hand_once():
    seen = []

    def use(file):
        name = cookie_name(file)
        seen.append(name)
        print(f"찍었다 {name}")
        if name == "stale":
            raise Expired()
        return "ok"

    with stage(exit_code=0, file="stale"):
        result, exc, out = run(ep.session_first, use=use, expired=(Expired,))
        judge("낡은 파일이 거절되면 손을 한 번 띄워 새 파일로 다시 돈다", result == "ok" and seen == ["stale", "fresh"] and len(calls()) == 1,
              f"{seen} {calls()} {exc}")
        judge("거절된 첫 판의 출력은 버리고 둘째 판만 나온다", out.strip() == "찍었다 fresh", out)


def check_same_stale_file_skips_the_second_round():
    seen = []

    def use(file):
        seen.append(cookie_name(file))
        raise Expired("낡았다")

    with stage(exit_code=2, file="stale"):
        result, exc, out = run(ep.session_first, use=use, expired=(Expired,))
        judge("손이 못 붙어 같은 파일만 가리키면 둘째 판 없이 첫 판의 거절을 올린다", isinstance(exc, Expired) and seen == ["stale"] and len(calls()) == 1,
              f"{seen} {calls()} {exc!r}")


def check_mutating_always_attaches_once():
    seen = []

    def use(file):
        seen.append(cookie_name(file))
        return "ok"

    with stage(exit_code=0, file="live"):
        result, exc, out = run(ep.session_first, use=use, expired=(Expired,), file_first=False)
        judge("file_first=False 면 산 파일이 있어도 손부터 받아 한 번만 돈다", result == "ok" and seen == ["fresh"] and len(calls()) == 1,
              f"{seen} {calls()} {exc}")


def check_other_errors_keep_the_held_output():
    def use(file):
        print("받은 파일: a.pdf")
        raise RuntimeError("넷째에서 졌다")

    with stage(exit_code=3, file="live"):
        result, exc, out = run(ep.session_first, use=use, expired=(Expired,))
        judge("거절 아닌 예외로 멈추면 멈춘 자리까지의 출력을 내보내고 올린다", isinstance(exc, RuntimeError) and "받은 파일: a.pdf" in out,
              f"{exc!r} {out!r}")


def check_no_file_and_hand_down_is_no_session():
    with stage(exit_code=3, file=None):
        result, exc, out = run(ep.session_first, use=lambda f: "ok", expired=(Expired,))
        judge("파일이 없고 손이 3 이면 NoSession(3)", isinstance(exc, ep.NoSession) and exc.got.code == ep.NOT_LOGGED_IN, repr(exc))


def check_bite():
    """물림 — 일부러 틀린 표본: 손이 2 로 다른 파일을 가리키는 꼴(파일을 새로 쓴 것처럼)에서는 둘째 판을 돌아야 한다."""
    seen = []

    def use(file):
        seen.append(file.name)
        if len(seen) == 1:
            raise Expired()
        return "ok"

    other = WORK / "other.json"
    other.write_text(json.dumps({"cookies": [{"name": "fresh2", "value": "1"}], "origins": []}), encoding="utf-8")
    with stage(exit_code=2, file="stale"):
        os.environ["STANDIN_PATH"] = str(other)          # 손이 다른 파일을 가리킨다
        result, exc, out = run(ep.session_first, use=use, expired=(Expired,))
        judge("물림 — 손이 다른 파일을 가리키면 둘째 판을 돈다(같은 파일 생략의 거울)", result == "ok" and seen == ["session.json", "other.json"],
              f"{seen} {exc!r}")


CHECKS = [v for k, v in sorted(globals().items()) if k.startswith("check_")]


def main() -> int:
    print(f"잰다: {HERE / 'ep_session.py'} · 대역 손 {HAND}")
    for check in CHECKS:
        check()
    shutil.rmtree(WORK, ignore_errors=True)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"{'통과' if passed == len(RESULTS) else '어긋남'} {passed}/{len(RESULTS)}")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
