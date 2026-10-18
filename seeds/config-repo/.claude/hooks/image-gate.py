"""그림 문 — 모델이 그림을 받기 **직전**에 치수를 재고, 안 고른 자리는 막는다 (PreToolUse 훅).

**왜 있나.** 그림의 값은 바이트가 아니라 가로×세로고(28×28 패치 하나가 토큰 하나), 상류 천장 위의
픽셀은 어차피 깎여 값이 0 이다. 규범이 「찍을 때 치수를 고른다」고 적어도 그 줄은 찍는 순간에
안 떠오른다 — 안 골라도 아무 데서도 안 걸리는 조용한 부재였다(claude-config #73). 이 문이 그
순간에 판단과 무관하게 건다.

세 길을 든다 — 픽셀이 **생기기 전**인가 **이미 있나**, 그리고 사람이 쥔 손이 무엇인가로 갈린다:

  · 도구 스크린샷·zoom (브라우저 · computer-use · 크롬 확장 · 그 배치들) — `scale` 을 안 적으면 **막는다.**
    적으면 1 이어도 통과 — 「골랐다」가 본이지 값이 본이 아니다. 화면을 재서 눈금에 맞는 scale 을
    곁에 댄다 (윈도우만 · 다른 판은 수만 댄다).
  · `Read` 로 그림 파일 열기 — 이미 있는 그림이라 막아도 픽셀은 안 아껴진다. 그래서
      긴 변 ≤ MAX_EDGE            조용히 통과
      MAX_EDGE < 긴 변, 천장 안    통과 + 곁말(치수 · 토큰 · 줄이면 얼마 · 줄이는 한 줄) — 판단은 모델
      천장 밖(상류가 깎는다)       막는다 — 값 0 인 픽셀이고 어느 판으로 깎일지 못 고른다
  · `Read` 로 PDF 열기 — Read 가 페이지마다 그림 한 장으로 그려 싣는다(poppler `pdftoppm`). 그 치수는 파일에 없고 Read 가
    그리는 dpi(`READ_PDF_DPI`)가 정하는데 사람은 그 값을 못 고른다 — 쥔 손은 `pages`(몇 장을 여나) 하나라 **막지 않고**
    곁말만 낸다. 판정은 장당이고(상류가 장마다 깎는다) 곁말은 합이다(창을 먹는 것은 합이다):
      장마다 긴 변 ≤ MAX_EDGE, 합 ≤ 조용한 선    조용히 통과
      그 밖                                     통과 + 곁말(장수 · 장당 치수와 토큰 · 합 · pages 로 줄이는 길)
      장당 천장 밖                              곁말에 「장마다 깎인다」를 더한다 — 그래도 안 막는다
      크기를 못 읽으면 장수만 · 장수도 못 읽으면 「못 쟀다」 — 막지 않는다
    조용한 선은 새 숫자가 아니다 — 긴 변 MAX_EDGE 정사각형의 패치 수(`patches((MAX_EDGE, MAX_EDGE))`), 곧 그림 한 장이면
    문이 조용히 넘기는 가장 큰 값이다. 작은 페이지도 여러 장이면 그 선을 넘어 사람이 모르는 채 창을 먹으므로 말한다.

⚠ **눈금은 씨앗 `_vision.py` 가 든다** — 여기 숫자를 안 적는다. 못 찾으면 **막지 않고** 「못 쟀다」
   한 줄만 남긴다: 문이 없는 것과 문이 잘못 잠긴 것은 다른 사고고, 뒤엣것이 더 비싸다.
⚠ **PIL 을 안 든다** — 치수는 파일 머리에서 읽는다(PNG · JPEG · GIF · WebP). 줄이는 손은 PIL 이
   드는데 그건 모델이 부르는 자리다(#72). PDF 도 표준 라이브러리로만 읽는다(`re` · `zlib`) — poppler 가 없는 PC 는
   Read 가 애초에 PDF 를 못 여니 문이 그것을 바랄 까닭이 없다.
⚠ **PDF 의 dpi 는 Read 구현이 든다** — 곁말은 「그 dpi 로 그린다면」으로 대고, 값의 출처와 다시 읽는 법은 `READ_PDF_DPI`
   곁이 든다. `pages` 없이 연 PDF 는 Claude Code 판과 모델에 따라 통째(document — 상류가 페이지를 그리고 그 해상도는
   모른다)로 가거나 거절되는데, 그때도 같은 dpi 로 센 짐작을 댄다.
⚠ **PDF 는 한 번 훑어 페이지 나무만 읽는다** — 객체를 파일 차례로 모으고(뒤 정의가 앞을 덮는다 · FlateDecode 객체
   묶음 `/ObjStm` 은 풀어서), trailer 의 `/Root` → 카탈로그의 `/Pages` 에서 `/Kids` 를 따라 장마다 `/MediaBox` 를 읽는다
   (Pages 에서 물려받기 · `/Rotate` 90·270 은 가로세로를 바꾼다 · 치수는 pdftoppm 처럼 `ceil(pt × dpi/72)`).
   안 읽는 꼴 — 암호로 감긴 스트림 · FlateDecode 밖 필터나 predictor 를 쓴 객체 묶음 · 끊긴 나무 · `/UserUnit` ·
   `/CropBox`(pdftoppm 은 기본으로 MediaBox 를 그린다) · `PDF_SCAN_BYTES` 를 넘는 파일. 그 꼴이면 크기 대신 장수만,
   장수도 없으면 「못 쟀다」를 댄다.
⚠ **1280 은 답이 아니다** — UI 글자는 그보다 커야 읽힌다. 곁말은 수를 대고 고르게 한다. 세부는 zoom.
⚠ **화면 전체 크기의 그림이면 한 줄을 더 붙인다** — 가려진 창은 안 찍힌다는 것과 창 손잡이로 찍는 손
   (`_see_window.ps1` · 눈금 곁)을 댄다. 까닭은 `whole_screen_note` 가 든다.

부르는 자리 — 홈 `~/.claude/settings.json` 의 PreToolUse. 앞에 셸 껍데기(`image-gate.sh` · 곁 파일)가
서서 stdin 에 그림 낌새(그림 · PDF 확장자 · screenshot · zoom)가 있을 때만 이 몸통을 띄운다 — 매 Read 마다 프로세스를
띄우지 않기 위해서다. 껍데기 글자와 matcher 는 그 파일 한 벌이고, 심는 손은 자리만 채운 한 줄을 심는다.
**심는 손은 갈 곳 표의 손(`tool-homes.py`) 하나다** — 껍데기 머리말(events · var · matcher)대로, Claude 를 고른
PC 에만, 이긴 층(설정 저장소가 있으면 개인 층)의 hooks 폴더를 가리키는 한 줄을 심는다(결정 0112).

시험 — `python -X utf8 scripts/image-gate-check.py` (양성·음성 표본을 먹여 판정을 문다).
**심긴 껍데기 층은 홈에 심긴 실물을 읽어 재므로 누가 심었든 그것을 잰다** — 나무에서 고친 껍데기는 나무 껍데기 층이 잰다.
"""
import json
import math
import os
import re
import struct
import sys
import zlib

