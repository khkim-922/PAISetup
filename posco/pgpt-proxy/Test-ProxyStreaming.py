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
        body = b"".join(case["chunks"])
        try:
            time.sleep(case.get("header_delay", 0))
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
        proxy._UPSTREAM_POOL = proxy.UpstreamPool(f"http://127.0.0.1:{cls.gateway.server_port}")
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
        delta = event("message_delta", delta={"stop_reason": "end_turn"}, usage={"output_tokens": 123})
        self.run_case("diagnostics", [START, frame, delta, STOP])
        log = proxy.LOG_PATH.read_text(encoding="utf-8")
        lines = [line for line in log.splitlines() if "test-diagnostics" in line]
        self.assertTrue(any("first_text=" in line and "output_tokens=123 stop_reason=end_turn" in line for line in lines))
        self.assertNotIn("private-summary-text", log)

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
        # (우리 것 · claude-config 결정 0082) 간결 지시는 기본으로 꺼져 있다 — 압축 지시문이 글자 그대로 간다.
        # 상류는 이 자리에서 `+ proxy._COMPACT_SUFFIX` 를 기대한다. 켠 판의 동작은 Test-ProxyCompaction 이 잰다.
        self.assertEqual(sent["messages"][0]["content"][0]["text"], p["messages"][0]["content"])
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

    def test_chat_done_and_cr_only_lines(self):
        frame = b'data: {"choices":[]}\r\rdata: [DONE]\r\r'
        self.assertIsNone(self.run_case("chat_done", [frame], path="/v1/chat/completions")[3])
        self.assertEqual(self.run_case("chat_missing", [b'data: {"choices":[]}\n\n'], path="/v1/chat/completions")[3], "IncompleteRead")

    def test_non_sse_length_and_body_remain_unchanged(self):
        body = b'{"ok":true}'
        _, headers, data, error = self.run_case("json", [body], fixed=True, content_type="application/json")
        self.assertEqual(headers["Content-Length"], str(len(body)))
        self.assertEqual(data, body)
        self.assertIsNone(error)

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
        self.assertTrue(handler._relay_stream(Response(), gemini_sse=False, sse=True, protocol="anthropic"))
        self.assertNotIn(b": keepalive", handler.wfile.getvalue())
        text = proxy.LOG_PATH.read_text(encoding="utf-8") if proxy.LOG_PATH.exists() else ""
        self.assertFalse(any("keepalive x" in line and "keepalive-isolation" in line
                             for line in text.splitlines()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
