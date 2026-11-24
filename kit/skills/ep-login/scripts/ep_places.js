// 회사 자리 값과 로그인 화면의 자 — 사내 주소 · 로그인 화면 호스트 · 시한을 환경값과 기본값에서 한 자리로 내고, 그 값으로 로그인 화면과
// 받을 확인 창을 가린다. 입구(ep_login.js) · 받는 손(edge_session.js) · Edge 줄(edge_cdp.js)이 싣는다 — 두 손이 같은 자로 가린다.
//
// 부르는 꼴:
//   const { settings, onLoginScreen, epConfirm } = require('./ep_places.js');
//   const cfg = settings();                       // 환경값은 부를 때 읽는다
//
// 내는 것
//   settings() — 아래 칸의 사전. 환경값의 뜻은 받는 손 · 입구의 머리말 「환경변수」가 든다
//   onLoginScreen(url, cfg) · onLoginHost(url, cfg) · epConfirm(type, message, url, cfg) — 참 · 거짓
// 회사 자리 값(메일 서버 · ECM 주소 · 세션 파일의 기본 자리)은 곁의 places.json 이 든다 — 형제 스킬의 파이썬 손은 ep_session.py 를 거쳐
// 같은 파일을 읽는다. 주소 · 호스트 · 도메인을 바꾸는 환경값은 가짜 서버로 재는 검사(설정 저장소 _check/skills/ep-login/check_session.js)를
// 위해 있다.
'use strict';

const PLACES = require('./places.json');
const SSO_REDIRECT = 'http://swpsso.posco.net/idms/U61/jsp/redirect.jsp';          // SSO 넘김 주소 — redir_url 이 가리키는 앱으로 세션을 넘긴다
// 사내 SSO 의 회사 로그인 — ADFS 로 넘어가 SSO(통합 인증)가 서는 PC 는 입력 없이 서지만, 안 서는 PC(VDI 따위)에서는 처음 보는 ADFS 화면이나
// 자격 증명 창이 선다 — 입구는 그것으로 SSO 가 안 서는 것을 잰다
const COMPANY_LOGIN = 'http://swpsso.posco.net/idms/U61/jsp/login/saml_login.jsp?companyCode=shared';
// EP 포털 — 사람이 평소 Edge 에서 여는 주소. 로그인 전이면 아래 평소 EP 로그인 화면으로 보내고, 로그인하면 포털로 돌아온다
const EP_PORTAL = 'http://swp.posco.net/';
// 평소 EP 로그인 — EP 포털(swp.posco.net)이 보내는 화면(아이디 · 비밀번호 칸). 통합 인증이 안 서는 자리에서 사람이 여기서 친다
const EP_LOGIN = 'http://swpsso.posco.net/idms/U61/jsp/login/login.jsp';
const DEFAULT_PORT = '9222';         // 입구(ep_login.js)가 여는 포트 — 받는 손도 이 포트를 먼저 본다
// 로그인 화면 — 로그인 화면 호스트 위의 이 경로(SSO 의 …/jsp/login/… · ADFS 의 /adfs/…). 같은 호스트의 넘김(redirect.jsp)은 아니다
const LOGIN_PATH = /\/(login|adfs)\//i;
const EP_DIALOG = '다른 PC에서 EP 접속 정보';   // SSO 가 로그인 도중 띄우는 확인 창의 글 — 이 창만 「확인」으로 받는다

// 환경값 하나 — 비었으면 기본값
const env = (name, fallback) => (process.env[name] || '').trim() || fallback;
// 초 단위 환경값 하나 — 양의 수가 아니면 기본값
const seconds = (name, fallback) => {
  const value = Number(env(name, String(fallback)));
  return Number.isFinite(value) && value > 0 ? value : fallback;
};

// 회사 자리 값 · 로그인 화면 호스트 · 시한을 환경값과 기본값에서 한 사전으로 낸다
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
    companyLogin: env('COMPANY_LOGIN_URL', COMPANY_LOGIN),   // 입구가 SSO 를 재며 여는 주소 — 로그인 탭과, SSO 가 서는지 모르는 평소 걸음
    epLogin: env('EP_LOGIN_URL', EP_LOGIN),                  // SSO 가 안 서는 로그온의 로그인 탭이 여는 주소 · SSO 가 안 설 때 넘기는 주소
    portal: env('EP_PORTAL_URL', EP_PORTAL),                 // SSO 가 안 서는 로그온의 평소 걸음이 여는 EP 포털 — 사람이 거기서 친다
    domain: env('SESSION_DOMAIN', 'posco.net').toLowerCase().replace(/^\./, ''),
    loginHosts: env('SESSION_LOGIN_HOSTS', 'swpsso.posco.net,adfs.m365.posco.net').toLowerCase().split(',').map(s => s.trim()).filter(Boolean),
    requestMs: seconds('SESSION_REQUEST_SECONDS', 5) * 1000,
    passMs: seconds('SESSION_PASS_SECONDS', 30) * 1000,
    loginMs: seconds('SESSION_LOGIN_WAIT_SECONDS', 300) * 1000,
    fallbackMs: seconds('SESSION_FALLBACK_SECONDS', 8) * 1000,    // 입구가 입력 칸 있는 로그인 화면에 이만큼 머물면 통합 인증이 안 선 것으로 본다
    ordinaryMs: seconds('SESSION_ORDINARY_SECONDS', 30) * 1000,   // 입구가 평소 Edge 에 EP 포털을 열고 확인 창을 기다리는 틈 — 통합 인증의 넘김과 넘어간 화면이 설 틈
    ssoMs: seconds('SESSION_SSO_SECONDS', 30) * 1000,             // 로그인 탭이 회사 SSO 주소에서 이만큼 못 넘으면(입력 칸이 안 보여도) SSO 가 안 선 것으로 본다
  };
}

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

module.exports = { PLACES, env, settings, onLoginScreen, onLoginHost, epConfirm };
