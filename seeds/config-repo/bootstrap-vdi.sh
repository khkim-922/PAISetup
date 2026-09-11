#!/bin/bash
# 비영속 VDI 재부팅 후 환경 복구. 여러 번 돌려도 안전하다.
#
#   진입점은 **`install.cmd` 다** — 그것을 더블클릭하면 프로그램을 깔고, 값 파일이
#   `#config-repo` 를 들면 이 저장소까지 받아 여기로 넘긴다. 손으로 부를 일은 없다.
#
#   저장소를 이미 받아 두었다면 직접도 된다:  bash <이 저장소>/bootstrap-vdi.sh
#
#   ⚠ **프로그램은 여기서 안 깐다.** 무엇을 깔지는 `install.ps1` 한 자리가 들고 이 파일은
#     확인만 한다 — 목록을 둘로 두면 한쪽만 낡는데 그 어긋남이 조용하다. 여기가 드는 것은
#     **사람에게 딸린 것**이다: git 신원 · 저장소 · 슬러그 폴더 · 자리 · 키 · 배포.
#
# ⚠ **몸통은 익명이다 — 값은 옆 `bootstrap.conf` 가 든다.** 이름·주소·저장소 목록을 여기
#   박으면 이 파일이 한 사람의 것이 되어, 남에게 줄 때 **다시 쓰게 된다.** 그러면 몸통이
#   둘이 되고 한쪽에서 고친 사고가 저쪽에 안 간다 — 골든 샘플을 손으로 지었다가 실제로
#   그렇게 났다(결정 기록 0004 의 축).
# ⚠ **이 저장소 안의 자리는 선언이 아니라 파생이다** — `$HERE` 가 든다. 제 폴더 이름을
#   값으로 적으면 이름을 바꾼 날 조용히 어긋나고, 포크한 사람은 그 줄부터 고쳐야 한다.
#
# 자격증명은 담지 않는다. clone 때 GitHub 로그인 창이 한 번 뜬다.
set -u

# ⚠ **파이썬이 내는 한글을 여기서 지킨다.** 윈도우 파이썬은 출력이 파이프로 갈 때 콘솔
#   코드페이지(한국은 cp949)로 인코딩하는데, 받는 쪽은 UTF-8 로 읽는다 — **그 한 줄만 깨진다.**
#   실측 2026-09-11(사내 PC): `9개를 맞췄다` 가 `9���� �����` 로 나왔다. 파일은 아래 칸들이
#   `encoding="utf-8"` 로 못박아 뒀는데 **출구만 빠져 있었다.**
# ⚠ **`deploy.ps1` 이 심는 사용자 환경변수에 안 기댄다.** 그것은 **새로 뜨는 프로세스부터**
#   걸리는데 그 심기는 아래 `7/7` 이고 파이썬은 그보다 **앞에서** 돈다 — 처음 세우는 기계에서는
#   영영 안 걸리는 순서다. 여기서 세우면 이 판이 부르는 자식들이 다 물고 뜬다.
# ⚠ **부르는 자리마다 안 적는다.** 한글을 찍는 파이썬이 지금은 하나뿐이지만, 하나 더 느는
#   날 그 자리를 또 밟는다 — 조건은 부르는 쪽이 한 번 세운다.
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

# 이 파일이 사는 자리 = 이 저장소의 뿌리. 아래 칸들이 여기서 형제 파일을 찾는다.
HERE="$(cd "$(dirname "$0")" && pwd)"
CONF="$HERE/bootstrap.conf"
[ -f "$CONF" ] || { echo "! 선언이 없다: $CONF"; exit 1; }

# ── 선언을 읽는다 — **순정 sh 파서다** ────────────────────────────────────────
# ⚠ 관대하지 않다: 이름 오타는 조용히 빈 값이 된다. 마지막 그물은 아래 판정이다.
# ⚠ `eval` 하지 않는다 — 선언은 값이지 코드가 아니고, 남이 준 파일일 수도 있다.
_conf() {
    sed -n "s/^[[:space:]]*$1=//p" "$CONF" | head -1 | tr -d '\r' |
        sed 's/[[:space:]]*$//'
}

GIT_NAME="$(_conf GIT_NAME)"
GIT_EMAIL="$(_conf GIT_EMAIL)"
REPOS="$(_conf REPOS)"
REPO_URL="$(_conf REPO_URL)"
PROBE="$(_conf PROBE)"
# `$HOME` 을 값에 쓸 수 있게 한 자리만 펴 준다 — 통째로 eval 하지 않는 대신이다.
ROOT="$(_conf ROOT)"; ROOT="$(printf '%s' "$ROOT" | sed "s|\$HOME|$HOME|g;s|^~|$HOME|")"
[ -n "$ROOT" ] || ROOT="$HOME/repos"

# 못 세운 것을 모은다 — 끝에서 **종료코드로** 낸다.
FAILS=""

echo "== 1/7  git 전역 설정 =="
# ⚠ **빈 값을 심지 않는다.** 선언에서 이름을 빼먹었는데 그대로 심으면 `user.name` 이 빈
#   문자열로 굳고, 커밋이 「누가 했는지 없는」 채로 선다 — git 은 그걸 막지 않는다.
if [ -n "$GIT_NAME" ] && [ -n "$GIT_EMAIL" ]; then
    git config --global user.name  "$GIT_NAME"
    git config --global user.email "$GIT_EMAIL"
    echo "  $GIT_NAME <$GIT_EMAIL>"
