// 사내 게시판의 글을 쓰는 사람의 Edge 화면에서 짓는 손 — 출발 화면 하나(새 글의 [글쓰기] 창 · 임시글의 편집 창)를 열고 준 바꿀 것을
// 아무 조합으로 한 번에 넣어 화면의 [임시저장]만 누른다. 등록은 안 한다 — 저장한 글을 편집 창으로 띄워 두고, 사람이 그 창에서 보고
// [등록]을 누른다.
//
// 부르는 꼴
//   node draft_board.js save --start new --board <게시판 id> --title <제목> --body-file <HTML 파일> [--file <경로> …]
//   node draft_board.js save --start draft --id <임시글 id> --at <그 글의 게시판 id> [--title <제목>]
//                       [--body-file <HTML 파일> | --swap-file <[[옛 조각, 새 조각]…] JSON>] [--file <경로> …] [--drop <첨부 이름> …] [--end YYYY-MM-DD]
//                                     출발마다 받는 바꿀 것은 STARTS 의 takes · 꼭 받는 것은 needs 다. 못 할 까닭(인자 · 파일 · 그 출발이 안
//                                     받는 바꿀 것)은 창을 열기 전에 다 가린다 — 하나라도 걸리면 아무 창도 안 열고 종료 2. 임시글은 쓰는
//                                     사람이 그 글을 열어 둔 창이 있으면 그 창에서 고친다(둘째 창을 안 연다)
//   node draft_board.js show <글 id> --board <게시판 id>
//                                     임시보관함의 글 하나를 편집 창으로 띄워 둔다(이미 열린 창이 있으면 앞으로 올린다)
//   환경변수 EDGE_DEBUG_PORT(기본 9222 — 형제 스킬 ep-login 의 띄우는 손이 여는 포트)
//   Edge 에 붙는 줄(디버깅 포트에 묻기 · CDP 한 줄 · 기다리기)은 형제 스킬 ep-login 의 scripts/edge_cdp.js 를 싣는다 — 포트를 읽는 자리와
//   Edge 의 답 하나에 두는 시한이 거기 있다. require 로 실으면 아무것도 안 돌고 두 표(STARTS · CHANGES)와 저장을 가리는 함수(draftProof)만 내준다
//
// 걸음마다의 화면 함수와 저장을 가리는 법은 ../references/DESIGN.md 「짓기」.
//
// 무엇을 내나 — 표준 출력에 JSON 한 줄 {id, start, board, title, files, where, reused, forked_from?}. 종료 값 0 됐다 · 1 도구 · 화면 오류 ·
// 임시글의 저장이 섰는지 못 가렸다(창은 띄워 둔다) · 2 인자 · 게시판이 거절했다(물은 글이 message 에 든다) · 3 Edge 에 못 붙었다 ·
// 게시판이 로그인을 청한다(스킬 ep-login)
'use strict';
const fs = require('fs');
const path = require('path');
const { sleep, waitFor, framesOf, edgeLine } = require('../../ep-login/scripts/edge_cdp.js');

const ROOT = 'http://swpappr.posco.net:7070/U14/U14010';
const ENTRY = 'http://swpsso.posco.net/idms/U61/jsp/redirectSMSP.jsp?redir_url='
  + encodeURIComponent(`${ROOT}/dispatcherSubmitSSO.jsp?menu=BBS_ALL`);
const BOARD_TAB = /\/U14\/U14010\/XClickController$/;
const WRITE_WINDOW = /\/U14\/U14010\/common\/pop\/windowOpenMain\.jsp/;   // 글쓰기 · 편집 창의 주소
const READY_SECONDS = 60;          // 창 · 편집기 · 첨부 틀이 다 서기를 기다리는 시한
const SAVE_SECONDS = 120;          // [임시저장] 뒤 저장 답을 기다리는 시한 — 첨부 올리기가 든다
const TEMPLATE_MS = 4000;          // 게시판을 고른 뒤 화면이 본문 틀을 다시 싣기를 기다리는 몫 — 그 전에 넣은 본문은 덮인다
const WINDOW_NAME = 'boardSkillPop';   // 이 손이 여는 창의 이름 머리 — 부를 때마다 새 이름이라 열린 창을 안 덮는다
const SAVE_CONFIRM = /^저장 하시겠습니까\?\s*$/;
const EXIT = {OK: 0, FAIL: 1, ARGS: 2, NO_EDGE: 3};
const LOOK_MS = 3000;              // [임시저장] 뒤 임시보관함 · 그 글의 모습을 다시 묻는 사이
const PROBE_MS = 5000;             // 열린 창 하나가 어느 글인가를 묻는 시한 — 저장 중 · 닫히는 창은 답을 안 한다

const trace = word => { if (process.env.DRAFT_BOARD_TRACE) process.stderr.write(`${new Date().toISOString().slice(11, 19)} ${word}\n`); };
const fail = (code, message) => { const e = new Error(message); e.code = code; return e; };
const { devtools, connect } = edgeLine({fail: EXIT.FAIL, noEdge: EXIT.NO_EDGE});

