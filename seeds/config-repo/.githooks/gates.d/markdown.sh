#!/bin/sh
# 조각 — 마크다운 서식. markdownlint-cli2 가 잰다.
#
# **담긴 .md 만 잰다.** 저장소 전체를 재면 내가 안 만진 파일이 무관한 커밋을 막고,
# 그 자리에서 `--no-verify` 가 습관이 된다.
#
# ⚠ `--no-globs` 가 있어야 인자가 산다. 설정(`.markdownlint-cli2.jsonc`)의 `globs` 가
#   명령줄 인자를 이기기 때문에, 빼면 준 파일과 무관하게 저장소를 통째로 잰다(실측).
#   제외 목록(`ignores`)은 `--no-globs` 를 줘도 그대로 살아서, 재료·생성물은 인자로
#   넘겨도 「0 files」로 빠진다.
#
# ⚠ **재는 것은 작업 트리 판이다.** 반쯤 스테이징하면 어긋난다 — 도구가 인덱스를 안 읽는다.
#
# ⚠ **설정이 `extends` 로 `node_modules` 를 가리키면 이 조각이 못 선다.** 전역 설치는
#   `markdownlint` 를 `markdownlint-cli2/node_modules/` 안에 중첩해 두므로(실측
#   2026-09-11) 저장소 기준 상대경로가 안 풀린다. 프리셋을 쓰려면 저장소가 node 축을
#   따로 지거나, 설정이 기본값 위에 규칙만 적어야 한다.
set -u

command -v markdownlint-cli2 >/dev/null 2>&1 || {
    printf '· markdownlint-cli2 가 없어 마크다운 검사를 건너뛴다.\n' >&2
    exit 2
}

staged_md="$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.md$' || true)"
[ -n "$staged_md" ] || exit 0

# 목록을 위치 인자로 세운다 — 줄바꿈으로만 가른다.
# ⚠ `tr` 로 NUL 을 만들지 않는다: 이스케이프가 파일에 제어문자로 굳으면 훅이 바이너리가
#   되어 `grep` 도 `diff` 도 안 읽힌다(실측).
oldifs=$IFS
IFS='
'
set --
for f in $staged_md; do [ -f "$f" ] && set -- "$@" "$f"; done
IFS=$oldifs
[ "$#" -gt 0 ] || exit 0

out="$(markdownlint-cli2 --no-globs "$@" 2>&1)" || {
    printf '✖ 마크다운 서식이 어긋났다.\n' >&2
    printf '%s\n' "$out" | grep -E ':[0-9]+' >&2 || printf '%s\n' "$out" | tail -n 20 >&2
    exit 1
}
exit 0
