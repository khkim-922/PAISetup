"""Codex 훅 예시를 사용자의 `config.toml` 에 병합한다 — 우리 훅만 갈고, 남의 훅은 그대로 둔다.

    python -X utf8 codex-hook-install.py --config ~/.codex/config.toml --example codex-hooks.example.toml

**무엇이 우리 것인가.** `[hooks]` 의 이벤트 배열 안 훅 가운데 명령(`command` · `commandWindows`)이 씨앗 자리의 우리 몸통
(`MARKER_DIR` + `MARKERS`)을 부르는 훅이다. 판정은 항목(matcher 묶음)이 아니라 **훅 하나** 단위다 — 사람이 우리 묶음 안에
제 훅을 끼워 넣었으면 그 훅은 같은 matcher 의 제 항목으로 남는다. 이벤트마다 「남의 항목 + 예시의 항목」이 되도록 배열을
고쳐 쓴다 — 남의 항목은 뜻이 그대로 남고, 우리 항목은 예시가 바뀌면 따라간다.

**뜻으로 재고 나서만 쓴다.** 원본과 결과를 둘 다 TOML 로 읽어, 결과가 「원본 + 이번에 고친 이벤트 배열」과
**뜻이 같을 때만** 파일을 갈아 끼운다. 줄로 고치는 손이 무엇을 놓쳐도 사용자 설정이 깨지거나 남의 훅이
사라진 채 쓰이는 일은 없다 — 그 자리는 쓰지 않고 오류로 끝난다.
⚠ **다시 지은 배열의 글꼴은 바뀐다** — 그 배열 안의 주석(주석으로 막아 둔 항목 포함)은 뜻이 아니라 TOML 이 안 든다.
  그래서 고쳐 쓰기 전에 원본을 곁에 떠 둔다(`BACKUP=`).

**못 알아보는 꼴은 안 건드린다.** 훅을 `[hooks]` 표의 `이벤트 = [ … ]` 가 아닌 꼴(`[[hooks.이벤트]]` · 맨 위의
점 이름 · 인라인 표)로 적은 설정은 줄 위치를 확정할 수 없다. 그 이벤트는 건너뛰고 까닭을 낸다.

표준 출력 — 한 줄에 하나:
  CHANGED=0|1                     고쳐 썼나
  SKIP=<이벤트>(<까닭>)[,…]        안 건드린 이벤트 — 설치기의 끝 검증이 빠진 배선을 [X] 로 알린다
  BACKUP=<경로>                    고쳐 쓰기 전 원본을 떠 둔 자리
  ERROR=<종류>:<말>                아무것도 안 썼다 — 종료 코드 1
"""

import argparse
import copy
import datetime
import json
import math
import os
import pathlib
import re
import shutil
import sys
import tempfile

try:
    import tomllib
except ImportError:   # 3.10 이하 — 읽는 자가 없으면 뜻을 못 재므로 쓰지 않는다
    tomllib = None

EVENTS = ('UserPromptSubmit', 'PreToolUse', 'PostToolUse')
# 우리 몸통은 늘 씨앗 자리에서 부른다 — 이름만 보면 사람의 `my-drm-guide.py` 도 우리 것으로 읽힌다
MARKER_DIR = 'config-repo/.claude/hooks/'
MARKERS = ('drm-guide.py', 'codex-image-gate.py', 'codex-safety-hooks.py')
HOOKS_TABLE = 'hooks'
COMMAND_KEYS = ('command', 'commandWindows')
NESTED_HOOKS_KEY = 'hooks'
BOM = '﻿'
BACKUP_SUFFIX = '.before-hooks-'

KEY_HEAD = re.compile(r'^\s*([A-Za-z0-9_-]+)\s*=\s*')
# 맨 위에서 `hooks` 를 표 머리 없이 정의하는 꼴 — 점 이름(`hooks.x = …`)과 인라인 표(`hooks = { … }`)
ROOT_HOOKS_KEY = re.compile(r'[ \t]*["\']?hooks["\']?[ \t]*[.=]')
BARE_KEY = re.compile(r'^[A-Za-z0-9_-]+$')
NAN = '\0nan'   # 뜻을 견줄 때 nan 을 대신 세우는 값 — nan 은 제 자신과도 안 같다


