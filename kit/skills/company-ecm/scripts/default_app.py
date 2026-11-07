"""확장자의 기본 앱(Windows 「항상 이 앱 사용」)을 보고, 비어 있을 때만 깔린 앱으로 채우는 손 — 표준 라이브러리만 쓰는 파일 하나.

무엇을 하나
    ECM 에이전트는 받은 파일을 그 확장자의 기본 앱으로 연다. 기본 앱이 안 정해진 확장자면 Windows 가 「어떤 앱으로
    열까요」 창만 띄우고 파일은 안 열린다. 이 파일은 열기 전에 그 자리를 보고(``state``), 비었으면 깔린 앱의 ProgId 를
    Windows 가 받아 주는 해시와 함께 적는다(``ensure``). **이미 고른 값은 덮지 않는다** — 쓰는 사람이 고른 앱이다.

어떻게 부르나::

        import default_app

        st = default_app.state(".docx")          # Choice — progid(빈 글자면 안 정해짐) · where(UserChoice · UserChoiceLatest)
        got = default_app.ensure(".docx")        # Ensured — 이미 있음 · 새로 적음. 못 적으면 DefaultAppNeeded
        default_app.preflight()                   # Preflight — 이 PC 에 Windows 가 적어 둔 해시를 우리 계산으로 다시 지은 셈

무엇을 내나
    ``ensure`` 는 ``Ensured(progid, written)`` 을 낸다 — ``written`` 이 참이면 이번에 적었다. 사람이 한 번 골라야 하는
    자리(깔린 앱이 없다 · Windows 가 쓰기를 막았다 · 적었는데 Windows 가 안 받았다 · 이 PC 의 해시 계산이 다르다)는
    ``DefaultAppNeeded`` 다 — 메시지가 사람에게 할 말이다.

Windows 가 받아 주는 값 — 어기면 조용히 망가진다
    * ``HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\.<확장자>\\UserChoice`` 의 ``ProgId`` 와
      ``Hash`` 둘이 한 벌이다. 해시가 틀리면 Windows 는 그 키를 지우고 고르는 창으로 돌아간다 — 오류는 안 낸다
    * 해시의 재료는 ``확장자 + 사용자 SID + ProgId + 그 키를 마지막으로 쓴 시각(분으로 내림 · FILETIME 16 자리 hex)
      + shell32.dll 이 든 「User Choice set via Windows User Experience {…}」 글`` 을 소문자로 이은 것이다. 그래서 키를 쓴
      분과 해시의 분이 같아야 한다 — 분 경계 직전이면 기다렸다 쓰고, 쓴 뒤 키의 시각으로 다시 지어 맞춘다
    * 계산의 꼴은 DanysysTeam/PS-SFTA 의 ``SFTA.ps1`` ``Get-Hash`` (커밋 22a32292e576afc976a1167d92b50741ef523066)가 공개한
      것을 따랐다. 그 저장소는 라이선스 표시가 없어 코드는 옮기지 않았다 — 같은 셈을 부호 없는 32 비트 산술로 우리가 다시 지었다
    * UserChoice 보호 드라이버(UCPD)는 일부 확장자(``.pdf`` 로 알려짐)의 이 키 쓰기를 막는다. 막히면 ``PermissionError`` 가
      나고, 그 확장자는 사람이 한 번 「항상 이 앱 사용」을 고르게 이끈다
    * 적은 뒤 Windows 가 그 확장자를 정말 그 ProgId 로 푸는지 ``AssocQueryStringW`` 로 묻는다 — 안 받았으면 이번에 적은
      키를 걷고 ``DefaultAppNeeded`` 를 낸다

기본 앱이 서 있어도 고르는 창이 뜨는 자리
    * 그 확장자를 열 수 있다고 등록된 앱(``HKCR\\.<확장자>\\OpenWithProgids``) 가운데 ``HKCU\\…\\ApplicationAssociationToasts`` 에
      ``<ProgId>_<확장자>`` 값이 없는 앱이 있으면, Windows 는 그 앱을 새로 깔린 앱으로 보고 그 확장자를 열 때 「이 파일을 열 때
      사용할 앱」 창을 한 번 띄운다(새 앱 옆에 「새로 만들기」가 붙는다). 그 창이 떠 있는 동안 문서는 안 열린다
    * 그래서 ``ensure`` 는 기본 앱이 선 확장자에서, 빠진 앱의 값만 DWORD 0 으로 더한다 — Windows 가 그 앱을 보인 뒤 적는 값과
      같은 꼴이다. 해시가 없는 키라 Windows 가 막지 않는다. 있는 값과 기본 앱은 건드리지 않는다. 그 확장자에서 「새 앱이
      깔렸다」 알림만 안 보이게 된다
"""

