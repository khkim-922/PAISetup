# matcher = Read
#
# DRM 길잡이 껍데기 — 몸통(`drm-guide.py`) 앞에서 먼저 거른다. 왜와 갈래는 몸통 머리말이 든다.
#
# 홈 `~/.claude/settings.json` 의 UserPromptSubmit · PostToolUseFailure 둘에 같은 한 줄로 심긴다 — 심는 손은
# 이 자리만 채운다:
#     _dg="<이 파일이 있는 자리>"; [ -f "$_dg/drm-guide.sh" ] || exit 0; . "$_dg/drm-guide.sh"
# 윗줄 `# matcher = …` 가 두 항목의 matcher 진본이다. **UserPromptSubmit 은 matcher 를 안 받아** 그 항목에서는 같은
# 값이 무시된다(공식 훅 문서 — matcher 를 못 받는 이벤트에 단 matcher 는 조용히 무시된다). 그래서 심는 손 하나가 두
# 이벤트에 같은 matcher 를 심는 꼴을 그대로 쓴다. 심는 손은 그림 문(`image-gate.sh`)과 같다 — `session-start-body.sh`
# 와 배포본 설치기. 주인 규율도 같다.
#
# ⚠ **점(`.`)으로 부른다** — 같은 셸 안에서 돌아 프로세스가 안 는다. 그래서 끝의 `exit 0` 이 훅을 끝낸다.
# ⚠ **파이썬은 오피스 · PDF 낌새(확장자)가 있을 때만 띄운다** — UserPromptSubmit 은 사람이 글을 보낼 때마다 걸려,
#   매번 띄우면 그 값이 모든 턴의 머리에 붙는다. 소문자로 눌러 재므로 확장자는 한 벌만 든다.
#   ⚠ **글롭은 스킬의 확장자 표(`read-drm.ps1` 의 `$HANDLER`)를 다 덮어야 한다** — 표에 확장자가 늘었는데 여기
#     없으면 그 파일은 조용히 안 걸린다. `scripts/check-drm-guide.py` 가 표의 확장자마다 이 껍데기를 지나 걸리나를 잰다.
# ⚠ **파이썬은 존재가 아니라 불러 보고 고른다** — 윈도우의 `python3` 는 스토어 껍데기라 49 로 죽는다.
#   못 뜨면 「못 쟀다」 한 줄을 직접 낸다 — 길잡이가 죽은 사실이 어디에도 안 남는 것이 침묵보다 비싸다.
#   막지는 않는다 — 이 훅은 길을 가리키기만 한다.
#
# 시험 — `python -X utf8 scripts/check-drm-guide.py` (감긴 표본 다섯과 지은 평문 머리를 먹여 걸 것과 둘 것을 문다).
# shellcheck shell=sh  # 점으로 읽혀 셔뱅이 없다 — 어느 셸이 읽어도 서게 POSIX 로 잰다
j=$(cat)
l=$(printf %s "$j" | tr A-Z a-z)
case "$l" in
  *.doc*|*.xls*|*.ppt*|*.pdf*|*.rtf*|*.csv*)
    py=
    for p in python python3; do
      "$p" -X utf8 -c "" >/dev/null 2>&1 && { py=$p; break; }
    done
    if [ -n "$py" ]; then
      # shellcheck disable=SC2154 # _dg 는 홈에 심긴 한 줄이 이 파일을 읽기 전에 세운다(머리말)
      printf %s "$j" | "$py" -X utf8 "$_dg/drm-guide.py"
    else
      ev=UserPromptSubmit
      case "$j" in *'"hook_event_name":"PostToolUseFailure"'*) ev=PostToolUseFailure ;; esac
      printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}' "$ev" \
        'DRM 길잡이 — 파이썬이 안 떠서 이 글의 오피스 · PDF 가 DRM 에 감겼는지 못 쟀다. 감긴 파일(머리에 DRMONE)은 Read 와 파서로 안 열리고, 스킬 drm-office-read 가 설치된 오피스로 글자를 뽑는다.'
    fi
    ;;
esac
exit 0
