#!/bin/bash
# 세션 시작 훅 — 익명 몸통 (SessionStart 훅 겸 설치기)
#
# 진본은 claude-config/.claude/hooks/session-start.sh 다. 각 저장소의 것은 deploy.ps1 이
# 뿌린 배포본이다 — 배포본을 고치면 다음 배포에 덮인다.
#
# **이 파일은 프로젝트 이름도 도구 이름도 모른다.** 목록의 진본은 선언 둘이다:
#   .claude/tools.global.conf   전역 도구 — 전역 스킬이 부르는 것 (claude-config 진본의 배포본)
#   .claude/tools.conf          이 저장소의 도구 — 저장소가 커밋한다
# 도구가 늘면 선언에 블록을 더한다. 이 파일을 고치는 것은 새 설치법·새 프로브 갈래가
# 필요할 때뿐이다 (claude-config 0004).
#
#   session-start.sh            리모트면 깐다. PC 면 당겨 오고(ff-only·main 만) 홈 규범을
#                               새로 민 뒤, 선언 지문이 어긋날 때만 깐다 (claude-config 0009)
#   session-start.sh --install  기계를 안 가리고 깐다        ← deploy.ps1 이 이걸로 부른다
#                               PC 에서 밖(설치기 · 사람)이 부르면 사람에게 딸린 것(git 신원 ·
#                               형제 저장소 · 개인 키 · 홈 개인 설정)을 세우고 deploy.ps1 에 넘긴다
#                               deploy.ps1 이 부른 자리(CLAUDE_CONFIG_DEPLOYING)에서는 **저장소
#                               몫만** 든다 — 전역형 도구는 아래 갈래가 이미 깔았다
#   session-start.sh --install-global
#                               **전역형 도구를 기계에 한 번 깐다** (#43) ← deploy.ps1 이 저장소
#                               고리 **앞에** 한 번 부른다. 전역 선언과 작업 루트에 붙은 모든
#                               저장소의 전역형 선언을 이름으로 합쳐 같은 이름을 한 번만 깐다.
#                               브라우저 뒷길도 여기서 한 번. 저장소 것(venv · npm ci · 배선)은 안 든다
#                               ⚠ 위 둘(--install · --install-global)은 찍는 줄을 ~/.claude/logs/
#                               session-start-<날짜>.log 에도 남긴다 — 걸음마다 (n초) 가 붙는다 (#48)
#   session-start.sh --check    안 깔고 진단만 낸다          ← 어디서 돌려도 안전
#   session-start.sh --needs-install
#                               **「깔 게 있나」에 예/아니오만 낸다** (#47 ②) ← deploy.ps1 의
#                               계획 단계가 이걸로 묻는다. 파일만 보고 1초 안에 끝난다 —
#                               프로브도 망도 안 탄다. 0 안 깐다 · 1 깐다 · 2 못 쟀다
#
# ⚠ 진짜 문제는 **부재가 통과로 읽히는 것**이다. 게이트는 도구가 없으면 그 검사만 건너뛰고
#   통과시킨다. 아래 §진단이 그 자리를 메운다 — 판정 문구는 거기 한 자리에만 둔다.
# ⚠ **깔린 것과 닿는 것은 다른 명제다.** 프로브는 전부 실행형이다 — 파일 존재로 물으면
#   ✅ 가 거짓말을 한다 (실측 2026-08-14 · 2026-08-16).
# ⚠ **말은 stdout 으로 낸다.** SessionStart 훅에서 모델의 문맥에 들어가는 것은 stdout 뿐이고
#   stderr 는 기록에만 남는다 — 아무도 안 읽는 경고는 부재와 같다. 세션이 읽어야 할 줄에
#   `>&2` 를 붙이지 않는다 (겪은 자리는 아래 침묵 갈래 주석이 든다).
# 순서가 값을 한다 — 가볍고 안 죽는 것(복사·git config)을 앞에, 네트워크 타는 것을 뒤에.
#   설치는 저마다 실패를 삼키되 사유는 남긴다(try) — 반쯤 깔린 채 침묵하지 않기 위해서다.
set -uo pipefail

MODE=auto
ASKED=""   # 인자로 명시된 갈래 — auto 가 지문 어긋남으로 install 이 되는 것과 가른다
case "${1:-}" in
  --check)          MODE=check ;;
  --needs-install)  MODE=needs-install ;;
  --install)        MODE=install; ASKED=install ;;
  --install-global) MODE=install; ASKED=install-global ;;
esac

# ── 어느 저장소를 깔고 있나 — **제 자리에서 역산하는 것이 먼저다.**
#    CLAUDE_PROJECT_DIR 은 저장소가 아니라 **세션 루트**다. 저장소를 둘 붙이면 루트가 한 칸
#    위로 올라가(0010) 이 값이 홈을 가리키고, 여기서 파생되는 선언 넷·venv·지문이 통째로
#    엉뚱한 자리를 본다. 그러면 훅은 아무것도 못 찾은 채 **빈 지문에 「완료」 도장을 찍고**
#    (빈 문자열의 sha256), 배선도 venv 가드에 걸려 조용히 걷힌다 — 성공으로 보고되는 무작동이다.
#    (실측 2026-08-25: 진단 머리줄의 PROJECT_NAME 이 저장소 이름 대신 홈 폴더 이름으로 찍혔다.)
#    이 스크립트는 정의상 <저장소>/.claude/hooks/ 에 산다 — 제 경로가 곧 저장소다.
#    ⚠ 꼴을 확인하고 쓴다. 그 꼴이 아닐 때만(파이프로 먹였다든지) 환경변수로 물러선다.
_self="${BASH_SOURCE[0]:-$0}"
PROJECT_DIR=""
case "$_self" in
  */.claude/hooks/*) PROJECT_DIR="$(cd "$(dirname "$_self")/../.." 2>/dev/null && pwd)" ;;
esac
[ -n "$PROJECT_DIR" ] || PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
PROJECT_NAME="$(basename "$PROJECT_DIR")"   # 진단 머리줄·profile.d 파일명이 여기서 파생된다
# ── `--install` · `--install-global` 은 찍는 줄을 파일에도 남긴다 (#48 ③) ─────────────
#    설치 화면이 닫히면 화면의 줄은 사라지고, 화면을 못 본 사람은 물을 물건이 없다 — 걸음마다
#    붙는 `(n초)` 도 이 파일에서 읽는다. 세션마다 도는 auto 갈래는 안 쓴다(매 세션 파일이 는다).
#    ⚠ **바깥 하나만 받는다.** PC 의 `--install` 은 deploy.ps1 을 부르고 그것이 저장소마다 이 훅을
#      다시 `--install` 로 부른다 — 바깥이 받고 있으면 안쪽 줄은 그 파이프로 흘러 같은 줄이 두 번
#      안 적힌다. 파일 이름(SESSION_LOG)이 환경에 서 있는 것이 「바깥이 받고 있다」는 표식이다.
#    ⚠ stderr 도 같이 받는다 — pip·npm 이 죽은 까닭이 그쪽으로 나온다. 그래서 위층(PowerShell)
#      에는 stderr 가 아예 안 가고, 5.1 이 그것을 오류로 승격하는 자리(deploy.ps1 곁말)도 안 밟는다.
#    ⚠ 제 경로를 못 잡은 세션(파이프로 먹인)은 다시 못 띄우므로 안 남긴다.
if [ -n "$ASKED" ] && [ -z "${SESSION_LOG:-}" ] && [ -f "$_self" ] && mkdir -p "$HOME/.claude/logs" 2>/dev/null; then
  SESSION_LOG="$HOME/.claude/logs/session-start-$(date +%Y%m%d).log"; export SESSION_LOG
  printf '── %s  %s  --%s  %s ──\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$PROJECT_NAME" "$ASKED" "$PROJECT_DIR" >> "$SESSION_LOG"
  bash "$_self" "$@" 2>&1 | tee -a "$SESSION_LOG"
  _lrc=$?   # pipefail — tee 가 아니라 훅의 종료코드다. 위층(deploy.ps1)이 이 값을 판정으로 받는다
  exit "$_lrc"
fi
VENV="$PROJECT_DIR/.venv"
FAILS="$PROJECT_DIR/.claude/install-fail"
# 전역 갈래의 실패는 **기계 한 자리**에 적는다 (#43). 저장소 파일에 적으면 그 저장소를 여는
# 세션만 사유를 보고, 같은 도구가 꺼진 형제의 진단에는 ❌ 만 서고 까닭이 영영 안 붙는다.
GFAILS="$HOME/.claude/install-global-fail"
GCONF="$PROJECT_DIR/.claude/tools.global.conf"
PCONF="$PROJECT_DIR/.claude/tools.conf"
STAMP="$PROJECT_DIR/.claude/install-stamp"   # 기계 상태 — install-fail 과 같은 자리, 커밋 안 한다
GSTAMP="$HOME/.claude/install-global-stamp"  # 전역형 선언의 지문 — 저장소가 아니라 기계 하나다 (#43)
# 전역 걸음이 **이번 실행에서** ✅ 로 낸 도구들의 명부 (#57). 쓰는 자는 `install_global`,
# 읽는 자는 아래 진단의 `global_verified` — 둘 다 이 한 자리를 가리킨다.
GVERIFIED="$HOME/.claude/install-global-verified"
FRESH="$PROJECT_DIR/.claude/install-upgraded"  # 마지막으로 도구를 최신으로 민 날. 같은 자리, 커밋 안 한다
UPGRADE_DAYS=7                                   # 그 뒤로 이만큼 지나면 한 번 민다

# ── 옛 이름에서 옮긴다 (2026-09-16) ─────────────────────────────────────────────
#    상태 파일이 `bootstrap-*` 에서 `install-*` 로 바뀌었다 (#56 · 걷힌 몸통의 이름이었다).
#    **이름만 갈면 이미 깐 기계의 도장이 통째로 사라진다** — 지문이 안 맞아 저장소마다 한 번
#    씩 다시 깐다(사내 VDI 실측 370초). 그래서 옛 이름이 있고 새 이름이 없을 때만 옮긴다:
#    `[ -e ]` 는 내장이라 스폰이 없고, `mv` 는 옛 파일을 든 기계에서 한 번만 돈다.
#    새 이름이 이미 서 있으면 **안 덮는다** — 지금 값이 옛 값보다 새 것이다.
#  ⚠ **걷는 날은 사람이 정한다.** 모든 기계가 한 번씩 이 줄을 밟았는지는 여기서 알 길이
#    없다 — 옛 이름이 어디에도 안 남았다고 사람이 판정하는 날 이 칸을 통째로 지운다.
_migrate_name() {   # $1 옛 이름 · $2 새 이름
  [ -e "$1" ] || return 0
  [ -e "$2" ] || mv "$1" "$2"
}
_migrate_name "$PROJECT_DIR/.claude/bootstrap-fail"          "$FAILS"
_migrate_name "$PROJECT_DIR/.claude/bootstrap-stamp"         "$STAMP"
_migrate_name "$PROJECT_DIR/.claude/bootstrap-upgraded"      "$FRESH"
_migrate_name "$HOME/.claude/bootstrap-global-fail"          "$GFAILS"
_migrate_name "$HOME/.claude/bootstrap-global-stamp"         "$GSTAMP"
unset -f _migrate_name

# ⚠ 선언이 하나도 없으면 **깔 것을 못 찾은 것**이다. 빈 지문은 「선언이 없다」와 「자리를 잘못
#   봤다」를 구별하지 못해, 엉뚱한 자리에서도 완료 도장이 찍힌다 — 그 침묵이 무작동을 성공으로
#   보이게 한다. 막지는 않고 자리를 말하고 간다(선언 없는 저장소도 정당하기 때문이다).
# ⚠ `--needs-install` 은 이 줄을 안 낸다 — 그 갈래의 답은 **기계가 읽는 한 줄**이라 다른 줄이
#   섞이면 사유가 밀린다. 이 말이 필요한 사람은 세션(auto)·설치 화면에서 그대로 듣는다.
[ "$MODE" = needs-install ] ||
[ -e "$PROJECT_DIR/requirements.txt" ] || [ -e "$PROJECT_DIR/package-lock.json" ] ||
[ -e "$GCONF" ] || [ -e "$PCONF" ] ||
  echo "$PROJECT_NAME: ⚠ 선언이 하나도 없다(requirements.txt · package-lock.json · tools*.conf) — $PROJECT_DIR 를 저장소로 보고 있다. 자리가 맞나 본다."

# ── 선언 지문 — 설치가 소비하는 선언 넷의 해시. 깨끗한 설치 끝에 굳고(⑧), PC 세션이
#    「깔 것이 있나」를 이 값과 대조한다(auto). 판정이 사건(풀이 있었나)이 아니라
#    상태(선언과 설치가 같은 세대인가) 위에 선다. 값은 기계 밖으로 안 나가 줄끝을 안 탄다.
#    ⚠ **이것은 저장소 몫의 지문이다.** 전역형 도구는 기계 하나에 서므로 지문도 하나다 —
#      그 짝은 아래 `global_fingerprint` 이고, 게이트도 둘로 갈린다 (#43).
decl_fingerprint() {
  cat "$PROJECT_DIR/requirements.txt" "$PROJECT_DIR/package-lock.json" \
      "$GCONF" "$PCONF" 2>/dev/null | sha256sum | awk '{print $1}'
}

# claude-config 가 어디 붙었나 — 커밋 게이트와 같은 자리(.githooks 의 경로 스크립트)를 본다.
# 그 스크립트가 없는 저장소는 아래서 직접 짚는다.
CONFIG_ROOT=""; ADR_GEN=""
[ -f "$PROJECT_DIR/.githooks/claude-config-path.sh" ] &&
  . "$PROJECT_DIR/.githooks/claude-config-path.sh"
if [ -z "$CONFIG_ROOT" ]; then
  for _c in "$PROJECT_DIR" "$(dirname "$PROJECT_DIR")/claude-config" "$HOME/claude-config" /workspace/claude-config; do
    [ -f "$_c/deploy.ps1" ] && [ -d "$_c/memory" ] && { CONFIG_ROOT="$_c"; break; }
  done
fi

# 기계를 가른다. Git Bash 는 `uname -s` 가 MINGW64_NT-… 를 낸다.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) OS=windows ;;
  *)                    OS=linux   ;;
esac
# ⚠ **파이썬의 stdio·open() 인코딩을 기계의 로케일에 안 맡긴다** (#51 · PEP 540). 아래 파이썬 셋
#   (홈 설정 병합 · 홈 훅·신뢰 심기 · 심겼나 재기)은 한국어 문구를 파이프로 내는데, 윈도우의 기본
#   인코딩(cp949)은 `—` 를 못 담아 **다 쓰고 나서 찍다가 죽는다.** deploy 가 심는 사용자 환경변수
#   (PYTHONUTF8)는 비영속 VDI 의 첫 로그인과 리모트에는 없다 — 훅이 어디서 돌든 이 한 줄이 덮는다.
export PYTHONUTF8=1
if [ "$OS" = windows ]; then
  VENV_BIN="$VENV/Scripts"; PY_CMD=python
else
  VENV_BIN="$VENV/bin";     PY_CMD=python3
fi

# ── 파일로 재는 자 둘 — **배선이 섰나 · venv 가 닿나** ─────────────────────────────────
#    아래 `--needs-install` 과 이 파일 끝의 진단이 같은 것을 묻는다. 자를 두 벌 두면 한쪽만
#    고쳐져 같은 저장소를 놓고 두 자리가 다르게 말한다 — 그래서 자는 하나다.
#    ⚠ 둘 다 **읽기만 한다.** 재는 갈래가 상태를 바꾸면 판정이 늘 초록이 된다
#      (`--check` 가 `wire_commit_hooks` 를 안 부르는 것과 같은 규율).
#    ⚠ 자리가 여기인 까닭 — 아래 `py_resolve` 는 파이썬을 **한 번 띄운다.** `--needs-install`
#      은 프로브를 안 문 갈래라 그 앞에 서야 하고, 그러려면 자도 그 앞에 서 있어야 한다.
hooks_wired() {  # 0 이면 이 저장소의 .githooks 로 배선돼 있다. 걸린 글자는 HOOKS_PATH 가 든다
  HOOKS_PATH="$(git -C "$PROJECT_DIR" config core.hooksPath 2>/dev/null)"
  [ -d "$PROJECT_DIR/.githooks" ] || return 1
  # ⚠ 글자 일치가 아니라 **자리 일치**다 — 절대경로(`C:/…/.githooks`)로 걸어 둔 저장소도 같은
  #   폴더를 가리키면 배선된 것이다. 옛 판은 `.githooks` 글자만 받아 그 저장소를 ❌ 로 찍었다.
  case "$HOOKS_PATH" in
    .githooks|./.githooks) return 0 ;;
    "") return 1 ;;
    *) _hw_here="$(cd "$PROJECT_DIR" 2>/dev/null && cd "$HOOKS_PATH" 2>/dev/null && pwd -P)"
       _hw_want="$(cd "$PROJECT_DIR/.githooks" && pwd -P)"
       [ -n "$_hw_here" ] && [ "$_hw_here" = "$_hw_want" ] ;;
  esac
}
# ⚠ venv 는 **폴더가 서 있나가 아니라 pip 이 닿나**로 잰다. `python -m venv` 는 트리를 만들고
#   해석기를 복사한 **뒤에** pip 을 깐다. 그 마지막 걸음만 져도 폴더는 그대로 남아, 존재로
#   물으면 반쯤 선 venv 가 「있다」로 읽힌다 — 그러면 **다시 깔아도 영영 안 낫는다**: 만들기를
#   건너뛰고, pip 이 없으니 의존성 칸도 조용히 지나가고, 실패는 한 줄도 안 남는다 (실측
#   2026-09-10 · VDI 넷이 다 그랬다). 이 파일 머릿말의 「깔린 것과 닿는 것은 다른 명제다」가
#   정작 제 venv 가드에만 안 걸려 있었다.
venv_ready() { [ -x "$VENV_BIN/pip" ] || [ -f "$VENV_BIN/pip.exe" ]; }

# ── `--needs-install` — 「이 저장소에 깔 게 있나」 **예/아니오 하나** (#47 ②) ──────────────
#    묻는 자는 `deploy.ps1` 의 계획 단계다. 거기 필요한 답은 진단이 아니라 이 한 마디인데,
#    옛 판은 `--check` 를 불러 도구마다 프로브를 띄웠다 — 사내 VDI 실측(PAISetup #5): 저장소당
#    31~57초 × 다섯 = 200초가, 설치 끝의 진단과 **같은 판정을 두 벌** 내는 데 들었다.
#    그래서 여기는 **파일만 본다** — 프로브도 망도 CI 조회도 없다. 「도구가 닿나」는 안 묻는다:
#    그 물음의 자리는 깐 뒤의 진단 한 벌이다(설치가 끝난 자리의 판정이라야 진짜다).
#  ⚠ **판정의 진본을 새로 짓지 않는다.** 「깔 게 있다」가 무엇인가는 auto 갈래의 지문 게이트가
#    이미 든 명제고, 여기는 같은 자(`decl_fingerprint`)를 그대로 부른다. 그 위에 더하는 것은
#    **설치가 세우는 것 중 파일로 보이는 것**뿐이다 — 배선(`wire_commit_hooks` 가 세운다) ·
#    venv(파이썬 선언이 있을 때) · 지난 설치가 남긴 실패(다시 까는 손은 여기라고 auto 가 적어 뒀다).
#  ⚠ **아무것도 안 쓴다 — 지문 도장(STAMP)도 안 찍는다.** 재는 갈래가 제 자국을 남기면 다음
#    판정이 그것을 읽는다.
#  ⚠ 종료코드 셋 — 0 안 깐다 · 1 깐다 · **2 못 쟀다**. 2 를 0 으로 접지 않는다: 부재가 통과로
#    읽히는 자리가 거기다. 사유는 stdout 한 줄이고, 위층이 그 줄을 그대로 화면에 싣는다.
if [ "$MODE" = needs-install ]; then
  _nfp="$(decl_fingerprint)"
  if [ -z "$_nfp" ]; then
    echo "선언 지문을 못 쟀다 — sha256sum 을 못 부른다"; exit 2
  fi
  if [ -d "$PROJECT_DIR/.githooks" ] && ! hooks_wired; then
    # 「안 걸렸다」와 「못 물었다」를 가른다 — git 이 이 자리를 저장소로 안 읽으면 배선은 1 이
    # 아니라 2 다. 성한 자리에서는 이 한 번을 안 묻는다(위가 이미 답했다) — 왕복 하나가 값이다.
    git -C "$PROJECT_DIR" rev-parse --git-dir >/dev/null 2>&1 ||
      { echo "배선을 못 쟀다 — git 이 $PROJECT_DIR 를 저장소로 안 읽는다"; exit 2; }
    echo "커밋 훅 배선이 없다 (core.hooksPath=${HOOKS_PATH:-빈 값})"; exit 1
  fi
  [ "$_nfp" = "$(cat "$STAMP" 2>/dev/null)" ] ||
    { echo "선언 지문이 어긋난다 — 선언이 바뀌었거나 아직 안 깔렸다"; exit 1; }
  if [ -f "$PROJECT_DIR/requirements.txt" ] && ! venv_ready; then
    echo "venv 에 pip 이 안 닿는다 — 파이썬 선언이 있는데 .venv 가 없거나 반쯤 섰다"; exit 1
  fi
  # 지난 실패는 설치가 제 층을 다시 돌 때만 걷힌다 — 남아 있다는 것은 **마지막 설치가 졌다**는 뜻이다.
  # 전역 쪽도 같이 본다: 전역형 도구가 못 깔린 저장소는 그 사유를 제 파일에 안 진다 (#43).
  for _nff in "$FAILS" "$GFAILS"; do
    [ -s "$_nff" ] || continue
    _nwho=저장소; [ "$_nff" = "$GFAILS" ] && _nwho=전역
    echo "지난 $_nwho 설치의 실패가 남아 있다 — $(awk -F'\t' '{printf "%s%s", (NR>1 ? " · " : ""), $1}' "$_nff" 2>/dev/null)"
    exit 1
  done
  echo "배선·지문 맞음"
  exit 0
fi
# ⚠ **윈도우의 `python` 이름은 스토어 껍데기일 수 있다** (#50). PATH 앞의 `WindowsApps\python.exe` 는
#   진짜 파이썬이 아니라 스토어를 여는 자리표라 비대화에서 진다 — 설치기가 같은 실행에서 파이썬을
#   막 깔았어도 이 셸의 PATH 는 그 전 것이라 껍데기가 먼저 걸린다. 그래서 이름을 믿지 않고
#   **한 번 불러 보고** 진짜를 고른다: 이름 → `py -3` 런처(python.org·winget 설치가 등록한다) →
#   winget/python.org 가 두는 자리. 셋 다 지면 이름을 그대로 둔다 — 심는 자리가 그때 사유를 댄다.
#   auto 갈래마다 파이썬 하나가 잠깐 뜬다 — 심는 자리가 어차피 띄우는 그 하나다.
py_resolve() {
  "$PY_CMD" -c '' >/dev/null 2>&1 && return 0
  [ "$OS" = windows ] || return 0
  if command -v py >/dev/null 2>&1 && py -3 -c '' >/dev/null 2>&1; then
    _pf="$(py -3 -c 'import sys; print(sys.executable)' 2>/dev/null)"
    [ -n "$_pf" ] && [ -x "$_pf" ] && { PY_CMD="$_pf"; return 0; }
  fi
  for _pf in "$LOCALAPPDATA"/Programs/Python/Python3*/python.exe; do
    [ -x "$_pf" ] && "$_pf" -c '' >/dev/null 2>&1 && { PY_CMD="$_pf"; return 0; }
  done
  return 0
}
py_resolve
VENV_PY="$VENV_BIN/python"; [ -x "$VENV_PY" ] || VENV_PY="$VENV_BIN/python.exe"
NPM_BIN="$PROJECT_DIR/node_modules/.bin"

