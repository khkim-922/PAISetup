# matcher = Read|mcp__(Claude_Browser|claude-in-chrome)__(computer|browser_batch)|mcp__computer-use__(screenshot|zoom|computer_batch)
# events = PreToolUse
# if.PreToolUse = Read(//**/*.png) | Read(//**/*.jpg) | Read(//**/*.jpeg) | Read(//**/*.gif) | Read(//**/*.webp) | Read(//**/*.pdf) | mcp__Claude_Browser__computer | mcp__Claude_Browser__browser_batch | mcp__claude-in-chrome__computer | mcp__claude-in-chrome__browser_batch | mcp__computer-use__screenshot | mcp__computer-use__zoom | mcp__computer-use__computer_batch
# var = _ig
#
# 그림 문 껍데기 — 몸통(`image-gate.py`) 앞에서 먼저 거른다. 왜와 갈래는 몸통 머리말이 든다.
#
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 이 줄들로 등록을 짓고, 몸통은
# 그 등록이 세운 `$_ig` 곁에 같이 실린다. 머리말의 뜻과 심기는 명령 꼴은 표(`tool-homes.conf`)의 hook 꼴이 든다.
#
# ⚠ **점(`.`)으로 부른다** — 같은 셸 안에서 돌아 프로세스가 안 는다. 그래서 끝의 `exit 0` 이 훅을 끝낸다.
# ⚠ **그림이 아닌 Read 에는 아예 안 뜬다** — 거는 자가 등록의 거름(`if.PreToolUse` — 규칙마다 등록 하나)으로 그림 · PDF Read 와
#   화면 캡처 도구에만 이 껍데기를 띄운다. 경로 규칙은 `//**/*.<확장자>` 꼴이다 — 어느 폴더에서나 · 대소문자를 안 가리고
#   맞는다(`tool-homes.conf` hook 꼴). 거름의 확장자 · 도구는 matcher · 아래 글롭 · 몸통 상수와 짝이다(`scripts/image-gate-check.py`).
# ⚠ **떴어도 흔한 길(그림 낌새 없는 입력)은 sh 말고 아무것도 안 띄운다** — 거름은 「best-effort」라 그것만 믿지 않는다. — 바깥 프로세스 하나가 윈도우에서 수백 ms 다(회사 PC
#   실측 하나에 약 0.3 초). 그래서 입력은 셸의 `read` 로 받고(훅 입력은 JSON 한 줄 · 끝 줄바꿈이 없어도 `|| [ -n ]` 이
#   받는다), 낌새는 아래 글롭이 입력 그대로에서 잰다 — 대소문자는 글자 묶음(`[Pp]`)으로 안 가린다(`tr` 로 누르지 않는다).
#   파이썬은 그 낌새(그림 확장자 · `.pdf` · screenshot · zoom)가 있을 때만 띄운다. `.pdf` 는 Read 가 페이지를 그림으로
#   그려 싣는 꼴이라 든다 — 몸통이 장수와 합을 곁말로만 대고 막지는 않는다(갈래는 몸통 머리말).
#   ⚠ **확장자 목록은 몸통의 `IMG_EXT` · `PDF_EXT` 를 합친 것과 짝이다** — `scripts/image-gate-check.py` 가 글자 묶음을 펴서
#   집합으로 맞대고, 묶음 밖의 맨 글자(대소문자를 가리는 칸)도 어긋남으로 댄다.
# ⚠ **파이썬은 따로 불러 보지 않고 몸통을 바로 돌린다** — 불러 보는 한 번이 그림마다 해석기를 한 번 더 띄운다. 첫 후보로
#   몸통을 돌리고, **해석기가 안 뜬 종료 값**일 때만 다음 후보로 넘어간다: 127(그 이름이 없다) · 126(못 돌린다) ·
#   49(윈도우의 `python3` 같은 스토어 껍데기 — 안내문을 stderr 로 뱉고 49 로 죽는다).
#   그 밖의 종료 값은 해석기가 뜬 것이다 — 몸통은 언제나 0 으로 끝나므로(몸통 머리말) 0 이 아니면 몸통이 죽은 것이고,
#   그때는 다른 해석기로 다시 돌리지 않는다.
#   몸통의 출력은 받아 뒀다가 0 일 때만 낸다 — 안 뜬 후보나 죽은 몸통이 흘린 글자가 훅의 답에 섞이지 않는다.
#   입력은 here-document 로 먹인다 — 관(`printf … |`)으로 먹이면 `printf` 를 돌릴 셸 갈래가 하나 더 선다.
# ⚠ **못 쟀으면 그렇다고 한 줄을 직접 낸다** — 해석기가 안 떴든 몸통이 죽었든, 문이 죽은 사실이 어디에도 안 남는 것이
#   침묵보다 비싸다. 문이 없는 것과 문이 잘못 잠긴 것은 다른 사고고 뒤엣것이 더 비싸다 — 그래서 막지는 않는다.
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
j=
while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done
case "$j" in
  *.[Pp][Nn][Gg]*|*.[Jj][Pp][Gg]*|*.[Jj][Pp][Ee][Gg]*|*.[Ww][Ee][Bb][Pp]*|*.[Gg][Ii][Ff]*|*.[Pp][Dd][Ff]*|\
  *[Ss][Cc][Rr][Ee][Ee][Nn][Ss][Hh][Oo][Tt]*|*[Zz][Oo][Oo][Mm]*)
    _rc=127
    for _p in python python3; do
      # shellcheck disable=SC2154 # _ig 는 홈에 심긴 한 줄이 이 파일을 읽기 전에 세운다(머리말)
      _out=$("$_p" -X utf8 "$_ig/image-gate.py" <<_IG_INPUT
$j
_IG_INPUT
      )
      _rc=$?
      case $_rc in 49|126|127) ;; *) break ;; esac
    done
    case $_rc in
      0) printf %s "$_out" ;;
      49|126|127) printf %s '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"그림 문 — 파이썬이 안 떠서 치수를 못 쟀다. 스스로 고른다"}}' ;;
      *) printf %s '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"그림 문 — 재는 자가 죽어(종료 '"$_rc"') 치수를 못 쟀다. 스스로 고른다"}}' ;;
    esac
    ;;
esac
exit 0
