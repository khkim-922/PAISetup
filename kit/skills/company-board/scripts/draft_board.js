// 사내 게시판의 글을 쓰는 사람의 Edge 화면에서 짓는 손 — 게시판의 [글쓰기] 창을 열어 게시판 · 제목 · 본문(HTML) · 첨부를 넣고
// 화면의 [임시저장]만 누른다. 등록은 안 한다 — 저장한 글을 편집 창으로 띄워 두고, 사람이 그 창에서 보고 [등록]을 누른다.
//
// 부르는 꼴
//   node draft_board.js save --board <게시판 id> --title <제목> --body-file <HTML 파일> [--file <경로> …]
//                                     새 글을 임시보관함에 저장하고 그 글을 편집 창으로 띄워 둔다
//   node draft_board.js show <글 id> --board <게시판 id>
//                                     임시보관함의 글 하나를 편집 창으로 띄워 둔다(이미 열린 창이 있으면 앞으로 올린다)
//   환경변수 EDGE_DEBUG_PORT(기본 9222 — 형제 스킬 ep-login 의 띄우는 손이 여는 포트)
//   Edge 에 붙는 줄(디버깅 포트에 묻기 · CDP 한 줄 · 기다리기)은 형제 스킬 ep-login 의 scripts/edge_cdp.js 를 싣는다 — 포트를 읽는 자리와
//   Edge 의 답 하나에 두는 시한이 거기 있다
//
// 어떻게 짓나(2026-11-16 회사 PC 에서 잰 것)
//   게시판 탭(XClickController 화면)이 쓰는 사람의 Edge 에 있어야 한다 — 글쓰기 창은 그 탭의 writeArticle 이 연다. 없으면 이 손이
//   게시판 입구(포털의 SSO 넘김 주소)를 새 탭으로 열어 선 뒤에 쓴다. 글쓰기 창에서
//   - 게시판 — 화면의 고름 상자에 값을 넣는 함수(jQuery.setDivisionSelect)로 넣는다. 본문보다 먼저 넣는다 — 게시판을 고르면 화면이
//     게시판의 본문 틀을 다시 싣고(setBbsTemplate) 앞서 넣은 본문을 덮는다(잼)
//   - 첨부 — 첨부 틀(html5uploader)의 숨은 파일 칸에 넣는다. 임시저장이 먼저 올리고 글에 묶는다(잼). 본문보다 먼저 넣는다 — 파일
//     칸을 찾느라 창의 DOM 을 통째로 받는데, 본문 뒤면 본문의 그림(data URI)이 그 답에 실려 Edge 의 답 시한을 넘길 수 있다
//   - 본문 — 편집기(DEXT5) 틀의 setContent. 그림은 data URI 그대로 본문에 들고 저장된다(잼)
//   - [임시저장] — 화면의 articleSave('TEMP'). 「저장 하시겠습니까?」 만 「예」 하고, 다른 물음은 「아니오」 하고 그 글을 들고 멈춘다
//   저장이 섰나는 임시보관함으로 가린다 — 저장 전에 없던, 같은 제목의 글이 서면 그것이 새 글이다. 저장 뒤 창은 닫고(화면도 닫으려 한다)
//   그 글을 편집 창으로 다시 연다 — 거기서 [등록]을 누르면 그 임시 글이 게시된다.
//
// 무엇을 내나 — 표준 출력에 JSON 한 줄 {id, board, title, files, where}. 종료 값 0 됐다 · 1 도구 · 화면 오류 · 2 인자 · 게시판이
// 거절했다(물은 글이 message 에 든다) · 3 Edge 에 못 붙었다 · 게시판이 로그인을 청한다(스킬 ep-login)
'use strict';
const fs = require('fs');
const path = require('path');
const { sleep, waitFor, framesOf, edgeLine } = require('../../ep-login/scripts/edge_cdp.js');

const ROOT = 'http://swpappr.posco.net:7070/U14/U14010';
const ENTRY = 'http://swpsso.posco.net/idms/U61/jsp/redirectSMSP.jsp?redir_url='
  + encodeURIComponent(`${ROOT}/dispatcherSubmitSSO.jsp?menu=BBS_ALL`);
