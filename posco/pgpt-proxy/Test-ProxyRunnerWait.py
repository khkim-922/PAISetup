"""러너가 도는 동안 부른 대화가 식지 않나 — 맡기기 러너의 공유 부품(`runner_common.py`)이 이 프록시에 알리고, 프록시가 그
알림으로 기다리는 대화를 잇나. 러너가 띄운 `claude -p` 의 요청 머리(`claude_bg.py`)를 프록시가 알아보나.

    python -X utf8 posco/pgpt-proxy/Test-ProxyRunnerWait.py

층: 쓰는 사람의 계약 — 틀리면 러너를 18 분 넘게 기다린 대화가 맥락을 통째로 다시 쓰거나, 답하고 끝난 러너의 대화에 데우기가
나간다. 둘 다 아무 오류 없이 값으로만 보인다. 러너 쪽 손과 이 프록시를 그대로 맞물려 재고(가짜 게이트웨이), 사내망은 안 탄다.
남기는 까닭: 조용히 깨진다(값으로만 보인다) · 닿으면 맥락을 통째로 다시 쓴다 · 러너와 프록시 사이의 약속은 다른 검사가 안 잰다 ·
레인 기록이 긴 경로에서 안 읽히는 결함이 실제로 났다.
걷는 조건: 러너의 알림(`waiting_notice`)이나 프록시의 데우기를 걷을 때.
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# 러너 스킬의 자리 — 설정 저장소는 `.claude/skills/`, 배포본은 `kit/skills/` 에 둔다
SKILLS = next((place for place in (ROOT.parent.parent / ".claude" / "skills", ROOT.parent.parent / "kit" / "skills")
               if (place / "agent-envelope").is_dir()), ROOT.parent.parent / ".claude" / "skills")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proxy = load("proxy", ROOT / "opus5_proxy.py")
sys.path.insert(0, str(SKILLS / "agent-envelope" / "scripts"))
common = load("runner_common", SKILLS / "agent-envelope" / "scripts" / "runner_common.py")
claude_bg = load("claude_bg", SKILLS / "claude-background" / "scripts" / "claude_bg.py")

SESSION = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
LANE_ID_HEADER = "x-claude-code-agent-id"   # 클라이언트가 레인의 요청에 싣는 머리 — 실물에서 잰 값
OUT_NAME = "runner-warm.answer.md"         # 러너의 답 파일 이름 — 부른 레인의 명령에 든다
NOTICE_HOLD_MOST = 0.25                    # 알림이 러너를 붙잡는다고 볼 끝 — 알림 한 번의 끝(0.5초)의 반


def event(kind, **fields):
    return ("event: " + kind + "\ndata: " + json.dumps({"type": kind, **fields}) + "\n\n").encode()


def stream(stop: str, tool: str = "") -> bytes:
    called = (event("content_block_start", index=0, content_block={"type": "tool_use", "id": "t", "name": tool, "input": {}})
              + event("content_block_stop", index=0)) if tool else b""
    return (event("message_start", message={"id": "m", "usage": {"input_tokens": 0, "output_tokens": 0}}) + called
            + event("message_delta", delta={"stop_reason": stop}, usage={"input_tokens": 9, "cache_read_input_tokens": 5000,
                                                                        "output_tokens": 6})
            + event("message_stop"))


class Gateway(BaseHTTPRequestHandler):
    """첫 메시지가 `tool:` 로 시작하는 스트림은 도구 호출(Bash)에서 멈추고, 나머지는 턴을 끝낸다. 데우기에는 캐시를 읽힌 답을 준다."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if body.get("stream"):
            first = body["messages"][0]["content"][0]["text"]
            data, kind = (stream("tool_use", "Bash") if first.startswith("tool:") else stream("end_turn")), "text/event-stream"
        else:
            data, kind = json.dumps({"type": "message", "stop_reason": "max_tokens", "usage": {
                "input_tokens": 3, "cache_read_input_tokens": 5000, "output_tokens": 1}}).encode(), "application/json"
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class Refusing(BaseHTTPRequestHandler):
    """옛 프록시 — 모르는 길에 403 으로 답한다."""

    def log_message(self, *args):
        pass

    def do_POST(self):
        self.send_response(403)
        self.send_header("Content-Length", "0")
        self.end_headers()


