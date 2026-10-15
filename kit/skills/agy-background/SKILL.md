---
name: agy-background
description: "agy(Antigravity CLI · 제미나이)에게 일을 맡기고 거둘 때 부른다 — Claude 에서는 백그라운드로 띄워 두고 끝나면 알림으로, Codex 에서는 끝날 때까지 기다려 답을 읽는다. 긴 조사 · 큰 코드나 여러 파일 읽기 · 분석 · 리뷰 · 다른 모델의 의견 · 작업 자리를 따로 세운 실험은 사람이 짚지 않아도 맡길 거리다. 맡길 프롬프트는 agent-envelope 로 짓는다. 「agy 한테 시켜」·「제미나이로 조사시켜」·「오래 걸리는 조사 맡기자」·「제미나이 의견도 들어 보자」."
---

# agy 에게는 래퍼 하나로 맡긴다

Claude 에서는 띄워 두고 대화를 잇다가, 끝나면 알림으로 답을 거둔다. Codex 에서는 끝날 때까지 기다려 거둔다. agy 는 이
스킬의 래퍼 하나로 부르고, 이 세션의 셸이 직접 띄운다(서브에이전트로 감싸지 않는다). **agy 는 이 대화를 모르니 프롬프트가 일의 전부다** — 무엇을 맡기고 어떻게
쓰나는 agent-envelope 가 든다.

## 맡기는 법

1. **프롬프트를 UTF-8 파일로 쓴다**(스크래치패드). 큰 자료는 경로를 주고 agy 가 읽게 한다 — 래퍼는 명령줄 한도
   (`MAX_PROMPT_CHARS`)를 넘는 프롬프트를 안 받는다. PowerShell 5.1 이면 `Set-Content -Encoding utf8` 로 쓴다 — 다른
   인코딩이면 래퍼가 4 로 돌려보낸다.
2. **Claude 에서는 Bash 를 `run_in_background: true` 로 부르고, `pythonw` 로 띄운다** — 다른 것으로 감싸면 창이 뜬다.
   윈도 밖에서는 `python3` 로 부른다(재지 않았다).

   ```sh
   pythonw "<이 스킬 폴더>/scripts/agy_bg.py" --prompt-file <프롬프트> --out <답 파일> --cwd <작업 자리> \
     [--model "<이름>"] [--timeout <초>] [--conversation <id>]
   ```

   **Codex 에서는 같은 명령을 콘솔 있는 `python` 으로 부르고 끝날 때까지 기다린다** — `pythonw` 는 창 없는 프로그램이라
   셸이 안 기다리고 바로 돌아온다. 명령의 시간 한도는 `--timeout` 보다 길게 준다. **그리고 샌드박스 밖에서 돌린다** —
   셸 도구 호출에 `sandbox_permissions: "require_escalated"` 와 허락을 묻는 한 줄(`justification`)을 실어 승인을 받는다.
   Codex 의 `workspace-write` 샌드박스는 망을 닫아 agy 가 첫 요청에서 진다. 망만 열어도 그 안의 agy 는 제 홈
   (`~/.gemini`)에 대화를 못 남기고, API 키 후보의 홈(`%LOCALAPPDATA%\agy-bg\api-home`)을 못 지어 그 후보가 실패(1)로
   끝난다. 이 길은 승인 정책이 `on-request` 일 때(앱의 기본 `Auto`) 있다 — 출처:
   [Codex 문서 「Agent approvals & security」](https://developers.openai.com/codex/agent-approvals-security) ·
   [Codex 의 승인 요청 안내](https://github.com/openai/codex/blob/main/codex-rs/prompts/templates/permissions/approval_policy/on_request.md).
   `never` 인 자리(`codex exec` 기본)에서는 이 요청이 안 서니 agy 맡기기가 안 선다.

3. **끝나면 `--out` 파일을 읽는다.** 윈도에서는 BOM 붙은 UTF-8 이라 PowerShell 5.1 의 `Get-Content` 가 인코딩을 안 줘도
   한글을 그대로 읽는다. 끝 줄 `[agy-bg] <갈래> …` 이 갈래 · 모델 · 넘어간 자취 · `conversation` id 를 든다. 종료 코드
   0 일 때만 답이 온 것이고, 아니면 그 위의 agy 출력 · stderr · 로그 경로가 까닭을 든다 — API 키 후보의 홈을 못 지었거나
   러너가 멈춘 것도 1 로 까닭을 남긴다. 인자가 틀려도 `--out` 을 줬으면 그 파일에 까닭과 끝 줄이 남는다(4). 교차
   검증으로 맡겼으면 끝 줄 `model=` 이 Claude 와 다른 계열인지 본다 — 넘김 차례는 자리 값이 정해 어느 계열이든 들 수 있다.
4. **이어 물을 때**는 `--conversation <id>` 를 준다. 끝 줄 `model=` 이 `api:` 로 시작하면 그 이름도 `--model` 로 준다.
   대화가 안 남은 실행은 `conversation=-` 에 까닭을 달고 끝난다 — 그때는 새로 맡긴다.

## 리뷰

agy 의 공식 리뷰(`/review-agent` — 리뷰 서브에이전트를 띄운다)는 이 러너의 비대화(`-p`)에서 안 펼쳐진다 — 프롬프트를
`/review-agent` 로 시작해도 그 글이 그대로 요청으로 가고 본 에이전트가 직접 리뷰한다(실측 agy 1.3.5 · 2026-10-15). 그래서
리뷰는 다른 일처럼 봉투로 맡긴다. 러너는 권한을 묻지 않고 돌아 리뷰도 읽기만 한다는 보장이 없다 — 끝나면 `git status
--porcelain` 으로 남긴 것을 본다.

## 모델 — 래퍼가 고른다

- 자리마다 어느 무게에 어느 모델을 대나는 맡기기 스킬 폴더의 모델 표
  [`models.conf`](../agent-envelope/models.conf) 가 들고, 설치기가 그 표에서 아래 자리 값을 심는다.
- 래퍼는 설치기가 심은 자리 값(`AGY_*`)의 차례대로 모델을 고르고, 한도나 과부하면 다음 모델로 넘어간다 — 차례가
  다 막히면 종료 코드 2 다. **`--model` 을 주면 그 하나만 쓰고 안 넘어간다** — 이름은 `agy models` 의 표시 이름
  그대로다.
- 맡기기 모델(`AGY_MODEL_DELEGATE`)이 심긴 자리에서는 래퍼가 그것을 먼저 쓴다 — 추론이 안 드는 일(훑기 · 찾기 ·
  요약)은 `--model "$AGY_DEFAULT_MODEL"` 로 준다. 안 심긴 자리에서는 래퍼가 고르게 둔다.

## 작업 자리

agy 는 권한을 묻지 않고 돈다 — 프롬프트의 금지로는 못 막으니 **작업 자리로 막는다.**

- 조사만 시킬 때 `--cwd` 는 스크래치패드다.
- 저장소를 줬으면 끝난 뒤 `git status --porcelain` 으로 남긴 것을 본다.
