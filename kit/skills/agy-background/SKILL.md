---
name: agy-background
description: "agy(Antigravity CLI · 제미나이)에게 일을 맡기고 거둘 때 부른다 — Claude 에서는 백그라운드로 띄워 두고 끝나면 알림으로, Codex 에서는 끝날 때까지 기다려 답을 읽는다. 긴 조사 · 큰 코드나 여러 파일 읽기 · 분석 · 리뷰 · 다른 모델의 의견 · 작업 자리를 따로 세운 실험은 사람이 짚지 않아도 맡길 거리다. 맡길 프롬프트는 agent-envelope 로 짓는다. 「agy 한테 시켜」·「제미나이로 조사시켜」·「오래 걸리는 조사 맡기자」·「제미나이 의견도 들어 보자」."
---

# agy 에게 맡긴다 — 울타리는 작업 자리뿐

agy 는 권한을 묻지 않고 돈다. 봉투의 금지는 부탁이고 울타리는 `--cwd` 다 — 조사만 시키면 스크래치패드를 주고, 저장소를 줬으면
끝난 뒤 `git status --porcelain` 으로 남긴 것을 본다. 이 대화를 모르니 프롬프트가 일의 전부다 — 무엇을 맡기고 어떻게 쓰나는
agent-envelope 가 든다. 공식 리뷰는 비대화에서 안 펼쳐지니 리뷰도 다른 일처럼 봉투로 맡긴다.

## 부르는 꼴

프롬프트를 파일로 쓰고 래퍼 하나로 띄운다. 인자 · 모델 고르기와 넘김 · 끝 줄의 칸 · 종료 값 · 이어 묻기는 `--help` 가 든다:

    python "<이 스킬 폴더>/scripts/agy_bg.py" --help

- **Claude 에서는** Bash 를 `run_in_background: true` 로 부르고 `pythonw` 로 띄운다 — 다른 것으로 감싸면 창이 뜬다. 끝 알림 뒤
  `--out` 을 읽는다. 윈도 밖에서는 `python3`
- **Codex 에서는** 콘솔 있는 `python` 으로 부르고 끝날 때까지 기다리되 **샌드박스 밖에서 돌린다** — 셸 호출에
  `sandbox_permissions: "require_escalated"` 와 허락을 묻는 한 줄(`justification`)을 싣는다. 샌드박스 안은 망이 닫혀 agy 가 첫
  요청에서 지고, 승인 정책이 `never` 인 자리(`codex exec` 기본)에서는 이 길이 없다

## 거둘 때

- **교차 검증으로 맡겼으면 끝 줄 `model=` 이 Claude 와 다른 계열인지 본다** — 넘김 차례는 자리 값이 정해 어느 계열이든 들 수 있다
- 심부름(훑기 · 찾기 · 요약)은 `--model "$AGY_DEFAULT_MODEL"` 로 띄운다 — 자리마다 어느 무게에 어느 모델인가는
  [`models.conf`](../agent-envelope/models.conf) 가 든다
