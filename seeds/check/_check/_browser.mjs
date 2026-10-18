/* 브라우저를 **판에 안 매이게** 띄운다 — 화면 실측들이 함께 쓰는 자리.
 *
 * 부르는 꼴 — `import { launch } from "./_browser.mjs"` · 실행 파일만 필요하면 `browserExe`. 내는 것 —
 * `launch(opts)` 는 띄운 브라우저의 Promise · `browserExe()` 는 경로나 null · `chromium` · `HEADLESS_MATCH`.
 * 무는 순간 playwright 모듈을 연다 — 못 열면 import 가 던진다. 부품이라 종료코드를 안 낸다.
 *
 * playwright 는 제가 받은 판만 안다. 레지스트리에 박힌 번호와 실물이 어긋나면
 * `Executable doesn't exist at …/chromium_headless_shell-1234/…` 로 서고, 안내는
 * `playwright install` 을 시킨다 — 그 길이 막힌 자리에서는 검사가 통째로 못 돈다. 재는 것은
 * 브라우저의 판이 아니라 우리 화면이라, 크로미움이 무엇이든 하나만 서 있으면 된다. 그래서 판을
 * 맞추는 대신 **실행 파일을 찾아 직접 가리킨다**(`executablePath`) — 크로미움이 올라가도,
 * playwright 가 올라가도, 둘이 어긋나도 그대로 돈다.
 *
 * 찾는 차례 — 먼저 걸리는 것을 쓴다:
 *   ① `PW_EXE` — 손으로 못박은 자리 (다른 다 제치고 이것)
 *   ② 받아 둔 자리 아래 아무 크로미움 — 훅·손이 받아 둔 것. 자리는 `PLAYWRIGHT_BROWSERS_PATH` · 그
 *      변수가 없으면 `~/.cache/ms-playwright`. 판 번호를 안 읽고 이름만 보고 집으므로 번호가 바뀌어도 걸린다
 *   ③ `PATH` 의 크로미움 계열 — 배포판이 깔아 둔 자리
 *   ④ 못 찾으면 playwright 기본값에 맡긴다 — 제 레지스트리가 맞는 자리(사내 PC 등)
 *      에서는 그게 정답이라, 못 찾았다고 실패로 접지 않는다
 *
 * ⚠ **앱이 지면을 찍는 파이썬 짝을 두면 이 차례에는 쌍둥이가 생긴다** — 아뜰리에는 `app/shot.py`
 *   의 `browser_exe()` 가 같은 차례를 든다. 언어가 갈려 코드를 못 나누므로 차례를 바꿀 때는
 *   둘 다 바꾼다(아뜰리에 결정 0175). 검사에서만 브라우저를 띄우는 저장소는 쌍둥이가 없다.
 *
 * 모듈 자리는 `PW` 가 든다 — 전역(npm -g)에 깔린 playwright 를 쓸 때. 꼴은 셋 다
 * 산다: 패키지 이름 · 폴더(`PW="$(npm root -g)/playwright"`) · 파일(`…/index.js` 나 `file://…`).
 * 윈도우 경로도 그대로 준다 — 모듈 주소로 푸는 것은 아래 `moduleSpec` 이다 (atelier #337).
 */
