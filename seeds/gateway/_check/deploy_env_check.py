"""배포가 심는 주소와 토큰 — 주소 손잡이가 갈래를 옮기고, 로그인을 선언한 앱만 서버 토큰을 쓰나.

    python -X utf8 _check/deploy_env_check.py

왜 이 검사가 있나 — 회사 방식 배포(SR → 회사 GitLab → CI/CD)는 운영팀이 CI 변수로 게이트웨이
주소와 앱 토큰을 심는다(`AI_GW_URL` · `AI_GW_TOKEN`). 배관이 그 이름을 안 읽으면 그 앱은 사내
게이트웨이를 한 번도 못 부르고 드라이런에 머무는데, **아무 데서도 안 운다** — 드라이런은 오류가
아니라 봉투 명세를 돌려주는 정상 응답이라서다.

재는 것 셋 — 손잡이는 적재 시점에 굳으므로 판마다 배관을 **자식 프로세스에서** 새로 올린다.
  [1] 주소 — 손잡이가 비면 회사 갈래가 한 바닥을 나눠 쓴다 · 회사 바닥 손잡이(앱 것 ·
      회사 이름)는 회사 갈래만 옮긴다 · 둘 다 있으면 앱 것이 이긴다 · `/v1` 을 붙여 와도 같은
      바닥이다 · 바깥 갈래는 제 손잡이로만 옮긴다 · SDK 표준 이름은 안 읽는다 · 주소가 아닌
      값은 뜰 때 죽는다
  [2] 서버 토큰 — 로그인을 선언 안 한 앱(기본)은 토큰이 있어도 안 쓴다 · 선언한 앱은 회사
      갈래에만 깐다 · 실어 온 키가 이긴다 · 담장에서 내린 요청과 드라이런 강제는 그대로
      드라이런이다 · 토큰이 없으면 드라이런이다
  [3] 끝에서 끝 — 로그인을 선언한 앱에 두 이름을 루프백 가짜 게이트웨이로 주면 회사 갈래마다
      요청이 그 바닥 아래 계약 경로로 그 토큰을 싣고 닿는다. 선언 안 한 앱은 한 건도 안 보낸다

**기대값은 회사 문서에서 온다** — 계약 경로와 변수 이름이다. 배관의 상수를 기대값으로 쓰면
배관이 틀릴 때 기대값도 같이 틀려 초록이 난다.

로그인 선언(`LOGIN_REQUIRED`)이 배관에 없으면 [2]·[3] 은 「못 쟀다」(2)다 — 빨강이 아니다
(`_plumb` 의 「없다」 규율). 로그인 없는 형제는 이 검사를 받아 가지 않는다. [1] 은 이름이 아니라
동작을 보므로 주소 손잡이가 없는 배관에서는 빨강이 난다.

내는 것 — 종료코드 0 판정이 다 초록 · 1 어긋남 · 2 못 쟀다(접두어를 못 읽었다 · 표에 회사 갈래가
없다 · 로그인 선언이 없다 · 자식 프로세스가 졌다). 어긋남이 하나라도 있으면 못 잰 자리가 있어도 1 이다.

안 재는 것 — 사내 게이트웨이가 그 토큰을 실제로 받나 · 운영팀이 `AI_GW_URL` 에 어느 꼴을
적나(회사 문서가 안 정했다) · 앱의 문이 정말 모든 요청을 로그인으로 거르나(선언의 참은 적는
사람이 든다). 망을 안 탄다 — [3] 의 상대는 이 PC 의 루프백이다.
"""
import json
import os
import subprocess
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from _verdict import (EXIT_MISMATCH, EXIT_OK, EXIT_UNMEASURED, Unmeasured, edge, fails, passes,
                      report, unmeasured, unmeasureds)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from _plumb import MODULE, PROVIDERS_MODULE, Missing, gateway, get, slot  # noqa: E402 — 배관은 선언이 고른다
from gateway_probe import SAY, _Fake  # noqa: E402 — 가짜 게이트웨이는 한 벌이다(지어 옮기지 않는다)

# ⚠ **접두어를 지어내지 않는다** — 재는 손잡이의 이름이 접두어에서 나온다. 지어내면 자식이
#   아무 손잡이도 안 받은 채 돌아 「비운 판」이 초록으로 선다. 못 읽으면 못 쟀다(2)다.
try:
    P = get("ENV_PREFIX")
except Missing as why:
    raise Unmeasured(f"⚠ 손잡이 이름을 못 지었다 — {why}") from why

