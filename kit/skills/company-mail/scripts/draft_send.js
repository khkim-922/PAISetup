// 임시보관함의 메일 한 통을 웹메일 화면 그대로 보내는 손 — 쓰는 사람의 Edge(디버깅 포트)에 붙어 그 메일의 편집 화면에서
// 웹메일의 [보내기]를 누른다. 그래서 웹메일이 보내기 전에 하는 정책 확인 · 첨부 확인을 다 거치고, 보낸편지함에 남는다.
//
// 부르는 꼴
//   node draft_send.js inspect <unid>                 그 메일의 지금 판(받는 사람 · 제목 · 첨부 · 본문 HTML)과 확인 열쇠를 낸다 — 글자는 부르는 쪽이 뽑는다
//   node draft_send.js send <unid> --confirm <열쇠>    지금 판의 열쇠가 같을 때만 보낸다
//   node draft_send.js reply <원래 unid> --type Reply|AllReply|Forward --body-file <HTML 파일> [--to 주소,…] [--cc 주소,…]
//                                                     받은 · 보낸 메일 하나에 웹메일의 [답장] · [전체답장] · [전달] 화면을 열어 글을
//                                                     인용 위에 넣고 [임시저장]만 누른다 — 안 보낸다. 새 임시메일의 unid 와 저장 직전의 판 · 그 판의
//                                                     확인 열쇠를 낸다. 다시 연 판이 같으면 그 열쇠로 send 가 선다 — 다르면 send 가 종료 4 로 멈춘다
//   node draft_send.js revise <unid> [--subject 제목] [--body-file <HTML 파일>] [--to 주소,…] [--cc 주소,…] [--bcc 주소,…]
//   (reply · revise 의 --depts <JSON> — 받는 사람 가운데 부서 주소 → 부서 이름. 그 주소는 조직 하나로 넣는다)
//                                                     임시보관함의 메일 하나를 그 편집 화면에서 고쳐 [임시저장]만 누른다 — 안 보낸다. 준 칸만
//                                                     바꾼다: 제목은 갈아 끼우고, 받는 사람 칸은 비우고 준 사람들로 채우고(빈 값이면 비우기만),
//                                                     글은 본문 맨 앞의 넣은 글 표지(TEXT_MARK) 자리만 갈아 끼운다 — 서명 · 인용은 그대로 둔다.
//                                                     그 자리가 없으면 아무 칸도 안 고치고 종료 2 다. 고친 판과 그 판의 확인 열쇠를 낸다
//   node draft_send.js show <unid>                    임시보관함의 메일 하나를 쓰는 사람의 Edge 에 편집 화면으로 띄워 둔다 — 사람이 거기서
//                                                     확인하고 [보내기]를 누른다. 이미 열린 화면이 있으면 그 탭을 앞으로 올리기만 하고, 닫지 않는다
//   환경변수 EDGE_DEBUG_PORT(기본 9222 — 형제 스킬 ep-login 의 띄우는 손이 여는 포트) · MAIL_SERVER(필수 · http://<메일 서버>) ·
//   MAILBOX_DB(필수 · 02/mail2/<번호>.nsf 꼴) — 둘 다 부르는 쪽(mail.py)이 메일함 주소 하나에서 뽑아 준다
//
// 어느 화면에서 보내나
//   그 메일이 쓰는 사람의 웹메일 탭 안에 이미 편집으로 열려 있으면 **그 화면**에서 보낸다 — 사람이 그 화면에서 고친 것까지 나간다.
//   ⚠ 열린 화면을 두고 따로 열어 보내면 열린 화면의 다음 저장이 저장 번호가 어긋나 새 임시메일로 갈라진다(wSendCheck 실측) —
//   그래서 따로 열지 않는다. 열린 화면이 없으면 최소화한 새 창 하나에 열고, 끝나면 그 창만 닫는다. 쓰는 사람의 탭은 안 닫는다.
//
// 답장 · 전달 화면(reply)
//   웹메일의 버튼과 같은 길이다 — process_doc 이 원래 메일에 이어진 새 문서를 짓고 편집 화면을 열면, 화면이 제목 머리(Re: · Fwd:) ·
//   받는 사람 · 서명 · 인용 · (전달이면) 원래 첨부를 채운다(회사에서 잼). 이 손은 그 위에 글을 서명 앞에 넣고, 전달이면 받는 사람을,
//   어느 쪽이든 더할 참조를 화면의 주소록 길(ag_org_search_json → tokenInput)로 넣은 뒤 화면의 saveDoc(SaveAgent=wSave)을 부른다.
//   ⚠ 편집 화면 주소(/0/<원래 unid>?EditDocument&type=Reply)를 바로 열면 머리 · 인용 · 원래 메일과의 이음이 빠진 원래 메일 자체가 열린다
//   — 늘 process_doc 으로 연다. 저장 전에 멈추면 process_doc 이 지은 문서는 임시보관함에 안 서고 남는다(웹메일에서 창을 닫은 것과 같다).
//
// 무엇을 내나
//   표준 출력에 JSON 한 줄 — {where, state, token} 또는 send 의 {pressed, where, ...} 또는 reply 의 {unid, state, token} 또는 revise 의 {unid, where, state, token}. send 의 0 은 「발송 확인에 예 하고 저장 답이
//   왔다」까지다 — 나갔나는 부르는 쪽이 보낸편지함 · 임시보관함으로 가린다(보낸 뒤의 알림 · 늦은 자동저장은 이 손이 못 가린다). 종료 값 0 됐다 · 1 도구 · 화면 오류 ·
//   2 그 메일을 못 찾았다 · 3 Edge 에 못 붙었다(스킬 ep-login) · 4 열쇠가 지금 판과 다르다(안 보냈다) · 5 웹메일이 다른 물음을 띄웠다(안 보냈다).
//   show 는 {unid, where} 를 낸다
'use strict';
const crypto = require('crypto');

