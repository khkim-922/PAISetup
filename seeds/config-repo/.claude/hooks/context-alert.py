"""컨텍스트 알림 — 세션의 컨텍스트가 창의 33 % · 66 % 를 처음 넘을 때 한 번씩 모델 곁에 한 줄을 붙인다 (UserPromptSubmit 훅).
붙이기만 한다 — 막지도 압축하지도 않는다. 끊을지는 사람이 정한다.

**왜 있나.** 모델은 제 컨텍스트가 얼마나 찼는지 못 본다. 그래서 인계 · 압축을 묻는 일이 사람이 먼저 짚은 뒤에야 왔다.
얼마나 찼나는 판단과 무관하게 기계가 재고, 지금이 끊을 자리인가는 스킬 `session-handover` 가 가른다(claude-config #173).

**왜 UserPromptSubmit 인가.** 그 이벤트의 `additionalContext` 는 모델이 본다. 사람이 글을 보낼 때 한 번만 돌아 값이 싸고,
알림이 받을 사람 — 압축을 하는 사람 — 이 자리에 있는 순간에 든다. 서브에이전트 안에서는 안 돈다: 도구 이벤트는
서브에이전트 안에서도 돌면서 `transcript_path` 로 **부모의** 기록을 주므로, 거기 걸면 부모의 수치가 서브에이전트에 들어간다.

**재는 값** — 기록의 마지막 응답 `usage` 의 입력 + 캐시 읽기 + 캐시 만들기. 하네스의 상태줄이 `used_percentage` 를 재는
식과 같다. 서버 쪽 도구 고리면 마지막 `iterations` 칸이 그 창이다(하네스가 `context_tokens` 를 그렇게 정의한다).
  · 모델이 `<synthetic>` 인 줄은 건너뛴다 — 하네스가 지어 넣는 오류 자리 줄이라 값이 다 0 이다(압축 직후에 선다)
  · 그 응답보다 **뒤에** 압축 경계(`compact_boundary`)가 있으면 경계의 `postTokens` 를 쓴다 — 압축 뒤 첫 응답 전에는
    마지막 usage 가 압축 전 값이라, 그대로 쓰면 압축 직후에 무장이 안 풀린다

**창 크기** — 훅 입력에도 기록에도 창이 없고, 기록의 모델 이름에는 `[1m]` 이 안 붙는다. 그래서 모델 이름으로 가른다:
200k 는 닫힌 옛 판 묶음(`LEGACY_200K`)이고 그 밖의 Claude 모델은 1M 이다. Claude 이름이 아니면(게이트웨이 별칭) 하네스가
모르는 모델에 두는 값과 같은 200k 다. 잰 값이 그 창을 넘으면 `[1m]` 으로 연 옛 판이라 1M 으로 올린다.

**작은 창은 안 알린다** — 창이 `MIN_WINDOW` 보다 작으면(200k 대) 침묵한다. 그 창에서는 일 하나 하는 사이에 압축이 와,
알림이 할 일을 못 바꾸고 잔소리만 된다. 어댑터가 넘긴 창에도 같이 걸린다.

**한 번씩만** — 세션마다 이미 알린 가장 높은 문턱을 임시 폴더의 작은 파일에 둔다. 지금 넘은 문턱이 그보다 높으면 알리고,
낮으면(압축으로 내려갔다) 그 값으로 낮춰 위 문턱을 다시 무장한다.

**문턱마다 안내가 다르다** — 앞 문턱은 진행 · 남은 일을 정리해 보고하라는 것만 붙인다. 마지막 문턱은 끊는 길을 더한다:
사내 자리(`PAISETUP_SITE` 가 `NEW_SESSION_SITES` 에 든다)는 인계를 쓰고 새 세션으로 옮기기, 그 밖은 압축이다 — 사내는
새 세션이 압축보다 낫다(사용자 · #173). 자리 값은 설치기 손의 `user_value` 가 읽는 차례 그대로 읽는다(곁이나 한 칸 위의 `tool-homes.py`).

⚠ **재다 지면 아무 말 없이 0 으로 끝난다** — 매 프롬프트에 걸리는 훅이라 실패 줄은 매 턴 되풀이된다. 알림이 없는 것은
  이 훅이 없던 자리와 같다.
⚠ **덧말은 사실로 쓴다** — 명령조의 바깥 글은 프롬프트 주입 방어에 걸릴 수 있다(웹 다시 찾기와 같은 까닭).

부르는 자리 — 홈 `~/.claude/settings.json` 의 UserPromptSubmit. 앞에 셸 껍데기(`context-alert.sh` · 곁 파일)가 선다.
다른 도구의 어댑터는 이 파일을 모듈로 불러(`agy-hooks.py` 의 `load` 꼴) 제 자리에서 잰 토큰 수 · 창으로 `step` 만 부른다.
"""
import importlib.util
import json
import os
import re
import sys
import tempfile

