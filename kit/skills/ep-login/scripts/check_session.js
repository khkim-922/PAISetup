// edge_session.js 의 계약을 가짜 SSO · 가짜 메일함 · 가짜 ECM 과 이 검사가 띄운 Edge(임시 프로필 · 창 없음)로 잰다 —
// 127.0.0.1 · localhost 밖으로 아무것도 안 나가고, 쓰는 사람의 Edge 에는 붙지 않는다.
//
// 층 — 쓰는 사람의 계약. 세션 파일에 회사 밖 사이트 · 로그인 화면의 쿠키가 새나(사람의 다른 세션 열쇠가 파일로 나간다) · 붙는 손이
// 사람의 탭을 건드리나(확인 창을 닫는다 · 탭을 남긴다) · 확인 창이 뜬 탭 하나에 붙기가 멈추나 · 종료 값이 닫힌 넷의 뜻대로 나오나
// (부르는 스킬이 그 값으로 사람에게 무엇을 할지 고른다) · ECM 을 이미 산 세션 위에서 다시 넘나 · 저장소 안에 열쇠를 쓰나.
// 남기는 까닭(check-design §1 넷) — 길이 분명하다(Edge 는 프로필의 모든 사이트 쿠키를 내고, Playwright 로 붙으면 사람의 확인 창이
// 닫히고 붙기가 멈추는 것을 이 PC 에서 쟀다) · 새는 쿠키와 닫힌 확인 창은 조용하고 되돌릴 수 없다 · 사람의 다른 세션이 남의 손에
// 가거나 사람이 고르던 창이 사라진다 · 다른 무엇도 안 잡는다(회사 SSO 는 회사 PC 에서만 닿고, 형제 저장소의 검사는 이 손을 안 돈다).
//
// 가짜의 꼴 — ECM 은 2026-11-06 이 PC 실물의 넘김이다(redirect.jsp?redir_url=index.jsp — action 이 빈 폼을 스크립트가 채워 POST ·
// ssoToken → index.jsp 가 jID · login.do 주소를 스크립트에 든다 → login.do…&USE_WEBSOCKET=F(302) → 메인 · 세션 없는 메인은
// 302 → /ECM/logout.jsp). 로그인 화면은 mail-secretary 의 docs/company-facts.md 「로그인」이고,
// 끊긴 메일 세션의 답(200 에 SSO 로 보내는 HTML)은 그 저장소 _check/_fake_domino.py 의 LOGIN_PAGE 꼴이다. 이 파일은
// edge_session.js 의 값을 읽어 오지 않는다 — 걸러 남길 쿠키의 표는 그 머리말 「무엇을 파일에 남기나」가 원본이다.
//
// 돌리는 법:
//     node check_session.js [edge_session.js 가 든 폴더]
//   폴더를 안 주면 이 파일의 폴더를 잰다. 일부러 틀린 사본을 다른 폴더에 두고 그 폴더를 주면 물림(검사가 정말 무나)을 잰다.
//   Node 22 이상 · Edge. --launch 판은 전역 playwright 를 쓴다(NODE_PATH 가 없으면 npm root -g 로 채운다).
//
// 판정 — 끝 줄이 「통과 N/N」 이면 종료 0, 하나라도 어긋나면 1, Edge 를 못 찾거나 못 띄우는 등 재지 못했으면 2.
//
// 언제 걷나 — edge_session.js 가 사라지거나, 같은 계약을 실물 회사 SSO 에서 재는 검사가 서서 이 검사가 더하는 믿음이 없어지면.
//
// 여기서 못 재는 것 — 실물 SSO 의 넘김 꼴(폼이 정적인가 · 스크립트가 짓는가 · Referer 를 보나) · 기본 프로필의 136 선 · 사람이
// 화면을 보는 창(검사의 Edge 는 창이 없다) · 회사 PC 의 Node 판. 이 줄들은 README 「회사에서 잴 것」이 든다.

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const { spawn, execSync } = require('child_process');

