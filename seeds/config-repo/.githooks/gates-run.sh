#!/bin/sh
# 게이트 러너 — 몸통 셋(pre-commit · commit-msg · pre-push)이 같이 쓰는 한 벌.
#
# 원본은 claude-config/.githooks/gates-run.sh 다. **저장소마다 사본을 두지 않는다**(결정 0064) —
# 형제의 몸통이 찾는 자(`claude-config-path.sh`)로 이 파일(또는 홈 씨앗의 것)을 찾아 부른다.
#
# gates-contract: 2
# ⚠ **위 줄은 계약 표식이다 — 지우거나 바꾸지 않는다.** 찾는 자가 이 줄이 있는 러너만 받는다. 이 판은
#   조각을 저장소 → 러너 곁(GATES_DIR) 차례로 찾는데, 표식 없는 옛 러너는 저장소 안만 봐서 조각이 없는
#   형제의 커밋을 **전부 막는다**(설치된 옛 홈 씨앗이 그 판이다). 러너가 조각을 찾는 계약을 바꾸면 수를 올리고,
#   찾는 자가 받는 범위도 같이 고친다.
#
# **이 파일은 저장소 이름도 검사 이름도 모른다.** 무엇을 켜고 어떻게 띄우나의 진본은 선언 하나다:
#   .githooks/gates.conf   이 저장소가 어느 조각을 켜나 — 저장소가 커밋한다
#     [pre-commit] · [commit-msg] · [pre-push]   단계마다 켤 조각 이름
#     [when]    `이름 = 글롭 …` — 그 조각이 지키는 경로. 이 판에서 바뀐 경로가 하나도 안 걸리면 안 띄운다
#     [alone]   이름 — 다른 조각과 같이 돌면 안 되는 조각. 혼자 돈다
# 검사가 늘면 조각을 더하고 선언에 한 줄을 적는다. 이 파일을 고치는 것은 새 계약이
# 필요할 때뿐이다 (도구 선언 tools.conf 와 같은 결 · claude-config 0004).
#
# ── 조각 계약 ───────────────────────────────────────────────────────────────
#   자리      .githooks/gates.d/<이름>.sh — 선언의 이름이 곧 파일 이름이다.
#              저장소 것이 먼저고, 없으면 러너 곁(GATES_DIR/gates.d/)을 본다
#   들어가는 것  작업 디렉터리가 저장소 뿌리. PROJECT_DIR · GATES_STAGE(절 이름)가 서 있다.
#              GATES_CHANGED — 이 판에서 바뀐 경로를 한 줄에 하나 든 파일(셸 경로). 그 절에 [when] 선언을 든
#                조각이 있고 바뀐 경로를 물을 수 있을 때만 선다 — 없으면 조각이 제 손으로 묻는다.
#                상태(더함 · 지움)는 안 든다. 옮긴 파일은 옛 자리와 새 자리가 다 선다
#              commit-msg 절의 조각은 메시지 파일 경로를 $1 로 받는다
#              pre-push 절의 조각은 원격 이름 · 주소를 $1 · $2 로 받는다
#              표준입력은 늘 비어 있다 — 러너가 막는다(아래 고리)
#   나오는 것    0 통과 · 1 어긋남 · **2 못 쟀다**(도구가 없어 이 검사를 못 돌렸다)
#
# ⚠ **2 를 어긋남으로 안 센다.** 재는 자가 없는 기계에서 무관한 커밋까지 막으면
#   `--no-verify` 가 습관이 되고, 그러면 게이트가 없는 것만 못해진다.
# ⚠ **그러나 조용히 넘기지도 않는다.** 못 잰 것을 판정 옆에 찍는다 — 「전부 통과」는
#   *여기까지* 통과인데 안 적으면 전부로 읽힌다(규범 [Goal-Driven Execution]).
# ⚠ **하나가 빨개도 나머지를 다 돌린다.** 한 판에 무엇이 빨간지 다 보이는 편이,
#   고칠 때마다 다음 빨강을 하나씩 만나는 것보다 낫다.
# ⚠ **선언에 있는데 조각을 못 찾으면 「못 쟀다」다 — 어긋남이 아니다**(0064). 조각은 claude-config
#   (또는 홈 씨앗)에 살아, 못 찾는 것은 대개 이 PC 의 claude-config 가 뒤처진 탓이고 저장소가 고칠
#   일이 아니다. 막으면 그 저장소 커밋이 통째로 서고 `--no-verify` 가 습관이 된다. 조용히 넘기지는
#   않는다 — 이름을 대며 말하고 「못 쟀다」 목록에 올린다. 대가: 선언의 오타도 막히지 않는다.
#   걷은 조각(`_GATES_RETIRED`)은 예외다 — 못 찾아도 말없이 지나간다.
#
# ── 고르기([when]) ──────────────────────────────────────────────────────────
#   바뀐 경로 — pre-commit 은 담긴 것(`git diff --cached`), pre-push 는 올라갈 가지와 갈라진 자리부터 작업
#     트리까지다(`repo-gates` 조각 · 결정 0076 과 같은 뜻). 상태로 거르지 않고(지운 것도 바뀐 것이다)
#     `--no-renames` 로 묻는다(옮긴 파일은 떠난 자리도 바뀐 것이다). 다른 절은 안 고른다
#   글롭은 뿌리 기준 `/` 경로에 셸 `case` 무늬로 댄다 — `*` 는 `/` 도 넘는다. 넘치게 걸리는 쪽은 조각이
#     한 번 더 뜨는 값이고, 모자라게 걸리는 쪽은 검사가 조용히 빠지는 값이다
#   ⚠ **선언이 없거나 글롭이 빈 조각은 늘 띄운다** — 모르면 돈다. 빈 값을 「어디에도 안 걸린다」로 읽으면
#     한 줄 실수가 조각을 끈다
#   ⚠ **바뀐 경로를 못 물으면 안 고른다** — 다 띄우고 까닭을 말한다. git 이 싸서 낸 이름(따옴표 · 제어 문자가
#     든 이름 — 첫 글자가 `"` 다)이 하나라도 있어도 같다: 싼 글자에는 글롭이 안 걸린다
#   ⚠ **선언은 조각 안 「내 몫이 담겼나」의 사본이다** — 조각이 선언보다 넓은 경로에 깨면 이 판이 그 조각을
#     조용히 뺀다. 선언이 넓은 쪽이어야 하고, 그것을 `scripts/check-gate-gatekeeper.sh` 가 조각을 실제로
#     돌려 잰다(선언 밖의 경로를 다 담아 띄워도 조각이 아무것도 안 하나)
#   안 띄운 조각은 판정 곁 「안 돌렸다」 줄에 이름으로 선다 — 초록은 돈 데까지다
#
# ── 동시 ─────────────────────────────────────────────────────────────────────
#   bash 5.1 이상(`wait -n -p`)이고 띄울 조각이 둘 이상이면 GATES_JOBS 개(기본은 아래 상수)씩 같이 띄운다.
#   출력은 조각마다 받아 두었다가 **선언 순서대로** 표준오류에 낸다 — 같이 돌아도 읽는 글의 차례가 차례 판과
#   같다. GATES_JOBS=1 이거나 다른 셸(dash)이면 차례로 띄우고 출력을 그대로 흘린다.
#   ⚠ [alone] 의 조각은 앞이 다 끝난 뒤 혼자 돌고, 그것이 끝나야 다음이 뜬다 — 같은 자리(고정 임시 파일 ·
#     잠금 · 포트)를 쓰는 조각이다. 러너는 그 자리를 스스로 모른다
#
# ── 시간 ─────────────────────────────────────────────────────────────────────
#   돈 조각마다 걸린 시간과 「모두 N초 · 기다린 것 M초 — 오래 걸린 셋」을 꼬리에 낸다 — 어디서 시간이 드나를
#   재는 자다. 시계는 bash 의 EPOCHREALTIME 이고(프로세스를 안 띄운다), 없으면 `date +%s%N`, 그것도 못
#   읽으면 시간 줄을 안 낸다.

