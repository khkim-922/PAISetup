"""양식 폴더를 .pptx 로 굽는다.

회사 PC 의 DRM(Fasoo)은 .pptx 를 시간이 지나면 감싸 파서가 못 연다. 평문 파일은 안 감싸므로
양식을 파트 단위로 푼 폴더(`template/<이름>/`)를 진본으로 두고, 쓸 때 이 스크립트로 굽는다.

  python -X utf8 build_template.py report-a4 out.pptx            # 굽기
  python -X utf8 build_template.py report-a4 out.pptx --check    # 구운 것이 폴더와 같은지 대조(아무것도 안 쓴다)

폴더 이름은 `<이 스킬>/template/` 아래에서 찾고, 없으면 주어진 경로를 폴더로 본다.
끝 코드: 0 같음/구움 · 1 다름 · 2 쓰는 법 틀림.

표준 라이브러리만 쓴다. 같은 폴더면 어느 PC 에서든 같은 바이트의 압축 전 내용이 나온다
(항목 시각 1980-01-01 · 운영체제 표지 고정).
"""
import argparse
import sys
import zipfile
import zlib
from pathlib import Path

CONTENT_TYPES = "[Content_Types].xml"
# 이미 압축된 형식은 다시 압축하지 않는다.
STORED_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif"}
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
TEMPLATE_ROOT = Path(__file__).resolve().parent.parent / "template"


def find_folder(name: str) -> Path:
    for cand in (TEMPLATE_ROOT / name, Path(name)):
        if cand.is_dir():
            return cand
    sys.exit(f"양식 폴더가 없다: {name} (찾은 자리: {TEMPLATE_ROOT})")


def collect(folder: Path) -> dict:
    """폴더의 모든 파일을 {zip 안 이름(/ 구분): 바이트} 로."""
    parts = {}
    for p in folder.rglob("*"):
        if p.is_file():
            parts[p.relative_to(folder).as_posix()] = p.read_bytes()
    if CONTENT_TYPES not in parts:
        sys.exit(f"{folder} 에 {CONTENT_TYPES} 가 없다 — 양식 폴더가 아니다")
    return parts


def ordered(names):
    """`[Content_Types].xml` 이 맨 앞, 나머지는 이름순."""
    return [CONTENT_TYPES] + sorted(n for n in names if n != CONTENT_TYPES)


def pack(parts: dict, out: Path) -> None:
    with zipfile.ZipFile(out, "w") as zf:
        for name in ordered(parts):
            zi = zipfile.ZipInfo(name, FIXED_TIME)
            zi.create_system = 0
            zi.external_attr = 0
            stored = Path(name).suffix.lower() in STORED_SUFFIXES
            zi.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            zf.writestr(zi, parts[name])


def first_diff(a: bytes, b: bytes) -> int:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))


def check(parts: dict, pptx: Path) -> list:
    """구운 .pptx 가 폴더와 같은지 대조해 다른 점의 목록을 낸다(빈 목록이 같음)."""
    problems = []
    with open(pptx, "rb") as f:
        if f.read(2) != b"PK":
            return [f"머리가 PK 가 아니다 — zip 이 아니거나 감겼다: {pptx}"]
    try:
        zf = zipfile.ZipFile(pptx)
    except zipfile.BadZipFile as e:
        return [f"zip 으로 못 연다: {e}"]
    with zf:
        names = zf.namelist()
        if names[:1] != [CONTENT_TYPES]:
            problems.append(f"첫 항목이 {CONTENT_TYPES} 가 아니다: {names[:1]}")
        dups = sorted({n for n in names if names.count(n) > 1})
        if dups:
            problems.append(f"이름이 겹친다: {dups}")
        for n in sorted(set(parts) - set(names)):
            problems.append(f"zip 에 없다: {n}")
        for n in sorted(set(names) - set(parts)):
            problems.append(f"폴더에 없는 항목이 zip 에 있다: {n}")
        for n in sorted(set(names) & set(parts)):
            try:
                got = zf.read(n)
            except (zipfile.BadZipFile, zlib.error) as e:
                problems.append(f"항목을 못 읽는다: {n} ({e})")
                continue
            if got != parts[n]:
                problems.append(
                    f"바이트가 다르다: {n} (폴더 {len(parts[n])} · zip {len(got)} · 첫 차이 {first_diff(got, parts[n])}번째)"
                )
        bad = zf.testzip()
        if bad:
            problems.append(f"CRC 가 깨진 항목: {bad}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="양식 폴더를 .pptx 로 굽거나, 구운 것을 폴더와 대조한다.")
    ap.add_argument("folder", help="양식 폴더 이름(template/ 아래) 또는 경로")
    ap.add_argument("out", type=Path, help="굽는 .pptx 경로")
    ap.add_argument("--check", action="store_true", help="굽지 않고, 이미 있는 out 이 폴더와 같은지만 대조")
    args = ap.parse_args()

    folder = find_folder(args.folder)
    parts = collect(folder)

    if args.check:
        if not args.out.is_file():
            print(f"대조할 파일이 없다: {args.out} — 먼저 굽는다", file=sys.stderr)
            return 2
        problems = check(parts, args.out)
        if problems:
            print(f"다름 — {args.out} 이 {folder} 와 같지 않다:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print(f"같음 — {len(parts)} 파트 · 이름 · 바이트 · {CONTENT_TYPES} 첫 항목 · CRC 를 봤다.")
        print("안 본 것: 파워포인트가 여는지 · 각 파트가 XML 문법에 맞는지.")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pack(parts, args.out)
    print(f"구웠다: {args.out} ({len(parts)} 파트 ← {folder})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
