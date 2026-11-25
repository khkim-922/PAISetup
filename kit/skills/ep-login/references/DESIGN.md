# ep-login 손의 설계 — 왜 이렇게 받나

`scripts/` 의 머리말이 부르는 꼴 · 환경변수 · 종료 값을 들고, 여기는 그 꼴을 고른 까닭을 든다. 잰 것 · 빌린 것은 `SOURCES.md` 가 든다.

## 받는 손(edge_session.js)

### 어느 Edge 에 붙나

이 PC 에서 디버깅 포트를 연 Edge 를 다 찾아(`debugPorts` — 입구의 포트 `DEFAULT_PORT` 가 먼저) 차례로 붙고, 꼭 서야 하는 앱이 다
선 첫 Edge 의 쿠키를 남긴다. 다른 세션이 이미 띄워 로그인한 Edge 가 있으면 그 로그인을 쓴다 — 새로 띄우거나 로그인을 청하지
않는다. 다 붙었는데 어디서도 안 섰으면 처음 붙은 Edge 의 종료 3 · 4 를 낸다. `--ecm-tab` 의 탭은 처음 붙은 Edge 에만 연다.

### 어떻게 붙나

Playwright 의 connectOverCDP 를 안 쓴다. 디버깅 포트의 브라우저 자리(`/json/version` 의 웹소켓)에만 붙어 `Storage.getCookies` 로
쿠키를 읽는다. 탭에는 붙지 않는다 — 그래서 사람의 탭을 안 건드린다. connectOverCDP 는 탭마다 붙고, 듣는 손이 없으면 사람의 탭에
뜬 확인 창을 「취소」로 닫으며, 한 탭이라도 확인 창을 띄운 채면 붙기 자체가 시한까지 멈춘다(잰 판은 `SOURCES.md` 「잰 것」).

묻기(앱 확인 · ECM 받기)는 이 손이 Node 의 http 로 하고, 그 쿠키는 Edge 에서 읽은 것을 싣는다. 답이 고친 쿠키는 Edge 에도 써
둔다(`Storage.setCookies`) — 사람의 Edge 가 그 주소를 열었을 때 받았을 쿠키와 같은 것이라, Edge 와 서버의 세션이 어긋나지 않는다.

### Domino 의 확인

`MAILBOX_URL` 이 있으면 그 메일함의 받은편지함 목록 하나, 없으면 Domino 서버의 세션 확인 주소
(`/common/lib_f.nsf/checksessionstatus?Openpage` → `{"status":"login"}` · 웹메일이 수십 초마다 부르는 주소)다. 둘 다 메일을
안 건드린다. 세션 확인 주소의 답이 그 꼴이 아니면 다 「로그인 안 됨」으로 본다. 확인이 안 서면 그 확인 주소에서 아래의
따라가기를 한 번 한다(SSO 는 섰는데 Domino 서버에 한 번도 안 들른 Edge).

### ECM 넘김 따라가기

세션은 swpecm 호스트의 쿠키(JSESSIONID)다. 그 쿠키가 없거나 서버가 안 받을 때만 SSO 넘김 주소
(`redirect.jsp?redir_url=<ECM 첫 화면 index.jsp>`)를 이 손이 따라가 받는다: 리다이렉트 · 스스로 제출하는 폼(`submit()` 을 부르는
폼 · 스크립트가 action 을 채우는 회사 넘김 화면도) · ECM 첫 화면이 에이전트 웹소켓 없는 브라우저에 주는 `login.do` 주소 ·
location 으로 넘기는 스크립트를 회사 호스트 안에서만 `MAX_HOPS` 걸음까지 따라가고, 메인에 다다르거나 암호 칸이 있는 화면
(로그인)에서 멈춘다. 스크립트가 폼 자체를 지어 내는 꼴처럼 이 손이 못 따라가는 꼴이면 「ECM — 못 받았다」이고(종료 4), 그때의
갈래가 `--ecm-tab` 이다. 넘김이 로그인 화면에서 멈췄으면 로그인이 끊긴 것이라 3 이다. 메일 · 일정만 쓰는 판이 ECM 넘김을 매번
치르지 않게, ECM 은 부른 쪽이 `ecm` 을 준 판에서만 받는다.

### 무엇을 파일에 남기나

회사 도메인(`SESSION_DOMAIN`)과 그 아래 호스트에 실리는 쿠키만. 로그인 화면 호스트(SSO · ADFS)가 제 이름으로 받은 쿠키, 회사
밖 사이트의 쿠키, 사이트 저장소(origins)는 안 남긴다 — Edge 는 그 프로필의 모든 사이트 쿠키를 낸다. `.posco.net` 쿠키는 메일 ·
일정 · 다른 Domino 앱이 다 쓰고, ECM 쿠키는 swpecm 호스트에 산다. 한 파일에 둘이 함께 들 수 있고, 읽는 쪽은 호스트로 골라 쓴다
— 어느 호스트의 쿠키가 꼭 있다고 기대지 않는다.

### 회사 자리 값

메일 서버 · ECM 주소 · 세션 파일의 기본 자리 · 평소 Edge 를 보는 눈의 두 시한은 `scripts/places.json` 한 장이 든다 — 입구와 받는 손은 회사 자리 값(`ep_places.js`)이 `require` 로, 파이썬 손은
`ep_session.py` 를 거쳐 json 으로 읽는다. 형제 스킬의 파이썬 손은 `ep_session` 의 이름(`DEFAULT_FILE` · `DOMINO_SERVER` · `ECM_URL` ·
`ECM_MAIN_PAGE`)으로 받고, 남의 코드를 싣지 않는 스킬(사람 없이 도는 메일함 스캔)은 이 파일의 열쇠를 곁에서 바로 읽는다 — 어느 쪽이든
내준 이름만 쓰고 남의 소스 글을 읽어 값을 뽑지 않는다.

## 다른 스킬에 내주는 것

사내 앱 스킬들은 이 스킬의 세션 바퀴와 명령 틀 위에 서 있다 — 쓰는 스킬들이 이미 함께 기대는 가장 아래가 이 스킬이라, 그들이 함께 쓰는
코드(명령의 뼈대 `ep_command.py` · 파이썬 자리 `ep_session.py` · Edge 에 붙는 줄 `edge_cdp.js`)와 회사 자리 값을 여기서 이름 붙여 내준다.
이 스킬이 쓰지 않는 셈(날짜 · 빈 틈 · 손가락의 표)도 그래서 여기 산다 — 새 기댐이 안 생기는 자리다.

- 다른 스킬이 이 폴더에서 싣거나 읽는 이름은 `scripts/handout.py` 한 자리에 적는다 — 거기 없는 이름은 다른 스킬이 싣지 않는다. 이름을
  바꾸거나 빼면 싣는 스킬을 같은 판에 고친다