// 탭 하나에 붙어 그 탭의 프레임마다 식을 돌리는 손 — {ev(frameUrlPattern|frameName, expr), frames(), sessionId}
async function attachPage(cdp, targetId) {
  const {sessionId} = await cdp.send('Target.attachToTarget', {targetId, flatten: true});
  const contexts = {};
  const listen = m => {
    if (m.sessionId !== sessionId) return;
    if (m.method === 'Runtime.executionContextCreated' && m.params.context.auxData?.isDefault)
      contexts[m.params.context.auxData.frameId] = m.params.context.id;
    if (m.method === 'Runtime.executionContextDestroyed')
      for (const k of Object.keys(contexts)) if (contexts[k] === m.params.executionContextId) delete contexts[k];
  };
  cdp.on(listen);
  await cdp.send('Runtime.enable', {}, sessionId);
  await cdp.send('Page.enable', {}, sessionId);
  const frames = async () => framesOf((await cdp.send('Page.getFrameTree', {}, sessionId)).frameTree);
  const ev = async (pick, expression) => {
    const all = await frames();
    const f = all.find(x => (pick instanceof RegExp ? pick.test(x.url) : x.name === pick));
    if (!f || !contexts[f.id]) return undefined;
    const r = await cdp.send('Runtime.evaluate', {expression, contextId: contexts[f.id], returnByValue: true, awaitPromise: true}, sessionId);
    if (r.exceptionDetails) throw fail(EXIT.FAIL, `화면에서 식이 깨졌다: ${r.exceptionDetails.exception?.description || r.exceptionDetails.text}`);
    return r.result.value;
  };
  return {sessionId, ev, frames, detach: () => { cdp.off(listen); return cdp.send('Target.detachFromTarget', {sessionId}).catch(() => {}); }};
}

const pages = async () => (await devtools('/json/list')).filter(t => t.type === 'page');

// 게시판 화면 탭 — 있으면 그것, 없으면 입구를 새 탭으로 열어 선 뒤의 것
async function boardTab(cdp) {
  const seen = async () => {
    for (const t of (await pages()).filter(t => BOARD_TAB.test(t.url))) {
      const page = await attachPage(cdp, t.id).catch(() => null);   // 멈춘 탭은 건너뛰고 다음 탭 · 새 탭으로 간다
      if (!page) continue;
      const ok = await waitFor(5, () => page.ev('_tabIfr0', "typeof writeArticle === 'function'").catch(() => false));
      if (ok) return {page, targetId: t.id};
      await page.detach();
    }
    return null;
  };
  const open = await seen();
  if (open) return open;
  await cdp.send('Target.createTarget', {url: ENTRY});
  const got = await waitFor(READY_SECONDS, seen);
  if (!got) {
    const login = (await pages()).some(t => /gate\/login\.jsp|sso\.posco\.net/.test(t.url));
    throw fail(login ? EXIT.NO_EDGE : EXIT.FAIL, login ? '게시판이 로그인을 청한다 — 스킬 ep-login 으로 사내 세션을 세운다'
      : `게시판 화면이 ${READY_SECONDS} 초 안에 안 섰다`);
  }
  return got;
}

// 게시판 탭에서 창 하나를 띄우고(open 식) 그 창의 탭을 낸다
async function popup(cdp, board, openExpr) {
  const before = new Set((await pages()).map(t => t.id));
  await board.page.ev('_tabIfr0', openExpr);
  const t = await waitFor(20, async () => (await pages()).find(x => !before.has(x.id) && WRITE_WINDOW.test(x.url)));
  if (!t) throw fail(EXIT.FAIL, '글쓰기 창이 안 떴다 — 팝업이 막혔는지 본다');
  const page = await attachPage(cdp, t.id);
  return {page, targetId: t.id};
}

const FORM = /\/XClickController$/;     // 글쓰기 창 안에서 폼(form2)을 든 프레임 — 이름이 매번 다르다
const READY = "typeof articleSave === 'function' && !!document.form2 && !!document.getElementById('editor1')"
  + " && typeof document.getElementById('editor1').contentWindow.setContent === 'function'"
  + " && !!document.getElementById('articleFile') && !!document.getElementById('articleFile').contentWindow._fileQueue";

async function ready(win) {
  const ok = await waitFor(READY_SECONDS, async () => {
    for (const f of (await win.page.frames()).filter(x => FORM.test(x.url))) {
      if (await win.page.ev(new RegExp(`^${f.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`), READY).catch(() => false)) return true;
    }
    return false;
  });
  if (!ok) throw fail(EXIT.FAIL, `글쓰기 창이 ${READY_SECONDS} 초 안에 다 서지 않았다`);
}

// 임시보관함 목록을 화면과 같은 출처에서 묻는 식 — 답의 HTML 이 ``x.responseText`` 에 든다
const TEMP_LIST = `const x = new XMLHttpRequest(); x.open('POST', _webapp + '/XClickController', false);
  x.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
  x.send(jQuery.param({facade:'BBSArticleFacade', command:'listTempArticle', nextpage:'/bbs/articleTempList.jsp', categoryId:'BBS_ALL', menuGbn:'TEMP', paging_listcnt:'50'}));`;

// 임시보관함에 그 제목으로 선 글의 id 들(저장이 섰나 · 새 글이 무엇인가를 함께 가린다)
const DRAFT_IDS = title => `(()=>{ ${TEMP_LIST}
  const ids = []; const re = /name="chkid" value='([^']+)'/g; let m;
  const box = document.createElement('textarea');
  while ((m = re.exec(x.responseText))) { box.innerHTML = m[1]; const k = JSON.parse(box.value); box.innerHTML = k.title || ''; if (box.value === ${JSON.stringify(title)}) ids.push(k.articleId); }
  return ids; })()`;

// 임시보관함의 줄마다 {id, title, text} — id · 제목은 DRAFT_IDS 와 같은 칸(chkid 의 JSON)에서, text 는 그 칸이 든 줄의 보이는 글자(날짜 ·
// 상태가 든다)다. 임시글 고치기의 저장을 가리는 데(draftProof) 쓴다
const DRAFT_ROWS = `(()=>{ ${TEMP_LIST}
  const doc = new DOMParser().parseFromString(x.responseText, 'text/html'); const box = document.createElement('textarea');
  return Array.from(doc.querySelectorAll('input[name="chkid"]'), el => { const k = JSON.parse(el.value); box.innerHTML = k.title || '';
    const tr = el.closest('tr'); return {id: k.articleId, title: box.value, text: (tr ? tr.textContent : '').replace(/\\s+/g, ' ').trim()}; }); })()`;

