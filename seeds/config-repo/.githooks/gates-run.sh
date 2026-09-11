#!/bin/sh
# 게이트 러너 — 몸통 둘(pre-commit · commit-msg)이 같이 쓰는 한 벌.
#
# 진본은 claude-config/.githooks/gates-run.sh 다. 각 저장소의 것은 deploy.ps1 이
# 뿌린 배포본이다 — 배포본을 고치면 다음 배포에 덮인다.
#
# **이 파일은 저장소 이름도 검사 이름도 모른다.** 목록의 진본은 선언 하나다:
#   .githooks/gates.conf   이 저장소가 어느 조각을 켜나 — 저장소가 커밋한다
# 검사가 늘면 조각을 더하고 선언에 한 줄을 적는다. 이 파일을 고치는 것은 새 계약이
# 필요할 때뿐이다 (도구 선언 tools.conf 와 같은 결 · claude-config 0004).
#
# ── 조각 계약 ───────────────────────────────────────────────────────────────
#   자리      .githooks/gates.d/<이름>.sh — 선언의 이름이 곧 파일 이름이다
#   들어가는 것  작업 디렉터리가 저장소 뿌리. PROJECT_DIR 이 서 있다.
#              commit-msg 절의 조각은 메시지 파일 경로를 $1 로 받는다
#   나오는 것    0 통과 · 1 어긋남 · **2 못 쟀다**(도구가 없어 이 검사를 못 돌렸다)
#
# ⚠ **2 를 어긋남으로 안 센다.** 재는 자가 없는 기계에서 무관한 커밋까지 막으면
#   `--no-verify` 가 습관이 되고, 그러면 게이트가 없는 것만 못해진다.
# ⚠ **그러나 조용히 넘기지도 않는다.** 못 잰 것을 판정 옆에 찍는다 — 「전부 통과」는
#   *여기까지* 통과인데 안 적으면 전부로 읽힌다(규범 [Goal-Driven Execution]).
# ⚠ **하나가 빨개도 나머지를 다 돌린다.** 한 판에 무엇이 빨간지 다 보이는 편이,
#   고칠 때마다 다음 빨강을 하나씩 만나는 것보다 낫다.
# ⚠ **선언에 있는데 파일이 없으면 어긋남이다.** 배포가 안 닿은 저장소에서 검사가
#   조용히 빠지는 자리를 여기서 막는다 — 부재가 통과로 읽히는 바로 그 자리다.

# gate_list <절> <선언파일> — 절 안의 이름을 한 줄에 하나씩. '#' 주석·빈 줄·CRLF 방어.
gate_list() {
    [ -f "$2" ] || return 0
    sed 's/\r$//' "$2" | awk -v sec="$1" '
        /^\[[^]]*\][[:space:]]*$/ {
            s = $0; gsub(/[][]/, "", s); gsub(/[[:space:]]+$/, "", s)
            insec = (s == sec); next
        }
        !insec { next }
        { sub(/[[:space:]]*#.*$/, ""); gsub(/^[[:space:]]+|[[:space:]]+$/, "")
          if ($0 != "") print }
    '
}

# run_gates <절> [조각에 넘길 인자…]
run_gates() {
    _stage="$1"; shift
    _conf="$PROJECT_DIR/.githooks/gates.conf"

    # ⚠ **선언이 없는 저장소는 잴 것이 없다** — 막지 않고 지나간다. 게이트를 아직 안 켠
    #   저장소도 정당하기 때문이다. 다만 자리를 말하고 간다: 있다고 믿는 채 없는 것이
    #   제일 나쁘다.
    if [ ! -f "$_conf" ]; then
        printf '· 게이트 선언이 없다(.githooks/gates.conf) — 이 저장소는 아무것도 안 잰다.\n' >&2
        return 0
    fi

    # ⚠ **조각은 하위 셸에서 돈다** — `export` 없이는 계약의 PROJECT_DIR 이 안 넘어가고,
    #   조각은 `set -u` 아래서 그 자리에 죽는다. 계약을 지키는 자리는 러너 한 곳이다.
    export PROJECT_DIR

    _fail=0; _cant=''; _ran=0
    for _g in $(gate_list "$_stage" "$_conf"); do
        _f="$PROJECT_DIR/.githooks/gates.d/$_g.sh"
        if [ ! -f "$_f" ]; then
            printf '✖ 선언에 [%s] 가 있는데 조각이 없다: .githooks/gates.d/%s.sh\n' "$_g" "$_g" >&2
            printf '  배포가 안 닿았다 — 설정 저장소에서 deploy.ps1 을 돌리고 이 저장소에서 커밋한다.\n' >&2
            _fail=1
            continue
        fi
        _ran=$((_ran + 1))
        sh "$_f" "$@"
        case "$?" in
            0) ;;
            2) _cant="$_cant $_g" ;;
            *) _fail=1 ;;
        esac
    done

    # 못 잰 것은 초록 옆에 찍는다 — 줄이려고 두는 목록이지 채우려고 두는 것이 아니다.
    [ -z "$_cant" ] || printf '· 못 쟀다:%s — 도구가 없어 건너뛴 검사다. 세션을 열면 훅이 깐다.\n' "$_cant" >&2
    [ "$_ran" -gt 0 ] || [ -n "$_cant" ] ||
        printf '· [%s] 절에 켜진 조각이 없다 — 이 단계는 아무것도 안 잰다.\n' "$_stage" >&2

    [ "$_fail" -eq 0 ] || printf '\n' >&2
    return "$_fail"
}
