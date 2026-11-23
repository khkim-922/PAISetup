// Edge 프로세스와 그 디버깅 포트 — 깔린 Edge 를 찾고, 디버깅 포트를 연 Edge 를 찾고, 그 포트의 HTTP 자리(버전 · 탭 목록 · 새 탭 · 닫기)에 묻는다. 입구(ep_login.js)와 받는 손(edge_session.js)이 같은 차례로 본다.
//
// 내는 것
//   findEdge() — msedge.exe 의 경로 · 못 찾으면 ""
//   version(port) — 그 포트의 /json/version 답 · 없으면 null
//   debugPorts(cfg) — 이 PC 에서 디버깅 포트를 연 Edge 의 포트(입구의 포트가 먼저)
//   portsToSee(cfg) — 볼 포트의 차례: EDGE_DEBUG_PORT 를 줬으면 그것, 아니면 debugPorts
//   openPort(cfg) — 그 차례에서 처음 답하는 포트 · 없으면 null
//   tabList(port, ms) · newTab(port, url) · closeTarget(port, id) — 디버깅 포트의 탭 목록 · 새 탭 · 탭 닫기
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const VERSION_MS = 2000;             // 디버깅 포트의 /json/version 답 시한 — 포트가 없으면 곧 끊긴다
const FIND_MS = 5000;                // 디버깅 포트를 연 Edge 찾기(debugPorts 의 PowerShell 한 번)의 시한
const CANDIDATES = [                 // Edge 가 깔리는 자리 — 시스템 설치(32 · 64 비트)가 먼저, 사용자 설치가 끝
  [process.env['ProgramFiles(x86)'], 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.ProgramFiles, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
  [process.env.LOCALAPPDATA, 'Microsoft', 'Edge', 'Application', 'msedge.exe'],
];

// 깔린 Edge 의 경로 — CANDIDATES 의 차례로 처음 있는 것
function findEdge() {
  for (const parts of CANDIDATES) {
    if (!parts[0]) continue;
    const exe = path.join(...parts);
    if (fs.existsSync(exe)) return exe;
  }
  return '';
}

// 디버깅 포트 하나에 /json/version 을 묻는다
async function version(port) {
  return fetch(`http://127.0.0.1:${port}/json/version`, { signal: AbortSignal.timeout(VERSION_MS) })
    .then(r => r.json()).catch(() => null);
}

// 디버깅 포트의 탭 목록(/json/list) — 못 읽으면 빈 목록. ms 를 주면 그 시한 안에만 기다린다
async function tabList(port, ms) {
  const got = await fetch(`http://127.0.0.1:${port}/json/list`, ms ? { signal: AbortSignal.timeout(ms) } : undefined).then(r => r.json()).catch(() => []);
  return Array.isArray(got) ? got : [];
}

// 디버깅 포트에 새 탭 하나를 그 주소로 연다(/json/new) — 내는 것: 그 탭 · 못 열었으면 null
const newTab = (port, url) => fetch(`http://127.0.0.1:${port}/json/new?${url}`, { method: 'PUT' }).then(r => r.json()).catch(() => null);

// 디버깅 포트로 탭 하나를 닫는다(/json/close) — 내는 것: 닫았나
const closeTarget = (port, id) => fetch(`http://127.0.0.1:${port}/json/close/${id}`).then(r => r.ok).catch(() => false);

// 이 PC 에서 디버깅 포트를 연 Edge 의 포트 — 입구의 포트가 먼저, 나머지는 찾은 차례. 브라우저 프로세스(--type= 없는 것)의
// 명령줄에서 읽는다 — 포트는 그 Edge 가 처음 뜰 때의 플래그라 명령줄이 원본이다. 못 읽으면(윈도가 아니다 · 시한) 입구의 포트만
function debugPorts(cfg) {
  const found = [];
  if (process.platform === 'win32') {
    try {
      const out = execFileSync('powershell', ['-NoProfile', '-Command',
        "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object { $_.CommandLine -notmatch '--type=' } | " +
        'ForEach-Object { $_.CommandLine }'], { encoding: 'utf8', timeout: FIND_MS, windowsHide: true });
      for (const m of out.matchAll(/--remote-debugging-port=(\d+)/g)) found.push(m[1]);
    } catch {}
  }
  return [...new Set([cfg.port, ...found])];
}

// 볼 포트의 차례 — 준 포트(EDGE_DEBUG_PORT)가 있으면 그것만, 없으면 이 PC 에서 찾는다
const portsToSee = cfg => cfg.ports || debugPorts(cfg);

// 포트를 연 Edge 가운데 받는 손이 먼저 붙는 것 — 그 손과 같은 차례로 처음 답하는 포트
async function openPort(cfg) {
  for (const port of portsToSee(cfg)) if (await version(port)) return port;
  return null;
}

module.exports = { VERSION_MS, findEdge, version, tabList, newTab, closeTarget, debugPorts, portsToSee, openPort };