IMG_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
PDF_EXT = ('.pdf',)       # 껍데기 글롭은 IMG_EXT 와 이것을 합친 집합과 짝이다
# Read 가 PDF 페이지를 그리는 해상도 — Claude Code 2.1.302 의 Read 는 `pdftoppm -jpeg -r 100` 을 부른다(설치본
# `@anthropic-ai/claude-code/bin/claude.exe` 안의 글자). 판이 바뀌면 그 파일에서 `pdftoppm` 곁의 `-r` 값을 다시 읽는다
READ_PDF_DPI = 100
PT_PER_INCH = 72          # PDF 의 길이 단위 — 1pt 는 1/72 인치
PDF_HEAD_WINDOW = 1024    # `%PDF-` 가 설 수 있는 자리 — 그 앞 군더더기를 이만큼까지 받는다(poppler 와 같은 너비)
PDF_SCAN_BYTES = 64 << 20  # PDF 를 훑는 한도 — 넘는 파일은 안 읽고 「못 쟀다」다. 매 Read 에 훅이 쓰는 시간 · 메모리의 선
SHOT_TOOLS = re.compile(r'^mcp__(Claude_Browser|claude-in-chrome)__(computer|browser_batch)$'
                        r'|^mcp__computer-use__(screenshot|zoom|computer_batch)$')


