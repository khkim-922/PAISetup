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


def event(kind, **fields):
    return ("event: " + kind + "\ndata: " + json.dumps({"type": kind, **fields}) + "\n\n").encode()


STREAM = (event("message_start", message={"id": "m", "usage": {"input_tokens": 0, "output_tokens": 0}})
          + event("message_delta", delta={"stop_reason": "end_turn"},
                  usage={"input_tokens": 9, "cache_read_input_tokens": 5000, "output_tokens": 6})
          + event("message_stop"))


class Gateway(BaseHTTPRequestHandler):
    """스트림 요청에는 끝 이벤트까지 든 SSE 를, 비스트리밍 요청에는 `ANSWER` 의 상태와 캐시 읽기 수를 준다."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        SEEN.append({"path": self.path, "headers": dict(self.headers), "body": body})
        if body.get("stream"):
            status, kind, data = 200, "text/event-stream", STREAM
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
        ANSWER.update(status=200, cache_read=5000)
        proxy._WARMER = proxy.CacheWarmer(3, 240.0)

    def send(self, payload):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request("POST", "/gpgpta01-gpt/v1/messages?beta=true", json.dumps(payload).encode(),
                         {"Content-Type": "application/json", "Authorization": "Bearer test-key-xxxx"})
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
        self.assertIn("cache warm session=aaaaaaaa HTTP 200 cache_read=5000", proxy.LOG_PATH.read_text(encoding="utf-8"))

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

    def test_a_turn_that_stops_being_warmable_drops_the_stored_one(self):
        self.send(turn())
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 1)
        self.send(turn(stream=False))                                      # 같은 대화가 비스트리밍으로 물러섰다
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
