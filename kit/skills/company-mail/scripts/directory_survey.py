"""웹메일 주소록 화면이 서버에 무엇을 묻는지를 HAR 하나에서 거둔다 — 주소록의 기능을 한 판에 다 조사하는 손.

무엇을 하나
    회사 PC 에서 사람이 웹메일 「새 메일」의 받는 사람 고름 창을 열고, Edge 개발자 도구(F12) 네트워크 탭에 「로그 유지」를 켠 채
    그 창의 기능을 다 눌러 본 뒤 「HAR 로 모두 저장」한 파일을 읽는다. 조직도 펼치기(회사 → 실 → 그룹) · 부서 누르기 · 이름 ·
    부서 · 직책 찾기 · 탭마다(개인 주소록 · 그룹 · 배포 목록 · 최근 · 즐겨찾기) 한 번씩. 그 판에 웹메일이 부른 요청을 주소마다
    한 덩어리로 묶어, 질의 칸 이름과 보기 값 · 답의 꼴(JSON 의 열쇠 · 배열 원소의 칸 · 코드 칸의 값 몇) · 읽기 길이 이미 그
    주소를 묻나(``inbox.read_only_patterns``)를 낸다. 받은 스크립트 본문에서 ``.nsf/…?Open…`` 꼴 주소를 더 찾아, 이 판에 안
    눌린 기능의 주소도 「스크립트에만 보인 주소」로 낸다.

부르는 꼴::

    python -X utf8 -I directory_survey.py <HAR 파일> [--db <메일 파일 경로>.nsf] [--all]

    ``--db`` 는 메일함 경로(``mail.py session`` 이 보이는 주소의 서버 뒤 ``…/<번호>.nsf`` 부분)를 앞 ``/`` 없이 준다 — Git Bash 는
    ``/`` 로 시작하는 인자를 윈도 경로로 바꿔 넘긴다. 주면 메일함 안 주소도 읽기 길에 대 본다. ``--all`` 은 주소록 밖 주소(메일 보기 · 본문)도 낸다 — 기본은 주소록 · 사람 · 조직에 닿는 주소만.

무엇을 내나
    사람이 읽는 글줄. 종료 값 0 거뒀다 · 2 파일을 못 읽었다(경로 · HAR 꼴).

지키는 것
    요청 · 응답의 머리(쿠키 · 인증)는 읽지도 내지도 않는다 — HAR 에는 세션 쿠키가 든다. HAR 파일은 저장소 밖에 두고 쓴 뒤
    지운다. 보기 값은 앞 몇 개 · 앞 글자 몇만 낸다. 서버에 아무것도 묻지 않는다 — 파일만 읽는다.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.parse
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent

# 주소록 · 사람 · 조직에 닿는 주소로 보는 낱말 — 경로에 하나라도 들면 낸다(``--all`` 이면 다 낸다)
DIRECTORY_WORDS = ("profile.nsf", "names.nsf", "org", "addr", "dept", "user", "person", "people", "group", "member",
                   "contact", "recipient", "buddy", "favorite", "recent")
STATIC_EXT = re.compile(r"\.(js|css|png|gif|jpe?g|svg|ico|woff2?|ttf|eot|map)(\?|$)", re.IGNORECASE)
SCRIPT_URL = re.compile(r"""["'](/?[\w./$-]+\.nsf/[\w$%./-]+\?(?:Open|Read)\w*[^"'\s]*)["']""", re.IGNORECASE)
CODE_KEY = re.compile(r"(code|type|kind|category|level|is_|yn$|flag|order|seq|depth|parent)", re.IGNORECASE)
SAMPLE_VALUES = 3          # 질의 칸 · 코드 칸마다 내는 보기 값의 수
SAMPLE_CHARS = 60          # 보기 값 하나의 글자 상한
SHAPE_DEPTH = 4            # JSON 꼴을 내려가 보는 깊이
TEXT_HEAD = 160            # JSON 이 아닌 답의 앞 글자


def load_har(path: pathlib.Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    entries = data.get("log", {}).get("entries")
    if not isinstance(entries, list):
        raise ValueError("HAR 꼴이 아니다 — log.entries 가 없다")
    return entries


def body_text(entry: dict) -> str:
    content = entry.get("response", {}).get("content", {}) or {}
    text = content.get("text") or ""
    if content.get("encoding") == "base64":
        import base64
        try:
            text = base64.b64decode(text).decode("utf-8", errors="replace")
        except ValueError:
            return ""
    return text


def endpoint(url: str) -> tuple[str, str, dict[str, list[str]], str]:
    """(호스트, 경로 · 명령, 질의 칸, 서버 뿌리부터의 경로+질의). Domino 의 명령(``?OpenAgent``)은 경로에 붙여 한 주소로 본다."""
    parts = urllib.parse.urlsplit(url)
    query = parts.query
    command, _, rest = query.partition("&")
    fields = urllib.parse.parse_qs(rest if "=" not in command else query, keep_blank_values=True)
    named = command if command and "=" not in command else ""
    path = parts.path + (f"?{named}" if named else "")
    # 읽기 길(inbox.py)은 질의 값을 urlencode(safe="()") 로 짓는다 — 브라우저가 둔 「/」 같은 글자를 같은 꼴로 다시 지어 대 본다
    pairs = urllib.parse.urlencode([(k, v) for k, vs in fields.items() for v in vs], safe="()")
    served = parts.path + ("?" + "&".join(x for x in (named, pairs) if x) if (named or pairs) else "")
    return parts.netloc, path, fields, served


def shape(value, depth: int = 0, codes: dict | None = None, at: str = "") -> str:
    """JSON 값의 꼴 — 열쇠와 형, 배열은 길이와 원소 칸의 합. 코드 같은 칸(CODE_KEY)의 값은 ``codes`` 에 모은다."""
    if depth >= SHAPE_DEPTH:
        return "…"
    if isinstance(value, dict):
        inner = ", ".join(f"{k}: {shape(v, depth + 1, codes, f'{at}.{k}')}" for k, v in value.items())
        return "{" + inner + "}"
    if isinstance(value, list):
        merged: dict = {}
        for item in value:
            if isinstance(item, dict):
                for k, v in item.items():
                    merged.setdefault(k, v)
                    if codes is not None and CODE_KEY.search(k) and isinstance(v, (str, int, bool)):
                        seen = codes.setdefault(f"{at}[].{k}", [])
                        if str(v) not in seen and len(seen) < SAMPLE_VALUES * 3:
                            seen.append(str(v))
        if merged:
            return f"[{len(value)} × {shape(merged, depth + 1, codes, at + '[]')}]"
        return f"[{len(value)}" + (f" × {type(value[0]).__name__}]" if value else "]")
    if codes is not None and at and CODE_KEY.search(at.rsplit(".", 1)[-1]) and isinstance(value, (str, int, bool)):
        seen = codes.setdefault(at, [])
        if str(value) not in seen and len(seen) < SAMPLE_VALUES * 3:
            seen.append(str(value))
    return type(value).__name__


def clip(text: str) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= SAMPLE_CHARS else text[:SAMPLE_CHARS] + "…"


def survey(entries: list[dict], *, patterns=(), everything: bool = False) -> list[str]:
    groups: dict[tuple[str, str, str], dict] = {}
    scripts: set[str] = set()
    for e in entries:
        req = e.get("request", {})
        url, method = req.get("url", ""), req.get("method", "GET")
        if not url.startswith("http"):
            continue
        host, path, fields, served = endpoint(url)
        mime = (e.get("response", {}).get("content", {}) or {}).get("mimeType", "")
        if STATIC_EXT.search(urllib.parse.urlsplit(url).path) or "javascript" in mime:
            scripts.update(SCRIPT_URL.findall(body_text(e)))
            continue
        if not everything and not any(w in path.lower() for w in DIRECTORY_WORDS):
            continue
        g = groups.setdefault((method, host, path), {"count": 0, "fields": defaultdict(list), "status": set(),
                                                       "mime": set(), "shapes": [], "codes": {}, "served": [],
                                                       "posted": set()})
        g["count"] += 1
        g["status"].add(e.get("response", {}).get("status"))
        g["mime"].add(mime.split(";")[0])
        g["served"].append(served)
        for k, vs in fields.items():
            for v in vs:
                if v not in g["fields"][k] and len(g["fields"][k]) < SAMPLE_VALUES:
                    g["fields"][k].append(v)
        post = req.get("postData", {}) or {}
        for p in post.get("params", []) or []:
            g["posted"].add(p.get("name", ""))
        text = body_text(e).strip()
        try:
            form = shape(json.loads(text), codes=g["codes"])
        except ValueError:
            form = ("XML <" + m.group(1) + ">" if (m := re.match(r"^\s*(?:<\?xml[^>]*>\s*)?<([\w:-]+)", text))
                    else clip(text[:TEXT_HEAD]) or "(빈 답)")
        if form not in g["shapes"]:
            g["shapes"].append(form)

    out = [f"잡은 주소 {len(groups)} 개" + ("" if everything else " — 주소록 · 사람 · 조직에 닿는 것만(--all 이면 다)")]
    for (method, host, path), g in sorted(groups.items(), key=lambda kv: -kv[1]["count"]):
        served = any(p.match(s) for s in g["served"] for p in patterns) if patterns else None
        mark = {True: "읽기 길이 이미 묻는다", False: "읽기 길 목록 밖 — 읽음을 안 바꾸는지 보고 inbox.read_only_patterns 에 더해야 묻는다",
                None: "읽기 길에 안 대 봄"}[served]
        out.append("")
        out.append(f"■ {method} {host}{path} · {g['count']} 번 · 상태 {sorted(s for s in g['status'] if s is not None)} · "
                   f"{', '.join(sorted(m for m in g['mime'] if m)) or '형 없음'}")
        out.append(f"  {mark}")
        for k, vs in g["fields"].items():
            out.append(f"  칸 {k} = " + " | ".join(clip(v) or "(빈 값)" for v in vs))
        if g["posted"]:
            out.append(f"  ⚠ POST 칸: {', '.join(sorted(g['posted']))} — 무엇을 바꾸는 요청인지 먼저 본다")
        for s in g["shapes"][:SAMPLE_VALUES]:
            out.append(f"  답: {clip(s) if len(s) > 400 else s}")
        for k, vs in g["codes"].items():
            out.append(f"  값 {k}: " + " | ".join(clip(v) for v in vs))
    seen_paths = {p for (_, _, p) in groups}
    unseen = sorted({u for u in scripts if endpoint("http://x" + ("" if u.startswith("/") else "/") + u)[1] not in seen_paths})
    if unseen:
        out.append("")
        out.append(f"스크립트에만 보인 주소 {len(unseen)} 개 — 이 판에 안 눌린 기능일 수 있다")
        out.extend(f"  {u}" for u in unseen)
    return out


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="directory_survey.py", description="웹메일 주소록 화면의 요청을 HAR 에서 거둔다")
    p.add_argument("har")
    p.add_argument("--db", default="", help="메일함 경로 <…>.nsf(앞 / 없이) — 주면 메일함 안 주소도 읽기 길에 대 본다")
    p.add_argument("--all", action="store_true", help="주소록 밖 주소도 낸다")
    args = p.parse_args(argv)
    try:
        entries = load_har(pathlib.Path(args.har))
    except (OSError, ValueError) as exc:
        print(f"HAR 를 못 읽었다: {exc}")
        return 2
    sys.path.insert(0, str(HERE))
    import inbox  # noqa: PLC0415 — 자리를 넣은 뒤에 싣는다
    db = args.db.strip().replace("\\", "/")
    if ":" in db:
        print(f"--db 가 윈도 경로로 바뀌어 왔다({db}) — 앞 / 없이 준다(예: mail/12345.nsf)")
        return 2
    patterns = inbox.read_only_patterns("/" + db.lstrip("/") if db else "/__no_mailbox__.nsf")
    print("\n".join(survey(entries, patterns=patterns, everything=args.all)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