# 회사가 정한 이름 — 회사 기준 씨앗 `seeds/vibecoding/` 의 `docs/references/futurem-adapters.md`
# (`llm_gateway.py` 절). 배관의 상수가 아니라 이 글자를 쓴다 — 머리말의 「기대값은 회사 문서에서」.
COMPANY_URL = "AI_GW_URL"
COMPANY_TOKEN = "AI_GW_TOKEN"
# 계약 경로 — 바닥 뒤에 붙는 것. Claude-Posco.setting.md 「Messages API (Anthropic)」 절의 `POST` 줄 ·
# OpenAI.-Posco.Setting.md 「Responses API (OpenAI)」 절의 `POST` 줄 · Gemini 는 바닥이 곧 갈래 주소다
# (Gemini-Posco.setting.md 「Gemini Native API (Gemini)」 절의 `POST` 줄 · 경로는 봉투가 짓는다).
PATH_OF = {gateway.CONTRACT_ANTHROPIC: "/v1/messages",
           gateway.CONTRACT_OPENAI: "/v1/responses",
           gateway.CONTRACT_GEMINI: ""}
# 바깥 갈래의 손잡이 — 계약마다 하나다(이 씨앗이 정한 이름).
OUTSIDE_HANDLE = {gateway.CONTRACT_ANTHROPIC: "ANTHROPIC_API_BASE_URL",
                  gateway.CONTRACT_GEMINI: "GEMINI_API_BASE_URL"}
# 회사 PC 에서 다른 클라이언트가 회사 쪽을 보라고 심는 SDK 표준 이름 — 읽으면 안 되는 쪽이다.
SDK_NAMES = ("ANTHROPIC_BASE_URL", "GOOGLE_GEMINI_BASE_URL")

# 손잡이에 얹는 값 — 기본 주소와 겹치지 않는 루프백이다. 겹치면 손잡이가 안 서는 판도 초록이 된다.
# [1] 은 주소를 짓기만 하고 안 두드린다.
SENTINEL = "http://127.0.0.1:9"
# 가짜 키 — 아스키다. 머리는 latin-1 로 나가므로 한글이면 배관이 아니라 `http.client` 가 넘어진다.
TOKEN = "probe-server-token"
CARRIED = "probe-carried-key"

ROWS = gateway._GATEWAY
COMPANY = [p for p, r in ROWS.items() if r["site"] == gateway.SITE_POSCO and not r.get("local")]
OUTSIDE = [p for p, r in ROWS.items() if r["site"] != gateway.SITE_POSCO and not r.get("local")]
LOCAL = [p for p, r in ROWS.items() if r.get("local")]

# ⚠ **배관 이름을 자식에게 인자로 건넨다.** 자식은 `_check/` 가 경로에 없어 `_plumb` 을 못 문다 —
#   자식이 제 손으로 `app.gateway` 를 적으면 배관을 다르게 두는 저장소에서 남의 모듈을 잰다.
_HEAD = ("import importlib, json, sys\n"
         "gateway = importlib.import_module(sys.argv[1])\n"
         "providers = importlib.import_module(sys.argv[2])\n")


def _env_of(**over):
    """자식이 받는 환경 — 이 PC 에 깔린 손잡이를 걷고 얹을 것만 얹는다.

    ⚠ **루프백은 프록시를 안 태운다.** 회사 PC 는 프록시를 환경변수로 걸어 두는데, 타면 [3] 의
      요청이 가짜 게이트웨이 대신 프록시로 가 없는 빨강이 난다.
    """
    drop = (f"{P}_", "AI_GW_") + SDK_NAMES
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith(drop) and k.lower() != "no_proxy"}
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["PYTHONUTF8"] = "1"
    env.update(over)
    return env


def child(code, **over):
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", _HEAD + code, MODULE, PROVIDERS_MODULE],
                       cwd=ROOT, env=_env_of(**over), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    return r.returncode, r.stdout.strip(), r.stderr


def _load(label, rc, out, err):
    """자식의 마지막 줄 JSON — 자식이 졌으면 「못 쟀다」로 찍고 None. 판정은 부르는 쪽이 낸다."""
    if rc != 0:
        unmeasured(label, f"자식이 졌다 (exit {rc}) — {err.strip()[-300:]}")
        return None
    return json.loads(out.splitlines()[-1])


# ---------- [1] 주소 ----------

_URLS = 'print(json.dumps({p: r["url"] for p, r in gateway._GATEWAY.items()}))'


