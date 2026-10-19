# matcher = SendMessage
# events = PreToolUse
# var = _lr
#
# 이어 묻기 값 — 식고 큰 레인에 SendMessage 로 이어 물으면 그 첫 번을 한 번 막고(PreToolUse `deny`), 그 레인이 얼마나 식었고
# 다시 읽힐 맥락이 얼마인지를 사유에 적는다. 같은 메시지를 그대로 다시 보내면 통과한다. 왜와 문턱의 근거는 결정 0168 이 든다.
#
# **왜 있나.** 이어 묻기는 그 레인의 기록을 통째로 다시 읽힌다. 캐시가 살아 있으면 싸지만, 식은 뒤에는 캐시 없이 처음부터
# 다시 읽힌다 — 고칠 자리 하나에 수십만 토큰이 든다. 규칙은 스킬 agent-envelope 1 절 「토큰」 줄에 있는데 보내는 그 순간에
# 안 걸려, 판단과 무관하게 걸리는 이 층에 둔다(규범 [Layer Triage]). 덧말(`additionalContext`)은 도구 결과 곁에 닿아 이번
# 이어 묻기의 값을 못 아끼므로, 보내기 **전에** 재료를 보이는 한 번 막기로 둔다 — 판단은 모델에 그대로 남는다.
#
# 거는 꼴 — 넷이 다 설 때만 막는다. 하나라도 아니면 말이 없다.
#   · 받는 쪽이 이 세션의 서브에이전트 기록으로 짚힌다 — `to` 가 id 꼴이고 `<세션 기록에서 .jsonl 을 뗀 자리>/subagents/agent-<id>.jsonl`
#     가 있다. 이름 · `main` · 다른 세션은 기록 자리를 못 짚어 둔다
#   · 식었다 — 그 기록의 마지막 쓰기가 서브에이전트 캐시 수명보다 오래다. 수명은 하네스의 차례 그대로 고른다(Claude Code 문서
#     「prompt caching · Choose the TTL yourself」): `FORCE_PROMPT_CACHING_5M=1` → 환경변수 `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL`
#     → 설정 `subagentPromptCacheTtl` → `ENABLE_PROMPT_CACHING_1H=1` → 기본 5 분. 값은 `5m` · `1h` 만 받는다.
#     설정 `env` 블록의 값은 훅 프로세스에 내려온다(잰 값 — 결정 0168) — 설치기가 심는 환경변수가 그 길이다.
#     설정 파일은 키가 든 줄까지만 읽고, 값은 그 줄에서 찾는다 — Claude Code 가 쓰는 꼴(키와 값이 한 줄)이다.
#     ⚠ 설정은 사용자 층 `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json` 하나만 읽는다 — 관리 · 프로젝트 층의 같은 키와
#     에이전트 앞머리의 `cacheTtl` 은 안 본다. 그 자리로 1 시간을 둔 곳에서는 5 분과 1 시간 사이에 헛막음이 난다
#   · 크다 — 기록 마지막 요청의 사용량(입력 + 캐시 쓰기 + 캐시 읽기 + 출력)이 MIN_TOK 이상이다. 압축한 레인도 그 값이 다시 읽힐
#     맥락이다. 끝 조각에 사용량이 없으면 바이트를 BYTES_PER_TOK 로 나눠 어림한다(그림이 든 기록은 크게 어림된다)
#   · 다른 도구가 아니다 — 등록 matcher 가 SendMessage 만 고르고, 입력의 tool_name 도 한 번 더 본다
#
# 한 번 막기 — 막을 때 표지 `<세션 자리>/subagents/lane-resume-<id>` 에 그 기록의 「바이트 mtime」을 적는다. 다음 SendMessage 가
#   같은 레인에 오고 기록이 그대로면(표지와 같다) 말없이 통과한다. 레인이 다시 돌아 기록이 바뀌면 표지는 저절로 낡아, 다음에
#   식었을 때 다시 막는다.
#   ⚠ **표지를 못 쓰면 막지 않는다** — 막고도 표지가 없으면 되보내도 또 막혀, 기억이 드는 이어 묻기가 영영 못 간다. 그때는
#   같은 사실을 덧말로만 붙인다.
#
# ⚠ **셸 밖의 프로세스는 낌새 뒤에만, 걸음마다 하나씩 더한다** — 회사 PC 에서는 프로세스 하나가 약 0.3 초다(claude-config #197).
#   SendMessage 아닌 호출 — 훅이 안 뜬다(matcher). 짚히는 기록이 없다 — `sh` 혼자(입력은 셸 `read`, 자리는 `[ -f ]`).
#   기록이 작다 · 막은 뒤 되보냈다 — `stat` 하나(표지는 `[ -f ]` · `read`). 크지만 살았다 — `stat` · `date` 둘.
#   식고 크다 — 셋째로 `tail` 이 끝 조각을 읽는다. 설정 파일은 셸 `read` 로 읽고 표지는 `>` 로 쓴다 — 프로세스가 늘지 않는다.
#   크기 문(MIN_BYTES)은 바이트로 먼저 거르는 싼 문이라, 토큰당 바이트가 가장 작은 기록도 놓치지 않게 낮게 둔다(결정 0168 의 잰 값).
# ⚠ **입력은 압축된 JSON 이다** — `"to":"` · `"usage":{` 는 JSON 문자열 안에서는 따옴표가 역슬래시를 앞세워 설 수 없어 키로만 걸린다.
#   윈도우 경로는 JSON 이스케이프로 역슬래시가 둘씩 온 그대로 쓴다 — Git Bash 의 `[ -f ]` · `stat` · `tail` · `>` 가 겹친 역슬래시
#   경로도 연다(잰 값 — 검사의 모든 판이 윈도우에서는 그 꼴이다).
# ⚠ **`to` 는 영숫자 · `_` · `-` 만 받는다** — 경로 글자(`/` · `.`)가 들면 기록 자리 밖을 짚게 된다.
# ⚠ **`stat -c` 는 GNU 꼴이다** — Git Bash 와 리눅스 원격이 든다. 못 읽으면 말이 없다.
# ⚠ **사유는 사실로 쓴다** — 명령조의 바깥 글은 프롬프트 주입 방어에 걸릴 수 있다(Claude Code 훅 문서).
#
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 짓고, 머리말의 뜻과 심기는 명령 꼴은
# 표(`tool-homes.conf`)의 hook 꼴이 든다. 홈 등록은 이 파일을 점(`.`)으로 읽어 같은 셸 안에서 돌고, 끝의 `exit 0` 이 훅을 끝낸다.
#
# 시험 — `python -X utf8 scripts/check-lane-resume.py` (홈 등록의 명령으로 막을 것 · 둘 것 · 되보냄 · 띄우는 프로세스 수를 문다) ·
#   물림 `sh scripts/mutate-lane-resume.sh`.
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
MIN_TOK=150000        # 다시 읽힐 맥락이 이만큼은 돼야 막는다
MIN_BYTES=450000      # 바이트 문 — MIN_TOK × 3(잰 기록의 토큰당 바이트 가장 작은 값 3.4 아래)
BYTES_PER_TOK=5       # 사용량이 없을 때의 어림 — 잰 기록의 가운데 값
TAIL_BYTES=65536      # 마지막 사용량을 찾는 끝 조각
TTL_5M=300            # 서브에이전트 캐시 수명의 두 값(초) — 머리말 「식었다」
TTL_1H=3600
j=; while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done
case "$j" in *'"tool_name":"SendMessage"'*) ;; *) exit 0 ;; esac
_in=${j#*'"tool_input":'}
case "$_in" in *'"to":"'*) ;; *) exit 0 ;; esac
to=${_in#*'"to":"'}; to=${to%%'"'*}
case "$to" in ''|*[!A-Za-z0-9_-]*) exit 0 ;; esac
case "$j" in *'"transcript_path":"'*) ;; *) exit 0 ;; esac
tp=${j#*'"transcript_path":"'}; tp=${tp%%'"'*}
case "$tp" in *.jsonl) ;; *) exit 0 ;; esac
f="${tp%.jsonl}/subagents/agent-$to.jsonl"
[ -f "$f" ] || exit 0
_st=$(stat -c '%s %Y' "$f" 2>/dev/null) || exit 0
size=${_st%% *}; mt=${_st#* }
case "$size$mt" in ''|*[!0-9]*) exit 0 ;; esac
[ "$size" -ge "$MIN_BYTES" ] || exit 0
# 한 번 막은 그 기록 그대로면 둔다 — 머리말 「한 번 막기」
mk="${tp%.jsonl}/subagents/lane-resume-$to"
if [ -f "$mk" ]; then
  _seen=; { IFS= read -r _seen < "$mk"; } 2>/dev/null
  [ "$_seen" = "$size $mt" ] && exit 0
