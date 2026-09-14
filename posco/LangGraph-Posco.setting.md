LangGraph + Native API
Native(OpenAI/Anthropic/Gemini 호환) 엔드포인트를 LangGraph 노드로 연결해 도구 호출(Function Calling) · 멀티턴 · 스트리밍을 그래프 흐름으로 구성하는 가이드입니다. LangChain 공식 어댑터(langchain-openai, langchain-anthropic 등)와 base_url 만 변경하면 그대로 동작합니다.

대상 엔드포인트: Chat Completions / Messages / Responses / Gemini Native / sLLM Native. 모두 Native API 그룹에 정리되어 있습니다.
1. 사전 준비
API Key 발급 — 사이드바 상단 "API 신청하기" 버튼.
Python 패키지 — pip install langgraph langchain-openai
모델 ID — Models API 페이지에서 사용 가능한 모델 식별자 확인 (예: gpt-5.2).
2. ChatOpenAI를 P-GPT base_url 로 구성
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-5.2",
    api_key="YOUR_PGPT_API_KEY",
    base_url="http://aigpt.posco.net/gpgpta01-gpt/v1",
    temperature=0.2,
    streaming=True )
3. 도구 호출 노드 + 라우팅
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool

@tool def search_intranet(q: str) -> str:     """사내 위키에서 키워드로 검색."""     return f"[mock] {q} 결과 3건"

llm_with_tools = llm.bind_tools([search_intranet])  class State(TypedDict):
    messages: Annotated[list, lambda l, r: l + r]  def chatbot(s: State) -> State:     return {"messages": [llm_with_tools.invoke(s["messages"])]}  def tools_node(s: State) -> State:
    last = s["messages"][-1]
    out = []     for call in last.tool_calls:
        result = search_intranet.invoke(call["args"])
        out.append(ToolMessage(content=result, tool_call_id=call["id"]))     return {"messages": out}  def should_continue(s: State) -> str:     return "tools" if s["messages"][-1].tool_calls else END

g = StateGraph(State)
g.add_node("chatbot", chatbot)
g.add_node("tools", tools_node)
g.set_entry_point("chatbot")
g.add_conditional_edges("chatbot", should_continue, {"tools": "tools", END: END})
g.add_edge("tools", "chatbot")

app = g.compile() print(app.invoke({"messages": [HumanMessage("안전 규정 검색해줘")]}))
4. 스트리밍 통합 (SSE)
LangGraph app.stream() 또는 app.astream_events() 로 노드 단위 결과를 SSE 형태로 흘릴 수 있습니다. P-GPT Native API 는 OpenAI 호환 SSE 포맷(data: {...}\n\n)을 그대로 반환합니다.

async for ev in app.astream_events({"messages": [HumanMessage("요약해줘")]}, version="v2"):     if ev["event"] == "on_chat_model_stream":
        chunk = ev["data"]["chunk"]         print(chunk.content, end="", flush=True)
5. Anthropic / Gemini 어댑터
Messages API — langchain-anthropic + base_url="http://.../v1". x-api-key 헤더는 라이브러리가 자동 처리.
Gemini Native — langchain-google-genai 는 base_url 변경이 제한적이므로, httpx + 커스텀 노드 권장.
Responses API — Codex CLI · 멀티턴 워크플로우에 적합. Chat Completions 와 다른 응답 구조.
6. 권장 패턴
Tool 분리 — 외부 시스템 호출은 항상 별도 노드로. LLM 호출과 부수 효과 분리.
모델 라우팅 — 비용 민감 노드는 Haiku/Mini 모델, 추론 무거운 노드는 Opus/4o.
에러 처리 — Native API 에러는 OpenAI 호환 포맷({"error": {...}})이지만 code 는 P-GPT 내부 enum(예: C046) 그대로 노출 — Error Codes 페이지 참고.
7. 다음 단계
RAG 컨텍스트가 필요하면 P-GPT API 가이드 참고하여 RAG API 노드를 같은 그래프에 추가할 수 있습니다.
Checkpoint(SQLite/Postgres) 로 대화 상태 영속화.
LangSmith 트레이싱으로 노드별 latency/cost 분석.

LangGraph + P-GPT API (PersonalApiLLM)
P-GPT 자체 스펙 API 를 LangGraph·LangChain 에 바로 연동할 수 있는 PersonalApiLLM 커스텀 클래스 가이드입니다. BaseChatOpenAI 를 상속받아 동기 호출(invoke) · 스트리밍(stream) · 도구 호출(Function Calling) 을 모두 지원합니다.

참고: 본 클래스는 Personal API · RAG API 두 엔드포인트 모두에서 사용 가능합니다 — category 파라미터를 채우면 RAG, 비우면 단순 LLM 호출로 동작합니다.
1. 개요
이 샘플은 LangGraph 를 사용하여 간단한 챗봇을 구현한 예제입니다. 기존의 Azure OpenAI 대신 POSCO 의 Personal API 를 사용하여 LLM 을 연동하는 방법을 보여줍니다.

