#!/usr/bin/env bash
# 브라우저를 띄우는 검사가 쓸 크로미움을 **판을 안 박고** 받는다.
#
# 진본은 claude-config/.claude/get-browser.sh 다. 각 저장소의 것은 deploy.ps1 이 뿌린
# 배포본이다 — **배포본을 고치면 다음 배포에 덮인다.** 어긋나면
# scripts/check-global-copies.sh 가 문다. 어느 저장소가 받나는 deploy.repofiles.conf 가 든다.
#
#   bash .claude/get-browser.sh          # 없으면 받는다, 있으면 그대로 둔다
#   bash .claude/get-browser.sh --force  # 있어도 최신으로 다시 받는다
#
# 왜 있나 — `playwright install` 은 제 판에 맞는 브라우저를 **playwright CDN 에서만**
# 받는다. 그 호스트가 막힌 자리(사내·리모트 컨테이너)에서는 브라우저를 띄우는 검사가
# 통째로 못 돈다. 여기서는 **구글 공식 스냅샷 버킷**에서 받는다 — 같은 크로미움이고
# 호스트만 다르다.
# ⚠ 게다가 그 명령은 받기 전에 **제 판과 안 맞는 브라우저를 「쓸모없다」며 먼저 지운다** —
#   막힌 자리에서는 지우기만 하고 못 받아 **있던 것까지 없어진다**(실측 2026-09-11). 그래서
#   훅은 이 뒷길이 선언돼 있으면 그 CDN 을 아예 안 부른다.
#
# ⚠ **판 번호를 어디에도 안 박는다.** 받을 때마다 `LAST_CHANGE` 를 물어 그때의 최신을
#   받고, 푼 자리 이름에만 그 번호가 남는다. 그래서 이 파일은 크로미움이 올라가도,
#   playwright 가 올라가도 안 낡는다 — `github-release-binary` 가 `releases/latest` 를
#   쓰는 것과 같은 결이다.
#
# ⚠ **받은 판과 playwright 의 판이 어긋나도 된다.** 검사는 `_check/_browser.mjs` 가
#   실행 파일을 찾아 직접 가리키므로(`executablePath`) 레지스트리를 안 탄다. 판을
#   맞추려 들지 말 것 — 맞추기 시작하면 다음 달에 또 어긋난다.
set -euo pipefail

BUCKET="https://commondatastorage.googleapis.com/chromium-browser-snapshots"
ROOT="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"
FORCE="${1:-}"

# ⚠ **판을 물으려고 브라우저를 부르지 않는다.** 윈도우 chrome.exe 는 `--version` 으로
#   콘솔에 안 쓰고 **끝나지도 않는다** — 창까지 떠서 프로세스가 여럿 남고 이 스크립트가
#   그대로 매달린다 (실측 2026-09-02: 뒷길이 20분을 안 끝냈고 크로미움 여덟이 살아 있었다).
#   훅이 매 세션 부르는 자리라 매달림은 곧 세션 시작이 안 끝나는 것이다.
#   파일 메타데이터로 묻는다 — 안 띄우고도 판은 알 수 있다.
say_version() {
  case "$PLATFORM" in
    Win_x64) powershell.exe -NoProfile -Command                "(Get-Item -LiteralPath '$(cygpath -w "$1")').VersionInfo.ProductVersion"                2>/dev/null | tr -d '
' | head -1 ;;
    *)       "$1" --version 2>/dev/null | head -1 ;;
  esac
}


case "$(uname -s)" in
  Linux)  PLATFORM="Linux_x64"; INNER="chrome-linux/chrome" ;;
  Darwin) PLATFORM="Mac";       INNER="chrome-mac/Chromium.app/Contents/MacOS/Chromium" ;;
  *)      PLATFORM="Win_x64";   INNER="chrome-win/chrome.exe" ;;
esac

# 이미 서 있나 — 이름만 보고 찾는다. **판 번호를 안 읽으므로** 무엇이 깔려 있든 걸린다.
found=""
if [ -d "$ROOT" ]; then
  found="$(find "$ROOT" -maxdepth 4 \
    \( -name chrome -o -name chromium -o -name headless_shell -o -name chrome-headless-shell \) \
    -type f -perm -u+x 2>/dev/null | head -1 || true)"
fi

