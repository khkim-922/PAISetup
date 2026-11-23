// 이 윈도 로그온에 평소 EP 로그인이 한 번 섰나를 묻는 문 — 아무것도 안 열고 안 쓴다. 다른 스킬의 손(문서함 손이 PC 의 문서함 에이전트를
// 부르기 전)이 ep_session.ordinary_login 을 거쳐 부른다. 판정은 바탕 ordinary_logon.js 의 ordinaryLogin 한 자리다.
//
// 부르는 꼴:
//     node ordinary_status.js
// 내는 것 — 표준 출력에 한 낱말: stood(섰다) · tried(이 로그온에 평소 걸음을 해 봤는데 섰는지 모른다) · missing(없다 — 입구를 ecm 으로 부른다) ·
//   unsure(평소 Edge 를 못 읽고 로그온 열쇠도 없어 가릴 수 없다 — 부르는 쪽은 잇는다).
//   종료 0. 못 가렸으면(눈 · PowerShell 이 고장) 종료 1 과 표준 오류의 까닭.
// 환경변수 — 입구와 같다(EP_LOGON_KEY · EP_ORDINARY_PROFILE · EP_PORTAL_URL · SESSION_LOGIN_HOSTS — 검사의 대역을 보게 한다).
'use strict';
const { ordinaryLogin } = require('./ordinary_logon.js');

if (require.main === module) {
  ordinaryLogin().then(state => { console.log(state); process.exit(0); },
    error => { console.error(error.message); process.exit(1); });
}
