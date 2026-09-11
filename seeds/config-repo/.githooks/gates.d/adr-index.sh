#!/bin/sh
# 조각 — 결정 목록(INDEX.md)이 결정 기록의 머리말과 어긋났나.
#
# 색인은 결정 파일 **머리말**의 파생물이다 — 생성기가 읽는 것은 number·title·status·
# date·superseded_by 다섯 줄뿐이다. 그래서 *"색인이 이 커밋에 담겼나"* 로 물으면
# 본문·좌표만 고친 커밋은 **통과할 길이 없다.** 색인이 한 글자도 안 바뀌니 git 이
# 담아줄 것이 없다. 그 자리에서 `--no-verify` 가 습관이 된다.
#
# 그래서 무는 자리를 「담겼나」가 아니라 「파생 관계가 성립하나」로 옮긴다.
#
#   생성기가 있으면   담겼든 아니든, 이 커밋에 담길 색인이 생성기 출력과 같은가
#   없으면           머리말이 실제로 바뀐 결정 파일이 있을 때만 색인 동반을 요구한다
#
# 아래쪽은 git 만 쓴다 — 생성기는 설정 저장소의 스킬이라 안 붙은 자리가 있고, 거기서
# 검사가 통째로 꺼지면 열화가 기본값이 된다.
set -u

DEC="docs/decisions"
[ -d "$DEC" ] || exit 0

# 생성기가 어디 있나는 여기서 안 정한다 — 세션 진단과 같은 자리를 봐야 한다.
# 목록이 갈리면 **게이트는 안 도는데 진단은 돈다고 말하게 되고**, 그 순간 부재가
# 통과로 읽힌다.
ADR_GEN=""
[ -f ".githooks/claude-config-path.sh" ] && . "./.githooks/claude-config-path.sh"

# ⚠ **`core.quotePath=false` 가 있어야 비ASCII 이름이 온다.** 기본값(참)에서 git 은
#   `"docs/\355\225\234\352\270\200.md"` 꼴로 **싸서** 내고, 그러면 줄 끝이 `"` 라 확장자
#   패턴에 안 걸리고 `[ -f ]` 도 거짓이라 **한 줄도 안 말하고 빠진다.** 우리 문서는 한국어라
#   그 이름이 드물지 않다 — 실측 2026-09-11: 한 형제 저장소에 그런 이름의 `.md` 가 322개였고,
#   같은 위반을 ASCII 이름이면 막고 한글 이름이면 통과했다.
staged_adr="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACM |
              grep -E "^$DEC/[0-9]{4}-.*\.md$" || true)"
[ -n "$staged_adr" ] || exit 0

# 머리말 — 여는 `---` 다음 첫 닫는 `---` 까지. 경계 판정을 생성기의 awk 와 같은 모양으로
# 둔다. 두 벌이면 어디까지가 머리말인지를 둘이 다르게 볼 수 있다.
adr_head() { awk '/^---[[:space:]]*$/ { fm++; if (fm == 2) exit; next } fm == 1'; }

if [ -n "$ADR_GEN" ]; then
    # `:경로` 는 이 커밋에 담길 판이다 — 스테이징했으면 그것, 안 했으면 HEAD 판.
    # ⚠ 생성기는 작업 트리를 읽는다. 결정 파일을 반쯤만 스테이징하면 어긋난다.
    staged="$(mktemp)"; fresh="$(mktemp)"
    git show ":$DEC/INDEX.md" 2>/dev/null | tr -d '\r' > "$staged"
    sh "$ADR_GEN" "$DEC"                  | tr -d '\r' > "$fresh"
    if ! diff -q "$staged" "$fresh" >/dev/null 2>&1; then
        printf '✖ %s/INDEX.md 가 결정 기록의 머리말과 어긋났다 — 손으로 고쳤거나 낡았다.\n' "$DEC" >&2
        printf '  색인을 다시 만들어 함께 담는다:\n' >&2
        printf '    sh "%s" %s > %s/INDEX.md\n' "$ADR_GEN" "$DEC" "$DEC" >&2
        printf '    git add %s/INDEX.md\n' "$DEC" >&2
        diff "$staged" "$fresh" | head -n 12 >&2
        rm -f "$staged" "$fresh"
        exit 1
    fi
    rm -f "$staged" "$fresh"
    exit 0
fi

# 생성기가 없는 자리 — 약하게라도 잰다. **안 쟀다고 말하고 간다.**
printf '· 색인 생성기가 없어 머리말 대조로 갈음한다 (설정 저장소를 붙이면 전부 본다).\n' >&2
# 머리말이 바뀐 첫 파일. 하나라도 있으면 색인이 낡는다.
# 새 파일은 HEAD 판이 없어 빈 머리말이 되고, 그래서 「바뀜」으로 잡힌다.
head_changed="$(printf '%s\n' "$staged_adr" | while IFS= read -r f; do
    old="$(git show "HEAD:$f" 2>/dev/null | tr -d '\r' | adr_head)"
    new="$(git show ":$f"     2>/dev/null | tr -d '\r' | adr_head)"
    [ "$old" = "$new" ] || { printf '%s' "$f"; break; }
done)"
if [ -n "$head_changed" ] && ! git diff --cached --name-only | grep -qx "$DEC/INDEX.md"; then
    printf '✖ 결정 기록의 머리말이 바뀌었는데 %s/INDEX.md 가 이 커밋에 없다.\n' "$DEC" >&2
    printf '  바뀐 자리: %s\n' "$head_changed" >&2
    printf '  adr-and-source-together 스킬의 scripts/adr-index.sh 로 다시 만들어 함께 담는다.\n' >&2
    exit 1
fi
exit 0
