# 사내 환경 (POSCO) — 기록·관리용

> 전역 규범은 `.claude/CLAUDE.global.md` 가 든다. 이 문서는 세션마다 읽히는 규범이 아니라, 사내 환경 정보가 필요할 때
> 열어 보는 기록이다. 파일은 `posco/` 폴더째 홈(`~/.claude/posco/`)과 설치본(PAISetup)에 함께 깔린다.

**사용자**: 초심자. 한 번에 한 명령씩, 성공 확인 후 다음 단계. 한국어로 설명.

**LLM API**: Anthropic API 직접 호출 불가 → 사내 게이트웨이 P-GPT 사용

> **명세는 여기 안 적는다** — 사내 문서를 그대로 옮겨 둔 이 폴더의 `*.setting.md` 가 원본이다:
> [`Claude-Posco.setting.md`](Claude-Posco.setting.md) (Messages API · Claude Code 연동) ·
> [`OpenAI.-Posco.Setting.md`](OpenAI.-Posco.Setting.md) (chat/completions · responses · Codex CLI 연동) ·
> [`Gemini-Posco.setting.md`](Gemini-Posco.setting.md) (Gemini 네이티브 API · Gemini CLI 연동) ·
> [`errors-Posco.setting.md`](errors-Posco.setting.md) (오류 코드 카탈로그) ·
> [`LangGraph-Posco.setting.md`](LangGraph-Posco.setting.md) (LangGraph 연결 가이드).
> 주소·헤더·파라미터·오류 코드·모델 목록은 전부 그쪽이 든다. **베껴 적으면 어긋난다.**
>
> ⚠ **다만 그 문서가 곧 사실은 아니다.** 아래 절이 그 차이를 든다.
>
> ⚠ **게이트웨이 앞에 한 겹이 더 있다.** 우리가 받는 504 중에는 P-GPT 가 낸 것이 아닌
> 것이 있다 — [`gateway-front-haproxy.md`](gateway-front-haproxy.md) 가 그 층을 든다.
> **사내 문서 어느 장도 그 층은 안 든다.**

- 백엔드는 **AWS Bedrock**이다 (문서가 밝힌다) — Anthropic 고유 기능 중 Bedrock 이 가진
  것만 건너간다고 보면 관측이 대체로 맞아떨어진다
- 우리가 쓰는 인증 — 사내 PC 에서는 앱(Anthropic SDK · atelier)도 Claude Code CLI 도 `ANTHROPIC_AUTH_TOKEN` 을
  읽어 `Authorization: Bearer` 로 보낸다(자리 파일 `secrets.d/posco.env`). 회사 문서는 `ANTHROPIC_API_KEY` →
  `x-api-key` 길도 적는다(`Claude-Posco.setting.md` 헤더 표). **게이트웨이는 둘 다 받는다** — 클라이언트마다
  읽는 이름이 다를 뿐이라, 하나를 「이게 아니다」로 못 박으면 다른 클라이언트를 못 붙인다.
  ⚠ 둘이 함께 실리면 프록시가 `x-api-key` 를 뗀다 — 개인 키가 평문 HTTP 로 사내에 새지 않게(`pgpt-proxy/README.md`)
- 우리가 쓰는 모델 — **`claude-opus-5` 가 기본이고 `opus` 별칭도 그것이다**(Claude Code · atelier · 결정 0046).
  Claude Code 에는 1M 창으로 열리게 접미사를 붙여 `claude-opus-5[1m]` 으로 심는다(`ANTHROPIC_MODEL` ·
  `ANTHROPIC_DEFAULT_OPUS_MODEL` · 결정 0049). `/model` 에서 고를 목록(4.7 · Sonnet 4.6 포함)은 설치기가
  사내에서만 홈 설정의 `modelPicker` 로 쓴다(결정 0048) — 옛 Custom 칸(`ANTHROPIC_CUSTOM_MODEL_OPTION`)은 걷었다.
  ⚠ **`claude-opus-5` 는 사내 문서 「지원 모델」 표에 없지만 실제로 돈다**
  (사용자 확인 2026-08-20) — **문서가 뒤처진 것이다.** 목록을 의심할 일이 있으면
  문서가 아니라 `GET /v1/models` 에 묻는다
  ⚠ **하이쿠는 한 판도 없다** — `GET /v1/models` 실측 2026-09-17: Claude 는 `opus-4.5`·`4.6`·`4.7`·`5` 와
  `sonnet-4.5`·`4.6` 여섯뿐이다(전체 37개). 그런데 Claude Code 는 곁 호출(서브에이전트·요약)에 하이쿠를
  제 이름으로 보내 그 호출이 `400`(「모델을 찾을 수 없습니다」)으로 진다 — **프록시가 이름에 `haiku` 가
  들면 `claude-sonnet-4.6` 으로 갈아 보낸다**(`pgpt-proxy/README.md` 의 예외 ⑶). 대가는 하이쿠 자리에
  소넷이 와서 토큰이 더 나가는 것이고, 지금은 아예 실패하니 후퇴는 아니다

