# 사내 환경 (POSCO) — 기록·관리용

> 전역 룰은 `.claude/CLAUDE.global.md`. 이 문서는 **배포 대상이 아니다** — 사내 환경 정보가 필요할 때 열어서 참조한다.

**사용자**: 초심자. 한 번에 한 명령씩, 성공 확인 후 다음 단계. 한국어로 설명.

**LLM API**: Anthropic API 직접 호출 불가 → 사내 게이트웨이 P-GPT 사용

> **명세는 여기 안 적는다** — 사내 문서 두 장이 진본이다:
> [`Claude-Posco.setting.md`](Claude-Posco.setting.md) (Messages API · Claude Code 연동) ·
> [`OpenAI.-Posco.Setting.md`](OpenAI.-Posco.Setting.md) (chat/completions · responses).
> 주소·헤더·파라미터·오류 코드·모델 목록은 전부 그쪽이 든다. **베껴 적으면 어긋난다.**
>
> ⚠ **다만 그 문서가 곧 사실은 아니다.** 아래 절이 그 차이를 든다.
>
> ⚠ **게이트웨이 앞에 한 겹이 더 있다.** 우리가 받는 504 중에는 P-GPT 가 낸 것이 아닌
> 것이 있다 — [`gateway-front-haproxy.md`](gateway-front-haproxy.md) 가 그 층을 든다.
> **사내 문서 어느 장도 그 층은 안 든다.**

- 백엔드는 **AWS Bedrock**이다 (문서가 밝힌다) — Anthropic 고유 기능 중 Bedrock 이 가진
  것만 건너간다고 보면 관측이 대체로 맞아떨어진다
- 우리가 쓰는 인증 — 앱(Anthropic SDK)은 `ANTHROPIC_AUTH_TOKEN` → Bearer,
  Claude Code CLI 는 `ANTHROPIC_API_KEY` → `x-api-key`. **게이트웨이는 둘 다 받는다** —
  클라이언트마다 읽는 이름이 다를 뿐이라, 하나를 「이게 아니다」로 못 박으면 다른
  클라이언트를 못 붙인다
- 우리가 쓰는 모델 — **`claude-opus-5` 가 기본이고 `opus` 별칭도 그것이다**(Claude Code · atelier).
  `claude-opus-4.7` 은 `/model` 의 Custom 칸에 두고, `claude-sonnet-4.6` 도 목록에 선다(결정 0046).
  ⚠ **`claude-opus-5` 는 사내 문서 「지원 모델」 표에 없지만 실제로 돈다**
  (사용자 확인 2026-08-20) — **문서가 뒤처진 것이다.** 목록을 의심할 일이 있으면
  문서가 아니라 `GET /v1/models` 에 묻는다

## 우리가 잰 것 — 문서가 안 드는 것

⚠ **이 게이트웨이는 모르는 것을 거절하지 않고 삼킨다.** 400 이 아니라 **200 에 조용히
무시**다. 그래서 *"규격에 있으니 되겠지"* 가 안 통하고, **안 재고 쓰면 안 먹는 줄도
모른다.** 새 계약 낱말·새 블록 종류를 쓰기 전에 프로브로 먼저 잰다.