# ── 파이썬 판 자 — 선언(probe = python-version)이 바닥을 들면 이 자로 잰다 ──
py_num() {  # py_num <해석기> — 3.13 → 313. 못 부르면 빈 값
  "$1" -c 'import sys; print(sys.version_info[0] * 100 + sys.version_info[1])' 2>/dev/null
}
ver_num() {  # ver_num <"3.12"> — 선언의 바닥 문자열을 같은 자로. 모양이 아니면 0
  case "$1" in
    *.*) _ma="${1%%.*}"; _mi="${1#*.}"; _mi="${_mi%%.*}"
         case "$_ma$_mi" in ''|*[!0-9]*) echo 0 ;; *) echo $(( _ma * 100 + _mi )) ;; esac ;;
    *) echo 0 ;;
  esac
}

# ── 선언 파서 — sh 순정. [절] + KEY = VALUE, '#' 주석, \r 방어(CRLF 체크아웃 대비) ──
decl_sections() {
  [ -f "$1" ] || return 0
  # CRLF 정리는 awk 안에서 같이 한다 — 선언 하나를 읽을 때 sed 프로세스를 따로 띄우지 않는다.
  awk '{
         sub(/\r$/, "", $0)
         if ($0 ~ /^\[[^]]+\][[:space:]]*$/) {
           line = $0
           gsub(/[][]/, "", line)
           gsub(/[[:space:]]+$/, "", line)
           print line
         }
       }' "$1"
}
decl_get() {  # decl_get <파일> <절> <키>
  [ -f "$1" ] || return 0
  awk -v sec="$2" -v key="$3" '
    {
      line = $0
      sub(/\r$/, "", line)
    }
    line ~ /^\[/ { s = line; gsub(/[][]/, "", s); gsub(/[[:space:]]+$/, "", s); insec = (s == sec); next }
    insec {
      sub(/[[:space:]]*#.*$/, "", line)
      if (line ~ "^"key"[[:space:]]*=") {
        sub(/^[^=]*=[[:space:]]*/, "", line); sub(/[[:space:]]+$/, "", line)
        print line; exit
      }
    }' "$1"
}

# ── 프로브 — 유한 4갈래, 전부 실행형. 새 갈래가 필요할 때만 이 함수가 는다 ──
# ⚠ npx --yes 는 갈래가 아니다 — 설치법과 도달 판정을 섞어 제3의 상태를 만든다 (0004).
# 실행 갈래의 인자는 기본 --version 이되 선언의 probe-arg 가 덮는다 — 인자를 받고도
# 멈추지 않는 도구가 실재한다(실측 2026-08-16: --version 을 받고 저장소 전체를 린트).
probe_tool() {  # probe_tool <갈래> <대상> [인자…]
  _k="$1"; _tg="$2"; shift 2
  [ $# -gt 0 ] || set -- --version
  case "$_k" in
    exec-on-path)      command -v "$_tg" >/dev/null 2>&1 && "$_tg" "$@" >/dev/null 2>&1 ;;
    exec-npm-bin)      [ -e "$NPM_BIN/$_tg" ] && "$NPM_BIN/$_tg" "$@" >/dev/null 2>&1 ;;
    node-resolvable)   ( cd "$PROJECT_DIR" && node --input-type=module -e "await import('$_tg')" ) >/dev/null 2>&1 ;;
    python-importable) if [ -x "$VENV_PY" ]; then "$VENV_PY" -c "import $_tg" >/dev/null 2>&1
                       else command -v "$PY_CMD" >/dev/null 2>&1 && "$PY_CMD" -c "import $_tg" >/dev/null 2>&1; fi ;;
    python-version)    # 「깔렸나」가 아니라 「선언한 판(probe-target)과 같나」 — venv 가
                       # 서 있으면 그 판을, 아니면 venv 를 만들 판(PY_CMD)을 잰다 (판 일치)
                       if [ -x "$VENV_PY" ]; then _pv="$(py_num "$VENV_PY")"
                       else _pv="$(py_num "$PY_CMD")"; fi
                       [ -n "$_pv" ] && [ "$_pv" -eq "$(ver_num "$_tg")" ] ;;
    *) return 1 ;;
  esac
}
# npm 전역에 깔린 판 — **기계에게 묻는다.** `--version` 출력을 파싱하지 않는다: 문구가
# 도구마다 달라, 그 차이를 표로 들면 그 표가 곧 매핑 레이어다(규범 [Determinism First]).
# 패키지의 package.json 이 제 판의 진본이고 그것을 읽는 자는 node 다 — npm 이 있으면 있다.
# ⚠ **경로를 JS 소스에 박지 않는다 — 인자로 넘긴다.** 윈도우의 `npm root -g` 는
#   `C:\Users\…\node_modules` 를 내는데, 그 문자열을 따옴표 사이에 그대로 넣으면 **역슬래시가
#   이스케이프로 읽힌다** — `\n` 은 줄바꿈이 되고 `\U` 는 글자가 날아간다. 그러면 경로가
#   부서져 이 함수가 늘 빈 값을 내고, **판이 정확히 깔린 기계에서도 판정이 「안 닿는다」로
#   굳는다**: 진단은 ❌, 설치는 매번 같은 패키지를 다시 깔고, 종료코드가 영영 1 이라 배포가
#   실패를 본다. 리눅스에서만 재면 이 자리는 영영 안 보인다.
npm_global_version() {  # npm_global_version <패키지 이름> — 못 읽으면 빈 값
  _nr="$(npm root -g 2>/dev/null)" || return 1
  [ -n "$_nr" ] && [ -f "$_nr/$1/package.json" ] || return 1
  node -e 'const p = require("path").join(process.argv[1], "package.json")
           console.log(require(p).version || "")' "$_nr/$1" 2>/dev/null
}

probe_reach() {  # probe_reach <선언파일> <이름> — **이 저장소에서** 닿나
  # shellcheck disable=SC2046 — probe-arg 는 낱말 분리가 의도다
  probe_tool "$(decl_get "$1" "$2" probe)" "$(decl_get "$1" "$2" probe-target)" \
    $(decl_get "$1" "$2" probe-arg)
}
probe_pin() {  # probe_pin <선언파일> <이름> — 선언이 판을 박았으면 깔린 판이 그것인가
  # ⚠ **「깔렸나」와 「선언한 판인가」는 다른 명제다.** 선언이 `이름@판` 으로 판을 박았으면
  #   여기서 그것도 잰다 — 안 재면 판을 박아도 **옛 판이 깔린 기계에서 그냥 통과하고**,
  #   선언만 정확해진 채 실물은 그대로 간다. `python-version` 갈래가 이미 같은 자를 든다.
  #   판을 안 박은 선언은 이 칸이 통째로 빠진다 — 최신을 받고 안 잰다.
  # ⚠ **자리가 갈려 나온 까닭** — 판은 npm 전역 한 자리에 서므로 **저장소를 안 탄다.** 그래서
  #   저장소 갈래(probe_decl)와 전역 갈래(probe_global)가 같은 이 몸통을 쓴다 (#43).
  [ "$(decl_get "$1" "$2" install)" = npm-global ] || return 0
  _pk="$(decl_get "$1" "$2" package)"
  # 스코프 패키지(@scope/name)는 맨 앞 `@` 가 판 구분자가 아니다 — 첫 글자 뒤의 `@` 만 문다.
  case "$_pk" in
    ?*@*) _pn="${_pk%@*}"; _pv="${_pk##*@}" ;;
    *) return 0 ;;
  esac
  [ -n "$_pn" ] && [ -n "$_pv" ] || return 0
  # ⚠ **정확한 판이 아니면 안 잰다.** 비교가 문자열 일치라 `^21.0.0`·`latest` 를 적으면 어떤
  #   판이 깔려도 다르고, 안내는 「다시 깔면 선언한 판을 받는다」인데 다시 깔아도 안 바뀐다 —
  #   영원한 ❌ 다. 재려면 semver 해석기가 필요하고 그건 매핑 레이어다(규범 [Determinism First]).
  #   안 재는 것은 `pin_mismatch` 가 진단에서 말한다.
  case "$_pv" in ''|*[!0-9.]*) return 0 ;; esac
  [ "$(npm_global_version "$_pn" || true)" = "$_pv" ]
}
probe_decl() {  # probe_decl <선언파일> <이름> — 저장소의 물음. 진단이 쓰는 자다
  probe_reach "$1" "$2" || return 1
  probe_pin   "$1" "$2"
}
# ── 전역 갈래의 물음 — **저장소가 아니라 기계에게 묻는다** (#43) ────────────────
# ⚠ **왜 딴 함수인가.** `node-resolvable` 은 「이 저장소 안에서 import 되나」라, 정션이
#   서기 **전**에 물으면 늘 진다. 전역 고리가 그 물음을 쓰면 playwright 는 매번 지고
#   `npm install -g` 가 되풀이된다 — 이슈 #43 의 ② 가 그 자리다. 전역형 도구가 사는 자리는
#   `npm root -g` 이므로 거기서 묻는다: 그 폴더 밑에서 node 를 띄우면 맨 이름이 풀린다.
# ⚠ **여전히 실행형이다** — 폴더가 있나로 안 묻는다. 「깔린 것과 닿는 것은 다른 명제」가
#   여기서도 그대로 선다(이 파일 머리말).
# ⚠ **경로를 JS 소스에 안 박는다 — cwd 로 준다.** 윈도우의 `npm root -g` 는 역슬래시
#   경로를 내므로 문자열에 끼우면 이스케이프로 읽힌다(`npm_global_version` 곁말과 같은 함정).
probe_global() {  # probe_global <선언파일> <이름>
  case "$(decl_get "$1" "$2" probe)" in
    node-resolvable)
      _gr="$(npm root -g 2>/dev/null)" || return 1
      [ -n "$_gr" ] || return 1
      ( cd "$_gr/.." 2>/dev/null &&
        node --input-type=module -e "await import('$(decl_get "$1" "$2" probe-target)')" ) >/dev/null 2>&1 || return 1 ;;
    *) probe_reach "$1" "$2" || return 1 ;;
  esac
  probe_pin "$1" "$2"
}

# ── 커밋 훅 배선 — **맨 앞이다.** `.githooks/` 를 둔 저장소만, 존재가 곧 선언이다 ───────
#    ⚠ **이 파일 머리의 순서(「가볍고 안 죽는 것을 앞에」)가 값을 하는 자리다.** 옛 판은 이
#      한 줄이 `deploy_home_norms` 꼬리에 붙어 있었는데, 그 함수는 auto 갈래에서 **망을 타는
#      당김 둘 뒤**에 선다. SessionStart 훅은 시간이 잘리므로 당김이 느린 저장소에서는 훅이
#      여기 닿기 전에 끊긴다 — 그러면 게이트가 안 걸린 채 커밋이 지나가고 **그 부재는
#      조용하다**(훅이 안 걸렸으니 안 걸렸다고 말할 자도 없다). 실측 2026-09-14: 한 번의
#      쓸기에서 형제 넷이 다 당김을 시작했는데 **작은 둘만** 배선이 섰다 (#31).
#    ⚠ 로컬 `git config` 한 줄이라 망도 디스크도 도구도 안 탄다 — **앞에 둬서 잃는 것이 없고
#      뒤에 둬서 얻는 것도 없다.** 그래서 자리가 곧 고침이다.
#    ⚠ `--check` 는 이것을 안 부른다 — 재는 갈래가 상태를 바꾸면 판정이 늘 초록이 된다.
wire_commit_hooks() {
  [ -d "$PROJECT_DIR/.githooks" ] || return 0
  git -C "$PROJECT_DIR" config core.hooksPath .githooks 2>/dev/null || true
}