const TREE = (() => { const p = path.resolve(process.argv[2] || __dirname); return fs.statSync(p).isDirectory() ? p : path.dirname(p); })();
const HAND = path.join(TREE, 'edge_session.js');
const DB = '/02/mail2/000000.nsf';
const ECM_MAIN = '/ECM/jsp/main/ecmMain.jsp';
const EP_DIALOG = '다른 PC에서 EP 접속 정보가 있어 안내드립니다';
const HAND_MS = 90000;
const sleep = ms => new Promise(r => setTimeout(r, ms));

const results = [];
function judge(name, ok, detail = '') {
  results.push(ok);
  console.log(`${ok ? '맞다' : '어긋났다'} — ${name}${ok || !detail ? '' : ` · ${detail}`}`);
}
class Cannot extends Error {}
function cannot(why) { throw new Cannot(why); }   // 정리(finally)를 지난 뒤 종료 2 로 끝난다

// ── 가짜 사내망 ──────────────────────────────────────────────────────────
// SSO 는 localhost, 메일함 · ECM 은 127.0.0.1 — 호스트가 달라야 「로그인 화면의 쿠키를 안 남긴다」를 잰다

const world = { sso: new Set(), dom: new Set(), ecm: new Set(), relay: new Set(), jid: new Set(), ssoHits: 0, epDialog: false, jsForm: false, n: 0 };
const token = prefix => `${prefix}-${++world.n}`;
const cookies = req => Object.fromEntries((req.headers.cookie || '').split(/;\s*/).filter(Boolean).map(p => [p.slice(0, p.indexOf('=')), p.slice(p.indexOf('=') + 1)]));
const body = req => new Promise(res => { let s = ''; req.on('data', c => s += c); req.on('end', () => res(new URLSearchParams(s))); });
const html = (res, text, headers = {}) => { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', ...headers }); res.end(text); };
const go = (res, to, headers = {}) => { res.writeHead(302, { Location: to, ...headers }); res.end(); };

let SSO = '', APP = '';

function ssoServer(req, res) {
  const url = new URL(req.url, SSO);
  const sid = cookies(req).SSOTOKEN;
  const live = sid && world.sso.has(sid);
  if (url.pathname === '/idms/U61/jsp/login/login.jsp') {
    const to = url.searchParams.get('to') || '';
    if (live) return go(res, `${to}${to.includes('?') ? '&' : '?'}t=${encodeURIComponent(sid)}`);
    // 사내 로그인 화면 — 암호 칸이 있다. 가짜는 통합 인증처럼 스스로 넘는다(사람 손 흉내). EP 접속 정보 창은 사람이 고른다
    const submit = 'document.getElementById("f").submit()';
    const script = world.epDialog ? `if (confirm(${JSON.stringify(EP_DIALOG)})) ${submit};` : submit;
    return html(res, `<form id="f" method="post" action="/dologin"><input name="id" value="me"><input type="password" name="pw" value="x">` +
      `<input type="hidden" name="to" value="${to}"></form><script>setTimeout(function(){${script}}, 300)</script>`);
  }
  if (url.pathname === '/dologin' && req.method === 'POST') {
    return body(req).then(form => {
      const fresh = token('sso');
      world.sso.add(fresh);
      const to = form.get('to') || '/';
      go(res, `${to}${to.includes('?') ? '&' : '?'}t=${encodeURIComponent(fresh)}`, { 'Set-Cookie': `SSOTOKEN=${fresh}; Path=/; HttpOnly` });
    });
  }
  if (url.pathname === '/idms/U61/jsp/redirect.jsp') {
    world.ssoHits++;
    const redir = url.searchParams.get('redir_url') || '';
    if (!live) return html(res, `<form method="post" action="/dologin"><input name="id"><input type="password" name="pw"><input type="hidden" name="to" value="${redir}"></form>`);
    // SSO 는 넘길 때마다 제 토큰을 갈아 준다 — 손이 받은 새 토큰을 Edge 에 되쓰지 않으면 사람의 Edge 가 옛 토큰을 든다
    world.sso.delete(sid);
    const fresh = token('sso');
    world.sso.add(fresh);
    const relay = token('relay');
    world.relay.add(relay);
    const entry = redir || `${APP}/ECM/index.jsp`;
    const set = { 'Set-Cookie': `SSOTOKEN=${fresh}; Path=/; HttpOnly` };
    if (world.jsForm) {
      return html(res, `<html><body><script>var f=document.createElement("FORM");f.method="post";f.action=${JSON.stringify(entry)};` +
        `var i=document.createElement("INPUT");i.type="hidden";i.name="ssoToken";i.value=${JSON.stringify(relay)};f.appendChild(i);` +
        `document.body.appendChild(f);f.submit();</script></body></html>`, set);
    }
    // 실물 꼴 — action 은 비었고, 스크립트가 숨은 칸 redir_url 의 title 을 action 에 넣어 제출한다
    return html(res, `<html><script>function go(){document.frmLogin.action=encodeURI(document.all.redir_url.title);document.frmLogin.submit();}</script>` +
      `<body onload="go()"><form name="frmLogin" action="" method="post"><input type="hidden" name="ssoToken" value="${relay}"></form>` +
      `<input type="hidden" id="redir_url" title="${entry}"></body></html>`, set);
  }
  res.writeHead(404); res.end();
}

function appServer(req, res) {
  const url = new URL(req.url, APP);
  const c = cookies(req);
  if (url.pathname === `${DB}/XML_Inbox` && url.search.startsWith('?ReadViewEntries')) {
    if (c.DomAuthSessId && world.dom.has(c.DomAuthSessId)) {
      res.writeHead(200, { 'Content-Type': 'text/xml; charset=UTF-8' });
      return res.end('<?xml version="1.0"?><viewentries toplevelentries="0"></viewentries>');
    }
    const back = `${APP}/federate?back=${encodeURIComponent(APP + req.url)}`;
    return html(res, `<html><head><script>window.location.href="${SSO}/idms/U61/jsp/login/login.jsp?to=${encodeURIComponent(back)}";</script></head><body></body></html>`);
  }
  if (url.pathname === '/common/lib_f.nsf/checksessionstatus') {
    // 사내 세션 확인의 산 답(company-facts 「세션 확인」). 끊긴 답은 안 쟀다 — 가짜는 메일 목록처럼 SSO 로 보내는 HTML 을 준다
    if (c.DomAuthSessId && world.dom.has(c.DomAuthSessId)) { res.writeHead(200, { 'Content-Type': 'application/json' }); return res.end('{"status":"login"}'); }
    const back = `${APP}/federate?back=${encodeURIComponent(APP + req.url)}`;
    return html(res, `<html><head><script>window.location.href="${SSO}/idms/U61/jsp/login/login.jsp?to=${encodeURIComponent(back)}";</script></head><body></body></html>`);
  }
  if (url.pathname === '/federate') {
    if (!world.sso.has(url.searchParams.get('t'))) return html(res, '<p>no</p>');
    const dom = token('dom');
    world.dom.add(dom);
    return go(res, url.searchParams.get('back') || `${DB}/`, { 'Set-Cookie': `DomAuthSessId=${dom}; Path=/` });
  }
  if (url.pathname === ECM_MAIN) {
    // 산 메인 화면은 제 주소로 되보내는 폼을 든다 — 손이 다다른 뒤에도 폼을 따라가면 걸음 상한에 걸린다
    if (c.JSESSIONID && world.ecm.has(c.JSESSIONID)) return html(res, '<html><body>ECM main<form name="o" method="post" action=""></form><script>document.o.submit()</script></body></html>');
    return go(res, '/ECM/logout.jsp');
  }
  if (url.pathname === '/ECM/logout.jsp') return html(res, '<script>alert("세션이 종료되었습니다")</script>');
  // 실물 꼴 — SSO 토큰을 받은 첫 화면이 jID 와 login.do 주소를 스크립트에 들고, 에이전트 웹소켓이 없으면 USE_WEBSOCKET=F 로 넘긴다
  if (url.pathname === '/ECM/index.jsp' && req.method === 'POST') {
    return body(req).then(form => {
      if (!world.relay.delete(form.get('ssoToken'))) return html(res, '<p>bad token</p>');
      const jid = token('jid');
      world.jid.add(jid);
      // 브라우저 갈래는 에이전트 없이 넘는 실물의 끝(USE_WEBSOCKET=F)만 흉내 낸다 — 이 PC 의 진짜 에이전트(8383)에 닿지 않게
      html(res, `<script>var contextPath = "/ECM"; var jID\t= "${jid}"; function IsWebSocket(){` +
        `window.location.href = contextPath + actionUrl + "&USE_WEBSOCKET=F&JID=" + jID + "&HID=";}</script><body onload="IsWebSocket();"></body>` +
        `<script> actionUrl = '/login.do?ServiceName=login-service&SESSION_ID=${jid}'</script>`);
    });
  }
  if (url.pathname === '/ECM/login.do') {
    if (url.searchParams.get('USE_WEBSOCKET') !== 'F' || !world.jid.delete(url.searchParams.get('JID'))) return html(res, '<p>no</p>');
    const id = token('ecm');
    world.ecm.add(id);
    return go(res, ECM_MAIN, { 'Set-Cookie': `JSESSIONID=${id}; Path=/ECM` });
  }
  if (url.pathname === '/dialog') return html(res, `<script>setTimeout(function(){document.title="answered:"+confirm("person's own question")}, 300)</script>`);
  res.writeHead(404); res.end();
}

const listen = (handler, host) => new Promise(res => { const s = http.createServer(handler).listen(0, host, () => res(s)); });

// ── 검사가 띄우는 Edge ─────────────────────────────────────────────────────

function findEdge() {
  for (const base of [process.env['ProgramFiles(x86)'], process.env.ProgramFiles, process.env.LOCALAPPDATA]) {
    const exe = base && path.join(base, 'Microsoft', 'Edge', 'Application', 'msedge.exe');
    if (exe && fs.existsSync(exe)) return exe;
  }
  return '';
}

async function freePort() {
  const s = await listen(() => {}, '127.0.0.1');
  const port = s.address().port;
  await new Promise(r => s.close(r));
  return port;
}

async function cdp(wsUrl) {
  const ws = new WebSocket(wsUrl);
  const waiting = new Map();
  let id = 0;
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); } };
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  const call = (method, params = {}) => new Promise(res => { waiting.set(++id, res); ws.send(JSON.stringify({ id, method, params })); });
  return { call, close: () => ws.close() };
}

