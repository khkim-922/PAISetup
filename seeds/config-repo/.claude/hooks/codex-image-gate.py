"""Codex 의 view_image 훅 입력을 Claude Read 꼴로 바꿔 `image-gate.py` 로 넘긴다.

Codex 가 넘기는 입력 꼴은 아직 실제 앱에서 못 쟀다(회사 PC 확인 목록 D2). 그래서 꼴을 넓게 받는다 — 도구 이름은
`view_image` 가 든 것이면 되고, `tool_input` 이 JSON 글로 와도 풀며, 경로 칸은 `path` · `file_path` · `image_path`
가운데 처음 것이고, 상대 경로는 입력의 `cwd` 기준이다.
**못 잰 자리는 말없이 넘기지 않는다** — 경로를 못 찾았거나 재는 자가 죽으면 막지 않고 「못 쟀다」를 곁에 붙인다
(`image-gate.py` 의 규율과 같다). 말없이 넘기면 그림 문이 선 줄 알고 큰 그림이 그대로 간다.
"""

import json
import os
import subprocess
import sys

PATH_KEYS = ('path', 'file_path', 'image_path')
GATE_TIMEOUT_SEC = 8   # 훅 한도(10초) 안에서 끝나게 — 넘기면 「못 쟀다」를 붙이고 비킨다


def note(text):
    sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'additionalContext': text}},
                                ensure_ascii=False))
    return 0


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0

    name = str(data.get('tool_name') or '').lower().replace('-', '_')
    if 'view_image' not in name and 'viewimage' not in name:
        return 0

    tool_input = data.get('tool_input')
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except ValueError:
            tool_input = {}
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    path = next((str(tool_input[k]) for k in PATH_KEYS if tool_input.get(k)), '')
    if not path:
        return note('그림 문 — 입력에서 그림 경로를 못 찾아 안 쟀다. 치수는 스스로 고른다')
    path = os.path.expanduser(path)
    if not os.path.isabs(path) and data.get('cwd'):
        path = os.path.join(str(data['cwd']), path)

    adapted = dict(data)
    adapted['hook_event_name'] = 'PreToolUse'
    adapted['tool_name'] = 'Read'
    adapted['tool_input'] = {'file_path': path}

    body = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'image-gate.py')
    try:
        proc = subprocess.run(
            [sys.executable, '-X', 'utf8', body],
            input=json.dumps(adapted, ensure_ascii=False),
            text=True,
            encoding='utf-8',
            capture_output=True,
            check=False,
            timeout=GATE_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return note(f'그림 문 — 재는 자를 못 돌려 안 쟀다({type(exc).__name__})')
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    elif proc.returncode != 0:
        tail = (proc.stderr or '').strip().splitlines()[-1:] or ['']
        return note(f'그림 문 — 재는 자가 죽어 안 쟀다(종료 {proc.returncode} · {tail[0][:160]})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
