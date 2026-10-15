#!/bin/sh
# 조각 — 바뀐 셸 스크립트가 **문법으로 서고 정적 결함이 없나.** shellcheck 가 잰다(#91 ① ③).
#
# 층 — 만드는 사람의 흐름
# 걷는 조건 — 저장소에 담기는 `.sh` 가 사라지거나, shellcheck 가 공유 전에 다른 자리에서 늘 돌면 걷는다
#
# 왜 이것인가 — 깨진 셸은 **깨졌다고 말하지 않고 반쯤 돈다.** 세션 훅 몸통은 모든 저장소 · 모든 PC 의
#   세션 시작에서 돌고, 게이트 조각(`gates.d/*.sh`)이 문법 오류로 죽으면 러너가 2 를 「못 쟀다」로 받아
#   **모든 형제에서** 그 검사가 빠진다(결정 0064). 인용 누락 · `set -u` 아래 빈 변수 · sh 파일에 든 bash
#   전용 문법 · 빈 값이면 `/` 가 되는 `rm -rf "$x/…"` 는 파서를 지나가서 **돌려 봐야, 그것도 운 나쁜 값이
#   올 때만** 드러난다. 깨진 셸이 남의 PC 에 닿는 길은 공유 · 배포 뒤라, 늦어도 공유 전에 잡는다.
#
# 어느 문에 서나는 저장소 선언이 정한다 — 커밋 문이면 **담긴 판**을, 푸시 문이면 **미는 판**(러너가 준 바뀐 경로의
#   작업 나무 판)을 잰다. 푸시 판에서 러너가 바뀐 경로를 못 줬으면(올라갈 가지가 없다 등) 추적하는 `.sh` 를 다 잰다 —
#   러너의 「모르면 다 띄운다」와 같은 뜻이다.
#
# 재는 자 — shellcheck 가 있으면 그것 하나다. 파서가 거부하는 것은 shellcheck 의 `error` 판정으로 오므로
#   (안 닫힌 `if` · `case` · 괄호 · 따옴표 · 중괄호 — 0.11.0 에서 `bash -n` 이 거부하는 꼴을 다 1 로 거부했다)
#   문법을 따로 재지 않는다. **없으면 `bash -n` · `sh -n` 으로 문법만 재고 「못 쟀다」(2)로 끝낸다** —
#   정적 결함은 안 쟀다.
#
# ⚠ **막는 것은 `warning` 이상이다.** `info` · `style` 은 대부분 일부러 쓴 자리다(작은따옴표 안의 `$` 를
#   글자로 찍는 것 등) — 그것까지 막으면 억제 주석이 코드보다 많아지거나 `--no-verify` 가 습관이 된다.
# ⚠ **일부러 쓴 자리는 억제 주석으로 까닭과 함께 든다:**  `# shellcheck disable=SC2086 # 까닭`
#   까닭 앞에 `#` 를 한 번 더 둔다 — `disable=SC2086 — 까닭` 꼴은 shellcheck 가 지시문 오류(SC1125)로 받는다.
#   ⚠ 거꾸로 **주석 줄이 그 도구 이름으로 시작하면** 지시문으로 읽혀 오류(SC1073)가 난다 — 문장을
#   다른 낱말로 시작한다.
set -u
# 이름에 `*` 가 들어도 파일 이름 확장으로 부풀지 않게 — 셔뱅을 낱말로 가를 때도 같다.
set -f

HAVE_SC=''
command -v shellcheck >/dev/null 2>&1 && HAVE_SC=1

# 잴 판의 해석기 이름 — 셔뱅 첫 낱말의 끝 이름. `env` 를 거치면 그 다음 낱말. 셔뱅이 없으면 빈 값.
#   받는 것: 첫 줄(`\r` 은 걷어서 준다).
interp_of() {
  case "$1" in '#!'*) ;; *) return 0 ;; esac
  # shellcheck disable=SC2086  # 셔뱅을 낱말로 가르는 것이 목적이다(위 `set -f` 가 확장을 막는다)
  set -- ${1#??}
  [ "$#" -gt 0 ] || return 0
  [ "${1##*/}" = env ] && [ "$#" -gt 1 ] && shift
  printf '%s' "${1##*/}"
}

# 이 판에서 바뀐 것만 잰다 — 손대지 않은 파일로 커밋 · 푸시를 막지 않는다.
# ⚠ **`core.quotePath=false` 가 있어야 비ASCII 이름이 온다.** 기본값에서는 싸인 이름의 끝이 `"` 라
#   `*.sh` 에 안 걸리고 **한 줄도 안 말하고 빠진다.**
# ⚠ **`R` 도 든다.** `git diff` 는 이름 바꿈을 알아보므로, 옮기면서 고친 파일은 `A`·`M` 이 아니라
#   `R` 로 온다 — 빼면 「옮기고 깨뜨린」 커밋이 그대로 지나간다.
# ⚠ **푸시 판은 담긴 것을 안 묻는다** — 푸시 때 담긴 것은 비어 있어 `diff --cached` 로 물으면 늘 초록이다. 러너의 바뀐
#   경로 목록에는 지운 자리 · 옮겨 떠난 자리도 들므로, 작업 나무에 없는 경로는 아래서 건너뛴다.
if [ "${GATES_STAGE:-}" = pre-push ]; then
  FROM=tree
  if [ -n "${GATES_CHANGED:-}" ] && [ -f "$GATES_CHANGED" ]; then
    STAGED="$(cat "$GATES_CHANGED")"
  else
    printf '· shellcheck — 러너가 바뀐 경로를 안 줘 추적하는 .sh 를 다 잰다.\n' >&2
    STAGED="$(git -c core.quotePath=false ls-files -- '*.sh')"
  fi
