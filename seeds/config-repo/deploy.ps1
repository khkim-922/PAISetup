# claude-config -> 이 PC에 배포
#
#   사용법:  .\deploy.ps1          배포. 무엇을 할지 보여주고 승인받은 뒤 실행
#            .\deploy.ps1 -Prune   배포 + 제거. 원본에 없는 것을 정리한다
#            .\deploy.ps1 -Yes     승인 없이 실행 (자동화용)
#            .\deploy.ps1 -ShowUnchanged   안 바뀐 것까지 한 줄씩 편다 (뭔가 어긋났을 때만)
#
# git이 옮기는 것은 파일일 뿐이다. 이 스크립트를 돌려야 실제로 적용된다.
# 회사 PC에서는 `git pull` 다음에 이것만 실행하면 된다.
#
# 하는 일 — **번호가 곧 차례다**
#   1. 형제 저장소를 원격까지 맞춘다 (main 위에서만 · 빨리감기로만 · 저장소마다 판정 한 줄)
#      **계획을 짓기 앞이다** — 계획과 설치 판정이 지문을 보므로, 뒤에 두면 새로 들어온 선언이
#      다음 회차에야 깔린다. 져도 던지지 않는다. 까닭은 아래 §당김 과 결정 0078
#   2. .githooks/ 를 둔 저장소에 core.hooksPath 설정 (git 훅은 clone 을 안 따라온다)
#      **바꾸는 걸음 가운데 맨 앞에 둔다** — 로컬 `git config` 한 줄이라 질 까닭이 없고, 뒤가
#      무엇으로 죽든 커밋 게이트만은 서 있어야 한다. 까닭은 아래 §실행 순서 (#31)
#   3. 진본을 홈과 형제 저장소로 민다 — **무엇이 어디로 가나의 표는 README 「배포 대상」이 든다**
#      (여기 옮겨 적지 않는다 — 세 자리가 같은 표를 다른 낱말로 들다 갈렸다). 목록의 진본은 선언
#      셋이다: deploy.repofiles.conf(저장소로 가는 파일) · deploy.seeds.conf(홈으로 폴더째) ·
#      deploy.skills.local.conf(홈에서 빼는 스킬). 어느 저장소·어느 슬러그로 가나는 선언이 아니라
#      personal.conf 의 REPOS · ROOT 에서 **파생한다**(결정 0072)
#   4. mcp-servers.json에 적힌 MCP 서버 등록 — **서버마다 `only` 로 자리를 걸 수 있다**
#      (`only = <자리>,<자리>`). 이 자리가 그 목록에 없으면 안 등록하고, 이미 등록돼 있으면
#      기본 실행에서 걷는다. 자리는 세션 훅에 묻는다(`--site`) — 결정 0079
#   5. 설치 — 걸음이 둘이다 (#43)
#      5a. 전역 설치 한 번    claude-config 의 훅을 `--install-global` 로 불러 전역형 도구
#                             (npm 전역 · 릴리스 바이너리 · winget · 브라우저)를 기계에 한 번 깐다
#      5b. 저장소마다         각 저장소의 .claude/hooks/session-start.sh 를 `--install` 로 불러
#                             프로젝트 축(venv · npm ci)과 배선을 세운다
#      무엇을 깔지는 그 훅이 알고 이 스크립트는 모른다 — 도구 이름이 여기 없는 까닭이다
#   6. 사용자 환경변수 — 이 PC 전체에 걸려야 하는 것 (인코딩 축. 아래 §사용자 환경변수)
#   7. 남은 수동 작업 안내 (API 키 등)
#
# 복사하지 않는 것 — 무엇이 배포되고 무엇이 안 되는지는 README 의 배포 대상 표가 든다.
# 여기 적는 것은 **이름이 같아 헷갈리는 자리** 하나뿐이다.
#   ~/.claude/settings.json   **홈의 개인 설정** (모델·테마 등). PC마다 달라 수동 관리.
#                             저장소의 .claude/settings.json 은 훅 등록 파일이라 배포한다 —
#                             이름이 같을 뿐 다른 것이다
#
# 기본 실행이 지우는 것은 **하나뿐이다** — 선언에 있으면서 `only` 로 이 자리에서 안 사는 MCP
# 이름(결정 0079). 그것은 「원본에 없는 것」이 아니라 **선언이 시킨 상태**라 -Prune 이 아닌
# 계획에 선다. 나머지 제거는 -Prune 을 줄 때만 하고, 후보가 있으면 기본 실행에서도 개수만 알려준다.
#
# 이미 맞는 것은 건드리지 않는다. 몇 번을 돌려도 안전하다.
# 덮어쓰거나 치우는 파일은 ~/.claude/backups/deploy-<시각>/ 에 원본을 남긴다.

param([switch]$Yes, [switch]$Prune, [switch]$ShowUnchanged)

$ErrorActionPreference = 'Stop'

