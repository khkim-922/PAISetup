// 사내 세션을 세우는 대화의 입구 — 스킬 ep-login 이 부르는 하나뿐인 명령. 쓰는 사람의 Edge 에서 세션을 받아 보고(받는 손
// edge_session.js), 안 서면 그 Edge 의 상태에 맞는 로그인을 띄워 지켜본 뒤 다시 받는다. 띄운 창 · 연 탭은 사람이 그대로 쓴다.
//
// 부르는 꼴:
//     node ep_login.js [세션 파일] [domino] [ecm] [--profile <폴더>]
//   세션 파일 · domino · ecm — 받는 손에 그대로 넘긴다(뜻은 그 머리말). 받는 손이 ECM 넘김만 화면 없이 못 따라가면(그 손의 4) 탭을
//     잠깐 여는 갈래(--ecm-tab)로 한 번 더 받는다 — 이 명령은 사람이 아는 자리에서만 돌아, 그 탭을 띄우기 전 알림에 함께 싣는다.
//   --profile — 띄우는 창의 프로필 폴더. 안 주면 PROFILE_DIR(LOCALAPPDATA 아래)이다.
//   환경변수 EDGE_DEBUG_PORT 포트 · SESSION_LOGIN_HOSTS 로그인 화면 호스트 · SESSION_LOGIN_WAIT_SECONDS 로그인 시한 — 뜻과 기본값은
//   받는 손의 settings 한 자리에서 읽는다. 로그인 화면과 받을 확인 창도 그 손의 onLoginScreen · epConfirm 이 가린다. EP_LOGIN_URL ·
//   COMPANY_LOGIN_URL 은 로그인 탭의 주소를 바꾼다 — 가짜 SSO 로 재는 검사(설정 저장소 _check/skills/ep-login/check_session.js)를 위해 있다.
//
// 차례 — 받는 손의 종료 값(상태)으로 가른다:
//   받는다 → 0 이면 끝
//   3 붙었는데 로그인이 안 됐다 → 그 Edge 에 로그인 탭 하나를 열어 지켜본 뒤 다시 받는다
//   2 붙을 Edge 가 없다 → ep-login 프로필의 Edge 창 하나를 포트와 로그인 탭으로 띄워 지켜본 뒤 다시 받는다. 사람의 평소 Edge 는
//     떠 있든 아니든 안 끝낸다 — 끝내면 사람의 창 · 탭 · 쓰던 글이 다 닫힌다
//   4 ECM 만 못 받았다 → --ecm-tab 으로 한 번 더 받는다
// 로그인 탭을 지켜보는 법 · 왜 따로 사는 프로필로 띄우나는 references/DESIGN.md 가 든다.
//
// 내는 것 — 종료 값은 닫힌 셋이다. 표준 출력은 종료 0 일 때 세션 파일의 절대 경로 한 줄뿐이고, 경과와 「다음: …」 은 표준 오류다:
//   0 세션이 섰다
//   4 로그인 시한 안에 세션이 안 섰다 · 또는 ECM 을 탭으로도 못 받았다 — 「다음」 대로 간다
//   1 그 밖 — Edge 를 못 찾음 · 인자 · 띄웠는데 포트가 안 열림 · 받는 손의 1
//
// ⚠ 포트는 이 PC 의 다른 프로그램도 쓸 수 있어 그 Edge 의 세션을 다 다룬다 — 127.0.0.1 에만 연다.
// ⚠ 로그인 탭에는 그 탭의 페이지 자리로만 붙는다 — 브라우저 자리에 자동 붙기를 걸면 SSO 가 여는 팝업(ssoframe)이 디버거를 기다리며
//   멈추고 EP 가 빈 화면에 선다.

