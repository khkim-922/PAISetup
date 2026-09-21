"""그림을 줄여 비전 토큰을 아낀다 — 치수가 토큰을 정하고 무손실 WebP 는 바이트만 정한다.

좌표 — 무손실 WebP 로 누르는 기전은 아뜰리에 `app/shot.py` 의 `_webp`(1cdb756 · 2026-09-21)
에서 왔다. **손으로 따라가지 않는다 — 일부러 갈랐다:** 저쪽은 지면을 첨부로 보내는 자리라
픽셀을 한 점도 안 잃는 것이 난간이고 치수를 안 건드린다. 이쪽은 **보는 자가 비전 모델**이라
치수가 곧 값이다. 그래서 리사이즈를 더했고, 형식은 저쪽 것을 그대로 받았다.

**왜 이 부품이 있나.** 모델이 그림을 보는 값은 28×28 패치 수로 매겨진다 —
`⌈가로/28⌉ × ⌈세로/28⌉`. **바이트가 아니라 치수가 값을 정한다**(Anthropic vision 문서 ·
2026-09-21 확인). 그래서 같은 그림을 더 세게 눌러도 값은 한 푼도 안 준다. 줄이는 자는
치수 하나뿐이다.

⚠ **그래서 손실 압축은 여기서 설 자리가 없다.** 값을 안 줄이면서 글자만 깎는다 — 같은
문서가 *"heavy JPEG compression can make text difficult to read"* 라고 못박는다. 바이트를
줄이려는 것이면 무손실 WebP 가 이미 그 일을 하고 글자는 안 건드린다.

바이트가 값이 되는 자리는 따로 있다 — 그림이 **글자로 실려 갈 때**(HTML 안의
`data:image/...;base64,…`)와 봉투 한도에 닿을 때다. 그 자리는 치수가 아니라 바이트가 물고,
`lossless` 를 끄지 않고도 WebP 가 든다.

⚠ **손실 원본을 무손실로 되구우면 바이트가 늘어난다**(실측: 190KB JPEG → 239KB WebP).
   무손실은 압축 아티팩트까지 고스란히 지기 때문이다. 찍는 쪽이 PNG 를 내면 안 겪는 일이라
   여기서 고르지 않고, 늘어나면 아래 줄이 그 사실을 댄다.

    python -X utf8 _check/_shrink.py 원본.png 결과.webp
    python -X utf8 _check/_shrink.py 원본.png 결과.webp --max-edge 1600

기본 긴 변은 `_vision.py` 의 `MAX_EDGE` — 근거(실측)와 그것이 눈금이지 천장이 아니라는 단서도
거기 있다. 더 줄이려면 **먼저 눈으로 보고 정한다.**

⚠ **PIL 이 든다** — 없는 저장소는 이 부품을 안 받는다(`_pixels.py` 와 같은 문 아래다).
   눈금만 필요한 자는 `_vision.py` 를 읽는다 — 그쪽은 의존성이 없다.
⚠ **안 하는 것 하나 — 여백 잘라내기.** 화면을 통째로 찍으면 지면 둘레에 빈 띠가 남고 그만큼
   값을 버린다(21:9 화면에 1.414:1 지면이면 띠가 41%다). **띠를 픽셀 색으로 찾는 것은 꼴이
   아니라 뜻이라** — 어두운 지면과 안 갈린다 — 여기서 안 짓는다. 다만 **비율로 재면 꼴이다**:
   지면 치수는 파일이 들고 지면은 화면 복판에 비율 맞춰 놓이니, 집을 자리가 계산으로 나온다.
   그 계산은 **찍는 쪽**이 든다 — 줄이는 자는 받은 그림을 줄일 뿐이다.
"""
import argparse
import os
import sys

from PIL import Image

# 눈금(패치 · 기본 긴 변 · 천장)과 셈(`patches` · `fit`)은 `_vision.py` 가 든다 — PIL 없이 도는
# 그림 문(홈 훅)이 같은 수를 읽어야 해서 여기 안 둔다.
from _vision import MAX_EDGE, fit, patches  # noqa: E402


def shrink(src, dest, max_edge=MAX_EDGE, lossless=True):
    """그림을 긴 변 상한까지 줄여 WebP 로 굽는다 — 줄인 치수를 돌려준다."""
    im = Image.open(src)
    before = im.size
    after = fit(before, max_edge)
    if after != before:
        im = im.convert("RGB").resize(after, Image.Resampling.LANCZOS)
    im.save(dest, "WEBP", lossless=lossless)
    return before, after


def say(src, dest, before, after):
    """줄인 결과를 한 줄로 — 치수와 시각 토큰을 함께 낸다. 바이트만 적으면 값을 오해한다.

    ⚠ 이름이 `report` 가 아닌 까닭 — 이 폴더에서 그 낱말은 **판정을 세우는 손**이고
      (`_verdict.py`), 검사가 그 이름을 보고 판정 검사로 센다. 여기는 판정을 안 낸다.
    """
    was, now = patches(before), patches(after)
    cut = "" if was == now else f" ({(1 - now / was) * 100:.0f}% 줄었다)"
    print(f"[줄임] {before[0]}x{before[1]} -> {after[0]}x{after[1]}"
          f" · 시각 토큰 {was:,} -> {now:,}{cut}")
    print(f"       {os.path.getsize(src):,} B -> {os.path.getsize(dest):,} B -> {dest}")
    if was == now:
        print("       치수가 이미 상한 안이라 값은 그대로다 — 더 줄이려면 찍는 쪽 해상도를 낮춘다.")


def main(argv=None):
    p = argparse.ArgumentParser(description="비전 토큰을 아끼게 그림을 줄인다")
    p.add_argument("src", help="원본 그림")
    p.add_argument("dest", nargs="?", help="결과 WebP (없으면 원본 이름에 .webp)")
    p.add_argument("--max-edge", type=int, default=MAX_EDGE,
                   help=f"긴 변 상한 픽셀 (기본 {MAX_EDGE})")
    p.add_argument("--lossy", action="store_true",
                   help="손실 WebP 로 굽는다 — 글자를 깎으므로 읽힐 일이 없는 그림에만")
    a = p.parse_args(argv)

    dest = a.dest or os.path.splitext(a.src)[0] + ".webp"
    before, after = shrink(a.src, dest, a.max_edge, lossless=not a.lossy)
    say(a.src, dest, before, after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
