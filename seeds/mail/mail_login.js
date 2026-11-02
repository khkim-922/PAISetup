// 사내 SSO 를 Edge 로 넘어 메일함 세션 쿠키를 파일로 남긴다 — inbox.py 가 그 파일을 읽는다.
//
// 부르는 꼴:
//     node mail_login.js <메일함 주소>  [쿠키 파일]
//   메일함 주소는 웹메일 주소창의 …/이름.nsf 까지(뒤는 버린다). 쿠키 파일 기본은 ~/.mailbox-session.json.
//   환경변수 MAILBOX_URL · MAILBOX_COOKIES 로 줘도 된다.
//
// 내는 것: 쿠키 파일(Playwright 저장 상태 꼴 · {"cookies": [...]}) — 종료 0. 시한 안에 못 넘으면 종료 1.
//
// 하는 일: Edge 창을 띄워 받은편지함 목록 주소를 연다. 그 창에서 사람이 로그인하면(VDI) 포털로 간 뒤 그 탭으로
// 목록 주소에 다시 들르고, 목록 XML 이 오면 넘은 것이다. 사내 SSO 가 Windows 로그인으로 그냥 넘겨 주는 PC 면 로그인
// 화면 없이 끝날 것으로 보지만 안 쟀다. ⚠ 메일 문서는 열지 않는다 — 여는 순간 그 메일이 읽음이 된다(inbox.py 머리말).
//
// ⚠ 쿠키 파일은 메일함 열쇠다 — 저장소 밖(홈)에 두고 남에게 넘기지 않는다.
//
// 필요한 것: Node · 전역 playwright · Edge. 전역 모듈을 찾게 NODE_PATH 를 준다:
//     NODE_PATH="$(npm root -g)" node mail_login.js <주소>

const fs = require('fs');
const os = require('os');
const path = require('path');
const { chromium } = require('playwright');

const VIEW = process.env.MAILBOX_VIEW || 'XML_Inbox';
const WAIT_SECONDS = Number(process.env.MAILBOX_LOGIN_WAIT_SECONDS || 300);
// 사람이 로그인하는 화면의 호스트 — 사내 SSO · ADFS
const LOGIN_HOSTS = /^(swpsso|adfs\.m365)\.posco\.net$/i;

function base(url) {
  const match = /^(https?:\/\/[^/]+\/.+?\.nsf)/i.exec((url || '').trim());
  if (!match) throw new Error(`메일함 주소(…/이름.nsf)가 아니다: ${url}`);
  return match[1];
}

async function main() {
  const box = base(process.argv[2] || process.env.MAILBOX_URL);
  const out = path.resolve((process.argv[3] || process.env.MAILBOX_COOKIES || '~/.mailbox-session.json')
    .replace(/^~(?=$|[\\/])/, os.homedir()));
  const list = `${box}/${encodeURIComponent(VIEW)}?ReadViewEntries&count=1`;

  // ⚠ 통합 인증을 플래그(--auth-server-allowlist)로 강제하지 않는다 — VDI 에서는 ADFS 의 통합 인증이 401 로 지고,
  // 강제하면 로그인 창이 되풀이된다. 데스크톱의 자동 로그인은 Edge 가 인트라넷에 원래 하는 통합 인증에 맡긴다
  const browser = await chromium.launch({ channel: 'msedge', headless: false });
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    // ⚠ Playwright 는 확인 창을 기본으로 「취소」로 닫는다. 사내 SSO 는 로그인이 이미 있으면 「끊고 다시 할까」를
    // 묻는데, 그것이 취소되면 로그인 화면이 되풀이된다 — 로그인 화면의 창만 「확인」으로 받는다
    page.on('dialog', dialog => {
      const fromLogin = LOGIN_HOSTS.test(new URL(page.url()).host);
      console.log(`로그인 화면의 창: ${dialog.message().slice(0, 80)} → ${fromLogin ? '확인' : '취소'}`);
      (fromLogin ? dialog.accept() : dialog.dismiss()).catch(() => {});
    });
    await page.goto(list, { timeout: 60000 }).catch(() => {});
    console.log(`로그인을 기다린다 — 창에 로그인 화면이 뜨면 로그인한다(최대 ${WAIT_SECONDS}초)`);

    const deadline = Date.now() + WAIT_SECONDS * 1000;
    while (Date.now() < deadline) {
      const response = await context.request.get(list, { maxRedirects: 0 }).catch(() => null);
      const type = response ? response.headers()['content-type'] || '' : '';
      if (response && response.status() === 200 && type.includes('xml')) {
        await context.storageState({ path: out });
        console.log(`넘었다 — 쿠키를 남겼다: ${out}`);
        return 0;
      }
      // 로그인 화면을 벗어났는데(포털로 갔는데) 아직 목록이 안 오면 그 탭으로 메일 서버에 한 번 들른다 —
      // SSO 가 메일 서버의 세션을 세우는 것은 그 서버로 가는 탐색에서다. 로그인 화면에 있는 동안은 탭을 건드리지 않는다
      if (!LOGIN_HOSTS.test(new URL(page.url()).host) && new URL(page.url()).href !== list) {
        await page.goto(list, { timeout: 60000 }).catch(() => {});
      }
      await page.waitForTimeout(3000);
    }
    console.error('시한 안에 로그인을 못 넘었다 — 다시 돌린다');
    return 1;
  } finally {
    await browser.close();
  }
}

main().then(code => process.exit(code), error => { console.error(error.message); process.exit(1); });
