# 셸 있는 Claude 레인의 설계 — 왜 이렇게 띄우나

`scripts/claude_lane.py` 머리말이 부르는 꼴과 내는 것을 들고, 인자 · 끝 줄 · 종료 코드의 뜻은 `--help` 가 원본이다. 여기는 그 꼴을
고른 까닭과 잰 것을 든다.

## 왜 따로 서나

맡기는 길 셋이 이 자리를 못 진다. Claude 서브에이전트(Agent)는 셸과 격리 워크트리를 받지만 맡기는 세션의 한도와 결제를 함께 쓴다.
claude-background 는 읽기 · 작업 자리 안 편집만 열고 셸을 끝내 안 연다 — 윈도에는 Claude 샌드박스가 없어 셸이 자리를 못 지킨다.
Codex · agy 레인은 다른 모델이다. 이 러너는 셸을 여는 대신 울타리를 **제 격리 워크트리 · 자동 모드 분류기 · push 막음** 셋으로 세운다.

## 띄우는 깃발

- **권한은 자동 모드(`--permission-mode auto`)** — 수락 편집 모드(`acceptEdits`)는 `.claude/` 아래 편집을 `--allowedTools
  "Edit(.claude/**)"` 를 줘도 거절해, 스킬 · 규범을 고치는 레인이 셸의 치환 스크립트로 돌아간다. 자동 모드는 같은 편집을 거절 없이 낸다
  (Claude Code 2.1.330).
- **묻는 창은 아무도 안 받는다(`--permission-prompts none`)** — `-p` 에는 답할 사람이 없다. 묻게 될 호출은 레인을 멈춰 세우지 않고
  거절돼 결과의 `permission_denials` 에 남는다(끝 줄 `denied=`).
- **push 막음(`--disallowedTools` 에 `Bash(git push:*)` · `Bash(git push)` · `Bash(git -C * push *)` · `Bash(git -C * push)`)** — 트리 밖으로
  나가는 상태는 부모가 바꾼다. 봉투의 레인 규칙도 같은 말을 하지만 규칙은 부탁이고 이 깃발은 울타리다. 가운데 `*` 뒤의 `:*` 는 안 먹어
  빈칸 `*` 로 잇는다. `git * push*` 처럼 넓히지 않는다 — 메시지에 push 가 든 커밋까지 막힌다. 다른 꼴(`git -c <값> push` ·
  `git --git-dir=<자리> push`)은 이 깃발에 안 걸려 봉투의 규칙이 든다.
- **피어 세션 이름(`--name lane-<이름>`)** — 같은 PC 의 Claude 세션 목록(ListAgents)에 그 이름 그대로 선다. 안 주면 하네스가 꼬리를
  붙인 이름을 지어 부모가 찾기 어렵다.
- **추론 깊이(`--effort`)는 부르는 쪽이 줄 때만 넘긴다** — 안 주면 CLI 가 사용자 설정을 따라 대화형 세션과 같은 깊이로 뜬다. 낱말은 CLI 가
  받는 다섯 그대로라 래퍼가 먼저 거른다 — 틀린 낱말이 레인을 띄운 뒤에야 지지 않게. 모델 · 상한처럼 레인 기록에 남아 이어 묻기가 물려받는다.
- **사용자 설정 · 훅 · 스킬 · 홈 규범을 끄지 않는다** — 짓는 레인은 대화형 세션과 같은 손을 써야 한다(claude-background 가 끄는 것과
  반대다 — 거기는 읽기 울타리가 먼저다).

## 결제

- **api** — `--key-env` 가 이름 댄 환경변수의 값을 레인 프로세스의 `ANTHROPIC_API_KEY` 로만 싣는다. 사용자 수준의 `ANTHROPIC_API_KEY`
  는 사람의 대화형 세션까지 키로 넘기므로 키는 제 이름의 환경변수에 산다. `ANTHROPIC_AUTH_TOKEN` · `ANTHROPIC_BASE_URL` 은 걷는다 — 앞의
  것은 키를 앞지르고, 뒤의 것이 게이트웨이를 가리키면 Console 키가 그 게이트웨이로 간다. 크레딧을 쓰는 판이라 상한(`--max-budget-usd`)이
  꼭 서고, 날 출력 첫 줄의 `apiKeySource` 가 `ANTHROPIC_API_KEY` 가 아니면 `billing` 으로 끝낸다 — 키로 돌리려던 약속이 깨진 것이다.
- **subscription** — Claude CLI 가 제 설정으로 붙게 둔다. 사내의 `ANTHROPIC_API_KEY` 는 게이트웨이 키라(`ANTHROPIC_BASE_URL` 이
  게이트웨이를 가리킨다) 둔다. Anthropic 으로 바로 가는 자리(주소가 없거나 `anthropic.com`)에 선 `ANTHROPIC_API_KEY` 만 걷는다 — 키로 띄운
  레인은 그 키를 제 환경에 들고 있어, 그 레인이 띄우는 구독 레인이 키를 물려받아 크레딧을 쓴다.
