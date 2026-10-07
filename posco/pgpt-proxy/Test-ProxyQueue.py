"""v21/v22 queue/cancellation regressions against a local, event-controlled gateway.

Run: python tests/Test-ProxyQueue.py. No company gateway or credentials are used.
"""
from __future__ import annotations

import concurrent.futures
import http.client
import importlib.util
import json
import os
import re
import select
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "/gpgpta01-gpt"
spec = importlib.util.spec_from_file_location("proxy", ROOT / "opus5_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)


class Control:
    def __init__(self, status=200, blocked=False):
        self.status = status
        self.entered = threading.Event()
        self.release = threading.Event()
        self.received = None
        self.disconnected = threading.Event()
        if not blocked:
            self.release.set()


CONTROLS: dict[str, Control] = {}


class Gateway(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def handle(self):
        try:
            super().handle()
        except ConnectionError:
            pass  # Expected when cancellation tests close a pooled connection.

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        control = CONTROLS[payload["test_id"]]
        control.received = payload
        control.entered.set()
        deadline = time.monotonic() + 10
        while not control.release.wait(0.05) and time.monotonic() < deadline:
            try:
                readable, _, _ = select.select([self.connection], [], [], 0)
                if readable and not self.connection.recv(1, socket.MSG_PEEK):
                    control.disconnected.set()
                    return
            except OSError:
                control.disconnected.set()
                return
        data = json.dumps({"ok": True, "test_id": payload["test_id"]}).encode()
        try:
            self.send_response(control.status)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Content-Type", "application/json")
            self.send_header("x-pgpt-request-id", "test-" + payload["test_id"])
            self.end_headers()
            self.wfile.write(data)
        except OSError:
            pass


class QueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
        threading.Thread(target=cls.gateway.serve_forever, daemon=True).start()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.work = tempfile.TemporaryDirectory(prefix="pgpt-queue-")
        source = Path(cls.work.name) / "opus5_proxy.py"
        shutil.copy(ROOT / "opus5_proxy.py", source)
        env = dict(os.environ, PGPT_PROXY_PORT=str(cls.port),
                   PGPT_PROXY_UPSTREAM=f"http://127.0.0.1:{cls.gateway.server_port}",
                   PGPT_PROXY_HEAVY_BYTES="512", PGPT_PROXY_HEAVY_CONCURRENCY="1",
                   PGPT_PROXY_HEAVY_QUEUE_TIMEOUT_SEC="1.5",
                   PGPT_PROXY_EXECUTION_LIMIT_SEC="0.5", PGPT_PROXY_EXECUTION_LIMIT_MARGIN_SEC="0.05")
        cls.proc = subprocess.Popen([sys.executable, str(source)], env=env)
        cls.pool = concurrent.futures.ThreadPoolExecutor(max_workers=8)
        for _ in range(50):
            try:
                cls.health()
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("proxy did not start")

    @classmethod
    def tearDownClass(cls):
        for control in CONTROLS.values():
            control.release.set()
        cls.pool.shutdown(wait=True)
        cls.proc.terminate()
        cls.proc.wait(5)
        cls.gateway.shutdown()
        cls.gateway.server_close()
        cls.work.cleanup()

    def tearDown(self):
        for control in CONTROLS.values():
            control.release.set()
        self.wait_for(lambda: self.health()["active_requests"] == 0)

    @classmethod
    def call(cls, path, payload=None, *, port=None):
        conn = http.client.HTTPConnection("127.0.0.1", port or cls.port, timeout=8)
        try:
            conn.request("POST" if payload else "GET", path,
                         body=json.dumps(payload).encode() if payload else None,
                         headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_SECRET"})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    @classmethod
    def health(cls):
        return json.loads(cls.call("/health")[2])

    def wait_for(self, predicate, timeout=4):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.02)
        self.fail("condition timed out")

    def payload(self, name, model="claude-opus-5", **kwargs):
        return {"test_id": name, "model": model, "messages": [
            {"role": "user", "content": "PRIVATE_PROMPT_" + "x" * 1024}], **kwargs}

    def start(self, name, status=200, blocked=False, model="claude-opus-5", path=None, **kwargs):
        control = Control(status, blocked)
        CONTROLS[name] = control
        future = self.pool.submit(self.call, path or BASE + "/v1/messages", self.payload(name, model, **kwargs))
        return control, future

    def raw_start(self, name):
        control = Control(blocked=True)
        CONTROLS[name] = control
        data = json.dumps(self.payload(name)).encode()
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        sock.sendall((f"POST {BASE}/v1/messages HTTP/1.1\r\nHost: localhost\r\n"
                      f"Content-Type: application/json\r\nContent-Length: {len(data)}\r\n\r\n").encode() + data)
        return control, sock

    def test_provider_queues_do_not_block_each_other(self):
        claude, first = self.start("provider_claude", blocked=True)
        self.assertTrue(claude.entered.wait(2))
        for name, model, path in (
            ("provider_openai", "gpt-6-astra", BASE + "/v1/responses"),
            ("provider_gemini", "gemini-3.6-flash", BASE + "/v1beta/models/gemini-3.6-flash:generateContent"),
            ("provider_xai", "grok-4.1", BASE + "/v1/chat/completions"),
        ):
            control, future = self.start(name, model=model, path=path)
            self.assertTrue(control.entered.wait(1), name)
            self.assertEqual(future.result(2)[0], 200)
        self.assertFalse(first.done())
        self.assertEqual(self.health()["heavy_by_provider"]["anthropic"]["heavy_active"], 1)
        claude.release.set()
        self.assertEqual(first.result(2)[0], 200)

    def test_default_allows_large_requests_without_local_429(self):
        work = Path(self.work.name) / "default"
        work.mkdir()
        source = work / "opus5_proxy.py"
        shutil.copy(ROOT / "opus5_proxy.py", source)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ, PGPT_PROXY_PORT=str(port),
                   PGPT_PROXY_UPSTREAM=f"http://127.0.0.1:{self.gateway.server_port}",
                   PGPT_PROXY_HEAVY_CONCURRENCY="1", PGPT_PROXY_HEAVY_QUEUE_TIMEOUT_SEC="0")
        env.pop("PGPT_PROXY_HEAVY_BYTES", None)  # exercise the shipped default
        proc = subprocess.Popen([sys.executable, str(source)], env=env)
        try:
            for _ in range(50):
                try:
                    health = json.loads(self.call("/health", port=port)[2])
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                self.fail("default proxy did not start")
            self.assertFalse(health["heavy_gate_enabled"])
            self.assertEqual(health["heavy_request_bytes"], 0)
            for provider, model, path in (
                ("claude", "claude-opus-5", BASE + "/v1/messages"),
                ("openai", "gpt-6-astra", BASE + "/v1/responses"),
            ):
                with self.subTest(provider=provider):
                    name = "default_" + provider
                    holder = Control(blocked=True)
                    CONTROLS[name] = holder
                    payload = self.payload(name, model)
                    payload["messages"][0]["content"] = "x" * 250_000
                    first = self.pool.submit(self.call, path, payload, port=port)
                    try:
                        self.assertTrue(holder.entered.wait(2))
                        second = Control()
                        CONTROLS[name + "_second"] = second
                        payload = dict(payload, test_id=name + "_second")
                        status, _, _ = self.call(path, payload, port=port)
                        self.assertEqual(status, 200)
                        self.assertTrue(second.entered.is_set())
                        self.assertFalse(first.done(), "first request must still be occupying the service")
                    finally:
                        holder.release.set()
                        first.result(3)
            health = json.loads(self.call("/health", port=port)[2])
            self.assertEqual(health["heavy_queue_timeouts"], 0)
            self.assertEqual(health["heavy_serialized"], 0)
        finally:
            proc.terminate()
            proc.wait(5)

    def test_timeout_returns_retryable_429_without_upstream_bypass(self):
        holder, first = self.start("timeout_holder", blocked=True)
        self.assertTrue(holder.entered.wait(2))
        before = self.health()
        queued, second = self.start("timeout_queued")
        status, headers, data = second.result(3)
        self.assertEqual(status, 429)
        self.assertEqual(headers.get("Retry-After"), "5")
        self.assertEqual(json.loads(data)["error"]["code"], "proxy_queue_timeout")
        self.assertFalse(queued.entered.is_set())
        after = self.health()
        self.assertEqual(after["heavy_queue_timeouts"], before["heavy_queue_timeouts"] + 1)
        self.assertEqual(after["execution_cuts"], before["execution_cuts"])
        holder.release.set()
        self.assertEqual(first.result(2)[0], 200)
        self.assertFalse(queued.entered.is_set())

    def test_cancelled_queue_entry_is_removed_and_never_sent(self):
        holder, first = self.start("cancel_holder", blocked=True)
        self.assertTrue(holder.entered.wait(2))
        before = self.health()["client_cancellations"]
        queued, sock = self.raw_start("cancel_queued")
        try:
            self.wait_for(lambda: self.health()["heavy_waiting"] == 1)
        finally:
            sock.close()
        self.wait_for(lambda: self.health()["heavy_waiting"] == 0)
        self.assertFalse(queued.entered.is_set())
        self.assertEqual(self.health()["client_cancellations"], before + 1)
        holder.release.set()
        self.assertEqual(first.result(2)[0], 200)
        self.assertFalse(queued.entered.is_set())

    def test_cancel_while_waiting_for_headers_releases_gate(self):
        control, sock = self.raw_start("cancel_upstream")
        try:
            self.assertTrue(control.entered.wait(2))
        finally:
            sock.close()
        self.wait_for(lambda: self.health()["heavy_active"] == 0)
        self.assertTrue(control.disconnected.wait(1), "cancelled upstream socket stayed open")
        next_control, next_call = self.start("after_cancel")
        self.assertTrue(next_control.entered.wait(1))
        self.assertEqual(next_call.result(2)[0], 200)
        self.assertFalse(control.release.is_set())

    def test_small_request_bypasses_busy_provider_gate(self):
        holder, first = self.start("small_holder", blocked=True)
        self.assertTrue(holder.entered.wait(2))
        control = Control()
        CONTROLS["small_bypass"] = control
        status, _, _ = self.call(BASE + "/v1/messages", {
            "test_id": "small_bypass", "model": "claude-opus-5", "messages": []})
        self.assertEqual(status, 200)
        self.assertTrue(control.entered.is_set())
        self.assertFalse(first.done())
        holder.release.set()
        self.assertEqual(first.result(2)[0], 200)

    def test_queue_time_does_not_count_as_gateway_execution(self):
        holder, first = self.start("clock_holder", blocked=True)
        self.assertTrue(holder.entered.wait(2))
        before = self.health()["execution_cuts"]
        queued, second = self.start("clock_fast500", status=500)
        self.wait_for(lambda: self.health()["heavy_waiting"] == 1)
        time.sleep(0.7)  # longer than fake execution limit; entirely local queue time
        holder.release.set()
        self.assertEqual(first.result(2)[0], 200)
        self.assertEqual(second.result(2)[0], 500)
        self.wait_for(lambda: self.health()["active_requests"] == 0)
        self.assertEqual(self.health()["execution_cuts"], before)
        text = (Path(self.work.name) / "proxy.log").read_text(encoding="utf-8")
        line = next(line for line in text.splitlines() if "complete POST" in line and "gw=test-clock_fast500" in line)
        queue_sec, upstream_sec = re.search(r"queue=([\d.]+)s .*upstream=([\d.]+)s", line).groups()
        self.assertGreater(float(queue_sec), 0.5)
        self.assertLess(float(upstream_sec), 0.45)

    def test_effort_preserved_and_immediate_rejection_is_logged(self):
        control, future = self.start("effort_reject", status=400, stream=True,
                                     output_config={"effort": "max"}, thinking={"type": "adaptive"})
        self.assertEqual(future.result(2)[0], 400)
        self.assertEqual(control.received["output_config"], {"effort": "max"})
        self.assertEqual(control.received["thinking"], {"type": "adaptive"})
        self.wait_for(lambda: self.health()["active_requests"] == 0)
        text = (Path(self.work.name) / "proxy.log").read_text(encoding="utf-8")
        line = next(line for line in text.splitlines() if "complete POST" in line and "gw=test-effort_reject" in line)
        for token in ("HTTP 400", "effort=max", "thinking=adaptive", "queue=", "upstream=", "model=claude-opus-5"):
            self.assertIn(token, line)
        self.assertNotIn("PRIVATE_PROMPT_", text)
        self.assertNotIn("TEST_SECRET", text)

    def test_slow_4xx_is_not_an_execution_cut(self):
        before = self.health()["execution_cuts"]
        control, future = self.start("slow400", status=400, blocked=True)
        self.assertTrue(control.entered.wait(2))
        time.sleep(0.6)
        control.release.set()
        self.assertEqual(future.result(2)[0], 400)
        self.wait_for(lambda: self.health()["active_requests"] == 0)
        self.assertEqual(self.health()["execution_cuts"], before)

    def test_fifo_and_zero_timeout(self):
        gate = proxy.HeavyGate(1)
        self.assertTrue(gate.acquire(0)[0])
        self.assertFalse(gate.acquire(0)[0])
        order = []

        def take(index):
            admitted, _ = gate.acquire(2)
            if admitted:
                order.append(index)
                gate.release()

        futures = []
        for index in range(4):
            futures.append(self.pool.submit(take, index))
            self.wait_for(lambda: gate.stats()["heavy_waiting"] == index + 1)
        gate.release()
        for future in futures:
            future.result(3)
        self.assertEqual(order, [0, 1, 2, 3])
        self.assertEqual(gate.stats(), {"heavy_active": 0, "heavy_waiting": 0})


if __name__ == "__main__":
    unittest.main(verbosity=2)