# ── 눈금 — 씨앗에서 읽는다 ─────────────────────────────────────────────────────────
def load_vision():
    """`_vision.py` 를 찾는 차례 — 시험이 주는 자리 · 홈 씨앗 · 붙은 저장소 · 이 파일 곁(진본)."""
    here = os.path.dirname(os.path.abspath(__file__))
    forced = os.environ.get('IMAGE_GATE_VISION_DIR')
    cands = [forced] if forced else [   # 시험이 자리를 주면 그 자리만 — 「없을 때」를 재려면 대체가 없어야 한다
        os.path.join(os.path.expanduser('~'), '.claude', 'seeds', 'check', '_check'),
        os.path.join(os.environ.get('CLAUDE_PROJECT_DIR', ''), 'seeds', 'check', '_check'),
        os.path.normpath(os.path.join(here, '..', '..', 'seeds', 'check', '_check')),
    ]
    for d in cands:
        if d and os.path.isfile(os.path.join(d, '_vision.py')):
            sys.path.insert(0, d)
            try:
                import _vision  # noqa: PLC0415
                return _vision, d
            except Exception:  # noqa: BLE001 — 눈금이 깨졌으면 없는 것과 같다
                return None, None
    return None, None


# ── 치수 — 파일 머리만 읽는다 ─────────────────────────────────────────────────────
def dims(path):
    """(가로, 세로) 또는 None. PNG · GIF · WebP(VP8/VP8L/VP8X) · JPEG(SOF)."""
    try:
        with open(path, 'rb') as f:
            head = f.read(32)
            if head.startswith(b'\x89PNG\r\n\x1a\n') and head[12:16] == b'IHDR':
                return struct.unpack('>II', head[16:24])
            if head[:6] in (b'GIF87a', b'GIF89a'):
                return struct.unpack('<HH', head[6:10])
            if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
                kind = head[12:16]
                if kind == b'VP8 ':
                    w, h = struct.unpack('<HH', head[26:30])
                    return (w & 0x3FFF, h & 0x3FFF)
                if kind == b'VP8L':
                    b = head[21:25]
                    w = 1 + (((b[1] & 0x3F) << 8) | b[0])
                    h = 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | (b[1] >> 6))
                    return (w, h)
                if kind == b'VP8X':
                    w = 1 + int.from_bytes(head[24:27], 'little')
                    h = 1 + int.from_bytes(head[27:30], 'little')
                    return (w, h)
                return None
            if head[:2] == b'\xff\xd8':
                f.seek(2)
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
                    if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                        continue
                    seg = f.read(2)
                    if len(seg) < 2:
                        return None
                    ln = struct.unpack('>H', seg)[0]
                    if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                        body = f.read(5)
                        h, w = struct.unpack('>xHH', body)
                        return (w, h)
                    f.seek(ln - 2, 1)
    except (OSError, struct.error, IndexError):
        return None
    return None


# ── PDF — 페이지 나무에서 장수와 크기를 읽는다(표준 라이브러리만) ─────────────────────────────
_PDF_OBJ = re.compile(rb'(\d+)\s+\d+\s+obj\b')
_PDF_STREAM = re.compile(rb'>>\s*stream(?:\r\n|\n|\r)')
_PDF_REF = re.compile(rb'(\d+)\s+\d+\s+R\b')
_PDF_INT = re.compile(rb'\d+')
_PDF_NUM = re.compile(rb'[-+]?(?:\d+\.?\d*|\.\d+)')
_PDF_ARRAY = re.compile(rb'\[([^\]]*)\]')
_PDF_ROOT = re.compile(rb'/Root\s+(\d+)\s+\d+\s+R\b')
_PDF_PAGES_REF = re.compile(rb'/Pages\s+(\d+)\s+\d+\s+R\b')
_PDF_KIDS = re.compile(rb'/Kids\s*\[([^\]]*)\]')
_PDF_TYPE_PAGE = re.compile(rb'/Type\s*/Page\b')
_PDF_TYPE_PAGES = re.compile(rb'/Type\s*/Pages\b')
_PDF_PARENT = re.compile(rb'/Parent\s+\d+\s+\d+\s+R\b')
_PDF_COUNT = re.compile(rb'/Count\s+(\d+)')
_PDF_BOX = re.compile(rb'/MediaBox\s*(?:\[([^\]]*)\]|(\d+)\s+\d+\s+R\b)')
_PDF_ROTATE = re.compile(rb'/Rotate\s+(-?\d+)')
_PDF_OBJSTM = re.compile(rb'/Type\s*/ObjStm\b')
_PDF_FILTER = re.compile(rb'/Filter\s*\[?\s*/(\w+)')
_PDF_N = re.compile(rb'/N\s+(\d+)')
_PDF_FIRST = re.compile(rb'/First\s+(\d+)')


