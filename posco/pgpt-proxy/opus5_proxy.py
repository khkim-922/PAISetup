"""Local compatibility proxy for the POSCO P-GPT gateway.

Serves both routes from one process:

* Claude Code   -> http://127.0.0.1:18901/gpgpta01-gpt        (no /v1)
* Codex CLI     -> http://127.0.0.1:18901/gpgpta01-gpt/v1     (with /v1)

Payload fixes, all required by the gateway:

* ``/v1/messages`` — drop a trailing assistant prefill so the conversation
  ends with a user message (the Opus 5 Bedrock route rejects prefill), and
  strip parameters that route refuses (temperature/top_p, system role).
* (ours) ``/v1/messages`` — hoist ``image`` blocks out of ``tool_result`` content
  and re-append them to the same user message, leaving a note behind. The
  gateway silently drops images nested inside ``tool_result`` (HTTP 200,
  no error), which is exactly where Claude Code's ``Read`` puts them — so
  screenshots were invisible on the corporate network. The same bytes are
  read fine as siblings of the ``tool_result`` block; placing them *before*
  it instead trips the gateway's tool_use/tool_result pairing check (400).
* (ours) ``/v1/messages`` — answer Claude Code's web search side request
  (a ``web_search_20250305`` server tool) with the gateway's Gemini
  ``googleSearch`` grounding. The gateway turns that server tool into a
  client ``tool_use`` nobody executes, so WebSearch came back empty.
* documented tool locations only — fill empty ``tools[].description``
  values, which Codex sends for gpt-5.6 class models and Azure rejects
  with minLength=1. The rest of the body, conversation history included,
  is never touched. Gemini (``/v1beta``) is excluded: its ``tools[*]``
  entries are ``{"functionDeclarations": [...]}`` and have no
  ``description`` field at all, so inventing one is a 400.
* ``/v1beta`` (Gemini CLI) — additionally send the key Gemini clients put
  in ``x-goog-api-key`` / ``?key=`` as ``Authorization: Bearer``. The
  original header and query are relayed untouched: the gateway's own
  Gemini guide relies on them, so this only adds a fallback for the
  Bearer check every other P-GPT route uses.
* Anthropic-compatible clients (Hermes ``anthropic_messages``) — if the
  request carries ``x-api-key`` and no ``Authorization``, also add
  ``Authorization: Bearer``. Hermes third-party Anthropic endpoints send
  ``x-api-key`` by default; P-GPT only accepts Bearer. The original
  ``x-api-key`` is left in place. When ``Authorization`` is already there,
  ``x-api-key`` is dropped (v16): Claude Code sends both when the user also
  has a personal ``ANTHROPIC_API_KEY``, which would otherwise travel to the
  company gateway over plain HTTP.
* Hermes ``anthropic_messages`` rewrites dotted P-GPT Claude IDs to
  Anthropic dash form (``claude-opus-4.6`` → ``claude-opus-4-6``). P-GPT
  rejects the dash form (C042 / model-not-found), so restore dots on
  ``/v1/messages``.
* Claude Code default Sonnet chip is often ``claude-sonnet-5``.
  Company P-GPT does not register that id (field issue #25), so map the
  alias to the latest registered sonnet (``claude-sonnet-4.6``).
* GPT-5 / GPT-6 / o-series OpenAI generation requests that still send
  ``max_tokens`` are rewritten to ``max_completion_tokens`` on
  ``/v1/chat/completions`` and to ``max_output_tokens`` on ``/v1/responses``.
* Hermes custom ``chat_completions`` with ``model`` starting ``gemini-``
  is translated to Gemini native ``generateContent`` and the response is
  converted back to an OpenAI chat completion. This is a chat-only
  bridge (no tool calls).

Performance (v10+):

* Upstream TCP connections are pooled with HTTP keep-alive (direct to
  ``aigpt``, never via corporate ``HTTP_PROXY``).
* Gemini ``streamGenerateContent`` SSE is reframed *as bytes arrive*
  instead of buffering the whole upstream body first.
* ``TCP_NODELAY`` on client and upstream sockets; one automatic retry when
  a pooled connection is stale.

Long turns (v18):

* Anthropic / OpenAI SSE that goes silent gets an SSE comment line every
  ``KEEPALIVE_SEC`` seconds. The gateway relays no thinking deltas, so a
  thinking turn looks like dead air to Claude Code's byte-idle watchdog,
  which aborted the stream and re-sent the whole request without streaming.
  The gateway's own 180-second execution limit on the stream path (#28) is
  *not* an idle limit and cannot be pushed back this way.
* Haiku model ids are rewritten to ``CLAUDE_HAIKU_SUBSTITUTE`` — the gateway
  lists no haiku, so Claude Code's side calls (subagents, summaries) failed
  with 400 while the main turn worked.
* An SSE ``error`` frame from the gateway is counted (``/health``
  ``stream_errors``) and logged with elapsed time and the gateway request id
  header, so the 180-second cut can be measured and reported.

Measuring the execution cut (v19):

* The gateway's 180-second cut does not always arrive as an SSE ``error``
  frame. Measured on a company PC 2026-10-02: ``HTTP 500`` at an elapsed
  180.0s, which ``stream_errors`` did not count (it stayed 0). A non-2xx
  response whose elapsed time lands near the limit is now counted as
  ``/health`` ``execution_cuts`` and logged as ``execution cut …`` with the
  gateway request id. This does not push the limit back — it makes the
  frequency countable, which is what an ops request needs.

Large requests (v22):

* The local queue is disabled by default (``PGPT_PROXY_HEAVY_BYTES=0``).
  v21's 10-second queue rejection exhausted client retries while another
  long request was running. Size alone did not identify the expensive
  calls. The proxy must not add rate limiting to normal multi-tab use.
* If explicitly enabled, requests >= ``PGPT_PROXY_HEAVY_BYTES`` queue in FIFO
  order per provider, with ``PGPT_PROXY_HEAVY_CONCURRENCY`` (default 1)
  slots each. Claude no longer blocks OpenAI, Gemini or Grok calls.
* The pre-response queue wait is bounded by ``PGPT_PROXY_HEAVY_QUEUE_TIMEOUT_SEC``
  (default 10s). A full queue returns HTTP 429 with Retry-After; it never
  bypasses the concurrency limit. Sending SSE keepalives before receiving
  upstream headers would hide real HTTP errors, so the queue stays short.
* Disconnected clients leave the queue, and cancelled requests waiting for
  upstream headers close their upstream connection. ``/health`` reports
  active requests, per-provider gates, queue timeouts and cancellations.
* Logs include model/effort/thinking settings and separate queue, upstream
  and total durations, without logging prompts or credentials. Effort is
  forwarded unchanged. Execution-cut detection excludes local queue time
  and client errors (4xx).

Everything else is relayed untouched, streaming included. Upstream 3xx
responses are relayed as-is, never followed (following would re-send the
Authorization header to whatever host Location names).

Stream integrity (v23):

* SSE is always framed as chunked downstream, including when the upstream
  sent Content-Length, so inserted keepalives cannot truncate the response.
* A bounded observer assembles complete SSE events across socket reads.
  Anthropic message_stop, Responses response.completed, and chat [DONE]
  verify completion. Explicit error/failed/incomplete events are relayed
  intact and logged as stream_error. EOF without a terminal is incomplete,
  not a successful chunked end. Oversized uninspectable terminal events
  are forwarded and reported as unverified rather than rejected.
* Keepalive counts are per request. A timed-out incomplete/error stream
  also contributes to execution_cuts, once per request.

Compaction and event boundaries (v24):

* Recognize Claude Code's exact text-only compaction prompt on /v1/messages
  and append a concise-handoff instruction. Preserve the original prompt,
  history, tools, effort and thinking. The instruction itself is a soft target;
  since v26 a separate max_tokens ceiling also applies (see below) and v25 changed
  the transport. PGPT_PROXY_COMPACT_CONCISE=0 opts out of the instruction only.
* Emit keepalive comments only between complete SSE events, never inside a
  split JSON field or CRLF. Log first event/nonempty text, output tokens and
  stop reason as metadata to distinguish response progress from HTTP headers.

Compaction transport (v25):

* Recognized compact requests use nonstream upstream by default, converted back
  to Anthropic SSE after full validation. Normal work stays streaming: the company
  gateway was observed returning empty tool arguments on its nonstream path.
* PGPT_PROXY_COMPACT_UNSTREAM=0 restores compact streaming. The diagnostic-only
  PGPT_PROXY_CLAUDE_UNSTREAM=1 expands conversion to all messages; required tool
  arguments are checked before emitting any calls. Do not enable it in production.
* This avoids the observed 180s streaming limit for compact calls only. The
  nonstream gateway still has an observed 300s limit; it is not an unlimited route.

Output ceilings (v26):

* Every Claude /v1/messages request gets max_tokens lowered (never raised) to a
  ceiling that finishes inside the gateway's limit on the route it actually takes:
  10000 when it goes upstream streaming (180s), 18000 when nonstream (300s).
  Measured 2026-10-06 over 197 Opus streaming turns: 1.2s + 13.77ms per output
  token, thinking included (worst observed 15.0ms/token, worst residual +13.7s),
  so the caps land near 165s and 285s in the worst case. The client asks 64000.
* Why: a turn that outgrows the gateway's clock was cut with HTTP 500 at 180s and
  the client re-sent the identical request up to 10 times. Ending it with
  stop_reason=max_tokens instead triggers Claude Code's own recovery ("Output token
  limit hit. Resume directly ... Break remaining work into smaller pieces."), so
  long work continues in pieces. The longest normal turn on 2026-10-06 was 7742
  tokens, so ordinary turns never reach the cap. Claude Code's compaction trigger
  is unchanged because its own max output setting is untouched.
* An enabled thinking budget is lowered to at most half the ceiling so the answer
  keeps room. /health: stream_max_tokens, nonstream_max_tokens, max_tokens_hits
  (all), compact_max_tokens_hit. PGPT_PROXY_STREAM_MAX_TOKENS=0 and
  PGPT_PROXY_NONSTREAM_MAX_TOKENS=0 restore the client's value on that route.
* Compact recognition accepts the client's prompt family: the shared
  "CRITICAL: Respond with TEXT ONLY" first line plus a "Your task is to create a
  detailed summary of" task within the first 4000 characters. This covers the
  whole-conversation, continuing-session and RECENT-portion variants and small
  rewordings of the bullets, so a client update does not silently drop compact
  calls back onto the 180s streaming path.
"""

from __future__ import annotations

import http.client
import io
import json
import os
import queue
import re
import select
import socket
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import quote, unquote_plus, urlsplit

LISTEN_HOST = "127.0.0.1"
# 시험(tests/Test-ProxyFaults.py)만 다른 포트를 쓴다. 설치기는 늘 18901 을 쓴다.
LISTEN_PORT = int(os.environ.get("PGPT_PROXY_PORT", "18901"))
# 운영 게이트웨이. 개발 게이트웨이(taigpt)나 시험용 스텁으로 바꿀 때만
# PGPT_PROXY_UPSTREAM 을 쓴다. 프로토콜은 http — https 는 연결되지 않는다.
UPSTREAM = os.environ.get("PGPT_PROXY_UPSTREAM", "http://aigpt.posco.net").rstrip("/")
ALLOWED_PREFIX = "/gpgpta01-gpt/"
# ── (우리 것) 판 번호는 두 칸이다 — **상류 판과 우리 판을 안 섞는다** ──────────────────
# 한 칸이면 **상류가 새 판을 내는 날 우리 번호와 부딪히고 번호로는 누가 새것인지 못 가른다** —
# 같은 축에 두 사람이 번호를 매기니 필연이다. 축을 둘로 가르면 그 충돌이 없어진다: 상류가 27 을
# 내면 우리 칸은 0 으로 돌아가 `27.0` 이 되고, 그것은 `26.4` 보다 뒤라는 것이 두 수를 차례로
# 견주면 그냥 나온다.
# ⚠ **`/health` 는 사람이 읽는 한 줄(`26.4`)을 내고, 견주는 자는 두 수를 따로 본다.**
#   점 찍힌 문자열을 크기로 견주면 `"9" > "10"` 이 되는 자리라, 설치기는 이 아래 두 이름을
#   각각 정수로 읽는다(`install.ps1` 의 프록시 칸).
# ⚠ **상류를 새로 받으면 위 칸을 그 판으로 올리고 아래 칸을 0 으로 되돌린다** — 우리 덩어리를
#   다시 얹은 만큼만 아래 칸이 오른다. README 「상류에서 새 판을 받을 때」.
VERSION_UPSTREAM = 26
# 우리 덩어리 넷 — 제미나이 이름 표 · 그림 끌어내기(#76) · 압축 간결 지시 끔(결정 0082) · 웹서치 메움(#118).
VERSION_OURS = 4
VERSION = f"{VERSION_UPSTREAM}.{VERSION_OURS}"
PID_PATH = Path(__file__).with_name("opus5_proxy.pid")
LOG_PATH = Path(__file__).with_name("proxy.log")
LOG_MAX_BYTES = 1_000_000
MAX_CHUNK_SIZE = 0x7FFFFFFF
MAX_SSE_EVENT_BYTES = 2 * 1024 * 1024
UPSTREAM_POOL_SIZE = 8
UPSTREAM_TIMEOUT = 600
UPSTREAM_IDLE_TTL = 30.0
SLOW_REQUEST_SEC = 5.0


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "") or default)
    except ValueError:
        return default


