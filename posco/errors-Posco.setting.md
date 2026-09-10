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

P002
400
요청 검증
요청한 모델을 찾을 수 없습니다
▾

P003
502
프로바이더 응답
LLM 서비스 응답 오류
▾

P004
400
요청 검증
요청 형식이 올바르지 않습니다
▾

P005
400
요청 검증
이 프로바이더는 요청한 API 형식을 지원하지 않습니다
▾

P099
500
서버 내부
서버 내부 오류
Enum Pending
▾

C040
400
요청 검증
유효하지 않은 채팅 요청입니다
▾

C042
400
요청 검증
호출할 수 없는 모델입니다. 모델명을 다시 확인해주세요
▾

C043
400
요청 검증
해당 모델은 사용 기간이 만료되었습니다
▾

C044
400
요청 검증
messages는 필수 항목입니다
▾

C045
400
요청 검증
지원하지 않는 LLM 프로바이더입니다
▾

C046
400
요청 검증
업무GPT 카테고리가 명시되어야 합니다
▾

C090
500
서버 내부
GPT API 호출 중 오류가 발생했습니다
▾

C091
500
서버 내부
RAG 검색 중 오류가 발생했습니다
▾

C051
400
스트리밍
AI 안전 정책에 의해 차단되었습니다
▾

C052
400
스트리밍
대화 내용이 너무 길어 처리할 수 없습니다
▾

C053
429
Rate Limit
요청이 너무 많습니다. 잠시 후 다시 시도해주세요
▾

C054
500
스트리밍
AI 에이전트 처리 중 오류가 발생했습니다
▾

C055
504
스트리밍
AI 에이전트 응답 시간이 초과되었습니다
▾

G011
400
요청 검증
category 는 필수입니다
▾

G012
400
요청 검증
등록된 category 와 일치하지 않습니다
Deprecated
▾

G013
400
인증/권한
해당 category 접근 권한이 없습니다
▾

K041
403
인증/권한
해당 API Key 타입으로는 이 기능을 사용할 수 없습니다
▾

E001
400
요청 검증
잘못된 입력 값입니다
▾

E003
500
서버 내부
서버 내부 오류가 발생했습니다
▾
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
POST /gptApi/personalEmbeddingApi				

참고사항
Anthropic Messages 포맷에는 P-GPT 코드가 없습니다.
POST /v1/messages 응답은 error.type(invalid_request_error 등)과 error.message 만 사용합니다. 코드 기반 분기가 필요하면 POST /v1/chat/completions 또는 POST /v1/responses 로 호출하세요.

프로바이더 패스스루.
Gemini Native(/v1beta/...) 와 sLLM Native(/sllm) 응답은 LLM 프로바이더(Vertex AI / Qwen)가 반환한 원본 에러 body 를 그대로 패스스루할 수 있습니다. 이 경우 P-GPT 카탈로그가 아닌 프로바이더 공식 문서를 참조하세요.

P099 폴백 코드.
LlmApiExceptionHandler 의 일반 Exception 폴백은 현재 enum 미등록 상태로 하드코딩된 P099 를 반환합니다. 백엔드에서 enum 정식화 PR 이 별도로 진행되며, 본 페이지는 머지 후 함께 갱신됩니다.

다국어(영문 메시지).
현재 카탈로그는 한글 메시지만 노출합니다. 영문 메시지 i18n 은 별도 티켓으로 분리되어 있습니다.


에러 코드
P-GPT API 는 호출한 엔드포인트에 따라 OpenAI / Anthropic / ApiResponse / SSE 4가지 응답 포맷 중 하나로 에러를 반환합니다. 응답 포맷은 표준화되어 있지만, 응답 body 의 code 필드에는 P-GPT 내부 에러 코드(예: C046)가 그대로 노출됩니다 — 즉 "포맷 wrap, 코드 패스스루" 방식입니다.

응답 포맷
응답 포맷은 호출한 컨트롤러에 의해 결정됩니다. Anthropic Messages 응답에는 P-GPT 코드가 포함되지 않으니 주의하세요.

