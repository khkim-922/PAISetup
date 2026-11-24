// 평소 Edge 의 로그인을 읽는 바탕 — 이 윈도 로그온의 열쇠와 세 기록(평소 걸음을 해 봤다 · 평소 로그인이 섰다 · SSO 가 안 선다), 평소 Edge 를 보는 눈과 그 가름,
// 그리고 그것들로 「이 로그온에 평소 EP 로그인이 한 번 섰나」를 아무것도 안 열고 가리는 답(ordinaryLogin). 입구(ep_login.js)와 그 답을 빌려
// 주는 문(ordinary_status.js)이 싣는다.
//
// 내는 것
//   logonKey() · readMark() · writeMark(key) · readStood() · writeStood(key) · readNoSso() · writeNoSso(key) — 로그온 열쇠와 세 기록(평소 걸음을
//     해 봤다 · 평소 로그인이 섰다 · 이 로그온에는 SSO 가 안 선다 — SAVED.* 로 끝을 낸다)
//   edgeEye(select) · eyeSelect() · lookOnce(eye) · lookForPortal(eye) · tabsState(tabs) · committedState(tabs) — 눈과 그 가름(LOOK.*)
//   ordinaryLogin() — ORDINARY.STOOD(섰다) · TRIED(해 봤는데 섰는지 모른다) · MISSING(없다) — 기록을 먼저 읽고, 기록이 없을 때만 눈으로 본다
//   readTitles() · TITLES · ordinaryProfile() · hostOf(url) · EYE · EYE_GAP_MS · STEADY · SAVED
'use strict';
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');
const { PLACES, env, settings } = require('./ep_places.js');

const cfg = settings();
const sleep = ms => new Promise(r => setTimeout(r, ms));

// 이 윈도 로그온에 평소 Edge 의 걸음을 했다는 표 — 로그온 열쇠(logonKey) 한 줄. 기록은 다 LOCALAPPDATA 아래라 비영속 VDI 는 로그오프 때 함께 사라진다
const ORDINARY_MARK = path.join(process.env.LOCALAPPDATA || '', 'ep-login', 'ordinary-logon');

const EYE = path.join(__dirname, 'ordinary_edge.ps1');   // 평소 Edge 를 보는 눈 — 포트가 없어 윈도 UI 자동화로 본다

// 눈의 두 시한 — 값은 places.json 한 자리가 든다(빌려 주는 문 ep_session.py 가 제 시한을 같은 값에서 짓는다). 뜨기와 보기를 따로 잰다 — 바쁜
// PC 의 PowerShell 은 뜨는 데만 수십 초가 들어, 한 시한으로 둘을 덮으면 느리게 뜬 멀쩡한 눈을 「답이 없다」로 접는다
const EYE_START_MS = PLACES.eye_start_s * 1000;   // 눈이 떠 UI 자동화를 다 싣기까지(준비 줄) — 준비 줄이나 눈의 끝이 기다림을 끝내고, 넘으면 뜨다 멈춘 것이다
const EYE_MS = PLACES.eye_look_s * 1000;          // 뜬 눈의 답 하나 — 한 번 보기는 1초 안쪽이고, 넘으면 보다 멈춘 것이다

const FIND_MS = EYE_START_MS + EYE_MS;   // 로그온 열쇠를 묻는 PowerShell 한 번 — 뜨기와 물음 하나. 답은 그 PowerShell 이 끝나면 오고, 시한은 멈춘 것만 끊는다

const EYE_GAP_MS = 300;               // 평소 Edge 의 물음 창을 다시 보는 사이

const LOOK_TRIES = 3;                 // 평소 Edge 의 탭을 못 읽었을 때 다시 읽는 수 — 물음 창이 잠깐 떠 탭 줄을 가린 판을 넘긴다

const LOOK_GAP_MS = 700;              // 그 다시 읽는 사이

const STEADY = 3;                     // 「EP 포털 탭이 있다」를 믿기까지 잇달아 같아야 하는 읽기 수 — 한 번 본 것은 넘어가는 중일 수 있다

// 이 PC 에서 배운 EP 화면의 탭 제목 — 포털과 로그인 화면 둘만 둔다(사람의 다른 탭은 안 둔다). 앞에 안 선 탭은 주소가 안 보여 제목으로 알아본다
const TITLES = path.join(process.env.LOCALAPPDATA || '', 'ep-login', 'ep-titles.json');