const SERVER = (process.env.MAIL_SERVER || '').trim().replace(/\/+$/, '');
const PORT = ((process.env.EDGE_DEBUG_PORT || '').split(',')[0] || '').trim() || '9222';
// 앞의 / 는 붙여도 떼도 된다 — Git Bash 가 /로 시작하는 값을 윈도 경로로 바꿔 넘기므로 부르는 쪽은 떼고 준다
const DB = '/' + (process.env.MAILBOX_DB || '').trim().replace(/^\/+/, '');
const READY_SECONDS = 60;          // 편집 화면이 다 서기를 기다리는 시한 — 편집기 · 첨부 칸이 늦게 선다
const SEND_SECONDS = 120;          // 보내기를 누른 뒤 저장 답을 기다리는 시한 — 첨부 확인이 든다
const TOKEN_LENGTH = 12;
// 웹메일이 보내기 전에 묻는 확인 — 이 꼴만 「예」 한다. 앞에 「첨부 없음」 안내 줄이 붙을 수 있다(실측). 다른 물음은 다 「아니오」 하고 멈춘다
const SEND_CONFIRM = /^(첨부 문서가 없는 메일 입니다\.\s*)?메일을 발송 하시겠습니까\?\s*$/;
// 임시저장이 끝나면 화면이 묻는 것 — 「아니오」 하면 창이 닫힌다(실측). 저장 전에 뜬 다른 물음은 다 「아니오」 하고 멈춘다
const SAVED_ASK = /^임시저장이 완료되었습니다/;
const REPLY_TYPES = ['Reply', 'AllReply', 'Forward'];
// 넣은 글을 감싼 div 의 id 머리 — 임시메일을 다시 고칠 때 이 자리만 갈아 끼운다. 새 메일을 저장하는 쪽(mail.py 의 TEXT_MARK)과 같은 글자다
const TEXT_MARK = 'cm-text-';
const PEOPLE_FIELDS = {'--to': 'send_to', '--cc': 'copy_to', '--bcc': 'bcopy_to'};   // revise 의 인자 → 편집 화면의 받는 사람 칸 id
// reply · revise 의 --depts <JSON> — 받는 사람 가운데 부서 주소 → 부서 이름(부르는 쪽이 받아 둔 조직도에서 짓는다)
const deptsOf = rest => { const i = rest.indexOf('--depts'); return i < 0 ? {} : JSON.parse(rest[i + 1] || '{}'); };
const SAVE_SECONDS = 60;           // [임시저장] 뒤 저장 답을 기다리는 시한 — 전달의 첨부를 다시 싣는 데 든다
const BODY_SECONDS = 10;           // 편집기가 넣은 글을 그리기를 기다리는 시한 — setBodyValue 는 늦게 든다(실측)
const LOOKUP_MS = 20000;           // 주소록 한 번의 시한 — 답이 없어도 이 손이 제 창을 닫고 끝나게
const EXIT = {OK: 0, FAIL: 1, MISSING: 2, NO_EDGE: 3, STALE: 4, ASKED: 5};

const POLL_MS = 250;               // 화면 · 답을 기다리며 다시 보는 눈금

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
const fail = (code, message, extra = {}) => { const e = new Error(message); e.code = code; e.extra = extra; return e; };

// ── Edge 에 붙기 ───────────────────────────────────────────────────────────