# 같이 띄우는 조각 수의 기본값 — GATES_JOBS 가 덮는다. 조각 대부분이 해석기를 띄우는 일이라 코어 수보다
# 프로세스 띄우는 값이 먼저 찬다.
_GATES_JOBS_DEFAULT=4

# _gates_conf <선언파일> <절 이름들(빈칸으로 가른다)> <꼬리표 0|1> — 그 절들의 줄을 한 줄에 하나씩.
#   '#' 주석 · 빈 줄 · CRLF · BOM 을 걷는다. 꼬리표 1 이면 줄 앞에 「절 이름 + 빈칸」을 붙이고 줄 안의 빈칸을
#   하나로 모으며 `=` 둘레를 ` = ` 로 맞춘다([when] 줄을 셸이 가르게).
#
# ⚠ **절 머리도 이름 줄과 똑같이 다듬고 나서 판정한다.** 머리를 줄 맨 앞의 `[` 로만 물으면 한 칸
#   들여쓰거나 꼬리 주석을 단 절을 통째로 못 알아봐 그 단계의 게이트가 다 꺼진다 — 이 저장소들의
#   문체에서 자연스러운 꼴이다(선언에 주석이 빼곡하고, 파워셸의 `>` 는 BOM 을 붙인다).
_gates_conf() {
    [ -f "$1" ] || return 0
    awk -v secs=" $2 " -v tag="$3" '
        BEGIN { bom = "\357\273\277" }
        {
            if (NR == 1 && index($0, bom) == 1) $0 = substr($0, length(bom) + 1)
            sub(/\r$/, "", $0)
            line = $0
            sub(/[[:space:]]*#.*$/, "", line)
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
        }
        line ~ /^\[[^]]*\]$/ {
            s = line; gsub(/[][]/, "", s)
            insec = (index(secs, " " s " ") > 0); next
        }
        !insec { next }
        line == "" { next }
        tag == 1 {
            gsub(/[[:space:]]+/, " ", line)
            sub(/ ?= ?/, " = ", line)
            print s " " line; next
        }
        { print line }
    ' "$1"
}