class Skip(Exception):
    """이 이벤트는 못 알아보는 꼴이라 안 건드린다."""


def ours_hook(h):
    if not isinstance(h, dict):
        return False
    for k in COMMAND_KEYS:
        cmd = str(h.get(k) or '').replace('\\', '/')
        if any(MARKER_DIR + m in cmd for m in MARKERS):
            return True
    return False


def without_ours(entry):
    """항목에서 우리 훅을 걷는다 — 남은 훅이 없으면 None, 걷을 것이 없으면 그대로."""
    hooks = entry.get(NESTED_HOOKS_KEY)
    if not isinstance(hooks, list):
        return entry
    kept = [h for h in hooks if not ours_hook(h)]
    if len(kept) == len(hooks):
        return entry
    if not kept:
        return None
    return {**entry, NESTED_HOOKS_KEY: kept}


def string_end(text, i):
    """`i` 에서 여는 문자열이 끝난 바로 뒤 자리. 여러 줄 문자열은 닫는 따옴표 뒤의 따옴표 두 개까지 본문이다(TOML 1.0)."""
    n = len(text)
    q = text[i]
    if text.startswith(q * 3, i):
        j = i + 3
        while j < n:
            if q == '"' and text[j] == '\\':
                j += 2
                continue
            if text.startswith(q * 3, j):
                end = j + 3
                extra = 0
                while end < n and text[end] == q and extra < 2:
                    end += 1
                    extra += 1
                return end
            j += 1
        raise ValueError('여러 줄 문자열이 안 닫혔다')
    j = i + 1
    while j < n and text[j] != q:
        if text[j] == '\n':
            raise ValueError('문자열이 안 닫혔다')
        j += 2 if (q == '"' and text[j] == '\\') else 1
    if j >= n:
        raise ValueError('문자열이 안 닫혔다')
    return j + 1


def value_end(text, i):
    """`i` 에서 시작하는 값 뒤의 줄바꿈 자리(없으면 글 끝)를 돌려준다.

    문자열 · 주석 안의 괄호는 안 센다. 결과는 뒤에서 TOML 로 다시 읽어 재므로, 여기서 놓친 꼴은 쓰기 전에 걸린다.
    """
    depth = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in '"\'':
            i = string_end(text, i)
            continue
        if c == '#':
            k = text.find('\n', i)
            i = n if k < 0 else k
            continue
        if c in '[{':
            depth += 1
        elif c in ']}':
            depth -= 1
        elif c == '\n' and depth <= 0:
            return i
        i += 1
    return n


def header(line):
    """표 머리 줄이면 `('table', 이름)` · `('array-table', None)`, 아니면 None. 따옴표 안의 `[` · `]` 는 안 센다."""
    s = line.strip()
    if s.startswith('[['):
        return 'array-table', None
    if not s.startswith('['):
        return None
    i, n = 1, len(s)
    while i < n and s[i] != ']':
        i = string_end(s, i) if s[i] in '"\'' else i + 1
    if i >= n:
        return None
    rest = s[i + 1:].strip()
    if rest and not rest.startswith('#'):
        return None
    name = s[1:i].strip()
    if len(name) >= 2 and name[0] == name[-1] and name[0] in '"\'' and name[0] not in name[1:-1]:
        name = name[1:-1]   # 한 마디를 따옴표로 감싼 이름(`["hooks"]`)은 맨 이름과 같은 표다
    return 'table', name


def statements(text):
    """최상위 문장을 차례로 낸다 — `(종류, 시작, 끝, 이름)`. 종류는 'table' · 'array-table' · 'key' · 'other'.

    값이 여러 줄에 걸쳐도 한 문장이다 — 그래서 배열 안의 줄이 표 머리로 읽히는 일이 없다.
    끝은 줄바꿈(`\\r\\n` 이면 `\\r`) 앞이다 — 바꿔 넣는 글이 줄끝을 안 먹는다.
    """
    i = 0
    n = len(text)
    while i < n:
        k = text.find('\n', i)
        eol = n if k < 0 else k
        line = text[i:eol]
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            kind, name, nl_at = 'other', None, eol
        else:
            h = header(line)
            if h:
                (kind, name), nl_at = h, eol
            else:
                m = KEY_HEAD.match(line)
                nl_at = value_end(text, i + (m.end() if m else len(line) - len(line.lstrip())))
                kind, name = 'key', (m.group(1) if m else None)
        end = nl_at - 1 if nl_at > i and text[nl_at - 1] == '\r' else nl_at
        yield kind, i, end, name
        i = nl_at + 1


