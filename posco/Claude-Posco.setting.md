Messages API (Anthropic)
Anthropic Messages API 호환 엔드포인트입니다. Claude CLI(Claude Code), Anthropic SDK 등 Anthropic 형식의 클라이언트에서 P-GPT를 통해 AWS Bedrock Claude 모델을 호출할 수 있습니다.

Anthropic 공식 문서: Messages API Reference ↗

P-GPT는 프록시 방식으로 동작하므로, 실제 요청은 AWS Bedrock Converse API로 변환되어 처리됩니다. Anthropic 공식 API와 일부 차이가 있을 수 있습니다.

POST
/v1/messages
Headers
Name	Required	Description
x-api-key	Required*	P-GPT API Key. Authorization: Bearer 헤더와 택 1 사용.
Authorization	Required*	Bearer YOUR_API_KEY 형식. x-api-key 헤더와 택 1 사용.
anthropic-version	Optional	API 버전. 기본값: 2023-06-01
content-type	Required	application/json
Request Body
Name	Type	Required	Description
model	string	Required	사용할 모델 ID (예: claude-sonnet-4.5). P-GPT에 등록된 Claude 모델만 사용 가능합니다.
messages	array	Required	메시지 배열. 각 메시지는 role("user", "assistant")과 content(문자열 또는 content block 배열)를 포함합니다.
max_tokens	integer	Required	응답에서 생성할 최대 토큰 수.
system	string | array	Optional	시스템 프롬프트. 문자열 또는 content block 배열.
stream	boolean	Optional	SSE 스트리밍 응답 여부. 기본값: false
temperature	number	Optional	샘플링 온도 (0~1). 기본값: 1
top_p	number	Optional	Top-p (nucleus) 샘플링.
top_k	integer	Optional	Top-k 샘플링. 상위 k개의 토큰만 고려합니다.
stop_sequences	array	Optional	생성을 중지할 문자열 배열.
tools	array	Optional	모델이 호출할 수 있는 도구 목록. 각 도구는 name, description, input_schema를 포함합니다.
tool_choice	object	Optional	도구 호출 방식. {"type":"auto"}, {"type":"any"}, {"type":"tool","name":"..."}
metadata	object	Optional	요청 메타데이터. user_id 필드가 감사 로그에 기록됩니다.
Response
Name	Type	Description
id	string	응답 고유 ID (msg_ 접두사)
type	string	"message"
role	string	"assistant"
model	string	사용된 모델 ID
content	array	응답 content block 배열. {"type":"text","text":"..."} 또는 {"type":"tool_use","id":"...","name":"...","input":{...}}
stop_reason	string	종료 사유: end_turn, tool_use, max_tokens, stop_sequence
usage	object	토큰 사용량 (input_tokens, output_tokens)
Streaming (SSE)
stream: true로 요청하면 Server-Sent Events 형식으로 응답합니다. 각 이벤트는 event:와 data: 줄로 구성됩니다.

Event	Description
message_start	스트림 시작. 메시지 메타데이터(id, model, usage.input_tokens) 포함.
content_block_start	content block 시작. index와 content_block 타입 포함.
content_block_delta	텍스트 또는 도구 입력 증분. text_delta 또는 input_json_delta.
content_block_stop	content block 종료.
message_delta	메시지 종료 정보. stop_reason과 usage.output_tokens 포함.
message_stop	스트림 완전 종료.
Tool Use
모델에 도구를 정의하면 적절한 시점에 도구 호출을 요청합니다. 응답의 stop_reason이 "tool_use"이면 content 배열에 tool_use 블록이 포함됩니다. 도구 실행 후 tool_result 블록으로 결과를 전달하여 최종 응답을 받습니다.

이미지 입력 (Multimodal)
메시지의 content에 image 타입 블록을 포함하여 이미지를 전송할 수 있습니다. base64 인코딩(source.type: "base64")을 지원하며, image/jpeg, image/png, image/gif, image/webp 형식을 지원합니다.

