"""캐시 1시간이 게이트웨이 너머에서 서나 — 두 갈래를 시작 간격 8분으로 두 번씩 부르는 회사 측정(결정 0174).

    python -X utf8 posco/pgpt-proxy/cache_ttl_probe.py [--gap 480] [--model claude-opus-5] [--base <게이트웨이 뿌리>]

갈래 A 는 system 표식에 `ttl: "1h"` 와 `anthropic-beta: extended-cache-ttl-2025-04-11` 을 싣고, 갈래 B(대조)는 둘 다 안 싣는다.
두 갈래는 서로 다른 고유 접두사(약 5천 토큰)를 쓴다. 첫 부름에서 둘 다 캐시에 쓰고, 첫 부름의 **시작**에서 `--gap` 초 뒤에 같은
본문을 다시 부른다 — 캐시 수명은 부름의 시작부터 센다.
내는 것: 부름마다 사용량 한 줄 · 판정 한 줄 · 같은 폴더의 `cache-ttl-probe-<시각>.json`. 종료 값 — 0 판정함 · 2 못 가림 · 1 부름 실패.
판정 — B 둘째가 0 을 읽어야 간격이 5분을 넘긴 것이 선다(아니면 못 가림). 그 위에서 A 둘째가 첫 쓰기만큼 읽으면 1시간이 선다, 0 을
읽으면 게이트웨이가 1시간을 안 옮긴다.
키는 곁의 `Test-AllPgptModels.py` 의 `load_key` 가 읽고, 그것이 못 찾으면 세션 환경의 `ANTHROPIC_AUTH_TOKEN` 을 쓴다 —
설치기가 토큰을 `settings.json` 에 안 적고 세션 환경으로만 넣는 자리가 있다. 게이트웨이에 직접 붙는다 — 프록시도 사내 `HTTP_PROXY` 도 안 탄다.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("smoke", HERE / "Test-AllPgptModels.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)

GATEWAY = "http://aigpt.posco.net/gpgpta01-gpt"
TTL_BETA = "extended-cache-ttl-2025-04-11"
FIVE_MIN = 300
# 접두사 — Opus 5 의 캐시 최소(512) · Sonnet 4.6 의 최소(1,024)를 넉넉히 넘기는 약 5천 토큰
FILLER = "This paragraph only pads a prompt-cache probe so that the cached prefix is long enough to be stored. " * 220
READ_SHARE = 0.9  # 둘째 읽기가 첫 쓰기의 이만큼 이상이면 「읽혔다」


def call(base: str, key: str, model: str, prefix: str, one_hour: bool) -> tuple[float, dict | str]:
    """게이트웨이에 한 번 부르고 (시작 시각, 사용량) 을 낸다 — 사용량을 못 읽으면 둘째 칸이 글이다.

    ⚠ 반드시 스트리밍으로 부른다 — 게이트웨이는 캐시 읽기 · 쓰기 항을 `message_delta` 에만 싣고
    비스트리밍 응답의 `usage` 에서는 뺀다. 비스트리밍으로 부르면 캐시에 썼는데도 0 으로 보여
    판정이 늘 「못 가림」 으로 떨어진다.
    """
    mark = {"type": "ephemeral", "ttl": "1h"} if one_hour else {"type": "ephemeral"}
    body = {"model": model, "max_tokens": 16, "stream": True,
            "system": [{"type": "text", "text": prefix, "cache_control": mark}],
            "messages": [{"role": "user", "content": "Reply with OK."}]}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
    if one_hour:
        headers["anthropic-beta"] = TTL_BETA
    request = urllib.request.Request(base.rstrip("/") + "/v1/messages", data=json.dumps(body).encode("utf-8"),
                                     headers=headers, method="POST")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    started = time.time()
    usage: dict = {}
    try:
        with opener.open(request, timeout=180) as response:
            for raw in response:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                try:
                    event = json.loads(line[5:].strip())
                except ValueError:
                    continue
                # 캐시 항은 나중 사건이 든다 — 보이는 사용량마다 덮어써 마지막 것을 남긴다.
                found = event.get("usage") or (event.get("message") or {}).get("usage")
                if found:
                    usage = {**usage, **found}
    except urllib.error.HTTPError as error:
        return started, f"HTTP {error.code}: {error.read().decode('utf-8', 'replace')[:300]}"
    except (OSError, ValueError) as error:
        return started, repr(error)[:300]
    return started, usage


def read_of(usage: dict | str) -> int:
    return usage.get("cache_read_input_tokens") or 0 if isinstance(usage, dict) else 0


def write_of(usage: dict | str) -> int:
    return usage.get("cache_creation_input_tokens") or 0 if isinstance(usage, dict) else 0


def resolve_key() -> str:
    """게이트웨이 키 — 곁 스크립트의 `load_key` 가 먼저, 그것이 못 찾으면 세션 환경의 `ANTHROPIC_AUTH_TOKEN`."""
    try:
        return smoke.load_key()
    except SystemExit:
        token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
        if not token:
            raise
        return token


def main() -> int:
    parser = argparse.ArgumentParser(description="캐시 1시간이 게이트웨이 너머에서 서나")
    parser.add_argument("--gap", type=float, default=480.0, help="첫 부름 시작에서 둘째 부름까지 초(기본 480 = 8분)")
    parser.add_argument("--model", default="claude-opus-5")
    parser.add_argument("--base", default=GATEWAY, help="게이트웨이 뿌리(…/gpgpta01-gpt)")
    args = parser.parse_args()
    key = resolve_key()
    nonce = uuid.uuid4().hex
    arms = {"A": (True, f"[cache ttl probe {nonce} arm A · 1h]\n{FILLER}"),
            "B": (False, f"[cache ttl probe {nonce} arm B · control]\n{FILLER}")}
    rows: list[dict] = []
    first: dict[str, tuple[float, dict | str]] = {}
    for name, (one_hour, prefix) in arms.items():
        first[name] = call(args.base, key, args.model, prefix, one_hour)
        rows.append({"arm": name, "round": 1, "started": first[name][0], "usage": first[name][1]})
        print(f"{name}1 · {'1h' if one_hour else '5m'} · {first[name][1]}", flush=True)
    if any(not isinstance(result, dict) for _, result in first.values()):
        print("판정: 첫 부름이 졌다 — 위 줄을 본다")
        return 1
    second: dict[str, tuple[float, dict | str]] = {}
    for name, (one_hour, prefix) in arms.items():
        wait = first[name][0] + args.gap - time.time()
        if wait > 0:
            print(f"… {name}2 까지 {wait:.0f}초 기다린다", flush=True)
            time.sleep(wait)
        second[name] = call(args.base, key, args.model, prefix, one_hour)
        rows.append({"arm": name, "round": 2, "started": second[name][0], "usage": second[name][1]})
        gap = second[name][0] - first[name][0]
        print(f"{name}2 · 시작 간격 {gap:.0f}초 · {second[name][1]}", flush=True)
    a_write, a_read = write_of(first["A"][1]) + read_of(first["A"][1]), read_of(second["A"][1])
    b_read = read_of(second["B"][1])
    gap_b = second["B"][0] - first["B"][0]
    if any(not isinstance(result, dict) for _, result in second.values()):
        verdict, code = "둘째 부름이 졌다 — 위 줄을 본다", 1
    elif a_write == 0:
        verdict, code = "못 가림 — 첫 부름이 캐시에 안 썼다(표식이 버려졌거나 접두사가 짧다)", 2
    elif gap_b <= FIVE_MIN or b_read > 0:
        verdict, code = f"못 가림 — 대조(B)가 {b_read} 를 읽었거나 간격이 {gap_b:.0f}초로 5분 안이다 · --gap 을 늘려 다시", 2
    elif a_read >= READ_SHARE * a_write:
        verdict, code = f"1시간이 선다 — A 가 {gap_b:.0f}초 뒤 {a_read} 를 읽었고 대조는 0 을 읽었다", 0
    elif a_read == 0:
        verdict, code = "1시간이 안 선다 — A 도 대조처럼 0 을 읽었다(게이트웨이가 1시간을 안 옮긴다)", 0
    else:
        verdict, code = f"일부만 읽었다 — A 쓰기 {a_write} · 읽기 {a_read} · 위 줄을 본다", 2
    print("판정:", verdict)
    out = HERE / f"cache-ttl-probe-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps({"model": args.model, "base": args.base, "gap": args.gap, "verdict": verdict, "rows": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("기록:", out)
    return code


if __name__ == "__main__":
    sys.exit(main())
