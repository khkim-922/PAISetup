"""Claude 갈래의 침묵은 **생각인가 버퍼링인가** — `thinking` 을 켜고 끄며 첫 조각 시각을 가른다.

    python -X utf8 _check/claude_thinking_probe.py                 # 회사 Claude 갈래 · claude-opus-4.7
    python -X utf8 _check/claude_thinking_probe.py --model claude-opus-5
    python -X utf8 _check/claude_thinking_probe.py --budget-form   # 옛 꼴 {"type":"enabled","budget_tokens":N}
    python -X utf8 _check/claude_thinking_probe.py --no-cli        # ④ 를 안 돈다

값을 치른다(사내 키 · 토큰). 키는 갈래의 키 묶음 환경변수(`gateway._KEY_ENV`)를 읽고, 없으면
「못 쟀다」(2) 로 나간다 — 초록이 아니다. `--key` 로 줄 수도 있다. 사내 밖에서는 닿음 판정이
갈래를 먼저 비켜 세운다(2).

⚠ **빌려 온 자다** — atelier `_check/claude_thinking_probe.py`(2026-09-09 판)를 이 씨앗의 배관
  위에 다시 세웠다. 저쪽은 그 앱의 `config` 에 묶여 있어 떼어 오면 안 돈다. 앞으로는 **여기가
  진본**이고 아뜰리에는 제 앱 사정(도구·베타·중계 잡기)이 더 있어 일부러 갈렸다. 원 실측
  좌표는 아래 곁말과 claude-config `posco/ENV-posco.md` 「Claude 갈래의 생각」이 든다.

실측된 사고(2026-08-27 · 09-09 · ENV-posco 「스트림 180초 컷」): Claude Code 클라이언트가 이
게이트웨이에서 `message_start` 하나만 받고 **180초를 조용히 있다가** 빈 채 끊겨 비스트리밍으로
되받았다 — 간단한 요청에서도. 그 침묵이 무엇인지는 화면에서 안 갈린다:

  ㉮ **생각 침묵** — 모델이 생각하는 동안 게이트웨이가 `thinking_delta` 조각을 **안 넘긴다.**
     첫 글자까지의 침묵 = 생각 시간. 생각을 끄면 첫 조각이 곧 온다
  ㉯ **게이트웨이 버퍼링** — 생각과 무관하게 응답을 다 만든 뒤 한꺼번에 뱉는다. 끄나 켜나 같다

**길이 둘이다 — 같은 게이트웨이를 다른 몸으로 지난다.** 사고가 난 클라이언트(Claude Code)는
`ANTHROPIC_BASE_URL` 로 이 게이트웨이에 붙고, 이 배관의 anthropic 갈래도 같은 주소에 붙는다.
다른 것은 **요청의 꼴**이다 — 저쪽은 생각·도구·베타를 싣고 이쪽은 안 싣는다. 그래서 둘로 잰다:
  · **HTTP 갈래**(①②③⑤) — 이 배관의 봉투에 `thinking` 낱말 하나만 얹는다. 사고의 꼴을 **흉내**낸다
  · **CLI 갈래**(④) — 이 PC 의 `claude` 실행파일을 파이프로 부른다. 그 실행파일은 **셸의
    `ANTHROPIC_BASE_URL` 을 그대로 따르므로** 회사 PC 에서는 사고가 난 클라이언트와 같은 몸(요청 꼴
    · 헤더)으로 같은 게이트웨이를 지난다. 그 변수가 없으면 구독으로 나가 견줄 수 없다

**흔들어 보면 갈린다** — 같은 물음을 다섯으로 보낸다:
  ① 간단한 물음 · 생각 끔 · HTTP  — 대조군. 첫 조각이 몇 초에 오나
  ② 간단한 물음 · 생각 켬 · HTTP  — 여기서 침묵이 길면 ㉮가 아니라 게이트웨이가 `thinking` 든
                                   요청을 다르게 다루는 것이다
  ③ 생각할 거리 · 생각 켬 · HTTP  — 생각이 **선을 타나**(심장박동). 넘어오면 선이 산다
  ④ 생각할 거리 · CLI              — 같은 물음을 사고가 난 클라이언트의 몸으로. `claude` 가 없으면 건너뛴다
  ⑤ 생각할 거리 · 생각 끔 · HTTP  — 낱말 없이도 생각이 나면 **모델 기본값**이 켠 것이다(Opus 5 는 기본이
                                   켬). ③과 ⑤가 같으면 낱말은 아무 일도 안 한 것이다
⚠ 모델이 곧 변수다 — Claude Code 의 `opus` 별칭은 이 게이트웨이에서 `claude-opus-5` 로 풀린다(잡은 몸 실측
  2026-09-09). ④를 ①②③과 견주려면 `--model` 을 같은 이름으로 맞춘다.

**생각이 났나는 세 자리에서 읽는다** — 조각만 세면 못 본다. Opus 4.7 부터 생각 표시 기본이
`omitted` 라 생각 블록이 **빈 글자로** 흐른다(문서). 그래서 `content_block_start` 의 `thinking`
블록 · `thinking_delta` 조각 · `message_delta` 의 `output_tokens`(글자보다 훨씬 크면 생각이 났다 —
표시와 무관하게 셈에 든다) 셋을 다 적는다.

재는 것 — 헤더 시각 · 첫 조각(무엇이든) 시각 · 첫 생각 신호 · 첫 `text_delta` · 조각 수 · 총 시간 ·
stop · 출력 토큰. **빈 채 끝나면 벽**이다(`stop=None` · 글자 0) — 그 시각이 곧 벽의 실측이고 벽에
걸린 판은 「생각 조각이 없다」가 아니라 **「못 쟀다」** 다.
⚠ 배관의 파서를 그대로 지나되 원형은 따로 갈라 둔다(`Tee`) — `_anthropic_once` 는 `thinking_delta`
  를 안 읽으므로 조각 수는 원형에서 센다.

**실측 2026-09-09(사내 · atelier 판)** — 두 모델 × 낱말 있이·없이 × 세 판:
  · `claude-opus-4.7` 은 어떤 몸으로도 생각이 안 난다(초과 5~20 · 켜도 꺼도 CLI 몸으로도 같다).
    옛 꼴 `enabled+budget_tokens` 는 문서상 400 인데 200 이 온다 — 낱말이 모델에 닿기 전에 떨어진다
  · `claude-opus-5` 는 어떤 몸으로도 생각이 난다(초과 78~151) — 모델 기본값이 켠 것이다
  · 생각 조각은 어느 판에도 없다 — 생각한 판에도 `thinking` 블록·`thinking_delta` 가 0.
    **모델이 생각하는 동안 게이트웨이는 아무 조각도 안 흘린다.** 바깥 API 는 같은 몸에 신호를 준다
  ➔ 그래서 판정 「③ 생각이 선을 탄다」는 이 게이트웨이에서 **빨강이 실측**이다. 초록이 나오면
    게이트웨이가 바뀐 것이고, 그것이 이 자를 다시 돌리는 까닭이다.

원형은 `_check/log/claude-thinking-probe-{판}.log`, 계열은 `claude-thinking-probe-runs.log` 에
판마다 한 줄씩 쌓인다 — 침묵은 판마다 흔들려 **한 판으로는 아무것도 안 정해진다.**
"""
import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