// 눈 — ordinary_edge.ps1 과 한 줄씩 주고받는다(그 머리말의 꼴 · select 는 볼 Edge 를 고르는 그 환경변수). 시한은 둘이다 — 뜨기(EYE_START_MS)는
// 눈의 첫 줄(준비 줄)이나 눈의 끝이 끝내고, 답 하나(EYE_MS)는 준비 줄 뒤에야 잰다. 그래서 느리게 뜨는 PowerShell 은 보기의 시한을 안 먹고,
// 뜬 뒤 멈춘 보기는 뜨기의 시한까지 안 기다린다. 눈이 죽거나 시한을 넘으면 물음마다 null 을 내고 그 뒤로는 안 묻는다
function edgeEye(select) {
  const child = spawn('powershell', ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', EYE],
    { windowsHide: true, env: { ...process.env, ...select } });
  let buffer = '', err = '', dead = '', ready = false;
  const waiting = [];                                // 답을 기다리는 물음 — { arm: 답의 시한을 건다, got: 답을 받는다 }
  const stop = why => { dead = dead || why; clearTimeout(starting); while (waiting.length) waiting.shift().got(null); };
  const halt = why => { stop(why); child.kill(); };
  const starting = setTimeout(() => halt(`${EYE_START_MS / 1000}초 안에 뜨지 않았다`), EYE_START_MS);
  // 눈의 한 줄 — 첫 줄은 준비 줄이라 답이 아니다. 그때 기다리던 물음의 시한을 건다
  const heard = line => {
    if (!ready) { ready = true; clearTimeout(starting); for (const w of waiting) w.arm(); return; }
    if (waiting.length) waiting.shift().got(line);
  };
  child.stdout.setEncoding('utf8');
  child.stdout.on('data', d => {
    buffer += d;
    for (let i; (i = buffer.indexOf('\n')) >= 0;) {
      const line = buffer.slice(0, i).trim();
      buffer = buffer.slice(i + 1);
      if (line) heard(line);
    }
  });
  child.stderr.on('data', d => err += d);
  child.stdin.on('error', () => {});                 // 눈이 먼저 죽은 뒤의 쓰기 — 까닭은 close 가 든다
  child.on('error', e => stop(e.message));
  child.on('close', code => stop(`종료 ${code}${err.trim() ? ` — ${err.trim().split(/\r?\n/)[0]}` : ''}`));
  const ask = line => new Promise(resolve => {
    if (dead) return resolve(null);
    let timer = null;
    const arm = () => { timer = setTimeout(() => halt(`${EYE_MS / 1000}초 안에 답이 없다`), EYE_MS); };
    waiting.push({ arm, got: got => { clearTimeout(timer); try { resolve(got && JSON.parse(got)); } catch { resolve(null); } } });
    if (ready) arm();
    child.stdin.write(`${line}\n`);
  });
  return {
    look: () => ask('look'),
    press: i => ask(`press ${i}`),
    tabs: () => ask('tabs'),
    why: () => dead || '답이 없다',
    dead: () => Boolean(dead),
    close: () => { clearTimeout(starting); try { child.stdin.end(); } catch {} setTimeout(() => { try { child.kill(); } catch {} }, 2000).unref(); },
  };
}

// 볼 평소 Edge 의 프로필 — "" 이면 사람의 평소 Edge 다(검사만 버리는 프로필을 준다)
const ordinaryProfile = () => env('EP_ORDINARY_PROFILE', '') && path.resolve(env('EP_ORDINARY_PROFILE', ''));

// 주소의 호스트 이름(소문자 · 포트 없이) — 못 읽으면 ""
const hostOf = url => { try { return new URL(url).hostname.toLowerCase().replace(/^\[|\]$/g, ''); } catch { return ''; } };

// 배운 탭 제목 — { portal, login }. 제목은 비밀이 아니고, EP 의 두 화면 것만 둔다
const readTitles = () => { try { const t = JSON.parse(fs.readFileSync(TITLES, 'utf8')); return { portal: String(t.portal || ''), login: String(t.login || '') }; } catch { return { portal: '', login: '' }; } };

// 제목을 남긴 끝 — 닫힌 셋
const SAVED = { SAME: 'same', WRITTEN: 'written', FAILED: 'failed' };

// 평소 Edge 를 한 번 본다 — 눈이 탭 줄 · 주소창을 읽어 EP 에 맞는 수만 낸다(사람의 다른 탭은 눈 밖으로 안 나온다).
// 내는 것: { state: LOOK.PORTAL | ABSENT | UNREAD, tabs } — tabs 는 눈이 낸 수(못 읽었으면 null)
async function lookOnce(eye) {
  const tabs = await eye.tabs();
  return { state: tabsState(tabs), tabs };
}

// 평소 Edge 를 본 끝 — 닫힌 넷
const LOOK = {
  PORTAL: 'portal',        // 앞 탭이 포털이거나, 배운 포털 제목의 탭이 있다
  ABSENT: 'absent',        // 평소 Edge 가 없거나, 읽혔는데 포털 탭이 없다
  UNREAD: 'unread',        // 탭 줄 · 주소창을 못 읽었다
  EYE_DOWN: 'eye-down',    // 눈이 안 선다
};

