// 사내 세션을 세우는 대화의 입구 — 스킬 ep-login 이 부르는 하나뿐인 명령. 쓰는 사람의 Edge 에서 세션을 받아 보고(받는 손
// edge_session.js), 안 서면 그 Edge 의 상태에 맞는 로그인을 띄워 지켜본 뒤 다시 받는다. 띄운 창 · 연 탭은 사람이 그대로 쓴다.
//
// 부르는 꼴:
//     node ep_login.js [세션 파일] [domino] [ecm] [--profile <폴더>] [--unattended] [--ordinary-done | --ordinary-not-yet] [--trace]
//   세션 파일 · domino · ecm — 받는 손에 그대로 넘긴다(뜻은 그 머리말). 받는 손이 ECM 넘김만 화면 없이 못 따라가면(그 손의 4) 탭을
//     잠깐 여는 갈래(--ecm-tab)로 한 번 더 받는다 — 그 탭을 띄우기 전 알림에 함께 싣는다.
//   --profile — 띄우는 창의 프로필 폴더. 안 주면 PROFILE_DIR(LOCALAPPDATA 아래)이다.
//   --unattended — 사람이 없는 부름(예약 실행). 입력 없이 넘는 통합 인증으로만 세운다 — 사람이 쳐야 하는 자리(VDI · 통합 인증이 안
//     선 로그인 화면)에서는 띄우거나 기다리지 않고 4 로 끝난다. 띄운 창은 그대로 둔다(사람이 와서 쓴다).
//   --ordinary-done · --ordinary-not-yet — 평소 Edge 를 못 읽어 4 로 물은 뒤, 사용자의 답(오늘 평소 Edge 에서 EP 에 이미 로그인했다 ·
//     아직이다)을 싣고 다시 부르는 꼴. 답은 이 윈도 로그온의 표(ORDINARY_MARK)로 남아 그 로그온에는 다시 안 묻는다.
//   --trace — 로그인 탭이 이 PC 의 프로그램(파수 · ECM 에이전트)에 무엇을 보내고 무엇이 막히나를 「trace …」 줄로 남긴다. 세션이
//     살아 있어도 로그인 탭을 열어 로그인 화면과 넘어간 화면을 지켜본다. 주소는 호스트 · 경로와 칸 이름까지만 남긴다(값은 없다).
//   환경변수 EDGE_DEBUG_PORT 포트 · SESSION_LOGIN_HOSTS 로그인 화면 호스트 · SESSION_LOGIN_WAIT_SECONDS 로그인 시한 — 뜻과 기본값은
//   받는 손의 settings 한 자리에서 읽는다. 로그인 화면과 받을 확인 창도 그 손의 onLoginScreen · epConfirm 이 가린다. EP_LOGIN_URL ·
//   COMPANY_LOGIN_URL 은 로그인 탭의 주소를 바꾼다 — 가짜 SSO 로 재는 검사(설정 저장소 _check/skills/ep-login/check_session.js)를 위해 있다.
//
//   EP_PORTAL_URL 은 평소 Edge 에 여는 EP 포털 주소를, EP_ORDINARY_PROFILE 은 평소 Edge 대신 볼 프로필 폴더를 바꾼다 — 같은 검사가 가짜
//   포털과 사람의 Edge 대신 버리는 프로필을 보게 한다. EP_LOGON_KEY 는 이 윈도 로그온의 열쇠(logonKey)를 그 값으로 둔다 — 같은 검사가
//   로그온마다의 차례를 탐색기가 없는 자리(CI 러너)에서도 같은 열쇠로 잰다.
//
// 차례:
//   먼저 — 사용자의 평소 Edge(포트 없음)에 EP 포털 탭이 있나를 윈도 UI 자동화(ordinary_edge.ps1)로 본다 — 창마다 앞 탭의 주소(EP_PORTAL 의
//     호스트인가 · 로그인 화면 호스트인가)와, 이 PC 에서 배운 포털의 탭 제목(TITLES)을 든 뒤쪽 탭. 평소 EP 로그인만 이 PC 의 프로그램(파수 · ECM
//     에이전트) 로그인까지 하고, 그 로그인이 서면 그 탭은 포털에 선다. 사람 없는 부름은 VDI 에서 보지도 열지도 않는다.
//     있다(STEADY 번 잇달아) → 평소 Edge 는 안 건드린다.
//     없다(평소 Edge 가 안 떠 있거나, 읽혔는데 포털 탭이 없다) → EP 포털을 포트 없이 사람처럼 열고 그 탭이 EP 포털로 넘어가기를 본 뒤 잇는다 —
//       데스크톱은 그동안 「EP 접속 정보」 창을 누르며 SESSION_ORDINARY_SECONDS 까지(지나도 알리고 잇는다), VDI 는 사용자가 거기서 치는 동안
//       SESSION_LOGIN_WAIT_SECONDS 까지(지나면 4 로 사용자에게 묻게 한다). 사람이 로그인해 두고 탭만 닫았으면 포털이 곧 서 곧 잇는다.
//     못 읽었다(탭 줄 · 주소창이 안 보인다 · 눈이 안 선다) → 표가 있으면 안 연다. 없으면 사람 있는 부름은 아무것도 안 열고 4 로 사용자에게
//       묻게 하고(답은 --ordinary-done · --ordinary-not-yet), 「아직」 이거나 사람 없는 부름이면 정한 틈의 걸음을 한다 — 데스크톱은
//       SESSION_ORDINARY_SECONDS 동안 확인 창을 누르고 잇고, VDI 는 포털만 열고 4 로 끝내 사용자가 로그인한 뒤 다시 부르게 한다.
//     어느 갈래든 평소 Edge 에는 포트를 열지 않고, 끝내지도 쿠키를 읽지도 않는다. 사람의 다른 탭의 주소 · 제목은 눈 밖으로 안 나온다.
//   포털 · 로그인 화면의 탭 제목은 포트 창에서 배운다 — 로그인 탭이 지나는 화면의 제목과, 포트 창의 포털 주소 탭의 제목(같은 화면이라 같은 제목이다).
//   그 뒤 받는 손의 종료 값(상태)으로 가른다:
//   받는다 → 0 이면 끝
//   3 붙었는데 로그인이 안 됐다 → 그 Edge 에 로그인 탭 하나를 열어 지켜본 뒤 다시 받는다
//   2 붙을 Edge 가 없다 → ep-login 프로필의 Edge 창 하나를 포트와 로그인 탭으로 띄워 지켜본 뒤 다시 받는다. 사람의 평소 Edge 는
//     떠 있든 아니든 안 끝낸다 — 끝내면 사람의 창 · 탭 · 쓰던 글이 다 닫힌다
//   4 ECM 만 못 받았다 → --ecm-tab 으로 한 번 더 받는다
// 로그인 탭을 지켜보는 법 · 왜 따로 사는 프로필로 띄우나 · 왜 평소 Edge 가 먼저인가는 references/DESIGN.md 가 든다.
//
// 내는 것 — 종료 값은 닫힌 셋이다. 표준 출력은 종료 0 일 때 세션 파일의 절대 경로 한 줄뿐이고, 경과와 「다음: …」 은 표준 오류다.
// 표준 오류의 끝은 종료 4 · 1 이면 그 까닭 · 회사 일 앞에 거는 한 줄(BEFORE_WORK · 사람 없는 부름은 안 낸다)의 차례다:
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
const { spawn, execFileSync } = require('child_process');

