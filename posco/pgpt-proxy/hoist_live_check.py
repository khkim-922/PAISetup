"""끝까지 재기 — 고친 프록시를 **거쳐** 보내면 `Read` 꼴 그림이 보이나 (claude-config #76).

앞선 것들과 재는 자리가 다르다:
  · `hoist_check.py`        — 함수가 본문 모양을 옳게 바꾸나 (망 없음 · 모양만)
  · `image_lane_probe.py`   — 게이트웨이가 어느 자리의 그림을 보나 (직결 · 자리 고름)
  · `image_tail_probe.py`   — `tool_result` 가 **마지막**일 때 어디에 두면 보나
  · 이 파일                 — **둘을 이어 붙인 것이 실제로 도나** (프록시 너머 · 눈가림)

같은 본문을 **직결**과 **프록시 너머**로 보낸다. 직결은 못 봐야 맞고(대조군), 프록시 너머는
봐야 맞다 — 둘 다 서야 「프록시가 고쳤다」가 참이다. 한쪽만 재면 프록시가 아무것도 안 하는데
게이트웨이가 마음을 바꾼 판과 안 갈린다.

    PGPT_PROXY_PORT=18907 python -X utf8 opus5_proxy.py &
    python -X utf8 hoist_live_check.py 18907

⚠ 눈가림이다 — 정답은 곁 파일에만 적고 화면에 안 찍는다.
⚠ 본문은 **`Read` 의 실제 꼴**이다: `tool_result` 가 마지막 메시지이고 그 안에 [text, image].
"""
from __future__ import annotations

import base64
import json
import os
import random
import struct
import sys
import urllib.error
import urllib.request
import zlib

W = H = 320
SHAPES = ("왼쪽 절반", "오른쪽 아래 사분면", "가운데 가로 띠", "대각선 띠")
COLORS = {"빨강": (220, 30, 30), "파랑": (30, 60, 220), "초록": (30, 170, 60), "노랑": (240, 200, 20)}
ASK = ("이 그림에서 ① 칠한 색과 ② 칠한 자리(왼쪽 절반 · 오른쪽 아래 사분면 · "
       "가운데 가로 띠 · 대각선 띠 중 하나)를 대라. 딴말 없이 「색 · 자리」 꼴로.")
VIEW = {"name": "view", "description": "그림을 돌려준다",
        "input_schema": {"type": "object", "properties": {}, "required": []}}


def bake() -> tuple[bytes, str]:
    shape = random.choice(SHAPES)
    name = random.choice(list(COLORS))
    color, bg = COLORS[name], (250, 250, 250)
    rows = []
    for y in range(H):
        row = bytearray(b"\x00")
        for x in range(W):
            if shape == "왼쪽 절반":
                hit = x < W // 2
            elif shape == "오른쪽 아래 사분면":
                hit = x >= W // 2 and y >= H // 2
            elif shape == "가운데 가로 띠":
                hit = H // 3 <= y < 2 * H // 3
            else:
                hit = abs(x - y) < 40
            row += bytes(color if hit else bg)
        rows.append(bytes(row))

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))
    return png, "%s · %s" % (name, shape)


def read_shaped_body(b64: str, model: str) -> dict:
    """Claude Code 의 `Read` 가 만드는 꼴 — `tool_result` 가 마지막이고 그 안에 그림."""
    return {"model": model, "max_tokens": 128, "tools": [VIEW], "messages": [
        {"role": "user", "content": [{"type": "text", "text": "view 를 불러 그림을 받고 " + ASK}]},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "tu_1", "name": "view", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tu_1", "content": [
            {"type": "text", "text": "그림 1장"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}}]}]}]}


def call(base: str, body: dict, token: str) -> tuple[int, str]:
    req = urllib.request.Request(
        base.rstrip("/") + "/v1/messages", data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + token,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=150) as resp:
            data = json.load(resp)
        text = " ".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        return resp.status, text.strip()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")[:200]
    except Exception as error:  # noqa: BLE001 — 「못 쟀다」도 결과다
        return 0, "%s: %s" % (type(error).__name__, error)


def hoisted_count(base: str) -> int | None:
    try:
        with urllib.request.urlopen(base.rstrip("/").rsplit("/", 1)[0] + "/health", timeout=5) as resp:
            return json.load(resp).get("hoisted_images")
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else "18907"
    model = sys.argv[2] if len(sys.argv) > 2 else "claude-opus-5"
    direct = os.environ["ANTHROPIC_BASE_URL"].rstrip("/")          # 도는 옛 판 = 보정 없음
    route = direct.rsplit("/", 1)[-1]                              # gpgpta01-gpt
    patched = "http://127.0.0.1:%s/%s" % (port, route)
    token = os.environ["ANTHROPIC_AUTH_TOKEN"]

    png, answer = bake()
    b64 = base64.b64encode(png).decode()
    with open(os.path.join(os.environ.get("TEMP", "."), "live-answer.txt"), "w", encoding="utf-8") as f:
        f.write(answer)
    print("모델 %s · 그림 %d×%d · `Read` 꼴 본문 · 정답은 곁 파일에만" % (model, W, H))
    print()

    before = hoisted_count(patched)
    lanes = [("대조군 — 보정 없는 판 (못 봐야 맞다)", direct),
             ("고친 프록시 너머 (봐야 맞다)", patched)]
    said = {}
    for label, base in lanes:
        status, text = call(base, read_shaped_body(b64, model), token)
        said[label] = text
        print("%s\n   %s · 상태 %s\n   답: %s\n" % (label, base, status, text[:160]))
    after = hoisted_count(patched)
    print("프록시 계수 hoisted_images: %s → %s" % (before, after))

    # 판정 — 정답 글자가 답에 다 들었나로 본다(사람 눈 대신).
    color, shape = answer.split(" · ")
    saw_patched = color in said[lanes[1][0]] and shape in said[lanes[1][0]]
    saw_direct = color in said[lanes[0][0]] and shape in said[lanes[0][0]]
    print()
    print("정답: %s" % answer)
    bad = []
    if not saw_patched:
        bad.append("고친 프록시 너머에서 못 봤다 — 보정이 안 걸렸거나 자리가 틀렸다")
    if saw_direct:
        bad.append("대조군이 봤다 — 게이트웨이가 바뀌었거나 이 검사가 보정을 안 재고 있다")
    if before is not None and after is not None and after <= before:
        bad.append("hoisted_images 가 안 늘었다 — 프록시가 이 본문을 안 만졌다")
    if bad:
        print()
        print("어긋남 %d" % len(bad))
        for line in bad:
            print("  · %s" % line)
        return 1
    print("어긋남 0 — 보정이 실제로 그림을 열리는 자리로 옮겼다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