from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes as wt
import hashlib
import os
import pathlib
import struct
import time
import winreg
from dataclasses import dataclass

FILE_EXTS = r"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts"
# 쓰는 사람의 고름이 놓이는 자리 — 앞이 지금 판, 뒤는 새 판 Windows 가 쓰는 자리다. 둘 중 하나라도 ProgId 가 있으면 고른 것이다
CHOICE_KEYS = ("UserChoice", "UserChoiceLatest")
CHOICE_LATEST_PROGID_SUBKEY = "ProgId"     # UserChoiceLatest 는 ProgId 를 하위 키에 든다
# Windows 가 「이 앱은 사람에게 보였다」를 적는 자리 — 값 이름은 <ProgId>_<확장자>, 값은 DWORD 0
TOASTS = r"Software\Microsoft\Windows\CurrentVersion\ApplicationAssociationToasts"
TOAST_SEEN = 0

# 확장자마다 깔렸으면 고를 ProgId — 앞에 선 것부터. 오피스는 그 앱이 깔릴 때 등록하는 이름이고, PDF 는 Acrobat 둘이다.
# 표에 없는 확장자는 이 손이 고를 앱을 모른다 — 사람이 고른다
PROGIDS = {
    ".doc": ("Word.Document.8",), ".docx": ("Word.Document.12",), ".rtf": ("Word.RTF.8",),
    ".xls": ("Excel.Sheet.8",), ".xlsx": ("Excel.Sheet.12",), ".xlsm": ("Excel.SheetMacroEnabled.12",), ".csv": ("Excel.CSV",),
    ".ppt": ("PowerPoint.Show.8",), ".pptx": ("PowerPoint.Show.12",),
    ".pdf": ("AcroExch.Document.DC", "Acrobat.Document.DC"),
}

EXPERIENCE_MARK = "User Choice set via Windows User Experience"
EXPERIENCE_FALLBACK = EXPERIENCE_MARK + " {D18B6DD5-6124-4341-9318-804003BAFA0B}"
MINUTE_TICKS = 60 * 10_000_000            # FILETIME 은 100 ns 단위다
LATE_SECOND = 57                           # 이 초를 넘겼으면 다음 분까지 기다렸다 쓴다 — 쓰는 사이 분이 넘어가지 않게
WRITE_TRIES = 3

U32 = 0xFFFFFFFF
ASSOCSTR_PROGID = 20
ASSOCSTR_FRIENDLYAPPNAME = 4
SHCNE_ASSOCCHANGED = 0x08000000
TOKEN_QUERY = 0x0008
TOKEN_USER = 1


class DefaultAppNeeded(Exception):
    """사람이 그 확장자의 기본 앱을 한 번 골라야 한다. 메시지가 사람에게 할 말이다."""


@dataclass(frozen=True)
class Choice:
    """그 확장자의 지금 고름. ``progid`` 가 빈 글자면 안 정해졌다. ``where`` 는 그 값이 놓인 키 이름이다."""
    ext: str
    progid: str
    where: str = ""


@dataclass(frozen=True)
class Ensured:
    progid: str
    written: bool


@dataclass(frozen=True)
class Preflight:
    """이 PC 에 Windows 가 적어 둔 UserChoice 를 우리 계산으로 다시 지은 셈 — ``total`` 중 ``matched`` 가 같았다."""
    total: int
    matched: int

    @property
    def algorithm_differs(self) -> bool:
        """하나도 안 맞으면 이 PC 의 Windows 는 다른 계산을 쓴다. 몇은 맞고 몇은 다르면 계산은 같고 그 키들이 옮겨 적힌 것이다."""
        return self.total > 0 and self.matched == 0