// 눈이 낸 수를 한 번 본 끝으로 가른다 — PORTAL · ABSENT · UNREAD
function tabsState(tabs) {
  if (!tabs) return LOOK.UNREAD;
  if (tabs.portal > 0 || tabs.titled > 0) return LOOK.PORTAL;
  if (!tabs.browsers) return LOOK.ABSENT;
  return tabs.unread > 0 ? LOOK.UNREAD : LOOK.ABSENT;
}

// 연 탭에 포털 화면이 섰나를 눈이 낸 수로 가른다 — PORTAL · ABSENT · UNREAD. 주소창만으로는 못 가른다: 포털 주소로 막 연 탭은 첫 응답이 오기
// 전에도 주소창이 포털이라, 그것을 「섰다」로 읽으면 사람이 치기 전에 평소 로그인이 섰다고 한다. 그래서 그 탭에 화면이 섰다는 증거(committed —
// 눈의 머리말)가 있는 포털이나 배운 포털 제목의 탭만 PORTAL 이다. 이름을 못 읽는 탭은 증거가 없어 기다린다 — 틀린 「섰다」는 아무 말 없이 문서
// 일을 막고 메일을 끊지만, 기다림은 시한에 사람에게 묻는다
function committedState(tabs) {
  if (!tabs) return LOOK.UNREAD;
  if (tabs.committed > 0 || tabs.titled > 0) return LOOK.PORTAL;
  return tabsState(tabs) === LOOK.UNREAD ? LOOK.UNREAD : LOOK.ABSENT;
}

// 평소 Edge 에 EP 포털 탭이 있나 — 무엇을 열기 전에. 「있다」는 STEADY 번 잇달아 본 것만 믿고, 못 읽으면 LOOK_TRIES 번까지 다시 읽는다.
// 내는 것: { state: LOOK.* } — EYE_DOWN 눈이 안 섰다(눈의 말 eyeWhy) · UNREAD 창의 탭 줄 · 주소창이
// 안 읽혔다(마지막 읽기의 창 수 windows · 못 읽은 창 수 unread — 모르면 '?')
async function lookForPortal(eye) {
  let unread = 0, steady = 0;
  for (;;) {
    const now = await lookOnce(eye);
    if (now.state === LOOK.PORTAL) { if (++steady >= STEADY) return { state: LOOK.PORTAL }; await sleep(EYE_GAP_MS); continue; }
    if (now.state === LOOK.ABSENT) return { state: LOOK.ABSENT };
    steady = 0;
    if (++unread >= LOOK_TRIES) {
      if (eye.dead()) return { state: LOOK.EYE_DOWN, eyeWhy: eye.why() };
      return { state: LOOK.UNREAD, windows: now.tabs ? now.tabs.windows : '?', unread: now.tabs ? now.tabs.unread : '?' };
    }
    await sleep(LOOK_GAP_MS);
  }
}

// 눈에 줄 환경값 — 볼 프로필 · 포털과 로그인 화면의 호스트 · 포털 제목(로그인 화면의 제목과 다를 때만 — 같으면 로그인 화면의 탭을 포털로 읽는다)
function eyeSelect() {
  const titles = readTitles();
  const title = titles.portal && titles.portal !== titles.login ? titles.portal : '';
  return { EP_ORDINARY_PROFILE: ordinaryProfile(), EP_TAB_PORTAL: hostOf(cfg.portal), EP_TAB_LOGIN: cfg.loginHosts.join(','), EP_TAB_TITLE: title };
}

const NO_KEY = '-';                   // EP_LOGON_KEY 에 이 값을 주면 열쇠가 없는 PC 를 흉내 낸다

// 이 윈도 로그온의 열쇠 — 이 세션의 탐색기(explorer)가 뜬 때. 로그온마다 새로 뜨고, 빠른 시작으로 끈 PC 도 켜서 로그온하면 바뀐다(부팅
// 시각은 빠른 시작이 안 바꾼다). 못 읽으면 "" — 그때는 표를 안 읽고 안 남긴다(묻기 · 걸음 · SSO 재기가 부를 때마다 다시 선다)
function logonKey() {
  const given = env('EP_LOGON_KEY', '');
  if (given === NO_KEY) return '';                  // 검사의 흉내 — 로그온을 못 가리는 PC(PowerShell 이 막힌 자리)
  if (given) return given;
  if (process.platform !== 'win32') return '';
  try {
    return execFileSync('powershell', ['-NoProfile', '-NonInteractive', '-Command',
      '$s = (Get-Process -Id $PID).SessionId; $e = Get-Process explorer -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -eq $s } | ' +
      "Sort-Object StartTime | Select-Object -First 1; if ($e) { $e.StartTime.ToUniversalTime().ToString('o') }"],
    { encoding: 'utf8', timeout: FIND_MS, windowsHide: true }).trim();
  } catch { return ''; }
}

