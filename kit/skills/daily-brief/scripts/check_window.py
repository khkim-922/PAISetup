"""일일 보고 창이 절 수와 상관없이 같은 꼴로 서고, 링크는 메일 번호에서만 짓고, 글은 글자로 세우고, 보고 글을 곁에 남기나를 문다.

    python -X utf8 -I check_window.py [스킬 폴더] [--teeth]

층 — 쓰는 사람의 계약. 곁의 `window.py` 를 명령 그대로 부르고 지은 HTML 을 표준 라이브러리의 HTML 읽개로 잰다(브라우저는 가짜가 받는다).
남기는 까닭 — 판정마다 check-design 1 절의 넷을 다 지난다(판정별 표 · 표본은 `references/DESIGN.md` 「검사가 남는 까닭」).
언제 걷나 — 보고 창이 스킬에서 빠지거나 그 계약을 다른 검사가 들 때. 보고 글을 다음 보고의 기록으로 삼지 않게 되면 「곁에 남는다」 · 「끝의 두 절」.
여기서 못 재는 것 — 디자인이 보이는 그대로 · 실제 브라우저 · 회사 웹메일에서 링크가 열리나 · 모델이 꼴대로 쓰나(같은 문서).

물림 — `--teeth` 는 계약 판정에 이어 판정마다 그 판정이 지키는 한 줄을 끈 사본에서 빨강을 본다. 계약 판정이 하나라도 빨가면 안 돌린다 —
늘 지는 판 앞에서는 모든 사본이 「잡혔다」로 센다. 사본을 못 심으면 그 물림이 빨갛다. 푸시 문은 인자 없이 불러 계약 판정만 돈다.

폴더를 안 주면 이 파일이 든 스킬 폴더(`SKILL.md` · `scripts/` · `assets/`)만 읽는다 — 푸시 문(`skill-checks`)은 `.claude/skills` 만
임시 자리로 내보내 거기서 돌린다. 기대값은 표본을 지은 뜻 · 꼴의 표시를 센 수 · 계약에서 낸다 — 돌린 값에서 거꾸로 내지 않는다.
종료 값 — 끝 줄이 「통과 N/N」이면 0, 하나라도 어긋나면 1, 스크립트 · 틀을 못 찾았으면 2.
"""

from __future__ import annotations

import ast
import html.parser
import http.server
import os
import socket
import threading
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import traceback

# ── 판정 손 — 씨앗 `_verdict.py` 의 일부를 줄여 둔 것(까닭은 `references/DESIGN.md`) ─────────────────────

# 한글 Windows 는 stdout 을 cp949 · strict 로 잡아, 판정 기호를 찍다 리디렉션 · 파이프에서만 죽는다 — `-X utf8` 없이 불려도 안 죽게 다시 잡는다
sys.stdout.reconfigure(encoding="utf-8")

EXIT_OK, EXIT_MISMATCH, EXIT_UNMEASURED = 0, 1, 2   # 쟀고 맞다 · 어긋났다 · 못 쟀다(초록이 아니다)
FAILS: list[str] = []
PASSES: list[str] = []


class Unmeasured(SystemExit):
    """「못 쟀다」로 그 자리에서 나간다 — 까닭을 stdout 에 찍고 2 로. `raise SystemExit("글자")` 는 1 로 나가 훅이 「어긋났다」로 읽는다."""

    def __init__(self, why):
        super().__init__(EXIT_UNMEASURED)
        self.why = str(why)
        print(self.why)

    def __str__(self):
        return self.why


def report(name, ok, detail=()):
    """계약 판정 한 줄 — 상세(줄들)는 실패에만 찍는다."""
    (PASSES if ok else FAILS).append(name)
    print(f"[{'OK ' if ok else 'NG '}] {name}")
    for row in detail if not ok else ():
        print(f"       {row}")


def edge(text):
    """통과할 때도 보여야 하는 경계 — 판정이 아니라 범위의 고지라 계수에 안 든다."""
    print(f"  ⚠ {text}")


HERE = pathlib.Path(__file__).resolve().parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
WITH_TEETH = "--teeth" in sys.argv[1:]          # 물림까지 — 정기 판의 몫(머리말 「물림」)
SKILL = pathlib.Path(ARGS[0]).resolve() if ARGS else HERE.parent
SCRIPT_REL = pathlib.Path("scripts") / "window.py"
TEMPLATE_REL = pathlib.Path("assets") / "report.html"
TIMEOUT_S = 30

MAILBOX = "https://mail.gaon.example/mail3/20231234.nsf"     # 회사 메일 손의 session 이 내는 꼴 — 가상의 호스트
MAIL_HREF = "{mailbox}/XML_Inbox/{unid}?OpenDocument"       # 계약 — 이 꼴만이 메일 링크다
REF = re.compile(r"\]\(mail:([0-9A-Fa-f]{32})\)")           # 꼴의 메일 링크 표시 — 표본에서 기대 링크를 센다
HEX32 = re.compile(r"\b[0-9A-Fa-f]{32}\b")
END_SECTIONS = ("이 보고가 본 데", "끝났다고 하신 것")      # 계약 — 다음 보고가 기대는 끝의 두 절(사용자가 정한 겉 · 스킬 글 「남긴다」)

# ── 표본 — 꼴대로 쓴 가상의 하루(가상의 회사 · 사람) ─────────────────────────────

