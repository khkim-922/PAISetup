"""사내 게이트웨이(P-GPT) 앞의 로컬 호환 프록시.

한 프로세스가 클라이언트 셋의 길을 받아, 본문을 게이트웨이가 받는 꼴로 고쳐 같은 경로로 넘기고 응답은 거의
그대로 중계한다::

    Claude Code           -> http://127.0.0.1:18901/gpgpta01-gpt          (끝에 /v1 없음)
    Codex · OpenAI 호환   -> http://127.0.0.1:18901/gpgpta01-gpt/v1
    agy(Gemini)           -> http://127.0.0.1:18901/gpgpta01-gpt/v1beta

부르는 꼴::

    python opus5_proxy.py              # 127.0.0.1:18901 에서 듣는다(PGPT_PROXY_PORT 로 바꾼다)
    python opus5_proxy.py --self-test  # 보정 함수를 스스로 검사하고 끝난다

내는 것 — 고친 요청의 응답 · GET /health 의 상태와 계수 · 제 파일 곁의 proxy.log(1 MB 를 넘으면
proxy.log.1 로 넘긴다)와 opus5_proxy.pid.

무엇을 왜 고치나와 손잡이(PGPT_PROXY_*)는 곁 README 의 「무엇을 쓰고 무엇이 노나」가 든다.
"""

from __future__ import annotations

import fnmatch
import hashlib
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
import traceback
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import quote, unquote_plus, urlsplit

LISTEN_HOST = "127.0.0.1"
# 시험(Test-ProxyFaults.py · pair_check.py 등)만 다른 포트를 쓴다. 설치기는 늘 18901 을 쓴다.
LISTEN_PORT = int(os.environ.get("PGPT_PROXY_PORT", "18901"))
# ⚠ 프로토콜은 http 다 — https 는 연결되지 않는다. 바꾸는 것은 개발 게이트웨이(taigpt) · 시험 스텁일 때뿐이다.
UPSTREAM = os.environ.get("PGPT_PROXY_UPSTREAM", "http://aigpt.posco.net").rstrip("/")
ALLOWED_PREFIX = "/gpgpta01-gpt/"
# 앞 칸은 마지막으로 받은 상류 판(결정 0163 — 33 에 선다), 뒤 칸은 그 위에 우리가 얹은 덩어리 수다.
# ⚠ 설치기는 두 이름을 각각 정수로 읽어 견준다 — 점 찍힌 `VERSION` 을 문자열로 견주면 `"9" > "10"` 이 된다.
VERSION_UPSTREAM = 33
VERSION_OURS = 5
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


# 게이트웨이는 생각 구간의 조각을 안 흘린다 — 침묵 동안 주석이 없으면 Claude Code 의 바이트 유휴 워치독이 끊는다.
KEEPALIVE_SEC = _env_float("PGPT_PROXY_KEEPALIVE_SEC", 15.0)
_KEEPALIVE_LINE = b": keepalive\n\n"
# 기본 끔(결정 0082) — 우리는 1M 창이라 압축이 드물고, 드문 압축을 짧게 줄이면 잃는 것이 더 크다.
COMPACT_CONCISE = os.environ.get("PGPT_PROXY_COMPACT_CONCISE", "0").lower() not in {"0", "false", "off"}
# ⚠ 진단용 — 비스트리밍 경로에서는 큰 도구 인자가 {} 로 빈다(결정 0051). 도구를 쓰는 클라이언트에는 켜지 않는다.
CLAUDE_UNSTREAM = os.environ.get("PGPT_PROXY_CLAUDE_UNSTREAM", "0").lower() in {"1", "true", "on"}
COMPACT_UNSTREAM = os.environ.get("PGPT_PROXY_COMPACT_UNSTREAM", "1").lower() not in {"0", "false", "off"}
MAX_UNSTREAM_BYTES = 32 * 1024 * 1024
# ── 웹서치 메움 — 왜 메우나는 README 「Claude 웹서치 메움」 칸 ─────────────────────────────────
WEB_SEARCH = os.environ.get("PGPT_PROXY_WEB_SEARCH", "1").lower() not in {"0", "false", "off"}
HOIST_TOOL_IMAGES = os.environ.get("PGPT_PROXY_HOIST_TOOL_IMAGES", "1").lower() not in {"0", "false", "off"}
GROK_STRIP = os.environ.get("PGPT_PROXY_GROK_STRIP", "1").lower() not in {"0", "false", "off"}
# -customtools 는 게이트웨이에 없는 이름이다(normalize_gemini_model_path 와 같은 자).
WEB_SEARCH_MODEL = os.environ.get("PGPT_PROXY_WEB_SEARCH_MODEL", "gemini-3.6-flash").strip().removesuffix("-customtools")
# 상류 기본 시한(600초)을 따르면 막힌 게이트웨이 앞에서 CLI 가 10분씩 묶인다.
WEB_SEARCH_TIMEOUT = _env_float("PGPT_PROXY_WEB_SEARCH_TIMEOUT", 90.0)
# 출처 풀기는 기본 끔(결정 0165) — 회사 웹필터가 구글 클라우드를 200 차단 페이지로 받아 3xx · Location 이 안 오고,
# 켜 두면 검색 턴마다 차단될 바깥 요청이 필터 로그에 쌓인다. 정책이 풀리면 PGPT_PROXY_WEB_SEARCH_RESOLVE=1 로 켠다.
# ⚠ 켜면 HEAD 는 게이트웨이가 아니라 PC 에서 vertexaisearch.cloud.google.com 으로 직접 나간다(질의 글은 안 실리고
#   리디렉트 토큰만 나간다). 못 풀면 구글 경유 주소를 그대로 둔다.
WEB_SEARCH_RESOLVE = os.environ.get("PGPT_PROXY_WEB_SEARCH_RESOLVE", "0").lower() not in {"0", "false", "off"}
WEB_SEARCH_RESOLVE_TIMEOUT = _env_float("PGPT_PROXY_WEB_SEARCH_RESOLVE_TIMEOUT", 4.0)
_GROUNDING_REDIRECT_HOST = "vertexaisearch.cloud.google.com"
# CLI 2.1.293 의 문구다 — CLI 가 바꾸면 메움이 멎는다(/health 의 web_search_filled 가 안 오른다).
_WEB_SEARCH_PROMPT_HEAD = "Perform a web search for the query: "
# 경로 시한(180 · 300초) 안에 끝나는 크기 — 셈은 README 「출력 상한」 칸. 0 이면 클라이언트 값 그대로.
STREAM_MAX_TOKENS = int(_env_float("PGPT_PROXY_STREAM_MAX_TOKENS", 10000))
NONSTREAM_MAX_TOKENS = int(_env_float("PGPT_PROXY_NONSTREAM_MAX_TOKENS", 18000))
# 100만 입력 토큰을 읽는 초 — 켜면 큰 본문의 출력 상한을 그만큼 더 낮춘다. 기본 0(끔) · 값은 README 「입력 크기로
# 출력 상한 낮추기」 칸.
INPUT_READ_SEC_PER_MTOK = _env_float("PGPT_PROXY_INPUT_READ_SEC_PER_MTOK", 0.0)
_INPUT_BYTES_PER_TOKEN = 3.0
_OUTPUT_SEC_PER_TOKEN = 0.015  # 잰 최악값 — 출력 토큰당 15.0ms
_TURN_BASE_SEC = 1.2
STREAM_LIMIT_SEC = 180.0  # 게이트웨이의 스트리밍 실행 시한(오류 문구 「timeout configuration: 180000 millis」)
NONSTREAM_LIMIT_SEC = 300.0  # 앞단 HAProxy 의 504 시한(잰 값 300.0~300.3초)
# 상한 계산은 절단 판정 손잡이(EXECUTION_LIMIT_SEC)가 아니라 이 실측 시한을 쓴다 — 그 손잡이를 낮춰 절단을 흉내 내는
# 시험이 상한까지 바닥으로 끌어내리지 않게 한다
_CAP_MARGIN_SEC = 5.0
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
# 알아보는 기준 — 머리 줄과 과제 문장의 앞부분. 위 두 상수는 시험과 문서의 기준 문구로 남긴다.
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
# 180초 절단은 SSE error 프레임 없이 `HTTP 500` 으로도 온다 — 경과가 이 창에 든 비-2xx 를 따로 센다(execution_cuts).
EXECUTION_LIMIT_SEC = _env_float("PGPT_PROXY_EXECUTION_LIMIT_SEC", STREAM_LIMIT_SEC)
# 시한 근방으로 볼 폭(초). 180.0 실측에 맞추되 측정 오차와 앞단 지연을 담는다.
EXECUTION_LIMIT_MARGIN_SEC = _env_float("PGPT_PROXY_EXECUTION_LIMIT_MARGIN_SEC", 5.0)
# 게이트웨이 목록을 못 읽었을 때 하이쿠가 갈 자리 — 목록을 읽으면 목록이 먼저다(resolve_claude_model).
CLAUDE_HAIKU_SUBSTITUTE = "claude-sonnet-4.6"
# 기본 0(끔) — 켜면 자리 없는 요청이 429 를 받아 긴 압축 중에 다른 탭의 재시도를 소진한다.
HEAVY_REQUEST_BYTES = int(_env_float("PGPT_PROXY_HEAVY_BYTES", 0))
HEAVY_CONCURRENCY = int(_env_float("PGPT_PROXY_HEAVY_CONCURRENCY", 1))
# 응답 머리 전에는 SSE 주석을 못 보내니 오래 붙잡지 않는다 — 시한이 지나면 429 로 재시도를 알린다.
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
    """P-GPT 게이트웨이로 가는 keep-alive 연결 풀.

    요청마다 TCP 를 새로 열면 사내망에서 핸드셰이크만 수십 ms 가 들고, 도구 루프 대화는 그 값을 되풀이해 낸다. 연결은 사내
    HTTP_PROXY 를 안 타고 게이트웨이로 직결한다.
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
        """풀에서 연결을 꺼낸다. ``conn.pgpt_reused`` 가 유휴 풀에서 왔는지를 든다.

        ``fresh=True`` 면 풀을 건너뛴다 — 죽은 풀 연결 뒤의 재시도가 같은 까닭(게이트웨이 재시작 · LB 전환)으로 죽은 다른
        연결을 집으면 안 된다.
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
_HOISTED_TOOL_IMAGES = 0
_GROK_DROPPED_TOTAL = 0
_SLOW_TOTAL = 0
_KEEPALIVE_TOTAL = 0
_STREAM_ERROR_TOTAL = 0
_STREAM_INCOMPLETE_TOTAL = 0
_STREAM_UNVERIFIED_TOTAL = 0
_COMPACT_MAX_TOKENS_HIT_TOTAL = 0
_MAX_TOKENS_HIT_TOTAL = 0
_EXECUTION_CUT_TOTAL = 0
_EXECUTION_CUT_300_TOTAL = 0
_MAX_REQUEST_BYTES = 0
_MODEL_SUBSTITUTION_TOTAL = 0
_HEAVY_SERIALIZED_TOTAL = 0
_HEAVY_QUEUE_TIMEOUT_TOTAL = 0
_HEAVY_WAIT_SEC_TOTAL = 0.0
_HEAVY_WAIT_MAX_SEC = 0.0
_CLIENT_CANCELLED_TOTAL = 0
_ACTIVE_REQUESTS = 0
_WEB_SEARCH_FILLED = 0
_WEB_SEARCH_FAILED = 0
_WEB_SEARCH_EMPTY = 0  # filled 에도 든다