async function startEdge(exe, profile) {
  const port = await freePort();
  const child = spawn(exe, [`--remote-debugging-port=${port}`, '--remote-debugging-address=127.0.0.1', `--user-data-dir=${profile}`,
    '--headless=new', '--no-first-run', '--no-default-browser-check', 'about:blank'], { stdio: 'ignore' });
  for (let i = 0; i < 60; i++) {
    const v = await fetch(`http://127.0.0.1:${port}/json/version`).then(r => r.json()).catch(() => null);
    if (v && v.webSocketDebuggerUrl) return { port, child, browser: await cdp(v.webSocketDebuggerUrl) };
    await sleep(500);
  }
  child.kill();
  return null;
}

const pages = async edge => (await edge.browser.call('Target.getTargets')).result.targetInfos.filter(t => t.type === 'page');
const edgeCookies = async edge => (await edge.browser.call('Storage.getCookies')).result.cookies;

async function waitFor(fn, ms = 15000) {
  const deadline = Date.now() + ms;
  while (Date.now() < deadline) { if (await fn()) return true; await sleep(250); }
  return false;
}

// 사람이 그 Edge 에서 로그인한다 — 탭 하나로 메일 목록을 열면 가짜 로그인 화면이 스스로 넘는다. 넘은 뒤 그 탭을 닫는다
async function personLogsIn(edge) {
  const { result } = await edge.browser.call('Target.createTarget', { url: `${APP}${DB}/XML_Inbox?ReadViewEntries&count=1` });
  const ok = await waitFor(async () => (await edgeCookies(edge)).some(c => c.name === 'DomAuthSessId' && world.dom.has(c.value)));
  await edge.browser.call('Target.closeTarget', { targetId: result.targetId });
  return ok;
}