def urls(label, **over):
    return _load(label, *child(_URLS, **over))


def moved(got, rows, base):
    """그 갈래들이 `base` + 계약 경로에 섰나 — 어긋난 자리를 상세로 돌려준다."""
    want = {p: base + PATH_OF[ROWS[p]["contract"]] for p in rows}
    return ([f"{p}: {got[p]!r} — 기대 {want[p]!r}" for p in rows if got[p] != want[p]])


def urls_section():
    print("[1] 주소 — 손잡이가 갈래를 옮기나")
    base = urls("[1] 손잡이 없이 올리기")
    if base is None:
        return
    # 회사 갈래 셋이 **한 바닥**을 나눠 쓰나 — 갈래마다 계약 경로를 떼어 남는 것이 하나여야 한다.
    floors = {p: base[p][:len(base[p]) - len(PATH_OF[ROWS[p]["contract"]])] for p in COMPANY}
    report("손잡이가 비면 회사 갈래가 한 바닥 + 계약 경로에 선다",
           len(set(floors.values())) == 1 and all(
               base[p].endswith(PATH_OF[ROWS[p]["contract"]]) for p in COMPANY),
           [f"{p}: {base[p]!r}" for p in COMPANY])
    edge("기본 주소 — " + " · ".join(f"{p}={base[p]}" for p in COMPANY + OUTSIDE))

    app_base, co_base = f"{SENTINEL}/app-handle", f"{SENTINEL}/company-name"
    over = {f"{P}_GATEWAY_BASE_URL": app_base}
    over.update({f"{P}_{OUTSIDE_HANDLE[ROWS[p]['contract']]}": f"{SENTINEL}/{p}" for p in OUTSIDE})
    got = urls("[1] 앱 손잡이 셋", **over)
    if got is not None:
        bad = moved(got, COMPANY, app_base)
        report(f"{P}_GATEWAY_BASE_URL 이 회사 갈래를 다 옮긴다", not bad, bad)
        for p in OUTSIDE:
            name = f"{P}_{OUTSIDE_HANDLE[ROWS[p]['contract']]}"
            bad = moved(got, [p], f"{SENTINEL}/{p}")
            report(f"{name} 가 바깥 갈래 {p} 를 옮긴다", not bad, bad)

    got = urls(f"[1] {COMPANY_URL}", **{COMPANY_URL: co_base})
    if got is not None:
        bad = moved(got, COMPANY, co_base)
        report(f"{COMPANY_URL} 가 회사 갈래를 다 옮긴다 — 운영팀이 심는 이름 그대로", not bad, bad)
        report(f"{COMPANY_URL} 는 바깥 갈래를 안 옮긴다 — 회사 주소가 「내 키」 갈래를 끌고 가지 않는다",
               all(got[p] == base[p] for p in OUTSIDE),
               [f"{p}: {got[p]!r} — 기대 {base[p]!r}" for p in OUTSIDE if got[p] != base[p]])

    got = urls("[1] 둘 다", **{f"{P}_GATEWAY_BASE_URL": app_base, COMPANY_URL: co_base})
    if got is not None:
        bad = moved(got, COMPANY, app_base)
        report(f"둘 다 있으면 {P}_GATEWAY_BASE_URL 이 이긴다 — 앱의 선언이 더 좁다", not bad, bad)

    # 회사 문서끼리 바닥의 꼴이 갈린다 — OpenAI 문서와 Codex 틀은 `/v1` 까지 적는다
    # (OpenAI.-Posco.Setting.md 「Chat Completions API (OpenAI)」 절의 `PGPT_BASE_URL` 문장). 운영팀이 그 꼴로 심어도
    # 같은 게이트웨이다.
    got = urls("[1] /v1 붙은 꼴", **{COMPANY_URL: co_base + "/v1/"})
    if got is not None:
        bad = moved(got, COMPANY, co_base)
        report(f"{COMPANY_URL} 에 `/v1` 이 붙어 와도 같은 바닥이다", not bad, bad)

    got = urls("[1] SDK 표준 이름", **{n: f"{SENTINEL}/sdk" for n in SDK_NAMES})
    if got is not None:
        report(f"SDK 표준 이름({' · '.join(SDK_NAMES)})은 어느 갈래도 안 옮긴다 — 회사 PC 에서 그 "
               "이름은 회사 쪽을 가리킨다",
               got == base, [f"{p}: {got[p]!r} — 기대 {base[p]!r}" for p in got if got[p] != base[p]])

    rc, out, err = child(_URLS, **{COMPANY_URL: "aigpt.posco.net/gpgpta01-gpt"})
    report(f"주소가 아닌 값은 뜰 때 죽고 {COMPANY_URL} 를 댄다 — 요청마다 넘어지면 배포는 성공으로 보인다",
           rc != 0 and COMPANY_URL in err, [f"exit {rc} · stderr 꼬리: {err.strip()[-300:]}"])