THREE_BODY = """# 11/17(화) 아침 보고
오전 10시 품질 회의 · 시험 성적서 승인은 오늘 17시까지

오늘의 마감
@ 10:00 — 품질 회의(본관 3층) — 지난주 불량 분석을 들고 가십니다
@ 17:00 — 시험 성적서 승인

오늘은 조용한 날입니다. 정하실 것은 둘입니다.

## 오늘 정하실 것
1. **시험 성적서 승인** — 17:00까지 {오늘 17:00}
   - 3로트 가운데 1로트의 수분 값이 상한에 붙어 있습니다.
   - 기다리는 분: 오세린 대리(14일부터)
   - 근거: [오세린 11/14 「성적서 승인 요청」](mail:0000000000000000A1B2C3D4E5F70001)
2. **협력사 납기 회신** — 내일까지
   - 동해정밀이 12월 물량을 이틀 당겨 달라고 했습니다.
   - 근거: [동해정밀 11/16 「12월 납기 조정 요청」](mail:0000000000000000A1B2C3D4E5F70002)

## 답을 기다리시는 일
- **설비 점검 결과** — 백준호 과장께 13일에 청하셨습니다 {!15일 기한 지남}
  - 근거: [백준호 11/13](mail:0000000000000000A1B2C3D4E5F70003)
- **하반기 교육 일정 회신** — 인사팀 문다은 님이 청함

## 알려 드릴 것
- 메일함 사용량이 81%입니다.
"""
THREE = THREE_BODY + f"""
## {END_SECTIONS[0]}
11/17(화) 07:40 — 지난 보고(11/16 08:00) 뒤 받은편지함과 폴더의 새 메일 9통을 훑어 4통을 열었습니다.

## {END_SECTIONS[1]}
- 하계 휴가 계획 회신 — 11/13 보고 뒤에 말씀하셨습니다 [총무팀 11/10](mail:0000000000000000A1B2C3D4E5F70004)
"""
THREE_LINES = ["3로트 가운데 1로트", "동해정밀이 12월 물량", "설비 점검 결과", "하반기 교육 일정 회신", "메일함 사용량이 81%", "하계 휴가 계획 회신"]

# Windows 도구(PowerShell 의 Set-Content 따위)가 사용자 폴더에 쓴 보고 글 — cp949 · CRLF. cp949 에 없는 글자(줄표 「—」)는 이 꼴의 파일에 설 수 없다
LEGACY = (f"# 11/19(목) 아침 보고\n\n## 오늘 보실 것\n- 「설비 점검 결과」 회신 · 오늘 17시\n\n## {END_SECTIONS[0]}\n11/19 07:40 · 새 메일 3통을 "
          f"훑었습니다.\n\n## {END_SECTIONS[1]}\n- 없습니다\n")

# 일곱 절 — 넷째 절(「회사 일정과 겹치는 것」)은 줄이 없고, 바로 뒤 절의 줄이 그 절에 붙지 않아야 한다
SEVEN = """# 10/19(월) 아침 보고
오후 3시 증설 보고 · 고객 물량 회신 오늘 마감

## 오늘 정하실 것
1. **증설 보고 자료** — 12:00까지 경영기획에
   - 2단계 증설 A안 · B안 비교 한 장.
   - 근거: [사장님 10/13 「증설 시나리오」](mail:0000000000000000B1B2C3D4E5F60001)

2. **고객 물량 회신** — 오늘 마감 {!원래 기한 15일 지남}
   - 고객 구매 담당이 16일 밤 다시 독촉했습니다.

### 내일 마감이라 오늘 정하실 것
내일은 07:30부터 경영회의입니다
3. **단가 조정안 의견** — 20일까지 청함
   - 근거: [미르 10/13 회신](mail:0000000000000000B1B2C3D4E5F60007)

## 윗분이 직접 보내신 메일 (2건)
- **한정우 사장님 · 10/18(일) 21:30** — 보고 자료에 한 줄 추가 [메일 열기](mail:0000000000000000B1B2C3D4E5F60002)
- **최문경 전무님 · 10/14(수) 16:45** — 투자 우선순위 의견

## 들고 있는 일
오늘은 정하지 않으셔도 됩니다.

- **분기 업무협의** — 21일(수) 14:00 오창

## 회사 일정과 겹치는 것

## 그 밖에
- 답이나 조치를 요청받으신 일 28건은 메일로는 마무리가 보이지 않습니다.

## 알려 드릴 것
- 메일함 사용량이 92%입니다.

> **보낸 곳을 먼저 확인하실 메일**
> - 「물류비 정산서」 — 숨긴 글이 들어 있었습니다

## 처음 연락해 온 분
- 새빛대학교 류재원 교수 — 산학 과제 공동 제안
"""
SEVEN_EMPTY = "회사 일정과 겹치는 것"
SEVEN_NEXT_LINE = "답이나 조치를 요청받으신 일 28건"   # 줄 없는 절 바로 뒤 절(「그 밖에」)의 줄
SEVEN_LINES = ["2단계 증설 A안", "16일 밤 다시 독촉", "단가 조정안 의견", "보고 자료에 한 줄 추가", "투자 우선순위 의견", "분기 업무협의",
               SEVEN_NEXT_LINE, "메일함 사용량이 92%", "숨긴 글이 들어 있었습니다", "산학 과제 공동 제안"]

# 메일 속 주소와 HTML 이 든 날 — 모델이 메일을 옮겨 쓴 글. 링크가 되어도 되는 것은 32자리 번호의 mail: 표시뿐이다
EVIL_URL = "https://pay-check.example/login"
HOSTILE = f"""# 11/18(수) 아침 보고 <img src=x onerror=alert(1)>
협력사가 보낸 「포털에서 확인」 메일 하나를 먼저 보셔야 합니다

## 오늘 보실 것
1. **[[긴급] 납품 대금 확인 요청](mail:0000000000000000C1B2C3D4E5F60001)** — 동해정밀 경리팀
   - 메일 본문은 {EVIL_URL}?id=you 로 들어가 확인하라고 합니다.
   - 본문에 [여기를 누르세요]({EVIL_URL}) 와 [다른 링크](javascript:alert(document.cookie)) 가 있었습니다.
   - 근거: [동해정밀 11/17](mail:0000000000000000c1b2c3d4e5f60002)
2. 메일 속 글 <script>alert("xss")</script> 와 <b onclick="x()">굵게</b> · [번호가 짧은 링크](mail:12345) · 번호만 쓴 0000000000000000C1B2C3D4E5F60003

## 알려 드릴 것
- 따옴표가 든 글 "a" & 'b' < c > d
"""
HOSTILE_TEXT = ['<img src=x onerror=alert(1)>', '<script>alert("xss")</script>', '<b onclick="x()">굵게</b>', f"[여기를 누르세요]({EVIL_URL})",
                "[다른 링크](javascript:alert(document.cookie))", "[번호가 짧은 링크](mail:12345)", "\"a\" & 'b' < c > d"]