def _pdf_objstm(head, raw):
    """객체 묶음 하나 → {번호: 사전 글자}. FlateDecode 거나 필터가 없을 때만 푼다 — 다른 필터 · predictor 면 빈 표."""
    n, first, filt = _PDF_N.search(head), _PDF_FIRST.search(head), _PDF_FILTER.search(head)
    if not n or not first:
        return {}
    if filt:
        if filt.group(1) != b'FlateDecode' or b'/DecodeParms' in head:
            return {}
        try:
            raw = zlib.decompressobj().decompress(raw, PDF_SCAN_BYTES)
        except zlib.error:
            return {}
    k = int(first.group(1))
    nums = [int(x) for x in _PDF_INT.findall(raw[:k])]
    pairs = list(zip(nums[0::2], nums[1::2]))[:int(n.group(1))]
    return {num: raw[k + off:(k + pairs[i + 1][1]) if i + 1 < len(pairs) else len(raw)]
            for i, (num, off) in enumerate(pairs)}


def pdf_objects(data):
    """{객체 번호: 사전 글자} — 파일 차례로 한 번 훑고 뒤 정의가 앞을 덮는다(증분 갱신은 뒤에 붙는다).

    객체마다 `endobj` 로 건너뛰어 스트림 몸 안은 다시 안 훑는다. 스트림 몸은 안 싣고, 객체 묶음(`/ObjStm`)만 그 자리에서
    풀어 안의 객체를 싣는다.
    """
    objs, pos = {}, 0
    while True:
        m = _PDF_OBJ.search(data, pos)
        if not m:
            return objs
        end = data.find(b'endobj', m.end())
        end = len(data) if end < 0 else end
        s = _PDF_STREAM.search(data, m.end(), end)
        head = data[m.end():s.start() + 2 if s else end]
        objs[int(m.group(1))] = head
        if s and _PDF_OBJSTM.search(head):
            objs.update(_pdf_objstm(head, data[s.end():end]))
        pos = end + len(b'endobj')


def _pdf_box(d, objs):
    """그 사전의 `/MediaBox` → (가로 pt, 세로 pt). 간접 참조면 따라간다. 없거나 넓이가 0 이면 None."""
    m = _PDF_BOX.search(d)
    if not m:
        return None
    arr = m.group(1)
    if arr is None:
        ref = _PDF_ARRAY.search(objs.get(int(m.group(2)), b''))
        arr = ref.group(1) if ref else b''
    nums = [float(x) for x in _PDF_NUM.findall(arr)]
    if len(nums) != 4:
        return None
    w, h = abs(nums[2] - nums[0]), abs(nums[3] - nums[1])
    return (w, h) if w > 0 and h > 0 else None


def _pdf_root(data, objs):
    """페이지 나무 뿌리의 객체 번호 — 마지막 trailer(또는 xref 스트림)의 `/Root` → 카탈로그의 `/Pages`.

    그 길이 끊기면 `/Parent` 없는 Pages 가운데 `/Count` 가 가장 큰 것. 없으면 None.
    """
    at = data.rfind(b'/Root')
    m = _PDF_ROOT.match(data, at) if at >= 0 else None
    cat = objs.get(int(m.group(1))) if m else None
    p = _PDF_PAGES_REF.search(cat) if cat else None
    if p and int(p.group(1)) in objs:
        return int(p.group(1))
    tops = []
    for num, d in objs.items():
        if _PDF_TYPE_PAGES.search(d) and not _PDF_PARENT.search(d):
            c = _PDF_COUNT.search(d)
            tops.append((int(c.group(1)) if c else -1, num))
    return max(tops)[1] if tops else None


def _pdf_walk(objs, root):
    """뿌리에서 `/Kids` 를 문서 차례로 따라 장마다 (가로 pt, 세로 pt) — 돌린 뒤 · MediaBox 가 없으면 그 장은 None.

    `/MediaBox` · `/Rotate` 는 Pages 에서 물려받는다. 나무가 끊기거나(없는 객체) 고리가 서면 None.
    """
    out, seen, stack = [], set(), [(root, None, 0)]
    while stack:
        num, box, rot = stack.pop()
        d = objs.get(num)
        if d is None or num in seen:
            return None
        seen.add(num)
        box = _pdf_box(d, objs) or box
        r = _PDF_ROTATE.search(d)
        rot = int(r.group(1)) if r else rot
        kids = _PDF_KIDS.search(d)
        if kids and not _PDF_TYPE_PAGE.search(d):
            stack.extend((int(k), box, rot) for k in reversed(_PDF_REF.findall(kids.group(1))))
        elif box is None:
            out.append(None)
        else:
            out.append((box[1], box[0]) if rot % 360 in (90, 270) else box)
    return out


