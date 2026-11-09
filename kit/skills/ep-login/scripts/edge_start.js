// 쓰는 사람의 Edge 를 디버깅 포트(127.0.0.1 에만)로 EP 로그인 탭 하나와 함께 띄우고, 그 탭의 로그인을 지켜본다(「EP 접속 정보」
// 창을 받는다 — 로그인은 데스크톱에서는 통합 인증이 넘고 VDI 에서는 사람이 친다) — edge_session.js 가 붙을 자리를 세우는 손.
// 스킬 ep-login 이 부른다. 띄운 창은 사람이 그대로 쓴다.
//
// 부르는 꼴:
//     node edge_start.js [--profile <폴더>] [주소]
//   주소 — 띄운 창의 하나뿐인 탭이 열 곳. 안 주면 데스크톱은 사내 SSO 의 회사 로그인(LOGIN_URL — 통합 인증으로 입력 없이 넘는다),
//     VDI 는 평소 EP 로그인 화면(EP_LOGIN_URL — 사람이 평소 아이디로 로그인한다)이다.
//   --profile — 기본 프로필 대신 그 폴더를 프로필로 쓴다. 기본 프로필로 띄웠는데 포트가 안 열리는 Chromium 136 이상의 Edge(종료 3)
//     에서만 쓴다 — 그 프로필은 사람의 평소 Edge 와 따로 놀아 그 로그인이 평소 Edge 의 메일 세션을 끊는다.
//   환경변수 EDGE_DEBUG_PORT 포트 · SESSION_LOGIN_HOSTS 로그인 화면 호스트 · SESSION_LOGIN_WAIT_SECONDS 로그인 탭을 지켜보는 시한 —
//   뜻과 기본값은 받는 손(edge_session.js)의 settings 한 자리에서 읽는다. 로그인 화면과 받을 창도 그 손의 onLoginScreen · epConfirm 이 가린다.
//
// 하는 일 — 이미 포트가 열려 있으면 아무것도 안 띄우고 0 이다(탭도 안 연다). 아니면 Edge 를 띄우고, 포트가 열리면 띄운 그 탭
//   하나에만 붙어 로그인 화면을 지켜본다: SSO 의 「다른 PC에서 EP 접속 정보」 확인 창이 로그인 화면에 뜨면 「확인」으로 받고,
//   탭이 로그인 화면을 벗어나면(EP 로 넘어가면) 떨어진다. 다른 탭 · 팝업에는 붙지 않는다 — 붙은 채 뜬 SSO 팝업(ssoframe)은 디버거를
//   기다리며 멈춰 EP 가 빈 화면에 선다. 그 밖의 확인 창은 건드리지 않는다(사람의 것이다).
//
// 내는 것 — 종료 값은 닫힌 넷이다:
//   0 포트가 열려 있다 — 이미 열렸거나 띄워서 열렸다. 판(Edg/…)과 로그인 탭의 결과를 한 줄씩 낸다(로그인이 섰는지는
//     edge_session.js 가 가린다)
//   2 포트 없이 도는 Edge 가 있다 — 그 Edge 를 트레이까지 다 닫아야 포트가 선다(떠 있는 Edge 에 새 명령의 플래그는 버려진다).
//     이 손은 사람의 Edge 를 닫지 않는다
//   3 기본 프로필로 띄웠는데 시한 안에 포트가 안 열렸다 — 까닭은 Edge 판으로 갈린다. Chromium 136 이상은 기본 프로필에 포트를 안
//     여는 판이라 --profile 로 다시 부른다. 그 아래 판은 포트 없이 떠 있던 Edge(시작 부스트 · 닫은 뒤에도 백그라운드 실행)나 정책이다
//   1 그 밖 — Edge 를 못 찾음 · 인자 · --profile 로 띄웠는데 포트가 안 열림(그 프로필의 Edge 가 이미 포트 없이 떴거나 정책이 막는다)
//
// 왜 이렇게 띄우나 — mail-secretary 결정 0009 · 0023 과 그 상주(runner.py 의 EDGE_FLAGS · find_edge · launch_edge)가 회사 데스크톱 ·
//   VDI 에서 잰 길이다: 쓰는 사람의 평소 Edge 를 포트로 띄우고 사람이 그 창에서 한 번 로그인한다. 플래그 둘(포트 · 127.0.0.1)은
//   그대로이고, 상주가 쓰는 --no-startup-window 는 안 쓴다 — 여기서는 그 창에서 바로 로그인한다. 판은 묻지 않고 띄워 본 결과로
//   가린다 — 깔린 폴더에는 아직 적용 안 된 업데이트의 판 폴더가 함께 있어, 폴더 이름의 판은 도는 판이 아니다.
// ⚠ 포트는 이 PC 의 다른 프로그램도 쓸 수 있어 그 Edge 의 세션을 다 다룬다 — 127.0.0.1 에만 연다.

