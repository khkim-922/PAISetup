Chat Completions API (OpenAI)
주어진 대화 메시지 목록에 대해 모델의 응답을 생성합니다. OpenAI Chat Completions API와 호환됩니다.

OpenAI 공식 문서: Chat Completions API Reference ↗

P-GPT는 프록시 방식으로 동작하므로, 실제 Request Body와 Response 형식은 OpenAI 공식 문서와 다를 수 있습니다. 정확한 파라미터와 응답 구조는 위 공식 문서를 함께 참고해주세요.

POST
/v1/chat/completions
Request Body
Name	Type	Required	Description
model	string	Required	사용할 모델 ID (예: gpt-5.2, gpt-5.4-mini)
messages	array	Required	메시지 배열. 각 메시지는 role("system", "user", "assistant", "tool")과 content를 포함합니다.
stream	boolean	Optional	SSE 스트리밍 응답 여부. 기본값: false
stream_options	object | null	Optional	스트리밍 옵션. stream: true일 때만 유효합니다. {"include_usage": true}로 설정하면 마지막 chunk에 토큰 사용량이 포함됩니다.
temperature	number	Optional	샘플링 온도 (0~2). 높을수록 무작위성이 증가합니다. 기본값: 1
top_p	number	Optional	Top-p (nucleus) 샘플링 (0~1). temperature와 함께 사용하지 않는 것을 권장합니다. 기본값: 1
max_completion_tokens	integer | null	Optional	응답에서 생성할 최대 토큰 수. gpt-5.2에서는 legacy 출력 토큰 파라미터 대신 이 필드를 사용합니다.
n	integer	Optional	각 입력에 대해 생성할 응답 수 (1~128). 기본값: 1
stop	string | array	Optional	생성을 중지할 토큰. 문자열 또는 최대 4개의 문자열 배열. 해당 토큰이 나타나면 생성을 멈춥니다.
frequency_penalty	number	Optional	빈도 기반 페널티 (-2.0~2.0). 양수이면 이미 등장한 토큰의 반복을 줄입니다. 기본값: 0
presence_penalty	number	Optional	존재 기반 페널티 (-2.0~2.0). 양수이면 새로운 주제로 전환할 가능성이 높아집니다. 기본값: 0
seed	integer | null	Optional	재현성을 위한 시드 값. 같은 시드와 파라미터로 요청하면 동일한 결과를 반환하려고 시도합니다.
response_format	object	Optional	응답 형식 지정. {"type": "json_object"}로 설정하면 JSON 형식으로만 응답합니다. 이 경우 system 메시지에 "JSON"이라는 단어를 포함해야 합니다.
logprobs	boolean	Optional	출력 토큰의 로그 확률 반환 여부. 기본값: false
top_logprobs	integer	Optional	각 위치에서 반환할 가장 확률이 높은 토큰 수 (0~5). logprobs: true일 때만 유효합니다.
logit_bias	object | null	Optional	특정 토큰의 출현 확률을 조정합니다. 토큰 ID를 키로, -100~100 값을 매핑합니다.
tools	array	Optional	모델이 호출할 수 있는 도구(함수) 목록. 각 도구는 type("function")과 function 객체(name, description, parameters)를 포함합니다.
tool_choice	string | object	Optional	도구 호출 방식 제어. "auto"(기본값 — 모델이 판단), "none"(도구 사용 안 함), "required"(반드시 도구 호출), 또는 특정 함수를 지정하는 객체({"type": "function", "function": {"name": "..."}}).
parallel_tool_calls	boolean	Optional	병렬 도구 호출 허용 여부. true이면 모델이 여러 도구를 동시에 호출할 수 있습니다. 기본값: true
Response
OpenAI Chat Completion 응답 형식과 동일합니다.

Name	Type	Description
id	string	응답 고유 ID
object	string	"chat.completion"
created	integer	생성 시간 (Unix timestamp)
model	string	사용된 모델 ID
choices	array	응답 선택지 배열. 각 항목에 message, finish_reason, index 포함. 도구 호출 시 message.tool_calls 배열이 포함되며 finish_reason은 "tool_calls"입니다.
usage	object	토큰 사용량 (prompt_tokens, completion_tokens, total_tokens)
이미지 입력 (Multimodal)
메시지의 content를 배열로 만들고 {"type":"text"} 블록과 {"type":"image_url"} 블록을 함께 넣으면 이미지를 입력할 수 있습니다. 멀티모달 지원 모델(예: gpt-5.2)이 필요합니다.

