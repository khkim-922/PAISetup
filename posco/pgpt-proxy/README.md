# pgpt-proxy — 사내 게이트웨이 앞의 로컬 프록시 (동료 코드 사본)

사내 게이트웨이(P-GPT)가 그대로는 안 받는 요청을 PC 안에서 고쳐 넘기는 프록시다. `127.0.0.1:18901` 에서
클라이언트의 요청을 받아, 본문을 게이트웨이가 받는 꼴로 고친 뒤 넘긴다.

코드는 사내 동료(GitHub `sejuone-cloud`)의 비공개 저장소 `pgpt-one-click-connect` 에서 **통째로** 가져왔고,
우리가 얹은 것은 아래 「상류 판」이 든다. 누가 이 프록시를 지나나는 결정 기록 0041(사내는 키 하나로 통일하고
Claude·Gemini 는 루프백 프록시를 지난다)이 정했다.

- **Claude Code** — Opus 5 가 게이트웨이 직결에서 assistant prefill 을 400 으로 거절해서 지난다
- **Gemini CLI** — CLI 가 `https` 가 아닌 주소를 거부하는데 루프백만은 `http` 를 받아 준다. 회사 문서가 시키는
  번들 패치 대신 이 길로 간다
- **Codex** — 게이트웨이에 직결이라 안 지난다(`../Codex-CLI.setting.toml` 의 `base_url`)

| 파일 | 상류 자리 | 무엇 |
|---|---|---|
| `opus5_proxy.py` | `app/opus5_proxy.py` | 프록시 본체. 표준 라이브러리만 쓴다 |
| `mock_gateway.py` | `tests/mock_gateway.py` | 가짜 게이트웨이 — 실제처럼 prefill 에 400 을 낸다. 사내망 밖에서 프록시를 끝까지 돌려 볼 때 |
| `Test-AllPgptModels.py` | `tests/Test-AllPgptModels.py` | 모델 전수 스모크 — 프록시 너머로 모델마다 「Reply OK」 한 줄. 결과는 곁 `model-results/` |
| `Test-ProxyFaults.py` | `tests/Test-ProxyFaults.py` | 비정상 응답·스트림 단절·413·surrogate·180초 절단 계수 등 결함 내성 검사 |
| `Test-ProxyStreaming.py` | `tests/Test-ProxyStreaming.py` | 스트림 무결성 — 이벤트 경계의 주석 · 길이 선언 SSE · 끝 이벤트 검증 · 진단 줄 |
| `Test-ProxyCompaction.py` | `tests/Test-ProxyCompaction.py` | 압축 알아보기 · 출력 상한 · thinking 예산 · 간결 지시(켠 판) |
| `Test-ProxyUnstream.py` | `tests/Test-ProxyUnstream.py` | 비스트리밍 갈래 — 압축이 비스트리밍·18,000 으로 가나 · 짓는 SSE · 필수 도구 인자 검증 |
| `Test-ProxyQueue.py` | `tests/Test-ProxyQueue.py` | 큰 요청 줄 세우기(기본 꺼짐) — 꺼진 채 큰 요청 둘이 동시에 통하나 · 켠 판의 차례 |
| `pair_check.py` | (우리 것) | 프록시와 가짜 게이트웨이를 함께 띄워 「직결 400 · 프록시 200 · prefill 1번 뗐다」를 잰다 |
| `hoist_check.py` | (우리 것) | 그림 끌어내기가 본문 모양을 옳게 바꾸나 — 함수를 직접 부른다(망 없음) · 양성·음성 양방향 |
| `hoist_live_check.py` | (우리 것) | 같은 것을 **실호출로** — 보정 없는 판은 못 보고 고친 판은 그림을 맞히나 |
| `image_lane_probe.py` | (우리 것) | 게이트웨이가 **어느 자리**의 그림을 보나 — 다섯 갈래를 한 그림으로 재는 눈가림 프로브 |
| `image_tail_probe.py` | (우리 것) | `tool_result` 가 **마지막**일 때(= `Read` 의 실제 꼴) 어디에 두면 보나 |
| `watchdog.ps1` | 모름 — 이 저장소에 기록이 없다 | 감시자 — 5초마다 `opus5_proxy.py` 를 돌리는 파이썬 프로세스가 있나 보고, 없으면 `pythonw` 로 창 없이 다시 띄운다. 뮤텍스(이름 `PGPTProxy-Supervisor`)로 한 개만 돌고, 프록시 파일과 같은 폴더에 감시 기록(watchdog.log)을 남긴다 |

## 상류 판

