# matcher = Read|mcp__(Claude_Browser|claude-in-chrome)__(computer|browser_batch)|mcp__computer-use__(screenshot|zoom|computer_batch)
#
# 그림 문 껍데기 — 몸통(`image-gate.py`) 앞에서 먼저 거른다. 왜와 갈래는 몸통 머리말이 든다.
#
# 홈 `~/.claude/settings.json` 의 PreToolUse 에 이 한 줄로 심긴다 — 심는 손은 이 자리만 채운다:
#     _ig="<이 파일이 있는 자리>"; . "$_ig/image-gate.sh"
# 윗줄 `# matcher = …` 가 그 항목의 matcher 진본이다 — 심는 손은 이 줄을 읽어 쓰고 손으로 안 든다.
#
# ⚠ **점(`.`)으로 부른다** — 같은 셸 안에서 돌아 프로세스가 안 는다. 그래서 끝의 `exit 0` 이 훅을 끝낸다.
# ⚠ **파이썬은 그림 낌새(확장자 · screenshot · zoom)가 있을 때만 띄운다** — 매 Read 마다 띄우면
#   윈도우에서 그 값이 일보다 크다. 소문자로 눌러 재므로 확장자는 한 벌만 든다.
#   ⚠ **확장자 목록은 몸통의 `IMG_EXT` 와 짝이다** — `scripts/image-gate-check.py` 가 집합으로 맞댄다.
# ⚠ **파이썬은 존재가 아니라 불러 보고 고른다** — 윈도우의 `python3` 는 스토어 껍데기라 49 로 죽는다.
#   못 뜨면 「못 쟀다」 한 줄을 직접 낸다 — 문이 죽은 사실이 어디에도 안 남는 것이 침묵보다 비싸다.
#   문이 없는 것과 문이 잘못 잠긴 것은 다른 사고고 뒤엣것이 더 비싸다 — 그래서 막지는 않는다.
j=$(cat)
l=$(printf %s "$j" | tr A-Z a-z)
case "$l" in
  *.png*|*.jpg*|*.jpeg*|*.webp*|*.gif*|*screenshot*|*zoom*)
    py=
    for p in python python3; do
      "$p" -X utf8 -c "" >/dev/null 2>&1 && { py=$p; break; }
    done
    if [ -n "$py" ]; then
      printf %s "$j" | "$py" -X utf8 "$_ig/image-gate.py"
    else
      printf %s '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"그림 문 — 파이썬이 안 떠서 치수를 못 쟀다. 스스로 고른다"}}'
    fi
    ;;
esac
exit 0
