"""검사 지도와 푸시 선언이 실물과 맞나 — 줄 ↔ 파일 · 칸 ↔ 머리 첫 줄 · 선언 ↔ 게이트 절과 트리.

층 — 만드는 사람의 흐름(판정 ①–⑤ — 앞 문에서 막는다) · 물림(`--teeth`)은 검사의 검사라 정기 판에서 돈다
걷는 조건 — 지도의 검사 표가 다 선언에서 나면(사람이 적는 표가 없어지면) ①② 를, 「무엇을 재나」 칸이 사라지면 ③ 을,
푸시의 경로 고르기(`[push_when]`)를 걷으면 ④ 를, 통째로 생성하는 표가 없어지면 ⑤ 를 걷는다

좌표 — 씨앗 규율은 claude-config 결정 0040 · 남기고 걷는 기준은 0148(스킬 check-design) · 푸시 판은 0073 · 경로
고르기는 0076 · 도장과 묶음은 0077 · 물림이 정기 판에 사는 까닭과 ④ 는 atelier #444 · #445 · 명부가 선언에 사는 까닭과
⑤ 는 atelier #447 · 「들머리는 스크립트가 읽는 목록의 원본이 되지 않는다」는 룰 doc-discipline
[Single Source · Point or Derive].

    python _check/map_check.py              # 판정 ①–⑤ 와 심은 표본의 물림 — 이 폴더
    python _check/map_check.py <폴더>       # 잴 `_check/` 를 지정 (병렬 작업나무)
    python _check/map_check.py --write      # ③ 의 칸과 ⑤ 의 표를 머리 첫 줄 · 곁 선언에서 다시 쓴다
    python _check/map_check.py --write --check  # 안 쓰고 판정만 — 다시 쓰면 바뀔 자리가 하나라도 있으면 빨강
    python _check/map_check.py --teeth      # 정기 판 — 물림 전부(심은 표본 · 실물 사본 · 러너 모의). 판정 ①–⑤ 는 안 낸다
    python _check/map_check.py --gates      # 게이트 명부를 한 줄에 하나 — 줄끝은 늘 LF
    python _check/map_check.py --decl       # 곁 선언 전부를 JSON 한 덩이로 — 다른 언어의 러너가 이 읽개로 읽는다
    python _check/map_check.py --run-gates  # 그 목록을 차례로 돌리고 모아 판정한다
    python _check/map_check.py --run-gates --push --jobs 4  # 푸시 직전 판 — 곁 선언 `[push_skip]` 을 빼고 넷씩 동시에
    python _check/map_check.py --run-gates --push --changed <파일>  # 고친 경로(한 줄에 하나)로 `[push_when]` 을 가린다
    python _check/map_check.py --run-gates --only <이름> [--only <이름> …]  # 게이트 몇 개만 러너로 — 도장이 남는다

내는 것 — 0 맞다 · 1 어긋났다(줄마다 무엇이 어디서 어긋났나를 댄다) · 2 못 쟀다(지도 · 곁 선언 · 트리 파일 목록을
못 읽었거나, 표 줄 · 표식 · 명부가 없어 판정이 안 선다). `--gates` 는 목록만, `--decl` 은 `{절: {이름: 값}}` 한 덩이만
내고(값은 한 줄로 편다 — 아래 ⑤), `--run-gates` 는 게이트들의 판정을 같은 셋으로 모은다. 정기 작업은
`python -X utf8 _check/map_check.py --teeth` 를 부른다 — 그 빨강은 「물림을 다시 지을 일」이지 지도의 빨강이 아니다.

**게이트 명부는 어디서 읽나.** 경로 고르기를 쓰는 저장소(곁 선언에 `[push_when]` · `[push_always]` 가 있다)는
선언이 명부다 — 그 두 절과 `[needs_arg]` 의 이름을 모은 것이 게이트다. 사람이 읽는 지도는 스크립트가 읽는 목록의
원본이 되지 않으므로, 그 저장소의 지도 게이트 표는 선언에서 생성한다(⑤). 두 절이 다 없는 저장소는 곁 선언이 있어도
지도의 게이트 절을 읽고, 경로 선언을 들이면 명부도 선언으로 옮겨 간다. `--gates` · `--run-gates` · `--push` 의 고르기 ·
④ 가 다 이 한 명부를 본다(`gate_roster`).

**판정 다섯.** 지도는 *어느 검사가 있고 무엇을 재나*를 들고, 곁 선언(`map_check.conf`)은 *무엇을 언제 돌리나*를
든다. 검사를 새로 짓거나 지우거나 이름을 바꿔도 아무 데서도 안 터진다 — 검사는 그대로 돌고 지도와 선언만
조용히 낡는다. 낡은 자리가 「없는 검사를 있다고 말하는」 쪽이면 그 줄을 읽은 사람은 재지도 않은 자리를 봤다고 여긴다.
  ① **표에 없는 검사** — 파일은 사는데 지도에 줄이 없다. 읽는 사람이 그 검사를 모른다
  ② **실물 없는 줄** — 지도에 줄은 있는데 파일이 없다. 읽는 사람이 없는 검사를 믿는다
  ③ **「무엇을 재나」 칸** — 그 줄의 첫 곁칸이 검사 파일의 머리 첫 줄과 같나. 칸이 손사본이 되지 않게 각 검사
     파일의 머리 첫 줄을 진본으로 삼아 거기서 낸다(`--write`)
  ④ **푸시 선언** — 곁 선언이 게이트 명부 · 트리와 맞나. 셋을 문다:
     ㉠ **죽은 글롭** — `[push_when]` 의 글롭이 트리 파일(추적 파일 + 무시 안 된 새 파일) 한 장에도 안 걸린다. 그
        글롭이 지키려던 자리를 고쳐도 게이트가 안 돌고 푸시는 초록으로 보인다
     ㉡ **모르는 이름** — `[needs_arg]` · `[push_skip]` · `[push_when]` · `[push_fresh]` · `[push_always]` · `[serial]` 의
        이름이 게이트 명부에 없다. 오타면 선언한 사람은 가렸다고 믿는데 러너는 그 이름을 모른다. 선언이 명부인
        저장소는 명부의 이름이 이 폴더의 검사 파일인가도 묻는다 — 명부를 짓는 절의 오타는 명부에 그대로 든다
     ㉢ **선언 없는 게이트** — `[needs_arg]` 밖의 게이트마다 `[push_when]` 글롭이나 `[push_always]` 의 「이름 = 까닭」
        이 있어야 한다. 선언이 명부인 저장소에서는 선언이 빠진 게이트가 명부에서도 빠져 아무도 안 돌리므로, 이
        폴더의 검사 파일 가운데 어느 명부(게이트 · ⑤ 의 다른 절)에도, 지도의 사람 표에도 없는 것을 같이 문다 —
        게이트 절에 사람이 적은 줄은 명부가 아니라 안 센다. ㉢ 은 경로 고르기를 쓰는 저장소에서만 선다 —
        `[push_when]` · `[push_always]` 가 하나도 없으면 러너가 지도의 게이트를 다 늘 돌려 빠질 것이 없다(판정 곁에
        그렇다고 말한다)
  ⑤ **생성하는 표** — 표 머리 곁 표식 `<!-- generated(표 · 게이트) … -->` · `<!-- generated(표 · [절]) … -->` 가
     이끄는 표는 통째로 곁 선언에서 난다. 줄은 명부(게이트면 위 게이트 명부, `[절]` 이면 그 절의 열쇠 — 이름 차례),
     둘째 칸은 그 검사 파일의 머리 첫 줄(③ 과 같은 손), 셋째 칸은 선언이다 — 게이트면 `[push_when]` 글롭과 그 이름이
     든 다른 절의 꼬리표, `[절]` 이면 그 값(여러 줄 값은 한 줄로 편다 — `flat`). 파일의 표가 생성 결과와 한 글자라도
     다르면 빨강이다 — 손으로 고친 칸이 조용히 진본 행세를 못 하게. 표식이 가리키는 절이 없거나 게이트 표인데 선언이
     명부가 아니면 그 표는 「못 쟀다」다

**머리 첫 줄의 계약 둘** — ③ 이 문다:
  · 표 한 칸에 드는 길이 안(아래 `LIMIT`) — 넘치면 표가 문단이 되고, 사람이 칸에 맞게 손으로 줄여 앉히면 그 칸이
    손사본이 된다
  · 마침표로 닫힌다 — 「한 문장인가」를 기계가 가르는 유일한 눈금이다. 안 닫히면 다음 줄로 이어지는 문장이라
    칸에 앉는 순간 **반 토막이 참말처럼 선다**

이슈·ADR 좌표는 첫 줄에 두지 않고 둘째 줄 이하(`좌표 — …`)에 둔다 — 표 한 칸에 좌표가 되풀이되면 칸이 안 읽힌다.

첫 줄은 지도(`.md`)에 앉으므로 문서 검사의 그물에도 든다 — 백틱 조각은 `doc_span_check.py` 가 경로·식별자로 읽어
실물을 찾는다. 좌표만 백틱으로 감싸고 낱말(`image/webp` 같은 형식 이름)은 맨글자로 둔다.

**표식은 둘이고 둘 다 구간 표식이 아니다.** 칸 단위 표식(`MARK`)의 표는 한 줄 안에서 둘째 칸만 기계 것이고
「언제 돌리나」·「무엇이 있어야 도나」는 사람 것이다 — 구간을 치면 손대지 말라는 말이 사람 칸까지 덮는다. 표 단위
표식(⑤)의 표는 사람 칸이 없어 표 전체가 생성물이다. 어느 쪽이든 표식은 표 머리 곁 한 줄로 서고 닫는 짝이 없다 —
표의 끝은 표가 스스로 말하고, 어느 칸인지는 그 표의 머리줄이 말한다.

**물림은 둘로 갈린다** — 막는 문에는 싼 물림만 서고, 무거운 물림은 검사의 검사라 정기 판으로 뺀다(스킬
check-design 「층 — 결함이 누구에게 닿나」).
  · 심은 표본 — 판정마다 일부러 틀린 작은 나무를 심어 빨강을 보인다. 싸서 판정 판에서 매번 돌고, 빨강이면 판정
    판도 빨강이다 — 탐지기가 아예 안 무는 판을 그 자리에서 잡는다(곁 `README.md` 「이 폴더의 규율」의 양성 대조)
  · 정기 판(`--teeth`) — 실물 사본을 손대 보는 물림(③ 의 두 방향)과 러너 모의(태우기 · 줄끝 · 동시 · 고르기 ·
    도장 · 묶음). 판정 판에서 빼고 정기 작업이 부른다

**태우는 자도 여기 있다.** `--gates` 를 셸 루프에 먹이는 손 루프는 두 함정을 매번 새로 연다 — ⓐ 윈도 파이썬은
표준출력의 `\\n` 을 `\\r\\n` 으로 써서 `read -r` 이 이름 끝에 `\\r` 을 붙이고, ⓑ 파이썬은 파일을 못 열면 2 로
나간다 — 종료코드 계약의 「못 쟀다」와 같은 숫자라 「이름이 틀렸다 · 파일이 없다」가 「러너가 못 갖춘 자리」 경고로
둔갑한다. 그러면 게이트가 한 개도 안 돌았는데 빨강이 안 선다(claude-config #103). 그래서 목록은 플랫폼과 무관하게
LF 로 내고, 태우기는 목록을 읽은 자가 파일이 있나를 먼저 묻고 없으면 어긋남(1)으로 센다.
바닥 수(「목록이 줄었나」)와 인자를 받는 게이트는 여기서 안 든다 — 그 저장소 CI 의 몫이다.

**푸시 직전 판(`--push`)은 저장소가 뺀 게이트를 뺀다.** 한 바퀴를 통째로 돌면 분 단위라 푸시마다 물 수 없다 —
무엇을 뺄지는 저장소가 곁 선언 `[push_skip]` 에 `이름 = 까닭` 으로 적는다(`[needs_arg]` 와 같은 꼴). 여기 적지 않은
게이트는 푸시에서도 돈다 — 새 게이트가 조용히 빠지지 않게 빼는 쪽을 선언한다. CI 는 `--gates` 로 목록 전부를 받으므로
여기서 뺀 게이트도 거기서는 돈다.
**푸시 판은 고친 경로로도 가린다(`--changed`).** 게이트마다 지키는 경로를 곁 선언 `[push_when]` 에
`이름 = 글롭 글롭 …` 으로 적으면, 고친 경로가 그 글롭에 하나도 안 걸린 게이트는 푸시에서 안 돈다. 저장소 전체를
보는 게이트처럼 늘 돌아야 하는 게이트는 `[push_always]` 에 `이름 = 까닭` 으로 적는다 — 경로 고르기에게는 선언이
없는 것과 같고(늘 돈다), ④ ㉢ 에게는 「일부러 늘 돈다」는 선언이다. 러너는 이름을 댄 절만 읽으므로, 이 절을 모르는
러너 사본도 그 절을 안 읽고 지나간다.
글롭은 저장소 뿌리 기준 `/` 경로에 `fnmatch` 로 대고, `*` 는 `/` 도 넘는다 — 넘치게 걸리는 쪽이 모자라게 걸리는
쪽보다 싸다(더 도는 것은 시간이고, 덜 도는 것은 빨강을 CI 로 미룬다).
선언 없는 게이트는 경로로 안 빠진다 — 모르면 돈다. 빼는 쪽을 선언하게 한 `[push_skip]` 과 같은 까닭이다(같은
입력으로 이미 초록을 봤으면 아래 도장이 따로 뺀다).
⚠ **`[push_skip]` 이 이긴다** — 거기 적은 게이트는 경로가 걸려도 푸시에서 안 돈다.
경로를 못 받으면 가리지 않는다 — 목록이 없거나 비었거나 못 읽으면 푸시 판 전부를 돌고 까닭을 말한다.
안 돌린 게이트는 판정 곁 「안 돌렸다」 줄에 이름으로 선다 — 초록은 돈 데까지다.
**`--jobs N` 은 게이트를 N 개씩 동시에 돌린다** — 출력은 게이트마다 받아 두었다가 목록 순서대로 낸다.
게이트끼리 같은 자리를 쓰면(포트 · 고정 임시 파일) 서로를 깬다 — 켜기 전에 차례 판과 같은 판정이 나오는지
재고 켠다. 같이 돌면 안 되는 게이트는 곁 선언 `[serial]` 에 `묶음 = 이름 이름 …` 으로 적는다 — 묶음 안은
동시 판에서도 목록 순서대로 하나씩 돌고(한 게이트가 두 묶음에 들면 두 묶음이 한 줄로 이어진다), 나머지는
그 곁에서 동시에 돈다. 프로세스 사이 공유 자원(클립보드 · 포트 · 골든)을 러너가 스스로는 모른다.
⚠ **묶음은 러너 한 판 안에서만 선다** — 두 레인이 따로 러너를 부르면 서로를 모른다.

**러너는 돈 게이트마다 판정 도장을 남긴다.** 「이름 · 입력 지문 · 판정 · 시각」을 저장소 git 공용 폴더 아래
(`<git-common-dir>/map-check-stamps/`)에 적고 — 작업 나무(레인)끼리 같은 자리를 본다 — 푸시 판은 지문이
같은 초록 도장이 있는 게이트를 안 돌리고 「앞서 쟀다(언제 · 지문)」로 이름을 댄다. 입력 지문은 `_check/`
아래 파일 전부(게이트 · 부품 · 곁 선언 · 검체 · 러너 자신) · `[push_when]` 글롭에 걸린 파일들(선언이 없으면
작업 트리의 파일 전부) · 파이썬 판과 깔린 꾸러미의 해시다 — 파일은 저장소 꼭대기 기준의 추적 파일과 무시 안 된
새 파일이고, 한 글자라도 바뀌면 다시 돈다.
⚠ **지문 밖의 입력은 도장이 못 본다** — 선언이 게이트가 읽는 자리를 덜 덮으면(푸시에서 경로로 빠지는 것과 같은
  크기) · 무시된 파일(`.env` · 생성물) · 저장소 밖의 파일. 그런 게이트는 선언을 넓히거나 `[push_fresh]` 에 적는다.
  안전망은 같다 — CI 는 도장을 안 보고 전부 돈다.
돌기 전과 돈 뒤의 지문이 다르면 도장을 안 남긴다 — 도는 사이 입력이 바뀌었으면 그 초록이 어느 입력의 것인지
모른다. 트리에 파일을 쓰는 게이트는 그래서 도장이 안 선다(늘 돈다).
⚠ **환경에 매인 게이트**(시계 · 네트워크 · 브라우저 · git 이력)는 입력 파일이 같아도 판정이 바뀐다 — 곁 선언
  `[push_fresh]` 에 `이름 = 까닭` 으로 적으면 도장을 안 믿고 푸시에서 늘 새로 돈다. 도장은 이 기계의 `.git`
  안에만 살므로 기계는 따로 지문에 안 넣는다.
검사 파일을 직접 부르면 도장이 없다 — 레인 · 세션이 게이트를 돌릴 때는 `--run-gates --only <이름>` 으로 러너를
거친다. git 밖에서 돌면(임시 나무) 도장을 안 남기고 안 읽는다.

**일부러 안 재는 것** — 판정에 새겨 둔다:
  · 밑줄로 시작하는 공용 부품(`_verdict.py`·`_serve.py` 따위)은 검사가 아니라 부품이라 표의 대상이 아니다.
    **양쪽에서 함께 뺀다** — 한쪽만 빼면 그것이 곧 어긋남으로 뜬다
  · 하위 폴더(`fixtures/`·`log/` 따위) 안은 안 본다. 검체와 기록이지 검사가 아니다
  · `_check/` 밖의 검사(`.githooks/` 처럼 검사와 생성기가 섞인 폴더)는 안 문다. 그런 폴더는 파일 목록으로 전수를
    못 뜬다 — 그 검사를 어디에 적고 누가 무나는 받은 저장소의 지도가 든다
  · 사람 표(⑤ 밖)의 「언제 돌리나」 칸 — 사람의 말이라 기계가 안 읽는다. ⑤ 의 표는 그 칸이 곧 선언이라 물을
    것이 없다. 칸을 명부로 읽지 않는 것은 사람 글을 계약으로 만들지 않으려는 것이다(atelier #444 ㉣)
  · 선언한 글롭이 게이트가 실제로 읽는 자리를 다 덮나 · ⑤ 의 다른 절 값이 뜻하는 바(그 절을 읽는 러너가 든다) —
    사람이 든다

③ 이 무는 것은 「같은 글자인가」까지다. 그 문장이 *맞는 말을 하나*는 못 잰다 — 머리 첫 줄이 틀리면 표도 나란히
틀린다. 그래도 **틀릴 자리가 둘에서 하나로 준다.** ⑤ 도 같다 — 선언이 틀리면 표도 틀리고, 사람 표의 「언제
돌리나」·「무엇이 있어야 도나」 칸과 어느 갈래 절에 앉나는 여전히 사람이 실물을 읽고 적은 판단이다.

어긋남 0 은 그 자체로 초록이 아니다 — 표를 못 읽어도 0 이 나온다. 그래서 심은 표본이 판정마다 정말 무는지를 같은
판에서 보이고, 실물과 표 줄 가운데 한쪽이라도 빈손이거나 표식이 한 자리도 없으면 초록이 아니라 「못 쟀다」(2)로
나간다.

토큰도 네트워크도 브라우저도 안 쓴다.
"""
import ast
import concurrent.futures
import configparser
import contextlib
import fnmatch
import functools
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from _verdict import (EXIT_MISMATCH, EXIT_OK, EXIT_UNMEASURED, edge, fails, passes, report,  # noqa: E402
                      unmeasured, unmeasureds)

