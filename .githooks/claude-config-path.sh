# 설정 저장소가 이 기계 어디에 붙었나 — **한 자리에서만 잰다.** (sh 로 source 한다)
#
# 진본은 claude-config/.githooks/claude-config-path.sh 다. 각 저장소의 것은 deploy.ps1 이
# 뿌린 배포본이다 — 배포본을 고치면 다음 배포에 덮인다.
#
# 왜 한 자리인가: 재는 쪽이 둘이다 — 커밋 게이트(.githooks/ 의 몸통 · 조각)와 세션 진단
#   (.claude/hooks/session-start-body.sh). 목록이 갈리면 **게이트는 안 도는데 진단은 돈다고
#   말하게 되고**, 그 순간 부재가 통과로 읽힌다. 게이트가 없는 것보다 나쁜 자리다.
#
# 부르는 법:  . "$PROJECT_DIR/.githooks/claude-config-path.sh"
# 내는 것:    CONFIG_ROOT  설정 저장소가 붙은 자리 — 세션 기록·사내 환경 문서 (없으면 빈 문자열)
#             ADR_GEN      결정 목록 생성기 adr-index.sh          (없으면 빈 문자열)
#             GATES_HOME   게이트 러너(gates-run.sh)가 선 폴더      (없으면 빈 문자열 · 0064)
#
# ⚠ 둘은 따로 논다. PC 는 deploy.ps1 이 **스킬만** 홈에 뿌리므로 저장소가 안 붙어도
#   생성기는 있다. 리모트는 그 반대다 — 저장소를 통째로 붙여 그 안의 스킬을 쓴다.

# shellcheck shell=sh  # sh 몸통과 bash 세션 훅이 같이 읽는다 — 둘 다 받는 POSIX 로 잰다

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
# ⚠ 형제 저장소의 `.githooks/adr-index.sh` 사본은 걷었다(결정 0064) — 그 저장소들은 뒤의 둘로 선다.
#   첫 후보는 사본을 아직 든 옛 판 · 제 생성기를 든 저장소를 위해 남긴다. 남은 사본은 스킬과
#   **같은 출력을 내야 한다** — 갈리면 한쪽에서 통과한 색인이 다른 쪽에서 걸린다.
ADR_GEN=""
_skill="skills/adr-and-source-together/scripts/adr-index.sh"
for _g in "$PROJECT_DIR/.githooks/adr-index.sh" \
          "$HOME/.claude/$_skill" ${CONFIG_ROOT:+"$CONFIG_ROOT/.claude/$_skill"}; do
    # shellcheck disable=SC2034 # 부른 쪽이 읽는 출력이다(머리말 「내는 것」)
    [ -f "$_g" ] && { ADR_GEN="$_g"; break; }
done

# 게이트 러너가 선 자리 (0064) — **git 이 부른 몸통 곁 → 붙은 claude-config → 홈 씨앗.** 형제 저장소는
# 러너 · 조각 사본을 안 들고 몸통(문지기)만 들어, 몸통이 이 값으로 러너를 찾는다. 세션 진단도 같은
# 값을 본다 — 둘이 따로 찾으면 게이트는 안 도는데 진단은 돈다고 말하게 된다(위 「왜 한 자리인가」).
# ⚠ **몸통 곁**(GATES_CALLER — 몸통이 제 자리를 넘긴다)은 그것이 **이 저장소 제 `.githooks` 가 아닐 때만**
#   본다. `core.hooksPath` 를 claude-config 쪽 절대경로로 건 자리가 그것이다. 제 `.githooks` 를 후보로
#   받으면 형제에 남은 옛 러너 사본이 잡혀 조각을 저장소 안에서만 찾게 된다 — claude-config 자신은
#   어차피 둘째 후보(CONFIG_ROOT)로 잡힌다.
# ⚠ **계약 표식(`# gates-contract: 2`)이 있는 러너만 받는다.** 설치된 옛 홈 씨앗의 러너는 조각을 저장소
#   안에서만 찾아, 조각이 없는 형제의 커밋을 전부 막는다. 표식이 없으면 없는 것으로 보고 다음으로 간다 —
#   다 없으면 몸통이 「러너를 못 찾았다」고 알리고 지나간다.
# ⚠ 홈 씨앗은 설치기가 모든 PC 에 깐다(`~/.claude/seeds/config-repo/`) — claude-config 가 없는
#   동료 PC 가 이 자리로 선다. 세션 훅 문지기가 몸통을 찾는 차례와 같다(0063).
_gates_ok() { [ -f "$1/gates-run.sh" ] && grep -q '^# gates-contract: [2-9]' "$1/gates-run.sh" 2>/dev/null; }
_h_own="$(cd "$PROJECT_DIR/.githooks" 2>/dev/null && pwd -P)"
GATES_HOME=""
if [ -n "${GATES_CALLER:-}" ] && [ "$(cd "$GATES_CALLER" 2>/dev/null && pwd -P)" != "$_h_own" ] &&
   _gates_ok "$GATES_CALLER"; then
    GATES_HOME="$(cd "$GATES_CALLER" && pwd)"
else
    for _h in ${CONFIG_ROOT:+"$CONFIG_ROOT/.githooks"} "$HOME/.claude/seeds/config-repo/.githooks"; do
        # shellcheck disable=SC2034 # 부른 쪽이 읽는 출력이다(머리말 「내는 것」)
        _gates_ok "$_h" && { GATES_HOME="$(cd "$_h" && pwd)"; break; }
    done
fi

unset _d _g _h _h_own _skill