def _pdf_count(objs, root):
    """뿌리의 `/Count` — 뿌리를 모르면 Pages 들 가운데 가장 큰 `/Count`. 없으면 None."""
    cands = [objs[root]] if root is not None else [d for d in objs.values() if _PDF_TYPE_PAGES.search(d)]
    counts = [int(c.group(1)) for c in (_PDF_COUNT.search(d) for d in cands) if c]
    return max(counts) if counts else None


def pdf_pages(path):
    """PDF 의 페이지 — (장수, 장마다 (가로 pt, 세로 pt) 또는 None 의 목록, 못 쟀을 때의 까닭).

    나무를 끝까지 따라가면 (장수, 목록, None) · 못 따라가도 `/Count` 가 서면 (장수, None, None) · 그것도 없으면
    (None, None, 까닭). 파일은 `PDF_SCAN_BYTES` 까지만 읽는다.
    """
    try:
        size = os.path.getsize(path)
        if size > PDF_SCAN_BYTES:
            return None, None, '%d MB 라 훑는 한도(%d MB) 밖이다' % (size >> 20, PDF_SCAN_BYTES >> 20)
        with open(path, 'rb') as f:
            data = f.read()
    except OSError:
        return None, None, '파일을 못 열었다'
    if b'%PDF-' not in data[:PDF_HEAD_WINDOW]:
        return None, None, 'PDF 머리(%PDF-)가 없다'
    objs = pdf_objects(data)
    root = _pdf_root(data, objs)
    sizes = _pdf_walk(objs, root) if root is not None else None
    if sizes:
        return len(sizes), sizes, None
    count = _pdf_count(objs, root)
    if count is None:
        return None, None, '페이지 나무를 못 찾았다'
    return count, None, None


_PAGES_ITEM = re.compile(r'^\s*(\d+)\s*(?:(-)\s*(\d*)\s*)?$')


def pdf_selection(arg, count):
    """Read 의 `pages` → (실릴 페이지 번호 목록 · 1 부터 · 겹침 없이, 못 푼 값 또는 None).

    값이 없으면 문서 전체. 꼴은 Claude Code 의 것 — 한 장 "3" · 범위 "1-5" · 끝이 빈 범위 "3-"(끝까지) — 에 쉼표로 이은
    목록을 더 받는다. 문서 밖 페이지는 버린다. 못 풀면 (문서 전체, 그 값).
    """
    whole = list(range(1, count + 1))
    if arg is None or str(arg).strip() == '':
        return whole, None
    sel = set()
    for item in str(arg).split(','):
        m = _PAGES_ITEM.match(item)
        if not m:
            return whole, str(arg)
        a = int(m.group(1))
        b = int(m.group(3)) if m.group(3) else (count if m.group(2) else a)
        if a < 1 or b < a:
            return whole, str(arg)
        sel.update(range(a, min(b, count) + 1))
    return sorted(sel), None


def pdf_px(size_pt):
    """(가로 pt, 세로 pt) → `READ_PDF_DPI` 로 그린 (가로 px, 세로 px). pdftoppm 처럼 올림한다 — `ceil(pt × (dpi/72))`."""
    k = READ_PDF_DPI / PT_PER_INCH
    return tuple(max(1, math.ceil(x * k)) for x in size_pt)


