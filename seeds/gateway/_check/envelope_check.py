"""봉투와 손잡이 — 계약 셋의 봉투가 규격대로 서고, 변수로 연 손잡이가 실제로 봉투를 바꾸나.

    python -X utf8 _check/envelope_check.py

바깥으로 안 나간다 — 봉투를 **짓기**까지만 한다(`providers.envelope` 는 순수 함수다).

**이 시험이 지키는 계약 여섯**:
  ① anthropic — 캐시 경계가 층 사이마다 서고 예산(`SYSTEM_MARKS_BUDGET`)을 안 넘는다 ·
     수명이 기본이 아니면 `ttl` 이 함께 실린다 · 베타 낱말은 갈래 표의 칸이 든다
  ② gemini — 생각 손잡이(`GEMINI_THOUGHTS`)가 켜면 `thinkingConfig` 가 실리고 끄면 **아예
     안 실린다**(빈 표를 보내지 않는다)
  ③ openai — 출력 상한이 그 계약의 이름(`max_output_tokens`)으로 앉고 `store` 가 꺼져 있다
  ④ 캐시 수명은 **한 손잡이**다 — `5m` 이면 `ttl` 필드도 그 수명을 여는 베타 낱말도 함께
     안 나간다. 한쪽만 꺼지면 「1시간을 열어 달라」 말해 놓고 5분 봉투를 보내는 어긋난
     요청이 되고 게이트웨이는 안 운다
  ⑤ 한도는 변수로 열려 있다 — 시간 벽 · 이어받기 바퀴 · 봉투 상한 · 출력 상한.
     **손잡이마다 판정 하나**다: 넷을 한 줄로 묶으면 하나가 안 서도 넷이 함께 빨강이라
     어느 것이 없는지가 화면에서 안 갈린다
  ⑥ 기본 갈래에 모르는 이름을 적으면 **뜰 때 죽는다** — 오타가 조용히 딴 갈래로 안 간다

⚠ 들여올 때 굳는 값(④⑤⑥)은 이 프로세스에서 못 바꾼다 — 새 프로세스에 손잡이를 주고 되읽는다.

⚠ **그 앱이 안 여는 손잡이는 「뺀 자리」다.** 한도를 상수로 박고 기본 갈래를 환경변수로 안
  여는 앱이 있다 — 곁 선언 `_check/gateway.conf` 의 `[no_handle]` 이 그 까닭을 들면 ⑤의 그
  한도와 ⑥ 셋이 **근거를 대고 뺀 자리**로 내려간다: 이름과 까닭을 판정 자리에 찍고 종료 `0`
  이다. 빨강도 「못 쟀다」(2)도 아니다 — 재려던 자리가 빈 것이 아니라 **잴 것이 애초에 없다.**
  선언이 비면 **손잡이가 다 있다**가 기본이라 선언을 안 채운 저장소는 종전 그대로 다 재진다.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from _verdict import (EXIT_MISMATCH, EXIT_UNMEASURED, Unmeasured, edge, fails, passes, show,
                      unmeasured, unmeasureds)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from _plumb import (MODULE, NO_HANDLE, PROVIDERS_MODULE, Missing,  # noqa: E402 — 배관은 선언이 고른다
                    gateway, get, providers, slot)

# ⚠ **이 둘만 `get` 으로 문다** — 형제 실측에서 이름이 갈린 자리다. 접두어는 배관에 속성으로
#   없는 저장소가 둘이고(선언 `[values]` 가 값을 든다), 봉투 예산은 이름이 갈린 저장소가 있다
#   (`CACHE_MARK_CAP`). 나머지는 어느 저장소나 같은 이름으로 살아 모듈에서 그대로 나온다.
# ⚠ **못 찾으면 「못 쟀다」(2)다 — 빨강이 아니다.** 접두어를 지어내면 자식이 아무 손잡이도
#   안 받은 채 돌아 절 셋이 「비운 판」으로 초록이 되고, 예산을 지어내면 경계 판정이 그 앱의
#   예산이 아니라 씨앗의 수를 잰다.
try:
    P = get("ENV_PREFIX")
    MARKS_BUDGET = get("SYSTEM_MARKS_BUDGET")
except Missing as why:
    raise Unmeasured(f"⚠ 봉투를 재는 재료를 못 찾았다 — {why}") from why

ASK = [{"role": "user", "content": "묻는다"}]

# 절 [5] 가 재는 한도 넷 — `(이름, 얹어 볼 값, 사람 말)`. **손잡이마다 판정 하나**다.
# ⚠ 얹는 값은 그 앱의 기본값과 겹치지 않을 만큼만 낮다 — 겹치면 손잡이가 안 서는 판도
#   초록이 된다. 이 넷은 어느 앱에서도 기본값이 이 수가 아니다(형제 실측).
LIMITS = (("TIMEOUT_S", "7", "시간 벽"),
          ("MAX_CONTINUE", "2", "이어받기 바퀴"),
          ("MAX_ENVELOPE_CHARS", "123", "봉투 상한"),
          ("WALL_MAX_TOKENS", "99", "출력 상한"))
# 이 검사가 무는 손잡이 — 선언의 `[no_handle]` 에서 이 이름들만 본다. 남의 판정을 여는
# 줄까지 여기서 들면 이 검사가 안 재는 자리의 결함으로 나가떨어진다.
HANDLES = ("PROVIDER",) + tuple(name for name, _, _ in LIMITS)
# ⚠ **까닭이 빈 선언은 「못 쟀다」(2)다.** 「근거를 대고」가 뺌의 조건이라 까닭이 곧 그 근거다
#   — 빈 채로 받으면 판정이 「」 하나를 달고 사라지고, 말없이 안 받으면 적은 사람은 왜 그대로
#   빨강인지 모른다. 둘 다 조용하므로 그 자리에서 말하고 나간다.
_blank = [name for name in HANDLES if name in NO_HANDLE and not NO_HANDLE[name].strip()]
if _blank:
    raise Unmeasured(f"⚠ 선언 `[no_handle]` 에 까닭이 없는 줄이 있다 — {' · '.join(_blank)}. "
                     "뺄 근거가 곧 그 까닭이라 빈 줄로는 못 뺀다. 이 앱이 왜 그 손잡이를 안 "
                     "여나를 적거나, 손잡이가 있으면 그 줄을 지운다")
CUT_OFF = []


def cut_off(what, handle):
    """근거를 대고 뺀 자리 — **판정이 아니다.** 이름과 까닭을 판정 자리에 찍고 계수만 든다.

    ⚠ **`unmeasured()` 로 찍지 않는다.** 저것은 「재려다 못 쟀다」(종료 2)이고 이쪽은 「잴
      것이 없다」(종료 0)다. 한 표찰에 둘을 담으면 손잡이가 없는 앱은 영원히 2 로 나가,
      그 앱에서 **초록이 도달 불가능한 상태**가 된다 — 그러면 아무도 이 검사를 안 돌린다.
    ⚠ **빈 목록이 통과의 조건이 아니다** — 뺀 자리는 숨기는 것이 아니라 이름과 까닭을 달고
      서 있다가 **줄어들기를** 기다리는 목록이다(검사 씨앗 `README.md`).
    """
    CUT_OFF.append(what)
    edge(f"뺀 자리 — {what}\n         까닭: 선언 `[no_handle] {handle}` 가 "
         f"「{NO_HANDLE[handle]}」 — 이 앱은 {P}_{handle} 를 안 읽는다")


def creds_of(contract):
    """그 계약을 쓰는 첫 갈래의 자격 — 키를 실어 봉투가 실제 꼴로 서게."""
    for pid, row in gateway._GATEWAY.items():
        if row["contract"] == contract and not row.get("local"):
            return gateway.creds(provider=pid, token="k")
    raise Unmeasured(f"표에 {contract} 계약의 갈래가 없다")


# ⚠ **배관 이름을 자식에게 인자로 건넨다.** 자식은 `_check/` 가 경로에 없어 `_plumb` 을 못
#   문다 — 여기서 푼 이름을 그대로 넘겨 같은 모듈을 올리게 한다. 자식이 제 손으로
#   `app.gateway` 를 적으면 배관을 다르게 두는 저장소에서 **남의 모듈을 재고** 초록이 난다
#   (씨앗 `README.md` 「받는 길 ②」의 ⚠ · `sites_lock_check` 가 같은 꼴).
_PLUMB = ("import importlib, sys; "
          "gateway = importlib.import_module(sys.argv[1]); "
          "providers = importlib.import_module(sys.argv[2]); ")


def peek(code, **env_over):
    """새 프로세스에 손잡이를 얹어 값을 되읽는다 — 굳는 값은 이 길로만 잰다."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(P + "_")}
    env.update(env_over)
    env["PYTHONUTF8"] = "1"
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", _PLUMB + code,
                        MODULE, PROVIDERS_MODULE], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=120)
    return r.returncode, r.stdout.strip(), r.stderr


