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

**망을 안 탄다.** 닿음 판정(`reachable`)은 이 검사의 축이 아니라 자식 안에서 참으로 갈아 끼운다.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from _verdict import EXIT_MISMATCH, fails, passes, report

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import gateway  # noqa: E402 — 접두어 하나만 읽는다

P = gateway.ENV_PREFIX

_PROBE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from app import gateway
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
    r = subprocess.run([sys.executable, "-c", _PROBE, str(ROOT)], cwd=ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=120)
    return r.returncode, r.stdout, r.stderr


def _load(code, out, err, label):
    if code != 0:
        print(f"[NG ] {label} — 자식이 죽었다 (exit {code})\n{err.strip()[-800:]}", file=sys.stderr)
        return None
    return json.loads(out.strip().splitlines()[-1])


def main():
    print(f"담장 스위치 검사 — 나무 {ROOT} · 접두어 {P}")

    code, out, err = _child()
    base = _load(code, out, err, "① 스위치 없이 올리기")
    if base is None:
        print("\n⚠ 기준 판을 못 올렸다 — 못 쟀다 (2)", file=sys.stderr)
        return 2
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
        print("\n⚠ 표에 바깥 담장의 갈래가 없다 — 닫힘을 잴 수 없다 (2)", file=sys.stderr)
        return 2
    code, out, err = _child(**{f"{P}_SITES": f" {posco} "})
    lock = _load(code, out, err, f"② {P}_SITES={posco}")
    if lock is None:
        return 1
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
    code, out, err = _child(**{f"{P}_SITES": out_site})
    report(f"④ `{out_site}` 만 열고 기본 갈래를 두면(회사 갈래) 뜰 때 죽고 {P}_PROVIDER 를 말한다",
           code != 0 and f"{P}_PROVIDER" in err,
           [f"exit {code} · stderr 꼬리: {err.strip()[-300:]}"])
    code, out, err = _child(**{f"{P}_SITES": out_site, f"{P}_PROVIDER": outside[0]})
    fixed = _load(code, out, err, f"④ {P}_SITES={out_site} {P}_PROVIDER={outside[0]}")
    report(f"④ 기본 갈래를 열린 담장 것({outside[0]})으로 두면 뜬다",
           fixed is not None and fixed["sites_allowed"] == [out_site],
           [f"실측 {fixed and fixed['sites_allowed']}"])

    report("⑤ 요청이 모르는 갈래 이름을 실어 오면 선다 — 기본으로 안 내린다",
           "error" in base["creds_typo"], [f"실측 {base['creds_typo']}"])
    code, out, err = _child(**{f"{P}_PROVIDER": "antropic"})
    report("⑤ 기본 갈래에 모르는 이름을 적으면 담장을 다 열어도 뜰 때 죽는다",
           code != 0 and "antropic" in err, [f"exit {code} · stderr 꼬리: {err.strip()[-300:]}"])

    bad = fails()
    if bad:
        print(f"\n❌ {len(bad)}건 실패 — {' · '.join(bad)}", file=sys.stderr)
        return EXIT_MISMATCH
    print(f"\n✅ 담장 스위치가 자격에서 선다 — 판정 {len(passes())}건 "
          f"(갈래 {len(all_ids)} · 담장 {len(base['sites_all'])} · 안 잰 것: 화면 목록 · 닿음 판정)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