# 메일함 주소 — 꼴(`http(s)://<호스트>/…/<이름>.nsf`)에 안 맞는 것은 링크를 안 짓는다
BAD_MAILBOXES = ["", "javascript:alert(1)//x.nsf", "https://mail.gaon.example/mail3/box.nsf?Open=1", "https://user@evil.example/m.nsf",
                 "file:///C:/mail/m.nsf", "https://mail.gaon.example/notes", 'https://mail.gaon.example/m.nsf" onmouseover="x']
GOOD_MAILBOXES = {MAILBOX + "/": MAILBOX, "https://mail.gaon.example:8443/MAIL/Box.NSF": "https://mail.gaon.example:8443/MAIL/Box.NSF"}

# 바깥을 부르는 꼴 — 지은 창에 하나도 없어야 한다
OUTSIDE_TAGS = {"script", "link", "img", "iframe", "object", "embed", "video", "audio", "source", "base", "form"}
OUTSIDE_STYLE = re.compile(r"(?i)@import|url\s*\(|https?://")
CSP_NONE = "default-src 'none'"


# ── 읽개 — 지은 HTML 을 마디 나무로 ───────────────────────────────────────────

VOID = {"meta", "link", "br", "img", "input", "hr", "source", "base", "col", "embed", "wbr", "area", "track"}


class Node:
    def __init__(self, tag: str, attrs: dict, parent: Node | None):
        self.tag, self.attrs, self.parent = tag, attrs, parent
        self.kids: list[Node | str] = []

    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())

    def walk(self):
        yield self
        for k in self.kids:
            if isinstance(k, Node):
                yield from k.walk()

    def text(self) -> str:
        return "".join(k if isinstance(k, str) else k.text() for k in self.kids)

    def find(self, tag: str | None = None, cls: str | None = None) -> list[Node]:
        return [n for n in self.walk() if (tag is None or n.tag == tag) and (cls is None or cls in n.classes())]


class Reader(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.at = self.root
        self.styles: list[str] = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.at)
        self.at.kids.append(node)
        if tag == "style":
            self._in_style = True
        if tag not in VOID:
            self.at = node

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        n = self.at
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.at = n.parent

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data)
        self.at.kids.append(data)


def read(page: str) -> Reader:
    r = Reader()
    r.feed(page)
    r.close()
    return r


# ── 부르기 ─────────────────────────────────────────────────────────────────

class Run:
    def __init__(self, code: int, out: str, page: str | None, names: list[str], kept: str | None):
        self.code, self.out, self.page = code, out, page
        self.names, self.kept = names, kept        # 그 폴더에 남은 파일 이름 · 남은 보고 글(.md 가 하나일 때 UTF-8 로 읽은 것)
        self.tree = read(page) if page is not None else None

    def body_text(self) -> str:
        return self.tree.root.find("body")[0].text() if self.tree else ""

    def mail_hrefs(self) -> list[str]:
        return [n.attrs.get("href", "") for n in self.tree.root.find("a") if not n.attrs.get("href", "").startswith("#")]


def run(skill: pathlib.Path, md: str, mailbox: str = MAILBOX, data: bytes | None = None) -> Run:
    """스크립트를 표준 입력(`data` 바이트, 없으면 `md` 를 UTF-8)으로 부른다 — 매번 새 빈 폴더에 짓고 HTML · 보고 글을 하나씩 읽는다."""
    out_dir = pathlib.Path(tempfile.mkdtemp())
    try:
        cmd = [sys.executable, "-X", "utf8", "-I", str(skill / SCRIPT_REL), "--dir", str(out_dir), "--mailbox", mailbox, "--no-open"]
        got = subprocess.run(cmd, input=md.encode("utf-8") if data is None else data, capture_output=True, timeout=TIMEOUT_S)
        out = (got.stdout + got.stderr).decode("utf-8", errors="replace")
        pages, texts = sorted(out_dir.glob("*.html")), sorted(out_dir.glob("*.md"))
        page = pages[0].read_text(encoding="utf-8") if len(pages) == 1 else None
        kept = texts[0].read_bytes().decode("utf-8", errors="replace") if len(texts) == 1 else None
        return Run(got.returncode, out, page, sorted(p.name for p in out_dir.iterdir()), kept)
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


def skill_example(skill: pathlib.Path) -> str | None:
    """스킬 글 「보고 글의 꼴」의 예 — 그 절 안의 첫 ```markdown 덩이."""
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    part = text.split("## 보고 글의 꼴", 1)
    if len(part) < 2:
        return None
    m = re.search(r"```markdown\n(.*?)\n```", part[1], re.S)
    return m.group(1) if m else None


def heads(md: str) -> list[str]:
    """꼴의 절 머리(「## 」)를 센다 — 기대 절 수의 원본은 표본 글이다."""
    return [line[3:].strip() for line in md.splitlines() if line.startswith("## ")]


# ── 판정 ──────────────────────────────────────────────────────────────────