# ── 홈 규범·룰·에이전트·씨앗 — 가볍고 멱등이라 설치 안(①②)만이 아니라
#    PC 매 세션(auto)에도 민다. **밀기는 견줌 뒤에 온다** — 아래 `_push_file` 이 그 게이트다.
#    **재료는 claude-config 진본 한 자리다.** 저장소는 전역 사본을 안 진다 — 지면 그 폴더가
#    「이 저장소 것」과 「전역 것」을 겸하게 되고, 겸하면 이름으로 갈라야 하는데 그 이름이
#    PC 에서는 뜻이 없다 (claude-config 0014). 안 붙어 있을 때 조용히 넘어가지 않는 것은
#    아래 진단 절의 「전역 축」이 든다 — 규율 없이 도는 세션은 스스로 그것을 모른다.
# ── 파일 하나를 미는 규율 — **이 칸의 모든 밀기가 이 문을 지난다** ────────────────
#    ⚠ **왜 게이트가 필요한가.** 리모트는 홈이 매 세션 새로 서서 이 복사가 살아야 하고, PC 는
#      `deploy.ps1` 이 이미 밀어 둬서 **같은 것을 매 세션 다시 옮겼다** — 파일마다 프로세스
#      둘(폴더 짓기 + 복사)이라 윈도우에서 마흔여덟 자리가 2.2초다 (#54). 두 자리를 가르는
#      물음은 기계가 아니라 **파일**이다: 없으면 민다 · 원본이 새것이면 민다 · 아니면 넘긴다.
#      그래서 빈 홈(리모트)에서는 전부 밀리고 이미 선 홈(PC)에서는 아무것도 안 밀린다 —
#      갈래를 안 세우고 같은 한 문으로 둘 다 든다.
#    ⚠ **내용을 안 견준다 — 자리와 때로 본다.** `cmp` 는 파일마다 프로세스라 고치려는 값을
#      도로 문다. `cp` 는 사본에 **지금 시각**을 찍으므로 다음 세션엔 사본이 새것이고, 원본이
#      당겨져 바뀌면 그때 원본이 새것이 된다 — `-nt` 로 충분하다.
#    ⚠ **덮어쓰기만 한다 — 홈에만 남은 파일은 안 지운다.** 옛 꼴의 뜻 그대로다.
_push_file() {   # _push_file <원본> <홈 사본>
  [ -f "$1" ] || return 0                       # 글롭이 안 맞으면 패턴 그대로 온다
  _pd="${2%/*}"
  [ -d "$_pd" ] || mkdir -p "$_pd" 2>/dev/null || true
  { [ -f "$2" ] && [ ! "$1" -nt "$2" ]; } && return 0
  cp "$1" "$2" 2>/dev/null || true
}
deploy_home_norms() {
  if [ -n "$CONFIG_ROOT" ] && [ -f "$CONFIG_ROOT/.claude/CLAUDE.global.md" ]; then
    _src="$CONFIG_ROOT/.claude"
    [ -d "$HOME/.claude" ] || mkdir -p "$HOME/.claude"
    _push_file "$_src/CLAUDE.global.md" "$HOME/.claude/CLAUDE.md"
    if [ -d "$_src/rules.global" ]; then
      for _hf in "$_src/rules.global/"*.md; do
        _push_file "$_hf" "$HOME/.claude/rules/${_hf##*/}"
      done
    fi
    # 에이전트 — 규범·룰과 같은 통로다. PC 는 deploy.ps1 이 이미 밀었고 리모트만 비어
    # 있었다: 붙여도 안 실렸고, 안 실린 줄도 몰랐다 (#5).
    # ⚠ **진본이 루트 `agents/` 인 것이 곧 안전장치다.** `.claude/agents/` 는 제품의 로드
    #   자리라, 거기 두면 이 저장소를 붙인 세션에서 저장소 층과 홈 층에 **두 벌** 실린다 —
    #   `0014` 가 룰에서 겪은 그 고장이다. 루트는 로드 자리가 아니라 짐칸 이름도 필요 없다.
    if [ -d "$CONFIG_ROOT/agents" ]; then
      for _hf in "$CONFIG_ROOT/agents/"*.md; do
        _push_file "$_hf" "$HOME/.claude/agents/${_hf##*/}"
      done
    fi
    # 사내 환경 문서와 씨앗 둘 — 규범·룰·에이전트와 **같은 통로에서 빠져 있던 칸**이다.
    # 진본은 이 저장소이고 스킬·형제 저장소 문서가 홈 좌표를 가리키는데, 그 홈 사본을
    # 갱신하는 자가 **사람이 부르는 deploy.ps1 뿐이었다** — 원격 당김은 매 세션 도는데
    # 홈으로 미는 손은 안 도니 커밋이 쌓이는 만큼 홈만 낡았다. 그리고 홈을 진본으로 믿는
    # 검사(`borrowed_check`)는 낡은 판을 보고 **초록을 냈다** — 부재보다 나쁘다
    # (실측 2026-09-13: 홈 씨앗이 나무와 12 자리 갈려 있었다).
    # ⚠ **무엇을 어떻게 미나의 진본은 deploy.ps1 의 「사내 환경 문서와 씨앗 둘」 절이다**
    #   (대상 셋 · `__pycache__` 제외 · `seeds/config-repo` 는 일부러 안 민다 — 몸통 없는
    #   골든이 완본처럼 서는 까닭을 거기 주석이 든다). 여기는 같은 값을 같은 뜻으로 들 뿐
    #   이고, 제외를 선언 파일로 뽑지 않는다 — 한 낱말이라 선언이 좌표만 늘린다.
    #   목록은 폴더가 든다. 파일이 늘어도 이 파일은 그대로 둔다.
    # ⚠ **덮어쓰기만 한다 — 홈에만 남은 파일은 안 지운다.** 위 룰·에이전트 칸이 그 뜻이고
    #   deploy.ps1 도 그 뜻이다(원본을 훑어 대상 목록을 짜고, 홈 쪽 고아는 안 본다).
    # ⚠ **`*.md` 한 줄로는 안 되는 까닭은 씨앗이 폴더를 진다**(`seeds/gateway/app` ·
    #   `_check/log`). 그래서 파일을 훑어 상대 경로를 지어 옮긴다 — deploy.ps1 이 같은 자리
    #   에서 `-Recurse` + 상대경로로 하는 것과 같은 셈이다.
    # ⚠ **이미 같으면 안 민다 — 문이 둘이다.** 폴더 한 벌을 `diff` 로 견주고, 넘어온 파일은
    #   위 `_push_file` 이 낱개로 다시 견준다. 폴더 문은 성한 판에서 `find` 와 고리를 통째로
    #   아끼고, 낱개 문은 폴더 문이 「다르다」를 낼 때 **정말 다른 파일만** 남긴다.
    #   파일마다 프로세스를 띄우는 셈이라(폴더 짓기 + 복사) 윈도우에서 쉰두 자리가 2.9초다.
    #   그런데 정상 상태의 홈은 **이미 같다** — 밀 것이 없는데 매 세션 3초를 물면 그 비용이
    #   곧 이 칸을 걷어내자는 말이 된다. 폴더마다 한 벌씩 견주고 같으면 넘긴다:
    #   실측 2026-09-13 (윈도우 Git Bash · 임시 홈) — 정상 0.15초 · 한 폴더가 낡으면 0.7초 ·
    #   빈 홈 첫 돌림 2.9초. 게이트 없는 판은 세 경우가 다 2.9초였다.
    #   **이것도 배포자의 뜻이다** — deploy.ps1 은 파일마다 해시를 견주어 같으면 `= 동일` 을
    #   내고 복사 계획에서 뺀다. 여기는 그 견줌을 폴더 단위로 한 벌 할 뿐이다.
    # ⚠ 홈에만 남은 파일(이름이 바뀐 씨앗의 옛 사본)이 있으면 `diff -rq` 가 그것도 「다르다」
    #   로 세어 그 폴더는 **매 세션 폴더 문을 못 지난다** — 이 PC 의 `posco` 가 그 자리다
    #   (실측 2026-09-16). 다만 그 뒤가 낱개 문이라 실제로 밀리는 파일은 없다: 느려지는 값이
    #   `find` 하나와 고리뿐이고, 복사 열여덟은 안 돈다. 산문을 읽어 「홈에만 있음」 줄만
    #   걸러내려 들지 않는다: 그 문구는 로케일이 든다.
    for _sd in seeds/gateway seeds/check posco; do
      [ -d "$CONFIG_ROOT/$_sd" ] || continue
      diff -rq -x __pycache__ "$CONFIG_ROOT/$_sd" "$HOME/.claude/$_sd" >/dev/null 2>&1 && continue
      find "$CONFIG_ROOT/$_sd" -type f 2>/dev/null | while IFS= read -r _sf; do
        case "$_sf" in */__pycache__/*) continue ;; esac
        _sr="${_sf#"$CONFIG_ROOT"/}"
        _push_file "$_sf" "$HOME/.claude/$_sr"
      done
    done
    # ── 씨앗의 판 줄 — 홈 사본이 **어느 판에서 왔나**를 그 자리에 남긴다 ────────
    # ⚠ **왜 한 줄이 더 필요한가.** 홈 사본을 진본으로 믿고 재는 자가 있다
    #   (`seeds/check/_check/borrowed_check.py` 의 `_stamp()`). 그런데 홈 뿌리는 git
    #   나무가 아니라 판을 물을 데가 없어, 옛 판은 **오늘 날짜**를 냈다 — 그래서 낡은
    #   홈과 견준 초록이 최신처럼 읽혔다 (실측 2026-09-13: 홈 씨앗이 나무와 12 자리
    #   갈려 있었다). 이 한 줄이 그 물음에 답한다. 이름은 그쪽 `VERSION_FILE` 이 들고
    #   쓰는 자는 여기와 `deploy.ps1` 의 「씨앗의 판 줄」 칸 둘이다.
    # ⚠ **자리가 위 폴더 목록 밑인 까닭** — 민 뒤에 적어야 「그 판이 깔렸다」가 참이다.
    # ⚠ **판이 그대로면 안 쓴다.** 날짜 칸은 「이 판이 홈에 깔린 날」이고 돌린 날이
    #   아니다 — 매 세션 덮으면 그 날짜가 늘 오늘이라 낡음을 아무것도 말하지 않는다.
    # ⚠ **위 `diff` 가 이것을 안 본다** — 견주는 자리가 `seeds/<이름>/` 안이고 이 줄은
    #   뿌리 `seeds/` 에 산다. 그래서 판 줄 때문에 폴더가 매 세션 다시 밀리지 않는다.
    # ⚠ **매 세션 프로세스 하나가 는다**(`git rev-parse`). 실측 2026-09-14 · 같은 임시 홈
    #   에서 옛 몸통과 A/B — 정상 0.33초 → 0.42초(빈 홈 첫 돌림은 3.2초 그대로). 판 줄이
    #   없으면 홈이 어느 판인지 **물을 데가 아예 없다** — 그 값에 이 0.09초를 문다.
    _sv="$(git -C "$CONFIG_ROOT" rev-parse --short HEAD 2>/dev/null || true)"
    if [ -n "$_sv" ] && [ -d "$HOME/.claude/seeds" ]; then
      _svf="$HOME/.claude/seeds/.version"
      [ "$(awk 'NR==1{print $1}' "$_svf" 2>/dev/null)" = "$_sv" ] ||
        printf '%s %s\n' "$_sv" "$(date +%Y-%m-%d)" > "$_svf" 2>/dev/null || true
    fi
  fi
}

# ── 사람에게 딸린 것 — git 신원 · 형제 저장소 · 슬러그 폴더 · 개인 키 · 홈 개인 설정 ──────
#    **PC 에서만, 그리고 전역 저장소가 `personal.conf` 를 들 때만.** 리모트는 저장소를 claude.ai 가
#    붙이고 키를 환경이 들어 이 칸이 통째로 조용히 지나간다.
#    옛 판은 이것이 `bootstrap-vdi.sh` 라는 딴 몸통에 살았다 — 설치기(`install.ps1`)가 `#config-repo`
#    로 받은 저장소 뿌리에서 그 이름을 찾아 불렀고, 그 몸통이 회사 키·프록시·Codex/Gemini 설정까지
#    들어 설치기와 일이 갈렸다(그 판에서는 확장·CLI 를 아무도 안 깔았다 · 실측 2026-09-14 · 사내 VDI).
#    이제 회사 것은 설치기가 자리만 보고 전부 세우고, **사람에게 딸린 것만 이 훅이 든다** — Claude Code
#    가 규격으로 보장하는 자리는 훅뿐이라, 리모트 Setup script 와 설치기가 같은 한 줄(`--install`)로 선다.
#    ⚠ **몸통은 이름을 모른다.** 값은 전역 저장소의 `personal.conf`(git 신원 · 저장소 · 주소 꼴 · 자리)와
#      `secrets.env`(개인 키)가 든다 (0004). 회사 키·주소는 여기 없다 — 설치기가 `install.env` 로 심는다.
#    ⚠ 가볍고 멱등인 것(git config · mkdir · 값이 같으면 건너뛰는 setx)은 매 세션(auto)도 민다 — 키가
#      돌면 다음 세션이 새 값을 심는다. 망을 타는 clone 과 자리를 재는 홈 설정 덮기는 `--install` 만.
# ⚠ **부를 때마다 아무것도 스폰하지 않는다.** 옛 꼴은 `sed | head | tr | sed` 넷을 띄웠고,
#   선언 다섯 자리를 읽는 값이 프로세스 스물이었다 (#54). 파싱은 `case` 와 `${}` 로 다 된다.
#   **옛 표현의 뜻을 낱낱이 진다** — 앞의 공백을 걷고 · `이름=` 이 **붙어** 선 첫 줄만 들고
#   (`이름 = 값` 은 안 든다 · 이름이 다른 이름의 앞토막인 줄도 안 든다) · 값은 첫 `=` 뒤 전부 ·
#   CR 은 어디 박혔든 지우고 · 꼬리 공백을 걷는다. 글자 부류는 `[[:space:]]` 를 case 의
#   괄호식으로 그대로 들어 옛 sed 와 같은 자를 쓴다.
# ⚠ **한 자리만 옛것과 갈린다** — 옛 꼴은 이름을 sed 정규식에 박아 넣어 이름 안의 `.`·`*` 이
#   메타로 섰다. 새 꼴은 글자 그대로 든다. 선언의 이름은 다 영숫자·밑줄이라 실물은 안 갈린다.
_CR=$(printf '\r')   # 고리 밖에서 한 번 — `$'\r'` 은 sh 에 없다
conf_get() {  # conf_get <파일> <이름> — `이름=값` 한 줄. eval 하지 않는다: 선언은 값이지 코드가 아니다
  [ -f "$1" ] || return 0
  while IFS= read -r _cgl || [ -n "$_cgl" ]; do
    while :; do case "$_cgl" in [[:space:]]*) _cgl="${_cgl#?}" ;; *) break ;; esac; done
    case "$_cgl" in "$2="*) ;; *) continue ;; esac
    _cgv="${_cgl#"$2="}"
    while :; do case "$_cgv" in *"$_CR"*) _cgv="${_cgv%%"$_CR"*}${_cgv#*"$_CR"}" ;; *) break ;; esac; done
    while :; do case "$_cgv" in *[[:space:]]) _cgv="${_cgv%?}" ;; *) break ;; esac; done
    printf '%s\n' "$_cgv"
    return 0
  done < "$1"
  return 0
}
# 자리를 가른다 — `secrets.d/*.env` 의 `#site-probe`(닿음) → `#site-path`(경로) → `#site-default`.
# **이름으로 안 가른다**: DNS 는 사외에서도 사내 IP 를 풀어 준다 (0026). 답은 파일 이름(`posco` ·
# `outside` · `home`)이고 `$_SITE`, 그 파일은 `$_SITE_FILE` 에 선다.
# ⚠ **묻는 자가 있을 때만 잰다.** 프로브는 안 닿는 자리에서 3초를 무는데, 아무도 자리를 안 묻는
#   판에서는 그 3초가 순수한 손해다. 한 번 잰 답은 들고 다시 안 잰다 — 부르는 자가 둘이다.
_SITE=''; _SITE_FILE=''; _SITE_MODE=''; _SITE_DONE=''
_site_meta() {
  awk '
    {
      line = $0
      gsub(/\r/, "", line)
      if (line ~ /^#[[:space:]]*site-default[[:space:]]*=/ && !seen_default) {
        sub(/^#[[:space:]]*site-default[[:space:]]*=[[:space:]]*/, "", line)
        defval = line; seen_default = 1
      } else if (line ~ /^#[[:space:]]*site-probe[[:space:]]*=/ && !seen_probe) {
        sub(/^#[[:space:]]*site-probe[[:space:]]*=[[:space:]]*/, "", line)
        sub(/[[:space:]]*$/, "", line)
        probe = line; seen_probe = 1
      } else if (line ~ /^#[[:space:]]*site-path[[:space:]]*=/ && !seen_path) {
        sub(/^#[[:space:]]*site-path[[:space:]]*=[[:space:]]*/, "", line)
        sub(/[[:space:]]*$/, "", line)
        path = line; seen_path = 1
      } else if (line ~ /^#[[:space:]]*home-settings[[:space:]]*=/ && !seen_mode) {
        sub(/^#[[:space:]]*home-settings[[:space:]]*=[[:space:]]*/, "", line)
        sub(/[[:space:]]*$/, "", line)
        mode = line; seen_mode = 1
      }
    }
    END {
      printf "%s\n%s\n%s\n%s\n", defval, probe, path, mode
    }
  ' "$1"
}
_site_of() {
  [ -n "$_SITE_DONE" ] && return 0
  _SITE_DONE=1
  _sf=''; _sd=''; _sp=''
  for _f in "$CONFIG_ROOT"/secrets.d/*.env; do
    [ -e "$_f" ] || continue
    _default=''; _probe=''; _path=''; _mode=''
    {
      IFS= read -r _default
      IFS= read -r _probe
      IFS= read -r _path
      IFS= read -r _mode
    } <<EOF
$(_site_meta "$_f")
EOF
    case "$_default" in *yes*) _sd="$_f" ;; esac
    [ -n "$_sf" ] || {
      [ -n "$_probe" ] &&
        timeout 3 bash -c "(exec 3<>/dev/tcp/${_probe%%:*}/${_probe#*:})" 2>/dev/null &&
        _sf="$_f"
    }
    [ -n "$_sp" ] 2>/dev/null || {
      [ -n "$_path" ] && [ -d "$_path" ] && _sp="$_f"
    }
    [ -n "$_sf" ] || [ -n "$_sp" ] || continue
  done
  [ -n "$_sf" ] || _sf="${_sp:-$_sd}"
  _SITE_FILE="$_sf"
  [ -n "$_sf" ] && _SITE="$(basename "$_sf" .env)"
  if [ -n "$_sf" ]; then
    _default=''; _probe=''; _path=''; _SITE_MODE=''
    {
      IFS= read -r _default
      IFS= read -r _probe
      IFS= read -r _path
      IFS= read -r _SITE_MODE
    } <<EOF
$(_site_meta "$_sf")
EOF
  fi
  return 0
}

deploy_personal() {   # deploy_personal auto|install
  [ "$OS" = windows ] || return 0
  [ -n "$CONFIG_ROOT" ] && [ -f "$CONFIG_ROOT/personal.conf" ] || return 0
  _bc="$CONFIG_ROOT/personal.conf"
  _gn="$(conf_get "$_bc" GIT_NAME)"; _ge="$(conf_get "$_bc" GIT_EMAIL)"
  _repos="$(conf_get "$_bc" REPOS)"; _url="$(conf_get "$_bc" REPO_URL)"
  # `$HOME` 을 값에 쓸 수 있게 한 자리만 펴 준다 — 통째로 eval 하지 않는 대신이다.
  _root="$(conf_get "$_bc" ROOT)"; _root="$(printf '%s' "$_root" | sed "s|\$HOME|$HOME|g;s|^~|$HOME|")"
  [ -n "$_root" ] || _root="$HOME/repos"

  # git 신원 — **빈 값을 심지 않는다.** 이름을 빼먹은 채 심으면 `user.name` 이 빈 문자열로 굳고
  # 커밋이 「누가 했는지 없는」 채로 선다 — git 은 그걸 막지 않는다.
  if [ -n "$_gn" ] && [ -n "$_ge" ]; then
    [ "$(git config --global user.name 2>/dev/null)" = "$_gn" ] || git config --global user.name "$_gn"
    [ "$(git config --global user.email 2>/dev/null)" = "$_ge" ] || git config --global user.email "$_ge"
  elif [ "$1" = install ]; then
    echo "$PROJECT_NAME: ⚠ personal.conf 에 GIT_NAME · GIT_EMAIL 이 없다 — git 신원을 안 심었다"
  fi
  # 윈도우에서 물리는 것들. 바꿀 일이 있으면 이 줄들을 고친다.
  git config --global init.defaultBranch main
  git config --global core.autocrlf true      # 체크아웃은 CRLF, 저장소는 LF
  git config --global core.longpaths true     # 260자 벽 — 깊은 나무에서 clone 이 진다
  git config --global credential.helper manager
  git config --global pull.rebase false

  # 형제 저장소 — **없는 것만 받는다.** 당김은 각 저장소의 세션(auto)과 deploy.ps1 이 든다. `--install` 만 —
  # 망을 타고, 맨바닥 VDI 의 첫 판은 설치기가 부르는 이 갈래가 지지 세션 훅의 시간 한도가 지지 않는다.
  if [ "$1" = install ] && [ -n "$_repos" ]; then
    if [ -z "$_url" ]; then
      echo "$PROJECT_NAME: ⚠ personal.conf 에 REPOS 는 있는데 REPO_URL 이 없다 — 어디서 받을지 모른다"
    else
      mkdir -p "$_root"
      for _r in $_repos; do
        [ -d "$_root/$_r/.git" ] && continue
        echo "$PROJECT_NAME: $_r — clone ($_root)"
        git clone "$(printf '%s' "$_url" | sed "s|<이름>|$_r|g")" "$_root/$_r" ||
          echo "$PROJECT_NAME: ⚠ $_r clone 실패 — 주소 · 계정 · 망을 본다"
      done
    fi
  fi

  # 슬러그 폴더 — deploy.ps1 은 폴더가 있을 때만 메모리를 민다. 슬러그는 **윈도우 경로**에서 파생한다
  # (영숫자 아닌 글자가 전부 `-`). ⚠ 글자로 센다 — 로케일 없이 sed 가 바이트를 세면 한글 한 자가 대시
  # 셋이 되어 슬러그가 통째로 어긋나고 **메모리가 조용히 안 깔린다** (실측 2026-09-10 · `바탕 화면`).
  # ⚠ **`cygpath` 는 루트에 한 번만 부른다.** 저장소마다 부르면 `cygpath`+`sed` 둘이 저장소
  #   수만큼 는다(#54 · 이 PC 의 다섯 저장소에 열둘). 영숫자 아닌 글자가 **전부** `-` 가 되니
  #   이어붙임이 성립한다: 루트의 슬러그 + `-`(구분자 `\` 가 바뀐 것) + 이름의 슬러그.
  # ⚠ **글자로 센다는 규율은 그대로인데, 그것을 지는 자가 sed 에서 셸로 옮겨 왔다.** bash 의
  #   `${//}` 도 로케일을 탄다 — 이 PC 의 맨 로케일에서 `바탕 화면` 이 대시 여섯이 아니라
  #   **열넷**이 나왔다(실측 2026-09-16 · LC_ALL=C 의 sed 와 같은 값). 그래서 옛 꼴이 sed 앞에
  #   붙이던 `LC_ALL=C.UTF-8` 을 **셸 제 것으로** 세운다. bash 는 `LC_ALL` 대입에서 곧바로
  #   setlocale 을 부른다(재 봤다). ⚠ **빌린 뒤 돌려준다** — 안 돌려주면 뒤따르는 걸음의
  #   정렬·메시지가 말없이 딴 로케일에서 선다.
  _olc="${LC_ALL+x}"; _olcv="${LC_ALL:-}"; LC_ALL=C.UTF-8
  _rw="$(cygpath -w "$_root" 2>/dev/null || printf '%s' "$_root")"
  _rs="${_rw//[^A-Za-z0-9]/-}"
  for _r in $_repos; do
    _pp="$HOME/.claude/projects/$_rs-${_r//[^A-Za-z0-9]/-}"
    [ -d "$_pp" ] || mkdir -p "$_pp" 2>/dev/null || true
  done
  # 전역 층 — 저장소들을 담은 폴더
  [ -d "$HOME/.claude/projects/$_rs" ] || mkdir -p "$HOME/.claude/projects/$_rs" 2>/dev/null || true
  if [ -n "$_olc" ]; then LC_ALL="$_olcv"; else unset LC_ALL; fi

  # 개인 키 — `secrets.env` 를 사용자 환경변수로. 값이 같으면 건너뛰고, **빈 값은 안 심는다**(심으면
  # 부재가 「있다」로 뒤집힌다). ⚠ 평문이다 — 저장소가 private 인 것이 유일한 울타리다 (0025).
  # ⚠ 이 셸에도 심는다 — setx 는 새로 뜨는 프로세스부터 걸려서, 안 심으면 뒤따르는 deploy 가 방금
  #   넣은 키를 「없다」로 보고 남은 수동 작업에 도로 띄운다.
  # ⚠ 이 고리는 줄마다 아무것도 스폰하지 않는다 — 윈도우는 프로세스 하나가 ~90ms 라, 줄마다
  #   `printf | tr | sed` 를 띄우면 값 셋을 심으려고 백 번을 넘게 띄운다 (0054). 파싱은 `case` 와
  #   `${}` 로 다 되는 일이고, **버릴 줄은 다듬기 전에 버린다** — 주석·빈 줄을 정규화할 까닭이 없다.
  # ⚠ **자리를 타는 이름이 섞여 있다.** 바로 위에 `#only = <자리>,<자리>` 를 단 줄은 **거기서만**
  #   심는다 — 저쪽에서 해로운 이름이 있어서다(`GOOGLE_API_KEY` 는 사내에서 회사 키를 제친다).
  #   넣는 기준은 「여기서 쓰나」가 아니라 **「저쪽에서 해로운가」**이고, 그 자는 README 가 든다.
  # ⚠ **auto 세션은 그 줄을 아예 안 본다** — 자리를 재려면 프로브가 3초를 무는데, 심는 일은
  #   `--install` 이 이미 한 번 한다. **안 심을 뿐 걷지는 않는다** — 이미 심긴 값을 걷는 자는 없다.
  if [ -f "$CONFIG_ROOT/secrets.env" ]; then
    _cr=$(printf '\r'); _tab=$(printf '\t')   # 고리 밖에서 한 번 — `$'\r'` 은 sh 에 없다
    _only=''
    while IFS= read -r _line || [ -n "$_line" ]; do
      case "$_line" in
        '#'*only*=*) _only="${_line#*=}"                        # 바로 다음 이름 한 줄에만 걸린다
                     while :; do case "$_only" in ' '*|"$_tab"*) _only="${_only#?}" ;; *) break ;; esac; done
                     while :; do case "$_only" in *' '|*"$_tab"|*"$_cr") _only="${_only%?}" ;; *) break ;; esac; done
                     continue ;;
        ''|'#'*)     continue ;;                 # CRLF 인 빈 줄은 CR 만 남아 아래 *=* 에서 걸린다
      esac
      case "$_line" in *=*) ;; *) continue ;; esac
      while :; do                                    # 꼬리의 CR·공백·탭을 걷는다 — sed 없이
        case "$_line" in *' '|*"$_tab"|*"$_cr") _line="${_line%?}" ;; *) break ;; esac
      done
      _k="${_line%%=*}"; _v="${_line#*=}"
      if [ -n "$_only" ]; then                   # 바로 위 줄이 자리를 걸었다 — 쓰고 비운다
        _o="$_only"; _only=''
        [ "$1" = install ] || continue
        _site_of
        case ",$_o," in
          *",$_SITE,"*) ;;
          *) echo "$PROJECT_NAME: $_k — 안 심는다 (자리가 ${_SITE:-모름} · 이 이름은 $_o 에서만 산다)"
             continue ;;
        esac
      fi
      if [ -z "$_v" ]; then
        [ "$1" = install ] && echo "$PROJECT_NAME: ⚠ $_k — 비었다 (secrets.env 에 값을 넣고 커밋할 것)"
        continue
      fi
      [ "${!_k:-}" = "$_v" ] && continue
      if setx "$_k" "$_v" >/dev/null 2>&1; then
        export "$_k=$_v"; echo "$PROJECT_NAME: $_k — 심었다"
      else
        echo "$PROJECT_NAME: ⚠ $_k 심기 실패 (값이 1024자를 넘나 본다)"
      fi
    done < "$CONFIG_ROOT/secrets.env"
  fi

  # 홈 개인 설정 씨앗 — `vdi-home-settings.json`. 없으면 깔고, 자리 파일이 `#home-settings = overwrite`
  # 를 들면 병합해 덮는다. 자리를 가르는 자는 위 `_site_of` 다.
  # `--install` 만 — 프로브는 안 닿는 자리에서 3초를 물고, 덮을 자리(사외 VDI)는 매 로그인 설치기를 거친다.
  # ⚠ 안 덮는 자리에서는 있으면 안 건드린다 — 세션 중에 앱에서 바꾼 값을 재실행이 지우면 안 된다.
  [ "$1" = install ] || return 0
  _hs="$CONFIG_ROOT/vdi-home-settings.json"; _hd="$HOME/.claude/settings.json"
  [ -f "$_hs" ] || return 0
  mkdir -p "$HOME/.claude"
  if [ ! -f "$_hd" ]; then
    cp "$_hs" "$_hd" && echo "$PROJECT_NAME: 홈 settings.json — 씨앗을 깔았다"
    return 0
  fi
  _site_of
  _mode="$_SITE_MODE"
  [ "$_mode" = overwrite ] || return 0
  # ⚠ **`hooks` 와 `env` 는 씨앗의 것이 아니라 기계가 심은 것이라 넘겨 준다** (0028 · 0030). 훅의 심는 명령은
  #   작업 루트 경로를 들어 PC 마다 다르고, env 는 설치기가 이 자리 값으로 방금 민 것이다. 지킬 수 없으면
  #   (파이썬이 없다) **안 덮는다** — 덮으면 이 칸이 고치려는 바로 그 고장을 이 칸이 만든다.
  # ⚠ **견줄 상대는 씨앗이 아니라 병합 결과다.** 씨앗과 견주면 심긴 훅 때문에 영영 안 맞아 매 로그인
  #   덮고 백업이 쌓인다. 먼저 만들고, 같으면 안 건드린다.
  _new="$_hd.new.$$"
  if "$PY_CMD" -c '' >/dev/null 2>&1 && "$PY_CMD" - "$_hs" "$_new" "$_hd" <<'PYMERGE'
import json, sys
src, out, cur = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src, encoding="utf-8") as f:
    cfg = json.load(f)
try:
    with open(cur, encoding="utf-8") as f:
        old = json.load(f)
except (OSError, ValueError):
    old = {}
if "hooks" in old:                      # 기계가 심은 것 — 씨앗은 이 키에 의견이 없다
    cfg["hooks"] = old["hooks"]
if isinstance(old.get("env"), dict):    # 설치기가 이 자리 값으로 민 것 — 씨앗보다 이긴다
    cfg["env"] = {**cfg.get("env", {}), **old["env"]}
with open(out, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
    f.write("\n")
PYMERGE
  then
    if cmp -s "$_new" "$_hd"; then
      rm -f "$_new"
    elif cp "$_hd" "$_hd.bak-$(date +%Y%m%d-%H%M%S)" && mv "$_new" "$_hd"; then
      echo "$PROJECT_NAME: 홈 settings.json — 덮었다 ($_SITE 가 overwrite 를 든다)"
    else
      rm -f "$_new"; echo "$PROJECT_NAME: ⚠ 홈 settings.json 덮기 실패 — 쓰기 권한을 본다"
    fi
  else
    rm -f "$_new"; echo "$PROJECT_NAME: ⚠ 홈 settings.json — 파이썬을 못 불러 안 덮는다 (심긴 훅을 지킬 수 없다)"
  fi
}

# ── 전역 SessionStart 훅을 홈에 심는다 (claude-config 0010 · 0028) ──────────────
#    **저장소 훅은 세션 루트가 그 저장소일 때만 걸린다.** 그 밖에서 연 세션 — 저장소들을
#    담은 폴더(전역 층 · deploy 가 `[memory:global]` 로 슬러그까지 두는 자리)나 홈 — 은
#    아무 훅도 안 건다. 세션마다 auto 를 다시 걸 자는 홈 훅뿐이다. 심는 명령은 익명이다 —
#    저장소 이름을 모르고 작업 루트만 든다 (0004 와 같은 결).
#    ⚠ **그 명령은 저장소 안에서 연 세션이면 빠진다** (결정 0036). 쓸기는 저장소 **밖에서**
#      연 세션에만 남는다 — 안에서 열면 그 저장소의 제 설정이 이미 훅을 걸기 때문이다.
#      옛 판은 조건 없이 쓸어, 저장소 하나를 열면 형제 전부가 돌고 연 저장소는 두 번 돌았다.
# ⚠ **자리가 여기인 까닭** — 옛 판은 설치 갈래 ②′ 안에 있었다. 그런데 지문이 맞는 세션은
#   설치를 통째로 건너뛰고(auto 의 침묵 갈래), deploy.ps1 도 `--check` 가 꺼진 검사를 낼
#   때만 `--install` 을 계획한다. 그래서 **도구가 멀쩡한 기계에서 훅만 걷히면 다시 심을
#   자가 없었다** — 「훅이 심겼나」와 「도구가 갖춰졌나」는 다른 명제인데 한 갈래에 묶여
#   있었다. 같은 고장을 위 `global_rule_reason` 이 이미 겪고 설치 갈래 밖으로 나왔다.
#   이 함수는 그 이사의 나머지 절반이다 — 홈 규범과 같은 자리에서 같은 두 갈래가 부른다.
# ⚠ **해석기는 OS 가 정한다** — 윈도우는 `python`, 리눅스는 `python3` (위 PY_CMD).
#   윈도우에서 `python3` 는 스토어로 보내는 껍데기라 `command -v` 로 물으면 「있다」가
#   나오고 부르면 49 로 죽는다. 그래서 가드가 `py_num`(실행형)이다 — 존재로 물으면
#   심기가 조용히 실패하고, 조용한 실패는 이 훅이 막으려는 바로 그것이다.
# ⚠ **실패는 stdout 으로 말한다.** 옛 판은 `try` 로 install-fail 에 적었는데, 그 파일은
#   설치 갈래에서만 읽히고 「파일을 열어 보라」는 말은 안 열린다 (아래 침묵 갈래 주석과
#   같은 자리다). 매 세션 한 줄 서는 것이 값이다 — 안 걸리는 것보다 싸다.
# ── 심는 명령 — **진본은 여기 한 자리다.** 심는 자와 재는 자가 이것을 인자로 받는다.
#    ⚠ 이 문자열에는 **작업 루트가 박힌다** — 그래서 「심겼나」는 이름이 아니라 루트로만
#      정직하게 물을 수 있다. 재는 쪽에 같은 꼴을 또 적으면 그것이 손사본이라, 루트가
#      바뀐 날 둘이 말없이 갈린다.
#    ⚠ **꼴을 굳혀야 완전일치가 선다.** 윈도우에서 같은 폴더가 두 꼴로 산다 — `C:/Users/…`
#      와 `/c/Users/…`. 실측 2026-09-08 (회사 VDI): 홈에 심겨 있던 것은 앞엣것인데 훅이
#      제자리에서 계산하면 뒤엣것이 나와, 완전일치가 **같은 루트를 「딴 루트」로** 잡았다.
#      ⚠ **어느 갈래가 앞엣것을 냈는지는 못 쟀다.** `cd … && pwd` 는 PowerShell 에서 불러도
#        POSIX 로 정규화된다(재 봤다) — 그러니 남는 후보는 위 `CLAUDE_PROJECT_DIR` 물러섬인데
#        그 값의 꼴은 하네스가 정하고 이 자리에서 못 잰다. **까닭을 모른 채로 굳힌다** —
#        고치려는 것이 「왜 갈렸나」가 아니라 「갈려도 안 쌓이나」라서다.
#      안 굳히면 부르는 자가 바뀔 때마다 항목이 하나씩 붙어, **이 함수가 막으려는 쌓임을
#      이 함수가 만든다.** 글롭은 bash 가 푸니 둘 다 돌지만, 진본은 하나여야 한다.
home_hook_root() {   # 작업 루트 — 굳힌 꼴. 명령도 진단 문구도 이것을 쓴다
  _hr="$(dirname "$PROJECT_DIR")"
  [ "$OS" = windows ] && _hr="$(cygpath -m "$_hr" 2>/dev/null || printf '%s' "$_hr")"
  printf '%s' "$_hr"
}

# ── 전역형 선언 — **기계에 하나만 서는 것들** (#43) ──────────────────────────────
# ⚠ **가르는 자는 설치법이다.** 아래 넷은 깔리는 자리가 홈·전역이라(npm 전역 · `~/bin` ·
#   winget 사용자 자리 · 배포판) 저장소가 몇이든 실물은 하나다. `project-axis` 만 저장소를
#   탄다 — 그것의 진본은 `package.json`·`requirements.txt` 이고 까는 자도 따로다.
global_kind() {  # global_kind <install 값>
  case "$1" in npm-global|github-release-binary|winget|apt-package) return 0 ;; esac
  return 1
}
# ── 전역형 선언을 든 파일들 — **이름을 안 박는다.** 제 것 둘이 먼저고, 그 다음 작업 루트에
#    붙은 저장소들의 선언이다. 훅을 든 저장소를 루트에서 훑는 것은 `plant_session_state` 가
#    이미 하는 일이고, 여기는 같은 자를 같은 뜻으로 들 뿐이다.
#    ⚠ **겹침은 파일이 아니라 이름으로 걷는다** — 윈도우에서 한 폴더가 두 꼴로 사므로
#      (`/c/Users/…` · `C:/Users/…`) 경로 문자열로 겹침을 못 판정한다. 부르는 쪽이 절 이름을
#      본 순서대로 한 번만 든다. 제 것을 앞에 두는 까닭이 그것이다 — 이 저장소의 선언이 이긴다.
global_conf_list() {
  printf '%s\n%s\n' "$GCONF" "$PCONF"
  for _gc in "$(home_hook_root)"/*/.claude/tools.global.conf "$(home_hook_root)"/*/.claude/tools.conf; do
    [ -f "$_gc" ] && printf '%s\n' "$_gc"
  done
  return 0
}
# ── 전역형 지문 — `decl_fingerprint` 의 짝이다. 저쪽은 저장소 몫, 이쪽은 기계 몫.
#    ⚠ **절을 안 가리고 파일을 통째로 문다.** 전역형만 골라 담으려면 파일을 파싱해 다시
#      이어야 하는데, 그 이음새가 어긋나면 **선언이 바뀌었는데 지문이 그대로**가 된다 —
#      부재가 통과로 읽히는 그 자리다. 넘치게 무는 쪽은 전역 갈래를 한 번 더 돌 뿐이고
#      그 갈래는 정상 상태에서 프로브뿐이다.
# ⚠ **프로세스는 `sha256sum` 하나다** (#54). 옛 꼴은 목록을 `mktemp` 파일로 받아 선언마다
#   `cat` 을 띄우고 끝에 `awk` 를 띄웠다 — 이 PC 의 열한 자리면 열다섯이다. 목록은 파이프로
#   바로 먹이고, 파일은 `read` 로 읽어 `printf` 로 도로 낸다.
#   ⚠ **무는 바이트와 그 차례가 안 바뀌는 것이 요점이다.** 바뀌면 이미 깔린 기계의 도장이
#     통째로 어긋나 저장소마다 한 번씩 다시 깐다 (#56 이 이름을 갈 때 겪은 그 자리).
#   ⚠ `$(<"$f")` 는 안 쓴다 — 꼬리 줄바꿈을 먹어 바이트가 갈린다. 줄바꿈 없이 끝나는 파일은
#     고리가 끝난 뒤 `$_gln` 에 남은 토막으로 잇는다.
global_fingerprint() {
  global_conf_list | {
    while IFS= read -r _gf; do
      [ -f "$_gf" ] || continue
      _gln=""
      while IFS= read -r _gln; do printf '%s\n' "$_gln"; done < "$_gf"
      [ -n "$_gln" ] && printf '%s' "$_gln"
    done
  } | sha256sum | { read -r _gh _grest; printf '%s\n' "$_gh"; }
}

home_hook_cmd() {
  # ⚠ **저장소 안에서 연 세션이면 이 훅은 빠진다.** 옛 꼴은 조건 없이 작업 루트를 쓸어, 저장소
  #   하나를 열면 형제 전부의 훅이 돌았다 — 게다가 연 저장소는 **제 설정과 이 고리가 겹쳐 두 번**
  #   돌았다. 0010 이 잰 값은 「저장소 둘을 2.2초」(리모트 컨테이너)였고 0028 이 윈도우로 넓힐 때
  #   **개수(넷)는 다시 셌으나 시간은 안 쟀다** — 컨테이너 둘의 값이 PC 다섯으로 그대로 넘어왔다.
  #   붙인 것만 있는 컨테이너에서는 곱셈이 안 보이고 **PC 에서만 보인다.**
  # ⚠ **쓸기는 지우지 않고 조건을 얻는다** — 저장소 밖에서 연 세션(홈·전역 층)은 0028 이 산
  #   값이라 그대로 남는다. 그때만 쓴다.
  # ⚠ **제 설정이 거는지 물어본다.** 「걸 것이다」로 가정하면 설정 없는 저장소가 아무것도 안 도는데
  #   그 부재는 조용하다 — 물어보고, 안 걸면 여기서 직접 부른다.
  # ⚠ **저장소 밖(홈·전역 층)에서는 설정 저장소의 훅 하나만 부른다** (0043). 옛 꼴은 형제 전부를 차례로
  #   불렀는데, VS Code 확장은 첫 스폰을 홈 cwd 로 띄우고 **초기화를 60초만 기다린다** — 회사 VDI 실측
  #   2026-09-14: 훅 다섯 × (당김 6~7초 + 몸통) 이 그 60초를 넘겨 「Subprocess initialization did not
  #   complete within 60000ms」로 두 번 죽었고 사람은 10분을 기다렸다. 형제 훅은 그 저장소를 열 때
  #   제 설정이 부른다 — 전역 층에서 필요한 것은 홈 규범·개인 칸·전역 도구뿐이고 그것은 설정 저장소
  #   훅이 든다. 이름은 안 박는다 — `deploy.ps1` 과 `memory/` 를 든 저장소가 곧 그것이다(위 CONFIG_ROOT
  #   와 같은 자).
  printf 'p="$CLAUDE_PROJECT_DIR"; if [ -f "$p/.claude/hooks/session-start.sh" ]; then grep -q session-start.sh "$p/.claude/settings.json" 2>/dev/null || bash "$p/.claude/hooks/session-start.sh"; else for h in "%s"/*/.claude/hooks/session-start.sh; do d="${h%%/.claude/*}"; [ -f "$d/deploy.ps1" ] && [ -d "$d/memory" ] && bash "$h"; done; fi' \
    "$(home_hook_root)"
}

# ── 세션 상태를 심는다 — **한 프로세스가 둘을 다 한다** ────────────────────────
#   드는 것: ① 홈 SessionStart 훅 ② 이 저장소의 신뢰.
# ⚠ **옛 판은 프로세스를 넷 띄웠다** — 판을 묻는 `py_num` · 훅 심기 · 껍데기 판별하는 `-c ''` ·
#   신뢰 심기. 저장소마다 넷이라 형제 다섯이면 **한 세션에 스물**이었고, 윈도우에서는 프로세스
#   뜨는 값이 일 자체보다 컸다. 파이썬을 한 번만 띄우고 그 안에서 둘을 다 한다.
# ⚠ **해석기가 못 뜨는 것은 종료코드로 안다** — 윈도우의 `python3` 는 스토어로 보내는 껍데기라
#   부르면 49 로 죽는다. 그래서 존재로 묻지 않고 **불러 보고 지면** 말한다(가드를 따로 띄우지
#   않는 것이 이 합침의 요점이다). 진 뒤에 가드 하나를 더 띄워 「못 뜬다」와 「죽었다」를 가르는
#   것은 실패 갈래뿐이다 (#51) — 성한 길은 그대로 프로세스 하나다.
# ⚠ **옛 항목을 지운다.** 심기는 여태 「없으면 붙인다」뿐이라, 명령 글자가 바뀌면 옛 항목이
#   남아 **옛 고리가 같이 돌았다** — 위 가드가 무효가 되는 자리다. 우리 꼴(`session-start.sh`
#   를 든 명령)만 걷고, 무엇을 걷었는지 화면에 댄다.
plant_session_state() {
  _pse="$(mktemp)"   # stderr 를 받아 둔다 — 「못 부른다」와 「죽었다」를 가르는 물증이다 (#51)
  _pss="$("$PY_CMD" - "$HOME/.claude/settings.json" "$(home_hook_cmd)" "$PROJECT_DIR" "$(home_hook_root)" <<'PSSEOF' 2>"$_pse"
import json, os, sys, tempfile

settings, cmd, proj, root = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
msgs = []


def save(path, cfg):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
        return True
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        return False


# ① 홈 SessionStart 훅 — 우리 옛 꼴은 걷고 지금 꼴만 남긴다
try:
    with open(settings, encoding="utf-8") as f:
        cfg = json.load(f)
except (OSError, ValueError):
    cfg = {}
entries = cfg.setdefault("hooks", {}).setdefault("SessionStart", [])
have, dropped = False, []
for e in entries:
    keep = []
    for h in e.get("hooks", []):
        c = h.get("command", "")
        if c == cmd:
            have = True
            keep.append(h)
        elif "session-start.sh" in c:
            dropped.append(c)
        else:
            keep.append(h)
    e["hooks"] = keep
entries[:] = [e for e in entries if e.get("hooks")]
if not have:
    entries.append({"hooks": [{"type": "command", "command": cmd, "timeout": 600}]})
if not have or dropped:
    if save(settings, cfg):
        if not have:
            msgs.append("  홈 SessionStart 훅 — 심었다")
        for c in dropped:
            msgs.append("  홈 SessionStart 훅 — 옛 항목을 걷었다: %s" % c[:70])
    else:
        msgs.append("  ! 홈 settings.json 을 못 썼다 — 쓰기 권한을 본다")

# ② 신뢰 — 없거나 깨진 파일은 손대지 않는다
# ⚠ **작업 루트의 저장소 전부에 건다.** 옛 판은 제 저장소만 걸고 「홈 훅이 어차피 전부
#   부른다」를 근거로 삼았는데, 그 고리에 가드가 붙어 그 근거가 사라졌다. 안 넓히면 저장소를
#   처음 열 때마다 신뢰 창이 뜨고, 프로필이 매 로그인 날아가는 PC 에서는 **매번** 뜬다.
#   같은 파일 쓰기 한 번에 담으니 값은 0 이고, 거는 대상은 옛 고리가 걸던 것과 같은 집합이다
#   (훅을 든 저장소만) — posture 를 넓히는 것이 아니라 하던 일을 한 자리로 옮기는 것이다.
BS = chr(92)
import glob as _glob
targets = [proj]
for h in _glob.glob(os.path.join(root, "*", ".claude", "hooks", "session-start.sh")):
    targets.append(os.path.dirname(os.path.dirname(os.path.dirname(h))))
forms = sorted({t.replace("/", BS) for t in targets} | {t.replace(BS, "/") for t in targets})
tp = os.path.join(os.path.expanduser("~"), ".claude.json")
try:
    with open(tp, encoding="utf-8") as f:
        tcfg = json.load(f)
except (OSError, ValueError):
    tcfg = None
if tcfg is not None:
    pr = tcfg.setdefault("projects", {})
    todo = [k for k in forms if not (pr.get(k) or {}).get("hasTrustDialogAccepted")]
    if todo:
        for k in todo:
            pr.setdefault(k, {})["hasTrustDialogAccepted"] = True
        if save(tp, tcfg):
            msgs.append("  신뢰 — %d 자리에 걸었다 (다음 세션부터 안 묻는다)" % len(todo))

for m in msgs:
    print(m)
PSSEOF
)"
  _prc=$?
  if [ "$_prc" -ne 0 ]; then
    # ⚠ **한 문구로 둘을 덮지 않는다** (#51). 해석기가 안 뜬 것과 스크립트가 다 쓰고 나서 죽은 것은
    #   고칠 자리가 다르다 — 옛 판은 stderr 를 버리고 둘 다 「못 부른다」로 내서, 인코딩으로 죽은
    #   자리를 스토어 껍데기로 오진했다(#50). 진 뒤에만 해석기를 한 번 더 불러 가른다. 죽은 쪽은
    #   홈 훅·신뢰가 이미 써졌을 수 있다 — 심겼나는 `--check` 가 잰다.
    if ! "$PY_CMD" -c '' >/dev/null 2>&1; then
      echo "$PROJECT_NAME: ⚠ 홈 SessionStart 훅·신뢰를 못 심는다 — $PY_CMD 를 못 부른다(윈도우면 스토어 껍데기다). 저장소 밖에서 연 세션은 아무 훅도 안 건다."
    else
      _pl="$(grep -v '^[[:space:]]*$' "$_pse" 2>/dev/null | tail -1 | cut -c1-160)"
      [ -n "$_pl" ] || _pl="stderr 가 비었다 (exit $_prc)"
      echo "$PROJECT_NAME: ⚠ 홈 SessionStart 훅·신뢰 — 심는 스크립트가 죽었다: $_pl — 심겼는지는 --check 가 잰다."
    fi
    rm -f "$_pse"
    return 0
  fi
  rm -f "$_pse"
  [ -n "$_pss" ] && printf '%s\n' "$_pss"
  return 0
}