'use strict';
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');

// 사내 SSO 의 회사 로그인 — mail-secretary secretary/identity.py 의 COMPANY_LOGIN_PATH · posco/ENV-posco.md 「사내 메일함」.
// ADFS 로 넘어가 데스크톱은 통합 인증으로 입력 없이 서지만, VDI 에서는 처음 보는 ADFS 창이 전체 메일 주소를 받는다
const LOGIN_URL = 'http://swpsso.posco.net/idms/U61/jsp/login/saml_login.jsp?companyCode=shared';
// 평소 EP 로그인 — swp.posco.net 이 보내는 화면(VDI 꼴의 아이디 · 비밀번호 칸). VDI 는 통합 인증이 안 서 사람이 여기서 로그인한다
const EP_LOGIN_URL = 'http://swpsso.posco.net/idms/U61/jsp/login/login.jsp';
// VMware Horizon VDI 인가 — 에이전트가 세션에 심는 브로커 값 · VDI 도메인
const onVdi = () => Boolean((process.env.ViewClient_Broker_DNS_Name || '').trim()) || /\.VDI$/i.test(process.env.USERDNSDOMAIN || '');
const WAIT_MS = 15000;                // 띄운 뒤 포트가 열리기를 기다리는 시한(상주의 EDGE_WAIT_SECONDS 와 같다)
const POLL_MS = 500;
const VERSION_MS = 2000;
const CALL_MS = 5000;                 // CDP 부름 하나의 시한
const CANDIDATES = [                  // 상주 runner.py 의 EDGE_CANDIDATES 와 같은 차례
  [process.env['ProgramFiles(x86)'], 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.ProgramFiles, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.LOCALAPPDATA, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
];

// 포트 · 로그인 화면 호스트 · 로그인 시한 · 로그인 화면과 받을 창의 가림은 받는 손이 든다 — 두 손이 같은 자로 가린다
const { settings, onLoginScreen, epConfirm } = require('./edge_session.js');
const cfg = settings();
const port = cfg.port;
const loginWaitMs = cfg.loginMs;              // 로그인 탭을 지켜보는 시한 — VDI 는 사람이 그 탭에서 로그인한다
const say = line => console.log(line);
const NEXT = ' 다음: 받는 손(session.sh)을 부른다';
const HUMAN = '다음: 그 창에서 사람이 로그인한다 — 「EP 접속 정보」 창이 뜨면 「확인」이 다른 자리에서 연 메일의 세션을 끊는다고 알린다 · 됐다고 하면 받는 손(session.sh)';
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function version() {
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

// 도는 Edge 가 있나 — 수만 센다(명령줄은 안 읽는다)
function edgeRunning() {
  try {
    const out = execFileSync('tasklist', ['/FI', 'IMAGENAME eq msedge.exe', '/FO', 'CSV', '/NH'], { encoding: 'utf8', windowsHide: true });
    return out.split(/\r?\n/).filter(line => /^"msedge\.exe"/i.test(line)).length > 0;
  } catch { return false; }
}

// 띄운 탭 하나의 페이지 자리에 붙는다 — 브라우저 자리의 자동 붙기를 안 써서 다른 탭 · 팝업은 멈추지 않는다
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

// 로그인 탭을 지켜본다 — 로그인 화면의 EP 접속 정보 창만 「확인」으로 받고, 탭이 로그인 화면을 벗어나면 떨어진다. 내는 것: 한 줄의 결과
async function watchLogin(target) {
  const page = await attachPage(target.webSocketDebuggerUrl);
  if (!page) return `로그인 탭에 못 붙었다. ${HUMAN}`;
  try {
    let url = target.url;
    let accepted = 0;
    page.on(m => {
      if (m.method === 'Page.frameNavigated' && !m.params.frame.parentId) url = m.params.frame.url;
      if (m.method === 'Page.javascriptDialogOpening') {
        const ours = epConfirm(m.params.type, m.params.message, m.params.url || url, cfg);
        if (ours) { accepted++; page.call('Page.handleJavaScriptDialog', { accept: true }); }
      }
    });
    await page.call('Page.enable');
    // 붙기 전에 이미 떠 있던 창 — 지금 주소가 로그인 화면일 때만 받는다(어느 창인지는 Page.enable 이 다시 알린다)
    const deadline = Date.now() + loginWaitMs;
    let left = false;
    while (Date.now() < deadline) {
      const now = await page.call('Runtime.evaluate', { expression: 'location.href', returnByValue: true });
      if (now.result && now.result.result && typeof now.result.result.value === 'string') url = now.result.result.value;
      if (url && /^https?:/i.test(url) && !onLoginScreen(url, cfg)) { left = true; break; }
      await sleep(POLL_MS);
    }
    const dialog = accepted ? ` · 「EP 접속 정보」 창을 「확인」으로 받았다(다른 자리의 EP 세션이 끊긴다)` : '';
    return left ? `로그인 탭이 넘어갔다 — ${new URL(url).host}${dialog}.${NEXT}`
      : `로그인 화면에서 시한(${Math.round(loginWaitMs / 1000)}초)이 지났다${dialog}. 다음: 사람이 그 창에서 로그인한다(VDI 는 통합 인증이 안 선다) · 됐다고 하면 받는 손(session.sh)`;
  } finally {
    page.close();                                    // 탭 자리의 연결만 끊는다 — 탭과 창은 사람이 쓴다
  }
}

async function main(argv) {
  let profile = '';
  let url = '';
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--profile') { profile = argv[++i] || ''; if (!profile) return fail(1, '--profile 뒤에 폴더를 준다'); }
    else if (argv[i].startsWith('--')) return fail(1, `모르는 선택: ${argv[i]}`);
    else if (!url) url = argv[i];
    else return fail(1, `인자가 남는다: ${argv[i]}`);
  }
  const open = await version();
  if (open && open.Browser) { say(`이미 열려 있다 — 127.0.0.1:${port} · ${open.Browser}.${NEXT} — 3 이면 그 Edge 에서 EP 로그인이 안 된 것이라 사람이 그 창에서 로그인한다`); return 0; }
  const exe = findEdge();
  if (!exe) return fail(1, 'Edge 를 못 찾았다');
  if (!profile && edgeRunning()) return fail(2, 'Edge 가 디버깅 포트 없이 돌고 있다 — 떠 있는 Edge 에는 포트를 못 연다. 다음: 사람에게 까닭을 알리고, 사람이 Edge 창과 알림 영역(트레이)의 Edge 를 다 닫거나 ' +
    '사람이 동의하면 이쪽이 Edge 프로세스를 다 끝낸 뒤 다시 부른다 — 동의 없이 끝내지 않는다(열린 탭 · 쓰던 글이 사람 것 · 탭은 「페이지 복원」으로 돌아온다). 닫았는데 또 2 면 Edge 가 뒤에서 사는 설정(시작 부스트 · 닫은 뒤에도 백그라운드 실행)이 켜진 것이다 — 끌지는 사람이 고른다');
  const start = url || (onVdi() ? EP_LOGIN_URL : LOGIN_URL);
  const args = [`--remote-debugging-port=${port}`, '--remote-debugging-address=127.0.0.1'];
  if (profile) args.push(`--user-data-dir=${path.resolve(profile)}`, '--no-first-run');
  args.push(start);                                  // 띄운 창의 하나뿐인 탭이 이 주소다 — 새 탭을 따로 안 연다
  const child = spawn(exe, args, { detached: true, stdio: 'ignore', windowsHide: false });
  child.unref();
  say(`띄웠다 — pid ${child.pid}${profile ? ` · 프로필 ${path.resolve(profile)}` : ''} · ${start}`);
  const deadline = Date.now() + WAIT_MS;
  let v = null;
  while (Date.now() < deadline && !(v && v.Browser)) { await sleep(POLL_MS); v = await version(); }
  if (!(v && v.Browser)) {
    return fail(profile ? 1 : 3, profile
      ? '띄웠는데 포트가 안 열린다 — 그 프로필의 Edge 가 이미 포트 없이 떠 있거나 회사 정책이 막는다. 다음: 사람에게 Edge 를 트레이까지 다 닫아 달라고 한 뒤 다시 부른다 · 그래도 안 서면 멈추고 알린다'
      : '띄웠는데 포트가 안 열린다. 다음: 사람에게 Edge 주소창에 edge://version 을 열어 첫 줄의 판을 읽어 달라고 한다. Chromium 136 이상이면 기본 프로필에 포트를 안 여는 판이다 — ' +
        '그 로그인이 평소 Edge 의 메일 세션을 끊는다고 알리고 동의를 받은 뒤 --profile "$LOCALAPPDATA/ep-login/edge-profile" 로 다시 부른다. 그 아래 판이면 포트 없이 떠 있던 Edge(시작 부스트 · 닫은 뒤 백그라운드 실행)나 회사 정책이 까닭이라 2 처럼 트레이까지 닫아 달라고 한 뒤 다시 부른다');
  }
  say(`포트가 열렸다 — 127.0.0.1:${port} · ${v.Browser}`);
  const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then(r => r.json()).catch(() => []);
  const tab = targets.find(t => t.type === 'page' && t.webSocketDebuggerUrl);
  say(tab ? await watchLogin(tab) : `로그인 탭을 못 찾았다. ${HUMAN}`);
  return 0;
}

function fail(code, message) { console.error(message); return code; }

main(process.argv.slice(2)).then(code => process.exit(code), error => { console.error(error.message); process.exit(1); });