- 명령(입구 · 받는 손)은 이름이 아니라 명령으로 내준다 — 꼴은 그 파일의 머리말이 든다
- 사람 파일의 꼴(꼴 번호 · 칸과 그 차례)은 읽는 자리 `ep_command` 한 곳이 든다 — 그 파일을 쓰는 주소록이 거기서 받아 그 차례로 쓴다. 쓰는
  쪽과 읽는 쪽이 따로 들면 한쪽만 고친 판에서 받는 손이 모든 사람 파일을 꼴이 아니라고 멈춘다

### 기본 프로필을 안 쓰는 까닭

Chromium 136 부터 기본 프로필에는 디버깅 포트가 안 열린다(Chrome 공지 · Edge 도 같다는 보고). 입구(`ep_login.js`)는 기본
프로필을 안 쓰고 제 프로필(`PROFILE_DIR` · `--profile`)로 띄운다.

## 입구(ep_login.js)

### 왜 따로 사는 프로필로 띄우나

프로필이 따로라 평소 Edge 가 떠 있어도 포트가 서고(Chromium 136 이 기본 프로필에 포트를 안 여는 것도 비켜 간다), 사람의 창은
그대로 산다. 그 창은 평소 Edge 와 쿠키를 안 나눠, 거기서 한 로그인은 SSO 가 앞선 로그인(평소 Edge 의 메일)을 끊고 새로 선다 —
사람이 평소 Edge 에서 메일을 다시 열면 거꾸로 이쪽이 끊기고, 다음 부름이 다시 로그인한다. 창을 띄우지 않는 플래그
(`--no-startup-window`)는 안 쓴다 — 사람이 그 창에서 바로 로그인한다. 동기화는 끈다(`--disable-sync`) — 새 프로필은 윈도 계정으로 저절로
로그인해 동기화를 묻는 작은 창을 따로 띄우고, 동기화로 들어온 확장의 안내 탭이 앞으로 나오면 로그인 탭에 뜬 확인 창이 닫힌다(`SOURCES.md` 「잰
것」). 그 창은 로그인 자리라 사람의 즐겨찾기 · 확장을 들일 까닭이 없다.

### 평소 Edge 를 먼저 — 사용자의 평소 로그인이 있나부터 본다

사용자의 평소 Edge(포트 없음)의 EP 로그인만 이 PC 의 프로그램(파수 · ECM 에이전트) 로그인까지 한다(`SOURCES.md` 「잰 것」 · 결정 0261). 그래서
차례는 「평소 로그인 → ep-login 창 로그인」이고, 입구는 **그 평소 로그인이 이미 있나부터 본다** — 있으면 평소 Edge 는 손대지 않고 곧장 ep-login
창 쪽(세션이 살았으면 아무 창도 안 뜬다)으로 가고, 없을 때만 평소 Edge 에 EP 포털을 연다(결정 0275). 보는 때는 받는 손의 답과 따로다 — 프로그램
로그인과 웹 세션은 수명이 달라, PC 를 새로 켠 아침에도 ep-login 프로필의 세션은 살아 있을 수 있다.

그래서 평소 로그인은 **필요한 자리에서 챙긴다.** 확인된 쓰임은 문서함 문서를 PC 로 받아 여는 일(파수 에이전트)까지라, 사람 있는 부름이 `ecm` 을
안 받고 포트 창의 세션이 살아 있으면 입구는 평소 Edge 를 보지도 열지도 않는다 — 메일 · 일정만 쓰는 일에 사용자의 화면에 창이 하나 더 서고 그
로그인이 포트 창의 메일을 끊어서다. 문서함 손은 PC 의 문서함 에이전트를 부르기 전에 빌려 주는 답(`ordinary_status.js` · 파이썬은
`ep_session.ordinary_login`)으로 묻고, 없으면 세션 없음(3)과 「입구를 `ecm` 으로」로 멈춘다 — 입구를 대신 부르지 않는다. 사실은 둘이다:
「해 봤다」(로그온 표 — 걸음이 시한에 끝나도 남는다)와 「섰다」(입구가 포털 탭을 봤거나 연 탭이 포털로 넘어갔거나 사용자가 「했다」고 답한 때만
남긴다). 해 봤는데 안 섰으면 문서함 손은 멈추지 않고 사람이 할 일을 한 줄 말한다 — 끝없이 「입구부터」를 안 낸다. 평소 Edge 를 못 읽고 로그온 열쇠도 없는 PC(PowerShell 이 막혀 둘이 함께 진다)도 같다 — 답은 「가릴 수 없다」(unsure)다. 「없다」로 멈추면
입구가 물은 답을 열쇠 없이 못 남겨 같은 자리로 끝없이 돈다. 열쇠가 있으면 「없다」 그대로다 — 입구가 한 번 묻고 답이 남는다. 섰으면 평소 Edge 를 닫았어도
그 로그온에는 아무도 다시 안 본다(한 번 선 평소 로그인은 그 뒤로 듣는다 — `SOURCES.md` 「잰 것」의 사람이 알린 줄). 사람 없는 아침 부름(인자는
`domino --unattended`)은 이 건너뛰기에서 빠진다 — 그날의 평소 로그인을 스스로 세우는 자리다.

평소 걸음은 로그인 탭이 SSO 를 재며 여는 주소(회사 SSO)를 연다 — 주소를 고르는 자리는 하나다(`loginUrls`). 평소 Edge 에는 포트가 없어 연 탭을
평소 EP 로그인 화면으로 넘기지 못하니, 시한 뒤에도 그 탭이 로그인 화면에 머물면 SSO 가 안 서는 로그온으로 남기고 같은 Edge 의 새 탭에 EP 포털을
열어 사람이 친다(아래 「SSO 가 서나」). 그 기록이 있는 로그온은 처음부터 EP 포털을 연다.

사람의 로그인을 돌려주는 문(`--give-back`)은 평소 걸음 하나만 한다 — 포털 탭이 있어도 열고, 포트 창은 안 건드리고 다시 받지도 않는다(다시
받으면 포트 창이 다시 로그인해 사람의 로그인을 곧장 도로 가져간다).

**사용자의 평소 로그인은 평소 Edge 에 선 EP 포털 탭이다.** 포트가 없으니 CDP 대신 윈도 UI 자동화(`ordinary_edge.ps1` 의 `tabs`)로 같은 것을 읽는다 —
창마다 앞 탭의 주소(주소창의 값)와 모든 탭의 제목(탭 줄). 포트 창에서 CDP 로 탭의 주소 · 제목을 읽는 것과 같은 일이고, 견주는 자도 입구가 이미 든
두 주소다 — EP 포털(`EP_PORTAL`)의 호스트와 로그인 화면 호스트(`SESSION_LOGIN_HOSTS`). 판정은 셋으로 닫는다.

