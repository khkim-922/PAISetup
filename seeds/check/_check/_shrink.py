"""그림을 줄여 비전 토큰을 아낀다 — 치수가 토큰을 정하고 무손실 WebP 는 바이트만 정한다.

좌표 — 무손실 WebP 로 누르는 기전은 아뜰리에 `app/shot.py` 의 `_webp`(1cdb756)에서 왔다.
**손으로 따라가지 않는다 — 일부러 갈랐다:** 저쪽은 지면을 첨부로 보내는 자리라 픽셀을 한 점도
안 잃는 것이 난간이고 치수를 안 건드린다. 이쪽은 보는 자가 비전 모델이라 치수가 곧 값이어서
치수를 줄이고, 형식(무손실 WebP)은 저쪽과 같다.

    python -X utf8 _check/_shrink.py 원본.png 결과.webp
    python -X utf8 _check/_shrink.py 원본.png 결과.webp --max-edge 1600
    python -X utf8 _check/_shrink.py --batch 원본1 결과1 [원본2 결과2 …] [--max-edge N]

내는 것 — 결과 WebP 한 장(이름을 안 주면 원본 이름에 `.webp`)과 줄인 결과 두세 줄(치수 · 시각 토큰 ·
바이트). 판정을 안 내는 부품이라 구우면 0 이고, 인자가 틀리면 argparse 가 2 로, 그림을 못 열면 역추적과
1 로 나간다. 다른 코드는 `shrink()` 를 불러 쓴다.

여러 장은 `--batch` 로 한 번에 넘긴다 — 프로세스를 장마다 띄우면 해석기와 PIL 을 장마다 다시 싣는다. 인자는
(원본, 결과) 짝의 나열이고, **앞 짝이 져도 남은 짝을 다 해 본다.** 구운 짝마다 stdout 에 한 줄(`say_pair`), 진 짝마다
stderr 에 그 원본을 든 한 줄을 내고, 진 짝의 결과 파일은 남기지 않는다(전에 있던 것도 지운다 — 결과가 원본과 같은
파일일 때만 그대로 둔다). 종료는 모든 짝을 구웠을 때만 0, 하나라도 지면 1 이다(짝이 안 맞는 인자는 argparse 의 2).
그래서 부르는 쪽은 짝마다 결과 파일이 있나로 가른다.

결과는 곁의 임시 파일(`PART_SUFFIX`)에 다 구운 뒤 제 이름으로 옮긴다 — 굽다 죽어도 반쪽 그림이 결과 이름으로
안 남고, 결과가 원본과 같은 파일이어도 원본을 읽기 전에 덮지 않는다.

모델이 그림을 보는 값은 28×28 패치 수로 매겨진다 — `⌈가로/28⌉ × ⌈세로/28⌉`. **바이트가 아니라
치수가 값을 정한다**(Anthropic vision 문서). 같은 그림을 더 세게 눌러도 값은 한 푼도 안 줄어,
줄이는 자는 치수 하나뿐이다.

손실 압축은 기본이 아니다 — 값을 안 줄이면서 글자만 깎는다. 같은 문서가 *"heavy JPEG compression
can make text difficult to read"* 라고 못박는다. `--lossy` 는 읽힐 일이 없는 그림에만 쓴다.
바이트를 줄이려는 것이면 무손실 WebP 가 이미 그 일을 하고 글자는 안 건드린다.

바이트가 값이 되는 자리는 따로 있다 — 그림이 **글자로 실려 갈 때**(HTML 안의
`data:image/...;base64,…`)와 봉투 한도에 닿을 때다. 그 자리는 치수가 아니라 바이트가 물고,
`lossless` 를 끄지 않고도 WebP 가 든다.

손실 원본을 무손실로 되구우면 바이트가 늘어난다(190KB JPEG 가 239KB WebP 가 되는 꼴) — 무손실은
압축 아티팩트까지 고스란히 진다. 찍는 쪽이 PNG 를 내면 안 겪는 일이라 여기서 고르지 않고, 늘면
`say()` 가 찍는 바이트 줄에 그대로 보인다.

기본 긴 변은 `_vision.py` 의 `MAX_EDGE` — 근거와 그것이 눈금이지 천장이 아니라는 단서도 거기
있다. 더 줄이려면 먼저 눈으로 보고 정한다.

PIL 이 든다 — 없는 저장소는 이 부품을 안 받는다(`_pixels.py` 와 같은 문 아래다). 눈금만 필요한
자는 `_vision.py` 를 읽는다 — 그쪽은 의존성이 없다.

안 하는 것 — 여백 잘라내기. 화면을 통째로 찍으면 지면 둘레에 빈 띠가 남고 그만큼 값을 버린다
(21:9 화면에 1.414:1 지면이면 띠가 41%다). 띠를 픽셀 색으로 찾는 것은 꼴이 아니라 뜻이라 — 어두운
지면과 안 갈린다 — 여기서 안 짓는다. 비율로 재면 꼴이다: 지면 치수는 파일이 들고 지면은 화면 복판에
비율 맞춰 놓이니, 집을 자리가 계산으로 나온다. 그 계산은 **찍는 쪽**이 든다 — 줄이는 자는 받은
그림을 줄일 뿐이다.
"""
import argparse
import os
import sys