# (v18) Anthropic · OpenAI SSE 가 침묵할 때 클라이언트에 흘리는 SSE 주석의 간격(초). 게이트웨이는 생각(thinking)
# 구간의 조각을 전혀 흘리지 않아, Claude Code 의 바이트 유휴 워치독(회사 실측 약 60초)이 스트림을 끊고 같은 요청을
# 비스트리밍으로 다시 보냈다 — 주석 한 줄이 그 시계를 되돌린다. 게이트웨이 자체의 180초 절대 시한(#28)은 유휴가
# 아니라 실행 시계라 이것으로는 못 넘는다. PGPT_PROXY_KEEPALIVE_SEC=0 이면 끈다.
KEEPALIVE_SEC = _env_float("PGPT_PROXY_KEEPALIVE_SEC", 15.0)
_KEEPALIVE_LINE = b": keepalive\n\n"
# A soft concision instruction, only for the recognized Claude Code compact
# prompt. Effort stays the caller's; the v26 output ceilings (STREAM_MAX_TOKENS,
# NONSTREAM_MAX_TOKENS) are a separate, explicit limit for every Claude call.
# (우리 것) **기본을 끔으로 뒤집었다** — 상류는 켬이다(결정 0082). 우리는 창을 1M 으로 열어(결정 0049)
# 압축이 드물고, 드물게 하는 압축을 「3000토큰 안팎」으로 줄이면 그 긴 대화에서 잃는 것이 더 크다.
# 압축을 180초 벽 밖으로 빼는 일은 아래 COMPACT_UNSTREAM(비스트리밍 · 300초 천장)이 따로 든다.
# 켜려면 PGPT_PROXY_COMPACT_CONCISE=1.
COMPACT_CONCISE = os.environ.get("PGPT_PROXY_COMPACT_CONCISE", "0").lower() not in {"0", "false", "off"}
# Opt in until the company gateway and Claude Code have been exercised together.
CLAUDE_UNSTREAM = os.environ.get("PGPT_PROXY_CLAUDE_UNSTREAM", "0").lower() in {"1", "true", "on"}
COMPACT_UNSTREAM = os.environ.get("PGPT_PROXY_COMPACT_UNSTREAM", "1").lower() not in {"0", "false", "off"}
MAX_UNSTREAM_BYTES = 32 * 1024 * 1024
# ── (우리 것 · claude-config #118) 웹서치 메움 ────────────────────────────────────────────────────
# Claude Code 의 WebSearch 는 서버 도구(`web_search_20250305`)를 선언한 하위 요청을 보내고, 상류가 검색해
# `server_tool_use` · `web_search_tool_result` · `text` 세 칸으로 답하길 기다린다. 게이트웨이는 그 선언을
# 클라이언트 도구(`tool_use`)로 되돌려 아무도 검색하지 않는다 — CLI 는 그 칸을 못 읽어 결과 0 건이 된다
# (사내 PC 실측 2026-10-08). 그래서 프록시가 그 하위 요청을 알아보고 **게이트웨이의 제미나이 검색**
# (`googleSearch` grounding — 실측으로 실제 웹을 찾는다)으로 바꿔 보낸 뒤, 답을 세 칸으로 지어 돌려준다.
# ⚠ **Claude 를 안 거친다** — #118 본문 안(게이트웨이의 `tool_use` 를 받아 검색 결과를 `tool_result` 로 되먹이는
#   왕복)보다 상류 호출이 하나로 준다. CLI 는 이 하위 요청의 답을 결과 목록으로만 쓰고 대화에 안 넣는다.
# ⚠ **Tavily 를 안 쓴다**(#118) — 질의가 회사 밖으로 안 나가고, 외부 한도에 안 매인다.
# 끄려면 PGPT_PROXY_WEB_SEARCH=0 — 그러면 상류 그대로 중계한다(빈손).
WEB_SEARCH = os.environ.get("PGPT_PROXY_WEB_SEARCH", "1").lower() not in {"0", "false", "off"}
WEB_SEARCH_MODEL = os.environ.get("PGPT_PROXY_WEB_SEARCH_MODEL", "gemini-3.6-flash")
# CLI 가 하위 요청의 첫 user 메시지에 싣는 머리 — 떼고 남는 것이 질의다(2.1.293 바이너리).
_WEB_SEARCH_PROMPT_HEAD = "Perform a web search for the query: "
# (v26) Claude 요청의 출력 상한 — 상류 경로의 시한 안에 끝나는 크기. 2026-10-06 실측: Opus 턴은 1.2초 + 출력 토큰당
# 13.77ms(thinking 포함, 최악 15.0ms, 최대 잔차 +13.7초). 스트리밍 10000 은 최악 약 165초로 180초 안, 비스트리밍
# 18000 은 최악 약 285초로 300초 안. 넘치면 180초 HTTP 500 → 같은 요청 10번 재시도였던 것이, 이제 max_tokens 로
# 끝나 Claude Code 가 스스로 "나눠서 이어 쓰기" 로 넘어간다. 0 이면 그 경로는 클라이언트 값을 그대로 둔다.
STREAM_MAX_TOKENS = int(_env_float("PGPT_PROXY_STREAM_MAX_TOKENS", 10000))
NONSTREAM_MAX_TOKENS = int(_env_float("PGPT_PROXY_NONSTREAM_MAX_TOKENS", 18000))
_COMPACT_TASK = (
    "Your task is to create a detailed summary of the conversation so far, "
    "paying close attention to the user's explicit requests and your previous actions."
)
_COMPACT_PREAMBLE = (
    "CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.\n\n"
    "- Do NOT use Read, Bash, Grep, Glob, Edit, Write, or ANY other tool.\n"
    "- You already have all the context you need in the conversation above.\n"
    "- Tool calls will be REJECTED and will waste your only turn — you will fail the task.\n"
    "- Your entire response must be plain text: an <analysis> block followed by a <summary> block.\n\n"
)
# (v26) 알아보는 기준 — 머리 줄과 과제 문장의 앞부분. 위 두 상수는 시험과 문서의 기준 문구로 남긴다.
_COMPACT_PREAMBLE_HEAD = "CRITICAL: Respond with TEXT ONLY. Do NOT call any tools."
_COMPACT_TASK_HEAD = "Your task is to create a detailed summary of "
_COMPACT_TASK_WINDOW = 4000
_COMPACT_SUFFIX = (
    "\n\nKeep this handoff concise, ideally within 3000 output tokens. "
    "Keep <analysis> brief (at most 5 sentences) and put the useful handoff in <summary>. "
    "Preserve the user goal, constraints, file paths, key decisions, errors, verified results, "
    "unfinished work and next steps. Remove repetition and long code excerpts. "
    "Do not perform the work or call tools.\n"
)
# 게이트웨이가 응답 머리에 실어 주는 요청 번호 — slow·오류 로그에 붙여 운영팀 문의에 쓴다. 없으면 비운다.
GATEWAY_REQUEST_ID_HEADER = "x-pgpt-request-id"
# (v19) 게이트웨이의 180초 요청 실행 시한(#28)은 SSE error 프레임으로만 오지 않는다 — 회사 PC 실측
# 2026-10-02 에 `HTTP 500` + 경과 180.0초로 왔고, 프레임만 세는 stream_errors 는 그 판을 놓쳤다(0 이었다).
# 그래서 비-2xx 응답의 경과가 이 창에 들면 따로 센다(`/health` 의 execution_cuts). 시한 자체는 못 늘린다 —
# 빈도를 세어 운영팀 문의 근거를 쌓는 것이 목적이다. 창을 벗어난 느린 오류는 세지 않는다.
EXECUTION_LIMIT_SEC = _env_float("PGPT_PROXY_EXECUTION_LIMIT_SEC", 180.0)
# 시한 근방으로 볼 폭(초). 180.0 실측에 맞추되 측정 오차와 앞단 지연을 담는다.
EXECUTION_LIMIT_MARGIN_SEC = _env_float("PGPT_PROXY_EXECUTION_LIMIT_MARGIN_SEC", 5.0)
# 게이트웨이에 하이쿠가 한 판도 없다(2026-09-17 /v1/models 실측). Claude Code 는 곁 호출
# (서브에이전트 · 요약 · 빠른 판정)에 하이쿠를 제 이름으로 보내므로 그 호출이 통째로 400 이었다. 클라이언트가 아는
# 하이쿠 이름이 열 개가 넘어 목록 대신 규칙(이름에 haiku)으로 잡는다. ⚠ 게이트웨이가 하이쿠를 들이면 이 대체를 지운다.
CLAUDE_HAIKU_SUBSTITUTE = "claude-sonnet-4.6"
# v21의 10초 429가 긴 압축 중 다른 탭의 재시도 횟수를 소진했다. 기본 제한은 해제한다.
# 필요할 때만 양수 바이트 임계값을 지정해 서비스별 게이트를 켠다.
HEAVY_REQUEST_BYTES = int(_env_float("PGPT_PROXY_HEAVY_BYTES", 0))
# 서비스별 큰 요청의 동시 허용 수.
HEAVY_CONCURRENCY = int(_env_float("PGPT_PROXY_HEAVY_CONCURRENCY", 1))
# HTTP 응답 전에는 SSE 주석을 보낼 수 없다. 짧게 기다린 뒤 429로 재시도를 알린다.
# 0 이하면 자리가 없을 때 즉시 429. 게이트를 끄려면 HEAVY_BYTES=0을 쓴다.
HEAVY_QUEUE_TIMEOUT_SEC = max(0.0, _env_float("PGPT_PROXY_HEAVY_QUEUE_TIMEOUT_SEC", 10.0))
CLIENT_POLL_SEC = 0.25
HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class UpstreamPool:
    """Keep-alive pool to the P-GPT gateway.

    urllib opened a fresh TCP connection per request. On the company LAN that
    handshake alone often costs tens of milliseconds, and tool-loop chats pay
    it repeatedly. Connections go *direct* (no corporate HTTP_PROXY) — same
    reason the old opener used ProxyHandler({}).
    """

    def __init__(self, base_url: str, max_idle: int = UPSTREAM_POOL_SIZE) -> None:
        parts = urlsplit(base_url if "://" in base_url else f"http://{base_url}")
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError(f"invalid upstream URL: {base_url!r}")
        self._scheme = parts.scheme
        self._host = parts.hostname
        self._port = parts.port or (443 if parts.scheme == "https" else 80)
        self._max_idle = max_idle
        self._lock = threading.Lock()
        self._idle: list[tuple[http.client.HTTPConnection, float]] = []
        self._created = 0
        self._reused = 0
        self._expired = 0

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "upstream_idle": len(self._idle),
                "upstream_created": self._created,
                "upstream_reused": self._reused,
                "upstream_expired": self._expired,
            }

    def _open(self) -> http.client.HTTPConnection:
        if self._scheme == "https":
            conn = http.client.HTTPSConnection(
                self._host, self._port, timeout=UPSTREAM_TIMEOUT
            )
        else:
            conn = http.client.HTTPConnection(
                self._host, self._port, timeout=UPSTREAM_TIMEOUT
            )
        conn.connect()
        sock = conn.sock
        if sock is not None:
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError:
                pass
        with self._lock:
            self._created += 1
        return conn

    def acquire(self, *, fresh: bool = False) -> http.client.HTTPConnection:
        """Pooled connection. ``conn.pgpt_reused`` says whether it came from the idle pool.

        ``fresh=True`` skips the pool — the retry after a stale pooled connection must not
        pick another connection that died the same way (gateway restart, LB failover).
        """
        with self._lock:
            while self._idle and not fresh:
                conn, released_at = self._idle.pop()
                if conn.sock is not None and time.monotonic() - released_at < UPSTREAM_IDLE_TTL:
                    self._reused += 1
                    conn.pgpt_reused = True  # type: ignore[attr-defined]
                    return conn
                self._expired += 1
                try:
                    conn.close()
                except OSError:
                    pass
        conn = self._open()
        conn.pgpt_reused = False  # type: ignore[attr-defined]
        return conn

    def release(self, conn: http.client.HTTPConnection | None, *, reuse: bool) -> None:
        if conn is None:
            return
        if not reuse:
            # keepalive 판독 스레드가 read1() 에 막혀 있을 수 있다 — close() 만으로는 리눅스에서 안 깨어난다
            sock = conn.sock
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            try:
                conn.close()
            except OSError:
                pass
            return
        with self._lock:
            if len(self._idle) < self._max_idle and conn.sock is not None:
                self._idle.append((conn, time.monotonic()))
                return
        try:
            conn.close()
        except OSError:
            pass


_UPSTREAM_POOL = UpstreamPool(UPSTREAM)
_LOG_LOCK = threading.Lock()
_STATS_LOCK = threading.Lock()
_PATCHED_TOTAL = 0
_TRIMMED_PREFILLS = 0
_SLOW_TOTAL = 0
_KEEPALIVE_TOTAL = 0
_STREAM_ERROR_TOTAL = 0
_STREAM_INCOMPLETE_TOTAL = 0
_STREAM_UNVERIFIED_TOTAL = 0
_COMPACT_MAX_TOKENS_HIT_TOTAL = 0
_MAX_TOKENS_HIT_TOTAL = 0
_EXECUTION_CUT_TOTAL = 0
_HEAVY_SERIALIZED_TOTAL = 0
_HEAVY_QUEUE_TIMEOUT_TOTAL = 0
_HEAVY_WAIT_SEC_TOTAL = 0.0
_HEAVY_WAIT_MAX_SEC = 0.0
_CLIENT_CANCELLED_TOTAL = 0
_ACTIVE_REQUESTS = 0
_HOISTED_IMAGES = 0  # (우리 것 · #76) tool_result 밖으로 내놓은 그림 장수
_WEB_SEARCH_FILLED = 0  # (우리 것 · #118) 제미나이 검색으로 메운 웹서치 수
_WEB_SEARCH_FAILED = 0  # (우리 것 · #118) 메우려다 진 수 — 검색 오류 칸으로 돌려줬다


class _ClientDisconnected(Exception):
    """The downstream client cancelled before a response was sent."""


class HeavyGate:
    """서비스별 큰 요청 FIFO. 취소와 대기 만료는 상류로 보내지 않는다."""

    def __init__(self, limit: int) -> None:
        self._limit = max(1, limit)
        self._cond = threading.Condition()
        self._active = 0
        self._tickets: deque[object] = deque()

    def stats(self) -> dict[str, int]:
        with self._cond:
            return {"heavy_active": self._active, "heavy_waiting": len(self._tickets)}

    def acquire(self, timeout: float, cancelled: Callable[[], bool] | None = None) -> tuple[bool, float]:
        """Return (admitted, wait); raise on cancellation, including just before admission."""
        started = time.monotonic()
        deadline = started + max(0.0, timeout)
        ticket = object()
        with self._cond:
            self._tickets.append(ticket)
            try:
                while True:
                    if cancelled is not None and cancelled():
                        raise _ClientDisconnected()
                    if self._tickets[0] is ticket and self._active < self._limit:
                        self._active += 1
                        return True, time.monotonic() - started
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False, time.monotonic() - started
                    self._cond.wait(min(remaining, CLIENT_POLL_SEC))
            finally:
                self._tickets.remove(ticket)
                self._cond.notify_all()

    def release(self) -> None:
        with self._cond:
            self._active -= 1
            self._cond.notify_all()


_HEAVY_GATES = {name: HeavyGate(HEAVY_CONCURRENCY) for name in ("anthropic", "openai", "gemini", "xai")}


def request_provider(path: str, model: str) -> str:
    model = model.lower()
    if "/v1beta/" in path or model.startswith("gemini-"):
        return "gemini"
    if path.rstrip("/").endswith("/v1/messages") or model.startswith("claude-"):
        return "anthropic"
    if model.startswith("grok-"):
        return "xai"
    return "openai"


def request_settings(payload: dict) -> str:
    """Allowlisted settings only; never dump prompt, tools, headers or arbitrary objects."""
    def token(value: object) -> str:
        return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", value) else "unset"

    output = payload.get("output_config")
    reasoning = payload.get("reasoning")
    thinking = payload.get("thinking")
    effort = output.get("effort") if isinstance(output, dict) else None
    if effort is None:
        effort = reasoning.get("effort") if isinstance(reasoning, dict) else payload.get("reasoning_effort")
    fields = [f"model={token(payload.get('model'))}", f"effort={token(effort)}",
              f"stream={str(payload.get('stream') is True).lower()}"]
    if isinstance(thinking, dict):
        fields.append(f"thinking={token(thinking.get('type'))}")
        if type(thinking.get("budget_tokens")) is int:
            fields.append(f"budget_tokens={thinking['budget_tokens']}")
    if type(payload.get("max_tokens")) is int:
        fields.append(f"max_tokens={payload['max_tokens']}")
    return " ".join(fields)


def is_claude_compaction(payload: dict) -> bool:
    """Recognize the client's own prompt, not size, stream mode or past messages.

    Claude Code 2.1.290 can reuse the main system prompt and tool definitions
    for compact, and omits its compaction headers on this third-party route.
    Prompts outside the compact family (see _is_compact_text) pass through unchanged.
    """
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return False
    last = messages[-1]
    if not isinstance(last, dict) or last.get("role") != "user":
        return False
    content = last.get("content")
    texts = [content] if isinstance(content, str) else [
        b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
    ] if isinstance(content, list) else []
    return any(_is_compact_text(t) for t in texts)


# (v26) Claude Code 2.1.283 의 출력 한도 복구 문구. 압축이 상한에 닿으면 클라이언트는 같은 압축 안에서
# 이 문구로 이어 쓰기를 최대 3번 보낸다. 그 요청도 압축과 같은 경로(비스트리밍·300초 상한)로 보낸다.
_OUTPUT_LIMIT_RESUME_HEAD = "Output token limit hit. Resume directly"


def is_compaction_continuation(payload: dict) -> bool:
    """A client 'resume after max_tokens' turn inside a compaction.

    The last user text is the client's output-limit nudge and an earlier user
    message carries the compact prompt. Without this, the resume went out as a
    normal streaming turn while the summary it continues was still being built.
    """
    messages = payload.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        return False
    if not any(isinstance(t, str) and t.startswith(_OUTPUT_LIMIT_RESUME_HEAD) for t in _user_texts(messages[-1])):
        return False
    return any(_is_compact_text(t) for message in messages[:-1] for t in _user_texts(message))


def _user_texts(message: object) -> list:
    if not isinstance(message, dict) or message.get("role") != "user":
        return []
    content = message.get("content")
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    return []


def _is_compact_text(text: object) -> bool:
    """Match the client's compact prompt family, not one exact wording.

    v24/v25 required the full preamble + one task sentence byte for byte, so a
    reworded bullet in a Claude Code update would silently send compaction back
    to the 180s streaming path with max_tokens 64000. The Claude Code 2.1.283
    binary ships three task variants (whole conversation, continuing session,
    RECENT portion) behind one shared preamble; 2.1.291 was observed sending the
    whole-conversation variant. Require that preamble's first line at
    the very start and a summary task near it; quoted prompts still do not match.
    """
    if not isinstance(text, str) or not text.startswith(_COMPACT_PREAMBLE_HEAD):
        return False
    return _COMPACT_TASK_HEAD in text[:_COMPACT_TASK_WINDOW]


