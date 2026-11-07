// 쓰는 사람의 Edge 에서 사내 세션(메일 · 일정 · 다른 Domino 앱 · ECM)의 쿠키를 받아 세션 파일로 남긴다 — 사내 앱을 다루는
// 손(스킬 company-mail · company-calendar · company-ecm)이 그 파일을 읽는다. 새로 로그인하지 않고 창 · 탭을 열지 않아, 아무 세션도 안 끊고 사람 화면에 아무것도
// 안 뜬다. 그래서 그 손들이 매번 읽기 전에 이 손부터 부른다 — 빠르고(붙어서 끝까지 1초 안팎) 몇 번을 불러도 같다.
//
// 부르는 꼴:
//     node edge_session.js [세션 파일] [domino] [ecm] [--ecm-tab]
//   세션 파일 — 안 주면 MAILBOX_COOKIES, 그것도 없으면 이 손의 기본 자리(DEFAULT_FILE · 홈). 기본 자리는 여기 한 곳에만 있다 —
//     부르는 쪽은 인자 없이 부르고 종료 0 의 끝 줄에서 경로를 읽는다(아래 「내는 것」). git 저장소 안의 자리는 거절한다(종료 1).
//   domino · ecm — 이번에 꼭 서야 하는 앱. 안 주면 domino 다(메일 · 일정 · 다른 Domino 앱이 쓰는 .posco.net 세션). ECM 세션은
//     `ecm` 을 준 판에서만 받는다 — 메일 · 일정만 쓰는 판이 ECM 넘김을 매번 치르지 않는다. 문서함을 다루는 쪽이 `ecm` 을 준다.
//   domino 의 확인 — MAILBOX_URL 이 있으면 그 메일함의 받은편지함 목록 하나, 없으면 Domino 서버(DOMINO_URL)의 세션 확인 주소
//     (/common/lib_f.nsf/checksessionstatus?Openpage → {"status":"login"} · 웹메일이 수십 초마다 부르는 주소)다. 둘 다 메일을
//     안 건드린다. 세션 확인 주소의 끊긴 답은 안 쟀다 — 그 꼴이 아니면 다 「로그인 안 됨」으로 본다.
//   --ecm-tab — 조용한 ECM 받기(아래)가 안 설 때만 쓰는 갈래. 사람의 Edge 에 뒤쪽 탭 하나를 열어 SSO 넘김 주소를 거치고 닫는다.
//     탭이 잠깐 보이므로 사람이 아는 자리(스킬 ep-login)에서만 준다.
//
// 환경변수 — 다 없어도 된다. MAILBOX_URL 메일함 주소(…/<번호>.nsf 까지 · 주면 domino 를 그 목록으로 가린다) ·
//   MAILBOX_VIEW 받은편지함 보기(기본 XML_Inbox) · DOMINO_URL Domino 서버(기본 아래 DOMINO_SERVER) ·
//   EDGE_DEBUG_PORT 디버깅 포트(기본 9222) · ECM_URL ECM 메인 주소(기본 아래 ECM_MAIN · 넘김이 가리킬 첫 화면 index.jsp 는 그
//   주소의 첫 경로 칸 아래에서 짓는다) · SSO_REDIRECT_URL SSO 넘김 주소 ·
//   SESSION_DOMAIN 회사 도메인(기본 posco.net) · SESSION_LOGIN_HOSTS 로그인 화면 호스트(쉼표 · 기본 swpsso · adfs.m365) ·
//   SESSION_REQUEST_SECONDS 묻기 하나의 시한(기본 5) · SESSION_PASS_SECONDS --ecm-tab 의 시한(기본 30) ·
//   SESSION_LOGIN_WAIT_SECONDS 띄우는 손(edge_start.js)이 로그인 탭을 지켜보는 시한(기본 300).
//   도메인 · 호스트 · 주소의 바꿈은 가짜 서버로 재는 검사(check_session.js)를 위해 있다 — 회사에서는 기본값 그대로 쓴다.
//
// 내는 것 — 세션 파일(Playwright 저장 상태 꼴 {"cookies": [...], "origins": []}). 종료 0 이면 표준 출력의 끝 줄이 그 파일의
//   절대 경로 하나다(앞 줄들은 사람이 읽는 경과). 종료 값은 닫힌 다섯이다:
//   0 파일이 지금 산 세션을 든다 — 꼭 서야 하는 앱마다 그 쿠키로 답이 왔다. 새로 썼거나, Edge 에 못 붙었는데 남은 파일이 아직
//     산다(그때는 파일을 안 고친다)
//   2 Edge 에 못 붙었고 남은 파일로도 안 섰다 — 디버깅 포트로 안 떴거나 닫혔다. 남은 파일이 있으면 그 절대 경로를 표준 출력의
//     끝 줄로 낸다(없으면 경로 줄이 없다) — Edge 가 닫힌 뒤에도 남은 세션이 서버에 살아 있을 수 있어, 부르는 쪽이 한 번 써 보고
//     서버가 안 받을 때(로그인 화면 · 302 · 401)만 ep-login 을 가리키게
//   3 붙었지만 꼭 서야 하는 앱이 로그인이 안 됐다 — Edge 에서 로그인이 안 됐거나 끊겼다(ECM 넘김이 로그인 화면에서 멈춘 판도
//     여기다). 파일은 안 고친다
//   4 붙었고 로그인 화면에는 안 닿았는데 ECM 만 못 받았다 — 이 손이 ECM 의 SSO 넘김을 화면 없이 못 따라갔다(못 따라가는 꼴 ·
//     회사 밖 주소 · 답 없음 · 걸음 초과 · --ecm-tab 으로도 안 섰다). 다시 로그인할 일이 아니다. 꼭 서야 하는 다른 앱이 안
//     섰으면 4 가 아니라 3 이다. 파일은 안 고친다
//   1 그 밖 — 설정(주소 · 인자 · 저장소 안의 자리) · Node 판 · 도구 고장
//   3 이면 부른 쪽은 사람에게 바로 스킬 ep-login 을 가리키고(그 스킬이 로그인을 이끈다), 4 면 같은 스킬의 「ECM 만 못 받았다」
//   (--ecm-tab)를 가리키되 다시 로그인을 청하지 않는다. 2 는 위대로 남은 파일을 먼저 써 본다. 이 값의 뜻을 바꾸면 그 스킬과
//   부르는 스킬들을 같은 판에 고친다.
//
// 어떻게 붙나 — Playwright 의 connectOverCDP 를 안 쓴다. 디버깅 포트의 브라우저 자리(/json/version 의 웹소켓)에만 붙어
//   Storage.getCookies 로 쿠키를 읽는다. 탭에는 붙지 않는다 — 그래서 사람의 탭을 안 건드린다. connectOverCDP 는 탭마다 붙고,
//   듣는 손이 없으면 사람의 탭에 뜬 확인 창을 「취소」로 닫으며, 한 탭이라도 확인 창을 띄운 채면 붙기 자체가 시한까지 멈춘다
//   (2026-11-06 이 PC Edge 146 · 임시 프로필로 잼 — README 「잰 것」).
//   묻기(앱 확인 · ECM 받기)는 이 손이 Node 의 http 로 하고, 그 쿠키는 Edge 에서 읽은 것을 싣는다. 답이 고친 쿠키는 Edge 에도
//   써 둔다(Storage.setCookies) — 사람의 Edge 가 그 주소를 열었을 때 받았을 쿠키와 같은 것이라, Edge 와 서버의 세션이 어긋나지 않는다.
//
// ECM — 세션은 swpecm 호스트의 쿠키(JSESSIONID)다. 그 쿠키가 없거나 서버가 안 받을 때만 SSO 넘김 주소
//   (redirect.jsp?redir_url=<ECM 첫 화면 index.jsp>)를 이 손이 따라가 받는다: 리다이렉트 · 스스로 제출하는 폼(submit() 을 부르는 폼 ·
//   스크립트가 action 을 채우는 회사 넘김 화면도) · ECM 첫 화면이 에이전트 웹소켓 없는 브라우저에 주는 login.do 주소 ·
//   location 으로 넘기는 스크립트를 회사 호스트 안에서만 열두 걸음까지 따라가고, 메인에 다다르거나 암호 칸이 있는 화면(로그인)에서
//   멈춘다. 스크립트가 폼 자체를 지어 내는 꼴처럼 이 손이 못 따라가는 꼴이면 「ECM — 못 받았다」이고(종료 4), 그때의
//   갈래가 --ecm-tab 이다. 넘김이 로그인 화면에서 멈췄으면 로그인이 끊긴 것이라 3 이다. Domino 도 같다 —
//   확인이 안 서면 그 확인 주소에서 같은 따라가기를 한 번 한다(SSO 는 섰는데 Domino 서버에 한 번도 안 들른 Edge).
//
// 무엇을 파일에 남기나 — 회사 도메인(SESSION_DOMAIN)과 그 아래 호스트에 실리는 쿠키만. 로그인 화면 호스트(SSO · ADFS)가 제
//   이름으로 받은 쿠키, 회사 밖 사이트의 쿠키, 사이트 저장소(origins)는 안 남긴다 — Edge 는 그 프로필의 모든 사이트 쿠키를 낸다.
//   .posco.net 쿠키는 메일 · 일정 · 다른 Domino 앱이 다 쓰고(mail-secretary #28 「C. 일정」), ECM 쿠키는 swpecm 호스트에 산다.
//   한 파일에 둘이 함께 들 수 있고, 읽는 쪽은 호스트로 골라 쓴다 — 어느 호스트의 쿠키가 꼭 있다고 기대지 않는다.
//
// ⚠ 세션 파일은 사내 앱의 열쇠다 — 저장소 밖(홈)에 두고 남에게 넘기지 않는다. 다 쓴 PC · 남에게 넘길 PC 에서는 지운다.
// ⚠ 디버깅 포트는 이 PC 의 다른 프로그램도 쓸 수 있다 — 127.0.0.1 에만 열고, 이 손은 127.0.0.1 로만 붙는다.
// ⚠ Chromium 136 부터 기본 프로필에는 디버깅 포트가 안 열린다(Chrome 공지 · Edge 는 공지 없이 같다는 보고) — 띄우는 손
//   (edge_start.js)이 기본 프로필로 띄워 본 결과로 가르고, 그 판에서 안 열리면 --profile 로 띄운다. 잰 자리의 판은 README 「잰 것」.
//
// 필요한 것: Node 22 이상(내장 WebSocket · fetch). npm 꾸러미는 안 든다.

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const https = require('https');

