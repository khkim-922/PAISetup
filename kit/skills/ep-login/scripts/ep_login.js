// 사내 세션을 세우는 대화의 입구 — 스킬 ep-login 이 부르는 하나뿐인 명령. 쓰는 사람의 Edge 에서 세션을 받아 보고(받는 손
// edge_session.js), 안 서면 그 Edge 의 상태에 맞는 로그인을 띄워 지켜본 뒤 다시 받는다. 띄운 창 · 연 탭은 사람이 그대로 쓴다.
//
// 부르는 꼴:
//     node ep_login.js [세션 파일] [domino] [ecm] [--profile <폴더>] [--ordinary-done | --ordinary-not-yet] [--trace]
//     node ep_login.js --give-back
//   세션 파일 · domino · ecm — 받는 손에 그대로 넘긴다(뜻은 그 머리말). 받는 손이 ECM 넘김만 화면 없이 못 따라가면(그 손의 4) 탭을
//     잠깐 여는 갈래(--ecm-tab)로 한 번 더 받는다 — 그 탭을 띄우기 전 알림에 함께 싣는다.
//   --profile — 띄우는 창의 프로필 폴더. 안 주면 PROFILE_DIR(LOCALAPPDATA 아래)이다.
//   --ordinary-done · --ordinary-not-yet — 평소 Edge 를 못 읽어 4 로 물은 뒤, 사용자의 답(오늘 평소 Edge 에서 EP 에 이미 로그인했다 ·
//     아직이다)을 싣고 다시 부르는 꼴. 답은 이 윈도 로그온의 표(「해 봤다」 · 「했다」면 「섰다」 기록도)로 남아 그 로그온에는 다시 안 묻는다.
//   --give-back — 사람의 평소 EP 로그인을 돌려준다: 평소 걸음 하나만 하고 끝난다. 포털 탭이 있든 「섰다」 기록이 있든 평소 Edge 에 로그인을
//     열고, 포트 창은 안 건드리고 다시 받지도 않는다 — 그 로그인이 AI 쪽(포트 창)의 메일 · 일정 세션을 끊는다. 사람 있는 부름만 받는다.
//   --trace — 로그인 탭이 이 PC 의 프로그램(파수 · ECM 에이전트)에 무엇을 보내고 무엇이 막히나를 「trace …」 줄로 남긴다. 세션이
//     살아 있어도 로그인 탭을 열어 로그인 화면과 넘어간 화면을 지켜본다. 주소는 호스트 · 경로와 칸 이름까지만 남긴다(값은 없다).
//   환경변수 EDGE_DEBUG_PORT 포트 · SESSION_LOGIN_HOSTS 로그인 화면 호스트 · SESSION_LOGIN_WAIT_SECONDS 로그인 시한 — 뜻과 기본값은
//   회사 자리 값(ep_places.js 의 settings) 한 자리에서 읽는다. 로그인 화면과 받을 확인 창도 거기의 onLoginScreen · epConfirm 이 가린다 — 받는 손과
//   같은 자다. EP_LOGIN_URL · COMPANY_LOGIN_URL 은 로그인 탭의 주소를 바꾼다 — 가짜 SSO 로 재는 검사(설정 저장소 _check/skills/ep-login/check_session.js)를 위해 있다.
//
//   EP_PORTAL_URL 은 평소 Edge 에 여는 EP 포털 주소를, EP_ORDINARY_PROFILE 은 평소 Edge 대신 볼 프로필 폴더를 바꾼다 — 같은 검사가 가짜
//   포털과 사람의 Edge 대신 버리는 프로필을 보게 한다. EP_LOGON_KEY 는 이 윈도 로그온의 열쇠(logonKey)를 그 값으로 둔다 — 같은 검사가
//   로그온마다의 차례를 탐색기가 없는 자리(CI 러너)에서도 같은 열쇠로 잰다.
//
// 프로그램이 부르는 문 — 대화의 모델은 안 부른다:
//     node ep_login.js domino --unattended
//   --unattended — 사람이 없는 부름(예약 실행 — 다른 스킬이 프로세스로 부른다). 입력 없이 넘는 통합 인증으로만 세운다 — 사람이 쳐야
//     하는 자리(VDI · 통합 인증이 안 선 로그인 화면)에서는 띄우거나 기다리지 않고 4 로 끝난다. 띄운 창은 그대로 둔다(사람이 와서 쓴다).
//     부르는 쪽은 종료 값(0 · 4 · 1)과 종료 0 의 표준 출력 한 줄(세션 파일 경로)을 읽는다.
//
// 차례:
//   받아 본다 — 받는 손을 한 번 돌린다. 사람 있는 부름이 문서함(ecm)을 안 받고 포트 창의 세션이 살아 있으면 평소 Edge 는 보지도 열지도 않는다
//     — 메일 · 일정 일에는 평소 로그인을 안 쓴다. 평소 로그인이 드는 일(문서함 문서를 PC 로 받아 여는 일)은 그 손이 그때 빌려 주는 답
//     (ordinary_status.js)으로 묻는다. ecm 을 받는 부름 · 세션이 없는 부름 · 사람 없는 아침 부름은 아래 평소 걸음을 한다. 이 로그온에 평소
//     로그인이 앞서 섰으면(「섰다」 기록) 다시 보지도 열지도 않는다 — 한 번 선 평소 로그인은 그 뒤로 듣는다(사용자가 겪어 알린 것).
//   평소 Edge — 사용자의 평소 Edge(포트 없음)에 EP 포털 탭이 있나를 윈도 UI 자동화(ordinary_edge.ps1)로 본다 — 창마다 앞 탭의 주소(EP_PORTAL 의
//     호스트인가 · 로그인 화면 호스트인가)와, 이 PC 에서 배운 포털의 탭 제목(TITLES)을 든 뒤쪽 탭. 평소 EP 로그인만 이 PC 의 프로그램(파수 · ECM
//     에이전트) 로그인까지 하고, 그 로그인이 서면 그 탭은 포털에 선다. 사람 없는 부름은 VDI 에서 보지도 열지도 않는다.
//     있다(STEADY 번 잇달아) → 평소 Edge 는 안 건드리고 「섰다」 기록을 남긴다.
//     없다(평소 Edge 가 안 떠 있거나, 읽혔는데 포털 탭이 없다) → 데스크톱은 로그인 탭이 데스크톱에서 여는 주소(회사 SSO — 통합 인증에 맡긴다)를,
//       VDI 는 EP 포털을 포트 없이 사람처럼 열고 그 탭이 EP 포털로 넘어가기를 본 뒤 잇는다(넘어가면 「섰다」 기록 · 막 연 탭은 주소창이 처음부터
//       포털이라 그 탭에 화면이 섰다는 증거까지 본다 — committedState) —
//       데스크톱은 그동안 「EP 접속 정보」 창을 누르며 SESSION_ORDINARY_SECONDS 까지(지나도 알리고 잇는다), VDI 는 사용자가 거기서 치는 동안
//       SESSION_LOGIN_WAIT_SECONDS 까지(지나면 4 로 사용자에게 묻게 한다). 사람이 로그인해 두고 탭만 닫았으면 포털이 곧 서 곧 잇는다.
//     못 읽었다(탭 줄 · 주소창이 안 보인다 · 눈이 안 선다) → 표가 있으면 안 연다. 없으면 사람 있는 부름은 아무것도 안 열고 4 로 사용자에게
//       묻게 하고(답은 --ordinary-done · --ordinary-not-yet), 「아직」 이거나 사람 없는 부름이면 정한 틈의 걸음을 한다 — 데스크톱은
//       SESSION_ORDINARY_SECONDS 동안 확인 창을 누르고 잇고, VDI 는 포털만 열고 4 로 끝내 사용자가 로그인한 뒤 다시 부르게 한다.
//     어느 갈래든 평소 Edge 에는 포트를 열지 않고, 끝내지도 쿠키를 읽지도 않는다. 사람의 다른 탭의 주소 · 제목은 눈 밖으로 안 나온다.
//   포털 · 로그인 화면의 탭 제목은 포트 창에서 배운다 — 로그인 탭이 지나는 로그인 화면(입력 칸이 선 화면)의 제목과, 포트 창의 포털 주소 탭의
//   제목(같은 화면이라 같은 제목이다).
//   그 뒤 받는 손의 종료 값(상태)으로 가른다:
//   받는다 → 0 이면 끝
//   3 붙었는데 로그인이 안 됐다 → 그 Edge 에 로그인 탭 하나를 열어 지켜본 뒤 다시 받는다
//   2 붙을 Edge 가 없다 → ep-login 프로필의 Edge 창 하나를 포트와 로그인 탭으로 띄워 지켜본 뒤 다시 받는다. 사람의 평소 Edge 는
//     떠 있든 아니든 안 끝낸다 — 끝내면 사람의 창 · 탭 · 쓰던 글이 다 닫힌다
//   4 ECM 만 못 받았다 → --ecm-tab 으로 한 번 더 받는다
// 로그인 탭을 지켜보는 법 · 왜 따로 사는 프로필로 띄우나 · 왜 평소 Edge 가 먼저인가는 references/DESIGN.md 가 든다.
//
// 짜임 — 세우는 손 main 이 차례를 엮는다: 받기(receive*) → 평소 Edge 손(ordinaryFirst) → 로그인 자리(loginPlace) → 로그인 탭 손(watchPlace ·
// watchLogin · 지켜보며 로그인 화면의 제목을 배운다) → 다시 받기(receiveUntil) → 뒤치레(tidyUp) → 끝(finish). 평소 Edge 손은 상태(ordinaryState)를 한 번 셈하고, 로그인 탭 손은 탭의
// 상태(tabState)를 한 번 셈한다. 셈과 말은 갈라 둔다 — 말은 상태만 받는다(say* · SAID_* · 끝의 말).
//
// 내는 것 — 종료 값은 닫힌 셋이다. 표준 출력은 종료 0 일 때 세션 파일의 절대 경로 한 줄뿐이고, 경과와 「다음: …」 은 표준 오류다.
// 표준 오류의 끝은 종료 4 · 1 이면 그 까닭이다:
//   0 세션이 섰다
//   4 로그인 시한 안에 세션이 안 섰다 · ECM 을 탭으로도 못 받았다 · 사람 없는 부름이 사람이 쳐야 하는 자리에 닿았다 · 평소 로그인을
//     사용자에게 물어야 한다(VDI 의 평소 Edge 를 열어 둔 뒤도) — 「다음」 대로 간다
//   1 그 밖 — Edge 를 못 찾음 · 인자 · 띄웠는데 포트가 안 열림 · 받는 손의 1
//
// ⚠ 포트는 이 PC 의 다른 프로그램도 쓸 수 있어 그 Edge 의 세션을 다 다룬다 — 127.0.0.1 에만 연다.
// ⚠ 로그인 탭에는 그 탭의 페이지 자리로만 붙는다 — 브라우저 자리에 자동 붙기를 걸면 SSO 가 여는 팝업(ssoframe)이 디버거를 기다리며
//   멈추고 EP 가 빈 화면에 선다.

