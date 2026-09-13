#!/bin/bash
# 부트스트랩 — 익명 몸통 (SessionStart 훅 겸 설치기)
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
#   session-start.sh --check    안 깔고 진단만 낸다          ← 어디서 돌려도 안전
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
case "${1:-}" in
  --check)   MODE=check ;;
  --install) MODE=install ;;
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
VENV="$PROJECT_DIR/.venv"
FAILS="$PROJECT_DIR/.claude/bootstrap-fail"
GCONF="$PROJECT_DIR/.claude/tools.global.conf"
PCONF="$PROJECT_DIR/.claude/tools.conf"
STAMP="$PROJECT_DIR/.claude/bootstrap-stamp"   # 기계 상태 — bootstrap-fail 과 같은 자리, 커밋 안 한다
FRESH="$PROJECT_DIR/.claude/bootstrap-upgraded"  # 마지막으로 도구를 최신으로 민 날. 같은 자리, 커밋 안 한다
UPGRADE_DAYS=7                                   # 그 뒤로 이만큼 지나면 한 번 민다

# ⚠ 선언이 하나도 없으면 **깔 것을 못 찾은 것**이다. 빈 지문은 「선언이 없다」와 「자리를 잘못
#   봤다」를 구별하지 못해, 엉뚱한 자리에서도 완료 도장이 찍힌다 — 그 침묵이 무작동을 성공으로
#   보이게 한다. 막지는 않고 자리를 말하고 간다(선언 없는 저장소도 정당하기 때문이다).
[ -e "$PROJECT_DIR/requirements.txt" ] || [ -e "$PROJECT_DIR/package-lock.json" ] ||
[ -e "$GCONF" ] || [ -e "$PCONF" ] ||
  echo "$PROJECT_NAME: ⚠ 선언이 하나도 없다(requirements.txt · package-lock.json · tools*.conf) — $PROJECT_DIR 를 저장소로 보고 있다. 자리가 맞나 본다."

# ── 선언 지문 — 설치가 소비하는 선언 넷의 해시. 깨끗한 설치 끝에 굳고(⑧), PC 세션이
#    「깔 것이 있나」를 이 값과 대조한다(auto). 판정이 사건(풀이 있었나)이 아니라
#    상태(선언과 설치가 같은 세대인가) 위에 선다. 값은 기계 밖으로 안 나가 줄끝을 안 탄다.
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
if [ "$OS" = windows ]; then
  VENV_BIN="$VENV/Scripts"; PY_CMD=python
else
  VENV_BIN="$VENV/bin";     PY_CMD=python3
