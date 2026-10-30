"""모델 대체 검사 — 프록시가 게이트웨이 `/v1/models` 목록을 읽고 그에 맞춰 이름을 고르나 (v32).

v31 까지는 하이쿠 · sonnet-5* 를 `claude-sonnet-4.6` 으로 박아 두고 바꿔 보냈다. 게이트웨이가 새 모델을 들여도
따라가지 않았다. v32 는 대체 대상 이름이 들어올 때만 목록을 읽어(키별 캐시) 목록에 있으면 그대로, 없으면 같은
계열의 가장 높은 판(하이쿠는 소네트까지)을 보낸다. 페이블(claude-fable-*)은 대상이 아니라 철자만 고쳐 그대로 보내고,
게이트웨이에 없으면 그 400 이 클라이언트에 보인다(결정 0164). 가짜 게이트웨이와 프록시를 이 프로세스 안에 띄워
잰다. 망도 회사 키도 안 쓴다.

    python -X utf8 posco/pgpt-proxy/Test-ProxyModelMap.py

⚠ 대체 대상이 아닌 이름(claude-opus-5 등)에는 목록을 읽지 않는다 — 평소 호출에 지연을 보태지 않는다.
⚠ 목록을 못 읽으면 v31 규칙으로 간다 — 요청은 막지 않는다.
⚠ 출력 상한(스트림 10000 · 비스트림 18000)은 대체된 모델에도 그대로 걸린다.
"""
from __future__ import annotations

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

PATH = "/gpgpta01-gpt/v1/messages?beta=true"
# 2026-10-15 실측 목록의 Claude 부분(#147) — 페이블 · 소네트 5 · 하이쿠는 없다
TODAY = ["claude-opus-5", "claude-opus-4.7", "claude-opus-4.6", "claude-opus-4.5",
         "claude-sonnet-4.6", "claude-sonnet-4.5", "gpt-5.5", "gemini-3.6-flash"]
STATE: dict[str, object] = {"models": list(TODAY), "list_status": 200, "list_calls": 0, "seen": []}


