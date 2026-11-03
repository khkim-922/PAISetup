#!/bin/sh
# 조각 — 마크다운 결함. markdownlint-cli2 가 잰다.
#
# **담긴 .md 만 잰다.** 저장소 전체를 재면 내가 안 만진 문서가 무관한 커밋을 막는다. 트리 전체는 그 저장소의
# CI 가 다시 묻는다 — 이 조각은 CI 에서야 처음 빨개지는 일을 커밋 앞으로 당기는 자리다.
#
# 규칙 파일 — **저장소 것이 먼저다.** 뿌리에 `.markdownlint-cli2.*` 나 `.markdownlint.*` 가 있으면 도구가 제 손으로
#   찾고, 그 설정의 `ignores`(굳는 문서 같은 뺄 자리)도 실제 경로로 준 파일에 걸린다(실측 2026-11-03 · cli2 0.24.0).
#   없으면 전역 배포본(`.claude/markdownlint.global.jsonc`)을 준다.
#
# ⚠ **경로는 `:` 를 붙여 글자 그대로 넘기고 `--no-globs` 를 준다.** 이 도구는 인자를 글롭으로 읽어 `[` · `(` 가 든
#   이름을 다른 파일로 풀고, 설정의 `globs` 를 인자에 덧붙여 저장소 전체를 돈다.
#
# ⚠ **재는 것은 작업 트리 판이다.** 반쯤 스테이징하면 어긋난다 — 도구가 인덱스를 안 읽는다.
set -u

command -v markdownlint-cli2 >/dev/null 2>&1 || {
    printf '· markdownlint-cli2 가 없어 마크다운 검사를 건너뛴다.\n' >&2
    exit 2
}

# ⚠ **`core.quotePath=false` 가 있어야 비ASCII 이름이 온다** — 형제 조각 `encoding.sh` 와 같은 자리다.
staged_md="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACM |
             grep -E '\.(md|markdown)$' || true)"
[ -n "$staged_md" ] || exit 0

oldifs=$IFS
IFS='
'
set --
for f in $staged_md; do [ -f "$f" ] && set -- "$@" ":$f"; done
IFS=$oldifs
[ "$#" -gt 0 ] || exit 0

has_cfg=""
for _c in .markdownlint-cli2.jsonc .markdownlint-cli2.yaml .markdownlint-cli2.cjs .markdownlint-cli2.mjs \
          .markdownlint.jsonc .markdownlint.json .markdownlint.yaml .markdownlint.yml .markdownlint.cjs .markdownlint.mjs; do
    [ -f "$_c" ] && { has_cfg=1; break; }
done
CFG=""
if [ -z "$has_cfg" ]; then
    for _c in .claude/markdownlint.global.jsonc "$(dirname "$0")/../../.claude/markdownlint.global.jsonc"; do
        [ -f "$_c" ] && { CFG="$_c"; break; }
    done
fi

# ⚠ **도구가 「못 쟀다」로 지는 것과 문서가 어긋난 것은 다른 명제다.** cli2 는 `0` 깨끗 · `1` 결함 · `2` 설정 · 실행
#   오류다. 둘을 같이 1 로 세면 「마크다운 결함이 있다」는 거짓 문장과 함께 막는다.
if [ -n "$CFG" ]; then out="$(markdownlint-cli2 --no-globs --config "$CFG" "$@" 2>&1)"; rc=$?
else                   out="$(markdownlint-cli2 --no-globs "$@" 2>&1)";                rc=$?
fi
case "$rc" in
    0) ;;
    1) printf '✖ 마크다운 결함이 있다.\n' >&2
       printf '%s\n' "$out" | grep -E ':[0-9]+(:[0-9]+)? ' >&2 || printf '%s\n' "$out" | tail -n 20 >&2
       exit 1 ;;
    *) printf '· markdownlint-cli2 가 %s 로 졌다 — 문서가 어긋난 게 아니라 **못 쟀다**(설정·실행).\n' "$rc" >&2
       printf '%s\n' "$out" | tail -n 5 >&2
       exit 2 ;;
esac
exit 0