// 임시글 고치기의 저장이 섰나 — 누르기 앞 · 뒤의 모습 둘(``before`` · ``after`` = {rows: 임시보관함 줄, state: 그 글의 모습})과 요청(``want``)으로
// 가린다. 임시보관함 줄의 날짜는 하루 단위라 그것만으로는 제목을 안 바꾼 저장이 늘 「못 가렸다」였다(회사 PC 2026-11-18). 그래서 그 글의 모습
// (draftState — 제목 · 게시 시각(분) · 게시기한 · 본문 글자 · 첨부 이름)을 함께 본다.
// - 앞에 없던 다른 줄이 요청한 제목으로 서면 'forked'(새 임시글로 갈라졌다 · 옛 글은 남는다)
// - 그 글의 모습이 앞과 다르고 요청한 것이 다 들었으면 'saved'
// - 모습은 바뀌었는데 요청한 것이 안 들었으면 'unproven' 과 그 까닭(why)
// - 그 밖(아무것도 안 바뀜 · 모습을 못 읽음 · 앞 목록에 그 글이 없었음)은 'unproven'
// ``want`` = {title, files: 더한 이름, drop: 뺀 이름, end: 게시종료일, body: 글 일부를 바꾼 판의 보이는 글자(빈칸은 안 본다)}
function draftProof(before, after, id, want) {
  const title = want.title;
  const fork = after.rows.find(r => r.id !== id && r.title === title && !before.rows.some(b => b.id === r.id));
  if (fork) return {verdict: 'forked', id: fork.id};
  const was = before.state, now = after.state;
  if (!before.rows.some(r => r.id === id) || !was || !now) return {verdict: 'unproven'};
  if (JSON.stringify(was) === JSON.stringify(now)) return {verdict: 'unproven'};
  const miss = [];
  if (now.title !== title) miss.push(`제목이 「${now.title}」 이다`);
  for (const f of want.files || []) if (!now.files.includes(f)) miss.push(`첨부 ${f} 가 없다`);
  for (const f of want.drop || []) if (now.files.includes(f)) miss.push(`뺄 첨부 ${f} 가 남았다`);
  if (want.end && !now.period.includes(want.end)) miss.push(`게시기한이 「${now.period}」 이다`);
  const flat = t => String(t).replace(/[\s\u200b\ufeff]+/g, '');
  if (want.body !== undefined && flat(now.text) !== flat(want.body)) miss.push('본문 글자가 바꾼 판과 다르다');
  return miss.length ? {verdict: 'unproven', why: miss.join(' · ')} : {verdict: 'saved', id};
}

// 그 글의 모습을 게시판 탭에서 묻는 식 — 글 화면(viewArticle · 조회수를 안 올린다)과 첨부 목록. 못 읽으면 null
const DRAFT_STATE = (id, bbs) => `(()=>{ const ask = (u, d) => { const x = new XMLHttpRequest(); x.open(d ? 'POST' : 'GET', _webapp + u, false);
  if (d) x.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded'); x.send(d ? jQuery.param(d) : null); return x.responseText; };
  const v = new DOMParser().parseFromString(ask('/XClickController', {facade:'BBSArticleFacade', command:'viewArticle', nextpage:'/bbs/articleView.jsp',
    transaction_yn:'N', articleId:${JSON.stringify(id)}, articleBbsId:${JSON.stringify(bbs)}, categoryId:'BBS_ALL', popYn:'Y'}), 'text/html');
  const body = v.querySelector('[id^="contentArea_"]'); const subject = v.querySelector('.top_subject');
  if (!body || !subject) return null;
  const flat = s => (s || '').replace(/\\s+/g, ' ').trim();
  const stamp = (flat(subject.parentNode.textContent).match(/(\\d{4}-\\d\\d-\\d\\d \\d\\d:\\d\\d)\\s*\\|\\s*조회수/) || [])[1] || '';
  const cells = Array.from(v.querySelectorAll('td.vsub_title')); const per = cells.find(c => flat(c.textContent) === '게시기한');
  const files = []; const re = /_fileArr\\.push\\(\\[url\\+"\\?fileId=[^"]+","((?:[^"\\\\]|\\\\.)*)",\\d+\\]/g; let m;
  const list = ask('/common/fileattach/download.jsp?refId=' + encodeURIComponent(${JSON.stringify(id)}) + '&downYn=Y&innoFDId=innoFDId&fileTitle=');
  while ((m = re.exec(list))) files.push(JSON.parse('"' + m[1] + '"'));
  return {title: flat(subject.textContent), posted: stamp, period: per ? flat(per.nextElementSibling.textContent).replace(/^:\\s*/, '') : '',
          text: flat(body.textContent), files: files.sort()}; })()`;

