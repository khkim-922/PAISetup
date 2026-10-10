"""DRM 길잡이 — 사람이 붙이거나 적은 오피스 · PDF 가 Fasoo DRM 에 감겼으면 스킬 `drm-office-read` 로 가는 길을 곁에
붙인다 (UserPromptSubmit · PreToolUse · PostToolUseFailure 훅). 붙이기만 한다 — 막지 않는다.

**왜 있나.** 감긴 파일은 Read 와 파서가 형식 인식 단계에서 진다. 그 자리를 여는 스킬은 description 으로만 걸리는데,
첨부의 실패는 모델의 판단 밖에서 난다 — 모델은 그 파일을 열어 보기 전에는 감긴 줄 모른다. 판단과 무관하게 걸려야 하는
자리라 훅의 층이다(claude-config #120 · 결정 0094).

보는 자리는 셋이다:

  · UserPromptSubmit 의 `prompt` — 글에 든 경로. 꼴은 넷이다
      @"…"             데스크톱 앱 Code 탭의 「+」 · 끌어다 놓기가 넣는 꼴(따옴표째 · 절대 경로)
      @경로            손으로 친 언급(공백 없는 한 낱말 · 상대면 입력의 `cwd` 기준)
      "C:\\…" · 'C:\\…'  탐색기 「경로로 복사」가 주는 꼴
      C:\\… · C:/…       붙여 넣은 맨 절대 경로 — 공백이 들 수 있어 스킬이 다루는 확장자에서 끝을 끊는다
  · UserPromptSubmit · **PreToolUse** 때 `transcript_path` 의 **이 턴 사용자 줄** — 앱의 「+」는 PDF 를 경로 없이
    본문으로 싣는다: 그 줄에 `{"type":"document","source":{"type":"base64","media_type":"application/pdf","data":…},
    "title":"<원래 이름>"}` 이 들고, 훅 입력에는 첨부 칸도 이름도 없다(#120 실측).
    ⚠ **자리가 둘인 것은 그 줄이 디스크에 닿는 시각이 표면마다 다르기 때문이다.** 데스크톱 앱은 제출 훅보다
      먼저 쓰지만 VS Code 앱은 **훅이 1.4 초 이르고**, 그 줄은 뒤따르는 메타 줄과 함께 **덩어리로** 닿는다
      (#120 실측 — 382→388 줄 · 42 KB 가 한 번에). 그래서 제출 때 못 찾은 턴을 **첫 도구 호출 때** 다시 본다:
      그 시점엔 반드시 써져 있다(착지보다 2.9 초 뒤). 한 턴에 한 번만 알린다(아래 「이 턴의 사용자 줄」).
    오피스는 앱이 첨부를 형식으로 거절해 이 길에 안 온다 — 글에 경로를 적는 길(위)이 든다
  · PostToolUseFailure(Read) — `tool_input.file_path`. 이 그물에 닿는 것은 PDF 다: Read 는 감긴 PDF 를 실행 단계에서
    지고(「missing %PDF- header」) 이 이벤트를 낸다. 오피스는 입력 검증에서 져(「cannot read binary files」) 어느 훅도
    안 걸린다 — 그 자리는 Read 의 거절 문구가 이미 「스킬을 쓰라」로 민다

**감겼나는 머리 16 바이트에 `DRMONE` 이 드나로 가른다** — Fasoo 가 감싼 파일의 표지다(`_check/drm-fixtures/README.md`).
평문 시그니처가 아닌 것을 「감겼다」로 치는 길(`read-drm.ps1` 의 `Test-PlainFormat`)은 안 쓴다 — 시그니처가 없는
평문 `.csv` 까지 감긴 것으로 읽는다. 첨부 본문은 base64 의 앞 24 글자(16 바이트)만 풀어 재고, 감겼을 때만 다 푼다.

**이 턴의 사용자 줄 — `prompt_id` 로 지목한다.** 입력의 `prompt_id` 는 기록 줄의 `promptId` 와 **같은 값이다**
(#120 실측 — 아홉 턴 전부 맞았다). 그 값이 달린 `user` 줄 가운데 문서 블록이 든 것을 든다. 꼬리를 거슬러 「지금이
어느 턴인가」를 추정하지 않는다 — 그 길은 **언제 보느냐**에 매여 양쪽에서 조인다: 제출 시점에는 그 줄이 아직
디스크에 없고(VS Code 앱에서 훅이 1.4 초 이르다), 42 초쯤 뒤면 꼬리 창에서 밀려난다. 지목은 **몇 줄째인지와
무관**해서 두 실패가 함께 사라진다.
⚠ **같은 `prompt_id` 가 잇단 두 턴에 오는 것이 보였다**(#120). 그래서 값만으로 턴을 가르지 않고 **그 줄에 문서
  블록이 드나를 다시 재므로** 오인이 안 난다 — 문서 블록이 든 줄의 `promptId` 는 그 턴에만 쓰였다.
⚠ **한 턴에 한 번만 알린다.** 거는 자리가 둘(제출 · 도구 호출)이라 같은 첨부가 두 번 걸릴 수 있다 — 알린
  `prompt_id` 를 떨궈 두고(`notified_dir`) 이미 있으면 조용히 끝낸다.
기록은 수 MB 이고 PDF 한 줄이 MB 단위라 **끝에서부터 찾는 줄까지만 읽는다**(`TAIL_MAX_BYTES` 가 울타리).

**떨구는 자리와 수명** — `read-drm.ps1` 은 디스크의 파일만 받으므로 감긴 첨부는 같은 바이트를
`<세션 스크래치패드 · 없으면 시스템 임시 폴더>/drm-attach/<session_id>/<원래 이름>` 에 쓴다. 같은 이름은 덮는다 — 한 세션에서
같은 첨부를 다시 붙이면 같은 자리라 사본이 안 쌓인다. 한 턴에 같은 이름이 둘이면 뒤엣것에 ` (2)` 를 붙인다. 지우는 손은 안
둔다 — 쓰는 것은 **풀린 글자가 아니라 감긴 바이트 그대로**라 원본이 이미 사람의 디스크에 있는 것보다 더 드러나는 것이 없고,
자리가 임시 폴더 밑(스크래치패드도 그 안이다)이라 임시 폴더를 비우는 손이 거둔다. 세션 칸을 두는 것은 스크래치패드가 없는
표면(VS Code 앱)에서 두 세션이 같은 이름을 서로 덮지 않게 하려는 것이다.

⚠ **다루는 확장자는 스킬의 표가 든다** — `read-drm.ps1` 의 `$HANDLER`(확장자 → 앱)를 그 자리에서 읽는다. 여기 따로 적으면
   스킬이 확장자를 늘린 날 길잡이만 낡는다. 껍데기의 글롭만은 파이썬을 띄우기 전이라 표를 못 읽어 한 벌을 든다 — 검사가
   표의 확장자마다 껍데기를 지나 걸리나를 잰다.
⚠ **스킬을 못 찾으면 그 사실을 말한다** — 감긴 파일이 있는데 읽을 길이 이 PC 에 없다는 것도 모델이 알아야 할 사실이다.
   그때는 표가 없어 확장자로 거르지 않고(감긴 표지가 거른다), 읽을 손이 없으니 첨부도 안 떨군다.
⚠ **파일 내용은 안 싣는다** — 덧말에는 이름과 자리만 든다. 읽기는 스킬의 스크립트가 하고, 이 훅은 길을 가리킨다(#120).
⚠ **덧말은 사실로 쓴다** — 명령조의 바깥 글은 프롬프트 주입 방어에 걸릴 수 있다(웹 다시 찾기와 같은 까닭).
⚠ **명령의 경로는 슬래시로 적는다** — 모델이 Bash 로 칠 때 겹따옴표 안의 역슬래시는 셸이 접고, 겹역슬래시는 홈 훅
   (`bash-backslash-deny.sh`)이 돌려보낸다. PowerShell 은 슬래시 경로를 그대로 받는다.
⚠ **재다 져도 막지 않는다** — 뜻밖의 예외는 그 이름만 대는 한 줄로 바꾸고 0 으로 끝낸다. 길잡이가 죽은 사실은 남기되
   사람이 보낸 글은 그대로 간다.

부르는 자리 — 홈 `~/.claude/settings.json` 의 UserPromptSubmit · PreToolUse · PostToolUseFailure. 앞에 셸
껍데기(`drm-guide.sh` · 곁 파일)가 서서, 입력에 오피스 · PDF 확장자가 있거나 기록에 이 턴의 문서 블록이 있을 때만
이 몸통을 띄운다. 심는 손과 주인 규율은 그림 문과 같다(`image-gate.py` 머리말).

시험 — `python -X utf8 scripts/check-drm-guide.py`.
"""
import base64
import binascii
import hashlib
import json
import os
import re
import sys
import tempfile

