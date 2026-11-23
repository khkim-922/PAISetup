"""PC 의 ECM 에이전트와 주고받는 손 — 웹소켓 한 줄로 받기 · 편집취소 · 올림을 맡기고 받은 파일이 다 쓰이기를 기다린다.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

from ecm_base import (AGENT_ACTION_EDIT, AGENT_ACTION_VIEW, AGENT_CANCEL, AGENT_FIELD_SEPARATOR, AGENT_OK, AGENT_SYSTEM, AGENT_TIMEOUT,
    AGENT_UPLOAD, AgentError, AgentTimeout, CHECKOUT_FOLDER, OFFICE_BY_EXT, DEFAULT_AGENT, DEFAULT_DOCS_ROOT, FILE_TIMEOUT, LOCK_PREFIX, POLL, REGISTER_ROW, Ticket,
    VIEW_FOLDER, WS_GUID, _object_id, agent_docs_root)


def _ws_frame(payload: bytes, opcode: int) -> bytes:
    """보내는 쪽 웹소켓 틀 하나 — FIN · ``opcode`` 에 길이를 달고 바이트를 무작위 가리개로 덮는다."""
    head = bytes([0x80 | opcode])
    size = len(payload)
    if size < 126:
        head += bytes([0x80 | size])
    elif size < 1 << 16:
        head += bytes([0x80 | 126]) + size.to_bytes(2, "big")
    else:
        head += bytes([0x80 | 127]) + size.to_bytes(8, "big")
    mask = os.urandom(4)
    return head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload))


class _Reader:
    """웹소켓 답을 바라는 바이트 수만큼씩 꺼내는 받기 버퍼 — 머리 뒤에 이미 받은 몫(``buffered``)부터 쓴다."""
    def __init__(self, sock: socket.socket, buffered: bytes = b""):
        self.sock, self.buf = sock, buffered

    def take(self, n: int) -> bytes:
        """``n`` 바이트가 찰 때까지 소켓에서 받아 앞의 ``n`` 바이트를 낸다 — 그 전에 연결이 닫히면 ``AgentError``."""
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise AgentError("ECM 에이전트가 답 없이 연결을 닫았다")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out


def ws_exchange(url: str, text: str, *, timeout: float = AGENT_TIMEOUT) -> str:
    """웹소켓 하나를 열어 글 한 줄을 보내고 첫 글 답을 낸다(RFC 6455 의 쓰는 몫만)."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "ws" or not parts.hostname:
        raise AgentError(f"에이전트 주소(ws://…)가 아니다: {url}")
    port = parts.port or 80
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (f"GET {parts.path or '/'} HTTP/1.1\r\nHost: {parts.hostname}:{port}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
    try:
        sock = socket.create_connection((parts.hostname, port), timeout=timeout)
    except OSError as exc:
        raise AgentError(f"ECM 에이전트에 못 닿았다({url}) — 이 PC 에서 ECM 에이전트(트레이의 Rayful)가 도는지 본다: {exc}") from exc
    with sock:
        try:
            sock.sendall(request.encode("ascii"))
            head = b""
            while b"\r\n\r\n" not in head:
                chunk = sock.recv(4096)
                if not chunk:
                    raise AgentError("ECM 에이전트가 웹소켓 머리 없이 닫았다")
                head += chunk
            head, rest = head.split(b"\r\n\r\n", 1)
            lines = head.decode("latin-1").split("\r\n")
            if " 101 " not in lines[0] + " ":
                raise AgentError(f"ECM 에이전트가 웹소켓을 안 받았다: {lines[0]}")
            accept = base64.b64encode(hashlib.sha1((key + WS_GUID).encode("ascii")).digest()).decode("ascii")
            headers = {k.strip().lower(): v.strip() for k, v in (l.split(":", 1) for l in lines[1:] if ":" in l)}
            if headers.get("sec-websocket-accept") != accept:
                raise AgentError("ECM 에이전트의 웹소켓 답 열쇠가 틀렸다")
            sock.sendall(_ws_frame(text.encode("utf-8"), 0x1))
            reader = _Reader(sock, rest)
            while True:
                b0, b1 = reader.take(2)
                size = b1 & 0x7F
                if size == 126:
                    size = int.from_bytes(reader.take(2), "big")
                elif size == 127:
                    size = int.from_bytes(reader.take(8), "big")
                mask = reader.take(4) if b1 & 0x80 else b""
                payload = reader.take(size)
                if mask:
                    payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
                opcode = b0 & 0x0F
                if opcode == 0x9:
                    sock.sendall(_ws_frame(payload, 0xA))
                elif opcode == 0x8:
                    raise AgentError("ECM 에이전트가 답 없이 웹소켓을 닫았다")
                elif opcode in (0x1, 0x2):
                    try:
                        sock.sendall(_ws_frame(b"", 0x8))
                    except OSError:
                        pass
                    return payload.decode("utf-8", "replace")
        except socket.timeout as exc:
            raise AgentTimeout(f"ECM 에이전트가 {timeout:.0f} 초 안에 답하지 않았다") from exc
        except OSError as exc:
            raise AgentError(f"ECM 에이전트와 주고받다 끊겼다: {exc}") from exc


def download_line(ticket: Ticket, action: str) -> str:
    """받기 한 줄을 짓는다 — 열기 표의 값에 제어 글자가 들면 보내지 않고 ``AgentError``."""
    fields = (ticket.doc_id, ticket.object_id, ticket.file_name)
    if any(ch < " " for f in fields for ch in f):
        raise AgentError("열기 답의 값에 제어 글자가 들어 있어 에이전트에 보내지 않는다")
    return AGENT_FIELD_SEPARATOR.join(("Download", ticket.doc_id, ticket.object_id, action, ticket.file_name, AGENT_SYSTEM))


def no_answer_word(exc: AgentError, action: str) -> str:
    """받기 줄에 에이전트가 말이 없을 때의 말 — 메일 첨부에서 온 열쇠면 다시 받는 길을 이른다."""
    # 열기 표는 왔는데 에이전트가 말이 없다 — 메일 쪽지의 머리 열쇠가 화면이 여는 링크 쪽 열쇠와 다를 때 머리 열쇠로 열면 이렇다.
    # 사람이 첨부를 눌러 연 파일은 등급 문을 안 지났다 — 그 파일을 모델이 읽으라고 이르지 않는다(references/DESIGN.md
    # 「기밀 · 핵심기술 문서는 묻고 받는다」)
    again = "company-mail 의 attachment --save 로 열쇠를 다시 받는다(화면이 여는 링크 쪽 열쇠를 낸다)"
    if action == AGENT_ACTION_VIEW:
        again += (". 그래도 같으면 사람이 그 첨부를 눌러 화면에서 본다 — 그렇게 내려온 파일은 등급 문을 안 지나 스킬 "
                  "drm-office-read 로 열지 않는다")
    return f"{exc} — 메일 첨부에서 온 열쇠면 {again}"


class Agent:
    """PC 의 ECM 에이전트 — 받은 파일을 기본 앱으로 열고(보기 · 편집), 새 문서로 올릴 파일을 서버 임시 자리에 올린다."""

    def __init__(self, url: str = DEFAULT_AGENT, docs_root=DEFAULT_DOCS_ROOT):
        self.url = url
        self.docs_root = pathlib.Path(docs_root)

    @classmethod
    def from_env(cls) -> "Agent":
        """환경변수 ``ECM_AGENT_URL``(비면 ``DEFAULT_AGENT``)과 받는 자리(``agent_docs_root``)로 에이전트 하나를 짓는다."""
        return cls(os.environ.get("ECM_AGENT_URL", "").strip() or DEFAULT_AGENT, agent_docs_root())

    def _received(self, folder: str) -> set[pathlib.Path]:
        """``<받는 자리>\\<계정>\\<folder>\\<시각 번호>\\`` 아래 받은 파일들(잠금 파일 ``~$`` 은 뺀다)."""
        found: set[pathlib.Path] = set()
        if not self.docs_root.is_dir():
            return found
        for account in self.docs_root.iterdir():
            place = account / folder
            if not place.is_dir():
                continue
            for stamp in place.iterdir():
                if stamp.is_dir():
                    found.update(f for f in stamp.iterdir() if f.is_file() and not f.name.startswith(LOCK_PREFIX))
        return found

    def newest_edit_file(self, object_id: str) -> pathlib.Path | None:
        """편집으로 받은 그 문서의 가장 새 파일(오피스 꼴) — 지금 잠금은 가장 새로 받은 판의 것이다. 없으면 None."""
        mine = [f for f in self._received(CHECKOUT_FOLDER) if object_id.lower() in f.name.lower() and f.suffix.lower() in OFFICE_BY_EXT]
        return max(mine, key=lambda f: f.stat().st_mtime, default=None)

    def _download(self, ticket: Ticket, action: str, folder: str, file_timeout: float) -> pathlib.Path:
        """에이전트에 받기 한 줄을 보내고, ``folder`` 아래 새로 생긴 받은 파일이 다 쓰일 때까지 기다려 그 경로를 낸다.
        받은 파일 이름은 짓지 않는다 — 편집 열기는 이름 끝에 열쇠 · 계정을 한 번 더 붙여 받는다."""
        line = download_line(ticket, action)
        before = self._received(folder)
        try:
            answer = ws_exchange(self.url, line)
        except AgentTimeout as exc:
            raise AgentError(no_answer_word(exc, action)) from exc
        if answer.strip().strip('"') != AGENT_OK:
            raise AgentError(f"ECM 에이전트가 OK 대신 이렇게 답했다: {answer[:200]}")
        return self._wait_received(folder, before, ticket, file_timeout)

    def _wait_received(self, folder: str, before: set[pathlib.Path], ticket: Ticket, file_timeout: float) -> pathlib.Path:
        """``folder`` 아래 ``before`` 에 없던 받은 파일이 생겨 크기가 두 번 같게 볼 때까지 기다려 그 경로를 낸다 — 시한을 넘기면
        ``AgentError``. 이름이 표의 파일 이름과 같은 것을 먼저 고른다."""
        deadline = time.monotonic() + file_timeout
        last: tuple[pathlib.Path, int] | None = None
        while time.monotonic() < deadline:
            fresh = sorted(self._received(folder) - before, key=lambda f: (f.name != ticket.file_name, f.name))
            if fresh:
                target = fresh[0]
                try:
                    size = target.stat().st_size
                except OSError:
                    size = -1
                if size > 0 and last == (target, size):
                    return target
                last = (target, size)
            time.sleep(POLL)
        raise AgentError(f"ECM 에이전트가 OK 를 냈는데 {file_timeout:.0f} 초 안에 {self.docs_root} 아래 {folder} 에 받은 파일이 안 생겼다")

    def download_view(self, ticket: Ticket, *, file_timeout: float = FILE_TIMEOUT) -> pathlib.Path:
        """보기로 받는다 — 읽기 전용으로 뜬다."""
        return self._download(ticket, AGENT_ACTION_VIEW, VIEW_FOLDER, file_timeout)

    def download_edit(self, ticket: Ticket, *, file_timeout: float = FILE_TIMEOUT) -> pathlib.Path:
        """편집으로 받는다 — ``Ecm.checkout`` 으로 잠근 뒤에만 부른다. 읽기 쓰기로 뜬다."""
        return self._download(ticket, AGENT_ACTION_EDIT, CHECKOUT_FOLDER, file_timeout)

    def cancel(self, object_id: str) -> str:
        """편집취소의 에이전트 한 줄 — 잠금을 풀고 편집으로 받은 자리를 정리한다. 답(OK · 「현재 파일을 사용 중입니다.」 ·
        java.lang.Exception: CancelCheckOut)을 그대로 낸다 — 판정은 부르는 쪽이 다시 읽은 잠금으로 한다."""
        return ws_exchange(self.url, AGENT_FIELD_SEPARATOR.join((AGENT_CANCEL, _object_id(object_id)))).strip().strip('"')

    def upload_new(self, path: pathlib.Path) -> tuple[str, str]:
        """새 문서로 올릴 파일을 서버 임시 자리에 올린다 — 화면의 등록 저장이 먼저 부르는 줄. (서버 자리, 서버 파일 이름)을 낸다.
        로컬 파일은 지우지 않는다(화면은 설정에 따라 지운다 — 이 손은 그 걸음을 안 한다)."""
        text = str(path)
        if any(ch < " " or ch == "|" for ch in text):
            raise AgentError("올릴 파일 경로에 제어 글자나 「|」가 들어 에이전트에 보내지 않는다")
        answer = ws_exchange(self.url, AGENT_UPLOAD + AGENT_FIELD_SEPARATOR + REGISTER_ROW + "|" + text)
        try:
            got = json.loads(answer)
        except json.JSONDecodeError as exc:
            raise AgentError(f"ECM 에이전트가 올림 답 대신 이렇게 답했다: {answer[:200]}") from exc
        server_path, server_file = str(got.get("SERVERPATH", "")), str(got.get("SERVERFILE", ""))
        if got.get("LISTID") != REGISTER_ROW or not server_path or not server_file:
            raise AgentError(f"ECM 에이전트의 올림 답에 서버 자리가 없다: {answer[:200]}")
        return server_path, server_file