async function devtools(path) {
  try {
    const r = await fetch(`http://127.0.0.1:${PORT}${path}`);
    return await r.json();
  } catch (e) {
    throw fail(EXIT.NO_EDGE, `Edge 에 못 붙었다 — 127.0.0.1:${PORT} 에 디버깅 포트가 없다. 스킬 ep-login 으로 Edge 를 띄운다`);
  }
}

// CDP 한 줄 — 보내고 답을 기다린다. 사건은 on 으로 받는다
function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let id = 0;
    const wait = {}, handlers = [];
    const cdp = {
      send: (method, params = {}, sessionId) => new Promise((ok, no) => {
        const i = ++id;
        wait[i] = m => (m.error ? no(fail(EXIT.FAIL, `${method}: ${m.error.message}`)) : ok(m.result));
        ws.send(JSON.stringify(sessionId ? {id: i, method, params, sessionId} : {id: i, method, params}));
      }),
      on: f => handlers.push(f),
      close: () => ws.close(),
    };
    ws.onmessage = ev => {
      const m = JSON.parse(ev.data);
      if (m.id && wait[m.id]) { wait[m.id](m); delete wait[m.id]; return; }
      handlers.forEach(f => f(m));
    };
    ws.onopen = () => resolve(cdp);
    ws.onerror = () => reject(fail(EXIT.NO_EDGE, 'Edge 의 디버깅 줄이 끊겼다'));
  });
}

// 이 메일의 편집 화면 주소인가 — 쓰는 사람 탭의 안쪽 프레임이든 새 창이든 /0/<unid>?EditDocument 꼴이다
const isEditor = (url, unid) => url.toUpperCase().includes(`/0/${unid}`) && /\?editdocument/i.test(url);

function frames(tree) {
  const out = [];
  const walk = n => { out.push(n.frame); (n.childFrames || []).forEach(walk); };
  walk(tree);
  return out;
}

// ── 편집 화면 찾기 · 열기 ─────────────────────────────────────────────────────

// 쓰는 사람의 탭 가운데 이 메일의 편집 화면을 든 것 — {target, frameId} 또는 null
async function findOpenEditor(cdp, unid) {
  const pages = (await devtools('/json/list')).filter(t => t.type === 'page' && t.url.startsWith(SERVER));
  for (const t of pages) {
    const {sessionId} = await cdp.send('Target.attachToTarget', {targetId: t.id, flatten: true});
    const {frameTree} = await cdp.send('Page.getFrameTree', {}, sessionId);
    const f = frames(frameTree).find(x => isEditor(x.url, unid));
    if (f) return {targetId: t.id, sessionId, frameId: f.id, opened: false};
    await cdp.send('Target.detachFromTarget', {sessionId});
  }
  return null;
}

// 열린 화면이 없으면 최소화한 새 창 하나에 연다 — 쓰는 사람의 창 위로 안 뜬다. ``url`` 을 주면 그 주소(답장 · 전달 화면)를 연다
async function openEditor(cdp, unid, url = `${SERVER}${DB}/0/${unid}?EditDocument&type=EditMode&opentype=popup`) {
  const {targetId} = await cdp.send('Target.createTarget', {url: 'about:blank', newWindow: true, background: true});
  try {
    const {windowId} = await cdp.send('Browser.getWindowForTarget', {targetId});
    await cdp.send('Browser.setWindowBounds', {windowId, bounds: {windowState: 'minimized'}});
  } catch (e) { /* 창을 못 접어도 보내기는 같다 — 화면에 잠깐 뜰 뿐이다 */ }
  const {sessionId} = await cdp.send('Target.attachToTarget', {targetId, flatten: true});
  await cdp.send('Page.enable', {}, sessionId);
  await cdp.send('Page.navigate', {url}, sessionId);
  const {frameTree} = await cdp.send('Page.getFrameTree', {}, sessionId);
  return {targetId, sessionId, frameId: frameTree.frame.id, opened: true};
}

// 그 프레임에서 식 하나 — 프레임마다 실행 자리가 따로라 자리를 받아 둔다
async function evaluator(cdp, ed) {
  const contexts = {};
  cdp.on(m => {
    if (m.sessionId === ed.sessionId && m.method === 'Runtime.executionContextCreated' && m.params.context.auxData?.isDefault)
      contexts[m.params.context.auxData.frameId] = m.params.context.id;
  });
  await cdp.send('Runtime.enable', {}, ed.sessionId);
  return async expression => {
    for (let i = 0; i < 20 && !contexts[ed.frameId]; i++) await sleep(250);
    const r = await cdp.send('Runtime.evaluate', {expression, contextId: contexts[ed.frameId], returnByValue: true, awaitPromise: true}, ed.sessionId);
    if (r.exceptionDetails) throw fail(EXIT.FAIL, `편집 화면에서 식이 깨졌다: ${r.exceptionDetails.text}`);
    return r.result.value;
  };
}

