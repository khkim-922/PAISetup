// 쓰는 사람의 Edge 에서 사내 세션(메일 · 일정 · 다른 Domino 앱 · ECM)의 쿠키를 받아 세션 파일로 남긴다 — 사내 앱 스킬의 손이
// 그 파일을 읽는다. 새로 로그인하지 않고 창 · 탭을 열지 않는다(`--ecm-tab` 만 탭 하나를 잠깐 연다). 몇 번을 불러도 같다.
//
// 부르는 꼴:
//     node edge_session.js [세션 파일] [domino] [ecm] [--ecm-tab]
//   세션 파일 — 안 주면 MAILBOX_COOKIES, 그것도 없으면 places.json 의 기본 자리(홈). 부르는 쪽은 인자 없이 부르고 종료 0 의
//     끝 줄에서 경로를 읽는다. git 저장소 안의 자리는 거절한다(종료 1).
//   domino · ecm — 이번에 꼭 서야 하는 앱. 안 주면 domino 다. ECM 세션은 `ecm` 을 준 판에서만 받는다.
//   --ecm-tab — 조용한 ECM 받기가 안 설 때만 쓰는 갈래. 사람의 Edge 에 뒤쪽 탭 하나를 열어 SSO 넘김을 거치고 닫는다 — 사람이
//     아는 자리(입구 ep_login.js)에서만 준다.
//
// 환경변수 — 다 없어도 된다. MAILBOX_URL 메일함 주소(…/<번호>.nsf 까지 · 주면 domino 를 그 목록으로 가린다) ·
//   MAILBOX_VIEW 받은편지함 보기(기본 XML_Inbox) · DOMINO_URL Domino 서버 · ECM_URL ECM 주소(…/ECM 까지 — 스킬 company-ecm 과
//   같은 뜻) · EDGE_DEBUG_PORT 디버깅 포트(쉼표로 여럿 · 주면 그 포트만 본다) · SSO_REDIRECT_URL SSO 넘김 주소 ·
//   SESSION_DOMAIN 회사 도메인 · SESSION_LOGIN_HOSTS 로그인 화면 호스트(쉼표) · SESSION_REQUEST_SECONDS 묻기 하나의 시한 ·
//   SESSION_PASS_SECONDS --ecm-tab 의 시한 · SESSION_LOGIN_WAIT_SECONDS 입구가 로그인 탭을 지켜보는 시한. 기본값은 places.json 과
//   settings() 가 든다. 서버 · 도메인 · 호스트의 바꿈은 가짜 서버로 재는 검사(check_session.js)를 위해 있다.
//
// 내는 것 — 세션 파일(Playwright 저장 상태 꼴 {"cookies": [...], "origins": []} · 회사 도메인의 쿠키만). 종료 0 이면 표준 출력의
//   끝 줄이 그 파일의 절대 경로 하나다(앞 줄들은 사람이 읽는 경과). 종료 값은 닫힌 다섯이다(EXIT):
//   0 파일이 지금 산 세션을 든다 — 새로 썼거나, Edge 에 못 붙었는데 남은 파일이 아직 산다(그때는 파일을 안 고친다)
//   2 Edge 에 못 붙었고 남은 파일로도 안 섰다. 남은 파일이 있으면 그 절대 경로를 끝 줄로 낸다 — 부르는 쪽이 한 번 써 보고 서버가
//     안 받을 때만 ep-login 을 가리킨다
//   3 붙었지만 꼭 서야 하는 앱이 로그인이 안 됐다(ECM 넘김이 로그인 화면에서 멈춘 판도). 파일은 안 고친다
//   4 붙었고 로그인은 섰는데 ECM 만 못 받았다 — 다시 로그인할 일이 아니다. 파일은 안 고친다
//   1 그 밖 — 설정(주소 · 인자 · 저장소 안의 자리) · Node 판 · 도구 고장
//   종료 2 · 3 · 4 는 표준 오류의 끝에 「다음: …」 한 줄을 낸다(1 은 까닭만). 이 값의 뜻을 바꾸면 스킬 ep-login 과 부르는 스킬들을
//   같은 판에 고친다.
// 어느 Edge 에 붙나 · 어떻게 붙나 · ECM 넘김 따라가기 · 무엇을 파일에 남기나는 references/DESIGN.md 가 든다.
//
// ⚠ 세션 파일은 사내 앱의 열쇠다 — 저장소 밖(홈)에 두고 남에게 넘기지 않는다. 다 쓴 PC · 남에게 넘길 PC 에서는 지운다.
// ⚠ 디버깅 포트는 이 PC 의 다른 프로그램도 쓸 수 있다 — 127.0.0.1 에만 열고, 이 손은 127.0.0.1 로만 붙는다.
//
// 필요한 것: Node 22 이상(내장 WebSocket · fetch). npm 꾸러미는 안 든다.

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const https = require('https');

