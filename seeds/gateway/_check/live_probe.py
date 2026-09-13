"""사내 실호출 프로브 — 씨앗이 「안 쟀다」로 박아 둔 자리를 잰다. 값을 치른다(사내 키 · 토큰).

    python -X utf8 _check/live_probe.py ratio [글 파일] [--contract anthropic|openai|gemini]
    python -X utf8 _check/live_probe.py cache-layers [--provider anthropic]
    python -X utf8 _check/live_probe.py thoughts [--provider gemini-posco]
    python -X utf8 _check/live_probe.py all [글 파일]

글 파일을 안 주면 이 저장소의 `agents/lean.md`(한국어 산문 · 한 앱의 system 층 진본)를 검체로
쓴다 — 프로브 자체를 시험할 때는 그것으로 족하다. 제 봉투의 결(HTML 섞임 등)로 재려면 파일을 준다.

재는 것 셋 — 씨앗 곁말의 「안 쟀다」와 하나씩 짝이다:
  ① **환산비**(자/토큰) — 준 글 파일을 system 층 하나로 실어 보내고 저쪽이 센 입력 토큰으로
     나눈다. 봉투 상한(`MAX_ENVELOPE_CHARS`)은 이 비로 벽에서 되짚으므로 **제 봉투의 결로**
     잰 값이 있어야 한다. 계약마다 토크나이저가 달라 셋 다 잰다 — 가장 낮은 벽은 GPT 다
  ② **층 셋 이상의 캐시 적중** — system 층 셋(각각 계약의 캐시 최소 길이를 넘는 글)을 같은
     봉투로 두 번 보낸다. 첫 판은 `cache_write`, 둘째 판은 `cache_read` 가 **첫 층과 둘째 층을
     합친 몫**이면 둘째 고정 층도 캐시에 든 것이다. 첫 층 몫만이면 둘째 층은 캐시 밖이다
  ③ **생각 조각** — gemini 갈래에 생각을 흘려 달라고 요청한 판에서 씀씀이에 `thinking_tokens`
     칸이 서나, 첫 조각이 몇 초에 오나. 앞단 무응답 자(300초)를 되돌리는 박동이 실물에서 서나

**판정을 안 낸다 — 숫자를 찍고 그 뜻을 한 줄 단다.** 결과는 `_check/log/live-probe.log` 에
쌓인다(날짜 · 나무 지문 · 숫자) — 그 줄을 씨앗 곁말의 「안 쟀다」 자리에 옮겨 적는 것은 사람이다.

⚠ 키는 갈래 표의 키 묶음이 든 환경변수를 읽는다(배관의 `env_token` — 이름이 갈리는 자리라
  선언이 좌표를 든다). 없으면 「못 쟀다」로 나간다 — 초록이 아니다. `--key` 로 줄 수도 있다.
⚠ ②는 캐시를 **쓴다** — 1시간 수명의 캐시 쓰기 비용이 든다. 세 번 이상 돌릴 일이 아니다.
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from _plumb import Missing, gateway, get, providers  # noqa: E402 — 배관은 선언이 고른다
from _verdict import EXIT_UNMEASURED, Unmeasured  # noqa: E402

LOG = ROOT / "_check" / "log" / "live-probe.log"
# 기본 검체 — 없다. 씨앗은 복사해 나가는 밑판이라 「이 저장소의 어느 파일」을 가리킬 수 없다
# (옛 판은 claude-config `agents/lean.md` 를 가리켰고, 복사된 뒤엔 뿌리 밖의 없는 자리였다 — #25).
# 검체는 인자로 받는다 — 한국어 산문 한 벌이면 헬퍼 결에 가깝고, 제 봉투의 결이면 제 값이다.
DEFAULT_SPECIMEN = None
ASK = "배관 측정 중이다. 「확인」 한 낱말만 답해라."
# ②의 층 하나 크기 — 계약의 캐시 최소 길이(anthropic 1,024토큰 · 일부 모델 2,048)를 어느
# 환산비에서도 넘게. 자/토큰 2.1 로 잡아도 1,900토큰이다.
LAYER_CHARS = 4000


def _tree():
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "?"


def _log(line):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')} tree={_tree()} {line}\n")
    print(f"  → {LOG.relative_to(ROOT)}")


def _creds(provider, key, **kw):
    row = gateway._GATEWAY.get(provider)
    if row is None:
        raise Unmeasured(f"[안 잼] 모르는 갈래다 — {provider} (있는 것: {', '.join(gateway._GATEWAY)})")
    if row.get("local"):
        raise Unmeasured(f"[안 잼] {provider} 는 로컬 CLI 갈래라 이 프로브 밖이다")
    # ⚠ **키를 읽는 손은 이름이 갈린다** — 밑줄을 붙여 두는 저장소가 있어(`_env_token`)
    #   선언이 좌표를 든다. `--key` 를 준 판은 애초에 안 부르므로, 그 손이 없는 저장소도
    #   키를 손으로 주면 그대로 돈다.
    try:
        token = key or get("env_token")(row["key_group"])
    except Missing as why:
        raise Unmeasured(f"[안 잼] 키를 읽는 손을 못 찾았다 — {why}") from why
    if not token:
        names = gateway._KEY_ENV.get(row["key_group"]) or ()
        raise Unmeasured("[안 잼] 키가 없다 — " + (
            f"`--key` 로 주거나 환경변수 {' · '.join(names)} 를 둔다" if names else
            f"`--key` 로 준다. `{row['key_group']}` 묶음은 환경변수를 안 읽는다"))
    return gateway.creds(provider=provider, token=token, **kw)


def _first_of(contract):
    for pid, row in gateway._GATEWAY.items():
        if row["contract"] == contract and not row.get("local"):
            return pid
    raise Unmeasured(f"[안 잼] 표에 {contract} 계약의 갈래가 없다")


def _call(c, system, ask):
    """한 바퀴 — (글자, stop, 마지막 씀씀이, 첫 조각 초, 총 초, 생각 신호들)."""
    used, thinks, t0 = [], [], time.monotonic()
    first = [None]

    def on_text(s):
        if first[0] is None:
            first[0] = round(time.monotonic() - t0, 1)

    try:
        text, stop = providers.stream_once(system, [{"role": "user", "content": ask}],
                                           on_text=on_text, creds=c, on_usage=used.append,
                                           on_think=thinks.append)
    except RuntimeError as exc:
        print(f"[거절] {exc}")
        raise SystemExit(EXIT_UNMEASURED) from exc
    return text, stop, (used[-1] if used else None), first[0], round(time.monotonic() - t0, 1), thinks


# ---------- ① 환산비 ----------
def ratio(path, contracts, key):
    if not path:
        raise Unmeasured("[안 잼] 검체 파일을 안 줬다 — `live_probe.py ratio <글 파일>`. 씨앗은 기본 검체를 안 든다")
    path = Path(path)
    if not path.is_file():
        raise Unmeasured(f"[안 잼] 검체 파일이 없다 — {path}")
    text = path.read_text(encoding="utf-8")
    chars = len(text) + len(ASK)
    print(f"[①] 환산비 — 검체 {path} · {len(text):,}자")
    for contract in contracts:
        pid = _first_of(contract)
        c = _creds(pid, key, max_tokens=16)
        _, stop, u, _, secs, _ = _call(c, [text], ASK)
        if not u:
            print(f"  {pid:14s} 씀씀이가 안 왔다 — 게이트웨이가 안 실었다. 못 쟀다")
            continue
        total = u["total_input"]
        r = round(chars / total, 2) if total else None
        print(f"  {pid:14s} {c.model} · 입력 {total:,}토큰 · {chars:,}자 → **{r} 자/토큰** · {secs}초")
        _log(f"ratio provider={pid} model={c.model} chars={chars} total_input={total} ratio={r}")
    print("  뜻 — 이 비가 낮을수록 같은 글자가 더 많은 토큰이다. `MAX_ENVELOPE_CHARS` 는 벽(가장 낮은")
    print("       모델 입력 한도)에 **가장 낮은 비**를 곱해 되짚는다. 씨앗은 1.0 을 난간으로 둔다.")


# ---------- ② 층 셋의 캐시 ----------
def cache_layers(provider, key):
    pid = provider or _first_of(gateway.CONTRACT_ANTHROPIC)
    c = _creds(pid, key, max_tokens=16)
    if c.contract != gateway.CONTRACT_ANTHROPIC:
        raise Unmeasured(f"[안 잼] {pid} 는 anthropic 계약이 아니다 — 표를 우리가 다는 계약만 잰다")
    # 층마다 글이 달라야 한다 — 같으면 둘째 층이 첫 층으로 오인된다. 번호를 박아 가른다.
    layers = [(f"[층 {i}] 이 층은 캐시 적중을 재는 채움 글이다. " * 200)[:LAYER_CHARS] for i in range(3)]
    # ⚠ **봉투 예산은 이름이 갈린다** — 이 절에서만 드므로 여기서 문다. 위에 올려 두면
    #   그 이름이 없는 저장소에서 ①③까지 같이 못 쟀다로 떨어진다.
    try:
        budget = get("SYSTEM_MARKS_BUDGET")
    except Missing as why:
        raise Unmeasured(f"[안 잼] 봉투 예산을 못 찾았다 — {why}") from why
    print(f"[②] 층 셋의 캐시 — {pid} · {c.model} · 층마다 {LAYER_CHARS:,}자 · 경계 예산 "
          f"{budget}")
    env = providers.envelope(layers, [{"role": "user", "content": ASK}], c)
    marks = [i for i, b in enumerate(env.body["system"]) if b.get("cache_control")]
    print(f"  표가 선 층: {marks} (기대 [0, 1] — 마지막 층은 턴 지시문 자리라 안 선다)")
    rows = []
    for n in (1, 2):
        _, _, u, _, secs, _ = _call(c, layers, ASK)
        if not u:
            print(f"  {n}판: 씀씀이가 안 왔다 — 못 쟀다")
            return
        rows.append(u)
        print(f"  {n}판: in={u['input_tokens']:,} · cache_write={u['cache_write']:,} · "
              f"cache_read={u['cache_read']:,} · total={u['total_input']:,} · {secs}초")
        _log(f"cache-layers provider={pid} model={c.model} lap={n} input={u['input_tokens']} "
             f"write={u['cache_write']} read={u['cache_read']} total={u['total_input']}")
    w, r, t = rows[0]["cache_write"], rows[1]["cache_read"], rows[1]["total_input"]
    print(f"  뜻 — 첫 판이 캐시에 쓴 몫 {w:,} 을 둘째 판이 {r:,} 만큼 읽었다 (봉투 {t:,}).")
    if w and r >= w * 0.9:
        print("       둘째 판이 첫 판의 쓴 몫을 거의 다 읽었다 → 표가 선 두 층이 **다** 캐시에 들었다.")
    elif w and 0 < r < w * 0.6:
        print("       읽은 몫이 쓴 몫의 절반 언저리다 → **둘째 고정 층은 캐시 밖**일 가능성이 크다.")
    elif not r:
        print("       읽은 몫이 0 이다 → 캐시가 아예 안 걸렸다. 층이 최소 길이에 못 미치거나 수명이 안 선 것이다.")
    else:
        print("       쓴 몫과 읽은 몫이 위 두 꼴 어디에도 안 맞는다 — 숫자를 그대로 남긴다.")


# ---------- ③ 생각 조각 ----------
def thoughts(provider, key):
    pid = provider or _first_of(gateway.CONTRACT_GEMINI)
    c = _creds(pid, key)
    if c.contract != gateway.CONTRACT_GEMINI:
        raise Unmeasured(f"[안 잼] {pid} 는 gemini 계약이 아니다")
    ask = ("다음 셋을 풀고 풀이를 각각 두 문장으로 적어라 — 17×23, 1부터 40까지의 합, "
           "365를 7로 나눈 몫과 나머지.")
    print(f"[③] 생각 조각 — {pid} · {c.model} · 손잡이 {'켬' if gateway.GEMINI_THOUGHTS else '끔'}")
    text, stop, u, first, secs, thinks = _call(c, ["짧고 정확하게 답한다."], ask)
    tk = (u or {}).get("thinking_tokens")
    print(f"  첫 조각 {first}초 · 총 {secs}초 · stop={stop!r} · 글자 {len(text):,}")
    print(f"  씀씀이 thinking_tokens={tk!r} · 생각 신호 {len(thinks)}번 (마지막 {thinks[-1] if thinks else '없음'})")
    _log(f"thoughts provider={pid} model={c.model} on={gateway.GEMINI_THOUGHTS} first={first} "
         f"secs={secs} thinking_tokens={tk} signals={len(thinks)}")
    if isinstance(tk, int):
        print("  뜻 — 생각 몫이 씀씀이까지 내려왔다 → 기전이 실물에서 선다. 「생각으로 예산을 다 썼나」에")
        print("       답할 재료가 기록에 남는다. 504 를 없앤다는 뜻은 아니다 — 죽는 판은 재현이 안 됐다.")
    else:
        print("  뜻 — 생각 칸이 안 왔다. 손잡이가 안 실렸거나 게이트웨이가 그 낱말을 삼켰다 — 봉투를 본다.")


def main():
    p = argparse.ArgumentParser(description="사내 실호출 프로브 — 씨앗의 「안 쟀다」 셋")
    p.add_argument("what", choices=["ratio", "cache-layers", "thoughts", "all"])
    p.add_argument("path", nargs="?", help="①의 검체 — 제 봉투의 결을 가진 글 파일")
    p.add_argument("--contract", choices=[gateway.CONTRACT_ANTHROPIC, gateway.CONTRACT_OPENAI,
                                          gateway.CONTRACT_GEMINI], help="①에서 한 계약만")
    p.add_argument("--provider", help="②③에서 갈래를 짚는다(기본: 표에서 그 계약의 첫 줄)")
    p.add_argument("--key", help="이 부름에 쓸 키. 없으면 키 묶음의 환경변수를 읽는다")
    a = p.parse_args()
    contracts = [a.contract] if a.contract else [gateway.CONTRACT_ANTHROPIC, gateway.CONTRACT_OPENAI,
                                                 gateway.CONTRACT_GEMINI]
    if a.what in ("ratio", "all"):
        ratio(a.path, contracts, a.key)
    if a.what in ("cache-layers", "all"):
        print()
        cache_layers(a.provider if a.what == "cache-layers" else None, a.key)
    if a.what in ("thoughts", "all"):
        print()
        thoughts(a.provider if a.what == "thoughts" else None, a.key)
    print(f"\n숫자는 {LOG.relative_to(ROOT)} 에 쌓였다 — 그 줄을 붙여 보내면 곁말에 옮겨 적는다.")


if __name__ == "__main__":
    main()
