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
for f in "$DIR"/[0-9]*.md; do
    [ -e "$f" ] || continue
    found=1
    awk -v file="$(basename "$f")" '
        /^---[[:space:]]*$/ { fm++; if (fm == 2) exit; next }
        fm != 1 { next }
        /^number:/         { sub(/^number:[[:space:]]*/, "");         num = $0 }
        /^title:/          { sub(/^title:[[:space:]]*/, "");          ttl = $0 }
        /^status:/         { sub(/^status:[[:space:]]*/, "");         st  = $0 }
        /^date:/           { sub(/^date:[[:space:]]*/, "");           dt  = $0 }
        /^superseded_by:/  { sub(/^superseded_by:[[:space:]]*/, "");  sup = $0 }
        END {
            if (num == "") exit                      # 머리가 없으면 결정 파일이 아니다
            if (sup != "") st = st " → " sup
            printf "| [%s](%s) | %s | %s | %s |\n", num, file, ttl, st, dt
        }
    ' "$f"
done

[ "$found" = 1 ] || printf '| — | _아직 없다_ | | |\n'
