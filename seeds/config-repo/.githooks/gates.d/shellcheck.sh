#!/bin/sh
# 조각 — 담긴 셸 스크립트의 **정적 결함**. shellcheck 가 잰다(#91 ③).
#
# 왜 이것인가 — 문법 조각(`shell-syntax.sh`)은 파서가 거부하는 것만 잡는다. 인용 누락 · `set -u` 아래
#   빈 변수 · sh 파일에 든 bash 전용 문법 · 빈 값이면 `/` 가 되는 `rm -rf "$x/…"` 는 파서를 지나가서
#   **돌려 봐야, 그것도 운 나쁜 값이 올 때만** 드러난다. 그 부류를 담는 자리에서 잡는다.
#
# ⚠ **막는 것은 `warning` 이상이다.** `info` · `style` 은 대부분 일부러 쓴 자리다(작은따옴표 안의 `$` 를
#   글자로 찍는 것 등) — 그것까지 막으면 억제 주석이 코드보다 많아지거나 `--no-verify` 가 습관이 된다.
# ⚠ **일부러 쓴 자리는 억제 주석으로 까닭과 함께 든다:**  `# shellcheck disable=SC2086 # 까닭`
#   까닭 앞에 `#` 를 한 번 더 둔다 — `disable=SC2086 — 까닭` 꼴은 shellcheck 가 지시문 오류(SC1125)로 받는다.
#   ⚠ 거꾸로 **주석 줄이 그 도구 이름으로 시작하면** 지시문으로 읽혀 오류(SC1073)가 난다 — 문장을
#   다른 낱말로 시작한다.
set -u
# 이름에 `*` 가 들어도 파일 이름 확장으로 부풀지 않게.
set -f

command -v shellcheck >/dev/null 2>&1 || {
    printf '· shellcheck 가 없어 셸 정적 검사를 건너뛴다.\n' >&2
    exit 2
}

# ⚠ **`core.quotePath=false` · `R` 포함 · 줄바꿈으로만 가르기** — 까닭은 문법 조각의 같은 자리가 든다.
STAGED="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR)"
[ -n "$STAGED" ] || exit 0

FAIL=0; CANT=0

oldifs=$IFS
IFS='
'
for f in $STAGED; do
  IFS=$oldifs
  case "$f" in
    *.sh) ;;
    *) IFS='
'; continue ;;
  esac

  # ⚠ **작업 트리가 아니라 담긴 판을 잰다** — 문법 조각과 같은 까닭이다. 표준 입력으로 먹이면
  #   도구가 셔뱅을 읽어 방언을 고른다(실측 0.11.0).
  # ⚠ **셔뱅도 `shell=` 지시문도 없으면 bash 로 잰다** — 점으로 읽히는 조각이라 어느 셸이 읽나가
  #   부르는 쪽에 있고, 거짓 빨강을 안 내는 쪽을 고른다(문법 조각과 같은 판단). 지시문이 있으면
  #   `-s` 를 안 준다: `-s` 가 지시문을 덮는다(실측 0.11.0).
  src="$(git show ":$f" 2>/dev/null)"
  set --
  case "$(printf '%s\n' "$src" | head -n 1)" in
    '#!'*) ;;
    *) printf '%s\n' "$src" | grep -q '^#[[:space:]]*shellcheck[[:space:]].*shell=' || set -- -s bash ;;
  esac

  out="$(printf '%s\n' "$src" | shellcheck -S warning -f gcc "$@" - 2>&1)"; rc=$?
  # 종료코드(shellcheck 0.11.0): 0 깨끗 · 1 결함 · 그 밖은 못 쟀다(2 읽기 실패 · 3·4 옵션 오류).
  case "$rc" in
    0) ;;
    1) printf '%s\n' "$out" | sed "s|^-:|$f:|" >&2
       FAIL=1 ;;
    *) printf '· shellcheck 가 %s 로 졌다 — %s 의 셸이 어긋난 게 아니라 **못 쟀다**.\n' "$rc" "$f" >&2
       printf '%s\n' "$out" | tail -n 3 >&2
       CANT=1 ;;
  esac
  IFS='
'
done
IFS=$oldifs

if [ "$FAIL" != 0 ]; then
  printf '  셸 정적 결함 — 일부러 쓴 자리면 그 줄 위에 `# shellcheck disable=SCxxxx # 까닭` 을 단다.\n' >&2
  exit 1
fi
[ "$CANT" = 0 ] || exit 2
exit 0
