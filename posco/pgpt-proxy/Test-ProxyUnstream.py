"""Real HTTP conversion checks with a local gateway; no credentials required."""
import importlib.util
import json
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("stream_tests", Path(__file__).with_name("Test-ProxyStreaming.py"))
streams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(streams)
proxy = streams.proxy


def message(content=None, stop="tool_use"):
    return {"type": "message", "id": "msg_fixture", "model": "claude-fixture", "role": "assistant",
            "content": content if content is not None else [{"type": "tool_use", "id": "tool_1", "name": "Write",
                                                            "input": {"path": "report.md", "content": "한글😀\n\\\"" * 60000}}],
            "stop_reason": stop, "stop_sequence": None,
            "usage": {"input_tokens": 123, "output_tokens": 456, "cache_read_input_tokens": 100}}


def parse(data):
    return [json.loads(line[6:]) for line in data.splitlines() if line.startswith(b"data: ")]


class ConversionTests(unittest.TestCase):
    def test_large_unicode_tool_input_roundtrips_through_delta_events(self):
        original = message()
        events = parse(b"".join(proxy.anthropic_message_events(original)))
        reconstructed = json.loads("".join(e["delta"]["partial_json"] for e in events
                                           if e["type"] == "content_block_delta"))
        self.assertEqual(reconstructed, original["content"][0]["input"])
        self.assertEqual(events[1]["content_block"]["input"], {})
        self.assertEqual(events[-2]["usage"], original["usage"])
        self.assertEqual(events[-1]["type"], "message_stop")

    def test_thinking_signature_text_and_multiple_tools(self):
        blocks = [{"type": "thinking", "thinking": "reason", "signature": "signature" * 1000},
                  {"type": "redacted_thinking", "data": "opaque"},
                  {"type": "text", "text": "report"},
                  {"type": "tool_use", "id": "a", "name": "Read", "input": {}},
                  {"type": "tool_use", "id": "b", "name": "Write", "input": {"content": "done"}}]
        events = parse(b"".join(proxy.anthropic_message_events(message(blocks))))
        self.assertEqual([e["index"] for e in events if e["type"] == "content_block_stop"], list(range(5)))
        self.assertEqual("".join(e["delta"]["signature"] for e in events if e.get("delta", {}).get("type") == "signature_delta"), blocks[0]["signature"])

    def test_unknown_or_invalid_blocks_fail_before_any_events(self):
        for block in ({"type": "future_block"}, {"type": "tool_use", "id": "a", "name": "Write", "input": "bad"}):
            with self.assertRaises(ValueError):
                proxy.anthropic_message_events(message(message()["content"] + [block]))
        for key in ("stop_reason", "content", "usage", "id"):
            invalid = message(); del invalid[key]
            with self.assertRaises(ValueError):
                proxy.anthropic_message_events(invalid)


