/* 검사가 **제 뿌리와 제 파이썬을 아는** 자리 — 다섯이 각자 짓던 것을 한 자리로.
 *
 * 여기 있는 것은 둘 다 **자리를 박는 자가 아니라 묻는 자**다. 기계 이름·절대 경로는
 * 한 글자도 안 든다 — 물어서 그 기계의 답을 받는다.
 *
 * ⚠ **`new URL(...).pathname` 은 한 글자가 두 뜻이다.** 윈도우에서 그것은 `/C:/…` 인데,
 *   `file://` 뒤에 붙일 때는 맞는 글자고 **파일 경로로 쓰면 드라이브가 두 번 박힌다**
 *   (`C:\C:\…`). 그래서 같은 자리에서 둘을 갈라 낸다 — 경로는 `treeDir`, 주소는
 *   `fileHref`. 리눅스에서는 둘이 종전과 같은 글자를 낸다(그래서 저쪽은 안 바뀐다).
 *
 * ⚠ **`python3` 는 이름부터 틀린 자리였다.** 윈도우에는 그런 파일이 없다 — 진짜 설치에도
 *   `.venv` 에도 없고, 그 이름을 가진 것은 스토어 리다이렉터(0바이트)뿐이라 이 저장소의
 *   파이썬에 **영영 안 닿는다.** 리눅스에서는 닿기는 하는데 **닿는 데가 틀리다**: 그것은
 *   컨테이너 기본 판이고, 이 저장소가 선언한 해석기는 이 나무의 `.venv` 다
 *   (아뜰리에 결정 0171 — 「다른 판으로
 *   조용히 서지 않는다」가 막은 것이 바로 그 기본값이다). 이 검사들은 `app` 을 불러
 *   봉투를 **진본으로** 짓는 자라, 해석기가 갈리면 재는 것이 그 세계의 것이 아니게 된다.
 */
import { existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

/** 잴 나무의 뿌리 — 인자로 준 것이 있으면 그것, 없으면 이 파일이 사는 나무.
 *
 * 병렬 레인이 제 작업나무를 인자로 넘기는 자리라, 준 것이 이긴다.
 */
export function treeDir(given) {
  return given ? resolve(given)
               : resolve(fileURLToPath(new URL("..", import.meta.url)));
}

/** 뿌리 밑 한 자리를 브라우저·`import` 가 열 수 있는 `file://` 주소로. */
export function fileHref(dir, ...parts) {
  return pathToFileURL(join(dir, ...parts)).href;
}

/** 이 나무의 파이썬.
 *
 * 차례가 셋이고 **위에서부터 처음 서는 것**을 쓴다.
 *   ① `PY` — 사람이 못박은 것이 언제나 이긴다
 *   ② 이 나무의 `.venv` — 검사가 부르는 `app` 의 의존성이 사는 자리
 *   ③ 판에 맞는 이름 — venv 없이 의존성을 시스템에 둔 기계의 종전 동작
 */
export function pyExe(dir = treeDir()) {
  if (process.env.PY) return process.env.PY;
  const venv = process.platform === "win32"
    ? join(dir, ".venv", "Scripts", "python.exe")
    : join(dir, ".venv", "bin", "python");
  if (existsSync(venv)) return venv;
  return process.platform === "win32" ? "python" : "python3";
}
