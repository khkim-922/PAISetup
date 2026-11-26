"""v23 streaming regressions against a local gateway, with no company credentials."""
from __future__ import annotations

import http.client
import importlib.util
import io
import json
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("proxy", ROOT / "opus5_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)


def event(kind, **fields):
    return ("event: " + kind + "\ndata: " + json.dumps({"type": kind, **fields}, ensure_ascii=False) + "\n\n").encode()


START = event("message_start", message={"id": "synthetic"})
STOP = event("message_stop")
CASES = {}


class Gateway(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def handle(self):
        try:
            super().handle()
        except ConnectionError:
            pass

    def do_POST(self):
        request_body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        case = CASES[urlsplit(self.path).query]
        case["received"] = json.loads(request_body)
        case["calls"] = case.get("calls", 0) + 1
        # per_call — 호출마다 다른 본문(앞 호출이 빈 답이고 뒤 호출이 판정인 분류기 따위). 호출 수가 넘으면 마지막 본문을 되풀이한다
        if case.get("per_call"):
            case["chunks"] = [case["per_call"][min(case["calls"], len(case["per_call"])) - 1]]
        body = b"".join(case["chunks"])
        try:
            delays = case.get("header_delays")
            time.sleep(delays[min(case["calls"], len(delays)) - 1] if delays else case.get("header_delay", 0))
            self.send_response(case.get("status", 200))
            self.send_header("Content-Type", case.get("content_type", "text/event-stream"))
            if case.get("fixed"):
                self.send_header("Content-Length", str(len(body) + case.get("extra_length", 0)))
            else:
                self.send_header("Transfer-Encoding", "chunked")
            self.send_header("x-pgpt-request-id", "test-" + urlsplit(self.path).query)
            self.end_headers()
            time.sleep(case.get("delay", 0))
            for chunk in case["chunks"]:
                if case.get("fixed"):
                    self.wfile.write(chunk)
                else:
                    self.wfile.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
                self.wfile.flush()
                time.sleep(case.get("chunk_delay", 0))
            if not case.get("fixed"):
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
            if case.get("extra_length"):
                self.close_connection = True
        except OSError:
            pass


class StreamingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix="pgpt-streams-")
        proxy.LOG_PATH = Path(cls.work.name) / "proxy.log"
        proxy.KEEPALIVE_SEC = 0.05
        proxy.EXECUTION_LIMIT_SEC = 0.3
        proxy.EXECUTION_LIMIT_MARGIN_SEC = 0.02
        cls.gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
        proxy._UPSTREAM = proxy.UpstreamTarget(f"http://127.0.0.1:{cls.gateway.server_port}")
        cls.server = proxy.ProxyServer(("127.0.0.1", 0), proxy.ProxyHandler)
        for server in (cls.gateway, cls.server):
            threading.Thread(target=server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        for server in (cls.server, cls.gateway):
            server.shutdown()
            server.server_close()
        cls.work.cleanup()

    def run_case(self, name, chunks, path="/v1/messages", payload=None, **options):
        CASES[name] = dict(chunks=chunks, **options)
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request("POST", "/gpgpta01-gpt" + path + "?" + name, json.dumps(payload or {}).encode(),
                         {"Content-Type": "application/json"})
            response = conn.getresponse()
            error = None
            try:
                data = response.read()
            except http.client.IncompleteRead as exc:
                data, error = exc.partial, "IncompleteRead"
            # End-of-body can reach the client just before finally updates metrics/logs.
            deadline = time.monotonic() + 2
            while proxy.stats()["active_requests"] and time.monotonic() < deadline:
                time.sleep(0.01)
            return response.status, dict(response.headers), data, error
        finally:
            conn.close()

    def test_fixed_length_sse_keepalive_retains_terminal_event(self):
        status, headers, data, error = self.run_case("fixed", [START, STOP], fixed=True, delay=0.2)
        self.assertEqual(status, 200)
        self.assertIsNone(error)
        self.assertNotIn("Content-Length", headers)
        self.assertEqual(headers.get("Transfer-Encoding"), "chunked")
        self.assertIn(b": keepalive", data)
        self.assertTrue(data.endswith(STOP))

    def test_missing_terminal_is_incomplete_and_counted(self):
        before = proxy.stats()["stream_incomplete"]
        _, _, data, error = self.run_case("missing", [START], fixed=True)
        self.assertEqual(error, "IncompleteRead")
        self.assertEqual(data, START)
        self.assertEqual(proxy.stats()["stream_incomplete"], before + 1)
        self.assertIn("result=stream_incomplete", proxy.LOG_PATH.read_text(encoding="utf-8"))

    def test_keepalive_does_not_split_json_utf8_or_event_fields(self):
        frame = event("content_block_delta", delta={"type": "text_delta", "text": "summary 한글"})
        for pos in (8, frame.index(b"data:") + 18, frame.index("한".encode()) + 1, len(frame) - 1):
            with self.subTest(pos=pos):
                _, _, data, error = self.run_case("partial_" + str(pos),
                    [START, frame[:pos], frame[pos:], STOP], chunk_delay=0.13)
                self.assertIsNone(error)
                self.assertEqual(data.replace(proxy._KEEPALIVE_LINE, b""), START + frame + STOP)
                # The JSON event itself must stay contiguous: removing injected
                # comments afterwards would hide corruption seen by a real client.
                self.assertIn(frame, data)
                self.assertIn(proxy._KEEPALIVE_LINE, data)

    def test_split_crlf_keeps_event_intact(self):
        frame = STOP.replace(b"\n", b"\r\n")
        pos = frame.index(b"\r") + 1
        _, _, data, error = self.run_case("partial_crlf", [frame[:pos], frame[pos:]], chunk_delay=0.13)
        self.assertIsNone(error)
        self.assertTrue(data.startswith(frame))

    def test_stream_diagnostics_exclude_generated_text(self):
        observer = proxy.SseObserver("anthropic")
        observer.feed(START + event("content_block_delta", delta={"type": "text_delta", "text": ""}))
        self.assertIsNotNone(observer.first_event_at)
        self.assertIsNone(observer.first_text_at)
        frame = event("content_block_delta", delta={"type": "text_delta", "text": "private-summary-text"})
        delta = event("message_delta", delta={"stop_reason": "end_turn"},
                      usage={"output_tokens": 123, "input_tokens": 40, "cache_read_input_tokens": 9000,
                             "cache_creation_input_tokens": 300})
        self.run_case("diagnostics", [START, frame, delta, STOP])
        log = proxy.LOG_PATH.read_text(encoding="utf-8")
        lines = [line for line in log.splitlines() if "test-diagnostics" in line]
        self.assertTrue(any("first_text=" in line and "output_tokens=123 stop_reason=end_turn" in line for line in lines))
        # 사용량 칸 — 캐시를 놓친 턴과 곁 호출의 값을 회사 로그에서 가린다(결정 0175)
        self.assertTrue(any("in=40 cache_read=9000 cache_write=300" in line for line in lines))
        self.assertNotIn("private-summary-text", log)

    def test_gateway_usage_gets_cache_ttl_bundle_and_nothing_else_changes(self):
        """층: 쓰는 사람의 계약 — 모든 Claude 턴이 이 중계를 지난다. 걷는 조건: 게이트웨이가 수명별 묶음을 싣게 되어
        채움(`PGPT_PROXY_FILL_CACHE_TTL`)을 걷을 때."""
        zero = {"input_tokens": 0, "output_tokens": 0}  # 게이트웨이의 message_start 꼴 — 캐시 칸이 없다(회사 실측 2026-11-16)
        real = {"input_tokens": 12, "cache_read_input_tokens": 3400, "cache_creation_input_tokens": 56, "output_tokens": 7}
        start = event("message_start", message={"id": "m", "usage": zero})
        # 글 안의 같은 낱말은 사용량이 아니다 — 안 건드린다
        text = event("content_block_delta", delta={"type": "text_delta", "text": '"cache_creation_input_tokens": 9'})
        delta = event("message_delta", delta={"stop_reason": "end_turn"}, usage=real)
        placeholder = proxy.START_CACHE_WRITE_PLACEHOLDER
        expected = [
            # 확장 웹뷰는 스트림 동안 message_start 로만 타이머를 다시 맞춘다 — 자리표 5분 쓰기가 실린다
            {"type": "message_start", "message": {"id": "m", "usage": dict(
                zero, cache_creation_input_tokens=placeholder, cache_creation={
                    "ephemeral_5m_input_tokens": placeholder, "ephemeral_1h_input_tokens": 0})}},
            json.loads(text.split(b"data: ", 1)[1]),
            {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": dict(real, cache_creation={
                "ephemeral_5m_input_tokens": 56, "ephemeral_1h_input_tokens": 0})},
            {"type": "message_stop"},
        ]

        def parsed(data):
            return [json.loads(line[6:]) for line in data.splitlines() if line.startswith(b"data: ")]

        # 이벤트가 어느 바이트에서 쪼개져 와도(CRLF 의 CR 과 LF 사이 포함) 같은 결과다
        for ending in (b"\n", b"\r\n"):
            stream = b"".join(frame.replace(b"\n", ending) for frame in (start, text, delta, STOP))
            for pos in range(1, len(stream)):
                with self.subTest(ending=ending, pos=pos):
                    filler = proxy.CacheTtlFiller()
                    out = filler.feed(stream[:pos]) + filler.feed(stream[pos:]) + filler.flush()
                    self.assertEqual(parsed(out), expected)
                    self.assertIn(text.replace(b"\n", ending), out)
                    self.assertTrue(out.endswith(STOP.replace(b"\n", ending)))

        before = proxy.stats()["cache_ttl_filled"]
        cut = delta.index(b"usage") + 3
        _, _, data, error = self.run_case("cache_ttl", [start, text, delta[:cut], delta[cut:], STOP])
        self.assertIsNone(error)
        self.assertEqual(parsed(data), expected)
        self.assertEqual(proxy.stats()["cache_ttl_filled"], before + 1)
        # 직결 꼴 — 묶음이 이미 있으면 받은 바이트 그대로다
        direct = event("message_delta", delta={"stop_reason": "end_turn"}, usage=dict(real, cache_creation={
            "ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 56}))
        _, _, data, error = self.run_case("cache_ttl_direct", [START, direct, STOP])
        self.assertEqual((data, error), (START + direct + STOP, None))
        self.assertEqual(proxy.stats()["cache_ttl_filled"], before + 1)

    def test_stream_start_estimate_comes_from_the_same_sessions_last_turn(self):
        """층: 쓰는 사람의 계약 — 확장 타이머 · 컨텍스트 표시가 message_start 의 사용량으로 선다. 걷는 조건: 게이트웨이가
        message_start 에 캐시 칸을 싣게 되거나 확장이 message_delta 로 타이머를 맞추게 될 때."""
        session = "11111111-2222-3333-4444-555555555555"
        proxy.remember_session_input(session, {"input_tokens": 2, "cache_read_input_tokens": 70000,
                                               "cache_creation_input_tokens": 500})
        self.assertEqual(proxy.session_input_estimate(session), 70502)
        self.assertEqual(proxy.session_input_estimate("other"), 0)
        filler = proxy.CacheTtlFiller(proxy.session_input_estimate(session))
        out = filler.feed(event("message_start", message={"id": "m", "usage": {"input_tokens": 0, "output_tokens": 0}}))
        usage = json.loads(out.split(b"data: ", 1)[1])["message"]["usage"]
        self.assertEqual(usage["input_tokens"], 70502)
        self.assertEqual(usage["cache_creation"]["ephemeral_5m_input_tokens"], proxy.START_CACHE_WRITE_PLACEHOLDER)
        # 직결 꼴 message_start(캐시 칸이 실제 값으로 있다)는 받은 바이트 그대로다
        direct = event("message_start", message={"id": "m", "usage": {
            "input_tokens": 3, "cache_read_input_tokens": 900, "cache_creation_input_tokens": 0,
            "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0}}})
        self.assertEqual(proxy.CacheTtlFiller(70502).feed(direct), direct)

    def test_second_turn_through_the_handler_carries_the_first_turns_total(self):
        """층: 핸들러 연결 — 세션 번호를 뽑아 끝의 실제 사용량을 기억하고 다음 턴 첫 이벤트에 싣는다.
        걷는 조건은 위 시험과 같다."""
        session = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        payload = {"model": "claude-opus-5-5", "stream": True, "max_tokens": 16,
                   "metadata": {"user_id": json.dumps({"session_id": session})},
                   "messages": [{"role": "user", "content": "hi"}]}
        start = event("message_start", message={"id": "m", "usage": {"input_tokens": 0, "output_tokens": 0}})
        first = event("message_delta", delta={"stop_reason": "end_turn"},
                      usage={"input_tokens": 9, "cache_creation_input_tokens": 3203, "output_tokens": 6})
        second = event("message_delta", delta={"stop_reason": "end_turn"},
                       usage={"input_tokens": 9, "cache_read_input_tokens": 3203, "output_tokens": 6})

        def start_usage(data):
            line = next(line for line in data.splitlines() if line.startswith(b"data: ") and b"message_start" in line)
            return json.loads(line[6:])["message"]["usage"]

        _, _, data, error = self.run_case("turn1", [start, first, STOP], payload=payload)
        self.assertIsNone(error)
        self.assertEqual(start_usage(data)["input_tokens"], 0)
        _, _, data, error = self.run_case("turn2", [start, second, STOP], payload=payload)
        self.assertIsNone(error)
        self.assertEqual(start_usage(data)["input_tokens"], 9 + 3203)
        self.assertEqual(start_usage(data)["cache_creation"]["ephemeral_5m_input_tokens"],
                         proxy.START_CACHE_WRITE_PLACEHOLDER)

    def test_compact_with_runtime_system_tail_is_tuned_on_messages_route(self):
        p = {"model": "claude-opus-5", "thinking": {"type": "adaptive"},
             "output_config": {"effort": "xhigh"}, "max_tokens": 64000,
             "messages": [{"role": "user", "content": proxy._COMPACT_PREAMBLE + proxy._COMPACT_TASK},
                          {"role": "system", "content": "# Environment update"}]}
        original = proxy.NONSTREAM_MAX_TOKENS
        proxy.NONSTREAM_MAX_TOKENS = 18000  # pin: the host may set the documented opt-out
        try:
            self.run_case("compact_wire", [START, STOP], payload=p)
        finally:
            proxy.NONSTREAM_MAX_TOKENS = original
        sent = CASES["compact_wire"]["received"]
        self.assertEqual(sent["output_config"]["effort"], "xhigh")
        # v26: only the output ceiling changes; this request is not streaming, so the 300s cap applies.
        self.assertEqual(sent["max_tokens"], 18000)
        self.assertEqual(sent["thinking"], {"type": "adaptive"})
        self.run_case("normal_route", [b'data: [DONE]\n\n'], path="/v1/chat/completions", payload=p)
        self.assertEqual(CASES["normal_route"]["received"]["output_config"]["effort"], "xhigh")

    def test_empty_stream_is_incomplete(self):
        self.assertEqual(self.run_case("empty", [], fixed=True)[3], "IncompleteRead")

    def test_split_multiline_utf8_error_is_counted_once(self):
        frame = 'event: error\r\ndata: {"type":"error",\r\ndata: "error":{"message":"시간 초과"}}\r\n\r\n'.encode()
        observer = proxy.SseObserver("anthropic")
        for byte in frame:
            observer.feed(bytes([byte]))
        self.assertEqual(observer.error, "시간 초과")
        before = proxy.stats()["stream_errors"]
        _, _, data, error = self.run_case("error", [frame[:35], frame[35:49], frame[49:], frame])
        self.assertIsNone(error)  # Preserve the real error, including normal HTTP framing.
        self.assertEqual(data, frame + frame)
        self.assertEqual(proxy.stats()["stream_errors"], before + 1)
        self.assertIn("result=stream_error", proxy.LOG_PATH.read_text(encoding="utf-8"))

    def test_text_markers_cannot_fake_terminal_or_error(self):
        text = event("content_block_delta", delta={"type": "text_delta", "text": 'message_stop response.completed {"type":"error"}'})
        before = proxy.stats()["stream_errors"]
        self.assertEqual(self.run_case("text_missing", [START, text])[3], "IncompleteRead")
        self.assertIsNone(self.run_case("text_complete", [START, text, STOP])[3])
        self.assertEqual(proxy.stats()["stream_errors"], before)

    def test_responses_terminal_and_failures(self):
        for kind in ("response.completed", "response.failed", "response.incomplete"):
            with self.subTest(kind=kind):
                before = proxy.stats()["stream_errors"]
                frame = event(kind, response={"status": kind.split(".")[1]})
                _, _, data, error = self.run_case(kind, [frame], path="/v1/responses")
                self.assertIsNone(error)
                self.assertEqual(data, frame)
                self.assertEqual(proxy.stats()["stream_errors"], before + (kind != "response.completed"))
        self.assertEqual(self.run_case("responses_missing", [event("response.created")], path="/v1/responses")[3], "IncompleteRead")

    def test_cr_only_lines(self):
        # SSE 는 CR 하나로도 줄을 끝낸다(HTML 표준 「Server-sent events」) — 그 꼴에서도 끝 이벤트를 알아본다
        cr_start, cr_stop = (frame.replace(b"\n", b"\r") for frame in (START, STOP))
        self.assertIsNone(self.run_case("cr_done", [cr_start + cr_stop])[3])
        self.assertEqual(self.run_case("cr_missing", [cr_start])[3], "IncompleteRead")

    def test_non_sse_length_and_body_remain_unchanged(self):
        body = b'{"ok":true}'
        _, headers, data, error = self.run_case("json", [body], fixed=True, content_type="application/json")
        self.assertEqual(headers["Content-Length"], str(len(body)))
        self.assertEqual(data, body)
        self.assertIsNone(error)

    def test_classifier_without_header_is_sent_again_once_and_others_are_not(self):
        """층: 쓰는 사람의 계약 — 회사 자동 모드에서 게이트웨이가 분류기 요청 하나에 머리를 안 내면 Claude Code 가 70 ~ 120 초 뒤 명령을
        거절했다(2026-11-26 · 오늘 셋). 걷는 조건: 게이트웨이가 머리 없이 서는 일이 사라지거나, 분류기가 판 없는 claude-sonnet-5 로 안 부를 때."""
        answer = json.dumps({"type": "message", "role": "assistant", "stop_reason": "end_turn",
                             "content": [{"type": "text", "text": "<severity>3</severity>"}],
                             "usage": {"input_tokens": 3, "output_tokens": 5}}).encode()
        old = proxy.CLASSIFIER_HEAD_WAIT_SEC
        proxy.CLASSIFIER_HEAD_WAIT_SEC = 0.3
        try:
            payload = {"model": "claude-sonnet-5", "max_tokens": 64, "stream": False, "messages": [{"role": "user", "content": "판정"}]}
            status, _, data, _ = self.run_case("cls-retry", [answer], fixed=True, content_type="application/json",
                                               header_delays=[1.0, 0.0], payload=payload)
            self.assertEqual((status, CASES["cls-retry"]["calls"]), (200, 2))
            self.assertEqual(json.loads(data)["content"][0]["text"], "<severity>3</severity>")
            status, _, data, _ = self.run_case("cls-dead", [answer], fixed=True, content_type="application/json",
                                               header_delays=[1.0, 1.0, 1.0], payload=payload)
            self.assertEqual((status, CASES["cls-dead"]["calls"]), (500, 2))
            self.assertIn("auto mode classifier", json.loads(data)["error"]["message"])
            other = {**payload, "model": "claude-sonnet-5-5"}
            status, _, _, _ = self.run_case("main-slow", [answer], fixed=True, content_type="application/json",
                                            header_delays=[1.0], payload=other)
            self.assertEqual((status, CASES["main-slow"]["calls"]), (200, 1))
        finally:
            proxy.CLASSIFIER_HEAD_WAIT_SEC = old

    def test_classifier_answer_without_verdict_is_sent_again_once_and_others_are_not(self):
        """층: 쓰는 사람의 계약 — 회사 자동 모드에서 게이트웨이가 분류기 요청에 200 으로 빈 답 · 열다 만 태그를 내면 Claude Code 가
        「판정 못 함」으로 명령을 거절한다(같은 요청을 Claude Code 가 다시 보내도 또 비었다). 걷는 조건: 게이트웨이가 판정 꼴 없는 200 을
        내지 않게 되거나, 분류기가 판 없는 claude-sonnet-5 로 안 부를 때."""
        def message(content, stop="end_turn"):
            return json.dumps({"type": "message", "role": "assistant", "stop_reason": stop, "content": content,
                               "usage": {"input_tokens": 3, "output_tokens": 5}}).encode()
        empty = message([])
        cut = message([{"type": "text", "text": "<th"}])
        verdict = message([{"type": "text", "text": "<thinking>살핀다</thinking><severity>3</severity>"}])
        truncated = message([{"type": "text", "text": "Looking at the action"}], stop="max_tokens")
        payload = {"model": "claude-sonnet-5", "max_tokens": 8192, "stream": False, "messages": [{"role": "user", "content": "판정"}]}
        json_case = dict(fixed=True, content_type="application/json", payload=payload)

        def calls(name, bodies):
            status, _, data, _ = self.run_case(name, [], per_call=bodies, **json_case)
            return status, data, CASES[name]["calls"]

        before = proxy.stats()["classifier_empty_retries"]
        status, data, count = calls("cls-empty-then-verdict", [empty, verdict])
        self.assertEqual((status, count), (200, 2))
        self.assertIn("<severity>3</severity>", json.loads(data)["content"][0]["text"])
        status, data, count = calls("cls-cut-then-verdict", [cut, verdict])
        self.assertEqual((status, count), (200, 2))
        status, data, count = calls("cls-empty-twice", [empty, cut, verdict])
        self.assertEqual((status, count), (200, 2))
        self.assertEqual(json.loads(data)["content"][0]["text"], "<th")
        status, data, count = calls("cls-truncated", [truncated, verdict])
        self.assertEqual((status, count), (200, 1))
        status, data, count = calls("cls-verdict-first", [verdict, empty])
        self.assertEqual((status, count), (200, 1))
        self.assertEqual(proxy.stats()["classifier_empty_retries"], before + 3)
        main = {**payload, "model": "claude-sonnet-5-5"}
        status, _, data, _ = self.run_case("main-empty", [], per_call=[empty, verdict], payload=main,
                                           fixed=True, content_type="application/json")
        self.assertEqual((status, CASES["main-empty"]["calls"], json.loads(data)["content"]), (200, 1, []))

    def test_classifier_miss_keeps_request_and_answer_and_only_the_newest(self):
        """층: 코드 규칙 — 판정 꼴 없이 끝난 분류기 답은 요청 본문과 함께 남아 원인을 요청 쪽에서 가를 수 있고, 건수 한도가 지켜진다.
        걷는 조건: 빈 답의 원인이 가려져 보관 장치를 걷을 때."""
        old = proxy.CLASSIFIER_MISS_KEEP
        proxy.CLASSIFIER_MISS_KEEP = 2
        folder = proxy.LOG_PATH.with_name("classifier-miss")
        try:
            for stamp in (1, 2, 3):
                time.sleep(1.05)
                name = proxy.keep_classifier_miss(json.dumps({"messages": [f"요청{stamp}"]}).encode(), b'{"content": []}', f"gw-{stamp}")
                self.assertTrue(name.endswith(f"gw{stamp}.json"), name)
            kept = sorted(path.name for path in folder.glob("*.json"))
            self.assertEqual(len(kept), 2)
            body = json.loads((folder / kept[-1]).read_text(encoding="utf-8"))
            self.assertEqual((body["request"]["messages"], body["answer"]), (["요청3"], {"content": []}))
            self.assertEqual(proxy._json_output_tokens(b'{"usage": {"output_tokens": 7}}'), 7)
            self.assertEqual(proxy._json_output_tokens(b"not json"), "unknown")
        finally:
            proxy.CLASSIFIER_MISS_KEEP = old
            for path in folder.glob("*.json"):
                path.unlink()

    def test_classifier_verdictless_names_only_a_normal_answer_with_no_verdict_tag(self):
        """층: 코드 규칙 — 다시 보낼 답과 그대로 중계할 답을 가른다. 걷는 조건: 분류기 판정 꼴이 `<severity>` 가 아니게 될 때."""
        def message(content, stop="end_turn", kind="message"):
            return json.dumps({"type": kind, "stop_reason": stop, "content": content}).encode()
        text = lambda t: [{"type": "text", "text": t}]
        self.assertTrue(proxy.classifier_verdictless(message([])))
        self.assertTrue(proxy.classifier_verdictless(message(text("<th"))))
        self.assertTrue(proxy.classifier_verdictless(message([{"type": "thinking", "thinking": "..."}])))
        self.assertFalse(proxy.classifier_verdictless(message(text("<severity>4</severity>"))))
        self.assertFalse(proxy.classifier_verdictless(message(text("살핀다"), stop="max_tokens")))
        self.assertFalse(proxy.classifier_verdictless(message([], kind="error")))
        self.assertFalse(proxy.classifier_verdictless(b"not json"))
        self.assertFalse(proxy.classifier_verdictless(None))

    def test_classifier_answer_tail_is_logged_only_for_the_classifier(self):
        """층: 회사 자동 모드의 「could not evaluate」 원인을 가르는 기록 — Claude Code 는 분류기 답 글을 어디에도 안 남긴다.
        걷는 조건: Claude Code 가 판정 꼴을 못 읽은 답을 제 기록에 남기게 되거나, 분류기가 판 없는 claude-sonnet-5 로 안 부를 때."""
        answer = {"type": "message", "role": "assistant", "model": "claude-sonnet-4.6", "stop_reason": "end_turn",
                  "content": [{"type": "text", "text": "<thinking>살핀다</thinking> <severity>2</severity>"}],
                  "usage": {"input_tokens": 3, "output_tokens": 9}}
        for name, model in (("cls", "claude-sonnet-5"), ("main", "claude-sonnet-4.6")):
            status, _, data, _ = self.run_case(name, [json.dumps(answer, ensure_ascii=False).encode()], fixed=True,
                                               content_type="application/json",
                                               payload={"model": model, "max_tokens": 64, "stream": False,
                                                        "messages": [{"role": "user", "content": "판정"}]})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(data)["content"], answer["content"])
        lines = [line for line in proxy.LOG_PATH.read_text(encoding="utf-8").splitlines() if "classifier answer" in line]
        self.assertEqual([("gw=test-cls" in line) for line in lines], [True], lines)
        self.assertIn('severity_tags=1 ', lines[0])
        self.assertIn('tail="<thinking>살핀다</thinking> <severity>2</severity>"', lines[0])

    def test_upstream_5xx_is_logged_as_failure_with_gateway_code(self):
        """층: 쓰는 사람의 계약 — 회사에서 모델 요청이 진 층을 가르는 기록. 걷는 조건: Codex 가 500 본문을 사용자에게 보이게 되거나
        프록시가 오류 응답을 더는 그대로 중계하지 않을 때."""
        # 게이트웨이의 Responses 오류는 OpenAI 봉투로 온다(errors-Posco.setting.md 「LlmApiExceptionHandler」 · P099 = 500 server_error).
        # Codex 는 500 본문을 버리고 고정 문구만 보이므로, 그 코드가 남는 자리는 프록시 기록뿐이다 — 그리고 본문을 끝까지 옮겼다고
        # `result=complete` 로 남기면 실패가 성공으로 세진다.
        body = json.dumps({"error": {"message": "서버 내부 오류", "type": "server_error", "code": "P099"}},
                          ensure_ascii=False).encode()
        status, _, _, error = self.run_case("gw500", [body], path="/v1/responses", fixed=True,
                                            status=500, content_type="application/json")
        self.assertEqual(status, 500)
        self.assertIsNone(error)
        lines = [line for line in proxy.LOG_PATH.read_text(encoding="utf-8").splitlines()
                 if " complete " in line and "gw=test-gw500" in line]
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("result=http_error", lines[0])
        self.assertIn('error_code="P099"', lines[0])

    def test_unknown_sse_route_does_not_require_model_terminal(self):
        self.assertIsNone(self.run_case("unknown", [b"data: custom\n\n"], path="/custom")[3])

    def test_limited_inspection_is_not_misreported_as_complete(self):
        frame = event("response.completed", response={"output": "x" * (proxy.MAX_SSE_EVENT_BYTES + 20)})
        before = proxy.stats()["stream_unverified"]
        _, _, data, error = self.run_case("large_terminal", [frame], path="/v1/responses", fixed=True)
        self.assertEqual(data, frame)
        self.assertIsNone(error)
        self.assertEqual(proxy.stats()["stream_unverified"], before + 1)
        # A later small terminal can still be observed after an oversized content event.
        observer = proxy.SseObserver("anthropic")
        observer.feed(frame)
        observer.feed(STOP)
        self.assertTrue(observer.limited and observer.terminal)
        self.assertLessEqual(len(observer._line), proxy.MAX_SSE_EVENT_BYTES)

    def test_timeout_candidate_counts_missing_terminal_but_not_success(self):
        before = proxy.stats()["execution_cuts"]
        self.assertEqual(self.run_case("timeout_missing", [START], delay=0.4)[3], "IncompleteRead")
        self.assertEqual(proxy.stats()["execution_cuts"], before + 1)
        self.assertIsNone(self.run_case("slow_success", [START, STOP], delay=0.4)[3])
        self.assertEqual(proxy.stats()["execution_cuts"], before + 1)
        self.assertIsNone(self.run_case("timeout_error", [event("error", error={"message": "timeout"})], delay=0.4)[3])
        self.assertEqual(proxy.stats()["execution_cuts"], before + 2)

    def test_upstream_truncated_content_length_stays_incomplete(self):
        self.assertEqual(self.run_case("length_short", [START, STOP], fixed=True, extra_length=10)[3], "IncompleteRead")

    def test_another_requests_keepalive_is_not_logged_for_this_request(self):
        class Response:
            length = None
            sent = False
            def read1(self, size):
                if self.sent:
                    return b""
                self.sent = True
                proxy._count_keepalive()  # Simulate a concurrent request's keepalive.
                return START + STOP
        handler = proxy.ProxyHandler.__new__(proxy.ProxyHandler)
        handler.wfile = io.BytesIO()
        handler._request_context = "keepalive-isolation"
        handler._gw_request_id = "keepalive-isolation"
        handler._chunked_out = True
        self.assertTrue(handler._relay_stream(Response(), sse=True, protocol="anthropic"))
        self.assertNotIn(b": keepalive", handler.wfile.getvalue())
        text = proxy.LOG_PATH.read_text(encoding="utf-8") if proxy.LOG_PATH.exists() else ""
        self.assertFalse(any("keepalive x" in line and "keepalive-isolation" in line
                             for line in text.splitlines()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