// 사내 SSO 의 회사 로그인 — ADFS 로 넘어가 데스크톱은 통합 인증으로 입력 없이 서지만, VDI 에서는 처음 보는 ADFS 창이 전체 메일 주소를 받는다
const COMPANY_LOGIN = 'http://swpsso.posco.net/idms/U61/jsp/login/saml_login.jsp?companyCode=shared';
// EP 포털 — 사람이 평소 Edge 에서 여는 주소. 로그인 전이면 아래 평소 EP 로그인 화면으로 보내고, 로그인하면 포털로 돌아온다
const EP_PORTAL = 'http://swp.posco.net/';
// 평소 EP 로그인 — EP 포털(swp.posco.net)이 보내는 화면(VDI 꼴의 아이디 · 비밀번호 칸). 통합 인증이 안 서는 자리에서 사람이 여기서 친다
const EP_LOGIN = 'http://swpsso.posco.net/idms/U61/jsp/login/login.jsp';
// VMware Horizon VDI 인가 — 에이전트가 세션에 심는 브로커 값 · VDI 도메인
const onVdi = () => Boolean((process.env.ViewClient_Broker_DNS_Name || '').trim()) || /\.VDI$/i.test(process.env.USERDNSDOMAIN || '');
// 띄우는 창의 프로필 — 사람의 평소 Edge 와 따로 산다. 로그인 쿠키가 여기 남아, 창을 닫았다 다시 띄워도 세션이 살아 있으면 로그인 없이 받는다
const PROFILE_DIR = path.join(process.env.LOCALAPPDATA || '', 'ep-login', 'edge-profile');
// 이 윈도 로그온에 평소 Edge 의 걸음을 했다는 표 — 로그온 열쇠(logonKey) 한 줄. 비영속 VDI 는 로그오프 때 함께 사라진다
const ORDINARY_MARK = path.join(process.env.LOCALAPPDATA || '', 'ep-login', 'ordinary-logon');
const FIND_MS = 5000;                 // 로그온 열쇠를 묻는 PowerShell 한 번의 시한
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
const CANDIDATES = [                  // Edge 가 깔리는 자리 — 시스템 설치(32 · 64 비트)가 먼저, 사용자 설치가 끝
  [process.env['ProgramFiles(x86)'], 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.ProgramFiles, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.LOCALAPPDATA, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
];
const HAND = path.join(__dirname, 'edge_session.js');
const EYE = path.join(__dirname, 'ordinary_edge.ps1');   // 평소 Edge 를 보는 눈 — 포트가 없어 윈도 UI 자동화로 본다
const EYE_MS = 15000;                 // 눈의 답 하나의 시한 — 한 번 보기는 1초 안쪽이고, 넘으면 눈이 멈춘 것이다
const EYE_GAP_MS = 300;               // 평소 Edge 의 물음 창을 다시 보는 사이
const LOOK_TRIES = 3;                 // 평소 Edge 의 탭을 못 읽었을 때 다시 읽는 수 — 물음 창이 잠깐 떠 탭 줄을 가린 판을 넘긴다
const LOOK_GAP_MS = 700;              // 그 다시 읽는 사이
const STEADY = 3;                     // 「EP 포털 탭이 있다」를 믿기까지 잇달아 같아야 하는 읽기 수 — 한 번 본 것은 넘어가는 중일 수 있다
// 이 PC 에서 배운 EP 화면의 탭 제목 — 포털과 로그인 화면 둘만 둔다(사람의 다른 탭은 안 둔다). 앞에 안 선 탭은 주소가 안 보여 제목으로 알아본다
const TITLES = path.join(process.env.LOCALAPPDATA || '', 'ep-login', 'ep-titles.json');
const ORDINARY_DONE = '--ordinary-done', ORDINARY_NOT_YET = '--ordinary-not-yet';
const BLANK = 'about:blank';          // 로그인 탭이 붙기 전에 서는 자리 — 로그인 주소는 붙은 뒤에 연다(blankTab)
const NEW_TAB = 'edge://newtab/';     // 띄운 Edge 가 제 시작 쪽으로 함께 여는 새 탭 — 로그인 뒤 남은 빈 탭으로 닫는다(closeOwnBlanks)

// 포트 · 로그인 화면 호스트 · 로그인 시한 · 로그인 화면과 받을 창의 가림 · 받는 손의 종료 값(RECEIVED)은 받는 손이 든다 — 두 손이
// 같은 자로 가린다. 평소 Edge 의 물음 창도 같은 자(epConfirm)로 가린다
const { settings, onLoginScreen, epConfirm, debugPorts, Exit, EXIT: RECEIVED, VERSION_MS } = require('./edge_session.js');
const cfg = settings();
const env = (name, fallback) => (process.env[name] || '').trim() || fallback;
const say = line => console.error(line);
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── Edge ─────────────────────────────────────────────────────────────────

async function version(port) {
  return fetch(`http://127.0.0.1:${port}/json/version`, { signal: AbortSignal.timeout(VERSION_MS) })
    .then(r => r.json()).catch(() => null);
}

function findEdge() {
  for (const parts of CANDIDATES) {
    if (!parts[0]) continue;
    const exe = path.join(...parts);
    if (fs.existsSync(exe)) return exe;
  }
  return '';
}

// 포트를 연 Edge 가운데 받는 손이 먼저 붙는 것 — 그 손과 같은 차례(debugPorts)로 처음 답하는 포트
async function openPort() {
  for (const port of cfg.ports || debugPorts(cfg)) if (await version(port)) return port;
  return null;
}

// ── 받기 ─────────────────────────────────────────────────────────────────

// 받는 손을 한 번 돌린다. 내는 것: { code, file, said } — file 은 종료 0 의 끝 줄, said 는 그 손의 「다음」 을 뺀 말
function receive(args) {
  return new Promise(resolve => {
    const child = spawn(process.execPath, [HAND, ...args], { windowsHide: true });
    let out = '', err = '';
    child.stdout.on('data', d => out += d);
    child.stderr.on('data', d => err += d);
    child.on('error', e => resolve({ code: RECEIVED.TOOL, file: '', said: e.message }));
    child.on('close', code => {
      const lines = out.split(/\r?\n/).filter(Boolean);
      const file = code === RECEIVED.OK && lines.length ? lines.pop() : '';
      // 경과는 넘기되 받는 손의 「다음」 과 남은 파일의 경로 줄은 안 넘긴다 — 다음 걸음은 이 명령이 고른다
      for (const line of lines) if (!path.isAbsolute(line)) say(line);
      const said = err.split(/\r?\n/).filter(line => line && !/^다음:/.test(line)).join(' ').replace(/\s*다음:.*$/, '').replace(/[.\s]+$/, '');
      resolve({ code: code ?? RECEIVED.TOOL, file, said });
    });
  });
}

// 받고, ECM 만 못 받았으면 탭을 잠깐 여는 갈래로 한 번 더 받는다
async function receiveAll(args) {
  const got = await receive(args);
  if (got.code !== RECEIVED.ECM_HANDOFF) return got;
  say('ECM 넘김을 화면 없이 못 따라갔다 — Edge 에 탭 하나를 잠깐 열어 넘긴다');
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
    const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then(r => r.json()).catch(() => []);
    const blank = targets.find(t => t.type === 'page' && t.webSocketDebuggerUrl && t.url === BLANK);
    if (blank) return blank;
  }
  return fetch(`http://127.0.0.1:${port}/json/new?${BLANK}`, { method: 'PUT' }).then(r => r.json()).catch(() => null);
}

