#!/usr/bin/env bash
# 세션의 받는 손(edge_session.js)을 이 폴더에서 부른다.
# 인자 · 종료 값은 그대로 넘긴다(그 파일 머리말): 0 산 세션 · 2 Edge 에 못 붙음 · 3 로그인 안 됨 · 4 ECM 넘김만 못 따라감 · 1 그 밖.
#     bash session.sh [세션 파일] [domino] [ecm] [--ecm-tab]
set -u
exec node "$(cd "$(dirname "$0")" && pwd)/edge_session.js" "$@"
