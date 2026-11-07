"""ecm.py · default_app.py 의 계약을 가짜 ECM 서버 · 가짜 에이전트로 잰다 — 127.0.0.1 밖으로는 아무것도 안 나간다.

층 — 쓰는 사람의 계약. 판정은 셋이다.
    * 읽기 길이 문서함을 바꾸는 요청(편집으로 열기 · 새 판 올리기 · 잰 꼴 밖의 서비스 · 칸 · 값 · 방법 · 서버)을 서버에 보내나.
      대조로 잰 읽기(목록 · 건수 · 열기 첫 걸음 · 세션 확인)는 서버에 닿아 풀려야 한다 — 다 막아서 초록이 되는 판을 가른다
    * 등록 길이 화면의 두 POST(같은 이름 찾기 · 등록)만 보내나 — 같은 이름이면 에이전트 올림도 등록도 안 가고, 화면에 없는 보안
      짝 · 꼴 밖의 서버 자리 · 다른 서비스의 POST 는 서버에 닿기 전에 막나. 대조로 한 판은 끝까지 서야 한다
    * 기본 앱 손이 이미 고른 값(UserChoice · UserChoiceLatest)을 덮나, 새 앱 알림 값을 빠진 것만 더하고 있는 값은 두나 — 버릴
      자리(HKCU\\Software\\PAISetupEcmCheck)에서 잰다. 이 PC 의 진짜 확장자 자리와 알림 자리는 안 건드린다
    * (``--office`` 일 때만) 창 닫는 손이 받은 문서 하나만 닫고, 같은 앱에 떠 있는 다른 문서와 앱은 남기나 — 남은 문서가
      없으면 앱을 끄나. 워드와 파워포인트(사용자 하나에 하나만 떠 사람의 앱에 들어간다), 그리고 pdf 의 Acrobat · Reader(창 하나에
      탭으로 든다 — 닫는 손이 Ctrl+W 를 보내 앞 탭이 사람의 것이면 그것을 닫는다)로 잰다. Acrobat 은 사람의 pdf 가 앞 탭일 때
      아무것도 안 닫나도 잰다. 앱은 셸이 띄우듯 실행 파일에
      파일을 줘서 띄운다. 오피스가 깔린 PC 에서 화면에 창이 잠깐 뜬다. 그 앱이 이미 떠 있으면 사람의 것이라 안 잰다(못 잼)
남기는 까닭(check-design §1 넷) — 길이 분명하다(같은 서비스 모음에 문서를 잠그는 편집 열기가 있고 손을 고칠 때마다 막는
목록이 흔들린다 · 등록은 동료가 보는 문서함에 문서를 더한다 · 기본 앱은 사람이 이미 고른 확장자에서 늘 불린다 · 파워포인트는 사람의 앱에 붙는다) · 깨지면 조용하거나
되돌릴 수 없다(서버의 잠금 · 바뀐 기본 앱 · 닫힌 사람의 문서) · 쓰는 사람의 문서함 · 설정 · 문서를 잃는다 · 다른 무엇도 안
잡는다(회사 ECM 은 회사 PC 에서만 닿는다).

가짜 서버는 사내 ECM 에서 잰 꼴을 흉내 낸다 — 꼴의 원본은 ecm.py 머리말 「사내 ECM 에서 잰 것」이 가리키는 회사 확인 기록이다
(이 파일은 ecm.py 의 막는 목록을 읽어 오지 않는다). ``JSESSIONID`` 가 없으면 ``302 → /ECM/logout.jsp``, 답은 ``text/xml`` 머리에
앞 빈 줄이 붙은 JSON 이다. 막혀야 할 주소에는 일부러 ``MB_RTN_VALUE:true`` 를 줘서, 새어 나가면 손은 조용히 성공한다 — 판정은
서버의 받은 기록으로 한다.

돌리는 법::

    python -X utf8 -I check_ecm.py [ecm.py 가 든 폴더] [--office]

폴더를 안 주면 이 파일의 폴더를 잰다. 일부러 틀린 사본을 다른 폴더에 두고 그 폴더를 주면 물림(검사가 정말 무나)을 잰다.

판정 — 끝 줄이 「통과 N/N」 이면 종료 코드 0, 하나라도 어긋나면 1, 재지 못한 것만 남았으면 2.

언제 걷나 — ecm.py 의 읽기 길이 사라지거나 · 기본 앱 손이 사라지거나 · 같은 계약을 실물 ECM 에서 재는 검사가 서서 더하는 믿음이
없어지면.

여기서 못 재는 것 — 사내 SSO 와 진짜 에이전트(웹소켓 줄을 에이전트가 받는 꼴 · 받은 파일이 감긴 채인 것 · 기본 앱으로 띄우는 것) ·
Windows 가 해시를 받아 주는지(그것은 손이 쓸 때마다 ``AssocQueryStringW`` 로 다시 본다) · UCPD 가 막는 판 · 엑셀의 닫기 ·
감긴 파일을 연 오피스.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import http.server
import importlib
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import winreg
import zipfile

SESSION_VALUE = "check-session-0001"
OBJ = "00a1b2c3d4e5f607"
DOC = "doc00a1b2c3d4e5f607"
ACCOUNT = "user01"
FAKE_DOCS = [
    {"MS_OBJECT_ID": OBJ, "MS_DOC_ID": DOC, "MS_OBJECT_NAME": "주간 보고", "MS_DOC_EXTENSION": "pdf",
     "MS_FILE_SIZE": "1024", "MS_DOC_VERSION": "0.1", "MS_REG_DATE": "2026-10-01", "MS_MODIFY_DATE_EXT": "2026-10-30 09:00",
     "MS_FOLDER_PATH": "내 문서함/보고", "MS_FOLDER_ID": "fdr0001", "MS_OWNER_NAME": "홍길동", "MS_SECURITY_LEVEL": "2A",
     "MS_LOCK_USER_ID": "", "MI_DOC_PERMIT": "7"},
    {"MS_OBJECT_ID": "11a1b2c3d4e5f608", "MS_DOC_ID": "doc11a1b2c3d4e5f608", "MS_OBJECT_NAME": "예산 계획",
     "MS_DOC_EXTENSION": "docx", "MS_FILE_SIZE": "2048", "MS_DOC_VERSION": "0.3", "MS_REG_DATE": "2026-09-01",
     "MS_MODIFY_DATE": "2026-09-15", "MS_FOLDER_PATH": "내 문서함", "MS_FOLDER_ID": "fdr0000", "MS_OWNER_NAME": "홍길동",
     "MS_SECURITY_LEVEL": "2A", "MS_LOCK_USER_ID": "", "MI_DOC_PERMIT": "7"},
]
CHECK_BASE = r"Software\PAISetupEcmCheck\FileExts"
CHECK_TOASTS = r"Software\PAISetupEcmCheck\ApplicationAssociationToasts"
CABINET = "cab00a1b2c3d4"
FOLDER = "fdr00a1b2c3d401"
SUB_FOLDER = "fdr00a1b2c3d402"
NEW_OBJ = "22a1b2c3d4e5f609"
# 실물 메인 화면의 꼴 — 문서함 고르기 칸의 option 과 제 부서 열쇠(스크립트 줄)
MAIN_HTML = ("<html><script>var s_UserDeptCabinetId\t= '" + CABINET + "';</script><select name='cabinetSel'>"
             "<option id=\"MENU_DEPT\"\n\t\t\tvalue='" + CABINET + "'>기획그룹</option>"
             "<option id=\"MENU_PROJECT\"\n\t\t\tvalue='cab99a1b2c3d4'>개선 프로젝트</option>"
             "<option id=\"F_LIST_RCB\" value=\"F_LIST_RCB\">휴지통</option></select>main</html>")
PROPERTY_HTML = ("<html><table><thead><tr><th>소유자<!-- 소유자 --></th><th>최종 수정자</th><th>최종 버전<!-- 최종 버전 --></th></tr>"
                 "</thead><tbody><tr><td>홍길동</td><td>홍길동</td><td>0.3</td> </tr></tbody></table></html>")


class Unmeasured(Exception):
    """이 판에서 못 쟀다."""


# ── 가짜 ECM 서버 ───────────────────────────────────────────────────────

class FakeEcm:
    """ECM 서버 흉내. ``hits`` 는 받은 요청(방법, 경로?질의) · ``docs`` 는 내 문서함 · ``file_names`` 는 objid → 받을 파일 이름."""

    def __init__(self, docs=None, *, session=SESSION_VALUE):
        self.docs = list(FAKE_DOCS if docs is None else docs)
        self.session = session
        self.hits: list[tuple[str, str]] = []
        self.bodies: list[str] = []
        self.duplicate = False
        fake = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _answer(self, method):
                fake.hits.append((method, self.path))
                if method == "POST":
                    fake.bodies.append(self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8"))
                cookies = dict(p.strip().split("=", 1) for p in (self.headers.get("Cookie") or "").split(";") if "=" in p)
                if cookies.get("JSESSIONID") != fake.session:
                    self.send_response(302)
                    self.send_header("Location", "/ECM/logout.jsp")
                    self.end_headers()
                    return
                parts = urllib.parse.urlsplit(self.path)
                if parts.path == "/ECM/jsp/main/ecmMain.jsp":
                    return self._send(MAIN_HTML.encode("utf-8"), "text/html;charset=UTF-8")
                if parts.path == "/ECM/docProperty_simple.do":
                    return self._send(PROPERTY_HTML.encode("utf-8"), "text/html;charset=UTF-8")
                q = dict(urllib.parse.parse_qsl(parts.query, keep_blank_values=True))
                body = fake.respond(parts.path, q)
                self._send(("\n\n\n" + json.dumps(body, ensure_ascii=False)).encode("utf-8"), "text/xml;charset=UTF-8")

            def _send(self, data, kind):
                self.send_response(200)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self._answer("GET")

            def do_POST(self):
                self._answer("POST")

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/ECM"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def respond(self, path: str, q: dict) -> dict:
        service = q.get("ServiceName")
        if path == "/ECM/ajaxAction.do" and service == "GetSubNaviMenu-service":
            # 실물 꼴 — MS_MENU_ID 는 <문서함>_<폴더>, MS_HAS_SUB 는 수
            if q.get("menuType") == "MENU_DEPT" and q.get("upperKey") == CABINET:
                rows = [(FOLDER, "기획", 1)]
            elif q.get("menuType") == "F_LIST_FOLDER" and q.get("upperKey") == f"{CABINET}_{FOLDER}":
                rows = [(SUB_FOLDER, "보고", 0)]
            else:
                return {"MB_RTN_VALUE": False, "MS_MSG_DESC": "폴더 경로를 조회하는데 실패 하였습니다."}
            return {"MB_RTN_VALUE": True, "ML_MENU_LIST": [
                {"ID": f, "TEXT": n, "CHILD": s, "CABINETID": CABINET, "MS_MENU_ID": f"{CABINET}_{f}", "MS_MENU_NAME": n,
                 "MS_FORM_ID": "F_LIST_FOLDER", "MS_HAS_SUB": s} for f, n, s in rows]}
        if path == "/ECM/ajaxAction.do" and service == "CheckDuplicatedDoc-service":
            title = dict(urllib.parse.parse_qsl(self.bodies[-1])).get("title", "")
            return {"MB_RTN_VALUE": True, "ML_DUPLICATED_LIST": [{"MS_DOC_TITLE": title, "MS_DOC_EXT": "xlsx"}] if self.duplicate else []}
        if path == "/ECM/ajaxAction.do" and q == {"isHTML": "T"} and self.bodies and "RegisterContents-service" in self.bodies[-1]:
            body = dict(urllib.parse.parse_qsl(self.bodies[-1], keep_blank_values=True))
            title = urllib.parse.unquote(re.search(r"<cell>1</cell><cell>([^<]*)</cell>", body["fileList"]).group(1))
            self.docs.append({"MS_OBJECT_ID": NEW_OBJ, "MS_DOC_ID": "doc" + NEW_OBJ, "MS_OBJECT_NAME": title + ".xlsx",
                              "MS_DOC_EXTENSION": "xlsx", "MS_FILE_SIZE": "2002", "MS_DOC_VERSION": "0.0",
                              "MS_FOLDER_ID": body["ecm_folder_id"], "MS_SECURITY_LEVEL": body["ecm_security_level"],
                              "MS_OWNER_NAME": "홍길동", "MS_LOCK_USER_ID": " "})
            return {"MB_RTN_VALUE": True, "MS_OBJECT_ID": NEW_OBJ, "MS_MSG_CODE": "MSG_I_0855", "MS_MSG_DESC": "컨텐츠가 등록되었습니다."}
        if path == "/ECM/ajaxAction.do" and service == "DocList-service":
            found = [d for d in self.docs if q.get("searchValue", "") in d["MS_OBJECT_NAME"]]
            if q.get("getDocCount") == "true":
                return {"MB_RTN_VALUE": True, "MI_DOC_COUNT": str(len(found))}
            size = int(q.get("docCntPerPage") or 15)
            page = int(q.get("pageNumber") or 1)
            return {"MB_RTN_VALUE": True, "ML_DOC_LIST": found[(page - 1) * size: page * size]}
        if path == "/ECM/ajaxAction.do" and service == "CheckOutCheckIn-service" and q.get("checkout") == "true":
            doc = next((d for d in self.docs if d["MS_OBJECT_ID"] == q.get("MS_OBJECT_ID")), None)
            name = f"{doc['MS_OBJECT_NAME']}_{doc['MS_OBJECT_ID']}_{ACCOUNT}.{doc['MS_DOC_EXTENSION']}"
            # 실물은 성공(true)과 실패 코드를 같이 준다 — 손은 MB_RTN_VALUE 만 본다
            return {"MB_RTN_VALUE": True, "MS_MSG_CODE": "MSG_E_0042", "MS_DOC_ID": doc["MS_DOC_ID"],
                    "MS_OBJECT_ID": doc["MS_OBJECT_ID"], "MS_FILE_NAME": urllib.parse.quote(name), "MS_IS_CHECKOUT": "0"}
        if path == "/ECM/ajaxAction.do" and service == "OpenContents-service":
            doc = next((d for d in self.docs if d["MS_OBJECT_ID"] == q.get("MS_OBJECT_ID")), None)
            if not doc:
                return {"MB_RTN_VALUE": False, "MS_MSG_CODE": "MSG_E_0001", "MS_MSG_DESC": "없는 문서"}
            name = f"{doc['MS_OBJECT_NAME']}_{doc['MS_OBJECT_ID']}_{ACCOUNT}.{doc['MS_DOC_EXTENSION']}"
            return {"MB_RTN_VALUE": True, "MS_DOC_ID": doc["MS_DOC_ID"], "MS_OBJECT_ID": doc["MS_OBJECT_ID"],
                    "MS_FILE_NAME": name, "MS_VIEW_PATH": "c:/WINNTF/View", "MS_AUTO_CHECKIN_FLAG": "V", "MS_USER_ID": ACCOUNT}
        return {"MB_RTN_VALUE": True}   # 막혀야 할 주소도 성공처럼 답한다 — 새면 손은 조용히 넘어간다

    def close(self):
        self.server.shutdown()
        self.server.server_close()


# ── 가짜 에이전트 ───────────────────────────────────────────────────────

class FakeAgent:
    """ECM 에이전트 흉내 — 웹소켓 한 줄을 받아 ``<docs_root>\\<계정>\\VIEW\\<시각 번호>\\<파일 이름>`` 에 ``content(이름)`` 을 쓰고,
    ``opener(경로)`` 가 있으면 부른 뒤 ``answer`` 로 답한다. ``lines`` 는 받은 줄이다."""

    def __init__(self, docs_root: pathlib.Path, content, *, opener=None, answer="OK"):
        self.docs_root, self.content, self.opener, self.answer = docs_root, content, opener, answer
        self.lines: list[str] = []
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen()
        self.url = f"ws://127.0.0.1:{self.sock.getsockname()[1]}/"
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._one, args=(conn,), daemon=True).start()

    def _one(self, conn: socket.socket):
        with conn:
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                data += chunk
            head, rest = data.split(b"\r\n\r\n", 1)
            key = next(l.split(":", 1)[1].strip() for l in head.decode().split("\r\n") if l.lower().startswith("sec-websocket-key"))
            accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            conn.sendall(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                         f"Sec-WebSocket-Accept: {accept}\r\n\r\n".encode())
            buf = rest
            while len(buf) < 2:
                buf += conn.recv(4096)
            size = buf[1] & 0x7F
            offset = 2
            if size == 126:
                while len(buf) < 4:
                    buf += conn.recv(4096)
                size, offset = int.from_bytes(buf[2:4], "big"), 4
            while len(buf) < offset + 4 + size:
                buf += conn.recv(65536)
            mask = buf[offset:offset + 4]
            line = bytes(b ^ mask[i % 4] for i, b in enumerate(buf[offset + 4: offset + 4 + size])).decode("utf-8")
            self.lines.append(line)
            fields = line.split("\x08")
            if self.answer == "OK" and len(fields) == 6 and fields[0] == "Download" and fields[3] == "VIEW":
                folder = self.docs_root / ACCOUNT / "VIEW" / (time.strftime("%y%m%d%H%M%S") + f"{len(self.lines):02d}")
                folder.mkdir(parents=True, exist_ok=True)
                target = folder / fields[4]
                target.write_bytes(self.content(fields[4]))
                if self.opener:
                    self.opener(target)
            reply = self.answer.encode("utf-8")
            if fields[0].startswith("uploadfilecreatedoc"):
                # 실물 꼴 — {"LISTID":"contentName_1","SERVERFILE":"<uuid>.<확장자>","SERVERPATH":"/WAS/ECMTEMP/<uuid>.<확장자>"}
                reply = json.dumps({"LISTID": fields[1].split("|")[0], "SERVERFILE": "0f0f-1a2b.xlsx",
                                    "SERVERPATH": "/WAS/ECMTEMP/0f0f-1a2b.xlsx"}).encode("utf-8")
            conn.sendall(bytes([0x81, len(reply)]) + reply)

    def close(self):
        self.sock.close()


def session_file(folder: pathlib.Path, host="127.0.0.1", value=SESSION_VALUE) -> pathlib.Path:
    """다른 호스트 쿠키가 섞인 Playwright 저장 상태 — 세션 파일은 메일 · EP 쿠키도 든다."""
    path = folder / "session.json"
    path.write_text(json.dumps({"cookies": [
        {"name": "JSESSIONID", "value": value, "domain": host, "path": "/", "expires": -1, "secure": False},
        {"name": "LtpaToken", "value": "mail-only", "domain": "mail.example.invalid", "path": "/", "expires": -1},
        {"name": "JSESSIONID", "value": "other-host", "domain": "other.example.invalid", "path": "/", "expires": -1},
    ], "origins": []}), encoding="utf-8")
    return path


def minimal_docx(text: str) -> bytes:
    """워드가 여는 가장 작은 docx — 평문이라 감기지 않았다."""
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p></w:body></w:document>')
    return buf.getvalue()


# ── 판정 ─────────────────────────────────────────────────────────────────

@contextlib.contextmanager
def stage(ecm_mod):
    fake = FakeEcm()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="check-ecm-"))
    try:
        yield fake, ecm_mod.Ecm(fake.url, session_file(tmp))
    finally:
        fake.close()
        shutil.rmtree(tmp, ignore_errors=True)


def check_reads_reach_and_changes_never_leave(ecm_mod):
    with stage(ecm_mod) as (fake, box):
        # 대조 — 잰 읽기는 닿고 풀린다
        assert box.session_alive(), "산 세션을 끊겼다고 읽었다"
        docs = box.list(search="보고")
        assert [d.object_id for d in docs] == [OBJ], f"찾기 결과가 다르다: {docs}"
        assert box.count() == len(FAKE_DOCS), "건수가 다르다"
        ticket = box.view(OBJ)
        assert (ticket.doc_id, ticket.object_id) == (DOC, OBJ) and ticket.file_name.endswith(".pdf"), ticket
        reached = len(fake.hits)
        assert reached == 4, f"읽기 넷이 서버에 넷으로 안 닿았다: {fake.hits}"
        sent = [urllib.parse.parse_qs(urllib.parse.urlsplit(p).query) for _, p in fake.hits[1:]]
        assert all(q.get("formId") == ["F_LIST_MYDOC"] for q in sent), "내 문서함 밖을 물었다"

        # 대조 — 부서 문서함 · 문서 정보의 판도 읽기로 닿는다
        cabinets = box.cabinets()
        assert [(c.key, c.name, c.kind, c.own) for c in cabinets] == [(CABINET, "기획그룹", "부서", True),
                                                                      ("cab99a1b2c3d4", "개선 프로젝트", "프로젝트", False)], cabinets
        box.list(cabinet=CABINET)
        dept = urllib.parse.parse_qs(urllib.parse.urlsplit(fake.hits[-1][1]).query)
        assert dept.get("formId") == ["F_LIST_MYDEPT"] and dept.get("listKey") == [f"{CABINET}_{CABINET}"], dept
        assert box.version(OBJ) == "0.3", "문서 정보의 최종 버전을 못 읽었다"

        # 편집 열기 문 — 정확한 꼴 하나가 닿고, 답의 퍼센트 이름을 푼다
        before_edit = len(fake.hits)
        locked = box.checkout(OBJ)
        assert locked.file_name.endswith(".pdf") and "%" not in locked.file_name, locked
        edit_sent = fake.hits[before_edit:]
        assert [urllib.parse.parse_qs(urllib.parse.urlsplit(p).query) for _, p in edit_sent] == [
            {"ServiceName": ["CheckOutCheckIn-service"], "checkout": ["true"], "MS_OBJECT_ID": [OBJ]}], edit_sent
        reached = len(fake.hits)
        edit_refused = [
            f"{box.server}{box.context}/ajaxAction.do?ServiceName=CheckOutCheckIn-service&checkout=true&MS_OBJECT_ID={OBJ}&cancelcheckout=true",
            f"{box.server}{box.context}/ajaxAction.do?ServiceName=CheckOutCheckIn-service&checkin=true&MS_OBJECT_ID={OBJ}",
            f"{box.server}{box.context}/ajaxAction.do?ServiceName=CheckOutCheckIn-service&cancelcheckout=true&MS_OBJECT_ID={OBJ}",
            f"{box.server}{box.context}/ajaxAction.do?ServiceName=DeleteDoc-service&checkout=true&MS_OBJECT_ID={OBJ}",
            f"{box.server}{box.context}/ajaxAction.do?ServiceName=CheckOutCheckIn-service&checkout=true&MS_OBJECT_ID=not-an-id",
            f"{box.server}{box.context}/ajaxAction.do?ServiceName=DeleteDoc-service&ServiceName=CheckOutCheckIn-service&checkout=true&MS_OBJECT_ID={OBJ}",
            f"{box.server}{box.context}/ajaxAction.do?ServiceName=CheckOutCheckIn-service&checkout=true&MS_OBJECT_ID=11a1b2c3d4e5f608&MS_OBJECT_ID={OBJ}",
        ]
        edit_leaked = []
        for url in edit_refused:
            try:
                box._fetch(url, edit=True)
                edit_leaked.append(url)
            except ecm_mod.Refused:
                pass
        assert not edit_leaked, "편집 열기 문이 다른 꼴을 내보냈다:\n  " + "\n  ".join(edit_leaked)
        assert len(fake.hits) == reached, f"편집 열기 문 밖의 꼴이 서버에 닿았다: {fake.hits[reached:]}"

        # 막혀야 할 것 — 잰 기록에 나온 바꾸는 꼴과, 잰 꼴에서 칸 · 값 · 방법 · 서버를 하나씩 벗어난 꼴
        base = box.server + box.context
        refused = [
            ("GET", f"{base}/ajaxAction.do?ServiceName=CheckOutCheckIn-service&checkout=true&MS_OBJECT_ID={OBJ}"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=CheckOutCheckIn-service&checkin=true&MS_OBJECT_ID={OBJ}&choice_version=0.2"),
            ("GET", f"{base}/checkoutcheckin.do?ServiceName=CheckOutCheckIn-service&MS_OBJECT_ID={OBJ}&SYSID=ECM&ACTID=checkin"),
            ("GET", f"{base}/servlet/EcmCheckinServlet?ACTID=checkin&VERSION_NO=0.2"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=OpenContents-service&view=true&checkout=true&MS_OBJECT_ID={OBJ}"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=OpenContents-service&edit=true&MS_OBJECT_ID={OBJ}"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=OpenContents-service&view=false&MS_OBJECT_ID={OBJ}"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=DocList-service&getDocList=true&ServiceName=CheckOutCheckIn-service"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=DocList-service&getDocList=true&getDocCount=true"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=DocList-service&getDocList=true&formId=F_LIST_SHARED"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=GetContextMenu-service&isHTML=T"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=DeleteDoc-service&delete=true&MS_OBJECT_ID={OBJ}"),
            ("GET", f"{base}/jsp/main/ecmMain.jsp?logout=true"),
            ("GET", f"{base}/docProperty_simple.do?ServiceName=DocPropertyHtml-service&basicinfo=true&DOCID={OBJ}&getType=user&delete=true"),
            ("GET", f"{base}/docProperty_simple.do?ServiceName=DeleteDoc-service&ServiceName=DocPropertyHtml-service&basicinfo=true&DOCID={OBJ}&getType=user"),
            ("GET", f"{base}/ajaxAction.do?ServiceName=DocList-service&getDocList=true&formId=F_LIST_MYDEPT&cancelcheckout=true"),
            ("GET", f"http://127.0.0.2:{urllib.parse.urlsplit(base).port}/ECM/ajaxAction.do?ServiceName=DocList-service&getDocList=true"),
            ("POST", f"{base}/ajaxAction.do?ServiceName=DocList-service&getDocList=true"),
        ]
        leaked = []
        for method, url in refused:
            try:
                box.guard(method, url)
                if method == "GET":
                    box._fetch(url)
                leaked.append(f"{method} {url}")
            except ecm_mod.Refused:
                pass
        assert not leaked, "막아야 할 요청을 막지 않았다:\n  " + "\n  ".join(leaked)
        assert len(fake.hits) == reached, f"막아야 할 요청이 서버에 닿았다: {fake.hits[reached:]}"

        # 폴더 나무 — 잰 두 꼴은 닿고, 칸 · 값이 벗어나면 막는다
        tops = box.folders(CABINET)
        assert [(f.id, f.has_sub) for f in tops] == [(FOLDER, True)], tops
        subs = box.folders(CABINET, FOLDER)
        assert [f.id for f in subs] == [SUB_FOLDER], subs
        reached = len(fake.hits)
        for url in (f"{base}/ajaxAction.do?ServiceName=GetSubNaviMenu-service&menuType=F_LIST_FOLDER&upperKey={FOLDER}",
                    f"{base}/ajaxAction.do?ServiceName=GetSubNaviMenu-service&menuType=MENU_DEPT&upperKey={CABINET}&delete=true",
                    f"{base}/ajaxAction.do?ServiceName=GetSubNaviMenu-service&menuType=MENU_PERSONAL&upperKey={CABINET}"):
            try:
                box._fetch(url)
                leaked.append(url)
            except ecm_mod.Refused:
                pass
        assert not leaked and len(fake.hits) == reached, f"폴더 나무의 꼴 밖이 새었다: {leaked} {fake.hits[reached:]}"


def check_register_sends_only_the_screens_two_posts(ecm_mod):
    """새 문서 등록 — 같은 이름 찾기 · 등록 두 POST 만 나가고, 같은 이름이면 에이전트에도 서버 등록에도 안 간다."""
    with stage(ecm_mod) as (fake, box):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="check-ecm-reg-"))
        agent = FakeAgent(tmp, lambda name: b"x")
        try:
            target = tmp / "새 보고.xlsx"
            target.write_bytes(b"PK" + b"0" * 2000)
            # 대조 — 한 판이 선다: 찾기 POST → 에이전트 올림 → 등록 POST → 목록 다시 읽기
            done = ecm_mod.register_document(box, ecm_mod.Agent(agent.url, tmp), target, cabinet=CABINET, folder=SUB_FOLDER,
                                             security="2A", open_flag="F")
            assert done.object_id == NEW_OBJ and done.version == "0.0", done
            posts = [p for m, p in fake.hits if m == "POST"]
            assert posts == ["/ECM/ajaxAction.do?ServiceName=CheckDuplicatedDoc-service&checkDup=true",
                             "/ECM/ajaxAction.do?isHTML=T"], posts
            assert agent.lines == ["uploadfilecreatedoc\x08contentName_1|" + str(target)], agent.lines
            body = dict(urllib.parse.parse_qsl(fake.bodies[-1], keep_blank_values=True))
            assert (body["ecm_folder_id"], body["ecm_security_level"], body["ecm_open_flag"], body["ServiceName"]) == \
                   (SUB_FOLDER, "2A", "F", "RegisterContents-service"), body
            assert "/WAS/ECMTEMP/" in body["fileList"] and "<cell>새 보고</cell>" in body["fileList"], body["fileList"]   # 몸을 한 번 풀면 화면처럼 이름이 선다

            # 같은 이름 — 에이전트에도 등록 POST 에도 안 간다
            fake.duplicate = True
            before_lines, before_posts = len(agent.lines), len(posts)
            try:
                ecm_mod.register_document(box, ecm_mod.Agent(agent.url, tmp), target, cabinet=CABINET, folder=SUB_FOLDER,
                                          security="2A", open_flag="F")
                raise AssertionError("같은 이름인데 올렸다")
            except ecm_mod.EcmError as exc:
                assert "같은 이름" in str(exc), exc
            assert len(agent.lines) == before_lines, "같은 이름인데 에이전트에 올렸다"
            assert [p for m, p in fake.hits if m == "POST"][before_posts:] == [
                "/ECM/ajaxAction.do?ServiceName=CheckDuplicatedDoc-service&checkDup=true"], "같은 이름인데 등록을 보냈다"
            fake.duplicate = False

            # 막혀야 할 것 — 화면에 없는 보안 짝 · 문서함 열쇠가 아닌 값 · 꼴 밖 서버 자리 · 다른 서비스의 POST. 서버에도 에이전트에도 안 닿는다
            reached, lines = len(fake.hits), len(agent.lines)
            for bad in (lambda: ecm_mod.register_document(box, ecm_mod.Agent(agent.url, tmp), target, cabinet=CABINET,
                                                          folder=SUB_FOLDER, security="1A", open_flag="T"),
                        lambda: ecm_mod.register_document(box, ecm_mod.Agent(agent.url, tmp), target, cabinet="not-a-cabinet",
                                                          folder=SUB_FOLDER, security="2A", open_flag="F"),
                        lambda: box.register(folder=SUB_FOLDER, title="a", ext="xlsx", size=1, server_path="/WAS/x&register=y",
                                             server_file="x.xlsx", security="2A", open_flag="F"),
                        lambda: box._post({"ServiceName": "DeleteDoc-service", "delete": "true"}, b"folderID=a&title=b&fileExt=c"),
                        lambda: box._post({"isHTML": "T"}, b"register=register&ServiceName=DeleteDoc-service")):
                try:
                    bad()
                except ecm_mod.EcmError:
                    continue
                raise AssertionError("막아야 할 등록 꼴을 보냈다")
            assert len(fake.hits) == reached, f"막아야 할 등록 꼴이 서버에 닿았다: {fake.hits[reached:]}"
            assert len(agent.lines) == lines, "막아야 할 등록 꼴이 에이전트에 닿았다"
        finally:
            agent.close()
            shutil.rmtree(tmp, ignore_errors=True)


def _delete_tree(path: str) -> None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    sub = winreg.EnumKey(key, 0)
                except OSError:
                    break
                _delete_tree(path + "\\" + sub)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
    except FileNotFoundError:
        pass


def _snapshot(path: str) -> tuple:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
        values, i = [], 0
        while True:
            try:
                values.append(winreg.EnumValue(key, i))
            except OSError:
                break
            i += 1
        return tuple(sorted(values)), winreg.QueryInfoKey(key)[2]


def check_existing_choice_is_never_overwritten(app_mod):
    root = CHECK_BASE.rsplit("\\", 1)[0]
    try:
        for ext, where, progid_key in ((".docx", "UserChoice", ""), (".pptx", "UserChoiceLatest", "ProgId")):
            path = rf"{CHECK_BASE}\{ext}\{where}" + (rf"\{progid_key}" if progid_key else "")
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProgId", 0, winreg.REG_SZ, "Person.Chose.This")
                winreg.SetValueEx(key, "Hash", 0, winreg.REG_SZ, "personHash=")
            before = _snapshot(path)
            time.sleep(0.05)
            got = app_mod.ensure(ext, base=CHECK_BASE, toasts=CHECK_TOASTS)
            assert (got.progid, got.written) == ("Person.Chose.This", False), f"{ext} {where}: 고른 값을 두지 않았다 — {got}"
            assert _snapshot(path) == before, f"{ext} {where}: 고른 값의 키가 바뀌었다"
            if where != "UserChoice":
                with contextlib.suppress(FileNotFoundError):
                    winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"{CHECK_BASE}\{ext}\UserChoice"))
                    raise AssertionError(f"{ext}: {where} 가 있는데 UserChoice 를 새로 지었다")
    finally:
        _delete_tree(root)
    with contextlib.suppress(FileNotFoundError):
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, root))
        raise AssertionError(f"버릴 자리를 못 걷었다: HKCU\\{root}")


def check_new_app_toasts_fill_only_the_missing(app_mod):
    """등록된 앱 목록은 이 PC 의 실물(HKCR)을 그대로 읽는다 — 버릴 자리에는 「보였다」 값만 짓는다."""
    ext = next((e for e in (".pdf", ".docx", ".xlsx", ".pptx") if len(app_mod.registered_progids(e)) >= 2), "")
    if not ext:
        raise Unmeasured("등록된 앱이 둘 넘는 확장자가 이 PC 에 없다")
    progids = app_mod.registered_progids(ext)
    kept, person_value = f"{progids[0]}_{ext}", 7
    root = CHECK_TOASTS.rsplit("\\", 1)[0]
    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, CHECK_TOASTS, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, kept, 0, winreg.REG_DWORD, person_value)
        added = app_mod.quiet_new_apps(ext, toasts=CHECK_TOASTS)
        assert added == [f"{p}_{ext}" for p in progids[1:]], f"{ext}: 빠진 앱만 더하지 않았다 — {added}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHECK_TOASTS) as key:
            assert winreg.QueryValueEx(key, kept) == (person_value, winreg.REG_DWORD), f"{ext}: 있던 값을 고쳤다"
            for name in added:
                assert winreg.QueryValueEx(key, name) == (0, winreg.REG_DWORD), f"{name}: Windows 가 적는 꼴(DWORD 0)이 아니다"
        assert app_mod.quiet_new_apps(ext, toasts=CHECK_TOASTS) == [], f"{ext}: 두 번째 부름이 또 더했다"
    finally:
        _delete_tree(root)


# 앱 이름 → (프로세스 이름, App Paths 의 실행 파일, COM 이름, 열린 문서 모음)
OFFICE = {"Word": ("WINWORD", "Winword.exe", "Word.Application", "Documents"),
          "PPT": ("POWERPNT", "powerpnt.exe", "PowerPoint.Application", "Presentations")}


def _ps(script: str) -> str:
    out = subprocess.run(["powershell.exe", "-NoProfile", "-Command", script], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return out.stdout.strip()


def _running(app: str) -> bool:
    return _ps(f"@(Get-Process -Name {OFFICE[app][0]} -ErrorAction SilentlyContinue).Count") not in ("", "0")


def _exe(app: str) -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{OFFICE[app][1]}") as key:
            return str(winreg.QueryValueEx(key, "")[0])
    except OSError:
        return ""


def _has(app: str, path: pathlib.Path) -> bool:
    _, _, com, docs = OFFICE[app]
    return _ps(f"$a = [Runtime.InteropServices.Marshal]::GetActiveObject('{com}'); "
               f"@($a.{docs} | Where-Object {{ $_.FullName -eq '{path}' }}).Count") == "1"


def _wait(predicate, seconds=40.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.5)
    return False


ACROBAT_PROCESSES = ("AcroRd32", "Acrobat")


def _acrobat_titles() -> list[str]:
    names = ",".join(ACROBAT_PROCESSES)
    out = _ps("[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
              f"Get-Process -Name {names} -ErrorAction SilentlyContinue | Where-Object {{ $_.MainWindowHandle -ne 0 }} | "
              "ForEach-Object { $_.MainWindowTitle }")
    return [line for line in out.splitlines() if line.strip()]


def _acrobat_has(path: pathlib.Path) -> bool:
    return any(t.startswith(path.name + " - Adobe ") for t in _acrobat_titles())


def minimal_pdf() -> bytes:
    """빈 쪽 하나짜리 pdf — Reader 가 탭으로 열기만 하면 된다."""
    objs = [b"<</Type/Catalog/Pages 2 0 R>>", b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
            b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>"]
    out, offs = bytearray(b"%PDF-1.4\n"), []
    for i, obj in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 4\n0000000000 65535 f \n" + b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<</Size 4/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % xref
    return bytes(out)


def _make_decks(paths: list[pathlib.Path]) -> None:
    """평문 pptx 를 파워포인트로 짓고 끈다 — 손으로 짓기엔 부품이 많다."""
    saves = "; ".join(f"$p = $a.Presentations.Add(0); [void]$p.Slides.Add(1, 1); $p.SaveAs('{d}'); $p.Close()" for d in paths)
    _ps(f"$a = New-Object -ComObject PowerPoint.Application; {saves}; $a.Quit(); "
        "[void][Runtime.InteropServices.Marshal]::ReleaseComObject($a); [GC]::Collect(); [GC]::WaitForPendingFinalizers()")


def _closes_only_received(ecm_mod, app: str, ext: str) -> None:
    exe = _exe(app)
    if not exe:
        raise Unmeasured(f"{app} 가 없다")
    if _running(app):
        raise Unmeasured(f"{app} 가 이미 떠 있다 — 사람의 것이라 안 건드린다")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="check-ecm-office-"))
    try:
        person, received = tmp / f"person-own{ext}", tmp / "VIEW" / f"received_00a1b2c3d4e5f607_user01{ext}"
        received.parent.mkdir()
        if app == "Word":
            person.write_bytes(minimal_docx("사람이 연 문서"))
            received.write_bytes(minimal_docx("받은 문서"))
        else:
            _make_decks([person, received])
            if not (person.exists() and received.exists()):
                raise Unmeasured("파워포인트로 시험 덱을 못 지었다")
            if not _wait(lambda: not _running(app), 20):
                raise Unmeasured("시험 덱을 지은 파워포인트가 안 꺼졌다")
        subprocess.Popen([exe, str(person)])
        if not _wait(lambda: _has(app, person)):
            raise Unmeasured(f"{app} 가 사람 몫 문서를 시한 안에 못 열었다")
        subprocess.Popen([exe, str(received)])
        if not _wait(lambda: _has(app, received)):
            raise Unmeasured(f"{app} 가 받은 문서를 시한 안에 못 열었다")
        assert ecm_mod.close_window(received, app) == "closed", f"{app}: 받은 문서를 못 닫았다"
        assert _running(app) and _has(app, person), f"{app}: 받은 문서를 닫다가 사람의 문서나 앱까지 닫았다"
        assert not _has(app, received), f"{app}: 받은 문서가 그대로 떠 있다"
        assert ecm_mod.close_window(person, app) == "closed", f"{app}: 남은 문서를 못 닫았다"
        assert _wait(lambda: not _running(app), 20), f"{app}: 문서가 다 닫혔는데 앱이 안 꺼졌다"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_word_closes_only_the_received_document(ecm_mod):
    _closes_only_received(ecm_mod, "Word", ".docx")


def check_powerpoint_closes_only_the_received_document(ecm_mod):
    _closes_only_received(ecm_mod, "PPT", ".pptx")


def check_acrobat_closes_only_the_received_pdf(ecm_mod):
    """사람의 pdf 를 **뒤에** 열어 앞 탭으로 세운 판에 받은 pdf 를 닫으라 하면 아무것도 안 닫는다(not-front) — Ctrl+W 를 그대로
    보내면 사람의 것이 닫힌다. 이어 사람의 pdf 를 닫고(앞 탭이다) 받은 pdf 가 앞 탭이 된 판에 그것만 닫고 앱을 끄나 본다."""
    if _acrobat_titles():
        raise Unmeasured("Acrobat · Reader 가 이미 떠 있다 — 사람의 것이라 안 건드린다")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="check-ecm-acrobat-"))
    try:
        person, received = tmp / "person-own.pdf", tmp / "VIEW" / "received_00a1b2c3d4e5f607_user01.pdf"
        received.parent.mkdir()
        person.write_bytes(minimal_pdf())
        received.write_bytes(minimal_pdf())
        os.startfile(str(received))
        if not _wait(lambda: _acrobat_has(received)):
            raise Unmeasured("pdf 기본 앱이 Acrobat · Reader 가 아니거나 시한 안에 못 열었다")
        os.startfile(str(person))
        if not _wait(lambda: _acrobat_has(person)):
            raise Unmeasured("Acrobat 이 사람 몫 pdf 를 시한 안에 못 열었다")
        got = ecm_mod.close_window(received, ecm_mod.ACROBAT, wait=3)
        assert got == "not-front", f"Acrobat: 사람의 pdf 가 앞 탭인데 {got} 를 냈다"
        assert _acrobat_has(person), "Acrobat: 받은 pdf 를 닫으라 했는데 사람의 pdf 가 닫혔다"
        assert ecm_mod.close_window(person, ecm_mod.ACROBAT) == "closed", "Acrobat: 앞 탭인 pdf 를 못 닫았다"
        assert _wait(lambda: _acrobat_has(received), 10), "Acrobat: 앞 탭을 닫았는데 남은 pdf 가 앞에 안 섰다(또는 앱까지 꺼졌다)"
        assert ecm_mod.close_window(received, ecm_mod.ACROBAT) == "closed", "Acrobat: 받은 pdf 가 앞 탭인데 못 닫았다"
        assert _wait(lambda: not _acrobat_titles(), 20), "Acrobat: 문서가 다 닫혔는데 앱이 안 꺼졌다"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str]) -> int:
    office = "--office" in argv
    rest = [a for a in argv if a != "--office"]
    tree = pathlib.Path(rest[0] if rest else __file__).resolve()
    tree = tree if tree.is_dir() else tree.parent
    sys.path.insert(0, str(tree))
    ecm_mod = importlib.import_module("ecm")
    app_mod = importlib.import_module("default_app")
    print(f"잰다: {tree / 'ecm.py'}")
    checks = [(check_reads_reach_and_changes_never_leave, ecm_mod), (check_register_sends_only_the_screens_two_posts, ecm_mod),
              (check_existing_choice_is_never_overwritten, app_mod), (check_new_app_toasts_fill_only_the_missing, app_mod)]
    if office:
        checks += [(check_word_closes_only_the_received_document, ecm_mod),
                   (check_powerpoint_closes_only_the_received_document, ecm_mod),
                   (check_acrobat_closes_only_the_received_pdf, ecm_mod)]
    passed = unmeasured = 0
    for check, mod in checks:
        try:
            check(mod)
        except Unmeasured as exc:
            unmeasured += 1
            print(f"? {check.__name__}: 못 쟀다 — {exc}")
        except AssertionError as exc:
            print(f"✗ {check.__name__}: {exc}")
        except Exception:
            print(f"✗ {check.__name__}: 예상 못 한 예외\n{traceback.format_exc()}")
        else:
            passed += 1
            print(f"✓ {check.__name__}")
    print(f"통과 {passed}/{len(checks)}" + (f" · 못 잼 {unmeasured}" if unmeasured else ""))
    if passed == len(checks):
        return 0
    return 1 if passed + unmeasured < len(checks) else 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        traceback.print_exc()
        print("못 쟀다")
        sys.exit(2)