else
    echo "  ! 선언에 GIT_NAME · GIT_EMAIL 이 없다 — 안 심었다"
    FAILS="$FAILS git신원"
fi
# 윈도우에서 물리는 것들. 바꿀 일이 있으면 이 줄들을 고친다.
git config --global init.defaultBranch main
git config --global core.autocrlf true      # 체크아웃은 CRLF, 저장소는 LF
git config --global core.longpaths true     # 260자 벽 — 깊은 나무에서 clone 이 진다
git config --global credential.helper manager
git config --global pull.rebase false

echo "== 2/7  저장소 =="
if [ -z "$REPOS" ]; then
    echo "  선언에 REPOS 가 없다 — 건너뜀"
elif [ -z "$REPO_URL" ]; then
    echo "  ! REPOS 는 있는데 REPO_URL 이 없다 — 어디서 받을지 모른다"
    FAILS="$FAILS 저장소"
else
    mkdir -p "$ROOT"
    for r in $REPOS; do
        _url="$(printf '%s' "$REPO_URL" | sed "s|<이름>|$r|g")"
        if [ -d "$ROOT/$r/.git" ]; then
            echo "  $r — 있음, pull"
            git -C "$ROOT/$r" pull --ff-only || {
                echo "  ! $r pull 실패 (손으로 확인한다)"; FAILS="$FAILS $r"; }
        else
            echo "  $r — clone"
            git clone "$_url" "$ROOT/$r" || {
                echo "  ! $r clone 실패"; FAILS="$FAILS $r"; }
        fi
    done
fi

echo "== 3/7  런타임 확인 =="
# ⚠ **여기서 깔지 않는다.** 무엇을 깔지는 `install.ps1` 한 자리가 들고, 이 스크립트는 그것이
#   이미 돌았다는 전제 위에 선다. 목록을 여기에도 두면 winget id 가 두 파일에 살고 그
#   어긋남은 **조용하다** — 낡은 쪽이 먼저 깔면 판이 갈리는데 게이트는 초록으로 끝난다.
#
# ⚠ **배선은 여전히 여기가 든다.** 이 셸은 install.ps1 이 깐 **뒤에** 떠도 그 PATH 를 못
#   물려받는다 — 창은 뜰 때 환경을 한 번 복사하고, 이 창을 띄운 부모가 winget 보다 먼저 떴다.
#   배선 없이 물으면 이미 깔린 것도 「없음」이 나와 판정이 통째로 뒤집힌다 (실측).
#   cygpath 로 POSIX 꼴을 만든다 — 윈도우 꼴(역슬래시)을 그대로 두면 `[ -d ]` 가 못 읽는다.
# ⚠ **파이썬 판의 진본은 도구 선언(`.claude/tools.conf` 의 `[python]`)** 이다 (지금 3.14).
#   거기가 오르면 아래 `Python314` 와 `install.ps1` 의 winget id 를 같이 올린다 — 판이
#   어긋나면 게이트가 초록인 채로 엉뚱한 판을 재는 자리가 난다 (그 저장소 `[python]` 주석).
_pf="$(cygpath -u "${PROGRAMFILES:-}" 2>/dev/null)"
_la="$(cygpath -u "${LOCALAPPDATA:-}" 2>/dev/null)"
_add_path() {
    [ -d "$1" ] || return 0
    case ":$PATH:" in *":$1:"*) return 0 ;; esac   # 여러 번 불러도 PATH 가 안 분다
    PATH="$1:$PATH"
}
_wire_runtime_path() {
    _add_path "$_pf/nodejs"
    _add_path "$_pf/GitHub CLI"
    _add_path "$_la/Programs/Python/Python314"
    _add_path "$_la/Programs/Python/Python314/Scripts"
    _add_path "$_la/Programs/Python/Launcher"
    # ⚠ `$APPDATA` 는 **윈도우 꼴**(`C:\Users\...\Roaming`)이라 `/npm` 을 그냥 붙이면 잡종
    #   경로가 된다. 그러면 npm shim 이 제 자리를 Git 설치 폴더 기준으로 잘못 풀어
    #   `claude.exe: No such file or directory` 로 죽는다 (실측 2026-08-31). deploy 는
    #   powershell 자식이라 윈도우가 알아서 풀어 줘 지금까지 안 드러났다 —
    #   **bash 에서 부를 때만 깨진다.**
    _add_path "$(cygpath -u "${APPDATA:-}" 2>/dev/null)/npm"
    export PATH
}
_wire_runtime_path

# ⚠ **존재로 묻지 않는다.** 윈도우는 `WindowsApps/python` 에 스토어로 보내는 **껍데기**를
#   깔아 두고, `command -v python` 이 그것을 잡아 「있음」을 낸다 — 부르면 「Python was not
#   found」 를 뱉고 49 로 죽는 파일이다. 그 오판으로 넘어가면 뒤의 deploy 가 파이썬 검사
#   넷을 꺼진 채로 두고 **초록으로 끝난다** (실측 2026-09-02 · VDI 첫 부트스트랩).
#   「깔린 것과 닿는 것은 다른 명제」 — 그러니 있나 묻지 말고 **불러 본다.**
_probe_cmd() { command -v "$1" >/dev/null 2>&1 && "$1" --version >/dev/null 2>&1; }

