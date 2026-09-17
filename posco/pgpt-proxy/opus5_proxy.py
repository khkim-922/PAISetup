"""Local compatibility proxy for the POSCO P-GPT gateway.

Serves both routes from one process:

* Claude Code   -> http://127.0.0.1:18901/gpgpta01-gpt        (no /v1)
* Codex CLI     -> http://127.0.0.1:18901/gpgpta01-gpt/v1     (with /v1)

Payload fixes, all required by the gateway:

* ``/v1/messages`` — drop a trailing assistant prefill so the conversation
  ends with a user message (the Opus 5 Bedrock route rejects prefill), and
  strip parameters that route refuses (temperature/top_p, system role).
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
  ``x-api-key`` is left in place.
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

Everything else is relayed untouched, streaming included. Upstream 3xx
responses are relayed as-is, never followed (following would re-send the
Authorization header to whatever host Location names).
"""

from __future__ import annotations

import http.client
import io
import json
import os
import queue
import re
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote_plus, urlsplit

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 18901
# 운영 게이트웨이. 개발 게이트웨이(taigpt)나 시험용 스텁으로 바꿀 때만
# PGPT_PROXY_UPSTREAM 을 쓴다. 프로토콜은 http — https 는 연결되지 않는다.
UPSTREAM = os.environ.get("PGPT_PROXY_UPSTREAM", "http://aigpt.posco.net").rstrip("/")
ALLOWED_PREFIX = "/gpgpta01-gpt/"
# 상류 v15 + 우리 덩어리 둘(keepalive `_relay_sse_keepalive` · unstream `_unstream_messages`). 설치기가 도는
# 판과 이 값을 견주어 낮으면 갈아 끼우므로 상류보다 늘 위에 둔다 — 상류가 17 을 내면 우리는 18 이다.
# README 「상류 판」.
VERSION = 17
# SSE keepalive — 상류가 이만큼 침묵하면 클라이언트 쪽에 SSE 주석 한 줄을 흘린다. 0 이면 끈다.
# 게이트웨이는 모델이 생각하는 동안 바이트를 안 흘리고, Claude Code 의 바이트 유휴 워치독은 그 침묵에
# 스트림을 끊는다(회사 실측 2026-09-14 · 자동 압축이 가장 잘 걸림). 주석 줄(`:`)은 SSE 규격상 버려지므로
# 내용은 안 바뀌고 바이트만 흐른다. 이기는 것은 클라이언트 워치독뿐이다 — 게이트웨이 쪽이 제 침묵에
# 끊으면 여기서는 못 막는다.
KEEPALIVE_SEC = float(os.environ.get("PGPT_PROXY_KEEPALIVE_SEC", "15"))
_KEEPALIVE_LINE = b": keepalive\n\n"
# unstream — 클라이언트의 `"stream": true` 를 상류엔 `"stream": false` 로 보내고, 답이 오면 SSE 로 지어 낸다.
# 게이트웨이는 /v1/messages 스트림을 요청 시작 약 180초에 신호 없이 닫지만(claude-config #46) 비스트리밍
# 경로에는 그 상한이 없다(회사 PC 실측 2026-09-16 — 119초에 200 · 300.04초에 앞단 HAProxy 의 504).
# ⚠ **기본이 끔이다 — 켜면 큰 도구 인자가 빈다**(회사 PC 실측 2026-09-17). 켠 판에서 `Edit` 호출이
#   `input={}` 로 오고(출력 78/64000 토큰이라 한도와 무관 · `stop_reason` 은 정상 `tool_use`) 같은 판의
#   작은 `Bash` 호출은 멀쩡하다. 끄면 같은 편집이 통한다(재현 3회). 우리 짓는 코드는 무죄다 —
#   6,642자 도구 입력이 SSE 왕복해 글자 대 글자로 살아남는다. 까닭은 게이트웨이 안이라 밖에서 못 본다.
#   **그래서 도구를 쓰는 클라이언트(Claude Code)에는 켜지 않는다.** 도구를 안 쓰는 쪽(아뜰리에)은
#   `PGPT_PROXY_UNSTREAM=1` 로 켜서 180초 벽을 비껴갈 수 있다 — 결정 0051.
UNSTREAM = os.environ.get("PGPT_PROXY_UNSTREAM", "0").strip().lower() not in {"0", "false", "off", "no"}
PID_PATH = Path(__file__).with_name("opus5_proxy.pid")
LOG_PATH = Path(__file__).with_name("proxy.log")
LOG_MAX_BYTES = 1_000_000
MAX_CHUNK_SIZE = 0x7FFFFFFF
UPSTREAM_POOL_SIZE = 8
UPSTREAM_TIMEOUT = 600
UPSTREAM_IDLE_TTL = 30.0
SLOW_REQUEST_SEC = 5.0
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

    def acquire(self) -> http.client.HTTPConnection:
        with self._lock:
            while self._idle:
                conn, released_at = self._idle.pop()
                if conn.sock is not None and time.monotonic() - released_at < UPSTREAM_IDLE_TTL:
                    self._reused += 1
                    return conn
                self._expired += 1
                try:
                    conn.close()
                except OSError:
                    pass
        return self._open()

    def release(self, conn: http.client.HTTPConnection | None, *, reuse: bool) -> None:
        if conn is None:
            return
        if not reuse:
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
_UNSTREAMED_TOTAL = 0


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


