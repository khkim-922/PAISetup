// 임시보관함의 메일 한 통을 웹메일 화면 그대로 보내는 손 — 쓰는 사람의 Edge(디버깅 포트)에 붙어 그 메일의 편집 화면에서 웹메일의
// [보내기]를 누른다. 그래서 웹메일이 보내기 전에 하는 정책 · 첨부 확인을 다 거치고 보낸편지함에 남는다.
//
// 부르는 꼴
//   node draft_send.js inspect <unid>                 그 메일의 지금 판(받는 사람 · 제목 · 첨부 · 본문 HTML)과 확인 열쇠를 낸다
//   node draft_send.js send <unid> --confirm <열쇠>    지금 판의 열쇠가 같을 때만 보낸다
//   node draft_send.js edit <unid> --start reply|all|forward|reuse|draft --ops <JSON 파일>
//                                                     출발 화면 하나를 열고 ops 의 바꿀 것을 아무 조합으로 한 번에 넣어 [임시저장]만
//                                                     누른다 — 안 보낸다. reply · all · forward · reuse 는 원래 메일에서 웹메일의 그 단추가
//                                                     여는 화면(reuse 는 보낸 메일의 [재사용]), draft 는 임시메일의 편집 화면이다. 못 할 까닭(넣은 글 자리가 없다 · 조각이
//                                                     한 번이 아니다 · 주소록에 없다)을 다 가린 뒤에야 화면을 건드리고, 하나라도 걸리면
//                                                     아무 칸도 안 고치고 종료 2. 임시메일의 unid · 저장한 판 · 그 열쇠를 낸다
//   ops — {subject?, body?(HTML), swaps?[[옛 글, 새 글]…], people?{to?, cc?, bcc?: [주소…]}, replace?[to|cc|bcc…], depts?{부서 주소: 부서 이름},
//          attach?[파일 경로…], detach?[첨부 이름…], groups?{to?, cc?, bcc?: [{key, name}…]},
//          options?{urgent?, no_forward?, one_by_one?: bool, send_at?: 'YYYY-MM-DD HH:MM' | ''}}
//     people 은 그 칸에 더하고 replace 에 든 칸은 먼저 비운다 · depts 에 든 주소는 조직 하나로 넣는다. body 의 자리는 출발마다 다르다(STARTS 의
//     body). swaps 는 본문 글자에서 한 번만 나오는 조각을 그 글자 자리에서만 바꾼다 — 서명 · 인용 · 서식은 그대로다.
//     attach 는 첨부 칸에 더하고(같은 이름이 칸에 있으면 멈춘다), detach 는 그 이름의 저장된 첨부(꼭 하나)를 뺀다. 임시메일 · 재사용은
//     저장된 본문의 <style> 을 지켜 저장한다. 쓰는 사람이 연 화면에서 바꾸기 시작한 뒤에 멈추면 그 말을 오류 글에 붙인다.
//     groups 는 배포그룹을 그룹째(열쇠 하나) 그 칸에 더한다 — 고름 창의 [배포그룹] 탭과 같은 토큰이다. options 는 메일속성 체크 칸을
//     준 것만 켜고 끈다(send_at 빈 글자는 예약을 푼다) — 저장은 화면의 saveDoc 이 그 체크에서 칸을 싣는다
//   node draft_send.js show <unid>                    임시메일 하나를 쓰는 사람의 Edge 에 편집 화면으로 띄워 둔다 — 사람이 거기서
//                                                     [보내기]를 누른다. 열린 화면이 있으면 그 탭을 앞으로 올리기만 한다
//   환경변수 EDGE_DEBUG_PORT(기본 9222) · MAIL_SERVER(필수 · http://<메일 서버>) · MAILBOX_DB(필수 · 02/mail2/<번호>.nsf 꼴) —
//   뒤의 둘은 부르는 쪽(mail.py)이 메일함 주소에서 뽑아 준다. require 로 실으면 아무것도 안 돌고 본문 짓는 함수(rebody)와 출발 표(STARTS)만
//   내준다 — 출발 표의 이름은 mail.py 의 DRAFT_STARTS 가운데 편집 화면에서 짓는 것(ON_SCREEN)과 같아야 한다. Edge 에 붙는 줄과 Edge 의 답 하나의 시한은 형제 스킬 ep-login 의
//   scripts/edge_cdp.js 를 싣는다 — 멈춘 탭은 그 시한에 종료 1 이다
//
// 어느 화면에서 보내나
//   그 메일이 쓰는 사람의 탭에 이미 편집으로 열려 있으면 **그 화면**에서 한다 — 사람이 거기서 고친 것까지 나간다. 없으면 최소화한
//   새 창에 열고 끝나면 그 창만 닫는다.
//   ⚠ 열린 화면을 두고 따로 열어 저장하면 열린 화면의 다음 저장이 새 임시메일로 갈라진다(저장 번호가 어긋난다) — 따로 열지 않는다.
//
// 무엇을 내나
//   표준 출력에 JSON 한 줄 — inspect {where, state, token} · send {pressed, where, asked, …} · edit {unid, start, where, asked, state, token} ·
//   show {unid, where}. 실패는 {error, …}. send 의 0 은 「발송 확인에 예 하고 저장 답이
//   왔다」까지다 — 나갔나는 부르는 쪽이 보낸편지함 · 임시보관함으로 가린다. 종료 값 0 됐다 · 1 도구 · 화면 오류 · 2 그 메일을 못
//   찾았다 · 3 Edge 에 못 붙었다(스킬 ep-login) · 4 열쇠가 지금 판과 다르다(안 보냈다) · 5 웹메일이 다른 물음을 띄웠다(안 보냈다).
//   웹메일 화면의 흐름과 물음의 꼴은 SOURCES.md 「draft_send.js」 가 든다.
'use strict';
const crypto = require('crypto');
const { sleep, waitFor, framesOf, edgeLine } = require('../../ep-login/scripts/edge_cdp.js');

