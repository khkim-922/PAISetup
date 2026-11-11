// 로그온 작업(설치기의 PAISetup-EpLogin)이 이름으로 부르는 자리 — 입구(ep_login.js)를 띄우기부터(--at-logon) 돌린다. 사람이 Edge 를
// 먼저 열면 그 Edge 에는 디버깅 포트가 안 서, 로그온하자마자 평소 Edge 를 포트와 로그인 탭으로 띄워 두려는 것이다.
//
// 부르는 꼴:
//     node edge_start.js [ep_login.js 의 인자]
// 내는 것 — ep_login.js 의 종료 값 그대로. Edge 가 이미 떠 있으면 아무것도 안 끝내고 2 로 물러난다.
// 이 이름은 설치기가 놓인 파일을 찾는 계약이다 — 바꾸려면 설치기(install.ps1 의 로그온 EP 로그인 창 걸음)를 같은 판에 고친다.

'use strict';
require('./ep_login.js').run(['--at-logon', ...process.argv.slice(2)]);
