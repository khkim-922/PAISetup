"""Compact requests are recognized by the client's compact prompt family only (v26), never by size or stream mode."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("proxy", Path(__file__).resolve().parent / "opus5_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)


def compact():
    return {"model": "claude-opus-5", "stream": True, "max_tokens": 64000,
            "thinking": {"type": "adaptive", "display": "omitted"},
            "output_config": {"effort": "xhigh", "format": {"type": "text"}},
            "tools": [{"name": "Write", "input_schema": {"type": "object"}}],
            "messages": [{"role": "assistant", "content": [{"type": "tool_use", "input": {"content": "keep all of this"}}]},
                         {"role": "user", "content": [{"type": "text", "text": proxy._COMPACT_PREAMBLE + proxy._COMPACT_TASK + "\nDetails..."}]}]}


class CompactionTests(unittest.TestCase):
    def setUp(self):
        self.original = proxy.COMPACT_CONCISE
        proxy.COMPACT_CONCISE = True

    def tearDown(self):
        proxy.COMPACT_CONCISE = self.original

    def test_compact_preserves_effort_budget_history_and_original_prompt(self):
        for stream in (True, False):
            p = compact(); p["stream"] = stream
            expected = copy.deepcopy(p)
            expected["messages"][-1]["content"][0]["text"] += proxy._COMPACT_SUFFIX
            self.assertEqual(proxy.tune_claude_compaction(p), "compact_concise=true")
            self.assertEqual(p, expected)

    def test_generic_summary_size_and_nonstream_are_not_compact(self):
        p = compact(); p["stream"] = False
        p["messages"][-1]["content"][0]["text"] = "Please summarize " + "a" * 250000
        before = copy.deepcopy(p)
        self.assertEqual(proxy.tune_claude_compaction(p), "")
        self.assertEqual(p, before)

    def test_old_compact_in_history_does_not_change_normal_turn(self):
        p = compact(); p["messages"].append({"role": "user", "content": "Continue implementing the feature."})
        self.assertFalse(proxy.is_claude_compaction(p))
        self.assertEqual(proxy.tune_claude_compaction(p), "")
        self.assertEqual(p["output_config"]["effort"], "xhigh")

    def test_quoted_marker_and_assistant_are_not_compact(self):
        p = compact(); p["messages"][-1]["role"] = "assistant"
        self.assertFalse(proxy.is_claude_compaction(p))
        p = compact(); p["messages"][-1]["content"][0]["text"] = "Explain this prompt: " + p["messages"][-1]["content"][0]["text"]
        self.assertFalse(proxy.is_claude_compaction(p))

    def test_opt_out_preserves_request(self):
        p = compact(); proxy.COMPACT_CONCISE = False
        before = copy.deepcopy(p)
        self.assertEqual(proxy.tune_claude_compaction(p), "")
        self.assertEqual(p, before)

    def test_thinking_and_all_effort_levels_are_preserved(self):
        for effort in (None, "low", "medium", "future", 42):
            p = compact(); p["output_config"]["effort"] = effort
            p["thinking"] = {"type": "enabled", "budget_tokens": 12000}
            self.assertEqual(proxy.tune_claude_compaction(p), "compact_concise=true")
            self.assertEqual(p["output_config"]["effort"], effort)
            self.assertEqual(p["thinking"]["budget_tokens"], 12000)

    def test_instruction_is_not_duplicated(self):
        p = compact()
        proxy.tune_claude_compaction(p)
        before = copy.deepcopy(p)
        self.assertEqual(proxy.tune_claude_compaction(p), "")
        self.assertEqual(p, before)

    def test_known_prompt_variants_and_reworded_bullets_are_compact(self):
        for task in ("Your task is to create a detailed summary of this conversation. This summary will be placed at the start of a continuing session.",
                     "Your task is to create a detailed summary of the RECENT portion of the conversation \u2014 the messages that follow earlier retained context."):
            p = compact(); p["messages"][-1]["content"][0]["text"] = proxy._COMPACT_PREAMBLE + task
            self.assertTrue(proxy.is_claude_compaction(p))
            self.assertEqual(proxy.tune_claude_compaction(p), "compact_concise=true")
        p = compact()
        p["messages"][-1]["content"][0]["text"] = (proxy._COMPACT_PREAMBLE_HEAD + "\n\n- A new bullet a future client added.\n\n"
                                                   + proxy._COMPACT_TASK)
        self.assertTrue(proxy.is_claude_compaction(p))

    def test_task_far_from_preamble_or_without_preamble_is_not_compact(self):
        p = compact()
        p["messages"][-1]["content"][0]["text"] = proxy._COMPACT_PREAMBLE_HEAD + "x" * 5000 + proxy._COMPACT_TASK
        self.assertFalse(proxy.is_claude_compaction(p))
        p = compact(); p["messages"][-1]["content"][0]["text"] = proxy._COMPACT_TASK
        self.assertFalse(proxy.is_claude_compaction(p))

    def test_output_limit_resume_inside_a_compaction_is_recognized(self):
        resume = "Output token limit hit. Resume directly \u2014 no apology, no recap of what you were doing. Break remaining work into smaller pieces."
        p = compact()
        p["messages"] += [{"role": "assistant", "content": [{"type": "text", "text": "<analysis>partial"}]},
                          {"role": "user", "content": [{"type": "text", "text": resume}]}]
        self.assertFalse(proxy.is_claude_compaction(p))
        self.assertTrue(proxy.is_compaction_continuation(p))
        self.assertEqual(proxy.tune_claude_compaction(p), "")  # the resume text itself is never rewritten
        # The same nudge in an ordinary conversation is a normal turn.
        normal = {"messages": [{"role": "user", "content": "Write the report."},
                               {"role": "assistant", "content": "partial"},
                               {"role": "user", "content": resume}]}
        self.assertFalse(proxy.is_compaction_continuation(normal))
        # A compact prompt quoted by the assistant does not count.
        quoted = {"messages": [{"role": "assistant", "content": proxy._COMPACT_PREAMBLE + proxy._COMPACT_TASK},
                               {"role": "user", "content": resume}]}
        self.assertFalse(proxy.is_compaction_continuation(quoted))

    def test_unrecognized_client_formats_pass_through(self):
        for content in (None, [], [{"type": "image"}], {"text": proxy._COMPACT_TASK}):
            p = compact(); p["messages"][-1]["content"] = content
            self.assertFalse(proxy.is_claude_compaction(p))


class OutputCeilingTests(unittest.TestCase):
    """v26: every Claude call is lowered to a ceiling that ends inside its route's gateway limit."""

    def setUp(self):
        self.original = (proxy.STREAM_MAX_TOKENS, proxy.NONSTREAM_MAX_TOKENS)
        proxy.STREAM_MAX_TOKENS, proxy.NONSTREAM_MAX_TOKENS = 10000, 18000

    def tearDown(self):
        proxy.STREAM_MAX_TOKENS, proxy.NONSTREAM_MAX_TOKENS = self.original

    def test_nonstream_route_uses_the_300s_ceiling_and_keeps_everything_else(self):
        p = compact(); p["stream"] = False
        expected = copy.deepcopy(p); expected["max_tokens"] = 18000
        self.assertEqual(proxy.cap_claude_output(p, unstream=True), "max_tokens_cap=18000")
        self.assertEqual(p, expected)

    def test_streaming_route_uses_the_180s_ceiling_for_normal_turns_too(self):
        p = compact(); p["messages"].append({"role": "user", "content": "Write the whole report."})
        self.assertEqual(proxy.cap_claude_output(p, unstream=False), "max_tokens_cap=10000")
        self.assertEqual(p["max_tokens"], 10000)
        self.assertEqual(p["output_config"]["effort"], "xhigh")

    def test_enabled_thinking_budget_keeps_half_the_ceiling_for_the_answer(self):
        for budget, expected in ((31999, 5000), (16000, 5000), (5000, 5000), (3000, 3000)):
            p = compact(); p["thinking"] = {"type": "enabled", "budget_tokens": budget}
            proxy.cap_claude_output(p, unstream=False)
            self.assertEqual((p["max_tokens"], p["thinking"]["budget_tokens"]), (10000, expected))
            self.assertEqual(p["thinking"]["type"], "enabled")

    def test_smaller_client_limits_are_never_raised(self):
        for value in (1, 4096, 9000, 10000):
            p = compact(); p["max_tokens"] = value
            self.assertEqual(proxy.cap_claude_output(p, unstream=False), "")
            self.assertEqual(p["max_tokens"], value)

    def test_missing_or_invalid_max_tokens_gets_the_ceiling(self):
        for value in (None, "64000", 0, -1, True):
            p = compact(); p["max_tokens"] = value
            if value is None:
                del p["max_tokens"]
            proxy.cap_claude_output(p, unstream=False)
            self.assertEqual(p["max_tokens"], 10000)

    def test_health_reports_the_effective_ceilings_and_opt_out(self):
        self.assertEqual((proxy.output_cap(unstream=False), proxy.output_cap(unstream=True)), (10000, 18000))
        proxy.STREAM_MAX_TOKENS = 2000
        self.assertEqual(proxy.output_cap(unstream=False), 4096)
        proxy.STREAM_MAX_TOKENS = 0
        p = compact(); before = copy.deepcopy(p)
        self.assertEqual(proxy.cap_claude_output(p, unstream=False), "")
        self.assertEqual(p, before)
        self.assertEqual(proxy.output_cap(unstream=True), 18000)
        stats = proxy.stats()
        self.assertEqual((stats["stream_max_tokens"], stats["nonstream_max_tokens"]), (0, 18000))


if __name__ == "__main__":
    unittest.main(verbosity=2)