const SERVER = (process.env.MAIL_SERVER || '').trim().replace(/\/+$/, '');
// 앞의 / 는 붙여도 떼도 된다 — Git Bash 가 /로 시작하는 값을 윈도 경로로 바꿔 넘기므로 부르는 쪽은 떼고 준다
const DB = '/' + (process.env.MAILBOX_DB || '').trim().replace(/^\/+/, '');
const READY_SECONDS = 60;          // 편집 화면이 다 서기를 기다리는 시한 — 편집기 · 첨부 칸이 늦게 선다
const SEND_SECONDS = 120;          // 보내기를 누른 뒤 저장 답을 기다리는 시한 — 첨부 확인이 든다
const TOKEN_LENGTH = 12;
// 웹메일이 보내기 전에 묻는 확인 — 이 꼴만 「예」 한다. 앞에 「첨부 없음」 안내 줄이 붙을 수 있다. 다른 물음은 다 「아니오」 하고 멈춘다
const SEND_CONFIRM = /^(첨부 문서가 없는 메일 입니다\.\s*)?메일을 발송 하시겠습니까\?\s*$/;
// 임시저장이 끝나면 화면이 묻는 것 — 「아니오」 하면 창이 닫힌다. 저장 전에 뜬 다른 물음은 다 「아니오」 하고 멈춘다
const SAVED_ASK = /^임시저장이 완료되었습니다/;
// 넣은 글을 감싼 div 의 id 머리 — 임시메일을 다시 고칠 때 이 자리만 갈아 끼운다. 새 메일을 저장하는 쪽(mail.py)이 이 줄을 읽어
// 같은 표지를 단다 — ⚠ 줄의 꼴(const TEXT_MARK = '…')을 바꾸면 mail.py 의 TEXT_MARK_IN_HAND 도 함께 바꾼다
const TEXT_MARK = 'cm-text-';
const PEOPLE_FIELDS = {to: 'send_to', cc: 'copy_to', bcc: 'bcopy_to'};   // ops 의 받는 사람 칸 → 편집 화면의 받는 사람 칸 id
const SAVE_SECONDS = 60;           // [임시저장] 뒤 저장 답을 기다리는 시한 — 전달의 첨부를 다시 싣는 데 든다
const BODY_SECONDS = 10;           // 편집기가 넣은 글을 그리기를 기다리는 시한 — setBodyValue 는 늦게 든다
const LOOKUP_MS = 20000;           // 주소록 한 번의 시한 — 답이 없어도 이 손이 제 창을 닫고 끝나게
// 주소록에 묻는 식 하나의 답을 기다리는 시한 — 화면의 주소록 시한(LOOKUP_MS)보다 길어야 「주소록이 답하지 않았다」가 제 까닭으로 온다
const LOOKUP_SECONDS = LOOKUP_MS / 1000 + 10;
// ⚠ 값이나 뜻을 바꾸면 mail.py 의 HAND_EXITS(이 명령의 종료 값으로 옮기기)와 HAND_UNPRESSED([보내기]를 누르기 전에만 내는 값 —
// 그 밖의 값으로 멈춘 send 는 나갔을 수 있다고 본다)도 함께 고친다
const EXIT = {OK: 0, FAIL: 1, MISSING: 2, NO_EDGE: 3, STALE: 4, ASKED: 5};

const fail = (code, message, extra = {}) => { const e = new Error(message); e.code = code; e.extra = extra; return e; };

// ── Edge 에 붙기 ───────────────────────────────────────────────────────────

// Edge 의 답 하나의 시한은 줄의 것(edge_cdp.js)을 쓴다. 화면의 긴 일이 끝나야 답하는 부름 — 화면 열기(Page.navigate) · 주소록 묻기 ·
// [보내기] · [임시저장]을 누르는 식 — 만 이 손이 그 일에 둔 시한(READY_SECONDS · LOOKUP_SECONDS · SEND_SECONDS · SAVE_SECONDS)을 준다
const { devtools, connect } = edgeLine({fail: EXIT.FAIL, noEdge: EXIT.NO_EDGE});

// 이 메일의 편집 화면 주소인가 — 쓰는 사람 탭의 안쪽 프레임이든 새 창이든 /0/<unid>?EditDocument 꼴이다
const isEditor = (url, unid) => url.toUpperCase().includes(`/0/${unid}`) && /\?editdocument/i.test(url);

// ── 편집 화면 찾기 · 열기 ─────────────────────────────────────────────────────