LangGraph 란?
LangGraph 는 LangChain 을 기반으로 한 복잡한 에이전트 워크플로우를 구축할 수 있는 프레임워크입니다.
2. LLM 선언 방식 변경
기존 방식 (Azure OpenAI):

llm = AzureChatOpenAI(
    azure_deployment = "gpt-4.1",
    api_version = "2025-01-01-preview",
    http_client = HTTPX_CLIENT,
    azure_endpoint = "https://xxx.openai.azure.com/",
    api_key = "xxxx123xxx456xxxx89xxxxx",
    timeout = 120 )
새로운 방식 (Personal API):

llm = PersonalApiLLM(
    api_url="http://aigpt.posco.net/gpgpta01-gpt/gptApi/personalApi",
    api_key="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",   # 발급받은 API 키
    category="Rxxxxxxxx",                              # 카테고리 (RAG API 사용 시 필요)
    comp_no="01",                                      # 회사코드
    system_code="P-GPT",                               # 시스템코드
    tools=tools                                        # 도구를 인스턴스 변수로 설정 )
장점: Personal API 를 사용하면 복잡한 Azure 설정 없이도 LLM 을 쉽게 연동할 수 있습니다.

3. PersonalApiLLM 클래스 구현
PersonalApiLLM 클래스는 BaseChatOpenAI 를 상속받아 LangChain 과 호환되며, 다음 장점이 있습니다.

LangChain · LangGraph 의 모든 도구·메시지 인터페이스(HumanMessage, SystemMessage, ToolMessage) 그대로 사용
_generate · _stream 양쪽 구현 — llm.invoke() / llm.stream() 호출에 자동 매핑
도구 호출(Function Calling) · 토큰 사용량(usage_metadata) · 컨텐츠 필터 결과 전달
인증 헤더(Authorization: Bearer base64(...)) 자동 생성
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult, ChatGenerationChunk
from langchain_core.messages import AIMessageChunk
import requests
import base64
import json
from typing import Any, Dict, Iterator, List, Optional
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage
from langchain_openai.chat_models.base import BaseChatOpenAI


class PersonalApiLLM(BaseChatOpenAI):     # default setting
    api_url: str      # header
    comp_no: str
    api_key: str
    system_code: Optional[str] = None
    category: Optional[str] = None      # azure parameter
    model: str = "gpt-4.1"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[Any] = None
    tools: Optional[Any] = None
    functions: Optional[Any] = None      @property     def _llm_type(self) -> str:         return "personal-api-llm"      @property     def _identifying_params(self) -> Dict[str, Any]:         return {             "api_url": self.api_url,             "model": self.model,             "temperature": self.temperature,         }      @staticmethod     def tools_to_dict(tools_list):         """도구 리스트를 JSON 직렬화 가능한 딕셔너리 리스트로 변환"""
        result = []         for tool in tools_list:             try:
                tool_dict = {                     "type": "function",                     "function": {                         "name": tool.name,                         "description": tool.description,                         "parameters": tool.args_schema.model_json_schema() if hasattr(tool, 'args_schema') and tool.args_schema else {}                     }                 }
                result.append(tool_dict)             except Exception as e:                 print(f"도구 변환 오류 ({tool.name}): {e}")         return result

    def _build_auth_headers(self):         """인증 헤더 생성 (공통)"""
        auth_dict = {             "apiKey": self.api_key,             "companyCode": self.comp_no,             "systemCode": self.system_code
        }         if self.category:
            auth_dict["category"] = self.category

        encoded_auth = base64.b64encode(
            json.dumps(auth_dict).encode("utf-8")         ).decode("utf-8")         return {             "accept": "*/*",             "Authorization": f"Bearer {encoded_auth}",             "Content-Type": "application/json"         }      def _build_payload(self, messages, **kwargs):         """요청 payload 생성 (공통)"""
        payload_messages = []         for m in messages:             if isinstance(m, SystemMessage):
                payload_messages.append({"role": "system", "content": m.content})             elif isinstance(m, HumanMessage):
                payload_messages.append({"role": "user", "content": m.content})             else:
                payload_messages.append({"role": "user", "content": m.content})

        payload = {             "messages": payload_messages,             "model": self.model,             "temperature": self.temperature,             "need_origin": True         }          for k in ["max_tokens", "top_p", "frequency_penalty", "presence_penalty", "stop", "functions"]:
            v = getattr(self, k, None)             if v is not None:
                payload[k] = v

        tools_param = kwargs.get('tools') or getattr(self, 'tools', None)         if tools_param is not None:             try:                 if isinstance(tools_param, list) and tools_param and isinstance(tools_param[0], dict):
                    payload["tools"] = tools_param
                else:
                    payload["tools"] = self.tools_to_dict(tools_param)             except Exception as e:                 print(f"도구 처리 오류: {e}")

        payload.update(kwargs)         return payload

    def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,             **kwargs: Any,     ) -> ChatResult:
        headers = self._build_auth_headers()
        payload = self._build_payload(messages, **kwargs)

        response = requests.post(self.api_url, headers=headers, json=payload)          # HTTP 에러 상태 코드 처리         if not response.ok:             try:
                error_data = response.json()
                error_message = error_data.get("error", response.text)             except (ValueError, KeyError):
                error_message = response.text if response.text else f"HTTP {response.status_code}: {response.reason}"             raise Exception(f"API Error: {error_message}")

        result = response.json()          # 응답에서 첫 번째 선택사항 가져오기
        first_choice = result.get("choices", [{}])[0]
        message_data = first_choice.get("message", {})

        additional_kwargs = {}          if function_call := message_data.get("function_call"):
            additional_kwargs["function_call"] = dict(function_call)         if message_data.get("tool_calls"):
            additional_kwargs["tool_calls"] = message_data["tool_calls"]         if audio := message_data.get("audio"):
            additional_kwargs["audio"] = audio

        content = "" if (message_data.get("tool_calls") or "function_call" in additional_kwargs) else message_data.get(             "content", str(result))

        usage_metadata = None         if token_usage := result.get("usage"):
            input_tokens = token_usage.get("prompt_tokens", 0)
            output_tokens = token_usage.get("completion_tokens", 0)
            total_tokens = token_usage.get("total_tokens", input_tokens + output_tokens)

            input_token_details = {}             if prompt_details := token_usage.get("prompt_tokens_details"):                 if audio_tokens := prompt_details.get("audio_tokens"):
                    input_token_details["audio"] = audio_tokens
                if cached_tokens := prompt_details.get("cached_tokens"):
                    input_token_details["cache_read"] = cached_tokens

            output_token_details = {}             if completion_details := token_usage.get("completion_tokens_details"):                 if audio_tokens := completion_details.get("audio_tokens"):
                    output_token_details["audio"] = audio_tokens
                if reasoning_tokens := completion_details.get("reasoning_tokens"):
                    output_token_details["reasoning"] = reasoning_tokens

            usage_metadata = {                 "input_tokens": input_tokens,                 "output_tokens": output_tokens,                 "total_tokens": total_tokens
            }             if input_token_details:
                usage_metadata["input_token_details"] = input_token_details
            if output_token_details:
                usage_metadata["output_token_details"] = output_token_details

        message = AIMessage(
            content=content,
            additional_kwargs=additional_kwargs,
            usage_metadata=usage_metadata
        )

        generation_info = {             "finish_reason": first_choice.get("finish_reason"),             "model_name": result.get("model"),             "system_fingerprint": result.get("system_fingerprint")         }         if "content_filter_results" in first_choice:
            generation_info["content_filter_results"] = first_choice["content_filter_results"]

        generation = ChatGeneration(message=message, generation_info=generation_info)

        llm_output = {             "token_usage": token_usage,             "model_name": result.get("model"),             "system_fingerprint": result.get("system_fingerprint", "")         }         if "prompt_filter_results" in result:
            llm_output["prompt_filter_results"] = result["prompt_filter_results"]          return ChatResult(generations=[generation], llm_output=llm_output)      def _stream(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,             **kwargs: Any,     ) -> Iterator[ChatGenerationChunk]:         """스트리밍 응답 처리 — llm.stream() 호출 시 자동 사용"""
        headers = self._build_auth_headers()
        payload = self._build_payload(messages, **kwargs)
        payload["stream"] = True

        response = requests.post(
            self.api_url, headers=headers, json=payload, stream=True         )         if not response.ok:             raise Exception(f"API Error: HTTP {response.status_code}")          for line in response.iter_lines():             if not line:                 continue
            decoded = line.decode('utf-8')             if not decoded.startswith('data: '):                 continue
            chunk_str = decoded[6:]             if chunk_str.strip() == '[DONE]':                 break
            chunk = json.loads(chunk_str)
            delta = chunk.get('choices', [{}])[0].get('delta', {})
            content = delta.get('content', '')             if content:                 yield ChatGenerationChunk(
                    message=AIMessageChunk(content=content)                 )                 if run_manager:
                    run_manager.on_llm_new_token(content)      def _create_chat_result(self, response: Dict[str, Any], **kwargs: Any) -> ChatResult:         return super()._create_chat_result(response, **kwargs)