# ── 해시 ─────────────────────────────────────────────────────────────────

def _words(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _hi(x: int) -> int:
    return (x & U32) >> 16


def _pass_one(data: bytes, rounds: int, seed_a: int, seed_b: int) -> tuple[int, int]:
    mul_a, mul_b = ((seed_a | 1) + 0x69FB0000) & U32, ((seed_b | 1) + 0x13DB0000) & U32
    carry = acc = 0
    for i in range(rounds):
        lo, hi = _words(data, 8 * i), _words(data, 8 * i + 4)
        x = (lo + carry) & U32
        x = (x * mul_a - 0x10FA9605 * _hi(x)) & U32
        x = (0x79F8A395 * x + 0x689B6B9F * _hi(x)) & U32
        mixed = (0xEA970001 * x - 0x3C101569 * _hi(x)) & U32
        y = (mixed + hi) & U32
        y = (y * mul_b - 0x3CE8EC25 * _hi(y)) & U32
        y = (0x59C3AF2D * y - 0x2232E0F1 * _hi(y)) & U32
        carry = (0x1EC90001 * y + 0x35BD1EC9 * _hi(y)) & U32
        acc = (acc + mixed + carry) & U32
    return carry, acc


def _pass_two(data: bytes, rounds: int, seed_a: int, seed_b: int) -> tuple[int, int]:
    mul_a, mul_b = (seed_a | 1) & U32, (seed_b | 1) & U32
    carry = acc = 0
    for i in range(rounds):
        lo, hi = _words(data, 8 * i), _words(data, 8 * i + 4)
        x = ((lo + carry) * mul_a) & U32
        x = (0xB1110000 * x - 0x30674EEF * _hi(x)) & U32
        x = (0x5B9F0000 * x - 0x78F7A461 * _hi(x)) & U32
        x = (0x12CEB96D * _hi(x) - 0x46930000 * x) & U32
        mixed = (0x1D830000 * x + 0x257E1D83 * _hi(x)) & U32
        y = (mul_b * (mixed + hi)) & U32
        y = (0x16F50000 * y - 0x5D8BE90B * _hi(y)) & U32
        y = (0x96FF0000 * y - 0x2C7C6901 * _hi(y)) & U32
        y = (0x2B890000 * y + 0x7C932B89 * _hi(y)) & U32
        carry = (0x9F690000 * y - 0x405B6097 * _hi(y)) & U32
        acc = (acc + carry + mixed) & U32
    return carry, acc


def choice_hash(ext: str, sid: str, progid: str, stamp: str, experience: str) -> str:
    """UserChoice 의 ``Hash`` 값(base64 여덟 바이트). ``stamp`` 는 키를 쓴 분의 FILETIME 16 자리 hex 다. 너무 짧은 재료면 빈 글자."""
    text = f"{ext}{sid}{progid}{stamp}{experience}".lower()
    data = text.encode("utf-16-le") + b"\0\0"
    size = len(data)
    words = (size >> 2) - 1 + (1 if size & 4 == 0 else 0)
    if words <= 1:
        return ""
    rounds = ((words - 2) >> 1) + 1
    digest = hashlib.md5(data).digest()
    seed_a, seed_b = _words(digest, 0), _words(digest, 4)
    one = _pass_one(data, rounds, seed_a, seed_b)
    two = _pass_two(data, rounds, seed_a, seed_b)
    return base64.b64encode(struct.pack("<II", one[0] ^ two[0], one[1] ^ two[1])).decode("ascii")


def minute_stamp(filetime: int) -> str:
    """FILETIME(100 ns · 1601 기준)을 분으로 내려 16 자리 소문자 hex 로."""
    return f"{filetime - filetime % MINUTE_TICKS:016x}"


def now_filetime() -> int:
    return int(time.time() * 10_000_000) + 116444736000000000


# ── 이 PC 의 재료 ────────────────────────────────────────────────────────

def user_sid() -> str:
    """이 프로세스를 돌리는 사용자의 SID(소문자) — 토큰에서 읽는다. 같은 이름의 다른 계정과 헷갈리지 않는다."""
    advapi, kernel = ctypes.WinDLL("advapi32", use_last_error=True), ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wt.HANDLE
    kernel.CloseHandle.argtypes = [wt.HANDLE]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    advapi.OpenProcessToken.argtypes = [wt.HANDLE, wt.DWORD, ctypes.POINTER(wt.HANDLE)]
    advapi.GetTokenInformation.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.POINTER(wt.DWORD)]
    advapi.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wt.LPWSTR)]
    token = wt.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)):
        raise OSError(ctypes.get_last_error(), "OpenProcessToken")
    try:
        need = wt.DWORD()
        advapi.GetTokenInformation(token, TOKEN_USER, None, 0, ctypes.byref(need))
        buf = ctypes.create_string_buffer(need.value)
        if not advapi.GetTokenInformation(token, TOKEN_USER, buf, need, ctypes.byref(need)):
            raise OSError(ctypes.get_last_error(), "GetTokenInformation")
        sid_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
        text = wt.LPWSTR()
        if not advapi.ConvertSidToStringSidW(ctypes.c_void_p(sid_ptr), ctypes.byref(text)):
            raise OSError(ctypes.get_last_error(), "ConvertSidToStringSidW")
        try:
            return text.value.lower()
        finally:
            kernel.LocalFree(ctypes.cast(text, ctypes.c_void_p))
    finally:
        kernel.CloseHandle(token)