// 쓰는 사람의 탭 가운데 이 메일의 편집 화면을 든 것 — {target, frameId} 또는 null
async function findOpenEditor(cdp, unid) {
  const pages = (await devtools('/json/list')).filter(t => t.type === 'page' && t.url.startsWith(SERVER));
  for (const t of pages) {
    const {sessionId} = await cdp.send('Target.attachToTarget', {targetId: t.id, flatten: true});
    const {frameTree} = await cdp.send('Page.getFrameTree', {}, sessionId);
    const f = framesOf(frameTree).find(x => isEditor(x.url, unid));
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
  await cdp.send('Page.navigate', {url}, sessionId, READY_SECONDS);   // 서버가 화면을 내기 시작해야 답이 온다
  const {frameTree} = await cdp.send('Page.getFrameTree', {}, sessionId);
  return {targetId, sessionId, frameId: frameTree.frame.id, opened: true};
}

// 그 프레임에서 식 하나 — 프레임마다 실행 자리가 따로라 자리를 받아 둔다. ``limit`` 은 그 식의 답을 기다리는 시한(초) — 안 주면 줄의 것
async function evaluator(cdp, ed) {
  const contexts = {};
  cdp.on(m => {
    if (m.sessionId === ed.sessionId && m.method === 'Runtime.executionContextCreated' && m.params.context.auxData?.isDefault)
      contexts[m.params.context.auxData.frameId] = m.params.context.id;
  });
  await cdp.send('Runtime.enable', {}, ed.sessionId);
  return async (expression, limit) => {
    for (let i = 0; i < 20 && !contexts[ed.frameId]; i++) await sleep(250);
    const r = await cdp.send('Runtime.evaluate', {expression, contextId: contexts[ed.frameId], returnByValue: true, awaitPromise: true}, ed.sessionId, limit);
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
// 임시메일 자신을 가리켜, 빼지 않으면 답장 저장(edit)이 낸 열쇠가 사람이 본 것과 같은 판에서도 늘 어긋난다
const IN_DOC = /(\.nsf\/0\/)[0-9a-f]{32}(?=\/)/gi;
const tokenOf = s => crypto.createHash('sha256')
  .update(JSON.stringify([s.subject, s.to, s.cc, s.bcc, s.files, s.body.replace(IN_DOC, '$1-')])).digest('hex').slice(0, TOKEN_LENGTH);

// ── 보내기 ─────────────────────────────────────────────────────────────────

// [보내기]를 누르고 발송 확인만 「예」 한다 — 그 **앞에** 뜬 다른 물음은 「아니오」 하고 멈춘다(안 나간다). 확인 뒤에 뜬 것은
// 「예」 하고 글만 든다 — 이미 나갔을 수 있어 「안 보냈다」고 하지 않는다. 저장 답이 오면 물음들의 글을 낸다
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
  await ev("_form.clickMailSend(); 'pressed'", SEND_SECONDS);
  const done = await waitFor(SEND_SECONDS, () => {
    if (asked.some(a => !a.accepted)) throw fail(EXIT.ASKED, '웹메일이 발송 확인 앞에 다른 물음을 띄워 「아니오」 했다 — 안 보냈다',
                                                  {asked: asked.map(a => a.message)});
    return saved;
  });
  if (done) return asked.map(a => a.message);
  throw fail(EXIT.FAIL, `보내기를 누르고 ${SEND_SECONDS} 초 안에 저장 답이 안 왔다 — 보낸편지함 · 임시보관함을 보고 확인한다`,
             {asked: asked.map(a => a.message)});
}


// ── 임시저장 — 출발 화면 하나 × 바꿀 것 아무 조합 ─────────────────────────────────

// [답장] · [전체답장] · [전달] · [재사용]을 누른 것과 같은 화면을 최소화한 새 창에 연다 — process_doc 이 새 문서를 짓고 편집 화면으로 넘긴다.
// ⚠ 편집 화면 주소(?EditDocument&type=Reply)를 바로 열면 머리 · 인용 · 원래 메일과의 이음이 빠진다 — 늘 process_doc 으로 연다
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

// 받는 사람 칸들에 사내 주소록의 사람 · 부서를 넣는 식 — ``pairs`` 는 [칸 id, 주소] 들, ``clear`` 는 넣기 전에 비울 칸 id 들,
// ``depts`` 는 부서 주소 → 부서 이름(조직 하나로 넣는다). 한 주소라도 꼭 하나로 안 맞으면 아무 칸도 안 건드리고 「주소 — 까닭」,
// 다 넣었으면 빈 글자를 낸다 — 쓰는 사람이 연 화면에 반쯤 고친 판을 안 남긴다. 부서는 주소록이 이름으로만 찾아 주어 이름으로 찾고
// 주소가 같은 하나를 고른다
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

// 본문의 새 판을 짓는다 — 편집기는 안 건드린다. 화면 안에서도 검사에서도 같은 함수가 돌아(문자열로 실어 보낸다) 바깥 이름을 안 쓴다.
// ``html`` 은 편집기의 본문 HTML(getHTML), ``spec`` 은 {place, piece, mark, prefix, swaps}. 지으면 {html: body 안, text: 보이는 글자},
// 못 지으면 {why} 다. 조각 바꾸기가 먼저고 넣을 글이 그 뒤다 — 조각은 원래 본문을 가리키는 말이다.
// - body 태그 없는 조각이면 맨 앞의 <style> 을 파서가 head 로 옮긴다 — 본문의 서식이라 새 판 앞에 되돌려 싣는다
// - swaps: 조각은 보이는 글자(style · script 밖)에서 공백을 너그럽게 맞춰 **꼭 한 번** 나와야 하고, 한 글자 마디 안에 들어야 한다 —
//   마디 안의 글자만 바꾸니 태그 · 서식 · 그림은 그대로다. 마디를 걸친 조각(굵게 · 링크 경계)은 고르지 않고 멈춘다
// - place top: 넣을 글을 표지 div 로 감싸 본문 맨 앞(서명 · 인용 앞)에 세운다
// - place mark: 넣은 글의 자리를 간다 — 본문의 첫 표지이고 **그 앞에 다른 글이 없을 때만** 그것이다. 표지는 인용한 옛 메일에도 들 수
//   있어(이 손으로 보낸 메일에 웹메일에서 직접 쓴 답장) 앞에 글이 있는 표지를 고르면 인용을 갈아 끼운다
function rebody(html, spec) {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  // 맨 앞 서식 되살리기 — body 태그 없는 조각이면 파서가 head 로 옮긴 <style> 을 새 판 앞에 되돌려 싣는다
  const hoisted = /<body[\s>]/i.test(html) ? '' : Array.from(doc.head.querySelectorAll('style'), s => s.outerHTML).join('');
  // 보이는 글자 마디들 — style · script · title 안은 본문 글자가 아니다
  const shown = () => {
    const out = [], walk = doc.createTreeWalker(doc.body, 4 /* NodeFilter.SHOW_TEXT */);
    for (let n = walk.nextNode(); n; n = walk.nextNode()) if (!/^(STYLE|SCRIPT|TITLE)$/.test(n.parentNode.nodeName)) out.push(n);
    return out;
  };
  // 조각 하나를 바꾼다 — 못 바꾸면 그 까닭, 바꿨으면 null
  const swap = (from, to) => {
    const words = String(from).trim().split(/\s+/).filter(Boolean);
    if (!words.length) return '바꿀 조각이 비었다';
    const pattern = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('\\s+');
    const nodes = shown();
    const hits = (nodes.map(n => n.data).join('').match(new RegExp(pattern, 'g')) || []).length;
    if (!hits) return `「${from}」 이 본문 글자에 없다 — 화면에 보이는 글자 그대로, 한 문단 안의 조각을 준다`;
    if (hits > 1) return `「${from}」 이 본문 글자에 ${hits} 번 나온다 — 앞뒤 글을 더 붙여 한 번만 나오는 조각을 준다`;
    const one = new RegExp(pattern);
    const node = nodes.find(n => one.test(n.data));
    if (!node) return `「${from}」 이 서식 경계(굵게 · 색 · 링크)를 걸쳐 있다 — 경계 안의 더 짧은 조각을 준다`;
    const m = node.data.match(one);
    node.data = node.data.slice(0, m.index) + String(to) + node.data.slice(m.index + m[0].length);
    return null;
  };
  // 넣을 글을 세운다 — top 은 표지 div 로 감싸 본문 맨 앞에, mark 는 앞에 다른 글이 없는 첫 표지 자리에. 못 세우면 그 까닭, 세웠으면 null
  const put = () => {
    if (spec.place === 'top') {
      const box = doc.createElement('div');
      box.id = spec.mark;
      box.innerHTML = spec.piece;
      doc.body.insertBefore(box, doc.body.firstChild);
      return null;
    }
    const el = doc.querySelector(`[id^="${spec.prefix}"]`);
    const before = doc.createRange();
    if (el) { before.setStart(doc.body, 0); before.setEndBefore(el); }
    if (!el || before.toString().trim()) return '본문 맨 앞에 넣은 글의 표지가 없다 — 글을 통째로 못 간다(통째로 갈면 서명 · 인용이 날아간다). 바꿀 데만 조각으로 준다';
    el.id = spec.mark;
    el.innerHTML = spec.piece;
    return null;
  };
  // 글자 뽑기 — 보이는 글자를 빈칸 하나로 펴서
  const text = () => shown().map(n => n.data).join('').replace(/[\s​﻿]+/g, ' ').trim();
  for (const [from, to] of spec.swaps || []) {
    const why = swap(from, to);
    if (why) return {why};
  }
  const why = spec.piece != null ? put() : null;
  if (why) return {why};
  return {html: hoisted + doc.body.innerHTML, text: text()};
}
const BODY_NOW = "(_PWEC.getHTML() || '')";

// 지은 본문(rebody 의 답)을 편집기에 넣는다 — 편집기가 늦게 그려서 다 섰나를 본 뒤에 돌아온다. ``mark`` 가 있으면 그 표지가 서기를, 없으면
// 판이 바뀌기를 기다린다 — 글자를 맞추면 편집기가 엔티티를 다시 쓴 판 · 그림만 든 글을 못 가린다. ``check`` 면 선 판의 보이는 글자가 지은
// 판과 같은지까지 본다 — 조각이 엉뚱한 자리에 선 판은 저장하지 않는다
async function putBody(ev, built, mark, check) {
  const before = await ev('_PWEC.getHTML()');
  await ev(`_PWEC.setBodyValue(${JSON.stringify(built.html)}); 1`);
  const drawn = h => (mark ? h.includes(mark) : h !== before);
  if (!(await waitFor(BODY_SECONDS, async () => drawn(await ev('_PWEC.getHTML()'))))) {
    throw fail(EXIT.FAIL, `편집기에 고친 본문이 ${BODY_SECONDS} 초 안에 안 섰다 — 저장하지 않았다`);
  }
  if (check && (await ev(`(${rebody})(${BODY_NOW}, {}).text`)) !== built.text) {
    throw fail(EXIT.FAIL, '편집기에 선 본문의 글자가 지은 판과 다르다 — 저장하지 않았다. 띄운 편집 화면에서 본다');
  }
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
  await ev("_form.saveDoc(); 'pressed'", SAVE_SECONDS);
  const done = await waitFor(SAVE_SECONDS, () => {
    if (saved) return true;
    if (asked.length) throw fail(EXIT.ASKED, '웹메일이 임시저장 앞에 다른 물음을 띄워 「아니오」 했다 — 저장하지 않았다', {asked});
    return false;
  });
  if (done) return asked;
  throw fail(EXIT.FAIL, `[임시저장]을 누르고 ${SAVE_SECONDS} 초 안에 저장됐다는 말이 안 왔다 — 임시보관함을 보고 확인한다`, {asked});
}

// ── 메일의 서식(<style>) 지키기 · 첨부 칸 ───────────────────────────────────────

// ⚠ 편집기는 메일을 열 때 메일의 <style> 을 버리고(head · body 어디에 있든) 제 서식만 들며, setBodyValue 로 넣은 <style> 도 버린다 —
// 그대로 [임시저장]하면 아무것도 안 고쳐도 표 · 글의 서식이 사라진다. 편집기 문서의 head 에 바로 단 <style> 은 저장에 실린다.
// 그래서 저장 전에 지킬 서식을 head 에 되단다. 편집기 제 서식은 data-destyle 이 달려 있어 고르지 않는다
const STORED_STYLES = unid => `fetch(${JSON.stringify(`${DB}/0/${unid}/Body?OpenField`)}, {credentials: 'same-origin', cache: 'no-store'})
  .then(function(r){ if (!r.ok) throw new Error('저장된 본문 ' + r.status); return r.text(); })
  .then(function(t){ return Array.from(new DOMParser().parseFromString(t, 'text/html').querySelectorAll('style:not([data-destyle])'), function(s){ return s.textContent; }); })`;
const stylesOf = html => (String(html).match(/<style\b[^>]*>[\s\S]*?<\/style>/gi) || []).map(s => s.replace(/^<style\b[^>]*>|<\/style>$/gi, ''));
const KEEP_STYLES = css => `(function(){ var d = DEXT5.getDext5DocumentDom(), css = ${JSON.stringify(css)};
  var have = Array.from(d.querySelectorAll('style'), function(s){ return s.textContent; }), n = 0;
  css.forEach(function(t){ if (t.trim() && have.indexOf(t) < 0) { var s = d.createElement('style'); s.textContent = t; d.head.appendChild(s); have.push(t); n++; } });
  return n; })()`;

// 편집 화면의 첨부 칸(KAM 프레임 · 웹메일의 XAM)에 있는 파일들 — {name, status}. status 는 complete(저장된 것) · ready(올릴 것) · remove(뺄 것)
// 배포그룹을 그 칸에 그룹째 더하는 식 — ``groups`` 는 [칸 id, {key, name}] 들. 고름 창의 [배포그룹] 탭이 짓는 토큰과 같은 꼴이다
// (org_mail.js — {type:'group', key, group_name}). 저장은 화면이 그 토큰에서 SendTo(열쇠) · 받는 사람 정보 칸을 짓는다
const ADD_GROUPS = groups => `(function(){
  var groups = ${JSON.stringify(groups)};
  groups.forEach(function(g){
    var tok = {type: 'group', key: g[1].key, group_name: g[1].name};
    window.duplicate_list[tok.key] = tok;
    $('#' + g[0]).tokenInput('add', tok);
  });
  _form.setRecipients(true);
  return 1;
})()`;

// 메일속성 체크 칸 — ops.options 의 칸 → 쓰기 화면의 체크 id. 전달불가는 화면이 DRM 복호화 발송과 함께 못 고르게 막는다(duplicate_chk)
const OPTION_BOXES = {urgent: 'important_check', no_forward: 'notforward', one_by_one: 'OnePost'};
// 준 메일속성만 바꾸는 식 — 체크를 바꾸고, 화면이 그 체크에 단 처리(전달불가 onclick 의 duplicate_chk · 예약 onchange 의
// drawTimeList)를 부른다. 긴급 · 한명씩 체크에는 화면이 단 처리가 없다 — saveDoc 이 체크를 그 자리에서 읽는다. 못 할 까닭은
// CHECK_OPTIONS 가 먼저 가려, 여기의 까닭 글은 화면이 그 사이 달라진 때만 선다
const SET_OPTIONS = options => `(function(){
  var o = ${JSON.stringify(options)}, boxes = ${JSON.stringify(OPTION_BOXES)};
  for (var k in boxes) if (k in o) {
    var el = document.getElementById(boxes[k]);
    if (!el) return '메일속성 칸 ' + boxes[k] + ' 이 화면에 없다';
    el.checked = !!o[k];
    if (o[k] && k === 'no_forward' && typeof _form.duplicate_chk === 'function') _form.duplicate_chk(el);
    if (!!o[k] !== el.checked) return '웹메일이 전달불가를 막았다(DRM 복호화 발송과 함께 못 고른다)';
  }
  if ('send_at' in o) {
    var box = document.getElementById('chbox_reservation');
    if (!box) return '예약발송 칸이 화면에 없다';
    box.checked = !!o.send_at;
    _form.drawTimeList();
    if (o.send_at) {
      var d = o.send_at.split(' ')[0], hm = o.send_at.split(' ')[1].split(':');
      $('[name=SDay]').val(d); $('#shour').val(hm[0]); $('#smin').val(hm[1]);
      if ($('#shour').val() !== hm[0] || $('#smin').val() !== hm[1]) return '예약 시각 ' + o.send_at + ' 이 화면의 시 · 분 고름에 없다';
    } else { $('[name=SDay]').val(''); }
  }
  return '';
})()`;

// 메일속성을 못 바꿀 까닭 — 화면을 바꾸기 전에 가린다. 칸이 없다 · 전달불가와 DRM 복호화 발송을 함께 · 예약의 분이 화면의 눈금 밖
const CHECK_OPTIONS = options => `(function(){
  var o = ${JSON.stringify(options)}, boxes = ${JSON.stringify(OPTION_BOXES)};
  for (var k in boxes) if (k in o && !document.getElementById(boxes[k])) return '메일속성 칸 ' + boxes[k] + ' 이 화면에 없다';
  if (o.no_forward) {
    var kam = document.getElementById('KAM'), drm = kam && kam.contentWindow.document.getElementById('decryptiondrm');
    if ((drm && drm.checked) || $('#decryptiondrm').is(':checked')) return '전달불가는 DRM 복호화 발송과 함께 못 고른다(웹메일이 막는다)';
  }
  if ('send_at' in o && !document.getElementById('chbox_reservation')) return '예약발송 칸이 화면에 없다';
  if (o.send_at) {
    // 시 · 분 고름은 drawTimeList 가 그린다 — 시는 00~23 두 자리, 분은 00 부터 Reservation_Interval 눈금. 그리기 전에 같은 자로 잰다
    var step = typeof Reservation_Interval === 'undefined' ? NaN : parseInt(Reservation_Interval, 10);
    if (!(step > 0)) return '쓰기 화면에 예약발송 분 눈금(Reservation_Interval)이 없다 — 웹메일 화면이 바뀌었다';
    var hm = (o.send_at.split(' ')[1] || '').split(':'), h = parseInt(hm[0], 10), m = parseInt(hm[1], 10);
    if (!/^\\d\\d$/.test(hm[0]) || !/^\\d\\d$/.test(hm[1]) || h > 23 || m > 59) return '예약 시각 ' + o.send_at + ' 이 화면의 시 · 분 고름 꼴(두 자리)이 아니다';
    if (m % step) return '예약발송의 분은 ' + step + ' 분 눈금이다(웹메일 화면의 고름 상자)';
  }
  return '';
})()`;

// 편집 화면의 메일속성 — 저장한 판을 보일 때 쓴다
const OPTIONS_NOW = `JSON.stringify({urgent: $('#important_check').is(':checked'), no_forward: $('#notforward').is(':checked'),
  one_by_one: $('#OnePost').is(':checked'),
  send_at: $('#chbox_reservation').is(':checked') ? ($('[name=SDay]').val() + ' ' + $('#shour').val() + ':' + $('#smin').val()) : ''})`;

const FILES_NOW = "JSON.stringify(am_handler.xam.g.getFileList().map(function(f){ return {name: f.name, status: f.status}; }))";

// 첨부 칸에서 이름이 같은 저장된 파일 하나를 뺀다 — 웹메일의 [삭제/취소]와 같은 길(줄을 고르고 그 단추). [임시저장]에 실린다
const DETACH = name => `(function(){ var w = document.getElementById('KAM').contentWindow, $ = w.$;
  var rows = $('#file_list tr').filter(function(){ return $(this).find('.name').attr('title') === ${JSON.stringify(name)}; });
  if (rows.length !== 1) return false;
  $('#file_list tr').removeClass('click-on'); rows.addClass('click-on'); $('#btn_delete').trigger('click');
  return rows.hasClass('remove'); })()`;

// 첨부 칸의 파일 입력에 파일들을 준다 — 사람이 [추가]로 고른 것과 같다. 칸에 ready 로 서고 [임시저장]이 올린다. 그 사이 화면이 물음을
// 띄우면(같은 이름 · 막힌 확장자) 「아니오」 하고 그 글을 들고 멈춘다
async function attachFiles(cdp, ed, ev, paths) {
  const asked = [];
  // 이 귀는 붙이는 동안만 둔다 — 남기면 [임시저장] 뒤 「창을 유지하시겠습니까」에도 먼저 「아니오」 해 쓰는 사람의 화면을 닫는다
  const ear = m => {
    if (m.sessionId !== ed.sessionId || m.method !== 'Page.javascriptDialogOpening') return;
    asked.push(m.params.message);
    cdp.send('Page.handleJavaScriptDialog', {accept: false}, ed.sessionId).catch(() => {});
  };
  cdp.on(ear);
  try { await putFiles(cdp, ed, ev, paths, asked); } finally { cdp.off(ear); }
}

async function putFiles(cdp, ed, ev, paths, asked) {
  await cdp.send('Page.enable', {}, ed.sessionId);
  // 파일 입력은 값이 아니라 요소로 건네야 해 이 프레임에 따로 실행 자리를 세운다 — 문서는 같은 것을 본다
  const {executionContextId} = await cdp.send('Page.createIsolatedWorld', {frameId: ed.frameId}, ed.sessionId);
  const {result} = await cdp.send('Runtime.evaluate', {contextId: executionContextId,
    expression: "document.getElementById('KAM').contentDocument.querySelector('input[type=file]')"}, ed.sessionId);
  if (!result.objectId) throw fail(EXIT.FAIL, '편집 화면의 첨부 칸에 파일 입력이 없다 — 첨부하지 않았고 저장하지 않았다');
  await cdp.send('DOM.setFileInputFiles', {files: paths, objectId: result.objectId}, ed.sessionId);
  const names = paths.map(p => require('path').basename(p));
  const done = await waitFor(BODY_SECONDS, async () => {
    if (asked.length) throw fail(EXIT.ASKED, '첨부 칸이 물음을 띄워 「아니오」 했다 — 저장하지 않았다', {asked});
    const now = JSON.parse(await ev(FILES_NOW));
    return names.every(n => now.some(f => f.name === n && f.status === 'ready'));
  });
  if (!done) throw fail(EXIT.FAIL, `붙인 파일이 ${BODY_SECONDS} 초 안에 첨부 칸에 안 섰다 — 저장하지 않았다`);
}

// 출발 — 어느 화면에서 시작하나. 손가락 하나가 한 줄이다: open 은 그 화면을 연다 · fresh 는 화면이 새 문서를 지었나(저장하면 새
// 임시메일이 선다) · body 는 ops.body 가 설 자리(rebody 의 place) · styles 는 받은 unid 의 저장된 본문 <style> 을 지켜 저장하나 — 본문이
// 그 메일의 것인 출발만 그렇다(답장 · 전달의 원래 메일은 인용이라 그 서식을 새 메일 전체에 걸지 않는다)
const STARTS = {
  reply: {open: (cdp, unid) => openReplyEditor(cdp, unid, 'Reply'), fresh: true, body: 'top'},
  all: {open: (cdp, unid) => openReplyEditor(cdp, unid, 'AllReply'), fresh: true, body: 'top'},
  forward: {open: (cdp, unid) => openReplyEditor(cdp, unid, 'Forward'), fresh: true, body: 'top'},
  // [재사용] — 읽기 화면의 copyEdit('Resend'). 원래 본문을 서명까지 그대로 옮기고 인용 · 서명을 더 안 붙여, 넣을 글은 그 맨 앞이다.
  // 서식 지키기(styles)는 회사 화면에서 아직 안 돌려 봤다 — 그 표지는 mail.py DRAFT_STARTS 의 unmeasured 칸이 든다
  reuse: {open: (cdp, unid) => openReplyEditor(cdp, unid, 'Resend'), fresh: true, body: 'top', styles: true},
  // 쓰는 사람이 그 메일을 편집으로 열어 두었으면 그 화면에서 — 따로 열면 열린 화면의 다음 저장이 갈라진다
  draft: {open: async (cdp, unid) => (await findOpenEditor(cdp, unid)) || openEditor(cdp, unid), fresh: false, body: 'mark', styles: true},
};

// 출발 화면 하나를 열고 ops 의 바꿀 것을 넣어 [임시저장]한다 — 받는 것 · 내는 것 · 종료 값은 머리말의 edit 이다. 못 할 까닭(넣은 글
// 자리 · 조각 · 주소록)을 다 가린 뒤에야 화면을 건드린다 — 쓰는 사람이 연 화면에 저장 안 된 반쪽 판을 안 남긴다
async function editDraft(cdp, unid, rest) {
  const opt = name => { const i = rest.indexOf(name); return i < 0 ? '' : (rest[i + 1] || ''); };
  const name = opt('--start');
  const start = STARTS[name];
  if (!start) throw fail(EXIT.FAIL, `--start 는 ${Object.keys(STARTS).join(' · ')} 가운데 하나다`);
  const ops = JSON.parse(require('fs').readFileSync(opt('--ops'), 'utf8'));
  const pairs = Object.entries(PEOPLE_FIELDS).flatMap(([k, id]) => (ops.people?.[k] || []).map(a => [id, a]));
  const clear = (ops.replace || []).map(k => PEOPLE_FIELDS[k]).filter(Boolean);
  const swaps = ops.swaps || [];
  const piece = typeof ops.body === 'string' ? innerBody(ops.body) : null;
  const attach = ops.attach || [], detach = ops.detach || [];
  const groups = Object.entries(PEOPLE_FIELDS).flatMap(([k, id]) => (ops.groups?.[k] || []).map(g => [id, g]));
  const options = ops.options || {};
  const bad = Object.keys(options).filter(k => !(k in OPTION_BOXES) && k !== 'send_at');
  if (bad.length) throw fail(EXIT.FAIL, `모르는 메일속성: ${bad.join(', ')}`);
  if (!start.fresh && ops.subject == null && piece === null && !swaps.length && !pairs.length && !clear.length && !attach.length
      && !detach.length && !groups.length && !Object.keys(options).length) {
    throw fail(EXIT.FAIL, '임시메일 고치기는 바꿀 것을 하나는 받는다');
  }
  const ed = await start.open(cdp, unid);
  let touched = false;
  try {
    const ev = await evaluator(cdp, ed);
    await readState(ev).catch(e => {
      throw e.code === EXIT.FAIL && ed.opened && !start.fresh ? fail(EXIT.MISSING, `임시보관함에 이 메일이 없거나 열리지 않는다: ${unid}`) : e;
    });
    const draft = start.fresh ? await ev('_form.info.unid') : unid;
    const mark = TEXT_MARK + crypto.randomBytes(6).toString('hex');
    const built = piece !== null || swaps.length
      ? await ev(`(${rebody})(${BODY_NOW}, ${JSON.stringify({place: start.body, piece, mark, prefix: TEXT_MARK, swaps})})`) : null;
    if (built && built.why) throw fail(EXIT.MISSING, `${built.why}. 저장하지 않았다`);
    const files = JSON.parse(await ev(FILES_NOW));
    const gone = detach.filter(n => files.filter(f => f.name === n && f.status === 'complete').length !== 1);
    if (gone.length) throw fail(EXIT.MISSING, `첨부 칸에 그 이름의 저장된 파일이 꼭 하나가 아니다: ${gone.join(', ')}. 저장하지 않았다`);
    // 첨부 칸은 뺄 것으로 고른 파일과도 같은 이름을 안 받는다 — 같은 이름으로 갈려면 빼서 저장한 뒤 다시 부른다
    const clash = attach.map(p => require('path').basename(p)).filter(n => files.some(f => f.name === n));
    if (clash.length) throw fail(EXIT.MISSING, `첨부 칸에 같은 이름의 파일이 이미 있다: ${clash.join(', ')}. 저장하지 않았다 — 같은 이름으로 갈려면 detach 로 빼서 저장한 뒤 다시 붙인다`);
    const css = [...(start.styles ? await ev(STORED_STYLES(unid), READY_SECONDS) : []), ...(piece !== null ? stylesOf(piece) : [])];
    const blocked = Object.keys(options).length ? await ev(CHECK_OPTIONS(options)) : '';
    if (blocked) throw fail(EXIT.MISSING, `${blocked}. 저장하지 않았다`);
    // 여기부터 화면을 바꾼다 — 쓰는 사람이 연 화면이면 저장 전에 멈춰도 바꾼 것이 남고, 웹메일의 자동저장이 그것을 실을 수 있다
    touched = !ed.opened;
    const why = pairs.length || clear.length ? await ev(addPeople(pairs, clear, ops.depts || {}), LOOKUP_SECONDS) : '';
    if (why) { touched = false; throw fail(EXIT.MISSING, `${why}. 저장하지 않았다`); }   // addPeople 은 못 찾으면 아무 칸도 안 바꾼다
    if (groups.length) await ev(ADD_GROUPS(groups));
    const refused = Object.keys(options).length ? await ev(SET_OPTIONS(options)) : '';
    if (refused) throw fail(EXIT.FAIL, `${refused}. 저장하지 않았다`);
    if (attach.length) await attachFiles(cdp, ed, ev, attach);
    if (built) await putBody(ev, built, piece !== null ? mark : null, swaps.length > 0);
    if (css.length) await ev(KEEP_STYLES(css));
    for (const n of detach) if (!(await ev(DETACH(n)))) throw fail(EXIT.FAIL, `첨부 「${n}」 를 못 뺐다 — 저장하지 않았다`);
    if (ops.subject != null) await ev(`document.forms[0].Subject.value = ${JSON.stringify(ops.subject)}; 1`);
    const state = JSON.parse(await ev(STATE));
    const optionsNow = JSON.parse(await ev(OPTIONS_NOW));
    const asked = await pressSave(cdp, ed, ev, !ed.opened);
    return {unid: draft, start: name, where: ed.opened ? '새 창(최소화)' : '쓰는 사람이 연 화면', asked, state, options: optionsNow,
            token: tokenOf(state)};
  } catch (e) {
    if (touched) e.message += ' — 쓰는 사람이 연 편집 화면에 반쯤 고친 판이 남았다. 그 화면에서 보고 되돌리거나 저장한다';
    throw e;
  } finally {
    if (ed.opened) await cdp.send('Target.closeTarget', {targetId: ed.targetId}).catch(() => {});
    else await cdp.send('Target.detachFromTarget', {sessionId: ed.sessionId}).catch(() => {});
  }
}

// 그 메일의 편집 화면을 쓰는 사람의 Edge 에 띄워 둔다 — 열린 화면이 있으면 그 탭을 앞으로 올리고(따로 열면 열린 화면의 다음 저장이
// 갈라진다), 없으면 보이는 새 창에 연다. 이 손은 그 창을 닫지 않는다 — 사람이 확인하고 보내거나, 뒤의 edit(임시메일 고치기) · send 가 그 화면을 쓴다
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
  if (!['inspect', 'send', 'edit', 'show'].includes(verb) || !/^[0-9A-F]{32}$/.test(unid)) {
    throw fail(EXIT.FAIL, '꼴: inspect|send <unid> [--confirm 열쇠] · edit <unid> --start … --ops <JSON 파일> · show <unid>');
  }
  if (!/^\/[\w/]+\.nsf$/i.test(DB)) throw fail(EXIT.FAIL, 'MAILBOX_DB 가 메일함 경로(/…/<번호>.nsf)가 아니다');
  if (!/^https?:\/\/[^/]+$/i.test(SERVER)) throw fail(EXIT.FAIL, 'MAIL_SERVER 가 메일 서버 주소(http://<서버>)가 아니다');
  if (verb === 'edit' || verb === 'show') {
    const cdp = await connect((await devtools('/json/version')).webSocketDebuggerUrl);
    const run = {edit: editDraft, show: showDraft}[verb];
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

if (require.main === module) {
  main().then(out => { console.log(JSON.stringify(out)); process.exit(EXIT.OK); })
    .catch(e => { console.log(JSON.stringify({error: e.message, ...(e.extra || {})})); process.exit(e.code ?? EXIT.FAIL); });
} else {
  module.exports = {rebody, STARTS};
}
