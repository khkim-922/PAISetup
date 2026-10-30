# pgpt-proxy — 사내 게이트웨이 앞의 로컬 프록시

사내 게이트웨이(P-GPT)가 그대로는 안 받는 요청을 PC 안에서 고쳐 넘기는 프록시다. `127.0.0.1:18901` 에서
클라이언트의 요청을 받아, 본문을 게이트웨이가 받는 꼴로 고친 뒤 넘긴다.

코드는 사내 동료(GitHub `sejuone-cloud`)의 비공개 저장소 `pgpt-one-click-connect` 에서 왔다. 그 v33 을 마지막으로
받았고, 그 뒤로는 **우리 판이다 — 상류를 따라가지 않는다**(결정 0163). 누가 이 프록시를 지나나는 결정 기록
0041(사내는 키 하나로 통일하고 Claude 길은 루프백 프록시를 지난다)이 정했고, 안티그래비티(`agy`)는 게이트웨이에
바로 붙는다(0203).

- **Claude Code** — 게이트웨이에 바로 붙으면 Read 로 연 그림이 모델에 안 실리고 WebSearch 가 0건이며(회사 실측 2026-10-30 · #226 ⑦),
  Opus 5 가 1 이 아닌 `temperature` 와 모든 `top_p` 를 400 으로 거절한다(같은 날 · #226). 그림 끌어내기 · 웹서치 메움 ·
  `temperature`/`top_p` 떼기가 그 셋을 메우고, 출력 상한이 긴 생각 턴을 앞단의 300초 벽 앞에서 끝낸다(아래 「출력 상한」 칸).
  assistant prefill 은 지금 게이트웨이가 받는다(#226) — 프록시가 그것을 떼는 까닭은 아래 「`/v1/messages`」 칸이 든다
- **Codex** — 내장 검색이 게이트웨이에 없는 `/v1/alpha/search` 로 나가므로 프록시를 지난다. 프록시가 같은
  게이트웨이의 `/v1/responses` + `web_search` 길로 바꾸고 Codex 의 `SearchResponse` 꼴로 되돌린다
- **안티그래비티(`agy`)는 지나지 않는다** — `GOOGLE_GEMINI_BASE_URL` 이 게이트웨이를 바로 가리켜 프록시가 꺼져도 agy 는
  선다(결정 0203). 대화 제목 짓기의 곁 호출만 agy 가 박아 둔 `gemini-3.1-flash-lite-preview` 가 게이트웨이에 없어 400 으로
  지고(#226 ⑯) 제목이 안 붙는다 — 본 턴은 선다. 이 문으로 온 `/v1beta` 요청은 고치지 않고 그대로 넘긴다(아래 쓰임 표)

| 파일 | 온 자리 | 무엇 |
|---|---|---|
| `opus5_proxy.py` | 상류 `app/opus5_proxy.py` v33 + 우리 덩어리 | 프록시 본체. 표준 라이브러리만 쓴다 |
| `mock_gateway.py` | 상류 `tests/` + 우리 칸 하나 | 가짜 게이트웨이 — prefill 에 400 을 내 프록시의 끝 assistant 떼기가 도는지 드러낸다(실물 게이트웨이는 지금 prefill 을 받는다 · #226). 사내망 밖에서 프록시를 끝까지 돌려 볼 때 |
| `Test-AllPgptModels.py` | 상류 `tests/` | 모델 전수 스모크 — 프록시 너머로 모델마다 「Reply OK」 한 줄. 결과는 곁 `model-results/` |
| `Test-ProxyFaults.py` | 상류 `tests/` | 비정상 응답·스트림 단절·413·surrogate·180초 절단 계수 · 깨진 본문 400 · 모델 대체 표시 등 결함 내성 검사 |
| `Test-ProxyStreaming.py` | 상류 `tests/` | 스트림 무결성 — 이벤트 경계의 주석 · 길이 선언 SSE · 끝 이벤트 검증 · 진단 줄 |
| `Test-ProxyCompaction.py` | 상류 `tests/` | 압축 알아보기 · 출력 상한 · thinking 예산 |
| `Test-ProxyUnstream.py` | 상류 `tests/` | 비스트리밍 갈래 — 압축이 비스트리밍·18,000 으로 가나 · 짓는 SSE · 압축 답의 도구 호출과 깨진 답은 오류 |
| `Test-ProxyImages.py` | 상류 `tests/` + 우리 칸 | 그림 끌어내기 — 본문 모양 · 짝 · 계수 · 끄는 스위치 · PDF 가 제자리에서 안내 글로 바뀌나 · 옮긴 묶음의 캐시 표식(Claude Code 실물 꼴로 앞 저장 지점이 20 칸 안에 드나) (망 없음) |
| `Test-ProxyModelMap.py` | 상류 `tests/` | 모델 대체 — 게이트웨이 목록 조회 · 담아 두기 · 못 읽을 때의 규칙 · `PGPT_PROXY_MODEL_MAP` |
| `Test-ProxyWebSearch.py` | 상류 `tests/` | Claude 웹서치 메움 — 알아보기 · 답 짓기 · 안 건드릴 요청 · 오류 갈래 |
| `Test-ProxyChunkedBody.py` | (우리 것) | 본문 받기 — `Transfer-Encoding` 이 붙은 요청이 바르든 깨졌든 411 이고 상류로 안 가나 · 기록에 본문 바이트가 안 남나 |
| `pair_check.py` | (우리 것) | 프록시와 가짜 게이트웨이를 함께 띄워 「직결 400 · 프록시 200 · prefill 1번 뗐다」를 잰다 |
| `codex_websearch_check.py` | (우리 것) | Codex 검색 메움 — `/v1/alpha/search` 요청이 Responses 웹 검색으로 가고 `SearchResponse` 로 돌아오나 · 상류로 가는 `web_search` 도구가 손대지 않은 꼴인가 |
| `hoist_live_check.py` | (우리 것) | 그림 끌어내기를 **실호출로** — 직결은 못 보고 프록시 너머는 그림을 맞히나 (눈가림) |
| `image_lane_probe.py` | (우리 것) | 게이트웨이가 **어느 자리**의 그림을 보나 — 다섯 갈래를 한 그림으로 재는 눈가림 프로브 |
| `cache_ttl_probe.py` | (우리 것) | 캐시 1시간이 게이트웨이 너머에서 서나 — 1시간 갈래와 대조 갈래를 시작 간격 8분으로 두 번씩 스트리밍으로 부른다(캐시 쓰기 항은 스트리밍에만 온다 · 회사 · 결정 0174). 결과는 곁 `cache-ttl-probe-<시각>.json` |
| `cache_usage_report.py` | (우리 것) | 실제 세션이 캐시를 얼마나 읽고 다시 썼나 — Claude Code 대화 기록(`~/.claude/projects`)의 사용량을 요청마다 읽어 5분 안의 다시 쓰기(깨짐)와 5분 넘게 쉰 뒤의 읽기(1시간)를 센다. 프록시 판과 무관하다 |
| `image_tail_probe.py` | (우리 것) | `tool_result` 가 **마지막**일 때(= `Read` 의 실제 꼴) 어디에 두면 보나 |
| `watchdog.ps1` | (우리 것 · PAISetup `284757c`) | 감시자 — 5초마다 `opus5_proxy.py` 를 돌리는 파이썬 프로세스가 있나 보고, 없으면 `pythonw` 로 창 없이 다시 띄운다. 뮤텍스(이름 `PGPTProxy-Supervisor`)로 한 개만 돌고, 프록시 파일과 같은 폴더에 감시 기록(watchdog.log)을 남긴다 |

## 판과 우리 덩어리

- **판 번호는 두 칸이다 — 지금 `33.14`**(`VERSION_UPSTREAM` · `VERSION_OURS`). 앞 칸은 마지막으로 받은 상류 판이라
  33 에 선다. 뒤 칸은 그 위에 우리가 얹은 덩어리 수고, 앞으로 우리 고침은 이 칸이 센다
  ⚠ **`/health` 는 사람이 읽기 좋게 `33.14` 한 줄을 내지만, 판을 견주는 설치기는 두 수를 따로 정수로 읽는다** —
  점 찍힌 문자열을 그대로 견주면 `"9" > "10"` 이 되기 때문이다. 설치기는 그렇게 견주어 낮으면 갈아 끼운다
  (`install.ps1` 프록시 칸)
  ⚠ **정수 한 칸(`17`·`26`)이 도는 자리도 받는다** — 옛 판과 상류 판은 두 이름이 없어 「못 읽었다」로 떨어지고,
  그때는 **갈아 끼우는 쪽으로 기운다.** 반대로 두면 옛 프록시가 영영 안 바뀐다
- 작성자 허락 2026-09-14 (라이선스 파일은 상류에 없다 — 허락으로 든다)
- **우리 덩어리 다섯** — 상류 v33 에 없는 것이다.
  ⑴ **Codex 검색 메움**(`codex_web_search` 부터 `responses_web_search_to_codex` 까지의 함수 묶음 · `is_generation_request`
  의 `/v1/alpha/search` 줄 · `_forward_request` 의 `codex_fill` 갈래들 · 머리 설명 한 칸) — Codex 의 독립
  `/v1/alpha/search` 는 게이트웨이에 없어, 같은 게이트웨이의 `/v1/responses` + `web_search` 로 바꾸고
  `SearchResponse` 로 되돌린다(이슈 #121 · 결정 0096). 못 닿음 · 시한 · 상태 코드 가르기는 Claude 웹서치 메움의 갈래를
  함께 타되, 답은 Codex 꼴로 짓는다
  ⑵ **페이블 그대로 보내기**(`needs_model_list` · `_CLAUDE_FALLBACK_FAMILIES` 에 `claude-fable-*` 가 없다) — 상류는
  목록에 없는 페이블을 오퍼스로 바꿔 보내지만, 사람이 고르는 이름을 조용히 구해 주면 400 이 보여야 할 자리에 다른
  모델이 200 으로 답한다(결정 0164). 그래서 철자만 고쳐 그대로 보낸다. 자체 검사의 페이블 줄(`needs_model_list` 대조
  포함)과 `Test-ProxyModelMap.py` 의 첫 페이블 검사(400 · 목록 안 읽음)가 이를 단언한다
  ⑶ **그림만 옮기기**(`_HOISTED_BLOCKS` 가 `{"image"}` · 회사 실측 · 결정 0165) — 상류는 PDF 도 옮긴다. 게이트웨이는
  PDF(`document`)를 자리와 상관없이 삼켜, 옮기면 `tool_result` 에 「붙였다」는 표지만 남고 모델은 PDF 가 왔다고 믿는다.
  자체 검사의 섞인 칸(`[document, image]` 에서 그림만 나간다)과 `Test-ProxyImages.py` 의 PDF 칸 · PDF + PNG 칸이 이를 단언한다
  ⑷ **옮긴 그림 묶음의 캐시 표식**(`_mark_hoisted_run` · 결정 0175) — 마지막 user 메시지에서 그림을 옮겼으면 그 묶음의
  빠진 쪽에 그 메시지의 표식을 본떠 단다(끝에 표식이 있으면 묶음 앞 `tool_result` 에, 앞에 있으면 묶음의 마지막 이름표에). 캐시는
  표식에서 뒤로 20 칸까지만 앞 요청의 저장 지점을 찾는데, 옮기기가 그림 한 장을 두 칸(이름표 · 그림)으로 늘려 그림 많은 턴이
  그 창을 넘긴다 — 그 턴은 대화 전체를 캐시 없이 다시 쓴다. 표식 한도(4)가 찼거나 그 메시지에 표식이 없으면 안 단다.
  ⚠ 게이트웨이는 요청을 Bedrock Converse 로 옮긴다(`../Claude-Posco.setting.md`) — Converse 의 캐시 표식은 `cachePoint` 블록뿐이고
  게이트웨이 너머 캐시가 걸리는 것은 실측이니(`../ENV-posco.md`), 표식은 그 블록으로 옮겨 선다. 그래서 표식은
  `tool_result` 뒤 · 글 뒤에만 단다. 그림 바로 뒤의 `cachePoint` 는 문서에도 실측에도 없다. ⚠ Bedrock 은 잇단 `tool_use` ·
  `tool_result` 를 한 칸으로 안 묶고 블록마다 센다는 남의 실측이 있다 — 그 셈법에서는 도구를 열 개 넘게 병렬로 부른 턴이 그림 없이도
  창 밖이고, 그것은 프록시가 못 구한다. 이 덩어리가 구하는 것은 한 도구 결과에 그림이 몰린 턴(PDF 쪽 · 캡처)이다.
  자체 검사의 표식 칸과 `Test-ProxyImages.py` 의 실물 꼴 칸(Claude Code 2.1.304 의 표식 배치 · 그림 12장에서 고치기 전 28 칸 →
  고친 뒤 20 칸 안 · Read 한 번에 그림 20장은 두 셈법 다 44 칸 → 20 칸 안)이 이를 단언한다
  ⑸ **사용량 칸**(`merge_usage` · `usage_text` · 결정 0175) — Claude 응답의 입력 · 캐시 읽기 · 캐시 쓰기 항을 기존
  `stream …` · `complete …` 줄에 숫자로 싣는다(아래 「진단」 칸). 자체 검사의 사용량 칸(게이트웨이 꼴 · 직결 꼴)과
  `Test-ProxyStreaming.py` 의 진단 줄 시험이 이를 단언한다
- **우리가 먼저 재고 지은 둘은 상류가 같은 꼴로 들여 상류 코드가 든다** — 그림 끌어내기(v31 · 이슈 #76) · Claude
  웹서치 메움(v27 · 이슈 #118 · 결정 0087). 무엇이 같았고 무엇을 더 받았나는 결정 0163.
  그 가운데 그림 끌어내기가 옮기는 블록은 위 ⑶ 이 바꾼다
- **상류 v33 에서 달라진 곳 — 우리 덩어리 말고** — 주석과 docstring 은 우리 꼴이다(코드 룰 [Comment Shape] · 서술은
  한국어). ruff 고침 다섯(예외를 다시 낼 때 원인 연결 셋 · 람다가 반복 변수를 값으로 묶기 · 안 쓰는 `import`)은 동작을 안
  바꾼다. 그 밖에 시험 파일의 프록시를 찾는 경로 줄(상류는 `app/` 아래, 우리는 같은 폴더) ·
  `Test-ProxyImages.py` 의 가짜 키(`xxxx` 꼴 — 배포본 뽑기의 「새면 안 되는 꼴」을 비켜선다 · `dist.manifest.conf`) ·
  `mock_gateway.py` 의 느린 비스트리밍 답 한 칸(`MOCK_SLOW_SEC` · `MOCK_ANSWER` · `_mock/last` — 비스트리밍 갈래를
  사내망 밖에서 잴 때) · 하이쿠 곁말의 출처 표기에서 뺀 우리 계정 이름(배포본 뽑기가 그 이름을 「새면 안
  되는 글자」로 문다). 상류가 CRLF 인 것은 이 저장소 규칙(`.gitattributes`)이 LF 로 눕힌다
- **ruff** — 이 폴더 전체가 전역 판정을 받는다(뿌리 `ruff.toml` 이 빼는 파일이 없다)

## 무엇을 쓰고 무엇이 노나

칸마다 회사 로그 실측이 든다 — 25시간 3039줄(2026-09-15 08:04 ~ 09-16 09:03) + Gemini·Codex 탐침 한 판씩.
그 실측은 옛 판(`17.x`) 때 것이다. **`26.x` · `33.x` 에서 새로 든 칸은 그 칸이 회사 실측을 따로 적지 않았으면 회사에서
아직 안 쟀다** — 그 칸의 근거는 상류의 회사 실측(같은 게이트웨이)이고, 그렇게 적었다. 무엇을 회사에서 재야 하나는 이슈 #193 이 든다.
**「논다」는 걷을 후보다** — 우리 클라이언트가 안 보내는 요청에만 걸린다. 걷는 근거가 설정 · 코드 · 실측으로 서면 걷고,
클라이언트가 그 꼴을 안 보낸다는 것에만 기대면 회사에서 잰 뒤 걷는다(결정 0201 · 회사 실측 #226).

| 프록시가 하는 일 | 우리 |
|---|---|
| `/v1/messages` — 끝의 assistant 마디 제거 · `system` 역할 마디를 `user` 로 · 같은 역할 병합 · `temperature`/`top_p` 제거 | **쓴다** (Claude Code) — `trimmed_prefills` 가 센다(회사에서 1회 · #226 ②). `temperature`/`top_p` 떼기는 Bedrock 의 400 을 막는다 — Opus 5 는 1 이 아닌 `temperature` 와 모든 `top_p` 를(`deprecated for this model`), sonnet-4.6 은 둘을 함께 보내면(`cannot both be specified`) 거절한다(회사 실측 2026-10-30 · #226). 끝 assistant 떼기와 system→user 는 게이트웨이 탓이 아니다 — 게이트웨이는 prefill 네 꼴과 system 세 꼴을 다 받는다(#226 ⑩). 프록시 안의 압축 알아보기 · 압축 이어 쓰기 알아보기 · 웹서치 질의 알아보기가 「마지막 메시지는 user」에 기대고, system→user 가 맨 앞 system 을 머리 떼기에서 살려서 둔다 |
| **모델 대체**(v32 · `resolve_claude_model`) — 대체 대상 이름(하이쿠 · `claude-sonnet-5*`)일 때만 게이트웨이 `/v1/models` 를 그 요청의 키로 읽어(키마다 10분 · `PGPT_PROXY_MODEL_LIST_TTL_SEC` · 시한 5초 · 못 읽으면 60초 쉰다) 목록에 있으면 그대로, 없으면 같은 계열의 가장 새 판으로 보낸다. 목록을 못 읽으면 고정 규칙(하이쿠는 아래 하이쿠 칸 · `claude-sonnet-5*` 는 `claude-sonnet-4.6`)으로 간다. `-latest` 같은 판을 안 박은 별칭은 대상이 아니다 — 우리 클라이언트는 안 보내고(회사 로그 모델 줄 1,373 에 0 · 2026-10-30 · #226) 보내면 400 이 보인다(0164). `PGPT_PROXY_MODEL_MAP`(`glob=target;…`)이 목록보다 먼저다. `PGPT_PROXY_MODEL_LIST_TTL_SEC=0` 이면 고정 규칙만 | **쓴다 · 758회**(`claude-sonnet-5` · 옛 판 실측) — `ANTHROPIC_MODEL` 은 메인 세션의 모델 하나만 못박고, Claude Code 가 스스로 부르는 곁 호출(서브에이전트·요약·모델 피커의 다른 칩)은 그 못을 안 타고 제 이름을 보낸다. 목록 조회는 회사에서 섰다(2026-10-18 · `model_list_fetches` 1 · `failures` 0 · 목록 28 · `by=list` · #193 ③㉤). 메인 턴(`claude-opus-5`)은 목록을 안 읽는다. `claude-fable-*` 는 대상이 아니라 철자만 고쳐 그대로 간다(우리 것 ⑵ · 결정 0164) |
| 하이쿠 → `claude-sonnet-4.6` (`CLAUDE_HAIKU_SUBSTITUTE` · 상류 v18) — 위 목록을 못 읽었을 때의 자리 | **쓴다** — 하이쿠는 이 게이트웨이에 **한 판도 없다**(`GET /v1/models` 실측 2026-09-17 · Claude 는 opus 4.5·4.6·4.7·5 와 sonnet 4.5·4.6 여섯뿐). 그래서 서브에이전트 호출이 통째로 `400`(「모델을 찾을 수 없습니다」)으로 지던 자리다. **이름을 목록으로 안 잡고 규칙으로 잡는다** — 클라이언트가 아는 하이쿠 이름이 열둘이라 판이 오를 때마다 샌다. 실측: `claude-haiku-4-5` · 날짜박은 판 둘 다 `200` 에 `model: claude-sonnet-4.6`. 게이트웨이 목록에 하이쿠가 서면 목록이 먼저라 이 규칙은 안 걸린다 |
| 대시 모델 ID 복원 — `claude-opus-4-7` → `claude-opus-4.7` | **쓴다 · 6회** — 같은 곁 호출 길. 별칭과 한 함수(`normalize_claude_model_id`)라 바뀌면 로그 한 줄이 찍힌다 |
| **대체 표시**(v29 · v32) — 바꿔 보낸 호출은 `proxy.log` 에 `SUBSTITUTED <보낸 이름> -> <간 이름> by=list·fixed·config` 로, 철자만 고친 것은 `restored` 로 따로 적는다 · `/health` 의 `model_substitutions` · 응답 머리 `x-pgpt-model-substituted`(`/v1/messages` 만 · Codex 는 안 받는다) | **쓴다** — 바꿔 보낸 200 을 그 모델이 된 것으로 읽지 않게 한다. 모델이 게이트웨이에 있나는 프록시가 아니라 직결로 잰다(`scripts/probe-gateway-models.sh`) |
| 빈 도구 `description` 채우기(`patch_tool_descriptions`) — Claude 의 `/v1/messages` 본문의 최상위 `tools` 만. Responses · `/v1beta` · `/v1/chat/completions` 와 웹서치 · Codex 검색 메움이 지은 본문은 손대지 않는다 | **쓴다 · 6회** (Claude Code) — 게이트웨이가 Messages 를 Bedrock Converse 로 옮기고(`../Claude-Posco.setting.md`) Converse 의 도구 설명은 한 글자 이상이어야 한다. Responses 는 빈 설명을 그대로 받는다 — 최상위 함수 도구도, Codex 가 MCP 도구를 싣는 namespace 의 안쪽 · 바깥도(`gpt-5.6-sol` · `gpt-6-astra` 다 200 · 회사 실측 2026-10-30 · #226 ⑮ ⑰). ⚠ `description` **칸 자체가 없으면** Responses 도 400 이다(`Missing required parameter` · 같은 날 · #226) — 지금 Codex 는 빈 글자를 실어 안 걸린다. 그 400 이 Codex 에 보이면 칸이 없을 때만 채우는 갈래를 Responses 에 되살린다 |
| **Claude 웹서치 메움**(v27 · v28) — 서버 도구 `web_search_*` 를 선언하고 마지막 user 글이 하위 요청 머리(「Perform a web search for the query:」)로 시작하는 요청을 게이트웨이의 제미나이 검색(`googleSearch` grounding · `PGPT_PROXY_WEB_SEARCH_MODEL` · 기본 `gemini-3.6-flash`)으로 메워 `server_tool_use` · `web_search_tool_result` · `text` 세 칸으로 지어 돌려준다. 출처는 구글 경유 주소 그대로 싣고, 허용 · 막는 도메인은 제미나이가 준 도메인 · 제목을 눕혀 견준다. 게이트웨이에 못 닿거나 90초를 넘기면 검색 오류 칸으로 답한다 · `/health` 의 `web_search_filled` · `web_search_failed` · `web_search_empty` · 끄려면 `PGPT_PROXY_WEB_SEARCH=0` | **쓴다** — 게이트웨이가 그 선언을 클라이언트 `tool_use` 로 되돌려 아무도 검색하지 않아 결과 0 건이던 자리다(사내 실측 2026-10-08 · #118). 제미나이 grounding 이 실제 웹을 찾는 것은 실측됐다. 머리로 알아보는 조건과 허용 도메인 견주기는 회사에서 섰다(2026-10-18 · `web_search_filled` 4 · `empty` 0 · `failed` 0 · 허용 도메인 칸의 출처 셋이 다 python.org · #193 ③㉢). 출처를 원래 주소로 풀지 않는 까닭 — 사내 웹필터가 구글 클라우드를 200 차단 페이지로 받아, 3xx 와 `Location` 을 기다리는 풀기가 출처 14 개에 하나도 못 풀었다(결정 0165). Claude 를 안 거치므로 상류 호출은 하나다. ⚠ 게이트웨이가 왜 그 선언을 바꾸는지는 밖에서 안 보여, 게이트웨이가 바뀌면 이 칸이 조용히 어긋날 수 있다 |
| **(우리 것)** Codex 의 `/v1/alpha/search`를 게이트웨이의 `/v1/responses` + `web_search`로 메워 `output` · `results`를 돌려준다(위 ⑴) · 못 닿음 · 90초 · 상태 코드 가르기는 위 칸의 갈래를 함께 탄다 | **쓴다 · 상류 능력 사내 실측 2026-10-09** — 같은 게이트웨이의 Responses 웹 검색이 `search`와 `open_page`를 수행하고 URL 인용을 돌려주는 것을 확인했다(#121). Codex 설정은 루프백 `base_url` · `supports_standalone_web_search=true` · `web_search="live"`. 계수는 Claude 웹서치와 같은 `web_search_*` 를 쓴다 — `/health` 로는 둘이 안 갈린다 |
| **그림 끌어내기**(v31 · `_hoist_tool_images`) — `tool_result` 안의 `image` 를 같은 user 메시지의 마지막 `tool_result` **바로 뒤**로 옮기고, 옮긴 그림마다 앞에 `[image from tool result <id>]` 이름표를, 빈 자리에 「[image attached after this tool result]」를 적는다. `document`(PDF)는 안 옮긴다(우리 것 ⑶) — 옮기기 앞에 아래 「PDF 안내 글」 칸이 글로 바꾼다. 역할 합치기 **뒤**에 돌고, 옮기는 그림의 `cache_control` 은 뗀다 · 마지막 user 메시지의 묶음 양쪽에 캐시 표식을 세운다(우리 것 ⑷) · `/health` 의 `hoisted_tool_images`(옮긴 그림 수) · `hoist_cache_marks`(단 표식 수) · `hoist_cache_marks_skipped`(한도가 차 못 단 수) · 끄려면 `PGPT_PROXY_HOIST_TOOL_IMAGES=0` | **쓴다** — 게이트웨이가 `tool_result` 안의 그림만 200 에 버리고 같은 바이트가 형제 블록으로 서면 읽는다(눈가림 실측 2026-09-22 · 이슈 #76). ⚠ 그림을 `tool_result` **앞**에 끼우면 짝 검사가 400 을 낸다 — 그래서 뒤로만 간다. 이 자리(이름표 · 뒤따르는 글 앞)는 회사에서 섰다(2026-10-18 · 눈가림 어긋남 0 · Claude Code 가 PNG 글자 `KRAKEN-7391-VOLT` 를 맞혔다 · #193 ③㉠). ⚠ **PDF(`document`)는 옮기지 않는다** — 게이트웨이가 자리와 상관없이 삼킨다(직결 · `tool_result` 안 · 옮긴 자리 셋 다 「안 보인다」 · #193 ③㉡ · 결정 0165). 옮기면 `tool_result` 에 「붙였다」는 표지만 남아 모델이 PDF 가 왔다고 믿는다. 회사에서 PDF 를 읽는 길은 페이지를 그림으로 그려 여는 것이다 — Read 가 poppler(`pdftoppm` · 설치기가 Claude 와 함께 깐다)로 스스로 그렇게 열어 이 그림 옮기기를 탄다(회사 실측 2026-10-18 · 두 판 다 첫 표의 값을 맞혔다 · #193 ③㉡ 뒤집기 코멘트). 감긴 PDF 는 `drm-office-read`(결정 0094). ⚠ **옮기면 블록 수가 늘어 캐시가 앞 요청을 못 찾을 수 있다** — 캐시는 표식에서 뒤로 20 칸까지만 찾고, `tool_result` 안에서 한 칸이던 그림이 밖에서는 이름표와 두 칸이 된다. 그래서 묶음 양쪽에 표식을 세운다(우리 것 ⑷). `hoist_cache_marks_skipped` 가 오르면 그 턴들은 대화 전체를 캐시 없이 다시 쓴 것이다 |
| **PDF 안내 글**(상류 v34 `3b1b3ad` · `_note_documents`) — user 턴과 그 안 `tool_result` 의 `document` 블록을 글로 바꾼다. PDF 는 「게이트웨이가 버려 이 파일은 안 보인다 · 짐작하지 마라 · Read 의 `pages` 로 다시 열어라 · 감긴 파일이면 `drm-office-read`」 안내(`_DOCUMENT_NOTE_TEXT`)로, 글 원본(`source.type` 이 text)은 그 글로. `cache_control` 은 제자리에 남긴다 · 역할 합치기 뒤 · 그림 끌어내기 앞에 돈다 · `/health` 의 `documents_noted` · 끄려면 `PGPT_PROXY_DOCUMENT_NOTE=0` | **쓴다** — Claude Code 는 작은 PDF 를 `pages` 없이 읽으면 `document` 블록으로 보내고, 게이트웨이가 그것을 삼켜 모델은 첫 문장도 못 받은 채 붙었다고 믿는다(회사 실측 2026-10-30 · VS Code 확장 2.1.314 · `hoisted_tool_images` 0 → 0 · #226 ⑥). 안내 글이 모델을 그림으로 여는 길(위 칸의 `pages`)로 돌린다. 상류의 안내 글은 우리 설치에 없는 스킬을 가리켜 글만 우리 길로 바꿨다 |
| 상류 연결 — 요청마다 새로 열고 응답을 다 읽으면 닫는다(`UpstreamTarget` · **(우리 것)** 상류 v33 의 keep-alive 풀을 걷었다) | **쓴다** — 다시 써서 아끼는 것이 접속 한 번의 손잡기뿐이다(회사 실측 p50 15.1 ms · 최대 46.4 ms · #226 ⑧ — 게이트웨이가 요청에 쓰는 평균 6.9초의 0.2%). 다시 쓰면 앞단이 쉬는 연결을 **정확히 30.0초**에 닫는 것과 겨루고(`front closed idle connection after 30.0s: EOF (FIN)`), 꺼낸 연결이 응답 전에 끊기면 다시 보내야 한다. 실패한 요청은 다시 보내지 않는다 — 게이트웨이가 이미 처리 중일 수 있어 생성이 두 번 돈다. 클라이언트(Claude Code · Codex)는 오류를 받으면 스스로 다시 보낸다(`cli-log` `attempt 1/11` · 결정 0202) |
| Anthropic · OpenAI SSE 가 침묵하면 `KEEPALIVE_SEC`(기본 15초)마다 `: keepalive` 주석 한 줄을 클라이언트에 흘린다(상류 v18) — 게이트웨이가 생각 조각을 안 흘려 Claude Code 의 바이트 유휴 워치독이 끊던 자리. **완성된 이벤트 사이에만 끼운다**(v24). `PGPT_PROXY_KEEPALIVE_SEC=0` 이면 끈다 | **쓴다 · 132회** (Claude Code · 옛 판 실측). ⚠ 180초 벽은 못 넘는다 — 유휴가 아니라 요청 실행 시계다(`../ENV-posco.md`) |
| **스트림 무결성**(v23 · v24) — SSE 는 늘 chunked 로 다시 싼다 · 끝 이벤트(`message_stop` · `response.completed`)를 확인하고, 없이 닫히면 끝 표시 없이 닫아 클라이언트가 잘린 응답으로 안다 · 오류 이벤트는 그대로 넘기고 센다 | **쓴다** — 옛 판에서 가짜 게이트웨이로 재현한 결함 둘을 막는다(2026-10-07): 이벤트 도중에 쉬면 주석이 이벤트 한가운데 끼어 그 이벤트가 깨지던 것 · 길이를 선언한 SSE 에 주석이 얹혀 끝 이벤트가 잘리던 것. 실제 게이트웨이에서 얼마나 잦은지는 모른다 |
| **출력 상한**(v26) — Claude 요청의 `max_tokens` 를 그 요청이 타는 길의 시한 안으로 **낮춘다**(안 올린다): 스트리밍 10,000(`PGPT_PROXY_STREAM_MAX_TOKENS`) · 비스트리밍 18,000(`PGPT_PROXY_NONSTREAM_MAX_TOKENS`) · `enabled` thinking 예산은 상한의 절반 이하로. `0` 이면 그 길은 클라이언트 값 | **쓴다** — 회사 실측(2026-10-30 · #226 ④ ⑦): 64,000 으로 와 10,000 으로 깎인 217건 가운데 상한에 닿은 턴이 0건이고, 같은 꼴을 프록시 없이 보낸 생각 턴은 앞단 300초 벽에 504 로 졌다(n=1) — 상한은 생각 예산도 함께 눌러 그 벽 앞에서 끝낸다. 긴 턴이 180초에 `HTTP 500` 으로 잘리면 Claude Code 가 같은 요청을 최대 10번 다시 보냈다. 상한에 닿으면 `stop_reason=max_tokens` 로 끝나 Claude Code 가 나눠서 이어 쓴다. 값은 상류 실측(Opus 턴 1.2초 + 토큰당 13.77ms · 197건 · 2026-10-06)에서 왔다. ⚠ 우리 아뜰리에의 8월 실측(초당 34~58토큰)으로 셈하면 10,000 이 170~290초라 벽을 넘을 수 있다 — `/health` 의 `execution_cuts` · `max_tokens_hits` 로 가린다. ⚠ 1만 토큰이 넘는 도구 호출 하나(큰 `Write`)는 못 끝난다 — 상한이 없어도 약 12,900 에서 벽이다 |
| **압축만 비스트리밍**(v25 · `PGPT_PROXY_COMPACT_UNSTREAM` · 기본 켬) — Claude Code 의 압축 요청을 알아보면(v26: 마지막 user 글이 `CRITICAL: Respond with TEXT ONLY` 로 시작하고 앞 4,000자 안에 요약 과제 문장) 상류엔 `"stream": false` 로 보내고 답을 다 받아 SSE 로 지어 낸다. 압축 안의 「Output token limit hit」 이어 쓰기도 같은 길(`kind=compact_continue`) | **쓴다 · 회사 실측 아직**(결정 0082) — 비스트리밍 경로에는 180초 상한이 없다(앞단 300초까지 산다 · 0051 실측). 압축은 도구를 안 부르니 그 경로의 도구 인자 유실과 무관하고, 압축 답에 도구 호출이 섞여 오면 내보내지 않고 오류로 돌린다. ⚠ **응답 머리가 올 때까지(최대 300초) 클라이언트로 바이트가 안 간다** — Claude Code 의 바이트 유휴 워치독이 그보다 길어야 하고, 자리 파일이 10분으로 심는다(0044 에서 사는 것) |
| 진단(v19 · v21 · v23 · v24 · v29) — 시한 근방의 절단을 `execution_cuts`(스트림 180초) · `execution_cuts_300`(비스트리밍 300초) 으로 · 오류 이벤트·잘린 스트림을 `stream_errors` · `stream_incomplete` 로 센다. 생성 요청마다 `request …`(모델 · effort · thinking · `max_tokens`) · `stream …`(첫 이벤트 · 첫 글자 시각 · 출력 토큰 · 종료 사유 · 사용량 — Codex 의 Responses 스트림은 `response.output_text.delta` 의 첫 조각과 `response.completed` 의 출력 토큰을 집는다 · #226 ⑤d) · `complete …`(머리 · 상류 · 전체 초) 줄과 게이트웨이 요청 번호(`gw=`)를 `proxy.log` 에 남긴다. **(우리 것)** 사용량은 Claude 응답의 `in=`(입력) · `cache_read=` · `cache_write=` 세 칸이다 — 스트림은 `stream …` 줄에, 그대로 중계한 비스트리밍(자동 모드 분류기 등)과 압축은 `complete …` 줄에 실린다 | **쓴다** — 위 상한과 압축 길이 맞나를 회사에서 재는 자다. 사용량 칸은 어느 턴이 캐시를 놓치나(`cache_write` 가 대화 크기만큼 튄다) · 곁 호출(`model=claude-sonnet-5` 등)이 캐시를 타나 · 1시간이 서나를 가리는 자다(결정 0175). 회사 실측(사외 VDI 2026-10-20 · #206) — 분류기 곁 호출은 매번 약 5만을 읽는다(`cache_write` 는 비스트리밍이라 `unknown`). 프롬프트·응답 글자·인증 헤더는 안 남긴다. 요청 번호는 게이트웨이 팀이 제 장부를 찾는 열쇠다(옛 판에서 우리가 얹던 것 · #67) |
| **기록 보존**(v29) — `proxy.log` 가 1 MB 를 넘으면 `proxy.log.1` 로 넘기고, 넘기기가 막히면 2 MB 에서 멈춘다 · 처리기에서 안 잡힌 예외를 `unhandled error …` 한 줄로, 클라이언트 끊김을 짧은 한 줄로 남긴다 · 숫자 아닌 · 음수 `Content-Length` 와 짧은 본문은 넘기지 않고 400 · `Transfer-Encoding` 이 붙은 요청은 본문을 안 읽고 411(`Length Required`)로 돌린다 — 이 문을 지나는 클라이언트 둘은 큰 본문도 `Content-Length` 로 올린다(Codex 64 KB · 회사 실측 2026-10-30 · #226 ⑨ · Claude Code 2.1.314 는 사외 실측) · `/health` 의 `max_request_bytes` | **쓴다** — 요청 바이트는 안 바뀐다. `pythonw` 아래에는 stderr 가 없어 안 잡힌 예외가 어디에도 안 남던 자리다. 180초 절단 줄을 몇 시간 뒤에 읽어도 남는다 |
| 입력 크기로 출력 상한 낮추기(v29 · `PGPT_PROXY_INPUT_READ_SEC_PER_MTOK` · 기본 `0`) | **논다** — 꺼져 있다. 값은 회사 `/health` 가 큰 `max_request_bytes` 곁에 `execution_cuts` 를 보인 뒤에 가른다. ⚠ 본문 바이트에는 base64 그림이 들어 그림 많은 대화를 길게 잰다 |
| 응답 머리를 기다리다 클라이언트가 끊으면 상류 연결도 닫는다(v21) · `/health` 의 `client_cancellations` | **쓴다** — 게이트웨이가 이미 시작한 생성까지 멈춘다는 보장은 없다 |
| `/v1beta` 그대로 넘기기 — 이 문으로 온 Gemini 요청은 경로 · 머리 · 본문을 안 고치고, 스트림은 바이트 그대로 옮긴다(keepalive 주석 · 끝 이벤트 확인 · chunked 로 다시 싸기를 안 한다). 모델 이름 · `-customtools` 접미사 · 쪼개진 SSE · 인증 머리를 고치는 칸은 없다 | **논다 · 걷을 것이 없다** — 경로를 가리지 않고 넘기는 문이라 따로 지닌 코드가 스트림 가르기 한 줄뿐이다. 우리 클라이언트 가운데 이 길을 타는 것이 없다 — 안티그래비티(`agy`)는 게이트웨이에 바로 붙는다(결정 0203). 주소를 아직 이 문에 둔 agy 도 본 턴은 선다 — 게이트웨이가 `x-goog-api-key` 를 받고(`../Gemini-Posco.setting.md` 인증 절), Gemini 스트림을 `data:` 줄 여럿으로 쪼개지 않는다(생각 서명 thoughtSignature 가 든 13,124 바이트 JSON 까지 한 줄로 · 회사 실측 2026-10-30 · #226 ⑱). 제목 짓기 곁 호출의 400 은 직결과 같다 |
| `x-api-key` 만 온 Anthropic 호환 요청에 같은 키를 `Authorization: Bearer` 로 덧붙이기 | **논다** — Claude Code 는 Bearer 로 보낸다 |
| 개인 `x-api-key` 헤더 누출 방지 — `Authorization` 이 이미 있으면 `x-api-key` 제거 (v16) | **쓴다** (Claude Code) — 사용자 환경에 개인 `ANTHROPIC_API_KEY` 가 있어도 평문 HTTP 로 사내 게이트웨이에 새지 않는다 |
| 짝 없는 surrogate(`\ud83d` 등) JSON 인코딩 보호 | **쓴다** — 이모지 반쪽에서 잘린 문자열이 와도 예외로 죽지 않고 `\uXXXX` 로 되돌린다 |
| 경로 순회(`..` 및 `.`) 차단 | **쓴다** — `/gpgpta01-gpt/../other` 처럼 허용 접두어를 빠져나가 게이트웨이의 다른 서비스로 가려는 경로는 403 으로 막고 연결을 닫는다(`Connection: close`) |
| 청크 전송(`Transfer-Encoding: chunked`)의 끝 표시 | **쓴다** — 상류 응답을 끝까지 받았을 때만 끝 표시(`0\r\n\r\n`)를 보낸다. 상류가 도중에 끊기면 끝 표시 없이 닫아서, 클라이언트가 잘린 응답(`IncompleteRead`)으로 알아채게 한다. SSE 는 끝 이벤트까지 와야 「끝까지 받았다」로 친다(위 무결성 칸) |
| 포트 잡기를 15초 동안 다시 시도 | **쓴다** — 재설치·키 교체로 프록시를 다시 띄울 때 옛 프록시의 연결이 아직 닫히는 중이면 포트 바인드가 잠깐 실패한다. 그 자리에서 죽으면 다음 로그인까지 프록시가 없으므로 15초 동안 다시 시도한다 |
| `PGPT_PROXY_PORT` 환경변수 | **쓴다** — 기본은 `18901`. 시험(`Test-ProxyFaults.py` · `pair_check.py`)은 이 값으로 다른 포트에 띄워, 떠 있는 프록시와 부딪히지 않는다 |
| `/health` 에 `pid` 포함 | **쓴다** — 설치기·검사기가 포트를 쥔 프로세스가 방금 제가 띄운 것인지 확인한다(한 PC 를 여럿이 쓰면 남의 프록시가 포트를 쥘 수 있다) |
| 응답 | **거의 그대로 중계한다** — 스트리밍 포함, 생각 낱말도 안 건드린다. 손대는 것은 위 칸들뿐이다: 침묵 동안 끼우는 keepalive 주석 · 비스트리밍 갈래의 SSE 짓기 · 웹서치 하위 요청과 Codex 검색의 답 짓기(위 웹서치 칸 둘). 180초 벽을 중계로는 못 넘는다(`../ENV-posco.md`) — 넘는 길은 비스트리밍 갈래뿐이고(압축은 기본으로 그 길이다), 그 길의 `/v1/messages` 응답은 중계가 아니라 프록시가 지은 것이다 |

**프록시가 하는 일이 아닌 것 하나** — `POST /v1/messages/count_tokens` 는 게이트웨이에 없어 **404** 다(실측
775회). 클라이언트가 스스로 어림셈으로 넘어가고 느린 요청(`slow`)도 0건이라 지연을 안 만든다 — 고칠 일이
아니라 알아 둘 일이다.

## 실행 규약

- 듣는 자리 `127.0.0.1:18901` (환경변수 `PGPT_PROXY_PORT` 로 바꿀 수 있다 · 포트를 받는 명령 인자는 없다) · 받는 경로는 `/gpgpta01-gpt/` 아래뿐
- 상류는 `PGPT_PROXY_UPSTREAM` (기본 `http://aigpt.posco.net`) — 사내 `HTTP_PROXY` 를 **안 탄다**(직결). 게이트웨이 말고는
  어디로도 나가지 않는다
- `proxy.log` · `proxy.log.1` 과 `opus5_proxy.pid` 를 **제 파일 곁에** 쓴다 — 그래서 설치기는 이 파일을 실행 폴더로 복사해 띄운다.
  저장소·홈 사본에서 바로 띄우면 그 곁에 남고, 저장소는 `.gitignore` 가 받는다
- `GET /health` — `status` · `service` · `version` · `pid` · 계수(`trimmed_prefills` · `hoisted_tool_images` · `documents_noted` · `hoist_cache_marks` · `hoist_cache_marks_skipped` · `web_search_filled` · `web_search_failed` ·
  `web_search_empty` · `model_substitutions` · `execution_cuts` · `execution_cuts_300` · `max_tokens_hits` 등) · 모델 목록(`model_list_size` ·
  `model_list_fetches` · `model_list_failures`)과 지금 걸린 손잡이(`compact_unstream` · `stream_max_tokens` · `hoist_tool_images` · `document_note` · `web_search` ·
  `model_list` 등)
- `--self-test` — 보정 함수를 스스로 검사하고 끝난다(프록시는 안 뜬다)

## 재는 법

```bash
python -X utf8 posco/pgpt-proxy/opus5_proxy.py --self-test     # 보정 함수 — 어디서나
python -X utf8 posco/pgpt-proxy/pair_check.py                 # 400 이 사라지나 — 어디서나 (가짜 게이트웨이)
python -X utf8 posco/pgpt-proxy/codex_websearch_check.py     # Codex 검색 메움 — alpha/search 요청 · SearchResponse — 어디서나
python -X utf8 posco/pgpt-proxy/Test-ProxyFaults.py          # 비정상 응답·스트림 단절 등 결함 내성 — 어디서나
python -X utf8 posco/pgpt-proxy/Test-ProxyStreaming.py       # 스트림 무결성 · 진단 줄 — 어디서나
python -X utf8 posco/pgpt-proxy/Test-ProxyCompaction.py      # 압축 알아보기 · 출력 상한 — 어디서나 (망 없음)
python -X utf8 posco/pgpt-proxy/Test-ProxyUnstream.py        # 비스트리밍 갈래 — 어디서나
python -X utf8 posco/pgpt-proxy/Test-ProxyImages.py          # 그림 끌어내기 · PDF 안내 글 — 본문 모양 · 계수 · 스위치 — 어디서나 (망 없음)
python -X utf8 posco/pgpt-proxy/Test-ProxyModelMap.py        # 모델 대체 — 목록 조회 · 실패 때 규칙 — 어디서나 (가짜 게이트웨이)
python -X utf8 posco/pgpt-proxy/Test-ProxyWebSearch.py       # Claude 웹서치 메움 — 알아보기 · 답 짓기 · 오류 갈래 — 어디서나
python -X utf8 posco/pgpt-proxy/Test-ProxyChunkedBody.py     # Transfer-Encoding 본문 411 — 어디서나
MOCK_SLOW_SEC=4 MOCK_ANSWER=tool_use python -X utf8 posco/pgpt-proxy/mock_gateway.py 18902
#   느린 비스트리밍 답 — 답 꼴은 text·tool_use·error500 · 상류가 받은 몸은 GET /gpgpta01-gpt/_mock/last
PGPT_API_KEY=<회사 키> python -X utf8 posco/pgpt-proxy/Test-AllPgptModels.py   # 회사 · 프록시가 떠 있어야

# 그림이 정말 보이나 — **회사** · 별 포트에 이 판을 띄워 두고 잰다 (#76 · 새 판을 들일 때의 회사 실측은 #193)
PGPT_PROXY_PORT=18907 python -X utf8 posco/pgpt-proxy/opus5_proxy.py &
python -X utf8 posco/pgpt-proxy/hoist_live_check.py 18907      # 보정 없는 판은 못 보고 이 판은 맞히나
python -X utf8 posco/pgpt-proxy/image_lane_probe.py claude-opus-5 gpt-5.2   # 어느 자리의 그림을 보나
python -X utf8 posco/pgpt-proxy/image_tail_probe.py claude-opus-5           # tool_result 가 마지막일 때
python -X utf8 posco/pgpt-proxy/cache_ttl_probe.py                         # 캐시 1시간이 서나 — 8분 남짓 걸린다 (결정 0174)
python -X utf8 posco/pgpt-proxy/cache_usage_report.py                      # 오늘 세션이 캐시를 읽었나 · 어디서 다시 썼나 (결정 0174 · 0175)

```

⚠ **눈가림 셋(`hoist_live_check.py` · `image_lane_probe.py` · `image_tail_probe.py`)은 정답을 화면에 안 찍는다** —
곁 파일에만 적는다(`%TEMP%\*-answer.txt`). 재는 사람도 정답을 먼저 보지 않는 것이 요점이다: 아는 값을
맞히는 것은 재는 것이 아니다. `hoist_live_check.py` 는 정답과의 대조까지 스스로 하고 판정 한 줄을 낸다.

⚠ **출력 상한과 압축 길은 회사에서만 갈린다** — 집에서 초록인 것은 중계 코드까지다. 회사에서는 이 판으로 긴 턴과
압축을 돈 뒤 `/health` 를 본다: `execution_cuts`(180초 근방 절단)가 늘면 스트리밍 상한이 벽 밖이다 ·
`max_tokens_hits` 가 늘었으면 그 세션이 이어 쓰기로 넘어갔나 본다 · `compact_unstream: true`.
`proxy.log` 의 `kind=compact … transport=unstream` 줄과 그 `complete …` 의 `upstream=` 초가 압축 한 번의 길이다.

전수 스모크는 키를 `PGPT_API_KEY` 나 홈 `.claude/settings.json` 의 `ANTHROPIC_AUTH_TOKEN` 에서 읽는다.

## 상류를 볼 때

상류는 **따라가지 않는다**(결정 0163) — 새 판을 통째로 받아 우리 덩어리를 다시 얹는 일은 이제 없다. 같은
게이트웨이를 쓰는 이웃이라, 상류 저장소의 변경 이력(docs 폴더의 CHANGELOG)에서 프록시 줄을 가끔 읽고 우리에게 없는 고침이 보이면
그 고침만 빌려 온다(스킬 `borrow-spec-as-pair`). 빌린 것은 우리 판의 뒤 칸을 올리고 위 쓰임 표에 「(상류 vNN 에서
빌림)」으로 적는다. ⚠ 빌릴 때 같은 이름의 함수 · 상수가 이미 있나 먼저 본다 — 파이썬은 뒤에 정의한 것이 조용히
이긴다. 커밋 게이트의 ruff(F811)가 그 덮어쓰기를 잡는다

**v35(`5da3136`)에서 빌린 것은 없다** — 안 빌린 것과 그 까닭:

- 재시도 고침 둘(쉬는 사이 닫힌 연결 버리기 · 재시도를 시간으로 가르기) — 우리 판은 연결을 다시 쓰지 않고 다시 보내지도 않는다(위 쓰임 표의
  상류 연결 칸 · 결정 0202)
- 깨진 chunked 본문 400 — 우리 클라이언트 셋이 chunked 로 안 올려(회사 실측 #226 ⑨) chunked 를 읽지 않는다. `Transfer-Encoding` 이 오면
  411 로 돌린다(기록 보존 칸)
- Gemini SSE 조각 잇기 — 게이트웨이가 지금 Gemini 스트림의 JSON 을 안 쪼개고(회사 실측 #226 ⑱), agy 는 이 문을 안 지나
  게이트웨이에 바로 붙는다(결정 0203). 다시 쪼개는 것이 보이면 결정 0203 의 커밋이 되살릴 원본이다
- Responses 가 출력 상한으로 끝난 `response.incomplete` 를 오류가 아니라 `max_tokens_hits` 로 세기 — Codex 는 그 상한 칸을 안 보내
  걸릴 길이 거의 없고, 클라이언트가 받는 바이트는 어느 쪽이든 같다. 우리 판에서는 `stream_errors` 로 센다(결정 0201)

- 날짜 붙은 Claude 이름(`claude-sonnet-4-5-20250929` → `claude-sonnet-4.5`) — 사용자가 고르지 않았다. 우리 클라이언트가 보내는 하이쿠 날짜 이름은 목록 길로 이미 맞게 간다(대조 2026-10-30). 사람이 날짜 붙은 판을 직접 칠 때만 걸린다
- Gemini 차단 · SAFETY 계열을 OpenAI 끝 사유 content_filter 로 — Gemini → OpenAI chat 다리에서만 걸리고, 우리 판에는 그 다리가 없다(아래 「안 담은 것」)
- `codex-auto-review` 를 GPT 기본 모델로 바꿔 보내기 — Paseo 전용이고 우리는 Paseo 를 안 쓴다. 사람이 안 고른 이름을 조용히 구해 주는 꼴이기도 하다(결정 0164)
- Claude Fast(`speed` · `fast-mode-*` 표식) · Codex Speed(`service_tier: "priority"`) 걷어 내기 — 사람이 누른 선택을 조용히 지우면 보이는 실패가 가짜 성공이 된다(결정 0164 의 생각). 회사에서 그 선택이 실제로 지는 것을 보면 그때 가른다

## 안 담은 것

상류의 설치기(`Install-*.ps1` · `START-*.bat` · `PGPT.*.ps1` · `Update-Proxy.ps1` · `Reset-ClaudeCompaction.ps1`)와
Hermes·Paseo·Grok 갈래, 문서. 우리 설치는 PAISetup `install.ps1` 이 들고, 이 폴더는 그 설치가 복사해 가는 **재료**다.
프록시 코드에도 우리 클라이언트(Claude Code · Codex)가 안 타는 상류 v33 의 갈래는 없다 — chat 문(`/v1/chat/completions`)의
`gemini-*` 요청을 Gemini 네이티브로 옮기는 다리 · Grok 4 가 거부하는 필드 떼기 · GPT-5 · o 계열의 `max_tokens` 이름 바꾸기 ·
큰 요청 줄 세우기 · 압축 지시 끝의 간결 지시 · 압축이 아닌 턴까지 비스트리밍으로 보내는 스위치 · 웹서치 출처 주소 풀기.
⚠ **상류 설치기의 압축 설정은 안 받는다** — 1M 문맥 끄기(`CLAUDE_CODE_DISABLE_1M_CONTEXT`) · 창 200K
(`CLAUDE_CODE_AUTO_COMPACT_WINDOW`) · 압축 비율(`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` 45·60). 창을 200K 로 묶고 압축을
당겨 압축이 되풀이되던 것을 상류가 그 판들에서 수습했는데, 우리는 창을 1M 으로 열어(결정 0049) 그 원인이 없다(결정 0082)
