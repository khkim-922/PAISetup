에러 코드
P-GPT API 는 호출한 엔드포인트에 따라 OpenAI / Anthropic / ApiResponse / SSE 4가지 응답 포맷 중 하나로 에러를 반환합니다. 응답 포맷은 표준화되어 있지만, 응답 body 의 code 필드에는 P-GPT 내부 에러 코드(예: C046)가 그대로 노출됩니다 — 즉 "포맷 wrap, 코드 패스스루" 방식입니다.

응답 포맷
응답 포맷은 호출한 컨트롤러에 의해 결정됩니다. Anthropic Messages 응답에는 P-GPT 코드가 포함되지 않으니 주의하세요.

Native API 에러 (OpenAI envelope)
Anthropic Messages
ApiResponse (Legacy)
SSE error event
LlmApiExceptionHandler 가 controller.api 패키지의 모든 Native API 컨트롤러(Chat Completions / Responses / Embeddings / Models / Agent / Gemini Native / sLLM Native)에 일괄 적용됩니다. 호출한 엔드포인트의 성공 응답 포맷(Gemini-native 등)과 무관하게 에러는 이 OpenAI envelope 으로 통일되며, error.code 필드에 P-GPT 내부 코드(예: C046) 가 그대로 노출됩니다.

적용 컨트롤러:
POST /v1/chat/completions
POST /v1/embeddings
GET /v1/models
POST /v1/responses
POST /agent
POST /v1beta/.../:generateContent
POST /sllm
type 은 HTTP status 에 따라 자동 매핑됩니다 (401 → authentication_error, 4xx → invalid_request_error, 5xx → server_error). Gemini Native 도 성공 응답은 Gemini 포맷이지만 에러는 본 envelope 으로 반환되므로 클라이언트는 OpenAI 스타일 에러 분기를 함께 구현해야 합니다.


{
  "error": {
    "message": "업무GPT 카테고리가 명시되어야 합니다.",
    "type": "invalid_request_error",
    "code": "C046"
  }
}


AnthropicExceptionHandler(@Order 0)가 LlmApiMessagesController 전용으로 적용됩니다. 응답 body 에 P-GPT 내부 코드(예: C046)는 포함되지 않으며, error.type 과 error.message 만 사용합니다.

적용 컨트롤러:
POST /v1/messages
⚠ Messages API 에는 P-GPT 코드(P001/C046 등)가 포함되지 않습니다. 코드 기반 분기가 필요하면 Chat Completions(/v1/chat/completions)를 사용하세요.


{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "messages는 필수 항목입니다."
  }
}