## 우리가 잰 것 — 문서가 안 드는 것

⚠ **이 게이트웨이는 모르는 것을 거절하지 않고 삼킨다.** 400 이 아니라 **200 에 조용히
무시**다. 그래서 *"규격에 있으니 되겠지"* 가 안 통하고, **안 재고 쓰면 안 먹는 줄도
모른다.** 새 계약 낱말·새 블록 종류를 쓰기 전에 프로브로 먼저 잰다.

| 무엇 | 실측 |
|---|---|
| `tools` + `tool_use`→`tool_result` 루프 | 돈다. **실패(`is_error`)를 돌려주면 스스로 고쳐 온다** |
| **`tool_choice: {"type":"none"}`** | **삼킨다** — 200·오류 없이 도구를 그대로 부른다. `system` 유무와 무관 |
| `image` 블록 (user content) | **본다** — 픽셀로 그린 숫자를 읽어 냈다 (찍어서 못 맞히는 값) |
| `image` 를 **`tool_result` 안**에 | **삼킨다** — 받아 놓고 버리고 **색을 지어낸다**(빨강을 「흰색」). ⚠ **여기가 `Read` 가 그림을 싣는 자리다** — 그래서 사내에서 그림을 여는 것이 통째로 눈멀어 있었다. **프록시가 비켜간다**(아래 ⚠) |
| `document` 블록 (PDF·워드·엑셀 원형) | **삼킨다** — 입력 토큰이 첨부 없을 때와 **같다** |
| **오류 코드의 HTTP 상태** | **문서의 매핑을 안 따를 수 있다.** 오류 명세는 `P003`(프로바이더 응답 오류)을 **502** 로 두는데, 실측은 **503** 으로 왔다 — 프로바이더가 낸 상태(구글 `503 UNAVAILABLE` · `Deadline expired before operation could complete.`)를 **그대로 흘린 꼴**이다. **코드로 갈라야지 상태로 갈리면 안 된다** |
| **스트림 180초 컷** (문서에 없다 · **게이트웨이가 제 입으로 든다**) | 스트림이 열려도 **요청부터 180.1초**에 신호(`stop_reason`) 없이 끊긴다. **생성량과 무관하다** — 초당 51토큰이 쉬지 않고 흐르던 판(9,182토큰)도, **한 토큰도 안 나온 판**도 같은 자리에서 잘렸다. 절단의 마지막 바이트가 사유를 적는다: `{"type":"error","error":{"type":"api_error","message":"내부 서버 오류: HTTP request execution did not complete before the specified timeout configuration: 180000 millis"}}` (회사 PC 실측 2026-09-17 · 직결 `stream:true` · 26,836바이트가 흐르던 중). 아래 ⚠ 절이 「어느 겹인가」를 든다 |
| **`cache_control`** (문서에 없다) | **걸린다.** 프로브 쓰기 8,355 → 재호출 읽기 8,355. 실사용에서도 — 렌더가 계획이 데운 판을 읽었다(`cache_read` 35,857 · `cache_write` 0), 도구 루프 왕복도 읽는다(바퀴1 쓰기 36,190 → 바퀴2 읽기 36,190) |
| **비스트리밍의 큰 `tool_use.input`** (문서에 없다) | **삼킨다** — `stream:false` 로 받으면 큰 도구 인자가 `{}` 로 오면서도 `stop_reason` 은 정상 `tool_use` 다. 출력 토큰이 한도에 한참 못 미쳐도(78/64,000) 그렇고, 같은 답의 작은 인자(163B)는 멀쩡하다. 같은 요청을 **스트림**으로 보내면 온전히 온다 — 경로가 갈리는 자리다(실측 2026-09-17 · 재현 3회 · `pgpt-proxy` 결함 추적). ⚠ **오류가 안 나므로 거절하지 않는 클라이언트는 빈 인자로 도구를 실행한다** — 파일을 빈 내용으로 덮을 자리다 |

