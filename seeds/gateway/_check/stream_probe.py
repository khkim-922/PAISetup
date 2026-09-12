"""글자가 **언제** 도착하나 — 진짜 흐르나, 끝에 몰아서 오나. 그리고 벽은 어디 있나.

    python -X utf8 _check/stream_probe.py                 # 닿는 HTTP 갈래 전부
    python -X utf8 _check/stream_probe.py openai          # 하나만
    python -X utf8 _check/stream_probe.py --wall          # 회사 Claude 갈래에 긴 출력을 시켜 벽을 잰다 (3분 · 값을 치른다)
    python -X utf8 _check/stream_probe.py --wall openai   # 다른 갈래로

값을 치른다(사내 키 · 토큰). 키는 갈래의 키 묶음 환경변수(`gateway._KEY_ENV`)를 읽고, 없으면
「못 쟀다」(2) 로 나간다 — 초록이 아니다. `--key` 로 줄 수도 있다. 안 닿는 갈래는 판정을 안 내고
「못 쟀다」로 센다 — 잰 갈래 0 에서 「전부 흐른다」가 서지 않게.

⚠ **빌려 온 자다** — atelier `_check/stream_probe.py`(2026-08-24 판)를 이 씨앗의 배관 위에 다시
  세웠다. 저쪽은 그 앱의 `config` 에 묶여 있어 떼어 오면 안 돈다. 앞으로는 **여기가 진본**이다.
  바꾼 것 둘 — 판정을 이 씨앗의 종료코드 계약(`_verdict`)으로 세웠고, `--wall` 모드는 저쪽에
  없던 것을 **새로 지었다**(아래).

## 흐르나 — 시각의 축

SSE 모양으로 오는데 **응답을 다 만든 뒤 한꺼번에 뱉을 수 있다.** 그러면 로그에는 `data:` 줄이
멀쩡히 남지만 화면은 끝까지 조용하다 — *"가만히 있다가 바로 결과 뜬다"* 가 그 증상이다.
**형식과 시각은 다른 축이라, 시각을 안 재면 이 둘이 안 갈린다.**

  ① 첫 글자까지 몇 초          — 이것이 곧 사람이 빈 화면을 보는 시간
  ② 본문이 전체의 몇 %를 차지하나 — 침묵이 본체면 **쌓아 뒀다 푼 것**이다
  ③ 조각이 퍼져 있나 몰려 있나  — 마지막 순간에 다 몰려 오면 **버퍼링**이다
  ④ 갈래끼리 견준다            — 같은 게이트웨이라도 경로마다 다를 수 있다

⚠ **②와 ③은 같은 사건의 두 이름이 아니다.** ③은 본문 **안에서** 조각이 어디 쏠렸나를
  보고(창을 첫 글자부터 다시 잰다 — 아래 `verdict`), ②는 본문 **바깥**, 곧 침묵이 전체를
  얼마나 먹었나를 본다. ③만 두면 **침묵 뒤 짧은 버스트가 「그 안에서는 고르다」로 초록이
  된다** — 원 실측 atelier `_check/log/stream-probe.posco-20260824.log`.
⚠ **배관이 보는 것을 그대로 잰다** (`providers.stream_once` 의 `on_text`). 프로브가 SSE 를
  따로 파싱하면 앱이 아닌 것을 재게 되고, **앱의 어느 층에서 막히는지**를 못 가른다 —
  여기서 흐르는데 화면이 조용하면 그때는 서버·브라우저 쪽 일이다.

실측 2026-08-24(사내 · atelier 판): anthropic · openai 둘 다 **고르게 흘렀다** — 첫 글자 5초
언저리, 뒤 창 몫 3%. 버퍼링이 아니다.

## 벽 — `--wall` (이 씨앗이 새로 지은 것)

사내 게이트웨이는 **요청부터의 절대 벽**에서 신호(`stop_reason`) 없이 끊는다. 생성량과 무관하다 —
초당 51토큰이 쉬지 않고 흐르던 판도, 한 토큰도 안 나온 판도 같은 시각에 잘렸다(claude-config
`posco/ENV-posco.md` 「스트림 180초 컷」 · 2026-08-27 180.1초 · 2026-09-09 180.0초). 배관은 그 값을
`gateway.GATEWAY_WALL_S` 로 들고 그 **안쪽**에 출력 상한(`WALL_MAX_TOKENS`)을 둔다 — 절단이
계약(`max_tokens`)으로 오게. 그래서 평소 부름은 벽에 안 닿고, **벽이 옮겨져도 아무도 모른다.**
이 모드는 일부러 벽 너머까지 시켜 **끊긴 시각**을 찍는다.

⚠ 상한을 벽 너머로 올리는 것은 이 자리뿐이다 — `Creds` 를 `_replace` 로 바꿔 그 부름 하나만
  풀고, 배관의 난간은 그대로 둔다. 배관을 고쳐 재면 잰 것이 배관이 아니다.
⚠ 값을 치른다 — 3분에 만 토큰 언저리. 벽이 옮겨졌는지 의심될 때만 돌린다.
⚠ **벽에 안 닿고 끝나면 「못 쟀다」다** — 벽이 없어진 것과 출력이 먼저 끝난 것을 못 가른다.
  더 긴 물음을 주거나 더 느린 모델로 다시 잰다.
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from _verdict import (EXIT_MISMATCH, EXIT_OK, EXIT_UNMEASURED, Unmeasured, edge, fails, passes,
                      report, unmeasured, unmeasureds)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import gateway, providers  # noqa: E402
from live_probe import _creds  # noqa: E402  — 키 묶음 환경변수 · --key · 「못 쟀다」 물러남을 한 자리에서

LOG = ROOT / "_check" / "log" / "stream-probe.log"

# 길게 흘러야 시각이 보인다 — 짧으면 한 덩이로 와도 버퍼링인지 알 수가 없다.
ASK = ("1부터 40까지 세어라. 숫자마다 그 숫자로 시작하는 짧은 한 문장을 붙인다. "
       "설명·머리말 없이 목록만 낸다.")
# 벽 너머까지 — 180초 × 51토큰/초 ≈ 9,200토큰이 벽까지의 몫이라 그 곱절을 시킨다.
WALL_ASK = ("1부터 800까지 세어라. 숫자마다 그 숫자로 시작하는 짧은 한 문장을 붙인다. "
            "설명·머리말 없이 목록만 낸다. 중간에 멈추지 말고 끝까지 낸다.")
WALL_ASK_TOKENS = 20000
WALL_SLACK_S = 10          # 실측이 벽의 이 안이면 「같은 벽」으로 본다

# 마지막 이만큼의 시간 안에 글자가 이만큼 넘게 몰려 오면 **버퍼링으로 본다.**
# 진짜 스트리밍이면 글자가 처음부터 고르게 오므로 이 창에는 그 몫만큼만 들어온다.
TAIL_WINDOW = 0.15      # 전체 걸린 시간의 뒤 15%
TAIL_LIMIT = 0.60       # 그 창에 60% 넘게 오면 몰려 온 것이다

# 본문(첫 글자→마지막 글자)이 전체의 이만큼도 안 되면 **침묵이 본체라고 본다.**
# 프리필이 길어도 그 뒤로 흐르기만 하면 이 값은 크게 나온다 — atelier #114 가 막으려던
# 「프리필 긴 것을 버퍼링으로 뒤집기」가 이 축에서 되살아나지 않는 까닭이다.
BODY_SPAN_MIN = 0.30


def _log(line):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')} {line}\n")


def measure(c, ask):
    """갈래 하나 — (걸린 시간, 조각마다 (도착 시각, 글자수), 글자 전부, stop, 끊긴 사유, 오류)."""
    marks, cut, t0 = [], [], time.monotonic()
    try:
        text, stop = providers.stream_once(
            "너는 시키는 대로 짧게 답한다.", [{"role": "user", "content": ask}],
            lambda t: marks.append((time.monotonic() - t0, len(t))), creds=c,
            on_cut=cut.append)
        return time.monotonic() - t0, marks, text, stop, (cut[0] if cut else ""), None
    except Exception as exc:                                   # noqa: BLE001
        return time.monotonic() - t0, marks, "", None, "", f"{type(exc).__name__}: {exc}"


def verdict(secs, marks):
    """조각이 퍼져 왔나 몰려 왔나 — (성한가, 판정, 첫 글자까지, 뒤 창 몫, 본문 구간).

    ⚠ **성패를 판정 문구에서 주워 읽지 않게 여기서 세운다.** 부르는 쪽이 「버퍼링」 같은
      낱말을 문구에서 찾아 세면, 실패 갈래를 하나 더할 때 그 낱말을 빠뜨리는 순간
      **재는 자가 조용히 초록을 낸다** — 문구는 사람 몫이고 판정은 값 몫이다.
    """
    if not marks:
        return False, "글자를 하나도 못 받았다", None, None, None
    first, last = marks[0][0], marks[-1][0]
    total = sum(n for _t, n in marks) or 1
    # 본문이 전체를 얼마나 차지하나 — 나머지가 곧 침묵이다.
    span = (last - first) / secs if secs > 0 else 0.0
    # 창은 첫 글자 도착부터 잰다 — t0(요청 시작) 기준이면 연결·프리필·대기가 전부 T 에 들어,
    # 첫 글자가 t₁ > 0.75T 로 늦으면 완전 균등 스트리밍도 「버퍼링」으로 뒤집힌다. 프리필이
    # 긴 것은 ①(첫 글자까지)이 따로 재는 축이라 여기 섞지 않는다.
    edge_t = first + (secs - first) * (1 - TAIL_WINDOW)
    tail = sum(n for t, n in marks if t >= edge_t) / total
    if len(marks) == 1:
        return False, "**한 덩이로 왔다 — 스트리밍이 아니다**", first, 1.0, 0.0
    if span < BODY_SPAN_MIN:
        return False, "**침묵이 본체다 — 쌓아 뒀다 한 번에 풀었다**", first, tail, span
    if tail > TAIL_LIMIT:
        return False, "**끝에 몰려 왔다 — 버퍼링이다**", first, tail, span
    return True, "고르게 흘렀다 — 스트리밍이 산다", first, tail, span


def bar(secs, marks, width=48):
    """도착을 시간축에 찍는다 — 숫자보다 이 줄 하나가 빨리 말한다."""
    if not marks or secs <= 0:
        return "(못 받았다)"
    cells = [0] * width
    for t, n in marks:
        cells[min(width - 1, int(t / secs * width))] += n
    top = max(cells) or 1
    return "".join(" ▁▂▃▄▅▆▇█"[min(8, round(v / top * 8))] for v in cells)


def _exit():
    bad = fails()
    if bad:
        print(f"\n❌ {len(bad)}건 어긋남 — {' · '.join(bad)}")
        raise SystemExit(EXIT_MISMATCH)
    if unmeasureds():
        print(f"\n판정 {len(passes())}건 초록 · 못 잰 갈래 {len(unmeasureds())} — 초록이 아니다")
        raise SystemExit(EXIT_UNMEASURED)
    print(f"\n✅ 판정 {len(passes())}건 초록")
    raise SystemExit(EXIT_OK)


def flow(want, key):
    print("--- 글자가 언제 도착하나 (실호출)")
    print(f"       본문 구간이 {int(BODY_SPAN_MIN * 100)}% 미만이면 침묵 · "
          f"뒤 {int(TAIL_WINDOW * 100)}% 창에 {int(TAIL_LIMIT * 100)}% 넘게 오면 버퍼링")
    for pid in want:
        if pid not in gateway._GATEWAY:
            unmeasured(pid, f"게이트웨이 표에 없다 (있는 것: {', '.join(gateway._GATEWAY)})")
            continue
        row = gateway._GATEWAY[pid]
        print(f"\n[{pid}] {row['label']} · 계약 {row['contract']}")
        if row.get("local"):
            # 「건너뜀」이 아니라 **미측정**이다 — 안 잰 것이 판정 밖으로 새면 잰 갈래 0에서도
            # 「전부 흐른다」가 선다.
            unmeasured(pid, "로컬 갈래는 스트리밍 시각 측정 대상이 아니다")
            continue
        if not gateway.reachable(pid):
            unmeasured(pid, f"안 닿는다 — {gateway.why_unreachable(pid)}")
            continue
        # 키는 부르기 전에 본다 — `_creds` 가 물러나며 찍는 줄과 여기 「못 쟀다」가 겹치지 않게.
        if not (key or gateway.env_token(row["key_group"])):
            names = gateway._KEY_ENV.get(row["key_group"]) or ()
            unmeasured(pid, "키가 없다 — " + (f"`--key` 로 주거나 환경변수 {' · '.join(names)} 를 둔다"
                                            if names else f"`--key` 로 준다. `{row['key_group']}` 묶음은 환경변수를 안 읽는다"))
            continue
        c = _creds(pid, key)
        secs, marks, text, stop, cut, err = measure(c, ASK)
        if err:
            unmeasured(pid, err)
            continue
        ok, say, first, tail, span = verdict(secs, marks)
        print(f"       {bar(secs, marks)}")
        detail = (f"첫 글자까지 {first:.1f}초 · 본문 구간 {span:.0%} · 뒤 창 몫 {tail:.0%}"
                  if marks else "도착한 조각이 없다")
        print(f"       {secs:.1f}초 · 조각 {len(marks)} · {len(text):,}자 · stop={stop!r} · {detail}")
        _log(f"flow provider={pid} model={c.model} secs={secs:.1f} marks={len(marks)} chars={len(text)} "
             f"first={first} span={span} tail={tail} stop={stop!r}")
        report(f"{pid} — {say}", ok, [f"실측 {detail}" + (f" · 끊김 {cut}" if cut else "")])
    # ⚠ **이 자가 답하는 것은 「누구 탓인가」지 「어떻게 고치나」가 아니다.**
    #   고르게 흘렀는데 화면이 조용하면 그때는 우리 쪽(서버 SSE·브라우저) 일이고,
    #   몰려 왔거나 침묵이 본체면 **요청으로는 못 고친다** — `stream: true` 는 이미 실려 나간다.
    edge("고르게 흘렀는데 화면이 조용하면 그때는 서버 SSE·브라우저 쪽 일이다 — 요청으로는 못 고친다")


def wall(pid, key):
    print(f"--- 벽은 어디 있나 (실호출 · 긴 출력 하나 · 배관이 아는 벽 {gateway.GATEWAY_WALL_S}초)")
    if pid not in gateway._GATEWAY:
        raise Unmeasured(f"[안 잼] 게이트웨이 표에 없다 — {pid} (있는 것: {', '.join(gateway._GATEWAY)})")
    row = gateway._GATEWAY[pid]
    if row.get("local"):
        raise Unmeasured(f"[안 잼] {pid} 는 로컬 갈래라 벽이 없다 — 벽은 사내 게이트웨이의 것이다")
    if not gateway.reachable(pid):
        raise Unmeasured(f"[안 잼] {pid} 에 안 닿는다 — {gateway.why_unreachable(pid)}")
    c = _creds(pid, key)
    # 배관의 난간(`WALL_MAX_TOKENS`)을 **이 부름 하나만** 넘긴다 — 벽을 재려면 벽 너머로 시켜야 한다.
    c = c._replace(max_tokens=WALL_ASK_TOKENS)
    print(f"       {pid} · {c.model} · 상한 {c.max_tokens:,} (평소 난간 {gateway.WALL_MAX_TOKENS:,} 을 이 부름만 넘긴다)")
    secs, marks, text, stop, cut, err = measure(c, WALL_ASK)
    n = len(marks)
    print(f"       {bar(secs, marks)}")
    print(f"       {secs:.1f}초 · 조각 {n} · {len(text):,}자 · stop={stop!r}" + (f" · 끊김 {cut}" if cut else ""))
    _log(f"wall provider={pid} model={c.model} secs={secs:.1f} marks={n} chars={len(text)} stop={stop!r} cut={cut!r} err={err!r}")
    if err:
        raise Unmeasured(f"[안 잼] 부름이 졌다 — {err}")
    if stop is not None:
        unmeasured("벽", f"출력이 벽 전에 끝났다 — 총 {secs:.1f}초 · stop={stop!r} · {len(text):,}자. "
                        "벽이 없어진 것과 출력이 먼저 끝난 것을 못 가른다 — 더 긴 물음이나 더 느린 모델로 다시 잰다")
    else:
        w = gateway.GATEWAY_WALL_S
        edge(f"신호 없이 끊긴 시각 {secs:.1f}초 · 그때까지 {len(text):,}자 — 이 숫자가 곧 벽의 실측이다")
        report(f"벽이 배관이 아는 자리({w}초 ± {WALL_SLACK_S})에 있다",
               abs(secs - w) <= WALL_SLACK_S,
               [f"실측 {secs:.1f}초 — 배관의 `GATEWAY_WALL_S`({w}) 와 그 안쪽의 `WALL_MAX_TOKENS` 역산을 다시 본다",
                "벽이 옮겨진 것이 실측이면 그 값을 claude-config posco/ENV-posco.md 「스트림 180초 컷」에 적는다"])


def main():
    p = argparse.ArgumentParser(description="글자가 언제 도착하나 — 흐르나(기본) · 벽은 어디 있나(--wall)")
    p.add_argument("providers", nargs="*", help="갈래 이름들. 안 주면 표의 HTTP 갈래 전부(--wall 이면 회사 Claude)")
    p.add_argument("--wall", action="store_true", help="긴 출력을 시켜 신호 없이 끊기는 시각을 찍는다 — 3분 · 값을 치른다")
    p.add_argument("--key", help="이 부름에 쓸 키. 없으면 키 묶음의 환경변수를 읽는다")
    a = p.parse_args()
    if a.wall:
        wall((a.providers or ["anthropic"])[0], a.key)
    else:
        want = a.providers or [pid for pid, row in gateway._GATEWAY.items() if not row.get("local")]
        flow(want, a.key)
    _exit()


if __name__ == "__main__":
    main()
