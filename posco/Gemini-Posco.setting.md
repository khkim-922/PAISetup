Gemini Native API (Gemini)
Google Gemini API(generativelanguage.googleapis.com)와 동일한 엔드포인트 구조의 패스스루 프록시입니다. Gemini CLI, Google AI SDK 등에서 P-GPT를 통해 Gemini 모델을 호출할 수 있습니다.

Google 공식 문서: Gemini API Reference ↗

P-GPT는 프록시 방식으로 동작하므로, 실제 Request Body와 Response 형식은 Google 공식 문서와 다를 수 있습니다. 정확한 파라미터와 응답 구조는 위 공식 문서를 함께 참고해주세요.

POST
/v1beta/models/{model}:generateContent
 
POST
/v1beta/models/{model}:streamGenerateContent
인증
다음 두 가지 인증 방식을 지원합니다.

방식	헤더	설명
x-goog-api-key	x-goog-api-key: YOUR_API_KEY	Gemini 네이티브 인증 방식. Gemini CLI가 기본 사용하는 방식입니다.
Authorization	Authorization: Bearer YOUR_API_KEY	Bearer 토큰 방식. 기존 P-GPT API Key를 그대로 사용할 수 있습니다.
Request Body
Gemini 네이티브 API 형식을 그대로 사용합니다.

Name	Type	Required	Description
contents	array	Required	대화 메시지 배열. 각 항목은 role("user", "model")과 parts를 포함합니다.
contents[].parts	array	Required	콘텐츠 파트 배열. 텍스트의 경우 {"text": "..."} 형식입니다.
generationConfig	object	Optional	생성 설정. temperature, maxOutputTokens, topP, topK 등을 포함합니다.
systemInstruction	object	Optional	시스템 프롬프트. {"parts": [{"text": "..."}]} 형식입니다.
Response
Name	Type	Description
candidates	array	응답 후보 배열
candidates[].content	object	role("model")과 parts를 포함하는 응답 콘텐츠
candidates[].finishReason	string	생성 완료 사유 ("STOP", "MAX_TOKENS" 등)
usageMetadata	object	토큰 사용량 (promptTokenCount, candidatesTokenCount, totalTokenCount)
사용 가능한 모델
P-GPT에 등록된 Gemini 모델을 사용할 수 있습니다. 관리자 설정에 따라 다를 수 있습니다.

gemini-2.5-flash
gemini-2.5-flash-lite
gemini-3-flash-preview
gemini-3.1-flash-lite
gemini-3.1-pro-preview
gemini-3.5-flash
이미지 입력 (Multimodal)
contents[].parts에 텍스트 part와 inline_data part를 함께 넣어 이미지를 전송합니다. inline_data는 접두사 없는 순수 Base64와 mime_type으로 구성합니다.

외부 이미지 URL은 사용할 수 없습니다. 내부망 다운로드 차단으로 오류가 나므로 반드시 Base64(inline_data)로 전달하세요.
구형 google-generativeai SDK는 프록시 경유 시 $alt 쿼리 파라미터 오류가 발생합니다. 신형 google-genai SDK 또는 raw REST를 사용하세요.
curl
Python

# 신형 google-genai SDK 사용 (구형 google-generativeai 는 프록시 경유 시 $alt 쿼리 오류) from google import genai
from google.genai import types

# P-GPT 프록시를 통한 Gemini API 호출
client = genai.Client(
    api_key="YOUR_API_KEY",
    http_options=types.HttpOptions(base_url="http://{host}/gpgpta01-gpt"), )  # 동기 응답
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="P-GPT API에 대해 알려주세요.", ) print(response.text)  # 스트리밍 응답 for chunk in client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents="안녕하세요!", ):     print(chunk.text, end="")
Response (동기)

{   "candidates": [     {       "content": {         "parts": [           {             "text": "P-GPT API는 OpenAI 및 Gemini 호환 인터페이스를 제공하는..."           }         ],         "role": "model"       },       "finishReason": "STOP"     }   ],   "usageMetadata": {     "promptTokenCount": 12,     "candidatesTokenCount": 150,     "totalTokenCount": 162   } }
Response (스트리밍 SSE)

data: {"candidates":[{"content":{"parts":[{"text":"P-GPT"}],"role":"model"}}]}

data: {"candidates":[{"content":{"parts":[{"text":" API는"}],"role":"model"}}]}

data: {"candidates":[{"content":{"parts":[{"text":" OpenAI 및 Gemini 호환..."}],"role":"model"},"finishReason":"STOP"}],"usageMetadata":{"promptTokenCount":12,"candidatesTokenCount":150,"totalTokenCount":162}}
이미지 입력 (Multimodal)
inline_data(순수 Base64 + mime_type)로 이미지를 전송합니다. 외부 URL은 지원하지 않습니다.