// 회사 자리 값(메일 서버 · ECM 주소 · 세션 파일의 기본 자리) — 형제 스킬의 파이썬 손은 ep_session.py 를 거쳐 같은 파일을 읽는다
const PLACES = require('./places.json');
const SSO_REDIRECT = 'http://swpsso.posco.net/idms/U61/jsp/redirect.jsp';          // SSO 넘김 주소 — redir_url 이 가리키는 앱으로 세션을 넘긴다
const SESSION_CHECK = '/common/lib_f.nsf/checksessionstatus?Openpage';             // Domino 의 세션 확인 주소 — 웹메일이 수십 초마다 부른다
const MAX_HOPS = 12;                 // 따라가기의 걸음 상한 — 정상 넘김보다 넉넉하고, 같은 화면을 도는 넘김은 여기서 끊긴다
const APPS = ['domino', 'ecm'];
const EXIT = { OK: 0, TOOL: 1, NO_EDGE: 2, NOT_LOGGED_IN: 3, ECM_HANDOFF: 4 };   // 종료 값 — 뜻은 머리말 「내는 것」 · 입구가 이 표를 싣는다
// 로그인 화면 — 로그인 화면 호스트 위의 이 경로(SSO 의 …/jsp/login/… · ADFS 의 /adfs/…). 같은 호스트의 넘김(redirect.jsp)은 아니다
const LOGIN_PATH = /\/(login|adfs)\//i;
const EP_DIALOG = '다른 PC에서 EP 접속 정보';   // SSO 가 로그인 도중 띄우는 확인 창의 글 — 이 창만 「확인」으로 받는다
// ECM 넘김이 멈춘 까닭(follow 의 답) → 사람의 말. login 은 여기 없다 — 로그인 화면에 닿은 판은 종료 3 이다
const HANDOFF_WORD = { end: '넘김 화면을 따라가지 못했다', outside: '회사 밖 주소로 넘어갔다', 'no-answer': '서버가 답하지 않았다',
  hops: '넘김이 걸음 상한을 넘었다' };
const DEFAULT_PORT = '9222';         // 입구(ep_login.js)가 여는 포트 — 받는 손도 이 포트를 먼저 본다
const FIND_MS = 5000;                // 디버깅 포트를 연 Edge 찾기(debugPorts 의 PowerShell 한 번)의 시한
const VERSION_MS = 2000;             // 디버깅 포트의 /json/version 답 시한 — 포트가 없으면 곧 끊긴다
const OPEN_MS = 5000;                // 브라우저 자리 웹소켓이 열리는 시한
const CALL_MS = 10000;               // CDP 부름 하나의 시한
const POLL_MS = 1000;                // --ecm-tab 이 선 것을 다시 보는 사이
const CLOSE_ROUNDS = 2;              // --ecm-tab 의 탭 닫기를 되풀이하는 수
const CLOSE_MS = 3000;               // 닫은 탭이 사라지기를 기다리는 시한(한 번마다)
const CLOSE_POLL_MS = 200;

const env = (name, fallback) => (process.env[name] || '').trim() || fallback;
const seconds = (name, fallback) => {
  const value = Number(env(name, String(fallback)));
  return Number.isFinite(value) && value > 0 ? value : fallback;
};

function settings() {
  return {
    port: env('EDGE_DEBUG_PORT', DEFAULT_PORT).split(',')[0].trim(),   // 입구가 Edge 를 띄울 때 여는 포트 · 받는 손이 먼저 보는 포트
    // 받는 손이 볼 포트 — 주면 그것만(쉼표로 여럿), 안 주면 null 이고 이 PC 에서 디버깅 포트를 연 Edge 를 다 찾는다(debugPorts)
    ports: env('EDGE_DEBUG_PORT', '') ? env('EDGE_DEBUG_PORT', '').split(',').map(s => s.trim()).filter(Boolean) : null,
    view: env('MAILBOX_VIEW', 'XML_Inbox'),
    mailbox: env('MAILBOX_URL', ''),
    domino: env('DOMINO_URL', PLACES.domino_server).replace(/\/+$/, ''),
    ecm: env('ECM_URL', PLACES.ecm).replace(/\/+$/, '') + PLACES.ecm_main_page,   // ECM_URL 은 맥락까지(…/ECM) — 스킬 company-ecm 과 같은 뜻
    sso: env('SSO_REDIRECT_URL', SSO_REDIRECT),
    domain: env('SESSION_DOMAIN', 'posco.net').toLowerCase().replace(/^\./, ''),
    loginHosts: env('SESSION_LOGIN_HOSTS', 'swpsso.posco.net,adfs.m365.posco.net').toLowerCase().split(',').map(s => s.trim()).filter(Boolean),
    requestMs: seconds('SESSION_REQUEST_SECONDS', 5) * 1000,
    passMs: seconds('SESSION_PASS_SECONDS', 30) * 1000,
    loginMs: seconds('SESSION_LOGIN_WAIT_SECONDS', 300) * 1000,
  };
}