def sections_stand(skill: pathlib.Path) -> tuple[bool, list[str]]:
    """절 셋 · 일곱(줄 없는 절 하나)의 날이 다 서고, 절마다 제 줄을 들고, 왼쪽 목록이 절을 다 가리킨다."""
    why: list[str] = []
    for name, md, lines in (("절 셋", THREE, THREE_LINES), ("절 일곱", SEVEN, SEVEN_LINES)):
        r = run(skill, md)
        if r.code != 0 or r.tree is None:
            why.append(f"{name}: 종료 값 {r.code} · 창 {'없음' if r.tree is None else '있음'} — {r.out.strip()[-200:]}")
            continue
        secs = r.tree.root.find("section")
        want = heads(md)
        got = [s.find("h2")[0].text().strip() if s.find("h2") else "" for s in secs]
        if got != want:
            why.append(f"{name}: 절 {got} — 글의 절 {want}")
        toc = {n.attrs.get("href") for n in r.tree.root.find("nav")[0].find("a")} if r.tree.root.find("nav") else set()
        missing = [s.attrs.get("id") for s in secs if f"#{s.attrs.get('id')}" not in toc]
        if missing:
            why.append(f"{name}: 왼쪽 목록이 안 가리키는 절 {missing}")
        text = r.body_text()
        lost = [w for w in lines if text.count(w) != 1]
        if lost:
            why.append(f"{name}: 한 번씩 서야 할 줄이 안 섰거나 겹쳤다 {lost}")
        if name == "절 일곱":
            empty = [s for s in secs if s.find("h2") and s.find("h2")[0].text().strip() == SEVEN_EMPTY]
            if not empty or empty[0].find("li") or SEVEN_NEXT_LINE in empty[0].text():
                why.append(f"{name}: 줄 없는 절 「{SEVEN_EMPTY}」이 없거나 다른 절의 줄을 들었다")
    return not why, why


def marks_render(skill: pathlib.Path) -> tuple[bool, list[str]]:
    """스킬 글의 예가 쓴 꼴마다 제 생김새가 선다 — 기대 수는 예의 표시를 센 것이다."""
    md = skill_example(skill)
    if md is None:
        return False, ["스킬 글에 「보고 글의 꼴」 절의 ```markdown 예가 없다 — 모델이 따라 쓸 꼴이 없다"]
    r = run(skill, md)
    if r.code != 0 or r.tree is None:
        return False, [f"예를 못 지었다: 종료 값 {r.code} — {r.out.strip()[-200:]}"]
    root = r.tree.root
    lines = md.splitlines()
    want = {
        "마감 시간줄의 점(「@ 」 줄)": (len(root.find("ol", "clock")[0].find("li")) if root.find("ol", "clock") else 0,
                                    sum(line.startswith("@ ") for line in lines)),
        "붉은 표지(「{!…}」)": (len(root.find("span", "over")), md.count("{!")),
        "회색 표지(「{…}」)": (len([n for n in root.find("span", "pill") if "over" not in n.classes()]), len(re.findall(r"\{(?!!)[^{}\n]+\}", md))),
        "메일 링크(「](mail:번호)」)": (len(r.mail_hrefs()), len(REF.findall(md))),
        "절(「## 」)": (len(root.find("section")), len(heads(md))),
        "작은 절(「### 」)": (len(root.find("div", "sub-head")), sum(line.startswith("### ") for line in lines)),
        "주의 상자(「> 」 덩이)": (len(root.find("div", "caution")), 1 if any(line.startswith(">") for line in lines) else 0),
    }
    why = [f"{k}: {got}개 — 글의 표시 {exp}개" for k, (got, exp) in want.items() if got != exp]
    for cls, what in (("lede", "제목 밑 한 줄"), ("summary", "요약 상자"), ("task", "카드"), ("facts", "카드 바닥의 칸"), ("clock-label", "시간줄의 이름")):
        if not root.find(None, cls):
            why.append(f"{what}(.{cls})이 안 섰다")
    if not root.find("code"):
        why.append("그대로 보일 글자(`…`)가 안 섰다")
    warned = [line for line in r.out.splitlines() if line.startswith("경고")]
    if warned:
        why.append(f"모델이 따라 쓰는 예가 경고를 받았다 — 스킬 글과 스크립트의 꼴이 갈렸다: {warned}")
    return not why, why


def links_only_from_numbers(skill: pathlib.Path) -> tuple[bool, list[str]]:
    """링크는 글의 mail: 표시마다 하나씩 `<메일함>/XML_Inbox/<번호>?OpenDocument` 로만 서고, 모델이 쓴 주소는 링크가 아니라 글자로 선다."""
    why: list[str] = []
    for name, md in (("절 셋", THREE), ("절 일곱", SEVEN), ("메일 속 주소", HOSTILE)):
        r = run(skill, md)
        if r.tree is None:
            why.append(f"{name}: 창이 없다 — {r.out.strip()[-200:]}")
            continue
        want = sorted(MAIL_HREF.format(mailbox=MAILBOX, unid=u.upper()) for u in REF.findall(md))
        got = sorted(r.mail_hrefs())
        if got != want:
            why.append(f"{name}: 링크 {got} — 글의 메일 번호에서 나야 할 링크 {want}")
        loose = [a.attrs for a in r.tree.root.find("a") if not a.attrs.get("href", "").startswith("#")
                 and not ({"noopener", "noreferrer"} <= set((a.attrs.get("rel") or "").split()))]
        if loose:
            why.append(f"{name}: rel 이 noopener · noreferrer 가 아닌 메일 링크 {loose[:2]}")
        stray = sorted({h.upper() for h in HEX32.findall(r.page)} - {h.upper() for h in HEX32.findall(md)})
        if stray:
            why.append(f"{name}: 글에 없는 메일 번호가 창에 섰다 {stray}")
    r = run(skill, HOSTILE)
    if r.tree is not None:
        attrs = [v for n in r.tree.root.walk() for v in n.attrs.values() if v]
        leaked = [v for v in attrs if "pay-check" in v or "javascript:" in v.lower()]
        if leaked:
            why.append(f"메일 속 주소: 모델이 쓴 주소가 속성에 섰다 {leaked}")
        if EVIL_URL not in r.body_text():
            why.append("메일 속 주소: 모델이 쓴 주소가 글자로 안 섰다")
    return not why, why


