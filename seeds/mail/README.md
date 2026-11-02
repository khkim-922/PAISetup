# 메일 씨앗

**회사 PC 의 스크립트가 사내 메일을 보내고 받는 파일들과, 그것을 무는 검사다.**

- **보내는 손** `mailer.py` — 환경변수를 하나도 안 줘도 사내망 안에서는 첫 판에 나간다. 사내 중계에서 잰 동작(인증
  없는 25 번 · 끊기는 STARTTLS 에서 평문으로 물러나기)이 기본값과 난간으로 들어 있다
- **받는 손** `inbox.py` — 받은편지함의 목록 · 본문 · 첨부를 받고, **메일의 읽음 표시를 바꾸지 않는다.** 사람이
  웹메일에서 열기 전까지 그 메일은 「안 읽음」으로 남는다. 로그인은 곁의 `mail_login.js` 가 한다

임포트해서 쓰는 묶음이 아니다. 파일을 복사하면 그때부터 그 저장소의 것이다.

## 왜 따로 있나

회사 메일 가이드(씨앗 `vibecoding/docs/guides/futurem-smtp.md`)는 환경변수 이름과 587 · STARTTLS · 인증서 검증을
기본으로 적지만 서버 값을 안 준다. 사내 중계는 인증 없이 25 번에서 받고 STARTTLS 핸드셰이크를 끊어서, 가이드대로
짜면 첫 발송이 진다.

받는 쪽은 가이드가 아예 없다. 사내 메일함은 Lotus Notes(HCL Domino) 웹메일이라 IMAP · POP3 가 닫혀 있고, 앞에
사내 SSO 가 서며, 메일을 여는 주소를 부르면 그 메일이 읽음이 된다. 두 쪽의 사실은 사내 환경 기록
(`posco/ENV-posco.md` 「네트워크 접근」)이 들고, 이 씨앗은 그것을 코드로 든다.

## 보내기

1. `mailer.py` 를 메일을 보낼 스크립트 곁에 복사한다. 검사도 받으려면 `check_mailer.py` 를 같은 폴더에 둔다.
2. 수신자를 파일로 두려면 `recipients.example.json` 을 제 저장소에 recipients.json 이라는 이름으로 복사해 주소를
   채우고, 그 파일은 `.gitignore` 에 넣는다.
3. 부르는 꼴 · 내는 것 · 환경변수 · 잰 동작은 `mailer.py` 머리말이 든다 — 여기 옮겨 적지 않는다.
4. 아래 「돌려 보기」를 돈다.

## 받기

1. `inbox.py` · `mail_login.js` 를 메일을 읽을 스크립트 곁에 복사한다. 검사도 받으려면 `check_inbox.py` 를 같은
   폴더에 둔다.
2. 웹메일을 브라우저로 열어 주소창에서 `…/이름.nsf` 까지를 환경변수 `MAILBOX_URL` 에 둔다.
3. 로그인해 세션 쿠키를 남긴다 — Node · 전역 playwright · Edge 가 필요하다:

   ```bash
   NODE_PATH="$(npm root -g)" node mail_login.js "$MAILBOX_URL"
   ```

   Edge 창이 뜬다. 넘겨 주지 않는 자리(VDI — ADFS 의 통합 인증이 401 로 진다)는 그 창에서 로그인한다. 사내 SSO 가
   Windows 로그인으로 넘겨 주는 PC(회사 데스크톱)는 사람 손 없이 끝날 것으로 보지만 안 쟀다. 쿠키는 `~/.mailbox-session.json` 에 남는다 — 메일함 열쇠이니 저장소 밖에 두고 넘기지 않는다.
4. 스크립트는 `inbox.Mailbox.from_env()` 로 연다. 부르는 꼴 · 내는 것 · 환경변수 · 잰 동작은 `inbox.py` 머리말이
   든다. 세션이 끊기면 `SessionExpired` 가 나니, 3 을 다시 돌린다.

## 돌려 보기

```bash
python -X utf8 -I check_mailer.py            # 이 폴더의 mailer.py 를 잰다 — 127.0.0.1 밖으로 안 나간다
python -X utf8 -I check_inbox.py             # 이 폴더의 inbox.py 를 잰다 — 127.0.0.1 밖으로 안 나간다
python -X utf8 -I check_mailer.py <폴더>     # 다른 폴더의 사본을 잰다(check_inbox.py 도 같다)
```

끝 줄이 「통과 N/N」이면 선 것이다. 가짜 중계 · 가짜 메일함이라 못 재는 길이 있다 — 보내기는 STARTTLS 가 실제로
서는 길, 받기는 사내 SSO 를 넘는 길(`mail_login.js`)과 실물 메일함의 다른 꼴의 메일. 첫 실발송 · 첫 실수신은 회사
PC 에서 제 주소로 한 통 보내 그 메일로 잰다.

⚠ 작업 스케줄러에서 `python -I` 로 띄우면 스크립트 폴더가 `sys.path` 에 안 서서 `import mailer` · `import inbox` 가
진다 — 스크립트가 부르기 전에 제 폴더를 넣는다(`sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))`).
