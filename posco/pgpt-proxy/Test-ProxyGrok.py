"""Grok 경로 검사 — 프록시가 Grok 4 추론 경로가 거부하는 필드만 떼고 나머지는 그대로 넘기나 (v33).

xAI 의 Grok 4 추론 모델은 `presence_penalty` · `frequency_penalty` · `stop` 을 받으면 턴 전체를 400 으로 돌려준다.
게이트웨이 목록의 옛 ID(`grok-4-1-fast-*`)는 `reasoning_effort` 까지 거부한다. OpenAI 호환 클라이언트가 흔히
붙이는 옵션 하나로 Grok 세션이 통째로 죽지 않게 프록시가 뗀다.
가짜 게이트웨이와 프록시를 이 프로세스 안에 띄우고 **Grok Build 가 보내는 꼴(chat_completions · 도구 · 스트림)**
으로 보낸 뒤, 상류가 받은 본문과 클라이언트가 받은 스트림을 잰다. 망도 회사 키도 안 쓴다.

    python -X utf8 posco/pgpt-proxy/Test-ProxyGrok.py

⚠ 떼는 것 말고는 한 글자도 안 바뀌어야 한다 — 도구 · 메시지 · 스트림 옵션 · max_tokens 그대로.
⚠ `-non-reasoning` 은 stop · penalty 를 받는다. grok-4.3 이후는 reasoning_effort 를 받는다.
⚠ chat 꼴 도구(`{"type": "function", "function": {...}}`)의 빈 설명은 function 안에서만 채운다.
⚠ 손잡이(PGPT_PROXY_GROK_STRIP=0)를 끄면 아무것도 안 떼는 것도 잰다.
"""
from __future__ import annotations

import copy
import http.client
import importlib.util
import json
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("proxy", ROOT / "opus5_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

SEEN: list[dict] = []
PATH = "/gpgpta01-gpt/v1/chat/completions"
REJECTED = ("presence_penalty", "frequency_penalty", "stop")

# 도구 호출 한 번을 조각으로 나눠 보내는 Grok 스트림(OpenAI chat.completion.chunk 꼴)
STREAM_EVENTS = [
    {"choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}}]},
    {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "id": "call_1", "type": "function",
                                                         "function": {"name": "read_file", "arguments": ""}}]}}]},
    {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "function": {"arguments": "{\"path\":"}}]}}]},
    {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "function": {"arguments": "\"a.txt\"}"}}]}}]},
    {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]},
    {"choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}},
]