// 편집기 본문에서 조각을 바꾸는 손은 형제 스킬 company-mail 의 짓는 손(draft_send.js 의 rebody)이 든다 — 메일과 같은 계약(보이는 글자에서
// 꼭 한 번 · 한 글자 마디 안)이다. require 로 실으면 그 손은 아무것도 안 돌고 함수만 내준다. 게시판 편집기의 본문은 문서 꼴
// (<html><head><style>…<body>)이라, 바꾼 body 안을 원래 문서의 body 자리에 되넣어 머리의 서식을 지킨다
const { rebody } = require('../../company-mail/scripts/draft_send.js');
// 지은 body 안(``built``)을 원래 문서(``html``)의 body 자리에 되넣는다 — body 가 없으면 지은 것 그대로
function intoBody(html, built) {
  const m = html.match(/(<body[^>]*>)[\s\S]*?(<\/body>|$)/i);
  return m ? html.slice(0, m.index) + m[1] + built + (m[2] || '') + html.slice(m.index + m[0].length) : built;
}
const BODY_NOW = "document.getElementById('editor1').contentWindow.getHtml()";   // 화면의 저장(saveArticle)이 본문을 읽는 그 함수

async function formFrameEval(win, expr) {
  for (const f of (await win.page.frames()).filter(x => FORM.test(x.url))) {
    const esc = new RegExp(`^${f.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`);
    const has = await win.page.ev(esc, '!!document.form2').catch(() => false);
    if (has) return win.page.ev(esc, expr);
  }
  throw fail(EXIT.FAIL, '글쓰기 창에서 폼을 못 찾았다');
}

// 첨부 틀의 숨은 파일 칸에 파일을 넣는다 — DOM.setFileInputFiles 가 화면의 change 사건을 그대로 낸다. 틀의 줄에 이미 선 것(임시글의
// 첨부일 수 있다)을 먼저 세고, 그 위로 준 수만큼 늘었나를 본다
async function attachFiles(cdp, win, files) {
  if (!files.length) return 0;
  const queued = () => win.page.ev(/html5uploader\/upload\.jsp/, '_fileQueue.getUploadList().length').catch(() => 0);
  const had = await queued();
  const doc = await cdp.send('DOM.getDocument', {depth: -1, pierce: true}, win.page.sessionId);
  const find = n => {
    if (n.nodeName === 'INPUT' && (n.attributes || []).join(' ').includes('fileBrowser')) return n;
    for (const c of [...(n.children || []), ...(n.contentDocument ? [n.contentDocument] : [])]) { const x = find(c); if (x) return x; }
    return null;
  };
  const input = find(doc.root);
  if (!input) throw fail(EXIT.FAIL, '첨부 틀의 파일 칸을 못 찾았다');
  await cdp.send('DOM.setFileInputFiles', {files, backendNodeId: input.backendNodeId}, win.page.sessionId);
  const want = had + files.length;
  const count = (await waitFor(10, async () => (await queued()) >= want)) ? want : await queued();   // 틀은 파일을 하나씩 줄에 세운다
  if (count !== want) throw fail(EXIT.FAIL, `첨부가 ${files.length} 개 중 ${Math.max(0, (count || 0) - had)} 개만 들었다`);
  return files.length;
}

// 물음 상자 — 「저장 하시겠습니까?」 만 예(``confirmed`` 가 선다), 나머지는 아니오 하고 그 글을 든다
function dialogs(cdp, win) {
  const asked = [], said = [];
  const box = {asked, said, confirmed: false};
  const f = m => {
    if (m.sessionId !== win.page.sessionId || m.method !== 'Page.javascriptDialogOpening') return;
    const yes = m.params.type === 'confirm' && SAVE_CONFIRM.test(m.params.message);
    if (yes) box.confirmed = true;
    if (!yes && m.params.type !== 'alert') asked.push(m.params.message);   // 알림(alert)은 받고 넘긴다 — 막음은 저장이 안 선 것으로 가린다
    if (m.params.type === 'alert') said.push(m.params.message);
    cdp.send('Page.handleJavaScriptDialog', {accept: yes || m.params.type === 'alert'}, win.page.sessionId).catch(() => {});
  };
  cdp.on(f);
  box.stop = () => cdp.off(f);
  return box;
}

// 인자 → {start, id, at, board, title, bodyFile, files}. 값 없는 칸은 undefined 로 남겨 「안 줬다」와 「빈 값을 줬다」를 가른다
function parseArgs(argv) {
  const out = {files: [], drop: [], swaps: []};
  const keys = {'--start': 'start', '--id': 'id', '--at': 'at', '--board': 'board', '--title': 'title', '--body-file': 'bodyFile',
                '--end': 'end', '--swap-file': 'swapFile'};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (keys[a]) out[keys[a]] = argv[++i] ?? '';
    else if (a === '--file') out.files.push(argv[++i] ?? '');
    else if (a === '--drop') out.drop.push(argv[++i] ?? '');
    else if (out.id === undefined) out.id = a;   // show <글 id>
  }
  return out;
}

// writeArticle 의 칸 — 곁의 write_params.json 한 벌(앱 손 xclick.py 가 같은 폼을 GET 으로 읽을 때도 그것을 쓴다)
const WRITE_PARAMS = JSON.parse(fs.readFileSync(path.join(__dirname, 'write_params.json'), 'utf8'));
const paramsOf = (kind, board, id = '') => Object.fromEntries(Object.entries(WRITE_PARAMS[kind])
  .map(([k, v]) => [k, String(v).replace('{board}', board).replace('{id}', id)]));
const newParams = board => paramsOf('new', board);   // 화면의 writeArticle 이 넘기는 칸 그대로
const editParams = (board, id) => paramsOf('draft', board, id);
// 화면 리본 [재활용](userContents.jsp 의 copyArticle)이 여는 창 — 원글 id 를 orgArticleId 로, articleId 는 비운다. 저장은 화면이 새 글로 바꾼다
const copyParams = (board, id) => paramsOf('copy', board, id);
const openExpr = params => `(()=>{ const w = openPopupWindowInCenter(_webapp + '/XClickController?' + jQuery.param(${JSON.stringify(params)}),`
  + ` ${JSON.stringify(WINDOW_NAME + Date.now())}, 850, screen.availHeight - 100, false); w.focus(); return true; })()`;   // 화면의 창 이름(wrtieArticlePop)을 쓰면 사람이 연 글쓰기 창을 덮는다