// 편집 화면이 다 섰나 — 편집기 · 받는 사람 칸 · 첨부 칸이 늦게 선다
const READY = "typeof _form!=='undefined' && window.isEditorLoaded===true && typeof am_handler!=='undefined'"
  + " && !!(am_handler.xam && am_handler.xam.g) && typeof $==='function' && !!$('#send_to').tokenInput";

// 지금 판 — 사람이 그 화면에서 고친 것까지 든다. 확인 열쇠는 이 위에 선다
const STATE = `JSON.stringify({
  subject: document.forms[0].Subject.value,
  to: $('#send_to').tokenInput('get').map(x => x.key),
  cc: $('#copy_to').tokenInput('get').map(x => x.key),
  bcc: $('#bcopy_to').tokenInput('get').map(x => x.key),
  files: am_handler.xam.g.getFileList().filter(f => f.status !== 'remove').map(f => f.name + ':' + f.size),
  body: (_PWEC.getHTML() || '')
})`;

async function readState(ev) {
  if (!(await waitFor(READY_SECONDS, () => ev(READY).catch(() => false)))) throw fail(EXIT.FAIL, `편집 화면이 ${READY_SECONDS} 초 안에 다 서지 않았다`);
  return JSON.parse(await ev(STATE));
}

// 본문 안 그림 주소의 문서 번호(…nsf/0/<unid>/Body/…)는 열쇠에서 뺀다 — 서명 그림은 저장 전엔 서명 문서를, 저장 뒤엔 새
// 임시메일 자신을 가리켜(회사에서 잼), 빼지 않으면 save-reply 가 낸 열쇠가 사람이 본 것과 같은 판에서도 늘 어긋난다
const IN_DOC = /(\.nsf\/0\/)[0-9a-f]{32}(?=\/)/gi;
const tokenOf = s => crypto.createHash('sha256')
  .update(JSON.stringify([s.subject, s.to, s.cc, s.bcc, s.files, s.body.replace(IN_DOC, '$1-')])).digest('hex').slice(0, TOKEN_LENGTH);

// ── 보내기 ─────────────────────────────────────────────────────────────────

// 웹메일의 [보내기]를 누르고, 발송 확인만 「예」 한다. 발송 확인 **앞에** 뜬 다른 물음(사외 결재 · 경고)은 「아니오」 하고 그 글을 들고
// 멈춘다 — 그 뒤로는 안 나간다. 발송 확인에 「예」 한 뒤 뜬 것(완료 알림 같은 것)은 「예」 하고 글만 든다 — 이미 나갔을 수 있어
// 이 손이 「안 보냈다」고 하지 않는다. 저장 답이 오면 「눌렀다」를 낸다
async function pressSend(cdp, ed, ev, unid) {
  const asked = [];
  let saved = null, confirmed = false;
  cdp.on(m => {
    if (m.sessionId !== ed.sessionId) return;
    if (m.method === 'Page.javascriptDialogOpening') {
      const isSend = m.params.type === 'confirm' && SEND_CONFIRM.test(m.params.message);
      const ok = isSend || confirmed;
      if (isSend) confirmed = true;
      asked.push({message: m.params.message, accepted: ok, after: !isSend && ok});
      cdp.send('Page.handleJavaScriptDialog', {accept: ok}, ed.sessionId).catch(() => {});
    }
    if (m.method === 'Network.responseReceived' && m.params.response.status === 200 && isEditor(m.params.response.url, unid)
        && /&seq=1/i.test(m.params.response.url)) saved = m.params.requestId;
  });
  await cdp.send('Page.enable', {}, ed.sessionId);
  await cdp.send('Network.enable', {}, ed.sessionId);
  await ev("_form.clickMailSend(); 'pressed'");
  const done = await waitFor(SEND_SECONDS, () => {
    if (asked.some(a => !a.accepted)) throw fail(EXIT.ASKED, '웹메일이 발송 확인 앞에 다른 물음을 띄워 「아니오」 했다 — 안 보냈다',
                                                  {asked: asked.map(a => a.message)});
    return saved;
  });
  if (done) return asked.map(a => a.message);
  throw fail(EXIT.FAIL, `보내기를 누르고 ${SEND_SECONDS} 초 안에 저장 답이 안 왔다 — 보낸편지함 · 임시보관함을 보고 확인한다`,
             {asked: asked.map(a => a.message)});
}


