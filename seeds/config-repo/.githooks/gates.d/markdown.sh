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

# ⚠ **`core.quotePath=false` 가 있어야 비ASCII 이름이 온다.** 기본값(참)에서 git 은
#   `"docs/\355\225\234\352\270\200.md"` 꼴로 **싸서** 내고, 그러면 줄 끝이 `"` 라 확장자
#   패턴에 안 걸리고 `[ -f ]` 도 거짓이라 **한 줄도 안 말하고 빠진다.** 우리 문서는 한국어라
#   그 이름이 드물지 않다 — 실측 2026-09-11: 한 형제 저장소에 그런 이름의 `.md` 가 322개였고,
#   같은 위반을 ASCII 이름이면 막고 한글 이름이면 통과했다.
staged_md="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACM |
             grep -E '\.md$' || true)"
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

# ⚠ **도구가 「못 쟀다」로 지는 것과 문서가 어긋난 것은 다른 명제다.** markdownlint-cli2 는
#   위반에 1, **제 오류에 2 이상**을 낸다(설정을 못 읽는 자리가 그렇다 — 배포가 반쪽만 닿으면
#   난다). 둘을 같이 1 로 세면 **「마크다운 서식이 어긋났다」는 거짓 문장**과 함께 막고,
#   다음 사람이 엉뚱한 파일을 뒤진다.
out="$(markdownlint-cli2 --no-globs "$@" 2>&1)"; rc=$?
case "$rc" in
    0) ;;
    1) printf '✖ 마크다운 서식이 어긋났다.\n' >&2
       printf '%s\n' "$out" | grep -E ':[0-9]+' >&2 || printf '%s\n' "$out" | tail -n 20 >&2
       exit 1 ;;
    *) printf '· markdownlint 가 %s 로 졌다 — 서식이 어긋난 게 아니라 **못 쟀다**.\n' "$rc" >&2
       printf '%s\n' "$out" | tail -n 5 >&2
       exit 2 ;;
esac

# ⚠ **담긴 것이 전부 제외 목록에 들면 한 장도 안 잰다** — 그 0 이 「전부 통과」로 읽히면
#   안 된다. 결정 기록만 담은 커밋이 이 저장소들의 일상 커밋 꼴이라 드물지 않다.
printf '%s\n' "$out" | grep -q 'Linting: 0 files' &&
    printf '· 담긴 .md 가 전부 제외 목록에 들어 **한 장도 안 쟀다**.\n' >&2
exit 0
