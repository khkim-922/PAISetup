# matcher = Read
# events = UserPromptSubmit,PostToolUseFailure
# var = _dg
#
# DRM 길잡이 껍데기 — 몸통(`drm-guide.py`) 앞에서 먼저 거른다. 왜와 갈래는 몸통 머리말이 든다.
#
# 윗줄들이 홈 `~/.claude/settings.json` 등록의 진본이다 — 갈 곳 표의 손(`tool-homes.py`)이 두 이벤트에 같은 명령으로
# 짓고, 몸통은 그 등록이 세운 `$_dg` 곁에 같이 실린다. 머리말의 뜻과 심기는 명령 꼴은 표(`tool-homes.conf`)의 hook 꼴이
# 든다. `matcher` 는 **PostToolUseFailure** 것이다 — Read 가 진 자리만 본다.
# ⚠ **PreToolUse 에는 안 건다.** 그 자리는 「제출 때 아직 안 써진 첨부 줄을 첫 도구 호출에서 다시 보는」 몫(VS Code 앱 —
#   몸통 머리말)인데, 도구를 못 가려 `*` 로 걸어야 하고 그러면 회사 PC 에서 모든 도구 호출에 프로세스 하나(약 0.27 초)가 붙는다.
#   그 값이 지키는 것보다 커서 안 건다(claude-config #213) — VS Code 앱에서 감긴 PDF 를 「+」로 붙인 턴은 자동 안내가 없다.
#   몸통의 PreToolUse 갈래는 agy · Codex 어댑터가 쓴다(`agy-hooks.py` · `codex-hooks.example.toml`).
# ⚠ **UserPromptSubmit 항목에는 matcher 키를 안 심는다.** 그 이벤트는 matcher 를 안 받는데, 거는 자는 받지 않는
#   값을 조용히 무시하는 것이 아니라 **맞출 도구 이름이 없는 호출을 항목째 걸러낸다** — 심어 두면 훅이 영원히 안
#   돈다. 설정에도 코드에도 결함으로 안 보이고, 몸통에 입력을 손으로 먹이면 멀쩡히 통과해 「코드는 맞는데 안
#   걸린다」로만 나타난다(claude-config #120 실측). 그래서 손이 그 이벤트에는 키를 안 둔다.
#
# ⚠ **점(`.`)으로 부른다** — 같은 셸 안에서 돌아 프로세스가 안 는다. 그래서 끝의 `exit 0` 이 훅을 끝낸다.
# ⚠ **파이썬은 낌새가 있을 때만 띄운다** — UserPromptSubmit 은 사람이 글을 보낼 때마다 걸려, 매번 띄우면 그 값이 모든
#   턴의 머리에 붙는다. 낌새는 둘이다:
#   ① 입력에 오피스 · PDF 확장자 — 대소문자는 글자 묶음(`[Pp][Dd][Ff]`)으로 가리므로 확장자는 한 벌만 든다.
#     ⚠ **글롭은 스킬의 확장자 표(`read-drm.ps1` 의 `$HANDLER`)를 다 덮어야 한다** — 표에 확장자가 늘었는데 여기
#       없으면 그 파일은 조용히 안 걸린다. `scripts/check-drm-guide.py` 가 표의 확장자마다 이 껍데기를 지나 걸리나를 잰다.
#   ② (UserPromptSubmit) 기록에 **이 턴의** 문서 블록 표지 — 앱의 「+」 PDF 는 입력에 아무 낌새도 안
#     남기고 기록의 이 턴 사용자 줄에만 실린다(몸통 머리말). 그 줄을 `prompt_id` 로 **지목**해 찾는다 — 꼬리 몇 줄을
#     더듬는 길은 **언제 보느냐**에 매여 양쪽에서 조인다: 제출 때는 그 줄이 아직 안 써졌고(VS Code 앱에서 훅이
#     1.4 초 이르다) 42 초쯤 뒤면 창에서 밀려난다. 지목은 몇 줄째인지와 무관하다.
#     ⚠ **한 줄에 두 표지가 함께 드나를 본다** — `promptId` 와 문서 블록이 **각각** 어딘가에 있는 것으로는 안 된다.
#       `grep` 한 번으로 한 줄 안의 두 표지를 재려면 정규식 `앞.*뒤` 를 앞뒤 바꿔 둘 건다 — 표지의 앞뒤 차례가 줄 꼴마다
#       달라서다. 줄은 셸이 `read` 로 읽어 가르지 않는다: 한 줄이 MB 단위면 셸은 바이트씩 읽어 초 단위로 들고 `grep` 은
#       0.1 초 안쪽이다. `LC_ALL=C` 는 `.` 이 깨진 UTF-8 바이트에서 멈춰 표지를 놓치지 않게 한다.
#     ⚠ **바이트로 끊지 않는다 — 줄 수로 끊는다.** 두 표지는 한 줄의 **머리 300 B 안**에 서고(실측: `promptId` 73 ·
#       `document` 174) 그 뒤가 MB 단위 base64 다. 끝에서 바이트로 자르면 큰 첨부에서는 남는 것이 순수 base64 꼬리라
#       **두 표지가 함께 잘려 조용히 안 걸린다** — 4 MB 로 잘랐을 때 6.7 MB 줄이 그렇게 빠졌다(#120 실측).
#       `grep` 은 줄 단위라 긴 줄을 만나도 그 줄만 들고, 꼬리 줄 수를 적게 쥐면 기록 앞은 안 건드린다.
#       ⚠ 줄 수는 **이 턴의 줄이 드는 창**이라 넉넉해야 한다 — 그 사이에 메타 줄과 도구 주고받기가 쌓인다.
#       지목이 「몇 줄째」에 안 매이므로 넓혀도 오인이 안 난다: 창 밖으로 밀린 턴은 몸통이 그 값으로 다시 찾는다.
#     기록 자리는 입력의 `transcript_path` 를 JSON 글자 그대로 쓴다 — 윈도우 경로의 역슬래시가 겹쳐(`\\`) 오지만 Git
#     Bash 는 겹친 구분자를 하나로 읽는다(검사가 윈도우 경로로 잰다). 기록은 늘 홈의 `.claude/projects` 밑이라 UNC
#     경로가 안 온다.
# ⚠ **낌새 앞 구간은 `sh` 밖의 프로세스를 하나도 안 띄운다** — 입력은 셸 `read` 로 받고(`cat` 없이) 확장자는 글자 묶음
#   글롭으로 가린다(`tr` 없이). 회사 PC 에서는 프로세스 하나가 약 0.3 초라, 걸릴 때마다 그 수만큼 값이 붙는다.
#   `tail` · `grep` 은 ② 의 기록 읽기에만 남는다.
# ⚠ **파이썬은 존재가 아니라 불러 보고 고른다** — 윈도우의 `python3` 는 스토어 껍데기라 49 로 죽는다.
#   못 뜨면 「못 쟀다」 한 줄을 직접 낸다 — 길잡이가 죽은 사실이 어디에도 안 남는 것이 침묵보다 비싸다.
#   막지는 않는다 — 이 훅은 길을 가리키기만 한다.
#
# 시험 — `python -X utf8 scripts/check-drm-guide.py` (감긴 표본 · 지은 평문 머리 · 지은 기록을 먹여 걸 것과 둘 것을 문다).
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
DRM_TAIL_LINES=64          # 기록 끝에서 볼 줄 수 — 이 턴의 줄이 드는 창(머리말 ⚠). 줄 단위라 긴 줄도 통째로 든다
j=; while IFS= read -r _l || [ -n "$_l" ]; do j="$j$_l"; done
run=
case "$j" in
  *.[Dd][Oo][Cc]*|*.[Xx][Ll][Ss]*|*.[Pp][Pp][Tt]*|*.[Pp][Dd][Ff]*|*.[Rr][Tt][Ff]*|*.[Cc][Ss][Vv]*) run=1 ;;