// ── 답장 · 전달 화면에서 임시저장 ─────────────────────────────────────────────

// 원래 메일에 웹메일의 [답장] · [전체답장] · [전달]을 누른 것과 같은 화면을 최소화한 새 창에 연다 — process_doc 이 새 문서를 짓고
// 그 편집 화면으로 넘긴다. 넘어간 뒤의 프레임을 쓴다
async function openReplyEditor(cdp, unid, type) {
  const url = `${SERVER}${DB}/process_doc?openagent&action=${type}&forward_deny_type=&forward_deny_fromname=&unid=${unid}`
    + '&lang=kor&callfrom=&imapuser=0&owner=&timezone=+540&opentype=popup';
  const ed = await openEditor(cdp, unid, url);
  const frame = await waitFor(READY_SECONDS, async () => {
    const {frameTree} = await cdp.send('Page.getFrameTree', {}, ed.sessionId);
    return /\?editdocument/i.test(frameTree.frame.url) && frameTree.frame;
  });
  if (frame) return {...ed, frameId: frame.id};
  throw fail(EXIT.MISSING, `[${type}] 화면이 ${READY_SECONDS} 초 안에 안 열렸다 — 원래 메일이 없거나 웹메일이 거절했다: ${unid}`);
}

// 받는 사람 칸들에 사내 주소록의 사람 · 부서를 넣는다 — 화면의 「비서 참조자 자동추가」와 같은 길(ag_org_search_json → tokenInput · duplicate_list).
// ``pairs`` 는 [칸 id, 주소] 들, ``clear`` 는 넣기 전에 비울 칸 id 들. 주소록에는 함께 묻고, 다 선 뒤에야 칸을 비우고 준 차례대로
// 넣는다 — 한 주소라도 사람이 꼭 하나가 아니면 아무 칸도 안 건드리고 「주소 — 까닭」을 낸다(쓰는 사람이 연 화면에 반쯤 고친 판을
// 안 남긴다). 다 넣었으면 빈 글자
// ``depts`` 는 부서 주소 → 부서 이름 — 그 주소는 사람 대신 조직 하나로 넣는다(고름 창에서 조직을 체크한 것과 같은 항목). 주소록 찾기는
// 부서를 type=org 에만 내고(type=memo 는 부서 0 곳) 부서 주소로는 안 내고 부서 이름으로 낸다(회사에서 잼) — 이름으로 찾고 주소가
// 같은 부서 하나를 고른다
const addPeople = (pairs, clear = [], depts = {}) => `(function(){
  var pairs = ${JSON.stringify(pairs)}, clear = ${JSON.stringify(clear)}, depts = ${JSON.stringify(depts)};
  function find(addr){ return new Promise(function(ok){
    var dept = depts[addr.toLowerCase()];
    $.ajax({type:'GET', dataType:'json', cache:false, timeout:${LOOKUP_MS},
      url:'/' + _form.info.orgDb + '/ag_org_search_json?OpenAgent&type=' + (dept ? 'org' : 'memo') + '&company=' + add_code
        + '&search_key=' + encodeURIComponent(dept || addr) + (dept ? '' : '&email_search_YN=Y'),
      success:function(d){
        var hit = ((dept ? d.dept : d.user) || []).filter(function(u){ return (u.email || '').toLowerCase() === addr.toLowerCase(); });
        ok(hit.length === 1 ? {hit: hit[0]} : {why: (dept ? '그 주소의 부서가 주소록에 ' : '그 주소의 사람이 주소록에 ') + hit.length + (dept ? ' 곳이다' : ' 명이다')});
      },
      error:function(x){ ok({why: '주소록이 답하지 않았다(' + x.status + ')'}); }});
  }); }
  return Promise.all(pairs.map(function(p){ return find(p[1]); })).then(function(got){
    for (var i = 0; i < got.length; i++) if (got[i].why) return pairs[i][1] + ' — ' + got[i].why;
    clear.forEach(function(id){ $('#' + id).tokenInput('clear'); });
    if (clear.length) _form.setRecipients(true);
    for (var j = 0; j < got.length; j++) {
      window.duplicate_list[got[j].hit.key] = got[j].hit;
      $('#' + pairs[j][0]).tokenInput('add', got[j].hit);
      _form.setRecipients(true);
    }
    return '';
  });
})()`;

// 문서 꼴 HTML(<html><head><style>…<body>…)은 body 안만 — 편집기 본문 안에 문서를 겹쳐 넣지 않는다. <style> 은 body 앞에 붙여 살린다
const innerBody = h => {
  const m = h.match(/<body[^>]*>([\s\S]*?)(<\/body>|$)/i);
  if (!m) return h;
  const styles = (h.slice(0, m.index).match(/<style\b[\s\S]*?<\/style>/gi) || []).join('');
  return styles + m[1];
};

