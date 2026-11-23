# 세션 손

**회사 PC 의 스크립트 · 스킬이 사내 앱(메일 · 일정 · 다른 Domino 앱 · ECM)을 부를 때 쓸 세션 쿠키를, 쓰는 사람의 Edge 에서 받아
파일로 남기는 손이다.**

- **받는 손** `edge_session.js` — 디버깅 포트로 떠 있는 Edge 의 브라우저 자리에만 붙어 사내 세션 쿠키를 세션 파일로 남긴다. 창 · 탭을
  안 열고 로그인하지 않는다 — 사람의 세션도 화면도 안 건드린다. 사내 앱을 다루는 손은 세션 파일이 있으면 그것으로 먼저 돌고, 서버가
  거절할 때만 이 손을 세션 파일 인자 없이 부르고(꼭 서야 할 앱만 `ecm` 처럼 붙인다) 종료 0 의 끝 줄에서 세션 파일의 경로를
  읽는다(까닭과 바퀴는 `ep_session.session_first`)
- **입구** `ep_login.js` — 대화에서 부르는 하나뿐인 명령. 먼저 사용자의 평소 Edge 에 EP 포털 탭이 있나를 보고, 없으면 그 Edge 에
  EP 포털을 열어 로그인을 먼저 세우고(못 읽으면 사용자에게 묻게 한다), 받는 손을 돌려 보고, 안 서면 포트가 열린 Edge 에 로그인 탭을 열거나, 붙을 Edge 가 없으면 ep-login 프로필의 Edge 창 하나를
  디버깅 포트(127.0.0.1 에만)와 로그인 탭으로 띄워 지켜본 뒤 다시 받는다. 사람의 평소 Edge 는 떠 있어도 안 끝낸다
- **평소 Edge 를 보는 눈** `ordinary_edge.ps1` — 포트 없는 평소 Edge 의 물음 창을 윈도 UI 자동화로 알리고 입구가 시킨
  단추 하나를 누른다. 탭 줄 · 주소창을 읽어 EP 포털 · 로그인 화면에 맞는 탭의 수만 낸다(사람의 다른 탭은 안 낸다). 입구만 부른다 — 무엇을 누를지는 입구가 회사 자리 값의 자(`epConfirm`)로 가린다
- **두 손의 바탕** — 입구와 받는 손이 함께 쓰는 것. 한 손이 다른 손의 파일을 싣지 않고 둘 다 여기서 받는다
  - `ep_places.js` — 회사 주소 · 로그인 화면 호스트 · 시한을 환경값과 `places.json` 에서 한 사전으로 내고(`settings`), 그 값으로 로그인 화면과 받을 확인 창을 가린다(`onLoginScreen` · `epConfirm`). Edge 줄도 포트를 여기서 읽는다
  - `edge_process.js` — 깔린 Edge 를 찾고(`findEdge`), 디버깅 포트를 연 Edge 를 같은 차례로 찾는다(`debugPorts` · `portsToSee` · `openPort`)
  - `ep_exit.js` — 받는 손의 닫힌 종료 값 다섯(`EXIT`)과 멈춤 꼴(`Exit`)
  - `ordinary_logon.js` — 평소 Edge 의 로그인을 읽는 바탕: 이 윈도 로그온의 열쇠와 두 기록(「해 봤다」 `ordinary-logon` · 「섰다」 `ordinary-stood`),
    평소 Edge 를 보는 눈과 그 가름, 그것들로 「이 로그온에 평소 EP 로그인이 섰나」를 아무것도 안 열고 가리는 답(`ordinaryLogin`)
- **빌려 주는 답** `ordinary_status.js` — 그 답을 한 낱말(`stood` · `tried` · `missing`)로 내는 문. 문서함 손이 PC 의 문서함 에이전트를 부르기 전에
  `ep_session.ordinary_login` 을 거쳐 묻는다 — 입구를 대신 부르지 않는다
  - 받는 손이 내놓는 이름 가운데 `settings` · `onLoginScreen` · `epConfirm` · `debugPorts` · `Exit` · `EXIT` · `VERSION_MS` 는 바탕의 것을 다시 낸다
- **파이썬에서 부르는 자리** `ep_session.py` — 받는 손을 돌려 종료 값 · 세션 파일 · 손의 말을 닫힌 꼴 하나로 내고, 그 세션 파일을
  쿠키 통으로 읽는다(`load_jar`). 사내 앱 스킬의 얇은 명령과 앱 손이 이 폴더를 `sys.path` 에 넣고 싣는다 — 받는 손의 계약과 세션
  파일의 꼴을 읽는 코드가 이 한 자리다. 그 명령들이 대화에 내는 답 하나의 크기(`OUT_BYTES`)도 여기 산다. 앱 손이 함께 쓰는
  것도 여기다 — 프록시 없이 묻고 리다이렉트를 안 따라가는 opener · SSO 넘김 화면의 칸 읽기(`sso_form`) · 이름을 견주기 꼴로
  누르기(`squash`) · 화면을 다루는 node 손 돌리기(`run_hand`)
