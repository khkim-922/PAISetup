"""Codex 의 전역 지침(`~/.codex/AGENTS.md`)에 우리 규범 · 룰 블록을 얹는다 (결정 0099).

    python -X utf8 codex-norms.py --norms <규범> --rules <룰 폴더> [--rules-home <가리킬 자리>] --target ~/.codex/AGENTS.md
    python -X utf8 codex-norms.py --remove --target ~/.codex/AGENTS.md     # 칸을 끈 판 — 블록만 걷는다
    python -X utf8 codex-norms.py ... --out <파일>     # 대상은 안 고치고 고칠 결과만 그 파일에 쓴다

부르는 자는 둘이다 — 배포본 설치기의 제작자 칸(Codex 칸)과 설정 저장소의 `deploy.ps1`(`~/.codex` 가 있고 Codex 를 골랐으면).
한 자가 블록을 지어 두 길이 같은 판을 낸다. 고르기는 사용자 환경변수 `PAISETUP_PERSONAL` 이 들고 둘이 같은 값을 읽는다.

**왜 옮겨 쓰나.** Claude 는 홈 규범을 `~/.claude/CLAUDE.md` 에서, agy 는 include 한 줄로 같은 파일을 읽는다(0083). Codex 의
`AGENTS.md` 에는 다른 파일을 끌어오는 길이 없다(Codex 문서 「Custom instructions with AGENTS.md」). 그래서 원본에서 **뽑아**
쓴다 — 블록은 매번 원본에서 다시 짓고 손으로 고치지 않는다. 블록 머리가 그 사실을 적는다.

**룰은 가리킨다.** Claude 룰은 특정 파일을 만질 때만 걸리는 장치(`paths:`)인데 Codex 에는 그런 장치가 없다. 규범에 통째로
붙이면 늘 실려 붓는다. 그래서 룰 머리말의 `globs:` · `description:` 으로 「이 파일들을 만질 때는 이 룰을 먼저 읽는다」 한 줄씩을
짓는다 — 본문은 Codex 가 그 자리에서 읽는다. 머리말 둘은 agy 가 이미 쓰는 칸이다(0083).
⚠ **가리키는 자리는 중립 자리(`~/.paisetup/norms/rules`)다** — Claude 홈(`~/.claude/rules`)은 Claude 가 스스로 싣는 자리라,
   Claude 칸을 끄고 Codex 칸만 켠 사람에게 거기 깔면 Claude 에도 실린다(결정 0099).

**사람의 글은 그대로 둔다.** 블록은 표지(`BEGIN` · `END`) 사이만 간다. 표지가 없으면 끝에 붙이고, 짝이 안 맞으면(하나만 · 둘
이상) 안 건드리고 까닭을 낸다. 줄바꿈은 파일의 것(CRLF · LF)을 따른다.

출력 계약 — 한 줄에 하나: CHANGED=0|1 · ERROR=<까닭>(아무것도 안 썼다)
"""
import argparse
import os
import pathlib
import re
import shutil
import sys
import tempfile

BEGIN = '<!-- paisetup:norms BEGIN -->'
END = '<!-- paisetup:norms END -->'
RULES_HOME = '~/.paisetup/norms/rules'   # 룰이 깔리는 중립 자리 — 가리키는 줄이 쓰는 경로(기본값)
FRONT = re.compile(r'\A---\r?\n(.*?)\r?\n---\r?\n', re.S)


def field(front, key):
    """머리말의 한 줄 값 — 감싼 따옴표를 걷는다. 없으면 빈 글."""
    m = re.search(r'^%s:\s*(.+?)\s*$' % re.escape(key), front, re.M)
    return m.group(1).strip('"\'') if m else ''


def rule_lines(rules_dir, rules_home):
    out = []
    for f in sorted(pathlib.Path(rules_dir).glob('*.md')):
        m = FRONT.match(f.read_text(encoding='utf-8-sig'))
        front = m.group(1) if m else ''
        globs, desc = field(front, 'globs'), field(front, 'description')
        if not globs:
            continue
        line = '- `%s` 를 만질 때는 `%s/%s` 를 먼저 읽는다' % (globs, rules_home, f.name)
        out.append(line + (' — ' + desc if desc else ''))
    return out