# ⚠ **안 닿아도 여기서 멈추지 않는다.** 아래 칸들(저장소·자리·키)은 런타임 없이도 제 일을
#   하고, 멈추면 그것까지 잃는다. 대신 **끝까지 데려간다** — 마지막 안내가 이 목록을 다시 편다.
# ⚠ **쉼표로 가른다.** 사람이 읽는 이름에 빈칸이 들어(`GitHub CLI`) 빈칸으로 가르면 한
#   항목이 둘로 쪼개지고, **있는 도구가 「안 닿는다」로 찍힌다.** `IFS` 는 이 고리 안에서만
#   바꾸고 되돌린다.
MISSING=""
_ifs_was="$IFS"; IFS=','
for _spec in $PROBE; do
    IFS="$_ifs_was"
    _spec="$(printf '%s' "$_spec" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [ -n "$_spec" ] || { IFS=','; continue; }
    _cmd="${_spec%%:*}"; _name="${_spec#*:}"
    if _probe_cmd "$_cmd"; then
        echo "  $_name — 있음"
    else
        echo "  ! $_name — 안 닿는다"
        MISSING="$MISSING $_name"
    fi
    IFS=','
done
IFS="$_ifs_was"
[ -n "$MISSING" ] && echo "  ⚠ install.cmd 를 먼저 돌린다 — 그것이 깐다:$MISSING"

echo "== 4/7  프로젝트 슬러그 폴더 =="
# deploy.ps1 은 슬러그 폴더가 이미 있을 때만 메모리를 배포한다(Test-Path 검사).
# 세션을 아직 안 연 폴더는 슬러그가 없으므로 여기서 미리 만든다.
# 슬러그는 경로에서 파생된다 — 영숫자가 아닌 문자가 전부 `-` 다. 그러니 목록을 따로
# 들지 않고 REPOS 에서 만든다. 손으로 든 목록은 저장소가 늘 때 조용히 어긋난다.
# ⚠ **접두사도 파생이다.** 옛 판은 저장소 이름만 파생하고 `C--Users-<남의-이름>-repos-` 를 손으로
#   박아, 사용자 이름이 다른 PC 에서 **남의 슬러그 폴더**를 만들었다. 그러면 deploy 는
#   「폴더가 있으면 배포한다」로 판정하므로 거기까지 메모리를 채운다 — 오류 한 줄 없이
#   그 PC 에 쓰지도 않을 사본이 한 벌 더 선다 (실측 2026-09-09 · 사내 PC).
# ⚠ 윈도우 꼴로 만들어야 한다 — 슬러그의 원본은 `C:\Users\...` 이지 `/c/Users/...` 가 아니다.
# ⚠ **글자로 세지 바이트로 세지 않는다.** 로케일을 안 주면 sed 가 바이트를 세어 한글 한 자가
#   대시 셋이 된다 — 사용자 이름이 한글인 PC 에서 슬러그가 통째로 어긋나는데, 폴더는
#   멀쩡히 만들어지므로 **메모리가 조용히 안 깔린다.** 집 PC 의 `바탕 화면` 으로 재보면
#   대시 7 개여야 할 자리에 15 개가 나온다 (실측 2026-09-10).
_slug_of() { cygpath -w "$1" | LC_ALL=C.UTF-8 sed 's/[^A-Za-z0-9]/-/g'; }
for r in $REPOS; do
    mkdir -p "$HOME/.claude/projects/$(_slug_of "$ROOT/$r")"
done
mkdir -p "$HOME/.claude/projects/$(_slug_of "$ROOT")"   # 전역 층 — 저장소들을 담은 폴더
echo "  $(($(echo $REPOS | wc -w) + 1))개 준비"

echo "== 5/7  자리 · 홈 개인 설정 =="
# 자리를 **여기서** 가른다. 홈 설정을 덮을지가 자리에 달렸고(아래), 키를 심는 6/7 도 같은
# 값을 쓴다 — 한 번만 재고 둘이 나눠 쓴다.

SECRETS_DIR="$HERE/secrets.d"

# 줄끝 공백·CR 을 턴다 — CRLF 로 받으면 값 끝의 CR 이 그대로 심겨 아무 데서도 안 먹히는
# 키가 된다. `.gitattributes` 가 LF 로 묶지만 여기서도 한 번 더 막는다.
_trim() {
    _t="$1"
    while :; do
        case "$_t" in *[[:space:]]) _t="${_t%?}" ;; *) break ;; esac
    done
    printf '%s' "$_t"
}

# 파일이 든 이름들. **몸통은 이름을 모른다** — 파일에 묻는다 (0004 의 축).
_names_of() {
    [ -f "$1" ] || return 0
    grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' "$1" 2>/dev/null | tr -d '='
}
_has_name() { _names_of "$1" | grep -qx "$2"; }

