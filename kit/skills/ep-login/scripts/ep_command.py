"""사내 앱 스킬의 얇은 명령이 함께 쓰는 뼈대 — 명령을 멈추는 꼴 · 종료 값 · 답을 JSON 하나로 내는 끝 · 답 크기에 본문 맞추기 ·
받아 둔 파일 · 날 말(오늘 · 내일 · 요일) · 빈 틈 셈(바쁜 구간 사이의 비는 때). 얇은 명령(company-board · company-regulation · company-meeting-room · company-calendar · 받아 둔 파일은 company-mail 도)이
이 폴더를 ``sys.path`` 에 넣고 싣는다. 앱 손(서버를 묻는 쪽)이 쓰는 것 — 세션 파일 · opener · SSO 넘김 칸 · 이름 누르기 · node 손
돌리기 — 은 곁의 ``ep_session.py`` 가 든다. 새 사내 앱 스킬은 제 서버를 묻는 앱 손과 제 명령만 짓고 나머지는 여기서 부른다.

부르는 꼴::

    HERE = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(HERE.parents[1] / "ep-login" / "scripts"))   # ``-I`` 로 돌면 어느 폴더도 ``sys.path`` 에 없다
    import ep_command, ep_session
    from ep_command import EXIT_ARGS, Stop, load

    def main() -> int:
        args = parser().parse_args()
        return ep_command.finish(
            lambda app: ep_session.session_first(lambda file: run(app.App(file), args),
                                                 expired=(app.SessionExpired, app.SessionMissing)),
            "xclick", HERE)                                     # 앱 손의 모듈 이름 · 그 폴더

    raise Stop(EXIT_ARGS, "args", "까닭. 다음: …")              # 명령 어디서든 — finish 가 종료 값과 JSON 으로 옮긴다
    ep_command.fit_text(out, "text", body, start, most, lambda end: f"--from {end}", ep_command.OUT_BYTES)
    gaps = ep_command.gaps_of([(시작, 끝), …], lo, hi, need)     # lo ~ hi 안에서 need 이상 비는 (시작, 끝) 들
    got = ep_command.kept(path, FORMAT, DAYS)                   # (받아 둔 dict, 받은 시각) 이나 None
    why = ep_command.keep(path, {"format": FORMAT, "stamp": time.time(), ...})   # 못 남긴 까닭 — 남겼으면 빈 글자

내는 것(``finish``) — 표준 출력에 JSON 하나와 종료 값: 0 됐다(명령의 답 그대로) · 1 도구 · 앱 고장 · 2 인자가 틀렸다 · 3 사내
세션이 없다 · 끊겼다(스킬 ep-login). 0 이 아니면 ``{"error": 갈래, "message": 까닭과 「다음: …」}`` 다. 명령이 제 종료 값을 더
두면(일정의 4) ``Stop`` 에 그 값과 갈래를 실어 올린다.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from datetime import date as _date, datetime as _datetime, timedelta as _timedelta

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))                  # 파일 경로로 실려도 곁의 ep_session 을 찾는다
import ep_session  # noqa: E402 — 이 폴더를 넣은 뒤에 싣는다

EXIT_OK, EXIT_TOOL, EXIT_ARGS, EXIT_SESSION = 0, 1, 2, 3
# 명령이 더 두는 종료 값 — 사내 앱 명령마다 한 값은 한 뜻이라, 새 갈래는 여기서 빈 값을 골라 이름을 더한다(5 는 메일의 보내는 손이 쓴다)
EXIT_STALE = 4          # 확인 열쇠가 지금과 다르다 — 미리 본 뒤 바뀌어 아무것도 안 바꿨다. 미리 보기를 다시 사람에게 보인다
EXIT_DEFAULT_APP = 6    # 사람이 그 확장자의 기본 앱을 한 번 골라야 한다
EXIT_CLASSIFIED = 7     # 기밀 · 핵심기술 문서이거나 등급을 못 읽어 사람에게 묻기 전에 멈췄다 — 답을 받은 뒤에만 넘긴다
EXIT_URL = 8            # 그 앱의 주소가 틀렸거나 잰 기본 주소로 안 읽힌다 — 사람에게 앱 화면의 주소를 받는다
NEXT_EP_LOGIN = "다음: 스킬 ep-login 으로 사내 세션을 세운 뒤 같은 명령을 다시 부른다"
OUT_BYTES = ep_session.OUT_BYTES                   # 답 하나(JSON)의 크기 — 수가 사는 자리와 까닭은 ep_session
DAY_SECONDS = 86400


class Stop(Exception):
    """명령을 멈춘다 — ``code`` 가 종료 값, ``kind`` 가 JSON 의 error 값, 메시지가 사람에게 낼 까닭이다."""

    def __init__(self, code: int, kind: str, message: str):
        super().__init__(message)
        self.code, self.kind = code, kind


def load(name: str, where: pathlib.Path):
    """``where`` 폴더의 모듈을 싣는다 — ``-I`` 로 돌면 그 폴더가 ``sys.path`` 에 없어 넣고 싣는다. 못 실으면 Stop(도구)."""
    if str(where) not in sys.path:
        sys.path.insert(0, str(where))
    try:
        return __import__(name)
    except ImportError as exc:
        raise Stop(EXIT_TOOL, "tool", f"{name} 를 못 실었다({where}) — 설치를 다시 돌린다") from exc


def size(out: dict, indent: int | None = None) -> int:
    """답이 표준 출력에서 차지할 바이트 수 — ``finish`` 가 찍는 꼴(``indent``) 그대로 센다."""
    return len(json.dumps(out, ensure_ascii=False, indent=indent).encode("utf-8"))


# ── 명령의 끝 ────────────────────────────────────────────────────────────
def no_session(got) -> Stop:
    """받는 손이 못 선 까닭(``ep_session.NoSession`` 의 ``got``)을 종료 값으로 옮긴다 — 남은 파일 없는 2 와 3 은 ep-login(종료 3),
    1 과 경로 없는 0 은 도구 고장이다."""
    if got.code in (ep_session.NO_EDGE, ep_session.NOT_LOGGED_IN):
        why = "Edge 에 붙지 못했고 앞서 받은 세션도 없다" if got.code == ep_session.NO_EDGE else "Edge 가 사내 로그인 전이다"
        return Stop(EXIT_SESSION, "session", f"사내 세션이 없다 — {why}. {NEXT_EP_LOGIN}")
    if got.code == ep_session.OK:
        return Stop(EXIT_TOOL, "tool", "세션 손이 0 으로 끝났는데 끝 줄에 세션 파일의 절대 경로가 없다")
    tail = (got.said.splitlines() or [""])[-1]
    return Stop(EXIT_TOOL, "tool", f"세션 손이 종료 {got.code} 로 졌다 — {tail}")


def _failed(app, exc: Exception, app_error: str, args_errors: tuple) -> tuple[dict, int]:
    """앱 손의 예외 → (답, 종료 값). 끊긴 · 없는 세션은 3, ``args_errors`` 는 2, 앱 손의 나머지 예외는 1, 모르는 예외는 꼴 이름과
    함께 1."""
    def one_of(*names) -> bool:
        return bool(app) and isinstance(exc, tuple(getattr(app, n) for n in names))

    if one_of("SessionExpired", "SessionMissing"):
        return {"error": "session", "message": f"{exc}. {NEXT_EP_LOGIN}"}, EXIT_SESSION
    if one_of(*args_errors):
        return {"error": "args", "message": str(exc)}, EXIT_ARGS
    if one_of(app_error):
        return {"error": "tool", "message": str(exc)}, EXIT_TOOL
    return {"error": "tool", "message": f"{type(exc).__name__}: {exc}"}, EXIT_TOOL


def finish(work, hand: str, where: pathlib.Path, *, indent: int | None = None,
           app_error: str = "AppError", args_errors: tuple = ()) -> int:
    """얇은 명령의 끝 — 앱 손(``where`` 폴더의 모듈 ``hand``)을 싣고 ``work(앱 손)`` 의 답을 표준 출력에 JSON 하나로 찍고 종료 값을
    낸다(머리말 「내는 것」). ``work`` 가 세션을 쥐는 법(``ep_session.session_first`` · 파일부터인가 손부터인가 · 세션 없이 답하는
    갈래)을 든다. 예외는 여기서 옮긴다 — ``Stop`` 은 그 값대로, 받는 손이 못 선 것(``NoSession``)은 ``no_session``, 앱 손의 예외는
    이름으로: ``SessionExpired`` · ``SessionMissing`` → 3, ``args_errors`` 에 든 이름 → 2, ``app_error``(그 손의 뿌리 예외) → 1.
    ``indent`` 는 JSON 을 찍는 꼴이다 — 그 명령의 답을 재는 ``size`` 에도 같은 값을 준다."""
    try:
        app = load(hand, where)
        try:
            result, code = work(app), EXIT_OK
        except ep_session.NoSession as exc:
            raise no_session(exc.got) from exc
    except Stop as exc:
        result, code = {"error": exc.kind, "message": str(exc)}, exc.code
    except Exception as exc:  # noqa: BLE001 — 손의 예외를 종료 값으로 옮긴다
        result, code = _failed(sys.modules.get(hand), exc, app_error, args_errors)
    print(json.dumps(result, ensure_ascii=False, indent=indent))
    return code


# ── 답 크기에 본문 맞추기 ─────────────────────────────────────────────────
def fit_end(body: str, start: int, most: int, over) -> int:
    """본문을 start 째 글자부터 most 자까지 싣되 한도를 안 넘는 끝 자리. ``over(끝)`` 은 그 끝까지 실었을 때 한도를 넘친 바이트
    수다(안 넘으면 0 이하) — 한글은 한 자가 3 바이트라 글자 수로는 못 맞춰, 넘친 만큼 글자를 덜고 다시 잰다. 남은 글이 있으면 줄
    끝에서 끊는다(표의 한 행이 두 쪽에 안 걸치게 · 그러려고 반 넘게 물러서야 하면 그 자리에서 끊는다). 한 글자는 늘 싣는다 —
    안 그러면 이어 읽기가 제자리를 돈다. 마지막으로 잰 끝을 낸다."""
    end = min(len(body), start + most)
    while True:
        if end < len(body):
            line = body.rfind("\n", start, end)
            if line - start > (end - start) // 2:
                end = line + 1
        spill = over(end)
        if spill <= 0 or end - start <= 1:
            return end
        end -= min(end - start - 1, max(1, spill // 3))


def fit_text(out: dict, key: str, body: str, start: int, most: int, more, limit: int, indent: int | None = None) -> int:
    """답 ``out`` 의 ``key`` 칸에 본문을 start 부터 most 자까지 싣되 답 전체가 ``limit`` 바이트를 안 넘게 끝을 당긴다(``fit_end``).
    남은 글이 있으면 ``out["more"]`` 에 ``more(다음 자리)`` 를 싣는다 — 그 말은 명령마다 제 것이다. 실은 끝 자리를 낸다. 이 뒤에
    답에 칸을 더하면 그만큼 한도를 넘을 수 있다 — 더할 칸은 먼저 싣고 부른다."""
    def over(end: int) -> int:
        out[key] = body[start:end]
        out.pop("more", None)
        if end < len(body):
            out["more"] = more(end)
        return size(out, indent) - limit

    return fit_end(body, start, most, over)


# ── 받아 둔 파일 ─────────────────────────────────────────────────────────
def kept(path: pathlib.Path, form: int, days: float, *, by_mtime: bool = False) -> tuple[dict, float] | None:
    """받아 둔 JSON 파일 — 꼴 번호(``format`` 칸)가 ``form`` 이고 받은 지 ``days`` 날이 안 된 것만 (내용, 받은 시각)으로 낸다.
    없거나 낡았거나 꼴이 다르거나 깨졌으면 None — 부르는 쪽이 새로 받는다. 받은 시각은 파일의 ``stamp`` 칸, ``by_mtime`` 이면 파일을
    쓴 시각이다. 어디에 두고 며칠 쓰고 내용의 무엇을 더 보나는 스킬마다 제 것이다."""
    try:
        stamp = path.stat().st_mtime if by_mtime else None
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("format") != form:
            return None
        if not by_mtime:
            stamp = float(raw["stamp"])
        return (raw, stamp) if time.time() - stamp < days * DAY_SECONDS else None
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def keep(path: pathlib.Path, data: dict) -> str:
    """``data`` 를 JSON 으로 ``path`` 에 남긴다 — 곁의 임시 파일에 다 쓴 뒤 바꿔 끼워, 도중에 죽어도 반쯤 쓴 파일이 안 남는다.
    내는 것은 못 남긴 까닭이다(남겼으면 빈 글자). 못 남겨도(권한 · 디스크 · 다른 프로세스가 그 파일을 쥠) 예외를 안 올린다 —
    받아 둔 것은 다음 판을 빠르게 할 뿐이라, 못 남겼다고 방금 받은 답을 잃으면 안 된다."""
    temp = path.with_suffix(f".{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        temp.replace(path)
    except OSError as exc:
        try:
            temp.unlink(missing_ok=True)           # 못 바꿔 끼운 임시 파일을 남기지 않는다
        except OSError:
            pass
        return f"{type(exc).__name__}: {exc}"
    return ""


# ── 날 말 ─────────────────────────────────────────────────────────────────
WEEKDAYS = "월화수목금토일"                        # date.weekday() 의 0 ~ 6 — 답에 요일을 실어 모델이 요일을 제 셈으로 짐작하지 않게
DAY_WORDS = {"오늘": 0, "today": 0, "내일": 1, "tomorrow": 1, "모레": 2}   # 날 말 → 오늘에서 며칠 뒤
# 날 말에 없는 말을 어떻게 주나 — 날을 받는 명령의 --help 와 멈추는 말이 함께 쓴다
DAY_COUNT = "요일 · 「다음 주 금요일」 같은 말은 안 받는다 — 오늘 날짜에서 세어 YYYY-MM-DD 로 준다"


def day_of(text: str | None, today: _date) -> _date:
    """사람이 준 날 — 날 말(``DAY_WORDS`` · 대소문자 무시)이나 ``YYYY-MM-DD``. 비면 오늘이다. 꼴이 아니면 Stop(인자)."""
    word = (text or "오늘").strip().lower()
    if word in DAY_WORDS:
        return today + _timedelta(days=DAY_WORDS[word])
    try:
        return _date.fromisoformat(word)
    except ValueError as exc:
        raise Stop(EXIT_ARGS, "args", f"날은 오늘 · 내일 · 모레 · YYYY-MM-DD 가운데 하나로 준다: {text!r}") from exc


# ── 빈 틈 셈 ──────────────────────────────────────────────────────────────
def gaps_of(busy, lo: _datetime, hi: _datetime, need: _timedelta) -> list[tuple[_datetime, _datetime]]:
    """``lo`` ~ ``hi`` 안에서 ``need`` 이상 비는 때를 (시작, 끝) 차례로 낸다. ``busy`` 는 바쁜 구간 ``(시작, 끝)`` 들이다 — 차례 ·
    겹침 · ``lo`` ~ ``hi`` 밖으로 삐져나감은 아무래도 된다(그 안으로 잘라 시작 차례로 겹친다). 시각은 다 시간대가 붙은 것이다."""
    out, at = [], lo
    for a, b in sorted((max(a, lo), min(b, hi)) for a, b in busy):
        if b <= a:
            continue
        if a - at >= need:
            out.append((at, a))
        at = max(at, b)
    if hi - at >= need:
        out.append((at, hi))
    return out
