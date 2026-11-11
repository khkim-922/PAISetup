// 사내 세션을 세우는 대화의 입구 — 스킬 ep-login 이 부르는 하나뿐인 명령. 쓰는 사람의 Edge 에서 세션을 받아 보고(받는 손
// edge_session.js), 안 서면 그 Edge 의 상태에 맞는 로그인을 띄워 지켜본 뒤 다시 받는다. 띄운 창 · 연 탭은 사람이 그대로 쓴다.
//
// 부르는 꼴:
//     node ep_login.js [세션 파일] [domino] [ecm] [--restart] [--profile <폴더>]
//   세션 파일 · domino · ecm — 받는 손에 그대로 넘긴다(뜻은 그 머리말). 받는 손이 ECM 넘김만 화면 없이 못 따라가면(그 손의 4) 탭을
//     잠깐 여는 갈래(--ecm-tab)로 한 번 더 받는다 — 이 명령은 사람이 아는 자리에서만 돌아, 그 탭을 띄우기 전 알림에 함께 싣는다.
//   --restart — 디버깅 포트 없이 도는 Edge 를 이 명령이 다 끝내고 포트로 다시 띄운다. 사람이 동의한 뒤에만 준다(종료 2). 다시 띄운
//     Edge 는 끝낸 탭을 되살리고(--restore-last-session) 로그인 탭 없이 뜬다 — 되살린 사내 탭 하나를 로그인 주소로 넘겨 늘 새로
//     로그인한다(되살린 세션은 포털이 깨져 있어 받아 보지 않는다). 그런 탭이 없을 때만 로그인 탭을 연다.
//   --at-logon — 받아 보기를 건너뛰고 띄우기부터 한다(포트를 연 Edge 가 이미 있으면 여느 차례대로 받는다). 로그온 작업이 곁의
//     edge_start.js 로 부르는 갈래다 — 로그온 직후에는 남은 세션 파일이 살아 있어도 사람이 Edge 를 먼저 열기 전에 포트를 세워야 한다.
//     Edge 가 이미 떠 있으면 아무것도 안 끝내고 종료 2 로 물러난다.
//   --profile — 기본 프로필 대신 그 폴더를 프로필로 띄운다. 기본 프로필로 띄웠는데 포트가 안 열리는 Chromium 136 이상의 Edge(종료 3)
//     에서만, 사람이 동의한 뒤에 준다 — 그 프로필은 평소 Edge 와 쿠키를 안 나눠 그 로그인이 평소 Edge 의 메일 세션을 끊는다.
//   환경변수 EDGE_DEBUG_PORT 포트 · SESSION_LOGIN_HOSTS 로그인 화면 호스트 · SESSION_LOGIN_WAIT_SECONDS 로그인 시한 — 뜻과 기본값은
//   받는 손의 settings 한 자리에서 읽는다. 로그인 화면과 받을 확인 창도 그 손의 onLoginScreen · epConfirm 이 가린다. EP_LOGIN_URL ·
//   COMPANY_LOGIN_URL 은 로그인 탭의 주소를 바꾼다 — 가짜 SSO 로 재는 검사(check_session.js)를 위해 있다.
//
// 차례 — 받는 손의 종료 값(상태)으로 가른다:
//   받는다 → 0 이면 끝
//   3 붙었는데 로그인이 안 됐다 → 그 Edge 에 로그인 탭 하나를 열어 지켜본 뒤 다시 받는다
//   2 붙을 Edge 가 없다 → 포트 없이 도는 Edge 가 있고 --restart 가 없으면 종료 2. --restart 면 끝내고 되살리기만으로 띄워 되살린
//     사내 탭을 로그인 주소로 넘긴다(없으면 로그인 탭을 연다). Edge 가 없으면 포트와 로그인 탭으로 띄운다. 로그인 탭은 지켜본 뒤 다시 받는다
//   4 ECM 만 못 받았다 → --ecm-tab 으로 한 번 더 받는다
// 로그인 탭 — 데스크톱은 회사 SSO 로그인(통합 인증이 입력 없이 넘는다), VDI 는 평소 EP 로그인 화면(사람이 친다). 데스크톱에서
//   탭이 입력 칸 있는 로그인 화면에 FALLBACK_MS 넘게 머물면 통합 인증이 안 선 것이라, 같은 탭을 평소 EP 로그인 화면으로 넘기고
//   사람이 친다. 그 탭에 뜬 SSO 의 「다른 PC에서 EP 접속 정보」 확인 창만 「확인」으로 받는다 — 다른 확인 창 · 다른 탭은 사람의
//   것이라 안 건드린다. 탭이 로그인 화면을 벗어나면 떨어지고, 받기는 로그인 시한 안에서 설 때까지 되풀이한다 — 사람이 다른 탭에서
//   로그인해도 선다.
//
// 내는 것 — 종료 값은 닫힌 다섯이다. 표준 출력은 종료 0 일 때 세션 파일의 절대 경로 한 줄뿐이고, 경과와 「다음: …」 은 표준 오류다:
//   0 세션이 섰다
//   2 포트 없이 도는 Edge 가 있다 — 사람이 동의하면 --restart 로 다시 부른다
//   3 기본 프로필로 띄웠는데 시한 안에 포트가 안 열렸다 — 까닭은 Edge 판으로 갈린다(아래 「다음」)
//   4 로그인 시한 안에 세션이 안 섰다 · 또는 ECM 을 탭으로도 못 받았다 — 「다음」 대로 간다
//   1 그 밖 — Edge 를 못 찾음 · 인자 · Edge 를 못 끝냄 · --profile 로 띄웠는데 포트가 안 열림 · 받는 손의 1
//
// 왜 이렇게 띄우나 — mail-secretary 결정 0009 · 0023 과 그 상주(runner.py 의 EDGE_FLAGS · find_edge · launch_edge)가 회사 데스크톱 ·
//   VDI 에서 잰 길이다: 쓰는 사람의 평소 Edge 를 포트로 띄우고 사람이 그 창에서 한 번 로그인한다. 플래그 둘(포트 · 127.0.0.1)은
//   그대로이고, 상주가 쓰는 --no-startup-window 는 안 쓴다 — 여기서는 그 창에서 바로 로그인한다. 판은 묻지 않고 띄워 본 결과로
//   가린다 — 깔린 폴더에는 아직 적용 안 된 업데이트의 판 폴더가 함께 있어, 폴더 이름의 판은 도는 판이 아니다.
// ⚠ 포트는 이 PC 의 다른 프로그램도 쓸 수 있어 그 Edge 의 세션을 다 다룬다 — 127.0.0.1 에만 연다.
// ⚠ 로그인 탭에는 그 탭의 페이지 자리로만 붙는다 — 브라우저 자리에 자동 붙기를 걸면 SSO 가 여는 팝업(ssoframe)이 디버거를 기다리며
//   멈추고 EP 가 빈 화면에 선다.

