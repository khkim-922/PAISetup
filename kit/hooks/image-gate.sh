# matcher = Read|mcp__(Claude_Browser|claude-in-chrome)__(computer|browser_batch)|mcp__computer-use__(screenshot|zoom|computer_batch)
# events = PreToolUse
# var = _ig
#
# 그림 문 껍데기 — 몸통(`image-gate.py`) 앞에서 먼저 거른다. 왜와 갈래는 몸통 머리말이 든다.
#
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 이 줄들로 등록을 짓고, 몸통은
# 그 등록이 세운 `$_ig` 곁에 같이 실린다. 머리말의 뜻과 심기는 명령 꼴은 표(`tool-homes.conf`)의 hook 꼴이 든다.
#
# ⚠ **점(`.`)으로 부른다** — 같은 셸 안에서 돌아 프로세스가 안 는다. 그래서 끝의 `exit 0` 이 훅을 끝낸다.
# ⚠ **흔한 길(그림 낌새 없는 Read)은 sh 말고 아무것도 안 띄운다** — 바깥 프로세스 하나가 윈도우에서 수백 ms 다(회사 PC
#   실측 하나에 약 0.3 초). 그래서 입력은 셸의 `read` 로 받고(훅 입력은 JSON 한 줄 · 끝 줄바꿈이 없어도 `|| [ -n ]` 이
#   받는다), 낌새는 아래 글롭이 입력 그대로에서 잰다 — 대소문자는 글자 묶음(`[Pp]`)으로 안 가린다(`tr` 로 누르지 않는다).
#   파이썬은 그 낌새(그림 확장자 · `.pdf` · screenshot · zoom)가 있을 때만 띄운다. `.pdf` 는 Read 가 페이지를 그림으로
#   그려 싣는 꼴이라 든다 — 몸통이 장수와 합을 곁말로만 대고 막지는 않는다(갈래는 몸통 머리말).
#   ⚠ **확장자 목록은 몸통의 `IMG_EXT` · `PDF_EXT` 를 합친 것과 짝이다** — `scripts/image-gate-check.py` 가 글자 묶음을 펴서
#   집합으로 맞대고, 묶음 밖의 맨 글자(대소문자를 가리는 칸)도 어긋남으로 댄다.
# ⚠ **파이썬은 존재가 아니라 불러 보고 고른다** — 윈도우의 `python3` 는 스토어 껍데기라 49 로 죽는다.
#   못 뜨면 「못 쟀다」 한 줄을 직접 낸다 — 문이 죽은 사실이 어디에도 안 남는 것이 침묵보다 비싸다.
#   문이 없는 것과 문이 잘못 잠긴 것은 다른 사고고 뒤엣것이 더 비싸다 — 그래서 막지는 않는다.
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
j=
while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done
case "$j" in
  *.[Pp][Nn][Gg]*|*.[Jj][Pp][Gg]*|*.[Jj][Pp][Ee][Gg]*|*.[Ww][Ee][Bb][Pp]*|*.[Gg][Ii][Ff]*|*.[Pp][Dd][Ff]*|\
  *[Ss][Cc][Rr][Ee][Ee][Nn][Ss][Hh][Oo][Tt]*|*[Zz][Oo][Oo][Mm]*)
    py=
    for p in python python3; do
      "$p" -X utf8 -c "" >/dev/null 2>&1 && { py=$p; break; }
    done
    if [ -n "$py" ]; then
      # shellcheck disable=SC2154 # _ig 는 홈에 심긴 한 줄이 이 파일을 읽기 전에 세운다(머리말)
      printf %s "$j" | "$py" -X utf8 "$_ig/image-gate.py"
    else
      printf %s '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"그림 문 — 파이썬이 안 떠서 치수를 못 쟀다. 스스로 고른다"}}'
    fi
    ;;
esac
exit 0