from _verdict import Unmeasured, edge, fails, passes, report

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import gateway, providers  # noqa: E402
from live_probe import _creds  # noqa: E402  — 키 묶음 환경변수 · --key · 「못 쟀다」 물러남을 한 자리에서

LOG = ROOT / "_check" / "log"
LOG_PREFIX = "claude-thinking-probe"        # 원형 파일 이름의 앞머리 — 이 배관을 빌리는 프로브는 제 것으로 바꾼다
RUNS = LOG / "claude-thinking-probe-runs.log"
RUNS_HEAD = ("# 판마다 실측 한 줄이 쌓인다 — 이 파일만 안 덮어쓴다. 원형(`claude-thinking-probe-*.log`)은\n"
             "# 마지막 판만 산다.\n#\n# 언제 · 판 · 모델 · 손잡이 · 실측\n")
STAMP = time.strftime("%Y-%m-%d %H:%M")

CLI_PROVIDER = "claude-cli"
# 자/토큰 — 한국어 산문 실측(이 씨앗 `live_probe.py ratio` 2026-09-09 · anthropic 1.26). 어림에만 쓴다.
CHARS_PER_TOKEN = 1.26
# 생각이 났다고 볼 초과 토큰 — 출력 토큰에서 글자 몫을 뺀 것. 실측(2026-09-09 사내): 생각 없는 판은
# 5~20, 생각이 난 판은 69~151(바깥 API 는 신호와 함께 97). 그 사이에 둔다.
THINK_EXCESS_TOKENS = 40

