# pgpt-proxy — 사내 게이트웨이 앞의 로컬 프록시 (동료 코드 사본)

사내 동료(GitHub `sejuone-cloud`)의 비공개 저장소 `pgpt-one-click-connect` 에서 **통째로** 가져온 사본이다.
`127.0.0.1:18901` 에 서서 클라이언트가 보내는 본문을 사내 게이트웨이(P-GPT)가 받는 꼴로 고쳐 넘긴다.
왜 싣나는 결정 기록 0041 이 든다 — Claude Code 의 Opus 5 (assistant prefill 400)와 Gemini CLI (http 주소
거부 · 번들 패치 대체)가 이 프록시를 지나고, Codex 는 직결이라 안 지난다.

| 파일 | 상류 자리 | 무엇 |
|---|---|---|
| `opus5_proxy.py` | `app/opus5_proxy.py` | 프록시 본체. 표준 라이브러리만 쓴다 |
| `mock_gateway.py` | `tests/mock_gateway.py` | 가짜 게이트웨이 — 실제처럼 prefill 에 400 을 낸다. 사내망 밖에서 프록시를 끝까지 돌려 볼 때 |
| `Test-AllPgptModels.py` | `tests/Test-AllPgptModels.py` | 모델 전수 스모크 — 프록시 너머로 모델마다 「Reply OK」 한 줄. 결과는 곁 `model-results/` |
| `pair_check.py` | (우리 것) | 위 둘로 「직결 400 · 프록시 200 · prefill 1번 뗐다」를 잰다 |

## 상류 판

