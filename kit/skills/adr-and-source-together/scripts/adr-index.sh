#!/bin/sh
# 결정 목록을 결정 파일들의 머리(frontmatter)에서 만들어 낸다.
#
# 왜 생성하나: 목록을 손으로 유지하면 결정을 쓴 뒤 목록이 뒤에 남는다.
#   진본은 결정 파일 자신이므로, 목록은 사본이 아니라 파생물이어야 한다.
#
# 사용:  adr-index.sh <결정 폴더> > <결정 폴더>/INDEX.md
#
# 읽는 것: NNNN-*.md 의 frontmatter — number · title · status · date · superseded_by
set -eu

DIR="${1:-.}"

printf '# 결정 목록\n\n'
printf '<!-- 생성물이다. 손으로 고치지 않는다 — adr-and-source-together 스킬의 scripts/adr-index.sh 가 만든다. -->\n\n'
printf '결정 하나가 파일 하나다. 상태가 `Superseded`면 어느 결정이 대체했는지 화살표가 든다.\n'
printf '본문·근거는 각 파일이 들고, 이 표는 **무엇이 있고 어느 것이 살아 있나**만 든다.\n\n'
printf '| # | 무엇을 정했나 | 상태 | 날짜 |\n|---|---|---|---|\n'

found=0
has_err=0
# 결정 파일 전부를 awk 하나가 차례로 읽는다 — 파일마다 awk · basename 을 띄우면 결정이 쌓일수록 프로세스가 둘씩 는다
#   (119 장에 238 번 · #155). 표의 차례는 셸 글롭의 차례 그대로다.
set -- "$DIR"/[0-9]*.md
[ -e "$1" ] && found=1
if [ "$found" = 1 ] && ! awk '
    # 앞 파일을 마무리한다 — 머리가 없으면 결정 파일이 아니다. 틀린 꼴은 알리고 그 줄만 빼고 다음 파일로 간다
    function flush() {
        if (file == "" || num == "") return
        if (st ~ /^Superseded./) {
            printf "✖ %s: status 는 Superseded 한 낱말이다 — 대체한 번호는 superseded_by 칸이 든다\n", file > "/dev/stderr"
            err = 1; return
        }
        if (st == "Superseded" && sup == "") {
            printf "✖ %s: status: Superseded 인데 superseded_by 가 없다\n", file > "/dev/stderr"
            err = 1; return
        }
        # 값의 **꼴**도 문다 — 규칙은 「NNNN」인데 칸이 있나만 보면 슬러그 · `.md` 슬러그 · 따옴표 친
        #   링크가 그대로 지나가 규칙이 글로만 산다(아뜰리에에서 18장 중 14장이 샜다 · #116).
        if (sup != "" && sup !~ /^[0-9][0-9][0-9][0-9]$/) {
            printf "✖ %s: superseded_by 는 네 자리 번호 하나다 (값: %s)\n", file, sup > "/dev/stderr"
            err = 1; return
        }
        if (sup != "") st = st " → " sup
        printf "| [%s](%s) | %s | %s | %s |\n", num, file, ttl, st, dt
    }
    FNR == 1 { flush(); file = FILENAME; sub(/.*[\/\\]/, "", file); fm = 0; num = ttl = st = dt = sup = "" }
    fm >= 2 { next }                                   # 머리 뒤 본문은 안 읽는다
    /^---[[:space:]]*$/ { fm++; next }
    fm != 1 { next }
    /^number:/         { sub(/^number:[[:space:]]*/, "");         num = $0 }
    /^title:/          { sub(/^title:[[:space:]]*/, "");          ttl = $0 }
    /^status:/         { sub(/^status:[[:space:]]*/, ""); sub(/[[:space:]]+$/, ""); st = $0 }
    /^date:/           { sub(/^date:[[:space:]]*/, "");           dt  = $0 }
    /^superseded_by:/  { sub(/^superseded_by:[[:space:]]*/, ""); sub(/[[:space:]]+$/, ""); sup = $0 }
    END { flush(); exit err }
' "$@"; then
    has_err=1
fi

[ "$found" = 1 ] || printf '| — | _아직 없다_ | | |\n'
[ "$has_err" -eq 0 ] || exit 1