4. LangGraph 전체 예시코드
위 PersonalApiLLM 클래스에 _stream 메서드가 포함되어 있어, llm.stream() 호출만으로 스트리밍을 사용할 수 있습니다.

참고: llm.invoke() 는 일반 호출(_generate), llm.stream() 은 스트리밍 호출(_stream) 을 자동으로 사용합니다.

########################################################### ################### PersonalApiLLM 구현 ################### ########################################################### # 위 3번 섹션의 PersonalApiLLM 클래스 코드를 그대로 사용  
########################################################### ###################### 도구 정의 ########################## ########################################################### from langchain_core.tools import tool
import math
import random

@tool def calculator(expression: str) -> str:     """수학 계산을 수행합니다. 예: '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)'"""     try:         # 안전한 수학 함수들만 허용
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")         }
        allowed_names.update({"abs": abs, "round": round})          # eval 을 사용하되 안전한 네임스페이스만 허용
        result = eval(expression, {"__builtins__": {}}, allowed_names)         return f"계산 결과: {result}"     except Exception as e:         return f"계산 오류: {str(e)}"  @tool def get_weather(city: str) -> str:     """도시의 날씨 정보를 가져옵니다. (시뮬레이션)"""
    weather_conditions = ["맑음", "흐림", "비", "눈", "구름많음"]
    temperature = random.randint(-5, 35)
    condition = random.choice(weather_conditions)     return f"{city}의 날씨: {condition}, 기온 {temperature}°C"  @tool def get_random_fact() -> str:     """랜덤한 재미있는 사실을 제공합니다."""
    facts = [         "고래의 심장은 자동차만큼 크다",         "바나나는 베리(berry)가 아니라 허브다",         "지구에서 가장 긴 강은 나일강이다",         "펭귄은 날 수 없는 새다",         "달은 매년 3.8cm 씩 지구에서 멀어지고 있다"     ]     return f"재미있는 사실: {random.choice(facts)}"  # 도구 목록
