"""보고 창에서 「끝났음」을 누르거나 푸신 표시를 로그인 Edge 에서 거둬, 가장 늦은 보고 글의 「끝났다고 하신 것」 · 「안 끝났다고 하신 것」에
옮긴다 — 일일 보고 스킬의 거두는 손.

    python -X utf8 -I ticks.py --dir <사용자 폴더>

    --dir — 보고 글(brief-….md)이 사는 사용자 폴더. 한 번만 받는다 · 그 안의 이름이 가장 늦은 보고 글 하나만 고친다

표시는 창(file://)의 localStorage 에 메일 번호마다 있다(`assets/report.js`). 로그인 Edge(스킬 ep-login 이 연 디버깅 포트 — `EDGE_DEBUG_PORT`
기본 9222)의 file: 탭 하나에서 읽고, 열린 file: 탭이 없으면 가장 늦은 보고 창을 뒤 탭으로 잠깐 열어 읽고 닫는다. 더한 표시에는 남긴 때를
적어 두어 다시 더하지 않고, 그 절에 이미 든 메일 번호도 더하지 않는다. 부르는 곳은 이 PC 의 디버깅 포트뿐이다 — 메일함에 닿지 않는다.

내는 것 — 표준 출력의 끝 줄이 더한 수 · 이미 든 수 · 고친 보고 글을 말하고, 거둘 수 없었으면 「다음: …」이 뒤에 선다.
종료 값 — 0 거뒀다(거둘 표시가 없었던 것도) · 1 보고 글을 못 고쳤다 · 2 인자가 틀렸다 · 3 로그인 Edge 에 못 닿았다(표시는 그 Edge 에 남는다).
무엇을 지키고 왜 그런가는 `references/DESIGN.md` 「끝났음 표시」가 든다.
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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # 곁의 window.py — `-I` 로 돌아도 싣는다
import window as W  # noqa: E402

EXIT_OK, EXIT_FAIL, EXIT_NO_EDGE = 0, 1, 3      # 틀린 인자는 argparse 가 2 로 나간다
TIMEOUT_S = 5
LOAD_WAIT_S = 3                                  # 뒤 탭으로 연 보고 창이 file: 문서가 되기를 기다리는 끝
LOAD_STEP_S = 0.1
TITLE_MAX = 80                                   # 보고 글 한 줄에 들일 일 이름의 길이
LINE = "- {title} — {when}보고 창에서 끝났다고 표시하셨습니다 [근거 메일](mail:{unid})"
REOPEN_LINE = "- {title} — {when}보고 창에서 끝나지 않았다고 표시하셨습니다 [근거 메일](mail:{unid})"

# 창의 localStorage 를 읽고 쓰는 식 — 창에서 받은 글로 식을 짓지 않는다. 쓰는 식은 이 손이 지은 JSON 한 덩이만 인자로 받는다
READ_EXPR = ("JSON.stringify(Object.keys(localStorage).filter(function (k) { return k.indexOf(%s) === 0; })"
             ".map(function (k) { return [k, localStorage.getItem(k)]; }))") % json.dumps(W.DONE_PREFIX)
WRITE_EXPR = ("(function (rows) { rows.forEach(function (r) { localStorage.setItem(r[0], r[1]); });"
              " window.dispatchEvent(new StorageEvent(\"storage\")); return rows.length; })(%s)")
WHERE_EXPR = "location.protocol"
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"   # RFC 6455 의 고정값 — 손잡기 답을 재는 데 쓴다
BROWSER_PATH = re.compile(r"^ws://[^/]+(/devtools/browser/[A-Za-z0-9._-]+)$")
MAIL_REF = re.compile(r"\(mail:([0-9A-Fa-f]{32})\)")
NUMBERISH = re.compile(r"\(?mail:[^\s)]*\)?|\b[0-9A-Fa-f]{32}\b")   # 일 이름 속 메일 번호 꼴 — 다음 업무 파악이 그 번호를 이 일의 메일로 읽는다


class EdgeGone(Exception):
    """로그인 Edge 에 못 닿았거나 그 답이 꼴이 아니다 — 표시는 그 Edge 에 남는다."""


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
    """표시를 읽고 쓸 file: 탭 하나 — 열린 것이 있으면 그것, 없으면 보고 창을 뒤 탭으로 열고 끝나면 닫는다."""

    def __init__(self, cdp: Cdp, fallback: pathlib.Path):
        self.cdp, self.made = cdp, None
        pages = [t for t in cdp.call("Target.getTargets").get("targetInfos", [])
                 if t.get("type") == "page" and str(t.get("url", "")).startswith("file:")]
        if pages:
            target = pages[0]["targetId"]
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

def ticks_of(rows: list) -> list[tuple[str, dict]]:
    """창에서 읽은 (열쇠, 값) 가운데 꼴에 맞는 표시만 — (메일 번호, 값). 열쇠의 메일 번호가 32자리가 아니거나 값이 꼴이 아니면 버린다."""
    out = []
    for row in rows if isinstance(rows, list) else []:
        if not (isinstance(row, list) and len(row) == 2 and all(isinstance(x, str) for x in row)):
            continue
        key, raw = row
        unid = key[len(W.DONE_PREFIX):] if key.startswith(W.DONE_PREFIX) else ""
        try:
            value = json.loads(raw)
        except ValueError:
            continue
        if W.UNID.match(unid) and isinstance(value, dict):
            out.append((unid.upper(), value))
    return sorted(out, key=lambda t: str(t[1].get("at", "")))


def title_of(value: dict) -> str:
    """보고 글 한 줄에 설 일 이름 — 줄바꿈 · 꼴 표시를 걷고 길이를 줄인다. 창의 칸에서 온 글이라 절 머리 · 링크로 서지 못하게 한다."""
    words = " ".join(str(value.get("title") or "").split())
    words = re.sub(r"[\[\]{}`*#<>]", "", NUMBERISH.sub("", words)).strip(" -—")
    if len(words) > TITLE_MAX:
        words = words[:TITLE_MAX - 1].rstrip() + "…"
    return words or "이름 없는 일"


def when_of(value: dict) -> str:
    """누르신 때 — 이 PC 의 시각으로 「M/D HH:MM」. 꼴이 아니면 빈 글."""
    try:
        at = dt.datetime.fromisoformat(str(value.get("at") or "")).astimezone()
    except ValueError:
        return ""
    return f"{at.month}/{at.day} {at:%H:%M}"


def fold(text: str, name: str, lines: list[str], drop: set[str] = frozenset()) -> tuple[str, set[str]]:
    """보고 글의 절 `name` 에서 `drop` 의 메일 번호가 든 줄을 걷고 끝에 `lines` 를 더한 글과, 고치기 전 그 절에 든 메일 번호.
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
    have = {u.upper() for u in MAIL_REF.findall("\n".join(section))}
    if not lines and not (drop & have):
        return text, have
    kept = [r for r in section if not (lines and W.NONE_LINE.match(r.strip()))
            and not {u.upper() for u in MAIL_REF.findall(r)} & drop]
    while kept and not kept[-1].strip():
        kept.pop()
    tail = [""] if end < len(rows) else []
    new = rows[:start + 1] + kept + lines + tail + rows[end:]
    out = "\n".join(new)
    return (out if out.endswith("\n") else out + "\n"), have