def text_stays_text(skill: pathlib.Path) -> tuple[bool, list[str]]:
    """메일에서 온 HTML · 따옴표 · 꺾쇠는 쓴 그대로 글자로 서고, 요소 · on… 속성으로 서지 않는다."""
    r = run(skill, HOSTILE)
    if r.tree is None:
        return False, [f"창이 없다 — {r.out.strip()[-200:]}"]
    why: list[str] = []
    body = r.body_text()
    title = "".join(n.text() for n in r.tree.root.find("title"))
    for w in HOSTILE_TEXT:
        if w not in body:
            why.append(f"글자로 서야 할 글이 없다: {w}")
    if "<img src=x onerror=alert(1)>" not in title:
        why.append(f"창의 이름에 제목이 글자로 안 섰다: {title!r}")
    bad_tags = sorted({n.tag for n in r.tree.root.walk() if n.tag in {"script", "img", "b"}})
    if bad_tags:
        why.append(f"메일 글이 요소로 섰다: {bad_tags}")
    handlers = sorted({k for n in r.tree.root.walk() for k in n.attrs if k.startswith("on")})
    if handlers:
        why.append(f"on… 속성이 섰다: {handlers}")
    return not why, why


def mailbox_shape(skill: pathlib.Path) -> tuple[bool, list[str]]:
    """꼴에 안 맞는 메일함 주소면 링크를 하나도 안 짓고 글과 메일 번호를 보이며 다음 걸음을 말한다. 꼴에 맞는 주소(끝의 / · 대문자 · 포트)는 링크가 된다."""
    why: list[str] = []
    numbers = [u.upper() for u in REF.findall(THREE)]
    for mb in BAD_MAILBOXES:
        r = run(skill, THREE, mb)
        if r.tree is None:
            why.append(f"{mb!r}: 창이 없다 — {r.out.strip()[-200:]}")
            continue
        if r.mail_hrefs():
            why.append(f"{mb!r}: 꼴이 아닌 주소로 링크를 지었다 {r.mail_hrefs()[:2]}")
        if any(n not in r.body_text() for n in numbers):
            why.append(f"{mb!r}: 링크 없이 보여야 할 메일 번호가 안 섰다")
        if "다음:" not in r.out:
            why.append(f"{mb!r}: 다음 걸음을 말하지 않았다 — {r.out.strip()[-160:]}")
    for mb, base in GOOD_MAILBOXES.items():
        r = run(skill, THREE, mb)
        want = sorted(MAIL_HREF.format(mailbox=base, unid=n) for n in numbers)
        if r.tree is None or sorted(r.mail_hrefs()) != want:
            why.append(f"{mb!r}: 꼴에 맞는 주소인데 링크 {r.mail_hrefs() if r.tree else '창 없음'} — 기대 {want}")
    return not why, why


def no_outside(skill: pathlib.Path) -> tuple[bool, list[str]]:
    """지은 창이 바깥 글꼴 · 스크립트 · 그림을 부르지 않고, 그 길을 닫는 CSP 를 든다."""
    r = run(skill, SEVEN)
    if r.tree is None:
        return False, [f"창이 없다 — {r.out.strip()[-200:]}"]
    why: list[str] = []
    tags = sorted({n.tag for n in r.tree.root.walk() if n.tag in OUTSIDE_TAGS})
    if tags:
        why.append(f"바깥을 부를 수 있는 요소: {tags}")
    srcs = sorted({k for n in r.tree.root.walk() for k in n.attrs if k in {"src", "srcset", "data", "poster", "action"}})
    if srcs:
        why.append(f"바깥을 부르는 속성: {srcs}")
    style = "".join(r.tree.styles) + "".join(n.attrs.get("style") or "" for n in r.tree.root.walk())
    hit = OUTSIDE_STYLE.findall(style)
    if hit:
        why.append(f"CSS 가 바깥을 부른다: {hit[:3]}")
    csp = [n.attrs.get("content", "") for n in r.tree.root.find("meta") if (n.attrs.get("http-equiv") or "").lower() == "content-security-policy"]
    if not csp or CSP_NONE not in csp[0] or "script-src" in csp[0]:
        why.append(f"바깥과 스크립트를 닫는 CSP(「{CSP_NONE}」 · script-src 없음)가 없다: {csp}")
    return not why, why


def text_kept(skill: pathlib.Path) -> tuple[bool, list[str]]:
    """창을 지으면 받은 글이 곁에 같은 이름의 .md 로 그대로(UTF-8 · LF) 남고 끝 줄이 댄다. 창을 못 지으면 아무것도 안 남는다."""
    why: list[str] = []
    for name, md, data in (("UTF-8 표준 입력", THREE, None),
                           ("cp949 · CRLF", LEGACY, LEGACY.replace("\n", "\r\n").encode("cp949"))):
        r = run(skill, md, data=data)
        stems = {pathlib.PurePath(n).stem for n in r.names}
        suffixes = sorted(pathlib.PurePath(n).suffix for n in r.names)
        if r.code != 0 or suffixes != [".html", ".md"] or len(stems) != 1:
            why.append(f"{name}: 종료 값 {r.code} · 남은 파일 {r.names} — 창 하나와 같은 이름의 보고 글 하나여야 한다")
            continue
        if r.kept != md:
            why.append(f"{name}: 남은 글이 받은 글과 다르다(앞 80자 {r.kept[:80]!r} — 받은 글 {md[:80]!r})")
        kept_name = next(n for n in r.names if n.endswith(".md"))
        if kept_name not in r.out:
            why.append(f"{name}: 끝 줄이 남긴 보고 글({kept_name})을 대지 않는다 — {r.out.strip()[-200:]}")
    r = run(skill, "오늘 보실 것은 없습니다\n- 제목 줄이 없는 글\n")
    if r.code == 0 or r.names:
        why.append(f"제목 없는 글: 종료 값 {r.code} · 남은 파일 {r.names} — 창을 못 지으면 1 로 나가고 아무것도 안 남아야 한다")
    return not why, why


