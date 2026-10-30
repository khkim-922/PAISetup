---
name: codex-copilot-background
description: "Codex 에게 일을 맡기고 거둘 때 부른다 — Claude 에서는 띄워 두고 대화를 잇다가 끝나면 알림으로, agy 에서는 끝날 때까지 기다려 답을 읽고, 자리 값이 허락하면 Codex 한도에서 Copilot 이 받는다. 긴 조사 · 큰 코드나 여러 파일 읽기 · 분석 · 리뷰 · 다른 모델 계열의 의견 · 웹 조사를 Claude 맥락 밖으로 넘길 때 부른다. 맡길 프롬프트는 agent-envelope 로 짓는다. 「코덱스한테 시켜」·「코파일럿으로 돌려」·「코덱스한테 리뷰 받아 보자」·「웹 조사 맡기자」."
---

# Codex · Copilot 에게 맡긴다 — 기본은 읽기, 쓰기는 작업 자리 안만

권한은 부를 때 일에 맞춰 고른다(무엇을 줄지는 agent-envelope 2 절 「자료 · 도구」). `--write` 가 없으면 Codex 는 읽기 전용
샌드박스에 앱 · 플러그인 · MCP 를 끄고 승인 `never` 로, Copilot 은 파일 읽기 · 웹 읽기 도구만 열고 뜬다 — 저장소를 통째로
가리켜도 된다. 이 대화를 모르니 프롬프트가 일의 전부다. Codex 레인은 제 홈의 규범(`~/.codex/AGENTS.md`)을 받는다(실측
2026-10-15).

## 부르는 꼴

프롬프트를 파일로 쓰고 이 스킬의 래퍼 하나로 띄운다. 받는 인코딩 · 플래그 · 끝 줄의 칸 · 종료 코드 · 이어 묻기는 래퍼의
도움말이 든다:

    python "<이 스킬 폴더>/scripts/codex_copilot_bg.py" --help

- **Claude 에서는** Bash 를 `run_in_background: true` 로 부르고 `pythonw` 로 띄운다 — 창 없이 돈다. 끝 알림 뒤 `--out` 을
  읽는다. 윈도 밖에서는 `python3`.
- **agy 에서는** 콘솔 있는 `python` 으로 부르고 끝날 때까지 기다린다(`pythonw` 는 셸이 안 기다린다). 명령의
  기다림(`WaitMsBeforeAsync`)은 `--timeout` 보다 길게 주고, 뒤로 넘어가면 끝난 뒤 `--out` 을 읽는다. 승인 건너뛰기 없이 뜬
  헤드리스 agy(`agy -p`)는 이 명령을 자동 거절한다 — 권한 설정을 고쳐 뚫지 말고 거절됐다고 알리고 멈춘다.

## 고치기 레인 — `--write`

고치기뿐 아니라 리뷰 · 재기처럼 돌려 보고 적어 봐야 하는 일에도 준다. **작업 자리(`--cwd`) 안만 고친다** — 따로 세워 주고, 본
트리를 주면 그 트리를 고친다. 이어 물을 때도 `--write` 를 다시 준다 — 안 주면 같은 대화가 읽기 레인으로 이어진다.

- **Codex** — 쓰기 샌드박스(`workspace-write`)로 뜨되 임시 폴더 변수(`TEMP` · `TMP` · `TMPDIR`)를 그 실행만의 빈 폴더로 돌리고
  `/tmp` 와 덧붙인 쓰기 자리는 끈다. 셸의 망은 닫혀 있고 앱 · 플러그인 · MCP 는 그대로 꺼진다.
- **Copilot** — 편집 도구를 더 열되 작업 자리 밖 쓰기는 경로 검사가 거절한다. **셸은 안 열린다** — 검사 돌리기는 맡긴 쪽이 한다.
  제 홈의 세션 폴더(`~/.copilot/session-state/<id>/`)에는 쓴다.

## 리뷰 모드 — `--review [대상]`

Codex 의 공식 리뷰(`$review-agent` — 이번 변경이 만든 것만 · 등급 · 0건 허용이 든다)로 시킨다. 읽기 레인 그대로 뜨고 그 안에서
git 읽기 명령이 돈다. 대상은 `uncommitted`(기본) · `base:<가지>` · `commit:<sha>` 이고 래퍼가 봉투 앞에 리뷰 부르기와 대상을
얹는다. 답은 `[P1] 제목 — 경로:줄` 꼴, 없으면 `No findings.`.

- **Copilot 은 리뷰 모드를 안 받는다** — 리뷰에 드는 셸을 읽기로 가둘 길이 없다(`git diff --output=<파일>` 이 작업 자리에 쓴다).
  Codex 가 한도여도 안 넘기고(2), `--agent copilot` 과 같이 주면 4 다. Copilot 리뷰는 읽기 레인에 봉투로.
- `--write` · `--resume` 과 같이 못 준다(4) — 리뷰는 읽기만 하는 새 대화다. 더 물을 때는 `--review` 없이 `resume=` 값으로 잇는다.

## 누가 받나 · 자리 값

자리마다 다른 값은 설치기가 심는 환경변수(`CC_BG_*`)이고 래퍼가 읽는다.

- **차례는 `CC_BG_AGENTS`**(없으면 Codex → Copilot). Codex 가 한도(사용 한도 · 할당량 · 용량 초과)면 다음 쪽이 받는다 — Copilot
  은 검색 없이 주소를 짐작해 열어서 공식 문서처럼 길이 뻔한 조사에 맞는다. 다른 실패와 시간 초과는 멈추고 까닭을 남긴다.
  여기 없는 쪽은 `--agent` · `--resume` 으로도 안 띄운다.
- **모델** — `--model` 이 없으면 맡기기 모델(`CC_BG_CODEX_MODEL_DELEGATE`) → 기본 모델(`CC_BG_CODEX_MODEL`) → Codex 설정의
  모델 차례다. 심부름(훑기 · 찾기 · 요약)은 `--model "$CC_BG_CODEX_MODEL"` 로. Copilot 은 제 모델로 뜬다. 자리마다 어느 무게에
  어느 모델인가는 [`models.conf`](../agent-envelope/models.conf) 가 든다.
- **웹 검색은 `CC_BG_CODEX_WEB_SEARCH`** — `disabled` 인 자리의 Codex 는 웹을 못 보니 웹이 드는 조사는 Claude 서브에이전트나
  agy 에게. `web=0` 인 답은 기억으로 낸 것이다 — 판 번호 · 날짜처럼 시점에 매인 답은 근거 URL 을 열어 맞춘 뒤 쓴다.
- 사내 게이트웨이는 답 하나를 요청부터 180초에 끊는다 — 긴 정리는 나눠 맡긴다.
- **로그인은 사람이 한 번** — Codex 는 `codex login`, Copilot 은 gh 로그인(`gh auth login`). gh 로그인이 무효라 졌으면 끝 줄
  바로 뒤에 그 말과 되살리는 명령이 선다 — 사람에게 그대로 전한다. API 키로 붙는 자리는 로그인이 없다.