NAME = 'DRM 길잡이'
SKILL = 'drm-office-read'
READER = os.path.join('scripts', 'read-drm.ps1')   # 확장자 표(`$HANDLER`)와 글자를 뽑는 손
FASOO_MARK = b'DRMONE'    # Fasoo 가 감싼 파일의 머리 표지
HEAD_BYTES = 16           # 표지를 찾는 머리 길이 — 표본은 셋째 바이트에서 시작한다
B64_HEAD = 24             # 머리 16 바이트를 푸는 데 드는 base64 글자 수 — 4 · ⌈16 / 3⌉
OUT_SUBDIR = 'drm-text'   # 뽑은 글자를 둘 폴더 이름 — 세션 스크래치패드(없으면 임시 폴더) 밑
ATTACH_SUBDIR = 'drm-attach'   # 감긴 첨부를 떨굴 폴더 이름 — 같은 밑, 세션마다 한 칸(머리말 「떨구는 자리와 수명」)
NOTIFIED_SUBDIR = '.notified'   # 알린 턴의 표식을 둘 폴더 — 떨구는 세션 칸 밑(`claim_turn` 머리말 ⚠)
DOC_MARK = b'"type":"document"'    # 문서 블록 표지 — 푸는 값을 내기 전에 글자로 먼저 거른다
ATTACH_MEDIA = {'application/pdf': '.pdf'}   # 첨부 문서 블록의 형식 → 확장자. 앱이 본문으로 싣는 문서는 PDF 다(#120)
# 기록 꼬리를 거꾸로 읽는 한도 — 사용자 줄 하나는 API 요청 한도(32 MB)를 못 넘으니 그 두 배면 한 줄을 다 담는다
TAIL_MAX_BYTES = 64 << 20
TAIL_CHUNK = 1 << 20      # 거꾸로 읽는 한 번의 크기
SKILL_DIR_ENV = 'DRM_GUIDE_SKILL_DIR'   # 시험이 스킬 자리를 줄 때 — 빈 값이면 「스킬 없음」

