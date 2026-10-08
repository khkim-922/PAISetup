---
name: agy-background
description: "agy(Antigravity CLI)에게 일을 넘길 때 부른다 — 1~2분이면 끝날 일은 agy-bridge MCP 도구로 바로, 그보다 길 일은 백그라운드로 띄워 대화를 안 막는다. 「agy 한테 시켜」·「제미나이로 조사시켜」·「오래 걸리는 조사 맡기자」·「백그라운드로 돌려」. 윈도에서 창이 안 뜨게 agy 를 띄우는 래퍼가 딸려 있다."
---

# 짧으면 MCP, 길면 백그라운드

agy 에게 넘기는 길은 둘이다. **MCP 도구는 끝날 때까지 대화를 막는다** — 돌아오기 전에는 사람이
말을 걸어도 답을 못 한다. 그래서 일의 길이로 가른다.

| | MCP (`mcp__agy-bridge__*`) | 백그라운드 (이 스킬의 래퍼) |
|---|---|---|
| 맞는 일 | 1~2분 안에 끝나고 답을 바로 써야 하는 일 | 그보다 길거나, 그동안 할 딴 일이 있는 일 |
| 대화 | 막힌다 | 안 막힌다 · 끝나면 알림이 온다 |
| 시간 한도 | 도구마다 다르다 — 짧게는 2분(`web_lookup`), 가장 긴 `delegate` 가 10분 | `--timeout` (기본은 래퍼의 `DEFAULT_TIMEOUT_SEC`) |
| 모델 | 도구마다 고른 목록(`AGY_MODEL_<도구>` 가 있으면 그것) 뒤에 `AGY_DEFAULT_MODEL` → `AGY_FALLBACK_MODELS` 차례로 — `api:` 후보는 거른다 | `--model` 하나, 없으면 `AGY_MODEL_DELEGATE` → `AGY_DEFAULT_MODEL` → `AGY_FALLBACK_MODELS` 차례로 — `api:` 후보는 키가 있을 때만 API 키 방식으로, 다 비면 agy 기본 |
| 한도(429) | 차례의 다음 모델로 넘어간다 — `model` 을 주거나 `follow_up` 이면 안 넘어간다 | 같다 — `--model` 을 주면 안 넘어간다 |
| 이어 묻기 | `follow_up` + 돌려받은 session_id | `--conversation` + 끝 줄의 id |

- MCP 가 한도에 걸려 끊겨도 agy 세션은 남는다 — 돌려받은 session_id 로 `follow_up` 하면 결과를 받는다.
- **한도가 차는 단위가 방식마다 다르다** — 로그인 방식은 갈래(제미나이 · 그외)마다, API 키 방식은 모델마다 찬다.
  그래서 래퍼는 로그인 기본 모델이 막히면 `api:` 후보로 제미나이 모델을 하나씩 돌리다가 마지막에 그외 갈래로
  간다. 키(`GOOGLE_API_KEY` · `GEMINI_API_KEY`)가 없으면 `api:` 후보는 조용히 건너뛰고, 브릿지는 로그인
  방식 안에서만 넘어간다. 이름들의 값과 차례는 설치기가 agy 묶음을 깔 때 자리마다 사용자 환경변수로 심는다.
- **사내는 일의 무게로 모델을 가른다** — 맡기기(`delegate` · 이 래퍼)는 `AGY_MODEL_DELEGATE`, 나머지는
  `AGY_DEFAULT_MODEL` 이고 넘기지 않는다(회사 키는 예산 한도라 하나가 막히면 다 막힌다). 값은 설치기의
  자리별 표(`$AgyModelVarsBySite`)가 든다.
  `analyze_files` 에 판단이 드는 물음을 줄 때는 그 호출의 `model` 로 `AGY_MODEL_DELEGATE` 값을 준다 —
  세션 시작 안내가 그 값을 댄다.
- **서브에이전트로 MCP 를 감싸 막힘을 피하지 않는다** — 서브는 제 시작 비용을 따로 싣고, 하는 일은
  기다리는 것뿐이다. 백그라운드가 같은 일을 그 비용 없이 한다.

## 백그라운드로 맡기기

1. **프롬프트를 파일로 쓴다**(Write · 스크래치패드). 명령줄에 싣지 않는다 — 따옴표와 역슬래시가
   셸을 거치며 바뀐다. 래퍼가 agy 에게는 명령줄로 넘기므로 윈도 명령줄 한도에 걸릴 만큼 길면 안
   받는다(`MAX_PROMPT_CHARS`) — 큰 자료는 파일 경로를 주고 agy 가 읽게 한다.