// 편집기의 본문 맨 앞(서명 · 인용 앞)에 글을 넣는다 — 편집기가 늦게 그려서, 넣은 글이 지금 판에 설 때까지 기다린다. 섰나는 글을 감싼
// 표지(id)로 가린다 — 글자를 맞추면 편집기가 엔티티를 다시 쓴 판 · 그림만 든 글 · 인용과 겹친 글을 못 가린다
async function putBody(ev, html) {
  const mark = TEXT_MARK + crypto.randomBytes(6).toString('hex');
  const piece = `<div id="${mark}">${innerBody(html)}</div>`;
  await ev(`(function(){ var h = _PWEC.getHTML(); var i = h.search(/<body[^>]*>/i); var j = h.toLowerCase().lastIndexOf('</body>');
    var b = i < 0 ? h : h.slice(h.indexOf('>', i) + 1, j < 0 ? undefined : j);
    _PWEC.setBodyValue(${JSON.stringify(piece)} + b); return 1; })()`);
  if (await waitFor(BODY_SECONDS, async () => (await ev('_PWEC.getHTML()')).includes(mark))) return;
  throw fail(EXIT.FAIL, `편집기에 넣은 글이 ${BODY_SECONDS} 초 안에 본문에 안 섰다 — 저장하지 않았다`);
}

// 화면의 [임시저장](saveDoc — SaveAgent=wSave)을 누른다. 저장 뒤 「창을 유지하시겠습니까」 만 답하고 — 이 손이 연 창이면 「아니오」
// (창이 닫힌다), ``keep`` 이면 「예」(쓰는 사람이 연 화면은 닫지 않는다) — 저장 전에 뜬 다른 물음은 「아니오」 하고 그 글을 들고 멈춘다
async function pressSave(cdp, ed, ev, keep = false) {
  const asked = [];
  let saved = false;
  cdp.on(m => {
    if (m.sessionId !== ed.sessionId || m.method !== 'Page.javascriptDialogOpening') return;
    const done = SAVED_ASK.test(m.params.message);
    if (done) saved = true; else asked.push(m.params.message);
    cdp.send('Page.handleJavaScriptDialog', {accept: done && keep}, ed.sessionId).catch(() => {});
  });
  await cdp.send('Page.enable', {}, ed.sessionId);
  await ev("_form.saveDoc(); 'pressed'");
  const done = await waitFor(SAVE_SECONDS, () => {
    if (saved) return true;
    if (asked.length) throw fail(EXIT.ASKED, '웹메일이 임시저장 앞에 다른 물음을 띄워 「아니오」 했다 — 저장하지 않았다', {asked});
    return false;
  });
  if (done) return asked;
  throw fail(EXIT.FAIL, `[임시저장]을 누르고 ${SAVE_SECONDS} 초 안에 저장됐다는 말이 안 왔다 — 임시보관함을 보고 확인한다`, {asked});
}

async function saveReply(cdp, unid, rest) {
  const opt = name => { const i = rest.indexOf(name); return i < 0 ? '' : (rest[i + 1] || ''); };
  const type = opt('--type');
  if (!REPLY_TYPES.includes(type)) throw fail(EXIT.FAIL, `--type 은 ${REPLY_TYPES.join(' · ')} 가운데 하나다`);
  const html = require('fs').readFileSync(opt('--body-file'), 'utf8');
  const list = s => s.split(',').map(x => x.trim()).filter(Boolean);
  const to = list(opt('--to')), cc = list(opt('--cc'));
  if (type === 'Forward' && !to.length) throw fail(EXIT.FAIL, '전달은 --to 를 받는다 — 화면이 받는 사람을 비워 연다');
  const ed = await openReplyEditor(cdp, unid, type);
  try {
    const ev = await evaluator(cdp, ed);
    await readState(ev);
    const draft = await ev('_form.info.unid');
    const pairs = [...to.map(a => ['send_to', a]), ...cc.map(a => ['copy_to', a])];
    const why = pairs.length ? await ev(addPeople(pairs, to.length ? ['send_to'] : [], deptsOf(rest))) : '';
    if (why) throw fail(EXIT.MISSING, `${why}. 저장하지 않았다`);
    await putBody(ev, html);
    const state = JSON.parse(await ev(STATE));
    const asked = await pressSave(cdp, ed, ev);
    return {unid: draft, type, asked, state, token: tokenOf(state)};
  } finally {
    await cdp.send('Target.closeTarget', {targetId: ed.targetId}).catch(() => {});
  }
}