# 콘솔 출력 UTF-8 강제. PowerShell 5.1 기본은 시스템 코드페이지(한국은 cp949)라
# 이 스크립트의 한글이 깨진다. UTF-8로 고정해 어느 PC에서도 그대로 읽히게 한다.
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$src    = $PSScriptRoot
$dst    = Join-Path $HOME '.claude'
$backup = Join-Path $dst ('backups\deploy-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))

$plan    = @()   # 바꿀 것
$same    = @()   # 이미 맞는 것
$todo    = @()   # 사람이 해야 할 것
# ⚠ **`$todo` 와 갈라 둔다.** 저쪽은 「사람이 손으로 할 것」(키 입력 같은)이라 남아 있어도
#   환경은 서 있다 — 그것으로 빨강을 내면 판정이 늘 빨강이라 아무것도 안 말한다.
#   이쪽은 **실행 환경이 안 선 것**이고, 이 목록이 비지 않으면 이 스크립트는 0 으로 안 끝난다.
$envDown = @()   # 실행 환경이 안 선 것 — 종료코드를 가른다
$prunable = @()  # 제거 후보 — **원본에 없는 것** (-Prune 없이는 세기만 한다)
# ⚠ 자리가 뺀 MCP 이름은 **여기 안 든다** — 선언에 있으므로 「원본에 없는 것」이 아니다.
#   그것은 $plan 의 `mcpremove` 로 서서 기본 실행에서 걷힌다 (§MCP 등록 · 결정 0079).
# ⚠ **초록도 편다.** 통과가 화면에서 침묵하면 「재서 다 살아 있다」와 「아예 안 쟀다」가
#   같아진다 — 그 침묵은 아무것도 안 말한 것과 같다. 여기는 나르기만 한다.
# ⚠ 이제 이 통에 드는 것은 **저장소마다 「마지막 CI」 한 줄**뿐이다 — 훅 진단은 계획 단계가
#   안 돌리고(`--needs-install` 은 파일만 본다 · #47 ②) 저장소 설치 걸음이 `--install` 끝에 그
#   자리에서 낸다.
$gateReport = @()  # 저장소마다 마지막 CI 한 줄 — 초록·빨강·못 쟀다

# 배포 대상은 PC 마다 적지 않고 `personal.conf` 에서 **파생한다** (결정 0072 · 0019 를 대체).
# ⚠ **왜 파생인가.** 옛 판은 PC 마다 `deploy.targets.d/<PC>.conf` 에 저장소 절대 경로와 메모리 슬러그를
#   손으로 적었다. 네 장이 사용자 이름 한 칸만 달랐고, 그 한 칸이 다른 새 PC 에서는 저장소 배포 · 저장소
#   설치 · **전역 설치** · 메모리가 통째로 안 섰다 — 게이트 도구(commitlint · markdownlint · lychee · ruff)가
#   안 깔려 커밋 게이트가 「못 쟀다」로만 돌았다(2026-09-24 · 09-28). 저장소 목록과 자리는 이미
#   `personal.conf`(REPOS · ROOT)가 들고 세션 훅이 그것으로 clone 하고 슬러그 폴더를 세운다 — 같은 사실의 사본이었다.
# ⚠ **슬러그는 제품의 규칙대로 짓는다** — 윈도 경로에서 영숫자가 아닌 글자를 **글자마다** `-` 로.
#   PowerShell 의 `-replace` 는 UTF-16 글자로 세므로 한글 한 자가 대시 하나다(세션 훅의 같은 규율 ·
#   `C:\Users\김균한\repos` → `C--Users-----repos`). 메모리 폴더와 자리의 짝은 셋이다:
#     memory/<REPOS 의 이름>/  → ROOT\<이름>
#     memory/<이 저장소 이름>/ → 이 저장소 자리
#     memory/global/           → ROOT (저장소들을 담은 폴더에서 연 세션)
$memTargets = @{}          # memory/<이름> -> 그 메모리가 딸린 폴더 경로 (슬러그는 이 경로에서 짓는다)
$globalRuleTargets = @()   # 저장소 배포본을 받고 설치 걸음이 도는 저장소 루트들
function ConvertTo-Slug([string]$Path) { $Path -replace '[^A-Za-z0-9]', '-' }
$personalConf = Join-Path $src 'personal.conf'
$pc = @{}
if (Test-Path $personalConf) {
    foreach ($line in (Get-Content $personalConf -Encoding UTF8)) {
        if ($line -match '^\s*([A-Z_]+)\s*=\s*(.*?)\s*$') { if (-not $pc.ContainsKey($Matches[1])) { $pc[$Matches[1]] = $Matches[2] } }
    }
} else {
    $todo += 'personal.conf 가 없다 — 어느 저장소로 뿌릴지 몰라 저장소 배포본 · 설치 · 저장소 메모리가 안 간다. 씨앗의 personal.conf 를 채워 둔다'
}
# ROOT 의 `$HOME` · `~` 는 세션 훅이 푸는 것과 같이 푼다. 비면 세션 훅의 기본값과 같은 `~/repos`.
$repoRoot = if ($pc['ROOT']) { $pc['ROOT'] } else { '$HOME/repos' }
$repoRoot = ($repoRoot -replace '^\$HOME', $HOME -replace '^~', $HOME) -replace '/', '\'
$repoNames = @(($pc['REPOS'] -split '\s+') | Where-Object { $_ })
foreach ($n in $repoNames) {
    $p = Join-Path $repoRoot $n
    $globalRuleTargets += $p
    $memTargets[$n] = $p
}
$memTargets[(Split-Path $src -Leaf)] = $src
$memTargets['global'] = $repoRoot
# ⚠ **적힌 저장소가 이 PC 에 하나도 없으면 말한다** — 그때 저장소 설치 걸음도, 그에 딸린 전역 설치 걸음도
#   통째로 안 선다. clone 은 세션 훅(`--install`)이 personal.conf 의 REPO_URL 로 한다.
if ($repoNames.Count -gt 0 -and -not ($globalRuleTargets | Where-Object { Test-Path $_ })) {
    $todo += "personal.conf 의 REPOS 가 이 PC 의 $repoRoot 에 하나도 없다 — 저장소 설치 · 전역 설치가 안 선다. 세션 훅의 --install 이 REPO_URL 로 받는다"
}
# 옛 선언이 남았으면 말한다 — 더는 안 읽는데 남아 있으면 「고쳤는데 안 먹는다」로 사람을 헤매게 한다.
if ((Test-Path (Join-Path $src 'deploy.targets.conf')) -or
    @(Get-ChildItem (Join-Path $src 'deploy.targets.d') -Filter *.conf -File -ErrorAction SilentlyContinue).Count) {
    $todo += 'deploy.targets.d/ · deploy.targets.conf 는 더 안 읽는다 — 대상은 personal.conf 의 REPOS · ROOT 에서 파생한다(결정 0072). 지운다'
}

# memory/<project>/ 가 이 PC 에서 갈 곳. 그 메모리가 딸린 폴더가 이 PC 에 없으면(적었지만 아직 안 받은
# 저장소) 빈 배열 — 없는 저장소의 슬러그 폴더를 새로 세우지 않는다. 폴더가 있으면 슬러그 폴더가 아직
# 없어도 간다(복사가 폴더를 세운다) — 곁에 붙이기만 하던 저장소는 Claude Code 가 그 폴더를 안 세운다.
# ⚠ 슬러그는 **실제 경로 글자**에서 짓는다(`Resolve-Path`) — 제품도 그 글자로 짓는다.
function Get-ProjectMemDst($project) {
    $home_ = $memTargets[$project]
    if (-not $home_) { return @() }
    $slug = if (Test-Path $home_) { ConvertTo-Slug (Resolve-Path $home_).Path } else { ConvertTo-Slug $home_ }
    if (-not (Test-Path $home_) -and -not (Test-Path (Join-Path $dst "projects\$slug"))) { return @() }
    @(Join-Path $dst "projects\$slug\memory")
}

# PATH의 bash는 WSL일 수 있다(배포판 없으면 실패). git.exe 위치에서 Git Bash를 직접 찾는다.
$bash = @(
    (Get-Command git -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path (Split-Path (Split-Path $_.Source -Parent) -Parent) 'bin\bash.exe' }),
    "$env:ProgramFiles\Git\bin\bash.exe",
    "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1


# ── 당김 — **계획을 짓기 앞에** 형제 저장소를 원격까지 맞춘다 (결정 0078 · 이슈 18 을 잇는다) ──
# ⚠ **왜 계획 앞인가.** 아래 계획(`$targets` · `$plan`)과 설치 판정(`--needs-install`)은 **지금 그
#   저장소에 있는 파일의 지문**을 본다. 당김을 그 뒤에 두면 새로 들어온 선언이 이번 회차에 안 깔리고
#   다음 회차에야 깔린다 — 실측 2026-09-12 의 ruff 가 그 병이었고(둘째 판에서 깔렸다) 아래
#   `$declChanges` 땜질이 그 자리에 남은 흉이다.
# ⚠ **왜 여기로 옮겼나.** 옛 판은 당기는 자를 `'copy'` 걸음 **안**에 두어, 배포본 지문이 어긋나
#   밀 것이 있는 회차에만 당겼다. 평상시에는 copy 가 안 서고 **당김도 함께 사라졌다** — 실측
#   2026-10-06 회사 PC: 2주 넘게 어떤 설치 회차도 형제를 당기지 않았고, 「안 당겼다」가 조용해서
#   아무도 몰랐다(#112). 그래서 지금은 **밀 것이 하나도 없는 회차에도** 저장소마다 판정 한 줄이 선다.
# ⚠ **밀기 전에 당긴다는 규율은 그대로다** — 뒤처진 저장소에 새 진본이 앉으면 그것이 M 이 되고,
#   다음 세션의 훅 당김(`merge --ff-only`)이 그 M 에 막힌다. 한 번 막히면 사람이 되돌리기 전까지
#   안 풀린다 — **배포가 다음 배포를 막는 고리다.** 실측 2026-09-09 회사 PC: 훅이
#   `error: Your local changes … would be overwritten by merge` 로 두 번 졌다.
# ⚠ **못 당기면 안 민다.** 밀어 봐야 그 저장소는 당김이 막힌 채 트리만 더 더러워진다 — 고리를
#   끊으려는 자리에서 고리를 한 바퀴 더 돌리는 꼴이다. 판정은 `$pulledRepos` 가 들고 아래
#   `'copy'` 걸음은 그것을 **읽기만** 한다(당기는 자를 부르는 자리는 이 한 곳이다).
# ⚠ main 위에서만 당긴다 — 작업 중인 브랜치를 건드리지 않는다(훅 `pull_ff` 와 같은 자).
# ⚠ **`pull` 이 아니라 `fetch` + `merge --ff-only` 다** (#87). `pull` 은 제 fetch 를 돌린 뒤
#   `FETCH_HEAD` 를 읽어 무엇을 병합할지 정하는데, 그 파일은 **저장소당 한 장이라 경쟁의 자리다** —
#   같은 순간 다른 git(VS Code 로 연 세션의 훅 당김)이 끼어들면 갈래가 두 줄 적히고 pull 은 그것을
#   병합 대상 둘로 읽어 `fatal: Cannot fast-forward to multiple branches.` 로 진다. 당김이 매 회차로
#   늘면 겹칠 자리도 늘어난다. `merge` 에 **이름 있는 자리**(추적 갈래)를 주면 남이 그 파일에 무엇을
#   쓰든 무관해진다.
# ⚠ **refspec 을 두 칸 다 적는다** — 한 갈래만 받게 클론된 저장소는 `fetch <원격> main` 이 추적
#   갈래를 안 옮기고 `FETCH_HEAD` 만 쓴다(훅 `sync_main` 의 같은 규율). 그러면 병합 대상이 안
#   움직여, 아무것도 안 전진했는데 성공으로 끝난다.
# ⚠ **fetch 는 저장소마다 동시에 띄우고, merge 는 다 끝난 뒤 차례로 한다.** 저장소가 다르면
#   `FETCH_HEAD` 도 다른 파일이라 fetch 끼리는 안 겹치고, 한 곳이 느려도 나머지를 안 막는다 —
#   직렬이면 사내 망에서 저장소 수 × 6~7초를 그대로 문다(세션 훅 `pull_ff` 머리의 실측). 작업
#   나무를 옮기는 `merge` 는 차례로 둔다.
# ⚠ **배경이 아니라 동기다.** 세션 훅은 당김을 배경으로 뺐는데(0043 · 0069) 그 까닭은 확장이
#   초기화를 60초만 기다리는 벽이었다. 이 자리는 부팅·로그온 자동 실행이고 그 **직후에 아뜰리에
#   서버가 뜬다** — 서버가 뜨기 전에 최신이어야 당긴 것이 이번 부팅에 실린다. 0043 과 안 부딪힌다.
# ⚠ **져도 던지지 않고 종료코드를 올리지도 않는다.** 부팅 라인의 서버 띄우기는 앞 단계의
#   종료코드·시간 초과를 안 보고 늘 서는데, 그 성질을 깨지 않는다 — 옛 판 서버가 도는 것이 서버가
#   아예 안 뜨는 것보다 낫다. 한 저장소의 실패는 그 저장소의 밀기만 막고 나머지는 다 돈다.
# ⚠ **훅의 90초 표식(`.git/claude-pull-attempted`)은 읽지도 쓰지도 않는다** — 까닭은 결정 0078.
#   그 표식은 한 세션에서 훅 둘이 겹치는 것을 막는 자리이고, 이 자리의 물음은 「서버가 뜨기 전에
#   최신인가」라 남이 90초 안에 **시도했다**는 사실로는 답이 안 된다.
# ⚠ **리다이렉트가 곧 위험이다** — 이 파일에서 가장 되묻기 쉬운 자리라 여기 적어 둔다.
#   이 스크립트는 `$ErrorActionPreference = 'Stop'` 을 든다. 그 아래에서 파워셸 5.1 은
#   네이티브의 stderr 를 **파워셸이 건드릴 때만** `NativeCommandError` 로 감싸고, 그것이
#   종료 오류가 되어 배포를 통째로 죽인다. 실측 2026-09-10 로 갈린 두 편:
#     · 죽는다 — `2>$null` · `2>$파일` · `2>&1` · `*> $null`  (넷 다 방패가 아니다)
#     · 안 죽는다 — 리다이렉트를 아예 안 한 자리. stderr 가 콘솔로 흘러 오류 기록이 안 난다
#                   (`| Out-Null` 이나 값으로 받는 것도 stdout 쪽이라 안전하다)
#   옛 판은 `2>$파일` 을 방패로 믿었고, 그래서 「못 당김」 갈래는 **한 번도 안 돌았다**
#   — 저장소 하나의 로컬 수정이 배포 전체를 죽였다 (실측 2026-09-09 · 사내 PC ·
#   deploy 가 exit 1 로 끝나고 뒤의 배포·MCP 가 다 남았다).
# ⚠ 그래서 **자식으로 띄운다.** `Start-Process` 는 stderr 를 파워셸에 안 태우고 파일에
#   바로 붓는다 — 파워셸이 볼 것이 없으니 승격될 것도 없다. 끝나기를 기다리면 종료코드도
#   제대로 든다. `ErrorActionPreference` 를 잠깐 내리는 길도 살긴 하는데, 그러면 파일에
#   담기는 것이 git 의 말이 아니라 **파워셸이 꾸민 오류 기록**이라 아래 사유 고르기가
#   `Aborting` 을 집는다 — 바로 그 주석이 막으려던 자리다.
# ⚠ **기다림에 한도가 있다 — 걸린 당김은 거두고 그 저장소만 「못 당김」으로 적는다.**
#   이 자리가 배포의 **첫 걸음**이라, 여기서 안 끝나면 배선(`core.hooksPath`) · 계획 · 배포 ·
#   설치가 통째로 안 돈다. 무인 라인에서 그것은 조용한 굳음이다: 라인의 10분 울타리가 autorun 을
#   거두고 아뜰리에 서버는 옛 판으로 뜬다. 걸리는 길이 둘 있다 — **창을 띄우려는 자격증명
#   도움꾼**(죽은 토큰 · 사람이 없는 세션)과 **답을 안 주는 망**(프록시가 삼키는 자리).
#   그래서 셋을 함께 둔다: 묻는 자리를 비대화로 못 박고(`Sync-Repos` 머리의 이름 둘) · 묶음
#   전체에 벽시계 한도를 두고 · 넘긴 자식을 거둔다. **최악의 경우 배선이 늦는 폭이 곧 이 한도다.**
# ⚠ **0043 이 거절한 「시간 제한」과 다른 것이다.** 저쪽이 거절한 것은 정상이 7초인 왕복을 5초로
#   자르는 일이었다 — 되던 당김까지 실패로 찍는다. 여기 한도는 **정상의 열 배를 넘는 자리**에
#   두어 걸린 것에만 걸린다(사내 망 실측 하나 6~7초 · 동시에 돌므로 묶음도 그 값에 가깝다).
# ⚠ 이 고침은 **차례를 바로잡는다.** 진본이 바뀌면 형제 저장소의 배포본 커밋도 같은 판에
#   나가야 하고(`chore(claude): 훅 배포본을 진본과 다시 맞춘다`), 안 나가면 당겨도
#   뒤처진 채라 M 이 다시 뜬다 — 그리고 그 M 은 맞다.
# 한도는 **이름 둘이 든다** — 값을 아래 고리에 박으면 화면에 찍는 초와 재는 초가 갈린다.
$PullBatchTimeoutSec = 120   # fetch **묶음 전체**의 벽시계 한도. 넘긴 자식만 거둔다
$PullMergeTimeoutSec = 30    # merge 하나의 한도 — 디스크 일이라 망을 안 탄다(걸리면 잠금이다)
$pulledRepos = @{}   # 저장소 -> 이번 회차에 그 저장소로 밀어도 되나 (당김 판정)

function Get-GitWhy($file) {
    # 사유를 고르는 자는 훅 `git_why` 와 같은 결이다 — 끝줄이 아니라 첫 `fatal:`/`error:` 줄이다.
    # 로컬 수정 갈래는 끝줄이 `Aborting` 이라, 끝줄을 집으면 사유가 있는데 층이 안 갈린다.
    $raw   = (Get-Content $file -Raw -ErrorAction SilentlyContinue)
    $lines = @(("$raw" -split "`r?`n") | Where-Object { $_.Trim() })
    $why   = @($lines | Where-Object { $_ -match '^(fatal|error):' })[0]
    if (-not $why) { $why = $lines[-1] }
    if (-not $why) { $why = '사유가 안 나왔다' }
    return "$why".Trim()
}

function Start-GitChild($gitArgs) {
    # git 하나를 자식으로 띄운다 — **기다리는 것은 부르는 쪽이 한다**(fetch 는 묶음으로 기다리고
    # merge 는 하나씩 기다려, 기다리는 꼴이 둘이라 이 자는 띄우기만 든다).
    # 돌려주는 것: @{ Proc; Err; Out } · 못 띄웠으면 @{ Why = 사유 }
    $errFile = [System.IO.Path]::GetTempFileName()
    $outFile = [System.IO.Path]::GetTempFileName()
    try {
        $p = Start-Process -FilePath 'git' -ArgumentList $gitArgs `
               -NoNewWindow -PassThru `
               -RedirectStandardError $errFile -RedirectStandardOutput $outFile
        # ⚠ **손잡이를 여기서 잡아 둬야 종료코드가 남는다.** `-Wait` 없이 띄운
        #   `Start-Process -PassThru` 의 Process 객체는 자식이 끝나면 `ExitCode` 가 **빈 값**이다 —
        #   던지지도 않아서 「0 이 아니다」로 읽히고, 그러면 성공한 fetch 가 전부
        #   `! 못 당김 — 사유가 안 나왔다` 로 나온다(실측 2026-10-06 · 가짜 저장소 다섯이 다
        #   그렇게 나왔다). `.Handle` 을 한 번 읽어 두면 .NET 이 핸들을 쥐고 있어 종료코드가
        #   남는다. 못 읽으면 그 저장소는 「못 쟀다」로 떨어진다 — 0 으로 접지 않는다.
        try { $null = $p.Handle } catch { }
        return @{ Proc = $p; Err = $errFile; Out = $outFile }
    } catch {
        Remove-Item $errFile, $outFile -Force -ErrorAction SilentlyContinue
        return @{ Why = "git 을 못 띄웠다: $($_.Exception.Message.Split([char]10)[0].Trim())" }
    }
}

function Stop-GitChild($job) {
    # 한도를 넘긴 자식을 거둔다.
    # ⚠ **`taskkill.exe` 에 매지 않는다 — 이 기계에서 그놈이 아예 안 돈다.** 실측 2026-10-06
    #   회사 PC: 제 자식에게조차 「액세스가 거부되었습니다」로 실행 자체가 거부된다(보안 소프트가
    #   그 바이너리를 막는다). 같은 자리에서 `Stop-Process -Force` 와 `.NET Kill()` 은 멀쩡히
    #   죽였다 — 부팅 라인(`scripts/startup-pipeline.ps1` 의 거두는 자)이 같은 까닭으로 같은 길이다.
    # ⚠ **나무째 안 내려간다.** git 이 띄운 전송 도움꾼(`git-remote-https`)은 부모가 죽으면 파이프가
    #   끊겨 제 발로 나간다. 그리고 이 자리에는 라인의 겹침 가드처럼 **남은 손자가 굳히는 자리가
    #   없다** — 다음 회차는 당김을 새로 띄운다.
    try { Stop-Process -Id $job.Proc.Id -Force -ErrorAction Stop }
    catch { try { $job.Proc.Kill() } catch { } }
}

function Complete-GitChild($job) {
    # 끝난 자식의 **종료코드와 사유 한 줄**을 읽고 임시 파일을 걷는다.
    # ⚠ 코드가 $null 이면 「못 쟀다」다 — 부르는 쪽이 0 으로 접지 않는다.
    $code = $null
    try { $code = $job.Proc.ExitCode } catch { $code = $null }
    $why = Get-GitWhy $job.Err
    Remove-Item $job.Err, $job.Out -Force -ErrorAction SilentlyContinue
    return @{ Code = $code; Why = $why }
}

function Invoke-GitWait($gitArgs, $timeoutSec) {
    # git 하나를 띄워 **한도 안에서** 기다린다. 넘기면 거두고 「시간 초과」로 낸다.
    $job = Start-GitChild $gitArgs
    if ($job.Why) { return @{ Code = $null; Why = $job.Why } }
    $done = $false
    try { $done = $job.Proc.WaitForExit($timeoutSec * 1000) } catch { $done = $true }
    if (-not $done) {
        Stop-GitChild $job
        Remove-Item $job.Err, $job.Out -Force -ErrorAction SilentlyContinue
        return @{ Code = $null; Why = "시간 초과 (${timeoutSec}초)" }
    }
    return Complete-GitChild $job
}

function Sync-Repos($repos) {
    # 저장소마다 판정 한 줄을 **반드시** 낸다 — `↓ 당김` · `· 당김 건너뜀` · `! 못 당김` 하나다.
    # 「안 당겼다」가 조용했던 것이 이 결함이 2주 묻힌 까닭이다(#112).
    #
    # ⚠ **묻는 자리를 비대화로 못 박는다.** 부팅·로그온 자동 실행에는 자격증명을 넣을 사람이
    #   없다. 토큰이 죽었거나 자격증명이 비면 git 의 도움꾼(GCM)이 **창을 띄우려 하고**, 창을
    #   띄울 데가 없는 세션에서 그 fetch 는 영영 안 끝난다 — 아래 한도가 그것을 거두지만,
    #   애초에 안 묻게 하는 편이 싸고 사유도 또렷하다(git 이 그 자리에서 지고 한 줄을 남긴다).
    # ⚠ **이 셸에 남기지 않는다.** 뒤의 걸음들(gh · 저장소 설치 · MCP)은 사람의 자격증명을 쓸
    #   수 있다. 옛 값을 쥐고 끝에서 되돌린다 — 없던 이름은 다시 없애야 한다.
    $savedPrompt = $env:GIT_TERMINAL_PROMPT
    $savedGcm    = $env:GCM_INTERACTIVE
    $env:GIT_TERMINAL_PROMPT = '0'
    $env:GCM_INTERACTIVE     = 'Never'
    try {
        $fetches = @()
        foreach ($repo in $repos) {
            if (-not (Test-Path (Join-Path $repo '.git'))) { continue }
            # ⚠ `2>$null` 은 위에 적은 대로 방패가 아니다 — 여기서는 잡아서 넘긴다.
            #   HEAD 를 못 읽으면 「main 이 아니다」와 같은 값이라 그 갈래로 떨어뜨린다.
            try { $head = (& git -C $repo symbolic-ref --short -q HEAD 2>$null) } catch { $head = '' }
            $head = "$head".Trim()
            if ($head -ne 'main') {
                # ⚠ **당길 수 없는 저장소에도 안 민다** — 못 당긴 자리와 같은 값이다. 여기 밀면
                #   그 M 은 사람이 main 으로 돌아온 뒤의 당김을 막는다. 「지금 안 막혔다」가
                #   아니라 「나중에 막힐 것을 안 만든다」가 이 게이트의 뜻이다.
                # ⚠ **빈 값은 「main 이 아니라 ''」가 아니다** — 분리된 HEAD(rebase · 태그 체크아웃)이거나
                #   HEAD 를 아예 못 읽은 자리다. 빈 따옴표를 보여 주면 사람이 브랜치 이름을 찾는다.
                $why = if ($head) { "main 이 아니라 '$head'" } else { '분리된 HEAD 이거나 읽지 못했다' }
                Write-Host "· 당김 건너뜀  $repo  ($why)" -ForegroundColor DarkGray
                $pulledRepos[$repo] = $false
                continue
            }
            # 원격 이름을 박지 않는다 — 추적 설정에서 읽는다(훅 `pull_ff` 와 같은 자리).
            try { $remote = (& git -C $repo config --get branch.main.remote 2>$null) } catch { $remote = '' }
            $remote = "$remote".Trim()
            if (-not $remote) {
                # 당길 자리가 없다. **그래도 안 민다** — 옛 판의 `pull --ff-only` 도 이 자리에서
                # 졌으므로(`There is no tracking information…`) 판정을 그대로 둔다. 이 고침은
                # 차례만 바꾼다.
                Write-Host "· 당김 건너뜀  $repo  (main 에 추적 원격이 없다)" -ForegroundColor DarkGray
                $pulledRepos[$repo] = $false
                continue
            }
            try { $was = (& git -C $repo rev-parse --short HEAD 2>$null) } catch { $was = '' }
            $job = Start-GitChild @('-C', $repo, 'fetch', '-q', $remote,
                                    "+refs/heads/main:refs/remotes/$remote/main")
            if ($job.Why) {
                Write-Host "! 못 당김  $repo — $($job.Why)" -ForegroundColor Red
                $pulledRepos[$repo] = $false
                continue
            }
            $job.Repo   = $repo
            $job.Remote = $remote
            $job.Was    = "$was".Trim()
            $fetches += $job
        }

        # ── 다 끝나기를 기다린다 — **묶음 전체에 벽시계 한도가 있다** ───────────────────
        # 동시에 돌므로 이 칸의 값은 보통 가장 느린 하나의 값이다. 한도를 넘기면 그때까지 안 끝난
        # 자식만 거두고 그 저장소를 「시간 초과」로 적는다 — 끝난 것들의 판정은 그대로 산다.
        # ⚠ **남은 예산으로 기다린다.** 자식마다 한도를 새로 주면 저장소 수만큼 곱해져, 다섯이 걸린
        #   날 한도가 열 배가 된다 — 배선이 그만큼 늦는다.
        $deadline = (Get-Date).AddSeconds($PullBatchTimeoutSec)
        foreach ($f in $fetches) {
            $leftMs = [int][math]::Max(0, ($deadline - (Get-Date)).TotalMilliseconds)
            $done = $false
            try { $done = $f.Proc.WaitForExit($leftMs) } catch { $done = $true }
            if (-not $done) {
                Stop-GitChild $f
                $f.TimedOut = $true
            }
        }

        foreach ($f in $fetches) {
            $repo = $f.Repo
            if ($f.TimedOut) {
                Remove-Item $f.Err, $f.Out -Force -ErrorAction SilentlyContinue
                Write-Host "! 못 당김  $repo — 시간 초과 (${PullBatchTimeoutSec}초)" -ForegroundColor Red
                $pulledRepos[$repo] = $false
                continue
            }
            $r = Complete-GitChild $f
            if ($r.Code -ne 0) {
                Write-Host "! 못 당김  $repo — $($r.Why)" -ForegroundColor Red
                $pulledRepos[$repo] = $false
                continue
            }
            $m = Invoke-GitWait @('-C', $repo, 'merge', '--ff-only', '-q',
                                  "refs/remotes/$($f.Remote)/main") $PullMergeTimeoutSec
            if ($m.Code -ne 0) {
                Write-Host "! 못 당김  $repo — $($m.Why)" -ForegroundColor Red
                $pulledRepos[$repo] = $false
                continue
            }
            try { $now = (& git -C $repo rev-parse --short HEAD 2>$null) } catch { $now = '' }
            $now = "$now".Trim()
            # ⚠ **전진했나를 같이 낸다.** 「당겼다」만 적으면 새 코드가 들어온 회차와 아무것도 안 온
            #   회차가 한 줄로 같아진다 — 이 건의 끝 조건이 「원격까지 전진한다」라 그 값을 보여야 한다.
            if ($now -and $f.Was -and ($now -ne $f.Was)) {
                Write-Host "↓ 당김  $repo  ($($f.Was) → $now)" -ForegroundColor DarkGray
            } else {
                Write-Host "↓ 당김  $repo  (이미 최신)" -ForegroundColor DarkGray
            }
            $pulledRepos[$repo] = $true
        }
    } finally {
        if ($null -eq $savedPrompt) { Remove-Item Env:GIT_TERMINAL_PROMPT -ErrorAction SilentlyContinue }
        else { $env:GIT_TERMINAL_PROMPT = $savedPrompt }
        if ($null -eq $savedGcm) { Remove-Item Env:GCM_INTERACTIVE -ErrorAction SilentlyContinue }
        else { $env:GCM_INTERACTIVE = $savedGcm }
    }
}

# 대상은 `personal.conf` 의 REPOS 중 이 PC 에 `.git` 을 든 것이다 — 목록을 여기 안 적는다.
# 이 저장소 자신은 대상이 아니다: 부팅 라인에서 이 스크립트가 도는 것은 설치 `[8/8]` 이 이미
# 그것을 당긴 뒤이고, 지금 도는 몸통이 곧 그때 당겨 온 판이다.
Sync-Repos $globalRuleTargets


# ============================ 1단계: 계획 수립 ============================
# 아무것도 바꾸지 않는다. 무엇을 바꿔야 하는지만 조사한다.
# ⚠ **당김은 이 앞에 있다** — 그래서 이 단계가 보는 나무는 **당긴 뒤**의 나무고, 이 한 줄은
#   그대로 참이다(당김은 `$plan` 에 아무것도 안 더하므로 「다 최신이면 안 묻는다」도 산다).

# --- 파일 배포 ---
$agentSrc = Join-Path $src 'agents'
$memSrc   = Join-Path $src 'memory'
# 전역 규범 진본. **이름이 `CLAUDE.md` 가 아닌 것이 요점이다** — 이 저장소를 세션에
# 붙여도 자동 로드 대상이 아니라, 규범은 아래가 깔아주는 홈 한 자리로만 실린다.
# 진본이 `CLAUDE.md` 이던 시절에는 붙인 세션에서 두 판이 로드됐다 (docs/decisions/0002).
$ruleSrc  = Join-Path $src '.claude\CLAUDE.global.md'
$targets  = @(
    @{ From = $ruleSrc; To = Join-Path $dst 'CLAUDE.md' }
)
# ⚠ **`agents` 폴더가 없을 수 있다** — 이 스크립트는 `$ErrorActionPreference = 'Stop'` 이라, 없는 경로를
#   `Get-ChildItem` 에 그대로 주면 종료 오류로 계획 단계 한가운데서 죽고 **그 뒤 걸음(MCP · 저장소 설치 ·
#   환경변수)이 하나도 안 돈다**(#114). 없으면 이 걸음만 건너뛰고 한 줄 말한다. 아래 제거 후보도 같은
#   값을 본다 — **없는 폴더를 「원본이 비었다」로 읽으면 `-Prune` 이 홈의 에이전트를 다 지운다.**
$hasAgents = Test-Path -LiteralPath $agentSrc -PathType Container
if ($hasAgents) {
    Get-ChildItem $agentSrc -Filter *.md | ForEach-Object {
        $targets += @{ From = $_.FullName; To = Join-Path $dst "agents\$($_.Name)" }
    }
} else {
    Write-Host "· 에이전트 건너뜀  ($agentSrc 가 없다 — 홈의 에이전트도 안 건드린다)" -ForegroundColor DarkGray
}

# 전역 규범·룰은 저장소로 안 간다 — 홈 한 자리다 (docs/decisions/0014).
# 리모트 컨테이너는 홈이 비어 뜨지만, 그 통로는 claude-config 를 함께 붙이는 것이다
# (docs/decisions/0001 · 0010). 저장소가 사본을 지면 「이 저장소 것」과 「전역 것」이
# 한 폴더에서 섞여, 이름으로 갈라야 하고 그 이름이 PC 에서는 뜻이 없다.

# 저장소마다 한 벌씩 있어야 하는 것들: 각 저장소로. 몸통은 익명이라 저장소마다 바이트가
# 같고, 목록은 선언이 든다 (docs/decisions/0004). 홈으로는 안 간다 — 홈이 읽는 자리가
# 아니라 **그 저장소 안에서 읽히는** 자리들이다: 훅과 그 등록, 그리고 깃허브가 편집창을
# 채울 때 여는 이슈 템플릿 (docs/decisions/0021).
#
# ⚠ 여기의 `.claude\settings.json` 은 **저장소의 훅 등록 파일**이지 홈의 개인 설정이
#   아니다. 홈 것(~/.claude/settings.json)은 여전히 수동이다 — 위 머리글 참조.
#   저장소 것은 세 저장소가 이미 바이트가 같아 익명 몸통과 같은 결로 뿌린다.
# 목록은 선언이 든다 — 재는 자(scripts/check-global-copies.sh)도 같은 파일을 읽는다.
# 배열로 박아 두면 두 자가 손사본이 되어 한쪽만 고쳐진다 (docs/decisions/0021).
$repoFilesConf = Join-Path $src 'deploy.repofiles.conf'
$repoFiles = @()
if (Test-Path $repoFilesConf) {
    $repoFiles = @(Get-Content $repoFilesConf -Encoding UTF8 |
        ForEach-Object { ($_ -replace '#.*$', '').Trim() } |
        Where-Object   { $_ } |
        ForEach-Object { $_ -replace '/', '\' })
}
if ($repoFiles.Count -eq 0) {
    $todo += 'deploy.repofiles.conf 없음(또는 빔) — 저장소 배포본이 하나도 안 깔린다'
}
foreach ($bootFile in $repoFiles) {
    $bootSrc = Join-Path $src $bootFile
    if (-not (Test-Path $bootSrc)) { continue }
    foreach ($repoRoot in $globalRuleTargets) {
        if (-not (Test-Path $repoRoot)) { continue }
        # Repo 를 달아 둔다 — 실행 단계가 **그 저장소의 당김 판정을 읽을** 근거다
        # (당김은 계획 앞에서 이미 돌았다 · 결정 0078). 못 당긴 저장소에는 안 민다.
        # 홈 대상에는 안 단다: ~/.claude 는 git 밖이라 당길 것도 더러워질 것도 없다.
        $targets += @{ From = $bootSrc; To = Join-Path $repoRoot $bootFile; Repo = $repoRoot }
    }
}

# ADR 색인 생성기는 저장소로 안 나른다(결정 0064) — 찾는 자(`claude-config-path.sh`)가 홈 스킬 ·
# 붙은 claude-config 의 스킬로 찾는다. 사본은 「claude-config 없이 연 리모트에서도 색인 검사가 서야
# 한다」가 까닭이었는데, 리모트는 늘 claude-config 를 붙인다(0061). 남은 옛 사본은 사본 대조가 문다.

# 영역 룰: rules.global/*.md -> ~/.claude/rules/ 한 자리
# **전역 룰은 홈에만 깐다** (docs/decisions/0014). 제품은 같은 이름을 두 층에서 읽는다 —
# `~/.claude/rules/` 와 `<저장소>/.claude/rules/`. 범위를 정하는 것은 이름이 아니라 층이라,
# 전역 룰을 저장소에 깔면 그 자리에서도 로드돼 한 세션에 두 벌 실린다. 저장소의 `rules/` 는
# **그 저장소 자신의 룰** 자리로 비워 둔다.
# 진본 폴더 이름만 `rules.global/` 이다 — 이 저장소를 세션에 붙였을 때 진본이 로드되지 않게
# (docs/decisions/0002 와 같은 결). 그 이름은 claude-config 안에서만 뜻이 있다.
$rulesSrc = Join-Path $src '.claude\rules.global'
if (Test-Path $rulesSrc) {
    foreach ($f in (Get-ChildItem $rulesSrc -Filter *.md)) {
        $targets += @{ From = $f.FullName; To = Join-Path $dst "rules\$($f.Name)" }
    }
}

# 제작자 세트를 받을 도구 — 사용자 환경변수 `PAISETUP_PERSONAL`(배포본 설치기의 제작자 칸이 심는다 · docs/decisions/0099)
# ⚠ **Claude 쪽은 이 값을 안 탄다** — Claude 홈에 규범 · 룰 · 스킬을 미는 것이 이 저장소의 본업이라 늘 민다.
#   Codex · agy 쪽만 이 값을 따른다 — 사람마다 Codex · agy 는 규범 없이 가볍게 쓸 수 있게.
# ⚠ **값이 없으면 있는 도구 다** — 그 설치기를 아직 안 돌린 PC 가 지금까지처럼 받는다. `none` 은 아무 도구도 아니다.
$personalRaw = $env:PAISETUP_PERSONAL
if (-not $personalRaw) { try { $personalRaw = [Environment]::GetEnvironmentVariable('PAISETUP_PERSONAL', 'User') } catch { } }
$personalSet = if ($personalRaw) { @($personalRaw -split '[,\s]+' | Where-Object { $_ }) } else { $null }
function Test-PersonalFor([string]$Tool) { ($null -eq $personalSet) -or ($personalSet -contains $Tool) }

# agy(Antigravity CLI) 설정: .gemini.global/* -> ~/.gemini/config/ (docs/decisions/0083 · 0099)
# 셋 다 **가리키는 파일**이다 — 규범은 include 한 줄, 룰은 아래 중립 자리(`~/.paisetup/norms`)를, 스킬 목록은 agy 홈
# (`~/.gemini/config/paisetup-skills`)을 가리킨다. 그래서 진본을 옮겨 적지 않고 agy 가 Claude Code 와 같은 판을 읽는다.
# ⚠ **agy 가 없는 PC 에는 안 깐다** — `~/.gemini` 가 없으면 건너뛴다. 없는 도구의 설정 폴더를 지어
#   두면 「깔렸다」로 읽힌다.
# ⚠ **스킬 목록만 늘 민다** — 규범 · 룰을 가리키는 둘은 agy 를 제작자 세트 도구로 골랐을 때만이다(위 값).
$geminiSrc = Join-Path $src '.gemini.global'
$geminiHome = Join-Path $HOME '.gemini'
if ((Test-Path $geminiSrc) -and (Test-Path $geminiHome)) {
    foreach ($f in (Get-ChildItem $geminiSrc -File)) {
        if (($f.Name -ne 'skills.json') -and -not (Test-PersonalFor 'agy')) { continue }
        $targets += @{ From = $f.FullName; To = Join-Path $geminiHome "config\$($f.Name)" }
    }
}

# 프로젝트별 메모리: memory/<project>/*.md -> ~/.claude/projects/<슬러그>/memory/
if (Test-Path $memSrc) {
    foreach ($proj in (Get-ChildItem $memSrc -Directory)) {
        $memDsts = Get-ProjectMemDst $proj.Name
        if ($memDsts.Count -eq 0) {
            # 조용히 넘어가지 않는다 — 배포된 줄 알고 있으면 어긋난 것을 나중에야 안다
            $todo += "memory/$($proj.Name)/ 배포 안 됨 — 딸린 폴더가 이 PC 에 없다(personal.conf 의 REPOS · ROOT 로 짓는다 · 결정 0072)"
            continue
        }
        foreach ($f in (Get-ChildItem $proj.FullName -Filter *.md)) {
            foreach ($d in $memDsts) {
                $targets += @{ From = $f.FullName; To = Join-Path $d $f.Name }
            }
        }
    }
}

# 이 저장소에서만 쓰는 스킬 — 홈으로 안 민다. **목록의 진본은 선언이고, 재는 자도 같은 줄을
# 본다**(`scripts/check-global-copies.sh`). 손사본 둘로 두면 한쪽만 고쳐지고, 그러면 재는 자가
# 빠진 자산을 안 재면서 초록을 낸다 (`docs/decisions/0021`).
# ⚠ **이 저장소는 역할이 둘이다** — 전역 자산의 진본이면서 공개 배포본을 뽑는 자다(0035).
#   뽑기 절차를 든 스킬은 다른 프로젝트를 여는 세션마다 따라붙을 것이 아니다. 도구 선언은
#   이미 둘로 갈려 있었는데(`tools.global.conf` ↔ `tools.conf`) 스킬만 한 벌이었다.
$localSkillsConf = Join-Path $src 'deploy.skills.local.conf'
$localSkills = @()
if (Test-Path $localSkillsConf) {
    $localSkills = @(Get-Content $localSkillsConf -Encoding UTF8 |
        ForEach-Object { ($_ -replace '#.*$', '').Trim() } |
        Where-Object   { $_ })
}

# 스킬: .claude/skills/** -> ~/.claude/skills/**
# 폴더를 통째로 미러링한다. SKILL.md만 집어오지 않는 것은 스킬이 references·scripts 같은
# 딸린 파일을 갖기 때문이다. 목록을 여기 적지 않으므로 스킬이 새로 생겨도 이 파일은 그대로 둔다.
# ⚠ **빠지는 것은 홈으로 미는 것뿐이다** — 위 선언이 든 스킬도 이 저장소를 붙인 세션에서는
#   `.claude/skills/` 에서 그대로 로드된다. 「홈에 안 깐다」와 「안 쓴다」는 다른 명제다.
$skillSrc = Join-Path $src '.claude\skills'
if (Test-Path $skillSrc) {
    # ⚠ **파이썬이 남긴 캐시는 안 민다** — 까닭은 아래 씨앗 칸의 같은 자리가 든다. 스킬도
    #   `scripts/` 를 들 수 있어 같은 부산물이 난다. 재는 자(`scripts/check-global-copies.sh`
    #   의 `DIFF_SKIP`)는 이미 그 이름을 빼므로, 여기만 안 빼면 **재는 자와 뿌리는 자가 다른
    #   것을 세어** 홈이 최신인 날에도 캐시 하나로 「어긋남」이 난다 — 고칠 것이 없는 빨강이다.
    foreach ($f in (Get-ChildItem $skillSrc -Recurse -File |
                    Where-Object { $_.FullName -notmatch '\\__pycache__\\' })) {
        $rel = $f.FullName.Substring($skillSrc.Length + 1)
        if ($localSkills -contains ($rel -split '\\')[0]) { continue }
        $targets += @{ From = $f.FullName; To = Join-Path $dst "skills\$rel" }
    }
}

# Codex · agy 홈: 스킬 · Codex 규범 블록(~/.codex/AGENTS.md) (docs/decisions/0099)
# 도구마다 제 스킬 홈을 든다 — Codex 는 `~/.agents/skills`(Codex 가 스스로 읽는 자리), agy 는 `~/.gemini/config/paisetup-skills`
# (agy 스킬 목록 — 위 `.gemini.global/skills.json` — 이 그 자리만 연다). Claude 홈과 같은 묶음을 그 홈들에도 민다.
# ⚠ **그 도구가 없는 PC 에는 그 홈을 안 깐다** — `~/.codex` · `~/.gemini` 가 없으면 건너뛴다(위 agy 와 같은 까닭).
# ⚠ **맡기기 러너는 받는 쪽 홈에 안 간다** — 러너마다 받는 쪽은 `deploy.skills.targets.conf` 가 든다. 받는 쪽 홈에 서면
#   그 도구가 제게 맡기는 길을 든다(0097). 홈을 같이 쓰면 이 갈림을 못 하므로 홈을 도구마다 둔다.
# ⚠ **규범은 옮겨 쓰지만 손사본이 아니다** — Codex 의 AGENTS.md 는 다른 파일을 끌어오지 못해, 블록 짓는 자
#   (`.claude/hooks/codex-norms.py`)가 진본에서 매번 다시 짓는다. 사람이 그 파일에 쓴 글은 표지 밖이라 그대로다.
#   지은 결과를 임시 파일로 받아 여느 배포 대상처럼 민다 — 바뀌었을 때만 백업과 함께 덮는다. agy 규범은 위 설정 셋의
#   include 한 줄이 든다.
# ⚠ 홈에서 걷는 손(-Prune)은 Claude 홈만 본다.
$codexHome = Join-Path $HOME '.codex'
$runnerTarget = @{}
$targetsConf = Join-Path $src 'deploy.skills.targets.conf'
if (Test-Path $targetsConf) {
    foreach ($ln in (Get-Content $targetsConf -Encoding UTF8)) {
        $parts = @((($ln -replace '#.*$', '').Trim()) -split '\s+' | Where-Object { $_ })
        if ($parts.Count -eq 2) { $runnerTarget[$parts[0]] = $parts[1] }
    }
}
foreach ($agentHome in @(
        @{ Tool = 'codex'; Root = $codexHome;  Dst = Join-Path $HOME '.agents\skills' }
        @{ Tool = 'agy';   Root = $geminiHome; Dst = Join-Path $geminiHome 'config\paisetup-skills' })) {
    if (-not (Test-Path $agentHome.Root) -or -not (Test-PersonalFor $agentHome.Tool)) { continue }
    foreach ($bundle in @($skillSrc, (Join-Path $src '.agents\skills'))) {
        if (-not (Test-Path $bundle)) { continue }
        foreach ($f in (Get-ChildItem $bundle -Recurse -File |
                        Where-Object { $_.FullName -notmatch '\\__pycache__\\' })) {
            $rel = $f.FullName.Substring($bundle.Length + 1)
            $name = ($rel -split '\\')[0]
            if (($localSkills -contains $name) -or ($runnerTarget[$name] -eq $agentHome.Tool)) { continue }
            $targets += @{ From = $f.FullName; To = Join-Path $agentHome.Dst $rel }
        }
    }
}
# 규범 · 룰의 중립 자리 — Codex 의 룰 줄과 agy 설정 셋이 가리킨다(docs/decisions/0099). Claude 홈(`~/.claude`)은 Claude 가
# 스스로 싣는 자리라 다른 도구를 위해 거기 두면 Claude 에도 실린다 — 그래서 따로 둔다. 이름이 `CLAUDE.md` 가 아닌 것도 같은
# 까닭이다(Claude 는 그 이름을 찾아 싣는다).
if (((Test-Path $codexHome) -and (Test-PersonalFor 'codex')) -or ((Test-Path $geminiHome) -and (Test-PersonalFor 'agy'))) {
    $neutralNorms = Join-Path $HOME '.paisetup\norms'
    $targets += @{ From = $ruleSrc; To = Join-Path $neutralNorms 'norms.md' }
    if (Test-Path $rulesSrc) {
        foreach ($f in (Get-ChildItem $rulesSrc -Filter *.md)) {
            $targets += @{ From = $f.FullName; To = Join-Path $neutralNorms "rules\$($f.Name)" }
        }
    }
}
if (Test-Path $codexHome) {
    $codexPy = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $codexPy) {
        $todo += 'Codex 규범 블록 — python 이 없어 ~/.codex/AGENTS.md 를 못 지었다'
    } else {
        $codexNormsPlan = Join-Path ([IO.Path]::GetTempPath()) 'deploy-codex-agents.md'
        # 고르지 않았으면 블록을 걷는 판을 짓는다 — 블록이 없으면 지금 파일과 같아 배포가 안 민다
        $codexNormsArgs = if (Test-PersonalFor 'codex') {
            @('--norms', $ruleSrc, '--rules', (Join-Path $src '.claude\rules.global'), '--rules-home', '~/.paisetup/norms/rules')
        } else { @('--remove') }
        $codexNormsOut = @(& $codexPy.Source -X utf8 (Join-Path $src '.claude\hooks\codex-norms.py') @codexNormsArgs `
            --target (Join-Path $codexHome 'AGENTS.md') --out $codexNormsPlan)
        if ($LASTEXITCODE -eq 0) {
            $targets += @{ From = $codexNormsPlan; To = Join-Path $codexHome 'AGENTS.md' }
        } else {
            $todo += "Codex 규범 블록 — 못 지었다: $($codexNormsOut | Select-Object -Last 1)"
        }
    }
}

# 사내 환경 문서와 씨앗 둘: posco/** · seeds/gateway/** · seeds/check/** -> ~/.claude/ 아래 같은 이름
# ⚠ **왜 홈에도 두나** — 이 둘의 진본은 저장소이고, 스킬·형제 저장소 문서가 그 좌표를
#   가리킨다. 그런데 설치본만 받은 사람에게는 저장소가 없어 그 좌표가 아예 없다. 그래서
#   설치(`install.ps1` 7 칸)가 홈에 깔고, 이 자리가 그 사본을 진본과 맞춘다 —
#   깔아만 두고 갱신을 안 하면 사본이 조용히 낡는다.
#   목록은 선언이 든다 — deploy.seeds.conf(뿌리는 자 둘 · 재는 자 하나가 같은 줄을 읽는다). 폴더 안의
#   파일이 늘어도 이 파일은 그대로다. `seeds\config-repo` 를 일부러 안 미는 까닭도 그 선언의 머리말이 든다.
$seedsConf = Join-Path $src 'deploy.seeds.conf'
$seedDirs = @()
if (Test-Path $seedsConf) {
    $seedDirs = @(Get-Content $seedsConf -Encoding UTF8 |
        ForEach-Object { ($_ -replace '#.*$', '').Trim() } |
        Where-Object   { $_ } |
        ForEach-Object { $_ -replace '/', '\' })
}
if ($seedDirs.Count -eq 0) {
    $todo += 'deploy.seeds.conf 없음(또는 빔) — 홈으로 폴더째 미는 씨앗·사내 환경 문서가 하나도 안 깔린다'
}
foreach ($sd in $seedDirs) {
    $aSrc = Join-Path $src $sd
    if (-not (Test-Path $aSrc)) { continue }
    # ⚠ **파이썬이 남긴 캐시는 안 민다.** 씨앗의 검사를 돌리면 `__pycache__\` 가 생기는데 git 은
    #   무시해도 이 복사는 모른다 — 실측 2026-09-12: 프로브를 돌린 직후 배포가 `.pyc` 일곱을 홈에
    #   깔았다. 그것은 자산이 아니라 그 PC 의 부산물이다.
    foreach ($f in (Get-ChildItem $aSrc -Recurse -File | Where-Object { $_.FullName -notmatch '\\__pycache__\\' })) {
        $rel = $f.FullName.Substring($aSrc.Length + 1)
        $targets += @{ From = $f.FullName; To = Join-Path $dst "$sd\$rel" }
    }
}

foreach ($t in $targets) {
    if ((Test-Path $t.To) -and ((Get-FileHash $t.From).Hash -eq (Get-FileHash $t.To).Hash)) {
        $same += "= 동일  $($t.To)"
    } else {
        $verb = if (Test-Path $t.To) { '덮어씀' } else { '새로 만듦' }
        $plan += @{ Kind = 'copy'; From = $t.From; To = $t.To; Repo = $t.Repo; Text = "+ 배포  $($t.To)  ($verb)" }
    }
}

# ── 씨앗의 판 줄 — 홈 사본이 **어느 판에서 왔나**를 그 자리에 남긴다 ────────────
# ⚠ **왜 한 줄이 더 필요한가.** 홈 사본을 진본으로 믿고 재는 자가 있다
#   (`seeds/check/_check/borrowed_check.py` 의 `_stamp()`). 그런데 홈 뿌리는 git 나무가
#   아니라 판을 물을 데가 없어, 옛 판은 **오늘 날짜**를 냈다 — 그래서 낡은 홈과 견준 초록이
#   최신처럼 읽혔다 (실측 2026-09-13: 홈 씨앗이 나무와 12 자리 갈려 있었다).
#   파일 이름은 그쪽 `VERSION_FILE` 이 들고, 쓰는 자는 여기와 세션 훅 `deploy_home_norms`
#   의 씨앗 칸 둘이다 — 한 낱말이라 선언 파일로 안 뽑고 곁말로 서로를 가리킨다.
# ⚠ **자리가 위 씨앗 칸이 아니라 여기인 까닭** — 계획은 순서대로 돈다. 저 위에 두면 이 줄이
#   **씨앗 복사보다 먼저** 서서, 복사가 지거나 건너뛰어도 「그 판이 깔렸다」고 말한다.
# ⚠ **판이 그대로면 안 쓴다.** 날짜 칸은 「이 판이 홈에 깔린 날」이고 돌린 날이 아니다 —
#   매번 덮으면 그 날짜가 늘 오늘이라 낡음을 아무것도 말하지 않는다.
# ⚠ **재는 자는 이 줄을 안 본다** — `scripts/check-global-copies.sh` 도 세션 훅도 견주는
#   자리가 `seeds/<이름>/` 안이고 이 줄은 뿌리 `seeds/` 에 산다. 그래서 그 둘에 제외를 따로
#   안 든다 — 안 잴 것을 빼는 선언은 없는 것을 가리키는 손사본이 된다.
$stampFile = Join-Path $dst 'seeds\.version'
$stampRev  = if (Get-Command git -ErrorAction SilentlyContinue) {
                 try { (& git -C $src rev-parse --short HEAD 2>$null) } catch { $null }   # 버리는 것도 방패가 아니라 잡는다(아래 「리다이렉트가 곧 위험이다」)
             } else { $null }
if ($stampRev) {
    $stampRev = ([string]$stampRev).Trim()
    $stampOld = if (Test-Path $stampFile) {
                    [string](Get-Content $stampFile -TotalCount 1 -Encoding UTF8)
                } else { '' }
    if ((($stampOld -split '\s+')[0]) -eq $stampRev) {
        $same += "= 동일  $stampFile  ($stampOld)"
    } else {
        $stampLine = "$stampRev $(Get-Date -Format 'yyyy-MM-dd')"
        $plan += @{
            Kind = 'stamp'; Path = $stampFile; Line = $stampLine
            Text = "+ 판 줄  $stampFile  ($stampLine)"
        }
    }
}

# --- MCP 등록 ---
# mcp-servers.json은 기록일 뿐이라 복사한다고 등록되지 않는다. CLI로 등록해야 한다.
#
# 등록 여부는 **주인에게 묻는다** — `claude mcp get <이름>` 이 exit 0/1 로 답한다.
# ⚠ 예전에는 ~/.claude.json 을 통짜로 파싱해 `.mcpServers` 를 읽었다. 그 파일은 우리 것이
#   아니고, deploy 가 볼 이유 없는 구역(projects · 세션 지표 · 신뢰 플래그)을 같이 든다.
#   그런데 ConvertFrom-Json 은 **대소문자 무시** 사전을 만들어, JSON 이 형제로 허용하는
#   `C:/x` 와 `c:/x` 를 못 담고 던진다. 실제로 projects 의 중복 하나가 배포 전체를 그
#   자리에서 넘어뜨렸다 (이슈 #13) — 질문은 키 하나짜리인데 **폭발 반경이 파일 전체**였다.
#   물을 자리를 바꾸면 그 반경이 사라진다: .claude.json 이 아무리 지저분해도 안 닿는다.
# ⚠ 대소문자도 같이 바로잡힌다. `-contains` 는 대소문자를 무시해서, .claude.json 에
#   `Github` 가 있고 여기가 `github` 을 원하면 「등록됨」으로 보고하고 **건너뛰었다** —
#   Claude Code 가 읽는 키는 `github` 이라 실제로는 없는데도. 잘못된 이름이 눌러앉고
#   원하는 서버는 영영 안 붙는데 매번 초록이었다. `mcp get` 은 가린다 (실측: `GitHub` → exit 1).
# ⚠ `claude mcp list` 를 안 쓰는 까닭은 그대로다 — 서버 뒤에 진단 블록을 함께 뱉고 그
#   줄들도 `이름: 값` 꼴이라, 산문을 훑으면 경고 줄이 서버 이름으로 잡힌다. --json 도 없다.
#
# ── 자리 게이트 — 선언이 서버마다 `only` 로 자리를 걸 수 있다 (결정 0079) ──────────────
# 어느 자리에서는 못 쓰는 서버가 있다(사내 웹 필터가 그 엔드포인트만 막는 자리). 그런 이름을
# 자리와 무관하게 등록하면 **매 세션 연결 실패 줄이 떠 진짜 고장과 섞인다.**
# ⚠ **두 명제를 가른다 — 「이 자리에서 안 쓴다」와 「선언에서 없어졌다」.** 자리 때문에 빠진
#   이름도 `$wantMcp` 에는 그대로 담는다. 안 담으면 아래 제거 후보 판정이 그것을 「선언에
#   없는 것」으로 집어, 자리를 옮기는 PC 에서 **등록·해제가 매 회차 오간다.**
# ⚠ **자리는 이 스크립트가 재지 않는다 — 훅 몸통에 묻는다**(`--site`). 재는 자가 둘이면
#   고칠 때 한쪽만 고쳐진 채 조용히 갈린다. 묻는 꼴은 `--needs-install` 과 같다(0061).
# ⚠ **지우는 손은 「저 자리임을 보인 답」 위에서만 선다.** 훅은 자리와 함께 **어느 자로
#   얻었나**를 낸다(`probe` · `path` · `default` · `default-after-probe`). 바닥값은 아무 자도
#   안 답해서 **남은** 답이라, 그것으로 걷으면 **안 재고 지우는 꼴**이다 — 부팅 직후 망이
#   아직 안 선 사내 PC 가 정확히 그 자리다: 프로브가 놓쳐 바닥값(사외)이 서고, 등록이 섰다가
#   다음 회차에 걷히며 **매 부팅 등록·해제가 오간다.** 그래서 바닥값이 프로브 선언을 두고
#   선 것이면(`default-after-probe`) 잠깐 뒤 한 번 다시 묻고, 그래도 바닥값이면 **받아들이되
#   걷지는 않는다.**
# ⚠ **자리를 아예 못 쟀으면 게이트를 안 건다 — 등록은 예전대로 한다.** 이 칸이 막는 것은
#   **아는 자리**이고, 모르는 자리에서 거두는 쪽으로 기울면 설정 저장소 씨앗만 받은 PC
#   (`secrets.d/` 가 없다)에서 멀쩡한 서버가 사라진다. 다만 **이미 등록된 것을 걷지는 않는다.**
$mcpFile  = Join-Path $src 'mcp-servers.json'
$wantMcp  = @()
if (Test-Path $mcpFile) {
    # 종료 코드만 본다. 출력은 버린다 — 산문을 읽기 시작하면 위의 까닭으로 되돌아간다.
    # bash 를 거치는 것은 이 파일의 확립된 방식이다: npm shim 이 제 자리를 Git 설치 폴더
    # 기준으로 잘못 풀어, PowerShell 에서 곧장 부르면 자리에 따라 깨진다.
    #
    # ⚠ **「못 물었다」와 「등록 안 됨」을 섞지 않는다.** claude 에 안 닿을 때의 127 을
    #   「없다」로 읽으면 이미 등록된 것을 다시 등록하러 들고, 실패하면 빨갛게 보고한다.
    #   맨바닥 PC 의 첫 설치가 바로 그 자리다 — npm 전역 폴더가 PATH 에 없어 배포가
    #   띄운 bash 가 claude 를 못 찾았다 (install.ps1 의 PATH 재배선이 그 짝이다).
    #   「깔린 것과 닿는 것은 다른 명제」가 여기서도 선다.
    $canAskMcp = $false
    if ($bash) {
        $probe = Join-Path $env:TEMP 'deploy-mcp-probe.sh'
        [System.IO.File]::WriteAllText($probe, "command -v claude >/dev/null 2>&1`n", (New-Object System.Text.UTF8Encoding($false)))
        & $bash $probe *> $null
        $canAskMcp = ($LASTEXITCODE -eq 0)
        Remove-Item $probe -Force -ErrorAction SilentlyContinue
    }

    function Test-McpRegistered($name) {
        if (-not $canAskMcp) { return $null }   # 물을 자가 없다. 「없다」와 구별한다
        $probe = Join-Path $env:TEMP "deploy-mcpget-$name.sh"
        # ⚠ **리다이렉트는 스크립트 안에 둔다.** `claude mcp get` 은 등록 안 된 이름을
        #   **stderr 로** 답한다(그것이 정상 갈래다). 그런데 PowerShell 5.1 은 네이티브의
        #   stderr 를 NativeCommandError 로 감싸고, 이 파일 머리의 `ErrorActionPreference = 'Stop'`
        #   아래에서 그것은 **종료 오류**다 — `*> $null` 은 그걸 못 막는다.
        #   그래서 배포가 **첫 MCP 조회에서 통째로 죽었고**, 바로 아래 127/0 갈래는
        #   한 번도 안 돌았다 (실측 2026-09-07 · 맨바닥 VDI 첫 설치에서
        #   저장소 배포·홈 규범·저장소 설치가 전부 안 선 채 「완료」가 찍혔다).
        #   위 `$canAskMcp` 프로브가 이미 쓰는 꼴이다 — 두 프로브를 같은 꼴로 둔다.
        [System.IO.File]::WriteAllText($probe, "claude mcp get $name >/dev/null 2>&1`n", (New-Object System.Text.UTF8Encoding($false)))
        & $bash $probe *> $null
        $code = $LASTEXITCODE
        Remove-Item $probe -Force -ErrorAction SilentlyContinue
        if ($code -eq 127) { return $null }     # 셸이 claude 를 못 찾았다 — 답이 아니다
        return ($code -eq 0)
    }

    # `only` 는 **선언의 칸이지 서버 설정이 아니다** — 등록에 넘기는 JSON 에서 뺀다. 넘기면
    # 모르는 키가 등록부에 눌러앉고, 그것을 쓰는 자는 아무도 없다.
    # ⚠ 키가 없는 서버에도 그냥 건다 — 빼기 전과 **바이트가 같다**(실측). 갈래를 하나 줄인다.
    function Get-McpDef($def) { $def | Select-Object -Property * -ExcludeProperty only }
    # **키가 없는 것과 비어 있는 것을 가른다** — 없으면 `$null`(안 거는 서버), 있으면 글자다.
    # 빈 글자를 「안 건다」로 접으면 `"only": ""` 가 **조용히 모든 자리에서 등록된다.**
    function Get-McpOnly($def) {
        $hit = @($def.PSObject.Properties | Where-Object { $_.Name -eq 'only' })
        if ($hit.Count -eq 0) { return $null }
        return ("$($hit[0].Value)").Trim()
    }
    # 쉼표로 가르고 칸마다 공백을 걷고 빈 칸은 버린다 — `"home, outside"` 도 `"home,outside"` 와
    # 같은 뜻이어야 한다. 글자 통째로 견주면 공백 하나가 그 서버를 **모든 자리에서** 뺀다.
    function Get-McpOnlyTokens($raw) {
        if ($null -eq $raw) { return @() }
        return @(($raw -split ',') | ForEach-Object { "$_".Trim() } | Where-Object { $_ })
    }

    $mcpProps = @((Get-Content $mcpFile -Raw | ConvertFrom-Json).mcpServers.PSObject.Properties)

    # 자리 **이름 목록**은 파일 이름이 든다 — 선언의 오타를 잡는 자다. ⚠ 이것은 두 번째 자리
    # 판별기가 아니다: 어느 자리인가를 **고르는** 자는 여전히 훅 하나이고, 여기서 읽는 것은
    # 「어떤 이름이 선언돼 있나」라는 다른 명제다(둘 다 같은 폴더를 원본으로 본다).
    $mcpSiteNames = @(Get-ChildItem (Join-Path $src 'secrets.d') -Filter *.env -File -ErrorAction SilentlyContinue |
                      ForEach-Object { [System.IO.Path]::GetFileNameWithoutExtension($_.Name) })

    # 바닥값으로 선 자리를 받아들이기 전에 다시 묻는 자 — 값에 이름을 준다(박으면 화면에 찍는
    # 초와 기다리는 초가 갈린다). 프로브는 안 닿을 때 3초를 무니 한 번 더 묻는 값이 그만큼이다.
    $McpSiteRetryPauseSec = 5   # 다시 묻기 전에 기다리는 시간 — 부팅 직후 망이 서는 틈을 준다
    $McpSiteRetryAttempts = 1   # 바닥값을 받아들이기 전에 다시 묻는 횟수

    function Get-McpSiteAnswer {
        # @{ Site; How; Why } — `Why` 가 서면 못 쟀다는 뜻이다
        if (-not $bash) { return @{ Site = ''; How = ''; Why = 'Git Bash 를 못 찾았다' } }
        # ⚠ **`2>&1` 을 안 붙인다** — 5.1 은 네이티브의 stderr 한 줄을 종료 오류로 승격한다
        #   (까닭은 `Sync-Repos` 머리에 있다). 답도 사유도 훅이 stdout 한 줄로 낸다.
        $body = Join-Path $src '.claude\hooks\session-start-body.sh'
        $env:SESSION_START_REPO = $src -replace '\\', '/'
        try { $out = & $bash ($body -replace '\\', '/') --site; $rc = $LASTEXITCODE }
        finally { Remove-Item Env:SESSION_START_REPO -ErrorAction SilentlyContinue }
        $line = @($out | Where-Object { "$_".Trim() }) | Select-Object -Last 1
        if ($rc -ne 0 -or -not $line) {
            $why = if ($line) { "$line".Trim() } else { "훅이 사유를 안 냈다 (exit $rc)" }
            return @{ Site = ''; How = ''; Why = $why }
        }
        $f = @(("$line".Trim() -split '\s+') | Where-Object { $_ })
        if ($f.Count -lt 2) {
            return @{ Site = ''; How = ''; Why = "훅이 자리와 길을 두 칸으로 안 냈다: $line" }
        }
        return @{ Site = $f[0]; How = $f[1]; Why = '' }
    }

    # 자리는 **거는 이름이 하나라도 있을 때만** 묻는다 — `_site_of` 는 안 닿는 자리에서 TCP
    # 프로브에 3초를 무는 자라, 아무도 자리를 안 거는 판에서는 그 3초가 순수한 손해다.
    # ⚠ 다시 묻는 값도 그 안에 있다 — 프로브를 선언한 자리가 없으면 훅이 `default` 를 내고
    #   아래 갈래가 아예 안 선다. 선언이 없는 PC 는 **한 초도 더 안 문다.**
    $mcpSite = ''; $mcpSiteHow = ''; $mcpSiteWhy = ''
    if (@($mcpProps | Where-Object { $null -ne (Get-McpOnly $_.Value) }).Count -gt 0) {
        $ans = Get-McpSiteAnswer
        for ($i = 0; $i -lt $McpSiteRetryAttempts -and $ans.How -eq 'default-after-probe'; $i++) {
            Write-Host "· 자리가 바닥값으로 섰다 — 프로브를 선언한 자리가 있어 $McpSiteRetryPauseSec 초 뒤 한 번 다시 묻는다 (부팅 직후면 망이 아직 안 섰다)" -ForegroundColor DarkGray
            Start-Sleep -Seconds $McpSiteRetryPauseSec
            $again = Get-McpSiteAnswer
            # 다시 물어 **못 쟀다**로 바뀌면 첫 답을 들고 간다 — 다시 묻기가 답을 깎지 않는다.
            if ($again.Why) { break }
            $ans = $again
        }
        $mcpSite = $ans.Site; $mcpSiteHow = $ans.How; $mcpSiteWhy = $ans.Why
    }
    # 「저 자리임을 보인 답」인가 — 지우는 손은 이것이 참일 때만 선다.
    $mcpSiteFirm = ($mcpSiteHow -ceq 'probe' -or $mcpSiteHow -ceq 'path')

    foreach ($p in $mcpProps) {
        # **선언에 있다는 사실은 자리와 무관하다** — 아래 제거 후보 판정이 이 목록을 본다.
        $wantMcp += $p.Name
        $only   = Get-McpOnly $p.Value
        $tokens = Get-McpOnlyTokens $only
        $isReg  = Test-McpRegistered $p.Name
        # ⚠ **자리로 빠지는 이름은 매 회차 화면에 한 줄 낸다.** `$same` 에 넣으면 개수에만
        #   잡혀 `-ShowUnchanged` 없이는 안 보이고, 「안 심었다」와 「아예 안 쟀다」가 같아진다.
        if ($null -ne $only) {
            if (-not $mcpSite) {
                # **게이트를 안 건다 — 등록은 예전대로.** 이 칸이 막는 것은 아는 자리다.
                # ⚠ **남은 수동 작업에는 안 올린다.** 자리 파일이 없는 PC 에서는 영영 뜨는 줄이
                #   되고, 영영 뜨는 할 일은 할 일 목록을 아무것도 안 말하는 목록으로 만든다.
                #   화면 한 줄은 매 회차 서므로 조용한 것은 아니다.
                # 사유는 훅이 낸 글자를 그대로 싣는다 — 여기서 다시 말하면 같은 말이 두 번 선다.
                Write-Host "? MCP $($p.Name) — 게이트를 안 건다 ($mcpSiteWhy) · 이 이름은 $only 에서만 산다. 없으면 등록하고, 있으면 그대로 둔다" -ForegroundColor Yellow
            } elseif ($tokens.Count -eq 0 -or @($tokens | Where-Object { $mcpSiteNames -cnotcontains $_ }).Count -gt 0) {
                # **선언 오류다 — 이번 회차에 이 이름은 안 건드린다.** 모르는 자리 이름은 어느
                # 자리와도 안 맞아, 고치는 대신 따르면 그 서버가 **모든 자리에서** 빠진다.
                # 걷지도 심지도 않는 까닭 — 망가진 선언을 근거로 지우면 되돌릴 사람이 없다.
                $bogus = @($tokens | Where-Object { $mcpSiteNames -cnotcontains $_ })
                $what = if ($tokens.Count -eq 0) { '자리 이름이 하나도 없다' } else { "모르는 자리: $($bogus -join ' · ')" }
                Write-Host "! MCP $($p.Name) — 선언의 only 가 틀렸다 ($what · 있는 자리: $($mcpSiteNames -join ' · ')). 이번 회차에 안 건드린다" -ForegroundColor Red
                $todo += "mcp-servers.json 의 $($p.Name) 의 only 를 고친다 ($what · 있는 자리: $($mcpSiteNames -join ' · ')) — 고칠 때까지 이 서버는 등록·해제를 안 한다"
                continue
            } elseif ($tokens -cnotcontains $mcpSite) {
                if ($null -eq $isReg) {
                    Write-Host "? MCP $($p.Name) — 자리가 $mcpSite 라 안 심는 이름인데 등록 여부를 못 물었다. 해제도 안 한다" -ForegroundColor Yellow
                    $todo += "MCP $($p.Name) 등록 여부를 못 물었다 (claude 에 안 닿는다) — 자리가 $mcpSite 라 걷어야 한다:  claude mcp remove $($p.Name) -s user"
                } elseif ($isReg -and -not $mcpSiteFirm) {
                    # **바닥값으로는 안 걷는다.** 「아무 자도 안 답했다」를 근거로 지우면 안 재고
                    # 지우는 꼴이고, 그 길이 곧 매 부팅 등록·해제가 오가는 떨림이다.
                    Write-Host "? MCP $($p.Name) — 자리가 바닥값으로 선 $mcpSite 라 안 걷는다 ($mcpSiteHow · 이 이름은 $only 에서만 산다). 걷는 일은 프로브·경로로 선 답에서만 한다" -ForegroundColor Yellow
                } elseif ($isReg) {
                    # **기본 실행에서 걷는다 — `-Prune` 이 아니다.** 저 깃발의 뜻은 「원본에 없는
                    # 것을 치운다」인데 이 이름은 원본에 있다. 선언이 시킨 상태를 맞추는 일이라
                    # 계획에 선다 (결정 0079).
                    $plan += @{
                        Kind = 'mcpremove'; Name = $p.Name
                        Text = "- 해제  MCP $($p.Name)  (자리가 $mcpSite · 이 이름은 $only 에서만 산다)"
                    }
                } else {
                    Write-Host "· 안 심는다  MCP $($p.Name)  (자리가 $mcpSite · 이 이름은 $only 에서만 산다)" -ForegroundColor DarkGray
                }
                continue
            }
        }
        if ($null -eq $isReg) {
            # 못 물었으면 「등록됐다」고도 「아니다」고도 하지 않는다. 침묵하지도 않는다.
            $todo += "MCP $($p.Name) 등록 여부를 못 물었다 (claude 에 안 닿는다 — Git Bash 나 npm 전역 PATH 를 본다) — 확인:  claude mcp get $($p.Name)"
        } elseif ($isReg) {
            $same += "= 등록됨  MCP $($p.Name)"
        } else {
            $plan += @{
                Kind = 'mcp'; Name = $p.Name
                Json = (Get-McpDef $p.Value | ConvertTo-Json -Compress -Depth 10)
                Text = "+ 등록  MCP $($p.Name)"
            }
        }
    }

    # 제거 후보: 등록돼 있는데 mcp-servers.json에 없는 것.
    # ⚠ 이것만은 **열거**가 필요한데 `claude mcp list` 에 --json 이 없어 파일을 읽는다.
    #   그러니 여기만 울타리를 친다 — **없어도 되는 답 하나 때문에 배포 전체가 죽지 않게.**
    #   이슈 #13 이 정확히 그렇게 났다: 못 읽으면 이 칸만 접고 나머지는 그대로 간다.
    # ⚠ 대조는 `-ccontains` 다(대소문자 구분). `-contains` 로 재면 위에서 `github` 을 새로
    #   등록해 놓고 남은 `Github` 는 「원하는 것」으로 잡혀 영영 안 걷힌다.
    # ⚠ **자리가 뺀 이름은 여기 안 걸린다** — `$wantMcp` 가 자리와 무관하게 선언의 이름을 다
    #   담기 때문이다(위 §자리 게이트). 그 이름을 걷는 손은 위 계획의 `mcpremove` 이고, 사유도
    #   「선언에 없음」이 아니라 「이 자리에서 안 산다」로 갈려 찍힌다 (결정 0079).
    $claudeJson = Join-Path $HOME '.claude.json'
    if (Test-Path $claudeJson) {
        try {
            # ⚠ **여기만 `ConvertFrom-Json` 이 아니다.** PS 5.1 의 그 파서는 대소문자 무시
            #   사전을 만들어, JSON 이 형제로 허용하는 `C:/x` 와 `c:/x` 를 못 담고 던진다.
            #   이 파일은 우리 것이 아니라 상류(Claude Code)가 `projects` 에 두 벌 키를 쌓고,
            #   그러면 위 울타리가 매 배포마다 「못 쟀다」로 접혀 제거 후보를 **영영 안 잰다**
            #   (이슈 #52 · 회사 PC 실측). 같은 PS 5.1 의 .NET 파서는 그 둘을 그대로 받는다.
            #   울타리는 그대로 둔다 — 파일이 정말 깨진 판은 여전히 있다.
            #   다른 `ConvertFrom-Json` 자리(우리 `mcp-servers.json` · gh 출력)는 안 건드린다.
            Add-Type -AssemblyName System.Web.Extensions
            $ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer
            # 기본 한도는 2,097,152 자다(실측). 지금 이 PC 의 실물은 47KB 라 안 걸리지만,
            # 이 파일은 상류가 projects 를 계속 쌓는 자리라 한도는 자라는 쪽으로 열어 둔다 —
            # 걸리는 날 나올 답이 「못 쟀다」 한 줄이라 원인이 안 보인다.
            $ser.MaxJsonLength = [int]::MaxValue
            $reg = ($ser.DeserializeObject((Get-Content $claudeJson -Raw)))['mcpServers']
            if ($reg) {
                foreach ($n in @($reg.Keys)) {
                    if ($wantMcp -ccontains $n) { continue }
                    $prunable += @{ Kind = 'mcpremove'; Name = $n; Text = "- 해제  MCP $n  (mcp-servers.json에 없음)" }
                }
            }
        } catch {
            $todo += "MCP 제거 후보를 못 쟀다 — ~/.claude.json 파싱 실패: $($_.Exception.Message.Split([char]10)[0].Trim()). 등록·배포는 영향 없다"
        }
    }
}

# --- git 훅 경로 ---
# 저장소가 .githooks/ 를 들고 있으면 core.hooksPath 를 거기로 맞춰야 훅이 실제로 돈다.
# git 이 추적하는 것은 .githooks/ 안의 파일뿐이고 .git/hooks/ 는 clone 을 안 따라오므로,
# 이 한 줄이 없는 PC 에서는 훅 파일만 있고 아무것도 안 걸린다 — 걸린 줄 알고 있으면
# 게이트가 없는 것보다 나쁘다.
#
# 대상 목록은 $globalRuleTargets 에 **배포본 저장소 하나를 더한 것**이다.
# ⚠ **두 쓰임을 여기서 가른다.** 그 목록은 위에서 개발 파일(훅 몸통·settings.json·도구 선언)을
#   복사하는 데도 쓰이는데, 배포본 저장소는 **동료에게 가는 zip 그 자체**라 거기에 개발 파일을
#   넣으면 그것이 zip 에 실려 나간다. 그러나 `core.hooksPath` 는 **설정일 뿐 파일이 아니라**
#   새어 나갈 것이 없다 — 그래서 이 자리만 넓힌다.
# ⚠ 배포본 이름을 박지 않는다 — `dist.manifest.conf` 가 이미 든다(뽑는 자·나무 재는 자와
#   같은 규약). 박으면 배포 대상이 옮겨진 날 이 자리만 낡는다.
$hookTargets = @($globalRuleTargets)
$distName = ''
$manifest = Join-Path $src 'dist.manifest.conf'
if (Test-Path $manifest) {
    $inSection = $false
    foreach ($line in (Get-Content $manifest -Encoding UTF8)) {
        $t = $line.Trim()
        # ⚠ `-like` 를 안 쓴다 — 대괄호가 와일드카드라 이스케이프가 필요하고, 그 문법을
        #   이 자리에서 못 재는 판(파워셸 없는 리눅스)에서 고쳤다. 뜻이 같고 모호하지 않은 쪽.
        if ($t.StartsWith('[') -and $t.EndsWith(']')) {
            $inSection = ($t -eq '[배포본이 서는 자리]'); continue
        }
        if (-not $inSection -or -not $t -or $t.StartsWith('#')) { continue }
        $distName = $t; break
    }
}
if ($distName) {
    # 형제 자리에서 파생한다 — 세 PC 가 다 홈 밑 `repos\` 를 본다.
    $distRoot = Join-Path (Split-Path -Parent $src) $distName
    if ((Test-Path (Join-Path $distRoot '.git')) -and ($hookTargets -notcontains $distRoot)) {
        $hookTargets += $distRoot
    }
}
foreach ($repoRoot in $hookTargets) {
    if (-not (Test-Path (Join-Path $repoRoot '.githooks'))) { continue }
    # ⚠ `2>$null` 은 방패가 아니다 (까닭은 `Sync-Repos` 머리에 있다) — 잡아서 넘긴다.
    #   값을 못 읽은 것과 값이 다른 것은 여기서 같은 값이다: 둘 다 「맞춰야 한다」로 간다.
    try { $cur = (& git -C $repoRoot config core.hooksPath 2>$null) }
    catch { $cur = $null }
    if ($cur -eq '.githooks') {
        $same += "= 설정됨  core.hooksPath  $repoRoot"
    } else {
        $plan += @{
            Kind = 'githooks'; Repo = $repoRoot
            Text = "+ 설정  core.hooksPath=.githooks  $repoRoot"
        }
    }
}

# --- 저장소 설치 ---
# 게이트가 부르는 도구(링크 검사기·commitlint·파이썬 의존성)를 깐다.
#
# 왜 여기가 그 자리인가: 이 스크립트가 `git pull` 다음에 **항상** 도는 유일한 자리다.
# 도구가 없으면 게이트는 그 검사만 건너뛰고 커밋을 통과시키므로, 새 도구가 늘어난 것을
# 아무도 모른 채 몇 달이 간다. 여기서 깔면 한쪽에서 늘린 것이 다음 배포에 따라온다.
#
# 무엇을 깔지는 이 스크립트가 모른다 — 각 저장소의 훅이 안다. 그래서 도구 이름이
# 여기 없고, 저장소가 늘어도 이 파일은 안 고친다.
#
# 계획 단계에서는 `--needs-install` 로 **묻기만** 한다(아무것도 안 바꾼다) — 답은
# 「이 저장소에 깔 게 있나」 예/아니오 하나고, 그것은 파일만 보면 난다. 깔 게 있는
# 저장소만 실행 목록에 올린다 — 다 살아 있으면 매번 승인을 묻지 않는다. **다만 물은
# 것은 초록이어도 화면에 한 줄 낸다** — 안 묻는 것과 안 재는 것은 다른 명제다(아래 ⚠).
# 진단(무엇을 쟀고 무엇이 사는가)은 **깐 저장소에서 설치 끝에 한 벌**만 난다.
#
# ⚠ **걸음이 둘로 갈렸다 — 전역은 한 번, 저장소는 저장소마다** (#43). 옛 꼴은 저장소마다
#   부른 훅이 그 안에서 전역 선언까지 다시 훑어, 프로브 비용이 저장소 수에 비례했다. 이제
#   전역형 도구(npm 전역 · 릴리스 바이너리 · winget · 브라우저)는 아래 고리 **앞에** 한 번
#   깔고, 고리 안에서는 저장소 몫(프로젝트 축 · 배선)만 부른다.
# ⚠ **차례가 값을 한다 — 그래서 여기서 바로 `$plan` 에 안 쌓는다.** 전역 걸음이 저장소 걸음
#   보다 먼저 서야 배선이 걸 물건이 이미 깔려 있다. 실행은 계획 순서대로라, 고리가 도는
#   동안 모아 두었다가 고리가 끝난 뒤 **전역 하나 + 저장소들** 차례로 붙인다.
$installSteps = @()
# ⚠ **이 저장소 자신도 설치 대상이다** — 파일 배포 대상은 아니지만(진본이라 덮을 것이 없다) 제 도구 선언과
#   배선이 있다. 옛 판은 형제만 돌아, 이 저장소의 세션 훅(auto)이 남긴 실패 기록을 **다시 까는 손이 없었다** —
#   auto 는 실패를 다시 안 깔고 알리기만 하므로 「지난 설치에 실패」가 세션마다 영영 떴다(2026-09-28 이 PC).
foreach ($repoRoot in @(@($src) + $globalRuleTargets)) {
    $boot = Join-Path $repoRoot '.claude\hooks\session-start.sh'
    if (-not (Test-Path $boot)) { continue }
    if (-not $bash) {
        $todo += "Git Bash 를 못 찾음. 직접 실행:  bash '$boot' --install"
        continue
    }
    # ⚠ **계획 단계는 진단을 안 돌린다 — 「이 저장소에 깔 게 있나」만 묻는다** (#47 ②).
    #   옛 판은 여기서 `--check` 를 불러 저장소마다 도구를 프로브했는데, 설치가 끝에
    #   **같은 판정을 한 벌 더** 낸다 — 사내 VDI 실측(PAISetup #5 · 1.11.0): 계획 5×31~57초
    #   = 200초와 설치 끝 5×45~70초 = 269초가 같은 물음의 두 벌이었다. 계획에 필요한 답은
    #   예/아니오 하나뿐이고 그것은 파일만 보면 나므로, 훅의 `--needs-install`(프로브도 망도
    #   안 탄다 · 1초 안)이 그 자리를 든다. 진단은 **깐 저장소에서 설치 끝에 한 벌**만 난다 —
    #   깐 뒤의 판정이라야 진짜라서다. 안 깐 저장소는 세션 훅이 매 세션 그것을 찍는다.
    # ⚠ **그래도 저장소마다 한 줄은 낸다.** 옛 판은 초록인 저장소의 판정을 파일 목록과 같은
    #   통(`$same`)에 넣어 개수에만 잡히게 했고, 그래서 **다 초록인 기계에서는 화면에 자국이
    #   하나도 안 남았다** — 「안 쟀다」와 구별이 안 된다 (실측 2026-09-11 · 사내 PC: 저장소
    #   다섯이 다 초록이라 이 칸이 통째로 안 보였다). 아래 한 줄이 그 자리를 든다.
    # ⚠ **`2>&1` 을 안 붙인다** — 5.1 은 네이티브 exe 의 stderr 한 줄을 오류로 승격한다
    #   (까닭은 `Sync-Repos` 머리에 있다). 사유는 훅이 stdout 한 줄로 낸다.
    # ⚠ **묻는 훅은 그 저장소의 사본이 아니라 진본이다.** 사본은 이 배포가 덮으러 가는 옛 판일 수
    #   있고, 옛 판은 `--needs-install` 을 몰라 auto 갈래로 빠져 저장소당 50초를 돌고 엉뚱한
    #   마지막 줄을 사유로 낸다(실측 2026-09-16 · 첫 실전: 다섯 저장소 235초). 그래서 이 저장소의
    #   몸통(`session-start-body.sh`)을 바로 부르고 대상 저장소는 `SESSION_START_REPO` 로 넘긴다 —
    #   문지기가 몸통을 부를 때 쓰는 것과 같은 입구다(0061).
    $needsProbe = Join-Path $src '.claude\hooks\session-start-body.sh'
    $env:SESSION_START_REPO = $repoRoot -replace '\\', '/'
    try { $needs = & $bash ($needsProbe -replace '\\', '/') --needs-install; $needsRc = $LASTEXITCODE }
    finally { Remove-Item Env:SESSION_START_REPO -ErrorAction SilentlyContinue }
    $needsWhy = @($needs | Where-Object { "$_".Trim() }) | Select-Object -Last 1
    if (-not $needsWhy) { $needsWhy = '훅이 사유를 안 냈다' }
    # ⚠ **재는 자는 그 저장소에 지금 있는 선언으로 잰다 — 복사는 아직 안 됐다.** 도구 선언
    #   (`tools.global.conf`)이 이번 배포에서 바뀌면 새 선언이 아직 그 저장소에 없어 지문이
    #   맞는 것으로 나오고, 설치가 안 올라 **배포를 두 번 돌려야 깔렸다**(실측 2026-09-12
    #   · ruff: 첫 판은 그 줄이 없었고 둘째 판이 깔았다). 그래서 선언을 덮는 복사가 계획에
    #   있으면 판정과 무관하게 올린다 — 실행은 계획 순서라 복사(앞)가 설치(여기)보다 먼저 돈다.
    $declChanges = @($plan | Where-Object {
        $_.Kind -eq 'copy' -and $_.Repo -eq $repoRoot -and $_.To -like '*\.claude\tools.global.conf' })
    # ⚠ **2 는 「못 쟀다」라 0 으로 안 접는다** — 부재가 통과로 읽히는 자리가 거기다. 못 쟀으면 깐다.
    if ($needsRc -eq 0 -and $declChanges.Count -eq 0) {
        Write-Host "· $repoRoot — $needsWhy, 안 깐다" -ForegroundColor DarkGray
    } else {
        $why = if ($needsRc -eq 1) { $needsWhy }
               elseif ($needsRc -ne 0) { "못 쟀다 — $needsWhy" }
               else { '도구 선언이 바뀐다 — 새 선언으로 깐다' }
        $installSteps += @{
            Kind = 'install'; Repo = $repoRoot; Script = $boot
            Text = "+ 저장소 설치  $repoRoot  ($why)"
        }
    }
    # --- 마지막 CI — 읽는 자를 세운다 ---
    # main 에 바로 커밋하는 이 집에서 CI 는 PR 도 자동머지도 없이 GitHub 페이지에만 빨강을 남긴다.
    # 읽는 자가 없어 저장소 둘이 사흘을 빨갛게 살았다(실측 2026-09-12). 배포가 도는 자리가 곧
    # 사람이 보는 자리라 여기서 한 줄 읽는다. 세밀 토큰(GH_TOKEN)에는 Actions 읽기가 없어 403 이
    # 나면 키링(gh auth login)으로 한 번 더 묻고, 그것도 없으면 「못 쟀다」로 남긴다 — 이 줄로
    # 배포를 막지 않는다. 빨강이면 남은 수동 작업에 올린다.
    $slug = $null
    try { $remote = & git -C $repoRoot remote get-url origin 2>$null } catch { $remote = '' }
    if ($remote -match 'github\.com[:/]([^/\s]+/[^/\s]+?)(\.git)?$') { $slug = $Matches[1] }
    if ($slug -and (Get-Command gh -ErrorAction SilentlyContinue)) {
        $ciArgs = @('run', 'list', '--repo', $slug, '--branch', 'main', '--limit', '1',
                    '--json', 'conclusion,status,headSha,createdAt')
        # ⚠ `2>$null` 은 방패가 아니다(`Sync-Repos` 머리) — 403 한 줄이 배포를 통째로 죽였다
        #   (실측 2026-09-12). 잡아서 넘긴다.
        try { $ciJson = & gh @ciArgs 2>$null; $ciRc = $LASTEXITCODE } catch { $ciJson = $null; $ciRc = 1 }
        if ($ciRc -ne 0 -and $env:GH_TOKEN) {
            $savedTok = $env:GH_TOKEN; $env:GH_TOKEN = $null
            try { $ciJson = & gh @ciArgs 2>$null; $ciRc = $LASTEXITCODE } catch { $ciJson = $null; $ciRc = 1 }
            $env:GH_TOKEN = $savedTok
        }
        $ci = $null
        if ($ciRc -eq 0 -and $ciJson) { $ci = @($ciJson | ConvertFrom-Json) | Select-Object -First 1 }
        if ($ci) {
            $verdict = if ($ci.conclusion) { $ci.conclusion } else { $ci.status }
            $ciLine  = "마지막 CI $verdict · $($ci.headSha.Substring(0, 7)) · $($ci.createdAt.Substring(0, 10))"
            # 결론이 아직 없으면(돌고 있다·줄 서 있다) 초록도 빨강도 아니다 — 남은 작업에 안 올린다.
            # 첫 판이 in_progress 를 빨강으로 찍어 「CI 빨강」을 거짓으로 남겼다(실측 2026-09-12).
            if ($verdict -eq 'success') { $gateReport += "  ✅ $ciLine" }
            elseif (-not $ci.conclusion) { $gateReport += "  · $ciLine — 아직 결론이 없다" }
            else {
                $gateReport += "  ❌ $ciLine — 왜인지는:  gh run view --repo $slug --log-failed"
                $todo += "CI 빨강 — $slug $($ci.headSha.Substring(0, 7)):  gh run view --repo $slug --log-failed"
            }
        } elseif ($ciRc -eq 0) {
            $gateReport += "  · 마지막 CI — 실행이 없다 ($slug)"
        } else {
            $gateReport += "  · 마지막 CI — 못 쟀다 (gh 가 Actions 를 못 읽는다: GH_TOKEN 에 Actions: Read 를 더하거나 gh auth login)"
        }
    }
}

# --- 전역형 도구 — 저장소 고리 **앞에** 한 번 (#43) ---
# 무엇이 전역형인지도, 어느 저장소의 선언을 합칠지도 이 스크립트는 모른다 — `--install-global`
# 갈래가 안다. 여기는 **한 번 부른다**는 것만 든다(도구 이름이 여기 없는 것과 같은 결).
# ⚠ **저장소 걸음이 하나도 없으면 이 걸음도 없다.** 다 살아 있는 기계에 매번 승인을 묻지
#   않는 규율이 위와 같다 — 전역 선언(`tools.global.conf`)은 저장소마다 배포된 사본이라,
#   전역형 도구가 늘거나 바뀌면 그것을 부르는 저장소의 선언 지문이 같이 어긋나 그 저장소가
#   위에서 걸음을 올린다. 그 걸음이 서면 이 걸음도 선다.
# ⚠ **「도구가 닿나」는 여기서 안 잰다** (#47 ②). 계획 단계는 파일만 보므로, 선언은 그대로인데
#   기계에서 도구만 빠진 자리는 여기 안 걸린다 — 지난 설치가 진 자리는 `--needs-install` 이
#   실패 기록으로 들고, 그 밖의 부재는 세션 훅의 진단이 매 세션 낸다.
# ⚠ **덮이지 않는 자리가 하나 있다 — 이 저장소 제 도구다**(`.claude/tools.conf`). 여기는
#   `[repos]` 에 안 들어 위 고리가 안 돌므로 재는 자가 없고, 그래서 그것만 꺼져 있으면
#   이 걸음이 안 선다. 그 자리는 이 저장소에서 세션을 열 때 그 훅이 든다 —
#   배포가 안 재는 것을 안 잰다고 말하는 편이, 매번 승인을 묻는 것보다 싸다.
if ($installSteps.Count -gt 0) {
    $globalBoot = Join-Path $src '.claude\hooks\session-start.sh'
    if (Test-Path $globalBoot) {
        if ($bash) {
            $plan += @{
                Kind = 'install-global'; Script = $globalBoot
                Text = '+ 전역 설치  전역형 도구를 기계에 한 번 (npm 전역 · 릴리스 바이너리 · winget · 브라우저)'
            }
        } else {
            $todo += "Git Bash 를 못 찾음. 직접 실행:  bash '$globalBoot' --install-global"
        }
    }
    $plan += $installSteps
}

# --- 제거 후보: 원본에 없는 에이전트 파일 ---
$agentDst = Join-Path $dst 'agents'
if ($hasAgents -and (Test-Path $agentDst)) {
    $keep = (Get-ChildItem $agentSrc -Filter *.md).Name
    Get-ChildItem $agentDst -Filter *.md | Where-Object { $keep -notcontains $_.Name } | ForEach-Object {
        $prunable += @{ Kind = 'remove'; Path = $_.FullName; Text = "- 제거  $($_.FullName)  (agents/에 없음)" }
    }
}

# --- 제거 후보: 원본에 없는 씨앗 파일 ---
# ⚠ **씨앗 폴더(`seeds\…`)만 센다 — `posco` 는 안 센다.** 씨앗은 새 프로젝트가 복사해 출발하는 자리라,
#   원본에서 걷은 부품이 홈에 남으면 계속 퍼진다. 예전에는 설치기가 판마다 거울로 걷었는데, 설정 저장소를
#   든 PC 에서는 설치기가 이 폴더를 비켜서므로(PAISetup install.ps1 7 칸) 걷는 손이 여기다.
#   `posco` 는 프록시가 제 기록(`proxy.log` · `*.pid`)을 쓰는 자리라 원본에 없는 파일이 곧 쓰레기가 아니다.
foreach ($sd in ($seedDirs | Where-Object { $_ -like 'seeds\*' })) {
    $sSrc = Join-Path $src $sd
    $sDst = Join-Path $dst $sd
    if (-not (Test-Path $sSrc) -or -not (Test-Path $sDst)) { continue }
    Get-ChildItem $sDst -Recurse -File | Where-Object { $_.FullName -notmatch '\\__pycache__\\' } | ForEach-Object {
        $rel = $_.FullName.Substring($sDst.Length + 1)
        if (-not (Test-Path -LiteralPath (Join-Path $sSrc $rel))) {
            $prunable += @{ Kind = 'remove'; Path = $_.FullName; Text = "- 제거  $($_.FullName)  ($($sd -replace '\\', '/')/에 없음)" }
        }
    }
}

# --- 제거 후보: 원본에 없는 메모리 파일 ---
if (Test-Path $memSrc) {
    foreach ($proj in (Get-ChildItem $memSrc -Directory)) {
        $keep = (Get-ChildItem $proj.FullName -Filter *.md).Name
        foreach ($d in (Get-ProjectMemDst $proj.Name)) {
            if (-not (Test-Path $d)) { continue }
            Get-ChildItem $d -Filter *.md | Where-Object { $keep -notcontains $_.Name } | ForEach-Object {
                $prunable += @{ Kind = 'remove'; Path = $_.FullName; Text = "- 제거  $($_.FullName)  (memory/$($proj.Name)/에 없음)" }
            }
        }
    }
}

# --- 제거 후보: 원본에 없는 스킬 파일 ---
# 에이전트·메모리와 같은 이유다. 저장소에서 지운 스킬이 홈에 남아 계속 로드되면
# 배포한 줄 알았던 것과 실제가 어긋난다.
$skillDst = Join-Path $dst 'skills'
if ((Test-Path $skillSrc) -and (Test-Path $skillDst)) {
    # ⚠ **이 저장소 전용 스킬은 여기서도 뺀다.** 그래야 전에 깔려 있던 홈 사본이 제거 후보로
    #   올라온다 — 선언에 이름을 더한 날 홈에서 저절로 걷히는 길이 이것이다. 안 빼면 「밀지도
    #   않고 걷지도 않는」 자리가 되어, 옛 사본이 계속 로드되면서 아무도 모른다.
    # ⚠ **앱이 관리하는 폴더는 이 저장소 것이 아니라 안 센다.** 데스크톱 앱이 제 스킬을
    #   `skills/synced/<id>/` 로 동기화한다 — 진본에 없는 것이 당연하고, 걷으면 앱 것을 지운다
    #   (실측 2026-09-22 집 PC: 제거 후보 231 중 204 가 그 폴더 · #74). `check-global-copies.sh`
    #   는 진본 없는 홈 스킬을 애초에 안 재므로 이쪽만 갈린다.
    $appManagedSkillDirs = @('synced')
    $keep = @(Get-ChildItem $skillSrc -Recurse -File |
        ForEach-Object { $_.FullName.Substring($skillSrc.Length + 1) } |
        Where-Object { $localSkills -notcontains ($_ -split '\\')[0] })
    Get-ChildItem $skillDst -Recurse -File |
        Where-Object { $appManagedSkillDirs -notcontains ($_.FullName.Substring($skillDst.Length + 1) -split '\\')[0] } |
        Where-Object { $keep -notcontains $_.FullName.Substring($skillDst.Length + 1) } |
        ForEach-Object {
            $prunable += @{ Kind = 'remove'; Path = $_.FullName; Text = "- 제거  $($_.FullName)  (skills/에 없음)" }
        }
}

# --- 제거 후보: 원본에 없는 룰 파일 ---
# 진본에서 지운 룰이 홈이나 저장소 사본에 남으면 계속 로드·복사된다 — 스킬과 같은 이유.
$rulesDst = Join-Path $dst 'rules'
if (Test-Path $rulesSrc) {
    $keep = (Get-ChildItem $rulesSrc -Filter *.md).Name
    # 홈만 본다. 저장소의 `.claude/rules/` 는 **그 저장소 자신의 룰** 자리라, 여기서 훑으면
    # 진본에 없다는 이유로 남의 룰을 지운다 (docs/decisions/0014).
    $ruleCopyDirs = @($rulesDst)
    foreach ($d in $ruleCopyDirs) {
        if (-not (Test-Path $d)) { continue }
        Get-ChildItem $d -Filter *.md | Where-Object { $keep -notcontains $_.Name } | ForEach-Object {
            $prunable += @{ Kind = 'remove'; Path = $_.FullName; Text = "- 제거  $($_.FullName)  (rules.global/에 없음)" }
        }
    }
}

if ($Prune) { $plan += $prunable }

# --- 사용자 환경변수 ---
# 한국어 윈도우의 인코딩 구멍은 둘이고 서로 다른 자리다:
#   ① PowerShell 5.1 은 **BOM 없는 .ps1 을 ANSI(cp949)로 읽는다** → utf8-bom.sh 훅이 막는다
#   ② 파이썬은 open() 기본 인코딩을 locale 에서 가져온다(역시 cp949) → 이 변수가 막는다
# PYTHONUTF8=1 은 PEP 540 UTF-8 모드다. open()·stdio 를 UTF-8 로 고정해 파일마다
# encoding= 을 적어야 하는 규율 자체를 없앤다.
#
# 저장소 settings.json 의 env 로도 같은 값을 걸지만 그것은 **Claude Code 세션 안에서만**
# 산다. 사람이 직접 연 터미널·에디터에서도 같으려면 사용자 환경변수여야 한다.
# 값이 고정이라 사람이 정할 것이 없으므로 안내가 아니라 여기서 심는다.
$userEnvWant = [ordered]@{ 'PYTHONUTF8' = '1' }
foreach ($k in $userEnvWant.Keys) {
    $v = $userEnvWant[$k]
    if ([Environment]::GetEnvironmentVariable($k, 'User') -eq $v) {
        $same += "= 설정됨  사용자 환경변수 $k=$v"
    } else {
        $plan += @{
            Kind = 'userenv'; Name = $k; Value = $v
            Text = "+ 설정  사용자 환경변수 $k=$v  (이미 열린 터미널에는 안 걸린다 — 새로 열 것)"
        }
    }
}

# --- 실행 순서 — **배선을 맨 앞에 세운다** ---
# `core.hooksPath` 는 로컬 `git config` 한 줄이다. 망도 안 타고 디스크도 안 타고 도구도
# 안 부르니 **질 까닭이 없다.** 그런데 계획에서 서는 자리는 배포 백여 걸음과 MCP 등록
# 뒤였고, 실행 고리는 `$ErrorActionPreference = 'Stop'` 아래 **하나**다 — 앞 걸음 하나가
# 던지면 뒤가 통째로 안 돈다.
# ⚠ **그러면 커밋 게이트가 없는 채로 저장소가 서고, 그 부재는 조용하다** — 훅이 안 걸렸으니
#   안 걸렸다고 말할 자도 없다. 이 저장소가 내내 막으려던 「부재가 통과로 읽히는 것」이
#   가장 비싸게 나는 자리다: 게이트를 안 탄 커밋은 되돌릴 수가 없다 (#31 · 실측 2026-09-14 ·
#   앞쪽 복사 하나가 던지자 계획에 있던 `+ 설정 core.hooksPath` 둘이 화면에만 남고
#   저장소에는 안 걸렸다 · 형제 둘에 커밋 넷이 게이트 없이 들어갔다).
# ⚠ **뒤가 무엇으로 죽든 게이트만은 선다** 는 것이 이 한 줄이 사는 값이다. 못 끝낸 배포도
#   커밋만은 지키게 둔다 — 고치는 동안에도 사람은 커밋한다.
# ⚠ **화면에 내는 목록도 이 순서다** — 계획을 굳힌 뒤에 세우니 사람이 읽는 차례와 실제로
#   도는 차례가 같다. 둘이 갈리면 화면이 거짓말을 한다.
# ⚠ **배선보다 앞에 서는 것이 하나 있다 — 당김이다**(결정 0078). 당김은 던지지 않으므로 「뒤가
#   무엇으로 죽든」은 그대로 서지만, **느린 망은 이 배선을 늦춘다** — 늦는 폭의 최대가 당김
#   칸의 `$PullBatchTimeoutSec` 다(그 한도를 넘긴 자식은 거둬지고 다음 걸음이 바로 선다).
#   커밋 게이트 배선의 임자는 매 세션 거는 세션 훅이고, 이 자리는 그 뒤를 받는다.
$plan = @($plan | Where-Object { $_.Kind -eq 'githooks' }) +
        @($plan | Where-Object { $_.Kind -ne 'githooks' })

# --- 사람이 해야 할 것 ---
# 키 이름을 여기 손으로 또 적으면 서버가 늘 때마다 두 자리를 고쳐야 하고, 한쪽만 고치면
# 새 PC 는 서버만 등록된 채 조용히 실패한다 — 등록 자체는 됐으니 목록엔 초록으로 뜬다.
# 그래서 설정이 ${VAR} 로 이름을 든 것은 세지 않고 mcp-servers.json 에서 뽑는다.
if (Test-Path $mcpFile) {
    $keyRefs = [regex]::Matches((Get-Content $mcpFile -Raw), '\$\{([A-Za-z_][A-Za-z0-9_]*)\}') |
               ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
    foreach ($k in $keyRefs) {
        if (-not [Environment]::GetEnvironmentVariable($k, 'User')) {
            $todo += "$k 설정 — 별도 터미널에서:  setx $k ""실제키값"""
        }
    }
}

# --- GitHub 토큰의 만료 ---
# `GH_TOKEN` 의 세밀 토큰은 만료가 강제다 — 커밋된 키라 좁게 두기로 했고(secrets.env 곁말 ·
# 결정 0025), 좁은 토큰은 GitHub 이 1년 안에 죽인다. 죽는 날 MCP 와 gh 가 **조용히** 선다: 위
# 「없으면 setx」 검사는 값이 있기만 하면 초록이라 만료된 토큰도 「있음」이다. 응답 머리글에
# 만료일이 실려 오므로 호출 한 번으로 잰다 — 죽었으면 실행 환경이 안 선 것(`$envDown`), 30일
# 안이면 사람이 할 일(`$todo`), 멀쩡하면 날짜를 한 줄 찍는다(초록도 편다).
# ⚠ 망이 안 닿으면 「못 쟀다」로 한 줄만 남긴다 — 그 사실로 배포를 막지 않는다.
$ghTok = [Environment]::GetEnvironmentVariable('GH_TOKEN', 'User')
if ($ghTok) {
    try {
        $ghResp = Invoke-WebRequest -Uri 'https://api.github.com/user' -UseBasicParsing -TimeoutSec 8 `
                    -Headers @{ Authorization = "Bearer $ghTok"; 'User-Agent' = 'claude-config-deploy' }
        $expKey = @($ghResp.Headers.Keys | Where-Object { $_ -ieq 'Github-Authentication-Token-Expiration' })
        if ($expKey.Count -eq 0) {
            Write-Host "= GH_TOKEN 만료 없음 (머리글에 만료일이 안 실렸다 — 클래식·OAuth 토큰)" -ForegroundColor DarkGray
        } else {
            $expRaw = [string]$ghResp.Headers[$expKey[0]]
            $expAt  = [datetime]::ParseExact(($expRaw -replace ' UTC$', ''), 'yyyy-MM-dd HH:mm:ss',
                        [Globalization.CultureInfo]::InvariantCulture)
            $left   = [int][math]::Floor(($expAt - (Get-Date).ToUniversalTime()).TotalDays)
            $expDay = $expAt.ToString('yyyy-MM-dd')
            if ($left -le 30) {
                $todo += "GH_TOKEN 만료 ${left}일 남음 ($expDay) — GitHub 에서 재발급해 secrets.env 를 고치고 다시 배포한다"
            } else {
                Write-Host "= GH_TOKEN 만료 $expDay (${left}일 남음)" -ForegroundColor DarkGray
            }
        }
    } catch {
        $code = $null
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        if ($code -eq 401) {
            $envDown += 'GH_TOKEN 이 죽었다 (401 — 만료됐거나 회수됐다). GitHub 에서 재발급해 secrets.env 를 고치고 다시 배포한다'
        } else {
            Write-Host "· GH_TOKEN 만료 — 못 쟀다 (api.github.com 이 안 닿는다: $($_.Exception.Message))" -ForegroundColor DarkGray
        }
    }
}

# ============================ 2단계: 보고 및 승인 ============================

# 개수만 낸다. 이미 맞는 것을 한 줄씩 펴면 매 실행이 100줄을 넘어 정작 봐야 할
# "바꿀 것"이 묻힌다 — 침묵하지 않는 목적은 개수 한 줄로 이미 달성된다.
# 어긋난 것을 찾을 때만 -ShowUnchanged 로 편다.
if ($same.Count -gt 0) {
    Write-Host "`n이미 맞는 것 $($same.Count)개 (건드리지 않음)" -ForegroundColor DarkGray
    if ($ShowUnchanged) {
        $same | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    } else {
        Write-Host "  전체를 보려면:  .\deploy.ps1 -ShowUnchanged" -ForegroundColor DarkGray
    }
}

# 기본 실행에서는 제거하지 않는다. 있다는 사실만 알린다.
if ((-not $Prune) -and $prunable.Count -gt 0) {
    Write-Host "`n제거 후보 $($prunable.Count)개 있음 (이번 실행에서는 건드리지 않음)" -ForegroundColor Yellow
    $prunable | ForEach-Object { Write-Host "  $($_.Text)" -ForegroundColor Yellow }
    Write-Host "  → 정리하려면:  .\deploy.ps1 -Prune" -ForegroundColor Yellow
}

# 마지막 CI 줄들 — **「바꿀 것이 없습니다」 앞이다.** 뒤에 두면 다 초록인 기계에서 그 return 에
# 걸려 영영 안 보인다 — 이 칸이 가장 필요한 자리가 바로 거기다. 줄은 담은 그대로 낸다.
if ($gateReport.Count -gt 0) {
    Write-Host ''
    $gateReport | ForEach-Object { Write-Host $_ }
}

if ($plan.Count -eq 0) {
    Write-Host "`n바꿀 것이 없습니다. 이미 최신입니다." -ForegroundColor Green
    if ($todo.Count -gt 0) {
        Write-Host "`n남은 수동 작업:" -ForegroundColor Yellow
        $todo | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    }
    return
}

Write-Host "`n바꿀 것 ($($plan.Count)개)" -ForegroundColor Cyan
$plan | ForEach-Object { Write-Host "  $($_.Text)" -ForegroundColor Cyan }
Write-Host "`n덮어쓰거나 치우는 파일은 먼저 여기 백업됩니다:"
Write-Host "  $backup"

if (-not $Yes) {
    # 승인은 **명시적인 y 하나만** 통과시킨다. 나머지는 전부 「안 함」이다.
    #
    # ⚠ 옛 판은 「물어볼 자리가 없으면 Read-Host 가 던진다」에 기댔다. **안 던진다.**
    #   비대화 세션(`powershell.exe -File`, 출력이 파이프로 물린 자리)에서 Read-Host 는
    #   조용히 $null 을 돌려주고, 그 $null 이 `-notmatch '^[yY]'` 를 통과해 취소 분기를
    #   건너뛴다 — 무인 실행을 막으려고 세운 관문이 거꾸로 **스스로 승인한다.**
    #   실측 2026-09-03: 이 VDI 에서 -Yes 없이 부른 배포가 계획을 그대로 실행했다.
    # ⚠ 그래서 「아니라고 했나」가 아니라 **「예라고 했나」를 묻는다.** 답이 없는 것과
    #   아니라고 한 것은 여기서 같은 값이어야 한다 — 다르게 두면 답이 없을 때가 통과다.
    #   부정을 재는 관문은 침묵 앞에서 열리고, 긍정을 재는 관문은 침묵 앞에서 닫힌다.
    $answer = $null
    try {
        $answer = Read-Host "`n진행할까요? (y/N)"
    } catch {
        # 던지는 호스트도 있다. 죽게 두면 **아무것도 안 바꿨는데 종료 코드 1** 이 나가
        # 부르는 쪽이 배포 실패로 센다 — 판정이 실물과 어긋나는 자리다. 「안 함」으로 내린다.
        $answer = $null
    }
    if ([string]::IsNullOrWhiteSpace($answer)) {
        Write-Host "`n물어볼 자리가 없어 멈췄습니다. 진행하려면:  .\deploy.ps1 -Yes" -ForegroundColor Yellow
        return
    }
    if ($answer.Trim() -notmatch '^[yY]') {
        Write-Host "취소했습니다. 아무것도 바꾸지 않았습니다." -ForegroundColor Yellow
        return
    }
}


# ============================ 3단계: 실행 ============================

function Save-Backup($path) {
    # 백업도 원래 폴더 구조를 유지한다. 이름만 떼어 평평하게 쌓으면
    # 여러 스킬의 SKILL.md처럼 같은 이름끼리 서로를 덮어써 백업이 소실된다.
    $rel = if ($path.StartsWith($dst, [StringComparison]::OrdinalIgnoreCase)) {
        $path.Substring($dst.Length).TrimStart('\')
    } else {
        # ~/.claude 밖 (저장소 배포본). 이름만 떼면 여러 저장소의 같은 이름끼리
        # 서로를 덮어써 백업이 소실된다 — 경로 전체를 이름에 접어 유일하게 만든다.
        Join-Path '_outside' (($path -replace ':', '') -replace '[\\/]', '-')
    }
    $to = Join-Path $backup $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $to -Parent) | Out-Null
    Copy-Item $path $to
}

# ── 이번 실행의 표식 — **같은 배포 안에서만 통하는 인용 좌표다** (#57) ──────────────────
# 전역 걸음(`--install-global`)이 도구마다 ✅ 를 내면 훅이 그것을 홈의 명부에 이 표식과 함께
# 적고, 이어 도는 저장소 걸음(`--install`)의 진단은 **표식이 같을 때만** 그 줄을 인용하고
# 프로브를 안 띄운다. 저장소 다섯이면 같은 명제를 스물다섯 번 재던 자리다(사내 VDI ~280초).
# ⚠ **캐시가 아니라서 값이 실행마다 갈려야 한다** — 시각에 PID 를 붙이는 까닭이 그것이다(같은
#   초에 둘이 돌아도 안 겹친다). 아래 고리가 끝나면 이름을 걷으므로, 다음 배포는 다른 값으로
#   서고 지난 실행의 명부는 아무도 못 읽는다.
# ⚠ 고리 **앞**에 한 번 세운다 — 걸음마다 세우면 같은 값을 짓는 자리가 둘이 되고, 갈리는 순간
#   전역 걸음이 적은 줄을 저장소 걸음이 못 알아본다.
$env:CLAUDE_CONFIG_RUN = "$(Get-Date -Format 'yyyyMMddTHHmmss')-$PID"

Write-Host ""
foreach ($step in $plan) {
    switch ($step.Kind) {

        'copy' {
            # 저장소 배포본은 그 저장소를 당긴 뒤에 민다. 못 당겼으면 안 민다.
            # ⚠ **여기서 당기지 않는다 — 당김은 계획 앞에서 이미 돌았고 이 걸음은 그 판정을
            #   읽기만 한다**(`$pulledRepos` · 결정 0078). 옛 판은 이 자리에서 당겼고, 그래서
            #   밀 것이 없는 회차에는 당김도 함께 사라졌다(#112).
            # ⚠ 판정에 없는 저장소는 당길 것이 없던 자리다(`.git` 이 없다) — 막을 까닭도 없다.
            $skip = $false
            if ($step.Repo -and $pulledRepos.ContainsKey($step.Repo) -and -not $pulledRepos[$step.Repo]) {
                Write-Host "· 건너뜀  $($step.To)  (그 저장소를 지금 못 맞춘다 — 까닭은 위 당김 줄. 밀면 다음 당김이 막힌다)" -ForegroundColor Yellow
                $skip = $true
            }
            # 계획은 당긴 뒤의 트리를 보고 섰지만, 그 사이 다른 손(VS Code 로 연 세션의 배경
            # 당김)이 같은 파일을 앉혔을 수 있다 — 여기서 한 번 더 묻는다. 같은 것을 다시 쓰면
            # 백업만 쌓이고 얻는 것이 없다.
            if (-not $skip -and (Test-Path $step.To) -and
                ((Get-FileHash $step.From).Hash -eq (Get-FileHash $step.To).Hash)) {
                Write-Host "= 동일  $($step.To)  (그 사이 같아졌다)" -ForegroundColor DarkGray
                $skip = $true
            }
            if (-not $skip) {
                if (Test-Path $step.To) { Save-Backup $step.To }
                # ⚠ **대상이 링크면 링크를 걷고 쓴다.** `Copy-Item` 은 링크를 따라가 **가리키는 원본**을
                #   덮는다 — 손으로 링크를 걸어 둔 PC(대상 → 이 저장소의 진본)에서 배포가 진본을 대상의
                #   새 내용으로 바꿔 버린다. 내용은 위 백업이 이미 떴다.
                $toItem = Get-Item -LiteralPath $step.To -Force -ErrorAction SilentlyContinue
                if ($toItem -and $toItem.LinkType) { Remove-Item -LiteralPath $step.To -Force }
                New-Item -ItemType Directory -Force -Path (Split-Path $step.To -Parent) | Out-Null
                Copy-Item $step.From $step.To -Force
                Write-Host "+ 배포  $($step.To)"
            }
        }

        'stamp' {
            # ⚠ **백업을 안 남긴다** — 옛 판 번호는 되살릴 자산이 아니라 **다시 재면 나오는
            #   값**이다(이 스크립트를 또 돌리면 그 자리에 또 선다).
            # BOM 없는 UTF-8 · LF 로 쓴다 — 읽는 자가 파이썬이고, BOM 이 붙으면 첫 낱말에
            # 그 세 바이트가 딸려 들어가 판이 엉뚱한 글자로 읽힌다.
            New-Item -ItemType Directory -Force -Path (Split-Path $step.Path -Parent) | Out-Null
            [System.IO.File]::WriteAllText($step.Path, $step.Line + "`n",
                                          (New-Object System.Text.UTF8Encoding($false)))
            Write-Host "+ 판 줄  $($step.Path)  ($($step.Line))"
        }

        'mcp' {
            if (-not $bash) {
                # Git Bash가 없으면 강행하지 않는다 — 따옴표가 깨진 채 등록되면 더 골치다
                Write-Host "! MCP $($step.Name) 미등록 (Git Bash 없음)" -ForegroundColor Red
                $todo += "Git Bash에서 실행:  claude mcp add-json $($step.Name) '$($step.Json)' -s user"
                break
            }
            # PowerShell이 -c 인자의 따옴표를 먹으므로 명령을 파일에 써서 넘긴다.
            # BOM이 있으면 bash가 첫 줄을 못 읽으므로 UTF8(BOM 없음) + LF로 쓴다.
            $cmd = "claude mcp add-json $($step.Name) '$($step.Json)' -s user"
            $sh  = Join-Path $env:TEMP "deploy-mcp-$($step.Name).sh"
            [System.IO.File]::WriteAllText($sh, $cmd + "`n", (New-Object System.Text.UTF8Encoding($false)))
            & $bash $sh
            $code = $LASTEXITCODE
            Remove-Item $sh -Force -ErrorAction SilentlyContinue

            # 종료 코드를 반드시 확인한다 — 실패를 성공으로 보고하면 기록과 실제가 어긋난다
            if ($code -eq 0) {
                Write-Host "+ 등록  MCP $($step.Name)"
            } else {
                Write-Host "! MCP $($step.Name) 등록 실패 (exit $code)" -ForegroundColor Red
                $todo += "Git Bash에서 실행:  $cmd"
            }
        }

        'githooks' {
            & git -C $step.Repo config core.hooksPath .githooks
            if ($LASTEXITCODE -eq 0) {
                Write-Host "+ 설정  core.hooksPath  $($step.Repo)"
            } else {
                Write-Host "! core.hooksPath 설정 실패  $($step.Repo)" -ForegroundColor Red
                $todo += "수동 설정:  git -C `"$($step.Repo)`" config core.hooksPath .githooks"
            }
        }

        'install-global' {
            # 전역형 도구를 기계에 한 번 깐다 (#43). 저장소 고리보다 **먼저** 선다 — 고리 안의
            # 배선(정션)이 걸 물건이 그때 이미 깔려 있어야 한다.
            # ⚠ 표식을 여기서 세운다 — 아래 저장소 걸음과 같은 뜻이고, 훅이 `--install-global`
            #   에서 deploy 로 되넘기는 일은 없지만 이름이 서 있는 것이 갈래의 진실이다.
            # ⚠ **종료코드를 받는다.** 전역형 도구가 안 선 채로 저장소 걸음이 초록을 내면
            #   부재가 통과로 읽힌다 — 훅이 그 판정을 내므로 여기서는 받아 나르기만 한다.
            $env:CLAUDE_CONFIG_DEPLOYING = '1'
            & $bash ($step.Script -replace '\\', '/') --install-global
            if ($LASTEXITCODE -ne 0) {
                Write-Host "! 전역 설치가 오류로 끝났습니다 (exit $LASTEXITCODE)" -ForegroundColor Red
                $envDown += '전역형 도구 — 안 선 것이 남았다 (위 ❌ 줄이 곧 고칠 자리)'
                $todo += "확인:  bash '$($step.Script)' --install-global"
            }
        }

        'install' {
            # Git Bash 로 돌린다. PATH 의 bash 는 WSL 일 수 있어 $bash 를 그대로 쓴다.
            # 경로는 슬래시로 바꿔 넘긴다 — 역슬래시는 bash 가 이스케이프로 먹는다.
            # 훅이 진단을 그대로 찍으므로 여기서 한 번 더 판정하지 않는다.
            # ⚠ **고리를 끊는 표식.** 훅은 PC 에서 밖(설치기 · 사람)이 `--install` 로 부르면 개인 칸을
            #   세우고 이 스크립트에 넘긴다 — 여기서 부른 훅이 또 넘기면 고리다. 이 이름이 서 있으면
            #   훅은 저장소 하나의 설치로 간다.
            $env:CLAUDE_CONFIG_DEPLOYING = '1'
            & $bash ($step.Script -replace '\\', '/') --install
            if ($LASTEXITCODE -ne 0) {
                # ⚠ **여기가 목표를 이뤘나를 아는 유일한 자리다.** 훅은 `--install` 에서도
                #   꺼진 검사를 종료코드로 낸다 — 그 신호를 여기서 받아 위층까지 물고 가지
                #   않으면 검사가 꺼진 채로 화면이 초록으로 끝난다 (실측 2026-09-10 · VDI 넷).
                Write-Host "! 저장소 설치가 오류로 끝났습니다 (exit $LASTEXITCODE)  $($step.Repo)" -ForegroundColor Red
                $envDown += "$($step.Repo) — 꺼진 검사가 남았다 (위 진단의 ❌ 줄이 곧 고칠 자리)"
                $todo += "확인:  bash '$($step.Script)' --check"
            }
        }

        'userenv' {
            # setx 와 같은 자리(사용자 환경변수)에 쓴다. setx.exe 는 값을 1024자에서
            # 자르지만 이 API 는 안 자른다 — 값이 짧아도 굳이 자르는 쪽을 쓸 이유가 없다.
            [Environment]::SetEnvironmentVariable($step.Name, $step.Value, 'User')
            Write-Host "+ 설정  사용자 환경변수 $($step.Name)=$($step.Value)"
        }

        'mcpremove' {
            # ⚠ **`2>&1` 을 뗐다 — 그것이 위험을 만들던 자였다** (까닭은 `Sync-Repos`
            #   머리에 있다). `claude mcp remove` 는 지울 것이 없을 때 stderr 로 답하는데,
            #   합쳐 놓으면 그 한 줄이 `NativeCommandError` 로 승격돼 **해제 한 건이 배포
            #   전체를 죽인다.** 안 합치면 그 줄은 콘솔로 흐르고 종료코드만 아래로 온다 —
            #   2026-09-07 에 `claude mcp get` 이 죽인 자리와 같은 병, 더 싼 약이다.
            & claude mcp remove $step.Name -s user | Out-Null
            $code = $LASTEXITCODE
            if ($code -eq 0) {
                Write-Host "- 해제  MCP $($step.Name)"
            } else {
                Write-Host "! MCP $($step.Name) 해제 실패 (exit $code)" -ForegroundColor Red
                $todo += "수동 해제:  claude mcp remove $($step.Name) -s user"
            }
        }

        'remove' {
            Save-Backup $step.Path
            Remove-Item $step.Path -Force
            Write-Host "- 제거  $($step.Path)"
            # ⚠ **파일만 걷으면 빈 폴더가 남는다** — 걷힌 스킬이 `skills/<이름>/scripts/` 같은 껍데기로
            #   남아 홈 목록을 흐린다. 비었을 때만 위로 올라가며 걷고, 홈 바로 아래 자리(`skills` ·
            #   `agents` · `projects` …)는 비어도 둔다 — 그 자리는 배포가 아니라 앱이 세운다.
            $parent = Split-Path $step.Path -Parent
            while ($parent -and ((Split-Path $parent -Parent) -ne $dst) -and ($parent -ne $dst) -and
                   (Test-Path $parent) -and -not (Get-ChildItem -LiteralPath $parent -Force | Select-Object -First 1)) {
                Remove-Item -LiteralPath $parent -Force
                Write-Host "- 제거  $parent  (빈 폴더)"
                $parent = Split-Path $parent -Parent
            }
        }
    }
}

# 표식은 이 실행과 함께 걷는다 — 프로세스가 죽으면 어차피 사라지지만, 그 전에 이 셸에서 손으로
# 부른 훅이 지난 걸음의 명부를 **제 실측으로** 읽는 자리를 안 만든다.
Remove-Item Env:CLAUDE_CONFIG_RUN -ErrorAction SilentlyContinue

if (Test-Path $backup) { Write-Host "`n백업: $backup" }

if ($todo.Count -gt 0) {
    Write-Host "`n남은 수동 작업:" -ForegroundColor Yellow
    $todo | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}

# ── 판정 — **환경이 안 섰으면 「완료」라고 말하지 않는다** ─────────────────
# ⚠ 옛 판은 무엇이 지든 초록 「완료」로 끝나고 종료코드도 늘 0 이었다. 그래서 이 스크립트를
#   부르는 자(훅 `--install` → `install.ps1` → 설치 화면)는 **물어볼 데가 없었다** —
#   저장소 설치가 꺼진 검사를 안고 끝나도 화면은 초록이었다 (실측 2026-09-10 · 사내·사외 VDI).
if ($envDown.Count -gt 0) {
    Write-Host "`n! 실행 환경이 안 섰습니다 — $($envDown.Count)곳:" -ForegroundColor Red
    $envDown | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "`n끝내지 못했습니다. 위 진단의 까닭을 고친 뒤 다시 돌립니다." -ForegroundColor Red
    exit 1
}

# ⚠ **「재시작」 한 낱말로 뭉개지 않는다 — 다시 여는 자리가 둘이다.** 규범·룰·스킬은 세션이 뜰 때
#   읽혀 새 세션이면 되지만, 새로 깐 도구는 PATH 를 타서 **Claude Code 를 띄운 앱**이 설치 뒤에 떠야
#   보인다 — 앱은 뜰 때 PATH 를 한 번 복사하고 그 뒤 바뀐 것은 안 따라온다.
Write-Host "`n완료. 이미 열려 있던 Claude Code 세션에는 안 들어갑니다 — 새 세션부터 적용되고, 새로 깐 도구는 Claude Code 를 띄운 앱(VS Code · 데스크탑 앱 · 터미널)을 완전히 닫았다 다시 열어야 잡힙니다." -ForegroundColor Green