tools = [calculator, get_weather, get_random_fact]  
########################################################### ###################### LangGraph 구현 ##################### ########################################################### from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

# LLM 인스턴스 생성 (도구 포함)
llm = PersonalApiLLM(     # api_url="http://aigpt.posco.net/gpgpta01-gpt/gptApi/personalApi",   # 가동계
    api_url="http://taigpt.posco.net/gpgpta01-gpt/gptApi/personalApi",   # 개발계
    api_key="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxXxXX",   # 발급받은 API 키     # api_key="xxxXXxxx-xxxx-xxxx-xxxx-xxxxxxxXxxxx",   # 발급받은 API 키 (RAG)     # category="R1736827779052",                        # 카테고리 (RAG API 사용 시 필요)
    comp_no="01",          # 회사코드
    system_code="P-GPT",   # 시스템코드
    tools=tools            # 도구를 인스턴스 변수로 설정 )  
# State 정의 class State(TypedDict):
    messages: Annotated[list, add_messages]  
# 챗봇 노드 def chatbot(state: State):     # LLM 호출 (도구는 인스턴스 변수로 이미 설정됨)
    response = llm.invoke(state["messages"])     return {"messages": [response]}  
# 도구 호출 처리 노드 def tool_executor(state: State):
    last_message = state["messages"][-1]      # 도구 호출이 있는지 확인     if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tool_results = []          for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]              # 도구 실행             for tool in tools:                 if tool.name == tool_name:                     try:
                        result = tool.invoke(tool_args)
                        tool_results.append({                             "tool_call_id": tool_call["id"],                             "content": result
                        })                     except Exception as e:
                        tool_results.append({                             "tool_call_id": tool_call["id"],                             "content": f"도구 실행 오류: {str(e)}"                         })                     break          # 도구 결과를 메시지로 추가         from langchain_core.messages import ToolMessage
        tool_messages = [ToolMessage(content=result["content"], tool_call_id=result["tool_call_id"])                         for result in tool_results]          return {"messages": tool_messages}      return {"messages": []}  
# 다음 단계 결정 함수 def should_continue(state: State):
    last_message = state["messages"][-1]      # 도구 호출이 있으면 도구 실행으로     if hasattr(last_message, 'tool_calls') and last_message.tool_calls:         return "tools"     # 그렇지 않으면 종료     return "__end__"  
# 그래프 구성
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_executor)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", should_continue, {"tools": "tools", "__end__": "__end__"})
graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()
스트리밍 사용 방법

from langchain_core.messages import HumanMessage

# LLM 인스턴스 (위 전체 예시코드와 동일)
llm = PersonalApiLLM(
    api_url="http://aigpt.posco.net/gpgpta01-gpt/gptApi/personalApi",
    api_key="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    comp_no="01",
    system_code="P-GPT", )  # 스트리밍 호출 — 토큰 단위로 실시간 출력 for chunk in llm.stream([HumanMessage(content="안녕하세요")]):     print(chunk.content, end="", flush=True)  print()  # 줄바꿈