# ⚠ **「있나」를 제 자리에서만 물으면 안 된다.** playwright 가 제 CDN 에서 이미 받아 둔
#   자리는 위 ROOT 가 아니다(윈도우는 `%LOCALAPPDATA%/ms-playwright`). 그것을 안 보면
#   브라우저가 멀쩡히 있는 기계에서도 매 세션 수백 MB 를 다시 받으려 들고, 그 시도가
#   막힌 자리에서는 **고칠 것이 없는 경고가 매 세션 선다** — 실측 2026-09-02(회사 VDI):
#   playwright 가 703MB 를 이미 들고 있는데 뒷길이 curl 로 죽어 ⚠ 가 떴다. 받을 까닭이
#   없는 실패였다.
# ⚠ **자리 이름을 여기 박지 않는다** — playwright 자신에게 묻는다. 그 자리는 판마다·OS
#   마다 갈리고, 박으면 이 파일이 그때부터 낡는다 (`판 번호를 안 박는다`와 같은 결).
# ⚠ **모듈을 여는 규칙을 여기 베끼지 않는다 — `_check/_browser.mjs` 를 부른다.** `PW` 는
#   폴더로도 온다(훅이 그렇게 세운다). ESM 의 `import()` 는 폴더와 윈도우 경로를 거절하므로
#   맨 이름으로 열면 그 자리에서 죽는데, 그 죽음이 아래 `2>/dev/null` 밑에서 **「브라우저가
#   없다」로 읽힌다** — 멀쩡한 브라우저를 두고 수백 MB 를 받으러 가는 길이다. 경로를 모듈
#   주소로 푸는 자는 저쪽 `moduleSpec` 하나이고(#337), 여기는 그것을 **가리킨다.**
_probe="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)/_check/_browser.mjs"
if [ -z "$found" ] && [ -f "$_probe" ] && command -v node >/dev/null 2>&1; then
  _pw="$(node --input-type=module -e "$(cat <<'JS'
const { pathToFileURL } = await import("node:url");
const { chromium } = await import(pathToFileURL(process.argv[1]).href);
try { const p = chromium.executablePath(); if (p) console.log(p); } catch {}
JS
)" "$_probe" 2>/dev/null || true)"
  if [ -n "$_pw" ] && [ -f "$_pw" ]; then
    echo "[browser] playwright 가 이미 들고 있다 — $_pw"
    exit 0
  fi
fi

if [ -n "$found" ] && [ "$FORCE" != "--force" ]; then
  echo "[browser] 이미 있다 — $found"
  say_version "$found" || true
  exit 0
fi

command -v curl >/dev/null || { echo "[browser] curl 이 없다" >&2; exit 1; }
# ⚠ **폐기 검사가 못 서면 schannel 은 연결 자체를 접는다.** 사내망은 CRL·OCSP 응답기가
#   막혀 있어 `curl: (35) … CRYPT_E_NO_REVOCATION_CHECK (0x80092012)` 로 죽는다 — 호스트가
#   막힌 것이 아니라 **폐기 여부를 물을 데가 없는 것**이다 (실측 2026-09-02, 회사 VDI:
#   같은 옵션으로 구글 버킷도 playwright CDN 도 그 자리에서 TLS 가 풀렸다).
#   `--ssl-no-revoke`(검사를 끈다)가 아니라 **못 물었을 때만 넘어가는** best-effort 를 쓴다 —
#   응답기가 살아 있는 자리에서는 폐기된 인증서가 그대로 걸린다.
# ⚠ 이 깃발은 **schannel 빌드에만 있다.** 빌드에 물어보고 붙인다 — 리눅스 curl(OpenSSL)에
#   그냥 붙이면 알 수 없는 옵션으로 죽어, 지금 도는 자리를 이 고침이 깨뜨린다.
TLS_OPT=""
if curl --version 2>/dev/null | grep -qi schannel; then
  TLS_OPT="--ssl-revoke-best-effort"
fi


command -v unzip >/dev/null || { echo "[browser] unzip 이 없다" >&2; exit 1; }

rev="$(curl -sSfL $TLS_OPT --max-time 60 "$BUCKET/$PLATFORM/LAST_CHANGE")"
[ -n "$rev" ] || { echo "[browser] 최신 판 번호를 못 받았다" >&2; exit 1; }
echo "[browser] 최신 $rev 을 받는다 ($PLATFORM)"

dest="$ROOT/chromium-snapshot-$rev"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

curl -sSfL $TLS_OPT --retry 3 --max-time 600 -o "$tmp/browser.zip" \
  "$BUCKET/$PLATFORM/$rev/${INNER%%/*}.zip"
mkdir -p "$dest"
unzip -q -o "$tmp/browser.zip" -d "$dest"

exe="$dest/$INNER"
[ -x "$exe" ] || { echo "[browser] 푼 자리에 실행 파일이 없다 — $exe" >&2; exit 1; }

# 지름길 링크 — `_browser.mjs` 의 찾기가 얕은 곳부터 훑으므로 여기 걸리면 제일 먼저 잡힌다
# ⚠ **윈도우에서는 안 만든다.** Git Bash 는 심링크 권한이 없으면 **복사로 내려앉는데**,
#   chrome.exe 를 제 폴더 밖으로 복사하면 옆에 있어야 할 DLL 이 없어 **안 도는 파일**이
#   된다. 그리고 찾기가 얕은 곳부터 훑으므로 그 못 도는 것이 **제일 먼저 걸린다** —
#   실측 2026-09-02: `spawn …/chromium ENOENT` 로 launch 가 죽었다. 지름길이 없으면
#   찾기는 한 칸 더 들어가면 되고, 못 찾으면 playwright 기본값으로 물러난다(0175 의 ④).
if [ "$PLATFORM" != Win_x64 ]; then
  ln -sfn "$exe" "$ROOT/chromium" 2>/dev/null || true
fi

echo "[browser] 받았다 — $exe"
say_version "$exe" || true
