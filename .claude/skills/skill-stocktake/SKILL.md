---
description: "Claude 스킬과 명령의 품질을 감사할 때 사용합니다. 변경된 스킬만 보는 Quick Scan과 전체 검토를 수행하는 Full Stocktake 모드를 지원합니다."
origin: ECC
---

# skill-stocktake

품질 체크리스트와 AI의 총체적 판단을 결합해 Claude 스킬과 명령을 감사하는 슬래시 명령(`/skill-stocktake`)입니다. 최근 변경된 스킬만 다시 보는 Quick Scan과 전체 점검을 위한 Full Stocktake 두 모드를 지원합니다.

## 범위

이 명령은 **실행한 디렉터리 기준**으로 다음 경로를 대상으로 합니다.

| Path | Description |
|------|-------------|
| `~/.claude/skills/` | Global skills (all projects) |
| `{cwd}/.claude/skills/` | Project-level skills (if the directory exists) |

**1단계 시작 시, 어떤 경로를 찾았고 실제로 스캔했는지 명시적으로 출력해야 합니다.**

### 특정 프로젝트만 대상으로 할 때

프로젝트 수준 스킬을 포함하려면 해당 프로젝트 루트에서 실행합니다.

```bash
cd ~/path/to/my-project
/skill-stocktake
```

프로젝트에 `.claude/skills/` 디렉터리가 없으면 전역 스킬과 명령만 평가합니다.

## 모드

| Mode | Trigger | Duration |
|------|---------|---------|
| Quick Scan | `results.json` exists (default) | 5–10 min |
| Full Stocktake | `results.json` absent, or `/skill-stocktake full` | 20–30 min |

**Results cache:** `~/.claude/skills/skill-stocktake/results.json`

## Quick Scan 흐름

지난 실행 이후 변경된 스킬만 다시 평가합니다. 예상 시간은 5~10분입니다.

1. Read `~/.claude/skills/skill-stocktake/results.json`
2. Run: `bash ~/.claude/skills/skill-stocktake/scripts/quick-diff.sh \
         ~/.claude/skills/skill-stocktake/results.json`
   (Project dir is auto-detected from `$PWD/.claude/skills`; pass it explicitly only if needed)
3. If output is `[]`: report "No changes since last run." and stop
4. Re-evaluate only those changed files using the same Phase 2 criteria
5. Carry forward unchanged skills from previous results
6. Output only the diff
7. Run: `bash ~/.claude/skills/skill-stocktake/scripts/save-results.sh \
         ~/.claude/skills/skill-stocktake/results.json <<< "$EVAL_RESULTS"`

## Full Stocktake 흐름

### 1단계 — 인벤토리

Run: `bash ~/.claude/skills/skill-stocktake/scripts/scan.sh`

스크립트는 스킬 파일을 열거하고, 프론트매터를 추출하고, UTC mtime을 수집합니다.
프로젝트 디렉터리는 `$PWD/.claude/skills`에서 자동 감지되며, 필요한 경우에만 명시적으로 전달합니다.
스크립트 출력에서 스캔 요약과 인벤토리 표를 그대로 제시합니다.

```
Scanning:
  ✓ ~/.claude/skills/         (17 files)
  ✗ {cwd}/.claude/skills/    (not found — global skills only)
```

| Skill | 7d use | 30d use | Description |
|-------|--------|---------|-------------|

### 2단계 — 품질 평가

전체 인벤토리와 체크리스트를 넘겨 Agent 도구 서브에이전트(**general-purpose agent**)를 실행합니다.

```text
Agent(
  subagent_type="general-purpose",
  prompt="
Evaluate the following skill inventory against the checklist.

[INVENTORY]

[CHECKLIST]

Return JSON for each skill:
{ \"verdict\": \"Keep\"|\"Improve\"|\"Update\"|\"Retire\"|\"Merge into [X]\", \"reason\": \"...\" }
"
)
```

서브에이전트는 각 스킬을 읽고 체크리스트를 적용한 뒤, 스킬별 JSON을 반환합니다.

`{ "verdict": "Keep"|"Improve"|"Update"|"Retire"|"Merge into [X]", "reason": "..." }`

**청크 가이드:** 컨텍스트를 감당 가능한 수준으로 유지하려면 서브에이전트 1회 호출당 약 20개 스킬씩 처리합니다. 각 청크 후 `results.json`에 중간 결과를 저장하고 `status: "in_progress"`로 표시합니다.

모든 스킬 평가가 끝나면 `status: "completed"`로 바꾸고 3단계로 진행합니다.