- **있다** — 어느 창의 앞 탭이 포털 호스트이거나, 이 PC 에서 배운 포털 제목과 통째로 같은 제목의 탭이 있다. STEADY 번 잇달아 그래야 믿는다 — 한 번 본 것은
  넘어가는 중일 수 있다
- **없다** — 평소 Edge 가 안 떠 있거나, 탭이 읽혔는데 포털 탭이 없다(앞 탭이 로그인 화면이어도 없다)
- **못 읽었다** — 탭 줄도 주소창도 안 잡히는 Edge 창이 있다 · 눈이 안 선다(회사 정책이 스크립트를 막는 따위). 잠깐 다시 읽고(LOOK_TRIES) 그래도면
  이 판정이다. 탭 줄 · 주소창은 창 바로 아래 브라우저 칸(BrowserRootView)에서 찾는다 — 창에서 한 번에 찾으면 판마다 놓친다(`SOURCES.md` 「잰 것」)

**눈의 기다림은 뜨기와 보기 둘이다.** 눈은 PowerShell 이 떠 UI 자동화를 다 실은 뒤 준비 줄 하나를 먼저 낸다. 뜨기의 시한(`eye_start_s`)은 그
준비 줄이나 눈의 끝이 끝내고, 답 하나의 시한(`eye_look_s`)은 준비 줄 뒤에야 잰다 — 바쁜 PC 의 PowerShell 은 뜨는 데만 수십 초가 들어, 한
시한으로 둘을 덮으면 느리게 뜬 멀쩡한 눈을 「못 읽었다」로 접고, 뜨기만큼 늘리면 멈춘 보기를 그만큼 기다린다. 두 값은 `places.json` 한 자리가
들고, 빌려 주는 문(`ep_session.ordinary_login`)은 제 시한을 같은 값에서 짓는다 — 문이 더 짧으면 느리게 뜬 눈을 문이 먼저 끊는다.

앞에 안 선 탭은 주소가 안 보여 제목으로 알아본다. 제목은 **포트 창에서 배운다** — 같은 화면은 같은 제목이라, 로그인 탭이 지나는 로그인 화면(아이디 ·
비밀번호 칸이 선 화면 — SSO 가 지나는 중간 화면의 찰나 제목은 안 배운다)의 제목과 포트 창의 포털 주소 탭의 제목을 이 로그온 표 곁(`TITLES`)에 둔다. 두 화면의 제목만 두고 사람의 다른 탭은 안 둔다. 아직
못 배운 PC(첫 부름)는 앞 탭의 주소가 가르고, 그 부름이 다음을 위해 배운다. 포털 제목이 로그인 화면의 제목과 같으면 제목은 안 쓴다 — 로그인 화면의
탭을 포털로 읽는다.

⚠ 사람의 다른 탭은 사람의 것이다 — 눈은 주소 · 제목을 제 프로세스 안에서 견주기만 하고 맞는 수만 낸다. 입구도 진행 줄에 EP 의 두 화면 말고는
아무 주소 · 제목도 안 낸다.

- **있다** → 평소 Edge 는 안 건드리고 포트 창 갈래로 간다
- **없다** → 평소 Edge 에 로그인을 열고 그 탭이 EP 포털로 넘어가기를 같은 눈으로 본 뒤 잇는다. 회사 SSO 주소를 연 판은 그동안 확인 창을 누르며
  `SESSION_ORDINARY_SECONDS` 까지 — 지나면 알리고 ep-login 창으로 이어 메일 · 일정은 세운다(그 탭이 로그인 화면에 머물렀으면 SSO 가 안 선다 — 아래).
  SSO 가 안 서는 로그온은 EP 포털을 열고 사용자가 거기서 치는 동안 `SESSION_LOGIN_WAIT_SECONDS` 까지 — 한 부름 안에서 기다리니 종료 4 의 왕복이
  없고, 지나면 4 로 사용자에게 마쳤나를 묻게 한다. 사람이 로그인해 두고 탭만 닫았으면 연 탭이 곧 포털에 서 묻지 않고 잇는다.
  EP 포털을 연 탭은 첫 응답이 오기 전에도 주소창이 포털이다 — 그래서 그 판의 「넘어갔다」는 주소창이 포털이고 **그 탭에 화면이 섰다는 증거**가
  있을 때만이다(`committedState`): 그 탭이 이 부름 안에서 로그인 화면 호스트를 보였다(사람이 로그인하고 돌아왔다) · 그 탭의 이름이 Edge 가 첫 화면이
  안 온 탭에 다는 자리 이름이 아니다. 자리 이름은 눈이 든 목록(`ordinary_edge.ps1` 의 `$Placeholders`)과, 주소창이 포털에 머문 채 이름이 바뀌는 것을
  본 눈이 배운 것이다 — 목록에 없는 말의 Edge 는 첫 바뀜을 보기까지 막 연 탭을 「섰다」로 읽을 수 있다. 이름이 비었거나 못 읽으면 증거가 아니라 기다린다
  — 틀린 「섰다」는 아무 말 없이 문서 일을 막고 메일을 끊지만, 기다림은 시한에 사람에게 묻는다. 회사 SSO 주소를 연 판은 로그인 화면 호스트를 열어
  막 연 탭이 포털로 안 읽혀 주소창만 본다
- **못 읽었다** → 사람 있는 부름은 아무것도 안 열고 4 로 사용자에게 한 번 묻게 한다 — 오늘 평소 Edge 에서 EP 에 이미 로그인했나. 답은 다음 부름의
  `--ordinary-done` · `--ordinary-not-yet` 로 온다. 「했다」면 평소 Edge 를 안 열고(이 답은 어느 판정보다 앞선다 — 사람이 치기를 기다린 시한이 지난
  뒤의 답도), 「아직」이면 정한 틈의 걸음을 한다 — 회사 SSO 주소를 열어 `SESSION_ORDINARY_SECONDS` 동안 확인 창을 누르고 잇고, SSO 가 안 서는
  로그온이면 EP 포털만 열고 4 로 끝내 사용자가 로그인한 뒤 다시 부르게 한다. 사람 없는 부름은 물을 사람이 없어 「아직」과 같은 걸음이다 — 열고
  누르고, SSO 가 안 서는 로그온이면 보지도 열지도 않는다. 못 읽는 자리는 탭이 로그인 화면에 머무는지도 못 보니 SSO 를 재지 못한다 — 포트 창이 잰다

바깥에서 읽는 것이 흔들린다는 앞의 잰 것(`SOURCES.md` 「잰 것」)은 탭을 연 직후 몇 초 안의 넘어감을 잡으려던 읽기다. 이 판정은 이미 선 탭이
무엇인가를 읽는 것이라 다른 잼이지만, 그 교훈은 그대로 산다 — 한 번 읽은 것으로 「있다」를 정하지 않는다(STEADY).

