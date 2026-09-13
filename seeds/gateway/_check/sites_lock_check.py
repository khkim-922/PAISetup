"""이 서버가 여는 담장(`{PREFIX}_SITES`) — 닫힌 갈래가 자격에서 빠지고, 비우면 종전 그대로인가.

    python -X utf8 _check/sites_lock_check.py

**왜 이 검사가 있나.** 회사에 띄운 서버에서 바깥 갈래(구글 직결 · 이 PC 구독)를 닫는
스위치가 담장 선언이다(atelier ADR 0253). 이것은 **회사 문서가 회사 밖으로 나가는 길을 막는
담**인데, 담은 두 자리에서 동시에 서야 담이다 — 목록에서 빠지는 것(편의)과 요청 자격에서
거절되는 것(경계). 목록만 빼고 자격은 받으면 옛 브라우저 저장분이 그대로 밖으로 나가고, 아무
검사도 안 운다.

재는 것 다섯 — 갈래마다 `gateway` 를 **자식 프로세스에서** 새로 올려 본다(환경변수가 적재
시점에 굳는 값이라 한 프로세스 안에서는 두 벌을 못 본다):
  ① **비우면 종전과 같다** — 여는 담장이 표의 담장 전부이고, 자격은 실어 온 그대로 선다
  ② **회사 담장만 열면** — 바깥 갈래를 실어 온 요청은 기본 갈래로 내려가되 키·모델이 함께
     비어 드라이런이 선다. 회사 갈래를 실어 온 요청은 그대로 선다
  ③ **모르는 담장 이름은 뜰 때 죽는다** — 오타가 「다 연다」로 떨어지면 닫은 줄 알고 연다
  ④ **기본 갈래가 닫힌 담장 것이면 뜰 때 죽는다** — 안 실어 온 요청마다 닫은 담장으로
     나가는 서버가 되기 때문이다. 기본 갈래를 열린 쪽으로 두면 뜬다
  ⑤ **모르는 갈래 이름은 담장과 무관하게 죽는다** — 요청이 실어 오면 `ValueError`, 기본
     갈래에 적으면 뜰 때. 형제 하나는 옛 환경과의 호환으로 기본 행에 내리는데, 그 내림이
     담장 검사 **앞**에 서 있던 날 오타가 닫은 담장으로 새었다. 새 프로젝트는 지킬 옛
     환경이 없어 세우는 쪽을 고른다

**기본 갈래 손잡이가 없는 앱에서는 셋이 뺀 자리로 내려간다.** 위 ④ 둘과 ⑤ 뒤엣것은 기본
갈래를 **환경변수로 여는** 앱을 전제한다 — 기본 갈래를 상수로 두고 그렇게 둔 까닭을 제 코드에
적어 둔 앱에서는 그 셋에 잴 것이 없다. 그 앱은 곁 선언 `_check/gateway.conf` 의
`[no_handle] PROVIDER` 에 까닭을 적고, 이 검사는 셋을 **근거를 대고 뺀 자리**로 내린다 —
이름과 까닭을 판정 자리에 찍고 종료 `0` 이다. 빨강도 「못 쟀다」도 아니다: 재려던 자리가 빈
것이 아니라 **잴 것이 애초에 없는** 자리다. 담의 축(①·②·③과 ⑤ 앞엣것 — 회사 담장만 열면
바깥 갈래가 목록에서도 자격에서도 빠지나)은 그 앱에서도 일곱 건 그대로 잰다.

⚠ **이 길이 여는 것은 손잡이가 없는 앱까지다 — 기본 갈래가 닫힌 앱은 아니다.** 손잡이도
  없고 상수 기본 갈래가 회사 담장 바깥이면 ② 부터 뜰 때 죽어 「못 쟀다」(2)로 나간다. 그
  자리는 선언이 못 여는 것이 맞다 — 그 서버는 회사 담장만 열면 **기본이 없는 서버**가 되므로,
  고칠 데가 검사가 아니라 앱이다.

⚠ **「없다」는 사람의 선언이라 이 검사가 실측으로 되뽑지 않는다.** 손잡이가 있는데 없다고
  적은 판은 여기서 안 걸린다 — 되뽑으려면 그 손잡이가 서나를 재야 하는데 그것이 곧 뺀 판정
  자체라, 뺀 자리를 뺐는지 재는 자가 되어 제자리를 돈다. 참인지는 적는 사람이 든다.

**망을 안 탄다.** 닿음 판정(`reachable`)은 이 검사의 축이 아니라 자식 안에서 참으로 갈아 끼운다.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from _verdict import (EXIT_MISMATCH, EXIT_UNMEASURED, Unmeasured, edge, fails, passes, report,
                      unmeasured)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from _plumb import MODULE, NO_HANDLE, Missing, get  # noqa: E402 — 접두어와 없는 손잡이

# ⚠ **접두어를 못 읽으면 못 쟀다(2)다.** 이 검사가 재는 스위치의 **이름 자체**가 접두어에서
#   나온다 — 지어내면 자식이 아무 스위치도 안 받은 채 돌고, 판정 다섯이 통째로 「비운 판」이
#   되어 담장이 안 서는데도 초록이 난다.
try:
    P = get("ENV_PREFIX")
except Missing as why:
    raise Unmeasured(f"⚠ 담장 스위치의 이름을 못 지었다 — {why}") from why

# 기본 갈래 손잡이를 이 앱이 여나 — 안 열면 선언이 까닭을 든다(머리말 「뺀 자리」 절).
# ⚠ **빈 것이 「손잡이 있음」이다.** 선언을 안 채운 형제에서 판정 열이 그대로 서야 하므로
#   기본값이 이쪽이어야 한다 — 반대로 두면 선언 없는 저장소가 조용히 일곱만 재고 초록이 난다.
NO_PROVIDER_WHY = NO_HANDLE.get("PROVIDER")
# ⚠ **까닭이 빈 선언은 「못 쟀다」(2)다.** 「근거를 대고」가 뺌의 조건이라 까닭이 곧 그 근거다
#   — 빈 채로 받으면 판정 셋이 「」 하나를 달고 사라지고, 안 받으면 적은 사람은 셋이 왜
#   그대로 빨강인지 모른다. 둘 다 조용하므로 그 자리에서 말하고 나간다.
if NO_PROVIDER_WHY is not None and not NO_PROVIDER_WHY.strip():
    raise Unmeasured("⚠ 선언 `[no_handle] PROVIDER` 에 까닭이 없다 — 뺄 근거가 곧 그 까닭이라 "
                     "빈 줄로는 못 뺀다. 이 앱이 왜 그 손잡이를 안 여나를 적거나, 손잡이가 "
                     "있으면 그 줄을 지운다")
CUT_OFF = []


def cut_off(name):
    """근거를 대고 뺀 자리 — **판정이 아니다.** 이름과 까닭을 판정 자리에 찍고 계수만 든다.

    ⚠ **`unmeasured()` 로 찍지 않는다.** 저것은 「재려다 못 쟀다」(종료 2)이고 이쪽은 「잴
      것이 없다」(종료 0)다. 한 표찰에 둘을 담으면 손잡이가 없는 앱은 영원히 2 로 나가,
      그 앱에서 **초록이 도달 불가능한 상태**가 된다 — 그러면 아무도 이 검사를 안 돌린다.
    ⚠ **빈 목록이 통과의 조건이 아니다** — 뺀 자리는 숨기는 것이 아니라 이름과 까닭을 달고
      서 있다가 **줄어들기를** 기다리는 목록이다(검사 씨앗 `README.md`).
    """
    CUT_OFF.append(name)
    edge(f"뺀 자리 — {name}\n         까닭: 선언 `[no_handle] PROVIDER` 가 "
         f"「{NO_PROVIDER_WHY}」 — 이 앱은 {P}_PROVIDER 를 안 읽는다")

# ⚠ **배관 이름을 자식에게 인자로 건넨다.** 자식은 `_check/` 가 경로에 없어 `_plumb` 을 못
#   문다 — 여기서 푼 이름을 그대로 넘겨 같은 모듈을 올리게 한다. 자식이 제 손으로
#   `app.gateway` 를 적으면 배관을 다르게 두는 저장소에서 **남의 모듈을 재고** 초록이 난다.
_PROBE = r"""
import importlib, json, sys
sys.path.insert(0, sys.argv[1])
gateway = importlib.import_module(sys.argv[2])
gateway.reachable = lambda *a, **k: True
def creds(p, t, m):
    try:
        c = gateway.creds(provider=p, token=t, model=m)
    except ValueError as e:
        return {"error": str(e)}
    return {"provider": c.provider, "token": c.token, "model": c.model, "dry_run": c.dry_run}
