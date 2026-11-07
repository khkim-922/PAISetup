---
name: codex-copilot-background
description: "Codex 에게 일을 맡기고 거둘 때 부른다 — Claude 에서는 띄워 두고 대화를 잇다가 끝나면 알림으로, agy 에서는 끝날 때까지 기다려 답을 읽고, 자리 값이 허락하면 Codex 한도에서 Copilot 이 받는다. 긴 조사 · 큰 코드나 여러 파일 읽기 · 분석 · 리뷰 · 다른 모델 계열의 의견 · 웹 조사를 Claude 맥락 밖으로 넘길 때 부른다. 맡길 프롬프트는 agent-envelope 로 짓는다. 「코덱스한테 시켜」·「코파일럿으로 돌려」·「코덱스한테 리뷰 받아 보자」·「웹 조사 맡기자」."
---

# Codex · Copilot 에게 맡긴다 — 기본은 읽기, 쓰기는 작업 자리 안만

권한은 부를 때 일에 맞춰 고른다(무엇을 줄지는 agent-envelope 2 절) — `--write` 가 없으면 읽기 레인, 있으면 작업 자리(`--cwd`)
안만 고치는 레인이다. 작업 자리는 따로 세워 준다 — 본 트리를 주면 그 트리를 고친다. 이 대화를 모르니 프롬프트가 일의 전부다.
리뷰는 Codex 의 공식 리뷰(`--review`)로 시킨다 — Copilot 은 리뷰에 드는 셸을 읽기로 가둘 길이 없어 리뷰 모드를 안 받으니,
Copilot 리뷰는 읽기 레인에 봉투로.

## 부르는 꼴

프롬프트를 파일로 쓰고 래퍼 하나로 띄운다. 인자 · 모드 셋 · 누가 받나의 차례 · 자리 값 · 끝 줄의 칸 · 종료 값 · 이어 묻기는
`--help` 가 든다:

    python "<이 스킬 폴더>/scripts/codex_copilot_bg.py" --help

- **Claude 에서는** Bash 를 `run_in_background: true` 로 부르고 `pythonw` 로 띄운다 — 창 없이 돈다. 끝 알림 뒤 `--out` 을 읽는다.
  윈도 밖에서는 `python3`
- **agy 에서는** 콘솔 있는 `python` 으로 부르고 끝날 때까지 기다린다. 명령의 기다림(`WaitMsBeforeAsync`)은 `--timeout` 보다 길게
  주고, 뒤로 넘어가면 끝난 뒤 `--out` 을 읽는다. 승인 건너뛰기 없이 뜬 헤드리스 agy(`agy -p`)는 이 명령을 자동 거절한다 —
  권한 설정을 고쳐 뚫지 말고 거절됐다고 알리고 멈춘다

## 맡기기 전에 가를 것

- **웹이 드는 조사** — 자리 값 `CC_BG_CODEX_WEB_SEARCH` 가 `disabled` 인 자리의 Codex 는 웹을 못 보니 Claude 서브에이전트나
  agy 에게. 판 번호 · 날짜처럼 시점에 매인 답은 끝 줄 `web=` 이 0 이면 기억이라 근거 URL 을 열어 맞춘 뒤 쓴다
- **검사 돌리기는 맡긴 쪽이 한다** — Copilot 이 받은 고치기 레인에는 셸이 없다
- 사내 게이트웨이는 답 하나를 요청부터 180초에 끊는다 — 긴 정리는 나눠 맡긴다
- 심부름(훑기 · 찾기 · 요약)은 `--model "$CC_BG_CODEX_MODEL"` 로 — 자리마다 어느 무게에 어느 모델인가는
  [`models.conf`](../agent-envelope/models.conf) 가 든다

## 사람만 하는 일

로그인 한 번 — Codex 는 `codex login`, Copilot 은 `gh auth login`. gh 로그인이 무효라 졌으면 끝 줄 바로 뒤의 말과 되살리는 명령을
사람에게 그대로 전한다. API 키로 붙는 자리는 로그인이 없다.
