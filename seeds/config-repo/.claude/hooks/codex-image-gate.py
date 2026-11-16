"""Codex 의 view_image 훅 입력을 Claude Read 꼴로 바꿔 `image-gate.py` 로 넘긴다.

Codex 가 넘기는 입력 꼴은 아직 실제 앱에서 못 쟀다(claude-config #125 의 D2). 그래서 꼴을 넓게 받는다 — 도구 이름은
`view_image` 가 든 것이면 되고, `tool_input` 이 JSON 글로 와도 풀며, 경로 칸은 `path` · `file_path` · `image_path`
가운데 처음 것이고, 상대 경로는 입력의 `cwd` 기준이다.
**못 잰 자리는 말없이 넘기지 않는다** — 경로를 못 찾았거나 재는 자가 죽으면 막지 않고 「못 쟀다」를 곁에 붙인다
(`image-gate.py` 의 규율과 같다). 말없이 넘기면 그림 문이 선 줄 알고 큰 그림이 그대로 간다.
**그림 문 몸통은 이 프로세스 안에서 돈다** — 파일로 실어 `main()` 을 부른다. 자식 해석기를 띄우면 그림 한 장에 해석기가
두 번 뜬다. 그래서 몸통을 따로 끊는 시한은 없다 — 훅을 거는 쪽의 한도가 이 프로세스째 끊는다.
"""

import contextlib
import importlib.util
import io
import json
import os
import sys

PATH_KEYS = ('path', 'file_path', 'image_path')
BODY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'image-gate.py')
DIED_WHY_CHARS = 160   # 죽은 까닭(예외 글)을 곁말에 싣는 길이


def note(text):
    sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'additionalContext': text}},
                                ensure_ascii=False))
    return 0


def gate(payload):
    """그림 문 몸통에 입력 하나를 먹인다 → (종료 값, 몸통이 stdout 에 낸 글). 몸통은 stdin 에서 읽고 stdout 에 쓰는 꼴이라 그
    둘만 이 한 번 갈아 끼우고 되돌린다. 몸통이 죽으면 그 예외(`SystemExit` 포함)가 그대로 오른다."""
    spec = importlib.util.spec_from_file_location('image_gate_body', BODY)
    body = importlib.util.module_from_spec(spec)
    out, stdin = io.StringIO(), sys.stdin
    sys.stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
    try:
        with contextlib.redirect_stdout(out):
            spec.loader.exec_module(body)
            rc = body.main()
    finally:
        sys.stdin = stdin
    return rc, out.getvalue()


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

    try:
        rc, said = gate(adapted)
    except (Exception, SystemExit) as exc:  # noqa: BLE001 — 몸통이 어떻게 죽든 막지 않고 못 쟀다고 댄다
        return note(f'그림 문 — 재는 자가 죽어 안 쟀다({type(exc).__name__}: {str(exc)[:DIED_WHY_CHARS]})')
    if said:
        sys.stdout.write(said)
    elif rc:
        return note(f'그림 문 — 재는 자가 죽어 안 쟀다(종료 {rc})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
