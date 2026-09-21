"""로컬 프록시가 게이트웨이의 비정상 응답을 올바르게 넘기는지 본다(v16).

게이트웨이를 흉내 내는 작은 서버를 띄우고, 복사한 프록시를 다른 포트에서 돌려 확인한다.

    python3 tests/Test-ProxyFaults.py

* 도중에 끊긴 응답은 클라이언트도 잘린 응답으로 받는다(전에는 정상 종료처럼 보였다)
* 본문을 다 보내기 전에 온 응답(413)은 그대로 넘기고, 다시 보내지 않는다
* 풀에 죽은 연결이 여럿 있어도 새 연결로 한 번 더 시도해 성공한다
* 짝 없는 surrogate 가 든 요청에도 응답한다
* ``..`` 경로는 막는다
"""

from __future__ import annotations

import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COUNT: dict[str, int] = {}
FAILURES = 0


def check(condition: bool, message: str) -> None:
    global FAILURES
    print(("  PASS  " if condition else "  FAIL  ") + message)
    if not condition:
        FAILURES += 1


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def handle(conn: socket.socket) -> None:
    try:
        reader = conn.makefile("rb")
        while True:
            line = reader.readline()
            if not line:
                return
            _method, path, _ = line.decode().split(" ", 2)
            headers: dict[str, str] = {}
            while True:
                raw = reader.readline()
                if raw in (b"\r\n", b"\n", b""):
                    break
                key, value = raw.decode().split(":", 1)
                headers[key.strip().lower()] = value.strip()
            length = int(headers.get("content-length", "0"))
            key = path.split("?")[0].rsplit("/", 1)[-1]
            COUNT[key] = COUNT.get(key, 0) + 1
            if key == "big413":
                conn.sendall(b"HTTP/1.1 413 Payload Too Large\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")
                # 실제 서버(nginx 의 lingering close 등)처럼 남은 본문을 읽어 버린 뒤 닫는다. 읽지 않은 채 닫으면
                # Windows 는 RST 를 보내 먼저 보낸 413 까지 클라이언트 쪽에서 버려진다.
                conn.shutdown(socket.SHUT_WR)
                conn.settimeout(5)
                try:
                    while conn.recv(1 << 20):
                        pass
                except OSError:
                    pass
                conn.close()
                return
            body = reader.read(length) if length else b""
            if key == "trunc":
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 1000\r\n\r\n" + b"x" * 446)
                conn.close()
                return
            if key == "sse-trunc":
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n")
                for i in range(6):
                    event = b'data: {"i":%d}\n\n' % i
                    conn.sendall(b"%X\r\n" % len(event) + event + b"\r\n")
                conn.close()
                return
            if key.endswith(":streamGenerateContent"):
                # 길이를 선언하고 모자라게 끊는 Gemini 스트림 — read1() 은 예외 없이 빈 바이트로 끝난다
                event = b'data: {"candidates":[]}\r\n\r\n'
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nContent-Length: 500\r\n\r\n" + event)
                conn.close()
                return
            if key.endswith(":generateContent"):
                # 변환(chat → Gemini)이 본문 전체를 기다리는 경로 — 모자라게 끊는다
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 500\r\n\r\n" + b'{"candidates":[')
                conn.close()
                return
            if key == "both":
                # 규칙 위반이지만 실제로 보이는 응답: chunked 와 틀린 Content-Length 를 함께 보낸다
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 999\r\nTransfer-Encoding: chunked\r\n\r\n"
                             b"A\r\n0123456789\r\n0\r\n\r\n")
                continue
            if key == "sse-ok":
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n")
                for i in range(3):
                    event = b'data: {"i":%d}\n\n' % i
                    conn.sendall(b"%X\r\n" % len(event) + event + b"\r\n")
                conn.sendall(b"0\r\n\r\n")
                continue
            if key == "short":
                data = b'{"ok":1}'
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n" % len(data) + data)
                time.sleep(0.5)   # 짧은 keep-alive 뒤 닫는 게이트웨이
                conn.close()
                return
            data = json.dumps({"ok": True, "body": body.decode("utf-8", "replace")}).encode()
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: %d\r\n\r\n" % len(data) + data)
    except OSError:
        pass
    finally:
        try:
            conn.close()
        except OSError:
            pass


def serve(listener: socket.socket) -> None:
    while True:
        try:
            conn, _ = listener.accept()
        except OSError:
            return
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