# ── 자리 — **이름이 아니라 닿음으로 가른다** (ADR 0159 와 같은 축).
#    DNS 는 사외에서도 사내 IP 를 풀어 주므로 이름으로는 안 갈린다 —
#    실측 2026-08-31: 사외에서도 사내 이름이 사내 IP 로 풀렸고 포트는 안 열렸다.
#    프로브 대상은 **파일이 든다**(`#site-probe = 호스트:포트`). 몸통은 자리 이름도
#    게이트웨이 주소도 모른다. 아무것도 안 닿으면 `#site-default = yes` 인 파일이 선다.
SITE=""; SITE_FILE=""; DEFAULT_FILE=""
for _f in "$SECRETS_DIR"/*.env; do
    [ -e "$_f" ] || continue
    case "$(sed -n 's/^#[[:space:]]*site-default[[:space:]]*=[[:space:]]*//p' "$_f" | head -1)" in
        *yes*) DEFAULT_FILE="$_f" ;;
    esac
    [ -n "$SITE_FILE" ] && continue
    _probe="$(_trim "$(sed -n 's/^#[[:space:]]*site-probe[[:space:]]*=[[:space:]]*//p' "$_f" | head -1)")"
    [ -n "$_probe" ] || continue
    _h="${_probe%%:*}"; _p="${_probe#*:}"
    if timeout 3 bash -c "(exec 3<>/dev/tcp/$_h/$_p)" 2>/dev/null; then
        SITE_FILE="$_f"; SITE="$(basename "$_f" .env)"
        echo "  자리 = $SITE   ($_probe 닿음)"
    else
        echo "  ($_probe 안 닿음)"
    fi
done
# ── 둘째 자 — **경로가 있나** (`#site-path`) ─────────────────────────────────────
# ⚠ **닿음으로는 못 가르는 자리가 있다.** 집과 사외 VDI 는 둘 다 사내에 안 닿아, 프로브만으로는
#   한 자리로 뭉친다. 그런데 성질이 다르다: 사외 VDI 는 프로필이 매 로그인 날아가고(그래서
#   홈 설정을 덮는다) 집은 안 날아간다 — 뭉친 채로 두면 **집에서 사람이 손댄 설정이 덮인다.**
# ⚠ **이것은 「이름으로 가르지 않는다」(결정 0026)를 어기는 것이 아니다.** 저쪽이 금한 것은
#   *네트워크 자리*를 DNS 이름으로 재는 일이고, 여기서 재는 것은 *어느 기계인가*다 — 다른
#   물음이라 다른 자를 든다. `deploy.targets.d/*.conf` 가 이미 같은 축(경로가 있나)을 쓴다.
# ⚠ **닿음보다 뒤에 선다.** 사내에서도 그 경로가 있을 수 있는데, 사내인 것이 더 확실하다.
if [ -z "$SITE_FILE" ]; then
    for _f in "$SECRETS_DIR"/*.env; do
        [ -e "$_f" ] || continue
        _path="$(_trim "$(sed -n 's/^#[[:space:]]*site-path[[:space:]]*=[[:space:]]*//p' "$_f" | head -1)")"
        [ -n "$_path" ] || continue
        if [ -d "$_path" ]; then
            SITE_FILE="$_f"; SITE="$(basename "$_f" .env)"
            echo "  자리 = $SITE   ($_path 있음)"
            break
        fi
    done
fi

if [ -z "$SITE_FILE" ] && [ -n "$DEFAULT_FILE" ]; then
    SITE_FILE="$DEFAULT_FILE"; SITE="$(basename "$DEFAULT_FILE" .env)"
    echo "  자리 = $SITE   (닿지도 않고 아는 경로도 없어 기본값)"
fi

# ── 데스크탑 앱 — **자리 파일이 정한다** (`#desktop-app = yes`) ──────────────────
# ⚠ **왜 여기 서나 — 순서 때문이다.** 무엇을 깔지는 install.ps1 이 드는데 이것만은 **자리를
#   안 뒤에야** 갈리고, 자리 판별은 `secrets.d/` 를 읽으므로 clone 뒤에나 설 수 있다.
# ⚠ **사내에는 쓸모가 없다.** 게이트웨이를 물리는 `ANTHROPIC_BASE_URL` 을 읽는 것은 Claude
#   Code CLI 뿐이고 데스크탑 앱에는 그 스위치가 없다 — 깔려도 앤트로픽 본사로 나가려 하고
#   그 길이 막혀 있다. 그래서 기본이 「안 깐다」이고, 자리 파일이 `#desktop-app = yes` 를
#   들 때만 깐다. **몸통은 어느 자리가 그것을 드는지 모른다** (`#site-probe` 와 같은 축).
#   ⚠ 아직 **사내에서 재 본 적이 없다.** 되는 것으로 밝혀지면 자리 파일에 한 줄 더하면
#   되고 이 몸통은 안 고친다 — 선언으로 둔 까닭이 그것이다.
_want_app=""
[ -n "$SITE_FILE" ] &&
    _want_app="$(_trim "$(sed -n 's/^#[[:space:]]*desktop-app[[:space:]]*=[[:space:]]*//p' "$SITE_FILE" | head -1)")"