print("[1] anthropic — 경계 · 수명 · 베타 낱말")
c = creds_of(gateway.CONTRACT_ANTHROPIC)
for n, want in ((1, 1), (2, 1), (3, 2), (6, MARKS_BUDGET)):
    env = providers.envelope([f"층{i}" for i in range(n)], ASK, c)
    marks = [b for b in env.body["system"] if b.get("cache_control")]
    show(f"층 {n} — 경계 {want} (예산 {MARKS_BUDGET} 안)", len(marks), want)
env = providers.envelope(["층0", "층1"], ASK, c)
show("수명이 기본(5m)이 아니면 ttl 이 실린다",
     env.body["system"][0]["cache_control"].get("ttl"), gateway.CACHE_TTL)
show("베타 낱말은 갈래 표의 칸이 든다 — 손글자가 아니다",
     env.headers.get("anthropic-beta"), ",".join(c.betas))

print("\n[2] gemini — 생각 손잡이")
c = creds_of(gateway.CONTRACT_GEMINI)
env = providers.envelope(["층"], ASK, c)
show("켠 판 — thinkingConfig 가 실린다",
     env.body["generationConfig"].get("thinkingConfig"), {"includeThoughts": True})
show("출력 상한은 그 곁에 그대로 선다 — 다른 겹이다",
     "maxOutputTokens" in env.body["generationConfig"], True)
