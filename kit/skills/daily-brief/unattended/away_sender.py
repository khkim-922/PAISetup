"""자리 밖에서 보기의 보내는 손 — 시계 판이 사람 없이 띄운 보고가 지은 보고 한 장을 메일 한 장으로 지어 표준 입력으로 주면, 사용자가 켤 때 적어 둔 본인
주소 하나를 받는 사람과 보내는 사람으로 삼아 회사 메일 손의 사내 중계(`mailer.py` 의 `send`)로 한 통 보낸다.

    python -X utf8 -I away_sender.py --dir <사용자 폴더> --hand <회사 메일 손 mail.py>   < {"subject": …, "html": …, "text": …}

받는 사람을 받는 칸이 없다 — 주소는 사용자 폴더의 보고 시각표(`daily-brief-schedule.json`)의 `away.address` 한 자리에서만 읽는다(사용자가 켤 때 판의 코드가
주소록의 「나」에서 받아 적은 것).

내는 것 — 끝 줄 한 줄(주소 · 제목 · 본문은 안 싣는다 — 중계의 거절 말은 주소를 들어 옮기지 않는다).
종료 값 — 0 보냈다 · 4 중계에 넘기기 전에 졌다(연결 · 이름 찾기 · 거절 코드 · 설정 — 다시 보내도 두 통이 안 된다) · 5 넘기는 도중이나 뒤에
졌다(중계가 받았는지 모른다 — 다시 보내면 두 통일 수 있어 다시 안 보낸다) · 2 인자가 틀렸다.

이 손만 형제 스킬의 코드(`mailer.py`)를 싣는다 — 그 손은 명령이 없는 라이브러리라 싣는 것이 그 손을 부르는 길이다. 시계 판은 이 손을 프로세스로
띄워, 그 손이 바뀌거나 없어도 판은 안 깨지고 「못 보냈다」만 적는다.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import smtplib
import socket
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "scripts"), str(HERE)]   # 같은 스킬의 바탕(scripts/)을 먼저 · 곁의 모듈 — `-I` 로 돌아도 싣는다
import unattended_const as C  # noqa: E402
import unattended_store as st  # noqa: E402
from brief_schedule import away_of, read_brief  # noqa: E402


def handed(exc: BaseException, mailer) -> bool:
    """중계에 글을 넘기기 시작한 뒤에 진 것인가. 중계가 거절 코드로 답했으면 안 받은 것이고, 글(DATA)을 보내기 전에 진 것도 안 간 것이다.
    글을 보내는 걸음(`smtplib.SMTP.data`) 안에서 거절 코드 없이 진 것만 받았는지 모른다."""
    if isinstance(exc, (smtplib.SMTPResponseException, smtplib.SMTPRecipientsRefused, mailer.MailError)):
        return False
    tb = exc.__traceback__
    while tb is not None:
        code = tb.tb_frame.f_code
        if code.co_name == "data" and pathlib.Path(code.co_filename).name == pathlib.Path(smtplib.__file__).name:
            return True
        tb = tb.tb_next
    return False


def why(exc: BaseException, mailer) -> str:
    """사람이 읽는 까닭 한 구절 — 예외의 말은 안 옮긴다(거절된 주소를 든다)."""
    if isinstance(exc, ConnectionRefusedError):
        return "사내 메일 중계가 연결을 받지 않았다"
    if isinstance(exc, socket.gaierror):
        return "사내 메일 중계의 이름을 못 찾았다 — 사내망 밖일 수 있다"
    if isinstance(exc, TimeoutError):
        return "사내 메일 중계가 시한 안에 답하지 않았다"
    if isinstance(exc, smtplib.SMTPResponseException):
        return f"사내 메일 중계가 {exc.smtp_code} 로 거절했다"
    if isinstance(exc, (smtplib.SMTPRecipientsRefused, mailer.MailRefused)):
        return "사내 메일 중계가 받는 사람을 거절했다"
    if isinstance(exc, mailer.MailConfigError):
        return "메일 보내기 설정(MAIL_*)이 틀렸다"
    if isinstance(exc, smtplib.SMTPServerDisconnected):
        return "사내 메일 중계가 도중에 끊었다"
    return f"보내다 멈췄다({type(exc).__name__})"


def address_of(folder: pathlib.Path) -> str:
    """켜 둔 자리 밖에서 보기의 본인 주소 — 꺼졌거나 없으면 "". 시각표를 못 읽으면 `st.Unreadable`(안 보낸다)."""
    away = away_of(read_brief(folder))
    if away.get("on") is not True or not isinstance(away.get("address"), str):
        return ""
    return away["address"].strip()


def main(argv: list[str] | None = None) -> int:
    """보내는 손의 입구 — 표준 입력의 메일 한 장을 본인 주소로 한 통 보낸다. 종료 값은 머리말이 든다."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="자리 밖에서 보기 — 표준 입력의 메일 한 장을 켤 때 적어 둔 본인 주소로 한 통 보낸다")
    ap.add_argument("--dir", required=True, help="사용자 폴더(보고 시각표 daily-brief-schedule.json 이 있는 곳)")
    ap.add_argument("--hand", required=True, help="회사 메일 손 mail.py — 곁의 mailer.py 로 보낸다")
    args = ap.parse_args(argv)
    try:
        address = address_of(pathlib.Path(args.dir))
    except st.Unreadable as exc:
        print(f"못 보냈다 — {exc}")
        return C.SEND_EXIT_BEFORE
    if not address:
        print("못 보냈다 — 자리 밖에서 보기가 꺼져 있거나 본인 주소가 없다")
        return C.SEND_EXIT_BEFORE
    try:
        sheet = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        subject, html, text = (str(sheet[k]) for k in ("subject", "html", "text"))
    except (ValueError, KeyError, TypeError):
        print("못 보냈다 — 받은 메일 한 장의 꼴이 틀렸다")
        return C.SEND_EXIT_BEFORE
    sys.path.insert(0, str(pathlib.Path(args.hand).resolve().parent))   # 회사 메일 손의 폴더 — mailer.py 가 그 곁에 산다
    try:
        import mailer
    except ImportError:
        print("못 보냈다 — 회사 메일 손 곁에 mailer.py 가 없다")
        return C.SEND_EXIT_BEFORE
    try:
        mailer.send(subject, to=[address], sender=address, html=html, text=text)
    except Exception as exc:  # noqa: BLE001 — 무엇으로 졌든 넘겼나 안 넘겼나로만 가른다
        if handed(exc, mailer):
            print(f"보냈는지 모른다 — {why(exc, mailer)}(중계가 받았는지 모른다)")
            return C.SEND_EXIT_UNSURE
        print(f"못 보냈다 — {why(exc, mailer)}")
        return C.SEND_EXIT_BEFORE
    print("보냈다")
    return C.SEND_EXIT_SENT


if __name__ == "__main__":
    sys.exit(main())