MAP = "README.md"
SUFFIXES = (".py", ".mjs", ".ps1")
PART = "_"          # 밑줄로 시작하면 공용 부품 — 검사가 아니다
LIMIT = 80          # 머리 첫 줄이 넘으면 안 되는 글자 수 — 표 한 칸에 드는 길이
CELL = 2            # 표 줄에서 파생되는 칸의 자리 — 첫 칸이 이름, 그 다음이 「무엇을 재나」

# 표 머리 곁에 서는 칸 단위 생성 표식. **닫는 짝이 없다** — 까닭은 머리말 「표식은 둘이고 둘 다 구간 표식이 아니다」.
MARK = ("<!-- generated(둘째 칸): python _check/map_check.py --write · 손으로 고치지 않는다 · "
        "어긋남은 같은 스크립트가 기본으로 문다 · 진본은 그 검사 파일의 머리 첫 줄 · "
        "나머지 칸은 사람 것이라 닫는 표식이 없다 -->")

# ⑤ 통째로 생성하는 표의 표식 — 괄호 안이 무엇에서 짓나: 「게이트」는 게이트 명부와 푸시 선언, `[절]` 은 곁 선언의 그 절.
# 표식 줄도 생성물이다(`table_mark`) — 읽을 때는 머리(`TABLE_RE`)만 보고 쓸 때 꼬리까지 다시 앉힌다.
TABLE_GATES = "게이트"
TABLE_RE = re.compile(r"^<!-- generated\(표 · (게이트|\[([A-Za-z0-9_-]+)\])\)")
TABLE_HEAD = ("| 검사 | 무엇을 재나 | 언제 돌리나 |", "|---|---|---|")
# 게이트 표 셋째 칸의 꼬리표 — 글롭 밖의 절이 그 게이트에 무엇을 말하나. 까닭(값)은 곁 선언이 든다.
GATE_TAGS = (("push_always", "늘 돈다"), ("needs_arg", "인자가 든다 — 목록 밖에서 부른다"),
             ("push_skip", "푸시에서 뺀다"), ("push_fresh", "도장을 안 믿는다"))
ORDINAL = ("", "첫째", "둘째", "셋째", "넷째")    # ⑤ 의 어긋남이 칸을 부르는 말 — 표 칸 자리(1부터)


def table_mark(source):
    """⑤ 의 표식 한 줄 — `source` 는 `게이트` 거나 곁 선언의 절 이름."""
    head = TABLE_GATES if source == TABLE_GATES else f"[{source}]"
    return (f"<!-- generated(표 · {head}): python _check/map_check.py --write · 손으로 고치지 않는다 · "
            "어긋남은 같은 스크립트가 기본으로 문다 · 줄과 셋째 칸의 진본은 곁 map_check.conf · "
            "둘째 칸은 그 검사 파일의 머리 첫 줄 -->")


def _is_check(name):
    """검사 파일의 이름꼴인가 — 표 줄과 파일 목록이 **같은 자**로 걸러진다."""
    return (name.endswith(SUFFIXES)
            and not name.startswith(PART)
            and "/" not in name and "\\" not in name)


def scan_files(check_dir):
    """이 폴더에 실제로 사는 검사 파일 — 하위 폴더는 안 본다(검체·기록이다)."""
    return {p.name for p in Path(check_dir).iterdir()
            if p.is_file() and _is_check(p.name)}


def scan_map(text):
    """지도의 표 줄이 든 검사 파일 — **첫 칸만** 본다.

    본문이 곁말로 다른 검사를 가리키는 자리가 많아, 「어디든 이름이 있나」로 재면
    ①(표에 없는 검사)이 통째로 눈이 먼다. 제 줄에 앉은 것만 센다.
    """
    out = set()
    for line in text.splitlines():
        name = _row_head(line)
        if name:
            out.add(name)
    return out


# 갈래표의 **게이트 절** 이름 — 선언이 명부가 아닌 저장소에서 기계가 「무엇을 태우나」를 여기서 판다
# (아뜰리에 결정 0260 · 머리말 「게이트 명부는 어디서 읽나」). 사람 표를 셀 때(`human_rows`)도 이 절은 뺀다.
# ⚠ 목록을 CI 에 손으로 적지 않는다 — 적으면 새 검사가 조용히 빠지고, 빠진 자리는 아무 데서도 안 보인다
#   (atelier #342).
GATE_SECTION = "게이트"

# 인자를 받아야 도는 검사 — 기계가 그냥 부르면 「못 쟀다」(2)를 낸다. 빼되 이름과 까닭을 함께 둔다 —
# 까닭 없이 빼면 눈감은 것이다. **씨앗은 비어 있고 이 파일에는 적지 않는다** — 받은 저장소는 곁
# `map_check.conf` 의 `[needs_arg]` 절에 `이름 = 까닭` 으로 적는다(받은 사본은 진본과 글자가 같아야
# `borrowed_check` 가 초록이다 — 저장소 값은 선언 파일이 든다).
NEEDS_ARG = {}
CONF = "map_check.conf"


def _conf_section(check_dir, section):
    """곁 선언의 한 절 — `이름 = 까닭`. 없으면 빈 사전. 선언은 씨앗이 안 싣는다."""
    conf = Path(check_dir) / CONF
    if not conf.is_file():
        return {}
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str            # 파일 이름은 대소문자가 뜻이다
    cp.read(conf, encoding="utf-8")
    return dict(cp[section]) if cp.has_section(section) else {}


def _push_skip(check_dir):
    """곁 선언의 `[push_skip]` — 푸시 직전 판에서만 빼는 게이트(CI 는 그대로 돈다). 까닭은 값이 든다."""
    return {n: f"푸시에서 뺀다 — {why}" for n, why in _conf_section(check_dir, "push_skip").items()}


def _push_when(check_dir):
    """곁 선언의 `[push_when]` — 게이트 → 그 게이트가 지키는 경로 글롭들(공백으로 가른다)."""
    return {n: v.split() for n, v in _conf_section(check_dir, "push_when").items()}


def _push_fresh(check_dir):
    """곁 선언의 `[push_fresh]` — 환경에 매여 도장을 안 믿는 게이트(푸시에서 늘 새로 돈다). 까닭은 값이 든다."""
    return _conf_section(check_dir, "push_fresh")


def _serial(check_dir):
    """곁 선언의 `[serial]` — 묶음 이름 → 같이 돌면 안 되는 게이트들(공백으로 가른다)."""
    return {n: v.split() for n, v in _conf_section(check_dir, "serial").items()}


# ── ④ 푸시 선언 — 곁 선언이 게이트 명부 · 트리와 맞나

# 열쇠가 게이트 이름인 절. `[serial]` 은 열쇠가 묶음 이름이고 값이 게이트 이름들이라 따로 읽는다.
# `[push_always]` 는 경로 고르기(`push_scope`)가 안 읽는다 — 거기서는 선언이 없는 것과 같아 늘 돈다. 읽는 자리는
# 명부(`decl_is_roster` · `gate_roster`) · ④ ㉢ · ⑤ 의 꼬리표(`GATE_TAGS`)다.
NAMED_SECTIONS = ("needs_arg", "push_skip", "push_when", "push_fresh", "push_always")


def read_decl(check_dir):
    """곁 선언 전부 — `(절 → {열쇠: 값}, 못 읽은 까닭)`. 파일이 없으면 `({}, None)`, 못 읽으면 `(None, 까닭)`."""
    conf = Path(check_dir) / CONF
    if not conf.is_file():
        return {}, None
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str            # 파일 이름은 대소문자가 뜻이다
    try:
        cp.read_string(conf.read_text(encoding="utf-8"), source=str(conf))
    except (OSError, UnicodeDecodeError, configparser.Error) as e:
        return None, f"{CONF} 를 못 읽었다 — {e.__class__.__name__}: {e}"
    return {s: dict(cp[s]) for s in cp.sections()}, None


def flat(value):
    """선언 값 하나를 한 줄로 — 들여 쓴 이음 줄을 빈칸 하나로 잇는다. 표 칸과 `--decl` 이 이 한 손을 쓴다.

    이음 줄은 읽개가 줄마다 다듬어 `\\n` 으로 이어 주므로, 여기서 빈칸으로 바꾸면 이음 자리가 빈칸 하나다 —
    값을 「`·` 뒤에서 끊어」 적으면 편 글이 끊기 전과 같다.
    """
    return " ".join(part.strip() for part in value.splitlines() if part.strip())


def decl_is_roster(decl):
    """선언이 게이트 명부인가 — 경로 고르기를 쓰는 저장소(`[push_when]` · `[push_always]` 가 있다)면 그렇다.

    명부를 어디서 읽나(`gate_roster`) · ④ ㉢ 이 서나(`decl_gaps`) · 게이트 표를 짓나(⑤)가 다 이 한 물음이다.
    """
    return bool(decl.get("push_when") or decl.get("push_always"))


def gate_roster(decl, map_text):
    """게이트 명부 — `(이름들, 어디서 읽었나)`. 머리말 「게이트 명부는 어디서 읽나」.

    선언이 명부면(`decl_is_roster`) `[push_when]` · `[push_always]` · `[needs_arg]` 의 열쇠를 이름 차례로 모은다.
    아니면 지도의 게이트 절이다(`gate_rows`). `decl` 은 `read_decl` 이 읽은 것이고, 못 읽었으면 부르는 쪽이 빈 사전을
    준다 — 명부는 지도 쪽에서 서고, 태우는 판(`--gates` · `--run-gates`)은 그 전에 「못 쟀다」로 나간다.
    선언 쪽 명부가 이름 차례인 것은 절 셋에 흩어진 이름에 차례를 정할 자가 따로 없어서다. 태우는 차례는 판정을
    안 바꾼다 — 게이트끼리 기대지 않고, 같이 돌면 안 되는 것은 `[serial]` 이 묶는다.
    """
    if decl_is_roster(decl):
        return sorted({*decl.get("push_when", {}), *decl.get("push_always", {}), *decl.get("needs_arg", {})}), \
            f"곁 선언 {CONF} 의 `[push_when]` · `[push_always]` · `[needs_arg]`"
    return gate_rows(map_text), f"지도 {MAP} 의 「{GATE_SECTION}」 절"


def decl_gaps(rows, decl, files, checks=None, claimed=()):
    """④ 를 잰다 — `(죽은 글롭, 모르는 이름, 선언 없는 게이트, 경로 고르기를 쓰나)`. 판정은 안 찍는다.

    받는 것 — `rows` 게이트 명부(`gate_roster`) · `decl` 곁 선언(`read_decl`) · `files` 트리 파일(뿌리 기준 `/` 경로 ·
    글롭이 없으면 None 이어도 된다) · `checks` 이 폴더의 검사 파일 이름(None 이면 선언이 명부일 때의 두 물음을 안
    묻는다) · `claimed` 게이트 명부 밖에서 자리를 받은 이름(⑤ 의 다른 절 · 지도의 사람 표). 재기와 판정을 가른 것은
    본판과 심은 표본이 같은 자로 재게 하려는 것이다.
    ⚠ 글롭은 러너와 같은 뜻(`fnmatch` · `*` 는 `/` 도 넘는다 · 대소문자를 가른다)으로 댄다 — 뜻이 갈리면 러너가
      고르는 것과 다른 것을 잰다.
    선언이 명부면(`used`) ㉡ 의 「명부에 없는 이름」은 명부를 짓는 절 셋에서는 늘 비므로 검사 파일인가를 같이
    묻고(`("명부", 이름)`), ㉢ 은 선언 밖에 남은 검사 파일을 같이 센다 — 선언에서 빠진 게이트는 명부에서도 빠져 아무도
    안 돌리기 때문이다.
    """
    gates = set(rows)
    when = {n: v.split() for n, v in decl.get("push_when", {}).items()}
    always = decl.get("push_always", {})
    needs = decl.get("needs_arg", {})
    dead = []
    for name, globs in when.items():
        for g in globs:
            if not any(map(re.compile(fnmatch.translate(g)).match, files or ())):
                dead.append((name, g))
    named = [(s, n) for s in NAMED_SECTIONS for n in decl.get(s, {})]
    named += [("serial", n) for v in decl.get("serial", {}).values() for n in v.split()]
    unknown = sorted({(s, n) for s, n in named if n not in gates})
    used = decl_is_roster(decl)
    undeclared = [n for n in rows if n not in needs and not when.get(n) and not always.get(n, "").strip()] \
        if used else []
    if used and checks is not None:
        unknown += sorted(("명부", n) for n in gates if n not in checks)
        undeclared += sorted(set(checks) - gates - set(claimed))
    return dead, unknown, undeclared, used