# gate_list <절> <선언파일> — 절 안의 이름을 한 줄에 하나씩. 세션 진단도 이것을 부른다(파서를 두 벌 안 둔다).
gate_list() { _gates_conf "$2" "$1" 0; }

# gates_changed <절> <파일> — 이 판에서 바뀐 경로를 한 줄에 하나 <파일> 에 쓴다.
#   0 = 섰다 · 1 = 못 세웠다(까닭은 _gates_why). 뜻은 머리말 「고르기」가 든다.
gates_changed() {
    _gates_why=''
    case "$1" in
        pre-commit)
            git -c core.quotePath=false diff --cached --name-only --no-renames >"$2" 2>/dev/null ||
                { _gates_why='담긴 것을 못 물었다(git diff --cached)'; return 1; } ;;
        pre-push)
            _gc_base=$(git merge-base '@{upstream}' HEAD 2>/dev/null) ||
                { _gates_why='올라갈 가지(upstream)가 없어 고친 경로를 못 가린다'; return 1; }
            git -c core.quotePath=false diff --name-only --no-renames "$_gc_base" >"$2" 2>/dev/null ||
                { _gates_why='고친 경로를 못 뽑았다(git diff)'; return 1; } ;;
        *)
            _gates_why="[$1] 절은 바뀐 경로로 안 고른다"; return 1 ;;
    esac
    while IFS= read -r _gc_p || [ -n "$_gc_p" ]; do
        case "$_gc_p" in
            '"'*) _gates_why="git 이 싸서 낸 이름이 있다($_gc_p)"; return 1 ;;
        esac
    done <"$2"
    return 0
}