# ---------- [2] 서버 토큰 ----------

def login_slot():
    """로그인 선언의 좌표 `(모듈 이름, 속성 이름)`.

    배관에 없으면 `Missing` 의 까닭을 「못 쟀다」로 찍고 None.
    """
    try:
        mod, attr = slot("LOGIN_REQUIRED")
        get("LOGIN_REQUIRED")          # 그 자리에 실제로 있나 — 없으면 까닭을 든다
    except Missing as why:
        unmeasured("[2]·[3] 서버 토큰", f"로그인 선언이 배관에 없다 — {why}")
        return None
    return mod.__name__, attr


def _creds_code(where):
    mod, attr = where
    return (f"mod = importlib.import_module({mod!r})\n"
            "def row(p, t=None, login=False):\n"
            f"    setattr(mod, {attr!r}, login)\n"
            "    c = gateway.creds(provider=p, token=t)\n"
            "    return {'provider': c.provider, 'token': c.token, 'dry_run': c.dry_run}\n"
            "ids = list(gateway._GATEWAY)\n"
            "print(json.dumps({'off': {p: row(p) for p in ids},\n"
            "                  'on': {p: row(p, login=True) for p in ids},\n"
            f"                  'carried': {{p: row(p, {CARRIED!r}, login=True) for p in ids}}}}))\n")


def _rows(got, rows, token, dry):
    return [f"{p}: {got[p]} — 기대 token={token!r} dry_run={dry}" for p in rows
            if got[p]["token"] != token or got[p]["dry_run"] is not dry]


def token_section(where):
    print("\n[2] 서버 토큰 — 로그인을 선언한 앱의 회사 갈래에만")
    code = _creds_code(where)
    got = _load("[2] 토큰을 심은 판", *child(code, **{COMPANY_TOKEN: TOKEN}))
    if got is not None:
        bad = _rows(got["off"], COMPANY + OUTSIDE, "", True)
        report(f"로그인을 선언 안 한 앱(기본)은 {COMPANY_TOKEN} 이 있어도 안 쓴다 — 드라이런 그대로",
               not bad, bad)
        bad = _rows(got["on"], COMPANY, TOKEN, False)
        report(f"선언한 앱은 회사 갈래에 {COMPANY_TOKEN} 을 깔아 드라이런이 풀린다", not bad, bad)
        bad = _rows(got["on"], OUTSIDE, "", True)
        report("회사 토큰은 바깥 갈래로 안 나간다", not bad, bad)
        report("로컬 CLI 갈래의 구독 토큰 자리에 회사 토큰이 안 앉는다",
               all(got["on"][p]["token"] == "" for p in LOCAL),
               [f"{p}: {got['on'][p]}" for p in LOCAL])
        bad = _rows(got["carried"], COMPANY, CARRIED, False)
        report("요청이 실어 온 키가 서버 토큰을 이긴다", not bad, bad)

    got = _load("[2] 토큰 없는 판", *child(code))
    if got is not None:
        bad = _rows(got["on"], COMPANY, "", True)
        report(f"선언한 앱도 {COMPANY_TOKEN} 이 없으면 지금처럼 드라이런이다", not bad, bad)

    got = _load("[2] 회사 담장만 연 판",
                *child(code, **{COMPANY_TOKEN: TOKEN, f"{P}_SITES": gateway.SITE_POSCO}))
    if got is not None:
        bad = [f"{p}: {got['on'][p]} — 기대 token='' dry_run=True" for p in OUTSIDE
               if got["on"][p]["token"] != "" or got["on"][p]["dry_run"] is not True]
        report("담장에서 내린 요청은 선언한 앱에서도 드라이런 — 서버 토큰을 달고 나가지 않는다",
               not bad, bad)

    got = _load("[2] 드라이런 강제", *child(code, **{COMPANY_TOKEN: TOKEN, f"{P}_DRY_RUN": "1"}))
    if got is not None:
        bad = [f"{p}: {got['on'][p]}" for p in COMPANY if got["on"][p]["dry_run"] is not True]
        report(f"{P}_DRY_RUN=1 이 서버 토큰을 이긴다", not bad, bad)


