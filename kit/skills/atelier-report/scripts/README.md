# atelier-report 의 손

| 손 | 하는 일 |
|---|---|
| `atelier.py` | 아뜰리에 서버 문을 밟아 짓고(`make`) · 고치기 화면으로 넘기고(`open`) · 최신 판을 받는다(`fetch`). 계약은 머리말 |

영구 검사는 없다 — 깨지는 길(추천을 못 읽음 · 드라이런 · 넘김 표 없음)이 다 종료 값과 「다음:」 줄로 시끄럽고, 지은 HTML 은
보내기 전에 사람이 본다. 돌려 보기는 로컬 아뜰리에 서버를 띄워 `ATELIER_URL` 로 가리킨다.

## 빌린 것

- 추천 줄 · 서브 줄의 꼴 — atelier `app/static/app.js` 의 `adviceRows` · `adviceSubs` (atelier 7f357211 판). 손으로 따라간다 — 저쪽 곁말이
  이 자리를 가리킨다
- 넘김 표 문(`/api/handoff` · `/api/handoff/take`) — atelier 결정 0307 · `docs/reference/http-api.md` §5

## 회사에서 잴 것

- 사내 아뜰리에 서버(`DEFAULT_URL`)가 넘김 표 문을 든 판으로 떠 있나 — 없으면 `open` 이 404 로 거절된다
- `gpt-6.1-sol` 로 추천 → 렌더 → 자체 점검이 걸리는 시간
- 넘겨받은 화면에서 고치기가 그 키로 도나(드라이런 알약이 아닌가)
- 아뜰리에 메일 지면 HTML 이 사내 중계를 거쳐 Notes 에서 제 꼴로 서나 · 첨부가 중계를 지나나
