#!/usr/bin/env bash
# 세션의 띄우는 손(edge_start.js)을 이 폴더에서 부른다.
# 인자 · 종료 값은 그대로 넘긴다(그 파일 머리말): 0 포트가 열렸다 · 2 포트 없이 도는 Edge 가 있다 · 3 기본 프로필로는 안 선다 · 1 그 밖.
#     bash start-edge.sh [--profile <폴더>] [주소]
set -u
exec node "$(cd "$(dirname "$0")" && pwd)/edge_start.js" "$@"
