// 받는 손의 종료 값과 멈춤 꼴 — 받는 손(edge_session.js)이 내고 입구(ep_login.js)가 받는 닫힌 다섯 값, 두 손이 함께 쓰는 멈춤(Exit)과
// 그 멈춤으로 끝나는 Node 판 재기(needNode).
// 값의 뜻은 받는 손의 머리말 「내는 것」이 든다. 파이썬 쪽 사본은 ep_session.py 의 같은 이름 다섯이다.
'use strict';

const EXIT = { OK: 0, TOOL: 1, NO_EDGE: 2, NOT_LOGGED_IN: 3, ECM_HANDOFF: 4 };

// 명령을 멈춘다 — code 가 종료 값, 메시지가 표준 오류에 낼 까닭이다
class Exit extends Error {
  constructor(code, message) { super(message); this.code = code; }
}

// 이 Node 로 두 손이 도나 — 내장 WebSocket · fetch 가 없으면 도구 고장(1)으로 멈춘다
function needNode() {
  if (typeof WebSocket !== 'function' || typeof fetch !== 'function') throw new Exit(EXIT.TOOL, `Node ${process.version} — 22 이상이 든다(내장 WebSocket)`);
}

module.exports = { EXIT, Exit, needNode };