def cap_claude_output(payload: dict, *, unstream: bool) -> str:
    """Bound a Claude call's output below the gateway's time limit on its route.

    Only lowers max_tokens (and an enabled thinking budget); the prompt, history,
    tools and effort stay intact. Return a metadata-only description if changed.
    """
    cap = output_cap(unstream=unstream)
    if not cap:
        return ""
    current = payload.get("max_tokens")
    if type(current) is int and 0 < current <= cap:
        return ""
    payload["max_tokens"] = cap
    thinking = payload.get("thinking")
    if isinstance(thinking, dict) and type(thinking.get("budget_tokens")) is int and thinking["budget_tokens"] > cap // 2:
        # Anthropic requires budget_tokens < max_tokens. Keep at least half of the
        # ceiling for the summary text itself, or a long think leaves no summary.
        payload["thinking"] = {**thinking, "budget_tokens": max(1024, cap // 2)}
    return f"max_tokens_cap={cap}"


def output_cap(*, unstream: bool) -> int:
    """The max_tokens ceiling actually applied on a route (0 = off)."""
    configured = NONSTREAM_MAX_TOKENS if unstream else STREAM_MAX_TOKENS
    return max(4096, configured) if configured > 0 else 0


def tune_claude_compaction(payload: dict) -> str:
    """Append a concise-handoff instruction; retain the full original request.

    The instruction is a soft target and never truncates or invents output;
    the hard ceiling is cap_claude_output's job. Return a metadata-only description if changed.
    """
    if not COMPACT_CONCISE or not is_claude_compaction(payload):
        return ""
    last = payload["messages"][-1]
    content = last["content"]
    if isinstance(content, str):
        if content.endswith(_COMPACT_SUFFIX):
            return ""
        content = content + _COMPACT_SUFFIX
    else:
        blocks = list(content)
        for index, block in enumerate(blocks):
            if not isinstance(block, dict) or block.get("type") != "text":
                continue
            text = block.get("text")
            if _is_compact_text(text):
                if text.endswith(_COMPACT_SUFFIX):
                    return ""
                blocks[index] = {**block, "text": text + _COMPACT_SUFFIX}
                break
        content = blocks
    payload["messages"] = [*payload["messages"][:-1], {**last, "content": content}]
    return "compact_concise=true"


def is_heavy_request(path: str, body: bytes | None) -> bool:
    """이 요청이 게이트를 타야 하는가 — 모델 생성 호출이고 본문이 임계보다 큰가."""
    if HEAVY_REQUEST_BYTES <= 0 or not body or len(body) < HEAVY_REQUEST_BYTES:
        return False
    return is_generation_request(path)


def is_generation_request(path: str) -> bool:
    stripped = path.rstrip("/")
    # 생성 호출만 센다. /v1/models 같은 조회는 커도 시한에 걸리지 않는다.
    return (
        stripped.endswith("/v1/messages")
        or stripped.endswith("/v1/chat/completions")
        or stripped.endswith("/v1/responses")
        or ":generateContent" in stripped
        or ":streamGenerateContent" in stripped
    )


def _count_heavy_serialized(waited: float) -> None:
    global _HEAVY_SERIALIZED_TOTAL, _HEAVY_WAIT_SEC_TOTAL, _HEAVY_WAIT_MAX_SEC
    with _STATS_LOCK:
        _HEAVY_SERIALIZED_TOTAL += 1
        _HEAVY_WAIT_SEC_TOTAL += waited
        _HEAVY_WAIT_MAX_SEC = max(_HEAVY_WAIT_MAX_SEC, waited)


def _count_heavy_queue_timeout() -> None:
    global _HEAVY_QUEUE_TIMEOUT_TOTAL
    with _STATS_LOCK:
        _HEAVY_QUEUE_TIMEOUT_TOTAL += 1


def _count_client_cancelled() -> None:
    global _CLIENT_CANCELLED_TOTAL
    with _STATS_LOCK:
        _CLIENT_CANCELLED_TOTAL += 1


def _count_hoisted(count: int) -> None:
    global _HOISTED_IMAGES
    with _STATS_LOCK:
        _HOISTED_IMAGES += count


def _count_web_search(filled: bool) -> None:
    global _WEB_SEARCH_FILLED, _WEB_SEARCH_FAILED
    with _STATS_LOCK:
        if filled:
            _WEB_SEARCH_FILLED += 1
        else:
            _WEB_SEARCH_FAILED += 1


def _count_patched(count: int) -> None:
    global _PATCHED_TOTAL
    with _STATS_LOCK:
        _PATCHED_TOTAL += count


def _count_trimmed() -> None:
    global _TRIMMED_PREFILLS
    with _STATS_LOCK:
        _TRIMMED_PREFILLS += 1


def _count_slow() -> None:
    global _SLOW_TOTAL
    with _STATS_LOCK:
        _SLOW_TOTAL += 1


def _count_keepalive() -> None:
    global _KEEPALIVE_TOTAL
    with _STATS_LOCK:
        _KEEPALIVE_TOTAL += 1


def _count_stream_error() -> None:
    global _STREAM_ERROR_TOTAL
    with _STATS_LOCK:
        _STREAM_ERROR_TOTAL += 1


def _json_stop_reason(body: bytes | bytearray | None) -> str:
    try:
        message = json.loads(body) if body else None
    except (ValueError, UnicodeDecodeError):
        return ""
    return message.get("stop_reason") or "" if isinstance(message, dict) else ""


def _count_max_tokens_hit(compact: bool) -> None:
    global _MAX_TOKENS_HIT_TOTAL, _COMPACT_MAX_TOKENS_HIT_TOTAL
    with _STATS_LOCK:
        _MAX_TOKENS_HIT_TOTAL += 1
        if compact:
            _COMPACT_MAX_TOKENS_HIT_TOTAL += 1


def _count_stream_incomplete() -> None:
    global _STREAM_INCOMPLETE_TOTAL
    with _STATS_LOCK:
        _STREAM_INCOMPLETE_TOTAL += 1


def _count_stream_unverified() -> None:
    global _STREAM_UNVERIFIED_TOTAL
    with _STATS_LOCK:
        _STREAM_UNVERIFIED_TOTAL += 1


def _count_execution_cut() -> None:
    global _EXECUTION_CUT_TOTAL
    with _STATS_LOCK:
        _EXECUTION_CUT_TOTAL += 1


def at_execution_limit(elapsed: float) -> bool:
    """경과가 게이트웨이의 요청 실행 시한 근방인가 — 시한을 0 이하로 끄면 늘 거짓."""
    if EXECUTION_LIMIT_SEC <= 0:
        return False
    return elapsed >= EXECUTION_LIMIT_SEC - EXECUTION_LIMIT_MARGIN_SEC


def stats() -> dict[str, object]:
    with _STATS_LOCK:
        base = {
            "heavy_gate_enabled": HEAVY_REQUEST_BYTES > 0,
            "heavy_request_bytes": HEAVY_REQUEST_BYTES,
            "active_requests": _ACTIVE_REQUESTS,
            "client_cancellations": _CLIENT_CANCELLED_TOTAL,
            "patched_tools": _PATCHED_TOTAL,
            "trimmed_prefills": _TRIMMED_PREFILLS,
            "hoisted_images": _HOISTED_IMAGES,
            "web_search": WEB_SEARCH,
            "web_search_model": WEB_SEARCH_MODEL,
            "web_search_filled": _WEB_SEARCH_FILLED,
            "web_search_failed": _WEB_SEARCH_FAILED,
            "slow_requests": _SLOW_TOTAL,
            "keepalives": _KEEPALIVE_TOTAL,
            "stream_errors": _STREAM_ERROR_TOTAL,
            "stream_incomplete": _STREAM_INCOMPLETE_TOTAL,
            "stream_unverified": _STREAM_UNVERIFIED_TOTAL,
            "compact_concise": COMPACT_CONCISE,
            "claude_unstream": CLAUDE_UNSTREAM,
            "compact_unstream": COMPACT_UNSTREAM,
            "stream_max_tokens": output_cap(unstream=False),
            "nonstream_max_tokens": output_cap(unstream=True),
            "max_tokens_hits": _MAX_TOKENS_HIT_TOTAL,
            "compact_max_tokens_hit": _COMPACT_MAX_TOKENS_HIT_TOTAL,
            "execution_cuts": _EXECUTION_CUT_TOTAL,
            "heavy_serialized": _HEAVY_SERIALIZED_TOTAL,
            "heavy_queue_timeouts": _HEAVY_QUEUE_TIMEOUT_TOTAL,
            "heavy_wait_max_sec": round(_HEAVY_WAIT_MAX_SEC, 1),
            "heavy_wait_avg_sec": (
                round(_HEAVY_WAIT_SEC_TOTAL / _HEAVY_SERIALIZED_TOTAL, 1)
                if _HEAVY_SERIALIZED_TOTAL
                else 0
            ),
        }
    gates = {name: gate.stats() for name, gate in _HEAVY_GATES.items()}
    base["heavy_by_provider"] = gates
    base["heavy_active"] = sum(gate["heavy_active"] for gate in gates.values())
    base["heavy_waiting"] = sum(gate["heavy_waiting"] for gate in gates.values())
    base.update(_UPSTREAM_POOL.stats())
    return base


def log(message: str) -> None:
    """Append a line to proxy.log. Never raises; logging must not kill a request."""
    try:
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with _LOG_LOCK:
            if LOG_PATH.exists() and LOG_PATH.stat().st_size > LOG_MAX_BYTES:
                LOG_PATH.unlink(missing_ok=True)
            with LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(f"{stamp} {message}\n")
    except OSError:
        pass


class _UpstreamReadError(Exception):
    """Upstream socket/parse failure while relaying a body — wraps the original error."""


class SseObserver:
    """Observe complete SSE events without changing bytes forwarded to the client.

    Line and event boundaries can cross any read, including CRLF and UTF-8.
    Inspection is bounded; an oversized event is skipped, not buffered forever.
    If that prevents terminal verification, report unverified rather than fail
    an otherwise intact response. No generated text is searched for markers.
    """

    def __init__(self, protocol: str = "") -> None:
        self.protocol = protocol
        self.terminal = False
        self.error: str | None = None
        self.limited = False
        self._line = bytearray()
        self._data: list[bytes] = []
        self._event = b""
        self._size = 0
        self._skip = False
        self._after_cr = False
        self._line_has_bytes = False
        self.events = 0
        self.last_event = "none"
        self.first_event_at: float | None = None
        self.first_text_at: float | None = None
        self.output_tokens: int | None = None
        self.stop_reason = "none"

    @property
    def can_keepalive(self) -> bool:
        # A blank line inside an unfinished data/event would dispatch it early.
        # Also avoid inserting between CR and the LF of a split CRLF.
        return self._size == 0 and not self._line_has_bytes and not self._after_cr

    def diagnostics(self, started: float) -> str:
        def elapsed(value: float | None) -> str:
            return f"{max(0.0, value - started):.3f}s" if value is not None and started else "none"
        return (f"events={self.events} last_event={self.last_event} "
                f"first_event={elapsed(self.first_event_at)} first_text={elapsed(self.first_text_at)} "
                f"output_tokens={self.output_tokens if self.output_tokens is not None else 'unknown'} "
                f"stop_reason={self.stop_reason}")

    def feed(self, chunk: bytes) -> None:
        # Split before decoding: a UTF-8 character can straddle socket reads.
        for part in re.split(rb"([\r\n])", chunk):
            if not part:
                continue
            if part in (b"\r", b"\n"):
                if part == b"\n" and self._after_cr:
                    self._after_cr = False
                    continue
                self._after_cr = part == b"\r"
                self._end_line()
                continue
            self._after_cr = False
            self._line_has_bytes = True
            self._size += len(part)
            if self._size > MAX_SSE_EVENT_BYTES:
                self.limited = self._skip = True
                self._line.clear()
                self._data.clear()
                self._event = b""
            if not self._skip:
                self._line.extend(part)

    def _end_line(self) -> None:
        if not self._line_has_bytes:
            if not self._skip:
                self._dispatch()
            self._data.clear()
            self._event = b""
            self._size = 0
            self._skip = False
        elif not self._skip:
            field, sep, value = bytes(self._line).partition(b":")
            if value.startswith(b" "):
                value = value[1:]
            if field == b"data":
                self._data.append(value if sep else b"")
            elif field == b"event":
                self._event = value
        self._line.clear()
        self._line_has_bytes = False

    def _dispatch(self) -> None:
        if not self._data:
            return
        data = b"\n".join(self._data)
        if self.protocol == "chat" and data == b"[DONE]":
            self.terminal = True
            return
        try:
            payload = json.loads(data)
        except (UnicodeDecodeError, ValueError):
            return
        if not isinstance(payload, dict):
            return
        kind = payload.get("type") or self._event.decode("utf-8", "replace")
        self.events += 1
        now = time.monotonic()
        if self.first_event_at is None:
            self.first_event_at = now
        known = {"message_start", "message_stop", "message_delta", "content_block_start",
                 "content_block_delta", "content_block_stop", "ping", "error",
                 "response.created", "response.completed", "response.failed", "response.incomplete"}
        self.last_event = kind if isinstance(kind, str) and kind in known else "other"
        delta = payload.get("delta")
        if isinstance(delta, dict):
            if (delta.get("type") == "text_delta" and isinstance(delta.get("text"), str)
                    and delta["text"] and self.first_text_at is None):
                self.first_text_at = now
            stop = delta.get("stop_reason")
            if stop in ("end_turn", "max_tokens", "stop_sequence", "tool_use", "pause_turn", "refusal"):
                self.stop_reason = stop
        usage = payload.get("usage")
        if isinstance(usage, dict) and type(usage.get("output_tokens")) is int:
            self.output_tokens = usage["output_tokens"]
        if ((self.protocol == "anthropic" and kind == "message_stop") or
                (self.protocol == "responses" and kind == "response.completed")):
            self.terminal = True
        failed = kind in ("error", "response.failed", "response.incomplete") or self._event == b"error"
        error = payload.get("error")
        # OpenAI chat SSE can carry {"error": {...}} without an event/type field.
        failed = failed or isinstance(error, dict)
        if failed and self.error is None:
            response = payload.get("response")
            if not error and isinstance(response, dict):
                error = response.get("error") or response.get("incomplete_details")
            if isinstance(error, dict):
                message = error.get("message") or error.get("type") or error.get("reason") or kind
            else:
                message = error or kind
            self.error = " ".join(str(message).split())[:200]


def sse_error_message(chunk: bytes) -> str | None:
    """Whole-frame helper for callers/tests; live streams keep one observer across reads."""
    observer = SseObserver()
    observer.feed(chunk)
    return observer.error


def _keeps_alive(response: http.client.HTTPResponse) -> bool:
    """업스트림 연결을 풀에 돌려도 되는가. HTTP/1.1 기본은 keep-alive — close 토큰이 있을 때만 버린다."""
    conn_hdr = (response.headers.get("Connection") or "").lower()
    return "close" not in {part.strip() for part in conn_hdr.split(",") if part.strip()}


def _json_bytes(payload: dict[str, object]) -> bytes:
    try:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except UnicodeEncodeError:
        # 짝 없는 surrogate(\ud83d 등 — 클라이언트가 이모지 반쪽에서 문자열을 자른 경우)는 UTF-8 로 못 쓴다.
        # 받은 그대로 \uXXXX 로 되돌려 보낸다. 전에는 여기서 예외가 나 응답 없이 연결이 끊겼다.
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")


GEMINI_PREFIX = "/gpgpta01-gpt/v1beta"

# Gemini ``tools[*]`` 는 이 키들만 갖는다(google.ai.generativelanguage.v1beta.Tool).
# 전부 name/description 이 없는 형태라, 우리 보정이 들어가면 400 이 난다.
GEMINI_TOOL_KEYS = {
    "functionDeclarations",
    "function_declarations",
    "googleSearch",
    "google_search",
    "googleSearchRetrieval",
    "google_search_retrieval",
    "codeExecution",
    "code_execution",
    "urlContext",
    "url_context",
    "fileSearch",
    "file_search",
    "googleMaps",
    "google_maps",
    "computerUse",
    "computer_use",
    "retrieval",
}


def _is_gemini_tool(tool: dict) -> bool:
    """Gemini Tool 형태인가. 그렇다면 description 보정 대상이 아니다."""
    return any(key in tool for key in GEMINI_TOOL_KEYS)


def _fill_tool_list(tools: list) -> int:
    """빈/누락 description 을 채운다. namespace 도구의 중첩 tools 까지 내려간다.

    Gemini 형태(``{"functionDeclarations": [...]}``)는 건너뛴다 — 그 스키마에는
    ``description`` 필드가 없어서 넣으면 게이트웨이가
    ``Unknown name "description" at 'tools[0]'`` 로 400 을 낸다.
    """
    patched = 0
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            continue
        if _is_gemini_tool(tool):
            continue
        description = tool.get("description")
        if description is None or (
            isinstance(description, str) and not description.strip()
        ):
            label = tool.get("name") or tool.get("type") or f"tool_{index}"
            tool["description"] = f"{label} tool"
            patched += 1
        nested = tool.get("tools")
        if isinstance(nested, list):
            patched += _fill_tool_list(nested)
    return patched


def patch_tool_descriptions(payload: dict, path: str = "") -> int:
    """도구 정의가 실리는 문서화된 위치만 보정한다.

    Codex 는 gpt-5.6 계열 모델에게 도구 목록을 보낼 때
    ``{"type": "namespace", "name": "functions", "description": "", "tools": [...]}``
    를 포함시키고, 게이트웨이(Azure)는 description 에 minLength=1 을 강제해
    빈 문자열 하나로 요청 전체가 400 이 된다. gpt-5.5 는 이 항목을 보내지
    않아 증상이 없다.

    본문 전체를 재귀하면 대화 히스토리(tool_use input 등) 안에 우연히 든
    "tools" 키 리스트까지 변조하므로, 최상위 ``tools`` 와 Responses API 의
    ``input[*].tools`` 두 위치만 본다.

    Gemini 경로는 보정 자체가 해롭다 — ``_fill_tool_list`` 가 형태로도
    걸러내지만, 호출부가 경로를 알 때는 아예 건너뛰게 한다.
    """
    if path and path.startswith(GEMINI_PREFIX):
        return 0
    patched = 0
    tools = payload.get("tools")
    if isinstance(tools, list):
        patched += _fill_tool_list(tools)
    items = payload.get("input")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("tools"), list):
                patched += _fill_tool_list(item["tools"])
    return patched


def normalize_openai_token_limit(payload: dict[str, object], path: str = "") -> bool:
    """Normalize legacy token limits for GPT-5/6 and o-series routes.

    The newer GPT 5.x/6.x and o-series chat routes reject ``max_tokens`` with
    ``Unsupported parameter: 'max_tokens'``.  Older GPT-4.x/Grok routes still
    accept ``max_tokens``.  Only rewrite OpenAI-compatible generation requests
    for the model families known to require the newer parameter, and leave
    Claude/Gemini paths untouched.
    """
    normalized_path = path.rstrip("/")
    if not (
        normalized_path.endswith("/v1/chat/completions")
        or normalized_path.endswith("/v1/responses")
    ):
        return False
    model = str(payload.get("model") or "")
    if not re.match(r"^(?:gpt-[56](?:[.\-]|$)|o[34](?:-|$))", model):
        return False
    target = "max_output_tokens" if normalized_path.endswith("/v1/responses") else "max_completion_tokens"
    if "max_tokens" not in payload:
        return False
    legacy_limit = payload.pop("max_tokens")
    payload.setdefault(target, legacy_limit)
    return True


# Hermes anthropic_messages 가 P-GPT 점 표기(claude-opus-4.6) 를 Anthropic
# 대시 표기(claude-opus-4-6) 로 바꿔 보낸다. 게이트웨이는 점만 받는다.
# 계열 이름(opus · sonnet · haiku · fable …)은 고정하지 않는다 — 새 계열이 나와도 프록시를 고칠 일이 없게.
_CLAUDE_DASH_VERSION = re.compile(
    r"^(claude-[a-z]+-\d+)-(\d+)(.*)$",
    re.IGNORECASE,
)

# ── (우리 것) 안티그래비티가 제목 짓기에 못박아 둔 이름 하나 ──────────────────────────
# 하이쿠 칸(CLAUDE_HAIKU_SUBSTITUTE)과 **같은 병이다** — 클라이언트가 곁 호출에 제 이름을 보내고
# 게이트웨이에 그 판이 없어 그 호출만 진다. 여기도 `--model` 이 메인 턴만 못박고 곁 호출은 그 못을
# 안 탄다.
# **그런데 약이 다르다.** 하이쿠는 게이트웨이에 한 판도 없어 다른 모델로 갈아야 했지만, 이쪽은
# **같은 모델이 이름만 다르게 등록돼 있다** — 접미사 `-preview` 하나가 임자다(실측 2026-09-17 ·
# 직결: `gemini-3.1-flash-lite` 는 200 에 `modelVersion: gemini-3.1-flash-lite` · `-preview`
# 붙은 것은 400 「모델을 찾을 수 없습니다」). 그래서 성능을 안 깎고 이름만 고친다.
# ⚠ **접미사를 규칙으로 떼지 않고 이름으로 잡는다** — 하이쿠 칸과 반대로 가는 자리다.
#   `-preview` 를 무조건 떼면 **게이트웨이에 실제로 있는** `gemini-3.1-pro-preview` 를 깨뜨린다
#   (같은 날 실측: 그 이름으로 본 턴이 통했다). 새는 쪽과 깨뜨리는 쪽 중 **깨뜨리지 않는 쪽으로
#   기운다** — 곁 호출 하나가 지면 제목이 안 붙을 뿐이고, 본 턴이 지면 아무것도 안 된다.
# ⚠ **`agy` 쪽에 이것을 갈 손잡이가 없다** — 바이너리에 상수로 박혀 있고 `titleModel` 류의 설정이
#   없다. 그래서 고칠 자리가 클라이언트가 아니라 여기다.
# ⚠ **걷는 날은 사람이 정한다** — 게이트웨이가 `-preview` 판을 들이거나 `agy` 가 이름을 고치면
#   이 줄이 쓸모없어진다. `/v1/models` 에 그 이름이 보이면 이 칸을 지운다.
_GEMINI_MODEL_ALIASES = {
    "gemini-3.1-flash-lite-preview": "gemini-3.1-flash-lite",
}

# Claude Code 2.1+ Sonnet chip. Not on the company gateway list.
_CLAUDE_MODEL_ALIASES = {
    "claude-sonnet-5": "claude-sonnet-4.6",
    "claude-sonnet-latest": "claude-sonnet-4.6",
    "claude-3-7-sonnet-latest": "claude-sonnet-4.6",
    "claude-3-5-sonnet-latest": "claude-sonnet-4.5",
    "claude-opus-latest": "claude-opus-5",
}


def normalize_pgpt_claude_model(model: str) -> str:
    """Restore dotted Claude IDs and map aliases the gateway does not list."""
    if not isinstance(model, str):
        return model
    name = model.strip()
    if not name:
        return model
    lower = name.lower()
    alias = _CLAUDE_MODEL_ALIASES.get(lower)
    if alias:
        return alias
    # (v18) 하이쿠는 게이트웨이에 없다 — 대시→점 변환보다 먼저 본다(그쪽을 먼저 타면 claude-haiku-4.5 가 되어
    # 여전히 없는 이름이다)
    if "haiku" in lower:
        return CLAUDE_HAIKU_SUBSTITUTE
    # dated Anthropic ids: claude-sonnet-5-20260219
    if lower.startswith("claude-sonnet-5"):
        return "claude-sonnet-4.6"
    if "." in name:
        return name
    match = _CLAUDE_DASH_VERSION.match(name)
    if not match:
        return name
    return f"{match.group(1)}.{match.group(2)}{match.group(3)}"


def normalize_claude_model_id(payload: dict[str, object], path: str = "") -> bool:
    """Restore P-GPT's dotted Claude minor-version IDs on Messages requests."""
    if not path.rstrip("/").endswith("/v1/messages"):
        return False
    model = payload.get("model")
    if not isinstance(model, str):
        return False
    fixed = normalize_pgpt_claude_model(model)
    if fixed == model:
        return False
    payload["model"] = fixed
    return True


def _text_from_openai_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(part for part in parts if part)
    return ""


def openai_chat_to_gemini_payload(payload: dict[str, object]) -> dict[str, object]:
    """Translate a simple OpenAI chat completion body to Gemini native JSON."""
    contents: list[dict[str, object]] = []
    system_parts: list[str] = []
    for message in payload.get("messages") or []:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user")
        text = _text_from_openai_content(message.get("content"))
        if not text.strip():
            continue
        if role == "system":
            system_parts.append(text)
            continue
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": text}]})
    if system_parts:
        contents.insert(0, {"role": "user", "parts": [{"text": "\n".join(system_parts)}]})
    if not contents:
        contents = [{"role": "user", "parts": [{"text": ""}]}]

    generation_config: dict[str, object] = {}
    max_tokens = payload.get("max_completion_tokens", payload.get("max_tokens"))
    if isinstance(max_tokens, int) and max_tokens > 0:
        generation_config["maxOutputTokens"] = max_tokens
    for src, dst in (("temperature", "temperature"), ("top_p", "topP")):
        value = payload.get(src)
        if isinstance(value, (int, float)):
            generation_config[dst] = value

    out: dict[str, object] = {"contents": contents}
    if generation_config:
        out["generationConfig"] = generation_config
    return out


def gemini_response_to_openai_chat(raw: bytes, model: str) -> bytes:
    """Translate Gemini generateContent JSON to an OpenAI chat completion JSON."""
    try:
        data = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, ValueError):
        return raw
    if not isinstance(data, dict) or "candidates" not in data:
        return raw
    parts = []
    finish_reason = "stop"
    candidates = data.get("candidates") or []
    if candidates and isinstance(candidates[0], dict):
        cand = candidates[0]
        finish = str(cand.get("finishReason") or "STOP").lower()
        finish_reason = "length" if finish == "max_tokens" else "stop"
        content = cand.get("content") or {}
        if isinstance(content, dict):
            for part in content.get("parts") or []:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    parts.append(part["text"])
    payload = {
        "id": f"chatcmpl-gemini-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "".join(parts)},
            "finish_reason": finish_reason,
        }],
    }
    usage = data.get("usageMetadata")
    if isinstance(usage, dict):
        payload["usage"] = {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens": usage.get("totalTokenCount", 0),
        }
    return _json_bytes(payload)