# gates_when_of <이름> — 그 조각의 [when] 글롭을 _gw_globs 에 둔다(없으면 빈 값). 읽는 것: _gates_when.
gates_when_of() {
    _gw_globs=''
    while IFS= read -r _gw_l; do
        [ "${_gw_l%% = *}" = "$1" ] || continue
        case "$_gw_l" in *" = "*) _gw_globs=${_gw_l#* = } ;; esac
        break
    done <<EOF
$_gates_when
EOF
}

# gates_wakes <이름> <바뀐 경로 파일> — 그 조각을 띄우나. 0 = 띄운다 · 1 = 안 띄운다(선언이 있고 한 경로도 안 걸렸다).
gates_wakes() {
    gates_when_of "$1"
    case "$_gw_globs" in *[!\ ]*) ;; *) return 0 ;; esac
    # 글롭을 낱말로 가를 때 파일 이름으로 부풀지 않게 — 부른 쪽의 `-f` 상태는 되돌린다.
    case $- in *f*) _gw_f=1 ;; *) _gw_f=''; set -f ;; esac
    _gw_rc=1
    while IFS= read -r _gw_p || [ -n "$_gw_p" ]; do
        for _gw_g in $_gw_globs; do
            # shellcheck disable=SC2254 # 글롭은 무늬로 대려고 인용하지 않는다
            case "$_gw_p" in $_gw_g) _gw_rc=0; break 2 ;; esac
        done
    done <"$2"
    [ -n "$_gw_f" ] || set +f
    return "$_gw_rc"
}

# 걷은 조각 — 옛 씨앗 틀로 만든 저장소의 선언에 아직 남은 이름(#170). 그 선언은 그 저장소 것이라 우리가 안 고치므로, 조각을
#   못 찾아도 「못 쟀다」로 안 세고 말없이 지나간다 — 매 커밋 「당겨 온다」를 내면 고칠 것이 없는 사람에게 소음만 쌓인다.
#   저장소가 제 조각을 들고 있으면 그것은 그대로 돈다. 세션 진단도 이 목록을 묻는다(`gate_retired`) — 목록은 이 한 자리다.
_GATES_RETIRED=' markdown commit-format shell-syntax rule-globs agy-desktop-projects word-pdf-quiet python-version ui-personal-boxes gh-keyring '

# gate_retired <이름> — 걷은 조각이면 0.
gate_retired() { case "$_GATES_RETIRED" in *" $1 "*) return 0 ;; esac; return 1; }

# _gates_now — 지금을 마이크로초로 _gn 에 둔다. 못 재면 빈 값.
_gates_now() {
    _gn=${EPOCHREALTIME:-}
    if [ -n "$_gn" ]; then
        _gn=${_gn%[.,]*}${_gn#*[.,]}
    else
        _gn=$(date +%s%N 2>/dev/null) || _gn=''
        case "$_gn" in ''|*[!0-9]*) _gn='' ;; *) _gn=${_gn%???} ;; esac
    fi
    case "$_gn" in ''|*[!0-9]*) _gn='' ;; esac
}

# _gates_secs <마이크로초> — 「1.6」 꼴을 _gs 에 둔다.
_gates_secs() { _gs="$(($1 / 1000000)).$(($1 % 1000000 / 100000))"; }

# _gates_replay <파일> — 받아 둔 출력을 표준오류로 낸다. 프로세스를 안 띄운다(cat 하나가 이 PC 들에서 수십 ms 다).
_gates_replay() {
    [ -f "$1" ] || return 0
    while IFS= read -r _rl || [ -n "$_rl" ]; do printf '%s\n' "$_rl"; done <"$1" >&2
}

# _gates_msg_gone <이름> · _gates_msg_shadow <이름> — 조각 자리에 대한 러너의 말. 차례 판은 그 자리에서, 동시 판은
#   그 조각의 출력 앞에 낸다.
_gates_msg_gone() {
    printf '· 선언에 [%s] 가 있는데 조각을 못 찾았다(.githooks/gates.d/%s.sh) — 이 PC 의 claude-config 가\n' "$1" "$1"
    printf '  뒤처졌나 본다(당겨 온다). 선언의 오타일 수도 있다. 이 검사는 못 쟀다.\n'
}
_gates_msg_shadow() {
    printf '· [%s] 는 이 저장소의 조각이 설정 저장소 원본을 가리고 돈다 — 옛 사본이면 지운다.\n' "$1"
}

