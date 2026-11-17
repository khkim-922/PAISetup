# matcher = Agent
# events = PreToolUse
# var = _et
#
# 봉투 꼬리 알림 — 레인(서브에이전트)을 띄우는 `Agent` 호출의 프롬프트에 스킬 agent-envelope 틀의 보고 꼬리(판정 자 줄)가 없으면,
# 그 띄우기의 결과 곁에 그 사실과 거둘 때의 자(스킬 norm-review-fix)를 한 줄로 붙인다(PreToolUse 훅 · claude-config #278).
# 붙이기만 한다 — 막지 않는다. 한두 줄 조회처럼 꼬리를 일부러 안 싣는 띄우기도 있다(#278 「안 하는 것」).
#
# **왜 있나.** 레인이 가져온 리뷰 지적의 자(스킬 norm-review-fix · 결정 0216 · 0244)는 봉투 보고 꼬리 한 줄에 기대고, 그 줄은
# 봉투를 틀(`assets/envelope.md`)로 쓸 때만 실린다. 손으로 쓴 봉투의 레인은 지적을 판정 없이 돌려줬고 부모도 가름을 건너뛰었다
# (#278 — 날짜와 자리는 그 이슈가 든다). 부모 쪽에 레인 보고가 도착하는 순간 거는 훅 이벤트는 없어(#278 의 훅 문서 정리)
# 띄우는 순간에 건다 — 원인(손으로 쓴 봉투)이 보이는 자리가 거기다.
#
# 닿는 때 — PreToolUse 의 덧말(`additionalContext`)은 도구가 돈 뒤 그 결과 곁에 실린다(Claude Code 훅 문서 「PreToolUse decision
#   control」 · 이 PC 기록에서 그림 문의 덧말이 도구 결과 앞에 붙은 실측). 그래서 이 줄은 띄우기 **전이 아니라** 띄운 결과와 함께
#   부모에게 간다 — 배경 레인은 띄우자마자(`async_launched`), 앞에서 도는 레인은 보고가 돌아올 때. 글은 두 때에 다 서게 쓴다
#   (거둘 때의 자를 댄다). 띄우기 전에 세우려면 막아야(`deny`) 하는데, 막기는 #278 이 뺐다.
#
# 거는 꼴 — 매처가 `Agent` 하나다. 글자만 든 매처는 정확한 이름으로 맞는다(Claude Code 훅 문서 「matcher」) — 다른 도구 호출에는
#   셸이 안 뜬다. ⚠ `.` · `*` · `^` 를 섞으면 이름의 일부로 맞기 시작한다 — 매처를 넓히지 않는다(사용자 결정 · 띄우기 한 번에 셸
#   하나 · #278). 입력의 tool_name 도 한 번 더 본다. `Agent` 는 Claude Code 의 도구라 등록도 갈 곳 표의 Claude 길로만 선다.
#
# 꼬리 글자 — 이 파일에 옮겨 적지 않고, 띄울 때마다 Claude 홈에 놓인 틀에서 읽는다(규범 [Single Source · Point or Derive]).
#   읽는 자리 `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/agent-envelope/assets/envelope.md` — 부모가 스킬을 열어 베끼는 바로 그
#   사본이라, 판이 어긋날 수 없다. 그 자리에 틀이 없으면 이름 댈 틀도 없어 말이 없다.
#   가르는 글자 — 틀에서 `norm-review-fix` 가 든 첫 줄의, 그 이름 앞으로 이어진 ASCII 글자 묶음(앞 빈칸은 떼고 `"` · `\` 에서
#   끊는다) + 그 이름. 지금 틀에서는 `the ruler for the verdict is norm-review-fix` 다. 이 묶음은 틀의 줄 그대로 베낀 봉투에도,
#   줄을 이어 붙인 봉투에도 같은 꼴로 선다. ASCII 만 쓰는 까닭 — 입력 JSON 이 비 ASCII 를 `\u` 로 싸든 안 싸든 같은 글자로
#   맞고, `"` · `\` 가 안 들어 JSON 이스케이프에 안 걸린다.
#   ⚠ 틀의 꼬리를 고쳐도 이 훅은 따라간다. 다만 꼬리가 `norm-review-fix` 를 더 안 대거나, 꼬리보다 앞줄에 그 이름이 서면 가르는
#   글자가 꼬리를 떠난다 — 검사(`scripts/check-envelope-tail-note.py`)가 틀 그대로의 꼬리로는 말이 없고 꼬리를 뺀 틀로는 한 줄이
#   서나를 문다. 틀(`envelope.md`)을 담으면 게이트가 그 검사를 깨운다.
#   부모가 꼬리 줄 가운데서 줄을 바꿔 베끼면 그 묶음이 끊겨 헛알림 한 줄이 선다 — 막지 않으니 값은 그 한 줄이다.
#
# ⚠ **셸 밖의 프로세스를 하나도 안 띄운다** — 입력은 셸 `read` 로, 틀은 `read` 로 읽고 판정은 `case` 다. 등록 명령이 띄우는 셸
#   하나가 띄우기 한 번의 값 전부다(회사 PC 에서 프로세스 하나가 약 0.3 초 — claude-config #197). 입력(봉투 통째 · 몇 KB ~ 수십
#   KB)은 파이프라 셸이 바이트씩 읽는다 — 이 PC 에서 24 KB 가 약 0.1 초였다.
# ⚠ **입력은 압축된 JSON 이다**(키와 값 사이에 공백이 없다 — `web-retry.sh` 의 실측). 꼬리는 입력 어디에 서든 맞는다 —
#   `prompt` 칸만 잘라 내려면 JSON 문자열의 끝을 셸로 가려야 해, 그 값을 안 들인다.
# ⚠ **덧말은 사실로 쓴다** — 명령조의 바깥 글은 프롬프트 주입 방어에 걸릴 수 있다(Claude Code 훅 문서). 덧말에 큰따옴표 ·
#   역슬래시 · 줄바꿈을 안 넣는다 — JSON 글자 안에 그대로 실린다(가르는 글자도 그 둘을 못 들게 끊었다).
#
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 짓고, 머리말의 뜻과 심기는 명령 꼴은
# 표(`tool-homes.conf`)의 hook 꼴이 든다. 홈 등록은 이 파일을 점(`.`)으로 읽어 같은 셸 안에서 돌고, 끝의 `exit 0` 이 훅을 끝낸다.
#
# 시험 — `python -X utf8 scripts/check-envelope-tail-note.py` (손이 머리말로 짓는 등록 · 꼬리 있음 · 없음 · 다른 도구 · 띄우는
#   프로세스 수를 문다).
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
j=; while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done
case "$j" in *'"tool_name":"Agent"'*) ;; *) exit 0 ;; esac
_ef="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/agent-envelope/assets/envelope.md"
[ -f "$_ef" ] || exit 0
_t=; while IFS= read -r _l || [ -n "$_l" ]; do
  case "$_l" in *norm-review-fix*) _t=$_l; break ;; esac
done < "$_ef"
[ -n "$_t" ] || exit 0
# 가르는 글자 — 머리말 「꼬리 글자」
_k=${_t%%norm-review-fix*}
_k=${_k##*[! -~]}
_k=${_k##*[\"\\]}
while :; do case "$_k" in ' '*) _k=${_k# } ;; *) break ;; esac; done
_k="${_k}norm-review-fix"
case "$j" in *"$_k"*) exit 0 ;; esac
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}' "레인 봉투 꼬리 알림 — 이 Agent 띄우기의 프롬프트에 스킬 agent-envelope 틀(assets/envelope.md)의 보고 꼬리가 없다. 그 꼬리의 판정 자 줄(${_k})이 안 보여, 봉투를 그 틀로 쓰지 않은 띄우기로 보인다. 이 레인이 리뷰 지적을 가져오면 판정 없이 올 수 있다 — 거둘 때 지적마다 이번 변경이 만든 것인가 · 심각도 · 닿는 길을 보고 스킬 norm-review-fix 로 고친다 · 버린다 · 이슈로를 가른다. 막지 않았다 — 한두 줄 조회처럼 꼬리가 필요 없는 띄우기면 그대로 둔다."
exit 0