def gemini_response_to_openai_stream(raw: bytes, model: str) -> bytes:
    """Translate one Gemini response to a complete OpenAI SSE stream."""
    converted = gemini_response_to_openai_chat(raw, model)
    try:
        chat = json.loads(converted.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return converted
    choices = chat.get("choices") or []
    choice = choices[0] if choices and isinstance(choices[0], dict) else {}
    message = choice.get("message") or {}
    content = message.get("content") if isinstance(message, dict) else ""
    finish_reason = choice.get("finish_reason") or "stop"
    base = {
        "id": chat.get("id"),
        "object": "chat.completion.chunk",
        "created": chat.get("created"),
        "model": model,
    }
    chunks: list[bytes] = []
    if content:
        item = dict(base)
        item["choices"] = [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}]
        chunks.append(b"data: " + _json_bytes(item) + b"\n\n")
    final = dict(base)
    final["choices"] = [{"index": 0, "delta": {}, "finish_reason": finish_reason}]
    if isinstance(chat.get("usage"), dict):
        final["usage"] = chat["usage"]
    chunks.append(b"data: " + _json_bytes(final) + b"\n\n")
    chunks.append(b"data: [DONE]\n\n")
    return b"".join(chunks)


def _content_blocks(content: object) -> list[dict[str, object]]:
    if isinstance(content, str):
        return [{"type": "text", "text": content}] if content.strip() else []
    if not isinstance(content, list):
        return []

    blocks: list[dict[str, object]] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and not str(block.get("text", "")).strip():
            continue
        blocks.append(block)
    return blocks


# ── (우리 것) tool_result 안의 그림을 그 블록 **뒤로** 내놓는다 (claude-config #76) ──────
#   게이트웨이는 `tool_result` **안**의 `image` 블록을 200 에 조용히 버린다 — 400 이 아니라
#   받아 놓고 픽셀을 버리므로, 읽는 쪽은 「도구가 빈 결과를 냈다」로 읽고 색을 지어낸다.
#   Claude Code 의 `Read` 가 그림을 바로 그 자리에 싣기 때문에 **사내에서는 그림을 못 봤다.**
#
#   눈가림 실측 (2026-09-22 · 답을 곁 파일에만 적은 320×320 검체 · `claude-opus-5` · 두 판).
#   같은 그림·같은 물음인데 **그림이 놓인 자리만으로** 갈렸다:
#     · `tool_result.content` 안에 [text, image] 또는 image 하나만  → **못 본다**
#     · 같은 user 메시지에서 `tool_result` **뒤**에 형제 블록으로    → **본다** ← 이 함수의 꼴
#     · `tool_result` 뒤 별개 user 메시지                            → 본다 (아래 ⚠ 가 안 쓰는 까닭)
#     · 같은 메시지에서 `tool_result` **앞**에                       → **400** — 짝 검사가 위치를
#       본다: `messages.N: tool_use ids were found without tool_result blocks`
#     · OpenAI 라우트 `image_url`                                    → 색은 맞고 **자리를 틀렸다**
#   마지막 것을 우회로 안 쓴다 — 200 을 내면서 틀린 답을 자신 있게 내므로, **반쯤 보는 것이
#   못 보는 것보다 비싸다.**
#
# ⚠ **`tool_result` 를 지우지 않는다.** 앞 턴의 `tool_use` 와 짝이 깨지면 위 400 이 난다.
#   블록 **안의 그림만** 빼고, 빈 자리에는 어디로 갔는지 적은 글자를 남긴다 — 안 남기면
#   모델이 「도구가 실패했다」로 읽어, 그림이 따라와도 그것을 안 믿는다.
# ⚠ **`tool_result` 보다 앞에 끼우지 않는다** — 위 400 이 그 자리다. 뽑은 그림은 그 메시지의
#   **끝**으로 간다: `tool_result` 가 여럿이면 다 지난 뒤가 유일하게 안전한 자리다.
# ⚠ **메시지를 새로 만들지 않는다.** 새로 끼우면 user 가 잇달아 서고, 아래 `sanitize_payload` 의
#   합치기가 그 둘을 **도로 한 메시지로 접는다** — 접히면 결과는 같지만 거치는 갈래가 늘고,
#   무엇보다 `tool_result` 가 마지막인 대화(도구 결과를 받고 모델이 답할 차례 · `Read` 의
#   실제 꼴)에서는 얹을 다음 메시지가 **아예 없다.** 같은 메시지 안에 두면 그 갈래가 안 선다.
# ⚠ **`tool_result` 가 여럿이면 짝을 글자로 댄다** — 그림이 어느 도구 것인지 순서로만 남는
#   자리라, 자리표시가 `tool_use_id` 를 든다. 안 대면 그림 둘이 뒤바뀌어도 아무도 모른다.
def hoist_tool_result_images(messages: list[object]) -> int:
    """`tool_result` 안의 `image` 를 **같은 메시지의 끝**으로 내놓는다. 옮긴 장수를 낸다."""
    moved = 0
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue

        pulled: list[dict[str, object]] = []
        for result in content:
            if not isinstance(result, dict) or result.get("type") != "tool_result":
                continue
            inner = result.get("content")
            if not isinstance(inner, list):
                continue
            kept: list[dict[str, object]] = []
            taken = 0
            for block in inner:
                if isinstance(block, dict) and block.get("type") == "image":
                    pulled.append(block)
                    taken += 1
                else:
                    kept.append(block)
            if not taken:
                continue
            label = "그림 %d장" % taken if taken > 1 else "그림"
            kept.append({"type": "text",
                         "text": "[%s은 이 도구 결과(%s) 것이고 이 메시지 끝에 실려 있다]"
                                 % (label, result.get("tool_use_id") or "?")})
            result["content"] = kept

        if not pulled:
            continue
        content.extend(pulled)
        moved += len(pulled)
    return moved


def sanitize_payload(payload: dict[str, object]) -> dict[str, object]:
    """Anthropic /v1/messages 본문을 Bedrock 라우트가 받는 형태로 정리한다."""
    payload.pop("temperature", None)
    payload.pop("top_p", None)

    raw_messages = payload.get("messages")
    if isinstance(raw_messages, list):
        # (우리 것) ⚠ **아래 합치기보다 먼저 선다.** 이 함수는 한 메시지 안에서만 블록을 옮기므로
        #   합치기와 다투지 않지만, 순서가 뒤면 합쳐진 메시지를 다시 훑어 **같은 일을 두 번 재게**
        #   된다. 여기가 이 함수의 유일한 자리다 (claude-config #76).
        hoisted = hoist_tool_result_images(raw_messages)
        if hoisted:
            _count_hoisted(hoisted)

        cleaned: list[dict[str, object]] = []
        for raw_message in raw_messages:
            if not isinstance(raw_message, dict):
                continue
            role = raw_message.get("role")
            if role == "system":
                role = "user"
            if role not in {"user", "assistant"}:
                continue
            blocks = _content_blocks(raw_message.get("content"))
            if not blocks:
                continue
            if cleaned and cleaned[-1]["role"] == role:
                previous = cleaned[-1]["content"]
                if isinstance(previous, list):
                    previous.extend(blocks)
            else:
                cleaned.append({"role": role, "content": blocks})

        while cleaned and cleaned[0]["role"] != "user":
            cleaned.pop(0)
        trimmed_prefill = False
        while cleaned and cleaned[-1]["role"] != "user":
            cleaned.pop()
            trimmed_prefill = True
        if trimmed_prefill:
            _count_trimmed()
        payload["messages"] = cleaned

    return payload


def normalize_gemini_auth(
    path: str, query: str, headers: dict[str, str]
) -> tuple[str, dict[str, str]]:
    """Gemini 계열 요청에 Bearer 인증을 덧붙인다.

    Gemini CLI 는 키를 ``x-goog-api-key`` 헤더(또는 ``?key=``)로 보내고
    사내 가이드의 직결 설정도 그대로 동작한다. 다만 P-GPT 의 다른 경로는
    전부 ``Authorization: Bearer`` 를 보므로, 그쪽만 검사하는 라우트에서도
    통하도록 Bearer 를 **추가**한다. 원래 헤더·쿼리는 건드리지 않는다 —
    떼어내면 헤더를 보는 게이트웨이에서 401 이 난다.
    """
    if not path.startswith(GEMINI_PREFIX):
        return query, headers
    if any(name.lower() == "authorization" for name in headers):
        return query, headers

    key = None
    for part in query.split("&"):
        if part.startswith("key="):
            key = unquote_plus(part[4:])
    for name, value in headers.items():
        if name.lower() == "x-goog-api-key" and value.strip():
            key = value.strip()
            break

    if key:
        headers = dict(headers)
        headers["Authorization"] = f"Bearer {key}"
    return query, headers


