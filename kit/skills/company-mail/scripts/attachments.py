"""첨부 가름 — 받은 첨부 하나를 어떤 이름으로 남기고 무엇으로 읽으라고 이르나를 가른다. 이 스킬의 명령(``mail.py``)과 형제 스킬
company-board 가 함께 부른다. 서버에 묻지 않는다 — 바이트는 부르는 쪽이 받아 넘긴다. 표준 라이브러리만 쓴다.

부르는 꼴::

    import attachments
    names = attachments.file_names({번호: 서버가 준 이름, …}, reserved=("body-images",))   # {번호: 저장할 파일 이름}
    path, note = attachments.keep(out_dir, names[번호], 서버가 준 이름, data)                # 남긴 경로 · 읽는 길을 이르는 말

``file_names`` 는 이번에 받는 것만이 아니라 파일로 남길 첨부 **전부**를 받는다 — 그래야 몇 번을 골라 받든 같은 이름으로 남는다. 이름이
겹치거나(윈도처럼 대소문자 · 끝의 점과 빈칸을 안 가린다) ``reserved`` 와 겹치면 모든 첨부에 「<번호>-」 를 붙이고, 아니면 ``safe_name`` 그대로다.

``note`` 는 빈 글자(머리로 못 가르는 꼴) · 평문이다 · DRM 에 감겼다(읽는 손이 받는다 · 감긴 한글 · 읽는 손이 안 받는 꼴 · 읽는 손이 곁에 없다)
가운데 하나다. 읽는 손이 받는 꼴은 형제 스킬 drm-office-read 의 ``$HANDLER`` 표를 그 자리에서 읽는다 — 여기 따로 적으면 그 표와 어긋난다.
"""

from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))                  # 파일 경로로 실려도 곁의 visible 을 찾는다
import visible  # noqa: E402 — 이 폴더를 넣은 뒤에 싣는다

# PLAIN_HEAD_EXTS 의 확장자인데 이 머리로 시작하지 않으면 DRM 에 감긴 것이다
PLAIN_HEADS = (b"%PDF", b"PK\x03\x04", b"\xd0\xcf\x11\xe0", b"{\\rtf")
# 감겼나를 머리로 가를 수 있는 확장자 — 읽는 손이 받는 꼴의 표가 아니다(그 표는 READER_TABLE)
PLAIN_HEAD_EXTS = frozenset({"pdf", "doc", "docx", "docm", "rtf", "xls", "xlsx", "xlsm", "ppt", "pptx", "pptm", "hwp", "hwpx"})
# 감긴 한글 — DRM 은 문서를 여는 앱이 푸는데 읽는 손은 오피스 앱만 태워, 한글은 풀 길이 없다
HWP_EXTS = frozenset({"hwp", "hwpx"})
UNSAFE_NAME = re.compile(r'[\\/:*?"<>|\x00-\x1f]')   # 윈도 파일 이름에 못 쓰는 글자
NO_NAME = "attachment"                               # 다듬고 나니 남은 글자가 없는 이름 대신 쓴다
READER_SKILL = "drm-office-read"
READER_TABLE = HERE.parents[1] / READER_SKILL / "scripts" / "office-read.ps1"   # 형제 스킬 — 스킬 홈에 나란히 깔린다
HANDLER_BLOCK = re.compile(r"^\$HANDLER\s*=\s*@\{(.*?)^\}", re.M | re.S)       # 읽는 손의 확장자 표 한 덩이
HANDLER_KEY = re.compile(r"'\.(\w+)'\s*=")                                      # 그 안의 열쇠 — 점 뒤의 확장자
PLAIN = "평문이다 — 보통 파서로 읽는다"
WRAPPED = "DRM 에 감겼다"


def safe_name(name: str) -> str:
    """서버가 준 첨부 이름 → 한 폴더 안의 파일 이름. 보이지 않는 문자와 맨 앞의 점은 걷고 금지 글자는 ``_`` 로 바꾼다 — 명령이 내는
    경로가 보이지 않는 문자를 걷은 글이라, 여기서도 걷어야 낸 경로와 남긴 파일이 같다."""
    cleaned = UNSAFE_NAME.sub("_", visible.invisible(name)[0]).strip().lstrip(".")
    return cleaned or NO_NAME


def _same(name: str) -> str:
    """두 파일 이름이 한 파일을 가리키나를 견주는 꼴 — 윈도는 대소문자와 끝의 점 · 빈칸을 안 가린다."""
    return name.casefold().rstrip(". ")


def file_names(names: dict[int, str], reserved: tuple[str, ...] = ()) -> dict[int, str]:
    """한 메일 · 글에서 파일로 남길 첨부 전부 ``{번호: 서버가 준 이름}`` → ``{번호: 저장할 파일 이름}`` — 계약은 머리말."""
    safe = {no: safe_name(name) for no, name in names.items()}
    seen = [_same(name) for name in safe.values()]
    if len(set(seen)) == len(seen) and not set(seen) & {_same(name) for name in reserved}:
        return safe
    return {no: f"{no}-{name}" for no, name in safe.items()}


def ext_of(name: str) -> str:
    """이름의 확장자 — 소문자, 점 없이. 없으면 빈 글자."""
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def wrapped(name: str, data: bytes) -> bool | None:
    """감겼으면 참 · 평문이면 거짓, 머리로 못 가르는 확장자면 None."""
    if ext_of(name) not in PLAIN_HEAD_EXTS:
        return None
    return not data.startswith(PLAIN_HEADS)


def reader_exts() -> frozenset[str] | None:
    """감긴 문서를 읽는 손이 받는 확장자(소문자, 점 없이). 그 손의 표를 못 읽거나 비었으면 None — 받는 꼴을 모른다."""
    try:
        source = READER_TABLE.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None
    block = HANDLER_BLOCK.search(source)
    exts = frozenset(ext.lower() for ext in HANDLER_KEY.findall(block.group(1))) if block else frozenset()
    return exts or None


def note(name: str, data: bytes) -> str:
    """받은 첨부 하나를 무엇으로 읽나 이르는 말 — 머리말의 여섯 가운데 하나."""
    state = wrapped(name, data)
    if state is None:
        return ""
    if not state:
        return PLAIN
    ext, takes = ext_of(name), reader_exts()
    if takes and ext in takes:
        return f"{WRAPPED} — 스킬 {READER_SKILL} 로 읽는다"
    if ext in HWP_EXTS:
        return f"{WRAPPED} — 감긴 한글(.{ext})은 풀어 읽을 손이 없어 이 PC 에서 글자를 못 뽑는다"
    if takes is None:
        return f"{WRAPPED} — 읽는 손(스킬 {READER_SKILL})이 이 스킬 곁에 없어 그 손이 받는 꼴인지 못 가렸다. 설치를 다시 돌린다"
    return f"{WRAPPED} — 읽는 손(스킬 {READER_SKILL})이 .{ext} 꼴을 안 받아 이 PC 에서 글자를 못 뽑는다"


def keep(out_dir: pathlib.Path, file_name: str, name: str, data: bytes) -> tuple[pathlib.Path, str]:
    """첨부 하나를 ``out_dir / file_name`` 에 남기고(폴더가 없으면 만든다) (경로, ``note``)를 낸다. 확장자는 서버가 준 ``name`` 에서 읽는다."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / file_name
    path.write_bytes(data)
    return path, note(name, data)