2. **Bash 를 `run_in_background: true` 로 부른다** — `pythonw` 로 부르는 것이 요점이다(아래 「창」):

   ```sh
   pythonw "<이 스킬 폴더>/scripts/agy_bg.py" --prompt-file <프롬프트> --out <답 파일> --cwd <작업 자리> \
     [--model "<이름>"] [--timeout <초>] [--conversation <id>]
   ```

   모델 이름은 `agy models` 가 내는 표시 이름을 그대로 쓴다(예: `Gemini 3.8 Flash (High)`).
3. **끝나면 알림이 온다 — `--out` 파일을 읽는다.** 맨 끝 줄 `[agy-bg] <갈래> …` 이 갈래 · 걸린
   시간 · 모델 · 넘어간 자취(`failover=`) · 토큰 · `conversation` id 를 든다. 갈래가 `ok` 가 아니면 그 위에 agy 가 낸 것과 stderr,
   끝 줄에 로그 경로가 남아 까닭을 든다. 종료 코드는 0 일 때만 답이 온 것이다(갈래별 코드는 래퍼
   머리말이 든다). ⚠ 인자가 틀리면 답 파일이 아예 안 생긴다 — 종료 코드만 남는다.

4. **이어 물을 때**는 끝 줄의 `conversation` id 를 `--conversation` 으로 준다 — 앞 맥락을 다시 안 보낸다.
   끝 줄 `model=` 이 `api:` 로 시작하면 그 이름을 `--model` 로 같이 준다 — 그 대화는 API 키 방식의 홈에
   쌓여 있어 로그인 방식으로는 못 찾는다.

## 작업 자리

agy 는 권한을 묻지 않고 돈다(`--dangerously-skip-permissions` — 화면 없이 돌면 물을 사람이 없다).
「파일을 만들지 마라」는 지시로는 안 막힌다.

- **조사만 시킬 때는 `--cwd` 를 스크래치패드로 준다** — 클론 · 임시 파일이 거기 쌓인다.
- 저장소를 줬으면 끝난 뒤 `git status --porcelain` 으로 남긴 것을 본다.

## 래퍼가 하는 일 — 왜 `agy -p` 를 그냥 안 띄우나

- **창.** 백그라운드 Bash 는 명령을 콘솔 없이 띄운다. 콘솔 없는 부모 밑의 콘솔 프로그램은 새 콘솔을
  받아 창이 뜨고, agy 가 명령을 돌릴 때마다 또 뜬다(앞에서 돌리면 안 뜬다). `pythonw` 는 콘솔 없는
  GUI 프로그램이라 제 창이 없고, agy 를 「창 없음」으로 띄워 **안 보이는 콘솔**을 붙인다 — agy 의
  자식들도 그 콘솔을 물려받는다. ⚠ `python`·`powershell`·`cmd`·`node` 로 감싸면 그것들이 콘솔
  프로그램이라 제 창이 먼저 뜬다.
- **한도 초과.** agy 는 화면 없이 돌 때 429 를 밖으로 안 낸다 — 시간이 다 될 때까지 조용히 다시
  시도하다가 빈 답에 종료 코드 0 으로 끝난다. 래퍼는 agy 로그를 주기적으로 훑다가
  `RESOURCE_EXHAUSTED (code 429)` 가 보이면 바로 끊는다.
- **agy 제 한도.** `--print-timeout` 이 차도 agy 는 종료 코드 0 · `status: SUCCESS` · 빈 답으로 끝나고
  까닭은 stderr 한 줄(`[agy] print timeout …`)에만 남긴다. 래퍼는 그 줄로 시간 초과를 가른다.
- **끊을 때는 나무째.** 래퍼가 끊으면 agy 가 띄운 셸까지 같이 끊는다.

⚠ **윈도 밖(리눅스·맥)에서는 재지 않았다.** 래퍼는 그쪽에서 창 플래그를 안 붙이게 짰고, `pythonw`
대신 `python3` 로 부른다.

---

> 출처 — agy 의 429 동작 · MCP 시간 한도 두 층 · 도구별 한도:
> [sshahzaiib/agy-bridge](https://github.com/sshahzaiib/agy-bridge) `README.md`
> (보관본 `references/agy-bridge-README.md` · 받은 판 v0.4.2 · MIT, 고지 `references/agy-bridge-LICENSE`).
>
> 안 묶은 것 — [yuting0624/antigravity-for-claude-code](https://github.com/yuting0624/antigravity-for-claude-code) 의 `agy-job` 이 같은 일(긴 위임을 백그라운드로
> 띄우고 나중에 거둔다)을 한다. bash `nohup … &` 로 띄우는 스크립트라 전제가 다르고, 그 저장소 스스로
> 네이티브 윈도를 권하지 않는다. 플러그인째 깔아야 하고 세션마다 위임 방침을 주입한다 — 이쪽은 Claude
> Code 의 백그라운드 실행에 래퍼 하나만 얹는다. 그쪽 `agy-job` 이 윈도에서 창을 내는지는 재지 않았다.