class Exit extends Error {
  constructor(code, message) { super(message); this.code = code; }
}

// ── 로그인 화면 ──────────────────────────────────────────────────────────
// 입구(ep_login.js)가 로그인 탭을 지켜보며 쓰는 자 — 설정(settings)과 한 자리에 둔다

// 로그인 화면인가 — 로그인 화면 호스트이고 그 경로다
function onLoginScreen(url, cfg) {
  try { const u = new URL(url); return cfg.loginHosts.includes(u.hostname.toLowerCase()) && LOGIN_PATH.test(u.pathname); } catch { return false; }
}

// 로그인 화면 호스트의 화면인가 — 경로는 안 본다
function onLoginHost(url, cfg) {
  try { return cfg.loginHosts.includes(new URL(url).hostname.toLowerCase()); } catch { return false; }
}

// 「확인」으로 받을 창인가 — 로그인 화면 호스트에 뜬 「EP 접속 정보」 확인 창만. 받는 것: 창의 꼴(confirm · alert …) · 글 · 뜬 주소.
// 뜬 주소는 로그인 화면 경로가 아니다 — SSO 는 로그인 화면 안의 틀(manysession.jsp)에서 그 창을 띄운다
function epConfirm(type, message, url, cfg) {
  return type === 'confirm' && String(message || '').includes(EP_DIALOG) && onLoginHost(url, cfg);
}

// ── 쿠키 ─────────────────────────────────────────────────────────────────
// 안의 꼴은 Playwright 저장 상태의 쿠키 꼴이다 — domain 이 「.」으로 시작하면 도메인 쿠키, 아니면 그 호스트에만 실린다(CDP 도 같다)

const bare = domain => String(domain || '').toLowerCase().replace(/^\./, '');

function under(host, domain) {
  host = String(host || '').toLowerCase();
  domain = bare(domain);
  return Boolean(domain) && (host === domain || host.endsWith('.' + domain));
}

// 파일에 남길 쿠키인가 — 회사 도메인 안 · 로그인 화면 호스트가 제 이름으로 받은 것이 아니다
function keep(cookie, cfg) {
  const domain = bare(cookie.domain);
  return under(domain, cfg.domain) && !cfg.loginHosts.includes(domain);
}

function sentTo(cookie, url) {
  const host = url.hostname.toLowerCase();
  const domain = String(cookie.domain || '').toLowerCase();
  const hostMatch = domain.startsWith('.') ? under(host, domain) : host === domain;
  if (!hostMatch) return false;
  if (cookie.secure && url.protocol !== 'https:') return false;
  const cpath = cookie.path || '/';
  const upath = url.pathname || '/';
  if (!(upath === cpath || upath.startsWith(cpath.endsWith('/') ? cpath : cpath + '/'))) return false;
  return !(cookie.expires > 0 && cookie.expires < Date.now() / 1000);
}

function cookieHeader(jar, url) {
  return jar.filter(c => sentTo(c, url)).sort((a, b) => (b.path || '').length - (a.path || '').length)
    .map(c => `${c.name}=${c.value}`).join('; ');
}

// Set-Cookie 한 줄을 받아 통에 넣는다(RFC 6265 5.2 · 5.3 의 꼴). 바뀐 쿠키는 changed 에 남겨 Edge 에 되쓴다
function store(jar, changed, line, url) {
  const [pair, ...attrs] = line.split(';');
  const eq = pair.indexOf('=');
  if (eq <= 0) return;
  const cookie = { name: pair.slice(0, eq).trim(), value: pair.slice(eq + 1).trim(), domain: url.hostname.toLowerCase(),
    path: '', expires: -1, httpOnly: false, secure: false, sameSite: 'Lax' };
  let maxAge = null;
  for (const attr of attrs) {
    const i = attr.indexOf('=');
    const key = (i < 0 ? attr : attr.slice(0, i)).trim().toLowerCase();
    const value = i < 0 ? '' : attr.slice(i + 1).trim();
    if (key === 'domain' && value) {
      if (!under(url.hostname, value)) return;                       // 남의 도메인에 쓰려는 쿠키는 브라우저처럼 버린다
      cookie.domain = '.' + bare(value);
    } else if (key === 'path' && value.startsWith('/')) cookie.path = value;
    else if (key === 'expires') { const t = Date.parse(value); if (!Number.isNaN(t)) cookie.expires = t / 1000; }
    else if (key === 'max-age' && /^-?\d+$/.test(value)) maxAge = Number(value);
    else if (key === 'secure') cookie.secure = true;
    else if (key === 'httponly') cookie.httpOnly = true;
    else if (key === 'samesite') cookie.sameSite = /^strict$/i.test(value) ? 'Strict' : /^none$/i.test(value) ? 'None' : 'Lax';
  }
  if (!cookie.path) {
    const dir = url.pathname.slice(0, url.pathname.lastIndexOf('/'));
    cookie.path = dir || '/';
  }
  if (maxAge !== null) cookie.expires = maxAge <= 0 ? 1 : Date.now() / 1000 + maxAge;
  const same = c => c.name === cookie.name && c.domain === cookie.domain && c.path === cookie.path;
  for (let i = jar.length - 1; i >= 0; i--) if (same(jar[i])) jar.splice(i, 1);
  for (let i = changed.length - 1; i >= 0; i--) if (same(changed[i])) changed.splice(i, 1);
  changed.push(cookie);
  if (!(cookie.expires > 0 && cookie.expires < Date.now() / 1000)) jar.push(cookie);
}

