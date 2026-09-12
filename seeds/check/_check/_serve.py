"""문을 두드리는 한 벌 — 검사마다 제 것이던 포트 잡개와 두드리개를 모은다.

좌표 — AI-prompt-helper 이슈 #52 ② (이 판이 난 저장소) · 아뜰리에 `_check/_serve.py` (`stand`·`stop` 이 온 자리) ·
씨앗 규율은 claude-config 결정 0040.

⚠ **두 형제의 `knock` 이 다르다** — 아뜰리에는 `(주소, 경로, 몸통, 머리)` 로 부르고 앱의 모델 머리를
  늘 싣는다(`config` 를 문다). 씨앗은 헬퍼 꼴(`(포트, 경로, …)` · 앱을 안 문다)을 들고, 서버를 제
  프로세스 안에 세우는 `stand`·`stop` 은 아뜰리에에서 받았다. 아뜰리에가 이 판을 받으려면 부르는
  자리를 고쳐야 하므로 그쪽은 **일부러 갈렸다**로 두고 곁말이 그것을 든다(claude-config #25).

`free_port()` 는 넷(`server`·`admin`·`diagram`·`log`)에 **글자까지 같은 사본**이었고,
두드리개는 검사마다 제 것이라 이미 갈리기 시작했다 — 오류 본문을 읽는 가드는 넷 다
있었으나, **깨진 바이트를 견디는 것은 하나의 오류 갈래뿐**이었고(`diagram.get`) 나머지는
그 자리에서 역추적을 낸다. 다음 검사를 **어느 쪽에서 베끼느냐로** 그런 성질이 갈리는
자리라 한 벌로 모은다.

여기가 드는 것은 **포트와 두드리기**까지다. 앱의 머리 이름(`config.HEADER_KEY` 따위)을
어느 부름에 싣나 · 흘려 온 몸통(SSE)을 어떻게 여미나 · 무엇을 임시 자리로 돌리나는
**부르는 쪽 몫**이다 — 검사마다 다르고, 그 갈림이 곧 그 검사가 무는 것이라서다.

⚠ **몸통은 늘 `replace` 로 푼다.** 성공 갈래만 strict 로 두면 게이트웨이가 깨진 바이트를
  실어 보내는 날 검사가 **빨강 대신 역추적**을 내고, 뒤따르는 판정이 통째로 안 돈다.

⚠ **서버를 세우는 손(`stand`·`stop`)은 아뜰리에 판에서 받았다.** 헬퍼는 `ThreadingHTTPServer` 를
  세우는 자리 열하나가 검사의 절 본문 안에 살아 아직 이 손을 안 문다 — 그쪽이 이 판을 받으면
  그 열하나가 이리로 온다.
"""
import json
import shutil
import socket
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer


def stand(handler):
    """임의 포트에 서버를 제 프로세스 안에 세운다 — (포트, httpd). 끝나면 `stop()`.

    데몬 스레드라 검사가 죽어도 프로세스가 안 남는다. 주소가 필요하면 `f"http://127.0.0.1:{port}"`.
    """
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd.server_address[1], httpd


def stop(httpd, *tmps):
    """서버를 내리고 임시 자리를 치운다 — 두 벌이 서로 반쪽씩만 하던 마감(아뜰리에 #114 ④)."""
    httpd.shutdown()
    for t in tmps:
        shutil.rmtree(t, ignore_errors=True)


def free_port():
    """지금 아무도 안 쓰는 포트 하나 — 잡았다 놓는다."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def knock(port, path, body=None, method=None, headers=None, timeout=30, host="127.0.0.1"):
    """(상태, 응답 머리, 몸통 글자) — **오류 응답도 예외로 안 올리고 원문 그대로 든다.**

    **머리까지 지고 오는 까닭**은 이 앱의 응답이 둘이기 때문이다(결정 0021): 모델을 부르는
    문은 흘려 보내고(`text/event-stream`) 나머지는 한 덩이다. 「어느 문이 어느 꼴로 오나」가
    판정 중 하나라, 몸통만 보면 그 판정을 잴 재료가 없다.

    ⚠ **`body` 가 None 이면 몸통을 안 싣는다** — `{}` 를 싣는 것과 다른 부름이다.
      「빈 몸통을 보냈다」와 「몸통이 없다」를 문이 갈라 보는 자리가 있어서다.
    ⚠ **`headers` 의 값이 None 인 칸은 안 싣는다** — 부르는 쪽이 「이 부름에는 키가
      없다」를 빈 글자가 아니라 None 으로 말하게 두려는 것이다.
    """
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"http://{host}:{port}{path}", data=data, method=method)
    if data is not None:
        req.add_header("content-type", "application/json")
    for name, value in (headers or {}).items():
        if value is not None:
            req.add_header(name, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read().decode("utf-8", "replace")


def as_json(status, text):
    """(상태, JSON) — 안 열리면 죽지 않고 **원문 도막**을 들려 보낸다.

    빈 사전이 아니라 원문을 드는 까닭은 판정이 까닭을 말하게 하려는 것이다 — 빈 사전은
    「몸통이 비었다」와 「JSON 이 아니었다」를 같은 얼굴로 만든다.
    """
    try:
        return status, json.loads(text)
    except ValueError:
        return status, {"_원문": text[:200]}


def jknock(port, path, **kw):
    """(상태, JSON) — `knock` 의 JSON 방언. 진본은 `knock` 하나다."""
    status, _head, text = knock(port, path, **kw)
    return as_json(status, text)
