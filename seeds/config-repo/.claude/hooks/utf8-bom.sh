#!/bin/sh
# matcher = Write|Edit
# events = PostToolUse
# if.PostToolUse = Write(//**/*.ps1) | Edit(//**/*.ps1) | Write(//**/*.psm1) | Edit(//**/*.psm1) | Write(//**/*.psd1) | Edit(//**/*.psd1)
# var = _ub
#
# 파워셸 스크립트에 UTF-8 BOM 을 찍는다 — PostToolUse 훅 (Write|Edit).
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 짓고, 머리말의 뜻과 심기는 명령
# 꼴은 표(`tool-homes.conf`)의 hook 꼴이 든다. 이 훅을 거는 쪽은 그 홈 등록 하나다 — 저장소 설정(`.claude/settings.json`)이
# 또 걸면 쓰기마다 두 번 돈다(결정 0124). 홈 등록은 이 파일을 점(`.`)으로 읽는다.
# ⚠ **파워셸 파일이 아닌 쓰기에는 아예 안 뜬다** — 회사에서는 프로세스 하나가 약 0.3 초라, 거는 자가 등록의 거름(`if.PostToolUse`
#   — 규칙마다 등록 하나)으로 맞는 쓰기에만 이 껍데기를 띄운다. 거름은 `//**/*.<확장자>` 꼴이다 — 어느 폴더에서나 · 대소문자를 안
#   가리고 맞는다(`tool-homes.conf` hook 꼴). 거름이 늘 맞는다고 믿지 않는다 — 떴으면 입력은 `cat` 이 아니라 셸 `read` 로 받고,
#   경로가 파워셸 확장자가 아니면 외부 명령을 열기 전에 나간다. 거름의 확장자와 아래 글롭은 짝이다(`scripts/check-utf8-bom.sh`).
# 이미 BOM 이 선 파일(흔한 길)은 외부 명령 없이 셸 내장만으로 판정하고 나간다 — BOM 을 찍는 드문 길에서만 외부 명령을 부른다.
#
# 진본은 claude-config/.claude/hooks/utf8-bom.sh 다. 각 저장소의 것은 deploy.ps1 이
# 뿌린 배포본이다 — 배포본을 고치면 다음 배포에 덮인다.
#
# ── 왜 이것이 훅인가 ────────────────────────────────────────────────────────
# Windows PowerShell 5.1 은 **BOM 없는 스크립트 파일을 시스템 ANSI 코드페이지로 읽는다**
# (한국어 윈도우는 cp949). UTF-8 로 저장한 한글이 그 자리에서 깨지고, 따옴표가 안 닫혀
# 파서가 죽는다. 콘솔 코드페이지(chcp 65001)는 **다른 자리**라 그걸 고쳐도 안 낫는다.
#
# 규율로 적으면 파일을 만드는 그 순간에 사람이 기억해야 하고, 기억해야 하는 것은
# 그 순간에 안 걸린다. 그래서 판단을 안 거치는 층에 둔다.
#
# ── 왜 JSON 을 안 파싱하나 ──────────────────────────────────────────────────
# jq 가 보장되지 않는다 (0004 의 「sh 순정 파서」와 같은 이유). Write·Edit 입력은 경로를 `tool_input.file_path` 하나로
# 싣는다 — 첫 `"file_path":"` 뒤에서 다음 `"` 앞까지를 셸 변수 확장으로 잘라 외부 명령 없이 경로를 얻는다. 경로의
# JSON 이스케이프는 윈도우 경로의 역슬래시(둘로 온 것)만 푼다 — `\"` · `\uXXXX` 는 다루지 않는다(윈도우 파일 이름에는 `"` 가
# 못 든다). 경로가 없거나 파워셸 확장자가 아니거나 실재하는 파일이 아니면 넘어가고, BOM 은 몇 번 돌려도 한 번만 붙는다(멱등).
#
# 전수 스캔(find)도 안 쓴다 — 이 훅은 Write·Edit 마다 돌아서 비용이 매번 든다.
#
# 시험 — `sh scripts/check-utf8-bom.sh` (실물 꼴의 입력을 홈 등록의 명령으로 먹여 찍을 것과 둘 것을, 그리고 홈 등록이
# 서나를 문다 — 저장소 설정이 또 거나는 어느 검사도 안 잰다).
set -u