# _gates_judge <이름> <종료코드> — 판정을 모은다.
_gates_judge() {
    case "$2" in
        0) ;;
        2) _cant="$_cant $1" ;;
        *) _fail=1 ;;
    esac
}

# _gates_times — 돈 조각마다의 시간과 꼬리 한 줄을 낸다. 읽는 것: _gn_n · _gnm_<i> · _gtm_<i> · _gw0 · _gjobs_used.
_gates_times() {
    [ "$_ran" -gt 0 ] && [ -n "$_gw0" ] || return 0
    _gates_now
    [ -n "$_gn" ] || return 0
    _gwall=$((_gn - _gw0))
    _gsum=0; _gline=''; _gtop=''; _gpick=' '; _gg=''
    _gi=0
    while [ "$_gi" -lt "$_gn_n" ]; do
        _gi=$((_gi + 1))
        eval "_gt=\${_gtm_$_gi:-} _gg=\$_gnm_$_gi"
        [ -n "$_gt" ] || continue
        _gsum=$((_gsum + _gt)); _gates_secs "$_gt"; _gline="$_gline · $_gg $_gs"
    done
    [ -n "$_gline" ] || return 0
    _gk=0
    while [ "$_gk" -lt 3 ]; do
        _gbest=''; _gbt=-1; _gi=0
        while [ "$_gi" -lt "$_gn_n" ]; do
            _gi=$((_gi + 1))
            eval "_gt=\${_gtm_$_gi:-}"
            [ -n "$_gt" ] || continue
            case "$_gpick" in *" $_gi "*) continue ;; esac
            [ "$_gt" -gt "$_gbt" ] && { _gbt=$_gt; _gbest=$_gi; }
        done
        [ -n "$_gbest" ] || break
        _gpick="$_gpick$_gbest "
        eval "_gg=\$_gnm_$_gbest"; _gates_secs "$_gbt"; _gtop="$_gtop · $_gg ${_gs}초"
        _gk=$((_gk + 1))
    done
    printf '· 조각마다 걸린 시간(초) —%s\n' "${_gline# ·}" >&2
    _gates_secs "$_gsum"; _gss=$_gs
    _gates_secs "$_gwall"
    printf '· 모두 %s초 · 기다린 것 %s초(%s) — 오래 걸린 셋:%s\n' "$_gss" "$_gs" "$_gjobs_used" "${_gtop# ·}" >&2
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

    # ⚠ **조각은 하위 셸에서 돈다** — `export` 없이는 계약의 변수가 안 넘어가고, 조각은 `set -u`
    #   아래서 그 자리에 죽는다. 계약을 지키는 자리는 러너 한 곳이다.
    export PROJECT_DIR
    GATES_STAGE="$_stage"; export GATES_STAGE
    unset GATES_CHANGED

    # 러너 곁 — 몸통이 제 자리에서 굳혀 넘긴다(GATES_DIR). 사본에서 돌면 저장소 `.githooks` 와
    #   같은 자리고, 저장소가 설정 저장소의 원본을 바로 가리킬 때는 원본 곁이다.
    # ⚠ 안 넘어오면 저장소 자리로 물러난다 — 이 값을 모르는 옛 몸통이 새 러너를 부르는 자리다.
    _home="${GATES_DIR:-$PROJECT_DIR/.githooks}"

    _fail=0; _cant=''; _ran=0; _skip=''; _nskip=0; _plan=''; _tmpd=''; _retired=''
    _gates_now; _gw0=$_gn

    # 저장소 조각 폴더와 러너 곁이 같은 자리인가 — 같으면(설정 저장소 자신) 가림을 잴 까닭이 없다.
    # 한 번만 잰다: 조각마다 `cmp` 를 띄우지 않으려는 것이다.
    _same=""
    [ "$(cd "$PROJECT_DIR/.githooks/gates.d" 2>/dev/null && pwd -P)" = "$(cd "$_home/gates.d" 2>/dev/null && pwd -P)" ] && _same=1

    # 선언 한 벌 — 이 단계의 이름 · [when] · [alone] 을 파서 한 번에 읽는다.
    # ⚠ **목록을 인용 없는 확장으로 펴지 않는다.** `for _g in $(…)` 는 낱말 분리와 파일 이름
    #   확장을 같이 받아, 이름에 공백이 들면 두 조각을 찾다 막고 `*` 한 줄은 저장소 뿌리의
    #   파일 이름으로 부푼다 — 오타가 「조각이 없다」로 나와 배포 사고처럼 보인다.
    _list=''; _gates_when=''; _alone=' '
    while IFS= read -r _l; do
        case "$_l" in
            "$_stage "*) _list="$_list${_l#* }
