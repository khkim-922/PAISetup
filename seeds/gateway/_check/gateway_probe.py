"""어댑터가 응답을 읽는 쪽 — 가짜 게이트웨이로 계약 셋, 실호출로 한 갈래를 잰다.

봉투를 **짓는** 쪽은 `envelope_check.py` 가 문다(순수 함수라 바깥으로 안 나간다). 여기는
그 반대쪽이다 — 응답이 들어와 **어댑터가 그것을 어떻게 읽나**. 그 자리는 계약마다 어휘가
달라(`stop_reason` · `finishReason` · `status`, 씀씀이 이름 셋) 통일이 무너져도 봉투는
멀쩡하고, 무너진 것은 위층의 기록과 이어받기에서야 보인다.

    python -X utf8 _check/gateway_probe.py --self-check       # 값을 안 치른다 · 망이 필요 없다
    python -X utf8 _check/gateway_probe.py                    # 기본 갈래로 실호출 한 바퀴
    python -X utf8 _check/gateway_probe.py --contract openai  # 계약을 골라 · 표의 첫 줄로
    python -X utf8 _check/gateway_probe.py --provider gemini --key …

**`--self-check` 는 값을 안 치른다.** 로컬에 가짜 SSE 게이트웨이를 띄워 계약마다 다섯 국면을
돌린다 — 성한 판 · 상한에서 이어받는 판 · 예외로 끊긴 판 · 조용히 끝난 판 · 봉투가 두 줄로
갈려 온 판. 키도 망도 안 든다.

**스위치가 없으면 실호출이다.** 키가 없으면 배관이 안 보내고 봉투 명세를 돌려주는데
(`providers.spec`), 그것을 찍고 「못 쟀다」(2)로 나간다 — 초록이 아니다. 명세를 여기서 다시
짓지 않는 까닭이 그것이다: 두 자리에 지으면 한쪽만 낡는다.

## 곁의 프로브와 어떻게 갈리나 — 넷이 같은 부름을 다른 축으로 쓴다

    gateway_probe.py     어댑터가 읽는 쪽의 계약 — 씀씀이 어휘 · 종료 어휘 · 이어받기 · 끊김
    stream_probe.py      글자가 **언제** 오나 — 첫 글자까지 · 버퍼링인가 · 벽은 어디
    live_probe.py        **숫자**를 얻는다 — 환산비 · 층 셋의 캐시 · 생각 조각 (판정을 안 낸다)
    claude_thinking_probe.py   Claude 갈래의 생각이 선을 타나

**CLI 계약은 여기 안 온다.** 저쪽은 주소도 머리도 없어(`providers.CliEnvelope`) 봉투가 통째로
다르다 — `--contract` 가 그 이름을 안 받는 것이 곧 그 경계고, 파이프 배관은 `cli_pipe_check.py`
가 문다. **그래서 이 프로브는 어떤 인자로도 진짜 CLI 를 안 부른다.**

**안 재는 것** — 캐시 경계가 **어디 서나**(봉투를 짓는 축이라 `envelope_check.py` [1] 이 든다) ·
캐시가 실제로 걸리나(`live_probe.py` ②) · 시각과 벽(`stream_probe.py`) · 게이트웨이가 모르는
낱말을 삼키나 · 사외 갈래의 출력 상한. `--self-check` 의 초록은 **「어댑터가 이 응답을 이렇게
읽는다」까지**고, 저쪽이 무엇을 주는지는 한 자도 안 잰다 — 그것을 재는 자는 실호출뿐이다.
"""
import argparse
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, report

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import gateway, providers  # noqa: E402

# 재는 검체 — 짧다. 고정 층은 앱이 얹는 것이라 씨앗이 지어낼 재료가 없고, 여기서 캐시
# 적중을 재려 들면 없는 재료를 짓는 것이 된다(그 자리는 `live_probe.py` ② 가 든다).
SYSTEM = "너는 배관 검사용 응답기다. 짧게 답한다."
ASK = "배관 점검 중이다. 「확인」 한 낱말만 답해라."
CONTINUE_ASK = "앞의 답이 상한에서 잘렸다. 잘린 자리부터 이어 써라."