// 이 메일에 넣은 글의 자리 — 본문의 첫 표지이고 **그 앞에 다른 글이 없을 때만** 그것이다. 넣은 글은 늘 본문 맨 앞에 서는데, 표지는
// 인용한 옛 메일에도 들 수 있어(이 손으로 보낸 메일에 웹메일에서 직접 쓴 답장) 앞에 글이 있는 표지를 고르면 인용을 갈아 끼운다
const FIND_TEXT = `function(doc){
    var el = doc.querySelector('[id^="${TEXT_MARK}"]');
    if (!el) return null;
    var before = doc.createRange(); before.setStart(doc.body, 0); before.setEndBefore(el);
    return before.toString().trim() ? null : el; }`;
const PARSED = "new DOMParser().parseFromString(_PWEC.getHTML() || '', 'text/html')";
const NO_TEXT = '이 임시메일의 본문 맨 앞에 넣은 글의 표지가 없다 — 고치지 않았다(통째로 갈면 서명 · 인용이 날아간다)';

// 넣은 글의 자리만 새 글로 갈아 끼운다 — 서명 · 인용 · 표지 밖의 것은 그대로다. 갈아 끼운 자리는 새 표지를 달아, 편집기가 그 판을
// 그렸나를 그 표지로 가린다. 자리가 없으면 고치지 않고 멈춘다
async function swapText(ev, html) {
  const mark = TEXT_MARK + crypto.randomBytes(6).toString('hex');
  const swapped = await ev(`(function(){
    var doc = ${PARSED};
    var el = (${FIND_TEXT})(doc);
    if (!el) return false;
    el.id = ${JSON.stringify(mark)};
    el.innerHTML = ${JSON.stringify(innerBody(html))};
    _PWEC.setBodyValue(doc.body.innerHTML);
    return true;
  })()`);
  if (!swapped) throw fail(EXIT.MISSING, NO_TEXT);
  if (await waitFor(BODY_SECONDS, async () => (await ev('_PWEC.getHTML()')).includes(mark))) return;
  throw fail(EXIT.FAIL, `편집기에 넣은 글이 ${BODY_SECONDS} 초 안에 본문에 안 섰다 — 저장하지 않았다`);
}

// 임시보관함의 메일 하나를 그 편집 화면에서 고쳐 [임시저장]한다 — 쓰는 사람이 그 메일을 편집으로 열어 두었으면 그 화면에서(따로 열면
// 다음 저장이 갈라진다), 아니면 최소화한 창에서. 준 칸만 바꾼다
async function reviseDraft(cdp, unid, rest) {
  const has = name => rest.includes(name);
  const opt = name => (has(name) ? rest[rest.indexOf(name) + 1] || '' : '');
  const list = s => s.split(',').map(x => x.trim()).filter(Boolean);
  const html = has('--body-file') ? require('fs').readFileSync(opt('--body-file'), 'utf8') : null;
  const fields = Object.keys(PEOPLE_FIELDS).filter(has);
  if (!has('--subject') && html === null && !fields.length) throw fail(EXIT.FAIL, 'revise 는 고칠 칸을 하나는 받는다');
  const ed = (await findOpenEditor(cdp, unid)) || (await openEditor(cdp, unid));
  try {
    const ev = await evaluator(cdp, ed);
    await readState(ev).catch(e => {
      throw e.code === EXIT.FAIL && ed.opened ? fail(EXIT.MISSING, `임시보관함에 이 메일이 없거나 열리지 않는다: ${unid}`) : e;
    });
    // 못 고칠 까닭(넣은 글의 자리가 없다 · 주소록에 그 사람이 없다)을 다 가린 뒤에야 화면을 건드린다 — 쓰는 사람이 연 화면에
    // 저장 안 된 반쪽 판을 안 남긴다
    if (html !== null && !(await ev(`!!(${FIND_TEXT})(${PARSED})`))) throw fail(EXIT.MISSING, NO_TEXT);
    const pairs = fields.flatMap(name => list(opt(name)).map(a => [PEOPLE_FIELDS[name], a]));
    const why = fields.length ? await ev(addPeople(pairs, fields.map(name => PEOPLE_FIELDS[name]), deptsOf(rest))) : '';
    if (why) throw fail(EXIT.MISSING, `${why}. 저장하지 않았다`);
    if (html !== null) await swapText(ev, html);
    if (has('--subject')) await ev(`document.forms[0].Subject.value = ${JSON.stringify(opt('--subject'))}; 1`);
    const state = JSON.parse(await ev(STATE));
    const asked = await pressSave(cdp, ed, ev, !ed.opened);
    return {unid, where: ed.opened ? '새 창(최소화)' : '쓰는 사람이 연 화면', asked, state, token: tokenOf(state)};
  } finally {
    if (ed.opened) await cdp.send('Target.closeTarget', {targetId: ed.targetId}).catch(() => {});
    else await cdp.send('Target.detachFromTarget', {sessionId: ed.sessionId}).catch(() => {});
  }
}