'use strict';
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// VMware Horizon VDI 인가 — 에이전트가 세션에 심는 브로커 값 · VDI 도메인
const onVdi = () => Boolean((process.env.ViewClient_Broker_DNS_Name || '').trim()) || /\.VDI$/i.test(process.env.USERDNSDOMAIN || '');
// 띄우는 창의 프로필 — 사람의 평소 Edge 와 따로 산다. 로그인 쿠키가 여기 남아, 창을 닫았다 다시 띄워도 세션이 살아 있으면 로그인 없이 받는다
const PROFILE_DIR = path.join(process.env.LOCALAPPDATA || '', 'ep-login', 'edge-profile');
const PORT_MS = 15000;                // 띄운 뒤 포트가 열리기를 기다리는 시한
const UNATTENDED_MS = 60000;          // 사람 없는 부름이 통합 인증을 기다리는 시한 — 입력 없이 넘는 로그인은 몇 초면 선다
const UNATTENDED = '--unattended';
const TRACE_AFTER_MS = 20000;         // 로그인 탭이 넘어간 뒤에도 이만큼 더 듣는다 — 넘어간 화면이 PC 의 프로그램에 붙는 것은 그 뒤다
const TRACE_TEXT = 160;               // trace 줄에 옮기는 글 하나의 길이
const LOOPBACK = /^(127\.\d+\.\d+\.\d+|localhost|\[::1\])$/i;
const BROWSER_SCHEMES = /^(about|data|blob|javascript|chrome|edge|devtools|chrome-extension|extension):$/i;
const RETRY_MS = 3000;                // 로그인 뒤 받기를 되풀이하는 사이
const POLL_MS = 500;
const BLANK_SETTLE_MS = 4000;         // 로그인 뒤 띄운 창의 빈 탭을 다시 보는 시한 — 늦게 열리는 새 탭을 기다린다
const CALL_MS = 5000;                 // CDP 부름 하나의 시한
const HAND = path.join(__dirname, 'edge_session.js');
const ORDINARY_DONE = '--ordinary-done', ORDINARY_NOT_YET = '--ordinary-not-yet';
const GIVE_BACK = '--give-back';      // 평소 걸음만 하고 끝내는 문 — 사람의 평소 로그인을 돌려준다(포트 창은 안 건드린다)
const BLANK = 'about:blank';          // 로그인 탭이 붙기 전에 서는 자리 — 로그인 주소는 붙은 뒤에 연다(blankTab)
const NEW_TAB = 'edge://newtab/';     // 띄운 Edge 가 제 시작 쪽으로 함께 여는 새 탭 — 로그인 뒤 남은 빈 탭으로 닫는다(closeOwnBlanks)

// 회사 주소 · 포트 · 로그인 화면 호스트 · 시한 · 로그인 화면과 받을 창의 가림 · Edge 찾기 · 받는 손의 종료 값(RECEIVED)은 받는 손과 함께
// 쓰는 바탕이다 — 두 손이 같은 자로 가린다. 평소 Edge 의 물음 창도 같은 자(epConfirm)로 가린다
const { env, settings, onLoginScreen, epConfirm } = require('./ep_places.js');
const { VERSION_MS, findEdge, version, openPort, tabList, newTab, closeTarget } = require('./edge_process.js');
const { Exit, EXIT: RECEIVED, needNode } = require('./ep_exit.js');
// 평소 Edge 의 로그인을 읽는 바탕 — 로그온 열쇠 · 두 기록 · 눈과 그 가름. 문서함 손이 빌리는 답(ordinary_status.js)도 같은 바탕을 쓴다
const { SAVED, LOOK, EYE, EYE_GAP_MS, STEADY, TITLES, logonKey, readMark, writeMark, readStood, writeStood, readTitles, ordinaryProfile, hostOf,
  edgeEye, eyeSelect, lookOnce, lookForPortal, committedState } = require('./ordinary_logon.js');
const cfg = settings();
const say = line => console.error(line);
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── 받기 ─────────────────────────────────────────────────────────────────

// 받는 손 프로세스를 한 번 돌린다 — 내는 것: { code, out, err } · 띄우지 못했으면 { failed: 그 까닭 }
function runHand(args) {
  return new Promise(resolve => {
    const child = spawn(process.execPath, [HAND, ...args], { windowsHide: true });
    let out = '', err = '';
    child.stdout.on('data', d => out += d);
    child.stderr.on('data', d => err += d);
    child.on('error', e => resolve({ failed: e.message }));
    child.on('close', code => resolve({ code, out, err }));
  });
}

// 받는 손의 표준 출력을 가른다 — 종료 0 의 끝 줄(세션 파일)과 사람에게 넘길 경과 줄. 남은 파일의 경로 줄은 경과가 아니다
function handLines(code, out) {
  const lines = out.split(/\r?\n/).filter(Boolean);
  const file = code === RECEIVED.OK && lines.length ? lines.pop() : '';
  return { file, progress: lines.filter(line => !path.isAbsolute(line)) };
}

// 받는 손의 표준 오류에서 까닭만 — 그 손의 「다음: …」 은 뗀다(다음 걸음은 이 명령이 고른다)
const handSaid = err => err.split(/\r?\n/).filter(line => line && !/^다음:/.test(line)).join(' ').replace(/\s*다음:.*$/, '').replace(/[.\s]+$/, '');

// 받는 손을 한 번 돌려 (종료 값 · 세션 파일 · 까닭)으로 접는다 — 그 손의 경과 줄은 그대로 넘긴다. 내는 것: { code, file, said }
async function receive(args) {
  const ran = await runHand(args);
  if (ran.failed !== undefined) return { code: RECEIVED.TOOL, file: '', said: ran.failed };
  const lines = handLines(ran.code, ran.out);
  for (const line of lines.progress) say(line);
  return { code: ran.code ?? RECEIVED.TOOL, file: lines.file, said: handSaid(ran.err) };
}

const SAID_ECM_TAB = 'ECM 넘김을 화면 없이 못 따라갔다 — Edge 에 탭 하나를 잠깐 열어 넘긴다';

// 받고, ECM 만 못 받았으면 탭을 잠깐 여는 갈래로 한 번 더 받는다
async function receiveAll(args) {
  const got = await receive(args);
  if (got.code !== RECEIVED.ECM_HANDOFF) return got;
  say(SAID_ECM_TAB);
  return receive([...args, '--ecm-tab']);
}

// 로그인 시한까지 받기를 되풀이한다 — 로그인 탭이 넘어간 뒤에도 사내 앱의 세션이 서기까지 틈이 있다
async function receiveUntil(args, deadline) {
  for (;;) {
    const got = await receiveAll(args);
    if (got.code !== RECEIVED.NOT_LOGGED_IN || Date.now() + RETRY_MS > deadline) return got;
    await sleep(RETRY_MS);
  }
}

// ── 로그인 탭 ─────────────────────────────────────────────────────────────

