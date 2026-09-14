from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MODELS = [
    "claude-opus-4.5",
    "claude-opus-4.6",
    "claude-opus-4.7",
    "claude-opus-5",
    "claude-sonnet-4.5",
    "claude-sonnet-4.6",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "google-gemma-4-31B-it",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-5-chat-latest",
    "gpt-5.1-chat",
    "gpt-5.2",
    "gpt-5.2-chat",
    "gpt-5.3-chat",
    "gpt-5.3-codex",
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.5",
    "gpt-5.6-luna",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "grok-4-1-fast-non-reasoning",
    "grok-4-1-fast-reasoning",
    "o3-mini",
    "o4-mini",
]

ROOT = "http://127.0.0.1:18901/gpgpta01-gpt"
OUT_DIR = Path(__file__).resolve().parent / "model-results"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_key() -> str:
    if os.environ.get("PGPT_API_KEY"):
        return os.environ["PGPT_API_KEY"].strip()
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "hermes" / ".env",
        Path(os.environ.get("USERPROFILE", "")) / ".claude" / "settings.json",
    ]
    env_path = candidates[0]
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            if line.strip().startswith("PGPT_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    claude_path = candidates[1]
    if claude_path.exists():
        try:
            data = json.loads(claude_path.read_text(encoding="utf-8-sig", errors="ignore"))
            token = (data.get("env") or {}).get("ANTHROPIC_AUTH_TOKEN")
            if token:
                return str(token).strip()
        except Exception:
            pass
    raise SystemExit("PGPT_API_KEY를 찾지 못했습니다. Hermes .env 또는 .claude/settings.json을 확인하세요.")


def post_json(url: str, headers: dict[str, str], payload: dict, timeout: int = 75) -> tuple[int, str, object]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            elapsed = time.time() - started
            try:
                parsed = json.loads(raw) if raw else None
            except Exception:
                parsed = raw[:500]
            return resp.status, f"{elapsed:.2f}s", parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        elapsed = time.time() - started
        return e.code, f"{elapsed:.2f}s", raw[:1200]
    except Exception as e:
        elapsed = time.time() - started
        return 0, f"{elapsed:.2f}s", repr(e)


def family(model: str) -> str:
    # Hermes uses Anthropic Messages for Claude providers and OpenAI-compatible
    # chat_completions for the rest.  The local proxy translates gemini-* chat
    # requests to P-GPT's Gemini native /v1beta route internally.
    if model.startswith("claude-"):
        return "claude_messages"
    return "chat_completions"


def test_model(model: str, token: str) -> dict:
    fam = family(model)
    if fam == "claude_messages":
        url = f"{ROOT}/v1/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "Reply exactly OK"}],
        }
    elif fam == "gemini_native":
        escaped = urllib.parse.quote(model, safe="")
        url = f"{ROOT}/v1beta/models/{escaped}:generateContent"
        headers = {
            "Authorization": f"Bearer {token}",
            "x-goog-api-key": token,
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [{"role": "user", "parts": [{"text": "Reply exactly OK"}]}],
            "generationConfig": {"maxOutputTokens": 8},
        }
    else:
        url = f"{ROOT}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Reply exactly OK"}],
            "max_tokens": 8,
            "stream": False,
        }
    status, elapsed, parsed = post_json(url, headers, payload)
    ok = False
    detail = ""
    if isinstance(parsed, dict):
        if fam == "claude_messages":
            ok = status == 200 and parsed.get("role") == "assistant" and bool(parsed.get("id"))
            detail = json.dumps({"id": parsed.get("id"), "model": parsed.get("model"), "content": parsed.get("content"), "stop_reason": parsed.get("stop_reason")}, ensure_ascii=False)[:500]
        elif fam == "gemini_native":
            ok = status == 200 and bool(parsed.get("candidates"))
            detail = json.dumps({"modelVersion": parsed.get("modelVersion"), "candidates": parsed.get("candidates")}, ensure_ascii=False)[:500]
        else:
            ok = status == 200 and bool(parsed.get("choices"))
            detail = json.dumps({"model": parsed.get("model"), "choices": parsed.get("choices")}, ensure_ascii=False)[:500]
    else:
        detail = str(parsed).replace("\n", " ")[:500]
    return {"model": model, "family": fam, "ok": ok, "status": status, "elapsed": elapsed, "detail": detail}


def main() -> int:
    token = load_key()
    print(f"Testing {len(MODELS)} models via {ROOT} (token hidden)", flush=True)
    results = []
    for idx, model in enumerate(MODELS, 1):
        result = test_model(model, token)
        results.append(result)
        mark = "OK" if result["ok"] else "FAIL"
        print(f"[{idx:02d}/{len(MODELS)}] {mark:4} {model:32} {result['family']:18} HTTP {result['status']} {result['elapsed']}", flush=True)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    json_path = OUT_DIR / f"pgpt-model-test-{stamp}.json"
    csv_path = OUT_DIR / f"pgpt-model-test-{stamp}.csv"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["model", "family", "ok", "status", "elapsed", "detail"])
        w.writeheader()
        w.writerows(results)

    ok = [r for r in results if r["ok"]]
    fail = [r for r in results if not r["ok"]]
    print("\nSUMMARY")
    print(f"OK={len(ok)} FAIL={len(fail)} TOTAL={len(results)}")
    print("OK_MODELS=" + ", ".join(r["model"] for r in ok))
    print("FAIL_MODELS=" + ", ".join(r["model"] for r in fail))
    print(f"JSON={json_path}")
    print(f"CSV={csv_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