GlobalExceptionHandler 가 ApiController(/gptApi/*) 응답에 사용합니다. success/data/error/timestamp 4-필드 envelope 입니다.

적용 컨트롤러:
POST /gptApi/personalApi
POST /gptApi/personalRagApi
POST /gptApi/personalEmbeddingApi
Legacy 경로 전용입니다. 신규 통합은 Native /v1/* 사용을 권장합니다.


{
  "success": false,
  "data": null,
  "error": {
    "code": "C046",
    "message": "업무GPT 카테고리가 명시되어야 합니다.",
    "details": "category is null"
  },
  "timestamp": "2026-05-15T10:00:00"
}


SseExceptionHandler 가 스트리밍 도중 발생한 에러를 HTTP 200 + event:error 프레임으로 전달합니다.

적용 컨트롤러:
POST /agent (stream)
POST /v1/messages (stream)
/chat/** SSE
SSE 채널이 이미 열려 있으므로 HTTP status 는 200 입니다. data JSON 의 code 필드로 분기하세요.


event:error
data:{"code":"C054","message":"AI 에이전트 처리 중 오류가 발생했습니다","detail":"upstream timeout"}



에러 코드 카탈로그
외부 API 에서 발생 가능한 코드 약 21개입니다. 코드/메시지/enum 이름으로 검색하거나 카테고리로 필터링할 수 있습니다. 각 코드를 클릭하면 일반적 원인과 권장 해결 방안이 표시됩니다.

코드, 메시지, enum 이름 검색...
전체
인증/권한
요청 검증
스트리밍
Rate Limit
프로바이더 응답
서버 내부
25개 / 전체 25개

P001
401
인증/권한
유효하지 않은 API Key입니다
▾
Enum
PROXY_INVALID_API_KEY
발생 위치
chat-completions embeddings models responses messages agent agent-list gemini-native sllm-native
일반적 원인
API Key 헤더(Authorization: Bearer 또는 x-api-key) 누락, UUID 형식 오류, DB 미존재, 회사코드 불일치 중 하나로 JwtVerificationFilter 가 인증 거절했습니다.
해결 방안
P-GPT 포털에서 발급받은 정상 API Key 를 Authorization 헤더(Bearer) 또는 x-api-key 헤더로 전달하세요. Key 가 비활성화/회수되지 않았는지도 확인하세요.
참조
ErrorCode.java:208

P002
400
요청 검증
요청한 모델을 찾을 수 없습니다
▾
Enum
PROXY_MODEL_NOT_FOUND
발생 위치
chat-completions embeddings responses messages agent gemini-native sllm-native
일반적 원인
회사 LLM 설정(LlmConfigResolver)에 등록되지 않은 모델 이름입니다.
해결 방안
GET /v1/models 로 사용 가능한 모델 목록을 먼저 확인한 뒤 요청하세요.
참조
ErrorCode.java:209

P003
502
프로바이더 응답
LLM 서비스 응답 오류
▾
Enum
PROXY_UPSTREAM_ERROR
발생 위치
chat-completions embeddings responses messages agent gemini-native sllm-native
일반적 원인
백엔드 → LLM 프로바이더(OpenAI/Bedrock/Vertex/Qwen) 호출 단계에서 오류가 발생했습니다. LlmApiExceptionHandler 의 ApiException 폴백 코드입니다.
해결 방안
잠시 후 재시도하세요. 지속되면 P-GPT 운영팀에 문의하세요. provider 응답 body 가 첨부될 수 있으니 detail 필드를 확인하세요.
참조
ErrorCode.java:210

P004
400
요청 검증
요청 형식이 올바르지 않습니다
▾
Enum
PROXY_INVALID_REQUEST
발생 위치
chat-completions embeddings responses messages agent gemini-native sllm-native
일반적 원인
요청 본문의 JSON 파싱 실패, 필수 필드 누락, 또는 sLLM 요청 시 X-MODEL-NAME 헤더 누락.
해결 방안
엔드포인트 별 Request 스키마를 다시 확인하세요. sLLM 호출 시 X-MODEL-NAME 헤더를 반드시 포함하세요.
참조
ErrorCode.java:211

P005
400
요청 검증
이 프로바이더는 요청한 API 형식을 지원하지 않습니다
▾
Enum
UNSUPPORTED_API_FORMAT
발생 위치
messages
일반적 원인
Messages API(Anthropic 포맷)는 일부 프로바이더(예: 비-Bedrock)에서 지원되지 않습니다.
해결 방안
Bedrock/Anthropic 호환 모델을 사용하거나, Chat Completions(/v1/chat/completions) 또는 Responses(/v1/responses) 엔드포인트로 전환하세요.
참조
ErrorCode.java:212

P099
500
서버 내부
서버 내부 오류
Enum Pending
▾
Enum
(미정의 — 핸들러 하드코딩)
발생 위치
chat-completions embeddings responses messages agent gemini-native sllm-native
일반적 원인
LlmApiExceptionHandler 의 일반 Exception 폴백 코드. 현재 enum 에 정식 등록되어 있지 않습니다.
해결 방안
이 코드를 받았다면 detail 메시지와 요청 시각을 첨부해 P-GPT 운영팀에 문의하세요. 백엔드에서 enum 정식화 PR 이 별도 진행 중입니다.
참조
LlmApiExceptionHandler.java (하드코딩, ErrorCode.java 미정의)

C040
400
요청 검증
유효하지 않은 채팅 요청입니다
▾
Enum
INVALID_CHAT_REQUEST
발생 위치
chat-completions agent messages
일반적 원인
채팅 요청 형식의 일반적 검증 실패.
해결 방안
messages 배열, role/content 필드, model 명을 다시 확인하세요.
참조
ErrorCode.java:88

C042
400
요청 검증
호출할 수 없는 모델입니다. 모델명을 다시 확인해주세요
▾
Enum
INVALID_MODEL
발생 위치
legacy-personal legacy-rag
일반적 원인
Legacy /gptApi/* 호출 시 사용자 회사에 허용되지 않은 모델명을 사용했습니다.
해결 방안
운영팀에 문의해 회사에 등록된 모델 목록을 확인하세요. 또는 Native /v1/* 엔드포인트로 전환을 검토하세요.
참조
ErrorCode.java:89

C043
400
요청 검증
해당 모델은 사용 기간이 만료되었습니다
▾
Enum
MODEL_EXPIRED
발생 위치
legacy-personal legacy-rag
일반적 원인
모델의 운영 기간이 만료되어 더 이상 호출할 수 없습니다.
해결 방안
운영팀이 안내하는 후속 모델로 교체하세요.
참조
ErrorCode.java:90

C044
400
요청 검증
messages는 필수 항목입니다
▾
Enum
MESSAGES_REQUIRED
발생 위치
chat-completions messages agent
일반적 원인
요청 본문에 messages 배열이 없거나 비어있습니다.
해결 방안
최소 하나 이상의 {role, content} 메시지를 포함하세요.
참조
ErrorCode.java:91

C045
400
요청 검증
지원하지 않는 LLM 프로바이더입니다
▾
Enum
UNSUPPORTED_LLM_PROVIDER
발생 위치
chat-completions embeddings responses messages
일반적 원인
model 명이 어떤 프로바이더에도 매핑되지 않습니다.
해결 방안
GET /v1/models 결과의 정확한 model id 를 사용하세요.
참조
ErrorCode.java:92

C046
400
요청 검증
업무GPT 카테고리가 명시되어야 합니다
▾
Enum
RAG_CATEGORY_REQUIRED
발생 위치
legacy-rag
일반적 원인
Legacy RAG (/gptApi/personalRagApi) 호출 시 category 파라미터가 없습니다.
해결 방안
회사 RAG 카테고리 키를 category 필드에 포함하세요.
참조
ErrorCode.java:93

C090
500
서버 내부
GPT API 호출 중 오류가 발생했습니다
▾
Enum
CHAT_API_ERROR
발생 위치
legacy-personal legacy-rag agent
일반적 원인
Legacy 경로에서 GPT/RAG 호출 중 예외 발생. GlobalExceptionHandler 의 ApiException 매핑.
해결 방안
잠시 후 재시도. 지속되면 운영팀에 detail 과 함께 문의하세요.
참조
ErrorCode.java:96

C091
500
서버 내부
RAG 검색 중 오류가 발생했습니다
▾
Enum
RAG_SEARCH_ERROR
발생 위치
legacy-rag
일반적 원인
벡터 검색 단계에서 오류가 발생했습니다.
해결 방안
잠시 후 재시도. 지속되면 운영팀에 문의하세요.
참조
ErrorCode.java:97

C051
400
스트리밍
AI 안전 정책에 의해 차단되었습니다
▾
Enum
CHAT_CONTENT_FILTERED
발생 위치
chat-completions messages agent
일반적 원인
입력 또는 응답이 LLM 안전 필터(Content filter)에 의해 차단되었습니다.
해결 방안
프롬프트에서 안전 정책 위반 가능성이 있는 표현을 제거하세요.
참조
ErrorCode.java:101

C052
400
스트리밍
대화 내용이 너무 길어 처리할 수 없습니다
▾
Enum
CHAT_CONTEXT_TOO_LONG
발생 위치
chat-completions messages agent
일반적 원인
입력 토큰 수가 모델의 context window 한도를 초과했습니다.
해결 방안
메시지 이력을 줄이거나 더 큰 context 의 모델로 전환하세요. RAG 사용 시 검색 청크 수를 조정하세요.
참조
ErrorCode.java:102

C053
429
Rate Limit
요청이 너무 많습니다. 잠시 후 다시 시도해주세요
▾
Enum
CHAT_RATE_LIMITED
발생 위치
chat-completions messages agent
일반적 원인
단위 시간당 요청량이 한도를 초과했습니다.
해결 방안
지수 backoff 로 재시도하세요. 지속적인 한도 초과 시 운영팀에 quota 상향을 문의하세요.
참조
ErrorCode.java:103

C054
500
스트리밍
AI 에이전트 처리 중 오류가 발생했습니다
▾
Enum
CHAT_AGENT_ERROR
발생 위치
agent
일반적 원인
SseExceptionHandler 의 기본 코드. Agent 스트림 처리 중 일반 예외.
해결 방안
detail 의 메시지를 확인하고 잠시 후 재시도하세요.
참조
ErrorCode.java:104

C055
504
스트리밍
AI 에이전트 응답 시간이 초과되었습니다
▾
Enum
CHAT_AGENT_TIMEOUT
발생 위치
agent
일반적 원인
Agent 응답이 타임아웃 한도(기본 ≥60초) 내에 완료되지 않았습니다.
해결 방안
입력을 줄이거나 streaming 으로 부분 응답을 받아 처리하세요. 지속되면 운영팀에 timeout 조정을 문의하세요.
참조
ErrorCode.java:105

G011
400
요청 검증
category 는 필수입니다
▾
Enum
AGENT_CATEGORY_REQUIRED
발생 위치
agent
일반적 원인
POST /agent 호출 시 category 필드가 없습니다.
해결 방안
발급받은 API Key 의 권한 범위에 해당하는 category 를 명시하세요.
참조
ErrorCode.java:115

G012
400
요청 검증
등록된 category 와 일치하지 않습니다
Deprecated
▾
Enum
AGENT_CATEGORY_MISMATCH
발생 위치
agent
일반적 원인
(Deprecated since 2.0) 과거 API Key 박힌 category 검증 코드. 현재는 throw 되지 않으나 외부 계약 호환성을 위해 enum 유지.
해결 방안
본 코드는 더 이상 발생하지 않습니다. 호환성 처리를 위해 클라이언트에서 무시 가능합니다.
참조
ErrorCode.java:118

G013
400
인증/권한
해당 category 접근 권한이 없습니다
▾
Enum
AGENT_CATEGORY_NOT_ALLOWED
발생 위치
agent
일반적 원인
요청한 category 가 API Key 의 허용 카테고리 목록에 포함되지 않습니다.
해결 방안
API Key 발급 시 허용된 category 만 사용하거나, 운영팀에 권한 추가를 요청하세요.
참조
ErrorCode.java:119

K041
403
인증/권한
해당 API Key 타입으로는 이 기능을 사용할 수 없습니다
▾
Enum
INVALID_API_KEY_TYPE
발생 위치
legacy-personal legacy-rag legacy-embedding
일반적 원인
Legacy /gptApi/* 는 특정 타입의 API Key 만 허용합니다.
해결 방안
신규 발급된 표준 API Key(Native /v1/* 호환)를 사용하거나, 운영팀에 Legacy 호환 Key 발급을 요청하세요.
참조
ErrorCode.java:170

E001
400
요청 검증
잘못된 입력 값입니다
▾
Enum
INVALID_INPUT_VALUE
발생 위치
legacy-personal legacy-rag legacy-embedding
일반적 원인
@Valid 검증 실패, JSON 파싱 실패(HttpMessageNotReadable), 또는 필수 파라미터 누락.
해결 방안
엔드포인트 별 Request 스키마와 Content-Type(application/json)을 다시 확인하세요.
참조
ErrorCode.java:29

E003
500
서버 내부
서버 내부 오류가 발생했습니다
▾
Enum
INTERNAL_SERVER_ERROR
발생 위치
legacy-personal legacy-rag legacy-embedding
일반적 원인
GlobalExceptionHandler 의 Exception 최종 폴백 (예: JsonProcessingRuntimeException).
해결 방안
잠시 후 재시도. 지속되면 timestamp 와 함께 운영팀에 문의하세요.
참조
ErrorCode.java:31
API 별 발생 가능 코드
각 엔드포인트에서 노출 가능한 코드를 한눈에 비교할 수 있는 매트릭스입니다. 포함된 코드는 일반적인 노출 사례 기준이며, 일부 폴백 코드(P099)는 enum 정식화 이전 상태입니다.

API	C040	C042	C043	C044	C045	C046	C051	C052	C053	C054	C055	C090	C091	E001	E003	G011	G013	K041	P001	P002	P003	P004	P005	P099
POST /v1/chat/completions	●			●	●		●	●	●										●	●	●	●		●
POST /v1/embeddings					●														●	●	●	●		●
GET /v1/models																			●					●
POST /v1/responses					●														●	●	●	●		●
POST /v1/messages	●			●	●		●	●	●										●	●	●	●	●	●
POST /agent	●			●			●	●	●	●	●	●				●	●		●		●			●
GET /agent/list																			●					●
POST /v1beta/.../:generateContent																			●	●	●	●		●
POST /sllm																			●	●	●	●		●
POST /gptApi/personalApi		●	●									●		●	●			●						
POST /gptApi/personalRagApi		●	●			●						●	●	●	●			●						
POST /gptApi/personalEmbeddingApi														●	●			●						
참고사항
Anthropic Messages 포맷에는 P-GPT 코드가 없습니다.
POST /v1/messages 응답은 error.type(invalid_request_error 등)과 error.message 만 사용합니다. 코드 기반 분기가 필요하면 POST /v1/chat/completions 또는 POST /v1/responses 로 호출하세요.

프로바이더 패스스루.
Gemini Native(/v1beta/...) 와 sLLM Native(/sllm) 응답은 LLM 프로바이더(Vertex AI / Qwen)가 반환한 원본 에러 body 를 그대로 패스스루할 수 있습니다. 이 경우 P-GPT 카탈로그가 아닌 프로바이더 공식 문서를 참조하세요.

P099 폴백 코드.
LlmApiExceptionHandler 의 일반 Exception 폴백은 현재 enum 미등록 상태로 하드코딩된 P099 를 반환합니다. 백엔드에서 enum 정식화 PR 이 별도로 진행되며, 본 페이지는 머지 후 함께 갱신됩니다.

다국어(영문 메시지).
현재 카탈로그는 한글 메시지만 노출합니다. 영문 메시지 i18n 은 별도 티켓으로 분리되어 있습니다.