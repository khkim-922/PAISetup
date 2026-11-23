"""본문 그림 — 메일 · 게시글 본문의 그림을 파일로 받아 둔다. 이 스킬의 명령과 형제 스킬 company-board · company-regulation 이 부른다.

부르는 꼴::

    import body_images
    got = body_images.save(srcs, fetch, out_dir)   # [{"no", "path", "kind", "bytes", "px"[, "shrunk_from" | "note"]} · {"no", "same_as"} · {"no", "skipped"}]

``srcs`` 는 본문에 나온 차례의 그림 주소고 ``no`` 는 그 차례(1 부터)다 — 본문 글자의 ``[그림 N]`` 과 같은 수다. ``fetch(src)`` 는 그 주소를
사내 세션으로 받아 바이트를 내고, 받을 수 없는 주소면 ``Refused`` 를 올린다(까닭이 ``skipped`` 에 든다). 그 밖의 예외는 그대로 오른다.
``data:`` 주소는 묻지 않고 풀고, 같은 주소는 한 번만 받는다. ``px`` 는 남긴 그림의 「가로×세로」, ``shrunk_from`` 은 줄이기 전 치수다.

⚠ 확장자는 Content-Type 이 아니라 파일 머리로 붙인다 — 모델이 파일을 여는 순간 그림 문(홈 훅 ``image-gate``)이 재는데, 확장자 없는 파일은
그 문을 비켜 간다. 그래서 꼴을 읽는 씨앗 부품(``_image_head.py``)을 못 실으면 그림을 하나도 안 받는다.

눈금(``_vision.fit_page``)을 넘는 그림은 씨앗의 줄이는 손(``_shrink.py``)을 본문 하나에 한 번 띄워 WebP 로 줄이고, 못 줄이면 받은 그대로
두고 ``note`` 에 적는다. 표준 라이브러리만 쓴다 — PIL 이 드는 줄이는 손은 딴 프로세스다. 까닭은 DESIGN.md 「body_images.py」.
"""

from __future__ import annotations

import base64
import binascii
import contextlib
import os
import pathlib
import subprocess
import sys
import urllib.parse

MAX_IMAGES = 12           # 한 본문에서 남기는 그림의 위 — 넘는 것은 「위를 넘었다」로 낸다. 아이콘처럼 안 남긴 것은 안 센다
MAX_ASKED = 48            # 한 본문에서 묻는 그림 주소의 위 — 아이콘뿐인 긴 본문이 주소마다 서버를 묻지 않게
MAX_BYTES = 20_000_000    # 그림 하나의 위 — 넘으면 남기지 않는다
ICON_EDGE = 48            # 긴 변이 이보다 작으면 아이콘 · 글머리표로 보고 안 남긴다
SEED_DIRS = (pathlib.Path.home() / ".claude" / "seeds" / "check" / "_check",                     # 설치가 홈에 놓은 씨앗
             pathlib.Path(__file__).resolve().parents[4] / "seeds" / "check" / "_check")          # 설정 저장소 안에서 돌 때의 진본
SEED_HEAD = "_image_head.py"   # 씨앗 폴더를 고르는 부품
SHRINK_SECONDS = 60       # 줄일 그림 한 장 몫의 시한 — 줄이는 손 한 번은 장 수만큼 받는다
SHRUNK_TAIL = ".shrunk.webp"   # 줄이는 손이 굽는 임시 이름의 꼬리 — 구운 뒤 ``image-<no>.webp`` 로 옮긴다(원본이 WebP 면 그 이름이 원본이다)
NO_SEED = "그림의 꼴을 읽는 씨앗 부품(_check/_image_head.py)을 못 찾아 그림을 안 받았다 — 씨앗이 이 스킬보다 낡았거나 없다. 설치를 다시 돌린다"
NO_SCALE = "눈금(씨앗 _vision.py)을 못 실어 안 줄였다"
SHRINK_LOST = "줄이기가 져서 받은 치수 그대로다(흔한 까닭은 PIL 이 없는 것 — python -m pip install pillow)"


class Refused(Exception):
    """앱 손이 그 주소를 안 받는다 — 사내 밖 · 읽기 전용으로 잰 꼴이 아니다 · 서버가 거절했다."""


def _seed():
    """(씨앗 폴더, ``_image_head``) — 그 부품을 든 첫 폴더를 ``sys.path`` 앞에 얹고 싣는다. 없거나 못 실으면 (None, None)."""
    where = next((d for d in SEED_DIRS if (d / SEED_HEAD).is_file()), None)
    if where is None:
        return None, None
    if str(where) not in sys.path:
        sys.path.insert(0, str(where))
    try:
        import _image_head  # noqa: PLC0415 — 자리를 넣은 뒤에 싣는다. 의존성이 없는 부품이다
    except Exception:  # noqa: BLE001 — 깨진 부품은 없는 것과 같다
        return None, None
    return where, _image_head


def _fit_page():
    """씨앗의 눈금 셈 ``_vision.fit_page``, 못 실으면 None. ``_seed()`` 가 자리를 얹은 뒤에 부른다."""
    try:
        import _vision  # noqa: PLC0415 — 의존성이 없는 눈금이다
        return _vision.fit_page
    except Exception:  # noqa: BLE001
        return None