def pdf_gate(path, pages_arg, v):
    """Read 로 여는 PDF 의 판정 — 막지 않는다. 조용히 · 곁말(장수 · 장당 · 합) · 장수만 · 「못 쟀다」 가운데 하나를 낸다."""
    name = os.path.basename(path)
    count, sizes, why = pdf_pages(path)
    if count is None:
        return emit(context='그림 문 — %s 의 페이지를 못 읽어 안 쟀다(%s). Read 는 PDF 를 장마다 그림 한 장으로 '
                            '싣는다 — 몇 장 · 얼마인지는 스스로 본다' % (name, why))
    sel, bad = pdf_selection(pages_arg, count)
    if not sel:
        return 0   # 실릴 장이 없다 — 범위 밖은 Read 가 스스로 알린다
    if bad is not None:
        scope = 'pages "%s" 를 못 풀어 문서 전체 %d 페이지로 셌다' % (bad, count)
    elif pages_arg is None or str(pages_arg).strip() == '':
        scope = '%d 페이지' % count
    else:
        scope = 'pages "%s" 로 %d 페이지(전체 %d)' % (pages_arg, len(sel), count)
    picked = [sizes[p - 1] for p in sel] if sizes else None
    if picked is None or None in picked:
        return emit(context='그림 문 — %s 는 %s — 페이지 크기를 못 읽어 토큰은 안 셌다. Read 는 장마다 그림 한 장을 '
                            '싣는다' % (name, scope))
    px = [pdf_px(s) for s in picked]
    # 천장 밖 장은 상류가 깎은 뒤라 패치 천장을 넘지 못한다 — 합은 그 장을 천장 값 이하로 센다
    total = sum(min(v.patches(p), v.TOKEN_CAP) if v.downscaled(p) else v.patches(p) for p in px)
    quiet = v.patches((v.MAX_EDGE, v.MAX_EDGE))   # 그림 한 장이면 문이 조용히 넘기는 가장 큰 값
    if bad is None and max(max(p) for p in px) <= v.MAX_EDGE and total <= quiet:
        return 0
    shapes = sorted(set(px), key=v.patches)
    lo, hi = shapes[0], shapes[-1]
    each = ('장당 %d×%d · %s 토큰' % (hi[0], hi[1], format(v.patches(hi), ',')) if lo == hi else
            '장당 %d×%d ~ %d×%d · %s ~ %s 토큰' % (lo[0], lo[1], hi[0], hi[1],
                                                 format(v.patches(lo), ','), format(v.patches(hi), ',')))
    ctx = ('그림 문 — %s 는 %s · %s · 합 %s 토큰 (Read 가 장마다 그림 한 장으로 싣고 %ddpi 로 그린다면 — Claude Code 의 '
           'pdftoppm 값이고 판마다 다를 수 있다)' % (name, scope, each, format(total, ','), READ_PDF_DPI))
    clipped = sum(1 for p in px if v.downscaled(p))
    if clipped:
        ctx += ('. 그 가운데 %d 장은 장당 천장(긴 변 %d · %s 토큰) 밖이라 보내기 전에 깎인다 — 합은 그 장을 천장 값으로 '
                '셌고, 깎이는 픽셀은 값이 0 이다' % (clipped, v.LONG_EDGE_CAP, format(v.TOKEN_CAP, ',')))
    if len(sel) > 1:
        ctx += '. 줄이는 손은 pages 다 — 볼 페이지만 열면 합이 준다. 다 필요하면 그대로 연다 — 고르는 것은 너다'
    return emit(context=ctx)


def screen_sizes():
    """이 PC 화면 전체의 치수들 — 주 화면과 가상 화면(여러 모니터를 합친 것). 윈도우만 · 못 재면 빈 집합.

    시험은 `IMAGE_GATE_SCREENS="3440x1440;1920x1080"` 로 준다 — 빈 값이면 화면이 없는 것으로 친다.
    """
    forced = os.environ.get('IMAGE_GATE_SCREENS')
    if forced is not None:
        out = set()
        for part in forced.split(';'):
            m = re.match(r'^\s*(\d+)x(\d+)\s*$', part)
            if m:
                out.add((int(m.group(1)), int(m.group(2))))
        return out
    if sys.platform != 'win32':
        return set()
    try:
        import ctypes  # noqa: PLC0415
        u = ctypes.windll.user32
        try:
            u.SetProcessDPIAware()
        except Exception:  # noqa: BLE001
            pass
        # 0·1 주 화면 · 78·79 가상 화면
        return {s for s in ((u.GetSystemMetrics(0), u.GetSystemMetrics(1)),
                            (u.GetSystemMetrics(78), u.GetSystemMetrics(79))) if s[0] and s[1]}
    except Exception:  # noqa: BLE001
        return set()


