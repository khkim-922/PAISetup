"""그림의 꼴과 치수를 파일 머리에서 읽는다 — 의존성 0. 그림 문(홈 훅 `image-gate.py` · PIL 없이 돈다)과 그림을
받아 두는 손(격리 모드 `-I` 로 돌아 표준 라이브러리만 본다)이 **같은 읽기를 여기서 부른다.** 두 자리에 따로 적으면
한쪽만 새 꼴을 배우고, 그때 받아 둔 그림과 문이 재는 그림이 서로 다른 치수를 말한다.

부르는 꼴 — 이 폴더를 `sys.path` 에 얹고 `import _image_head`:

    _image_head.kind(data)            # 바이트 머리 → (꼴 이름, 확장자) 또는 None
    _image_head.size(data)            # 바이트 → (가로, 세로) 또는 None
    _image_head.size_of_file(path)    # 파일 → (가로, 세로) 또는 None — 머리만 읽는다

읽는 꼴 — PNG(IHDR) · GIF · JPEG(SOF) · WebP(VP8 · VP8L · VP8X). 모델이 그림으로 받는 꼴이 이 넷이다.
못 읽으면 None 이다 — 꼴이 아니거나, 머리가 잘렸거나, 파일을 못 열었다. 던지지 않는다. 부품이라 종료코드를 안 낸다.

⚠ **`size` 는 `kind` 를 먼저 묻지 않는다** — JPEG 은 `FF D8` 두 바이트로 들어가 표지를 따라간다. 꼴을 가리는 자리는
   `kind` 다(`FF D8 FF`).
⚠ **파일은 통째로 안 읽는다** — 머리 `HEAD_BYTES` 를 읽고, JPEG 은 조각 길이만큼 건너뛰며 표지만 읽는다. 훅이 Read 마다
   도는 자리라 그림 크기만큼 읽으면 안 된다. 표지가 안 서는 깨진 JPEG 만은 끝까지 훑는다(치수 없이 None).
"""
import io
import struct

HEAD_BYTES = 32     # PNG · GIF · WebP 의 치수가 다 드는 머리 길이 — WebP 가 가장 길다(RIFF 12 + 조각 머리 8 + 치수 칸)
WEBP_SIZE_END = 30  # WebP 세 갈래의 치수 칸이 끝나는 자리 — 이보다 짧은 머리는 잘린 것이다

PNG_HEAD = b'\x89PNG\r\n\x1a\n'
GIF_HEADS = (b'GIF87a', b'GIF89a')
JPEG_SOI = b'\xff\xd8'
# 꼴을 가리는 머리 · 꼴 이름 · 확장자. WebP 는 RIFF 머리 뒤를 봐야 해서 `kind` 가 따로 가린다
KINDS = ((PNG_HEAD, 'PNG', 'png'), (JPEG_SOI + b'\xff', 'JPEG', 'jpg')) + tuple((h, 'GIF', 'gif') for h in GIF_HEADS)
WEBP = ('WebP', 'webp')

# JPEG 표지 — 길이 칸 없이 홀로 서는 것(SOI · TEM · RST0–7)과 치수를 든 것(SOF: C0–CF 에서 DHT · JPG · DAC 를 뺀 것)
JPEG_BARE = frozenset([0xD8, 0x01]) | frozenset(range(0xD0, 0xD8))
JPEG_SOF = frozenset(range(0xC0, 0xD0)) - frozenset([0xC4, 0xC8, 0xCC])


def _is_webp(head):
    return head[:4] == b'RIFF' and head[8:12] == b'WEBP'


def kind(data):
    """바이트 머리 → (꼴 이름, 확장자). 읽는 꼴이 아니면 None."""
    for head, name, ext in KINDS:
        if data.startswith(head):
            return name, ext
    return WEBP if _is_webp(data) else None


def _webp_size(head):
    """WebP 머리 → (가로, 세로). 갈래는 첫 조각의 이름이 정한다 — 손실(`VP8 `) · 무손실(`VP8L`) · 확장(`VP8X`)."""
    if len(head) < WEBP_SIZE_END:
        return None
    chunk = head[12:16]
    if chunk == b'VP8 ':
        w, h = struct.unpack('<HH', head[26:30])
        return (w & 0x3FFF, h & 0x3FFF)
    if chunk == b'VP8L':
        b = head[21:25]
        return (1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | (b[1] >> 6)))
    if chunk == b'VP8X':
        return (1 + int.from_bytes(head[24:27], 'little'), 1 + int.from_bytes(head[27:30], 'little'))
    return None


def _jpeg_size(f):
    """SOI 뒤에 선 흐름에서 SOF 를 찾아 (가로, 세로). 표지 앞의 채움 바이트(`FF` 되풀이)와 홀로 서는 표지는 건너뛴다."""
    while True:
        b = f.read(1)
        if not b:
            return None
        if b != b'\xff':
            continue
        marker = f.read(1)
        while marker == b'\xff':
            marker = f.read(1)
        if not marker:
            return None
        m = marker[0]
        if m in JPEG_BARE:
            continue
        seg = f.read(2)
        if len(seg) < 2:
            return None
        if m in JPEG_SOF:
            h, w = struct.unpack('>xHH', f.read(5))
            return (w, h)
        f.seek(struct.unpack('>H', seg)[0] - 2, 1)


def _head_size(f):
    """머리에 적힌 치수 그대로 — 꼴이 아니면 None. 잘린 머리는 `struct.error` · `IndexError` 로 오른다."""
    head = f.read(HEAD_BYTES)
    if head.startswith(PNG_HEAD) and head[12:16] == b'IHDR':
        return struct.unpack('>II', head[16:24])
    if head[:6] in GIF_HEADS:
        return struct.unpack('<HH', head[6:10])
    if _is_webp(head):
        return _webp_size(head)
    if head[:2] == JPEG_SOI:
        f.seek(len(JPEG_SOI))
        return _jpeg_size(f)
    return None


def size_from(f):
    """자리를 옮길 수 있는 바이트 흐름(처음에 선 것) → (가로, 세로) 또는 None. 흐름이 내는 `OSError` 는 그대로 오른다.
    한 변이 0 이라고 적힌 머리는 못 읽은 것이다 — 그런 그림은 없고, 받는 쪽의 비율 셈이 0 으로 나누게 된다."""
    try:
        got = _head_size(f)
    except (struct.error, IndexError):   # 머리가 치수 칸 앞에서 잘렸다
        return None
    return got if got and all(got) else None


def size(data):
    """바이트(그림 전체나 그 앞머리) → (가로, 세로) 또는 None."""
    return size_from(io.BytesIO(data))


def size_of_file(path):
    """파일 → (가로, 세로) 또는 None. 머리만 읽는다 — 못 여는 파일도 None 이다."""
    try:
        with open(path, 'rb') as f:
            return size_from(f)
    except OSError:
        return None
