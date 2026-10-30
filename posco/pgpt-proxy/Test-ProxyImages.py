"""그림 전달 검사 — 프록시가 tool_result 안의 그림을 user 턴 바깥으로 옮겨 상류로 넘기나 (v31 · 이슈 #144 · #146).

Read 도구로 PNG 를 읽으면 Claude Code 는 그림을 `tool_result` 안의 `image` 블록(base64)으로 싣는다. 게이트웨이는
user 턴에 바로 붙인 그림은 모델에 넘기지만 tool_result 안의 그림은 버린다(사내 실측). 그래서 프록시가 옮긴다.
가짜 게이트웨이와 프록시를 이 프로세스 안에 띄우고 **CLI 가 보내는 꼴 그대로** 보낸 뒤, 상류가 받은 본문을 잰다.
망도 회사 키도 안 쓴다.

    python -X utf8 posco/pgpt-proxy/Test-ProxyImages.py

⚠ **그림 바이트는 한 바이트도 안 바뀌어야 한다** — 자리만 옮긴다. tool_result 는 턴 앞에 그대로 남고 비지 않는다.
⚠ **PDF(`document`)는 안 옮긴다** — 게이트웨이가 자리와 상관없이 삼켜(결정 0165), 같은 자리에서 프록시의 안내 글
  (`_document_note` 가 짓는 꼴)로 바뀌고 「붙였다」는 표지도 옮긴 수도 안 생기는지 잰다. 같은 tool_result 의 그림은 그대로 옮겨져야
  한다. 안내 글 손잡이(PGPT_PROXY_DOCUMENT_NOTE=0)를 끄면 PDF 가 바이트 그대로 남는 것도 잰다.
⚠ 본문을 고치는 갈래(모델 이름 복원 · 출력 상한 · 빈 글 조각 정리 · 끝 assistant 자르기 · user 턴 합치기)를 모두
  타게 짰다 — 고치는 갈래가 그림을 떨어뜨려도 여기서 걸린다.
⚠ 손잡이(PGPT_PROXY_HOIST_TOOL_IMAGES=0)를 끄면 tool_result 를 건드리지 않는 것도 잰다.
⚠ 옮긴 묶음은 캐시 표식 사이에 서야 한다 — 그림 한 장이 밖에서는 두 칸이라, 그림 많은 턴은 앞 요청의 저장 지점이 캐시가 찾는
  20 칸 밖으로 밀린다(결정 0175). 그 칸들은 Claude Code 2.1.304 가 실제로 보낸 표식 배치를 본뜬 꼴로 칸 수를 센다.
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


def post(port: int, payload: dict) -> int:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
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

    def stays(item: dict) -> dict:
        # PDF 는 제자리에서 안내 글로 바뀐다 — 기대값은 프록시가 짓는 꼴에서 끌어온다
        return proxy._document_note(item) if proxy.DOCUMENT_NOTE and item.get("type") == "document" else item
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
            if [i for i in inner if not is_marker(i)] != [stays(i) for i in want["content"] if i.get("type") not in HOISTED]:
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


def claude_code_turn(images: list[dict], mark: dict, *, system_mark: dict | None = None) -> dict:
    """Claude Code 2.1.304 가 그림 여러 장을 한 턴에 Read 한 다음 요청의 꼴 — 2026-10-20 가짜 게이트웨이로 잰 배치를 본떴다.

    표식 셋: system 블록 셋 가운데 뒤 둘 · 끝의 대화 중간 system 메시지(그 턴의 알림). 첫 user 뒤에도 표식 없는 system
    메시지가 선다. 프록시는 system 메시지를 앞 user 에 합치므로 끝 표식이 옮긴 그림 묶음 **뒤**에 선다.
    """
    ids = [f"toolu_p{n:02d}" for n in range(len(images))]
    head = system_mark or mark
    return {
        "model": "claude-opus-5", "max_tokens": 64000, "stream": False,
        "system": [{"type": "text", "text": "billing"}, {"type": "text", "text": "You are Claude Code.", "cache_control": head},
                   {"type": "text", "text": "# Doing tasks", "cache_control": head}],
        "tools": [{"name": "Read", "description": "Read a file", "input_schema": {"type": "object"}}],
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "<system-reminder>ctx</system-reminder>"},
                                         {"type": "text", "text": "슬라이드 그림들을 읽어 줘"}]},
            {"role": "system", "content": "# Environment"},
            {"role": "assistant", "content": [{"type": "text", "text": "그림을 연다."},
                                              *[{"type": "tool_use", "id": i, "name": "Read", "input": {"file_path": f"C:/t/p{n}.png"}}
                                                for n, i in enumerate(ids)]]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": i, "content": [image]}
                                         for i, image in zip(ids, images)]},
            {"role": "system", "content": [{"type": "text", "text": "<total_tokens>9</total_tokens>", "cache_control": mark}]},
        ],
    }


# 프롬프트 캐시는 표식에서 뒤로 20 칸까지만 앞 요청의 저장 지점을 찾는다(Anthropic · Bedrock 문서). 잇단 tool_use · tool_result 를
# 한 칸으로 치는 것은 Anthropic 이 Claude API 에만 적었고, Bedrock 에서는 블록마다 세더라는 남의 실측이 있다(결정 0175) — 그래서
# 칸 수는 두 셈법으로 다 잰다.
LOOKBACK = 20


def lookback_gap(messages: list, saved_block: int = -1, *, collapse: bool = True) -> int | None:
    """앞 요청의 저장 지점에서 이번 마지막 user 메시지의 가장 가까운 표식까지 칸 수. 표식이 없으면 None.

    앞 요청의 저장 지점은 끝에서 둘째 user 메시지의 `saved_block` 번째 블록 — 앞 요청이 그 메시지에 단 마지막 표식 자리다.
    그 표식은 다음 요청에는 실려 오지 않으니 부르는 쪽이 댄다. 기본은 마지막 블록(Claude Code 가 매 요청 마지막 메시지의 마지막
    블록에 표식을 단다). `collapse` 가 참이면 잇단 tool_use · tool_result 를 한 칸으로, 거짓이면 블록마다 센다. 캐시는 이 수가
    LOOKBACK 이하여야 앞 요청을 읽는다.
    """
    spots, pos = [], -1
    for index, message in enumerate(messages):
        previous = None
        for block in message["content"] if isinstance(message["content"], list) else [{"type": "text"}]:
            kind = block.get("type")
            if not (collapse and kind in ("tool_use", "tool_result") and kind == previous):
                pos += 1
            previous = kind
            spots.append((index, pos, "cache_control" in block))
    users = [i for i, m in enumerate(messages) if m["role"] == "user"]
    saved = [pos for index, pos, _ in spots if index == users[-2]]
    marks = [pos for index, pos, marked in spots if index == users[-1] and marked]
    if not saved or not marks:
        return None
    return min(pos - saved[saved_block] for pos in marks if pos >= saved[saved_block])


def mark_order(body: dict) -> list[str]:
    """요청이 캐시에 놓이는 차례(tools → system → messages)대로 표식의 TTL. 긴 TTL 이 짧은 것보다 앞에 서야 한다."""
    blocks = [*(body.get("tools") or []), *(body.get("system") or [])]
    for message in body["messages"]:
        for block in message["content"]:
            blocks.append(block)
            if block.get("type") == "tool_result" and isinstance(block.get("content"), list):
                blocks += block["content"]
    return [b["cache_control"].get("ttl", "5m") for b in blocks if "cache_control" in b]


def main() -> int:
    work = tempfile.TemporaryDirectory()
    proxy.LOG_PATH = Path(work.name) / "proxy.log"
    gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
    proxy._UPSTREAM = proxy.UpstreamTarget(f"http://127.0.0.1:{gateway.server_port}")
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

    # (이름, 본문, 계약이 옮기는 수 — tool_result 안의 그림 수 · PDF 는 0)
    cases = [
        ("tool_result 안의 PNG(원본 크기)", read_turn("claude-opus-5", [big]), 1),
        ("tool_result 안의 축소 PNG + 글", read_turn("claude-opus-5", [{"type": "text", "text": "slide 1"}, small]), 1),
        ("tool_result 안의 JPEG", read_turn("claude-opus-5", [jpeg]), 1),
        ("tool_result 안의 PDF document 는 제자리", read_turn("claude-opus-5", [pdf]), 0),
        ("tool_result 안의 PDF + PNG — 그림만 옮긴다", read_turn("claude-opus-5", [pdf, small]), 1),
        ("user 턴에 바로 붙인 PNG", read_turn("claude-opus-5", [{"type": "text", "text": "x"}], extra_user=[big]), 0),
        ("tool_result 그림 + 바깥 그림", read_turn("claude-opus-5", [small], extra_user=[big]), 1),
        ("대시 표기 모델(이름 복원 갈래)", read_turn("claude-opus-4-7", [big]), 1),
        ("스트리밍 요청(stream: true)", {**read_turn("claude-opus-5", [big]), "stream": True}, 1),
        ("cache_control 이 붙은 그림은 떼고 옮긴다", read_turn("claude-opus-5", [{**big, "cache_control": {"type": "ephemeral"}}]), 1),
    ]
    for name, payload, moves in cases:
        sent = payload["messages"][-1]["content"]
        before = proxy.stats()["hoisted_tool_images"]
        status = post(port, payload)
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

    # 옮긴 묶음의 캐시 표식 — 그림이 많아도 앞 요청의 저장 지점이 20 칸 안에 들어야 캐시를 읽는다(그림 한 장이 두 칸이다)
    one_hour, five_min = {"type": "ephemeral", "ttl": "1h"}, {"type": "ephemeral"}

    def marks_of(name: str) -> int:
        return proxy.stats().get(name, 0)

    for ttl_name, mark in (("1h", one_hour), ("5m", five_min)):
        payload = claude_code_turn([small] * 12, mark)
        before = marks_of("hoist_cache_marks")
        status = post(port, payload)
        body = SEEN[-1]
        got = body["messages"][-1]["content"]
        gap = lookback_gap(body["messages"])
        problem = f"HTTP {status}" if status != 200 else hoist_problem(payload["messages"][3]["content"], got)
        if not problem and (gap is None or gap > LOOKBACK):
            problem = f"앞 저장 지점까지 {gap} 칸 — 캐시가 읽는 창은 {LOOKBACK} 칸"
        if not problem and len(mark_order(body)) > 4:
            problem = f"표식이 {len(mark_order(body))} 개 — 한도 4"
        if not problem and (marks_of("hoist_cache_marks") - before != 1 or got[11].get("cache_control") != mark):
            problem = f"묶음 앞 tool_result 의 표식 {got[11].get('cache_control')} · 계수 {marks_of('hoist_cache_marks') - before}"
        # ⚠ 블록마다 세는 셈법에서는 도구 12개를 병렬로 부른 턴이 그림이 없어도 창 밖이다(tool_use 12 + tool_result 12) — 프록시
        #   몫 밖이라 이 칸은 묶어 세는 셈법으로만 잰다. 그림이 한 도구 결과에 몰린 꼴은 아래 PDF 칸이 두 셈법으로 다 잰다
        check(f"Claude Code 실물 꼴 · 그림 12장 · {ttl_name} — 묶음 앞에 같은 표식, 앞 저장 지점이 {LOOKBACK} 칸 안", not problem, problem)

    # Read 한 번이 PDF 20 쪽을 그림 20장으로 돌려준 턴 — 두 셈법 다 창 안이어야 한다
    payload = claude_code_turn([small], one_hour)
    payload["messages"][3]["content"][0]["content"] = [small] * 20
    post(port, payload)
    body = SEEN[-1]
    gaps = {rule: lookback_gap(body["messages"], collapse=rule) for rule in (True, False)}
    check(f"Read 한 번에 그림 20장(PDF 쪽) — 두 셈법 다 앞 저장 지점이 {LOOKBACK} 칸 안",
          all(gap is not None and gap <= LOOKBACK for gap in gaps.values()), f"묶어 세기 {gaps[True]} · 블록마다 {gaps[False]} 칸")

    payload = claude_code_turn([small] * 12, five_min, system_mark=one_hour)
    post(port, payload)
    order = mark_order(SEEN[-1])
    check("system 1h · 끝 5m — 더한 표식은 5m 라 긴 TTL 이 앞에 선다",
          order == ["1h", "1h", "5m", "5m"], order)

    # 표식이 tool_result 에 있는 꼴(대화 중간 system 메시지가 없는 클라이언트) — 묶음의 마지막 이름표에 달려 다음 턴이 읽는다.
    # 마지막 그림 뒤가 아니라 이름표 글 뒤다 — 게이트웨이가 옮기는 Converse cachePoint 의 그림 바로 뒤 자리는 문서에 없다(결정 0175)
    payload = claude_code_turn([small] * 12, five_min)
    payload["messages"].pop()
    payload["messages"][-1]["content"][-1]["cache_control"] = five_min
    post(port, payload)
    first = SEEN[-1]["messages"][-1]["content"]
    nxt = {**payload, "messages": [*SEEN[-1]["messages"],
                                   {"role": "assistant", "content": [{"type": "text", "text": "봤다"}]},
                                   {"role": "user", "content": [{"type": "text", "text": "다음", "cache_control": five_min}]}]}
    post(port, nxt)
    gap = lookback_gap(SEEN[-1]["messages"], max(i for i, b in enumerate(first) if "cache_control" in b))
    check(f"표식이 tool_result 에 있는 꼴 — 마지막 이름표에 달리고 다음 턴이 {LOOKBACK} 칸 안",
          first[-2].get("type") == "text" and first[-2].get("cache_control") == five_min
          and "cache_control" not in first[-1] and gap is not None and gap <= LOOKBACK,
          f"끝 둘째 블록 {first[-2].get('type')} {first[-2].get('cache_control')} · 다음 턴 {gap} 칸")

    # 표식이 이미 넷이면 안 단다(400 을 안 만든다) · 못 단 수를 센다
    payload = claude_code_turn([small] * 12, one_hour)
    payload["tools"][0]["cache_control"] = one_hour
    skipped = marks_of("hoist_cache_marks_skipped")
    status = post(port, payload)
    check("표식 넷이 찼으면 안 달고 못 단 수를 센다",
          status == 200 and len(mark_order(SEEN[-1])) == 4 and marks_of("hoist_cache_marks_skipped") - skipped == 1,
          f"HTTP {status} · 표식 {len(mark_order(SEEN[-1]))} · 못 단 수 {marks_of('hoist_cache_marks_skipped') - skipped}")

    # 끝에 표식이 없으면(클라이언트가 캐시를 안 쓴다) 안 단다
    payload = claude_code_turn([small] * 12, one_hour)
    payload["messages"][-1]["content"][0].pop("cache_control")
    before = marks_of("hoist_cache_marks")
    post(port, payload)
    check("마지막 메시지에 표식이 없으면 안 단다",
          len(mark_order(SEEN[-1])) == 2 and marks_of("hoist_cache_marks") == before, mark_order(SEEN[-1]))

    # 안내 글 손잡이를 끄면 PDF 는 바이트 그대로 남고, 켜면 계수가 오른다
    before = proxy.stats()["documents_noted"]
    post(port, read_turn("claude-opus-5", [pdf]))
    check("PDF 안내 글 계수(documents_noted)", proxy.stats()["documents_noted"] - before == 1,
          proxy.stats()["documents_noted"] - before)
    proxy.DOCUMENT_NOTE = False
    payload = read_turn("claude-opus-5", [pdf, small])
    sent = payload["messages"][-1]["content"]
    status = post(port, payload)
    problem = f"HTTP {status}" if status != 200 else hoist_problem(sent, SEEN[-1]["messages"][-1]["content"])
    check("안내 글 손잡이 끔(PGPT_PROXY_DOCUMENT_NOTE=0) → PDF 바이트 그대로", not problem, problem)
    proxy.DOCUMENT_NOTE = True

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