const ECM_MAIN = 'http://swpecm.posco.net:7091/ECM/jsp/main/ecmMain.jsp';       // mail-secretary #28 ECM 둘째 판(에이전트 ini 의 서버 · 포트)
const SSO_REDIRECT = 'http://swpsso.posco.net/idms/U61/jsp/redirect.jsp';          // 같은 #28 ECM 첫째 판 · company-facts 「처음 실행」
const DOMINO_SERVER = 'http://pcfma0b.posco.net';                                  // 메일 서버 — mail-secretary docs/company-facts.md 「메일함」
const SESSION_CHECK = '/common/lib_f.nsf/checksessionstatus?Openpage';             // 같은 문서의 세션 확인 줄 · 스킬 company-mail 의 inbox.py 머리말
const DEFAULT_FILE = '~/.mailbox-session.json';                                     // 세션 파일의 기본 자리 — 이 한 곳에만 둔다
const MAX_HOPS = 12;                 // 따라가기의 걸음 상한 — ECM 넘김은 잰 판에서 여섯 걸음 남짓이다(#28 ECM 둘째 판)
const APPS = ['domino', 'ecm'];
// 로그인 화면 — 로그인 화면 호스트 위의 이 경로(SSO 의 …/jsp/login/… · ADFS 의 /adfs/…). 같은 호스트의 넘김(redirect.jsp)은 아니다
const LOGIN_PATH = /\/(login|adfs)\//i;
const EP_DIALOG = '다른 PC에서 EP 접속 정보';   // SSO 가 로그인 도중 띄우는 확인 창의 글 — 이 창만 「확인」으로 받는다
// ECM 넘김이 멈춘 까닭(follow 의 답) → 사람의 말. login 은 여기 없다 — 로그인 화면에 닿은 판은 종료 3 이다
const HANDOFF_WORD = { end: '넘김 화면을 따라가지 못했다', outside: '회사 밖 주소로 넘어갔다', 'no-answer': '서버가 답하지 않았다',
  hops: '넘김이 걸음 상한을 넘었다' };
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
    port: env('EDGE_DEBUG_PORT', '9222'),
    view: env('MAILBOX_VIEW', 'XML_Inbox'),
    mailbox: env('MAILBOX_URL', ''),
    domino: env('DOMINO_URL', DOMINO_SERVER).replace(/\/+$/, ''),
    ecm: env('ECM_URL', ECM_MAIN),
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
// 띄우는 손(edge_start.js)이 로그인 탭을 지켜보며 쓰는 자 — 설정(settings)과 한 자리에 둔다

