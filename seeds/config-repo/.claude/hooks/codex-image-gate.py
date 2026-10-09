"""Adapt Codex view_image hook input to the Claude Read shape used by image-gate.py."""

import json
import os
import subprocess
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0

    name = str(data.get('tool_name') or '')
    if name not in ('view_image', 'functions.view_image'):
        return 0

    tool_input = data.get('tool_input')
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    adapted = dict(data)
    adapted['hook_event_name'] = 'PreToolUse'
    adapted['tool_name'] = 'Read'
    adapted['tool_input'] = {'file_path': str(tool_input.get('path') or '')}

    body = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'image-gate.py')
    proc = subprocess.run(
        [sys.executable, '-X', 'utf8', body],
        input=json.dumps(adapted, ensure_ascii=False),
        text=True,
        encoding='utf-8',
        capture_output=True,
        check=False,
    )
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    return 0


if __name__ == '__main__':
    sys.exit(main())