import { accessSync, constants, readdirSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { homedir } from "node:os";
import { delimiter, isAbsolute, join } from "node:path";
import { pathToFileURL } from "node:url";

// 경로로 온 `PW` 를 모듈 주소로 푼다 (atelier #337). ESM 의 `import()` 는 둘을 거절한다 —
// 윈도우 경로(드라이브 글자를 「c: 스킴」으로 읽는다)와 폴더(진입점이 없다). 머리말이 시키는 값
// `PW="$(npm root -g)/playwright"` 가 윈도우에서 바로 그 꼴이라, 안 풀면 첫 줄에서 죽는다.
// 패키지 이름과 `file://` 주소는 안 건드린다. 진입점은 손으로 안 찾는다 — CJS 해석기가
// `package.json` 을 읽어 답한다.
const PW = process.env.PW || "playwright";
function moduleSpec(said) {
  if (!isAbsolute(said)) return said;
  try { return pathToFileURL(createRequire(import.meta.url).resolve(said)).href; }
  catch { return pathToFileURL(said).href; }
}
export const { chromium } = await import(moduleSpec(PW)).then(m => m.default ?? m);

// 크로미움 계열이 쓰는 실행 파일 이름들 — playwright 판에 따라 헤드리스 셸 이름이 `headless_shell`
// 이거나 `chrome-headless-shell` 이라 다 문다.
const EXE_NAMES = ["chrome", "chromium", "headless_shell", "chrome-headless-shell"];
// 윈도우 실행 파일은 `.exe` 가 붙는다 — 그 꼴이 목록에 없으면 받아 둔 자리를 훑어도 아무것도 안 걸린다
// (atelier #313). 목록을 손으로 여덟 줄로 늘리지 않고 위 넷에서 파생한다 — 이름의 진본은 위 넷 하나로
// 두고, 파이썬 쌍둥이가 있는 저장소는 그쪽도 같은 규칙을 든다(아뜰리에 0175).
const EXE_MATCH = new Set([...EXE_NAMES, ...EXE_NAMES.map(n => `${n}.exe`)]);
// **받아 둔 자리 안에서는 헤드리스 셸을 먼저 집는다.** 검사는 헤드리스로 띄우고, 회사 PC 에서
// `chrome.exe` 는 `spawn UNKNOWN` 으로 못 뜨는데 헤드리스 셸은 뜬다(atelier #313). playwright 기본값이
// 도는 것도 헤드리스 셸을 쓰기 때문이라, 이름만 맞춰 `chrome.exe` 를 먼저 집으면 잘 돌던 기계가 못 뜬다.
// 파이썬 쌍둥이가 같은 순서를 든다(아뜰리에 0175). 이 순서는 찾는 차례를 안 바꾼다 — 받아 둔 자리
// 안에서 무엇을 먼저 집나뿐이다.
// 내보내는 까닭 — 브라우저 MCP 실행기(claude-config `.claude/hooks/browser-mcp.mjs`)는 창 있게 띄우는 것이
// 기본이라, 집힌 파일이 헤드리스 셸이면 창 없이 띄우려고 같은 이름표로 묻는다. 이름을 그쪽에 베끼면
// 여기서 이름이 늘 때 저쪽만 낡는다.
const HEADLESS_FIRST = ["chrome-headless-shell", "headless_shell"];
export const HEADLESS_MATCH = new Set([...HEADLESS_FIRST, ...HEADLESS_FIRST.map(n => `${n}.exe`)]);
// ⚠ **`chrome` 은 이 목록에 안 넣는다.** 이름을 맞추면 회사 PC 에서 `chrome.exe` 가 걸리는데
//   그 파일은 `spawn UNKNOWN` 으로 못 뜬다 — 잘 돌던 검사가 죽는다(atelier #313).
//   여기는 배포판이 깔아 두는 이름만 든다 — 확장자는 아래 `PATH_EXTS` 가 든다.
const ON_PATH = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"];
// 윈도우는 확장자가 이름의 일부라 `PATHEXT` 를 얹는다 — 안 얹으면 `chromium.exe` 를 못 본다.
// 파이썬 쌍둥이의 `shutil.which` 가 하는 그대로다(이름 → 자리 → 확장자 순으로 돈다).
const PATH_EXTS = process.platform === "win32"
  ? (process.env.PATHEXT || ".COM;.EXE;.BAT;.CMD").split(";").filter(Boolean)
  : [""];

// ⚠ 윈도우에서는 확장자가 실행 가능성의 일부다 — `X_OK` 는 거기서 아무것도 안 거른다. 확장자 없는
//   사본이 실행 파일로 집히면 `spawn` 이 ENOENT 로 진다. 쌍둥이는 설정 저장소(claude-config)의
//   `scripts/pw-resolve.mjs` 와 `.claude/get-browser.sh` 의 `runnable` 에 살고 같은 줄을 든다 — 바뀌면 셋 다 바꾼다.
function runnable(p) {
  if (process.platform === "win32" && !p.toLowerCase().endsWith(".exe")) return false;
  try {
    accessSync(p, constants.X_OK);
    return statSync(p).isFile();      // statSync 는 링크를 따라간다 — 끊긴 링크는 여기서 걸린다
  } catch {
    return false;
  }
}

// 받아 둔 자리 — 변수가 없을 때의 자리까지 이 한 줄이 든다. 그 변수가 안 선 기계가 보통이라, 변수만
// 보고 없으면 null 을 내면 브라우저가 멀쩡히 있는 기계에서 이 갈래가 통째로 눈이 멀고, 기본값으로 떨어진
// playwright 가 제 레지스트리의 없는 판을 가리켜 `Executable doesn't exist` 로 선다.
// ⚠ **받는 자리와 찾는 자리는 같은 식으로 정한다** — 받는 손(claude-config `.claude/get-browser.sh` 의
//   `ROOT`)이 변수가 없으면 `~/.cache/ms-playwright` 에 풀므로 여기도 같은 기본값을 든다. 한쪽만 바꾸면
//   받아 둔 것을 아무도 못 본다. 그 자리는 리눅스에서만 playwright 자신의 기본 자리와 겹친다 — 윈도우의
//   playwright 는 `%LOCALAPPDATA%/ms-playwright` 에 받아 이 갈래에는 안 걸린다(그 판은 기본값이 찾는다).
const browsersRoot = () => process.env.PLAYWRIGHT_BROWSERS_PATH || join(homedir(), ".cache", "ms-playwright");

function underBrowsersPath() {
  // 얕은 곳부터 훑는다(너비 우선) — `…/chromium` 같은 지름길 링크가 먼저 걸린다
  const queue = [browsersRoot()];
  let fallback = null;                // 헤드리스 셸이 끝내 안 나오면 이것을 쓴다
  while (queue.length) {
    let entries;
    const dir = queue.shift();
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;                       // 못 읽는 자리는 건너뛴다
    }
    const dirs = [];
    for (const e of entries) {
      const p = join(dir, e.name);
      if (EXE_MATCH.has(e.name) && runnable(p)) {
        if (HEADLESS_MATCH.has(e.name)) return p;   // 우리가 쓸 꼴이다 — 더 볼 것 없다
        if (fallback === null) fallback = p;        // 머리 달린 판 — 셸이 없을 때만
      }
      if (e.isDirectory()) dirs.push(p);
    }
    queue.push(...dirs);
  }
  return fallback;
}