// CDP 의 쿠키 → 저장 상태 꼴. SameSite 가 없으면 Lax — Chromium 이 SameSite 없는 쿠키를 다루는 기본값이다
function fromCdp(c) {
  return { name: c.name, value: c.value, domain: c.domain, path: c.path || '/', expires: c.session ? -1 : c.expires,
    httpOnly: Boolean(c.httpOnly), secure: Boolean(c.secure), sameSite: c.sameSite || 'Lax' };
}

function toCdp(c) {
  const param = { name: c.name, value: c.value, path: c.path, secure: c.secure, httpOnly: c.httpOnly, sameSite: c.sameSite };
  if (c.domain.startsWith('.')) param.domain = c.domain;
  else param.url = `${c.secure ? 'https' : 'http'}://${c.domain}${c.path}`;           // 호스트에만 실리는 쿠키는 url 로 준다
  if (c.expires > 0) param.expires = c.expires;
  return param;
}

// ── 묻기 ─────────────────────────────────────────────────────────────────
// 리다이렉트를 따라가지 않는 GET · POST 하나. 몸은 latin1 로 읽어 바이트를 그대로 둔다(폼 값을 되보낼 때 그 바이트로 보낸다)

function send(cfg, jar, changed, req) {
  const url = new URL(req.url);
  const lib = url.protocol === 'https:' ? https : http;
  const headers = { 'User-Agent': cfg.userAgent || 'Mozilla/5.0', Accept: '*/*' };
  const cookie = cookieHeader(jar, url);
  if (cookie) headers.Cookie = cookie;
  if (req.referer) headers.Referer = req.referer;
  let body = null;
  if (req.body !== undefined && req.body !== null) {
    body = Buffer.from(req.body, 'latin1');
    headers['Content-Type'] = 'application/x-www-form-urlencoded';
    headers['Content-Length'] = body.length;
    if (req.referer) headers.Origin = new URL(req.referer).origin;
  }
  return new Promise(resolve => {
    const r = lib.request(url, { method: req.method || 'GET', headers, timeout: cfg.requestMs }, res => {
      for (const line of [].concat(res.headers['set-cookie'] || [])) store(jar, changed, line, url);
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => resolve({ url, status: res.statusCode, type: String(res.headers['content-type'] || ''),
        location: res.headers.location || '', body: Buffer.concat(chunks).toString('latin1') }));
      res.on('error', () => resolve(null));
    });
    r.on('timeout', () => r.destroy());
    r.on('error', () => resolve(null));
    if (body) r.write(body);
    r.end();
  });
}

