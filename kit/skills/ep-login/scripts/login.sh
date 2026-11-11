#!/usr/bin/env bash
# 스킬 ep-login 의 입구(ep_login.js)를 이 폴더에서 부른다 — 받아 보고, 안 서면 로그인을 띄워 지켜본 뒤 다시 받는다.
# 인자 · 종료 값은 그대로 넘긴다(그 파일 머리말): 0 섰다(표준 출력이 세션 파일 경로) · 2 포트 없이 도는 Edge · 3 포트가 안 열린다 · 4 로그인 · ECM 이 안 섰다 · 1 그 밖.
#     bash login.sh [세션 파일] [domino] [ecm] [--restart] [--profile <폴더>]
set -u
exec node "$(cd "$(dirname "$0")" && pwd)/ep_login.js" "$@"