⚠ **그림은 프록시로 비켜 갔다 — 그림을 어디에 두느냐 하나가 갈랐다.** 위 표의 두 줄이 한 사실의 앞뒤다: 게이트웨이는
`tool_result` **안**의 그림만 버리고, **같은 바이트가 그 블록의 형제로 서면 그대로 읽는다.** 그래서
프록시가 `tool_result` 안의 `image` 를 빼서 같은 메시지 **끝**으로 내놓고 빈 자리에 「그림은 이
메시지 끝에」를 적는다 — 그것만으로 `Read` 가 사내에서 선다(claude-config #76 · 프록시 판 `17.6`).
- **블록을 지우지도, 앞에 끼우지도 않는다** — 짝이 깨지면 400 이고(`tool_use ids were found without
  tool_result blocks`), 짝 검사는 **위치를 본다.**
- **OpenAI 라우트의 `image_url` 은 우회가 아니다** — 200 을 내면서 색은 맞히고 **자리를 틀렸다**.
  반쯤 보는 것이 못 보는 것보다 비싸다: 틀린 답을 자신 있게 낸다.
- **프록시를 안 지나는 자리는 그대로 눈멀어 있다** — 사외·구독 로그인은 애초에 이 벽이 없고, `17.6`
  보다 옛 판 프록시(옛 한 칸 번호 `17`·`18` 포함)를 든 기계는 여전히 못 본다. 판은 `/health` 가 댄다.
- 재는 스크립트와 그것이 어디까지 재나는 `pgpt-proxy/README.md` 의 「재는 법」이 든다 — 눈가림 검체라 답을 화면에
  안 찍는다.

⚠ **그 180초는 요청 시작부터 재는 시계지, 글을 쓰는 시간이 아니다.** 두 관측이 정반대라 깨끗하게 갈린다 —
생성 시간의 벽이라면 0토큰 판이, 침묵 시한이라면 초당 51토큰이 흐른 판이 안 잘렸어야 한다.
둘을 함께 설명하는 것은 **요청부터의 절대 벽** 하나뿐이다.

⚠ **배치로 옮겨진 것이 아니다.** 앤트로픽 Message Batches 는 **별도 엔드포인트**
(`POST /v1/messages/batches`)이고, 호출자가 요청마다 `custom_id` 를 달아 **비스트리밍
파라미터로 싸서** 보낸 뒤 `batch.id` 로 폴링해 따로 받아 간다 — **스트리밍 단건 호출을
조용히 배치로 바꿀 자리가 프로토콜에 없고**, 클라이언트가 그 id 를 모르면 결과를 받을
길도 없다. 완료도 *"most batches complete within 1 hour; maximum 24 hours"* 라 3분 규모가
아니고, 50% 할인의 대가가 비동기인 계약이라 4.8초에 돌려주는 배치도 아니다.
**사내가 제 나름의 큐를 뒀다면 그건 앤트로픽 배치 API 가 아니라 사내 구현이다** — 밖에서 못 잰다.

⚠ **요청이 지나는 층은 셋이고, 180초에 끊는 것은 가운데 층이다** — 게이트웨이가 끊으면서 남긴 사유(위 표)로 갈렸다.

| 층 | 시한 | 어느 길을 끊나 |
|---|---|---|
| 앞단 HAProxy | **300초** (`timeout server`) | 스트림·비스트리밍 **둘 다**. 돌아온 본문이 JSON 이 아니라 HTML(`504 Gateway Time-out`)이라 그 층이 낸 것이 드러난다 |
| **P-GPT 앱** (Bedrock 변환) | **180초** · `180000 millis` | **스트림 길에서만.** 같은 앱의 비스트리밍은 300초까지 산다 — 왜 경로마다 다른지는 그쪽 안이라 밖에서 못 본다 |
| AWS Bedrock | 모른다 | 안 쟀다. 회사 문서의 `C055`(`/agent` 시한 「기본 ≥60초 · 운영팀이 조정」)로 보아 **엔드포인트마다 제 시한이 있고 운영이 조정한다** |

⚠ **유휴(침묵) 시한이 아니다 — 요청 실행 시한이다.** 게이트웨이가 남긴 사유 문장이 `HTTP request execution` 이다:
앱이 **밖으로 나가는 호출**을 기다리는 시계이고, 침묵과 무관하게 걸린다. 26,836바이트가 쉬지 않고
흐르던 판이 같은 자리에서 잘린 것이 그 증거다. ⚠ **그래서 심장박동(keepalive)으로는 안 넘는다** —
주석은 클라이언트 쪽으로만 흐르고 게이트웨이의 시계를 못 되감는다(결정 0044 가 이미 그렇게 판정했다).
넘는 길은 **스트림이 아닌 길로 보내는 것**뿐이다(결정 0051 · 프록시의 unstream 갈래).

**표본 하나 — 2026-08-27, 우리가 안 만든 클라이언트**(Claude Code VS Code 확장)가 같은
게이트웨이에서 `message_start` 하나만 받고 180초를 조용히 있다가 끊겼고, **스트리밍을 접고
다시 부르니 4.80초에 왔다** — 사람 손 없이. 되받기가 빨랐던 것은 그 길에 180초 시한이 없어서다.

**둘째 표본 — 2026-09-09 15:57, 같은 클라이언트(Claude Code 2.1.266 · claude-opus-4.7).** 첫 바이트
268ms 에 `message_start` 267바이트, 그 뒤 조각 없음 → **180.0초**(로그 시각 UTC 06:56:56.175 → 06:59:55.958)에
스트림이 빈 채 끝났고, 클라이언트가 비스트리밍으로 다시 불러 **10.4초**에 왔다. 값이 8-27 판과
같다 — 벽은 클라이언트와 무관한 게이트웨이 시계다. 로그에서 함께 드러난 것이 둘 있다. 그 클라이언트의
「150초 idle warning」은 **경고 줄일 뿐, 비스트리밍으로 되부르게 만든 것이 아니다**(제 유휴 시한은 300초라
벽이 먼저 왔다). 그리고 옵션 없이 생각을 켜는 모델(opus)에서 **생각하는 동안의 조각이 이 게이트웨이를 안
넘어온다** — gemini 는 흘려 달라 하면 흘러오는데(생각 조각 심장박동 · AI-prompt-helper 결정 0033), Claude
쪽은 같은 날 잰 값이 아래와 같다.

**Claude 쪽에서 생각을 하느냐는 모델이 정한다 — 요청에 적은 `thinking` 설정은 모델에 안 닿고, 생각 조각은
스트림으로 안 넘어온다(2026-09-09 18:18, atelier `_check/claude_thinking_probe.py` · `capture_proxy.py`).**
같은 물음(셈 셋)을 두 모델에, `thinking` 설정을 넣은 판과 뺀 판으로 보냈고, Claude Code 가 실제로 보내는
본문도 중계로 잡아 그대로 다시 보냈다. **다시 재는 스크립트는 씨앗에 있다** —
`seeds/gateway/_check/claude_thinking_probe.py`(설치본은 `~/.claude/seeds/gateway/`)이고 앱 없이 돈다.
본문을 중계로 잡는 `capture_proxy.py` 만 아뜰리에 것이라 설치본만 받은 사람은 못 연다. 생각을 재는 눈금은
초과 토큰(출력 토큰 − 눈에 보이는 글자 몫)이다:

- **`claude-opus-4.7` 은 어떤 본문으로 보내도 생각을 안 한다** — 앱 봉투에 `thinking` 을 켜도(초과 15) 꺼도(15)
  같고, Claude Code 의 본문(adaptive · effort high · 베타 여덟)을 모델만 4.7 로 바꿔 보내도 같다(34).
  옛 꼴 `enabled+budget_tokens` 는 4.7 이 문서상 400 으로 되받는데 200 이 온다 — 낱말이 모델에 닿기
  전에 떨어진다
- **`claude-opus-5` 는 어떤 본문으로 보내도 생각을 한다** — 켜도(90) 꺼도(91) Claude Code 의 본문으로도(142)
  앱 봉투에 `thinking` 설정 없이도(98). Opus 5 는 문서상 생각이 기본으로 켜진 모델이라 **모델 기본값이 켠 것**이다.
  Claude Code 의 `opus` 별칭은 이 게이트웨이에서 `claude-opus-5` 로 풀린다(중계로 잡은 본문)
- **생각 조각은 어느 판에도 없다** — Opus 5 가 생각한 판(초과 78~148 · 첫 바이트 뒤 2~4초 침묵)에도
  `thinking` 블록·`thinking_delta` 가 0 이다. 바깥 API 는 같은 본문에 신호를 준다(리모트 실측 · 초과 97 과
  신호 99 가 맞는다). 즉 **모델이 생각하는 동안 게이트웨이는 아무 조각도 안 흘린다.** 뒤가 Bedrock 이면
  Converse 스트림의 생각 조각(`reasoningContent`)을 안 옮기는 꼴과 맞아떨어진다 — 추정이다
- **따라서 위 두 표본(Claude Code · `claude-opus-4.7`)의 180초 침묵은 생각이 아니다.** 4.7 은 이 게이트웨이에서
  생각을 안 한다. 첫 바이트 뒤 아무것도 안 온 채 벽에 닿은 원인은 게이트웨이 안쪽이고 밖에서 못 가른다.
  잡는 길은 하나다 — VS Code 를 `capture_proxy.py serve` 너머로 두면 멈추는 그 요청이 본문과 응답 시각
  (첫 바이트 · 첫 글자 · 벽)을 함께 남긴다
- **생각을 조일 손잡이는 없다 — 2026-09-09 18:37, `effort_probe.py`.** `claude-opus-5` 에 같은 물음(답 두 줄)을
  `output_config.effort` low·high·xhigh·max 와 `thinking: disabled` 로 판마다 두 번 보냈다. 초과 토큰이 전부
  166~201 로 같고 disabled 도 184~199 다. 넷 다 400 없이 200 — **효과값도 disabled 도 모델에 안 닿는다.**
  `thinking`·`output_config` 는 이 게이트웨이가 통째로 떨구는 필드다
- **게이트웨이 팀에 낼 보고** — `gateway-report-claude-thinking-2026-09-09.md`(관측 사실 · 여쭙는 것 셋 · curl 재현 ·
  설치본에는 안 실린다). 답이 오면 이 절을 그 답으로 고친다
- atelier 는 회사에서 `claude-opus-5` 를 쓰므로 **생각이 켜진 채 조용히, 조일 수 없이 돈다.** 렌더 봉투에서
  그 생각이 180초를 넘으면 스트림 벽 → 접은 비스트리밍이 300초를 더 태우고 504 (2026-09-07 14:07~14:15 실측,
  atelier `output/_fail/fail-141502`). 이 게이트웨이에서 침묵을 없애는 손잡이는 **모델 이름**뿐이다 — 4.7 은
  생각을 안 한다
- **동료 도구 `pgpt-one-click-connect` 는 이 벽을 안 건드린다** — 사내 다른 사용자(sejuone-cloud)가 배포한
  Claude Code·Codex·Paseo·Hermes 용 원클릭 설치기(읽은 판: 그 저장소의 포크 · 비공개 · 프록시 v14 ·
  2026-09-14 대조). `127.0.0.1:18901` 에 파이썬 프록시(`app/opus5_proxy.py`)를 세우고 클라이언트의 base URL 을 거기로
  돌린다. 그 프록시가 `/v1/messages` 에 하는 일은 **요청 본문 보정뿐**이다 — 끝의 assistant 마디(prefill) 제거 ·
  `system` 역할 마디를 `user` 로 · 같은 역할 병합 · `temperature`/`top_p` 제거. **응답은 스트리밍 포함 무수정
  중계**다(심장박동 없음 · 생각 낱말 안 건드림 · 상류 타임아웃 600초). 그쪽이 푼 것은 **Opus 5 직결 때의 400**
  (「assistant message prefill」 거절 — 그 저장소 README · `docs/수동-설정.md`)이고, 우리 실패는 전부 **200 뒤
  침묵 → 504** 라(atelier `output/_fail/fail-141502`·`190126`·`191131` · 09-10 은 4.7 로도 504) 층이 다르다.
  atelier 는 prefill 로 끝나는 봉투를 안 보낸다 — 이어받기(`llm._post` resume)도 user 「이어서」 마디로 끝난다.
  그쪽 검증은 전부 짧은 「Reply OK」 스모크(`tests/Test-AllPgptModels.py`)라 긴 생성의 벽은 잰 적이 없다.
  **우리 사본은 `posco/pgpt-proxy/`** — 프록시·가짜 게이트웨이·전수 스모크를 통째로 담았고, 무엇을 쓰고 무엇이
  놀고 있나와 상류 판·갱신법은 그 폴더의 README 가 든다(결정 0041).
  - 건질 것 — 그쪽 `docs/P-GPT_연동_노하우.md` 가 「Claude 경로는 내부적으로 Bedrock Converse 로 변환」이라 적어 위
    「추정」과 방향이 같다(그쪽도 실측이 아니라 전언). 그쪽 설치기는 Claude Code 에
    `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` 을 심고 별칭(`opus`) 대신 명시 ID 만 쓰라 한다. `claude-sonnet-5` 는
    게이트웨이에 미등록이라 프록시가 `claude-sonnet-4.6` 으로 바꿔 보낸다
  - **실측 2026-09-14(회사) — 프록시는 벽을 안 넘는다.** 아뜰리에를 `ATELIER_GATEWAY_URL` 로 프록시 너머에
    두고 Opus 5 렌더 한 판: 첫 글자 없이 180초에 끊겼다(사용자 실측). 같은 날 Claude Code(VS Code 2.1.270 ·
    `claude-opus-5` · 프록시 너머) 75 요청 중 짧은 도구 루프는 첫 바이트 0.4초로 흘렀고, 셋은 60초 유휴
    워치독(`CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS`)에 끊겨 비스트리밍으로 되받아 각 65초쯤에 성공, 13:50 의
    한 턴은 180초 벽 → 비스트리밍 300초 초과 → 재시도 300초 초과 → 14:04 포기(14분). 자동 압축 요청
    (`source=compact`)도 첫 바이트 뒤 멈췄다 — 압축을 다른 모델로 돌릴 설정은 문서에 없다. 원형은
    `cli-log/2026-09-14 132157.593 *` · `cli-log/autocompact problem.txt`. 그래서 프록시가 Opus 5 의 문(400)을
    연다(결정 0041). 별칭을 어디 두나는 그 뒤 결정 0046 이 든다 — 기본도 `opus` 별칭도 Opus 5 다. 4.7 을 고르는
    자리는 결정 0048 이 `modelPicker` 로 옮겼다
  - **워치독 둘은 끊는 쪽이 Claude Code 일 때만 효과가 있다 — 실제로 끊던 것은 게이트웨이였다(2026-09-17 실측).**
    자리 파일이 유휴 워치독 둘(`CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS` · `CLAUDE_STREAM_IDLE_TIMEOUT_MS`)을 10분으로
    심고, 프록시가 상류 침묵 15초마다 SSE 주석을 흘린다(`/health` 의 `keepalives` · 결정 0044). **둘 다 그대로 두지만
    이 벽에는 안 통한다** — 까닭은 위 층 표가 든다. ⚠ **바이너리 실측 2026-09-17**: 값으로 읽히는 것은
    `CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS` 하나고, `CLAUDE_STREAM_IDLE_TIMEOUT_MS` 는 **`>0` 인지만 보는 스위치**다
    (원격 설정을 무시하라는 뜻 · 첫 변수가 이미 이겨 그 갈래는 안 밟힌다). 클램프도 있다(`Math.min(Math.max(…))`).
    압축 모델을 따로 두는 설정은 문서에 없다(claude-code-guide 재확인 2026-09-15)
  - **끊는 쪽이 게이트웨이(180초 스트림 상한)면 셋째 방법 — 프록시가 스트림을 비스트리밍으로 받아 SSE 로 지어
    낸다(결정 0051).** 회사 PC 실측 2026-09-16(이슈 #46): 직결 `stream:false` 는 119초에 `200`, 300.04초에야 **앞단 HAProxy**
    가 `504`(HTML) — 비스트리밍 경로에는 180초 상한이 없다. 그래서 프록시는 `/v1/messages` 의 `stream:true` 를
    상류엔 `stream:false` 로 보내고 기다리는 동안 0044 의 주석을 흘리다 답을 SSE 로 짓는다(`/health` 의 `unstreamed` ·
    **기본은 끔** · `PGPT_PROXY_UNSTREAM=1` 이면 켠다). 다음 벽은 앞단의 300초다.
    ⚠ **켜면 큰 도구 인자가 빈다 — 그래서 도구를 쓰는 클라이언트에는 안 켠다**(실측 2026-09-17 · 재현 3회).
    켠 판에서 `Edit` 호출이 `input={}` 로 오고(`out=78/64000` 이라 한도와 무관 · `stop_reason` 은 정상 `tool_use`)
    같은 판의 작은 `Bash`(163B)는 멀쩡하다. **SSE 를 짓는 우리 코드 탓은 아니다** — 6,642자 도구 입력이 SSE 왕복해 글자 대
    글자로 살아남는다. 까닭은 게이트웨이 안이라 밖에서 못 본다. 곧 **스트림 경로와 비스트리밍 경로가 다르게
    도는 증거가 둘**이다(180초 시한 · 이 인자 유실). 도구를 안 쓰는 아뜰리에는 켜서 벽을 비껴갈 수 있다
  - **Gemini CLI 는 회사 문서의 번들 패치를 안 쓴다** — 문서(`Gemini-Posco.setting.md`)는 http 주소를 받게 CLI 파일을
    고치는 `gemini-patch.ps1` 을 시키고 업데이트마다 다시 돌리라 하는데, 우리는 주소를 루프백 프록시로 둔다(결정 0041 ·
    `GOOGLE_GEMINI_BASE_URL`). CLI 가 루프백은 http 를 허용해 고칠 파일이 없다. 그 스크립트는 이 저장소에서 지웠다
  - **안티그래비티는 로그인 없이 회사 키로 선다** — VS Code 확장 `Google.google-antigravity` 는 다리 역할만 하고,
    게이트웨이에 실제로 붙는 것은 확장이 받아 오는 `agy`(`~/.gemini/bin/agy.exe`)다. 확장 설정에는 주소 칸이 없어
    거기만 보면 「못 붙인다」로 읽히는데,
    `agy` 쪽에 셋이 있다 — `~/.gemini/antigravity-cli/settings.json` 의 `modelProvider: "gemini"` ·
    `GEMINI_API_KEY` · `GOOGLE_GEMINI_BASE_URL`(Gemini CLI 와 **같은 이름을 공유해** 루프백 프록시를 그대로 탄다).
    그 셋으로 `agy` 가 `authenticated via gemini_api_key` 를 찍고 게이트웨이가 답했다(실측 2026-09-17 ·
    `gemini-3.6-flash --effort medium`). **게이트웨이가 답했다는 근거**는 게이트웨이만 내는 이 문구다 —
    「모델을 찾을 수 없습니다 … 회사코드: 02」
    ⚠ **`GOOGLE_API_KEY` 가 사용자 환경에 있으면 회사 키를 제친다** — `agy` 가 스스로 알린다(`Both GOOGLE_API_KEY and
    GEMINI_API_KEY are set. Using GOOGLE_API_KEY.`). 그러면 **답은 오는데 구글에서 온다** — 답이 왔다는 것과
    게이트웨이가 답했다는 것이 다른 명제라, 여기서 두 번 잘못 짚었다. 가른 것은 프록시 로그에 그 호출이 없다는 사실이었다
    ⚠ **제목 짓기는 못박힌 이름으로 나간다 — 프록시가 고친다.** `agy` 가 대화 제목 생성에
    `gemini-3.1-flash-lite-preview` 를 쓰는데 게이트웨이에는 `-preview` 없는 판만 있어 그 곁 호출만 `400`
    이었다. 고를 모델을 바꿔도 이 이름은 그대로다(실측: `3.6-flash` · `3.1-pro-low` · `3.8-flash-low` 세 판 다
    같은 이름) — 바이너리 상수라 `agy` 쪽에 갈 손잡이가 없다. 프록시가 이름을 갈아 보낸다
    (`_GEMINI_MODEL_ALIASES` · 옛 한 칸 판 번호로 v18 부터 · `pgpt-proxy/README.md` 의 예외 ⑷).
    ⚠ **접미사를 규칙으로 떼지 않는다** — `gemini-3.1-pro-preview` 는 게이트웨이에 실제로 있고 본 턴이 그 이름으로
    통한다
  - **게이트웨이는 `POST /v1/messages/count_tokens` 를 404(`E006`)로 되돌린다** — 같은 로그. Claude Code 는
    「count unavailable, estimating locally」로 넘어가 해는 없다. 게이트웨이 팀 보고에 얹을 한 줄

⚠ 위 두 표본(2026-08-27 · 09-09)에서 비스트리밍 재요청이 빨리 온 것(4.80초 · 10.4초)은 둘 다 캐시나 짧은 답
덕일 수도 있다 — 스트림을 접은 길이 정말 빠른지는 표본 둘로 못 가른다.

## 아직 안 잰 것 — 다음에 잴 자리

- **`anthropic-beta` 헤더가 문서 헤더 표에 없다.** 우리는 둘을 싣는다 —
  `output-128k-2025-02-19`(128K 출력)와 `extended-cache-ttl-2025-04-11`(캐시 1시간).
  게이트웨이가 이 헤더를 흘려 버리면 **출력 상한은 옛 값이고 캐시 수명은 5분**이다. 캐시가 걸리는 것도 앞 턴→뒤 턴
  전달이 되는 것도 확인했지만 **그 판들이 몇 분 만에 이어졌는지는 안 쟀다** — 5분으로도
  설명되는 간격이다. 게이트웨이가 수명별로 쪼갠 항(`ephemeral_1h_input_tokens`)을 **안
  실어 보내** 응답으로는 못 가린다. 남은 길은 같은 요청을 **6분 이상 사이를 두고** 두 번 부르는 것
- `tool_choice` 의 나머지 세 값 · `metadata.user_id` · `temperature`·`top_p`·`top_k`

**재는 자리** — `atelier/_check/` 의 프로브들: `tool_probe.py`(도구·이미지·`tool_choice`) ·
`gateway_probe.py`(캐시 쓰기/읽기) · `attach_probe.py`(첨부 블록). 원형 응답은
`atelier/_check/log/` 에 남는다. **여기 수치를 손으로 옮기지 말고 그 프로브를 다시
돌린다** — 게이트웨이는 예고 없이 바뀐다.

## 네트워크 접근

- GitHub **HTTPS만 가능** (`github.com`, `api.github.com`, `raw.githubusercontent.com` 전부 200). 프록시 없음, 직결.
- GitHub **SSH는 차단** (22번, 443번 대체 포트 모두 타임아웃) → 리모트는 반드시 `https://...` 형식
- Git 인증 세팅 완료: `credential.helper=manager` (GCM + OAuth 방식, PAT 불필요, 첫 push 때 브라우저 로그인)
- Git 신원·기본 브랜치·`core.autocrlf` 는 **세션 훅이 심는다** — 원본은 훅 몸통
  `claude-config/.claude/hooks/session-start-body.sh` 의 개인 칸(`deploy_personal`)이다(`session-start.sh` 는
  몸통을 찾아 넘기는 문지기다). 여기 옮겨 적으면 어긋난다
- Supabase 접근 가능
- Google Drive, Gmail 발신은 사내망에서 불가
- npm 레지스트리 접근 가능
- 신규 패키지는 **유료 라이선스인지만** 본다 — 설치 시점에 이미 걸리는 확인이다. 무료면 그대로 깐다

## 환경

- Windows 11 Enterprise, PowerShell (Git Bash 병행), VS Code
- Node.js v24.x (npm 11), Python 3.14.6, Git 2.55
- PostgreSQL CLI(`psql`) 미설치 — 로컬 DB 필요시 설치 안내 요청
- `.env` 로드 시 항상 `load_dotenv(override=True)`. 우선순위: `$env:` > 시스템 > `.env`
- 근무 외 시간 PC 종료 → 야간 자동화 스케줄러는 별도 협의 전 가정 금지

## 보안

- API 키를 채팅/파일/커밋에 절대 노출 금지. 유출 시 IT 재발급 요청
- PII, 계약, HR 문서는 처리 대상 아님

## 구현 범위 (전역)

- 로그인/인증/권한 구현 불필요 — 별도 시스템에서 처리됨. 요청 없으면 만들지 말 것
- 기본 스택 권장: **Node.js + PostgreSQL** (Supabase 사용 가능하니 자연스럽게 매칭)
- 모바일 앱 개발은 범위 밖 — 웹만

## 기타

- 에러 발생 시 원인 한 줄로 먼저, 고치기 전에 확인
- 프로젝트별 CLAUDE.md가 있으면 그쪽 규칙 우선 (atelier, intelligence 등)
