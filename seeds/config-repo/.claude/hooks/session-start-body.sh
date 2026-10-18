#!/bin/bash
# 세션 시작 훅 — 익명 몸통 (SessionStart 훅 겸 설치기)
#
# 원본은 claude-config/.claude/hooks/session-start-body.sh 다. **저장소마다 사본을 두지 않는다** —
# 저장소마다 서는 것은 문지기 `session-start.sh` 이고, 문지기가 붙은 claude-config 의 이 몸통(없으면 홈 씨앗의
# 몸통)을 찾아 저장소를 넘기며 부른다. 그래서 이 파일을 고쳐도 형제 저장소 커밋이 따라 나오지 않는다.
#
# 이 파일은 프로젝트 이름도 도구 이름도 모른다. 목록의 진본은 선언 둘이다:
#   .claude/tools.global.conf   전역 도구 — 전역 스킬이 부르는 것 (claude-config 진본의 배포본)
#   .claude/tools.conf          이 저장소의 도구 — 저장소가 커밋한다
# 도구가 늘면 선언에 블록을 더한다. 이 파일을 고치는 것은 새 설치법 · 새 프로브 갈래가 필요할 때뿐이다.
#
# 부르는 꼴 — 하는 일 · 끝 값:
#   session-start.sh            세션(auto). 리모트면 깐다. PC 면 당겨 오고(ff-only · main 만 · 저장소가 고른 커밋에서
#                               멈출 수 있다) 홈 규범을 새로 민 뒤, 선언 지문이 어긋날 때만 깐다 — 까는 것은 배경에서
#                               돌아 세션 시작이 안 기다린다. 홈 밀기 같은 PC 전체 일은 설정 저장소 세션 · 저장소 밖
#                               세션만 하고, 형제 저장소 세션은 그 저장소 일만 한다. 늘 0
#   session-start.sh --install  기계를 안 가리고 깐다        ← deploy.ps1 이 저장소마다 이걸로 부른다
#                               PC 에서 밖(설치기 · 사람)이 부르면 사람에게 딸린 것(git 신원 · 형제 저장소 · 개인 키 ·
#                               홈 개인 설정)을 세우고 deploy.ps1 에 넘긴다 — 끝 값은 deploy 의 것이다.
#                               deploy.ps1 이 부른 자리(CLAUDE_CONFIG_DEPLOYING)에서는 저장소 몫만 든다 — 전역형
#                               도구는 아래 갈래가 이미 깔았다. 그 deploy.ps1 을 바깥 `--install` 이
#                               불렀으면(CLAUDE_CONFIG_PC_WIDE_HELD) PC 전체 일도 안 든다 — 바깥이 한 번 한다.
#                               꺼진 검사가 있으면 1
#   session-start.sh --install-global
#                               전역형 도구를 기계에 한 번 깐다 ← deploy.ps1 이 저장소 고리 앞에 한 번 부른다.
#                               전역 선언과 작업 루트에 붙은 모든 저장소의 전역형 선언을 이름으로 합쳐 같은 이름을
#                               한 번만 깐다. 브라우저 뒷길도 여기서 한 번. 저장소 것(venv · npm ci · 배선)은 안 든다.
#                               안 서는 전역형 도구가 있으면 1
#   session-start.sh --plant <작업 루트>
#                               심기만 한다 ← 설치기가 저장소 걸음 뒤에 PC 마다 부른다. 홈 SessionStart 훅 · 작업 루트
#                               우리 저장소의 폴더 신뢰 · 데스크탑 앱 목록과 권한(`plant_session_state`). 설정 저장소가
#                               없어도 돈다(홈 씨앗의 몸통) — 그 몸통은 제 자리로 루트를 못 잡으므로 작업 루트를 꼭
#                               받는다(씨앗 폴더의 부모로 심으면 홈 훅이 엉뚱한 루트를 가리키고 씨앗 폴더가 신뢰
#                               대상에 든다). 깔기 · 배포 · 당김 · 배선 · 홈 밀기는 안 한다.
#                               0 · 홈 훅이나 Claude 신뢰를 못 심었거나 심는 스크립트가 못 돌았으면 1 · 작업 루트가
#                               없거나 폴더가 아니면 아무것도 안 하고 2. 다른 칸(Codex · 데스크탑 앱 · agy · Copilot ·
#                               VS Code)은 못 심어도(`ERROR=desktop-state` 도) `!` 줄만 남기고 0 이다 — 다음 설치가
#                               다시 심는다
#   session-start.sh --check    안 깔고 진단만 낸다          ← 어디서 돌려도 안전. 꺼진 검사가 있으면 1
#   session-start.sh --needs-install
#                               「깔 게 있나」에 예/아니오만 낸다 ← deploy.ps1 의 계획 단계가 이걸로 묻는다. 파일만
#                               보고 1초 안에 끝난다 — 프로브도 망도 안 탄다. 0 안 깐다 · 1 깐다 · 2 못 쟀다
#   session-start.sh --pull-target <저장소> <원격>
#                               당김이 멈출 커밋을 묻는다 ← PowerShell 의 당김(deploy.ps1 · 부팅 라인)이 fetch 뒤 ·
#                               merge 앞에서 몸통을 바로 부른다. 세션 당김과 같은 자(`_pull_target`)로 저장소의 손에
#                               묻고 답을 재고 판정을 `.git/claude-pull-target.last` 에 적는다 — 같은 원격을 당기는
#                               자리가 다 같은 커밋에서 선다. stdout 에 병합할 커밋의 온전한 sha 한 줄과 0 · 저장소나
#                               `<원격>/main` 을 못 읽으면 stderr 한 줄과 2
#   session-start.sh <그 밖의 인자>
#                               아무것도 안 하고 stderr 한 줄과 2 로 끝난다 — 오타(`--chek`)가 인자 없는 갈래(당김 ·
#                               홈 밀기 · 설치)로 새지 않는다. 2 는 「답을 못 냈다」다 — 1 은 갈래마다 잰 판정(꺼진
#                               검사 · 깔 것 있음)이라 아무것도 안 잰 자리에 못 쓴다
# 명시한 셋(--install · --install-global · --plant)은 찍는 줄을 ~/.claude/logs/session-start-<날짜>.log 에도
# 남긴다 — 걸음마다 (n초) 가 붙는다.
#
# 지키는 것 —
#   부재가 통과로 읽히지 않게 한다. 게이트는 도구가 없으면 그 검사만 건너뛰고 통과시키므로 진단 단계가 그 자리를
#   메운다 — 판정 문구는 거기 한 자리에만 둔다.
#   깔린 것과 닿는 것은 다른 명제다. 프로브는 전부 실행형이다 — 파일 존재로 물으면 ✅ 가 거짓말을 한다.
#   ⚠ 말은 stdout 으로 낸다. SessionStart 훅에서 모델의 문맥에 들어가는 것은 stdout 뿐이고 stderr 는 기록에만
#   남는다 — 세션이 읽어야 할 줄에 `>&2` 를 붙이면 아무도 안 읽는 경고가 되어 부재와 같다.
#   순서가 값을 한다 — 가볍고 안 죽는 것(복사 · git config)을 앞에, 망을 타는 것을 뒤에. 설치는 저마다 실패를
#   삼키되 사유는 남긴다(`try`) — 반쯤 깔린 채 침묵하지 않는다.
set -uo pipefail

# ══ 단계 · 부름 — 모든 갈래 ════════════════════════
#    층 — 없음(준비). 무엇을 어느 저장소에 할지를 잡는다
#    하는 일 — 인자로 갈래(`MODE` · `ASKED`)를 고르고(모르는 인자 · 작업 루트 없는 `--plant` 는 무엇도 하기 전에 2 로
#      끝낸다), 대상 저장소(`PROJECT_DIR` · `PROJECT_NAME`)를 문지기가 넘긴 값 → 제 경로 → `CLAUDE_PROJECT_DIR`(없으면
#      지금 폴더) 차례로 잡는다. 명시한 갈래(`--install` · `--install-global` · `--plant`)의 바깥 실행은 기록 파일을 열고
#      저를 다시 띄워 그 줄을 받은 뒤, 안쪽의 종료코드로 끝난다
#    앞에서 받는 것 — 인자 하나(`--plant` 는 작업 루트 하나 더 · `PLANT_ROOT` · `--pull-target` 은 저장소와 원격 둘 더 ·
#      `PT_REPO` · `PT_REMOTE`) · `SESSION_START_REPO`(문지기 · deploy.ps1) ·
#      `SESSION_LOG`(바깥이 받고 있다는 표식) · `CLAUDE_PROJECT_DIR`
#    안 하는 것 — 함수를 부르지 않는다(라이브러리는 이 단계 뒤에 선다). 깔지도 홈에 밀지도 않는다 — 쓰는 것은
#      바깥 실행의 기록 파일(`~/.claude/logs/`) 하나다
MODE=auto
ASKED=""   # 인자로 명시된 갈래 — auto 가 지문 어긋남으로 install 이 되는 것과 가른다
PLANT_ROOT=""   # `--plant` 가 받은 작업 루트 — 아래에서 `pwd` 꼴로 굳혀 SIBLING_BASE 가 된다
case "${1:-}" in
  '')               ;;   # 인자 없음 — 세션(auto)
  --check)          MODE=check ;;
  --needs-install)  MODE=needs-install ;;
  --install)        MODE=install; ASKED=install ;;
  --install-global) MODE=install; ASKED=install-global ;;
  --plant)          MODE=plant; ASKED=plant; PLANT_ROOT="${2:-}" ;;
  --pull-target)    MODE=pull-target; PT_REPO="${2:-}"; PT_REMOTE="${3:-}" ;;
  # 모르는 인자는 무엇도 하기 전에 끝낸다 — 기본 갈래가 없으면 오타 하나가 auto 를 통째로 돈다.
  #   stderr 로 낸다 — 세션 문맥에 실을 말이 아니라 부른 자의 실수이고, 훅으로 걸렸으면 하네스가 0 아닌
  #   끝의 stderr 를 사람에게 보인다
  *) printf '세션 훅: 모르는 인자 「%s」 — 아무것도 안 하고 끝낸다 (아는 것: 인자 없음 · --check · --needs-install · --install · --install-global · --plant · --pull-target)\n' "$1" >&2
     exit 2 ;;
esac
# `--plant` 의 작업 루트는 무엇도 하기 전에 굳힌다 — 없거나 폴더가 아니면 모르는 인자와 같이 2 로 끝낸다.
#   `pwd` 꼴로 굳히는 것은 `--install` 이 제 자리에서 잡는 루트(`SIBLING_BASE`)와 같은 글자를 내려서다 — 글자가 다르면
#   두 갈래가 번갈아 홈 훅 명령을 갈아 심는다. 끝의 구분자도 여기서 떨어진다
if [ "$MODE" = plant ]; then
  _pr="$(cd "$PLANT_ROOT" 2>/dev/null && pwd)" || _pr=""
  if [ -z "$PLANT_ROOT" ] || [ -z "$_pr" ]; then
    printf '세션 훅: --plant 는 작업 루트(있는 폴더) 하나를 받는다 — 받은 것 「%s」 — 아무것도 안 하고 끝낸다\n' "$PLANT_ROOT" >&2
    exit 2
  fi
  PLANT_ROOT="$_pr"
fi

# ── 어느 저장소를 깔고 있나 — 넘겨받은 값 → 제 자리 → CLAUDE_PROJECT_DIR 차례로 잡는다 ──
#    문지기가 부른 자리는 저장소를 넘겨받는다(`SESSION_START_REPO`) — 몸통은 claude-config(또는 홈 씨앗)에 살아 제 경로가
#    대상 저장소가 아니다. 받은 글자를 그대로 쓴다: 꼴 굳히기는 `home_hook_root` 한 자리가 들고, 여기서 `pwd` 로 먼저
#    누르면 그 자리를 재는 검사가 딴 꼴을 못 밟는다.
#    ⚠ 받은 자리에서 끊는다(unset). 이 몸통은 deploy.ps1 을 부르고 그것이 claude-config 훅을 다시 부른다 — 값이 환경에
#      남으면 그쪽이 형제 저장소를 제 저장소로 잡는다. 이어 받을 자리(아래 기록의 다시 띄우기)는 값을 명시해 넘긴다.
#    넘겨받지 않았으면 제 경로에서 역산한다 — 이 스크립트는 <저장소>/.claude/hooks/ 에 산다. 그 꼴이 아닐 때만(파이프로
#    먹인 판) 환경변수로 물러선다.
#    ⚠ CLAUDE_PROJECT_DIR 은 저장소가 아니라 세션 루트다. 저장소를 둘 붙이면 루트가 한 칸 위로 올라가 홈을 가리키고, 여기서
#      파생되는 선언 넷 · venv · 지문이 통째로 엉뚱한 자리를 본다 — 훅은 아무것도 못 찾은 채 빈 지문에 「완료」 도장을
#      찍고 배선도 venv 가드에 걸려 걷힌다. 성공으로 보고되는 무작동이다.
_self="${BASH_SOURCE[0]:-$0}"
PROJECT_DIR=""
if [ -n "${SESSION_START_REPO:-}" ] && [ -d "$SESSION_START_REPO" ]; then
  PROJECT_DIR="$SESSION_START_REPO"
fi
unset SESSION_START_REPO
if [ -z "$PROJECT_DIR" ]; then
  case "$_self" in
    */.claude/hooks/*) PROJECT_DIR="$(cd "$(dirname "$_self")/../.." 2>/dev/null && pwd)" ;;
  esac
fi
[ -n "$PROJECT_DIR" ] || PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
PROJECT_NAME="$(basename "$PROJECT_DIR")"   # 진단 머리줄·profile.d 파일명이 여기서 파생된다
# ── 명시한 갈래(`--install` · `--install-global` · `--plant`)는 찍는 줄을 파일에도 남긴다 ─────────────
#    설치 화면이 닫히면 화면의 줄은 사라진다 — 걸음마다 붙는 `(n초)` 도 이 파일에서 읽는다. 세션마다 도는 auto 갈래는
#    안 쓴다(매 세션 파일이 는다).
#    ⚠ 바깥 하나만 받는다. PC 의 `--install` 은 deploy.ps1 을 부르고 그것이 저장소마다 이 훅을 다시 `--install` 로
#      부른다 — 바깥이 받고 있으면 안쪽 줄은 그 파이프로 흘러야 같은 줄이 두 번 안 적힌다. 파일 이름(SESSION_LOG)이
#      환경에 서 있는 것이 「바깥이 받고 있다」는 표식이다.
#    stderr 도 같이 받는다 — pip · npm 이 죽은 까닭이 그쪽으로 나오고, 위층(PowerShell 5.1)이 stderr 를 오류로 올리는
#    자리도 안 밟는다. 제 경로를 못 잡은 세션(파이프로 먹인)은 다시 못 띄우므로 안 남긴다.
if [ -n "$ASKED" ] && [ -z "${SESSION_LOG:-}" ] && [ -f "$_self" ] && mkdir -p "$HOME/.claude/logs" 2>/dev/null; then
  SESSION_LOG="$HOME/.claude/logs/session-start-$(date +%Y%m%d).log"; export SESSION_LOG
  printf '── %s  %s  --%s  %s ──\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$PROJECT_NAME" "$ASKED" "$PROJECT_DIR" >> "$SESSION_LOG"
  SESSION_START_REPO="$PROJECT_DIR" bash "$_self" "$@" 2>&1 | tee -a "$SESSION_LOG"
  _lrc=$?   # pipefail — tee 가 아니라 훅의 종료코드다. 위층(deploy.ps1)이 이 값을 판정으로 받는다
  exit "$_lrc"
fi

#region 라이브러리 — 흐름이 부르는 함수는 다 여기 선다. 정의만 있고 도는 문장은 없다
#   함수가 읽는 전역 값(상태 파일 자리 · 처음 값)은 흐름이 세운다 — 함수는 불릴 때 그 값을 읽는다

_migrate_name() {   # $1 옛 이름 · $2 새 이름
  [ -e "$1" ] || return 0
  [ -e "$2" ] || mv "$1" "$2"
}

# ── 선언 지문 — 설치가 소비하는 선언 넷의 sha256 한 줄을 낸다 ──
#    설치 걸음 끝(「선언 지문 굳히기」)에 굳고, PC 세션(auto)이 「깔 것이 있나」를 이 값과 대조한다 — 판정이 사건(풀이
#    있었나)이 아니라 상태(선언과 설치가 같은 세대인가) 위에 선다. 값은 기계 밖으로 안 나가 줄끝을 안 탄다.
#    이것은 저장소 몫의 지문이다 — 전역형 도구는 기계 하나에 서므로 그 짝(`global_fingerprint`)이 따로 있고 게이트도
#    둘로 갈린다.
decl_fingerprint() {
  cat "$PROJECT_DIR/requirements.txt" "$PROJECT_DIR/package-lock.json" \
      "$GCONF" "$PCONF" 2>/dev/null | sha256sum | awk '{print $1}'
}

# ── 파일로 재는 자 둘 — 배선이 섰나 · venv 가 닿나 ─────────────────────────────────
#    `--needs-install` 과 진단 단계가 같은 것을 묻는다 — 자를 두 벌 두면 한쪽만 고쳐져 같은 저장소를 놓고 두 자리가
#    다르게 말한다. 둘 다 읽기만 한다 — 재는 갈래가 상태를 바꾸면 판정이 늘 초록이 된다(`--check` 가
#    `wire_commit_hooks` 를 안 부르는 것과 같은 규율). 파이썬을 안 띄워, 해석기를 고르기(`py_resolve`) 전에 끝나는
#    `--needs-install` 이 쓸 수 있다.
hooks_wired() {  # 0 이면 이 저장소의 .githooks 로 배선돼 있다. 걸린 글자는 HOOKS_PATH 가 든다
  HOOKS_PATH="$(git -C "$PROJECT_DIR" config core.hooksPath 2>/dev/null)"
  [ -d "$PROJECT_DIR/.githooks" ] || return 1
  # 글자 일치가 아니라 자리 일치다 — 절대경로(`C:/…/.githooks`)로 걸어 둔 저장소도 같은 폴더를 가리키면 배선된 것이다.
  case "$HOOKS_PATH" in
    .githooks|./.githooks) return 0 ;;
    "") return 1 ;;
    *) _hw_here="$(cd "$PROJECT_DIR" 2>/dev/null && cd "$HOOKS_PATH" 2>/dev/null && pwd -P)"
       [ -n "$_hw_here" ] || return 1
       _hw_want="$(cd "$PROJECT_DIR/.githooks" && pwd -P)"
       [ "$_hw_here" = "$_hw_want" ] && return 0
       # 설정 저장소의 원본 `.githooks` 를 바로 가리켜도 배선된 것이다 — 원본 게이트는 제 자리를
       #   기준으로 서서, 저장소의 선언과 조각을 먼저 쓰고 없는 것만 제 곁에서 찾는다.
       # 설정 저장소가 어디냐는 준비 단계의 CONFIG_ROOT 한 자리가 든다 — 그 표지를 여기 또 적지 않는다.
       [ -n "$CONFIG_ROOT" ] &&
         [ "$_hw_here" = "$(cd "$CONFIG_ROOT/.githooks" 2>/dev/null && pwd -P)" ] ;;
  esac
}

# venv_ready — 0 이면 venv 에 pip 이 있다.
# ⚠ venv 는 폴더가 서 있나가 아니라 pip 이 닿나로 잰다. `python -m venv` 는 트리를 만들고 해석기를 복사한 뒤에 pip 을
#   깐다 — 그 마지막 걸음만 져도 폴더가 남아, 존재로 물으면 반쯤 선 venv 가 「있다」로 읽히고 다시 깔아도 안 낫는다
#   (만들기를 건너뛰고, 의존성 칸도 조용히 지나가고, 실패는 한 줄도 안 남는다).
venv_ready() { [ -x "$VENV_BIN/pip" ] || [ -f "$VENV_BIN/pip.exe" ]; }

# py_resolve — PY_CMD 를 진짜 해석기로 고쳐 세운다 · 늘 0. needs-install 을 뺀 갈래마다 파이썬이 한 번 뜬다.
# ⚠ 윈도우의 `python` 이름은 스토어 껍데기일 수 있다. PATH 앞의 `WindowsApps\python.exe` 는 스토어를 여는 자리표라
#   비대화에서 지고, 설치기가 같은 실행에서 파이썬을 막 깔았어도 이 셸의 PATH 는 그 전 것이라 껍데기가 먼저 걸린다.
#   그래서 이름을 믿지 않고 한 번 불러 보고 진짜를 고른다: 이름 → `py -3` 런처(python.org · winget 설치가 등록한다) →
#   winget/python.org 가 두는 자리. 셋 다 지면 이름을 그대로 둔다 — 심는 자리가 그때 사유를 댄다.
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

# ── uv 를 새 판으로 — 파이썬을 받기 전에 한 실행에 한 번(늘 0). 「파이썬 축」 · 「세션의 python3」 칸이 부른다 ──
#    낡은 uv 는 낡은 목록으로 rc 판까지만 안다. self update 는 GitHub API 라 프록시 제한에 걸리고 astral.sh 가 막힌 망도
#    있어 PyPI 경로가 뒤를 받친다. venv 에 물린 파이썬은 --user 를 거부하므로 시스템 해석기를 명시한다. 셋 다 막히면 있는
#    목록으로 간다.
uv_fresh() {
  [ -n "${UV_FRESHED:-}" ] && return 0
  UV_FRESHED=1
  uv self update >/dev/null 2>&1 ||
    /usr/bin/python3 -m pip install -q --user --upgrade uv >/dev/null 2>&1 || true
}

# ── uv 가 세운 링크인가 — `uv python install --default` 가 `~/.local/bin` 에 세우는 것은 uv 의 파이썬 자리를 가리키는
#    심링크다. 그 밖의 것(저장소 venv 감싸개 · 남이 둔 파일)은 uv 가 안 덮는다 ──
uv_link() {  # uv_link <경로> — 0 uv 의 파이썬 자리 밑을 가리키는 심링크다 · 1 아니다 · 2 uv 의 자리를 못 읽어 모른다
  [ -L "$1" ] || return 1
  # 색을 끈다 — FORCE_COLOR · CLICOLOR_FORCE 가 선 환경에서는 경로 앞에 색 부호가 붙어 어느 링크도 그 밑으로 안 읽힌다
  _uvd="$(NO_COLOR=1 uv --color never python dir 2>/dev/null)" && [ -n "$_uvd" ] || return 2
  _uvd="$(readlink -f "$_uvd" 2>/dev/null)" || return 2
  case "$(readlink -f "$1" 2>/dev/null)" in "$_uvd"/*) return 0 ;; esac
  return 1
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

# ── 절 하나를 한 번 읽어 달라는 키를 달라는 순서로 낸다 ─────────────────────
#    `decl_get` 은 키 하나에 awk 한 프로세스라, 프로브 · 판 검사 · 진단이 도구마다 키를 물으면 선언 조회가 세션에서
#    수십 번이 된다. 자리 메타(`_site_meta`)와 같은 꼴로 파일당 한 번 읽어 필요한 값을 같이 낸다.
#    키 목록은 부르는 자가 제 자리에서 댄다 — 선언의 낱말을 이 함수가 들면 그 목록이 손사본이 되어 키가 늘 때 조용히 낡는다.
# ⚠ 줄 수는 달라는 키 수와 같고, 없는 키는 빈 줄이다 — 값을 자리로 읽으므로 한 칸이 비면 그 뒤가 다 밀린다. 그래서
#   부르는 자는 읽기 전에 변수를 다 비운다: 명령 치환이 끝 개행을 깎아 꼬리의 빈 값은 줄째로 사라지고 `read` 가 EOF 를
#   만난다(`_site_of` 와 같은 결). 선언은 한 줄이 한 값이라 값에 줄바꿈은 들 수 없다.
decl_fields() {  # decl_fields <파일> <절> <키…>
  _dff="$1"; _dfs="$2"; shift 2
  [ -f "$_dff" ] || { for _dfk in "$@"; do echo; done; return 0; }
  awk -v sec="$_dfs" -v keys="$*" '
    BEGIN { n = split(keys, k, " ") }
    {
      line = $0
      sub(/\r$/, "", line)
    }
    line ~ /^\[/ { s = line; gsub(/[][]/, "", s); gsub(/[[:space:]]+$/, "", s); insec = (s == sec); next }
    insec {
      sub(/[[:space:]]*#.*$/, "", line)
      for (i = 1; i <= n; i++) {
        if (!(i in got) && line ~ "^"k[i]"[[:space:]]*=") {
          v = line
          sub(/^[^=]*=[[:space:]]*/, "", v); sub(/[[:space:]]+$/, "", v)
          got[i] = v
        }
      }
    }
    END { for (i = 1; i <= n; i++) printf "%s\n", (i in got ? got[i] : "") }
  ' "$_dff"
}

# ── 사용자 PATH 따라잡기 — 윈도우에서만 · 프로브가 질 때 · 프로세스에 한 번 ──────────────
#    앱은 뜰 때 PATH 를 한 번 복사한다. winget 은 깐 자리를 사용자 PATH(레지스트리)에 적는데, 그 전에 뜬 앱(VS Code ·
#    데스크탑 앱 · 터미널)과 그 자식인 이 훅은 그것을 모른다 — 방금 깐 도구가 「안 닿는다」로 서고, 다시 깔려 들면
#    winget 은 「올릴 판이 없다」(43)로 진다. 레지스트리를 한 번 읽어 뒤에 붙인다 — 이미 선 자리가 이기고, 겹친 항목은
#    해가 없다. 값은 `cygpath -p` 한 번으로 목록째 옮긴다(항목마다 부르면 그 수만큼 프로세스가 뜬다). 통과하는 프로브에는
#    안 붙는다.
#    ⚠ `//v` — Git Bash 가 `/v` 를 경로로 바꿔 넘긴다.
path_catchup() {  # 0 = 이번에 붙였다 · 1 = 붙일 것이 없거나 이미 붙였다
  [ "$OS" = windows ] || return 1
  [ -z "$PATH_CAUGHT" ] || return 1
  PATH_CAUGHT=1
  _pcu="$(reg.exe query 'HKCU\Environment' //v Path 2>/dev/null |
          sed -n 's/^.*REG_[A-Z_]*SZ[[:space:]]*//p' | tr -d '\r')"
  [ -n "$_pcu" ] || return 1
  _pcu="$(cygpath -u -p "$_pcu" 2>/dev/null)" || return 1
  [ -n "$_pcu" ] || return 1
  PATH="$PATH:$_pcu"; export PATH
}

# ── 프로브 — 유한 4갈래, 전부 실행형. 새 갈래가 필요할 때만 이 함수가 는다. 0 이면 닿는다 ──
#    npx --yes 는 갈래가 아니다 — 설치법과 도달 판정을 섞어 제3의 상태를 만든다.
#    실행 갈래의 인자는 기본 --version 이되 선언의 probe-arg 가 덮는다 — 인자를 받고도 멈추지 않는 도구가 있다(--version
#    을 받고 저장소 전체를 린트한다).
#    npm 이 깐 도구는 PATH 로 부르지 않는다. `npm install -g` 는 실행파일 앞에 셸 래퍼를 하나 더 깔고, 래퍼는 제 안에서
#    경로를 풀려고 보조 프로세스 몇을 띄운 뒤에야 node 를 부른다 — 프로세스 생성이 비싼 자리(가상 데스크톱 · 실시간 검사가
#    끼는 파일시스템)에서는 같은 패키지가 열 배 넘게 느리다. 그리고 여기서 묻는 것은 「이 이름이 PATH 에서 풀려 도나」가
#    아니라 「이 도구가 기계에 서 있나」라, 사는 자리가 `npm root -g` 한 곳인 npm 것은 그 자리에 대고 묻는 쪽이 뜻이 더
#    곧다(`probe_global` 의 node-resolvable 갈래와 같은 판단).
#    npm 패키지 이름은 인자로 받는다 — 밖의 변수를 훔쳐보면 새로 부르는 자가 그 칸을 빈 채 조용히 지나간다. 빈 값은 「npm 이
#    깐 것이 아니다」라 PATH 에서 실행해 잰다(단일 실행파일로 받은 도구 — 래퍼가 없어 애초에 빠르다).
probe_tool() {  # probe_tool <갈래> <대상> <npm패키지|빈값> [인자…]
  _k="$1"; _tg="$2"; _knp="$3"; shift 3
  [ $# -gt 0 ] || set -- --version
  case "$_k" in
    exec-on-path)      if [ -n "$_knp" ]; then
                         # ⚠ 판 떼기는 첫 글자 뒤의 `@` 만 문다(`probe_pin` 과 같은 꼴). 그냥 `%@*` 면 판 없는
                         #   스코프 패키지(`@scope/name`)가 통째로 지워져 npm 전역 뿌리 자체를 재게 되고, 그
                         #   자리는 늘 있으니 안 깔린 것도 초록이 된다.
                         case "$_knp" in ?*@*) _knp="${_knp%@*}" ;; esac
                         npm_root_g && [ -d "$NPM_ROOT_G/$_knp" ]
                       else { command -v "$_tg" >/dev/null 2>&1 ||
                              { path_catchup && command -v "$_tg" >/dev/null 2>&1; }; } &&
                            "$_tg" "$@" >/dev/null 2>&1; fi ;;
    exec-npm-bin)      [ -e "$NPM_BIN/$_tg" ] && "$NPM_BIN/$_tg" "$@" >/dev/null 2>&1 ;;
    node-resolvable)   ( cd "$PROJECT_DIR" && node --input-type=module -e "await import('$_tg')" ) >/dev/null 2>&1 ;;
    python-importable) if [ -x "$VENV_PY" ]; then "$VENV_PY" -c "import $_tg" >/dev/null 2>&1
                       else command -v "$PY_CMD" >/dev/null 2>&1 && "$PY_CMD" -c "import $_tg" >/dev/null 2>&1; fi ;;
    # 위 갈래와 딴 명제다 — venv 를 안 본다. 위는 「이 저장소의 venv 에서 import 되나」라 venv 가 서 있으면 그쪽만
    #   잰다. 전역 파이썬 패키지는 PC 의 파이썬에 서고 부르는 자도 그것을 부르므로, 위 갈래로 재면 venv 가 있는
    #   저장소에서 깔린 패키지가 ❌ 로 읽힌다.
    machine-python-importable)
                       "$PC_PY" -c "import $_tg" >/dev/null 2>&1 ;;
    python-version)    # 「깔렸나」가 아니라 「선언한 판(probe-target)과 같나」 — venv 가
                       # 서 있으면 그 판을, 아니면 venv 를 만들 판(PY_CMD)을 잰다 (판 일치)
                       if [ -x "$VENV_PY" ]; then _pv="$(py_num "$VENV_PY")"
                       else _pv="$(py_num "$PY_CMD")"; fi
                       [ -n "$_pv" ] && [ "$_pv" -eq "$(ver_num "$_tg")" ] ;;
    *) return 1 ;;
  esac
}

# npm 전역 자리 — 한 세션에 한 번만 묻는다. `npm root -g` 는 값을 내기까지 node 를 띄우는데 그 값은 세션 안에서 안
# 바뀐다 — 프로브 · 판 검사 · 진단이 저마다 물으면 도구 수만큼 되풀이되고, 프로세스가 비싼 자리에서는 그것이 곧 벽이다.
# ⚠ 값을 되돌리지 않고 변수에 세운다 — 명령 치환은 서브셸이라 캐시가 부모에 안 남는다. `$(npm_root_g)` 꼴로 부르면 매
#   호출이 제 서브셸에서 빈 캐시를 보고 다시 묻는데, 판정은 멀쩡하니 느린 것만 남고 까닭은 안 보인다. 그래서 부르는 자는
#   이것을 문장으로 부르고 값은 `$NPM_ROOT_G` 에서 읽는다.
npm_root_g() {  # 성공하면 $NPM_ROOT_G 에 자리가 선다
  [ -n "$NPM_ROOT_G_ASKED" ] || {
    NPM_ROOT_G_ASKED=1
    NPM_ROOT_G="$(npm root -g 2>/dev/null)" || NPM_ROOT_G=''
  }
  [ -n "$NPM_ROOT_G" ]
}

# npm 전역에 깔린 판 — 기계에게 묻는다. `--version` 출력을 파싱하지 않는다: 문구가 도구마다 달라 그 차이를 표로 들면 그
# 표가 곧 매핑 레이어다(규범 [Determinism First]). 패키지의 package.json 이 제 판의 진본이고 그것을 읽는 자는 node 다.
# ⚠ 경로를 JS 소스에 박지 않는다 — 인자로 넘긴다. 윈도우의 `npm root -g` 는 `C:\Users\…\node_modules` 를 내는데, 따옴표
#   사이에 그대로 넣으면 역슬래시가 이스케이프로 읽혀(`\n` 은 줄바꿈 · `\U` 는 글자가 날아간다) 이 함수가 늘 빈 값을 내고,
#   판이 정확히 깔린 기계에서도 판정이 「안 닿는다」로 굳는다. 리눅스에서만 재면 안 보이는 자리다.
npm_global_version() {  # npm_global_version <패키지 이름> — 못 읽으면 빈 값
  npm_root_g || return 1
  _nr="$NPM_ROOT_G"
  [ -f "$_nr/$1/package.json" ] || return 1
  node -e 'const p = require("path").join(process.argv[1], "package.json")
           console.log(require(p).version || "")' "$_nr/$1" 2>/dev/null
}

# ── 판 견주기 — 주기 밀기가 새 판이 있는 도구만 다시 깔게 한다 ─────────────────
#    깔린 판과 최신 판을 같은 자로 읽는다 — 글에서 처음 나오는 `숫자.숫자[.숫자]` 하나. `--version` 문구는 도구마다
#    다르지만(`ruff 0.16.9` · `version: 0.11.0`) 판 번호의 꼴은 같아, 도구마다 문구를 읽는 표 없이 규칙 하나로 선다.
#    태그도 같은 자로 읽는다(`lychee-v0.24.2` → `0.24.2`). npm 이 깐 것은 문구를 안 읽고 `npm_global_version` 이 든다.
#    못 읽으면 빈 값이고, 빈 값은 「다르다」로 간다 — 부르는 자는 그때 다시 깐다. 잘못 읽어도 치르는 값은 한 번 더 까는
#    것뿐이라 도구가 낡지는 않는다.
ver_first() { grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n 1; }

# GitHub 의 최신 릴리스 태그 — API 를 안 탄다. 최신 자산 주소가 태그 주소로 넘기는 자리에서 태그를 읽는다 — API 와
# `releases/latest` 는 막히고 받는 주소만 열린 망이 있다. 자산 이름은 아무것이나 된다 — 넘기기는 자산이 있나를 안 보고 선다.
gh_latest_tag() {  # gh_latest_tag <owner/repo> — 못 읽으면 빈 값
  curl -sS --connect-timeout "$GH_CONNECT_S" --max-time 20 -o /dev/null -w '%{redirect_url}' \
    "https://github.com/$1/releases/latest/download/_" 2>/dev/null |
    sed -n 's|.*/releases/download/\([^/][^/]*\)/.*|\1|p'
}

# GitHub 릴리스 자산 받기 — `github-release-binary` 갈래의 세 푸는 꼴이 이 한 자리를 부른다. 끝 값은 curl 의 것이다.
#   이 값들은 매달리지 않게만 한다 — 세션(auto)의 설치는 통째로 배경에서 돌아(`install_bg`) 확장의 초기화 창 밖이다.
#   걸음 전체의 시간을 호출마다 나눠 지키면 호출 수만큼 더해져 상한이 안 선다.
#   기다림은 둘로 가른다: 닿기(`--connect-timeout`)는 막힌 망의 시도를 곧 떨구고, `--max-time` 은 닿은 뒤 느린 망이 30MB
#   를 끝까지 받을 몫이다 — 시도마다 새로 잰다. 되풀이 창은 따로 안 둔다 — 되풀이는 GitHub 의 순간 5xx 와 받다가 끊긴
#   시도를 건지려는 것이라, 창을 닿기 기다림에 묶으면 그 창보다 오래 돈 시도는 되풀이가 안 나 순간 결함이 다음 설치까지
#   「안 닿는다」로 굳는다. `--speed-limit` 은 안 단다 — 사내 프록시는 검사를 마칠 때까지 한 바이트도 안 넘기기도 해
#   멎음과 느림이 바이트로는 안 갈린다(그 몫은 `--max-time` 이 든다).
gh_asset_get() {  # gh_asset_get <받을 파일> <주소>
  curl -sSfL --connect-timeout "$GH_CONNECT_S" --retry 3 --max-time 180 -o "$1" "$2"
}

tool_version_have() {  # tool_version_have <선언파일> <이름> — 깔린 판 · 못 읽으면 빈 값
  _vhi=''; _vhp=''; _vht=''; _vha=''
  { IFS= read -r _vhi; IFS= read -r _vhp; IFS= read -r _vht; IFS= read -r _vha; } <<EOF
$(decl_fields "$1" "$2" install package probe-target probe-arg)
EOF
  case "$_vhi" in
    npm-global) case "$_vhp" in ?*@*) _vhp="${_vhp%@*}" ;; esac
                npm_global_version "$_vhp" ;;
    # 파이썬 패키지는 제 메타데이터가 판의 진본이다 — npm 갈래가 package.json 을 읽는 것과 같은 결.
    #   import 이름(`PIL`)이 아니라 배포 이름(`pillow`)으로 묻는다. 최신 판과 같은 자(`ver_first`)로 읽는다 —
    #   메타데이터는 `1.2.3.post1` 꼴도 내는데 색인 쪽은 `1.2.3` 으로 읽혀, 한쪽만 누르면 판이 같아도 밀 때마다
    #   「다르다」가 된다.
    pip-user) "$PC_PY" -c 'import importlib.metadata as m, sys; print(m.version(sys.argv[1]))' "$_vhp" 2>/dev/null |
                ver_first ;;
    # winget 이 깐 것도 실행해서 읽는다 — `winget list` 는 표를 내 칸을 가려야 하고, 도구가 제 판을
    #   말하는 자리가 이미 있다.
    github-release-binary|winget)
      command -v "$_vht" >/dev/null 2>&1 || return 0
      # shellcheck disable=SC2086 # probe-arg 는 인자 여럿을 한 줄에 든다 — 갈라야 인자가 된다
      "$_vht" ${_vha:---version} 2>/dev/null | ver_first ;;
  esac
}

tool_version_latest() {  # tool_version_latest <선언파일> <이름> — 받을 판 · 못 읽으면 빈 값
  _vli=''; _vlp=''; _vlr=''; _vlt=''; _vlw=''
  { IFS= read -r _vli; IFS= read -r _vlp; IFS= read -r _vlr; IFS= read -r _vlt; IFS= read -r _vlw; } <<EOF
$(decl_fields "$1" "$2" install package repo tag winget-id)
EOF
  case "$_vli" in
    npm-global) case "$_vlp" in
                  ?*@*) printf '%s\n' "${_vlp##*@}" | ver_first ;;   # 판을 박았으면 그 판이 받을 판이다
                  *)    npm view "$_vlp" version 2>/dev/null | ver_first ;;
                esac ;;
    # pip 에게 묻는다 — PyPI 주소를 직접 안 친다. pip 은 제 설정(사내 색인 · 프록시)을 따라 묻는데, 주소를 박아 `curl`
    #   로 치면 그 설정을 비켜서 받는 길과 묻는 길이 갈린다. 첫 줄이 `pillow (12.3.0)` 꼴이라 같은 자(`ver_first`)로
    #   읽힌다. 막힌 망은 빈 값 → 다시 깐다. 기다림 · 되풀이는 pip-user 설치 칸과 같은 값이고 까닭도 그 칸이 든다.
    pip-user) "$PC_PY" -m pip index versions "$_vlp" --disable-pip-version-check --timeout 15 --retries 1 \
                2>/dev/null | ver_first ;;
    github-release-binary)
      if [ -n "$_vlt" ]; then printf '%s\n' "$_vlt" | ver_first
      else gh_latest_tag "$_vlr" | ver_first; fi ;;
    # 이 자리가 없으면 winget 도구는 밀 때마다 「설치가 졌다」로 찍힌다 — 판을 못 읽으면 고리가 다시 까는데, 이미 깔린
    #   패키지에 `winget install` 은 「올릴 판이 없다」며 0 이 아닌 값(43)으로 끝나 멀쩡한 도구에 실패 사유가 붙는다.
    # 첫 줄을 버리고 읽는다 — 첫 줄은 이름과 id 이고(`찾음 jq [jqlang.jq]`) id 에 숫자가 드는 패키지가 있다. 둘째 줄이
    #   판이다(`버전: 1.8.2` — 낱말은 로캘을 타도 숫자는 안 탄다).
    winget)
      winget.exe show --id "$_vlw" --exact --source winget --accept-source-agreements --disable-interactivity \
        2>/dev/null | sed 1d | ver_first ;;
  esac
}

probe_reach() {  # probe_reach <선언파일> <이름> — **이 저장소에서** 닿나
  # `install` · `package` 을 같이 읽는다 — 실행 갈래가 npm 래퍼를 비켜서려면 「이것이 npm 이 깐 것인가」를 알아야
  #   하는데 그 답이 선언에 있다(`probe_tool` 머리말). 같은 파일을 두 번 안 읽도록 이 한 번의 조회에 칸을 더한다.
  _prk=''; _prt=''; _pra=''; _pri=''; _prp=''
  {
    IFS= read -r _prk
    IFS= read -r _prt
    IFS= read -r _pra
    IFS= read -r _pri
    IFS= read -r _prp
  } <<EOF
$(decl_fields "$1" "$2" probe probe-target probe-arg install package)
EOF
  [ "$_pri" = npm-global ] || _prp=''
  # shellcheck disable=SC2086 # probe-arg 는 낱말 분리가 의도다
  probe_tool "$_prk" "$_prt" "$_prp" $_pra
}

probe_pin() {  # probe_pin <선언파일> <이름> — 선언이 판을 박았으면 깔린 판이 그것인가
  # 「깔렸나」와 「선언한 판인가」는 다른 명제다 — 선언이 `이름@판` 으로 판을 박았으면 그것도 잰다. 안 재면 낡은 판이
  #   깔린 기계에서 그냥 통과해 선언만 정확해진 채 실물은 그대로 간다(`python-version` 갈래가 같은 자를 든다). 판을 안
  #   박은 선언은 이 칸이 통째로 빠진다 — 최신을 받고 안 잰다. 0 이면 맞거나 안 잰다.
  # 판은 npm 전역 한 자리에 서서 저장소를 안 타므로, 저장소 갈래(`probe_decl`)와 전역 갈래(`probe_global`)가 이 몸통을 같이 쓴다.
  _ppi=''; _pk=''
  { IFS= read -r _ppi; IFS= read -r _pk; } <<EOF
$(decl_fields "$1" "$2" install package)
EOF
  [ "$_ppi" = npm-global ] || return 0
  # 스코프 패키지(@scope/name)는 맨 앞 `@` 가 판 구분자가 아니다 — 첫 글자 뒤의 `@` 만 문다.
  case "$_pk" in
    ?*@*) _pn="${_pk%@*}"; _pv="${_pk##*@}" ;;
    *) return 0 ;;
  esac
  [ -n "$_pn" ] && [ -n "$_pv" ] || return 0
  # 정확한 판이 아니면 안 잰다 — 비교가 문자열 일치라 `^21.0.0` · `latest` 를 적으면 어떤 판이 깔려도 다르고, 다시 깔아도
  #   안 바뀌는 영원한 ❌ 가 된다. 재려면 semver 해석기가 필요하고 그건 매핑 레이어다(규범 [Determinism First]).
  #   안 잰다는 사실은 `pin_shape` 가 진단 줄에 단다.
  case "$_pv" in ''|*[!0-9.]*) return 0 ;; esac
  [ "$(npm_global_version "$_pn" || true)" = "$_pv" ]
}

probe_decl() {  # probe_decl <선언파일> <이름> — 저장소의 물음. 진단이 쓰는 자다
  probe_reach "$1" "$2" || return 1
  probe_pin   "$1" "$2"
}

# ── 전역 갈래의 물음 — 저장소가 아니라 기계에게 묻는다. 0 이면 닿고 판도 맞다 ────────────────
#    `node-resolvable` 은 「이 저장소 안에서 import 되나」라 정션이 서기 전에 물으면 늘 진다 — 전역 고리가 그 물음을 쓰면
#    playwright 가 매번 지고 `npm install -g` 가 되풀이된다. 전역형 도구가 사는 자리는 `npm root -g` 이므로 거기서 묻는다:
#    그 폴더 밑에서 node 를 띄우면 맨 이름이 풀린다. 여전히 실행형이다 — 폴더가 있나로 안 묻는다(이 파일 머리말).
#    ⚠ 경로를 JS 소스에 안 박는다 — cwd 로 준다(`npm_global_version` 머리말과 같은 함정).
probe_global() {  # probe_global <선언파일> <이름>
  _pgk=''; _pgt=''
  { IFS= read -r _pgk; IFS= read -r _pgt; } <<EOF
$(decl_fields "$1" "$2" probe probe-target)
EOF
  case "$_pgk" in
    node-resolvable)
      npm_root_g || return 1
      _gr="$NPM_ROOT_G"
      ( cd "$_gr/.." 2>/dev/null &&
        node --input-type=module -e "await import('$_pgt')" ) >/dev/null 2>&1 || return 1 ;;
    *) probe_reach "$1" "$2" || return 1 ;;
  esac
  probe_pin "$1" "$2"
}

# ── 다른 손이 든 릴리스 바이너리인가 — 그 이름이 winget 자리(`GRB_FOREIGN_ROOTS`)에서 PATH 에 닿나 ──────────
#    닿으면 설치기의 winget 이 그 도구를 들고, 훅은 깔지도 올리지도 않는다 — 훅이 제 자리에 한 벌 더 놓으면 한 도구가
#    두 길로 서고, 판이 갈리는 날 PATH 앞자리가 어느 쪽이냐에 따라 조용히 어긋난다.
#    다른 손은 winget 하나다 — 배포판의 낡은 판 · 켜진 venv · 저장소 감싸개는 훅이 제 자리를 앞에 세워 일부러 가리는
#    것이라, 그것까지 다른 손으로 보면 훅이 도구를 안 깔거나 안 올린다. 리눅스는 그 자리가 비어(`GRB_FOREIGN_ROOTS`) 이
#    가름이 통째로 없다 — 훅이 `/usr/local/bin` 에 놓아 배포판 것을 가린다.
#    PATH 의 모든 자리를 본다 — Git Bash 는 `~/bin` 을 PATH 앞에 세워 첫 자리가 늘 훅 것이라, 두 벌이 된 기계에서 첫
#    자리만 보면 winget 것을 못 본다. winget 자리에서 못 찾으면 사용자 PATH 를 따라잡고 한 번 더 본다(`path_catchup` —
#    프로브가 「닿나」를 재는 것과 같은 자). 윈도우는 경로의 대소문자를 안 가려 굳힌 자리(`pwd -P`)를 낮춰서 견준다.
#    ⚠ 문장으로 부르고 값은 `GRB_FOREIGN` 에서 읽는다 — 명령 치환으로 부르면 따라잡은 PATH 가 서브셸에 갇힌다.
#    ⚠ `LOCALAPPDATA` 는 `cygpath -u` 로 옮긴다 — 글자 치환으로 안 옮긴다. Git Bash 는 윈도 PATH 를 마운트 표대로 옮겨
#      마운트 밑의 자리를 `/c/…` 가 아니라 마운트 꼴(`/tmp/…`)로 낸다 — 같은 자로 옮겨야 PATH 자리와 견줘진다. 프로세스라
#      한 실행에 한 번만 옮긴다(`GRB_FOREIGN_LAD`).
grb_foreign() {  # grb_foreign <실행 이름> — 0 = winget 의 것이 닿는다(그 경로가 `GRB_FOREIGN`) · 1 = 아니다
  GRB_FOREIGN=''
  { [ -n "$GRB_FOREIGN_ROOTS" ] && [ -n "${LOCALAPPDATA:-}" ]; } || return 1
  if [ -z "${GRB_FOREIGN_LAD:-}" ]; then
    GRB_FOREIGN_LAD="$(cygpath -u "$LOCALAPPDATA" 2>/dev/null)" || return 1
    _gfp="$(cd "$GRB_FOREIGN_LAD" 2>/dev/null && pwd -P)" && GRB_FOREIGN_LAD="$_gfp"
    GRB_FOREIGN_LAD="${GRB_FOREIGN_LAD,,}"
  fi
  _gfl="$GRB_FOREIGN_LAD"
  while :; do
    while IFS= read -r _gfp; do
      [ -n "$_gfp" ] || continue
      _gfd="$(cd "${_gfp%/*}" 2>/dev/null && pwd -P)" || continue
      _gfd="${_gfd,,}/"
      for _gfr in $GRB_FOREIGN_ROOTS; do
        case "$_gfd" in "$_gfl/${_gfr,,}/"*) GRB_FOREIGN="$_gfp"; return 0 ;; esac
      done
    done <<EOF
$(type -aP "$1" 2>/dev/null)
EOF
    path_catchup || return 1
  done
}

# ── 커밋 훅 배선 — `.githooks/` 를 둔 저장소만, 존재가 곧 선언이다. 늘 0 ───────
#    ⚠ 부르는 자리마다 맨 앞에 둔다(이 파일 머리의 「가볍고 안 죽는 것을 앞에」). SessionStart 훅은 시간이 잘리므로 망을
#      타는 당김 뒤에 서면 느린 저장소에서 훅이 여기 닿기 전에 끊기고, 게이트가 안 걸린 채 커밋이 지나간다 — 그 부재는
#      조용하다. 로컬 `git config` 한 줄이라 앞에 둬서 잃는 것이 없다.
#    `--check` 는 이것을 안 부른다 — 재는 갈래가 상태를 바꾸면 판정이 늘 초록이 된다.
wire_commit_hooks() {
  [ -d "$PROJECT_DIR/.githooks" ] || return 0
  git -C "$PROJECT_DIR" config core.hooksPath .githooks 2>/dev/null || true
}

# ── 홈 규범 · 룰 · 에이전트 · 씨앗 — 가볍고 멱등이라 설치 걸음만이 아니라 PC 매 세션(auto)에도 민다 ──
#    밀기는 견줌 뒤에 온다 — 규범 · 룰 · 에이전트 · 스킬은 손 하나(`tool_homes`)가 견주고 놓고, 씨앗은 `_push_file` 이 그
#    문이다. 재료는 claude-config 진본 한 자리다 — 저장소가 전역 사본을 지면 그 폴더가 「이 저장소 것」과 「전역 것」을
#    겸하고, 겸하면 이름으로 갈라야 하는데 그 이름이 PC 에서는 뜻이 없다. 안 붙어 있을 때 조용히 넘어가지 않는 것은 진단
#    단계의 「전역 규율」 줄이 든다 — 규율 없이 도는 세션은 스스로 그것을 모른다.
#
# ── 파일 하나를 미는 문 — 씨앗의 모든 밀기가 이 문을 지난다. 늘 0 ────────────────
#    없으면 민다 · 원본이 새것이면 민다 · 아니면 넘긴다 — 빈 홈(리모트)에서는 전부 밀리고 이미 선 홈(PC)에서는 아무것도 안
#    밀린다. 파일마다 프로세스 둘(폴더 짓기 + 복사)이라 같은 것을 매 세션 다시 옮기지 않으려는 문이다.
#    내용을 안 견주고 자리와 때로 본다 — `cmp` 는 파일마다 프로세스다. `cp` 는 사본에 지금 시각을 찍으므로 다음 세션엔
#    사본이 새것이고, 원본이 당겨져 바뀌면 그때 원본이 새것이 된다. 덮어쓰기만 한다 — 홈에만 남은 파일은 안 지운다(걷는 손은
#    deploy.ps1 씨앗 칸 하나다 — 원본 이력이 지운 파일을 기본 실행에서 걷는다).
#    판이 둘 더 있다. 견주기만 하는 판(`HOME_SYNC=check`)은 형제 저장소 세션이 홈에 밀지 않고 밀었다면 옮겼을 파일을
#    `HOME_STALE` 에 적기만 한다 — 견주는 목록을 따로 두면 미는 목록과 갈리므로 같은 문을 지난다. 바뀐 것만 보는 판
#    (`PUSH_ONLY`)은 그 목록(설정 저장소 뿌리에서 본 상대경로 · 줄로 감싼 꼴 — `pc_wide_key` 가 짓는다)에 든 원본만 본다.
#    못 밀면 PC_WIDE_FAIL 을 세운다.
_push_file() {   # _push_file <원본> <홈 사본>
  if [ -n "$PUSH_ONLY" ]; then
    case "$PUSH_ONLY" in *"
${1#"$CONFIG_ROOT"/}
"*) ;; *) return 0 ;; esac
  fi
  [ -f "$1" ] || return 0                       # 글롭이 안 맞으면 패턴 그대로 온다
  if [ "$HOME_SYNC" = check ]; then
    { [ -f "$2" ] && [ ! "$1" -nt "$2" ]; } || HOME_STALE="$HOME_STALE ${2#"$HOME/.claude/"}"
    return 0
  fi
  _pd="${2%/*}"
  [ -d "$_pd" ] || mkdir -p "$_pd" 2>/dev/null || true
  # ⚠ 바뀐 것만 보는 판은 시각 문을 안 탄다. 목록은 git 이 「판 사이에 바뀌었다」고 한 파일이라 곧 밀 것이고, 밀고
  #   나면 표식이 「이 판으로 맞췄다」를 굳힌다 — 사본이 더 새것이면(다른 클론이 딴 판을 나중에 민 자리) 시각 문이 넘겨
  #   버려 그 굳힘이 거짓이 된다. 목록만큼만 복사하므로 값도 작다.
  [ -z "$PUSH_ONLY" ] && [ -f "$2" ] && [ ! "$1" -nt "$2" ] && return 0
  cp "$1" "$2" 2>/dev/null || PC_WIDE_FAIL=1   # 진 판에 열쇠를 안 적는다
}

# ── 도구 홈의 규범 · 룰 · 에이전트 · 스킬 · Claude 훅 등록 — 손 하나를 부르고 그 줄만 읽는다. 늘 0 ──────────────
#    무엇이 어느 도구 홈에 어떤 꼴로 가나 · 제작자 칸 · 두 층 가운데 무엇이 이기나는 갈 곳 표와 손
#    (`.claude/hooks/tool-homes.py`)만 안다. 부르는 꼴 · 내는 줄 · 종료 값은 손의 머리말이 든다.
#    밀기 판은 `sync` 로, 견주기 판(`HOME_SYNC=check`)은 같은 명령에 `--dry-run` 을 붙여 부른다 — 밀었다면 바꿨을 자리가 곧
#    낡은 자리다. 손의 `check` 는 홈을 층과만 견주어, 설정 저장소가 층보다 앞선 판(형제 세션이 알려야 할 바로 그 자리)을 못
#    본다. 기록만 고치는 줄(`record`)은 파일이 이미 맞다는 뜻이라 안 센다.
#    바뀐 것만 보는 판(`PUSH_ONLY`)에서도 통째로 부른다 — 바뀐 파일이 이 일에 드나는 갈 곳 표가 드는 사실이다. 손은 바뀐
#    것이 없으면 안 쓴다.
#    내는 말 — 진 것(`ERROR=` · 0 아닌 종료)은 까닭째 내고, 밀기 판이면 열쇠를 안 적게 한다(`PC_WIDE_FAIL`). 밀기 판의
#    `WARN=` 도 낸다. 바꾼 줄은 안 낸다(내면 매 판 문맥만 문다) — 다만 손이 백업 자리로 옮기거나 떠 둔 파일(`backup`)은 한
#    줄로 댄다: 사람이 고친 파일이 제자리에서 사라진 까닭을 홈에서는 알 길이 없다. 견주기 판은 낡은 자리를 `HOME_STALE` 에 더한다.
#    손도 갈 곳 표도 없는 설정 저장소(갈 곳 표가 없던 씨앗에서 만든 것)는 말없이 지나간다 — 그 PC 의 규범은 설치기가 채운
#    표준 층에서 오고, 세션마다 경고하면 열쇠도 안 적혀 매번 다시 돈다. 표가 있는데 손이 없으면 진 것이다.
#    손이 없거나 해석기를 못 부르면 한 줄로 말하고 지나간다 — 세션 시작을 안 막는다. 해석기를 미리 불러 보지 않고 진
#    뒤에만 한 번 더 불러 까닭을 가른다(성한 판에 파이썬이 하나 더 뜨지 않게 · `plant_session_state` 와 같은 결).
tool_homes() {
  _th="$CONFIG_ROOT/.claude/hooks/tool-homes.py"
  if [ "$HOME_SYNC" = check ]; then
    _thn="도구 홈의 규범 · 룰 · 스킬 · 훅이 claude-config 와 같은지 못 쟀다"
  else
    _thn="도구 홈의 규범 · 룰 · 스킬 · 훅을 다 못 맞췄다 — 다음 세션이 다시 해 본다"
  fi
  if [ ! -f "$_th" ]; then
    [ -f "$CONFIG_ROOT/tool-homes.conf" ] || return 0
    [ "$HOME_SYNC" = check ] || PC_WIDE_FAIL=1
    echo "$PROJECT_NAME: ⚠ $_thn (손이 없다: $_th)"
    return 0
  fi
  set -- sync --layer personal --from "$CONFIG_ROOT"
  [ "$HOME_SYNC" = check ] && set -- "$@" --dry-run
  _tho="$("$PY_CMD" -X utf8 "$_th" "$@" 2>&1)"; _thr=$?
  _thf=""; _thx=""; _thb=""; _thl=""   # 진 까닭 · 계약 밖의 끝줄 · 백업한 자리 · 층 자리
  # ⚠ 파이프로 먹이지 않는다 — 고리가 하위 셸에서 돌면 `HOME_STALE` 이 밖으로 안 나온다.
  while IFS= read -r _tl; do
    _tl="${_tl%"$_CR"}"
    case "$_tl" in
      CHANGE=*)
        _tv="${_tl#CHANGE=}"; _tv="${_tv%%"$_TAB"*}"
        _tp="${_tl#*"$_TAB"}"; _tp="${_tp%%"$_TAB"*}"
        if [ "$HOME_SYNC" = check ]; then
          # 층을 채우는 줄(fill · drop)은 홈 자리 뒤에 둔다 — 알림이 앞 셋만 이름으로 든다
          case "$_tv" in
            record) ;;
            fill|drop) case " $_thl " in *" $_tp "*) ;; *) _thl="$_thl $_tp" ;; esac ;;
            *) case " $HOME_STALE " in *" $_tp "*) ;; *) HOME_STALE="$HOME_STALE $_tp" ;; esac ;;
          esac
        elif [ "$_tv" = backup ]; then
          case " $_thb " in *" $_tp "*) ;; *) _thb="$_thb $_tp" ;; esac
        fi ;;
      WARN=*)  [ "$HOME_SYNC" = check ] || echo "$PROJECT_NAME: ⚠ 도구 홈 — ${_tl#WARN=}" ;;
      ERROR=*) _thf="$_thf  · ${_tl#ERROR=}$_NL" ;;
      CHANGED=*|'') ;;
      *) _thx="$_tl" ;;   # 계약 밖의 줄 — 죽은 해석기가 남긴 stderr 다. 진 판의 까닭으로만 쓴다
    esac
  done <<EOF
$_tho
EOF
  HOME_STALE="$HOME_STALE$_thl"
  if [ -n "$_thb" ]; then
    # shellcheck disable=SC2086 # 자리 목록을 낱말로 편다(홈 아래 자리라 공백이 없다)
    set -- $_thb
    _thc="$1${2:+ · $2}${3:+ · $3}"
    [ "$#" -gt 3 ] && _thc="$_thc 외 $(($# - 3))개"
    echo "$PROJECT_NAME: 도구 홈 — 우리 것이 아니거나 옛 꼴인 파일을 백업 자리로 옮기거나 떠 두었다: $_thc (백업 자리는 tool-homes.py 머리말이 든다)"
  fi
  [ "$_thr" -eq 0 ] && [ -z "$_thf" ] && return 0
  [ "$HOME_SYNC" = check ] || PC_WIDE_FAIL=1
  if [ -n "$_thf" ]; then
    echo "$PROJECT_NAME: ⚠ $_thn (tool-homes.py):"
    printf '%s' "$_thf"
  elif ! "$PY_CMD" -c '' >/dev/null 2>&1; then
    echo "$PROJECT_NAME: ⚠ $_thn ($PY_CMD 를 못 부른다 · 윈도우면 스토어 껍데기다)"
  else
    echo "$PROJECT_NAME: ⚠ $_thn (tool-homes.py 가 exit $_thr 로 끝났다: ${_thx:-까닭 줄이 없다})"
  fi
  return 0
}

deploy_home_norms() {
  # 홈 밀기 — 읽는 값 CONFIG_ROOT · HOME_SYNC · PUSH_ONLY · 쓰는 값 HOME_STALE · PC_WIDE_FAIL · 늘 0.
  # 규범 · 룰 · 에이전트 · 스킬 — 설정 저장소마다 손을 부른다. 씨앗에서 만든 동료 저장소도 그 갈 곳 표로 제 것을 댄다.
  #   아래 씨앗 칸의 문과 무관하다.
  [ -n "$CONFIG_ROOT" ] && tool_homes
  # ⚠ 씨앗 칸의 문은 「이 저장소가 홈 씨앗의 원본인가」 — 뿌리에 `deploy.seeds.conf` 가 있나다. 그 선언은 씨앗에 안
  #   실리는 제작자 저장소의 것이라 씨앗으로 만든 동료 저장소에는 없다. 그 PC 의 홈 씨앗은 설치기가 짐에서 깐 것이고
  #   판 줄도 설치기가 적은 그대로여야 한다 — 문 없이 돌면 밀 목록이 없는데도 판 줄을 동료 저장소의 커밋으로 덮는다.
  #   문을 못 지나면 이 칸은 아무것도 안 하고 아무 말도 안 한다. 동료가 그 파일을 두면 그 저장소가 홈 씨앗의 원본이다.
  #   deploy.ps1 의 씨앗 칸(`Get-SeedColumn`)이 같은 문을 쓴다.
  _seeds_conf="$CONFIG_ROOT/deploy.seeds.conf"
  if [ -n "$CONFIG_ROOT" ] && [ -f "$_seeds_conf" ]; then
    # 사내 환경 문서와 씨앗 — 세션마다 민다. 진본은 이 저장소이고 스킬 · 형제 저장소 문서가 홈 좌표를 가리키며, 홈을
    #   진본으로 믿는 검사(`borrowed_check`)도 있다 — 홈 사본을 사람이 부르는 deploy.ps1 만 갱신하면 커밋이 쌓이는 만큼 홈만
    #   낡고, 그 검사는 낡은 판과 견준 초록을 낸다(부재보다 나쁘다).
    # 어느 폴더를 미나는 선언(`$CONFIG_ROOT/deploy.seeds.conf`)이 든다 — deploy.ps1 이 같은 줄을 읽고, `seeds/config-repo` 를
    #   일부러 안 미는 까닭도 그 머리말이 든다. 어떻게 미나(`__pycache__` 제외 · 덮어쓰기만)는 deploy.ps1 의 같은 칸과 같은 뜻이고,
    #   홈에만 남은 파일은 여기서 안 지운다 — 원본 이력으로 걷는 손은 deploy.ps1 씨앗 칸 하나다(손을 둘 두면 걷는 규칙이 갈린다).
    #   제외 한 낱말은 선언으로 안 뽑는다(선언이 좌표만 늘린다). 선언이 없는 저장소를
    #   위한 후퇴 목록은 없다 — 그 저장소는 위 문에서 끝난다. 목록을 여기 한 벌 더 두면 그것이 곧 손사본이다.
    # 씨앗이 폴더를 지므로(`seeds/gateway/app` · `_check/log`) 파일을 훑어 상대 경로를 지어 옮긴다 — deploy.ps1 이 같은
    #   자리에서 `-Recurse` + 상대경로로 하는 것과 같은 셈이다.
    # 문은 셋이다. 열쇠(`pc_wide_key`)가 먼저 서서, 홈이 같은 판으로 이미 맞춰졌으면 이 함수가 아예 안 불리고 그 뒤 바뀐
    #   것만 있으면 폴더 문 대신 `PUSH_ONLY` 목록을 걷는다 — 아래 두 문이 도는 것은 열쇠를 못 믿는 판(표식이 없다 · 판이
    #   저장소에 없다 · 오래됐다)과 열쇠를 안 보는 설치 갈래뿐이다. 폴더 문은 폴더 한 벌을 `diff` 로 견주어 같으면 `find` 와
    #   고리를 통째로 아끼고, 낱개 문(`_push_file`)은 폴더 문이 「다르다」를 낼 때 정말 다른 파일만 남긴다. 정상 상태의
    #   홈은 이미 같다 — 밀 것이 없는데 매 세션 파일마다 프로세스를 띄우면 그 비용이 곧 이 칸을 걷어내자는 말이 된다.
    #   deploy.ps1 도 파일마다 해시를 견주어 같으면 복사 계획에서 뺀다 — 여기는 그 견줌을 폴더 단위로 한 벌 할 뿐이다.
    # 홈에만 남은 파일(이름이 바뀐 씨앗의 옛 사본)이 있으면 `diff -rq` 가 그것도 「다르다」로 세어 그 폴더는 매 세션 폴더
    #   문을 못 지난다 — 그래도 낱개 문이 받아 실제로 밀리는 파일은 없다(느려지는 값은 `find` 하나와 고리뿐이다). 산문을
    #   읽어 「홈에만 있음」 줄만 걸러내려 들지 않는다: 그 문구는 로케일이 든다.
    _seed_dirs="$(awk '{ sub(/#.*/, ""); sub(/^[[:space:]]*/, ""); sub(/[[:space:]]*$/, ""); if (length) print }' "$_seeds_conf")"
    for _sd in $_seed_dirs; do
      [ -d "$CONFIG_ROOT/$_sd" ] || continue
      # 바뀐 것만 보는 판은 폴더를 안 견주고 안 훑는다 — 목록이 곧 밀 후보라 그 폴더 아래 줄만 문에 댄다(폴더 견주기는
      #   느린 파일시스템에서 폴더마다 초 단위다).
      if [ -n "$PUSH_ONLY" ]; then
        while IFS= read -r _sr; do
          case "$_sr" in */__pycache__/*) continue ;; "$_sd"/*) _push_file "$CONFIG_ROOT/$_sr" "$HOME/.claude/$_sr" ;; esac
        done <<EOF
$PUSH_ONLY
EOF
        continue
      fi
      diff -rq -x __pycache__ "$CONFIG_ROOT/$_sd" "$HOME/.claude/$_sd" >/dev/null 2>&1 && continue
      # ⚠ 파이프로 먹이지 않는다 — 고리가 하위 셸에서 돌면 견주기 판의 `HOME_STALE` 이 밖으로 안 나온다.
      while IFS= read -r _sf; do
        [ -n "$_sf" ] || continue
        case "$_sf" in */__pycache__/*) continue ;; esac
        _sr="${_sf#"$CONFIG_ROOT"/}"
        _push_file "$_sf" "$HOME/.claude/$_sr"
      done <<EOF
$(find "$CONFIG_ROOT/$_sd" -type f 2>/dev/null)
EOF
    done
    # 견주기 판은 여기까지다 — 아래 판 줄은 「민 뒤에 적는다」가 뜻이라 안 민 판에는 적을 것이 없다.
    [ "$HOME_SYNC" = push ] || return 0
    # ── 씨앗의 판 줄 — 홈 사본이 어느 판에서 왔나를 그 자리에 남긴다 ────────
    #    홈 사본을 진본으로 믿고 재는 자가 있다(`seeds/check/_check/borrowed_check.py` 의 `_stamp()`). 홈 뿌리는 git 나무가
    #    아니라 판을 물을 데가 없어, 이 줄이 없으면 낡은 홈과 견준 초록이 최신처럼 읽힌다. 이름은 그쪽 `VERSION_FILE` 이
    #    들고, 쓰는 자는 여기와 `deploy.ps1` 의 「씨앗의 판 줄」 칸 둘이다.
    #    민 뒤에 적어야 「그 판이 깔렸다」가 참이라 위 폴더 목록 밑에 선다. 판이 그대로면 안 쓴다 — 날짜 칸은 「이 판이
    #    홈에 깔린 날」이라, 매 세션 덮으면 그 날짜가 늘 오늘이 되어 낡음을 아무것도 말하지 않는다. 위 `diff` 는 이 줄을 안
    #    본다(견주는 자리는 `seeds/<이름>/` 안이고 이 줄은 뿌리 `seeds/` 에 산다) — 판 줄 때문에 폴더가 다시 밀리지 않는다.
    #    매 세션 프로세스 하나(`git rev-parse`)가 는다 — 그 값으로 홈이 어느 판인지 물을 데가 생긴다.
    _sv="$(git -C "$CONFIG_ROOT" rev-parse --short HEAD 2>/dev/null || true)"
    if [ -n "$_sv" ] && [ -d "$HOME/.claude/seeds" ]; then
      _svf="$HOME/.claude/seeds/.version"
      [ "$(awk 'NR==1{print $1}' "$_svf" 2>/dev/null)" = "$_sv" ] ||
        printf '%s %s\n' "$_sv" "$(date +%Y-%m-%d)" > "$_svf" 2>/dev/null || true
    fi
  fi
}

# ── PC 전체 일의 열쇠 — 같은 판으로 이미 맞춘 홈은 다시 안 맞춘다 ──────────────────
#    표식(`$PC_WIDE_STAMP`)의 시각은 「PC 전체를 맞춘 때」(오래되면 통째로 돈다)이고, 내용이 「어느 판으로 맞췄나」다 — 첫
#    줄이 설정 저장소의 커밋, 그 뒤 줄은 그때 커밋 안 한 채 밀린 파일. 판이 아니라 작업 나무가 홈에 간 것이라, 그 편집을
#    되돌려도 다음 세션이 그 파일을 다시 보게 적는다.
#    `pc_wide_key` 가 표식과 지금 판을 견줘 값을 세운다(늘 0):
#      PW_RUN      빈 값 = 건너뛴다 · part = 바뀐 것만 · full = 통째로
#      PW_CHANGED  바뀐 파일(뿌리 상대경로 · 줄로 감싼 꼴) — part 에서 `PUSH_ONLY` 가 된다
#      PW_REST     개인 설정 · 전역 도구 대조를 다시 하나 — PC 전체 일의 입력이 바뀌었다
#      PW_HOMESET  홈 settings.json 이 표식보다 새것이거나, 없는데 손이 되메운다(고른 제품에 Claude 가 든다) — 바뀐 파일이
#                  없어도 홈 밀기를 돌려 손이 도구 훅 등록을 되놓는다. 홈 훅 · 신뢰는 세션이 안 심는다 — 명시한 설치만
#                  심는다(plant_session_state 머리말)
#      PW_OID · PW_DIRTY  지금 판 · 커밋 안 한 파일 — `pc_wide_mark` 가 이것으로 적는다
# ⚠ 확실하지 않으면 full 이다 — 표식이 없다 · 비었다 · 판이 저장소에 없다(얕은 클론 · 이력 재작성 뒤 청소) ·
#   `UPGRADE_DAYS` 를 넘었다 · 병합이 덜 끝났다 · 경로가 따옴표로 왔다 · git 이 안 답한다. 건너뛰기가 틀리면 낡은 홈이
#   조용히 남고, 더 도는 것이 틀리면 초만 든다.
# git 에 한 번 묻는다 — `status --porcelain=v2 --branch` 가 판과 커밋 안 한 편집을 같이 낸다. 판이 바뀐 때만 `diff` 하나가
# 는다. `--no-optional-locks` 는 배경 당김(`pull_ff`)과 index 잠금을 안 다투게 한다 — status 는 틈나면 잠금을 잡고 index 를
# 되쓰는데, 그 순간 병합이 진다.
#
# 고른 제품에 Claude 가 드나 — 손(`tool-homes.py`)이 읽는 그대로 손에게 묻는다(`read_cond` · 사용자 값이 먼저 · 비면 Claude 만).
#   0 = 든다 · 1 = 안 든다 · 손이 없다. 손을 못 부르면 든다고 본다 — 부르는 `pc_wide_key` 는 모르면 도는 쪽이다.
claude_picked() {
  _cpf="$CONFIG_ROOT/.claude/hooks/tool-homes.py"
  [ -f "$_cpf" ] || return 1
  _cpo="$("$PY_CMD" - "$_cpf" 2>/dev/null <<'CPEOF'
import importlib.util, sys

sys.dont_write_bytecode = True   # 손 곁에 캐시를 흘리지 않는다 — plant_session_state 와 같은 까닭
spec = importlib.util.spec_from_file_location("tool_homes_hand", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Quiet(mod.Out):   # 모르는 이름은 손이 놓는 자리에서 알린다 — 여기는 Claude 가 들었나만 본다
    def line(self, text):
        pass


sys.stdout.write("yes" if "claude" in mod.read_cond(mod.COND_PICK, None, ("claude",), Quiet()) else "no")
CPEOF
)"
  [ "$_cpo" != no ]
}

pc_wide_key() {
  PW_RUN=full; PW_CHANGED=""; PW_REST=1; PW_HOMESET=1; PW_OID=""; PW_DIRTY=""
  [ -n "$CONFIG_ROOT" ] || return 0
  _pwst="$(git -C "$CONFIG_ROOT" --no-optional-locks -c core.quotepath=false \
             status --porcelain=v2 --branch --untracked-files=all 2>/dev/null)" || return 0
  while IFS= read -r _pwe; do
    case "$_pwe" in
      '# branch.oid '*) PW_OID="${_pwe#'# branch.oid '}" ;;
      '#'*|'') ;;
      # 1 XY sub mH mI mW hH hI <경로> · 2 … Xscore <경로><탭><옛 경로> — 앞 칸을 떼어 낸다
      '1 '*) _pwp="$_pwe"; for _pwi in 1 2 3 4 5 6 7 8; do _pwp="${_pwp#* }"; done
             PW_DIRTY="$PW_DIRTY$_pwp$_NL" ;;
      '2 '*) _pwp="$_pwe"; for _pwi in 1 2 3 4 5 6 7 8 9; do _pwp="${_pwp#* }"; done
             PW_DIRTY="$PW_DIRTY${_pwp%%"$_TAB"*}$_NL${_pwp#*"$_TAB"}$_NL" ;;
      '? '*) PW_DIRTY="$PW_DIRTY${_pwe#'? '}$_NL" ;;
      *) PW_OID=""; return 0 ;;   # u(병합이 덜 끝났다) · 모르는 꼴
    esac
  done <<EOF
$_pwst
EOF
  case "$PW_OID" in ''|*[!0-9a-f]*) PW_OID=""; return 0 ;; esac   # `(initial)` · 모르는 꼴
  [ -s "$PC_WIDE_STAMP" ] || return 0
  [ -z "$(find "$PC_WIDE_STAMP" -mtime "+$UPGRADE_DAYS" 2>/dev/null)" ] || return 0
  _pwso=""; _pwsd=""
  {
    IFS= read -r _pwso
    while IFS= read -r _pwl || [ -n "$_pwl" ]; do _pwsd="$_pwsd$_pwl$_NL"; done
  } < "$PC_WIDE_STAMP"
  [ "${#_pwso}" -ge 40 ] || return 0
  case "$_pwso" in *[!0-9a-f]*) return 0 ;; esac
  _pwc="$_NL$PW_DIRTY$_pwsd"
  if [ "$_pwso" != "$PW_OID" ]; then
    _pwd="$(git -C "$CONFIG_ROOT" -c core.quotepath=false diff --name-only "$_pwso" "$PW_OID" -- 2>/dev/null)" || return 0
    _pwc="$_pwc$_pwd$_NL"
  fi
  case "$_pwc" in *"$_NL\""*) return 0 ;; esac   # 따옴표로 감싼 경로 — 글자 그대로 못 견준다
  for _pwf in $PW_FULL_IF; do
    case "$_pwc" in *"$_NL$_pwf$_NL"*) return 0 ;; esac
  done
  PW_REST=""
  for _pwf in $PW_INPUTS; do
    case "$_pwf" in
      */) case "$_pwc" in *"$_NL$_pwf"*) PW_REST=1 ;; esac ;;
      *)  case "$_pwc" in *"$_NL$_pwf$_NL"*) PW_REST=1 ;; esac ;;
    esac
  done
  PW_HOMESET="$PW_REST"
  # 없는 settings.json 은 손이 되메울 때만 센다 — 고른 제품에 Claude 가 들면 홈 밀기의 손이 도구 훅 등록과 함께 그 파일을 다시
  #   짓는다. 안 들면 아무도 안 메워, 세면 그 PC 는 세션마다 홈 밀기를 돈다. 그 파일의 SessionStart 는 다음 설치가 심는다
  if [ -f "$HOME/.claude/settings.json" ]; then
    [ "$HOME/.claude/settings.json" -nt "$PC_WIDE_STAMP" ] && PW_HOMESET=1
  elif [ -z "$PW_HOMESET" ] && claude_picked; then
    PW_HOMESET=1
  fi
  PW_CHANGED="$_pwc"
  if [ -z "${_pwc//"$_NL"/}" ] && [ -z "$PW_HOMESET" ]; then
    PW_RUN=""
  else
    PW_RUN=part
  fi
  return 0
}

# 열쇠를 적는다(늘 0) — 적는 몸통은 여기 한 자리다. PC 전체 일을 끝내는 자리(auto · 밖에서 부른 --install · --install 의
# PC 전체 갈래)가 다 이것을 부른다. 판은 시작할 때 읽은 값(PW_OID)으로만 적는다.
# ⚠ 다 성공했고 그사이 판이 안 움직였을 때만 열쇠를 적는다. 아니면 내용을 비운 채 시각만 새로 찍는다 — 시각은 「맞추기를
#   돌았다」(형제 세션의 알림이 읽는다)라 살리고, 빈 내용은 다음 세션을 통째로 돌린다. 판이 움직이는 것은 다른 세션의 배경
#   당김이 작업 나무를 바꾼 판이다 — 무엇이 밀렸는지 섞였을 수 있다.
# 열쇠는 임시 파일에 쓰고 옮긴다 — 동시에 뜬 세션이 반쯤 쓰인 줄을 읽지 않게. 읽더라도 판이 짧거나 비면 full 이다.
pc_wide_mark() {
  if [ -n "$PC_WIDE_FAIL" ] || [ -z "$PW_OID" ] ||
     [ "$(git -C "$CONFIG_ROOT" rev-parse HEAD 2>/dev/null)" != "$PW_OID" ]; then
    : > "$PC_WIDE_STAMP" 2>/dev/null || true
    return 0
  fi
  if printf '%s\n%s' "$PW_OID" "$PW_DIRTY" > "$PC_WIDE_STAMP.$$" 2>/dev/null &&
     mv -f "$PC_WIDE_STAMP.$$" "$PC_WIDE_STAMP" 2>/dev/null; then
    return 0
  fi
  rm -f "$PC_WIDE_STAMP.$$" 2>/dev/null
  : > "$PC_WIDE_STAMP" 2>/dev/null || true
}

# ── 형제 저장소 세션의 알림 — PC 전체 일을 안 맡는 대신 맡는 자리가 비었나만 본다. 늘 0 ──
#    둘을 본다. 하나, 맡는 자리가 오래 안 돌았나 — 자동 실행을 꺼 둔 PC(동료 설치본은 고를 수 있다)는 형제 세션만 열면
#    홈이 설치 때 판에 머문다. 「돌았다」는 맞춘 때(`PC_WIDE_STAMP`)와 할 일이 없다고 본 때(`PC_WIDE_SEEN`) 가운데 새것이다.
#    표식의 판이 설정 저장소의 판과 같다는 것으로는 안 가린다 — 맡는 자리가 안 돌면 설정 저장소도 안 당겨져 둘이 같이
#    낡은 채로 같다. 둘, 홈 파일이 이 PC 의 설정 저장소와 다른가 — 미는 문을 견주기 판으로 한 번 지나게 해 밀었다면
#    옮겼을 파일만 센다.
#    막지 않는다 — 한 줄씩 말만 한다(stdout). 문구는 쉬운 말로 쓴다 — 읽는 사람이 이 훅의 낱말(「PC 전체 일」 · 「판」)을
#    모른다. 날수 기준은 도구 낡음과 같은 값(`UPGRADE_DAYS`)이다 — 둘 다 「이만큼 안 맞추면 낡았다」를 재는 자다.
#    설정 저장소가 안 붙은 자리(동료 PC · 단독 리모트)는 이 함수에 안 온다 — 그 자리는 형제 세션이 PC 전체 일을 맡는다
#    (준비 단계의 PC_WIDE). 견줄 원본도 없다.
pc_wide_notice() {
  if [ ! -f "$PC_WIDE_STAMP" ]; then
    echo "$PROJECT_NAME: ⚠ 이 PC 의 공통 설정(홈에 까는 규범 · 룰 · 스킬 · 개인 설정 · 전역 도구)을 맞춘 기록이 아직 없다 — 보통은 로그인할 때 자동으로 맞춰진다. 지금 맞추려면 claude-config 를 한 번 열거나 deploy.ps1 을 돌린다"
  elif [ -n "$(find "$PC_WIDE_STAMP" -mtime "+$UPGRADE_DAYS" 2>/dev/null)" ] &&
       { [ ! -f "$PC_WIDE_SEEN" ] || [ -n "$(find "$PC_WIDE_SEEN" -mtime "+$UPGRADE_DAYS" 2>/dev/null)" ]; }; then
    echo "$PROJECT_NAME: ⚠ 이 PC 의 공통 설정을 ${UPGRADE_DAYS}일 넘게 안 맞췄다 — 로그인할 때 도는 자동 실행이 꺼졌거나 실패하고 있는 것 같다. claude-config 를 한 번 열거나 deploy.ps1 을 돌리면 맞춰진다"
  fi
  [ -n "$CONFIG_ROOT" ] || return 0
  # 같은 열쇠를 본다 — 홈이 지금 판으로 맞춰졌다는 것이 표식으로 서 있으면 견줄 것이 없고, 그 뒤 바뀐 것만 있으면 그것만
  # 견준다. 표식을 못 믿으면 다 견준다.
  pc_wide_key
  [ -n "$PW_RUN" ] || return 0
  [ "$PW_RUN" = part ] && PUSH_ONLY="$PW_CHANGED"
  HOME_SYNC=check; HOME_STALE=""
  deploy_home_norms
  HOME_SYNC=push; PUSH_ONLY=""
  [ -n "$HOME_STALE" ] || return 0
  # shellcheck disable=SC2086 # 이름 목록을 낱말로 편다(홈 아래 상대경로라 공백이 없다)
  set -- $HOME_STALE
  _hn=$#; _hl="$1${2:+ · $2}${3:+ · $3}"
  [ "$_hn" -gt 3 ] && _hl="$_hl 외 $((_hn - 3))개"
  echo "$PROJECT_NAME: ⚠ 이 PC 홈에 깔린 규범 · 룰 · 스킬 파일이 claude-config 에 있는 최신과 다르다($_hl — 없거나 옛것) — 이 세션에는 최신 규칙이 안 실려 있다. claude-config 를 한 번 열면 다음 세션부터 맞춰진다"
}

# ── 사람에게 딸린 것 — git 신원 · 형제 저장소 · 슬러그 폴더 · 개인 키 · 홈 개인 설정 ──────
#    PC 에서만, 그리고 전역 저장소가 `personal.conf` 를 들 때만. 리모트는 저장소를 claude.ai 가 붙이고 키를 환경이 들어
#    이 칸이 통째로 조용히 지나간다. 회사 것(회사 키 · 주소 · 프록시 · 확장 · CLI)은 설치기가 자리만 보고 세우고
#    (`install.env`), 사람에게 딸린 것만 이 훅이 든다 — Claude Code 가 규격으로 보장하는 자리는 훅뿐이라, 리모트 Setup
#    script 와 설치기가 같은 한 줄(`--install`)로 선다.
#    몸통은 이름을 모른다 — 값은 전역 저장소의 `personal.conf`(git 신원 · 저장소 · 주소 꼴 · 자리)와 `secrets.env`(개인 키)가 든다.
#    가볍고 멱등인 것(git config · mkdir · 값이 같으면 건너뛰는 setx)은 매 세션(auto)도 민다 — 키가 돌면 다음 세션이 새 값을
#    심는다. 망을 타는 clone 과 자리를 재는 홈 설정 덮기는 `--install` 만.
#
# conf_get — 없으면 빈 값 · 늘 0. 부를 때마다 아무것도 스폰하지 않는다 — 파싱은 `case` 와 `${}` 로 다 된다. 앞의 공백을
#   걷고 · `이름=` 이 붙어 선 첫 줄만 들고(`이름 = 값` 은 안 든다 · 이름이 다른 이름의 앞토막인 줄도 안 든다) · 값은 첫
#   `=` 뒤 전부 · CR 은 어디 박혔든 지우고 · 꼬리 공백을 걷는다. 이름은 글자 그대로 맞춘다(선언의 이름은 다 영숫자 · 밑줄이다).
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

# 자리를 가른다 — `secrets.d/*.env` 의 `#site-probe`(닿음) → `#site-path`(경로) → `#site-default`. 이름으로 안 가른다:
# DNS 는 사외에서도 사내 IP 를 풀어 준다. 답은 파일 이름(`posco` · `outside` · `home`)이고 `$_SITE`, 그 파일은 `$_SITE_FILE`,
# 그 파일의 덮기 모드(`#home-settings`)는 `$_SITE_MODE` 에 선다. `_site_meta <파일>` 은 기본 · 프로브 · 경로 · 모드를 네 줄로 낸다.
# 묻는 자가 있을 때만 잰다 — 프로브는 안 닿는 자리에서 3초를 문다. 한 번 잰 답은 들고 다시 안 잰다 — 부르는 자가 둘이다.
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
  # 이긴 파일의 모드를 그 자리에서 들고 간다 — 고른 뒤에 다시 읽으면 같은 파일을 두 번 읽는다. 그래서 후보 셋마다 짝을 둔다.
  _sf=''; _sd=''; _sp=''; _sfm=''; _sdm=''; _spm=''
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
    case "$_default" in *yes*) _sd="$_f"; _sdm="$_mode" ;; esac
    # 프로브는 **아직 안 이긴 자리에서만** 띄운다 — 3초를 무는 자라 한 번 이기면 그 뒤는 안 잰다.
    if [ -z "$_sf" ] && [ -n "$_probe" ]; then
      if timeout 3 bash -c "(exec 3<>/dev/tcp/${_probe%%:*}/${_probe#*:})" 2>/dev/null; then
        _sf="$_f"; _sfm="$_mode"
      fi
    fi
    if [ -z "$_sp" ] && [ -n "$_path" ] && [ -d "$_path" ]; then
      _sp="$_f"; _spm="$_mode"
    fi
  done
  # 우선순위는 **프로브 > 경로 > 기본** 이다 — 망이 답한 자리가 가장 세고, 기본은 바닥이다.
  if   [ -n "$_sf" ]; then            _SITE_MODE="$_sfm"
  elif [ -n "$_sp" ]; then _sf="$_sp"; _SITE_MODE="$_spm"
  elif [ -n "$_sd" ]; then _sf="$_sd"; _SITE_MODE="$_sdm"
  fi
  _SITE_FILE="$_sf"
  [ -n "$_sf" ] && _SITE="$(basename "$_sf" .env)"
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
  # 줄끝 — 들일 때만 LF 로 누르고, 꺼낼 때는 바꾸지 않는다(input). `true` 는 체크아웃을 CRLF 로 풀어, 저장소가 LF 로
  #   못박지 않은 파일이 작업 폴더에서 CRLF 가 되고 `git apply --index` 도 LF 를 못박은 파일까지 CRLF 로 쓴다 — 배포가 같은
  #   파일을 매번 덮고 바이트로 견주는 검사가 헛돈다. `input` 은 이미 CRLF 로 풀린 작업 파일도 들일 때 LF 로 견주어
  #   「바뀌었다」로 안 세고, 새로 꺼내는 파일은 LF 로 둔다. CRLF 가 꼭 필요한 파일(`*.cmd`)은 저장소 `.gitattributes` 의
  #   `eol=crlf` 가 든다.
  git config --global core.autocrlf input
  git config --global core.longpaths true     # 260자 벽 — 깊은 나무에서 clone 이 진다
  git config --global credential.helper manager
  git config --global pull.rebase false

  # 형제 저장소 — **없는 것만 받는다.** 당김은 각 저장소의 세션(auto)과 deploy.ps1 이 든다. `--install` 만 —
  # 망을 타고, 맨바닥 VDI 의 첫 판은 설치기가 부르는 이 갈래가 지지 세션 훅의 시간 한도가 지지 않는다.
  # 받은 나무는 당김 문의 답에 세운다(`gate_fresh_clone`) — clone 은 원격 끝을 받고 그 뒤의 당김은 뒤로 못 간다.
  if [ "$1" = install ] && [ -n "$_repos" ]; then
    if [ -z "$_url" ]; then
      echo "$PROJECT_NAME: ⚠ personal.conf 에 REPOS 는 있는데 REPO_URL 이 없다 — 어디서 받을지 모른다"
    else
      mkdir -p "$_root"
      for _r in $_repos; do
        [ -d "$_root/$_r/.git" ] && continue
        echo "$PROJECT_NAME: $_r — clone ($_root)"
        # 저장소마다 초를 붙인다 — 받는 양이 저장소마다 자리 수가 다르고, 합만 보면 그 차가
        # 망 탓인지 파일 수 탓인지 안 갈린다. 진 판도 찍는다(진 데 든 시간도 시간이다).
        _ct0=$SECONDS
        git clone "$(printf '%s' "$_url" | sed "s|<이름>|$_r|g")" "$_root/$_r" ||
          echo "$PROJECT_NAME: ⚠ $_r clone 실패 — 주소 · 계정 · 망을 본다"
        printf '  · %s clone — %s초\n' "$_r" "$((SECONDS - _ct0))"
        if [ -d "$_root/$_r/.git" ]; then gate_fresh_clone "$_root/$_r"; fi
      done
    fi
  fi

  # 슬러그 폴더 — deploy.ps1 은 폴더가 있을 때만 메모리를 민다. 슬러그는 윈도우 경로에서 파생한다(영숫자 아닌 글자가
  #   전부 `-`). `cygpath` 는 루트에 한 번만 부른다 — 영숫자 아닌 글자가 전부 `-` 가 되니 루트의 슬러그 + `-`(구분자 `\`
  #   가 바뀐 것) + 이름의 슬러그로 이어붙임이 선다.
  # ⚠ 글자로 센다 — bash 의 `${//}` 는 로케일을 타서, 맨 로케일에서는 한글 한 자가 대시 여럿이 되어 슬러그가 통째로
  #   어긋나고 메모리가 조용히 안 깔린다. 그래서 셸 제 `LC_ALL` 을 `C.UTF-8` 로 세운다(bash 는 `LC_ALL` 대입에서 곧바로
  #   setlocale 을 부른다). 빌린 뒤 돌려준다 — 안 돌려주면 뒤따르는 걸음의 정렬 · 메시지가 말없이 딴 로케일에서 선다.
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

  # 개인 키 — `secrets.env` 를 사용자 환경변수로. 값이 같으면 건너뛰고, 빈 값은 안 심는다(심으면 부재가 「있다」로
  #   뒤집힌다). 평문이다 — 저장소가 private 인 것이 유일한 울타리다.
  # 이 셸에도 심는다 — setx 는 새로 뜨는 프로세스부터 걸려서, 안 심으면 뒤따르는 deploy 와 그것이 부르는 도구(`gh` 등)가
  #   방금 넣은 키를 못 본다.
  # 이 고리는 줄마다 아무것도 스폰하지 않는다 — 윈도우는 프로세스가 비싸, 줄마다 `printf | tr | sed` 를 띄우면 값 몇을
  #   심으려고 백 번을 넘게 띄운다. 파싱은 `case` 와 `${}` 로 다 되고, 버릴 줄은 다듬기 전에 버린다.
  # 자리를 타는 이름이 섞여 있다 — 바로 위에 `#only = <자리>,<자리>` 를 단 줄은 거기서만 심는다(`GOOGLE_API_KEY` 는
  #   사내에서 회사 키를 제친다). 넣는 기준은 「여기서 쓰나」가 아니라 「저쪽에서 해로운가」이고, 그 자는
  #   `docs/sites-and-keys.md` 가 든다. auto 세션은 그 줄을 아예 안 본다 — 자리를 재려면 프로브가 3초를 무는데 심는 일은
  #   `--install` 이 한다. 안 심을 뿐 걷지는 않는다 — 이미 심긴 값을 걷는 자는 없다.
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

  home_settings_seed "$1"
}

# ── 홈 개인 설정 씨앗 — 재이려면 혼자 돌 수 있어야 해서 제 이름을 갖는다 ─────
#    `deploy_personal` 안에 두면 재는 자가 그 함수를 통째로 불러야 하는데, 그쪽은 같은 호출에서 진짜 전역 git 설정과
#    환경변수를 심어 가짜 세상에서 못 돌린다. 그래서 떼어 내고, 부르는 자리는 저쪽 끝의 한 줄이다 — 이름만 떼고 안 부르면
#    걸음이 조용히 사라지므로 설정 저장소의 검사(`scripts/check-home-issue-permissions.sh`)가 그 한 줄까지 잰다.
#    ⚠ 바깥 두 문은 여기 없다 — `$OS` 가 윈도우인가와 `personal.conf` 가 있나는 저쪽 머리의 문이고, 이 함수를 직접 부르는
#      자리(검사)는 그 둘을 안 거친다. 옮기면 저쪽의 다른 걸음들이 그 문을 잃는다.
home_settings_seed() {   # home_settings_seed auto|install
  # install 만 한다 · 늘 0 · 홈 settings.json 을 쓴다(바꾸면 옆에 백업을 남긴다) · 찍는 줄은 stdout.
  # 하는 일은 둘이고 문은 하나에만 선다:
  #   덮기 — 씨앗 `vdi-home-settings.json` 으로 홈을 통째로 간다. 사람이 넣은 값이 사라지므로 자리 파일이
  #     `#home-settings = overwrite` 를 드는 자리에서만 한다. 홈에 아무것도 없으면 자리를 안 묻고 깐다 — 지울 것이 없다.
  #   얹기 — 겹침 `vdi-home-settings.private.json` 의 `permissions.allow` 줄 가운데 없는 것만 더한다. 지우는 것이 없으니
  #     어느 자리에서나 한다.
  # ⚠ 둘을 한 문 뒤에 묶지 않는다 — 얹기를 덮기의 문 뒤에 두면 홈이 남는 PC(회사 · 집)에서 걸음이 겹침을 읽기도 전에
  #   돌아선다. 문이 막아야 하는 명제는 「씨앗이 사람 설정을 덮나」 하나다.
  # `--install` 만 — 프로브는 안 닿는 자리에서 3초를 물고, 덮을 자리는 매 로그인 설치기를 거친다.
  # 겹침을 씨앗과 갈라 두는 까닭은 받는 사람이 다르다는 것이다 — 씨앗은 배포본에 실려 남에게 가는 익명 층이라, 남이 안
  #   물은 허용 규칙을 거기 적으면 조용히 함께 나간다. 겹침은 배포 목록에 없어 안 나가고, 그 파일이 없는 PC 에서는 그냥
  #   없다. 겹침이 더하는 것은 `permissions.allow` 줄뿐이다 — 넓히면 어느 쪽이 이기나를 키마다 따로 외워야 한다.
  #   깨진 겹침은 터뜨린다 — 조용히 비켜서면 규칙이 빠진 채로 서고, 그 꼴은 막힌 그 자리에서만 드러나 거기서는 못 고친다.
  [ "$1" = install ] || return 0
  _hs="$CONFIG_ROOT/vdi-home-settings.json"
  _ho="$CONFIG_ROOT/vdi-home-settings.private.json"
  _hd="$HOME/.claude/settings.json"
  [ -f "$_hs" ] || return 0
  [ -f "$_ho" ] || _ho=''
  mkdir -p "$HOME/.claude"
  # 어느 일을 하나 — `seed`(씨앗이 바탕) 또는 `add`(홈 파일이 바탕, 줄만 더한다). 자리를 묻는 것은 덮기 때문뿐이다 — 홈에
  #   파일이 없으면 묻지 않고(프로브 3초) `seed` 로 가고, 있으면 「덮어도 되나」를 한 번 묻는다. 아니라는 답은 `add` 로
  #   떨어질 뿐 돌아서지 않는다.
  _how=seed; _fresh=''
  if [ -f "$_hd" ]; then
    _site_of
    [ "$_SITE_MODE" = overwrite ] || _how=add
  else
    _fresh=1
  fi
  # 겹침이 없는 PC(동료) — `add` 갈래에는 할 일이 아예 없다.
  if [ "$_how" = add ] && [ -z "$_ho" ]; then
    return 0
  fi
  # ⚠ `hooks` 와 `env` 는 씨앗의 것이 아니라 기계가 심은 것이라 넘겨 준다. 훅의 심는 명령은 작업 루트 경로를 들어 PC
  #   마다 다르고, env 는 설치기가 이 자리 값으로 방금 민 것이다. 지킬 수 없으면(파이썬이 없다) 안 덮는다 — 덮으면 심긴
  #   훅이 지워진다.
  # 견줄 상대는 씨앗이 아니라 병합 결과다 — 씨앗과 견주면 심긴 훅 때문에 영영 안 맞아 매 로그인 덮고 백업이 쌓인다.
  #   먼저 만들고, 같으면 안 건드린다.
  _new="$_hd.new.$$"
  # 「파이썬이 없다」와 「JSON 을 못 읽었다」를 한 조건에 묶지 않는다 — 묶으면 겹침이 깨진 날 화면이 「파이썬을 못
  #   불러」라고 말해 고칠 자리를 없는 쪽으로 가리킨다. 못 했으면 못 했다고 말한다 — 규칙이 안 선 PC 에서 막히는 자리는
  #   그 세션 안이고, 거기서는 까닭을 알 길이 없다.
  if ! "$PY_CMD" -c '' >/dev/null 2>&1; then
    if [ -n "$_fresh" ]; then
      cp "$_hs" "$_hd" &&
        echo "$PROJECT_NAME: 홈 settings.json — 씨앗을 깔았다 (파이썬을 못 불러 겹침은 못 얹었다)"
    elif [ "$_how" = add ]; then
      echo "$PROJECT_NAME: ⚠ 홈 settings.json — 파이썬을 못 불러 허용 규칙을 못 얹었다"
    else
      echo "$PROJECT_NAME: ⚠ 홈 settings.json — 파이썬을 못 불러 안 덮는다 (심긴 훅을 지킬 수 없다)"
    fi
    return 0
  fi
  # 병합은 한 자리다 — `add` 는 바탕만 다르다(씨앗이 아니라 홈 파일). 조각을 둘로 두면
  #   한쪽에서 고친 사고가 다른 쪽에 안 간다.
  # 종료코드 셋 — 0 `$_new` 를 썼다 · 3 더할 줄이 없다(아무것도 안 썼다) · 그 밖은 JSON 을 못 읽었다.
  # 설치기가 `permissions` 에 심은 값의 기록 — 자리의 진본은 설치기의 `$ClaudePlantLedger`(PAISetup install.ps1)다.
  #   설치기가 없는 자리(리눅스 · 설치기를 안 돌린 PC)는 비어 넘겨 줄 것이 없다
  _hl="${LOCALAPPDATA:+$LOCALAPPDATA/Claude Code Setup/claude-settings.tsv}"
  "$PY_CMD" - "$_how" "$_hs" "$_new" "$_hd" "$_ho" "$_hl" <<'PYMERGE'
import json, sys
how, src, out, cur = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
own = sys.argv[5] if len(sys.argv) > 5 else ""
ledger = sys.argv[6] if len(sys.argv) > 6 else ""
if how == "add":
    # 바탕이 **사람 파일**이다 — 못 읽으면 터뜨린다. 못 읽은 파일을 바꿔 쓰지 않는다.
    # `utf-8-sig` — 윈도우 도구(파워셸 5.1 의 `-Encoding utf8` 등)가 쓴 파일은 BOM 을 달고, `utf-8` 로
    # 읽으면 「Unexpected UTF-8 BOM」으로 터져 그 PC 는 규칙이 영영 안 서고 매 로그인 경고만 뜬다.
    with open(cur, encoding="utf-8-sig") as f:
        cfg = json.load(f)
else:
    with open(src, encoding="utf-8") as f:
        cfg = json.load(f)
    try:
        with open(cur, encoding="utf-8-sig") as f:
            old = json.load(f)
    except (OSError, ValueError):
        old = {}
    if "hooks" in old:                  # 기계가 심은 것 — 씨앗은 이 키에 의견이 없다
        cfg["hooks"] = old["hooks"]
    if isinstance(old.get("env"), dict):  # 설치기가 이 자리 값으로 민 것 — 씨앗보다 이긴다
        cfg["env"] = {**cfg.get("env", {}), **old["env"]}
    # 설치기가 `permissions` 에 심은 값(자동 모드 · 맡기기 러너 허락)도 기계가 심은 것이라 넘겨 준다 — 그 걸음은 이 덮기보다
    #   먼저 돌아, 안 넘기면 덮을 때마다 지워진다. 넘기는 것은 기록에 들었고 옛 파일에서 값이 그대로인 것뿐이다(사람이 손으로
    #   넣은 줄은 여전히 씨앗 것으로 덮인다). 씨앗이 같은 칸을 정했으면 씨앗이 이긴다 — 사람이 씨앗에 둔 뜻이 먼저다.
    old_perm = old.get("permissions") if isinstance(old.get("permissions"), dict) else {}
    planted = []
    try:
        with open(ledger, encoding="utf-8") as f:
            planted = [ln.rstrip("\r\n").split("\t", 1) for ln in f if "\t" in ln]
    except OSError:
        pass
    for key, value in planted:
        perm = cfg.get("permissions", {})
        if not isinstance(perm, dict):   # 씨앗이 다른 꼴이면 그 칸을 안 건드린다
            break
        if key == "defaultMode" and old_perm.get(key) == value and key not in perm:
            cfg["permissions"] = {**perm, key: value}
        elif key == "allow" and value in (old_perm.get(key) or []) and isinstance(perm.get(key, []), list) \
                and value not in perm.get(key, []):
            cfg["permissions"] = {**perm, key: perm.get(key, []) + [value]}
added = 0
if own:                                 # 겹침 — `permissions.allow` 에 줄을 더한다
    with open(own, encoding="utf-8") as f:
        mine = json.load(f)             # 깨졌으면 여기서 터진다 — 셸이 사유를 낸다
    allow = cfg.setdefault("permissions", {}).setdefault("allow", [])
    for rule in mine.get("permissions", {}).get("allow", []):
        if rule not in allow:           # 같은 줄이 두 번 서면 앱이 잉여 규칙으로 경고한다
            allow.append(rule)
            added += 1
if how == "add" and not added:
    # 더할 것이 없다 — **한 바이트도 안 건드린다.** 다시 적으면 사람 파일의 들여쓰기가 매 로그인
    # 바뀌어 백업이 쌓인다(바탕이 사람 파일이라 바이트 견주기로는 멱등이 안 선다).
    raise SystemExit(3)
with open(out, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
    f.write("\n")
PYMERGE
  _prc=$?
  if [ "$_prc" = 3 ]; then
    rm -f "$_new"
    return 0
  fi
  if [ "$_prc" != 0 ]; then
    rm -f "$_new"
    if [ "$_how" = add ]; then
      echo "$PROJECT_NAME: ⚠ 홈 settings.json — JSON 을 못 읽어 허용 규칙을 못 얹었다 (홈 설정과 겹침을 본다)"
    elif [ -z "$_fresh" ]; then
      echo "$PROJECT_NAME: ⚠ 홈 settings.json — 씨앗이나 겹침의 JSON 을 못 읽어 안 덮는다 (둘을 본다)"
    elif cp "$_hs" "$_hd"; then
      # 빈 홈을 씨앗 없이 두지 않는다 — 겹침 하나가 깨졌다고 홈 설정 전체를 안 깔면 테마 · 알림 · 기능 스위치까지 함께
      #   잃는다. 고장 하나가 둘이 된다.
      echo "$PROJECT_NAME: ⚠ 홈 settings.json — 씨앗만 깔았다. 겹침의 JSON 을 못 읽어 허용 규칙이 안 섰다"
    else
      echo "$PROJECT_NAME: ⚠ 홈 settings.json — 씨앗을 못 깔았다 (쓰기 권한을 본다)"
    fi
    return 0
  fi
  if cmp -s "$_new" "$_hd"; then
    rm -f "$_new"
  elif [ -n "$_fresh" ]; then
    mv "$_new" "$_hd" && echo "$PROJECT_NAME: 홈 settings.json — 씨앗을 깔았다"
  elif cp "$_hd" "$_hd.bak-$(date +%Y%m%d-%H%M%S)" && mv "$_new" "$_hd"; then
    if [ "$_how" = add ]; then
      echo "$PROJECT_NAME: 홈 settings.json — 겹침의 허용 규칙을 얹었다 (다른 키는 안 건드렸다)"
    else
      echo "$PROJECT_NAME: 홈 settings.json — 덮었다 ($_SITE 가 overwrite 를 든다)"
    fi
  else
    rm -f "$_new"; echo "$PROJECT_NAME: ⚠ 홈 settings.json 쓰기 실패 — 쓰기 권한을 본다"
  fi
}

# ── 본 작업 폴더 — 형제가 서는 자리는 이 폴더의 부모다 ─────────────────────
#    연결된 작업 트리(`.claude/worktrees/<이름>` — 데스크탑 앱이 세션마다 만든다)의 부모는 형제 자리가 아니다 — 거기서
#    훑으면 설정 저장소를 못 찾고 다른 작업 트리를 형제로 센다. 본 작업 폴더는 git 이 댄다: 공통 git 폴더
#    (`--git-common-dir`)가 `<본 작업 폴더>/.git` 이다. 검사가 쓰는 `scripts/sibling_base.py` 와 같은 자리를 내고, 찾는 자
#    (`claude-config-path.sh`)도 같은 손을 제 안에 든다 — `sibling_base.py` 는 안 실리고, 이 앞머리는 파이썬 없이도 돈다.
#    ⚠ `--path-format=absolute` 를 안 쓴다 — 그 옵션이 없는 git(2.31 앞)의 `rev-parse` 는 모르는 옵션을 출력에 그대로
#      되돌려 틀린 자리가 조용히 선다. 맨 꼴의 답은 상대 경로(`.git`)일 수 있어 저장소 자리에서 푼다.
#    git 이 없거나 · git 나무가 아니거나 · 공통 git 폴더가 `.git` 이 아니면(맨 저장소 · 따로 둔 git 폴더 · 하위 모듈) 제
#    자리를 본 작업 폴더로 본다. 본 작업 폴더에서는 받은 글자를 그대로 낸다 — 꼴 굳히기는 `home_hook_root` 한 자리가 든다.
main_worktree() {   # main_worktree <저장소 뿌리> — 그 저장소의 본 작업 폴더를 낸다
  _mw="$(git -C "$1" rev-parse --git-common-dir 2>/dev/null)" || _mw=""
  case "$_mw" in
    */.git) (cd "$1" && cd "${_mw%/.git}" && pwd) 2>/dev/null || printf '%s' "$1" ;;
    *)      printf '%s' "$1" ;;
  esac
}

# ── 전역 SessionStart 훅을 홈에 심는다 — 심는 명령(`home_hook_cmd`) · 그 루트 · 우리 꼴 · 심기(`plant_session_state`) ──
#    저장소 훅은 세션 루트가 그 저장소일 때만 걸린다. 그 밖에서 연 세션 — 저장소들을 담은 폴더(전역 층 · deploy 가
#    `[memory:global]` 로 슬러그까지 두는 자리)나 홈 — 은 아무 훅도 안 건다. 세션마다 auto 를 다시 걸 자는 홈 훅뿐이다.
#    심는 명령은 익명이다 — 저장소 이름을 모르고 작업 루트만 든다.
#    「훅이 심겼나」와 「도구가 갖춰졌나」는 다른 명제라 심기는 설치 걸음과 따로 선다 — 지문이 맞는 세션은 설치를
#    통째로 건너뛰고 deploy.ps1 도 꺼진 검사가 있을 때만 `--install` 을 계획하므로, 한 갈래에 묶으면 도구가 멀쩡한
#    기계에서 훅만 걷힐 때 다시 심을 자가 없다. 심기는 명시한 설치(`--install`)와 심기만(`--plant`)이 부른다.
#    ⚠ 해석기는 OS 가 정한다 — 윈도우는 `python`, 리눅스는 `python3`(준비 단계의 PY_CMD). 윈도우에서 `python3` 는 스토어로
#      보내는 껍데기라 `command -v` 로 물으면 「있다」가 나오고 부르면 49 로 죽는다 — 존재로 물으면 심기가 조용히 진다.
#      그래서 불러 보고 가른다(심기는 지면 말하고, 재기 `home_hook_planted` 는 `py_num` 으로 먼저 묻는다).
#    실패는 stdout 으로 말한다 — 기록 파일에 적으면 「파일을 열어 보라」는 말은 안 열린다.
#
# ── 심는 명령의 작업 루트 — 굳힌 꼴 하나를 낸다 ──
#    작업 루트는 형제가 서는 자리(`SIBLING_BASE` — 준비 단계가 `main_worktree` 로 세운다)다 — 작업 트리에서 연 세션도 본
#    작업 폴더에서 연 세션과 같은 루트를 심고 훑는다. 심는 명령에는 이 루트가 박히므로 「심겼나」는 이름이 아니라 루트로만
#    정직하게 물을 수 있다 — 명령의 진본은 `home_hook_cmd` 한 자리고, 심는 자와 재는 자가 그것을 인자로 받는다(재는 쪽에
#    같은 꼴을 또 적으면 손사본이라 루트가 바뀐 날 둘이 말없이 갈린다).
#    ⚠ 꼴을 굳혀야 완전일치가 선다 — 윈도우에서 같은 폴더가 두 꼴(`C:/Users/…` · `/c/Users/…`)로 살고, 어느 꼴이 오는지는
#      부르는 자리에 따라 갈린다(`CLAUDE_PROJECT_DIR` 의 꼴은 하네스가 정한다). 안 굳히면 부르는 자가 바뀔 때마다 심긴
#      명령이 두 꼴 사이를 오가 세션마다 홈 설정을 다시 쓴다. 고치려는 것은 「왜 갈렸나」가 아니라 「갈려도 안 쌓이나」다.
home_hook_root() {   # 작업 루트 — 굳힌 꼴. 명령도 진단 문구도 이것을 쓴다
  _hr="$SIBLING_BASE"
  [ "$OS" = windows ] && _hr="$(cygpath -m "$_hr" 2>/dev/null || printf '%s' "$_hr")"
  printf '%s' "$_hr"
}

# ── 전역형 선언 — 기계에 하나만 서는 것들. 0 이면 전역형이다 ──────────────────────────────
#    가르는 자는 설치법이다 — 아래 다섯은 깔리는 자리가 홈 · 전역이라(npm 전역 · `~/bin` · winget 사용자 자리 · 배포판 ·
#    PC 파이썬의 사용자 자리) 저장소가 몇이든 실물은 하나다. `project-axis` 만 저장소를 탄다 — 그것의 진본은
#    `package.json` · `requirements.txt` 이고 까는 자도 따로다.
global_kind() {  # global_kind <install 값>
  case "$1" in npm-global|github-release-binary|winget|apt-package|pip-user) return 0 ;; esac
  return 1
}

# ── 이 자리에서 탈 수 있는 설치법인가 — winget 은 윈도우, apt 는 리눅스에만 선다. 0 이면 탄다 ────────────
#    못 타는 자리의 부재는 꺼진 검사가 아니다 — 선언 머리말의 약속이 「다른 자리에서는 사유를 남기고 비켜선다」인데, 이
#    가름이 없으면 설치 갈래의 nogo 가 곧 ❌ 가 되어 리눅스 세션마다 빨강이 서고 `--install` 이 1 로 끝난다 — 고칠 수 없는
#    빨강이라 진짜 빨강을 가린다. 그 자리에 이미 있으면(배포판이 들고 온 jq 등) 프로브가 먼저 초록을 낸다.
kind_here() {  # kind_here <install 값>
  case "$1" in
    winget)      [ "$OS" = windows ] ;;
    apt-package) [ "$OS" = linux ] ;;
    *)           return 0 ;;
  esac
}

# ── 전역형 선언을 든 파일들 — 줄마다 경로 하나 · 늘 0. 이름을 안 박는다 ──
#    제 것 둘이 먼저고, 그 다음 작업 루트에 붙은 저장소들의 선언이다. 훅을 든 저장소를 루트에서 훑는 것은
#    `plant_session_state` 와 같은 자를 같은 뜻으로 드는 것이다.
#    겹침은 파일이 아니라 이름으로 걷는다 — 윈도우에서 한 폴더가 두 꼴(`/c/Users/…` · `C:/Users/…`)로 살아 경로 문자열로
#    겹침을 못 판정한다. 부르는 쪽이 절 이름을 본 순서대로 한 번만 들므로, 제 것을 앞에 두어 이 저장소의 선언이 이긴다.
global_conf_list() {
  printf '%s\n%s\n' "$GCONF" "$PCONF"
  for _gc in "$(home_hook_root)"/*/.claude/tools.global.conf "$(home_hook_root)"/*/.claude/tools.conf; do
    [ -f "$_gc" ] && printf '%s\n' "$_gc"
  done
  return 0
}

# ── 한 글자를 대문자로 — 프로세스도 서브셸도 없이 ──────────────────────────
#   드라이브 문자를 굳히는 자리(`_canon_path`)에서만 쓴다. 답은 `_cpu` 에 둔다. `tr` 은 파일마다 프로세스를 하나 더 띄우고,
#   `${v^}` 는 bash 4 전용이라 `sh` 로 불린 자리에서 죽고, `$( )` 로 받으면 부를 때마다 서브셸이 선다 — `case` 는 내장이라
#   셋을 다 피한다.
_upper_one() {   # _upper_one <한 글자> — 대문자를 `_cpu` 에 둔다
  case "$1" in
    a) _cpu=A ;; b) _cpu=B ;; c) _cpu=C ;; d) _cpu=D ;; e) _cpu=E ;;
    f) _cpu=F ;; g) _cpu=G ;; h) _cpu=H ;; i) _cpu=I ;; j) _cpu=J ;;
    k) _cpu=K ;; l) _cpu=L ;; m) _cpu=M ;; n) _cpu=N ;; o) _cpu=O ;;
    p) _cpu=P ;; q) _cpu=Q ;; r) _cpu=R ;; s) _cpu=S ;; t) _cpu=T ;;
    u) _cpu=U ;; v) _cpu=V ;; w) _cpu=W ;; x) _cpu=X ;; y) _cpu=Y ;;
    z) _cpu=Z ;; *) _cpu="$1" ;;
  esac
}

# ── 경로 꼴 굳히기 — `/c/…` → `C:/…` ──────────────────────────────────────────
#   드라이브 문자는 대문자로 눌러 글롭이 내는 꼴(`home_hook_root` 의 `cygpath -m`)과 맞춘다. 답은 `_cpath` 에 둔다 —
#   `$( )` 로 받으면 부를 때마다 서브셸이 서고, 지문 한 번에 이 손을 경로마다 부른다.
_canon_path() {   # _canon_path <경로> — 굳힌 꼴을 `_cpath` 에 둔다
  _cpath="$1"
  case "$_cpath" in
    /?/*) _cpd="${_cpath#/}"; _cpd="${_cpd%%/*}"
          case "$_cpd" in
            [a-z]) _upper_one "$_cpd"; _cpd="$_cpu" ;;
          esac
          _cpath="$_cpd:/${_cpath#/?/}" ;;
  esac
}

# ── 전역형 지문 — `decl_fingerprint` 의 짝이다. 저쪽은 저장소 몫, 이쪽은 기계 몫. sha256 한 줄을 낸다 ──
#    절을 안 가리고 파일을 통째로 문다 — 전역형만 골라 담으려면 파싱해 다시 이어야 하는데, 그 이음새가 어긋나면 선언이
#    바뀌었는데 지문이 그대로가 된다(부재가 통과로 읽히는 그 자리). 넘치게 무는 쪽은 전역 갈래를 한 번 더 돌 뿐이고 그
#    갈래는 정상 상태에서 프로브뿐이다. 바이트를 내는 프로세스는 `sha256sum` 하나다 — 목록은 파이프로 먹이고, 파일은
#    `read` 로 읽어 `printf` 로 도로 낸다.
#    ⚠ 무는 바이트와 그 차례를 안 바꾼다 — 바뀌면 이미 깔린 기계의 도장이 통째로 어긋나 저장소마다 한 번씩 다시 깐다.
#      `$(<"$f")` 는 꼬리 줄바꿈을 먹어 바이트가 갈리므로 안 쓴다 — 줄바꿈 없이 끝나는 파일은 고리가 끝난 뒤 `$_gln` 에
#      남은 토막으로 잇는다.
#    무는 것은 이 기계에 붙은 전역 선언의 집합이라 순서가 없다 — 그래서 목록을 굳혀서 정렬하고 겹침을 걷는다.
#    `global_conf_list` 는 부르는 저장소의 것을 맨 앞에 놓고(그쪽의 뜻이다 — 제 선언이 이긴다) 제 저장소 선언이 앞자리와
#    글롭에 두 번 들어, 그대로 물면 저장소마다 지문이 갈리고 도장은 기계 하나라 다른 저장소를 열 때마다 전역 걸음이 선다.
#    ⚠ 경로 꼴을 먼저 굳힌다 — 윈도우에서 한 파일이 두 꼴(`/c/Users/…` 는 `PROJECT_DIR` 파생 · `C:/Users/…` 는 글롭 파생 —
#      `home_hook_root` 가 `cygpath -m` 을 탄다)로 살아, 드라이브 문자까지 한 꼴로 눌러야 `sort -u` 가 한 줄로 만든다.
#      굳히기는 순정 치환이다(`_canon_path`) — 파일마다 `cygpath` 를 부르면 프로세스가 그 수만큼 는다.
#    ⚠ 정렬은 이 자리 안에서 끝낸다 — `global_conf_list` 에 정렬을 넣으면 같은 이름의 절을 형제가 들 때 누가 이길지가
#      알파벳순이 되어 「제 저장소의 선언이 이긴다」가 깨진다. 고칠 것은 무는 방식이지 목록이 아니다.
#    한 저장소는 한 자리로 문다 — 작업 트리에서 연 세션도. 글롭은 작업 루트 바로 아래만 봐서, 본 클론 안에 선 작업 트리
#    (`.claude/worktrees/<이름>` — 데스크탑 앱 · 레인 격리)는 안 잡히고 그 저장소는 본 클론 자리로 잡힌다. 제 선언(`$GCONF`
#    · `$PCONF`)을 제 경로로 물면 한 저장소가 두 자리로 들어 같은 바이트를 두 번 씹고, 지문이 본 클론 세션과 갈려 둘이
#    번갈아 도장을 깬다. 그래서 그 세션의 제 선언은 본 클론의 자리에 세우고, 그 자리의 바이트는 제 파일에서 읽는다 —
#    선언이 같으면 본 클론 세션과 지문이 같고, 고친 선언이면 지문이 달라 그 선언이 깔린다. 작업 루트 바로 아래 선 나무
#    (본 클론 · 형제 자리에 둔 작업 트리)는 글롭이 제 경로로 이미 보므로 자리를 안 옮긴다 — 옮기면 다른 세션들이 따로
#    세는 형제 작업 트리를 이 세션만 본 클론 자리에 겹쳐 집합이 갈린다. 그 자리에서는 git 을 안 띄운다.
#    ⚠ 옮기는 것은 연결된 작업 트리의 뿌리(`.git` 이 파일)일 때뿐이다 — 세션 자리가 본 클론의 하위 폴더(`<본 클론>/sub` —
#      `CLAUDE_PROJECT_DIR` 물러섬)면 `main_worktree` 가 본 클론을 내는데, 그때 옮기면 되읽기가 본 클론 자리를 없는 하위
#      폴더 파일로 돌려 본 클론의 선언이 지문에서 빠진다.
#    겹침을 내용으로 걷지 않는다 — `tools.global.conf` 는 저장소마다 같은 바이트의 사본이라, 내용으로 걸으면 이미 깔린 모든
#    기계의 도장이 한 번씩 어긋난다.
global_fingerprint() {
  _canon_path "$PROJECT_DIR"; _gown="$_cpath"; _gmain="$_gown"
  _canon_path "${SIBLING_BASE:-}"
  [ "${_gown%/*}" = "$_cpath" ] || [ ! -f "$PROJECT_DIR/.git" ] ||
    { _canon_path "$(main_worktree "$PROJECT_DIR")"; _gmain="$_cpath"; }
  global_conf_list | {
    while IFS= read -r _gf; do
      _canon_path "$_gf"; _gf="$_cpath"
      case "$_gf" in "$_gown"/*) _gf="$_gmain${_gf#"$_gown"}" ;; esac
      printf '%s\n' "$_gf"
    done
  } | sort -u | {
    while IFS= read -r _gf; do
      case "$_gf" in "$_gmain"/*) _gf="$_gown${_gf#"$_gmain"}" ;; esac
      [ -f "$_gf" ] || continue
      _gln=""
      while IFS= read -r _gln; do printf '%s\n' "$_gln"; done < "$_gf"
      [ -n "$_gln" ] && printf '%s' "$_gln"
    done
  } | sha256sum | { read -r _gh _grest; printf '%s\n' "$_gh"; }
}

home_hook_cmd() {
  # 홈 SessionStart 에 심는 명령을 낸다 — 진본은 여기 한 자리다(인자는 `home_hook_root`).
  # 저장소 안에서 연 세션이면 이 훅은 빠진다 — 그 저장소의 제 설정이 훅을 걸므로, 쓸면 형제 전부의 훅이 돌고 연 저장소는
  #   두 번 돈다. 그래서 제 설정이 거는지 물어보고(`grep`) 안 걸 때만 여기서 직접 부른다 — 「걸 것이다」로 가정하면 설정
  #   없는 저장소가 아무것도 안 도는데 그 부재는 조용하다.
  # 저장소 밖(홈 · 전역 층)에서는 설정 저장소의 훅 하나만 부른다 — VS Code 확장은 첫 스폰을 홈 cwd 로 띄우고 초기화를
  #   60초만 기다려, 형제 훅을 차례로 다 부르면 그 60초를 넘겨 죽는다. 형제 훅은 그 저장소를 열 때 제 설정이 부른다 — 전역
  #   층에서 필요한 것은 홈 규범 · 개인 칸 · 전역 도구뿐이고 그것은 설정 저장소 훅이 든다. 이름은 안 박는다 — `deploy.ps1` 과
  #   `memory/` 를 든 저장소가 곧 그것이다(준비 단계의 CONFIG_ROOT 와 같은 자).
  # ⚠ 끝은 `exit 0` 이다 — 안 두면 고리의 마지막 시험(설정 저장소가 아닌 형제)이 명령의 종료 값이 되어, 저장소 밖에서 연
  #   세션마다 훅이 1 로 진 것으로 보인다. 글자가 바뀐 명령은 설치 갈래의 심기가 옛 항목을 걷고 한 번 갈아 심는다.
  printf 'p="$CLAUDE_PROJECT_DIR"; if [ -f "$p/.claude/hooks/session-start.sh" ]; then grep -q session-start.sh "$p/.claude/settings.json" 2>/dev/null || bash "$p/.claude/hooks/session-start.sh"; else for h in "%s"/*/.claude/hooks/session-start.sh; do d="${h%%/.claude/*}"; [ -f "$d/deploy.ps1" ] && [ -d "$d/memory" ] && bash "$h"; done; fi; exit 0' \
    "$(home_hook_root)"
}

# 홈 SessionStart 의 어느 항목이 우리 것인가 — 파이썬 정규식 하나를 낸다. 심기(`plant_session_state` 가 옛 꼴을 걷는다)와
#   재기(`home_hook_planted` 가 낡은 항목을 댄다)가 이 한 자를 받는다.
#   우리 꼴은 작업 루트를 훑는 고리다 — 이 몸통이 심어 온 홈 명령은 판마다 다 그 고리를 들었다(위 `home_hook_cmd`). 이름에
#   `session-start.sh` 가 든 다른 항목은 그 사람의 것이라 안 걷고 낡았다고도 안 한다. 첫 묶음이 그 항목의 작업 루트다 — 재기가
#   낡은 항목을 그 루트로 댄다(명령의 첫 따옴표 안은 판에 따라 루트가 아니라 `$CLAUDE_PROJECT_DIR` 다)
home_hook_shape() {
  printf '%s' 'for h in "([^"]*)"/\*/\.claude/hooks/session-start\.sh; do'
}

# ── 세션 상태를 심는다 — 한 프로세스가 다 한다. 늘 0 · 다 못 심었으면 PC_WIDE_FAIL=1 · 찍는 줄은 stdout ────────────────────────
#   드는 것: 홈 SessionStart 훅 · 작업 루트 저장소들의 폴더 신뢰(고른 도구마다 · VS Code 자체) · 데스크탑 앱 상태(아래 「폴더
#   신뢰」 칸 머리말). 읽는 값 MODE · PROJECT_DIR · CONFIG_ROOT · `home_hook_*` 셋.
#   명시한 설치(`--install`)와 심기만(`--plant`)이 부른다 — 설치기 · 로그온 자동 실행 · 사람이 바로 돌린 deploy.ps1 의 저장소마다
#   부름 · 리눅스 설정 스크립트. 심기만은 설정 저장소가 없는 PC 에서도 돈다 — 그때 고른 제품은 몸통 곁의 손(홈 씨앗에 함께
#   실린다)이 읽고, 부른 자리(홈 씨앗)는 저장소가 아니라 거는 집합에 안 넣는다(작업 루트 훑기만).
#   세션은 안 부른다 — 폴더 신뢰 창은 훅보다 먼저 떠 세션이 제 저장소에는 늘 늦고, VS Code 세션에서는 VS Code 가 떠 있어
#   그 칸이 미루기만 한다. 로그온마다 자동 실행이 바깥 `--install` 로 이것을 지난다.
# ⚠ 홈 설정 파일에서 SessionStart 밖은 안 건드린다 — Claude 도구 훅 등록은 갈 곳 표의 손이 같은 파일에 놓는다(`tool_homes`).
#   손은 SessionStart 를 안 건드리고 여기는 그 밖을 안 건드린다 — 한쪽이 상대의 항목을 제 것으로 읽으면 PC 전체 일이 도는
#   세션마다 둘이 번갈아 고쳐 쓴다.
# 파이썬을 한 번만 띄우고 그 안에서 다 한다 — 윈도우에서는 프로세스 뜨는 값이 일 자체보다 크다. 해석기가 못 뜨는 것은
#   종료코드로 안다(윈도우의 `python3` 는 부르면 49 로 죽는 스토어 껍데기다) — 존재로 묻지 않고 불러 보고 지면 말한다. 진
#   뒤에만 해석기를 한 번 더 띄워 「못 뜬다」와 「죽었다」를 가른다 — 성한 길은 프로세스 하나다.
# 옛 항목을 지운다 — 명령 글자가 바뀌면 옛 항목이 남아 옛 고리가 같이 돈다. 우리 꼴(작업 루트를 훑는 고리를 든 명령 —
#   `home_hook_shape`)만 걷고, 무엇을 걷었는지 화면에 댄다.
plant_session_state() {
  _pse="$(mktemp)"   # stderr 를 받아 둔다 — 「못 부른다」와 「죽었다」를 가르는 물증이다
  _psp="$PROJECT_DIR"; _psh="${CONFIG_ROOT:+$CONFIG_ROOT/.claude/hooks/tool-homes.py}"
  if [ "$MODE" = plant ]; then
    _psp=""
    [ -n "$_psh" ] || _psh="${_self%/*}/tool-homes.py"
  fi
  _pss="$("$PY_CMD" - "$HOME/.claude/settings.json" "$(home_hook_cmd)" "$_psp" "$(home_hook_root)" \
    "$_psh" "${_self%/*}/codex-hook-trust.py" "$MODE" "$(home_hook_shape)" \
    <<'PSSEOF' 2>"$_pse"
import contextlib, functools, importlib.util, json, os, pathlib, re, sys, tempfile

sys.dont_write_bytecode = True   # 불러 쓰는 손 · 도우미 곁에 캐시를 흘리지 않는다 — 씨앗 자리는 거울로 깔린다
settings, cmd, proj, root, hand, codex_helper, mode, shape = sys.argv[1:9]
if not shape:   # 빈 자는 모든 항목에 맞아 사람의 SessionStart 까지 걷는다 — 쓰기 전에 죽는다
    sys.exit("홈 훅 꼴(home_hook_shape)을 못 받았다")
install = mode in ("install", "plant")   # 명시한 설치 · 심기만 — 할 일이 없는 칸도 줄을 남기고, Codex 를 띄워 신뢰를 적을 수 있다
msgs = []
failed = False   # 다 못 심었다 — 끝에서 3 으로 알린다. 셸이 표식에 판을 안 적는다


def save(path, cfg, like=None, head=""):
    """JSON 으로 옆에 쓰고 옮긴다. like — 원래 글(새 파일은 빈 글). 주면 그 줄끝(LF · CRLF)과 끝 줄바꿈 유무를 따르고,
    안 주면 이 판의 기본(끝에 줄바꿈)이다. 들여쓰기는 두 칸 — Claude 가 제 설정을 쓰는 꼴과 같다. head — JSON 앞에 그대로
    다시 쓸 글(원래 글 머리의 주석 줄 · 줄끝 그대로)."""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d)
    nl = None if like is None else ("\r\n" if "\r\n" in like else "\n")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline=nl) as f:
            f.write(head.replace("\r\n", "\n") if nl else head)
            json.dump(cfg, f, ensure_ascii=False, indent=2)
            if like is None or like.endswith("\n"):
                f.write("\n")
        os.replace(tmp, path)
        return True
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        return False


@functools.lru_cache(maxsize=None)
def load_hand():
    """갈 곳 표의 손 모듈 — 손이 없는 자리는 None. 못 불러오면 예외가 그대로 올라간다."""
    if not hand or not os.path.isfile(hand):
        return None
    spec = importlib.util.spec_from_file_location("tool_homes_hand", hand)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def hand_lock():
    """갈 곳 표의 손과 같은 잠금 — 손도 같은 홈 settings.json 을 통째로 읽고 고쳐 쓴다(훅 등록).
    잠금은 손의 것을 불러 쓴다(자리 · 기다림 · 못 잡으면 `Busy`). 손이 없는 자리는 잡을 상대도 없어 그냥 간다."""
    mod = load_hand()
    if mod is None:
        return contextlib.nullcontext()
    home = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(settings))))
    return mod.Lock(home / mod.HUB)


# 홈 SessionStart 훅 — 우리 옛 꼴은 걷고 지금 꼴만 남긴다
# 우리 꼴만 걷는다 — 자는 셸의 `home_hook_shape` 한 자리가 든다. 이름에 `session-start.sh` 가 든 다른 항목은 그 사람의 것이다.
OUR_HOME_CMD = re.compile(shape)


# ⚠ 「없음」과 「못 읽음」을 가른다(아래 Claude 신뢰의 `~/.claude.json` 과 같은 규율). 못 읽은 파일을 빈 설정으로 보고
#   쓰면 훅 항목만 남기고 사람의 설정(model · env · permissions)을 통째로 덮는다 — 손으로 고친 직후가 파일이 깨지기 가장
#   쉬운 순간이다. 그래서 없을 때만 빈 설정에서 시작하고, 못 읽으면 쓰지 않고 알린다. BOM 은 읽는다(`utf-8-sig`) —
#   윈도우 편집기가 붙이는 것이라 깨진 것이 아니다.
def plant_home_hook():
    global failed
    cfg_ok = True
    try:
        with open(settings, encoding="utf-8-sig") as f:
            cfg = json.load(f)
        if not isinstance(cfg, dict):
            raise ValueError("최상위가 객체가 아니다")
    except FileNotFoundError:
        cfg = {}
    except (OSError, ValueError):
        cfg, cfg_ok, failed = {}, False, True
        msgs.append("  ! 홈 settings.json 을 못 읽었다 — 덮어쓰지 않았다. JSON 문법을 고치면 다음 설치가 훅을 심는다")
    entries = cfg.setdefault("hooks", {}).setdefault("SessionStart", [])
    have, dropped = False, []
    for e in entries:
        keep = []
        for h in e.get("hooks", []):
            c = h.get("command", "")
            if c == cmd:
                have = True
                keep.append(h)
            elif OUR_HOME_CMD.search(c):
                dropped.append(c)
            else:
                keep.append(h)
        e["hooks"] = keep
    entries[:] = [e for e in entries if e.get("hooks")]
    if not have:
        entries.append({"hooks": [{"type": "command", "command": cmd, "timeout": 600}]})
    if cfg_ok and (not have or dropped):
        if save(settings, cfg):
            if not have:
                msgs.append("  홈 SessionStart 훅 — 심었다")
            for c in dropped:
                msgs.append("  홈 SessionStart 훅 — 옛 항목을 걷었다: %s" % c[:70])
        else:
            msgs.append("  ! 홈 settings.json 을 못 썼다 — 쓰기 권한을 본다")
            failed = True


# 읽기부터 쓰기까지 손의 잠금 안에서 한다 — 두 세션이 함께 돌면 한쪽의 고침이 다른 쪽의 통째 쓰기에 덮인다.
#   못 잡거나 손을 못 불러오면 이번엔 안 심고 3 으로 알린다 — 다음 설치가 다시 심는다.
try:
    with hand_lock():
        plant_home_hook()
except Exception as e:  # 손의 `Busy` · 손을 못 불러옴
    failed = True
    msgs.append("  ! 홈 SessionStart 훅 — 손의 잠금을 못 잡아 이번엔 안 심었다(다음 설치가 다시 심는다): %s" % e)

# 폴더 신뢰 — 작업 루트의 우리 저장소에만, 고른 도구(Claude · Codex · agy · Copilot)마다 건다. VS Code 자체의 작업 영역 신뢰는
#   고른 도구와 관계없이 VS Code 가 있으면 건다. 고른 도구의 데스크탑 앱 프로젝트 목록(Codex · agy)과 Codex 데스크탑의 기본
#   권한도 이 칸이 같은 규칙(떠 있으면 미룸 · 사람이 뺀 것은 둠)으로 든다.
# 거는 집합은 하나다(`targets`) — 이 저장소와 작업 루트 바로 아래 저장소 가운데 세션 훅(`.claude/hooks/session-start.sh`)이
#   우리 표지를 든 것. 네 도구 · VS Code · 데스크탑 목록이 다 이 목록을 받는다. 그 밖의 폴더는 그대로 묻는다. 신뢰 창은 도구가
#   훅보다 먼저 띄우므로 저장소를 처음 열기 전에 서 있어야 한다 — 설치기 · 로그인 자동 실행이 부르는 `--install` 이 그 자리다.
# 고른 제품은 손이 읽는 그대로 읽는다(사용자 값이 먼저 · 비면 Claude 만). 손을 못 부르면 Claude 는 비었을 때의 뜻대로
#   걸고, Codex · agy · Copilot 은 안 건다 — 고른 줄 모르는 도구에 신뢰를 넓히지 않는다.
# 다 손이 쓰는 파일이 아니라 손의 잠금을 안 잡는다. `~/.claude.json` 은 Claude 가, Codex 설정은 Codex 의 쓰는 자(판
#   맞추기)가, agy · Copilot 설정은 그 도구가 경합을 든다. VS Code 의 DB 는 도우미가 SQLite 거래로 든다.
# 역슬래시는 글자로 안 적고 `chr(92)` 로 짓는다 — 셸을 지나는 글에 박은 역슬래시는 인용 꼴에 따라 삼켜질 수 있다.
BS = chr(92)
CLAUDE, CODEX, AGY = "claude", "codex", "agy"   # 고른 제품 값의 이름 — 갈 곳 표의 도구 이름이다
COPILOT = "copilot"   # 고른 제품 값에 들지만 갈 곳 표에 길이 없다 — 폴더 신뢰만 건다
import glob as _glob
# 우리 표지 — 원본은 설치기 `install.ps1` 의 `Test-OurMark` 다. 설치기는 파워셸 · 여기는 파이썬이라 가리킬 수 없어 같은
#   정규식을 여기서 짓는다 — 어긋나면 설치기가 넘긴 훅과 신뢰를 거는 훅이 다른 답을 낸다. 같은 표본으로 두 자리를 무는 것은
#   설정 저장소의 검사(`scripts/check-home-hook.sh`)가 든다. `-match` 처럼 대소문자를 안 가리고, 못 읽으면 우리 것이 아니다.
OUR_HOOK = (".claude", "hooks", "session-start.sh")
MARK_LINES = 12
_MARK_AT = re.escape("claude-config/" + "/".join(OUR_HOOK))
OUR_MARK = re.compile(r"^\s*(#|//).*(?:(?:진본|원본)은 " + _MARK_AT + r" 다|\(진본: " + _MARK_AT + r"\))", re.IGNORECASE)
GITDIR_PREFIX = "gitdir:"


def our_hook(repo):
    try:
        with open(os.path.join(repo, *OUR_HOOK), encoding="utf-8-sig", errors="replace") as f:
            return any(OUR_MARK.match(ln) for _, ln in zip(range(MARK_LINES), f))
    except OSError:
        return False


def main_checkout(p):
    """git 작업 트리면 그 본 저장소 — `.git` 이 파일이고 그 `gitdir` 에 `commondir` 이 있으면 작업 트리다. 작업 트리를 못 풀면
    None(뺀다) — 작업 트리마다 신뢰 줄 · 데스크탑 프로젝트가 생기고 지우면 찌꺼기로 남는다. `gitdir` 이 없는 `.git` 파일(본
    저장소에서 걷힌 작업 트리)도 못 푼 것이다. 작업 트리가 아니면 그대로."""
    dotgit = os.path.join(p, ".git")
    if not os.path.isfile(dotgit):
        return p
    try:
        with open(dotgit, encoding="utf-8") as f:
            line = f.readline().strip()
        if not line.startswith(GITDIR_PREFIX):
            return None
        gitdir = os.path.join(p, line[len(GITDIR_PREFIX):].strip())   # 절대 경로면 그대로 선다
        if not os.path.isdir(gitdir):
            return None
        common_file = os.path.join(gitdir, "commondir")
        if not os.path.isfile(common_file):
            return p   # 하위 모듈 — 제 저장소다
        with open(common_file, encoding="utf-8") as f:
            common = os.path.normpath(os.path.join(gitdir, f.readline().strip()))
    except OSError:
        return None
    return os.path.dirname(common) if os.path.basename(common) == ".git" else None


# 겹침은 경로를 고른 꼴로 가린다 — 이 저장소는 문지기가 넘긴 철자(`C:/…/x`)로, 작업 루트 아래는 훑은 철자(`C:/…\x`)로 와 글자가 갈린다.
#   집합에는 처음 온 철자를 둔다. 윈도는 대소문자도 안 가린다(`normcase`).
targets, _target_keys = [], set()
for t in ([proj] if proj else []) + [os.path.dirname(os.path.dirname(os.path.dirname(h)))
                   for h in _glob.glob(os.path.join(root, "*", *OUR_HOOK))]:
    r = main_checkout(t)
    k = r and os.path.normcase(os.path.normpath(r))
    if r and k not in _target_keys and our_hook(r):
        targets.append(r)
        _target_keys.add(k)


def picked():
    """고른 제품 가운데 이 칸이 거는 넷 — 손을 못 부르면 None."""
    mod = load_hand()
    if mod is None:
        return None

    class Quiet(mod.Out):   # 모르는 이름은 손이 놓는 자리에서 알린다 — 여기는 넷이 들었나만 본다
        def line(self, text):
            pass
    return mod.read_cond(mod.COND_PICK, None, (CLAUDE, CODEX, AGY, COPILOT), Quiet())


try:
    tools, pick_why = picked(), "갈 곳 표의 손이 없다"
except Exception as e:  # 손을 못 불러옴
    tools, pick_why = None, "손을 못 불렀다: %s" % e


# Claude — `~/.claude.json`(`CLAUDE_CONFIG_DIR` 가 서면 그 안)의 `projects` 에 건다. Claude 는 철자 그대로 맞추므로 받은 철자와
#   사람이 치는 철자(`typed_spellings`)마다 구분자 두 벌 × 드라이브 글자 두 벌로 건다(윈도 — 저장소마다 여덟 남짓). 드라이브
#   글자도 두 벌인 까닭 — 우리 경로는 `C:` 로 오는데 VS Code 는 드라이브 글자를 소문자(`c:`)로 다룬다. 켜서 잃는 것이 없다.
# 더하기만 한다 — 철자 여럿 가운데 어느 쪽이 살아 있나는 PC 마다 달라, 지우는 규칙은 살아 있는 쪽을 지울 수 있다. 이미
#   다 켜져 있으면 안 쓴다 — 돌고 있는 Claude 가 쥔 파일이라 쓸 때마다 경합한다. 이 세션에는 안 먹을 수 있다 — Claude 가
#   제 메모리 판으로 나중에 덮으면 다음 세션부터 선다.
# ⚠ 없는 것과 못 읽은 것을 가른다 — 없으면 `projects` 만 든 파일을 새로 짓는다(첫 실행의 안내는 그대로 돌고 심은 항목은
#   산다). 못 읽은 것(앱이 쓰는 도중 · 깨졌다 · 꼴이 다르다)은 손대지 않고 진 것으로 알린다 — 안 알리면 진 판이 PC 전체
#   일의 표식에 「맞췄다」로 적힌다. 다시 거는 것은 다음 설치다. 쓸 때는 원래 글의 줄끝과 끝 줄바꿈을 따른다.
def _drive_cases(p):
    return {p[0].upper() + p[1:], p[0].lower() + p[1:]} if len(p) > 1 and p[1] == ":" else {p}


def disk_spelling(p):
    """그 자리의 디스크 철자 — 윈도면 `realpath`(대소문자를 디스크대로), 그 밖은 경로를 고른 꼴."""
    return os.path.realpath(p) if os.name == "nt" else os.path.normpath(p)


def typed_spellings(p):
    """사람이 그 자리를 여는 흔한 철자 — 디스크 철자와 통째 소문자에 드라이브 글자 두 벌(윈도). 철자 그대로 맞추는
    도구(Claude · agy)에 이 꼴을 다 건다 — 탐색기 · VS Code · 탭 완성은 디스크 철자를, 손으로 친 경로는 대개 통째 소문자를
    준다. 대소문자를 섞어 친 꼴은 못 덮는다. 윈도 밖은 철자가 하나다."""
    d = disk_spelling(p)
    if os.name != "nt":
        return [d]
    out = []
    for b in (d, d.lower()):
        for v in ((b[:1].upper() + b[1:], b[:1].lower() + b[1:]) if len(b) > 1 and b[1] == ":" else (b,)):
            if v not in out:
                out.append(v)
    return out


def plant_claude():
    global failed
    # 받은 철자 · 사람이 치는 철자마다 구분자 두 벌 × 드라이브 글자 두 벌
    forms = sorted({v for t in targets for b in {t, *typed_spellings(t), *([t.lower()] if os.name == "nt" else [])}
                    for f in (b.replace("/", BS), b.replace(BS, "/")) for v in _drive_cases(f)})
    cdir = os.environ.get("CLAUDE_CONFIG_DIR")
    tp = os.path.join(cdir or os.path.expanduser("~"), ".claude.json")
    shown = tp if cdir else "~/.claude.json"
    try:
        with open(tp, encoding="utf-8", newline="") as f:
            like = f.read()
        tcfg = json.loads(like)
        pr = tcfg.get("projects", {}) if isinstance(tcfg, dict) else None
        if not isinstance(pr, dict) or any(not isinstance(pr.get(k, {}), dict) for k in forms):
            raise ValueError("최상위 · projects · 그 항목이 객체가 아니다")
    except FileNotFoundError:
        like, tcfg = "", {}
    except (OSError, ValueError):
        failed = True
        msgs.append("  ! 신뢰(Claude) — %s 를 못 읽었다 — 손대지 않았다. 다음 설치가 다시 건다" % shown)
        return
    pr = tcfg.setdefault("projects", {})
    todo = [k for k in forms if not pr.get(k, {}).get("hasTrustDialogAccepted")]
    if not todo:
        if install:
            msgs.append("  신뢰(Claude) — 이미 다 걸려 있다 (%d 자리)" % len(forms))
        return
    for k in todo:
        pr.setdefault(k, {})["hasTrustDialogAccepted"] = True
    if save(tp, tcfg, like):
        msgs.append("  신뢰(Claude) — %s%d 자리에 걸었다 (다음 세션부터 안 묻는다)"
                    % ("" if like else "%s 이 없어 새로 짓고 " % shown, len(todo)))
    else:
        failed = True
        msgs.append("  ! 신뢰(Claude) — %s 를 못 썼다 — 다음 설치가 다시 건다" % shown)


def codex_helper_module():
    """몸통 곁의 Codex 신뢰 도우미 — 없으면 None."""
    if not os.path.isfile(codex_helper):
        return None
    spec = importlib.util.spec_from_file_location("codex_hook_trust", codex_helper)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Codex — 몸통 곁의 Codex 신뢰 도우미가 `config.toml` 의 `projects` 에 Codex 제 철자로 적는다(도우미 머리말).
# app-server 는 명시한 설치 · 심기만(MODE 가 install · plant)일 때만 띄운다 — 아니면 설정 파일만 보고 빈 자리를 말한다(Codex
#   가 느리거나 서면 오래 걸린다). 이 칸을 부르는 자리는 다 그 둘이다(plant_session_state 머리말).
# 못 걸어도 진 것으로 안 돌린다(표식은 적는다) — 진 까닭이 Codex 쪽에 있으면 다음 설치도 똑같이 져, 그때마다 PC 전체 일을
#   통째로 다시 돈다. 줄은 늘 남기고, 다시 거는 것은 다음 설치가 든다.
def plant_codex(mod):
    try:
        states, _ = mod.plant_projects(targets, mod.codex_home(None), start=install)
    except mod.Stop as s:
        msgs.append("  ! 신뢰(Codex) — 못 걸었다: %s" % s.line)
        return
    now = sum(1 for _, s in states if s == mod.P_NOW)
    kept = sum(1 for _, s in states if s == mod.P_KEPT)
    empty = sum(1 for _, s in states if s is None)
    if now:
        msgs.append("  신뢰(Codex) — %d 자리에 걸었다 (다음 열기부터 안 묻는다)" % now)
    if empty:
        msgs.append("  신뢰(Codex) — %d 자리가 비었다 — 세션은 Codex 를 안 띄운다. 다음 설치(로그인 자동 실행 · --install)가 건다"
                    % empty)
    if install and kept:
        msgs.append("  신뢰(Codex) — 사람이 「신뢰 안 함」으로 둔 %d 자리는 안 덮었다" % kept)
    if install and not (now or empty or kept):
        msgs.append("  신뢰(Codex) — 이미 다 걸려 있다 (%d 자리)" % len(states))


# Codex 데스크탑 — 저장소 뿌리를 데스크탑 프로젝트 목록(제 상태 파일)에 더한다(도우미 `plant_desktop_projects`). 신뢰는
#   앞 칸이 이미 걸어, 더한 프로젝트는 열 때 안 묻는다. 데스크탑이 떠 있으면 안 쓰고 미룬다 — 이번 설치가 띄운 창은 설치기가
#   이 걸음 앞에서 닫는다. 사람이 목록에서 뺀 저장소는 다시 안 넣는다.
# 못 더해도 진 것으로 안 돌린다 — 신뢰와 같은 까닭이다. 다시 더하는 것은 다음 설치가 든다.
def plant_codex_desktop(mod):
    label = "  프로젝트(Codex 데스크탑) — "
    try:
        states, held = mod.plant_desktop_projects(targets, mod.codex_home(None))
    except mod.Stop as s:
        msgs.append("  ! 프로젝트(Codex 데스크탑) — 못 더했다: %s" % s.line)
        return
    now = sum(1 for _, s in states if s == mod.DP_NOW)
    gone = sum(1 for _, s in states if s == mod.DP_GONE)
    if now:
        msgs.append(label + "%d 개 더했다 (다음에 데스크탑을 열면 보인다)" % now)
    if held == mod.DP_RECORD:   # 저절로 안 풀린다 — 말 수를 줄이는 판(MODE 가 install 이 아님)에서도 알린다
        msgs.append("  ! 프로젝트(Codex 데스크탑) — 우리 기록(%s)을 못 읽어 아무것도 안 더했다(사람이 뺀 것을 다시 넣지 않으려고)"
                    % mod.DESKTOP_SEEN)
    if not install:
        return
    if held == mod.DP_RUNNING:
        msgs.append(label + "데스크탑이 떠 있어 미뤘다 — 닫힌 뒤의 다음 설치가 더한다")
    elif held == mod.DP_UNKNOWN:
        msgs.append(label + "데스크탑이 떠 있는지 못 가려 미뤘다 — 다음 설치가 다시 본다")
    elif held == mod.DP_NEVER:
        msgs.append(label + "데스크탑을 아직 한 번도 안 띄웠다 — 띄운 뒤의 다음 설치가 더한다")
    elif held == mod.DP_OFF:
        msgs.append(label + "윈도에서만 더한다 — 건너뛰었다")
    if gone:
        msgs.append(label + "사람이 목록에서 뺀 %d 개는 다시 안 넣었다" % gone)
    if held is None and not (now or gone):
        msgs.append(label + "이미 다 들어 있다 (%d 개)" % len(states))


# Codex 데스크탑 권한 — 같은 상태 파일의 로컬 호스트 권한 모드를 「나 대신 승인」으로 쓴다(도우미 `plant_desktop_agent_mode`).
#   지금 값이 무엇이든 그 한 칸만 쓰고 기록은 안 남긴다 — 설치마다 다시 쓴다. 상태 파일이 없으면 안 짓고, 데스크탑이 떠 있으면 미룬다
#   (설치기는 이번에 깐 Codex 를 설치 끝에 로그인이 섰을 때만 닫고 부른다). 못 심어도 진 것으로 안 돌린다 — 프로젝트 칸과 같은 까닭이다.
def plant_codex_desktop_mode(mod):
    label = "  권한(Codex 데스크탑) — "
    try:
        state, held = mod.plant_desktop_agent_mode(mod.codex_home(None))
    except mod.Stop as s:
        msgs.append("  ! 권한(Codex 데스크탑) — 못 심었다: %s" % s.line)
        return
    if state == mod.DM_NOW:
        msgs.append(label + "새 대화의 기본을 「나 대신 승인」으로 심었다 (계정이 안 열면 앱이 「승인 요청」으로 둔다)")
    if not install:
        return
    if held == mod.DP_RUNNING:
        msgs.append(label + "데스크탑이 떠 있어 미뤘다 — 닫힌 뒤의 다음 설치가 심는다")
    elif held == mod.DP_UNKNOWN:
        msgs.append(label + "데스크탑이 떠 있는지 못 가려 미뤘다 — 다음 설치가 다시 본다")
    elif held == mod.DP_NEVER:
        msgs.append(label + "데스크탑을 아직 한 번도 안 띄웠다(상태 파일을 안 지어 둔다) — 띄운 뒤의 다음 설치가 심는다")
    elif held == mod.DP_OFF:
        msgs.append(label + "윈도에서만 심는다 — 건너뛰었다")
    elif state == mod.DM_HAVE:
        msgs.append(label + "이미 「나 대신 승인」이다")


# agy CLI · Copilot CLI — 제 설정 JSON 의 목록 하나에 저장소 뿌리를 한 줄씩 더한다(두 도구의 데스크탑 · VS Code 확장은 안
#   묻는다). 줄은 디스크 철자로 짓고(윈도 — `realpath`), 이미 섰나는 그 도구가 맞추는 법대로 가린다.
#   agy — `~/.gemini/antigravity-cli/settings.json` 의 `trustedWorkspaces`. 작업 폴더 글을 **철자 그대로** 맞춘다 — 대소문자만
#     다른 줄은 다른 자리라, 사람이 치는 철자(`typed_spellings` — 디스크 · 통째 소문자 × 드라이브 글자)마다 한 줄씩 건다
#   Copilot — `config.json`(`COPILOT_HOME` 이 서면 그 안, 아니면 `~/.copilot`)의 `trustedFolders`. 대소문자 없이 맞추고 아래
#     폴더까지 덮는다
# app-server 같은 것 없이 파일만 쓴다 — MODE 와 관계없이 건다. 새 파일은 두 도구가 제 설정을 쓰는 꼴(두 칸 · LF · 끝
#   줄바꿈)로 짓고, 있던 파일은 원래 줄끝 · 끝 줄바꿈을 따른다. 없던 파일을 지어도 두 도구가 첫 실행에 그대로 읽는다.
# ⚠ 머리의 `//` 주석 줄은 살린다 — Copilot 이 제 `config.json` 맨 위에 두 줄을 단다. 그 밖의 주석이 든 글은 못 읽는 글이다.
# 못 걸어도 진 것으로 안 돌린다 — Codex 와 같은 까닭이다. 못 읽는 파일은 그 도구의 것이라 다음 설치에도 못 읽는다.
#   손대지 않고 줄만 남기며, 다시 거는 것은 다음 설치가 든다.
LISTED_NEW_LIKE = "\n"   # save 에 넘기는 「원래 글」 — LF · 끝 줄바꿈
LINE_COMMENT = "//"


def listed_files():
    """{도구: (파일, 보일 이름, 목록 열쇠, 대소문자를 안 가리나)} — 목록 꼴로 신뢰를 드는 둘."""
    cph = os.environ.get("COPILOT_HOME")
    return {AGY: (os.path.join(os.path.expanduser("~"), ".gemini", "antigravity-cli", "settings.json"),
                  "~/.gemini/antigravity-cli/settings.json", "trustedWorkspaces", False),
            COPILOT: (os.path.join(cph or os.path.join(os.path.expanduser("~"), ".copilot"), "config.json"),
                      os.path.join(cph, "config.json") if cph else "~/.copilot/config.json", "trustedFolders", True)}


def split_head(text):
    """(머리의 `//` 주석 줄들, 나머지 글) — 줄끝은 그대로 둔다."""
    lines = text.splitlines(keepends=True)
    n = 0
    while n < len(lines) and lines[n].lstrip().startswith(LINE_COMMENT):
        n += 1
    return "".join(lines[:n]), "".join(lines[n:])


def plant_listed(label, path, shown, key, fold):
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            like = f.read()
        head, body = split_head(like)
        cfg = json.loads(body)
        ws = cfg.get(key, []) if isinstance(cfg, dict) else None
        if not isinstance(ws, list) or any(not isinstance(w, str) for w in ws):
            raise ValueError("최상위가 객체가 아니거나 %s 가 글 목록이 아니다" % key)
    except FileNotFoundError:
        like, head, cfg, ws = None, "", {}, []
    except (OSError, ValueError):
        msgs.append("  ! 신뢰(%s) — %s 를 못 읽었다 — 손대지 않았다. 다음 설치가 다시 건다" % (label, shown))
        return
    same = (lambda p: os.path.normcase(os.path.normpath(p))) if fold else os.path.normpath
    have = {same(w) for w in ws}
    roots = {}
    for t in targets:   # 대소문자를 가리는 도구(agy)는 사람이 치는 철자마다, 안 가리는 도구는 디스크 철자 하나로
        for s in ([disk_spelling(t)] if fold else typed_spellings(t)):
            roots.setdefault(same(s), s)
    todo = [p for k, p in roots.items() if k not in have]
    if not todo:
        if install:
            msgs.append("  신뢰(%s) — 이미 다 걸려 있다 (%d 자리)" % (label, len(roots)))
        return
    cfg[key] = ws + todo
    if save(path, cfg, LISTED_NEW_LIKE if like is None else like, head):
        msgs.append("  신뢰(%s) — %s%d 자리에 걸었다 (다음 열기부터 안 묻는다)"
                    % (label, "%s 이 없어 새로 짓고 " % shown if like is None else "", len(todo)))
    else:
        msgs.append("  ! 신뢰(%s) — %s 를 못 썼다 — 다음 설치가 다시 건다" % (label, shown))


# agy 데스크탑 — 몸통 곁의 도우미(`agy-desktop-projects.py`)가 저장소 뿌리를 Antigravity 의 프로젝트 목록(프로젝트 하나에
#   파일 하나)에 더한다. agy 를 고를 때만이다. 앱이 떠 있으면 미루고, 사람이 목록에서 뺀 저장소는 다시 안 넣는다.
# 못 더해도 진 것으로 안 돌린다 — Codex 데스크탑과 같은 까닭이다.
AGY_DESKTOP_HELPER = "agy-desktop-projects.py"


def plant_agy_desktop():
    label = "  프로젝트(agy 데스크탑) — "
    path = os.path.join(os.path.dirname(codex_helper), AGY_DESKTOP_HELPER)   # 도우미는 다 몸통 곁에 실린다
    if not os.path.isfile(path):
        msgs.append("  ! 프로젝트(agy 데스크탑) — 도우미가 몸통 곁에 없다(%s) — 못 더했다" % path)
        return
    spec = importlib.util.spec_from_file_location("agy_desktop_projects", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        states, held = mod.plant_agy_projects(targets)
    except mod.Stop as s:
        msgs.append("  ! 프로젝트(agy 데스크탑) — 못 더했다: %s" % s.line)
        return
    now = sum(1 for _, s in states if s == mod.AP_NOW)
    gone = sum(1 for _, s in states if s == mod.AP_GONE)
    if now:
        msgs.append(label + "%d 개 더했다 (다음에 앱을 열면 보인다)" % now)
    if held == mod.AP_RECORD:   # 저절로 안 풀린다 — 말 수를 줄이는 판(MODE 가 install 이 아님)에서도 알린다
        msgs.append("  ! 프로젝트(agy 데스크탑) — 우리 기록(~/.gemini/config/%s)을 못 읽어 아무것도 안 더했다(사람이 뺀 것을 다시 넣지 않으려고)"
                    % mod.SEEN_FILE)
    if not install:
        return
    if held == mod.AP_RUNNING:
        msgs.append(label + "앱이 떠 있어 미뤘다 — 닫힌 뒤의 다음 설치가 더한다")
    elif held == mod.AP_UNKNOWN:
        msgs.append(label + "앱이 떠 있는지 못 가려 미뤘다 — 다음 설치가 다시 본다")
    elif held == mod.AP_ABSENT:
        msgs.append(label + "agy 설정 폴더(~/.gemini/config)가 없어 건너뛰었다")
    elif held == mod.AP_OFF:
        msgs.append(label + "윈도에서만 더한다 — 건너뛰었다")
    if gone:
        msgs.append(label + "사람이 목록에서 뺀 %d 개는 다시 안 넣었다" % gone)
    if held is None and not (now or gone):
        msgs.append(label + "이미 다 들어 있다 (%d 개)" % len(states))


# VS Code — 몸통 곁의 VS Code 신뢰 도우미(`vscode-trust.py`)가 VS Code 의 신뢰 목록(공유 DB)에 저장소 뿌리마다 한 줄씩 더한다.
#   설정 파일이 아니라 VS Code 의 상태 DB 라, VS Code 가 떠 있으면 안 쓰고 미룬다 — 설치기는 VS Code 를 이 걸음 뒤에 띄운다.
#   사람이 VS Code 에서 신뢰를 뺀 저장소는 다시 안 넣는다.
# 못 걸어도 진 것으로 안 돌린다 — Codex 와 같은 까닭이다. 다시 거는 것은 다음 설치가 든다.
VSCODE_HELPER = "vscode-trust.py"


def plant_vscode():
    label = "  신뢰(VS Code) — "
    path = os.path.join(os.path.dirname(codex_helper), VSCODE_HELPER)   # 두 도우미 다 몸통 곁에 실린다
    if not os.path.isfile(path):
        msgs.append("  ! 신뢰(VS Code) — 도우미가 몸통 곁에 없다(%s) — 못 걸었다" % path)
        return
    spec = importlib.util.spec_from_file_location("vscode_trust", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        states, held = mod.plant_trusted_folders(targets)
    except mod.Stop as s:
        msgs.append("  ! 신뢰(VS Code) — 못 걸었다: %s" % s.line)
        return
    now = sum(1 for _, s in states if s == mod.VT_NOW)
    gone = sum(1 for _, s in states if s == mod.VT_GONE)
    if now:
        msgs.append(label + "%d 자리에 걸었다 (다음 열기부터 안 묻는다)" % now)
    if held == mod.VT_RECORD:   # 저절로 안 풀린다 — 말 수를 줄이는 판(MODE 가 install 이 아님)에서도 알린다
        msgs.append("  ! 신뢰(VS Code) — 우리 기록(~/.vscode-shared/sharedStorage/%s)을 못 읽어 아무것도 안 걸었다(사람이 뺀 것을 다시 넣지 않으려고)"
                    % mod.SEEN_FILE)
    if not install:
        return
    if held == mod.VT_RUNNING:
        msgs.append(label + "VS Code 가 떠 있어 미뤘다 — 다 닫은 뒤의 다음 설치(로그인 자동 실행 · --install)가 건다")
    elif held == mod.VT_UNKNOWN:
        msgs.append(label + "VS Code 가 떠 있는지 못 가려 미뤘다 — 다음 설치가 다시 본다")
    elif held == mod.VT_UNMOVED:
        msgs.append(label + "VS Code 가 앞서 믿은 폴더 목록을 아직 새 자리로 안 옮겨 미뤘다 — VS Code 를 한 번 연 뒤의 다음 설치가 건다")
    elif held == mod.VT_ABSENT:
        msgs.append(label + "VS Code 가 없어 건너뛰었다")
    elif held == mod.VT_OFF:
        msgs.append(label + "윈도에서만 건다 — 건너뛰었다")
    if gone:
        msgs.append(label + "사람이 신뢰를 뺀 %d 자리는 다시 안 넣었다" % gone)
    if held is None and not (now or gone):
        msgs.append(label + "이미 다 걸려 있다 (%d 자리)" % len(states))


if tools is None or CLAUDE in tools:
    plant_claude()
elif install:
    msgs.append("  신뢰(Claude) — Claude 를 안 골라 건너뛰었다")
if tools is not None and CODEX in tools:
    try:
        codex_mod = codex_helper_module()
    except Exception as e:  # 도우미를 못 불러옴 — Claude 쪽 줄까지 잃지 않게 여기서 받는다
        codex_mod = None
        msgs.append("  ! 신뢰(Codex) — 도우미를 못 불렀다: %s: %s" % (type(e).__name__, e))
    else:
        if codex_mod is None:
            msgs.append("  ! 신뢰(Codex) — 도우미가 몸통 곁에 없다(%s) — 못 걸었다" % codex_helper)
    for step, what in ((plant_codex, "  ! 신뢰(Codex) — 못 걸었다"),
                       (plant_codex_desktop, "  ! 프로젝트(Codex 데스크탑) — 못 더했다"),
                       (plant_codex_desktop_mode, "  ! 권한(Codex 데스크탑) — 못 심었다")):
        if codex_mod is None:
            break
        try:
            step(codex_mod)
        except Exception as e:  # 모르는 꼴 — 앞뒤 칸의 줄까지 잃지 않게 칸마다 받는다
            msgs.append("%s: %s: %s" % (what, type(e).__name__, e))
elif install:
    msgs.append("  신뢰(Codex) — %s 건너뛰었다" % ("Codex 를 안 골라" if tools is not None else "고른 제품을 못 읽어(%s)" % pick_why))
for tool, label, obj in ((AGY, "agy", "agy 를"), (COPILOT, "Copilot", "Copilot 을")):
    if tools is not None and tool in tools:
        try:
            plant_listed(label, *listed_files()[tool])
        except Exception as e:  # 모르는 꼴 — 앞 도구의 줄까지 잃지 않게 여기서 받는다
            msgs.append("  ! 신뢰(%s) — 못 걸었다: %s: %s" % (label, type(e).__name__, e))
    elif install:
        msgs.append("  신뢰(%s) — %s 건너뛰었다" % (label, "%s 안 골라" % obj if tools is not None else "고른 제품을 못 읽어(%s)" % pick_why))
if tools is not None and AGY in tools:
    try:
        plant_agy_desktop()
    except Exception as e:  # 도우미를 못 불러옴 · 모르는 꼴 — 앞뒤 칸의 줄까지 잃지 않게 여기서 받는다
        msgs.append("  ! 프로젝트(agy 데스크탑) — 못 더했다: %s: %s" % (type(e).__name__, e))
try:
    plant_vscode()
except Exception as e:  # 도우미를 못 불러옴 · 모르는 꼴 — 앞 도구의 줄까지 잃지 않게 여기서 받는다
    msgs.append("  ! 신뢰(VS Code) — 못 걸었다: %s: %s" % (type(e).__name__, e))

for m in msgs:
    print(m)
sys.exit(3 if failed else 0)
PSSEOF
)"
  _prc=$?
  # 3 은 「돌았는데 다 못 심었다」다 — 까닭은 스크립트가 이미 찍었다. 해석기가 안 뜬 것 · 죽은 것(아래)과 고칠 자리가 달라
  #   한 갈래로 안 섞는다. 어느 쪽이든 표식에 판을 안 적는다.
  if [ "$_prc" -eq 3 ]; then
    PC_WIDE_FAIL=1
    rm -f "$_pse"
    [ -n "$_pss" ] && printf '%s\n' "$_pss"
    return 0
  fi
  if [ "$_prc" -ne 0 ]; then
    PC_WIDE_FAIL=1   # 진 판에 열쇠를 안 적는다 — 다음 판이 PC 전체 일을 다시 돌고, 심기는 다음 설치가 다시 한다
    # 한 문구로 둘을 덮지 않는다 — 해석기가 안 뜬 것과 스크립트가 다 쓰고 나서 죽은 것(인코딩 등)은 고칠 자리가 다르다.
    #   하나로 내면 인코딩으로 죽은 자리를 스토어 껍데기로 오진한다. 진 뒤에만 해석기를 한 번 더 불러 가른다. 죽은 쪽은 홈
    #   훅 · 신뢰가 이미 써졌을 수 있다 — 심겼나는 `--check` 가 잰다.
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

# ── 심겼나 — 판정도 문구도 진단 단계 한 자리가 낸다. 여기는 재기만 한다(낡은 항목의 루트를 줄마다 낸다) ──
#    `--check` 만 정직하게 잴 수 있는 자리다 — 설치 갈래는 재기 전에 심어 버려 늘 초록이 나온다. 그래서 이 값을 쓰는 자는
#    진단 단계이고, 거기서 `--check` 가 이 기계의 홈을 있는 그대로 낸다.
#    가드가 심기와 같은 해석기다 — 못 부르면 「없다」가 아니라 「못 잼」이다(못 잼도 초록으로 읽지 않는다).
#    ⚠ 이름이 아니라 루트로 묻는다 — 심는 쪽은 루트가 박힌 문자열을 완전일치로 거르므로, 재는 쪽이 부분일치면 어느 루트가
#      박혀 있든 초록이다. 저장소를 옮기면 새 항목이 붙고 낡은 항목은 남으므로 갈래가 넷이다. 낡은 것을 지우지는 않는다 —
#      작업 루트를 둘 둔 기계가 정당하고, 사람이 손댄 설정을 말없이 지우는 것은 이 훅의 일이 아니다. 자리를 말하고 간다.
home_hook_planted() {   # 0=이 루트로 심김 · 1=안 심김 · 2=못 잼 · 3=심겼는데 낡은 항목이 남음
  [ -n "$(py_num "$PY_CMD")" ] || return 2
  "$PY_CMD" - "$HOME/.claude/settings.json" "$(home_hook_cmd)" "$(home_hook_shape)" <<'HOOKEOF'
import json, re, sys
path, cmd, shape = sys.argv[1:4]
try:
    cfg = json.load(open(path, encoding="utf-8"))
except (OSError, ValueError):
    raise SystemExit(1)
found, stale = False, []
for e in cfg.get("hooks", {}).get("SessionStart", []):
    for h in e.get("hooks", []):
        c = h.get("command", "")
        ours = re.search(shape, c)
        if c == cmd:
            found = True
        elif ours:
            # 우리 꼴이면 그 루트(꼴의 첫 묶음)를 댄다 — 「파일을 열어 보라」는 말은 안 열린다. 그 사람의 항목은 안 센다
            stale.append(ours.group(1))
for s in stale:
    print(s)
raise SystemExit((3 if stale else 0) if found else 1)
HOOKEOF
}

# ── 세션 셸에 venv 를 배선한다 — 설치의 일이 아니라 매 세션의 일이다. venv 가 없으면 아무것도 안 한다 · 늘 0 ──
#    CLAUDE_ENV_FILE 은 세션마다 새로 오는 값이라, 설치 갈래 안에만 두면 지문이 깨끗한 세션(정상 상태)은 배선 없이 출발해
#    에이전트 셸이 시스템 파이썬을 보고 「의존성이 없다」로 오판한다. 갈래 셋 — 닿는 셸이 서로 다르다:
#      CLAUDE_ENV_FILE    훅으로 불린 세션의 도구 셸 — 훅이 발화할 때만 존재한다
#      /etc/profile.d     로그인 셸 — 사람이 컨테이너에 들어온 자리
#      ~/.local/bin 래퍼  그 밖 전부 — 도구 셸은 PATH 를 하네스가 제 목록으로 덮어 rc 파일의 프리펜드가 안 남고, PATH
#                         1순위인 이 폴더만 통한다. 훅이 발화하지 않거나 저장소를 잘못 잡은 세션에도 스냅샷에 실려 남는
#                         유일한 길이다.
#    ⚠ 래퍼는 심링크가 아니다 — venv 파이썬을 링크로 부르면 argv0 곁에서 pyvenv.cfg 를 못 찾아 맨 해석기(패키지 없는 판)로
#      선다. exec 가 실경로를 넘겨야 venv 로 선다.

wire_python_path() {
  [ -x "$VENV_BIN/python" ] || [ -x "$VENV_BIN/python.exe" ] || return 0
  [ -n "${CLAUDE_ENV_FILE:-}" ] &&
    echo "export PATH=\"$VENV_BIN:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  if [ "$OS" = linux ]; then
    [ -w /etc/profile.d ] 2>/dev/null &&
      printf 'export PATH="%s:$PATH"\n' "$VENV_BIN" > "/etc/profile.d/${PROJECT_NAME}-venv.sh"
    # 리눅스는 이 함대에서 리모트 컨테이너 계열뿐이라 PC 파이썬을 덮을 일이 없다
    mkdir -p "$HOME/.local/bin" 2>/dev/null || return 0
    # ⚠ 자리를 갈아 끼운다 — 그 자리로 써 넣지 않는다. 그 이름이 uv 의 링크면(「세션의 python3」 칸의 `--default` 가
    #   세운다) `>` 는 링크를 따라가 uv 의 해석기 실물을 감싸개로 덮는다. 그 실물로 선 venv 가 감싸개를 다시 부르니
    #   python3 가 저를 끝없이 exec 한다. 곁에 쓰고 옮기면 링크 자리만 감싸개로 바뀐다.
    for _wn in python python3; do
      _wt="$HOME/.local/bin/.$_wn.wire.$$"
      if printf '#!/bin/sh\nexec "%s/python" "$@"\n' "$VENV_BIN" > "$_wt" 2>/dev/null &&
         chmod +x "$_wt" 2>/dev/null && mv -f "$_wt" "$HOME/.local/bin/$_wn" 2>/dev/null; then :
      else rm -f "$_wt" 2>/dev/null; fi
    done
  fi
  return 0
}

# ── 전역 축 — claude-config 가 붙어 있나. 판정도 문구도 여기 한 자리다 ──
#    지문이 맞는 세션은 설치를 통째로 건너뛰고 침묵 갈래는 진단 단계 앞에서 나가므로, 설치 걸음이나 진단에만 두면 조용히
#    도는 세션이 경고를 못 받는다. 그래서 따로 세우고 세 자리(세션의 침묵 갈래 · 배경 설치를 띄운 갈래 · 진단)가 낸다.
#    판정은 「내가 깔았나」가 아니라 홈이 지금 무엇을 들고 있나로 낸다 — 리모트 홈은 이미지에 구워져 오므로 못 닿는 세션도
#    규율은 들고 있다. 없는 것이 아니라 낡는 것이 위험이다.
global_rule_reason() {   # 낸다: 못 닿으면 까닭 한 줄, 닿으면 빈 문자열
  [ -n "$CONFIG_ROOT" ] && return 0
  if [ -f "$HOME/.claude/CLAUDE.md" ]; then
    echo "claude-config 를 못 찾아 홈에 있는 것을 못 갱신한다 — 언제 판인지 모른다. add_repo 로 함께 붙인다"
  else
    echo "claude-config 를 못 찾았고 홈에도 없다 — 전역 규범·영역 룰·세션 기록·문서 표준 스킬·사내 환경 문서·씨앗에 못 닿는다. add_repo 로 함께 붙인다"
  fi
}

# ── git 이 진 까닭 한 줄 — 삼키지 않는다 ──
#    진본은 여기 한 자리고, 배경 일의 실패 알림(`bg_fail_report` — 당김 · main 맞추기)과 설치 걸음의 「로컬 main」 칸이 같이 쓴다.
#    끝줄이 아니라 첫 `fatal:`/`error:` 줄이다 — 로컬 작업 트리 갈래는 끝줄이 `Aborting` 이라, 끝줄을 집으면 사유가 있는데
#    층이 안 갈린다. 층이 갈리는 것이 요점이다 — 아래가 여기서 나뉘고, 손대는 자리가 서로 다르다:
#     `could not read Username`  자격증명 — GCM 이 사람을 부르려는데 훅엔 부를 사람이 없다
#     `unable to access …`       망·게이트
#     `Your local changes …`     로컬 수정 · 줄끝(`core.autocrlf`)
#     `Not possible to fast-forward`  로컬이 원격과 갈라졌다
#     `! [rejected] … (non-fast-forward)`  fetch 가 로컬 갈래를 못 옮겼다 — 갈라졌다
#    `fatal:`/`error:` 줄이 없으면 끝줄이 아니라 첫 거절 줄(`! [rejected]`)이다 — fetch 의 거절은 갱신 표의 한 줄로 나오고,
#    그 뒤에 `* [new tag] …` 같은 줄이 붙을 수 있어 끝줄은 사유가 아니다.
git_why() {   # git_why <붙잡은 stderr> — 층이 갈리는 한 줄
  _w="$({ printf '%s\n' "$1" | grep -m1 -E '^(fatal|error):' ||
          printf '%s\n' "$1" | grep -m1 -E '^[[:space:]]*! \[rejected\]' ||
          printf '%s\n' "$1" | grep -v '^[[:space:]]*$' | tail -1; } 2>/dev/null | cut -c1-160)"
  printf '%s' "${_w:-사유가 안 나왔다}"
}

# ── 방금 당겨 봤나 — 한 세션에 같은 저장소를 여러 번 당기지 않는다 ──
#    한 세션에 이 훅이 두 번 불릴 수 있다(저장소 설정이 거는 것과 홈 훅이 거는 것) — 둘 다 제 저장소를 당기면 같은 당김이
#    두 번이다. 프로세스가 갈려 있어 메모리로는 못 가르고 표식 파일이 유일한 자리다.
#    성공 · 실패를 안 가리고 찍는다 — 비싼 쪽이 실패 갈래라 실패만 다시 도는 판이면 걷는 뜻이 없다. 당김 자체가 아니라
#    시도를 적는 것이라 이름도 그렇게 둔다.
#    ⚠ 표식은 `.git` 안에 둔다 — 작업 트리를 더럽히면 그 더러움이 다음 세션의 당김을 막아, 이 함수가 줄이려는 실패를 이
#      함수가 만든다.
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

# ── 배경 일의 실패를 다음 세션이 말한다 — 배경으로 뺀 당김(`pull_ff`)과 main 맞추기(`sync_main_bg`)가 같이 쓴다 ──
#    로그가 차 있으면 원문을 옆에 두고 경고 한 줄을 낸다 — 부른 쪽이 곧 로그를 비우므로, 안 두면 사람이 한 줄을 한 번 읽고
#    나면 사유의 원문이 사라진다(`git_why` 의 160자는 화면의 값이고 원문은 파일의 값이다). 다음 성공이 그 파일을 걷는다:
#    성공하면 로그가 비어 else 로 오고, 그때가 곧 「이제 안 진다」이다.
bg_fail_report() {  # bg_fail_report <저장소> <로그> <원문 보관> <무엇이 졌나>
  if [ -s "$2" ]; then
    cp "$2" "$3" 2>/dev/null || true
    echo "$(basename "$1"): ⚠ $4 — $(git_why "$(cat "$2")") · 원문 $3"
  else
    rm -f "$3" 2>/dev/null || true
  fi
}

# ── 로컬 main 을 원격에 맞춘다 — main 이 아닌 갈래 위에서만. main 위라면 당김(`pull_ff`) 몫이다 ──
#    `origin/main` 과 로컬 main 은 마지막 fetch 때의 사진이다 — 원격이 그 뒤에 움직이면 사진이 낡고, 낡은 사진을 지금으로
#    읽으면 「main 이 뒤처졌다」 같은 거짓 판정이 선다. 작업 나무는 안 건드린다 — 참조 둘(추적 갈래 · 로컬 main)만 옮긴다.
#    부르는 자리는 둘이다 — 설치 걸음의 「로컬 main」 칸(기다린다) · 리눅스 auto(배경, `sync_main_bg`).
#    ⚠ 빨리감기만 한다 — 로컬 main 에 밀지 않은 커밋이 있으면 git 이 `non-fast-forward` 로 거절하고 그 사유가 실패로 남는다.
#      억지로 옮기면(`branch -f`) 그 커밋이 경고 없이 main 에서 떨어진다.
#    ⚠ refspec 을 두 칸 다 적는다 — 한 갈래만 받게 클론된 저장소는 `fetch <원격> main` 이 추적 갈래를 안 옮기고 FETCH_HEAD 만
#      써서, 사진이 그대로인데 성공으로 끝난다.
#    원격 이름을 안 박는다 — 당김과 같이 추적 설정에서 읽는다. 없으면 맞출 자리가 없어 조용히 물러난다.
#    얕게 받은 저장소는 거절을 한 번 더 따진다 — 리모트 하네스는 얕게(깊이 50) 받아, 원격이 그 창을 넘게 앞서면 로컬 main 과
#    추적 갈래의 창이 안 겹쳐 갈라지지 않았는데도 git 이 빨리감기를 증명하지 못해 거절한다. 그래서 지면 로컬 main 의 커밋
#    시각(epoch · 같은 초의 커밋도 든다) 이후까지만 깊이를 늘려 한 번 더 한다 — 그래도 지면 정말 갈라진 것이라 그 사유를
#    낸다. 받는 양은 로컬 main 이 뒤처진 만큼으로 끝난다.
_fetch_main() {  # _fetch_main <저장소> <원격> — 추적 갈래(강제)와 로컬 main(빨리감기만)을 옮긴다. 출력은 부른 쪽이 붙잡는다
  git -C "$1" fetch "$2" "+refs/heads/main:refs/remotes/$2/main" "refs/heads/main:refs/heads/main" 2>&1
}

sync_main() {  # sync_main <저장소> — 0=맞췄거나 맞출 것이 없다 · 1=졌다(사유는 stdout)
  git -C "$1" rev-parse --git-dir >/dev/null 2>&1 || return 0
  git -C "$1" show-ref --verify --quiet refs/heads/main || return 0
  [ "$(git -C "$1" symbolic-ref --short -q HEAD 2>/dev/null)" != main ] || return 0
  _sr="$(git -C "$1" config --get branch.main.remote 2>/dev/null)" || true
  [ -n "$_sr" ] || return 0
  # ⚠ `-q` 를 안 준다 — 주면 거절 줄(`! [rejected] … (non-fast-forward)`)까지 숨어 사유 없이 진다. 대신 출력을
  #   붙잡아 두고 질 때만 낸다 — 성공 출력이 로그에 남으면 다음 세션이 그것을 실패로 읽는다.
  _so="$(_fetch_main "$1" "$_sr")" && return 0
  if [ "$(git -C "$1" rev-parse --is-shallow-repository 2>/dev/null)" = true ]; then
    _since="$(git -C "$1" log -1 --format=%ct main 2>/dev/null)"
    if [ -n "$_since" ]; then
      _so="$(git -C "$1" fetch "$_sr" --shallow-since="$_since" main 2>&1)" &&
        _so="$(_fetch_main "$1" "$_sr")" && return 0
    fi
  fi
  printf '%s\n' "$_so"; return 1
}

# 리눅스 auto 에서 붙은 저장소마다 배경으로 맞춘다(리눅스는 이 함대에서 리모트 컨테이너뿐이다) · 늘 0.
#   머신이 처음 뜰 때는 설치 걸음의 「로컬 main」 칸이 맞추지만, 같은 머신에서 훅이 다시 돌면(대화 압축 · `/clear` — 대화마다
#   머신은 따로 뜬다) 훅이 auto 로만 돌고 auto 의 당김은 main 체크아웃에서만 움직인다 — 리모트 세션은 대개 `claude/*` 갈래
#   위라서 로컬 main 이 머신이 뜬 순간의 사진으로 남는다.
#   기다리지 않는다 — 세션 시작 시간을 안 늘린다. 그래서 이번 대화의 첫 판정에는 늦을 수 있다(원격을 판정하기 전에 fetch
#   하는 것은 규범 몫이다). 붙은 저장소를 다 돈다 — 리모트는 설정 저장소 훅 하나가 대표로 돌아 형제는 제 훅이 안 선다.
#   진 사유는 `.git/claude-main-sync.log` 에 남고, 다음 세션이 한 줄로 말한다.
# ⚠ main 위면 표식(`pull_due`)을 찍기 전에 물러난다 — 찍으면 같은 저장소의 당김이 「방금 해 봤다」로 막힌다.
sync_main_bg() {  # sync_main_bg <저장소>
  [ "$(git -C "$1" symbolic-ref --short -q HEAD 2>/dev/null)" != main ] || return 0
  _gd="$(git -C "$1" rev-parse --absolute-git-dir 2>/dev/null)" || return 0
  _lg="$_gd/claude-main-sync.log"
  bg_fail_report "$1" "$_lg" "$_gd/claude-main-sync.last-fail" "지난 세션에 로컬 main 을 원격에 못 맞췄다"
  pull_due "$1" || return 0
  : > "$_lg" 2>/dev/null || true
  ( sync_main "$1" >"$_lg" 2>&1 </dev/null & )
}

# 당김이 어디서 멈출지 저장소에 묻는다 — 저장소가 둔 손(`.claude/hooks/pull-target.sh`)이 있을 때. 늘 0.
#   몸통은 어느 커밋이 좋은지 모른다 — 기전만 여기 살고 정책은 저장소가 든다(`run_repo_start` 와 같은 갈림).
#   부르는 자리는 셋이다 — 세션 당김(`pull_ff`) · 당김 문 갈래(`--pull-target` — PowerShell 의 당김이 부른다) · 맨바닥 설치의
#   형제 받기(`gate_fresh_clone`). 같은 원격을 받는 자리가 다 이 한 자를 지나야 같은 커밋에서 선다.
#   받는 것 — 저장소 · 추적 원격 이름 · `.git` 자리. fetch 가 이긴 뒤에 부른다. 내는 것 — 판정에 적은 병합할 커밋의 sha 한 줄
#   (받은 커밋, 아니면 원격 끝) — 원격 끝을 못 읽었으면 `<원격>/main` 이름을 그대로 내 병합이 git 의 사유로 진다.
#   부작용 — 판정 한 줄(`<까닭> <병합할 커밋> — <원격>/main <그 커밋> · 덧말`)을 `.git/claude-pull-target.last`
#   에 덮어 쓴다. 까닭은 no-script · no-opinion · accepted · rejected 넷이다.
#   손과의 약속 — `sh pull-target.sh <원격>/main` · 자리는 저장소 뿌리 · stdin 은 비었다. 0 으로 끝나며 온전한 커밋 sha 한 줄을
#   내면 「거기까지」, 빈 출력이나 0 이 아닌 끝은 「의견 없음」이다. 받는 것은 그 sha 가 이 저장소의 커밋이고 `<원격>/main` 의
#   조상(같아도 된다)일 때뿐이다 — 의견이 없거나 답을 못 받으면 원격 끝을 병합한다. 손이 지거나 틀려도 당김은 그대로 선다.
#   손의 stderr 는 당김 로그로 흐른다 — 말이 있으면 다음 세션이 실패로 말한다.
# ⚠ 판정은 당김 로그에 안 쓴다 — 그 로그는 「비면 성공」이라(`bg_fail_report`) 판정 한 줄이 들면 성공한 당김이 실패로 읽힌다.
#   답을 재는 git 의 stderr 도 같은 까닭으로 버린다.
# ⚠ 꼴(16진 40 · 64자)부터 본다 — 답은 git 의 인자로 들어가, 이름(`HEAD` · 갈래)이나 `-` 로 시작하는 답이 거기 닿으면 엉뚱한
#   자리나 옵션으로 읽힌다. 끝의 CR 하나는 걷는다 — 윈도우에서 난 도구는 줄을 CRLF 로 끝내고 `$(…)` 는 LF 만 걷는다.
_pull_target() {  # _pull_target <저장소> <원격> <.git 자리>
  _ptip="$2/main"; _ptw="$_ptip"; _ptn=""
  _pts="$1/.claude/hooks/pull-target.sh"
  if [ ! -f "$_pts" ]; then
    _ptk=no-script
  else
    _pta="$(cd "$1" && sh "$_pts" "$_ptip" </dev/null)"; _ptx=$?
    _pta="${_pta%"$(printf '\r')"}"
    if [ "$_ptx" -ne 0 ] || [ -z "$_pta" ]; then
      _ptk=no-opinion; _ptn="손의 끝 값 $_ptx"
    else
      _ptk=rejected; _ptn="답 '$(printf '%s\n' "$_pta" | head -n 1 | cut -c1-80)'"
      case "$_pta" in
        *[!0-9a-f]*) _ptn="$_ptn — sha 꼴이 아니다" ;;
        *) if [ "${#_pta}" -ne 40 ] && [ "${#_pta}" -ne 64 ]; then
             _ptn="$_ptn — sha 꼴이 아니다"
           elif [ "$(git -C "$1" rev-parse -q --verify "$_pta^{commit}" 2>/dev/null)" != "$_pta" ]; then
             _ptn="$_ptn — 이 저장소의 커밋이 아니다"
           elif ! git -C "$1" merge-base --is-ancestor "$_pta" "$_ptip" 2>/dev/null; then
             _ptn="$_ptn — $_ptip 위에 없다"
           else
             _ptk=accepted; _ptw="$_pta"; _ptn=""
           fi ;;
      esac
    fi
  fi
  _ptt="$(git -C "$1" rev-parse -q --verify "$_ptip^{commit}" 2>/dev/null)" || _ptt="?"
  if [ "$_ptk" = accepted ]; then _ptm="$_ptw"; else _ptm="$_ptt"; fi
  printf '%s %s — %s %s%s\n' "$_ptk" "$_ptm" "$_ptip" "$_ptt" "${_ptn:+ · $_ptn}" 2>/dev/null >"$3/claude-pull-target.last" || true
  if [ "$_ptm" = "?" ]; then printf '%s\n' "$_ptw"; else printf '%s\n' "$_ptm"; fi
}

# 갓 받은 나무를 당김 문의 답에 세운다 — 맨바닥 설치가 형제를 막 clone 한 뒤. 늘 0.
#   clone 은 원격 끝을 받고, 그 뒤의 당김은 빨리감기만이라 뒤로 못 간다 — 끝이 빨갛고 손이 그 앞의 초록을 골라도 나무는
#   빨간 끝에 남는다. 그래서 이 자리도 세션 · 부팅 · 배포의 당김과 같은 자(`_pull_target`)에 묻는다.
#   받는 것 — 저장소. 내는 것 — 옮겼거나 못 옮겼을 때 한 줄(설치기 기록에 든다). 부작용 — 판정 한 줄(`_pull_target`) · main 의 자리.
#   옮기는 것은 갓 받은 꼴일 때뿐이다 — main 체크아웃이고 HEAD 가 원격 끝과 같다. `reset --keep` 이라 편집이 끼어 있으면 git 이
#   거절하고 나무는 원격 끝에 남는다.
gate_fresh_clone() {  # gate_fresh_clone <저장소>
  [ "$(git -C "$1" symbolic-ref --short -q HEAD 2>/dev/null)" = main ] || return 0
  _gfg="$(git -C "$1" rev-parse --absolute-git-dir 2>/dev/null)" || return 0
  _gfr="$(git -C "$1" config --get branch.main.remote 2>/dev/null)" || return 0
  _gfh="$(git -C "$1" rev-parse -q --verify HEAD 2>/dev/null)" || return 0
  [ "$_gfh" = "$(git -C "$1" rev-parse -q --verify "$_gfr/main^{commit}" 2>/dev/null)" ] || return 0
  _gft="$(_pull_target "$1" "$_gfr" "$_gfg")"
  [ "$_gft" != "$_gfh" ] || return 0
  if git -C "$1" reset -q --keep "$_gft" >/dev/null 2>&1; then
    printf '%s: %s — 당김 문이 원격 끝 %.7s 앞 %.7s 에 세웠다\n' "$PROJECT_NAME" "$(basename "$1")" "$_gfh" "$_gft"
  else
    printf '%s: ⚠ %s — 당김 문의 답 %.7s 로 못 옮겨 원격 끝 %.7s 에 둔다\n' "$PROJECT_NAME" "$(basename "$1")" "$_gft" "$_gfh"
  fi
  return 0
}

# 원격을 당긴다 — main 체크아웃일 때만 · 빨리감기로만 · 배경에서. 늘 0.
#   어디까지 — 원격 main 의 끝이다. 저장소가 손을 두면 그 손이 고른 그 위의 커밋이다(`_pull_target`). 빨리감기만이라 이미 그
#   커밋을 지난 나무는 그 자리에 선다.
#   타임아웃은 안 씌운다 — 왕복이 원래 느린 자리(당김 하나가 몇 초인 망)가 있어 느린 것과 막힌 것이 시간으로는 안 갈린다.
#   자르면 되던 당김까지 실패로 찍혀, 진단을 세우려다 없던 고장을 만든다 — 가르는 것은 사유다.
#   기다리지도 않는다 — 배경으로 띄우고 결과는 다음 세션이 본다. 세션 시작에 당김이 둘 서는데 확장은 초기화를 60초만
#   기다린다. 당긴 것이 이 세션에 안 보이는 값을 치른다 — 규범 · 선언이 바뀐 커밋은 다음 세션부터 선다. 진 사유는
#   `.git/claude-pull.log` 에 남고 다음 세션이 그것을 말한다 — 성공은 빈 파일이라 조용하다.
# ⚠ stdout · stderr · stdin 을 다 뗀다 — 하나라도 훅의 파이프를 물고 있으면 Claude Code 가 그 자식이 끝날 때까지 훅을
#   기다려 배경으로 뺀 뜻이 없어진다.
pull_ff() {  # pull_ff <저장소> — main 체크아웃일 때만, 빨리감기로만, 배경에서
  [ -e "$1/.git" ] || return 0
  [ "$(git -C "$1" symbolic-ref --short -q HEAD 2>/dev/null)" = main ] || return 0
  _gd="$(git -C "$1" rev-parse --absolute-git-dir 2>/dev/null)" || return 0
  _lg="$_gd/claude-pull.log"
  # 원문 보관과 경고는 `bg_fail_report` 한 자리다 — main 맞추기도 같은 것을 쓴다.
  bg_fail_report "$1" "$_lg" "$_gd/claude-pull.last-fail" "지난 세션의 원격 당김이 졌다"
  # 지난 당김이 저장소 손의 답을 물리쳤으면 한 줄 말한다 — 물리친 당김은 문이 꺼진 채 원격 끝까지 간 것이라, 판정 파일에만
  #   두면 손이 틀린 줄을 아무도 모른다. 판정은 저장소에 한 장이라 어느 당김(세션 · `--pull-target`)이 적었든 여기서 읽힌다.
  #   덧말(첫 ` · ` 뒤)이 답과 물리친 까닭이다.
  _ptl=""; [ -f "$_gd/claude-pull-target.last" ] && IFS= read -r _ptl < "$_gd/claude-pull-target.last"
  case "$_ptl" in
    rejected\ *) echo "$(basename "$1"): ⚠ 지난 당김이 저장소 손(.claude/hooks/pull-target.sh)의 답을 물리치고 원격 끝까지 갔다 — ${_ptl#* · } · 판정 $_gd/claude-pull-target.last" ;;
  esac
  pull_due "$1" || return 0
  : > "$_lg" 2>/dev/null || true
  # ⚠ `pull` 이 아니라 `fetch` + `merge` 다. `pull` 은 제 fetch 뒤 `FETCH_HEAD` 를 읽어 무엇을 병합할지 정하는데, 그 파일은
  #   저장소당 한 장이라 다른 git 이 같은 순간에 끼어들면 갈래가 두 줄 적히고 pull 이 그것을 병합 대상 둘로 읽어
  #   `fatal: Cannot fast-forward to multiple branches.` 로 진다. `merge` 에 이름 있는 자리(추적 갈래)를 주면 남이 그
  #   파일에 무엇을 쓰든 무관해진다.
  # 원격 이름을 안 박는다 — 추적 설정에서 읽는다. 못 읽으면 당길 자리가 없다는 뜻이라 조용히 물러난다.
  # fetch · 멈출 자리 고르기 · merge 를 `&&` 로 한 덩이에 둔다 — 어느 쪽이 져도 로그에 남아야 「로그가 비면 성공」이 선다.
  #   고르기는 fetch 뒤라야 한다 — 손과 몸통이 이번에 받은 `<원격>/main` 을 같이 본다.
  _rm="$(git -C "$1" config --get branch.main.remote 2>/dev/null)" || true
  [ -n "$_rm" ] || return 0
  ( { git -C "$1" fetch -q "$_rm" main &&
      _to="$(_pull_target "$1" "$_rm" "$_gd")" &&
      git -C "$1" merge --ff-only -q "$_to"; } >"$_lg" 2>&1 </dev/null & )
}

# 저장소가 제 세션 시작 일을 두는 자리(`.claude/hooks/repo-start.sh`) — 있으면 부르고 없으면 조용하다. 늘 0.
#   몸통은 무엇을 할지 모른다 — 기전만 여기 살고 정책은 저장소가 든다. 목록을 안 들므로 쓰는 저장소가 늘어도 안 낡는다.
#   자리가 여기인 까닭 — `.claude/settings.json` 은 배포가 통째로 덮는 파일이라(`deploy.repofiles.conf`), 저장소 제 훅을
#   거기 등록하면 다음 배포가 지운다. claude-config 를 안 붙인 세션은 그 파일이 관리 대상인 줄 알 길이 없다.
#   진다고 세션을 안 죽인다 — 저장소 제 일이라 사유만 내고 간다(`set -e` 가 없어도 `||` 로 명시해 둔다). 그 말은 stdout
#   이다 — 세션이 읽어야 손이 진 줄을 안다(머리말 「말은 stdout 으로」). 타임아웃은 안 씌운다(당김과 같은 결) — 오래 끄는
#   손은 세션 시작을 그만큼 늦추므로 막는 것은 저장소 몫이다.
#   auto 에만 선다 — 이 자리의 뜻이 「당김이 설 수 있는 꼴로 만든다」라 당김이 없는 갈래에는 지킬 것이 없다.
run_repo_start() {
  _rs="$PROJECT_DIR/.claude/hooks/repo-start.sh"
  [ -f "$_rs" ] || return 0
  sh "$_rs" || echo "$PROJECT_NAME: ⚠ 저장소 제 시작 일(.claude/hooks/repo-start.sh)이 졌다 — 저장소 제 일이라 넘어간다"
}

# ── 설치 걸음 — 설치 단계가 기다려 부르고, 세션(auto)은 `install_bg` 가 배경으로 부른다 ──
#    읽는 값 ASKED · DO_GLOBAL · DO_REPO · UPGRADE(세션 단계가 정한다). 내는 것 — 칸마다 한 줄과 초 · 실패 기록(FAILS ·
#    GFAILS) · 지문 도장(STAMP · GSTAMP) · 전역형 도구의 ✅ · ❌ 줄. 끝 — PC 에서 밖이 부른 `--install` 은 deploy 의 끝
#    값으로, 전역만 돈 갈래는 여기서 끝나고(안 서는 전역형 도구가 있으면 1), 저장소 갈래는 돌아와 진단 단계로 간다.
#    칸 차례 — 갈래 → 바깥 `--install` 이면 deploy.ps1 에 넘김 → 커밋 훅 배선 · 홈 밀기 → 파이썬 축 → 노드 축 → 전역형
#    도구 → 세션의 python3 → 저장소 배선 → 로컬 main → 선언 지문 굳히기.
install_step() {

  # ── 갈래 둘 — 전역은 기계에 한 번, 저장소는 배선만 ────────────────────
  #    auto 는 세션 단계의 지문 게이트가 이미 정했다. 인자로 온 자리는 여기서 정한다:
  #      --install-global                    전역만          ← deploy.ps1 이 고리 앞에 한 번
  #      --install + CLAUDE_CONFIG_DEPLOYING 저장소만        ← deploy.ps1 이 고리 안에서
  #      --install (그 표식 없이)            전역 + 저장소   ← 리모트 Setup script
  #    리모트를 안 가른다 — 거기는 `deploy.ps1` 이 없어 `--install` 하나가 전부라, 가르면 전역형 도구를 아무도 안 깐다.
  #    표식이 곧 「위에서 갈라 부르고 있다」는 뜻이다.
  case "$ASKED" in
    install-global) DO_GLOBAL=1; DO_REPO="" ;;
    install)        DO_REPO=1
                    if [ -n "${CLAUDE_CONFIG_DEPLOYING:-}" ]; then DO_GLOBAL=""; else DO_GLOBAL=1; fi ;;
    *)              DO_GLOBAL="${DO_GLOBAL:-}"; DO_REPO="${DO_REPO:-}" ;;
  esac

  # ── PC 에서 밖(설치기 · 사람)이 `--install` 로 불렀으면 — 개인 칸을 세우고 `deploy.ps1` 에 넘긴다 ──
  # ⚠ 고리를 끊는 표식이 있다 — `deploy.ps1` 은 이 훅을 저장소마다 `--install` 로 부르는 자리라, 여기서 다시 그것을
  #   부르면 고리다. 그 표식(`CLAUDE_CONFIG_DEPLOYING`)은 deploy.ps1 이 세운다 — 있으면 저장소 하나의 설치로 간다. 명시된
  #   `--install` 만 탄다: 세션(auto)이 지문 어긋남으로 여기 온 판에서 배포 전체를 돌리면 세션이 그만큼 멎는다. 리모트는
  #   deploy.ps1 이 없어 이 갈래를 안 탄다.
  # 종료코드는 deploy 의 것이다 — 안 재고 0 으로 끝나면 deploy 가 죽어도 「완료」가 된다(부재가 통과로 읽히는 그 자리).
  #   deploy 가 0 인데 아래 심기가 졌으면 1 이다 — 고리 안의 저장소 훅은 심기를 이 갈래에 맡기고 안 심겼다를 안 센다.
  if [ "$ASKED" = install ] && [ "$OS" = windows ] && [ -z "${CLAUDE_CONFIG_DEPLOYING:-}" ] &&
     [ -n "$CONFIG_ROOT" ] && [ -f "$CONFIG_ROOT/deploy.ps1" ]; then
    # 열쇠는 deploy 앞에서 읽는다 — deploy 가 민 것이 그 판이다. deploy 가 도는 사이 판이 움직였으면
    #   `pc_wide_mark` 가 열쇠를 안 적는다.
    pc_wide_key; PC_WIDE_FAIL=""
    deploy_personal install
    echo "$PROJECT_NAME: deploy.ps1 에 넘긴다 — 저장소·메모리를 밀고 각 저장소 훅을 --install 로 부른다"
    # PC 전체 일은 이 갈래가 쥔다 — 표식을 그 부름 하나에만 실어, 고리 안의 저장소 훅이 그 일을 또 안 하게 한다(준비 단계의 PC_WIDE)
    CLAUDE_CONFIG_PC_WIDE_HELD=1 \
      powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$CONFIG_ROOT/deploy.ps1")" -Yes
    _drc=$?
    # 홈 훅 · 신뢰를 여기서 심고 PC 전체 일의 표식을 남긴다 — deploy.ps1 은 할 일이 없는 평소 상태면 저장소 훅을 안
    #   부르므로(`--needs-install` 이 0), 이 입구(로그인 자동 실행이 매번 지나는 자리)가 안 남기면 표식이 안 서고 형제
    #   세션이 멀쩡한 PC 를 「자동 실행이 안 돈다」고 말한다. 표식은 deploy 가 성공했을 때만 — 진 판에 찍으면 「맞췄다」가
    #   거짓이 된다.
    plant_session_state
    if [ "$_drc" -eq 0 ]; then
      pc_wide_mark
      if [ -n "$PC_WIDE_FAIL" ]; then
        echo "$PROJECT_NAME: ⚠ deploy.ps1 은 성공했는데 홈 훅 · 신뢰를 다 못 심었다 — 위 줄이 곧 고칠 자리"
        exit 1
      fi
    else
      echo "$PROJECT_NAME: ⚠ deploy.ps1 이 exit $_drc 로 끝났다 — 위 진단의 ❌ 줄이 곧 고칠 자리"
    fi
    exit "$_drc"
  fi

  # 실패는 삼키되 까닭까지 버리지는 않는다 — 진단이 ❌ 줄에 사유를 이어 붙인다. 지난 실패는 지우기 전에 찍는다 — 안
  #   그러면 「무엇이 왜 실패했었나」가 성공한 재설치와 함께 사라져 다시 못 잰다.
  # 이번에 안 도는 층의 기록은 안 지운다 — 저장소 갈래가 전역 기록을 비우면 전역형 도구가 못 깔린 사유가 깔아 보지도
  #   않은 채 사라진다. 지우는 자와 채우는 자를 층마다 맞춘다.
  for _ff in ${DO_REPO:+"$FAILS"} ${DO_GLOBAL:+"$GFAILS"}; do
    if [ -s "$_ff" ]; then
      echo "$PROJECT_NAME: 지난 설치 실패 — 이번에 다시 깐다:"
      awk -F'\t' '{printf "  · %s — %s\n", $1, $2}' "$_ff" 2>/dev/null
    fi
    mkdir -p "$(dirname "$_ff")" 2>/dev/null; : > "$_ff" 2>/dev/null
  done
  try() {   # try <이름> <명령…> — 안 죽고, 실패하면 출력 한 줄을 사유로 남긴다
    # 스택 프레임은 사유가 아니다 — 끝줄을 그대로 집으면 node 계열이 뱉는 `    at ChildProcess…` 한 줄만 남아 기록이
    #   있는데 원인이 없다. 프레임을 걷고 남은 끝줄을 집되, 전부 프레임이면 그때는 끝줄이라도 남긴다(빈 사유보다 낫다).
    _n="$1"; shift
    _o="$(mktemp)"; _r=0
    "$@" >"$_o" 2>&1 || { _r=$?
      _lines="$(grep -v '^[[:space:]]*$' "$_o" 2>/dev/null)"
      _msg="$(printf '%s\n' "$_lines" | grep -v '^[[:space:]]*at [^[:space:]]' | tail -1)"
      [ -n "$_msg" ] || _msg="$(printf '%s\n' "$_lines" | tail -1)"
      printf '%s\t%s\n' "$_n" "$(printf '%s' "$_msg" | cut -c1-160)" >> "$FAILS" 2>/dev/null; }
    # 마지막 출력 줄(`TRY_LAST`)은 부르는 쪽이 판정으로 쓴다 — 뒷길이 「받았다」인지 「이미 있다」인지는 이 줄에만
    # 있고, 삼키면 초만 남아 헛받기가 안 보인다. 설치 갈래에서만 도는 자리라 `tail` 하나는 싸다.
    TRY_LAST="$(tail -1 "$_o" 2>/dev/null)"
    rm -f "$_o"
    return "$_r"
  }
  # ── nogo <이름> <사유> — 「전제가 안 맞아 설치 갈래를 못 탔다」를 `try` 와 같은 형식으로 적고 1 을 낸다 ──
  #    `try` 의 형제다: 저쪽은 돌려 보고 진 사유를, 이쪽은 돌려 보지도 못한 사유를 남긴다. 전제 가드는 `try` 앞에서
  #    빠져나가므로, 여기서 안 적으면 진단이 「안 닿는다」만 내고 무엇을 갖추면 닿는지는 아무 데도 없다 — 사유 없는 ❌ 는
  #    다음 사람에게 부재와 같다.
  nogo() {
    printf '%s\t%s\n' "$1" "$2" >> "$FAILS" 2>/dev/null
    return 1
  }

  # ── 커밋 훅 배선 · 홈 밀기 — 가볍고 안 죽는 것이 맨 앞이고, 그 안에서도 안 죽는 쪽이 더 앞이다 ──
  #    배선은 로컬 한 줄이라 뒤따르는 복사가 무엇으로 지든 살아남는다. 몸통은 `wire_commit_hooks` · `deploy_home_norms` 각 한
  #    벌이다 — PC 매 세션 갈래(auto)와 같은 것을 같은 차례로 민다.
  #    배선은 저장소 몫이라 `DO_REPO` 아래 선다 — `--install-global` 은 저장소를 안 든다(같은 배포 안에서 `deploy.ps1` 의
  #    저장소 고리가 저장소마다 이것을 이미 민다).
  if [ -n "$DO_REPO" ]; then
    wire_commit_hooks
  fi
  # PC 전체 일은 맡는 실행만 한다 — 형제 저장소 세션이 도구 선언 어긋남으로 여기 온 판은 저장소 몫만 깐다. 명시한
  #   `--install` 은 어디서 불려도 맡고, 바깥 `--install` 이 부른 deploy.ps1 의 고리 안만 안 맡는다(준비 단계의 PC_WIDE).
  if [ -n "$DO_REPO" ] && [ -n "$PC_WIDE" ]; then
    # 설치 갈래는 열쇠를 안 믿고 다 한다 — 다 한 뒤 그 판을 적는다
    pc_wide_key; PC_WIDE_FAIL=""
    deploy_home_norms
    deploy_personal auto  # 가벼운 것만 — 무거운 것(clone · 홈 설정 덮기)은 위 PC 분기가 이미 들었다

    # ── 홈 훅 · 신뢰 심기 — 몸통은 `plant_session_state` 한 벌이다 ──
    #    명시한 `--install` 로 들어온 갈래(사람이 바로 돌린 deploy.ps1 의 저장소마다 · 리눅스 설정 스크립트)만 심는다. 세션
    #    (auto)이 지문 어긋남으로 이 갈래에 온 판은 `ASKED` 가 비어 안 심는다 — 심기는 세션의 일이 아니다(plant_session_state
    #    머리말). 멱등이라 겹쳐 불려도 항목은 하나다.
    [ "$ASKED" = install ] && plant_session_state
    # 전역 도구를 깔 판이면 표식은 전역 지문을 굳힌 뒤(「선언 지문 굳히기」)로 미룬다 — 세션 단계의 지문 게이트와 같은 까닭이다
    if [ -n "$DO_GLOBAL" ]; then PW_DEFER=1; else pc_wide_mark; fi
  fi

  # ── 파이썬 축 — requirements.txt 의 존재가 곧 선언이다. venv 에 깐다 ──
  #    프로젝트 축이라 저장소마다 돈다 — 실물이 저장소 안 `.venv` 다.
  if [ -n "$DO_REPO" ] && [ -f "$PROJECT_DIR/requirements.txt" ]; then
    # 판 일치 — 선언(probe = python-version)이 들면 그 판으로 venv 를 만든다. 개발 세계의 판(선언 값)과 다른 판으로 재면
    #   같은 코드가 두 세계에서 다르게 판정된다 — 바닥(최저선)이 아니라 일치다. 기본 python3 이 낡은 판이면 코드가 import
    #   부터 죽는데 의존성 프로브는 초록이다(부재가 통과로 읽히는 자리). 그 판을 찾는 차례 — PATH 의 그 판 이름 → 윈도우
    #   py 런처 → uv 로 내려받기.
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
        # PATH 에 그 판 이름이 이미 있나 — uv 가 깐 것도 다음 세션부턴 이 이름으로 선다
        _ma="${PY_TGT_STR%%.*}"; _mi="${PY_TGT_STR#*.}"; _mi="${_mi%%.*}"
        if [ "$(py_num "python${_ma}.${_mi}")" = "$PY_TGT" ]; then
          PY_CMD="python${_ma}.${_mi}"
        # 윈도우 py 런처 — python.org · winget 설치는 `python3.14` 같은 이름을 안 만들고 `py -3.14` 런처에만 등록한다.
        #   런처가 내주는 실행 파일 경로를 잡아야 venv/-m 호출에 단일 실행형으로 쓸 수 있다.
        elif [ "$OS" = windows ] && command -v py >/dev/null 2>&1 &&
             py "-${_ma}.${_mi}" -c '' >/dev/null 2>&1; then
          _found="$(py "-${_ma}.${_mi}" -c 'import sys; print(sys.executable)' 2>/dev/null)"
          [ -n "$_found" ] && [ "$(py_num "$_found")" = "$PY_TGT" ] && PY_CMD="$_found"
        # uv 로 내려받는다 — 패치판은 uv 목록의 최신이 정한다(선언은 부판까지만 문다). 받기 전에 uv 부터 새 판으로
        #   올린다(`uv_fresh` 머리말).
        elif command -v uv >/dev/null 2>&1; then
          uv_fresh
          try "$PY_TGT_BY" uv python install "$PY_TGT_STR" || true
          _found="$(uv python find "$PY_TGT_STR" 2>/dev/null)"
          [ -n "$_found" ] && [ "$(py_num "$_found")" = "$PY_TGT" ] && PY_CMD="$_found"
        fi
      fi
      # 고른 해석기를 실물로 편다 — 그 이름이 uv 의 링크(~/.local/bin)면 그것이 venv 의 home 으로 앉아 표준 라이브러리를
      # 못 찾고 venv 가 깨진다(encodings 부재로 즉사). 다른 venv 의 감싸개(`wire_python_path`)면 남의
      # venv 를 거쳐 선다 — 감싸개는 보통 파일이라 링크 풀기로는 안 펴진다. 그래서 해석기에게 제 바탕 실행파일의
      # 실경로를 묻는다: 링크도 감싸개도 같은 실물로 펴진다. 윈도우는 venv 를 복사로 만들어 이 함정이 없다.
      if [ "$OS" = linux ]; then
        _rp="$("$PY_CMD" -c 'import os, sys; print(os.path.realpath(getattr(sys, "_base_executable", "") or sys.executable))' 2>/dev/null)"
        [ -n "$_rp" ] && [ -x "$_rp" ] && PY_CMD="$_rp"
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
    # venv 는 폴더가 서 있나가 아니라 pip 이 닿나로 잰다(`venv_ready` — `--needs-install` 과 같은 자). 반쯤 선 것은 지우고
    #   다시 만든다.
    if ! venv_ready; then
      [ -d "$VENV" ] && rm -rf "$VENV"
      # ⚠ stdin 을 물려준다 — venv 는 pip 을 깔 때 제 안에서 파이썬을 한 번 더 띄우며 부모의 표준입력 손잡이를 복제하는데,
      #   창 없이 띄워진 사슬(`CreateNoWindow` — 설치 화면이 엔진을 그렇게 띄운다)을 타고 오면 그 손잡이가 없어
      #   `[WinError 6]` 으로 죽는다. 부르는 자리마다 고치면 다음 런처에서 또 만나므로 여기서 막는다 — `/dev/null` 은
      #   윈도우에서 NUL 로 서서 어느 부모 밑에서도 성한 손잡이가 된다.
      _vt0=$SECONDS
      if try "venv" "$PY_CMD" -m venv "$VENV" </dev/null; then
        printf '  · venv — 만들었다 (%s초)\n' "$((SECONDS - _vt0))"
      else
        printf '  · venv — 못 만들었다 (%s초)\n' "$((SECONDS - _vt0))"
      fi
    fi
    # 방금 만든 venv 를 프로브가 보게 한다 — VENV_PY 는 「해석기와 처음 값」 단계(venv 가 아직 없던 때)에 굳었다. 안 풀면
    #   첫 회 진단이 맨 해석기를 재서 헛빨강을 낸다.
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
      # 조용히 건너뛰지 않는다 — pip 이 없을 때 말없이 지나가면 다음 세션은 실패 줄조차 못 본 채 의존성만 꺼진 상태로
      #   돈다. 사유가 있어야 다음 사람이 무엇을 갖추면 닿는지 안다.
      nogo "파이썬 의존성" "venv 에 pip 이 없다 — 위 「venv」 사유를 본다. 그것이 서야 requirements.txt 를 깐다" || true
    fi
    # 세션 셸 배선은 wire_python_path 한 벌이다 — auto 매 세션 갈래와 같은 것을 민다
    wire_python_path
  fi

  # ── 노드 축 — package-lock.json 의 존재가 곧 선언이다. install 이 아니라 ci 다 ──
  #    잠금을 추적하는 까닭이 「판이 갈리면 게이트를 못 믿는다」라서다. 프로젝트 축이라 저장소마다 돈다 — 실물이 저장소 안
  #    `node_modules` 다.
  if [ -n "$DO_REPO" ] && [ -f "$PROJECT_DIR/package-lock.json" ] && command -v npm >/dev/null 2>&1; then
    _nt0=$SECONDS
    if ( cd "$PROJECT_DIR" && try "노드 의존성" npm ci --no-audit --no-fund --silent ); then
      printf '  · 노드 의존성 — 깔았다 (%s초)\n' "$((SECONDS - _nt0))"
    else
      printf '  · 노드 의존성 — 못 깔았다 (%s초)\n' "$((SECONDS - _nt0))"
    fi
  fi

  # ── 선언 도구를 까는 손 — 프로브 → 설치 → 배선 → 재프로브. 판정은 진단 단계 한 자리가 낸다 ──
  install_tool() {  # install_tool <선언파일> <이름> — 끝 값은 못 믿는다(갈래마다 끝 명령이 덮는다) · 성패는 실패 기록이 든다
    _f="$1"; _t="$2"
    case "$(decl_get "$_f" "$_t" install)" in
      github-release-binary)
        _repo="$(decl_get "$_f" "$_t" repo)"; _bin="$(decl_get "$_f" "$_t" bin)"
        if [ "$OS" = linux ]; then _asset="$(decl_get "$_f" "$_t" asset-linux)"
        else _asset="$(decl_get "$_f" "$_t" asset-windows)"; fi
        [ -n "$_repo" ] && [ -n "$_asset" ] && [ -n "$_bin" ] ||
          { nogo "$_t" "선언에 repo·asset-$OS·bin 중 빠진 것이 있다"; return 1; }
        # 태그를 박은 선언은 그 릴리스를 받고, 안 박으면 최신 릴리스다. 자산 이름에 판이 물린
        # 도구는 `{tag}` 를 그 태그로 채운다 — 안 박았으면 최신 태그를 읽어 채운다(`gh_latest_tag`).
        _tag="$(decl_get "$_f" "$_t" tag)"
        case "$_asset" in *'{tag}'*)
          [ -n "$_tag" ] || _tag="$(gh_latest_tag "$_repo")"
          [ -n "$_tag" ] ||
            { nogo "$_t" "자산 이름에 판이 물렸는데 최신 태그를 못 읽었다 — github.com 에 닿나 본다"; return 1; } ;;
        esac
        if [ -n "$_tag" ]; then
          _asset="$(printf '%s' "$_asset" | sed "s/{tag}/$_tag/g")"
          _url="https://github.com/$_repo/releases/download/$_tag/$_asset"
        else
          _url="https://github.com/$_repo/releases/latest/download/$_asset"
        fi
        case "$_asset" in
          *.tar.gz)   # 리눅스 — 풀어서 훅 자리(`GRB_HOME`)에 놓는다
            { [ "$OS" = linux ] && [ -w "$GRB_HOME" ]; } ||
              { nogo "$_t" "$_asset 는 tar.gz 인데 여기는 $OS 이거나 $GRB_HOME 에 쓸 권한이 없다"; return 1; }
            _tgz="$(mktemp)"
            if try "$_t" gh_asset_get "$_tgz" "$_url"; then
              try "$_t" tar xzf "$_tgz" --strip-components=1 -C "$GRB_HOME" "${_asset%.tar.gz}/$_bin" &&
                chmod +x "$GRB_HOME/$_bin" 2>/dev/null
            fi
            rm -f "$_tgz" ;;
          *.tar.xz)   # 리눅스 — 묶음 안 폴더 이름이 자산 이름과 다를 수 있어(판만 든다) 풀고 찾는다
            { [ "$OS" = linux ] && [ -w "$GRB_HOME" ]; } ||
              { nogo "$_t" "$_asset 는 tar.xz 인데 여기는 $OS 이거나 $GRB_HOME 에 쓸 권한이 없다"; return 1; }
            _work="$(mktemp -d)"
            if try "$_t" gh_asset_get "$_work/pkg.tar.xz" "$_url" &&
               try "$_t" tar xJf "$_work/pkg.tar.xz" -C "$_work"; then
              _found="$(find "$_work" -name "$_bin" -type f 2>/dev/null | head -1)"
              # 못 찾거나 못 놓으면 사유를 남긴다 — 안 남기면 진단이 사유 없는 ❌ 를 낸다
              if [ -z "$_found" ]; then nogo "$_t" "$_asset 을 풀었는데 안에 $_bin 이 없다 — 묶음 꼴이 바뀌었나 본다"
              elif cp "$_found" "$GRB_HOME/$_bin" 2>/dev/null; then chmod +x "$GRB_HOME/$_bin"
              else nogo "$_t" "$_bin 을 $GRB_HOME 에 못 놓았다 — 도는 중이거나 권한이 없다"; fi
            fi
            rm -rf "$_work" ;;
          *.zip)      # 윈도우 — Git Bash 에 unzip 이 없을 수 있어 PowerShell 로 풀고 훅 자리(`GRB_HOME`)에 놓는다
            _work="$(mktemp -d)"; mkdir -p "$GRB_HOME"
            if try "$_t" gh_asset_get "$_work/pkg.zip" "$_url"; then
              powershell.exe -NoProfile -Command \
                "Expand-Archive -Force -Path '$(cygpath -w "$_work/pkg.zip")' -DestinationPath '$(cygpath -w "$_work")'" \
                >/dev/null 2>&1
              _found="$(find "$_work" -name "$_bin.exe" -type f 2>/dev/null | head -1)"
              if [ -z "$_found" ]; then nogo "$_t" "$_asset 을 풀었는데 안에 $_bin.exe 가 없다 — 풀기가 졌거나 묶음 꼴이 바뀌었다"
              elif ! cp "$_found" "$GRB_HOME/$_bin.exe" 2>/dev/null; then
                nogo "$_t" "$_bin.exe 를 $GRB_HOME 에 못 놓았다 — 도는 중이면 창을 닫고 다시 연다"; fi
            fi
            rm -rf "$_work" ;;
          *) nogo "$_t" "$_asset — 모르는 자산 꼴이다(푸는 갈래는 .tar.gz · .tar.xz · .zip 셋뿐)"; return 1 ;;
        esac ;;
      npm-global)
        npm_ready "$_f" "$_t" || return 1
        try "$_t" npm install -g --no-audit --no-fund --silent "$_pkg" || true
        npm_browsers "$_f" "$_t" ;;
      apt-package)   # 배포판 저장소에서 깐다 — 자산 이름에 판이 안 물려 선언이 안 낡는다.
        _pkg="$(decl_get "$_f" "$_t" package)"
        { [ "$OS" = linux ] && [ -n "$_pkg" ] && command -v apt-get >/dev/null 2>&1; } ||
          { nogo "$_t" "apt 갈래를 못 탄다 — 여기는 $OS 이거나 선언에 package 가 없거나 apt-get 이 없다"; return 1; }
        # 권한이 없으면 물러난다 — sudo 를 부르지 않는다(물어볼 사람이 없는 자리다). 물러나되 사유는 남긴다 — 안 남기면
        #   진단이 「안 닿는다」만 낸다.
        [ "$(id -u)" = 0 ] ||
          { nogo "$_t" "루트가 아니라 apt 로 못 깐다 — sudo 는 부르지 않는다"; return 1; }
        # 목록이 신선하면 한 걸음, 낡았으면 갱신하고 한 번 더. 갱신을 앞에 세우면 매 설치가
        # 느려지고, 아예 안 두면 이미지가 오래된 기계에서 영영 못 깐다.
        try "$_t" sh -c "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $_pkg ||
          { apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $_pkg; }" ;;
      winget)        # 윈도우 패키지 관리자 — 폴더째 와야 도는 도구가 여기 산다.
                     # ⚠ `github-release-binary` 로는 못 깐다 — 그 갈래는 자산 zip 에서 실행파일 하나만 꺼내
                     #   `$HOME/bin` 에 놓는데, 곁의 `lib/` 가 있어야 도는 물건은 깔린 것처럼 보이고 안 돈다.
                     # 자산 이름에 판이 안 물려 선언이 안 낡는다 — `apt-package` 와 같은 값이다.
        _id="$(decl_get "$_f" "$_t" winget-id)"
        { [ "$OS" = windows ] && [ -n "$_id" ]; } ||
          { nogo "$_t" "winget 갈래를 못 탄다 — 여기는 $OS 이거나 선언에 winget-id 가 없다"; return 1; }
        command -v winget.exe >/dev/null 2>&1 ||
          { nogo "$_t" "winget 이 없다 — 옛 윈도우이거나 앱 설치 관리자가 안 깔렸다"; return 1; }
        # 사용자 자리에 깐다 — 관리자 없이 서야 하는 것이 이 훅의 규율이다(apt 갈래가 sudo 를 안 부르는 것과 같은 축).
        # ⚠ `--source winget` 을 박는다 — 안 박으면 msstore 까지 훑다가 그쪽 인증서 오류(`0x8a15005e`)로 설치가 아예 시작을
        #   못 한다. 묻지 않게 한다 — 물어볼 사람이 없는 자리다.
        # 깐 뒤 이 세션에서는 아직 PATH 에 안 걸린다 — winget 은 사용자 PATH 를 고치고 그 값은 이미 뜬 셸에 안 온다. 그래서
        #   부르는 쪽이 winget 의 링크 자리도 보게 둔다(`scripts/build-setup-exe.ps1` 이 그렇게 한다).
        # winget 에 이미 있는데 실행파일이 안 보이면 다시 깔지 않는다 — 낡은 PATH 는 프로브가 레지스트리에서 따라잡으므로
        #   (`path_catchup`) 여기 오는 것은 따라잡고도 안 보이는 자리다: 선언의 `probe-target` 이 winget 이 세운 실행파일
        #   이름과 다르다. 그대로 깔러 가면 winget 이 「올릴 판이 없다」(43)로 지고 고칠 자리가 winget 인 것처럼 읽힌다.
        #   실행파일이 PATH 에 있을 때는 안 묻는다 — 판을 올리러 온 것이라 그대로 깐다.
        _wtg="$(decl_get "$_f" "$_t" probe-target)"
        if ! command -v "$_wtg" >/dev/null 2>&1 &&
           winget.exe list --id "$_id" --exact --source winget --accept-source-agreements --disable-interactivity >/dev/null 2>&1; then
          nogo "$_t" "winget 에는 $_id 가 깔려 있는데 사용자 PATH 에서도 $_wtg 가 안 보인다 — 선언의 probe-target 이 winget 이 세운 실행파일 이름과 맞는지 본다"
          return 1
        fi
        try "$_t" winget.exe install --id "$_id" --exact --source winget --scope user --accept-package-agreements --accept-source-agreements --disable-interactivity
        # 깐 자리를 winget 이 **방금** 레지스트리에 적었다 — 설치 앞의 프로브가 이미 한 번 따라잡았으므로
        #   표식을 풀어 뒤따르는 프로브가 다시 읽게 한다. 안 풀면 첫 설치가 「안 닿는다」로 선다.
        PATH_CAUGHT='' ;;
      pip-user)      # 파이썬 패키지 — **저장소 venv 가 아니라 PC 의 파이썬**에 깐다(`PC_PY` 곁말).
        _pkg="$(decl_get "$_f" "$_t" package)"
        [ -n "$_pkg" ] || { nogo "$_t" "선언에 package 가 없다"; return 1; }
        "$PC_PY" -c '' >/dev/null 2>&1 ||
          { nogo "$_t" "파이썬이 안 선다 — $PC_PY 가 안 불린다. 파이썬을 깔면 다음 설치가 깐다"; return 1; }
        # `--user` 로 깐다 — 관리자 없이 서야 한다(winget 갈래와 같은 축). `Program Files` 에 선 파이썬은 사이트 폴더에 못 쓴다.
        # ⚠ `--upgrade` 를 단다 — 이 걸음은 없을 때만이 아니라 판이 다를 때도 불린다. 안 달면 pip 이 「이미 있다」로 끝나 새
        #   판이 영영 안 온다.
        # ⚠ 배포판 파이썬의 잠금(PEP 668)은 환경변수로 연다 — 리눅스 배포판의 파이썬은 pip 을 「밖에서 관리된다」며 거절하는데,
        #   사용자 자리 설치는 배포판 패키지를 안 건드린다. 인자(`--break-system-packages`)로 주면 그 인자를 모르는 낡은 pip 이
        #   통째로 지고, 환경변수는 모르는 판이 그냥 지나친다.
        # 기다림 15초 · 되풀이 한 번 — 되풀이는 순간 결함을 건지는 몫이라 없애지 않는다. 패킷을 떨구는 망에서는 한 번 묻는 데
        #   `기다림 × (되풀이 + 1)` 이 들지만 세션의 설치는 배경에서 돌아(`install_bg`) 세션 시작을 안 잡는다.
        try "$_t" env PIP_BREAK_SYSTEM_PACKAGES=1 "$PC_PY" -m pip install --user --upgrade \
          --disable-pip-version-check --no-input --timeout 15 --retries 1 "$_pkg" ;;
      project-axis) : ;;   # 설치 없음 — 판의 진본은 package.json·requirements.txt 다
      # 모르는 갈래도 사유를 남긴다 — 선언에 `install` 을 빠뜨리거나 오타를 내면 아무것도 안 하고 지나가, 진단은 「안
      #   닿는다」만 내고 선언이 틀렸다는 말은 아무 데도 없다. 이름을 그대로 되돌려 준다.
      *) nogo "$_t" "설치법(install)이 선언에 없거나 모르는 갈래다: $(decl_get "$_f" "$_t" install)"; return 1 ;;
    esac
  }
  # ── npm-global 갈래의 앞뒤 — 하나씩 까는 `install_tool` 과 묶어 까는 `install_npm_batch` 가 같이 쓴다 ──
  npm_ready() {  # npm_ready <선언파일> <이름> — 깔 수 있으면 0 이고 $_pkg 가 선다 · 아니면 사유를 남기고 1
    _pkg="$(decl_get "$1" "$2" package)"
    [ -n "$_pkg" ] || { nogo "$2" "선언에 package 가 없다"; return 1; }
    command -v npm >/dev/null 2>&1 ||
      { nogo "$2" "npm 이 없다 — 노드를 깔면 다음 설치가 깐다"; return 1; }
  }
  npm_browsers() {  # npm_browsers <선언파일> <이름> — 패키지를 깐 뒤에 부른다 · 값은 늘 0
    # 브라우저는 패키지와 따로 온다 — 선언이 browsers 를 들 때만, 컨테이너가 미리
    # 받아 둔 자리(skip-browsers-env)가 없을 때만 받는다.
    _pkg="$(decl_get "$1" "$2" package)"
    _br="$(decl_get "$1" "$2" browsers)"
    _skipname="$(decl_get "$1" "$2" skip-browsers-env)"
    _skipval=""; [ -n "$_skipname" ] && _skipval="${!_skipname:-}"
    if [ -n "$_br" ] && [ -z "$_skipval" ] && command -v "$_pkg" >/dev/null 2>&1; then
      # ⚠ 뒷길(browsers-fallback)이 선언돼 있으면 제 CDN 을 아예 안 부른다 — 그 명령은 받기 전에 제 판과 안 맞는 브라우저를
      #   「쓸모없다」며 먼저 지워, 받는 길이 막힌 자리에서는 지우기만 하고 못 받아 멀쩡히 있던 것(이미지가 미리 들고 온
      #   브라우저)까지 없어진다. 뒷길이 선언돼 있다는 것은 받는 길이 따로 서 있다는 뜻이라 여기서 걸 값이 없다(뒷길로
      #   받은 것은 실행 파일을 직접 가리켜 쓰므로 playwright 의 판과 어긋나도 된다).
      if [ -z "$(decl_get "$1" "$2" browsers-fallback)" ]; then
        # shellcheck disable=SC2086 # browsers 는 브라우저 이름 여럿을 한 줄에 든다 — 갈라야 인자가 된다
        try "$2" "$_pkg" install $_br || true
      fi
    fi
    return 0
  }
  install_one() {  # install_one <선언파일> <이름> — 하나씩 깐다 · 걸린 초를 `GQ_SECS` 에 이름과 함께 더한다
    _io0=$SECONDS
    install_tool "$1" "$2" || true
    GQ_SECS="$GQ_SECS $2=$((SECONDS - _io0))"
  }
  # ── npm-global 을 한 번에 깐다 — `npm install -g` 한 번의 고정 값(노드 띄우기 · 레지스트리 묻기)을 도구마다 안 문다 ──
  #    한 패키지가 지면 npm 은 묶음 전체를 되돌린다 — 그때는 하나씩 다시 깔아 진 것을 제 이름으로 가른다.
  #    묶음의 사유는 실패 기록에 안 적고 화면 한 줄로만 낸다: 기록은 도구 이름으로 읽히는데(진단 · 다음 설치의
  #    「지난 실패」) 묶음은 도구가 아니고, 진 도구는 하나씩 깔 때 제 이름으로 적힌다.
  install_npm_batch() {  # install_npm_batch <차례 파일> — 그 파일의 npm-global 줄만 깐다 · 판정은 안 낸다
    _nbsrc="$1"; _nbq="$(mktemp)"; _nbn=''
    set --
    while IFS="$GQ_SEP" read -r _nbf _nbt _nbi _nbrest <&4; do
      [ "$_nbi" = npm-global ] || continue
      npm_ready "$_nbf" "$_nbt" || continue
      set -- "$@" "$_pkg"
      _nbn="$_nbn $_nbt"
      printf '%s%s%s\n' "$_nbf" "$GQ_SEP" "$_nbt" >> "$_nbq"
    done 4< "$_nbsrc"
    if [ $# -le 1 ]; then
      # 하나면 묶을 것이 없다 — 하나씩 까는 길 그대로다(지면 같은 것을 두 번 깔지 않는다)
      while IFS="$GQ_SEP" read -r _nbf _nbt <&4; do install_one "$_nbf" "$_nbt"; done 4< "$_nbq"
      rm -f "$_nbq"; return 0
    fi
    _nbt0=$SECONDS; _nbfl="$(mktemp)"; _nbsave="$FAILS"; FAILS="$_nbfl"
    try "npm 전역 묶음" npm install -g --no-audit --no-fund --silent "$@"; _nbr=$?
    FAILS="$_nbsave"
    if [ "$_nbr" -eq 0 ]; then
      printf '  · npm 전역 묶음 (%s) — 한 번에 깔았다 (%s초)\n' "${_nbn# }" "$((SECONDS - _nbt0))"
      while IFS="$GQ_SEP" read -r _nbf _nbt <&4; do npm_browsers "$_nbf" "$_nbt"; done 4< "$_nbq"
    else
      printf '  · npm 전역 묶음 (%s) — 한 번에 못 깔아 하나씩 다시 깐다: %s (%s초)\n' "${_nbn# }" \
        "$(awk -F'\t' '{print $2; exit}' "$_nbfl" 2>/dev/null)" "$((SECONDS - _nbt0))"
      while IFS="$GQ_SEP" read -r _nbf _nbt <&4; do install_one "$_nbf" "$_nbt"; done 4< "$_nbq"
    fi
    rm -f "$_nbq" "$_nbfl"
  }
  # ── 깔 차례를 깐다 — 릴리스 자산은 배경에서 나란히, npm-global 은 한 번에, 나머지는 하나씩 ──────────
  #    받기는 망을 기다리는 일이라 겹쳐도 서로 안 늦춘다 — 릴리스 자산을 먼저 배경에 띄우고 그동안 앞에서 나머지를 깐다.
  #    ⚠ 배경 작업은 출력 · 실패 기록 · 임시 파일을 작업마다 제 자리(`<작업 폴더>/<번호>.*`)에 둔다 — 한 파일에 같이
  #      적으면 줄이 섞인다. 다 끝난 뒤 차례대로 붙이고 작업 폴더째 걷는다. 성패는 이 뒤 다시 재기가 도구마다 낸다 —
  #      여기서는 판정을 안 낸다.
  install_queue() {  # install_queue <차례 파일> — 표준 입력은 부르는 쪽이 뗀다(`</dev/null`)
    _iqd="$(mktemp -d)"; _iqk=0; _iqpids=''; _iqn=''
    while IFS="$GQ_SEP" read -r _iqf _iqt _iqi _iqrest <&4; do
      [ "$_iqi" = github-release-binary ] || continue
      _iqk=$((_iqk + 1)); _iqw="$_iqd/$_iqk"
      mkdir -p "$_iqw.tmp"; printf '%s' "$_iqt" > "$_iqw.name"
      # 받기의 초는 작업이 안에서 찍는다 — 바깥에서 재면 앞에서 도는 npm · winget 을 기다린 초가 섞인다.
      # 4 번은 닫고 띄운다 — 차례 파일을 같이 쥐면 작업이 읽는 만큼 이 고리의 읽기 자리가 밀린다.
      ( printf '%s\n' "$SECONDS" > "$_iqw.t0"
        TMPDIR="$_iqw.tmp"; export TMPDIR; FAILS="$_iqw.fail"
        install_tool "$_iqf" "$_iqt"; _iqr=$?
        printf '%s\n' "$SECONDS" > "$_iqw.t1"
        exit "$_iqr" ) 4<&- > "$_iqw.log" 2>&1 &
      _iqpids="$_iqpids $!"; _iqn="$_iqn $_iqt"
    done 4< "$1"
    install_npm_batch "$1"
    while IFS="$GQ_SEP" read -r _iqf _iqt _iqi _iqrest <&4; do
      case "$_iqi" in github-release-binary|npm-global) continue ;; esac
      install_one "$_iqf" "$_iqt"
    done 4< "$1"
    [ -n "$_iqpids" ] || { rm -rf "$_iqd"; return 0; }
    _iqj=0; _iqs=''; _iqe=''
    for _iqp in $_iqpids; do
      _iqj=$((_iqj + 1)); _iqw="$_iqd/$_iqj"
      wait "$_iqp"; _iqr=$?
      # 신호로 죽은 작업은 `try` · `nogo` 가 적을 틈이 없다 — 여기서 적지 않으면 ❌ 가 사유 없이 서고, 낡은 실행파일이 남은
      #   자리에서는 다시 재기가 「앞선 옛 것이 가린다」로 읽어 진짜 까닭이 가려진다.
      _iqm=''
      if [ "$_iqr" -ge 128 ]; then _iqm="설치 작업이 신호로 끝났다 (rc $_iqr)"
      elif [ "$_iqr" -ne 0 ] && [ ! -s "$_iqw.fail" ]; then _iqm="설치 작업이 사유를 안 남기고 끝났다 (rc $_iqr)"; fi
      if [ -n "$_iqm" ]; then
        IFS= read -r _iqnm < "$_iqw.name"
        printf '%s\t%s\n' "$_iqnm" "$_iqm" >> "$_iqw.fail"
      fi
      # 받기의 초 — 가장 이른 시작부터 가장 늦은 끝까지(받고 풀어 놓기까지). 끝을 못 찍고 죽은 작업은 끝에 안 든다
      _iqv=''; [ -s "$_iqw.t0" ] && IFS= read -r _iqv < "$_iqw.t0"
      [ -n "$_iqv" ] && { [ -z "$_iqs" ] || [ "$_iqv" -lt "$_iqs" ]; } && _iqs="$_iqv"
      _iqv=''; [ -s "$_iqw.t1" ] && IFS= read -r _iqv < "$_iqw.t1"
      [ -n "$_iqv" ] && { [ -z "$_iqe" ] || [ "$_iqv" -gt "$_iqe" ]; } && _iqe="$_iqv"
    done
    _iqsec='?'; [ -n "$_iqs" ] && [ -n "$_iqe" ] && _iqsec=$((_iqe - _iqs))
    printf '  · 릴리스 자산 (%s) — 나란히 받았다 (%s초)\n' "${_iqn# }" "$_iqsec"
    _iqj=0
    while [ "$_iqj" -lt "$_iqk" ]; do
      _iqj=$((_iqj + 1))
      [ -s "$_iqd/$_iqj.log" ] && cat "$_iqd/$_iqj.log"
      [ -s "$_iqd/$_iqj.fail" ] && cat "$_iqd/$_iqj.fail" >> "$FAILS" 2>/dev/null
    done
    rm -rf "$_iqd"
  }
  browsers_ready() {  # browsers_ready <선언파일> <이름> — 브라우저는 패키지와 따로 온다
    # 설치 안이 아니라 따로 서는 까닭 — 줄기가 `프로브 실패 → 설치`라 패키지가 한 번 깔린 뒤로는 설치가 안 불리는데,
    #   패키지가 있다고 브라우저가 있는 것이 아니다(컨테이너가 새로 뜨면 브라우저만 사라진다). 그래서 프로브와 무관하게
    #   전역 걸음이 도구마다 한 번 댄다. 받을지 말지는 스크립트가 스스로 가른다 — 있으면 두고, 없으면 그때의 최신을 받는다.
    _f="$1"; _t="$2"
    _br=''; _skipname=''; _fb=''
    {
      IFS= read -r _br
      IFS= read -r _skipname
      IFS= read -r _fb
    } <<EOF
$(decl_fields "$_f" "$_t" browsers skip-browsers-env browsers-fallback)
EOF
    [ -n "$_br" ] || return 0
    _skipval=""; [ -n "$_skipname" ] && _skipval="${!_skipname:-}"
    [ -z "$_skipval" ] || return 0
    [ -n "$_fb" ] || return 0
    # 경로는 **그 선언을 든 저장소** 기준이다(선언은 <저장소>/.claude/ 에 산다) — 그래서
    # 몸통은 무엇을 받는지도 어디서 받는지도 모른 채로 남는다.
    _fbroot="$(dirname "$(dirname "$_f")")"
    [ -f "$_fbroot/$_fb" ] || return 0
    _bt0=$SECONDS
    # 판정을 같이 싣는다 — 스크립트의 마지막 `[browser]` 줄(받았다 / 이미 있다). 초만 찍으면
    # 「받는 데 30초」와 「있는 것 확인에 30초」가 같은 얼굴이라 헛받기가 안 보인다.
    if try "$_t" bash "$_fbroot/$_fb"; then
      printf '  · %s — 브라우저 뒷길 (%s초 · %s)\n' "$_t" "$((SECONDS - _bt0))" "${TRY_LAST#\[browser\] }"
    else
      printf '  · %s — 브라우저 뒷길이 졌다 (%s초 · %s)\n' "$_t" "$((SECONDS - _bt0))" "${TRY_LAST#\[browser\] }"
    fi
  }
  wire_tool() {  # wire_tool <선언파일> <이름> — node-link: 이름 해석이 되게 만든다
    _f="$1"; _t="$2"
    _wg=''; _mod=''; _env=''; _wod=''
    {
      IFS= read -r _wg
      IFS= read -r _mod
      IFS= read -r _env
      IFS= read -r _wod
    } <<EOF
$(decl_fields "$_f" "$_t" wiring probe-target wiring-env on-demand)
EOF
    [ "$_wg" = node-link ] || return 0
    # 닿으면 그 답을 적는다 — 진단이 같은 물음을 다시 안 띄우고 인용한다(`repo_verified` 곁말).
    probe_tool node-resolvable "$_mod" "" && { repo_verified_put "$_f" "$_t" node-resolvable "$_mod"; return 0; }
    # ⚠ 못 건 배선은 실패로 적는다 — 이 걸음 뒤에 지문 도장이 찍히므로(「선언 지문 굳히기」) 조용히 나가면 그 저장소는
    #   「배선됐다」로 굳고, 다음 세션(auto)도 재설치(`--needs-install`)도 파일만 봐서 영영 다시 안 건다. 전역 도구가 저장소
    #   걸음보다 늦게 서는 판(노드가 설치 도중에 들어온 새 PC)이 그 자리다. 적어 두면 `--needs-install` 이 1 을 내 다음
    #   배포가 이 걸음을 다시 돌고, auto 는 매 세션 사유를 알린다.
    # on-demand 는 빼고 적는다 — 그 도구는 전역에 없는 것이 정상이다(부르는 자가 제 손으로 찾는다).
    [ "$_wod" = yes ] && return 0
    npm_root_g; _groot="$NPM_ROOT_G"
    [ -n "$_groot" ] ||
      { nogo "$_t" "배선을 못 걸었다 — npm 이 없다. 노드를 깔면 다음 설치가 잇는다"; return 0; }
    [ -d "$_groot/$_mod" ] ||
      { nogo "$_t" "배선을 못 걸었다 — 전역에 $_mod 가 아직 없다. 전역 설치가 선 뒤 다음 설치가 잇는다"; return 0; }
    # 전역 설치는 저장소 node_modules 밖이라 import 가 못 찾는다 — 저장소 안으로 건다.
    # ⚠ npm ci 가 node_modules 를 지우고 다시 만든다 — 그래서 「노드 축」 뒤에 선다.
    # ⚠ 스코프 패키지는 중간 폴더가 먼저 서야 한다 — `@scope/name` 은 링크 자리가 `node_modules/@scope/name` 이라, 뿌리만
    #   만들면 `ln` 이 조용히 진다.
    mkdir -p "$(dirname "$PROJECT_DIR/node_modules/$_mod")" 2>/dev/null
    if [ "$OS" = linux ]; then
      ln -sfn "$_groot/$_mod" "$PROJECT_DIR/node_modules/$_mod" 2>/dev/null || true
    elif [ ! -e "$PROJECT_DIR/node_modules/$_mod" ]; then
      # Git Bash 는 심링크를 못 건다 — 정션(관리자 권한 불요)으로 같은 효과를 낸다.
      # ⚠ 명령 전체를 한 문자열로 주면 cmd 인용이 깨진다 — 낱개 인자 + //J 로 넘긴다.
      cmd //c mklink //J "$(cygpath -w "$PROJECT_DIR/node_modules/$_mod")" "$(cygpath -w "$_groot/$_mod")" \
        >/dev/null 2>&1 || true
    fi
    probe_tool node-resolvable "$_mod" "" && { repo_verified_put "$_f" "$_t" node-resolvable "$_mod"; return 0; }
    # 이름 해석이 그래도 안 되면 소비자 계약(환경변수)으로 넘긴다 — 이름은 선언이 든다(`_env` 는 위 조회가 이미 읽었다).
    # 진입점을 손으로 찾지 않는다 — 폴더를 넘긴다. `index.js` 는 추측이라 그 이름이 아닌 패키지에서는 배선이 조용히 안
    #   선다. 진입점의 진본은 그 패키지의 `package.json` 이고 그것을 읽는 자는 받는 쪽의 해석기다.
    _entry="$_groot/$_mod"
    if [ -n "$_env" ]; then
      # 이 훅 **안에서도** 곧바로 선다 — 아래 걸음이 이 값을 본다. 파일로만 내보내면
      # 다음 세션에서야 서고, 이번 세션의 뒷걸음은 배선 없이 돈다.
      export "$_env=$_entry"
      [ -n "${CLAUDE_ENV_FILE:-}" ] && echo "export $_env=\"$_entry\"" >> "$CLAUDE_ENV_FILE"
      if [ "$OS" = linux ] && [ -w /etc/profile.d ] 2>/dev/null; then
        printf 'export %s="%s"\n' "$_env" "$_entry" > "/etc/profile.d/${PROJECT_NAME}-${_t}.sh"
      fi
    else
      # 넘길 계약도 없으면 이름 해석이 안 선 채로 남는다 — 위와 같은 까닭으로 적는다.
      nogo "$_t" "배선을 걸었는데 저장소 안에서 $_mod 가 안 풀린다 — node_modules/$_mod 를 본다"
    fi
    return 0
  }
  # ── 전역 자리의 배선 — 정션이 아니라 값 하나다. 늘 0 ──
  #    저장소 배선(`wire_tool`)은 `node_modules` 에 정션을 걸어 저장소 안에서 이름이 풀리게 한다. 전역 갈래에는 걸 저장소가
  #    없다 — 여기서 서야 하는 것은 바로 뒤의 브라우저 뒷길이 「playwright 가 이미 브라우저를 들고 있나」를 그 모듈에 물을
  #    수 있게 하는 것뿐이다. 그 값의 이름은 선언이 든다(`wiring-env`) — 몸통은 여기서도 도구 이름을 모른다.
  wire_global() {  # wire_global <선언파일> <이름>
    _wf="$1"; _wn="$2"
    _we=''; _wm=''
    { IFS= read -r _we; IFS= read -r _wm; } <<EOF
$(decl_fields "$_wf" "$_wn" wiring-env probe-target)
EOF
    [ -n "$_we" ] || return 0
    [ -n "$_wm" ] || return 0
    npm_root_g || return 0
    _wr="$NPM_ROOT_G"
    [ -d "$_wr/$_wm" ] || return 0
    export "$_we=$_wr/$_wm"
  }

  # ── 전역형 도구 — 기계에 한 번이다 ─────────────────────────────────
  #    전역 선언과 작업 루트에 붙은 모든 저장소의 전역형 선언을 이름으로 합쳐 같은 이름은 한 번만 깐다. 브라우저 뒷길도
  #    여기서 한 번. 저장소 고리 안에 두면 프로브 비용이 저장소 수에 비례하고, 저장소 안의 import 로 묻는 프로브가 정션
  #    전에 져서 `npm install -g` 가 저장소마다 되풀이된다 — 「전역은 한 번, 저장소는 배선만」이다.
  #    프로브를 빼서 빨리 하지 않는다 — 「깔린 것과 닿는 것은 다른 명제」다(이 파일 머리말). 줄인 것은 재는 일이 아니라
  #    묻는 횟수다.
  #    판정을 여기서 낸다 — 이 갈래는 진단 단계(저장소의 물음)를 안 지나므로, 여기서 말하지 않으면 무엇이 섰는지 아무 데도
  #    안 남는다. 설치의 목표는 「깔기를 돌았다」가 아니라 환경이 서 있다이다.
  GDOWN=0
  # ── 이 실행이 확인한 것을 적는다 — 캐시가 아니라 같은 실행의 인용문이다 ──────
  #    `CLAUDE_CONFIG_RUN` 은 배포 한 번을 가리키는 표식이고 그것을 세우는 자는 `deploy.ps1` 하나다. 표식이 없으면(세션 auto
  #    · `--check` · 사람이 손으로 부른 설치) 아무것도 안 적는다 — 그러면 저장소 진단도 볼 것이 없어 매번 프로브한다.
  #    ⚠ ✅ 명부에는 ✅ 만 적는다 — ❌ 를 적으면 저장소 진단이 안 선 도구를 「확인했다」로 읽는다. ❌ 는 따로 ❌ 명부
  #      (`GDOWNED`)에 적는다 — 저장소 진단이 같은 실패를 저장소마다 또 세지 않게 인용한다(`render_decl`).
  #    이름과 프로브 대상을 함께 적는다 — 이름만 적으면 대상이 다른 선언(같은 이름, 딴 모듈)이 같은 명제로 읽힌다. 어긋나면
  #    인용하지 않는 것이 규율이다. 줄의 꼴은 `global_run_put` 이 든다.
  gverified_put() {  # gverified_put <이름> <probe-target>
    global_run_put "$GVERIFIED" "$1" "$2"
  }
  install_global() {
    _gseen=""; _gl="$(mktemp)"; _gq="$(mktemp)"; GQ_SECS=''
    # 깔 차례의 칸 구분자 — 빈 칸(판을 못 읽었다)이 있어 공백류가 아닌 글자라야 칸이 안 접힌다
    GQ_SEP="$(printf '\037')"
    # 이번 실행의 명부는 **이번 실행이 처음부터 짓는다** — 이어 적으면 지난 실행에서 ✅ 였다가
    # 이번에 ❌ 인 도구가(❌ 명부는 그 반대가) 옛 줄로 살아남는다. 표식이 없으면 파일에 손도 안 댄다.
    [ -z "${CLAUDE_CONFIG_RUN:-}" ] || : > "$GVERIFIED" 2>/dev/null || true
    [ -z "${CLAUDE_CONFIG_RUN:-}" ] || : > "$GDOWNED" 2>/dev/null || true
    global_conf_list > "$_gl" 2>/dev/null
    # ── 걸음은 셋이다 — 다 재고 → 깔 것만 한꺼번에 깔고(`install_queue`) → 깐 것을 하나씩 다시 잰다.
    #    닿는 도구의 줄은 재는 자리에서 바로 내고, 깐 도구의 줄은 다시 재는 자리에서 차례대로 낸다.
    # ⚠ 걸린 초는 줄 끝에 붙는다 — 재는 자(installer · deploy)가 줄 앞을 보므로 앞은 안 바꾼다.
    #   깐 도구의 줄은 제 두 번의 재기에 하나씩 깐 초(`install_one`)를 더한다. 묶어 깐 초는 묶음 줄이 든다 —
    #   도구마다 붙이면 합이 실제보다 부푼다. `npm 전역 묶음` 은 그 한 번의 초고, `릴리스 자산` 은 작업들이 안에서
    #   찍은 가장 이른 시작부터 가장 늦은 끝까지 — 받고 풀어 놓기까지다(앞에서 도는 npm · winget 과 겹친 초라 걸음
    #   합에 더하지 않는다).
    # ⚠ 고리들은 차례를 4 번으로 읽고 표준 입력을 뗀다 — 프로브 · 깔기 · 브라우저 뒷길이 표준 입력을 먹으면 남은
    #   차례가 사라지고, 사람이 터미널에서 부른 판에서는 숨은 물음이 그 입력을 기다리며 멎는다.
    while IFS= read -r _gf <&4; do
      [ -f "$_gf" ] || continue
      for _gn in $(decl_sections "$_gf"); do
        _gi=''; _god=''; _gcb=''; _gtg=''; _gbn=''
        {
          IFS= read -r _gi
          IFS= read -r _god
          IFS= read -r _gcb
          IFS= read -r _gtg
          IFS= read -r _gbn
        } <<EOF
$(decl_fields "$_gf" "$_gn" install on-demand called-by probe-target bin)
EOF
        global_kind "$_gi" || continue
        case " $_gseen " in *" $_gn "*) continue ;; esac
        _gseen="$_gseen $_gn"
        # on-demand 는 안 깐다 — 부르는 자가 제 손으로 찾는다(선언 필드 표). 이름은 찍는다:
        # 안 찍으면 「선언했는데 왜 안 깔렸나」를 다음 사람이 훅에서 판다.
        if [ "$_god" = yes ]; then
          # 첫 낱말은 셸이 뗀다 — `cut` 을 띄우면 도구마다 프로세스가 하나 더 뜬다
          printf '  · %s — 필요할 때 깐다 (on-demand · %s)
' "$_gn" "${_gcb%% *}"
          continue
        fi
        # 밀 때는 「있나」에서 멈추지 않는다 — 「있나」와 「최신인가」는 다른 명제라, 있으면 건너뛰는 규칙으로는 영영 안
        # 올라간다. 그래서 깔린 판과 최신 판을 견주고 다를 때만 다시 깐다(`tool_version_*`). 둘 중 하나라도 못 읽으면 다시
        # 깐다 — 견주기가 져서 도구가 낡는 일은 없게 한다.
        _gt0=$SECONDS; _gvh=''; _gvw=''
        # 못 타는 설치법 — 있으면 초록, 없으면 비켜선다. 판 견주기도 안 한다(올릴 손이 없다).
        if ! kind_here "$_gi"; then
          if probe_global "$_gf" "$_gn"; then
            printf '  ✅ %s — 이미 닿는다 (전역) (%s초)\n' "$_gn" "$((SECONDS - _gt0))"
            gverified_put "$_gn" "$_gtg"
          else
            printf '  · %s — 이 자리(%s)에서는 안 깐다 — 설치법 %s 가 여기서 안 선다\n' "$_gn" "$OS" "$_gi"
          fi
          continue
        fi
        # winget 이 든 릴리스 바이너리는 판을 견주지도 않는다 — 깔지도 올리지도 않는다(`grb_foreign`).
        GRB_FOREIGN=''; _gvh=''   # 앞 도구의 판이 이 도구 줄에 안 묻게 — 다른 손 갈래는 판을 안 잰다
        if probe_global "$_gf" "$_gn" &&
           { { [ "$_gi" = github-release-binary ] && grb_foreign "$_gtg"; } ||
             [ -z "${UPGRADE:-}" ] ||
             { _gvh="$(tool_version_have "$_gf" "$_gn" || true)"
               _gvw="$(tool_version_latest "$_gf" "$_gn" || true)"
               [ -n "$_gvh" ] && [ "$_gvh" = "$_gvw" ]; }; }; then
          printf '  ✅ %s — 이미 닿는다 (전역)%s%s (%s초)\n' "$_gn" "${_gvh:+ · 최신 $_gvh}" \
            "${GRB_FOREIGN:+ · 다른 손이 든다($GRB_FOREIGN) — 훅은 깔지도 올리지도 않는다}" "$((SECONDS - _gt0))"
          # 다른 손이 드는데 훅 자리에도 제 사본이 남았으면 비킨다 — 안 비키면 PATH 앞에 선 그 사본(Git Bash 는 `~/bin` 이
          #   앞이다)이 계속 불리면서 이제 아무도 안 올려 낡는다. 지우지 않고 이름만 바꾼다 — 이름이 바뀌면 PATH 에서 안 풀린다.
          #   다른 손이 서는 것은 윈도뿐이라(`grb_foreign`) 훅이 놓는 이름(`<bin>.exe` · `install_tool`)만 본다.
          if [ -n "$GRB_FOREIGN" ] && [ -n "$_gbn" ] && [ -e "$GRB_HOME/$_gbn.exe" ]; then
            _gro="$GRB_HOME/$_gbn.exe"; _grn="$GRB_HOME/$_gbn.paisetup-retired"
            # `-n` — 앞서 비킨 것이 있으면 덮지 않는다. 덮지 않았으면 원본이 남으므로 남았나로 가른다
            mv -n "$_gro" "$_grn" 2>/dev/null
            if [ -e "$_gro" ]; then
              printf '  ⚠ %s — 훅 자리의 사본을 못 비켰다(%s) — 도는 중이거나 앞서 비킨 %s 가 있다. 두 벌이 PATH 에 남는다\n' \
                "$_gn" "$_gro" "$_grn"
            else
              printf '  · %s — 훅 자리의 사본을 비켰다(%s → %s) — 이제 다른 손의 것만 닿는다\n' "$_gn" "$_gro" "$_grn"
            fi
          fi
          gverified_put "$_gn" "$_gtg"
          wire_global "$_gf" "$_gn"
          browsers_ready "$_gf" "$_gn"
        else
          # 깔 차례 — 칸: 선언파일 · 이름 · 설치법 · 프로브 대상 · 깔린 판 · 최신 판 · 이 재기에 든 초
          printf '%s\n' "$_gf$GQ_SEP$_gn$GQ_SEP$_gi$GQ_SEP$_gtg$GQ_SEP$_gvh$GQ_SEP$_gvw$GQ_SEP$((SECONDS - _gt0))" >> "$_gq"
        fi
      done
    done 4< "$_gl" </dev/null
    [ -s "$_gq" ] && install_queue "$_gq" </dev/null
    while IFS="$GQ_SEP" read -r _gf _gn _gi _gtg _gvh _gvw _gtp <&4; do
      case "$GQ_SECS" in *" $_gn="*) _gxs="${GQ_SECS##* "$_gn"=}"; _gxs="${_gxs%% *}" ;; *) _gxs=0 ;; esac
      _gt0=$((SECONDS - _gtp - _gxs))
      if probe_global "$_gf" "$_gn"; then
        # 민 자리면 무엇이 무엇으로 갔나를 적는다 — 새 판이 규칙을 바꿔 어제 통과한 파일이
        # 막히면, 까닭을 짚을 자리가 이 한 줄이다.
        # ⚠ 설치가 졌나는 종료코드가 아니라 실패 기록으로 가른다 — 갈래마다 끝 명령(`rm` 등)이 종료코드를 덮어
        #   `install_tool` 의 값을 못 믿는다. 이 실행 머리에서 비운 기록에 이 도구의 줄이 섰으면 졌다 — 낡은 실행파일이
        #   남아 프로브는 참이어도, 「다시 깔았다」나 「옛 것이 가린다」로 읽으면 진짜 사유(받기가 막힌 망 등)가 가려진다.
        _gvf="$(awk -F'\t' -v k="$_gn" '$1==k{print $2; exit}' "$GFAILS" 2>/dev/null)"
        _gvn=''; [ -n "$_gvh" ] && _gvn="$(tool_version_have "$_gf" "$_gn" || true)"
        if [ -n "$_gvf" ]; then _gvm="닿지만 설치가 졌다 — ${_gvf}${_gvn:+ · 지금 $_gvn}${_gvw:+ (최신 $_gvw)}"
        elif [ -z "$_gvh" ]; then _gvm='이번에 깔았다'
        elif [ "$_gvn" != "$_gvh" ]; then _gvm="새 판으로 올렸다: $_gvh → $_gvn"
        elif [ -z "$_gvw" ]; then _gvm="다시 깔았다 — 최신 판을 못 읽었다 · 지금 $_gvn"
        else
          # 깔았는데 판이 그대로다 — 받은 자리보다 앞선 옛 것이 이름을 쥐고 있다.
          _gvm="다시 깔았는데 여전히 $_gvn 다 (최신 $_gvw) — 앞선 옛 것: $(command -v "$_gtg" 2>/dev/null || echo '?')"
        fi
        printf '  ✅ %s — %s (전역) (%s초)\n' "$_gn" "$_gvm" "$((SECONDS - _gt0))"
        gverified_put "$_gn" "$_gtg"
      else
        printf '  ❌ %s — 안 닿는다%s (%s초)\n' "$_gn" \
          "$(awk -F'\t' -v k="$_gn" '$1==k{printf " · 설치 실패: %s", $2; exit}' "$GFAILS" 2>/dev/null)" \
          "$((SECONDS - _gt0))"
        GDOWN=$((GDOWN + 1))
        global_run_put "$GDOWNED" "$_gn" "$_gtg"
      fi
      wire_global "$_gf" "$_gn"
      browsers_ready "$_gf" "$_gn"
    done 4< "$_gq" </dev/null
    rm -f "$_gl" "$_gq"
  }
  if [ -n "$DO_GLOBAL" ]; then
    echo "전역: 전역형 도구 — 기계에 한 번 깐다 · 깔리는 자리는 저장소가 아니라 홈이다 ($(home_hook_root) 에 붙은 저장소의 선언까지 합친다)"
    # 전역 갈래의 실패는 기계 한 자리에 적는다 — `try`·`nogo` 가 보는 이름을 그 동안만 바꾼다
    _savefails="$FAILS"; FAILS="$GFAILS"
    install_global
    FAILS="$_savefails"
  fi

  # ── 세션의 python3 — 리눅스는 전역 선언(`probe = python-version`)의 판을 기계 파이썬으로 세운다 ──────────────
  #    설치기가 안 도는 자리(클라우드 컨테이너)라 이 걸음이 든다 — 윈도우는 설치기가 같은 선언에서 winget id 를 지어 깐다.
  #    uv 의 `--default` 가 `~/.local/bin` 에 `python3` · `python` 링크를 세우고 시스템 파이썬은 그대로 둔다. 판을 올리면
  #    전역 지문이 바뀌어 다음 세션이 이 걸음을 다시 돈다.
  #    재는 자리는 `~/.local/bin/python3` 다 — 도구 셸은 그 폴더가 PATH 맨 앞이라(`wire_python_path` 곁말) 거기 선 것이
  #    세션의 python3 다. 그 자리의 꼴로 가른다:
  #      비었다          PATH 의 python3 이 그 판이면 둔다 · 아니면 uv 로 세운다
  #      uv 의 링크다    그 판이면 둔다 · 아니면 uv 로 다시 세운다
  #      그 밖의 것이다  안 건드리고 그렇다고 한 줄 낸다 — 저장소 venv 감싸개면 그 자리의 python3 는 그 venv 이고 venv 의
  #                      판은 「파이썬 축」이 맞춘다. uv 는 제가 안 세운 파일을 안 덮고 경고만 남긴 채 0 으로 끝나므로,
  #                      불러도 같은 거절이 매번 되풀이될 뿐이다
  #    전역 선언만 읽는다 — 저장소 선언이 이기는 것은 그 저장소의 venv 까지고, 기계에 하나인 python3 는 전역 판을 따른다.
  #    진 것은 까닭을 달고 꺼진 검사로 센다 — `PY3_WHY` 를 진단 단계가 「세션의 python3」 줄로 내고, `--install` 의 종료코드가
  #    그 수에서 나온다(`--check` 는 이 걸음을 안 돈다). 저장소를 안 드는 갈래는 진단에 안 가므로 `GDOWN` 이 같은 몫을 든다.
  #    ⚠ uv 의 자리를 못 읽은 링크(`uv_link` 의 2)는 「uv 것이 아니다」로 안 보고 다시 세우는 쪽으로 간다 — 모르는 것을 둘
  #      쪽으로 읽으면 틀린 판이 소리 없이 남는다.
  if [ -n "$DO_GLOBAL" ] && [ "$OS" = linux ]; then
    _gpv=''; _gpn=''
    for _rpn in $(decl_sections "$GCONF"); do
      [ "$(decl_get "$GCONF" "$_rpn" probe)" = python-version ] || continue
      _gpv="$(decl_get "$GCONF" "$_rpn" probe-target)"; _gpn="$_rpn"
    done
    _gl3="$HOME/.local/bin/python3"
    if [ "$(ver_num "$_gpv")" -eq 0 ]; then
      echo "  · python3 — 전역 선언에 판 일치 절(probe = python-version)이 없어 세션의 python3 를 안 맞춘다"
    elif { [ -e "$_gl3" ] || [ -L "$_gl3" ]; } && { _ul=0; uv_link "$_gl3" || _ul=$?; [ "$_ul" -eq 1 ]; }; then
      printf '  · %s — %s 가 uv 의 링크가 아니라(저장소 venv 감싸개 등) 기계 파이썬을 안 건드린다 · 그 자리는 지금 %s\n' \
        "$_gpn" "$_gl3" "$("$_gl3" -V 2>&1 | tail -1)"
    else
      _gt0=$SECONDS
      _gpc=python3; { [ -e "$_gl3" ] || [ -L "$_gl3" ]; } && _gpc="$_gl3"
      if [ "$(py_num "$_gpc")" = "$(ver_num "$_gpv")" ]; then
        printf '  ✅ %s — 세션의 python3 가 선언한 판(%s)이다 (전역) (%s초)\n' "$_gpn" "$_gpv" "$((SECONDS - _gt0))"
      else
        _savefails="$FAILS"; FAILS="$GFAILS"; TRY_LAST=''
        if ! command -v uv >/dev/null 2>&1; then
          nogo "$_gpn" "uv 가 없어 python3 를 $_gpv 로 못 세운다 — 전역 선언의 [uv] 가 서야 한다" || true
        elif uv_fresh && try "$_gpn" uv python install "$_gpv" --default; then
          _gpc=python3; { [ -e "$_gl3" ] || [ -L "$_gl3" ]; } && _gpc="$_gl3"
          [ "$(py_num "$_gpc")" = "$(ver_num "$_gpv")" ] ||
            nogo "$_gpn" "uv 가 0 으로 끝났는데 세션의 python3 가 그 판이 아니다 — uv 끝 줄: ${TRY_LAST:-없음}" || true
        fi
        FAILS="$_savefails"
        _gpw="$(awk -F'\t' -v k="$_gpn" '$1==k{print $2; exit}' "$GFAILS" 2>/dev/null)"
        if [ -z "$_gpw" ]; then
          printf '  ✅ %s — 세션의 python3 를 선언한 판(%s)으로 세웠다 (전역) (%s초)\n' "$_gpn" "$_gpv" "$((SECONDS - _gt0))"
        else
          PY3_WHY="선언한 판($_gpv)이 아니다 · 지금 $("$_gpc" -V 2>&1 | tail -1) · 설치 실패: $_gpw"
          printf '  ❌ %s — 세션의 python3 가 %s (%s초)\n' "$_gpn" "$PY3_WHY" "$((SECONDS - _gt0))"
          GDOWN=$((GDOWN + 1))
        fi
      fi
    fi
  fi

  # ── 저장소 배선 — 깔지 않는다. 잇기만 한다 ────────────────────────
  #    전역 설치는 저장소 `node_modules` 밖이라 import 가 못 찾는다 — 그 한 칸을 잇는 것이 저장소의 몫이다. 도구가 닿나는
  #    진단 단계가 도구마다 한 번 든다 — 잇는 걸음이 정션을 걸려고 이미 물어 닿은 도구는 진단이 그 답을 인용한다
  #    (`repo_verified`). 잇는 일 밖의 프로브는 여기 안 둔다 — 설치 앞에서 한 번, 진단에서 또 한 번 물으면 저장소마다 두
  #    벌이고, 판정 문구의 진본은 진단 단계 한 자리다.
  if [ -n "$DO_REPO" ]; then
    _wt0=$SECONDS
    for _conf in "$GCONF" "$PCONF"; do
      for _name in $(decl_sections "$_conf"); do
        wire_tool "$_conf" "$_name"
      done
    done
    printf '  · 배선 — 전역 도구를 저장소 node_modules 에 잇는다 (%s초)\n' "$((SECONDS - _wt0))"
  fi

  # ── 로컬 main — 컨테이너가 뜬 순간의 스냅샷에 박제된 채 남는다. 원격 최신으로 맞춘다 ──
  #    main 이 지금 체크아웃돼 있으면 건드리지 않는다 — 작업 중인 브랜치일 수 있다. 저장소 몫이라 전역 갈래에는 맞출 저장소가
  #    없다. 맞추는 몸통은 `sync_main` 한 자리다 — 리눅스 auto 도 같은 것을 배경으로 부른다.
  #    ⚠ auto 에서 배경 맞추기가 이미 떴으면 건너뛴다 — auto 가 설치로 넘어온 판에 여기서 또 부르면 같은 저장소에 fetch 둘이
  #      겹쳐 참조 잠금에서 한쪽이 지고, 거짓 「못 맞췄다」가 선다.
  if [ -n "$DO_REPO" ] && [ -z "${SYNC_BG:-}" ]; then
    # 사유를 삼키지 않는다 — 여기가 조용히 지면 낡은 main 을 든 채 세션이 돈다. 당김과 같은 자(`git_why`)로 낸다.
    if ! _fe="$(sync_main "$PROJECT_DIR")"; then
      echo "$PROJECT_NAME: ⚠ 로컬 main 을 원격에 못 맞췄다 — $(git_why "$_fe"). 스냅샷 시점의 낡은 main 이 그대로 남는다."
    fi
  fi

  # ── 선언 지문 굳히기 — PC 세션(auto)의 「깔 것이 있나」가 이 값과 대조된다 ──
  #    실패가 남아도 굳는다 — 안 굳히면 막힌 망에서 매 세션 재설치가 돈다. 남은 실패는 auto 갈래가 매 세션 한 줄로 알려
  #    부재가 통과로 안 읽힌다.
  #    ⚠ 돈 층만 굳힌다 — 전역만 돈 갈래가 저장소 지문까지 찍으면 저장소가 깔린 적 없는데 「깔 것이 없다」가 되어, 그 침묵이
  #      무작동을 성공으로 보이게 한다.
  [ -n "$DO_REPO" ] && { decl_fingerprint > "$STAMP" 2>/dev/null || true; }
  if [ -n "$DO_GLOBAL" ]; then
    mkdir -p "$(dirname "$GSTAMP")" 2>/dev/null || true
    global_fingerprint > "$GSTAMP" 2>/dev/null
    # ⚠ 종료코드로 안 가른다 — 이 함수는 pipefail 아래서 지문을 다 내고도 1 을 낸다(마지막 선언 파일이 줄바꿈으로 끝나면
    #   꼬리 검사가 거짓이다). 적혔나를 파일로 본다 — 폴더 자리면 `-f` 가 거짓이다.
    { [ -f "$GSTAMP" ] && [ -s "$GSTAMP" ]; } || PC_WIDE_FAIL=1
  fi
  # 미룬 PC 전체 일의 표식 — 전역 지문이 굳은 지금이 「맞췄다」가 참인 자리다. 못 굳혔으면 판을 안 적는다.
  [ -n "$PW_DEFER" ] && pc_wide_mark
  # ⚠ 낡음 표식은 민 뒤에만 찍는다 — 선언이 바뀌어 깐 세션은 밀기가 아니라, 찍으면 낡음 시계가 공짜로 되감겨 선언을 자주
  #   고치는 기계는 영영 안 밀린다.
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
}

# ── 세션(auto)의 설치는 배경에서 돈다 — 세션 시작은 설치를 안 기다린다. 늘 0 · 기록은 `INSTALL_BG_LOG` ──────────────
#    확장은 초기화를 60초만 기다리는데 설치 걸음은 망을 타는 명령이 여럿이라(태그 읽기 · 자산 받기 · pip · npm · winget ·
#    브라우저) 막힌 망에서 그 기다림이 호출 수만큼 더해진다. 호출마다 기다림을 줄여서는 합이 안 묶인다 — 걸음을 창 밖으로
#    뺀다. 이 세션에는 새 도구가 늦게 서고, 진 사유는 실패 기록(`install-fail` · `install-global-fail`)에 남아 다음 세션이
#    말한다.
#    자물쇠 하나로 한 번에 하나만 돈다 — 한 세션에 훅이 둘(저장소 설정 · 홈 훅) 불리고, 배경 설치가 도는 사이 새 세션이
#    떠도 지문은 아직 어긋나 있다. 둘이 같은 자리에 `npm ci` 를 겹치면 서로 깨뜨린다. 자물쇠는 저장소의 기계 상태
#    자리(`install-*`)에 산다 — 전역형 도구는 PC 전체 일을 맡는 세션에서만 깔리므로 그 저장소의 자물쇠가 곧 기계의 자물쇠다.
#    죽은 자물쇠는 말하고 걷는다 — 적힌 프로세스가 없으면 지난 배경 설치가 끝을 못 본 것이다(창을 닫아 함께 죽었다 등).
#    지문을 못 굳혔으니 이번에 다시 띄우고, 그 사실과 기록의 끝줄을 낸다 — 안 내면 「매 세션 다시 띄우는데 매번 못
#    끝낸다」가 아무 데도 안 보인다.
#    ⚠ stdin · stdout · stderr 를 다 뗀다 — 하나라도 훅의 파이프를 물면 Claude Code 가 그 자식을 기다려 배경으로 뺀 뜻이
#      없어진다(`pull_ff` 와 같은 결).
install_bg() {
  if ! ( set -C; printf '%s\n' "$$" > "$INSTALL_BG_LOCK" ) 2>/dev/null; then
    _bp="$(cat "$INSTALL_BG_LOCK" 2>/dev/null)"
    if [ -n "$_bp" ] && kill -0 "$_bp" 2>/dev/null; then
      echo "$PROJECT_NAME: 다른 세션이 배경에서 도구를 맞추고 있다 — 이번엔 안 띄운다 · 결과는 다음 세션이 말한다"
      return 0
    fi
    echo "$PROJECT_NAME: ⚠ 지난 배경 설치가 끝을 못 봤다 — 다시 띄운다 · 기록 끝줄: $(grep -v '^[[:space:]]*$' "$INSTALL_BG_LOG" 2>/dev/null | tail -1 | cut -c1-160)"
    rm -f "$INSTALL_BG_LOCK"
    ( set -C; printf '%s\n' "$$" > "$INSTALL_BG_LOCK" ) 2>/dev/null || {
      echo "$PROJECT_NAME: 다른 세션이 방금 배경 설치를 띄웠다 — 이번엔 안 띄운다"; return 0; }
  fi
  # ⚠ 자물쇠의 주인은 배경 프로세스가 스스로 적는다 — 부모가 `$!` 로 적으면, 곧 끝난 자식이 자물쇠를
  #   걷은 뒤에 부모가 죽은 번호로 다시 세워 다음 세션이 「끝을 못 봤다」로 잘못 읽는다.
  ( printf '%s\n' "$BASHPID" > "$INSTALL_BG_LOCK"
    trap 'rm -f "$INSTALL_BG_LOCK"' EXIT
    printf '── %s  %s  auto 배경 설치  %s ──\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$PROJECT_NAME" "$PROJECT_DIR"
    install_step ) >"$INSTALL_BG_LOG" 2>&1 </dev/null &
  echo "$PROJECT_NAME: 도구를 배경에서 맞춘다 ($(printf '%s' "${DO_GLOBAL:+전역형 도구 · }${DO_REPO:+이 저장소 도구 · }${UPGRADE:+새 판 견주기 · }" | sed 's/ · $//')) — 세션 시작은 안 기다린다. 이 세션에는 아직 안 선 도구가 있을 수 있고, 진 사유는 다음 세션이 말한다 · 기록 $INSTALL_BG_LOG"
}

gate() {  # gate <이름> <ok|ok-partial|held|off> <까닭> — 진단 줄 하나. off 는 꺼진 검사(`down`)로 센다
  # ok-partial 은 ✅ 이되 그 초록이 다 재지는 않은 줄이다 — 안 닿는데 안 세거나(on-demand · 못 타는 설치법)
  #   판을 못 쟀다. `down` 에는 안 들고, 저장소를 한 줄로 접을지(`gate_flush`)만 가른다.
  # held 는 안 서는데 그 실패를 다른 자리가 센다는 줄이다(전역 걸음이 이 실행에서 ❌ 로 낸 전역형 도구 · 바깥 `--install` 이 deploy
  #   뒤에 심는 홈 훅). 서지 않았으니 ✅ 가 아니라 ⚠ 로 찍고, `down` 에는 안 들며, 접지도 않는다.
  case "$2" in
    ok)         _gate_line="  ✅ $1 — $3" ;;
    ok-partial) _gate_line="  ✅ $1 — $3"; GATE_PARTIAL=$((GATE_PARTIAL + 1)) ;;
    held)       _gate_line="  ⚠ $1 — $3"; GATE_PARTIAL=$((GATE_PARTIAL + 1)) ;;
    *)          _gate_line="  ❌ $1 — $3"; down=$((down + 1)) ;;
  esac
  GATE_N=$((GATE_N + 1))
  # `--install` 만 모아 두고 끝에 낸다 — 접을지는 마지막 줄까지 봐야 갈린다. 다른 갈래는 바로 낸다.
  if [ "$MODE" = install ]; then GATE_LINES="$GATE_LINES$_gate_line$_NL"
  else printf '%s\n' "$_gate_line"; fi
}

# ── 모아 둔 진단 줄을 낸다 — `--install` 에서 다 초록이면 저장소마다 한 줄로 접는다 ──
#    `--install` 을 읽는 자는 설치 화면과 기록이고, 거기서 필요한 것은 성패와 고칠 자리다. ❌ 가 하나라도 있거나 다 재지
#    않은 초록(`ok-partial`) · 다른 자리가 세는 ⚠(`held`)가 있으면 줄을 다 낸다 — 접힌 한 줄이 그것을 가리면 다 선 저장소와
#    구별이 안 된다.
#    `--check` 는 접지 않는다 — 사람이 「어느 검사가 도나」를 물으러 온 자리이고, 배포가 진 저장소마다 그 명령을 고칠
#    자리로 건넨다(deploy.ps1). 거기서 목록을 접으면 물은 것에 답을 안 한다.
#    종료코드와 무관하다 — 판정은 `down` 하나가 들고, 여기는 줄을 어떻게 내나만 정한다.
gate_flush() {
  [ -n "$GATE_LINES" ] || return 0
  if [ "$down" -eq 0 ] && [ "$GATE_PARTIAL" -eq 0 ]; then
    printf '  ✅ 검사 %s개가 다 선다 — 줄마다 보려면 session-start.sh --check\n' "$GATE_N"
  else
    printf '%s' "$GATE_LINES"
  fi
  GATE_LINES=''
}

why() {  # why <도구> [<설치 걸음>] — 도구 이름으로 못 찾으면 그 도구를 깐 걸음의 실패를 든다
  # project-axis 도구(commitlint · markdownlint · pyyaml…)는 제 이름으로 실패를 안 남긴다 — 까는 자가 `npm ci` ·
  #   `pip install` 한 걸음이라 사유는 「노드 의존성」 · 「파이썬 의존성」으로 적힌다. 도구 이름으로만 찾으면 ❌ 줄에 사유가
  #   영영 안 붙는다. 전역 갈래의 기록도 본다 — 전역형 도구는 `--install-global` 이 기계 한 자리에 적는다. 늘 0
  #   (찾으면 「 · 설치 실패: …」 를 낸다).
  _w=""
  for _wf in "$FAILS" "$GFAILS"; do
    [ -f "$_wf" ] || continue
    [ -n "$_w" ] || _w="$(awk -F'\t' -v k="$1" '$1==k{print $2; exit}' "$_wf" 2>/dev/null)"
    [ -n "$_w" ] || [ -z "${2:-}" ] || _w="$(awk -F'\t' -v k="$2" '$1==k{print $2; exit}' "$_wf" 2>/dev/null)"
  done
  [ -n "$_w" ] && printf ' · 설치 실패: %s' "$_w"
  return 0
}

# 선언의 판이 잴 수 있는 꼴인가 — 선언만 읽는다(npm 을 안 부르므로 통과 갈래에서도 싸다).
#   범위 · 딱지는 안 잰 것이다 — 통과 옆에 그 사실이 안 찍히면 「전부 통과」가 「판까지 봤다」로 읽힌다. 초록의 폭을 검사가
#   스스로 말하게 한다(규범 [Goal-Driven Execution]).
pin_shape() {  # pin_shape <선언파일> <이름> — 안 잰 까닭 한 줄, 잴 수 있으면 빈 값
  _psi=''; _sk=''
  { IFS= read -r _psi; IFS= read -r _sk; } <<EOF
$(decl_fields "$1" "$2" install package)
EOF
  [ "$_psi" = npm-global ] || return 0
  case "$_sk" in ?*@*) ;; *) return 0 ;; esac   # 판을 안 박은 선언은 애초에 안 잰다고 적혀 있다
  _sv="${_sk##*@}"
  case "$_sv" in ''|*[!0-9.]*)
    printf '판 「%s」 는 정확한 판이 아니라 **판은 안 쟀다**(`이름@1.2.3` 꼴이어야 잰다)' "$_sv" ;;
  esac
  return 0
}

# 선언이 판을 박았는데 깔린 판이 다른가 — 「안 깔렸다」와 「판이 다르다」는 고칠 자리가 다르다. 둘 다 ❌ 로 나오는데
# 사유가 「안 닿는다」 하나면 다음 사람은 npm 이 없나부터 뒤진다(`nogo` 머리말과 같은 결).
pin_mismatch() {  # pin_mismatch <선언파일> <이름> — 어긋나면 읽을 한 줄, 아니면 빈 값
  _pmi=''; _mk=''
  { IFS= read -r _pmi; IFS= read -r _mk; } <<EOF
$(decl_fields "$1" "$2" install package)
EOF
  [ "$_pmi" = npm-global ] || return 0
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

# ── 전역 걸음이 이 실행에서 낸 판정이 있나 — 캐시가 아니라 인용이다 ─────────
#    배포 한 번(`deploy.ps1`)이 전역 걸음에서 도구마다 프로브를 이미 띄웠는데, 이어 도는 저장소들의 진단이 같은 전역형
#    도구를 저장소마다 또 띄우면 같은 실행에서 같은 명제를 저장소 수만큼 묻는다 — 전역형 도구는 기계에 하나라 답이 같다.
#    프로브를 뺀 것이 아니다 — 「깔린 것과 닿는 것은 다른 명제」는 그대로 서 있고, 그 실행이 방금 실행해서 낸 판정을
#    인용할 뿐이다. 그래서 문은 셋이고 셋이 다 열려야 한다: 표식이 서 있나(`CLAUDE_CONFIG_RUN` — 세우는 자는 `deploy.ps1`
#    하나다) · 이름과 프로브 대상이 같나(대상이 다르면 같은 이름이라도 딴 명제다) · 표식이 같나(지난 실행의 명부는 이번
#    실행의 잰 값이 아니다). 배포 밖에서는 표식이 없어 한 줄도 안 바뀐다. 읽기는 셸 안에서 끝낸다(`read` 는 내장이다) —
#    저장소마다 도구마다 도는 자리라 프로세스를 띄우면 줄이려던 값을 되돌려 놓는다.
# 명부는 둘이다 — 전역 걸음이 이 실행에서 ✅ 로 낸 도구(`GVERIFIED`)와 ❌ 로 낸 도구(`GDOWNED`).
# ⚠ 줄의 꼴(`이름 \t 프로브대상 \t 표식`)은 쓰는 자 `global_run_put` 과 읽는 자 `global_run_has` 한 벌만 안다 — 한쪽만 고치면
#   인용이 조용히 끊긴다. 표식이 없으면 쓰지도 읽지도 않는다.
global_run_put() {  # global_run_put <명부> <이름> <probe-target>
  [ -n "${CLAUDE_CONFIG_RUN:-}" ] || return 0
  printf '%s\t%s\t%s\n' "$2" "$3" "$CLAUDE_CONFIG_RUN" >> "$1" 2>/dev/null || true
  return 0
}
global_run_has() {  # global_run_has <명부> <이름> <probe-target> — 통째로 견줘 셋 중 하나만 달라도 안 문다
  [ -n "${CLAUDE_CONFIG_RUN:-}" ] || return 1
  [ -f "$1" ] || return 1
  _vq="$(printf '%s\t%s\t%s' "$2" "$3" "$CLAUDE_CONFIG_RUN")"
  while IFS= read -r _vl; do
    [ "$_vl" = "$_vq" ] && return 0
  done < "$1"
  return 1
}
global_verified() {  # global_verified <선언파일> <이름> <probe-target>
  [ -n "${CLAUDE_CONFIG_RUN:-}" ] || return 1
  [ -f "$GVERIFIED" ] || return 1
  _gvi=''; _gvk=''
  { IFS= read -r _gvi; IFS= read -r _gvk; } <<EOF
$(decl_fields "$1" "$2" install probe)
EOF
  global_kind "$_gvi" || return 1
  # ⚠ `node-resolvable` 은 인용이 못 선다 — 프로브 둘이 딴 명제를 잰다. 전역 걸음의 `probe_global` 은 `npm root -g` 에
  #   대고 「기계에 있나」를 묻고, 저장소의 `probe_reach` 는 이 저장소 안에서 「정션을 타고 이름이 풀리나」를 묻는다. 기계에
  #   있어도 저장소 배선이 지면 후자는 져야 하는데, 전자를 인용하면 그 ❌(「깔렸는데 프로브가 못 찾는다: 배선이 끊겼다」)가
  #   통째로 사라진다. 인용은 같은 명제를 대신할 때만 선다 — 기계에 대고 묻는 갈래(PATH 실행형)만 남기고 이 갈래는
  #   저장소마다 잰다.
  [ "$_gvk" = node-resolvable ] && return 1
  global_run_has "$GVERIFIED" "$2" "$3"
}

# ── 설치 걸음이 이 프로세스에서 「이 저장소에서 닿나」를 이미 물었나 — 저장소 도구의 인용 ──
#    배선 걸음(`wire_tool`)은 정션을 걸기 앞뒤로 `node-resolvable` 을 이 저장소에서 묻는다 — 진단의 `probe_reach` 와 같은
#    명령이다. 그 답이 참이었으면 진단은 닿나를 다시 안 묻고 이 기록을 인용한다.
#    기록은 파일이 아니라 이 셸의 변수다 — 설치 걸음과 진단이 한 프로세스에서 돌아(`--install`) 다른 실행에서 올 길이 없다.
#    처음 값은 「해석기와 처음 값」 단계가 비운다 — 환경에서 같은 이름이 들어와도 인용이 안 선다. `--check` 는 설치 걸음을
#    안 돌아 기록이 늘 비고, 그래서 늘 묻는다.
#    ⚠ 참만 적는다 — 거짓을 적으면 진단이 안 선 도구를 「확인했다」로 읽는다.
#    선언 파일 · 이름 · 프로브 갈래 · 대상을 다 견준다 — 배선 걸음은 선언의 프로브 갈래와 무관하게 `node-resolvable` 을
#    묻는다. 선언이 딴 갈래면 딴 명제라 인용이 안 선다(같은 이름이 두 선언에서 딴 갈래로 서는 저장소도 있다). 판은 인용하지
#    않는다 — 배선 걸음은 닿나만 물었고, 판(`probe_pin`)은 진단이 묻는다.
repo_verified_put() {  # repo_verified_put <선언파일> <이름> <probe> <probe-target>
  REPO_VERIFIED="$REPO_VERIFIED$1$_TAB$2$_TAB$3$_TAB$4$_NL"
}
repo_verified() {  # repo_verified <선언파일> <이름> <probe> <probe-target> — 0 이면 인용한다
  # 줄째로 견준다 — 줄 앞뒤에 줄바꿈을 붙여, 긴 줄의 꼬리가 짧은 줄로 읽히지 않게 한다.
  case "$_NL$REPO_VERIFIED" in
    *"$_NL$1$_TAB$2$_TAB$3$_TAB$4$_NL"*) return 0 ;;
  esac
  return 1
}

render_decl() {  # render_decl <선언파일> <층라벨>
  for _name in $(decl_sections "$1"); do
    # on-demand · install 도 여기서 같이 읽는다 — 같은 조회가 이미 그 절을 읽고 있어 키 한 칸을 더 받는 값이 0 이다.
    #   아래서 따로 물으면 프로세스 하나가 도구마다 더 뜬다.
    _probe=''; _target=''; _by=''; _ondemand=''; _inst=''
    {
      IFS= read -r _probe
      IFS= read -r _target
      IFS= read -r _by
      IFS= read -r _ondemand
      IFS= read -r _inst
    } <<EOF
$(decl_fields "$1" "$_name" probe probe-target called-by on-demand install)
EOF
    # 판 일치 갈래는 저장소 venv 를 잰다 — venv 가 안 서는 저장소(`requirements.txt` 없음)에는 잴 것이 없어 안 그린다.
    #   전역 선언의 것은 저장소 선언이 같은 갈래를 두면 그쪽이 venv 의 판을 정하므로(「파이썬 축」) 안 그린다 — 그리면
    #   저장소 판으로 선 venv 를 전역 판으로 재는 헛빨강이 선다.
    if [ "$_probe" = python-version ]; then
      [ -f "$PROJECT_DIR/requirements.txt" ] || continue
      if [ "$1" = "$GCONF" ]; then
        for _rpn in $(decl_sections "$PCONF"); do
          [ "$(decl_get "$PCONF" "$_rpn" probe)" = python-version ] && continue 2
        done
      fi
    fi
    # 까는 걸음의 이름 — project-axis 도구는 이 이름으로 실패가 남는다 (why 곁주석). `try` 가
    # 적는 그 이름 그대로여야 한다 — 갈리면 사유가 또 안 붙는다.
    case "$_probe" in
      exec-npm-bin)      _step="노드 의존성" ;;
      python-importable) _step="파이썬 의존성" ;;
      *)                 _step="" ;;
    esac
    # `pin_mismatch` 는 판정 앞에서 부르지 않는다 — 그 안에서 `npm root -g` + `node` 가 도는데, 통과할 도구에도 그 쌍이
    #   돌면 세션마다 도구 수만큼 곱해진다.
    # 인용이 프로브 앞에 선다 — 이기면 프로브를 안 띄운다. 문 셋(표식 · 이름+대상 · 같은 표식)은 `global_verified` 가 들고,
    #   표식이 없는 자리에서는 첫 문에서 바로 진다. 설치 걸음이 이 프로세스에서 닿나를 이미 물었으면(`repo_verified`) 판만
    #   묻는다 — 기록이 없으면 둘 다 묻는다. 어느 쪽이든 지면 아래 갈래가 같은 줄을 낸다.
    _cited=''
    repo_verified "$1" "$_name" "$_probe" "$_target" && _cited=' — 설치 걸음이 이 실행에서 확인했다'
    if global_verified "$1" "$_name" "$_target"; then
      gate "$_name" ok "$_by ($2) — 전역 걸음이 이 실행에서 확인했다"
    elif { [ -n "$_cited" ] && probe_pin "$1" "$_name"; } ||
         { [ -z "$_cited" ] && probe_decl "$1" "$_name"; }; then
      _shape="$(pin_shape "$1" "$_name")"
      if [ -n "$_shape" ]; then gate "$_name" ok-partial "$_by ($2)$_cited — $_shape"
      else                      gate "$_name" ok "$_by ($2)$_cited"; fi
    elif _pin="$(pin_mismatch "$1" "$_name")"; [ -n "$_pin" ]; then
      gate "$_name" off "$_by ($2) — $_pin$(why "$_name" "$_step")"
    elif [ "$_probe" = node-resolvable ] && npm_root_g && [ -d "$NPM_ROOT_G/$_target" ]; then
      gate "$_name" off "$_by ($2) — 깔렸는데 프로브가 못 찾는다: 배선이 끊겼다$(why "$_name" "$_step")"
    elif [ "$_ondemand" = yes ]; then
      # 선언이 「필요할 때 깐다」로 둔 도구 — 부재가 이 저장소의 검사를 끄는 것이 아니다
      gate "$_name" ok-partial "$_by ($2) — 안 닿는다 · 필요할 때 깐다 (on-demand)"
    elif ! kind_here "$_inst"; then
      # 이 자리에서 못 타는 설치법 — 깔 손이 없으니 꺼진 검사로 안 센다(`kind_here` 곁말)
      gate "$_name" ok-partial "$_by ($2) — 안 닿는다 · 이 자리($OS)에서는 안 깐다 (설치법 $_inst)"
    elif global_kind "$_inst" && global_run_has "$GDOWNED" "$_name" "$_target"; then
      # 전역 걸음이 이 실행에서 이미 ❌ 로 내고 실패로 셌다 — 전역형 도구는 기계에 하나라 그 실패는 전역 걸음의 몫이다. 저장소마다
      #   또 세면 한 고장이 저장소 수만큼 「저장소 설치가 오류로 끝났다」가 된다.
      #   저장소의 프로브가 진 뒤에만 인용한다 — 저장소 안의 길로 서는 도구를 안 선 것으로 찍지 않는다.
      gate "$_name" held "$_by ($2) — 안 닿는다 · 전역 걸음이 이 실행에서 이미 ❌ 로 냈다 — 이 저장소의 꺼진 검사로는 안 센다$(why "$_name" "$_step")"
    else
      gate "$_name" off "$_by ($2) — 안 닿는다$(why "$_name" "$_step")"
    fi
  done
}

#endregion 라이브러리

# ══ 단계 · 당김 문 답 — pull-target 만 ════════════════════════
#    층 — 없음(묻는 갈래). 쓰는 것은 판정 한 줄(`.git/claude-pull-target.last`)뿐이다
#    하는 일 — 이미 받아 온 `<원격>/main` 을 놓고 당김이 어디서 멈출지를 세션 당김과 같은 자(`_pull_target`)로 정해, 병합할
#      커밋의 온전한 sha 한 줄을 내고 0 으로 끝난다. PowerShell 의 당김(deploy.ps1 · 부팅 라인)이 fetch 뒤 · merge 앞에서
#      부른다 — 손에 묻고 답을 재고 판정을 적는 규칙이 여기 한 벌이라, 같은 원격을 당기는 자리가 다 같은 커밋에서 선다
#    앞에서 받는 것 — 부름의 `PT_REPO` · `PT_REMOTE`
#    안 하는 것 — fetch · merge(부른 쪽이 한다) · 준비 단계부터의 모든 것(상태 파일 · 파이썬 · 알림 줄)
#    ⚠ 준비 단계 앞에 선다 — 준비 단계는 stdout 에 알림 줄을 낼 수 있는데, 부른 쪽은 stdout 을 통째로 병합할 커밋으로 읽는다.
#    못 답하면(저장소 · `<원격>/main` 을 못 읽는다) 까닭을 stderr 한 줄로 내고 2 다 — 부른 쪽은 그때 원격 끝으로 간다.
#    빈 저장소 인자는 여기서 막는다 — `git -C ""` 는 지금 폴더를 저장소로 읽는다.
if [ "$MODE" = pull-target ]; then
  if [ -z "$PT_REPO" ] || [ -z "$PT_REMOTE" ] ||
     ! _ptg="$(git -C "$PT_REPO" rev-parse --absolute-git-dir 2>/dev/null)"; then
    printf '세션 훅: --pull-target — 저장소 「%s」 를 못 읽는다(원격 「%s」) — 아무것도 안 하고 끝낸다\n' "$PT_REPO" "$PT_REMOTE" >&2
    exit 2
  fi
  _pto="$(_pull_target "$PT_REPO" "$PT_REMOTE" "$_ptg")"
  # 원격 끝을 못 읽은 판은 sha 가 아니라 `<원격>/main` 이름이 온다(`_pull_target` 머리말)
  case "$_pto" in
    ''|*[!0-9a-f]*) printf '세션 훅: --pull-target — %s 에서 %s/main 을 못 읽는다(fetch 뒤에 부른다)\n' "$PT_REPO" "$PT_REMOTE" >&2
                    exit 2 ;;
  esac
  printf '%s\n' "$_pto"
  exit 0
fi

# ══ 단계 · 준비 — 모든 갈래 ════════════════════════
#    층 — 없음(준비). 뒤 단계가 읽을 자리와 값을 세운다
#    하는 일 — 기계 상태 파일 자리(`install-*`)를 세우고 옛 이름(`bootstrap-*`)을 옮긴다. 선언이 하나도 없으면 한 줄
#      알린다. 형제가 서는 자리(`SIBLING_BASE`) · 설정 저장소 자리(`CONFIG_ROOT` — 저장소의 경로 스크립트를 먼저
#      읽는다) · 이 실행이 PC 전체 일을 맡나(`PC_WIDE`) · 기계(`OS` · `PY_CMD` · `VENV_BIN`)를 정한다
#    앞에서 받는 것 — 부름의 `MODE` · `PROJECT_DIR` · `PROJECT_NAME`
#    안 하는 것 — 깔기 · 홈 밀기 · 망. 쓰는 것은 옛 상태 파일의 이름 옮기기뿐이다
VENV="$PROJECT_DIR/.venv"
FAILS="$PROJECT_DIR/.claude/install-fail"
# 전역 갈래의 실패는 기계 한 자리에 적는다 — 저장소 파일에 적으면 그 저장소를 여는 세션만 사유를 보고, 같은 도구가
# 꺼진 형제의 진단에는 ❌ 만 서고 까닭이 영영 안 붙는다.
GFAILS="$HOME/.claude/install-global-fail"
GCONF="$PROJECT_DIR/.claude/tools.global.conf"
PCONF="$PROJECT_DIR/.claude/tools.conf"
STAMP="$PROJECT_DIR/.claude/install-stamp"   # 기계 상태 — install-fail 과 같은 자리, 커밋 안 한다
GSTAMP="$HOME/.claude/install-global-stamp"  # 전역형 선언의 지문 — 저장소가 아니라 기계 하나다
# 전역 걸음이 이번 실행에서 ✅ 로 낸 도구들의 명부. 쓰는 자는 `install_global`, 읽는 자는 진단의 `global_verified` —
# 둘 다 이 한 자리를 가리킨다.
GVERIFIED="$HOME/.claude/install-global-verified"
# 같은 실행에서 ❌ 로 낸 도구들의 명부. 쓰는 자는 `install_global`, 읽는 자는 진단의 `render_decl` 이다.
GDOWNED="$HOME/.claude/install-global-down"
FRESH="$PROJECT_DIR/.claude/install-upgraded"  # 마지막으로 도구의 새 판을 견준 날. 같은 자리, 커밋 안 한다
UPGRADE_DAYS=7                                   # 그 뒤로 이만큼 지나면 한 번 견주고 새 판만 받는다

# ── 옛 이름에서 옮긴다 — 상태 파일의 옛 이름 `bootstrap-*` 를 `install-*` 로 ─────────────────────────────────────────────
#    이름만 갈면 이미 깐 기계의 도장이 통째로 사라져 저장소마다 한 번씩 다시 깐다 — 그래서 옛 이름이 있고 새 이름이 없을
#    때만 옮긴다(`[ -e ]` 는 내장이라 스폰이 없고, `mv` 는 옛 파일을 든 기계에서 한 번만 돈다). 새 이름이 이미 서 있으면
#    안 덮는다 — 지금 값이 옛 값보다 새 것이다.
#    걷는 조건 — 옛 이름이 어느 기계에도 안 남았다고 사람이 판정하는 날 이 칸을 통째로 지운다(모든 기계가 이 줄을
#    밟았는지는 여기서 알 길이 없다).
_migrate_name "$PROJECT_DIR/.claude/bootstrap-fail"          "$FAILS"
_migrate_name "$PROJECT_DIR/.claude/bootstrap-stamp"         "$STAMP"
_migrate_name "$PROJECT_DIR/.claude/bootstrap-upgraded"      "$FRESH"
_migrate_name "$HOME/.claude/bootstrap-global-fail"          "$GFAILS"
_migrate_name "$HOME/.claude/bootstrap-global-stamp"         "$GSTAMP"
unset -f _migrate_name

# 선언이 하나도 없으면 깔 것을 못 찾은 것이다 — 빈 지문은 「선언이 없다」와 「자리를 잘못 봤다」를 구별하지 못해 엉뚱한
#   자리에서도 완료 도장이 찍힌다. 막지는 않고 자리를 말하고 간다(선언 없는 저장소도 정당하다).
#   `--needs-install` 은 이 줄을 안 낸다 — 그 갈래의 답은 기계가 읽는 한 줄이라 다른 줄이 섞이면 사유가 밀린다(이 말이
#   필요한 사람은 세션 · 설치 화면에서 듣는다). `--plant` 도 안 낸다 — 저장소를 깔러 온 갈래가 아니다.
[ "$MODE" = needs-install ] || [ "$MODE" = plant ] ||
[ -e "$PROJECT_DIR/requirements.txt" ] || [ -e "$PROJECT_DIR/package-lock.json" ] ||
[ -e "$GCONF" ] || [ -e "$PCONF" ] ||
  echo "$PROJECT_NAME: ⚠ 선언이 하나도 없다(requirements.txt · package-lock.json · tools*.conf) — $PROJECT_DIR 를 저장소로 보고 있다. 자리가 맞나 본다."

# 형제가 서는 자리 — 이 저장소 본 작업 폴더의 부모(`main_worktree`). 아래 설정 저장소 후보 · 작업 루트(`home_hook_root`) ·
# 리눅스의 붙은 저장소 훑기가 다 이 값을 읽는다 — git 은 한 번만 띄운다.
SIBLING_BASE="$(dirname "$(main_worktree "$PROJECT_DIR")")"
# claude-config 가 어디 붙었나 — 커밋 게이트와 같은 자리(.githooks 의 경로 스크립트)를 본다.
# 그 스크립트가 없거나 못 찾은 저장소(작업 트리를 모르는 옛 배포본 포함)는 아래서 직접 짚는다.
CONFIG_ROOT=""; ADR_GEN=""; GATES_HOME=""
[ -f "$PROJECT_DIR/.githooks/claude-config-path.sh" ] &&
  . "$PROJECT_DIR/.githooks/claude-config-path.sh"
if [ -z "$CONFIG_ROOT" ]; then
  for _c in "$PROJECT_DIR" "$SIBLING_BASE/claude-config" "$HOME/claude-config" /workspace/claude-config; do
    [ -f "$_c/deploy.ps1" ] && [ -d "$_c/memory" ] && { CONFIG_ROOT="$_c"; break; }
  done
fi

# ── 이 실행이 PC 전체 일을 맡나 ─────────────────────────────
#    PC 전체 일 — 홈에 규범 · 룰 · 에이전트 · 스킬 · Claude 훅 등록 · 씨앗 밀기 · 개인 설정(git 전역 설정 · 키) · 홈 훅과
#    신뢰 목록 심기 · 전역 도구 선언 대조. 저장소가 몇이든 PC 에 한 번이면 되는 일이다.
#    맡는 자리는 넷이다 — 로그인 자동 실행(`deploy.ps1` → `--install`) · 설정 저장소를 연 세션 · 저장소 밖에서 연 세션(홈
#    훅이 설정 저장소 훅을 부른다) · 리모트 설정 스크립트(`--install`). 형제 저장소를 연 세션(auto)은 안 맡는다 — 그 저장소
#    일만 하고, 맡는 자리가 오래 안 돌았거나 홈 파일이 설정 저장소와 다르면 알리기만 한다(`pc_wide_notice`).
#    명시한 `--install` 은 어느 저장소에서 불려도 맡는다 — 위 넷 가운데 셋이 그 입구로 들어온다. 하나만 빠진다 — 바깥
#    `--install` 이 부른 deploy.ps1 의 저장소 고리 안(아래 둘째 문).
#    ⚠ claude-config 가 이 PC 에 없으면 형제 세션도 맡는다 — 동료 PC(설치기만 쓰고 설정 저장소가 없는 자리)에는 위 넷
#      가운데 서는 자리가 없어(설치기는 설정 저장소가 없으면 이 몸통을 안 부르고, 설정 저장소 세션도 없다), 형제 세션까지
#      빠지면 전역 도구(게이트가 쓰는 lint 들)를 아무도 안 깐다.
PC_WIDE=""
if [ "$MODE" != auto ] || [ -z "$CONFIG_ROOT" ] || [ "$CONFIG_ROOT" = "$PROJECT_DIR" ]; then
  PC_WIDE=1
fi
# deploy.ps1 의 저장소 고리 안이고 그 deploy.ps1 을 바깥 `--install` 이 불렀으면 안 맡는다 — 바깥이 deploy 앞에서 개인 칸을,
#   뒤에서 심기와 표식을 한 번 하고, deploy 가 제 걸음으로 도구 홈 · 씨앗을 한 번 민다. 고리 안의 저장소마다 다시 하면 같은
#   일이 저장소 수만큼 돈다. 둘째 표식(`CLAUDE_CONFIG_PC_WIDE_HELD`)은 바깥이 deploy.ps1 을 부르는 그 한 줄에만 세운다.
#   사람이 deploy.ps1 을 바로 돌린 판은 고리 표식(`CLAUDE_CONFIG_DEPLOYING`)만 서서 저장소마다 맡는다 — 그 판에는 심기 ·
#   개인 칸 · 표식을 할 바깥이 없다. 이 판이면 `PC_WIDE_HELD` 가 서고, 진단의 홈 훅 축이 그것을 읽는다.
PC_WIDE_HELD=""
if [ "$ASKED" = install ] && [ -n "${CLAUDE_CONFIG_DEPLOYING:-}" ] && [ -n "${CLAUDE_CONFIG_PC_WIDE_HELD:-}" ]; then
  PC_WIDE=""; PC_WIDE_HELD=1
fi
# PC 전체 일이 마지막으로 돈 때 — 파일의 시각이 곧 값이고, 내용은 그때 맞춘 설정 저장소의 판이다.
# 쓰는 몸통은 `pc_wide_mark` 한 자리(부르는 자리는 PC 전체 일을 끝내는 곳마다)이고, 시각과 내용을 `pc_wide_key` 가
# 읽는다 — 시각이 `UPGRADE_DAYS` 를 넘으면 통째로 다시 돈다.
PC_WIDE_STAMP="$HOME/.claude/pc-wide-ran"
# 맡는 자리가 열쇠를 견줘 할 일이 없다고 본 때 — 빈 파일이고 시각만 값이다. 건너뛴 세션은 위 표식을
# 안 건드리므로, 「맡는 자리가 돌고 있나」를 묻는 `pc_wide_notice` 는 두 시각 가운데 새것을 본다.
# ⚠ 한 파일에 두 뜻을 싣지 않는다 — 건너뛸 때 위 표식의 시각을 찍으면 통째로 다시 도는 안전망이 영영 안 선다.
PC_WIDE_SEEN="$HOME/.claude/pc-wide-seen"

# 기계를 가른다. Git Bash 는 `uname -s` 가 MINGW64_NT-… 를 낸다.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) OS=windows ;;
  *)                    OS=linux   ;;
esac
# ⚠ 파이썬의 stdio · open() 인코딩을 기계의 로케일에 안 맡긴다(PEP 540). 이 몸통이 띄우는 파이썬(홈 설정 병합 · 홈 훅 ·
#   신뢰 심기 · 심겼나 재기 · 고른 제품 묻기)은 한국어 문구를 파이프로 내는데, 윈도우의 기본 인코딩(cp949)은 `—` 를 못
#   담아 다 쓰고 나서 찍다가 죽는다. deploy 가 심는 사용자 환경변수(PYTHONUTF8)는 비영속 VDI 의 첫 로그인과 리모트에는
#   없다 — 훅이 어디서 돌든 이 한 줄이 덮는다.
export PYTHONUTF8=1
# `GRB_HOME` — 릴리스 바이너리(github-release-binary)를 훅이 놓는 자리. 놓는 자(`install_tool`)와 제 사본을 비키는 자
#   (`install_global`)가 이 한 값을 본다. 환경에 서 있으면 그 값이 이긴다 — 검사가 시스템 폴더 대신 임시 폴더를 가리키는
#   자리다.
# `GRB_FOREIGN_ROOTS` — 다른 손이 릴리스 바이너리를 놓는 자리(`%LOCALAPPDATA%` 밑) — 설치기의 winget 하나다. 리눅스는
#   비어 그 가름이 없다(`grb_foreign`).
if [ "$OS" = windows ]; then
  VENV_BIN="$VENV/Scripts"; PY_CMD=python;  GRB_HOME="${GRB_HOME:-$HOME/bin}"
  GRB_FOREIGN_ROOTS="Microsoft/WinGet/Links Microsoft/WinGet/Packages"
else
  VENV_BIN="$VENV/bin";     PY_CMD=python3; GRB_HOME="${GRB_HOME:-/usr/local/bin}"
  GRB_FOREIGN_ROOTS=""
fi

# ══ 단계 · 「깔 게 있나」 답 — needs-install 만 ════════════════════════
#    층 — 없음(묻는 갈래)
#    하는 일 — 파일만 보고 이 저장소에 깔 게 있나를 한 줄과 종료코드(0 안 깐다 · 1 깐다 · 2 못 쟀다)로 내고 끝난다.
#      묻는 자는 `deploy.ps1` 의 계획 단계다 — 필요한 답은 진단이 아니라 이 한 마디라, 도구마다 프로브를 띄우면 설치 끝의
#      진단과 같은 판정을 두 벌 낸다. 「도구가 닿나」는 안 묻는다 — 그 물음의 자리는 깐 뒤의 진단 한 벌이다.
#      판정의 진본을 새로 짓지 않는다 — 「깔 게 있다」는 세션 단계의 지문 게이트가 든 명제라 같은 자(`decl_fingerprint`)를
#      부르고, 그 위에 설치가 세우는 것 가운데 파일로 보이는 것(배선 · 파이썬 선언이 있을 때의 venv · 지난 설치가 남긴
#      실패)만 더한다
#    앞에서 받는 것 — 준비의 상태 파일 자리 · 선언 자리 · `CONFIG_ROOT`
#    안 하는 것 — 아무것도 안 쓴다(지문 도장도 안 찍는다 — 재는 갈래가 제 자국을 남기면 다음 판정이 그것을 읽는다).
#      프로브 · 망 · 파이썬을 안 띄운다(해석기 고르기는 이 단계 뒤에 선다)
#    ⚠ 2 를 0 으로 접지 않는다 — 부재가 통과로 읽히는 자리가 거기다. 사유는 stdout 한 줄이고, 위층이 그 줄을 그대로 싣는다.
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
  # 지난 실패는 설치가 제 층을 다시 돌 때만 걷힌다 — 남아 있다는 것은 마지막 설치가 졌다는 뜻이다.
  # 전역 쪽도 같이 본다: 전역형 도구가 못 깔린 저장소는 그 사유를 제 파일에 안 진다.
  for _nff in "$FAILS" "$GFAILS"; do
    [ -s "$_nff" ] || continue
    _nwho=저장소; [ "$_nff" = "$GFAILS" ] && _nwho=전역
    echo "지난 $_nwho 설치의 실패가 남아 있다 — $(awk -F'\t' '{printf "%s%s", (NR>1 ? " · " : ""), $1}' "$_nff" 2>/dev/null)"
    exit 1
  done
  echo "배선·지문 맞음"
  exit 0
fi

# ══ 단계 · 해석기와 처음 값 — needs-install 을 뺀 갈래 다 ════════════════════════
#    층 — 없음(준비)
#    하는 일 — 파이썬 이름을 한 번 불러 보고 진짜를 고른다(`py_resolve`). PC 파이썬(`PC_PY`) · venv 파이썬 · 저장소
#      npm 자리를 굳히고, 라이브러리 함수가 읽고 쓰는 전역 값의 처음 값을 세운다
#    앞에서 받는 것 — 준비의 `OS` · `PY_CMD` · `VENV_BIN` · `PROJECT_DIR`
#    안 하는 것 — 깔기 · 쓰기. 파이썬이 한 번 뜰 뿐이다
py_resolve
# PC 의 파이썬 — 전역 파이썬 패키지(`pip-user`)가 사는 자리라 여기서 굳혀 둔다.
# ⚠ `PY_CMD` 를 그대로 안 쓴다 — 「파이썬 축」이 선언한 판(`probe = python-version`)으로 venv 를 세우려고 그 이름을 다른
#   해석기로 바꿔 끼운다. 전역 패키지를 부르는 자는 저장소와 무관하게 PATH 의 파이썬으로 돈다 — 깔고 재는 자리도 그것이어야
#   명제가 같다.
PC_PY="$PY_CMD"
VENV_PY="$VENV_BIN/python"; [ -x "$VENV_PY" ] || VENV_PY="$VENV_BIN/python.exe"
NPM_BIN="$PROJECT_DIR/node_modules/.bin"

PATH_CAUGHT=''
NPM_ROOT_G=''; NPM_ROOT_G_ASKED=''
# 설치 걸음이 이 프로세스에서 닿는다고 확인한 저장소 도구 — 진단이 인용한다(`repo_verified`). 여기서 비운다:
#   환경에서 같은 이름이 들어와도 인용이 서면 안 된다.
REPO_VERIFIED=''
# 이 실행의 전역 걸음(「세션의 python3」 칸)이 세션의 python3 를 못 맞춘 까닭 — 진단이 꺼진 검사로 낸다. 여기서 비운다(위와 같은 결).
PY3_WHY=''

# GitHub 에 닿는 기다림(초) — 연결 마감 하나만 뜻한다. `gh_latest_tag` · `gh_asset_get` 이 같이 쓴다.
#   ⚠ 되풀이 창에 이 값을 겹쳐 쓰지 않는다 — 한 값이 두 뜻을 지면, 연결을 넉넉히 하려고 올린 손이 되풀이까지 조용히 바꾼다.
GH_CONNECT_S=10

HOME_SYNC=push
HOME_STALE=""
PUSH_ONLY=""

# ⚠ PC 전체 일의 입력(`PW_INPUTS`) — 개인 설정 · 심기 · 전역 도구 대조가 읽는 파일이다. 여기 없는 파일만 바뀐 판은 홈
#   밀기만 한다. 그 일이 새 파일을 읽기 시작하면 여기 더한다 — 새 입력은 대개 이 몸통을 고치는 커밋과 함께 와서 그 판은
#   다 돌지만, 그 뒤 그 파일만 바뀐 판은 여기서 갈린다.
#   바뀌면 바뀐 파일만으로는 모자라 통째로 가는 것이 둘이다(`PW_FULL_IF`) — `deploy.seeds.conf` 는 밀 폴더 목록이고, 이
#   몸통은 무엇을 어디로 미나 자체다. 몸통이 미는 칸을 넓히면 그 칸의 묵은 파일은 판 사이 diff 에 안 나오므로, 바뀐
#   파일만 보면 새 칸이 빈 채로 표식이 「맞췄다」를 적는다.
PW_INPUTS=".claude/hooks/ personal.conf secrets.env .claude/tools.global.conf .claude/tools.conf"
PW_FULL_IF="deploy.seeds.conf .claude/hooks/session-start-body.sh"
_TAB=$(printf '\t')   # 옮김 줄의 두 경로를 가르는 글자 — 글자로 박으면 편집기가 공백으로 바꿔도 모른다
_NL='
'
PW_RUN=full; PW_CHANGED=""; PW_REST=1; PW_HOMESET=1; PW_OID=""; PW_DIRTY=""; PC_WIDE_FAIL=""; PW_DEFER=""

_CR=$(printf '\r')   # 고리 밖에서 한 번 — `$'\r'` 은 sh 에 없다
_SITE=''; _SITE_FILE=''; _SITE_MODE=''; _SITE_DONE=''
PULL_TTL=90   # 초. 훅 둘(저장소·홈)이 한 세션에서 40여 초 걸러 도는 것을 한 창으로 덮는다

# ══ 단계 · 심기만 — plant 만 ════════════════════════
#    층 — 홈과 환경(홈 SessionStart 훅 · 작업 루트 우리 저장소의 폴더 신뢰 · 데스크탑 앱 목록과 권한 — `plant_session_state`)
#    하는 일 — 심기 하나를 하고 끝난다. 설정 저장소가 없는 PC 에서도 설치기가 홈 씨앗의 이 몸통으로 부른다. 작업 루트는
#      받은 값(`PLANT_ROOT` — 부름 단계가 굳혔다)이다. 홈 훅이나 Claude 신뢰를 못 심었거나 심는 스크립트가 못 돌았으면
#      (`PC_WIDE_FAIL`) 1 로 끝난다(까닭은 위 줄). 다른 칸은 못 심어도 줄만 남기고 0 이다(머리말 `--plant`)
#    앞에서 받는 것 — `PLANT_ROOT` · `CONFIG_ROOT`(없어도 된다 — `plant_session_state` 머리말) · 고른 해석기
#    안 하는 것 — 깔기 · 배포 · 당김 · 커밋 훅 배선 · PC 전체 일(홈 밀기)과 그 표식 · 진단
if [ "$MODE" = plant ]; then
  SIBLING_BASE="$PLANT_ROOT"
  plant_session_state
  [ -n "$PC_WIDE_FAIL" ] && exit 1
  exit 0
fi

# ══ 단계 · 세션 — auto 만 ════════════════════════
#    층 — 저장소(커밋 훅 배선 · 저장소 제 시작 일 · 당김 · venv 를 세션 셸에 잇기) · 홈과 환경(PC 전체 일을 맡을
#      때 — 규범 · 룰 · 에이전트 · 스킬 · Claude 훅 등록 · 씨앗 밀기 · 개인 칸의 가벼운 것). 홈 훅과 신뢰 심기는 명시한 설치만 한다
#    하는 일 — 매 세션 일을 하고(리눅스는 붙은 저장소마다 당김 · main 맞추기를 배경으로 더한다), 낡음과 선언 지문(전역 ·
#      저장소)을 견준다. 깔 것이 없으면 여기서 0 으로 끝나고, 있으면 `MODE=install` · `INSTALL_BG=1` 로 설치
#      단계에 넘긴다
#    앞에서 받는 것 — 준비의 `PC_WIDE` · `CONFIG_ROOT` · 상태 파일 자리, 고른 해석기, 처음 값
#    안 하는 것 — 깔기(설치 단계가 배경에서 든다) · 진단 줄. 형제 저장소 세션은 홈에 안 쓰고 견주어 알리기만 한다
#    걸음 — 당김과 홈 밀기는 매 세션, 설치는 지문이 어긋나거나 도구가 낡았을 때만:
#      당김     원격을 ff-only 로, main 체크아웃일 때만. 로컬을 다치게 하지 않는다 — 갈라졌거나 오프라인이면 그대로 두고
#               사유까지 말한다(배경이라 다음 세션이 말한다). 저장소가 손(`pull-target.sh`)을 두면 원격 main 위의 그
#               손이 고른 커밋까지만 간다(`_pull_target`) — 손의 답을 물리쳤으면 그것도 다음 세션이 한 줄 말한다
#      홈 밀기  홈 규범 · 훅 배선을 새로 민다 — 멱등 · 싼 것이라 매 세션. PC 전체 일이라 설정 저장소 세션과 저장소 밖
#               세션만 한다(준비 단계의 PC_WIDE). 형제 저장소 세션은 게이트 배선만 하고 홈은 견주기만 해서, 맞출 것이
#               있으면 한 줄로 알린다(`pc_wide_notice`)
#      설치     설치의 무거움(npm ci)이 선언 바뀐 세션에만 든다. 그 설치도 배경에서 돌아 세션 시작을 안 잡는다(`install_bg`)
#      리눅스(리모트 컨테이너)는 하나 더 — 붙은 저장소마다 main 을 배경으로 원격에 맞춘다(`sync_main_bg` · `pull_ff`).
#    리모트도 같은 걸음이다 — 도구 · venv · 지문은 환경 이미지 시점에 실려 오고 코드만 세션마다 최신이라, 지문이 「이미지가
#    낡았나」를 가른다. 맨 컨테이너에서도 옳다: 지문 파일이 없으면 어긋남이라 그대로 설치로 간다.
if [ "$MODE" = auto ]; then
  wire_commit_hooks  # 당김 앞이다 — 망이 느리거나 훅이 잘려도 게이트만은 선다
  run_repo_start     # 당김 앞이다 — 저장소가 제 나무를 당김이 설 수 있는 꼴로 만든다
  # 열쇠는 당김 앞에서 읽는다 — 배경 병합이 작업 나무를 바꾸기 전의 판을 잡는다. 그래도 도는 사이 판이
  #   움직이면 `pc_wide_mark` 가 열쇠를 안 적는다.
  [ -n "$PC_WIDE" ] && pc_wide_key
  pull_ff "$PROJECT_DIR"
  # 리눅스(리모트 컨테이너)만 — 붙은 저장소마다 main 을 배경으로 원격에 맞춘다. main 이 아닌 갈래 위면 참조만
  #   (`sync_main_bg`), main 위면 작업 나무까지 빨리감기로(`pull_ff`) 옮긴다.
  # ⚠ `OS=linux` 가 아니라 `uname` 으로 가른다 — 저 값은 윈도우가 아닌 모든 것(맥 포함)을 받는 칸이다.
  # main 위 형제의 작업 나무를 옮기는 것은 뜻한 것이다 — 설정 저장소 세션이 형제 파일을 읽어 견주는 일(형제 사본 대조 ·
  #   규격 빌려 오기)이 최신을 보게. 커밋 안 한 편집과 겹치면 git 이 거절한다. 이 세션의 저장소는 위에서 이미 당겼다(두 번
  #   부르면 경고가 두 줄이 된다).
  #   훑는 자리는 본 작업 폴더의 곁(`SIBLING_BASE`)이다 — 작업 트리 세션이면 그 작업 트리는 안 나오고, 이 저장소의
  #   본 작업 폴더가 main 위 형제와 같이 당겨진다(main 이 거기 꺼내져 있어 `sync_main_bg` 는 비켜서고 `pull_ff` 가 옮긴다).
  SYNC_BG=""
  if [ "$(uname -s)" = Linux ]; then
    SYNC_BG=1
    for _g in "$SIBLING_BASE"/*/.git; do
      [ -e "$_g" ] || continue
      _r="${_g%/.git}"
      [ "$_r" = "$PROJECT_DIR" ] || pull_ff "$_r"
      sync_main_bg "$_r"
    done
  fi
  # PC 전체 일 — 설정 저장소 세션과 저장소 밖 세션만 맡는다. 형제 저장소 세션은 설정 저장소를 당기려고 따로 걸음을 두지
  #   않는다: 당겨 온 것은 홈에 밀어야 실리는데 그 밀기를 이 세션이 안 한다. 리눅스는 위 고리가 붙은 저장소를 다 돌아 main
  #   위 설정 저장소도 당겨지지만, 홈에 미는 것은 여전히 없다.
  # 같은 판으로 이미 맞춘 홈은 다시 안 맞춘다 — 로그인 자동 실행이 방금 다 한 일을 세션마다 되풀이하지 않는다. 열쇠가 안
  #   맞으면 그 사이 바뀐 걸음만 한다.
  if [ -n "$PC_WIDE" ]; then
    if [ -n "$PW_RUN" ]; then
      PC_WIDE_FAIL=""
      [ "$PW_RUN" = part ] && PUSH_ONLY="$PW_CHANGED"
      deploy_home_norms  # 당김이 배경이라 이번엔 지난 판을 민다 — 방금 당긴 것은 다음 세션이 민다
      PUSH_ONLY=""
      [ -n "$PW_REST" ] && deploy_personal auto  # 가벼운 것만 — git 신원 · 슬러그 · 값이 바뀐 개인 키
      # 홈 훅 · 신뢰 · 데스크탑 목록은 여기서 안 심는다 — 명시한 설치만 심는다(plant_session_state 머리말)
      # 표식은 아래 지문 게이트 뒤에 적는다 — 전역 도구를 깔 판이면 그 설치가 끝나야 「맞췄다」가 참이다
    else
      # 할 일이 없다고 봤다 — 형제 세션 알림에 「맡는 자리가 돌고 있다」를 남긴다.
      # ⚠ 할 일이 있는 갈래에서는 안 찍는다 — 그 일이 도중에 죽으면 「돌고 있다」가 거짓이 된다.
      : > "$PC_WIDE_SEEN" 2>/dev/null || true
    fi
  else
    pc_wide_notice
  fi
  wire_python_path   # 지문 게이트 앞이다 — 배선은 설치의 사건이 아니라 세션의 상태다
  # ── 낡음 게이트 — 선언이 그대로여도 도구는 낡는다 ────────────────────────
  #    지문은 「선언이 바뀌었나」를 재지 「도구가 낡았나」를 안 잰다 — 선언을 안 고치는 기계(집 · 회사 PC)에서도 도구가
  #    올라가게, 마지막 견주기(`FRESH`)가 `UPGRADE_DAYS` 를 넘으면 한 번 견주고 새 판만 받는다.
  #    표식이 없으면 안 밀고 표식만 남긴다 — 컨테이너는 세션마다 새로 나서 표식이 늘 없는데, 거기서 밀면 매 세션 수십 초를
  #    문다(도구는 이미지만큼만 낡았고 이미지는 이 훅이 관리하는 것이 아니다). 영속 기계는 표식이 남아 제때 낡고, 그때 한 번 민다.
  UPGRADE=""
  if [ ! -f "$FRESH" ]; then
    : > "$FRESH" 2>/dev/null || true
  elif [ -n "$(find "$FRESH" -mtime "+$UPGRADE_DAYS" 2>/dev/null)" ]; then
    UPGRADE=1
    echo "$PROJECT_NAME: 도구의 새 판을 견준다 (마지막 견주기가 ${UPGRADE_DAYS}일을 넘었다 · 새 판이 있는 것만 받는다)"
  fi

  # ── 지문 게이트 — 둘로 갈린다. 전역형 도구는 기계 하나에 서므로 지문도 하나고, 저장소 지문이 어긋나도 전역을 다시
  #    훑을 까닭이 없다(그 반대도 같다). 낡음(UPGRADE)은 둘 다 민다 — 「도구가 낡았나」는 어느 층에도 같이 걸리는 명제다.
  DO_GLOBAL=""; DO_REPO=""
  # 전역 도구는 PC 전체 일이다 — 형제 저장소 세션은 대조조차 안 한다(형제 선언을 전부 읽는 자리라서다). 대조도 열쇠를
  #   탄다 — 같은 판으로 맞춘 홈이면 그때 이미 대조했다. 형제 저장소의 전역 선언이 바뀐 것은 이 열쇠에 안 잡히고, 로그인
  #   자동 실행의 설치가 잡는다.
  if [ -n "$PC_WIDE" ] && { [ -n "$PW_REST" ] || [ -n "$UPGRADE" ]; }; then
    { [ -z "$UPGRADE" ] && [ "$(global_fingerprint)" = "$(cat "$GSTAMP" 2>/dev/null)" ]; } || DO_GLOBAL=1
  fi
  { [ -z "$UPGRADE" ] && [ "$(decl_fingerprint)"   = "$(cat "$STAMP"  2>/dev/null)" ]; } || DO_REPO=1
  # ⚠ PC 전체 일의 표식은 여기서 적는다 — 전역 도구를 깔 판이면 미룬다. 대조가 어긋나 설치로 가는 세션이 먼저 판을 적고
  #   설치 도중 죽으면(창을 닫았다 · 느린 망에서 끊겼다), 다음 세션은 판이 맞아 대조를 아예 안 하고 새 도구가 안 깔린 채
  #   조용히 남는다. 미룬 표식은 설치 걸음이 전역 지문을 굳힌 뒤(「선언 지문 굳히기」) 적는다.
  if [ -n "$PC_WIDE" ] && [ -n "$PW_RUN" ]; then
    if [ -n "$DO_GLOBAL" ]; then PW_DEFER=1; else pc_wide_mark; fi
  fi
  if [ -z "$DO_GLOBAL" ] && [ -z "$DO_REPO" ]; then
    # 침묵하되 실패까지 삼키지는 않는다 — 지난 설치의 실패가 남아 있으면 사유까지 알린다(저장소 기록 · 기계 한 자리의
    #   전역 기록 둘 다 — 전역 쪽을 안 읽으면 전역형 도구가 못 깔린 저장소는 사유를 아무 데서도 못 본다). 다시 깔지는
    #   않는다: 막힌 자리(예: 내려받기가 막힌 망)는 다시 깔아도 또 막혀 재시도가 매 세션 비용만 된다. 다시 까는 손은
    #   deploy.ps1 · --install 이 든다.
    # ⚠ stdout 이다 — 이 줄을 stderr 로 내면 세션이 못 읽고, 실패가 남은 채 게이트 없는 커밋이 지나간다(파일 머리의 「말은
    #   stdout 으로」). 사유를 같이 찍는 까닭도 같다 — 「파일을 열어 보라」는 말은 안 열린다.
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
  # 선언이 어긋났거나 도구가 낡았다 — 배경에서 깐다(`install_bg`). 지문은 설치 걸음 끝(「선언 지문 굳히기」)에 굳는다
  MODE=install; INSTALL_BG=1
fi

# ══ 단계 · 설치 — install(명시한 갈래 · auto 에서 넘어온 판) ════════════════════════
#    층 — 기계(전역형 도구) · 저장소(venv · npm ci · 배선 · 로컬 main · 선언 지문) · 홈과 환경(PC 전체 일을 맡을 때)
#    하는 일 — auto 에서 넘어온 판은 `install_bg` 로 배경에 띄우고 0 으로 끝난다. 명시한 갈래는 `install_step` 을
#      기다린다 — PC 에서 밖이 부른 `--install` 은 개인 칸을 세우고 deploy.ps1 에 넘긴 뒤 그 종료코드로 끝나고,
#      `--install-global` 은 전역형 도구만 깔고 끝난다. 나머지(deploy.ps1 의 저장소 고리 · 리모트)는 진단으로 간다
#    앞에서 받는 것 — `ASKED` · `CLAUDE_CONFIG_DEPLOYING`, 세션 단계가 정한 `DO_GLOBAL` · `DO_REPO` · `UPGRADE` ·
#      `INSTALL_BG`
#    안 하는 것 — 저장소 도구의 ✅ · ❌ 줄(진단 단계가 낸다 — 전역형 도구 줄만 여기서 낸다)

INSTALL_BG_LOCK="$PROJECT_DIR/.claude/install-bg.lock"
INSTALL_BG_LOG="$PROJECT_DIR/.claude/install-bg.log"

if [ "$MODE" = install ]; then
  if [ -n "${INSTALL_BG:-}" ]; then
    install_bg
    _gr="$(global_rule_reason)"
    [ -n "$_gr" ] && echo "$PROJECT_NAME: ⚠ 전역 규율 — $_gr"
    exit 0
  fi
  install_step
fi

# ══ 단계 · 진단 — check · 진단까지 오는 install ════════════════════════
#    층 — 없음(재기)
#    하는 일 — 전역 규율 · 홈 훅(설정 저장소 세션만) · 커밋 훅 배선과 게이트 · 선언 도구마다 닿나를 한 줄씩 내고,
#      메모리 목차 한도를 잰다. `--install` 은 다 초록이면 그 줄들을 한 줄로 접는다(`gate_flush`)
#    앞에서 받는 것 — 설치가 남긴 실패 기록(`install-fail` · `install-global-fail`) · 전역 걸음의 확인 명부(`GVERIFIED`)와
#      ❌ 명부(`GDOWNED`) · 설치 걸음의 확인 기록(`REPO_VERIFIED`)
#    안 하는 것 — 깔기 · 심기 · 쓰기
#    판정 문구는 여기 한 자리에만 둔다. 위층이 죽으면 아래는 「실패」가 아니라 「못 잼」으로 낸다.

# ── 재기용 문(`CLAUDE_SKIP_DIAG`) — 진단 몫이 몇 초인가를 같은 조건에서 견주려면 끈 판이 있어야 한다 ──────
# ⚠ 이 문을 열면 설치의 성패 판정이 사라진다 — 판정 단계가 `--check` · `--install` 의 종료코드를 꺼진 검사 수(`down`)로
#   내는데, 진단을 안 돌면 그 수가 0 으로 남아 무엇이 꺼져 있어도 0 으로 끝난다. 그래서 재기 전용이고 기본값은 도는 쪽이다.
#   켠 판은 화면에 박는다 — 안 박으면 로그를 나중에 읽는 자리에서 그 판의 초록이 성공으로 읽힌다.
if [ -n "${CLAUDE_SKIP_DIAG:-}" ]; then
  echo "$PROJECT_NAME — ⚠ 진단을 건너뛴다 (CLAUDE_SKIP_DIAG · 재기 전용) — 이 판의 종료코드는 설치 성패를 안 가린다"
  exit 0
fi

down=0
GATE_N=0; GATE_PARTIAL=0; GATE_LINES=''   # 진단 줄의 수 · 다 재지 않은 초록 · `--install` 이 모아 둔 줄 (`gate`)

_dt0=$SECONDS   # 진단 단계가 걸린 시간 — 끝줄에 붙는다
echo "$PROJECT_NAME — 지금 어느 검사가 도나  ($OS · $MODE)"

# 전역 축 — 판정과 문구는 위 global_rule_reason 이 든다. 여기는 내는 자리일 뿐이다
_gr="$(global_rule_reason)"
[ -n "$_gr" ] && gate "전역 규율" off "$_gr"

# 홈 훅 축 — 저장소 밖에서 연 세션에 auto 를 걸 자가 서 있나
#   내는 자리는 하나다 — 홈 훅은 기계당 하나인데 그 훅이 부르면 저장소마다 이 진단이 돌아 같은 줄이 저장소 수만큼 찍힌다.
#   홈 층의 진본을 든 저장소(설정 저장소)만 낸다 — 규범 · 룰 · 에이전트가 거기서만 나가는 것과 같은 자리다. 그 저장소가
#   안 붙은 세션은 이 줄이 없는 대신 위 「전역 규율」이 선다.
# home_hook_gate <재는 자의 종료 값> <낡은 항목의 루트(줄마다)> — 재는 자(`home_hook_planted`)의 답을 진단 줄 하나로 낸다.
#   낡은 항목은 이 루트의 것(명령 글자만 옛 꼴이다 — 몸통이 명령을 바꾼 뒤 아직 설치가 안 돌았다)과 딴 루트의 것으로 갈라 댄다.
#   견주기 전에 그 루트를 `home_hook_root` 의 꼴로 굳힌다 — 굳히기 전에 심긴 `/c/…` 도 같은 루트다.
home_hook_gate() {
  _hgh="$(home_hook_root)"; _hgsame=""; _hgother=""
  while IFS= read -r _hgr; do
    [ -n "$_hgr" ] || continue
    if [ "$(SIBLING_BASE="$_hgr"; home_hook_root)" = "$_hgh" ]; then _hgsame=1; else _hgother="$_hgother $_hgr"; fi
  done <<< "$2"
  _hgother="${_hgother# }"
  case "$1" in
    0) gate "홈 훅" ok  "심겼다 — 저장소 밖(전역 층·홈)에서 연 세션도 auto 가 선다" ;;
    1) if [ -n "$_hgsame" ]; then
         gate "홈 훅" off "이 루트($_hgh)로 심긴 항목이 옛 판의 명령이다${_hgother:+ — 딴 루트에도 심겨 있다: $_hgother}. 다음 설치(설치기 · 로그온 자동 실행의 --install)가 지금 명령으로 갈아 심는다"
       elif [ -n "$_hgother" ]; then
         gate "홈 훅" off "이 루트($_hgh)로는 안 심겼다 — 딴 루트만 심겨 있다: $_hgother. 저장소를 옮겼으면 다음 설치(설치기 · 로그온 자동 실행의 --install)가 이 루트로 심는다"
       else
         gate "홈 훅" off "안 심겼다 — 저장소 밖에서 연 세션은 아무 훅도 안 건다. 다음 설치(설치기 · 로그온 자동 실행의 --install)가 심는다"
       fi ;;
    2) gate "홈 훅" off "**못 잼** — $PY_CMD 를 못 부른다(윈도우면 스토어 껍데기다). 심기도 같은 가드에서 진다" ;;
    3) gate "홈 훅" off "이 루트로는 심겼는데 **낡은 항목이 남아 있다**: $(printf '%s' "$2" | tr '\n' ' ') — 그 루트의 저장소를 세션마다 헛돈다. ~/.claude/settings.json 에서 그 항목을 지운다" ;;
  esac
}
# 바깥 `--install` 이 쥔 deploy 고리 안(`PC_WIDE_HELD`)에서는 안 심겼거나 낡은 항목이 남은 것을 꺼진 검사로 안 센다 —
#   심기는 그 바깥이 deploy.ps1 뒤에 하고, 못 심었으면 바깥의 종료 값이 센다(설치기는 이어 부르는 `--plant` 로도 센다). 세면 맨바닥 PC 에서 아직
#   안 온 심기 때문에 deploy 가 1 로 끝나고, 바깥은 PC 전체 일의 표식을 못 적는다. 못 잼(2)은 그대로 센다.
if [ -n "$CONFIG_ROOT" ] && [ "$CONFIG_ROOT" = "$PROJECT_DIR" ]; then
  _stale="$(home_hook_planted)"; _hh=$?
  if [ -n "$PC_WIDE_HELD" ] && { [ "$_hh" -eq 1 ] || [ "$_hh" -eq 3 ]; }; then
    gate "홈 훅" held "아직 안 맞다 — 이 deploy.ps1 을 부른 바깥 --install 이 끝에 심는다"
  else
    home_hook_gate "$_hh" "$_stale"
  fi
fi

# 저장소 규약 축 — .githooks/ 의 존재가 곧 선언이다
if [ -d "$PROJECT_DIR/.githooks" ]; then
  # 자리 일치로 재는 몸통은 앞머리의 `hooks_wired` 한 벌이다 — `--needs-install` 과 같은 자다.
  if hooks_wired; then
    gate "커밋 훅 배선" ok "core.hooksPath=$HOOKS_PATH"

    # 몸통을 다 본다 — 하나만 물으면 다른 몸통(`pre-commit` 등)에 실행권한이 없을 때 조각이 통째로 안 도는데 진단은 ✅ 다.
    for _b in pre-commit commit-msg pre-push; do
      [ -f "$PROJECT_DIR/.githooks/$_b" ] && [ ! -x "$PROJECT_DIR/.githooks/$_b" ] &&
        gate "커밋 게이트($_b)" off "실행권한이 없어 git 이 무시한다 — 조각이 다 멀쩡해도 안 돈다"
    done

    # 선언을 연다 — 폴더 존재와 `core.hooksPath` 만 보면 선언을 치워도 ✅ 이고, 커밋 때 러너는 「아무것도 안 잰다」고
    #   말한다. 「훅이 걸렸나」와 「무엇을 재나」는 다른 명제다. 파서를 여기 두 벌 두지 않는다 — 러너를 그대로 부른다(`gate_list`).
    # 러너는 찾는 자(`claude-config-path.sh`)가 정한 GATES_HOME(붙은 claude-config → 홈 씨앗 · 계약 표식을 든 러너만)에서
    #   찾고, 조각은 저장소 안을 먼저 보고 없으면 그 곁에서 찾는다 — 형제 저장소는 사본을 안 들어, 저장소 안만 보면 멀쩡한
    #   형제가 「조각이 없다」로 찍힌다. GATES_HOME 이 비면 러너를 못 찾았다고 낸다 — 저장소 안의 러너로 물러나지 않는다:
    #   형제에 남은 낡은 사본을 잡으면 진단이 몸통과 다른 러너를 본다.
    _gc="$PROJECT_DIR/.githooks/gates.conf"
    _gr="${GATES_HOME:+$GATES_HOME/gates-run.sh}"
    if [ ! -f "$_gc" ]; then
      gate "커밋 게이트" off "선언이 없다(.githooks/gates.conf) — 훅은 걸렸는데 **아무것도 안 잰다**"
    elif [ -z "$_gr" ]; then
      gate "커밋 게이트" off "러너를 못 찾았다 — 이 저장소 · claude-config · 홈 씨앗 어디에도 gates-run.sh 가 없다. 커밋이 **아무것도 안 재고** 지나간다"
    else
      # shellcheck source=/dev/null
      . "$_gr"
      _on=""; _gone=""
      for _stage in pre-commit commit-msg pre-push; do
        for _g in $(gate_list "$_stage" "$_gc"); do
          if [ -f "$PROJECT_DIR/.githooks/gates.d/$_g.sh" ] || [ -f "$GATES_HOME/gates.d/$_g.sh" ]; then _on="$_on $_g"
          elif command -v gate_retired >/dev/null 2>&1 && gate_retired "$_g"; then :   # 걷은 조각 — 러너도 말없이 지나간다
          else _gone="$_gone $_g"; fi
        done
      done
      if [ -n "$_gone" ]; then
        gate "커밋 게이트" off "선언에 있는데 조각을 못 찾았다:$_gone — 이 PC 의 claude-config 가 뒤처졌나 본다(선언의 오타일 수도 있다). 그 검사는 못 잰다 · 커밋은 안 막는다"
      elif [ -z "$_on" ]; then
        gate "커밋 게이트" off "선언은 있는데 켠 검사가 없다 — **아무것도 안 잰다**"
      else
        gate "커밋 게이트" ok "켜진 검사:$_on"
      fi
      # 자리가 아니라 찾는 자가 세운 값(`ADR_GEN`)으로 묻는다 — 생성기의 한 자리(`.githooks/adr-index.sh`)가 있나로 물으면
      #   그 사본을 안 든 저장소에서는 `adr-index` 를 켰는데도 한 줄도 안 난다.
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

# 선언 축 — 전역·프로젝트 두 층. 이름·뜻은 전부 선언에서 온다
render_decl "$GCONF" "전역"
render_decl "$PCONF" "프로젝트"
# 세션의 python3 — 이 실행의 전역 걸음(「세션의 python3」 칸)이 못 맞췄을 때만 선다. 그 걸음을 돈 실행만 센다(전역 걸음이 없는 실행은 안 잰다)
[ -n "$PY3_WHY" ] && gate "세션의 python3" off "$PY3_WHY"
gate_flush

if [ "$down" -gt 0 ]; then
  echo "  ── 꺼진 검사 $down 개. 위 까닭이 곧 고칠 자리다."
  echo "     리모트는 세션을 다시 열면 다시 깐다. PC 는 deploy.ps1 이나 --install 로 다시 깐다."
  echo "     같은 줄이 또 꺼지면 다시 깔지 말고 위의 「설치 실패」 사유를 본다."
fi
# ── 메모리 목차 한도 — 넘으면 세션이 뒷줄을 말없이 버린다 ─────────────────────────
#    세션은 목차(MEMORY.md)를 앞 200줄 · 25KB 까지만 싣는다. 넘었다는 신호가 없으면 잘린 채 돈다.
#    막지 않는다 — 무엇을 남길지는 의미 판단이라 consolidate-memory 스킬이 든다. 여기는 재고 부르기만 한다.
#    `wc` 는 한 번만 띄운다 — 파일마다 띄우면 세션마다 프로젝트 수만큼 곱해진다. `LC_ALL=C` 는 합계 줄
#    이름(`total`)이 로케일 따라 옮겨져 파일로 읽히지 않게 한다.
MEMORY_INDEX_MAX_LINES=200
MEMORY_INDEX_MAX_BYTES=25600
set -- "$HOME"/.claude/projects/*/memory/MEMORY.md
if [ -f "$1" ]; then
  LC_ALL=C wc -lc "$@" | while read -r _ml _mb _mi; do
    [ "$_mi" = total ] && continue
    if [ "$_ml" -gt "$MEMORY_INDEX_MAX_LINES" ] || [ "$_mb" -gt "$MEMORY_INDEX_MAX_BYTES" ]; then
      echo "  ⚠ 메모리 목차가 한도(${MEMORY_INDEX_MAX_LINES}줄 · 25KB)를 넘었다 — ${_ml}줄 · ${_mb}바이트: $_mi"
      echo "     뒷줄은 세션에 안 실린다. consolidate-memory 스킬로 정리한다(배포되는 메모리면 진본에서)."
    fi
  done
fi
printf '  ── 진단을 마쳤다 (%s초)\n' "$((SECONDS - _dt0))"

# ══ 단계 · 판정 — 진단을 지난 갈래 ════════════════════════
#    층 — 없음(마무리)
#    하는 일 — check · install 은 꺼진 검사가 있으면 1, 없으면 0 으로 끝난다
#    앞에서 받는 것 — 진단의 꺼진 검사 수(`down`)
#    안 하는 것 — 줄을 더 내지 않는다
#    가르는 것은 「깔았나」가 아니라 누가 물었나다. `auto` 는 세션 시작이라 0 이 아니면 세션 자체가 오류로 보인다 — 그래서
#    auto 는 이 단계에 오기 전에 0 으로 끝난다. `--check` 와 `--install` 은 판정을 받으러 온 자리라 꺼진 검사를 종료코드로
#    낸다 — deploy.ps1 은 종료코드만 보므로, 여기서 0 이면 설치가 목표를 못 이루고도 위층에 초록으로 보고된다. 설치의
#    목표는 「깔기를 돌았다」가 아니라 환경이 서 있다이다.
case "$MODE" in
  check|install) [ "$down" -gt 0 ] && exit 1 ;;
esac
exit 0
