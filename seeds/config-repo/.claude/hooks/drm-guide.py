"""DRM 길잡이 — 사람이 붙이거나 적은 오피스 · PDF 가 Fasoo DRM 에 감겼으면 스킬 `drm-office-read` 로 가는 길을 곁에
붙인다 (UserPromptSubmit · PostToolUseFailure 훅). 붙이기만 한다 — 막지 않는다.

**왜 있나.** 감긴 파일은 Read 와 파서가 형식 인식 단계에서 진다. 그 자리를 여는 스킬은 description 으로만 걸리는데,
첨부의 실패는 모델의 판단 밖에서 난다 — 데스크톱 앱의 「+」 · 끌어다 놓기는 파일 내용을 안 싣고 경로 글자만 `prompt` 에
넣고(`@"C:\\…\\보고서.xlsx"`), 모델은 그 파일을 열어 보기 전에는 감긴 줄 모른다. 판단과 무관하게 걸려야 하는 자리라
훅의 층이다(claude-config #120 · 결정 0094).

두 이벤트를 든다:

  · UserPromptSubmit — `prompt` 에서 경로를 뽑는다. 꼴은 넷이다
      @"…"             「+」 · 끌어다 놓기가 넣는 꼴(따옴표째 · 절대 경로)
      @경로            손으로 친 언급(공백 없는 한 낱말 · 상대면 입력의 `cwd` 기준)
      "C:\\…" · 'C:\\…'  탐색기 「경로로 복사」가 주는 꼴
      C:\\… · C:/…       붙여 넣은 맨 절대 경로 — 공백이 들 수 있어 스킬이 다루는 확장자에서 끝을 끊는다
  · PostToolUseFailure(Read) — `tool_input.file_path`. 이 그물에 닿는 것은 PDF 다: Read 는 감긴 PDF 를 실행 단계에서
    지고(「missing %PDF- header」) 이 이벤트를 낸다. 오피스는 입력 검증에서 져(「cannot read binary files」) 어느 훅도
    안 걸린다 — 그 자리는 Read 의 거절 문구가 이미 「스킬을 쓰라」로 민다

**감겼나는 머리 16 바이트에 `DRMONE` 이 드나로 가른다** — Fasoo 가 감싼 파일의 표지다(`_check/drm-fixtures/README.md`).
평문 시그니처가 아닌 것을 「감겼다」로 치는 길(`read-drm.ps1` 의 `Test-PlainFormat`)은 안 쓴다 — 시그니처가 없는
평문 `.csv` 까지 감긴 것으로 읽는다.

⚠ **다루는 확장자는 스킬의 표가 든다** — `read-drm.ps1` 의 `$HANDLER`(확장자 → 앱)를 그 자리에서 읽는다. 여기 따로 적으면
   스킬이 확장자를 늘린 날 길잡이만 낡는다. 껍데기의 글롭만은 파이썬을 띄우기 전이라 표를 못 읽어 한 벌을 든다 — 검사가
   표의 확장자마다 껍데기를 지나 걸리나를 잰다.
⚠ **스킬을 못 찾으면 그 사실을 말한다** — 감긴 파일이 있는데 읽을 길이 이 PC 에 없다는 것도 모델이 알아야 할 사실이다.
   그때는 표가 없어 확장자로 거르지 않는다(감긴 표지가 거른다).
⚠ **파일 내용은 안 싣는다** — 머리만 읽어 감겼나만 본다. 읽기는 스킬의 스크립트가 하고, 이 훅은 길을 가리킨다(#120).
⚠ **덧말은 사실로 쓴다** — 명령조의 바깥 글은 프롬프트 주입 방어에 걸릴 수 있다(웹 다시 찾기와 같은 까닭).
⚠ **명령의 경로는 슬래시로 적는다** — 모델이 Bash 로 칠 때 겹따옴표 안의 역슬래시는 셸이 접고, 겹역슬래시는 홈 훅
   (`bash-backslash-deny.sh`)이 돌려보낸다. PowerShell 은 슬래시 경로를 그대로 받는다.
⚠ **재다 져도 막지 않는다** — 뜻밖의 예외는 그 이름만 대는 한 줄로 바꾸고 0 으로 끝낸다. 길잡이가 죽은 사실은 남기되
   사람이 보낸 글은 그대로 간다.

부르는 자리 — 홈 `~/.claude/settings.json` 의 UserPromptSubmit · PostToolUseFailure. 앞에 셸 껍데기(`drm-guide.sh` · 곁
파일)가 서서 stdin 에 오피스 · PDF 확장자가 있을 때만 이 몸통을 띄운다. 심는 손과 주인 규율은 그림 문과 같다
(`image-gate.py` 머리말).

시험 — `python -X utf8 scripts/check-drm-guide.py`.
"""
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
OUT_SUBDIR = 'drm-text'   # 뽑은 글자를 둘 폴더 이름 — 세션 스크래치패드(없으면 임시 폴더) 밑
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