// 쓰는 사람이 이미 연 그 글의 편집 창 — 붙은 채로 {page, targetId, mine: false}, 없으면 null. 막 닫힌 창은 목록에 잠깐 남고, 저장 중 ·
// 닫히는 창은 답을 안 해 건너뛴다
async function windowOf(cdp, id) {
  for (const t of (await pages()).filter(t => WRITE_WINDOW.test(t.url))) {
    const page = await attachPage(cdp, t.id).catch(() => null);
    if (!page) continue;
    const same = await Promise.race([
      formFrameEval({page}, `document.form2.articleId.value === ${JSON.stringify(id)}`).catch(() => false),
      sleep(PROBE_MS).then(() => false)]);
    if (same) return {page, targetId: t.id, mine: false};
    await page.detach();
  }
  return null;
}

async function showDraft(cdp, board, id, boardId) {
  const open = await windowOf(cdp, id);
  if (open) {
    await open.page.detach();
    await cdp.send('Target.activateTarget', {targetId: open.targetId}).catch(() => {});
    return '쓰는 사람이 연 창';
  }
  const win = await popup(cdp, board, openExpr(editParams(boardId, id)));
  await ready(win);
  await win.page.detach();
  return '새 창';
}

const exists = p => !!p && fs.existsSync(p);

// 출발 — 어느 화면에서 시작하나. 손가락 하나가 한 줄이다: takes 는 받는 바꿀 것 · needs 는 꼭 받는 것 · check 는 그 출발의 인자를 창을 열기
// 전에 가린다 · open 은 그 화면을 연다(쓰는 사람이 연 창이면 mine 이 거짓) · verify 는 연 창이 그 글인가 · rows 는 저장 앞 · 뒤에 견줄
// 임시보관함의 모습 · proof 는 저장이 섰나({verdict, id} · 아직 모르면 null)
const STARTS = {
  new: {
    takes: ['board', 'files', 'title', 'body'], needs: ['board', 'title', 'body'],
    check: () => '',
    // 화면의 writeArticle 은 목록 칸의 카테고리를 읽어, 그 칸이 비면 「카테고리가 존재하지 않는다」 경고에 창이 멈춘다 — 값을 직접 준다
    open: async (cdp, board, a) => ({...(await popup(cdp, board, openExpr(newParams(a.board)))), mine: true}),
    verify: async () => true,
    rows: (board, title) => board.page.ev('_tabIfr0', DRAFT_IDS(title)).then(ids => (Array.isArray(ids) ? ids : null)),
    proof: (before, after) => { const id = (after || []).find(x => !before.includes(x)); return id ? {verdict: 'saved', id} : null; },
  },
  copy: {
    takes: ['files', 'title', 'end', 'body', 'swap'], needs: [],
    check: a => (!/^QF_\d+$/.test(a.id || '') ? '--id 는 원글 id(QF_ 와 숫자) 다'
      : !/^BBS\d+$/.test(a.at || '') ? '--at 은 원글의 게시판 id(BBS 와 숫자) 다' : ''),
    open: async (cdp, board, a) => ({...(await popup(cdp, board, openExpr(copyParams(a.at, a.id)))), mine: true}),
    // 재활용 창이다 — 원글을 가리키고 새 글(articleId 빈 값)이다. 아니면 원글을 고칠 수 있어 아무것도 안 넣는다
    verify: async (win, a) => (await formFrameEval(win, `(()=>{ const f = document.form2;
      return f.articleCopyYn.value === 'Y' && f.orgArticleId.value === ${JSON.stringify(a.id)} && f.articleId.value === ''; })()`)) === true,
    rows: (board, title) => board.page.ev('_tabIfr0', DRAFT_IDS(title)).then(ids => (Array.isArray(ids) ? ids : null)),
    proof: (before, after) => { const id = (after || []).find(x => !before.includes(x)); return id ? {verdict: 'saved', id} : null; },
  },
  draft: {
    // 게시판은 안 받는다 — 편집 창에는 게시판 고름이 없다(「게시판 위치」 는 글자뿐)
    takes: ['files', 'drop', 'title', 'end', 'body', 'swap'], needs: [],
    check: a => (!/^QF_\d+$/.test(a.id || '') ? '--id 는 임시글 id(QF_ 와 숫자) 다'
      : !/^BBS\d+$/.test(a.at || '') ? '--at 은 그 임시글의 게시판 id(BBS 와 숫자) 다'
      : ''),
    // 쓰는 사람이 그 글을 열어 둔 창이 있으면 그 창에서 — 같은 글의 둘째 창을 열지 않는다
    open: async (cdp, board, a) => (await windowOf(cdp, a.id)) || {...(await popup(cdp, board, openExpr(editParams(a.at, a.id)))), mine: true},
    verify: async (win, a) => (await formFrameEval(win, 'document.form2.articleId.value')) === a.id,
    // 임시보관함 줄(갈라짐을 본다)과 그 글의 모습(제목 · 게시 시각 · 게시기한 · 본문 글자 · 첨부 이름 — 저장을 가린다)
    rows: async (board, title, a) => {
      const rows = await board.page.ev('_tabIfr0', DRAFT_ROWS);
      const state = await board.page.ev('_tabIfr0', DRAFT_STATE(a.id, a.at)).catch(() => null);
      return Array.isArray(rows) ? {rows, state} : null;
    },
    proof: (before, after, a, title) => {
      const got = after ? draftProof(before, after, a.id, {title, files: a.files.map(f => path.basename(f)), drop: a.drop, end: a.end,
                                                           body: a.body}) : {verdict: 'unproven'};
      if (got.why) a.why = got.why;
      return got.verdict === 'unproven' ? null : got;
    },
  },
};