Native API 에러 (OpenAI envelope)
Anthropic Messages
ApiResponse (Legacy)
SSE error event
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

P002
400
요청 검증
요청한 모델을 찾을 수 없습니다
▾

P003
502
프로바이더 응답
LLM 서비스 응답 오류
▾

P004
400
요청 검증
요청 형식이 올바르지 않습니다
▾

P005
400
요청 검증
이 프로바이더는 요청한 API 형식을 지원하지 않습니다
▾

P099
500
서버 내부
서버 내부 오류
Enum Pending
▾

C040
400
요청 검증
유효하지 않은 채팅 요청입니다
▾

C042
400
요청 검증
호출할 수 없는 모델입니다. 모델명을 다시 확인해주세요
▾

C043
400
요청 검증
해당 모델은 사용 기간이 만료되었습니다
▾

C044
400
요청 검증
messages는 필수 항목입니다
▾

C045
400
요청 검증
지원하지 않는 LLM 프로바이더입니다
▾

C046
400
요청 검증
업무GPT 카테고리가 명시되어야 합니다
▾

C090
500
서버 내부
GPT API 호출 중 오류가 발생했습니다
▾

C091
500
서버 내부
RAG 검색 중 오류가 발생했습니다
▾

C051
400
스트리밍
AI 안전 정책에 의해 차단되었습니다
▾

C052
400
스트리밍
대화 내용이 너무 길어 처리할 수 없습니다
▾

C053
429
Rate Limit
요청이 너무 많습니다. 잠시 후 다시 시도해주세요
▾

C054
500
스트리밍
AI 에이전트 처리 중 오류가 발생했습니다
▾

C055
504
스트리밍
AI 에이전트 응답 시간이 초과되었습니다
▾

G011
400
요청 검증
category 는 필수입니다
▾

G012
400
요청 검증
등록된 category 와 일치하지 않습니다
Deprecated
▾

G013
400
인증/권한
해당 category 접근 권한이 없습니다
▾

K041
403
인증/권한
해당 API Key 타입으로는 이 기능을 사용할 수 없습니다
▾

E001
400
요청 검증
잘못된 입력 값입니다
▾

E003
500
서버 내부
서버 내부 오류가 발생했습니다
▾
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

에러 코드
P-GPT API 는 호출한 엔드포인트에 따라 OpenAI / Anthropic / ApiResponse / SSE 4가지 응답 포맷 중 하나로 에러를 반환합니다. 응답 포맷은 표준화되어 있지만, 응답 body 의 code 필드에는 P-GPT 내부 에러 코드(예: C046)가 그대로 노출됩니다 — 즉 "포맷 wrap, 코드 패스스루" 방식입니다.

응답 포맷
응답 포맷은 호출한 컨트롤러에 의해 결정됩니다. Anthropic Messages 응답에는 P-GPT 코드가 포함되지 않으니 주의하세요.

Native API 에러 (OpenAI envelope)
Anthropic Messages
ApiResponse (Legacy)
SSE error event
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

P002
400
요청 검증
요청한 모델을 찾을 수 없습니다
▾

P003
502
프로바이더 응답
LLM 서비스 응답 오류
▾

P004
400
요청 검증
요청 형식이 올바르지 않습니다
▾

P005
400
요청 검증
이 프로바이더는 요청한 API 형식을 지원하지 않습니다
▾

P099
500
서버 내부
서버 내부 오류
Enum Pending
▾

C040
400
요청 검증
유효하지 않은 채팅 요청입니다
▾

C042
400
요청 검증
호출할 수 없는 모델입니다. 모델명을 다시 확인해주세요
▾

C043
400
요청 검증
해당 모델은 사용 기간이 만료되었습니다
▾

C044
400
요청 검증
messages는 필수 항목입니다
▾

C045
400
요청 검증
지원하지 않는 LLM 프로바이더입니다
▾

C046
400
요청 검증
업무GPT 카테고리가 명시되어야 합니다
▾

