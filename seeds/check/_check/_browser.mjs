/* 브라우저를 **판에 안 매이게** 띄운다 — 화면 실측들이 함께 쓰는 자리.
 *
 * playwright 는 **제가 받은 판만 안다.** 레지스트리에 박힌 번호와 실물이 어긋나면
 * `Executable doesn't exist at …/chromium_headless_shell-1234/…` 로 서고, 안내는
 * `playwright install` 을 시킨다 — 그 길이 막힌 자리에서는 검사가 통째로 못 돈다.
 *
 * 그런데 **우리가 재는 것은 브라우저의 판이 아니라 우리 화면**이다. 크로미움이
 * 무엇이든 하나만 서 있으면 잴 수 있다. 그래서 판을 맞추는 대신 **실행 파일을 찾아
 * 직접 가리킨다**(`executablePath`) — 크로미움이 올라가도, playwright 가 올라가도,
 * 둘이 어긋나도 그대로 돈다.
 *
 * 찾는 차례 — 먼저 걸리는 것을 쓴다:
 *   ① `PW_EXE` — 손으로 못박은 자리 (다른 다 제치고 이것)
 *   ② **받아 둔 자리** 아래 아무 크로미움 — 훅·playwright·손이 받아 둔 것. 자리는
 *      `PLAYWRIGHT_BROWSERS_PATH` · **그 변수가 없으면 `~/.cache/ms-playwright`**.
 *      **판 번호를 안 읽는다** — 이름만 보고 집으므로 번호가 바뀌어도 걸린다
 *   ③ `PATH` 의 크로미움 계열 — 배포판이 깔아 둔 자리
 *   ④ 못 찾으면 **playwright 기본값에 맡긴다** — 제 레지스트리가 맞는 자리(사내 PC 등)
 *      에서는 그게 정답이라, 못 찾았다고 실패로 접지 않는다
 *
 * ⚠ **판이 어긋나면 그 사실을 말한다** — 못 찾아 기본값으로 갔는지, 어느 실행 파일을
 *   집었는지를 한 줄 찍는다. 초록만 내고 무엇으로 쟀는지 안 말하면, 다음 사람이
 *   「이 검사가 무엇을 봤나」를 되물어야 한다.
 *
 * ⚠ **앱이 지면을 찍는 파이썬 짝을 두면 이 차례에는 쌍둥이가 생긴다** — 아뜰리에는 `app/shot.py`
 *   의 `browser_exe()` 가 같은 차례를 든다. 언어가 갈려 코드를 못 나누므로 **차례를 바꿀 때는
 *   둘 다 바꾼다**(아뜰리에 결정 0175). 검사에서만 브라우저를 띄우는 저장소는 쌍둥이가 없다.
 *
 * 모듈 자리는 종전대로 `PW` 가 든다 — 전역(npm -g)에 깔린 playwright 를 쓸 때. 꼴은 셋 다
 * 산다: 패키지 이름 · 폴더(`PW="$(npm root -g)/playwright"`) · 파일(`…/index.js` 나 `file://…`).
 * 윈도우 경로도 그대로 준다 — 모듈 주소로 푸는 것은 아래 `moduleSpec` 이다 (atelier #337).
 */
