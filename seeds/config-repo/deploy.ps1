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
# 하는 일
#   1. .claude/CLAUDE.global.md -> ~/.claude/CLAUDE.md             전역 룰 (진본은 이 한 자리)
#      .claude/rules.global/*.md -> ~/.claude/rules/                 영역 룰 (홈 한 자리)
#      agents/*.md -> ~/.claude/agents/                            서브에이전트
#      memory/<이름>/*.md -> ~/.claude/projects/<슬러그>/memory/    프로젝트·워크스페이스 메모리
#      .claude/skills/** -> ~/.claude/skills/**                   스킬 (폴더 통째로)
#      어느 저장소·어느 슬러그로 가나는 deploy.targets.d/*.conf 가 든다 — 스크립트는 모른다
#      .claude/hooks/*.sh 와 .claude/settings.json -> <저장소>/  훅 몸통과 그 등록
#   2. mcp-servers.json에 적힌 MCP 서버 등록
#   3. .githooks/ 를 둔 저장소에 core.hooksPath 설정 (git 훅은 clone 을 안 따라온다)
#   4. 저장소 부트스트랩 — 각 저장소의 .claude/hooks/session-start.sh 를 Git Bash 로 불러
#      게이트가 쓰는 도구를 확인·설치한다. 무엇을 깔지는 그 훅이 알고 이 스크립트는 모른다
#   5. 사용자 환경변수 — 이 PC 전체에 걸려야 하는 것 (인코딩 축. 아래 §사용자 환경변수)
#   6. 남은 수동 작업 안내 (API 키 등)
#
# 복사하지 않는 것 — 무엇이 배포되고 무엇이 안 되는지는 README 의 배포 대상 표가 든다.
# 여기 적는 것은 **이름이 같아 헷갈리는 자리** 하나뿐이다.
#   ~/.claude/settings.json   **홈의 개인 설정** (모델·테마 등). PC마다 달라 수동 관리.
#                             저장소의 .claude/settings.json 은 훅 등록 파일이라 배포한다 —
#                             이름이 같을 뿐 다른 것이다
#
# 기본 실행은 아무것도 지우지 않는다. 제거는 -Prune 을 줄 때만 한다.
# 제거 후보가 있으면 기본 실행에서도 개수만 알려준다.
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
$prunable = @()  # 제거 후보 (-Prune 없이는 세기만 한다)
# ⚠ **초록도 편다.** 통과가 화면에서 침묵하면 「재서 다 살아 있다」와 「아예 안 쟀다」가
#   같아진다 — 그 침묵은 아무것도 안 말한 것과 같다. 문구는 훅이 든다, 여기는 나르기만 한다.
$gateReport = @()  # 게이트 진단 — 무엇을 쟀고 무엇이 사는가

# 배포 대상은 코드가 아니라 선언이 든다 — deploy.targets.d/*.conf.
# 사람·PC·프로젝트 구성마다 다른 값이라 스크립트에 박지 않는다. 새 PC·새 저장소·
# 새 사람(포크)은 그 폴더에 파일을 더할 뿐 이 스크립트를 고치지 않는다.
# 실제로 존재하는 경로에만 배포하므로, 여러 PC 파일이 같이 있어도 된다.
$memTargets = @{}          # memory/<이름> -> ~/.claude/projects/ 슬러그들
$globalRuleTargets = @()   # 전역 배포본(규범·영역 룰)을 받을 저장소 루트들
# 파일 하나가 PC 하나다. 한 파일에 몰지 않는 이유는 포크다 — 갈려 있으면 포크한 사람이
# 제 파일만 두고 나머지를 지우면 되고, 그 뒤 upstream 머지가 남의 파일만 건드려 안 문다.
$targetsDir   = Join-Path $src 'deploy.targets.d'
$legacyFile   = Join-Path $src 'deploy.targets.conf'
$targetsFiles = @()
if (Test-Path $targetsDir) {
    $targetsFiles += @(Get-ChildItem $targetsDir -Filter *.conf -File |
        Sort-Object Name | ForEach-Object { $_.FullName })
}
# 옛 단일 파일도 읽는다 — 이 갈래 전에 포크한 사람의 값이 조용히 빠지지 않게.
if (Test-Path $legacyFile) {
    $targetsFiles += $legacyFile
    $todo += 'deploy.targets.conf 가 아직 있음 — deploy.targets.d/<PC이름>.conf 로 옮기면 upstream 머지가 이 자리에서 안 문다'
}
if ($targetsFiles.Count -gt 0) {
    foreach ($tf in $targetsFiles) {
        $section = ''
        foreach ($line in (Get-Content $tf -Encoding UTF8)) {
            $line = ($line -replace '#.*$', '').Trim()
            if (-not $line) { continue }
            if ($line -match '^\[(.+)\]$') { $section = $Matches[1]; continue }
            if ($section -eq 'repos') {
                $globalRuleTargets += $line
            } elseif ($section -like 'memory:*') {
                $proj = $section.Substring('memory:'.Length)
                if (-not $memTargets.ContainsKey($proj)) { $memTargets[$proj] = @() }
                $memTargets[$proj] += $line
            }
        }
    }
} else {
    # 선언이 없어도 홈 배포는 돈다(막 포크한 사람의 첫 실행 형태). 침묵하지 않는다.
    $todo += 'deploy.targets.d/ 에 *.conf 없음 — 저장소 배포본·프로젝트 메모리는 배포 안 됨. 그 폴더에 <PC이름>.conf 를 만들어 [repos]·[memory:<이름>] 를 채울 것'
}