// 탭 하나의 페이지 자리에 붙는다 — 브라우저 자리의 자동 붙기를 안 써서 다른 탭 · 팝업은 멈추지 않는다
async function attachPage(wsUrl) {
  const ws = new WebSocket(wsUrl);
  const waiting = new Map();
  const handlers = [];
  let id = 0;
  ws.onmessage = event => {
    const m = JSON.parse(event.data);
    if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); }
    else if (m.method) for (const h of handlers) h(m);
  };
  const opened = await new Promise(resolve => { ws.onopen = () => resolve(true); ws.onerror = () => resolve(false); });
  if (!opened) return null;
  const call = (method, params = {}) => new Promise(resolve => {
    const timer = setTimeout(() => resolve({ error: { message: `${method} 답이 없다` } }), CALL_MS);
    waiting.set(++id, m => { clearTimeout(timer); resolve(m); });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return { call, on: h => handlers.push(h), close: () => { try { ws.close(); } catch {} } };
}

// 빈 로그인 탭 — 로그인 주소는 붙은 뒤에 연다. 데스크톱 SSO 는 통합 인증이 입력 없이 넘어 「EP 접속 정보」 창을 화면이 서자마자 띄우고,
// 붙기 전에 떠 있던 창은 붙은 뒤의 Page.enable 이 다시 알리지 않아 받을 손이 없다. 띄운 창은 시작 주소의 빈 탭을, 떠 있던 Edge 는 새 빈
// 탭을 쓴다(앞쪽 탭 — 사람이 볼 자리다)
async function blankTab(port, launched) {
  if (launched) {
    const blank = (await tabList(port)).find(t => t.type === 'page' && t.webSocketDebuggerUrl && t.url === BLANK);
    if (blank) return blank;
  }
  return newTab(port, BLANK);
}

// 로그인 걸음이 끝난 뒤(세션을 받았거나 접었거나) 이 부름이 띄운 창에 남은 빈 탭을 닫는다 — 띄운 Edge 는 시작 주소의 빈 탭 말고도 제
// 시작 쪽 새 탭을 함께 열 수 있다(SOURCES 「잰 것」). 닫는 것은 빈 탭(about:blank)과 새 탭(edge://newtab)뿐이고, 로그인 탭(붙은 탭)과 그
// Edge 의 마지막 탭은 둔다 — 마지막 탭을 닫으면 창이 사라진다. 떠 있던 Edge 는 사람의 것이라 안 본다(이 부름이 만든 탭은 붙은 그 탭뿐이다).
// 한 번 훑고 끝내지 않는다 — Edge 는 제 새 탭을 늦게 열기도 해(바쁜 PC), 빈 탭이 두 번 잇달아 안 보일 때까지 BLANK_SETTLE_MS 안에서 다시 본다
// 내는 것: 닫은 탭의 수
async function closeOwnBlanks(port, tab) {
  let closed = 0, quiet = 0;
  const until = Date.now() + BLANK_SETTLE_MS;
  while (quiet < 2 && Date.now() < until) {
    const pages = (await tabList(port)).filter(t => t.type === 'page');
    const mine = pages.filter(t => (t.url === BLANK || t.url === NEW_TAB) && !(tab && t.id === tab.id));
    let left = pages.length, last = false;
    for (const t of mine) {
      if (left <= 1) { last = true; break; }         // 남은 것이 이 빈 탭 하나뿐이다 — 그것이 창을 쥔다
      if (await closeTarget(port, t.id)) { left--; closed++; }
    }
    if (last) break;
    quiet = mine.length ? 0 : quiet + 1;
    await sleep(POLL_MS);
  }
  return closed;
}

// 띄운 창에서 닫은 빈 탭을 알린다 — 닫은 것이 없으면 말이 없다
function sayClosedBlanks(closed) {
  if (closed > 0) say(`띄운 창에 남은 빈 탭 ${closed} 개를 닫았다`);
}

// 탭의 상태 — 닫힌 넷
const TAB = {
  PASSED: 'passed',        // 로그인 화면을 벗어나 http(s) 화면에 섰다 — 넘어갔다
  TYPING: 'typing',        // 로그인 화면의 입력 칸(암호 · 메일)에 머문다 — 통합 인증이 안 섰을 수 있다
  LOGIN: 'login',          // 로그인 화면이다(입력 칸은 안 보인다 — 넘어가는 중)
  UNKNOWN: 'unknown',      // 아직 모른다(주소가 없거나 빈 탭 · 브라우저 화면)
};

// 탭의 지금을 읽는다 — 주소 · 입력 칸이 있나 · 제목. 읽은 주소는 seen.url 에 남긴다(확인 창 귀가 창의 주소가 비었을 때 쓴다).
// 못 읽으면 앞서 본 주소(창이 넘어갈 때 귀가 남긴 것)로 낸다
async function readTab(page, seen) {
  const now = await page.call('Runtime.evaluate', {
    expression: '[location.href, !!document.querySelector("input[type=password],input[type=email]"), document.title]', returnByValue: true });
  const value = now.result && now.result.result && now.result.result.value;
  if (!Array.isArray(value)) return { url: seen.url, typing: false, title: '' };
  seen.url = value[0];
  return { url: value[0], typing: Boolean(value[1]), title: value[2] || '' };
}

// 탭의 상태를 한 번 셈한다
function tabState(now) {
  if (Boolean(now.url) && onLoginScreen(now.url, cfg)) return now.typing ? TAB.TYPING : TAB.LOGIN;
  return now.url && /^https?:/i.test(now.url) ? TAB.PASSED : TAB.UNKNOWN;
}

// 지켜보며 본 화면의 제목을 그 자리에서 배운다 — 로그인 화면의 제목은 아이디 · 비밀번호 칸이 선 화면에서만 배운다. SSO 가 지나는 중간 화면은
// 같은 호스트에 서면서 제목이 찰나마다 달라, 그것을 배우면 포털 제목과 겹치나를 가리는 눈이 거짓 위에 선다. 포털 제목은 넘어간 뒤 선 탭이
// 든다(learnPortalTitle). 읽을 때마다 부른다 — 이미 배운 제목이면 learnTitle 이 아무것도 안 한다
function learnSeenTitle(state, title) {
  if (state === TAB.TYPING && title) learnTitle(TITLE_OF.LOGIN, title);
}

// 통합 인증이 안 섰을 때의 걸음 — 닫힌 셋
const STALL = { WAIT: 'wait', LEAVE: 'leave', FALL_BACK: 'fall-back' };

// 통합 인증이 안 섰을 때 무엇을 하나 — 사람 없는 부름은 물러나고(칠 사람이 없다), 넘길 곳이 남았으면 한 번 넘기고, 아니면 기다린다
function stallStep(stuck, unattended, fellBack) {
  if (stuck && unattended) return STALL.LEAVE;
  return stuck && !fellBack ? STALL.FALL_BACK : STALL.WAIT;
}

// 넘어간 화면의 자리(호스트:포트) — 알림에 싣는다
const passedHost = url => new URL(url).host;

// 로그인 탭에서 확인 창을 받았나 — 닫힌 둘
const CONFIRM = { ACCEPTED: 'accepted', NONE: 'none' };

// 확인 창을 받았나 — CONFIRM.*
const confirmState = seen => seen.accepted ? CONFIRM.ACCEPTED : CONFIRM.NONE;

// 통합 인증이 안 섰나를 재는 시계 — 입력 칸 있는 로그인 화면에 cfg.fallbackMs 넘게 잇달아 머물면 참
function stallClock() {
  let since = 0;
  return state => {
    since = state === TAB.TYPING ? since || Date.now() : 0;
    return Boolean(since) && Date.now() - since > cfg.fallbackMs;
  };
}

// 탭이 넘어간 주소를 따라 seen.url 에 남긴다 — 바깥 틀의 넘어감만
function followUrl(page, seen) {
  page.on(m => { if (m.method === 'Page.frameNavigated' && !m.params.frame.parentId) seen.url = m.params.frame.url; });
}

// 확인 창 귀 — 로그인 화면의 「EP 접속 정보」 창(epConfirm)만 「확인」으로 받고 seen.accepted 를 센다. 다른 물음은 사람의 것이라 둔다
function acceptConfirms(page, seen) {
  page.on(m => {
    if (m.method === 'Page.javascriptDialogOpening' && epConfirm(m.params.type, m.params.message, m.params.url || seen.url, cfg)) {
      seen.accepted++;
      page.call('Page.handleJavaScriptDialog', { accept: true });
    }
  });
}

// 로그인 탭이 넘어갔다고 알린다 — 확인 창을 받았으면 그 값(다른 자리에서 연 메일의 세션이 끊긴다)도
const sayPassed = (host, confirmed) =>
  say(`로그인 탭이 넘어갔다 — ${host}${confirmed === CONFIRM.ACCEPTED ? ' · 「EP 접속 정보」 창을 「확인」으로 받았다(다른 자리에서 연 메일의 세션이 끊긴다)' : ''}`);
const SAID_NO_TAB = '로그인 탭에 못 붙었다 — 주소만 열고 받기를 되풀이한다. 「EP 접속 정보」 창이 뜨면 사람이 「확인」을 누른다';
const SAID_STALL_ALONE = '통합 인증이 안 섰다 — 사람이 없어 로그인 화면에서 기다리지 않는다';
const SAID_FALL_BACK = '통합 인증이 안 섰다 — 같은 탭을 평소 EP 로그인 화면으로 넘긴다. 사람이 그 창에서 평소 아이디로 로그인한다';

// 로그인 탭을 지켜본다 — 빈 탭에 붙어 창 알림을 켠 뒤 로그인 주소로 넘기고, 탭의 상태를 시한까지 본다. 넘어가면 끝, 통합 인증이 안 서면
// 평소 EP 로그인 화면으로 한 번 넘기고(사람 없는 부름은 넘기지 않고 떨어진다 — 칠 사람이 없다), 시한이 지나면 떨어진다.
// 지켜보는 동안 입력 칸이 선 로그인 화면의 제목을 그 자리에서 배운다(learnSeenTitle). 내는 것: { passed: 넘어갔나 }
async function watchLogin(port, tab, start, deadline, fallback, unattended, trace) {
  const page = await attachPage(tab.webSocketDebuggerUrl);
  if (!page) {
    say(SAID_NO_TAB);
    await newTab(port, start);
    return { passed: false };
  }
  const tracing = trace ? tracer(page) : null;
  try {
    const seen = { url: start, accepted: 0 };
    followUrl(page, seen);
    acceptConfirms(page, seen);
    await page.call('Page.enable');
    if (tracing) await tracing.start();
    await page.call('Page.navigate', { url: start });
    const stalled = stallClock();
    let fellBack = !fallback;
    while (Date.now() < deadline) {
      const now = await readTab(page, seen);
      const state = tabState(now);
      learnSeenTitle(state, now.title);
      if (state === TAB.PASSED) {
        sayPassed(passedHost(now.url), confirmState(seen));
        if (tracing) await tracing.after();
        return { passed: true };
      }
      const step = stallStep(stalled(state), unattended, fellBack);
      if (step === STALL.LEAVE) {
        say(SAID_STALL_ALONE);
        return { passed: false };
      }
      if (step === STALL.FALL_BACK) {
        fellBack = true;
        say(SAID_FALL_BACK);
        await page.call('Page.navigate', { url: fallback });
      }
      await sleep(POLL_MS);
    }
    return { passed: false };
  } finally {
    if (tracing) tracing.done();
    page.close();                                    // 탭 자리의 연결만 끊는다 — 탭과 창은 사람이 쓴다
  }
}

// ── 평소 Edge(포트 없음) ─────────────────────────────────────────────────
// 사람의 평소 Edge 에서 먼저 로그인한다 — 그 로그인만 이 PC 의 프로그램(파수 · ECM 에이전트) 로그인까지 한다(references/SOURCES.md
// 「잰 것」). 포트가 없어 탭에 못 붙으니, 주소는 사람이 여는 것처럼 Edge 에 넘겨 열고 물음 창은 윈도 UI 자동화로 본다

const many = x => [].concat(x || []);
// 물음 창의 꼴 — 입력 칸이 있으면 prompt, 단추 하나면 alert, 둘이면 confirm(CDP 의 Page.javascriptDialogOpening 이 주는 type 과 같은 말)
const dialogType = d => d.edit ? 'prompt' : d.buttons === 1 ? 'alert' : d.buttons === 2 ? 'confirm' : 'other';
// 물음 창 제목의 앞머리가 그 물음을 띄운 화면의 호스트다(「<호스트>의 메시지」 · 「<호스트> says」) — epConfirm 은 주소를 받는다
const dialogUrl = title => { const m = /^([a-z0-9.-]+(?::\d+)?)/i.exec(String(title || '')); return m ? `http://${m[1]}/` : ''; };

// 확인 창 하나를 누른 끝 — 닫힌 둘
const PRESS = { PRESSED: 'pressed', MISSED: 'missed' };

// 눈의 누름 답을 끝으로 가른다 — 그 창을 눌렀나(누른 단추) · 못 눌렀나(까닭)
const pressOutcome = (d, got) => got.pressed === d.i ? { state: PRESS.PRESSED, button: got.button || '확인' } : { state: PRESS.MISSED, why: got.why || '?' };

// 확인 창 하나를 누른 끝을 알린다
function sayPress(outcome) {
  if (outcome.state === PRESS.PRESSED) say(`평소 Edge 의 「EP 접속 정보」 창을 바깥에서(UI 자동화) 「${outcome.button}」으로 눌렀다`);
  else say(`평소 Edge 의 「EP 접속 정보」 창을 못 눌렀다 — ${outcome.why}. 다음 보기에서 다시 누른다`);
}

// 눈이 한 번 본 물음 창 가운데 받을 창(epConfirm)만 누른다 — 다른 물음은 사람의 것이라 둔다. 내는 것: 누른 수 · 눈이 죽었으면 -1
async function pressConfirms(eye, now) {
  let pressed = 0;
  for (const d of many(now.dialogs)) {
    if (!epConfirm(dialogType(d), d.message, dialogUrl(d.title), cfg)) continue;
    const got = await eye.press(d.i);
    if (!got) return -1;
    const outcome = pressOutcome(d, got);
    if (outcome.state === PRESS.PRESSED) pressed++;
    sayPress(outcome);
  }
  return pressed;
}

// 평소 Edge 에 로그인 주소를 연다 — 사람이 주소를 넘긴 것과 같다. 떠 있으면 그 Edge 의 새 탭, 없으면 평소 프로필로 뜬다. 포트는 안 연다.
// 늘 떼어 띄운다 — 떼지 않은 Edge 는 부른 쪽이 끝나면 함께 끝날 수 있다(SOURCES 「잰 것」)
function openOrdinary(exe, profile, url) {
  const args = profile ? [`--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check', url] : [url];
  spawn(exe, args, { detached: true, stdio: 'ignore' }).unref();
}

// 배우는 제목의 자리 — 제목 파일의 칸 이름이다
const TITLE_OF = { PORTAL: 'portal', LOGIN: 'login' };

// 배울 만한 제목 — 앞뒤 빈칸을 뗀 것. 비었거나 주소 꼴이면 ''(제목 없는 화면은 Edge 가 주소를 제목 자리에 둔다 — 그것은 안 배운다)
function cleanTitle(title) {
  const clean = String(title || '').trim();
  return !clean || /^[a-z]+:\/\//i.test(clean) || clean.includes('/') ? '' : clean;
}

// 제목 하나를 제목 파일에 남긴다 — 이미 그 제목이면 안 쓴다. 내는 것: { state: SAVED.*, why: 못 남긴 까닭 }
function storeTitle(which, clean) {
  const known = readTitles();
  if (known[which] === clean) return { state: SAVED.SAME };
  try {
    fs.mkdirSync(path.dirname(TITLES), { recursive: true });
    fs.writeFileSync(TITLES, JSON.stringify({ ...known, [which]: clean }));
    return { state: SAVED.WRITTEN };
  } catch (e) { return { state: SAVED.FAILED, why: e.code || e.message }; }
}

// 제목을 남긴 끝을 알린다 — 이미 배운 제목이면 말이 없다
function sayTitle(which, saved) {
  if (saved.state === SAVED.WRITTEN) say(`EP ${which === TITLE_OF.PORTAL ? '포털' : '로그인 화면'}의 탭 제목을 배웠다 — 다음 부름부터 평소 Edge 의 뒤쪽 탭도 그 제목으로 알아본다`);
  if (saved.state === SAVED.FAILED) say(`EP 탭 제목을 못 남겼다(${saved.why}) — 평소 Edge 는 앞 탭의 주소로만 본다`);
}

// 탭 제목 하나를 배운다 — 고르고 · 남기고 · 알린다
function learnTitle(which, title) {
  const clean = cleanTitle(title);
  if (clean) sayTitle(which, storeTitle(which, clean));
}

// 포트 창의 탭 가운데 EP 포털 주소의 탭에서 포털의 제목을 배운다 — 평소 Edge 의 포털 탭도 같은 화면이라 같은 제목이다. 다른 탭은 안 본다
async function learnPortalTitle(port) {
  if (!port) return;
  const pages = await tabList(port, VERSION_MS);    // 배우기는 곁일이다 — 못 읽으면 빈 목록, 받은 세션을 이 일로 접지 않는다
  const portal = pages.find(t => t.type === 'page' && hostOf(t.url) === hostOf(cfg.portal) && !onLoginScreen(t.url, cfg));
  if (portal) learnTitle(TITLE_OF.PORTAL, portal.title);
}

// 평소 Edge 의 걸음 한 판 — 눈을 먼저 세우고(PowerShell 이 뜨는 틈을 확인 창이 뜨기 앞에 치른다) 포털을 연 뒤, 틈(plan.ms)까지 받을 확인
// 창(epConfirm)만 누르거나(plan.press — 다른 물음은 사람의 것) 앞 탭이 EP 포털로 STEADY 번 잇달아 서는 것을 보고 곧 끝낸다(plan.watch).
// plan.committed 면 포털 주소만으로는 안 서고 그 탭에 화면이 섰다는 증거까지 든다(committedState).
// 눈이 안 서도(회사 정책이 스크립트를 막는 따위) 포털은 열고 기다림은 그대로 둔다 — 확인 창만 못 누른다. 로그인을 접지는 않는다.
// 내는 것: { confirmed: 포털이 섰나, eye: 눈이 한 일(stepEye), pressed: 누른 수, why: 눈이 안 섰으면 그 말 }
async function ordinaryStep(eye, exe, plan) {
  let seeing = Boolean(await eye.look());
  openOrdinary(exe, ordinaryProfile(), plan.url);
  const until = Date.now() + plan.ms;                // 틈은 포털을 연 때부터다 — 눈이 뜨는 틈이 그 틈을 먹으면 확인 창을 누를 틈이 없다
  let pressed = 0, steady = 0;
  while (Date.now() < until) {
    await sleep(EYE_GAP_MS);
    if (!seeing) continue;
    if (plan.press) {
      const got = await pressRound(eye);
      if (got < 0) { seeing = false; continue; }
      pressed += got;
    }
    if (plan.watch) {
      const seen = await lookOnce(eye);
      steady = (plan.committed ? committedState(seen.tabs) : seen.state) === LOOK.PORTAL ? steady + 1 : 0;
      if (steady >= STEADY) return { confirmed: true, eye: stepEye(true, pressed), pressed, why: '' };
    }
  }
  return { confirmed: false, eye: stepEye(seeing, pressed), pressed, why: seeing ? '' : eye.why() };
}

// 걸음 한 판에 눈이 한 일 — 닫힌 셋
const STEP_EYE = { BLIND: 'blind', PRESSED: 'pressed', UNSEEN: 'unseen' };

// 걸음 한 판에 눈이 한 일을 가른다 — 눈이 안 섰다 · 확인 창을 눌렀다 · 못 봤다
const stepEye = (seeing, pressed) => !seeing ? STEP_EYE.BLIND : pressed ? STEP_EYE.PRESSED : STEP_EYE.UNSEEN;

// 확인 창 한 번 — 눈이 지금 본 물음 창 가운데 받을 창만 누른다. 내는 것: 누른 수 · 눈이 죽었으면 -1
async function pressRound(eye) {
  const now = await eye.look();
  return now ? pressConfirms(eye, now) : -1;
}

const SAID_UNNEEDED = '포트 창의 메일 · 일정 세션이 살아 있고 문서함(ecm)은 안 받는 부름이다 — 평소 Edge 는 보지도 열지도 않는다';
const SAID_STOOD_BEFORE = '이 로그온에 평소 EP 로그인이 앞서 섰다 — 평소 Edge 는 다시 보지도 열지도 않는다';

// 「섰다」 기록을 못 남겼으면 알린다 — 문서함 손이 평소 Edge 를 다시 볼 수 있다
function sayStood(saved) {
  if (saved.state === SAVED.FAILED) say(`평소 EP 로그인이 섰다는 기록을 못 남겼다(${saved.why}) — 문서함 명령이 평소 Edge 를 다시 볼 수 있다`);
}

// 표를 못 남겼으면 알린다 — 다음 부름이 걸음을 한 번 더 한다
function sayMark(saved) {
  if (saved.state === SAVED.FAILED) say(`평소 Edge 로그인의 표를 못 남겼다(${saved.why}) — 다음 부름이 평소 Edge 의 걸음을 한 번 더 한다`);
}

// 평소 로그인의 상태 — 닫힌 열둘. 눈으로 보기 전(seen 없음)에는 앞의 다섯 가운데 하나를, 본 뒤에는 뒤의 일곱 가운데 하나를 낸다
const ORD = {
  SKIP: 'skip',            // 사람 없는 VDI — 칠 사람이 없어 보지도 열지도 않는다
  UNNEEDED: 'unneeded',    // 사람 있는 부름이 ecm 을 안 받고 포트 창의 세션이 산다 — 메일 · 일정 일이라 보지도 열지도 않는다(문서함 손이 그때 묻는다)
  ANSWERED: 'answered',    // 사용자가 오늘 평소 Edge 에서 이미 로그인했다고 답했다 — 사용자의 말이 눈 위에 선다(VDI 의 기다림이 지난 뒤의 답도)
  STOOD_BEFORE: 'stood-before',   // 이 로그온에 평소 로그인이 앞서 섰다(「섰다」 기록) — 탭이나 Edge 를 닫았어도 다시 보지도 열지도 않는다
  LOOK: 'look',            // 눈으로 봐야 가른다
  PORTAL: 'portal',        // 평소 Edge 에 EP 포털 탭이 있다 — 평소 로그인이 섰다
  ABSENT: 'absent',        // 평소 Edge 에 EP 포털 탭이 없다 — 포털을 열고 그 탭이 포털로 넘어가기를 본다
  DECIDED: 'decided',      // 못 읽었는데 이 로그온의 평소 로그인은 앞서 정해졌다(표)
  ASK: 'ask',              // 못 읽었고 정해지지 않았다 — 사람 있는 부름은 사용자에게 묻는다
  UNKEYED: 'unkeyed',      // 못 읽었고 로그온을 못 가린 VDI — 정한 틈 걸음을 건너뛴다(표 없이 4 로 끝내면 부를 때마다 같은 자리로 돌아온다)
  FIXED: 'fixed',          // 못 읽었고 사용자가 「아직」 이라 답했다 — 정한 틈의 걸음을 한다
  ALONE: 'alone',          // 못 읽었고 사람 없는 부름이라 물을 사람이 없다 — 정한 틈의 걸음을 한다
};

// 사람 없는 VDI 부름인가 — 칠 사람이 없어 평소 Edge 도 로그인 창도 안 연다
const aloneOnVdi = (vdi, opts) => Boolean(vdi && opts.unattended);

// 메일 · 일정만 쓰는 사람 있는 부름이 산 세션 위에 섰나 — 그 일에는 평소 로그인을 안 쓴다. 사람 없는 아침 부름(인자는 domino 다)은 빼고,
// 세션이 죽은 부름은 지금 차례(평소 Edge → 포트 창)대로 간다
const unneeded = (opts, got) => !opts.unattended && got.code === RECEIVED.OK && !opts.pass.includes('ecm');

// 평소 로그인의 상태를 받은 증거로 한 번 셈한다 — vdi 자리 · opts 부름의 선택 · got 첫 받기 · key 로그온 열쇠 · stood 「섰다」 기록 · seen 눈이 본
// 것(lookForPortal) · mark 「해 봤다」 표. 증거는 차례로 모인다 — key 가 없으면(undefined) 열쇠 없이 가를 수 있는 데까지만 가른다
function ordinaryState({ vdi, opts, got, key, stood, seen, mark }) {
  if (aloneOnVdi(vdi, opts)) return ORD.SKIP;
  if (opts.ordinary === ORDINARY_DONE) return ORD.ANSWERED;   // 사용자의 답은 기록으로 남긴다 — 메일 부름에 실려 와도
  if (unneeded(opts, got)) return ORD.UNNEEDED;
  if (key === undefined) return ORD.LOOK;
  if (key && stood === key) return ORD.STOOD_BEFORE;
  if (!seen) return ORD.LOOK;
  if (seen.state === LOOK.PORTAL) return ORD.PORTAL;
  if (seen.state === LOOK.ABSENT) return ORD.ABSENT;
  if (key && mark === key) return ORD.DECIDED;
  if (!opts.ordinary && !opts.unattended) return ORD.ASK;
  if (opts.unattended) return ORD.ALONE;
  return vdi && !key ? ORD.UNKEYED : ORD.FIXED;
}

// 포털을 여는 판의 갈래 — 닫힌 넷
const PLAN = {
  WATCH_VDI: 'watch-vdi',  // 없다 · VDI — 사용자가 치는 동안 포털이 서기를 본다
  WATCH: 'watch',          // 없다 · 데스크톱 — 확인 창을 누르며 포털이 서기를 본다
  PRESS: 'press',          // 못 읽는 자리의 데스크톱 — 정한 틈 동안 확인 창을 누른다
  OPEN_VDI: 'open-vdi',    // 못 읽는 자리의 VDI — 포털만 연다
};

// 포털을 열고 기다리는 판의 꼴 — 평소 로그인의 상태와 자리(VDI)로 정한다. kind 판의 갈래 · ms 기다릴 틈 · press 확인 창을 누르나 · watch 포털이
// 서기를 보나 · step 눈과 함께 걷나(아니면 포털만 연다) · committed 포털 주소에 더해 그 탭에 화면이 섰다는 증거를 드나. 데스크톱은 확인 창을
// 누르며 ordinaryMs 까지 — 붙은 창 로그인으로 메일 · 일정은 서야 한다. VDI 는 사람이 자판 앞에서 제 물음 창까지 누르니 누르지 않는다 — 없으면
// 사용자가 치는 동안 loginMs 까지 보고, 못 읽는 자리면 포털만 연다. VDI 만 증거를 드는 까닭 — VDI 는 포털 주소를 열어 막 연 탭도 주소창이
// 포털이고, 데스크톱은 로그인 화면 호스트를 열어 막 연 탭이 포털로 안 읽힌다
function portalPlan(state, vdi) {
  if (![ORD.ABSENT, ORD.FIXED, ORD.ALONE].includes(state)) return null;   // 여는 상태가 아니다 — 평소 Edge 는 안 연다
  const url = ordinaryUrl(vdi);
  if (state === ORD.ABSENT) return vdi ? { kind: PLAN.WATCH_VDI, url, ms: cfg.loginMs, press: false, watch: true, step: true, committed: true }
    : { kind: PLAN.WATCH, url, ms: cfg.ordinaryMs, press: true, watch: true, step: true };
  return vdi ? { kind: PLAN.OPEN_VDI, url, ms: 0, press: false, watch: false, step: false }
    : { kind: PLAN.PRESS, url, ms: cfg.ordinaryMs, press: true, watch: false, step: true };
}

// 평소 Edge 에 여는 주소 — 데스크톱은 로그인 탭이 데스크톱에서 여는 주소(회사 SSO — 통합 인증에 맡긴다)와 한 자리(loginUrls)에서, VDI 는
// EP 포털(사람이 거기서 친다). 평소 Edge 에는 포트가 없어 연 탭을 다른 주소로 넘기지 못한다 — 통합 인증이 안 서면 시한 뒤 알리고 잇는다
const ordinaryUrl = vdi => vdi ? cfg.portal : loginUrls(false).start;

// 포털을 열고 기다린 판의 끝 — 닫힌 다섯
const PORTAL_END = {
  STOOD: 'stood',              // 그 탭이 EP 포털로 넘어갔다 — 평소 로그인이 섰다
  LATE: 'late',                // 데스크톱 · 틈 안에 안 넘어갔다 — 알리고 포트 창으로 잇는다
  VDI_LATE: 'vdi-late',        // VDI · 사용자가 치는 동안 안 넘어갔다 — 4 로 사용자에게 묻는다. 표는 안 남긴다(사용자의 답이 다음 부름을 정한다)
  OPENED: 'opened',            // 못 읽는 자리의 데스크톱 · 정한 틈을 다 뒀다 — 넘었나는 못 본다
  VDI_OPENED: 'vdi-opened',    // 못 읽는 자리의 VDI · 포털만 열었다 — 4 로 사용자가 로그인한 뒤 다시 부르게 한다
};

// 그 끝이 이 로그온의 표를 남기나 — VDI 에서 사람의 로그인을 못 기다린 판만 안 남긴다(사용자의 답이 다음 부름을 정한다)
const endMarks = end => end !== PORTAL_END.VDI_LATE;

// 포털을 열고 기다린 판의 끝을 셈한다
function portalEnd(plan, step) {
  if (plan.kind === PLAN.OPEN_VDI) return PORTAL_END.VDI_OPENED;
  if (plan.kind === PLAN.PRESS) return PORTAL_END.OPENED;
  if (step.confirmed) return PORTAL_END.STOOD;
  return plan.kind === PLAN.WATCH_VDI ? PORTAL_END.VDI_LATE : PORTAL_END.LATE;
}

// 평소 Edge 에 포털을 열고 기다린다 — 걸음(또는 포털만 열기) · 그 끝을 알리고 표를 남긴 뒤, VDI 의 끝이면 4 로 멈춘다. 내는 것: true(열었다 —
// 부른 쪽이 세션을 다시 받는다)
async function untilPortal(eye, plan, key) {
  const exe = findEdge();
  if (!exe) throw new Exit(1, NO_EDGE);
  sayPortalOpen(plan);
  let step = null;
  if (plan.step) step = await ordinaryStep(eye, exe, plan);
  else openOrdinary(exe, ordinaryProfile(), plan.url);
  if (plan.press) sayStep(step);
  const end = portalEnd(plan, step);
  sayPortalEnd(end, plan);
  if (endMarks(end) && key) sayMark(writeMark(key));
  if (end === PORTAL_END.STOOD && key) sayStood(writeStood(key));
  if (end === PORTAL_END.VDI_LATE) throw new Exit(4, VDI_NOT_YET(plan.ms));
  if (end === PORTAL_END.VDI_OPENED) throw new Exit(4, VDI_ORDINARY);
  return true;
}

// 평소 Edge 의 걸음 — 사용자의 평소 Edge 를 보고 고른다(머리말 「차례」). 이 로그온의 표(ORDINARY_MARK)는 평소 Edge 를 못 읽는 자리에서 이 로그온의
// 평소 로그인이 정해졌다는 기록이다 — 정한 틈의 걸음을 했거나 사용자가 답했다. 내는 것: 평소 Edge 를 열었나(열었으면 부른 쪽이 세션을 다시
// 받는다 — 평소 로그인이 포트 창의 메일을 끊는다). 사람에게 물어야 하거나 VDI 에서 사람의 로그인을 못 기다렸으면 Exit(4)
async function ordinaryFirst(vdi, opts, got) {
  const before = ordinaryState({ vdi, opts, got });
  if (before === ORD.SKIP || before === ORD.UNNEEDED) {
    sayOrdinary(before);
    return false;
  }
  const key = logonKey();
  if (before === ORD.ANSWERED) {
    sayOrdinary(before);
    if (key) sayMark(writeMark(key));
    if (key) sayStood(writeStood(key));
    return false;
  }
  const stood = readStood();
  if (ordinaryState({ vdi, opts, got, key, stood }) === ORD.STOOD_BEFORE) {
    sayOrdinary(ORD.STOOD_BEFORE);
    return false;
  }
  const eye = edgeEye(eyeSelect());
  try {
    const seen = await lookForPortal(eye);
    const state = ordinaryState({ vdi, opts, got, key, stood, seen, mark: key ? readMark() : '' });
    sayOrdinary(state, seen);
    if (state === ORD.PORTAL && key) sayStood(writeStood(key));
    if (state === ORD.ASK) throw new Exit(4, ASK_PERSON);
    const plan = portalPlan(state, vdi);
    if (!plan) return false;
    return await untilPortal(eye, plan, key);                         // await — 안 기다리면 finally 가 눈을 먼저 닫는다
  } finally {
    eye.close();
  }
}

// ── 평소 Edge 의 말 ───────────────────────────────────────────────────────

// VDI 의 정한 틈 걸음이 끝내는 말 — 평소 Edge 를 못 읽는 자리에서 사용자가 「아직」 이라 했다. 사용자가 평소 Edge 에서 로그인한 뒤에 같은
// 명령을 다시 불러야 ep-login 창이 그 뒤에 로그인한다
const VDI_ORDINARY = 'VDI — 사용자의 평소 Edge 에 EP 포털을 열었다(포트 없이 — 사람이 연 것과 같다). 문서함의 DRM 문서는 평소 Edge 의 로그인이 ' +
  '먼저 있어야 열린다. 다음: 사용자에게 방금 열린 평소 Edge 의 EP 탭에서 평소 아이디로 로그인해 달라고 하고(「다른 PC에서 EP 접속 정보」 창이 뜨면 ' +
  '「확인」), 됐다고 하면 같은 명령을 다시 부른다 — 그때 세션이 안 서 있으면 EP 로그인용 Edge 창이 떠 거기서 한 번 더 로그인한다';
// 평소 Edge 를 못 읽었을 때 사람 있는 부름이 끝내는 말 — 사용자만 아는 것을 한 번 묻는다
const ASK_PERSON = '사용자의 평소 Edge 를 읽지 못해 평소 EP 로그인이 있는지 모르고, 아무것도 안 열었다(까닭은 위 줄). 다음: 사용자에게 한 번 묻는다 — ' +
  `「오늘 평소 쓰시는 Edge 에서 EP 에 이미 로그인하셨나요?」. 했다면 같은 명령에 ${ORDINARY_DONE} 를, 아직이면 ${ORDINARY_NOT_YET} 를 붙여 다시 부른다 ` +
  '(답은 이 윈도 로그온 동안 남아 다시 안 묻는다)';
// VDI 에서 평소 Edge 를 열고 기다린 시한이 지났을 때 끝내는 말
const VDI_NOT_YET = ms => `VDI — 사용자의 평소 Edge 에 EP 포털을 열고 ${Math.round(ms / 1000)}초 기다렸는데 그 탭이 EP 포털로 넘어가지 않았다. ` +
  `다음: 사용자에게 그 EP 탭에서 평소 아이디로 로그인을 마쳤는지 묻는다 — 마쳤다면 같은 명령에 ${ORDINARY_DONE} 를 붙여 다시 부르고, 아직이면 ` +
  '로그인한 뒤 그대로 다시 부른다';

// 평소 Edge 를 보는 눈이 안 선 까닭의 말
const eyeDown = why => `평소 Edge 를 보는 눈(${path.basename(EYE)} · 윈도 UI 자동화)이 안 선다 — ${why}`;

// 평소 Edge 를 못 읽은 까닭의 말 — 눈이 안 섰나(EYE_DOWN), 창의 탭 줄 · 주소창이 안 읽혔나(UNREAD)
const unreadWhy = seen => seen.state === LOOK.EYE_DOWN ? eyeDown(seen.eyeWhy)
  : `평소 Edge 창 ${seen.windows} 개 가운데 ${seen.unread} 개의 탭 줄 · 주소창이 안 읽힌다(창이 브라우저 칸을 UI 자동화에 안 내놓는다)`;

// 평소 로그인의 상태를 경과 줄로 알린다 — 그 상태에 이른 까닭부터
function sayOrdinary(state, seen) {
  if (state === ORD.SKIP) return;                    // 사람 없는 VDI — 알릴 사람이 없다
  if (state === ORD.UNNEEDED) return say(SAID_UNNEEDED);
  if (state === ORD.STOOD_BEFORE) return say(SAID_STOOD_BEFORE);
  if (state === ORD.ANSWERED) return say('사용자가 오늘 평소 Edge 에서 EP 에 이미 로그인했다고 답했다 — 평소 Edge 는 안 연다');
  if (state === ORD.PORTAL) return say('사용자의 평소 Edge 에 EP 포털 탭이 이미 있다 — 평소 EP 로그인이 서 있어 평소 Edge 는 안 연다');
  if (state === ORD.ABSENT) return say('사용자의 평소 Edge 에 EP 포털 탭이 없다(평소 Edge 가 안 떠 있거나, 떠 있는데 EP 탭이 없거나 로그인 화면에 있다)');
  say(`사용자의 평소 Edge 를 읽지 못했다 — ${unreadWhy(seen)}`);
  if (state === ORD.DECIDED) say('이 로그온의 평소 로그인은 앞서 정해졌다(평소 Edge 걸음을 했거나 사용자가 답했다) — 평소 Edge 는 안 연다');
  if (state === ORD.ALONE) say('사람 없는 부름이라 물을 사람이 없다 — 정한 틈의 평소 Edge 걸음을 한다');
  if (state === ORD.UNKEYED || state === ORD.FIXED) say('사용자가 아직이라고 답했다 — 평소 Edge 걸음부터 한다');
  if (state === ORD.UNKEYED) {
    say('이 윈도 로그온을 못 가려 평소 Edge 를 먼저 여는 걸음을 건너뛴다 — DRM 문서가 안 열리면 사용자가 평소 Edge 에서 EP 에 로그인한 뒤 이 명령을 다시 부른다');
  }
}

// 포털을 여는 판의 첫 줄 — 못 읽는 자리의 VDI 는 말 없이 연다(끝의 4 가 다음을 든다)
function sayPortalOpen(plan) {
  if (plan.kind === PLAN.WATCH_VDI) {
    say(`VDI — 사용자의 평소 Edge 에 EP 포털을 연다(포트 없이). 사용자가 거기서 평소 아이디로 로그인하면 이어 간다 — 그 탭이 EP 포털로 넘어가기를 최대 ${Math.round(plan.ms / 1000)}초 본다`);
  } else if (plan.kind === PLAN.WATCH) {
    say(`사용자의 평소 Edge 에 EP 포털을 연다(포트 없이 — 사람이 연 것과 같다) — 「EP 접속 정보」 창이 뜨면 누르며, 그 탭이 EP 포털로 넘어가기를 최대 ${plan.ms / 1000}초 본다`);
  } else if (plan.kind === PLAN.PRESS) {
    say(`사용자의 평소 Edge 에 EP 포털을 연다(포트 없이 — 사람이 연 것과 같다) — ${plan.ms / 1000}초 동안 「EP 접속 정보」 창이 뜨면 누른다`);
  }
}

// 평소 Edge 걸음의 눈이 한 일을 알린다
function sayStep(step) {
  if (step.eye === STEP_EYE.BLIND) say(`${eyeDown(step.why)}. 평소 Edge 에 EP 포털은 열었다 — 거기 「EP 접속 정보」 창이 떠 있으면 사용자가 누른다`);
  else say(`평소 Edge 에 EP 포털을 열었다 — 「EP 접속 정보」 창을 ${step.eye === STEP_EYE.PRESSED ? `눌렀다(${step.pressed}번)` : '못 봤다'}`);
}

// 포털을 열고 기다린 판의 끝을 알린다 — 4 로 끝나는 판의 말은 그 멈춤이 든다
function sayPortalEnd(end, plan) {
  if (end === PORTAL_END.STOOD) say(`평소 Edge 의 EP 탭이 EP 포털로 넘어갔다 — 평소 EP 로그인이 섰다. EP 로그인용 창으로 잇는다`);
  if (end === PORTAL_END.LATE) {
    say(`${plan.ms / 1000}초 안에 평소 Edge 의 EP 탭이 EP 포털로 넘어가지 않았다 — 평소 로그인이 안 넘었을 수 있다. EP 로그인용 창으로 이어 메일 · 일정은 ` +
      '세운다. DRM 문서가 안 열리면 사용자가 평소 Edge 에서 EP 에 로그인한 뒤 이 명령을 다시 부른다');
  }
}

// ── 기록(--trace) ────────────────────────────────────────────────────────

// 주소에서 호스트 · 경로와 칸 이름만 — 칸의 값(토큰일 수 있다)은 안 남긴다
function traceUrl(raw) {
  try {
    const u = new URL(raw);
    const keys = [...new Set(u.searchParams.keys())];
    return `${u.protocol}//${u.host}${u.pathname}${keys.length ? `?${keys.join('&')}` : ''}`.slice(0, TRACE_TEXT);
  } catch { return String(raw).split('?')[0].slice(0, TRACE_TEXT); }
}

// 이 PC 로 가는 주소(루프백)이거나, 브라우저 밖의 프로그램을 여는 주소(http · ws 가 아닌 스킴)인가
function towardThisPc(raw) {
  try {
    const u = new URL(raw);
    return /^(https?|wss?):$/i.test(u.protocol) ? LOOPBACK.test(u.hostname) : !BROWSER_SCHEMES.test(u.protocol);
  } catch { return false; }
}

// 기록하는 사건의 갈래 — 닫힌 여덟
const TRACE = { SENT: 'sent', ANSWER: 'answer', BLOCKED: 'blocked', SOCKET: 'socket', SOCKET_ANSWER: 'socket-answer', SOCKET_BLOCKED: 'socket-blocked',
  HANDOFF: 'handoff', ERROR: 'error' };

// 기록할 사건 하나를 가른다 — 이 PC 로 가는 요청 · 웹소켓과 그 답 · 막힘, 다른 프로그램을 여는 넘김, 화면의 오류 줄. 기록할 것이 아니면 null.
// seen 은 이 PC 로 간 요청 · 웹소켓의 id → 주소다(읽기만 한다 — 새로 볼 것은 track 으로 낸다). count 는 그 사건이 늘릴 수의 이름이다
function traceEvent(m, seen) {
  const p = m.params || {};
  if (m.method === 'Network.requestWillBeSent' && towardThisPc(p.request.url)) {
    return { kind: TRACE.SENT, track: [p.requestId, traceUrl(p.request.url)], count: 'sent', method: p.request.method, url: traceUrl(p.request.url), from: traceUrl(p.documentURL || '') };
  }
  if (m.method === 'Network.responseReceived' && seen.has(p.requestId)) return { kind: TRACE.ANSWER, status: p.response.status, url: seen.get(p.requestId) };
  if (m.method === 'Network.loadingFailed' && seen.has(p.requestId)) {
    return { kind: TRACE.BLOCKED, count: 'blocked', url: seen.get(p.requestId), why: `${p.errorText || ''}${p.blockedReason ? ` · ${p.blockedReason}` : ''}` +
      `${p.corsErrorStatus ? ` · ${p.corsErrorStatus.corsError}` : ''}` };
  }
  if (m.method === 'Network.webSocketCreated' && towardThisPc(p.url)) return { kind: TRACE.SOCKET, track: [p.requestId, traceUrl(p.url)], count: 'sockets', url: traceUrl(p.url) };
  if (m.method === 'Network.webSocketHandshakeResponseReceived' && seen.has(p.requestId)) return { kind: TRACE.SOCKET_ANSWER, status: p.response.status, url: seen.get(p.requestId) };
  if (m.method === 'Network.webSocketFrameError' && seen.has(p.requestId)) {
    return { kind: TRACE.SOCKET_BLOCKED, count: 'blocked', url: seen.get(p.requestId), why: String(p.errorMessage || '').slice(0, TRACE_TEXT) };
  }
  if (m.method === 'Page.frameRequestedNavigation' && towardThisPc(p.url)) return { kind: TRACE.HANDOFF, count: 'handoffs', url: traceUrl(p.url), why: p.reason || '' };
  if (m.method === 'Log.entryAdded' && p.entry && p.entry.level === 'error') {
    return { kind: TRACE.ERROR, count: 'errors', why: String(p.entry.text || '').replace(/\s+/g, ' ').slice(0, TRACE_TEXT) };
  }
  return null;
}

// 기록한 사건 하나를 「trace …」 줄로 알린다
function sayTrace(ev) {
  if (ev.kind === TRACE.SENT) say(`trace 요청 ${ev.method} ${ev.url} ← ${ev.from}`);
  if (ev.kind === TRACE.ANSWER) say(`trace 답 ${ev.status} ${ev.url}`);
  if (ev.kind === TRACE.BLOCKED) say(`trace 막힘 ${ev.url} — ${ev.why}`);
  if (ev.kind === TRACE.SOCKET) say(`trace 웹소켓 ${ev.url}`);
  if (ev.kind === TRACE.SOCKET_ANSWER) say(`trace 웹소켓 답 ${ev.status} ${ev.url}`);
  if (ev.kind === TRACE.SOCKET_BLOCKED) say(`trace 웹소켓 막힘 ${ev.url} — ${ev.why}`);
  if (ev.kind === TRACE.HANDOFF) say(`trace 넘김 ${ev.url} (${ev.why})`);
  if (ev.kind === TRACE.ERROR) say(`trace 화면 오류 ${ev.why}`);
}

// 기록을 맺는 줄
const sayTraceDone = count => say(`trace — 이 PC 로 간 요청 ${count.sent} · 웹소켓 ${count.sockets} · 막힌 것 ${count.blocked} · 이 PC · 다른 프로그램으로 가는 넘김 ` +
  `${count.handoffs} · 화면 오류 ${count.errors}. 탭 안의 다른 사이트 틀(따로 도는 프로세스)은 못 듣는다`);
const SAID_TRACE_AFTER = `trace — 넘어간 화면을 ${TRACE_AFTER_MS / 1000}초 더 듣는다`;

// 로그인 탭의 연결을 듣는다 — 사건마다 가르고(traceEvent) · 새 요청을 적고 · 세고 · 알린다(sayTrace)
function tracer(page) {
  const seen = new Map();
  const count = { sent: 0, sockets: 0, blocked: 0, handoffs: 0, errors: 0 };
  page.on(m => {
    const ev = traceEvent(m, seen);
    if (!ev) return;
    if (ev.track) seen.set(...ev.track);
    if (ev.count) count[ev.count]++;
    sayTrace(ev);
  });
  return {
    start: async () => { await page.call('Network.enable'); await page.call('Log.enable'); },
    // 넘어간 화면을 더 듣는다 — 넘어간 화면이 PC 의 프로그램에 붙는 것은 그 뒤다
    after: async () => { say(SAID_TRACE_AFTER); await sleep(TRACE_AFTER_MS); },
    done: () => sayTraceDone(count),
  };
}

// ── 띄우기 · 로그인 자리 ────────────────────────────────────────────────────

// 그 프로필의 Edge 창 하나를 포트와 빈 탭으로 띄운다(로그인 주소는 붙은 뒤에 연다 — blankTab). 내는 것: 띄운 프로세스의 pid.
// 동기화는 끈다(--disable-sync) — 새 프로필은 윈도 계정으로 저절로 로그인해 동기화를 묻는 작은 창을 따로 띄우고, 동기화된 확장이 안내 탭을
// 앞으로 내면 로그인 탭에 뜬 「EP 접속 정보」 창이 닫힌다(SOURCES 「잰 것」). 이 창은 로그인 자리라 사람의 즐겨찾기 · 확장을 안 들인다
function startEdge(exe, dir) {
  const args = [`--remote-debugging-port=${cfg.port}`, '--remote-debugging-address=127.0.0.1', `--user-data-dir=${dir}`,
    '--no-first-run', '--no-default-browser-check', '--disable-sync', BLANK];
  const child = spawn(exe, args, { detached: true, stdio: 'ignore', windowsHide: false });
  child.unref();
  return child.pid;
}

// 띄운 Edge 의 포트가 열리기를 PORT_MS 까지 본다 — 내는 것: 그 Edge 의 이름(Browser) · 안 열렸으면 ''
async function waitPort(port) {
  const deadline = Date.now() + PORT_MS;
  while (Date.now() < deadline) {
    await sleep(POLL_MS);
    const v = await version(port);
    if (v && v.Browser) return v.Browser;
  }
  return '';
}

const sayLaunched = (pid, dir) => say(`Edge 창을 띄웠다 — pid ${pid} · 프로필 ${dir}`);
const sayPortOpen = (port, browser) => say(`포트가 열렸다 — 127.0.0.1:${port} · ${browser}`);
const PORT_NOT_OPEN = (dir, port) => `띄웠는데 포트가 안 열린다 — 그 프로필(${dir})의 Edge 가 이미 포트 없이 떠 있거나, 포트 ${port} 를 다른 프로그램이 ` +
  '쓰거나, 회사 정책이 막는다. 다음: 멈추고 이 말을 사람에게 그대로 전한다';

// ep-login 프로필의 Edge 창 하나를 띄우고 포트가 열리기를 본다 — 내는 것: 열린 포트 · 못 열었으면 Exit(1)
async function launch(exe, profile) {
  const dir = path.resolve(profile);
  sayLaunched(startEdge(exe, dir), dir);
  const browser = await waitPort(cfg.port);
  if (!browser) throw new Exit(1, PORT_NOT_OPEN(dir, cfg.port));
  sayPortOpen(cfg.port, browser);
  return cfg.port;
}

// 로그인 탭을 여는 까닭 — 닫힌 둘
const TAB_WHY = { LOST: 'lost', TRACE: 'trace' };

// 사람의 로그인을 돌려준다(--give-back) — 평소 걸음 하나만 하고 끝낸다. 포털 탭이 있든 「섰다」 기록이 있든 평소 Edge 에 로그인을 열고, 포트
// 창은 안 건드리고 다시 받지도 않는다(그 로그인이 포트 창의 메일 · 일정 세션을 끊는다 — 사람이 쓰려는 것이다). 포털이 섰나는 보지 않는다 —
// 사람이 쓰던 죽은 포털 탭도 포털로 읽혀 새 로그인을 못 가린다. 데스크톱은 정한 틈 동안 확인 창을 누르고(PRESS), VDI 는 열고 끝낸다(사람이
// 거기서 친다). 사람 없는 부름은 거절한다. 내는 것: 0
async function giveBack(vdi, opts) {
  if (opts.unattended) throw new Exit(1, GIVE_BACK_ALONE);
  const plan = portalPlan(ORD.FIXED, vdi);
  if (vdi) return openOnly(plan);
  const key = logonKey();
  const eye = edgeEye(eyeSelect());
  try {
    await untilPortal(eye, plan, key);
  } finally {
    eye.close();
  }
  say(SAID_GIVEN_BACK);
  return 0;
}

// VDI 에서 돌려주는 걸음 — 평소 Edge 에 EP 포털만 연다(사람이 거기서 친다). 내는 것: 0
function openOnly(plan) {
  const exe = findEdge();
  if (!exe) throw new Exit(1, NO_EDGE);
  openOrdinary(exe, ordinaryProfile(), plan.url);
  say(SAID_GIVEN_BACK);
  return 0;
}

const GIVE_BACK_ALONE = `${GIVE_BACK} 는 사람 있는 부름만 받는다 — 사람의 로그인을 돌려주는 일은 사람이 그 자리에서 한다`;
const SAID_GIVEN_BACK = '사람의 평소 Edge 에 EP 로그인을 열었다 — 그 로그인이 서면 평소 Edge 의 EP 포털에서 앱(ERP · MES 따위)을 다시 띄울 수 ' +
  '있고, AI 쪽(포트 창)의 메일 · 일정 세션은 끊긴다(다음 회사 일이 입구를 부르면 포트 창이 다시 로그인한다). 서지 않았으면 사람이 그 탭에서 로그인한다';

// 로그인 자리를 고른다 — 포트를 연 Edge 가 있으면(로그인이 끊겼거나 기록하는 부름) 그 Edge 의 새 빈 탭, 붙을 Edge 가 없으면 ep-login 프로필의
// 창 하나를 띄워 그 시작 탭. 사람의 평소 Edge 는 떠 있어도 안 건드린다. 내는 것: { port, tab(못 열었으면 null), launched }
async function loginPlace(got, opts) {
  const lost = got.code === RECEIVED.NOT_LOGGED_IN;
  const open = lost || opts.trace ? await openPort(cfg) : null;
  if (lost && !open) throw new Exit(1, NO_OPEN_PORT);
  if (open) {
    sayLoginTab(open, lost ? TAB_WHY.LOST : TAB_WHY.TRACE);
    return { port: open, tab: await blankTab(open, false), launched: false };
  }
  const exe = findEdge();
  if (!exe) throw new Exit(1, NO_EDGE);
  const port = await launch(exe, opts.profile);
  return { port, tab: await blankTab(port, true), launched: true };
}

const NO_EDGE = 'Edge 를 못 찾았다';
const NO_OPEN_PORT = '받는 손은 붙었다는데 포트를 연 Edge 를 못 찾았다';
const SAID_WATCH_VDI = '그 창에서 사람이 평소 아이디로 로그인한다 — 이쪽은 로그인이 끝나기를 기다린다';
const SAID_WATCH = '로그인 탭을 지켜본다 — 통합 인증이면 입력 없이 넘는다';
const SAID_NO_LOGIN_TAB = '로그인 탭을 못 열었다 — 받기만 되풀이한다';

// 포트 창에 로그인 탭을 연다고 알린다 — TAB_WHY.LOST 로그인이 끊겼다 · TRACE 기록하는 부름이다
const sayLoginTab = (port, why) => say(`Edge(127.0.0.1:${port})에 ${why === TAB_WHY.LOST ? '로그인이 안 됐다 — ' : ''}로그인 탭을 연다`);

// 로그인 시한 — 사람 없는 부름은 통합 인증이 설 만큼만 기다린다
const loginDeadline = opts => Date.now() + (opts.unattended ? Math.min(cfg.loginMs, UNATTENDED_MS) : cfg.loginMs);

// 고른 자리의 로그인 탭을 지켜본다 — VDI 는 사람이 치는 것을, 데스크톱은 통합 인증이 넘는 것을. 내는 것: watchLogin 의 답
async function watchPlace(place, vdi, deadline, opts) {
  say(vdi ? SAID_WATCH_VDI : SAID_WATCH);
  if (!place.tab) {
    say(SAID_NO_LOGIN_TAB);
    return { passed: false };
  }
  const urls = loginUrls(vdi);
  return watchLogin(place.port, place.tab, urls.start, deadline, urls.fallback, opts.unattended, opts.trace);
}

// 로그인 탭이 여는 주소와 통합 인증이 안 설 때 넘길 주소 — VDI 는 처음부터 평소 EP 로그인 화면이라 넘길 곳이 없다
const loginUrls = vdi => vdi ? { start: cfg.epLogin, fallback: '' } : { start: cfg.companyLogin, fallback: cfg.epLogin };

// 로그인 뒤 다시 받기의 시한 — 사람 없는 부름은 안 넘어간 로그인을 시한까지 기다리지 않는다(한 번 받아 보고 끝낸다)
const receiveDeadline = (opts, watched, deadline) => opts.unattended && !watched.passed ? Date.now() : deadline;

// 로그인 걸음의 뒤치레 — 띄운 창의 빈 탭을 닫고, 포트 창의 포털 제목을 배운다
async function tidyUp(place) {
  if (place.launched) sayClosedBlanks(await closeOwnBlanks(place.port, place.tab));
  await learnPortalTitle(place.port);
}

// ── 갈래 ─────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const opts = { pass: [], profile: PROFILE_DIR };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--profile') { opts.profile = argv[++i] || ''; if (!opts.profile) throw new Exit(1, '--profile 뒤에 폴더를 준다'); }
    else if (argv[i] === UNATTENDED) opts.unattended = true;
    else if (argv[i] === '--trace') opts.trace = true;
    else if (argv[i] === GIVE_BACK) opts.giveBack = true;
    else if (argv[i] === ORDINARY_DONE || argv[i] === ORDINARY_NOT_YET) {
      if (opts.ordinary && opts.ordinary !== argv[i]) throw new Exit(1, `${ORDINARY_DONE} 와 ${ORDINARY_NOT_YET} 는 하나만 준다`);
      opts.ordinary = argv[i];
    }
    else if (argv[i].startsWith('--')) throw new Exit(1, `모르는 선택: ${argv[i]}`);
    else opts.pass.push(argv[i]);                    // 세션 파일 · domino · ecm — 받는 손이 가린다
  }
  return opts;
}

