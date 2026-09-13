"""CLI 갈래의 **파이프 배관** — 맞물림 없음 · 전량 전달 · 시계 · 받아 둔 몫 · 사람 말 사유 · 이음매 · 증거.

    python -X utf8 _check/cli_pipe_check.py

바깥으로 안 나간다 — 진짜 `claude` CLI 도 사내 게이트웨이도 안 부른다. 임시 자리에 **가짜
자식 프로세스**를 구워 세우고(`_fake_cli`), 그것이 실물과 같은 순서로 굴게 해서 배관만
잰다. 가짜가 안 서면 **부르기 전에 멈춘다** — 진짜로 안 넘어간다.

**이 시험이 지키는 계약 일곱**:
  ① 자식이 stdin 을 다 읽기 전에 로그를 흘려도 **맞물려 서지 않는다** — 쓰기 하나와
     읽기 둘이 동시에 흘러야 한다
  ② 큰 봉투가 **한 자도 안 빠지고** 건너간다 — 곁줄기로 갈랐다고 새면 안 된다
  ③ **시계가 있다** — 입 다문 자식은 `gateway.TIMEOUT_S` 에서 끊긴다
  ④ 벽에 걸려도 **받아 둔 몫은 산다** — 글자가 왔으면 그것을 돌려주고 **사유를 올린다**
  ⑤ 사유가 **사람 말로** 온다 — 벽에 걸린 것을 `-9 로 끝났다` 로 말하면 진단이 아니다
  ⑥ 시계가 재는 것은 **침묵**이다 — 생각(thinking)처럼 글자 없이 신호만 오는 구간은
     `TIMEOUT_S` 를 넘겨도 산다
  ⑦ 로그인 안 된 판은 **일반 실패와 갈라 선다**(`CliLoginRequired`) — 문 하나로 풀리는
     막힘이라 화면이 할 일이 다르다
  ⑧ 자식이 **스스로 이은 자리**(둘째 `message_start`)의 코드 펜스를 벗긴다 — 우리 봉합은
     이 안을 못 보므로 여기서 벗기지 않으면 펜스가 산출물 한복판에 앉는다(아뜰리에 #335)
  ⑨ 자식이 성내며 죽으면 **직전 스트림 꼬리가 파일로 남고** 사유가 그 좌표를 든다 —
     「무슨 일이 오갔나」는 그 꼬리에만 있다

⚠ **①이 이 파일이 선 까닭이다.** 한 줄기로 쓰던 판에서는 봉투(한글이면 UTF-8 로 수십만
  바이트)가 OS 파이프 버퍼(보통 64KB)를 넘는 순간, 부모는 stdin 을 다 못 쓴 채 막히고
  자식은 안 읽히는 stdout·stderr 에 막혀 **서로 상대를 기다렸다.** 오류도 안 나고 영영
  안 끝나 화면에는 그냥 「도는 중」으로 보인다. HTTP 갈래 셋은 `urlopen(timeout=…)` 이 이
  자리를 대신 지므로 **파이프인 이 갈래만 손으로 진다.**

⚠ **맞물림은 시계로 못 잰다** — 시계가 끊어 주면 「돌아왔다」가 되어 판정이 흐려진다.
  그래서 시계보다 **짧은 자**로 먼저 재고(①), 시계는 따로 잰다(③).
"""
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

from _verdict import EXIT_MISMATCH, edge, fails, passes, report, show

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import _fake_cli  # noqa: E402 — 가짜를 심는 자와 진짜로 안 넘어가게 하는 담
from _plumb import gateway, get, providers, put  # noqa: E402 — 배관은 선언이 고른다


TMP = Path(tempfile.mkdtemp(prefix="seed-clipipe-"))
# ⑨의 증거 파일 — 이 PC 의 기록 폴더를 안 더럽힌다.
# ⚠ **선언이 든 자리에 앉힌다**(`put`). 기록 자리를 배관이 아니라 설정 모듈이 드는 저장소가
#   있어, 배관에 직접 앉히면 갈아 끼운 줄 알고 **그 PC 의 진짜 기록 폴더**가 더럽혀진다.
put("LOGS_DIR", TMP / "logs")