# 이 프로브가 아는 계약 — CLI 는 없다(머리말의 그 경계). 초록 줄의 범위가 이 표에서
# 파생되므로 손글자를 안 둔다.
SELF_CONTRACTS = (gateway.CONTRACT_ANTHROPIC, gateway.CONTRACT_OPENAI,
                  gateway.CONTRACT_GEMINI)


def pick(contract=None, provider=None):
    """부를 갈래 하나 — 안 고르면 기본 갈래, 계약만 고르면 표에서 그 계약의 첫 줄.

    ⚠ **담장이 닫힌 갈래를 여기서 거른다.** `gateway.creds` 는 그런 갈래를 말없이 기본
      갈래로 내리고 키·모델까지 비운다(그 자리의 곁말). 안 거르면 **재려던 계약이 아닌
      것을 재는데 초록 줄은 재려던 계약의 이름을 댄다** — 빨강도 초록도 아닌 거짓말이다.
    """
    table = gateway._GATEWAY
    if provider is None and contract is None:
        provider = gateway.DEFAULT_PROVIDER
    if provider is not None:
        row = table.get(provider)
        if row is None:
            raise Unmeasured(f"[안 잼] 모르는 갈래다 — {provider} (있는 것: {' · '.join(table)})")
        if contract and row["contract"] != contract:
            raise Unmeasured(f"[안 잼] {provider} 는 {contract} 계약이 아니다 — "
                             f"{row['contract']} 다")
        if row["contract"] not in SELF_CONTRACTS:
            raise Unmeasured(f"[안 잼] {provider} 는 {row['contract']} 계약이라 이 프로브 밖이다 "
                             "— 주소도 머리도 없어 봉투가 통째로 다르다. 그 배관은 "
                             "`cli_pipe_check.py` 가 문다")
        if not gateway.site_allowed(provider):
            raise Unmeasured(f"[안 잼] {provider} 의 담장({row['site']})을 이 서버가 안 연다 — "
                             f"{gateway.ENV_PREFIX}_SITES 가 "
                             f"{' · '.join(gateway.SITES_ALLOWED)} 만 연다")
        return provider
    for slug, row in table.items():
        if row["contract"] == contract and gateway.site_allowed(slug):
            return slug
    raise Unmeasured(f"[안 잼] 이 담장이 여는 갈래 중 {contract} 계약이 없다 — 열린 담장은 "
                     f"{' · '.join(gateway.SITES_ALLOWED)} 다")


# ---------- 실호출 — 저쪽이 지금 그렇게 하더라 ----------