// 로그인 걸음이 끝난 뒤(세션을 받았거나 접었거나) 이 부름이 띄운 창에 남은 빈 탭을 닫는다 — 띄운 Edge 는 시작 주소의 빈 탭 말고도 제
// 시작 쪽 새 탭을 함께 열 수 있다(SOURCES 「잰 것」). 닫는 것은 빈 탭(about:blank)과 새 탭(edge://newtab)뿐이고, 로그인 탭(붙은 탭)과 그
// Edge 의 마지막 탭은 둔다 — 마지막 탭을 닫으면 창이 사라진다. 떠 있던 Edge 는 사람의 것이라 안 본다(이 부름이 만든 탭은 붙은 그 탭뿐이다).
// 한 번 훑고 끝내지 않는다 — Edge 는 제 새 탭을 늦게 열기도 해(바쁜 PC), 빈 탭이 두 번 잇달아 안 보일 때까지 BLANK_SETTLE_MS 안에서 다시 본다
async function closeOwnBlanks(port, tab) {
  let closed = 0, quiet = 0;
  const until = Date.now() + BLANK_SETTLE_MS;
  while (quiet < 2 && Date.now() < until) {
    const pages = (await fetch(`http://127.0.0.1:${port}/json/list`).then(r => r.json()).catch(() => [])).filter(t => t.type === 'page');
    const mine = pages.filter(t => (t.url === BLANK || t.url === NEW_TAB) && !(tab && t.id === tab.id));
    let left = pages.length, last = false;
    for (const t of mine) {
      if (left <= 1) { last = true; break; }         // 남은 것이 이 빈 탭 하나뿐이다 — 그것이 창을 쥔다
      const ok = await fetch(`http://127.0.0.1:${port}/json/close/${t.id}`).then(r => r.ok).catch(() => false);
      if (ok) { left--; closed++; }
    }
    if (last) break;
    quiet = mine.length ? 0 : quiet + 1;
    await sleep(POLL_MS);
  }
  if (closed) say(`띄운 창에 남은 빈 탭 ${closed} 개를 닫았다`);
}

// 로그인 탭을 지켜본다 — 빈 탭에 붙어 창 알림을 켠 뒤 로그인 주소로 넘기고, 로그인 화면의 EP 접속 정보 창만 「확인」으로 받고,
// 통합 인증이 안 서면 평소 EP 로그인 화면으로 넘기고(사람 없는 부름은 넘기지 않고 떨어진다 — 칠 사람이 없다), 탭이 로그인 화면을
// 벗어나거나 시한이 지나면 떨어진다. 내는 것: 넘어갔나
async function watchLogin(port, tab, start, deadline, fallback, unattended, trace) {
  const page = await attachPage(tab.webSocketDebuggerUrl);
  if (!page) {
    say('로그인 탭에 못 붙었다 — 주소만 열고 받기를 되풀이한다. 「EP 접속 정보」 창이 뜨면 사람이 「확인」을 누른다');
    await fetch(`http://127.0.0.1:${port}/json/new?${start}`, { method: 'PUT' }).catch(() => null);
    return false;
  }
  const tracing = trace ? tracer(page) : null;
  try {
    let url = start;
    let accepted = 0;
    page.on(m => {
      if (m.method === 'Page.frameNavigated' && !m.params.frame.parentId) url = m.params.frame.url;
      if (m.method === 'Page.javascriptDialogOpening' && epConfirm(m.params.type, m.params.message, m.params.url || url, cfg)) {
        accepted++;
        page.call('Page.handleJavaScriptDialog', { accept: true });
      }
    });
    await page.call('Page.enable');
    if (tracing) await tracing.start();
    await page.call('Page.navigate', { url: start });
    let typingSince = 0;
    let fellBack = !fallback;
    while (Date.now() < deadline) {
      const now = await page.call('Runtime.evaluate', {
        expression: '[location.href, !!document.querySelector("input[type=password],input[type=email]"), document.title]', returnByValue: true });
      const value = now.result && now.result.result && now.result.result.value;
      if (Array.isArray(value)) url = value[0];
      const onLogin = Boolean(url) && onLoginScreen(url, cfg);
      // EP 의 두 화면의 제목을 배운다 — 평소 Edge 에서 앞에 안 선 탭은 제목으로만 알아본다(같은 화면이라 같은 제목이다)
      if (Array.isArray(value) && value[2]) {
        if (onLogin) learnTitle('login', value[2]);
        else if (hostOf(url) === hostOf(portalUrl())) learnTitle('portal', value[2]);
      }
      if (url && /^https?:/i.test(url) && !onLogin) {
        say(`로그인 탭이 넘어갔다 — ${new URL(url).host}${accepted ? ' · 「EP 접속 정보」 창을 「확인」으로 받았다(다른 자리에서 연 메일의 세션이 끊긴다)' : ''}`);
        if (tracing) {
          say(`trace — 넘어간 화면을 ${TRACE_AFTER_MS / 1000}초 더 듣는다`);
          await sleep(TRACE_AFTER_MS);
        }
        return true;
      }
      const typing = onLogin && Array.isArray(value) && value[1];
      typingSince = typing ? typingSince || Date.now() : 0;
      const stuck = typingSince && Date.now() - typingSince > cfg.fallbackMs;
      if (stuck && unattended) {
        say('통합 인증이 안 섰다 — 사람이 없어 로그인 화면에서 기다리지 않는다');
        return false;
      }
      if (!fellBack && stuck) {
        fellBack = true;
        say('통합 인증이 안 섰다 — 같은 탭을 평소 EP 로그인 화면으로 넘긴다. 사람이 그 창에서 평소 아이디로 로그인한다');
        await page.call('Page.navigate', { url: fallback });
      }
      await sleep(POLL_MS);
    }
    return false;
  } finally {
    if (tracing) tracing.done();
    page.close();                                    // 탭 자리의 연결만 끊는다 — 탭과 창은 사람이 쓴다
  }
}