def request(port: int, method: str, path: str, body: bytes | None = None) -> tuple[int, bytes, str]:
    """(status, body, error) — 잘린 응답이면 error 에 예외 이름이 들어간다."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request(method, path, body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        try:
            return response.status, response.read(), ""
        except http.client.IncompleteRead as error:
            return response.status, error.partial, type(error).__name__
    finally:
        conn.close()


def main() -> int:
    up_port, proxy_port = free_port(), free_port()
    listener = socket.socket()
    listener.bind(("127.0.0.1", up_port))
    listener.listen(64)
    threading.Thread(target=serve, args=(listener,), daemon=True).start()

    work = Path(tempfile.mkdtemp(prefix="pgpt-proxy-faults-"))
    shutil.copy(ROOT / "opus5_proxy.py", work / "opus5_proxy.py")
    env = dict(os.environ, PGPT_PROXY_UPSTREAM=f"http://127.0.0.1:{up_port}", PGPT_PROXY_PORT=str(proxy_port))
    proc = subprocess.Popen([sys.executable, str(work / "opus5_proxy.py")], env=env)
    try:
        for _ in range(50):
            try:
                health = json.loads(request(proxy_port, "GET", "/health")[1])
                break
            except OSError:
                time.sleep(0.1)
        else:
            check(False, "프록시가 뜨지 않았습니다")
            return 1
        check(health.get("pid") == proc.pid, "/health 가 자기 pid 를 알린다")

        base = "/gpgpta01-gpt"
        status, _, error = request(proxy_port, "GET", f"{base}/trunc")
        check(error == "IncompleteRead", f"길이보다 짧게 끊긴 응답은 잘린 것으로 받는다 ({status} {error or '정상 종료'})")
        status, _, error = request(proxy_port, "GET", f"{base}/sse-trunc")
        check(error == "IncompleteRead", f"도중에 끊긴 스트림은 잘린 것으로 받는다 ({status} {error or '정상 종료'})")
        status, _, error = request(proxy_port, "POST", f"{base}/v1beta/models/gemini-3.5-flash:streamGenerateContent?alt=sse", b"{}")
        check(error == "IncompleteRead", f"길이를 선언한 Gemini 스트림이 모자라게 끝나도 잘린 것으로 받는다 ({status} {error or '정상 종료'})")
        chat = b'{"model":"gemini-3.5-flash","messages":[{"role":"user","content":"hi"}]}'
        status, _, _ = request(proxy_port, "POST", f"{base}/v1/chat/completions", chat)
        check(status == 502, f"Gemini 변환 중 업스트림이 끊기면 잘린 답을 만들지 않고 502 ({status})")
        status, data, error = request(proxy_port, "GET", f"{base}/both")
        check(status == 200 and not error and data == b"0123456789", f"chunked 와 틀린 길이를 함께 보낸 응답도 온전히 넘긴다 ({status} {data!r} {error})")
        status, data, error = request(proxy_port, "GET", f"{base}/sse-ok")
        check(status == 200 and not error and data.count(b"data:") == 3, "끝까지 온 스트림은 그대로")

        status, data, _ = request(proxy_port, "POST", f"{base}/big413", b"x" * (8 * 1024 * 1024))
        check(status == 413 and COUNT.get("big413") == 1, f"본문을 다 받기 전의 413 은 그대로, 다시 보내지 않는다 ({status}, {COUNT.get('big413')}번)")

        threads = [threading.Thread(target=request, args=(proxy_port, "POST", f"{base}/short", b"{}")) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        time.sleep(1.0)
        status, _, _ = request(proxy_port, "POST", f"{base}/short", b"{}")
        check(status == 200, f"풀의 연결이 여럿 죽어 있어도 새 연결로 성공한다 ({status})")

        lone = b'{"model":"claude-opus-5","messages":[{"role":"user","content":"a\\ud83d b"}]}'
        status, data, _ = request(proxy_port, "POST", f"{base}/v1/messages", lone)
        check(status == 200 and b"ud83d" in data, f"짝 없는 surrogate 가 든 요청도 중계한다 ({status})")

        for bad in (f"{base}/../other", f"{base}/%2e%2e/other"):
            status, _, _ = request(proxy_port, "GET", bad)
            check(status == 403, f"점 세그먼트 경로는 막는다: {bad} ({status})")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        listener.close()
        shutil.rmtree(work, ignore_errors=True)

    print()
    print("전체 통과" if FAILURES == 0 else f"{FAILURES} 건 실패")
    return 0 if FAILURES == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