def live(slug, key):
    row = gateway._GATEWAY[slug]
    c = gateway.creds(provider=slug, token=key or gateway.env_token(row["key_group"]))
    msgs = [{"role": "user", "content": ASK}]
    if c.dry_run:
        # **키가 없으면 배관이 안 보내고 명세를 돌려준다** — 여기서 다시 짓지 않는다.
        said, _ = providers.stream_once(SYSTEM, msgs, creds=c)
        print(said)
        names = gateway._KEY_ENV.get(row["key_group"]) or ()
        raise Unmeasured("\n[안 잼] 키가 없어 **안 보냈다** — 위는 지어만 본 봉투 명세다. " + (
            f"`--key` 로 주거나 환경변수 {' · '.join(names)} 를 둔다" if names else
            f"`--key` 로 준다. `{row['key_group']}` 묶음은 환경변수를 안 읽는다"))
    print(f"[갈래] {slug} · {c.contract} · {c.model} · 상한 {c.max_tokens:,}")
    used, cuts = [], []
    t0 = time.monotonic()
    try:
        text, stop = providers.stream_once(
            SYSTEM, msgs, on_text=lambda s: print(s, end="", flush=True),
            creds=c, on_usage=used.append, on_cut=cuts.append)
    except RuntimeError as exc:
        # 거절(HTTP 4xx·5xx)은 어댑터가 사람 말로 접어 올린다 — 트레이스백이 아니라 그
        # 말을 그대로 보인다. 할당량 0(429)·모르는 모델(404)이 여기로 온다.
        # ⚠ **판정이 아니라 「못 쟀다」다.** 저쪽이 문을 안 열어 준 것이라 우리 배관이
        #   어긋났다는 말을 할 근거가 없다 — 빨강으로 세면 키가 만료된 날마다 빨강이다.
        print(f"\n[거절] {exc}")
        raise Unmeasured("[안 잼] 게이트웨이가 거절했다 — 위 한 줄이 저쪽의 말이다") from exc
    seen = used[-1] if used else {}
    print(f"\n[{round(time.monotonic() - t0, 2)}초] stop={stop!r} · 씀씀이={seen or '안 왔다'} "
          f"· 절단={cuts or '없다'}")
    report("글자가 왔다", bool(text.strip()), [f"{len(text)}자 — {text[:80]!r}"])
    report("종료 신호가 섰다 — Anthropic 어휘로 통일돼서", stop == "end_turn", [f"stop={stop!r}"])
    report("끊김 사유가 없다", not cuts, [str(cuts)])
    report("씀씀이가 한 어휘로 왔다 — 봉투가 몇 토큰이었나가 선다",
           isinstance(seen.get("total_input"), int) and seen["total_input"] > 0,
           [f"씀씀이={seen or '안 왔다 — 게이트웨이가 안 실었다'}"])
    edge("프로브의 초록은 「저쪽이 지금 그렇게 하더라」다 — 한 판은 사실이지 규칙이 아니다")
    edge("캐시 칸이 0 인 것은 어긋남이 아니다 — 이 검체의 고정 층이 계약의 캐시 최소 길이에 "
         "한참 못 미친다. 캐시를 재는 자는 `live_probe.py` ② 다")
    edge("씀씀이 줄이 빨강이면 우리 배관이 아니라 **게이트웨이가 안 실은 것**일 수 있다 — "
         "다음에 열 것은 어댑터가 아니라 저쪽 응답 원문이다")
    _exit(f"{slug}({c.contract} 계약)로 실호출 한 바퀴 · 시각과 벽은 `stream_probe.py` 몫이다")


# ---------- 가짜 게이트웨이 — 어댑터만 돌린다 ----------

# 같은 숫자를 계약 셋이 **다른 이름으로** 싣는다. 통일이 됐으면 셋이 같은 줄로 온다.
IN_TOTAL, CACHE_READ, CACHE_WRITE, OUT = 1502, 1000, 500, 7
SAY = ["안녕", "하세요"]
# 가짜 키 — **아스키다.** 머리는 latin-1 로 나가므로 한글 키를 넣으면 어댑터가 아니라
# `http.client` 가 먼저 넘어진다. 실물이 안 만드는 꼴로 재면 멀쩡한 코드가 빨개진다.
FAKE_KEY = "probe-fake-key"


def _sse(*objs):
    return "".join(f"data: {json.dumps(o, ensure_ascii=False)}\n\n" for o in objs)


def _frames(contract, scene, hit):
    """계약·국면별 가짜 SSE. `hit` 은 그 국면의 몇 번째 부름인가 — 이어받기가 이걸로 갈린다."""
    last = scene != "resume" or hit > 1
    say = SAY if scene != "resume" else (["앞"] if hit == 1 else ["뒤"])
    fin = "end_turn" if last else "max_tokens"
    if contract == gateway.CONTRACT_ANTHROPIC:
        # 게이트웨이가 `message_start` 에 0 을 싣고 진짜 값을 `message_delta` 에 주는 꼴을
        # 그대로 짓는다(`providers._anthropic_once` 곁말) — 그래서 이 검체가 배관의
        # **「빈 보고를 거른다」**(`_report_usage` 의 합 0 판정)도 같이 잰다.
        head = _sse({"type": "message_start", "message": {"usage": {"input_tokens": 0}}})
        body = _sse(*[{"type": "content_block_delta",
                       "delta": {"type": "text_delta", "text": s}} for s in say])
        tail = _sse({"type": "message_delta", "delta": {"stop_reason": fin},
                     "usage": {"input_tokens": IN_TOTAL - CACHE_READ - CACHE_WRITE,
                               "cache_read_input_tokens": CACHE_READ,
                               "cache_creation_input_tokens": CACHE_WRITE,
                               "output_tokens": OUT}})
        return head + body, tail
    if contract == gateway.CONTRACT_OPENAI:
        body = _sse(*[{"type": "response.output_text.delta", "delta": s} for s in say])
        done = {"status": "completed"} if last else {
            "status": "incomplete",
            "incomplete_details": {"reason": "max_output_tokens"}}
        tail = _sse({"type": "response.completed" if last else "response.incomplete",
                     "response": {**done, "usage": {
                         "input_tokens": IN_TOTAL, "output_tokens": OUT,
                         "input_tokens_details": {"cached_tokens": CACHE_READ,
                                                  "cache_write_tokens": CACHE_WRITE}}}})
        return body, tail
    body = _sse(*[{"candidates": [{"content": {"parts": [{"text": s}],
                                               "role": "model"}}]} for s in say])
    tail = _sse({"candidates": [{"content": {"parts": [{"text": ""}], "role": "model"},
                                 "finishReason": "STOP" if last else "MAX_TOKENS"}],
                 "usageMetadata": {"promptTokenCount": IN_TOTAL,
                                   "candidatesTokenCount": OUT,
                                   "cachedContentTokenCount": CACHE_READ}})
    return body, tail