def normalize_anthropic_auth(headers: dict[str, str]) -> dict[str, str]:
    """Hermes 등 Anthropic 호환 클라이언트의 ``x-api-key`` 를 Bearer 로 보강한다.

    Hermes 의 third-party ``anthropic_messages`` 경로는 기본이 ``x-api-key`` 이고,
    P-GPT 게이트웨이는 Bearer 만 본다. Gemini 경로와 같이 원래 헤더는 남기고
    ``Authorization`` 만 덧붙인다.

    이미 Authorization 이 있으면 x-api-key 는 뺀다(v16). 게이트웨이는 Bearer 만 보는데, 사용자 환경에
    개인 ANTHROPIC_API_KEY 가 있으면 Claude Code 가 두 헤더를 함께 보내 개인 키가 평문 HTTP 로
    사내 게이트웨이까지 갔다.
    """
    if any(name.lower() == "authorization" for name in headers):
        if any(name.lower() == "x-api-key" for name in headers):
            return {name: value for name, value in headers.items() if name.lower() != "x-api-key"}
        return headers

    key = None
    for name, value in headers.items():
        if name.lower() == "x-api-key" and value.strip():
            key = value.strip()
            break
    if not key:
        return headers

    headers = dict(headers)
    headers["Authorization"] = f"Bearer {key}"
    return headers


def normalize_gemini_model_path(path: str) -> str:
    """Remove Gemini CLI's virtual ``-customtools`` model suffix.

    Gemini CLI 0.55 adds this suffix when tools are enabled, but P-GPT only
    registers the underlying model ID.  The suffix is a client-side routing
    hint, not a distinct gateway model.
    """
    if not path.startswith(f"{GEMINI_PREFIX}/models/"):
        return path
    marker = ":"
    model_start = path.find("/models/") + len("/models/")
    model_end = path.find(marker, model_start)
    if model_end < 0:
        model_end = len(path)
    model = path[model_start:model_end]
    base_model = model
    suffix = "-customtools"
    if base_model.endswith(suffix):
        base_model = base_model[: -len(suffix)]
    # (우리 것) 안티그래비티의 제목 짓는 호출만 없는 이름으로 온다 — 그 하나를 이름으로 잡는다.
    base_model = _GEMINI_MODEL_ALIASES.get(base_model, base_model)
    if base_model == model:
        return path
    normalized = path[:model_start] + base_model + path[model_end:]
    log(f"Gemini model alias normalized: {model} -> {base_model}")
    return normalized