// ── 손 부르기 ───────────────────────────────────────────────────────────

let NODE_PATH = process.env.NODE_PATH || '';
function hand(args, extra = {}) {
  const inherited = { ...process.env };
  delete inherited.MAILBOX_COOKIES;                  // 이 PC 의 값이 판에 새지 않게 — 판이 주는 값(extra)만 선다
  const env = { ...inherited, NODE_PATH, EDGE_DEBUG_PORT: '1', MAILBOX_URL: `${APP}${DB}`, DOMINO_URL: APP, ECM_URL: `${APP}${ECM_MAIN}`,
    SSO_REDIRECT_URL: `${SSO}/idms/U61/jsp/redirect.jsp`, SESSION_DOMAIN: '127.0.0.1', SESSION_LOGIN_HOSTS: 'localhost',
    SESSION_PASS_SECONDS: '15', SESSION_LOGIN_WAIT_SECONDS: '30', ...extra };
  for (const [k, v] of Object.entries(extra)) if (v === null) delete env[k];
  // 가짜 서버가 이 프로세스에 살아서 기다리는 동안에도 답해야 한다 — spawnSync 로 부르면 서버가 멈춰 손의 묻기가 다 시한에 걸린다
  const t0 = Date.now();
  return new Promise(resolve => {
    const child = spawn(process.execPath, [HAND, ...args], { env });
    let out = '', stdout = '';
    child.stdout.on('data', d => { out += d; stdout += d; });
    child.stderr.on('data', d => out += d);
    const timer = setTimeout(() => child.kill(), HAND_MS);
    child.on('close', code => {
      clearTimeout(timer);
      const lines = stdout.split(/\r?\n/).filter(Boolean);
      resolve({ code, out, last: lines.length ? lines[lines.length - 1] : '', ms: Date.now() - t0 });
    });
  });
}
const fileCookies = file => { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; } };
const names = state => (state && state.cookies || []).map(c => c.name).sort().join(',');