THRESHOLDS = (33, 66)     # 알리는 문턱(%) — 사용자가 정한 값이다(#173) · 사람이 압축하는 45 · 75 보다 앞에서 알린다
WINDOW_1M = 1000000
WINDOW_200K = 200000
MIN_WINDOW = 500000   # 이보다 작은 창은 안 알린다 — 일 하나 하는 사이에 압축이 와 알림이 잔소리만 된다(사용자 · #173)
# 창이 200k 인 Claude 모델 — Claude Code 의 모델 표(2.1.300)에서 창이 200000 인 판이다. 그 뒤 판은 다 1M 이라 이 묶음은
#   더 안 는다. 이름은 1P · 날짜 붙은 꼴 · Bedrock(`us.anthropic.…`) · Vertex(`…@날짜`) 어느 꼴로 와도 `model_version` 이 푼다.
LEGACY_200K = {('opus', 4, 0), ('opus', 4, 1), ('opus', 4, 5), ('opus', 4, 6),
               ('sonnet', 4, 0), ('sonnet', 4, 5), ('sonnet', 4, 6), ('haiku', 4, 5)}
CLAUDE3 = 'claude-3-'     # Claude 3 계열은 다 200k 다
CLAUDE_MARK = 'claude-'   # 이것이 없는 이름은 하네스도 모르는 모델로 친다
# `claude-<계열>-<큰 판>[-<작은 판>]` — 작은 판은 한두 자리라 여덟 자리 날짜를 안 문다
MODEL_RE = re.compile(r'claude-(opus|sonnet|haiku|fable)-(\d+)(?:-(\d{1,2}))?(?!\d)')
SYNTHETIC = '<synthetic>'
TAIL_MAX_BYTES = 64 << 20   # 기록 꼬리를 거꾸로 읽는 한도 — 사람이 붙인 첨부 한 줄이 MB 단위다
TAIL_CHUNK = 1 << 20
SITE_VAR = 'PAISETUP_SITE'      # 설치기가 심는 자리 값
NEW_SESSION_SITES = {'inside'}  # 마지막 문턱에서 압축 대신 새 세션을 안내하는 자리
HOMES_HAND = 'tool-homes.py'    # 사용자 값을 읽는 차례의 진본(`user_value`) — 원본 저장소에서는 곁에, 홈 꾸러미에서는 한 칸 위에 선다
STATE_SUBDIR = 'claude-context-alert'   # 세션마다 알린 문턱을 둘 폴더 — 시스템 임시 폴더 밑
EVENT = 'UserPromptSubmit'


