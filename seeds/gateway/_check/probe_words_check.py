"""끝점 프로브가 **못 닿은 까닭을 사람 말로** 내나 (검증기마다 다른 칸).

층 — 쓰는 사람의 계약(회사 PC 에서 상태 문이 넘어지지 않고 까닭을 말한다)
걷는 조건 — 배관의 `_probe` 가 TLS 실패의 까닭을 더는 가르지 않거나, 앱이 OS 신뢰 저장소(truststore)를 안 끼면 걷는다

좌표 — 배관 씨앗은 claude-config 결정 0033 · 사본 규율은 0040 · 남기고 걷는 기준은 0148(스킬 check-design) — 전제를
재던 두 절과 닫힌 표 대조를 걷은 판정은 atelier #445(레인 B1) · 지키는 결함은 AI-prompt-helper #183.

    python -X utf8 _check/probe_words_check.py

내는 것 — 0 맞다 · 1 어긋났다(`_ssl_why` · `_probe` 가 그 갈래에서 넘어지거나 까닭을 버린다) · 2 못 쟀다(이 망의
리졸버가 없는 이름을 풀어 줘 「이름이 안 풀린다」 갈래를 못 밟았다).

바깥으로 안 나간다 — 루프백에 듣는 자리를 세워 거기로만 붙는다. 토큰도 안 쓴다.

**왜 이 검사가 있나.** `gateway._probe` 는 *"인증서를 검사 장비가 갈아 끼웠을 수 있어요"* 라고 말하려고 있는
함수다(사내 SSL 검사 장비가 바깥 도메인을 가로채 파이썬만 죽는 그 자리). 그 말의 괄호 안을 채우는 칸이
**검증기마다 다르다**:

  · OpenSSL 이 직접 거부      → `reason` 이 찬다 (`CERTIFICATE_VERIFY_FAILED`)
  · OS 신뢰 저장소를 낀 갈래   → 예외를 **손으로 지어** `verify_message`·`verify_code` 만
                                 달고 **`reason` 은 속성 자체가 없다**

`e.reason` 을 바로 읽으면 뒤엣 갈래에서 `AttributeError` 가 나고, 그것이 `except` 절 **안**에서 난 예외라 뒤의
`except OSError` 가 안 받아 `_probe` 밖으로 나간다 — **까닭을 말하려던 자리가 말 대신 넘어지고** 상태
문(`/api/status`)이 500 이 된다.

⚠ **깨지는 자리와 도는 자리가 갈린다.** 리눅스에서는 OS 신뢰 저장소를 끼워도 OpenSSL 판정이 그대로 남아 `reason`
  이 차므로 **아무리 돌려도 안 보인다.** 그래서 OS 갈래는 그 예외를 흉내 내 실물 `_probe` 의 `except` 절에 먹인다.

**무는 것 둘**
  까닭 고르기 — `gateway._ssl_why` 가 칸마다 무엇을 고르나(넘어지는 것까지 값으로 받는다)
  실물 말     — 실물 `gateway._probe` 가 갈래 다섯에서 넘어지지 않고 말을 내나
"""
import socket
import ssl
import sys
import threading
from pathlib import Path

from _verdict import (EXIT_MISMATCH, EXIT_UNMEASURED, edge, fails, passes, report, show,
                      unmeasured, unmeasureds)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from _plumb import gateway  # noqa: E402 — 배관은 선언이 고른다


# --- 까닭 고르기 — `_ssl_why` 가 칸마다 무엇을 드나 ----------------------------------

print("까닭 고르기 — gateway._ssl_why 가 칸마다 무엇을 고르나")
why_of = getattr(gateway, "_ssl_why", None)
report("까닭을 고르는 자가 있다 (gateway._ssl_why)", callable(why_of),
       ["없으면 `except ssl.SSLError` 가 e.reason 을 바로 읽던 그 판이다 —",
        "OS 검증기를 끼우는 날 AttributeError 로 넘어진다"])