# ── 심겼나 — **판정도 문구도 진단 절 한 자리가 낸다.** 여기는 재기만 한다.
#    ⚠ **`--check` 만 정직하게 잴 수 있는 자리다.** auto·install 은 재기 전에 심어 버려
#      늘 초록이 나온다. 그래서 이 값을 쓰는 자는 진단 절이고, 거기서 `--check` 가 이
#      기계의 홈을 있는 그대로 낸다.
#    ⚠ 가드가 심기와 **같은 자리**다 — 못 부르면 「없다」가 아니라 「못 잼」이다.
#      부재를 통과로 읽지 않는 것과 같은 결로, 못 잼도 초록으로 읽지 않는다.
#    ⚠ **이름이 아니라 루트로 묻는다.** 옛 판은 명령에 `session-start.sh` 가 들었나만 봤다
#      — 심는 쪽은 루트가 박힌 문자열을 **완전일치**로 거르는데 재는 쪽만 부분일치라,
#      **어느 루트가 박혀 있든 초록이었다.** 저장소를 옮기면 새 항목이 붙고 낡은 항목은
#      남는데 진단은 둘 다 통과시킨다 — 그래서 갈래가 넷이다. 낡은 것을 **지우지는
#      않는다**: 작업 루트를 둘 둔 기계가 정당하고, 사람이 손댄 설정을 말없이 지우는 것은
#      이 훅의 일이 아니다. 자리를 말하고 간다(선언 부재를 다루는 자리와 같은 결).
home_hook_planted() {   # 0=이 루트로 심김 · 1=안 심김 · 2=못 잼 · 3=심겼는데 낡은 항목이 남음
  [ -n "$(py_num "$PY_CMD")" ] || return 2
  "$PY_CMD" - "$HOME/.claude/settings.json" "$(home_hook_cmd)" <<'HOOKEOF'
import json, sys
path, cmd = sys.argv[1], sys.argv[2]
try:
    cfg = json.load(open(path, encoding="utf-8"))
except (OSError, ValueError):
    raise SystemExit(1)
found, stale = False, []
for e in cfg.get("hooks", {}).get("SessionStart", []):
    for h in e.get("hooks", []):
        c = h.get("command", "")
        if c == cmd:
            found = True
        elif "session-start.sh" in c:
            # 우리 꼴이면 루트만 — 아니면 명령 그대로. 「파일을 열어 보라」는 말은 안 열린다
            parts = c.split('"')
            stale.append(parts[1] if len(parts) > 2 else c)
for s in stale:
    print(s)
raise SystemExit((3 if stale else 0) if found else 1)
HOOKEOF
}