const BOARD_TAB = /\/U14\/U14010\/XClickController$/;   // 게시판 화면 탭의 주소
const WRITE_WINDOW = /\/U14\/U14010\/common\/pop\/windowOpenMain\.jsp/;   // 글쓰기 · 편집 창의 주소
const READY_SECONDS = 60;          // 창 · 편집기 · 첨부 틀이 다 서기를 기다리는 시한
const SAVE_SECONDS = 120;          // [임시저장] 뒤 저장 답을 기다리는 시한 — 첨부 올리기가 든다
const TEMPLATE_MS = 4000;          // 게시판을 고른 뒤 화면이 본문 틀을 다시 싣기를 기다리는 몫(잼 — 그 전에 넣은 본문은 덮인다)
const WINDOW_NAME = 'boardSkillPop';   // 이 손이 여는 창의 이름 머리 — 부를 때마다 새 이름이라 열린 창을 안 덮는다
const SAVE_CONFIRM = /^저장 하시겠습니까\?\s*$/;
const EXIT = {OK: 0, FAIL: 1, ARGS: 2, NO_EDGE: 3};
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

// 임시보관함에 그 제목으로 선 글의 id 들 — 화면과 같은 출처에서 목록을 묻는다(저장이 섰나 · 새 글이 무엇인가를 함께 가린다)
const DRAFT_IDS = title => `(()=>{ const x = new XMLHttpRequest(); x.open('POST', _webapp + '/XClickController', false);
  x.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
  x.send(jQuery.param({facade:'BBSArticleFacade', command:'listTempArticle', nextpage:'/bbs/articleTempList.jsp', categoryId:'BBS_ALL', menuGbn:'TEMP', paging_listcnt:'50'}));
  const ids = []; const re = /name="chkid" value='([^']+)'/g; let m;
  const box = document.createElement('textarea');
  while ((m = re.exec(x.responseText))) { box.innerHTML = m[1]; const k = JSON.parse(box.value); box.innerHTML = k.title || ''; if (box.value === ${JSON.stringify(title)}) ids.push(k.articleId); }
  return ids; })()`;

async function formFrameEval(win, expr) {
  for (const f of (await win.page.frames()).filter(x => FORM.test(x.url))) {
    const esc = new RegExp(`^${f.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`);
    const has = await win.page.ev(esc, '!!document.form2').catch(() => false);
    if (has) return win.page.ev(esc, expr);
  }
  throw fail(EXIT.FAIL, '글쓰기 창에서 폼을 못 찾았다');
}

// 첨부 틀의 숨은 파일 칸에 파일을 넣는다 — DOM.setFileInputFiles 가 화면의 change 사건을 그대로 낸다
async function attachFiles(cdp, win, files) {
  if (!files.length) return 0;
  const doc = await cdp.send('DOM.getDocument', {depth: -1, pierce: true}, win.page.sessionId);
  const find = n => {
    if (n.nodeName === 'INPUT' && (n.attributes || []).join(' ').includes('fileBrowser')) return n;
    for (const c of [...(n.children || []), ...(n.contentDocument ? [n.contentDocument] : [])]) { const x = find(c); if (x) return x; }
    return null;
  };
  const input = find(doc.root);
  if (!input) throw fail(EXIT.FAIL, '첨부 틀의 파일 칸을 못 찾았다');
  await cdp.send('DOM.setFileInputFiles', {files, backendNodeId: input.backendNodeId}, win.page.sessionId);
  const queued = () => win.page.ev(/html5uploader\/upload\.jsp/, '_fileQueue.getUploadList().length').catch(() => 0);
  const count = (await waitFor(10, async () => (await queued()) >= files.length)) ? files.length : await queued();   // 틀은 파일을 하나씩 줄에 세운다
  if (count !== files.length) throw fail(EXIT.FAIL, `첨부가 ${files.length} 개 중 ${count || 0} 개만 들었다`);
  return count;
}

// 물음 상자 — 「저장 하시겠습니까?」 만 예, 나머지는 아니오 하고 그 글을 든다
function dialogs(cdp, win) {
  const asked = [], said = [];
  const f = m => {
    if (m.sessionId !== win.page.sessionId || m.method !== 'Page.javascriptDialogOpening') return;
    const yes = m.params.type === 'confirm' && SAVE_CONFIRM.test(m.params.message);
    if (!yes && m.params.type !== 'alert') asked.push(m.params.message);   // 알림(alert)은 받고 넘긴다 — 막음은 저장이 안 선 것으로 가린다
    if (m.params.type === 'alert') said.push(m.params.message);
    cdp.send('Page.handleJavaScriptDialog', {accept: yes || m.params.type === 'alert'}, win.page.sessionId).catch(() => {});
  };
  cdp.on(f);
  return {asked, said, stop: () => cdp.off(f)};
}