| 무엇 | 실측 |
|---|---|
| `tools` + `tool_use`→`tool_result` 루프 | 돈다. **실패(`is_error`)를 돌려주면 스스로 고쳐 온다** |
| **`tool_choice: {"type":"none"}`** | **삼킨다** — 200·오류 없이 도구를 그대로 부른다. `system` 유무와 무관 |
| `image` 블록 (user content) | **본다** — 픽셀로 그린 숫자를 읽어 냈다 (찍어서 못 맞히는 값) |
| `image` 를 **`tool_result` 안**에 | **삼킨다** — 받아 놓고 버리고 **색을 지어낸다**(빨강을 「흰색」) |
| `document` 블록 (PDF·워드·엑셀 원형) | **삼킨다** — 입력 토큰이 첨부 없을 때와 **같다** |
| **오류 코드의 HTTP 상태** | **문서의 매핑을 안 따를 수 있다.** 오류 명세는 `P003`(프로바이더 응답 오류)을 **502** 로 두는데, 실측은 **503** 으로 왔다 — 프로바이더가 낸 상태(구글 `503 UNAVAILABLE` · `Deadline expired before operation could complete.`)를 **그대로 흘린 꼴**이다. **코드로 갈라야지 상태로 갈리면 안 된다** |
| **스트림 180초 컷** (문서에 없다) | 스트림이 열려도 **요청부터 180.1초**에 신호(`stop_reason`) 없이 끊긴다. **생성량과 무관하다** — 초당 51토큰이 쉬지 않고 흐르던 판(9,182토큰)도, **한 토큰도 안 나온 판**도 같은 자리에서 잘렸다. 아래 ⚠ 절이 「그럼 무엇인가」를 든다 |
| **`cache_control`** (문서에 없다) | **걸린다.** 프로브 쓰기 8,355 → 재호출 읽기 8,355. 실사용에서도 — 렌더가 계획이 데운 판을 읽었다(`cache_read` 35,857 · `cache_write` 0), 도구 루프 왕복도 읽는다(바퀴1 쓰기 36,190 → 바퀴2 읽기 36,190) |

⚠ **그 180초는 시계지 「글 쓰는 시간」이 아니다.** 두 관측이 정반대라 가름이 깨끗하다 —
생성 시간의 벽이라면 0토큰 판이, 침묵 시한이라면 초당 51토큰이 흐른 판이 안 잘렸어야 한다.
둘을 함께 설명하는 것은 **요청부터의 절대 벽** 하나뿐이다.

⚠ **배치로 옮겨진 것이 아니다.** 앤트로픽 Message Batches 는 **별도 엔드포인트**
(`POST /v1/messages/batches`)이고, 호출자가 요청마다 `custom_id` 를 달아 **비스트리밍
파라미터로 싸서** 보낸 뒤 `batch.id` 로 폴링해 따로 받아 간다 — **스트리밍 단건 호출을
조용히 배치로 바꿀 자리가 프로토콜에 없고**, 클라이언트가 그 id 를 모르면 결과를 받을
길도 없다. 완료도 *"most batches complete within 1 hour; maximum 24 hours"* 라 3분 규모가
아니고, 50% 할인의 대가가 비동기인 계약이라 4.8초에 돌려주는 배치도 아니다.
**사내가 제 나름의 큐를 뒀다면 그건 앤트로픽 배치 API 가 아니라 사내 구현이다** — 밖에서 못 잰다.

⚠ **앞단 HAProxy 도 아니다** — 그 층 실측은 `timeout server` **300초**라 값이 안 맞는다
(300 ≠ 180 · [`gateway-front-haproxy.md`](gateway-front-haproxy.md)). **어느 겹인지는
모른다**: P-GPT 앱인지 그 안의 또 다른 홉인지 밖에서 못 가른다.

**남는 설명은 조용한 선을 무는 유휴 자다.** 2026-08-27, **우리가 안 만든 클라이언트**
(Claude Code VS Code 확장)가 같은 게이트웨이에서 `message_start` 하나만 받고 180초를
조용히 있다가 끊겼고, **스트리밍을 접고 다시 부르니 4.80초에 왔다** — 사람 손 없이.
일이 오래 걸린 것이 아니라 **선이 죽은 것**이다. 처방은 앞단 문서가 이미 든다 —
*「선을 조용하게 두지 않는다」*(심장박동).
**둘째 표본 — 2026-09-09 15:57, 같은 클라이언트(Claude Code 2.1.266 · claude-opus-4.7).** 첫 바이트
268ms 에 `message_start` 267바이트, 그 뒤 조각 없음 → **180.0초**(06:56:56.175 → 06:59:55.958)에
스트림이 빈 채 끝났고, 클라이언트가 비스트리밍으로 다시 불러 **10.4초**에 왔다. 값이 8-27 판과
같다 — 벽은 클라이언트와 무관한 게이트웨이 시계다. 곁에서 읽힌 것 둘: 그 클라이언트의 로그
「150초 idle warning」은 **경고 줄이지 폴백을 부른 자가 아니다**(제 유휴 시한은 300초 · 벽이 먼저
왔다) · 옵션 없이 생각을 켜는 모델(opus)에서 **생각 구간의 조각이 이 게이트웨이를 안 넘어온다** —
gemini 는 흘려 달라 하면 흘러오는데(생각 조각 심장박동 · AI-prompt-helper 결정 0033) Claude 갈래는
같은 날 잰 값이 아래다.
**Claude 갈래의 생각은 모델이 정하고, 낱말은 무관하며, 조각은 선을 안 탄다 — 2026-09-09 18:18,
atelier `_check/claude_thinking_probe.py` · `capture_proxy.py`.** 같은 물음(셈 셋)을 두 모델 × 낱말
있이·없이로 보내고, Claude Code 가 실제로 보내는 몸을 중계로 잡아 되보냈다. **다시 재는 자는 씨앗에
있다** — `seeds/gateway/_check/claude_thinking_probe.py`(설치본은 `~/.claude/seeds/gateway/`). 앱 없이
돈다. 몸을 중계로 잡는 자만 아뜰리에 것이라 받는 사람은 못 연다. 초과 토큰(출력 토큰 −
글자 몫)이 생각의 자다:

