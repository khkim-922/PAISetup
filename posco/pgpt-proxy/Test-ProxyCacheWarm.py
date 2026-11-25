"""쉬는 대화의 캐시 데우기 — 사람이 보내지 않은 요청이 정해진 꼴 · 정해진 횟수로만 나가나.

    python -X utf8 posco/pgpt-proxy/Test-ProxyCacheWarm.py

층: 쓰는 사람의 계약 — 데우기 요청은 그 사람의 키로 게이트웨이에 나가고 화면에 안 보인다. 꼴이 틀리면(max_tokens 가 1 이
아니다 · 횟수가 안 멈춘다) 조용히 생성이 돈다. 가짜 게이트웨이로 재고 사내망은 안 탄다.
걷는 조건: 데우기(`PGPT_PROXY_CACHE_WARM_CYCLES`)를 걷을 때.
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("proxy", ROOT / "opus5_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

SESSION = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
SEEN: list[dict] = []        # 가짜 게이트웨이가 받은 요청 — 길 · 머리 · 몸
ANSWER = {"status": 200, "cache_read": 5000}   # 비스트리밍(데우기) 요청에 줄 답
HOLD = "hold:"               # 첫 메시지가 이 글로 시작하는 스트림은 RELEASE 가 설 때까지 답을 쥔다 — 도는 중인 레인
RELEASE = threading.Event()


def event(kind, **fields):
    return ("event: " + kind + "\ndata: " + json.dumps({"type": kind, **fields}) + "\n\n").encode()


STREAM = (event("message_start", message={"id": "m", "usage": {"input_tokens": 0, "output_tokens": 0}})
          + event("message_delta", delta={"stop_reason": "end_turn"},
                  usage={"input_tokens": 9, "cache_read_input_tokens": 5000, "output_tokens": 6})
          + event("message_stop"))
TOOL = "tool:"               # 첫 메시지가 이 글로 시작하는 스트림은 도구 호출에서 멈춘다 — 자식 레인을 기다리는 부모
REPORT = "report:"           # 마지막 메시지가 이 글로 시작하는 스트림은 보고 도구만 부르고 멈춘다 — 일을 마친 레인
# 클라이언트가 레인의 요청에 싣는 머리 이름 — 실물(Claude Code 의 요청)에서 잰 값이다. 프록시의 상수에서 읽어 오면 그 상수가
# 틀려도 초록이다
LANE_ID_HEADER, LANE_PARENT_HEADER = "x-claude-code-agent-id", "x-claude-code-parent-agent-id"
PARENT_OF: dict[str, str] = {}  # 첫 메시지 → 그 레인을 띄운 레인의 번호. 메인이 띄운 레인은 없다
LANE_OF: dict[str, str] = {}  # 첫 메시지 → 레인 번호. ``lane`` 이 채우고 ``send`` 가 그 머리를 싣는다 — 메인의 첫 메시지는 없다
# 맡기기 러너(claude-background)가 띄운 `claude -p` 의 요청에 그 러너가 싣는 머리 — 러너(`claude_bg.py`)와 맺은 약속이라 글자로 적는다
RUNNER_HEADER = "x-agent-runner"
RUNNER_OF: set[str] = set()   # 첫 메시지 — 러너가 띄운 대화. ``send`` 가 그 머리를 싣는다


def stream_calling(tool: str) -> bytes:
    """``tool`` 을 부르고 도구 호출에서 멈추는 스트림 — 클라이언트가 받는 차례(블록 시작 → 멈춤 까닭) 그대로."""
    called = event("content_block_start", index=0,
                   content_block={"type": "tool_use", "id": "toolu_1", "name": tool, "input": {}})
    head, tail = STREAM.split(b"event: message_delta")
    stopped = (b"event: message_delta" + tail).replace(b'"stop_reason": "end_turn"', b'"stop_reason": "tool_use"')
    assert b'"tool_use"' in stopped
    return head + called + event("content_block_stop", index=0) + stopped


STREAM_TOOL = stream_calling("Agent")
STREAM_REPORT = stream_calling(proxy.LANE_REPORT_TOOL)


class Gateway(BaseHTTPRequestHandler):
    """스트림 요청에는 끝 이벤트까지 든 SSE 를, 비스트리밍 요청에는 `ANSWER` 의 상태와 캐시 읽기 수를 준다."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        SEEN.append({"path": self.path, "headers": dict(self.headers), "body": body})
        if body.get("stream") and first_text(body).startswith(HOLD):
            RELEASE.wait(5)
        if body.get("stream"):
            status, kind = 200, "text/event-stream"
            first, last = first_text(body), first_text({"messages": body["messages"][-1:]})
            data = (STREAM_REPORT if last.startswith(REPORT) else STREAM_TOOL if first.startswith(TOOL) else STREAM)
        else:
            status, kind = ANSWER["status"], "application/json"
            data = json.dumps({"type": "message", "stop_reason": "max_tokens",
                               "usage": {"input_tokens": 3, "cache_read_input_tokens": ANSWER["cache_read"],
                                         "output_tokens": 1}}).encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def turn(**changes) -> dict:
    """Claude Code 의 본 턴 꼴 — 세션 번호 · 캐시 표식 · 도구 · 적응형 생각 · 스트림."""
    payload = {"model": "claude-opus-5-5", "stream": True, "max_tokens": 64000,
               "metadata": {"user_id": json.dumps({"session_id": SESSION})},
               "thinking": {"type": "adaptive"}, "output_config": {"effort": "high"},
               "system": [{"type": "text", "text": "main agent", "cache_control": {"type": "ephemeral"}}],
               "tools": [{"name": "Read", "description": "read a file", "input_schema": {"type": "object"}}],
               "messages": [{"role": "user", "content": [{"type": "text", "text": "hi " * 50,
                                                          "cache_control": {"type": "ephemeral"}}]}]}
    payload.update(changes)
    return payload