def _count_unstreamed() -> None:
    global _UNSTREAMED_TOTAL
    with _STATS_LOCK:
        _UNSTREAMED_TOTAL += 1


def stats() -> dict[str, int]:
    with _STATS_LOCK:
        base = {
            "patched_tools": _PATCHED_TOTAL,
            "trimmed_prefills": _TRIMMED_PREFILLS,
            "slow_requests": _SLOW_TOTAL,
            "keepalives": _KEEPALIVE_TOTAL,
            "unstreamed": _UNSTREAMED_TOTAL,
        }
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


def _json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


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
_CLAUDE_DASH_VERSION = re.compile(
    r"^(claude-(?:opus|sonnet|haiku)-\d+)-(\d+)(.*)$",
    re.IGNORECASE,
)

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
    alias = _CLAUDE_MODEL_ALIASES.get(name.lower())
    if alias:
        return alias
    # dated Anthropic ids: claude-sonnet-5-20260219
    lower = name.lower()
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
    ``Authorization`` 만 덧붙인다. 이미 Authorization 이 있으면 그대로 둔다.
    """
    if any(name.lower() == "authorization" for name in headers):
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
    suffix = "-customtools"
    if not model.endswith(suffix):
        return path
    base_model = model[: -len(suffix)]
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


# ── (우리 것 · 결정 0051) 비스트리밍 답 하나를 클라이언트가 기대하는 SSE 로 짓는 자들 ──────────────
# 잃는 것은 첫 글자가 늦는 것뿐이다 — 이 게이트웨이는 어느 길로도 생각 조각을 안 흘린다(#46 물음 ②).


def _sse_event(name: str, data: dict[str, object]) -> bytes:
    return b"event: " + name.encode("ascii") + b"\ndata: " + _json_bytes(data) + b"\n\n"


def _content_block_events(index: int, block: dict[str, object]) -> list[bytes]:
    """Expand one finished content block into start / delta(s) / stop events."""
    kind = block.get("type")
    deltas: list[dict[str, object]] = []
    if kind == "text":
        start: dict[str, object] = {"type": "text", "text": ""}
        deltas.append({"type": "text_delta", "text": str(block.get("text") or "")})
    elif kind == "tool_use":
        # Claude Code 는 도구 호출을 input_json_delta 로만 읽는다. 답에는 이미 완성된 input 이
        # 들어 있으므로 조각내지 않고 JSON 문자열 하나로 통째 싣는다.
        tool_input = block.get("input")
        start = {
            "type": "tool_use",
            "id": block.get("id"),
            "name": block.get("name"),
            "input": {},
        }
        deltas.append({
            "type": "input_json_delta",
            "partial_json": _json_bytes(tool_input if isinstance(tool_input, dict) else {}).decode("utf-8"),
        })
    elif kind == "thinking":
        start = {"type": "thinking", "thinking": "", "signature": ""}
        deltas.append({"type": "thinking_delta", "thinking": str(block.get("thinking") or "")})
        signature = block.get("signature")
        if isinstance(signature, str) and signature:
            deltas.append({"type": "signature_delta", "signature": signature})
    else:
        # redacted_thinking 처럼 델타가 없는 블록은 시작 이벤트에 통째로 싣는다 (본가와 같은 꼴).
        start = block
    events = [_sse_event(
        "content_block_start",
        {"type": "content_block_start", "index": index, "content_block": start},
    )]
    events.extend(
        _sse_event("content_block_delta", {"type": "content_block_delta", "index": index, "delta": delta})
        for delta in deltas
    )
    events.append(_sse_event("content_block_stop", {"type": "content_block_stop", "index": index}))
    return events


def synthesize_anthropic_sse(message: dict[str, object]) -> bytes:
    """Build the SSE stream a ``stream: true`` client expects from a finished message."""
    raw_usage = message.get("usage")
    usage = raw_usage if isinstance(raw_usage, dict) else {}
    start_message = {
        key: value
        for key, value in message.items()
        if key not in {"content", "usage", "stop_reason", "stop_sequence"}
    }
    start_message["content"] = []
    start_message["stop_reason"] = None
    start_message["stop_sequence"] = None
    # 문맥 계산과 화면이 그대로이려면 input_tokens·cache_* 가 여기 실려야 한다. 낸 토큰은 아직 0 이고
    # 최종 수는 message_delta 가 든다 (본가도 시작 이벤트의 output_tokens 는 아직 안 센 값이다).
    start_message["usage"] = {key: value for key, value in usage.items() if key != "output_tokens"}
    start_message["usage"]["output_tokens"] = 0

    events = [_sse_event("message_start", {"type": "message_start", "message": start_message})]
    content = message.get("content")
    blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content
    index = 0
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, dict):
                continue
            events.extend(_content_block_events(index, block))
            index += 1
    events.append(_sse_event("message_delta", {
        "type": "message_delta",
        "delta": {
            "stop_reason": message.get("stop_reason"),
            "stop_sequence": message.get("stop_sequence"),
        },
        "usage": {"output_tokens": usage.get("output_tokens", 0)},
    }))
    events.append(_sse_event("message_stop", {"type": "message_stop"}))
    return b"".join(events)


def anthropic_sse_error(status: int, raw: bytes) -> bytes:
    """Carry an upstream failure as an SSE ``error`` event.

    Once a keepalive comment has gone out the status line is already spent, so the
    only way left to tell the client is an event.
    """
    try:
        parsed = json.loads(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, ValueError):
        parsed = None
    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
        error: dict[str, object] = parsed["error"]
    else:
        # 앞단 HAProxy 의 504 는 JSON 이 아니라 HTML 이다(#46 실측) — 상태와 첫 줄만 담는다.
        text = raw.decode("utf-8", "replace")
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        message = f"upstream HTTP {status}"
        if first_line:
            message = f"{message}: {first_line[:200]}"
        error = {"type": "api_error", "message": message}
    return _sse_event("error", {"type": "error", "error": error})


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        data = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self.wfile.write(data)
        self.close_connection = False

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

        last_error: Exception | None = None
        for attempt in range(2):
            conn = _UPSTREAM_POOL.acquire()
            try:
                conn.request(method, path, body=body, headers=upstream_headers)
                return conn.getresponse(), conn
            except (http.client.HTTPException, OSError, TimeoutError) as error:
                last_error = error
                _UPSTREAM_POOL.release(conn, reuse=False)
                if attempt == 0:
                    log(f"{method} {path} upstream retry after {error!r}")
                    continue
                raise
        assert last_error is not None
        raise last_error

    def _relay_sse_keepalive(self, response: object, interval: float) -> bool:
        """Copy an SSE body, writing an SSE comment whenever upstream is silent.

        Upstream is read on a helper thread so the HTTP parser never sees a
        socket timeout; the writer waits on the queue with a timeout and fills
        the gap with a comment line. Returns True if fully consumed.
        """
        chunks: queue.Queue = queue.Queue()

        def reader() -> None:
            try:
                while True:
                    chunk = response.read1(65536)  # type: ignore[attr-defined]
                    if not chunk:
                        break
                    chunks.put(chunk)
                chunks.put(None)
            except BaseException as error:  # noqa: BLE001 — 사유째 넘긴다
                chunks.put(error)

        threading.Thread(target=reader, daemon=True).start()
        sent = 0
        try:
            while True:
                try:
                    item = chunks.get(timeout=interval)
                except queue.Empty:
                    self.wfile.write(_KEEPALIVE_LINE)
                    self.wfile.flush()
                    sent += 1
                    _count_keepalive()
                    continue
                if item is None:
                    break
                if isinstance(item, BaseException):
                    log(f"upstream read aborted: {item!r}")
                    return False
                self.wfile.write(item)
                self.wfile.flush()
            if sent:
                log(f"keepalive x{sent} (upstream silent > {interval:g}s)")
            return True
        except (BrokenPipeError, ConnectionResetError):
            return False

    def _relay_stream(
        self,
        response: http.client.HTTPResponse,
        *,
        gemini_sse: bool,
        keepalive: bool = False,
        interval: float | None = None,
    ) -> bool:
        """Copy upstream body to the client. Returns True if fully consumed."""
        if keepalive and not gemini_sse:
            return self._relay_sse_keepalive(response, interval or KEEPALIVE_SEC)
        if gemini_sse:
            joiner = GeminiSseJoiner()
            try:
                while True:
                    try:
                        chunk = response.read1(65536)
                    except OSError as error:
                        log(f"upstream read aborted: {error!r}")
                        return False
                    if not chunk:
                        break
                    for event in joiner.feed(chunk):
                        self.wfile.write(event)
                        self.wfile.flush()
                for event in joiner.finish():
                    self.wfile.write(event)
                    self.wfile.flush()
                if joiner.joined_fragments:
                    log(f"Gemini SSE fragments joined={joiner.joined_fragments}")
                return True
            except (BrokenPipeError, ConnectionResetError):
                return False

        try:
            while True:
                try:
                    chunk = response.read1(65536)
                except OSError as error:
                    log(f"upstream read aborted: {error!r}")
                    return False
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError):
            return False

    def _write_client(self, data: bytes) -> bool:
        """(우리 것 · 0051) 클라이언트 쪽 쓰기. 끊겨 있으면 False."""
        try:
            self.wfile.write(data)
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError):
            return False

    def _begin_synthesized_sse(self) -> None:
        """(우리 것 · 0051) 200 SSE 로 못박는다 — 이 뒤로는 상태를 못 바꾼다."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

    def _unstream_messages(
        self,
        method: str,
        upstream_path: str,
        body: bytes | None,
        headers: dict[str, str],
    ) -> tuple[http.client.HTTPConnection | None, bool]:
        """(우리 것 · 결정 0051) 스트림 요청 하나를 비스트리밍 상류 호출 하나로 답한다.

        상류 호출은 블로킹이라 헬퍼 스레드가 받고 이쪽이 기다리며 주석을 흘린다 —
        ``_relay_sse_keepalive``(0044)와 같은 짜임이다. 돌려주는 것은 풀에 되돌릴 연결과
        그것을 재사용해도 되는가.
        """
        interval = KEEPALIVE_SEC if KEEPALIVE_SEC > 0 else None
        answers: queue.Queue = queue.Queue()
        held: dict[str, http.client.HTTPConnection] = {}

        def caller() -> None:
            try:
                response, conn = self._write_upstream(method, upstream_path, body, headers)
                held["conn"] = conn
                answers.put((response, response.read()))
            except BaseException as error:  # noqa: BLE001 — 사유째 넘긴다
                answers.put(error)

        threading.Thread(target=caller, daemon=True).start()
        comments = 0
        opened = False
        aborted = False
        while True:
            try:
                item = answers.get(timeout=interval)
                break
            except queue.Empty:
                if aborted:
                    continue
                if not opened:
                    self._begin_synthesized_sse()
                    opened = True
                if not self._write_client(_KEEPALIVE_LINE):
                    # 클라이언트가 갔다. 그래도 상류 답은 끝까지 기다린다 — 안 그러면 풀 연결이 샌다.
                    aborted = True
                    continue
                comments += 1
                _count_keepalive()

        conn = held.get("conn")
        if isinstance(item, BaseException):
            log(f"{method} {upstream_path} -> unstream upstream failed: {item!r}")
            if aborted:
                return conn, False
            if opened:
                self._write_client(_sse_event(
                    "error",
                    {"type": "error", "error": {"type": "api_error", "message": str(item)}},
                ))
            else:
                self._send_json(502, {"type": "error", "error": {"message": str(item)}})
            return conn, False

        response, raw = item
        conn_tokens = {
            part.strip()
            for part in (response.headers.get("Connection") or "").lower().split(",")
            if part.strip()
        }
        reuse = "close" not in conn_tokens
        if aborted:
            return conn, reuse

        message = None
        if 200 <= response.status < 300:
            try:
                message = json.loads(raw.decode("utf-8")) if raw else None
            except (UnicodeDecodeError, ValueError):
                message = None
        if not isinstance(message, dict) or not isinstance(message.get("content"), (list, str)):
            if response.status >= 400:
                log(f"{method} {upstream_path} -> HTTP {response.status} (unstream)")
            else:
                log(f"{method} {upstream_path} -> unstream: not an Anthropic message ({len(raw)}B)")
            if opened:
                self._write_client(anthropic_sse_error(response.status, raw))
                return conn, reuse
            # 주석을 아직 안 흘린 판이면 상태와 몸을 그대로 넘긴다 — 옛 길과 같게.
            self.send_response(response.status)
            for key, value in response.headers.items():
                if key.lower() in HOP_BY_HOP or key.lower() in {"content-length", "date", "server"}:
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.end_headers()
            self._write_client(raw)
            return conn, reuse

        if not opened:
            self._begin_synthesized_sse()
        self._write_client(synthesize_anthropic_sse(message))
        _count_unstreamed()
        content = message.get("content")
        # ⚠ **개수만 세면 「무엇이 빠졌나」가 안 보인다.** 도구 호출이 큰 판에서 클라이언트가
        #   인자를 못 받는 사고를 쫓는 중이라(2026-09-17), 종류와 tool_use 의 input 크기를 함께
        #   남긴다. **본문은 안 남긴다** — 이름과 숫자뿐이라 대화가 로그로 새지 않는다.
        shape = "?"
        if isinstance(content, list):
            parts = []
            for blk in content:
                if not isinstance(blk, dict):
                    parts.append("?")
                    continue
                kind = str(blk.get("type"))
                if kind == "tool_use":
                    size = len(_json_bytes(blk.get("input") if isinstance(blk.get("input"), dict) else {}))
                    parts.append(f"tool_use({blk.get('name')} input={size}B)")
                elif kind == "text":
                    parts.append(f"text({len(str(blk.get('text') or ''))}자)")
                else:
                    parts.append(kind)
            shape = " + ".join(parts) or "(빈 content)"
        # ⚠ **한도에 닿았나를 같이 찍는다.** 큰 도구 인자가 비는 사고의 원인 후보가
        #   「모델이 인자를 다 쓰기 전에 출력 한도에 걸려 JSON 이 미완성이 된 것」이다
        #   (직결 실측 2026-09-17: max_tokens 8k 에서 필드가 사라지고 32k 에서 온전했다).
        #   요청의 max_tokens 와 실제 output_tokens 가 나란히 있으면 그 자리에서 갈린다.
        want = "?"
        if body:
            try:
                want = str(json.loads(body).get("max_tokens"))
            except (ValueError, AttributeError):
                want = "?"
        usage = message.get("usage")
        got = usage.get("output_tokens") if isinstance(usage, dict) else "?"
        log(
            f"unstreamed model={message.get('model')} "
            f"blocks={len(content) if isinstance(content, list) else 1} "
            f"stop={message.get('stop_reason')} out={got}/{want} [{shape}] keepalive x{comments}"
        )
        return conn, reuse

    def _forward(self) -> None:
        started = time.monotonic()
        parsed = urlsplit(self.path)
        if parsed.path == "/health":
            payload: dict[str, object] = {
                "status": "ok",
                "service": "pgpt-proxy",
                "version": VERSION,
            }
            payload.update(stats())
            self._send_json(200, payload)
            return
        if not parsed.path.startswith(ALLOWED_PREFIX):
            self._send_json(
                403,
                {"type": "error", "error": {"message": "허용되지 않은 경로입니다."}},
            )
            return

        body = self._read_body()
        gemini_chat_model: str | None = None
        gemini_chat_stream = False
        unstream = False
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
                    if is_messages:
                        if normalize_claude_model_id(payload_obj, parsed.path):
                            log(f"{parsed.path} Claude model restored: {model_name} -> {payload_obj.get('model')}")
                        payload_obj = sanitize_payload(payload_obj)
                        changed = True
                        # (우리 것 · 결정 0051) 스트림 요청만 · 손잡이가 켜졌을 때만. 상류엔 stream:false 로
                        # 간다. 이 한 칸 말고는 몸을 안 건드린다 — 프롬프트 캐시는 본문 앞부분의 성질이라
                        # cache_control 도 키 차례도 그대로여야 캐시가 산다.
                        if UNSTREAM and self.command == "POST" and payload_obj.get("stream") is True:
                            payload_obj["stream"] = False
                            unstream = True
                    elif is_openai_generation and model_name.startswith("gemini-"):
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
        if gemini_chat_model:
            upstream_path = f"{GEMINI_PREFIX}/models/{quote(gemini_chat_model, safe='')}:generateContent"
        else:
            upstream_path = normalize_gemini_model_path(parsed.path)
        if query:
            upstream_path += f"?{query}"

        conn: http.client.HTTPConnection | None = None
        response: http.client.HTTPResponse | None = None
        reuse = False
        try:
            if unstream:
                # (우리 것 · 결정 0051) 여기부터는 상류가 비스트리밍이라 중계가 아니라 짓기다.
                conn, reuse = self._unstream_messages(
                    self.command, upstream_path, body, headers
                )
                return
            try:
                response, conn = self._write_upstream(
                    self.command, upstream_path, body, headers
                )
            except Exception as error:
                log(f"{self.command} {parsed.path} -> upstream unreachable: {error}")
                self._send_json(
                    502, {"type": "error", "error": {"message": str(error)}}
                )
                return

            if response.status >= 400:
                log(f"{self.command} {parsed.path} -> HTTP {response.status}")

            if gemini_chat_model and response.status < 400:
                raw = response.read()
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
                reuse = "close" not in (response.headers.get("Connection") or "").lower()
                return

            # 3xx: relay as-is, never follow (following would re-send Authorization).
            is_gemini_stream = (
                upstream_path.startswith(f"{GEMINI_PREFIX}/models/")
                and ":streamGenerateContent" in upstream_path
                and response.status < 400
            )

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
            # Streaming bodies have no Content-Length — close after the body.
            # Fixed-length replies could keep-alive, but BaseHTTPRequestHandler
            # still mixes poorly with upstream streaming; close is the safe default.
            self.send_header("Connection", "close")
            self.end_headers()

            # Anthropic SSE 만 keepalive 를 얹는다 — Gemini 는 재조립 갈래가 따로 있고, JSON 응답은 침묵이 곧 끝이다.
            keepalive_sse = (
                KEEPALIVE_SEC > 0
                and not is_gemini_stream
                and response.status < 400
                and (response.headers.get("Content-Type") or "").lower().startswith("text/event-stream")
            )
            fully_read = self._relay_stream(
                response, gemini_sse=is_gemini_stream, keepalive=keepalive_sse
            )
            if fully_read:
                conn_hdr = (response.headers.get("Connection") or "").lower()
                # HTTP/1.1 기본은 keep-alive. close 가 명시된 경우만 버린다.
                tokens = {part.strip() for part in conn_hdr.split(",") if part.strip()}
                reuse = "close" not in tokens
            else:
                reuse = False
        finally:
            _UPSTREAM_POOL.release(conn, reuse=reuse)
            self.close_connection = True
            elapsed = time.monotonic() - started
            if elapsed >= SLOW_REQUEST_SEC and parsed.path != "/health":
                _count_slow()
                log(f"slow {self.command} {parsed.path} {elapsed:.1f}s")

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
    headers = normalize_anthropic_auth({"Authorization": "Bearer REAL", "x-api-key": "pgpt-tok"})
    assert headers["Authorization"] == "Bearer REAL"
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

    # keepalive: 상류가 침묵하는 동안 SSE 주석이 흐르고, 본문은 글자 하나 안 바뀌고 지나간다.
    class _SlowResponse:
        def __init__(self) -> None:
            self._chunks = [b"event: ping\ndata: {}\n\n", b""]

        def read1(self, _size: int) -> bytes:
            time.sleep(0.12)
            return self._chunks.pop(0)

    handler = ProxyHandler.__new__(ProxyHandler)
    handler.wfile = io.BytesIO()  # type: ignore[assignment]
    assert handler._relay_stream(_SlowResponse(), gemini_sse=False, keepalive=True, interval=0.03)  # type: ignore[arg-type]
    relayed = handler.wfile.getvalue()
    assert relayed.startswith(_KEEPALIVE_LINE), relayed
    assert b"event: ping\ndata: {}\n\n" in relayed, relayed  # 본문은 그대로 — EOF 전 침묵에는 뒤에도 주석이 붙는다
    assert relayed.count(_KEEPALIVE_LINE) >= 2, relayed
    assert stats()["keepalives"] >= 2

    # unstream(결정 0051): 비스트리밍 답 하나를 클라이언트가 기대하는 SSE 로 짓는다.
    def _events(raw: bytes) -> list[tuple[str, dict]]:
        parsed: list[tuple[str, dict]] = []
        for chunk in raw.decode("utf-8").split("\n\n"):
            if not chunk.strip():
                continue
            name = ""
            data = "{}"
            for line in chunk.splitlines():
                if line.startswith("event: "):
                    name = line[len("event: "):]
                elif line.startswith("data: "):
                    data = line[len("data: "):]
            parsed.append((name, json.loads(data)))
        return parsed

    # 7. 글 — 생각 조각이 섞여 와도 index 가 차례대로 붙고 usage 가 두 이벤트로 나뉜다.
    text_answer = {
        "id": "msg_01", "type": "message", "role": "assistant", "model": "claude-opus-5",
        "content": [
            {"type": "thinking", "thinking": "음", "signature": "sig-abc"},
            {"type": "text", "text": "안녕하세요"},
        ],
        "stop_reason": "end_turn", "stop_sequence": None,
        "usage": {"input_tokens": 11, "cache_read_input_tokens": 7,
                  "cache_creation_input_tokens": 0, "output_tokens": 3},
    }
    events = _events(synthesize_anthropic_sse(text_answer))
    assert [name for name, _ in events] == [
        "message_start",
        "content_block_start", "content_block_delta", "content_block_delta", "content_block_stop",
        "content_block_start", "content_block_delta", "content_block_stop",
        "message_delta", "message_stop",
    ], events
    start = events[0][1]["message"]
    assert start["content"] == [] and start["id"] == "msg_01" and start["model"] == "claude-opus-5"
    assert start["usage"]["input_tokens"] == 11 and start["usage"]["cache_read_input_tokens"] == 7
    assert start["usage"]["output_tokens"] == 0 and start["stop_reason"] is None
    assert events[1][1]["content_block"] == {"type": "thinking", "thinking": "", "signature": ""}
    assert events[2][1]["delta"] == {"type": "thinking_delta", "thinking": "음"}
    assert events[3][1]["delta"] == {"type": "signature_delta", "signature": "sig-abc"}
    assert events[5][1]["index"] == 1 and events[5][1]["content_block"] == {"type": "text", "text": ""}
    assert events[6][1]["delta"] == {"type": "text_delta", "text": "안녕하세요"}
    assert events[-2][1]["delta"] == {"stop_reason": "end_turn", "stop_sequence": None}
    assert events[-2][1]["usage"] == {"output_tokens": 3}
    assert events[-1][1] == {"type": "message_stop"}

    # 8. 도구 호출 — input 전체가 input_json_delta 하나에 JSON 문자열로 실린다 (Claude Code 가 읽는 꼴).
    tool_input = {"file_path": "C:/일감/x.py", "limit": 10, "nested": {"a": [1, 2]}}
    tool_answer = {
        "id": "msg_02", "type": "message", "role": "assistant", "model": "claude-opus-5",
        "content": [{"type": "tool_use", "id": "toolu_01", "name": "Read", "input": tool_input}],
        "stop_reason": "tool_use", "stop_sequence": None,
        "usage": {"input_tokens": 9, "output_tokens": 21},
    }
    tool_events = _events(synthesize_anthropic_sse(tool_answer))
    deltas = [data for name, data in tool_events if name == "content_block_delta"]
    assert len(deltas) == 1, deltas
    assert deltas[0]["delta"]["type"] == "input_json_delta"
    assert json.loads(deltas[0]["delta"]["partial_json"]) == tool_input
    opening = [data for name, data in tool_events if name == "content_block_start"][0]
    assert opening["content_block"] == {"type": "tool_use", "id": "toolu_01", "name": "Read", "input": {}}
    assert tool_events[-2][1]["delta"]["stop_reason"] == "tool_use"

    # 9. 오류 — 상류 몸이 JSON 이면 그 error 를, 앞단 HTML 504 면 상태와 첫 줄을 담는다.
    json_error = _events(anthropic_sse_error(500, _json_bytes(
        {"type": "error", "error": {"type": "api_error", "message": "게이트웨이 실패"}})))
    assert json_error[0][0] == "error"
    assert json_error[0][1] == {"type": "error",
                                "error": {"type": "api_error", "message": "게이트웨이 실패"}}
    html_error = _events(anthropic_sse_error(
        504, b"<html><body><h1>504 Gateway Time-out</h1>\nThe server didn't respond in time.\n"))
    assert html_error[0][1]["error"]["type"] == "api_error"
    assert "504" in html_error[0][1]["error"]["message"], html_error

    print("Self-test: OK")


def main() -> None:
    try:
        server = ProxyServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    except OSError as error:
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
