# 출처

이 스킬은 참조 원문 없이 섰다 — 보관한 파일이 없다.

## 견준 표준

- **Chrome DevTools Protocol** — 브라우저 자리의 `Storage.getCookies` · `Storage.setCookies` · `Target.createTarget`(`background`) ·
  `Target.closeTarget`. 받는 손이 탭에 안 붙고 쓰는 도메인이다(chromedevtools.github.io/devtools-protocol)
- **Chrome 136 의 디버깅 포트 바꿈** — 기본 데이터 폴더에는 `--remote-debugging-port` 를 안 받고 `--user-data-dir` 이 들어야
  한다(developer.chrome.com/blog/remote-debugging-port). Edge 는 공지가 없고 같은 증상의 사용자 보고가 있다
  (learn.microsoft.com 의 Q&A 「Microsoft Edge Remote Debugging is Not Working When Using the Default User Profile」). 2 절의
  종료 3 갈래(`--profile`)가 이 자리다 — 판은 띄워 본 결과로 가른다
- **RFC 6265** — 받는 손이 SSO 넘김을 따라갈 때 쿠키를 싣고 받는 규칙(도메인 · 경로 · 만료)

## 본 후보

- GitHub 의 `SKILL.md` 코드 검색 「remote-debugging-port」(2026-11-06) — 브라우저를 디버깅 포트로 띄워 화면을 보거나 긁는
  개인 저장소의 스킬들이 나왔다. 공식이거나 널리 쓰인 것이 없고, 쓰는 사람의 세션을 끊지 않고 사내 SSO 를 빌리는 물음은 아무도
  안 다뤘다 — 탈락
- Playwright 의 `connectOverCDP` — 붙는 손의 첫 후보였다. 탭마다 붙어 사람의 확인 창을 닫고, 확인 창 하나에 붙기가 멈춰 버렸다
  (`scripts/README.md` 「잰 것」). 새 창 갈래(`--launch`)만 Playwright 를 쓴다

## 우리 판이 기댄 자리

- 붙는 길 · 종료 값 · 사람의 몫 — mail-secretary 결정 0009 · mail-secretary 결정 0023 과 회사 확인 대장 #28 「돌리기 전에」
- ECM 세션 — 같은 대장 #28 의 ECM 판