class GeminiSseJoiner:
    """Join gateway-split Gemini ``data:`` fragments as bytes arrive.

    P-GPT sometimes wraps a large Gemini JSON object (notably a long
    ``thoughtSignature``) across several physical SSE ``data:`` lines.  The
    Gemini CLI treats every line as a complete JSON segment and fails with
    ``Incomplete JSON segment at the end``.

    v9 buffered the entire upstream body before emitting anything — Gemini
    first-token latency paid the full generation time.  This joiner emits
    each complete event as soon as its JSON parses.
    """

    def __init__(self) -> None:
        self.pending = b""
        self.fragment_count = 0
        self.joined_fragments = 0
        self._buf = b""

    def feed(self, chunk: bytes) -> list[bytes]:
        if not chunk:
            return []
        self._buf += chunk
        events: list[bytes] = []
        while True:
            nl = self._buf.find(b"\n")
            if nl < 0:
                break
            line = self._buf[:nl]
            self._buf = self._buf[nl + 1 :]
            if line.endswith(b"\r"):
                line = line[:-1]
            events.extend(self._feed_line(line))
        return events

    def finish(self) -> list[bytes]:
        events: list[bytes] = []
        if self._buf.strip():
            events.extend(self._feed_line(self._buf.strip()))
            self._buf = b""
        if self.pending:
            events.append(b"data: " + self.pending + b"\n\n")
            self.pending = b""
        return events

    def _feed_line(self, line: bytes) -> list[bytes]:
        if not line:
            return []
        if line.startswith(b"data:"):
            fragment = line[5:].lstrip()
        elif self.pending:
            fragment = line
        else:
            return []

        if fragment == b"[DONE]":
            out: list[bytes] = []
            if self.pending:
                out.append(b"data: " + self.pending + b"\n\n")
                self.pending = b""
                self.fragment_count = 0
            out.append(b"data: [DONE]\n\n")
            return out

        self.pending += fragment
        self.fragment_count += 1
        try:
            json.loads(self.pending.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return []

        if self.fragment_count > 1:
            self.joined_fragments += self.fragment_count - 1
        event = b"data: " + self.pending + b"\n\n"
        self.pending = b""
        self.fragment_count = 0
        return [event]


def reframe_gemini_sse(raw: bytes) -> tuple[bytes, int]:
    """Buffering helper used by self-test. Live traffic uses GeminiSseJoiner."""
    joiner = GeminiSseJoiner()
    parts = joiner.feed(raw)
    parts.extend(joiner.finish())
    return b"".join(parts), joiner.joined_fragments


def anthropic_message_events(message: object, *, tools: list | None = None, allow_tools: bool = True) -> list[bytes]:
    """Convert a complete message, validating everything before exposing any tool call.

    Input JSON travels in input_json_delta (including large Unicode strings), never
    in the empty tool_use start block where SDKs would discard it. Unknown block
    types fail explicitly instead of silently losing model output.
    """
    if not isinstance(message, dict) or message.get("type") != "message":
        raise ValueError("Expected an Anthropic message")
    if (not isinstance(message.get("content"), list) or not message.get("id")
            or not message.get("model") or message.get("role") != "assistant"
            or not message.get("stop_reason") or not isinstance(message.get("usage"), dict)):
        raise ValueError("Incomplete Anthropic message metadata")
    events: list[bytes] = []

    def emit(kind: str, **fields: object) -> None:
        events.append(b"event: " + kind.encode("ascii") + b"\ndata: "
                      + _json_bytes({"type": kind, **fields}) + b"\n\n")

    start = dict(message, content=[], stop_reason=None, stop_sequence=None)
    start["usage"] = dict(message["usage"], output_tokens=0)
    emit("message_start", message=start)
    for index, block in enumerate(message["content"]):
        if not isinstance(block, dict):
            raise ValueError("Invalid content block")
        kind = block.get("type")
        initial = dict(block)
        deltas: list[tuple[str, str, str]] = []
        if kind == "text":
            if not isinstance(block.get("text"), str):
                raise ValueError("Invalid text block")
            initial["text"] = ""
            deltas.append(("text_delta", "text", block["text"]))
        elif kind in {"tool_use", "server_tool_use"}:
            if not allow_tools:
                raise ValueError("Compaction must not execute tools")
            if not block.get("id") or not block.get("name") or not isinstance(block.get("input"), dict):
                raise ValueError("Invalid tool input")
            if tools is not None and kind == "tool_use":
                definition = next((tool for tool in tools if isinstance(tool, dict) and tool.get("name") == block["name"]), None)
                if definition is None:
                    raise ValueError("Unknown tool")
                schema = definition.get("input_schema")
                if not isinstance(schema, dict):
                    raise ValueError("Invalid tool schema")
                required = schema.get("required", [])
                if not isinstance(required, list):
                    raise ValueError("Invalid required tool fields")
                if any(key not in block["input"] for key in required):
                    raise ValueError("Missing required tool arguments from gateway")
            initial["input"] = {}
            deltas.append(("input_json_delta", "partial_json", json.dumps(block["input"], ensure_ascii=False)))
        elif kind == "thinking":
            if not isinstance(block.get("thinking"), str) or not isinstance(block.get("signature"), str):
                raise ValueError("Invalid thinking block")
            initial.update(thinking="", signature="")
            deltas.extend([("thinking_delta", "thinking", block["thinking"]),
                           ("signature_delta", "signature", block["signature"])])
        elif kind == "redacted_thinking":
            if not isinstance(block.get("data"), str):
                raise ValueError("Invalid redacted thinking block")
        elif kind == "web_search_tool_result":
            # (우리 것 · #118) 서버 검색 결과 — 실제 API 처럼 시작 칸에 통째로 싣는다(조각 없음).
            #   목록이면 결과, 객체면 검색 오류다(CLI 가 둘을 가른다).
            if not block.get("tool_use_id") or not isinstance(block.get("content"), (list, dict)):
                raise ValueError("Invalid web search result block")
        else:
            raise ValueError("Unsupported Anthropic content block")
        emit("content_block_start", index=index, content_block=initial)
        for delta_kind, field, value in deltas:
            for offset in range(0, len(value), 4096):
                emit("content_block_delta", index=index,
                     delta={"type": delta_kind, field: value[offset:offset + 4096]})
        emit("content_block_stop", index=index)
    emit("message_delta", delta={"stop_reason": message["stop_reason"],
                                 "stop_sequence": message.get("stop_sequence")}, usage=message["usage"])
    emit("message_stop")
    return events


# ── (우리 것 · #118) 웹서치 메움 — 알아보기 · 바꾸기 · 짓기. 프록시 칸은 `_forward_request` 의 `web_search` 갈래 ──
def web_search_tool(payload: dict) -> dict | None:
    """서버 웹서치 도구 선언(`web_search_*`)을 든 요청이면 그 선언을, 아니면 None."""
    tools = payload.get("tools")
    if not isinstance(tools, list):
        return None
    return next((tool for tool in tools if isinstance(tool, dict)
                 and str(tool.get("type", "")).startswith("web_search_")), None)


def web_search_query(payload: dict) -> str | None:
    """CLI 웹서치 하위 요청의 질의 — user 메시지 글에서 CLI 머리를 뗀 것. 글이 없으면 None."""
    texts = [text for message in payload.get("messages") or [] for text in _user_texts(message)]
    query = "\n".join(text for text in texts if isinstance(text, str)).strip()
    if query.startswith(_WEB_SEARCH_PROMPT_HEAD):
        query = query[len(_WEB_SEARCH_PROMPT_HEAD):].strip()
    return query or None


def _domain_list(tool: dict, key: str) -> list[str]:
    values = tool.get(key)
    return [v.strip().lower() for v in values if isinstance(v, str) and v.strip()] if isinstance(values, list) else []


def web_search_gemini_payload(query: str, tool: dict) -> dict:
    """제미나이 grounding 요청. 도메인 제한은 검색 도구에 칸이 없어 말로 싣고, 돌아온 출처를 다시 거른다."""
    lines = [f"Search the web for: {query}",
             "Report what the search results say — key facts, names, dates, versions and numbers — "
             "in the language of the query. Do not answer from memory."]
    allowed, blocked = _domain_list(tool, "allowed_domains"), _domain_list(tool, "blocked_domains")
    if allowed:
        lines.append("Use only sources from these sites: " + ", ".join(allowed))
    if blocked:
        lines.append("Do not use sources from these sites: " + ", ".join(blocked))
    return {"contents": [{"role": "user", "parts": [{"text": "\n".join(lines)}]}],
            "tools": [{"googleSearch": {}}]}


def web_search_headers(headers: dict[str, str]) -> dict[str, str]:
    """Anthropic 요청 머리를 제미나이 경로 꼴로 — 회사 키 하나가 두 경로에 다 선다.

    `Authorization: Bearer` 는 그대로 두고 같은 키를 `x-goog-api-key` 로도 싣는다(제미나이 클라이언트가 쓰는
    이름 · 위 `normalize_gemini_auth` 와 같은 자). Anthropic 전용 머리와 본문 길이는 뺀다 — 본문이 바뀐다.
    """
    out = {name: value for name, value in headers.items()
           if not name.lower().startswith("anthropic-") and name.lower() not in {"content-type", "x-api-key"}}
    out["Content-Type"] = "application/json; charset=utf-8"
    bearer = next((value for name, value in headers.items() if name.lower() == "authorization"), "")
    if bearer.lower().startswith("bearer ") and bearer[7:].strip():
        out["x-goog-api-key"] = bearer[7:].strip()
    return out


def _source_ok(title: str, allowed: list[str], blocked: list[str]) -> bool:
    """grounding 출처 거르기 — 출처 주소는 구글 경유 주소로 감싸져 오고 제목이 도메인이라 제목으로 견준다."""
    site = title.strip().lower()

    def hits(domain: str) -> bool:
        return site == domain or site.endswith("." + domain)
    if allowed and not any(hits(domain) for domain in allowed):
        return False
    return not any(hits(domain) for domain in blocked)


def _web_search_message(query: str, model: str, result: list | dict, text: str, usage: dict) -> dict:
    tool_id = f"srvtoolu_pgpt_{time.monotonic_ns():x}"
    content: list[dict] = [
        {"type": "server_tool_use", "id": tool_id, "name": "web_search", "input": {"query": query}},
        {"type": "web_search_tool_result", "tool_use_id": tool_id, "content": result},
    ]
    if text.strip():
        content.append({"type": "text", "text": text})
    return {"id": f"msg_pgpt_{time.monotonic_ns():x}", "type": "message", "role": "assistant", "model": model,
            "content": content, "stop_reason": "end_turn", "stop_sequence": None, "usage": usage}


def gemini_grounding_to_anthropic(raw: bytes, query: str, model: str, tool: dict) -> dict:
    """제미나이 grounding 답을 CLI 가 읽는 세 칸으로 — 출처는 `groundingChunks`, 본문은 생각 아닌 글 조각."""
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Expected a Gemini response object")
    candidates = data.get("candidates") or [{}]
    candidate = candidates[0] if isinstance(candidates[0], dict) else {}
    parts = (candidate.get("content") or {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts
                   if isinstance(part, dict) and not part.get("thought") and isinstance(part.get("text"), str))
    meta = candidate.get("groundingMetadata") or {}
    allowed, blocked = _domain_list(tool, "allowed_domains"), _domain_list(tool, "blocked_domains")
    results: list[dict] = []
    seen: set[str] = set()
    for chunk in meta.get("groundingChunks") or []:
        web = chunk.get("web") if isinstance(chunk, dict) else None
        url = web.get("uri") if isinstance(web, dict) else None
        if not isinstance(url, str) or not url or url in seen:
            continue
        title = web.get("title") if isinstance(web.get("title"), str) and web.get("title") else url
        if not _source_ok(title, allowed, blocked):
            continue
        seen.add(url)
        results.append({"type": "web_search_result", "title": title, "url": url,
                        "encrypted_content": "", "page_age": None})
    usage_meta = data.get("usageMetadata") or {}
    searches = meta.get("webSearchQueries") if isinstance(meta.get("webSearchQueries"), list) else []
    usage = {"input_tokens": int(usage_meta.get("promptTokenCount") or 0),
             "output_tokens": int(usage_meta.get("candidatesTokenCount") or 0),
             "server_tool_use": {"web_search_requests": max(1, len(searches))}}
    return _web_search_message(query, model, results, text, usage)


def web_search_error_message(query: str, model: str, code: str = "unavailable") -> dict:
    """메우기가 졌을 때 — 서버 도구의 검색 오류 칸으로 돌려준다. CLI 는 「Web search error: <code>」로 읽는다."""
    return _web_search_message(query, model, {"type": "web_search_tool_result_error", "error_code": code}, "",
                               {"input_tokens": 0, "output_tokens": 0})


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    _chunked_out = False
    _gw_request_id = ""
    _started = 0.0
    _upstream_started = 0.0
    _request_context = ""
    _keepalives_sent = 0
    _stream_outcome = "complete"

    def _client_disconnected(self) -> bool:
        """Peek without consuming request/pipelined bytes or changing socket timeout."""
        try:
            readable, _, _ = select.select([self.connection], [], [], 0)
            return bool(readable) and self.connection.recv(1, socket.MSG_PEEK) == b""
        except (OSError, ValueError):
            return True

    def _gw(self) -> str:
        """로그 꼬리: 게이트웨이 요청 번호가 있으면 ` gw=<id>`."""
        return f" gw={self._gw_request_id}" if self._gw_request_id else ""

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _send_json(self, status: int, payload: dict[str, object], *, keep_alive: bool = True,
                   retry_after: int | None = None) -> None:
        data = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "keep-alive" if keep_alive else "close")
        if retry_after is not None:
            self.send_header("Retry-After", str(retry_after))
        self.end_headers()
        self.wfile.write(data)
        self.close_connection = not keep_alive

    def _read_body(self) -> bytes | None:
        """Read the request body, honouring chunked transfer encoding.

        Claude Code and Codex both fall back to chunked uploads for large
        payloads; reading only Content-Length silently dropped those bodies.
        """
        transfer_encoding = self.headers.get("Transfer-Encoding", "")
        codings = [part.strip().lower() for part in transfer_encoding.split(",") if part.strip()]
        if codings and codings[-1] == "chunked":
            chunks: list[bytes] = []
            while True:
                line = self.rfile.readline(65536).strip()
                if not line:
                    break
                try:
                    size = int(line.split(b";")[0], 16)
                except ValueError:
                    log(f"chunked parse error: {line!r}")
                    break
                # 음수/과대 크기는 read(-1) 블록·메모리 폭주로 이어진다
                if size < 0 or size > MAX_CHUNK_SIZE:
                    log(f"chunked size rejected: {size}")
                    break
                if size == 0:
                    self.rfile.readline(65536)
                    break
                chunks.append(self.rfile.read(size))
                self.rfile.read(2)
            return b"".join(chunks)

        length = int(self.headers.get("Content-Length", "0") or "0")
        return self.rfile.read(length) if length else None

    def _exchange_upstream(self, conn: http.client.HTTPConnection, method: str, path: str,
                           body: bytes | None, headers: dict[str, str]) -> http.client.HTTPResponse:
        """Wait for headers while noticing client cancellation, including long thinking turns.

        The helper owns request/getresponse; the caller owns connection cleanup. A late
        response is closed on cancellation so it cannot keep the socket alive or be pooled.
        HTTP status and headers remain untouched; no speculative SSE 200 is sent.
        """
        done = threading.Event()
        lock = threading.Lock()
        abandoned = False
        results: list[http.client.HTTPResponse | Exception] = []

        def exchange() -> None:
            result: http.client.HTTPResponse | Exception
            try:
                try:
                    conn.request(method, path, body=body, headers=headers)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError) as upload_error:
                    # Preserve an early rejection such as 413 received during upload.
                    try:
                        result = conn.getresponse()
                    except (http.client.HTTPException, OSError):
                        raise upload_error
                else:
                    result = conn.getresponse()
            except Exception as error:
                result = error
            with lock:
                if abandoned:
                    if isinstance(result, http.client.HTTPResponse):
                        result.close()
                else:
                    results.append(result)
            done.set()

        threading.Thread(target=exchange, daemon=True).start()
        while not done.wait(CLIENT_POLL_SEC):
            if self._client_disconnected():
                with lock:
                    abandoned = True
                    for result in results:
                        if isinstance(result, http.client.HTTPResponse):
                            result.close()
                raise _ClientDisconnected()
        result = results[0]
        if isinstance(result, Exception):
            raise result
        return result

    def _write_upstream(
        self,
        method: str,
        path: str,
        body: bytes | None,
        headers: dict[str, str],
    ) -> tuple[http.client.HTTPResponse, http.client.HTTPConnection]:
        """POST/GET to the gateway on a pooled keep-alive connection."""
        upstream_headers = {
            key: value
            for key, value in headers.items()
            if key.lower() not in HOP_BY_HOP and key.lower() not in {"host", "content-length"}
        }
        upstream_headers["Connection"] = "keep-alive"
        if body is not None:
            upstream_headers["Content-Length"] = str(len(body))
        elif method.upper() in {"POST", "PUT", "PATCH"}:
            upstream_headers["Content-Length"] = "0"

        log_path = path.split("?", 1)[0]   # 쿼리(?key=...)는 로그에 남기지 않는다
        for attempt in range(2):
            if self._client_disconnected():
                raise _ClientDisconnected()
            conn = _UPSTREAM_POOL.acquire(fresh=attempt > 0)
            reused = bool(getattr(conn, "pgpt_reused", False))
            try:
                return self._exchange_upstream(conn, method, path, body, upstream_headers), conn
            except _ClientDisconnected:
                _UPSTREAM_POOL.release(conn, reuse=False)
                raise
            except (http.client.HTTPException, OSError, TimeoutError) as error:
                _UPSTREAM_POOL.release(conn, reuse=False)
                # 다시 보내도 되는 경우는 하나뿐: 풀에서 꺼낸(오래 쉰) 연결이 응답 전에 끊긴 것. 새 연결이 실패했거나
                # 시간 초과면 게이트웨이가 이미 요청을 처리 중일 수 있어 다시 보내면 생성이 두 번 돈다(비용 두 배).
                stale = isinstance(error, (http.client.RemoteDisconnected, BrokenPipeError,
                                           ConnectionResetError, ConnectionAbortedError))
                if attempt == 0 and reused and stale:
                    log(f"{method} {log_path} upstream retry on a fresh connection after {error!r}")
                    continue
                raise
        raise RuntimeError("unreachable")

    def _emit(self, data: bytes) -> None:
        if not data:
            return
        if self._chunked_out:
            self.wfile.write(f"{len(data):X}\r\n".encode("ascii") + data + b"\r\n")
        else:
            self.wfile.write(data)
        self.wfile.flush()

    def _read_chunks(self, response: object, interval: float, can_keepalive: Callable[[], bool] | None = None):
        """Yield upstream body chunks; upstream failures surface as ``_UpstreamReadError``.

        ``interval > 0`` (v18): the socket is read on a helper thread and whenever nothing has
        arrived for ``interval`` seconds an SSE comment goes to the client, so a silent gateway
        (thinking deltas are not relayed) does not trip the client's byte-idle watchdog.
        """
        if interval <= 0:
            while True:
                try:
                    chunk = response.read1(65536)  # type: ignore[attr-defined]
                except (OSError, http.client.HTTPException) as error:
                    # IncompleteRead 는 OSError 가 아니다 — 함께 잡아 잘린 응답을 기록한다
                    raise _UpstreamReadError(error) from error
                if not chunk:
                    return
                yield chunk

        items: queue.Queue = queue.Queue()

        def reader() -> None:
            try:
                while True:
                    chunk = response.read1(65536)  # type: ignore[attr-defined]
                    if not chunk:
                        break
                    items.put(chunk)
                items.put(None)
            except BaseException as error:  # noqa: BLE001 — 사유째 넘긴다
                items.put(error)

        threading.Thread(target=reader, daemon=True).start()
        while True:
            try:
                item = items.get(timeout=interval)
            except queue.Empty:
                if can_keepalive is not None and not can_keepalive():
                    if self._client_disconnected():
                        raise ConnectionAbortedError("client disconnected during partial SSE event")
                    continue
                self._emit(_KEEPALIVE_LINE)
                _count_keepalive()
                self._keepalives_sent += 1
                continue
            if item is None:
                return
            if isinstance(item, BaseException):
                raise _UpstreamReadError(item) from item
            yield item

    def _relay_stream(
        self,
        response: http.client.HTTPResponse,
        *,
        gemini_sse: bool,
        sse: bool = False,
        keepalive_interval: float = 0.0,
        protocol: str = "",
    ) -> bool:
        """Copy upstream body to the client. Returns True if fully consumed.

        끝까지 받았을 때만 chunked 종료 표시를 쓴다. 업스트림이 도중에 끊기면 종료 표시 없이 연결을 닫아
        클라이언트가 잘린 응답임을 알게 한다(전에는 Connection: close 로만 끝나 정상 종료와 구별되지 않았다).
        ``sse`` (Anthropic · OpenAI 스트림)면 게이트웨이의 ``error`` 프레임을 세고 기록한다 — 180초 시한(#28)의 자국이다.
        """
        joiner = GeminiSseJoiner() if gemini_sse else None
        observer = SseObserver(protocol) if sse else None
        # (v26) A Claude response relayed as-is (client asked for nonstream, e.g. its own
        # "Retrying without streaming") is rare and small; keep a bounded copy to read stop_reason.
        claude_messages = getattr(self, "_claude_messages", False)
        compact_copy = bytearray() if (claude_messages and not sse and not gemini_sse) else None
        keepalives_before = self._keepalives_sent
        self._stream_outcome = "complete"

        def incomplete(reason: str) -> bool:
            self._stream_outcome = "stream_incomplete" if sse else "incomplete"
            if sse:
                _count_stream_incomplete()
            log(f"upstream incomplete: {reason} {self._request_context}{self._gw()}")
            return False

        try:
            for chunk in self._read_chunks(response, keepalive_interval,
                                           (lambda: observer.can_keepalive) if observer is not None else None):
                if observer is not None:
                    observer.feed(chunk)
                    if observer.error is not None and self._stream_outcome != "stream_error":
                        self._stream_outcome = "stream_error"
                        _count_stream_error()
                        elapsed = time.monotonic() - self._upstream_started if self._upstream_started else 0.0
                        log(f"stream error after {elapsed:.1f}s: {observer.error} {self._request_context}{self._gw()}")
                if compact_copy is not None:
                    if len(compact_copy) + len(chunk) <= MAX_UNSTREAM_BYTES:
                        compact_copy.extend(chunk)
                    else:
                        compact_copy = None
                if joiner is not None:
                    for event in joiner.feed(chunk):
                        self._emit(event)
                else:
                    self._emit(chunk)
            # 길이를 선언한 응답이 모자라게 끝나면 read1() 은 예외 없이 빈 바이트를 돌려준다 — 남은 길이로 가린다
            remaining = getattr(response, "length", None)
            if remaining:
                return incomplete(f"ended {remaining} bytes early")
            if joiner is not None:
                for event in joiner.finish():
                    self._emit(event)
                if joiner.joined_fragments:
                    log(f"Gemini SSE fragments joined={joiner.joined_fragments}")
            if observer is not None and protocol and not observer.terminal and observer.error is None:
                if observer.limited:
                    self._stream_outcome = "stream_unverified"
                    _count_stream_unverified()
                    log(f"stream terminal unverified: event exceeded inspection limit {self._request_context}{self._gw()}")
                else:
                    # Do not emit a successful chunked terminator or invent a model event.
                    return incomplete(f"missing {protocol} terminal event")
            if self._chunked_out:
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
            if claude_messages:
                stop_reason = observer.stop_reason if observer is not None else _json_stop_reason(compact_copy)
                if stop_reason == "max_tokens":
                    _count_max_tokens_hit(getattr(self, "_compact_request", False))
                    log(f"reached max_tokens {self._request_context}{self._gw()}")
            sent = self._keepalives_sent - keepalives_before
            if sent:
                log(f"keepalive x{sent} (upstream silent > {keepalive_interval:g}s){self._gw()}")
            return True
        except _UpstreamReadError as error:
            return incomplete(f"read aborted: {error.__cause__!r}")
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # 클라이언트가 갔다(취소 · 시간 초과)
            self._stream_outcome = "client_cancelled"
            _count_client_cancelled()
            return False
        finally:
            if observer is not None and protocol:
                log(f"stream {observer.diagnostics(self._upstream_started)} "
                    f"keepalives={self._keepalives_sent - keepalives_before} "
                    f"{self._request_context}{self._gw()}")

    def _forward(self) -> None:
        global _ACTIVE_REQUESTS
        tracked = urlsplit(self.path).path != "/health"
        if tracked:
            with _STATS_LOCK:
                _ACTIVE_REQUESTS += 1
        try:
            self._forward_request()
        finally:
            if tracked:
                with _STATS_LOCK:
                    _ACTIVE_REQUESTS -= 1

    def _forward_request(self) -> None:
        started = time.monotonic()
        self._started = started
        self._upstream_started = 0.0
        self._request_context = f"id={time.monotonic_ns():x}"
        self._compact_request = False
        self._claude_messages = False
        self._keepalives_sent = 0
        self._stream_outcome = "complete"
        self._gw_request_id = ""
        parsed = urlsplit(self.path)
        if parsed.path == "/health":
            payload: dict[str, object] = {
                "status": "ok",
                "service": "pgpt-proxy",
                "version": VERSION,
                # 설치기가 방금 띄운 자기 프로세스인지 확인한다(한 PC 를 여럿이 쓰면 남의 프록시가 포트를 쥘 수 있다)
                "pid": os.getpid(),
            }
            payload.update(stats())
            self._send_json(200, payload)
            return
        # 접두어만 보면 /gpgpta01-gpt/../other 같은 경로가 게이트웨이의 다른 서비스로 간다 — 점 세그먼트도 막는다
        segments = unquote_plus(parsed.path).split("/")
        if not parsed.path.startswith(ALLOWED_PREFIX) or ".." in segments or "." in segments:
            # 본문을 읽지 않았으므로 연결을 닫는다 — 남은 본문이 같은 연결의 다음 요청 줄로 읽혔다
            self._send_json(
                403,
                {"type": "error", "error": {"message": "허용되지 않은 경로입니다."}},
                keep_alive=False,
            )
            return

        body = self._read_body()
        model_name = ""
        gemini_chat_model: str | None = None
        gemini_chat_stream = False
        claude_unstream = False
        compact_request = False
        claude_tools = None
        web_search: dict[str, object] | None = None  # (우리 것 · #118) 메울 웹서치 하위 요청 — 질의 · 모델 · 도구 · 스트림
        if body:
            stripped_path = parsed.path.rstrip("/")
            is_messages = stripped_path.endswith("/v1/messages")
            is_openai_generation = (
                stripped_path.endswith("/v1/chat/completions")
                or stripped_path.endswith("/v1/responses")
            )
            # tools 가 아예 없는 본문은 파싱 자체를 건너뛴다 (요청당 비용 절감).
            # 단 GPT-5/o 계열 토큰 파라미터 보정과 Gemini chat 변환은 짧은 호출에도 필요하다.
            if is_messages or is_openai_generation or b'"tools"' in body:
                try:
                    payload_obj = json.loads(body)
                except (UnicodeDecodeError, ValueError, TypeError):
                    payload_obj = None

                if isinstance(payload_obj, dict):
                    changed = False
                    model_name = str(payload_obj.get("model") or "")
                    self._request_context += " " + request_settings(payload_obj)
                    # (우리 것 · #118) 웹서치 하위 요청은 Claude 갈래를 안 탄다 — 제미나이 grounding 요청으로 바꾼다.
                    web_tool = web_search_tool(payload_obj) if (is_messages and WEB_SEARCH) else None
                    web_query = web_search_query(payload_obj) if web_tool else None
                    if web_tool and web_query:
                        web_search = {"query": web_query, "model": model_name or "claude", "tool": web_tool,
                                      "stream": payload_obj.get("stream") is True}
                        payload_obj = web_search_gemini_payload(web_query, web_tool)
                        changed = True
                        self._request_context += f" kind=web_search search_model={WEB_SEARCH_MODEL}"
                    elif is_messages:
                        if normalize_claude_model_id(payload_obj, parsed.path):
                            log(f"{parsed.path} Claude model restored: {model_name} -> {payload_obj.get('model')}")
                        payload_obj = sanitize_payload(payload_obj)
                        compact_request = is_claude_compaction(payload_obj)
                        if not compact_request and is_compaction_continuation(payload_obj):
                            compact_request = True
                            self._request_context += " kind=compact_continue"
                        elif compact_request:
                            self._request_context += " kind=compact"
                        self._compact_request = compact_request
                        self._claude_messages = True
                        if compact_request:
                            adjustment = tune_claude_compaction(payload_obj)
                            if adjustment:
                                self._request_context += " " + adjustment
                        changed = True
                        if (CLAUDE_UNSTREAM or (COMPACT_UNSTREAM and compact_request)) and payload_obj.get("stream") is True:
                            payload_obj["stream"] = False
                            claude_unstream = True
                            claude_tools = payload_obj.get("tools", [])
                            self._request_context += " transport=unstream"
                        ceiling = cap_claude_output(payload_obj, unstream=payload_obj.get("stream") is not True)
                        if ceiling:
                            self._request_context += " " + ceiling
                    elif stripped_path.endswith("/v1/chat/completions") and model_name.startswith("gemini-"):
                        # /v1/responses 는 프롬프트가 input · instructions 에 있어 이 변환(messages 만 읽음)을 타면
                        # 빈 프롬프트가 된다 — chat/completions 만 바꾼다
                        gemini_chat_model = model_name
                        gemini_chat_stream = bool(payload_obj.get("stream"))
                        payload_obj = openai_chat_to_gemini_payload(payload_obj)
                        changed = True
                        log(f"{parsed.path} model={model_name} openai-chat->gemini-native")
                    if normalize_openai_token_limit(payload_obj, parsed.path):
                        changed = True
                        limit_field = (
                            "max_output_tokens"
                            if parsed.path.rstrip("/").endswith("/v1/responses")
                            else "max_completion_tokens"
                        )
                        log(f"{parsed.path} model={payload_obj.get('model')} max_tokens->{limit_field}")
                    filled = patch_tool_descriptions(payload_obj, parsed.path)
                    if filled:
                        changed = True
                        _count_patched(filled)
                        log(
                            f"{parsed.path} model={payload_obj.get('model')} "
                            f"tool_descriptions_filled={filled}"
                        )
                    if changed:
                        body = _json_bytes(payload_obj)

        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP
            and key.lower() not in {"host", "content-length", "accept-encoding", "expect"}
        }
        query, headers = normalize_gemini_auth(parsed.path, parsed.query, headers)
        headers = normalize_anthropic_auth(headers)
        if web_search:
            headers = web_search_headers(headers)
        if gemini_chat_model:
            upstream_path = f"{GEMINI_PREFIX}/models/{quote(gemini_chat_model, safe='')}:generateContent"
        elif web_search:
            upstream_path = f"{GEMINI_PREFIX}/models/{quote(WEB_SEARCH_MODEL, safe='')}:generateContent"
            # (우리 것 · #118) Anthropic 쪽 쿼리는 제미나이 경로에 안 싣는다 — Claude Code 는
            #   `/v1/messages?beta=true` 로 보내는데, 제미나이는 모르는 쿼리를 400
            #   (`Unknown name "beta": Cannot bind query parameter`)으로 거절한다. 인증 키가
            #   `?key=` 로 온 경우만 남긴다(`normalize_gemini_auth` 가 쓰는 자리).
            query = "&".join(part for part in query.split("&") if part.startswith("key="))
        else:
            upstream_path = normalize_gemini_model_path(parsed.path)
        if query:
            upstream_path += f"?{query}"

        conn: http.client.HTTPConnection | None = None
        response: http.client.HTTPResponse | None = None
        reuse = False
        upstream_status = 0
        client_status = 0
        outcome = "complete"
        waited = 0.0
        headers_sec = 0.0
        provider = "gemini" if web_search else request_provider(parsed.path, model_name)
        gate = _HEAVY_GATES[provider]
        self._request_context += f" provider={provider} bytes={len(body or b'')}"
        generation = is_generation_request(parsed.path)
        if generation:
            log(f"request {self.command} {parsed.path} {self._request_context}")
        heavy = is_heavy_request(parsed.path, body)
        heavy_held = False
        queue_started = time.monotonic()
        try:
            if heavy:
                try:
                    heavy_held, waited = gate.acquire(HEAVY_QUEUE_TIMEOUT_SEC, self._client_disconnected)
                finally:
                    waited = time.monotonic() - queue_started
                if not heavy_held:
                    _count_heavy_queue_timeout()
                    outcome = "queue_timeout"
                    client_status = 429
                    log(
                        f"heavy gate timeout {self.command} {parsed.path} "
                        f"waited={waited:.1f}s HTTP 429 {self._request_context}"
                    )
                    self._send_json(429, {
                        "type": "error", "error": {
                            "type": "rate_limit_error", "code": "proxy_queue_timeout",
                            "message": f"Local P-GPT proxy {provider} queue is busy. Retry shortly.",
                        },
                    }, keep_alive=False, retry_after=5)
                    return
                _count_heavy_serialized(waited)
                if waited >= 1.0:
                    log(f"heavy gate {self.command} {parsed.path} waited={waited:.1f}s {self._request_context}")
            self._upstream_started = time.monotonic()
            try:
                response, conn = self._write_upstream(
                    self.command, upstream_path, body, headers
                )
            except _ClientDisconnected:
                raise
            except Exception as error:
                outcome = "upstream_error"
                client_status = 502
                log(f"{self.command} {parsed.path} -> upstream unreachable: {error} {self._request_context}")
                # 이 요청 뒤에 연결을 닫으므로(close_connection) keep-alive 를 약속하지 않는다
                self._send_json(
                    502, {"type": "error", "error": {"message": str(error)}}, keep_alive=False
                )
                return

            headers_sec = time.monotonic() - self._upstream_started
            self._gw_request_id = response.getheader(GATEWAY_REQUEST_ID_HEADER) or ""
            # (v19) 시한 판정은 경과를 아는 finally 에서 한다 — 여기서는 상태만 넘겨 둔다
            upstream_status = response.status
            client_status = upstream_status
            if response.status >= 400:
                log(f"{self.command} {parsed.path} -> HTTP {response.status} {self._request_context}{self._gw()}")

            if web_search:
                # (우리 것 · #118) 답 전체를 읽어 세 칸으로 짓는다. 상류가 지거나 꼴이 어긋나면 **검색 오류 칸**으로
                #   돌려준다 — 서버 도구의 오류는 원래 그 칸으로 오고, 그러면 대화는 안 깨지고 CLI 는 「Web search
                #   error」를 결과로 읽는다(그 뒤는 웹 다시 찾기 훅이 다른 길을 댄다).
                message: dict | None = None
                try:
                    raw = response.read()
                    reuse = _keeps_alive(response)
                    if response.status < 400:
                        message = gemini_grounding_to_anthropic(
                            raw, str(web_search["query"]), str(web_search["model"]), dict(web_search["tool"]))
                    else:
                        log(f"web search fill: upstream HTTP {response.status} "
                            f"body={raw[:400]!r} {self._request_context}{self._gw()}")
                except (OSError, http.client.HTTPException, ValueError, TypeError, AttributeError,
                        KeyError, IndexError) as error:
                    log(f"web search fill: Gemini answer unreadable: {error!r} {self._request_context}{self._gw()}")
                if message is None:
                    _count_web_search(False)
                    outcome = "web_search_failed"
                    message = web_search_error_message(str(web_search["query"]), str(web_search["model"]))
                else:
                    _count_web_search(True)
                    self._request_context += f" sources={len(message['content'][1]['content'])}"
                if web_search["stream"]:
                    data = b"".join(anthropic_message_events(message))
                    content_type = "text/event-stream; charset=utf-8"
                else:
                    data = _json_bytes(message)
                    content_type = "application/json; charset=utf-8"
                client_status = 200
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(data)
                return

            if gemini_chat_model and response.status < 400:
                try:
                    raw = response.read()
                except (OSError, http.client.HTTPException) as error:
                    outcome = "incomplete"
                    client_status = 502
                    # 변환하려면 본문 전체가 필요하다 — 끊기면 잘린 답을 만들지 말고 502 로 알린다
                    log(f"{self.command} {parsed.path} -> upstream read aborted before Gemini conversion: {error!r}")
                    self._send_json(502, {"type": "error", "error": {"message": f"upstream read aborted: {error}"}}, keep_alive=False)
                    return
                if gemini_chat_stream:
                    converted = gemini_response_to_openai_stream(raw, gemini_chat_model)
                    content_type = "text/event-stream; charset=utf-8"
                else:
                    converted = gemini_response_to_openai_chat(raw, gemini_chat_model)
                    content_type = "application/json; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(converted)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(converted)
                reuse = _keeps_alive(response)
                return

            # 3xx: relay as-is, never follow (following would re-send Authorization).
            is_gemini_stream = (
                upstream_path.startswith(f"{GEMINI_PREFIX}/models/")
                and ":streamGenerateContent" in upstream_path
                and response.status < 400
            )

            content_type = (response.getheader("Content-Type") or "").lower()
            if claude_unstream and 200 <= response.status < 300 and not content_type.startswith("text/event-stream"):
                # Keep real HTTP errors/statuses until upstream headers arrive. The
                # installed 600s client idle timeout covers the header wait. After
                # headers, heartbeat while buffering; a failure is an SSE error,
                # never a fabricated successful tool call or message_stop.
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Transfer-Encoding", "chunked")
                self.send_header("Connection", "close")
                self.end_headers()
                self._chunked_out = True
                try:
                    raw = bytearray()
                    for chunk in self._read_chunks(response, KEEPALIVE_SEC):
                        raw.extend(chunk)
                        if len(raw) > MAX_UNSTREAM_BYTES:
                            raise ValueError("Nonstream response exceeds buffer limit")
                    if response.length not in (None, 0):
                        raise ValueError("Truncated nonstream response")
                    message = json.loads(raw)
                    events = anthropic_message_events(message, tools=claude_tools, allow_tools=not compact_request)
                    for event in events:
                        self._emit(event)
                    self._request_context += f" output_tokens={message['usage'].get('output_tokens', 'unknown')} stop_reason={message['stop_reason']}"
                    if message["stop_reason"] == "max_tokens":
                        _count_max_tokens_hit(compact_request)
                        log(f"reached max_tokens {self._request_context}{self._gw()}")
                    reuse = _keeps_alive(response)
                except (_UpstreamReadError, ValueError, TypeError):
                    outcome = "stream_error"
                    _count_stream_error()
                    self._emit(b"event: error\ndata: " + _json_bytes({"type": "error", "error": {
                        "type": "api_error", "message": "Proxy could not convert a complete Anthropic response; no tool calls were emitted."
                    }}) + b"\n\n")
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
                return
            is_sse = content_type.startswith("text/event-stream") and not is_gemini_stream
            protocol = ""
            if is_sse and response.status < 400:
                route = parsed.path.rstrip("/")
                if route.endswith("/v1/messages"):
                    protocol = "anthropic"
                elif route.endswith("/v1/responses"):
                    protocol = "responses"
                elif route.endswith("/v1/chat/completions"):
                    protocol = "chat"

            self.send_response(response.status)
            for key, value in response.headers.items():
                # date/server 는 send_response 가 이미 보냈다 — 중복 방지
                if key.lower() in HOP_BY_HOP or key.lower() in {
                    "content-length",
                    "date",
                    "server",
                }:
                    continue
                self.send_header(key, value)
            # 본문 길이를 클라이언트가 알 수 있게 한다: 업스트림 길이를 그대로 쓰거나(본문을 바꾸지 않을 때),
            # chunked 로 다시 싼다. 그래야 업스트림이 도중에 끊긴 응답을 클라이언트가 잘린 것으로 안다.
            no_body = (
                self.command == "HEAD"
                or response.status in (204, 304)
                or 100 <= response.status < 200
            )
            upstream_length = response.getheader("Content-Length")
            self._chunked_out = False
            if no_body:
                pass
            elif upstream_length is not None and not is_gemini_stream and not is_sse and not getattr(response, "chunked", False):
                # chunked 와 Content-Length 를 함께 보낸 업스트림은 http.client 가 chunked 로 읽는다 — 그 길이는 틀린 값이다
                self.send_header("Content-Length", upstream_length)
            else:
                self.send_header("Transfer-Encoding", "chunked")
                self._chunked_out = True
            self.send_header("Connection", "close")
            self.end_headers()

            if no_body:
                fully_read = True
                try:
                    response.read()
                except (OSError, http.client.HTTPException):
                    fully_read = False
            else:
                # (v18) Anthropic · OpenAI 스트림에만 주석을 흘린다. Gemini 는 재조립기가 조각을 쥐고 있어 제외한다.
                keepalive_interval = KEEPALIVE_SEC if (is_sse and response.status < 400 and KEEPALIVE_SEC > 0) else 0.0
                fully_read = self._relay_stream(
                    response,
                    gemini_sse=is_gemini_stream,
                    sse=is_sse,
                    keepalive_interval=keepalive_interval,
                    protocol=protocol,
                )
            if self._stream_outcome != "complete":
                outcome = self._stream_outcome
            elif not fully_read:
                outcome = "incomplete"
            reuse = fully_read and _keeps_alive(response)
        except (_ClientDisconnected, BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # 클라이언트가 응답을 받기 전에 끊었다(취소 · 시간 초과) — 조용히 끝낸다. 업스트림 연결은 버린다.
            reuse = False
            outcome = "client_cancelled"
            _count_client_cancelled()
        finally:
            _UPSTREAM_POOL.release(conn, reuse=reuse)
            if heavy_held:
                gate.release()
            self.close_connection = True
            elapsed = time.monotonic() - started
            upstream_sec = time.monotonic() - self._upstream_started if self._upstream_started else 0.0
            # (v21) 로컬 대기는 빼고, 시한을 넘긴 5xx만 게이트웨이 시간 초과 후보로 센다.
            # SSE error 프레임 판은 _relay_stream 이 이미 stream_errors 로 세므로 여기서 겹치지 않는다.
            if (upstream_status >= 500 or outcome in ("stream_error", "stream_incomplete")) and at_execution_limit(upstream_sec):
                _count_execution_cut()
                log(
                    f"execution cut {self.command} {parsed.path} upstream={upstream_sec:.1f}s "
                    f"HTTP {upstream_status} (possible gateway timeout; limit "
                    f"~{EXECUTION_LIMIT_SEC:g}s) {self._request_context}{self._gw()}"
                )
            if generation or outcome != "complete":
                log(f"complete {self.command} {parsed.path} HTTP {client_status} result={outcome} "
                    f"queue={waited:.3f}s headers={headers_sec:.3f}s upstream={upstream_sec:.3f}s "
                    f"total={elapsed:.3f}s {self._request_context}{self._gw()}")
            if elapsed >= SLOW_REQUEST_SEC and parsed.path != "/health":
                _count_slow()
                log(f"slow {self.command} {parsed.path} {elapsed:.1f}s{self._gw()}")

    do_HEAD = _forward
    do_GET = _forward
    do_POST = _forward


class ProxyServer(ThreadingHTTPServer):
    daemon_threads = True
    # Windows 에서 SO_REUSEADDR 은 두 번째 프로세스의 중복 바인드를 허용한다.
    # 우리 소켓에서 이를 끄는 것(allow_reuse_address=False)만으로는 남이
    # SO_REUSEADDR 로 우리 위에 바인드하는 것을 못 막으므로, Windows 전용
    # SO_EXCLUSIVEADDRUSE 로 포트를 배타 점유한다.
    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1
            )
        super().server_bind()

    def get_request(self):  # noqa: D102
        sock, addr = super().get_request()
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        return sock, addr