show("출력 상한 = 답 크기 + 생각 몫 — 생각이 maxOutputTokens 를 먹는다(실측 2026-09-09)",
     env.body["generationConfig"]["maxOutputTokens"], c.max_tokens + gateway.GEMINI_THINK_TOKENS)
big = providers.envelope(["층"], ASK, c._replace(max_tokens=10**6))
show("  모델 상한은 못 넘긴다", big.body["generationConfig"]["maxOutputTokens"], gateway.model_cap(c.model))
was = gateway.GEMINI_THOUGHTS
gateway.GEMINI_THOUGHTS = False
try:
    off = providers.envelope(["층"], ASK, c)
finally:
    gateway.GEMINI_THOUGHTS = was
show("끄면 그 낱말을 아예 안 싣는다 (양성 대조)",
     "thinkingConfig" in off.body["generationConfig"], False)

print("\n[3] openai — 상한 이름과 store")
c = creds_of(gateway.CONTRACT_OPENAI)
env = providers.envelope(["층"], ASK, c)
show("출력 상한이 그 계약의 이름으로 앉는다", env.cap_field, c.max_tokens_field)
show("  그 이름에 값이 실린다", env.body.get(env.cap_field), c.max_tokens)
show("저쪽에 대화를 안 남긴다", env.body.get("store"), False)

print("\n[4] 캐시 수명은 한 손잡이다")
code = ("import json; "
        "print(json.dumps([providers._cache_ctl().get('ttl'), "
        "[b for r in gateway._GATEWAY.values() for b in r.get('betas', ()) "
        "if b == gateway.CACHE_TTL_BETA]]))")
rc, out, err = peek(code, **{f"{P}_CACHE_TTL": "5m"})
ttl_off = json.loads(out) if rc == 0 else None
show("5m 이면 ttl 필드가 안 나간다", ttl_off and ttl_off[0], None)
show("  그 수명을 여는 낱말도 어느 갈래에도 안 실린다", ttl_off and ttl_off[1], [])
show("기본에서는 낱말이 실린다 (양성 대조)",
     any(gateway.CACHE_TTL_BETA in r.get("betas", ()) for r in gateway._GATEWAY.values()), True)