def ends_named(skill: pathlib.Path) -> tuple[bool, list[str]]:
    """끝의 두 절을 갖춘 글은 경고 없이 서고, 두 절이 빠진 글은 창과 글이 남되 빠진 절마다 이름을 댄 경고와 그 이름을 든 다음 걸음을 받는다."""
    why: list[str] = []
    r = run(skill, THREE)
    warned = [line for line in r.out.splitlines() if line.startswith("경고")]
    if r.code != 0 or warned:
        why.append(f"두 절을 갖춘 글: 종료 값 {r.code} · 경고 {warned}")
    r = run(skill, THREE_BODY)
    if r.code != 0 or r.tree is None or r.kept is None:
        why.append(f"두 절이 빠진 글: 종료 값 {r.code} · 남은 파일 {r.names} — 경고만 하고 창과 글은 남아야 한다")
    lines = r.out.splitlines()
    for end in END_SECTIONS:
        if not any(line.startswith("경고") and end in line for line in lines):
            why.append(f"두 절이 빠진 글: 「{end}」 절을 대는 경고가 없다 — {r.out.strip()[-200:]}")
        if not any(line.startswith("다음:") and end in line for line in lines):
            why.append(f"두 절이 빠진 글: 「{end}」 절을 더하라는 다음 걸음이 없다")
    return not why, why


def opens_in_login_edge(skill: pathlib.Path) -> tuple[bool, list[str]]:
    """창은 로그인 Edge 의 디버깅 포트로 먼저 연다(`PUT /json/new?<file: 주소>`) — 포트가 닫혔거나 오류면 기본 브라우저로 간다.
    기본 브라우저는 환경변수 BROWSER 의 가짜 명령이 받는다 — 진짜 브라우저는 안 뜬다."""
    why: list[str] = []
    seen: list[tuple[str, str]] = []
    status = [200]

    class H(http.server.BaseHTTPRequestHandler):
        def _any(self) -> None:
            seen.append((self.command, self.path))
            self.send_response(status[0])
            self.end_headers()
            self.wfile.write(b"{}")
        do_PUT = do_GET = do_POST = _any

        def log_message(self, *a: object) -> None:
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with socket.socket() as s0:                      # 닫힌 포트 — 잡았다 놓은 번호
        s0.bind(("127.0.0.1", 0))
        closed = s0.getsockname()[1]
    work = pathlib.Path(tempfile.mkdtemp())
    stub = work / "browser_stub.py"
    got_file = work / "browser_got.txt"
    stub.write_text("import sys,pathlib\npathlib.Path(sys.argv[1]).write_text(sys.argv[2],encoding='utf-8')\n", encoding="utf-8")
    md = skill_example(skill) or "# 보고\n"

    def go(port: str, extra: list[str] | None = None) -> str:
        out_dir = work / f"o{len(list(work.iterdir()))}"
        out_dir.mkdir()
        env = dict(os.environ, EDGE_DEBUG_PORT=port, BROWSER=f'"{sys.executable}" "{stub}" "{got_file}" %s')
        cmd = [sys.executable, "-X", "utf8", "-I", str(skill / SCRIPT_REL), "--dir", str(out_dir), "--mailbox", MAILBOX, *(extra or [])]
        r = subprocess.run(cmd, input=md.encode("utf-8"), capture_output=True, timeout=TIMEOUT_S, env=env)
        return (r.stdout + r.stderr).decode("utf-8", errors="replace")

    try:
        ok_port = f"{srv.server_address[1]},9999"      # 쉼표로 여럿이면 첫 것
        out = go(ok_port)
        if len(seen) != 1 or seen[0][0] != "PUT":
            why.append(f"열린 포트에 PUT 한 번이어야 한다: {seen}")
        elif not seen[0][1].startswith("/json/new?file:///") or not seen[0][1].endswith(".html"):
            why.append(f"/json/new? 뒤에 지은 HTML 의 file: 주소가 와야 한다: {seen[0][1]}")
        if "로그인된 Edge" not in out or got_file.exists():
            why.append(f"로그인 Edge 에 열었으면 끝 줄이 그렇게 말하고 기본 브라우저는 안 부른다: {out.splitlines()[-1:]}")
        seen.clear()
        out = go(str(closed))
        if "기본 브라우저" not in out or not got_file.exists() or not got_file.read_text(encoding="utf-8").startswith("file:///"):
            why.append(f"포트가 닫히면 기본 브라우저가 file: 주소를 받고 끝 줄이 그렇게 말해야 한다: {out.splitlines()[-1:]}")
        got_file.unlink(missing_ok=True)
        status[0] = 500
        out = go(str(srv.server_address[1]))
        if "기본 브라우저" not in out or not got_file.exists():
            why.append("포트가 오류를 내면 기본 브라우저로 가야 한다")
        got_file.unlink(missing_ok=True)
        seen.clear()
        status[0] = 200
        out = go(str(srv.server_address[1]), ["--no-open"])
        if seen or got_file.exists() or "--no-open" not in out:
            why.append(f"--no-open 은 아무것도 안 띄운다: {seen} · {out.splitlines()[-1:]}")
    finally:
        srv.shutdown()
        srv.server_close()
        shutil.rmtree(work, ignore_errors=True)
    return not why, why


# 홀로 선다 — import 말고 코드를 싣는 길과, 메일함에 닿을 수 있는 모듈. 이 손이 짓는 주소는 부르면 메일을 읽음으로 바꾼다
LOADERS = ("spec_from_file_location", "SourceFileLoader", "runpy", "import_module", "__import__(")
NETWORK = {"urllib", "http", "socket", "ssl", "ftplib", "smtplib", "asyncio", "subprocess"}


