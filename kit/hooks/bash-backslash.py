"""겹역슬래시 훅의 몸통 — Bash 도구 입력의 `command` 역슬래시를 다 두 배로 늘린 고친 입력을 낸다.

부르는 꼴: 껍데기(`bash-backslash-deny.sh`)가 PreToolUse 입력 JSON 을 표준입력으로 넘긴다(윈도우에서 그 명령에 겹역슬래시가 들 때만).
내는 것: `{"hookSpecificOutput":{"hookEventName":"PreToolUse","updatedInput":{…}}}` — 권한 판단은 안 적어 평소 판단을 그대로
  탄다. 겹역슬래시가 없으면 아무것도 안 낸다.
종료 값: 0 — 냈거나 낼 것이 없다. 입력을 못 읽으면 예외로 끝나고 껍데기가 막는 답으로 갈음한다.

왜 두 배인가 — 하네스가 역슬래시 n 개를 올림(n/2) 개로 접는다(짝마다 하나 · 남는 홑 것은 그대로). 2n 개를 보내면 n 개가 닿고,
홑 것 하나도 둘로 보내면 하나가 닿는다 — 다 두 배로 늘리면 명령이 쓴 그대로 닿는다.
우회의 범위 — 윈도우 Bash 도구의 접힘(상류 anthropics/claude-code#88561). Claude Code 판은 안 본다(결정 0185). 상류가 접힘을
고친 판에서는 두 배가 그대로 닿아 결과만 틀리므로, 훅을 끈 판에서 겹역슬래시가 둘 그대로 닿으면(`scripts/README.md` 의 사람이
재는 한 줄) 이 훅을 통째로 걷는다.
"""
import json
import sys

BS = chr(92)


def emit(out):
    sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', **out}}, ensure_ascii=False))


def main():
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get('tool_input') or {}
    cmd = tool_input.get('command')
    if not isinstance(cmd, str) or BS * 2 not in cmd:
        return 0
    # 입력 전체를 갈아 끼우는 칸이라 원래 입력을 펴고 command 만 바꾼다
    emit({'updatedInput': {**tool_input, 'command': cmd.replace(BS, BS * 2)}})
    return 0


if __name__ == '__main__':
    sys.exit(main())