def lane(envelope: str, system: str = "general-purpose lane", lane_id: str | None = None, parent: str = "") -> dict:
    """같은 세션의 서브에이전트 턴 — 같은 종류의 형제 레인은 system 이 같고 첫 메시지(봉투)만 다르다. 요청에는 레인 번호
    머리가 실린다(``send``). ``lane_id`` 를 안 주면 봉투마다 다른 번호다."""
    LANE_OF[envelope] = lane_id or f"a{abs(hash(envelope)):x}"
    PARENT_OF.pop(envelope, None)
    if parent:
        PARENT_OF[envelope] = parent      # 레인이 띄운 레인 — 요청에 부모 레인 번호 머리도 실린다
    return turn(system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": [{"type": "text", "text": envelope,
                                                        "cache_control": {"type": "ephemeral"}}]}])


def first_text(body: dict) -> str:
    messages = body.get("messages") or [{}]
    content = messages[0].get("content")
    return content if isinstance(content, str) else (content or [{}])[0].get("text", "")


class PickTests(unittest.TestCase):
    """층: 고르는 손 — 시계 없이 잰다. 기대값은 계약(간격마다 · 마지막 실제 요청 뒤 정해진 횟수까지)에서 온다."""

    def warmer(self, cycles=3):
        return proxy.CacheWarmer(cycles, 240.0)

    def test_pings_at_each_interval_and_stops_after_the_cycles(self):
        warmer = self.warmer()
        warmer.remember("k", SESSION, "/p", {}, b"{}", started=0.0)
        self.assertEqual(warmer.due(239.0), [])
        fired = []
        for now in (240.0, 480.0, 720.0, 960.0, 1200.0, 6000.0):
            for entry in warmer.due(now):
                fired.append(now)
                self.assertEqual(warmer.due(now + 1), [])   # 나가 있는 동안은 다시 안 고른다
                warmer.finish(entry, True, now)
        self.assertEqual(fired, [240.0, 480.0, 720.0])
        self.assertEqual(warmer.sessions(), 0)

    def test_a_real_request_postpones_and_restarts_the_count(self):
        warmer = self.warmer()
        warmer.remember("k", SESSION, "/p", {}, b"{}", started=0.0)
        [entry] = warmer.due(240.0)
        warmer.finish(entry, True, 240.0)
        warmer.touch("k", 400.0)                       # 실제 요청이 시작됐다
        self.assertEqual(warmer.due(480.0), [])
        warmer.remember("k", SESSION, "/p", {}, b"{}", started=400.0)   # 그 요청이 끝났다
        fired = []
        for now in (640.0, 880.0, 1120.0, 1360.0):
            for entry in warmer.due(now):
                fired.append(now)
                warmer.finish(entry, True, now)
        self.assertEqual(fired, [640.0, 880.0, 1120.0])

    def test_a_ping_that_read_no_cache_ends_the_conversation(self):
        warmer = self.warmer()
        warmer.remember("k", SESSION, "/p", {}, b"{}", started=0.0)
        [entry] = warmer.due(240.0)
        warmer.finish(entry, False, 240.0)
        self.assertEqual(warmer.due(480.0), [])
        self.assertEqual(warmer.sessions(), 0)

    def test_a_late_ping_result_does_not_touch_the_newer_request(self):
        warmer = self.warmer()
        warmer.remember("k", SESSION, "/p", {}, b"old", started=0.0)
        [stale] = warmer.due(240.0)
        warmer.remember("k", SESSION, "/p", {}, b"new", started=250.0)   # 데우기가 나가 있는 사이 실제 요청이 끝났다
        warmer.finish(stale, False, 240.0)
        [entry] = warmer.due(490.0)
        self.assertEqual(entry.body, b"new")

    def test_only_the_most_recent_conversations_are_kept(self):
        warmer = self.warmer()
        for index in range(proxy.CACHE_WARM_SESSIONS + 2):
            warmer.remember(f"k{index}", SESSION, "/p", {}, b"{}", started=float(index))
        self.assertEqual(warmer.sessions(), proxy.CACHE_WARM_SESSIONS)
        self.assertEqual({entry.key for entry in warmer.due(1000.0)},
                         {f"k{index}" for index in range(2, proxy.CACHE_WARM_SESSIONS + 2)})

    def test_when_full_the_conversation_cheapest_to_miss_leaves(self):
        # 기대값 — 자리가 넘치면 놓쳤을 때 다시 쓰는 양이 가장 작은 대화, 곧 몸이 가장 작은 대화가 빠지고, 크기가 같으면 최근 것이
        # 남는다. 레인을 기다리는 메인과 자식을 기다리는 부모는 가장 오래 쉬어도 그 뒤에 끝난 작은 레인들에 안 밀린다
        warmer = self.warmer()
        warmer.remember("main", SESSION, "/p", {}, b"m" * 4000, started=0.0)
        warmer.remember("parent", SESSION, "/p", {}, b"p" * 3000, started=1.0)
        lanes = proxy.CACHE_WARM_SESSIONS + 4
        for index in range(lanes):
            warmer.remember(f"lane{index}", SESSION, "/p", {}, b"l" * 1500, started=2.0 + index)
        kept = {entry.key for entry in warmer.due(1000.0)}
        self.assertEqual(len(kept), proxy.CACHE_WARM_SESSIONS)
        self.assertLessEqual({"main", "parent"}, kept)
        self.assertEqual(kept - {"main", "parent"},
                         {f"lane{index}" for index in range(lanes - proxy.CACHE_WARM_SESSIONS + 2, lanes)})
        warmer.remember("late-small", SESSION, "/p", {}, b"s" * 100, started=500.0)   # 새로 온 것이 가장 낮으면 그것이 빠진다
        self.assertNotIn("late-small", {entry.key for entry in warmer.due(2000.0)})

    def test_alive_is_the_life_already_secured_and_outlasts_the_last_ping(self):
        # 기대값 — 캐시는 마지막으로 읽힌 때(실제 요청의 시작 · 캐시를 읽힌 데우기의 시작)에서 수명만큼 산다. 아직 안 나간 데우기는
        # 셈에 안 넣는다 — 그 데우기가 지면 그 사이 「살았다」가 거짓이 된다
        ttl = 300.0
        warmer = proxy.CacheWarmer(2, 240.0, ttl)
        warmer.remember("k", SESSION, "/p", {}, b"{}", started=0.0, message_id="msg_a")
        self.assertEqual(warmer.alive(10.0), {"msg_a": ttl})
        [entry] = warmer.due(240.0)
        warmer.finish(entry, True, 240.0)
        self.assertEqual(warmer.alive(250.0), {"msg_a": 240.0 + ttl})
        [entry] = warmer.due(480.0)
        warmer.finish(entry, True, 480.0)                # 횟수를 다 써 데울 목록에서 빠진다
        self.assertEqual(warmer.sessions(), 0)
        self.assertEqual(warmer.alive(700.0), {"msg_a": 480.0 + ttl})   # 마지막 데우기가 확보한 수명은 남는다
        self.assertEqual(warmer.alive(480.0 + ttl), {})                 # 그 끝이 지나면 걷힌다

    def test_a_conversation_whose_client_process_ended_is_dropped_not_warmed(self):
        # 기대값 — 창을 닫은 대화는 돌아올 길이 없다. 프로세스를 모르는 대화(0)는 지금처럼 정해진 횟수까지 데운다
        warmer = proxy.CacheWarmer(3, 240.0, 300.0)
        warmer.remember("closed", SESSION, "/p", {}, b"{}", started=0.0, message_id="msg_c", pid=111)
        warmer.remember("open", SESSION, "/p", {}, b"{}", started=0.0, pid=222)
        warmer.remember("unknown", SESSION, "/p", {}, b"{}", started=0.0)
        gone = lambda pid: pid == 111
        self.assertEqual(warmer.due(100.0, gone), [])                  # 차례 전에는 안 본다
        self.assertEqual({entry.key for entry in warmer.due(240.0, gone)}, {"open", "unknown"})
        self.assertEqual(warmer.sessions(), 2)
        self.assertEqual(warmer.alive(250.0), {"msg_c": 300.0})        # 확보한 수명은 그 끝까지 둔다

    def test_process_gone_tells_a_running_process_from_an_ended_one(self):
        if os.name != "nt":
            self.skipTest("Windows 에서만 프로세스를 본다")
        self.assertFalse(proxy.process_gone(os.getpid()))
        self.assertFalse(proxy.process_gone(0))
        child = subprocess.Popen([sys.executable, "-I", "-c", "pass"])
        child.wait()
        self.assertTrue(proxy.process_gone(child.pid))

    def test_alive_drops_what_is_not_known_to_be_alive(self):
        warmer = proxy.CacheWarmer(3, 240.0, 300.0)
        warmer.remember("k", SESSION, "/p", {}, b"{}", started=0.0, message_id="msg_a")
        [entry] = warmer.due(240.0)
        warmer.finish(entry, False, 240.0)               # 캐시를 못 읽힌 데우기 — 이미 사라진 캐시다
        self.assertEqual(warmer.alive(250.0), {})
        warmer.remember("j", SESSION, "/p", {}, b"{}", started=300.0, message_id="msg_b")
        warmer.forget("j")                               # 같은 대화의 실제 요청이 졌다
        self.assertEqual(warmer.alive(310.0), {})
        warmer.remember("i", SESSION, "/p", {}, b"{}", started=400.0, message_id='msg_"},x')
        self.assertEqual(warmer.alive(410.0), {})        # /health 를 셸로 가르는 쪽이 못 읽는 글자는 안 싣는다
        warmer.remember("h", SESSION, "/p", {}, b"{}", started=500.0)
        self.assertEqual(warmer.alive(510.0), {})        # 응답 id 를 모르면 짚을 길이 없다

    def test_what_is_warmed_and_what_the_ping_carries(self):
        body = json.dumps(turn()).encode()
        big = proxy.CACHE_WARM_MIN_BYTES
        self.assertTrue(proxy.cache_warm_candidate(SESSION, turn(), big))
        self.assertFalse(proxy.cache_warm_candidate(SESSION, turn(), big - 1))                 # 작은 몸
        self.assertFalse(proxy.cache_warm_candidate("", turn(), big))                          # 세션을 모른다
        self.assertFalse(proxy.cache_warm_candidate(
            SESSION, turn(thinking={"type": "enabled", "budget_tokens": 4000}), big))          # 예산 꼴은 400 이다
        bare = turn(system="plain", messages=[{"role": "user", "content": "hi"}])
        self.assertFalse(proxy.cache_warm_candidate(SESSION, bare, big))                       # 캐시 표식이 없다
        sent = json.loads(proxy.cache_warm_body(body))
        self.assertEqual((sent["max_tokens"], sent["stream"]), (1, False))
        self.assertEqual({key: value for key, value in sent.items() if key not in ("max_tokens", "stream")},
                         {key: value for key, value in turn().items() if key not in ("max_tokens", "stream")})
        self.assertIsNone(proxy.cache_warm_body(b"not json"))
        self.assertNotEqual(proxy.cache_warm_key(SESSION, turn()),
                            proxy.cache_warm_key(SESSION, turn(system="subagent")))            # 서브에이전트는 다른 대화다

    def test_sibling_lanes_are_different_conversations_and_a_next_turn_is_the_same_one(self):
        # 기대값 — 대화는 한 대화 안에서 안 바뀌는 첫 메시지로 갈린다. 같은 세션 · 같은 system 의 형제 레인은 봉투(첫 메시지)가
        # 다르다. 같은 대화의 다음 턴은 뒤에 메시지가 붙고 캐시 표식이 마지막 메시지로 옮겨 갈 뿐이다
        first = lane("envelope A")
        self.assertNotEqual(proxy.cache_warm_key(SESSION, first), proxy.cache_warm_key(SESSION, lane("envelope B")))
        later = lane("envelope A")
        later["messages"] = [{"role": "user", "content": [{"type": "text", "text": "envelope A"}]},
                             {"role": "assistant", "content": [{"type": "text", "text": "working"}]},
                             {"role": "user", "content": [{"type": "text", "text": "go on",
                                                           "cache_control": {"type": "ephemeral"}}]}]
        self.assertEqual(proxy.cache_warm_key(SESSION, first), proxy.cache_warm_key(SESSION, later))
        # 레인 번호가 다르면 봉투가 같아도(같은 봉투를 두 번 띄웠다), 메인의 system · 첫 메시지를 물려받아도(포크) 다른 대화다
        self.assertNotEqual(proxy.cache_warm_key(SESSION, first, "a1"), proxy.cache_warm_key(SESSION, first, "a2"))
        self.assertNotEqual(proxy.cache_warm_key(SESSION, turn()), proxy.cache_warm_key(SESSION, turn(), "a1"))
        self.assertEqual(proxy.cache_warm_key(SESSION, first, "a1"), proxy.cache_warm_key(SESSION, later, "a1"))

    def test_only_the_main_and_a_lane_waiting_on_a_tool_stay_to_be_warmed(self):
        # 기대값 — 사람이 안 보낸 요청은 반드시 돌아올 대화에만 나간다. 메인은 턴을 끝내도 남고(레인을 기다린다), 레인은 도구
        # 결과를 기다리며 멈췄을 때만 남는다 — 턴을 끝냈거나 보고 도구만 부르고 멈춘 레인은 끝난 것이다
        holds, report = proxy.cache_warm_holds, proxy.LANE_REPORT_TOOL
        self.assertTrue(holds("", "end_turn", ()))
        self.assertTrue(holds("", "tool_use", (report,)))
        self.assertTrue(holds("a1", "tool_use", ("Agent",)))          # 자식 레인을 앞에서 기다린다
        self.assertTrue(holds("a1", "tool_use", ("Bash", report)))   # 보고와 함께 다른 도구도 불렀다 — 그 결과를 기다린다
        self.assertTrue(holds("a1", "tool_use", ()))                 # 부른 도구를 못 읽었다 — 기다리는 쪽으로 본다
        self.assertFalse(holds("a1", "end_turn", ()))
        self.assertFalse(holds("a1", "tool_use", (report,)))
        self.assertFalse(holds("a1", "max_tokens", ("Agent",)))
        self.assertTrue(holds("a1", "none", ()))                     # 멈춘 까닭을 못 읽었다 — 기다리는 쪽으로 본다
        self.assertTrue(holds("a1", "", ()))
        # 러너가 띄운 `claude -p` 의 대화는 레인과 같다 — 답하고 끝났으면 안 담고, 도구 결과를 기다리면 담는다
        self.assertFalse(holds("", "end_turn", (), runner=True))
        self.assertFalse(holds("", "tool_use", (report,), runner=True))
        self.assertTrue(holds("", "tool_use", ("Agent",), runner=True))
        self.assertTrue(holds("", "", (), runner=True))

    def test_a_lanes_request_restarts_the_count_of_those_waiting_for_it(self):
        # 기대값 — 기다리는 쪽(메인 · 그 레인을 띄운 부모 레인)은 자식이 요청을 보내는 동안 횟수를 다 쓰지 않고, 자식이 조용해지면
        # 그 뒤 정해진 횟수에서 멈춘다. 그 자식의 부모가 아닌 레인과 다른 세션의 대화는 제 횟수대로 멈춘다
        warmer = self.warmer()
        warmer.remember("main", SESSION, "/p", {}, b"m", started=0.0)
        warmer.remember("parent", SESSION, "/p", {}, b"p", started=0.0, lane_id="a1")
        warmer.remember("uncle", SESSION, "/p", {}, b"u", started=0.0, lane_id="a2")
        warmer.remember("elsewhere", "another-session", "/p", {}, b"e", started=0.0)
        fired: dict[str, list[float]] = {}
        for now in (240.0, 480.0, 720.0, 960.0, 1200.0, 1440.0, 1680.0, 1920.0):
            if now <= 960.0:
                warmer.lane_active(SESSION, "a1")        # a1 이 띄운 레인이 요청을 보냈다
            for entry in warmer.due(now):
                fired.setdefault(entry.key, []).append(now)
                warmer.finish(entry, True, now)
        self.assertEqual(fired["uncle"], [240.0, 480.0, 720.0])
        self.assertEqual(fired["elsewhere"], [240.0, 480.0, 720.0])
        self.assertEqual(fired["main"], [240.0, 480.0, 720.0, 960.0, 1200.0, 1440.0])   # 마지막 요청(960) 뒤 세 번째에서 멈춘다
        self.assertEqual(fired["parent"], fired["main"])
        self.assertEqual(warmer.sessions(), 0)

    def test_only_the_latest_body_of_the_main_is_kept_going_by_its_lanes(self):
        # 기대값 — 압축했거나 모델을 바꾼 메인의 옛 몸(열쇠가 달라 목록에 남는다)은 다시 안 이어진다. 레인이 요청을 보내도 옛 몸은
        # 제 횟수에서 멈추고, 가장 나중에 담긴 몸만 이어 데워진다
        warmer = self.warmer()
        warmer.remember("main-before-compact", SESSION, "/p", {}, b"old" * 100, started=0.0)
        warmer.remember("main", SESSION, "/p", {}, b"new", started=10.0)
        fired: dict[str, int] = {}
        for now in (250.0, 490.0, 730.0, 970.0, 1210.0):
            warmer.lane_active(SESSION)
            for entry in warmer.due(now):
                fired[entry.key] = fired.get(entry.key, 0) + 1
                warmer.finish(entry, True, now)
        self.assertEqual(fired, {"main-before-compact": 3, "main": 5})

    def test_a_request_not_held_takes_the_old_body_away_and_keeps_the_secured_life(self):
        warmer = proxy.CacheWarmer(3, 240.0, 300.0)
        warmer.remember("lane", SESSION, "/p", {}, b"waiting", started=0.0, message_id="msg_a")
        warmer.remember("main", SESSION, "/p", {}, b"main", started=1.0, message_id="msg_m")
        warmer.remember("lane", SESSION, "/p", {}, b"stopped", started=100.0, message_id="msg_b", hold=False)
        self.assertEqual([entry.key for entry in warmer.due(1000.0)], ["main"])
        self.assertEqual(warmer.alive(110.0)["msg_b"], 400.0)


