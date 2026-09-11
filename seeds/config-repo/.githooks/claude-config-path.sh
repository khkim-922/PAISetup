# 설정 저장소가 이 기계 어디에 붙었나 — **한 자리에서만 잰다.** (sh 로 source 한다)
#
# 진본은 claude-config/.githooks/claude-config-path.sh 다. 각 저장소의 것은 deploy.ps1 이
# 뿌린 배포본이다 — 배포본을 고치면 다음 배포에 덮인다.
#
# 왜 한 자리인가: 재는 쪽이 둘이다 — 커밋 게이트(.githooks/gates.d/)와 세션 진단
#   (.claude/hooks/session-start.sh). 목록이 갈리면 **게이트는 안 도는데 진단은 돈다고
#   말하게 되고**, 그 순간 부재가 통과로 읽힌다. 게이트가 없는 것보다 나쁜 자리다.
#
# 부르는 법:  . "$PROJECT_DIR/.githooks/claude-config-path.sh"
# 내는 것:    CONFIG_ROOT  설정 저장소가 붙은 자리 — 세션 기록·사내 환경 문서 (없으면 빈 문자열)
#             ADR_GEN      결정 목록 생성기 adr-index.sh          (없으면 빈 문자열)
#
# ⚠ 둘은 따로 논다. PC 는 deploy.ps1 이 **스킬만** 홈에 뿌리므로 저장소가 안 붙어도
#   생성기는 있다. 리모트는 그 반대다 — 저장소를 통째로 붙여 그 안의 스킬을 쓴다.

# PROJECT_DIR 이 안 서 있는 자리에서도 선다 — 부르는 쪽을 믿지 않는다.
[ -n "${PROJECT_DIR:-}" ] || PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# ⚠ **이름이 아니라 지문으로 확인한다.** 이름만 보면 그 이름의 빈 폴더도 잡히고, 반대로
#   클론 이름이 다른 자리(리모트가 소문자로 바꾸는 자리 — 실측 2026-09-11)는 못 잡는다.
#   세션 진단이 쓰는 것과 같은 지문이다: 뿌리는 자(deploy.ps1)와 기록(memory/)이 같이 있나.
# ⚠ **자기 자신이 첫 후보다.** 이 저장소는 역할이 둘이라(전역 자산의 진본 · 게이트를 쓰는
#   자 — 결정 0035) 제 안에서 이 스크립트가 돌 때 형제를 찾으면 영영 못 찾는다.
CONFIG_ROOT=""
for _d in "$PROJECT_DIR" \
          "$(dirname "$PROJECT_DIR")/claude-config" \
          /workspace/claude-config \
          "$HOME/claude-config"; do
    # 자기 자신  — 역할이 둘인 저장소
    # 형제       — 저장소 둘을 나란히 clone 한 자리
    # /workspace — 리모트. add_repo 가 여기 붙인다(실측 2026-08-14). 세션 루트와 다른
    #              자리라 형제로만 찾으면 리모트에서 영영 못 찾는다
    # $HOME      — 손으로 홈에 clone 한 자리
    [ -f "$_d/deploy.ps1" ] && [ -d "$_d/memory" ] && { CONFIG_ROOT="$_d"; break; }
done

# 생성기는 **이 저장소가 든다.** 이 저장소의 커밋 게이트가 도는 데 딴 저장소가 필요하면
# 그 게이트는 구조적으로 늘 꺼져 있게 된다 — 붙이는 것은 셸이 못 하는 일이라
# (`add_repo` 는 도구 호출이다) 훅을 몇 번 다시 돌려도 안 고쳐진다.
# 뒤의 둘은 남긴다: 옛 자리로 도는 세션이 갑자기 검사를 잃지 않게.
# ⚠ `.githooks/adr-index.sh` 는 설정 저장소의 스킬과 **같은 출력을 내야 한다** —
#   갈리면 한쪽에서 통과한 색인이 다른 쪽에서 걸린다. 본문을 손보지 말 것.
ADR_GEN=""
_skill="skills/adr-and-source-together/scripts/adr-index.sh"
for _g in "$PROJECT_DIR/.githooks/adr-index.sh" \
          "$HOME/.claude/$_skill" ${CONFIG_ROOT:+"$CONFIG_ROOT/.claude/$_skill"}; do
    [ -f "$_g" ] && { ADR_GEN="$_g"; break; }
done

unset _d _g _skill
