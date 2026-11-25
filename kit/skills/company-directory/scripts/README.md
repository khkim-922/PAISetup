# 주소록 손

**회사 PC 의 스크립트 · 스킬이 사내 주소록 · 조직도에서 사람을 찾고, 찾은 사람을 다른 손에 넘길 파일로 쓰는 자리다.**

- **얇은 명령** `directory.py` — 대화 · 스크립트에서 부르는 명령(다른 손은 이 파일을 싣지 않고 명령과 그 답인 사람 파일을 받는다). 출처 ×
  거르기로 사람을 찾고 `--out` 폴더에 사람 파일(`people.json` · `people.txt`)과 칸마다 주소 파일을 쓴다. 주소록 · 조직도를 묻는 손은 형제
  스킬 company-mail 의 `inbox.py`, 세션으로 메일함 열기 · 받아 둔 조직도 · 주소를 사람으로 잇는 자 · 멈춤의 꼴 · 메일 한 통 찾기 · 받는
  사람 명단은 그 스킬이 내준 조각이다 — 싣는 이름의 한 자리는 그 스킬의 `handout.py` 다. 전화는 형제 스킬 company-regulation 의
  `cbsop.py` 가 내준 이름이다(한 자리는 그 스킬의 `handout.py`) — 셋 다 스킬 홈에 나란히 깔려 있어야 선다
- **사람찾기 손** `findpeople.py` — 그룹사 사람찾기 앱에 사내 세션으로 들어가 찾기 · 한 사람의 상세를 읽는다(읽기만). `directory.py` 의
  출처 `--finder` 와 `--detail` 만 이 손을 부른다. 세션 파일은 형제 스킬 ep-login 의 `ep_session` 으로 읽는다

대화에서 쓰는 절차는 스킬 `company-directory` 가 든다. 부르는 꼴 · 내는 것 · 사람 파일의 꼴은 `directory.py` 머리말이, 회사에서 잰 꼴은
`../references/SOURCES.md` 가, 설계의 까닭은 `../references/DESIGN.md` 가 든다 — 여기 옮겨 적지 않는다.

## 돌려 보기

```bash
python -X utf8 -I _check/skills/company-directory/check_directory.py      # 가짜 메일 서버 · 세션 손 대역 위에서 잰다 — node 가 든다
```

검사는 설정 저장소에 있다 — 깔린 스킬 폴더에는 없다. 설정 저장소 루트에서 돌린다. 끝 줄이 「통과 N/N」이면 선 것이다. 실물 주소록과
전화(사규 앱)는 회사 PC 에서 잰다 — 잴 것은 `../references/SOURCES.md` 「회사에서 잴 것」 이 든다.