def _shrink_all(where: pathlib.Path, pairs: list[tuple[pathlib.Path, pathlib.Path]]) -> str:
    """(원본, 임시 결과) 짝들을 씨앗의 줄이는 손 한 번으로 줄인다 → 못 돌렸거나 시한에 끊었으면 그 까닭, 돌았으면 "". 어느 짝이
    구워졌나는 결과 파일이 있나로 가른다 — 그 손은 다 구운 것만 결과 이름으로 옮긴다."""
    for _, part in pairs:
        part.unlink(missing_ok=True)    # 앞 판이 남긴 결과를 이번 판의 것으로 읽지 않게
    argv = [sys.executable, "-X", "utf8", str(where / "_shrink.py"), "--batch", *(str(p) for pair in pairs for p in pair)]
    try:
        subprocess.run(argv, capture_output=True, timeout=SHRINK_SECONDS * len(pairs), env={**os.environ, "PYTHONUTF8": "1"})
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"줄이는 손을 못 돌려 안 줄였다({type(exc).__name__})"
    return ""


def _data_uri(src: str) -> bytes:
    """base64 data 주소의 바이트를 푼다 — base64 가 아니거나 못 풀면 Refused."""
    meta, _, payload = src.partition(",")
    if ";base64" not in meta.lower():
        raise Refused("base64 가 아닌 data 주소다")
    try:
        return base64.b64decode(payload, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise Refused("data 주소를 못 풀었다") from exc


def save(srcs: list[str], fetch, out_dir: pathlib.Path) -> list[dict]:
    """그림을 ``out_dir`` 에 ``image-<no>.<확장자>`` 로 남긴다 — 계약은 머리말."""
    where, head = _seed()
    if head is None:
        return [{"no": no, "skipped": NO_SEED} for no in range(1, len(srcs) + 1)]
    out, seen, dropped, asked = [], {}, {}, 0   # seen: 남긴 주소 → 그 번호 · dropped: 안 남긴 주소 → 그 까닭
    kept = []                                   # 남긴 그림 — (out 의 자리, 번호, 경로, 꼴 이름, 치수)
    for no, src in enumerate(srcs, 1):
        key = urllib.parse.unquote(src.strip())
        if key in seen:
            out.append({"no": no, "same_as": seen[key]})
            continue
        if key in dropped:                      # 되풀이되는 아이콘 · 거절된 주소 — 다시 묻지 않는다
            out.append({"no": no, "skipped": dropped[key]})
            continue
        if len(seen) >= MAX_IMAGES:             # 위는 남긴 장으로 센다 — 차례로 세면 앞의 아이콘이 위를 먹어 뒤의 도표가 빠진다
            out.append({"no": no, "skipped": f"한 본문에서 {MAX_IMAGES} 장까지만 받는다"})
            continue
        if asked >= MAX_ASKED:
            out.append({"no": no, "skipped": f"한 본문에서 그림 주소 {MAX_ASKED} 곳까지만 묻는다"})
            continue
        asked += 1
        try:
            data = _data_uri(src) if src.lower().startswith("data:") else fetch(src)
            why = ""
        except Refused as exc:
            data, why = b"", str(exc)
        kind = size = None
        if not why:
            kind = head.kind(data)
            if not kind:
                why = "그림 문이 재는 꼴(PNG · JPEG · GIF · WebP)이 아니다 — 화면에서 본다"
        if not why and len(data) > MAX_BYTES:
            why = f"{len(data):,} 바이트 — 한 장의 위를 넘었다"
        if not why:
            size = head.size(data)              # 못 읽으면 None — 그때는 아이콘으로 거르지도 줄이지도 않는다
            if size and max(size) < ICON_EDGE:
                why = f"{size[0]}×{size[1]} — 아이콘 · 글머리표다"
        if why:
            dropped[key] = why
            out.append({"no": no, "skipped": why})
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"image-{no}.{kind[1]}"
        path.write_bytes(data)
        seen[key] = no
        kept.append((len(out), no, path, kind[0], size))
        out.append(None)                        # 줄이기가 끝난 뒤에 채운다 — 본문의 차례를 지킨다

    fit = _fit_page() if any(size for *_, size in kept) else None
    jobs = {}                                   # out 의 자리 → (임시 결과, 줄인 치수) — 눈금을 넘는 그림만
    for at, no, path, _name, size in kept:
        after = tuple(fit(size)) if size and fit else None
        if after and after != tuple(size):
            jobs[at] = (path.with_name(f"image-{no}{SHRUNK_TAIL}"), after)
    stopped = _shrink_all(where, [(path, jobs[at][0]) for at, _no, path, _name, _size in kept if at in jobs]) if jobs else ""
    for at, no, path, name, size in kept:
        note, was = (NO_SCALE if size and not fit else ""), None
        if at in jobs:
            part, after = jobs[at]
            final = path.with_suffix(".webp")   # 원본이 WebP 면 이 이름이 곧 원본이다 — 임시 결과로 구운 뒤에 덮는다
            if not part.is_file():
                note = stopped or SHRINK_LOST
            else:
                try:
                    os.replace(part, final)
                except OSError as exc:          # 결과 이름이 잠겼다 — 받은 그림은 그대로 있다
                    with contextlib.suppress(OSError):
                        part.unlink()
                    note = f"줄인 그림을 제 이름으로 못 옮겨 받은 치수 그대로다({type(exc).__name__})"
                else:
                    if final != path:
                        with contextlib.suppress(OSError):
                            path.unlink()
                    path, name, was, size = final, "WebP", size, after
        row = {"no": no, "path": str(path), "kind": name, "bytes": path.stat().st_size}
        if size:
            row["px"] = f"{size[0]}×{size[1]}"
        if was:
            row["shrunk_from"] = f"{was[0]}×{was[1]}"
        if note:
            row["note"] = note
        out[at] = row
    return out