// ── 판정 ─────────────────────────────────────────────────────────────────

function filterTable() {
  let mod;
  try { mod = require(HAND); } catch (e) { return judge('손을 모듈로 읽는다', false, e.message); }
  const cfg = { domain: 'posco.net', loginHosts: ['swpsso.posco.net', 'adfs.m365.posco.net'] };
  // 남길 쿠키의 표 — edge_session.js 머리말 「무엇을 파일에 남기나」: 회사 도메인과 그 아래 · 로그인 화면 호스트의 제 쿠키는 뺀다
  const table = [
    ['.posco.net', true], ['pcfma0b.posco.net', true], ['swpecm.posco.net', true], ['.pcfma0b.posco.net', true],
    ['swpsso.posco.net', false], ['.swpsso.posco.net', false], ['adfs.m365.posco.net', false],
    ['example.com', false], ['.google.com', false], ['evilposco.net', false], ['posco.net.evil.com', false],
  ];
  const wrong = table.filter(([domain, want]) => mod.keep({ name: 'x', value: 'y', domain }, cfg) !== want);
  judge('파일에 남길 쿠키 — 회사 도메인 안만 · 로그인 화면 호스트 · 밖 · 이름만 닮은 도메인은 뺀다', wrong.length === 0, wrong.map(w => w[0]).join(' '));
}

