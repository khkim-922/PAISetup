"""회사 Codex 틀의 자리만 사용자의 `config.toml` 에 맞춘다 — 틀에 없는 키 · 표 · 주석은 그대로 둔다.

    python -X utf8 codex-config-merge.py --config ~/.codex/config.toml --template posco/Codex-CLI.setting.toml
    python -X utf8 codex-config-merge.py --config ~/.codex/config.toml --template posco/Codex-CLI.setting.toml --check

`--check` 는 같은 판정을 하되 아무것도 안 쓴다 — 설치기의 끝 검증이 부른다.

**왜 있나.** 사내 Codex 는 회사 틀(값 파일의 `#codex-config`)로 게이트웨이를 탄다. 그런데 그 파일에는 틀 밖의 것도 산다 —
Codex 가 적는 훅 신뢰(`[hooks.state]`)와 폴더 신뢰(`[projects.*]`), 사람이 둔 키. 틀로 파일을 통째로 갈면 그것이 다 사라지고,
그 파일은 틀과 글자가 같아질 날이 없어 설치마다 갈린다. 그래서 틀이 든 자리만 틀의 값으로 맞춘다.

**자리는 틀의 대입 하나다** — 표 머리 아래의 `키 = 값`, 맨 위의 대입, 점 이름. 그 자리의 값이 틀의 값과 뜻이 다르면 값 글자만
틀의 글자로 갈고(같은 줄의 주석은 둔다), 없으면 틀의 꼴(표 머리 · 키 글자 · 값 글자)로 더한다. 뜻이 같으면 글꼴이 달라도
안 건드린다. 줄끝(CRLF) · BOM 은 원본을 따른다.
⚠ **`[hooks]` 는 안 맞춘다** — 이벤트 배열에는 사람 훅이 섞이고 Codex 의 신뢰 열쇠가 그 자리 번호라, 병합 규칙의 진본인
  곁의 `codex-hook-install.py` 가 든다(설치기가 이 손 뒤에 부른다). 틀의 훅 블록은 그 병합기의 예시와 같다 — 그 병합기의
  검사가 잰다.
⚠ **틀이 더는 안 드는 키는 안 걷는다** — 사람이 둔 키와 가를 기록이 없다.

**뜻으로 재고 나서만 쓴다.** 원본과 결과를 둘 다 TOML 로 읽어, 결과가 「원본 + 틀의 자리마다 틀의 값」과 뜻이 같을 때만
갈아 끼운다. 원본을 TOML 로 못 읽거나, 틀의 자리가 못 알아보는 꼴(인라인 표 · 배열 표 안 · 원본에서는 표인 자리)이면
아무것도 안 쓰고 오류로 끝난다. 고쳐 쓰기 전 원본은 곁에 떠 둔다(`<설정 이름>.before-pgpt-<시각>`). 줄 나누기 · 원본 떠 두기 ·
옆 파일에 쓰고 옮기기는 곁의 병합기 것을 불러 쓴다.
설정 파일이 없으면 오류다 — 없는 자리에는 설치기가 틀을 그대로 쓴다.

표준 출력 — 한 줄에 하나:
  SET=<자리>         틀의 값으로 맞춘 자리(`--check` 면 맞출 자리) — 이름을 점으로 이었다(보이기만 한다)
  CHANGED=0|1        고쳐 썼나(`--check` 면 고칠 것이 있나)
  BACKUP=<경로>       고쳐 쓰기 전 원본을 떠 둔 자리
  ERROR=<종류>:<말>   아무것도 안 썼다 — 종료 코드 1. 종류 = config · template · shape · verify (그 밖은 예외 이름)
종료 코드: 0 맞췄다 · 맞다(`--check` 는 CHANGED 가 판정이다) · 1 ERROR · 2 인자가 틀렸다(argparse).
"""

import argparse
import copy
import importlib.util
import pathlib
import sys

try:
    import tomllib
except ImportError:   # 3.10 이하 — 읽는 자가 없으면 뜻을 못 재므로 쓰지 않는다
    tomllib = None

MERGER_FILE = 'codex-hook-install.py'   # 줄 나누기 · 원본 떠 두기 · 옆 파일 쓰기의 진본 — 이 파일 곁에 같이 실린다
KEEP_TABLES = ('hooks',)                # 맞추지 않는 맨 위 표 — 맨 위 「[hooks] 는 안 맞춘다」
BACKUP_SUFFIX = '.before-pgpt-'
M = None                                # 곁의 병합기 — main 이 싣는다


class Fail(Exception):
    """한 줄 계약으로 끝낸다 — `ERROR=<kind>:<msg>`."""

    def __init__(self, kind, msg):
        super().__init__(f'{kind}:{msg}')
        self.kind, self.msg = kind, msg


