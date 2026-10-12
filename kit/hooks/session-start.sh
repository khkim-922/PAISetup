#!/bin/bash
# 세션 시작 훅 — 문지기 (claude-config 0061)
#
# 원본은 claude-config/.claude/hooks/session-start.sh 다. 각 저장소의 것은 deploy.ps1 이
# 뿌린 배포본이다 — 배포본을 고치면 다음 배포에 덮인다.
#
# **몸통이 아니다.** 하는 일은 하나 — 이 저장소를 잡아 몸통(`session-start-body.sh`)을 찾아 넘긴다.
# 몸통을 저장소마다 사본으로 두면 몸통 한 줄을 고칠 때마다 형제 저장소가 다 따라 커밋해야 했다.
# 이 파일은 거의 안 바뀌므로 사본으로 서도 그 값을 안 부른다.
#
# 부르는 자는 그대로다 — 저장소 설정(`.claude/settings.json`) · 홈 훅 · deploy.ps1 · 리모트 설정
# 스크립트 · 설치기. 인자(`--install` · `--check` 등)와 종료코드도 몸통 것을 그대로 건넨다.
#
# 몸통을 찾는 차례:
#   ① 이 저장소 안   — claude-config 자신 · 씨앗에서 만든 설정 저장소는 몸통을 곁에 든다
#   ② 붙은 claude-config — 찾는 자는 `.githooks/claude-config-path.sh` 한 자리다(게이트와 같은 자)
#   ③ 홈 씨앗        — 설치기가 모든 PC 의 `~/.claude/seeds/config-repo/` 에 몸통을 깐다.
#                      claude-config 가 없는 동료 PC 가 이 자리로 선다
# ⚠ 셋 다 없으면 **막지 않고 알린다**(0001 의 뜻). 커밋 게이트 배선 한 줄만은 여기서 건다 — 로컬
#   git 설정 하나라 몸통 없이도 서고, 안 걸면 게이트 없이 커밋이 지나가는데 그 부재는 조용하다.
# ⚠ 말은 stdout 으로 낸다 — SessionStart 훅에서 모델이 읽는 것은 stdout 뿐이다.
set -u

# 이 저장소 — 제 경로가 곧 저장소다. 파이프로 먹여 제 경로를 못 잡으면 하네스 값으로 물러선다.
_self="${BASH_SOURCE[0]:-$0}"
_repo=""
case "$_self" in
  */.claude/hooks/*) _repo="$(cd "$(dirname "$_self")/../.." 2>/dev/null && pwd)" ;;
esac
[ -n "$_repo" ] || _repo="${CLAUDE_PROJECT_DIR:-$PWD}"

_body=""
if [ -f "$_repo/.claude/hooks/session-start-body.sh" ]; then
  _body="$_repo/.claude/hooks/session-start-body.sh"
else
  CONFIG_ROOT=""
  if [ -f "$_repo/.githooks/claude-config-path.sh" ]; then
    # shellcheck disable=SC2034 # 바로 아래 점으로 읽는 찾는 자(claude-config-path.sh)의 입력이다
    PROJECT_DIR="$_repo"
    . "$_repo/.githooks/claude-config-path.sh"
  fi
  for _b in ${CONFIG_ROOT:+"$CONFIG_ROOT/.claude/hooks/session-start-body.sh"} \
            "$HOME/.claude/seeds/config-repo/.claude/hooks/session-start-body.sh"; do
    [ -f "$_b" ] && { _body="$_b"; break; }
  done
fi

if [ -z "$_body" ]; then
  # 까닭을 가른다 — 고칠 손이 다르다.
  if [ -n "${CONFIG_ROOT:-}" ]; then
    _why="claude-config 는 붙었는데 몸통이 없다 — 옛 판이다. claude-config 를 당긴다"
  elif [ -f "$HOME/.claude/seeds/config-repo/.claude/hooks/session-start.sh" ]; then
    _why="홈 씨앗이 옛 설치본이라 몸통이 없다 — 새 설치본을 깐다(또는 claude-config 를 함께 붙인다)"
  else
    _why="claude-config 가 이 PC(또는 이 세션)에 안 붙었고 홈 씨앗도 없다 — claude-config 를 함께 붙이거나 설치기를 돌린다"
  fi
  # ⚠ **종료코드는 부른 갈래의 약속을 따른다.** 세션(auto)은 막지 않는다(0001). 재는 갈래와 설치 갈래는
  #   「안 깔았다 · 못 쟀다」를 성공으로 내면 위층(deploy.ps1 · 설치기)이 초록으로 읽는다.
  # ⚠ 배선은 세션에서만 건다 — 재는 갈래가 상태를 바꾸면 판정이 늘 초록이 된다(몸통의 `--check` 규율).
  case "${1:-}" in
    --needs-install) echo "세션 훅 몸통을 못 찾았다 — $_why"; exit 2 ;;
    --check|--install|--install-global)
      echo "$(basename "$_repo"): ✖ 세션 훅 몸통을 못 찾았다 — $_why"; exit 1 ;;
  esac
  [ -d "$_repo/.githooks" ] && git -C "$_repo" config core.hooksPath .githooks 2>/dev/null
  echo "$(basename "$_repo"): ⚠ 세션 훅 몸통을 못 찾았다 — $_why. 커밋 게이트 배선만 걸었고, 도구 설치 · 진단은 안 돌았다"
  exit 0
fi

SESSION_START_REPO="$_repo" exec bash "$_body" "$@"