curl
Python
Node.js

from anthropic import Anthropic

client = Anthropic(
    api_key="YOUR_API_KEY",
    base_url="http://{host}/gpgpta01-gpt" )  # 일반 응답
response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[         {"role": "user", "content": "P-GPT API에 대해 알려주세요."}     ] )  print(response.content[0].text)  # 스트리밍 응답 with client.messages.stream(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[         {"role": "user", "content": "안녕하세요!"}     ] ) as stream:     for text in stream.text_stream:         print(text, end="")
Response

{   "id": "msg_01XFDUDYJgAACzvnptvVoYEL",   "type": "message",   "role": "assistant",   "model": "claude-sonnet-4.5",   "content": [     {       "type": "text",       "text": "P-GPT API는 포스코그룹에서 LLM을 활용하기 위해 제공하는..."     }   ],   "stop_reason": "end_turn",   "usage": {     "input_tokens": 25,     "output_tokens": 150   } }
Streaming Response

event: message_start
data: {"type":"message_start","message":{"id":"msg_01...","type":"message","role":"assistant","model":"claude-sonnet-4.5","content":[],"usage":{"input_tokens":25}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"P-GPT"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" API는"}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":150}}

event: message_stop
data: {"type":"message_stop"}
Tool Use
curl
Python
Node.js

import json
from anthropic import Anthropic

client = Anthropic(
    api_key="YOUR_API_KEY",
    base_url="http://{host}/gpgpta01-gpt" )

tools = [     {         "name": "get_weather",         "description": "지정한 도시의 현재 날씨를 조회합니다.",         "input_schema": {             "type": "object",             "properties": {                 "city": {"type": "string", "description": "도시명"}             },             "required": ["city"]         }     } ]  # 1단계: 도구와 함께 요청
response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "서울 날씨 어때?"}] )  # 2단계: tool_use가 있으면 실행 후 결과 전달 if response.stop_reason == "tool_use":
    tool_block = next(b for b in response.content if b.type == "tool_use")
    result = json.dumps({"temp": 22, "condition": "맑음"})

    final = client.messages.create(
        model="claude-sonnet-4.5",
        max_tokens=1024,
        tools=tools,
        messages=[             {"role": "user", "content": "서울 날씨 어때?"},             {"role": "assistant", "content": response.content},             {"role": "user", "content": [                 {"type": "tool_result", "tool_use_id": tool_block.id, "content": result}             ]}         ]     )     print(final.content[0].text)
Tool Use Response

{   "id": "msg_01XFDUDYJgAACzvnptvVoYEL",   "type": "message",   "role": "assistant",   "model": "claude-sonnet-4.5",   "content": [     {       "type": "text",       "text": "날씨를 확인해보겠습니다."     },     {       "type": "tool_use",       "id": "toolu_01A09q90qw90lq917835lq9",       "name": "get_weather",       "input": {"city": "Seoul"}     }   ],   "stop_reason": "tool_use",   "usage": {     "input_tokens": 85,     "output_tokens": 42   } }
이미지 입력 (Multimodal)
content 배열에 {"type":"image"} 블록을 넣고 source에 접두사 없는 순수 Base64와 media_type을 지정합니다. (OpenAI처럼 data: 접두사를 붙이지 않습니다.)

curl
Python

import base64
from anthropic import Anthropic

client = Anthropic(api_key="YOUR_API_KEY", base_url="http://{host}/gpgpta01-gpt")  with open("photo.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")   # 순수 Base64 (접두사 없음)

response = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[{         "role": "user",         "content": [             {"type": "text", "text": "이 이미지를 설명해줘."},             {"type": "image", "source": {                 "type": "base64", "media_type": "image/png", "data": b64,   # JPG면 image/jpeg             }},         ],     }], )  print(response.content[0].text)

Claude CLI 연동
P-GPT는 Anthropic Messages API 호환 엔드포인트(/v1/messages)를 제공하므로, Claude CLI(Claude Code)를 P-GPT에 연결하여 사내 AWS Bedrock Claude 모델을 사용할 수 있습니다. P-GPT 에서 발급받은 API Key 하나로 별도 추가 자격증명 없이 연동됩니다.

POST
/v1/messages
개요
Claude CLI(Claude Code)는 Anthropic의 터미널 기반 코딩 에이전트로, 자연어 명령을 코드 변경으로 변환합니다. P-GPT가 Anthropic Messages API와 호환되는 /v1/messages 엔드포인트를 제공하므로, Claude CLI를 P-GPT 프록시를 통해 그대로 사용할 수 있습니다.

Messages API — /v1/messages 엔드포인트로 Claude 모델과 대화합니다.
SSE 스트리밍 — 실시간 스트리밍 응답을 지원합니다.
Tool Use — Claude Code의 도구 호출(파일 읽기/쓰기, 셸 실행 등)을 지원합니다.
API Key 관리 — P-GPT에서 발급한 API Key를 사용합니다.
인증
Claude CLI는 Anthropic 표준 인증 방식을 사용합니다.

방식	설정	설명
x-api-key	x-api-key: YOUR_API_KEY	Anthropic 표준 API Key 헤더. Claude CLI가 자동으로 설정합니다.
환경변수	ANTHROPIC_API_KEY=YOUR_API_KEY	Claude CLI가 자동으로 읽는 환경변수입니다. P-GPT API Key를 설정합니다.
Claude CLI 설정 방법
Claude CLI에서 P-GPT를 사용하려면 환경변수를 설정합니다.

P-GPT API Key 발급 — "P-GPT API 신청" 메뉴에서 API Key를 발급받습니다.
Claude CLI 설치 — npm install -g @anthropic-ai/claude-code
환경변수 설정 — ANTHROPIC_API_KEY와 ANTHROPIC_BASE_URL을 설정합니다.
Claude CLI 실행 — claude 명령으로 CLI를 시작합니다.
커스텀 설정 항목
P-GPT에 연결하기 위해 반드시 변경해야 하는 설정 항목입니다.

항목	설정 위치	값	설명
ANTHROPIC_API_KEY	환경변수	P-GPT에서 발급받은 API Key	Claude CLI가 x-api-key 헤더로 전송합니다. Anthropic API Key가 아닌 P-GPT API Key를 입력해야 합니다.
ANTHROPIC_BASE_URL	환경변수	http://{host}/gpgpta01-gpt	Claude CLI의 API 요청 대상 URL. 기본값(https://api.anthropic.com)을 P-GPT 주소로 변경해야 합니다. /v1을 포함하지 않습니다 (Claude CLI가 자동으로 /v1/messages를 붙입니다).
--model	CLI 옵션	claude-sonnet-4.5 등	(선택) 사용할 모델 지정. P-GPT에 등록된 Claude 모델만 사용 가능합니다.
주의: ANTHROPIC_BASE_URL의 프로토콜은 http://입니다. 사내 환경에서는 https://가 아닌 http://를 사용해야 정상 연결됩니다. 또한 Codex CLI와 달리 URL 끝에 /v1을 포함하지 않습니다.
환경별 URL
환경	ANTHROPIC_BASE_URL
개발계	http://taigpt.posco.net/gpgpta01-gpt
운영계	http://aigpt.posco.net/gpgpta01-gpt
주요 Claude CLI 옵션
옵션	설명	예시
--model	사용할 모델 지정	claude --model claude-sonnet-4.5
--allowedTools	허용할 도구 지정	claude --allowedTools "Edit,Bash(read-only)"
-p	비대화형 모드 (단일 프롬프트 실행, 결과 출력)	claude -p "이 함수를 설명해줘"
--verbose	상세 로그 출력 (디버깅용)	claude --verbose
지원 모델
P-GPT 게이트웨이가 라우팅하는 Claude 모델은 GET /v1/models 응답에서 확인할 수 있습니다. 현재 지원 모델:

모델 ID	설명
claude-sonnet-4.5	Sonnet 4.5 — 균형 잡힌 성능/속도 (Claude CLI 기본 권장)
claude-sonnet-4.6	Sonnet 4.6 — Sonnet 계열 최신
claude-opus-4.5	Opus 4.5 — 고난도 추론
claude-opus-4.6	Opus 4.6 — 고난도 추론
claude-opus-4.7	Opus 4.7 — Opus 계열 최신
트러블슈팅
증상	원인	해결
API Error: 401 / "API Key가 제공되지 않았습니다"	ANTHROPIC_API_KEY 미설정 또는 잘못된 값	환경변수 확인. Anthropic API Key 가 아닌 P-GPT 발급 키 사용. CLI 재시작 후 재시도
API Error: 400 / "모델을 찾을 수 없습니다"	모델 ID 가 P-GPT 등록 목록에 없음	--model 값을 지원 모델 표의 정확한 ID로 변경 (예: claude-sonnet-4.5)
응답 hang / 연결 실패	ANTHROPIC_BASE_URL 오설정 — /v1 포함, https:// 사용, 경로 끝 슬래시 등	정확히 http://{host}/gpgpta01-gpt 형태로 설정. /v1 미포함, http:// 사용
OAuth 로그인 화면이 뜸	Claude CLI 가 환경변수를 못 읽고 OAuth flow 진입	현재 셸에서 echo $ANTHROPIC_API_KEY 로 노출 확인. 영구 설정 후 새 셸 사용 권장

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


{   "type": "error",   "error": {     "type": "invalid_request_error",     "message": "messages는 필수 항목입니다."   } }
에러 코드 카탈로그
외부 API 에서 발생 가능한 코드 약 21개입니다. 코드/메시지/enum 이름으로 검색하거나 카테고리로 필터링할 수 있습니다. 각 코드를 클릭하면 일반적 원인과 권장 해결 방안이 표시됩니다.

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
ENUM PENDING
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
ENUM
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
ENUM
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
ENUM
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
ENUM
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
ENUM
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

G012
400
요청 검증
등록된 category 와 일치하지 않습니다
DEPRECATED
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
POST /v1/chat/completions	●	
 

 

●	●	
 

●	●	●	
 

 

 

 

 

 

 

 

 

●	●	●	●	
 

●
POST /v1/embeddings	
 

 

 

 

●	
 

 

 

 

 

 

 

 

 

 

 

 

 

●	●	●	●	
 

●
GET /v1/models	
 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

●	
 

 

 

 

●
POST /v1/responses	
 

 

 

 

●	
 

 

 

 

 

 

 

 

 

 

 

 

 

●	●	●	●	
 

●
POST /v1/messages	●	
 

 

●	●	
 

●	●	●	
 

 

 

 

 

 

 

 

 

●	●	●	●	●	●
POST /agent	●	
 

 

●	
 

 

●	●	●	●	●	●	
 

 

 

●	●	
 

●	
 

●	
 

 

●
GET /agent/list	
 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

●	
 

 

 

 

●
POST /v1beta/.../:generateContent	
 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

●	●	●	●	
 

●
POST /sllm	
 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

●	●	●	●	
 

●
POST /gptApi/personalApi	
 

●	●	
 

 

 

 

 

 

 

 

●	
 

●	●	
 

 

●	
 

 

 

 

 

 

POST /gptApi/personalRagApi	
 

●	●	
 

 

●	
 

 

 

 

 

●	●	●	●	
 

 

●	
 

 

 

 

 

 

POST /gptApi/personalEmbeddingApi	
 

 

 

 

 

 

 

 

 

 

 

 

 

●	●	
 

 

●	
 

 

 

 

 

 

참고사항
Anthropic Messages 포맷에는 P-GPT 코드가 없습니다.
POST /v1/messages 응답은 error.type(invalid_request_error 등)과 error.message 만 사용합니다. 코드 기반 분기가 필요하면 POST /v1/chat/completions 또는 POST /v1/responses 로 호출하세요.

 