# ---------- [3] 끝에서 끝 ----------

class _Seen(_Fake):
    """가짜 게이트웨이 한 벌(`gateway_probe._Fake`)에 **받은 것을 적는 손**만 더한다.

    그 가짜는 길의 첫 두 칸을 `/<국면>/<계약>` 으로 읽는다 — 그래서 바닥 주소를
    `/ok/<계약>` 으로 주면 배관이 그 뒤에 계약 경로를 붙여도 가짜가 계약을 안다.
    """
    seen = []

    def do_POST(self):
        _Seen.seen.append((self.path, dict(self.headers.items())))
        super().do_POST()


def _call_code(where, pid, login):
    mod, attr = where
    return (f"setattr(importlib.import_module({mod!r}), {attr!r}, {login!r})\n"
            f"c = gateway.creds(provider={pid!r})\n"
            "text, stop = providers.stream_once('배관 검사', [{'role': 'user', 'content': '묻는다'}],"
            " creds=c)\n"
            "print(json.dumps({'dry_run': c.dry_run, 'text': text, 'stop': stop},"
            " ensure_ascii=False))\n")


def wire_section(where):
    print("\n[3] 끝에서 끝 — 두 이름만 주고 루프백 가짜 게이트웨이까지")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Seen)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    try:
        for pid in COMPANY:
            contract = ROWS[pid]["contract"]
            floor = f"/ok/{contract}"
            _Seen.seen.clear()
            got = _load(f"[3] {pid}", *child(_call_code(where, pid, True),
                                              **{COMPANY_URL: f"http://127.0.0.1:{port}{floor}",
                                                 COMPANY_TOKEN: TOKEN}))
            if got is None:
                continue
            report(f"{pid} — 드라이런 없이 닿아 글자와 종료 신호가 돌아왔다",
                   got["dry_run"] is False and got["text"] == "".join(SAY)
                   and got["stop"] == "end_turn", [str(got)])
            paths = [path for path, _ in _Seen.seen]
            report(f"{pid} — 요청 한 건이 그 바닥 아래 계약 경로로 왔다",
                   len(paths) == 1 and paths[0].startswith(floor + PATH_OF[contract]),
                   [f"받은 길 {paths} — 기대 {floor + PATH_OF[contract]!r} 로 시작하는 한 건"])
            report(f"{pid} — 그 요청에 {COMPANY_TOKEN} 이 실려 왔다",
                   any(TOKEN in v for _, heads in _Seen.seen for v in heads.values()),
                   [f"받은 머리 이름 {[list(h) for _, h in _Seen.seen]}"])

        pid = COMPANY[0]
        _Seen.seen.clear()
        got = _load(f"[3] {pid} · 선언 안 한 앱",
                    *child(_call_code(where, pid, False),
                           **{COMPANY_URL: f"http://127.0.0.1:{port}/ok/{ROWS[pid]['contract']}",
                              COMPANY_TOKEN: TOKEN}))
        if got is not None:
            report("선언 안 한 앱은 두 이름이 있어도 한 건도 안 보낸다 — 드라이런 명세가 돌아온다",
                   got["dry_run"] is True and not _Seen.seen,
                   [f"{got} · 가짜가 받은 것 {len(_Seen.seen)}건"])
    finally:
        srv.shutdown()


def main():
    print(f"배포 환경 검사 — 나무 {ROOT} · 배관 {MODULE} · 접두어 {P}")
    if not COMPANY:
        raise Unmeasured("[안 잼] 표에 회사 담장의 갈래가 없다 — 회사 주소와 토큰을 잴 자리가 없다")
    urls_section()
    where = login_slot()
    if where is not None:
        token_section(where)
        wire_section(where)
    print()
    bad = fails()
    if bad:
        print(f"❌ {len(bad)}건 어긋남 — {' · '.join(bad)}")
        return EXIT_MISMATCH
    if unmeasureds():
        print(f"판정 {len(passes())}건 초록 · 못 잰 자리 {len(unmeasureds())} — 초록이 아니다")
        return EXIT_UNMEASURED
    print(f"✅ 판정 {len(passes())}건 초록 · 잰 범위: 주소 손잡이 · 서버 토큰 · 루프백 가짜 게이트웨이까지 "
          f"회사 갈래 {len(COMPANY)}. 사내 게이트웨이가 그 토큰을 받나는 안 쟀다")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