const unescape = s => s.replace(/&(amp|quot|#39|apos|lt|gt);/g, (_, e) => ({ amp: '&', quot: '"', '#39': "'", apos: "'", lt: '<', gt: '>' })[e]);
const attr = (tag, name) => {
  const m = new RegExp(`\\b${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s>]+))`, 'i').exec(tag);
  return m ? unescape(m[1] ?? m[2] ?? m[3]) : null;
};
// latin1 글자(바이트 하나씩)를 그대로 퍼센트로 싼다 — 받은 바이트를 바꾸지 않고 되보낸다
const pct = s => Array.from(s, ch => /[A-Za-z0-9\-_.~]/.test(ch) ? ch : '%' + ch.charCodeAt(0).toString(16).toUpperCase().padStart(2, '0')).join('');

// 다음 걸음 — 스스로 제출하는 폼 · location 으로 넘기는 스크립트. 로그인 화면(암호 칸)이면 멈춘다
function nextStep(page) {
  const html = page.body;
  if (/<input[^>]*type\s*=\s*["']?password/i.test(html)) return { stop: 'login' };
  // ECM 첫 화면(index.jsp) — PC 의 ECM 에이전트 웹소켓을 거치지 않는 갈래로 간다. 그 화면이 웹소켓을 못 쓰는 브라우저에 주는
  // 주소(login.do …&USE_WEBSOCKET=F)를 그 화면의 값(actionUrl · jID)으로 짓는다 — 실물 index.jsp 의 IsWebSocket() 갈래
  const ecmAction = /\bactionUrl\s*=\s*'(\/login\.do\?[^']+)'/.exec(html);
  const ecmJid = /\bvar\s+jID\s*=\s*"([^"]+)"/.exec(html);
  if (ecmAction && ecmJid) {
    const context = /\bcontextPath\s*=\s*"([^"]*)"/.exec(html);
    const next = `${context ? context[1] : ''}${ecmAction[1]}&USE_WEBSOCKET=F&JID=${ecmJid[1]}&HID=&WEBSOCKETERRTYPE=DCase`;
    return { method: 'GET', url: new URL(next, page.url).href };
  }
  const form = /<form\b[^>]*>([\s\S]*?)<\/form>/i.exec(html);
  if (form && /\.submit\s*\(\s*\)/.test(html)) {
    const tag = /<form\b[^>]*>/i.exec(form[0])[0];
    const fields = [];
    for (const input of form[1].match(/<input\b[^>]*>/gi) || []) {
      const name = attr(input, 'name');
      const type = (attr(input, 'type') || 'text').toLowerCase();
      if (!name || ['submit', 'button', 'image', 'reset', 'file'].includes(type)) continue;
      if (['checkbox', 'radio'].includes(type) && !/\bchecked\b/i.test(input)) continue;
      fields.push(pct(name) + '=' + pct(attr(input, 'value') || ''));
    }
    // 회사 SSO 넘김 화면은 action 을 비워 두고 스크립트가 숨은 칸 redir_url 의 title 을 action 에 넣어 제출한다 — 빈 action 을 제
    // 주소로 읽으면 같은 화면에 되보내며 돈다
    const redir = /<input\b[^>]*\bid\s*=\s*["']?redir_url\b[^>]*>/i.exec(html);
    const scripted = /\.action\s*=/.test(html) && redir ? attr(redir[0], 'title') : null;
    const target = new URL(attr(tag, 'action') || scripted || page.url.href, page.url);
    if ((attr(tag, 'method') || 'get').toLowerCase() === 'post') return { method: 'POST', url: target.href, body: fields.join('&') };
    target.search = fields.join('&');
    return { method: 'GET', url: target.href };
  }
  const js = /location(?:\.href)?\s*=\s*["']([^"']+)["']|location\.(?:replace|assign)\(\s*["']([^"']+)["']/i.exec(html);
  if (js) return { method: 'GET', url: new URL(unescape(js[1] || js[2]), page.url).href };
  return { stop: 'end' };
}

// 회사 호스트 안에서만 열두 걸음까지 따라간다. 멈춘 까닭을 낸다(끝 · 로그인 · 밖 · 답 없음 · 걸음 초과)
// 같은 화면인가 — 물음표 뒤 · 호스트 대소문자 · 기본 포트 표기는 안 본다
const samePage = (a, b) => a.origin === b.origin && a.pathname === b.pathname;

async function follow(cfg, jar, changed, start, goal = null) {
  let req = { method: 'GET', url: start };
  for (let hop = 0; hop < MAX_HOPS; hop++) {
    const host = new URL(req.url).hostname.toLowerCase();
    if (!under(host, cfg.domain) && !cfg.loginHosts.includes(host)) return 'outside';
    const page = await send(cfg, jar, changed, req);
    if (!page) return 'no-answer';
    if (page.status >= 300 && page.status < 400 && page.location) {
      req = { method: 'GET', url: new URL(page.location, page.url).href, referer: req.referer };
      continue;
    }
    if (page.status !== 200 || !/html/i.test(page.type)) return 'end';
    if (goal && samePage(page.url, goal)) return 'end';  // 다다랐다 — 메인 화면의 폼을 따라 되보내지 않는다
    const step = nextStep(page);
    if (step.stop) return step.stop;
    req = { ...step, referer: page.url.href };
  }
  return 'hops';
}

// ── 앱마다의 확인 ──────────────────────────────────────────────────────────

function listUrl(cfg) {
  const match = /^(https?:\/\/[^/]+\/.+?\.nsf)/i.exec(cfg.mailbox);
  if (!match) throw new Exit(EXIT.TOOL, `MAILBOX_URL 이 메일함 주소(…/이름.nsf)가 아니다: ${cfg.mailbox || '(비었다)'}`);
  return `${match[1]}/${encodeURIComponent(cfg.view)}?ReadViewEntries&count=1`;
}

// Domino — 메일함 주소가 있으면 목록 하나(문서는 안 연다 · 여는 순간 그 메일이 읽음이 된다), 없으면 서버의 세션 확인.
// 끊긴 세션은 200 에 SSO 로 보내는 HTML 이라 상태 코드가 아니라 답의 꼴로 가린다
const dominoUrl = cfg => cfg.mailbox ? listUrl(cfg) : cfg.domino + SESSION_CHECK;
async function dominoStands(cfg, jar, changed) {
  const page = await send(cfg, jar, changed, { url: dominoUrl(cfg) });
  if (!page || page.status !== 200) return false;
  return cfg.mailbox ? /xml/i.test(page.type) : /"status"\s*:\s*"login"/.test(page.body);
}

// ECM — 메인 화면. 세션이 없으면 302 → /ECM/logout.jsp 다
async function ecmStands(cfg, jar, changed) {
  if (!jar.some(c => sentTo(c, new URL(cfg.ecm)))) return false;
  const page = await send(cfg, jar, changed, { url: cfg.ecm });
  return Boolean(page && page.status === 200 && /html/i.test(page.type));
}

// SSO 넘김이 가리킬 ECM 첫 화면 — 메인을 가리키면 곧장 logout 으로 튕기고, 첫 화면(<맥락 경로>/index.jsp)이 세션을 세운다.
// 맥락 경로는 ECM_URL 의 첫 경로 칸이다 — 서버 · 포트 · 맥락을 ECM_URL 한 곳에서만 읽는다
const ecmEntry = cfg => { const u = new URL(cfg.ecm); return new URL(`/${u.pathname.split('/')[1]}/index.jsp`, u).href; };
const ecmStart = cfg => `${cfg.sso}${cfg.sso.includes('?') ? '&' : '?'}redir_url=${encodeURIComponent(ecmEntry(cfg))}`;
const checks = { domino: dominoStands, ecm: ecmStands };

// ── Edge 의 브라우저 자리 ────────────────────────────────────────────────────

async function browserTarget(cfg) {
  const version = await fetch(`http://127.0.0.1:${cfg.port}/json/version`, { signal: AbortSignal.timeout(VERSION_MS) })
    .then(r => r.json()).catch(() => null);
  if (!version || !version.webSocketDebuggerUrl) return null;
  const ws = new WebSocket(version.webSocketDebuggerUrl);
  const waiting = new Map();
  let id = 0;
  ws.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.id && waiting.has(message.id)) { waiting.get(message.id)(message); waiting.delete(message.id); }
  };
  const opened = await new Promise(resolve => {
    const timer = setTimeout(() => resolve(false), OPEN_MS);
    ws.onopen = () => { clearTimeout(timer); resolve(true); };
    ws.onerror = () => { clearTimeout(timer); resolve(false); };
  });
  if (!opened) { try { ws.close(); } catch {} return null; }
  const call = (method, params = {}) => new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`${method} 답이 없다`)), CALL_MS);
    waiting.set(++id, message => { clearTimeout(timer); message.error ? reject(new Error(`${method}: ${message.error.message}`)) : resolve(message.result); });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return { version: version.Browser || '?', userAgent: version['User-Agent'], call, close: () => { try { ws.close(); } catch {} } };
}