SYSTEM = "짧고 정확하게 답한다."
SIMPLE = "배관 측정 중이다. 「확인」 한 낱말만 답해라."
HARD = ("다음 셋을 풀고 풀이를 각각 두 문장으로 적어라 — 17×23, 1부터 40까지의 합, "
        "365를 7로 나눈 몫과 나머지.")


def thinking_param(a):
    return {"type": "enabled", "budget_tokens": a.budget} if a.budget_form else {"type": "adaptive"}


def with_thinking(req, a, on):
    """배관이 지은 요청에 `thinking` 을 얹는다 — 봉투는 배관 것 그대로, 낱말 하나만 더한다.

    옛 꼴의 예산은 `max_tokens` 보다 작아야 한다(문서 규칙) — 모자라면 상한을 예산 위로 올린다.
    """
    if not on:
        return req
    body = json.loads(req.data.decode("utf-8"))
    body["thinking"] = thinking_param(a)
    if a.budget_form and body.get("max_tokens", 0) <= a.budget:
        body["max_tokens"] = a.budget + 1024
    return urllib.request.Request(req.full_url, data=json.dumps(body).encode("utf-8"),
                                  headers=dict(req.header_items()), method=req.get_method())


def fresh():
    return {"head": None, "first": None, "first_think": None, "first_text": None,
            "n_think": 0, "n_think_blocks": 0, "n_text": 0, "out_tokens": None, "think_est": None,
            "text": "", "stop": None, "error": None, "secs": 0}


def _at(v):
    """시각 하나 — 0.0초도 값이다(거짓값으로 「없음」이 되지 않게)."""
    return "없음" if v is None else f"{v}초"


def walled(r):
    """벽에 걸린 판 — 예외 없이 빈 채 끝났다(stop 도 글자도 없다)."""
    return r["stop"] is None and not r["text"] and not r["error"]


def excess(r):
    """출력 토큰에서 글자 몫을 뺀 것 — 표시와 무관하게 생각이 셈에 든 양의 어림. 못 재면 None."""
    if r["out_tokens"] is None:
        return None
    return round(r["out_tokens"] - len(r["text"]) / CHARS_PER_TOKEN)


def thought(r):
    """생각이 났다 — 블록이 섰거나 조각이 왔거나, 초과 토큰이 문턱을 넘는다."""
    if r["n_think_blocks"] or r["n_think"]:
        return True
    x = excess(r)
    return x is not None and x >= THINK_EXCESS_TOKENS


def signalled(r):
    """생각이 선을 탔다 — 블록이든 조각이든 신호가 **흐르는 동안** 왔다."""
    return bool(r["n_think_blocks"] or r["n_think"])