class _Fake(BaseHTTPRequestHandler):
    """가짜 게이트웨이. 길의 첫 두 칸이 `/<국면>/<계약>` 이다 — Gemini 는 그 뒤에 제
    경로를 붙이므로(`providers._gm_envelope`) 앞에서 읽어야 계약 셋이 한 서버를 쓴다.

    ⚠ **청크로 보낸다 — 길이를 미리 부르지 않는다.** 스트리밍 문은 다 만들기 전에
      머리를 내보내므로 길이를 알 수가 없고, 실물이 안 쓰는 꼴로 재면 **끊김이 오는
      모양부터 달라진다**: 잘린 Content-Length 는 예외 없이 조용히 끝나고 잘린 청크는
      `IncompleteRead` 로 온다. 끊김을 재는 국면 둘이 그 차이 위에 선다.
    """
    hits = {}
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):        # 검사 출력에 서버 로그가 섞이지 않게
        pass

    def _chunk(self, text):
        raw = text.encode("utf-8")
        self.wfile.write(b"%x\r\n" % len(raw) + raw + b"\r\n")
        self.wfile.flush()

    def do_POST(self):
        self.rfile.read(int(self.headers.get("content-length") or 0))
        segs = [s for s in self.path.split("?")[0].split("/") if s]
        scene, contract = segs[0], segs[1]
        _Fake.hits[(scene, contract)] = _Fake.hits.get((scene, contract), 0) + 1
        body, tail = _frames(contract, scene, _Fake.hits[(scene, contract)])
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("transfer-encoding", "chunked")
        self.end_headers()
        self._chunk(body)
        if scene == "cut":
            # **크기를 부르고 덜 쓴 채 닫는다** — TCP 가 죽은 꼴. 예외로 온다.
            self.wfile.write(b"20\r\ndata: half")
            self.wfile.flush()
            self.close_connection = True
            return
        if scene == "quiet":
            # **규격대로 닫되 끝 프레임을 안 준다.** 예외가 아예 안 나므로, 사건이 아니라
            # 상태로 재야만 걸린다 — 그 이름은 `providers.CUT_NO_SIGNAL` 이 든다.
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
            return
        if scene == "split":
            # **봉투 하나를 두 `data:` 줄로 갈라 보낸다** — 이 게이트웨이가 긴 몸통에 하는
            # 짓이고 그 까닭은 `providers._sse_events` 곁말이 든다. 여미는 자가 없으면
            # 못 읽은 조각이 조용히 버려져 **씀씀이도 종료 사유도 통째로 증발한다.**
            first, second = _split_tail(tail)
            self._chunk(f"data: {first}\n\n")
            self._chunk(f"data: {second}\n\n")
            self.wfile.write(b"0\r\n\r\n")
            return
        self._chunk(tail)
        self.wfile.write(b"0\r\n\r\n")


def _split_tail(tail):
    """봉투 한 줄을 두 `data:` 조각으로 가른다 — split 국면과 **그 이빨이 같은 자를 쓴다.**

    가르는 규칙을 두 자리에 적으면 이빨이 국면과 다른 데를 갈라, **국면은 안 갈린 봉투를
    보내는데 이빨만 갈린 것을 보고 초록**이 난다.
    """
    payload = tail[len("data: "):].rstrip("\n")
    k = len(payload) // 2
    while payload[k] == " ":     # 갈린 자리가 공백이면 SSE 규약이 한 칸을 걷는다
        k += 1
    return payload[:k], payload[k:]