def load_merger():
    path = pathlib.Path(__file__).resolve().with_name(MERGER_FILE)
    if not path.is_file():
        raise Fail('config', f'곁에 {MERGER_FILE} 이 없다')
    spec = importlib.util.spec_from_file_location('codex_hook_install', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def single_path(data):
    """`{a: {b: …}}` 꼴로 한 갈래만 든 표에서 이름의 차례를 낸다 — 끝은 빈 표거나 표가 아닌 값이다."""
    path = []
    while isinstance(data, dict) and data:
        (k, data), = data.items()
        path.append(k)
    return tuple(path)


def key_path(key_text):
    """대입의 키 글자(`a` · `"a.b".c` · `'x'`)를 이름의 차례로 — 따옴표 · 이스케이프는 TOML 이 푼다."""
    return single_path(tomllib.loads(key_text + ' = 0'))


def bracket_inner(line, depth):
    """표 머리 줄(`[이름]` · `[[이름]]`)의 이름 글자. 따옴표 안의 `]` 는 안 센다."""
    s = line.strip()
    i = depth
    while i < len(s) and s[i] != ']':
        i = M.string_end(s, i) if s[i] in '"\'' else i + 1
    return s[depth:i]


def split_assignment(text, start, end):
    """대입 문장의 `(키 글자, 값의 시작, 값의 끝)` — 값의 끝은 같은 줄 주석 · 꼬리 빈칸 앞이다."""
    i = start
    while i < end and text[i] != '=':
        i = M.string_end(text, i) if text[i] in '"\'' else i + 1
    key_text = text[start:i].strip()
    vs = i + 1
    while vs < end and text[vs] in ' \t':
        vs += 1
    j, depth = vs, 0
    while j < end:
        c = text[j]
        if c in '"\'':
            j = M.string_end(text, j)
            continue
        if c == '#':
            if depth <= 0:
                break
            k = text.find('\n', j)   # 배열 안의 주석 — 값의 일부다
            j = end if k < 0 or k > end else k
            continue
        if c in '[{':
            depth += 1
        elif c in ']}':
            depth -= 1
        j += 1
    while j > vs and text[j - 1] in ' \t\r\n':
        j -= 1
    return key_text, vs, j


def walk(text):
    """최상위 문장을 차례로 — 표 머리는 `('table'|'array-table', 자리, 시작, 끝)`,
    대입은 `('key', 선 표의 자리, 표 안의 키 자리, 시작, 끝, 키 글자, 값의 시작, 값의 끝, 배열 표 안인가)`."""
    section, in_array = (), False
    for kind, start, end, _ in M.statements(text):
        if kind in ('table', 'array-table'):
            depth = 1 if kind == 'table' else 2
            section = single_path(tomllib.loads('[' * depth + bracket_inner(text[start:end], depth) + ']' * depth))
            in_array = kind == 'array-table'
            yield kind, section, start, end
        elif kind == 'key':
            key_text, vs, ve = split_assignment(text, start, end)
            yield 'key', section, key_path(key_text), start, end, key_text, vs, ve, in_array


def lookup(data, path):
    for k in path:
        data = data[k]
    return data


def assign(data, path, value):
    for k in path[:-1]:
        data = data.setdefault(k, {})
    data[path[-1]] = value


def is_prefix(a, b):
    """`a` 가 `b` 의 앞자리인가(같으면 거짓)."""
    return len(a) < len(b) and b[:len(a)] == a


def template_leaves(template_text):
    """틀의 자리마다 `(자리, 선 표, 그 표의 머리 줄, 키 글자, 값 글자, 값)` — `[hooks]` 는 뺀다."""
    try:
        data = tomllib.loads(template_text)
    except tomllib.TOMLDecodeError as exc:
        raise Fail('template', f'틀을 TOML 로 못 읽는다({exc})') from exc
    leaves, heads = [], {(): None}
    for item in walk(template_text):
        if item[0] == 'array-table':
            raise Fail('template', f'틀에 배열 표가 있다({".".join(item[1])}) — 자리로 못 맞춘다')
        if item[0] == 'table':
            heads[item[1]] = template_text[item[2]:item[3]].strip()
            continue
        _, section, rel, _, _, key_text, vs, ve, _ = item
        full = section + rel
        if full[0] in KEEP_TABLES:
            continue
        leaves.append((full, section, heads[section], key_text, template_text[vs:ve], lookup(data, full)))
    return leaves


def merge(config_text, template_text):
    """`(새 글, 고쳤나, 맞춘 자리)`. 못 알아보는 꼴 · 뜻 어긋남이면 Fail — 그때는 아무것도 안 쓴다."""
    if tomllib is None:
        raise Fail('config', 'tomllib 이 없다 — 파이썬 3.11 이상이 든다')
    leaves = template_leaves(template_text.lstrip(M.BOM))
    bom = config_text.startswith(M.BOM)
    text = config_text[1:] if bom else config_text
    nl = '\r\n' if '\r\n' in text else '\n'
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise Fail('config', f'설정을 TOML 로 못 읽는다 — 안 건드린다({exc})') from exc

    found, keys, tables, arrays = {}, [], [], []
    insert_at = {}             # 표마다 새 대입을 끼울 자리 — 그 표의 마지막 대입 뒤(대입이 없으면 머리 줄 뒤)
    first_head = None
    for item in walk(text):
        if item[0] in ('table', 'array-table'):
            (arrays if item[0] == 'array-table' else tables).append(item[1])
            if item[0] == 'table':
                insert_at[item[1]] = item[3]
            if first_head is None:
                first_head = item[2]
            continue
        _, section, rel, _, end, _, vs, ve, in_array = item
        if in_array:
            continue
        full = section + rel
        keys.append(full)
        found[full] = (vs, ve)
        insert_at[section] = end

    def unify(s):
        return s.replace('\r\n', '\n').replace('\n', nl)

    edits, missing, sets = [], [], []
    for path, section, head, key_text, value_text, value in leaves:
        name = '.'.join(path)
        if any(is_prefix(k, path) for k in keys):
            raise Fail('shape', f'{name} 이 인라인 값 안에 있다 — 그 자리만 못 맞춘다')
        if any(is_prefix(path, k) for k in keys) or any(t == path or is_prefix(path, t) for t in tables):
            raise Fail('shape', f'{name} 이 설정에서는 표다 — 틀은 값이다')
        if any(a == path or is_prefix(a, path) for a in arrays):
            raise Fail('shape', f'{name} 이 배열 표 안에 있다')
        if path in found:
            if M.comparable(lookup(data, path)) == M.comparable(value):
                continue
            vs, ve = found[path]
            edits.append((vs, ve, unify(value_text)))
        else:
            missing.append((section, head, f'{unify(key_text)} = {unify(value_text)}'))
        sets.append(name)
    if not sets:
        return config_text, False, []

    groups = {}
    for section, head, line in missing:
        groups.setdefault((section, head), []).append(line)
    appended = []
    for (section, head), lines in groups.items():
        block = nl.join(lines)
        if section in insert_at:
            edits.append((insert_at[section], insert_at[section], nl + block))
        elif not section:      # 맨 위 대입이 없다 — 첫 표 머리 앞에(표도 없으면 끝에)
            if first_head is None:
                appended.append(block)
            else:
                edits.append((first_head, first_head, block + nl + nl))
        else:
            appended.append(unify(head) + nl + block)
    new = text
    for start, end, repl in sorted(edits, key=lambda e: e[0], reverse=True):
        new = new[:start] + repl + new[end:]
    if appended:
        body = new.rstrip('\r\n')
        new = body + (nl + nl if body else '') + (nl + nl).join(appended) + nl

    expect = copy.deepcopy(data)
    for path, _, _, _, _, value in leaves:
        assign(expect, path, copy.deepcopy(value))
    try:
        result = tomllib.loads(new)
    except tomllib.TOMLDecodeError as exc:
        raise Fail('verify', f'맞춘 결과가 TOML 로 안 읽힌다 — 쓰지 않았다({exc})') from exc
    if M.comparable(result) != M.comparable(expect):
        raise Fail('verify', '맞춘 결과가 뜻과 다르다 — 쓰지 않았다')
    if nl == '\r\n' and M.bare_lf(new) > M.bare_lf(text):
        raise Fail('verify', '맞춘 결과에 줄끝이 섞였다 — 쓰지 않았다')
    return (M.BOM + new if bom else new), True, sets


def main():
    global M
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--template', required=True)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    try:
        M = load_merger()
        config = pathlib.Path(args.config).expanduser()
        if not config.is_file():
            raise Fail('config', f'설정 파일이 없다({config}) — 없는 자리에는 설치기가 틀을 그대로 쓴다')
        with open(config, encoding='utf-8', newline='') as f:
            current = f.read()
        with open(pathlib.Path(args.template), encoding='utf-8', newline='') as f:
            template = f.read()
        new, changed, sets = merge(current, template)
        for s in sets:
            print('SET=' + s)
        if changed and not args.check:
            print('BACKUP=' + str(M.backup_copy(config, BACKUP_SUFFIX)))
            M.write_atomic(config, new)
        print('CHANGED=' + ('1' if changed else '0'))
        return 0
    except Fail as exc:
        print(f'ERROR={exc.kind}:{exc.msg}')
        return 1
    except Exception as exc:   # 설치기와의 약속은 ERROR= 한 줄이다 — 트레이스백으로 죽으면 까닭이 안 읽힌다
        print('ERROR=' + type(exc).__name__ + ':' + str(exc))
        return 1


if __name__ == '__main__':
    sys.exit(main())
