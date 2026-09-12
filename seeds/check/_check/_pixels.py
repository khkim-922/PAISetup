"""결정론 잡음 그림 — 검사 검체용.

이 자가 난 자리는 아뜰리에다 — 접는 문과 갈래 판정이 **속(머리 바이트)을 보게 된 뒤**(atelier #170 ·
#194 · 결정 0233)로 「이름만 그림」인 가짜 base64 는 옳게 안 접히고 안 실린다 — 그 전제
위에 서 있던 검체들이 한꺼번에 자격을 잃었다(실측 2026-08-30: 검사 하나 4빨강 · 하나 크래시).
크기·접힘·실림을 재는 검체는 이걸로 짓는다. **PIL 이 든다** — 없는 저장소는 이 부품을 안 받는다.

- **결정론** — LCG 잡음이라 매 판·매 자리 같은 바이트다 (`Date`·`random` 없음)
- **몸통이 산다** — 잡음이라 PNG 압축(zlib)이 못 줄여, 「큰 덩이」 검체가 된다(atelier #88)
- **크기(side)가 곧 신원이다** — IHDR 에 치수가 박혀 side 가 다르면 머리 64자부터 다르다
"""
import base64
import io

from PIL import Image


def noise_png(side=180):
    """진짜 PNG 바이트 — side×side RGB 결정론 잡음."""
    x, out = 1, bytearray()
    for _ in range(side * side * 3):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        out.append((x >> 16) & 0xFF)
    buf = io.BytesIO()
    Image.frombytes("RGB", (side, side), bytes(out)).save(buf, "PNG")
    return buf.getvalue()


def noise_png_b64(side=180):
    return base64.b64encode(noise_png(side)).decode()
