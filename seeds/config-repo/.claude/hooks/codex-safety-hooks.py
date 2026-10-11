r"""Codex 안전 훅 둘 — Windows 에서 bash 로 넘기는 명령의 겹역슬래시를 막고, apply_patch 가 고친 PowerShell 파일에 BOM 을 찍는다.

    python -X utf8 codex-safety-hooks.py bash-backslash   < PreToolUse 입력   (matcher 셸 도구)
    python -X utf8 codex-safety-hooks.py utf8-bom         < PostToolUse 입력  (matcher apply_patch)

**입력 꼴.** Codex 는 셸 명령도 apply_patch 도 내용을 `tool_input.command` 글 하나로 넘긴다 — 셸 명령은 그 명령 글이고,
apply_patch 는 `*** Begin Patch` 로 여는 패치 글이다(Codex 문서 「Hooks」 <https://developers.openai.com/codex/hooks>:
"Bash and apply_patch use tool_input.command"). 다른 칸은 Codex 가 안 실어 읽지 않는다.

**bash 인지는 명령 글로 가른다.** Codex 는 어느 셸이 돌리든 셸 명령을 모두 `tool_name: "Bash"` 로 넘기고, Windows 에서
그 명령을 돌리는 기본 셸은 PowerShell 이다. PowerShell 은 역슬래시를 건드리지 않아 `Write-Output 'a\\b'` 가 쓴 그대로 닿는다.
겹역슬래시를 하나로 접는 것은 Git for Windows 의 bash · sh 가 받은 명령줄을 풀 때다 — `& "…/bash.exe" -c "printf '%s' 'a\\b'"`
는 `a\b` 를 찍는다. 그래서 명령 글의 머리 자리(글 머리 · 문장 가름 뒤 · PowerShell 부르기 연산자 `&` 뒤)에 bash · sh 가
섰을 때만 보고, 겹역슬래시도 그 이름 **뒤**에서만 찾는다 — 앞쪽은 PowerShell 이 쓴 대로 넘긴다. 이런 명령은 성공으로
끝나고 결과만 틀리므로 묻지 않고 막는다. 고칠 쪽은 명령을 지은 모델이라, 까닭을 돌려주면 다시 짓는다.
⚠ 못 보는 자리 — exec_command 의 `shell` 인자로 bash 를 고르면 그 이름이 훅 입력에 안 실려 명령 글만으로는 모른다.
   bash 를 다른 프로그램의 인자로 띄우는 꼴(`Start-Process` · `cmd /c` · `wsl`)도 머리 자리가 아니라 안 본다.

**BOM 보정.** Windows PowerShell 5.1 은 BOM 없는 스크립트를 시스템 ANSI 코드페이지로 읽어 한글이 깨진다. 패치 글의
`*** Add File:` · `*** Update File:` · `*** Move to:` 줄에서 경로를 집어, 상대 경로는 입력의 `cwd` 기준으로 풀고
PowerShell 파일이면 BOM 을 붙인다.
"""

import argparse
import json
import os
import re
import sys


POWERSHELL_EXT = ('.ps1', '.psm1', '.psd1')
# 받은 명령줄의 겹역슬래시를 접는 셸 — Git for Windows 의 bash · sh. 맨 이름 `bash` 는 PowerShell 에서 WSL 의 bash.exe 로
# 풀릴 수도 있지만 bash 로 넘기는 명령이라 함께 본다
BASH_PROGRAMS = ('bash', 'bash.exe', 'sh', 'sh.exe')
# 명령 머리 자리의 프로그램 이름 — 글 머리, 또는 문장을 가르는 글자(; | & 줄바꿈)나 묶음을 여는 글자(( {) 뒤.
# `&` 는 PowerShell 의 부르기 연산자이기도 해 `& "C:/…/bash.exe"` 도 여기 걸린다. 이름은 겹 · 홑따옴표로 감싸도 되고
# (`"C:/Program Files/Git/bin/bash.exe"`), 안 감쌌으면 빈칸이나 가름 글자에서 끝난다
PROGRAM_RE = re.compile(r'''(?:^|[;|&\n({])\s*(?:"([^"]*)"|'([^']*)'|([^\s;|&(){}<>"']+))''')


def emit_deny(reason):
    out = {'hookSpecificOutput': {'hookEventName': 'PreToolUse',
                                  'permissionDecision': 'deny',
                                  'permissionDecisionReason': reason}}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))


def command_text(data):
    tool_input = data.get('tool_input') if isinstance(data.get('tool_input'), dict) else {}
    return str(tool_input.get('command') or '')


def bash_tail(command):
    """명령 머리 자리에 bash · sh 가 서면 그 이름 뒤의 글 전부를, 없으면 None 을 낸다."""
    for m in PROGRAM_RE.finditer(command):
        program = next(g for g in m.groups() if g is not None)
        if re.split(r'[\\/]', program)[-1].lower() in BASH_PROGRAMS:
            return command[m.end():]
    return None


def bash_backslash(data, windows=os.name == 'nt'):
    tail = bash_tail(command_text(data))
    if windows and tail is not None and '\\\\' in tail:
        emit_deny('Windows에서 bash(Git Bash)로 넘기는 명령의 겹역슬래시는 bash에 닿기 전에 하나로 접힐 수 있다. '
                  '파일 내용은 apply_patch로 쓰고, 경로는 /로 적거나, bash를 거치지 않고 PowerShell로 바로 돌린다 — '
                  'PowerShell은 역슬래시를 쓴 대로 넘긴다.')


def patch_paths(text):
    for line in text.splitlines():
        # 이름을 바꾸며 고친 파일은 `*** Move to:` 줄의 새 이름에 있다
        m = re.match(r'^\*{3} (?:Add File|Update File|Move to):\s*(.+?)\s*$', line)
        if m:
            yield m.group(1)


def add_bom(path, cwd):
    """PowerShell 파일이면 UTF-8 BOM 을 앞에 붙인다 — 이미 있거나 다른 파일이면 그대로. agy 어댑터도 부른다."""
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    path = os.path.normpath(path)
    if not path.lower().endswith(POWERSHELL_EXT) or not os.path.isfile(path):
        return
    try:
        with open(path, 'rb') as f:
            body = f.read()
        if not body.startswith(b'\xef\xbb\xbf'):
            part = path + '.codex-bom-part'
            with open(part, 'wb') as f:
                f.write(b'\xef\xbb\xbf' + body)
            os.replace(part, path)
    except OSError:
        return


def utf8_bom(data):
    cwd = str(data.get('cwd') or os.getcwd())
    for raw in patch_paths(command_text(data)):
        add_bom(raw, cwd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=('bash-backslash', 'utf8-bom'))
    args = ap.parse_args()
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    if args.mode == 'bash-backslash':
        bash_backslash(data)
    else:
        utf8_bom(data)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
