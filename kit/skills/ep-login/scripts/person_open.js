// 사람에게 주소 하나를 띄우는 문 — 다른 스킬의 손(결재 문서 창 띄우기)이 ep_session.open_for_person 을 거쳐 부른다. 사내 세션이 사는 Edge(디버깅
// 포트가 열린 ep-login 창)가 떠 있으면 그 Edge 에 새 창으로 열고, 없으면 바탕 ordinary_logon.js 의 openOrdinary 로 평소 Edge 에 연다(입구가 EP 포털을
// 여는 길과 같다 · 떠 있는 평소 Edge 의 새 탭 · 없으면 평소 프로필로 뜬다).
// 포트 Edge 가 먼저인 까닭 — 회사 SSO 는 로그인 하나만 살린다. 사내 앱 손이 세션 파일로 돈다는 것은 그 로그인이 포트 Edge 에 있다는 뜻이라, 평소
// Edge 에 SSO 넘김 주소를 열면 토큰이 없어 손으로 치는 로그인 화면에 떨어진다. 아무것도 안 누르고 탭 · 쿠키를 안 읽는다.
//
// 부르는 꼴:
//     node person_open.js <주소>
// 내는 것 — 열었으면 표준 출력에 한 줄 「opened session」(포트 Edge) 또는 「opened ordinary」(평소 Edge) · 종료 0. 못 열었으면(Edge 가 없다 · 주소가
// http(s) 가 아니다 · 띄우기가 졌다) 종료 1 과 표준 오류의 까닭.
// 환경변수 — 입구와 같다(EDGE_DEBUG_PORT · EP_ORDINARY_PROFILE — 검사가 버리는 프로필 · 닫힌 포트를 준다).
'use strict';
const { findEdge } = require('./edge_process.js');
const { ordinaryProfile, openOrdinary } = require('./ordinary_logon.js');
const { edgeLine } = require('./edge_cdp.js');

const NO_PORT = 'no_port';   // 포트 Edge 가 없다는 표지 — 평소 Edge 로 물러날 까닭이고 오류가 아니다

// 포트 Edge 에 새 창으로 연다 — 열었으면 참. 포트에 아무도 안 들으면 거짓(물러난다). 포트 Edge 가 답했는데 창을 못 열면 그 까닭을 던진다 —
// 세션이 사는 곳에서 진 것을 평소 Edge 로 덮으면 다시 로그인 화면에 떨어진다
async function openInSession(url) {
  const { devtools, connect } = edgeLine({ fail: 'fail', noEdge: NO_PORT });
  let version;
  try { version = await devtools('/json/version'); } catch (e) { if (e.code === NO_PORT) return false; throw e; }
  const cdp = await connect(version.webSocketDebuggerUrl);
  try {
    await cdp.send('Target.createTarget', { url, newWindow: true });
    return true;
  } finally { cdp.close(); }
}

// 평소 Edge 에 연다 — 띄운 자식이 섰다(spawn) · 졌다(error) 가운데 먼저 온 것으로 끝을 낸다. spawn 은 실패를 던지지 않고 뒤의 사건으로 알린다
function openOrdinaryEdge(url) {
  const exe = findEdge();
  if (!exe) { console.error('이 PC 에서 Edge(msedge.exe)를 못 찾았다'); return Promise.resolve(1); }
  return new Promise(resolve => {
    let child;
    try { child = openOrdinary(exe, ordinaryProfile(), url); } catch (e) { console.error(`Edge 를 못 띄웠다(${e.code || e.message})`); resolve(1); return; }
    child.once('error', e => { console.error(`Edge 를 못 띄웠다(${e.code || e.message})`); resolve(1); });
    child.once('spawn', () => { console.log('opened ordinary'); resolve(0); });
  });
}

async function main(url) {
  if (!/^https?:\/\//i.test(url || '')) { console.error(`http(s) 주소가 아니다: ${url || '(없음)'}`); return 1; }
  try {
    if (await openInSession(url)) { console.log('opened session'); return 0; }
  } catch (e) { console.error(`세션이 사는 Edge 에 창을 못 열었다(${e.message})`); return 1; }
  return openOrdinaryEdge(url);
}

if (require.main === module) main(process.argv[2]).then(code => process.exit(code));
