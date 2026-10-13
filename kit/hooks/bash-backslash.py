"""겹역슬래시 훅의 몸통 — Bash 도구 입력의 `command` 역슬래시를 다 두 배로 늘린 고친 입력을 낸다(접힘을 잰 판에서만).

부르는 꼴: 껍데기(`bash-backslash-deny.sh`)가 PreToolUse 입력 JSON 을 표준입력으로 넘긴다(그 명령에 겹역슬래시가 들 때만).
내는 것: 잰 판이면 `{"hookSpecificOutput":{"hookEventName":"PreToolUse","updatedInput":{…}}}` — 권한 판단은 안 적어 평소
  판단을 그대로 탄다. 모르는 판 · 판을 못 읽으면 막는 답(`permissionDecision: deny`). 겹역슬래시가 없으면 아무것도 안 낸다.
종료 값: 0 — 냈거나 낼 것이 없다. 입력을 못 읽으면 예외로 끝나고 껍데기가 막는 답으로 갈음한다.

왜 두 배인가 — 하네스가 역슬래시 n 개를 올림(n/2) 개로 접는다(짝마다 하나 · 남는 홑 것은 그대로). 2n 개를 보내면 n 개가 닿고,
홑 것 하나도 둘로 보내면 하나가 닿는다 — 다 두 배로 늘리면 명령이 쓴 그대로 닿는다.
왜 판을 보나 — 상류가 접힘을 고친 판에서 두 배를 보내면 그대로 닿아 결과만 조용히 틀린다(이 훅이 막으려던 꼴이다). 그래서 잰
판 이하만 고치고 새 판은 다시 잴 때까지 막는다. 판은 하네스가 기록 줄마다 적는 `"version"` 칸에서 읽는다.
"""
import json
import re
import sys

# 접힘을 잰 판 가운데 가장 새것 — 이 판 이하만 고친다. 판이 오르면 `scripts/probe-bash-collapse.sh` 로 다시 재고 올린다.
COLLAPSE_MEASURED_UPTO = (2, 1, 296)
TAIL_BYTES = 262144                     # 기록 끝에서 판을 찾을 창 — 줄마다 판이 들어 끝 몇 줄이면 된다
VERSION = re.compile(r'"version"\s*:\s*"(\d+)\.(\d+)\.(\d+)"')
BS = chr(92)
UNMEASURED_WHY = ('이 판(%s)의 Bash 도구가 겹역슬래시를 접는지 아직 안 쟀다 — 고쳐 넘기면 접힘이 고쳐진 판에서 두 배가 그대로 닿을 수 '
                  '있어 막았다. 역슬래시를 빼고 다시 짓거나(경로는 / · 정규식은 [.] 같은 문자 묶음), 데이터로 꼭 들어야 하면 Write 로 '
                  '파일에 써서 돌린다. 판을 재려면 scripts/probe-bash-collapse.sh 를 돌리고 몸통의 COLLAPSE_MEASURED_UPTO 를 올린다.')


def version_of(transcript):
    """기록 끝의 Claude Code 판 — (주, 부, 고침) · 못 읽으면 None."""
    try:
        with open(transcript, 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - TAIL_BYTES))
            tail = f.read().decode('utf-8', 'replace')
    except (OSError, TypeError, ValueError):
        return None
    found = VERSION.findall(tail)
    return tuple(int(x) for x in found[-1]) if found else None


def emit(out):
    sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', **out}}, ensure_ascii=False))


def main():
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get('tool_input') or {}
    cmd = tool_input.get('command')
    if not isinstance(cmd, str) or BS * 2 not in cmd:
        return 0
    ver = version_of(hook_input.get('transcript_path'))
    if ver is None or ver > COLLAPSE_MEASURED_UPTO:
        shown = '.'.join(map(str, ver)) if ver else '판을 못 읽음'
        emit({'permissionDecision': 'deny', 'permissionDecisionReason': UNMEASURED_WHY % shown})
        return 0
    # 입력 전체를 갈아 끼우는 칸이라 원래 입력을 펴고 command 만 바꾼다
    emit({'updatedInput': {**tool_input, 'command': cmd.replace(BS, BS * 2)}})
    return 0


if __name__ == '__main__':
    sys.exit(main())
