// 쓰는 사람의 Edge(디버깅 포트)에서 화면을 다루는 손들이 함께 쓰는 줄 — 디버깅 포트에 묻기 · CDP 한 줄 · 기다리기 · 프레임 펴기.
// 어느 탭 · 어느 프레임에서 무엇을 누르나는 손마다 달라 손이 든다. 여기는 Edge 와 말을 주고받는 자리만 든다.
//
// 부르는 꼴 — 형제 스킬의 손이 상대 경로로 싣는다(스킬 홈에 나란히 깔린다)
//   const { sleep, waitFor, framesOf, edgeLine } = require('../../ep-login/scripts/edge_cdp.js');
//   const { devtools, connect } = edgeLine({fail: EXIT.FAIL, noEdge: EXIT.NO_EDGE});
//   const cdp = await connect((await devtools('/json/version')).webSocketDebuggerUrl);
//   await cdp.send('Page.enable', {}, sessionId);
//
// 내는 것
//   sleep(ms) · waitFor(seconds, probe) · framesOf(frameTree)
//   edgeLine({fail, noEdge, seconds}) — 손 하나의 줄 {devtools, connect}. ``fail`` · ``noEdge`` 는 그 손의 종료 값이다(손마다 표가
//     달라 손이 준다). 여기서 던지는 오류는 Error 에 ``code`` 로 그 값을 단다 — 손의 끝이 그 값으로 끝난다
//   - devtools(path) — 127.0.0.1 의 디버깅 포트에 물은 /json/… 답(JSON). 못 받으면 noEdge
//   - connect(wsUrl) — CDP 한 줄 {send, on, off, close}. 못 열면 noEdge
//     send(method, params, sessionId, limit) 는 답의 result 를 낸다. Edge 가 오류로 답하면 fail 「method: Edge 의 말」, ``limit`` 초
//     (안 주면 줄의 시한 ``seconds``, 그것도 안 주면 REPLY_SECONDS) 안에 답이 없으면 fail 「method: N 초 안에 답이 없다 — 그 탭이 멈췄다」
//     on(f) 는 답이 아닌 글(사건)마다 f(글) 을 부르고, off(f) 는 그 귀를 뗀다
//
// 환경변수 EDGE_DEBUG_PORT(기본 9222 — 입구 ep_login.js 가 여는 포트. 쉼표로 여럿이면 첫 것)
// 필요한 것: Node 22 이상(내장 WebSocket · fetch). npm 꾸러미는 안 든다.
'use strict';

const PORT = require('./edge_session.js').settings().port;   // 기본 포트와 EDGE_DEBUG_PORT 읽기는 받는 손 한 자리다
const POLL_MS = 250;               // 화면 · 답을 기다리며 다시 보는 눈금
const REPLY_SECONDS = 15;          // Edge 의 답 하나를 기다리는 시한 — 붙기 · 식 하나는 곧 답해 넉넉한 값이다

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ``probe`` 가 참을 낼 때까지 POLL_MS 눈금으로 다시 본다 — 그 값을 내고, ``seconds`` 가 지나도록 안 서면 undefined. probe 가 던지면 그대로 나간다
async function waitFor(seconds, probe) {
  const until = Date.now() + seconds * 1000;
  for (;;) {
    const got = await probe();
    if (got) return got;
    if (Date.now() >= until) return undefined;
    await sleep(POLL_MS);
  }
}

// Page.getFrameTree 의 답(frameTree)을 프레임의 목록으로 편다 — 바깥 프레임이 먼저다
function framesOf(frameTree) {
  const out = [];
  const walk = n => { out.push(n.frame); (n.childFrames || []).forEach(walk); };
  walk(frameTree);
  return out;
}

function edgeLine({fail, noEdge, seconds = REPLY_SECONDS}) {
  const stop = (code, message) => { const e = new Error(message); e.code = code; return e; };

  async function devtools(path) {
    try {
      return await (await fetch(`http://127.0.0.1:${PORT}${path}`)).json();
    } catch (e) {
      throw stop(noEdge, `Edge 에 못 붙었다 — 127.0.0.1:${PORT} 에 디버깅 포트가 없다. 스킬 ep-login 으로 Edge 를 띄운다`);
    }
  }

  // CDP 한 줄 — 보내고 답을 기다린다. 사건은 on 으로 받고 off 로 그만 받는다
  function connect(wsUrl) {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(wsUrl);
      let id = 0;
      const wait = {}, handlers = [];
      const cdp = {
        // 답 하나에 시한을 둔다 — 멈춘 탭(남의 손이 잡은 탭 · 숨은 물음 상자)은 답을 영영 안 해, 시한 없이는 손이 통째로 선다.
        // 화면의 긴 일(주소록 묻기 · 저장)이 끝나야 답하는 부름은 부르는 쪽이 그 일의 시한을 ``limit`` 으로 준다
        send: (method, params = {}, sessionId, limit = seconds) => new Promise((ok, no) => {
          const i = ++id;
          const timer = setTimeout(() => { delete wait[i]; no(stop(fail, `${method}: ${limit} 초 안에 답이 없다 — 그 탭이 멈췄다`)); }, limit * 1000);
          wait[i] = m => { clearTimeout(timer); return m.error ? no(stop(fail, `${method}: ${m.error.message}`)) : ok(m.result); };
          ws.send(JSON.stringify(sessionId ? {id: i, method, params, sessionId} : {id: i, method, params}));
        }),
        on: f => handlers.push(f),
        off: f => { const i = handlers.indexOf(f); if (i >= 0) handlers.splice(i, 1); },
        close: () => ws.close(),
      };
      ws.onmessage = ev => {
        const m = JSON.parse(ev.data);
        if (m.id && wait[m.id]) { wait[m.id](m); delete wait[m.id]; return; }
        handlers.slice().forEach(f => f(m));   // 사본을 돈다 — 받는 귀가 도중에 저를 떼도(off) 그 사건이 다른 귀를 건너뛰지 않는다
      };
      ws.onopen = () => resolve(cdp);
      ws.onerror = () => reject(stop(noEdge, 'Edge 의 디버깅 줄이 끊겼다'));
    });
  }

  return {devtools, connect};
}

module.exports = { sleep, waitFor, framesOf, edgeLine };