# ── 세션 셸에 venv 를 배선한다 — 설치의 일이 아니라 **매 세션의 일**이다 (0011).
#    CLAUDE_ENV_FILE 은 세션마다 새로 오는 값이라, 설치 갈래 안에만 두면 지문이
#    깨끗한 세션(정상 상태)은 배선 없이 출발한다 — 실측 2026-08-25: venv 는
#    완비인데 에이전트 셸은 시스템 파이썬을 보고 「의존성이 없다」로 오판했다.
#    갈래 셋 — 닿는 셸이 서로 다르다:
#      CLAUDE_ENV_FILE    훅으로 불린 세션의 도구 셸 — 훅이 발화할 때만 존재한다
#      /etc/profile.d     로그인 셸 — 사람이 컨테이너에 들어온 자리
#      ~/.local/bin 래퍼  그 밖 전부 — 도구 셸은 PATH 를 하네스가 제 목록으로 덮어
#                         rc 파일의 프리펜드가 안 남고(실측), PATH 1순위인 이 폴더만
#                         통한다. 훅이 발화하지 않거나 저장소를 잘못 잡은 세션(0011 · 0012)
#                         에도 스냅샷에 실려 남는 유일한 길이다.
#    ⚠ 래퍼는 심링크가 아니다 — venv 파이썬을 링크로 부르면 argv0 곁에서 pyvenv.cfg
#      를 못 찾아 **맨 해석기**(패키지 없는 3.14)로 선다(실측 2026-08-25). exec 가
#      실경로를 넘겨야 venv 로 선다.
# ── Claude Code 의 신뢰 목록에 이 저장소를 넣는다 (claude-config #14) ─────────────
# ⚠ **왜 있나.** `~/.claude.json` 의 `projects` 키는 경로가 **문자열 그대로** 박힌다. 윈도우에서
#   한 폴더는 철자가 여럿이라(역슬래시 꼴 · 슬래시 꼴) 같은 폴더가 두 벌로 앉고 **신뢰가 한쪽
#   에만 붙는다.** 그러면 반대 철자로 여는 세션이 이미 승인한 폴더에 대화상자를 다시 띄운다.
#   비영속 VDI 는 그 파일이 매 로그인 새로 나서 손으로는 못 따라간다.
# ⚠ **더하기만 한다 — 아무것도 안 지운다.** #14 의 방침이 막은 것은 「규칙으로 지우기」다:
#   두 벌 중 어느 쪽이 살아 있나는 PC 마다 달라 규칙이 살아 있는 쪽을 지울 수 있다. 신뢰
#   플래그를 양쪽에 켜는 것은 그 위험에 안 걸린다 — 켜서 잃는 것이 없다.
# ⚠ **이미 켜져 있으면 안 쓴다.** 그 파일은 돌고 있는 Claude Code 가 쥔 것이라 쓸 때마다
#   경합한다. **아무것도 안 하는 것이 이 함수의 정상**이고, 쓸 때도 옆에 쓰고 옮긴다.
# ⚠ **이 세션에는 안 먹을 수 있다** — CLI 가 제 메모리 판으로 나중에 덮으면 다음 세션부터
#   선다. 막을 자리가 없어 아는 채로 둔다.
# ⚠ 몸통은 저장소 이름을 모른다 — 목록을 박지 않고 **작업 루트를 훑어** 훅을 든 저장소를
#   찾는다. 옛 근거는 「홈 훅이 어차피 전부 부른다」였는데 그 고리에 가드가 붙어(결정 0036)
#   근거가 사라졌다 — 그래서 거는 자리를 이 함수가 직접 든다.
# ⚠ **역슬래시를 글자로 안 적는다** — MSYS heredoc 이 삼켜 조용히 어긋난다(#14 가 쟀다).
#   파이썬 쪽에서 `chr(92)` 로 짓는다.

wire_python_path() {
  [ -x "$VENV_BIN/python" ] || [ -x "$VENV_BIN/python.exe" ] || return 0
  [ -n "${CLAUDE_ENV_FILE:-}" ] &&
    echo "export PATH=\"$VENV_BIN:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  if [ "$OS" = linux ]; then
    [ -w /etc/profile.d ] 2>/dev/null &&
      printf 'export PATH="%s:$PATH"\n' "$VENV_BIN" > "/etc/profile.d/${PROJECT_NAME}-venv.sh"
    # 리눅스는 이 함대에서 리모트 컨테이너 계열뿐이라(0009 의 넷) PC 파이썬을 덮을 일이 없다
    mkdir -p "$HOME/.local/bin" 2>/dev/null || return 0
    for _wn in python python3; do
      printf '#!/bin/sh\nexec "%s/python" "$@"\n' "$VENV_BIN" > "$HOME/.local/bin/$_wn" 2>/dev/null &&
        chmod +x "$HOME/.local/bin/$_wn" 2>/dev/null
    done
  fi
  return 0
}

# ── 전역 축 — claude-config 가 붙어 있나. **판정도 문구도 여기 한 자리다.**
#    자리가 여기인 까닭: 옛 판은 설치 분기 안에 있었고(옛 ⑥), 지문이 맞는 세션은 설치를
#    통째로 건너뛰므로 **정작 조용히 도는 세션이 경고를 못 받았다.** 진단 절도 늦다 —
#    침묵 갈래는 그 앞에서 나간다. 그래서 게이트 앞에 세우고 두 자리에서 달리 낸다.
# ⚠ 판정은 「내가 깔았나」가 아니라 **홈이 지금 무엇을 들고 있나**로 낸다 — 리모트 홈은
#   이미지에 구워져 오므로 못 닿는 세션도 규율은 들고 있다. 없는 것이 아니라 낡는 것이 위험이다.
global_rule_reason() {   # 낸다: 못 닿으면 까닭 한 줄, 닿으면 빈 문자열
  [ -n "$CONFIG_ROOT" ] && return 0
  if [ -f "$HOME/.claude/CLAUDE.md" ]; then
    echo "claude-config 를 못 찾아 홈에 있는 것을 못 갱신한다 — 언제 판인지 모른다. add_repo 로 함께 붙인다"
  else
    echo "claude-config 를 못 찾았고 홈에도 없다 — 전역 규범·영역 룰·세션 기록·문서 표준 스킬·사내 환경 문서·씨앗에 못 닿는다. add_repo 로 함께 붙인다"
  fi
}

# ── git 이 진 까닭 한 줄 — **삼키지 않는다.** 진본은 여기 한 자리고, 당김(auto ①)과
#    스냅샷 맞춤(install ⑦)이 같이 쓴다.
# ⚠ **끝줄이 아니라 첫 `fatal:`/`error:` 줄이다.** 로컬 작업 트리 갈래는 끝줄이 `Aborting`
#   이라, 끝줄을 집으면 사유가 있는데 층이 안 갈린다(실물로 재 봤다). 층이 갈리는 것이
#   요점이다 — 아래 넷이 여기서 나뉘고, 넷은 손대는 자리가 서로 다르다:
#     `could not read Username`  자격증명 — GCM 이 사람을 부르려는데 훅엔 부를 사람이 없다
#     `unable to access …`       망·게이트
#     `Your local changes …`     로컬 수정 · 줄끝(`core.autocrlf`)
#     `Not possible to fast-forward`  로컬이 원격과 갈라졌다
git_why() {   # git_why <붙잡은 stderr> — 층이 갈리는 한 줄
  _w="$({ printf '%s\n' "$1" | grep -m1 -E '^(fatal|error):' ||
          printf '%s\n' "$1" | grep -v '^[[:space:]]*$' | tail -1; } 2>/dev/null | cut -c1-160)"
  printf '%s' "${_w:-사유가 안 나왔다}"
}

# ── 방금 당겨 봤나 — **한 세션에 같은 저장소를 여러 번 당기지 않는다.**
#    홈 훅은 저장소마다 프로세스를 새로 띄우고, 그 프로세스가 각자 「제 저장소 +
#    claude-config」를 당긴다. 저장소 다섯이면 claude-config 만 다섯 번이다
#    (실측 2026-09-09 회사 PC: 한 훅 출력에 같은 경고가 아홉 줄, 그중 다섯이 claude-config).
#    프로세스가 갈려 있어 메모리로는 못 가른다 — 표식 파일이 유일한 자리다.
# ⚠ **성공·실패를 안 가리고 찍는다.** 비싼 쪽이 실패 갈래라, 실패만 다시 도는 판이면
#   걷는 뜻이 없다. 당김 자체가 아니라 **시도**를 적는 것이라 이름도 그렇게 둔다.
# ⚠ 표식은 `.git` 안에 둔다 — 작업 트리를 안 더럽힌다. 더럽히면 그 더러움이 다음 세션의
#   `pull --ff-only` 를 막아, 이 함수가 줄이려는 실패를 이 함수가 만든다.
PULL_TTL=90   # 초. 훅 둘(저장소·홈)이 한 세션에서 40여 초 걸러 도는 것을 한 창으로 덮는다
pull_due() {   # pull_due <저장소> — 0=당길 차례 · 1=방금 다른 프로세스가 해 봤다
  _gd="$(git -C "$1" rev-parse --absolute-git-dir 2>/dev/null)" || return 0
  [ -n "$_gd" ] || return 0
  _st="$_gd/claude-pull-attempted"
  if [ -f "$_st" ]; then
    _age=$(( $(date +%s) - $(date -r "$_st" +%s 2>/dev/null || echo 0) ))
    [ "$_age" -ge 0 ] && [ "$_age" -lt "$PULL_TTL" ] && return 1
  fi
  : > "$_st" 2>/dev/null || true
  return 0
}

# auto — 두 걸음은 매 세션, 설치는 지문이 어긋날 때만 (claude-config 0009 · 0010):
#   ① 원격을 당긴다 — ff-only, main 체크아웃일 때만. 로컬을 다치게 하지 않는다:
#      갈라졌거나 오프라인이면 그대로 두고 **사유까지** 말한다. 「매 세션 풀부터」가 여기로 들어온다.
#   ② 홈 규범·훅 배선을 새로 민다 — 멱등·싼 것이라 매 세션.
#   ③ 선언 지문이 어긋날 때만 깐다 — 설치의 무거움(npm ci)이 선언 바뀐 세션에만 든다.
# ⚠ 리모트도 같은 세 걸음이다 (0010). 옛 판(「컨테이너가 새로 떠 무조건 깐다」)은 맨
#   컨테이너 전제였는데 환경 이미지가 서면서 뒤집혔다 — 도구·venv·지문은 이미지 시점에
#   실려 오고 코드만 세션마다 최신이라, 지문이 「이미지가 낡았나」를 가른다. 맨
#   컨테이너에서도 옳다: 지문 파일이 없으면 어긋남이라 그대로 설치로 간다.
if [ "$MODE" = auto ]; then
  # ⚠ **초를 같이 찍는다.** 왕복이 원래 느린 자리가 있다 — 실측 2026-09-09 회사 PC:
  #   성공한 `git fetch` 가 6.9초, 훅의 실패한 pull 이 하나당 6.3초였다. 두 숫자가 같아서
  #   **느린 것과 막힌 것이 시간으로는 안 갈린다** — 사유가 가르고, 초는 그 사유가 「원래
  #   이만큼」인지 「여느 때와 다른지」를 말해 준다.
  # ⚠ 그래서 **타임아웃을 안 씌운다.** 정상이 7초인 자리에서 5초로 자르면 되던 당김까지
  #   실패로 찍힌다 — 진단을 세우려다 없던 고장을 만드는 꼴이다.
  # ⚠ **기다리지도 않는다 — 배경으로 띄우고 결과는 다음 세션이 본다** (0043). 회사 망에서는 당김 하나가
  #   6~7초이고 세션 시작에 둘이 서는데, 확장이 초기화를 60초만 기다려 그 초가 곧 죽는 자리였다.
  #   당긴 것이 이 세션에 안 보이는 값을 치른다 — 규범·선언이 바뀐 커밋은 **다음 세션**부터 선다.
  #   진 사유는 `.git/claude-pull.log` 에 남고 다음 세션이 그것을 말한다 — 성공은 빈 파일이라 조용하다.
  #   stdout·stderr·stdin 을 다 떼어야 한다 — 하나라도 훅의 파이프를 물고 있으면 Claude Code 가
  #   그 자식이 끝날 때까지 훅을 기다려 배경으로 뺀 뜻이 없어진다.
  pull_ff() {  # pull_ff <저장소> — main 체크아웃일 때만, 빨리감기로만, 배경에서
    [ -e "$1/.git" ] || return 0
    [ "$(git -C "$1" symbolic-ref --short -q HEAD 2>/dev/null)" = main ] || return 0
    _gd="$(git -C "$1" rev-parse --absolute-git-dir 2>/dev/null)" || return 0
    _lg="$_gd/claude-pull.log"
    # ⚠ **원문은 경고를 내기 전에 옆에 둔다** (#38). 아래 `: > "$_lg"` 가 같은 실행에서 로그를
    #   비우므로, 사람이 이 한 줄을 한 번 읽고 나면 사유의 원문이 사라진다 — `git_why` 가 든
    #   160자는 **화면의 값**이고 원문은 파일의 값이다. 다음 성공이 그 파일을 걷는다:
    #   당김이 성공하면 로그가 비어 이 갈래의 else 로 오고, 그때가 곧 「이제 안 진다」이다.
    _lf="$_gd/claude-pull.last-fail"
    if [ -s "$_lg" ]; then
      cp "$_lg" "$_lf" 2>/dev/null || true
      echo "$(basename "$1"): ⚠ 지난 세션의 원격 당김이 졌다 — $(git_why "$(cat "$_lg")") · 원문 $_lf"
    else
      rm -f "$_lf" 2>/dev/null || true
    fi
    pull_due "$1" || return 0
    : > "$_lg" 2>/dev/null || true
    ( git -C "$1" pull --ff-only -q >"$_lg" 2>&1 </dev/null & )
  }
  # 저장소가 제 세션 시작 일을 두는 자리 — **있으면 부르고 없으면 조용하다.**
  # ⚠ **몸통은 무엇을 할지 모른다.** 기전만 여기 살고 정책은 저장소가 든다 — 그래서 쓰는
  #   저장소가 늘어도 이 자리는 안 낡는다. 목록을 안 들므로 더할 때 고칠 자리도 없다.
  # ⚠ **여기 두는 까닭 — `.claude/settings.json` 은 배포가 통째로 덮는 파일이다**
  #   (`deploy.repofiles.conf`). 저장소 제 훅을 거기 등록하면 **다음 배포가 지운다** — 실측
  #   2026-09-17: 아뜰리에가 거기 둔 훅이 배포 한 번에 사라졌다(그 저장소 61edde2). 그 세션은
  #   claude-config 를 안 붙이고 있어 그 파일이 관리 대상인 줄 알 길이 없었다. **자리가 없어서
  #   난 사고라 자리를 낸다.**
  # ⚠ **진다고 세션을 안 죽인다.** 저장소 제 일이라 몸통이 그것으로 멈출 까닭이 없다 — 사유만
  #   내고 간다. 그래서 `set -e` 가 없어도 `||` 로 명시해 둔다.
  # ⚠ **타임아웃을 안 씌운다** — 당김에 안 씌우는 것과 같은 결이다(위 ⚠). 대신 오래 끄는 손은
  #   세션 시작을 그만큼 늦추므로 **막는 것은 저장소 몫**이다.
  # ⚠ **auto 에만 선다.** 이 자리의 뜻이 「당김이 설 수 있는 꼴로 만든다」라 당김이 없는
  #   갈래에는 지킬 것이 없다.
  run_repo_start() {
    _rs="$PROJECT_DIR/.claude/hooks/repo-start.sh"
    [ -f "$_rs" ] || return 0
    sh "$_rs" || printf '  ! repo-start.sh 가 졌다 — 저장소 제 일이라 넘어간다
' >&2
  }
  wire_commit_hooks  # 당김 앞이다 — 망이 느리거나 훅이 잘려도 게이트만은 선다 (#31)
  run_repo_start     # 당김 앞이다 — 저장소가 제 나무를 당김이 설 수 있는 꼴로 만든다
  pull_ff "$PROJECT_DIR"
  [ -n "$CONFIG_ROOT" ] && [ "$CONFIG_ROOT" != "$PROJECT_DIR" ] && pull_ff "$CONFIG_ROOT"
  deploy_home_norms  # 당김이 배경이라 이번엔 지난 판을 민다 — 방금 당긴 것은 다음 세션이 민다 (0043)
  deploy_personal auto  # 가벼운 것만 — git 신원 · 슬러그 · 값이 바뀐 개인 키
  plant_session_state  # 지문 게이트 앞이다 — 심겼나·신뢰는 선언 지문과 무관한 명제다
  wire_python_path   # 지문 게이트 앞이다 — 배선은 설치의 사건이 아니라 세션의 상태다 (0011)
  # ── 낡음 게이트 — **선언이 그대로여도 도구는 낡는다** ────────────────────────
  # ⚠ 지문은 「선언이 바뀌었나」를 재지 「도구가 낡았나」를 안 잰다. 그래서 선언을 안 고치는
  #   기계(집·회사 PC)에서는 한 번 깔린 도구가 **영영 안 올라갔다** — 낡은 줄도 모르고 돈다.
  # ⚠ **표식이 없으면 안 민다. 표식만 남긴다.** 컨테이너는 세션마다 새로 나서 표식이 늘
  #   없는데, 거기서 밀면 **매 세션 수십 초를 물어야 한다.** 그리고 그 자리에서는 밀 까닭도
  #   약하다: 도구가 이미지만큼만 낡았고 이미지는 이 훅이 관리하는 것이 아니다.
  #   영속 기계는 표식이 남아 쌓이므로 제때 낡고, 그때 한 번 민다.
  UPGRADE=""
  if [ ! -f "$FRESH" ]; then
    : > "$FRESH" 2>/dev/null || true
  elif [ -n "$(find "$FRESH" -mtime "+$UPGRADE_DAYS" 2>/dev/null)" ]; then
    UPGRADE=1
    echo "$PROJECT_NAME: 도구를 최신으로 민다 (마지막 밀기가 ${UPGRADE_DAYS}일을 넘었다)"
  fi

  # ── 지문 게이트 — **둘로 갈린다** (#43). 전역형 도구는 기계 하나에 서므로 지문도 하나고,
  #    저장소 지문이 어긋나도 전역을 다시 훑을 까닭이 없다(그 반대도 같다). 갈려 있지 않던
  #    판에서는 저장소 하나의 선언이 바뀌면 그 세션이 전역 다섯을 통째로 다시 물었다.
  # ⚠ 낡음(UPGRADE)은 둘 다 민다 — 「도구가 낡았나」는 어느 층에도 같이 걸리는 명제다.
  DO_GLOBAL=""; DO_REPO=""
  { [ -z "$UPGRADE" ] && [ "$(global_fingerprint)" = "$(cat "$GSTAMP" 2>/dev/null)" ]; } || DO_GLOBAL=1
  { [ -z "$UPGRADE" ] && [ "$(decl_fingerprint)"   = "$(cat "$STAMP"  2>/dev/null)" ]; } || DO_REPO=1
  if [ -z "$DO_GLOBAL" ] && [ -z "$DO_REPO" ]; then
    # 침묵하되 실패까지 삼키지는 않는다 — 지난 설치의 실패가 남아 있으면 **사유까지** 알린다.
    # 다시 깔지는 않는다: 막힌 자리(예: 내려받기가 막힌 망)는 다시 깔아도 또 막혀,
    # 재시도가 매 세션 비용만 된다. 다시 까는 손은 deploy.ps1·--install 이 든다.
    # ⚠ **stdout 이다.** SessionStart 훅에서 모델의 문맥에 들어가는 것은 stdout 뿐이고 stderr 는
    #   기록에만 남는다 — 종전엔 이 줄이 stderr 라 네 세션 연속 아무도 못 읽었다(실측 2026-09-05:
    #   npm ci 실패가 남은 채 commitlint 없는 커밋이 넷 지나갔다). 사유를 같이 찍는 까닭도 같다 —
    #   「파일을 열어 보라」는 말은 안 열린다.
    # ⚠ **전역 갈래의 실패도 같이 낸다** (#43). 그쪽은 기계 한 자리에 적히므로, 여기서 안 읽으면
    #   전역형 도구가 못 깔린 채로 도는 저장소는 사유를 아무 데서도 못 본다.
    if [ -s "$FAILS" ] || [ -s "$GFAILS" ]; then
      echo "$PROJECT_NAME: ⚠ 지난 설치에 실패가 남아 있다 — deploy.ps1 이나 --install 로 다시 깐다. 사유:"
      # 하나가 없을 때 awk 가 그 자리에서 죽어 뒤엣것을 안 읽는다 — 파일마다 따로 부른다
      for _ff in "$FAILS" "$GFAILS"; do
        [ -s "$_ff" ] && awk -F'\t' '{printf "  · %s — %s\n", $1, $2}' "$_ff" 2>/dev/null
      done
    fi
    _gr="$(global_rule_reason)"
    [ -n "$_gr" ] && echo "$PROJECT_NAME: ⚠ 전역 규율 — $_gr"
    exit 0
  fi
  MODE=install   # 선언이 어긋났거나 도구가 낡았다 — 이 세션에서 바로 깐다. 지문은 설치 끝(⑧)에 굳는다