// ── 평소 Edge(포트 없음) ─────────────────────────────────────────────────
// 사람의 평소 Edge 에서 먼저 로그인한다 — 그 로그인만 이 PC 의 프로그램(파수 · ECM 에이전트) 로그인까지 한다(references/SOURCES.md
// 「잰 것」). 포트가 없어 탭에 못 붙으니, 주소는 사람이 여는 것처럼 Edge 에 넘겨 열고 물음 창은 윈도 UI 자동화로 본다

// 눈 — ordinary_edge.ps1 과 한 줄씩 주고받는다(그 머리말의 꼴 · select 는 볼 Edge 를 고르는 그 환경변수). 눈이 죽거나 답이 시한을 넘으면 null 을
// 내고 그 뒤로는 안 묻는다
function edgeEye(select) {
  const child = spawn('powershell', ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', EYE],
    { windowsHide: true, env: { ...process.env, ...select } });
  let buffer = '', err = '', dead = '';
  const waiting = [];
  const stop = why => { dead = dead || why; while (waiting.length) waiting.shift()(null); };
  child.stdout.setEncoding('utf8');
  child.stdout.on('data', d => {
    buffer += d;
    for (let i; (i = buffer.indexOf('\n')) >= 0;) {
      const line = buffer.slice(0, i).trim();
      buffer = buffer.slice(i + 1);
      if (line && waiting.length) waiting.shift()(line);
    }
  });
  child.stderr.on('data', d => err += d);
  child.stdin.on('error', () => {});                 // 눈이 먼저 죽은 뒤의 쓰기 — 까닭은 close 가 든다
  child.on('error', e => stop(e.message));
  child.on('close', code => stop(`종료 ${code}${err.trim() ? ` — ${err.trim().split(/\r?\n/)[0]}` : ''}`));
  const ask = line => new Promise(resolve => {
    if (dead) return resolve(null);
    const timer = setTimeout(() => { stop(`${EYE_MS / 1000}초 안에 답이 없다`); child.kill(); }, EYE_MS);
    waiting.push(got => { clearTimeout(timer); try { resolve(got && JSON.parse(got)); } catch { resolve(null); } });
    child.stdin.write(`${line}\n`);
  });
  return {
    look: () => ask('look'),
    press: i => ask(`press ${i}`),
    tabs: () => ask('tabs'),
    why: () => dead || '답이 없다',
    dead: () => Boolean(dead),
    close: () => { try { child.stdin.end(); } catch {} setTimeout(() => { try { child.kill(); } catch {} }, 2000).unref(); },
  };
}

const many = x => [].concat(x || []);
// 물음 창의 꼴 — 입력 칸이 있으면 prompt, 단추 하나면 alert, 둘이면 confirm(CDP 의 Page.javascriptDialogOpening 이 주는 type 과 같은 말)
const dialogType = d => d.edit ? 'prompt' : d.buttons === 1 ? 'alert' : d.buttons === 2 ? 'confirm' : 'other';
// 물음 창 제목의 앞머리가 그 물음을 띄운 화면의 호스트다(「<호스트>의 메시지」 · 「<호스트> says」) — epConfirm 은 주소를 받는다
const dialogUrl = title => { const m = /^([a-z0-9.-]+(?::\d+)?)/i.exec(String(title || '')); return m ? `http://${m[1]}/` : ''; };

// 눈이 한 번 본 물음 창 가운데 받을 창(epConfirm)만 누른다 — 다른 물음은 사람의 것이라 둔다. 내는 것: 누른 수 · 눈이 죽었으면 -1
async function pressConfirms(eye, now) {
  let pressed = 0;
  for (const d of many(now.dialogs)) {
    if (!epConfirm(dialogType(d), d.message, dialogUrl(d.title), cfg)) continue;
    const got = await eye.press(d.i);
    if (!got) return -1;
    if (got.pressed === d.i) { pressed++; say(`평소 Edge 의 「EP 접속 정보」 창을 바깥에서(UI 자동화) 「${got.button || '확인'}」으로 눌렀다`); }
    else say(`평소 Edge 의 「EP 접속 정보」 창을 못 눌렀다 — ${got.why || '?'}. 다음 보기에서 다시 누른다`);
  }
  return pressed;
}