'use strict';
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');

// 사내 SSO 의 회사 로그인 — mail-secretary secretary/identity.py 의 COMPANY_LOGIN_PATH · posco/ENV-posco.md 「사내 메일함」.
// ADFS 로 넘어가 데스크톱은 통합 인증으로 입력 없이 서지만, VDI 에서는 처음 보는 ADFS 창이 전체 메일 주소를 받는다
const COMPANY_LOGIN = 'http://swpsso.posco.net/idms/U61/jsp/login/saml_login.jsp?companyCode=shared';
// 평소 EP 로그인 — swp.posco.net 이 보내는 화면(VDI 꼴의 아이디 · 비밀번호 칸). 통합 인증이 안 서는 자리에서 사람이 여기서 친다
const EP_LOGIN = 'http://swpsso.posco.net/idms/U61/jsp/login/login.jsp';
// VMware Horizon VDI 인가 — 에이전트가 세션에 심는 브로커 값 · VDI 도메인
const onVdi = () => Boolean((process.env.ViewClient_Broker_DNS_Name || '').trim()) || /\.VDI$/i.test(process.env.USERDNSDOMAIN || '');
const PORT_MS = 15000;                // 띄운 뒤 포트가 열리기를 기다리는 시한(상주의 EDGE_WAIT_SECONDS 와 같다)
const GONE_MS = 15000;                // --restart 가 끝낸 Edge 가 다 사라지기를 기다리는 시한
const FALLBACK_MS = 8000;             // 입력 칸 있는 로그인 화면에 이만큼 머물면 통합 인증이 안 선 것으로 본다
const RETRY_MS = 3000;                // 로그인 뒤 받기를 되풀이하는 사이
const POLL_MS = 500;
const VERSION_MS = 2000;
const CALL_MS = 5000;                 // CDP 부름 하나의 시한
const CANDIDATES = [                  // 상주 runner.py 의 EDGE_CANDIDATES 와 같은 차례
  [process.env['ProgramFiles(x86)'], 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.ProgramFiles, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.LOCALAPPDATA, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
];
const HAND = path.join(__dirname, 'edge_session.js');
const RECEIVED = { OK: 0, TOOL: 1, NO_EDGE: 2, NOT_LOGGED_IN: 3, ECM_HANDOFF: 4 };   // 받는 손의 종료 값(그 머리말)

// 포트 · 로그인 화면 호스트 · 로그인 시한 · 로그인 화면과 받을 창의 가림은 받는 손이 든다 — 두 손이 같은 자로 가린다
const { settings, onLoginScreen, epConfirm, debugPorts, under, Exit } = require('./edge_session.js');
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

// 도는 Edge 가 있나 — 수만 센다(명령줄은 안 읽는다)
function edgeRunning() {
  try {
    const out = execFileSync('tasklist', ['/FI', 'IMAGENAME eq msedge.exe', '/FO', 'CSV', '/NH'], { encoding: 'utf8', windowsHide: true });
    return out.split(/\r?\n/).some(line => /^"msedge\.exe"/i.test(line));
  } catch { return false; }
}

// --restart — 이 사용자의 Edge 프로세스를 다 끝내고 다 사라질 때까지 본다. 내는 것: 다 사라졌나
async function endEdge() {
  try { execFileSync('taskkill', ['/IM', 'msedge.exe', '/T', '/F'], { stdio: 'ignore', windowsHide: true }); } catch {}
  const deadline = Date.now() + GONE_MS;
  while (Date.now() < deadline) {
    if (!edgeRunning()) return true;
    await sleep(POLL_MS);
  }
  return !edgeRunning();
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

// 로그인 탭을 고른다 — 띄운 Edge 는 되살린 탭도 함께 연다. 로그인 주소 · 로그인 화면 · 로그인 화면 호스트의 다른 화면(넘김 도중)
// 차례로 찾는다 — 넘김 도중의 탭을 놓치면 뒤이어 뜨는 「EP 접속 정보」 창을 받을 손이 없다. 셋 다 아니면 이미 넘어갔다
async function loginTab(port, start) {
  const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then(r => r.json()).catch(() => []);
  const pages = targets.filter(t => t.type === 'page' && t.webSocketDebuggerUrl);
  const onLoginHost = url => { try { return cfg.loginHosts.includes(new URL(url).hostname.toLowerCase()); } catch { return false; } };
  return pages.find(t => t.url === start) || pages.find(t => onLoginScreen(t.url, cfg)) || pages.find(t => onLoginHost(t.url)) || null;
}

// 다시 띄운 Edge 의 로그인 탭 — 회사 도메인 · 로그인 화면 호스트에 선 되살린 탭 하나(로그인 화면에 선 것이 먼저)를 로그인 주소
// (start)로 넘겨 쓴다. 되살린 사내 탭은 끝내기 전 화면을 다시 그릴 뿐 그 세션을 믿을 수 없다 — 되살린 쿠키로 메일 · ECM 은 서도
// 포털 서버의 세션은 깨져 404 · 500 을 낸다. 그런 탭이 없거나 붙지 못하면 로그인 탭을 연다 — 사내 탭을 둔 채 새 탭을 열면 같은
// 포털 탭이 둘 남는다. 내는 것: 지켜볼 탭
async function restoredLoginTab(port, start) {
  const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then(r => r.json()).catch(() => []);
  const pages = targets.filter(t => t.type === 'page' && t.webSocketDebuggerUrl);
  const inCompany = url => { try { const h = new URL(url).hostname.toLowerCase(); return under(h, cfg.domain) || cfg.loginHosts.includes(h); } catch { return false; } };
  const tab = pages.find(t => t.url === start) || pages.find(t => onLoginScreen(t.url, cfg)) || pages.find(t => inCompany(t.url));
  if (tab && tab.url === start) return tab;
  const page = tab && await attachPage(tab.webSocketDebuggerUrl);
  if (!page) return openTab(port, start);
  try { await page.call('Page.navigate', { url: start }); } finally { page.close(); }
  return { ...tab, url: start };
}

// 포트가 열린 Edge 에 로그인 탭을 하나 연다(앞쪽 탭 — 사람이 볼 자리다)
async function openTab(port, start) {
  return fetch(`http://127.0.0.1:${port}/json/new?${start}`, { method: 'PUT' }).then(r => r.json()).catch(() => null);
}

// 로그인 탭을 지켜본다 — 로그인 화면의 EP 접속 정보 창만 「확인」으로 받고, 통합 인증이 안 서면 평소 EP 로그인 화면으로 넘기고,
// 탭이 로그인 화면을 벗어나거나 시한이 지나면 떨어진다. 내는 것: 넘어갔나
async function watchLogin(tab, deadline, fallback) {
  const page = await attachPage(tab.webSocketDebuggerUrl);
  if (!page) { say('로그인 탭에 못 붙었다 — 받기만 되풀이한다'); return false; }
  try {
    let url = tab.url;
    let accepted = 0;
    page.on(m => {
      if (m.method === 'Page.frameNavigated' && !m.params.frame.parentId) url = m.params.frame.url;
      if (m.method === 'Page.javascriptDialogOpening' && epConfirm(m.params.type, m.params.message, m.params.url || url, cfg)) {
        accepted++;
        page.call('Page.handleJavaScriptDialog', { accept: true });
      }
    });
    await page.call('Page.enable');                  // 붙기 전에 이미 떠 있던 창도 이것이 다시 알린다
    let typingSince = 0;
    let fellBack = !fallback;
    while (Date.now() < deadline) {
      const now = await page.call('Runtime.evaluate', {
        expression: '[location.href, !!document.querySelector("input[type=password],input[type=email]")]', returnByValue: true });
      const value = now.result && now.result.result && now.result.result.value;
      if (Array.isArray(value)) url = value[0];
      const onLogin = Boolean(url) && onLoginScreen(url, cfg);
      if (url && /^https?:/i.test(url) && !onLogin) {
        say(`로그인 탭이 넘어갔다 — ${new URL(url).host}${accepted ? ' · 「EP 접속 정보」 창을 「확인」으로 받았다(다른 자리에서 연 메일의 세션이 끊긴다)' : ''}`);
        return true;
      }
      const typing = onLogin && Array.isArray(value) && value[1];
      typingSince = typing ? typingSince || Date.now() : 0;
      if (!fellBack && typingSince && Date.now() - typingSince > FALLBACK_MS) {
        fellBack = true;
        say('통합 인증이 안 섰다 — 같은 탭을 평소 EP 로그인 화면으로 넘긴다. 사람이 그 창에서 평소 아이디로 로그인한다');
        await page.call('Page.navigate', { url: fallback });
      }
      await sleep(POLL_MS);
    }
    return false;
  } finally {
    page.close();                                    // 탭 자리의 연결만 끊는다 — 탭과 창은 사람이 쓴다
  }
}

// ── 띄우기 ───────────────────────────────────────────────────────────────

// Edge 를 포트로 띄운다 — start 가 있으면 그 로그인 탭 하나와 함께. 내는 것: 열린 포트 · 못 열었으면 Exit
async function launch(exe, start, { profile, restore }) {
  const args = [`--remote-debugging-port=${cfg.port}`, '--remote-debugging-address=127.0.0.1'];
  if (profile) args.push(`--user-data-dir=${path.resolve(profile)}`, '--no-first-run');
  if (restore) args.push('--restore-last-session');   // 끝낸 탭을 「페이지 복원」 없이 되살린다
  if (start) args.push(start);
  const child = spawn(exe, args, { detached: true, stdio: 'ignore', windowsHide: false });
  child.unref();
  say(`Edge 를 띄웠다 — pid ${child.pid}${profile ? ` · 프로필 ${path.resolve(profile)}` : ''} · ${start || '끝낸 탭만 되살린다'}`);
  const deadline = Date.now() + PORT_MS;
  while (Date.now() < deadline) {
    await sleep(POLL_MS);
    const v = await version(cfg.port);
    if (v && v.Browser) { say(`포트가 열렸다 — 127.0.0.1:${cfg.port} · ${v.Browser}`); return cfg.port; }
  }
  if (profile) {
    throw new Exit(1, '띄웠는데 포트가 안 열린다 — 그 프로필의 Edge 가 이미 포트 없이 떠 있거나 회사 정책이 막는다. 다음: 멈추고 이 말을 사람에게 그대로 전한다');
  }
  throw new Exit(3, '띄웠는데 포트가 안 열린다. 다음: 사람에게 Edge 주소창에 edge://version 을 열어 첫 줄의 판을 읽어 달라고 한다. ' +
    'Chromium 136 이상이면 기본 프로필에 포트를 안 여는 판이다 — 그 창의 로그인이 평소 Edge 의 메일 세션을 끊는다고 알리고 동의를 받은 뒤 ' +
    '--profile "$LOCALAPPDATA/ep-login/edge-profile" 을 붙여 다시 부른다. 그 아래 판이면 포트 없이 떠 있던 Edge(시작 부스트 · 닫은 뒤 ' +
    '백그라운드 실행)나 회사 정책이 까닭이다 — 사람에게 그 설정을 끌지 묻는다');
}

// ── 갈래 ─────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const opts = { pass: [], restart: false, profile: '', atLogon: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--restart') opts.restart = true;
    else if (argv[i] === '--at-logon') opts.atLogon = true;
    else if (argv[i] === '--profile') { opts.profile = argv[++i] || ''; if (!opts.profile) throw new Exit(1, '--profile 뒤에 폴더를 준다'); }
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

  // 로그온 갈래는 입구의 포트만 본다 — 포트 찾기(PowerShell)가 사람이 Edge 를 먼저 열 틈을 만들지 않게
  let got = opts.atLogon && !await version(cfg.port) ? { code: RECEIVED.NO_EDGE, file: '', said: '' } : await receiveAll(opts.pass);
  if (settled(got)) return finish(got);

  const deadline = Date.now() + cfg.loginMs;
  let port, tab;
  if (got.code === RECEIVED.NOT_LOGGED_IN) {
    // 포트가 열린 Edge 에 로그인이 끊겼다 — 그 Edge 에 로그인 탭을 연다
    port = await openPort();
    if (!port) throw new Exit(1, '받는 손은 붙었다는데 포트를 연 Edge 를 못 찾았다');
    say(`Edge(127.0.0.1:${port})에 로그인이 안 됐다 — 로그인 탭을 연다`);
    tab = await openTab(port, start);
  } else {
    // 붙을 Edge 가 없다 — 띄운다. 포트 없이 도는 Edge 는 사람의 동의 없이 안 끝낸다
    const exe = findEdge();
    if (!exe) throw new Exit(1, 'Edge 를 못 찾았다');
    if (!opts.profile && edgeRunning()) {
      if (!opts.restart) {
        throw new Exit(2, 'Edge 가 디버깅 포트 없이 돌고 있다 — 떠 있는 Edge 에는 포트를 못 연다. 다음: 사람에게 까닭을 알리고, Edge 를 이쪽이 다 ' +
          '끝내고 다시 띄워도 되는지 묻는다(열린 탭은 다시 뜬 Edge 가 되살리지만 저장 안 한 입력은 잃을 수 있다). 동의하면 --restart 를 붙여 다시 부르고, ' +
          '사람이 손수 닫겠다면 창과 알림 영역(트레이)의 Edge 를 다 닫은 뒤 그대로 다시 부른다');
      }
      say('Edge 를 다 끝낸다(사람이 동의했다)');
      if (!await endEdge()) {
        throw new Exit(1, 'Edge 를 끝냈는데 다시 뜬다 — Edge 가 뒤에서 사는 설정(시작 부스트 · 닫은 뒤에도 백그라운드 실행)이 켜졌을 수 있다. 다음: 사람에게 그 설정을 끌지 묻는다');
      }
    }
    if (opts.restart) {
      // 되살린 세션으로 받아 보지 않는다 — 되살린 쿠키로 메일 · ECM 이 서도 포털은 깨져 있어, 받아 보면 0 으로 끝나 사람에게 깨진
      // 포털만 남는다. 로그인 탭 없이 띄우고 되살린 사내 탭을 로그인 주소로 넘겨 새로 로그인한다
      port = await launch(exe, '', { profile: opts.profile, restore: true });
      say(`다시 띄운 Edge(127.0.0.1:${port})의 되살린 사내 탭을 로그인 화면으로 넘긴다 — 되살린 세션은 믿지 않는다`);
      tab = await restoredLoginTab(port, start);
    } else {
      port = await launch(exe, start, { profile: opts.profile, restore: false });
      tab = await loginTab(port, start);
    }
  }

  say(vdi ? '그 창에서 사람이 평소 아이디로 로그인한다 — 이쪽은 로그인이 끝나기를 기다린다' : '로그인 탭을 지켜본다 — 통합 인증이면 입력 없이 넘는다');
  if (tab) await watchLogin(tab, deadline, fallback);
  got = await receiveUntil(opts.pass, deadline);
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

// 명령 한 번 — main 의 종료 값으로 프로세스를 끝낸다. 곧바로 부를 때와 로그온 자리(edge_start.js)가 부를 때 같은 길이다
function run(argv) {
  main(argv).then(code => process.exit(code), error => {
    console.error(error.message);
    process.exit(error instanceof Exit ? error.code : 1);
  });
}

// run 은 로그온 자리가, restoredLoginTab 은 검사(check_session.js)가 쓴다 — --restart 자체는 그 PC 의 Edge 를 다 끝내서 못 잰다
module.exports = { run, restoredLoginTab };

if (require.main === module) run(process.argv.slice(2));
