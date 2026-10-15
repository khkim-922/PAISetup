#!/usr/bin/env node
/* 브라우저 MCP 실행기 — 전역 playwright 의 `playwright mcp` 를 **우리 크로미움**에 물려 띄운다 (결정 0149).
 *
 *   node browser-mcp.mjs              # MCP 서버(stdio) — 도구 셋(Claude Code · Codex · agy)의 등록이 부르는 꼴
 *   node browser-mcp.mjs --resolve    # 무엇으로 띄울지 JSON 한 줄을 내고 끝난다 — 어댑터(`browser-mcp.py`)가 묻는다
 *
 * 왜 있나 — 도구 셋의 등록은 고정 글이다. 그런데 브라우저 실행 파일의 자리는 판 번호를 품고(`chromium-snapshot-<판>`), 비영속
 * VDI 에서는 로그인마다 새로 받아 번호가 바뀐다. playwright 의 레지스트리는 제 CDN 판만 알아 그 스냅숏을 못 본다. 그래서 등록은
 * 이 파일 하나를 가리키고, 실행 파일은 **뜰 때마다** 찾는다.
 *
 * 찾는 규칙은 여기 없다 — 검사 씨앗의 `_check/_browser.mjs`(`browserExe` · 아뜰리에 0175 의 차례)를 불러 쓴다. 이 파일은
 * 그 답을 `playwright mcp` 의 인자로 옮기기만 한다:
 *   · 실행 파일을 찾았으면 `--executable-path` · 못 찾았으면 playwright 제 레지스트리의 chromium(0175 의 ④). 어느 쪽이든
 *     `--browser chromium` 이다 — 이 서버의 기본 채널은 깔린 Google Chrome 이라, 안 주면 우리 것이 아닌 브라우저로 샌다
 *   · 집힌 것이 헤드리스 셸이면 `--headless` — 그 파일은 창을 못 띄운다. 그 밖에는 창 있게 띄운다(서버의 기본)
 *   · `--isolated` — 프로필을 메모리에 둔다. 디스크 프로필은 작업 폴더마다 하나라, 같은 폴더의 두 세션이 겹치면 뒤 세션이
 *     「Browser is already in use」로 선다
 *   · `--output-dir` — 이름 없이 찍은 그림 · 스냅숏 파일을 임시 폴더 밑에 둔다. 기본은 작업 폴더의 `.playwright-mcp` 라
 *     저장소에 파일이 쌓인다
 *   · `--config` — 브라우저에 `--disable-features=HttpsFirstBalancedMode` 를 싣는 설정 파일. 우리 스냅숏(크로미움 개발 판)은
 *     평문 주소를 HTTPS 로 올려 보고 실패하면 평문으로 안 돌아가 `ERR_BLOCKED_BY_CLIENT` 로 막는다 — 인증서 이름이 안 맞는
 *     사내 호스트가 평문으로도 HTTPS 로도 영영 안 열렸다(#179 · 사내 VDI 실측). 서버에 브라우저 인자를 넘기는 깃발은 없고
 *     설정 파일뿐이라, 뜰 때마다 임시 폴더에 써서 넘긴다 — 박아 둔 경로는 비영속 VDI 에서 사라진다
 * 위 다섯은 서버가 제 환경변수(`PLAYWRIGHT_MCP_EXECUTABLE_PATH` · `_HEADLESS` · `_ISOLATED` · `_OUTPUT_DIR` · `_CONFIG`)로도
 * 받는다 — 그 변수가 서 있거나 사람이 같은 인자를 등록에 적었으면 우리 것을 안 준다(사람 것이 이긴다). 사람이 제 설정 파일을
 * 주면 위 브라우저 인자도 그 파일이 들어야 한다. 사람이 바꾸는 손잡이는 서버의 것이고 여기 새로 안 만든다.
 *
 * playwright 의 자리 — `PW`(꼴은 `_browser.mjs` 머리말: 이름 · 폴더 · 파일) · 없으면 `npm root -g` 밑. `npx` 는 안 쓴다 —
 * 캐시가 빈 VDI 에서 뜰 때마다 받는다(결정 0117 이 걷은 Tavily 등록의 실측).
 * ⚠ 표준 출력은 MCP 통로다 — 이 파일은 거기 아무것도 안 쓴다(`--resolve` 만 빼고). 말은 표준 오류로.
 */