- **`claude-opus-4.7` 은 어떤 몸으로도 생각이 안 난다** — 앱 봉투에 `thinking` 을 켜도(초과 15) 꺼도(15)
  같고, Claude Code 의 몸(adaptive · effort high · 베타 여덟)을 모델만 4.7 로 바꿔 보내도 같다(34).
  옛 꼴 `enabled+budget_tokens` 는 4.7 이 문서상 400 으로 되받는데 200 이 온다 — 낱말이 모델에 닿기
  전에 떨어진다
- **`claude-opus-5` 는 어떤 몸으로도 생각이 난다** — 켜도(90) 꺼도(91) Claude Code 의 몸으로도(142) 앱
  봉투에 낱말 없이도(98). Opus 5 는 문서상 생각이 기본으로 켜진 모델이라 **모델 기본값이 켠 것**이다.
  Claude Code 의 `opus` 별칭은 이 게이트웨이에서 `claude-opus-5` 로 풀린다(잡은 몸)
- **생각 조각은 어느 판에도 없다** — Opus 5 가 생각한 판(초과 78~148 · 첫 바이트 뒤 2~4초 침묵)에도
  `thinking` 블록·`thinking_delta` 가 0 이다. 바깥 API 는 같은 몸에 신호를 준다(리모트 실측 · 초과 97 과
  신호 99 가 맞는다). 즉 **모델이 생각하는 동안 게이트웨이는 아무 조각도 안 흘린다.** 뒤가 Bedrock 이면
  Converse 스트림의 생각 조각(`reasoningContent`)을 안 옮기는 꼴과 맞아떨어진다 — 추정이다
- **따라서 위 두 표본(Claude Code · `claude-opus-4.7`)의 180초 침묵은 생각이 아니다.** 4.7 은 이 게이트웨이에서
  생각을 안 한다. 첫 바이트 뒤 아무것도 안 온 채 벽에 닿은 원인은 게이트웨이 안쪽이고 밖에서 못 가른다.
  잡는 길은 하나다 — VS Code 를 `capture_proxy.py serve` 너머로 두면 멈추는 그 요청이 몸과 응답 시각
  (첫 바이트 · 첫 글자 · 벽)을 함께 남긴다
- **생각을 조일 손잡이는 없다 — 2026-09-09 18:37, `effort_probe.py`.** `claude-opus-5` 에 같은 물음(답 두 줄)을
  `output_config.effort` low·high·xhigh·max 와 `thinking: disabled` 로 판마다 두 번 보냈다. 초과 토큰이 전부
  166~201 로 같고 disabled 도 184~199 다. 넷 다 400 없이 200 — **효과값도 disabled 도 모델에 안 닿는다.**
  `thinking`·`output_config` 는 이 게이트웨이가 통째로 떨구는 필드다