def _reads_alone(halves):
    """두 조각을 **따로** 읽어 하나라도 열리나 — 갈려 있으면 둘 다 안 열린다."""
    for half in halves:
        try:
            json.loads(half)
        except ValueError:
            continue
        return True
    return False


def _creds_at(slug, port, scene, contract):
    """그 갈래의 자격을 가짜 서버로 돌린다 — 주소 한 칸만 바꾸고 나머지는 실물 그대로."""
    return gateway.creds(provider=slug, token=FAKE_KEY)._replace(
        url=f"http://127.0.0.1:{port}/{scene}/{contract}")


# 예외로 끊긴 판과 조용히 끝난 판 — **끝나는 꼴이 둘**이라 둘 다 돈다.
CUT_SCENES = (("cut", "예외로 끊긴 판"), ("quiet", "조용히 끝난 판"))


def self_check():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]

    # 판정은 **계약의 손**이 센다 — 여기서 제 계수를 따로 지으면 초록 줄이 몇 건을 쟀는지
    # 스스로 못 말하고, 형제 검사의 셈에도 안 든다.
    def ok(name, cond, saw=""):
        report(name, cond, [saw] if saw else ())

    try:
        for contract in SELF_CONTRACTS:
            slug = pick(contract)
            print(f"[{contract}] 갈래 {slug}")
            msgs = [{"role": "user", "content": ASK}]

            # ① 봉투에 키가 안 들어간다 — 짓기와 보내기가 갈렸나.
            # ⚠ 무는 것은 **키 자리 하나**다. 나머지 머리(content-type·accept…)는 값이
            #   있는 것이 정상이라, 「다 비었나」로 물으면 재려던 것이 아닌 자리가 걸린다.
            env = providers.envelope(SYSTEM, msgs, gateway.creds(provider=slug, token=""))
            ok("봉투의 키 자리가 비었다", env.headers.get(env.key_header) == "",
               f"{env.key_header}={env.headers.get(env.key_header)!r} · "
               f"머리 {len(env.headers)}칸")
            ok("키 자리에 값을 채우면 거기만 찬다",
               providers._sealed(env, FAKE_KEY)[env.key_header]
               == env.key_fmt.format(FAKE_KEY))

            # ② 글자·종료 신호·씀씀이가 한 어휘로 온다
            used, cuts = [], []
            text, stop = providers.stream_once(
                SYSTEM, msgs, creds=_creds_at(slug, port, "ok", contract),
                on_usage=used.append, on_cut=cuts.append)
            ok("글자를 이어붙였다", text == "".join(SAY), repr(text))
            ok("종료 신호가 Anthropic 어휘로 온다", stop == "end_turn", repr(stop))
            seen = used[-1] if used else {}
            ok("씀씀이가 한 번만 왔다 — 빈 보고를 걸렀다", len(used) == 1, f"{len(used)}번")
            ok("총 입력이 계약을 안 탄다", seen.get("total_input") == IN_TOTAL, str(seen))
            ok("캐시 읽기가 그 자리로 왔다", seen.get("cache_read") == CACHE_READ, str(seen))
            ok("출력 토큰이 실렸다", seen.get("output_tokens") == OUT, str(seen))
            # 쓰기 칸은 Gemini 에 없다 — 없는 것과 0 은 여기서 같은 값으로 온다.
            ok("캐시 쓰기 칸이 섰다",
               seen.get("cache_write") == (0 if contract == gateway.CONTRACT_GEMINI
                                           else CACHE_WRITE), str(seen.get("cache_write")))
            ok("끊김 사유가 없다", not cuts, str(cuts))

            # ③ 상한에 걸리면 한 번 이어받는다
            laps = []
            text, stop = providers.stream_resumed(
                SYSTEM, msgs, CONTINUE_ASK,
                creds=_creds_at(slug, port, "resume", contract),
                on_continue=laps.append)
            ok("이어받아 붙였다", text == "앞뒤", repr(text))
            ok("이어받기가 한 번 걸렸다", laps == [1], str(laps))
            ok("이어받은 뒤 정상 종료다", stop == "end_turn", repr(stop))

            # ④ 끊긴 스트림은 사유를 내고 종료 신호가 빈다
            for scene, want in CUT_SCENES:
                cuts = []
                text, stop = providers.stream_once(
                    SYSTEM, msgs, creds=_creds_at(slug, port, scene, contract),
                    on_cut=cuts.append)
                ok(f"{want} — 받다 만 글자는 손에 남는다", text == "".join(SAY), repr(text))
                ok(f"{want} — 종료 신호가 비었다", stop is None, repr(stop))
                ok(f"{want} — 사유가 한 줄 왔다", len(cuts) == 1 and bool(cuts[0]), str(cuts))
            # 조용히 끝난 판의 사유는 **이름이 정해져 있다** — 예외 이름이 아니다.
            cuts = []
            providers.stream_once(SYSTEM, msgs,
                                  creds=_creds_at(slug, port, "quiet", contract),
                                  on_cut=cuts.append)
            ok("조용한 끝은 제 낱말로 온다", cuts == [providers.CUT_NO_SIGNAL], str(cuts))

            # ⑤ 두 줄로 갈라 온 봉투를 여민다 — 안 여미면 조용히 버려진다
            used, cuts = [], []
            text, stop = providers.stream_once(
                SYSTEM, msgs, creds=_creds_at(slug, port, "split", contract),
                on_usage=used.append, on_cut=cuts.append)
            ok("갈라 온 봉투를 여몄다 — 종료 신호가 섰다", stop == "end_turn", repr(stop))
            ok("갈라 온 봉투를 여몄다 — 씀씀이가 왔다",
               (used[-1] if used else {}).get("total_input") == IN_TOTAL, str(used))
            ok("갈라 온 봉투 — 버린 조각이 없다", not cuts, str(cuts))

            # ⑥ **이빨** — ⑤ 가 여미기를 재고 있나, 아니면 애초에 안 갈린 봉투를 재고
            #    있나. 갈린 두 줄이 **따로는 어느 쪽도 안 열린다**는 것이 그 증거다.
            #    안 보이면 ⑤ 는 「여몄다」가 아니라 무엇이든 초록이다.
            halves = _split_tail(_frames(contract, "split", 1)[1])
            ok("이빨 — 갈린 두 줄은 따로 읽으면 어느 쪽도 안 열린다",
               not _reads_alone(halves), str(halves))
    finally:
        srv.shutdown()

    _exit(f"계약 {len(SELF_CONTRACTS)}갈래({' · '.join(SELF_CONTRACTS)})의 한 바퀴 — 성한 판 · "
          "상한 이어받기 · 예외로 끊긴 판 · 조용히 끝난 판 · 갈라 온 봉투. "
          "가짜 게이트웨이라 저쪽이 무엇을 주는지는 한 자도 안 잰다")