fi

if [ "$MODE" = install ]; then

  # ── 갈래 둘 — **전역은 기계에 한 번, 저장소는 배선만** (#43) ────────────────────
  #    auto 는 위 지문 게이트가 이미 정했다. 인자로 온 자리는 여기서 정한다:
  #      --install-global                    전역만          ← deploy.ps1 이 고리 **앞에** 한 번
  #      --install + CLAUDE_CONFIG_DEPLOYING 저장소만        ← deploy.ps1 이 고리 **안에서**
  #      --install (그 표식 없이)            전역 + 저장소   ← 리모트 Setup script. 지금 꼴 그대로
  #    ⚠ **리모트를 안 가른다.** 거기는 `deploy.ps1` 이 없어 `--install` 하나가 전부라, 가르면
  #      전역형 도구를 아무도 안 깐다. 표식이 곧 「위에서 갈라 부르고 있다」는 뜻이다.
  case "$ASKED" in
    install-global) DO_GLOBAL=1; DO_REPO="" ;;
    install)        DO_REPO=1
                    if [ -n "${CLAUDE_CONFIG_DEPLOYING:-}" ]; then DO_GLOBAL=""; else DO_GLOBAL=1; fi ;;
    *)              DO_GLOBAL="${DO_GLOBAL:-}"; DO_REPO="${DO_REPO:-}" ;;
  esac

  # ── PC 에서 밖(설치기 · 사람)이 `--install` 로 불렀으면 — 개인 칸을 세우고 `deploy.ps1` 에 넘긴다 ──
  # ⚠ **고리를 끊는 표식이 있다.** `deploy.ps1` 은 이 훅을 저장소마다 `--install` 로 부르는 자리라, 여기서
  #   다시 그것을 부르면 고리다. 그 표식(`CLAUDE_CONFIG_DEPLOYING`)은 deploy.ps1 이 세운다 — 있으면 저장소
  #   하나의 설치로 간다. 명시된 `--install` 만 탄다: 세션(auto)이 지문 어긋남으로 여기 온 판에서 배포
  #   전체를 돌리면 세션이 그만큼 멎는다. 리모트는 deploy.ps1 이 없어 이 갈래를 안 탄다.
  # ⚠ **종료코드는 deploy 의 것이다.** 옛 부트스트랩이 그것을 안 재 「완료」를 찍고 0 으로 끝난 자리가
  #   있었다(실측 2026-09-07 · deploy 가 첫 MCP 조회에서 죽은 자리) — 부재가 통과로 읽히는 그 자리다.
  if [ "$ASKED" = install ] && [ "$OS" = windows ] && [ -z "${CLAUDE_CONFIG_DEPLOYING:-}" ] &&
     [ -n "$CONFIG_ROOT" ] && [ -f "$CONFIG_ROOT/deploy.ps1" ]; then
    deploy_personal install
    echo "$PROJECT_NAME: deploy.ps1 에 넘긴다 — 저장소·메모리·MCP 를 밀고 각 저장소 훅을 --install 로 부른다"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$CONFIG_ROOT/deploy.ps1")" -Yes
    _drc=$?
    [ "$_drc" -eq 0 ] || echo "$PROJECT_NAME: ⚠ deploy.ps1 이 exit $_drc 로 끝났다 — 위 진단의 ❌ 줄이 곧 고칠 자리"
    exit "$_drc"
  fi

  # 실패는 삼키되 까닭까지 버리지는 않는다 — 진단이 ❌ 줄에 사유를 이어 붙인다.
  # 지난 실패는 **지우기 전에 찍는다** — 안 그러면 「무엇이 왜 실패했었나」가 성공한 재설치와
  # 함께 사라져 다시 못 잰다(실측 2026-09-05: --install 이 성공하며 npm ci 의 원래 사유가 증발했다).
  # ⚠ **제가 이번에 안 도는 층의 기록은 안 지운다** (#43). 저장소 갈래가 전역 기록을 비우면
  #   전역형 도구가 못 깔린 사유가 **깔아 보지도 않은 채** 사라진다 — 위 「지우기 전에 찍는다」
  #   와 같은 결이고, 지우는 자와 채우는 자를 층마다 맞춘다.
  for _ff in ${DO_REPO:+"$FAILS"} ${DO_GLOBAL:+"$GFAILS"}; do
    if [ -s "$_ff" ]; then
      echo "$PROJECT_NAME: 지난 설치 실패 — 이번에 다시 깐다:"
      awk -F'\t' '{printf "  · %s — %s\n", $1, $2}' "$_ff" 2>/dev/null
    fi
    mkdir -p "$(dirname "$_ff")" 2>/dev/null; : > "$_ff" 2>/dev/null
  done
  try() {   # try <이름> <명령…> — 안 죽고, 실패하면 출력 한 줄을 사유로 남긴다
    # ⚠ **스택 프레임은 사유가 아니다.** 끝줄을 그대로 집으면 node 계열이 뱉는
    #   `    at ChildProcess…` 한 줄만 남아, 기록이 있는데 원인이 없다 — 다음 사람이
    #   실패를 처음부터 재현해야 한다. 프레임을 걷고 남은 끝줄을 집되, 전부 프레임이면
    #   그때는 끝줄이라도 남긴다(빈 사유보다 낫다).
    _n="$1"; shift
    _o="$(mktemp)"; _r=0
    "$@" >"$_o" 2>&1 || { _r=$?
      _lines="$(grep -v '^[[:space:]]*$' "$_o" 2>/dev/null)"
      _msg="$(printf '%s\n' "$_lines" | grep -v '^[[:space:]]*at [^[:space:]]' | tail -1)"
      [ -n "$_msg" ] || _msg="$(printf '%s\n' "$_lines" | tail -1)"
      printf '%s\t%s\n' "$_n" "$(printf '%s' "$_msg" | cut -c1-160)" >> "$FAILS" 2>/dev/null; }
    # 마지막 출력 줄은 부르는 쪽이 판정으로 쓴다 — 뒷길이 「받았다」인지 「이미 있다」인지는 이 줄에만
    # 있고, 삼키면 초만 남아 헛받기가 안 보인다(#58). 설치 갈래에서만 도는 자리라 `tail` 하나는 싸다.
    TRY_LAST="$(tail -1 "$_o" 2>/dev/null)"
    rm -f "$_o"
    return "$_r"
  }
  # ── nogo <이름> <사유> — **전제가 안 맞아 설치 갈래를 못 탔다**를 `try` 와 같은 형식으로
  #    적고 1 을 낸다. `try` 의 형제다: 저쪽은 돌려 보고 진 사유를, 이쪽은 돌려 보지도
  #    못한 사유를 남긴다.
  # ⚠ **전제 가드는 `try` 앞에서 빠져나간다** — 그래서 「실패를 삼키되 사유는 남긴다」가
  #   이 자리에만 안 걸렸다. 사유 없는 ❌ 는 다음 사람에게 부재와 같다: 진단이 「안 닿는다」
  #   만 내고 **무엇을 갖추면 닿는지는 아무 데도 없다** (실측 2026-09-08: npm 없는 VDI 에서
  #   markdownlint-cli2 가 그렇게 꺼졌다). 부재를 통과로 안 읽는 것과 같은 결이다.
  nogo() {
    printf '%s\t%s\n' "$1" "$2" >> "$FAILS" 2>/dev/null
    return 1
  }

  # ── ①② 커밋 훅 배선 + 전역 규범·영역 룰·에이전트·씨앗을 홈으로 — 가볍고 안 죽는 것이
  #      맨 앞이고, **그 안에서도 안 죽는 쪽이 더 앞이다.** 배선은 로컬 한 줄이라 뒤따르는
  #      복사가 무엇으로 지든 살아남는다 (#31).
  #      몸통은 wire_commit_hooks · deploy_home_norms 각 한 벌이다 — PC 매 세션 갈래(auto)와
  #      같은 것을 같은 차례로 민다 ──
  #      ⚠ **저장소 몫이라 `DO_REPO` 아래 선다** (#43). `--install-global` 은 저장소를 안 든다 —
  #        같은 배포 안에서 `deploy.ps1` 의 저장소 고리가 저장소마다 이것을 이미 민다.
  if [ -n "$DO_REPO" ]; then
    wire_commit_hooks
    deploy_home_norms
    deploy_personal auto  # 가벼운 것만 — 무거운 것(clone · 홈 설정 덮기)은 위 PC 분기가 이미 들었다

    # ── ②′ 전역 SessionStart 훅 · 신뢰 — 몸통은 위 plant_session_state 한 벌이다.
    #    auto 가 지문 게이트 앞에서 이미 부르지만, `--install` 로 곧장 들어온 갈래
    #    (deploy.ps1 · 리모트 Setup script)는 그 자리를 안 지나므로 여기서도 부른다.
    #    멱등이라 겹쳐 불려도 항목은 하나다 (0028 이 쟀다).
    plant_session_state
  fi

  # ── ③ 파이썬 축 — requirements.txt 의 존재가 곧 선언이다. venv 에 깐다 ──
  #      **프로젝트 축이라 저장소마다 돈다** — 실물이 저장소 안 `.venv` 다 (#43).
  if [ -n "$DO_REPO" ] && [ -f "$PROJECT_DIR/requirements.txt" ]; then
    # 판 일치 — 선언(probe = python-version)이 들면 **그 판으로** venv 를 만든다.
    # 개발 세계의 판(선언 값)과 다른 판으로 재면 같은 코드가 두 세계에서 다르게
    # 판정된다 — 바닥(최저선)이 아니라 일치다. 컨테이너에 그 판이 없으면 uv 로
    # 내려받는다 (실측 2026-08-24: 2초. 그리고 기본 python3 이 낡은 판이면 코드가
    # import 부터 죽는데 의존성 프로브는 초록이었다 — 부재가 통과로 읽히는 자리).
    PY_TGT=0; PY_TGT_BY=""; PY_TGT_STR=""
    for _pf in "$GCONF" "$PCONF"; do
      for _pn in $(decl_sections "$_pf"); do
        [ "$(decl_get "$_pf" "$_pn" probe)" = python-version ] || continue
        PY_TGT_STR="$(decl_get "$_pf" "$_pn" probe-target)"
        PY_TGT="$(ver_num "$PY_TGT_STR")"; PY_TGT_BY="$_pn"
      done
    done
    if [ "$PY_TGT" -gt 0 ]; then
      if [ "$(py_num "$PY_CMD")" != "$PY_TGT" ]; then
        # ① PATH 에 그 판 이름이 이미 있나 — uv 가 깐 것도 다음 세션부턴 이 이름으로 선다
        _ma="${PY_TGT_STR%%.*}"; _mi="${PY_TGT_STR#*.}"; _mi="${_mi%%.*}"
        if [ "$(py_num "python${_ma}.${_mi}")" = "$PY_TGT" ]; then
          PY_CMD="python${_ma}.${_mi}"
        # ①′ windows py 런처 — python.org·winget 설치는 `python3.14` 같은 이름을 안 만들고
        #    `py -3.14` 런처에만 등록한다(실측 2026-08-26: winget 설치 직후 ①은 못 찾았다).
        #    런처가 내주는 실행 파일 경로를 잡아야 venv/-m 호출에 단일 실행형으로 쓸 수 있다.
        elif [ "$OS" = windows ] && command -v py >/dev/null 2>&1 &&
             py "-${_ma}.${_mi}" -c '' >/dev/null 2>&1; then
          _found="$(py "-${_ma}.${_mi}" -c 'import sys; print(sys.executable)' 2>/dev/null)"
          [ -n "$_found" ] && [ "$(py_num "$_found")" = "$PY_TGT" ] && PY_CMD="$_found"
        # ② uv 로 내려받는다 — 패치판은 uv 목록의 최신이 정한다 (선언은 부판까지만 문다).
        #    낡은 uv 는 낡은 목록으로 rc 판까지만 알아(실측 2026-08-24: 0.8 이 3.14.0rc2
        #    를 최신으로 알았다) 받기 전에 uv 부터 갱신을 시도한다. self update 는
        #    GitHub API 라 프록시 제한에 걸리고(rate limit 실측) astral.sh 는 403 —
        #    PyPI 경로가 뒤를 받친다. venv 에 물린 파이썬은 --user 를 거부하므로
        #    시스템 해석기를 명시한다. 셋 다 막히면 있는 목록으로 간다.
        elif command -v uv >/dev/null 2>&1; then
          uv self update >/dev/null 2>&1 ||
            /usr/bin/python3 -m pip install -q --user --upgrade uv >/dev/null 2>&1 || true
          try "$PY_TGT_BY" uv python install "$PY_TGT_STR" || true
          _found="$(uv python find "$PY_TGT_STR" 2>/dev/null)"
          [ -n "$_found" ] && [ "$(py_num "$_found")" = "$PY_TGT" ] && PY_CMD="$_found"
        fi
      fi
      # 고른 해석기의 심링크를 실경로로 편다 — uv 의 shim(~/.local/bin)이 venv 의
      # home 으로 앉으면 표준 라이브러리를 못 찾아 venv 가 깨진다 (실측 2026-08-24:
      # encodings 부재로 즉사). 윈도우는 venv 를 복사로 만들어 이 함정이 없다.
      if [ "$OS" = linux ]; then
        _rp="$(command -v "$PY_CMD" 2>/dev/null)"
        [ -n "$_rp" ] && _rp="$(readlink -f "$_rp" 2>/dev/null)" &&
          [ -x "$_rp" ] && PY_CMD="$_rp"
      fi
      if [ "$(py_num "$PY_CMD")" != "$PY_TGT" ]; then
        printf '%s\t%s\n' "$PY_TGT_BY" \
          "선언한 판($PY_TGT_STR)을 못 구했다 — PATH 에 없고 uv 로도 못 받았다. $("$PY_CMD" -V 2>&1 | tail -1) 로 선다" >> "$FAILS"
      else
        # 다른 판으로 이미 선 venv 는 그대로 두면 프로브만 빨갛다 — 다시 만든다
        _vv=""; [ -x "$VENV_PY" ] && _vv="$(py_num "$VENV_PY")"
        [ -n "$_vv" ] && [ "$_vv" != "$PY_TGT" ] && rm -rf "$VENV"
      fi
    fi
    # ── venv 는 **폴더가 서 있나가 아니라 pip 이 닿나**로 잰다. 반쯤 선 것은 지우고 다시 만든다.
    #    자(`venv_ready`)는 이 파일 앞머리에 있다 — `--needs-install` 이 같은 것을 묻는다.
    if ! venv_ready; then
      [ -d "$VENV" ] && rm -rf "$VENV"
      # ⚠ **stdin 을 물려준다.** venv 는 pip 을 깔 때 제 안에서 파이썬을 한 번 더 띄우고, 그때
      #   부모의 표준입력 손잡이를 복제한다. 창 없이 띄워진 사슬(`CreateNoWindow`)을 타고 오면
      #   그 손잡이가 없어 `[WinError 6]` 으로 죽는다 — 설치 화면이 엔진을 그렇게 띄웠다.
      #   **부르는 자리마다 고치면 다음 런처에서 또 만난다** — 그래서 여기서 막는다.
      #   `/dev/null` 은 윈도우에서 NUL 로 서서 어느 부모 밑에서도 성한 손잡이가 된다
      #   (실측 2026-09-10: 닫힌 stdin 아래서 죽던 것이 이 한 자로 pip 까지 완주했다).
      _vt0=$SECONDS
      if try "venv" "$PY_CMD" -m venv "$VENV" </dev/null; then
        printf '  · venv — 만들었다 (%s초)\n' "$((SECONDS - _vt0))"
      else
        printf '  · venv — 못 만들었다 (%s초)\n' "$((SECONDS - _vt0))"
      fi
    fi
    # 방금 만든 venv 를 프로브가 보게 한다 — VENV_PY 는 스크립트 첫머리(venv 가 아직
    # 없던 때)에 굳었다. 안 풀면 첫 회 진단이 맨 해석기를 재서 헛빨강을 낸다(실측
    # 2026-08-24: 새 venv 인데 pyyaml ❌).
    VENV_PY="$VENV_BIN/python"; [ -x "$VENV_PY" ] || VENV_PY="$VENV_BIN/python.exe"
    if venv_ready; then
      _pip="$VENV_BIN/pip"; [ -x "$_pip" ] || _pip="$VENV_BIN/pip.exe"
      _pt0=$SECONDS
      if try "파이썬 의존성" "$_pip" install --quiet --disable-pip-version-check \
           -r "$PROJECT_DIR/requirements.txt"; then
        printf '  · 파이썬 의존성 — 깔았다 (%s초)\n' "$((SECONDS - _pt0))"
      else
        printf '  · 파이썬 의존성 — 못 깔았다 (%s초)\n' "$((SECONDS - _pt0))"
      fi
    else
      # ⚠ **조용히 건너뛰지 않는다.** 옛 판은 pip 이 없으면 아무 말 없이 지나갔고, 그래서
      #   다음 세션은 **실패 줄조차 못 본 채** 의존성만 꺼진 상태로 돌았다 — 부재가 통과로
      #   읽히는 그 자리다. 사유가 있어야 다음 사람이 무엇을 갖추면 닿는지 안다.
      nogo "파이썬 의존성" "venv 에 pip 이 없다 — 위 「venv」 사유를 본다. 그것이 서야 requirements.txt 를 깐다" || true
    fi
    # 세션 셸 배선은 wire_python_path 한 벌이다 — auto 매 세션 갈래와 같은 것을 민다 (0011)
    wire_python_path
  fi

  # ── ④ 노드 축 — package-lock.json 의 존재가 곧 선언이다. install 이 아니라 ci 다:
  #      잠금을 추적하는 이유가 "판이 갈리면 게이트를 못 믿는다"라서다 ──
  #      프로젝트 축이라 저장소마다 돈다 — 실물이 저장소 안 `node_modules` 다 (#43).
  if [ -n "$DO_REPO" ] && [ -f "$PROJECT_DIR/package-lock.json" ] && command -v npm >/dev/null 2>&1; then
    _nt0=$SECONDS
    if ( cd "$PROJECT_DIR" && try "노드 의존성" npm ci --no-audit --no-fund --silent ); then
      printf '  · 노드 의존성 — 깔았다 (%s초)\n' "$((SECONDS - _nt0))"
    else
      printf '  · 노드 의존성 — 못 깔았다 (%s초)\n' "$((SECONDS - _nt0))"
    fi
  fi

  # ── ⑤ 선언 도구 — 프로브 → 설치 → 배선 → 재프로브. 판정은 §진단 한 자리가 낸다 ──
  install_tool() {  # install_tool <선언파일> <이름>
    _f="$1"; _t="$2"
    case "$(decl_get "$_f" "$_t" install)" in
      github-release-binary)
        _repo="$(decl_get "$_f" "$_t" repo)"; _bin="$(decl_get "$_f" "$_t" bin)"
        if [ "$OS" = linux ]; then _asset="$(decl_get "$_f" "$_t" asset-linux)"
        else _asset="$(decl_get "$_f" "$_t" asset-windows)"; fi
        [ -n "$_repo" ] && [ -n "$_asset" ] && [ -n "$_bin" ] ||
          { nogo "$_t" "선언에 repo·asset-$OS·bin 중 빠진 것이 있다"; return 1; }
        _url="https://github.com/$_repo/releases/latest/download/$_asset"
        case "$_asset" in
          *.tar.gz)   # 리눅스 — 풀어서 /usr/local/bin 에 놓는다
            { [ "$OS" = linux ] && [ -w /usr/local/bin ]; } ||
              { nogo "$_t" "$_asset 는 tar.gz 인데 여기는 $OS 이거나 /usr/local/bin 에 쓸 권한이 없다"; return 1; }
            _tgz="$(mktemp)"
            if try "$_t" curl -sSfL --retry 3 --max-time 180 -o "$_tgz" "$_url"; then
              try "$_t" tar xzf "$_tgz" --strip-components=1 -C /usr/local/bin "${_asset%.tar.gz}/$_bin" &&
                chmod +x "/usr/local/bin/$_bin" 2>/dev/null
            fi
            rm -f "$_tgz" ;;
          *.zip)      # 윈도우 — Git Bash 에 unzip 이 없을 수 있어 PowerShell 로 풀고 $HOME/bin 에 놓는다
            _work="$(mktemp -d)"; mkdir -p "$HOME/bin"
            if try "$_t" curl -sSfL --retry 3 --max-time 180 -o "$_work/pkg.zip" "$_url"; then
              powershell.exe -NoProfile -Command \
                "Expand-Archive -Force -Path '$(cygpath -w "$_work/pkg.zip")' -DestinationPath '$(cygpath -w "$_work")'" \
                >/dev/null 2>&1
              _found="$(find "$_work" -name "$_bin.exe" -type f 2>/dev/null | head -1)"
              [ -n "$_found" ] && cp "$_found" "$HOME/bin/$_bin.exe"
            fi
            rm -rf "$_work" ;;
          *) nogo "$_t" "$_asset — 모르는 자산 꼴이다(푸는 갈래는 .tar.gz · .zip 둘뿐)"; return 1 ;;
        esac ;;
      npm-global)
        _pkg="$(decl_get "$_f" "$_t" package)"
        [ -n "$_pkg" ] || { nogo "$_t" "선언에 package 가 없다"; return 1; }
        command -v npm >/dev/null 2>&1 ||
          { nogo "$_t" "npm 이 없다 — 노드를 깔면 다음 설치가 깐다"; return 1; }
        try "$_t" npm install -g --no-audit --no-fund --silent "$_pkg" || true
        # 브라우저는 패키지와 따로 온다 — 선언이 browsers 를 들 때만, 컨테이너가 미리
        # 받아 둔 자리(skip-browsers-env)가 없을 때만 받는다.
        _br="$(decl_get "$_f" "$_t" browsers)"
        _skipname="$(decl_get "$_f" "$_t" skip-browsers-env)"
        _skipval=""; [ -n "$_skipname" ] && _skipval="${!_skipname:-}"
        if [ -n "$_br" ] && [ -z "$_skipval" ] && command -v "$_pkg" >/dev/null 2>&1; then
          # ⚠ **뒷길(browsers-fallback)이 선언돼 있으면 제 CDN 을 아예 안 부른다.**
          #   옛 판은 「첫 시도」로 한 번 불렀다. 그런데 그 명령은 받기 전에 **제 판과 안 맞는
          #   브라우저를 「쓸모없다」며 먼저 지운다** — 받는 길이 막힌 자리에서는 지우기만 하고
          #   못 받아 **멀쩡히 있던 것까지 없어진다.** 실측 2026-09-11(리모트 컨테이너):
          #   이미지가 미리 들고 온 크로미움이 그 한 번에 사라졌고, 새 판은 403 이라 못 받아
          #   그림 굽기가 그 세션 내내 죽었다.
          #   **뒷길이 선언돼 있다는 것은 받는 길이 따로 서 있다는 뜻이다** — 여기서 헛되이 걸
          #   값이 없고, 판을 맞추는 값도 없다(뒷길로 받은 것은 실행 파일을 직접 가리켜 쓰므로
          #   playwright 의 판과 어긋나도 된다). 그래서 **뒷길이 없을 때만** 이 길로 간다.
          if [ -z "$(decl_get "$_f" "$_t" browsers-fallback)" ]; then
            try "$_t" "$_pkg" install $_br || true
          fi
        fi ;;
      apt-package)   # 배포판 저장소에서 깐다 — 자산 이름에 판이 안 물려 선언이 안 낡는다.
                     # github-release-binary 가 못 쓰이던 까닭이 이 갈래에는 없다.
        _pkg="$(decl_get "$_f" "$_t" package)"
        { [ "$OS" = linux ] && [ -n "$_pkg" ] && command -v apt-get >/dev/null 2>&1; } ||
          { nogo "$_t" "apt 갈래를 못 탄다 — 여기는 $OS 이거나 선언에 package 가 없거나 apt-get 이 없다"; return 1; }
        # 권한이 없으면 물러난다 — **sudo 를 부르지 않는다.** 물어볼 사람이 없는 자리다.
        # ⚠ 물러나되 **조용히는 아니다.** 안 부르는 것과 안 말하는 것은 다른 명제다 —
        #   사유를 남겨도 sudo 는 안 불리고, 남기지 않으면 진단이 「안 닿는다」만 낸다.
        [ "$(id -u)" = 0 ] ||
          { nogo "$_t" "루트가 아니라 apt 로 못 깐다 — sudo 는 부르지 않는다"; return 1; }
        # 목록이 신선하면 한 걸음, 낡았으면 갱신하고 한 번 더. 갱신을 앞에 세우면 매 설치가
        # 느려지고, 아예 안 두면 이미지가 오래된 기계에서 영영 못 깐다.
        try "$_t" sh -c "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $_pkg ||
          { apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $_pkg; }" ;;
      winget)        # 윈도우 패키지 관리자 — **폴더째 와야 도는 도구**가 여기 산다.
                     # ⚠ `github-release-binary` 로는 못 깐다: 그 갈래는 자산 zip 에서 실행파일
                     #   **하나만** 꺼내 `$HOME/bin` 에 놓는데, 곁의 `lib/` 가 있어야 도는 물건은
                     #   그렇게 꺼내면 **깔린 것처럼 보이고 안 돈다** — 제일 나쁜 실패다.
                     # ⚠ 자산 이름에 판이 안 물려 선언이 안 낡는다 — `apt-package` 와 같은 값이다.
        _id="$(decl_get "$_f" "$_t" winget-id)"
        { [ "$OS" = windows ] && [ -n "$_id" ]; } ||
          { nogo "$_t" "winget 갈래를 못 탄다 — 여기는 $OS 이거나 선언에 winget-id 가 없다"; return 1; }
        command -v winget.exe >/dev/null 2>&1 ||
          { nogo "$_t" "winget 이 없다 — 옛 윈도우이거나 앱 설치 관리자가 안 깔렸다"; return 1; }
        # ⚠ **사용자 자리에 깐다** — 관리자 없이 서야 하는 것이 이 훅의 규율이다(apt 갈래가
        #   sudo 를 안 부르는 것과 같은 축).
        # ⚠ **`--source winget` 을 박는다.** 안 박으면 msstore 까지 훑다가 그쪽 인증서 오류로
        #   통째로 진다 — 실측 2026-09-15: `0x8a15005e` 로 설치가 아예 시작을 못 했다.
        # ⚠ **묻지 않게 한다** — 물어볼 사람이 없는 자리다.
        # ⚠ **깐 뒤 이 세션에서는 아직 PATH 에 안 걸린다** — winget 은 사용자 PATH 를 고치고
        #   그 값은 이미 뜬 셸에 안 온다. 다음 세션에서 선다. 그래서 **부르는 쪽이 winget 의
        #   링크 자리도 보게** 둔다(`scripts/build-setup-exe.ps1` 이 그렇게 한다).
        try "$_t" winget.exe install --id "$_id" --exact --source winget --scope user --accept-package-agreements --accept-source-agreements --disable-interactivity ;;
      project-axis) : ;;   # 설치 없음 — 판의 진본은 package.json·requirements.txt 다
      # ⚠ 모르는 갈래도 **조용한 무작동이다.** 선언에 `install` 을 빠뜨리거나 오타를 내면
      #   여기까지 와서 아무것도 안 하고 0 을 냈다 — 진단은 「안 닿는다」만 내고 선언이
      #   틀렸다는 말은 아무 데도 없었다. 이름을 그대로 되돌려 준다.
      *) nogo "$_t" "설치법(install)이 선언에 없거나 모르는 갈래다: $(decl_get "$_f" "$_t" install)"; return 1 ;;
    esac
  }
  browsers_ready() {  # browsers_ready <선언파일> <이름> — 브라우저는 패키지와 따로 온다
    # ⚠ **설치 안이 아니라 여기 서는 까닭.** 위 줄기는 `프로브 실패 → 설치`라, 패키지가
    #   한 번 깔린 뒤로는 설치가 영영 안 불린다 — 그런데 **패키지가 있다고 브라우저가
    #   있는 것이 아니다**(컨테이너가 새로 뜨면 브라우저만 사라진다). 그래서 프로브와
    #   무관하게 매 세션 한 번 댄다. 받을지 말지는 **스크립트가 스스로 가른다** —
    #   있으면 그대로 두고, 없으면 그때의 최신을 받는다.
    _f="$1"; _t="$2"
    _br="$(decl_get "$_f" "$_t" browsers)"; [ -n "$_br" ] || return 0
    _skipname="$(decl_get "$_f" "$_t" skip-browsers-env)"
    _skipval=""; [ -n "$_skipname" ] && _skipval="${!_skipname:-}"
    [ -z "$_skipval" ] || return 0
    _fb="$(decl_get "$_f" "$_t" browsers-fallback)"; [ -n "$_fb" ] || return 0
    # 경로는 **그 선언을 든 저장소** 기준이다(선언은 <저장소>/.claude/ 에 산다) — 그래서
    # 몸통은 무엇을 받는지도 어디서 받는지도 모른 채로 남는다.
    _fbroot="$(dirname "$(dirname "$_f")")"
    [ -f "$_fbroot/$_fb" ] || return 0
    _bt0=$SECONDS
    # 판정을 같이 싣는다 — 스크립트의 마지막 `[browser]` 줄(받았다 / 이미 있다). 초만 찍으면
    # 「받는 데 30초」와 「있는 것 확인에 30초」가 같은 얼굴이라 헛받기를 아무도 못 봤다(#58).
    if try "$_t" bash "$_fbroot/$_fb"; then
      printf '  · %s — 브라우저 뒷길 (%s초 · %s)\n' "$_t" "$((SECONDS - _bt0))" "${TRY_LAST#\[browser\] }"
    else
      printf '  · %s — 브라우저 뒷길이 졌다 (%s초 · %s)\n' "$_t" "$((SECONDS - _bt0))" "${TRY_LAST#\[browser\] }"
    fi
  }
  wire_tool() {  # wire_tool <선언파일> <이름> — node-link: 이름 해석이 되게 만든다
    _f="$1"; _t="$2"
    [ "$(decl_get "$_f" "$_t" wiring)" = node-link ] || return 0
    _mod="$(decl_get "$_f" "$_t" probe-target)"
    probe_tool node-resolvable "$_mod" && return 0
    _groot="$(npm root -g 2>/dev/null)"
    { [ -n "$_groot" ] && [ -d "$_groot/$_mod" ]; } || return 0
    # 전역 설치는 저장소 node_modules 밖이라 import 가 못 찾는다 — 저장소 안으로 건다.
    # ⚠ npm ci 가 node_modules 를 지우고 다시 만든다. 그래서 ④ 뒤에 선다.
    # ⚠ **스코프 패키지는 중간 폴더가 먼저 서야 한다** — `@scope/name` 은 링크 자리가
    #   `node_modules/@scope/name` 이라, 뿌리만 만들면 `ln` 이 조용히 진다.
    mkdir -p "$(dirname "$PROJECT_DIR/node_modules/$_mod")" 2>/dev/null
    if [ "$OS" = linux ]; then
      ln -sfn "$_groot/$_mod" "$PROJECT_DIR/node_modules/$_mod" 2>/dev/null || true
    elif [ ! -e "$PROJECT_DIR/node_modules/$_mod" ]; then
      # Git Bash 는 심링크를 못 건다 — 정션(관리자 권한 불요)으로 같은 효과를 낸다.
      # ⚠ 명령 전체를 한 문자열로 주면 cmd 인용이 깨진다(실측) — 낱개 인자 + //J 로 넘긴다.
      cmd //c mklink //J "$(cygpath -w "$PROJECT_DIR/node_modules/$_mod")" "$(cygpath -w "$_groot/$_mod")" \
        >/dev/null 2>&1 || true
    fi
    probe_tool node-resolvable "$_mod" && return 0
    # 이름 해석이 그래도 안 되면 소비자 계약(환경변수)으로 넘긴다 — 이름은 선언이 든다.
    _env="$(decl_get "$_f" "$_t" wiring-env)"
    # ⚠ **진입점을 손으로 찾지 않는다 — 폴더를 넘긴다.** `index.js` 는 추측이라 그 이름이
    #   아닌 패키지에서는 `[ -f ]` 가 빗나가 **배선이 조용히 안 섰다.** 진입점의 진본은 그
    #   패키지의 `package.json` 이고 그것을 읽는 자는 받는 쪽의 해석기다 — 폴더만 주면
    #   된다(소비자 예: 아뜰리에 `_check/_browser.mjs` 의 `moduleSpec` · 그 저장소 #337).
    _entry="$_groot/$_mod"
    if [ -n "$_env" ]; then
      # 이 훅 **안에서도** 곧바로 선다 — 아래 걸음이 이 값을 본다. 파일로만 내보내면
      # 다음 세션에서야 서고, 이번 세션의 뒷걸음은 배선 없이 돈다.
      export "$_env=$_entry"
      [ -n "${CLAUDE_ENV_FILE:-}" ] && echo "export $_env=\"$_entry\"" >> "$CLAUDE_ENV_FILE"
      if [ "$OS" = linux ] && [ -w /etc/profile.d ] 2>/dev/null; then
        printf 'export %s="%s"\n' "$_env" "$_entry" > "/etc/profile.d/${PROJECT_NAME}-${_t}.sh"
      fi
    fi
  }
  # ── 전역 자리의 배선 — **정션이 아니라 값 하나다** (#43).
  #    저장소 배선(`wire_tool`)은 `node_modules` 에 정션을 걸어 저장소 안에서 이름이 풀리게
  #    한다. 전역 갈래에는 걸 저장소가 없다 — 여기서 서야 하는 것은 바로 뒤의 브라우저 뒷길이
  #    「playwright 가 이미 브라우저를 들고 있나」를 **그 모듈에 물을 수 있게** 하는 것뿐이다.
  #    그 값의 이름은 선언이 든다(`wiring-env`) — 몸통은 여기서도 도구 이름을 모른다.
  wire_global() {  # wire_global <선언파일> <이름>
    _wf="$1"; _wn="$2"
    _we="$(decl_get "$_wf" "$_wn" wiring-env)"; [ -n "$_we" ] || return 0
    _wm="$(decl_get "$_wf" "$_wn" probe-target)"; [ -n "$_wm" ] || return 0
    _wr="$(npm root -g 2>/dev/null)" || return 0
    { [ -n "$_wr" ] && [ -d "$_wr/$_wm" ]; } || return 0
    export "$_we=$_wr/$_wm"
  }

  # ── ⑤ 전역형 도구 — **기계에 한 번이다** (#43) ─────────────────────────────────
  #    전역 선언과 작업 루트에 붙은 **모든 저장소의 전역형 선언**을 이름으로 합쳐, 같은 이름은
  #    한 번만 깐다. 브라우저 뒷길도 여기서 한 번.
  # ⚠ **옛 꼴은 이 걸음이 저장소 고리 안에 살았다.** 그래서 프로브 비용이 저장소 수에 비례했고
  #   (실측: 형제 여섯이면 전역형 프로브 35회), playwright 는 프로브가 「이 저장소 안에서
  #   import 되나」라 정션 **전**에 물어 늘 져서 `npm install -g` 가 저장소마다 되풀이됐다.
  #   설계는 「전역은 한 번, 저장소는 배선만」인데 구조가 그것을 안 들고 있었다 (#43).
  # ⚠ **프로브를 빼서 빨리 하지 않는다** — 「깔린 것과 닿는 것은 다른 명제」다(이 파일 머리말).
  #   줄인 것은 재는 일이 아니라 **묻는 횟수**다.
  # ⚠ **판정을 여기서 낸다.** 이 갈래는 아래 진단 절(저장소의 물음)을 안 지나므로, 여기서
  #   말하지 않으면 무엇이 섰는지 아무 데도 안 남는다 — 설치의 목표는 「깔기를 돌았다」가
  #   아니라 환경이 서 있다이다.
  GDOWN=0
  # ── 이 실행이 확인한 것을 적는다 — **캐시가 아니라 같은 실행의 인용문이다** (#57) ──────
  # ⚠ `CLAUDE_CONFIG_RUN` 은 배포 한 번을 가리키는 표식이고 그것을 세우는 자는 `deploy.ps1`
  #   하나다. 표식이 없으면(세션 auto · `--check` · 사람이 손으로 부른 설치) **아무것도 안
  #   적는다** — 안 적으면 아래 저장소 진단도 볼 것이 없어 지금처럼 매번 프로브한다.
  # ⚠ **✅ 만 적는다.** ❌ 를 적으면 저장소 진단이 안 선 도구를 「확인했다」로 읽는다.
  # ⚠ **이름과 프로브 대상을 함께 적는다.** 이름만 적으면 대상이 다른 선언(같은 이름, 딴
  #   모듈)이 같은 명제로 읽힌다 — 어긋나면 인용하지 않는 것이 규율이다.
  # ⚠ 줄의 꼴(`이름 \t 프로브대상 \t 표식`)은 읽는 자 `global_verified` 와 **한 벌이다** —
  #   한쪽만 고치면 인용이 조용히 끊기고, 끊긴 자리는 느려질 뿐이라 아무도 안 걸린다.
  gverified_put() {  # gverified_put <이름> <probe-target>
    [ -n "${CLAUDE_CONFIG_RUN:-}" ] || return 0
    printf '%s\t%s\t%s\n' "$1" "$2" "$CLAUDE_CONFIG_RUN" >> "$GVERIFIED" 2>/dev/null || true
    return 0
  }
  install_global() {
    _gseen=""; _gl="$(mktemp)"
    # 이번 실행의 명부는 **이번 실행이 처음부터 짓는다** — 이어 적으면 지난 실행에서 ✅ 였다가
    # 이번에 ❌ 인 도구가 옛 줄로 살아남는다. 표식이 없으면 파일에 손도 안 댄다.
    [ -z "${CLAUDE_CONFIG_RUN:-}" ] || : > "$GVERIFIED" 2>/dev/null || true
    global_conf_list > "$_gl" 2>/dev/null
    while IFS= read -r _gf; do
      [ -f "$_gf" ] || continue
      for _gn in $(decl_sections "$_gf"); do
        global_kind "$(decl_get "$_gf" "$_gn" install)" || continue
        case " $_gseen " in *" $_gn "*) continue ;; esac
        _gseen="$_gseen $_gn"
        # on-demand 는 안 깐다 — 부르는 자가 제 손으로 찾는다(선언 필드 표). 이름은 찍는다:
        # 안 찍으면 「선언했는데 왜 안 깔렸나」를 다음 사람이 훅에서 판다.
        if [ "$(decl_get "$_gf" "$_gn" on-demand)" = yes ]; then
          printf '  · %s — 필요할 때 깐다 (on-demand · %s)