print("\n[5] 한도는 변수로 열려 있다 — 손잡이마다 판정 하나")
# ⚠ **넷을 한 줄로 묶지 않는다.** 묶으면 한 손잡이가 안 서도 넷이 통째로 빨강이라 **어느
#   것이 없는지가 화면에서 안 갈린다** — 형제 실측에서 출력 상한 하나가 나머지 셋까지
#   물들였다. 판정이 갈려야 그 앱이 고칠 자리도 갈린다.
# ⚠ **좌표는 선언이 푼다**(`slot`) — 같은 이름이 배관에 사는 저장소도 말하기에 사는
#   저장소도 있다. 자식은 `_check/` 가 경로에 없어 `_plumb` 을 못 무므로, 여기서 푼 좌표를
#   글자로 건네 제 손으로 그 모듈을 올리게 한다.
live = []
for name, want, label in LIMITS:
    if name in NO_HANDLE:
        cut_off(f"{label} — {P}_{name} 가 값을 바꾼다", name)
        continue
    try:
        mod, attr = slot(name)
        get(name)                    # 그 자리에 실제로 있나 — 없으면 `Missing` 이 까닭을 든다
    except Missing as why:
        unmeasured(f"{label}({P}_{name})", str(why))
        continue
    live.append((name, mod.__name__, attr, want, label))
if live:
    code = ("import importlib, json; "
            "print(json.dumps({n: str(getattr(importlib.import_module(m), a)) "
            "for n, m, a in " + repr([row[:3] for row in live]) + "}))")
    rc, out, err = peek(code, **{f"{P}_{name}": want for name, _, _, want, _ in live})
    if rc == 0:
        got = json.loads(out)
        for name, _, _, want, label in live:
            show(f"{label} — {P}_{name} 가 값을 바꾼다", got.get(name), want)
    else:
        # 자식이 통째로 졌으면 **넷 다 안 잰 것**이다 — 어긋났다고 말하면 배관이 성한데도
        # 빨강이 나간다. 까닭은 자식의 stderr 가 든다.
        for name, _, _, _, label in live:
            unmeasured(f"{label}({P}_{name})", f"값을 되읽는 자식이 졌다 — {err.strip()[-200:]}")

print("\n[6] 기본 갈래에 모르는 이름")
if "PROVIDER" in NO_HANDLE:
    # ⚠ **뺀 자리에서는 자식도 안 올린다.** 손잡이를 안 읽는 앱에 그 변수를 실어 올리면
    #   화면에 「exit 1」이 남아, 판정을 안 냈는데 빨강처럼 읽힌다.
    cut_off("뜰 때 죽는다", "PROVIDER")
    cut_off("  그 이름과 손잡이 이름을 말한다", "PROVIDER")
    cut_off("아는 이름이면 그것이 기본이 된다 (양성 대조)", "PROVIDER")
else:
    # 배관을 무는 것만으로 죽는다 — 자식의 머리말(`_PLUMB`)이 그 임포트다.
    rc, out, err = peek("pass", **{f"{P}_PROVIDER": "antropic"})
    show("뜰 때 죽는다", rc != 0, True)
    show("  그 이름과 손잡이 이름을 말한다", "antropic" in err and f"{P}_PROVIDER" in err, True)
    rc, out, err = peek("print(gateway.DEFAULT_PROVIDER)",
                        **{f"{P}_PROVIDER": list(gateway._GATEWAY)[-1]})
    show("아는 이름이면 그것이 기본이 된다 (양성 대조)", out, list(gateway._GATEWAY)[-1])

print("\n[7] 안 잰 것")
edge("게이트웨이가 이 봉투를 실제로 받나 — 실호출 프로브 몫이다. 여기는 **꼴**만 잰다")
edge("환산비(자/토큰)와 층 셋 이상 봉투의 캐시 적중 — 양쪽 앱 다 실측이 없다(곁말 참조)")

print()
bad = fails()
if bad:
    print(f"❌ {len(bad)}건 어긋남 — {', '.join(bad)}")
    sys.exit(EXIT_MISMATCH)
# ⚠ **뺀 자리와 못 잰 자리를 초록 줄이 함께 든다.** 안 적으면 「판정 몇 건」이 전부로 읽혀,
#   손잡이가 없다고 선언한 앱에서 한도와 기본 갈래 난간이 조용히 사라진다.
cut = (f" · 근거를 대고 뺀 자리 {len(CUT_OFF)}건(까닭은 위 ⚠ 줄이 든다)" if CUT_OFF else "")
if unmeasureds():
    print(f"판정 {len(passes())}건 초록{cut} · 못 잰 자리 {len(unmeasureds())} — 초록이 아니다")
    sys.exit(EXIT_UNMEASURED)
print(f"✅ 전부 통과 (판정 {len(passes())}건{cut} — 봉투와 손잡이 계약)")