# 시계를 실물(초 단위 수백)로 두면 이 검사가 그만큼 걸린다 — 자만 줄인다.
# ⚠ **자 셋의 크기 순서가 곧 판정이다.** 어긋나면 검사가 저 혼자 빨강을 낸다:
#   DEADLOCK_WAIT < TIMEOUT_S < WALL
#   · 맞물림을 재는 자가 시계보다 **짧아야** 「시계가 끊어 준 것」을 「돌아왔다」로 안 센다
#   · 기다리는 자가 시계보다 **길어야** 시계가 끊는 것을 「맞물림」으로 안 센다
DEADLOCK_WAIT = 3
gateway.TIMEOUT_S = 5
WALL = 15


# ---------- 가짜 자식 ----------
# 실물과 같은 순서로 군다: `--verbose` 로 띄운 자식은 stdin 을 다 읽기 **전에** 로그를
# 흘리고, 그 로그가 파이프 버퍼를 채우면 거기서 멈춘다 — 그 뒤로는 stdin 도 안 읽는다.
_EMIT = '''
import json, sys
def emit(o):
    sys.stdout.write(json.dumps(o, ensure_ascii=False) + "\\n"); sys.stdout.flush()
'''
FAKES = {
    # ①②용 — stderr 300KB 를 먼저 흘리고 그 뒤에 stdin 을 읽는다
    "loud": _EMIT + '''
sys.stderr.write("경고: 자식이 흘리는 로그\\n" * 12000); sys.stderr.flush()
data = sys.stdin.read()
emit({"type":"stream_event","event":{"type":"message_start",
      "message":{"usage":{"input_tokens":11,"output_tokens":0}}}})
emit({"type":"stream_event","event":{"type":"content_block_delta",
      "delta":{"text": "받은 바이트 %d" % len(data.encode("utf-8"))}}})
emit({"type":"stream_event","event":{"type":"message_delta",
      "delta":{"stop_reason":"end_turn"}}})
emit({"type":"result","stop_reason":"end_turn","is_error":False})
''',
    # ③용 — 입 다물고 버틴다
    "mute": _EMIT + '''
import time
sys.stdin.read(); time.sleep(600)
''',
    # ④용 — 한 마디만 내고 버틴다
    "half": _EMIT + '''
import time
sys.stdin.read()
emit({"type":"stream_event","event":{"type":"content_block_delta",
      "delta":{"text":"여기까지는 왔다"}}})
time.sleep(600)
''',
    # ⑤용 — 아무것도 안 내고 성내며 죽는다
    "angry": _EMIT + '''
sys.stdin.read()
sys.stderr.write("모델 이름을 못 찾겠다"); sys.stderr.flush()
sys.exit(3)
''',
    # ⑥용 — 글자 없이 생각 신호만 시계보다 길게 흘리고, 그제야 글자를 낸다.
    # 자 셋의 순서가 곧 판정이다: 신호 간격(1) < TIMEOUT_S(5) < 생각 총 시간(7) —
    # 침묵 시계면 살아서 돌아오고, 총 시간 시계면 5초에 죽는다.
    "think": _EMIT + '''
import time
sys.stdin.read()
for i in range(7):
    emit({"type":"system","subtype":"thinking_tokens",
          "estimated_tokens": (i + 1) * 50})
    time.sleep(1)
emit({"type":"stream_event","event":{"type":"content_block_delta",
      "delta":{"text":"생각 끝에 나온 글"}}})
emit({"type":"stream_event","event":{"type":"message_delta",
      "delta":{"stop_reason":"end_turn"}}})
emit({"type":"result","stop_reason":"end_turn","is_error":False})
''',
    # ⑧용 — 첫 메시지가 산문 한가운데서 상한에 잘리고 자식이 **스스로 둘째 메시지**를 연다.
    # 둘째는 실물(아뜰리에 #335)처럼 `\`\`\`markdown` 펜스를 다시 열어 시작하고 그 펜스로
    # 끝난다 — 첫 메시지 안의 진짜 코드 블록은 건드리면 안 된다.
    "seam": _EMIT + '''
sys.stdin.read()
def start():
    emit({"type":"stream_event","event":{"type":"message_start",
          "message":{"usage":{"input_tokens":11,"output_tokens":0}}}})
def text(t):
    emit({"type":"stream_event","event":{"type":"content_block_delta","delta":{"text":t}}})
start(); text("첫머리\\n```python\\nx = 1\\n```\\n"); text("그리고 ")
emit({"type":"stream_event","event":{"type":"message_delta","delta":{"stop_reason":"max_tokens"}}})
start(); text("```markdown\\n이어서 쓴다"); text("\\n```")
emit({"type":"stream_event","event":{"type":"message_delta","delta":{"stop_reason":"end_turn"}}})
emit({"type":"result","stop_reason":"end_turn","is_error":False})
''',
    # ⑦용 — CLI 가 로그인 안 됐을 때의 마지막 한 줄. **글자를 안 내고** 그 말만 낸다.
    "nologin": _EMIT + '''
sys.stdin.read()
emit({"type":"result","is_error":True,
      "result":"Not logged in. Please run /login"})
''',
}
# 심는 일은 `_fake_cli` 가 든다 — OS 마다 무엇을 어떤 꼴로 세우나(윈도우의 `.cmd` 겉옷 ·
# 그 본문이 ASCII 라야 하는 까닭)는 그 파일 머리말이 진본이다.
EXE = {name: _fake_cli.plant(TMP, name, body) for name, body in FAKES.items()}