def turn(first: str) -> dict:
    return {"model": "claude-opus-5-5", "stream": True, "max_tokens": 64000,
            "metadata": {"user_id": json.dumps({"session_id": SESSION})}, "thinking": {"type": "adaptive"},
            "system": [{"type": "text", "text": "agent", "cache_control": {"type": "ephemeral"}}],
            "tools": [{"name": "Bash", "description": "run", "input_schema": {"type": "object"}}],
            "messages": [{"role": "user", "content": [{"type": "text", "text": first, "cache_control": {"type": "ephemeral"}}]}]}


def launch_line(command: str) -> str:
    """레인 기록의 assistant 줄 — 러너를 띄운 셸 호출(Claude Code 의 대화 기록 꼴)."""
    return json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": command}}]}}) + "\n"


class RunnerWaitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix="pgpt-runner-")
        proxy.LOG_PATH = Path(cls.work.name) / "proxy.log"
        proxy.CACHE_WARM_MIN_BYTES = 10
        cls.gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
        proxy._UPSTREAM = proxy.UpstreamTarget(f"http://127.0.0.1:{cls.gateway.server_port}")
        proxy._GATEWAY_MODELS = proxy.GatewayModelList(f"http://127.0.0.1:{cls.gateway.server_port}", ttl=0, retry=1, timeout=1)
        cls.server = proxy.ProxyServer(("127.0.0.1", 0), proxy.ProxyHandler)
        cls.refusing = ThreadingHTTPServer(("127.0.0.1", 0), Refusing)
        for server in (cls.gateway, cls.server, cls.refusing):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        # 사내 꼴의 주소 — 끝에 게이트웨이 길이 붙는다. 러너의 알림은 그 원점의 로컬 문으로 간다
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/gpgpta01-gpt/"

    @classmethod
    def tearDownClass(cls):
        for server in (cls.server, cls.gateway, cls.refusing):
            server.shutdown()
            server.server_close()
        cls.work.cleanup()

    def setUp(self):
        proxy._WARMER = proxy.CacheWarmer(3, 240.0)
        self.home = tempfile.TemporaryDirectory(prefix="claude-home-")
        self.addCleanup(self.home.cleanup)
        # 260 자를 넘는 기록은 긴 경로 머리로만 지워진다 — 먼저 돈다(뒤에 단 것이 앞서 돈다)
        self.addCleanup(shutil.rmtree, common.long_path(self.home.name), True)

    def send(self, payload: dict, headers: dict | None = None) -> None:
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request("POST", "/gpgpta01-gpt/v1/messages?beta=true", json.dumps(payload).encode(),
                         {"Content-Type": "application/json", "Authorization": "Bearer k", **(headers or {})})
            conn.getresponse().read()
            deadline = time.monotonic() + 2
            while proxy.stats()["active_requests"] and time.monotonic() < deadline:
                time.sleep(0.01)
        finally:
            conn.close()

    def ping_due(self) -> list[str]:
        """간격이 지난 것으로 치고 고른 대화를 그 자리에서 데운다 — 데운 대화의 첫 메시지들."""
        picked = proxy._WARMER.due(time.monotonic() + 240.0)
        for entry in picked:
            proxy.cache_warm_ping(proxy._WARMER, entry)
        return sorted(json.loads(entry.body)["messages"][0]["content"][0]["text"] for entry in picked)

    def runner_env(self, session: str = SESSION, base_url: str | None = None) -> dict:
        """러너가 부른 Claude 의 Bash 에서 받는 환경 — 세션 번호 · 요청이 지나는 주소 · 설정 폴더."""
        return {"CLAUDE_CODE_SESSION_ID": session, "ANTHROPIC_BASE_URL": base_url or self.base_url,
                "CLAUDE_CONFIG_DIR": self.home.name}

    def lane_record(self, lane: str, line: str, home: str | None = None) -> None:
        # 긴 경로 머리로 짓는다 — 머리 없이는 260 자를 넘는 기록을 이 검사가 못 짓는다
        folder = Path(common.long_path(home or self.home.name)) / "projects" / "C--work" / SESSION / "subagents"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"agent-{lane}.jsonl").write_text(line, encoding="utf-8")

    def warm_while_running(self, env: dict, rounds: int = 5) -> list[list[str]]:
        """러너가 도는 동안(알림이 짧은 간격으로 나간다) 데우기를 ``rounds`` 번 돌리고, 끝난 뒤 넷을 더 돌린다 — 판마다 데운 대화들.
        도는 동안의 판은 그 판 앞에 새 알림이 닿은 뒤에 돈다."""
        warmed = []
        with common.waiting_notice(f"C:/work/{OUT_NAME}", env=env, every=0.02):
            for _ in range(rounds):
                seen = proxy.stats()["runner_waits"]
                deadline = time.monotonic() + 3
                while proxy.stats()["runner_waits"] == seen and time.monotonic() < deadline:
                    time.sleep(0.01)
                warmed.append(self.ping_due())
        time.sleep(0.1)    # 나가 있던 알림이 닿게 둔다 — 그 뒤로는 알림이 없다
        return warmed + [self.ping_due() for _ in range(4)]

    def test_the_main_that_called_a_runner_is_warmed_while_it_runs_and_stops_three_pings_after(self):
        # 기대값 — 메인이 부른 러너(부른 레인이 없다)가 도는 동안 메인은 세 번에서 안 끊기고, 끝나면 마지막 알림 뒤 세 번째에서 멈춘다
        self.send(turn("main"))
        warmed = self.warm_while_running(self.runner_env())
        self.assertEqual(warmed[:5], [["main"]] * 5)
        self.assertLessEqual(warmed[5:].count(["main"]), 3)
        self.assertEqual(warmed[-1], [])

    def test_the_lane_that_called_a_runner_and_the_main_are_warmed_but_not_a_sibling(self):
        # 기대값 — 러너를 부른 레인(제 기록의 셸 호출에 답 파일 이름이 든 레인)과 메인은 이어지고, 곁의 레인은 제 횟수에서 멈춘다
        self.send(turn("main"))
        self.send(turn("tool: caller"), {LANE_ID_HEADER: "acaller"})
        self.send(turn("tool: sibling"), {LANE_ID_HEADER: "asibling"})
        self.lane_record("acaller", launch_line(f'pythonw agy_bg.py --prompt-file p.md --out "C:/work/{OUT_NAME}" --cwd .'))
        self.lane_record("asibling", launch_line("git status"))
        warmed = self.warm_while_running(self.runner_env())
        self.assertEqual(warmed[:3], [["main", "tool: caller", "tool: sibling"]] * 3)
        self.assertEqual(warmed[3:5], [["main", "tool: caller"]] * 2)

    def test_every_runner_run_sends_the_notice_while_it_runs(self):
        # 러너 셋은 한 판을 공유 부품의 `main` 으로 돈다 — 그 판이 도는 동안 알림이 나가고, 판의 종료 코드 · 답은 그대로다
        self.send(turn("main"))
        out = Path(self.home.name) / OUT_NAME
        seen = proxy.stats()["runner_waits"]

        def build_parser():
            parser = common.Parser(add_help=False)
            parser.add_argument("--out", required=True)
            return parser

        def run(args):
            deadline = time.monotonic() + 3
            while proxy.stats()["runner_waits"] == seen and time.monotonic() < deadline:
                time.sleep(0.01)
            common.write(args.out, "answer\n")
            return 0

        saved_argv, saved_env = sys.argv, {key: os.environ.get(key) for key in self.runner_env()}
        sys.argv = ["runner.py", "--out", str(out)]
        os.environ.update(self.runner_env())
        try:
            code = common.main(build_parser, lambda: "", run, "[test-bg]", {"ok": 0, "usage": 4, "failed": 1})
        finally:
            sys.argv = saved_argv
            for key, value in saved_env.items():
                os.environ.pop(key, None) if value is None else os.environ.__setitem__(key, value)
        self.assertEqual((code, out.read_text(encoding=common.ANSWER_ENCODING)), (0, "answer\n"))
        self.assertGreater(proxy.stats()["runner_waits"], seen)

    def test_the_caller_lane_is_found_only_by_a_command_that_names_the_answer_file(self):
        # 기대값 — 셸 호출의 명령에 답 파일 이름이 든 레인 하나만 부른 레인이다. 이름이 명령 밖(읽기 도구)에만 들거나, 둘 이상의
        # 레인이 들면 레인을 어림하지 않는다(빈 글 — 프록시는 메인만 잇는다). 다른 세션의 기록은 안 본다
        read_only = json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": f"C:/work/{OUT_NAME}"}}]}}) + "\n"
        self.lane_record("areader", read_only)
        # 이름이 더 긴 이름의 꼬리로만 든 명령(다른 러너의 답 파일)은 부른 레인이 아니다
        self.lane_record("alonger", launch_line(f"python agy_bg.py --out C:/work/old-{OUT_NAME} && type C:\\work\\final_{OUT_NAME}"))
        self.assertEqual(common.caller_lane(SESSION, OUT_NAME, self.home.name), "")
        self.lane_record("acaller", launch_line(f"python codex_copilot_bg.py --out C:\\work\\{OUT_NAME}"))
        self.assertEqual(common.caller_lane(SESSION, OUT_NAME, self.home.name), "acaller")
        self.assertEqual(common.caller_lane("bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeeeee", OUT_NAME, self.home.name), "")
        self.lane_record("atwin", launch_line(f"python codex_copilot_bg.py --out C:/other/{OUT_NAME}"))
        self.assertEqual(common.caller_lane(SESSION, OUT_NAME, self.home.name), "")

    def test_the_lane_records_are_read_only_at_the_start_of_a_run(self):
        # 부른 레인을 찾는 판은 러너가 뜬 뒤 처음 두 번뿐이다 — 러너를 띄운 호출은 그때 이미 기록에 있다. 메인이 부른 판(못 찾는다)도
        # 러너가 도는 내내 기록을 다시 훑지 않는다
        calls = []
        real = common.caller_lane

        def counting(*args):
            calls.append(args)
            return real(*args)

        common.caller_lane = counting
        before = proxy.stats()["runner_waits"]
        try:
            with common.waiting_notice(OUT_NAME, env=self.runner_env(), every=0.01):
                deadline = time.monotonic() + 3
                while proxy.stats()["runner_waits"] < before + 6 and time.monotonic() < deadline:
                    time.sleep(0.01)
        finally:
            common.caller_lane = real
        self.assertGreaterEqual(proxy.stats()["runner_waits"], before + 6)
        self.assertEqual(len(calls), 2)

    def test_the_caller_lane_is_found_when_the_record_path_is_longer_than_260_characters(self):
        # 작업 자리 이름을 접은 기록 폴더 이름이 길면 레인 기록의 경로가 윈도의 옛 한도(260 자)를 넘는다 — 그래도 찾는다
        deep = Path(self.home.name) / ("d" * 160)
        self.lane_record("acaller", launch_line(f"pythonw agy_bg.py --out C:/work/{OUT_NAME}"), home=str(deep))
        self.assertGreater(len(str(deep / "projects" / "C--work" / SESSION / "subagents" / "agent-acaller.jsonl")), 260)
        self.assertEqual(common.caller_lane(SESSION, OUT_NAME, str(deep)), "acaller")

    def test_no_notice_without_a_claude_caller_or_a_loopback_proxy(self):
        # 부른 쪽이 Claude 가 아니거나(세션 번호가 없다) 요청이 루프백 프록시를 안 지나면(사외 · 게이트웨이 직결) 알리지 않는다
        for env in ({**self.runner_env(), "CLAUDE_CODE_SESSION_ID": ""},
                    self.runner_env(base_url="http://aigpt.example/gpgpta01-gpt"),
                    self.runner_env(base_url="https://127.0.0.1:18901/gpgpta01-gpt"),
                    {**self.runner_env(), "ANTHROPIC_BASE_URL": ""}):
            notice = common.waiting_notice(OUT_NAME, env=env)
            with notice:
                pass
            self.assertIsNone(notice.thread, env)
        for url in ("http://localhost:18901/x", "http://[::1]:18901/x", "http://127.0.0.1:18901"):
            self.assertIsNotNone(common.loopback_proxy({"ANTHROPIC_BASE_URL": url}), url)

    def test_a_silent_old_or_absent_proxy_does_not_hold_the_runner(self):
        # 답 없는 프록시(받기만 한다) 앞에서도 알림이 러너의 걸음을 붙잡지 않고, 옛 프록시(403) · 꺼진 프록시에는 조용히 진다
        silent = socket.socket()
        silent.bind(("127.0.0.1", 0))
        silent.listen(8)
        self.addCleanup(silent.close)
        started = time.monotonic()
        with common.waiting_notice(OUT_NAME, env=self.runner_env(base_url=f"http://127.0.0.1:{silent.getsockname()[1]}/x")):
            pass
        self.assertLess(time.monotonic() - started, NOTICE_HOLD_MOST)
        self.assertEqual(common.notify_waiting(("127.0.0.1", self.refusing.server_port), SESSION, ""), 403)
        with socket.socket() as spare:
            spare.bind(("127.0.0.1", 0))
            closed = spare.getsockname()[1]
        self.assertIsNone(common.notify_waiting(("127.0.0.1", closed), SESSION, ""))

    def test_the_header_the_claude_runner_sets_makes_the_proxy_drop_its_finished_conversation(self):
        # 기대값 — 루프백 프록시를 지나는 자리에서 Claude 러너가 받는 Claude 에 싣는 머리(있던 머리는 둔다)를 이 프록시가 알아보고,
        # 답하고 끝난 그 대화를 데울 목록에 안 남긴다. 사람이 손으로 띄운 `claude -p`(머리 없음)는 남는다. 프록시가 없는 자리에서는
        # 러너가 머리를 안 싣는다
        env = claude_bg.child_env({"ANTHROPIC_BASE_URL": self.base_url, "ANTHROPIC_CUSTOM_HEADERS": "x-keep: 1",
                                   "CLAUDE_CODE_SESSION_ID": SESSION})
        lines = env["ANTHROPIC_CUSTOM_HEADERS"].split("\n")
        self.assertEqual(lines[0], "x-keep: 1")
        self.assertNotIn("CLAUDE_CODE_SESSION_ID", env)
        name, value = (part.strip() for part in lines[-1].split(":", 1))
        self.send(turn("runner job"), {name: value})
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 0)
        self.send(turn("person's own"))
        self.assertEqual(proxy.stats()["cache_warm_sessions"], 1)
        away = claude_bg.child_env({"ANTHROPIC_BASE_URL": "http://aigpt.example/gpgpta01-gpt", "ANTHROPIC_CUSTOM_HEADERS": "x-keep: 1"})
        self.assertEqual(away["ANTHROPIC_CUSTOM_HEADERS"], "x-keep: 1")
        twice = claude_bg.child_env(env)
        self.assertEqual(twice["ANTHROPIC_CUSTOM_HEADERS"], env["ANTHROPIC_CUSTOM_HEADERS"])   # 이어 묻기로 또 띄워도 한 줄이다


if __name__ == "__main__":
    unittest.main(verbosity=2)
