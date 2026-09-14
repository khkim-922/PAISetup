"""짝 검사 — 프록시가 Opus 5 의 400(assistant prefill 거절)을 정말 없애나, 사내망 밖에서 잰다.

가짜 게이트웨이(`mock_gateway.py` · 실제처럼 prefill 에 400 을 낸다)를 루프백에 세우고 그 앞에
프록시를 세운 뒤, assistant 로 끝나는 본문 하나를 **직결**과 **프록시 너머**로 보낸다.
직결 400 · 프록시 200 · 프록시 계수 `trimmed_prefills` 1 이 다 서야 초록이다 — 짧은 답이 오나가
아니라 **그 400 이 사라졌나**를 잰다. 회사 설치기의 검증 칸(결정 0041)이 실물 게이트웨이에서
재는 것과 같은 물음이고, 여기는 집에서 미리 재는 자리다.

    python -X utf8 pair_check.py        # 포트 18901(프록시) · 18902(가짜) 를 잠깐 쓴다
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOCK_PORT = 18902
PROXY_PORT = 18901          # 프록시 파일이 못박은 값 — 인자가 없다


def _post(url: str, body: dict) -> int:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"content-type": "application/json",
                 "Authorization": "Bearer " + "x" * 36,       # 가짜는 길이만 본다
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as err:
        return err.code


def _wait_health() -> dict:
    for _ in range(50):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PROXY_PORT}/health", timeout=1) as resp:
                return json.load(resp)
        except OSError:
            time.sleep(0.1)
    raise SystemExit(f"프록시가 {PROXY_PORT} 에 안 떴다 — 포트가 잡혀 있나 본다")


def main() -> int:
    env = dict(os.environ, PGPT_PROXY_UPSTREAM=f"http://127.0.0.1:{MOCK_PORT}", PYTHONUTF8="1")
    quiet = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    mock = subprocess.Popen([sys.executable, str(HERE / "mock_gateway.py"), str(MOCK_PORT)], **quiet)
    proxy = subprocess.Popen([sys.executable, str(HERE / "opus5_proxy.py")], env=env, **quiet)
    try:
        _wait_health()
        body = {"model": "claude-opus-5", "max_tokens": 16, "temperature": 0.2,
                "messages": [{"role": "user", "content": "hi"},
                             {"role": "assistant", "content": "prefill"}]}
        direct = _post(f"http://127.0.0.1:{MOCK_PORT}/gpgpta01-gpt/v1/messages", body)
        via = _post(f"http://127.0.0.1:{PROXY_PORT}/gpgpta01-gpt/v1/messages", body)
        trimmed = _wait_health().get("trimmed_prefills")
    finally:
        proxy.terminate()
        mock.terminate()
        for leftover in ("proxy.log", "opus5_proxy.pid"):      # 프록시가 제 곁에 남기는 것
            (HERE / leftover).unlink(missing_ok=True)
    checks = {"직결은 400": direct == 400, "프록시 너머는 200": via == 200,
              "프록시가 prefill 을 1번 뗐다": trimmed == 1}
    for name, ok in checks.items():
        print(f"  [{'O' if ok else 'X'}] {name}")
    good = sum(checks.values())
    print(f"짝 검사: {good}/{len(checks)} — {'OK' if good == len(checks) else 'FAIL'} "
          f"(직결 {direct} · 프록시 {via} · trimmed_prefills {trimmed})")
    return 0 if good == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
