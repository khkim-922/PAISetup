# 주소록 손

**회사 PC 의 스크립트 · 스킬이 사내 주소록 · 조직도에서 사람을 찾고, 찾은 사람을 다른 손에 넘길 파일로 쓰는 자리다.**

- **얇은 명령** `directory.py` — 대화에서 부르는 명령이자, 사람을 다루는 형제 손이 불러 쓰는 모듈. 출처 × 거르기로 사람을 찾고 `--out`
  폴더에 사람 파일(`people.json` · `people.txt`)과 칸마다 주소 파일을 쓴다. 주소록 · 조직도를 묻는 손은 형제 스킬 company-mail 의
  `inbox.py`, 세션으로 메일함을 여는 자리는 그 스킬의 `mail.py`, 전화는 형제 스킬 company-regulation 의 `cbsop.py` 다 — 셋 다 스킬
  홈에 나란히 깔려 있어야 선다

대화에서 쓰는 절차는 스킬 `company-directory` 가 든다. 부르는 꼴 · 내는 것 · 사람 파일의 꼴은 `directory.py` 머리말이, 회사에서 잰 꼴은
`../references/SOURCES.md` 가, 설계의 까닭은 `../references/DESIGN.md` 가 든다 — 여기 옮겨 적지 않는다.

## 돌려 보기

```bash
python -X utf8 -I _check/skills/company-directory/check_directory.py      # 가짜 메일 서버 · 세션 손 대역 위에서 잰다 — node 가 든다
```

검사는 설정 저장소에 있다 — 깔린 스킬 폴더에는 없다. 설정 저장소 루트에서 돌린다. 끝 줄이 「통과 N/N」이면 선 것이다. 실물 주소록과
전화(사규 앱)는 회사 PC 에서 잰다 — 잴 것은 `../references/SOURCES.md` 「회사에서 잴 것」 이 든다.