// ⚠ **하위 프로세스를 안 띄우고 `PATH` 를 갈라 파일로 훑는다.** 셸에 묻는 꼴(`command -v`)은 윈도우 cmd 에
//   `command` 가 없어 이름마다 오류문을 내고, 그 소음을 삼키면 이 갈래가 윈도우에서 늘 「없다」를 낸다
//   (atelier #337). 파이썬 쌍둥이의 `shutil.which` 는 양쪽에서 답하므로 그때 차례가 플랫폼마다 갈린다
//   (아뜰리에 0175). 파일 조회는 어디서나 답하고, cmd 를 넷 안 띄우고, Node 24 의 DEP0190 경고도 안 난다.
//   이 자리가 재는 것은 「그 이름이 있나」뿐이다.
function onPath() {
  const dirs = (process.env.PATH || "").split(delimiter).filter(Boolean);
  for (const name of ON_PATH) {
    for (const dir of dirs) {
      for (const ext of PATH_EXTS) {
        const p = join(dir, name + ext);
        if (runnable(p)) return p;
      }
    }
  }
  return null;
}

/** 쓸 실행 파일 — 머리말의 찾는 차례대로 집은 경로, 못 찾으면 null(= playwright 기본값에 맡긴다). */
export function browserExe() {
  return process.env.PW_EXE || underBrowsersPath() || onPath() || null;
}

/** 판에 안 매인 launch — `opts` 는 `chromium.launch` 의 옵션이고, 찾은 실행 파일이 있으면
 *  `executablePath` 로 얹는다. 띄울 때마다 무엇을 집었나(또는 기본값으로 갔나)를 `[browser]` 한 줄로
 *  찍는다 — 초록만 내고 무엇으로 쟀는지 안 말하면 다음 사람이 「이 검사가 무엇을 봤나」를 되물어야 한다. */
export async function launch(opts = {}) {
  const exe = browserExe();
  console.log(exe
    ? `[browser] ${exe}`
    : "[browser] playwright 기본값 — 실행 파일을 못 찾아 제 레지스트리에 맡긴다");
  return chromium.launch(exe ? { ...opts, executablePath: exe } : opts);
}
