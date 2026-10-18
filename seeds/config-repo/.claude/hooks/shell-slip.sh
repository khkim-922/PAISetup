#!/bin/sh
# matcher = Bash|PowerShell
# events = PreToolUse
# var = _ss
#
# PreToolUse(Bash · PowerShell) — 셸 명령의 비싼 실수 둘을 그 순간에 건다. 이름 · 창 제목으로 프로세스 끄기는 묻고, 상태를 바꾸는
# 스크립트(설치기 · 배포)를 앞만 읽고 끊는 자에 물리기는 막는다. 무엇에 걸고 무엇을 두나는 몸통(`shell-slip.py`) 머리말이 든다.
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 짓고, 머리말의 뜻과 심기는 명령 꼴은
# 표(`tool-homes.conf`)의 hook 꼴이 든다. 홈 등록은 이 파일을 점(`.`)으로 읽고, 셔뱅과 끝의 `exit 0` 은 바로 돌려도(검사) 서게 둔다.
#
# ⚠ **파이썬은 낌새가 있을 때만 띄운다** — Bash · PowerShell 호출마다 도는 훅이라, 매번 띄우면 그 값이 모든 호출에 붙는다.
#   낌새는 아래 글롭이 입력 전체에서 잰다 — 대소문자는 글자 묶음(`[Kk]`)으로 안 가린다. 소문자로 누르는 `tr` 은 호출마다
#   프로세스를 하나 더 띄워 안 쓴다. 글롭은 몸통이 거는 꼴을 다 덮어야 한다 — 좁으면 그 꼴은 조용히 안 걸린다. 검사가
#   걸어야 할 표본마다 이 껍데기를 지나 걸리나를 잰다.
# ⚠ **낌새 앞 구간은 `sh` 밖의 프로세스를 하나도 안 띄운다** — 입력은 셸 `read` 로 받는다(`cat` 없이). 회사 PC 에서는 프로세스 하나가
#   약 0.3 초이고 이 훅은 Bash · PowerShell 을 부를 때마다 돌아, 호출마다 그 수만큼 값이 붙는다.
# ⚠ **몸통이 못 돌면 낌새의 이름을 대고 묻는다**(파이썬이 없다 · 몸통이 졌다) — 정밀 판정 없이 막으면 무해한 명령을 막고, 말없이
#   지나가면 문이 죽은 것이 안 보인다.
# ⚠ **파이썬은 존재가 아니라 불러 보고 고른다** — 윈도우의 `python3` 는 스토어 껍데기라 49 로 죽는다.
#
# 시험 — `python -X utf8 scripts/check-shell-slip.py` (실물 꼴의 입력을 홈 등록의 명령으로 먹여 물을 것 · 막을 것 · 둘 것을 문다).
j=; while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done
hint=
case "$j" in
  *[Tt][Aa][Ss][Kk][Kk][Ii][Ll][Ll]*|*[Pp][Kk][Ii][Ll][Ll]*|*[Kk][Ii][Ll][Ll][Aa][Ll][Ll]*|*[!A-Za-z][Kk][Ii][Ll][Ll][!A-Za-z]*|\
  *[Ss][Tt][Oo][Pp]-[Pp][Rr][Oo][Cc][Ee][Ss][Ss]*|*[Ss][Pp][Pp][Ss]*|*[Mm][Aa][Ii][Nn][Ww][Ii][Nn][Dd][Oo][Ww][Tt][Ii][Tt][Ll][Ee]*)
    hint="프로세스 끄기" ;;
esac
case "$j" in
  *[Dd][Ee][Pp][Ll][Oo][Yy].[Pp][Ss]1*|*[Ii][Nn][Ss][Tt][Aa][Ll][Ll].[Pp][Ss]1*|*[Ii][Nn][Ss][Tt][Aa][Ll][Ll].[Cc][Mm][Dd]*|\
  *[Ss][Ee][Tt][Uu][Pp]-[Rr][Ee][Mm][Oo][Tt][Ee].[Ss][Hh]*|*[Bb][Uu][Ii][Ll][Dd]-[Dd][Ii][Ss][Tt].[Ss][Hh]*|\
  *[Tt][Oo][Oo][Ll]-[Hh][Oo][Mm][Ee][Ss].[Pp][Yy]*)
    case "$j" in
      *[Hh][Ee][Aa][Dd]*|*[Ss][Ee][Ll][Ee][Cc][Tt]*) hint="${hint:+$hint · }상태를 바꾸는 스크립트 끊기" ;;
    esac ;;
esac
[ -n "$hint" ] || exit 0
# 몸통은 껍데기 곁에 산다 — 홈 등록은 그 자리를 `_ss` 로 세우고 이 파일을 점으로 읽는다(`$0` 은 셸 이름). 바로 돌리면 `$0` 이 이 파일이다
case "$0" in */shell-slip.sh) _ss=$(dirname "$0") ;; esac
for p in python python3; do
  # shellcheck disable=SC2154 # _ss 는 홈에 심긴 한 줄이 이 파일을 읽기 전에 세운다(위)
  out=$(printf '%s' "$j" | "$p" -X utf8 "$_ss/shell-slip.py" 2>/dev/null) && { printf '%s' "$out"; exit 0; }
done
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"셸 실수 문의 몸통(shell-slip.py)이 못 돌았다 — 파이썬이 없거나 몸통이 졌다. 이 명령에 %s 의 낌새가 있어 정밀 판정 없이 묻는다. 이름 · 창 제목으로 프로세스를 끄거나, 설치기 · 배포 스크립트의 출력을 head · Select-Object -First 로 끊는 명령이 아니면 승인한다."}}' "$hint"
exit 0
