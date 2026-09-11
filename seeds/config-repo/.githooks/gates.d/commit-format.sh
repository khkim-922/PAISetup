#!/bin/sh
# 조각 — 커밋 메시지 형식. **메시지 파일 경로를 $1 로 받는다**(commit-msg 절).
#
# 검사 둘
#   1. BOM     제목 맨 앞의 U+FEFF. 눈에 안 보이는데 파서를 깨뜨린다. 우리가 잰다.
#   2. 형식    Conventional Commits. commitlint 가 잰다.
#
# 왜 BOM 을 따로 보나
#   commitlint 는 BOM 붙은 메시지를 "type-empty / subject-empty" 로 보고한다. 틀린 말은
#   아닌데 원인을 못 짚어서 같은 실수를 또 하게 된다. 형제 저장소 이력 314건 중 10건이
#   그 상태였다 (실측 · atelier).
#
# 낱말 목록(type-enum)은 여기 안 적는다 — 명세가 든다(규범 [Conventional Commits]).
# 규칙 파일은 저장소가 `commitlint.config.mjs` 로 든다.
set -u

msgfile="${1:-}"
[ -n "$msgfile" ] && [ -f "$msgfile" ] || exit 0
lintfile="$msgfile"
tmp=""
fail=0
cleanup() { [ -n "$tmp" ] && rm -f "$tmp"; }
trap cleanup EXIT

# 주석(#)과 빈 줄을 걷어낸 첫 줄이 제목이다.
subject="$(grep -v '^#' "$msgfile" | sed '/^[[:space:]]*$/d' | head -n 1)"
[ -n "$subject" ] || exit 0   # 빈 메시지는 git 이 알아서 막는다

# 자동 병합·되돌리기·rebase 보조 커밋은 규약 밖이다.
case "$subject" in
    "Merge "*|"Revert "*|"fixup! "*|"squash! "*|"amend! "*) exit 0 ;;
esac

# ------------------------------------------------------------------ 1. BOM
# PowerShell 의 >, >>, Out-File 은 UTF-8 with BOM 으로 쓴다. 메시지를 파일로 넘기면
# BOM 이 맨 앞에 붙는데, `git log` 에도 안 보인다.
#
# 걷어내는 데 외부 도구를 안 쓴다 — 셸 파라미터 확장만 쓴다.
# (`sed` 의 `\xNN` 은 구현마다 달라서, 안 되는 셸에서 조용히 안 걸릴 수 있다.)
BOM="$(printf '\357\273\277')"
if [ "$(printf '%s' "$BOM" | wc -c | tr -d ' ')" = "3" ]; then
    if [ "$(head -c 3 "$msgfile")" = "$BOM" ]; then
        printf '✖ 커밋 메시지 맨 앞에 BOM(U+FEFF)이 붙었다 — 눈에는 안 보인다.\n' >&2
        printf '  원인: 메시지를 PowerShell 의 >, >>, Out-File 로 쓴 파일에서 넘겼다.\n' >&2
        printf '  고치는 법: git commit -m 으로 직접 주거나, 파일로 넘길 때 BOM 없이 쓴다.\n' >&2
        printf '    Out-File -Encoding utf8NoBOM   또는   Set-Content -Encoding utf8NoBOM\n' >&2
        fail=1
        # 형식 검사가 엉뚱한 오류를 내지 않도록, 벗긴 사본으로 이어서 잰다.
        tmp="$(mktemp)" && tail -c +4 "$msgfile" > "$tmp" && lintfile="$tmp"
    fi
else
    printf '· 이 셸에서 BOM 상수를 못 만들어 BOM 검사를 건너뛴다 — 형식 검사만 돈다.\n' >&2
fi

# --------------------------------------------------------------- 2. 형식
# ⚠ **저장소 축을 먼저 본다.** 판을 잠근 저장소는 그쪽이 진본이고, 전역은 그것을 안 쓰는
#   저장소를 위한 자리다. 둘 다 없으면 약하게라도 재고 **안 쟀다고 말하고 간다.**
CL=""
[ -x "node_modules/.bin/commitlint" ] && CL="node_modules/.bin/commitlint"
[ -z "$CL" ] && command -v commitlint >/dev/null 2>&1 && CL="commitlint"

# 규칙 파일 — **저장소 것이 먼저다.** 저장소가 제 규칙을 두면 그것이 진본이고, 전역
# 배포본은 안 둔 저장소를 위한 자리다. commitlint 는 뿌리 설정을 제 손으로 찾으므로
# 저장소 것이 있으면 아무것도 안 넘긴다.
CFG=""
if [ ! -f commitlint.config.mjs ] && [ ! -f commitlint.config.js ] && [ ! -f .commitlintrc.mjs ]; then
    [ -f .claude/commitlint.global.mjs ] && CFG=".claude/commitlint.global.mjs"
fi

if [ -n "$CL" ]; then
    if [ -n "$CFG" ]; then out="$("$CL" --edit "$lintfile" --config "$CFG" 2>&1)" || out_rc=1
    else                   out="$("$CL" --edit "$lintfile" 2>&1)"              || out_rc=1
    fi
    if [ "${out_rc:-0}" = 1 ]; then
        printf '%s\n' "$out" >&2
        fail=1
    fi
else
    printf '· commitlint 이 없어 첫 줄 형식만 대충 본다 — 본문·꼬리는 안 쟀다.\n' >&2
    types='feat|fix|docs|refactor|test|chore|style|perf|build|ci|revert'
    check="$(grep -v '^#' "$lintfile" | sed '/^[[:space:]]*$/d' | head -n 1)"
    if ! printf '%s' "$check" | grep -qE "^($types)(\([^)]+\))?!?: .+"; then
        printf '✖ 커밋 제목이 Conventional Commits 형식이 아니다.\n' >&2
        printf '  받은 것: %s\n' "$check" >&2
        printf '  형식:    <type>[(범위)][!]: <한 줄 요약>\n' >&2
        printf '  type:    %s\n' "$(printf '%s' "$types" | tr '|' ' ')" >&2
        fail=1
    fi
fi
exit "$fail"
