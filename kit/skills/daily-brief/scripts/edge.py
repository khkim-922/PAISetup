"""로그인 Edge 의 열린 보고 창과 주고받는다 — 일일 보고 손들이 Edge 에 닿는 한 자리. 디버깅 포트(`port`)에 새 탭을 열고(`open_tab`),
CDP 웹소켓 하나(`Cdp`)로 열린 보고 창(file: 탭 — `page` · `brief_tabs`)에 붙어 그 창의 저장소(localStorage)를 읽고 쓰고(`Tab`), 읽은 칸을
값으로 푼다(`cells` · `stored` · `pressed_at`). 부르는 곳은 늘 이 PC 의 디버깅 포트(`brief_const.EDGE_HOST`)다 — 메일함에 닿지 않는다.

창의 저장소는 file: 창끼리 하나다(Chromium) — 어느 보고 창에 붙어도 같은 칸을 읽는다. 무엇을 지키고 왜 그런가는 `references/DESIGN.md` 가 든다.
"""

from __future__ import annotations

import base64
import contextlib
import datetime as dt
import hashlib
import http.client
import json
import os
import pathlib
import re
import socket
import struct
import sys
import time
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 brief_const.py · brief_files.py — `-I` 로 돌아도 싣는다
import brief_const as C  # noqa: E402
from brief_files import is_window  # noqa: E402

TIMEOUT_S = 5
EDGE_TIMEOUT_S = 2                               # 새 탭을 청하는 한 번의 시한 — 못 받으면 기본 브라우저로 간다
LOAD_WAIT_S = 3                                  # 뒤 탭으로 연 보고 창이 file: 문서가 되기를 기다리는 끝
LOAD_STEP_S = 0.1

# 창의 localStorage 를 읽고 쓰는 식 — 창에서 받은 글로 식을 짓지 않는다. 쓰는 식은 이 손이 지은 JSON 한 덩이만 인자로 받는다
HAND_KEYS = [C.DONE_PREFIX, C.UNQUIET_PREFIX, C.TIMES_KEY, C.CAL_PREFIX, C.AWAY_KEY, C.ASK_KEY, C.APPR_PREFIX]   # 거두는 손 · 넣는 손이 읽는 칸


def read_expr(prefixes: list[str]) -> str:
    """열쇠가 `prefixes` 의 하나로 시작하는 칸을 (열쇠, 값)의 JSON 으로 내는 식."""
    return ("JSON.stringify(Object.keys(localStorage).filter(function (k) { return %s.some(function (p) { return k.indexOf(p) === 0; }); })"
            ".map(function (k) { return [k, localStorage.getItem(k)]; }))") % json.dumps(prefixes)


WRITE_EXPR = ("(function (rows) { rows.forEach(function (r) { localStorage.setItem(r[0], r[1]); });"
              " window.dispatchEvent(new StorageEvent(\"storage\")); return rows.length; })(%s)")
QUIET_WRITE = "(function (rows) { rows.forEach(function (r) { localStorage.setItem(r[0], r[1]); }); return rows.length; })(%s)"
# ↑ 숨 표처럼 창이 다시 그릴 까닭이 없는 쓰기 — 저장소 사건을 안 일으킨다(그 창은 2초마다 스스로 숨 표를 읽는다)
SWAP_WRITE = ("(function (k, was, now) { if (localStorage.getItem(k) !== was) return false; localStorage.setItem(k, now); return true; })"
              "(%s, %s, %s)")
# ↑ 누름을 맡는 쓰기 — 창이 그 사이 맺었으면 안 맡는다(맺은 누름을 손이 하면 「못 열었다 · 못 맡김」 뒤에 일이 된다)
WHERE_EXPR = "location.protocol"
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"   # RFC 6455 의 고정값 — 손잡기 답을 재는 데 쓴다
BROWSER_PATH = re.compile(r"^ws://[^/]+(/devtools/browser/[A-Za-z0-9._-]+)$")


class EdgeGone(Exception):
    """로그인 Edge 에 못 닿았거나 그 답이 꼴이 아니다 — 표시는 그 Edge 에 남는다."""


class NoEdge(EdgeGone):
    """처음부터 로그인 Edge 에 못 닿았다(주고받다 멈춘 것과 다른 끝) — 표시는 그 Edge 에 남는다."""


class NoWindow(Exception):
    """열린 보고 창(file: 탭)이 없다 — 새로 열지 않는 부름(창의 문 `window_door` 의 고름 읽기 · 돌려 적기)이 받는다."""


# ── 디버깅 포트 — 브라우저 자리의 CDP 웹소켓 하나 ─────────────────────────────