def block(norms, rules_dir, rules_home=RULES_HOME):
    body = norms.rstrip() + '\n'
    lines = rule_lines(rules_dir, rules_home) if rules_dir and os.path.isdir(rules_dir) else []
    if lines:
        body += ('\n## 영역 룰 — 파일을 만질 때만 걸리는 원칙\n\n'
                 '아래 파일을 만지기 전에 가리킨 룰을 읽고 따른다. 위 규범이 「룰이 든다」고 적은 자리가 이것들이다.\n\n'
                 + '\n'.join(lines) + '\n')
    head = ('%s\n<!-- 설치 · 배포가 제작자 규범 원본에서 뽑아 쓴다. 여기서 고치면 다음 설치에 사라진다 — '
            '원본을 고친다. -->\n\n' % BEGIN)
    return head + body + END + '\n'


def merge(current, new_block):
    """(결과, 까닭). 까닭이 있으면 못 고친다. `new_block` 이 빈 글이면 블록을 걷는다."""
    nb, ne = current.count(BEGIN), current.count(END)
    if nb == 0 and ne == 0:
        if not new_block:
            return current, ''
        if not current.strip():
            return new_block, ''
        return current.rstrip('\r\n') + '\n\n' + new_block, ''
    if nb != 1 or ne != 1 or current.index(BEGIN) > current.index(END):
        return None, '표지 짝이 안 맞는다(BEGIN %d · END %d) — 안 건드린다' % (nb, ne)
    i, j = current.index(BEGIN), current.index(END) + len(END)
    rest = current[j:]
    rest = rest[1:] if rest.startswith('\n') else rest[2:] if rest.startswith('\r\n') else rest
    head = current[:i]
    if not new_block:   # 걷기 — 붙일 때 앞에 둔 빈 줄 하나도 같이 걷는다
        head = head[:-1] if head.endswith('\n\n') else head
        return (head + rest) if (head + rest).strip() else '', ''
    return head + new_block + rest, ''


def write_atomic(path, text):
    path = path.resolve() if path.is_symlink() else path
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, part = tempfile.mkstemp(prefix=path.name + '.', suffix='.part', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        if path.exists():
            shutil.copymode(path, part)
        os.replace(part, path)
    except BaseException:
        if os.path.exists(part):
            os.remove(part)
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--norms')
    ap.add_argument('--rules')
    ap.add_argument('--rules-home', default=RULES_HOME)
    ap.add_argument('--remove', action='store_true')
    ap.add_argument('--target', required=True)
    ap.add_argument('--out')
    a = ap.parse_args()
    try:
        new_block = ''
        if not a.remove:
            norms_path = pathlib.Path(a.norms or '').expanduser()
            if not a.norms or not norms_path.is_file():
                print('ERROR=규범 원본이 없다(%s) — 안 건드린다' % (a.norms or '--norms 없음'))
                return 1
            norms = norms_path.read_text(encoding='utf-8-sig').replace('\r\n', '\n')
            new_block = block(norms, os.path.expanduser(a.rules) if a.rules else None, a.rules_home)
        target = pathlib.Path(a.target).expanduser()
        raw = target.read_bytes() if target.exists() else b''
        current = raw.decode('utf-8-sig')
        crlf = '\r\n' in current
        lf = current.replace('\r\n', '\n')
        merged, why = merge(lf, new_block)
        if why:
            print('ERROR=' + why)
            return 1
        if crlf:
            merged = merged.replace('\n', '\r\n')
        if raw.startswith(b'\xef\xbb\xbf') and merged:
            merged = '\ufeff' + merged
        if a.out:
            pathlib.Path(a.out).write_bytes(merged.encode('utf-8'))
        changed = merged.encode('utf-8') != raw
        if changed and not a.out:
            write_atomic(target, merged)
        print('CHANGED=%d' % int(changed))
        return 0
    except Exception as e:  # noqa: BLE001 — 부르는 자는 이 한 줄로 까닭을 받는다
        print('ERROR=%s: %s' % (type(e).__name__, e))
        return 1


if __name__ == '__main__':
    sys.exit(main())
