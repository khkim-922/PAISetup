# P-GPT Claude 경로 — 생각(thinking) 설정이 전달되지 않고 생각 구간이 스트림에서 비어 긴 요청이 시간 초과로 끝납니다

작성 2026-09-09 · 대상 P-GPT(`aigpt.posco.net/gpgpta01-gpt`) 운영팀 · 측정 주체 사내 사용자(Claude 연동 앱 · Claude Code)

## 요약

P-GPT 의 Claude 경로에서 두 가지가 관측됩니다. 첫째, 요청에 실은 생각 관련 설정(`thinking`,
`output_config.effort`)이 모델에 전달되지 않습니다. 둘째, 모델이 생각하는 동안의 스트림 이벤트
(`thinking` 블록)가 클라이언트에 오지 않습니다. 그 결과 생각이 기본으로 켜진 모델(`claude-opus-5`)은
긴 요청에서 첫 글자가 오기 전에 180초 동안 아무 이벤트도 없다가 스트림이 닫히고, 클라이언트가
비스트리밍으로 재시도하면 300초 뒤 504 가 됩니다. 한 번의 요청이 8분을 소모하고 실패합니다.

## 관측 사실

같은 질문(짧은 셈 문제 · 답 두 줄)을 모델과 설정만 바꿔 보내고, 응답의 `usage.output_tokens` 에서
글자 수에 해당하는 몫을 뺀 **초과 토큰**으로 생각량을 읽었습니다. 판마다 두 번씩 보냈습니다.

| 모델 | 설정 | 초과 토큰 | 생각 블록 이벤트 |
|---|---|---|---|
| claude-opus-4.7 | 없음 | 15 | 0 |
| claude-opus-4.7 | `thinking: {type: adaptive}` | 15 | 0 |
| claude-opus-4.7 | `thinking: {type: enabled, budget_tokens: 4096}` | 16 | 0 |
| claude-opus-5 | 없음 | 91 | 0 |
| claude-opus-5 | `thinking: {type: adaptive}` | 90 | 0 |
| claude-opus-5 | `output_config.effort` low / high / xhigh / max | 198 / 177 / 199 / 182 | 0 |
| claude-opus-5 | `thinking: {type: disabled}` | 192 | 0 |

읽히는 것은 셋입니다.

1. **설정이 모델에 닿지 않습니다.** 4.7 은 `thinking` 을 어떻게 실어도 생각을 안 하고, Opus 5 는
   `disabled` 를 실어도 생각을 합니다. `effort` 넷의 생각량이 같습니다. 참고로
   `enabled + budget_tokens` 는 Anthropic 문서상 4.7 에서 400 이 나야 하는 형식인데 200 으로 옵니다.
2. **생각은 모델 기본값이 정합니다.** Opus 5 는 문서상 생각이 기본으로 켜진 모델이라 설정과 무관하게
   생각하고, 그 토큰이 `output_tokens` 에 계산됩니다(위 표의 초과분).
3. **생각 구간이 스트림에서 비어 있습니다.** Opus 5 가 생각한 판에도 `content_block_start(type:
   thinking)` · `thinking_delta` 이벤트가 0 입니다. 같은 요청을 Anthropic 공식 API(`api.anthropic.com`)
   로 보내면 첫 글자 전에 생각 이벤트가 오고, 그 생각량(99)이 초과 토큰(97)과 일치합니다.

실제 실패 세 건의 시간표입니다(Claude 연동 앱의 요청 기록 · 모델 claude-opus-5 · 긴 문서 생성 요청).

| 요청 시작 | 종료 | 소요 | 종료 사유 |
|---|---|---|---|
| 09-07 14:07:02 | 14:15:02 | 480초 | 스트림 180초 무응답 후 닫힘 → 비스트리밍 재시도 → HAProxy 504 |
| 09-09 18:53:25 | 19:01:26 | 481초 | 같음 |
| 09-09 19:03:31 | 19:11:31 | 480초 | 같음 |

