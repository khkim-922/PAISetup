# matcher = Read
# matcher.PreToolUse = *
#
# DRM 길잡이 껍데기 — 몸통(`drm-guide.py`) 앞에서 먼저 거른다. 왜와 갈래는 몸통 머리말이 든다.
#
# 홈 `~/.claude/settings.json` 의 UserPromptSubmit · PreToolUse · PostToolUseFailure 셋에 같은 한 줄로 심긴다 —
# 심는 손은 이 자리만 채운다:
#     _dg="<이 파일이 있는 자리>"; [ -f "$_dg/drm-guide.sh" ] || exit 0; . "$_dg/drm-guide.sh"
# 윗줄 둘이 matcher 진본이다 — 꾸밈 없는 `# matcher =` 는 **PostToolUseFailure** 것이고,
# `# matcher.PreToolUse =` 는 **PreToolUse** 것이다. 자리가 둘인 까닭은 보는 것이 다르기 때문이다:
# 저쪽은 Read 가 진 자리만, 이쪽은 **첨부를 아직 못 알린 턴의 첫 도구 호출**이다.
# ⚠ **PreToolUse 는 도구를 안 가린다(`*`).** 「첫 도구 호출」이 뜻이라면 그 첫 도구가 무엇일지 못 고른다 —
#   목록으로 적으면 그 밖의 도구로 턴을 시작한 날(웹 조회만 하고 답하는 턴) 그 첨부는 조용히 빠진다.
#   값은 아래 ② 의 거르기가 든다: 표지 둘이 한 줄에 함께 안 들면 파이썬을 아예 안 띄운다.
# ⚠ **UserPromptSubmit 항목에는 matcher 키를 안 심는다.** 그 이벤트는 matcher 를 안 받는데, 거는 자는 받지 않는
#   값을 조용히 무시하는 것이 아니라 **맞출 도구 이름이 없는 호출을 항목째 걸러낸다** — 심어 두면 훅이 영원히 안
#   돈다. 설정에도 코드에도 결함으로 안 보이고, 몸통에 입력을 손으로 먹이면 멀쩡히 통과해 「코드는 맞는데 안
#   걸린다」로만 나타난다(claude-config #120 실측). 그래서 심는 손이 이벤트마다 키를 가른다.
# 심는 손은 그림 문(`image-gate.sh`)과 같다 — `session-start-body.sh` 와 배포본 설치기. 주인 규율도 같다.
#
# ⚠ **점(`.`)으로 부른다** — 같은 셸 안에서 돌아 프로세스가 안 는다. 그래서 끝의 `exit 0` 이 훅을 끝낸다.
# ⚠ **파이썬은 낌새가 있을 때만 띄운다** — UserPromptSubmit 과 PreToolUse 는 사람이 글을 보낼 때마다 · 도구를 부를
#   때마다 걸려, 매번 띄우면 그 값이 모든 턴의 머리에 붙는다. 낌새는 둘이다:
#   ① 입력에 오피스 · PDF 확장자 — 소문자로 눌러 재므로 확장자는 한 벌만 든다.
#     ⚠ **글롭은 스킬의 확장자 표(`read-drm.ps1` 의 `$HANDLER`)를 다 덮어야 한다** — 표에 확장자가 늘었는데 여기
#       없으면 그 파일은 조용히 안 걸린다. `scripts/check-drm-guide.py` 가 표의 확장자마다 이 껍데기를 지나 걸리나를 잰다.
#   ② (UserPromptSubmit · PreToolUse) 기록에 **이 턴의** 문서 블록 표지 — 앱의 「+」 PDF 는 입력에 아무 낌새도 안
#     남기고 기록의 이 턴 사용자 줄에만 실린다(몸통 머리말). 그 줄을 `prompt_id` 로 **지목**해 찾는다 — 꼬리 몇 줄을
#     더듬는 길은 **언제 보느냐**에 매여 양쪽에서 조인다: 제출 때는 그 줄이 아직 안 써졌고(VS Code 앱에서 훅이
#     1.4 초 이르다) 42 초쯤 뒤면 창에서 밀려난다. 지목은 몇 줄째인지와 무관하다.
#     ⚠ **한 줄에 두 표지가 함께 드나를 본다** — `promptId` 와 문서 블록이 **각각** 어딘가에 있는 것으로는 안 된다.
#       `grep` 한 번으로 두 표지를 한 줄에서 재려면 이어 거는 꼴(`grep … | grep …`)이 든다.
#     ⚠ **바이트로 끊지 않는다 — 줄 수로 끊는다.** 두 표지는 한 줄의 **머리 300 B 안**에 서고(실측: `promptId` 73 ·
#       `document` 174) 그 뒤가 MB 단위 base64 다. 끝에서 바이트로 자르면 큰 첨부에서는 남는 것이 순수 base64 꼬리라
#       **두 표지가 함께 잘려 조용히 안 걸린다** — 4 MB 로 잘랐을 때 6.7 MB 줄이 그렇게 빠졌다(#120 실측).
#       `grep` 은 줄 단위라 긴 줄을 만나도 그 줄만 들고, 꼬리 줄 수를 적게 쥐면 기록 앞은 안 건드린다.
#       ⚠ 줄 수는 **이 턴의 줄이 드는 창**이라 넉넉해야 한다 — 그 사이에 메타 줄과 도구 주고받기가 쌓인다.
#       지목이 「몇 줄째」에 안 매이므로 넓혀도 오인이 안 난다: 창 밖으로 밀린 턴은 몸통이 그 값으로 다시 찾는다.
#     기록 자리는 입력의 `transcript_path` 를 JSON 글자 그대로 쓴다 — 윈도우 경로의 역슬래시가 겹쳐(`\\`) 오지만 Git
#     Bash 는 겹친 구분자를 하나로 읽는다(검사가 윈도우 경로로 잰다). 기록은 늘 홈의 `.claude/projects` 밑이라 UNC
#     경로가 안 온다.
# ⚠ **파이썬은 존재가 아니라 불러 보고 고른다** — 윈도우의 `python3` 는 스토어 껍데기라 49 로 죽는다.
#   못 뜨면 「못 쟀다」 한 줄을 직접 낸다 — 길잡이가 죽은 사실이 어디에도 안 남는 것이 침묵보다 비싸다.
#   막지는 않는다 — 이 훅은 길을 가리키기만 한다.
#
# 시험 — `python -X utf8 scripts/check-drm-guide.py` (감긴 표본 · 지은 평문 머리 · 지은 기록을 먹여 걸 것과 둘 것을 문다).
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
DRM_TAIL_LINES=64          # 기록 끝에서 볼 줄 수 — 이 턴의 줄이 드는 창(머리말 ⚠). 줄 단위라 긴 줄도 통째로 든다
j=$(cat)
l=$(printf %s "$j" | tr A-Z a-z)
run=
case "$l" in
  *.doc*|*.xls*|*.ppt*|*.pdf*|*.rtf*|*.csv*) run=1 ;;