def human_rows(map_text):
    """지도의 사람 표에 앉은 검사 이름 — ⑤ 의 표 밖이고 게이트 절 밖인 표 줄의 첫 칸.

    게이트 절을 빼는 까닭 — 선언이 명부인 저장소에서 그 절에 사람이 적은 줄은 명부가 아니라(러너가 안 읽는다)
    「자리를 받았다」로 세면 선언이 빠진 게이트가 ㉢ 을 빠져나간다.
    """
    lines = map_text.split("\n")
    inside = {k for start, end, _src in table_spans(lines) for k in range(start, end)}
    out, here = set(), None
    for k, line in enumerate(lines):
        if line.startswith("## "):
            here = line[3:].split("—")[0].strip()
        name = _row_head(line)
        if name and k not in inside and here != GATE_SECTION:
            out.add(name)
    return out


def judge_decl(check_dir, map_text, decl, rows):
    """④ 를 이 저장소의 곁 선언 · 게이트 명부 · 트리로 판정한다 — 못 읽은 자리는 `unmeasured` 로 남긴다.

    `decl` 은 `read_decl` 이 읽은 것(못 읽었으면 None) · `rows` 는 `gate_roster` 의 명부다.
    """
    print("\n--- ④ 푸시 선언이 실물과 맞나 — 죽은 글롭 · 모르는 이름 · 선언 없는 게이트")
    if decl is None:
        unmeasured("④ 푸시 선언", read_decl(check_dir)[1])
        return
    if not decl:
        edge(f"④ 는 잴 선언이 없다 — 곁 `{CONF}` 가 없거나 비어 러너는 지도의 게이트를 늘 다 돌린다")
        return
    if not rows:
        unmeasured("④ 푸시 선언", f"지도에 「{GATE_SECTION}」 절의 표 줄이 없다 — 선언의 이름을 견줄 명부가 없다")
        return
    globs = sum(len(v.split()) for v in decl.get("push_when", {}).values())
    files = None
    if globs:
        top = _git(Path(check_dir).parent, "rev-parse", "--show-toplevel")
        files = tree_files(Path(top.decode("utf-8", "replace").strip())) if top else None
        if files is None:
            unmeasured("④ ㉠ 죽은 글롭", "작업 트리 파일 목록을 못 뽑았다 — git 밖이거나 git 을 못 부른다")
    tables = {src for _s, _e, src in table_spans(map_text.split("\n")) if src != TABLE_GATES}
    claimed = human_rows(map_text) | {n for src in tables for n in decl.get(src, {})}
    checks = scan_files(check_dir)
    dead, unknown, undeclared, used = decl_gaps(rows, decl, files, checks, claimed)
    if files is not None:
        report(f"④ ㉠ 죽은 글롭이 없다 — 글롭 {globs}개마다 트리 파일이 걸린다", not dead,
               [f"{n} — `{g}` 에 걸리는 트리 파일이 없다. 그 글롭으로는 푸시가 그 게이트를 안 고른다 — 옮긴 · 지운 "
                "자리를 따라 글롭을 고친다" for n, g in dead])
    if any(decl.get(s) for s in (*NAMED_SECTIONS, "serial")):
        report("④ ㉡ 모르는 이름이 없다 — 선언의 이름이 다 게이트 명부에 있다"
               + (" · 명부의 이름이 다 이 폴더의 검사 파일이다" if used else ""), not unknown,
               [f"{n} — 이 폴더에 그 검사 파일이 없다. 명부를 짓는 절(`[push_when]` · `[push_always]` · `[needs_arg]`)의 "
                "오타면 고치고, 걷은 게이트면 그 줄을 걷는다" if s == "명부" else
                f"[{s}] {n} — 게이트 명부에 없는 이름이다. 오타면 고치고, 걷은 게이트면 그 줄을 걷는다"
                for s, n in unknown])
    if used:
        report(f"④ ㉢ 선언 없는 게이트가 없다 — `[needs_arg]` 밖의 게이트마다 `[push_when]` 이나 "
               f"`[push_always]` 가 있고, 이 폴더의 검사 파일이 다 어느 명부나 사람 표에 앉는다 "
               f"(게이트 {len(rows)}개 · 검사 파일 {len(checks)}개)", not undeclared,
               [f"{n} — 게이트면 `[push_when] {n} = <지키는 경로 글롭>` 이나 `[push_always] {n} = <까닭>` 을 적고 "
                "`--write` 로 표를 다시 쓴다 · 게이트가 아니면 지도의 제 절(⑤ 의 절이나 사람 표)에 앉힌다"
                for n in undeclared])
    else:
        edge("④ ㉢ 은 안 섰다 — `[push_when]` · `[push_always]` 가 하나도 없어 경로 고르기를 안 쓴다(러너는 지도의 "
             "게이트를 늘 다 돌린다)")
    edge(f"쟀다: 게이트 {len(rows)}개 · 경로 선언 {len(decl.get('push_when', {}))}개(글롭 {globs}개) · "
         f"늘 돈다 선언 {len(decl.get('push_always', {}))}개 · 인자가 드는 게이트 {len(decl.get('needs_arg', {}))}개 · "
         f"트리 파일 {len(files) if files is not None else '안 뽑음'}"
         + (f" · 명부 밖에서 자리를 받은 검사 {len(claimed)}개(⑤ 의 다른 절 {len(tables)}개 · 사람 표)" if used else ""))
    edge("안 잰 것 — 글롭이 게이트가 실제로 읽는 자리를 다 덮나. 사람이 든다")


def serial_chains(groups, names):
    """동시 판에서 차례로 돌 사슬들 — 각 사슬은 `names` 순서대로 선다.

    한 게이트가 두 묶음에 들면 두 묶음이 한 사슬로 이어진다 — 따로 두면 그 게이트를 사이에 두고 두 묶음의 다른
    게이트가 동시에 돌 수 있다. `names` 에 한 개만 남은 묶음은 사슬이 아니다(같이 돌 짝이 없다).
    """
    chains = []
    for members in groups.values():
        got = set(members) & set(names)
        for c in [c for c in chains if c & got]:
            chains.remove(c)
            got |= c
        if got:
            chains.append(got)
    return [[n for n in names if n in c] for c in chains if len(c) > 1]


# ── 판정 도장 — 같은 입력으로 이미 초록을 본 게이트를 푸시가 다시 안 돌린다

STAMP_DIR = "map-check-stamps"  # git 공용 폴더 아래 도장 자리 — 작업 나무(레인)끼리 같은 자리를 본다
STAMP_KEEP = 8                  # 게이트마다 남길 지문 수 — 레인 여럿이 서로의 도장을 밀어내지 않을 만큼
STAMP_SCHEME = "2"              # 지문 짜임의 판 — 짜임을 바꾸면 올려서 옛 도장을 한꺼번에 무른다
MISSING = "-"                   # 목록에는 있는데 없는 파일의 해시 자리 — 지워진 것도 입력이다


def _git(root, *args):
    """저장소 뿌리에서 git 한 번 — 표준출력 바이트, 못 부르거나 0 이 아니면 None. 훅이 내보낸 변수는 걷는다."""
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, env=_gate_env(), timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def tree_files(root):
    """작업 트리의 파일 — 추적 파일과 무시 안 된 새 파일(`root` 기준 `/` 경로). git 이 아니면 None.

    ⚠ `root` 는 저장소 꼭대기여야 한다 — 하위 폴더에서 부르면 그 폴더 안만, 그 폴더 기준 경로로 나와
      뿌리 기준인 `[push_when]` 글롭이 한 파일에도 안 걸린다(지문이 입력을 못 보고 틀린 초록을 믿는다).
    """
    out = _git(root, "ls-files", "-z", "-co", "--exclude-standard")
    return None if out is None else sorted({p for p in out.decode("utf-8", "replace").split("\0") if p})


def stamp_home(root):
    """도장 자리 — 저장소 git 공용 폴더 아래. git 이 아니면 None."""
    out = _git(root, "rev-parse", "--git-common-dir")
    if not out or not out.strip():
        return None
    common = Path(out.decode("utf-8", "replace").strip())
    return (common if common.is_absolute() else Path(root) / common) / STAMP_DIR


@functools.lru_cache(maxsize=None)
def _interpreter():
    """게이트가 도는 파이썬의 판과 깔린 꾸러미의 해시 — 작업 나무마다 다른 venv 가 같은 판 글자를 내도 갈린다."""
    try:
        from importlib import metadata
        pkgs = sorted(f"{d.metadata.get('Name') or '?'}=={d.version}" for d in metadata.distributions())
    except Exception:  # noqa: BLE001 — 꾸러미 목록을 못 내면 이 판만의 값을 넣어 도장이 안 맞게 한다
        pkgs = [os.urandom(8).hex()]
    return hashlib.sha256("\n".join([sys.version, *pkgs]).encode("utf-8")).hexdigest()