def count(got, s, at):
    """원형 한 줄(들)을 보고 `got` 을 채운다 — 생각 블록 · 생각 조각 · 글자 조각 · 출력 토큰 · 첫 시각."""
    if got["first"] is None:
        got["first"] = at()
    if "thinking_delta" in s:
        got["n_think"] += 1
        got["first_think"] = got["first_think"] if got["first_think"] is not None else at()
    if "content_block_start" in s and '"type": "thinking"' in s.replace('":"', '": "'):
        got["n_think_blocks"] += 1
        got["first_think"] = got["first_think"] if got["first_think"] is not None else at()
    if "text_delta" in s:
        got["n_text"] += 1
        got["first_text"] = got["first_text"] if got["first_text"] is not None else at()
    if "message_delta" in s:
        for row in s.splitlines():
            if row.startswith("data:"):
                try:
                    n = (json.loads(row[5:]).get("usage") or {}).get("output_tokens")
                except ValueError:
                    n = None
                if isinstance(n, int):
                    got["out_tokens"] = n


def line(r):
    head = "죽음" if r["head"] is None else f"{r['head']}초"
    return (f"헤더 {head} · 첫 조각 {_at(r['first'])} · 첫 생각 {_at(r['first_think'])} · "
            f"첫 글자 {_at(r['first_text'])} · 생각 블록 {r['n_think_blocks']} · 생각 조각 {r['n_think']} · "
            f"글자 조각 {r['n_text']} · 출력 토큰 {r['out_tokens'] if r['out_tokens'] is not None else '없음'}"
            + (f" · 생각 추정 {r['think_est']}" if r["think_est"] is not None else "")
            + (f" · 초과 {excess(r)}" if excess(r) is not None else "")
            + f" · 총 {r['secs']}초 · stop={r['stop']!r} · 글자 {len(r['text'])}"
            + (f" · 예외 {r['error']}" if r["error"] else ""))


def _keep(tag, model, knob, got, f):
    got["secs"] = round(got["secs"], 1)
    f.write(f"\n# --- 실측\n# {line(got)}\n")
    f.close()
    if not RUNS.exists():
        RUNS.write_text(RUNS_HEAD, encoding="utf-8")
    with RUNS.open("a", encoding="utf-8") as a:
        a.write(f"{STAMP}  {tag:12s} {model}  {knob}  {line(got)}\n")


def call(a, c, tag, ask, on):
    """HTTP 갈래 한 바퀴 — 배관으로, 요청에 `thinking` 만 얹고 원형을 갈라 조각을 센다."""
    log = LOG / f"{LOG_PREFIX}-{tag}.log"
    got = fresh()
    real = providers.urllib.request.urlopen
    f = log.open("w", encoding="utf-8")
    t0 = time.monotonic()

    def at():
        return round(time.monotonic() - t0, 1)

    class Tee:
        def __init__(self, resp):
            self._r = resp
            self.headers = resp.headers
            self.status = getattr(resp, "status", None)

        def _seen(self, s):
            count(got, s, at)

        def __iter__(self):
            for raw in self._r:
                s = raw.decode("utf-8", "replace")
                f.write(s)
                if s.strip():
                    self._seen(s)
                yield raw

        def read(self):
            data = self._r.read()
            s = data.decode("utf-8", "replace")
            f.write(s)
            self._seen(s)
            return data

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

    def opened(req, timeout=None):
        resp = real(with_thinking(req, a, on), timeout=timeout)
        got["head"] = at()
        return Tee(resp)

    providers.urllib.request.urlopen = opened
    knob = ("budget" if a.budget_form else "adaptive") if on else "끈"
    try:
        f.write(f"# provider={c.provider} model={c.model} thinking={thinking_param(a) if on else 'off'}\n\n")
        text, stop = providers.stream_once(SYSTEM, [{"role": "user", "content": ask}],
                                           on_text=lambda _p: None, creds=c)
        got["text"], got["stop"] = text, stop
    except Exception as exc:                                  # noqa: BLE001
        got["error"] = f"{type(exc).__name__}: {exc}"
        f.write(f"\n# 예외 {got['error']}\n")
    finally:
        providers.urllib.request.urlopen = real
        got["secs"] = at()
        _keep(tag, c.model, knob, got, f)
    return got