C = gateway.creds(provider="claude-cli")
BIG = "가" * 60000            # 봉투 실측 폭 — UTF-8 로 180KB


def call(fake, layers=None, wait=WALL, on_usage=None, on_cut=None):
    """가짜 자식으로 `_cli_once` 를 부른다. `wait` 안에 안 돌아오면 ('맞물림', None).

    ⚠ 곁줄기로 돌린다 — 맞물리면 그 줄기는 영영 안 끝나므로 **daemon** 이라야 이 검사가
      제 발로 나갈 수 있다. `_cli_once` 안에서 쓰는 것과 같은 수법이다.
    """
    # `shutil.which` 는 경로 구분자가 든 이름을 그대로 되돌려준다 — 그래서 실행 파일
    # 이름만 갈아 끼우면 되고 표준 라이브러리를 손댈 일이 없다.
    gateway.CLI_EXE = EXE[fake]
    _fake_cli.guard(TMP)        # 가짜가 안 서면 진짜로 안 넘어가고 여기서 나간다
    box = {}
    # **봉투도 실물이 짓는 것을 쓴다** — 검사가 stdin 글자를 손으로 지으면 접는 규율
    # (`_cli_envelope`)이 깨져도 여기서는 안 걸린다.
    env = providers.envelope(layers if layers is not None else [BIG],
                             [{"role": "user", "content": "안녕"}], C)

    def go():
        try:
            box["got"] = providers._cli_once(env, C, None, on_usage, None, on_cut)
        except Exception as e:                       # noqa: BLE001 — 사유까지 판정한다
            box["err"] = e

    t = threading.Thread(target=go, daemon=True)
    t.start()
    t.join(wait)
    if t.is_alive():
        return "맞물림", (None, env)
    if "err" in box:
        return "예외", (box["err"], env)
    return "돌아옴", (box["got"], env)


print("[1] 자식이 로그를 먼저 흘려도 맞물려 서지 않는다")
kind, (got, env1) = call("loud", wait=DEADLOCK_WAIT)
show(f"큰 봉투(180KB) + stderr 300KB — {DEADLOCK_WAIT}초 안에", kind, "돌아옴")
show("작은 봉투 — 종전에도 돌던 자리",
     call("loud", layers=["안녕"], wait=DEADLOCK_WAIT)[0], "돌아옴")

