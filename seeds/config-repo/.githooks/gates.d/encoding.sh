#!/bin/sh
# 조각 — **파워셸은 BOM 이 있어야 하고, cmd 는 없어야 한다.** 그 둘만 막는다.
#
# 왜 이것 둘인가 — 둘 다 **파일은 멀쩡히 커밋되고 남의 PC 에서만 깨진다.**
#
#   · `*.ps1` — Windows PowerShell 5.1 은 **BOM 없는 스크립트를 시스템 ANSI 코드페이지로
#     읽는다**(한국어 윈도우는 cp949). UTF-8 로 저장한 한글이 그 자리에서 깨지고, 따옴표가
#     안 닫혀 파서가 죽는다. 콘솔 코드페이지(`chcp 65001`)는 다른 자리라 고쳐도 안 낫는다.
#   · `*.cmd` — 반대다. cmd.exe 는 배치 파일을 콘솔 OEM 코드페이지로 읽으므로 **BOM 이 붙으면
#     첫 줄이 깨진다.** `@echo off` 가 명령으로 안 읽혀 창에 그대로 찍히고 그 뒤가 어긋난다.
#
# ⚠ **고쳐 주지 않고 막는다.** 커밋 훅이 스테이지한 파일을 조용히 바꾸면, 사람이 본 것과
#   커밋된 것이 달라진다. 무엇을 어떻게 고칠지 대고 물러난다.
#   (파일을 **만드는 순간** 찍는 것은 다른 층이 든다 — `.claude/hooks/utf8-bom.sh` 가
#   Write·Edit 마다 돌아 찍는다. 여기는 그것이 안 걸린 길을 막는 마지막 자리다.)
set -u

BOM="$(printf '\357\273\277')"
FAIL=0

# 스테이지된 것만 잰다 — 손대지 않은 파일로 커밋을 막지 않는다.
STAGED="$(git diff --cached --name-only --diff-filter=ACM)"
[ -n "$STAGED" ] || exit 0

for f in $STAGED; do
  [ -f "$f" ] || continue
  head3="$(head -c 3 "$f" 2>/dev/null || true)"
  case "$f" in
    *.ps1|*.psm1|*.psd1)
      if [ "$head3" != "$BOM" ]; then
        printf '✖ BOM 이 없다 — 한국어 윈도우에서 한글이 깨진다:  %s\n' "$f" >&2
        # ⚠ **`echo` 로 찍지 않는다.** 역슬래시를 먹는 셸이 있어 안내가 BOM 글자 자체로
        #   찍혔다(실측) — 그대로 복사하면 안 듣는다. `printf %s` 는 안 먹는다.
        printf '%s\n' "    고치는 법:  printf '\\357\\273\\277' | cat - '$f' > t && mv t '$f'" >&2
        FAIL=1
      fi
      ;;
    *.cmd|*.bat)
      if [ "$head3" = "$BOM" ]; then
        printf '✖ BOM 이 붙었다 — cmd.exe 가 첫 줄을 못 읽는다:  %s\n' "$f" >&2
        printf '%s\n' "    고치는 법:  tail -c +4 '$f' > t && mv t '$f'" >&2
        FAIL=1
      fi
      ;;
  esac
done

[ "$FAIL" = 0 ] || printf '  파일은 멀쩡히 커밋되고 **남의 PC 에서만** 깨지는 자리다.\n' >&2
exit "$FAIL"