이미지는 Base64 Data URL(data:image/png;base64,...)로 전달합니다. 한 메시지에 여러 이미지를 넣을 수 있습니다.
image_url.detail 로 해상도를 조절합니다(auto(기본) / low / high).
외부 이미지 URL(https://...)은 사용할 수 없습니다. P-GPT 내부망에서 외부 다운로드가 차단되어 Failed to download image 오류가 납니다 — 반드시 Base64로 인코딩하세요.
응답 형식은 request body의 stream으로 결정됩니다. true이면 text/event-stream, false 또는 생략이면 application/json입니다. OpenAI SDK는 스트리밍 요청에도 Accept: application/json을 보낼 수 있으며, 클라이언트가 Accept를 변경할 필요가 없습니다.
먼저 환경변수를 설정하세요. PGPT_BASE_URL에는 /gpgpta01-gpt/v1까지 포함하고, PGPT_API_KEY와 선택적 PGPT_MODEL(기본값 gpt-5.2)을 사용합니다. 실제 API Key는 Portal이나 브라우저 저장소에 입력하지 마세요.
curl
Python
Node.js
Sync
Streaming
복사
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["PGPT_API_KEY"],
    base_url=os.environ["PGPT_BASE_URL"],
)

response = client.chat.completions.create(
    model=os.getenv("PGPT_MODEL", "gpt-5.2"),
    messages=[{"role": "user", "content": "P-GPT API에 대해 알려주세요."}],
    max_completion_tokens=1024,
    stream=False,
)

print(response.choices[0].message.content)
Response

{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "gpt-5.2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "P-GPT API는 OpenAI 호환 인터페이스를 제공하는..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175
  }
}
Function Calling (Tools)
모델이 외부 함수를 호출하도록 할 수 있습니다. tools에 함수를 정의하면 모델이 적절한 시점에 함수 호출을 요청하고, 결과를 받아 최종 응답을 생성합니다.

curl
Python
Node.js

# 1단계: 도구 정의와 함께 요청
curl "$PGPT_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $PGPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "messages": [
      {"role": "user", "content": "서울 날씨 어때?"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "지정한 도시의 현재 날씨를 조회합니다.",
          "parameters": {
            "type": "object",
            "properties": {
              "city": {
                "type": "string",
                "description": "도시명 (예: Seoul, Tokyo)"
              }
            },
            "required": ["city"]
          }
        }
      }
    ],
    "tool_choice": "auto"
  }'

# 2단계: 도구 실행 결과를 포함하여 재요청
curl "$PGPT_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $PGPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "messages": [
      {"role": "user", "content": "서울 날씨 어때?"},
      {"role": "assistant", "content": null, "tool_calls": [
        {
          "id": "call_abc123",
          "type": "function",
          "function": {"name": "get_weather", "arguments": "{\"city\":\"Seoul\"}"}
        }
      ]},
      {"role": "tool", "tool_call_id": "call_abc123", "content": "{\"temp\": 22, \"condition\": \"맑음\"}"}
    ]
  }'
Tool Calls Response
모델이 도구 호출이 필요하다고 판단하면 finish_reason이 "tool_calls"이며, message.tool_calls 배열에 호출할 함수 정보가 포함됩니다.


{
  "id": "chatcmpl-abc456",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "gpt-5.2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"city\":\"Seoul\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 85,
    "completion_tokens": 18,
    "total_tokens": 103
  }
}
JSON Mode
response_format을 사용하면 모델이 항상 유효한 JSON 객체를 반환합니다.


response = client.chat.completions.create(
    model="gpt-5.2",
    messages=[
        {"role": "system", "content": "Extract the name and age as JSON."},
        {"role": "user", "content": "박병제, 30살입니다."}
    ],
    response_format={"type": "json_object"}
)

print(response.choices[0].message.content)
# {"name": "박병제", "age": 30}
이미지 입력 (Multimodal)
content 배열에 image_url 블록을 넣어 이미지를 전송합니다. 이미지는 Base64 Data URL로 전달하며, 외부 URL은 지원하지 않습니다.

curl
Python

curl "$PGPT_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $PGPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "이 이미지를 설명해줘."},
          {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KG...", "detail": "auto"}}
        ]
      }
    ]
  }'
  Streaming
