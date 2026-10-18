"""웹서치 메움 검사 — 프록시가 Claude Code 의 웹서치 하위 요청을 제미나이 검색으로 메우나 (v27 · v28).

가짜 게이트웨이와 프록시를 이 프로세스 안에 띄우고 **CLI 가 보내는 꼴 그대로** 하위 요청을 보낸다. 돌아온
SSE 를 SDK 처럼 칸으로 다시 짓고, CLI 가 그 칸을 읽는 규칙(2.1.293 바이너리의 `hs()` 와 결과 글 짓기)을 그대로
옮겨 **모델이 받을 글**을 만든 뒤 그 글을 잰다. 망도 회사 키도 안 쓴다.

    python -X utf8 posco/pgpt-proxy/Test-ProxyWebSearch.py

⚠ **양방향이다.** 메우는 것만 재면 「안 건드릴 요청까지 가로채는」 결함이 안 잡힌다 — 서버 웹서치 선언이 없는
  요청 · 손잡이를 끈 판은 원래 길(`/v1/messages`)로 그대로 가야 한다.
⚠ **상류가 무엇을 받았나도 잰다** — 경로(제미나이 모델) · 쿼리(Anthropic 쪽 것은 뺐다) · 머리(회사 키가 두
  이름으로) · 본문(검색 도구 · 질의가 UTF-8 그대로). 한국어 질의가 다른 인코딩으로 가면 게이트웨이 너머에서 깨진다(실측).
⚠ **가짜 게이트웨이는 실물이 거절하는 것을 거절한다** — 제미나이 경로에 모르는 쿼리가 오면 실물과 같은 400 을 낸다.
  CLI 는 하위 요청을 `/v1/messages?beta=true` 로 보내는데(사내 PC 실측), 그 쿼리를 빼고 재면 메움이 실물에서만 진다.
⚠ **집에서 초록인 것은 모양까지다** — 게이트웨이의 제미나이가 grounding 으로 실제 웹을 찾는 것은 회사에서만 잰다.
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("proxy", ROOT / "opus5_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

KEY = "test-key-0000"
QUERY_EN = "python 3.13 release notes"
QUERY_KO = "파이썬 최신 버전 출시일"
MODE: dict[str, str] = {"answer": "ok"}
SEEN: list[dict] = []
# CLI 가 하위 요청을 보내는 경로 — 쿼리까지가 실물이다(사내 PC 의 프록시 기록 2026-10-08)
CLI_PATH = "/gpgpta01-gpt/v1/messages?beta=true"
# 제미나이 경로가 받는 쿼리 이름 — 나머지는 실물 게이트웨이가 「Cannot bind query parameter」 400 으로 거절한다
GEMINI_QUERY_NAMES = {"key", "alt"}

GROUNDED = {
    "candidates": [{
        "content": {"parts": [{"text": "searching", "thought": True},
                              {"text": "Python 3.14.8 was released on 2026-09-30."}]},
        "groundingMetadata": {
            "webSearchQueries": ["latest python release"],
            "groundingChunks": [
                {"web": {"uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AAA", "title": "python.org"}},
                {"web": {"uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/BBB", "title": "herodevs.com"}},
            ],
        },
    }],
    "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 34},
}


class Gateway(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802 — http.server 의 이름
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        url = urlsplit(self.path)
        SEEN.append({"path": url.path, "query": url.query,
                     "headers": {k.lower(): v for k, v in self.headers.items()}, "body": body})
        unknown = [name for name, _ in parse_qsl(url.query) if name not in GEMINI_QUERY_NAMES]
        if url.path.endswith("/v1/messages"):
            data = json.dumps({"type": "message", "id": "msg_gw", "model": "claude-opus-5", "role": "assistant",
                               "content": [{"type": "text", "text": "plain"}], "stop_reason": "end_turn",
                               "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}).encode()
            status = 200
        elif unknown:
            data = json.dumps({"error": {"code": 400, "status": "INVALID_ARGUMENT", "message": (
                f'Invalid JSON payload received. Unknown name "{unknown[0]}": Cannot bind query parameter. '
                f"Field '{unknown[0]}' could not be found in request message.")}}).encode()
            status = 400
        elif MODE["answer"] == "error":
            data, status = b'{"error":{"code":500,"message":"boom"}}', 500
        elif MODE["answer"] == "ratelimit":
            data, status = b'{"error":{"code":429,"message":"slow down"}}', 429
        elif MODE["answer"] == "slow":
            time.sleep(2.0)
            data, status = json.dumps(GROUNDED).encode(), 200
        elif MODE["answer"] == "garbage":
            data, status = b"<html>not json</html>", 200
        else:
            data, status = json.dumps(GROUNDED).encode(), 200
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def cli_request(query: str, *, stream: bool = True, server_tool: bool = True) -> dict:
    """CLI 웹서치 하위 요청의 꼴 — 2.1.293 바이너리에서 옮겼다(첫 user 글 · 시스템 글 · 도구 지정 · 서버 도구)."""
    tools = ([{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}] if server_tool
             else [{"name": "WebSearch", "description": "client tool", "input_schema": {"type": "object"}}])
    return {"model": "claude-opus-5", "max_tokens": 4096, "stream": stream,
            "system": [{"type": "text", "text": "You are an assistant for performing a web search tool use"}],
            "messages": [{"role": "user", "content": [{"type": "text",
                                                       "text": "Perform a web search for the query: " + query}]}],
            "tools": tools, "tool_choice": {"type": "tool", "name": tools[0]["name"]}}


def post(port: int, payload: dict) -> tuple[int, str, bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("POST", CLI_PATH, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                     {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}",
                      "anthropic-version": "2023-06-01"})
        response = conn.getresponse()
        return response.status, response.getheader("Content-Type") or "", response.read()
    finally:
        conn.close()


def blocks_from_sse(data: bytes) -> list[dict]:
    """SDK 처럼 SSE 를 칸으로 다시 짓는다 — 시작 칸 + 조각."""
    blocks: list[dict] = []
    partial: dict[int, str] = {}
    for line in data.splitlines():
        if not line.startswith(b"data: "):
            continue
        event = json.loads(line[6:])
        if event["type"] == "content_block_start":
            blocks.append(dict(event["content_block"]))
        elif event["type"] == "content_block_delta":
            delta, block = event["delta"], blocks[event["index"]]
            if delta["type"] == "text_delta":
                block["text"] = block.get("text", "") + delta["text"]
            elif delta["type"] == "input_json_delta":
                partial[event["index"]] = partial.get(event["index"], "") + delta["partial_json"]
        elif event["type"] == "content_block_stop" and event["index"] in partial:
            blocks[event["index"]]["input"] = json.loads(partial.pop(event["index"]))
    return blocks


def cli_tool_result(query: str, blocks: list[dict]) -> str:
    """CLI 가 칸을 결과로 읽고(`hs()`) 모델에게 줄 글을 짓는 규칙 — 바이너리에서 옮겼다."""
    results: list[object] = []
    text = ""
    for block in blocks:
        if block.get("type") == "server_tool_use":
            if text.strip():
                results.append(text.strip())
            text = ""
            continue
        if block.get("type") == "web_search_tool_result":
            if not isinstance(block.get("content"), list):
                results.append(f"Web search error: {block['content'].get('error_code')}")
                continue
            results.append({"content": [{"title": r["title"], "url": r["url"]} for r in block["content"]]})
        if block.get("type") == "text":
            text += block["text"]
    if text.strip():
        results.append(text.strip())
    out = f'Web search results for query: "{query}"\n\n'
    for item in results:
        if isinstance(item, str):
            out += item + "\n\n"
        elif item["content"]:
            out += "Links: " + json.dumps(item["content"]) + "\n\n"
        else:
            out += "No links found.\n\n"
    return out.strip()


def main() -> int:
    work = tempfile.TemporaryDirectory(prefix="pgpt-websearch-")
    proxy.LOG_PATH = Path(work.name) / "proxy.log"
    gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
    proxy._UPSTREAM_POOL = proxy.UpstreamPool(f"http://127.0.0.1:{gateway.server_port}")
    server = proxy.ProxyServer(("127.0.0.1", 0), proxy.ProxyHandler)
    for s in (gateway, server):
        threading.Thread(target=s.serve_forever, daemon=True).start()
    port = server.server_port
    fails: list[str] = []
    # 출처 주소 풀기(v28)는 밖(구글)으로 HEAD 를 보낸다 — 이 검사는 망을 안 쓰므로 끄고, ⑥ 에서 가짜로 잰다
    proxy.WEB_SEARCH_RESOLVE = False

    def check(name: str, ok: bool, detail: object = "") -> None:
        print(("✓ " if ok else "✗ ") + name + ("" if ok else f" — {detail}"))
        if not ok:
            fails.append(name)

    try:
        # ① 메운다 — 스트림 · 영어
        before = proxy.stats()["web_search_filled"]
        status, ctype, data = post(port, cli_request(QUERY_EN))
        got = SEEN[-1]
        text = cli_tool_result(QUERY_EN, blocks_from_sse(data))
        check("스트림 하위 요청에 200 · SSE 로 답한다", status == 200 and ctype.startswith("text/event-stream"), (status, ctype))
        check("상류는 제미나이 검색 경로를 받았다",
              got["path"].endswith(f"/v1beta/models/{proxy.WEB_SEARCH_MODEL}:generateContent"), got["path"])
        check("상류 쿼리에 Anthropic 쪽 것(beta)이 안 실린다", "beta" not in got["query"], got["query"])
        sent = json.loads(got["body"])
        check("상류 본문 — 검색 도구 · 질의", sent.get("tools") == [{"googleSearch": {}}]
              and QUERY_EN in sent["contents"][0]["parts"][0]["text"], sent)
        check("상류 머리 — 회사 키가 두 이름으로 · Anthropic 머리는 뺐다",
              got["headers"].get("x-goog-api-key") == KEY and got["headers"].get("authorization") == f"Bearer {KEY}"
              and "anthropic-version" not in got["headers"], got["headers"])
        check("모델이 받을 글에 출처 둘이 Links 로 선다",
              "Links: " in text and "grounding-api-redirect/AAA" in text and "herodevs.com" in text, text)
        check("모델이 받을 글에 검색 본문이 실리고 생각 조각은 빠진다",
              "3.14.8" in text and "searching" not in text, text)
        check("「출처 없음」이 안 선다", "No links found" not in text and "Web search error" not in text, text)
        check("메운 수를 센다", proxy.stats()["web_search_filled"] == before + 1, proxy.stats()["web_search_filled"])

        # ② 한국어 질의가 UTF-8 그대로 상류에 닿는다
        post(port, cli_request(QUERY_KO))
        body = SEEN[-1]["body"]
        check("한국어 질의가 UTF-8 그대로 상류에 간다", QUERY_KO.encode("utf-8") in body, body[:200])

        # ③ 비스트림이면 JSON 메시지
        status, ctype, data = post(port, cli_request(QUERY_EN, stream=False))
        message = json.loads(data) if ctype.startswith("application/json") else {}
        check("비스트림 하위 요청은 JSON 메시지로 답한다",
              [b.get("type") for b in message.get("content", [])] == ["server_tool_use", "web_search_tool_result", "text"],
              (ctype, data[:200]))

        # ④ 상류가 지면 검색 오류 칸 — 대화는 안 깨진다
        for answer in ("error", "garbage"):
            MODE["answer"] = answer
            failed = proxy.stats()["web_search_failed"]
            status, _, data = post(port, cli_request(QUERY_EN))
            text = cli_tool_result(QUERY_EN, blocks_from_sse(data))
            check(f"상류가 {answer} 면 200 · 「Web search error: unavailable」",
                  status == 200 and "Web search error: unavailable" in text, (status, text))
            check(f"상류가 {answer} 면 진 수를 센다", proxy.stats()["web_search_failed"] == failed + 1)
        MODE["answer"] = "ok"
        log = proxy.LOG_PATH.read_text(encoding="utf-8") if proxy.LOG_PATH.exists() else ""
        check("상류가 4xx · 5xx 면 그 본문을 기록에 남긴다", "boom" in log, log[-400:])

        # ⑤ 안 건드릴 것 — 서버 웹서치 선언이 없는 요청 · 손잡이를 끈 판
        post(port, cli_request(QUERY_EN, server_tool=False))
        check("클라이언트 도구 요청은 원래 길(/v1/messages · 쿼리 그대로)로 간다",
              SEEN[-1]["path"].endswith("/v1/messages") and SEEN[-1]["query"] == "beta=true", SEEN[-1])
        proxy.WEB_SEARCH = False
        try:
            post(port, cli_request(QUERY_EN))
            check("손잡이를 끄면 원래 길로 간다", SEEN[-1]["path"].endswith("/v1/messages"), SEEN[-1]["path"])
        finally:
            proxy.WEB_SEARCH = True
        log = proxy.LOG_PATH.read_text(encoding="utf-8") if proxy.LOG_PATH.exists() else ""
        check("기록에 갈래가 남는다(kind=web_search · sources=2)", "kind=web_search" in log and "sources=2" in log, log[-400:])

        # ⑥ (v28) 서버 웹서치를 선언했어도 CLI 머리가 없는 여러 턴 대화는 가로채지 않는다
        multi = cli_request(QUERY_EN)
        multi["messages"] = [{"role": "user", "content": "Hello, what is new in python?"},
                             {"role": "assistant", "content": [{"type": "text", "text": "Let me check."}]},
                             {"role": "user", "content": "thanks, also search rust"}]
        post(port, multi)
        check("CLI 머리가 없는 여러 턴 대화는 원래 길로 간다", SEEN[-1]["path"].endswith("/v1/messages"), SEEN[-1]["path"])
        reminder = cli_request(QUERY_EN)
        reminder["messages"][0]["content"].insert(0, {"type": "text", "text": "<system-reminder>ctx</system-reminder>"})
        post(port, reminder)
        sent = json.loads(SEEN[-1]["body"])["contents"][0]["parts"][0]["text"]
        check("머리 앞에 붙은 다른 글 조각은 질의에 안 섞인다", QUERY_EN in sent and "system-reminder" not in sent, sent)

        # ⑦ (v28) 출처 주소를 원래 주소로 푼다(가짜 HEAD) — 못 푼 것은 경유 주소 그대로
        real = {"https://vertexaisearch.cloud.google.com/grounding-api-redirect/AAA": "https://www.python.org/downloads/"}
        original = proxy._resolve_grounding_url
        proxy._resolve_grounding_url = lambda url: real.get(url)
        proxy.WEB_SEARCH_RESOLVE = True
        try:
            status, _, data = post(port, cli_request(QUERY_EN))
            text = cli_tool_result(QUERY_EN, blocks_from_sse(data))
            check("푼 출처는 원래 주소로, 못 푼 출처는 경유 주소로 실린다",
                  "https://www.python.org/downloads/" in text and "grounding-api-redirect/AAA" not in text
                  and "grounding-api-redirect/BBB" in text, text)
        finally:
            proxy._resolve_grounding_url = original
            proxy.WEB_SEARCH_RESOLVE = False

        # ⑧ (v28) 상태별 오류 코드 · 시한 · 연결 실패도 검색 오류 칸(502 아님)
        MODE["answer"] = "ratelimit"
        status, _, data = post(port, cli_request(QUERY_EN))
        text = cli_tool_result(QUERY_EN, blocks_from_sse(data))
        check("상류가 429 면 「Web search error: too_many_requests」", status == 200 and "too_many_requests" in text, text)
        MODE["answer"] = "slow"
        saved_timeout = proxy.WEB_SEARCH_TIMEOUT
        proxy.WEB_SEARCH_TIMEOUT = 0.5
        try:
            started = time.monotonic()
            status, _, data = post(port, cli_request(QUERY_EN))
            took = time.monotonic() - started
            text = cli_tool_result(QUERY_EN, blocks_from_sse(data))
            check("검색 시한을 넘기면 시한 안에 「Web search error」로 답한다",
                  status == 200 and "Web search error: unavailable" in text and took < 1.8, (status, round(took, 2), text))
        finally:
            proxy.WEB_SEARCH_TIMEOUT = saved_timeout
            MODE["answer"] = "ok"
        dead = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
        dead_port = dead.server_port
        dead.server_close()
        saved_pool = proxy._UPSTREAM_POOL
        proxy._UPSTREAM_POOL = proxy.UpstreamPool(f"http://127.0.0.1:{dead_port}")
        try:
            failed = proxy.stats()["web_search_failed"]
            status, _, data = post(port, cli_request(QUERY_EN))
            text = cli_tool_result(QUERY_EN, blocks_from_sse(data))
            check("게이트웨이에 닿지 않으면 502 대신 200 · 「Web search error」",
                  status == 200 and "Web search error: unavailable" in text, (status, data[:200]))
            check("닿지 않은 것도 진 수로 센다", proxy.stats()["web_search_failed"] == failed + 1)
        finally:
            proxy._UPSTREAM_POOL = saved_pool
    finally:
        for s in (server, gateway):
            s.shutdown()
            s.server_close()
        work.cleanup()
    print("웹서치 메움 검사: " + ("OK" if not fails else f"{len(fails)} 개 어긋남"))
    return 1 if fails else 0


if __name__ == "__main__":
    # 회사 PC 콘솔은 cp949 라 ✓ 를 못 찍고 첫 줄에서 죽었다(VM 실측) — 못 적는 글자는 물음표로 바꿔 끝까지 돈다
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
