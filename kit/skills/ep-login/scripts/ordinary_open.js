// 사람의 평소 Edge 에 주소 하나를 여는 문 — 다른 스킬의 손(결재 문서 창 띄우기)이 ep_session.open_ordinary 를 거쳐 부른다. 여는 손은 바탕
// ordinary_logon.js 의 openOrdinary 한 자리이고, 입구가 EP 포털을 여는 길과 같다(떠 있는 평소 Edge 의 새 탭 · 없으면 평소 프로필로 뜬다).
// 아무것도 안 누르고 탭 · 쿠키를 안 읽는다.
//
// 부르는 꼴:
//     node ordinary_open.js <주소>
// 내는 것 — 열었으면 표준 출력에 한 낱말 opened · 종료 0. 못 열었으면(Edge 가 없다 · 주소가 http(s) 가 아니다 · 띄우기가 졌다) 종료 1 과 표준 오류의 까닭.
// 환경변수 — 입구와 같다(EP_ORDINARY_PROFILE — 검사가 버리는 프로필을 준다).
'use strict';
const { findEdge } = require('./edge_process.js');
const { ordinaryProfile, openOrdinary } = require('./ordinary_logon.js');

// 띄운 자식이 섰다(spawn) · 졌다(error) 가운데 먼저 온 것으로 끝을 낸다 — spawn 은 실패를 던지지 않고 뒤의 사건으로 알린다
function main(url) {
  if (!/^https?:\/\//i.test(url || '')) { console.error(`http(s) 주소가 아니다: ${url || '(없음)'}`); return Promise.resolve(1); }
  const exe = findEdge();
  if (!exe) { console.error('이 PC 에서 Edge(msedge.exe)를 못 찾았다'); return Promise.resolve(1); }
  return new Promise(resolve => {
    let child;
    try { child = openOrdinary(exe, ordinaryProfile(), url); } catch (e) { console.error(`Edge 를 못 띄웠다(${e.code || e.message})`); resolve(1); return; }
    child.once('error', e => { console.error(`Edge 를 못 띄웠다(${e.code || e.message})`); resolve(1); });
    child.once('spawn', () => { console.log('opened'); resolve(0); });
  });
}

if (require.main === module) main(process.argv[2]).then(code => process.exit(code));
