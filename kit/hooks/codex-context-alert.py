"""Codex 컨텍스트 알림 — Codex 세션 기록에서 잰 사용량 · 창으로 `context-alert.py` 의 판정을 불러 쓴다 (UserPromptSubmit 훅).

**왜 어댑터인가.** 문턱 · 한 번씩 · 다시 무장은 몸통 하나가 든다(`step`) — 같은 판정을 두 벌 두면 한쪽만 낡는다. 여기서는
Codex 의 입력에서 사용량과 창을 재고, 알릴 한 줄을 Codex 의 출력 꼴에 싣기만 한다(claude-config #173).

**재는 값** — 훅 입력의 `transcript_path` 가 세션 기록(`rollout-*.jsonl`)이다. 그 기록의 `event_msg` · `token_count` 줄 가운데
`info` 가 null 이 아닌 마지막 줄에서
  · 사용량 — `info.last_token_usage.input_tokens`. 마지막 모델 부르기가 본 입력이다. 캐시 읽은 몫(`cached_input_tokens`)은
    이 값 **안에** 든다 — 더하면 겹쳐 센다. `total_token_usage` 는 세션 누적이라 창과 견줄 값이 아니다
  · 창 — 같은 줄의 `info.model_context_window`. Codex 가 모델의 창에서 실효 몫만 실어 낸 값이라 그대로 넘긴다 — 창이 작아
    알리지 않는 판정도 몸통이 든다
  압축 뒤 값은 안 쟀다 — 다음 응답의 `token_count` 가 내려오면 몸통이 다시 무장한다.
기록 꼬리를 거꾸로 읽는 손은 몸통의 `tail_lines` 를 불러 쓴다.

**왜 UserPromptSubmit 인가.** 그 이벤트의 `hookSpecificOutput.additionalContext` 가 모델 곁에 붙는다(Codex 문서) · 사람이 글을
보낼 때 한 번 돈다 — 몸통이 Claude 에서 그 이벤트를 고른 까닭과 같다.

⚠ **재다 지면 아무 말 없이 0 으로 끝난다** — 매 프롬프트에 걸리는 훅이라 실패 줄은 매 턴 되풀이된다(몸통과 같은 규율).

부르는 자리 — `~/.codex/config.toml` 의 `[hooks]` UserPromptSubmit(예시 `codex-hooks.example.toml` · 병합기
`codex-hook-install.py` · 신뢰는 `codex-hook-trust.py`). 몸통은 이 파일 곁에 같이 실린다.
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BODY_FILE = 'context-alert.py'
EVENT = 'UserPromptSubmit'
TOKEN_COUNT = 'token_count'


def load_body():
    """곁의 몸통을 모듈로 부른다 — 이름에 `-` 가 들어 import 문으로는 못 부른다."""
    spec = importlib.util.spec_from_file_location('context_alert', HERE / BODY_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def current(ca, path):
    """세션 기록 → (사용량, 창) · 못 찾으면 None. 끝에서 거슬러 처음 만나는, `info` 가 선 `token_count` 줄이다."""
    for raw in ca.tail_lines(path):
        if TOKEN_COUNT.encode() not in raw:
            continue
        try:
            o = json.loads(raw)
        except ValueError:
            continue
        p = o.get('payload') if isinstance(o, dict) else None
        if o.get('type') != 'event_msg' or not isinstance(p, dict) or p.get('type') != TOKEN_COUNT:
            continue
        info = p.get('info')
        if not isinstance(info, dict):
            continue
        last = info.get('last_token_usage')
        used = last.get('input_tokens') if isinstance(last, dict) else None
        window = info.get('model_context_window')
        if isinstance(used, int) and isinstance(window, int):
            return used, window
        return None
    return None


def alert(data):
    """Codex 훅 입력 → 알릴 한 줄 · 없으면 None."""
    if data.get('hook_event_name') != EVENT:
        return None
    tp = os.path.expanduser(str(data.get('transcript_path') or ''))
    if not tp or not os.path.isfile(tp):
        return None
    ca = load_body()
    got = current(ca, tp)
    if got is None:
        return None
    return ca.step(data.get('session_id'), *got)


def main():
    try:
        data = json.load(sys.stdin)
        line = alert(data) if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001 — 재다 지면 조용히 끝난다(머리말 ⚠)
        return 0
    if line:
        sys.stdout.write(json.dumps({'hookSpecificOutput': {'hookEventName': EVENT, 'additionalContext': line}},
                                    ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
