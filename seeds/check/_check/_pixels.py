"""결정론 잡음 그림 — 검사 검체용.

접는 문과 갈래 판정은 그림의 속(머리 바이트)을 본다(atelier #170 · #194 · 아뜰리에 결정 0233) —
「이름만 그림」인 가짜 base64 는 옳게 안 접히고 안 실린다. 그래서 크기·접힘·실림을 재는 검체는
진짜 PNG 여야 하고, 이걸로 짓는다. **PIL 이 든다** — 없는 저장소는 이 부품을 안 받는다.

부르는 꼴 — `from _pixels import noise_png, noise_png_b64`. 내는 것 — PNG 바이트와 그 base64 글자.
부품이라 종료코드를 안 낸다.

- 결정론 — LCG 잡음이라 매 판·매 자리 같은 바이트다 (`random` 도 시각도 안 쓴다)
- 몸통이 산다 — 잡음이라 PNG 압축(zlib)이 못 줄여, 「큰 덩이」 검체가 된다(atelier #88)
- 크기(side)가 곧 신원이다 — IHDR 에 치수가 박혀 side 가 다르면 base64 머리 64자 안에서 갈린다
"""
import base64
import io

from PIL import Image


def noise_png(side=180):
    """진짜 PNG 바이트 — side×side RGB 결정론 잡음. 같은 side 면 늘 같은 바이트다."""
    x, out = 1, bytearray()
    for _ in range(side * side * 3):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        out.append((x >> 16) & 0xFF)
    buf = io.BytesIO()
    Image.frombytes("RGB", (side, side), bytes(out)).save(buf, "PNG")
    return buf.getvalue()


def noise_png_b64(side=180):
    """`noise_png(side)` 의 base64 글자(ASCII `str`)."""
    return base64.b64encode(noise_png(side)).decode()