복사
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["PGPT_API_KEY"],
    base_url=os.environ["PGPT_BASE_URL"],
)

stream = client.chat.completions.create(
    model=os.getenv("PGPT_MODEL", "gpt-5.2"),
    messages=[{"role": "user", "content": "안녕하세요!"}],
    max_completion_tokens=1024,
    stream=True,
)

for chunk in stream:
    for choice in chunk.choices or []:
        content = choice.delta.content
        if isinstance(content, str):
            print(content, end="", flush=True)
print()
Response

{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "gpt-5.2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "P-GPT API는 OpenAI 호환 인터페이스를 제공하는..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175
  }
}
Function Calling (Tools)
모델이 외부 함수를 호출하도록 할 수 있습니다. tools에 함수를 정의하면 모델이 적절한 시점에 함수 호출을 요청하고, 결과를 받아 최종 응답을 생성합니다.

curl
Python
Node.js

# 1단계: 도구 정의와 함께 요청
curl "$PGPT_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $PGPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "messages": [
      {"role": "user", "content": "서울 날씨 어때?"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "지정한 도시의 현재 날씨를 조회합니다.",
          "parameters": {
            "type": "object",
            "properties": {
              "city": {
                "type": "string",
                "description": "도시명 (예: Seoul, Tokyo)"
              }
            },
            "required": ["city"]
          }
        }
      }
    ],
    "tool_choice": "auto"
  }'

# 2단계: 도구 실행 결과를 포함하여 재요청
curl "$PGPT_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $PGPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "messages": [
      {"role": "user", "content": "서울 날씨 어때?"},
      {"role": "assistant", "content": null, "tool_calls": [
        {
          "id": "call_abc123",
          "type": "function",
          "function": {"name": "get_weather", "arguments": "{\"city\":\"Seoul\"}"}
        }
      ]},
      {"role": "tool", "tool_call_id": "call_abc123", "content": "{\"temp\": 22, \"condition\": \"맑음\"}"}
    ]
  }'
Tool Calls Response
모델이 도구 호출이 필요하다고 판단하면 finish_reason이 "tool_calls"이며, message.tool_calls 배열에 호출할 함수 정보가 포함됩니다.


{
  "id": "chatcmpl-abc456",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "gpt-5.2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"city\":\"Seoul\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 85,
    "completion_tokens": 18,
    "total_tokens": 103
  }
}
JSON Mode
response_format을 사용하면 모델이 항상 유효한 JSON 객체를 반환합니다.


response = client.chat.completions.create(
    model="gpt-5.2",
    messages=[
        {"role": "system", "content": "Extract the name and age as JSON."},
        {"role": "user", "content": "박병제, 30살입니다."}
    ],
    response_format={"type": "json_object"}
)

print(response.choices[0].message.content)
# {"name": "박병제", "age": 30}
이미지 입력 (Multimodal)
content 배열에 image_url 블록을 넣어 이미지를 전송합니다. 이미지는 Base64 Data URL로 전달하며, 외부 URL은 지원하지 않습니다.

curl
Python

curl "$PGPT_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $PGPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "이 이미지를 설명해줘."},
          {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KG...", "detail": "auto"}}
        ]
      }
    ]
  }'
Responses API (OpenAI)
Responses API는 Codex CLI · LangGraph 등 OpenAI Responses API를 사용하는 클라이언트를 지원하기 위한 엔드포인트입니다. 내부적으로 Chat Completions API로 변환되어 처리되며, stream 필드로 동기/스트리밍 응답을 선택할 수 있습니다.

stream 분기 (PGPT-485, 2026-05-06 반영):
stream: true → text/event-stream (SSE 스트리밍, Codex CLI 등)
stream: false → application/json (단건 JSON, LangGraph · 일반 클라이언트)
미지정 → application/json (OpenAI 기본값 false 준수)
OpenAI 공식 문서: Responses API Reference ↗

P-GPT는 프록시 방식으로 동작하므로, 실제 Request Body와 Response 형식은 OpenAI 공식 문서와 다를 수 있습니다. 정확한 파라미터와 응답 구조는 위 공식 문서를 함께 참고해주세요.