def hands(scripts: pathlib.Path) -> list[pathlib.Path]:
    """스킬의 손 — `scripts/` 의 .py 가운데 검사(`check_*.py`)가 아닌 것. 검사는 금줄 낱말을 제 표로 들어 훑으면 늘 걸린다."""
    return sorted(f for f in scripts.glob("*.py") if not f.name.startswith("check_"))


def strangers(scripts: pathlib.Path) -> list[str]:
    """스크립트가 표준 라이브러리 · 같은 폴더 밖에서 싣는 것과 메일함에 닿을 수 있는 모듈."""
    own = {f.stem for f in hands(scripts)}
    out: list[str] = []
    for f in hands(scripts):
        text = f.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".")[0]]
            else:
                continue
            full = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module]
            out += [f"{f.name}:{node.lineno} import {n}" for n in names if n not in sys.stdlib_module_names and n not in own]
            # 열린 예외는 http.client 하나 — 로그인 Edge 의 디버깅 포트(127.0.0.1)로 창을 여는 길. 그 밖의 망 모듈은 막는다
            out += [f"{f.name}:{node.lineno} import {n} — 메일함에 닿을 수 있다"
                    for n, d in zip(names, full) if n in NETWORK and d != "http.client"]
        out += [f"{f.name}: {w}" for w in LOADERS if w in text]
        out += [f"{f.name}:{i} {line.strip()}" for i, line in enumerate(text.splitlines(), 1) if "sys.path.insert" in line or "sys.path.append" in line]
    return out


def check_contract(skill: pathlib.Path) -> None:
    got = strangers(skill / "scripts")
    report("홀로 선다 · 메일함에 안 닿는다 — 스크립트는 표준 라이브러리와 제 폴더의 것만 싣고, 망에 닿는 모듈을 싣지 않는다", not got, got)
    for name, judge in JUDGES:
        ok, why = judge(skill)
        report(name, ok, why)


JUDGES = [
    ("절 수가 달라도 선다 — 절 셋 · 일곱(줄 없는 절 하나)의 날이 같은 틀로 서고, 절마다 제 줄을 들고, 줄은 다 한 번씩 선다", sections_stand),
    ("생김새는 그 꼴의 줄에서 — 스킬 글의 예가 쓴 표시마다 시간줄 · 표지 · 카드 · 칸 · 주의 상자 · 링크가 선다", marks_render),
    ("링크는 메일 번호에서만 — 글의 mail: 표시마다 웹메일 여는 주소 하나, 글에 없는 메일은 안 서고, 모델이 쓴 주소는 글자로 선다", links_only_from_numbers),
    ("글은 글자로 — 메일에서 온 HTML · 따옴표 · 꺾쇠가 요소 · 속성이 아니라 쓴 그대로 선다", text_stays_text),
    ("메일함 주소의 꼴 — 꼴이 아니면 링크 없이 번호를 보이고 다음 걸음을 말한다 · 꼴이면 링크가 된다", mailbox_shape),
    ("바깥을 안 부른다 — 지은 창에 바깥 글꼴 · 스크립트 · 그림이 없고 CSP 가 그 길을 닫는다", no_outside),
    ("보고 글이 창 곁에 남는다 — 받은 글 그대로 같은 이름의 .md 로(cp949 · CRLF 로 와도 UTF-8 · LF 로), 끝 줄이 그 자리를 대고, 창을 못 지으면 아무것도 안 남는다",
     text_kept),
    ("끝의 두 절 — 「이 보고가 본 데」 · 「끝났다고 하신 것」을 갖춘 글은 경고 없이 서고, 빠진 글은 창과 글이 남되 빠진 절마다 경고와 다음 걸음을 받는다",
     ends_named),
    ("창은 로그인 Edge 로 — 디버깅 포트(127.0.0.1)에 새 탭을 PUT 하고, 포트가 닫혔거나 오류면 기본 브라우저로, --no-open 이면 아무것도 안 띄운다",
     opens_in_login_edge),
]


# ── 물림 — 일부러 틀린 사본에서 빨강이 나나 ─────────────────────────────────────────

def mutant(rel: pathlib.Path, old: str, new: str) -> pathlib.Path | None:
    """스킬 폴더(scripts · assets)를 임시 자리에 베끼고 한 파일의 한 줄을 바꾼다 — 바꿀 줄이 없으면 None(물림을 다시 지을 일)."""
    tmp = pathlib.Path(tempfile.mkdtemp()) / "daily-brief"
    for part in ("scripts", "assets"):
        shutil.copytree(SKILL / part, tmp / part, ignore=shutil.ignore_patterns("__pycache__", "check_*.py"))
    shutil.copy2(SKILL / "SKILL.md", tmp / "SKILL.md")
    target = tmp / rel
    text = target.read_text(encoding="utf-8")
    if old not in text:
        shutil.rmtree(tmp.parent, ignore_errors=True)
        return None
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    return tmp


