#!/bin/sh
# 조각 — 파이썬 결함. ruff 가 잰다.
#
# **담긴 .py 만 잰다.** 저장소 전체를 재면 내가 안 만진 파일이 무관한 커밋을 막고,
# 그 자리에서 `--no-verify` 가 습관이 된다.
#
# ⚠ **재는 것은 결함 부류뿐이다** — 정의 안 된 이름 · 안 쓰는 import · 루프 변수를 붙든 함수 ·
#   `from` 없는 되던짐 · 문법 오류. 무엇을 켜나는 전역 판정(`.claude/ruff.global.toml`)이 들고,
#   왜 그렇게 좁은지의 실측도 거기 있다. 문체 규칙(줄 길이 · 정렬)을 켜면 게이트가 글을
#   고치게 된다 — 이 조각의 몫이 아니다.
#
# ⚠ `--no-cache` 가 있어야 저장소에 `.ruff_cache/` 가 안 생긴다. 조각이 커밋마다 폴더를 만들면
#   그것이 곧 추적 안 된 쓰레기고, 무시 목록에 올리면 저장소마다 손사본이다.
#
# ⚠ **재는 것은 작업 트리 판이다.** 반쯤 스테이징하면 어긋난다 — 도구가 인덱스를 안 읽는다.
set -u

command -v ruff >/dev/null 2>&1 || {
    printf '· ruff 가 없어 파이썬 검사를 건너뛴다.\n' >&2
    exit 2
}

# ⚠ **`core.quotePath=false` 가 있어야 비ASCII 이름이 온다** — 마크다운 조각과 같은 자리다.
staged_py="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACM |
             grep -E '\.py$' || true)"
[ -n "$staged_py" ] || exit 0

oldifs=$IFS
IFS='
'
set --
for f in $staged_py; do [ -f "$f" ] && set -- "$@" "$f"; done
IFS=$oldifs
[ "$#" -gt 0 ] || exit 0

# 규칙 파일 — **저장소 것이 먼저다.** 저장소가 뿌리에 제 설정을 두면 그것이 진본이고, 전역
#   배포본은 안 둔 저장소를 위한 자리다. 도구는 뿌리 설정을 제 손으로 찾으므로 저장소 것이
#   있으면 아무것도 안 넘긴다. `pyproject.toml` 은 `[tool.ruff` 절이 있을 때만 설정이다.
#   전역 배포본도 저장소 것이 먼저고, 없으면 이 조각이 선 자리의 `.claude/` 를 본다 — 까닭은
#   마크다운 조각(`markdown.sh`)의 같은 자리가 든다.
CFG=""
if [ ! -f ruff.toml ] && [ ! -f .ruff.toml ] &&
   ! { [ -f pyproject.toml ] && grep -q '^\[tool\.ruff' pyproject.toml; }; then
    for _c in .claude/ruff.global.toml "$(dirname "$0")/../../.claude/ruff.global.toml"; do
        [ -f "$_c" ] && { CFG="$_c"; break; }
    done
fi

# ⚠ **도구가 「못 쟀다」로 지는 것과 코드가 어긋난 것은 다른 명제다.** 실측 2026-09-12 · ruff 0.16.7:
#   `0` 깨끗 · `1` 위반(문법 오류 · 없는 파일 E902 도 여기) · `2` 설정 오류 · 모르는 규칙.
#   둘을 같이 1 로 세면 「파이썬 결함이 있다」는 거짓 문장과 함께 막고, 다음 사람이 엉뚱한
#   파일을 뒤진다.
if [ -n "$CFG" ]; then out="$(ruff check --no-cache --output-format concise --config "$CFG" "$@" 2>&1)"; rc=$?
else                   out="$(ruff check --no-cache --output-format concise "$@" 2>&1)";                rc=$?
fi
case "$rc" in
    0) ;;
    1) printf '✖ 파이썬 결함이 있다.\n' >&2
       printf '%s\n' "$out" | grep -E ':[0-9]+:[0-9]+:' >&2 || printf '%s\n' "$out" | tail -n 20 >&2
       exit 1 ;;
    *) printf '· ruff 가 %s 로 졌다 — 코드가 어긋난 게 아니라 **못 쟀다**(설정·규칙).\n' "$rc" >&2
       printf '%s\n' "$out" | tail -n 5 >&2
       exit 2 ;;
esac
exit 0