C090
500
서버 내부
GPT API 호출 중 오류가 발생했습니다
▾

C091
500
서버 내부
RAG 검색 중 오류가 발생했습니다
▾

C051
400
스트리밍
AI 안전 정책에 의해 차단되었습니다
▾

C052
400
스트리밍
대화 내용이 너무 길어 처리할 수 없습니다
▾

C053
429
Rate Limit
요청이 너무 많습니다. 잠시 후 다시 시도해주세요
▾

C054
500
스트리밍
AI 에이전트 처리 중 오류가 발생했습니다
▾

C055
504
스트리밍
AI 에이전트 응답 시간이 초과되었습니다
▾

G011
400
요청 검증
category 는 필수입니다
▾

G012
400
요청 검증
등록된 category 와 일치하지 않습니다
Deprecated
▾

G013
400
인증/권한
해당 category 접근 권한이 없습니다
▾

K041
403
인증/권한
해당 API Key 타입으로는 이 기능을 사용할 수 없습니다
▾

E001
400
요청 검증
잘못된 입력 값입니다
▾

E003
500
서버 내부
서버 내부 오류가 발생했습니다
▾
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

에러 코드
P-GPT API 는 호출한 엔드포인트에 따라 OpenAI / Anthropic / ApiResponse / SSE 4가지 응답 포맷 중 하나로 에러를 반환합니다. 응답 포맷은 표준화되어 있지만, 응답 body 의 code 필드에는 P-GPT 내부 에러 코드(예: C046)가 그대로 노출됩니다 — 즉 "포맷 wrap, 코드 패스스루" 방식입니다.

응답 포맷
응답 포맷은 호출한 컨트롤러에 의해 결정됩니다. Anthropic Messages 응답에는 P-GPT 코드가 포함되지 않으니 주의하세요.

Native API 에러 (OpenAI envelope)
Anthropic Messages
ApiResponse (Legacy)
SSE error event
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

P002
400
요청 검증
요청한 모델을 찾을 수 없습니다
▾

P003
502
프로바이더 응답
LLM 서비스 응답 오류
▾

P004
400
요청 검증
요청 형식이 올바르지 않습니다
▾

P005
400
요청 검증
이 프로바이더는 요청한 API 형식을 지원하지 않습니다
▾

P099
500
서버 내부
서버 내부 오류
Enum Pending
▾

C040
400
요청 검증
유효하지 않은 채팅 요청입니다
▾

C042
400
요청 검증
호출할 수 없는 모델입니다. 모델명을 다시 확인해주세요
▾

C043
400
요청 검증
해당 모델은 사용 기간이 만료되었습니다
▾

C044
400
요청 검증
messages는 필수 항목입니다
▾

C045
400
요청 검증
지원하지 않는 LLM 프로바이더입니다
▾

C046
400
요청 검증
업무GPT 카테고리가 명시되어야 합니다
▾

C090
500
서버 내부
GPT API 호출 중 오류가 발생했습니다
▾

C091
500
서버 내부
RAG 검색 중 오류가 발생했습니다
▾

C051
400
스트리밍
AI 안전 정책에 의해 차단되었습니다
▾

C052
400
스트리밍
대화 내용이 너무 길어 처리할 수 없습니다
▾

C053
429
Rate Limit
요청이 너무 많습니다. 잠시 후 다시 시도해주세요
▾

C054
500
스트리밍
AI 에이전트 처리 중 오류가 발생했습니다
▾

C055
504
스트리밍
AI 에이전트 응답 시간이 초과되었습니다
▾

G011
400
요청 검증
category 는 필수입니다
▾

G012
400
요청 검증
등록된 category 와 일치하지 않습니다
Deprecated
▾

G013
400
인증/권한
해당 category 접근 권한이 없습니다
▾

K041
403
인증/권한
해당 API Key 타입으로는 이 기능을 사용할 수 없습니다
▾

E001
400
요청 검증
잘못된 입력 값입니다
▾

E003
500
서버 내부
서버 내부 오류가 발생했습니다
▾
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