POST
/v1/responses
Request Body
Name	Type	Required	Description
model	string	Required	사용할 모델 ID (예: gpt-5.2, gpt-5.4-mini)
input	string | array	Required	입력 텍스트 또는 메시지 배열. 문자열인 경우 [{"role": "user", "content": input}]으로 자동 변환됩니다.
instructions	string	Optional	모델에 대한 시스템 지시사항. Chat Completions의 system 메시지에 해당합니다.
stream	boolean	Optional	응답 형식 분기. true → SSE 스트리밍, false 또는 미지정 → JSON 단건 응답. 기본값은 OpenAI 스펙에 따라 false.
temperature	number	Optional	샘플링 온도 (0~2). 높을수록 무작위성이 증가합니다. 기본값: 1
top_p	number	Optional	Top-p (nucleus) 샘플링 (0~1). 기본값: 1
max_output_tokens	integer	Optional	응답에서 생성할 최대 토큰 수
tools	array	Optional	모델이 호출할 수 있는 도구 목록. type("function")과 함수 정의를 포함합니다.
tool_choice	string | object	Optional	도구 호출 방식 제어. "auto", "none", "required", 또는 특정 함수 지정 객체.
previous_response_id	string	Optional	이전 응답 ID. 멀티턴 대화에서 이전 컨텍스트를 자동으로 이어갑니다.
truncation	string	Optional	컨텍스트 윈도우 초과 시 잘라내기 방식. "auto"(기본값) 또는 "disabled".
참고 사항
이 엔드포인트는 Codex CLI, LangGraph 등 OpenAI Responses API 클라이언트를 지원합니다.
응답 형식은 stream 필드로 결정됩니다 — true 시 SSE, false/미지정 시 JSON.
input이 문자열인 경우 user 메시지로 자동 변환됩니다.
input이 배열인 경우, 각 항목의 role과 content가 Chat Completions 형식으로 매핑됩니다.
추가 파라미터는 OpenAI 프로바이더로 그대로 전달됩니다.
이미지 입력 (Multimodal)
input 배열의 메시지 content에 {"type":"input_text"}와 {"type":"input_image"} 블록을 사용합니다. Chat Completions와 달리 image_url이 객체가 아니라 문자열(Base64 Data URL)입니다. 멀티모달 지원 모델(예: gpt-5.2) 필요.

이미지는 Base64 Data URL(data:image/png;base64,...) 문자열로 전달합니다.
외부 이미지 URL(https://...)은 사용할 수 없습니다. 내부망 다운로드 차단으로 오류가 나므로 반드시 Base64로 인코딩하세요.
curl
Python
Node.js

from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="http://{host}/gpgpta01-gpt/v1"
)

# 기본 사용
response = client.responses.create(
    model="gpt-5.2",
    input="P-GPT API 사용법을 알려주세요."
)

print(response.output_text)

# 멀티턴 대화 (previous_response_id)
response2 = client.responses.create(
    model="gpt-5.2",
    input="좀 더 자세히 설명해줘.",
    previous_response_id=response.id
)

print(response2.output_text)
이미지 입력 (Multimodal)
input_image 블록의 image_url 은 문자열(Base64 Data URL)입니다. 외부 URL은 지원하지 않습니다.

curl
Python

import base64
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY", base_url="http://{host}/gpgpta01-gpt/v1")

with open("photo.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")
data_url = f"data:image/png;base64,{b64}"   # JPG면 f"data:image/jpeg;base64,{b64}"

response = client.responses.create(
    model="gpt-5.2",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "이 이미지를 설명해줘."},
            {"type": "input_image", "image_url": data_url},
        ],
    }],
)

print(response.output_text)
Embeddings API (OpenAI)
입력 텍스트를 벡터로 변환합니다. OpenAI Embeddings API와 호환되며, 벡터 검색·RAG·시맨틱 유사도 계산 등에 사용됩니다.

OpenAI 공식 문서: Embeddings API Reference ↗

P-GPT는 프록시 방식으로 동작하므로, 실제 Request Body와 Response 형식은 OpenAI 공식 문서와 다를 수 있습니다. 정확한 파라미터와 응답 구조는 위 공식 문서를 함께 참고해주세요.

