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
# ⚠ **낱말 목록(type-enum)은 여기 안 적는다** — 명세가 든다(규범 [Conventional Commits]).
#   commitlint 이 없는 기계의 열화 갈래도 **꼴만** 보고 낱말은 안 본다: 목록을 적으면 명세와
#   어긋나는 날 아무도 모르고, 그 갈래는 애초에 「안 쟀다」고 말하는 자리다.
# 규칙 파일은 저장소가 제 것(`commitlint.config.*`)을 두면 그것이, 없으면 전역 배포본
# (`.claude/commitlint.global.mjs`)이 든다 — 아래 「규칙 파일」 칸.
set -u

msgfile="${1:-}"
[ -n "$msgfile" ] && [ -f "$msgfile" ] || exit 0
lintfile="$msgfile"
tmp=""
fail=0
cleanup() { [ -n "$tmp" ] && rm -f "$tmp"; }
trap cleanup EXIT

# 주석(#)과 빈 줄을 걷어낸 첫 줄이 제목이다. 한 awk가 grep·sed·head를 대신한다.
subject="$(awk '!/^#/ && !/^[[:space:]]*$/ { print; exit }' "$msgfile")"
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
# 전역 배포본도 저장소 것이 먼저고, 없으면 이 조각이 선 자리의 `.claude/` 를 본다 — 까닭은
# 마크다운 조각(`markdown.sh`)의 같은 자리가 든다.
CFG=""
if [ ! -f commitlint.config.mjs ] && [ ! -f commitlint.config.js ] && [ ! -f .commitlintrc.mjs ]; then
    for _c in .claude/commitlint.global.mjs "$(dirname "$0")/../../.claude/commitlint.global.mjs"; do
        [ -f "$_c" ] && { CFG="$_c"; break; }
    done
fi

if [ -n "$CL" ]; then
    # ⚠ **초기화한다.** `${out_rc:-0}` 만 두면 환경에 그 이름이 실려 올 때 **멀쩡한 메시지를
    #   빈 줄과 함께 막는다** — 사유 없는 빨강이 이 집에서 가장 나쁜 모양이다.
    out_rc=0
    if [ -n "$CFG" ]; then out="$("$CL" --edit "$lintfile" --config "$CFG" 2>&1)" || out_rc=$?
    else                   out="$("$CL" --edit "$lintfile" 2>&1)"                 || out_rc=$?
    fi
    # ⚠ **commitlint 은 「위반」과 「제 오류」를 종료코드로 안 가른다** — 설정 문법 오류도,
    #   `extends` 를 못 푸는 것도, 규칙 위반도 전부 1 이다(실측 2026-09-11 · 21.2.2). 그래서
    #   여기서 「못 쟀다」(2)로 가를 수단이 없다. 대신 **출력을 통째로 낸다** — 스택이 보이면
    #   사람이 「메시지가 아니라 설정이 문제구나」를 그 자리에서 안다.
    #   markdownlint·lychee 는 제 오류에 2 이상을 내서 그쪽 조각은 갈래를 든다.
    if [ "$out_rc" != 0 ]; then
        printf '%s\n' "$out" >&2
        fail=1
    fi
else
    # ⚠ **낱말 목록을 여기 안 적는다** — 머리글이 그렇게 말하고, 명세를 옮겨 적으면 명세와
    #   어긋나는 날 아무도 모른다. 그래서 이 갈래는 **꼴만** 본다: `<type>(범위)!: 요약`.
    #   어느 낱말이 정당한가는 commitlint 가 있는 자리가 든다.
    check="$(awk '!/^#/ && !/^[[:space:]]*$/ { print; exit }' "$lintfile")"
    if ! printf '%s' "$check" | grep -qE '^[a-z][a-z]*(\([^)]+\))?!?: .+'; then
        printf '✖ 커밋 제목이 Conventional Commits 꼴이 아니다.\n' >&2
        printf '  받은 것: %s\n' "$check" >&2
        printf '  꼴:      <type>[(범위)][!]: <한 줄 요약>\n' >&2
        printf '  낱말 목록은 명세가 든다 — https://www.conventionalcommits.org\n' >&2
        exit 1
    fi
    # ⚠ **꼴만 봤다는 것은 안 쟀다는 것이다.** 통과시키되 판정 옆에 찍히게 2 로 끝낸다 —
    #   본문·꼬리·낱말은 한 자도 안 봤고, 「전부 통과」로 읽히면 안 된다.
    [ "$fail" -eq 0 ] && {
        printf '· commitlint 이 없어 **제목의 꼴만** 봤다 — 본문·꼬리·낱말은 안 쟀다.\n' >&2
        exit 2
    }
fi
exit "$fail"
