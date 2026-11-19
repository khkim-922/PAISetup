"""보고 창에서 누르신 것을 로그인 Edge 에서 거둔다 — 일일 보고 스킬의 거두는 손. 「끝났음」 · 푸신 「끝났음」은 가장 늦은 보고 글의
「끝났다고 하신 것」 · 「안 끝났다고 하신 것」에, 「내일 다시」 · 「안 올려도 됨」 · 「다시 올리기」는 보고 맞춤 파일(곁의 `prefs.py`)에
옮기고, 끝에 이 보고가 올리지 않을 것 · 오늘 돌아온 것 · 아직 미룬 것을 댄다.

    python -X utf8 -I ticks.py --dir <사용자 폴더>
    python -X utf8 -I ticks.py --dir <사용자 폴더> --times                                  보고 창에서 고르신 보고 시각만 읽는다
    python -X utf8 -I ticks.py --dir <사용자 폴더> --times-done <고르신 때> --said <말> [--refused]   받았나를 그 창에 돌려 적는다
    python -X utf8 -I ticks.py --dir <사용자 폴더> --sync                                   열린 보고 창에 지금 모습만 알린다
    (셋 다 · 그리고 거둔 뒤에도 열린 창에 지금 모습(`window.state_of` — 시각표 · 규칙의 수 · 맞춤 파일의 두 절)을 적는다 — 창은 그보다 앞서
    고른 것을 낡았다고 알고, 대화에서 바꾸신 것을 다음 스캔을 기다리지 않고 보인다. `--sync` 는 그것을 바꾸는 대화의 명령이 부른다)

    --dir — 보고 글(brief-….md)이 사는 사용자 폴더. 한 번만 받는다 · 그 안의 이름이 가장 늦은 보고 글 하나만 고친다
    --times · --times-done — 스킬 mailbox-scan 의 스캔 판이 부른다(보고 시각표의 주인은 그 스킬이다). 열린 file: 탭이 없으면 아무것도 안 연다

표시는 창(file://)의 localStorage 에 있다(`assets/report.js`). 로그인 Edge(스킬 ep-login 이 연 디버깅 포트 — `EDGE_DEBUG_PORT`
기본 9222)의 file: 탭 하나에서 읽고, 열린 file: 탭이 없으면 가장 늦은 보고 창을 뒤 탭으로 잠깐 열어 읽고 닫는다. 옮긴 표시에는 남긴 때를
적어 두어 다시 옮기지 않고, 그 절에 이미 든 메일 번호도 더하지 않는다. 부르는 곳은 이 PC 의 디버깅 포트뿐이다 — 메일함에 닿지 않는다.

내는 것 — 표준 출력의 끝 줄이 더한 수 · 이미 든 수 · 고친 보고 글을 말하고, 거둘 수 없었으면 「다음: …」이 뒤에 선다. 그 앞 줄들이
맞춤 파일의 올리지 않을 것 · 돌아온 것 · 미룬 것이다(Edge 에 못 닿아도 댄다).
`--times` 의 끝 줄 — 고르신 것이 있으면 「고르신 보고 시각: HH:MM … · 보던 시각: HH:MM …(없으면 -) · 고르신 때 <때>」(`TIMES_LINE` · 스캔이
이 꼴로 읽는다 — 보던 시각에서 무엇을 더하고 빼셨나로 걸린 시각표를 고친다).
종료 값 — 0 거뒀다(거둘 표시가 없었던 것도) · 1 보고 글이나 맞춤 파일을 못 고쳤다 · 2 인자가 틀렸다 · 3 로그인 Edge 에 못 닿았다(표시는 그
Edge 에 남는다). 무엇을 지키고 왜 그런가는 `references/DESIGN.md` 「누르신 표시」 · 「보고 맞춤」이 든다.
"""

from __future__ import annotations

import argparse
import base64
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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 window.py · prefs.py — `-I` 로 돌아도 싣는다
import prefs as P  # noqa: E402
import window as W  # noqa: E402

