"""그림 전달 검사 — 프록시가 tool_result 안의 그림을 user 턴 바깥으로 옮겨 상류로 넘기나 (v31 · 이슈 #144 · #146).

Read 도구로 PNG 를 읽으면 Claude Code 는 그림을 `tool_result` 안의 `image` 블록(base64)으로 싣는다. 게이트웨이는
user 턴에 바로 붙인 그림은 모델에 넘기지만 tool_result 안의 그림은 버린다(사내 실측). 그래서 프록시가 옮긴다.
가짜 게이트웨이와 프록시를 이 프로세스 안에 띄우고 **CLI 가 보내는 꼴 그대로** 보낸 뒤, 상류가 받은 본문을 잰다.
망도 회사 키도 안 쓴다.

    python -X utf8 posco/pgpt-proxy/Test-ProxyImages.py

⚠ **그림 바이트는 한 바이트도 안 바뀌어야 한다** — 자리만 옮긴다. tool_result 는 턴 앞에 그대로 남고 비지 않는다.
⚠ **PDF(`document`)는 안 옮긴다** — 게이트웨이가 자리와 상관없이 삼켜(결정 0165), tool_result 안에 바이트 그대로
  남고 「붙였다」는 표지도 계수도 안 생기는지 잰다. 같은 tool_result 의 그림은 그대로 옮겨져야 한다.
⚠ 본문을 고치는 갈래(모델 이름 복원 · 출력 상한 · 빈 글 조각 정리 · 끝 assistant 자르기 · user 턴 합치기)를 모두
  타게 짰다 — 고치는 갈래가 그림을 떨어뜨려도 여기서 걸린다.
⚠ 손잡이(PGPT_PROXY_HOIST_TOOL_IMAGES=0)를 끄면 tool_result 를 건드리지 않는 것도 잰다.
"""
from __future__ import annotations

import base64
import http.client
import importlib.util
import json
import random
import struct
import sys
import tempfile
import threading
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("proxy", ROOT / "opus5_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

SEEN: list[dict] = []
PATH = "/gpgpta01-gpt/v1/messages?beta=true"
# 옮기는 블록 — 결정 0165 의 계약이다. 프록시 모듈에서 읽지 않는다 — 읽으면 프록시가 틀려도 같이 틀려 초록이다.
HOISTED = ("image",)
MARKER_TAIL = "after this tool result]"  # tool_result 에 남는 「옮겼다」 표지의 끝


def png(width: int, height: int) -> bytes:
    """올바른 RGBA PNG — 이슈의 화면 캡처(32bpp)와 같은 꼴. 화면 캡처만큼 크도록 일부 줄을 잡음으로 채운다."""
    noise = random.Random(144)
    rows = b"".join(b"\x00" + (noise.randbytes(width * 4) if y % 24 == 0 else bytes(width * 4)) for y in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 1)) + chunk(b"IEND", b""))


class Gateway(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802 — http.server 의 이름
        length = int(self.headers.get("Content-Length", "0") or "0")
        SEEN.append(json.loads(self.rfile.read(length)))
        data = json.dumps({"id": "msg_1", "type": "message", "role": "assistant", "model": "claude-opus-5",
                           "content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn",
                           "usage": {"input_tokens": 1, "output_tokens": 1}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def image_block(data: bytes, media_type: str = "image/png") -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                         "data": base64.b64encode(data).decode("ascii")}}


def read_turn(model: str, blocks: list[dict], *, extra_user: list[dict] | None = None) -> dict:
    """Read 도구가 그림을 돌려준 다음 턴 — CLI 가 보내는 꼴(도구 선언 · tool_use · tool_result)."""
    return {
        "model": model, "max_tokens": 32000, "stream": False,
        "tools": [{"name": "Read", "description": "Read a file", "input_schema": {"type": "object"}}],
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "화면 캡처를 읽어 줘"}, {"type": "text", "text": " "}]},
            {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_1", "name": "Read",
                                               "input": {"file_path": "C:\\temp\\슬라이드 1, 캡처.png"}}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": blocks},
                                         *(extra_user or [])]},
        ],
    }


def post(port: int, payload: dict, *, chunked: bool = False) -> int:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    if chunked:
        conn.putrequest("POST", PATH)
        conn.putheader("Authorization", "Bearer test-key-xxxx")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Transfer-Encoding", "chunked")
        conn.endheaders()
        for start in range(0, len(body), 65536):
            part = body[start:start + 65536]
            conn.send(b"%x\r\n" % len(part) + part + b"\r\n")
        conn.send(b"0\r\n\r\n")
    else:
        conn.request("POST", PATH, body, {"Authorization": "Bearer test-key-xxxx", "Content-Type": "application/json"})
    response = conn.getresponse()
    response.read()
    conn.close()
    return response.status