# ── 들고 나기 ─────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="보고 창의 「끝났음」 표시를 로그인 Edge 에서 거둬 가장 늦은 보고 글의 「끝났다고 하신 것」에 더한다.")
    ap.add_argument("--dir", required=True, action=W.Once, help="보고 글(brief-….md)이 사는 사용자 폴더(한 번만)")
    args = ap.parse_args(argv)

    folder = pathlib.Path(args.dir)
    briefs = W.kept_briefs(folder) if folder.is_dir() else []
    if not briefs:
        print(f"거둘 자리가 없다 — {folder} 에 보고 글(brief-….md)이 없다. 창이 선 적이 없으니 표시도 없다")
        return EXIT_OK
    latest = briefs[-1]
    page_file = latest.with_suffix(".html")
    port = edge_port()
    try:
        cdp = Cdp(port)
    except EdgeGone as exc:
        print(f"표시를 못 거뒀다 — 로그인 Edge({W.EDGE_HOST}:{port})에 못 닿았다({exc}). 누르신 표시는 그 Edge 에 남아 다음에 거둔다. "
              "다음: 대화에서 끝났다고 하신 일만 보고 글에 더하고 이어 간다")
        return EXIT_NO_EDGE
    page = None
    try:
        page = Page(cdp, page_file if page_file.is_file() else latest)
        ticks = ticks_of(page.read())
        waiting = [(u, v) for u, v in ticks if not v.get("folded")]
        if not waiting:
            print(f"거둘 표시가 없다 — 창에서 새로 「끝났음」을 누르신 것이 없다(남긴 표시 {len(ticks)}건) · 보고 글 {latest}")
            return EXIT_OK
        try:
            text = latest.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"표시를 못 남겼다 — 보고 글을 못 읽었다({latest}: {exc}). 표시는 창에 그대로 있다. 다음: 그 파일을 확인하고 다시 부른다")
            return EXIT_FAIL
        # 끝났다는 표시(done 이 없거나 참)는 「끝났다고 하신 것」에, 풀린 표시는 「안 끝났다고 하신 것」에 — 맞은편 절의 같은 번호 줄은 걷는다
        _, have = fold(text, W.DONE_SECTION, [])
        _, back = fold(text, W.REOPEN_SECTION, [])
        add, reopen, dup = [], [], 0               # 표시는 메일 번호마다 하나다(창의 저장소 열쇠)
        done_ids, open_ids = set(), set()
        for unid, value in waiting:
            when = when_of(value)
            words = dict(title=title_of(value), when=f"{when} " if when else "", unid=unid)
            if value.get("done") is False:
                open_ids.add(unid)
                if unid not in back:
                    reopen.append(REOPEN_LINE.format(**words))
            elif unid in have:
                done_ids.add(unid)
                dup += 1
            else:
                done_ids.add(unid)
                add.append(LINE.format(**words))
        new, _ = fold(text, W.DONE_SECTION, add, open_ids)
        new, _ = fold(new, W.REOPEN_SECTION, reopen, done_ids)
        if new != text:
            tmp = folder / f".{latest.name}.tmp"
            try:
                tmp.write_bytes(new.encode("utf-8"))
                os.replace(tmp, latest)
            except OSError as exc:
                tmp.unlink(missing_ok=True)
                print(f"표시를 못 남겼다 — 보고 글을 못 썼다({latest}: {exc}). 표시는 창에 그대로 있다. 다음: 그 폴더에 쓸 수 있는지 보고 다시 부른다")
                return EXIT_FAIL
        stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        marks = [[W.DONE_PREFIX + unid, json.dumps({**value, "folded": stamp}, ensure_ascii=False)] for unid, value in waiting]
        try:
            page.write(marks)
        except EdgeGone as exc:
            print(f"경고: 보고 글에는 남겼지만 창에 「남겼다」를 못 적었다({exc}) — 다음 판이 보고 글에 든 번호를 보고 다시 더하지 않는다")
        print(f"거뒀다: 「끝났음」 표시 {len(add)}건을 {latest} 의 「{W.DONE_SECTION}」에 더했다"
              + (f" · 그 절에 이미 든 {dup}건은 더하지 않았다" if dup else "")
              + (f" · 푸신 {len(open_ids)}건은 「{W.REOPEN_SECTION}」로 옮겼다" if open_ids else "")
              + " — 다음 업무 파악이 이 두 절로 그 일을 닫거나 다시 연다")
        return EXIT_OK
    except EdgeGone as exc:
        print(f"표시를 못 거뒀다 — 로그인 Edge 와 주고받다 멈췄다({exc}). 누르신 표시는 그 Edge 에 남아 다음에 거둔다. "
              "다음: 대화에서 끝났다고 하신 일만 보고 글에 더하고 이어 간다")
        return EXIT_NO_EDGE
    finally:
        if page is not None:
            page.close()
        cdp.close()


if __name__ == "__main__":
    sys.exit(main())