def user_experience() -> str:
    """shell32.dll 이 든 「User Choice set via Windows User Experience {…}」 글. 못 찾으면 알려진 값."""
    windir = pathlib.Path(os.environ.get("SystemRoot", r"C:\Windows"))
    mark = EXPERIENCE_MARK.encode("utf-16-le")
    for dll in (windir / "SysWOW64" / "shell32.dll", windir / "System32" / "shell32.dll"):
        try:
            data = dll.read_bytes()
        except OSError:
            continue
        start = data.find(mark)
        if start < 0:
            continue
        end = data.find("}".encode("utf-16-le"), start)
        if end > start:
            return data[start:end + 2].decode("utf-16-le")
    return EXPERIENCE_FALLBACK


def _progid_installed(progid: str) -> bool:
    try:
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid))
        return True
    except OSError:
        return False


def resolved_progid(ext: str) -> str:
    """Windows 가 지금 그 확장자를 어느 ProgId 로 푸는가(``AssocQueryStringW`` · ASSOCSTR_PROGID). 못 풀면 빈 글자."""
    shlwapi = ctypes.WinDLL("shlwapi")
    shlwapi.AssocQueryStringW.argtypes = [wt.DWORD, ctypes.c_int, wt.LPCWSTR, wt.LPCWSTR, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    shlwapi.AssocQueryStringW.restype = ctypes.c_long
    size = wt.DWORD(512)
    buf = ctypes.create_unicode_buffer(size.value)
    hr = shlwapi.AssocQueryStringW(0, ASSOCSTR_PROGID, ext, None, buf, ctypes.byref(size))
    return buf.value if hr == 0 else ""


def app_name(progid: str) -> str:
    """ProgId 의 사람이 읽는 앱 이름(``AssocQueryStringW`` · ASSOCSTR_FRIENDLYAPPNAME) — 고르는 창에 보이는 그 이름. 못 얻으면 ProgId."""
    shlwapi = ctypes.WinDLL("shlwapi")
    shlwapi.AssocQueryStringW.argtypes = [wt.DWORD, ctypes.c_int, wt.LPCWSTR, wt.LPCWSTR, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    shlwapi.AssocQueryStringW.restype = ctypes.c_long
    size = wt.DWORD(512)
    buf = ctypes.create_unicode_buffer(size.value)
    hr = shlwapi.AssocQueryStringW(0, ASSOCSTR_FRIENDLYAPPNAME, progid, None, buf, ctypes.byref(size))
    return buf.value if hr == 0 and buf.value else progid


def _notify_assoc_changed() -> None:
    shell32 = ctypes.WinDLL("shell32")
    shell32.SHChangeNotify.argtypes = [ctypes.c_long, wt.UINT, ctypes.c_void_p, ctypes.c_void_p]
    shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, 0, None, None)


# ── 보기 · 채우기 ────────────────────────────────────────────────────────

def _read_value(path: str, name: str) -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value or "")
    except OSError:
        return ""