// ── 파일 ─────────────────────────────────────────────────────────────────

function sessionFile(arg) {
  const raw = arg || env('MAILBOX_COOKIES', PLACES.session_file);
  const out = path.resolve(raw.replace(/^~(?=$|[\\/])/, os.homedir()));
  for (let dir = path.dirname(out); ; dir = path.dirname(dir)) {
    if (fs.existsSync(path.join(dir, '.git'))) {
      throw new Exit(EXIT.TOOL, `세션 파일 자리가 git 저장소(${dir}) 안이다 — 사내 앱의 열쇠라 저장소 밖(홈)에 둔다: ${out}`);
    }
    if (path.dirname(dir) === dir) break;
  }
  return out;
}

function readFileJar(file) {
  try {
    const state = JSON.parse(fs.readFileSync(file, 'utf8'));
    return Array.isArray(state.cookies) ? state.cookies.filter(c => c && c.name && c.domain) : null;
  } catch { return null; }
}

function write(file, cookies, cfg) {
  const state = { cookies: cookies.filter(c => keep(c, cfg)), origins: [] };
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(temp, JSON.stringify(state));
  fs.renameSync(temp, file);                        // 도중에 죽어도 반쯤 쓴 파일이 안 남는다
  return state.cookies.length;
}

// ── 갈래 ─────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const opts = { file: null, apps: [], ecmTab: false };
  for (const arg of argv) {
    if (arg === '--ecm-tab') opts.ecmTab = true;
    else if (APPS.includes(arg)) opts.apps.push(arg);
    else if (arg.startsWith('--')) throw new Exit(EXIT.TOOL, `모르는 선택: ${arg}`);
    else if (!opts.file) opts.file = arg;
    else throw new Exit(EXIT.TOOL, `인자가 남는다: ${arg}`);
  }
  return opts;
}

const say = line => console.log(line);
const label = { domino: 'Domino(메일 · 일정)', ecm: 'ECM' };

