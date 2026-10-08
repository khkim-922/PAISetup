# matcher = WebSearch|WebFetch
#
# 웹 다시 찾기 — 웹 도구가 못 닿았을 때 **다른 길이 있다는 것을 결과 곁에 한 줄 붙인다**(PostToolUse ·
# PostToolUseFailure 훅). 붙이기만 한다 — 막지 않는다.
#
# **왜 있나.** 웹서치·웹페치가 막히면 모델은 「못 찾았다」로 끝내기 쉽다 — Tavily MCP 나 agy 다리가 세션에
# 붙어 있어도 그 순간에는 안 떠오른다. 그런데 같은 일을 그 길로 하면 닿는 일이 많다. 규범에 적어도
# 도구를 고르는 순간에는 안 걸려, 못 닿은 바로 그 결과 곁에 거는 이 층에 둔다(규범 [Layer Triage]).
#
# 거는 꼴 넷 — 실패가 **오류로 오지 않는 꼴이 더 많다**(정상 반환 안에 든다):
#   · 오류로 끝났다(PostToolUseFailure) — 주소를 못 푼다 등. 도구가 무엇이든 건다
#   · 웹페치 결과가 「Unable to verify if domain」 — 웹페치가 도메인 검사를 claude.ai 에 묻는 길이 막혔다.
#     대상이 직결로 열려도 진다(사내 PC 실측 2026-10-08 — TLS 검사 장비가 claude.ai 를 끊는다 · #117)
#   · 웹페치 응답 코드가 4xx · 5xx — 사이트가 거부했다(403 등). 하네스는 이것을 실패로 안 친다
#   · 웹서치 결과에 주소(`"url":`)가 하나도 없다 — 출처 0 개. 머리글과 「출처를 달라」 알림만 남아
#     그대로 두면 없는 출처를 지어 달게 민다(사내 PC 실측). 진짜로 결과가 없는 물음도 같은 꼴이라
#     거기도 걸리는데, 틀려도 「다른 길로도 찾아본다」에 그쳐 그 값을 감수한다
# ⚠ **문면 「Unable to verify if domain」은 Claude Code 판에 매여 있다** — 문면이 바뀌면 조용히 안 걸린다.
#   나머지 셋은 하네스가 주는 칸(이벤트 이름 · 응답 코드 · 주소 키)을 본다.
# ⚠ **입력은 압축된 JSON 이다**(키와 값 사이에 공백이 없다 — 실측). `"code":4` 와 `"url":` 는 JSON 문자열
#   안에서는 설 수 없는 글자라(안의 따옴표는 역슬래시가 앞선다) 키로만 걸린다.
# ⚠ **파이썬을 안 띄운다** — 셸만으로 가른다. 윈도우 파이썬은 표준 입력을 지역 인코딩으로 읽어 UTF-8
#   본문에서 죽는다(실측) — 죽은 훅은 아무 말도 안 붙인다.
# ⚠ **덧말은 사실로 쓴다** — 명령조의 바깥 글은 프롬프트 주입 방어에 걸릴 수 있다(Claude Code 훅 문서).
#
# 홈 `~/.claude/settings.json` 의 PostToolUse · PostToolUseFailure 둘에 같은 한 줄로 심긴다 — 심는 손은
# 이 자리만 채운다:
#     _wr="<이 파일이 있는 자리>"; [ -f "$_wr/web-retry.sh" ] || exit 0; . "$_wr/web-retry.sh"
# 윗줄 `# matcher = …` 가 두 항목의 matcher 진본이다. 심는 손은 그림 문(`image-gate.sh`)과 같다 —
# `session-start-body.sh` 와 배포본 설치기. 주인 규율도 같다.
#
# 시험 — `sh scripts/check-web-retry.sh` (실물 꼴의 입력을 먹여 걸 것과 둘 것을 문다).
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
j=$(cat)
ev=PostToolUse
why=
note=
case "$j" in
  *'"hook_event_name":"PostToolUseFailure"'*)
    ev=PostToolUseFailure
    why='오류로 끝났다' ;;
  *'"tool_name":"WebFetch"'*)
    case "$j" in
      *'Unable to verify if domain'*) why='도메인 검사 길이 막혔다' ;;
      *'"code":4'[0-9][0-9]*|*'"code":5'[0-9][0-9]*) why='사이트가 거부했다' ;;
    esac ;;
  *'"tool_name":"WebSearch"'*)
    case "$j" in
      *'"url":'*) ;;
      *) why='출처를 하나도 안 돌려줬다'
         note=' 결과의 「출처를 달라」 알림이 가리킬 출처가 없다 — 출처를 지어 달지 않는다.' ;;
    esac ;;
esac
[ -n "$why" ] || exit 0
# 다른 길 — **이 PC 에 깔린 것만 댄다**(claude-config #118 끝 조건). 없는 길을 대면 모델이 헛걸음을 한 번 더 한다.
#   재는 것은 실행 파일이 PATH 에 있나다 — 셸 검사라 값이 없다. ⚠ claude.ai 커넥터로 붙은 Tavily 는 실행 파일이
#   없어 못 본다(그 자리는 안 대고 넘어간다 — 없는 길을 대는 쪽보다 덜 비싸다).
# 차례가 도구마다 다르다 — 웹페치는 `curl` 이 맨 앞이다(직결로는 열리는데 웹페치만 못 가는 주소가 있고 가장
#   싸다). 웹서치는 `curl` 로 못 한다. agy 다리를 Tavily 보다 앞에 두는 까닭은 사내에서 다리가 게이트웨이 안의
#   길이고 Tavily 는 질의가 회사 밖으로 나가서다(#118).
has() { command -v "$1" >/dev/null 2>&1; }
alts=
add() { if [ -n "$alts" ]; then alts="$alts · $1"; else alts=$1; fi; }
case "$j" in
  *'"tool_name":"WebFetch"'*)
    has curl && add "같은 주소를 Bash 의 \`curl\` 로(프록시 환경변수를 비끼려면 \`-x ''\`)"
    has tavily-mcp && add "같은 주소를 Tavily 의 \`tavily_extract\` 로"
    has agy-bridge && add "같은 물음을 agy 다리 \`mcp__agy-bridge__web_lookup\` 으로"
    head="웹 다시 찾기 — WebFetch 가 이 주소의 본문을 못 받았다($why)." ;;
  *)
    has agy-bridge && add "같은 물음을 agy 다리 \`mcp__agy-bridge__web_lookup\` 으로"
    has tavily-mcp && add "같은 물음을 Tavily 의 \`tavily_search\` 로"
    head="웹 다시 찾기 — WebSearch 가 $why.$note" ;;
esac
if [ -n "$alts" ]; then
  msg="$head 이 PC 에 있는 다른 길로는 닿는 일이 많다: $alts. MCP 도구가 목록에 안 보이면 ToolSearch 로 이름을 불러 쓸 수 있다. 다 막혔을 때만 못 닿았다고 적는다."
else
  msg="$head 이 PC 에서 쓸 다른 길이 안 보인다 — 못 닿았다고 적는다."
fi
printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}' "$ev" "$msg"
exit 0
