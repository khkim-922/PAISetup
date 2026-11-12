# 사규 손

**회사 PC 의 스크립트가 사내 세션으로 사규관리 앱에 들어가, 문서 목록을 받아 두고 · 찾고 · 한 건을 읽는 파일이다.** 읽기만 한다.

- **앱 손** `cbsop.py` — 사내 세션(쿠키)으로 SSO 를 넘어 앱에 들어가고, 앱의 JSON 자리를 부른다. 판단은 없다
- **얇은 명령** `regulation.py` — 대화에서 부르는 명령. 형제 스킬 ep-login 의 `ep_session.py` 로 세션을 받은 뒤 앱 손을 부른다.
  목록을 홈에 받아 두고 거기서 찾으며, 본문 HTML 을 읽을 글자로 바꾼다
- **검사** `check_regulation.py` — 앱 없이 얇은 명령의 답 꼴을 잰다. 판정과 걷는 조건은 그 머리말이 든다

로그인은 이 손이 하지 않는다 — 사내 세션은 메일함과 한 벌이고, 그 세션을 파일로 남기는 손은 스킬 ep-login 이 든다. 들어가는 길 ·
열람 기록을 안 남기는 까닭은 `cbsop.py` 머리말, 부르는 꼴 · 내는 것 · 종료 값 · 받아 둔 목록의 자리는 `regulation.py` 머리말이 든다.
대화에서 쓰는 절차는 스킬 `company-regulation` 이 든다.

## 돌려 보기

```bash
python -X utf8 -I regulation.py find 출장      # 회사 PC — 받아 둔 목록이 없으면 먼저 받는다
python -X utf8 -I regulation.py read <processIdx> --max 2000
python -X utf8 -I check_regulation.py           # 어느 PC 에서나 — 앱 없이 본문 풀기 · 답의 크기 · recent 의 목록 나이를 잰다
```

검사(`check_regulation.py`)의 끝 줄이 「통과 N/N」이면 선 것이다. 앱에 들어가는 길 · 앱의 답 꼴은 검사가 못 잰다 — 회사 PC 의 실물로
확인했다(`references/SOURCES.md`).