class _ClientDisconnected(Exception):
    """응답을 보내기 전에 클라이언트가 끊었다."""


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
        """(들어왔나, 기다린 초)를 돌려준다. 취소되면 — 들어가기 직전이라도 — 예외를 낸다."""
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
    """로그에 남길 설정만 고른다 — 프롬프트 · 도구 · 머리 · 임의 객체는 안 남긴다."""
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
    """Claude Code 의 압축 요청인가 — 크기 · 스트림 여부가 아니라 압축 프롬프트(_is_compact_text)로 가린다.

    Claude Code 2.1.290 은 압축에 본 세션의 system 프롬프트와 도구를 그대로 싣고, 이 경로에서는 압축 머리글을 안
    보낸다.
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


# Claude Code 2.1.283 의 출력 한도 복구 문구 — 압축 안의 이어 쓰기를 압축과 같은 비스트리밍 길로 보내려고 알아본다.
# CLI 가 문구를 바꾸면 이어 쓰기가 스트리밍 길로 새어 180초 벽에 걸린다.
_OUTPUT_LIMIT_RESUME_HEAD = "Output token limit hit. Resume directly"


def is_compaction_continuation(payload: dict) -> bool:
    """압축 안에서 「max_tokens 뒤 이어 쓰기」를 하는 턴인가.

    마지막 user 글이 클라이언트의 출력 한도 복구 문구이고 앞선 user 메시지에 압축 프롬프트가 있으면 참이다. 이 판을 못 가리면
    이어 쓰기가 평범한 스트리밍 턴으로 나가, 이어 쓰는 요약이 180초 벽에 걸린다.
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
    """클라이언트의 압축 프롬프트 무리에 맞나 — 머리 줄이 맨 앞에 서고 그 가까이에 요약 과제 문장이 있으면 맞다.

    한 가지 문구에 바이트로 묶지 않는다 — CLI 가 문구 하나를 바꾸는 날 압축이 조용히 180초 스트리밍 길로 돌아간다. Claude
    Code 2.1.283 의 과제 셋(대화 전체 · 이어지는 세션 · 최근 부분)을 받는다. 인용된 프롬프트는 안 맞는다.
    """
    if not isinstance(text, str) or not text.startswith(_COMPACT_PREAMBLE_HEAD):
        return False
    return _COMPACT_TASK_HEAD in text[:_COMPACT_TASK_WINDOW]