def tail_lines(path):
    """기록을 끝에서부터 한 줄씩(바이트) 낸다 — 앞은 안 읽는다. 읽은 양이 `TAIL_MAX_BYTES` 를 넘으면 멈춘다."""
    with open(path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        buf, taken = b'', 0
        while True:
            i = buf.rfind(b'\n')
            while i >= 0:
                line, buf = buf[i + 1:], buf[:i]
                if line.strip():
                    yield line
                i = buf.rfind(b'\n')
            if pos == 0:
                if buf.strip():
                    yield buf
                return
            if taken >= TAIL_MAX_BYTES:
                return
            n = min(TAIL_CHUNK, pos)
            pos -= n
            f.seek(pos)
            buf = f.read(n) + buf
            taken += n


def window_tokens(u):
    """usage 하나 → 그 응답이 본 컨텍스트 토큰 수."""
    its = u.get('iterations')
    if isinstance(its, list) and its and isinstance(its[-1], dict):
        u = its[-1]
    return sum(int(u.get(k) or 0) for k in ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'))


def current(path):
    """기록 → (지금 토큰 수, 모델 이름). 못 찾으면 (None, None).

    끝에서 거슬러 처음 만나는 것이 실 응답이면 그 usage, 압축 경계면 경계의 `postTokens` 다(머리말 「재는 값」).
    경계에는 모델이 없어 모델만 더 거슬러 찾는다."""
    post = None
    for raw in tail_lines(path):
        if b'"usage"' not in raw and b'compact_boundary' not in raw:
            continue
        try:
            o = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(o, dict):
            continue
        if post is None and o.get('type') == 'system' and o.get('subtype') == 'compact_boundary':
            post = int((o.get('compactMetadata') or {}).get('postTokens') or 0)
            continue
        m = o.get('message')
        if o.get('type') != 'assistant' or not isinstance(m, dict) or not isinstance(m.get('usage'), dict):
            continue
        if o.get('isSidechain') or o.get('isApiErrorMessage') or m.get('model') == SYNTHETIC:
            continue
        model = str(m.get('model') or '')
        return (post if post is not None else window_tokens(m['usage'])), model
    return post, None


def model_version(model):
    """모델 이름 → (계열, 큰 판, 작은 판) · 못 풀면 None."""
    hit = MODEL_RE.search(model)
    if not hit:
        return None
    return hit.group(1), int(hit.group(2)), int(hit.group(3) or 0)


def window_for(model, used):
    """모델 이름과 잰 값 → 창 크기(머리말 「창 크기」)."""
    if not model or CLAUDE_MARK not in model or CLAUDE3 in model or model_version(model) in LEGACY_200K:
        win = WINDOW_200K
    else:
        win = WINDOW_1M
    return WINDOW_1M if used > win else win


def state_path(sid):
    name = re.sub(r'[^A-Za-z0-9_-]', '', sid)
    return os.path.join(tempfile.gettempdir(), STATE_SUBDIR, name) if name else None


def read_armed(path):
    try:
        with open(path, encoding='utf-8') as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def write_armed(path, level):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(str(level))


# ── 문턱 · 한 번씩 · 다시 무장 — 도구와 무관하다. 다른 도구의 어댑터는 이 둘만 불러 쓴다 ──────────────
def step(session_id, used, window):
    """세션 열쇠 · 지금 토큰 수 · 창 크기 → 알릴 한 줄 · 없으면 None. 세션의 상태 파일을 고친다(머리말 「한 번씩만」).
    열쇠가 비면 상태를 못 두니 알리지 않는다."""
    sp = state_path(str(session_id or ''))
    if not sp or window < MIN_WINDOW:
        return None
    pct = used * 100 // window
    level = max([t for t in THRESHOLDS if pct >= t] or [0])
    armed = read_armed(sp)
    if level != armed:
        write_armed(sp, level)
    if level <= armed:
        return None
    return message(pct, used, window, level)


def site():
    """자리 값(소문자) · 못 읽으면 빈 글."""
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        hand = next(p for p in (os.path.join(here, HOMES_HAND), os.path.join(os.path.dirname(here), HOMES_HAND))
                    if os.path.isfile(p))
        spec = importlib.util.spec_from_file_location('tool_homes', hand)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.user_value(SITE_VAR).strip().lower()
    except Exception:  # noqa: BLE001 — 곁 손이 없거나 깨졌으면 프로세스 환경만 본다
        return os.environ.get(SITE_VAR, '').strip().lower()


def message(pct, used, window, level):
    head = ('컨텍스트 알림 — 이 세션의 컨텍스트가 창의 %d %%(%dk / %dk 토큰)에 닿아 문턱 %d %% 를 넘었다. '
            '사람에게 지금까지의 진행(끝난 것 · 도는 것)과 남은 일 · 계획 · 정할 것을 정리해 보고할 자리다.'
            % (pct, used // 1000, window // 1000, level))
    if level < THRESHOLDS[-1]:
        return head
    if site() in NEW_SESSION_SITES:
        cut = '인계(스킬 session-handover)를 써 두고 새 세션으로 옮겨 잇는 길도 함께 안내한다'
    else:
        cut = '압축(/compact)도 함께 안내한다'
    return '%s %s — 끊을지는 사람이 정한다.' % (head, cut)


# ── Claude 훅 ────────────────────────────────────────────────────────────────────
def alert(data):
    """Claude 훅 입력 → 알릴 한 줄 · 없으면 None."""
    if data.get('hook_event_name') != EVENT:
        return None
    tp = str(data.get('transcript_path') or '')
    if not tp or not os.path.isfile(tp):
        return None
    used, model = current(tp)
    if used is None:
        return None
    return step(data.get('session_id'), used, window_for(model, used))


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
