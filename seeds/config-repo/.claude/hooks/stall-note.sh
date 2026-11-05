# events = UserPromptSubmit
# var = _sn
#
# 머리 없이 선 요청 알림 — 사내 로컬 프록시가 이 세션 몫으로 남긴 「요청 하나가 응답 머리 없이 몇 초 섰다가 끊겼다」 줄을
# 다음 프롬프트 곁에 싣고 지운다(UserPromptSubmit 훅). 붙이기만 한다 — 막지 않는다.
#
# **왜 있나.** 첫 바이트를 못 받은 요청은 모델 쪽에서 보면 한 글자도 안 쓴 판이라, 사람이 ESC 로 끊거나 프록시가 시한에
# 끊어도 모델은 그 멈춤을 모른 채 다음 말을 받는다. 멈춤을 아는 것은 프록시뿐이라 프록시가 적고 이 훅이 나른다(claude-config #237).
# 줄을 짓는 쪽 · 남기는 문턱 · 글은 프록시(`posco/pgpt-proxy/opus5_proxy.py` 의 `note_stall`)가 든다.
#
# 읽는 자리 — `%LOCALAPPDATA%\PGPT-Proxy\notes\<세션 번호>.txt`. 폴더 이름은 설치기가 프록시를 놓는 자리(PAISetup `install.ps1`
#   의 `$ProxyDirName`)이고, `notes` 는 프록시의 `STALL_NOTES_DIR` 다 — ⚠ 셋 가운데 하나만 바꾸면 알림이 조용히 끊긴다.
#   프록시가 없는 자리(사외 · 리눅스)는 파일이 없어 아무것도 안 낸다.
# ⚠ **입력은 압축된 JSON 이다**(키와 값 사이에 공백이 없다 — `web-retry.sh` 의 실측). 세션 번호는 uuid 꼴만 받는다 —
#   파일 경로에 들어가므로 다른 글자가 들면 아무것도 안 한다.
# ⚠ **파일이 없으면 셸 밖의 프로세스를 하나도 안 띄운다** — 이 훅은 프롬프트마다 돈다. 파일이 있을 때만 `mv` · `cat` · `rm` 이
#   돈다. 읽기 전에 이름을 옮겨, 읽는 사이 프록시가 잇는 줄은 다음 프롬프트로 넘긴다.
# ⚠ **글은 프록시가 사실로 짓는다** — 명령조의 바깥 글은 프롬프트 주입 방어에 걸릴 수 있다(Claude Code 훅 문서). 출력은 맨
#   글이고 하네스가 모델 곁 문맥으로 싣는다.
#
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 이 줄들로 등록을 짓는다. 머리말의
# 뜻과 심기는 명령 꼴은 표(`tool-homes.conf`)의 hook 꼴이 든다. ⚠ UserPromptSubmit 이라 matcher 줄을 안 둔다(#120).
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
[ -n "${LOCALAPPDATA:-}" ] || exit 0
j=; while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done
_s=${j#*\"session_id\":\"}
[ "$_s" != "$j" ] || exit 0
_s=${_s%%\"*}
case "$_s" in ''|*[!0-9a-f-]*) exit 0 ;; esac
_n="$LOCALAPPDATA/PGPT-Proxy/notes/$_s.txt"
[ -f "$_n" ] || exit 0
mv -f "$_n" "$_n.reading" 2>/dev/null || exit 0
cat "$_n.reading"
rm -f "$_n.reading"
exit 0
