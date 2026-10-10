"""Codex adapters for the Windows Bash backslash gate and PowerShell BOM hook."""

import argparse
import json
import os
import re
import sys


POWERSHELL_EXT = ('.ps1', '.psm1', '.psd1')


def emit_deny(reason):
    out = {'hookSpecificOutput': {'hookEventName': 'PreToolUse',
                                  'permissionDecision': 'deny',
                                  'permissionDecisionReason': reason}}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))


def bash_backslash(data, windows=os.name == 'nt'):
    tool_input = data.get('tool_input') if isinstance(data.get('tool_input'), dict) else {}
    command = str(tool_input.get('cmd') or tool_input.get('command') or '')
    shell = str(tool_input.get('shell') or '').lower()
    name = str(data.get('tool_name') or '').lower()
    # 단어 경계는 따옴표 없는 갈래에만 건다 — 따옴표로 감싼 경로(`"C:\Program Files\Git\bin\bash.exe"`)는 닫는 따옴표
    # 뒤가 빈칸이라 경계가 안 선다
    is_bash = name == 'bash' or 'bash' in shell or re.match(r'^\s*(?:["\'][^"\']*bash(?:\.exe)?["\']|\S*bash(?:\.exe)?\b)', command, re.I)
    if windows and is_bash and '\\\\' in command:
        emit_deny('Windows에서 Bash로 보낸 명령의 겹역슬래시는 셸에 닿기 전에 하나로 접힐 수 있다. '
                  '파일 내용은 apply_patch로 쓰고, 경로는 /로 적거나 역슬래시는 안전한 방식으로 다시 짓는다.')


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
    tool_input = data.get('tool_input') if isinstance(data.get('tool_input'), dict) else {}
    patch = str(tool_input.get('patch') or tool_input.get('input') or '')
    cwd = str(data.get('cwd') or os.getcwd())
    for raw in patch_paths(patch):
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