esac
if [ -z "$run" ]; then
  case "$j" in
    *'"hook_event_name":"UserPromptSubmit"'*|*'"hook_event_name":"PreToolUse"'*)
      t=${j#*'"transcript_path":"'}
      p=${j#*'"prompt_id":"'}
      if [ "$t" != "$j" ] && [ "$p" != "$j" ]; then
        t=${t%%'"'*}
        p=${p%%'"'*}
        # 두 표지가 **한 줄에** 함께 들어야 한다 — 이어 걸어 그 줄만 남긴다
        [ -f "$t" ] && tail -n "$DRM_TAIL_LINES" "$t" 2>/dev/null \
          | grep -F "\"promptId\":\"$p\"" 2>/dev/null \
          | grep -q -F '"type":"document"' && run=1
      fi
      ;;
  esac
fi
if [ -n "$run" ]; then
  py=
  for p in python python3; do
    "$p" -X utf8 -c "" >/dev/null 2>&1 && { py=$p; break; }
  done
  if [ -n "$py" ]; then
    # shellcheck disable=SC2154 # _dg 는 홈에 심긴 한 줄이 이 파일을 읽기 전에 세운다(머리말)
    printf %s "$j" | "$py" -X utf8 "$_dg/drm-guide.py"
  else
    ev=UserPromptSubmit
    case "$j" in
      *'"hook_event_name":"PreToolUse"'*) ev=PreToolUse ;;
      *'"hook_event_name":"PostToolUseFailure"'*) ev=PostToolUseFailure ;;
    esac
    printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}' "$ev" \
      'DRM 길잡이 — 파이썬이 안 떠서 이 턴의 오피스 · PDF(글의 경로 · 첨부)가 DRM 에 감겼는지 못 쟀다. 감긴 파일(머리에 DRMONE)은 Read 와 파서로 안 열리고, 스킬 drm-office-read 가 Fasoo 에이전트가 도는 PC 의 오피스로 글자를 뽑는다.'
  fi
fi
exit 0
