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

- 저장소 `pgpt-one-click-connect` · 커밋 `319529d8` (2026-08-26) · 프록시 `VERSION = 14`
- **우리 판은 `VERSION = 15` = 상류 14 + keepalive 한 덩어리** (결정 0044). 설치기가 도는 판과 이 값을 견주어
  낮으면 갈아 끼우므로 상류보다 하나 위에 둔다 — 상류가 15 를 내면 우리는 16 이다
- 작성자 허락 2026-09-14 (라이선스 파일은 상류에 없다 — 허락으로 든다)
- **파일은 안 고친다 — 예외가 하나다.** `_relay_sse_keepalive`(+ `KEEPALIVE_SEC` · 카운터 `keepalives` · 자체
  검사 한 칸)만 우리 것이고, 나머지는 상류 그대로다. 상류가 CRLF 인 것만 이 저장소 규칙(`.gitattributes`)이 LF 로 눕힌다. 커밋 게이트의
  파이썬 판정이 무는 두 줄(`raise` 에 `from` 없음 · 안 쓰는 import)은 뿌리 `ruff.toml` 이 이 세 파일을
  제외해 받는다 — 판정은 전역, 제외는 저장소(결정 0039)

## 무엇을 쓰고 무엇이 노나

| 프록시가 하는 일 | 우리 |
|---|---|
| `/v1/messages` — 끝의 assistant 마디 제거 · `system` 역할 마디를 `user` 로 · 같은 역할 병합 · `temperature`/`top_p` 제거 | **쓴다** (Claude Code) |
| `/v1beta` — `x-goog-api-key` 곁에 Bearer 추가 · `-customtools` 접미사 제거 · 쪼개진 SSE 재조립 | **쓴다** (Gemini CLI) |
| `claude-sonnet-5` → `claude-sonnet-4.6` (게이트웨이 미등록 별칭) | 지난다 — 우리는 `ANTHROPIC_MODEL` 로 4.6 을 못박아 걸릴 일이 없다 |
| GPT-5 계열 `max_tokens` → `max_completion_tokens` · 빈 도구 `description` 채우기 | **논다** — Codex 는 직결이다 |
| **(우리 것)** Anthropic SSE 가 침묵하면 `KEEPALIVE_SEC`(기본 15초)마다 `: keepalive` 주석 한 줄을 클라이언트에 흘린다 — 게이트웨이가 생각 조각을 안 흘려 Claude Code 의 바이트 유휴 워치독이 끊던 자리. `PGPT_PROXY_KEEPALIVE_SEC=0` 이면 끈다 | **쓴다** (Claude Code · 결정 0044 · 회사 실측 전) |
| Hermes 갈래 — 대시 모델 ID 복원 · chat 문의 Gemini 변환 · `x-api-key` → Bearer | **논다** — Hermes 를 안 쓴다. 걷어 내지 않는 까닭은 위 「파일은 안 고친다」 |
| 응답 | **무수정 중계** — 스트리밍 포함. 심장박동도 생각 낱말도 안 건드린다. 180초 벽은 이것으로 안 넘는다(`ENV-posco.md`) |

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