// 그 메일의 편집 화면을 쓰는 사람의 Edge 에 띄워 둔다 — 열린 화면이 있으면 그 탭을 앞으로 올리고(따로 열면 열린 화면의 다음 저장이
// 갈라진다), 없으면 보이는 새 창에 연다. 이 손은 그 창을 닫지 않는다 — 사람이 확인하고 보내거나, 뒤의 revise · send 가 그 화면을 쓴다
async function showDraft(cdp, unid) {
  const open = await findOpenEditor(cdp, unid);
  if (open) {
    await cdp.send('Target.activateTarget', {targetId: open.targetId}).catch(() => {});
    await cdp.send('Target.detachFromTarget', {sessionId: open.sessionId}).catch(() => {});
    return {unid, where: '쓰는 사람이 연 화면'};
  }
  await cdp.send('Target.createTarget', {url: `${SERVER}${DB}/0/${unid}?EditDocument&type=EditMode&opentype=popup`, newWindow: true});
  return {unid, where: '새 창'};
}

async function main() {
  const [verb, rawUnid, ...rest] = process.argv.slice(2);
  const unid = (rawUnid || '').toUpperCase();
  if (!['inspect', 'send', 'reply', 'revise', 'show'].includes(verb) || !/^[0-9A-F]{32}$/.test(unid)) {
    throw fail(EXIT.FAIL, '꼴: inspect|send <unid> [--confirm 열쇠] · reply <원래 unid> --type … --body-file … · revise <unid> [--subject …] … · show <unid>');
  }
  if (!/^\/[\w/]+\.nsf$/i.test(DB)) throw fail(EXIT.FAIL, 'MAILBOX_DB 가 메일함 경로(/…/<번호>.nsf)가 아니다');
  if (!/^https?:\/\/[^/]+$/i.test(SERVER)) throw fail(EXIT.FAIL, 'MAIL_SERVER 가 메일 서버 주소(http://<서버>)가 아니다');
  if (verb === 'reply' || verb === 'revise' || verb === 'show') {
    const cdp = await connect((await devtools('/json/version')).webSocketDebuggerUrl);
    const run = {reply: saveReply, revise: reviseDraft, show: showDraft}[verb];
    try { return await run(cdp, unid, rest); } finally { cdp.close(); }
  }
  const confirm = rest[rest.indexOf('--confirm') + 1];
  if (verb === 'send' && (rest.indexOf('--confirm') < 0 || !confirm)) throw fail(EXIT.FAIL, 'send 는 --confirm <열쇠> 를 받는다');
  const cdp = await connect((await devtools('/json/version')).webSocketDebuggerUrl);
  let ed = null;
  try {
    ed = (await findOpenEditor(cdp, unid)) || (await openEditor(cdp, unid));
    const where = ed.opened ? '새 창(최소화)' : '쓰는 사람이 연 화면';
    const ev = await evaluator(cdp, ed);
    const state = await readState(ev).catch(e => {
      throw e.code === EXIT.FAIL && ed.opened ? fail(EXIT.MISSING, `임시보관함에 이 메일이 없거나 열리지 않는다: ${unid}`) : e;
    });
    const token = tokenOf(state);
    if (verb === 'inspect') return {where, state, token};
    if (token !== confirm) throw fail(EXIT.STALE, '확인 열쇠가 지금 판과 다르다 — 확인한 뒤 바뀌었다. 안 보냈다');
    const asked = await pressSend(cdp, ed, ev, unid);
    return {pressed: true, where, asked, subject: state.subject, to: state.to.length, cc: state.cc.length, bcc: state.bcc.length};
  } finally {
    if (ed && ed.opened) await cdp.send('Target.closeTarget', {targetId: ed.targetId}).catch(() => {});
    else if (ed) await cdp.send('Target.detachFromTarget', {sessionId: ed.sessionId}).catch(() => {});
    cdp.close();
  }
}

main().then(out => { console.log(JSON.stringify(out)); process.exit(EXIT.OK); })
  .catch(e => { console.log(JSON.stringify({error: e.message, ...(e.extra || {})})); process.exit(e.code ?? EXIT.FAIL); });