// 바꿀 것 — 받은 것만 이 차례로 한 화면에 넣는다. 게시판이 맨 앞이다(고르면 화면이 본문 틀을 다시 실어 앞서 넣은 본문을 덮는다). 첨부가
// 본문보다 앞이다(파일 칸을 찾느라 창의 DOM 을 통째로 받는데, 본문 뒤면 본문의 data URI 그림이 그 답에 실려 Edge 의 답 시한을 넘길 수 있다).
// word 는 반쯤 고친 창을 알리는 말에 드는 사람 말이다
const CHANGES = [
  {name: 'board', word: '게시판', given: a => a.board !== undefined, run: async (cdp, win, a) => {
    const picked = await formFrameEval(win, `(()=>{ const f = document.form2; jQuery('#bbsSelect').attr('FOLDERYN','N');
      jQuery.setDivisionSelect(f, 'bbsSelect', ${JSON.stringify(a.board)}, ''); return f.bbsId.value; })()`);
    if (picked !== a.board) throw fail(EXIT.ARGS, `게시판 ${a.board} 을 못 골랐다 — 쓸 수 있는 게시판인지 boards --write 로 본다`);
    await sleep(TEMPLATE_MS);
  }},
  {name: 'files', word: '첨부', given: a => a.files.length > 0, run: (cdp, win, a) => attachFiles(cdp, win, a.files)},
  // 있던 첨부 빼기 — 첨부 틀의 줄(_fileQueue)에서 이름으로 고르고 화면의 [파일삭제](deleteSelectFiles)와 같은 걸음을 밟는다: 줄을 빼고
  // _OnBeforeRemoveItem 이 그 파일 id 를 지울 목록에 모은다. 저장(saveArticle)이 그 목록을 폼의 delFileIdLists 로 실어 보낸다
  {name: 'drop', word: '첨부 빼기', given: a => a.drop.length > 0, run: async (cdp, win, a) => {
    const got = await win.page.ev(/html5uploader\/upload\.jsp/, `(()=>{ const names = ${JSON.stringify(a.drop)}; const out = {gone: [], miss: []};
      for (const n of names) { const f = _fileQueue.getFileAtName(n);
        if (!f || f.status !== 'Temp') { out.miss.push(n); continue; } }
      if (out.miss.length) return out;
      for (const n of names) { const f = _fileQueue.remove(n); if (window._OnBeforeRemoveItem) _OnBeforeRemoveItem(f);
        jQuery('.filelistTR').filter(function(){ return this.id === n; }).remove(); out.gone.push(n); }
      if (window.updateStatusBar) updateStatusBar(); return {...out, list: getDelFileList()}; })()`);
    if (!got) throw fail(EXIT.FAIL, '첨부 틀을 못 찾았다');
    if (got.miss.length) throw fail(EXIT.ARGS, `임시글에 없는 첨부다: ${got.miss.join(' · ')} — read 의 attachments 이름 그대로 준다`);
  }},
  {name: 'title', word: '제목', given: a => a.title !== undefined,
    run: (cdp, win, a) => formFrameEval(win, `(()=>{ document.form2.title.value = ${JSON.stringify(a.title)}; return true; })()`)},
  // 게시종료일 — 화면은 게시판 옵션 termModifyYn 이 Y 일 때만 날짜 고름을 켠다(N 이면 기본 기간 고정). 명령이 그 값을 미리 보고 막는다
  {name: 'end', word: '게시기한', given: a => a.end !== undefined, run: async (cdp, win, a) => {
    const got = await formFrameEval(win, `(()=>{ const f = document.form2; if (jQuery('#endDate').datepicker('isDisabled')) return 'off';
      const today = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10); if (${JSON.stringify(a.end)} <= today) return 'early'; f.endDate.value = ${JSON.stringify(a.end)}; return f.endDate.value; })()`);
    if (got === 'off') throw fail(EXIT.ARGS, '이 게시판은 게시종료일을 못 바꾼다(화면이 칸을 잠갔다)');
    if (got === 'early') throw fail(EXIT.ARGS, `게시종료일 ${a.end} 이 오늘(한국 시각)이거나 지났다`);
    if (got !== a.end) throw fail(EXIT.FAIL, '게시종료일 칸에 날짜가 안 들었다');
  }},
  {name: 'body', word: '글', given: a => a.bodyFile !== undefined,
    run: (cdp, win, a) => formFrameEval(win, `(()=>{ document.getElementById('editor1').contentWindow.setContent(${JSON.stringify(a.html)}); return true; })()`)},
  // 글 일부 바꾸기 — 편집기의 지금 본문을 읽어(getHtml — 화면의 저장이 읽는 함수) 조각만 바꾼 판을 되넣고, 선 판의 글자가 지은 판과 같은지 본다
  {name: 'swap', word: '글 일부', given: a => a.swaps.length > 0, run: async (cdp, win, a) => {
    const now = await formFrameEval(win, BODY_NOW);
    const built = await formFrameEval(win, `(${rebody})(${JSON.stringify(now)}, ${JSON.stringify({swaps: a.swaps})})`);
    if (built.why) throw fail(EXIT.ARGS, built.why);
    await formFrameEval(win, `(()=>{ document.getElementById('editor1').contentWindow.setContent(${JSON.stringify(intoBody(now, built.html))}); return true; })()`);
    const drawn = await waitFor(10, async () => {
      const again = await formFrameEval(win, `(${rebody})(${BODY_NOW}, {}).text`).catch(() => '');
      return again === built.text;
    });
    if (!drawn) throw fail(EXIT.FAIL, '편집기에 선 본문의 글자가 지은 판과 다르다 — 저장하지 않는다. 띄운 편집 창에서 본다');
    a.body = built.text;   // 저장 뒤 글 화면의 본문 글자가 이 판과 같아야 섰다(draftProof 의 body)
  }},
];