else
  FROM=index
  STAGED="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR)"
fi
[ -n "$STAGED" ] || exit 0

FAIL=0; CANT=0; SYNTAX_ONLY=0

# ⚠ **줄바꿈으로만 가른다.** 기본 `IFS` 로 돌리면 `my script.sh` 가 두 조각이 되어 둘 다 빠진다.
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

  # ⚠ **커밋 판은 작업 트리가 아니라 담긴 판을 잰다.** 커밋되는 것은 인덱스다 — 깨진 판을 담아 두고 작업
  #   트리에서만 고치면(`git add -p` · 담고 나서 고친 자리) 초록이 나고 **깨진 판이 커밋된다.**
  #   푸시 판은 작업 나무를 잰다 — 푸시 몸통이 정한 「재는 것은 작업 트리다」와 같다.
  if [ "$FROM" = tree ]; then
    [ -f "$f" ] || { IFS='
'; continue; }
    src="$(cat "$f")"
  else
    src="$(git show ":$f" 2>/dev/null)"
  fi
  first="$(printf '%s\n' "$src" | head -n 1 | tr -d '\r')"

  if [ -n "$HAVE_SC" ]; then
    # 표준 입력으로 먹이면 도구가 셔뱅을 읽어 방언을 고른다(실측 0.11.0).
    # ⚠ **셔뱅도 `shell=` 지시문도 없으면 bash 로 잰다** — 아래 문법 갈래와 같은 판단이다. 지시문이
    #   있으면 `-s` 를 안 준다: `-s` 가 지시문을 덮는다(실측 0.11.0).
    set --
    case "$first" in
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
    continue
  fi

  # ── shellcheck 가 없는 기계 — 문법만 잰다 ─────────────────────────────────────
  # 파서는 **셔뱅으로 고른다** — 그 파일을 실제로 읽을 셸이 그것이다.
  #   `#!/bin/bash` · `#!/usr/bin/env bash`  → bash -n
  #   `#!/bin/sh`   · `#!/usr/bin/env sh`    → sh -n
  # ⚠ **셔뱅이 없으면 `bash -n` 이다.** 셔뱅 없는 `.sh` 는 점(`.`)으로 읽히는 조각이라 어느 셸이 읽나는
  #   **부르는 쪽에** 있다 — 찾는 자는 sh 몸통과 bash 세션 훅이 같이 읽는다. 거짓 빨강을 안 내는 쪽을
  #   고른다: bash 는 POSIX sh 문법을 다 받는다. `sh -n` 으로 재면 판정이 기계마다 갈린다(윈도우 Git
  #   Bash 의 sh 는 bash 의 POSIX 모드, 리눅스 컨테이너의 sh 는 dash).
  SYNTAX_ONLY=1
  it="$(interp_of "$first")"
  case "$it" in
    ''|bash) p='bash' ;;
    sh|dash) p='sh' ;;
    *)
      printf '· 셸 문법 — %s 는 셔뱅이 %s 라 이 조각의 파서(bash · sh)로 못 잰다.\n' "$f" "$it" >&2
      CANT=1; IFS='
'; continue ;;
  esac
  if ! command -v "$p" >/dev/null 2>&1; then
    printf '· 셸 문법 — %s 가 없어 %s 를 못 쟀다.\n' "$p" "$f" >&2
    CANT=1; IFS='
'; continue
  fi

  # 오류 줄의 `line N` 은 그 파일의 줄 번호다.
  err="$(printf '%s\n' "$src" | "$p" -n 2>&1)"; rc=$?
  if [ "$rc" -ne 0 ]; then
    printf '✖ 셸 문법이 깨졌다 (%s -n):  %s\n' "$p" "$f" >&2
    line1="$(printf '%s\n' "$err" | head -n 1)"
    [ -n "$line1" ] || line1="(파서가 말없이 $rc 로 졌다)"
    printf '    %s\n' "$line1" >&2
    FAIL=1
  fi
  IFS='
'
done
IFS=$oldifs

if [ "$FAIL" != 0 ]; then
  printf '  셸이 깨졌거나 정적 결함이 있다 — 깨진 셸은 말없이 반쯤 돌고, 게이트 조각이면 「못 쟀다」로 새어\n' >&2
  printf '  형제의 검사까지 빠진다. 일부러 쓴 자리면 그 줄 위에 `# shellcheck disable=SCxxxx # 까닭` 을 단다.\n' >&2
  exit 1
fi
[ "$SYNTAX_ONLY" = 0 ] ||
  printf '· shellcheck 가 없어 바뀐 .sh 의 **문법만** 쟀다(bash -n · sh -n) — 정적 결함은 못 쟀다.\n' >&2
[ "$CANT" = 0 ] && [ "$SYNTAX_ONLY" = 0 ] || exit 2
exit 0
