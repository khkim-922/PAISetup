#!/bin/sh
# 조각 — 빌려 온 사본이 진본과 같은가.
#
# 씨앗에서 빌려 온 사본(머리말에 「빌려 온 자다」가 있는 파일)과 `.githooks/` 배포본이
# 진본과 어긋나지 않았나를 `borrowed_check.py` 로 잰다.
#
# 이 저장소(claude-config)에서는 게이트웨이 가족 둘을 물고,
# 형제 저장소(atelier 등)에서는 `_check/` 사본 22장과 `.githooks/` 조각들을 문다.
#
# ⚠ 담긴 것에 `_check/` · `.githooks/` · `seeds/` 가 있을 때만 돈다 (repo-copies.sh · dist.sh 와 같은 자).
# ⚠ 형제가 없는 기계에서는 2 (안 잰 자리)로 말하고 넘어간다.
set -u

# ── 담긴 것 확인 ─────────────────────────────────────────────────────────────
staged="$(git -c core.quotePath=false diff --cached --name-only 2>/dev/null || true)"
[ -n "$staged" ] || exit 0

nl='
'
has_target=0
case "$nl$staged$nl" in
    *"${nl}_check/"*|*"${nl}.githooks/"*|*"${nl}seeds/"*) has_target=1 ;;
esac

[ "$has_target" -eq 1 ] || exit 0

# ── 파이썬 찾기 ─────────────────────────────────────────────────────────────
# 파이썬은 **불러 보고** 고른다 — 씨앗의 `_py.sh` 가 그 자다(환경변수 PY → .venv → 시스템 · 각각 `-c ""` 로 확인).
# 존재(`command -v`)로 고르면 윈도우의 스토어 `python3` 껍데기를 잡아 49 로 죽는다 — 씨앗 커밋마다 막혔다(0028 · #86).
# 자리는 셋 — 씨앗 진본을 든 저장소 · 씨앗을 받아 `_check/` 에 둔 저장소 · 홈 씨앗. 없으면 「못 쟀다」(2).
_py_sh=""
for _cand in seeds/check/_check/_py.sh _check/_py.sh "$HOME/.claude/seeds/check/_check/_py.sh"; do
    [ -f "$_cand" ] && { _py_sh="$_cand"; break; }
done
[ -n "$_py_sh" ] || {
    printf '· 파이썬을 고를 _py.sh 가 없어 borrowed 검사를 못 쟀다(홈 씨앗이 안 깔렸다 — deploy.ps1).\n' >&2
    exit 2
}
# shellcheck source=seeds/check/_check/_py.sh # 자리는 위에서 고르고, 진본은 이것이다
. "$_py_sh"     # $PY 가 선다 — 못 고르면 저쪽이 「python 이 없다」 한 줄과 2 로 나간다
_py="$PY"

# ── 실행할 자리 결정 ─────────────────────────────────────────────────────────
if [ -f "seeds/check/_check/borrowed_check.py" ] && [ -d "seeds/gateway/_check" ]; then
    # claude-config 저장소 제 나무
    out="$("$_py" -X utf8 seeds/check/_check/borrowed_check.py seeds/gateway/_check --seeds seeds 2>&1)"
    rc=$?
elif [ -f "_check/borrowed_check.py" ]; then
    # 형제 저장소 (배포본이 도는 자리)
    out="$("$_py" -X utf8 _check/borrowed_check.py 2>&1)"
    rc=$?
else
    # 잴 자리가 없는 저장소
    exit 0
fi

if [ "$rc" -eq 0 ]; then
    exit 0
elif [ "$rc" -eq 2 ]; then
    printf '%s\n' "$out" >&2
    exit 2
else
    printf '%s\n' "$out" >&2
    exit 1
fi