// 창을 열기 전에 가린다 — 못 할 까닭 하나를 말로, 없으면 빈 글자. 이 손은 이것이 빈 뒤에야 Edge 에 붙는다
function refusal(a) {
  if (a.swapFile !== undefined) {   // 글 일부 — [[옛 조각, 새 조각], …] 의 JSON 파일(명령이 짓는다)
    if (!exists(a.swapFile)) return `--swap-file 이 없다: ${a.swapFile}`;
    try { a.swaps = JSON.parse(fs.readFileSync(a.swapFile, 'utf8')); } catch (e) { return '--swap-file 이 JSON 이 아니다'; }
    if (!Array.isArray(a.swaps) || !a.swaps.length || a.swaps.some(x => !Array.isArray(x) || x.length !== 2 || !String(x[0]).trim()))
      return '--swap-file 은 [[옛 조각, 새 조각], …] 이다';
  }
  const start = STARTS[a.start];
  if (!start) return `--start 는 ${Object.keys(STARTS).join(' · ')} 가운데 하나다`;
  const given = CHANGES.filter(c => c.given(a)).map(c => c.name);
  const extra = given.filter(n => !start.takes.includes(n));
  if (extra.length) return `${a.start} 출발은 ${extra.join(' · ')} 를 안 받는다`;
  const missing = start.needs.filter(n => !given.includes(n));
  if (missing.length) return `${a.start} 출발은 ${missing.join(' · ')} 를 꼭 받는다`;
  if (!given.length) return `${a.start} 출발은 바꿀 것을 하나는 받는다`;
  if (a.board !== undefined && !/^BBS\d+$/.test(a.board)) return '--board 는 게시판 id(BBS 와 숫자) 다';
  if (a.title !== undefined && !a.title.trim()) return '--title 이 비었다';
  if (a.bodyFile !== undefined && !exists(a.bodyFile)) return `--body-file 이 없다: ${a.bodyFile}`;
  const gone = a.files.find(f => !exists(f));
  if (gone !== undefined) return `첨부 파일이 없다: ${gone}`;
  if (a.end !== undefined && !/^\d{4}-\d\d-\d\d$/.test(a.end)) return '--end 는 YYYY-MM-DD 다';
  if (a.drop.some(n => !n.trim())) return '--drop 이 비었다';
  if (a.bodyFile !== undefined && a.swaps.length) return '글 통째(--body-file)와 글 일부(--swap-file)는 한 부름에 같이 안 받는다';
  return start.check(a);
}

async function save(cdp, a) {
  const start = STARTS[a.start];
  if (a.title !== undefined) a.title = a.title.trim();   // 게시판은 앞뒤 빈칸을 걷어 저장한다 — 같은 글자로 찾아야 저장을 가린다
  a.files = a.files.map(f => path.resolve(f));
  if (a.bodyFile !== undefined) a.html = fs.readFileSync(a.bodyFile, 'utf8');
  const board = await boardTab(cdp);
  let win = null;
  try {
    win = await start.open(cdp, board, a);
    return await fill(cdp, a, start, board, win);
  } catch (e) {
    if (win && win.mine) {   // 이 손이 연 창은 반쯤 든 판이라 닫는다 — 저장 전이면 아무것도 안 남는다
      await win.page.detach().catch(() => {});
      await cdp.send('Target.closeTarget', {targetId: win.targetId}).catch(() => {});
    } else if (win) {
      await win.page.detach().catch(() => {});   // 쓰는 사람이 연 창은 그대로 둔다
      if (win.touched?.length) {   // 그 창에 넣은 것은 저장 안 된 채 남는다 — 사람이 그대로 [등록]하거나, 다시 부르면 첨부가 겹으로 붙는다
        const again = win.touched.includes('첨부') ? '첨부가 겹으로 붙는다' : '그 창의 저장 안 된 고침이 함께 저장된다';
        e.message += ` — 쓰는 사람이 연 편집 창에 저장 안 된 고침(${win.touched.join(' · ')})이 남았다. 다시 부르지 않는다(${again}):`
          + ' 그 창에서 사람이 보고 되돌리거나 [임시저장]하도록 이른다';
      }
    }
    throw e;
  } finally {
    await board.page.detach().catch(() => {});
  }
}