fi
now=$(date +%s 2>/dev/null) || exit 0
case "$now" in ''|*[!0-9]*) exit 0 ;; esac
age=$((now - mt))
[ "$age" -ge "$TTL_5M" ] || exit 0
# 캐시 수명 — 머리말 「식었다」의 차례
cold=
case "${CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL:-}" in
  1h) cold=$TTL_1H ;;
  5m) cold=$TTL_5M ;;
esac
if [ -z "$cold" ]; then
  _sf="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
  if [ -f "$_sf" ]; then
    _set=; while IFS= read -r _l || [ -n "$_l" ]; do
      case "$_l" in *'"subagentPromptCacheTtl"'*) _set=$_l; break ;; esac
    done < "$_sf"
    case "$_set" in
      *'"subagentPromptCacheTtl"'*)
        _s=${_set#*'"subagentPromptCacheTtl"'}
        while :; do case "$_s" in [' :	']*) _s=${_s#?} ;; *) break ;; esac; done
        case "$_s" in '"1h"'*) cold=$TTL_1H ;; '"5m"'*) cold=$TTL_5M ;; esac ;;
    esac
  fi
fi
if [ -z "$cold" ]; then
  if [ "${ENABLE_PROMPT_CACHING_1H:-}" = 1 ]; then cold=$TTL_1H; else cold=$TTL_5M; fi