480초 = 스트림 상한 180초 + 비스트리밍 앞단 상한 300초입니다. 스트림 쪽 첫 이벤트(`message_start`)는
0.3초에 오고 그 뒤 아무것도 오지 않습니다. `message_start` 의 `usage.output_tokens` 가 0 으로 오는
것도 함께 적어 둡니다(공식 API 는 1).

같은 게이트웨이를 쓰는 Claude Code(VS Code 확장 · 모델 claude-opus-4.7)에서도 `message_start` 뒤
180초 무응답 후 닫히는 판이 8-27, 9-9 두 차례 기록됐습니다. 4.7 은 이 경로에서 생각을 안 하므로 이
침묵은 생각이 아닙니다. 원인은 저희 쪽에서 가릴 수 없어 별도 항목으로 둡니다.

## 여쭙는 것

1. **Claude 경로가 Bedrock 의 어느 API 로 연결되어 있는지** — Messages API 호환 엔드포인트
   (`/anthropic/v1/messages` · SSE)인지, `InvokeModel`/`Converse`(AWS 이벤트 스트림)인지. 후자라면
   요청·응답을 변환하는 층이 있고, 위 관측(설정 누락 · 생각 이벤트 누락 · `output_tokens` 0)은 그 변환이
   `thinking`/`output_config` 필드와 `reasoningContent` 이벤트를 옮기지 않는 모양과 일치합니다.
2. **`thinking` · `output_config` 를 요청 그대로 전달하고, 응답의 생각 블록 이벤트를 클라이언트로
   되돌려 줄 수 있는지.** 둘 중 하나만 되어도 문제가 풀립니다 — 설정이 전달되면 생각 길이를 줄여
   180초 안에 들어오고, 생각 이벤트가 오면 스트림이 비지 않아 상한에 걸리지 않습니다.
3. (부수) 스트림 180초 상한이 어느 층의 정책인지, 그리고 4.7 에서 `message_start` 뒤 무응답으로
   닫힌 판(9-9 15:57~15:59 · 클라이언트 Claude Code 2.1.266)의 서버 쪽 기록을 확인해 주실 수 있는지.

## 재현 방법

인증 헤더만 바꾸면 그대로 돕니다. 두 요청의 `usage.output_tokens` 를 견주면 1·2 가 보이고, 스트림에서
`thinking` 이벤트가 없는 것으로 3 이 보입니다.

```bash
# Opus 5 · 설정 없음 — 생각이 기본으로 켜져 output_tokens 가 글자 수보다 훨씬 큽니다
curl -sN http://aigpt.posco.net/gpgpta01-gpt/v1/messages \
  -H 'content-type: application/json' -H 'anthropic-version: 2023-06-01' -H 'x-api-key: <키>' \
  -d '{"model":"claude-opus-5","max_tokens":1024,"stream":true,
       "messages":[{"role":"user","content":"1부터 100까지의 정수 가운데 3 또는 5의 배수의 합, 그리고 그 수들 가운데 7의 배수인 것의 개수. 풀이 없이 답만 두 줄로."}]}'

# Opus 5 · thinking disabled — 공식 API 에서는 생각이 꺼져야 하는데 위와 같은 output_tokens 가 옵니다
curl -sN http://aigpt.posco.net/gpgpta01-gpt/v1/messages \
  -H 'content-type: application/json' -H 'anthropic-version: 2023-06-01' -H 'x-api-key: <키>' \
  -d '{"model":"claude-opus-5","max_tokens":1024,"stream":true,
       "thinking":{"type":"disabled"},"output_config":{"effort":"high"},
       "messages":[{"role":"user","content":"1부터 100까지의 정수 가운데 3 또는 5의 배수의 합, 그리고 그 수들 가운데 7의 배수인 것의 개수. 풀이 없이 답만 두 줄로."}]}'
```

## 저희 쪽에서 한 것

Opus 5 로 긴 요청이 나가지 않도록 앱에서 그 모델 선택을 막아 두었고, 게이트웨이가 바뀌면 설정 하나로
다시 엽니다. 측정에 쓴 스크립트와 원본 응답은 보관하고 있어 필요하시면 드립니다.