// 로그온 열쇠 한 줄을 든 기록 하나 — 읽기(없으면 "")와 남기기(SAVED.WRITTEN · 못 남겼으면 SAVED.FAILED 와 까닭)
function logonRecord(file) {
  return {
    read: () => { try { return fs.readFileSync(file, 'utf8').trim(); } catch { return ''; } },
    write: key => {
      try { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, `${key}\n`); return { state: SAVED.WRITTEN }; }
      catch (e) { return { state: SAVED.FAILED, why: e.code || e.message }; }
    },
  };
}

// 이 로그온의 표 — 평소 Edge 의 걸음을 했다
const { read: readMark, write: writeMark } = logonRecord(ORDINARY_MARK);

// 이 윈도 로그온에 평소 EP 로그인이 섰다는 기록 — 로그온 열쇠 한 줄. 입구가 선 것을 본 때(포털 탭이 이미 있다 · 연 탭이 포털로 넘어갔다 ·
// 사용자가 「했다」고 답했다)에만 남긴다. 「해 봤다」(ORDINARY_MARK)와 다른 사실이다 — 해 본 걸음이 안 섰을 수 있다
const ORDINARY_STOOD = path.join(process.env.LOCALAPPDATA || '', 'ep-login', 'ordinary-stood');
const { read: readStood, write: writeStood } = logonRecord(ORDINARY_STOOD);

// 이 윈도 로그온에는 SSO(통합 인증)가 안 선다는 기록 — 로그온 열쇠 한 줄. 입구의 로그인 탭이나 평소 Edge 의 걸음이 회사 SSO 주소에서 넘지
// 못한 것을 본 때 남긴다(DESIGN 「SSO 가 서나」). 이 기록이 있는 로그온은 처음부터 사람이 치는 화면(EP 포털 · 평소 EP 로그인)을 열고, 사람
// 없는 부름은 창을 안 띄운다. 「선다」는 남기지 않는다 — 기록이 없으면 회사 SSO 주소로 잰다
const NO_SSO = path.join(process.env.LOCALAPPDATA || '', 'ep-login', 'no-sso');
const { read: readNoSso, write: writeNoSso } = logonRecord(NO_SSO);

// 이 로그온의 평소 EP 로그인 — 닫힌 셋
const ORDINARY = {
  STOOD: 'stood',          // 섰다 — 기록이 있거나, 기록이 없는데 평소 Edge 에 EP 포털 탭이 선 것을 지금 봤다
  TRIED: 'tried',          // 이 로그온에 평소 걸음을 해 봤는데 섰는지는 모른다 — 그대로 잇는다(문서가 안 열리면 사람이 평소 Edge 에서 로그인한다)
  MISSING: 'missing',      // 기록이 없고 평소 Edge 에 EP 포털 탭이 없다(읽었는데 없다 · 못 읽었지만 로그온 열쇠가 있다) — 입구를 ecm 으로 부른다
  UNSURE: 'unsure',        // 기록이 없고 평소 Edge 를 못 읽었고 로그온 열쇠도 없다 — 입구가 물어도 답을 남길 수 없어 「입구부터」가 끝나지 않는다. 잇는다
};

// 이 로그온에 평소 EP 로그인이 한 번 섰나 — 기록을 먼저 읽고, 기록이 없을 때만 눈으로 평소 Edge 를 본다. 아무것도 안 열고 안 쓴다
async function ordinaryLogin() {
  const key = logonKey();
  if (key && readStood() === key) return ORDINARY.STOOD;
  if (key && readMark() === key) return ORDINARY.TRIED;
  const eye = edgeEye(eyeSelect());
  try {
    const look = await lookForPortal(eye);
    if (look.state === LOOK.PORTAL) return ORDINARY.STOOD;
    if (!key && look.state !== LOOK.ABSENT) return ORDINARY.UNSURE;   // 못 읽었고 기록도 못 남기는 PC — 끝없는 「입구부터」를 막는다
    return ORDINARY.MISSING;
  } finally {
    eye.close();
  }
}

module.exports = {
  ORDINARY, SAVED, LOOK, EYE, EYE_GAP_MS, STEADY, TITLES,
  logonKey, readMark, writeMark, readStood, writeStood, readNoSso, writeNoSso, readTitles, ordinaryProfile, hostOf,
  edgeEye, eyeSelect, lookOnce, lookForPortal, tabsState, committedState, ordinaryLogin,
};