# 판정 하나에 사본 하나 — (이름, 파일, 바꿀 줄, 바꾼 줄, 빨개져야 할 판정). 바꾼 줄은 그 판정이 지키는 자리를 끄거나 옛 꼴로 되돌린다
TEETH = [
    ("줄 없는 절을 빼는 손에서는 「절 수가 달라도 선다」가 빨갛다", SCRIPT_REL,
     "    for n, sec in enumerate(rep.sections[1:], 1):\n", "    for n, sec in enumerate([s for s in rep.sections[1:] if s.blocks], 1):\n",
     sections_stand),
    ("「@」 줄을 모르는 손에서는 「생김새는 그 꼴의 줄에서」가 빨갛다", SCRIPT_REL,
     'CLOCK = re.compile(r"^@\\s+(.*)$")', 'CLOCK = re.compile(r"^@@@\\s+(.*)$")', marks_render),
    ("번호의 꼴을 안 대는 손에서는 「링크는 메일 번호에서만」이 빨갛다(32자리가 아닌 mail: 표시가 링크가 된다)", SCRIPT_REL,
     "                if not UNID.match(ref):\n", "                if False:\n", links_only_from_numbers),
    ("이스케이프를 뺀 손에서는 「글은 글자로」가 빨갛다", SCRIPT_REL,
     "            out.append(html.escape(text[at:m.start()], quote=True))\n", "            out.append(text[at:m.start()])\n", text_stays_text),
    ("메일함 주소의 꼴을 안 대는 손에서는 「메일함 주소의 꼴」이 빨갛다", SCRIPT_REL,
     "    return url if MAILBOX.match(url) else None\n", "    return url or None\n", mailbox_shape),
    ("바깥 글꼴을 부르는 틀에서는 「바깥을 안 부른다」가 빨갛다", TEMPLATE_REL,
     "<title>$page_title</title>\n",
     '<title>$page_title</title>\n<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600" rel="stylesheet">\n', no_outside),
    ("CSP 를 뺀 틀에서는 「바깥을 안 부른다」가 빨갛다", TEMPLATE_REL,
     '<meta http-equiv="Content-Security-Policy"', '<meta name="x-no-csp"', no_outside),
    ("보고 글을 안 남기는 손에서는 「보고 글이 창 곁에 남는다」가 빨갛다", SCRIPT_REL,
     '        kept.write_text(text.replace("\\r\\n", "\\n")', '        kept.with_suffix(".txt").write_text(text.replace("\\r\\n", "\\n")', text_kept),
    ("줄끝을 맞추지 않는 손에서는 「보고 글이 창 곁에 남는다」가 빨갛다(CRLF 로 온 글이 CRLF 로 남는다)", SCRIPT_REL,
     'kept.write_text(text.replace("\\r\\n", "\\n").replace("\\r", "\\n"), ', "kept.write_text(text, ", text_kept),
    ("끝의 절을 안 보는 손에서는 「끝의 두 절」이 빨갛다", SCRIPT_REL,
     "    ends = missing_ends(rep)\n", "    ends = []\n", ends_named),
    ("새 탭을 PUT 대신 GET 으로 청하는 손에서는 「창은 로그인 Edge 로」가 빨갛다", SCRIPT_REL,
     'conn.request("PUT", ', 'conn.request("GET", ', opens_in_login_edge),
    ("실패해도 기본 브라우저로 안 가는 손에서는 「창은 로그인 Edge 로」가 빨갛다", SCRIPT_REL,
     "    if webbrowser.open(uri):\n", "    if False:\n", opens_in_login_edge),
    ("끝의 절 이름이 스킬 글과 갈린 손에서는 「생김새는 그 꼴의 줄에서」가 빨갛다(모델이 따라 쓰는 예가 경고를 받는다)", SCRIPT_REL,
     'END_SECTIONS = ("이 보고가 본 데", "끝났다고 하신 것")', 'END_SECTIONS = ("이 보고가 본 데", "끝난 일")', marks_render),
]


def check_teeth() -> None:
    body = mutant(SCRIPT_REL, "import sys\n", "import sys\nfrom secretary import judge\n")
    net = mutant(SCRIPT_REL, "import sys\n", "import sys\nimport urllib.request\n")
    report("물림 — 몸통을 싣거나 망에 닿는 모듈을 더한 사본에서는 「홀로 선다 · 메일함에 안 닿는다」가 빨갛다",
           body is not None and net is not None and bool(strangers(body / "scripts")) and bool(strangers(net / "scripts")),
           ["물림 표본을 못 심었다 — window.py 의 import 줄이 바뀌었으면 이 물림을 다시 짓는다"])
    for tmp in (body, net):
        if tmp is not None:
            shutil.rmtree(tmp.parent, ignore_errors=True)
    for name, rel, old, new, judge in TEETH:
        tmp = mutant(rel, old, new)
        report(f"물림 — {name}", tmp is not None and not judge(tmp)[0],
               [f"물림 표본을 못 심었다 — {rel} 의 「{old.strip()[:50]}」 줄이 바뀌었으면 이 물림을 다시 짓는다"])
        if tmp is not None:
            shutil.rmtree(tmp.parent, ignore_errors=True)


def main() -> int:
    if not (SKILL / SCRIPT_REL).is_file() or not (SKILL / TEMPLATE_REL).is_file():
        raise Unmeasured(f"[안 잼] 스크립트나 틀을 못 찾았다: {SKILL}")
    print(f"잰다: {SKILL}")
    for check in (check_contract, check_teeth):
        if check is check_teeth and not WITH_TEETH:
            continue
        if check is check_teeth and FAILS:
            edge("계약 판정이 빨개 물림을 안 돌렸다 — 늘 지는 판 앞의 물림은 뜻이 없다(머리말 「물림」)")
            continue
        try:
            check(SKILL) if check is check_contract else check()
        except Unmeasured:
            raise
        except Exception:   # noqa: BLE001 — 판정 하나가 넘어져도 나머지를 잰다
            report(f"판정이 넘어지지 않고 끝난다 ({check.__name__})", False, traceback.format_exc().splitlines()[-8:])
    edge("창이 고른 디자인 그대로 보이나 · 링크를 눌러 회사 웹메일에서 그 메일이 한 번에 열리나는 여기서 못 잰다(머리말)")
    print("\n잰 것 — 홀로 선다 · 절 수 · 생김새 · 메일 링크 · 글자 · 메일함 주소 · 바깥 · 보고 글 · 끝의 두 절 · 로그인 Edge"
          + (f" · 물림 {1 + len(TEETH)}" if WITH_TEETH else " (물림은 --teeth)") + (f" — 어긋남 {len(FAILS)}건" if FAILS else ""))
    # 건수는 손으로 적지 않는다 — 이번 판에서 실제로 선 판정을 센다
    print(f"통과 {len(PASSES)}/{len(PASSES) + len(FAILS)}")
    return EXIT_MISMATCH if FAILS else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
