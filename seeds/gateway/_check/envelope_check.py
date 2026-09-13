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
  ⑤ 한도는 변수로 열려 있다 — 시간 벽 · 이어받기 바퀴 · 봉투 상한 · 출력 상한
  ⑥ 기본 갈래에 모르는 이름을 적으면 **뜰 때 죽는다** — 오타가 조용히 딴 갈래로 안 간다

⚠ 들여올 때 굳는 값(④⑤⑥)은 이 프로세스에서 못 바꾼다 — 새 프로세스에 손잡이를 주고 되읽는다.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from _verdict import EXIT_MISMATCH, Unmeasured, edge, fails, passes, show

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from _plumb import (MODULE, PROVIDERS_MODULE, Missing, gateway,  # noqa: E402 — 배관은 선언이 고른다
                    get, providers)

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

print("\n[5] 한도는 변수로 열려 있다")
code = ("print(gateway.TIMEOUT_S, providers.MAX_CONTINUE, gateway.MAX_ENVELOPE_CHARS, "
        "gateway.WALL_MAX_TOKENS)")
rc, out, err = peek(code, **{f"{P}_TIMEOUT_S": "7", f"{P}_MAX_CONTINUE": "2",
                             f"{P}_MAX_ENVELOPE_CHARS": "123", f"{P}_WALL_MAX_TOKENS": "99"})
show("시간 벽 · 이어받기 바퀴 · 봉투 상한 · 출력 상한이 변수를 따른다", out, "7 2 123 99")

print("\n[6] 기본 갈래에 모르는 이름")
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
print(f"✅ 전부 통과 (판정 {len(passes())}건 — 봉투와 손잡이 계약)")