class Gateway(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        return

    def _send(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/gpgpta01-gpt/v1/models":
            STATE["list_calls"] = int(STATE["list_calls"]) + 1
            if not self.headers.get("Authorization", "").startswith("Bearer "):
                self._send(401, {"error": {"message": "no key"}})
                return
            status = int(STATE["list_status"])
            self._send(status, {"object": "list", "data": [{"id": m, "object": "model"} for m in STATE["models"]]}
                       if status == 200 else {"error": {"message": "down"}})
            return
        self._send(404, {})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = json.loads(self.rfile.read(length))
        STATE["seen"].append(body)  # type: ignore[union-attr]
        if body.get("model") not in STATE["models"]:
            self._send(400, {"type": "error", "error": {"type": "invalid_request_error",
                                                         "message": f"모델을 찾을 수 없습니다: {body.get('model')}"}})
            return
        self._send(200, {"id": "msg_1", "type": "message", "role": "assistant", "model": body["model"],
                         "content": [{"type": "text", "text": "OK"}], "stop_reason": "end_turn",
                         "usage": {"input_tokens": 1, "output_tokens": 1}})


def post(port: int, model: str, *, key: str = "test-key-0123456789", max_tokens: int = 32000) -> tuple[int, str, str]:
    """(상태, 상류가 받은 모델, x-pgpt-model-substituted 머리)"""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    body = json.dumps({"model": model, "max_tokens": max_tokens, "stream": False,
                       "messages": [{"role": "user", "content": "Reply exactly OK"}]})
    conn.request("POST", PATH, body=body, headers={"Content-Type": "application/json",
                                                   "Authorization": f"Bearer {key}",
                                                   "anthropic-version": "2023-06-01"})
    response = conn.getresponse()
    response.read()
    conn.close()
    seen = STATE["seen"][-1] if STATE["seen"] else {}  # type: ignore[index]
    return response.status, str(seen.get("model")), response.getheader("x-pgpt-model-substituted") or ""


def main() -> int:
    work = tempfile.TemporaryDirectory()
    proxy.LOG_PATH = Path(work.name) / "proxy.log"
    gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
    upstream = f"http://127.0.0.1:{gateway.server_port}"
    proxy._UPSTREAM = proxy.UpstreamTarget(upstream)
    proxy._GATEWAY_MODELS = proxy.GatewayModelList(upstream, ttl=600, retry=60, timeout=5)
    server = proxy.ProxyServer(("127.0.0.1", 0), proxy.ProxyHandler)
    for s in (gateway, server):
        threading.Thread(target=s.serve_forever, daemon=True).start()
    port = server.server_port
    failures = 0

    def check(name: str, ok: bool, detail: object = "") -> None:
        nonlocal failures
        failures += 0 if ok else 1
        print(f"{'OK  ' if ok else 'FAIL'} {name}" + ("" if ok else f" — {detail}"))

    # 1. 대체 대상이 아닌 이름은 목록을 읽지 않는다
    status, sent, header = post(port, "claude-opus-5")
    check("claude-opus-5 그대로 · 목록 안 읽음", (status, sent, header, STATE["list_calls"]) == (200, "claude-opus-5", "", 0),
          (status, sent, header, STATE["list_calls"]))
    # 페이블은 사람이 고르는 이름이라 대상이 아니다 — 철자만 고쳐 보내고 게이트웨이의 400 이 그대로 보인다(결정 0164).
    # 목록을 읽는 하이쿠보다 먼저 보내야 「목록 안 읽음」을 잰다.
    status, sent, header = post(port, "claude-fable-5-1")
    check("claude-fable-5-1 그대로 · 400 이 보인다 · 목록 안 읽음",
          (status, sent, header, STATE["list_calls"]) == (400, "claude-fable-5.1", "", 0),
          (status, sent, header, STATE["list_calls"]))

    # 2. 오늘 목록(#147): 하이쿠 · 소네트 5 → 소네트 4.6
    for model, want in (("claude-haiku-4-5-20251001", "claude-sonnet-4.6"), ("claude-sonnet-5", "claude-sonnet-4.6"),
                        ("claude-sonnet-5-5", "claude-sonnet-4.6")):
        status, sent, header = post(port, model)
        check(f"{model} → {want}", (status, sent) == (200, want) and header == f"{model} -> {want}", (status, sent, header))
    check("목록은 키당 한 번만 읽는다(캐시)", STATE["list_calls"] == 1, STATE["list_calls"])

    # 3. 게이트웨이가 새 모델을 들이면 대체를 멈추고 따라간다 — 다른 키는 따로 읽는다. 페이블은 대상이 아니라 목록에
    #    서면 손 안 대고 200 이다
    STATE["models"] = TODAY + ["claude-sonnet-5.5", "claude-haiku-4.5", "claude-fable-5.1"]
    for model, want, substituted in (("claude-sonnet-5-5", "claude-sonnet-5.5", False),
                                     ("claude-haiku-4-5-20251001", "claude-haiku-4.5", False),
                                     ("claude-fable-5-1", "claude-fable-5.1", False),
                                     ("claude-sonnet-5", "claude-sonnet-5.5", True)):
        status, sent, header = post(port, model, key="other-key-0123456789")
        check(f"새 목록: {model} → {want}", (status, sent) == (200, want) and bool(header) == substituted,
              (status, sent, header))
    check("새 키는 목록을 다시 읽는다", STATE["list_calls"] == 2, STATE["list_calls"])

    # 4. 출력 상한은 대체된 모델에도 걸린다(비스트림 18000)
    post(port, "claude-haiku-4-5", key="other-key-0123456789", max_tokens=64000)
    capped = STATE["seen"][-1].get("max_tokens")  # type: ignore[index]
    check("대체된 모델에도 출력 상한", capped == proxy.output_cap(unstream=True), capped)

    # 5. 목록을 못 읽으면 v31 규칙(하이쿠 → 소네트 4.6) — 요청은 막지 않는다
    STATE["models"] = list(TODAY)
    STATE["list_status"] = 503
    status, sent, header = post(port, "claude-haiku-4-5", key="third-key-0123456789")
    check("목록 실패 → 기본 규칙", (status, sent) == (200, "claude-sonnet-4.6"), (status, sent))
    status, sent, _ = post(port, "claude-fable-5-1", key="third-key-0123456789")
    check("페이블은 목록과 무관하게 손대지 않는다(게이트웨이가 판정)", (status, sent) == (400, "claude-fable-5.1"), (status, sent))
    calls = STATE["list_calls"]
    post(port, "claude-haiku-4-5", key="third-key-0123456789")
    check("실패 뒤에는 잠시 다시 묻지 않는다", STATE["list_calls"] == calls, (calls, STATE["list_calls"]))

    # 6. 사용자 규칙(PGPT_PROXY_MODEL_MAP)이 목록보다 앞선다
    proxy.MODEL_MAP = proxy.parse_model_map("claude-haiku*=claude-opus-4.7")
    status, sent, header = post(port, "claude-haiku-4-5")
    check("PGPT_PROXY_MODEL_MAP 우선", (status, sent) == (200, "claude-opus-4.7") and header, (status, sent, header))
    proxy.MODEL_MAP = []

    health = proxy.stats()
    check("/health 에 목록 계수", health["model_list_fetches"] == 3 and health["model_list_failures"] == 1
          and health["model_list_size"] > 0, {k: v for k, v in health.items() if k.startswith("model_")})
    log = proxy.LOG_PATH.read_text(encoding="utf-8")
    check("로그에 대체 근거(by=list · fixed · config)", all(f"by={src}" in log for src in ("list", "fixed", "config")))

    for s in (gateway, server):
        s.shutdown()
    print("전체: 통과" if not failures else f"전체: 실패 {failures}건")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