curl
Python

curl http://{host}/gpgpta01-gpt/v1beta/models/gemini-2.5-flash:generateContent \   -H "x-goog-api-key: YOUR_API_KEY" \   -H "Content-Type: application/json" \   -d '{
    "contents": [
      {
        "role": "user",
        "parts": [
          {"text": "이 이미지를 설명해줘."},
          {"inline_data": {"mime_type": "image/png", "data": "iVBORw0KG..."}}
        ]
      }
    ]
  }'


Gemini CLI 연동
P-GPT 프록시 서버를 통해 Gemini CLI를 사용하는 방법입니다. Gemini CLI는 Google의 AI 코딩 어시스턴트로, 터미널 기반에서 코드 리뷰, 생성, 리팩토링 등을 수행합니다.

API 스펙 상세는 Gemini Native API 문서를 참조하세요.

1. 설치
npm install -g @google/gemini-cli
Node.js 18+ 필요. 설치 확인: gemini --version

2. HTTP 패치 (필수, 최초 1회)
사내망(HTTP)에서 사용하기 위해 HTTPS 검증을 완화하는 패치가 필요합니다. 아래 스크립트를 gemini-patch.ps1로 저장한 후 실행하세요.

powershell -ExecutionPolicy Bypass -File gemini-patch.ps1
세부정보
주의: Gemini CLI 업데이트(npm update -g @google/gemini-cli) 후에는 패치를 다시 실행해야 합니다.
3. 환경변수 설정
항목	값	설명
GOOGLE_GEMINI_BASE_URL	http://taigpt.posco.net/gpgpta01-gpt	P-GPT 프록시 서버 주소. 반드시 http://를 사용합니다.
GEMINI_API_KEY	발급받은 UUID API Key	P-GPT 관리자 페이지에서 발급받은 키. Google API Key가 아닙니다.
세부정보
세부정보
환경별 URL
환경	GOOGLE_GEMINI_BASE_URL
개발계	http://taigpt.posco.net/gpgpta01-gpt
운영계	http://aigpt.posco.net/gpgpta01-gpt
4. 사용법
명령	설명
gemini	대화형 모드 실행
gemini -m gemini-2.5-flash	모델 지정하여 실행
gemini -p "코드 리뷰해줘"	1회성 프롬프트 (비대화형)
gemini -y -m gemini-2.5-flash	자동 승인 모드 (YOLO)
Gemini CLI는 현재 디렉토리의 코드를 자동으로 인식합니다.

5. 사용 가능한 모델
모델	용도	추천
gemini-2.5-flash	빠른 응답, 일반 코딩	기본 추천
gemini-3-flash-preview	최신 기능, 고품질	복잡한 작업
gemini-2.5-flash-lite	경량, 빠른 속도	간단한 질문
gemini-3.1-pro-preview	최고 성능	아키텍처 설계
6. 동작 원리
Gemini CLI가 x-goog-api-key 헤더에 UUID API Key를 포함하여 요청
P-GPT 프록시 서버가 DB에서 실제 Google API Key를 조회
사용 이력 감사 로그 저장
Google Gemini API로 요청 전달 → AI 응답 → 터미널 출력
실제 Google API Key는 서버에서 관리되어 개인에게 노출되지 않습니다.

7. 트러블슈팅
에러	해결
Custom base URL must use HTTPS	HTTP 패치가 적용되지 않음. gemini-patch.ps1 다시 실행
API Key가 제공되지 않았습니다	$env:GEMINI_API_KEY 환경변수 확인
모델을 찾을 수 없습니다	DB에 해당 모델 등록 여부를 관리자에게 확인
업데이트 후 다시 안 됨	npm update 시 패치 초기화됨. 패치 스크립트 재실행
빠른 시작
사용 예시

# 1. 설치
npm install -g @google/gemini-cli  # 2. 패치 (최초 1회, 업데이트 후 재실행)
powershell -ExecutionPolicy Bypass `
  -File gemini-patch.ps1

# 3. 환경변수 $env:GOOGLE_GEMINI_BASE_URL = `
  "http://taigpt.posco.net/gpgpta01-gpt" $env:GEMINI_API_KEY = `
  "발급받은-UUID-API-Key"  # 4. 실행
gemini -m gemini-2.5-flash
동작 흐름
Gemini CLI (내 PC)
  ↓ x-goog-api-key: {UUID API Key}
P-GPT 프록시 (taigpt.posco.net)
  ↓ DB에서 실제 Google API Key 조회
  ↓ 감사 로그 저장
Google Gemini API
  ↓ AI 응답
내 터미널에 출력