def hooks_layout(text):
    """`[hooks]` 표를 잰다 — `(표 머리가 있나, 맨 위에서 표 머리 없이 정의됐나, 새 대입을 끼울 자리,
    그 표 안 이벤트 대입의 자리 {이벤트: (시작, 끝)})`.

    끼울 자리는 그 표의 마지막 대입 바로 뒤다(대입이 없으면 머리 줄 뒤) — 표 뒤의 빈 줄 · 주석은 다음 표 몫으로 둔다.
    """
    has_header = False
    hooks_at_root = False
    insert_at = None
    found = {}
    current = None
    for kind, start, end, name in statements(text):
        if kind in ('table', 'array-table'):
            current = name if kind == 'table' else 'array-table'
            if current == HOOKS_TABLE:
                has_header = True
                insert_at = end
            continue
        if kind != 'key':
            continue
        if current is None and ROOT_HOOKS_KEY.match(text, start):
            hooks_at_root = True
        if current == HOOKS_TABLE:
            insert_at = end
            if name in EVENTS:
                found[name] = (start, end)
    return has_header, hooks_at_root, insert_at, found


def render_key(k):
    return k if BARE_KEY.match(k) else json.dumps(k, ensure_ascii=False)


def render_value(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isnan(v):
            return 'nan'
        if math.isinf(v):
            return 'inf' if v > 0 else '-inf'
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
        return v.isoformat()
    if isinstance(v, list):
        return '[' + ', '.join(render_value(x) for x in v) + ']'
    if isinstance(v, dict):
        return '{ ' + ', '.join(f'{render_key(k)} = {render_value(x)}' for k, x in v.items()) + ' }'
    raise Skip(f'다시 짓지 못하는 값({type(v).__name__})')


def render_array(event, entries, nl):
    """예시와 같은 꼴 — 항목 하나가 한 덩어리, 그 안의 `hooks` 배열은 한 줄에 하나."""
    out = [f'{event} = [']
    for e in entries:
        parts = []
        for k, v in e.items():
            if k == NESTED_HOOKS_KEY and isinstance(v, list):
                inner = ''.join(f'    {render_value(h)},{nl}' for h in v)
                parts.append(f'{render_key(k)} = [{nl}{inner}  ]')
            else:
                parts.append(f'{render_key(k)} = {render_value(v)}')
        out.append('  { ' + ', '.join(parts) + ' },')
    out.append(']')
    return nl.join(out)


def plan_events(data, wanted):
    """이벤트마다 바라는 배열을 정한다 — `(고칠 것 {이벤트: 배열}, 건너뛴 것 [이벤트(까닭)])`."""
    hooks = data.get(HOOKS_TABLE, {})
    if not isinstance(hooks, dict):
        return {}, [f'{ev}(hooks 가 표가 아니다)' for ev in EVENTS]
    plan, skipped = {}, []
    for ev in EVENTS:
        cur = hooks.get(ev, [])
        if not isinstance(cur, list) or not all(isinstance(e, dict) for e in cur):
            skipped.append(f'{ev}(배열이 아니다)')
            continue
        kept = [e for e in (without_ours(x) for x in cur) if e is not None]
        desired = kept + wanted[ev]
        if desired != cur:
            plan[ev] = desired
    return plan, skipped


def comparable(x):
    """뜻을 견줄 꼴 — nan 은 제 자신과도 안 같아 그대로 견주면 멀쩡한 결과가 「다르다」가 된다."""
    if isinstance(x, float) and math.isnan(x):
        return NAN
    if isinstance(x, list):
        return [comparable(v) for v in x]
    if isinstance(x, dict):
        return {k: comparable(v) for k, v in x.items()}
    return x


def bare_lf(s):
    return s.replace('\r\n', '').count('\n')


def merge(config_text, example_text):
    """`(새 글, 고쳤나, 건너뛴 것)`. 뜻이 어긋나면 ValueError — 그때는 아무것도 안 쓴다."""
    if tomllib is None:
        raise RuntimeError('tomllib 이 없다 — 파이썬 3.11 이상이 든다')
    bom = config_text.startswith(BOM)
    text = config_text[1:] if bom else config_text
    nl = '\r\n' if '\r\n' in text else '\n'
    data = tomllib.loads(text)
    example = tomllib.loads(example_text.lstrip(BOM)).get(HOOKS_TABLE, {})
    missing = [ev for ev in EVENTS if not isinstance(example.get(ev), list)]
    if missing:
        raise ValueError('예시에 이벤트가 없다: ' + ', '.join(missing))
    wanted = {ev: example[ev] for ev in EVENTS}

    plan, skipped = plan_events(data, wanted)
    has_header, hooks_at_root, insert_at, found = hooks_layout(text)
    for ev in list(plan):
        if ev in data.get(HOOKS_TABLE, {}) and ev not in found:
            skipped.append(f'{ev}([hooks] 표의 대입이 아닌 꼴)')
            del plan[ev]
        elif hooks_at_root and not has_header:
            # 맨 위의 `hooks.x = …` · `hooks = { … }` 가 표를 이미 정의했다 — 머리를 새로 세우면 같은 표를 두 번 정의한다
            skipped.append(f'{ev}(hooks 가 [hooks] 표 머리 없이 정의됐다)')
            del plan[ev]
    rendered = {}
    for ev in list(plan):
        try:
            rendered[ev] = render_array(ev, plan[ev], nl)
        except Skip as s:
            skipped.append(f'{ev}({s})')
            del plan[ev]
    if not plan:
        return config_text, False, skipped

    # 뒤에서부터 바꿔 앞의 자리가 안 밀린다
    edits = [(found[ev][0], found[ev][1], rendered[ev]) for ev in plan if ev in found]
    added = [rendered[ev] for ev in plan if ev not in found]
    if added:
        block = nl.join(added)
        if has_header:
            edits.append((insert_at, insert_at, nl + block))
        else:
            body = text.rstrip('\r\n')
            sep = nl + nl if body else ''
            edits.append((len(body), len(text), f'{sep}[{HOOKS_TABLE}]{nl}{block}{nl}'))
    new = text
    for start, end, repl in sorted(edits, key=lambda e: e[0], reverse=True):
        new = new[:start] + repl + new[end:]

    expect = copy.deepcopy(data)
    expect.setdefault(HOOKS_TABLE, {}).update(plan)
    try:
        result = tomllib.loads(new)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f'병합 결과가 TOML 로 안 읽힌다 — 쓰지 않았다({exc})') from exc
    if comparable(result) != comparable(expect):
        raise ValueError('병합 결과가 뜻과 다르다 — 쓰지 않았다')
    if nl == '\r\n' and bare_lf(new) > bare_lf(text):
        raise ValueError('병합 결과에 줄끝이 섞였다 — 쓰지 않았다')
    return (BOM + new if bom else new), True, skipped