def call_cli(a, tag, ask):
    """CLI 갈래 한 바퀴 — 사고가 난 클라이언트의 몸으로. 생각은 `on_think` 신호(누적 추정 토큰)로 센다."""
    log = LOG / f"{LOG_PREFIX}-{tag}.log"
    got = fresh()
    f = log.open("w", encoding="utf-8")
    t0 = time.monotonic()

    def at():
        return round(time.monotonic() - t0, 1)

    def on_think(n):
        got["n_think"] += 1
        got["think_est"] = n                       # 누적 추정치 — 마지막 값이 생각 토큰의 어림이다
        if got["first"] is None:
            got["first"] = at()
        if got["first_think"] is None:
            got["first_think"] = at()
        f.write(f"# 생각 신호 {at()}초 · 누적 {n}\n")

    def on_usage(u):
        n = (u or {}).get("output_tokens")
        if isinstance(n, int):
            got["out_tokens"] = n

    def on_text(piece):
        got["n_text"] += 1
        if got["first"] is None:
            got["first"] = at()
        if got["first_text"] is None:
            got["first_text"] = at()
        f.write(piece)

    exe = shutil.which(gateway.CLI_EXE)
    f.write(f"# provider={CLI_PROVIDER} model={a.cli_model} exe={exe} "
            f"base_url={os.environ.get('ANTHROPIC_BASE_URL', '(없음 — 구독으로 나간다)')}\n\n")
    try:
        if not exe:
            raise RuntimeError(f"이 PC 에 {gateway.CLI_EXE} 가 없다")
        c = gateway.creds(provider=CLI_PROVIDER, model=a.cli_model)
        text, stop = providers.stream_once(SYSTEM, [{"role": "user", "content": ask}],
                                           on_text=on_text, creds=c, on_think=on_think,
                                           on_usage=on_usage)
        got["head"] = got["first"]
        got["text"], got["stop"] = text, stop
    except Exception as exc:                                  # noqa: BLE001
        got["error"] = f"{type(exc).__name__}: {exc}"
        f.write(f"\n# 예외 {got['error']}\n")
    finally:
        got["secs"] = at()
        _keep(tag, a.cli_model, "cli", got, f)
    return got