esac
if [ -z "$run" ]; then
  case "$j" in
    *'"hook_event_name":"UserPromptSubmit"'*)
      t=${j#*'"transcript_path":"'}
      if [ "$t" != "$j" ]; then
        t=${t%%'"'*}
        if [ -f "$t" ]; then
          # 꼴이 둘이다(#124) — 옛 꼴은 이 턴 값과 문서 표지가 **한 줄에** 함께 들어야 하고, 큐에 담기는
          # 꼴은 그 값이 아예 없어 사람이 보낸 첨부 줄(`humanTurn`)로 가른다. 가르는 것은 몸통이 다시
          # 하므로 여기서는 띄울지만 정한다 — 둘 가운데 하나라도 보이면 띄운다. 값은 정규식에 들어가므로
          # 낯선 글자가 든 값은 자리를 넓혀(`[^"]*`) 띄우는 쪽으로 틀린다
          k='"humanTurn":true'
          d='"type":"document"'
          p=${j#*'"prompt_id":"'}
          if [ "$p" != "$j" ]; then
            p=${p%%'"'*}
            case "$p" in
              *[!A-Za-z0-9_-]*) q='"promptId":"[^"]*"' ;;
              *) q="\"promptId\":\"$p\"" ;;
            esac
          else
            q=$k
          fi
          tail -n "$DRM_TAIL_LINES" "$t" 2>/dev/null \
            | LC_ALL=C grep -q -E -e "$k.*$d" -e "$d.*$k" -e "$q.*$d" -e "$d.*$q" 2>/dev/null && run=1
        fi
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
      *'"hook_event_name":"PostToolUseFailure"'*) ev=PostToolUseFailure ;;
    esac
    printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}' "$ev" \
      'DRM 길잡이 — 파이썬이 안 떠서 이 턴의 오피스 · PDF(글의 경로 · 첨부)가 DRM 에 감겼는지 못 쟀다. 감긴 파일(머리에 DRMONE)은 Read 와 파서로 안 열리고, 스킬 drm-office-read 가 Fasoo 에이전트가 도는 PC 의 오피스로 글자를 뽑는다.'
  fi
fi
exit 0