# memory/<project>/ 가 이 PC에서 갈 곳. 해당하는 폴더가 없으면 빈 배열.
# 프로젝트 폴더의 존재로 판정한다 — memory 하위 폴더는 아직 없을 수 있다(첫 배포).
function Get-ProjectMemDst($project) {
    $slugs = $memTargets[$project]
    if (-not $slugs) { return @() }
    @($slugs |
        ForEach-Object { Join-Path $dst "projects\$_" } |
        Where-Object   { Test-Path $_ } |
        ForEach-Object { Join-Path $_ 'memory' })
}

# PATH의 bash는 WSL일 수 있다(배포판 없으면 실패). git.exe 위치에서 Git Bash를 직접 찾는다.
$bash = @(
    (Get-Command git -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path (Split-Path (Split-Path $_.Source -Parent) -Parent) 'bin\bash.exe' }),
    "$env:ProgramFiles\Git\bin\bash.exe",
    "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1


# ============================ 1단계: 계획 수립 ============================
# 아무것도 바꾸지 않는다. 무엇을 바꿔야 하는지만 조사한다.

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
Get-ChildItem $agentSrc -Filter *.md | ForEach-Object {
    $targets += @{ From = $_.FullName; To = Join-Path $dst "agents\$($_.Name)" }
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
        # Repo 를 달아 둔다 — 실행 단계가 **밀기 전에 그 저장소를 당길** 근거다.
        # 홈 대상에는 안 단다: ~/.claude 는 git 밖이라 당길 것도 더러워질 것도 없다.
        $targets += @{ From = $bootSrc; To = Join-Path $repoRoot $bootFile; Repo = $repoRoot }
    }
}

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

