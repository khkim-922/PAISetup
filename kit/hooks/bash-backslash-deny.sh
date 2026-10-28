#!/bin/sh
# matcher = Bash
# events = PreToolUse
# var = _bb
#
# PreToolUse(Bash) — 명령의 겹역슬래시가 셸에 쓴 그대로 닿게 **고쳐 넘긴다**(#92 · 상류 anthropics/claude-code#88561).
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 짓고, 머리말의 뜻과 심기는 명령
# 꼴은 표(`tool-homes.conf`)의 hook 꼴이 든다. 이 훅을 거는 쪽은 그 홈 등록 하나다 — 저장소 설정(`.claude/settings.json`)이
# 또 걸면 Bash 호출마다 두 번 돈다(결정 0124). 홈 등록은 이 파일을 점(`.`)으로 읽고, 셔뱅과 끝의 `exit 0` 은 바로 돌려도
# (검사 · 손) 서게 둔다.
#
# 윈도우에서 Bash 도구로 보낸 명령은 셸에 닿기 전에 역슬래시 n 개가 올림(n/2) 개로 접힌다 — 짝마다 하나가 되고 남는 홑 것은
# 그대로다. 홑따옴표 · 따옴표 친 heredoc 안에서도 같아, 파이썬 · sed 를 흘려 파일을 고치는 명령이 **성공으로 끝나고 파일만
# 틀린다.** 접힘이 아직 있나는 사람이 가끔 잰다 — 그 한 줄(훅을 끈 머리 없는 Claude 한 판)은 `scripts/README.md` 가 든다.
# 훅이 고칠 수 있는 까닭 — 접히는 것은 명령이 셸로 넘어가는 순간이고, 훅은 그 전의 도구 입력을 받아 고친 입력
# (`updatedInput`)을 돌려줄 수 있다. 몸통(`bash-backslash.py`)이 역슬래시를 다 두 배로 늘려 돌려주면 접힌 뒤 쓴 그대로 닿는다.
# ⚠ **Claude Code 판은 안 본다** — 상류가 접힘을 고친 판에서는 두 배가 그대로 닿아 결과만 틀린다. 그날은 위의 사람 손 한 줄이
#   재고, 그때 이 훅을 통째로 걷는다(결정 0185). 파이썬이 안 떠 못 고치면 **막는다** — 까닭을 돌려주면 모델이 역슬래시 없이 다시 짓는다.
# ⚠ **윈도우에서만 건다.** 리눅스는 안 접힌다(원격 컨테이너 실측 · #150) — 거기서 고치면 두 배가 그대로 닿는다.
# ⚠ 재는 것은 `command` 칸 하나다 — `cwd` 같은 다른 칸은 UNC 경로로 겹역슬래시를 들 수 있다.
#   `"command":` 는 JSON 문자열 안에서는 설 수 없는 글자라(안의 따옴표는 역슬래시가 앞선다) 키로만 걸린다.
# ⚠ **겹역슬래시 낌새 앞 구간은 `sh` 밖의 프로세스를 하나도 안 띄운다** — 입력은 셸 `read` 로 받고(`cat` 없이), `command` 칸을 `sed` 로
#   뽑는 일은 입력 전체에 JSON 으로 이스케이프된 겹역슬래시(역슬래시 넷)가 있을 때만 한다. 회사 PC 에서는 프로세스 하나가 약 0.3 초이고
#   이 훅은 Bash 를 부를 때마다 돌아, 호출마다 그 수만큼 값이 붙는다. 역슬래시 넷은 `cwd` 의 UNC 경로에도 있을 수 있어 낌새일 뿐이고,
#   판정은 뽑은 `command` 가 한다.
# 시험 — `sh scripts/check-bash-backslash.sh` (실물 꼴의 입력을 먹여 고칠 것 · 막을 것 · 둘 것을 문다).
[ "${OS:-}" = Windows_NT ] || exit 0
j=; while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done
cmd=
case "$j" in
  *'\\\\'*) cmd=$(printf '%s' "$j" | sed -nE 's/.*"command" *: *"(([^"\\]|\\.)*)".*/\1/p') ;;
esac
case "$cmd" in
  *'\\\\'*)
    py=
    for p in python python3; do
      "$p" -X utf8 -c "" >/dev/null 2>&1 && { py=$p; break; }
    done
    # 몸통은 껍데기 곁에 산다 — 홈 등록은 그 자리를 `_bb` 로 세우고 이 파일을 점으로 읽는다(`$0` 은 셸 이름). 바로 돌리면
    #   (검사 · 손) `$0` 이 이 파일이다. 변수는 표 머리의 꼴로만 편다(갈 곳 표의 손이 그 꼴로 곁 파일을 싣는다)
    case "$0" in */bash-backslash-deny.sh) _bb=$(dirname "$0") ;; esac
    # shellcheck disable=SC2154 # _bb 는 홈에 심긴 한 줄이 이 파일을 읽기 전에 세운다(위)
    if [ -z "$py" ] || ! printf '%s' "$j" | "$py" -X utf8 "$_bb/bash-backslash.py"; then
      printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"이 PC 에서 Bash 도구로 보낸 명령은 겹역슬래시가 셸에 닿기 전에 하나로 접힌다 — 홑따옴표 · 따옴표 친 heredoc 안에서도. 고쳐 넘기는 몸통이 못 돌아(파이썬이 없거나 몸통이 졌다) 막았다. 먼저 역슬래시를 빼고 같은 Bash 명령으로 다시 짓는다 — 경로는 / 로, 정규식의 이스케이프는 [.] 같은 문자 묶음으로, 필요 없는 이스케이프는 지운다. 역슬래시가 데이터로 꼭 들어야 할 때(스크립트 본문 · 파일 내용)만 Write 로 파일에 써서 돌린다 — 파이썬 안이면 chr(92)."}}'
    fi
    ;;
esac
exit 0