def cap_claude_output(payload: dict, *, unstream: bool, body_bytes: int = 0) -> str:
    """Claude 호출의 출력을 그 경로의 게이트웨이 시한 안으로 묶는다.

    max_tokens(와 켜진 thinking 예산)를 낮추기만 한다 — 프롬프트 · 이력 · 도구 · effort 는 그대로다. 바꿨으면
    로그용 설명(값만)을 돌려준다.
    """
    cap = output_cap(unstream=unstream, body_bytes=body_bytes)
    if not cap:
        return ""
    current = payload.get("max_tokens")
    if type(current) is int and 0 < current <= cap:
        return ""
    payload["max_tokens"] = cap
    thinking = payload.get("thinking")
    if isinstance(thinking, dict) and type(thinking.get("budget_tokens")) is int and thinking["budget_tokens"] > cap // 2:
        # Anthropic 은 budget_tokens < max_tokens 를 요구한다. 요약 글 자리로 상한의 절반은 남긴다 — 생각이 길면
        # 요약이 안 남는다.
        payload["thinking"] = {**thinking, "budget_tokens": max(1024, cap // 2)}
    return f"max_tokens_cap={cap}"


def output_cap(*, unstream: bool, body_bytes: int = 0) -> int:
    """그 경로에 실제로 거는 max_tokens 상한(0 = 끔).

    body_bytes > 0 이면 큰 입력을 읽는 시간만큼 더 낮춘다(INPUT_READ_SEC_PER_MTOK). 결과는 4096 아래로
    안 내려간다 — 잰 가장 긴 압축이 6,948 토큰이고, 압축이 타는 비스트리밍 경로는 1M 에서도 그보다 훨씬 남는다.
    """
    configured = NONSTREAM_MAX_TOKENS if unstream else STREAM_MAX_TOKENS
    if configured <= 0:
        return 0
    cap = max(4096, configured)
    if body_bytes > 0 and INPUT_READ_SEC_PER_MTOK > 0:
        read_sec = body_bytes / _INPUT_BYTES_PER_TOKEN / 1_000_000 * INPUT_READ_SEC_PER_MTOK
        limit = NONSTREAM_LIMIT_SEC if unstream else STREAM_LIMIT_SEC
        room = int((limit - _CAP_MARGIN_SEC - _TURN_BASE_SEC - read_sec) / _OUTPUT_SEC_PER_TOKEN)
        cap = min(cap, max(4096, room))
    return cap


def tune_claude_compaction(payload: dict) -> str:
    """압축 요청 끝에 간결 지시를 덧붙인다 — 원래 요청은 그대로 둔다.

    지시는 부드러운 목표라 출력을 자르거나 지어내지 않는다. 딱딱한 상한은 cap_claude_output 의 몫이다. 바꿨으면 로그용
    설명(값만)을 돌려준다.
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
        or stripped.endswith("/v1/alpha/search")
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


def _count_model_substitution() -> None:
    global _MODEL_SUBSTITUTION_TOTAL
    with _STATS_LOCK:
        _MODEL_SUBSTITUTION_TOTAL += 1


def _note_request_bytes(size: int) -> None:
    """가장 큰 요청 본문을 남긴다 — 입력 크기에 따른 출력 상한(output_cap)의 계수를 다듬을 자료다."""
    global _MAX_REQUEST_BYTES
    with _STATS_LOCK:
        if size > _MAX_REQUEST_BYTES:
            _MAX_REQUEST_BYTES = size


def _count_web_search(filled: bool, empty: bool = False) -> None:
    global _WEB_SEARCH_FILLED, _WEB_SEARCH_FAILED, _WEB_SEARCH_EMPTY
    with _STATS_LOCK:
        if filled:
            _WEB_SEARCH_FILLED += 1
            if empty:
                _WEB_SEARCH_EMPTY += 1
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


def _count_hoisted(count: int) -> None:
    global _HOISTED_TOOL_IMAGES
    with _STATS_LOCK:
        _HOISTED_TOOL_IMAGES += count


def _count_grok_dropped(count: int) -> None:
    global _GROK_DROPPED_TOTAL
    with _STATS_LOCK:
        _GROK_DROPPED_TOTAL += count


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


def _count_execution_cut(nonstream: bool = False) -> None:
    global _EXECUTION_CUT_TOTAL, _EXECUTION_CUT_300_TOTAL
    with _STATS_LOCK:
        _EXECUTION_CUT_TOTAL += 1
        if nonstream:
            _EXECUTION_CUT_300_TOTAL += 1


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
            "hoist_tool_images": HOIST_TOOL_IMAGES,
            "hoisted_tool_images": _HOISTED_TOOL_IMAGES,
            "grok_strip": GROK_STRIP,
            "grok_params_dropped": _GROK_DROPPED_TOTAL,
            "web_search": WEB_SEARCH,
            "web_search_model": WEB_SEARCH_MODEL,
            "web_search_filled": _WEB_SEARCH_FILLED,
            "web_search_failed": _WEB_SEARCH_FAILED,
            "web_search_empty": _WEB_SEARCH_EMPTY,
            "web_search_resolve": WEB_SEARCH_RESOLVE,
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
            # 그중 300초 근방(앞단 504) — 180초 판과 따로 세야 압축 경로의 절단 빈도가 보인다
            "execution_cuts_300": _EXECUTION_CUT_300_TOTAL,
            "max_request_bytes": _MAX_REQUEST_BYTES,
            "model_substitutions": _MODEL_SUBSTITUTION_TOTAL,
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
    base.update(_GATEWAY_MODELS.stats())
    return base


def log(message: str) -> None:
    """proxy.log 에 한 줄 덧붙인다. 예외를 안 낸다 — 기록 때문에 요청이 죽으면 안 된다."""
    try:
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with _LOG_LOCK:
            if LOG_PATH.exists() and LOG_PATH.stat().st_size > LOG_MAX_BYTES:
                # 한 세대 남긴다 — 절단 직전의 증거를 지우지 않게. Windows 에서 남이 파일을 잡고 있으면 이번에는 넘기고 이어 쓴다.
                try:
                    os.replace(LOG_PATH, LOG_PATH.with_name(LOG_PATH.name + ".1"))
                except OSError:
                    # 끝없이 키우지는 않는다 — 한도의 두 배를 넘으면 바꿀 수 있을 때까지 새 줄을 버린다
                    if LOG_PATH.stat().st_size > LOG_MAX_BYTES * 2:
                        return
            with LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(f"{stamp} {message}\n")
    except OSError:
        pass


class _BadRequestBody(Exception):
    """클라이언트의 요청 본문이 깨졌거나 덜 왔다 — 400 으로 답하고 상류로 안 보낸다."""


class _UpstreamReadError(Exception):
    """본문을 중계하다 난 상류 소켓 · 파싱 실패 — 원래 예외를 싸서 넘긴다."""


class SseObserver:
    """클라이언트로 보내는 바이트를 안 바꾸고 완성된 SSE 이벤트를 지켜본다.

    줄 · 이벤트 경계는 어느 읽기에서든 끊길 수 있다(CRLF · UTF-8 포함). 들여다보는 양에는 한도가 있어 너무 큰 이벤트는 쌓지
    않고 건너뛴다 — 그 탓에 끝 이벤트를 못 확인하면 멀쩡한 응답을 실패로 돌리지 않고 「확인 못 함」으로 센다. 생성된 글에서 표지를
    찾지 않는다.
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
        # 끝나지 않은 data/event 안에 빈 줄을 끼우면 그 이벤트가 일찍 나간다. 쪼개진 CRLF 의 CR 과 LF 사이에도
        # 끼우지 않는다.
        return self._size == 0 and not self._line_has_bytes and not self._after_cr

    def diagnostics(self, started: float) -> str:
        def elapsed(value: float | None) -> str:
            return f"{max(0.0, value - started):.3f}s" if value is not None and started else "none"
        return (f"events={self.events} last_event={self.last_event} "
                f"first_event={elapsed(self.first_event_at)} first_text={elapsed(self.first_text_at)} "
                f"output_tokens={self.output_tokens if self.output_tokens is not None else 'unknown'} "
                f"stop_reason={self.stop_reason}")

    def feed(self, chunk: bytes) -> None:
        # 디코딩 전에 자른다 — UTF-8 한 글자가 소켓 읽기 둘에 걸칠 수 있다.
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
        # OpenAI chat SSE 는 event/type 칸 없이 {"error": {...}} 를 실을 수 있다.
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
    """프레임 하나를 통째로 보는 도우미(부르는 쪽 · 시험용). 실제 스트림은 읽기를 가로질러 SseObserver 하나를 쓴다."""
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
        # 받은 그대로 \uXXXX 로 되돌려 보낸다 — 그러지 않으면 예외가 나 응답 없이 연결이 끊긴다.
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
        function = tool.get("function")
        if tool.get("type") == "function" and isinstance(function, dict):
            # chat/completions 꼴은 description 이 function 안에 있다 — 바깥에 넣으면 도구마다 모르는 칸이 붙는다.
            inner = function.get("description")
            if inner is None or (isinstance(inner, str) and not inner.strip()):
                function["description"] = f"{function.get('name') or f'tool_{index}'} tool"
                patched += 1
            continue
        if not isinstance(tool.get("name"), str) and not isinstance(tool.get("tools"), list):
            continue  # hosted 도구({"type": "web_search"} 등)에는 description 칸이 없다 — 붙이면 게이트웨이가 요청을 거절한다(#121)
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
    """도구 정의가 실리는 문서화된 자리 둘 — 최상위 ``tools`` 와 Responses 의 ``input[*].tools`` — 의 빈
    description 을 채우고 채운 수를 돌려준다.

    ⚠ 본문 전체를 훑지 않는다 — 대화 이력(tool_use input 등)에 우연히 든 "tools" 까지 바뀐다. Gemini 경로는
    부르는 쪽이 건너뛴다(그 스키마에는 description 칸이 없다).
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
    """GPT-5 · GPT-6 · o 계열 경로의 옛 토큰 한도 이름을 바꾼다.

    새 GPT 5.x · 6.x 와 o 계열 chat 경로는 max_tokens 를 「Unsupported parameter:
    'max_tokens'」로 거절하고, GPT-4.x · Grok 경로는 아직 받는다. 새 이름이 드는 모델 계열의 OpenAI 호환 생성
    요청만 바꾸고, Claude · Gemini 경로는 안 건드린다.
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


# Grok 4 계열 추론 모델이 받지 않는 필드. 하나라도 있으면 xAI 가 턴 전체를 400 으로 돌려준다.
_GROK_REASONING_REJECTS = ("presence_penalty", "frequency_penalty", "stop")
# reasoning_effort 까지 거부하는 옛 ID(게이트웨이 목록의 grok-4-1-fast-* 가 여기 든다). grok-4.3 이후는 low/medium/high 를 받는다.
_GROK_LEGACY_EFFORT = re.compile(r"^grok-4(?:-0709|-latest|-1-fast(?:-.*)?|-fast(?:-.*)?)?$", re.IGNORECASE)


def normalize_grok_params(payload: dict[str, object], path: str = "") -> list[str]:
    """Grok 4 추론 경로가 거부하는 필드를 떼고, 뗀 이름을 돌려준다.

    OpenAI 호환 생성 경로의 grok-4* 모델에만 건다. -non-reasoning 판은 penalty · stop 을 그대로 둔다.
    없는 필드는 안 세므로, 깨끗한 Grok Build 요청은 바이트 그대로 지나간다.
    """
    if not GROK_STRIP:
        return []
    normalized_path = path.rstrip("/")
    if not (normalized_path.endswith("/v1/chat/completions") or normalized_path.endswith("/v1/responses")):
        return []
    model = str(payload.get("model") or "").strip().lower()
    if not model.startswith("grok-4"):
        return []
    dropped: list[str] = []
    if "non-reasoning" not in model:
        for name in _GROK_REASONING_REJECTS:
            if name in payload:
                payload.pop(name)
                dropped.append(name)
    if _GROK_LEGACY_EFFORT.match(model):
        if "reasoning_effort" in payload:
            payload.pop("reasoning_effort")
            dropped.append("reasoning_effort")
        reasoning = payload.get("reasoning")
        if isinstance(reasoning, dict) and "effort" in reasoning:
            reasoning.pop("effort")
            if not reasoning:
                payload.pop("reasoning")
            dropped.append("reasoning.effort")
    return dropped


# 게이트웨이는 점 표기(claude-opus-4.6)만 받는데 Hermes 는 대시 표기로 바꿔 보낸다. 계열 이름은 고정하지 않는다 —
# 새 계열이 나와도 프록시를 안 고치게.
_CLAUDE_DASH_VERSION = re.compile(
    r"^(claude-[a-z]+-\d+)-(\d+)(.*)$",
    re.IGNORECASE,
)

# 게이트웨이 목록을 못 읽었을 때의 고정 규칙 — 목록을 읽으면 목록에서 고른다.
_CLAUDE_MODEL_ALIASES = {
    "claude-sonnet-5": "claude-sonnet-4.6",
    "claude-sonnet-latest": "claude-sonnet-4.6",
    "claude-3-7-sonnet-latest": "claude-sonnet-4.6",
    "claude-3-5-sonnet-latest": "claude-sonnet-4.5",
    "claude-opus-latest": "claude-opus-5",
}
# 대체할 이름이 목록에 없을 때 고를 계열. 대체는 Claude Code 가 곁 호출에 제 손으로 보내는 이름(하이쿠 ·
# claude-sonnet-5*)과 판을 안 박은 별칭(-latest)에만 건다 — 사람이 고르는 이름(claude-fable-* 등)을 구해 주면 400 이
# 보여야 할 자리에 다른 모델이 200 으로 답한다(결정 0164).
_CLAUDE_FALLBACK_FAMILIES = {"haiku": ("haiku", "sonnet")}


def parse_model_map(text: str) -> list[tuple[str, str]]:
    """``PGPT_PROXY_MODEL_MAP`` — ``요청이름=보낼이름`` 을 ``;`` · ``,`` · 줄바꿈으로 잇는다. 왼쪽은 글롭(*)."""
    rules: list[tuple[str, str]] = []
    for item in re.split(r"[;,\n]", text or ""):
        if "=" not in item:
            continue
        pattern, target = (part.strip() for part in item.split("=", 1))
        if pattern and target:
            rules.append((pattern.lower(), target))
    return rules


# 사용자가 정한 대체 규칙 — 목록보다 앞선다. 예: claude-haiku*=claude-sonnet-4.6;claude-sonnet-5*=claude-sonnet-5
MODEL_MAP = parse_model_map(os.environ.get("PGPT_PROXY_MODEL_MAP", ""))


def claude_family_version(model: str) -> tuple[str, tuple[int, ...]] | None:
    """``claude-sonnet-4.6`` → ("sonnet", (4, 6)), ``claude-3-5-sonnet-latest`` → ("sonnet", (3, 5)). 날짜 꼬리는 뺀다."""
    lower = re.sub(r"-\d{8}$", "", model.strip().lower())
    tokens = re.split(r"[-.]", lower)
    if len(tokens) < 2 or tokens[0] != "claude":
        return None
    family = next((token for token in tokens[1:] if token.isalpha() and token != "latest"), None)
    if not family:
        return None
    version = tuple(int(token) for token in tokens[1:] if token.isdigit() and len(token) <= 2)
    return family, version[:2]


def _dotted_claude_name(name: str) -> str:
    if "." in name:
        return name
    match = _CLAUDE_DASH_VERSION.match(name)
    if not match:
        return name
    return f"{match.group(1)}.{match.group(2)}{match.group(3)}"


def needs_model_list(model: object) -> bool:
    """대체 대상 이름(하이쿠 · claude-sonnet-5* · ``_CLAUDE_MODEL_ALIASES``)인가 — 이런 요청에만 목록을 읽는다."""
    if not isinstance(model, str):
        return False
    lower = model.strip().lower()
    return ("haiku" in lower or lower.startswith("claude-sonnet-5")
            or lower in _CLAUDE_MODEL_ALIASES)


def newest_listed_claude(family: str, listed: frozenset[str]) -> str | None:
    """목록에서 그 계열의 가장 높은 판. 날짜 붙은 이름은 고르지 않는다."""
    best: tuple[tuple[int, ...], str] | None = None
    for model_id in listed:
        if re.search(r"-\d{8}$", model_id):
            continue
        parsed = claude_family_version(model_id)
        if not parsed or parsed[0] != family:
            continue
        if best is None or parsed[1] > best[0]:
            best = (parsed[1], model_id)
    return best[1] if best else None


def resolve_claude_model(model: str, listed: frozenset[str] | None = None) -> tuple[str, str]:
    """(보낼 이름, 근거). 근거: config(사용자 규칙) · list(게이트웨이 목록) · fixed(기본 규칙) · spelling(표기만)."""
    name = model.strip()
    lower = name.lower()
    for pattern, target in MODEL_MAP:
        if fnmatch.fnmatchcase(lower, pattern):
            return target, "config"
    if listed is not None and needs_model_list(name):
        listed_lower = {item.lower(): item for item in listed}
        spelled = _dotted_claude_name(re.sub(r"-\d{8}$", "", name)).lower()
        if spelled in listed_lower:
            return listed_lower[spelled], "list"  # 게이트웨이가 들였다 — 대체하지 않는다
        parsed = claude_family_version(name)
        if parsed:
            for family in _CLAUDE_FALLBACK_FAMILIES.get(parsed[0], (parsed[0],)):
                pick = newest_listed_claude(family, listed)
                if pick:
                    return pick, "list"
    alias = _CLAUDE_MODEL_ALIASES.get(lower)
    if alias:
        return alias, "fixed"
    # 하이쿠는 게이트웨이에 없다 — 대시→점 변환보다 먼저 본다(그쪽을 먼저 타면 claude-haiku-4.5 가 되어
    # 여전히 없는 이름이다)
    if "haiku" in lower:
        return CLAUDE_HAIKU_SUBSTITUTE, "fixed"
    # 날짜 박힌 Anthropic ID: claude-sonnet-5-20260219
    if lower.startswith("claude-sonnet-5"):
        return "claude-sonnet-4.6", "fixed"
    return _dotted_claude_name(name), "spelling"


def normalize_pgpt_claude_model(model: str, listed: frozenset[str] | None = None) -> str:
    """Claude ID 의 점 표기를 되살리고, 게이트웨이 목록에 없는 별칭을 바꾼다."""
    if not isinstance(model, str):
        return model
    if not model.strip():
        return model
    return resolve_claude_model(model, listed)[0]


class GatewayModelList:
    """게이트웨이 ``/v1/models`` 를 키별로 읽어 둔다 — 대체할 이름이 들어왔을 때만 읽는다.

    못 읽으면 None 을 돌려 기본 규칙으로 간다(요청은 막지 않는다). 실패 뒤에는 ``retry`` 초 동안 다시 묻지 않고,
    전에 읽은 목록이 있으면 그것을 계속 쓴다. 키 원문은 남기지 않는다(해시만).
    """

    def __init__(self, base_url: str, *, ttl: float, retry: float, timeout: float) -> None:
        parts = urlsplit(base_url if "://" in base_url else f"http://{base_url}")
        self._scheme = parts.scheme
        self._host = parts.hostname or ""
        self._port = parts.port or (443 if parts.scheme == "https" else 80)
        self._ttl = ttl
        self._retry = retry
        self._timeout = timeout
        self._lock = threading.Lock()
        self._key_locks: dict[str, threading.Lock] = {}
        self._cache: dict[str, tuple[frozenset[str] | None, float, float]] = {}  # ids, 읽은 때, 다음에 물을 때
        self._fetches = 0
        self._failures = 0

    def stats(self) -> dict[str, object]:
        with self._lock:
            latest = max(self._cache.values(), key=lambda entry: entry[1], default=None)
            return {
                "model_list": self._ttl > 0,
                "model_list_fetches": self._fetches,
                "model_list_failures": self._failures,
                "model_list_size": len(latest[0]) if latest and latest[0] is not None else 0,
                "model_list_age_sec": round(time.monotonic() - latest[1]) if latest and latest[0] is not None else None,
                "model_map_rules": len(MODEL_MAP),
            }

    def _fetch(self, token: str) -> frozenset[str]:
        cls = http.client.HTTPSConnection if self._scheme == "https" else http.client.HTTPConnection
        conn = cls(self._host, self._port, timeout=self._timeout)
        try:
            conn.request("GET", f"{ALLOWED_PREFIX}v1/models", headers={"Authorization": f"Bearer {token}"})
            response = conn.getresponse()
            body = response.read()
        finally:
            conn.close()
        if response.status != 200:
            raise OSError(f"HTTP {response.status}")
        data = json.loads(body).get("data")
        if not isinstance(data, list):
            raise ValueError("no data list")
        return frozenset(str(item["id"]) for item in data if isinstance(item, dict) and item.get("id"))

    def get(self, token: str | None) -> frozenset[str] | None:
        if self._ttl <= 0 or not token or not self._host:
            return None
        key = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
        with self._lock:
            entry = self._cache.get(key)
            if entry and time.monotonic() < entry[2]:
                return entry[0]
            key_lock = self._key_locks.setdefault(key, threading.Lock())
        with key_lock:  # 같은 키로 동시에 들어온 요청은 한 번만 읽는다
            with self._lock:
                entry = self._cache.get(key)
                if entry and time.monotonic() < entry[2]:
                    return entry[0]
                self._fetches += 1
            try:
                ids = self._fetch(token)
            except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as error:
                with self._lock:
                    self._failures += 1
                    previous = entry[0] if entry else None
                    self._cache[key] = (previous, entry[1] if entry else 0.0, time.monotonic() + self._retry)
                log(f"model list unavailable ({type(error).__name__}: {error}) — "
                    f"{'keeping previous list' if previous is not None else 'using fixed substitutions'}")
                return previous
            now = time.monotonic()
            with self._lock:
                self._cache[key] = (ids, now, now + self._ttl)
            log(f"model list loaded: {len(ids)} models")
            return ids


# TTL 0 이면 목록을 안 읽고 고정 규칙만 쓴다.
_GATEWAY_MODELS = GatewayModelList(
    UPSTREAM,
    ttl=_env_float("PGPT_PROXY_MODEL_LIST_TTL_SEC", 600.0),
    retry=_env_float("PGPT_PROXY_MODEL_LIST_RETRY_SEC", 60.0),
    timeout=_env_float("PGPT_PROXY_MODEL_LIST_TIMEOUT_SEC", 5.0),
)


def bearer_token(headers: object) -> str | None:
    """요청 머리의 P-GPT 키 — ``Authorization: Bearer`` 가 먼저, 없으면 ``x-api-key``."""
    auth = headers.get("Authorization") if hasattr(headers, "get") else None
    if isinstance(auth, str) and auth.lower().startswith("bearer ") and auth[7:].strip():
        return auth[7:].strip()
    key = headers.get("x-api-key") if hasattr(headers, "get") else None
    return key.strip() if isinstance(key, str) and key.strip() else None


def is_model_substitution(before: object, after: object) -> bool:
    """같은 모델의 점 표기만 고친 것이 아니라 다른 모델로 보냈으면 참."""
    if not isinstance(before, str) or not isinstance(after, str):
        return False
    spelled = re.sub(r"-\d{8}$", "", before.strip().lower()).replace("-", ".")
    return spelled != after.strip().lower().replace("-", ".")


def normalize_claude_model_id(payload: dict[str, object], path: str = "",
                              listed: frozenset[str] | None = None) -> bool:
    """Messages 요청의 Claude 소수 판 ID 를 P-GPT 의 점 표기로 되살린다."""
    if not path.rstrip("/").endswith("/v1/messages"):
        return False
    model = payload.get("model")
    if not isinstance(model, str):
        return False
    fixed = normalize_pgpt_claude_model(model, listed)
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
    """단순한 OpenAI chat completion 본문을 Gemini native JSON 으로 옮긴다."""
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
    """Gemini generateContent JSON 을 OpenAI chat completion JSON 으로 옮긴다."""
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
    """Gemini 응답 하나를 완결된 OpenAI SSE 스트림으로 옮긴다."""
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


def _hoist_tool_images(content: list) -> int:
    """tool_result 안의 그림(_HOISTED_BLOCKS)을 같은 user 메시지의 마지막 tool_result 뒤로 옮기고, 옮긴 수를 돌려준다.

    빈 자리에는 옮겼다는 표지를 둔다 — tool_result 가 비면 모델이 「(empty)」로 읽는다. ⚠ 그림을 tool_result
    앞에 끼우지 않는다 — 짝 검사가 400 을 낸다. 왜 옮기나는 README 「그림 끌어내기」 칸.
    """
    moved: list[dict] = []
    last_result = -1
    for index, block in enumerate(content):
        if not isinstance(block, dict) or block.get("type") != "tool_result":
            continue
        last_result = index
        inner = block.get("content")
        if not isinstance(inner, list):
            continue
        before = len(moved)
        kept: list = []
        for item in inner:
            if isinstance(item, dict) and item.get("type") in _HOISTED_BLOCKS:
                moved.append({"type": "text", "text": f"[{item['type']} from tool result {block.get('tool_use_id', '')}]"})
                # cache_control 은 떼고 옮긴다 — 그대로 두면 캐시 경계가 하나 늘어 「cache_control 블록은 4개까지」 400 이 날 수 있다
                moved.append({k: v for k, v in item.items() if k != "cache_control"})
                kept.append({"type": "text", "text": f"[{item['type']} attached after this tool result]"})
            else:
                kept.append(item)
        if len(moved) > before:
            content[index] = {**block, "content": kept}
    if moved:
        content[last_result + 1:last_result + 1] = moved
    return len(moved) // 2


# 그림만 옮긴다 — PDF(document)는 게이트웨이가 자리와 상관없이 삼킨다(회사 실측 #193 ③㉡ · 결정 0165).
# ⚠ PDF 를 옮기면 tool_result 에는 「붙였다」는 표지만 남아 모델이 PDF 가 왔다고 믿는다.
_HOISTED_BLOCKS = {"image"}


def sanitize_payload(payload: dict[str, object]) -> dict[str, object]:
    """Anthropic /v1/messages 본문을 Bedrock 라우트가 받는 형태로 정리한다."""
    payload.pop("temperature", None)
    payload.pop("top_p", None)

    raw_messages = payload.get("messages")
    if isinstance(raw_messages, list):
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
        if HOIST_TOOL_IMAGES:
            hoisted = sum(_hoist_tool_images(m["content"]) for m in cleaned
                          if m["role"] == "user" and isinstance(m["content"], list))
            if hoisted:
                _count_hoisted(hoisted)
        payload["messages"] = cleaned

    return payload


def normalize_gemini_auth(
    path: str, query: str, headers: dict[str, str]
) -> tuple[str, dict[str, str]]:
    """Gemini 계열 요청에 ``Authorization: Bearer`` 를 덧붙인다 — ``x-goog-api-key`` ·
    ``?key=`` 의 키로.

    ⚠ 원래 헤더 · 쿼리는 떼지 않는다 — 그것을 보는 게이트웨이 경로에서 401 이 난다.
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
    """``x-api-key`` 만 온 Anthropic 호환 요청에 같은 키를 ``Authorization: Bearer`` 로 덧붙인다 —
    게이트웨이는 Bearer 만 본다.

    ⚠ Authorization 이 이미 있으면 x-api-key 는 뗀다 — Claude Code 는 사용자 환경의 개인
    ANTHROPIC_API_KEY 를 함께 실어, 두면 개인 키가 평문 HTTP 로 사내 게이트웨이에 간다.
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


# 안티그래비티가 제목 짓기에 박아 둔 이름 → 게이트웨이 등록 이름(README 「제미나이 이름 표」 칸).
# ⚠ `-preview` 를 규칙으로 떼지 않는다 — 게이트웨이에 실제로 있는 `gemini-3.1-pro-preview` 가 깨진다.
# 걷는 조건: 게이트웨이 /v1/models 에 왼쪽 이름이 서면 그 줄을 지운다.
_GEMINI_MODEL_ALIASES = {
    "gemini-3.1-flash-lite-preview": "gemini-3.1-flash-lite",
}


def normalize_gemini_model_path(path: str) -> str:
    """Gemini CLI 의 가상 접미사(-customtools)를 떼고, 안티그래비티가 박아 둔 이름을 게이트웨이 등록 이름으로 바꾼다.

    Gemini CLI 0.55 는 도구를 켜면 이 접미사를 붙이는데 P-GPT 는 바탕 모델 ID 만 등록한다 — 접미사는 클라이언트 쪽
    경로 표시이지 따로 있는 게이트웨이 모델이 아니다. 이름 표는 _GEMINI_MODEL_ALIASES 가 든다.
    """
    if not path.startswith(f"{GEMINI_PREFIX}/models/"):
        return path
    marker = ":"
    model_start = path.find("/models/") + len("/models/")
    model_end = path.find(marker, model_start)
    if model_end < 0:
        model_end = len(path)
    model = path[model_start:model_end]
    suffix = "-customtools"
    base_model = model[: -len(suffix)] if model.endswith(suffix) else model
    base_model = _GEMINI_MODEL_ALIASES.get(base_model, base_model)
    if base_model == model:
        return path
    normalized = path[:model_start] + base_model + path[model_end:]
    log(f"Gemini model alias normalized: {model} -> {base_model}")
    return normalized


class GeminiSseJoiner:
    """게이트웨이가 쪼갠 Gemini ``data:`` 조각을 바이트가 오는 대로 잇는다.

    게이트웨이는 큰 JSON(긴 ``thoughtSignature`` 등)을 ``data:`` 줄 여럿에 걸쳐 싸고, Gemini CLI 는
    줄마다 완결된 JSON 으로 읽어 진다. 다 받고 내보내면 첫 글자가 생성 시간 전체를 기다리므로 JSON 이 풀리는 대로 이벤트를
    내보낸다.
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
    """자체 검사가 쓰는, 한꺼번에 모아 잇는 도우미. 실제 트래픽은 GeminiSseJoiner 를 쓴다."""
    joiner = GeminiSseJoiner()
    parts = joiner.feed(raw)
    parts.extend(joiner.finish())
    return b"".join(parts), joiner.joined_fragments


def anthropic_message_events(message: object, *, tools: list | None = None, allow_tools: bool = True) -> list[bytes]:
    """완결된 message 를 SSE 이벤트로 바꾼다 — 도구 호출을 내보내기 전에 전부 검증한다.

    입력 JSON(큰 유니코드 문자열 포함)은 input_json_delta 로 싣는다 — SDK 가 버리는 빈 tool_use 시작 칸에는
    안 싣는다. 모르는 블록 종류는 모델 출력을 조용히 잃지 않고 드러내 실패한다.
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
            # 서버 검색 결과 — 실제 API 처럼 시작 칸에 통째로 싣는다(조각 없음).
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


# ── 웹서치 메움 — 알아보기 · 바꾸기 · 짓기. 프록시 칸은 `_forward_request` 의 `web_search` 갈래 ──
def web_search_tool(payload: dict) -> dict | None:
    """서버 웹서치 도구 선언(`web_search_*`)을 든 요청이면 그 선언을, 아니면 None."""
    tools = payload.get("tools")
    if not isinstance(tools, list):
        return None
    return next((tool for tool in tools if isinstance(tool, dict)
                 and str(tool.get("type", "")).startswith("web_search_")), None)


def web_search_query(payload: dict) -> str | None:
    """CLI 웹서치 하위 요청의 질의 — **마지막 user 메시지**에서 CLI 머리로 시작하는 글 조각의 나머지. 없으면 None.

    머리가 있는 조각만 메운다 — 웹서치 도구를 선언만 한 여러 턴 대화(SDK · 다른 도구)를 질의로 읽으면 답 대신 검색 결과만
    돌아가고, 머리 앞의 다른 조각(system-reminder 등)이 질의에 섞인다. None 이면 원래 길로 보낸다.
    """
    messages = payload.get("messages") or []
    if not isinstance(messages, list) or not messages:
        return None
    for text in _user_texts(messages[-1]):
        if isinstance(text, str) and text.lstrip().startswith(_WEB_SEARCH_PROMPT_HEAD):
            query = text.lstrip()[len(_WEB_SEARCH_PROMPT_HEAD):].strip()
            return query or None
    return None


def _bare_domain(value: str) -> str:
    """`https://www.python.org/blog` · `Python.org:443` 같은 꼴을 `python.org` 로 — 견주기 전에 맞춘다."""
    site = value.strip().lower()
    if "://" in site:
        site = site.split("://", 1)[1]
    site = site.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    site = site.rsplit("@", 1)[-1].split(":", 1)[0].strip(".")
    return site[4:] if site.startswith("www.") else site


def _domain_list(tool: dict, key: str) -> list[str]:
    values = tool.get(key)
    if not isinstance(values, list):
        return []
    return [d for d in (_bare_domain(v) for v in values if isinstance(v, str)) if d]


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


def _source_ok(site: str, allowed: list[str], blocked: list[str], exact: bool) -> bool:
    """grounding 출처 거르기. `site` 는 출처의 도메인 — 원래 주소를 풀었으면 그 호스트(exact), 못 풀었으면 제미나이가
    준 제목(대개 등록 도메인 `python.org`)이다. 도메인을 모르면(빈 값) 허용 목록이 있을 때 걷고, 차단 목록만 있으면 둔다.

    제목만 알 때는 허용 `docs.python.org` 에 제목 `python.org` 도 들인다 — 제미나이가 하위 도메인을 떼고 주므로
    가릴 수 없고, 다 걷으면 결과가 늘 빈다. 차단은 그렇게 넓히지 않는다(정확한 호스트일 때만 하위 도메인까지).
    """
    site = _bare_domain(site) if site else ""
    if not site:
        return not allowed

    def under(domain: str) -> bool:
        return site == domain or site.endswith("." + domain)

    if allowed and not any(under(d) or (not exact and d.endswith("." + site)) for d in allowed):
        return False
    return not any(under(d) for d in blocked)


def _resolve_grounding_url(url: str) -> str | None:
    """구글 경유 출처 주소의 원래 주소(Location). 경유 주소가 아니거나 못 풀면 None — 받은 주소를 그대로 쓴다."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != _GROUNDING_REDIRECT_HOST:
        return None
    conn = http.client.HTTPSConnection(parts.hostname, parts.port or 443, timeout=WEB_SEARCH_RESOLVE_TIMEOUT)
    try:
        conn.request("HEAD", parts.path + (f"?{parts.query}" if parts.query else ""),
                     headers={"User-Agent": "pgpt-proxy"})
        response = conn.getresponse()
        location = response.getheader("Location") or ""
        if 300 <= response.status < 400 and location.lower().startswith(("http://", "https://")):
            return location
    except (OSError, http.client.HTTPException, ValueError):
        pass
    finally:
        conn.close()
    return None


def resolve_grounding_urls(urls: list[str]) -> dict[str, str]:
    """경유 주소들을 한꺼번에 푼다(스레드 몇 개 · 전체 시한 WEB_SEARCH_RESOLVE_TIMEOUT + 1초). 푼 것만 돌려준다."""
    targets = [url for url in dict.fromkeys(urls) if urlsplit(url).hostname == _GROUNDING_REDIRECT_HOST]
    if not WEB_SEARCH_RESOLVE or not targets:
        return {}
    resolved: dict[str, str] = {}

    def work(url: str) -> None:
        real = _resolve_grounding_url(url)
        if real:
            resolved[url] = real

    threads = [threading.Thread(target=work, args=(url,), daemon=True) for url in targets[:10]]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + WEB_SEARCH_RESOLVE_TIMEOUT + 1.0
    for thread in threads:
        thread.join(max(0.0, deadline - time.monotonic()))
    return dict(resolved)


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


def gemini_grounding_to_anthropic(raw: bytes, query: str, model: str, tool: dict,
                                  resolve=resolve_grounding_urls) -> dict:
    """제미나이 grounding 답을 CLI 가 읽는 세 칸으로 — 출처는 `groundingChunks`, 본문은 생각 아닌 글 조각.

    출처 주소는 원래 주소로 풀어 싣고(못 풀면 경유 주소), 도메인 거르기는 푼 주소의 호스트로 한다.
    """
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
    sources: list[tuple[str, str, str]] = []  # (주소, 제목, 제미나이가 준 도메인)
    for chunk in meta.get("groundingChunks") or []:
        web = chunk.get("web") if isinstance(chunk, dict) else None
        url = web.get("uri") if isinstance(web, dict) else None
        if not isinstance(url, str) or not url:
            continue
        title = web.get("title") if isinstance(web.get("title"), str) else ""
        domain = web.get("domain") if isinstance(web.get("domain"), str) else ""
        sources.append((url, title.strip(), domain.strip()))
    real_urls = resolve([url for url, _, _ in sources]) if sources else {}
    results: list[dict] = []
    seen: set[str] = set()
    for url, title, domain in sources:
        real = real_urls.get(url, url)
        if real in seen:
            continue
        # 푼 원래 주소면 그 호스트가 가장 정확하다. 못 풀었으면 제미나이가 준 도메인 → 제목(대개 도메인) 차례로 본다
        site, exact = (urlsplit(real).hostname or "", True) if url in real_urls else (domain or title, False)
        if not _source_ok(site, allowed, blocked, exact):
            continue
        seen.add(real)
        results.append({"type": "web_search_result", "title": title or _bare_domain(site) or real, "url": real,
                        "encrypted_content": "", "page_age": None})
    usage_meta = data.get("usageMetadata") or {}
    searches = meta.get("webSearchQueries") if isinstance(meta.get("webSearchQueries"), list) else []
    usage = {"input_tokens": int(usage_meta.get("promptTokenCount") or 0),
             "output_tokens": int(usage_meta.get("candidatesTokenCount") or 0),
             "server_tool_use": {"web_search_requests": max(1, len(searches))}}
    return _web_search_message(query, model, results, text, usage)


def codex_web_search(payload: dict, path: str) -> dict[str, object] | None:
    """Codex 의 독립 ``alpha/search`` 명령을 Responses 웹 검색 요청으로 옮긴다 — 그 경로가 아니면 None.

    Codex 0.162 는 search · open · find 를 공급자 기준 이 엔드포인트로 보낸다. P-GPT 에는 이 엔드포인트가
    없지만, 같은 게이트웨이가 ``/v1/responses`` 에 ``web_search`` 를 선언하면 search 와
    ``open_page`` 를 수행한다.
    """
    if not path.rstrip("/").endswith("/v1/alpha/search"):
        return None
    commands = payload.get("commands")
    if not isinstance(commands, dict):
        commands = {}
    lines = ["Carry out these web operations. Use current web results and include source URLs."]
    labels = {
        "search_query": "Search",
        "image_query": "Image search",
        "open": "Open",
        "click": "Click",
        "find": "Find",
        "screenshot": "Screenshot",
        "finance": "Finance",
        "weather": "Weather",
        "sports": "Sports",
        "time": "Time",
    }
    for key, label in labels.items():
        values = commands.get(key)
        if isinstance(values, list) and values:
            lines.append(f"{label}: " + json.dumps(values, ensure_ascii=False, separators=(",", ":")))
    if len(lines) == 1:
        # 드문 꼴 · 빈 명령에는 최근 대화를 맥락으로 싣는다.
        lines.append("Context: " + json.dumps(payload.get("input") or "", ensure_ascii=False)[:12000])

    settings = payload.get("settings")
    filters = settings.get("filters") if isinstance(settings, dict) else None
    tool: dict[str, object] = {}
    if isinstance(filters, dict):
        for key in ("allowed_domains", "blocked_domains"):
            if isinstance(filters.get(key), list):
                tool[key] = filters[key]
    return {
        "query": "\n".join(lines),
        "model": str(payload.get("model") or "codex"),
        "tool": tool,
        "stream": False,
        "response": "codex",
        "upstream": "responses",
    }


def codex_responses_web_search_payload(search: dict[str, object]) -> dict:
    """Codex 웹 작업에 쓰는 게이트웨이 Responses 요청을 짓는다."""
    return {
        "model": str(search["model"]),
        "input": str(search["query"]),
        "tools": [{"type": "web_search"}],
    }


def codex_web_search_error(code: str = "unavailable") -> dict:
    """검색이 졌다는 것을 드러내며 Codex 턴은 살린다 — 결과가 빈 SearchResponse."""
    return {"encrypted_output": None, "output": f"Web search error: {code}", "results": []}


def responses_web_search_to_codex(raw: bytes) -> dict:
    """게이트웨이 Responses 답(open_page 인용 포함)을 Codex 의 SearchResponse 로 바꾼다."""
    response = json.loads(raw)
    output = response.get("output")
    if not isinstance(output, list):
        raise ValueError("Responses answer has no output list")
    texts: list[str] = []
    sources: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "output_text":
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
            annotations = part.get("annotations")
            if not isinstance(annotations, list):
                continue
            for annotation in annotations:
                if not isinstance(annotation, dict):
                    continue
                url = annotation.get("url")
                if not isinstance(url, str) or not url or url in seen:
                    continue
                seen.add(url)
                title = annotation.get("title")
                sources.append({"url": url, "title": title if isinstance(title, str) and title else url})
    results = [
        {"type": "text_result", "ref_id": f"turn0search{index}", **source}
        for index, source in enumerate(sources)
    ]
    text = "\n\n".join(texts).strip()
    if results:
        links = "\n".join(f"[{item['ref_id']}] {item['title']} — {item['url']}" for item in results)
        text = (text + "\n\nSources:\n" + links).strip()
    return {"encrypted_output": None, "output": text or "No web results found.", "results": results}


def web_search_error_code(status: int) -> str:
    """상류 상태 코드 → 서버 도구 검색 오류 코드(CLI 가 「Web search error: <code>」로 읽는다)."""
    if status == 429:
        return "too_many_requests"
    if status in {400, 413, 422}:
        return "invalid_input"
    return "unavailable"


def web_search_error_message(query: str, model: str, code: str = "unavailable") -> dict:
    """메우기가 졌을 때 — 서버 도구의 검색 오류 칸으로 돌려준다. CLI 는 「Web search error: <code>」로 읽는다."""
    return _web_search_message(query, model, {"type": "web_search_tool_result_error", "error_code": code}, "",
                               {"input_tokens": 0, "output_tokens": 0})


class ProxyHandler(BaseHTTPRequestHandler):
    _model_substituted = ""

    def end_headers(self) -> None:  # noqa: D102
        # 바꿔 보낸 요청의 200 을 「요청한 모델이 된다」로 읽지 않게 머리글로 밝힌다
        if self._model_substituted:
            self.send_header("x-pgpt-model-substituted", self._model_substituted)
        super().end_headers()

    protocol_version = "HTTP/1.1"
    _chunked_out = False
    _gw_request_id = ""
    _started = 0.0
    _upstream_started = 0.0
    _request_context = ""
    _keepalives_sent = 0
    _stream_outcome = "complete"

    def _client_disconnected(self) -> bool:
        """요청 · 이어 온 바이트를 소비하지 않고, 소켓 시한도 안 바꾸고 들여다본다."""
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
        """요청 본문을 읽는다 — chunked 전송도 받는다.

        Claude Code 와 Codex 는 큰 본문을 chunked 로 올린다. Content-Length 만 읽으면 그 본문이 조용히
        빠진다.
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

        # 길이가 숫자가 아니거나 덜 받은 본문은 상류로 보내지 않고 400 으로 돌려준다
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            raise _BadRequestBody("Content-Length 가 숫자가 아닙니다") from None
        if length < 0:
            raise _BadRequestBody("Content-Length 가 음수입니다")
        if not length:
            return None
        data = self.rfile.read(length)
        if len(data) < length:
            raise _BadRequestBody(f"본문이 덜 왔습니다({len(data)}/{length} 바이트)")
        return data

    def _exchange_upstream(self, conn: http.client.HTTPConnection, method: str, path: str,
                           body: bytes | None, headers: dict[str, str]) -> http.client.HTTPResponse:
        """응답 머리를 기다리며 클라이언트 취소를 알아챈다 — 긴 생각 턴도 같다.

        이 도우미가 request/getresponse 를 쥐고, 연결 정리는 부르는 쪽 몫이다. 취소되면 늦게 온 응답은 닫는다 — 소켓을
        살려 두거나 풀에 들지 않게. HTTP 상태 · 머리는 안 건드리고, 미리 SSE 200 을 보내지 않는다.
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
                    # 올리는 도중에 받은 413 같은 이른 거절은 그대로 지킨다.
                    try:
                        result = conn.getresponse()
                    except (http.client.HTTPException, OSError):
                        raise upload_error from None
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

    def _send_web_search(self, web_search: dict, message: dict) -> None:
        """메운 웹서치 답(또는 검색 오류 칸)을 CLI 가 보낸 꼴(SSE · JSON) 그대로 200 으로 보낸다."""
        if web_search["stream"]:
            data = b"".join(anthropic_message_events(message))
            content_type = "text/event-stream; charset=utf-8"
        else:
            data = _json_bytes(message)
            content_type = "application/json; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def _write_upstream(
        self,
        method: str,
        path: str,
        body: bytes | None,
        headers: dict[str, str],
        timeout: float | None = None,
    ) -> tuple[http.client.HTTPResponse, http.client.HTTPConnection]:
        """풀의 keep-alive 연결로 게이트웨이에 POST · GET 한다. ``timeout`` 은 이 요청의 응답 시한(초) — 준 연결은
        풀에 돌려보내지 말 것(부른 쪽 몫).
        """
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
            if timeout is not None and conn.sock is not None:
                conn.sock.settimeout(timeout)
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
        """상류 본문을 조각으로 내놓는다. 상류 실패는 ``_UpstreamReadError`` 로 올라온다.

        ``interval > 0`` 이면 도우미 스레드가 소켓을 읽고, ``interval`` 초 동안 아무것도 안 오면 클라이언트에 SSE
        주석을 보낸다 — 게이트웨이는 생각 조각을 안 흘려, 그대로 두면 클라이언트의 바이트 유휴 워치독이 끊는다.
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
                        raise ConnectionAbortedError("client disconnected during partial SSE event") from None
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
        """상류 본문을 클라이언트로 옮긴다. 끝까지 받았으면 True.

        끝까지 받았을 때만 chunked 끝 표시를 쓴다. 업스트림이 도중에 끊기면 끝 표시 없이 연결을 닫아 클라이언트가 잘린 응답임을 알게
        한다 — Connection: close 로만 끝내면 정상 종료와 안 갈린다. ``sse``(Anthropic · OpenAI 스트림)면
        게이트웨이의 ``error`` 프레임을 세고 기록한다 — 180초 시한의 자국이다.
        """
        joiner = GeminiSseJoiner() if gemini_sse else None
        observer = SseObserver(protocol) if sse else None
        # 그대로 중계하는 Claude 비스트리밍 응답(클라이언트가 청한 판 — 「Retrying without streaming」)은 드물고 작다 —
        # stop_reason 을 읽으려고 한도 있는 사본을 둔다.
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
                    # 성공한 chunked 끝 표시를 내지 않고, 모델 이벤트도 지어내지 않는다.
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
        self._model_substituted = ""
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

        try:
            body = self._read_body()
        except _BadRequestBody as error:
            log(f"bad request body {self.command} {parsed.path}: {error}")
            self._send_json(400, {"type": "error", "error": {"type": "invalid_request_error", "message": str(error)}},
                            keep_alive=False)
            return
        if body:
            _note_request_bytes(len(body))
        model_name = ""
        gemini_chat_model: str | None = None
        gemini_chat_stream = False
        claude_unstream = False
        compact_request = False
        claude_tools = None
        web_search: dict[str, object] | None = None
        if body:
            stripped_path = parsed.path.rstrip("/")
            is_messages = stripped_path.endswith("/v1/messages")
            is_codex_search = stripped_path.endswith("/v1/alpha/search")
            is_openai_generation = (
                stripped_path.endswith("/v1/chat/completions")
                or stripped_path.endswith("/v1/responses")
            )
            # tools 가 아예 없는 본문은 파싱 자체를 건너뛴다 (요청당 비용 절감).
            # 단 GPT-5/o 계열 토큰 파라미터 보정과 Gemini chat 변환은 짧은 호출에도 필요하다.
            if is_messages or is_openai_generation or is_codex_search or b'"tools"' in body:
                try:
                    payload_obj = json.loads(body)
                except (UnicodeDecodeError, ValueError, TypeError):
                    payload_obj = None

                if isinstance(payload_obj, dict):
                    changed = False
                    model_name = str(payload_obj.get("model") or "")
                    self._request_context += " " + request_settings(payload_obj)
                    # 웹서치 하위 요청은 Claude 갈래를 안 탄다 — 제미나이 grounding 요청으로 바꾼다.
                    codex_search = codex_web_search(payload_obj, parsed.path) if (is_codex_search and WEB_SEARCH) else None
                    web_tool = web_search_tool(payload_obj) if (is_messages and WEB_SEARCH) else None
                    web_query = web_search_query(payload_obj) if web_tool else None
                    if codex_search:
                        web_search = codex_search
                        payload_obj = codex_responses_web_search_payload(web_search)
                        changed = True
                        self._request_context += " kind=codex_web_search upstream=responses"
                    elif web_tool and web_query:
                        web_search = {"query": web_query, "model": model_name or "claude", "tool": web_tool,
                                      "stream": payload_obj.get("stream") is True}
                        payload_obj = web_search_gemini_payload(web_query, web_tool)
                        changed = True
                        self._request_context += f" kind=web_search search_model={WEB_SEARCH_MODEL}"
                    elif is_messages:
                        # 대체 대상 이름일 때만 게이트웨이 목록을 본다(키별 캐시) — 새 모델이 오르면 따라간다
                        listed = _GATEWAY_MODELS.get(bearer_token(self.headers)) if needs_model_list(model_name) else None
                        if normalize_claude_model_id(payload_obj, parsed.path, listed):
                            restored = payload_obj.get("model")
                            if is_model_substitution(model_name, restored):
                                # 응답의 200 은 바뀐 모델의 것이다 — 표기만 고친 것(4-7 → 4.7)과 갈라 따로 센다
                                _count_model_substitution()
                                self._model_substituted = f"{model_name} -> {restored}"
                                log(f"{parsed.path} Claude model SUBSTITUTED (gateway has no {model_name}): "
                                    f"{model_name} -> {restored} "
                                    f"by={resolve_claude_model(model_name, listed)[1]}")
                            else:
                                log(f"{parsed.path} Claude model restored: {model_name} -> {restored}")
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
                        ceiling = cap_claude_output(payload_obj, unstream=payload_obj.get("stream") is not True,
                                                    body_bytes=len(body))
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
                    grok_dropped = normalize_grok_params(payload_obj, parsed.path)
                    if grok_dropped:
                        changed = True
                        _count_grok_dropped(len(grok_dropped))
                        log(f"{parsed.path} model={payload_obj.get('model')} grok_dropped={','.join(grok_dropped)}")
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
        codex_fill = bool(web_search) and web_search.get("response") == "codex"
        if web_search and not codex_fill:
            headers = web_search_headers(headers)
        if gemini_chat_model:
            upstream_path = f"{GEMINI_PREFIX}/models/{quote(gemini_chat_model, safe='')}:generateContent"
        elif codex_fill:
            upstream_path = parsed.path.rstrip("/")[:-len("/alpha/search")] + "/responses"
            query = ""
        elif web_search:
            upstream_path = normalize_gemini_model_path(
                f"{GEMINI_PREFIX}/models/{quote(WEB_SEARCH_MODEL, safe='')}:generateContent")
            # ⚠ Claude Code 의 `?beta=true` 를 제미나이 경로에 실으면 400(`Unknown name "beta"`)이다 — `?key=` 만 남긴다.
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
        provider = ("openai" if codex_fill else "gemini" if web_search
                    else request_provider(parsed.path, model_name))
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
                    self.command, upstream_path, body, headers,
                    timeout=WEB_SEARCH_TIMEOUT if web_search else None,
                )
            except _ClientDisconnected:
                raise
            except Exception as error:
                outcome = "upstream_error"
                log(f"{self.command} {parsed.path} -> upstream unreachable: {error} {self._request_context}")
                if web_search:
                    # 웹서치는 502 대신 검색 오류 칸으로 답한다 — 502 면 CLI 가 다시 보내며 시한만큼 또 묶인다
                    outcome = "web_search_failed"
                    client_status = 200
                    _count_web_search(False)
                    self._send_web_search(web_search, codex_web_search_error() if codex_fill else
                                          web_search_error_message(str(web_search["query"]),
                                                                   str(web_search["model"])))
                    return
                client_status = 502
                # 이 요청 뒤에 연결을 닫으므로(close_connection) keep-alive 를 약속하지 않는다
                self._send_json(
                    502, {"type": "error", "error": {"message": str(error)}}, keep_alive=False
                )
                return

            headers_sec = time.monotonic() - self._upstream_started
            self._gw_request_id = response.getheader(GATEWAY_REQUEST_ID_HEADER) or ""
            # 시한 판정은 경과를 아는 finally 에서 한다 — 여기서는 상태만 넘겨 둔다
            upstream_status = response.status
            client_status = upstream_status
            if response.status >= 400:
                log(f"{self.command} {parsed.path} -> HTTP {response.status} {self._request_context}{self._gw()}")

            if web_search:
                # 상류가 지거나 꼴이 어긋나도 4xx · 5xx 로 넘기지 않고 검색 오류 칸으로 답한다 — 그래야 대화가 안 깨진다.
                message: dict | None = None
                error_code = "unavailable"
                try:
                    raw = response.read()
                    # 시한을 줄인 연결은 풀에 돌려보내지 않는다 — 다음 긴 Claude 요청이 그 시한으로 끊긴다
                    reuse = False
                    if response.status < 400 and codex_fill:
                        message = responses_web_search_to_codex(raw)
                    elif response.status < 400:
                        message = gemini_grounding_to_anthropic(
                            raw, str(web_search["query"]), str(web_search["model"]), dict(web_search["tool"]))
                    else:
                        error_code = web_search_error_code(response.status)
                        log(f"web search fill: upstream HTTP {response.status} "
                            f"body={raw[:400]!r} {self._request_context}{self._gw()}")
                except (OSError, http.client.HTTPException, ValueError, TypeError, AttributeError,
                        KeyError, IndexError) as error:
                    log(f"web search fill: Gemini answer unreadable: {error!r} {self._request_context}{self._gw()}")
                if message is None:
                    _count_web_search(False)
                    outcome = "web_search_failed"
                    message = (codex_web_search_error(error_code) if codex_fill else
                               web_search_error_message(str(web_search["query"]), str(web_search["model"]), error_code))
                else:
                    sources = (len(message.get("results") or []) if codex_fill
                               else len(message["content"][1]["content"]))
                    _count_web_search(True, empty=sources == 0)
                    self._request_context += f" sources={sources}"
                client_status = 200
                self._send_web_search(web_search, message)
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

            # ⚠ 3xx 는 따라가지 않고 그대로 중계한다 — 따라가면 Authorization 을 Location 의 호스트로 다시 보낸다.
            is_gemini_stream = (
                upstream_path.startswith(f"{GEMINI_PREFIX}/models/")
                and ":streamGenerateContent" in upstream_path
                and response.status < 400
            )

            content_type = (response.getheader("Content-Type") or "").lower()
            if claude_unstream and 200 <= response.status < 300 and not content_type.startswith("text/event-stream"):
                # 머리가 오기 전에는 SSE 200 을 미리 안 보낸다 — 진짜 HTTP 오류를 지키려고. 그동안은 설치기가 심는 클라이언트
                # 유휴 시한(10분)이 든다. 실패는 SSE 오류로 내고, 성공한 도구 호출이나 message_stop 을 지어내지 않는다.
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
                # Anthropic · OpenAI 스트림에만 주석을 흘린다. Gemini 는 재조립기가 조각을 쥐고 있어 뺀다.
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
            # 로컬 대기는 빼고, 시한을 넘긴 5xx 만 게이트웨이 시간 초과 후보로 센다.
            # SSE error 프레임 판은 _relay_stream 이 이미 stream_errors 로 세므로 여기서 겹치지 않는다.
            if (upstream_status >= 500 or outcome in ("stream_error", "stream_incomplete")) and at_execution_limit(upstream_sec):
                cut_300 = upstream_sec >= NONSTREAM_LIMIT_SEC - EXECUTION_LIMIT_MARGIN_SEC
                _count_execution_cut(nonstream=cut_300)
                log(
                    f"execution cut {self.command} {parsed.path} upstream={upstream_sec:.1f}s "
                    f"HTTP {upstream_status} (possible gateway timeout; limit "
                    f"~{NONSTREAM_LIMIT_SEC if cut_300 else EXECUTION_LIMIT_SEC:g}s) {self._request_context}{self._gw()}"
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
    # ⚠ Windows 의 SO_REUSEADDR 은 남이 우리 포트 위에 바인드하게 둔다 — 우리 쪽에서 끄는 것만으로는 못 막아
    #   SO_EXCLUSIVEADDRUSE 로 배타 점유한다.
    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1
            )
        super().server_bind()

    def handle_error(self, request, client_address) -> None:  # noqa: D102
        # pythonw 에는 stderr 가 없다 — 기본 구현대로 두면 처리 안 된 예외가 어디에도 안 남는다
        error = sys.exc_info()[1]
        if isinstance(error, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            # 클라이언트가 요청을 끊은 것 — 흔하고 정상이다. 긴 traceback 으로 로그를 채워 절단 증거를 밀어내지 않는다
            log(f"client disconnected from {client_address}: {type(error).__name__}")
            return
        log("unhandled error from " + str(client_address) + ": " + traceback.format_exc().strip().replace("\n", " | "))

    def get_request(self):  # noqa: D102
        sock, addr = super().get_request()
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        return sock, addr


def self_test() -> None:
    # sanitize: 파라미터 제거·병합·prefill 제거. 도구 description 은 건드리지 않는다.
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

    # 그림 끌어내기: 그림만 이름표와 함께 나가고 PDF 는 tool_result 안에 바이트 그대로 남는다(결정 0165)
    doc = {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "JVBERi0xLjQ="}}
    img = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo="}}
    doc_sent = json.dumps(doc)
    turn = [{"type": "tool_result", "tool_use_id": "toolu_h", "content": [doc, img]}]
    assert _hoist_tool_images(turn) == 1
    kept = turn[0]["content"]
    assert len(kept) == 2 and json.dumps(kept[0]) == doc_sent
    assert kept[1]["type"] == "text" and kept[1]["text"].startswith("[image ")
    assert not any("document" in str(item.get("text", "")) for item in kept)
    assert [b["type"] for b in turn] == ["tool_result", "text", "image"] and turn[2] == img
    assert "toolu_h" in turn[1]["text"]

    # patch: 최상위 tools 보정 (sanitize 이후 단일 소유자)
    assert patch_tool_descriptions(result) == 1
    assert result["tools"][0]["description"] == "Read tool"

    # Codex Responses: input[*].tools 의 중첩 namespace 까지
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

    # 대화 데이터는 절대 변조하지 않는다 — tool_use input 안의 "tools" 리스트
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

    # Gemini tools 는 절대 보정하지 않는다 — description 필드가 없는 스키마라
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

    # GPT-5/o 계열 chat 경로는 max_tokens 를 max_completion_tokens 로 바꾼다.
    token_payload = {"model": "gpt-5.6-sol", "max_tokens": 8}
    assert normalize_openai_token_limit(token_payload, "/gpgpta01-gpt/v1/chat/completions")
    assert "max_tokens" not in token_payload and token_payload["max_completion_tokens"] == 8
    old_payload = {"model": "gpt-4o", "max_tokens": 8}
    assert not normalize_openai_token_limit(old_payload, "/gpgpta01-gpt/v1/chat/completions")
    assert old_payload["max_tokens"] == 8
    # GPT-6(아스트라) 도 같은 보정을 받고, /v1/responses 는 max_output_tokens 로 간다.
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

    # chat/completions 꼴 도구는 function 안의 description 만 본다 — 바깥에 칸을 붙이지 않는다.
    chat_tools = {"tools": [{"type": "function", "function": {"name": "read_file", "description": "Read"}},
                            {"type": "function", "function": {"name": "ls", "description": ""}}]}
    assert patch_tool_descriptions(chat_tools, "/gpgpta01-gpt/v1/chat/completions") == 1
    assert [sorted(t) for t in chat_tools["tools"]] == [["function", "type"], ["function", "type"]]
    assert chat_tools["tools"][0]["function"]["description"] == "Read"
    assert chat_tools["tools"][1]["function"]["description"] == "ls tool"

    # Grok 4 추론 경로가 거부하는 필드를 뗀다. 옛 ID 는 reasoning_effort 까지.
    chat_path = "/gpgpta01-gpt/v1/chat/completions"
    grok_payload = {"model": "grok-4-1-fast-reasoning", "reasoning_effort": "high", "stop": ["x"],
                    "presence_penalty": 0.1, "temperature": 0.2}
    assert normalize_grok_params(grok_payload, chat_path) == [
        "presence_penalty", "stop", "reasoning_effort"]
    assert grok_payload == {"model": "grok-4-1-fast-reasoning", "temperature": 0.2}
    grok_plain = {"model": "grok-4-1-fast-non-reasoning", "stop": ["x"], "reasoning_effort": "low"}
    assert normalize_grok_params(grok_plain, chat_path) == ["reasoning_effort"]
    assert grok_plain["stop"] == ["x"]
    grok_new = {"model": "grok-4.3", "reasoning_effort": "low", "frequency_penalty": 0.5}
    assert normalize_grok_params(grok_new, chat_path) == ["frequency_penalty"]
    assert grok_new["reasoning_effort"] == "low"
    assert normalize_grok_params({"model": "gpt-5.6-sol", "stop": ["x"]}, chat_path) == []
    assert normalize_grok_params({"model": "grok-4-1-fast-reasoning", "stop": ["x"]},
                                 "/gpgpta01-gpt/v1/messages") == []

    # Hermes가 점을 대시로 바꾼 Claude 소수 버전 ID를 복원한다.
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

    # Hermes/OpenAI 호환 Gemini 호출은 Gemini native 응답을 chat completion 으로 되돌린다.
    converted = gemini_response_to_openai_chat(
        _json_bytes({"candidates": [{"content": {"parts": [{"text": "OK"}]}, "finishReason": "STOP"}]}),
        "gemini-3.6-flash",
    )
    converted_obj = json.loads(converted.decode("utf-8"))
    assert converted_obj["choices"][0]["message"]["content"] == "OK"

    # Gemini: 원래 헤더·쿼리는 그대로 두고 Bearer 만 덧붙인다
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

    # Hermes anthropic_messages: x-api-key → Bearer 보강 (원래 헤더 유지)
    headers = normalize_anthropic_auth({"x-api-key": "pgpt-tok", "Content-Type": "application/json"})
    assert headers["Authorization"] == "Bearer pgpt-tok"
    assert headers["x-api-key"] == "pgpt-tok"
    headers = normalize_anthropic_auth({"Authorization": "Bearer REAL", "x-api-key": "sk-ant-personal"})
    assert headers["Authorization"] == "Bearer REAL"
    assert "x-api-key" not in headers  # 개인 키가 게이트웨이로 새지 않는다
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
    # 안티그래비티의 제목 모델 이름은 게이트웨이 등록 이름으로, 실제로 있는 -preview 판은 그대로 둔다.
    assert normalize_gemini_model_path(
        "/gpgpta01-gpt/v1beta/models/gemini-3.1-flash-lite-preview:streamGenerateContent"
    ) == "/gpgpta01-gpt/v1beta/models/gemini-3.1-flash-lite:streamGenerateContent"
    assert normalize_gemini_model_path(
        "/gpgpta01-gpt/v1beta/models/gemini-3.1-flash-lite-preview-customtools:generateContent"
    ) == "/gpgpta01-gpt/v1beta/models/gemini-3.1-flash-lite:generateContent"
    assert normalize_gemini_model_path(
        "/gpgpta01-gpt/v1beta/models/gemini-3.1-pro-preview:generateContent"
    ) == "/gpgpta01-gpt/v1beta/models/gemini-3.1-pro-preview:generateContent"

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

    # 하이쿠 대체 — 게이트웨이에 없는 이름은 규칙으로 잡고, 나머지 대시→점 변환은 그대로다
    for haiku in ("claude-haiku-4-5", "claude-haiku-4-5-20251001", "claude-3-5-haiku-latest", "Claude-Haiku-4.5"):
        assert normalize_pgpt_claude_model(haiku) == CLAUDE_HAIKU_SUBSTITUTE, haiku
    assert normalize_pgpt_claude_model("claude-opus-4-7") == "claude-opus-4.7"
    assert normalize_pgpt_claude_model("claude-sonnet-4.6") == "claude-sonnet-4.6"
    haiku_payload = {"model": "claude-haiku-4-5-20251001", "messages": []}
    assert normalize_claude_model_id(haiku_payload, "/gpgpta01-gpt/v1/messages") is True
    assert haiku_payload["model"] == CLAUDE_HAIKU_SUBSTITUTE

    # SSE 오류 프레임 — 게이트웨이가 180초 시한에 끊을 때 남기는 마지막 조각을 읽는다
    frame = (b'event: error\r\ndata: {"type":"error","error":{"type":"api_error","message":'
             b'"HTTP request execution did not complete before the specified timeout configuration: 180000 millis"}}\r\n\r\n')
    assert (sse_error_message(frame) or "").endswith("180000 millis")
    assert sse_error_message(b'data: {"type":"content_block_delta","delta":{"text":"error"}}\n\n') is None

    # 표기 고침과 다른 모델로 바꾼 것을 가른다
    assert is_model_substitution("claude-opus-4-7", "claude-opus-4.7") is False
    assert is_model_substitution("claude-sonnet-4-6-20250929", "claude-sonnet-4.6") is False
    assert is_model_substitution("claude-sonnet-5.5", "claude-sonnet-4.6") is True
    assert is_model_substitution("claude-haiku-4-5-20251001", "claude-sonnet-4.6") is True
    # 입력 크기에 따른 상한은 기본 꺼짐 — 큰 본문에도 상한이 그대로다
    assert output_cap(unstream=False, body_bytes=4_000_000) == output_cap(unstream=False)
    # 실행 절단 판정 — 시한 근방(180초 · 300초)만 든다
    assert at_execution_limit(180.0) is True
    assert at_execution_limit(179.0) is True   # 측정 오차·앞단 지연을 담는 폭 안
    assert at_execution_limit(300.0) is True   # 넘겨 도착한 판도 든다
    assert at_execution_limit(170.0) is False  # 폭 밖의 느린 오류는 절단이 아니다
    assert at_execution_limit(12.5) is False
    assert "execution_cuts" in stats()

    # keepalive — 상류가 interval 보다 오래 침묵하면 주석이 나가고, 조각은 순서대로 그대로 온다
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

    # 웹서치 메움 — 알아보기 · 바꾸기 · 짓기. HTTP 갈래는 Test-ProxyWebSearch.py 가 잰다.
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
    # 질의는 마지막 user 메시지의 CLI 머리 조각만 — 여러 턴 대화 · 머리 없는 요청은 안 메운다
    assert web_search_query({"messages": [{"role": "user", "content": [
        {"type": "text", "text": "<system-reminder>x</system-reminder>"},
        {"type": "text", "text": _WEB_SEARCH_PROMPT_HEAD + "foo"}]}]}) == "foo"
    assert web_search_query({"messages": [{"role": "user", "content": "Hello, what is new in python?"},
                                          {"role": "assistant", "content": "..."},
                                          {"role": "user", "content": "thanks, also search rust"}]}) is None
    # 도메인 견주기는 scheme · 경로 · www 를 떼고, 푼 주소면 그 호스트로
    norm_tool = {"allowed_domains": ["https://www.python.org/blog"], "blocked_domains": ["Bad.example"]}
    assert _domain_list(norm_tool, "allowed_domains") == ["python.org"]
    redirected = json.dumps({"candidates": [{"content": {"parts": [{"text": "t"}]}, "groundingMetadata": {"groundingChunks": [
        {"web": {"uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/A", "title": "python.org"}},
        {"web": {"uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/B", "title": "python.org"}},
        {"web": {"uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/C"}}]}}]}).encode()
    fake_resolve = {"https://vertexaisearch.cloud.google.com/grounding-api-redirect/A": "https://docs.python.org/3/whatsnew/",
                    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/B": "https://sub.bad.example/x"}
    msg = gemini_grounding_to_anthropic(redirected, "q", "m", {"allowed_domains": ["www.python.org"]},
                                        resolve=lambda urls: fake_resolve)
    assert [r["url"] for r in msg["content"][1]["content"]] == ["https://docs.python.org/3/whatsnew/"]  # 원래 주소 · 남은 걷음
    msg = gemini_grounding_to_anthropic(redirected, "q", "m", {"blocked_domains": ["bad.example"]},
                                        resolve=lambda urls: fake_resolve)
    assert [r["url"] for r in msg["content"][1]["content"]] == [
        "https://docs.python.org/3/whatsnew/", "https://vertexaisearch.cloud.google.com/grounding-api-redirect/C"]
    assert web_search_error_code(429) == "too_many_requests" and web_search_error_code(400) == "invalid_input"
    assert web_search_error_code(503) == "unavailable"
    assert resolve_grounding_urls(["https://r/1"]) == {}  # 경유 주소가 아니면 밖으로 안 나간다
    ws_err = web_search_error_message("q", "claude-opus-5")
    assert ws_err["content"][1]["content"] == {"type": "web_search_tool_result_error", "error_code": "unavailable"}
    assert anthropic_message_events(ws_err)
    assert "web_search_filled" in stats()

    # 대체는 게이트웨이 목록을 따른다 — 목록이 없으면 고정 규칙 그대로
    today = frozenset({"claude-opus-5", "claude-opus-4.7", "claude-sonnet-4.6", "gpt-5.5"})
    assert normalize_pgpt_claude_model("claude-haiku-4-5-20251001", today) == "claude-sonnet-4.6"
    assert normalize_pgpt_claude_model("claude-sonnet-5", today) == "claude-sonnet-4.6"
    assert normalize_pgpt_claude_model("claude-fable-5-1", today) == "claude-fable-5.1"  # 사람이 고르는 이름은 구하지 않는다(0164)
    assert not needs_model_list("claude-fable-5.1") and needs_model_list("claude-haiku-4-5")
    assert normalize_pgpt_claude_model("claude-fable-5-1") == "claude-fable-5.1"
    assert normalize_pgpt_claude_model("claude-opus-latest", today) == "claude-opus-5"
    assert normalize_pgpt_claude_model("claude-opus-6", today) == "claude-opus-6"  # 대상 아닌 이름은 그대로
    later = today | {"claude-sonnet-5", "claude-sonnet-5.5", "claude-haiku-4.5", "claude-fable-5.1"}
    assert normalize_pgpt_claude_model("claude-sonnet-5", later) == "claude-sonnet-5"
    assert normalize_pgpt_claude_model("claude-sonnet-5-5", later) == "claude-sonnet-5.5"
    assert normalize_pgpt_claude_model("claude-sonnet-5-7", later) == "claude-sonnet-5.5"
    assert normalize_pgpt_claude_model("claude-haiku-4-5-20251001", later) == "claude-haiku-4.5"
    assert normalize_pgpt_claude_model("claude-haiku-5", later) == "claude-haiku-4.5"
    assert normalize_pgpt_claude_model("claude-fable-5-1", later) == "claude-fable-5.1"
    assert normalize_pgpt_claude_model("claude-sonnet-latest", later) == "claude-sonnet-5.5"
    assert claude_family_version("claude-3-5-sonnet-latest") == ("sonnet", (3, 5))
    assert parse_model_map(" claude-haiku*=claude-opus-5 ; bad ;x=") == [("claude-haiku*", "claude-opus-5")]
    assert bearer_token({"Authorization": "Bearer k1", "x-api-key": "k2"}) == "k1"
    assert bearer_token({"x-api-key": "k2"}) == "k2" and bearer_token({}) is None
    assert GatewayModelList(UPSTREAM, ttl=0, retry=1, timeout=1).get("k") is None  # 끄면 묻지 않는다
    assert "model_list_fetches" in stats()

    # 압축 간결 지시는 기본으로 꺼져 있다(결정 0082) — 압축은 알아보되 본문은 안 고친다.
    assert COMPACT_CONCISE is False or os.environ.get("PGPT_PROXY_COMPACT_CONCISE")
    assert stats()["compact_concise"] is COMPACT_CONCISE
    # 출처 풀기도 기본으로 꺼져 있다(결정 0165) — 회사 웹필터가 구글을 막아 풀 수 있는 주소가 없다.
    assert WEB_SEARCH_RESOLVE is False or os.environ.get("PGPT_PROXY_WEB_SEARCH_RESOLVE")
    assert stats()["web_search_resolve"] is WEB_SEARCH_RESOLVE

    print("Self-test: OK")


def main() -> None:
    # 재설치 · 키 교체 직후에는 옛 프록시의 연결이 닫히는 중이라 bind 가 잠깐 진다 — 바로 죽으면 다음 로그인까지
    # 프록시가 없으니 15초 동안 다시 시도한다.
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
            raise SystemExit(2) from error

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