// 로그인 화면인가 — 로그인 화면 호스트이고 그 경로다
function onLoginScreen(url, cfg) {
  try { const u = new URL(url); return cfg.loginHosts.includes(u.hostname.toLowerCase()) && LOGIN_PATH.test(u.pathname); } catch { return false; }
}

// 「확인」으로 받을 창인가 — 로그인 화면에 뜬 「EP 접속 정보」 확인 창만. 받는 것: 창의 꼴(confirm · alert …) · 글 · 뜬 주소
function epConfirm(type, message, url, cfg) {
  return type === 'confirm' && String(message || '').includes(EP_DIALOG) && onLoginScreen(url, cfg);
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
  // 주소(login.do …&USE_WEBSOCKET=F)를 그 화면의 값(actionUrl · jID)으로 짓는다 — 2026-11-06 이 PC 실물 index.jsp 의 IsWebSocket()
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
    // 주소로 읽으면 같은 화면에 되보내며 돈다(2026-11-06 이 PC 실물 redirect.jsp)
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
  if (!match) throw new Exit(1, `MAILBOX_URL 이 메일함 주소(…/이름.nsf)가 아니다: ${cfg.mailbox || '(비었다)'}`);
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

// ECM — 메인 화면. 세션이 없으면 302 → /ECM/logout.jsp 다(#28 ECM 첫째 판)
async function ecmStands(cfg, jar, changed) {
  if (!jar.some(c => sentTo(c, new URL(cfg.ecm)))) return false;
  const page = await send(cfg, jar, changed, { url: cfg.ecm });
  return Boolean(page && page.status === 200 && /html/i.test(page.type));
}

// SSO 넘김이 가리킬 ECM 첫 화면 — 메인을 가리키면 곧장 logout 으로 튕기고, 첫 화면(<맥락 경로>/index.jsp)이 세션을 세운다(2026-11-06
// 실물). 맥락 경로는 ECM_URL 의 첫 경로 칸이다 — 서버 · 포트 · 맥락을 ECM_URL 한 곳에서만 읽는다
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
  const raw = arg || env('MAILBOX_COOKIES', DEFAULT_FILE);
  const out = path.resolve(raw.replace(/^~(?=$|[\\/])/, os.homedir()));
  for (let dir = path.dirname(out); ; dir = path.dirname(dir)) {
    if (fs.existsSync(path.join(dir, '.git'))) {
      throw new Exit(1, `세션 파일 자리가 git 저장소(${dir}) 안이다 — 사내 앱의 열쇠라 저장소 밖(홈)에 둔다: ${out}`);
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
    else if (arg.startsWith('--')) throw new Exit(1, `모르는 선택: ${arg}`);
    else if (!opts.file) opts.file = arg;
    else throw new Exit(1, `인자가 남는다: ${arg}`);
  }
  return opts;
}

const say = line => console.log(line);
const label = { domino: 'Domino(메일 · 일정)', ecm: 'ECM' };

// Edge 에 붙는 갈래 — 기본
async function attach(cfg, opts, file, needed) {
  const browser = await browserTarget(cfg);
  if (!browser) {
    // 못 붙어도 남은 파일이 아직 살면 그 파일로 선다 — 파일은 안 고친다
    const jar = readFileJar(file);
    if (jar && jar.length) {
      const scratch = [];
      let alive = true;
      for (const app of needed) alive = alive && await checks[app](cfg, jar, scratch);
      if (alive) { say('Edge 에 못 붙었지만 남은 세션 파일이 아직 산다'); say(file); return 0; }
    }
    // 남은 파일이 있으면 그 경로를 끝 줄로 낸다 — 이 손이 그 파일을 못 가렸어도(서버가 답을 안 줬다) 부르는 쪽이 한 번 써 보고,
    // 서버가 안 받을 때만 스킬 ep-login 을 가리킨다. 파일이 없으면 경로를 안 낸다
    if (fs.existsSync(file)) say(file);
    throw new Exit(2, `Edge 에 못 붙었다 — 127.0.0.1:${cfg.port} 에 디버깅 포트가 없다. 스킬 ep-login 이 다시 세우는 길을 이끈다`);
  }
  try {
    cfg.userAgent = browser.userAgent;
    say(`Edge ${browser.version} 에 붙었다`);
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
      throw new Exit(4, `붙었지만 ECM 세션을 조용히 못 받았다(${word}) — 로그인 화면에는 안 닿았다. 다시 로그인할 일이 아니다 — ` +
        '스킬 ep-login 의 「ECM 만 못 받았다」(--ecm-tab)로 받는다');
    }
    if (missing.length) {
      throw new Exit(3, `붙었지만 ${missing.map(a => label[a]).join(' · ')} 로그인이 안 됐다 — Edge 에서 로그인한 뒤 다시 부른다(스킬 ep-login)`);
    }
    say(`쿠키 ${write(file, jar, cfg)} 개를 남겼다`);
    say(file);                                       // 끝 줄 — 부르는 쪽이 이 경로를 읽는다
    return 0;
  } finally {
    browser.close();                                 // 브라우저 자리의 연결만 끊는다 — Edge 와 그 세션은 산다
  }
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
  if (typeof WebSocket !== 'function' || typeof fetch !== 'function') throw new Exit(1, `Node ${process.version} — 22 이상이 든다(내장 WebSocket)`);
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
    process.exit(error instanceof Exit ? error.code : 1);
  });
}

module.exports = { keep, store, sentTo, nextStep, settings, onLoginScreen, epConfirm, Exit };
