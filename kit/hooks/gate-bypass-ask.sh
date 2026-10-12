#!/bin/sh
# PreToolUse(Bash · PowerShell) — 커밋 게이트를 건너뛰는 git 명령이면 **막지 않고 묻는다.**
#
# 게이트는 `.githooks/` 가 돌리고, 그것을 끄는 길은 둘이다 — `--no-verify` 와 `core.hooksPath` 덮어쓰기
# (`-c core.hooksPath=…`). 둘 다 게이트를 **소리 없이** 끈다. 규범 [State Change Requires Approval] 가
# 말하는 「되돌리기 어렵거나 밖으로 나가는 일」이 여기서는 명령 글자 하나로 드러나므로, 판단 없이
# 글자로 건다.
# ⚠ **막지 않는다(exit 2 가 아니다).** 게이트가 틀렸거나 알면서 넘겨야 하는 때가 실제로 있다 —
#   그때 사람이 승인하면 지나간다. 묻는 까닭을 곁에 댄다.
# ⚠ **git 명령과 그 글자가 함께 있을 때만** 문다 — `--no-verify` 를 설명하거나 찾는 명령
#   (grep · echo)까지 물면 묻기가 잦아져 아무도 안 읽는다.
j=$(cat)
case "$j" in
  *git*--no-verify*|*git*core.hooksPath=*)
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"커밋 게이트를 건너뛰는 git 명령이다(--no-verify 또는 core.hooksPath 덮어쓰기). 게이트가 무엇을 막았는지 먼저 보고, 알면서 넘길 때만 승인한다."}}'
    ;;
esac
exit 0