- **게이트웨이 팀에 낼 보고** — [`gateway-report-claude-thinking-2026-09-09.md`](gateway-report-claude-thinking-2026-09-09.md)(관측 사실 · 여쭙는 것 셋 · curl 재현). 답이 오면 이 절을 그 답으로 고친다
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
    연다(결정 0041). 별칭을 어디 두나는 그 뒤 결정 0046 이 든다 — 기본도 `opus` 별칭도 Opus 5 이고 4.7 은 Custom 칸이다
  - **침묵을 끊는 자가 Claude Code 쪽이면 두 손이 있다(결정 0044 · 둘 다 회사 실측 전).** 자리 파일이 유휴 워치독 둘
    (`CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS` · `CLAUDE_STREAM_IDLE_TIMEOUT_MS`)을 10분으로 심고, 프록시(v15)가 상류
    침묵 15초마다 SSE 주석을 흘린다(`/health` 의 `keepalives`). 게이트웨이 쪽이 제 침묵에 끊는 것이면 둘 다 못 막는다 —
    그때는 게이트웨이 팀에 낼 한 줄이다. 압축 모델을 따로 두는 설정은 문서에 없다(claude-code-guide 재확인 2026-09-15)
  - **Gemini CLI 는 회사 문서의 번들 패치를 안 쓴다** — 문서(`Gemini-Posco.setting.md`)는 http 주소를 받게 CLI 파일을
    고치는 `gemini-patch.ps1` 을 시키고 업데이트마다 다시 돌리라 하는데, 우리는 주소를 루프백 프록시로 둔다(결정 0041 ·
    `GOOGLE_GEMINI_BASE_URL`). CLI 가 루프백은 http 를 허용해 고칠 파일이 없다. 그 스크립트는 이 저장소에서 지웠다
  - **게이트웨이는 `POST /v1/messages/count_tokens` 를 404(`E006`)로 되돌린다** — 같은 로그. Claude Code 는
    「count unavailable, estimating locally」로 넘어가 해는 없다. 게이트웨이 팀 보고에 얹을 한 줄
⚠ 재요청이 짧게 온 것은 여전히 두 판 다 캐시·짧은 답일 수 있다 — 접은 길의 값은 표본 둘로도 못 가른다.

## 아직 안 잰 것 — 다음에 물릴 자리

- **`anthropic-beta` 헤더가 문서 헤더 표에 없다.** 우리는 둘을 싣는다 —
  `output-128k-2025-02-19`(128K 출력)와 `extended-cache-ttl-2025-04-11`(캐시 1시간).
  흘려지면 **출력 상한은 옛 값이고 캐시 수명은 5분**이다. 캐시가 걸리는 것도 앞 턴→뒤 턴
  전달이 되는 것도 확인했지만 **그 판들이 몇 분 만에 이어졌는지는 안 쟀다** — 5분으로도
  설명되는 간격이다. 게이트웨이가 수명별로 쪼갠 항(`ephemeral_1h_input_tokens`)을 **안
  실어 보내** 응답으로는 못 가린다. 남은 길은 같은 봉투를 **6분 이상 띄워** 두 번 부르는 것
- `tool_choice` 의 나머지 세 값 · `metadata.user_id` · `temperature`·`top_p`·`top_k`

**재는 자리** — `atelier/_check/` 의 프로브들: `tool_probe.py`(도구·이미지·`tool_choice`) ·
`gateway_probe.py`(캐시 쓰기/읽기) · `attach_probe.py`(첨부 블록). 원형 응답은
`atelier/_check/log/` 에 남는다. **여기 수치를 손으로 옮기지 말고 그 프로브를 다시
돌린다** — 게이트웨이는 예고 없이 바뀐다.

## 네트워크 접근

- GitHub **HTTPS만 가능** (`github.com`, `api.github.com`, `raw.githubusercontent.com` 전부 200). 프록시 없음, 직결.
- GitHub **SSH는 차단** (22번, 443번 대체 포트 모두 타임아웃) → 리모트는 반드시 `https://...` 형식
- Git 인증 세팅 완료: `credential.helper=manager` (GCM + OAuth 방식, PAT 불필요, 첫 push 때 브라우저 로그인)
- Git 신원·기본 브랜치·`core.autocrlf` 는 **세션 훅이 심는다** — 진본은
  `claude-config/.claude/hooks/session-start.sh` 의 개인 칸(`deploy_personal`)이다. 여기 옮겨 적으면 어긋난다
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
