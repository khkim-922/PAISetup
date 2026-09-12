# 검사 씨앗

**새 프로젝트의 `_check/` 가 복사해서 출발하는 골든이다** — 판정 한 벌과 종료코드 계약(`_verdict.py`) ·
그 계약을 무는 자 둘 · 지도를 실물에서 파생하는 자 · 브라우저·서버·나무·검체 부품 · 그리고 **받아 간
사본이 낡았나를 재는 자**. 배포되지도 임포트되지도 않는다. 복사한 순간부터 그 프로젝트의 것이다 —
다만 사본은 진본을 가리키고, 진본이 움직이면 다시 받는다.

왜 씨앗인가 — 검사는 형제 저장소에서 읽어 베끼면 판정 손이 따로 자란다. 실측(claude-config #25 ·
2026-09-13): 세 저장소 148장 중 어느 저장소에서나 도는 것이 18장인데 진본이 정리된 것은 둘뿐이었고,
사유 없는 형제 표류가 일곱 짝이었다. 자리와 규율은 결정 `docs/decisions/0040` 이 든다. 게이트웨이
배관과 그 검사는 **다른 씨앗**(`seeds/gateway/`)이다 — 그쪽의 부품 둘은 이쪽의 사본이다.

## 출발하는 법

1. `_check/` 를 새 저장소로 복사한다 — 부품(`_*`)과 검사 넷과 지도(`_check/README.md`)
2. 지도의 갈래표 아래에 제 검사를 적는다 — 「무엇을 재나」 칸은 손으로 안 적는다(`map_check.py --write` 가 머리 첫 줄에서 낸다)
3. 받아 간 파일의 머리말 곁말을 세운다 — 「⚠ **빌려 온 자다** — 진본은 claude-config `seeds/check/_check/<이름>`(<커밋> 판)이고, 고침은 **진본에서 받는다**」. 문단 **끝**에 둔다
4. 검사를 돌린다 — 초록이면 틀이 선 것이다

```bash
python -X utf8 _check/exit_code_check.py       # 검사들이 종료코드 계약을 지키나 — 원문만 읽는다
python -X utf8 _check/verdict_line_check.py    # 초록 줄이 건수를 파생하나 — passes() 를 읽나
python -X utf8 _check/map_check.py             # 지도가 실물과 맞나 — 「무엇을 재나」는 머리 첫 줄에서
python -X utf8 _check/borrowed_check.py        # 받아 간 사본이 진본과 같은가 — 진본은 ~/.claude/seeds/
```

## 무엇이 들고 무엇이 안 드나

| 든다 | 안 든다 — 그 저장소가 얹는다 |
|---|---|
| 판정 세 방언(`report`·`show`·`edge`) · 「못 쟀다」 손(`Unmeasured`) · 계수 | 그 저장소의 계약을 재는 검사 |
| 종료코드 계약(0 쟀고 맞다 · 1 어긋났다 · 2 못 쟀다)과 그것을 무는 자 | CI · 커밋 훅에 무엇을 태우나(지도의 게이트 절이 말하고 `map_check.py --gates` 가 판다) |
| 초록 줄 규율(건수는 `passes()` 가 센다)과 그것을 무는 자 | 한국어 수사로 적은 범위가 맞는 말인가 |
| 브라우저 집기 · 서버 세우기와 두드리기 · 나무 뿌리와 파이썬 묻기 · 결정론 잡음 그림 | 앱의 머리 이름 · 임시 자리 · 판단 층 대역 |
| 받는 자 — 곁말을 읽어 진본과 견준다 | 곁말 없이 베낀 사본(그건 갈림을 세우는 자 `seeds/gateway/_check/drift_check.py` 류의 몫) |

## 진본과 사본

받아 간 파일은 **사본**이다. 곁말 한 줄이 진본을 가리키고, `borrowed_check.py` 가 그 곁말을 읽어
줄끝·BOM·곁말 블록을 뺀 글자가 같은지 문다. 진본이 움직이면 다시 받고 곁말의 커밋을 올린다.
일부러 갈랐으면 곁말을 걷고 그 자리에 사유를 적는다 — 곁말과 갈림이 함께 있으면 어긋남이다.

이 저장소 안에서도 같은 규율이 돈다 — 게이트웨이 씨앗의 `_check/_verdict.py` · `exit_code_check.py`
는 이쪽의 사본이라 `python -X utf8 seeds/check/_check/borrowed_check.py seeds/gateway/_check --seeds seeds` 가 문다.

## 안 옮긴 것 — 자리만 정했다

인자 하나만 빼면 어느 저장소에서나 도는 게이트 아홉이 아직 아뜰리에에 산다(`part_map_check` ·
`env_names_check` · `doc_span_check` · `boundary_edge_check` · `script_syntax_check` · `shot_clip_check` ·
`log_race_check` · `child_decode_check` ⑤ · `_bake.mjs`). 옮기는 손마다 짝을 세어야 하므로(스킬
borrow-spec-as-pair) 파일마다 따로 든다 — 진도는 #25 가 든다.