// 세션을 세운다 — 받기 → 평소 로그인 → (섰으면 끝) → 로그인 자리 → 지켜보기 → 다시 받기 → 뒤치레 → 끝
async function main(argv) {
  needNode();
  const opts = parseArgs(argv);
  const vdi = onVdi();
  if (opts.giveBack) return giveBack(vdi, opts);
  let got = await receiveAll(opts.pass);
  // 평소 Edge 의 로그인이 먼저다 — 포트 창의 세션이 살았든 아니든 평소 Edge 를 보고 고른다(그 로그인만 이 PC 의 프로그램 로그인까지 한다).
  // 받는 손이 스스로 멈춘 부름(인자 따위)은 열 일이 아니다. 걸음 뒤에는 다시 받는다 — 평소 로그인이 포트 창의 메일을 끊는다
  if (!handStopped(got) && await ordinaryFirst(vdi, opts, got)) got = await receiveAll(opts.pass);
  if (settled(got, opts)) return finish(got, opts);
  if (aloneOnVdi(vdi, opts)) throw new Exit(4, UNATTENDED_VDI);
  const deadline = loginDeadline(opts);
  const place = await loginPlace(got, opts);
  const watched = await watchPlace(place, vdi, deadline, opts);
  got = await receiveUntil(opts.pass, receiveDeadline(opts, watched, deadline));
  await tidyUp(place);
  return finish(got, opts);
}