print("\n[2] 봉투가 한 자도 안 빠지고 건너간다")
if kind == "돌아옴":
    # 보낸 것은 **실물이 지은 stdin 한 줄**이다 — 자식이 센 것과 견준다. 손으로 다시
    # 접으면 접는 규율이 바뀐 날 이 줄만 낡는다.
    sent = len((env1.payload + "\n").encode("utf-8"))
    saw = int(got[0].split()[-1])
    report("자식이 받은 바이트가 보낸 줄의 몸통과 맞는다", 0 < saw <= sent,
           [f"자식이 센 것 {saw} · 보낸 줄 {sent}"])
    show("접힌 봉투가 실제로 크다 — 파이프 버퍼를 넘겨야 ①이 뜻을 갖는다",
         saw > 64 * 1024, True)
    show("stop_reason 이 그대로 온다", got[1], "end_turn")
else:
    report("봉투 전달 — 앞이 맞물려 못 쟀다", False, ["앞에서 맞물려 못 쟀다"])

print("\n[2-b] 씀씀이가 HTTP 갈래와 **같은 어휘로** 온다")
seen_usage = []
call("loud", layers=["안녕"], on_usage=seen_usage.append)
show("입력 토큰이 한 어휘로 넘어온다",
     seen_usage[-1].get("total_input") if seen_usage else None, 11)

print(f"\n[3] 시계가 있다 — 입 다문 자식은 {gateway.TIMEOUT_S}초에 끊긴다")
kind, (err, _) = call("mute")
show("영영 안 끝나지 않는다", kind, "예외")
show("사유가 사람 말이다 — `-9 로 끝났다` 가 아니다",
     "초를 잠잠해" in str(err) if kind == "예외" else str(err), True)

print("\n[4] 벽에 걸려도 받아 둔 몫은 살고, **사유가 올라온다**")
cuts = []
kind, (got, _) = call("half", on_cut=cuts.append)
show("예외가 아니라 받은 글자를 돌려준다", kind, "돌아옴")
show("받아 둔 글자가 살아 있다", got[0] if kind == "돌아옴" else None, "여기까지는 왔다")
# **여기가 안 서면 「끊김」만 남고 무엇에 끊겼나가 증발한다** — HTTP 갈래는 같은 자리를
# `on_cut` 으로 올린다. 같은 일을 하는 갈래를 반대로 두지 않는다.
show("사유가 한 줄 올라온다 — 종전에는 셋 다 버려지던 자리다", len(cuts), 1)
show("  그 사유가 시간 벽을 이름 부른다",
     "초를 잠잠해" in cuts[0] if cuts else None, True)

print("\n[5] 자식이 성내며 죽으면 그 말이 사유에 실린다")
kind, (err, _) = call("angry")
show("예외로 끝난다", kind, "예외")
show("자식이 흘린 말이 사유에 실린다",
     "모델 이름을 못 찾겠다" in str(err) if kind == "예외" else str(err), True)
show("  종료 코드도 함께 실린다", "3 로 끝났다" in str(err) if kind == "예외" else "", True)

print("\n[6] 시계는 침묵을 잰다 — 생각 신호가 오는 동안은 안 끊긴다")
kind, (got, _) = call("think", layers=["안녕"])
show(f"생각 7초 > 시계 {gateway.TIMEOUT_S}초 — 그래도 돌아온다", kind, "돌아옴")
show("생각 끝의 글자가 산다", got[0] if kind == "돌아옴" else got, "생각 끝에 나온 글")

print("\n[7] 로그인 안 된 판은 일반 실패와 갈라 선다")
kind, (err, _) = call("nologin", layers=["안녕"])
show("예외로 끝난다", kind, "예외")
report("갈라 세운 예외다 — 서버가 이것으로 「문 하나로 풀리는 막힘」을 안다",
       isinstance(err, providers.CliLoginRequired),
       [f"실제 {type(err).__name__}: {err}"])