**재개 감지:** 시작 시 `status: "in_progress"`가 있으면 첫 번째 미평가 스킬부터 이어서 진행합니다.

각 스킬은 다음 체크리스트로 평가합니다.

```
- [ ] Content overlap with other skills checked
- [ ] Overlap with MEMORY.md / CLAUDE.md checked
- [ ] Freshness of technical references verified (use WebSearch if tool names / CLI flags / APIs are present)
- [ ] Usage frequency considered
```

판정 기준:

| Verdict | Meaning |
|---------|---------|
| Keep | Useful and current |
| Improve | Worth keeping, but specific improvements needed |
| Update | Referenced technology is outdated (verify with WebSearch) |
| Retire | Low quality, stale, or cost-asymmetric |
| Merge into [X] | Substantial overlap with another skill; name the merge target |

평가는 **총체적 AI 판단**이며 수치형 루브릭이 아닙니다. 주요 관점은 다음과 같습니다.
- **Actionability**: code examples, commands, or steps that let you act immediately
- **Scope fit**: name, trigger, and content are aligned; not too broad or narrow
- **Uniqueness**: value not replaceable by MEMORY.md / CLAUDE.md / another skill
- **Currency**: technical references work in the current environment

**근거 품질 요구사항** — `reason` 필드는 자기완결적이어야 하고 의사결정에 바로 쓸 수 있어야 합니다.
- Do NOT write "unchanged" alone — always restate the core evidence
- For **Retire**: state (1) what specific defect was found, (2) what covers the same need instead
  - Bad: `"Superseded"`
  - Good: `"disable-model-invocation: true already set; superseded by continuous-learning-v2 which covers all the same patterns plus confidence scoring. No unique content remains."`
- For **Merge**: name the target and describe what content to integrate
  - Bad: `"Overlaps with X"`
  - Good: `"42-line thin content; Step 4 of chatlog-to-article already covers the same workflow. Integrate the 'article angle' tip as a note in that skill."`
- For **Improve**: describe the specific change needed (what section, what action, target size if relevant)
  - Bad: `"Too long"`
  - Good: `"276 lines; Section 'Framework Comparison' (L80–140) duplicates ai-era-architecture-principles; delete it to reach ~150 lines."`
- For **Keep** (mtime-only change in Quick Scan): restate the original verdict rationale, do not write "unchanged"
  - Bad: `"Unchanged"`
  - Good: `"mtime updated but content unchanged. Unique Python reference explicitly imported by rules/python/; no overlap found."`

### 3단계 — 요약 표

| Skill | 7d use | Verdict | Reason |
|-------|--------|---------|--------|

### 4단계 — 통합 정리

1. **Retire / Merge**: present detailed justification per file before confirming with user:
   - What specific problem was found (overlap, staleness, broken references, etc.)
   - What alternative covers the same functionality (for Retire: which existing skill/rule; for Merge: the target file and what content to integrate)
   - Impact of removal (any dependent skills, MEMORY.md references, or workflows affected)
2. **Improve**: present specific improvement suggestions with rationale:
   - What to change and why (e.g., "trim 430→200 lines because sections X/Y duplicate python-patterns")
   - User decides whether to act
3. **Update**: present updated content with sources checked
4. Check MEMORY.md line count; propose compression if >100 lines

## 결과 파일 스키마

`~/.claude/skills/skill-stocktake/results.json`:

**`evaluated_at`**: 평가 완료의 실제 UTC 시각이어야 합니다.
Bash로는 `date -u +%Y-%m-%dT%H:%M:%SZ`를 사용합니다. `T00:00:00Z` 같은 날짜-only 근사값은 쓰지 않습니다.

```json
{
  "evaluated_at": "2026-02-21T10:00:00Z",
  "mode": "full",
  "batch_progress": {
    "total": 80,
    "evaluated": 80,
    "status": "completed"
  },
  "skills": {
    "skill-name": {
      "path": "~/.claude/skills/skill-name/SKILL.md",
      "verdict": "Keep",
      "reason": "Concrete, actionable, unique value for X workflow",
      "mtime": "2026-01-15T08:30:00Z"
    }
  }
}
```

## 참고사항

- 평가는 블라인드 방식입니다. 출처(ECC, 직접 작성, 자동 추출)와 무관하게 동일한 체크리스트를 적용합니다.
- 아카이브/삭제 작업은 항상 사용자 명시적 확인이 필요합니다.
- 스킬 출처에 따라 판정 기준을 달리하지 않습니다.