class Gateway(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802 — http.server 의 이름
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = json.loads(self.rfile.read(length))
        SEEN.append(body)
        # 실제 xAI 처럼 거부 필드가 남아 있으면 400 을 돌려준다 — 프록시가 놓치면 여기서 드러난다
        model = str(body.get("model", ""))
        bad = [k for k in REJECTED if k in body] if "non-reasoning" not in model else []
        if model.startswith("grok-4-1-fast") and "reasoning_effort" in body:
            bad.append("reasoning_effort")
        if bad:
            data = json.dumps({"code": "Client specified an invalid argument",
                               "error": f"Argument not supported on this model: {bad[0]}"}).encode()
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        base = {"id": "chatcmpl-1", "object": "chat.completion.chunk", "created": 1, "model": model}
        if body.get("stream"):
            raw = b"".join(b"data: " + json.dumps({**base, **event}).encode() + b"\n\n" for event in STREAM_EVENTS)
            raw += b"data: [DONE]\n\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        data = json.dumps({**base, "object": "chat.completion", "choices": [
            {"index": 0, "message": {"role": "assistant", "content": "OK"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def build_turn(model: str, *, stream: bool = True, **extra: object) -> dict:
    """Grok Build 가 보내는 꼴 — 시스템 · user · 도구 결과 턴, function 도구, 스트림 사용량."""
    payload = {
        "model": model, "stream": stream, "max_completion_tokens": 8192,
        "messages": [
            {"role": "system", "content": "You are Grok Build."},
            {"role": "user", "content": "a.txt 를 읽어 줘"},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_0", "type": "function", "function": {"name": "list_dir", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "call_0", "content": "a.txt"},
        ],
        "tools": [{"type": "function", "function": {
            "name": "read_file", "description": "Read a file",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}],
        "tool_choice": "auto", "parallel_tool_calls": True, "temperature": 0.2,
    }
    if stream:
        payload["stream_options"] = {"include_usage": True}
    payload.update(extra)
    return payload


def post(port: int, payload: dict) -> tuple[int, bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    data = json.dumps(payload).encode()
    conn.request("POST", PATH, body=data, headers={"Content-Type": "application/json",
                                                   "Authorization": "Bearer test-key"})
    response = conn.getresponse()
    raw = response.read()
    conn.close()
    return response.status, raw


def stream_events(raw: bytes) -> list[dict]:
    events = []
    for line in raw.decode("utf-8").splitlines():
        if line.startswith("data: ") and line != "data: [DONE]":
            events.append(json.loads(line[6:]))
    return events


def main() -> int:
    work = tempfile.TemporaryDirectory()
    proxy.LOG_PATH = Path(work.name) / "proxy.log"
    gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
    proxy._UPSTREAM_POOL = proxy.UpstreamPool(f"http://127.0.0.1:{gateway.server_port}")
    server = proxy.ProxyServer(("127.0.0.1", 0), proxy.ProxyHandler)
    for s in (gateway, server):
        threading.Thread(target=s.serve_forever, daemon=True).start()
    port = server.server_port
    failures = 0

    def check(name: str, ok: bool, detail: object = "") -> None:
        nonlocal failures
        failures += 0 if ok else 1
        print(f"{'OK  ' if ok else 'FAIL'} {name}" + ("" if ok else f" — {detail}"))

    def expect(sent: dict, *drop: str) -> dict:
        want = copy.deepcopy(sent)
        for name in drop:
            want.pop(name, None)
        return want

    before = proxy.stats()["grok_params_dropped"]

    # 1. 거부 필드가 모두 붙은 옛 추론 ID — 넷 다 떼고 나머지는 그대로
    sent = build_turn("grok-4-1-fast-reasoning", reasoning_effort="high", stop=["\n\n"],
                      presence_penalty=0.1, frequency_penalty=0.2)
    status, raw = post(port, sent)
    check("grok-4-1-fast-reasoning: 거부 필드 넷을 떼고 통과", status == 200, f"HTTP {status} {raw[:200]!r}")
    check("  나머지 본문(도구 · 메시지 · 스트림 옵션 · 상한) 그대로",
          SEEN[-1] == expect(sent, "reasoning_effort", "stop", "presence_penalty", "frequency_penalty"),
          sorted(set(SEEN[-1]) ^ set(sent)))

    # 2. 스트림의 도구 호출 조각이 클라이언트에 그대로 온다
    events = stream_events(raw)
    arguments = "".join(c["delta"]["tool_calls"][0]["function"].get("arguments", "")
                        for e in events for c in e.get("choices", []) if c.get("delta", {}).get("tool_calls"))
    check("  스트림 도구 호출 조각 · 끝 사유 · 사용량 전달",
          arguments == '{"path":"a.txt"}' and raw.rstrip().endswith(b"data: [DONE]")
          and any(c.get("finish_reason") == "tool_calls" for e in events for c in e.get("choices", []))
          and any(e.get("usage") for e in events), arguments)

    # 3. 거부 필드가 없는 깨끗한 요청은 손대지 않는다
    sent = build_turn("grok-4-1-fast-reasoning")
    status, _ = post(port, sent)
    check("깨끗한 요청은 그대로", status == 200 and SEEN[-1] == sent, f"HTTP {status}")

    # 4. -non-reasoning 은 stop · penalty 를 받는다(옛 ID 라 effort 만 뗀다)
    sent = build_turn("grok-4-1-fast-non-reasoning", stream=False, stop=["END"], presence_penalty=0.3,
                      reasoning_effort="low")
    status, _ = post(port, sent)
    check("grok-4-1-fast-non-reasoning: effort 만 떼고 stop · penalty 유지",
          status == 200 and SEEN[-1] == expect(sent, "reasoning_effort"), f"HTTP {status}")

    # 5. 새 ID(grok-4.3)는 effort 를 받고 stop · penalty 만 뗀다
    sent = build_turn("grok-4.3", reasoning_effort="low", stop=["END"], frequency_penalty=0.5)
    status, _ = post(port, sent)
    check("grok-4.3: effort 유지 · stop · penalty 만 뗌",
          status == 200 and SEEN[-1] == expect(sent, "stop", "frequency_penalty"), f"HTTP {status}")

    # 5a. 빈 설명 도구는 function 안만 채운다 — 도구 바깥에 칸을 붙이지 않는다(v31 까지는 바깥에 붙였다)
    sent = build_turn("grok-4-1-fast-reasoning")
    sent["tools"][0]["function"]["description"] = ""
    status, _ = post(port, sent)
    tool = SEEN[-1]["tools"][0]
    check("빈 설명 도구: function.description 만 채움", status == 200 and sorted(tool) == ["function", "type"]
          and tool["function"]["description"] == "read_file tool", tool)

    # 6. Grok 이 아닌 모델은 손대지 않는다
    sent = build_turn("gpt-4o", stop=["END"], presence_penalty=0.1)
    post(port, sent)
    check("GPT 요청의 stop · penalty 는 그대로", SEEN[-1] == sent)

    check("/health 의 뗀 수", proxy.stats()["grok_params_dropped"] - before == 7,
          proxy.stats()["grok_params_dropped"] - before)

    # 7. 손잡이를 끄면 그대로 보낸다(가짜 게이트웨이가 400 — 실제 xAI 와 같은 반응)
    proxy.GROK_STRIP = False
    sent = build_turn("grok-4-1-fast-reasoning", stop=["\n\n"])
    status, _ = post(port, sent)
    check("손잡이 끔(PGPT_PROXY_GROK_STRIP=0) → 그대로 · 게이트웨이 400 이 클라이언트에 간다",
          status == 400 and SEEN[-1] == sent, f"HTTP {status}")
    proxy.GROK_STRIP = True

    for s in (server, gateway):
        s.shutdown()
        s.server_close()
    print("결과:", "모두 통과" if not failures else f"실패 {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