def state(ext: str, *, base: str = FILE_EXTS) -> Choice:
    """그 확장자의 지금 고름 — 쓰지 않는다. ``base`` 는 FileExts 자리다(검사가 버릴 자리를 줄 때만 바꾼다)."""
    ext = normalize(ext)
    for where in CHOICE_KEYS:
        path = rf"{base}\{ext}\{where}"
        progid = _read_value(path, "ProgId") or _read_value(rf"{path}\{CHOICE_LATEST_PROGID_SUBKEY}", "ProgId")
        if progid:
            return Choice(ext, progid, where)
    return Choice(ext, "")


def preflight() -> Preflight:
    """이 PC 의 UserChoice 마다 키의 마지막 쓴 시각으로 해시를 다시 지어 Windows 가 적은 값과 견준다 — 읽기만 한다."""
    sid, experience = user_sid(), user_experience()
    total = matched = 0
    try:
        root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, FILE_EXTS)
    except OSError:
        return Preflight(0, 0)
    with root:
        index = 0
        while True:
            try:
                ext = winreg.EnumKey(root, index)
            except OSError:
                break
            index += 1
            try:
                with winreg.OpenKey(root, rf"{ext}\UserChoice") as key:
                    progid = str(winreg.QueryValueEx(key, "ProgId")[0])
                    written = str(winreg.QueryValueEx(key, "Hash")[0])
                    stamp = minute_stamp(winreg.QueryInfoKey(key)[2])
            except OSError:
                continue
            total += 1
            matched += choice_hash(ext, sid, progid, stamp, experience) == written
    return Preflight(total, matched)


def normalize(ext: str) -> str:
    ext = ext.strip().lower()
    if not ext.startswith("."):
        ext = "." + ext
    if len(ext) < 2 or any(c in ext for c in "\\/ ") or ext.count(".") != 1:
        raise ValueError(f"확장자가 아니다: {ext!r}")
    return ext


def pick_progid(ext: str) -> str:
    """그 확장자에 깔린 앱의 ProgId — 표의 앞에 선 것부터. 깔린 것이 없으면 빈 글자."""
    for progid in PROGIDS.get(normalize(ext), ()):
        if _progid_installed(progid):
            return progid
    return ""


def write_choice(ext: str, progid: str, *, base: str = FILE_EXTS, sid: str | None = None,
                 experience: str | None = None) -> str:
    """UserChoice 를 ProgId · Hash 한 벌로 적고, 키의 시각으로 다시 지어 맞을 때까지 고쳐 쓴다. 적은 해시를 낸다.

    이미 고른 값이 있는지는 보지 않는다 — 부르는 쪽(``ensure``)이 본다. 쓰기가 막히면 ``PermissionError`` 가 그대로 난다.
    """
    ext = normalize(ext)
    sid = sid or user_sid()
    experience = experience or user_experience()
    if time.localtime().tm_sec >= LATE_SECOND:
        time.sleep(61 - time.localtime().tm_sec)
    path = rf"{base}\{ext}\UserChoice"
    written = ""
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as key:
        winreg.SetValueEx(key, "ProgId", 0, winreg.REG_SZ, progid)
        stamp = minute_stamp(now_filetime())
        for _ in range(WRITE_TRIES):
            written = choice_hash(ext, sid, progid, stamp, experience)
            winreg.SetValueEx(key, "Hash", 0, winreg.REG_SZ, written)
            stamp = minute_stamp(winreg.QueryInfoKey(key)[2])
            if choice_hash(ext, sid, progid, stamp, experience) == written:
                break
    return written


def _remove_choice(ext: str, base: str = FILE_EXTS) -> None:
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"{base}\{ext}\UserChoice")
    except OSError:
        pass