async function fill(cdp, a, start, board, win) {
  await ready(win);
  if (!(await start.verify(win, a))) {
    throw fail(EXIT.ARGS, a.start === 'copy' ? `글 ${a.id} 의 재활용 창이 안 열렸다 — 목록 줄의 id · board 를 본다`
      : `임시글 ${a.id} 의 편집 창이 안 열렸다 — drafts 로 id 를 본다`);
  }
  const title = (a.title ?? await formFrameEval(win, 'document.form2.title.value')).trim();   // 저장 뒤 임시보관함에서 찾을 제목
  const before = await start.rows(board, title, a).catch(() => null);
  if (before == null) throw fail(EXIT.FAIL, '임시보관함 목록을 못 읽었다 — 아무 칸도 안 바꿨다');
  // 여기부터 창을 바꾼다 — 쓰는 사람이 연 창이면 멈춰도 넣은 것이 남으니 무엇을 넣기 시작했나를 적는다(save 가 알린다)
  if (!win.mine) win.touched = [];
  for (const c of CHANGES) {
    if (!c.given(a)) continue;
    if (win.touched) win.touched.push(c.word);
    await c.run(cdp, win, a);
  }
  const box = dialogs(cdp, win);
  // 저장 뒤 화면이 창을 닫으려 한다 — 닫히는 창에 붙어 있으면 손이 선다. 쓰는 사람이 연 창은 그 사람의 [닫기]가 살아야 해 안 건드린다
  if (win.mine) await formFrameEval(win, "(()=>{ top.close = function(){}; window.close = function(){}; return true; })()");
  trace(`${a.start} · 첨부 ${a.files.length} · 저장을 누른다`);
  await formFrameEval(win, "(()=>{ articleSave('TEMP'); return true; })()");
  trace('저장을 눌렀다');
  const done = await waitFor(SAVE_SECONDS, async () => {
    if (box.asked.length) return {verdict: 'asked'};
    if (box.said.length && !(await formFrameEval(win, 'true').catch(() => false))) return {verdict: 'gone'};
    if (Date.now() < (a.nextLook || 0)) return null;
    a.nextLook = Date.now() + LOOK_MS;   // 저장 답 하나를 보는 데 게시판에 묻는 것이 셋이다 — 촘촘히 안 묻는다
    return start.proof(before, await start.rows(board, title, a).catch(() => null), a, title);
  });
  box.stop();
  if (done && done.verdict === 'asked') throw fail(EXIT.ARGS, `게시판이 저장을 막았다: ${box.asked.join(' / ')}`);
  const said = box.said.length ? `게시판이 띄운 글: ${box.said.join(' / ')} — ` : '';
  const saved = !!done && (done.verdict === 'saved' || done.verdict === 'forked');
  win.touched = null;   // [임시저장]을 눌러 막히지 않았다 — 섰거나, 못 가린 판은 아래 말이 창을 보라고 이른다
  if (!saved && a.start !== 'draft') {
    throw fail(EXIT.FAIL, `${said}저장이 섰는지 못 가렸다 — 다시 부르기 전에 drafts 로 임시보관함을 본다(섰으면 show 로 띄운다)`);
  }
  if (win.mine) {   // 이 손이 연 창은 닫기를 막아 두었다 — 닫고 그 글의 편집 창으로 다시 연다(새 글이면 창이 아직 「새 글」 판이다)
    await win.page.detach().catch(() => {});
    await cdp.send('Target.closeTarget', {targetId: win.targetId}).catch(() => {});
    await waitFor(10, async () => !(await pages()).some(t => t.id === win.targetId));
  } else {
    await win.page.detach().catch(() => {});
  }
  const id = saved ? done.id : a.id;
  const at = a.start === 'new' ? a.board : a.at;
  trace(`저장 ${saved ? done.verdict : '못 가림'} ${id} · 편집 창을 띄운다`);
  const where = await showDraft(cdp, board, id, at).catch(e => `못 띄웠다(${e.message}) — show ${id} --board ${at} 로 다시 띄운다`);
  if (!saved) {
    throw fail(EXIT.FAIL, `${said}[임시저장]을 눌렀는데${box.confirmed ? '(「저장 하시겠습니까?」에 예 했다)' : '(저장 물음이 안 떴다)'} 임시보관함의 그 글`
      + `${a.why ? `이 바뀌었으나 요청한 것이 안 보여(${a.why})` : '과 글 모습이 안 바뀌어'} 섰는지 못 가렸다. 다시 부르지 않는다: 띄운 편집 창(${where})에서`
      + ' 제목 · 본문 · 첨부를 보고 사람에게 확인받는다');
  }
  return {id, start: a.start, board: at, title, files: a.files.length, where, reused: !win.mine,
          ...(done.verdict === 'forked' ? {forked_from: a.id} : {})};
}

const USAGE = '꼴: save --start new --board <id> --title <제목> --body-file <파일> [--file <경로> …] · '
  + 'save --start draft --id <임시글 id> --at <게시판 id> [--title …] [--body-file … | --swap-file …] [--file …] [--drop <이름> …]'
  + ' [--end YYYY-MM-DD] · show <글 id> --board <id>';

async function main() {
  const [verb, ...rest] = process.argv.slice(2);
  const a = parseArgs(rest);
  if (!['save', 'show'].includes(verb)) throw fail(EXIT.ARGS, USAGE);
  const why = verb === 'save' ? refusal(a)
    : !/^QF_\d+$/.test(a.id || '') || !/^BBS\d+$/.test(a.board || '') ? 'show 는 <글 id(QF_…)> --board <BBS…> 를 받는다' : '';
  if (why) throw fail(EXIT.ARGS, why);
  const cdp = await connect((await devtools('/json/version')).webSocketDebuggerUrl);
  try {
    if (verb === 'save') return await save(cdp, a);
    const board = await boardTab(cdp);
    try {
      return {id: a.id, board: a.board, where: await showDraft(cdp, board, a.id, a.board)};
    } finally {
      await board.page.detach().catch(() => {});
    }
  } finally {
    cdp.close();
  }
}

if (require.main === module) {
  main().then(out => { console.log(JSON.stringify(out)); process.exit(EXIT.OK); })
    .catch(e => { console.log(JSON.stringify({error: e.message})); process.exit(Number.isInteger(e.code) ? e.code : EXIT.FAIL); });
} else {
  module.exports = {STARTS, CHANGES, refusal, draftProof};
}