ATTACH = re.compile(r'@"([^"\r\n]+)"')                                     # 「+」 · 끌어다 놓기
MENTION = re.compile(r'(?:^|(?<=[\s(\[{,]))@([^\s"\'<>|]+)')               # 손으로 친 @경로
QUOTED = re.compile(r'["\']((?:[A-Za-z]:[\\/]|\\\\)[^"\'\r\n]*)["\']')    # 「경로로 복사」
# 맨 절대 경로 — 앞에 낱말 · 따옴표 · 경로 글자가 붙지 않은 드라이브(또는 UNC)에서 시작한다. 몸통은 다른 드라이브
#   시작을 건너지 않는다 — 안 그러면 「C:\a.txt 와 C:\b.pdf」가 한 경로로 묶인다.
BARE_START = r'(?<![A-Za-z0-9_"\'@/\\:])((?:[A-Za-z]:[\\/]|\\\\)'
BARE_BODY = r'(?:(?![A-Za-z]:[\\/])[^"\'\r\n<>|*?])'
BARE_NOEXT = re.compile(BARE_START + r'(?:(?![A-Za-z]:[\\/])[^\s"\'<>|*?])+)')
TRAIL = '.,;:!?)]}'       # 표가 없을 때 후보 끝에서 걷는 문장 부호
UNSAFE_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')   # 윈도우 파일 이름에 못 쓰는 글자


# ── 스킬 — 자리와 확장자 표 ──────────────────────────────────────────────────────
def skill_dir():
    """스킬 폴더 — 이 파일 곁(설정 저장소의 진본) · Claude 홈 · Codex 홈(`~/.agents/skills`) · agy 홈
    (`~/.gemini/config/paisetup-skills`). `SKILL.md` 와 `read-drm.ps1` 이 다 있어야 선다. 도구마다 제 홈을 들어, Claude 를
    안 고른 PC 에는 뒤의 둘만 있다(결정 0097 · 0099)."""
    forced = os.environ.get(SKILL_DIR_ENV)
    if forced is not None:   # 시험이 자리를 주면 그 자리만 — 「없을 때」를 재려면 대체가 없어야 한다
        cands = [forced]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        home = os.path.expanduser('~')
        cands = [os.path.normpath(os.path.join(here, '..', 'skills', SKILL)),
                 os.path.join(home, '.claude', 'skills', SKILL),
                 os.path.join(home, '.agents', 'skills', SKILL),
                 os.path.join(home, '.gemini', 'config', 'paisetup-skills', SKILL)]
    for d in cands:
        if d and os.path.isfile(os.path.join(d, 'SKILL.md')) and os.path.isfile(os.path.join(d, READER)):
            return d
    return None