report("일반 실패와 **다른 종류**다 (음성 대조 — [5] 는 이 종류가 아니었다)",
       not isinstance(call("angry")[1][0], providers.CliLoginRequired))
show("사람 말이 실린다", "로그인" in str(err), True)

print("\n[8] 자식이 스스로 이은 자리의 펜스를 벗긴다 — 우리 봉합이 못 보는 이음매")
kind, (got, _) = call("seam", layers=["안녕"])
show("돌아온다", kind, "돌아옴")
joined = got[0] if kind == "돌아옴" else got
show("둘째 메시지의 머리·꼬리 펜스가 벗겨지고 첫 메시지 안의 코드 블록은 그대로다",
     joined, "첫머리\n```python\nx = 1\n```\n그리고 이어서 쓴다")
show("stop 은 마지막 메시지 것이다 — 잘린 첫 메시지의 max_tokens 가 남지 않는다",
     got[1] if kind == "돌아옴" else None, "end_turn")
# 음성 대조 — 이음매가 없는 판은 종전과 **바이트로 같다**(`_join_seams` 의 빈 갈래)
show("이음매 없는 판은 종전과 같다 (음성 대조)", providers._join_seams(["a", "b"], []), "ab")

print("\n[9] 자식이 마지막 줄로 오류를 말한 판은 직전 스트림이 파일로 남고 사유가 그 좌표를 든다")
# ⚠ 증거는 `result` 줄로 끝난 판에만 선다 — 성내며 죽는 판([5])은 그 줄 없이 죽어 이 자리를
#   안 지난다(저쪽도 같다). 그래서 검체는 로그인 안 된 판([7]과 같은 가짜)이다.
evidence = get("LOGS_DIR") / "_cli_error.log"
if evidence.exists():
    evidence.unlink()               # [7] 이 이미 남긴 것을 걷어야 이 판이 세운 것만 잰다
kind, (err, _) = call("nologin", layers=["안녕"])
show("사유가 증거 파일 좌표를 든다", "logs/_cli_error.log" in str(err), True)
show("그 파일이 이 판에서 섰다", evidence.exists(), True)
show("자식이 낸 마지막 줄이 그 안에 있다 — 「무슨 일이 오갔나」의 증거",
     "Not logged in" in evidence.read_text(encoding="utf-8") if evidence.exists() else None, True)

print("\n[10] 안 잰 것")
edge("실물 `claude` CLI 가 정말 이 순서로 구나 — 진짜를 부르면 그날의 구독을 태운다. "
     "여기는 **가짜로 배관만** 잰다")
# ⚠ **이 줄은 윈도우에서 스스로 걷힌다** — 거기서는 이 판이 곧 그 측정이다. 사람이 지우게
#   두면 다음에도 똑같이 남아, 이미 잰 것을 「안 쟀다」로 말한다.
if os.name != "nt":
    edge("가짜를 세우는 **윈도우 길**(`.cmd` 겉옷)은 이 OS 에서 안 탄다 — 회사 PC 몫이다")
edge("파이프 버퍼가 몇 바이트나 — OS·판마다 다르다. 여기는 「넘겨도 안 선다」만 잰다")
edge("`deadline`(예산)이 침묵보다 먼저 오는 갈래 — 자 둘 중 먼저 오는 쪽이 눕는 것은 "
     "코드로만 봤다. 여기 판정은 침묵 쪽 하나다")
edge("**로그인 판정**(`gateway._cli_logged_in`)은 여기서 안 잰다 — 저쪽은 `claude auth "
     "status` 를 따로 띄우는 자라 이 배관을 안 탄다")

shutil.rmtree(TMP, ignore_errors=True)
print()
bad = fails()
if bad:
    print(f"❌ {len(bad)}건 어긋남 — {', '.join(bad)}")
    sys.exit(EXIT_MISMATCH)
print(f"✅ 전부 통과 (판정 {len(passes())}건 — 파이프 배관 계약, 항목은 머리말이 든다)")