function done(got) { console.log(got.file); return 0; }

// 로그인 걸음 없이 이 명령의 끝이 섰나 — 섰다 · 받는 손이 멈췄다 · ECM 만 못 받았다. 로그인이 안 됐다 · Edge 가 없다는 다음 걸음이 있다.
// 기록하는 부름은 세션이 살아 있어도 로그인 탭을 연다 — 볼 것은 로그인 화면과 넘어간 화면이 이 PC 에 무엇을 보내나다
const settled = (got, opts) => (got.code === RECEIVED.OK || handStopped(got) || got.code === RECEIVED.ECM_HANDOFF) && !(opts.trace && got.code === RECEIVED.OK);

// 받는 손이 스스로 멈췄나(인자 · 설정 · 도구) — 열 일이 아니다
const handStopped = got => got.code === RECEIVED.TOOL;

const UNATTENDED_VDI = 'VDI 는 사람이 아이디를 쳐야 한다 — 사람 없는 부름은 로그인 창을 띄우지 않는다. 다음: 사람이 대화에서 EP 로그인을 한다';
const UNATTENDED_NOT_STOOD = '통합 인증으로 세션이 안 섰다 — 사람이 없어 더 기다리지 않았다. 다음: 사람이 그 Edge 창이나 대화에서 EP 로그인을 한다';
const NOT_STOOD = got => `로그인 시한(${Math.round(cfg.loginMs / 1000)}초) 안에 세션이 안 섰다${got.said ? ` — ${got.said}` : ''}. ` +
  '다음: 사람에게 그 Edge 창에서 EP 로그인을 마쳐 달라고 하고, 됐다고 하면 같은 명령을 다시 부른다(이번엔 받기만 하고 끝난다)';