EXIT_OK, EXIT_FAIL, EXIT_NO_EDGE = 0, 1, 3      # 틀린 인자는 argparse 가 2 로 나간다
TIMEOUT_S = 5
LOAD_WAIT_S = 3                                  # 뒤 탭으로 연 보고 창이 file: 문서가 되기를 기다리는 끝
LOAD_STEP_S = 0.1
LINE = "- {title} — {when}보고 창에서 끝났다고 표시하셨습니다 [근거 메일](mail:{unid})"
REOPEN_LINE = "- {title} — {when}보고 창에서 끝나지 않았다고 표시하셨습니다 [근거 메일](mail:{unid})"

TIMES_LINE = "고르신 보고 시각: {times} · 보던 시각: {base} · 고르신 때 {at}"   # 스캔 판이 이 꼴로 읽는다(그 스킬 `scan_brief.py` 의 WINDOW_TIMES)
CLOCK = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
AT = re.compile(r"^\S{1,40}$")
SAID_MAX = 240
MARKS = ("done", "open", "later", "quiet", "clear")    # 표시의 값 — `assets/report.js` 가 적는 것. 옛 표시는 done(참 · 거짓)만 든다

# 창의 localStorage 를 읽고 쓰는 식 — 창에서 받은 글로 식을 짓지 않는다. 쓰는 식은 이 손이 지은 JSON 한 덩이만 인자로 받는다
READ_EXPR = ("JSON.stringify(Object.keys(localStorage).filter(function (k) { return %s.some(function (p) { return k.indexOf(p) === 0; }); })"
             ".map(function (k) { return [k, localStorage.getItem(k)]; }))") % json.dumps([W.DONE_PREFIX, W.UNQUIET_PREFIX, W.TIMES_KEY])
WRITE_EXPR = ("(function (rows) { rows.forEach(function (r) { localStorage.setItem(r[0], r[1]); });"
              " window.dispatchEvent(new StorageEvent(\"storage\")); return rows.length; })(%s)")
WHERE_EXPR = "location.protocol"
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"   # RFC 6455 의 고정값 — 손잡기 답을 재는 데 쓴다
BROWSER_PATH = re.compile(r"^ws://[^/]+(/devtools/browser/[A-Za-z0-9._-]+)$")


class EdgeGone(Exception):
    """로그인 Edge 에 못 닿았거나 그 답이 꼴이 아니다 — 표시는 그 Edge 에 남는다."""


class NoWindow(Exception):
    """열린 보고 창(file: 탭)이 없다 — 새로 열지 않는 부름(`--times`)이 받는다."""


# ── 디버깅 포트 — 브라우저 자리의 CDP 웹소켓 하나 ─────────────────────────────

class Cdp:
    """부르는 곳은 늘 `W.EDGE_HOST` 다 — 디버깅 포트의 답에 든 주소에서는 길(path)만 쓴다."""

    def __init__(self, port: int):
        self.next_id = 0
        self.rest = b""
        try:
            conn = http.client.HTTPConnection(W.EDGE_HOST, port, timeout=TIMEOUT_S)
            try:
                conn.request("GET", "/json/version")
                resp = conn.getresponse()
                info = json.loads(resp.read().decode("utf-8")) if resp.status == 200 else {}
            finally:
                conn.close()
            m = BROWSER_PATH.match(str(info.get("webSocketDebuggerUrl") or ""))
            if not m:
                raise EdgeGone("디버깅 포트가 브라우저 자리를 안 댔다")
            self.sock = socket.create_connection((W.EDGE_HOST, port), timeout=TIMEOUT_S)
            self._handshake(port, m.group(1))
        except (OSError, http.client.HTTPException, ValueError) as exc:
            raise EdgeGone(str(exc)) from exc

    def _handshake(self, port: int, path: str) -> None:
        """Origin 을 안 싣는다 — Chromium 은 Origin 이 든 손잡기만 --remote-allow-origins 로 거른다."""
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        self.sock.sendall((f"GET {path} HTTP/1.1\r\nHost: {W.EDGE_HOST}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
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
        chunk = self.sock.recv(65536)
        if not chunk:
            raise EdgeGone("웹소켓이 끊겼다")
        self.rest += chunk

    def _take(self, n: int) -> bytes:
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
        res = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True}, session)
        if "exceptionDetails" in res:
            raise EdgeGone("창에서 식이 넘어졌다")
        return (res.get("result") or {}).get("value")

    def close(self) -> None:
        try:
            self._send(0x8, b"")
            self.sock.close()
        except OSError:
            pass