' "$_gn" "$(decl_get "$_gf" "$_gn" called-by | cut -d' ' -f1)"
          continue
        fi
        # 밀 때는 프로브를 안 묻는다 — 「있나」와 「최신인가」는 다른 명제라, 있으면 건너뛰는
        # 규칙으로는 영영 안 올라간다. 같은 설치가 곧 밀기다(옛 고리와 같은 뜻).
        # 걸린 초는 줄 끝에 붙는다 (#48) — 재는 자(installer · deploy)가 줄 앞을 보므로 앞은 안 바꾼다
        _gt0=$SECONDS
        if [ -z "${UPGRADE:-}" ] && probe_global "$_gf" "$_gn"; then
          printf '  ✅ %s — 이미 닿는다 (전역) (%s초)\n' "$_gn" "$((SECONDS - _gt0))"
          gverified_put "$_gn" "$(decl_get "$_gf" "$_gn" probe-target)"
        else
          install_tool "$_gf" "$_gn" || true
          if probe_global "$_gf" "$_gn"; then
            printf '  ✅ %s — 이번에 깔았다 (전역) (%s초)\n' "$_gn" "$((SECONDS - _gt0))"
            gverified_put "$_gn" "$(decl_get "$_gf" "$_gn" probe-target)"
          else
            printf '  ❌ %s — 안 닿는다%s (%s초)\n' "$_gn" \
              "$(awk -F'\t' -v k="$_gn" '$1==k{printf " · 설치 실패: %s", $2; exit}' "$GFAILS" 2>/dev/null)" \
              "$((SECONDS - _gt0))"
            GDOWN=$((GDOWN + 1))
          fi
        fi
        wire_global "$_gf" "$_gn"
        browsers_ready "$_gf" "$_gn"
      done
    done < "$_gl"
    rm -f "$_gl"
  }
  if [ -n "$DO_GLOBAL" ]; then
    echo "전역: 전역형 도구 — 기계에 한 번 깐다 · 깔리는 자리는 저장소가 아니라 홈이다 ($(home_hook_root) 에 붙은 저장소의 선언까지 합친다)"
    # 전역 갈래의 실패는 기계 한 자리에 적는다 — `try`·`nogo` 가 보는 이름을 그 동안만 바꾼다
    _savefails="$FAILS"; FAILS="$GFAILS"
    install_global
    FAILS="$_savefails"
  fi

  # ── ⑥ 저장소 배선 — **깔지 않는다. 잇기만 한다** (#43) ────────────────────────
  #    전역 설치는 저장소 `node_modules` 밖이라 import 가 못 찾는다 — 그 한 칸을 잇는 것이
  #    저장소의 몫이고, 그 뒤에 서는 프로브는 아래 진단 절이 **도구마다 한 번** 든다.
  # ⚠ **여기서 다시 프로브하지 않는다.** 옛 꼴은 설치 앞에서 한 번, 진단에서 또 한 번 물어
  #   저장소마다 두 벌이었다. 깔 자가 없는 고리에서 프로브는 판정일 뿐이고, 판정 문구의
  #   진본은 진단 절 한 자리다.
  if [ -n "$DO_REPO" ]; then
    _wt0=$SECONDS
    for _conf in "$GCONF" "$PCONF"; do
      for _name in $(decl_sections "$_conf"); do
        wire_tool "$_conf" "$_name"
      done
    done
    printf '  · 배선 — 전역 도구를 저장소 node_modules 에 잇는다 (%s초)\n' "$((SECONDS - _wt0))"
  fi

  # ── ⑦ 로컬 main — 컨테이너가 뜬 순간의 스냅샷에 박제된 채 남는다. 원격 최신으로 맞춘다.
  #      main 이 지금 체크아웃돼 있으면 건드리지 않는다 — 작업 중인 브랜치일 수 있다.
  #      저장소 몫이다 — 전역 갈래에는 맞출 저장소가 없다 (#43).
  if [ -n "$DO_REPO" ] &&
     git -C "$PROJECT_DIR" show-ref --verify --quiet refs/heads/main &&
     [ "$(git -C "$PROJECT_DIR" symbolic-ref --short -q HEAD 2>/dev/null)" != main ]; then
    # 사유를 삼키지 않는다 — 여기가 조용히 지면 **낡은 main 을 든 채 세션이 돈다.**
    # 위 당김(①)과 같은 자(git_why)로 낸다: 삼킴이 한 자리에만 남으면 다음엔 저기서 만난다.
    if _fe="$(git -C "$PROJECT_DIR" fetch origin main -q 2>&1)"; then
      git -C "$PROJECT_DIR" branch -f main origin/main >/dev/null 2>&1 || true
    else
      echo "$PROJECT_NAME: ⚠ 로컬 main 을 원격에 못 맞췄다 — $(git_why "$_fe"). 스냅샷 시점의 낡은 main 이 그대로 남는다."
    fi
  fi

  # ── ⑧ 선언 지문을 굳힌다 — PC 세션(auto)의 「깔 것이 있나」가 이 값과 대조된다.
  #      실패가 남아도 굳는다 — 안 굳히면 막힌 망에서 매 세션 재설치가 돈다. 남은 실패는
  #      auto 갈래가 매 세션 한 줄로 알려 부재가 통과로 안 읽힌다.
  #      ⚠ **돈 층만 굳힌다** (#43) — 전역만 돈 갈래가 저장소 지문까지 찍으면 저장소가 깔린
  #        적 없는데 「깔 것이 없다」가 되어, 그 침묵이 무작동을 성공으로 보이게 한다.
  [ -n "$DO_REPO" ] && { decl_fingerprint > "$STAMP" 2>/dev/null || true; }
  if [ -n "$DO_GLOBAL" ]; then
    mkdir -p "$(dirname "$GSTAMP")" 2>/dev/null || true
    global_fingerprint > "$GSTAMP" 2>/dev/null || true
  fi
  # ⚠ **민 뒤에만 찍는다.** 선언이 바뀌어 깐 세션은 밀기가 아니라, 찍으면 낡음 시계가
  #   공짜로 되감긴다 — 그러면 선언을 자주 고치는 기계는 영영 안 밀린다.
  [ -n "${UPGRADE:-}" ] && { : > "$FRESH" 2>/dev/null || true; }

  # ── 전역만 돈 갈래는 여기서 끝난다 — 아래 진단은 **저장소의 물음**이라 부를 자리가 없다.
  #    판정은 위 고리가 이미 냈다(GDOWN). `--check`·`--install` 과 같은 규율로 종료코드를 낸다:
  #    꺼진 것이 있으면 0 으로 안 끝나고, 그 신호를 deploy.ps1 이 받아 위층까지 물고 간다.
  if [ -z "$DO_REPO" ]; then
    if [ "${GDOWN:-0}" -gt 0 ]; then
      echo "  ── 전역형 도구 $GDOWN 개가 안 선다. 위 까닭이 곧 고칠 자리다."
      exit 1
    fi
    exit 0
  fi
