"""measure.sh 의 runs/*.jsonl 에서 판마다 — 연 스킬 · 읽은 파일 · 끝 글 — 을 뽑아 runs/<열쇠>.<팔>.txt 로 쓰고 한 줄 요약을 찍는다.

    python -X utf8 -I extract.py <결과 폴더>

요약 한 줄 — 열쇠.팔 · 연 스킬(걸리나) · 읽은 파일 수(「없을 때」 팔이 홈의 옛 사본을 찾아 읽었나) · 끝 글의 길이 · 비용.
"""
import json, pathlib, sys

out = pathlib.Path(sys.argv[1]).resolve()
for f in sorted((out / "runs").glob("*.jsonl")):
    skills, reads, result, cost = [], [], "", 0.0
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "assistant":
            for b in d.get("message", {}).get("content", []):
                if b.get("type") == "tool_use":
                    name, inp = b.get("name"), b.get("input", {})
                    if name == "Skill":
                        skills.append(inp.get("skill") or inp.get("name") or "?")
                    elif name == "Read":
                        reads.append(pathlib.Path(str(inp.get("file_path", ""))).name)
        elif d.get("type") == "result":
            result = d.get("result", "") or ""
            cost = float(d.get("total_cost_usd", 0) or 0)
    (out / "runs" / (f.stem + ".txt")).write_text(
        f"# {f.stem}\n스킬: {', '.join(skills) or '없음'}\n읽음: {', '.join(reads) or '없음'}\n\n{result}\n", encoding="utf-8")
    print(f"{f.stem:16s} 스킬={','.join(skills) or '-':24s} 읽음={len(reads):2d} 글={len(result):5d}자 ${cost:.2f}")