from PIL import Image

# 눈금(패치 · 기본 긴 변 · 천장)과 셈(`patches` · `fit`)은 `_vision.py` 가 든다 — PIL 없이 도는
# 그림 문(홈 훅)이 같은 수를 읽어야 해서 여기 안 둔다.
from _vision import MAX_EDGE, fit, fit_page, patches  # noqa: E402

PAPER = (255, 255, 255)   # 투명한 자리에 까는 바탕 — 지면 · 메일 · 문서의 바탕색
PART_SUFFIX = ".part"     # 굽는 동안의 임시 이름에 붙는 꼬리 — 다 구우면 결과 이름으로 옮긴다


def opaque(im):
    """RGB 로 바꾼다 — 투명이 든 그림은 흰 바탕(`PAPER`)에 얹는다. 그냥 바꾸면 투명한 자리가 그 픽셀의 색
    (흔히 검정)으로 드러나, 투명 바탕의 어두운 글씨 도표가 통째로 검은 그림이 된다."""
    if im.mode in ("RGBA", "LA") or "transparency" in im.info:
        im = im.convert("RGBA")
        paper = Image.new("RGB", im.size, PAPER)
        paper.paste(im, mask=im.getchannel("A"))
        return paper
    return im.convert("RGB")


def shrink(src, dest, max_edge=None, lossless=True):
    """그림을 줄여 `dest` 에 WebP 로 굽는다 — (원본 치수, 줄인 치수)를 돌려준다.

    `max_edge` 를 주면 긴 변을 거기 맞추고, 안 주면 눈금의 기본(`_vision.fit_page` — 한 쪽 꼴까지는 긴 변
    `MAX_EDGE`, 그보다 길쭉한 세로 그림은 폭을 한 쪽 폭에)을 따른다. 이미 그 안이면 치수는 그대로 두고
    형식만 바꾼다. 줄일 때는 RGB 로 바꿔(`opaque`) LANCZOS 로 줄인다.

    `dest` 곁의 임시 파일에 굽고 원본을 닫은 뒤 `dest` 로 옮긴다 — 못 구우면 `dest` 는 손대지 않은 채 예외가 오르고,
    `dest` 가 `src` 와 같은 파일이어도 된다.
    """
    part = os.fspath(dest) + PART_SUFFIX
    try:
        with Image.open(src) as im:
            before = im.size
            after = fit_page(before) if max_edge is None else fit(before, max_edge)
            out = opaque(im).resize(after, Image.Resampling.LANCZOS) if after != before else im
            out.save(part, "WEBP", lossless=lossless)
        os.replace(part, dest)   # 원본을 닫은 뒤다 — 윈도우는 열린 파일 위로 못 옮긴다
    except BaseException:
        _unlink(part)
        raise
    return before, after


def _unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def _same_file(a, b):
    try:
        return os.path.samefile(a, b)
    except OSError:   # 한쪽이 없다
        return False