fi
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
  sed -e 's/\r$//' "$1" | awk '/^\[[^]]+\][[:space:]]*$/ { gsub(/[][]/, ""); gsub(/[[:space:]]+$/, ""); print }'
}
decl_get() {  # decl_get <파일> <절> <키>
  [ -f "$1" ] || return 0
  sed -e 's/\r$//' "$1" | awk -v sec="$2" -v key="$3" '
    /^\[/ { s = $0; gsub(/[][]/, "", s); gsub(/[[:space:]]+$/, "", s); insec = (s == sec); next }
    insec {
      line = $0; sub(/[[:space:]]*#.*$/, "", line)
      if (line ~ "^"key"[[:space:]]*=") {
        sub(/^[^=]*=[[:space:]]*/, "", line); sub(/[[:space:]]+$/, "", line)
        print line; exit
      }
    }'
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

probe_decl() {  # probe_decl <선언파일> <이름> — 선언에서 갈래·대상·인자를 읽어 잰다
  # shellcheck disable=SC2046 — probe-arg 는 낱말 분리가 의도다
  probe_tool "$(decl_get "$1" "$2" probe)" "$(decl_get "$1" "$2" probe-target)" \
    $(decl_get "$1" "$2" probe-arg) || return 1
  # ⚠ **「깔렸나」와 「선언한 판인가」는 다른 명제다.** 선언이 `이름@판` 으로 판을 박았으면
  #   여기서 그것도 잰다 — 안 재면 판을 박아도 **옛 판이 깔린 기계에서 그냥 통과하고**,
  #   선언만 정확해진 채 실물은 그대로 간다. `python-version` 갈래가 이미 같은 자를 든다.
  #   판을 안 박은 선언은 이 칸이 통째로 빠진다 — 최신을 받고 안 잰다.
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

# ── 홈 규범·룰·에이전트·씨앗·커밋 훅 배선 — 가볍고 멱등이라 설치 안(①②)만이 아니라
#    PC 매 세션(auto)에도 민다.
#    **재료는 claude-config 진본 한 자리다.** 저장소는 전역 사본을 안 진다 — 지면 그 폴더가
#    「이 저장소 것」과 「전역 것」을 겸하게 되고, 겸하면 이름으로 갈라야 하는데 그 이름이
#    PC 에서는 뜻이 없다 (claude-config 0014). 안 붙어 있을 때 조용히 넘어가지 않는 것은
#    아래 진단 절의 「전역 축」이 든다 — 규율 없이 도는 세션은 스스로 그것을 모른다.
deploy_home_norms() {
  if [ -n "$CONFIG_ROOT" ] && [ -f "$CONFIG_ROOT/.claude/CLAUDE.global.md" ]; then
    _src="$CONFIG_ROOT/.claude"
    mkdir -p "$HOME/.claude"
    cp "$_src/CLAUDE.global.md" "$HOME/.claude/CLAUDE.md" 2>/dev/null || true
    if [ -d "$_src/rules.global" ]; then
      mkdir -p "$HOME/.claude/rules"
      cp "$_src/rules.global/"*.md "$HOME/.claude/rules/" 2>/dev/null || true
    fi
    # 에이전트 — 규범·룰과 같은 통로다. PC 는 deploy.ps1 이 이미 밀었고 리모트만 비어
    # 있었다: 붙여도 안 실렸고, 안 실린 줄도 몰랐다 (#5).
    # ⚠ **진본이 루트 `agents/` 인 것이 곧 안전장치다.** `.claude/agents/` 는 제품의 로드
    #   자리라, 거기 두면 이 저장소를 붙인 세션에서 저장소 층과 홈 층에 **두 벌** 실린다 —
    #   `0014` 가 룰에서 겪은 그 고장이다. 루트는 로드 자리가 아니라 짐칸 이름도 필요 없다.
    if [ -d "$CONFIG_ROOT/agents" ]; then
      mkdir -p "$HOME/.claude/agents"
      cp "$CONFIG_ROOT/agents/"*.md "$HOME/.claude/agents/" 2>/dev/null || true
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
    # ⚠ **이미 같으면 안 민다 — 그 게이트가 이 칸을 매 세션 물 만한 값으로 만든다.**
    #   파일마다 프로세스를 띄우는 셈이라(폴더 짓기 + 복사) 윈도우에서 쉰두 자리가 2.9초다.
    #   그런데 정상 상태의 홈은 **이미 같다** — 밀 것이 없는데 매 세션 3초를 물면 그 비용이
    #   곧 이 칸을 걷어내자는 말이 된다. 폴더마다 한 벌씩 견주고 같으면 넘긴다:
    #   실측 2026-09-13 (윈도우 Git Bash · 임시 홈) — 정상 0.15초 · 한 폴더가 낡으면 0.7초 ·
    #   빈 홈 첫 돌림 2.9초. 게이트 없는 판은 세 경우가 다 2.9초였다.
    #   **이것도 배포자의 뜻이다** — deploy.ps1 은 파일마다 해시를 견주어 같으면 `= 동일` 을
    #   내고 복사 계획에서 뺀다. 여기는 그 견줌을 폴더 단위로 한 벌 할 뿐이다.
    # ⚠ 홈에만 남은 파일(이름이 바뀐 씨앗의 옛 사본)이 있으면 `diff -rq` 가 그것도 「다르다」
    #   로 세어 그 폴더는 매 세션 다시 밀린다 — 느려질 뿐 틀리지는 않는다. 산문을 읽어
    #   「홈에만 있음」 줄만 걸러내려 들지 않는다: 그 문구는 로케일이 든다.
    for _sd in seeds/gateway seeds/check posco; do
      [ -d "$CONFIG_ROOT/$_sd" ] || continue
      diff -rq -x __pycache__ "$CONFIG_ROOT/$_sd" "$HOME/.claude/$_sd" >/dev/null 2>&1 && continue
      find "$CONFIG_ROOT/$_sd" -type f 2>/dev/null | while IFS= read -r _sf; do
        case "$_sf" in */__pycache__/*) continue ;; esac
        _sr="${_sf#"$CONFIG_ROOT"/}"
        mkdir -p "$HOME/.claude/${_sr%/*}" 2>/dev/null || true
        cp "$_sf" "$HOME/.claude/$_sr" 2>/dev/null || true
      done
    done
  fi
  # 커밋 훅 배선 — .githooks/ 를 둔 저장소만. 존재가 곧 선언이다
  if [ -d "$PROJECT_DIR/.githooks" ]; then
    git -C "$PROJECT_DIR" config core.hooksPath .githooks 2>/dev/null || true
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
# ⚠ **실패는 stdout 으로 말한다.** 옛 판은 `try` 로 bootstrap-fail 에 적었는데, 그 파일은
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
  printf 'p="$CLAUDE_PROJECT_DIR"; if [ -f "$p/.claude/hooks/session-start.sh" ]; then grep -q session-start.sh "$p/.claude/settings.json" 2>/dev/null || bash "$p/.claude/hooks/session-start.sh"; else for h in "%s"/*/.claude/hooks/session-start.sh; do [ -f "$h" ] && bash "$h"; done; fi' \
    "$(home_hook_root)"
}

# ── 세션 상태를 심는다 — **한 프로세스가 둘을 다 한다** ────────────────────────
#   드는 것: ① 홈 SessionStart 훅 ② 이 저장소의 신뢰.
# ⚠ **옛 판은 프로세스를 넷 띄웠다** — 판을 묻는 `py_num` · 훅 심기 · 껍데기 판별하는 `-c ''` ·
#   신뢰 심기. 저장소마다 넷이라 형제 다섯이면 **한 세션에 스물**이었고, 윈도우에서는 프로세스
#   뜨는 값이 일 자체보다 컸다. 파이썬을 한 번만 띄우고 그 안에서 둘을 다 한다.
# ⚠ **해석기가 못 뜨는 것은 종료코드로 안다** — 윈도우의 `python3` 는 스토어로 보내는 껍데기라
#   부르면 49 로 죽는다. 그래서 존재로 묻지 않고 **불러 보고 지면** 말한다(가드를 따로 띄우지
#   않는 것이 이 합침의 요점이다).
# ⚠ **옛 항목을 지운다.** 심기는 여태 「없으면 붙인다」뿐이라, 명령 글자가 바뀌면 옛 항목이
#   남아 **옛 고리가 같이 돌았다** — 위 가드가 무효가 되는 자리다. 우리 꼴(`session-start.sh`
#   를 든 명령)만 걷고, 무엇을 걷었는지 화면에 댄다.
plant_session_state() {
  _pss="$("$PY_CMD" - "$HOME/.claude/settings.json" "$(home_hook_cmd)" "$PROJECT_DIR" "$(home_hook_root)" <<'PSSEOF' 2>/dev/null
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
  if [ $? -ne 0 ]; then
    echo "$PROJECT_NAME: ⚠ 홈 SessionStart 훅·신뢰를 못 심는다 — $PY_CMD 를 못 부른다(윈도우면 스토어 껍데기다). 저장소 밖에서 연 세션은 아무 훅도 안 건다."
    return 0
  fi
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
  pull_ff() {  # pull_ff <저장소> — main 체크아웃일 때만, 빨리감기로만
    [ -e "$1/.git" ] || return 0
    [ "$(git -C "$1" symbolic-ref --short -q HEAD 2>/dev/null)" = main ] || return 0
    pull_due "$1" || return 0
    _t0="$(date +%s)"
    _pe="$(git -C "$1" pull --ff-only -q 2>&1)" ||
      echo "$(basename "$1"): ⚠ 원격 못 당김($(( $(date +%s) - _t0 ))초) — $(git_why "$_pe")"
  }
  pull_ff "$PROJECT_DIR"
  [ -n "$CONFIG_ROOT" ] && [ "$CONFIG_ROOT" != "$PROJECT_DIR" ] && pull_ff "$CONFIG_ROOT"
  deploy_home_norms
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

  if [ -z "$UPGRADE" ] && [ "$(decl_fingerprint)" = "$(cat "$STAMP" 2>/dev/null)" ]; then
    # 침묵하되 실패까지 삼키지는 않는다 — 지난 설치의 실패가 남아 있으면 **사유까지** 알린다.
    # 다시 깔지는 않는다: 막힌 자리(예: 내려받기가 막힌 망)는 다시 깔아도 또 막혀,
    # 재시도가 매 세션 비용만 된다. 다시 까는 손은 deploy.ps1·--install 이 든다.
    # ⚠ **stdout 이다.** SessionStart 훅에서 모델의 문맥에 들어가는 것은 stdout 뿐이고 stderr 는
    #   기록에만 남는다 — 종전엔 이 줄이 stderr 라 네 세션 연속 아무도 못 읽었다(실측 2026-09-05:
    #   npm ci 실패가 남은 채 commitlint 없는 커밋이 넷 지나갔다). 사유를 같이 찍는 까닭도 같다 —
    #   「파일을 열어 보라」는 말은 안 열린다.
    if [ -s "$FAILS" ]; then
      echo "$PROJECT_NAME: ⚠ 지난 설치에 실패가 남아 있다 — deploy.ps1 이나 --install 로 다시 깐다. 사유:"
      awk -F'\t' '{printf "  · %s — %s\n", $1, $2}' "$FAILS" 2>/dev/null
    fi
    _gr="$(global_rule_reason)"
    [ -n "$_gr" ] && echo "$PROJECT_NAME: ⚠ 전역 규율 — $_gr"
    exit 0
  fi
  MODE=install   # 선언이 어긋났거나 도구가 낡았다 — 이 세션에서 바로 깐다. 지문은 설치 끝(⑧)에 굳는다
fi

if [ "$MODE" = install ]; then

  # 실패는 삼키되 까닭까지 버리지는 않는다 — 진단이 ❌ 줄에 사유를 이어 붙인다.
  # 지난 실패는 **지우기 전에 찍는다** — 안 그러면 「무엇이 왜 실패했었나」가 성공한 재설치와
  # 함께 사라져 다시 못 잰다(실측 2026-09-05: --install 이 성공하며 npm ci 의 원래 사유가 증발했다).
  if [ -s "$FAILS" ]; then
    echo "$PROJECT_NAME: 지난 설치 실패 — 이번에 다시 깐다:"
    awk -F'\t' '{printf "  · %s — %s\n", $1, $2}' "$FAILS" 2>/dev/null
  fi
  mkdir -p "$(dirname "$FAILS")" 2>/dev/null; : > "$FAILS" 2>/dev/null
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

  # ── ①② 전역 규범·영역 룰·에이전트·씨앗을 홈으로 + 커밋 훅 배선 — 가볍고 안 죽는 것이
  #      맨 앞이다.
  #      몸통은 deploy_home_norms 한 벌이다 — PC 매 세션 갈래(auto)와 같은 것을 민다 ──
  deploy_home_norms

  # ── ②′ 전역 SessionStart 훅 · 신뢰 — 몸통은 위 plant_session_state 한 벌이다.
  #    auto 가 지문 게이트 앞에서 이미 부르지만, `--install` 로 곧장 들어온 갈래
  #    (deploy.ps1 · bootstrap-vdi.sh)는 그 자리를 안 지나므로 여기서도 부른다.
  #    멱등이라 겹쳐 불려도 항목은 하나다 (0028 이 쟀다).
  plant_session_state

  # ── ③ 파이썬 축 — requirements.txt 의 존재가 곧 선언이다. venv 에 깐다 ──
  if [ -f "$PROJECT_DIR/requirements.txt" ]; then
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
    # ⚠ `python -m venv` 는 트리를 만들고 해석기를 복사한 **뒤에** pip 을 깐다. 그 마지막
    #   걸음만 져도 폴더는 그대로 남아, 존재로 물으면 반쯤 선 venv 가 「있다」로 읽힌다 —
    #   그러면 **다시 깔아도 영영 안 낫는다**: 만들기를 건너뛰고, pip 이 없으니 아래 의존성
    #   칸도 조용히 지나가고, 실패는 한 줄도 안 남는다 (실측 2026-09-10 · VDI 넷이 다 그랬다).
    #   이 파일 머릿말의 「깔린 것과 닿는 것은 다른 명제다」가 정작 제 venv 가드에만 안 걸려 있었다.
    venv_ready() { [ -x "$VENV_BIN/pip" ] || [ -f "$VENV_BIN/pip.exe" ]; }
    if ! venv_ready; then
      [ -d "$VENV" ] && rm -rf "$VENV"
      # ⚠ **stdin 을 물려준다.** venv 는 pip 을 깔 때 제 안에서 파이썬을 한 번 더 띄우고, 그때
      #   부모의 표준입력 손잡이를 복제한다. 창 없이 띄워진 사슬(`CreateNoWindow`)을 타고 오면
      #   그 손잡이가 없어 `[WinError 6]` 으로 죽는다 — 설치 화면이 엔진을 그렇게 띄웠다.
      #   **부르는 자리마다 고치면 다음 런처에서 또 만난다** — 그래서 여기서 막는다.
      #   `/dev/null` 은 윈도우에서 NUL 로 서서 어느 부모 밑에서도 성한 손잡이가 된다
      #   (실측 2026-09-10: 닫힌 stdin 아래서 죽던 것이 이 한 자로 pip 까지 완주했다).
      try "venv" "$PY_CMD" -m venv "$VENV" </dev/null || true
    fi
    # 방금 만든 venv 를 프로브가 보게 한다 — VENV_PY 는 스크립트 첫머리(venv 가 아직
    # 없던 때)에 굳었다. 안 풀면 첫 회 진단이 맨 해석기를 재서 헛빨강을 낸다(실측
    # 2026-08-24: 새 venv 인데 pyyaml ❌).
    VENV_PY="$VENV_BIN/python"; [ -x "$VENV_PY" ] || VENV_PY="$VENV_BIN/python.exe"
    if venv_ready; then
      _pip="$VENV_BIN/pip"; [ -x "$_pip" ] || _pip="$VENV_BIN/pip.exe"
      try "파이썬 의존성" "$_pip" install --quiet --disable-pip-version-check \
        -r "$PROJECT_DIR/requirements.txt" || true
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
  if [ -f "$PROJECT_DIR/package-lock.json" ] && command -v npm >/dev/null 2>&1; then
    ( cd "$PROJECT_DIR" && try "노드 의존성" npm ci --no-audit --no-fund --silent ) || true
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
    try "$_t" bash "$_fbroot/$_fb" || true
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
  for _conf in "$GCONF" "$PCONF"; do
    for _name in $(decl_sections "$_conf"); do
      # ⚠ **밀 때는 프로브를 안 묻는다.** 「있나」와 「최신인가」는 다른 명제라, 있으면
      #   건너뛰는 규칙으로는 영영 안 올라간다. npm-global 은 `npm install -g` 가 최신을
      #   가져오고, github-release-binary 는 `releases/latest` 를 부르므로 **같은 설치가
      #   곧 밀기다** — 밀기용 갈래를 따로 두지 않는다.
      if [ -n "${UPGRADE:-}" ]; then
        install_tool "$_conf" "$_name" || true
      else
        probe_decl "$_conf" "$_name" || install_tool "$_conf" "$_name"
      fi
      # ⚠ **배선이 브라우저 찾기 앞에 선다.** 뒷길(`browsers-fallback`)은 「playwright 가
      #   이미 브라우저를 들고 있나」를 **그 모듈에 물어** 받을지를 가른다. 그 물음은 이름
      #   해석이나 `wiring-env` 가 먼저 서야 서는데, 뒤집혀 있던 판에서는 첫 세션마다
      #   조용히 지고 **멀쩡한 브라우저를 둔 기계가 수백 MB 를 받으러 갔다.** 둘 다 ④
      #   (`npm ci`) 뒤라 맞바꿔도 node_modules 를 밟지 않는다.
      wire_tool "$_conf" "$_name"
      browsers_ready "$_conf" "$_name"
    done
  done

  # ── ⑦ 로컬 main — 컨테이너가 뜬 순간의 스냅샷에 박제된 채 남는다. 원격 최신으로 맞춘다.
  #      main 이 지금 체크아웃돼 있으면 건드리지 않는다 — 작업 중인 브랜치일 수 있다.
  if git -C "$PROJECT_DIR" show-ref --verify --quiet refs/heads/main &&
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
  decl_fingerprint > "$STAMP" 2>/dev/null || true
  # ⚠ **민 뒤에만 찍는다.** 선언이 바뀌어 깐 세션은 밀기가 아니라, 찍으면 낡음 시계가
  #   공짜로 되감긴다 — 그러면 선언을 자주 고치는 기계는 영영 안 밀린다.
  [ -n "${UPGRADE:-}" ] && { : > "$FRESH" 2>/dev/null || true; }
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
  [ -f "$FAILS" ] || return 0
  _w="$(awk -F'\t' -v k="$1" '$1==k{print $2; exit}' "$FAILS" 2>/dev/null)"
  [ -n "$_w" ] || [ -z "${2:-}" ] || _w="$(awk -F'\t' -v k="$2" '$1==k{print $2; exit}' "$FAILS" 2>/dev/null)"
  [ -n "$_w" ] && printf ' · 설치 실패: %s' "$_w"
  return 0
}

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
  if [ "$(git -C "$PROJECT_DIR" config core.hooksPath 2>/dev/null)" = ".githooks" ]; then
    gate "커밋 훅 배선" ok "core.hooksPath=.githooks"

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
    if probe_decl "$1" "$_name"; then
      _shape="$(pin_shape "$1" "$_name")"
      if [ -n "$_shape" ]; then gate "$_name" ok "$_by ($2) — $_shape"
      else                      gate "$_name" ok "$_by ($2)"; fi
    elif _pin="$(pin_mismatch "$1" "$_name")"; [ -n "$_pin" ]; then
      gate "$_name" off "$_by ($2) — $_pin$(why "$_name" "$_step")"
    elif [ "$_probe" = node-resolvable ] && [ -d "$(npm root -g 2>/dev/null)/$_target" ]; then
      gate "$_name" off "$_by ($2) — 깔렸는데 프로브가 못 찾는다: 배선이 끊겼다$(why "$_name" "$_step")"
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
