"""P-GPT 게이트웨이 스텁.

사내망 밖(맥·집 PC)에서 설치기와 프록시를 끝까지 돌려 보기 위한 최소 구현.
실제 게이트웨이의 계약 중 설치기가 의존하는 부분만 흉내낸다.

    python3 tests/mock_gateway.py 18902

* 모든 경로에서 ``Authorization: Bearer <key>`` 를 요구한다.
  Gemini 경로(/v1beta)도 마찬가지 — 프록시가 ``x-goog-api-key`` 를 Bearer 로
  덧붙이지 못하면 여기서 401 이 나므로 회귀가 바로 드러난다.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

PREFIX = "/gpgpta01-gpt"
# 사내 포털에 등록돼 있는 이름들(2026-08 기준). Grok 만 대시 표기다.
MODELS = [
    "claude-opus-5",
    "claude-opus-4.7",
    "claude-sonnet-4.6",
    "gpt-5.6-sol",
    "gpt-5.5",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "grok-4-1-fast-reasoning",
    "grok-4-1-fast-non-reasoning",
]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _send(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except ValueError:
            return {}

    def _authorized(self, query: str) -> bool:
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer ") or len(header) < 24:
            self._send(401, {"error": {"code": "P001", "message": "인증 실패"}})
            return False
        return True

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if not self._authorized(parsed.query):
            return
        if parsed.path == f"{PREFIX}/v1/models":
            self._send(200, {
                "object": "list",
                "data": [{"id": name, "object": "model", "owned_by": "p-gpt"} for name in MODELS],
            })
            return
        self._send(404, {"error": {"message": f"unknown path {parsed.path}"}})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if not self._authorized(parsed.query):
            return
        body = self._body()
        path = parsed.path

        if path == f"{PREFIX}/v1/messages":
            # 프록시가 prefill 을 떼지 못하면 실제 게이트웨이처럼 400 을 낸다
            messages = body.get("messages") or []
            if messages and messages[-1].get("role") != "user":
                self._send(400, {"type": "error", "error": {"message": "assistant prefill 은 허용되지 않습니다."}})
                return
            self._send(200, {
                "id": "msg_mock", "type": "message", "role": "assistant",
                "model": body.get("model"),
                "content": [{"type": "text", "text": "OK"}],
            })
            return

        if path == f"{PREFIX}/v1/responses":
            # 빈 tool description 이 남아 있으면 실제 게이트웨이처럼 400
            for item in body.get("input") or []:
                if isinstance(item, dict):
                    for tool in item.get("tools") or []:
                        if isinstance(tool, dict) and not str(tool.get("description", "")).strip():
                            self._send(400, {"error": {"code": "empty_string", "message": "tool description minLength=1"}})
                            return
            self._send(200, {"id": "resp_mock", "status": "completed", "model": body.get("model")})
            return

        if path == f"{PREFIX}/v1/chat/completions":
            self._send(200, {
                "id": "chatcmpl_mock", "object": "chat.completion", "model": body.get("model"),
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "OK"}, "finish_reason": "stop"}],
            })
            return

        if path.startswith(f"{PREFIX}/v1beta/models/") and ":streamGenerateContent" in path:
            for tool in body.get("tools") or []:
                if isinstance(tool, dict) and "description" in tool:
                    self._send(400, {"error": {
                        "code": 400, "status": "INVALID_ARGUMENT",
                        "message": "Invalid JSON payload received. "
                                   "Unknown name \"description\" at 'tools[0]': Cannot find field.",
                    }})
                    return
            chunk = json.dumps({
                "candidates": [{"content": {"role": "model", "parts": [{"text": "OK"}]},
                                "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1, "totalTokenCount": 2},
                "modelVersion": path.split("/")[-1].split(":")[0],
            }, ensure_ascii=False)
            data = f"data: {chunk}\r\n\r\n".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path.startswith(f"{PREFIX}/v1beta/models/"):
            # 프록시가 Gemini tools 에 description 을 끼워 넣으면 실제 게이트웨이처럼 400.
            # Gemini Tool 스키마에는 그 필드가 없다.
            for tool in body.get("tools") or []:
                if isinstance(tool, dict) and "description" in tool:
                    self._send(400, {"error": {
                        "code": 400, "status": "INVALID_ARGUMENT",
                        "message": "Invalid JSON payload received. "
                                   "Unknown name \"description\" at 'tools[0]': Cannot find field.",
                    }})
                    return
            self._send(200, {
                "candidates": [{"content": {"role": "model", "parts": [{"text": "OK"}]}, "finishReason": "STOP"}],
                "modelVersion": path.split("/")[-1].split(":")[0],
            })
            return

        self._send(404, {"error": {"message": f"unknown path {path}"}})


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18902
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    print(f"mock gateway on 127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