def say(src, dest, before, after):
    """줄인 결과를 찍는다 — 치수와 시각 토큰 한 줄 · 바이트 한 줄 · 값이 그대로면 한 줄 더.

    치수와 시각 토큰을 함께 내는 것은 바이트만 적으면 값을 오해해서다.
    이름이 `report` 가 아닌 까닭 — 이 폴더에서 그 낱말은 판정을 세우는 손(`_verdict.py`)이라
    `exit_code_check.py` 가 그 이름을 보고 판정 검사로 센다. 여기는 판정을 안 낸다.
    """
    was, now = patches(before), patches(after)
    cut = "" if was == now else f" ({(1 - now / was) * 100:.0f}% 줄었다)"
    print(f"[줄임] {before[0]}x{before[1]} -> {after[0]}x{after[1]}"
          f" · 시각 토큰 {was:,} -> {now:,}{cut}")
    print(f"       {os.path.getsize(src):,} B -> {os.path.getsize(dest):,} B -> {dest}")
    if was == now:
        print("       치수가 이미 상한 안이라 값은 그대로다 — 더 줄이려면 찍는 쪽 해상도를 낮춘다.")


def say_pair(src, dest, before, after):
    """`--batch` 의 구운 짝 하나를 한 줄로 찍는다 — 원본 · 결과 · 치수 · 시각 토큰. 짝마다 바로 내보낸다(부르는 쪽이
    시한으로 끊어도 그때까지 구운 짝의 줄은 건너가 있다)."""
    print(f"[줄임] {src} -> {dest} · {before[0]}x{before[1]} -> {after[0]}x{after[1]}"
          f" · 시각 토큰 {patches(before):,} -> {patches(after):,}", flush=True)


def batch(pairs, max_edge=None, lossless=True):
    """(원본, 결과) 짝을 차례로 줄인다 — 진 짝의 수를 돌려준다. 계약은 머리말의 `--batch` 문단이 든다."""
    lost = 0
    for src, dest in pairs:
        try:
            before, after = shrink(src, dest, max_edge, lossless)
        except Exception as exc:  # noqa: BLE001 — 한 장이 져도 남은 장을 해 본다
            lost += 1
            if not _same_file(src, dest):
                _unlink(dest)
            print(f"[못 줄임] {src} — {type(exc).__name__}: {' '.join(str(exc).split())}", file=sys.stderr, flush=True)
            continue
        say_pair(src, dest, before, after)
    return lost


def main(argv=None):
    p = argparse.ArgumentParser(description="비전 토큰을 아끼게 그림을 줄인다")
    p.add_argument("paths", nargs="+", metavar="그림",
                   help="원본 [결과 WebP — 없으면 원본 이름에 .webp]. --batch 면 (원본, 결과) 짝의 나열")
    p.add_argument("--batch", action="store_true",
                   help="여러 장을 한 번에 — 앞 짝이 져도 남은 짝을 다 해 보고, 하나라도 지면 1 로 나간다")
    p.add_argument("--max-edge", type=int, default=None,
                   help=f"긴 변 상한 픽셀 (안 주면 {MAX_EDGE} — 한 쪽보다 길쭉한 세로 그림은 폭을 한 쪽 폭에 맞춘다)")
    p.add_argument("--lossy", action="store_true",
                   help="손실 WebP 로 굽는다 — 글자를 깎으므로 읽힐 일이 없는 그림에만")
    a = p.parse_intermixed_args(argv)   # 옵션이 경로 사이에 와도 받는다 — `원본 --max-edge N 결과`

    if a.batch:
        if len(a.paths) % 2:
            p.error("--batch 는 (원본, 결과) 짝으로 받는다 — 경로 수가 홀수다")
        return 1 if batch(zip(a.paths[0::2], a.paths[1::2]), a.max_edge, lossless=not a.lossy) else 0
    if len(a.paths) > 2:
        p.error("원본과 결과 둘까지만 받는다 — 여러 장은 --batch 로 넘긴다")
    src = a.paths[0]
    dest = a.paths[1] if len(a.paths) > 1 else os.path.splitext(src)[0] + ".webp"
    before, after = shrink(src, dest, a.max_edge, lossless=not a.lossy)
    say(src, dest, before, after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