평소 Edge 에는 포트가 없어 탭에 못 붙으니 두 일만 다른 손으로 한다.

- **주소 열기** — 사람이 여는 EP 포털(`EP_PORTAL`)을 `msedge.exe <주소>` 로 넘긴다. 떠 있으면 그 Edge 의 새 탭(앞 탭), 없으면 평소 프로필로 뜬다 —
  사람이 링크를 연 것과 같다. 늘 떼어 띄운다
- **확인 창 누르기** — 데스크톱에서 기다리는 동안 눈이 그 Edge 의 창마다 자바스크립트 물음 창을 찾아 꼴(단추 수 · 입력 칸) · 글 · 제목을 알리고,
  입구가 CDP 쪽과 같은 자(`epConfirm`)로 가려 맞는 것만 누르라고 시킨다. 제목의 앞머리가 그 물음을 띄운 화면의 호스트라 그것을 주소로 넘긴다. 키
  입력이 아니라 단추의 Invoke 로 누른다 — 키는 창이 앞에 와야 들어가 잠긴 화면 · 사람이 다른 창을 쓰는 낮에 엉뚱한 곳에 든다. 사람이 치는 판(SSO 가
  안 서는 로그온)은 사용자가 자판 앞에서 제 물음 창을 누르니 안 누른다

표(`ORDINARY_MARK`)는 **평소 Edge 를 못 읽는 자리에서 이 로그온의 평소 로그인이 정해졌다**는 기록이다 — 로그온 열쇠(`logonKey` · 이 세션의 탐색기가
뜬 때) 한 줄이고, 평소 Edge 를 연 걸음 직후나 사용자가 「했다」고 답한 때 남긴다. 못 읽었을 때 표가 있으면 그 로그온에는 다시 안 묻고 다시 안 연다 —
물음은 로그온마다 많아야 한 번이다. 읽히는 자리에서는 탭이 판정한다(표는 안 본다). 로그온 열쇠를 못 읽으면 표를 안 읽고 안 남긴다 — SSO 가 안
선다는 기록도 못 남아, 그 PC 는 부를 때마다 회사 SSO 주소로 다시 잰다. 사람 없는 부름은 SSO 가 안 서는 로그온에서 표도 안 남긴다 — 남기면
사용자가 와서 부른 대화가 평소 걸음을 건너뛴다. 평소 Edge 를 연 뒤에는 세션을 다시 받는다 — 평소 로그인이 포트 창의 메일을 끊는다.

눈이 안 서면(회사 정책이 스크립트를 막는 따위) 「못 읽었다」 갈래로 간다. 눈은 사람의 페이지 나무를 훑지 않는다 — 물음 창은 브라우저 창 아래 얕은
자리에서만 찾고, 탭은 탭 줄 · 주소창만 읽는다. 검사는 `EP_ORDINARY_PROFILE` · `EP_PORTAL_URL` · `SESSION_ORDINARY_SECONDS` 로 사람의 Edge 대신 버리는
프로필 · 가짜 포털 · 짧은 틈을 준다.

### SSO 가 서나 — 자리를 어림하지 않고 잰다

입구가 고르는 것(회사 SSO 주소를 열어 통합 인증에 맡기나, 사람이 치는 화면을 여나 · 사람 없는 부름이 창을 띄우나)은 다 **이 로그온에 SSO(통합
인증)가 서나** 하나에 걸린다. 그것을 PC 의 종류(VDI · 데스크톱)로 어림하지 않는다 — VDI 를 환경 변수로 가린 판정이 거짓으로 나온 VDI 에서 입구가
회사 SSO 주소를 열고 그 화면을 로그인 중으로 읽어 시한까지 기다렸다(`SOURCES.md` 「잰 것」). 미리 묻는 길도 없다 — 그래서 회사 SSO 주소를 연 탭에서
잰다.

- **포트 창의 로그인 탭** — 셋 가운데 하나면 안 선 것이다: 로그인 화면 호스트의 요청이 아이디 · 비밀번호를 묻는다(통합 인증이 못 답한 401 —
  `Fetch.authRequired` 로 받아 Edge 의 자격 증명 창은 띄우지 않고 거절한다) · 입력 칸 화면에 `SESSION_FALLBACK_SECONDS` 넘게 머문다 · 입력 칸이 안
  보여도 `SESSION_SSO_SECONDS` 안에 못 넘는다. 안 섰으면 같은 탭을 평소 EP 로그인 화면으로 넘긴다(사람 없는 부름은 물러난다)
- **평소 Edge 의 걸음** — 포트가 없어 화면 속은 못 보니 눈이 본 탭으로 가른다: `SESSION_ORDINARY_SECONDS` 가 지나도 앞 탭이 로그인 화면 호스트에
  머물고, 그 탭을 막은 사람의 물음 창(제목에 띄운 화면의 호스트가 든 자바스크립트 창)이 없으면 안 선 것이다. 사람 있는 부름은 같은 Edge 의 새 탭에
  EP 포털을 열어 사람이 치기를 기다린다 — 로그인 화면에 머문 앞 탭은 사람의 것이라 닫지 않는다
- **기록** — 안 선 것을 보면 그 윈도 로그온의 기록(`ordinary_logon.js` 의 `NO_SSO` · 로그온 열쇠 한 줄)으로 남긴다. 그 로그온의 다음 부름은
  처음부터 사람이 치는 화면(평소 Edge 에 EP 포털 · ep-login 창에 평소 EP 로그인 화면)을 열고, 사람 없는 부름은 창을 띄우지 않고 4 로 끝난다.
  「선다」는 남기지 않는다 — 기록이 없으면 늘 회사 SSO 주소로 잰다. 비영속 VDI 는 로그온마다 기록이 사라져 그날 첫 부름이 한 번 잰다

SSO 가 서는 PC 에서 통합 인증이 `SESSION_SSO_SECONDS` 보다 늦으면 그 로그온을 안 선다고 남겨 사람이 치게 된다 — 값은 회사에서 잰다(`SOURCES.md`
「회사에서 잴 것」).

### 로그인 탭을 지켜보는 법