def is_marker(item: dict) -> bool:
    return item.get("type") == "text" and str(item.get("text", "")).endswith(MARKER_TAIL)


def hoist_problem(sent: list, got: list) -> str:
    """상류가 받은 user 턴(got)이 보낸 턴(sent)을 옳게 옮긴 꼴인지. 옳으면 빈 글, 아니면 무엇이 틀렸는지.

    옮길 블록(HOISTED)만 tool_result 밖으로 나가고, 나머지(글 · PDF)는 같은 tool_result 안에 같은 차례 · 같은 바이트로
    남아야 한다. 표지는 옮긴 블록마다 하나이고 옮긴 블록의 종류를 단다.
    """
    results = [b for b in sent if b.get("type") == "tool_result"]
    media = [{k: v for k, v in item.items() if k != "cache_control"}      # 옮길 때 cache_control 은 뗀다(캐시 경계 4개 제한)
             for b in results if isinstance(b.get("content"), list)
             for item in b["content"] if item.get("type") in HOISTED]
    others = [b for b in sent if b.get("type") != "tool_result"]
    if got[:len(results)] and any(b.get("type") != "tool_result" for b in got[:len(results)]):
        return "tool_result 가 턴 앞에 없다"
    for want, have in zip(results, got):
        if have.get("tool_use_id") != want.get("tool_use_id"):
            return "tool_use_id 가 바뀌었다"
        inner = have.get("content")
        if isinstance(inner, list):
            if not inner:
                return "tool_result 가 비었다"
            if any(item.get("type") in HOISTED for item in inner):
                return "tool_result 안에 그림이 남았다"
            if [i for i in inner if not is_marker(i)] != [i for i in want["content"] if i.get("type") not in HOISTED]:
                return "tool_result 에 남을 블록(글 · PDF)이 빠지거나 바뀌었다"
            markers = [i["text"] for i in inner if is_marker(i)]
            if len(markers) != sum(i.get("type") in HOISTED for i in want["content"]) \
                    or not all(m.startswith(tuple(f"[{kind} " for kind in HOISTED)) for m in markers):
                return f"옮겼다는 표지가 옮긴 그림과 안 맞는다 — {markers}"
        elif inner != want.get("content"):
            return "tool_result 의 글이 바뀌었다"
    rest = got[len(results):]
    moved = [b for b in rest if b.get("type") in HOISTED]
    if moved[:len(media)] != media:
        return "옮긴 그림이 보낸 것과 다르거나 순서가 바뀌었다"
    if moved[len(media):] != [b for b in others if b.get("type") in HOISTED]:
        return "원래 바깥에 있던 그림이 바뀌었다"
    return ""


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

    big = image_block(png(1920, 1329))           # 이슈 표의 원본 크기 · 32bpp
    small = image_block(png(800, 554))
    jpeg = image_block(b"\xff\xd8\xff\xe0" + b"\x00" * 4096 + b"\xff\xd9", "image/jpeg")
    pdf = {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                           "data": base64.b64encode(b"%PDF-1.4\n%%EOF\n").decode("ascii")}}
    print(f"그림 본문: {len(big['source']['data']) / 1_000_000:.1f} MB(base64)")

    # (이름, 본문, chunked 로 보내나, 계약이 옮기는 수 — tool_result 안의 그림 수 · PDF 는 0)
    cases = [
        ("tool_result 안의 PNG(원본 크기)", read_turn("claude-opus-5", [big]), False, 1),
        ("tool_result 안의 PNG · chunked 본문", read_turn("claude-opus-5", [big]), True, 1),
        ("tool_result 안의 축소 PNG + 글", read_turn("claude-opus-5", [{"type": "text", "text": "slide 1"}, small]), False, 1),
        ("tool_result 안의 JPEG", read_turn("claude-opus-5", [jpeg]), False, 1),
        ("tool_result 안의 PDF document 는 제자리", read_turn("claude-opus-5", [pdf]), False, 0),
        ("tool_result 안의 PDF + PNG — 그림만 옮긴다", read_turn("claude-opus-5", [pdf, small]), False, 1),
        ("user 턴에 바로 붙인 PNG", read_turn("claude-opus-5", [{"type": "text", "text": "x"}], extra_user=[big]), False, 0),
        ("tool_result 그림 + 바깥 그림", read_turn("claude-opus-5", [small], extra_user=[big]), False, 1),
        ("대시 표기 모델(이름 복원 갈래)", read_turn("claude-opus-4-7", [big]), False, 1),
        ("스트리밍 요청(stream: true)", {**read_turn("claude-opus-5", [big]), "stream": True}, False, 1),
        ("cache_control 이 붙은 그림은 떼고 옮긴다", read_turn("claude-opus-5", [{**big, "cache_control": {"type": "ephemeral"}}]), False, 1),
    ]
    for name, payload, chunked, moves in cases:
        sent = payload["messages"][-1]["content"]
        before = proxy.stats()["hoisted_tool_images"]
        status = post(port, payload, chunked=chunked)
        counted = proxy.stats()["hoisted_tool_images"] - before
        got = SEEN[-1]["messages"][-1]["content"] if SEEN else []
        problem = f"HTTP {status}" if status != 200 else hoist_problem(sent, got)
        if not problem and counted != moves:
            problem = f"/health 의 옮긴 수가 {counted} — 계약은 {moves}"
        check(name, not problem, problem)

    # Screenshot(MCP) 꼴 — 그림 뒤에 [Image: source: …] 글이 붙는다. 글은 tool_result 에 남고 그림만 나와야 한다
    caption = {"type": "text", "text": "[Image: source: C:\\Users\\u\\tool-results\\mcp-windows-mcp-blob-1.png]"}
    payload = read_turn("claude-opus-5", [big, caption])
    sent = payload["messages"][-1]["content"]
    status = post(port, payload)
    got = SEEN[-1]["messages"][-1]["content"]
    problem = f"HTTP {status}" if status != 200 else hoist_problem(sent, got)
    check("MCP 화면 캡처 꼴(그림 + 경로 글)", not problem and caption in got[0]["content"], problem or got[0]["content"])

    # 도구 두 개를 한 턴에 부른 결과 — 그림은 두 tool_result 뒤에 원래 순서대로 모인다
    payload = read_turn("claude-opus-5", [big])
    payload["messages"][1]["content"].append({"type": "tool_use", "id": "toolu_2", "name": "Read", "input": {}})
    payload["messages"][2]["content"].insert(1, {"type": "tool_result", "tool_use_id": "toolu_2", "content": [small]})
    sent = payload["messages"][-1]["content"]
    status = post(port, payload)
    got = SEEN[-1]["messages"][-1]["content"]
    problem = f"HTTP {status}" if status != 200 else hoist_problem(sent, got)
    check("tool_result 두 개", not problem and [b["type"] for b in got][:2] == ["tool_result", "tool_result"], problem)

    # 그림이 없는 tool_result(글 · 문자열)는 손대지 않는다
    for inner in ("plain text result", [{"type": "text", "text": "line 1"}]):
        payload = read_turn("claude-opus-5", [{"type": "text", "text": "x"}])
        payload["messages"][-1]["content"][0]["content"] = inner
        sent = payload["messages"][-1]["content"]
        post(port, payload)
        check(f"그림 없는 tool_result 그대로({type(inner).__name__})", SEEN[-1]["messages"][-1]["content"] == sent)

    # 끝에 assistant 미리 채움이 붙어 잘리는 갈래도 그림은 옮겨져 가야 한다
    payload = read_turn("claude-opus-5", [big])
    sent = payload["messages"][-1]["content"]
    payload["messages"].append({"role": "assistant", "content": [{"type": "text", "text": "그림에는"}]})
    status = post(port, payload)
    got = SEEN[-1]["messages"]
    problem = f"HTTP {status}" if status != 200 else hoist_problem(sent, got[-1]["content"])
    check("끝 assistant 를 잘라도 그림 유지", not problem and got[-1]["role"] == "user", problem)

    # 연속된 user 턴을 하나로 합치는 갈래 — 두 번째 턴의 그림이 합쳐진 뒤에도 남아야 한다
    payload = read_turn("claude-opus-5", [big])
    payload["messages"].append({"role": "user", "content": [small]})
    status = post(port, payload)
    got = SEEN[-1]["messages"][-1]["content"]
    check("연속 user 턴 합치기에서 그림 유지", status == 200 and got[-1] == small and big in got
          and not any(i.get("type") == "image" for i in got[0]["content"]), f"HTTP {status}")

    # 손잡이를 끄면 tool_result 를 그대로 보낸다
    proxy.HOIST_TOOL_IMAGES = False
    payload = read_turn("claude-opus-5", [big])
    sent = payload["messages"][-1]["content"]
    status = post(port, payload)
    check("손잡이 끔(PGPT_PROXY_HOIST_TOOL_IMAGES=0) → 그대로", status == 200 and SEEN[-1]["messages"][-1]["content"] == sent)
    proxy.HOIST_TOOL_IMAGES = True

    for s in (server, gateway):
        s.shutdown()
        s.server_close()
    print("결과:", "모두 통과" if not failures else f"실패 {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
