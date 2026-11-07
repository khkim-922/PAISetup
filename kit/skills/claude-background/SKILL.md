---
name: claude-background
description: "Claude 에게 일을 맡기고 답을 받을 때 부른다 — Codex 나 agy 가 맡기는 쪽이다. 긴 조사 · 큰 코드나 여러 파일 읽기 · 분석 · 리뷰 · 다른 모델 계열의 의견 · 웹 조사를 Claude 에게 넘길 때 쓰고, 봉투가 고치기를 고르면 작업 자리 안만 고치게 맡긴다. 맡길 프롬프트는 agent-envelope 로 짓는다. 「클로드한테 시켜」·「클로드 의견도 들어 보자」·「클로드한테 리뷰 받아 보자」."
---

# Claude 에게 맡긴다 — 쓰기는 작업 자리 안만

Codex 나 agy 가 Claude 를 부를 때의 러너다(Claude 안에서는 Agent 도구가 그 자리다). 권한은 부를 때 일에 맞춰 고른다(무엇을
줄지는 agent-envelope 2 절) — `--write` 가 없으면 읽기 레인, 있으면 작업 자리(`--cwd`) 안만 고치는 레인이다. 작업 자리는 따로
세워 준다 — 본 트리를 주면 그 트리를 고친다. 이 대화를 모르니 프롬프트가 일의 전부다. 리뷰는 내장 리뷰 스킬(`--review`)로
시킨다 — 봉투는 프롬프트 파일 그대로 주고, 모델은 깊은 리뷰면 [`models.conf`](../agent-envelope/models.conf) 의 것을 `--model` 로.

## 부르는 꼴

프롬프트를 파일로 쓰고 래퍼 하나로 띄운다. 인자 · 모드 셋 · 끝 줄의 칸 · 종료 값 · 이어 묻기 · 규범이 어떻게 실리나는 `--help`
가 든다:

    python "<이 스킬 폴더>/scripts/claude_bg.py" --help

- 콘솔 있는 `python` 으로 부르고 끝날 때까지 기다린다 — 명령의 시간 한도는 `--timeout` 보다 길게 준다(`pythonw` 는 셸이 안
  기다린다)
- **Codex 에서는 샌드박스 밖에서 돌린다** — 셸 호출에 `sandbox_permissions: "require_escalated"` 와 허락을 묻는 한 줄
  (`justification`)을 싣는다. 받는 Claude 는 망이 있어야 답하고, 샌드박스 안에서는 제 홈에 대화 기록을 못 써 이어 묻기가 안 선다.
  승인 정책이 `never` 인 자리(`codex exec` 기본)에서는 `-c sandbox_workspace_write.network_access=true` 로 띄워야 답이 오고 그래도
  이어 묻기는 안 선다
- **agy 에서는** 명령의 기다림(`WaitMsBeforeAsync`)을 `--timeout` 보다 길게 주고, 뒤로 넘어가면 끝난 뒤 `--out` 을 읽는다. 승인
  건너뛰기 없이 뜬 헤드리스 agy(`agy -p`)는 이 명령을 자동 거절한다 — 뚫지 말고 거절됐다고 알리고 멈춘다

## 맡기기 전에 가를 것

- **셸은 고치기 레인에도 없다** — 이 러너의 「재 볼 손」은 사본에 적어 보기까지다. 명령을 돌려 재야 하는 리뷰는 셸이 있는
  쪽(Claude 서브에이전트 · Codex 고치기 레인)에 맡기고, 검사 돌리기는 맡긴 쪽이 한다
- 파일 경로에 걸리는 룰은 레인에 안 온다 — 홈 규범은 래퍼가 싣는다(끝 줄 `norms=`)

## 사람만 하는 일

Claude Code CLI(`claude`)가 이 PC 에 서 있어야 한다 — 사외는 구독 로그인, 사내는 설치기가 심은 게이트웨이 값으로 붙는다. 인증
실패로 멈추면 터미널에서 `claude` 를 한 번 띄워 로그인하게 알린다.