SSO 가 안 선다는 기록이 없으면 회사 SSO 로그인(통합 인증이 입력 없이 넘는다)을, 있으면 평소 EP 로그인 화면(사람이 친다)을 연다. 회사 SSO 로그인이
안 넘으면(위 「SSO 가 서나」의 셋) 같은 탭을 평소 EP 로그인 화면으로 넘기고 사람이 친다. 로그인 탭은 빈 탭으로 열어 붙고 창 알림을 켠 뒤에 로그인 주소로 넘긴다 — 통합 인증은 화면이 서자마자 확인 창을 띄우고, 붙기 전에
떠 있던 창은 붙은 뒤에 알림이 안 와 받을 손이 없다. 그 탭(안의 틀 포함)에서 로그인 화면 호스트가 띄운 SSO 의 「다른 PC에서 EP 접속 정보」 확인 창만 「확인」으로 받는다 — 다른 확인 창 · 다른 탭은 사람의 것이라 안
건드린다. 탭이 로그인 화면을 벗어나면 떨어지고, 받기는 로그인 시한 안에서 설 때까지 되풀이한다 — 사람이 다른 탭에서 로그인해도
선다. 띄운 창이면 로그인 걸음이 끝난 뒤(받았거나 접었거나) 그 창에 남은 빈 탭(about:blank · 새 탭)을 닫는다 — 띄운 Edge 는 시작 빈 탭 말고도
제 새 탭을 함께 열 수 있다(`SOURCES.md` 「잰 것」). 붙은 탭과 마지막 탭은 두고, 떠 있던 Edge 의 탭은 안 본다. 붙는 차례(빈 탭 → 붙기 → 알림 켜기
→ 로그인 주소)는 이 정리와 따로 그대로다.

## 파이썬 자리(ep_session.py)

### 쿠키 통이 무엇을 싣나

세션 파일을 쿠키 통으로 읽는 것은 `load_jar` 하나다 — 파일의 꼴(Playwright 저장 상태 `{"cookies": [...]}`)을 아는 자리가 받는 손과
이 파일 둘뿐이게. 어느 호스트에 어느 쿠키가 실리나는 쿠키 통이 브라우저의 규칙(도메인 · 경로 · secure)대로 가린다 — 파일에 다른
사내 호스트의 쿠키가 함께 들어도 묻는 서버에는 그 서버의 쿠키만 간다. 만료 칸이 수가 아니거나 음수면 세션 쿠키(Playwright 는
`-1` 로 적는다)로 싣는다.

### 리다이렉트를 안 따르는 opener

묻는 곳이 다 사내 호스트라 시스템 · 환경변수의 프록시 설정을 안 따른다. 끊긴 세션은 SSO 로 넘기는데, 따라가면 세션 쿠키가 SSO 에
실린다 — 그래서 리다이렉트를 따라가지 않고 `Redirected`(넘기려던 주소를 든다)로 멈추고, 부르는 쪽은 그것을 제 「세션이 끊겼다」로
옮긴다. 3xx 의 `Location` 을 성공 신호로 읽는 앱(회의실 예약의 출입증 받기)은 이 opener 를 안 쓰고 제 처리기를 둔다.

### 파일부터 도는 바퀴(session_first)

회사 PC 는 프로세스 하나를 띄우는 값이 커서, 세션 파일이 이미 있으면 그것으로 먼저 돌고 서버가 거절할 때(`expired`)만 손을 띄워
새 파일로 한 번 더 돈다. 파일의 자리는 받는 손과 같은 차례로 안다(`session_path` — `MAILBOX_COOKIES`, 없으면 손 곁 `places.json`
의 기본 자리). 읽는 일만 그렇게 두 번 돌고, 서버를 바꾸는 일은 `file_first=False` 로 늘 손부터 받아 한 번만 돈다 — 바꾼 뒤 끊긴
세션으로 둘째 판이 돌면 「이미 그렇다」는 틀린 말이 사람에게 간다. 첫 판의 표준 출력은 담아 두었다가 선 뒤에 내보내고, `expired`
가 아닌 예외로 멈추면 담은 것을 먼저 내보내고 올린다 — 되풀이해 찍히지도, 멈춘 자리까지의 글이 사라지지도 않게.

### 답 하나의 크기(OUT_BYTES)

대화 도구는 명령의 출력이 제 한도를 넘으면 파일로 빼고 모델에게는 앞 조각만 싣는다 — 이 수는 그 한도 아래에 둔다(한도는 스킬
company-regulation 의 `references/SOURCES.md` 「대화 도구에서 잰 것」). 넘친 답은 종료 0 이고 그럴듯해 아무도 모른다. 한글은 한
자가 3 바이트라 글자 수로는 못 맞춘다 — 명령이 이 수 안에서 줄 · 본문을 덜어 내고 이어 볼 자리를 댄다(끊는 법은 답의 꼴마다
달라 명령이 든다). 얇은 명령은 `ep_command` 를 거쳐, 앱 손은 `ep_session` 에서 바로 읽는다.

## 조각의 지도

로그인 손의 파이썬 자리는 둘이다 — 사내 앱 스킬의 얇은 명령이 함께 쓰는 뼈대(`ep_command.py`)와 받는 손을 부르고 세션 파일을 읽는
자리(`ep_session.py`). 입구(`ep_login.js`)와 받는 손(`edge_session.js`)은 자바스크립트라 이 지도에 안 선다 — 함수의 머리 주석을 문장으로
읽고 부름을 잇는 손은 표준 라이브러리로 정확히 못 짓는다(중첩 함수 · 화살표 함수 · 객체의 메서드를 가르려면 JS 파서가 든다). 두 손의
까닭은 위 절들이 든다.

아래는 코드에서 뽑은 지도다 — 줄의 문장은 그 조각 머리말의 첫 문장이라, 문장을 고치려면 머리말을 고치고 다시 짓는다.

<!-- drawn:piece-map · 손으로 고치지 않는다 — scripts/skill-map.py 가 짓는다 -->
| 조각 | 맡은 일 | 싣는 곁 조각 | 다른 스킬에서 싣는 것 |
|---|---|---|---|
| `ep_command.py` | 사내 앱 스킬의 얇은 명령이 함께 쓰는 뼈대 — 명령을 멈추는 꼴 · 종료 값 · 답을 JSON 하나로 내는 끝 · 답 크기에 본문 맞추기 · 받아 둔 파일 · 날 말(오늘 · 내일 · 모레) · 요일 말에 돌려주는 날짜 표 · 서울 시각과 날짜의 꼴(「<날 말> HH:MM」 도) · 모델이 쓴 글 파일 · 사람 파일(한 손이 찾은 사람을 다음 손이 받는 people.json) · 종료 값의 뜻 · 빈 틈 셈(바쁜 구간 사이의 비는 때) · 손가락의 표(한 건을 다루는 손 — 일정 · 회의실 — 의 출발 · 바꿀 것 · 아직 없는 손가락 칸과 그 거름 · 지도 줄 · 확인 열쇠). 얇은 명령(company-board · company-regulation · company-meeting-room · company-calendar · company-ecm(종료 값 · 글 파일 · 범례 · 사람 파일) · company-approval · 종료 값 · 받아 둔 파일 · 본문 맞추기는 company-mail 도)이 이 폴더를 ``sys.path`` 에 넣고 싣는다. | `ep_session` | — |
| `ep_session.py` | 받는 손(``edge_session.js``)을 파이썬에서 부르고 그 손이 남긴 세션 파일을 읽는 한 자리 — 사내 앱 스킬의 얇은 명령과 앱 손이 이 폴더를 ``sys.path`` 에 넣고 싣는다. | — | — |
| `handout.py` | 로그인 스킬이 다른 스킬에 내주는 이름의 한 자리 — 이 폴더의 파일 → 다른 스킬이 그 파일에서 실어 쓰거나 읽는 이름. | — | — |