if callable(why_of):
    def err(**kw):
        e = ssl.SSLCertVerificationError("바깥 메시지")
        for k, v in kw.items():
            setattr(e, k, v)
        return e

    def why(e):
        """`_ssl_why` 를 부르되 **넘어지는 것까지 값으로 받는다.**

        `e.reason` 직독 꼴이 살아 있으면 바로 아래 줄에서 `AttributeError` 가 난다. 그대로 두면 이 검사가 판정
        대신 역추적을 뱉고 거기서 죽어 실물 말 절이 한 줄도 안 돌고, 종료코드 1 이 「어긋났다」와 「검사가
        죽었다」를 뭉갠다. 넘어진 것도 값이라 표에 세워 빨강으로 받고, 뒤엣 갈래는 계속 잰다.
        """
        try:
            return why_of(e)
        except Exception as exc:                               # noqa: BLE001
            return f"<넘어졌다: {type(exc).__name__}: {exc}>"

    show("reason 이 차면 그것", why(err(reason="CERTIFICATE_VERIFY_FAILED")),
         "CERTIFICATE_VERIFY_FAILED")
    # OS 검증기 갈래 — reason 이 아예 없고 verify_message 만 있다
    show("reason 이 없으면 verify_message", why(err(verify_message="루트가 안 믿긴다")),
         "루트가 안 믿긴다")
    # 둘 다 있으면 표의 차례대로 — 앞엣것이 이긴다
    show("둘 다 있으면 표의 앞엣것",
         why(err(reason="CERTIFICATE_VERIFY_FAILED", verify_message="루트가 안 믿긴다")),
         "CERTIFICATE_VERIFY_FAILED")
    # 빈 값은 건너뛴다 — 고치면서 잃기 쉬운 자리다
    show("빈 reason 은 건너뛴다", why(err(reason="", verify_message="루트가 안 믿긴다")),
         "루트가 안 믿긴다")
    # 여느 OSError 가지 — 인자 두 칸으로 서면 strerror 가 말을 든다
    show("두 칸 꼴은 strerror 가 든다", why(ssl.SSLError(1, "악수가 끊겼다")), "악수가 끊겼다")
    # 아무 칸도 없으면 인자 첫 칸 — ⚠ `str(e)` 면 여기서 `"('악수가 끊겼다',)"` 가 나온다.
    # `ssl.SSLError` 가 인자 하나짜리를 튜플째 찍어 **괄호 안에 파이썬 문법이 샌다.**
    show("칸이 하나도 없으면 인자 첫 칸", why(ssl.SSLError("악수가 끊겼다")), "악수가 끊겼다")
    show("  그 자리에 튜플 문법이 안 샌다", "(" in why(ssl.SSLError("악수가 끊겼다")), False)
    show("인자도 없으면 SSL", why(ssl.SSLError()), "SSL")


# --- 실물 말 — 실물 `_probe` 가 갈래마다 무엇을 내나 --------------------------------

# 붙은 쪽이 ClientHello 를 보낼 때까지 기다리는 참을성. 클라이언트는 붙자마자 보내므로
# 넉넉하고, 안 오는 갈래(평문·그냥 끊긴 경우)에서는 여기서 풀려 서버가 안 매달린다.
CLIENT_HELLO_WAIT_S = 3


def plaintext_listener(reply=b"HTTP/1.1 400 Bad Request\r\n\r\n"):
    """루프백에 **평문으로** 듣는 자리 하나 — (소켓, 포트).

    자가서명 인증서를 굽지 않는 까닭: 그러려면 `openssl` 실행 파일이나 선언 안 된 의존이
    있어야 하는데 **씨앗 배관에는 실행 의존이 없고**, 이 결함이 사는 자리가 하필 윈도우라
    거기서 못 도는 검사가 되면 뜻이 없다. 평문 답을 받은 OpenSSL 이 TLS 레코드가 아니라며
    거부하면 `ssl.SSLError` 가 `reason`(`WRONG_VERSION_NUMBER`)을 달고 온다 — 여기 필요한
    것은 그 「reason 이 찬 꼴」 하나다.

    ⚠ **답하기 전에 ClientHello 를 먼저 읽는다.** 안 읽은 수신 버퍼를 둔 채 닫으면 TCP 는
      FIN 이 아니라 RST 로 끊고, **윈도우는 그 RST 를 받은 쪽에 이미 와 있던 바이트를
      버린다** — 방금 보낸 400 이 사라져 OpenSSL 이 읽을 것이 없고, `SSLError` 대신
      `ConnectionAbortedError(10053)` 이 올라와 `except OSError` 로 샌다. 그러면 이
      기준선은 악수 실패가 아니라 **연결 끊김**을 재게 된다. 먼저 비워 두면 닫기가 어느
      OS 에서든 그냥 FIN 이라, **이 함수는 OS 를 안 가른다.**
    """
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    srv.settimeout(5)

    def talk():
        try:
            conn, _ = srv.accept()
        except OSError:
            return
        try:
            conn.settimeout(CLIENT_HELLO_WAIT_S)
            try:
                conn.recv(4096)      # ← 비워야 아래 close 가 RST 가 안 된다 (곁말)
            except OSError:
                pass
            conn.sendall(reply)
        except OSError:
            pass
        finally:
            conn.close()

    threading.Thread(target=talk, daemon=True).start()
    return srv, srv.getsockname()[1]