def handled_exts(sdir):
    """`read-drm.ps1` 의 `$HANDLER` 열쇠 — 소문자 확장자 집합. 못 읽으면 빈 집합."""
    try:
        with open(os.path.join(sdir, READER), encoding='utf-8-sig') as f:
            src = f.read()
    except OSError:
        return set()
    m = re.search(r'^\$HANDLER\s*=\s*@\{(.*?)^\}', src, re.M | re.S)
    return {e.lower() for e in re.findall(r"'(\.\w+)'\s*=", m.group(1))} if m else set()


# ── 경로 — 뽑고 다듬고 푼다 ─────────────────────────────────────────────────────
def ext_alt(exts):
    """확장자 표 → 정규식 갈래. 긴 것부터 — `.docx` 가 `.doc` 에 먼저 먹히지 않게."""
    return '|'.join(re.escape(e[1:]) for e in sorted(exts, key=len, reverse=True))


def candidates(text, alt):
    """글에서 경로 후보를 뽑는다 — 꼴마다 따로 훑고, 겹친 것은 부르는 쪽이 하나로 접는다."""
    found = ATTACH.findall(text) + MENTION.findall(text) + QUOTED.findall(text)
    if alt:
        bare = re.compile(BARE_START + BARE_BODY + r'*?\.(?:%s))(?![A-Za-z0-9_])' % alt, re.I)
        found += bare.findall(text)
    else:
        found += BARE_NOEXT.findall(text)
    return found


def trim(tok, ext_re):
    """후보 끝의 군더더기를 걷는다 — 붙은 조사 · 문장 부호. 표가 있으면 그 확장자에서 끊고, 없으면 버린다."""
    tok = tok.strip()
    if ext_re is None:
        return tok.rstrip(TRAIL) or None
    m = ext_re.match(tok)
    return m.group(1) if m else None


def resolve(tok, cwd):
    """후보 → 절대 경로. 상대면 입력의 `cwd` 기준이다 — `@경로` 언급이 그 자리에서 풀린다."""
    p = os.path.expanduser(tok)
    if not os.path.isabs(p) and not re.match(r'^[A-Za-z]:[\\/]', p):
        p = os.path.join(cwd or os.getcwd(), p)
    return os.path.normpath(p)


def wrapped(path):
    """머리에 Fasoo 표지가 드나 — 머리만 읽는다."""
    try:
        with open(path, 'rb') as f:
            return FASOO_MARK in f.read(HEAD_BYTES)
    except OSError:
        return False


def ext_pattern(exts):
    """확장자 표 → (정규식 갈래, 후보를 그 확장자에서 끊는 식). 표가 비면 둘 다 빈 값."""
    alt = ext_alt(exts) if exts else ''
    return alt, (re.compile(r'(.*?\.(?:%s))(?![A-Za-z0-9_])' % alt, re.I) if alt else None)


def wrapped_paths(toks, ext_re, cwd):
    """후보 → 감긴 파일의 절대 경로. 다듬고 풀고, 겹친 것은 하나로 접는다. agy 어댑터(`agy-hooks.py`)도 부른다."""
    seen, hits = set(), []
    for t in toks:
        t = trim(t, ext_re)
        if not t:
            continue
        p = resolve(t, cwd)
        k = os.path.normcase(p)
        if k in seen:
            continue
        seen.add(k)
        if os.path.isfile(p) and wrapped(p):
            hits.append(p)
    return hits