'use strict';
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// 사내 SSO 의 회사 로그인 — ADFS 로 넘어가 데스크톱은 통합 인증으로 입력 없이 서지만, VDI 에서는 처음 보는 ADFS 창이 전체 메일 주소를 받는다
const COMPANY_LOGIN = 'http://swpsso.posco.net/idms/U61/jsp/login/saml_login.jsp?companyCode=shared';
// 평소 EP 로그인 — swp.posco.net 이 보내는 화면(VDI 꼴의 아이디 · 비밀번호 칸). 통합 인증이 안 서는 자리에서 사람이 여기서 친다
const EP_LOGIN = 'http://swpsso.posco.net/idms/U61/jsp/login/login.jsp';
// VMware Horizon VDI 인가 — 에이전트가 세션에 심는 브로커 값 · VDI 도메인
const onVdi = () => Boolean((process.env.ViewClient_Broker_DNS_Name || '').trim()) || /\.VDI$/i.test(process.env.USERDNSDOMAIN || '');
// 띄우는 창의 프로필 — 사람의 평소 Edge 와 따로 산다. 로그인 쿠키가 여기 남아, 창을 닫았다 다시 띄워도 세션이 살아 있으면 로그인 없이 받는다
const PROFILE_DIR = path.join(process.env.LOCALAPPDATA || '', 'ep-login', 'edge-profile');
const PORT_MS = 15000;                // 띄운 뒤 포트가 열리기를 기다리는 시한
const FALLBACK_MS = 8000;             // 입력 칸 있는 로그인 화면에 이만큼 머물면 통합 인증이 안 선 것으로 본다
const RETRY_MS = 3000;                // 로그인 뒤 받기를 되풀이하는 사이
const POLL_MS = 500;
const CALL_MS = 5000;                 // CDP 부름 하나의 시한
const CANDIDATES = [                  // Edge 가 깔리는 자리 — 시스템 설치(32 · 64 비트)가 먼저, 사용자 설치가 끝
  [process.env['ProgramFiles(x86)'], 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.ProgramFiles, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.LOCALAPPDATA, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
];
const HAND = path.join(__dirname, 'edge_session.js');
const BLANK = 'about:blank';          // 로그인 탭이 붙기 전에 서는 자리 — 로그인 주소는 붙은 뒤에 연다(blankTab)

// 포트 · 로그인 화면 호스트 · 로그인 시한 · 로그인 화면과 받을 창의 가림 · 받는 손의 종료 값(RECEIVED)은 받는 손이 든다 — 두 손이
// 같은 자로 가린다
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

// 로그인 탭을 지켜본다 — 빈 탭에 붙어 창 알림을 켠 뒤 로그인 주소로 넘기고, 로그인 화면의 EP 접속 정보 창만 「확인」으로 받고,
// 통합 인증이 안 서면 평소 EP 로그인 화면으로 넘기고, 탭이 로그인 화면을 벗어나거나 시한이 지나면 떨어진다. 내는 것: 넘어갔나
async function watchLogin(port, tab, start, deadline, fallback) {
  const page = await attachPage(tab.webSocketDebuggerUrl);
  if (!page) {
    say('로그인 탭에 못 붙었다 — 주소만 열고 받기를 되풀이한다. 「EP 접속 정보」 창이 뜨면 사람이 「확인」을 누른다');
    await fetch(`http://127.0.0.1:${port}/json/new?${start}`, { method: 'PUT' }).catch(() => null);
    return false;
  }
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
    await page.call('Page.navigate', { url: start });
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

// 그 프로필의 Edge 창 하나를 포트와 빈 탭으로 띄운다(로그인 주소는 붙은 뒤에 연다 — blankTab). 내는 것: 열린 포트 · 못 열었으면 Exit
async function launch(exe, profile) {
  const dir = path.resolve(profile);
  const args = [`--remote-debugging-port=${cfg.port}`, '--remote-debugging-address=127.0.0.1', `--user-data-dir=${dir}`,
    '--no-first-run', '--no-default-browser-check', BLANK];
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
  if (settled(got)) return finish(got);

  const deadline = Date.now() + cfg.loginMs;
  let port, tab;
  if (got.code === RECEIVED.NOT_LOGGED_IN) {
    // 포트가 열린 Edge 에 로그인이 끊겼다 — 그 Edge 에 로그인 탭을 연다
    port = await openPort();
    if (!port) throw new Exit(1, '받는 손은 붙었다는데 포트를 연 Edge 를 못 찾았다');
    say(`Edge(127.0.0.1:${port})에 로그인이 안 됐다 — 로그인 탭을 연다`);
    tab = await blankTab(port, false);
  } else {
    // 붙을 Edge 가 없다 — ep-login 프로필의 창 하나를 띄운다. 사람의 평소 Edge 는 떠 있어도 안 건드린다
    const exe = findEdge();
    if (!exe) throw new Exit(1, 'Edge 를 못 찾았다');
    port = await launch(exe, opts.profile);
    tab = await blankTab(port, true);
  }

  say(vdi ? '그 창에서 사람이 평소 아이디로 로그인한다 — 이쪽은 로그인이 끝나기를 기다린다' : '로그인 탭을 지켜본다 — 통합 인증이면 입력 없이 넘는다');
  if (tab) await watchLogin(port, tab, start, deadline, fallback);
  else say('로그인 탭을 못 열었다 — 받기만 되풀이한다');
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

// 명령 한 번 — main 의 종료 값으로 프로세스를 끝낸다
function run(argv) {
  main(argv).then(code => process.exit(code), error => {
    console.error(error.message);
    process.exit(error instanceof Exit ? error.code : 1);
  });
}

if (require.main === module) run(process.argv.slice(2));
