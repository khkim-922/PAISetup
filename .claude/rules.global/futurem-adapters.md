---
paths:
  - "**/adapters/**"
---

<!-- 생성물 — scripts/pull-vibecoding.sh 가 씨앗의 continue-rules/futurem-adapters.md 에서 굽는다. 손으로 고치지 않는다(결정 0074). -->

> **회사가 쓴 사내 FastAPI 코딩 기준이다.** 아래 본문은 회사 원본 그대로다.
>
> - **사내 FastAPI 앱이 아니면 이 룰을 무시한다.** 걸리는 경로(`main.py` · `services/` 같은)는
>   흔한 이름이라 무관한 프로젝트에서도 걸린다. 사내 앱의 표지 — 원격이 회사 GitLab 이다 ·
>   `.futurem-prompts/` 나 `adapters/llm_gateway` 가 있다 · 사용자가 사내 앱이라고 했다. 표지가
>   하나도 없으면 이 기준으로 코드를 고치거나 요청을 막지 않는다.
> - 본문의 `docs/…` 경로는 **씨앗 뿌리** 기준이다 — `~/.claude/seeds/vibecoding/`(없으면
>   claude-config 의 `seeds/vibecoding/`).
> - 본문이 말하는 VS Code · Continue · PGPT 는 회사 원본이 겨눈 도구다. 규약은 도구와 무관하게
>   이 세션에도 선다.

`docs/references/futurem-adapters.md`를 참고하라.

adapters 레이어 상세 규약은 logger, LLM gateway, preprocess, 외부 시스템 연동, 금지 목록을 포함한다.
