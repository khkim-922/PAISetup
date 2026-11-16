# atelier-report 의 손

| 손 | 하는 일 |
|---|---|
| `atelier.py` | 아뜰리에 서버 문을 밟아 짓고(`make`) · 고치기 화면으로 넘기고(`open`) · 최신 판을 받는다(`fetch`). 계약은 머리말 |

영구 검사는 없다 — 깨지는 길(추천을 못 읽음 · 드라이런 · 넘김 표 없음 · 그림 파일 없음 · 그림이 지면에서 빠짐)이 다 종료 값과
「다음:」 줄로 시끄럽고, 지은 HTML 은 보내기 전에 사람이 본다. 돌려 보기는 로컬 아뜰리에 서버를 띄워 `ATELIER_URL` 로 가리킨다.
서버 없이 그림 박기만 볼 때는 atelier 의 파이썬으로 `embed_images` 가 낸 글을 `app.assemble.fold_data_images` ·
`assemble.assemble` 에 댄다 — 그림 수만큼 자리표가 제 줄에 서고 `unfoldable` 이 비면 선 것이다.

## 빌린 것

- 추천 줄 · 서브 줄의 꼴 — atelier `app/static/app.js` 의 `adviceRows` · `adviceSubs` (atelier 7f357211 판). 손으로 따라간다 — 저쪽 곁말이
  이 자리를 가리킨다
- 넘김 표 문(`/api/handoff` · `/api/handoff/take`) — atelier 결정 0307 · `docs/reference/http-api.md` §5
- 원문에 박힌 그림 — atelier `app/assemble.py` 의 `fold_data_images`(박힌 `<img src="data:image/…">` 를 그림 자리표로 접는다) ·
  `_press_fig`(서버가 누른다) · `fig_tag`(지면에 앉은 그림의 표식 `data-atelier-fig`) · `docs/reference/http-api.md` 4 절의 `extra`
  (atelier b408a7da 판). 손으로 따라간다 — 저쪽에는 이 자리를 가리키는 곁말이 없다. 저쪽 꼴이 바뀌어 그림이 안 접히면
  `make` 가 「그림 N 장 가운데 몇 장이 안 섰다」로 말한다
  - 안 가져온 것 — 화면의 첨부 길(`files[]` 의 `figures` · `inspected` · 그림 번호 매기기)은 안 쓴다: 번호를 매기는 자가
    서버 하나로 남는다. 화면이 그림을 판 폭에 맞춰 미리 누르는 걸음(`shrinkFigure`)도 없다 — 서버가 폭 `FIG_SCAN_W` 로 누른 판이
    실려 화면에서 붙인 그림보다 무겁다
  - 화면의 「알아서 만들기」 사슬과 같은 문 · 같은 칸을 쓴다(`extra` 는 화면의 요청 칸) — 그 사슬 가운데 계획 · 설계검토 · 상담 ·
    알아서 고치기는 안 밟는다. 지면 형태는 `--mode auto` 일 때만 화면처럼 추천 줄의 지면 칸을 따르고, 메일 본문용 기본은
    추천이 무엇을 짚든 문서형태다 — 추천은 지면까지 묶어 디자인을 고르므로, 웹으로 짚은 디자인이 문서형태로 지어질 수 있다
    (추천 문에 지면을 정해 건넬 칸이 없다)

## 회사에서 잴 것

- 사내 아뜰리에 서버(`DEFAULT_URL`)가 넘김 표 문을 든 판으로 떠 있나 — 없으면 `open` 이 404 로 거절된다
- `gpt-6.1-sol` 로 추천 → 렌더 → 자체 점검이 걸리는 시간
- 넘겨받은 화면에서 고치기가 그 키로 도나(드라이런 알약이 아닌가)
- 아뜰리에 메일 지면 HTML 이 사내 중계를 거쳐 Notes 에서 제 꼴로 서나 · 첨부가 중계를 지나나
- 사진을 든 원문과 `--extra` 로 지은 판 — 그림이 원문의 그 자리에 서나 · 요청이 지면에 먹나 · 사내 서버가 사진을 누르나
  (받은 HTML 의 크기) · 문서형태 지면의 WebP 그림이 Notes 본문에서 뜨나(세이프모드는 안 쓴다)
