#!/bin/bash
# 설치가 넘겨받는 자리 — **당신 저장소가 여기서부터 든다.** 여러 번 돌려도 안전하다.
#
#   부르는 자는 `install.ps1` 의 마지막 칸이다. 규약은 **파일 이름 하나** — 저장소 뿌리에
#   이 이름(`bootstrap-vdi.sh`)이 있으면 설치가 Git Bash 로 부르고, 없으면 실패로 찍는다.
#   손으로도 된다:  bash ~/repos/<당신 저장소>/bootstrap-vdi.sh
#
# ⚠ **몸통은 익명이다 — 목록은 옆 `bootstrap.conf` 가 든다.** 이름·주소·저장소 목록을
#   여기 박으면 다음 사람이 코드를 읽고 고쳐야 하고, 그러면 이 파일은 그 사람 것이 된다.
#   고칠 자리는 선언이고 여기는 그것을 읽어 도는 자다.
#
# ⚠ **프로그램은 여기서 안 깐다.** 무엇을 깔지는 `install.ps1` 한 자리가 들고 이 파일은
#   확인만 한다 — 목록을 둘로 두면 winget id 가 두 파일에 살고 그 어긋남이 **조용하다.**
#   여기가 드는 것은 **사람에게 딸린 것**이다: git 신원 · 저장소 · 닿음 판정.
#
# 자격증명은 담지 않는다. clone 때 GitHub 로그인 창이 한 번 뜬다.
set -u

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

FAILS=""

echo "== 1/3  git 전역 설정 =="
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

echo "== 2/3  저장소 =="
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

echo "== 3/3  런타임 확인 =="
# ⚠ **배선이 먼저다.** 이 셸은 `install.ps1` 이 깐 **뒤에** 떠도 그 PATH 를 못 물려받는다 —
#   창은 뜰 때 환경을 한 번 복사하고, 이 창을 띄운 부모가 그것들보다 먼저 떴다. 배선 없이
#   물으면 이미 깔린 것도 「없음」이 나와 판정이 통째로 뒤집힌다.
#   `cygpath` 로 POSIX 꼴을 만든다 — 윈도우 꼴(역슬래시)을 그대로 두면 `[ -d ]` 가 못 읽는다.
_pf="$(cygpath -u "${PROGRAMFILES:-}" 2>/dev/null)"
_la="$(cygpath -u "${LOCALAPPDATA:-}" 2>/dev/null)"
_add_path() {
    [ -d "$1" ] || return 0
    case ":$PATH:" in *":$1:"*) return 0 ;; esac   # 여러 번 불러도 PATH 가 안 분다
    PATH="$1:$PATH"
}
_add_path "$_pf/nodejs"
_add_path "$_pf/GitHub CLI"
# ⚠ 파이썬 판이 오르면 이 두 줄과 `install.ps1` 의 winget id 를 **같이** 올린다 —
#   한쪽만 고치면 게이트가 초록인 채로 엉뚱한 판을 재는 자리가 난다.
for _v in Python314 Python313 Python312; do
    _add_path "$_la/Programs/Python/$_v"
    _add_path "$_la/Programs/Python/$_v/Scripts"
done
_add_path "$_la/Programs/Python/Launcher"
# ⚠ `$APPDATA` 는 **윈도우 꼴**(`C:\Users\...\Roaming`)이라 `/npm` 을 그냥 붙이면 잡종
#   경로가 된다. 그러면 npm shim 이 제 자리를 Git 설치 폴더 기준으로 잘못 풀어
#   `claude.exe: No such file or directory` 로 죽는다. powershell 자식은 윈도우가 알아서
#   풀어 주므로 **bash 에서 부를 때만 깨진다.**
_add_path "$(cygpath -u "${APPDATA:-}" 2>/dev/null)/npm"
export PATH

# ⚠ **있나로 묻지 않고 불러 본다.** 윈도우는 `WindowsApps/python` 에 스토어로 보내는
#   **껍데기**를 깔아 두고, `command -v python` 이 그것을 잡아 「있음」을 낸다 — 부르면
#   「Python was not found」 를 뱉고 죽는 파일이다. 그 오판으로 넘어가면 뒤엣것이 검사를
#   꺼진 채로 두고 **초록으로 끝난다.** 깔린 것과 닿는 것은 다른 명제다.
_probe_cmd() { command -v "$1" >/dev/null 2>&1 && "$1" --version >/dev/null 2>&1; }

# ⚠ **안 닿아도 여기서 멈추지 않는다** — 위 칸들은 런타임 없이도 제 일을 했고, 멈추면
#   그 결과 보고까지 잃는다. 목록에 담아 끝에서 한 번에 낸다.
# ⚠ **쉼표로 가른다.** 사람이 읽는 이름에 빈칸이 들어(`GitHub CLI`) 빈칸으로 가르면 한
#   항목이 둘로 쪼개지고, **있는 도구가 「안 닿는다」로 찍힌다** — 씨앗을 처음 돌려 본
#   자리에서 그렇게 났다. `IFS` 는 이 고리 안에서만 바꾸고 되돌린다.
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

# ── 여기부터가 당신 자리다 ────────────────────────────────────────────────────
# 위 셋은 누구에게나 같다. 아래는 사람마다 갈리므로 씨앗이 지어 주지 않는다 —
# 필요한 것만 골라 여기 잇는다:
#
#   · 키를 심는다 — `setx` 로 사용자 환경변수에. **화면에 찍지 않는다**
#   · 홈 설정을 깐다 — `~/.claude/settings.json`
#   · 배포를 돈다 — 규범·룰·스킬을 저장소에서 홈으로
#   · 자리를 가른다 — 사내·사외를 **이름이 아니라 닿음으로** 잰다
#
# ⚠ **자리 판정은 `install.ps1` 에도 있다.** 여기에 또 쓰면 같은 사실이 두 자리에 살고,
#   한쪽만 고쳐지는 날 어느 쪽이 맞는지 아무도 모른다. 그쪽 값을 쓰거나, 여기서만 잰다.

# ── 판정 — **말만 하지 말고 종료코드로 낸다** ─────────────────────────────────
# ⚠ 마지막 `echo` 로 끝내면 이 스크립트는 **늘 0** 이다. 그러면 부르는 `install.ps1` 은
#   부트스트랩이 졌다는 것을 알 길이 없어 **설치 화면이 초록으로 끝난다.** 안내는 안내대로
#   다 찍고, 판정은 여기서 낸다.
echo ''
if [ -n "$FAILS" ]; then
    echo "끝내지 못했다 —$FAILS"
    exit 1
fi
# ⚠ **초록 옆에 「안 닿는 것」을 찍는다.** 런타임이 모자란 것은 이 스크립트의 실패가
#   아니지만(깔 자는 `install.ps1` 이다), 그 사실을 안 적으면 「됐다」가 **전부 됐다**로
#   읽힌다. 판정과 경계를 한자리에서 낸다.
if [ -n "$MISSING" ]; then
    echo "됐다 — 다만 안 닿는 것이 있다:$MISSING"
    echo '  install.cmd 를 먼저 돌린다. 이 칸이 깔지는 않는다.'
    exit 0
fi
echo '됐다 — 열려 있는 VS Code 를 전부 닫고 새로 연다.'
echo '  창은 뜰 때 환경을 한 번 복사하고 그 뒤에 바뀐 것은 안 따라온다.'
exit 0