import { accessSync, constants, readdirSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { homedir } from "node:os";
import { delimiter, isAbsolute, join } from "node:path";
import { pathToFileURL } from "node:url";

// ⚠ **경로로 온 `PW` 를 모듈 주소로 푼다** (atelier #337). ESM 의 `import()` 는 둘을 거절한다 —
//   윈도우 경로(드라이브 글자를 「c: 스킴」으로 읽는다)와 폴더(진입점이 없다). 그런데
//   머리말이 시키는 값이 정확히 그 꼴이다: `PW="$(npm root -g)/playwright"` 가 윈도우에서
//   첫 줄에서 죽었다(실측 2026-09-05). 패키지 이름과 `file://` 주소는 안 건드린다.
//   진입점은 손으로 안 찾는다 — CJS 해석기가 `package.json` 을 읽어 답한다.
const PW = process.env.PW || "playwright";
function moduleSpec(said) {
  if (!isAbsolute(said)) return said;
  try { return pathToFileURL(createRequire(import.meta.url).resolve(said)).href; }
  catch { return pathToFileURL(said).href; }
}
export const { chromium } = await import(moduleSpec(PW)).then(m => m.default ?? m);

// 크로미움 계열이 쓰는 실행 파일 이름들 — 판마다 갈리므로 다 문다.
// (`headless_shell` 은 옛 이름, `chrome-headless-shell` 은 지금 이름)
const EXE_NAMES = ["chrome", "chromium", "headless_shell", "chrome-headless-shell"];
// 윈도우 실행 파일은 `chrome.exe` 다 — 이름 목록에 그 꼴이 없어 ②가 통째로 눈이 멀었다
// (atelier #313 · 실측 2026-09-02). **목록을 손으로 여덟 줄로 늘리지 않고 파생한다** —
// 이름의 진본은 위 넷 하나로 두고, 파이썬 쌍둥이가 있는 저장소는 그쪽도 같은 규칙을 든다(아뜰리에 0175).
const EXE_MATCH = new Set([...EXE_NAMES, ...EXE_NAMES.map(n => `${n}.exe`)]);
// **헤드리스 셸을 먼저 집는다 — 우리는 늘 헤드리스로 띄우기 때문이다.** 취향이 아니라
// 실측이 세운 순서다: 이 자리에서 `chrome.exe` 는 **못 뜨고**(`spawn UNKNOWN` · 회사 PC
// 실측 2026-09-02) 헤드리스 셸은 뜬다. playwright 기본값이 여태 멀쩡히 돌던 까닭도 저쪽이
// 헤드리스 셸을 쓰기 때문이다 — 이름만 맞춰 `chrome.exe` 를 집으면 **잘 돌던 기계를
// 망가뜨린다**(atelier #313 을 고치다 실제로 그렇게 됐다). 파이썬 쌍둥이가 같은 순서를 든다(아뜰리에 0175).
// ⚠ 차례(①②③④)는 안 바꾼다 — 여기서 정하는 것은 ② **안에서** 무엇을 먼저 집나뿐이다.
const HEADLESS_FIRST = ["chrome-headless-shell", "headless_shell"];
const HEADLESS_MATCH = new Set([...HEADLESS_FIRST, ...HEADLESS_FIRST.map(n => `${n}.exe`)]);
// ⚠ **`chrome` 은 이 목록에 안 넣는다.** 이름을 맞추면 회사 PC 에서 `chrome.exe` 가 걸리는데
//   그 파일은 `spawn UNKNOWN` 으로 **못 뜬다**(atelier #313 을 고치다 잘 돌던 검사를 실제로 죽였다).
//   여기는 배포판이 깔아 두는 이름만 든다 — 확장자는 아래 `PATH_EXTS` 가 든다.
const ON_PATH = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"];
// ⚠ **윈도우는 확장자가 이름의 일부다** — `PATHEXT` 를 얹지 않으면 `chromium.exe` 를 못 본다.
//   파이썬 쌍둥이의 `shutil.which` 가 하는 그대로다(이름 → 자리 → 확장자 순으로 돈다).
const PATH_EXTS = process.platform === "win32"
  ? (process.env.PATHEXT || ".COM;.EXE;.BAT;.CMD").split(";").filter(Boolean)
  : [""];

// ⚠ 윈도우에서는 확장자가 실행 가능성의 일부다 — `X_OK` 는 거기서 아무것도 안 거른다. 확장자 없는
//   사본이 실행 파일로 집히면 `spawn` 이 ENOENT 로 진다. 쌍둥이 `scripts/pw-resolve.mjs` 와 같은 줄.
function runnable(p) {
  if (process.platform === "win32" && !p.toLowerCase().endsWith(".exe")) return false;
  try {
    accessSync(p, constants.X_OK);
    return statSync(p).isFile();      // statSync 는 링크를 따라간다 — 끊긴 링크는 여기서 걸린다
  } catch {
    return false;
  }
}

// 받아 둔 자리 — **변수가 없을 때의 자리까지 이 한 줄이 든다.**
// ⚠ **그 변수가 안 선 기계가 보통이다.** 받아 두는 자는 변수가 없으면 `~/.cache/ms-playwright`
//   에 푸는데(playwright 자신의 기본 자리이기도 하다), 여기서 변수만 보고 없으면 곧장 null 을
//   내던 판은 **브라우저가 멀쩡히 있는 기계에서 ②가 통째로 눈이 멀었다** — ④ 로 떨어진
//   playwright 가 제 레지스트리의 **없는 판**을 가리켜 `Executable doesn't exist` 로 섰다
//   (실측 2026-09-14 · 윈도우). **받는 자리와 찾는 자리는 같은 식으로 정한다** — 한쪽만
//   기본값을 들면 받아 둔 것을 아무도 못 본다.
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

// ⚠ **하위 프로세스를 안 띄운다.** 여기서 `command -v` 를 부르던 판은 윈도우 cmd 에
//   `command` 가 없어 이름마다 오류문을 냈고, 그 소음을 삼키고 나니 **③ 이 윈도우에서
//   늘 「없다」를 내는 자리로 굳었다**(atelier #337). 그런데 파이썬 쌍둥이는 `shutil.which` 라
//   양쪽에서 답한다 — 즉 그 판은 아뜰리에 0175 의 「차례는 둘이 같다」를 **플랫폼에서 어기고
//   있었다.** `PATH` 를 갈라 훑는 순수 파일 조회는 어디서나 답하고, cmd 를 넷 안 띄우고,
//   Node 24 의 DEP0190 경고도 함께 사라진다. 이 자리가 재는 것은 「그 이름이 있나」뿐이다.
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

/** 쓸 실행 파일 — 못 찾으면 null(= playwright 기본값에 맡긴다). */
export function browserExe() {
  return process.env.PW_EXE || underBrowsersPath() || onPath() || null;
}

/** 판에 안 매인 launch — 찾은 실행 파일을 가리키고, 무엇으로 쟀는지 한 줄 찍는다. */
export async function launch(opts = {}) {
  const exe = browserExe();
  console.log(exe
    ? `[browser] ${exe}`
    : "[browser] playwright 기본값 — 실행 파일을 못 찾아 제 레지스트리에 맡긴다");
  return chromium.launch(exe ? { ...opts, executablePath: exe } : opts);
}