// 평소 Edge 에 로그인 주소를 연다 — 사람이 주소를 넘긴 것과 같다. 떠 있으면 그 Edge 의 새 탭, 없으면 평소 프로필로 뜬다. 포트는 안 연다.
// 늘 떼어 띄운다 — 떼지 않은 Edge 는 부른 쪽이 끝나면 함께 끝날 수 있다(SOURCES 「잰 것」)
function openOrdinary(exe, profile, url) {
  const args = profile ? [`--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check', url] : [url];
  spawn(exe, args, { detached: true, stdio: 'ignore' }).unref();
}

// 볼 평소 Edge 의 프로필 — "" 이면 사람의 평소 Edge 다(검사만 버리는 프로필을 준다)
const ordinaryProfile = () => env('EP_ORDINARY_PROFILE', '') && path.resolve(env('EP_ORDINARY_PROFILE', ''));
// 평소 Edge 에 여는 EP 포털 — 데스크톱과 VDI 가 같은 주소를 연다
const portalUrl = () => env('EP_PORTAL_URL', EP_PORTAL);

// 주소의 호스트 이름(소문자 · 포트 없이) — 못 읽으면 ""
const hostOf = url => { try { return new URL(url).hostname.toLowerCase().replace(/^\[|\]$/g, ''); } catch { return ''; } };

// 배운 탭 제목 — { portal, login }. 제목은 비밀이 아니고, EP 의 두 화면 것만 둔다
const readTitles = () => { try { const t = JSON.parse(fs.readFileSync(TITLES, 'utf8')); return { portal: String(t.portal || ''), login: String(t.login || '') }; } catch { return { portal: '', login: '' }; } };
function learnTitle(which, title) {
  const clean = String(title || '').trim();
  if (!clean || /^[a-z]+:\/\//i.test(clean) || clean.includes('/')) return;   // 제목 없는 화면은 Edge 가 주소를 제목 자리에 둔다 — 그것은 안 배운다
  const known = readTitles();
  if (known[which] === clean) return;
  try {
    fs.mkdirSync(path.dirname(TITLES), { recursive: true });
    fs.writeFileSync(TITLES, JSON.stringify({ ...known, [which]: clean }));
    say(`EP ${which === 'portal' ? '포털' : '로그인 화면'}의 탭 제목을 배웠다 — 다음 부름부터 평소 Edge 의 뒤쪽 탭도 그 제목으로 알아본다`);
  } catch (e) { say(`EP 탭 제목을 못 남겼다(${e.code || e.message}) — 평소 Edge 는 앞 탭의 주소로만 본다`); }
}

// 포트 창의 탭 가운데 EP 포털 주소의 탭에서 포털의 제목을 배운다 — 평소 Edge 의 포털 탭도 같은 화면이라 같은 제목이다. 다른 탭은 안 본다
async function learnPortalTitle(port) {
  if (!port) return;
  const got = await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(VERSION_MS) }).then(r => r.json()).catch(() => []);
  const pages = Array.isArray(got) ? got : [];      // 배우기는 곁일이다 — 받은 세션을 이 일로 접지 않는다
  const portal = pages.find(t => t.type === 'page' && hostOf(t.url) === hostOf(portalUrl()) && !onLoginScreen(t.url, cfg));
  if (portal) learnTitle('portal', portal.title);
}

// 평소 Edge 를 한 번 본다 — 눈이 탭 줄 · 주소창을 읽어 EP 에 맞는 수만 낸다(사람의 다른 탭은 눈 밖으로 안 나온다).
// 내는 것: 'portal'(앞 탭이 포털이거나, 배운 포털 제목의 탭이 있다) · 'absent'(평소 Edge 가 없거나, 읽혔는데 포털이 없다) · 'unread'(못 읽었다)
async function lookOnce(eye) {
  const got = await eye.tabs();
  lastTabs = got;
  if (!got) return 'unread';
  if (got.portal > 0 || got.titled > 0) return 'portal';
  if (!got.browsers) return 'absent';
  return got.unread > 0 ? 'unread' : 'absent';
}
let lastTabs = null;                                 // 마지막 읽기의 수 — 못 읽었을 때 진행 줄에 창의 수만 댄다

// 평소 Edge 에 EP 포털 탭이 있나 — 무엇을 열기 전에. 「있다」는 STEADY 번 잇달아 본 것만 믿고, 못 읽으면 LOOK_TRIES 번까지 다시 읽는다.
// 내는 것: { state: 'portal' | 'absent' | 'unread', why }
async function lookForPortal(eye) {
  let unread = 0, steady = 0;
  for (;;) {
    const now = await lookOnce(eye);
    if (now === 'portal') { if (++steady >= STEADY) return { state: 'portal' }; await sleep(EYE_GAP_MS); continue; }
    if (now === 'absent') return { state: 'absent' };
    steady = 0;
    if (++unread >= LOOK_TRIES) {
      return { state: 'unread', why: eye.dead() ? `평소 Edge 를 보는 눈(${path.basename(EYE)} · 윈도 UI 자동화)이 안 선다 — ${eye.why()}`
        : `평소 Edge 창 ${lastTabs ? lastTabs.windows : '?'} 개 가운데 ${lastTabs ? lastTabs.unread : '?'} 개의 탭 줄 · 주소창이 안 읽힌다(창이 브라우저 칸을 UI 자동화에 안 내놓는다)` };
    }
    await sleep(LOOK_GAP_MS);
  }
}

// 평소 Edge 의 걸음 — 사람이 여는 EP 포털을 열고 그 Edge 를 본다. press 면 받을 확인 창(epConfirm)만 누르고(다른 물음은 사람의 것), watch 면 앞 탭이
// EP 포털로 STEADY 번 잇달아 서는 것을 보고 곧 끝낸다(아니면 until 까지 다 둔다).
// 눈이 안 서도(회사 정책이 스크립트를 막는 따위) 포털은 열고 기다림은 그대로 둔다 — 확인 창만 못 누른다. 로그인을 접지는 않는다.
// 내는 것: { pressed: 누른 수, blind: 눈이 안 선 까닭이나 '', confirmed: 포털이 섰나 }
async function ordinaryStep(eye, exe, { until, press, watch }) {
  let seeing = Boolean(await eye.look());            // 포털을 열기 앞에 한 번 — 눈(PowerShell)이 뜨는 틈을 확인 창이 뜨기 앞에 치른다
  openOrdinary(exe, ordinaryProfile(), portalUrl());
  let pressed = 0, steady = 0;
  while (Date.now() < until) {
    await sleep(EYE_GAP_MS);
    if (!seeing) continue;
    if (press) {
      const now = await eye.look();
      const got = now ? await pressConfirms(eye, now) : -1;
      if (got < 0) { seeing = false; continue; }
      pressed += got;
    }
    if (watch) {
      steady = await lookOnce(eye) === 'portal' ? steady + 1 : 0;
      if (steady >= STEADY) return { pressed, blind: '', confirmed: true };
    }
  }
  return { pressed, confirmed: false, blind: seeing ? '' : `평소 Edge 를 보는 눈(${path.basename(EYE)} · 윈도 UI 자동화)이 안 선다 — ${eye.why()}` };
}

// 이 윈도 로그온의 열쇠 — 이 세션의 탐색기(explorer)가 뜬 때. 로그온마다 새로 뜨고, 빠른 시작으로 끈 PC 도 켜서 로그온하면 바뀐다(부팅
// 시각은 빠른 시작이 안 바꾼다). 못 읽으면 "" — 그때는 표를 안 읽고 안 남긴다(묻기 · 걸음이 부를 때마다 다시 선다), VDI 의 정한 틈 걸음은 건너뛴다
function logonKey() {
  const given = env('EP_LOGON_KEY', '');
  if (given) return given;
  if (process.platform !== 'win32') return '';
  try {
    return execFileSync('powershell', ['-NoProfile', '-NonInteractive', '-Command',
      '$s = (Get-Process -Id $PID).SessionId; $e = Get-Process explorer -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -eq $s } | ' +
      "Sort-Object StartTime | Select-Object -First 1; if ($e) { $e.StartTime.ToUniversalTime().ToString('o') }"],
    { encoding: 'utf8', timeout: FIND_MS, windowsHide: true }).trim();
  } catch { return ''; }
}

const readMark = () => { try { return fs.readFileSync(ORDINARY_MARK, 'utf8').trim(); } catch { return ''; } };
function writeMark(key) {
  try { fs.mkdirSync(path.dirname(ORDINARY_MARK), { recursive: true }); fs.writeFileSync(ORDINARY_MARK, `${key}\n`); }
  catch (e) { say(`평소 Edge 로그인의 표를 못 남겼다(${e.code || e.message}) — 다음 부름이 평소 Edge 의 걸음을 한 번 더 한다`); }
}

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
const VDI_NOT_YET = seconds => `VDI — 사용자의 평소 Edge 에 EP 포털을 열고 ${seconds}초 기다렸는데 그 탭이 EP 포털로 넘어가지 않았다. ` +
  `다음: 사용자에게 그 EP 탭에서 평소 아이디로 로그인을 마쳤는지 묻는다 — 마쳤다면 같은 명령에 ${ORDINARY_DONE} 를 붙여 다시 부르고, 아직이면 ` +
  '로그인한 뒤 그대로 다시 부른다';

// 평소 Edge 의 걸음 — 사용자의 평소 Edge 를 보고 고른다(머리말 「차례」). 이 로그온의 표(ORDINARY_MARK)는 평소 Edge 를 못 읽는 자리에서 이 로그온의
// 평소 로그인이 정해졌다는 기록이다 — 정한 틈의 걸음을 했거나 사용자가 답했다. 내는 것: 평소 Edge 를 열었나(열었으면 부른 쪽이 세션을 다시
// 받는다 — 평소 로그인이 포트 창의 메일을 끊는다). 사람에게 물어야 하거나 VDI 에서 사람의 로그인을 못 기다렸으면 Exit(4)
async function ordinaryFirst(vdi, opts) {
  if (vdi && opts.unattended) return false;          // 사람 없는 VDI — 칠 사람이 없어 보지도 열지도 않는다
  const key = logonKey();
  if (opts.ordinary === ORDINARY_DONE) {             // 4 로 물은 답 — 사용자의 말이 눈 위에 선다(VDI 의 기다림이 지난 뒤의 답도)
    say('사용자가 오늘 평소 Edge 에서 EP 에 이미 로그인했다고 답했다 — 평소 Edge 는 안 연다');
    if (key) writeMark(key);
    return false;
  }
  const titles = readTitles();
  // 포털 제목은 로그인 화면의 제목과 다를 때만 쓴다 — 같으면 로그인 화면의 탭을 포털로 읽는다
  const title = titles.portal && titles.portal !== titles.login ? titles.portal : '';
  const eye = edgeEye({ EP_ORDINARY_PROFILE: ordinaryProfile(), EP_TAB_PORTAL: hostOf(portalUrl()), EP_TAB_LOGIN: cfg.loginHosts.join(','), EP_TAB_TITLE: title });
  try {
    const seen = await lookForPortal(eye);
    if (seen.state === 'portal') {
      say('사용자의 평소 Edge 에 EP 포털 탭이 이미 있다 — 평소 EP 로그인이 서 있어 평소 Edge 는 안 연다');
      return false;
    }
    if (seen.state === 'absent') {
      say('사용자의 평소 Edge 에 EP 포털 탭이 없다(평소 Edge 가 안 떠 있거나, 떠 있는데 EP 탭이 없거나 로그인 화면에 있다)');
      return await ordinaryUntilPortal(eye, vdi, key);      // await — 안 기다리면 finally 가 눈을 먼저 닫는다
    }
    say(`사용자의 평소 Edge 를 읽지 못했다 — ${seen.why}`);
    if (key && readMark() === key) { say('이 로그온의 평소 로그인은 앞서 정해졌다(평소 Edge 걸음을 했거나 사용자가 답했다) — 평소 Edge 는 안 연다'); return false; }
    if (!opts.ordinary && !opts.unattended) throw new Exit(4, ASK_PERSON);
    say(opts.unattended ? '사람 없는 부름이라 물을 사람이 없다 — 정한 틈의 평소 Edge 걸음을 한다' : '사용자가 아직이라고 답했다 — 평소 Edge 걸음부터 한다');
    return await ordinaryFixed(eye, vdi, key);
  } finally {
    eye.close();
  }
}

// 평소 Edge 에 EP 포털 탭이 없다 — 포털을 열고 그 탭이 EP 포털로 넘어가기를 본다. 사람이 로그인해 두고 탭만 닫았으면 포털이 곧 서 곧 잇는다.
// 데스크톱은 확인 창을 누르며 cfg.ordinaryMs 까지 보고, 지나면 알리고 잇는다 — 붙은 창 로그인으로 메일 · 일정은 서야 한다. VDI 는 사용자가 치는 동안
// cfg.loginMs 까지 보고, 지나면 4(VDI_NOT_YET)다 — 표는 안 남긴다(사용자의 답이 다음 부름을 정한다). 내는 것: true(열었다)
async function ordinaryUntilPortal(eye, vdi, key) {
  const exe = findEdge();
  if (!exe) throw new Exit(1, 'Edge 를 못 찾았다');
  const ms = vdi ? cfg.loginMs : cfg.ordinaryMs;
  say(vdi ? `VDI — 사용자의 평소 Edge 에 EP 포털을 연다(포트 없이). 사용자가 거기서 평소 아이디로 로그인하면 이어 간다 — 그 탭이 EP 포털로 넘어가기를 최대 ${Math.round(ms / 1000)}초 본다`
    : `사용자의 평소 Edge 에 EP 포털을 연다(포트 없이 — 사람이 연 것과 같다) — 「EP 접속 정보」 창이 뜨면 누르며, 그 탭이 EP 포털로 넘어가기를 최대 ${ms / 1000}초 본다`);
  const step = await ordinaryStep(eye, exe, { until: Date.now() + ms, press: !vdi, watch: true });
  if (!vdi) sayStep(step);
  if (step.confirmed) {
    say(`평소 Edge 의 EP 탭이 EP 포털로 넘어갔다 — 평소 EP 로그인이 섰다. EP 로그인용 창으로 잇는다`);
    if (key) writeMark(key);
    return true;
  }
  if (vdi) throw new Exit(4, VDI_NOT_YET(Math.round(ms / 1000)));
  say(`${ms / 1000}초 안에 평소 Edge 의 EP 탭이 EP 포털로 넘어가지 않았다 — 평소 로그인이 안 넘었을 수 있다. EP 로그인용 창으로 이어 메일 · 일정은 ` +
    '세운다. DRM 문서가 안 열리면 사용자가 평소 Edge 에서 EP 에 로그인한 뒤 이 명령을 다시 부른다');
  if (key) writeMark(key);
  return true;
}

// 평소 Edge 를 못 읽는 자리의 걸음 — 정한 틈(cfg.ordinaryMs)을 다 둔다. 넘었나는 못 본다 — 안 넘은 걸음은 다시 해도 안 넘고, 그때는 사용자가 평소
// Edge 에서 로그인한다. VDI 는 사람이 자판 앞에서 제 물음 창까지 누르니 누르지 않는다 — 포털을 열고 표를 남긴 뒤 4(VDI_ORDINARY)로 끝낸다. 로그온
// 열쇠가 "" 인 VDI 는 걸음을 건너뛴다 — 표 없이 4 로 끝내면 부를 때마다 같은 자리로 돌아와 로그인에 못 닿는다. 내는 것: 걸음을 했나
async function ordinaryFixed(eye, vdi, key) {
  if (vdi && !key) {
    say('이 윈도 로그온을 못 가려 평소 Edge 를 먼저 여는 걸음을 건너뛴다 — DRM 문서가 안 열리면 사용자가 평소 Edge 에서 EP 에 로그인한 뒤 이 명령을 다시 부른다');
    return false;
  }
  const exe = findEdge();
  if (!exe) throw new Exit(1, 'Edge 를 못 찾았다');
  if (vdi) {
    openOrdinary(exe, ordinaryProfile(), portalUrl());
    writeMark(key);
    throw new Exit(4, VDI_ORDINARY);
  }
  say(`사용자의 평소 Edge 에 EP 포털을 연다(포트 없이 — 사람이 연 것과 같다) — ${cfg.ordinaryMs / 1000}초 동안 「EP 접속 정보」 창이 뜨면 누른다`);
  sayStep(await ordinaryStep(eye, exe, { until: Date.now() + cfg.ordinaryMs, press: true, watch: false }));
  if (key) writeMark(key);
  return true;
}

// 평소 Edge 걸음의 눈이 한 일을 알린다
function sayStep(step) {
  if (step.blind) say(`${step.blind}. 평소 Edge 에 EP 포털은 열었다 — 거기 「EP 접속 정보」 창이 떠 있으면 사용자가 누른다`);
  else say(`평소 Edge 에 EP 포털을 열었다 — 「EP 접속 정보」 창을 ${step.pressed ? `눌렀다(${step.pressed}번)` : '못 봤다'}`);
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

// 로그인 탭의 연결을 듣는다 — 이 PC 로 가는 요청 · 웹소켓과 그 답 · 막힘, 다른 프로그램을 여는 넘김, 화면의 오류 줄
function tracer(page) {
  const seen = new Map();
  const count = { sent: 0, sockets: 0, blocked: 0, handoffs: 0, errors: 0 };
  page.on(m => {
    const p = m.params || {};
    if (m.method === 'Network.requestWillBeSent' && towardThisPc(p.request.url)) {
      seen.set(p.requestId, traceUrl(p.request.url)); count.sent++;
      say(`trace 요청 ${p.request.method} ${traceUrl(p.request.url)} ← ${traceUrl(p.documentURL || '')}`);
    } else if (m.method === 'Network.responseReceived' && seen.has(p.requestId)) {
      say(`trace 답 ${p.response.status} ${seen.get(p.requestId)}`);
    } else if (m.method === 'Network.loadingFailed' && seen.has(p.requestId)) {
      count.blocked++;
      say(`trace 막힘 ${seen.get(p.requestId)} — ${p.errorText || ''}${p.blockedReason ? ` · ${p.blockedReason}` : ''}` +
        `${p.corsErrorStatus ? ` · ${p.corsErrorStatus.corsError}` : ''}`);
    } else if (m.method === 'Network.webSocketCreated' && towardThisPc(p.url)) {
      seen.set(p.requestId, traceUrl(p.url)); count.sockets++;
      say(`trace 웹소켓 ${traceUrl(p.url)}`);
    } else if (m.method === 'Network.webSocketHandshakeResponseReceived' && seen.has(p.requestId)) {
      say(`trace 웹소켓 답 ${p.response.status} ${seen.get(p.requestId)}`);
    } else if (m.method === 'Network.webSocketFrameError' && seen.has(p.requestId)) {
      count.blocked++;
      say(`trace 웹소켓 막힘 ${seen.get(p.requestId)} — ${String(p.errorMessage || '').slice(0, TRACE_TEXT)}`);
    } else if (m.method === 'Page.frameRequestedNavigation' && towardThisPc(p.url)) {
      count.handoffs++;
      say(`trace 넘김 ${traceUrl(p.url)} (${p.reason || ''})`);
    } else if (m.method === 'Log.entryAdded' && p.entry && p.entry.level === 'error') {
      count.errors++;
      say(`trace 화면 오류 ${String(p.entry.text || '').replace(/\s+/g, ' ').slice(0, TRACE_TEXT)}`);
    }
  });
  return {
    start: async () => { await page.call('Network.enable'); await page.call('Log.enable'); },
    done: () => say(`trace — 이 PC 로 간 요청 ${count.sent} · 웹소켓 ${count.sockets} · 막힌 것 ${count.blocked} · 이 PC · 다른 프로그램으로 가는 넘김 ` +
      `${count.handoffs} · 화면 오류 ${count.errors}. 탭 안의 다른 사이트 틀(따로 도는 프로세스)은 못 듣는다`),
  };
}

// ── 띄우기 ───────────────────────────────────────────────────────────────

// 그 프로필의 Edge 창 하나를 포트와 빈 탭으로 띄운다(로그인 주소는 붙은 뒤에 연다 — blankTab). 내는 것: 열린 포트 · 못 열었으면 Exit.
// 동기화는 끈다(--disable-sync) — 새 프로필은 윈도 계정으로 저절로 로그인해 동기화를 묻는 작은 창을 따로 띄우고, 동기화된 확장이 안내 탭을
// 앞으로 내면 로그인 탭에 뜬 「EP 접속 정보」 창이 닫힌다(SOURCES 「잰 것」). 이 창은 로그인 자리라 사람의 즐겨찾기 · 확장을 안 들인다
async function launch(exe, profile) {
  const dir = path.resolve(profile);
  const args = [`--remote-debugging-port=${cfg.port}`, '--remote-debugging-address=127.0.0.1', `--user-data-dir=${dir}`,
    '--no-first-run', '--no-default-browser-check', '--disable-sync', BLANK];
  const child = spawn(exe, args, { detached: true, stdio: 'ignore', windowsHide: false });
  child.unref();
  say(`Edge 창을 띄웠다 — pid ${child.pid} · 프로필 ${dir}`);
  const deadline = Date.now() + PORT_MS;
  while (Date.now() < deadline) {
    await sleep(POLL_MS);
    const v = await version(cfg.port);
    if (v && v.Browser) { say(`포트가 열렸다 — 127.0.0.1:${cfg.port} · ${v.Browser}`); return cfg.port; }
  }
  throw new Exit(1, `띄웠는데 포트가 안 열린다 — 그 프로필(${dir})의 Edge 가 이미 포트 없이 떠 있거나, 포트 ${cfg.port} 를 다른 프로그램이 ` +
    '쓰거나, 회사 정책이 막는다. 다음: 멈추고 이 말을 사람에게 그대로 전한다');
}

// ── 갈래 ─────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const opts = { pass: [], profile: PROFILE_DIR };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--profile') { opts.profile = argv[++i] || ''; if (!opts.profile) throw new Exit(1, '--profile 뒤에 폴더를 준다'); }
    else if (argv[i] === UNATTENDED) opts.unattended = true;
    else if (argv[i] === '--trace') opts.trace = true;
    else if (argv[i] === ORDINARY_DONE || argv[i] === ORDINARY_NOT_YET) {
      if (opts.ordinary && opts.ordinary !== argv[i]) throw new Exit(1, `${ORDINARY_DONE} 와 ${ORDINARY_NOT_YET} 는 하나만 준다`);
      opts.ordinary = argv[i];
    }
    else if (argv[i].startsWith('--')) throw new Exit(1, `모르는 선택: ${argv[i]}`);
    else opts.pass.push(argv[i]);                    // 세션 파일 · domino · ecm — 받는 손이 가린다
  }
  return opts;
}

async function main(argv) {
  if (typeof WebSocket !== 'function' || typeof fetch !== 'function') throw new Exit(1, `Node ${process.version} — 22 이상이 든다(내장 WebSocket)`);
  const opts = parseArgs(argv);
  const vdi = onVdi();
  const epLogin = env('EP_LOGIN_URL', EP_LOGIN);
  const start = vdi ? epLogin : env('COMPANY_LOGIN_URL', COMPANY_LOGIN);
  const fallback = vdi ? '' : epLogin;               // VDI 는 처음부터 평소 EP 로그인 화면이라 넘길 곳이 없다
  let got = await receiveAll(opts.pass);
  // 평소 Edge 의 로그인이 먼저다 — 포트 창의 세션이 살았든 아니든 평소 Edge 를 보고 고른다(그 로그인만 이 PC 의 프로그램 로그인까지 한다).
  // 받는 손이 스스로 멈춘 부름(인자 따위)은 열 일이 아니다. 걸음 뒤에는 다시 받는다 — 평소 로그인이 포트 창의 메일을 끊는다
  if (got.code !== RECEIVED.TOOL && await ordinaryFirst(vdi, opts)) got = await receiveAll(opts.pass);
  // 기록하는 부름은 세션이 살아 있어도 로그인 탭을 연다 — 볼 것은 로그인 화면과 넘어간 화면이 이 PC 에 무엇을 보내나다
  if (settled(got) && !(opts.trace && got.code === RECEIVED.OK)) return finish(got);
  if (opts.unattended && vdi) {
    throw new Exit(4, 'VDI 는 사람이 아이디를 쳐야 한다 — 사람 없는 부름은 로그인 창을 띄우지 않는다. 다음: 사람이 대화에서 EP 로그인을 한다');
  }

  const deadline = Date.now() + (opts.unattended ? Math.min(cfg.loginMs, UNATTENDED_MS) : cfg.loginMs);
  let port, tab, launched = false;
  port = got.code === RECEIVED.NOT_LOGGED_IN || opts.trace ? await openPort() : null;
  if (got.code === RECEIVED.NOT_LOGGED_IN && !port) throw new Exit(1, '받는 손은 붙었다는데 포트를 연 Edge 를 못 찾았다');
  if (port) {
    // 포트가 열린 Edge 가 있다 — 로그인이 끊겼거나 기록하는 부름이다. 그 Edge 에 로그인 탭을 연다
    say(`Edge(127.0.0.1:${port})에 ${got.code === RECEIVED.NOT_LOGGED_IN ? '로그인이 안 됐다 — ' : ''}로그인 탭을 연다`);
    tab = await blankTab(port, false);
  } else {
    // 붙을 Edge 가 없다 — ep-login 프로필의 창 하나를 띄운다. 사람의 평소 Edge 는 떠 있어도 안 건드린다
    const exe = findEdge();
    if (!exe) throw new Exit(1, 'Edge 를 못 찾았다');
    port = await launch(exe, opts.profile);
    launched = true;
    tab = await blankTab(port, true);
  }

  say(vdi ? '그 창에서 사람이 평소 아이디로 로그인한다 — 이쪽은 로그인이 끝나기를 기다린다' : '로그인 탭을 지켜본다 — 통합 인증이면 입력 없이 넘는다');
  let passed = false;
  if (tab) passed = await watchLogin(port, tab, start, deadline, fallback, opts.unattended, opts.trace);
  else say('로그인 탭을 못 열었다 — 받기만 되풀이한다');
  // 사람 없는 부름은 안 넘어간 로그인을 시한까지 기다리지 않는다 — 한 번 받아 보고 끝낸다
  got = await receiveUntil(opts.pass, opts.unattended && !passed ? Date.now() : deadline);
  if (launched) await closeOwnBlanks(port, tab);
  await learnPortalTitle(port);
  if (got.code === RECEIVED.NOT_LOGGED_IN && opts.unattended) {
    throw new Exit(4, '통합 인증으로 세션이 안 섰다 — 사람이 없어 더 기다리지 않았다. 다음: 사람이 그 Edge 창이나 대화에서 EP 로그인을 한다');
  }
  if (got.code === RECEIVED.NOT_LOGGED_IN) {
    throw new Exit(4, `로그인 시한(${Math.round(cfg.loginMs / 1000)}초) 안에 세션이 안 섰다${got.said ? ` — ${got.said}` : ''}. ` +
      '다음: 사람에게 그 Edge 창에서 EP 로그인을 마쳐 달라고 하고, 됐다고 하면 같은 명령을 다시 부른다(이번엔 받기만 하고 끝난다)');
  }
  return finish(got);
}

function done(got) { console.log(got.file); return 0; }

// 받기 한 판이 이 명령의 끝을 정했나 — 섰다 · 받는 손이 멈췄다 · ECM 만 못 받았다. 로그인이 안 됐다 · Edge 가 없다는 다음 걸음이 있다
const settled = got => [RECEIVED.OK, RECEIVED.TOOL, RECEIVED.ECM_HANDOFF].includes(got.code);

// 끝난 받기를 이 명령의 종료로 바꾼다 — 0 · ECM 만 못 받았으면 4 · 그 밖은 1
function finish(got) {
  if (got.code === RECEIVED.OK) return done(got);
  if (got.code === RECEIVED.ECM_HANDOFF) return ecmFailed(got);
  throw new Exit(1, got.said || `받는 손이 ${got.code} 로 멈췄다`);
}

function ecmFailed(got) {
  throw new Exit(4, `EP 로그인은 섰는데 ECM 세션을 탭으로도 못 받았다${got.said ? ` — ${got.said}` : ''}. 다음: 멈추고 이 말을 사람에게 그대로 전한다 — 다시 로그인할 일이 아니다`);
}

// 끝마다 표준 오류에 거는 한 줄 — 사람이 회사 일을 시킨 대화에서 그 일의 첫 걸음에 손부터 나가는 것을 한 번 건다. 사람 없는
// 부름에는 읽을 모델이 없어 안 건다. 표준 출력(세션 파일 경로)은 건드리지 않는다
const BEFORE_WORK = '회사 일 — 이 일의 목적과 가장 나은 길(어떤 스킬을 어떤 차례로 · 무엇을 하위 에이전트에 맡길지)부터 세우고 간다';

// 명령 한 번 — main 의 종료 값으로 프로세스를 끝낸다
function run(argv) {
  const remind = () => { if (!argv.includes(UNATTENDED)) say(BEFORE_WORK); };
  main(argv).then(code => { remind(); process.exit(code); }, error => {
    console.error(error.message);
    remind();
    process.exit(error instanceof Exit ? error.code : 1);
  });
}

if (require.main === module) run(process.argv.slice(2));