fi

# ════════════════════════ 진단 — 지금 어느 검사가 도나 ════════════════════════
# 판정 문구는 여기 한 자리에만 둔다. 위층이 죽으면 아래는 "실패"가 아니라 "못 잼"으로 낸다.

down=0
gate() {  # gate <이름> <ok|off> <까닭>
  if [ "$2" = ok ]; then printf '  ✅ %s — %s\n' "$1" "$3"
  else printf '  ❌ %s — %s\n' "$1" "$3"; down=$((down + 1)); fi
}
why() {  # why <도구> [<설치 걸음>] — 도구 이름으로 못 찾으면 그 도구를 깐 걸음의 실패를 든다
  # ⚠ project-axis 도구(commitlint · markdownlint · pyyaml…)는 제 이름으로 실패를 안 남긴다 —
  #   까는 자가 `npm ci`·`pip install` 한 걸음이라 사유는 「노드 의존성」·「파이썬 의존성」으로
  #   적힌다. 도구 이름으로만 찾으면 ❌ 줄에 사유가 영영 안 붙는다(실측 2026-09-05: npm ci 가
  #   실패했는데 진단은 「commitlint 안 닿는다」만 찍었다).
  # ⚠ **전역 갈래의 기록도 본다** (#43). 전역형 도구는 저장소 고리가 안 깔고 `--install-global`
  #   이 기계 한 자리에 적으므로, 저장소 파일만 보면 그 ❌ 에 사유가 영영 안 붙는다.
  _w=""
  for _wf in "$FAILS" "$GFAILS"; do
    [ -f "$_wf" ] || continue
    [ -n "$_w" ] || _w="$(awk -F'\t' -v k="$1" '$1==k{print $2; exit}' "$_wf" 2>/dev/null)"
    [ -n "$_w" ] || [ -z "${2:-}" ] || _w="$(awk -F'\t' -v k="$2" '$1==k{print $2; exit}' "$_wf" 2>/dev/null)"
  done
  [ -n "$_w" ] && printf ' · 설치 실패: %s' "$_w"
  return 0
}

_dt0=$SECONDS   # 진단 절이 걸린 시간 — 끝줄에 붙는다 (#48)
echo "$PROJECT_NAME — 지금 어느 검사가 도나  ($OS · $MODE)"

# 전역 축 — 판정과 문구는 위 global_rule_reason 이 든다. 여기는 내는 자리일 뿐이다
_gr="$(global_rule_reason)"
[ -n "$_gr" ] && gate "전역 규율" off "$_gr"

# 홈 훅 축 — 저장소 밖에서 연 세션에 auto 를 걸 자가 서 있나 (0010 · 0028 · 0031)
# ⚠ **내는 자리는 하나다.** 홈 훅은 기계당 하나인데 그 훅이 부르면 저장소마다 이 진단이
#   돌아 같은 줄이 저장소 수만큼 찍힌다. 홈 층의 진본을 든 저장소만 낸다 — 규범·룰·
#   에이전트가 거기서만 나가는 것과 같은 자리다 (0014). 그 저장소가 안 붙은 세션은 이
#   줄이 없는 대신 위 「전역 규율」이 선다.
if [ -n "$CONFIG_ROOT" ] && [ "$CONFIG_ROOT" = "$PROJECT_DIR" ]; then
  # 낡은 항목의 루트는 재는 자가 stdout 으로 낸다 — 받아서 문구에 실어 준다
  _stale="$(home_hook_planted)"; _hh=$?
  _stale="$(printf '%s' "$_stale" | tr '\n' ' ')"
  case "$_hh" in
    0) gate "홈 훅" ok  "심겼다 — 저장소 밖(전역 층·홈)에서 연 세션도 auto 가 선다" ;;
    1) if [ -n "$_stale" ]; then
         gate "홈 훅" off "이 루트($(home_hook_root))로는 안 심겼다 — 딴 루트만 심겨 있다: $_stale. 저장소를 옮겼으면 deploy.ps1 이나 --install 이 이 루트로 심는다"
       else
         gate "홈 훅" off "안 심겼다 — 저장소 밖에서 연 세션은 아무 훅도 안 건다. deploy.ps1 이나 --install 이 심는다"
       fi ;;
    2) gate "홈 훅" off "**못 잼** — $PY_CMD 를 못 부른다(윈도우면 스토어 껍데기다). 심기도 같은 가드에서 진다" ;;
    3) gate "홈 훅" off "이 루트로는 심겼는데 **낡은 항목이 남아 있다**: $_stale — 그 루트의 저장소를 세션마다 헛돈다. ~/.claude/settings.json 에서 그 항목을 지운다" ;;
  esac
fi

# 저장소 규약 축 — .githooks/ 의 존재가 곧 선언이다
if [ -d "$PROJECT_DIR/.githooks" ]; then
  # 자리 일치로 재는 몸통은 앞머리의 `hooks_wired` 한 벌이다 — `--needs-install` 과 같은 자다.
  if hooks_wired; then
    gate "커밋 훅 배선" ok "core.hooksPath=$HOOKS_PATH"

    # ⚠ **몸통 둘 다 본다.** 옛 판은 `commit-msg` 만 물어서, `pre-commit` 에 실행권한이 없으면
    #   **조각이 통째로 안 도는데 진단은 ✅ 였다.** 가드의 부재지 고장이 아니다.
    for _b in pre-commit commit-msg; do
      [ -f "$PROJECT_DIR/.githooks/$_b" ] && [ ! -x "$PROJECT_DIR/.githooks/$_b" ] &&
        gate "커밋 게이트($_b)" off "실행권한이 없어 git 이 무시한다 — 조각이 다 멀쩡해도 안 돈다"
    done

    # ⚠ **선언을 연다.** 옛 판은 폴더 존재와 `core.hooksPath` 둘만 보고 `gates.conf` 를 **한 번도
    #   안 읽었다** — 선언을 치워도 ✅ 였고, 커밋 때 러너는 *"아무것도 안 잰다"* 고 말했다.
    #   「훅이 걸렸나」와 「무엇을 재나」는 다른 명제다.
    # ⚠ 파서를 여기 두 벌 두지 않는다 — 러너를 그대로 부른다(`gate_list`).
    _gc="$PROJECT_DIR/.githooks/gates.conf"
    _gr="$PROJECT_DIR/.githooks/gates-run.sh"
    if [ ! -f "$_gc" ]; then
      gate "커밋 게이트" off "선언이 없다(.githooks/gates.conf) — 훅은 걸렸는데 **아무것도 안 잰다**"
    elif [ ! -f "$_gr" ]; then
      gate "커밋 게이트" off "선언은 있는데 러너가 없다(.githooks/gates-run.sh) — 배포가 반쪽만 닿았다"
    else
      # shellcheck source=/dev/null
      . "$_gr"
      _on=""; _gone=""
      for _stage in pre-commit commit-msg; do
        for _g in $(gate_list "$_stage" "$_gc"); do
          if [ -f "$PROJECT_DIR/.githooks/gates.d/$_g.sh" ]; then _on="$_on $_g"
          else _gone="$_gone $_g"; fi
        done
      done
      if [ -n "$_gone" ]; then
        gate "커밋 게이트" off "선언에 있는데 조각이 없다:$_gone — 배포가 안 닿았다. 커밋이 막힌다"
      elif [ -z "$_on" ]; then
        gate "커밋 게이트" off "선언은 있는데 켠 검사가 없다 — **아무것도 안 잰다**"
      else
        gate "커밋 게이트" ok "켜진 검사:$_on"
      fi
      # ⚠ **자리가 아니라 해석기로 묻는다.** 옛 판은 `.githooks/adr-index.sh`(생성기의 한 자리)가
      #   있나로 물어서, 그 사본을 안 든 저장소에서는 `adr-index` 를 켰는데도 **한 줄도 안 났다**.
      case " $_on " in
        *" adr-index "*)
          [ -n "$ADR_GEN" ] ||
            gate "커밋: 색인 대조" off "생성기를 못 찾아 **약한 검사로 갈음한다** — 머리말이 바뀐 것만 본다" ;;
      esac
    fi
  else
    gate "커밋 게이트" off "core.hooksPath 가 안 걸려 **못 잼** — 훅 자체가 안 돈다"
  fi
fi

# 선언의 판이 **잴 수 있는 꼴인가** — 선언만 읽는다(npm 을 안 부르므로 통과 갈래에서도 싸다).
# ⚠ **범위·딱지는 안 잰 것이다.** 통과 옆에 그 사실이 안 찍히면 「전부 통과」가 「판까지 봤다」로
#   읽힌다 — 초록의 폭을 검사가 스스로 말하게 한다(규범 [Goal-Driven Execution]).
pin_shape() {  # pin_shape <선언파일> <이름> — 안 잰 까닭 한 줄, 잴 수 있으면 빈 값
  [ "$(decl_get "$1" "$2" install)" = npm-global ] || return 0
  _sk="$(decl_get "$1" "$2" package)"
  case "$_sk" in ?*@*) ;; *) return 0 ;; esac   # 판을 안 박은 선언은 애초에 안 잰다고 적혀 있다
  _sv="${_sk##*@}"
  case "$_sv" in ''|*[!0-9.]*)
    printf '판 「%s」 는 정확한 판이 아니라 **판은 안 쟀다**(`이름@1.2.3` 꼴이어야 잰다)' "$_sv" ;;
  esac
  return 0
}

# 선언이 판을 박았는데 깔린 판이 다른가 — **「안 깔렸다」와 「판이 다르다」는 고칠 자리가
# 다르다.** 둘 다 ❌ 로 나오는데 사유가 「안 닿는다」 하나면, 다음 사람은 npm 이 없나부터
# 뒤진다. 사유 없는 ❌ 는 다음 사람에게 부재와 같다 (위 `nogo` 곁말과 같은 결).
pin_mismatch() {  # pin_mismatch <선언파일> <이름> — 어긋나면 읽을 한 줄, 아니면 빈 값
  [ "$(decl_get "$1" "$2" install)" = npm-global ] || return 0
  _mk="$(decl_get "$1" "$2" package)"
  # 스코프 패키지(@scope/name)는 맨 앞 `@` 가 판 구분자가 아니다 — 첫 글자 뒤의 `@` 만 문다.
  case "$_mk" in ?*@*) ;; *) return 0 ;; esac
  _mv="${_mk##*@}"
  # 꼴 판정은 `pin_shape` 한 자리가 든다 — 여기서도 말하면 같은 문장이 두 벌이 된다.
  case "$_mv" in ''|*[!0-9.]*) return 0 ;; esac
  _mh="$(npm_global_version "${_mk%@*}" || true)"
  [ -n "$_mh" ] && [ "$_mh" != "$_mv" ] &&
    printf '깔린 판이 다르다: %s (선언은 %s) — 다시 깔면 선언한 판을 받는다' "$_mh" "$_mv"
  return 0
}

# ── 전역 걸음이 **이 실행에서** 낸 판정이 있나 — 캐시가 아니라 인용이다 (#57) ─────────
# ⚠ 배포 한 번(`deploy.ps1`)이 전역 걸음에서 도구마다 프로브를 이미 띄웠는데, 이어 도는
#   저장소 다섯의 진단이 같은 전역형 도구를 저장소마다 또 띄웠다 — 같은 실행에서 같은 명제를
#   스물다섯 번(사내 VDI 실측 ~280초). 전역형 도구는 기계에 하나라 저장소마다 답이 같다.
# ⚠ **프로브를 뺀 것이 아니다** — 「깔린 것과 닿는 것은 다른 명제」는 그대로 서 있고(이 파일
#   머리말), 그 실행이 방금 실행해서 낸 판정을 좌표로 인용할 뿐이다. 그래서 문은 셋이고 셋이
#   다 열려야 한다: **표식이 서 있나**(`CLAUDE_CONFIG_RUN` — 세우는 자는 `deploy.ps1` 하나다)
#   · **이름과 프로브 대상이 같나**(대상이 다르면 같은 이름이라도 딴 명제다) · **표식이 같나**
#   (지난 실행의 명부는 이번 실행의 실측이 아니다). 배포 밖에서는 표식이 없어 한 줄도 안 바뀐다.
# ⚠ **읽기는 셸 안에서 끝낸다** — 저장소마다 도구마다 도는 자리라, 여기서 프로세스를 띄우면
#   줄이려던 값을 되돌려 놓는다. `read` 는 내장이다.
global_verified() {  # global_verified <선언파일> <이름> <probe-target>
  [ -n "${CLAUDE_CONFIG_RUN:-}" ] || return 1
  [ -f "$GVERIFIED" ] || return 1
  global_kind "$(decl_get "$1" "$2" install)" || return 1
  # ⚠ **`node-resolvable` 은 인용이 못 선다 — 프로브 둘이 딴 명제를 잰다.** 전역 걸음의
  #   `probe_global` 은 `npm root -g` 에 대고 「기계에 있나」를 묻고, 저장소의 `probe_reach` 는
  #   **이 저장소 안에서** 「정션을 타고 이름이 풀리나」를 묻는다. 기계에 있어도 저장소 배선이
  #   지면 후자는 져야 하는데, 전자를 인용하면 그 ❌(「깔렸는데 프로브가 못 찾는다: 배선이
  #   끊겼다」)가 통째로 사라진다 — **인용은 같은 명제를 대신할 때만 선다.** 기계에 대고 묻는
  #   갈래(PATH 실행형)만 남기고 이 갈래는 옛 길 그대로 저장소마다 잰다.
  [ "$(decl_get "$1" "$2" probe)" = node-resolvable ] && return 1
  # 줄의 꼴은 쓰는 자 `gverified_put` 과 한 벌이다 — 통째로 견줘 셋 중 하나만 달라도 안 문다.
  _vq="$(printf '%s\t%s\t%s' "$2" "$3" "$CLAUDE_CONFIG_RUN")"
  while IFS= read -r _vl; do
    [ "$_vl" = "$_vq" ] && return 0
  done < "$GVERIFIED"
  return 1
}

# 선언 축 — 전역·프로젝트 두 층. 이름·뜻은 전부 선언에서 온다
render_decl() {  # render_decl <선언파일> <층라벨>
  for _name in $(decl_sections "$1"); do
    _probe="$(decl_get "$1" "$_name" probe)"
    _target="$(decl_get "$1" "$_name" probe-target)"
    _by="$(decl_get "$1" "$_name" called-by)"
    # 까는 걸음의 이름 — project-axis 도구는 이 이름으로 실패가 남는다 (why 곁주석). `try` 가
    # 적는 그 이름 그대로여야 한다 — 갈리면 사유가 또 안 붙는다.
    case "$_probe" in
      exec-npm-bin)      _step="노드 의존성" ;;
      python-importable) _step="파이썬 의존성" ;;
      *)                 _step="" ;;
    esac
    # ⚠ **판정 앞에서 부르지 않는다.** `pin_mismatch` 안에서 `npm root -g` + `node` 가 도는데,
    #   통과할 도구에도 그 쌍이 돌면 세션마다 도구 수만큼 곱해진다(npm 은 시작만으로 수백 ms 다).
    # ⚠ **프로브 앞에 선다 — 이기면 프로브를 안 띄운다.** 문 셋(표식·이름+대상·같은 표식)은
    #   `global_verified` 가 든다. 표식이 없는 자리에서는 첫 문에서 바로 져 옛 길 그대로다.
    if global_verified "$1" "$_name" "$_target"; then
      gate "$_name" ok "$_by ($2) — 전역 걸음이 이 실행에서 확인했다"
    elif probe_decl "$1" "$_name"; then
      _shape="$(pin_shape "$1" "$_name")"
      if [ -n "$_shape" ]; then gate "$_name" ok "$_by ($2) — $_shape"
      else                      gate "$_name" ok "$_by ($2)"; fi
    elif _pin="$(pin_mismatch "$1" "$_name")"; [ -n "$_pin" ]; then
      gate "$_name" off "$_by ($2) — $_pin$(why "$_name" "$_step")"
    elif [ "$_probe" = node-resolvable ] && [ -d "$(npm root -g 2>/dev/null)/$_target" ]; then
      gate "$_name" off "$_by ($2) — 깔렸는데 프로브가 못 찾는다: 배선이 끊겼다$(why "$_name" "$_step")"
    elif [ "$(decl_get "$1" "$_name" on-demand)" = yes ]; then
      # 선언이 「필요할 때 깐다」로 둔 도구 — 부재가 이 저장소의 검사를 끄는 것이 아니다
      gate "$_name" ok "$_by ($2) — 안 닿는다 · 필요할 때 깐다 (on-demand)"
    else
      gate "$_name" off "$_by ($2) — 안 닿는다$(why "$_name" "$_step")"
    fi
  done
}
render_decl "$GCONF" "전역"
render_decl "$PCONF" "프로젝트"

if [ "$down" -gt 0 ]; then
  echo "  ── 꺼진 검사 $down 개. 위 까닭이 곧 고칠 자리다."
  echo "     리모트는 세션을 다시 열면 다시 깐다. PC 는 deploy.ps1 이나 --install 로 다시 깐다."
  echo "     같은 줄이 또 꺼지면 다시 깔지 말고 위의 「설치 실패」 사유를 본다."
fi
printf '  ── 진단을 마쳤다 (%s초)\n' "$((SECONDS - _dt0))"

# ── 판정 — **꺼진 검사가 있으면 0 으로 안 끝난다** ────────────────────────────
# ⚠ 가르는 것은 「깔았나」가 아니라 **누가 물었나**다. `auto` 는 세션 시작이라, 0 이 아니면
#   세션 자체가 오류로 보인다 — 거기서는 진단을 말로만 낸다. `--check` 와 `--install` 은
#   **판정을 받으러 온 자리**이므로 꺼진 검사를 종료코드로 낸다.
# ⚠ 옛 판은 `--install` 도 늘 0 이었다. 그래서 **설치가 목표를 못 이루고도 위층에 초록으로
#   보고됐다**: deploy.ps1 은 「훅이 진단을 찍으니 여기서 또 판정하지 않는다」며 종료코드만
#   보는데 그 신호가 영영 안 왔고, 화면은 검사 셋이 꺼진 채 초록으로 끝났다 (실측 2026-09-10
#   · 사외·사내 VDI). 「부재가 통과로 읽힌다」가 **설치가 목표를 이뤘나를 가르는 그 한 줄**에
#   앉아 있었다. 설치의 목표는 「깔기를 돌았다」가 아니라 **환경이 서 있다**이다.
case "$MODE" in
  check|install) [ "$down" -gt 0 ] && exit 1 ;;
esac
exit 0