// Edge 에 붙는 갈래 — 기본. 볼 포트를 차례로 붙어 보고, 꼭 서야 하는 앱이 다 선 첫 Edge 의 쿠키를 남긴다
async function attach(cfg, opts, file, needed) {
  const ports = cfg.ports || debugPorts(cfg);
  let attached = 0, first = null;
  for (const port of ports) {
    const browser = await browserTarget({ ...cfg, port });
    if (!browser) continue;
    try {
      // --ecm-tab 은 처음 붙은 Edge 에서만 연다 — 사람이 그 탭을 보는 한 자리여야 한다
      return await harvest(cfg, { ...opts, ecmTab: opts.ecmTab && attached === 0 }, file, needed, browser, port);
    } catch (error) {
      if (!(error instanceof Exit) || ![EXIT.NOT_LOGGED_IN, EXIT.ECM_HANDOFF].includes(error.code)) throw error;
      first = first || error;                        // 처음 붙은 Edge 의 말을 낸다 — 사람이 평소 쓰는 창이 먼저다
    } finally {
      attached += 1;
      browser.close();                               // 브라우저 자리의 연결만 끊는다 — Edge 와 그 세션은 산다
    }
  }
  if (first) throw first;
  {
    // 못 붙어도 남은 파일이 아직 살면 그 파일로 선다 — 파일은 안 고친다
    const jar = readFileJar(file);
    if (jar && jar.length) {
      const scratch = [];
      let alive = true;
      for (const app of needed) alive = alive && await checks[app](cfg, jar, scratch);
      if (alive) { say('Edge 에 못 붙었지만 남은 세션 파일이 아직 산다'); say(file); return EXIT.OK; }
    }
    // 남은 파일이 있으면 그 경로를 끝 줄로 낸다 — 이 손이 그 파일을 못 가렸어도(서버가 답을 안 줬다) 부르는 쪽이 한 번 써 보고,
    // 서버가 안 받을 때만 스킬 ep-login 을 가리킨다. 파일이 없으면 경로를 안 낸다
    if (fs.existsSync(file)) say(file);
    throw new Exit(EXIT.NO_EDGE, `Edge 에 못 붙었다 — 127.0.0.1:${ports.join(' · ')} 에 디버깅 포트가 없다` +
      (fs.existsSync(file) ? '(남은 세션 파일로도 확인이 안 섰다 — 서버가 안 받았거나 답이 없었다 · 둘은 못 가르니 「거절됐다」고 말하지 않는다)' : '') +
      '. 다음: 사내망 안인지 먼저 본다(밖이면 Edge 를 띄워도 안 선다) — 안이면 스킬 ep-login 의 입구(login.sh)가 ep-login 용 Edge 창 하나를 포트와 로그인 탭으로 띄운다(사람의 Edge 는 그대로 둔다)');
  }
}

// 붙은 Edge 하나에서 쿠키를 읽어 꼭 서야 하는 앱을 가리고, 다 섰으면 파일에 쓴다 — 안 서면 Exit 3 · 4
async function harvest(cfg, opts, file, needed, browser, port) {
  {
    cfg.userAgent = browser.userAgent;
    say(`Edge ${browser.version} 에 붙었다(127.0.0.1:${port})`);
    const jar = (await browser.call('Storage.getCookies')).cookies.map(fromCdp);
    const changed = [];
    const stood = {};
    if (needed.includes('domino')) {
      stood.domino = await dominoStands(cfg, jar, changed);
      if (!stood.domino) {
        await follow(cfg, jar, changed, dominoUrl(cfg));
        stood.domino = await dominoStands(cfg, jar, changed);
      }
    }
    // ECM 은 부른 쪽이 `ecm` 을 줄 때만 받는다 — 메일 · 일정만 쓰는 판이 ECM 넘김(최대 열두 걸음)을 매번 치르지 않게
    const tryEcm = needed.includes('ecm');
    stood.ecm = tryEcm && await ecmStands(cfg, jar, changed);
    let why = '';
    if (tryEcm && !stood.ecm) {
      why = await follow(cfg, jar, changed, ecmStart(cfg), new URL(cfg.ecm));
      stood.ecm = await ecmStands(cfg, jar, changed);
    }
    if (changed.length) await browser.call('Storage.setCookies', { cookies: changed.map(toCdp) });
    if (tryEcm && !stood.ecm && opts.ecmTab) stood.ecm = await ecmTab(cfg, browser, jar);
    if (stood.domino !== undefined) say(`${label.domino} — ${stood.domino ? '섰다' : '로그인이 안 됐다'}`);
    if (tryEcm) say(`ECM — ${stood.ecm ? '섰다' : `못 받았다(${opts.ecmTab ? '탭으로도 안 섰다' : why || '?'})`}`);
    const missing = needed.filter(app => !stood[app]);
    // ECM 만 안 섰고 넘김이 로그인 화면에 안 닿았다 — 로그인은 섰다. 3 으로 내면 부르는 쪽이 사람에게 다시 로그인을 청한다
    if (missing.length === 1 && missing[0] === 'ecm' && why !== 'login') {
      const word = opts.ecmTab ? '탭으로도 안 섰다' : HANDOFF_WORD[why] || why || '?';
      throw new Exit(EXIT.ECM_HANDOFF, `붙었지만 ECM 세션을 조용히 못 받았다(${word}) — 로그인 화면에는 안 닿았다. 다시 로그인할 일이 아니다. 다음: ` +
        (opts.ecmTab ? '멈추고 이 말을 사람에게 그대로 전한다'
          : '스킬 ep-login 의 입구(login.sh ecm)가 Edge 에 탭 하나를 잠깐 열어 받는다'));
    }
    if (missing.length) {
      throw new Exit(EXIT.NOT_LOGGED_IN, `붙었지만 ${missing.map(a => label[a]).join(' · ')} 로그인이 안 됐다. 다음: 스킬 ep-login 의 입구(login.sh)가 그 Edge 에 로그인 탭을 연다`);
    }
    say(`쿠키 ${write(file, jar, cfg)} 개를 남겼다`);
    say(file);                                       // 끝 줄 — 부르는 쪽이 이 경로를 읽는다
    return EXIT.OK;
  }
}

