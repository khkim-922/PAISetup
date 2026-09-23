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
    PROJECT_DIR="$_repo"
    . "$_repo/.githooks/claude-config-path.sh"
  fi
  for _b in ${CONFIG_ROOT:+"$CONFIG_ROOT/.claude/hooks/session-start-body.sh"} \
            "$HOME/.claude/seeds/config-repo/.claude/hooks/session-start-body.sh"; do
    [ -f "$_b" ] && { _body="$_b"; break; }
  done
fi

if [ -z "$_body" ]; then
  [ -d "$_repo/.githooks" ] && git -C "$_repo" config core.hooksPath .githooks 2>/dev/null
  echo "$(basename "$_repo"): ⚠ 세션 훅 몸통을 못 찾았다 — claude-config 가 이 PC(또는 이 세션)에 안 붙었고 홈 씨앗도 없다. 커밋 게이트 배선만 걸었고, 도구 설치 · 진단은 안 돌았다. claude-config 를 함께 붙이거나 설치기를 다시 돌린다"
  exit 0
fi

SESSION_START_REPO="$_repo" exec bash "$_body" "$@"
