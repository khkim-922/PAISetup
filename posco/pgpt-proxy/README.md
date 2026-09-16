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

- 저장소 `pgpt-one-click-connect` · 커밋 `701765da` (2026-09-15 · v0.5.3) · 프록시 `VERSION = 15`
- **우리 판은 `VERSION = 16` = 상류 15 + keepalive 한 덩어리** (결정 0044). 설치기가 도는 판과 이 값을 견주어
  낮으면 갈아 끼우므로 상류보다 하나 위에 둔다 — 상류가 16 을 내면 우리는 17 이다
- 작성자 허락 2026-09-14 (라이선스 파일은 상류에 없다 — 허락으로 든다)
- **파일은 안 고친다 — 예외가 하나다.** `_relay_sse_keepalive`(+ `KEEPALIVE_SEC` · 카운터 `keepalives` · 자체
  검사 한 칸)만 우리 것이고, 나머지는 상류 그대로다. 상류가 CRLF 인 것만 이 저장소 규칙(`.gitattributes`)이 LF 로 눕힌다. 커밋 게이트의
  파이썬 판정이 무는 두 줄(`raise` 에 `from` 없음 · 안 쓰는 import)은 뿌리 `ruff.toml` 이 이 세 파일을
  제외해 받는다 — 판정은 전역, 제외는 저장소(결정 0039)

## 무엇을 쓰고 무엇이 노나

칸마다 회사 로그 실측이 든다 — 25시간 3039줄(2026-09-15 08:04 ~ 09-16 09:03) + Gemini·Codex 탐침 한 판씩.
**「논다」는 안 걸린다는 판정이지 걷어 낸다는 뜻이 아니다** — 걷어 내지 않는 까닭은 위 「파일은 안 고친다」.

| 프록시가 하는 일 | 우리 |
|---|---|
| `/v1/messages` — 끝의 assistant 마디 제거 · `system` 역할 마디를 `user` 로 · 같은 역할 병합 · `temperature`/`top_p` 제거 | **쓴다** (Claude Code) — `trimmed_prefills` 가 센다 |
| `claude-sonnet-5` → `claude-sonnet-4.6` (게이트웨이 미등록 별칭) | **쓴다 · 758회** — `ANTHROPIC_MODEL` 은 메인 세션의 모델 하나만 못박고, Claude Code 가 스스로 부르는 곁 호출(서브에이전트·요약·모델 피커의 다른 칩)은 그 못을 안 타고 제 이름을 보낸다 |
| 대시 모델 ID 복원 — `claude-opus-4-7` → `claude-opus-4.7` | **쓴다 · 6회** — 같은 곁 호출 길. 별칭과 한 함수(`normalize_claude_model_id`)라 바뀌면 로그 한 줄이 찍힌다 |
| 빈 도구 `description` 채우기 | **쓴다 · 6회** (Claude Code) · Codex 를 루프백에 태우면 `/v1/responses` 에서도 걸린다(탐침 `tool_descriptions_filled=1`) |
| 상류 연결 풀 — 30초(`UPSTREAM_IDLE_TTL`) 넘게 논 연결은 재사용하지 않고 닫는다 · `/health` 의 `upstream_expired` | **쓴다** — 게이트웨이가 keep-alive 를 끊은 뒤 남은 연결을 집어 첫 요청이 지던 자리. 실측 `upstream_expired=8` · 재사용 82 |
| **(우리 것)** Anthropic SSE 가 침묵하면 `KEEPALIVE_SEC`(기본 15초)마다 `: keepalive` 주석 한 줄을 클라이언트에 흘린다 — 게이트웨이가 생각 조각을 안 흘려 Claude Code 의 바이트 유휴 워치독이 끊던 자리. `PGPT_PROXY_KEEPALIVE_SEC=0` 이면 끈다 | **쓴다 · 132회** (Claude Code · 결정 0044) |
| `/v1beta` 통과 — Gemini CLI 가 루프백을 지난다 | **쓴다** — 프록시의 값은 보정이 아니라 **주소**다(CLI 가 `https` 아니면 거부하는데 `127.0.0.1` 만 `http` 를 허용한다 · 0041) |
| `/v1beta` — `-customtools` 접미사 제거 | **논다** — CLI 0.60 은 도구를 켜도 접미사를 안 붙인다(코드 주석은 0.55 기준) |
| `/v1beta` — 쪼개진 SSE 재조립 | **안 걸렸다** — 탐침 한 판이라 「논다」로 굳히지 않는다. 게이트웨이 버릇이라 Gemini 를 실제로 쓰기 시작하면 다시 잰다 |
| `/v1beta` — `x-goog-api-key` 곁에 Bearer 추가 | **값이 없다** — 게이트웨이가 두 방식을 다 받는다(`Gemini-Posco.setting.md` 인증 절) · 원래 헤더만으로 200(직결 실측) |
| GPT-5·GPT-6 계열 `max_tokens` → `max_completion_tokens`(`/v1/responses` 는 `max_output_tokens`) | **논다** — Codex 가 이미 `max_output_tokens` 로 보낸다. 직결도 루프백도 0 |
| Hermes 갈래 — chat 문의 Gemini 변환 · `x-api-key` → Bearer | **논다** — Hermes 를 안 쓴다. Claude Code 는 Bearer 로 보낸다 |
| 응답 | **무수정 중계** — 스트리밍 포함. 심장박동도 생각 낱말도 안 건드린다. 180초 벽은 이것으로 안 넘는다(`ENV-posco.md`) |

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
PGPT_API_KEY=<회사 키> python -X utf8 posco/pgpt-proxy/Test-AllPgptModels.py   # 회사 · 프록시가 떠 있어야
```

전수 스모크는 키를 `PGPT_API_KEY` 나 홈 `.claude/settings.json` 의 `ANTHROPIC_AUTH_TOKEN` 에서 읽는다.

## 상류에서 새 판을 받을 때

1. 상류의 세 파일을 그대로 복사한다 — `diff --strip-trailing-cr` 로 대조하면 줄끝 잡음이 안 낀다.
   ⚠ `opus5_proxy.py` 는 복사한 뒤 **keepalive 덩어리를 다시 얹는다** — `git diff` 로 이번 판과 견주면 그 덩어리가
   그대로 보인다(`KEEPALIVE_SEC` · `_count_keepalive` · `_relay_sse_keepalive` · `_relay_stream` 의 두 인자 ·
   호출 자리의 `keepalive_sse` · 자체 검사 끝 칸)
2. 위 「상류 판」의 커밋·`VERSION` 을 고친다 — 우리 `VERSION` 은 상류보다 하나 위
3. `pair_check.py` 와 `--self-test` 가 초록인지 본다. 프록시가 새 보정을 얹었으면 위 표에 「쓴다/논다」를 더한다

## 안 담은 것

상류의 설치기(`Install-*.ps1` · `START-*.bat` · `PGPT.*.ps1`)와 Hermes·Paseo·Grok 갈래, 문서. 우리 설치는
PAISetup `install.ps1` 이 들고, 이 폴더는 그 설치가 복사해 가는 **재료**다.
