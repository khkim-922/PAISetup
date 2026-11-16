"""사내 아뜰리에 서버로 보고 글을 HTML 로 짓고, 그 문서를 브라우저 고치기 화면으로 넘기고, 최신 판을 받는다.

무엇을 하나
    쓰는 사람 PC 의 환경값 키로 아뜰리에 서버의 문을 차례로 밟는다 — 표준 라이브러리만 쓴다::

        make   추천(디자인 하나로 확정) → 렌더 → 자체 점검. 끝 판을 임시 폴더에 받는다
        open   넘김 표를 받아 브라우저로 그 문서의 고치기 화면을 연다 — 화면에는 이 키 · 갈래 · 모델이 골라져 선다
        fetch  그 문서의 최신 판(사람이 화면에서 고친 뒤의 판)을 임시 폴더에 받는다

    받은 HTML 은 스킬 company-mail 의 ``save-draft --html-file`` (본문) · ``--attach`` (첨부)로 넘긴다.

    그림은 원문 글이 든다 — 마크다운 그림 줄 ``![캡션](경로)`` 의 경로가 이 PC 의 파일이면 그 자리에 그림을 박아 보내고,
    아뜰리에가 그 자리의 그림으로 지면에 앉힌다. 경로는 원문 파일의 폴더에서 풀고, 괄호가 든 경로는 ``(<경로>)`` 로 감싼다.
    바깥 주소(http · data · cid)의 그림 줄은 글자 그대로 간다.

어떻게 부르나
    python -X utf8 -I atelier.py make --source-file 글.md [--mode mail|web|auto] [--extra "정리 요청 한 줄"]
    python -X utf8 -I atelier.py open 문서
    python -X utf8 -I atelier.py fetch 문서

    서버는 ``ATELIER_URL`` · 없으면 ``DEFAULT_URL``. 키는 ``KEY_ENV``(설치가 까는 회사 키)다. 갈래 · 모델은 ``PROVIDER`` ·
    ``MODEL`` 이고 자격을 싣는 머리 이름은 서버의 ``/api/status`` 가 댄다. 사내 망의 서버라 시스템 프록시를 안 탄다.

무엇을 내나
    사람이 읽을 글줄을 표준 출력에 내고, 끝 줄은 늘 「다음: …」 이다. 종료 값 — 0 됐다 · 1 서버 · 망 오류이거나 서버가
    문서 대신 말을 돌려줬다 · 2 설정 · 인자가 틀렸다(키 없음 · 파일 없음 · 드라이런으로 떨어짐).

안 하는 것
    메일 보내기(company-mail 이 한다) · 설계 → 검토 → 상담 · 알아서 고치기(화면의 「알아서 만들기」 사슬 가운데 느린 몫 —
    고치기는 사람이 화면에서 한다) · 문서 파일(오피스 · PDF)을 원문 첨부로 싣기(글 파일 하나와 그 글이 가리킨 그림만
    보낸다) · 참고 그림(모양만 따오는 그림) 싣기 · 원문구조 다이얼(모드 기본값으로 돈다) · 세이프모드(바깥 메일용 지면 —
    사내 메일에는 안 쓴다).
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import pathlib
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

DEFAULT_URL = "http://192.168.221.83:8765"   # 사내 아뜰리에 서버
URL_ENV = "ATELIER_URL"
KEY_ENV = "ANTHROPIC_AUTH_TOKEN"   # 설치가 까는 회사 게이트웨이 키 — 아뜰리에의 회사 묶음(회사 Claude · 회사 GPT)이 같은 키를 받는다
PROVIDER = "openai"                # 아뜰리에의 「회사 GPT」 갈래
MODEL = "gpt-6.1-sol"              # 그 갈래에서 빠른 쪽 — 화면의 알아서 만들기보다 빨리 돌리려는 판
DEFAULT_MODE = "mail"              # 아뜰리에의 「문서형태」 — 메일 본문으로 실을 지면. 브라우저에서 열 판은 web(「웹페이지」)
AUTO_MODE = "auto"                 # 추천이 고른 지면을 따른다 — 화면의 「알아서 만들기」와 같은 길. 첨부로 붙일 판에 쓴다
ADVICE_PAGE = {"웹": "web", "메일": "mail"}   # 추천 줄의 지면 칸 → 모드
AUTO_FALLBACK = "web"              # 추천이 지면을 안 짚었을 때 — auto 는 브라우저로 여는 판에 쓰니 웹페이지다
REQUEST_TIMEOUT_S = 1800           # 렌더 · 자체 점검 한 문의 상한 — 서버가 게이트웨이를 기다리는 시한(ATELIER_TIMEOUT_S)보다 길게
OUT_ROOT = "atelier-report"        # 받은 HTML 의 자리 — 임시 폴더 아래

EXIT_OK, EXIT_FAIL, EXIT_CONFIG = 0, 1, 2

# 추천 줄 · 서브 줄 — atelier `app/static/app.js` 의 `adviceRows` · `adviceSubs` 를 옮겼다(atelier 7f357211 판).
# 손으로 따라간다: 저쪽 지시문(`prompts/advise-system.md` 「어떻게 답하나」)과 정규식이 바뀌면 여기도 고친다 — 저쪽
# `adviceRows` 곁말이 이 자리를 가리킨다. 이름은 디자인 목록과 대조해 없는 것은 버린다(저쪽 난간 그대로).
# `변형:` 줄은 안 가져왔다 — 다이얼 없이 보내면 렌더가 모드 기본값을 세운다(atelier assemble).
ADVICE_ROW = re.compile(r"^\s*추천\s*[:：]\s*([^|｜]+?)\s*[|｜]\s*(?:(웹|메일)\s*[|｜]\s*)?(.+?)\s*$")
ADVICE_SUB = re.compile(r"^\s*서브\s*[:：]\s*([^|｜]+?)\s*[|｜]\s*(.+?)\s*$")

# 원문 글의 그림 줄 — 표준 마크다운 그림 문법. 경로는 `(<…>)` 로 감싼 꼴이 먼저다(괄호 · 빈칸이 든 경로).
SOURCE_IMAGE = re.compile(r"!\[([^\]]*)\]\(\s*(?:<([^>]+)>|([^)]+?))\s*\)")
OUTSIDE_REF = re.compile(r"^(?:https?:|data:|cid:)", re.I)   # 이 PC 의 파일이 아닌 그림 줄 — 글자 그대로 둔다
# 박는 꼴 · 박힌 그림의 이름표 · 지면에 앉은 그림의 표식 — atelier 의 원문 현관이 원문에 박힌 그림을 그림으로 접어
# 눌러 싣고 렌더 뒤 그 자리에 되꽂는 계약을 빌렸다(atelier b408a7da 판 · `app/assemble.py` `fold_data_images` ·
# `_DATA_IMG_RE` · `fig_tag` · `docs/reference/http-api.md` 4 절). 손으로 따라간다 — 저쪽 정규식이 바뀌면 여기도 고친다.
# ⚠ 이름표가 `EMBED_MIME` 꼴을 벗어나면 저쪽이 그림으로 못 접어 base64 가 글자로 봉투에 샌다 — 보내기 전에 여기서 막는다.
EMBED_TAG = '<img src="data:{mime};base64,{data}">'
EMBED_MIME = re.compile(r"image/[a-z.+-]+")
# 저쪽이 그림으로 실을 수 있는 바이트의 머리(PNG · JPEG · GIF · BMP · TIFF, WebP 는 `raster` 가 따로 본다) — 저쪽의 접는 문턱은
# 이름표가 아니라 속이다(같은 판 `fold_data_images` 의 「실을 수 있나」). 이름만 그림인 파일(EMF · WMF · SVG · 그림 아닌 것)은 못 접힌다
RASTER_HEADS = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"BM", b"II*\x00", b"MM\x00*")
SEATED_FIGURE = re.compile(rb'\bdata-atelier-fig="(\d+)"')


class Stop(Exception):
    def __init__(self, code: int, message: str, next_step: str):
        super().__init__(message)
        self.code, self.next_step = code, next_step


class Server:
    """아뜰리에 서버 한 대 — 자격 머리를 실어 JSON 문을 두드린다."""

    def __init__(self, base: str, key: str):
        self.base = base.rstrip("/")
        self.key = key
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.heads = None

    def _send(self, method: str, path: str, body=None, *, creds=True, raw=False):
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            req.add_header("content-type", "application/json")
        if creds:
            for name, value in self.cred_heads().items():
                req.add_header(name, value)
        try:
            with self.opener.open(req, timeout=REQUEST_TIMEOUT_S) as res:
                payload = res.read()
        except urllib.error.HTTPError as exc:
            try:
                why = json.loads(exc.read().decode("utf-8")).get("error", "")
            except (ValueError, AttributeError):
                why = ""
            raise Stop(EXIT_FAIL, f"아뜰리에가 {path} 를 {exc.code} 로 거절했다 — {why or exc.reason}",
                       "그 말을 사람에게 그대로 전한다") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise Stop(EXIT_FAIL, f"아뜰리에 서버 {self.base} 에 못 닿았다({exc})",
                       f"사내망 안인가 · 서버가 떠 있나 본다. 주소가 다르면 {URL_ENV} 로 준다") from exc
        return payload if raw else json.loads(payload.decode("utf-8"))

    def cred_heads(self) -> dict:
        if self.heads is None:
            names = self._send("GET", "/api/status", creds=False).get("creds_headers") or {}
            if not all(names.get(k) for k in ("key", "provider", "model")):
                raise Stop(EXIT_FAIL, "아뜰리에가 자격 머리 이름을 안 댔다(/api/status 의 creds_headers)",
                           "서버 판이 이 스크립트와 맞는지 본다")
            self.heads = {names["key"]: self.key, names["provider"]: PROVIDER, names["model"]: MODEL}
        return self.heads

    def get(self, path, **kw):
        return self._send("GET", path, **kw)

    def post(self, path, body):
        return self._send("POST", path, body)


def server_from_env() -> Server:
    key = os.environ.get(KEY_ENV, "").strip()
    if not key:
        raise Stop(EXIT_CONFIG, f"키가 없다 — 환경값 {KEY_ENV} 가 비었다",
                   "설치(PAISetup)가 회사 키를 깔았는지 사람에게 묻는다. 새 셸에서 다시 연다")
    return Server(os.environ.get(URL_ENV, "").strip() or DEFAULT_URL, key)


def pick_design(reply: str, slugs: set[str]) -> tuple[str, str, str]:
    """추천 답에서 (디자인, 서브, 지면) 을 고른다 — 목록에 있는 첫 줄. 서브 · 지면(「웹」 · 「메일」)은 없으면 빈 글자."""
    row = next((m for m in map(ADVICE_ROW.match, reply.splitlines()) if m and m.group(1).strip() in slugs), None)
    design, page = (row.group(1).strip(), row.group(2) or "") if row else ("", "")
    sub = next((m.group(1).strip() for m in map(ADVICE_SUB.match, reply.splitlines())
                if m and m.group(1).strip() in slugs and m.group(1).strip() != design), "")
    return design, sub, page


def raster(raw: bytes) -> bool:
    """그 바이트가 아뜰리에가 그림으로 실을 수 있는 꼴인가 — 파일 머리로 가린다."""
    return raw.startswith(RASTER_HEADS) or (raw[:4] == b"RIFF" and raw[8:12] == b"WEBP")


def embed_images(source: str, base: pathlib.Path) -> tuple[str, list[str]]:
    """원문 글의 그림 줄을 박힌 그림 태그로 바꾼다 — (바꾼 글, 박은 파일 이름들).

    그림은 제 줄에 서고 캡션은 그 아랫줄 글자로 남는다. 바깥 주소의 그림 줄은 안 건드린다. 파일이 없거나 그림
    이름표를 못 얻거나 속이 실을 수 있는 그림(`raster`)이 아니면 `Stop`(설정 오류)이다.
    """
    names = []

    def embed(m):
        caption, ref = m.group(1).strip(), (m.group(2) or m.group(3)).strip()
        if OUTSIDE_REF.match(ref):
            return m.group(0)
        path = pathlib.Path(ref).expanduser()
        path = path if path.is_absolute() else base / path
        if not path.is_file():
            raise Stop(EXIT_CONFIG, f"원문이 가리킨 그림 파일이 없다: {path}",
                       "경로를 바로잡는다 — 원문 파일의 폴더에서 풀고, 괄호가 든 경로는 (<경로>) 로 감싼다")
        mime = (mimetypes.guess_type(path.name)[0] or "").lower()
        raw = path.read_bytes()
        if not EMBED_MIME.fullmatch(mime) or not raster(raw):
            raise Stop(EXIT_CONFIG, f"그림으로 실을 수 없는 파일이다: {path.name}",
                       "PNG 나 JPEG 로 바꿔 그 경로를 원문에 적는다")
        names.append(path.name)
        tag = EMBED_TAG.format(mime=mime, data=base64.b64encode(raw).decode("ascii"))
        return "\n\n" + tag + ("\n" + caption if caption else "") + "\n\n"

    return SOURCE_IMAGE.sub(embed, source), names


def out_path(doc: str, version: int) -> pathlib.Path:
    folder = pathlib.Path(tempfile.gettempdir()) / OUT_ROOT
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[\\/:*?"<>|\s]+', "_", doc).strip("_") or "doc"
    return folder / f"{safe}-v{version}.html"


def save(server: Server, doc: str, version: int) -> pathlib.Path:
    html = server.get(f"/out/{urllib.parse.quote(doc)}/v{version}.html", creds=False, raw=True)
    path = out_path(doc, version)
    path.write_bytes(html)
    return path


def cmd_make(args, server: Server) -> None:
    source_file = pathlib.Path(args.source_file).expanduser()
    if not source_file.is_file():
        raise Stop(EXIT_CONFIG, f"원문 파일이 없다: {source_file}", "보고 글을 UTF-8 글 파일로 쓰고 그 경로를 준다")
    source = source_file.read_text(encoding="utf-8").strip()
    if not source:
        raise Stop(EXIT_CONFIG, "원문이 비었다", "보고 글을 채운다")
    # 추천은 글만 보고 고른다 — 박은 판은 렌더에만 싣는다(추천 문은 그림을 안 접어 base64 가 글자로 간다)
    with_images, images = embed_images(source, source_file.parent)

    print(f"1/3 추천 — {server.base} · {PROVIDER} · {MODEL}", flush=True)
    advice = server.post("/api/advise", {"source": source, "single": True})
    if advice.get("dry_run"):
        raise Stop(EXIT_CONFIG, "서버가 드라이런으로 답했다 — 키가 안 먹었거나 이 서버가 회사 GPT 갈래를 닫았다",
                   f"{KEY_ENV} 가 회사 키인지 · 서버의 ATELIER_SITES 에 회사 담장이 열렸는지 본다")
    slugs = {d.get("slug") for d in server.get("/api/designs", creds=False) if not d.get("custom")}
    design, sub, page = pick_design(advice.get("reply") or "", slugs)
    if not design:
        print(advice.get("reply") or "")
        raise Stop(EXIT_FAIL, "추천을 디자인 하나로 못 읽었다(위가 온 답 그대로다)",
                   "아뜰리에 화면에서 디자인을 골라 만들거나, 원문을 다듬어 다시 돌린다")
    mode, why = args.mode, ""
    if mode == AUTO_MODE:
        mode = ADVICE_PAGE.get(page, AUTO_FALLBACK)
        why = "(추천이 골랐다)" if page in ADVICE_PAGE else "(추천이 지면을 안 짚었다)"
    print(f"   디자인 {design}" + (f" · 서브 {sub}" if sub else ""), flush=True)

    extra = args.extra.strip()
    print(f"2/3 렌더 — 모드 {mode}{why}" + (f" · 그림 {len(images)} 장({', '.join(images)})" if images else "")
          + (f" · 요청 「{extra}」" if extra else ""), flush=True)
    landed = server.post("/api/render", {"source": with_images, "design": design, "mode": mode,
                                         "sub_design": sub, "extra": extra, "files": [], "emoji": True})
    if not landed.get("doc") or "reply" in landed:
        print(landed.get("reply") or "")
        raise Stop(EXIT_FAIL, "문서 대신 말이 왔다(위가 그 말이다)" + (" — 만들다 끊겼다" if landed.get("cut") else ""),
                   "그 물음에 답할 것을 원문에 더해 다시 돌리거나, 아뜰리에 화면에서 잇는다")
    if landed.get("dry_run"):
        raise Stop(EXIT_CONFIG, "렌더가 드라이런으로 섰다", f"{KEY_ENV} 와 서버의 회사 담장을 본다")
    doc, version = landed["doc"], landed["version"]

    print("3/3 자체 점검", flush=True)
    try:
        checked = server.post("/api/selfcheck", {"doc": doc})
        version = checked.get("version", version)
    except Stop as exc:
        print(f"   자체 점검을 건너뛰었다 — {exc}", flush=True)
    path = save(server, doc, version)
    print(f"지었다: 문서 {doc} · 판 {version}")
    print(f"HTML: {path}")
    print(f"화면: {server.base}/out/{urllib.parse.quote(doc)}/v{version}.html")
    # 그림이 섰나는 받은 끝 판에서 센다 — 모델이 자리 줄을 지우면 아뜰리에는 그 그림을 아무 데도 안 놓는다
    lost = len(images) - len(set(SEATED_FIGURE.findall(path.read_bytes())))
    if lost > 0:
        print(f"그림 {len(images)} 장 가운데 {lost} 장이 지면에 안 섰다")
        print(f"다음: 사람에게 그림이 빠졌다고 말하고 open {doc} 으로 고치기 화면에서 그림을 놓게 하거나, 원문의 그림 자리를 "
              "다듬어 다시 짓는다")
        return
    print(f"다음: 사람에게 이 HTML 을 확인하거나 고칠지 묻는다 — 고치면 open {doc} · 그대로 보내면 이 파일을 company-mail 로")


def cmd_open(args, server: Server) -> None:
    ticket = server.post("/api/handoff", {"doc": args.doc})
    url = server.base + ticket["url"]
    opened = webbrowser.open(url)
    print(f"고치기 화면: 문서 {args.doc} · {PROVIDER} · {MODEL}" + ("" if opened else " — 브라우저를 못 띄웠다"))
    if not opened:
        print(f"이 주소를 {ticket['ttl']} 초 안에 브라우저로 연다(한 번만 열린다): {url}")
    print(f"다음: 사람이 화면에서 고치고 「다 고쳤다」고 하면 fetch {args.doc} 로 최신 판을 받는다")


def cmd_fetch(args, server: Server) -> None:
    meta = next((m for m in server.get("/api/docs", creds=False) if m.get("id") == args.doc), None)
    if not meta or not meta.get("versions"):
        raise Stop(EXIT_CONFIG, f"아뜰리에 문서함에 판이 선 그 문서가 없다: {args.doc}", "make 가 낸 문서 이름을 그대로 준다")
    version = len(meta["versions"])
    path = save(server, args.doc, version)
    print(f"받았다: 문서 {args.doc} · 최신 판 {version}")
    print(f"HTML: {path}")
    print("다음: 이 파일을 company-mail 의 save-draft --html-file(본문) 이나 --attach(첨부)로 넘긴다")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="atelier.py", description="사내 아뜰리에로 보고를 짓고 고치기 화면으로 넘긴다 — 머리말이 계약이다")
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("make")
    q.set_defaults(fn=cmd_make)
    q.add_argument("--source-file", required=True, help="보고 글(UTF-8) — 그림은 ![캡션](경로) 줄로 그 자리에 적는다")
    q.add_argument("--mode", default=DEFAULT_MODE, choices=(*ADVICE_PAGE.values(), AUTO_MODE),
                   help="mail 은 문서형태(메일 본문 지면) · web 은 웹페이지(브라우저로 여는 판) · auto 는 추천이 고른 지면")
    q.add_argument("--extra", default="", help="어떻게 정리할지 아뜰리에에 건네는 요청 한 줄")
    for name, fn in (("open", cmd_open), ("fetch", cmd_fetch)):
        q = sub.add_parser(name)
        q.set_defaults(fn=fn)
        q.add_argument("doc", help="make 가 낸 문서 이름")
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        args.fn(args, server_from_env())
    except Stop as exc:
        print(f"못 했다: {exc}")
        print(f"다음: {exc.next_step}")
        return exc.code
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
