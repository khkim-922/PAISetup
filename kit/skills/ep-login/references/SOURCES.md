# 출처

이 스킬은 참조 원문 없이 섰다 — 보관한 파일이 없다.

## 견준 표준

- **Chrome DevTools Protocol** — 브라우저 자리의 `Storage.getCookies` · `Storage.setCookies` · `Target.createTarget`(`background`) ·
  `Target.closeTarget`. 받는 손이 탭에 안 붙고 쓰는 도메인이다(chromedevtools.github.io/devtools-protocol)
- **Chrome 136 의 디버깅 포트 바꿈** — 기본 데이터 폴더에는 `--remote-debugging-port` 를 안 받고 `--user-data-dir` 이 들어야
  한다(developer.chrome.com/blog/remote-debugging-port). Edge 는 공지가 없고 같은 증상의 사용자 보고가 있다
  (learn.microsoft.com 의 Q&A 「Microsoft Edge Remote Debugging is Not Working When Using the Default User Profile」). 띄우는 손(`scripts/edge_start.js`)의 종료 3 갈래(`--profile`)가 이 자리다 — 판은 띄워 본 결과로 가른다
- **RFC 6265** — 받는 손이 SSO 넘김을 따라갈 때 쿠키를 싣고 받는 규칙(도메인 · 경로 · 만료)

## 본 후보

- GitHub 의 `SKILL.md` 코드 검색 「remote-debugging-port」(2026-11-06) — 브라우저를 디버깅 포트로 띄워 화면을 보거나 긁는
  개인 저장소의 스킬들이 나왔다. 공식이거나 널리 쓰인 것이 없고, 쓰는 사람의 세션을 끊지 않고 사내 SSO 를 빌리는 물음은 아무도
  안 다뤘다 — 탈락
- Playwright 의 `connectOverCDP` — 붙는 손의 첫 후보였다. 탭마다 붙어 사람의 확인 창을 닫고, 확인 창 하나에 붙기가 멈춰 버렸다
  (아래 「잰 것」)

## 우리 판이 기댄 자리

- 붙는 길 · 종료 값 · 사람의 몫 — mail-secretary 결정 0009 · mail-secretary 결정 0023 과 회사 확인 대장 #28 「돌리기 전에」
- ECM 세션 — 같은 대장 #28 의 ECM 판

## 잰 것 — 손의 꼴을 정한 측정

- **Playwright 의 `connectOverCDP` 로 붙지 않는다** — 2026-11-06 이 PC(Edge 146 · 검사처럼 임시 프로필)에서 쟀다. 듣는 손이 없으면
  붙어 있는 동안 사람의 탭에 뜬 확인 창을 「취소」로 닫았고(`answered:false`), 한 탭이라도 확인 창을 띄운 채면 붙기 자체가 시한
  (5초 · 15초)까지 멈췄다. 브라우저 자리의 웹소켓(`Storage.getCookies`)은 같은 판에서 0.2초에 끝났고 그 확인 창은 그대로 떠 있었다.
  사내 화면은 확인 창을 띄운다(ECM 의 「세션이 종료되었습니다」 · SSO 의 「EP 접속 정보」) — 그래서 받는 손은 브라우저 자리에만 붙는다
- **136 의 선** — Chrome 은 136 부터 기본 데이터 폴더에 디버깅 포트 플래그를 안 받는다고 공지했다. Edge 의 공지는 없고 같은 증상의
  사용자 보고만 있다. 잰 회사 자리의 판은 데스크톱 131 · VDI 107 이다(mail-secretary 결정 0009 · 0023). 판은 깔린 폴더 이름으로 못
  가린다 — 회사 데스크톱의 Application 폴더에 아직 적용 안 된 업데이트의 판 폴더(143)가 도는 판(131)과 함께 있었다. 그래서 띄우는
  손은 판을 묻지 않고 띄워 본 결과(포트가 열리나)로 가른다
- **띄우는 손이 붙는 자리** — 띄운 탭 하나의 페이지 자리에만 붙는다. 브라우저 자리에 자동 붙기를 걸면 로그인 도중 SSO 가 여는 팝업
  (사내 SSO 의 ssoframe 페이지)이 디버거를 기다리며 멈추고, EP 가 빈 화면에 선다 — 회사 데스크톱에서 그렇게 멈췄다
- **새 창으로 따로 로그인하는 길은 두지 않는다** — 그 로그인이 「EP 접속 정보」로 같은 사람의 다른 세션을 끊고, 사람이 다시 로그인하면
  받아 둔 쿠키도 죽는다 — 한쪽이 늘 끊긴다. 평소 Edge 의 세션을 빌리면 둘 다 산다

## 회사에서 잴 것 — 가짜로는 못 잰다

회사 PC 에서 한 판씩 잰다. mail-secretary 의 회사 확인 대장(#28)이 Node 판 · 136 판 · SSO 만 선 Edge 에서 Domino 따라가기를 들고,
아래 넷은 아직 거기 없다.

- 조용한 ECM 받기가 못 따라갈 때 `--ecm-tab` 이 서나
- 끊긴 세션에 Domino 의 세션 확인 주소(`checksessionstatus`)가 무엇을 답하나 — 산 답 `{"status":"login"}` 만 쟀다
- 메일 서버(`DOMINO_URL` 의 기본)가 사람마다 같은가
- Edge 136 이상 PC 에서 기본 프로필에 포트가 정말 안 열리나 · `--profile` 로는 서나

## 빌린 것

| 무엇 | 어디서 | 따라가는 법 |
|---|---|---|
| 붙는 길 · 종료 값 넷 · 메일 목록으로 로그인을 가리기 · 파일에 쓰기 전에 거르기 | mail-secretary 저장소 secretary/edge_session.js(68ad771) · 결정 0009 · 0023 | 일부러 갈랐다 — 브라우저 자리에만 붙고(위 「잰 것」) · ECM 을 함께 받고 · 회사 도메인 전체로 거른다(저쪽은 메일 호스트만). 비서는 이 손을 깔린 자리에서 부르고 제 저장소에 사본을 안 든다(mail-secretary #34 · `secretary/hands.py`) |
| 띄우는 플래그 · Edge 자리 후보 · 15초 | 같은 저장소 secretary/runner.py 의 `EDGE_FLAGS` · `EDGE_CANDIDATES` · `launch_edge`(68ad771) | 손으로 따라간다 — 이쪽은 `--no-startup-window` 를 안 쓰고 EP 로그인 탭 하나로 띄운다(사람이 그 창에서 로그인하고 그대로 쓴다) |
| 회사 로그인 주소 | 같은 저장소 secretary/identity.py 의 `COMPANY_LOGIN_PATH`(68ad771) | 손으로 따라간다 |
| ECM 메인 · SSO 넘김 주소 · 세션 쿠키 · 넘김의 차례 | 같은 저장소 이슈 #28 의 ECM 첫째 · 둘째 판(2026-11-06 VDI) | 손으로 따라간다 — 실물이 바뀌면 `edge_session.js` 의 상수와 검사의 가짜를 함께 고친다 |
