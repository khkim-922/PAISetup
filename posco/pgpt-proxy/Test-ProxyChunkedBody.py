"""요청 본문 받기의 회귀 검사 — `Transfer-Encoding` 이 붙은 요청은 411 이다.

가짜 게이트웨이와 프록시를 이 프로세스 안에 띄워 잰다. 포트는 50000~60999 에서 고르고 끝나면 내린다. 망도 회사 키도 안 쓴다.

    python -X utf8 posco/pgpt-proxy/Test-ProxyChunkedBody.py

1. `Transfer-Encoding` 이 붙은 요청은 바르든 깨졌든 411 이고 상류로 가지 않는다(빈 본문으로도).
2. 기록에 본문 바이트가 안 남는다.

층 — 쓰는 사람의 계약(건넴 전 · 배포본 릴리스 전에 손으로 돌린다). 남긴 까닭 — 조용히 깨지고(chunked 본문이 길이 0 으로 읽혀
빈 요청이 상류로 간다) 다른 시험이 안 잡는다. 걷는 조건 — 411 을 내는 코드(`_read_body`)가 사라지거나 다른 시험이 같은 동작을 잴 때.
출처 — 우리 것이다(회사 실측 #226 ⑨).
"""
from __future__ import annotations

import importlib.util
import json
import os
import random
import socket
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 모듈을 읽는 순간의 기본값이 회사 게이트웨이를 가리키지 않게 한다(아래에서 가짜 게이트웨이로 바꿔 끼운다)
os.environ.setdefault("PGPT_PROXY_UPSTREAM", "http://127.0.0.1:9")
os.environ.setdefault("PGPT_PROXY_MODEL_LIST_TTL_SEC", "0")
spec = importlib.util.spec_from_file_location("proxy_chunked_body", HERE / "opus5_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

STATE: dict[str, object] = {"seen": []}


def bind_random(factory):
    """50000~60999 에서 빈 포트를 골라 띄운다."""
    for _ in range(300):
        port = random.randint(50000, 60999)
        try:
            return factory(("127.0.0.1", port))
        except OSError:
            continue
    raise RuntimeError("50000~60999 에서 빈 포트를 찾지 못했습니다")


class Gateway(BaseHTTPRequestHandler):
    """무엇이 왔나만 적고 200 으로 답한다 — 이 시험에서는 아무것도 오면 안 된다."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
        STATE["seen"].append({"path": self.path, "raw": raw})  # type: ignore[union-attr]
        data = json.dumps({"id": "resp_1", "object": "response", "status": "completed", "output": []}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def raw_request(port: int, data: bytes, *, half_close: bool = True) -> bytes:
    """원본 바이트를 보내고(끊긴 본문을 흉내 낼 때는 쓰기 쪽을 닫고) 응답 첫 줄을 돌려준다.

    쓰기 쪽을 닫으면 프록시는 상류로 보내기 전에 클라이언트가 떠났다고 본다(_client_disconnected) — 바른 본문은 닫지 않는다.
    """
    with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
        sock.sendall(data)
        if half_close:
            sock.shutdown(socket.SHUT_WR)
        reply = b""
        try:
            while True:
                piece = sock.recv(65536)
                if not piece:
                    break
                reply += piece
        except OSError:
            pass
    return reply.split(b"\r\n", 1)[0]


def main() -> int:
    work = tempfile.TemporaryDirectory()
    proxy.LOG_PATH = Path(work.name) / "proxy.log"
    gateway = bind_random(lambda addr: ThreadingHTTPServer(addr, Gateway))
    gateway.daemon_threads = True
    upstream = f"http://127.0.0.1:{gateway.server_port}"
    proxy._UPSTREAM = proxy.UpstreamTarget(upstream)
    proxy._GATEWAY_MODELS = proxy.GatewayModelList(upstream, ttl=0, retry=60, timeout=5)
    server = bind_random(lambda addr: proxy.ProxyServer(addr, proxy.ProxyHandler))
    for s in (gateway, server):
        threading.Thread(target=s.serve_forever, daemon=True).start()
    port = server.server_port
    failures = 0

    def check(name: str, ok: bool, detail: object = "") -> None:
        nonlocal failures
        failures += 0 if ok else 1
        print(f"{'OK  ' if ok else 'FAIL'} {name}" + ("" if ok else f" — {detail}"))

    def log_text() -> str:
        return proxy.LOG_PATH.read_text(encoding="utf-8") if proxy.LOG_PATH.exists() else ""

    try:
        # ── Transfer-Encoding 본문은 411 ─────────────────────────────────────────
        # 바른 chunked 도 깨진 chunked 도 본문을 안 읽고 411 · 연결을 닫는다. 상류로 가면(빈 본문 POST 포함) 실패다.
        head = (b"POST /gpgpta01-gpt/v1/responses HTTP/1.1\r\nHost: x\r\nAuthorization: Bearer k\r\n"
                b"Content-Type: application/json\r\n")
        first = b'{"model":"gpt-6-astra",'

        def chunk(data: bytes, ext: bytes = b"") -> bytes:
            return b"%X" % len(data) + ext + b"\r\n" + data + b"\r\n"

        whole = chunk(first) + chunk(b'"input":"rest"}', b";ext=1") + b"0\r\n\r\n"
        for name, coding, body, half_close in (
                ("바른 chunked 본문(확장 포함)", b"chunked", whole, False),
                ("16진 아닌 크기 줄", b"chunked", chunk(first) + b"ZZ-not-hex\r\n", True),
                ("끝 청크 없음(EOF)", b"chunked", chunk(first), True),
                ("Content-Length 와 함께 온 chunked", b"chunked\r\nContent-Length: 15", whole, False),
                ("chunked 아닌 coding", b"gzip", b"", False)):
            STATE["seen"].clear()  # type: ignore[union-attr]
            line = raw_request(port, head + b"Transfer-Encoding: " + coding + b"\r\n\r\n" + body, half_close=half_close)
            check(f"1. {name} → 411 · 상류로 안 감", line.startswith(b"HTTP/1.1 411") and not STATE["seen"],
                  (line, STATE["seen"]))
        raw_request(port, head + b"Transfer-Encoding: chunked\r\n\r\n" + chunk(first) + b"x" * 5000 + b"\r\n")
        refused = [entry for entry in log_text().splitlines() if "bad request body" in entry and "Transfer-Encoding" in entry]
        check("2. 기록에 본문 바이트가 안 남는다", refused and all("gpt-6-astra" not in e and "x" * 9 not in e for e in refused),
              refused)

    finally:
        for s in (gateway, server):
            s.shutdown()
            s.server_close()
        work.cleanup()
    print("전체: 통과" if not failures else f"전체: 실패 {failures}건")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
