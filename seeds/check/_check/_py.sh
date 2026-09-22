#!/bin/sh
# 실행형 파이썬 해석기를 골라 부르거나 변수로 세운다 — 다섯이 각자 짓던 것을 한 자리로.
#
# 왜 있나: 윈도의 python3 은 스토어로 보내는 껍데기다 — 존재(command -v)로 물으면
#   「있다」가 나오고 부르면 안내문을 뱉고 49 로 죽는다 (0028).
#   바 .py 하나로는 리눅스(python 이 없다)와 윈도(python3 이 껍데기다)를 셰방 하나로
#   못 든다 — 그래서 부르는 자리가 이 부품으로 해석기를 고른다 (0040 · #75).
#
# 진본:     claude-config/seeds/check/_check/_py.sh
# 로드 자리: ~/.claude/seeds/check/_check/_py.sh (0034)
#
# 차례가 셋이고 위에서부터 처음 실제로 도는(-c "") 것을 쓴다:
#   ① $PY — 사람이 못박은 환경변수가 언제나 이긴다
#   ② 이 나무의 .venv — 검사가 부르는 모듈의 의존성이 사는 자리
#   ③ 시스템 해석기 — OS별 우선순위 (윈도는 python, 리눅스는 python3)
#
# 사용:
#   1. 인자를 주어 실행:      _py.sh <스크립트.py> [인자...]
#   2. 인자 없이 실행:        PY=$(_py.sh)
#   3. 스크립트 안에서 소싱:  . "$SEEDS_CHECK/_py.sh"  # $PY 변수가 선다
set -u

_find_py() {
    # ① 환경변수 PY 가 이미 서 있고 실제로 도는가
    if [ -n "${PY:-}" ] && "$PY" -X utf8 -c "" >/dev/null 2>&1; then
        return 0
    fi

    # ② .venv 탐색 (현재 폴더 또는 git 작업나무 뿌리)
    _top="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    for _v in ${dir:+"$dir/.venv/Scripts/python.exe"} \
              ${_top:+"$_top/.venv/Scripts/python.exe"} \
              .venv/Scripts/python.exe \
              ${dir:+"$dir/.venv/bin/python"} \
              ${_top:+"$_top/.venv/bin/python"} \
              .venv/bin/python; do
        if [ -f "$_v" ] && "$_v" -X utf8 -c "" >/dev/null 2>&1; then
            PY="$_v"
            return 0
        fi
    done

    # ③ 시스템 해석기 — 있나가 아니라 도나로 고른다
    _candidates="python python3"
    case "$(uname -s 2>/dev/null || echo Windows)" in
        Linux*|Darwin*) _candidates="python3 python" ;;
        *) _candidates="python python3" ;;
    esac
    for _p in $_candidates; do
        if "$_p" -X utf8 -c "" >/dev/null 2>&1; then
            PY="$_p"
            return 0
        fi
    done

    PY=""
    return 1
}

if ! _find_py; then
    printf '· python 이 없다 — 실행형 해석기를 찾지 못했다\n' >&2
    exit 2
fi

case "$0" in
    *_py.sh)
        if [ $# -gt 0 ]; then
            exec "$PY" "$@"
        else
            printf '%s\n' "$PY"
        fi
        ;;
    *)
        # 소싱된 경우: $PY 변수가 호출 환경에 그대로 남는다
        ;;
esac