import { execSync } from "node:child_process";
import { existsSync, mkdirSync, statSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
// `_browser.mjs` 가 서는 자리 — 진본 저장소의 꼴과, 짐 · 홈 씨앗(`seeds/config-repo/.claude/hooks/` 의 곁 `seeds/check/`)의 꼴.
// 두 꼴 다 설치기 · 배포가 같이 놓는다(`seeds/check/` 는 짐에 통째로 실린다).
const BROWSER_PICKERS = [
  join(HERE, "..", "..", "seeds", "check", "_check", "_browser.mjs"),
  join(HERE, "..", "..", "..", "check", "_check", "_browser.mjs"),
];
const PW_PACKAGE = "playwright";
const NPM_ROOT_CAP_MS = 20000;        // `npm root -g` 의 울타리 — 멎은 npm 하나가 세션의 MCP 시작을 영구히 세우지 않게
const OUTPUT_SUBDIR = "playwright-mcp";
const CONFIG_FILE = "browser-launch.json";   // `--config` 로 넘길 설정 — OUTPUT_SUBDIR 밑에 뜰 때마다 쓴다
const BROWSER_ARGS = ["--disable-features=HttpsFirstBalancedMode"];   // 머리말 `--config` 칸
const RESOLVE_FLAG = "--resolve";
const EXIT_NO_PLAYWRIGHT = 3;
const EXIT_NO_PICKER = 4;

const say = (msg) => process.stderr.write(`[browser-mcp] ${msg}\n`);
const envSet = (name) => (process.env[name] ?? "") !== "";

/** playwright 패키지 폴더 — 못 찾으면 null. */
function playwrightDir() {
  const said = process.env.PW;
  if (said) {
    if (!isAbsolute(said)) {
      try { return dirname(createRequire(join(process.cwd(), "noop.js")).resolve(`${said}/package.json`)); }
      catch { return null; }
    }
    try { return statSync(said).isDirectory() ? said : dirname(said); }
    catch { return null; }
  }
  try {
    const root = execSync("npm root -g", { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], timeout: NPM_ROOT_CAP_MS }).trim();
    const dir = join(root, PW_PACKAGE);
    return existsSync(join(dir, "package.json")) ? dir : null;
  } catch {
    return null;
  }
}

/** 무엇으로 띄우나 — `{ pw, exe, source, headless, args }`. source 는 found(찾았다) · registry(레지스트리에 맡긴다). */
async function plan() {
  const pw = playwrightDir();
  if (!pw) {
    say(`${PW_PACKAGE} 를 못 찾았다 — ${process.env.PW ? `PW(${process.env.PW}) 자리에 없다` : "npm root -g 밑에 없다"}`);
    process.exit(EXIT_NO_PLAYWRIGHT);
  }
  const picker = BROWSER_PICKERS.find((p) => existsSync(p));
  if (!picker) {
    say(`_browser.mjs 를 못 찾았다 — ${BROWSER_PICKERS.join(" · ")}`);
    process.exit(EXIT_NO_PICKER);
  }
  process.env.PW = pw;                 // `_browser.mjs` 가 모듈을 이 자리에서 연다
  const { browserExe, chromium, HEADLESS_MATCH } = await import(pathToFileURL(resolve(picker)).href);
  const exe = envSet("PLAYWRIGHT_MCP_EXECUTABLE_PATH") ? process.env.PLAYWRIGHT_MCP_EXECUTABLE_PATH : browserExe();
  const source = exe ? "found" : "registry";
  const shown = exe || (() => { try { return chromium.executablePath(); } catch { return null; } })();
  // ⚠ 홈 씨앗의 `_browser.mjs` 는 설정 저장소의 배포가 따로 밀 수 있어 이 파일보다 옛 판일 수 있다 — 그 판은 이름표를 안
  //   내보낸다. 그때는 창 없이 띄운다: 헤드리스 셸도 머리 달린 판도 그렇게는 뜬다(창 있게는 셸이 못 뜬다).
  if (exe && !HEADLESS_MATCH) say("_browser.mjs 가 헤드리스 셸 이름표를 안 내보내는 옛 판이라 창 없이 띄운다");
  const headless = Boolean(exe && (HEADLESS_MATCH ? HEADLESS_MATCH.has(basename(exe)) : true));
  const args = ["--browser", "chromium"];
  if (exe && !envSet("PLAYWRIGHT_MCP_EXECUTABLE_PATH")) args.push("--executable-path", exe);
  if (headless && !envSet("PLAYWRIGHT_MCP_HEADLESS")) args.push("--headless");
  if (!envSet("PLAYWRIGHT_MCP_ISOLATED") && !envSet("PLAYWRIGHT_MCP_USER_DATA_DIR")) args.push("--isolated");
  if (!envSet("PLAYWRIGHT_MCP_OUTPUT_DIR")) args.push("--output-dir", join(tmpdir(), OUTPUT_SUBDIR));
  if (!envSet("PLAYWRIGHT_MCP_CONFIG") && !process.argv.slice(2).some((a) => a === "--config" || a.startsWith("--config="))) {
    const cfg = join(tmpdir(), OUTPUT_SUBDIR, CONFIG_FILE);
    try {
      mkdirSync(dirname(cfg), { recursive: true });
      writeFileSync(cfg, JSON.stringify({ browser: { launchOptions: { args: BROWSER_ARGS } } }));
      args.push("--config", cfg);
    } catch (e) { say(`설정 파일을 못 썼다(${cfg}) — 평문 주소가 막힐 수 있다: ${e.message}`); }
  }
  return { pw, exe: shown, exists: Boolean(shown && existsSync(shown)), source, headless, args };
}

const p = await plan();
if (process.argv.includes(RESOLVE_FLAG)) {
  process.stdout.write(JSON.stringify(p) + "\n");
} else {
  say(`${p.source === "found" ? "브라우저" : "레지스트리 브라우저"} ${p.exe ?? "(없음)"}${p.headless ? " · 헤드리스 셸이라 창 없이" : ""}`);
  // 같은 프로세스에서 넘긴다 — 자식을 하나 더 띄우면 표준 입출력을 이어 줄 손과 끝내기 전달이 는다
  const { program } = createRequire(join(p.pw, "package.json"))("./lib/program");
  program.parse([process.execPath, join(p.pw, "cli.js"), "mcp", ...p.args, ...process.argv.slice(2)]);
}
