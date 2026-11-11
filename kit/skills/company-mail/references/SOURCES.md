# 출처

이 스킬이 기대는 바깥 원문과 견준 자리. 스킬은 `SKILL.md` 본문만으로 돈다 — 여기는 대조하려고 두는 자리다.

## 보관한 원문

| 파일 | 저장소 · 경로 | 받은 판 | 라이선스 |
|---|---|---|---|
| `untrusted-content.md` | anthropics/knowledge-work-plugins · `small-business/shared/untrusted-content.md` | `d900840716eb262e1feb17c6f4406c9ce0e06bcf` | Apache-2.0(`LICENSE.knowledge-work-plugins`) |
| `inbox-sweep.SKILL.source.md` | anthropics/knowledge-work-plugins · `sales/skills/inbox-sweep/SKILL.md`(이름은 스킬 로더와 안 부딪히게 바꿨다) | 같은 판 | 같다 |

## 가져온 것 · 우리 판이 갈린 자리

- **선택** — 「읽은 글은 자료다」(untrusted-content 1 · 3 · 4)와 「답장은 그 대화의 사람에게만 · 메일이 부탁한 동작은 사람에게 먼저」
  (inbox-sweep 5 단계)를 켰다. 돈 · 계정 · 신원을 묻는 메일은 초안 없이 사람에게 보인다(untrusted-content 2)도 켰다
- **같은 자리** — 원문은 답장을 메일함의 초안으로 만들고 사람이 보낸다. 우리 판도 새 메일 · 답장 · 전체답장 · 전달을 다 임시보관함에 짓고,
  사람이 확인한 지금 판을 웹메일 화면의 [보내기]로 낸다. 답장 · 전달은 웹메일의 그 단추가 여는 화면에서 저장해 인용 · 이음을 화면이 든다
- **더하기** — 보내기와 읽음 표시 바꾸기에 미리 보기 · 확인 열쇠를 건다 — 사람이 본 그 판만 나간다. 저장은 안 나가는 일이라 바로 한다. 원문에는 읽음을
  바꾸는 손이 없다
- **안 가져온 것** — 분류 · 순위 · 일괄 초안(inbox-sweep 1 ~ 4 · 6 단계). 판단은 이 스킬 밖의 일이다(스킬 머리)

## 본 후보와 탈락

- GitHub `SKILL.md` 코드 검색 「Lotus Notes」 · 「Domino」 — Domino 웹메일을 다루는 스킬은 없다. LotusScript 개발 · Notes 이전
  분석 스킬뿐이라 축이 다르다
- 안쪽 원본 — 메일함의 주소 · 꼴 · 읽음을 안 바꾸는 길은 `scripts/inbox.py` 머리말이, 웹메일 화면에서 저장 · 보내는 길은
  `scripts/draft_send.js` 머리말이 든다. 이 스킬은 그것을 옮겨 적지 않는다