function parseArgs(argv) {
  const out = {files: []};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--board') out.board = argv[++i];
    else if (a === '--title') out.title = argv[++i];
    else if (a === '--body-file') out.body = argv[++i];
    else if (a === '--file') out.files.push(argv[++i]);
    else if (!out.id) out.id = a;
  }
  return out;
}

const newParams = board => ({facade: 'BBSArticleFacade', command: 'writeArticle', nextpage: '/bbs/articleWrite.jsp', writeGbn: 'NEW',
  categoryId: 'BBS_ALL', bbsId: board, popYn: 'Y', isCop: 'false', copId: '', msgId: 'BBS-000105'});   // 화면의 writeArticle 이 넘기는 칸 그대로
const editParams = (board, id) => ({facade: 'BBSArticleFacade', command: 'writeArticle', nextpage: '/bbs/articleWrite.jsp', writeGbn: 'EDIT',
  categoryId: 'BBS_ALL', bbsId: board, articleId: id, orgArticleId: id, menuGbn: 'TEMP', popYn: 'Y', isCop: 'false', msgId: 'BBS-000105'});
const openExpr = params => `(()=>{ const w = openPopupWindowInCenter(_webapp + '/XClickController?' + jQuery.param(${JSON.stringify(params)}),`
  + ` ${JSON.stringify(WINDOW_NAME + Date.now())}, 850, screen.availHeight - 100, false); w.focus(); return true; })()`;   // 화면의 창 이름(wrtieArticlePop)을 쓰면 사람이 연 글쓰기 창을 덮는다

async function showDraft(cdp, board, id, boardId) {
  for (const t of (await pages()).filter(t => WRITE_WINDOW.test(t.url))) {
    const page = await attachPage(cdp, t.id).catch(() => null);   // 막 닫힌 창은 목록에 잠깐 남는다 — 못 붙으면 건너뛴다
    if (!page) continue;
    const same = await Promise.race([
      formFrameEval({page}, `document.form2.articleId.value === ${JSON.stringify(id)}`).catch(() => false),
      sleep(PROBE_MS).then(() => false)]);
    await page.detach();
    if (same) { await cdp.send('Target.activateTarget', {targetId: t.id}).catch(() => {}); return '쓰는 사람이 연 창'; }
  }
  const win = await popup(cdp, board, openExpr(editParams(boardId, id)));
  await ready(win);
  await win.page.detach();
  return '새 창';
}

async function save(cdp, args) {
  if (!/^BBS\d+$/.test(args.board || '')) throw fail(EXIT.ARGS, '--board 는 게시판 id(BBS 와 숫자) 다');
  args.title = (args.title || '').trim();   // 게시판은 앞뒤 빈칸을 걷어 저장한다 — 같은 글자로 찾아야 새 글을 가린다
  if (!args.title) throw fail(EXIT.ARGS, '--title 이 비었다');
  if (!args.body || !fs.existsSync(args.body)) throw fail(EXIT.ARGS, `--body-file 이 없다: ${args.body}`);
  const files = args.files.map(f => path.resolve(f));
  for (const f of files) if (!fs.existsSync(f)) throw fail(EXIT.ARGS, `첨부 파일이 없다: ${f}`);
  const html = fs.readFileSync(args.body, 'utf8');
  const board = await boardTab(cdp);
  const win = await popup(cdp, board, openExpr(newParams(args.board)));   // 화면의 writeArticle 은 목록 칸의 카테고리를 읽어, 그 칸이 비면 「카테고리가 존재하지 않는다」 경고에 창이 멈춘다 — 값을 직접 준다
  try {
    return await fill(cdp, args, files, html, board, win);
  } catch (e) {   // 멈춘 창은 반쯤 든 새 글이라 닫는다 — 저장 전이면 아무것도 안 남는다
    await win.page.detach().catch(() => {});
    await cdp.send('Target.closeTarget', {targetId: win.targetId}).catch(() => {});
    await board.page.detach().catch(() => {});
    throw e;
  }
}