class Cdp:
    """부르는 곳은 늘 `brief_const.EDGE_HOST` 다 — 디버깅 포트의 답에 든 주소에서는 길(path)만 쓴다."""

    def __init__(self, port: int):
        self.next_id = 0
        self.rest = b""
        try:
            conn = http.client.HTTPConnection(C.EDGE_HOST, port, timeout=TIMEOUT_S)
            try:
                conn.request("GET", "/json/version")
                resp = conn.getresponse()
                info = json.loads(resp.read().decode("utf-8")) if resp.status == 200 else {}
            finally:
                conn.close()
            m = BROWSER_PATH.match(str(info.get("webSocketDebuggerUrl") or ""))
            if not m:
                raise EdgeGone("디버깅 포트가 브라우저 자리를 안 댔다")
            self.sock = socket.create_connection((C.EDGE_HOST, port), timeout=TIMEOUT_S)
            self._handshake(port, m.group(1))
        except (OSError, http.client.HTTPException, ValueError) as exc:
            raise EdgeGone(str(exc)) from exc

    def _handshake(self, port: int, path: str) -> None:
        """Origin 을 안 싣는다 — Chromium 은 Origin 이 든 손잡기만 --remote-allow-origins 로 거른다."""
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        self.sock.sendall((f"GET {path} HTTP/1.1\r\nHost: {C.EDGE_HOST}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode("ascii"))
        while b"\r\n\r\n" not in self.rest:
            self._fill()
        head, self.rest = self.rest.split(b"\r\n\r\n", 1)
        lines = head.decode("latin-1").split("\r\n")
        want = base64.b64encode(hashlib.sha1((key + WS_GUID).encode("ascii")).digest()).decode("ascii")
        accept = [v.split(":", 1)[1].strip() for v in lines[1:] if v.lower().startswith("sec-websocket-accept:")]
        if lines[0].split(" ")[1:2] != ["101"] or accept != [want]:
            raise EdgeGone(f"웹소켓 손잡기를 안 받았다({lines[0][:60]})")

    def _fill(self) -> None:
        """웹소켓에서 받은 바이트를 남은 몫에 덧붙인다 — 끊겼으면 EdgeGone."""
        chunk = self.sock.recv(65536)
        if not chunk:
            raise EdgeGone("웹소켓이 끊겼다")
        self.rest += chunk

    def _take(self, n: int) -> bytes:
        """받은 바이트의 앞 `n` 바이트를 떼어 낸다 — 모자라면 더 받는다."""
        while len(self.rest) < n:
            self._fill()
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def _send(self, opcode: int, payload: bytes) -> None:
        """보내는 틀은 늘 가린다(mask) — RFC 6455 가 손님 쪽에 시키는 것이다."""
        mask = os.urandom(4)
        n = len(payload)
        if n < 126:
            size = bytes([0x80 | n])
        elif n < 1 << 16:
            size = bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            size = bytes([0x80 | 127]) + struct.pack(">Q", n)
        self.sock.sendall(bytes([0x80 | opcode]) + size + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def _message(self) -> str:
        """웹소켓 글 하나를 받는다 — 조각을 잇고, 핑에는 퐁으로 답하고, 닫힘이면 EdgeGone."""
        parts: list[bytes] = []
        while True:
            b0, b1 = self._take(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._take(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._take(8))[0]
            mask = self._take(4) if b1 & 0x80 else b""
            data = self._take(n)
            if mask:
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            opcode = b0 & 0x0F
            if opcode == 0x8:
                raise EdgeGone("Edge 가 웹소켓을 닫았다")
            if opcode == 0x9:
                self._send(0xA, data)
            elif opcode in (0x0, 0x1, 0x2):
                parts.append(data)
                if b0 & 0x80:
                    return b"".join(parts).decode("utf-8")

    def call(self, method: str, params: dict | None = None, session: str | None = None) -> dict:
        """명령 하나를 보내고 같은 번호의 답을 기다린다 — 사이에 오는 사건은 버린다. CDP 가 오류로 답하면 EdgeGone."""
        self.next_id += 1
        msg: dict = {"id": self.next_id, "method": method, "params": params or {}}
        if session:
            msg["sessionId"] = session
        try:
            self._send(0x1, json.dumps(msg).encode("utf-8"))
            while True:
                got = json.loads(self._message())
                if got.get("id") == self.next_id:
                    break
        except (OSError, ValueError) as exc:
            raise EdgeGone(f"{method}: {exc}") from exc
        if "error" in got:
            raise EdgeGone(f"{method}: {got['error']}")
        return got.get("result") or {}

    def evaluate(self, session: str, expr: str):
        """탭(`session`)에서 식 하나를 돌려 그 값을 낸다 — 식이 넘어지면 EdgeGone."""
        res = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True}, session)
        if "exceptionDetails" in res:
            raise EdgeGone("창에서 식이 넘어졌다")
        return (res.get("result") or {}).get("value")

    def close(self) -> None:
        """닫힘 틀을 보내고 소켓을 닫는다 — 이미 끊겼으면 그대로 둔다."""
        try:
            self._send(0x8, b"")
            self.sock.close()
        except OSError:
            pass


def port() -> int:
    """로그인 Edge 의 디버깅 포트 — `EDGE_DEBUG_PORT` 의 첫 것, 꼴이 아니면 기본. 창을 여는 손과 거두는 손이 같은 포트를 본다."""
    got = (os.environ.get("EDGE_DEBUG_PORT", "").split(",")[0]).strip()
    return int(got) if got.isdigit() and 0 < int(got) < 65536 else int(C.EDGE_PORT_DEFAULT)


def open_tab(uri: str) -> bool:
    """보고 창을 로그인 Edge 의 새 탭에 연다 — 열었나. 주소 꼬리(`VIA_EDGE`)를 달아, 누르신 표시가 거둬지는 창에서만 단추가 선다. 포트가
    닫혔거나 답이 오류면 False — 부르는 쪽이 기본 브라우저로 간다."""
    try:
        conn = http.client.HTTPConnection(C.EDGE_HOST, port(), timeout=EDGE_TIMEOUT_S)
        try:
            conn.request("PUT", "/json/new?" + uri + "?" + C.VIA_EDGE)   # 새 Chromium 은 PUT 만 받는다
            return conn.getresponse().status == 200
        finally:
            conn.close()
    except (OSError, http.client.HTTPException, ValueError):
        return False


# ── 보고 창 — 붙은 탭 하나와 그 저장소 ───────────────────────────────────────────

class Tab:
    """열린 보고 창 하나 — 붙어 읽고 쓴다. `made` 는 이 손이 뒤 탭으로 연 탭이면 그 탭이다 — 닫을 때 그 탭만 닫는다(사람이 연 창은 안 닫는다)."""

    def __init__(self, cdp: Cdp, target: str, made: str | None = None):
        self.cdp, self.target, self.made = cdp, target, made
        self.session = cdp.call("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]

    def filed(self) -> bool:
        """file: 문서가 섰나 — 새 탭은 about:blank 에서 옮겨 가는 동안 식이 문맥을 잃고 넘어질 수 있어, 그것도 「아직」으로 본다."""
        try:
            return self.cdp.evaluate(self.session, WHERE_EXPR) == "file:"
        except EdgeGone:
            return False

    def read(self, prefixes: list[str] = HAND_KEYS) -> list:
        """저장소의 (열쇠, 값) 가운데 열쇠가 `prefixes` 의 하나로 시작하는 것. 답이 JSON 글이 아니면 EdgeGone."""
        got = self.cdp.evaluate(self.session, read_expr(prefixes)) or "[]"
        try:
            return json.loads(got)
        except (TypeError, ValueError) as exc:
            raise EdgeGone(f"창의 저장소를 읽은 답이 꼴이 아니다({type(exc).__name__})") from exc

    def write(self, rows: list[list[str]], quiet: bool = False) -> None:
        """칸들(열쇠, 값)을 창의 저장소에 적는다 — `quiet` 면 창이 다시 그리게 하는 저장소 사건을 안 일으킨다."""
        self.cdp.evaluate(self.session, (QUIET_WRITE if quiet else WRITE_EXPR) % json.dumps(rows, ensure_ascii=False))

    def swap(self, key: str, old: str, new: str) -> bool:
        """그 열쇠의 값이 아직 `old` 그대로면 `new` 로 바꾼다 — 바꿨으면 True. 창의 글 하나 안에서 읽고 쓰므로 그 사이에 창이 쓸 틈이 없다."""
        return self.cdp.evaluate(self.session, SWAP_WRITE % tuple(json.dumps(x, ensure_ascii=False) for x in (key, old, new))) is True

    def close(self) -> None:
        """이 손이 뒤 탭으로 연 탭이면 그 탭을 닫는다 — 사람이 연 창은 두고, 못 닫아도 그대로 둔다."""
        if self.made:
            try:
                self.cdp.call("Target.closeTarget", {"targetId": self.made})
            except EdgeGone:
                pass


def page(cdp: Cdp, fallback: pathlib.Path | None) -> Tab:
    """표시를 읽고 쓸 file: 탭 하나 — 열린 것이 있으면 그것, 없으면 보고 창(`fallback`)을 뒤 탭으로 열고(닫을 때 닫는다) file: 문서가 서기를
    기다린다. `fallback` 이 없으면 새로 열지 않고 `NoWindow`. 연 탭이 서지 않아 `EdgeGone` 으로 끝나면 그 탭을 닫고 나간다 — 사람의 Edge 에
    안 연 탭이 남지 않는다."""
    pages = [t for t in cdp.call("Target.getTargets").get("targetInfos", [])
             if t.get("type") == "page" and str(t.get("url", "")).startswith("file:")]
    made = None
    if pages:
        target = pages[0]["targetId"]
    elif fallback is None:
        raise NoWindow
    else:
        target = made = cdp.call("Target.createTarget", {"url": fallback.resolve().as_uri(), "background": True})["targetId"]
    try:
        tab = Tab(cdp, target, made)
        end = time.monotonic() + LOAD_WAIT_S
        while not tab.filed():
            if time.monotonic() > end:
                raise EdgeGone("보고 창이 file: 문서로 안 섰다")
            time.sleep(LOAD_STEP_S)
    except EdgeGone:
        if made is not None:
            try:
                cdp.call("Target.closeTarget", {"targetId": made})
            except EdgeGone:
                pass
        raise
    return tab


def brief_tabs(cdp: Cdp) -> list[tuple[str, str]]:
    """열린 보고 창 — (탭, 파일 이름). file: 탭 가운데 이름이 보고 창의 꼴인 것만. 새로 열지 않는다(사람의 Edge 에 탭이 뜨면 안 된다)."""
    out = []
    for t in cdp.call("Target.getTargets").get("targetInfos", []):
        url = str(t.get("url", ""))
        if t.get("type") != "page" or not url.startswith("file:"):
            continue
        name = urllib.parse.unquote(urllib.parse.urlsplit(url).path).rsplit("/", 1)[-1]
        if is_window(name):
            out.append((t["targetId"], name))
    return out


@contextlib.contextmanager
def connected():
    """로그인 Edge 의 디버깅 포트에 붙은 동안 — 그 이음(`Cdp`)을 낸다. 못 닿으면 `NoEdge`. 나가는 길마다 이음을 닫는다."""
    try:
        cdp = Cdp(port())
    except EdgeGone as exc:
        raise NoEdge(str(exc)) from exc
    try:
        yield cdp
    finally:
        cdp.close()


@contextlib.contextmanager
def window(fallback: pathlib.Path | None):
    """열린 보고 창 하나에 붙은 동안 — 그 탭(`page` — 열린 것이 없으면 `fallback` 을 뒤 탭으로 연다)을 낸다. 못 닿으면 `NoEdge`, 창이 없고
    `fallback` 도 없으면 `NoWindow`, 주고받다 멈추면 `EdgeGone`. 나가는 길마다 이 판이 연 탭과 이음을 닫는다."""
    with connected() as cdp:
        tab = page(cdp, fallback)
        try:
            yield tab
        finally:
            tab.close()


def tell_open(rows) -> bool:
    """열린 보고 창에 칸들(`rows()` 의 답)을 적는다 — 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다(탭을 안 연다 · `rows` 도 안 부른다).
    적었나."""
    try:
        with window(None) as tab:
            tab.write(rows())
            return True
    except (EdgeGone, NoWindow):
        return False


# ── 저장소의 칸 — 창이 남긴 값 ─────────────────────────────────────────────────

def cells(rows: list, prefix: str) -> dict[str, tuple[str, dict]]:
    """창에서 읽은 칸 가운데 그 머리의 것 — {열쇠의 나머지: (값 그대로, 값)}. 값이 JSON 사전이 아니면 버린다."""
    out = {}
    for row in rows if isinstance(rows, list) else []:
        if not (isinstance(row, list) and len(row) == 2 and all(isinstance(x, str) for x in row)) or not row[0].startswith(prefix):
            continue
        try:
            value = json.loads(row[1])
        except ValueError:
            continue
        if isinstance(value, dict):
            out[row[0][len(prefix):]] = (row[1], value)
    return out


def stored(rows: list, prefix: str) -> list[tuple[str, dict]]:
    """`cells` 를 (열쇠의 나머지, 값)으로 — 남긴 때 차례."""
    return sorted(((k, v) for k, (_, v) in cells(rows, prefix).items()), key=lambda t: str(t[1].get("at", "")))


def pressed_at(value: dict) -> dt.datetime | None:
    """누르신 때 — 이 PC 의 시각. 꼴이 아니면 None."""
    try:
        return dt.datetime.fromisoformat(str(value.get("at") or "")).astimezone()
    except ValueError:
        return None