if [ "$_want_app" = yes ]; then
    # ⚠ **GUI 앱이라 PATH 로 못 잰다.** `--version` 을 부를 이름이 안 생겨 다른 것들이 쓰는
    #   프로브가 여기서는 안 선다 — winget 의 목록에 물어야 하고, 그것이 이 갈래만 판정이
    #   다른 까닭이다. 「깔린 것과 닿는 것은 다르다」의 예외가 아니라, **닿을 이름이 없는 것**이다.
    _app_there() { winget list --id Anthropic.Claude --source winget >/dev/null 2>&1; }
    if _app_there; then
        echo "  데스크탑 앱 — 있음"
    else
        echo "  데스크탑 앱 — 설치"
        winget install --id Anthropic.Claude --source winget --exact --silent \
            --accept-package-agreements --accept-source-agreements --disable-interactivity \
            >/dev/null 2>&1
        if _app_there; then
            echo "  데스크탑 앱 — 깔았다"
        else
            echo "  ! 데스크탑 앱 설치 실패 — 사내라면 정책이 막았을 수 있다"
        fi
    fi
fi

# 프로필이 매 로그인 날아가 홈 settings.json 도 매번 없다. deploy.ps1 은 PC마다 다르다는
# 이유로 이 파일을 일부러 안 건드리니, 비영속 PC 에서는 여기가 그 자리다.
# ⚠ **덮을지는 자리 파일이 정한다** (`#home-settings = overwrite`). 「사외면 덮는다」를
#   몸통에 박지 않는다 — 박으면 자리가 늘 때마다 이 파일을 고쳐야 하고, 포크한 사람의
#   자리는 이름이 달라 안 걸린다. `#site-probe`·`#site-default` 와 같은 축이다:
#   **몸통은 자리 이름을 모른다.**
# ⚠ 안 덮는 자리에서는 있으면 안 건드린다 — 세션 중에 앱에서 바꾼 값을 재실행이 지우면 안 된다.
# ⚠ 덮는 자리에서도 **먼저 옆에 치워 둔다.** 앱이 세션마다 새로 만드는 껍데기와 사람이
#   손댄 설정은 겉이 같아, 지우고 나면 무엇을 지웠는지 물을 자리가 없다.
mkdir -p "$HOME/.claude"
_home_src="$HERE/vdi-home-settings.json"
_home_dst="$HOME/.claude/settings.json"
_home_mode=""
if [ -n "$SITE_FILE" ]; then
    _home_mode="$(_trim "$(sed -n 's/^#[[:space:]]*home-settings[[:space:]]*=[[:space:]]*//p' "$SITE_FILE" | head -1)")"
fi
if [ ! -f "$_home_dst" ]; then
    if cp "$_home_src" "$_home_dst"; then echo "  깔았음"; else echo "  ! 깔기 실패 — vdi-home-settings.json 확인"; fi
elif [ "$_home_mode" != "overwrite" ]; then
    if [ -n "$SITE" ]; then
        echo "  있음 — 안 건드림 ($SITE 가 overwrite 를 안 든다)"
    else
        echo "  있음 — 안 건드림 (자리를 못 정했다)"
    fi
else
    # ⚠ **`hooks` 는 씨앗의 것이 아니라 기계가 심은 것이라 넘겨 준다** (0028 · 0030).
    #   심는 명령이 작업 루트 경로를 들어 PC 마다 달라서 익명 씨앗에 못 담긴다. 그런데
    #   이 덮기는 7/7(deploy → --install)보다 **앞선다** — 그냥 덮으면 훅이 지워진 채로
    #   뒤 단계의 재심기에 기대게 되고, 그 재심기가 실패하면 홈 훅이 조용히 사라진다.
    #   실측 2026-09-02: 그 자리를 밟았다(deploy 의 자식 셸이 파이썬을 못 봐 심기가 걷혔고,
    #   덮기는 이미 지운 뒤였다). 그러니 기대지 않고 **여기서 지킨다.**
    # ⚠ 지킬 수 없으면 **안 덮는다.** 파이썬이 없어 병합을 못 하는데 덮으면, 이 칸이
    #   고치려는 바로 그 고장을 이 칸이 만든다.
    # ⚠ **견줄 상대는 씨앗이 아니라 병합 결과다.** 씨앗과 견주면 심긴 훅 때문에 영영
    #   안 맞아 **매 로그인 덮고 백업이 쌓인다.** 먼저 만들고, 같으면 안 건드린다.
    _pym=""
    for _c in python python3; do
        command -v "$_c" >/dev/null 2>&1 && "$_c" -c '' >/dev/null 2>&1 && { _pym="$_c"; break; }
    done
    if [ -z "$_pym" ]; then
        echo "  ! 안 덮는다 — 파이썬을 못 불러 심긴 훅을 지킬 수 없다 (3/7 을 먼저 본다)"
    else
        _new="$_home_dst.new.$$"
        if "$_pym" - "$_home_src" "$_new" "$_home_dst" <<'PYMERGE'
import json, sys
src, out, cur = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src, encoding="utf-8") as f:
    cfg = json.load(f)
try:
    with open(cur, encoding="utf-8") as f:
        old = json.load(f)
except (OSError, ValueError):
    old = {}
if "hooks" in old:                      # 기계가 심은 것 — 씨앗은 이 키에 의견이 없다
    cfg["hooks"] = old["hooks"]