def registered_progids(ext: str) -> list[str]:
    """그 확장자를 열 수 있다고 등록된 앱의 ProgId(``HKCR\\.<확장자>\\OpenWithProgids`` 의 값 이름) — 읽기만 한다."""
    names: list[str] = []
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"{normalize(ext)}\OpenWithProgids") as key:
            index = 0
            while True:
                try:
                    name = winreg.EnumValue(key, index)[0]
                except OSError:
                    break
                index += 1
                if name:
                    names.append(name)
    except OSError:
        pass
    return names


def quiet_new_apps(ext: str, *, toasts: str = TOASTS) -> list[str]:
    """그 확장자에 등록된 앱 가운데 「보였다」 값이 없는 앱만 값을 더한다 — 더한 값 이름을 낸다. 있는 값은 안 건드린다.

    ``toasts`` 는 검사가 버릴 자리를 줄 때만 바꾼다.
    """
    ext = normalize(ext)
    added: list[str] = []
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, toasts, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE) as key:
        for progid in registered_progids(ext):
            name = f"{progid}_{ext}"
            try:
                winreg.QueryValueEx(key, name)
            except FileNotFoundError:
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, TOAST_SEEN)
                added.append(name)
    return added


def ensure(ext: str, *, base: str = FILE_EXTS, toasts: str = TOASTS) -> Ensured:
    """그 확장자의 기본 앱이 서 있게 한다 — 있으면 그대로 두고, 없으면 깔린 앱으로 적은 뒤 Windows 가 받았나 본다. 기본 앱이
    섰으면 새 앱 알림 창이 그 열기를 막지 않게 ``quiet_new_apps`` 를 부른다.

    사람이 골라야 하면 ``DefaultAppNeeded``. ``base`` · ``toasts`` 는 검사가 버릴 자리를 줄 때만 바꾼다.
    """
    ext = normalize(ext)
    got = _ensure_choice(ext, base)
    quiet_new_apps(ext, toasts=toasts)
    return got


def _ensure_choice(ext: str, base: str) -> Ensured:
    now = state(ext, base=base)
    if now.progid:
        return Ensured(now.progid, False)
    progid = pick_progid(ext)
    if not progid:
        raise DefaultAppNeeded(
            f"{ext} 파일을 열 앱이 정해져 있지 않고, 이 손이 고를 앱도 이 PC 에 없다 — 탐색기에서 {ext} 파일 하나를 오른쪽 단추로 눌러 "
            "「연결 프로그램 → 다른 앱 선택」에서 앱을 고르고 「항상 이 앱 사용」을 누른 뒤 다시 연다")
    name = app_name(progid)
    check = preflight()
    if check.algorithm_differs:
        raise DefaultAppNeeded(
            f"이 PC 의 Windows 는 기본 앱 값을 이 손이 아는 것과 다르게 지어서(다시 지은 해시 {check.total} 개 중 0 개가 같다) 대신 "
            f"적지 않았다 — {ext} 파일 하나를 오른쪽 단추로 눌러 「연결 프로그램 → 다른 앱 선택」에서 {name} 을(를) 고르고 "
            "「항상 이 앱 사용」을 누른 뒤 다시 연다")
    try:
        write_choice(ext, progid, base=base)
    except PermissionError as exc:
        raise DefaultAppNeeded(
            f"Windows 가 {ext} 의 기본 앱 쓰기를 막았다(UserChoice 보호) — {ext} 파일 하나를 오른쪽 단추로 눌러 「연결 프로그램 → "
            f"다른 앱 선택」에서 {name} 을(를) 고르고 「항상 이 앱 사용」을 누른 뒤 다시 연다") from exc
    _notify_assoc_changed()
    if resolved_progid(ext).lower() != progid.lower():
        _remove_choice(ext, base)
        raise DefaultAppNeeded(
            f"{ext} 의 기본 앱을 {name}({progid}) 로 적었지만 Windows 가 받지 않아 걷었다 — {ext} 파일 하나를 오른쪽 단추로 눌러 「연결 "
            "프로그램 → 다른 앱 선택」에서 앱을 고르고 「항상 이 앱 사용」을 누른 뒤 다시 연다")
    return Ensured(progid, True)