- **부른 세션의 표지(`CLAUDECODE` · `CLAUDE_CODE_SESSION_ID` · `CLAUDE_CODE_REMOTE_SESSION_ID`)는 걷는다** — 남으면 레인이 부른 세션의
  대화 id 를 이어 쓴다. 걷어도 레인은 피어 세션으로 선다.

## 트리와 기록

- **트리는 러너가 `git worktree add` 로 세운다** — 본 사본의 `.claude/worktrees/lane-<이름>`, 가지 `lane/<이름>`, 출발은 이름 댄 판(기본
  로컬 `main`). 트리 안에서 불러도 본 사본(공통 git 자리의 부모)에 선다 — 거두기(`harvest_worktree.py`)가 그 자리의 트리를 다른 레인 것으로
  빼고 센다. 하네스의 `claude -w` 는 출발점 · 가지 이름을 우리가 못 정한다(안 쟀다). `claude --bg` 는 레인에 안 쓴다 — 곧바로 돌아와 앱의 배경 작업
  창에 도는 항목이 안 서고(띄운 명령만 끝난 채 선다), 결과 줄 · 비용 · 인증 출처가 없으며, 결제가 오래 사는 배경 서비스의 환경을
  따를 수 있다(안 쟀다). `-p` 를 배경 셸 명령으로 띄우면 그 창에 명령 설명의 이름으로 도는 항목과 멈춤 단추가 선다.
- **환경 · CLI 를 다 본 뒤에 트리를 세운다** — 못 띄울 판에 빈 트리가 안 남는다.
- **레인 기록은 트리의 git 자리(`<git dir>/claude-lane/lane.json`)에 둔다** — 이어 묻기는 같은 작업 폴더에서만 대화를 찾으니 기록의 수명이
  트리의 수명과 같아야 한다. 트리를 걷으면 git 이 함께 걷고, 작업 사본에 안 보여 레인이 커밋할 일도 없다. 키 값은 안 적고 키 환경변수의
  이름만 적는다.
- **보고는 결과 줄의 `result`(레인의 마지막 말)다** — `--out` 에 보고와 끝 줄, 곁의 `.result.json` 에 칸 전부, `.jsonl` 에 날 출력을
  남긴다. 날 출력은 성공에도 남긴다 — 짓는 레인의 걸음은 거둘 때 근거다.
- **시간 한도는 7000 초** — Claude 부모의 배경 셸 한도(2 시간)보다 짧아, 셸이 끊기 전에 러너가 레인을 끊고(`runner_common.watch` 가
  프로세스 나무째) 끝 줄을 남긴다.

## 잰 것 (Claude Code 2.1.330 · Windows 11)

| 잰 것 | 결과 |
|---|---|
| api 결제 · 작은 판 | 트리가 서고 `auth=ANTHROPIC_API_KEY` · `cost=$0.0074` · 보고가 거둬졌다 |
| `--resume` | 같은 대화 id 로 이어 앞 판의 답을 기억했다 |
| 지출 상한에 닿음 | 결과 `subtype=error_max_budget_usd` → 갈래 `budget` |
| 구독 결제 · 키를 든 환경에서 | `auth=none`(로그인) — 물려받은 Console 키를 걷었다 |
| `--name` | ListAgents 에 `lane-<이름>` 그대로 섰다 |
| push 막음 · 새 레인 | `git -C . push <원격> HEAD` · `git -C "." push` · `git -C .. push <원격> HEAD` · `git push <원격> HEAD` 넷이 다 거절되고 `git -C . log` · `git -C . status` 는 섰다 |
| 띄운 배경 셸을 멈춤 | 피어 목록에서 곧 빠졌다 · 날 출력에 그 뒤 줄이 안 붙었다 — 레인 프로세스가 함께 끝났다 |

## 빌린 자리

부모 세션이 쓰던 띄우기 셸 스크립트(`lane_p.sh` — 저장소 밖 임시 자리)의 깃발 다섯(`-p` · `--permission-mode auto` · push 막음 ·
`--max-budget-usd` · `--output-format stream-json --verbose`)과 날 출력에서 `apiKeySource` · `result` 를 뽑는 법을 빌렸다. 갈라 고친 것 —
키를 사용자 환경변수 하나에 묶지 않고 이름을 받는다 · 출발 판 · 저장소를 받는다 · 이어 묻기 · 피어 이름 · 결제 약속 판정 · 구독에서 물려받은
키 걷기.