with open(out, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
    f.write("\n")
PYMERGE
        then
            if cmp -s "$_new" "$_home_dst"; then
                rm -f "$_new"
                echo "  이미 같다 — 안 건드림"
            else
                _bak="$_home_dst.bak-$(date +%Y%m%d-%H%M%S)"
                if cp "$_home_dst" "$_bak" && mv "$_new" "$_home_dst"; then
                    echo "  덮었음 ($SITE 가 overwrite 를 든다) — 옛 것은 $(basename "$_bak")"
                else
                    rm -f "$_new"
                    echo "  ! 덮기 실패 — 쓰기 권한 확인"
                fi
            fi
        else
            rm -f "$_new"
            echo "  ! 덮기 실패 — vdi-home-settings.json 확인"
        fi
    fi
fi

echo "== 6/7  키 =="
# 심은 이름·값을 모을 자리. 끝에서 홈 설정으로 밀 때 쓴다.
PLANTED="$(mktemp)"
trap 'rm -f "$PLANTED"' EXIT
# ⚠ **평문이다.** `secrets.env`(공통)와 `secrets.d/<자리>.env`(자리마다)가 커밋된 채로
#   키를 든다 — 저장소가 private 인 것이 유일한 울타리다 (`docs/decisions/0025`).
# ⚠ **이 셸에도 심는다.** setx 는 새로 뜨는 프로세스부터 걸려서, 안 심으면 바로 아래
#   deploy 가 방금 넣은 키를 「없다」로 보고 남은 수동 작업에 도로 띄운다.
# ⚠ **빈 값은 안 심는다.** 심으면 deploy 판정이 「있다」로 뒤집혀 부재가 조용해진다.
# ⚠ **자리가 갈리면 저쪽 이름을 지운다.** 사외 VDI 에 사내 두 줄이 남으면 설정은 맞아
#   보이는데 닿지를 않는다 — 그 고장은 **조용해서** 지우는 것이 심는 것만큼 중요하다
#   (실측 2026-08-31 · `docs/decisions/0026`).


_plant_file() {
    [ -f "$1" ] || return 0
    while IFS= read -r _line || [ -n "$_line" ]; do
        _line="$(_trim "$_line")"
        case "$_line" in ''|'#'*) continue ;; esac
        case "$_line" in *=*) ;; *) continue ;; esac
        _k="${_line%%=*}"; _v="${_line#*=}"
        if [ -z "$_v" ]; then
            echo "  $_k — 비었다 ($(basename "$1") 에 값을 넣고 커밋할 것)"
            continue
        fi
        if setx "$_k" "$_v" >/dev/null 2>&1; then
            export "$_k=$_v"
            # 심은 것을 모아 둔다 — 자리가 그러라고 하면 홈 설정에도 같은 값을 민다(아래).
            # 값을 두 번 읽지 않고 **한 번 심은 것을 두 자리로 민다** — 파생과 사본을 가르는 자리다.
            printf '%s=%s\n' "$_k" "$_v" >> "$PLANTED"
            echo "  $_k — 심었다"
        else
            echo "  ! $_k 심기 실패 (값이 1024자를 넘나 본다)"
        fi
    done < "$1"
}

# ⚠ `setx "$1" ""` 은 **지우는 것이 아니다** — 빈 글자를 남긴다. 지우는 자는 reg 다.
# ⚠ `MSYS_NO_PATHCONV=1` 이 있어야 한다 — 없으면 Git Bash 가 `/V`·`/F` 를 경로로 바꿔
#   reg 가 「잘못된 구문」으로 죽는다. 죽어도 조용해서 안 재면 모른다 (실측 2026-08-31).
# ⚠ **있었을 때만 말한다.** 없던 것을 「지웠다」고 하면 보고가 사실보다 커지고,
#   자리 파일에 이름이 늘수록 그 거짓이 화면을 덮는다. 물어보고 지운다.
_forget() {
    if MSYS_NO_PATHCONV=1 reg query "HKCU\Environment" /V "$1" >/dev/null 2>&1; then
        MSYS_NO_PATHCONV=1 reg delete "HKCU\Environment" /V "$1" /F >/dev/null 2>&1
        echo "  $1 — 지웠다 (이 자리 것이 아니다)"
    fi
    unset "$1" 2>/dev/null || true
}

_plant_file "$HERE/secrets.env"


if [ -n "$SITE_FILE" ]; then
    _plant_file "$SITE_FILE"
    for _f in "$SECRETS_DIR"/*.env; do
        [ -e "$_f" ] || continue
        [ "$_f" = "$SITE_FILE" ] && continue
        for _n in $(_names_of "$_f"); do
            _has_name "$SITE_FILE" "$_n" && continue
            _forget "$_n"
        done
    done
else
    echo "  ! 자리를 못 정했다 — secrets.d 에 #site-probe 도 #site-default 도 없다"
fi

# ── 자리가 들면 홈 `settings.json` 의 `env` 에도 같은 값을 민다 ──────────────────
# ⚠ **왜 두 자리인가.** 사내에서는 둘 다 봐야 한다 — 환경변수만 두면 모델 고르는 자리가
#   엉뚱한 값으로 서고, 파일만 두면 같은 변수를 읽는 다른 앱이 키를 잃는다.
# ⚠ **사본이 아니라 파생이다.** 값의 진본은 자리 파일 하나고, 방금 심은 것을 그대로 민다.
# ⚠ **어느 자리가 이것을 드나를 몸통이 모른다** — 자리 파일의 `#settings-env` 가 든다.
#   사외는 안 든다: 거기는 게이트웨이를 안 타 심을 이름 자체가 없다.
# ⚠ **덮기(5/7)보다 뒤에 선다.** 앞에 두면 그 덮기가 방금 민 값을 지운다.
_want_senv=""
[ -n "$SITE_FILE" ] &&
    _want_senv="$(_trim "$(sed -n 's/^#[[:space:]]*settings-env[[:space:]]*=[[:space:]]*//p' "$SITE_FILE" | head -1)")"