- **얇은 명령의 뼈대** `ep_command.py` — 사내 앱 스킬의 얇은 명령이 함께 쓰는 자리. 명령을 멈추는 꼴(`Stop`) · 종료 값 · 답을 JSON
  하나로 내는 끝(`finish`) · 답 크기에 본문 맞추기(`fit_text`) · 받아 둔 파일 읽고 쓰기(`kept` · `keep`) · 바쁜 구간 사이의 비는 때
  셈(`gaps_of` — 회의실의 빈 틈 · 일정의 모두 비는 때) · 사람 파일 읽기(`people_of` · `add_people_file` — 주소록이 쓴 people.json 을
  사람을 받는 손이 다 같은 인자 `--people-file` 로 받는다 · 손마다 제 열쇠만 고른다). 새 사내 앱 스킬은 제 서버를
  묻는 앱 손과 제 명령만 짓고 나머지는 이 두 파일을 부른다 — 한 스킬에서 고친 것이 같은 일을 하는 스킬에 다 닿게
- **Edge 에 붙는 줄** `edge_cdp.js` — 쓰는 사람의 Edge 에서 화면을 다루는 node 손(`run_hand` 가 돌리는 손)이 함께 싣는 자리. 디버깅
  포트에 묻기 · CDP 한 줄(Edge 의 답 하나에 두는 시한 · 사건 받기) · 기다리기 · 프레임 펴기. 종료 값은 싣는 손이 준다 — 손마다 표가
  다르다. 어느 탭 · 어느 프레임에서 무엇을 누르나는 손이 든다. 받는 손(브라우저 자리에만 붙는다)과 입구(로그인 탭 하나의 페이지
  자리에 붙는다)는 제 줄을 따로 든다. 포트는 `ep_places.js` 에서 읽는다
- `login.sh` — 대화에서 입구를 부르는 껍데기
- **내주는 이름의 한 자리** `handout.py` — 다른 스킬이 이 폴더의 파일에서 싣거나 읽는 이름의 표. 거기 없는 이름은 싣지 않는다

부르는 꼴 · 종료 값과 종료 값마다의 「다음」 · 세션 파일의 자리와 꼴 · 환경변수는 세 파일의 머리말이 든다 — 여기 옮겨 적지 않는다.
대화에서 쓰는 절차는 스킬 `ep-login` 이 든다. 형제 스킬(어느 스킬이 무엇을 싣나는 `handout.py` 의 이름으로 찾는다)과 깔린 자리에서 부르는
앱도 이 손을 쓴다 — 복사해 쓰는 밑판이 아니라 불러 쓰는 손이라, 공개 이름과 꼴(부르는 꼴 · 종료 값 · 세션 파일의 꼴)을 바꾸면
부르는 쪽이 다 깨진다. 바꿀 때는 아래를 돌고 부르는 쪽을 같은 판에 고친다.

## 돌려 보기

```bash
node _check/skills/ep-login/check_session.js            # 이 스킬의 edge_session.js · ep_login.js · ordinary_edge.ps1 을 잰다 — 가짜 SSO · 메일함 · ECM · EP 포털과 검사가 띄운 Edge(임시 프로필 · 평소 Edge 의 대역은 화면 밖에 창으로 내내 뜨고, 입구 판정 둘이 창을 잠깐 띄운다)
node _check/skills/ep-login/check_session.js <폴더>     # 다른 폴더의 사본을 잰다
python -X utf8 -I _check/skills/ep-login/check_ep_session.py        # ep_session.py 의 바퀴를 잰다 — 파일부터 · 거절되면 손 한 번 · 바꾸는 일은 손부터. 대역 손이라 Edge 는 안 뜬다. ep_command.py 는 받아 둔 파일을 못 남겨도 답을 안 잃나 하나
```

검사는 설정 저장소에 있다 — 깔린 스킬 폴더에는 없다. 설정 저장소 루트에서 돌린다. 끝 줄이 「통과 N/N」이면 선 것이다. 쓰는 사람의 Edge 에는 붙지 않고 127.0.0.1 · localhost 밖으로 안 나간다. Node 22 이상 · Edge 가
든다. `ep_session.py` 는 `check_mail.py`(설정 저장소 `_check/skills/company-mail/`)가 대역 손으로 잰다.

왜 이 길인가와 잰 것 · 빌린 것 · 가짜로 못 재어 회사에서 잴 것은 `../references/SOURCES.md` 가 든다.