def whole_screen_note(path, size, vdir):
    """화면 전체 캡처로 보이는 그림에 붙일 한 줄 — 아니면 빈 문자열.

    ⚠ **왜 있나.** 화면 전체를 찍은 그림은 **맨 위에 보이는 픽셀**이다. 보려던 창이 다른 창 뒤에
    있으면 앞 창이 찍히고, 캡처를 막는 창(VDI 클라이언트 등)은 대체 그림으로 찍힌다. 새 창은 사람이
    쓰던 창의 초점을 못 뺏어 뒤에 뜨는 것이 흔한데, 그 빈 자리를 「창이 안 떴다 · 글씨가 없다」로
    읽으면 멀쩡한 것을 고치러 간다(실측 2026-09-25 — 떠서 글씨를 흘리던 콘솔이 앞 창에 가려 전체
    캡처에 없었다). 그 교훈은 **그림을 여는 순간에만** 쓸모가 있어 이 문이 든다.
    ⚠ **치수가 화면과 똑같을 때만 붙인다** — 줄인 그림은 비율만 같아 슬라이드 같은 16:9 그림과 안
    갈린다. 원본을 여는 첫 순간(대개 천장 밖이라 막히는 그 자리)에 한 번 뜨면 된다.
    """
    if tuple(size) not in screen_sizes():
        return ''
    see = os.path.join(vdir, '_see_window.ps1')
    return ('그림 문 — %s 는 이 PC 화면 전체와 같은 크기(%d×%d)다. 화면 합성본이라 **다른 창에 가려진 창은 안 '
            '찍히고**, 캡처를 막는 창(VDI 등)은 대체 그림으로 찍힌다 — 빈 자리는 「없다」가 아니라 「안 보였다」다. '
            '특정 창을 보려면 창 손잡이로 찍는다(가려져도 찍힌다): powershell -NoProfile -ExecutionPolicy Bypass '
            '-File "%s" -Title "<창 제목 일부>"  (제목 목록은 -List)'
            % (os.path.basename(path), size[0], size[1], see))


def screen_long_edge():
    """주 화면의 긴 변 — 윈도우만 잰다(ctypes · 표준 라이브러리). 못 재면 None."""
    if sys.platform != 'win32':
        return None
    try:
        import ctypes  # noqa: PLC0415
        u = ctypes.windll.user32
        try:
            u.SetProcessDPIAware()
        except Exception:  # noqa: BLE001
            pass
        return max(u.GetSystemMetrics(0), u.GetSystemMetrics(1)) or None
    except Exception:  # noqa: BLE001
        return None


# ── 판정 ─────────────────────────────────────────────────────────────────────────
def _no_scale(d):
    """`scale` 이 없거나 `null` 이면 안 고른 것이다 — null 은 부재를 글자로 쓴 것이지 고른 값이 아니다."""
    return d.get('scale') is None


def shots_without_scale(name, inp):
    """scale 을 안 적은 스크린샷·zoom — 배치 안까지 훑는다. `(표찰, 갈래)` 목록.

    갈래는 힌트를 가른다 — `screen`(computer-use 스크린샷 · 주 화면 치수가 기준) ·
    `viewport`(브라우저 스크린샷 · 패널 뷰포트라 화면 치수와 무관) · `zoom`(region 크기가 기준).
    """
    out = []
    browser = '__computer-use__' not in name
    if name.endswith('__screenshot'):
        if _no_scale(inp):
            out.append(('screenshot', 'screen'))
    elif name.endswith('__zoom'):
        if _no_scale(inp):
            out.append(('zoom', 'zoom'))
    elif name.endswith('__computer'):
        if inp.get('action') in ('screenshot', 'zoom') and _no_scale(inp):
            out.append((inp['action'], 'zoom' if inp['action'] == 'zoom' else 'viewport'))
    elif name.endswith('__browser_batch'):
        for i, a in enumerate(inp.get('actions') or []):
            sub = (a or {}).get('input') or {}
            if (a or {}).get('name') == 'computer' and sub.get('action') in ('screenshot', 'zoom') \
                    and _no_scale(sub):
                out.append(('actions[%d] %s' % (i, sub['action']), 'zoom' if sub['action'] == 'zoom' else 'viewport'))
    elif name.endswith('__computer_batch'):
        for i, a in enumerate(inp.get('actions') or []):
            if (a or {}).get('action') in ('screenshot', 'zoom') and _no_scale(a):
                out.append(('actions[%d] %s' % (i, a['action']), 'zoom' if a['action'] == 'zoom' else 'screen'))
    del browser
    return out


def scale_hints(kinds, v):
    """갈래마다 맞는 힌트 — 주 화면 치수는 computer-use 스크린샷에만 맞다(리뷰 2026-09-22)."""
    hints = []
    if 'screen' in kinds:
        edge = screen_long_edge()
        hints.append('화면 긴 변 %d — 눈금 %d 이면 scale ≈ %.2f' % (edge, v.MAX_EDGE, min(1.0, v.MAX_EDGE / edge))
                     if edge else '눈금은 긴 변 %d (3440 화면이면 ≈ 0.37 · 1920 이면 ≈ 0.67)' % v.MAX_EDGE)
    if 'viewport' in kinds:
        hints.append('브라우저는 패널 뷰포트를 찍는다 — 뷰포트 긴 변이 %d 안이면 1, 넘으면 그 비율' % v.MAX_EDGE)
    if 'zoom' in kinds:
        hints.append('zoom 은 region 크기가 기준 — region 긴 변이 %d 을 넘을 때만 줄인다' % v.MAX_EDGE)
    return ' · '.join(hints)