if [ "$_want_senv" = yes ] && [ -s "$PLANTED" ]; then
    echo
    echo "  홈 settings.json 의 env 에도 민다 (#settings-env = yes)"
    _pym2=""
    for _c in python python3; do
        command -v "$_c" >/dev/null 2>&1 && "$_c" -c '' >/dev/null 2>&1 && { _pym2="$_c"; break; }
    done
    if [ -z "$_pym2" ]; then
        echo "  ! 파이썬을 못 불러 못 민다 — 3/7 을 먼저 본다"
    elif "$_pym2" - "$HOME/.claude/settings.json" "$PLANTED" <<'PYENV'
import json, sys, io, os
cfg_path, planted_path = sys.argv[1], sys.argv[2]
try:
    with io.open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
except (OSError, ValueError):
    cfg = {}
env = cfg.setdefault("env", {})
n = 0
with io.open(planted_path, encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        if env.get(k) != v:
            env[k] = v
            n += 1
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
with io.open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("  %d개를 맞췄다" % n)
PYENV
    then :; else echo "  ! 밀기 실패 — settings.json 꼴을 본다"; fi
fi

echo "== 7/7  deploy =="
# ⚠ **종료코드를 재다.** 안 재면 deploy 가 죽어도 아래 「완료」가 찍히고 이 스크립트가
#   0 으로 끝난다 — 저장소 배포도 홈 규범도 부트스트랩(--install)도 안 선 기계가
#   성공으로 보인다 (실측 2026-09-07 · deploy 가 첫 MCP 조회에서 죽은 자리).
#   부재가 통과로 읽히는 것을 막는 것이 이 스크립트의 규율인데, 마지막 걸음만 그것이 없었다.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$HERE/deploy.ps1")" -Yes
DEPLOY_RC=$?
[ "$DEPLOY_RC" -eq 0 ] || echo "  ! deploy 가 오류로 끝났다 (exit $DEPLOY_RC) — 위를 보고 고친 뒤 다시 돌린다"


echo
if [ "$DEPLOY_RC" -eq 0 ]; then
    echo "완료. 남은 것은 새 창에서 한다."
else
    echo "끝내지 못했다 — 7/7 deploy 가 exit $DEPLOY_RC 로 죽었다. 아래는 그래도 남는 일이다."
fi
# ⚠ 「재시작할 것」만으로는 모자랐다. 이미 열려 있던 PowerShell 창에서 `claude auth login`
#   을 불렀다가 「'claude' 용어가 ... 인식되지 않습니다」로 죽었다 (실측 2026-09-03).
#   창은 뜰 때 PATH 와 환경변수를 **한 번 복사**하고, 그 뒤에 바뀐 것은 따라오지 않는다.
#   setx 로 심은 키가 안 걸리는 것과 **같은 까닭 하나**다 — 그런데 옛 문구는 키 쪽만
#   말하고 PATH 쪽을 안 말해서, 낡은 창에서 claude 를 부르는 자리가 안 막혔다.
# ⚠ 로그인은 **재고 말한다.** 「하라」고만 적으면 이미 선 PC 에서도 매번 뜨고, 그러면
#   읽는 사람이 이 칸을 통째로 넘기기 시작한다 — 진짜로 필요한 날에도.
# ⚠ **토큰을 저장소에 두지 않는다.** 장기 토큰(`claude setup-token`)이면 손이 아예 안
#   가지만, 그것은 갱신 토큰을 낀 OAuth 라 **돌고**(만료·회전) 커밋해 두면 낡은 뒤에도
#   「설정된 것처럼 보인다」 — 부재보다 나쁘다. 게다가 그 값은 구독 계정 그 자체다.
#   그래서 값을 안 두고 **사람이 브라우저에서 누르게 한다.** 까닭의 진본은 자리 파일이 든다.
_logged=""
if command -v claude >/dev/null 2>&1; then
    _logged="$(claude auth status 2>/dev/null |
        sed -n 's/.*"loggedIn"[[:space:]]*:[[:space:]]*\([a-z]*\).*/\1/p' | head -1)"
fi