print("\n실물 말 — 실물 _probe 가 갈래마다 말을 내나 (루프백만 · 바깥으로 안 나간다)")
srv, port = plaintext_listener()
try:
    # 기준선 ① — **진짜** 악수 실패. reason 이 찬 꼴이 그대로 말에 실리나.
    ok, why = gateway._probe(f"https://127.0.0.1:{port}/")
    show("진짜 악수 실패 — 안 닿았다고 한다", ok, False)
    show("  그 까닭이 말에 실린다", "WRONG_VERSION_NUMBER" in why, True)
    show("  이 함수의 존재 이유가 그대로 선다", "검사 장비가 갈아 끼웠을" in why, True)
    print(f"     └ {why}")
finally:
    srv.close()

# 기준선 ② — **음성 대조.** 평문(http)은 악수를 안 하므로 이 갈래로 안 온다. 이 줄이
# 없으면 위 초록이 「늘 그렇게 말한다」인지 「악수 갈래에서만 그렇다」인지 못 가른다.
srv2, port2 = plaintext_listener()
try:
    ok2, why2 = gateway._probe(f"http://127.0.0.1:{port2}/")
    show("평문은 열리기만 하면 닿은 것이다", (ok2, why2), (True, ""))
finally:
    srv2.close()

# 기준선 ③ — **아무도 안 듣는 자리.** 열리지도 않았으니 악수 이야기가 나오면 안 된다.
# ⚠ **어느 갈래로 오나는 OS 가 정한다.** 리눅스는 곧바로 거절(`ConnectionRefusedError`)이
#   오지만 **윈도우는 닫힌 루프백 포트에도 SYN 을 되쏘아 두어 초를 쓴다** — 손잡이
#   `REACH_TIMEOUT_S` 가 그보다 짧으면 거기서는 시간 초과 갈래로 떨어진다. 그래서 판정은
#   **어느 말이 오나가 아니라 악수 이야기를 안 하나**로 세운다: 저 갈림은 우리 결함이 아니고
#   손잡이를 우리가 못 정한다.
dead = socket.socket()
dead.bind(("127.0.0.1", 0))
dead_port = dead.getsockname()[1]
dead.close()
ok3, why3 = gateway._probe(f"http://127.0.0.1:{dead_port}/")
show("아무도 안 듣는 자리는 안 닿았다고 한다", ok3, False)
show("  악수 이야기를 안 한다 — 열리지도 않은 자리다", "보안 악수" in why3, False)
print(f"     └ {why3}")

# 기준선 ④ — **이름이 안 풀리는 자리.** RFC 2606 이 못박은 예약 이름이라 안 풀려야 한다.
# ⚠ 가로채는 리졸버가 있는 망에서는 풀린다 — 그때는 **빨강이 아니라 「못 쟀다」**다.
#   판정을 그대로 두면 망 사정이 우리 결함으로 찍힌다.
BAD_NAME = "seed-no-such-host-4f2a.invalid"
try:
    socket.getaddrinfo(BAD_NAME, 80)
    unmeasured("실물 말 — 이름이 안 풀리는 갈래",
               f"이 망의 리졸버가 {BAD_NAME} 를 풀어 준다")
except socket.gaierror:
    ok4, why4 = gateway._probe(f"http://{BAD_NAME}/")
    show("이름이 안 풀리면 안 닿았다고 한다", ok4, False)
    show("  이름 이야기를 한다 — 「연결이 안 돼요」와 다른 사건이다",
         "이름이 안 풀려요" in why4, True)
    print(f"     └ {why4}")

# 기준선 ⑤ — OS 검증기 갈래. 손으로 지은 예외가 **실물 `_probe` 의 except 절**을 지나 말이
# 되나. 저쪽 두 걸음(악수 동안 검증 끄기 · 뒤에 OS 검증기로 판정)은 여기서 못 밟으므로
# **악수 한 자리만** 갈아 끼운다 — `_probe` 도 `_ssl_why` 도 손 안 댄 실물이다.
#
# ⚠ **문장의 내용은 안 잡는다 — 그건 로케일 몫이다.** 이 자리에 실제로 오는 것은 OS
#   검증기가 **그 기계의 언어로** 낸 문장이라, 영문 한 줄을 박아 두고 그 영문을 다시 찾으면
#   *제가 먹인 것을 제가 찾는* 꼴이면서 로케일이 다른 기계의 실물과는 어긋난다. 붙잡는 것은
#   로케일을 안 타는 둘뿐이다 — 예외의 **꼴**과, 먹인 문장이 골라 버려지지 않고 실려 나오나.
OS_VERIFY_CODE = 0x800B0109      # CERT_E_UNTRUSTEDROOT — 뿌리가 안 믿긴다
OS_SENTENCE = "OS 검증기가 그 기계의 언어로 낸 문장"