j=; while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done

# 경로 — 첫 `"file_path":"` 뒤 · 다음 `"` 앞. 없으면 이 훅이 다룰 쓰기가 아니다
f=${j#*'"file_path":"'}
[ "$f" != "$j" ] || exit 0
f=${f%%'"'*}
# 역슬래시를 슬래시로 눕힌다 — Git Bash 는 C:/… 를 그대로 연다. JSON 에서 둘로 온 것을 하나씩 먼저, 그다음 남은 하나짜리를
while case $f in *'\\'*) ;; *) false ;; esac; do f=${f%%'\\'*}/${f#*'\\'}; done
while case $f in *'\'*) ;; *) false ;; esac; do f=${f%%'\'*}/${f#*'\'}; done

# 확장자는 대소문자를 안 가린다(윈도우 파일 이름이 그렇다)
case $f in *.[Pp][Ss]1|*.[Pp][Ss][Mm]1|*.[Pp][Ss][Dd]1) ;; *) exit 0 ;; esac
[ -f "$f" ] || exit 0

BOM=$(printf '\357\273\277')

# 이미 UTF-8 BOM 이 서 있다 — 첫 줄을 셸 `read` 로 받아 앞 세 바이트(EF BB BF)를 견준다. 외부 명령이 없는 흔한 길이다
_first=; IFS= read -r _first < "$f" 2>/dev/null
case "$_first" in
  "$BOM"*) exit 0 ;;
esac

# ── 여기부터 BOM 이 없는 파일이다 (드문 길 — 외부 명령을 쓴다) ────────────────────
# UTF-16 BOM(FF FE · FE FF)이 선 파일은 둔다 — 그 앞에 UTF-8 BOM 을 붙이면 PowerShell 5.1 이 깨진 글로 읽는다.
#   그 두 바이트는 UTF-8 로 성립하지 않아 셸 글자 견주기 대신 16 진으로 본다
case "$(head -c 2 "$f" 2>/dev/null | od -An -tx1 | tr -d ' \n')" in
  fffe|feff) exit 0 ;;
esac

# ⚠ **한 쓰기에 이 훅이 겹쳐 돌 수 있다** — 제 설정(`.claude/settings.json`)으로 이 훅을 따로 거는 저장소에서는 홈
#   등록과 두 층에 걸려 제품이 둘을 함께 띄운다. 씨앗으로 만든 저장소는 만든 사람 것이라 그 설정이 우리 것과 따로 간다.
#   그래서 임시본은 실행마다 제 이름(`$$`)으로 짓고, 바꿔 넣기 직전에 BOM 을 다시 본다 — 그 사이
#   다른 실행이 찍었으면 내 임시본은 버린다. 임시본 이름을 나눠 쓰면 한쪽이 다른 쪽의 임시본을
#   비운 채 옮겨 넣어 **본문이 사라지고 BOM 만 남는다.**
tmp="$f.utf8bom.$$.tmp"
if { printf '%s' "$BOM"; cat "$f"; } > "$tmp" 2>/dev/null; then
  _now=; IFS= read -r _now < "$f" 2>/dev/null
  case "$_now" in
    "$BOM"*) ;;                  # 그 사이 겹친 실행이 찍었다 — 내 임시본은 버린다
    *) mv -f "$tmp" "$f" 2>/dev/null &&
         echo "utf8-bom: BOM 을 찍었다 (PowerShell 5.1 이 ANSI 로 읽는 것을 막는다) — $f" >&2 ;;
  esac
fi
rm -f "$tmp" 2>/dev/null

# 훅이 0 이 아니면 도구 호출이 실패한 것처럼 보인다. 이 훅은 절대 막지 않는다.
exit 0