POST
/v1/embeddings
Request Body
Name	Type	Required	Description
model	string	Required	사용할 임베딩 모델 ID (예: text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002)
input	string | string[]	Required	임베딩할 텍스트. 단일 문자열 또는 문자열 배열(배치)로 전달할 수 있습니다.
encoding_format	string	Optional	반환되는 임베딩 포맷. "float"(기본값) 또는 "base64".
dimensions	integer	Optional	반환할 임베딩 차원 수. text-embedding-3-* 모델에서만 지원됩니다.
user	string	Optional	최종 사용자 식별자(남용 모니터링용).
Response
OpenAI Embeddings 응답 형식과 동일합니다.

Name	Type	Description
object	string	"list"
data	array	임베딩 결과 배열. 각 항목은 object: "embedding", index, embedding: number[] 를 포함합니다. input 순서와 동일합니다.
model	string	사용된 모델 ID
usage	object	토큰 사용량 (prompt_tokens, total_tokens)
curl
Python
Node.js

from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="http://{host}/gpgpta01-gpt/v1"
)

# 단일 텍스트
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="임베딩할 텍스트 내용입니다."
)
print(response.data[0].embedding[:5])

# 배치 (여러 문장을 한 번에)
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=["첫 번째 문장", "두 번째 문장", "세 번째 문장"]
)
for item in response.data:
    print(item.index, item.embedding[:3])
Response

{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.0023064255, -0.009327292, 0.015729427, ...]
    }
  ],
  "model": "text-embedding-3-small",
  "usage": {
    "prompt_tokens": 8,
    "total_tokens": 8
  }
}  

# 동기 모드 (stream:false 또는 미지정 → JSON 단건) curl http://{host}/gpgpta01-gpt/v1/responses \   -H "Authorization: Bearer YOUR_API_KEY" \   -H "Content-Type: application/json" \   -d '{
    "model": "gpt-5.2",
    "input": "P-GPT API 사용법을 알려주세요."
  }' 
  
# 스트리밍 모드 (stream:true → SSE) curl -N http://{host}/gpgpta01-gpt/v1/responses \   -H "Authorization: Bearer YOUR_API_KEY" \   -H "Content-Type: application/json" \   -H "Accept: text/event-stream" \   -d '{
    "model": "gpt-5.2",
    "stream": true,
    "input": "P-GPT API 사용법을 알려주세요."
  }'  
  
# 메시지 배열 + instructions (동기 모드) curl http://{host}/gpgpta01-gpt/v1/responses \   -H "Authorization: Bearer YOUR_API_KEY" \   -H "Content-Type: application/json" \   -d '{
    "model": "gpt-5.2",
    "instructions": "항상 한국어로 답변하세요.",
    "input": [
      {"role": "user", "content": "What is P-GPT?"}
    ]
  }'

Codex CLI 연동
P-GPT는 OpenAI 호환 API를 제공하므로, OpenAI Codex CLI를 P-GPT에 연결하여 사용할 수 있습니다. ~/.codex/config.toml에 P-GPT를 모델 제공자로 등록하면 됩니다.

POST
/v1/chat/completions
 
POST
/v1/responses
개요
Codex CLI는 OpenAI의 터미널 기반 코딩 에이전트로, 자연어 명령을 코드 변경으로 변환합니다. P-GPT가 OpenAI API와 호환되는 /v1/chat/completions 및 /v1/responses 엔드포인트를 제공하므로, Codex CLI를 P-GPT 프록시를 통해 그대로 사용할 수 있습니다.

Chat Completions — /v1/chat/completions 엔드포인트로 대화 기반 응답을 생성합니다.
Responses API — /v1/responses 엔드포인트로 단일 요청 응답을 생성합니다.
스트리밍 지원 — SSE 스트리밍으로 실시간 응답을 받을 수 있습니다.
API Key 관리 — P-GPT에서 발급한 API Key를 사용합니다.
인증
Codex CLI는 OpenAI 표준 인증 방식을 사용합니다.

방식	설정	설명
Authorization	Authorization: Bearer YOUR_API_KEY	OpenAI 표준 Bearer 토큰 인증. P-GPT에서 발급받은 API Key를 사용합니다.
환경변수	OPENAI_API_KEY=YOUR_API_KEY	Codex CLI가 자동으로 읽는 환경변수입니다.
Codex CLI 설정 방법
Codex CLI에서 P-GPT를 사용하려면 ~/.codex/config.toml에 P-GPT를 모델 제공자(model provider)로 등록해야 합니다. OPENAI_BASE_URL 환경변수만으로는 기본 OpenAI 엔드포인트가 우회되지 않아 인증에 실패합니다.

