# 메일 씨앗

**회사 PC 의 스크립트가 사내 메일을 보내는 파일 하나와, 그것을 무는 검사 하나다.** 환경변수를 하나도 안 줘도
사내망 안에서는 첫 판에 나간다 — 사내 중계에서 잰 동작(인증 없는 25 번 · 끊기는 STARTTLS 에서 평문으로 물러나기)이
기본값과 난간으로 들어 있다.

임포트해서 쓰는 묶음이 아니다. 파일을 복사하면 그때부터 그 저장소의 것이다.

## 왜 따로 있나

회사 메일 가이드(씨앗 `vibecoding/docs/guides/futurem-smtp.md`)는 환경변수 이름과 587 · STARTTLS · 인증서 검증을
기본으로 적지만 서버 값을 안 준다. 사내 중계는 인증 없이 25 번에서 받고 STARTTLS 핸드셰이크를 끊어서, 가이드대로
짜면 첫 발송이 진다. 그 사실은 사내 환경 기록(`posco/ENV-posco.md` 「네트워크 접근」)이 들고, 이 씨앗은 그것을
코드로 든다.

## 받는 법

1. `mailer.py` 를 메일을 보낼 스크립트 곁에 복사한다. 검사도 받으려면 `check_mailer.py` 를 같은 폴더에 둔다.
2. 수신자를 파일로 두려면 `recipients.example.json` 을 제 저장소에 recipients.json 이라는 이름으로 복사해 주소를
   채우고, 그 파일은 `.gitignore` 에 넣는다.
3. 부르는 꼴 · 내는 것 · 환경변수 · 잰 동작은 `mailer.py` 머리말이 든다 — 여기 옮겨 적지 않는다.
4. 아래 「돌려 보기」를 돈다.

⚠ 작업 스케줄러에서 `python -I` 로 띄우면 스크립트 폴더가 `sys.path` 에 안 서서 `import mailer` 가 진다 — 스크립트가
부르기 전에 제 폴더를 넣는다(`sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))`).

## 돌려 보기

```bash
python -X utf8 -I check_mailer.py            # 이 폴더의 mailer.py 를 잰다 — 127.0.0.1 밖으로 안 나간다
python -X utf8 -I check_mailer.py <폴더>     # 다른 폴더의 mailer.py 를 잰다
```

끝 줄이 「통과 N/N」이면 선 것이다. 가짜 중계라 STARTTLS 가 실제로 서는 길은 못 잰다 — 첫 실발송은 회사 PC 에서 제
주소 하나로 보낸다.