// 이 PC 에서 디버깅 포트를 연 Edge 의 포트 — 입구의 포트가 먼저, 나머지는 찾은 차례. 브라우저 프로세스(--type= 없는 것)의
// 명령줄에서 읽는다 — 포트는 그 Edge 가 처음 뜰 때의 플래그라 명령줄이 원본이다. 못 읽으면(윈도가 아니다 · 시한) 입구의 포트만
function debugPorts(cfg) {
  const found = [];
  if (process.platform === 'win32') {
    try {
      const out = require('child_process').execFileSync('powershell', ['-NoProfile', '-Command',
        "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object { $_.CommandLine -notmatch '--type=' } | " +
        'ForEach-Object { $_.CommandLine }'], { encoding: 'utf8', timeout: FIND_MS, windowsHide: true });
      for (const m of out.matchAll(/--remote-debugging-port=(\d+)/g)) found.push(m[1]);
    } catch {}
  }
  return [...new Set([cfg.port, ...found])];
}

// --ecm-tab — 뒤쪽 탭 하나로 SSO 넘김 주소를 거치고, 선 것을 보면 그 탭을 닫는다
async function ecmTab(cfg, browser, jar) {
  const { targetId } = await browser.call('Target.createTarget', { url: ecmStart(cfg), background: true });
  try {
    const deadline = Date.now() + cfg.passMs;
    while (Date.now() < deadline) {
      await new Promise(r => setTimeout(r, POLL_MS));
      const fresh = (await browser.call('Storage.getCookies')).cookies.map(fromCdp);
      if (await ecmStands(cfg, fresh, [])) { jar.splice(0, jar.length, ...fresh); return true; }
    }
    return false;
  } finally {
    await closeTab(browser, targetId);
  }
}

// 탭을 닫고 정말 사라질 때까지 본다 — 넘김 도중(리다이렉트 · 폼 제출)에 닫은 탭은 닫기의 답이 온 뒤에도 잠시 남는다.
// 시한 안에 안 사라지면 한 번 더 닫는다. 끝내 남으면 그 탭의 주소를 알린다 — 사람이 그 탭을 닫는다
async function closeTab(browser, targetId) {
  const alive = async () => (await browser.call('Target.getTargets').catch(() => ({ targetInfos: [] })))
    .targetInfos.find(t => t.targetId === targetId);
  for (let round = 0; round < CLOSE_ROUNDS; round++) {
    await browser.call('Target.closeTarget', { targetId }).catch(() => {});
    const deadline = Date.now() + CLOSE_MS;
    while (Date.now() < deadline) {
      if (!await alive()) return;
      await new Promise(r => setTimeout(r, CLOSE_POLL_MS));
    }
  }
  const left = await alive();
  if (left) say(`⚠ 넘김에 쓴 탭이 안 닫혔다 — Edge 에서 그 탭을 닫아 주세요: ${left.url}`);
}

async function main(argv) {
  if (typeof WebSocket !== 'function' || typeof fetch !== 'function') throw new Exit(EXIT.TOOL, `Node ${process.version} — 22 이상이 든다(내장 WebSocket)`);
  const cfg = settings();
  const opts = parseArgs(argv);
  const file = sessionFile(opts.file);
  const needed = opts.apps.length ? [...new Set(opts.apps)] : ['domino'];
  if (cfg.mailbox) listUrl(cfg);                     // 준 메일함 주소가 틀리면 붙기 전에 1
  return attach(cfg, opts, file, needed);
}

if (require.main === module) {
  main(process.argv.slice(2)).then(code => process.exit(code), error => {
    console.error(error.message);
    process.exit(error instanceof Exit ? error.code : EXIT.TOOL);
  });
}

module.exports = { keep, store, sentTo, nextStep, settings, onLoginScreen, epConfirm, debugPorts, under, Exit, EXIT, VERSION_MS };