def edge_port() -> int:
    """창을 연 손(window.py)과 같은 포트 — `EDGE_DEBUG_PORT` 의 첫 것, 꼴이 아니면 기본."""
    port = (os.environ.get("EDGE_DEBUG_PORT", "").split(",")[0]).strip()
    return int(port) if port.isdigit() and 0 < int(port) < 65536 else int(W.EDGE_PORT_DEFAULT)


class Page:
    """표시를 읽고 쓸 file: 탭 하나 — 열린 것이 있으면 그것, 없으면 보고 창(`fallback`)을 뒤 탭으로 열고 끝나면 닫는다. `fallback` 이
    없으면 새로 열지 않고 `NoWindow`."""

    def __init__(self, cdp: Cdp, fallback: pathlib.Path | None):
        self.cdp, self.made = cdp, None
        pages = [t for t in cdp.call("Target.getTargets").get("targetInfos", [])
                 if t.get("type") == "page" and str(t.get("url", "")).startswith("file:")]
        if pages:
            target = pages[0]["targetId"]
        elif fallback is None:
            raise NoWindow
        else:
            target = self.made = cdp.call("Target.createTarget", {"url": fallback.resolve().as_uri(), "background": True})["targetId"]
        self.session = cdp.call("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
        end = time.monotonic() + LOAD_WAIT_S
        while not self._filed():
            if time.monotonic() > end:
                raise EdgeGone("보고 창이 file: 문서로 안 섰다")
            time.sleep(LOAD_STEP_S)

    def _filed(self) -> bool:
        """file: 문서가 섰나 — 새 탭은 about:blank 에서 옮겨 가는 동안 식이 문맥을 잃고 넘어질 수 있어, 그것도 「아직」으로 본다."""
        try:
            return self.cdp.evaluate(self.session, WHERE_EXPR) == "file:"
        except EdgeGone:
            return False

    def read(self) -> list:
        return json.loads(self.cdp.evaluate(self.session, READ_EXPR) or "[]")

    def write(self, rows: list[list[str]]) -> None:
        self.cdp.evaluate(self.session, WRITE_EXPR % json.dumps(rows, ensure_ascii=False))

    def close(self) -> None:
        if self.made:
            try:
                self.cdp.call("Target.closeTarget", {"targetId": self.made})
            except EdgeGone:
                pass


# ── 표시 → 보고 글의 줄 ──────────────────────────────────────────────────────

def stored(rows: list, prefix: str) -> list[tuple[str, dict]]:
    """창에서 읽은 (열쇠, 값) 가운데 열쇠가 `prefix` 로 시작하고 값이 JSON 사전인 것 — (열쇠의 나머지, 값), 남긴 때 차례."""
    out = []
    for row in rows if isinstance(rows, list) else []:
        if not (isinstance(row, list) and len(row) == 2 and all(isinstance(x, str) for x in row)) or not row[0].startswith(prefix):
            continue
        try:
            value = json.loads(row[1])
        except ValueError:
            continue
        if isinstance(value, dict):
            out.append((row[0][len(prefix):], value))
    return sorted(out, key=lambda t: str(t[1].get("at", "")))


def mark_of(value: dict) -> str:
    """표시가 무엇을 누르신 것인가 — `mark`, 옛 표시는 done 이 거짓이면 open · 그 밖은 done. 꼴이 아니면 ""."""
    mark = value.get("mark")
    if mark is None:
        return "open" if value.get("done") is False else "done"
    return mark if mark in MARKS else ""


def ticks_of(rows: list) -> list[tuple[str, dict]]:
    """창에서 읽은 (열쇠, 값) 가운데 꼴에 맞는 누름 표시만 — (메일 번호, 값). 열쇠의 메일 번호가 32자리가 아니거나 값이 꼴이 아니면 버린다."""
    return [(unid.upper(), v) for unid, v in stored(rows, W.DONE_PREFIX) if W.UNID.match(unid) and mark_of(v)]


def title_of(value: dict) -> str:
    """보고 글 한 줄에 설 일 이름 — 줄바꿈 · 꼴 표시를 걷고 길이를 줄인다. 창의 칸에서 온 글이라 절 머리 · 링크로 서지 못하게 한다."""
    return P.clean(str(value.get("title") or "")) or "이름 없는 일"


def pressed_at(value: dict) -> dt.datetime | None:
    """누르신 때 — 이 PC 의 시각. 꼴이 아니면 None."""
    try:
        return dt.datetime.fromisoformat(str(value.get("at") or "")).astimezone()
    except ValueError:
        return None


def when_of(value: dict) -> str:
    """누르신 때 — 이 PC 의 시각으로 「M/D HH:MM」. 꼴이 아니면 빈 글."""
    at = pressed_at(value)
    return f"{at.month}/{at.day} {at:%H:%M}" if at else ""


def fold(text: str, name: str, lines: list[str], drop: set[str] = frozenset()) -> tuple[str, set[str]]:
    """보고 글의 절 `name` 에서 첫 메일 번호가 `drop` 에 든 줄을 걷고 끝에 `lines` 를 더한 글과, 고치기 전 그 절 줄들의 첫 메일 번호.
    줄의 열쇠는 첫 메일 번호다(창의 상자와 같다) — 둘째부터의 번호는 근거일 뿐이라 그 번호의 표시가 이 줄을 건드리지 않는다.
    절이 없으면 더할 줄이 있을 때만 글 끝에 세운다. 줄을 더할 때 그 절의 「없음」 줄은 걷는다 — 남기면 「없음」과 일이 한 절에 함께 선다."""
    rows = text.split("\n")
    start = end = None
    level = 0
    for i, row in enumerate(rows):
        head = W.HEADING.match(row)
        if not head:
            continue
        if start is not None and len(head.group(1)) <= level:
            end = i
            break
        if start is None and len(head.group(1)) in (2, 3) and W.plain(head.group(2)).strip().startswith(name):
            start, level = i, len(head.group(1))
    if start is None:
        if not lines:
            return text, set()
        body = text.rstrip("\n")
        return f"{body}\n\n## {name}\n" + "\n".join(lines) + "\n", set()
    end = len(rows) if end is None else end
    section = rows[start + 1:end]
    have = {k for k in map(W.first_unid, section) if k}
    if not lines and not (drop & have):
        return text, have
    kept = [r for r in section if not (lines and W.NONE_LINE.match(r.strip())) and W.first_unid(r) not in drop]
    while kept and not kept[-1].strip():
        kept.pop()
    tail = [""] if end < len(rows) else []
    new = rows[:start + 1] + kept + lines + tail + rows[end:]
    out = "\n".join(new)
    return (out if out.endswith("\n") else out + "\n"), have


# ── 들고 나기 ─────────────────────────────────────────────────────────────

def n_moved(n: dict) -> int:
    return sum(n.values())


def first_today(folder: pathlib.Path) -> bool:
    """오늘(이 PC 의 날) 지은 보고 글이 아직 없나 — 이 보고가 오늘의 첫 보고면 True."""
    today = dt.date.today().isoformat()
    return not any(f.name[6:16] == today for f in W.kept_briefs(folder))


def summary(quiet: list[str], back: list[str], wait: list[str]) -> list[str]:
    """보고를 짓는 쪽이 읽을 맞춤 — 올리지 않을 것 · 돌아온 것 · 미룬 것(없는 무리는 안 선다)."""
    out: list[str] = []
    if quiet:
        out += ["올리지 않을 것 — 사용자가 정하셨다. 같은 갈래의 일은 이 보고에 올리지 않고 「이 보고가 본 데」에 그 수만 적는다:", *quiet]
    if back:
        out += ["돌아온 것 — 「내일 다시」 하신 일이 오늘 첫 보고로 돌아왔다. 아직 열려 있으면 이 보고에 다시 올린다:", *back]
    if wait:
        out += ["미룬 것 — 「내일 다시」 하신 일이다. 돌아오는 날 전에는 이 보고에 올리지 않는다:", *wait]
    return out


def collect(folder: pathlib.Path, prefs: P.Prefs) -> tuple[int, str]:
    """창의 표시를 가장 늦은 보고 글과 맞춤 파일에 옮기고, 옮긴 표시에 남긴 때를 적는다 — (종료 값, 끝 줄). 보고 글과 맞춤 파일을 다 쓴
    뒤에만 창에 적는다 — 그 사이에 멈추면 다음 판이 다시 옮기고, 보고 글에 든 번호는 더하지 않는다."""
    briefs = W.kept_briefs(folder) if folder.is_dir() else []
    if not briefs:
        return EXIT_OK, f"거둘 자리가 없다 — {folder} 에 보고 글(brief-….md)이 없다. 창이 선 적이 없으니 표시도 없다"
    latest = briefs[-1]
    page_file = latest.with_suffix(".html")
    port = edge_port()
    try:
        cdp = Cdp(port)
    except EdgeGone as exc:
        return EXIT_NO_EDGE, (f"표시를 못 거뒀다 — 로그인 Edge({W.EDGE_HOST}:{port})에 못 닿았다({exc}). 누르신 표시는 그 Edge 에 남아 다음에 "
                              "거둔다. 다음: 대화에서 끝났다고 하신 일만 보고 글에 더하고 이어 간다")
    page = None
    try:
        page = Page(cdp, page_file if page_file.is_file() else latest)
        rows = page.read()
        ticks = ticks_of(rows)
        waiting = [(u, v) for u, v in ticks if not v.get("folded")]
        undo = [(k, v) for k, v in stored(rows, W.UNQUIET_PREFIX) if not v.get("folded") and k]
        if not waiting and not undo:
            return EXIT_OK, f"거둘 표시가 없다 — 창에서 새로 누르신 것이 없다(남긴 표시 {len(ticks)}건) · 보고 글 {latest}"
        try:
            text = latest.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return EXIT_FAIL, f"표시를 못 남겼다 — 보고 글을 못 읽었다({latest}: {exc}). 표시는 창에 그대로 있다. 다음: 그 파일을 확인하고 다시 부른다"
        # 끝났다는 표시는 「끝났다고 하신 것」에, 푸신 표시는 「안 끝났다고 하신 것」에 — 맞은편 절의 같은 번호 줄은 걷는다. 미루거나 올리지
        # 말라신 일은 맞춤 파일로 가고 「끝났다고 하신 것」에서 걷힌다(뒤에 누르신 것이 이긴다)
        _, have = fold(text, W.DONE_SECTION, [])
        _, back = fold(text, W.REOPEN_SECTION, [])
        add, reopen, dup = [], [], 0               # 표시는 메일 번호마다 하나다(창의 저장소 열쇠)
        done_ids, open_ids, aside = set(), set(), set()
        n = {"later": 0, "quiet": 0, "clear": 0, "unquiet": 0}
        before = (list(prefs.quiet), list(prefs.later))
        for unid, value in waiting:
            mark = mark_of(value)
            when = when_of(value)
            words = dict(title=title_of(value), when=f"{when} " if when else "", unid=unid)
            at = pressed_at(value) or dt.datetime.now().astimezone()
            if mark == "open":
                open_ids.add(unid)
                if unid not in back:
                    reopen.append(REOPEN_LINE.format(**words))
            elif mark == "done":
                done_ids.add(unid)
                P.drop_unid(prefs, unid)
                if unid in have:
                    dup += 1
                else:
                    add.append(LINE.format(**words))
            elif mark == "later":
                aside.add(unid)
                n["later"] += 1
                P.put_later(prefs, P.LATER_LINE.format(title=words["title"], due=(at.date() + dt.timedelta(days=1)).isoformat(),
                                                       when=P.when_words(at), where="보고 창에서", unid=unid))
            elif mark == "quiet":
                aside.add(unid)
                n["quiet"] += 1
                P.put_quiet(prefs, P.QUIET_FROM_WINDOW.format(title=words["title"], when=P.when_words(at), unid=unid))
            else:
                n["clear"] += 1
                P.drop_unid(prefs, unid)
        for k, _ in undo:
            n["unquiet"] += P.forget(prefs, k) is not None
        new, _ = fold(text, W.DONE_SECTION, add, open_ids | aside)
        new, _ = fold(new, W.REOPEN_SECTION, reopen, done_ids)
        if new != text:
            tmp = folder / f".{latest.name}.tmp"
            try:
                tmp.write_bytes(new.encode("utf-8"))
                os.replace(tmp, latest)
            except OSError as exc:
                tmp.unlink(missing_ok=True)
                return EXIT_FAIL, f"표시를 못 남겼다 — 보고 글을 못 썼다({latest}: {exc}). 표시는 창에 그대로 있다. 다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다"
        if (prefs.quiet, prefs.later) != before:
            try:
                P.write(folder, prefs)
            except OSError as exc:
                return EXIT_FAIL, (f"표시를 못 남겼다 — 보고 맞춤 파일을 못 썼다({P.path_of(folder)}: {exc}). 표시는 창에 그대로 있다. 다음: 그 폴더에 "
                                   "쓸 수 있는지 보고 다시 부른다")
        stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        marks = [[W.DONE_PREFIX + unid, json.dumps({**value, "folded": stamp}, ensure_ascii=False)] for unid, value in waiting]
        marks += [[W.UNQUIET_PREFIX + k, json.dumps({**value, "folded": stamp}, ensure_ascii=False)] for k, value in undo]
        try:
            page.write(marks)
        except EdgeGone as exc:
            print(f"경고: 보고 글 · 맞춤 파일에는 남겼지만 창에 「남겼다」를 못 적었다({exc}) — 다음 판이 보고 글에 든 번호를 보고 다시 더하지 않는다")
        moved = [f"「내일 다시」 {n['later']}건", f"「안 올려도 됨」 {n['quiet']}건", f"되돌리신 {n['clear']}건", f"「다시 올리기」 {n['unquiet']}건"]
        moved = [m for m, k in zip(moved, n) if n[k]]
        return EXIT_OK, ("거뒀다: " + (f"「끝났음」 표시 {len(add)}건을 {latest} 의 「{W.DONE_SECTION}」에 더했다" if add or dup or not (open_ids or n_moved(n))
                                       else f"보고 글 {latest}")
                         + (f" · 그 절에 이미 든 {dup}건은 더하지 않았다" if dup else "")
                         + (f" · 푸신 {len(open_ids)}건은 「{W.REOPEN_SECTION}」으로 옮겼다" if open_ids else "")
                         + (f" · {' · '.join(moved)}은 보고 맞춤 파일 {P.path_of(folder)} 에 옮겼다" if moved else "")
                         + " — 다음 업무 파악이 두 절로 그 일을 닫거나 다시 열고, 보고가 맞춤 파일을 따른다")
    except EdgeGone as exc:
        return EXIT_NO_EDGE, (f"표시를 못 거뒀다 — 로그인 Edge 와 주고받다 멈췄다({exc}). 누르신 표시는 그 Edge 에 남아 다음에 거둔다. "
                              "다음: 대화에서 끝났다고 하신 일만 보고 글에 더하고 이어 간다")
    finally:
        if page is not None:
            page.close()
        cdp.close()


def state_row(folder: pathlib.Path) -> list[str]:
    return [W.STATE_KEY, json.dumps(W.state_of(folder), ensure_ascii=False)]


def sync(folder: pathlib.Path) -> str:
    """열린 보고 창에 지금 모습을 적는다 — 창이 없거나 Edge 에 못 닿으면 아무것도 안 한다(탭을 안 연다). 내는 것 — 한 줄(못 했으면 "")."""
    try:
        cdp = Cdp(edge_port())
    except EdgeGone:
        return ""
    page = None
    try:
        try:
            page = Page(cdp, None)
        except NoWindow:
            return ""
        page.write([state_row(folder)])
        return "열린 보고 창에 지금 모습을 알렸다"
    except EdgeGone:
        return ""
    finally:
        if page is not None:
            page.close()
        cdp.close()


def times(folder: pathlib.Path, done_at: str | None, said: str, refused: bool) -> int:
    """보고 창에서 고르신 보고 시각을 읽거나(`done_at` 이 None), 받았나를 그 창에 돌려 적는다. 두 길 다 그 창에 지금 모습을 함께 적는다.
    열린 보고 창이 없으면 아무것도 안 연다."""
    port = edge_port()
    try:
        cdp = Cdp(port)
    except EdgeGone as exc:
        print(f"보고 창의 시각을 못 읽었다 — 로그인 Edge({W.EDGE_HOST}:{port})에 못 닿았다({exc})")
        return EXIT_NO_EDGE
    page = None
    try:
        try:
            page = Page(cdp, None)
        except NoWindow:
            print("고르신 보고 시각 없음 — 열린 보고 창이 없다")
            return EXIT_OK
        got = dict(stored(page.read(), W.TIMES_KEY)).get("")
        stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        page.write([state_row(folder)])
        if done_at is not None:
            if not got or got.get("at") != done_at:
                print("안 적었다 — 그 뒤에 시각을 새로 고르셨거나 고르신 것이 없다")
                return EXIT_OK
            page.write([[W.TIMES_KEY, json.dumps({**got, "done": stamp, "said": " ".join(said.split())[:SAID_MAX], "refused": refused},
                                                 ensure_ascii=False)]])
            print("적었다 — 보고 창에 받았나를 돌려 적었다")
            return EXIT_OK
        picked = got.get("times") if got and not got.get("done") else None
        if not (isinstance(picked, list) and picked and all(isinstance(t, str) and CLOCK.match(t) for t in picked)
                and AT.match(str(got.get("at") or ""))):
            print("고르신 보고 시각 없음")
            return EXIT_OK
        base = got.get("base") if isinstance(got.get("base"), list) else []
        base = [t for t in base if isinstance(t, str) and CLOCK.match(t)]
        print(TIMES_LINE.format(times=" ".join(sorted(set(picked))), base=" ".join(sorted(set(base))) or "-", at=got["at"]))
        return EXIT_OK
    except EdgeGone as exc:
        print(f"보고 창의 시각을 못 읽었다 — 로그인 Edge 와 주고받다 멈췄다({exc})")
        return EXIT_NO_EDGE
    finally:
        if page is not None:
            page.close()
        cdp.close()


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="보고 창에서 누르신 것을 로그인 Edge 에서 거둬 가장 늦은 보고 글과 보고 맞춤 파일에 옮긴다.")
    ap.add_argument("--dir", required=True, action=W.Once, help="보고 글(brief-….md)이 사는 사용자 폴더(한 번만)")
    way = ap.add_mutually_exclusive_group()
    way.add_argument("--times", action="store_true", help="보고 창에서 고르신 보고 시각만 읽는다(스캔 판이 부른다)")
    way.add_argument("--times-done", metavar="고르신_때", help="고르신 시각을 받았나를 그 창에 돌려 적는다(스캔 판이 부른다)")
    ap.add_argument("--said", default="", help="--times-done 과 함께 — 그 창에 보일 한 줄")
    ap.add_argument("--refused", action="store_true", help="--times-done 과 함께 — 안 받았다")
    way.add_argument("--sync", action="store_true", help="열린 보고 창에 지금 모습만 알린다(그것을 바꾸는 대화의 명령이 부른다)")
    args = ap.parse_args(argv)

    folder = pathlib.Path(args.dir)
    if args.times or args.times_done is not None:
        return times(folder, args.times_done, args.said, args.refused)
    if args.sync:
        print(sync(folder) or "알리지 않았다 — 열린 보고 창이 없거나 로그인 Edge 에 못 닿았다")
        return EXIT_OK
    prefs = P.read(folder)
    code, last = collect(folder, prefs)
    back, wait = P.take_due(prefs, dt.date.today(), first_today(folder)) if folder.is_dir() else ([], [])
    if back:
        try:
            P.write(folder, prefs)
        except OSError as exc:
            print(f"경고: 돌아온 것을 보고 맞춤 파일에서 못 걷었다({exc}) — 다음 보고도 돌아온 것으로 다시 댄다")
    sync(folder)                       # 열린 창이 거둔 뒤의 모습을 보이게 — 대화에서 걷은 것도 여기서 따라간다
    for line in summary(prefs.quiet, back, wait):
        print(line)
    print(last)
    return code


if __name__ == "__main__":
    sys.exit(main())