# 프로젝트별 메모리: memory/<project>/*.md -> ~/.claude/projects/<슬러그>/memory/
if (Test-Path $memSrc) {
    foreach ($proj in (Get-ChildItem $memSrc -Directory)) {
        $memDsts = Get-ProjectMemDst $proj.Name
        if ($memDsts.Count -eq 0) {
            # 조용히 넘어가지 않는다 — 배포된 줄 알고 있으면 어긋난 것을 나중에야 안다
            $todo += "memory/$($proj.Name)/ 배포 안 됨 — 이 PC의 대상 폴더를 못 찾음. deploy.targets.d/ 의 [memory:$($proj.Name)] 확인"
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

# 사내 환경 문서와 씨앗 둘: posco/** · seeds/gateway/** · seeds/check/** -> ~/.claude/ 아래 같은 이름
# ⚠ **왜 홈에도 두나** — 이 둘의 진본은 저장소이고, 스킬·형제 저장소 문서가 그 좌표를
#   가리킨다. 그런데 설치본만 받은 사람에게는 저장소가 없어 그 좌표가 아예 없다. 그래서
#   설치(`install.ps1` 7 칸)가 홈에 깔고, 이 자리가 그 사본을 진본과 맞춘다 —
#   깔아만 두고 갱신을 안 하면 사본이 조용히 낡는다.
#   목록은 폴더가 든다. 파일이 늘어도 이 파일은 그대로 둔다.
# ⚠ **설정 저장소 씨앗(`seeds\config-repo`)은 여기서 안 민다.** 이 저장소가 그 폴더에
#   들고 있는 것은 **사람이 쓴 선언뿐**이다 — 안내문 · `bootstrap.conf` 견본 · 배포 대상
#   견본. 씨앗의 **몸통은 이 저장소 뿌리의 진본에서 굽는다**(뿌리의 `bootstrap-vdi.sh` ·
#   `deploy.ps1` · 훅 둘이 그것이고, 굽는 규약은 `dist.manifest.conf` 가 든다) — 그래서
#   **완본은 배포본에만 한 벌로 선다.** 여기서 밀면 홈에 **몸통 없는 골든**이 서는데, 그
#   반쪽이 안내문을 달고 있어 **완본처럼 보인다** — 부재보다 나쁘다.
#   홈에 완본을 까는 자는 설치본(`install.ps1` 의 씨앗 칸)이다.
foreach ($pair in @(
        @{ Src = 'posco';             Dst = 'posco' }
        @{ Src = 'seeds\gateway';     Dst = 'seeds\gateway' }
        @{ Src = 'seeds\check';       Dst = 'seeds\check' })) {
    $aSrc = Join-Path $src $pair.Src
    if (-not (Test-Path $aSrc)) { continue }
    # ⚠ **파이썬이 남긴 캐시는 안 민다.** 씨앗의 검사를 돌리면 `__pycache__\` 가 생기는데 git 은
    #   무시해도 이 복사는 모른다 — 실측 2026-09-12: 프로브를 돌린 직후 배포가 `.pyc` 일곱을 홈에
    #   깔았다. 그것은 자산이 아니라 그 PC 의 부산물이다.
    foreach ($f in (Get-ChildItem $aSrc -Recurse -File | Where-Object { $_.FullName -notmatch '\\__pycache__\\' })) {
        $rel = $f.FullName.Substring($aSrc.Length + 1)
        $targets += @{ From = $f.FullName; To = Join-Path $dst "$($pair.Dst)\$rel" }
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
                 (& git -C $src rev-parse --short HEAD 2>$null)
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
$mcpFile  = Join-Path $src 'mcp-servers.json'
$wantMcp  = @()
if (Test-Path $mcpFile) {
    # 종료 코드만 본다. 출력은 버린다 — 산문을 읽기 시작하면 위의 까닭으로 되돌아간다.
    # bash 를 거치는 것은 이 파일의 확립된 방식이다: npm shim 이 제 자리를 Git 설치 폴더
    # 기준으로 잘못 풀어, PowerShell 에서 곧장 부르면 자리에 따라 깨진다.
    #
    # ⚠ **「못 물었다」와 「등록 안 됨」을 섞지 않는다.** claude 에 안 닿을 때의 127 을
    #   「없다」로 읽으면 이미 등록된 것을 다시 등록하러 들고, 실패하면 빨갛게 보고한다.
    #   맨바닥 PC 의 첫 부트스트랩이 바로 그 자리다 — npm 전역 폴더가 PATH 에 없어 배포가
    #   띄운 bash 가 claude 를 못 찾았다 (bootstrap-vdi.sh 3/7 의 재배선이 그 짝이다).
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
        #   한 번도 안 돌았다 (실측 2026-09-07 · 맨바닥 VDI 첫 부트스트랩에서
        #   저장소 배포·홈 규범·부트스트랩이 전부 안 선 채 「완료」가 찍혔다).
        #   위 `$canAskMcp` 프로브가 이미 쓰는 꼴이다 — 두 프로브를 같은 꼴로 둔다.
        [System.IO.File]::WriteAllText($probe, "claude mcp get $name >/dev/null 2>&1`n", (New-Object System.Text.UTF8Encoding($false)))
        & $bash $probe *> $null
        $code = $LASTEXITCODE
        Remove-Item $probe -Force -ErrorAction SilentlyContinue
        if ($code -eq 127) { return $null }     # 셸이 claude 를 못 찾았다 — 답이 아니다
        return ($code -eq 0)
    }

    foreach ($p in ((Get-Content $mcpFile -Raw | ConvertFrom-Json).mcpServers.PSObject.Properties)) {
        $wantMcp += $p.Name
        $isReg = Test-McpRegistered $p.Name
        if ($null -eq $isReg) {
            # 못 물었으면 「등록됐다」고도 「아니다」고도 하지 않는다. 침묵하지도 않는다.
            $todo += "MCP $($p.Name) 등록 여부를 못 물었다 (claude 에 안 닿는다 — Git Bash 나 npm 전역 PATH 를 본다) — 확인:  claude mcp get $($p.Name)"
        } elseif ($isReg) {
            $same += "= 등록됨  MCP $($p.Name)"
        } else {
            $plan += @{
                Kind = 'mcp'; Name = $p.Name
                Json = ($p.Value | ConvertTo-Json -Compress -Depth 10)
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
    $claudeJson = Join-Path $HOME '.claude.json'
    if (Test-Path $claudeJson) {
        try {
            $reg = (Get-Content $claudeJson -Raw | ConvertFrom-Json).mcpServers
            if ($reg) {
                foreach ($n in @($reg.PSObject.Properties.Name)) {
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
    # ⚠ `2>$null` 은 방패가 아니다 (까닭은 `Sync-RepoOnce` 머리에 있다) — 잡아서 넘긴다.
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

# --- 저장소 부트스트랩 ---
# 게이트가 부르는 도구(링크 검사기·commitlint·파이썬 의존성)를 깐다.
#
# 왜 여기가 그 자리인가: 이 스크립트가 `git pull` 다음에 **항상** 도는 유일한 자리다.
# 도구가 없으면 게이트는 그 검사만 건너뛰고 커밋을 통과시키므로, 새 도구가 늘어난 것을
# 아무도 모른 채 몇 달이 간다. 여기서 깔면 한쪽에서 늘린 것이 다음 배포에 따라온다.
#
# 무엇을 깔지는 이 스크립트가 모른다 — 각 저장소의 훅이 안다. 그래서 도구 이름이
# 여기 없고, 저장소가 늘어도 이 파일은 안 고친다.
#
# 계획 단계에서는 `--check` 로 **재기만** 한다(아무것도 안 바꾼다). 꺼진 검사가 있을
# 때만 실행 목록에 올린다 — 다 살아 있으면 매번 승인을 묻지 않는다. **다만 잰 것은
# 초록이어도 화면에 낸다** — 안 묻는 것과 안 재는 것은 다른 명제다(아래 ⚠).
foreach ($repoRoot in $globalRuleTargets) {
    $boot = Join-Path $repoRoot '.claude\hooks\session-start.sh'
    if (-not (Test-Path $boot)) { continue }
    if (-not $bash) {
        $todo += "Git Bash 를 못 찾음. 직접 실행:  bash '$boot' --install"
        continue
    }
    # ⚠ **훅이 찍은 진단을 안 버린다.** 훅은 무엇을 쟀고 무엇이 사는지 stdout 으로 다 내는데,
    #   옛 판은 그것을 `Out-Null` 로 버리고 종료코드만 받아 「= 게이트 도구 갖춤」 한 줄로
    #   접었다. 그 한 줄마저 파일 목록과 같은 통(`$same`)에 들어가 개수에만 잡혀, **다 초록인
    #   기계에서는 화면에 자국이 하나도 안 남았다** — 「안 쟀다」와 구별이 안 된다 (실측
    #   2026-09-11 · 사내 PC: 저장소 다섯이 다 초록이라 이 칸이 통째로 안 보였다).
    $gate   = & $bash ($boot -replace '\\', '/') --check
    $gateRc = $LASTEXITCODE
    if ($gate) { $gateReport += $gate }
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
        # ⚠ `2>$null` 은 방패가 아니다(`Sync-RepoOnce` 머리) — 403 한 줄이 배포를 통째로 죽였다
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
    # ⚠ 초록이어도 `$same` 에 한 줄을 또 두지 않는다 — 위 블록이 이미 그 말을 했다.
    # ⚠ **진단은 그 저장소에 지금 있는 선언으로 잰다 — 복사는 아직 안 됐다.** 도구 선언
    #   (`tools.global.conf`)이 이번 배포에서 바뀌면 새 도구는 이 진단에 아예 안 나와 초록이
    #   서고, 부트스트랩이 안 올라 **배포를 두 번 돌려야 깔렸다**(실측 2026-09-12 · ruff: 첫 판은
    #   그 줄이 없었고 둘째 판이 깔았다). 그래서 선언을 덮는 복사가 계획에 있으면 진단과 무관하게
    #   올린다 — 실행은 계획 순서라 복사(앞)가 부트스트랩(여기)보다 먼저 돈다.
    $declChanges = @($plan | Where-Object {
        $_.Kind -eq 'copy' -and $_.Repo -eq $repoRoot -and $_.To -like '*\.claude\tools.global.conf' })
    if ($gateRc -ne 0 -or $declChanges.Count -gt 0) {
        $why = if ($gateRc -ne 0) { '꺼진 검사가 있다 — 도구를 깐다' } else { '도구 선언이 바뀐다 — 새 선언으로 깐다' }
        $plan += @{
            Kind = 'bootstrap'; Repo = $repoRoot; Script = $boot
            Text = "+ 부트스트랩  $repoRoot  ($why)"
        }
    }
}

# --- 제거 후보: 원본에 없는 에이전트 파일 ---
$agentDst = Join-Path $dst 'agents'
if (Test-Path $agentDst) {
    $keep = (Get-ChildItem $agentSrc -Filter *.md).Name
    Get-ChildItem $agentDst -Filter *.md | Where-Object { $keep -notcontains $_.Name } | ForEach-Object {
        $prunable += @{ Kind = 'remove'; Path = $_.FullName; Text = "- 제거  $($_.FullName)  (agents/에 없음)" }
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
    $keep = @(Get-ChildItem $skillSrc -Recurse -File |
        ForEach-Object { $_.FullName.Substring($skillSrc.Length + 1) } |
        Where-Object { $localSkills -notcontains ($_ -split '\\')[0] })
    Get-ChildItem $skillDst -Recurse -File |
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

# tavily 는 위에서 안 뽑힌다 — 설정에 ${} 가 없고 서버가 프로세스 환경에서 직접 읽어가므로
# 진본이 이름을 들지 않는다. 뽑을 자리가 없어 여기 명시한다.
if (-not [Environment]::GetEnvironmentVariable('TAVILY_API_KEY', 'User')) {
    $todo += 'Tavily 키 설정 — 별도 터미널에서:  setx TAVILY_API_KEY "실제키값"'
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

# 게이트 진단 — **「바꿀 것이 없습니다」 앞이다.** 뒤에 두면 다 초록인 기계에서 그 return 에
# 걸려 영영 안 보인다 — 이 칸이 가장 필요한 자리가 바로 거기다. 줄은 훅이 쓴 그대로 낸다.
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

# ── 저장소를 이번 실행에 한 번만 당긴다 — **배포본을 밀기 전에** (docs/decisions 이슈 18) ──
#    왜 밀기 전인가: 뒤처진 저장소에 새 진본이 앉으면 그것이 M 이 되고, 다음 세션의 훅
#    당김(`pull --ff-only`)이 그 M 에 막힌다. 한 번 막히면 사람이 되돌리기 전까지 안
#    풀린다 — **배포가 다음 배포를 막는 고리다.** 실측 2026-09-09 회사 PC: 훅이
#    `error: Your local changes … would be overwritten by merge` 로 두 번 졌다.
# ⚠ **못 당기면 안 민다.** 밀어 봐야 그 저장소는 pull 이 막힌 채 트리만 더 더러워진다 —
#   고리를 끊으려는 자리에서 고리를 한 바퀴 더 돌리는 꼴이다.
# ⚠ main 위에서만 당긴다 — 작업 중인 브랜치를 건드리지 않는다(훅 `pull_ff` 와 같은 자).
# ⚠ **리다이렉트가 곧 위험이다** — 이 파일에서 가장 되묻기 쉬운 자리라 여기 적어 둔다.
#   이 스크립트는 `$ErrorActionPreference = 'Stop'` 을 든다. 그 아래에서 파워셸 5.1 은
#   네이티브의 stderr 를 **파워셸이 건드릴 때만** `NativeCommandError` 로 감싸고, 그것이
#   종료 오류가 되어 배포를 통째로 죽인다. 실측 2026-09-10 로 갈린 두 편:
#     · 죽는다 — `2>$null` · `2>$파일` · `2>&1` · `*> $null`  (넷 다 방패가 아니다)
#     · 안 죽는다 — 리다이렉트를 아예 안 한 자리. stderr 가 콘솔로 흘러 오류 기록이 안 난다
#                   (`| Out-Null` 이나 값으로 받는 것도 stdout 쪽이라 안전하다)
#   옛 판은 `2>$파일` 을 방패로 믿었고, 그래서 아래 「못 당김」 갈래는 **한 번도 안 돌았다**
#   — 저장소 하나의 로컬 수정이 배포 전체를 죽였다 (실측 2026-09-09 · 사내 PC ·
#   deploy 가 exit 1 로 끝나고 뒤의 배포·MCP 가 다 남았다).
# ⚠ 그래서 **자식으로 띄운다.** `Start-Process -Wait` 는 stderr 를 파워셸에 안 태우고 파일에
#   바로 붓는다 — 파워셸이 볼 것이 없으니 승격될 것도 없다. `-Wait` 를 걸면 종료코드도
#   제대로 든다. `ErrorActionPreference` 를 잠깐 내리는 길도 살긴 하는데, 그러면 파일에
#   담기는 것이 git 의 말이 아니라 **파워셸이 꾸민 오류 기록**이라 아래 사유 고르기가
#   `Aborting` 을 집는다 — 바로 그 주석이 막으려던 자리다.
# ⚠ 이 고침은 **순서만 바로잡는다.** 진본이 바뀌면 형제 저장소의 배포본 커밋도 같은 판에
#   나가야 하고(`chore(claude): 훅 배포본을 진본과 다시 맞춘다`), 안 나가면 당겨도
#   뒤처진 채라 M 이 다시 뜬다 — 그리고 그 M 은 맞다.
$pulledRepos = @{}
function Sync-RepoOnce($repo) {
    if ($pulledRepos.ContainsKey($repo)) { return $pulledRepos[$repo] }
    $ok = $true
    if (Test-Path (Join-Path $repo '.git')) {
        # ⚠ `2>$null` 은 위에 적은 대로 방패가 아니다 — 여기서는 잡아서 넘긴다.
        #   HEAD 를 못 읽으면 「main 이 아니다」와 같은 값이라 그 갈래로 떨어뜨린다.
        try { $head = (& git -C $repo symbolic-ref --short -q HEAD 2>$null) }
        catch { $head = '' }
        if ($head -ne 'main') {
            # ⚠ **당길 수 없는 저장소에도 안 민다** — 못 당긴 자리와 같은 값이다. 여기 밀면
            #   그 M 은 사람이 main 으로 돌아온 뒤의 당김을 막는다. 「지금 안 막혔다」가
            #   아니라 「나중에 막힐 것을 안 만든다」가 이 게이트의 뜻이다.
            Write-Host "· 당김 건너뜀  $repo  (main 이 아니라 '$head')" -ForegroundColor DarkGray
            $ok = $false
        } else {
            $errFile = [System.IO.Path]::GetTempFileName()
            $outFile = [System.IO.Path]::GetTempFileName()
            $git = Start-Process -FilePath 'git' `
                     -ArgumentList @('-C', $repo, 'pull', '--ff-only', '-q') `
                     -NoNewWindow -Wait -PassThru `
                     -RedirectStandardError $errFile -RedirectStandardOutput $outFile
            $code = $git.ExitCode
            $out  = (Get-Content $errFile -Raw -ErrorAction SilentlyContinue)
            Remove-Item $errFile, $outFile -Force -ErrorAction SilentlyContinue
            if ($code -ne 0) {
                # 사유를 고르는 자는 훅 `git_why` 와 같은 결이다 — 끝줄이 아니라 첫
                # `fatal:`/`error:` 줄이다. 로컬 수정 갈래는 끝줄이 `Aborting` 이라
                # 끝줄을 집으면 사유가 있는데 층이 안 갈린다.
                $lines = @(($out -split "`r?`n") | Where-Object { $_.Trim() })
                $why   = @($lines | Where-Object { $_ -match '^(fatal|error):' })[0]
                if (-not $why) { $why = $lines[-1] }
                if (-not $why) { $why = '사유가 안 나왔다' }
                Write-Host "! 못 당김  $repo — $($why.Trim())" -ForegroundColor Red
                $ok = $false
            } else {
                Write-Host "↓ 당김  $repo" -ForegroundColor DarkGray
            }
        }
    }
    $pulledRepos[$repo] = $ok
    return $ok
}

Write-Host ""
foreach ($step in $plan) {
    switch ($step.Kind) {

        'copy' {
            # 저장소 배포본은 그 저장소를 당긴 뒤에 민다. 못 당겼으면 안 민다 (위 Sync-RepoOnce).
            $skip = $false
            if ($step.Repo -and -not (Sync-RepoOnce $step.Repo)) {
                Write-Host "· 건너뜀  $($step.To)  (그 저장소를 지금 못 맞춘다 — 까닭은 위 줄. 밀면 다음 당김이 막힌다)" -ForegroundColor Yellow
                $skip = $true
            }
            # 계획은 **당기기 전** 트리를 보고 섰다 — 당김이 진본을 이미 앉혔을 수 있으니
            # 여기서 한 번 더 묻는다. 같은 것을 다시 쓰면 백업만 쌓이고 얻는 것이 없다.
            if (-not $skip -and (Test-Path $step.To) -and
                ((Get-FileHash $step.From).Hash -eq (Get-FileHash $step.To).Hash)) {
                Write-Host "= 동일  $($step.To)  (당긴 뒤 같아졌다)" -ForegroundColor DarkGray
                $skip = $true
            }
            if (-not $skip) {
                if (Test-Path $step.To) { Save-Backup $step.To }
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

        'bootstrap' {
            # Git Bash 로 돌린다. PATH 의 bash 는 WSL 일 수 있어 $bash 를 그대로 쓴다.
            # 경로는 슬래시로 바꿔 넘긴다 — 역슬래시는 bash 가 이스케이프로 먹는다.
            # 훅이 진단을 그대로 찍으므로 여기서 한 번 더 판정하지 않는다.
            & $bash ($step.Script -replace '\\', '/') --install
            if ($LASTEXITCODE -ne 0) {
                # ⚠ **여기가 목표를 이뤘나를 아는 유일한 자리다.** 훅은 `--install` 에서도
                #   꺼진 검사를 종료코드로 낸다 — 그 신호를 여기서 받아 위층까지 물고 가지
                #   않으면 검사가 꺼진 채로 화면이 초록으로 끝난다 (실측 2026-09-10 · VDI 넷).
                Write-Host "! 부트스트랩이 오류로 끝났습니다 (exit $LASTEXITCODE)  $($step.Repo)" -ForegroundColor Red
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
            # ⚠ **`2>&1` 을 뗐다 — 그것이 위험을 만들던 자였다** (까닭은 `Sync-RepoOnce`
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
        }
    }
}

if (Test-Path $backup) { Write-Host "`n백업: $backup" }

if ($todo.Count -gt 0) {
    Write-Host "`n남은 수동 작업:" -ForegroundColor Yellow
    $todo | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}

# ── 판정 — **환경이 안 섰으면 「완료」라고 말하지 않는다** ─────────────────
# ⚠ 옛 판은 무엇이 지든 초록 「완료」로 끝나고 종료코드도 늘 0 이었다. 그래서 이 스크립트를
#   부르는 자(`bootstrap-vdi.sh` → `install.ps1` → 설치 화면)는 **물어볼 데가 없었다** —
#   부트스트랩이 꺼진 검사를 안고 끝나도 화면은 초록이었다 (실측 2026-09-10 · 사내·사외 VDI).
if ($envDown.Count -gt 0) {
    Write-Host "`n! 실행 환경이 안 섰습니다 — $($envDown.Count)곳:" -ForegroundColor Red
    $envDown | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "`n끝내지 못했습니다. 위 진단의 까닭을 고친 뒤 다시 돌립니다." -ForegroundColor Red
    exit 1
}

Write-Host "`n완료. Claude Code를 재시작해야 적용됩니다." -ForegroundColor Green