def self_test() -> None:
    # 1. sanitize: 파라미터 제거·병합·prefill 제거. 도구 description 은 건드리지 않는다.
    payload = {
        "temperature": 0.2,
        "top_p": 0.9,
        "messages": [
            {"role": "assistant", "content": "old"},
            {"role": "user", "content": "question"},
            {"role": "user", "content": "more"},
            {"role": "assistant", "content": "prefill"},
        ],
        "tools": [{"name": "Read", "description": ""}],
    }
    result = sanitize_payload(payload)
    assert "temperature" not in result and "top_p" not in result
    assert len(result["messages"]) == 1
    assert result["messages"][0]["role"] == "user"
    assert len(result["messages"][0]["content"]) == 2
    assert result["tools"][0]["description"] == ""  # sanitize 는 도구를 안 만진다

    # 2. patch: 최상위 tools 보정 (sanitize 이후 단일 소유자)
    assert patch_tool_descriptions(result) == 1
    assert result["tools"][0]["description"] == "Read tool"

    # 3. Codex Responses: input[*].tools 의 중첩 namespace 까지
    codex = {
        "model": "gpt-5.6-sol",
        "input": [{"tools": [
            {"type": "namespace", "name": "functions", "description": "", "tools": [
                {"name": "shell", "description": ""},
                {"name": "apply_patch", "description": "이미 있음"},
            ]},
        ]}],
    }
    assert patch_tool_descriptions(codex) == 2  # namespace 자신 + 중첩 shell
    namespace = codex["input"][0]["tools"][0]
    assert namespace["description"] == "functions tool"
    assert namespace["tools"][0]["description"] == "shell tool"
    assert namespace["tools"][1]["description"] == "이미 있음"
    assert patch_tool_descriptions(codex) == 0

    # 4. 대화 데이터는 절대 변조하지 않는다 — tool_use input 안의 "tools" 리스트
    conversation = {
        "model": "claude-opus-5",
        "messages": [{"role": "assistant", "content": [{
            "type": "tool_use", "name": "write_config",
            "input": {"tools": [{"name": "x"}]},
        }]}],
        "tools": [],
    }
    assert patch_tool_descriptions(conversation) == 0
    assert "description" not in conversation["messages"][0]["content"][0]["input"]["tools"][0]

    # 5. Gemini tools 는 절대 보정하지 않는다 — description 필드가 없는 스키마라
    #    넣으면 "Unknown name \"description\" at 'tools[0]'" 400 이 난다.
    gemini = {
        "contents": [{"role": "user", "parts": [{"text": "hi"}]}],
        "tools": [
            {"functionDeclarations": [{"name": "list_directory", "description": ""}]},
            {"googleSearch": {}},
            {"urlContext": {}},
        ],
    }
    gemini_path = "/gpgpta01-gpt/v1beta/models/gemini-3.6-flash:generateContent"
    assert patch_tool_descriptions(gemini, gemini_path) == 0
    for tool in gemini["tools"]:
        assert "description" not in tool, tool
    # 경로를 몰라도 형태만으로 걸러낸다 (functionDeclarations 안쪽까지 무수정)
    assert patch_tool_descriptions(gemini) == 0
    assert gemini["tools"][0]["functionDeclarations"][0]["description"] == ""
    for tool in gemini["tools"]:
        assert "description" not in tool, tool
    # Gemini 경로에서는 Codex 형태가 섞여 있어도 손대지 않는다
    assert patch_tool_descriptions({"tools": [{"name": "shell", "description": ""}]},
                                   gemini_path) == 0

    # 5b. GPT-5/o 계열 chat 경로는 max_tokens 를 max_completion_tokens 로 바꾼다.
    token_payload = {"model": "gpt-5.6-sol", "max_tokens": 8}
    assert normalize_openai_token_limit(token_payload, "/gpgpta01-gpt/v1/chat/completions")
    assert "max_tokens" not in token_payload and token_payload["max_completion_tokens"] == 8
    old_payload = {"model": "gpt-4o", "max_tokens": 8}
    assert not normalize_openai_token_limit(old_payload, "/gpgpta01-gpt/v1/chat/completions")
    assert old_payload["max_tokens"] == 8
    # 5b-1. GPT-6(아스트라) 도 같은 보정을 받고, /v1/responses 는 max_output_tokens 로 간다.
    astra_payload = {"model": "gpt-6-astra", "max_tokens": 8}
    assert normalize_openai_token_limit(astra_payload, "/gpgpta01-gpt/v1/chat/completions")
    assert "max_tokens" not in astra_payload and astra_payload["max_completion_tokens"] == 8
    responses_payload = {"model": "gpt-6-astra", "max_tokens": 8}
    assert normalize_openai_token_limit(responses_payload, "/gpgpta01-gpt/v1/responses")
    assert "max_tokens" not in responses_payload and responses_payload["max_output_tokens"] == 8
    # 둘 다 있으면 legacy 만 떼고 이미 있는 새 필드 값을 지킨다.
    both_payload = {"model": "gpt-5.6-sol", "max_tokens": 8, "max_completion_tokens": 32}
    assert normalize_openai_token_limit(both_payload, "/gpgpta01-gpt/v1/chat/completions")
    assert "max_tokens" not in both_payload and both_payload["max_completion_tokens"] == 32
    assert not normalize_openai_token_limit({"model": "gpt-4o", "max_tokens": 8}, "/gpgpta01-gpt/v1/responses")

    # 5b2. Hermes가 점을 대시로 바꾼 Claude 소수 버전 ID를 복원한다.
    claude_alias = {"model": "claude-opus-4-6"}
    assert normalize_claude_model_id(claude_alias, "/gpgpta01-gpt/v1/messages")
    assert claude_alias["model"] == "claude-opus-4.6"
    assert normalize_pgpt_claude_model("claude-sonnet-4-5") == "claude-sonnet-4.5"
    assert normalize_pgpt_claude_model("claude-opus-4.6") == "claude-opus-4.6"
    assert normalize_pgpt_claude_model("claude-opus-5") == "claude-opus-5"
    assert normalize_pgpt_claude_model("claude-fable-5-1") == "claude-fable-5.1"
    assert normalize_pgpt_claude_model("claude-fable-5.1") == "claude-fable-5.1"
    assert normalize_pgpt_claude_model("claude-newfamily-7-2") == "claude-newfamily-7.2"
    assert normalize_pgpt_claude_model("claude-3-5-sonnet-20241022") == "claude-3-5-sonnet-20241022"
    assert normalize_pgpt_claude_model("gpt-5.6-sol") == "gpt-5.6-sol"
    assert normalize_pgpt_claude_model("claude-sonnet-5") == "claude-sonnet-4.6"
    assert normalize_pgpt_claude_model("claude-sonnet-5-20260219") == "claude-sonnet-4.6"
    assert normalize_claude_model_id({"model": "claude-opus-5"}, "/gpgpta01-gpt/v1/messages") is False

    # 5c. Hermes/OpenAI 호환 Gemini 호출은 Gemini native 응답을 chat completion 으로 되돌린다.
    converted = gemini_response_to_openai_chat(
        _json_bytes({"candidates": [{"content": {"parts": [{"text": "OK"}]}, "finishReason": "STOP"}]}),
        "gemini-3.6-flash",
    )
    converted_obj = json.loads(converted.decode("utf-8"))
    assert converted_obj["choices"][0]["message"]["content"] == "OK"

    # 6. Gemini: 원래 헤더·쿼리는 그대로 두고 Bearer 만 덧붙인다
    query, headers = normalize_gemini_auth(
        "/gpgpta01-gpt/v1beta/models/gemini-3.6-flash:streamGenerateContent",
        "alt=sse&key=SECRET",
        {"Content-Type": "application/json"},
    )
    assert query == "alt=sse&key=SECRET", query
    assert headers["Authorization"] == "Bearer SECRET"

    query, headers = normalize_gemini_auth(
        "/gpgpta01-gpt/v1beta/models/gemini-3.6-flash:generateContent",
        "",
        {"x-goog-api-key": "HEADERKEY"},
    )
    assert headers["x-goog-api-key"] == "HEADERKEY"  # 게이트웨이가 이걸 볼 수도 있다
    assert headers["Authorization"] == "Bearer HEADERKEY"

    # 이미 Authorization 이 있으면 그쪽이 이긴다
    _, headers = normalize_gemini_auth(
        "/gpgpta01-gpt/v1beta/models/x:generateContent",
        "key=SECRET",
        {"Authorization": "Bearer REAL"},
    )
    assert headers["Authorization"] == "Bearer REAL"

    # Gemini 경로가 아니면 아무것도 건드리지 않는다 (Claude·Codex 무영향)
    query, headers = normalize_gemini_auth(
        "/gpgpta01-gpt/v1/messages", "key=SECRET", {"x-goog-api-key": "K"}
    )
    assert query == "key=SECRET" and headers == {"x-goog-api-key": "K"}

    # 6b. Hermes anthropic_messages: x-api-key → Bearer 보강 (원래 헤더 유지)
    headers = normalize_anthropic_auth({"x-api-key": "pgpt-tok", "Content-Type": "application/json"})
    assert headers["Authorization"] == "Bearer pgpt-tok"
    assert headers["x-api-key"] == "pgpt-tok"
    headers = normalize_anthropic_auth({"Authorization": "Bearer REAL", "x-api-key": "sk-ant-personal"})
    assert headers["Authorization"] == "Bearer REAL"
    assert "x-api-key" not in headers  # 개인 키가 게이트웨이로 새지 않는다(v16)
    assert normalize_anthropic_auth({"Content-Type": "application/json"}) == {
        "Content-Type": "application/json"
    }

    # Gemini CLI 0.55 의 도구용 가상 모델명은 P-GPT 등록 모델로 되돌린다.
    assert normalize_gemini_model_path(
        "/gpgpta01-gpt/v1beta/models/gemini-3.1-pro-preview-customtools:generateContent"
    ) == "/gpgpta01-gpt/v1beta/models/gemini-3.1-pro-preview:generateContent"
    assert normalize_gemini_model_path(
        "/gpgpta01-gpt/v1beta/models/gemini-3.6-flash:generateContent"
    ) == "/gpgpta01-gpt/v1beta/models/gemini-3.6-flash:generateContent"

    # P-GPT 가 JSON 하나를 여러 data: 줄로 잘라도 완전한 이벤트로 합친다.
    broken_sse = (
        b'data: {"candidates":[{"content":{"parts":[{"text":"","thoughtSignature":"abc\n'
        b'data: def"}]}}]}\n\n'
        b'data: {"candidates":[{"content":{"parts":[{"text":"OK"}]}}]}\n\n'
    )
    reframed, joined = reframe_gemini_sse(broken_sse)
    events = [line[6:] for line in reframed.splitlines() if line.startswith(b"data: ")]
    assert joined == 1 and len(events) == 2
    for event in events:
        json.loads(event.decode("utf-8"))

    # 스트리밍 joiner 도 같은 결과를 낸다 (바이트가 한 글자씩 와도).
    joiner = GeminiSseJoiner()
    streamed: list[bytes] = []
    for byte in broken_sse:
        streamed.extend(joiner.feed(bytes([byte])))
    streamed.extend(joiner.finish())
    assert b"".join(streamed) == reframed
    assert joiner.joined_fragments == 1

    # 풀은 직접 연결(사내 HTTP_PROXY 무시) + 생성 카운터만 확인
    pool = UpstreamPool("http://127.0.0.1:9", max_idle=2)
    assert pool.stats()["upstream_idle"] == 0

    # 유휴 연결은 UPSTREAM_IDLE_TTL 이 지나면 재사용하지 않고 닫는다 (서버 keep-alive 만료 대비).
    class _FakeConn:
        def __init__(self) -> None:
            self.sock: object | None = object()
            self.closed = False

        def close(self) -> None:
            self.closed = True
            self.sock = None

    fresh = _FakeConn()
    pool.release(fresh, reuse=True)  # type: ignore[arg-type]
    assert pool.stats()["upstream_idle"] == 1
    assert pool.acquire() is fresh
    assert pool.stats()["upstream_reused"] == 1
    stale = _FakeConn()
    pool.release(stale, reuse=True)  # type: ignore[arg-type]
    pool._idle[-1] = (stale, time.monotonic() - UPSTREAM_IDLE_TTL - 1)  # type: ignore[list-item]
    try:
        pool.acquire()
    except OSError:
        pass  # 만료 뒤 새 연결을 127.0.0.1:9 에 열다 거부되는 것은 정상
    assert stale.closed
    assert pool.stats()["upstream_expired"] == 1 and pool.stats()["upstream_idle"] == 0

    # 짝 없는 surrogate 는 UTF-8 로 못 쓴다 — \uXXXX 로 되돌려 보낸다(예외로 연결이 끊기지 않게)
    lone = json.loads('{"t":"a\\ud83d b"}')
    assert _json_bytes(lone) == b'{"t":"a\\ud83d b"}'
    assert _json_bytes({"t": "한글"}) == '{"t":"한글"}'.encode("utf-8")

    # (우리 것) 안티그래비티의 제목 짓기는 등록 안 된 `-preview` 이름으로 온다 — 그것만 고친다.
    assert normalize_gemini_model_path(
        "/gpgpta01-gpt/v1beta/models/gemini-3.1-flash-lite-preview:streamGenerateContent"
    ) == "/gpgpta01-gpt/v1beta/models/gemini-3.1-flash-lite:streamGenerateContent"
    # ⚠ **게이트웨이에 있는 `-preview` 는 안 건드린다** — 접미사를 규칙으로 떼면 이 줄이 깨진다.
    assert normalize_gemini_model_path(
        "/gpgpta01-gpt/v1beta/models/gemini-3.1-pro-preview:streamGenerateContent"
    ) == "/gpgpta01-gpt/v1beta/models/gemini-3.1-pro-preview:streamGenerateContent"
    # 두 접미사가 겹쳐 와도 등록 이름으로 내려앉는다.
    assert normalize_gemini_model_path(
        "/gpgpta01-gpt/v1beta/models/gemini-3.1-flash-lite-preview-customtools:generateContent"
    ) == "/gpgpta01-gpt/v1beta/models/gemini-3.1-flash-lite:generateContent"

    # (우리 것 · 결정 0082) 압축 간결 지시는 기본으로 꺼져 있다 — 압축은 알아보되 본문은 안 고친다.
    assert COMPACT_CONCISE is False or os.environ.get("PGPT_PROXY_COMPACT_CONCISE")
    assert stats()["compact_concise"] is COMPACT_CONCISE

    # (v18) 하이쿠 대체 — 게이트웨이에 없는 이름은 규칙으로 잡고, 나머지 대시→점 변환은 그대로다
    for haiku in ("claude-haiku-4-5", "claude-haiku-4-5-20251001", "claude-3-5-haiku-latest", "Claude-Haiku-4.5"):
        assert normalize_pgpt_claude_model(haiku) == CLAUDE_HAIKU_SUBSTITUTE, haiku
    assert normalize_pgpt_claude_model("claude-opus-4-7") == "claude-opus-4.7"
    assert normalize_pgpt_claude_model("claude-sonnet-4.6") == "claude-sonnet-4.6"
    haiku_payload = {"model": "claude-haiku-4-5-20251001", "messages": []}
    assert normalize_claude_model_id(haiku_payload, "/gpgpta01-gpt/v1/messages") is True
    assert haiku_payload["model"] == CLAUDE_HAIKU_SUBSTITUTE

    # (v18) SSE 오류 프레임 — 게이트웨이가 180초 시한에 끊을 때 남기는 마지막 조각을 읽는다
    frame = (b'event: error\r\ndata: {"type":"error","error":{"type":"api_error","message":'
             b'"HTTP request execution did not complete before the specified timeout configuration: 180000 millis"}}\r\n\r\n')
    assert (sse_error_message(frame) or "").endswith("180000 millis")
    assert sse_error_message(b'data: {"type":"content_block_delta","delta":{"text":"error"}}\n\n') is None

    # (v19) 실행 절단 판정 — 시한 근방만 든다. 회사 PC 실측은 180.0s + HTTP 500 이었다.
    assert at_execution_limit(180.0) is True
    assert at_execution_limit(179.0) is True   # 측정 오차·앞단 지연을 담는 폭 안
    assert at_execution_limit(300.0) is True   # 넘겨 도착한 판도 든다
    assert at_execution_limit(170.0) is False  # 폭 밖의 느린 오류는 절단이 아니다
    assert at_execution_limit(12.5) is False
    assert "execution_cuts" in stats()

    # (v18) keepalive — 상류가 interval 보다 오래 침묵하면 주석이 나가고, 조각은 순서대로 그대로 온다
    class _Silent:
        def __init__(self) -> None:
            self.calls = 0

        def read1(self, _size: int) -> bytes:
            self.calls += 1
            if self.calls == 1:
                time.sleep(0.35)
                return b"data: one\n\n"
            if self.calls == 2:
                return b"data: two\n\n"
            return b""

    handler = ProxyHandler.__new__(ProxyHandler)
    handler.wfile = io.BytesIO()  # type: ignore[assignment]
    handler._chunked_out = False
    assert list(handler._read_chunks(_Silent(), 0.1)) == [b"data: one\n\n", b"data: two\n\n"]
    assert handler.wfile.getvalue().count(_KEEPALIVE_LINE) >= 2
    handler.wfile = io.BytesIO()  # type: ignore[assignment]
    assert list(handler._read_chunks(_Silent(), 0.0)) == [b"data: one\n\n", b"data: two\n\n"]
    assert handler.wfile.getvalue() == b""
    assert stats()["keepalives"] >= 2

    # (우리 것 · #118) 웹서치 메움 — 알아보기 · 바꾸기 · 짓기. HTTP 갈래는 `websearch_check.py` 가 잰다.
    ws_tool = {"type": "web_search_20250305", "name": "web_search", "max_uses": 8, "allowed_domains": ["python.org"]}
    ws_payload = {"model": "claude-opus-5", "tools": [ws_tool],
                  "messages": [{"role": "user", "content": _WEB_SEARCH_PROMPT_HEAD + "python 3.13 release notes"}]}
    assert web_search_tool(ws_payload) is ws_tool
    assert web_search_tool({"tools": [{"name": "WebSearch", "input_schema": {}}]}) is None  # 클라이언트 도구는 안 건다
    assert web_search_query(ws_payload) == "python 3.13 release notes"
    gem = web_search_gemini_payload("python 3.13 release notes", ws_tool)
    assert gem["tools"] == [{"googleSearch": {}}] and "python.org" in gem["contents"][0]["parts"][0]["text"]
    assert web_search_headers({"Authorization": "Bearer k1", "anthropic-version": "2023-06-01"}) == {
        "Authorization": "Bearer k1", "Content-Type": "application/json; charset=utf-8", "x-goog-api-key": "k1"}
    grounded = json.dumps({"candidates": [{"content": {"parts": [{"text": "plan", "thought": True}, {"text": "3.14.8"}]},
                                           "groundingMetadata": {"webSearchQueries": ["a", "b"], "groundingChunks": [
                                               {"web": {"uri": "https://r/1", "title": "python.org"}},
                                               {"web": {"uri": "https://r/1", "title": "python.org"}},
                                               {"web": {"uri": "https://r/2", "title": "docs.python.org"}},
                                               {"web": {"uri": "https://r/3", "title": "herodevs.com"}}]}}]}).encode()
    ws_msg = gemini_grounding_to_anthropic(grounded, "q", "claude-opus-5", ws_tool)
    assert [b["type"] for b in ws_msg["content"]] == ["server_tool_use", "web_search_tool_result", "text"]
    assert [r["url"] for r in ws_msg["content"][1]["content"]] == ["https://r/1", "https://r/2"]  # 겹침 · 남의 도메인 걷음
    assert ws_msg["content"][2]["text"] == "3.14.8"  # 생각 조각은 안 싣는다
    assert ws_msg["content"][1]["tool_use_id"] == ws_msg["content"][0]["id"]
    ws_events = b"".join(anthropic_message_events(ws_msg))
    assert b'"web_search_tool_result"' in ws_events and b'"https://r/2"' in ws_events
    ws_err = web_search_error_message("q", "claude-opus-5")
    assert ws_err["content"][1]["content"] == {"type": "web_search_tool_result_error", "error_code": "unavailable"}
    assert anthropic_message_events(ws_err)
    assert "web_search_filled" in stats()

    print("Self-test: OK")


def main() -> None:
    # 재설치 · 키 교체는 옛 프록시를 끄자마자 새 프록시를 띄운다. 옛 프록시의 연결이 아직 닫히는 중이면 bind 가
    # 잠깐 실패할 수 있다 — 바로 죽으면 다음 로그인까지 프록시가 없으므로 15초 동안 다시 시도한다.
    deadline = time.monotonic() + 15
    while True:
        try:
            server = ProxyServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
            break
        except OSError as error:
            if time.monotonic() < deadline:
                time.sleep(0.5)
                continue
            log(f"bind {LISTEN_HOST}:{LISTEN_PORT} failed: {error}")
            print(f"포트 {LISTEN_PORT} 점유: {error}", file=sys.stderr)
            raise SystemExit(2)

    log(f"started pid={os.getpid()} version={VERSION} python={sys.version.split()[0]}")
    PID_PATH.write_text(str(os.getpid()), encoding="ascii")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        PID_PATH.unlink(missing_ok=True)
        log("stopped")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        main()