class UnstreamHTTPTests(unittest.TestCase):
    setUpClass = classmethod(streams.StreamingTests.setUpClass.__func__)
    tearDownClass = classmethod(streams.StreamingTests.tearDownClass.__func__)
    run_case = streams.StreamingTests.run_case

    def setUp(self):
        proxy.CLAUDE_UNSTREAM = True

    def tearDown(self):
        proxy.CLAUDE_UNSTREAM = False

    def run_message(self, name, raw=None, **options):
        return self.run_case(name, [json.dumps(message()).encode() if raw is None else raw],
                             payload={"model": "claude-fixture", "stream": True, "max_tokens": 8192,
                                      "tools": [{"name": "Write", "input_schema": {"required": ["path", "content"]}}],
                                      "messages": [{"role": "user", "content": "Make a report"}]},
                             content_type="application/json", fixed=True, **options)

    def test_header_and_body_delays_with_large_tool_input(self):
        status, headers, data, error = self.run_message("large", header_delay=0.15, delay=0.15)
        self.assertEqual(status, 200); self.assertIsNone(error)
        self.assertIn(b": keepalive", data)
        self.assertEqual(headers["Transfer-Encoding"], "chunked")
        self.assertFalse(streams.CASES["large"]["received"]["stream"])
        self.assertEqual(streams.CASES["large"]["received"]["max_tokens"], 8192)
        events = parse(data)
        tool_input = json.loads("".join(e["delta"]["partial_json"] for e in events if e["type"] == "content_block_delta"))
        self.assertEqual(tool_input, message()["content"][0]["input"])

    def test_http_errors_are_preserved(self):
        for status in (401, 429, 500, 504):
            actual, headers, data, error = self.run_message("error" + str(status), b'{"error":"fixture"}', status=status)
            self.assertEqual(actual, status)
            self.assertEqual(data, b'{"error":"fixture"}')
            self.assertNotIn("text/event-stream", headers["Content-Type"])

    def test_bad_or_truncated_responses_never_emit_tools_or_success(self):
        for name, raw, options in [("invalid", b'bad json', {}), ("truncated", json.dumps(message()).encode(), {"extra_length": 30}),
                                   ("unknown", json.dumps(message(message()["content"] + [{"type": "future"}])).encode(), {})]:
            status, headers, data, error = self.run_message(name, raw, **options)
            self.assertEqual([e["type"] for e in parse(data)], ["error"])

    def test_buffer_limit_fails_explicitly(self):
        old = proxy.MAX_UNSTREAM_BYTES
        try:
            proxy.MAX_UNSTREAM_BYTES = 100
            _, _, data, _ = self.run_message("oversize")
            self.assertEqual([e["type"] for e in parse(data)], ["error"])
        finally:
            proxy.MAX_UNSTREAM_BYTES = old

    def test_gateway_empty_input_is_an_error(self):
        raw = json.dumps(message([{"type": "tool_use", "id": "a", "name": "Write", "input": {}}])).encode()
        _, _, data, _ = self.run_message("empty_args", raw)
        self.assertEqual([e["type"] for e in parse(data)], ["error"])

    def test_compact_only_default_does_not_switch_normal_work(self):
        proxy.CLAUDE_UNSTREAM = False
        normal = {"stream": True, "messages": [{"role": "user", "content": "Make report"}]}
        compact = {"stream": True, "messages": [{"role": "user", "content": proxy._COMPACT_PREAMBLE + proxy._COMPACT_TASK}]}
        raw = json.dumps(message([{"type": "text", "text": "<summary>Next: write report</summary>"}], "end_turn")).encode()
        for name, payload, expected in [("normal", normal, True), ("compact", compact, False)]:
            _, _, data, _ = self.run_case(name, [raw], payload=payload, content_type="application/json", fixed=True)
            self.assertEqual(streams.CASES[name]["received"]["stream"], expected)
            if not expected:
                self.assertEqual(parse(data)[-1]["type"], "message_stop")
        tool_raw = json.dumps(message()).encode()
        _, _, data, _ = self.run_case("compact_tool", [tool_raw], payload=compact, content_type="application/json", fixed=True)
        self.assertEqual([e["type"] for e in parse(data)], ["error"])

    def test_capped_paths_count_max_tokens(self):
        """v26: the real compaction path (stream=true -> nonstream bridge) gets the 300s ceiling, a normal
        streaming turn gets the 180s ceiling, and every max_tokens ending is counted on every relay path."""
        proxy.CLAUDE_UNSTREAM = False
        original = (proxy.STREAM_MAX_TOKENS, proxy.NONSTREAM_MAX_TOKENS)
        proxy.STREAM_MAX_TOKENS, proxy.NONSTREAM_MAX_TOKENS = 10000, 18000
        try:
            prompt = proxy._COMPACT_PREAMBLE + proxy._COMPACT_TASK
            capped = json.dumps(message([{"type": "text", "text": "<analysis>long"}], "max_tokens")).encode()
            base = proxy.stats()
            _, _, data, _ = self.run_case("cap_bridge", [capped], content_type="application/json", fixed=True,
                                          payload={"stream": True, "max_tokens": 64000, "thinking": {"type": "adaptive"},
                                                   "messages": [{"role": "user", "content": prompt}]})
            sent = streams.CASES["cap_bridge"]["received"]
            self.assertEqual((sent["stream"], sent["max_tokens"]), (False, 18000))
            self.assertEqual(parse(data)[-1]["type"], "message_stop")
            # The client's own nonstream retry of a compaction is relayed as-is and still counted.
            _, _, data, _ = self.run_case("cap_raw", [capped], content_type="application/json", fixed=True,
                                          payload={"stream": False, "max_tokens": 64000,
                                                   "messages": [{"role": "user", "content": prompt}]})
            self.assertEqual(data, capped)
            self.assertEqual(streams.CASES["cap_raw"]["received"]["max_tokens"], 18000)
            # A normal streaming turn: 180s ceiling, counted as a hit but not as a compaction hit.
            stream_stop = (streams.START + streams.event("message_delta", delta={"stop_reason": "max_tokens"},
                                                         usage={"output_tokens": 10000}) + streams.STOP)
            self.run_case("normal_stream", [stream_stop],
                          payload={"stream": True, "max_tokens": 64000, "messages": [{"role": "user", "content": "Write"}]})
            self.assertEqual(streams.CASES["normal_stream"]["received"]["max_tokens"], 10000)
            # The client's output-limit resume inside that compaction takes the same nonstream, 300s route.
            resume = "Output token limit hit. Resume directly \u2014 no apology. Break remaining work into smaller pieces."
            done = json.dumps(message([{"type": "text", "text": "</summary>"}], "end_turn")).encode()
            _, _, data, _ = self.run_case("cap_resume", [done], content_type="application/json", fixed=True,
                                          payload={"stream": True, "max_tokens": 64000,
                                                   "messages": [{"role": "user", "content": prompt},
                                                                {"role": "assistant", "content": "<analysis>long"},
                                                                {"role": "user", "content": resume}]})
            sent = streams.CASES["cap_resume"]["received"]
            self.assertEqual((sent["stream"], sent["max_tokens"]), (False, 18000))
            self.assertEqual(parse(data)[-1]["type"], "message_stop")
            self.assertIn("kind=compact_continue", proxy.LOG_PATH.read_text(encoding="utf-8"))
            stats = proxy.stats()
            self.assertEqual(stats["compact_max_tokens_hit"], base["compact_max_tokens_hit"] + 2)
            self.assertEqual(stats["max_tokens_hits"], base["max_tokens_hits"] + 3)
            self.assertIn("reached max_tokens", proxy.LOG_PATH.read_text(encoding="utf-8"))
        finally:
            proxy.STREAM_MAX_TOKENS, proxy.NONSTREAM_MAX_TOKENS = original

    def test_off_nonstream_and_other_routes_remain_unchanged(self):
        raw = json.dumps(message()).encode()
        for name, enabled, path, request_stream in [("off", False, "/v1/messages", True),
                ("already_nonstream", True, "/v1/messages", False), ("openai", True, "/v1/responses", True)]:
            proxy.CLAUDE_UNSTREAM = enabled
            _, _, data, _ = self.run_case(name, [raw], path=path, payload={"stream": request_stream}, content_type="application/json", fixed=True)
            self.assertEqual(data, raw)
            self.assertEqual(streams.CASES[name]["received"]["stream"], request_stream)


if __name__ == "__main__":
    unittest.main(verbosity=2)