**다른 스킬이 부르는 조각** — 입구에서 안 닿는 것.

- `ep_command.Stop` ← company-approval · company-board · company-calendar · company-directory · company-ecm · company-mail · company-meeting-room · company-regulation — 명령을 멈춘다 — ``code`` 가 종료 값, ``kind`` 가 JSON 의 error 값, 메시지가 사람에게 낼 까닭이다.
- `ep_command.load` ← company-approval · company-board · company-calendar · company-directory · company-meeting-room · company-regulation — ``where`` 폴더의 모듈을 싣는다 — ``-I`` 로 돌면 그 폴더가 ``sys.path`` 에 없어 넣고 싣는다.
  - ↑ `Stop`
- `ep_command.size` ← company-approval · company-board · company-calendar · company-meeting-room · company-regulation — 답이 표준 출력에서 차지할 바이트 수 — ``finish`` 가 찍는 꼴(``indent``) 그대로 센다.
- `ep_command.exit_legend` ← company-approval · company-board · company-calendar · company-directory · company-ecm · company-mail · company-meeting-room · company-regulation — 맨 위 --help 의 종료 값 범례 — 그 손이 내는 값(``codes``)마다 ``EXIT_MEANINGS`` 의 뜻을 한 줄씩, 손이 덧붙일 것(``more`` — 값 → 말)은 그 아래 줄에 단다.
- `ep_command.no_session` ← company-mail — 받는 손이 못 선 까닭(``ep_session.NoSession`` 의 ``got``)을 종료 값으로 옮긴다 — 남은 파일 없는 2 와 3 은 ep-login(종료 3), 1 과 경로 없는 0 은 도구 고장이다.
  - ↑ `Stop`
- `ep_command.finish` ← company-approval · company-board · company-calendar · company-meeting-room · company-regulation — 얇은 명령의 끝 — 앱 손(``where`` 폴더의 모듈 ``hand``)을 싣고(``load``) ``work(앱 손)`` 을 돌려(``_worked``) 예외를 답과 종료 값으로 옮기고(``_stopped`` · ``_failed``) 찍는다(``_print``)(머리말 「내는 것」). ``work`` 가 세션을 쥐는 법(``ep_session.session_first`` · 파일부터인가 손부터인가 · 세션 없이 답하는 갈래)을 든다.
  - `_worked` — ``work(앱 손)`` 을 돌려 그 답을 낸다 — 받는 손이 못 선 것(``NoSession``)은 ``no_session`` 의 ``Stop`` 으로 바꿔 올린다.
    - `ep_session.NoSession` ← company-directory · company-mail — 손을 띄웠는데 못 섰다 — ``got`` 이 손의 종료 값 · 말을 든다.
    - ↑ `no_session`
  - ↑ `load`
  - ↑ `Stop`
  - `_stopped` — ``Stop`` → (답, 종료 값) — 그 값과 갈래 그대로.
  - `_failed` — 앱 손의 예외 → (답, 종료 값). 끊긴 · 없는 세션은 3, ``args_errors`` 는 2, 앱 손의 나머지 예외는 1, 모르는 예외는 꼴 이름과 함께 1.
  - `_print` — 답을 표준 출력에 JSON 하나로 찍는다 — ``size`` 가 세는 꼴 그대로.
- `ep_command.fit_end` ← company-mail — 본문을 start 째 글자부터 most 자까지 싣되 한도를 안 넘는 끝 자리. ``over(끝)`` 은 그 끝까지 실었을 때 한도를 넘친 바이트 수다(안 넘으면 0 이하) — 한글은 한 자가 3 바이트라 글자 수로는 못 맞춰, 넘친 만큼 글자를 덜고 다시 잰다.
- `ep_command.fit_text` ← company-approval · company-board · company-regulation — 답 ``out`` 의 ``key`` 칸에 본문을 start 부터 most 자까지 싣되 답 전체가 ``limit`` 바이트를 안 넘게 끝을 당긴다(``fit_end``). 남은 글이 있으면 ``out["more"]`` 에 ``more(다음 자리)`` 를 싣는다 — 그 말은 명령마다 제 것이다.
  - ↑ `size`
  - ↑ `fit_end`
- `ep_command.kept` ← company-board · company-directory · company-mail · company-regulation — 받아 둔 JSON 파일 — 꼴 번호(``format`` 칸)가 ``form`` 이고 받은 지 ``days`` 날이 안 된 것만 (내용, 받은 시각)으로 낸다.
  - `stamp` ← company-calendar · company-mail · company-meeting-room — 시각 → 서울 벽시계 ``YYYY-MM-DD HH:MM`` — ``stamp_of`` 가 받는 꼴 그대로라 답의 시각을 다음 명령(일정 · 회의실)에 그대로 준다.
- `ep_command.keep` ← company-board · company-directory · company-mail · company-regulation — ``data`` 를 JSON 으로 ``path`` 에 남긴다 — 곁의 임시 파일에 다 쓴 뒤 바꿔 끼워, 도중에 죽어도 반쯤 쓴 파일이 안 남는다.
- `ep_command.text_file` ← company-approval · company-board · company-directory · company-ecm · company-mail — 모델이 쓴 글 파일 하나(바꿀 조각 · 글) — UTF-8 로 읽어 앞의 BOM 과 끝 줄바꿈을 걷는다.
  - ↑ `Stop`
- `ep_command.add_people_file` ← company-calendar · company-meeting-room — 사람 파일 인자 하나를 단다 — 이름 · 꼴(여러 번 · 안 주면 None) · 도움말이 손마다 같게.
- `ep_command.people_of` ← company-approval · company-calendar · company-ecm · company-meeting-room — 사람 파일들 → 사람들(준 차례 · 파일 안 차례 그대로). 꼴이 아니면 Stop(인자) — 없거나 UTF-8 이 아닌 파일 · JSON 이 아닌 글 · 꼴 번호가 다른 파일 · 칸이 빠졌거나 값의 꼴이 틀린 사람 · 사람이 하나도 없는 파일. 같은 사람이 두 번 들어도(받는 칸이 달라) 그대로 낸다 — 한 번씩만 쓸 손은 ``distinct`` 를 거친다.
  - `Person` — 사람 파일의 한 사람 — 칸은 파일의 칸 그대로이고, ``where`` 는 그 사람이 든 자리(「파일:몇째」)다.
    - `Person.label` — 사람에게 보일 한 줄 — 동명이인이 부서 · 직급으로 갈리게.
  - ↑ `Stop`