async function fill(cdp, args, files, html, board, win) {
  await ready(win);
  const picked = await formFrameEval(win, `(()=>{ const f = document.form2; jQuery('#bbsSelect').attr('FOLDERYN','N');
    jQuery.setDivisionSelect(f, 'bbsSelect', ${JSON.stringify(args.board)}, ''); f.title.value = ${JSON.stringify(args.title)};
    return f.bbsId.value; })()`);
  if (picked !== args.board) throw fail(EXIT.ARGS, `게시판 ${args.board} 을 못 골랐다 — 쓸 수 있는 게시판인지 boards --write 로 본다`);
  await sleep(TEMPLATE_MS);
  const n = await attachFiles(cdp, win, files);   // 본문보다 먼저 — 파일 칸을 찾느라 창의 DOM 을 통째로 받는데, 본문 뒤면 본문의 data URI 그림이 그 답에 든다
  await formFrameEval(win, `(()=>{ document.getElementById('editor1').contentWindow.setContent(${JSON.stringify(html)}); return true; })()`);
  const before = new Set(await formFrameEval(win, DRAFT_IDS(args.title)));
  const box = dialogs(cdp, win);
  await formFrameEval(win, "(()=>{ top.close = function(){}; window.close = function(){}; return true; })()");
  trace(`첨부 ${n} · 저장을 누른다`);
  await formFrameEval(win, "(()=>{ articleSave('TEMP'); return true; })()");
  trace('저장을 눌렀다');
  const done = await waitFor(SAVE_SECONDS, async () => {
    if (box.asked.length) return 'asked';
    if (box.said.length && !(await formFrameEval(win, 'true').catch(() => false))) return 'gone';
    const ids = await board.page.ev('_tabIfr0', DRAFT_IDS(args.title)).catch(() => null);
    return (ids || []).find(id => !before.has(id)) || false;
  });
  box.stop();
  if (done === 'asked') throw fail(EXIT.ARGS, `게시판이 저장을 막았다: ${box.asked.join(' / ')}`);
  if (!done || done === 'gone') {
    const why = box.said.length ? `게시판이 띄운 글: ${box.said.join(' / ')} — ` : '';
    throw fail(EXIT.FAIL, `${why}저장이 섰는지 못 가렸다 — 다시 부르기 전에 drafts 로 임시보관함을 본다(섰으면 show 로 띄운다)`);
  }
  await win.page.detach();
  await cdp.send('Target.closeTarget', {targetId: win.targetId}).catch(() => {});   // 저장 뒤 창은 「새 글」 판이라 닫고 그 글의 편집 창으로 다시 연다
  await waitFor(10, async () => !(await pages()).some(t => t.id === win.targetId));
  trace(`저장 답 ${done} · 편집 창을 연다`);
  const where = await showDraft(cdp, board, done, args.board).catch(e => `못 띄웠다(${e.message}) — 저장은 섰다. show ${done} --board ${args.board} 로 다시 띄운다`);
  return {id: done, board: args.board, title: args.title, files: n, where, board_tab: board};
}

async function main() {
  const [verb, ...rest] = process.argv.slice(2);
  const args = parseArgs(rest);
  if (!['save', 'show'].includes(verb)) throw fail(EXIT.ARGS, '꼴: save --board <id> --title <제목> --body-file <파일> [--file <경로> …] · show <글 id> --board <id>');
  const cdp = await connect((await devtools('/json/version')).webSocketDebuggerUrl);
  try {
    if (verb === 'show') {
      if (!/^QF_\d+$/.test(args.id || '') || !/^BBS\d+$/.test(args.board || '')) throw fail(EXIT.ARGS, 'show 는 <글 id(QF_…)> --board <BBS…> 를 받는다');
      const board = await boardTab(cdp);
      const where = await showDraft(cdp, board, args.id, args.board);
      await board.page.detach();
      return {id: args.id, board: args.board, where};
    }
    const got = await save(cdp, args);
    await got.board_tab.page.detach();
    delete got.board_tab;
    return got;
  } finally {
    cdp.close();
  }
}

main().then(out => { console.log(JSON.stringify(out)); process.exit(EXIT.OK); })
  .catch(e => { console.log(JSON.stringify({error: e.message})); process.exit(Number.isInteger(e.code) ? e.code : EXIT.FAIL); });