// 끝난 받기를 이 명령의 종료로 바꾼다 — 0 · ECM 만 못 받았으면 4 · 로그인이 끝내 안 섰으면 4 · 그 밖은 1
function finish(got, opts) {
  if (got.code === RECEIVED.OK) return done(got);
  if (got.code === RECEIVED.ECM_HANDOFF) return ecmFailed(got);
  if (got.code === RECEIVED.NOT_LOGGED_IN) throw new Exit(4, opts.unattended ? UNATTENDED_NOT_STOOD : NOT_STOOD(got));
  throw new Exit(1, HAND_STOPPED(got));
}

// 받는 손이 스스로 멈춘 까닭 — 그 손의 말이 없으면 종료 값으로
const HAND_STOPPED = got => got.said || `받는 손이 ${got.code} 로 멈췄다`;

function ecmFailed(got) {
  throw new Exit(4, ECM_FAILED(got));
}

// ECM 을 탭으로도 못 받은 끝의 말
const ECM_FAILED = got => `EP 로그인은 섰는데 ECM 세션을 탭으로도 못 받았다${got.said ? ` — ${got.said}` : ''}. 다음: 멈추고 이 말을 사람에게 그대로 전한다 — 다시 로그인할 일이 아니다`;

// 명령 한 번 — main 의 종료 값으로 프로세스를 끝낸다
function run(argv) {
  main(argv).then(code => process.exit(code), error => {
    console.error(error.message);
    process.exit(error instanceof Exit ? error.code : 1);
  });
}

if (require.main === module) run(process.argv.slice(2));