async function main() {
  if (typeof WebSocket !== 'function') cannot(`Node ${process.version} — 22 이상이 든다`);
  if (!fs.existsSync(HAND)) cannot(`잴 손이 없다: ${HAND}`);
  const exe = findEdge();
  if (!exe) cannot('Edge 를 못 찾았다');
  if (!NODE_PATH) { try { NODE_PATH = execSync('npm root -g', { encoding: 'utf8' }).trim(); } catch {} }
  const ssoServerHandle = await listen(ssoServer, 'localhost');
  const appServerHandle = await listen(appServer, '127.0.0.1');
  SSO = `http://localhost:${ssoServerHandle.address().port}`;
  APP = `http://127.0.0.1:${appServerHandle.address().port}`;
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'check-session-'));
  const file = path.join(scratch, 'home', 'session.json');
  let edge = null;
  try {
    filterTable();

    // 포트가 없고 남은 파일도 없다 → 2
    const closed = String(await freePort());
    let r = await hand([file], { EDGE_DEBUG_PORT: closed });
    judge('못 붙고 남은 파일이 없다 → 종료 2 · 경로 줄이 없다', r.code === 2 && r.last === '', `종료 ${r.code} · 끝 줄 ${r.last} · ${r.out.trim()}`);

    edge = await startEdge(exe, path.join(scratch, 'profile'));
    if (!edge) cannot('검사의 Edge 가 디버깅 포트를 안 연다');
    const port = String(edge.port);
    await edge.browser.call('Storage.setCookies', { cookies: [{ name: 'outside', value: 'x', domain: '.example.com', path: '/' }] });

    // 붙었지만 로그인 안 됨 → 3 · 파일을 안 쓴다
    r = await hand([file], { EDGE_DEBUG_PORT: port });
    judge('붙었지만 메일함 로그인이 안 됐다 → 종료 3 · 파일을 안 쓴다', r.code === 3 && !fs.existsSync(file), `종료 ${r.code} · ${r.out.trim()}`);
    r = await hand([file], { EDGE_DEBUG_PORT: port, MAILBOX_URL: null });
    judge('메일함 주소 없이도 Domino 세션 확인으로 가른다 — 로그인 전 → 종료 3', r.code === 3 && !fs.existsSync(file), `종료 ${r.code} · ${r.out.trim()}`);
    r = await hand([file], { EDGE_DEBUG_PORT: port, MAILBOX_URL: 'http://127.0.0.1/no-database' });
    judge('준 메일함 주소가 …/이름.nsf 꼴이 아니다 → 종료 1', r.code === 1, `종료 ${r.code}`);

    // 사람이 로그인하고, 탭 하나에 사람의 확인 창이 떠 있다
    if (!await personLogsIn(edge)) cannot('가짜 로그인이 안 섰다');
    const { result: own } = await edge.browser.call('Target.createTarget', { url: `${APP}/dialog` });
    await sleep(1200);
    const before = (await pages(edge)).length;
    world.ssoHits = 0;
    r = await hand([file, 'domino', 'ecm'], { EDGE_DEBUG_PORT: port });
    const state = fileCookies(file);
    judge('로그인된 Edge → 종료 0 · 메일과 ECM 쿠키를 한 파일에 · 끝 줄이 그 경로', r.code === 0 && names(state) === 'DomAuthSessId,JSESSIONID' && r.last === file,
      `종료 ${r.code} · 쿠키 ${names(state)} · 끝 줄 ${r.last} · ${r.out.trim()}`);
    judge('파일에 회사 밖 · 로그인 화면의 쿠키 · 사이트 저장소가 없다',
      Boolean(state) && !state.cookies.some(c => /example|localhost/.test(c.domain) || c.name === 'SSOTOKEN') && Array.isArray(state.origins) && state.origins.length === 0,
      JSON.stringify(state && state.cookies.map(c => c.domain)));
    judge('확인 창이 뜬 탭이 있어도 붙어서 곧 끝난다', r.code === 0 && r.ms < 15000, `${r.ms}ms`);
    judge('사람의 탭 수가 그대로다(남긴 탭 · 닫은 탭 없음)', (await pages(edge)).length === before, `${before} → ${(await pages(edge)).length}`);
    const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.id === own.targetId);
    const tab = await cdp(target.webSocketDebuggerUrl);
    const blocked = await Promise.race([tab.call('Runtime.evaluate', { expression: 'document.title' }).then(() => false), sleep(1500).then(() => true)]);
    tab.close();
    judge('사람의 확인 창이 그대로 떠 있다(손이 닫지 않았다)', blocked);
    await edge.browser.call('Target.closeTarget', { targetId: own.targetId });
    const browserEcm = (await edgeCookies(edge)).find(c => c.name === 'JSESSIONID');
    const browserSso = (await edgeCookies(edge)).find(c => c.name === 'SSOTOKEN');
    judge('ECM 넘김이 고친 쿠키를 Edge 에도 되썼다(새 ECM 세션 · 갈린 SSO 토큰)',
      Boolean(browserEcm && world.ecm.has(browserEcm.value) && browserSso && world.sso.has(browserSso.value)),
      `ECM ${browserEcm ? world.ecm.has(browserEcm.value) : '없음'} · SSO ${browserSso ? world.sso.has(browserSso.value) : '없음'}`);

    // ECM 세션이 산 Edge 에 또 부른다 → SSO 에 안 간다
    world.ssoHits = 0;
    r = await hand([file, 'domino', 'ecm'], { EDGE_DEBUG_PORT: port });
    judge('ECM 세션이 살아 있으면 SSO 넘김을 다시 안 한다', r.code === 0 && world.ssoHits === 0, `종료 ${r.code} · 넘김 ${world.ssoHits}번`);

    // 메일함 주소 없이(일정 · ECM 이 부르는 꼴) — Domino 세션 확인으로 선다
    r = await hand([file], { EDGE_DEBUG_PORT: port, MAILBOX_URL: null });
    judge('메일함 주소 없이 부르면 Domino 세션 확인으로 선다 → 종료 0', r.code === 0 && r.last === file, `종료 ${r.code} · ${r.out.trim()}`);
    // 경로 없이 부르면 기본 자리 — 머리말의 계약: 세션 파일의 기본은 홈의 .mailbox-session.json · MAILBOX_COOKIES 가 그 앞에 선다
    const home = path.join(scratch, 'fakehome');
    fs.mkdirSync(home, { recursive: true });
    r = await hand([], { EDGE_DEBUG_PORT: port, USERPROFILE: home, HOME: home });
    const fallback = path.join(home, '.mailbox-session.json');
    judge('경로 없이 부르면 홈의 기본 자리에 쓰고 끝 줄로 그 경로를 낸다', r.code === 0 && r.last === fallback && fs.existsSync(fallback), `종료 ${r.code} · 끝 줄 ${r.last}`);
    const envFile = path.join(scratch, 'env', 'session.json');
    r = await hand([], { EDGE_DEBUG_PORT: port, USERPROFILE: home, HOME: home, MAILBOX_COOKIES: envFile });
    judge('경로 없이 MAILBOX_COOKIES 를 주면 그 자리에 쓰고 끝 줄로 낸다', r.code === 0 && r.last === envFile && fs.existsSync(envFile), `종료 ${r.code} · 끝 줄 ${r.last}`);

    // 손이 못 따라가는 넘김(스크립트가 폼을 짓는다)
    world.ecm.clear();
    world.jsForm = true;
    world.ssoHits = 0;
    r = await hand([file], { EDGE_DEBUG_PORT: port });
    judge('ecm 을 안 준 판은 ECM 넘김을 안 한다 · 메일이 서면 종료 0', r.code === 0 && world.ssoHits === 0 && !/ECM —/.test(r.out), `종료 ${r.code} · 넘김 ${world.ssoHits}번 · ${r.out.trim()}`);
    r = await hand([file, 'domino', 'ecm'], { EDGE_DEBUG_PORT: port });
    judge('ECM 을 꼭 서야 하는 앱으로 주면 → 종료 3', r.code === 3, `종료 ${r.code} · ${r.out.trim()}`);
    const beforeTab = (await pages(edge)).length;
    r = await hand([file, 'ecm', '--ecm-tab'], { EDGE_DEBUG_PORT: port });
    const tabState = fileCookies(file);
    judge('--ecm-tab 은 탭 하나로 넘겨 ECM 을 받고 그 탭을 닫는다',
      r.code === 0 && tabState && tabState.cookies.some(c => c.name === 'JSESSIONID' && world.ecm.has(c.value)) && (await pages(edge)).length === beforeTab,
      `종료 ${r.code} · 탭 ${beforeTab} → ${(await pages(edge)).map(p => p.url.replace(APP, "APP").replace(SSO, "SSO")).join(" ")} · ${r.out.trim()}`);
    world.jsForm = false;

    // 못 붙어도 남은 파일이 살면 0 · 파일을 안 고친다 / 죽었으면 2
    const bytes = fs.existsSync(file) ? fs.readFileSync(file, 'utf8') : '';
    r = await hand([file], { EDGE_DEBUG_PORT: closed });
    judge('못 붙었지만 남은 파일이 산다 → 종료 0 · 파일 그대로 · 끝 줄이 그 경로', r.code === 0 && Boolean(bytes) && fs.readFileSync(file, 'utf8') === bytes && r.last === file,
      `종료 ${r.code} · ${r.out.trim()}`);
    world.dom.clear();
    r = await hand([file], { EDGE_DEBUG_PORT: closed });
    judge('못 붙었고 남은 파일도 안 선다 → 종료 2 · 끝 줄이 그 남은 파일의 경로', r.code === 2 && r.last === file, `종료 ${r.code} · 끝 줄 ${r.last} · ${r.out.trim()}`);

    // 저장소 안의 자리는 거절한다
    const repo = path.join(scratch, 'repo');
    fs.mkdirSync(path.join(repo, '.git'), { recursive: true });
    r = await hand([path.join(repo, 'sub', 'session.json')], { EDGE_DEBUG_PORT: port });
    judge('세션 파일 자리가 git 저장소 안이다 → 종료 1 · 안 쓴다', r.code === 1 && !fs.existsSync(path.join(repo, 'sub', 'session.json')), `종료 ${r.code}`);

    // --launch — 임시 프로필 창에서 로그인(EP 접속 정보 창은 로그인 화면에서 「확인」) → 메일 · ECM
    world.sso.clear(); world.dom.clear(); world.ecm.clear();
    world.epDialog = true;
    const launched = path.join(scratch, 'launched.json');
    r = await hand([launched, '--launch'], { EDGE_DEBUG_PORT: closed, SESSION_LAUNCH_HEADLESS: '1' });
    judge('--launch 는 창에서 로그인을 넘겨 메일 · ECM 쿠키를 남긴다 · 끝 줄이 그 경로',
      r.code === 0 && names(fileCookies(launched)) === 'DomAuthSessId,JSESSIONID' && r.last === launched,
      `종료 ${r.code} · 쿠키 ${names(fileCookies(launched))} · ${r.out.trim()}`);
    world.epDialog = false;
    // 새 창 갈래 뒤에도 사람의 Edge 에는 여전히 못 붙는다 — 부르는 쪽의 조용한 부름이 ep-login 으로 되돌아가지 않아야 한다
    r = await hand([launched], { EDGE_DEBUG_PORT: closed });
    judge('새 창 갈래로 받은 파일 — 못 붙어도 그 파일이 살면 종료 0 · 끝 줄이 그 경로', r.code === 0 && r.last === launched, `종료 ${r.code} · ${r.out.trim()}`);
  } finally {
    if (edge) {
      edge.browser.close();
      try { execSync(`taskkill /PID ${edge.child.pid} /T /F`, { stdio: 'ignore' }); } catch {}
    }
    ssoServerHandle.close(); appServerHandle.close();
    await sleep(1500);
    try { fs.rmSync(scratch, { recursive: true, force: true }); } catch {}
  }
  const passed = results.filter(Boolean).length;
  console.log(`${passed === results.length ? '통과' : '어긋남'} ${passed}/${results.length}`);
  process.exit(passed === results.length ? 0 : 1);
}

main().catch(e => { console.log(`못 쟀다 — ${e instanceof Cannot ? e.message : e.stack || e.message}`); process.exit(2); });
