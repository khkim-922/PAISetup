"""첨부 가름 — 받은 첨부 하나를 어떤 이름으로 남기고, 무엇으로 읽으라고 이르나를 가르는 한 손. 이 스킬의 명령(``mail.py``)과 형제 스킬
company-board 의 명령이 함께 쓴다 — 가름이 한 벌이라 한쪽만 고쳐져 어긋나는 일이 없다. 서버에 묻지 않는다 — 바이트는 부르는 쪽의 앱 손이
받아 넘긴다. 문서함(ECM) 쪽지의 이름 꼴과 열쇠는 곁의 ``inbox`` 가 든다(``ECM_ATTACHMENT`` · ``ecm_note_key``).

부르는 꼴::

    import attachments
    names = attachments.file_names({번호: 서버가 준 이름, …}, reserved=("body-images",))   # {번호: 저장할 파일 이름}
    path, note = attachments.keep(out_dir, names[번호], 서버가 준 이름, data)                # 남긴 경로 · 읽는 길을 이르는 말

``file_names`` 는 파일로 남길 첨부 **전부**를 받는다(이번에 받는 것만이 아니라) — 한 메일 · 글의 첨부는 몇 번을 골라 받든 같은 이름으로
남는다. 이름이 서로 다르면 서버가 준 이름을 다듬은 것(``safe_name``) 그대로고, 둘이 겹치거나(대소문자 · 끝의 점과 빈칸을 안 가린다 —
윈도 파일 이름이 그렇다) ``reserved``(그 폴더에 부르는 쪽이 따로 쓰는 이름)와 겹치면 그 메일 · 글의 첨부 모두에 「<번호>-」 를 붙인다 —
번호가 달라 서로 안 겹친다.

``note`` 는 여섯 가운데 하나다 — 빈 글자(평문 머리로 가를 수 없는 꼴) · 평문이다 · DRM 에 감겼고 스킬 drm-office-read 로 읽는다 · DRM 에
감긴 한글이라 읽을 손이 없다 · DRM 에 감겼는데 읽는 손이 그 꼴을 안 받는다 · DRM 에 감겼는데 읽는 손이 곁에 없어 받는 꼴인지 못 가렸다.

**읽는 손이 받는 꼴은 그 손의 표가 든다** — 형제 스킬 drm-office-read 의 ``office-read.ps1`` 에 선 ``$HANDLER``(확장자 → 앱)를 그 자리에서
읽는다(DRM 길잡이 훅도 같은 표를 같은 꼴로 읽는다). 여기 따로 적으면 읽는 손이 꼴을 늘리거나 줄인 날 이 말만 낡아, 안 받는 꼴을 그 손으로
넘긴다. 그 파일이 곁에 없거나 표를 못 읽으면 「받는 꼴」을 지어내지 않는다 — 감긴 첨부마다 못 가렸다고 말한다(한글은 표와 상관없이 제 말이다).
표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))                  # 파일 경로로 실려도 곁의 visible 을 찾는다
import visible  # noqa: E402 — 이 폴더를 넣은 뒤에 싣는다

# 평문 형식의 머리 — PLAIN_HEAD_EXTS 의 확장자인데 이 머리가 아니면 DRM 에 감긴 것이다(스킬 drm-office-read 1 절)
PLAIN_HEADS = (b"%PDF", b"PK\x03\x04", b"\xd0\xcf\x11\xe0", b"{\\rtf")
# 평문이면 PLAIN_HEADS 로 시작하는 문서 꼴 — 감겼나를 머리로 가를 수 있는 확장자다. 읽는 손이 받는 꼴의 표가 아니다(그 표는 READER_TABLE)
PLAIN_HEAD_EXTS = frozenset({"pdf", "doc", "docx", "docm", "rtf", "xls", "xlsx", "xlsm", "ppt", "pptx", "pptm", "hwp", "hwpx"})
# 감긴 한글 문서 — DRM 을 풀어 주는 것은 그 문서를 여는 앱인데, 감긴 문서를 읽는 손(drm-office-read)은 오피스 앱만 태워 한글을 열 앱이 없다
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
    """서버가 준 첨부 이름을 한 폴더 안의 파일 이름으로 — 보이지 않는 문자(폭 없는 문자 · 방향 뒤집기)는 걷고, 경로 가름 · 금지 글자는
    바꾸고, 맨 앞의 점은 걷는다. 보이지 않는 문자를 여기서 걷는 것은 명령이 내는 경로가 그 문자를 걷은 글이기 때문이다 — 파일 이름에
    남으면 낸 경로와 남긴 파일이 달라진다."""
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
    """평문 머리로 가를 수 있는 꼴(``PLAIN_HEAD_EXTS``)이면 감겼나(참) · 평문인가(거짓), 그 밖의 확장자는 None."""
    if ext_of(name) not in PLAIN_HEAD_EXTS:
        return None
    return not data.startswith(PLAIN_HEADS)


def reader_exts() -> frozenset[str] | None:
    """감긴 문서를 읽는 손(형제 스킬 drm-office-read)이 받는 확장자 — 소문자, 점 없이. 그 손의 표(``READER_TABLE`` 의 ``$HANDLER``)를
    그 자리에서 읽는다. 파일이 없거나 표에서 확장자를 하나도 못 읽으면 None — 받는 꼴을 모른다."""
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
    """받은 첨부 하나를 ``out_dir`` 에 ``file_name``(``file_names`` 가 낸 것)으로 남기고 (경로, ``note``)를 낸다. ``name`` 은 서버가 준
    이름이다 — 확장자를 거기서 읽는다. 폴더가 없으면 만든다."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / file_name
    path.write_bytes(data)
    return path, note(name, data)