def _exit(scope):
    """초록 줄은 **건수와 범위**를 달고 나간다 — 건수는 `passes()` 가 센다(손글자를 안 둔다)."""
    bad = fails()
    if bad:
        print(f"\n❌ {len(bad)}건 어긋남 — {' · '.join(bad)}")
        raise SystemExit(EXIT_MISMATCH)
    print(f"\n✅ 판정 {len(passes())}건 초록 · 잰 범위: {scope}")
    raise SystemExit(EXIT_OK)


def main():
    p = argparse.ArgumentParser(
        description="갈래 프로브 — 어댑터가 응답을 읽는 쪽을 잰다")
    p.add_argument("--contract", choices=list(SELF_CONTRACTS),
                   help="어떤 말로 묻나. 안 주면 기본 갈래의 계약")
    p.add_argument("--provider", help="그 계약을 여는 갈래를 골라 짚는다(기본: 표의 첫 줄)")
    p.add_argument("--key", help="이 부름에 쓸 키. 없으면 키 묶음의 표준 환경변수를 읽는다")
    p.add_argument("--self-check", action="store_true",
                   help="가짜 SSE 로 어댑터를 한 바퀴 돌린다 — 키도 망도 안 든다")
    a = p.parse_args()
    if a.self_check:
        self_check()
    else:
        live(pick(a.contract, a.provider), a.key)


if __name__ == "__main__":
    main()