out = {
    "sites_all": list(gateway.SITES),
    "sites_allowed": list(gateway.SITES_ALLOWED),
    "gateway": {pid: row["site"] for pid, row in gateway._GATEWAY.items()},
    "default": gateway.DEFAULT_PROVIDER,
    "creds": {pid: creds(pid, "k-" + pid, "m-" + pid) for pid in gateway._GATEWAY},
    "creds_bare": creds(None, None, None),
    "creds_typo": creds("antropic", "k", None),
}
print(json.dumps(out))
"""


def _child(**env_over):
    env = {k: v for k, v in os.environ.items()
           if k not in (f"{P}_SITES", f"{P}_PROVIDER", f"{P}_DRY_RUN")}
    env.update(env_over)
    env["PYTHONUTF8"] = "1"
    r = subprocess.run([sys.executable, "-c", _PROBE, str(ROOT), MODULE], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=120)
    return r.returncode, r.stdout, r.stderr


def _load(code, out, err, label):
    if code != 0:
        # ⚠ **판정 표찰을 여기서 안 붙인다** — 같은 「자식이 죽었다」를 부르는 쪽이 저마다
        #   다르게 센다(①·②는 「못 쟀다」로, ④는 「안 떴다」라는 판정 실패로). `[NG ]` 를
        #   찍으면 한 사건이 표찰 둘을 져, 화면은 어긋남이라 하고 계수는 못 쟀다로 간다.
        #   이 줄이 드는 것은 판정이 아니라 **증거**(자식 stderr 꼬리)다.
        print(f"⚠ {label} — 자식이 죽었다 (exit {code})\n{err.strip()[-800:]}", file=sys.stderr)
        return None
    return json.loads(out.strip().splitlines()[-1])


def main():
    print(f"담장 스위치 검사 — 나무 {ROOT} · 배관 {MODULE} · 접두어 {P}")

    code, out, err = _child()
    base = _load(code, out, err, "① 스위치 없이 올리기")
    if base is None:
        unmeasured("① 스위치 없이 올리기", "기준 판을 못 올렸다 — 아래 판정이 다 이 판에 선다")
        return EXIT_UNMEASURED
    all_ids = list(base["gateway"])
    report("① 스위치를 비우면 여는 담장이 표의 담장 전부다",
           base["sites_allowed"] == base["sites_all"],
           [f"실측 {base['sites_allowed']} — 기대 {base['sites_all']}"])
    report("① 어느 갈래를 실어 와도 자격이 실어 온 그대로 선다",
           all(c.get("provider") == pid and c.get("token") == "k-" + pid and c.get("model") == "m-" + pid
               for pid, c in base["creds"].items()),
           [f"{pid}: {c}" for pid, c in base["creds"].items()])

    posco = base["sites_all"][0]
    inside = [pid for pid, s in base["gateway"].items() if s == posco]
    outside = [pid for pid in all_ids if pid not in inside]
    if not outside:
        unmeasured("② 담장 닫힘", "표에 바깥 담장의 갈래가 없다 — 닫힘을 잴 수 없다")
        return EXIT_UNMEASURED
    code, out, err = _child(**{f"{P}_SITES": f" {posco} "})
    lock = _load(code, out, err, f"② {P}_SITES={posco}")
    if lock is None:
        unmeasured(f"② {P}_SITES={posco}",
                   "담장을 닫은 판을 못 올렸다 — 아래 ② 판정 셋이 이 판에 선다")
        return EXIT_UNMEASURED
    report(f"② `{posco}` 만 열면 여는 담장이 그 하나다", lock["sites_allowed"] == [posco],
           [f"실측 {lock['sites_allowed']}"])
    report("② 회사 갈래를 실어 온 요청은 그대로 선다",
           all(lock["creds"][pid]["provider"] == pid and lock["creds"][pid]["token"] == "k-" + pid
               for pid in inside),
           [f"{pid}: {lock['creds'][pid]}" for pid in inside])
    report("② 바깥 갈래를 실어 온 요청은 기본 갈래로 내려가고 키·모델이 비어 드라이런이 선다",
           all(lock["creds"][pid]["provider"] == lock["default"]
               and lock["creds"][pid]["token"] == ""
               and lock["creds"][pid]["model"] == lock["creds_bare"]["model"]
               and lock["creds"][pid]["dry_run"] is True
               for pid in outside),
           [f"{pid}: {lock['creds'][pid]} — 기대 provider={lock['default']} token='' "
            f"model={lock['creds_bare']['model']} dry_run=True" for pid in outside])

    code, out, err = _child(**{f"{P}_SITES": f"{posco},nowhere"})
    report("③ 모르는 담장 이름을 적으면 뜰 때 죽고 그 이름을 말한다",
           code != 0 and "nowhere" in err and f"{P}_SITES" in err,
           [f"exit {code} · stderr 꼬리: {err.strip()[-300:]}"])

    out_site = base["gateway"][outside[0]]
    # ⚠ **뺀 자리에서는 자식도 안 올린다.** 손잡이를 안 읽는 앱에 그 변수를 실어 올리면
    #   화면에 「exit 1 · stderr 꼬리」가 남아, 판정을 안 냈는데 빨강처럼 읽힌다.
    if NO_PROVIDER_WHY:
        cut_off(f"④ `{out_site}` 만 열고 기본 갈래를 두면(회사 갈래) 뜰 때 죽고 "
                f"{P}_PROVIDER 를 말한다")
        cut_off(f"④ 기본 갈래를 열린 담장 것({outside[0]})으로 두면 뜬다")
    else:
        code, out, err = _child(**{f"{P}_SITES": out_site})
        report(f"④ `{out_site}` 만 열고 기본 갈래를 두면(회사 갈래) 뜰 때 죽고 {P}_PROVIDER 를 말한다",
               code != 0 and f"{P}_PROVIDER" in err,
               [f"exit {code} · stderr 꼬리: {err.strip()[-300:]}"])
        code, out, err = _child(**{f"{P}_SITES": out_site, f"{P}_PROVIDER": outside[0]})
        fixed = _load(code, out, err, f"④ {P}_SITES={out_site} {P}_PROVIDER={outside[0]}")
        report(f"④ 기본 갈래를 열린 담장 것({outside[0]})으로 두면 뜬다",
               fixed is not None and fixed["sites_allowed"] == [out_site],
               [f"실측 {fixed and fixed['sites_allowed']}"])

    # ⑤ 앞엣것은 손잡이와 무관하다 — 요청이 실어 오는 이름을 배관이 어떻게 받나라서,
    #    기본 갈래를 상수로 두는 앱에서도 그대로 선다.
    report("⑤ 요청이 모르는 갈래 이름을 실어 오면 선다 — 기본으로 안 내린다",
           "error" in base["creds_typo"], [f"실측 {base['creds_typo']}"])
    if NO_PROVIDER_WHY:
        cut_off("⑤ 기본 갈래에 모르는 이름을 적으면 담장을 다 열어도 뜰 때 죽는다")
    else:
        code, out, err = _child(**{f"{P}_PROVIDER": "antropic"})
        report("⑤ 기본 갈래에 모르는 이름을 적으면 담장을 다 열어도 뜰 때 죽는다",
               code != 0 and "antropic" in err, [f"exit {code} · stderr 꼬리: {err.strip()[-300:]}"])

    bad = fails()
    if bad:
        print(f"\n❌ {len(bad)}건 실패 — {' · '.join(bad)}", file=sys.stderr)
        return EXIT_MISMATCH
    # ⚠ **뺀 자리를 초록 줄이 함께 든다.** 안 적으면 「판정 7건」이 전부로 읽혀, 손잡이가
    #   없다고 선언한 앱에서 담장 난간 셋이 조용히 사라진다.
    cut = f" · 근거를 대고 뺀 자리 {len(CUT_OFF)}건" if CUT_OFF else ""
    why = (" · 뺀 까닭: 선언 `[no_handle] PROVIDER` — 이름과 까닭은 위 ⚠ 줄이 든다"
           if CUT_OFF else "")
    print(f"\n✅ 담장 스위치가 자격에서 선다 — 판정 {len(passes())}건{cut} "
          f"(갈래 {len(all_ids)} · 담장 {len(base['sites_all'])}{why} · "
          f"안 잰 것: 화면 목록 · 닿음 판정)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