# ── 첨부 — 기록의 이 턴 사용자 줄 ─────────────────────────────────────────────────
def tail_lines(path):
    """기록을 끝에서부터 한 줄씩 낸다 — 앞은 안 읽는다. 읽은 양이 `TAIL_MAX_BYTES` 를 넘으면 멈춘다."""
    with open(path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        buf, taken = b'', 0
        while True:
            i = buf.rfind(b'\n')
            while i >= 0:   # 줄바꿈 뒤는 끝이 알려진 온전한 줄이다
                line, buf = buf[i + 1:], buf[:i]
                if line.strip():
                    yield line
                i = buf.rfind(b'\n')
            if pos == 0:
                if buf.strip():
                    yield buf
                return
            if taken >= TAIL_MAX_BYTES:
                return
            n = min(TAIL_CHUNK, pos)
            pos -= n
            f.seek(pos)
            buf = f.read(n) + buf
            taken += n


def turn_documents(path, pid):
    """`prompt_id` 로 지목한 이 턴 사용자 줄의 문서 블록 — `(블록들, 줄 식별자)`. 못 찾으면 `([], '')`.

    끝에서 거꾸로 읽어 **그 `promptId` 가 달린 가장 새 `user` 줄**을 찾고, 그 줄에 문서 블록이 있을 때만 든다.
    「지금이 어느 턴인가」를 추정하지 않으므로 그 줄이 몇 줄째인지 · 뒤에 무엇이 붙었는지와 무관하다.

    ⚠ **「가장 새」가 판정의 핵이다.** 문서 블록이 든 줄만 골라 거슬러 오르면, 같은 `prompt_id` 가 잇달아
      올 때(#120 실측) **앞 턴의 첨부를 뒤 턴에 알린다** — 뒤 턴이 첨부 없는 평문이어도 그렇다. 없는 첨부를
      가리키는 안내는 모델을 틀린 길로 밀어 침묵보다 나쁘다. 그래서 그 값의 가장 새 사용자 줄 하나만 보고,
      거기 문서가 없으면 조용히 끝낸다.
    ⚠ **줄 식별자를 함께 낸다** — `prompt_id` 는 턴을 못 가르므로(같은 값이 잇달아 온다) 한 번만 알리는
      표식의 열쇠는 이 값이 든다(`claim_turn`). 기록 줄의 `uuid` 가 그 자리다.
    """
    if not path or not pid or not os.path.isfile(path):
        return [], ''
    needle = ('"promptId":"%s"' % pid).encode('utf-8')
    try:
        for raw in tail_lines(path):
            if needle not in raw:
                continue    # 다른 턴의 줄 — 푸는 값을 안 낸다
            try:
                o = json.loads(raw)
            except ValueError:
                continue    # 쓰이다 만 줄
            if not isinstance(o, dict) or o.get('type') != 'user' or o.get('isMeta'):
                continue
            content = (o.get('message') or {}).get('content')
            if not isinstance(content, list):
                return [], ''   # 이 턴의 가장 새 사용자 줄인데 블록이 없다(평문 글)
            if any(b.get('type') == 'tool_result' for b in content if isinstance(b, dict)):
                continue        # 도구 결과 줄 — 사람이 보낸 줄이 아니다
            uid = str(o.get('uuid') or '')
            blocks = [b for b in content if isinstance(b, dict) and b.get('type') == 'document']
            return blocks, uid   # 문서가 없으면 빈 목록 — 거슬러 더 오르지 않는다
    except OSError:
        return [], ''
    return [], ''


def wrapped_attachments(path, pid):
    """이 턴의 감긴 첨부 — `([(이름, 확장자, base64)], 줄 식별자)`. 머리 글자만 풀어 잰다."""
    out = []
    blocks, uid = turn_documents(path, pid)
    for b in blocks:
        src = b.get('source') if isinstance(b.get('source'), dict) else {}
        ext = ATTACH_MEDIA.get(src.get('media_type'))
        data = src.get('data')
        if src.get('type') != 'base64' or not ext or not isinstance(data, str):
            continue
        try:
            head = base64.b64decode(data[:B64_HEAD])
        except (binascii.Error, ValueError):
            continue
        if FASOO_MARK in head[:HEAD_BYTES]:
            out.append((str(b.get('title') or ''), ext, data))
    return out, uid


def safe_name(title, ext):
    """첨부 이름 → 쓸 파일 이름. 경로 조각과 못 쓰는 글자를 걷고, 확장자가 없으면 붙인다."""
    n = UNSAFE_NAME.sub('_', os.path.basename(title.replace('\\', '/'))).strip().rstrip('. ')
    n = n or 'attachment'
    return n if n.lower().endswith(ext) else n + ext


def attach_dir(data):
    base = str(data.get('scratchpad_dir') or tempfile.gettempdir())
    sid = re.sub(r'[^A-Za-z0-9_-]', '', str(data.get('session_id') or '')) or 'session'
    return os.path.join(base, ATTACH_SUBDIR, sid)


def claim_turn(data, key):
    """이 턴을 **처음** 알리는 자리인가 — 먼저 왔으면 참, 이미 알렸으면 거짓.

    거는 자리가 둘이라(제출 · 도구 호출) 같은 첨부가 두 번 걸릴 수 있다. 표식 파일을 **배타 생성**으로
    만들어 먼저 온 쪽만 참을 받는다 — 읽고 나서 쓰는 꼴은 두 훅이 겹칠 때 둘 다 통과한다.

    ⚠ **열쇠는 기록 줄의 식별자(`uuid`)다 — `prompt_id` 가 아니다.** 같은 `prompt_id` 가 잇단 두 턴에 오는
      것이 보였고(#120), 그 값으로 표식을 두면 앞 턴의 표식이 뒤 턴의 다른 첨부를 막는다. 줄 식별자는 줄마다
      달라 그 일이 안 난다. 식별자가 없는 줄이면(옛 기록 꼴) 막지 않는다 — 안 알리는 것보다 두 번이 낫다.
    ⚠ **표식은 떨구기가 **선 뒤에** 둔다**(부르는 쪽 차례) — 먼저 두면 떨구다 진 턴이 영구히 막힌다.
      그 사이에 두 훅이 겹치면 둘 다 떨구고 하나만 알린다: 떨구기는 같은 바이트를 같은 자리에 쓰므로
      덮어도 해가 없고, 알림이 둘인 것보다 안 알리는 것이 비싸다.
    ⚠ **표식은 떨구는 세션 칸 밑에 둔다** — 임시 폴더를 비우는 손이 첨부 사본과 함께 거둔다. 세션 칸을 안
      두면 앞 세션의 표식이 다음 세션을 막는다.
    """
    if not key:
        return True
    folder = os.path.join(attach_dir(data), NOTIFIED_SUBDIR)
    name = hashlib.sha256(key.encode('utf-8')).hexdigest()[:32]
    try:
        os.makedirs(folder, exist_ok=True)
        fd = os.open(os.path.join(folder, name), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    except OSError:
        return True   # 표식을 못 두면 막지 않는다 — 안 알리는 것보다 두 번이 낫다
    os.close(fd)
    return True


def drop(items, folder):
    """감긴 첨부를 같은 바이트로 쓴다 — [(이름, 쓴 자리)]. 반쯤 쓴 파일이 그 이름으로 안 서게 옆에 쓰고 바꿔 단다."""
    os.makedirs(folder, exist_ok=True)
    used, out = set(), []
    for title, ext, data in items:
        name = safe_name(title, ext)
        stem, e = os.path.splitext(name)
        k = 2
        while name.lower() in used:
            name = '%s (%d)%s' % (stem, k, e)
            k += 1
        used.add(name.lower())
        path = os.path.join(folder, name)
        part = path + '.part'
        with open(part, 'wb') as f:
            f.write(base64.b64decode(data))
        os.replace(part, path)
        out.append((title or name, path))
    return out


# ── 덧말 ─────────────────────────────────────────────────────────────────────────
def slash(p):
    return p.replace('\\', '/')


def ps_quote(s):
    """PowerShell 홑따옴표 글자 — 안의 홑따옴표는 겹친다."""
    return "'" + s.replace("'", "''") + "'"


def message(event, paths, attached, sdir, out_dir):
    """paths — 글이 가리킨 감긴 파일 · attached — (첨부 이름, 쓴 자리 또는 None)."""
    parts = []
    if paths:
        names = ' · '.join(os.path.basename(p) for p in paths)
        if event == 'PostToolUseFailure':
            parts.append('Read 가 진 %s 는 Fasoo DRM 에 감긴 파일이다' % names)
        elif event == 'PreToolUse':    # agy 어댑터 — 열기 전에 막는 자리(`agy-hooks.py`)
            parts.append('열려던 %s 는 Fasoo DRM 에 감긴 파일이다' % names)
        else:
            parts.append('이 글이 가리키는 파일 가운데 Fasoo DRM 에 감긴 것: %s' % names)
    if attached:
        parts.append('이 턴의 첨부 가운데 Fasoo DRM 에 감긴 것: %s' % ' · '.join(t for t, _ in attached))
    head = '%s — %s (머리에 DRMONE). 감긴 파일은 Read 와 파서가 형식 인식 단계에서 진다.' % (NAME, ' · '.join(parts))
    if not sdir:
        return head + (' 글자를 뽑는 스킬 %s 가 이 PC 에 없다(~/.claude/skills · ~/.agents/skills · ~/.gemini/config/paisetup-skills 에 없음) — 이 자리에서는 읽을 길이 없다.'
                       % SKILL)
    written = [p for _, p in attached if p]
    if written:
        head += (' 첨부는 경로 없이 본문으로 와서, 같은 바이트(감긴 그대로)를 디스크에 떨궜다: %s.'
                 % ' · '.join('%s → %s' % (t, slash(p)) for t, p in attached if p))
    cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "& %s -Path %s -OutDir %s"' % (
        ps_quote(slash(os.path.join(sdir, READER))),
        ','.join(ps_quote(slash(p)) for p in list(paths) + written),
        ps_quote(slash(out_dir)))
    return head + (' 글자는 스킬 %s 가 오피스를 태워 뽑는다 — Fasoo 에이전트가 도는 PC(회사 PC)에서만 풀린다'
                   '(%s — 차례와 주의는 그 2 · 3절). 이 파일들이면: %s'
                   ' — 뽑은 글자는 -OutDir 에 「<파일 이름>.txt」로 남는다.'
                   % (SKILL, slash(os.path.join(sdir, 'SKILL.md')), cmd))


def emit(event, context):
    sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': event, 'additionalContext': context}},
                                ensure_ascii=False))
    return 0