- 저장소 [`pgpt-one-click-connect`](https://github.com/sejuone-cloud/pgpt-one-click-connect) · 커밋 `701765da`
  (2026-09-15 · v0.5.3) · 프록시 `VERSION = 15`
- **우리 판은 `15.5` — 두 칸이다**(`VERSION_UPSTREAM` · `VERSION_OURS`). 앞 칸이 받아온 상류 판이고 뒤 칸이
  우리가 얹은 덩어리 수다. **한 칸으로 세지 않는 까닭**: 상류와 우리가 같은 축에 번호를 매기면 상류가 16 을
  내는 날 우리 18 과 부딪히고, 그때 번호로는 누가 새것인지 못 가른다. 축을 가르면 **상류가 16 을 내면 우리
  칸은 0 으로 돌아가 `16.0`** 이 되고 그것이 `15.5` 보다 뒤라는 것이 그냥 나온다
  ⚠ **`/health` 는 사람이 읽는 `15.5` 를 내고, 견주는 자는 두 수를 각각 정수로 읽는다** — 점 찍힌 문자열을
  크기로 견주면 `"9" > "10"` 이 되는 자리다. 설치기가 그렇게 견주어 낮으면 갈아 끼운다(`install.ps1` 프록시 칸)
  ⚠ **옛 정수 한 칸(`17`·`18`)이 도는 자리도 받는다** — 그 판은 새 이름이 없어 「못 읽었다」로 떨어지고,
  그때는 **갈아 끼우는 쪽으로 기운다.** 반대로 두면 옛 프록시가 영영 안 바뀐다
- 작성자 허락 2026-09-14 (라이선스 파일은 상류에 없다 — 허락으로 든다)
- **파일은 안 고친다 — 예외가 넷이다.** ⑴ keepalive(`KEEPALIVE_SEC` · `_relay_sse_keepalive` · 카운터
  `keepalives` · 자체 검사 한 칸 · 결정 0044) ⑵ unstream(`UNSTREAM` 손잡이 · `synthesize_anthropic_sse` 무리 ·
  `_unstream_messages` · 카운터 `unstreamed` · 자체 검사 세 칸 · 진단 두 줄 · 결정 0051) ⑶ 하이쿠 대체
  (`_CLAUDE_HAIKU_SUBSTITUTE` · `normalize_pgpt_claude_model` 의 `haiku` 갈래 · 위 표) — 게이트웨이에 하이쿠가
  없어 서브에이전트가 지던 자리다 ⑷ 제미나이 이름 표(`_GEMINI_MODEL_ALIASES` ·
  `normalize_gemini_model_path` 의 그 조회 · 자체 검사 세 칸) — 안티그래비티가 제목 짓기에 못박아 둔 이름이
  게이트웨이에 없어 그 곁 호출만 지던 자리다 ⑸ 게이트웨이 요청 번호 로그(`_GW_REQUEST_ID_HEADER` ·
  `_write_upstream` 이 잡는 한 줄 · 꼬리를 짓는 `_gw` · 판마다 한 줄 넷) — 게이트웨이가 응답 머리에 주는
  번호를 셋 다 버려서 벽에 걸린 판을 「이 요청」으로 못 대던 자리다(#67). **판 번호 두 칸도 우리 것이다**(위). 그 둘째를 사내망 밖에서 재느라
  `mock_gateway.py` 에도 느린 비스트리밍 답 한 칸이 붙었다(`MOCK_SLOW_SEC` · `MOCK_ANSWER` · `_mock/last`).
  나머지는 상류 그대로다. 상류가 CRLF 인 것만 이 저장소 규칙(`.gitattributes`)이 LF 로 눕힌다. 커밋 게이트의
  파이썬 판정이 무는 두 줄(`raise` 에 `from` 없음 · 안 쓰는 import)은 뿌리 `ruff.toml` 이 이 세 파일을
  제외해 받는다 — 판정은 전역, 제외는 저장소(결정 0039)

## 무엇을 쓰고 무엇이 노나

칸마다 회사 로그 실측이 든다 — 25시간 3039줄(2026-09-15 08:04 ~ 09-16 09:03) + Gemini·Codex 탐침 한 판씩.
**「논다」는 안 걸린다는 판정이지 걷어 낸다는 뜻이 아니다** — 걷어 내지 않는 까닭은 위 「파일은 안 고친다」.

| 프록시가 하는 일 | 우리 |
|---|---|
| `/v1/messages` — 끝의 assistant 마디 제거 · `system` 역할 마디를 `user` 로 · 같은 역할 병합 · `temperature`/`top_p` 제거 | **쓴다** (Claude Code) — `trimmed_prefills` 가 센다 |
| `claude-sonnet-5` → `claude-sonnet-4.6` (게이트웨이 미등록 별칭) | **쓴다 · 758회** — `ANTHROPIC_MODEL` 은 메인 세션의 모델 하나만 못박고, Claude Code 가 스스로 부르는 곁 호출(서브에이전트·요약·모델 피커의 다른 칩)은 그 못을 안 타고 제 이름을 보낸다 |
| **(우리 것)** 이름에 `haiku` 가 들면 `claude-sonnet-4.6` 으로 (`_CLAUDE_HAIKU_SUBSTITUTE`) | **쓴다** — 하이쿠는 이 게이트웨이에 **한 판도 없다**(`GET /v1/models` 실측 2026-09-17 · Claude 는 opus 4.5·4.6·4.7·5 와 sonnet 4.5·4.6 여섯뿐). 그래서 서브에이전트 호출이 통째로 `400`(「모델을 찾을 수 없습니다」)으로 지던 자리다. **이름을 목록으로 안 잡고 규칙으로 잡는다** — 클라이언트가 아는 하이쿠 이름이 열둘이라 판이 오를 때마다 샌다. 실측: `claude-haiku-4-5` · 날짜박은 판 둘 다 `200` 에 `model: claude-sonnet-4.6` · 로그에 `restored` 한 줄. ⚠ **게이트웨이가 하이쿠를 들이면 이 칸을 지운다** — 그때는 이 규칙이 진짜 하이쿠까지 갈아버린다 |
| 대시 모델 ID 복원 — `claude-opus-4-7` → `claude-opus-4.7` | **쓴다 · 6회** — 같은 곁 호출 길. 별칭과 한 함수(`normalize_claude_model_id`)라 바뀌면 로그 한 줄이 찍힌다 |
| 빈 도구 `description` 채우기 | **쓴다 · 6회** (Claude Code) · Codex 를 루프백에 태우면 `/v1/responses` 에서도 걸린다(탐침 `tool_descriptions_filled=1`) |
| 상류 연결 풀 — 30초(`UPSTREAM_IDLE_TTL`) 넘게 논 연결은 재사용하지 않고 닫는다 · `/health` 의 `upstream_expired` | **쓴다** — 게이트웨이가 keep-alive 를 끊은 뒤 남은 연결을 집어 첫 요청이 지던 자리. 실측 `upstream_expired=8` · 재사용 82 |
| **(우리 것)** Anthropic SSE 가 침묵하면 `KEEPALIVE_SEC`(기본 15초)마다 `: keepalive` 주석 한 줄을 클라이언트에 흘린다 — 게이트웨이가 생각 조각을 안 흘려 Claude Code 의 바이트 유휴 워치독이 끊던 자리. `PGPT_PROXY_KEEPALIVE_SEC=0` 이면 끈다 | **쓴다 · 132회** (Claude Code · 결정 0044) |
| **(우리 것)** `/v1/messages` 에 `"stream": true` 가 오면 상류엔 **`"stream": false`** 로 보내고, 기다리는 동안 위 주석을 흘리다, 답이 오면 SSE 를 지어 낸다(`message_start` → 블록마다 `content_block_*` → `message_delta` → `message_stop` · 도구 호출은 `input_json_delta` 하나에 `input` 통째). 몸은 그 한 칸 말고 안 바뀐다 — `cache_control` 도 키 차례도 그대로다. **기본은 끔** · `PGPT_PROXY_UNSTREAM=1` 이면 켠다 | ⚠ **도구를 쓰는 클라이언트에는 켜지 않는다 — 큰 도구 인자가 빈다** (결정 0051). 회사 실측 2026-09-17: 벽은 넘는다(직결 `stream:true` 는 180.06초에 게이트웨이가 `180000 millis` 를 실토하며 끊고, 이 길은 300.01초까지 살아 앞단 `504` 를 SSE `error` 로 옮겼다). **그런데 켠 판에서 `Edit` 호출이 `input={}` 로 온다** — 출력 78/64000 토큰이라 한도와 무관하고 `stop_reason` 은 정상 `tool_use` 이며, 같은 판의 작은 `Bash`(163B)는 멀쩡하다. 끄면 같은 편집이 통한다(재현 3회). **우리 짓는 코드는 무죄다** — 6,642자 도구 입력이 SSE 왕복해 글자 대 글자로 살아남는다(왕복 검증). 까닭은 게이트웨이 안이라 밖에서 못 본다. 도구를 안 쓰는 쪽(아뜰리에)은 켜서 180초 벽을 비껴갈 수 있다 |
| `/v1beta` 통과 — Gemini CLI 가 루프백을 지난다 | **쓴다** — 프록시의 값은 보정이 아니라 **주소**다(CLI 가 `https` 아니면 거부하는데 `127.0.0.1` 만 `http` 를 허용한다 · 0041) |
| `/v1beta` — `-customtools` 접미사 제거 | **논다** — CLI 0.60 은 도구를 켜도 접미사를 안 붙인다(코드 주석은 0.55 기준) |
| **(우리 것)** `/v1beta` — `gemini-3.1-flash-lite-preview` → `gemini-3.1-flash-lite`(`_GEMINI_MODEL_ALIASES`) | **쓴다** — 안티그래비티(`agy`)가 **대화 제목 짓기에 이 이름을 못박아 둬서** 그 곁 호출만 `400` 으로 지던 자리다. 하이쿠 칸과 같은 병인데(`--model` 은 메인 턴만 못박고 곁 호출은 그 못을 안 탄다) **약이 다르다 — 같은 모델이 이름만 다르게 등록돼 있어 접미사만 고친다**(실측 2026-09-17 직결: `gemini-3.1-flash-lite` 는 `200` 에 `modelVersion` 도 그것 · `-preview` 는 `400`). ⚠ **이름으로 잡고 규칙으로 안 잡는다** — `-preview` 를 무조건 떼면 **게이트웨이에 실제로 있는** `gemini-3.1-pro-preview` 를 깨뜨린다(본 턴이 그 이름으로 통한다). 곁 호출이 새는 값은 제목이 안 붙는 것이고, 본 턴을 깨뜨리는 값은 아무것도 안 되는 것이다. ⚠ `agy` 쪽에 이 이름을 갈 손잡이가 없다 — 바이너리 상수다 |
| `/v1beta` — 쪼개진 SSE 재조립 | **안 걸렸다** — 탐침 한 판이라 「논다」로 굳히지 않는다. 게이트웨이 버릇이라 Gemini 를 실제로 쓰기 시작하면 다시 잰다 |
| `/v1beta` — `x-goog-api-key` 곁에 Bearer 추가 | **값이 없다** — 게이트웨이가 두 방식을 다 받는다(`Gemini-Posco.setting.md` 인증 절) · 원래 헤더만으로 200(직결 실측) |
| GPT-5·GPT-6 계열 `max_tokens` → `max_completion_tokens`(`/v1/responses` 는 `max_output_tokens`) | **논다** — Codex 가 이미 `max_output_tokens` 로 보낸다. 직결도 루프백도 0 |
| Hermes 갈래 — chat 문의 Gemini 변환 · `x-api-key` → Bearer | **논다** — Hermes 를 안 쓴다. Claude Code 는 Bearer 로 보낸다 |
| 응답 | **무수정 중계** — 스트리밍 포함. 심장박동도 생각 낱말도 안 건드린다. 180초 벽을 중계로는 못 넘는다(`ENV-posco.md`) — 넘는 것은 위 unstream 갈래고, 그 길의 `/v1/messages` 만 중계가 아니라 짓기다 |

**프록시가 하는 일이 아닌 것 하나** — `POST /v1/messages/count_tokens` 는 게이트웨이에 없어 **404** 다(실측
775회). 클라이언트가 제 계산으로 넘어가고 `slow` 는 0건이라 지연을 안 만든다 — 고칠 자리가 아니라 알아둘
자리다.

## 실행 규약

- 듣는 자리 `127.0.0.1:18901` (파일에 못박혀 있다 · 인자 없음) · 허용 경로 `/gpgpta01-gpt/` 아래만
- 상류는 `PGPT_PROXY_UPSTREAM` (기본 `http://aigpt.posco.net`) — 사내 `HTTP_PROXY` 를 **안 탄다**(직결)
- `proxy.log` 와 `opus5_proxy.pid` 를 **제 파일 곁에** 쓴다 — 그래서 설치기는 이 파일을 실행 폴더로 복사해 띄운다.
  저장소·홈 사본에서 바로 띄우면 그 곁에 남고, 저장소는 `.gitignore` 가 받는다
- `GET /health` — `status` · `version` · 계수(`trimmed_prefills` 등) · `--self-test` — 보정 함수 자체 검사

## 재는 법

```bash
python -X utf8 posco/pgpt-proxy/opus5_proxy.py --self-test     # 보정 함수 — 어디서나
python -X utf8 posco/pgpt-proxy/pair_check.py                 # 400 이 사라지나 — 어디서나 (가짜 게이트웨이)
MOCK_SLOW_SEC=4 MOCK_ANSWER=tool_use python -X utf8 posco/pgpt-proxy/mock_gateway.py 18902
#   느린 비스트리밍 답 — 답 꼴은 text·tool_use·error500 · 상류가 받은 몸은 GET /gpgpta01-gpt/_mock/last (0051)
PGPT_API_KEY=<회사 키> python -X utf8 posco/pgpt-proxy/Test-AllPgptModels.py   # 회사 · 프록시가 떠 있어야
```

전수 스모크는 키를 `PGPT_API_KEY` 나 홈 `.claude/settings.json` 의 `ANTHROPIC_AUTH_TOKEN` 에서 읽는다.

## 상류에서 새 판을 받을 때

1. 상류의 세 파일을 그대로 복사한다 — `diff --strip-trailing-cr` 로 대조하면 줄끝 잡음이 안 낀다.
   ⚠ `opus5_proxy.py` 는 복사한 뒤 **우리 덩어리 다섯을 다시 얹는다** — `git diff` 로 이번 판과 견주면 둘 다
   그대로 보인다.
   - keepalive(0044) — `KEEPALIVE_SEC` · `_count_keepalive` · `_relay_sse_keepalive` · `_relay_stream` 의 두 인자 ·
     호출 자리의 `keepalive_sse` · 자체 검사 한 칸
   - unstream(0051) — `UNSTREAM` · `_count_unstreamed` · `stats()` 의 `unstreamed` · `_sse_event` ·
     `_content_block_events` · `synthesize_anthropic_sse` · `anthropic_sse_error` · `_write_client` ·
     `_begin_synthesized_sse` · `_unstream_messages` · `_forward` 의 `unstream` 두 자리 · 자체 검사 세 칸
   - 하이쿠 대체 — `_CLAUDE_HAIKU_SUBSTITUTE` · `normalize_pgpt_claude_model` 의 `haiku` 갈래
   - 제미나이 이름 표 — `_GEMINI_MODEL_ALIASES` · `normalize_gemini_model_path` 의 그 조회
     (상류 함수가 `-customtools` 만 떼므로 **그 함수 안에 한 줄이 든다**) · 자체 검사 세 칸
   ⚠ `mock_gateway.py` 에도 얹을 것이 있다 — `SLOW_SEC`/`ANSWER`/`LAST` · `_body` 의 `raw_body` ·
   `_mock/last` 창구 · `/v1/messages` 의 답 세 꼴(0051)
2. 위 「상류 판」의 커밋을 고치고 **판 번호 두 칸을 옮긴다** — `VERSION_UPSTREAM` 을 받아온 판으로 올리고
   `VERSION_OURS` 를 **0 으로 되돌린다.** 그다음 우리 덩어리를 다시 얹은 만큼만 뒤 칸을 올린다.
   ⚠ **뒤 칸을 안 되돌리면 번호가 뜻을 잃는다** — 그 수는 「이 상류 판 위에 우리가 몇 번 얹었나」다
3. `pair_check.py` 와 `--self-test` 가 초록인지 본다. 프록시가 새 보정을 얹었으면 위 표에 「쓴다/논다」를 더한다

## 안 담은 것

상류의 설치기(`Install-*.ps1` · `START-*.bat` · `PGPT.*.ps1`)와 Hermes·Paseo·Grok 갈래, 문서. 우리 설치는
PAISetup `install.ps1` 이 들고, 이 폴더는 그 설치가 복사해 가는 **재료**다.
