"""실제 세션이 캐시를 얼마나 읽고 다시 썼나 — Claude Code 대화 기록(`~/.claude/projects/**/*.jsonl`)의 사용량을 요청마다 읽는다.

    python -X utf8 posco/pgpt-proxy/cache_usage_report.py [--since 2026-10-20] [--root <projects 폴더>] [--all]

요청 하나는 Claude Code 가 받은 응답 하나다(블록마다 여러 줄로 적혀도 하나로 센다). 시작 시각은 `api-request` 줄에서, 없으면
그 응답의 부모 줄에서 읽는다. 나이는 같은 기록(메인 · 서브에이전트 따로)에서 앞 요청의 시작부터 이 요청의 시작까지다 —
캐시 수명은 부름의 시작부터 센다.
표식 — `다시씀`: 첫 요청이 아닌데 읽기가 (읽기 + 쓰기)의 절반에 못 미친다(접두사가 통째로 다시 쓰였다).
`쉼>5분`: 나이가 5분을 넘는다. 5분 안의 `다시씀` 은 캐시가 깨진 것이고, 5분 넘은 요청의 읽기는 1시간이 선 것이다.
`레인대기`: 메인의 `쉼>5분` 가운데 그 쉼 안에 같은 세션의 서브에이전트 요청이 시작된 것 — 메인이 레인의 답을 기다리느라 쉰
판이다. 그 판의 `다시씀` 쓰기 합이 레인이 도는 동안만 캐시를 데우는 장치가 막을 수 있는 몫이다.
`생각만끊김`: `max_tokens` 로 끝났는데 글 · 도구 호출이 없는 응답 — 출력 상한을 생각에만 다 쓴 턴이다. 세션 줄의 `이어쓰기` 는
Claude Code 가 출력 상한 뒤에 보낸 이어 쓰기 글의 수다 — 내용 칸 없이 끊긴 턴은 응답 줄이 안 남아도 이것으로 보인다.
내는 것: 세션마다 요약 한 줄과 표식 붙은 요청(`--all` 이면 모든 요청) · 전체 요약 · 세션 끝 `cost-state` 의 모델별 합.
대화 글 · 계정 · 세션 ID 는 안 낸다 — 세션은 S1 · S2 … 와 작업 폴더 이름으로 가리킨다. 종료 값 — 0 · 기록 없음 1.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIVE_MIN = 300
ONE_HOUR = 3600
REWRITE_SHARE = 0.5   # 읽기가 (읽기 + 쓰기)의 이만큼에 못 미치면 다시 쓴 것
REWRITE_FLOOR = 10_000  # 이보다 작은 접두사의 다시 쓰기는 안 센다
# Claude Code 가 출력 상한 뒤에 보내는 이어 쓰기 글의 머리 — 프록시 `_OUTPUT_LIMIT_RESUME_HEAD` 와 같은 글이다
RESUME_HEAD = "Output token limit hit. Resume directly"
ANSWER_BLOCKS = {"text", "tool_use", "server_tool_use"}  # 이 가운데 하나라도 있으면 답을 낸 응답이다


def parse_time(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def session_of(path: Path) -> str:
    """기록 파일이 속한 세션 — 메인은 `<세션>.jsonl`, 서브에이전트는 `<세션>/subagents/agent-*.jsonl` 이다."""
    return path.parent.parent.name if path.parent.name == "subagents" else path.stem


def _answer_kinds(message: dict) -> set[str]:
    """응답 한 줄에 실린 내용 칸 가운데 답에 드는 종류 — 빈 글은 답으로 안 친다."""
    content = message.get("content")
    if not isinstance(content, list):
        return set()
    return {block.get("type") for block in content if isinstance(block, dict) and block.get("type") in ANSWER_BLOCKS
            and (block.get("type") != "text" or str(block.get("text") or "").strip())}


def _is_resume(entry: dict) -> bool:
    """Claude Code 가 출력 상한 뒤에 보낸 이어 쓰기 글인가."""
    message = entry.get("message")
    if entry.get("type") != "user" or not isinstance(message, dict):
        return False
    content = message.get("content")
    texts = [content] if isinstance(content, str) else [
        block.get("text") for block in content or [] if isinstance(block, dict) and block.get("type") == "text"]
    return any(isinstance(text, str) and text.lstrip().startswith(RESUME_HEAD) for text in texts)


def read_file(path: Path) -> tuple[list[dict], dict, list[datetime]]:
    """한 기록 파일의 요청 목록(시작 순) · 마지막 cost-state 의 모델별 합 · 이어 쓰기 글의 시각을 낸다."""
    entries: list[dict] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
    by_uuid = {e["uuid"]: e for e in entries if isinstance(e, dict) and e.get("uuid")}
    sent = {e["id"]: parse_time(e.get("timestamp")) for e in entries if e.get("type") == "api-request" and e.get("id")}
    resumes = [t for t in (parse_time(e.get("timestamp")) for e in entries if _is_resume(e)) if t]
    requests: dict[str, dict] = {}
    model_usage: dict = {}
    for entry in entries:
        if entry.get("type") == "cost-state":
            model_usage = entry.get("modelUsage") or model_usage
        if entry.get("type") != "assistant" or not isinstance(entry.get("message"), dict):
            continue
        message = entry["message"]
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        key = entry.get("requestRef") or f"{message.get('id')}|{json.dumps(usage, sort_keys=True)}"
        if key in requests:
            # 응답 하나가 내용 칸마다 한 줄로 적힌다 — 칸의 종류는 줄마다 모은다
            requests[key]["answer"] |= _answer_kinds(message)
            continue
        parent = by_uuid.get(entry.get("parentUuid") or "")
        start = sent.get(entry.get("requestRef") or "") or parse_time((parent or {}).get("timestamp")) or parse_time(entry.get("timestamp"))
        if start is None:
            continue
        requests[key] = {
            "start": start,
            "chain": "sub" if entry.get("isSidechain") or "subagents" in path.parts else "main",
            "model": entry.get("requestedModel") or message.get("model") or "?",
            "cwd": Path(entry.get("cwd") or "?").name,
            "in": usage.get("input_tokens") or 0,
            "read": usage.get("cache_read_input_tokens") or 0,
            "write": usage.get("cache_creation_input_tokens") or 0,
            "out": usage.get("output_tokens") or 0,
            "stop": message.get("stop_reason"),
            "answer": _answer_kinds(message),
            "lane": False,
        }
    ordered = sorted(requests.values(), key=lambda r: r["start"])
    previous: dict[str, datetime] = {}
    for request in ordered:
        before = previous.get(request["chain"])
        request["age"] = (request["start"] - before).total_seconds() if before else None
        previous[request["chain"]] = request["start"]
        total = request["read"] + request["write"]
        request["rewrite"] = (request["age"] is not None and total >= REWRITE_FLOOR
                              and request["read"] < REWRITE_SHARE * total)
        request["thinking_cut"] = request["stop"] == "max_tokens" and not request["answer"]
    return ordered, model_usage, resumes


def mark_lane_waits(requests: list[dict], sub_starts: list[datetime]) -> None:
    """메인의 5분 넘은 쉼 안에 서브에이전트 요청이 시작됐으면 그 메인 요청에 `lane` 을 단다."""
    for request in requests:
        if request["chain"] != "main" or request["age"] is None or request["age"] <= FIVE_MIN:
            continue
        idle_from = request["start"] - timedelta(seconds=request["age"])
        request["lane"] = any(idle_from < start < request["start"] for start in sub_starts)


def flags(request: dict) -> str:
    marks = []
    if request["age"] is not None and request["age"] > FIVE_MIN:
        marks.append("쉼>5분")
    if request["lane"]:
        marks.append("레인대기")
    if request["rewrite"]:
        marks.append("다시씀")
    if request["thinking_cut"]:
        marks.append(f"생각만끊김(out {request['out']:,})")
    return " ".join(marks)


def tally(requests: list[dict], resumes: int = 0) -> dict:
    out = {"n": len(requests), "in": 0, "read": 0, "write": 0, "broke": 0, "broke_write": 0,
           "long": 0, "long_read": 0, "long_rewrite": 0, "lane": 0, "lane_rewrite": 0, "lane_write": 0,
           "thinking_cut": 0, "resumes": resumes}
    for r in requests:
        out["in"] += r["in"]; out["read"] += r["read"]; out["write"] += r["write"]
        out["thinking_cut"] += r["thinking_cut"]
        if r["lane"]:
            out["lane"] += 1
            if r["rewrite"]:
                out["lane_rewrite"] += 1; out["lane_write"] += r["write"]
        if r["age"] is None:
            continue
        if r["age"] <= FIVE_MIN and r["rewrite"]:
            out["broke"] += 1; out["broke_write"] += r["write"]
        if FIVE_MIN < r["age"] <= ONE_HOUR:
            out["long"] += 1
            out["long_rewrite" if r["rewrite"] else "long_read"] += 1
    return out


def summary(t: dict) -> str:
    total = t["in"] + t["read"] + t["write"]
    share = f"{t['read'] / total:.0%}" if total else "-"
    return (f"요청 {t['n']} · in {t['in']:,} · read {t['read']:,} · write {t['write']:,} · 읽기 몫 {share} · "
            f"5분 안 다시씀 {t['broke']}(쓰기 {t['broke_write']:,}) · 5–60분 쉼 {t['long']}(읽음 {t['long_read']} · 다시씀 {t['long_rewrite']}) · "
            f"레인대기 {t['lane']}(다시씀 {t['lane_rewrite']} · 쓰기 {t['lane_write']:,}) · "
            f"생각만끊김 {t['thinking_cut']} · 이어쓰기 {t['resumes']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="실제 세션의 캐시 읽기 · 다시 쓰기")
    parser.add_argument("--root", default=str(Path.home() / ".claude" / "projects"))
    parser.add_argument("--since", default=datetime.now().strftime("%Y-%m-%d"), help="이 날(현지) 0시 뒤의 요청만(기본 오늘)")
    parser.add_argument("--all", action="store_true", help="표식 없는 요청도 낸다")
    args = parser.parse_args()
    since = datetime.fromisoformat(args.since).astimezone(timezone.utc)
    sessions = []
    sub_starts: dict[str, list[datetime]] = {}
    for path in sorted(Path(args.root).rglob("*.jsonl")):
        requests, model_usage, resumes = read_file(path)
        requests = [r for r in requests if r["start"] >= since]
        resumes = [t for t in resumes if t >= since]
        if requests:
            sessions.append((session_of(path), requests, model_usage, resumes))
            sub_starts.setdefault(session_of(path), []).extend(r["start"] for r in requests if r["chain"] == "sub")
    if not sessions:
        print(f"기록 없음 — {args.root} 에 {args.since} 뒤의 사용량이 안 보인다")
        return 1
    sessions.sort(key=lambda s: s[1][0]["start"])
    everything: list[dict] = []
    all_resumes = 0
    models: dict[str, dict] = {}
    for number, (session, requests, model_usage, resumes) in enumerate(sessions, 1):
        mark_lane_waits(requests, sub_starts.get(session, []))
        everything += requests
        all_resumes += len(resumes)
        chains = sorted({r["chain"] for r in requests})
        print(f"S{number} · {requests[0]['cwd']} · {requests[0]['start'].astimezone():%H:%M} · {'+'.join(chains)} · "
              f"{summary(tally(requests, len(resumes)))}")
        for r in requests:
            mark = flags(r)
            if mark or args.all:
                age = "-" if r["age"] is None else f"{r['age']:.0f}s"
                print(f"   {r['start'].astimezone():%H:%M:%S} {r['chain']:4} {r['model']:22} 나이 {age:>6} · in {r['in']:>7,} · "
                      f"read {r['read']:>9,} · write {r['write']:>9,}  {mark}")
        for model, usage in (model_usage or {}).items():
            slot = models.setdefault(model, {"in": 0, "read": 0, "write": 0})
            slot["in"] += usage.get("inputTokens") or 0
            slot["read"] += usage.get("cacheReadInputTokens") or 0
            slot["write"] += usage.get("cacheCreationInputTokens") or 0
    print(f"전체 · 세션 {len(sessions)} · {summary(tally(everything, all_resumes))}")
    for model, slot in sorted(models.items()):
        print(f"cost-state · {model} · in {slot['in']:,} · read {slot['read']:,} · write {slot['write']:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
