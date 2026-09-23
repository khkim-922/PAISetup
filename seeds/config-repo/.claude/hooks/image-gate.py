"""그림 문 — 모델이 그림을 받기 **직전**에 치수를 재고, 안 고른 자리는 막는다 (PreToolUse 훅).

**왜 있나.** 그림의 값은 바이트가 아니라 가로×세로고(28×28 패치 하나가 토큰 하나), 상류 천장 위의
픽셀은 어차피 깎여 값이 0 이다. 규범이 「찍을 때 치수를 고른다」고 적어도 그 줄은 찍는 순간에
안 떠오른다 — 안 골라도 아무 데서도 안 걸리는 조용한 부재였다(claude-config #73). 이 문이 그
순간에 판단과 무관하게 건다.

두 길을 든다 — 픽셀이 **생기기 전**인가 **이미 있나**로 갈린다:

  · 도구 스크린샷·zoom (브라우저 · computer-use · 크롬 확장 · 그 배치들) — `scale` 을 안 적으면 **막는다.**
    적으면 1 이어도 통과 — 「골랐다」가 본이지 값이 본이 아니다. 화면을 재서 눈금에 맞는 scale 을
    곁에 댄다 (윈도우만 · 다른 판은 수만 댄다).
  · `Read` 로 그림 파일 열기 — 이미 있는 그림이라 막아도 픽셀은 안 아껴진다. 그래서
      긴 변 ≤ MAX_EDGE            조용히 통과
      MAX_EDGE < 긴 변, 천장 안    통과 + 곁말(치수 · 토큰 · 줄이면 얼마 · 줄이는 한 줄) — 판단은 모델
      천장 밖(상류가 깎는다)       막는다 — 값 0 인 픽셀이고 어느 판으로 깎일지 못 고른다

⚠ **눈금은 씨앗 `_vision.py` 가 든다** — 여기 숫자를 안 적는다. 못 찾으면 **막지 않고** 「못 쟀다」
   한 줄만 남긴다: 문이 없는 것과 문이 잘못 잠긴 것은 다른 사고고, 뒤엣것이 더 비싸다.
⚠ **PIL 을 안 든다** — 치수는 파일 머리에서 읽는다(PNG · JPEG · GIF · WebP). 줄이는 손은 PIL 이
   드는데 그건 모델이 부르는 자리다(#72).
⚠ **1280 은 답이 아니다** — UI 글자는 그보다 커야 읽힌다. 곁말은 수를 대고 고르게 한다. 세부는 zoom.

부르는 자리 — 홈 `~/.claude/settings.json` 의 PreToolUse. 앞에 셸 껍데기(`image-gate.sh` · 곁 파일)가
서서 stdin 에 그림 낌새(확장자·screenshot·zoom)가 있을 때만 이 몸통을 띄운다 — 매 Read 마다 프로세스를
띄우지 않기 위해서다. 껍데기 글자와 matcher 는 그 파일 한 벌이고, 심는 손은 자리만 채운 한 줄을 심는다.
**심는 손이 둘이다** — `session-start-body.sh`(이 저장소를 든 자리 · 홈 SessionStart 훅과 같은 자리)와 배포본
설치기(`PAISetup/install.ps1` 의 씨앗 칸 직후 · 저장소 없는 동료 자리). 가리키는 몸통은 갈린다 — 이쪽은
저장소 진본, 저쪽은 홈 씨앗 사본. **주인은 저장소 진본이다** — 세션 훅은 늘 제 판으로 갈아타고, 설치기는
저장소 진본을 가리키는 항목이 살아 있으면 비켜선다.

시험 — `python -X utf8 scripts/image-gate-check.py` (양성·음성 표본을 먹여 판정을 문다).
**껍데기 층은 홈에 심긴 실물을 읽어 재므로 누가 심었든 그것을 잰다.**
"""
import json
import os
import re
import struct
import sys

IMG_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
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

    # Read — 확장자 목록은 껍데기(`image-gate.sh` 의 case 글롭)와 짝이다
    path = str(inp.get('file_path') or '')
    if not path.lower().endswith(IMG_EXT):
        return 0
    size = dims(path)
    if not size:
        return emit(context='그림 문 — %s 의 치수를 머리에서 못 읽어 안 쟀다' % os.path.basename(path))
    w, h = size
    toks = v.patches(size)
    # 줄이는 손은 눈금을 읽은 그 폴더의 이웃이다 — 홈 씨앗이 없으면 저장소 진본을 가리킨다
    shrink = 'python -X utf8 "%s" "%s" 결과.webp' % (os.path.join(vdir, '_shrink.py'), path)
    if v.downscaled(size):
        fw, fh = v.fit(size, v.MAX_EDGE)
        return emit('deny',
                    '그림 문 — %s 는 %d×%d · %s 토큰인데 상류 천장(긴 변 %d · %s 토큰) 밖이라 보내기 전에 '
                    '깎인다 — 그 픽셀은 값이 0 이고 어느 판으로 깎일지 못 고른다. 먼저 줄인다: %s  '
                    '(긴 변 %d → %d×%d · %s 토큰 · 글자가 작으면 --max-edge 로 더 크게 · '
                    'PIL 이 없으면 python -m pip install pillow, 그것도 안 되면 다른 손으로 긴 변 %d 안까지 줄여 연다)'
                    % (os.path.basename(path), w, h, format(toks, ','), v.LONG_EDGE_CAP,
                       format(v.TOKEN_CAP, ','), shrink, v.MAX_EDGE, fw, fh,
                       format(v.patches((fw, fh)), ','), v.LONG_EDGE_CAP))
    if max(size) > v.MAX_EDGE:
        fw, fh = v.fit(size, v.MAX_EDGE)
        return emit(context='그림 문 — %s 는 %d×%d · %s 토큰. 긴 변 %d 이면 %d×%d · %s 토큰 (%s). '
                            '글자가 작으면 그대로 읽는다 — 고르는 것은 너다'
                            % (os.path.basename(path), w, h, format(toks, ','), v.MAX_EDGE, fw, fh,
                               format(v.patches((fw, fh)), ','), shrink))
    return 0


if __name__ == '__main__':
    sys.exit(main())
