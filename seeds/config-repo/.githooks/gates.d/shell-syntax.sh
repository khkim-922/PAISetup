#!/bin/sh
# 조각 — 담긴 셸 스크립트가 **문법으로** 서나. `bash -n` · `sh -n` 이 잰다(#91 ①).
#
# 왜 이것인가 — 깨진 셸은 **깨졌다고 말하지 않고 반쯤 돈다.**
#
#   · 세션 훅 몸통은 모든 저장소 · 모든 PC 의 세션 시작에서 돈다. 한 줄이 깨지면 그 세션들이
#     조용히 반쯤 돌고, 화면에는 아무 일도 없어 보인다.
#   · 게이트 조각(`gates.d/*.sh`)이 문법 오류로 죽으면 셸이 2 로 끝나고, 러너는 2 를 「못 쟀다」로
#     받아 **커밋을 안 막는다.** 형제 저장소는 이 저장소의 조각을 부르므로(결정 0064) 반쯤 고친
#     조각 하나가 **모든 형제에서** 그 검사를 뺀다. 그 조각이 커밋되는 이 자리에서 막는다.
#
# ⚠ **재는 것은 파서가 거부하는 것뿐이다** — 안 닫힌 `if` · 따옴표 · 괄호 같은 것. 인용 누락 ·
#   `set -u` 아래 빈 변수 · sh 파일에 든 bash 전용 문법은 파서를 지나가므로 여기서 안 잡힌다.
#   그 부류는 shellcheck 의 몫이다(#91 ③).
set -u
# 이름에 `*` 가 들어도 파일 이름 확장으로 부풀지 않게 — 아래 셔뱅을 낱말로 가를 때도 같다.
set -f

FAIL=0; CANT=0

# 담긴 판의 해석기 이름 — 셔뱅 첫 낱말의 끝 이름. `env` 를 거치면 그 다음 낱말. 셔뱅이 없으면 빈 값.
# ⚠ **작업 트리가 아니라 담긴 판을 잰다.** 커밋되는 것은 인덱스다 — 깨진 판을 담아 두고 작업
#   트리에서만 고치면(`git add -p` · 담고 나서 고친 자리) 초록이 나고 **깨진 판이 커밋된다.**
interp_of() {
  _l="$(git show ":$1" 2>/dev/null | head -n 1 | tr -d '\r')"
  case "$_l" in '#!'*) ;; *) return 0 ;; esac
  # shellcheck disable=SC2086  # 셔뱅을 낱말로 가르는 것이 목적이다(위 `set -f` 가 확장을 막는다)
  set -- ${_l#??}
  [ "$#" -gt 0 ] || return 0
  [ "${1##*/}" = env ] && [ "$#" -gt 1 ] && shift
  printf '%s' "${1##*/}"
}

# 스테이지된 것만 잰다 — 손대지 않은 파일로 커밋을 막지 않는다.
# ⚠ **`core.quotePath=false` 가 있어야 비ASCII 이름이 온다** — 인코딩 조각(`encoding.sh`)과 같은 자리다.
#   기본값에서는 싸인 이름의 끝이 `"` 라 `*.sh` 에 안 걸리고 **한 줄도 안 말하고 빠진다.**
# ⚠ **`R` 도 든다.** `git diff` 는 이름 바꿈을 알아보므로, 옮기면서 고친 파일은 `A`·`M` 이 아니라
#   `R` 로 온다 — 빼면 「옮기고 깨뜨린」 커밋이 그대로 지나간다.
STAGED="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR)"
[ -n "$STAGED" ] || exit 0

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

  # 파서는 **셔뱅으로 고른다** — 그 파일을 실제로 읽을 셸이 그것이다.
  #   `#!/bin/bash` · `#!/usr/bin/env bash`  → bash -n
  #   `#!/bin/sh`   · `#!/usr/bin/env sh`    → sh -n
  # ⚠ **셔뱅이 없으면 `bash -n` 이다.** 셔뱅 없는 `.sh` 는 실행되지 않고 점(`.`)으로 읽히는 조각이라
  #   (찾는 자 `claude-config-path.sh` · 그림 문 껍데기 `image-gate.sh`), 어느 셸이 읽나는 **파일이 아니라
  #   부르는 쪽에** 있다 — 찾는 자는 sh 몸통과 bash 세션 훅이 같이 읽는다. 파일만 보고는 모르므로
  #   거짓 빨강을 안 내는 쪽을 고른다: bash 는 POSIX sh 문법을 다 받는다.
  #   `sh -n` 으로 재면 판정이 **기계마다 갈린다.** 윈도우 Git Bash 의 sh 는 bash 의 POSIX 모드라
  #   bash 전용 문법을 받고, 리눅스 컨테이너의 sh 는 dash 라 같은 파일을 빨강으로 세운다 — bash 만
  #   읽는 파일이면 그 빨강은 거짓이고, 한 기계에서만 막히는 게이트는 `--no-verify` 를 부른다.
  #   값: sh 도 읽는 셔뱅 없는 파일에 bash 전용 문법이 들면 여기서 안 잡힌다 — shellcheck 가 든다(#91 ③).
  it="$(interp_of "$f")"
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

  # 담긴 판을 표준 입력으로 먹인다 — 임시 파일을 안 만든다. 오류 줄의 `line N` 은 그 파일의 줄 번호다.
  err="$(git show ":$f" 2>/dev/null | "$p" -n 2>&1)"; rc=$?
  if [ "$rc" -ne 0 ]; then
    printf '✖ 셸 문법이 깨졌다 (%s -n):  %s\n' "$p" "$f" >&2
    first="$(printf '%s\n' "$err" | head -n 1)"
    [ -n "$first" ] || first="(파서가 말없이 $rc 로 졌다)"
    printf '    %s\n' "$first" >&2
    FAIL=1
  fi
  IFS='
'
done
IFS=$oldifs

if [ "$FAIL" != 0 ]; then
  printf '  깨진 셸은 말없이 반쯤 돈다 — 게이트 조각이면 「못 쟀다」로 새어 형제의 검사까지 빠진다.\n' >&2
  exit 1
fi
[ "$CANT" = 0 ] || exit 2
exit 0
