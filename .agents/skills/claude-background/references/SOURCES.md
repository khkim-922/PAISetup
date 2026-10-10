# 출처 — claude-background

보관본은 없다 — 상류 저장소에 라이선스 고지가 없어 원문을 묶지 않고 인용만 한다.

## 인용만 한 원문

- `sejuone-cloud/pgpt-one-click-connect` · `app/optional-skills/pgpt-delegate/scripts/Invoke-PgptAgent.ps1` 의 Claude 작업자
  갈래(65e981a · 2026-10-09) — 사내 P-GPT 게이트웨이를 거쳐 어느 호스트에서든 Claude Code 작업자를 띄우는 실행기.
  빌린 것: 플래그 다섯(`--strict-mcp-config` · `--disable-slash-commands` · `--permission-mode dontAsk` · `--tools` ·
  `--allowedTools`), 결과를 가르는 법(`result` 이벤트의 `subtype` · `is_error` · `permission_denials` · 빈 답).
  일부러 가른 것:
  - **도구** — 상류는 쓰기 · 셸까지 연다(실행 위임). 여기는 기본이 읽기 · 찾기 · 웹 읽기뿐이고(결정 0098), 고치기 레인도
    편집 도구 둘을 작업 자리 안에만 더할 뿐 셸은 안 연다(결정 0100)
  - **설정** — 상류는 `--setting-sources ''` 로 설정을 다 끄고 게이트웨이 값을 환경변수로 직접 넣는다(자리를 안다).
    이 러너는 자리를 모르므로 사용자 설정을 읽고 훅만 끈다(`disableAllHooks`)
  - **대화 남기기** — 상류는 `--no-session-persistence` 로 매번 새 대화다. 여기는 남긴다 — 봉투의 「이어 묻기」가 선다
  - **작업 규칙** — 상류는 `--append-system-prompt` 로 작업자 규칙을 붙인다. 여기는 안 붙인다 — 규칙은 봉투가 든다(0095)
  - **되맡기기 막기** — 상류는 환경변수 표지(`PGPT_DELEGATE_ACTIVE`)로 막는다. 여기는 셸 도구가 없어 다시 띄울 길이 없다
  - **실행 파일** — 상류는 셔틀(`.cmd`)을 피해 네이티브 `claude.exe` 만 찾는다(꾸러미 안 `bin/claude.exe` 자리를 포함해).
    여기는 셔틀이면 꾸러미 `package.json` 의 `bin` 을 따라간다 — JS 면 node 로, 실행 파일이면 그대로 부른다. 판에 따라
    둘 다 온다. 프롬프트는 표준 입력이라 cmd.exe 를 안 탄다

## 실측

- Claude Code 2.1.295 · 2026-10-09 · 리눅스 — 위 플래그로 띄우니 `system init` 의 `tools` 가 읽기 다섯뿐이었고,
  파일에 덧붙이라는 요청에 「쓸 도구가 없다」로 답하고 파일은 그대로였다. 이벤트 꼴: `system init`(`model` · `tools`) →
  `assistant`(`tool_use` · `name`) → `user`(`tool_result`) → `assistant`(`text`) → `result`(`subtype` · `is_error` ·
  `result` · `session_id` · `permission_denials` · `usage` · `api_error_status`). 래퍼 검사의 지은 표본이 이 꼴을 따른다
- 같은 실측 — 부른 쪽이 Claude 리모트 세션이면 받는 쪽이 부른 쪽과 같은 대화 id 로 섰다. `CLAUDECODE` ·
  `CLAUDE_CODE_SESSION_ID` 를 걷어도 그대로였고 `CLAUDE_CODE_REMOTE_SESSION_ID` 까지 걷어야 새 id 가 섰다. 래퍼가 세
  변수를 걷는 까닭이다 — 로컬 Claude 세션에서 어느 것이 그 일을 하나는 안 쟀다
- Claude Code 2.1.296 · 2026-10-10 · 리눅스 · 하이쿠 — 고치기 레인 꼴(`--tools` 에 `Edit,Write` 를 더하고 `--allowedTools` 는
  `Edit(./**),Write(./**)`)로 띄워, 자리 안 파일 하나를 고치고 자리 밖 파일 하나를 쓰라고 했다. 자리 안 `Edit` 은 섰고 자리 밖
  `Write` 는 `permission_denials` 에 실려 거절됐으며 그 파일은 안 생겼다. 부른 쪽이 자동 모드 Claude 세션이었는데 분류기가 그
  띄우기를 막지 않았다(결정 0100)
