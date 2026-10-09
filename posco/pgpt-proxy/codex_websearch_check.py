"""Check the Codex /v1/alpha/search -> gateway Responses bridge (#121)."""

from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

import opus5_proxy as proxy  # noqa: E402


KEY = "test-key-0000"
QUERY = "openai codex latest release"
SEEN: list[dict] = []
RESPONSES = {
    "id": "resp_test",
    "status": "completed",
    "output": [
        {"type": "web_search_call", "status": "completed",
         "action": {"type": "search", "query": QUERY}},
        {"type": "web_search_call", "status": "completed",
         "action": {"type": "open_page", "url": "https://github.com/openai/codex/releases/latest"}},
        {"type": "message", "role": "assistant", "content": [{
            "type": "output_text",
            "text": "The latest stable release is rust-v0.162.0.",
            "annotations": [{
                "type": "url_citation",
                "url": "https://github.com/openai/codex/releases/tag/rust-v0.162.0",
                "title": "openai/codex release",
            }],
        }]},
    ],
}


class Gateway(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        SEEN.append({"path": urlsplit(self.path).path,
                     "headers": {k.lower(): v for k, v in self.headers.items()}, "body": body})
        data = json.dumps(RESPONSES).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def request() -> dict:
    return {
        "id": "search-session",
        "model": "gpt-5.6-sol",
        "input": [{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": "Find the latest release."}]}],
        "commands": {"search_query": [{"q": QUERY, "domains": ["github.com"]}],
                     "open": [{"ref_id": "turn0search0"}],
                     "response_length": "short"},
        "settings": {"filters": {"allowed_domains": ["github.com"]},
                     "allowed_callers": ["direct"], "external_web_access": False},
        "max_output_tokens": 10000,
    }


def post(port: int, payload: dict) -> tuple[int, str, bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("POST", "/gpgpta01-gpt/v1/alpha/search",
                     json.dumps(payload, ensure_ascii=False).encode(),
                     {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
        response = conn.getresponse()
        return response.status, response.getheader("Content-Type") or "", response.read()
    finally:
        conn.close()


def main() -> int:
    work = tempfile.TemporaryDirectory(prefix="pgpt-codex-websearch-")
    proxy.LOG_PATH = Path(work.name) / "proxy.log"
    gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
    proxy._UPSTREAM_POOL = proxy.UpstreamPool(f"http://127.0.0.1:{gateway.server_port}")
    server = proxy.ProxyServer(("127.0.0.1", 0), proxy.ProxyHandler)
    for service in (gateway, server):
        threading.Thread(target=service.serve_forever, daemon=True).start()
    failures: list[str] = []

    def check(name: str, ok: bool, detail: object = "") -> None:
        print(("✓ " if ok else "✗ ") + name + ("" if ok else f" — {detail}"))
        if not ok:
            failures.append(name)

    try:
        status, content_type, raw = post(server.server_port, request())
        result = json.loads(raw)
        sent = SEEN[-1]
        sent_body = json.loads(sent["body"])
        check("Codex 검색은 200 JSON SearchResponse 로 돌아온다",
              status == 200 and content_type.startswith("application/json")
              and result.get("encrypted_output") is None, (status, content_type, result))
        check("본문과 구조화된 출처가 함께 돌아온다",
              "rust-v0.162.0" in result.get("output", "")
              and result.get("results", [{}])[0].get("ref_id") == "turn0search0"
              and result["results"][0].get("url", "").startswith("https://github.com/"), result)
        check("상류는 사내 게이트웨이의 Responses 웹 검색 길을 탄다",
              sent["path"].endswith("/v1/responses")
              and sent_body.get("tools") == [{"type": "web_search"}], sent)
        check("질의와 도메인 제한이 상류 프롬프트에 실린다",
              QUERY in sent_body["input"] and "github.com" in sent_body["input"]
              and "Open" in sent_body["input"], sent_body)
        check("회사 키가 Responses 머리에 실리고 Gemini 키로 복제되지 않는다",
              sent["headers"].get("authorization") == f"Bearer {KEY}"
              and "x-goog-api-key" not in sent["headers"], sent["headers"])

        hosted = {"model": "gpt-5.6-sol", "tools": [{"type": "web_search"}]}
        check("Responses 내장 web_search 에 description 을 붙이지 않는다",
              proxy.patch_tool_descriptions(hosted, "/gpgpta01-gpt/v1/responses") == 0
              and hosted == {"model": "gpt-5.6-sol", "tools": [{"type": "web_search"}]}, hosted)

        log = proxy.LOG_PATH.read_text(encoding="utf-8") if proxy.LOG_PATH.exists() else ""
        check("기록에 Codex 검색 갈래와 출처 수가 남는다",
              "kind=codex_web_search upstream=responses" in log and "sources=1" in log, log[-600:])
    finally:
        for service in (server, gateway):
            service.shutdown()
            service.server_close()
        work.cleanup()
    print("Codex 웹서치 메움 검사: " + ("OK" if not failures else f"{len(failures)} 개 어긋남"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
