"""로컬 프록시가 게이트웨이의 비정상 응답을 올바르게 넘기는지 본다(v16).

게이트웨이를 흉내 내는 작은 서버를 띄우고, 복사한 프록시를 다른 포트에서 돌려 확인한다.

    python3 tests/Test-ProxyFaults.py

* 도중에 끊긴 응답은 클라이언트도 잘린 응답으로 받는다(전에는 정상 종료처럼 보였다)
* 본문을 다 보내기 전에 온 응답(413)은 그대로 넘기고, 다시 보내지 않는다
* 풀에 죽은 연결이 여럿 있어도 새 연결로 한 번 더 시도해 성공한다
* 짝 없는 surrogate 가 든 요청에도 응답한다
* ``..`` 경로는 막는다
* (v18) 상류 SSE 가 침묵하면 주석을 흘리고, 게이트웨이의 ``error`` 프레임은 세어 요청 번호와 함께 기록한다
* (v18) 하이쿠 모델 이름은 게이트웨이에 있는 소넷으로 바꿔 보낸다
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
# (v20) 모의 게이트웨이가 본 동시 가동 — 게이트가 큰 요청을 직렬로 보내는지 확인하는 데 쓴다
_OVERLAP = {"now": 0, "max": 0}
_OVERLAP_LOCK = threading.Lock()


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
            if key == "sse-slow":
                # 생각 구간처럼 조각 사이가 긴 스트림 — 프록시는 keepalive 주석으로 메운다(시험은 0.3초 간격으로 띄운다)
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n\r\n")
                for i in range(2):
                    time.sleep(0.8)
                    event = b'data: {"i":%d}\n\n' % i
                    conn.sendall(b"%X\r\n" % len(event) + event + b"\r\n")
                conn.sendall(b"0\r\n\r\n")
                continue
            if key == "sse-error":
                # 게이트웨이가 180초 시한에 끊을 때의 마지막 프레임(회사 실측 문구) + 요청 번호 머리
                frame = (b'event: error\ndata: {"type":"error","error":{"type":"api_error","message":'
                         b'"HTTP request execution did not complete before the specified timeout configuration: 180000 millis"}}\n\n')
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nTransfer-Encoding: chunked\r\n"
                             b"x-pgpt-request-id: req-test-1\r\n\r\n")
                conn.sendall(b"%X\r\n" % len(frame) + frame + b"\r\n0\r\n\r\n")
                continue
            if key == "exec-cut":
                # (v19) 회사 PC 실측 2026-10-02 의 다른 얼굴 — SSE 프레임이 아니라 HTTP 500 으로 온 절단.
                # 실제로는 180초 뒤에 오지만, 시험은 PGPT_PROXY_EXECUTION_LIMIT_SEC 를 낮춰 그 자리를 만든다.
                time.sleep(0.6)
                data = (b'{"type":"error","error":{"type":"api_error","message":'
                        b'"\xeb\x82\xb4\xeb\xb6\x80 \xec\x84\x9c\xeb\xb2\x84 \xec\x98\xa4\xeb\xa3\x98: '
                        b'HTTP request execution did not complete before the specified timeout '
                        b'configuration: 180000 millis"}}')
                conn.sendall(b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n"
                             b"x-pgpt-request-id: req-cut-1\r\nContent-Length: %d\r\n\r\n" % len(data) + data)
                continue
            if key == "slow500":
                # 같은 500 이지만 시한과 무관하게 빠르게 진 판 — 절단으로 세지 않아야 한다
                data = b'{"type":"error","error":{"message":"bad request"}}'
                conn.sendall(b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n"
                             b"Content-Length: %d\r\n\r\n" % len(data) + data)
                continue
            if key == "short":
                data = b'{"ok":1}'
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n" % len(data) + data)
                time.sleep(0.5)   # 짧은 keep-alive 뒤 닫는 게이트웨이
                conn.close()
                return
            # (v20) 그 밖의 경로는 본문을 되울린다. 겹침을 세어 게이트가 큰 요청을 직렬로 보내는지 본다 —
            # 큰 본문에만 잠깐 머물러 겹칠 틈을 만든다(게이트웨이의 180초 시한을 흉내 내지는 않는다).
            with _OVERLAP_LOCK:
                _OVERLAP["now"] += 1
                _OVERLAP["max"] = max(_OVERLAP["max"], _OVERLAP["now"])
            try:
                if len(body) >= 4096:
                    time.sleep(0.6)
                data = json.dumps({"ok": True, "body": body.decode("utf-8", "replace")}).encode()
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: %d\r\n\r\n" % len(data) + data)
            finally:
                with _OVERLAP_LOCK:
                    _OVERLAP["now"] -= 1
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
    # 회사 PC 의 콘솔은 cp949 다 — 한글은 되지만 em dash 같은 글자에서 print 가 터진다. 그러면 뒤의
    # 검사가 아예 돌지 않아 결과를 못 본다. 못 적는 글자는 물음표로 바꿔 끝까지 돌린다.
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, OSError):
        pass

    up_port, proxy_port = free_port(), free_port()
    listener = socket.socket()
    listener.bind(("127.0.0.1", up_port))
    listener.listen(64)
    threading.Thread(target=serve, args=(listener,), daemon=True).start()

    work = Path(tempfile.mkdtemp(prefix="pgpt-proxy-faults-"))
    shutil.copy(ROOT / "opus5_proxy.py", work / "opus5_proxy.py")
    env = dict(os.environ, PGPT_PROXY_UPSTREAM=f"http://127.0.0.1:{up_port}", PGPT_PROXY_PORT=str(proxy_port),
               PGPT_PROXY_KEEPALIVE_SEC="0.3",
               # (v19) 180초를 기다릴 수 없어 시한을 0.5초로 줄여 절단 자리를 만든다. 폭은 0.2초.
               PGPT_PROXY_EXECUTION_LIMIT_SEC="0.5", PGPT_PROXY_EXECUTION_LIMIT_MARGIN_SEC="0.2",
               # (v20) 200KB 짜리 본문을 시험마다 만들지 않도록 큰 요청 임계를 4KB 로 낮춘다
               PGPT_PROXY_HEAVY_BYTES="4096", PGPT_PROXY_HEAVY_CONCURRENCY="1",
               PGPT_PROXY_HEAVY_QUEUE_TIMEOUT_SEC="30")
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

        status, data, error = request(proxy_port, "GET", f"{base}/sse-slow")
        keepalives = data.count(b": keepalive")
        check(status == 200 and not error and data.count(b"data:") == 2 and keepalives >= 2,
              f"상류가 침묵하면 주석을 흘리고 조각은 그대로 넘긴다 ({keepalives} keepalive, {status} {error or '정상 종료'})")
        status, data, error = request(proxy_port, "GET", f"{base}/sse-error")
        health = json.loads(request(proxy_port, "GET", "/health")[1])
        check(status == 200 and not error and b"180000 millis" in data
              and health.get("stream_errors") == 1 and health.get("keepalives", 0) >= 2,
              f"게이트웨이 error 프레임은 그대로 넘기고 센다 (stream_errors={health.get('stream_errors')}, keepalives={health.get('keepalives')})")
        log_text = (work / "proxy.log").read_text(encoding="utf-8", errors="replace")
        check("stream error after" in log_text and "gw=req-test-1" in log_text,
              "스트림 오류 로그에 경과 시간과 게이트웨이 요청 번호가 붙는다")

        # (v19) SSE 프레임이 아니라 HTTP 500 으로 오는 절단 — v18 의 stream_errors 는 이것을 놓쳤다
        before = json.loads(request(proxy_port, "GET", "/health")[1])
        status, data, _ = request(proxy_port, "POST", f"{base}/exec-cut", b"{}")
        after = json.loads(request(proxy_port, "GET", "/health")[1])
        check(status == 500 and after.get("execution_cuts") == before.get("execution_cuts", 0) + 1,
              f"시한 근방의 HTTP 500 은 실행 절단으로 센다 ({status}, execution_cuts={after.get('execution_cuts')})")
        check(after.get("stream_errors") == before.get("stream_errors"),
              f"그 판은 stream_errors 로는 세지 않는다 (겹쳐 세면 빈도가 틀린다) ({after.get('stream_errors')})")
        log_text = (work / "proxy.log").read_text(encoding="utf-8", errors="replace")
        check("execution cut" in log_text and "gw=req-cut-1" in log_text,
              "절단 로그에 경과 시간과 게이트웨이 요청 번호가 붙는다 (운영팀 문의 근거)")

        # 시한과 무관한 500 은 절단이 아니다 — 이것까지 세면 근거가 부풀려진다
        before = json.loads(request(proxy_port, "GET", "/health")[1])
        status, _, _ = request(proxy_port, "POST", f"{base}/slow500", b"{}")
        after = json.loads(request(proxy_port, "GET", "/health")[1])
        check(status == 500 and after.get("execution_cuts") == before.get("execution_cuts"),
              f"시한 밖의 HTTP 500 은 절단으로 세지 않는다 ({status}, execution_cuts={after.get('execution_cuts')})")
        haiku = b'{"model":"claude-haiku-4-5-20251001","messages":[{"role":"user","content":"hi"}]}'
        status, data, _ = request(proxy_port, "POST", f"{base}/v1/messages", haiku)
        check(status == 200 and b"claude-sonnet-4.6" in data and b"haiku" not in data,
              f"하이쿠는 게이트웨이에 없어 소넷으로 바꿔 보낸다 ({status})")

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

        # (v20) 큰 요청(압축)의 직렬화 게이트. 회사 PC 에서 탭 네 개가 동시에 압축하자 모두 180초에 잘렸다.
        # 시험은 임계를 4KB 로 낮춰(PGPT_PROXY_HEAVY_BYTES) 큰 요청 자리를 만든다.
        def post(path: str, payload: bytes) -> None:
            request(proxy_port, "POST", path, payload)

        big = b'{"model":"claude-opus-5","pad":"' + b"x" * 8192 + b'","messages":[]}'
        with _OVERLAP_LOCK:
            _OVERLAP["max"] = 0
        before = json.loads(request(proxy_port, "GET", "/health")[1])
        threads = [threading.Thread(target=post, args=(f"{base}/v1/messages", big)) for _ in range(4)]
        started = time.monotonic()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        elapsed = time.monotonic() - started
        after = json.loads(request(proxy_port, "GET", "/health")[1])
        with _OVERLAP_LOCK:
            peak = _OVERLAP["max"]
        check(peak == 1, f"큰 요청 4건이 동시에 와도 게이트웨이는 한 번에 하나만 본다 (겹침 최대 {peak})")
        # 한 판 0.6초 × 4 = 2.4초 — 직렬이면 그만큼 걸린다(병렬이면 1초 안)
        check(elapsed >= 2.0, f"그만큼 차례를 기다린다 ({elapsed:.1f}초)")
        check(after.get("heavy_serialized", 0) - before.get("heavy_serialized", 0) == 4,
              f"게이트를 탄 수를 센다 (heavy_serialized={after.get('heavy_serialized')})")
        check(after.get("heavy_active") == 0 and after.get("heavy_waiting") == 0,
              f"다 끝나면 게이트는 비어 있다 (active={after.get('heavy_active')}, waiting={after.get('heavy_waiting')})")
        log_text = (work / "proxy.log").read_text(encoding="utf-8", errors="replace")
        check("heavy gate" in log_text and "waited=" in log_text,
              "기다린 요청은 기다린 시간을 로그에 남긴다")

        # 작은 호출은 게이트를 타지 않는다 — 압축 뒤에 줄서면 곁 호출(서브에이전트 · 요약)이 더 느려진다
        before = json.loads(request(proxy_port, "GET", "/health")[1])
        threads = [threading.Thread(target=post, args=(f"{base}/v1/messages", b'{"model":"claude-opus-5","messages":[]}')) for _ in range(4)]
        started = time.monotonic()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        elapsed = time.monotonic() - started
        after = json.loads(request(proxy_port, "GET", "/health")[1])
        check(elapsed < 2.0, f"작은 호출 4건은 차례를 기다리지 않는다 ({elapsed:.1f}초 — 직렬이면 2.4초)")
        check(after.get("heavy_serialized") == before.get("heavy_serialized"),
              "작은 호출은 게이트 수에 들지 않는다")

        # 큰 조회(/v1/models 류)는 생성 호출이 아니라 게이트를 타지 않는다
        before = json.loads(request(proxy_port, "GET", "/health")[1])
        request(proxy_port, "POST", f"{base}/v1/models", big)
        after = json.loads(request(proxy_port, "GET", "/health")[1])
        check(after.get("heavy_serialized") == before.get("heavy_serialized"),
              "생성 호출이 아닌 큰 요청은 게이트를 타지 않는다")

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