- `ep_command.distinct` ← company-approval · company-calendar · company-ecm · company-meeting-room — 한 사람은 한 번 — 사번 · 메일 주소 · Notes 이름 · (이름, 메일 ID) 가운데 먼저 찬 것으로 같은 사람을 가린다(이름만으로는 안 가린다 — 동명이인이 하나로 접힌다). 먼저 든 줄이 남는다.
  - `notes_key` ← company-calendar — Notes 이름을 견줄 꼴 — 「CN=홍길동/OU=…/O=…」 와 줄인 꼴 「홍길동/…/…」 을 같게(마디마다 「이름=」 을 떼고 대소문자를 안 가린다).
- `ep_command.weeks_word` ← company-calendar · company-meeting-room — 이번 주부터 ``WEEKS_SHOWN`` 주의 날짜 · 요일 표 한 줄 — 요일로 말한 날을 모델이 세지 않고 고르게.
- `ep_command.day_of` ← company-calendar · company-meeting-room — 사람이 준 날 — 날 말(``DAY_WORDS`` · 대소문자 무시)이나 ``YYYY-MM-DD``. 비면 오늘이다.
  - ↑ `Stop`
  - `today_word` ← company-calendar · company-mail · company-meeting-room — 멈추는 말에 싣는 오늘 — 모델이 「내일」 · 「다음 주 금요일」 을 제 셈으로 날짜로 바꿀 때 기댈 자리.
  - ↑ `weeks_word`
  - `_real_date` — ``YYYY-MM-DD`` 꼴의 있는 날 — 꼴이 아니거나 없는 날(2026-13-45 · 2026-02-30)이면 None.
- `ep_command.date_of` ← company-approval · company-board · company-mail — 사람이 준 날짜 — 있는 날의 ``YYYY-MM-DD`` 만. 아니면 Stop(인자) — 말은 ``lead``(「--since 는」 처럼 무엇이 틀렸나) · 받는 꼴 · 오늘을 든다.
  - ↑ `_real_date`
  - ↑ `Stop`
  - ↑ `today_word`
- `ep_command.stamp_of` ← company-calendar · company-mail · company-meeting-room — 서울 벽시계 ``YYYY-MM-DD HH:MM`` 이나 「<날 말> HH:MM」(오늘 · 내일 · 모레) → 서울 시간대가 붙은 시각. 요일 말이 든 시각은 날을 고르지 않고 Stop(인자)으로 날짜 표를 돌려준다(``day_of``). 그 밖에 꼴이 아니면 Stop(인자) — 말이 받는 꼴을 든다.
  - ↑ `day_of`
  - ↑ `Stop`
  - ↑ `today_word`
- `ep_command.gaps_of` ← company-calendar · company-meeting-room — ``lo`` ~ ``hi`` 안에서 ``need`` 이상 비는 때를 (시작, 끝) 차례로 낸다.
- `ep_command.Start` ← company-approval · company-calendar · company-meeting-room — 출발 하나 — 앱의 화면 · 창 하나.
  - `Start.dest` — 출발을 고르는 인자의 argparse 이름(``flag_dest``).
    - `flag_dest` — 인자의 argparse 이름 — ``--add-to`` → ``add_to``.
- `ep_command.Change` ← company-approval · company-calendar · company-meeting-room — 바꿀 것 하나 — 손가락 하나.
  - `Change.name` — 바꿀 것의 이름 — 사람 말에서 「 — 」 앞.
- `ep_command.NotYet` ← company-approval · company-calendar · company-meeting-room — 아직 없는 손가락 하나 — 회사에서 안 잰 화면 동작이라 짓지 않았다.
- `ep_command.given` ← company-approval · company-calendar · company-meeting-room — 표의 줄(``Change`` · ``NotYet``)의 인자 가운데 하나라도 받았나.
  - ↑ `flag_dest`
- `ep_command.fingerprint` ← company-approval · company-calendar · company-meeting-room — 보인 판의 열쇠 — 판 전체(JSON 으로 옮길 것)의 해시. 같은 판이면 늘 같은 글자이고, 무엇이든 달라지면 달라진다.
- `ep_command.refuse_not_yet` ← company-approval · company-calendar · company-meeting-room — 아직 없는 손가락을 받았으면 사람이 어디서 하나를 대며 Stop(인자) — 거듭 준 칸(``NotYet.again``)도 그 손가락을 바란 것이다.
  - ↑ `flag_dest`
  - ↑ `given`
  - ↑ `Stop`
- `ep_command.pick_start` ← company-approval · company-calendar · company-meeting-room — 부른 명령의 출발 — 출발을 고르는 인자 가운데 받은 것, 없으면 인자 없는 출발. 둘 이상 받았으면 Stop(인자).
  - ↑ `Stop`
- `ep_command.refuse_foreign` ← company-approval · company-calendar · company-meeting-room — 그 출발이 안 받는 손가락을 받았으면 그 일을 어디서 하나를 대며 Stop(인자).
  - ↑ `given`
  - ↑ `Stop`
- `ep_command.refuse_missing` ← company-approval · company-calendar · company-meeting-room — 그 출발이 꼭 드는 손가락이 빠졌으면 Stop(인자). ``have(줄)`` 이 참이면 다른 인자가 그 줄을 채운 것이다.
  - ↑ `given`
  - ↑ `Stop`
- `ep_command.change_lines` ← company-approval · company-calendar · company-meeting-room — --help 지도의 「바꿀 것」 줄 — 손가락마다 출발별 표시(● 꼭 든다 · △ 받되 안 쟀다 · ○ 받는다 · — 없다)와 사람 말, 그 아래 — 의 자리 · △ 의 자리.
- `ep_command.not_yet_lines` ← company-approval · company-calendar · company-meeting-room — --help 지도의 「아직 없는 손가락」 줄 — 부르는 인자(거듭이면 「인자 거듭」)와 무엇을 · 어디서.
  - ↑ `NotYet`
- `ep_session.known_file` ← company-directory — 받는 손을 안 띄우고 세션 파일을 낸다 — ``session_path`` 의 자리에 파일이 있을 때만, 없으면 None.
  - `session_path` — 받는 손이 쓰는 세션 파일의 자리 — 손과 같은 차례(``MAILBOX_COOKIES`` → 손 곁 ``places.json`` 의 기본 자리). 파일이 있는지는 안 본다.
    - `hand_path` — 받는 손(``edge_session.js``)의 자리 — ``EP_SESSION_HAND`` 이 있으면 그 값, 없으면 이 파일 곁.