fi
[ "${FORCE_PROMPT_CACHING_5M:-}" = 1 ] && cold=$TTL_5M
if [ "$cold" = "$TTL_1H" ]; then ttl='1 시간'; else ttl='5 분'; fi
[ "$age" -ge "$cold" ] || exit 0
# 다시 읽힐 맥락 — 끝 조각의 마지막 사용량. 없으면 바이트로 어림한다
tok=; how='기록 크기로 어림해'
_tl=$(tail -c "$TAIL_BYTES" "$f" 2>/dev/null)
case "$_tl" in
  *'"usage":{'*)
    _u=${_tl##*'"usage":{'}
    _sum=0
    for _k in input_tokens cache_creation_input_tokens cache_read_input_tokens output_tokens; do
      case "$_u" in *"\"$_k\":"[0-9]*) ;; *) _sum=; break ;; esac
      _v=${_u#*"\"$_k\":"}; _v=${_v%%[!0-9]*}
      _sum=$((_sum + _v))
    done
    [ -n "$_sum" ] && { tok=$_sum; how='마지막 요청 기준'; } ;;
esac
[ -n "$tok" ] || tok=$((size / BYTES_PER_TOK))
[ "$tok" -ge "$MIN_TOK" ] || exit 0
_h=$((age / 3600)); _m=$((age % 3600 / 60))
if [ "$_h" -gt 0 ]; then gap="${_h}시간 ${_m}분"; else gap="${_m}분"; fi
msg="이어 묻기 값 — 받는 레인($to)은 마지막 기록 뒤 ${gap}이 지나 프롬프트 캐시(서브에이전트 $ttl)가 식었고, 이어 물으면 다시 읽힐 맥락이 $how 약 $((tok / 1000))k 토큰이다. 그 맥락을 캐시 없이 처음부터 다시 읽힌다."
if { printf '%s\n' "$size $mt" > "$mk"; } 2>/dev/null; then
  msg="$msg 이 레인의 이 상태에서는 이번 한 번만 막았다. 다음 걸음이 그 레인의 기억을 쓰면 같은 메시지를 그대로 다시 보내면 통과한다. 기억은 안 쓰고 고칠 자리만 같다면 Agent 로 새 봉투를 띄우는 쪽이 싸다(스킬 agent-envelope 1 절 「토큰」 줄)."
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$msg"
else
  msg="$msg 막기 표지를 못 써서 막지 않았다. 다음 걸음이 그 레인의 기억을 안 쓰고 고칠 자리만 같다면 새 봉투가 더 싸다(스킬 agent-envelope 1 절 「토큰」 줄)."
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}' "$msg"
fi
exit 0
