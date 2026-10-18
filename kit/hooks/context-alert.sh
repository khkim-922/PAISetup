# events = UserPromptSubmit
# var = _ca
#
# 컨텍스트 알림 껍데기 — 몸통(`context-alert.py`)을 띄운다. 왜 · 이벤트를 고른 까닭 · 갈래는 몸통 머리말이 든다.
#
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 이 줄들로 등록을 짓고, 몸통은
# 그 등록이 세운 `$_ca` 곁에 같이 실린다. 머리말의 뜻과 심기는 명령 꼴은 표(`tool-homes.conf`)의 hook 꼴이 든다.
# ⚠ **matcher 줄을 안 둔다** — UserPromptSubmit 은 matcher 를 안 받고, 키가 있으면 거는 자가 항목째 걸러낸다(#120).
#
# ⚠ **점(`.`)으로 부른다** — 같은 셸 안에서 돌아 프로세스가 안 는다. 그래서 끝의 `exit 0` 이 훅을 끝낸다.
# 파이썬은 거르지 않고 매번 띄운다 — 사람이 글을 보낼 때 한 번이고, 수치는 기록을 JSON 으로 읽어야 나온다.
# ⚠ **공통 경로에서 셸 밖의 프로세스는 파이썬 몸통 하나뿐이다** — 회사에서는 프로세스 하나가 약 0.3 초이고 이 훅은 프롬프트마다
#   돈다. 그래서 입력은 `cat` 이 아니라 셸 `read` 로 받고, 몸통 앞의 파이썬 탐침도 없다.
# ⚠ **파이썬은 존재가 아니라 불러 보고 고른다** — 윈도우의 `python3` 는 스토어 껍데기라 49 로 죽는다. 몸통을 바로 불러 보고
#   죽으면 다음 후보로 간다 — 몸통은 찍은 뒤에는 늘 0 으로 끝나(재다 지면 아무것도 안 찍고 0) 같은 몸통이 두 번 돌지 않는다.
#   못 뜨면 아무것도 안 낸다 — 매 프롬프트마다 같은 실패 줄이 붙는 값이, 알림이 없는 값(이 훅이 없던 자리)보다 크다.
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
j=; while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done
# shellcheck disable=SC2154 # _ca 는 홈에 심긴 한 줄이 이 파일을 읽기 전에 세운다(머리말)
printf %s "$j" | python -X utf8 "$_ca/context-alert.py" 2>/dev/null ||
  printf %s "$j" | python3 -X utf8 "$_ca/context-alert.py" 2>/dev/null
exit 0