def write_atomic(path, text):
    """옆 파일에 쓰고 옮긴다. 심볼릭 링크면 가리키는 파일을 갈고, 있던 파일의 권한을 잇는다."""
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
    ap.add_argument('--config', required=True)
    ap.add_argument('--example', required=True)
    args = ap.parse_args()
    config = pathlib.Path(args.config).expanduser()
    example = pathlib.Path(args.example)
    try:
        current = ''
        if config.exists():
            with open(config, encoding='utf-8', newline='') as f:
                current = f.read()
        with open(example, encoding='utf-8', newline='') as f:
            wanted_text = f.read()
        new, changed, skipped = merge(current, wanted_text)
        if changed and config.exists():
            stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            backup = config.resolve().with_name(config.name + BACKUP_SUFFIX + stamp)
            shutil.copy2(config.resolve(), backup)
            print('BACKUP=' + str(backup))
        if changed:
            write_atomic(config, new)
        if skipped:
            print('SKIP=' + ','.join(skipped))
        print('CHANGED=' + ('1' if changed else '0'))
        return 0
    except Exception as exc:   # 설치기와의 약속은 ERROR= 한 줄이다 — 트레이스백으로 죽으면 까닭이 안 읽힌다
        print('ERROR=' + type(exc).__name__ + ':' + str(exc))
        return 1


if __name__ == '__main__':
    sys.exit(main())