class _OsVerifierCtx:
    """OS 신뢰 저장소 갈래가 악수 끝에 올리는 그 예외만 낸다."""

    def wrap_socket(self, sock, **kw):
        e = ssl.SSLCertVerificationError(OS_SENTENCE)
        e.verify_message = OS_SENTENCE      # ← OS 신뢰 저장소 갈래가 다는 칸
        e.verify_code = OS_VERIFY_CODE
        raise e from None


print()
# 흉내가 **실물 꼴**인가 — 여기가 어긋나면 아래 초록은 실물이 아닌 것을 통과시킨다.
# 넷 다 로케일을 안 탄다. 값은 흉내가 아니라 **그 흉내가 실제로 낸 예외**에서 읽는다.
try:
    _OsVerifierCtx().wrap_socket(None)
    raise AssertionError("흉내가 예외를 안 냈다 — 아래 판정이 잴 것이 없다")
except ssl.SSLCertVerificationError as exc:
    os_exc = exc
show("흉내가 실물 꼴인가 — 예외 이름", type(os_exc).__name__, "SSLCertVerificationError")
show("  reason 은 속성 자체가 없다", hasattr(os_exc, "reason"), False)
show("  verify_code 는 뿌리가 안 믿긴다는 그 값", hex(os_exc.verify_code), "0x800b0109")
show("  strerror 는 안 찬다 — 인자가 한 칸이라", os_exc.strerror, None)

srv3, port3 = plaintext_listener()
real_ctx = ssl.create_default_context
try:
    ssl.create_default_context = lambda *a, **k: _OsVerifierCtx()
    try:
        ok5, why5 = gateway._probe(f"https://127.0.0.1:{port3}/")
        report("OS 검증기 갈래 — _probe 가 안 넘어진다", True)
        show("  안 닿았다고 한다", ok5, False)
        show("  이 함수의 존재 이유가 그 갈래에서도 선다",
             "검사 장비가 갈아 끼웠을" in why5, True)
        # **괄호가 비면 안 된다** — 넘어지지만 않고 "SSL" 만 뱉으면 고친 값이 없다.
        # 찾는 것은 그 예외가 실제로 든 문장이다(문장의 **내용**은 로케일 몫이라 안 잰다).
        show("  OS 가 낸 문장을 골라 버리지 않고 싣는다",
             os_exc.verify_message in why5, True)
        print(f"     └ {why5}")
    except Exception as exc:                                   # noqa: BLE001
        report("OS 검증기 갈래 — _probe 가 안 넘어진다", False,
               [f"{type(exc).__name__}: {exc}",
                "app/gateway.py 의 `except ssl.SSLError` 가 e.reason 을 바로 읽고 있다 —",
                "그 예외는 except 절 **안**에서 나 뒤의 except OSError 가 안 받는다.",
                "까닭을 말하려던 자리가 말 대신 넘어져 상태 문이 500 이 된다."])
finally:
    ssl.create_default_context = real_ctx
    srv3.close()

print()
edge("여기서 안 재는 것 — **OS 신뢰 저장소가 실제로 내는 예외.** 그 두 걸음을 실물로 못 "
     "밟는다: 안 믿기는 인증서를 구울 도구가 씨앗에 없다. 위 흉내가 예외 꼴로 그 자리를 대신 들고, "
     "흉내의 꼴(`reason` 없음 · `verify_message`)이 저쪽 꾸러미의 지금 판과 맞나는 안 잰다")
edge("여기서 안 재는 것 — OS 검증기가 낸 문장의 **내용**. 로케일마다 다르므로 이 검사는 "
     "그 문장이 실려 나오나만 보고, 꼴은 로케일 안 타는 넷으로 붙잡는다")
edge(f"여기서 안 재는 것 — **연결 거절 갈래의 말**(`OSError` → `strerror`). 윈도우는 닫힌 "
     f"루프백 포트에도 두어 초를 써서 이 판의 손잡이"
     f"(`REACH_TIMEOUT_S`={gateway.REACH_TIMEOUT_S})로는 시간 초과가 먼저 온다 — 그 갈래의 "
     f"문구는 이 OS 에서 못 밟는다")
edge("여기서 안 재는 것 — 끝점 캐시(`gateway._reach_of`)가 한 번만 두드리나. 그 판정은 "
     "이 배관을 무는 앱의 상태 문 검사 몫이다")

bad = fails()
if bad:
    print(f"\n❌ {len(bad)}건 어긋남 — {', '.join(bad)}")
    sys.exit(EXIT_MISMATCH)
left = unmeasureds()
if left:
    print(f"\n⚠ 안 쟀다 — {', '.join(left)}")
    sys.exit(EXIT_UNMEASURED)
print(f"\n✅ 전부 통과 (판정 {len(passes())}건 — 까닭 고르기와 실물 말의 갈래 다섯, 항목은 머리말이 든다)")