P-GPT API Key 발급 — "P-GPT API 신청" 메뉴에서 API Key를 발급받습니다.
Codex CLI 설치 — npm install -g @openai/codex
config.toml 작성 — ~/.codex/config.toml (Windows: %USERPROFILE%\.codex\config.toml)에 P-GPT provider 블록을 추가합니다.
API Key 환경변수 설정 — OPENAI_API_KEY를 P-GPT에서 발급받은 키로 설정합니다.
Codex CLI 실행 — codex 명령으로 CLI를 시작합니다.
커스텀 설정 항목
P-GPT에 연결하기 위해 반드시 설정해야 하는 항목입니다.

항목	설정 위치	값	설명
model_provider	~/.codex/config.toml (top-level)	"pgpt"	기본 모델 제공자 이름. 아래 [model_providers.pgpt] 블록의 키와 일치해야 합니다.
model	~/.codex/config.toml (top-level)	"gpt-5.2" 등	기본 사용 모델. P-GPT에 등록된 모델만 사용 가능합니다.
[model_providers.pgpt].name	provider 블록 내	"P-GPT Internal Server"	(자유 문자열) 표시용 이름.
[model_providers.pgpt].base_url	provider 블록 내	"http://{host}/gpgpta01-gpt/v1"	P-GPT API 엔드포인트. 반드시 /v1까지 포함, 프로토콜은 http://를 사용합니다.
[model_providers.pgpt].env_key	provider 블록 내	"OPENAI_API_KEY"	API Key를 읽어올 환경변수의 이름. 값이 아닌 변수 이름을 명시합니다.
OPENAI_API_KEY	환경변수	P-GPT에서 발급받은 API Key	env_key가 가리키는 환경변수. Codex CLI가 Authorization: Bearer 헤더로 전송합니다. OpenAI API Key가 아닌 P-GPT API Key를 입력해야 합니다.
주의: OPENAI_BASE_URL 환경변수만 설정하는 방식은 동작하지 않습니다. Codex CLI는 config.toml의 [model_providers.xxx] 블록을 통해서만 base_url을 인식하므로, 반드시 config.toml을 작성해야 인증이 통과됩니다. 또한 base_url의 프로토콜은 사내 환경에서 https://가 아닌 http://를 사용해야 정상 연결됩니다.
환경별 URL
위 [model_providers.pgpt].base_url에 사용할 환경별 엔드포인트입니다.

환경	base_url
개발계	http://taigpt.posco.net/gpgpta01-gpt/v1
운영계	http://aigpt.posco.net/gpgpta01-gpt/v1
주요 Codex CLI 옵션
옵션	설명	예시
--model	사용할 모델 지정	codex --model gpt-5.2
--approval-mode	파일 수정 승인 모드 (suggest, auto-edit, full-auto)	codex --approval-mode suggest
-q	비대화형 모드 (단일 프롬프트 실행)	codex -q "이 함수를 리팩토링해줘"
config.toml (Linux/macOS)
PowerShell (Windows)
curl 테스트

# 1. %USERPROFILE%\.codex\config.toml 작성
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex" | Out-Null
@'
model = "gpt-5.2"
model_provider = "pgpt"

[model_providers.pgpt]
name = "P-GPT Internal Server"
base_url = "http://{host}/gpgpta01-gpt/v1"
env_key = "OPENAI_API_KEY"
'@ | Set-Content -Path "$env:USERPROFILE\.codex\config.toml" -Encoding utf8

# 2. API Key 환경변수 설정 (현재 세션)
$env:OPENAI_API_KEY = "YOUR_API_KEY"

# 영구 설정 (사용자 환경변수)
[System.Environment]::SetEnvironmentVariable(
    "OPENAI_API_KEY", "YOUR_API_KEY", "User")

# 3. Codex CLI 설치 및 실행
npm install -g @openai/codex
codex
연결 확인
Response (Models)

{
  "object": "list",
  "data": [
    {
      "id": "gpt-5.2",
      "object": "model",
      "owned_by": "p-gpt"
    },
    {
      "id": "gpt-4o-mini",
      "object": "model",
      "owned_by": "p-gpt"
    },
    {
      "id": "o4-mini",
      "object": "model",
      "owned_by": "p-gpt"
    }
  ]
}