def main():
    p = argparse.ArgumentParser(description="Claude 갈래의 침묵은 생각인가 버퍼링인가 — 실호출 다섯")
    p.add_argument("--provider", default="anthropic", help="anthropic 계약의 갈래(기본: 회사 Claude)")
    p.add_argument("--model", default="claude-opus-4.7",
                   help="사고가 난 클라이언트가 쓰는 이름 그대로(기본 claude-opus-4.7)")
    p.add_argument("--budget-form", action="store_true",
                   help="②③에 옛 꼴 {type:enabled,budget_tokens} 을 싣는다. 기본은 {type:adaptive} — "
                        "Opus 4.7 이상의 유일한 켜는 꼴(문서). 옛 꼴은 4.7 에서 문서상 400 이라, 200 이 오며 "
                        "생각이 안 났으면 그 낱말은 어딘가에서 삼켜진 것이다")
    p.add_argument("--budget", type=int, default=4096, help="옛 꼴의 예산 토큰(1,024 이상)")
    p.add_argument("--cli-model", default="opus", help="④의 모델 별칭(기본 opus)")
    p.add_argument("--no-cli", action="store_true", help="④를 안 돈다")
    p.add_argument("--key", help="이 부름에 쓸 키. 없으면 키 묶음의 환경변수를 읽는다")
    a = p.parse_args()

    LOG.mkdir(parents=True, exist_ok=True)
    if not gateway.reachable(a.provider):
        raise Unmeasured(f"[안 잼] {a.provider} 에 안 닿는다 — {gateway.why_unreachable(a.provider)}")
    c = _creds(a.provider, a.key, model=a.model)
    if c.contract != gateway.CONTRACT_ANTHROPIC:
        raise Unmeasured(f"[안 잼] {a.provider} 는 anthropic 계약이 아니다 — `thinking` 낱말은 그 계약 것이다")

    print("--- Claude 갈래의 침묵은 생각인가 버퍼링인가 (사내 전용 · 실호출 다섯)")
    print(f"       HTTP 갈래 {c.provider} · 모델 {c.model} · 생각 {thinking_param(a)}")
    cli_on = not a.no_cli
    print(f"       CLI 갈래 {gateway.CLI_EXE} · 모델 {a.cli_model if cli_on else '(안 돈다)'} · "
          f"ANTHROPIC_BASE_URL {os.environ.get('ANTHROPIC_BASE_URL', '없음 — 구독으로 나간다')}")

    runs = {}
    for tag, ask, on, label in (("simple-off", SIMPLE, False, "① 간단한 물음 · 생각 끔 · HTTP (대조군)"),
                                ("simple-on", SIMPLE, True, "② 간단한 물음 · 생각 켬 · HTTP (사고의 꼴)"),
                                ("hard-on", HARD, True, "③ 생각할 거리 · 생각 켬 · HTTP"),
                                ("hard-off", HARD, False, "⑤ 생각할 거리 · 생각 끔 · HTTP (모델 기본값)")):
        print(f"\n--- {label}")
        runs[tag] = r = call(a, c, tag, ask, on)
        print(f"       {line(r)}")
    if cli_on:
        print("\n--- ④ 생각할 거리 · CLI (사고가 난 클라이언트의 몸으로 · 이 셸의 ANTHROPIC_BASE_URL 을 따른다)")
        runs["hard-cli"] = r = call_cli(a, "hard-cli", HARD)
        print(f"       {line(r)}")

    off, on, hard, hard_off = runs["simple-off"], runs["simple-on"], runs["hard-on"], runs["hard-off"]
    cli = runs.get("hard-cli")
    print("\n--- 판정")
    report("계약이 `thinking` 을 받는다 — 400 으로 되받지 않는다",
           not any("HTTP 400" in (r["error"] or "") for r in (on, hard)),
           [f"② {on['error']}", f"③ {hard['error']}",
            "400 이면 이 프록시는 그 꼴을 안 받는다 — --budget-form 을 뒤집어 다른 꼴도 재 본다"])
    # ③ 은 상태 셋이다 — 신호가 왔다 · 글자는 왔는데 생각 신호가 없다 · 벽에 걸려 아무것도
    # 안 왔다. 셋째를 둘째로 읽으면 「게이트웨이가 생각을 안 던진다」는 거짓 결론이 선다.
    if walled(hard):
        report("③ 생각이 선을 탄다 — **벽에 걸려 못 쟀다**", False,
               [f"③ 실측 {line(hard)}",
                "생각 신호가 없어서가 아니라 아무것도 안 왔다 — 「생각 켠 요청이 벽에 걸린다」가 실측이다"])
    else:
        report("③ 생각이 났다 — 블록·조각이 있거나 출력 토큰이 글자보다 훨씬 크다",
               thought(hard),
               [f"③ 실측 {line(hard)}",
                "안 났으면 `thinking` 낱말이 어딘가에서 삼켜진 것이다 — 이 판은 생각 없는 요청을 잰 셈이라 "
                "침묵의 물음에 답을 못 준다. 꼴을 바꿔(--budget-form) 다시 잰다. "
                "claude-opus-4.7 은 이 게이트웨이에서 안 나는 것이 실측(2026-09-09)이다"])
        report("③ 생각이 선을 탄다 — 생각 블록·조각이 흐르는 동안 온다(심장박동)",
               signalled(hard),
               ["생각은 났는데(출력 토큰) 신호가 없다 — 생각하는 동안 선이 조용하다. 그것이 곧 "
                "180초 벽에 걸리는 침묵이다(㉮). **이 빨강이 2026-09-09 실측이다** — 초록이면 게이트웨이가 바뀐 것",
                f"③ 실측 {line(hard)}"])
    if not walled(hard) and not walled(hard_off):
        report("⑤ 낱말이 일을 한다 — 생각 켠 판(③)과 끈 판(⑤)이 갈린다",
               thought(hard) != thought(hard_off),
               [f"③ 초과 {excess(hard)} · ⑤ 초과 {excess(hard_off)} (문턱 {THINK_EXCESS_TOKENS})",
                "둘 다 났으면 모델 기본값이 켠 것이고(낱말은 삼켜져도 상관없다), 둘 다 안 났으면 낱말이 삼켜진 "
                "것이다 — 어느 쪽이든 `thinking` 낱말은 이 게이트웨이에서 아무 일도 안 한다(2026-09-09 실측)"])
    if cli is not None:
        if cli["error"] and "없다" in cli["error"]:
            edge(f"④ 안 돌았다 — {cli['error']}. 사고가 난 클라이언트의 몸은 못 쟀다")
        elif walled(cli):
            report("④ CLI 갈래 — **벽에 걸려 못 쟀다**", False, [f"④ 실측 {line(cli)}"])
        else:
            report("④ CLI 갈래에서 생각 신호가 온다 — 사고가 난 클라이언트의 몸으로 같은 게이트웨이를 지나",
                   cli["n_think"] > 0,
                   [f"④ 실측 {line(cli)}",
                    "③은 오고 ④는 안 오면 갈림은 게이트웨이가 아니라 **요청 꼴**(도구·베타·표시)이다. "
                    "둘 다 안 오면 게이트웨이다. ANTHROPIC_BASE_URL 이 없으면 ④는 구독으로 나간 판이라 견줄 수 없다"])
    report("② 간단한 물음은 생각을 켜도 첫 조각이 곧 온다 — 켠 판이 끈 판의 3배 안",
           on["first"] is not None and off["first"] is not None and on["first"] <= max(off["first"] * 3, 5.0),
           [f"① 첫 조각 {_at(off['first'])} · ② {_at(on['first'])}",
            "②가 길면 생각 시간이 아니라 `thinking` 든 요청을 게이트웨이가 다르게 다루는 것이다(㉯ 쪽)"])
    hit = [t for t, r in runs.items() if walled(r)]
    report("벽에 걸린 판이 없다 — 빈 채 끝난 스트림 없음",
           not hit, [f"벽: {hit} — 그 판의 총 시간이 곧 벽의 실측이다. 끈 판(①)은 흐르고 켠 판만 "
                     "걸리면 침묵의 원인은 생각이 아니라 `thinking` 든 요청을 다루는 꼴이다(㉯)"])
    edge("첫 조각 시각은 판마다 흔들린다 — 한 판으로 정하지 않는다. 계열은 "
         f"{RUNS.relative_to(ROOT)} 에 쌓인다")
    edge("①②③⑤는 사고가 난 클라이언트의 요청과 같지 않다 — 도구·interleaved 베타 헤더는 여기 없다. "
         "그 몸으로 재는 것은 ④뿐이고, ④가 게이트웨이를 지나는지는 이 셸의 ANTHROPIC_BASE_URL 이 정한다. "
         "실제 몸을 중계로 잡는 자(atelier `_check/capture_proxy.py`)는 앱의 서버 자리가 필요해 여기 없다")

    print()
    bad = fails()
    if bad:
        print(f"❌ {len(bad)}건 어긋남 — {' · '.join(bad)}")
        raise SystemExit(1)
    print(f"✅ 판정 {len(passes())}건 초록 — 숫자는 runs 로그에 있다")


if __name__ == "__main__":
    main()
