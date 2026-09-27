#!/bin/sh
# 조각 — 저장소가 선언한 게이트 목록을 돈다. `[pre-push]` 절에 켠다.
#
# 목록의 진본은 저장소의 검사 지도(`_check/README.md` 의 게이트 절)고, 그것을 파서 돌리는 손은 저장소가
# 빌려 든 `_check/map_check.py --run-gates` 다 — 원격 CI 가 도는 목록과 같은 자리에서 판다. 이 조각은
# 목록을 모르고 옮겨 적지도 않는다. 옮겨 적으면 새 게이트가 한쪽에서만 조용히 빠진다.
#
# ⚠ **판정 계약은 CI 와 같다** — 러너가 목록을 모아 1(어긋남) · 2(못 쟀다) · 0 을 낸다. 목록에 있는데
#   파일이 없는 게이트는 어긋남이다. 2 는 막지 않고 「못 쟀다」로 이름을 댄다(0064 · 몸통 러너의 계약).
# ⚠ **돌린 기록은 파일로 남기고 화면에는 판정 줄만 낸다** — 게이트 수십 개의 출력을 푸시 창에 다
#   쏟으면 빨간 줄이 그 속에 묻힌다. 빨강이면 기록 자리를 댄다. 기록은 **저장소마다 한 자리**를 덮어써
#   푸시마다 임시 파일이 쌓이지 않는다.
# ⚠ **재는 것은 작업 트리다.** 커밋 안 한 변경이 있으면 미는 커밋과 다른 판을 잰 것이라 그렇다고 말한다.
# ⚠ **서버를 띄워야 도는 화면 검사는 이 목록 밖이다** — 목록이 게이트 절만 들고, 원격 CI 에도 없다.
set -u

MAP_CHECK="_check/map_check.py"
[ -f "$MAP_CHECK" ] || {
    printf '· 저장소 게이트 — %s 가 없어 목록을 못 판다. 이 저장소는 [pre-push] 의 repo-gates 를 끈다.\n' "$MAP_CHECK" >&2
    exit 2
}
# 목록을 돌리는 손은 씨앗의 새 판에서 왔다 — 옛 사본은 그 낱말을 모르고 폴더 이름으로 읽어 2 로 나간다.
grep -q -- '--run-gates' "$MAP_CHECK" || {
    printf '· 저장소 게이트 — %s 가 옛 판이라 목록을 돌리는 손(--run-gates)이 없다.\n' "$MAP_CHECK" >&2
    printf '  씨앗에서 다시 받는다:  python -X utf8 _check/borrowed_check.py --receive\n' >&2
    exit 2
}

# ── 파이썬 찾기 — `borrowed.sh` 와 같은 자(씨앗의 `_py.sh`)가 고른다 ────────────────────
_py_sh=""
for _cand in _check/_py.sh seeds/check/_check/_py.sh "$HOME/.claude/seeds/check/_check/_py.sh"; do
    [ -f "$_cand" ] && { _py_sh="$_cand"; break; }
done
[ -n "$_py_sh" ] || {
    printf '· 저장소 게이트 — 파이썬을 고를 _py.sh 가 없어 못 쟀다(홈 씨앗이 안 깔렸다 — deploy.ps1).\n' >&2
    exit 2
}
# shellcheck source=seeds/check/_check/_py.sh # 자리는 위에서 고르고, 진본은 이것이다
. "$_py_sh"     # $PY 가 선다 — 못 고르면 저쪽이 「python 이 없다」 한 줄과 2 로 나간다

[ -z "$(git status --porcelain --untracked-files=no 2>/dev/null)" ] ||
    printf '· 저장소 게이트 — 커밋 안 한 변경이 있다. 미는 커밋이 아니라 작업 트리를 잰다.\n' >&2

log="${TMPDIR:-/tmp}/repo-gates-$(basename "$PROJECT_DIR").log"
: > "$log" 2>/dev/null || {
    printf '· 저장소 게이트 — 기록 자리(%s)에 못 쓴다. 못 쟀다.\n' "$log" >&2
    exit 2
}
printf '· 저장소 게이트 — 선언된 목록을 돈다 (몇 분 걸린다 · 기록: %s)\n' "$log" >&2
_t0=$(date +%s)
"$PY" -X utf8 "$MAP_CHECK" --run-gates >"$log" 2>&1
rc=$?
_dt=$(( $(date +%s) - _t0 ))

# 러너가 스스로 낸 판정 줄만 올린다 — 어긋남 · 못 쟀다 · 모음 두 줄. 줄 꼴은 러너(`run_gates`)가 든다.
grep -E '^(❌ |⚠ .* — 못 쟀다|⚠ 못 쟀다 — |게이트 [0-9]+개 · |[[:space:]]+· 못 쟀다 [0-9]+개|[[:space:]]+· 모두 [0-9]+초)' "$log" >&2
case "$rc" in
    0) printf '· 저장소 게이트 — 통과 (%s초)\n' "$_dt" >&2
       exit 0 ;;
    2) printf '· 저장소 게이트 — 못 잰 것이 있다 (%s초 · 기록: %s)\n' "$_dt" "$log" >&2
       exit 2 ;;
    *) printf '✖ 저장소 게이트가 어긋났다 (%s초) — 전문: %s\n' "$_dt" "$log" >&2
       exit 1 ;;
esac
