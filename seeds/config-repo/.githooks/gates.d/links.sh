#!/bin/sh
# 조각 — 깨진 링크·앵커. lychee 가 잰다.
#
# **익명이다 — 무엇을 빼는지 모른다.** 제외 목록은 저장소가 `lychee.toml` 로 든다.
# 옛 판은 명령과 제외 목록을 한 셸 스크립트에 같이 담았고, 그래서 저장소마다 몸통이
# 갈렸다(실측: 형제 둘의 같은 파일이 25줄 달랐다 — 전부 제외 목록과 그 까닭이었다).
# 명령은 한 벌이고 목록은 저장소 것이다.
#
# ⚠ **제외 목록을 여기 적지 않는다.** `lychee.toml` 은 lychee 가 제 손으로 읽는 표준
#   자리다 — 우리 문법을 새로 짓지 않는다. 거기 적을 때의 함정 둘은 그 파일이 든다.
#
# ⚠ `--offline` 이다. 바깥 주소는 안 두드린다 — 커밋마다 네트워크를 타면 비행기·사내망
#   에서 게이트가 멈추고, 멈추는 게이트는 `--no-verify` 를 습관으로 만든다. 바깥 링크가
#   살아있나는 커밋이 아니라 CI 나 문서 감사가 잴 자리다.
set -u

command -v lychee >/dev/null 2>&1 || {
    printf '· lychee 가 없어 링크 검사를 건너뛴다.\n' >&2
    exit 2
}

set -- --offline --no-progress
[ -f lychee.toml ] && set -- "$@" --config lychee.toml

out="$(lychee "$@" . 2>&1)" || {
    printf '✖ 깨진 링크·경로가 있다.\n' >&2
    printf '%s\n' "$out" | grep '^\[ERROR\]' >&2 || printf '%s\n' "$out" | tail -n 20 >&2
    exit 1
}
exit 0
