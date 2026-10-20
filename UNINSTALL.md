# 무를 때

PC 를 반납하거나 부서를 옮기거나 회사 게이트웨이를 떠나 개인 구독으로 돌아갈 때, 설치가 남긴 것을 지우는 차례를 적은 글이다.

되돌리는 스위치는 아직 없어 아래를 손으로 지운다. 몇 가지는 설치 창에서 그 도구나 칸을 빼고 한 번 더 누르면 설치가 걷는다.
여기 나오는 말(놓는 프로그램 · 경계 표시 줄 · 견본 폴더)은 [INSTALLED.md 「이 글에 나오는 말」](INSTALLED.md#이-글에-나오는-말)이 푼다.

## 목차

- [지우는 차례](#지우는-차례)
- [게이트웨이 주소](#게이트웨이-주소)
- [설치를 다시 눌러 걷히는 것](#설치를-다시-눌러-걷히는-것)
- [손으로 지울 것](#손으로-지울-것)
- [남겨도 되는 것](#남겨도-되는-것)
- [사외에서 다시 누르면](#사외에서-다시-누르면)

## 지우는 차례

아래 차례 둘을 지켜야 지운 것이 되살아나지 않고 헛도는 것도 안 남는다.

1. [자동 실행 작업](#자동-실행-작업) 둘을 맨 먼저 지운다 — 남아 있으면 로그온 · 밤마다 설치가 다시 돌아 지운 것을 도로 깐다
2. [`~/.paisetup` 과 고른 도구 값](#paisetup-폴더와-고른-도구-값)은 다른 것을 다 지운 뒤 지운다 — 홈의 가져오기 줄 · 가리킴 파일 ·
   Claude 훅 등록이 이 폴더를 가리킨다

## 게이트웨이 주소

⚠ 자동 실행 작업 다음으로 급한 것은 `ANTHROPIC_BASE_URL` 이다.

이 값이 사내 로컬 프록시를 가리킨 채로 남으면, 사외로 나간 노트북의 Claude 가 돌지도 않는 프록시로 요청을 보낸다 — 프로그램을 다
지워도 이 줄 하나가 남으면 그렇다. 이 값은 사용자 환경변수와 홈 설정(`~/.claude/settings.json`) 두 곳에 있으니 둘 다 지운다.

## 설치를 다시 눌러 걷히는 것

아래는 설치 창에서 그 칸을 빼고 한 번 더 누르면 설치가 우리 것만 걷는다.

| 설치 창에서 | 걷히는 것 |
|---|---|
| Claude 를 뺀다 | 홈 설정의 Claude 훅 등록을 놓는 프로그램이 걷는다 |
| 안티그래비티를 뺀다 | `~/.gemini/config/hooks.json` 의 우리 항목 셋을 걷는다(꺼 둔 것도) |
| Codex 를 뺀다 | `~/.codex/config.toml` 의 우리 훅을 걷는다 — 파이썬 3.11 이상이 있을 때만이고, 없으면 노란 줄로 알리고 남긴다 |
| 브라우저 MCP 를 단 도구를 뺀다 | 그 도구의 `playwright` 등록 가운데 우리 것만 걷는다 |
| 제작자 칸을 다 끈다 | 놓는 프로그램이 제가 놓은 규범 · 룰 · 에이전트 · 스킬을 걷는다 |
| 자동 실행 칸을 끈다 | 자동 실행 작업과 딸린 파일을 걷고, 끈 것을 적어 두어 다음 창도 이 칸을 꺼진 채로 띄운다 |

손으로 할 때도 아래 [손으로 지울 것](#손으로-지울-것)의 같은 자리들이다.

## 손으로 지울 것

손으로 지울 것은 자리마다 아래에 모았고, 사람이 쓰던 것일 수 있는 나머지는 둔다.

### 자동 실행 작업

로그온 · 밤마다 도는 자동 실행 작업 `PAISetup-AutoRun` · `PAISetup-AutoRun-Night` 은 「작업 스케줄러」를 열어 두 이름을 지운다.

```powershell
Unregister-ScheduledTask -TaskName PAISetup-AutoRun,PAISetup-AutoRun-Night -Confirm:$false
```

⚠ 다른 무엇보다 이것을 먼저 지운다 — [지우는 차례](#지우는-차례).

### 사용자 환경변수

설치가 심은 사용자 환경변수는 시작 메뉴에서 「환경 변수」로 검색해 「계정의 환경 변수 편집」에서 지운다.

- 펴진 묶음의 `install.env` 에 값이 적힌 이름 전부(`ANTHROPIC_BASE_URL` · `GOOGLE_GEMINI_BASE_URL` · `ANTHROPIC_MODEL` 등)
- 키 셋 `ANTHROPIC_AUTH_TOKEN` · `OPENAI_API_KEY` · `GEMINI_API_KEY`
- `NODE_EXTRA_CA_CERTS` 와 그것이 가리키는 파일 `~/.claude/node-ca.pem` — 값이 그 파일일 때만 지우고, 다른 파일을 가리키면 사람이
  넣은 것이라 그대로 둔다. 회사 망에서 npm · VS Code 확장을 계속 쓰면 남긴다 — Node 는 이 파일이 있어야 회사 망의 인증서를 믿는다
- 지운 뒤 창을 새로 연다

맡기기 값과 고른 도구 값은 아래 칸마다 따로 적었다.

### Claude 홈 설정

`~/.claude/settings.json` 에서 설치가 넣은 줄만 지우고, 나머지는 사람이 쓰던 설정일 수 있으니 둔다.

- `env` 칸에서 이 글이 지우라는 사용자 환경변수와 같은 이름들
- `modelPicker` 칸과 `skipWebFetchPreflight` 칸
- 설치기 폴더의 기록 `%LOCALAPPDATA%\Claude Code Setup\claude-settings.tsv` 에 적힌 `permissions` 의 값 — `defaultMode` 와 `allow` 의
  `pythonw` 러너 줄 — 과 그 기록 파일
- `hooks` 의 `SessionStart` 에서 `command` 에 `/*/.claude/hooks/session-start.sh` 가 든 우리 항목 하나 — 설치가 매번 다시 심고,
  설치 창에서 무엇을 빼도 안 걷힌다
- `hooks` 의 우리 훅 줄 — 아래 표. 이 줄들은 설치 창에서 Claude 를 빼고 한 번 더 누르면 놓는 프로그램이 우리 것만 걷는다

| `hooks` 의 이벤트 | 지울 줄 |
|---|---|
| `PreToolUse` | `image-gate` · `bash-backslash-deny` · `shell-slip` · `lane-resume` · `drm-guide` |
| `PostToolUse` | `utf8-bom` · `web-retry` |
| `PostToolUseFailure` | `web-retry` · `drm-guide` |
| `UserPromptSubmit` | `drm-guide` · `context-alert` |

### 워드의 PDF 변환 안내

워드가 깔린 PC 면 `HKCU\Software\Microsoft\Office\<판>\Word\Options` 의 `DisableConvertPdfWarning` 을 지운다(판은 대개 `16.0`).

```powershell
Remove-ItemProperty 'HKCU:\Software\Microsoft\Office\16.0\Word\Options' -Name DisableConvertPdfWarning
```

지우면 PDF 를 워드로 열 때 안내가 다시 뜨고, 스킬 `drm-office-read` 는 그 PC 에서 PDF 를 워드로 못 연다. 설치를 다시 누르면(로그온
자동 실행도) 다시 1 로 둔다.

### 프록시 감시 작업

로그인마다 뜨는 프록시 감시 작업 `PGPTProxy-Watchdog` 은 「작업 스케줄러」를 열어 그 이름을 지운다.

```powershell
Unregister-ScheduledTask -TaskName PGPTProxy-Watchdog -Confirm:$false
```

프록시가 도는 폴더 `%LOCALAPPDATA%\PGPT-Proxy` 도 지운다. 옛 판이 남긴 것은 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 의
`PGPTProxy` 다.

### 홈에 깔린 환경 자료

`~/.claude/posco/` 와 `~/.claude/seeds/` 폴더를 지운다.

`~/.node_modules/` 안의 연결(pptxgenjs · @commitlint 폴더 안의 config-conventional)도 지운다 — 저장소 밖에 사는 스킬 스크립트가 npm
전역 패키지를 찾게 설치가 걸어 둔 정션이다. 연결만 지우면 npm 전역의 실물은 남는다. ⚠ `Remove-Item -Recurse` 로 지우지 않는다 —
정션 너머 실물까지 지울 수 있다. `cmd /c rmdir "%USERPROFILE%\.node_modules\pptxgenjs"` 처럼 연결을 하나씩 걷고, 빈 폴더가
남으면 그것만 지운다.

견본 폴더 곁에 깔린 파이썬 패키지는 `python -m pip uninstall pillow` 로 지운다 — 다른 프로그램도 쓸 수 있으니 필요할 때만 지운다.

### 칸 없이 깔린 스킬

제작자 칸을 끈 도구의 홈에서 기록에 적힌 이름의 스킬 폴더와 그 기록, 옮겨 둔 백업을 지운다.

| 도구 | 스킬 자리 | 기록 | 백업 자리 |
|---|---|---|---|
| Claude | `~/.claude/skills/` | `~/.claude/.paisetup-skills` | `~/.claude/backups/` |
| Codex | `~/.agents/skills/` | `~/.agents/.paisetup-skills` | `~/.agents/backups/` |
| 안티그래비티 | `~/.gemini/config/skills/` | `~/.gemini/.paisetup-skills` | `~/.gemini/backups/` |

- 백업 자리의 `install-skills-*` 는 걷은 스킬을 옮겨 둔 것이고, `install-aside-*` 는 같은 이름이라 비켜 둔 것이다 — 사람 것이면 되살린다
- 스킬 폴더에는 사람이 둔 스킬도 사니 기록에 없는 이름은 둔다

### 안티그래비티의 훅

설치 창에서 안티그래비티를 빼고 한 번 더 누르면 설치가 걷는다.

손으로는 `~/.gemini/config/hooks.json` 의 `paisetup-drm-guide` · `paisetup-utf8-bom` · `paisetup-context-alert` 항목을 지운다. 다른
항목은 사람이 넣은 것일 수 있으니 두고, 고치기 전 것은 곁의 `hooks.json.before-paisetup-*` 에 있다.

### 브라우저 MCP

설치 창에서 그 도구를 빼고 한 번 더 누르면 설치가 우리 등록만 걷는다.

```powershell
claude mcp remove -s user playwright
codex mcp remove playwright
agy mcp remove playwright
```

- 지우기 전에 그 항목이 우리 것(명령 `node` · 첫 인자가 `browser-mcp.mjs`)인지 본다
- Codex 를 고치기 전 것은 `config.toml.before-browser-mcp-<시각>` 에 있다
- 꾸러미는 `npm uninstall -g playwright`, 받은 브라우저는 `%USERPROFILE%\.cache\ms-playwright\chromium-snapshot-*` 폴더다

### 묻지 않고 돌기

고른 agy · Copilot · Codex 에 심은 묻지 않고 돌기 설정은 설치가 걷지 않는다.

손으로 지우거나, 그 도구의 설정 화면에서 다른 값을 고른다.

| 도구 | 지울 자리 |
|---|---|
| agy CLI | `~/.gemini/antigravity-cli/settings.json` 의 `toolPermission` |
| agy 데스크탑 앱 | `~/.gemini/config/config.json` 의 `userSettings` 세 칸 |
| Copilot CLI | `~/.copilot/settings.json` 의 `defaultPermissionMode` · `defaultMode` |
| Codex CLI | `~/.codex/config.toml` 맨 위의 `approvals_reviewer` 줄 |

### 제작자 칸이 놓은 것

설치 창에서 제작자 칸을 다 끄고 한 번 더 누르면 놓는 프로그램이 제가 놓은 것을 걷는다.

손으로 할 때도 아래 자리들이고, 경계 표시 줄 밖은 사람이 쓴 글이다.

- `~/.claude/CLAUDE.md` 와 `~/.codex/AGENTS.md` 의 경계 표시 줄(`<!-- paisetup:norms BEGIN -->` · `END`) 사이
- `~/.gemini/config/AGENTS.md` · `~/.gemini/config/rules.json`
- 기록 `~/.paisetup/placed.tsv` 에 든 룰 · 에이전트 · 스킬 사본

### paisetup 폴더와 고른 도구 값

`~/.paisetup/` 폴더와 사용자 환경변수 `PAISETUP_PERSONAL` · `PAISETUP_PICK` · `PAISETUP_SITE` 는 다른 칸을 다 지운 뒤 지운다.

폴더에는 두 층 `~/.paisetup/standard/` · `~/.paisetup/personal/` 과 기록 `~/.paisetup/placed.tsv`, 덮거나 걷기 전에 떠 둔 백업
`~/.paisetup/backups/` 가 든다 — 백업에 사람 것이 들었으면 되살린다.

### agy 맡기기 값

Claude · 안티그래비티를 같이 골랐으면 사용자 환경변수 `AGY_DEFAULT_MODEL` · `AGY_FALLBACK_MODELS` · `AGY_MODEL_DELEGATE` 를 지운다.

옛 판이 옛 스킬 목록을 떠 둔 `~/.claude/backups/install-agy-*` 도 지운다.

### Codex 와 Copilot 맡기기 값

Claude · Codex 를 같이 골랐으면 사용자 환경변수 `CC_BG_AGENTS` · `CC_BG_CODEX_WEB_SEARCH` · `CC_BG_CODEX_WIN_SANDBOX` 를 지운다.

맡기기 모델 표가 Codex 모델 이름을 준 자리면 `CC_BG_CODEX_MODEL` · `CC_BG_CODEX_MODEL_DELEGATE` 도 지운다.

### Codex 훅

설치 창에서 Codex 를 빼고 한 번 더 누르면 설치가 우리 훅만 걷는다(파이썬 3.11 이상이 있을 때 — 없으면 노란 줄로 알리고 남긴다).

- 뒤에 사람 항목이 남으면 그 자리를 지키느라 빈 항목(`{ hooks = [] }`)을 두고, 적어 둔 신뢰(`[hooks.state]` 의 우리 훅 열쇠)는 둔다 —
  남아도 해가 없다
- 손으로는 `~/.codex/config.toml` 의 `[hooks]` 안에서 `drm-guide.py` · `codex-context-alert.py` · `codex-image-gate.py` ·
  `codex-safety-hooks.py` 를 가리키는 UserPromptSubmit · PreToolUse · PostToolUse 항목과 그 빈 항목을 지운다
- 다른 Codex 설정과 사람이 넣은 훅은 둔다

### Codex 와 안티그래비티의 회사 설정

회사 설정은 `~/.codex/config.toml` 과 `~/.gemini/antigravity-cli/settings.json` 에 있다.

- Codex 는 회사 틀이 든 자리만 지우면 된다 — 맞추기 전 것은 `config.toml.before-pgpt-<시각>` 에 있다(가장 새 다섯만 둔다 · 사내 ↔ 사외를 많이 오갔으면 더 옛 것은 걷혔다)
- 안티그래비티 것은 `modelProvider` 줄만 지우면 로그인 갈래로 돌아간다

### 옛 판이 깐 Gemini CLI

옛 판에서 Gemini 칸을 켰던 PC 의 Gemini CLI 는 이 설치가 깔지도 걷지도 않으니, 안 쓰면 손으로 지운다.

- `npm uninstall -g @google/gemini-cli`
- VS Code 확장 「Gemini CLI Companion」
- `~/.gemini/settings.json`
- 같은 폴더의 `~/.gemini/antigravity-cli/` · `~/.gemini/config/` 는 안티그래비티 것이라 둔다

### 사용자 PATH 의 두 줄

사용자 PATH 에 더한 npm 전역 자리 `%APPDATA%\npm` 와 pip 사용자 자리 `%APPDATA%\Python\Python<판>\Scripts` 는 설치가 걷지 않는다.

- 같은 자리를 Node · Python 설치나 사람이 넣었을 수 있어 누가 넣었는지 못 가려서다
- PATH 에는 펴진 경로 `C:\Users\<이름>\AppData\Roaming\…` 으로 적힌다
- npm · pip 로 깐 명령을 남기면 이 줄도 둔다
- 지우려면 시작 메뉴에서 「환경 변수」로 검색 → 「계정의 환경 변수 편집」 → `Path` → 그 줄을 지우고 창을 새로 연다
- 그 폴더가 남아 있으면 설치를 다시 누를 때(로그온 자동 실행도) 다시 더한다

### 바로가기

바탕화면과 시작 메뉴의 「PAI Setup Wizard」 바로가기를 지운다.

### 펴 둔 설치 묶음

판마다 폴더가 하나씩 쌓이는 `%LOCALAPPDATA%\Claude Code Setup\` 를 통째로 지운다.

로그온 자동 실행을 켰으면 옛 판 폴더는 몇 개만 남아 있다. 자동 실행이 쓰던 `autorun.ps1` · `autorun-gate.ps1` · `.autorun-site` ·
`.autorun-night.env` · `.autorun-last` 와 고른 것의 기록 `%LOCALAPPDATA%\Claude Code Setup\choices.env` · 회사 키의 암호화 사본 · 설치 기록 폴더도 그 안이다. 자동 실행
칸을 끄고 설치한 PC 면 끈 것을 적어 둔 `.autorun-off` 도 그 안이다.

## 남겨도 되는 것

프로그램(VS Code · Node · Git · Python · GitHub CLI · 고른 도구의 CLI · 데스크탑 앱)은 회사와 무관해 남겨도 된다.

지우려면 윈도우의 「앱」 화면이나 `winget uninstall` 을 쓴다. VC++ 런타임은 지우지 않는다 — 그 PC 의 다른 프로그램도 같은 런타임을
쓴다.

설치가 `~/repos` 아래 저장소에 걸어 둔 폴더 신뢰(고른 도구 · VS Code)와 데스크탑 앱의 프로젝트 목록도 그 저장소들만 가리키니 남겨도
된다.

## 사외에서 다시 누르면

사내에서 쓰던 기계를 사외에서 다시 누르면 이 글에 적은 사내 값은 설치가 걷어 낸다.

걷는 것은 게이트웨이 주소 · 키 · 사내 전용 값(환경변수와 홈 설정 양쪽)과 프록시 감시 작업 · 그 폴더, Codex · 안티그래비티의 회사 연결(`~/.codex/config.toml` 의 `model_provider` 와 그 제공자 표 · 회사 값 그대로인 창 두 줄 · `~/.gemini/antigravity-cli/settings.json` 의 `modelProvider`)이다. 걷은 회사 키는 이 사용자만 푸는 암호화 사본(`%LOCALAPPDATA%\Claude Code Setup\company-key.dpapi`)으로 남아 사내로 돌아오면 다시 서고, 그 폴더를 지우면 같이 사라진다. 옛 값이 남아 새 값을 가리는
것은 값이 없는 것보다 나빠서다. 다만 우리가 넣은 값이라는 근거가 설 때만 지우고, 모르는 값은 알리기만 한다 — 그렇게 가릴 수 없는
경우(회사를 아주 떠날 때)를 위해 이 글을 둔다.