class StampBook:
    """러너 한 판의 도장 장부 — 지문을 내고(`snap`), 도장을 읽고(`green`) 쓴다(`put`).

    도장은 **지문마다 파일 하나**(`<자리>/<게이트>/<지문>.json`)다 — 게이트마다 한 파일에 모으면 두 판이
    읽고 고쳐 쓰는 사이 한쪽이 다른 쪽의 빨강을 지우고 옛 초록을 되살린다. 파일 하나를 통째로 갈아 끼우면
    합치는 쓰기가 없다.
    `root` 는 저장소 꼭대기(지문의 경로 기준)이고, `lister` 는 작업 트리의 파일 목록을 내는 자리다 — 본판은
    `tree_files`(git), 자기 이빨은 임시 나무를 걷는 손을 끼운다.
    """

    def __init__(self, check_dir, when, home, root=None, lister=tree_files):
        self.check_dir, self.when, self.home, self.lister = Path(check_dir), when, Path(home), lister
        self.root = Path(root) if root else self.check_dir.parent

    @classmethod
    def here(cls, check_dir, when):
        """이 저장소의 장부 — git 밖이거나 `_check/` 가 저장소 밖으로 풀리면 None(도장을 안 남기고 안 읽는다)."""
        top = _git(Path(check_dir).parent, "rev-parse", "--show-toplevel")
        home = stamp_home(Path(check_dir).parent)
        if not top or not home:
            return None
        root = Path(top.decode("utf-8", "replace").strip()).resolve()
        try:
            Path(check_dir).resolve().relative_to(root)
        except ValueError:
            return None
        return cls(check_dir, when, home, root=root)

    def snap(self):
        """지금 작업 트리로 지문을 내는 손 — 게이트 이름 → 지문. 목록을 못 뽑으면 None.

        지문 = 게이트 이름 · 파이썬과 꾸러미 · `_check/` 아래 파일 전부(게이트 · 부품 · 곁 선언 · 검체 · 러너 자신) ·
        `[push_when]` 글롭에 걸린 파일(선언이 없으면 작업 트리 전부)의 글자 해시.
        ⚠ **글자를 못 잰 자리는 이 판만의 값으로 넣는다** — 디렉터리(서브모듈) · 권한 · 이름이 안 풀린 경로를
          고정값으로 두면 그 속이 바뀌어도 지문이 같아 틀린 초록을 믿는다. 이 판만의 값이면 도장이 안 맞아 돈다.
          없는 파일만 고정값(`MISSING`)이다 — 지워진 상태는 그 자체가 잴 수 있는 입력이다.
        """
        paths = self.lister(self.root)
        if paths is None:
            return None
        cache = {}

        def digest(p):
            if p not in cache:
                try:
                    if "�" in p:
                        raise OSError("이름이 utf-8 로 안 풀린다")
                    cache[p] = hashlib.sha256((self.root / p).read_bytes()).hexdigest()
                except FileNotFoundError:
                    cache[p] = MISSING
                except OSError:
                    cache[p] = "못 잼 " + os.urandom(8).hex()
            return cache[p]

        cd = self.check_dir.resolve().relative_to(self.root.resolve()).as_posix()
        own = [p for p in paths if p.startswith(f"{cd}/")]

        def fp(name):
            globs = self.when.get(name)
            reach = [p for p in paths if any(fnmatch.fnmatchcase(p, g) for g in globs)] if globs else paths
            h = hashlib.sha256(f"{STAMP_SCHEME}\n{name}\n{_interpreter()}\n".encode("utf-8"))
            for p in sorted({f"{cd}/{name}", *own, *reach}):
                h.update(f"{p}\0{digest(p)}\n".encode("utf-8"))
            return h.hexdigest()
        return fp

    def green(self, name, fp):
        """그 지문의 마지막 판정이 초록이면 그 도장, 아니면 None — 같은 지문에 뒤에 선 빨강이 앞의 초록을 덮는다."""
        try:
            rec = json.loads((self.home / name / f"{fp}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return rec if isinstance(rec, dict) and rec.get("code") == EXIT_OK else None

    def put(self, name, fp, code, secs):
        """도장 하나를 남긴다 — 게이트마다 최근 `STAMP_KEEP` 개 지문만 둔다. 못 쓰면 False(판정은 안 바꾼다)."""
        box = self.home / name
        tmp = box / f"{fp}.{os.getpid()}.tmp"
        rec = {"code": code, "at": time.strftime("%Y-%m-%d %H:%M:%S"), "secs": round(secs, 1)}
        try:
            box.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, box / f"{fp}.json")     # 반쯤 쓴 도장을 다른 판이 읽지 않게 통째로 갈아 끼운다
        except OSError:
            with contextlib.suppress(OSError):
                tmp.unlink()
            return False
        # 오래된 지문은 치운다 — 치우다 지운 도장은 다시 돌 뿐이라 틀린 초록을 못 낸다
        with contextlib.suppress(OSError):
            for q in sorted(box.glob("*.json"), key=lambda q: q.stat().st_mtime)[:-STAMP_KEEP]:
                q.unlink()
        return True

    def trusted(self, names, fresh):
        """지문이 같은 초록 도장이 있는 게이트 → 「앞서 쟀다」 까닭. `fresh`(`[push_fresh]`)는 안 믿는다."""
        fp = self.snap()
        if fp is None:
            return {}
        out = {}
        for name in names:
            if name in fresh:
                continue
            now = fp(name)
            rec = self.green(name, now)
            if rec:
                out[name] = f"초록 · {rec.get('at', '?')} · 지문 {now[:12]}"
        return out


def read_changed(path):
    """고친 경로 목록 — (경로들, 못 받은 까닭). 한 줄에 하나 · `\\` 는 `/` 로 편다 · 빈 줄은 버린다."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return None, f"고친 경로 목록을 못 읽었다({path} · {e.__class__.__name__})"
    out = []
    for line in text.splitlines():
        p = line.strip().replace("\\", "/")
        while p.startswith("./"):
            p = p[2:]
        if p:
            out.append(p)
    return out, (None if out else "고친 경로 목록이 비었다")


def push_scope(rows, when, changed, skip, why=None):
    """고친 경로로 푸시 판을 가린다 — (뺄 게이트 → 까닭, 고른 판 한 줄).

    `rows` 는 게이트 명부(`gate_roster`), `when` 은 `[push_when]`, `changed` 는 고친 경로(None 이면 못 받았다),
    `skip` 은 이미 뺀 것(`[needs_arg]` · `[push_skip]`) — 거기 든 게이트는 경로가 걸려도 되살리지 않는다. `why` 는
    고친 경로를 못 받은 까닭이고 고른 판 줄에 선다.
    ⚠ **선언이 없거나 글롭이 빈 게이트는 늘 돈다** — 빈 값을 「어디에도 안 걸린다」로 읽으면 한 줄의
      실수가 게이트를 조용히 끈다.
    명부에 없는 선언 이름은 고른 판 줄에 선다 — 오타면 그 게이트는 선언 없이 늘 돈다(안전한 쪽이지만 선언한
    사람은 가렸다고 믿는다).
    """
    if not when:
        return {}, "고른 판 — `[push_when]` 선언이 없어 경로로 안 가린다 · 푸시 판 전부"
    stray = sorted(set(when) - set(rows))
    tail = f" · 게이트 명부에 없는 선언 이름 {len(stray)}개: {' '.join(stray)}" if stray else ""
    if not changed:
        return {}, f"고른 판 — {why or '고친 경로를 안 받았다'} · 경로로 안 가리고 푸시 판 전부{tail}"
    out, hit = {}, 0
    for name in rows:
        globs = when.get(name)
        if name in skip or not globs:
            continue
        if any(fnmatch.fnmatchcase(p, g) for p in changed for g in globs):
            hit += 1
        else:
            out[name] = f"고친 경로 밖 — 지키는 자리 {' '.join(globs)}"
    declared = sum(1 for n in rows if when.get(n) and n not in skip)
    return out, (f"고른 판 — 고친 경로 {len(changed)}개 · 경로 선언 {declared}개 중 걸림 {hit}개 · "
                 f"선언 없는 게이트는 경로로 안 빠진다{tail}")


def gate_rows(text):
    """지도의 **게이트 절**에 앉은 검사 이름 — 절을 따라가며 첫 칸만 줍는다. 선언이 명부가 아닌 저장소의 명부다.

    어느 절에 앉나는 이 검사가 안 무는 자리라(사람이 적는다 — 판정 곁의 「안 잰 것」이 그렇게 말한다), 여기서
    읽는 것은 사람이 적어 둔 갈래다.
    ⚠ 빈손이면 부르는 쪽(`print_gates` · `run_gates` · `judge_decl`)이 판정이 아니라 「못 쟀다」로 나간다 — 절
      이름이 갈리면 목록이 조용히 0 이 되는데 **빈 목록은 CI 에서 초록으로 읽힌다.**
    """
    out, here = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            here = line[3:].split("—")[0].strip()
        name = _row_head(line)
        if name and here == GATE_SECTION:
            out.append(name)
    return out


def print_gates(rows, source, needs):
    """태울 목록을 낸다 — 이름은 stdout, **뺀 것과 까닭은 stderr.** `rows` 는 게이트 명부 · `source` 는 그 명부를
    어디서 읽었나(`gate_roster`) · `needs` 는 뺄 것(이름 → 까닭). 내는 것은 종료 값이다 — 0, 명부가 비면 2."""
    if not rows:
        print(f"⚠ 못 쟀다 — 게이트 명부가 비었다({source}). "
              "절 이름이 갈렸으면 목록이 조용히 비고, 빈 목록은 초록으로 읽힌다.",
              file=sys.stderr)
        return EXIT_UNMEASURED
    for name in rows:
        if name in needs:
            print(f"— 뺐다: {name} · {needs[name]}", file=sys.stderr)
            continue
        print(name)
    return EXIT_OK


@functools.lru_cache(maxsize=None)
def _gate_env():
    """게이트에 물릴 환경 — 훅이 내보낸 저장소 변수(`git rev-parse --local-env-vars`)를 걷는다.

    ⚠ 푸시 게이트(`pre-push`) 안에서 돌면 git 이 `GIT_DIR` 따위를 내보낸다. 연결된 작업 트리에서는 그 값이
      절대 경로라, 임시 폴더에 `git init` 하는 게이트가 **진짜 저장소를 다시 초기화한다**(같은 까닭으로
      `borrowed_check` 의 `_git_env()` 도 걷는다). 게이트는 저장소 안(`_check/` 의 부모)에서 돌므로 걷어도 제
      저장소를 스스로 찾는다 — 여기서 걷으면 그 꼴의 게이트가 하나 더 생겨도 이 자리에서 막힌다.
    """
    env = dict(os.environ)
    try:
        out = subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.SubprocessError):
        return env
    for name in out.stdout.split():
        env.pop(name, None)
    return env


def _run_one(check_dir, name):
    """게이트 하나를 CI 처럼 돌린다 — `_check/` 의 부모(보통 저장소 뿌리)에서, 출력은 그대로 흘린다. 표준입력은
    막는다. 내는 것은 그 게이트의 종료코드다."""
    return subprocess.run([sys.executable, "-X", "utf8", str(Path(check_dir) / name)],
                          cwd=str(Path(check_dir).parent), stdin=subprocess.DEVNULL,
                          env=_gate_env()).returncode


def _run_captured(check_dir, name):
    """게이트 하나를 돌리고 출력을 받아 둔다 — 동시 판에서 출력이 섞이지 않게. (종료코드, 글). 자리는 `_run_one` 과 같다."""
    p = subprocess.run([sys.executable, "-X", "utf8", str(Path(check_dir) / name)],
                       cwd=str(Path(check_dir).parent), stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=_gate_env())
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def run_gates(check_dir, rows, needs, run=None, jobs=1, plan=None,
              book=None, known=None, serial=None, only=None):
    """게이트 명부(`rows` — `gate_roster`)의 검사를 돌려 모은다 — (종료코드, 어긋남, 못 쟀다).

    받는 것 — `needs` 안 돌릴 게이트(이름 → 까닭 — 인자가 필요하다 · 푸시에서 뺀다 · 고친 경로 밖) · `jobs` 동시에 돌
    수 · `plan` 푸시 판이 무엇으로 골랐나를 말하는 한 줄(`push_scope`) · `book` 도장 장부(`StampBook`) · `known` 지문이
    같은 초록 도장이 있어 안 돌릴 게이트(이름 → 까닭) · `serial` 은 `[serial]`(묶음 → 이름들 — 동시 판에서 묶음 안을 한
    사슬로 차례로 돌린다, `serial_chains`) · `only` 돌릴 이름들(명부에 없는 이름이 있으면 무엇을 돌렸나가 흐려져 못
    쟀다로 나간다) · `run` 자기 이빨이 프로세스를 안 띄우고 갈래만 재려고 갈아 끼우는 자리(종료코드나 (종료코드, 글)을
    낸다). 종료코드는 어긋남이 있으면 1 · 못 쟀다가 있거나 판정이 하나도 없으면 2 · 아니면 0 이다. 부작용 — 게이트마다
    줄과 모음을 stdout 에(판 전체가 못 쟀다인 까닭은 stderr 에) 찍고, `book` 이 있으면 도장을 남긴다.
    ⚠ **돌리기 전에 파일이 있나를 묻는다.** 없는 이름을 파이썬에 넘기면 2 가 나와
      「못 쟀다」 경고로 섞인다 — 목록에 있는데 파일이 없는 것은 러너 사정이 아니라 어긋남이다.
    하나가 빨개도 나머지를 다 돈다 — 한 판에 무엇이 빨간지 다 보이게. 동시 판(`jobs` > 1)도 판정 줄은 목록
    순서다 — 먼저 끝난 차례로 찍으면 같은 입력에 판마다 다른 글이 나 두 판을 견줄 수 없다.
    안 돌린 게이트는 모음 곁에 이름으로 선다 — `needs` 로 빠진 것을 「안 돌렸다」 한 줄에 모으고, 게이트마다의
    까닭은 목록 자리의 「— 뺐다」 줄이 든다. 앞서 쟀다(`known`)는 판정이라 「안 돌렸다」가 아니라 「앞서 쟀다」 줄에
    서고, 전부가 그것이어도 못 쟀다가 아니다 — 「안 돌렸다」는 판정이 없는 자리다.
    도장은 돌기 전과 돈 뒤의 지문이 같을 때만 남긴다 — 판정이 어느 입력의 것인지 알 때만.
    """
    if run is None:
        run = _run_captured if jobs > 1 else _run_one
    known = known or {}
    rows = list(rows)
    if not rows:
        print("⚠ 못 쟀다 — 게이트 명부가 비었다.", file=sys.stderr)
        return EXIT_UNMEASURED, [], []
    if only:
        stray = sorted(set(only) - set(rows))
        if stray:
            print(f"⚠ 못 쟀다 — `--only` 의 이름이 게이트 명부에 없다: {' '.join(stray)}", file=sys.stderr)
            return EXIT_UNMEASURED, [], []
        rows = [n for n in rows if n in only]
    bad, cant, ran, took, verdicts = [], [], 0, [], {}

    def timed(name):
        t0 = time.monotonic()
        res = run(check_dir, name)
        code, text = res if isinstance(res, tuple) else (res, "")
        return code, text, time.monotonic() - t0

    def batch(names):
        return {n: timed(n) for n in names}     # 사슬 안은 하나씩 — 사전 짓기가 순서대로 돈다

    todo = [n for n in rows if n not in needs and n not in known and (Path(check_dir) / n).is_file()]
    before = book.snap() if book else None
    fp0 = {n: before(n) for n in todo} if before else {}
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=jobs) if jobs > 1 else None
    futures, chains = {}, []
    if pool:
        chains = serial_chains(serial or {}, todo)
        chained = {n for c in chains for n in c}
        tasks = chains + [[n] for n in todo if n not in chained]
        for names in sorted(tasks, key=lambda c: todo.index(c[0])):
            fut = pool.submit(batch, names)
            futures.update({n: fut for n in names})
    for name in rows:
        if name in needs:
            print(f"— 뺐다: {name} · {needs[name]}", flush=True)
            continue
        if name in known:
            print(f"— 앞서 쟀다: {name} · {known[name]}", flush=True)
            continue
        print(f"── {name}", flush=True)
        if not (Path(check_dir) / name).is_file():
            bad.append(name)
            print(f"❌ {name} — 목록에 있는데 파일이 없다 (어긋남)", flush=True)
            continue
        ran += 1
        code, text, secs = futures[name].result()[name] if pool else timed(name)
        if text:
            print(text.rstrip("\n"), flush=True)
        took.append((secs, name))
        verdicts[name] = (code, secs)
        if code == EXIT_UNMEASURED:
            cant.append(name)
            print(f"⚠ {name} — 못 쟀다(2)", flush=True)
        elif code != EXIT_OK:
            bad.append(name)
            print(f"❌ {name} — 어긋났다(종료코드 {code})", flush=True)
    if pool:
        pool.shutdown()
    print(f"\n게이트 {len(rows)}개 · 돌았다 {ran}개 · 어긋남 {len(bad)}개 — {' '.join(bad) or '없음'}")
    print(f"         · 못 쟀다 {len(cant)}개 — {' '.join(cant) or '없음'}")
    skipped = [n for n in rows if n in needs]
    if skipped:
        print(f"         · 안 돌렸다 {len(skipped)}개 — {' '.join(skipped)}")
    seen = [n for n in rows if n in known and n not in needs]
    if seen:
        print(f"         · 앞서 쟀다 {len(seen)}개 — {' '.join(seen)} (같은 입력의 초록 도장 · 까닭은 목록 자리)")
    if plan:
        print(f"         · {plan}")
    if chains:
        print(f"         · 차례로 돈 묶음 — {' · '.join(' → '.join(c) for c in chains)}")
    if before and verdicts:
        after = book.snap()
        if after is None:
            print(f"         · 도장 — 돈 뒤 지문을 못 내(파일 목록) 안 남겼다 {len(verdicts)}개")
        else:
            moved = [n for n in verdicts if after(n) != fp0[n]]
            lost = [n for n in verdicts if n not in moved and not book.put(n, fp0[n], *verdicts[n])]
            print(f"         · 도장 — 남겼다 {len(verdicts) - len(moved) - len(lost)}개"
                  + (f" · 도는 사이 입력이 바뀌어 안 남겼다 {len(moved)}개: {' '.join(moved)}" if moved else "")
                  + (f" · 못 썼다 {len(lost)}개: {' '.join(lost)}" if lost else ""))
    # 한 바퀴가 분 단위라 **어디서 시간이 드나**를 같이 낸다 — 켤지 말지를 가르는 값이 이것이다.
    if took:
        slow = " · ".join(f"{n} {s:.0f}초" for s, n in sorted(took, reverse=True)[:3])
        print(f"         · 모두 {sum(s for s, _ in took):.0f}초 — 오래 걸린 셋: {slow}"
              + (f" · 동시 {jobs}" if jobs > 1 else ""))
    # ⚠ **하나도 안 돌았으면 초록이 아니다** — 목록이 전부 `needs` 로 빠지면 어긋남도 못 쟀다도 0 이라
    #   「통과」로 읽힌다. 빈 목록을 못 쟀다로 내는 `gate_rows` 곁말과 같은 자리다.
    #   앞서 쟀다(`seen`)는 판정이 있으므로 돈 것과 같이 센다.
    if not ran and not bad and not seen:
        print("⚠ 못 쟀다 — 게이트 명부의 이름이 전부 빠져 한 개도 안 돌았다", file=sys.stderr)
    code = EXIT_MISMATCH if bad else EXIT_UNMEASURED if (cant or not (ran or seen)) else EXIT_OK
    return code, bad, cant


def _row_head(line):
    """표 한 줄의 첫 칸이 검사 이름이면 그 이름, 아니면 None."""
    s = line.strip()
    if not s.startswith("|"):
        return None
    cells = s.split("|")
    if len(cells) < 2:
        return None
    name = cells[1].strip().strip("`").strip()
    return name if _is_check(name) else None


def compare(files, rows):
    """(표에 없는 검사, 실물 없는 줄)."""
    return sorted(files - rows), sorted(rows - files)


# ── ③ 「무엇을 재나」 칸 — 진본은 그 검사 파일의 머리 첫 줄이다

def head_line(path):
    """검사 파일의 머리 첫 줄 — 못 읽으면 None.

    갈래마다 머리가 다른 자리에 산다. **꼴이 아니라 그 언어의 관례**로 가른다:
    파이썬은 모듈 독스트링, `.mjs` 는 파일 머리 첫 주석 줄, `.ps1` 은 머리 첫 주석
    줄이되 `.SYNOPSIS` 가 있으면 그것(파워셸이 `Get-Help` 로 내는 자리라 진본이다).
    """
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix == ".py":
        try:
            doc = ast.get_docstring(ast.parse(text), clean=False)
        except SyntaxError:
            return None
        head = (doc or "").splitlines()
    else:
        head = _comment_head(text, path.suffix)
    return head[0].strip() if head and head[0].strip() else None


def _comment_head(text, suffix):
    """머리 주석 덩이를 줄 목록으로 — 주석 표시는 걷고 글자만 남긴다."""
    lines = text.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return []
    first = lines[i].strip()
    if suffix == ".ps1":
        for k, line in enumerate(lines):
            if line.strip().lower().startswith(".synopsis"):
                rest = [x.strip() for x in lines[k + 1:] if x.strip()]
                return rest[:1]
        if first.startswith("<#"):
            return _until(lines, i, "#>", "<#")
        return _run(lines, i, "#")
    if first.startswith("/*"):
        return _until(lines, i, "*/", "/*")
    return _run(lines, i, "//")


def _run(lines, i, mark):
    """한 줄 주석이 잇달아 선 덩이."""
    out = []
    while i < len(lines) and lines[i].strip().startswith(mark):
        out.append(lines[i].strip()[len(mark):].strip())
        i += 1
    return out


def _bare(line):
    """줄머리의 주석 별표만 걷는다.

    ⚠ **굵은 글씨(`**`)는 글자라 안 걷는다.** 뭉뚱그려 `lstrip("*")` 로 걷으면
      `**워드 COM …**` 이 `워드 COM …**` 이 되어 칸이 조용히 반쪽 문법으로 앉는다.
    걷는 것은 줄머리의 별표 하나(바로 뒤에 `*` 가 안 오는 것)와 그 뒤 빈칸이다 — 별표 하나로 여는 기울임
    (`*기울임*`)도 첫 별표를 잃는다.
    """
    s = line.strip()
    return s[1:].strip() if s.startswith("*") and not s.startswith("**") else s


def _until(lines, i, close, open_mark):
    """여닫는 주석 덩이 — 여는 표시와 줄머리 별표를 걷는다."""
    out = [_bare(lines[i].strip()[len(open_mark):])]
    i += 1
    while i < len(lines) and not lines[i].strip().startswith(close):
        out.append(_bare(lines[i]))
        i += 1
    return [x for n, x in enumerate(out) if n or x]     # 여는 줄이 비면 다음 줄이 머리다


def cell_of(first):
    """칸에 앉는 글자 — 첫 줄에서 **맺음 마침표 하나만** 뗀다.

    독스트링 첫 줄은 문장이라 마침표로 닫히는데(PEP 257 · 이 파일의 계약도 같다),
    표 한 칸은 문장이 아니라 조각이라 이 문서의 나머지 칸과 맺음이 갈린다.
    떼는 것이 하나뿐이라 되돌릴 수 있다 — 뜻을 만드는 손질은 여기 없다.
    """
    return first[:-1] if first.endswith(".") else first


def _flaws(first):
    """머리 첫 줄이 계약을 어긴 자리 — 성하면 빈 목록."""
    bad = []
    if len(first) > LIMIT:
        bad.append(f"{len(first)}자 — {LIMIT}자를 넘어 표 한 칸에 안 든다")
    if not first.endswith("."):
        bad.append("마침표로 안 닫힌다 — 다음 줄로 이어지는 문장인지 기계가 못 가른다")
    return bad


def _is_mark(line):
    """칸 단위 표식(`MARK`)이거나 ⑤ 의 표 단위 표식인가 — 둘 다 둘째 칸이 머리 첫 줄에서 난다(③)."""
    s = line.strip()
    return s == MARK or bool(TABLE_RE.match(s))


def row_lines(lines):
    """표식(`_is_mark`)이 이끄는 표의 자료 줄 번호 — 표식이 없으면 빈 목록.

    표식 다음이 머리줄·구분줄이고 그 뒤가 자료다. 구분줄이 없으면 표가 아니므로
    **그 표식은 세지 않는다** — 문서를 고치다 표식만 남은 자리를 조용히 안 넘긴다.
    """
    out, i, n = [], 0, len(lines)
    while i < n:
        if not _is_mark(lines[i]):
            i += 1
            continue
        j = i + 1
        while j < n and not lines[j].strip():
            j += 1
        if j + 1 >= n or "---" not in lines[j + 1] or not lines[j + 1].lstrip().startswith("|"):
            i += 1
            continue
        j += 2
        while j < n and lines[j].lstrip().startswith("|"):
            out.append(j)
            j += 1
        i = j
    return out


def set_cell(line, cell):
    """표 한 줄의 파생 칸만 갈아 앉힌다 — 나머지 칸은 글자 그대로 둔다."""
    cells = line.split("|")
    cells[CELL] = f" {cell} "
    return "|".join(cells)


def read_map(path):
    """지도를 (줄 목록, **그 파일의 줄끝**)으로 — 읽을 때 잰 줄끝을 쓸 때 돌려주려고 짝으로 낸다.

    ⚠ **되쓰는 손은 이 줄끝을 받아 쓴다.** `read_text()` 는 CRLF 를 조용히 `\\n` 으로 눕히고
      되쓰는 손은 `newline=""` 라, 잰 줄끝 없이 되쓰면 칸 하나를 갈아 앉혀도 파일이 통째로 LF 가
      된다 — 줄끝을 `.gitattributes` 로 안 못박은 저장소에서는 그 한 칸이 전 줄 변경으로 보이고,
      칸은 양쪽이 같게 나오므로 화면은 멀쩡하고 diff 만 거짓말을 한다.
    """
    raw = path.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"), eol


def cell_gap(check_dir):
    """(표에 앉은 검사, 어긋난 칸, 머리 첫 줄의 흠) — 판정을 안 찍고 재기만 한다.

    재기와 판정을 가른 것은 본판과 물림(③ 의 심은 표본 `_plant_cells` · 정기 판의 실물 사본 ㉲㉳㉴)이 **같은 자**로
    재게 하려는 것이다.
    """
    lines, _ = read_map(check_dir / MAP)
    seated, gaps, flaw = [], [], []
    for i in row_lines(lines):
        name = _row_head(lines[i])
        if not name:
            continue
        seated.append(name)
        first = head_line(check_dir / name)
        if first is None:
            flaw.append(f"{name} — 머리 첫 줄을 못 읽었다")
            continue
        flaw += [f"{name} — {w}" for w in _flaws(first)]
        got = lines[i].split("|")[CELL].strip()
        want = cell_of(first)
        if got != want:
            gaps.append(f"{name} — 칸 「{got}」 ↔ 머리 「{want}」")
    return seated, gaps, flaw


def write_cells(check_dir):
    """파생 칸을 머리 첫 줄에서 다시 쓴다 — 갈아 앉힌 줄 수를 돌려준다."""
    path = check_dir / MAP
    lines, eol = read_map(path)
    hit = 0
    for i in row_lines(lines):
        name = _row_head(lines[i])
        first = head_line(check_dir / name) if name else None
        if not first:
            continue
        made = set_cell(lines[i], cell_of(first))
        if made != lines[i]:
            lines[i] = made
            hit += 1
    if hit:
        # `newline=""` 는 파이썬이 제 마음대로 `os.linesep` 을 끼우지 말라는 뜻이고, 무엇을
        # 끼울지는 **읽을 때 잰 `eol`** 이 든다 — 둘이 짝이라 하나만 두면 줄끝이 흔들린다.
        path.write_text(eol.join(lines), encoding="utf-8", newline="")
    return hit


# ── ⑤ 생성하는 표 — 진본은 곁 선언(줄 · 셋째 칸)과 그 검사 파일의 머리 첫 줄(둘째 칸)이다

def table_spans(lines):
    """⑤ 의 표마다 `(표식 줄, 표가 끝난 다음 줄, 무엇에서)` — 무엇에서는 `게이트` 거나 절 이름.

    표식 다음의 빈 줄을 건너 `|` 로 시작하는 줄이 이어지는 데까지가 표다. 표가 없으면(표식만 남았으면) 끝이
    표식 바로 다음이라 생성기가 그 자리에 표를 새로 앉힌다.
    """
    out = []
    for i, line in enumerate(lines):
        m = TABLE_RE.match(line.strip())
        if not m:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and lines[j].lstrip().startswith("|"):
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
        else:
            j = i + 1
        out.append((i, j, m.group(2) or TABLE_GATES))
    return out


def gate_when(name, decl):
    """게이트 표의 셋째 칸 — `[push_when]` 글롭(백틱)과, 그 이름이 든 다른 절의 꼬리표(`GATE_TAGS` · `[serial]`)."""
    globs = " · ".join(f"`{g}`" for g in decl.get("push_when", {}).get(name, "").split())
    tags = [say for sect, say in GATE_TAGS if name in decl.get(sect, {})]
    tags += [f"차례 묶음 {group}" for group, members in decl.get("serial", {}).items() if name in members.split()]
    return " — ".join(x for x in (globs, " · ".join(tags)) if x)


def table_lines(check_dir, decl, source, gates):
    """⑤ 한 표가 되어야 할 줄들(표식 · 머리줄 · 구분줄 · 자료 줄) — `(줄들, 못 지은 까닭)`.

    `gates` 는 선언이 명부일 때의 게이트 명부(`gate_roster`), 아니면 None — 게이트 표는 선언이 명부일 때만 선다.
    """
    if source == TABLE_GATES:
        if gates is None:
            return None, "게이트 표인데 선언이 명부가 아니다 — 곁 선언에 `[push_when]` · `[push_always]` 가 없다"
        rows = [(n, gate_when(n, decl)) for n in gates]
    elif source in decl:
        rows = [(n, flat(v)) for n, v in sorted(decl[source].items())]
    else:
        return None, f"표식이 가리키는 절 `[{source}]` 이 곁 선언에 없다"
    out = [table_mark(source), *TABLE_HEAD]
    for name, when in rows:
        first = head_line(Path(check_dir) / name) if _is_check(name) else None
        out.append(f"| `{name}` | {cell_of(first) if first else ''} | {when} |")
    return out, None


def _table_diff(label, have, want):
    """⑤ 한 표의 어긋남을 줄 단위로 — 빠진 줄 · 남는 줄 · 칸이 다른 줄 · 차례 · 머리."""
    out = []
    if have[:3] != want[:3]:
        out.append(f"{label} — 표식 · 머리줄 · 구분줄이 생성과 다르다")
    keyed = [{(_row_head(ln) or ln): ln for ln in side[3:]} for side in (have, want)]
    for name in sorted(keyed[1].keys() - keyed[0].keys()):
        out.append(f"{label} — `{name}` 줄이 없다(선언에는 있다)")
    for name in sorted(keyed[0].keys() - keyed[1].keys()):
        out.append(f"{label} — `{name}` 줄이 남는다(선언에는 없다)")
    for name in sorted(keyed[0].keys() & keyed[1].keys()):
        got, exp = keyed[0][name].split("|"), keyed[1][name].split("|")
        cols = [ORDINAL[k] if k < len(ORDINAL) else f"{k}번째" for k in range(1, max(len(got), len(exp)) - 1)
                if (got[k] if k < len(got) else None) != (exp[k] if k < len(exp) else None)]
        if cols:
            out.append(f"{label} — `{name}` 줄의 {' · '.join(cols)} 칸이 생성과 다르다")
    if not out and have != want:
        out.append(f"{label} — 줄 차례가 생성과 다르다(이름 차례)")
    return out


def table_gap(check_dir, lines, decl, gates):
    """⑤ 를 잰다 — `(지은 표, 어긋남, 못 지은 까닭)`. 판정은 안 찍는다.

    지은 표는 `[(표식 줄, 끝, 줄들)]` 이라 쓰는 손(`write_tables`)이 그대로 받는다. 값이나 머리 첫 줄에 `|` 가 들면
    표 칸이 갈려 그 표는 못 짓는다 — 어긋남으로 센다(선언을 고칠 일이다).
    """
    built, gaps, cant = [], [], []
    for start, end, source in table_spans(lines):
        label = f"{'게이트' if source == TABLE_GATES else f'[{source}]'} 표({start + 1}줄)"
        want, why = table_lines(check_dir, decl, source, gates)
        if want is None:
            cant.append(f"{label} — {why}")
            continue
        split = [ln for ln in want[3:] if ln.count("|") != 4]
        if split:
            gaps += [f"{label} — `{_row_head(ln)}` 의 머리 첫 줄이나 선언 값에 `|` 가 들어 칸이 갈린다" for ln in split]
            continue
        built.append((start, end, want))
        gaps += _table_diff(label, lines[start:end], want)
    return built, gaps, cant


def write_tables(path, built):
    """⑤ 의 표를 지은 것으로 갈아 앉힌다 — 바꾼 표 수를 돌려준다. 줄끝은 읽을 때 잰 것을 지킨다(`read_map`)."""
    lines, eol = read_map(path)
    hit = 0
    for start, end, want in sorted(built, reverse=True):
        if lines[start:end] != want:
            lines[start:end] = want
            hit += 1
    if hit:
        path.write_text(eol.join(lines), encoding="utf-8", newline="")
    return hit


# ── 물림 — 심은 표본(판정 판에서 매번)과 실물 사본 · 러너 모의(`--teeth` 정기 판)

def _plant(files, map_text):
    """검사 이름만 빈 파일로 세운 임시 나무 — 지도는 준 글자 그대로."""
    root = Path(tempfile.mkdtemp(prefix="map-check-"))
    (root / MAP).write_text(map_text, encoding="utf-8")
    for name in files:
        (root / name).write_text("", encoding="utf-8")
    return root


def _drop_row(text):
    """첫 검사 줄 하나를 지운 지도 — (지운 지도, 지운 이름)."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        name = _row_head(line)
        if name:
            return "".join(lines[:i] + lines[i + 1:]), name
    return text, None


def _survey(root):
    return compare(scan_files(root), scan_map((root / MAP).read_text(encoding="utf-8")))


def _copy(check_dir):
    """검사 파일과 지도만 뜬 사본 — 하위 폴더(검체·기록)는 안 뜬다.

    ③ 의 이빨은 **실물 글자**를 읽으므로 빈 파일로 세운 나무(`_plant`)로는 안 물린다.
    """
    root = Path(tempfile.mkdtemp(prefix="map-cell-"))
    shutil.copy2(check_dir / MAP, root / MAP)
    for p in check_dir.iterdir():
        if p.is_file() and _is_check(p.name):
            shutil.copy2(p, root / p.name)
    return root


def _first_seat(root):
    """사본에서 파생 칸이 앉는 첫 줄 — (줄 번호, 검사 이름, 그 머리 첫 줄)."""
    lines, _ = read_map(root / MAP)
    for i in row_lines(lines):
        name = _row_head(lines[i])
        first = head_line(root / name) if name else None
        if first:
            return i, name, first
    return None, None, None


def _bend_head(root):
    """사본의 머리 첫 줄 하나를 손댄다 — 그 검사 이름을 돌려준다."""
    _, name, first = _first_seat(root)
    if not name:
        return None
    p = root / name
    text = p.read_text(encoding="utf-8-sig")
    p.write_text(text.replace(first, "머리를 손댄 " + first, 1), encoding="utf-8", newline="")
    return name


def _bend_cell(root):
    """사본의 지도에서 파생 칸 하나를 손으로 고친다 — 그 검사 이름을 돌려준다."""
    i, name, _ = _first_seat(root)
    if not name:
        return None
    path = root / MAP
    lines, eol = read_map(path)
    lines[i] = set_cell(lines[i], "손으로 고친 칸")
    path.write_text(eol.join(lines), encoding="utf-8", newline="")
    return name


def _plant_cells():
    """③ 의 심은 표본 — 칸이 머리 첫 줄과 같은 검사 하나 · 다른 검사 하나를 든 임시 나무. `(나무, 같은 쪽, 다른 쪽)`."""
    root = Path(tempfile.mkdtemp(prefix="map-cell-"))
    same, bent = "zz_same_check.py", "zz_bent_check.py"
    (root / same).write_text('"""칸과 같은 머리 첫 줄이다."""\n', encoding="utf-8")
    (root / bent).write_text('"""칸과 다른 머리 첫 줄이다."""\n', encoding="utf-8")
    (root / MAP).write_text(f"## {GATE_SECTION} — 심은 표본\n\n{MARK}\n| 검사 | 무엇을 재나 |\n|---|---|\n"
                            f"| `{same}` | 칸과 같은 머리 첫 줄이다 |\n| `{bent}` | 손으로 고친 칸 |\n",
                            encoding="utf-8")
    return root, same, bent


# ④ 의 심은 표본 — 게이트 넷과 트리 파일 둘. 기대는 선언의 뜻에서 온다(아래 `main` 의 ④ 물림이 적는다).
DECL_ROWS = ["a_check.py", "b_check.py", "c_check.py", "d_check.py"]
DECL_FILES = ["docs/a.md", "_check/a_check.py"]
DECL_BAD = ("[needs_arg]\nd_check.py = 인자가 든다\n"
            "[push_when]\na_check.py = docs/*.md\nb_check.py = nowhere/*.txt\n"
            "[push_always]\nzz_typo_check.py = 오타 난 이름\n"
            "[serial]\ng = a_check.py yy_typo_check.py\n")
DECL_GOOD = ("[needs_arg]\nd_check.py = 인자가 든다\n"
             "[push_when]\na_check.py = docs/*.md\nb_check.py = _check/*\n"
             "[push_always]\nc_check.py = 저장소 전체를 본다\n"
             "[serial]\ng = a_check.py b_check.py\n")
DECL_NONE = "[needs_arg]\nd_check.py = 인자가 든다\n"
DECL_BROKEN = "절 머리가 없는 줄\n"


# ⑤ 와 명부의 심은 표본 — 게이트 셋(경로 둘 · 인자 하나)과 화면 절 하나. 기대 표(`TABLE_WANT`)는 선언의 뜻을 사람이
# 읽고 적은 것이다 — 줄은 이름 차례 · 둘째 칸은 머리 첫 줄에서 맺음 마침표만 뗀 것 · 셋째 칸은 게이트면 글롭과
# 꼬리표, 절이면 이음 줄을 빈칸 하나로 편 값. 표식 · 머리줄은 꼴의 상수(`table_mark` · `TABLE_HEAD`)를 그대로 쓴다.
TABLE_DECL = ("[needs_arg]\nb_check.py = 인자가 든다\n"
              "[push_when]\na_check.py = docs/*.md _check/a_check.py\nc_check.py = src/*\n"
              "[push_skip]\na_check.py = 무겁다\n"
              "[scr]\ns_one.mjs = 첫째 · `one`\ns_two.mjs = 둘째 ·\n    `two`\n")
TABLE_FILES = {"a_check.py": '"""에이 게이트다."""\n', "b_check.py": '"""비 게이트다."""\n',
               "c_check.py": '"""시 게이트다."""\n', "s_one.mjs": "// 화면 하나다.\n", "s_two.mjs": "// 화면 둘이다.\n"}
TABLE_WANT = ("## 게이트 — 심은 표본\n\n" + table_mark(TABLE_GATES) + "\n" + "\n".join(TABLE_HEAD) + "\n"
              "| `a_check.py` | 에이 게이트다 | `docs/*.md` · `_check/a_check.py` — 푸시에서 뺀다 |\n"
              "| `b_check.py` | 비 게이트다 | 인자가 든다 — 목록 밖에서 부른다 |\n"
              "| `c_check.py` | 시 게이트다 | `src/*` |\n"
              "\n## 화면 — 심은 표본\n\n" + table_mark("scr") + "\n" + "\n".join(TABLE_HEAD) + "\n"
              "| `s_one.mjs` | 화면 하나다 | 첫째 · `one` |\n"
              "| `s_two.mjs` | 화면 둘이다 | 둘째 · `two` |\n")


def _plant_tables(map_text, decl_text=TABLE_DECL):
    """⑤ 의 심은 나무 — 검사 파일(`TABLE_FILES`) · 곁 선언 · 준 지도. `(나무, 선언, 지도 줄들)`."""
    root = Path(tempfile.mkdtemp(prefix="map-table-"))
    for name, text in TABLE_FILES.items():
        (root / name).write_text(text, encoding="utf-8")
    (root / CONF).write_text(decl_text, encoding="utf-8")
    (root / MAP).write_text(map_text, encoding="utf-8")
    return root, read_decl(root)[0], map_text.split("\n")


def _read_planted_decl(text):
    """곁 선언 글을 임시 폴더에 심고 `read_decl` 로 읽는다 — 읽는 손까지 같은 자로 잰다."""
    root = Path(tempfile.mkdtemp(prefix="map-decl-"))
    try:
        (root / CONF).write_text(text, encoding="utf-8")
        return read_decl(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def judge_tables(check_dir, map_text, decl, gates):
    """판정 ⑤ — 생성하는 표가 곁 선언 · 머리 첫 줄에서 지은 것과 같은가. 못 지은 표는 `unmeasured` 로 남긴다."""
    print("\n--- ⑤ 생성하는 표가 곁 선언에서 나오나 — 줄 ↔ 명부 · 셋째 칸 ↔ 선언")
    lines = map_text.split("\n")
    spans = table_spans(lines)
    if not spans:
        edge("⑤ 는 잴 표가 없다 — 표 단위 표식(`generated(표 · …)`)이 이끄는 표가 지도에 없다")
        return
    if decl is None:
        unmeasured("⑤ 생성하는 표", read_decl(check_dir)[1])
        return
    built, gaps, cant = table_gap(check_dir, lines, decl, gates)
    for row in cant:
        unmeasured("⑤ 생성하는 표", row)
    if built or gaps:
        report(f"⑤ 생성하는 표가 선언과 같다 — 표 {len(built)}개 · 줄 {sum(len(w) - 3 for _s, _e, w in built)}개",
               not gaps, gaps + ["고치는 법: 선언(곁 map_check.conf)이나 머리 첫 줄을 고치고 `--write` 로 다시 쓴다 — "
                                 "표를 손으로 고치지 않는다"])
    edge(f"쟀다: 표 단위 표식 {len(spans)}개 — "
         + " · ".join(TABLE_GATES if src == TABLE_GATES else f"[{src}]" for _s, _e, src in spans))


def judge_map(check_dir, map_text, files, rows, marks, decl, gates):
    """판정 ①–⑤ — 이 저장소의 지도 · 검사 파일 · 곁 선언으로 잰다. 표식이 이끄는 표에 앉은 검사 이름들을 낸다.

    `decl` 은 곁 선언(`read_decl` · 못 읽었으면 None) · `gates` 는 게이트 명부(`gate_roster`)의 이름들이다. 쓰기
    (`--write`)는 부르는 쪽이 먼저 끝내고 다시 읽은 지도를 준다 — 줄을 바꾸는 ⑤ 의 쓰기 뒤라야 ①② 가 제 판을 잰다.
    못 읽은 자리는 `unmeasured` 로 남긴다.
    """
    print("--- ① 실물 대조")
    unlisted, ghost = compare(files, rows)
    report("표에 없는 검사가 없다 — 파일마다 제 줄이 있다", not unlisted,
           [f"{n} — 파일은 사는데 {MAP} 에 줄이 없다" for n in unlisted])
    report("실물 없는 줄이 없다 — 줄마다 그 파일이 산다", not ghost,
           [f"{n} — {MAP} 에 줄은 있는데 파일이 없다" for n in ghost])
    edge(f"쟀다: 실물 {len(files)}개 ↔ 표 줄 {len(rows)}개 (첫 칸 기준)")

    parts = sorted(p.name for p in check_dir.iterdir()
                   if p.is_file() and p.name.startswith(PART) and p.suffix in SUFFIXES)
    edge("일부러 뺐다 — 공용 부품 " + (" · ".join(parts) if parts else "이 나무에는 없다"))
    edge("일부러 뺐다 — 하위 폴더(검체·기록)와 `_check/` 밖의 검사. 까닭은 이 파일 머리말")

    print("\n--- ③ 「무엇을 재나」 칸이 머리 첫 줄에서 나오나")
    seated, gaps, flaw = cell_gap(check_dir)
    report("머리 첫 줄이 계약을 지킨다 — 길이 안에 들고 한 문장으로 닫힌다", not flaw, flaw)
    report(f"칸이 머리 첫 줄과 같다 — 파생 {len(seated)}줄", not gaps, gaps)

    # 표식 밖에 사는 검사 줄은 이 자가 **통째로 못 본다** — 세는 자리를 센티널로 세운다.
    stray = sorted(rows - set(seated))
    report("검사 줄이 전부 표식이 이끄는 표 안에 산다", not stray,
           [f"{n} — 표식 밖의 줄이라 칸이 생성도 대조도 안 된다" for n in stray])
    edge(f"쟀다: 표식 {marks}개 · 파생 칸 {len(seated)}개 (진본은 그 파일의 머리 첫 줄)")
    edge("안 잰 것 — 그 문장이 **맞는 말인가** · 사람 표의 「언제 돌리나」 칸 · 어느 갈래 절에 앉나. 사람이 든다")

    judge_decl(check_dir, map_text, decl, gates)
    judge_tables(check_dir, map_text, decl, gates if decl and decl_is_roster(decl) else None)
    return seated


def main(argv):
    jobs = 1
    if "--jobs" in argv[1:]:
        i = argv.index("--jobs")
        try:
            jobs = max(1, int(argv[i + 1]))
        except (IndexError, ValueError):
            print("⚠ 못 쟀다 — `--jobs` 뒤에 수가 없다", file=sys.stderr)
            return EXIT_UNMEASURED
        argv = argv[:i] + argv[i + 2:]
    changed_path = None             # 푸시 판에서만 읽는다 — CI 판(`--push` 없이)은 경로로 안 가린다
    if "--changed" in argv[1:]:
        i = argv.index("--changed")
        if i + 1 >= len(argv):
            print("⚠ 못 쟀다 — `--changed` 뒤에 파일이 없다", file=sys.stderr)
            return EXIT_UNMEASURED
        changed_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    only = []                       # `--run-gates` 에서만 읽는다 — 레인이 게이트 몇 개를 러너로 돌려 도장을 남기는 입구
    while "--only" in argv[1:]:
        i = argv.index("--only", 1)
        if i + 1 >= len(argv):
            print("⚠ 못 쟀다 — `--only` 뒤에 이름이 없다", file=sys.stderr)
            return EXIT_UNMEASURED
        only.append(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    flags = ("--write", "--check", "--gates", "--decl", "--run-gates", "--push", "--teeth")
    args = [a for a in argv[1:] if a not in flags]
    write = "--write" in argv[1:]
    check = "--check" in argv[1:]   # `--write` 와만 — 안 쓰고 「다시 쓰면 바뀔 자리」를 빨강으로 판정만 낸다
    gates = "--gates" in argv[1:]
    run = "--run-gates" in argv[1:]
    teeth = "--teeth" in argv[1:]   # 정기 판 — 물림 전부를 돌고 판정 ①–⑤ 는 안 낸다(머리말 「물림은 둘로 갈린다」)
    if only and not run:
        print("⚠ 못 쟀다 — `--only` 는 `--run-gates` 와 함께만 뜻이 선다", file=sys.stderr)
        return EXIT_UNMEASURED
    if check and not write:
        print("⚠ 못 쟀다 — `--check` 는 `--write` 와 함께만 뜻이 선다(쓰지 않고 쓸 자리를 판정한다)", file=sys.stderr)
        return EXIT_UNMEASURED
    if teeth and (write or gates or run):
        print("⚠ 못 쟀다 — `--teeth` 는 `--write` · `--gates` · `--run-gates` 없이 부를 때만 뜻이 선다", file=sys.stderr)
        return EXIT_UNMEASURED
    check_dir = Path(args[0]).resolve() if args else HERE
    map_path = check_dir / MAP

    if "--decl" in argv[1:]:        # 곁 선언 한 덩이만 내고 나간다 — 지도가 없어도 선다(읽는 것은 선언뿐이다)
        decl, why = read_decl(check_dir)
        if decl is None:
            print(f"⚠ 못 쟀다 — {why}", file=sys.stderr)
            return EXIT_UNMEASURED
        sys.stdout.reconfigure(newline="\n", encoding="utf-8")
        print(json.dumps({s: {n: flat(v) for n, v in sect.items()} for s, sect in decl.items()}, ensure_ascii=False))
        return EXIT_OK

    if not map_path.is_file():
        print(f"⚠ 지도가 없다 — {map_path}", file=sys.stderr)
        return EXIT_UNMEASURED

    map_text = map_path.read_text(encoding="utf-8")
    decl, decl_why = read_decl(check_dir)
    if (gates or run or teeth) and decl is None:
        # 선언을 못 읽으면 명부가 선언인지 지도인지부터 모른다 — 지도로 흘리면 선언이 명부인 저장소에서 다른 목록이 돈다.
        print(f"⚠ 못 쟀다 — {decl_why}. 게이트 명부를 어디서 읽을지 모른다", file=sys.stderr)
        return EXIT_UNMEASURED
    roster, source = gate_roster(decl or {}, map_text)
    needs = {**NEEDS_ARG, **(decl or {}).get("needs_arg", {})}
    if gates:                      # 태울 목록만 내고 나간다 — 판정은 안 낸다
        # ⚠ **줄끝을 LF 로 못박는다** — 윈도 파이썬의 텍스트 표준출력은 `\n` 을 `\r\n` 으로
        #   쓰고, 루프가 받은 이름 끝에 `\r` 이 붙어 게이트가 하나도 안 돈다(머리말 「태우는 자도 여기 있다」 ⓐ).
        sys.stdout.reconfigure(newline="\n")
        return print_gates(roster, source, needs)
    if run:
        plan, known, when = None, {}, _push_when(check_dir)
        book = StampBook.here(check_dir, when)
        # `--only` 는 「이것을 돌려라」다 — 푸시 판의 거르기(`[push_skip]` · 경로 · 도장)를 안 탄다. 걸렀다가 빠지면
        # 레인이 돌려 달라고 한 게이트가 말없이 안 돌고 도장도 안 선다.
        if "--push" in argv[1:] and not only:
            needs = {**needs, **_push_skip(check_dir)}
            changed, why = read_changed(changed_path) if changed_path else (None, None)
            scoped, plan = push_scope(roster, when, changed, needs, why)
            needs = {**needs, **scoped}
            # 도장은 푸시 판에서만 믿는다 — CI 는 늘 전부 새로 돈다.
            if book:
                known = book.trusted([n for n in roster if n not in needs], _push_fresh(check_dir))
        return run_gates(check_dir, roster, needs, jobs=jobs, plan=plan, book=book, known=known,
                         serial=_serial(check_dir), only=only)[0]

    if write and not check:
        # 쓰기를 판정보다 먼저 끝낸다 — ⑤ 는 줄을 바꾸므로, 쓰기 전의 지도로 ①② 를 재면 낡은 판을 잰다.
        if decl is not None:
            built, _gaps, _cant = table_gap(check_dir, read_map(map_path)[0], decl,
                                            roster if decl_is_roster(decl) else None)
            print(f"⑤ 표를 갈아 앉혔다 — {write_tables(map_path, built)}개")
        print(f"③ 칸을 갈아 앉혔다 — {write_cells(check_dir)}줄\n")
        map_text = map_path.read_text(encoding="utf-8")
        roster, source = gate_roster(decl or {}, map_text)
    files, rows = scan_files(check_dir), scan_map(map_text)
    marks = sum(1 for line in map_text.split("\n") if _is_mark(line))

    # 실물과 표 줄 가운데 한쪽이라도 빈손이면 판정이 안 선다 — 양쪽이 비면 차집합도 비어 **아무것도 안 재고
    # 초록이 난다.** 그 자리를 먼저 막는다.
    if not files or not rows:
        print(f"⚠ 못 쟀다 — 실물 {len(files)}개 · 표 줄 {len(rows)}개. "
              f"한쪽만 비면 다른 쪽이 통째로 어긋남으로 뜨고 둘 다 비면 아무것도 안 잰 초록이라 판정이 안 선다.", file=sys.stderr)
        return EXIT_UNMEASURED

    # 표식이 없으면 ③ 은 **셀 것이 없어 조용히 초록**이 된다. 같은 자리를 막는다.
    if not row_lines(map_text.split("\n")):
        print(f"⚠ 못 쟀다 — 표식이 이끄는 표가 한 자리도 없다 (표식 {marks}개). "
              f"칸을 어디서 낼지 모르므로 ③ 이 안 선다.", file=sys.stderr)
        return EXIT_UNMEASURED

    seated = [] if teeth else judge_map(check_dir, map_text, files, rows, marks, decl, roster)

    if write:
        said = "다시 쓰면 바뀔 자리를 쟀다" if check else "갈아 앉혔다"
        print(f"\n{'❌' if fails() else '⚠' if unmeasureds() else '✅'} {said} — 판정 {len(passes()) + len(fails())}건 "
              f"(어긋남 {len(fails())} · 못 쟀다 {len(unmeasureds())} · 물림은 `--write` 에서 안 돈다)")
        return EXIT_MISMATCH if fails() else EXIT_UNMEASURED if unmeasureds() else EXIT_OK

    print("\n--- 물림 — 심은 표본이 판정마다 정말 빨강을 내나")
    # ⚠ **사본의 파일 목록은 `rows` 로 세운다 — `files` 가 아니다.** 실물에서 뜨면 ① 이
    #   빨간 날 사본도 같이 빨개져, 「손댄 탓」과 「원래 어긋나 있던 탓」이 안 갈린다.
    #   표에서 세우면 ㉮ 가 짜임으로 초록이라, ㉯㉰㉱ 의 빨강은 손댄 것만 가리킨다.
    #   지도 글자는 실물 그대로 쓴다 — 표 읽개가 진짜 표 모양에 물리는지도 같이 재려는 것이다.
    tmps = []
    try:
        # ㉮ 양성 대조 — 안 건드린 사본은 초록이라야 한다. 이게 없으면 아래 빨강이
        #    「손댄 탓」인지 「사본이 애초에 깨진 탓」인지 안 갈린다.
        base = _plant(rows, map_text); tmps.append(base)
        report("㉮ 안 건드린 사본은 초록이다 (양성 대조)", _survey(base) == ([], []))

        # ㉯ 표 줄 하나를 지운다 → 그 검사가 「표에 없는 검사」로 서야 한다
        dropped_text, dropped = _drop_row(map_text)
        cut = _plant(rows, dropped_text); tmps.append(cut)
        report(f"㉯ 표 줄을 하나 지우면 빨강이다 ({dropped})",
               _survey(cut) == ([dropped], []) if dropped else False,
               [f"실측 {_survey(cut)} — 기대 ([{dropped!r}], [])"])

        # ㉰ 가짜 검사 파일을 심는다 → 같은 갈래로 서야 한다
        fake = "zzz_planted_check.py"
        planted = _plant(rows | {fake}, map_text); tmps.append(planted)
        report(f"㉰ 가짜 검사를 심으면 빨강이다 ({fake})",
               _survey(planted) == ([fake], []),
               [f"실측 {_survey(planted)} — 기대 ([{fake!r}], [])"])

        # ㉱ 파일 하나를 지운다 → **다른 갈래**(실물 없는 줄)가 서야 한다.
        #    ㉯㉰ 는 둘 다 같은 갈래를 무므로, 이것이 없으면 둘째 갈래는 이빨이 없다.
        gone = sorted(rows)[0]
        holed = _plant(rows - {gone}, map_text); tmps.append(holed)
        report(f"㉱ 파일을 하나 지우면 다른 갈래로 빨강이다 ({gone})",
               _survey(holed) == ([], [gone]),
               [f"실측 {_survey(holed)} — 기대 ([], [{gone!r}])"])

        # ③ 의 심은 표본 — 칸이 머리 첫 줄과 다른 줄 하나만 서야 한다. ㉮–㉱ 는 **빈 파일**로 세운 나무라 머리 첫
        #   줄이 없어 칸 축이 안 물리고, 실물 사본을 뜨는 ㉲㉳㉴ 는 정기 판이다 — 판정 판에서는 이것이 ③ 을 문다.
        cells, same, bent_name = _plant_cells(); tmps.append(cells)
        c_seated, c_gaps, c_flaw = cell_gap(cells)
        report(f"③ 물림 — 칸을 머리 첫 줄과 다르게 심으면 그 줄만 빨강이다 ({bent_name})",
               c_seated == [same, bent_name] and len(c_gaps) == 1 and c_gaps[0].startswith(f"{bent_name} — ")
               and not c_flaw,
               [f"실측 앉은 줄 {c_seated} · 어긋남 {c_gaps} · 흠 {c_flaw} — 기대 {bent_name} 한 줄만"])

        # ④ 의 심은 표본 — 기대는 선언의 뜻에서 온다: 한 장에도 안 걸리는 글롭(`nowhere/*.txt`)만 죽은 글롭이고(㉠),
        #   게이트 절에 없는 이름은 `[push_always]` 의 열쇠든 `[serial]` 의 값이든 모르는 이름이며(㉡), `[needs_arg]` 의
        #   게이트는 빠지고 선언이 없는 `c_check.py` 만 선언 없는 게이트다(㉢). 다 맞은 선언은 셋 다 비고, 경로 고르기를
        #   안 쓰면 ㉢ 이 안 서며, 못 읽는 선언은 「못 쟀다」로 간다. 선언은 임시 폴더에 심어 읽는 손까지 같은 자로 잰다.
        bad_decl, _ = _read_planted_decl(DECL_BAD)
        dead, unknown, undeclared, used = decl_gaps(DECL_ROWS, bad_decl or {}, DECL_FILES)
        report("④ 물림 ㉠ — 죽은 글롭을 심으면 그 글롭만 빨강이다", dead == [("b_check.py", "nowhere/*.txt")],
               [f"실측 {dead} — 기대 [('b_check.py', 'nowhere/*.txt')]"])
        report("④ 물림 ㉡ — 모르는 이름을 심으면 그 이름만 빨강이다 (`[push_always]` · `[serial]`)",
               unknown == [("push_always", "zz_typo_check.py"), ("serial", "yy_typo_check.py")],
               [f"실측 {unknown} — 기대 [('push_always', 'zz_typo_check.py'), ('serial', 'yy_typo_check.py')]"])
        report("④ 물림 ㉢ — 선언 없는 게이트를 심으면 그 게이트만 빨강이다 (`[needs_arg]` 는 빠진다)",
               used and undeclared == ["c_check.py"], [f"실측 쓰나 {used} · {undeclared} — 기대 ['c_check.py']"])
        good_decl, _ = _read_planted_decl(DECL_GOOD)
        none_decl, _ = _read_planted_decl(DECL_NONE)
        broken, broken_why = _read_planted_decl(DECL_BROKEN)
        g_gaps = decl_gaps(DECL_ROWS, good_decl or {}, DECL_FILES)
        n_gaps = decl_gaps(DECL_ROWS, none_decl or {}, DECL_FILES)
        report("④ 음성 대조 — 다 맞은 선언은 셋 다 비고 · 경로 고르기를 안 쓰면 ㉢ 이 안 서고 · 못 읽는 선언은 못 쟀다다",
               g_gaps == ([], [], [], True) and n_gaps == ([], [], [], False)
               and broken is None and bool(broken_why),
               [f"실측 다 맞음 {g_gaps} · 안 씀 {n_gaps} · 못 읽음 {broken!r} {broken_why!r} — "
                "기대 ([], [], [], True) · ([], [], [], False) · None 과 까닭"])

        # 명부 · ⑤ 의 심은 표본 — 기대는 선언의 뜻에서 온다(`TABLE_WANT` 머리 곁말). 같은 선언에서 게이트 명부는 선언의
        #   열쇠이고(경로 고르기를 안 쓰면 지도의 게이트 절), 사람이 적은 표 그대로면 ⑤ 가 초록 · 칸 하나를 손대면 그 줄의
        #   그 칸만 · 줄을 빼거나 더하면 그 이름만 · 없는 절을 가리키거나 선언이 명부가 아닌데 게이트 표면 못 지은 표다.
        #   쓰는 손은 손댄 지도를 사람이 적은 표로 되돌린다. ㉢ 은 선언이 명부일 때 선언 밖에 남은 검사 파일을 문다.
        troot, tdecl, tlines = _plant_tables(TABLE_WANT); tmps.append(troot)
        t_gates, t_src = gate_roster(tdecl, TABLE_WANT)
        built, t_gaps, t_cant = table_gap(troot, tlines, tdecl, t_gates)
        legacy, l_src = gate_roster({"needs_arg": {"b_check.py": "인자가 든다"}}, TABLE_WANT)
        report("⑤ 물림 — 선언이 명부면 게이트는 선언의 열쇠 · 아니면 지도의 게이트 절 · 사람이 적은 표 그대로면 초록 (양성 대조)",
               t_gates == ["a_check.py", "b_check.py", "c_check.py"] and CONF in t_src and MAP in l_src
               and legacy == ["a_check.py", "b_check.py", "c_check.py"] and len(built) == 2 and not t_gaps
               and not t_cant,
               [f"실측 명부 {t_gates} ({t_src}) · 지도 쪽 {legacy} ({l_src}) · 지은 표 {len(built)} · 어긋남 {t_gaps} · "
                f"못 지음 {t_cant} — 기대 a · b · c 둘 다 · 표 2 · 어긋남과 못 지음 없음"])
        bent_cell = TABLE_WANT.replace("| 둘째 · `two` |", "| 둘째 · `twoo` |")
        dropped = TABLE_WANT.replace("| `s_one.mjs` | 화면 하나다 | 첫째 · `one` |\n", "")
        extra = TABLE_WANT.replace("| `c_check.py` | 시 게이트다 | `src/*` |\n",
                                   "| `c_check.py` | 시 게이트다 | `src/*` |\n| `zz_check.py` | 덧붙인 줄 | 손 |\n")
        nowhere = TABLE_WANT.replace(table_mark("scr"), table_mark("nope"))
        got = {k: table_gap(troot, v.split("\n"), tdecl, t_gates)[1:]
               for k, v in (("bent", bent_cell), ("dropped", dropped), ("extra", extra), ("nowhere", nowhere))}
        no_roster = table_gap(troot, tlines, tdecl, None)[2]
        report("⑤ 물림 — 손댄 칸 · 빠진 줄 · 남는 줄은 그 이름만 빨강 · 없는 절과 명부 아닌 게이트 표는 못 지은 표다",
               len(got["bent"][0]) == 1 and "`s_two.mjs`" in got["bent"][0][0] and "셋째" in got["bent"][0][0]
               and len(got["dropped"][0]) == 1 and "`s_one.mjs` 줄이 없다" in got["dropped"][0][0]
               and len(got["extra"][0]) == 1 and "`zz_check.py` 줄이 남는다" in got["extra"][0][0]
               and not got["nowhere"][0] and len(got["nowhere"][1]) == 1 and "[nope]" in got["nowhere"][1][0]
               and len(no_roster) == 1 and "게이트" in no_roster[0],
               [f"실측 {got} · 명부 없이 {no_roster} — 기대 그 줄 하나씩 · 못 지음 하나씩"])
        # 첫 표(게이트)는 머리줄을, 둘째 표(화면)는 칸 하나를 손댄 지도 — 쓰는 손은 두 표를 다 갈아 앉혀야 한다.
        (troot / MAP).write_text(bent_cell.replace(TABLE_HEAD[0], "| 손 | 머리 | 줄 |", 1), encoding="utf-8")
        wrote = write_tables(troot / MAP, table_gap(troot, read_map(troot / MAP)[0], tdecl, t_gates)[0])
        undeclared = {k: decl_gaps(gate_roster(d, TABLE_WANT)[0], d, None, {*TABLE_FILES, "d_check.py"},
                                   {"s_one.mjs", "s_two.mjs"})[2]
                      for k, d in (("whole", tdecl),
                                   ("cut", {**tdecl, "push_when": {"a_check.py": tdecl["push_when"]["a_check.py"]}}))}
        report("⑤ 물림 — 쓰는 손이 손댄 표를 선언대로 되돌리고 · ㉢ 이 선언 밖의 검사 파일과 선언에서 뺀 게이트를 문다",
               wrote == 2 and (troot / MAP).read_text(encoding="utf-8") == TABLE_WANT
               and undeclared == {"whole": ["d_check.py"], "cut": ["c_check.py", "d_check.py"]},
               [f"실측 바꾼 표 {wrote} · 같아졌나 {(troot / MAP).read_text(encoding='utf-8') == TABLE_WANT} · "
                f"선언 없는 것 {undeclared} — 기대 2 · True · d 만 · c 와 d"])

        if teeth:
            print("\n--- 정기 물림 — 실물 사본과 러너 모의 (`--teeth`)")
            # ㉲㉳㉴ — ③ 의 실물 사본. 위 심은 표본이 탐지기를 매번 보이고, 여기는 실물 지도 · 실물 머리 꼴에서도 두 방향
            #   으로 무는지 본다. 검사 파일 전부를 세 벌 떠 읽어 무거우므로 정기 판에서만 돈다.
            keep = _copy(check_dir); tmps.append(keep)
            report("㉲ 안 건드린 사본은 칸도 초록이다 (양성 대조)", cell_gap(keep)[1:] == ([], []))

            # ㉳ 진본 쪽을 손댄다 → 칸이 어긋나야 한다
            bent = _copy(check_dir); tmps.append(bent)
            hurt = _bend_head(bent)
            report(f"㉳ 머리 첫 줄을 바꾸면 칸이 빨강이다 ({hurt})",
                   bool(hurt) and any(str(hurt) in g for g in cell_gap(bent)[1]),
                   [f"실측 {cell_gap(bent)[1] or '어긋남 없음'} — {hurt} 가 서야 한다"])

            # ㉴ 문서 쪽을 손댄다 → **반대 방향**이다. ㉳ 만 있으면 「사람이 칸을 고친 자리」는
            #    이빨이 없다 — 손사본을 끊자는 것이 이 축의 본론이라 그쪽이 더 값이 크다.
            hand = _copy(check_dir); tmps.append(hand)
            touched = _bend_cell(hand)
            report(f"㉴ 칸을 손으로 고치면 빨강이다 ({touched})",
                   bool(touched) and any(str(touched) in g for g in cell_gap(hand)[1]),
                   [f"실측 {cell_gap(hand)[1] or '어긋남 없음'} — {touched} 가 서야 한다"])

            # ㉵ 태울 목록의 줄끝 — 이 판의 파이썬이 실제로 낸 바이트를 잰다. 리눅스에서는 늘
            #    초록이고, 이빨이 서는 자리는 윈도(머리말 「태우는 자도 여기 있다」 ⓐ)다.
            listed = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()),
                                     str(check_dir), "--gates"], capture_output=True)
            crs = listed.stdout.count(b"\r")
            report("㉵ `--gates` 목록 줄끝에 CR 이 없다 — 셸 루프가 이름을 그대로 받는다",
                   listed.returncode == EXIT_OK and bool(listed.stdout) and not crs,
                   [f"실측 종료코드 {listed.returncode} · {len(listed.stdout)}바이트 · CR {crs}개"])

            # ㉶ 태우는 자의 갈래 — 목록에 있는데 파일이 없는 게이트는 「못 쟀다」가 아니라
            #    어긋남이고, 2 를 낸 게이트는 못 쟀다로 남으며, 전부 빠져 하나도 안 돌면 못 쟀다다.
            #    프로세스는 안 띄운다(`run` 갈아 끼움).
            grows = [n for n in roster if n not in needs]
            if len(grows) >= 2:
                gone_g, cant_g = grows[0], grows[1]
                fake = lambda _d, n: EXIT_UNMEASURED if n == cant_g else EXIT_OK  # noqa: E731
                whole = _plant(rows | set(grows), map_text); tmps.append(whole)
                hole = _plant((rows | set(grows)) - {gone_g}, map_text); tmps.append(hole)
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    got_whole = run_gates(whole, roster, needs, run=lambda _d, _n: EXIT_OK)
                    got_hole = run_gates(hole, roster, needs, run=fake)
                    got_none = run_gates(whole, roster, {n: "시험" for n in roster},
                                         run=lambda _d, _n: EXIT_OK)
                report("㉶ 태우기 — 다 있으면 초록 · 없는 파일은 어긋남 · 2 는 못 쟀다 · 하나도 안 돌면 못 쟀다 "
                       f"({gone_g} · {cant_g})",
                       got_whole == (EXIT_OK, [], []) and got_hole == (EXIT_MISMATCH, [gone_g], [cant_g])
                       and got_none == (EXIT_UNMEASURED, [], []),
                       [f"실측 {got_whole} · {got_hole} · {got_none} — 기대 (0, [], []) · "
                        f"(1, [{gone_g!r}], [{cant_g!r}]) · (2, [], [])"])

                # ㉷ 푸시 판 — 동시 판(`jobs`)이 차례 판과 같은 판정을 내나, `[push_skip]` 에 적은 게이트가 정말
                #    안 도나. 곁 선언은 사본 나무에 심는다 — 진짜 저장소 선언을 안 건드린다.
                (whole / CONF).write_text(f"[push_skip]\n{gone_g} = 시험\n", encoding="utf-8")
                seen = []
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    got_par = run_gates(hole, roster, needs, run=fake, jobs=3)
                    run_gates(whole, roster, {**needs, **_push_skip(whole)},
                              run=lambda _d, n: seen.append(n) or EXIT_OK)
                report(f"㉷ 푸시 판 — 동시 판이 차례 판과 같고 · `[push_skip]` 의 게이트는 안 돈다 ({gone_g})",
                       got_par == got_hole and gone_g not in seen and len(seen) == len(grows) - 1,
                       [f"실측 동시 {got_par} · 차례 {got_hole} · 돈 것 {len(seen)}/{len(grows)} "
                        f"· 뺀 것이 돌았나 {gone_g in seen}"])

                # ㉸ 경로로 가리기 — `[push_when]` 에 적은 게이트는 고친 경로가 글롭에 걸릴 때만 돈다. 기대값은
                #    선언의 뜻에서 온다: 문서 글롭만 지키는 게이트는 코드 경로를 고친 푸시에서 빠지고(ⓐ), `*` 는
                #    `/` 를 넘어 깊은 문서에도 걸리며(ⓑ), 선언 없는 게이트는 늘 돌고(ⓐ 의 둘째), `[push_skip]` 이
                #    이기고(ⓒ), 빈 글롭은 선언 없음과 같고(ⓓ), 경로를 못 받거나 빈 목록이면 안 가린다(ⓔ).
                #    안 돌린 이름은 모음 곁 「안 돌렸다」 줄에 서야 한다(ⓕ) — 조각이 그 줄을 화면에 올린다.
                doc_g, free_g = grows[0], grows[1]
                when = {doc_g: ["docs/*.md"], "zzz_not_a_gate.py": ["src/*"]}
                rows_g = roster
                a_out, a_plan = push_scope(rows_g, when, ["src/app.py"], needs)
                b_out, _ = push_scope(rows_g, when, ["docs/deep/x.md", "src/app.py"], needs)
                c_skip = {**needs, doc_g: "푸시에서 뺀다 — 시험"}
                c_out, _ = push_scope(rows_g, when, ["src/app.py"], c_skip)
                c_why = {**c_skip, **c_out}.get(doc_g, "")
                d_out, _ = push_scope(rows_g, {doc_g: []}, ["src/app.py"], needs)
                e_out, e_plan = push_scope(rows_g, when, None, needs, "시험 — 못 받았다")
                e2_out, _ = push_scope(rows_g, when, [], needs, "고친 경로 목록이 비었다")
                f_buf, seen = io.StringIO(), []
                with contextlib.redirect_stdout(f_buf), contextlib.redirect_stderr(io.StringIO()):
                    run_gates(whole, roster, {**needs, **a_out}, run=lambda _d, n: seen.append(n) or EXIT_OK,
                              plan=a_plan)
                f_lines = f_buf.getvalue().splitlines()
                named = any(ln.startswith("         · 안 돌렸다 ") and doc_g in ln.split(" — ", 1)[-1].split()
                            for ln in f_lines)
                planned = any(ln.startswith("         · 고른 판 — ") and "zzz_not_a_gate.py" in ln for ln in f_lines)
                chg = Path(tempfile.mkdtemp(prefix="map-check-chg-")); tmps.append(chg)
                (chg / "list").write_text(".\\docs\\a.md\n\n./src/b.py\n", encoding="utf-8")
                got_list = read_changed(chg / "list")
                (chg / "empty").write_text("\n", encoding="utf-8")
                empty_list = read_changed(chg / "empty")
                ok = (set(a_out) == {doc_g} and b_out == {} and c_why.startswith("푸시에서 뺀다") and d_out == {}
                      and e_out == {} and e2_out == {} and "시험 — 못 받았다" in e_plan
                      and free_g in seen and doc_g not in seen and named and planned
                      and got_list == (["docs/a.md", "src/b.py"], None)
                      and empty_list[0] == [] and empty_list[1]
                      and read_changed(chg / "nope")[0] is None)
                report(f"㉸ 경로로 가리기 — 걸린 게이트만 · 선언 없으면 늘 · `[push_skip]` 이 이긴다 · 못 받으면 전부 "
                       f"· 안 돌린 이름이 모음에 선다 ({doc_g} · {free_g})",
                       ok,
                       [f"실측 ⓐ {sorted(a_out)} · ⓑ {sorted(b_out)} · ⓒ {c_why!r} · ⓓ {sorted(d_out)} "
                        f"· ⓔ {sorted(e_out)} {sorted(e2_out)} · 돈 것에 {free_g} {free_g in seen} · {doc_g} {doc_g in seen} "
                        f"· 이름 줄 {named} · 고른 판 줄 {planned} · 목록 {got_list} · 빈 목록 {empty_list} — "
                        f"기대 ⓐ [{doc_g!r}] · ⓒ 까닭은 [push_skip] 것 · 나머지 빈 · {free_g} 돌고 {doc_g} 안 돈다 · 두 줄 선다"])

                # ㉹ 판정 도장 — 기대값은 도장의 뜻에서 온다: 돈 게이트는 도장을 남겨 같은 입력이면 믿히고(ⓐ),
                #    `[push_fresh]` 는 안 믿고(ⓑ), 글롭 밖을 고치면 선언한 게이트만 믿히고 선언 없는 게이트(트리 전부)는
                #    안 믿히고(ⓒ), 글롭 안을 고치면 안 믿히고(ⓓ), 같은 입력의 빨강이 앞의 초록을 덮고(ⓔ), 도는 사이
                #    입력이 바뀐 게이트는 도장을 안 남기고 그렇다고 말하고(ⓕ), 게이트 파일을 고치면 안 믿히고(ⓖ),
                #    전부 앞서 쟀으면 한 개도 안 돌고 초록이며 「앞서 쟀다」 줄이 선다(ⓗ). 도장 자리는 트리 밖 임시 폴더다.
                sroot = Path(tempfile.mkdtemp(prefix="map-check-stamp-")); tmps.append(sroot)
                shome = Path(tempfile.mkdtemp(prefix="map-check-home-")); tmps.append(shome)
                sdir = sroot / "_check"
                sdir.mkdir()
                (sdir / MAP).write_text(map_text, encoding="utf-8")
                for n in rows | set(grows):
                    (sdir / n).write_text("", encoding="utf-8")
                (sroot / "docs").mkdir()
                (sroot / "docs" / "a.md").write_text("문서\n", encoding="utf-8")
                (sroot / "src").mkdir()

                def walk(r):
                    return sorted(p.relative_to(r).as_posix() for p in Path(r).rglob("*") if p.is_file())

                book = StampBook(sdir, {doc_g: ["docs/*.md"]}, shome, lister=walk)

                def quiet(**kw):
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
                        got = run_gates(sdir, roster, needs, book=book, **kw)
                    return got, buf.getvalue()

                def trust(fresh=None):
                    return set(book.trusted(grows, fresh or {}))

                quiet(run=lambda _d, _n: EXIT_OK)
                s_a = trust() == set(grows)
                s_b = free_g not in trust({free_g: "시험"}) and doc_g in trust({free_g: "시험"})
                (sroot / "src" / "x.py").write_text("x\n", encoding="utf-8")
                t_c = trust()
                s_c = doc_g in t_c and free_g not in t_c
                (sroot / "docs" / "a.md").write_text("문서를 고쳤다\n", encoding="utf-8")
                s_d = doc_g not in trust()
                # ⓔ 는 **같은 지문**에서 초록 → 빨강이어야 덮기를 잰다 — 새 지문의 빨강은 덮을 초록이 애초에 없다.
                quiet(run=lambda _d, _n: EXIT_OK)
                e_before = doc_g in trust()
                quiet(run=lambda _d, n: EXIT_MISMATCH if n == doc_g else EXIT_OK)
                t_e = trust()
                s_e = e_before and doc_g not in t_e and free_g in t_e
                (sroot / "src" / "z.py").write_text("z\n", encoding="utf-8")
                fp_free = book.snap()(free_g)

                def touch(_d, n):
                    if n == free_g:
                        (sroot / "src" / "y.py").write_text("도는 사이에 썼다\n", encoding="utf-8")
                    return EXIT_OK
                _, f_out = quiet(run=touch)
                s_f = (book.green(free_g, fp_free) is None and doc_g in trust()
                       and any("안 남겼다" in ln and free_g in ln.split(":", 1)[-1].split() for ln in f_out.splitlines()))
                (sdir / doc_g).write_text("# 게이트를 고쳤다\n", encoding="utf-8")
                s_g = doc_g not in trust()
                h_seen = []
                h_got, h_out = quiet(run=lambda _d, n: h_seen.append(n) or EXIT_OK, known={n: "시험" for n in grows})
                s_h = (h_got == (EXIT_OK, [], []) and not h_seen
                       and any(ln.startswith(f"         · 앞서 쟀다 {len(grows)}개 ") for ln in h_out.splitlines()))
                # ⓘ `_check/` 가 꼭대기에 없는 저장소 — 글롭은 꼭대기 기준이라 지문도 꼭대기에서 재야 문서 변경을 본다.
                ndir = sroot / "sub" / "_check"
                ndir.mkdir(parents=True)
                (ndir / doc_g).write_text("", encoding="utf-8")
                nbook = StampBook(ndir, {doc_g: ["docs/*.md"]}, Path(tempfile.mkdtemp(prefix="map-check-home-")),
                                  root=sroot, lister=walk)
                tmps.append(nbook.home)
                n_fp = nbook.snap()(doc_g)
                nbook.put(doc_g, n_fp, EXIT_OK, 0.0)
                (sroot / "docs" / "a.md").write_text("꼭대기 문서를 또 고쳤다\n", encoding="utf-8")
                s_i = nbook.green(doc_g, n_fp) is not None and not nbook.trusted([doc_g], {})
                report(f"㉹ 판정 도장 — 같은 입력의 초록만 믿는다 · `[push_fresh]` 는 안 믿는다 · 글롭 밖/안 · 빨강이 덮는다 "
                       f"· 도는 사이 바뀌면 안 남긴다 · 게이트 파일도 입력이다 · 전부 앞서 쟀으면 초록 · 꼭대기 기준 "
                       f"({doc_g} · {free_g})",
                       all((s_a, s_b, s_c, s_d, s_e, s_f, s_g, s_h, s_i)),
                       [f"실측 ⓐ {s_a} · ⓑ {s_b} · ⓒ {s_c} · ⓓ {s_d} · ⓔ {s_e} · ⓕ {s_f} · ⓖ {s_g} · ⓗ {s_h} {h_got} "
                        f"돈 것 {h_seen} · ⓘ {s_i} — 기대 전부 True"])

                # ㉺ 차례 묶음 · `--only` — 이름은 시험 지도에서 짓는다(재는 것은 러너의 짜기이지 실물 지도가 아니다).
                #    묶음 안(ⓐ)은 동시 판에서도 겹치지 않고, 묶음 밖 둘은 서로를 기다리는 장벽을 넘어야 하므로 동시에
                #    돌아야만 초록이다(ⓑ — 전부를 차례로 돌리는 러너는 여기서 빨개진다). 두 묶음이 한 게이트를 나누면 한
                #    사슬로 잇고(ⓒ), 동시 판의 판정은 초록이며 모음 곁에 「차례로 돈 묶음」 줄이 선다(ⓓ). `--only` 는 그
                #    이름만 돌리고, 절에 없는 이름은 못 쟀다다(ⓔ).
                names = ["sa_check.py", "sb_check.py", "sc_check.py", "sd_check.py"]
                smap = ("## 게이트 — 시험\n\n| 검사 | 무엇을 재나 |\n|---|---|\n"
                        + "".join(f"| `{n}` | 시험. |\n" for n in names))
                stree = _plant(set(names), smap); tmps.append(stree)
                lock, inside, overlap = threading.Lock(), [], []
                wall = threading.Barrier(2, timeout=10)

                def sched(_d, n):
                    if n in names[:2]:
                        with lock:
                            inside.append(n)
                            if len(inside) > 1:
                                overlap.append(tuple(inside))
                        time.sleep(0.2)
                        with lock:
                            inside.remove(n)
                        return EXIT_OK
                    try:
                        wall.wait()
                    except threading.BrokenBarrierError:
                        return EXIT_MISMATCH
                    return EXIT_OK
                s_buf, o_seen = io.StringIO(), []
                with contextlib.redirect_stdout(s_buf), contextlib.redirect_stderr(io.StringIO()):
                    s_got = run_gates(stree, gate_rows(smap), {}, run=sched, jobs=4, serial={"clip": names[:2]})
                    o_got = run_gates(stree, gate_rows(smap), {}, run=lambda _d, n: o_seen.append(n) or EXIT_OK, only=[names[2]])
                    o_bad = run_gates(stree, gate_rows(smap), {}, run=lambda _d, _n: EXIT_OK, only=["zzz_not_a_gate.py"])
                chained = serial_chains({"x": ["a", "b"], "y": ["b", "e"], "z": ["q"]}, ["a", "b", "c", "e", "q"])
                s_line = any(ln.startswith("         · 차례로 돈 묶음 — ") and " → ".join(names[:2]) in ln
                             for ln in s_buf.getvalue().splitlines())
                report("㉺ 차례 묶음 — 묶음 안은 안 겹치고 밖은 동시에 돈다 · 겹친 묶음은 한 사슬 · `--only` 는 그 이름만",
                       (not overlap and s_got == (EXIT_OK, [], []) and s_line and chained == [["a", "b", "e"]]
                        and o_seen == [names[2]] and o_got == (EXIT_OK, [], []) and o_bad[0] == EXIT_UNMEASURED),
                       [f"실측 겹침 {overlap} · 판정 {s_got} · 줄 {s_line} · 사슬 {chained} · only 돈 것 {o_seen} {o_got} "
                        f"· 없는 이름 {o_bad} — 기대 겹침 없음 · (0, [], []) · 줄 선다 · [['a', 'b', 'e']] · "
                        f"[{names[2]!r}] · 없는 이름은 2"])
            else:
                report("㉶ 태우기 — 게이트 명부에 이름이 둘 이상 있어야 이빨이 선다", False,
                       [f"게이트 명부 이름 {len(grows)}개 — 못 쟀다"])
    finally:
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    bad = fails()
    if bad:
        print(f"\n❌ {len(bad)}건 실패 — {' · '.join(bad)}", file=sys.stderr)
        return EXIT_MISMATCH
    left = unmeasureds()
    if left:
        print(f"\n⚠ 못 쟀다 — {' · '.join(left)}", file=sys.stderr)
        return EXIT_UNMEASURED
    if teeth:
        print(f"\n✅ 물림이 다 문다 — 판정 {len(passes())}건 (심은 표본 · 실물 사본 · 러너 모의 — 판정 ①–⑤ 는 기본 판이 든다)")
    else:
        print(f"\n✅ 지도와 선언이 실물과 맞는다 — 판정 {len(passes())}건 (실물 {len(files)} ↔ 표 줄 {len(rows)} · "
              f"파생 칸 {len(seated)} · 심은 표본의 물림 포함 · 실물 사본과 러너 모의는 `--teeth`)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