" ;;
            "when "*) _gates_when="$_gates_when${_l#* }
" ;;
            "alone "*) _alone="$_alone${_l#* } " ;;
        esac
    done <<EOF
$(_gates_conf "$_conf" "$_stage when alone" 1)
EOF

    # 바뀐 경로 — 이 단계의 조각 가운데 [when] 을 든 것이 있을 때만 묻는다(없으면 git 을 안 띄운다).
    _sel=''
    case "$_stage" in
        pre-commit|pre-push)
            while IFS= read -r _g; do
                [ -n "$_g" ] || continue
                gates_when_of "$_g"
                [ -z "$_gw_globs" ] || { _sel=1; break; }
            done <<EOF
$_list
EOF
            ;;
    esac
    if [ -n "$_sel" ]; then
        if ! _tmpd=$(mktemp -d 2>/dev/null) || [ -z "$_tmpd" ]; then
            _tmpd=''; _sel=''; _plan='고른 판 — 임시 자리를 못 만들어 경로로 안 가리고 다 띄운다'
        elif gates_changed "$_stage" "$_tmpd/changed"; then
            GATES_CHANGED="$_tmpd/changed"; export GATES_CHANGED
        else
            _sel=''; _plan="고른 판 — $_gates_why · 경로로 안 가리고 다 띄운다"
        fi
    fi

    # 조각마다 자리와 할 일을 정한다 — 못 찾음(gone) · 안 띄움(skip) · 띄움(run).
    _gn_n=0; _nrun=0
    while IFS= read -r _g; do
        [ -n "$_g" ] || continue
        _gn_n=$((_gn_n + 1))
        # 저장소 조각이 먼저다 — 저장소가 제 판을 든 자리는 그 판이 돈다.
        _f="$PROJECT_DIR/.githooks/gates.d/$_g.sh"; _own=1
        [ -f "$_f" ] || { _f="$_home/gates.d/$_g.sh"; _own=''; }
        if [ ! -f "$_f" ] && gate_retired "$_g"; then
            _st=skip; _retired=1
        elif [ ! -f "$_f" ]; then
            _st=gone
        elif [ -n "$_sel" ] && ! gates_wakes "$_g" "$_tmpd/changed"; then
            _st=skip; _skip="$_skip $_g"; _nskip=$((_nskip + 1))
        else
            _st=run; _nrun=$((_nrun + 1))
        fi
        # ⚠ **가리면 말한다.** 저장소 조각이 러너 곁의 같은 이름과 다르면, 일부러 든 판일 수도 있지만
        #   걷히지 않은 옛 사본일 수도 있다 — 옛 사본은 원본을 영영 가리고 아무도 모른다(0064).
        # ⚠ 줄끝(CRLF)만 다른 사본은 같은 것으로 본다 — 윈도우 체크아웃이 흔히 그렇고, 빌린 부품
        #   대조(`borrowed_check.py`)도 줄끝을 안 가린다. 띄울 조각만 잰다.
        _sh=''
        [ "$_st" = run ] && [ -n "$_own" ] && [ -z "$_same" ] && [ -f "$_home/gates.d/$_g.sh" ] &&
            ! diff -q --strip-trailing-cr "$_f" "$_home/gates.d/$_g.sh" >/dev/null 2>&1 && _sh=1
        # 자리마다 값 — 같은 셸에서 다시 불려도 앞 판의 값이 안 남게 시간 · 끝남 · 종료코드도 비운다.
        eval "_gnm_$_gn_n=\$_g _gf_$_gn_n=\$_f _gst_$_gn_n=\$_st _gsh_$_gn_n=\$_sh _gtm_$_gn_n= _gt0_$_gn_n= _gdn_$_gn_n= _grc_$_gn_n="
    done <<EOF