def emit(decision=None, reason=None, context=None):
    out = {'hookEventName': 'PreToolUse'}
    if decision:
        out['permissionDecision'] = decision
        out['permissionDecisionReason'] = reason
    if context:
        out['additionalContext'] = context
    if len(out) > 1:
        sys.stdout.write(json.dumps({'hookSpecificOutput': out}, ensure_ascii=False))
    return 0


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    name = data.get('tool_name') or ''
    inp = data.get('tool_input') or {}
    if name != 'Read' and not SHOT_TOOLS.match(name):
        return 0

    v, vdir = load_vision()
    if v is None:
        return emit(context='그림 문 — 눈금(씨앗 _check/_vision.py)을 못 찾아 안 쟀다. 치수는 스스로 고른다')

    if SHOT_TOOLS.match(name):
        missing = shots_without_scale(name, inp)
        if not missing:
            return 0
        return emit('deny',
                    '그림 문 — `scale` 을 안 골랐다: %s. 찍을 때 치수를 고르는 것이 본이다(값은 가로×세로). '
                    '%s · UI 글자가 작으면 더 크게 · 값을 적으면(1 이어도) 통과한다'
                    % (' · '.join(m for m, _ in missing), scale_hints({k for _, k in missing}, v)))

    # Read — 확장자 목록(IMG_EXT · PDF_EXT)은 껍데기(`image-gate.sh` 의 case 글롭)와 짝이다
    path = str(inp.get('file_path') or '')
    if path.lower().endswith(PDF_EXT):
        return pdf_gate(path, inp.get('pages'), v)
    if not path.lower().endswith(IMG_EXT):
        return 0
    size = dims(path)
    if not size:
        return emit(context='그림 문 — %s 의 치수를 머리에서 못 읽어 안 쟀다' % os.path.basename(path))
    w, h = size
    toks = v.patches(size)
    # 줄이는 손은 눈금을 읽은 그 폴더의 이웃이다 — 홈 씨앗이 없으면 저장소 진본을 가리킨다
    shrink = 'python -X utf8 "%s" "%s" 결과.webp' % (os.path.join(vdir, '_shrink.py'), path)
    # 화면 전체 캡처면 치수 말과 **같이** 낸다 — 막히는 판(천장 밖)에서도 빠지면 안 된다: 원본을 처음
    # 여는 그 순간이 대개 막히는 판이다.
    note = whole_screen_note(path, size, vdir)
    if v.downscaled(size):
        fw, fh = v.fit(size, v.MAX_EDGE)
        reason = ('그림 문 — %s 는 %d×%d · %s 토큰인데 상류 천장(긴 변 %d · %s 토큰) 밖이라 보내기 전에 '
                  '깎인다 — 그 픽셀은 값이 0 이고 어느 판으로 깎일지 못 고른다. 먼저 줄인다: %s  '
                  '(긴 변 %d → %d×%d · %s 토큰 · 글자가 작으면 --max-edge 로 더 크게 · '
                  'PIL 이 없으면 python -m pip install pillow, 그것도 안 되면 다른 손으로 긴 변 %d 안까지 줄여 연다)'
                  % (os.path.basename(path), w, h, format(toks, ','), v.LONG_EDGE_CAP,
                     format(v.TOKEN_CAP, ','), shrink, v.MAX_EDGE, fw, fh,
                     format(v.patches((fw, fh)), ','), v.LONG_EDGE_CAP))
        return emit('deny', reason + ('\n' + note if note else ''))
    if max(size) > v.MAX_EDGE:
        fw, fh = v.fit(size, v.MAX_EDGE)
        ctx = ('그림 문 — %s 는 %d×%d · %s 토큰. 긴 변 %d 이면 %d×%d · %s 토큰 (%s). '
               '글자가 작으면 그대로 읽는다 — 고르는 것은 너다'
               % (os.path.basename(path), w, h, format(toks, ','), v.MAX_EDGE, fw, fh,
                  format(v.patches((fw, fh)), ','), shrink))
        return emit(context=ctx + ('\n' + note if note else ''))
    if note:
        return emit(context=note)
    return 0


if __name__ == '__main__':
    sys.exit(main())