class HandlerTests(unittest.TestCase):
    """층: 핸들러 연결 — 끝까지 받은 본 턴만 담고, 데우기는 상류로 나간 그 몸 · 그 머리로 간다."""

    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix="pgpt-warm-")
        proxy.LOG_PATH = Path(cls.work.name) / "proxy.log"
        proxy.CACHE_WARM_MIN_BYTES = 10
        cls.gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
        proxy._UPSTREAM = proxy.UpstreamTarget(f"http://127.0.0.1:{cls.gateway.server_port}")
        # 모델 목록 조회는 끈다 — 대시 이름이 진짜 게이트웨이 주소로 목록을 물으러 간다
        proxy._GATEWAY_MODELS = proxy.GatewayModelList(f"http://127.0.0.1:{cls.gateway.server_port}", ttl=0, retry=1, timeout=1)
        cls.server = proxy.ProxyServer(("127.0.0.1", 0), proxy.ProxyHandler)
        for server in (cls.gateway, cls.server):
            threading.Thread(target=server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        for server in (cls.server, cls.gateway):
            server.shutdown()
            server.server_close()
        cls.work.cleanup()

    def setUp(self):
        SEEN.clear()
        LANE_OF.clear()
        PARENT_OF.clear()
        RUNNER_OF.clear()
        ANSWER.update(status=200, cache_read=5000)
        proxy._WARMER = proxy.CacheWarmer(3, 240.0)

    def send(self, payload):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        headers = {"Content-Type": "application/json", "Authorization": "Bearer test-key-xxxx"}
        if first_text(payload) in LANE_OF:
            headers[LANE_ID_HEADER] = LANE_OF[first_text(payload)]
        if first_text(payload) in PARENT_OF:
            headers[LANE_PARENT_HEADER] = PARENT_OF[first_text(payload)]
        if first_text(payload) in RUNNER_OF:
            headers[RUNNER_HEADER] = "claude-background"
        try:
            conn.request("POST", "/gpgpta01-gpt/v1/messages?beta=true", json.dumps(payload).encode(), headers)
            response = conn.getresponse()
            response.read()
            deadline = time.monotonic() + 2
            while proxy.stats()["active_requests"] and time.monotonic() < deadline:
                time.sleep(0.01)
            return response.status
        finally:
            conn.close()

    def ping_due(self):
        """간격이 지난 것으로 치고 고른 대화를 그 자리에서 데운다 — 고른 수를 낸다."""
        picked = proxy._WARMER.due(time.monotonic() + 240.0)
        for entry in picked:
            proxy.cache_warm_ping(proxy._WARMER, entry)
        return len(picked)

    def test_a_finished_turn_is_warmed_with_the_upstream_body_and_one_token(self):
        self.assertEqual(self.send(turn(temperature=0.3)), 200)
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 1)
        before = proxy.stats()["cache_warm_sent"]
        self.assertEqual(self.ping_due(), 1)
        real, warm = SEEN
        self.assertEqual((warm["body"]["max_tokens"], warm["body"]["stream"]), (1, False))
        for key in ("model", "system", "tools", "messages", "thinking", "output_config", "metadata"):
            self.assertEqual(warm["body"][key], real["body"][key], key)   # 상류로 나간 몸 그대로다
        self.assertNotIn("temperature", warm["body"])
        self.assertEqual(warm["path"], real["path"])
        self.assertEqual(warm["headers"]["Authorization"], "Bearer test-key-xxxx")
        self.assertEqual(proxy.stats()["cache_warm_sent"], before + 1)
        self.assertRegex(proxy.LOG_PATH.read_text(encoding="utf-8"),
                         r"cache warm session=aaaaaaaa conv=[0-9a-f]{8} HTTP 200 cache_read=5000")

    def test_the_stored_turn_knows_the_client_process_that_sent_it(self):
        if os.name != "nt":
            self.skipTest("Windows 에서만 접속의 프로세스를 찾는다")
        self.assertEqual(self.send(turn()), 200)
        [entry] = proxy._WARMER._entries
        self.assertEqual(entry.pid, os.getpid())

    def test_health_names_the_response_whose_cache_is_kept_alive(self):
        # 이어 묻기 값 훅이 읽는 칸 — 응답 id 는 대화 기록의 마지막 assistant 줄이 드는 그 id(스트림 message_start 의 message.id)다
        self.send(turn())
        status, health = self.health()
        self.assertEqual(status, 200)
        alive = health["cache_warm_alive_until"]
        self.assertEqual(list(alive), ["m"])
        self.assertLessEqual(alive["m"], time.time() + proxy.GATEWAY_CACHE_TTL_SEC)
        self.assertGreater(alive["m"], time.time() + proxy.GATEWAY_CACHE_TTL_SEC - 10)
        ANSWER.update(cache_read=0)
        self.ping_due()                                  # 캐시를 못 읽힌 데우기 뒤에는 살았다고 내지 않는다
        self.assertEqual(self.health()[1]["cache_warm_alive_until"], {})

    def health(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request("GET", "/health")
            response = conn.getresponse()
            return response.status, json.loads(response.read())
        finally:
            conn.close()

    def test_three_pings_then_nothing_more_goes_out(self):
        self.send(turn())
        self.assertEqual([self.ping_due() for _ in range(5)], [1, 1, 1, 0, 0])
        self.assertEqual(len(SEEN), 1 + 3)
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 0)

    def test_a_ping_that_reads_no_cache_or_fails_stops_the_conversation(self):
        for answer in ({"status": 200, "cache_read": 0}, {"status": 500, "cache_read": 5000}):
            SEEN.clear()
            ANSWER.update(answer)
            self.send(turn())
            before = proxy.stats()["cache_warm_failed"]
            self.assertEqual([self.ping_due() for _ in range(3)], [1, 0, 0], answer)
            self.assertEqual(proxy.stats()["cache_warm_failed"], before + 1)
            self.assertEqual(len(SEEN), 1 + 1)

    def test_side_calls_and_small_or_budget_turns_are_not_warmed(self):
        self.send(turn(stream=False, max_tokens=64))                       # 자동 모드 분류기 꼴의 비스트리밍 곁 호출
        self.send(turn(thinking={"type": "enabled", "budget_tokens": 4000}))
        self.send(turn(metadata={}))                                       # 세션을 모른다
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 0)
        self.assertEqual(self.ping_due(), 0)

    def shape_lines(self, *payloads):
        before = len(proxy.LOG_PATH.read_text(encoding="utf-8")) if proxy.LOG_PATH.exists() else 0
        for payload in payloads:
            self.send(payload)
        added = proxy.LOG_PATH.read_text(encoding="utf-8")[before:]
        return [line for line in added.splitlines() if "cache warm shape " in line]

    def test_a_new_conversation_leaves_one_shape_line_without_secrets_or_message_text(self):
        # 처음 보는 대화는 요청의 꼴을 한 줄 남긴다 — 칸의 이름과 갈래를 가를 만한 값만, 인증 값과 메시지의 글은 없다.
        # 같은 대화의 다음 요청에는 또 안 남긴다
        shapes = self.shape_lines(lane("envelope SHAPE-PROBE"), lane("envelope SHAPE-PROBE"))
        self.assertEqual(len(shapes), 1, shapes)
        line = shapes[0]
        self.assertRegex(line, r"cache warm shape session=aaaaaaaa conv=[0-9a-f]{8} bytes=\d+ model=claude-opus-5\S5 effort=high "
                               r"thinking=adaptive header_values=\[x-claude-code-agent-id=a[0-9a-f]+\] user_values=\[\] "
                               r"tools=1 built_in=Read mcp=0 max_tokens=\d+ headers=\S*authorization\S* ")
        self.assertIn(" user_id=session_id ", line)
        self.assertIn('system_heads=["general-purpose lane"]', line)
        self.assertNotIn("test-key-xxxx", line)             # 인증 값
        self.assertNotIn("SHAPE-PROBE", line)               # 첫 메시지의 글
        self.assertNotIn(SESSION, line)                     # 세션 번호는 앞 8자만

    def test_a_different_mark_under_the_same_key_leaves_another_shape_line(self):
        # 한 열쇠를 나눠 쓰는 다른 대화(system · 첫 메시지 · 레인 번호가 다 같은 둘)는 갈래 값이 다르면 줄을 한 번 더 남긴다 —
        # 그 줄이 둘을 가를 신호의 재료다. 같은 값으로 다시 오면 안 남긴다
        parent = lane("envelope SHARED")
        fork = dict(lane("envelope SHARED"), output_config={"effort": "low"})
        shapes = self.shape_lines(parent, fork, parent, fork)
        self.assertEqual([("effort=high" in line, "effort=low" in line) for line in shapes], [(True, False), (False, True)], shapes)
        self.assertEqual(len({line.split(" conv=")[1].split()[0] for line in shapes}), 1)   # 둘은 한 열쇠다

    def test_sibling_lanes_waiting_on_a_tool_are_each_warmed(self):
        # 같은 세션 · 같은 system 의 형제 레인 둘이 도구 결과를 기다리면 데우기도 둘이 저마다의 몸으로 나간다
        self.send(lane(TOOL + " envelope A"))
        self.send(lane(TOOL + " envelope B"))
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 2)
        self.assertEqual(self.ping_due(), 2)
        self.assertEqual(sorted(first_text(seen["body"]) for seen in SEEN if not seen["body"]["stream"]),
                         [TOOL + " envelope A", TOOL + " envelope B"])

    def test_a_stopped_lane_is_not_warmed_and_only_the_main_is(self):
        # 기대값 — 멈춘 레인(턴을 끝냈다 · 보고 도구만 부르고 멈췄다)에는 사람이 안 보낸 요청이 안 나간다. 메인에는 나간다.
        # 멈춘 레인이 방금 읽힌 캐시의 수명은 /health 에 남아, 그 안의 이어 묻기를 이어 묻기 훅이 식었다고 막지 않는다
        self.send(lane("envelope A"))                               # 턴을 끝낸 레인
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 0)
        self.assertEqual(list(self.health()[1]["cache_warm_alive_until"]), ["m"])
        self.send(lane(REPORT + " envelope B"))                     # 보고 도구로 멈춘 레인
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 0)
        self.send(turn())
        SEEN.clear()
        self.assertEqual(self.ping_due(), 1)
        self.assertEqual([first_text(seen["body"]) for seen in SEEN], ["hi " * 50])
        self.assertRegex(proxy.LOG_PATH.read_text(encoding="utf-8"),
                         r"cache warm skip session=aaaaaaaa conv=[0-9a-f]{8} lane stopped stop_reason=tool_use id=m")

    def test_a_lane_that_waited_and_then_stopped_leaves_the_list(self):
        # 도구 결과를 기다리던 레인의 몸은 그 레인이 일을 마치면 걷힌다 — 끝난 레인의 옛 몸에 데우기가 안 나간다
        waiting = lane(TOOL + " envelope A")
        self.send(waiting)
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 1)
        done = lane(TOOL + " envelope A")
        done["messages"] = [{"role": "user", "content": [{"type": "text", "text": TOOL + " envelope A"}]},
                            {"role": "assistant", "content": [{"type": "text", "text": "working"}]},
                            {"role": "user", "content": [{"type": "text", "text": REPORT + " child came back",
                                                          "cache_control": {"type": "ephemeral"}}]}]
        self.send(done)
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 0)
        self.assertEqual(self.ping_due(), 0)

    def test_a_stopped_lane_that_shares_the_mains_prefix_leaves_the_main_in_place(self):
        # 메인의 system · 첫 메시지를 그대로 물려받는 레인(포크)이 멈춰도 메인의 몸은 남는다 — 레인 번호가 둘을 가른다
        self.send(turn())
        LANE_OF[first_text(turn())] = "afork1"
        self.send(turn())
        del LANE_OF[first_text(turn())]
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 1)
        SEEN.clear()
        self.assertEqual(self.ping_due(), 1)
        self.assertNotIn(LANE_ID_HEADER, {name.lower() for name in SEEN[0]["headers"]})

    def test_the_main_is_warmed_for_as_long_as_its_lanes_keep_sending(self):
        # 레인이 요청을 보내는 동안 메인은 세 번에서 안 끊긴다 — 레인이 조용해지면 그 뒤 세 번째에서 멈춘다. 레인은 턴을 끝내
        # 스스로는 안 담긴다(데우기는 메인 것뿐이다)
        self.send(turn())
        while_running = []
        for _ in range(5):
            self.send(lane("envelope A"))
            while_running.append(self.ping_due())
        self.assertEqual(while_running, [1, 1, 1, 1, 1])
        self.assertEqual([self.ping_due() for _ in range(4)], [1, 1, 0, 0])
        self.assertEqual({first_text(seen["body"]) for seen in SEEN if not seen["body"]["stream"]}, {"hi " * 50})

    def test_a_parent_lane_is_warmed_for_as_long_as_its_own_child_keeps_sending(self):
        # 자식을 앞에서 기다리는 짓기 레인은 그 자식(부모 레인 번호 머리가 이 레인을 댄다)이 요청을 보내는 동안 세 번에서 안
        # 끊긴다. 곁에서 기다리는 다른 레인은 제 횟수에서 멈춘다 — 그 자식의 부모가 아니다
        build, other = TOOL + " build envelope", TOOL + " other envelope"
        self.send(lane(build, lane_id="abuild"))
        self.send(lane(other, lane_id="aother"))
        warmed = []
        for _ in range(5):
            self.send(lane("review envelope", system="code-review lane", parent="abuild"))
            SEEN.clear()
            self.ping_due()
            warmed.append(sorted(first_text(seen["body"]) for seen in SEEN))
        self.assertEqual(warmed, [[build, other]] * 3 + [[build]] * 2)

    def test_the_main_and_a_waiting_parent_keep_their_place_while_many_lanes_run(self):
        # 메인이 레인을 띄우고 턴을 끝내고(end_turn), 짓기 레인이 리뷰 자식을 기다리며 도구 호출에서 멈춘 뒤, 자리 수보다 많은
        # 자식 레인이 도구 호출에서 멈춰 있다. 메인과 부모는 몸이 자식보다 크다 — 메인과 부모는 봉투 위에 쌓인 대화를,
        # 자식은 봉투 하나를 든다
        self.send(turn(messages=[{"role": "user", "content": [{"type": "text", "text": "main " * 4000,
                                                               "cache_control": {"type": "ephemeral"}}]}]))
        self.send(lane(TOOL + " build envelope " + "b" * 12000))
        for index in range(proxy.CACHE_WARM_SESSIONS + 2):
            self.send(lane(f"{TOOL} review envelope {index}", system="code-review lane"))
        self.assertEqual(proxy.stats()["cache_warm_sessions"], proxy.CACHE_WARM_SESSIONS)
        SEEN.clear()
        self.ping_due()
        warmed = [first_text(seen["body"])[:20] for seen in SEEN]   # 실패 글이 몸 전체를 안 찍게 머리만 견준다
        self.assertIn(("main " * 4000)[:20], warmed)
        self.assertIn((TOOL + " build envelope ")[:20], warmed)

    def test_a_next_turn_through_the_handler_takes_the_same_place(self):
        # 처리기가 몸을 고친 뒤 짓는 열쇠로도 다음 턴은 같은 대화다 — 데울 몸은 다음 턴의 것 하나
        self.send(lane(TOOL + " envelope A"))
        later = lane(TOOL + " envelope A")
        later["messages"] = [{"role": "user", "content": [{"type": "text", "text": TOOL + " envelope A"}]},
                             {"role": "assistant", "content": [{"type": "text", "text": "working"}]},
                             {"role": "user", "content": [{"type": "text", "text": "go on",
                                                           "cache_control": {"type": "ephemeral"}}]}]
        self.send(later)
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 1)
        self.assertEqual(self.ping_due(), 1)
        self.assertEqual(len(SEEN[-1]["body"]["messages"]), 3)

    def idle_while_running(self, idle: dict, running: dict) -> list[str]:
        """``idle`` 이 끝난 뒤 ``running`` 이 도는 동안 ``idle`` 의 간격이 차면 데울 대화의 첫 메시지들. 간격은 ``idle`` 이 끝난 때부터
        잰다 — ``running`` 이 그보다 늦게 시작해, 그 시작이 ``idle`` 을 미루면 아직 간격이 안 찬 것으로 보인다."""
        self.send(idle)
        idle_done = time.monotonic()
        time.sleep(0.3)
        RELEASE.clear()
        worker = threading.Thread(target=self.send, args=(running,), daemon=True)
        worker.start()
        try:
            deadline = time.monotonic() + 3
            while not any(first_text(seen["body"]) == first_text(running) for seen in SEEN):
                self.assertLess(time.monotonic(), deadline, "도는 레인이 게이트웨이에 안 닿았다")
                time.sleep(0.01)
            picked = proxy._WARMER.due(idle_done + proxy._WARMER.interval_sec + 0.1)
            for entry in picked:
                proxy._WARMER.finish(entry, True, idle_done)
            return [first_text(json.loads(entry.body)) for entry in picked]
        finally:
            RELEASE.set()
            worker.join(5)

    def test_a_lane_waiting_on_a_tool_is_warmed_while_its_sibling_runs(self):
        self.assertEqual(self.idle_while_running(lane(TOOL + " envelope A"), lane(HOLD + " envelope B")),
                         [TOOL + " envelope A"])

    def test_a_parent_lane_waiting_on_its_child_is_warmed_while_the_child_runs(self):
        # 자식 레인을 앞에서 기다리는 부모 레인 — 도구 호출에서 멈춰 있고, 자식의 요청이 부모의 데우기를 미루지 않는다
        self.assertEqual(self.idle_while_running(lane(TOOL + " build envelope"),
                                                 lane(HOLD + " review envelope", system="code-review lane")),
                         [TOOL + " build envelope"])

    def test_an_idle_main_is_warmed_while_a_lane_runs(self):
        self.assertEqual(self.idle_while_running(turn(), lane(HOLD + " envelope A")), ["hi " * 50])

    def notify(self, notice) -> int:
        """러너의 알림 하나를 프록시의 로컬 문(`/runner-wait`)에 보낸다 — 러너(`runner_common.py`)와 맺은 길과 몸 꼴이라 글자로
        적는다. 상태 코드를 낸다."""
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            body = notice if isinstance(notice, bytes) else json.dumps(notice).encode()
            conn.request("POST", "/runner-wait", body, {"Content-Type": "application/json"})
            response = conn.getresponse()
            response.read()
            return response.status
        finally:
            conn.close()

    def test_a_waiting_main_is_warmed_while_its_runner_runs_and_stops_three_pings_after(self):
        # 기대값 — 러너에 맡기고 기다리는 메인은 러너가 알려 오는 동안 세 번에서 안 끊기고, 알림이 멎으면(러너가 끝났다 · 죽었다)
        # 그 뒤 세 번째에서 멈춘다. 다른 세션의 대화는 제 횟수대로 멈춘다. 알림은 상류로 안 나간다
        self.send(turn())
        other = turn(metadata={"user_id": json.dumps({"session_id": "bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeeeee"})},
                     messages=[{"role": "user", "content": [{"type": "text", "text": "other session",
                                                             "cache_control": {"type": "ephemeral"}}]}])
        self.send(other)
        before = proxy.stats()["runner_waits"]
        warmed = []
        for _ in range(5):
            self.assertEqual(self.notify({"session": SESSION, "lane": ""}), 200)
            SEEN.clear()
            self.ping_due()
            warmed.append(sorted(first_text(seen["body"]) for seen in SEEN))
        self.assertEqual(warmed, [["hi " * 50, "other session"]] * 3 + [["hi " * 50]] * 2)
        self.assertEqual([self.ping_due() for _ in range(4)], [1, 1, 0, 0])   # 마지막 알림 뒤 세 번째에서 멈춘다
        self.assertEqual(proxy.stats()["runner_waits"], before + 5)
        self.assertRegex(proxy.LOG_PATH.read_text(encoding="utf-8"), r"runner wait session=aaaaaaaa lane=- restarted=1")

    def test_a_waiting_lane_is_warmed_while_the_runner_it_called_runs(self):
        # 기대값 — 러너를 부른 레인(알림의 lane)과 그 세션의 메인은 이어지고, 곁에서 기다리는 다른 레인은 제 횟수에서 멈춘다
        caller, other = TOOL + " caller envelope", TOOL + " other envelope"
        self.send(turn())
        self.send(lane(caller, lane_id="acaller"))
        self.send(lane(other, lane_id="aother"))
        warmed = []
        for _ in range(5):
            self.notify({"session": SESSION, "lane": "acaller"})
            SEEN.clear()
            self.ping_due()
            warmed.append(sorted(first_text(seen["body"]) for seen in SEEN))
        self.assertEqual(warmed, [sorted([caller, other, "hi " * 50])] * 3 + [sorted([caller, "hi " * 50])] * 2)

    def test_a_malformed_runner_notice_is_refused_and_restarts_nothing(self):
        # 꼴이 틀린 알림(세션 번호가 uuid 가 아니다 · 레인 번호에 경로 글자 · 몸이 JSON 이 아니다)은 400 이고 아무것도 안 잇는다
        self.send(turn())
        for bad in ({"session": "not-a-session", "lane": ""}, {"session": SESSION, "lane": "../x"},
                    {"session": SESSION, "lane": 7}, {"lane": ""}, b"not json", [SESSION]):
            self.assertEqual(self.notify(bad), 400, bad)
        self.assertEqual([self.ping_due() for _ in range(4)], [1, 1, 1, 0])

    def test_a_runner_started_conversation_is_not_warmed_after_it_answers_but_a_persons_own_is(self):
        # 기대값 — 러너가 띄운 `claude -p`(요청에 러너 머리)가 답하고 끝나면 데울 목록에 안 남고, 확보한 수명은 /health 에 남는다.
        # 도구 결과를 기다리는 동안은 레인처럼 남는다. 사람이 손으로 띄운 `claude -p`(머리 없음)는 지금처럼 메인으로 남는다
        RUNNER_OF.add("hi " * 50)
        self.send(turn())
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 0)
        self.assertEqual(list(self.health()[1]["cache_warm_alive_until"]), ["m"])
        self.assertRegex(proxy.LOG_PATH.read_text(encoding="utf-8"),
                         r"cache warm skip session=aaaaaaaa conv=[0-9a-f]{8} runner stopped stop_reason=end_turn id=m")
        waiting = turn(messages=[{"role": "user", "content": [{"type": "text", "text": TOOL + " runner job",
                                                               "cache_control": {"type": "ephemeral"}}]}])
        RUNNER_OF.add(TOOL + " runner job")
        self.send(waiting)
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 1)
        RUNNER_OF.clear()
        self.send(turn())
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 2)

    def test_a_turn_that_stops_being_warmable_drops_the_stored_one(self):
        self.send(turn())
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 1)
        self.send(turn(stream=False))                                      # 같은 대화가 비스트리밍으로 물러섰다
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