# ── 스킬 — 자리와 확장자 표 ──────────────────────────────────────────────────────
def skill_dir():
    """스킬 폴더 — 이 파일 곁(설정 저장소의 진본) · 홈. `SKILL.md` 와 `read-drm.ps1` 이 다 있어야 선다."""
    forced = os.environ.get(SKILL_DIR_ENV)
    if forced is not None:   # 시험이 자리를 주면 그 자리만 — 「없을 때」를 재려면 대체가 없어야 한다
        cands = [forced]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        cands = [os.path.normpath(os.path.join(here, '..', 'skills', SKILL)),
                 os.path.join(os.path.expanduser('~'), '.claude', 'skills', SKILL)]
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


# ── 덧말 ─────────────────────────────────────────────────────────────────────────
def slash(p):
    return p.replace('\\', '/')


def ps_quote(s):
    """PowerShell 홑따옴표 글자 — 안의 홑따옴표는 겹친다."""
    return "'" + s.replace("'", "''") + "'"


def message(event, paths, sdir, out_dir):
    names = ' · '.join(os.path.basename(p) for p in paths)
    if event == 'PostToolUseFailure':
        head = '%s — Read 가 진 %s 는 Fasoo DRM 에 감긴 파일이다(머리에 DRMONE).' % (NAME, names)
    else:
        head = '%s — 이 글이 가리키는 파일 가운데 Fasoo DRM 에 감긴 것: %s (머리에 DRMONE).' % (NAME, names)
    head += ' 감긴 파일은 Read 와 파서가 형식 인식 단계에서 진다.'
    if not sdir:
        return head + (' 글자를 뽑는 스킬 %s 가 이 PC 에 없다(~/.claude/skills 에 없음) — 이 자리에서는 읽을 길이 없다.'
                       % SKILL)
    cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "& %s -Path %s -OutDir %s"' % (
        ps_quote(slash(os.path.join(sdir, READER))),
        ','.join(ps_quote(slash(p)) for p in paths),
        ps_quote(slash(out_dir)))
    return head + (' 글자는 스킬 %s 가 설치된 오피스를 태워 뽑는다(%s — 차례와 주의는 그 2 · 3절). 이 파일들이면: %s'
                   ' — 뽑은 글자는 -OutDir 에 「<파일 이름>.txt」로 남는다.'
                   % (SKILL, slash(os.path.join(sdir, 'SKILL.md')), cmd))


def emit(event, context):
    sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': event, 'additionalContext': context}},
                                ensure_ascii=False))
    return 0


# ── 판정 ─────────────────────────────────────────────────────────────────────────
def guide(data):
    event = data.get('hook_event_name') or ''
    if event == 'UserPromptSubmit':
        toks = None
        text = str(data.get('prompt') or '')
    elif event == 'PostToolUseFailure' and data.get('tool_name') == 'Read':
        toks = [str((data.get('tool_input') or {}).get('file_path') or '')]
        text = ''
    else:
        return 0
    sdir = skill_dir()
    exts = handled_exts(sdir) if sdir else set()
    alt = ext_alt(exts) if exts else ''
    ext_re = re.compile(r'(.*?\.(?:%s))(?![A-Za-z0-9_])' % alt, re.I) if alt else None
    if toks is None:
        toks = candidates(text, alt)
    cwd = str(data.get('cwd') or '')
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
    if not hits:
        return 0
    out_dir = os.path.join(str(data.get('scratchpad_dir') or tempfile.gettempdir()), OUT_SUBDIR)
    return emit(event, message(event, hits, sdir, out_dir))


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
        if event in ('UserPromptSubmit', 'PostToolUseFailure'):
            return emit(event, '%s — 경로를 재다 졌다(%s). 감긴 파일(머리에 DRMONE)은 Read 와 파서로 안 열리고, '
                               '스킬 %s 가 설치된 오피스로 글자를 뽑는다.' % (NAME, type(e).__name__, SKILL))
        return 0


if __name__ == '__main__':
    sys.exit(main())