# 안 서 있으면 여기서 세운다. 프로필이 매번 날아가는 PC 라 매 부팅의 일이다.
# ⚠ 데스크탑 앱을 쓰는 PC 는 이 칸이 대개 안 걸린다 — 앱 로그인이 CLI 까지 세운다
#   (둘이 `~/.claude` 를 같이 쓴다. 실측 2026-09-03). 그래서 「안 서 있을 때만」이다.
# ⚠ **로그인을 끝내는 것은 stdin 이 아니라 브라우저 콜백이다.** 옛 판은 `[ -t 0 ]` 로
#   갈라, 물어볼 자리가 없으면 통째로 건너뛰고 사람에게 미뤘다 — 그런데 미뤄 봐야 그
#   사람도 **새 창을 열어 같은 명령을 칠 뿐**이고, 낡은 창에서 치면 PATH 가 잘려 또 진다
#   (실측 2026-09-08: 그 자리를 밟아 세 창을 헛 열었다). 띄우는 것 자체는 tty 가 없어도
#   된다 — 배경으로 띄운 것이 콜백을 받아 「Login successful」을 찍었다(실측 2026-09-07 ·
#   AI-prompt-helper 핸드오버). **창을 더 띄우지 않는다.**
# ⚠ 띄우고 **재고 나서 말한다.** 안 재고 「떴다」로 끝내면 사람이 안 누른 기계도 성공으로
#   보고된다 — 부재가 통과로 읽히는 것을 막는 것이 이 스크립트의 규율이다. 다만 무한정
#   기다리지 않는다: 안 누르는 것도 정당한 선택이라 시간을 끊고 아래 안내로 내린다.
_login_wait=180
if [ "$_logged" != "true" ] && command -v claude >/dev/null 2>&1; then
    echo
    echo "== 로그인 =="
    echo "  구독 계정으로 **브라우저가 뜹니다** — 눌러 주세요. (최대 ${_login_wait}초 기다린다)"
    if [ -t 0 ]; then
        claude auth login
    else
        claude auth login >/dev/null 2>&1 &
        _login_pid=$!
        _waited=0
        while [ "$_waited" -lt "$_login_wait" ]; do
            kill -0 "$_login_pid" 2>/dev/null || break
            sleep 5; _waited=$((_waited + 5))
        done
        kill -0 "$_login_pid" 2>/dev/null &&
            echo "  (${_login_wait}초 안에 안 눌렸다 — 브라우저는 그대로 열려 있다. 눌러도 되고, 아래 2 로 다시 해도 된다)"
    fi
    _logged="$(claude auth status 2>/dev/null |
        sed -n 's/.*"loggedIn"[[:space:]]*:[[:space:]]*\([a-z]*\).*/\1/p' | head -1)"
    [ "$_logged" = true ] && echo "  섰다."
fi
echo
echo "  1. 새 터미널을 연다 — 지금 이 창도, 열려 있던 다른 창도 못 쓴다."
if [ "$_logged" = "true" ]; then
    echo "  2. claude 로그인 — 서 있다 (claude auth status: loggedIn=true). 건너뛴다."
else
    echo "  2. claude 로그인이 안 서 있다:"
    echo "         claude auth login       (구독 로그인이 기본이다. 브라우저가 뜬다)"
    echo "       데스크탑 앱을 쓰면 앱 로그인만으로도 선다 — 둘이 자격증명을 같이 쓴다."
    echo "     확인:  claude auth status   (loggedIn 이 true 로 바뀐다)"
fi
echo "  3. 저장소는 그 새 창에서 연다. 낡은 창에서 띄운 세션은 PATH 가 잘린 채라"
echo "     게이트가 꺼진 채로 돈다 — 초록이 아니라 「안 닿는다」가 계속 뜬다."
# ⚠ 여기에 키 이름을 박지 않는다. 무엇이 비었나는 `6/7` 칸이 이름을 대며 이미 말했고
#   deploy 도 `mcp-servers.json` 에서 뽑아 말한다. 박아 두면 그 목록만 낡는다 — 옛 판이
#   `setx TAVILY_API_KEY` 를 박고 있어, 파일에서 심고 난 뒤에도 손으로 치라고 말했다
#   (실측 2026-08-31). 진본은 `mcp-servers.json` 하나다.

# ── 판정 — **말만 하지 말고 종료코드로 낸다** ──────────────────────────────────
# ⚠ 위 「끝내지 못했다」는 화면에만 있었다. 이 스크립트는 마지막 `echo` 로 끝나 **늘 0** 이었고,
#   그래서 이것을 부르는 `install.ps1` 은 부트스트랩이 졌다는 것을 알 길이 없었다 —
#   설치 화면이 초록으로 끝났다 (실측 2026-09-10 · 사내·사외 VDI). 안내는 안내대로 다 찍고,
#   판정만 여기서 낸다.
#   판정만 여기서 낸다.
# ⚠ **deploy 만이 지는 자리가 아니다.** 앞 칸들이 못 세운 것(`FAILS`)도 같이 낸다 — 옛 판은
#   deploy 종료코드만 봐서, git 신원을 못 심고 clone 이 다 진 기계도 **0 으로 끝났다.**
_rc="${DEPLOY_RC:-0}"
if [ -n "$FAILS" ] || [ "$_rc" -ne 0 ]; then
    echo
    [ -n "$FAILS" ] && echo "못 세운 것 —$FAILS"
    [ "$_rc" -ne 0 ] && echo "deploy 가 exit $_rc 로 죽었다"
    exit 1
fi
# ⚠ **초록 옆에 「안 선 것」을 찍는다.** 런타임이 모자란 것도 로그인이 안 선 것도 이 몸통이
#   질 일이 아니다(깔 자는 `install.ps1` 이고 누를 자는 사람이다). 그렇다고 안 적으면
#   「됐다」가 **전부 됐다**로 읽힌다 — 판정과 경계를 한자리에서 낸다.
_edge=""
[ -n "$MISSING" ] && _edge="$_edge 안 닿는 것(${MISSING# })"
[ "${_logged:-}" != "true" ] && _edge="$_edge 로그인"
[ -n "$_edge" ] && echo "다만 안 선 것이 있다:$_edge"
exit 0