- `ep_session.SessionFileError` ← company-mail — 세션 파일이 없거나 · 못 읽거나 · 쿠키가 없다 — ``load_jar`` 가 ``missing`` 을 안 받았을 때 낸다.
- `ep_session.load_jar` ← company-approval · company-board · company-directory · company-ecm · company-mail · company-meeting-room · company-regulation — 세션 파일(``{"cookies": [...]}``)을 쿠키 통으로 낸다.
  - `_lasting_until` — 만료 칸을 시각으로 — 수가 아니거나(``None`` · 글자 · 참거짓) 음수면 None(세션 쿠키), 그 밖은 그 시각.
- `ep_session.Redirected` ← company-approval · company-board · company-directory · company-ecm · company-mail · company-regulation — ``opener`` 가 리다이렉트를 따라가지 않고 멈췄다 — ``location`` 은 넘기려던 주소.
- `ep_session.opener` ← company-approval · company-board · company-directory · company-ecm · company-mail · company-regulation — ``jar`` 를 싣고(주면) 프록시 없이 묻고 리다이렉트는 안 따라가는 opener — 3xx 를 만나면 ``Redirected``. 3xx 의 ``Location`` 을 성공 신호로 읽는 앱은 이 opener 대신 제 처리기를 둔다.
  - `NoRedirect` — 리다이렉트를 따라가지 않고 ``Redirected`` 를 낸다 — 따라가면 세션 쿠키가 SSO 에 실린다.
    - `NoRedirect.redirect_request` — 넘김을 따라가지 않는다 — 넘기려던 주소를 들고 ``Redirected`` 를 낸다.
      - ↑ `Redirected`
- `ep_session.sso_form` ← company-approval · company-board · company-directory · company-meeting-room · company-regulation — SSO 넘김 화면의 ``<input>`` 칸 → ``{name: value}`` — name · value 의 차례와 따옴표 꼴(겹 · 홑)을 안 가리고, 값의 HTML 엔티티는 푼다(브라우저가 폼을 낼 때와 같은 글자). value 없는 칸은 빈 글자, name 없는 칸은 버린다.
- `ep_session.squash` ← company-board · company-mail · company-regulation — 견주기 꼴 — 빈칸 · 가운뎃점 · 괄호를 빼고 대소문자를 접는다(「안전 · 환경」 = 「안전환경」 · 「(포항)화성」 = 「포항화성」 · 「[공지] 식단」 = 「공지식단」). None 은 빈 글자다.
- `ep_session.session_first` ← company-approval · company-board · company-calendar · company-directory · company-mail · company-meeting-room · company-regulation — 흔한 길에서 손을 안 띄운다 — 있는 세션 파일로 ``use(file)`` 을 먼저 돌리고, 그것이 ``expired`` 를 내거나 파일이 없을 때만 손을 띄워 새 파일로 한 번 더 돈다(``file_first=False`` 면 늘 손부터 받아 한 번만). 손이 못 서면 ``NoSession``. 손이 같은 낡은 파일만 가리키면(Edge 에 못 붙어 안 고쳤다) 둘째 판 없이 첫 판의 ``expired`` 를 올린다.
  - ↑ `known_file`
  - `_held` — ``use(file)`` 을 돌리되 표준 출력을 담는다 — 선 뒤에 내보내고, ``expired`` 면 버리고(둘째 판이 다시 찍는다), 그 밖의 예외로 멈추면 멈춘 자리까지의 글을 먼저 내보내고 올린다.
  - `attach` — 받는 손을 말없이 돌린다 — ``apps`` 는 꼭 서야 하는 앱(``"ecm"``), 안 주면 손의 기본(domino)이다.
    - ↑ `hand_path`
    - `Attached` — 받는 손을 한 번 돌린 결과 — 손의 종료 값(code) · 손이 쓴 세션 파일(file · 없으면 None) · 손의 말(said).
      - `Attached.usable` — 손이 쓴 파일(0)이거나, Edge 에 못 붙었지만 남은 파일이 있다(2) — 서버가 받나는 부르는 쪽이 그 파일로 가린다.
    - `_node` — node 로 ``script`` 를 돌려 끝난 판을 낸다 — 출력은 UTF-8 로 읽고 못 읽는 바이트는 바꿔 읽는다(손의 글 한 조각 때문에 판 전체를 잃지 않게). ``env`` 는 이 프로세스의 환경에 더할 변수다.
      - `NoNode` ← company-board · company-mail — node 가 PATH 에 없어 손을 못 돌렸다.
      - `TimedOut` ← company-board · company-mail — 손이 시한 안에 안 끝났다 — 손은 거뒀다.
    - ↑ `NoNode`
    - ↑ `TimedOut`
  - ↑ `NoSession`
- `ep_session.run_hand` ← company-board · company-mail — 화면을 다루는 node 손(임시저장 · 보내기 · 창 띄우기) 한 판 — 손은 표준 출력의 끝 줄(빈 줄 아닌)에 답을 JSON 객체 하나로 낸다.
  - ↑ `_node`
  - `Ran` — node 손 한 판의 끝 — ``code`` 손의 종료 값 · ``answer`` 끝 줄의 답 · ``said`` 손이 댄 까닭(없으면 빈 글자).
- `ep_session.NotOpened` ← company-approval — 평소 Edge 에 주소를 못 열었다 — 메시지가 까닭이다(node 가 없다 · Edge 가 없다 · 띄우기가 졌다).
- `ep_session.open_ordinary` ← company-approval — 사람의 평소 Edge 에 주소 하나를 연다 — 입구가 EP 포털을 여는 길(``ordinary_logon.js`` 의 ``openOrdinary``) 그대로: 떠 있으면 새 탭, 없으면 평소 프로필로 뜬다.
  - ↑ `_node`
  - ↑ `NoNode`
  - ↑ `NotOpened`
  - ↑ `TimedOut`

**어디서도 안 닿는 조각** — 표 · 인스턴스를 거쳐 부르거나 아무도 안 부른다.

- `ep_session.ordinary_login` — 이 윈도 로그온에 평소 EP 로그인이 한 번 섰나 — 아무것도 안 열고 안 쓴다(입구의 「섰다」 기록을 먼저 읽고, 기록이 없을 때만 눈으로 평소 Edge 를 본다). 내는 것: ``ORDINARY_STOOD`` · ``ORDINARY_TRIED``(해 봤는데 섰는지 모른다) · ``ORDINARY_MISSING``(없다 — 입구를 ecm 으로 부른다) · ``ORDINARY_UNSURE``(못 읽고 로그온 열쇠도 없다) · ``ORDINARY_UNKNOWN``(못 가렸다). 문서함 손이 PC 의 문서함 에이전트를 부르기 전에 묻는다 — 입구를 대신 부르지 않는다.
  - ↑ `_node`
  - ↑ `NoNode`
  - ↑ `TimedOut`
<!-- /drawn:piece-map -->