$_list
EOF

    # 같이 띄우나 — 수 · 셸 · 시계 · 띄울 조각이 둘 이상인가.
    _jobs=${GATES_JOBS:-$_GATES_JOBS_DEFAULT}
    case "$_jobs" in ''|*[!0-9]*|0) _jobs=$_GATES_JOBS_DEFAULT ;; esac
    _pool=''
    if [ "$_jobs" -gt 1 ] && [ "$_nrun" -gt 1 ] && [ -n "${EPOCHREALTIME:-}" ]; then
        case "${BASH_VERSION:-}" in 5.[1-9]*|[6-9].*|[1-9][0-9].*) _pool=1 ;; esac
    fi
    if [ -n "$_pool" ] && [ -z "$_tmpd" ]; then
        _tmpd=$(mktemp -d 2>/dev/null) || _tmpd=''
        [ -n "$_tmpd" ] || _pool=''
    fi

    if [ -n "$_pool" ]; then
        _gjobs_used="동시 $_jobs"
        _next=1; _flush=1; _running=0; _solo=''; _pidmap=' '
        while [ "$_flush" -le "$_gn_n" ]; do
            # 띄운다 — 자리가 남고 혼자 도는 조각이 안 돌 때. 안 띄울 자리는 곧장 끝난 것으로 둔다.
            while [ "$_next" -le "$_gn_n" ] && [ "$_running" -lt "$_jobs" ] && [ -z "$_solo" ]; do
                eval "_g=\$_gnm_$_next _f=\$_gf_$_next _st=\$_gst_$_next _sh=\$_gsh_$_next"
                _o="$_tmpd/$_next.out"
                case "$_st" in
                    skip) eval "_gdn_$_next=1 _grc_$_next=skip"; _next=$((_next + 1)); continue ;;
                    gone) _gates_msg_gone "$_g" >"$_o"; eval "_gdn_$_next=1 _grc_$_next=gone"; _next=$((_next + 1)); continue ;;
                esac
                case "$_alone" in
                    *" $_g "*) [ "$_running" -eq 0 ] || break; _solo=1 ;;
                esac
                if [ -n "$_sh" ]; then _gates_msg_shadow "$_g" >"$_o"; else : >"$_o"; fi
                _gates_now; eval "_gt0_$_next=\$_gn"
                # ⚠ **표준입력을 막는다** — 조각이 입력을 읽어도 러너의 것을 못 먹는다.
                sh "$_f" "$@" </dev/null >>"$_o" 2>&1 &
                _pidmap="$_pidmap$!:$_next "
                _running=$((_running + 1)); _next=$((_next + 1))
            done
            # 끝난 앞자리를 선언 순서대로 낸다 — 판정도 이 자리에서 모은다.
            while [ "$_flush" -le "$_gn_n" ]; do
                eval "_d=\${_gdn_$_flush:-} _rc=\${_grc_$_flush:-} _g=\$_gnm_$_flush"
                [ -n "$_d" ] || break
                case "$_rc" in
                    skip) ;;
                    gone) _gates_replay "$_tmpd/$_flush.out"; _cant="$_cant $_g" ;;
                    *) _gates_replay "$_tmpd/$_flush.out"; _ran=$((_ran + 1)); _gates_judge "$_g" "$_rc" ;;
                esac
                _flush=$((_flush + 1))
            done
            [ "$_flush" -le "$_gn_n" ] || break
            [ "$_running" -gt 0 ] || continue
            # 아무 조각이나 끝나기를 기다린다 — 끝난 차례로 자리를 채워 앞의 긴 조각이 뒤를 안 막게.
            _wp=''
            # shellcheck disable=SC3045 # bash 5.1 이상일 때만 이 갈래로 온다(위 `_pool` 판정)
            wait -n -p _wp
            _wrc=$?
            _gates_now
            if [ -n "$_wp" ]; then
                _x=${_pidmap#* "$_wp":}; _x=${_x%% *}
                eval "_t0=\${_gt0_$_x:-} _gg=\$_gnm_$_x _gdn_$_x=1 _grc_$_x=\$_wrc"
                [ -n "$_t0" ] && [ -n "$_gn" ] && eval "_gtm_$_x=\$((_gn - _t0))"
                _running=$((_running - 1))
                case "$_alone" in *" $_gg "*) _solo='' ;; esac
            else
                # ⚠ 기다릴 것이 있는데 아무것도 안 잡혔다 — 셈이 어긋난 자리다. 띄운 것을 하나씩 거둬 끝을
                #   보장한다(멈춘 커밋 훅보다 느린 거둠이 낫다). 시간은 못 잰 것으로 둔다.
                for _pe in $_pidmap; do
                    _x=${_pe#*:}
                    eval "_d=\${_gdn_$_x:-}"
                    [ -z "$_d" ] || continue
                    wait "${_pe%%:*}"
                    eval "_gdn_$_x=1 _grc_$_x=$?"
                done
                _running=0; _solo=''
            fi
        done
    else
        _gjobs_used='차례로'
        _gi=0
        while [ "$_gi" -lt "$_gn_n" ]; do
            _gi=$((_gi + 1))
            eval "_g=\$_gnm_$_gi _f=\$_gf_$_gi _st=\$_gst_$_gi _sh=\$_gsh_$_gi"
            case "$_st" in
                skip) continue ;;
                gone) _gates_msg_gone "$_g" >&2; _cant="$_cant $_g"; continue ;;
            esac
            [ -z "$_sh" ] || _gates_msg_shadow "$_g" >&2
            _ran=$((_ran + 1))
            _gates_now; _t0=$_gn
            # ⚠ **표준입력을 막는다** — 이 판은 목록을 변수에서 돌지만, 조각이 입력을 읽어도 훅이 받은
            #   입력(pre-push 의 참조 목록 따위)을 못 먹게 한다.
            sh "$_f" "$@" </dev/null
            _rc=$?
            _gates_now
            [ -n "$_t0" ] && [ -n "$_gn" ] && eval "_gtm_$_gi=\$((_gn - _t0))"
            _gates_judge "$_g" "$_rc"
        done
    fi

    # 안 띄운 것 · 고르지 못한 까닭 · 못 잰 것을 판정 곁에 찍는다.
    # ⚠ 못 잰 까닭은 조각이 이미 제 줄로 냈다 — 여기는 **목록**만 든다. 러너가 까닭을 짐작해 적으면
    #   도구는 있는데 못 잰 자리에서 그 문장이 거짓이 된다.
    [ -z "$_skip" ] || printf '· 안 돌렸다 %s개 — 바뀐 경로가 지키는 자리([when]) 밖이다:%s\n' "$_nskip" "$_skip" >&2
    [ -z "$_plan" ] || printf '· %s\n' "$_plan" >&2
    [ -z "$_cant" ] || printf '· 못 쟀다:%s — 위 까닭을 본다. 초록은 여기까지다.\n' "$_cant" >&2
    [ "$_ran" -gt 0 ] || [ -n "$_cant" ] || [ -n "$_skip" ] || [ -n "$_retired" ] ||
        printf '· [%s] 절에 켜진 조각이 없다 — 이 단계는 아무것도 안 잰다.\n' "$_stage" >&2
    _gates_times

    [ -z "$_tmpd" ] || rm -rf "$_tmpd"
    [ "$_fail" -eq 0 ] || printf '\n' >&2
    return "$_fail"
}