# ── 판정 ─────────────────────────────────────────────────────────────────────────
def guide(data):
    event = data.get('hook_event_name') or ''
    # 첨부를 보는 자리는 둘이다 — 제출(줄이 써졌으면 여기서 잡힌다)과 도구 호출(그때는 반드시 써져 있다).
    # 글이 가리킨 경로는 제출 때만 본다 — 도구 호출 때 다시 읽으면 같은 글을 매 호출 되읽는다.
    if event == 'UserPromptSubmit':
        toks = None
        text = str(data.get('prompt') or '')
    elif event == 'PreToolUse':
        toks, text = [], ''          # 첨부만 본다
    elif event == 'PostToolUseFailure' and data.get('tool_name') == 'Read':
        toks = [str((data.get('tool_input') or {}).get('file_path') or '')]
        text = ''
    else:
        return 0
    sdir = skill_dir()
    exts = handled_exts(sdir) if sdir else set()
    alt, ext_re = ext_pattern(exts)
    if toks is None:
        toks = candidates(text, alt)
    hits = wrapped_paths(toks, ext_re, str(data.get('cwd') or ''))
    attached = []
    if event in ('UserPromptSubmit', 'PreToolUse'):
        pid = str(data.get('prompt_id') or '')
        found, uid = wrapped_attachments(str(data.get('transcript_path') or ''), pid)
        found = [a for a in found if not exts or a[1] in exts]
        if found and sdir:
            # ⚠ **떨구고 나서 표식을 둔다** — 먼저 두면 떨구다 진 턴이 영구히 막힌다(`claim_turn` 머리말 ⚠).
            #   떨구기가 지면 예외가 올라가 바깥의 「재다 졌다」 한 줄이 나가고, 표식이 없으니 다음 자리가 다시 잰다.
            dropped = drop(found, attach_dir(data))
            attached = dropped if claim_turn(data, uid) else []
        elif found:
            # 읽을 손이 없으면 아무것도 디스크에 안 남긴다(머리말 ⚠) — 표식도 안 둔다
            attached = [(t or 'attachment' + e, None) for t, e, _ in found]
    if not hits and not attached:
        return 0
    out_dir = os.path.join(str(data.get('scratchpad_dir') or tempfile.gettempdir()), OUT_SUBDIR)
    return emit(event, message(event, hits, attached, sdir, out_dir))


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    try:
        return guide(data)
    except Exception as e:  # noqa: BLE001 — 길잡이가 진 것은 알리되 사람이 보낸 글은 그대로 간다
        event = data.get('hook_event_name')
        if event in ('UserPromptSubmit', 'PreToolUse', 'PostToolUseFailure'):
            return emit(event, '%s — 경로와 첨부를 재다 졌다(%s). 감긴 파일(머리에 DRMONE)은 Read 와 파서로 안 열리고, '
                               '스킬 %s 가 Fasoo 에이전트가 도는 PC 의 오피스로 글자를 뽑는다.'
                               % (NAME, type(e).__name__, SKILL))
        return 0


if __name__ == '__main__':
    sys.exit(main())