- 저장소 [`pgpt-one-click-connect`](https://github.com/sejuone-cloud/pgpt-one-click-connect) · 커밋 `2ab3f39`
  (2026-10-07 · v0.7.0) · 프록시 `VERSION = 26`. 프록시 파일이 마지막으로 바뀐 상류 커밋은 `3dac49b`(v0.6.32)다
- **우리 판 번호는 두 칸이다 — 지금 `26.4`**(`VERSION_UPSTREAM` · `VERSION_OURS`). 앞 칸은 받아 온 상류 판이고,
  뒤 칸은 그 위에 우리가 얹은 덩어리 수다. **한 칸으로 세지 않는 까닭**: 상류와 우리가 한 줄에 번호를 매기면
  상류가 새 판을 내는 날 우리 번호와 부딪히고, 그때는 번호만 보고 어느 쪽이 새것인지 못 가른다. 칸을 나누면
  **상류가 27 을 낼 때 우리 칸이 0 으로 돌아가 `27.0`** 이 되고, 그것이 `26.4` 보다 새것이라는 것이 번호에서
  바로 보인다
  ⚠ **`/health` 는 사람이 읽기 좋게 `26.4` 한 줄을 내지만, 판을 견주는 설치기는 두 수를 따로 정수로 읽는다** —
  점 찍힌 문자열을 그대로 견주면 `"9" > "10"` 이 되기 때문이다. 설치기는 그렇게 견주어 낮으면 갈아 끼운다
  (`install.ps1` 프록시 칸)
  ⚠ **정수 한 칸(`17`·`26`)이 도는 자리도 받는다** — 우리 옛 판과 상류 판은 새 이름이 없어 「못 읽었다」로
  떨어지고, 그때는 **갈아 끼우는 쪽으로 기운다.** 반대로 두면 옛 프록시가 영영 안 바뀐다
- 작성자 허락 2026-09-14 (라이선스 파일은 상류에 없다 — 허락으로 든다)
- **상류 파일은 안 고친다 — 예외는 `opus5_proxy.py` 의 넷과 판 번호, 시험 파일의 몇 줄, `mock_gateway.py` 의 한 칸이다**
  (결정 0082).
  ⑴ **제미나이 이름 표**(`_GEMINI_MODEL_ALIASES` · `normalize_gemini_model_path` 의 그 조회 · 자체 검사 세 칸) —
  안티그래비티가 제목 짓기에 못박아 둔 이름이 게이트웨이에 없어 그 곁 호출만 지던 자리다
  ⑵ **그림 끌어내기**(`hoist_tool_result_images` · `sanitize_payload` 의 그 한 줄 · 카운터 `hoisted_images` ·
  머리 설명 한 칸 · 검사 둘 · 프로브 둘) — 게이트웨이가 `tool_result` **안**의 `image` 를 200 에 조용히 버려서
  `Read` 로 여는 그림이 사내에서 한 픽셀도 안 오던 자리다(이슈 #76)
  ⑶ **압축 간결 지시 끔**(`COMPACT_CONCISE` 의 기본값 `"0"` · 자체 검사 한 칸) — 상류는 켬이다. 우리는 1M 창이라
  압축이 드물고, 드물게 하는 압축을 짧게 줄이면 잃는 것이 더 크다(결정 0082)
  ⑷ **웹서치 메움**(`WEB_SEARCH` · `WEB_SEARCH_MODEL` · `_WEB_SEARCH_PROMPT_HEAD` · 계수 둘 · `stats()` 의 네 칸 ·
  `web_search_*` 함수 묶음 · `anthropic_message_events` 의 `web_search_tool_result` 갈래 · `_forward_request` 의
  `web_search` 갈래 · 머리 설명 한 칸 · 자체 검사 한 칸) — 게이트웨이가 서버 웹서치 도구를 클라이언트 `tool_use` 로
  되돌려, Claude Code 의 WebSearch 가 사내에서 늘 빈손이던 자리다(이슈 #118 · 결정 0087)
  **판 번호 두 칸도 우리 것이다**(위).
  시험 파일은 **프록시를 찾는 경로 줄만** 바꿨다(상류는 `app/` 아래, 우리는 같은 폴더). 하나만 더 —
  `Test-ProxyStreaming.py` 의 압축 HTTP 경로 시험이 간결 지시가 켜진 기본값을 박아 두어, 그 단언 한 줄을
  ⑶ 에 맞췄다.
  `mock_gateway.py` 에는 느린 비스트리밍 답 한 칸이 붙어 있다(`MOCK_SLOW_SEC` · `MOCK_ANSWER` · `_mock/last`) —
  옛 우리 unstream(결정 0051)을 재려고 붙였고, 지금은 상류의 비스트리밍 갈래를 사내망 밖에서 잴 때 쓴다.
  **예전에 얹던 넷은 걷었다** — keepalive(0044) · unstream(0051) · 하이쿠 대체 · 게이트웨이 요청 번호 로그(#67).
  상류 v18 · v25 가 같은 일을 들고, 걷은 까닭과 무엇이 남나는 결정 0082 가 든다.
  나머지는 상류 그대로다. 상류가 CRLF 인 것만 이 저장소 규칙(`.gitattributes`)이 LF 로 눕힌다. 곁말 한 줄도
  손댔다 — 하이쿠 칸(`CLAUDE_HAIKU_SUBSTITUTE`) 곁말의 출처 표기에서 우리 계정 이름을 뺐다. 배포본을 뽑는 검사가
  그 이름을 「새면 안 되는 글자」로 물기 때문이다(`dist.manifest.conf`). 동작은 안 바뀌어 판 번호에 안 센다. 커밋 게이트의
  파이썬 판정(ruff)이 상류 코드에서 문제 삼는 것은 뿌리 `ruff.toml` 이 그 파일들(`opus5_proxy.py` · `mock_gateway.py` ·
  `Test-AllPgptModels.py` · `Test-ProxyQueue.py`)을 검사에서 빼는 것으로 받는다. 나머지 시험 넷은 판정을 통과해 뺄
  까닭이 없다. 판정 기준은 전역 설정이 들고, 무엇을 뺄지는 저장소가 정한다(결정 0039)

## 무엇을 쓰고 무엇이 노나

칸마다 회사 로그 실측이 든다 — 25시간 3039줄(2026-09-15 08:04 ~ 09-16 09:03) + Gemini·Codex 탐침 한 판씩.
그 실측은 옛 판(`17.x`) 때 것이다. **`26.x` 에서 새로 든 칸은 회사에서 아직 안 쟀다** — 그 칸의 근거는 상류의
회사 실측(같은 게이트웨이)이고, 그렇게 적었다.
**「논다」는 안 걸린다는 판정이지 걷어 낸다는 뜻이 아니다** — 걷어 내지 않는 까닭은 위 「상류 파일은 안 고친다」.

| 프록시가 하는 일 | 우리 |
|---|---|
| `/v1/messages` — 끝의 assistant 마디 제거 · `system` 역할 마디를 `user` 로 · 같은 역할 병합 · `temperature`/`top_p` 제거 | **쓴다** (Claude Code) — `trimmed_prefills` 가 센다 |
| `claude-sonnet-5` → `claude-sonnet-4.6` (게이트웨이 미등록 별칭) · 같은 표(`_CLAUDE_MODEL_ALIASES`)가 `-latest` 별칭 넷도 등록된 이름으로 푼다 | **쓴다 · 758회**(`claude-sonnet-5`) — `ANTHROPIC_MODEL` 은 메인 세션의 모델 하나만 못박고, Claude Code 가 스스로 부르는 곁 호출(서브에이전트·요약·모델 피커의 다른 칩)은 그 못을 안 타고 제 이름을 보낸다 |
| 이름에 `haiku` 가 들면 `claude-sonnet-4.6` 으로 (`CLAUDE_HAIKU_SUBSTITUTE` · 상류 v18 — 우리가 먼저 얹던 것과 같은 규칙) | **쓴다** — 하이쿠는 이 게이트웨이에 **한 판도 없다**(`GET /v1/models` 실측 2026-09-17 · Claude 는 opus 4.5·4.6·4.7·5 와 sonnet 4.5·4.6 여섯뿐). 그래서 서브에이전트 호출이 통째로 `400`(「모델을 찾을 수 없습니다」)으로 지던 자리다. **이름을 목록으로 안 잡고 규칙으로 잡는다** — 클라이언트가 아는 하이쿠 이름이 열둘이라 판이 오를 때마다 샌다. 실측: `claude-haiku-4-5` · 날짜박은 판 둘 다 `200` 에 `model: claude-sonnet-4.6` · 로그에 `restored` 한 줄. ⚠ **게이트웨이가 하이쿠를 들이면 이 칸을 지운다** — 그때는 이 규칙이 진짜 하이쿠까지 갈아버린다 |
| 대시 모델 ID 복원 — `claude-opus-4-7` → `claude-opus-4.7` | **쓴다 · 6회** — 같은 곁 호출 길. 별칭과 한 함수(`normalize_claude_model_id`)라 바뀌면 로그 한 줄이 찍힌다 |
| 빈 도구 `description` 채우기 | **쓴다 · 6회** (Claude Code) · Codex 를 루프백에 태우면 `/v1/responses` 에서도 걸린다(탐침 `tool_descriptions_filled=1`) |
| **(우리 것)** Claude Code 의 웹서치 하위 요청(서버 도구 `web_search_20250305` 를 선언한 요청)을 게이트웨이의 제미나이 검색(`googleSearch` grounding · `PGPT_PROXY_WEB_SEARCH_MODEL` · 기본 `gemini-3.6-flash`)으로 메워 `server_tool_use` · `web_search_tool_result` · `text` 세 칸으로 지어 돌려준다. 상류가 지면 검색 오류 칸으로 · `/health` 의 `web_search_filled` · `web_search_failed` · 끄려면 `PGPT_PROXY_WEB_SEARCH=0` | **쓴다 · 회사 실측 아직** — 게이트웨이가 그 선언을 클라이언트 `tool_use` 로 되돌려 아무도 검색하지 않아 결과 0 건이던 자리다(사내 실측 2026-10-08 · #118). 제미나이 grounding 이 실제 웹을 찾는 것은 실측됐다. Claude 를 안 거치므로 상류 호출은 하나다. ⚠ 출처 주소는 구글 경유 주소(`grounding-api-redirect`)로 감싸진 채 싣는다 — 풀지 않는다. ⚠ 게이트웨이가 왜 그 선언을 바꾸는지는 밖에서 안 보여, 게이트웨이가 바뀌면 이 칸이 조용히 어긋날 수 있다 |
| **(우리 것)** `tool_result` 안의 `image` 를 같은 메시지 **끝**으로 내놓고 빈 자리에 「그림은 이 메시지 끝에」를 적는다(`hoist_tool_result_images` · `/health` 의 `hoisted_images`) | **쓴다** — 게이트웨이가 `tool_result` 안의 그림만 200 에 버리고 같은 바이트가 형제 블록으로 서면 읽는다(눈가림 실측 2026-09-22 · 이슈 #76). ⚠ 그림을 `tool_result` **앞**에 끼우면 짝 검사가 400 을 낸다 — 그래서 끝으로만 간다 |
| 상류 연결 풀 — 30초(`UPSTREAM_IDLE_TTL`) 넘게 논 연결은 재사용하지 않고 닫는다 · `/health` 의 `upstream_expired` | **쓴다** — 게이트웨이가 keep-alive 를 끊은 뒤 남은 연결을 집어 첫 요청이 지던 자리. 실측 `upstream_expired=8` · 재사용 82 |
| Anthropic · OpenAI SSE 가 침묵하면 `KEEPALIVE_SEC`(기본 15초)마다 `: keepalive` 주석 한 줄을 클라이언트에 흘린다(상류 v18) — 게이트웨이가 생각 조각을 안 흘려 Claude Code 의 바이트 유휴 워치독이 끊던 자리. **완성된 이벤트 사이에만 끼운다**(v24). `PGPT_PROXY_KEEPALIVE_SEC=0` 이면 끈다 | **쓴다 · 132회** (Claude Code · 옛 판 실측). ⚠ 180초 벽은 못 넘는다 — 유휴가 아니라 요청 실행 시계다(`../ENV-posco.md`) |
| **스트림 무결성**(v23 · v24) — SSE 는 늘 chunked 로 다시 싼다 · 끝 이벤트(`message_stop` · `response.completed` · `[DONE]`)를 확인하고, 없이 닫히면 끝 표시 없이 닫아 클라이언트가 잘린 응답으로 안다 · 오류 이벤트는 그대로 넘기고 센다 | **쓴다** — 옛 판에서 가짜 게이트웨이로 재현한 결함 둘을 막는다(2026-10-07): 이벤트 도중에 쉬면 주석이 이벤트 한가운데 끼어 그 이벤트가 깨지던 것 · 길이를 선언한 SSE 에 주석이 얹혀 끝 이벤트가 잘리던 것. 실제 게이트웨이에서 얼마나 잦은지는 모른다 |
| **출력 상한**(v26) — Claude 요청의 `max_tokens` 를 그 요청이 타는 길의 시한 안으로 **낮춘다**(안 올린다): 스트리밍 10,000(`PGPT_PROXY_STREAM_MAX_TOKENS`) · 비스트리밍 18,000(`PGPT_PROXY_NONSTREAM_MAX_TOKENS`) · `enabled` thinking 예산은 상한의 절반 이하로. `0` 이면 그 길은 클라이언트 값 | **쓴다 · 회사 실측 아직** — 긴 턴이 180초에 `HTTP 500` 으로 잘리면 Claude Code 가 같은 요청을 최대 10번 다시 보냈다. 상한에 닿으면 `stop_reason=max_tokens` 로 끝나 Claude Code 가 나눠서 이어 쓴다. 값은 상류 실측(Opus 턴 1.2초 + 토큰당 13.77ms · 197건 · 2026-10-06)에서 왔다. ⚠ 우리 아뜰리에의 8월 실측(초당 34~58토큰)으로 셈하면 10,000 이 170~290초라 벽을 넘을 수 있다 — `/health` 의 `execution_cuts` · `max_tokens_hits` 로 가린다. ⚠ 1만 토큰이 넘는 도구 호출 하나(큰 `Write`)는 못 끝난다 — 상한이 없어도 약 12,900 에서 벽이다 |
| **압축만 비스트리밍**(v25 · `PGPT_PROXY_COMPACT_UNSTREAM` · 기본 켬) — Claude Code 의 압축 요청을 알아보면(v26: 마지막 user 글이 `CRITICAL: Respond with TEXT ONLY` 로 시작하고 앞 4,000자 안에 요약 과제 문장) 상류엔 `"stream": false` 로 보내고 답을 다 받아 SSE 로 지어 낸다. 압축 안의 「Output token limit hit」 이어 쓰기도 같은 길(`kind=compact_continue`) | **쓴다 · 회사 실측 아직**(결정 0082) — 비스트리밍 경로에는 180초 상한이 없다(앞단 300초까지 산다 · 0051 실측). 압축은 도구를 안 부르니 그 경로의 도구 인자 유실과 무관하고, 압축 답에 도구 호출이 섞여 오면 내보내지 않고 오류로 돌린다. ⚠ **응답 머리가 올 때까지(최대 300초) 클라이언트로 바이트가 안 간다** — Claude Code 의 바이트 유휴 워치독이 그보다 길어야 하고, 자리 파일이 10분으로 심는다(0044 에서 사는 것) |
| 압축 간결 지시(v24 · `PGPT_PROXY_COMPACT_CONCISE`) — 압축 지시 끝에 「3000토큰 안팎 · 분석은 다섯 문장 안」을 덧붙인다 | **끔 (우리 것 · 결정 0082)** — 상류는 켬이다. 켜려면 `=1`. ⚠ 끈 대가로 압축 출력이 18,000 상한에 닿을 수 있다 — 닿으면 Claude Code 가 같은 압축 안에서 이어 쓴다 |
| 전체 비스트리밍(`PGPT_PROXY_CLAUDE_UNSTREAM=1` · 기본 끔) — 압축이 아닌 Claude 턴까지 위 길로 보낸다. 필수 도구 인자가 빠진 도구 호출은 내보내지 않고 오류로 돌린다 | **논다** — ⚠ **도구를 쓰는 클라이언트에는 켜지 않는다 — 큰 도구 인자가 빈다**(결정 0051 실측 2026-09-17: 켠 판에서 `Edit` 호출이 `input={}` 로 오고 `stop_reason` 은 정상 `tool_use`, 같은 판의 작은 `Bash` 는 멀쩡, 끄면 통한다 · 재현 3회 · 까닭은 게이트웨이 안). 도구를 안 쓰는 쪽(아뜰리에)은 켜서 180초 벽을 비껴갈 수 있다. 옛 우리 스위치 이름은 `PGPT_PROXY_UNSTREAM` 이었다 |
| 진단(v19 · v21 · v23 · v24) — 시한 근방의 절단을 `execution_cuts` 로 · 오류 이벤트·잘린 스트림을 `stream_errors` · `stream_incomplete` 로 센다. 생성 요청마다 `request …`(모델 · effort · thinking · `max_tokens`) · `stream …`(첫 이벤트 · 첫 글자 시각 · 출력 토큰 · 종료 사유) · `complete …`(대기 · 머리 · 상류 · 전체 초) 줄과 게이트웨이 요청 번호(`gw=`)를 `proxy.log` 에 남긴다 | **쓴다** — 위 상한과 압축 길이 맞나를 회사에서 재는 자다. 프롬프트·응답 글자·인증 헤더는 안 남긴다. 요청 번호는 게이트웨이 팀이 제 장부를 찾는 열쇠다(옛 판에서 우리가 얹던 것 · #67) |
| 응답 머리를 기다리다 클라이언트가 끊으면 상류 연결도 닫는다(v21) · `/health` 의 `client_cancellations` | **쓴다** — 게이트웨이가 이미 시작한 생성까지 멈춘다는 보장은 없다 |
| 큰 요청 줄 세우기(v20~v22 · `PGPT_PROXY_HEAVY_BYTES` · 기본 `0`) | **논다** — 상류가 v22 에서 스스로 껐다. 「잘린 호출이 더 붐빌 때 시작했다」는 근거가 길이의 부수 현상이었고(긴 요청은 오래 살아 원래 많이 겹친다), 켠 판이 480초 절단(v20)과 재시도 소진(v21)을 만들었다 |
| `/v1beta` 통과 — Gemini CLI 가 루프백을 지난다 | **쓴다** — 프록시의 값은 보정이 아니라 **주소**다(CLI 가 `https` 아니면 거부하는데 `127.0.0.1` 만 `http` 를 허용한다 · 0041) |
| `/v1beta` — `-customtools` 접미사 제거 | **논다** — CLI 0.60 은 도구를 켜도 접미사를 안 붙인다(코드 주석은 0.55 기준) |
| **(우리 것)** `/v1beta` — `gemini-3.1-flash-lite-preview` → `gemini-3.1-flash-lite`(`_GEMINI_MODEL_ALIASES`) | **쓴다** — 안티그래비티(`agy`)가 **대화 제목 짓기에 이 이름을 못박아 둬서** 그 곁 호출만 `400` 으로 지던 자리다. 하이쿠 칸과 같은 병인데(`--model` 은 메인 턴만 못박고 곁 호출은 그 못을 안 탄다) **약이 다르다 — 같은 모델이 이름만 다르게 등록돼 있어 접미사만 고친다**(실측 2026-09-17 직결: `gemini-3.1-flash-lite` 는 `200` 에 `modelVersion` 도 그것 · `-preview` 는 `400`). ⚠ **이름으로 잡고 규칙으로 안 잡는다** — `-preview` 를 무조건 떼면 **게이트웨이에 실제로 있는** `gemini-3.1-pro-preview` 를 깨뜨린다(본 턴이 그 이름으로 통한다). 곁 호출이 새는 값은 제목이 안 붙는 것이고, 본 턴을 깨뜨리는 값은 아무것도 안 되는 것이다. ⚠ `agy` 쪽에 이 이름을 갈 손잡이가 없다 — 바이너리 상수다 |
| `/v1beta` — 쪼개진 SSE 재조립 | **안 걸렸다** — 탐침 한 판이라 「논다」로 굳히지 않는다. 게이트웨이 버릇이라 Gemini 를 실제로 쓰기 시작하면 다시 잰다 |
| `/v1beta` — `x-goog-api-key` 곁에 Bearer 추가 | **값이 없다** — 게이트웨이가 두 방식을 다 받는다(`Gemini-Posco.setting.md` 인증 절) · 원래 헤더만으로 200(직결 실측) |
| GPT-5·GPT-6 계열 `max_tokens` → `max_completion_tokens`(`/v1/responses` 는 `max_output_tokens`) | **논다** — Codex 가 이미 `max_output_tokens` 로 보낸다. 직결도 루프백도 0 |
| Hermes 갈래 — chat 문의 Gemini 변환 · `x-api-key` → Bearer | **논다** — Hermes 를 안 쓴다. Claude Code 는 Bearer 로 보낸다 |
| 개인 `x-api-key` 헤더 누출 방지 — `Authorization` 이 이미 있으면 `x-api-key` 제거 (v16) | **쓴다** (Claude Code) — 사용자 환경에 개인 `ANTHROPIC_API_KEY` 가 있어도 평문 HTTP 로 사내 게이트웨이에 새지 않는다 |
| 짝 없는 surrogate(`\ud83d` 등) JSON 인코딩 보호 | **쓴다** — 이모지 반쪽에서 잘린 문자열이 와도 예외로 죽지 않고 `\uXXXX` 로 되돌린다 |
| 경로 순회(`..` 및 `.`) 차단 | **쓴다** — `/gpgpta01-gpt/../other` 처럼 허용 접두어를 빠져나가 게이트웨이의 다른 서비스로 가려는 경로는 403 으로 막고 연결을 닫는다(`Connection: close`) |
| 청크 전송(`Transfer-Encoding: chunked`)의 끝 표시 | **쓴다** — 상류 응답을 끝까지 받았을 때만 끝 표시(`0\r\n\r\n`)를 보낸다. 상류가 도중에 끊기면 끝 표시 없이 닫아서, 클라이언트가 잘린 응답(`IncompleteRead`)으로 알아채게 한다. SSE 는 끝 이벤트까지 와야 「끝까지 받았다」로 친다(위 무결성 칸) |
| 상류 연결 풀 — 재시도는 한 번, 죽은 연결일 때만 | **쓴다** — 풀에서 꺼낸 연결이 이미 죽어 있어(stale) 응답 전에 끊겼을 때만 새 연결(fresh)로 한 번 더 보낸다. 새 연결이 실패하거나 시간이 넘은 것은 다시 보내지 않는다 — 같은 요청이 두 번 생성·과금되는 것을 막으려는 것이다 |
| 포트 잡기를 15초 동안 다시 시도 | **쓴다** — 재설치·키 교체로 프록시를 다시 띄울 때 옛 프록시의 연결이 아직 닫히는 중이면 포트 바인드가 잠깐 실패한다. 그 자리에서 죽으면 다음 로그인까지 프록시가 없으므로 15초 동안 다시 시도한다 |
| `PGPT_PROXY_PORT` 환경변수 | **쓴다** — 기본은 `18901`. 시험(`Test-ProxyFaults.py` · `pair_check.py`)은 이 값으로 다른 포트에 띄워, 떠 있는 프록시와 부딪히지 않는다 |
| `/health` 에 `pid` 포함 | **쓴다** — 설치기·검사기가 포트를 쥔 프로세스가 방금 제가 띄운 것인지 확인한다(한 PC 를 여럿이 쓰면 남의 프록시가 포트를 쥘 수 있다) |
| `gemini-` 모델 변환은 `/v1/chat/completions` 에서만 | **쓴다** — Gemini 네이티브로 옮기는 변환(위 Hermes 갈래)을 chat 경로에만 건다. `/v1/responses` 요청까지 옮기면 변환기가 `messages` 만 읽어 그 API 의 프롬프트를 잃는다 |
| 응답 | **거의 그대로 중계한다** — 스트리밍 포함, 생각 낱말도 안 건드린다. 손대는 것은 위 칸들뿐이다: 침묵 동안 끼우는 keepalive 주석 · `/v1beta` 의 쪼개진 SSE 재조립 · Hermes 갈래의 Gemini→OpenAI 변환 · 비스트리밍 갈래의 SSE 짓기 · 웹서치 하위 요청의 답 짓기(위 우리 칸). 180초 벽을 중계로는 못 넘는다(`../ENV-posco.md`) — 넘는 길은 비스트리밍 갈래뿐이고(압축은 기본으로 그 길이다), 그 길의 `/v1/messages` 응답은 중계가 아니라 프록시가 지은 것이다 |

**프록시가 하는 일이 아닌 것 하나** — `POST /v1/messages/count_tokens` 는 게이트웨이에 없어 **404** 다(실측
775회). 클라이언트가 스스로 어림셈으로 넘어가고 느린 요청(`slow`)도 0건이라 지연을 안 만든다 — 고칠 일이
아니라 알아 둘 일이다.

## 실행 규약

- 듣는 자리 `127.0.0.1:18901` (환경변수 `PGPT_PROXY_PORT` 로 바꿀 수 있다 · 포트를 받는 명령 인자는 없다) · 받는 경로는 `/gpgpta01-gpt/` 아래뿐
- 상류는 `PGPT_PROXY_UPSTREAM` (기본 `http://aigpt.posco.net`) — 사내 `HTTP_PROXY` 를 **안 탄다**(직결)
- `proxy.log` 와 `opus5_proxy.pid` 를 **제 파일 곁에** 쓴다 — 그래서 설치기는 이 파일을 실행 폴더로 복사해 띄운다.
  저장소·홈 사본에서 바로 띄우면 그 곁에 남고, 저장소는 `.gitignore` 가 받는다
- `GET /health` — `status` · `service` · `version` · `pid` · 계수(`trimmed_prefills` · `hoisted_images` · `web_search_filled` · `web_search_failed` · `execution_cuts` ·
  `max_tokens_hits` 등)와 지금 걸린 손잡이(`compact_concise` · `compact_unstream` · `stream_max_tokens` 등)
- `--self-test` — 보정 함수를 스스로 검사하고 끝난다(프록시는 안 뜬다)

## 재는 법

```bash
python -X utf8 posco/pgpt-proxy/opus5_proxy.py --self-test     # 보정 함수 — 어디서나
python -X utf8 posco/pgpt-proxy/pair_check.py                 # 400 이 사라지나 — 어디서나 (가짜 게이트웨이)
python -X utf8 posco/pgpt-proxy/hoist_check.py                # 그림 끌어내기가 본문 모양을 옳게 바꾸나 — 어디서나 (망 없음)
python -X utf8 posco/pgpt-proxy/websearch_check.py           # 웹서치 메움 — CLI 꼴 요청 · 모델이 받을 글 — 어디서나 (가짜 게이트웨이)
python -X utf8 posco/pgpt-proxy/Test-ProxyFaults.py          # 비정상 응답·스트림 단절 등 결함 내성 — 어디서나
python -X utf8 posco/pgpt-proxy/Test-ProxyStreaming.py       # 스트림 무결성 · 진단 줄 — 어디서나
python -X utf8 posco/pgpt-proxy/Test-ProxyCompaction.py      # 압축 알아보기 · 출력 상한 — 어디서나 (망 없음)
python -X utf8 posco/pgpt-proxy/Test-ProxyUnstream.py        # 비스트리밍 갈래 — 어디서나
python -X utf8 posco/pgpt-proxy/Test-ProxyQueue.py           # 줄 세우기(꺼진 채 둘이 통하나) — 어디서나
MOCK_SLOW_SEC=4 MOCK_ANSWER=tool_use python -X utf8 posco/pgpt-proxy/mock_gateway.py 18902
#   느린 비스트리밍 답 — 답 꼴은 text·tool_use·error500 · 상류가 받은 몸은 GET /gpgpta01-gpt/_mock/last
PGPT_API_KEY=<회사 키> python -X utf8 posco/pgpt-proxy/Test-AllPgptModels.py   # 회사 · 프록시가 떠 있어야

# 그림이 정말 보이나 — **회사** · 별 포트에 이 판을 띄워 두고 잰다 (#76)
PGPT_PROXY_PORT=18907 python -X utf8 posco/pgpt-proxy/opus5_proxy.py &
python -X utf8 posco/pgpt-proxy/hoist_live_check.py 18907      # 보정 없는 판은 못 보고 이 판은 맞히나
python -X utf8 posco/pgpt-proxy/image_lane_probe.py claude-opus-5 gpt-5.2   # 어느 자리의 그림을 보나
python -X utf8 posco/pgpt-proxy/image_tail_probe.py claude-opus-5           # tool_result 가 마지막일 때
```

⚠ **눈가림 셋(`hoist_live_check.py` · `image_lane_probe.py` · `image_tail_probe.py`)은 정답을 화면에 안 찍는다** —
곁 파일에만 적는다(`%TEMP%\*-answer.txt`). 재는 사람도 정답을 먼저 보지 않는 것이 요점이다: 아는 값을
맞히는 것은 재는 것이 아니다. `hoist_live_check.py` 는 정답과의 대조까지 스스로 하고 판정 한 줄을 낸다.

⚠ **출력 상한과 압축 길은 회사에서만 갈린다** — 집에서 초록인 것은 중계 코드까지다. 회사에서는 이 판으로 긴 턴과
압축을 돈 뒤 `/health` 를 본다: `execution_cuts`(180초 근방 절단)가 늘면 스트리밍 상한이 벽 밖이다 ·
`max_tokens_hits` 가 늘었으면 그 세션이 이어 쓰기로 넘어갔나 본다 · `compact_unstream: true` · `compact_concise: false`.
`proxy.log` 의 `kind=compact … transport=unstream` 줄과 그 `complete …` 의 `upstream=` 초가 압축 한 번의 길이다.

전수 스모크는 키를 `PGPT_API_KEY` 나 홈 `.claude/settings.json` 의 `ANTHROPIC_AUTH_TOKEN` 에서 읽는다.

## 상류에서 새 판을 받을 때

1. 상류 파일(위 표에서 「상류 자리」가 적힌 것)을 그대로 복사한다 — `diff --strip-trailing-cr` 로 대조하면
   줄끝 잡음이 안 낀다.
   ⚠ `opus5_proxy.py` 는 복사한 뒤 **우리 덩어리 넷과 판 번호를 다시 얹는다** — 복사한 뒤 `git diff` 로 직전 판과
   견주면 상류가 바꾼 것과 복사로 지워진 우리 덩어리가 함께 보인다.
   - 제미나이 이름 표 — `_GEMINI_MODEL_ALIASES` · `normalize_gemini_model_path` 의 그 조회
     (상류 함수가 `-customtools` 만 떼므로 **그 함수 안에 한 줄이 든다**) · 자체 검사 세 칸
   - 그림 끌어내기(이슈 #76) — `_HOISTED_IMAGES` · `_count_hoisted` · `stats()` 의 `hoisted_images` ·
     `hoist_tool_result_images` · `sanitize_payload` 가 **합치기보다 앞에서** 부르는 한 줄 · 머리 설명의 한 칸
     ⚠ **그 순서가 뜻을 진다** — 합친 뒤에 부르면 같은 메시지를 두 번 훑는다. 그리고 그림은
     `tool_result` **뒤**로만 가야 한다: 앞에 끼우면 게이트웨이가 짝 검사에서 400 을 낸다(실측)
   - 압축 간결 지시 끔(결정 0082) — `COMPACT_CONCISE` 의 기본값 `"0"` 과 그 곁말 · 자체 검사 한 칸
   - 웹서치 메움(#118) — 상수 셋(`WEB_SEARCH` · `WEB_SEARCH_MODEL` · `_WEB_SEARCH_PROMPT_HEAD`) · 계수 둘과
     `_count_web_search` · `stats()` 의 네 칸 · `web_search_tool` 부터 `web_search_error_message` 까지의 함수 묶음 ·
     `anthropic_message_events` 의 `web_search_tool_result` 갈래 · `_forward_request` 의 `web_search` 갈래(알아보기 ·
     머리 · 경로 · 공급자 · 답 짓기) · 머리 설명 한 칸 · 자체 검사 한 칸
     ⚠ **답 짓기 갈래는 제미나이 chat 변환 갈래보다 앞이고 상태 코드를 안 가린다** — 상류가 지면(4xx · 5xx)
     그대로 중계하지 않고 검색 오류 칸으로 돌려줘야 대화가 안 깨진다
   - 판 번호 — `VERSION = 정수` 한 줄을 `VERSION_UPSTREAM` · `VERSION_OURS` · `VERSION` 셋으로
   - 하이쿠 칸 곁말의 출처 표기 — 상류가 우리 계정 이름을 적어 두었으면 뺀다. ⚠ 안 빼면 배포본 뽑기가
     「새면 안 되는 글자」로 멈춘다. 상류가 새로 지은 가짜 키가 같은 검사에 걸리면 상류 파일은 두고
     `dist.manifest.conf` 의 `#자리표시자` 줄에 그 값을 더한다
   ⚠ 시험 파일은 **프록시를 찾는 경로 줄**을 같은 폴더로 고친다(`ROOT` · `"app/opus5_proxy.py"`). 그리고
   `Test-ProxyStreaming.py` 의 압축 HTTP 경로 시험이 간결 지시 기본값을 박아 두었으면 그 단언을 우리 기본값에 맞춘다
   ⚠ `mock_gateway.py` 에도 얹을 것이 있다 — `SLOW_SEC`/`ANSWER`/`LAST` · `_body` 의 `raw_body` ·
   `_mock/last` 창구 · `/v1/messages` 의 답 세 꼴
   ⚠ 상류가 새 시험 파일을 더했으면 위 표에 줄을 더하고 같은 경로 고침을 한다
2. 위 「상류 판」의 커밋을 고치고 **판 번호 두 칸을 옮긴다** — `VERSION_UPSTREAM` 을 받아온 판으로 올리고
   `VERSION_OURS` 를 **0 으로 되돌린다.** 그다음 우리 덩어리를 다시 얹은 만큼만 뒤 칸을 올린다.
   ⚠ **뒤 칸을 안 되돌리면 번호가 뜻을 잃는다** — 그 수는 「이 상류 판 위에 우리가 몇 번 얹었나」다
3. 「재는 법」의 **어디서나** 줄이 다 초록인지 보고, `ruff check posco/pgpt-proxy/` 를 돌린다 — 상류 시험이 판정에
   걸리면 우리 자로 고치지 않고 뿌리 `ruff.toml` 의 제외에 더한다. 프록시가 새 보정을 얹었으면 위 표에
   「쓴다/논다」를 더한다. ⚠ **`hoist_live_check.py` 와 출력 상한·압축 길은 회사에서만 선다** — 실물 게이트웨이가
   있어야 잰다. 집에서 초록인 것은 모양까지고, 그 경계를 판정 옆에 적는다

## 안 담은 것

상류의 설치기(`Install-*.ps1` · `START-*.bat` · `PGPT.*.ps1` · `Update-Proxy.ps1` · `Reset-ClaudeCompaction.ps1`)와
Hermes·Paseo·Grok 갈래, 문서. 우리 설치는 PAISetup `install.ps1` 이 들고, 이 폴더는 그 설치가 복사해 가는 **재료**다.
⚠ **상류 설치기의 압축 설정은 안 받는다** — 1M 문맥 끄기(`CLAUDE_CODE_DISABLE_1M_CONTEXT`) · 창 200K
(`CLAUDE_CODE_AUTO_COMPACT_WINDOW`) · 압축 비율(`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` 45·60). 창을 200K 로 묶고 압축을
당겨 압축이 되풀이되던 것을 상류가 그 판들에서 수습했는데, 우리는 창을 1M 으로 열어(결정 0049) 그 원인이 없다(결정 0082)
