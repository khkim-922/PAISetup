# claude-config -> 이 PC 에 배포 — 진본을 홈 · 형제 저장소 · 도구 홈에 맞추고, 저장소 훅을 불러 도구를 깐다
#
# 부르는 꼴
#   .\deploy.ps1                  무엇을 할지 보여주고 승인받은 뒤 실행
#   .\deploy.ps1 -Prune           배포 + 제거. 원본에 없는 씨앗 · 메모리 파일을 걷는다
#   .\deploy.ps1 -Yes             승인 없이 실행 (자동화용)
#   .\deploy.ps1 -ShowUnchanged   이미 맞는 것까지 한 줄씩 편다 (어긋난 것을 찾을 때만)
#   git 이 옮기는 것은 파일뿐이라 `git pull` 다음에 이것을 돌려야 적용된다.
#
# 내는 것 — 걸음마다 한 줄 · 남은 수동 작업 · 판정. 실행 환경이 안 선 것(`$envDown`)이 남으면 종료 값 1 로 끝난다.
#   바꿀 것이 없거나 승인이 안 서면 아무것도 안 바꾸고 돌아간다 — 당김만은 승인 앞에서 이미 돌았다.
#
# 하는 일 — 차례대로
#   당김 — 형제 저장소를 원격 쪽으로 맞춘다(main 위에서만 · 빨리감기로만 · 저장소마다 판정 한 줄 · 어디까지는 세션 훅
#     몸통의 `--pull-target` 이 정한다 — 원격 끝, 저장소가 당김 문을 두었으면 그 문이 고른 커밋). 빨리감기를 막는 것이 이 배포가
#     전에 심은 사본뿐이면 그것을 걷고 당긴다. 계획과 설치 판정이 지문을 보므로 계획 앞에 서고(밀 것이 없는 회차에도 돈다),
#     져도 던지지 않는다
#   배선 — .githooks/ 를 둔 저장소에 core.hooksPath 를 건다(git 훅은 clone 을 안 따라온다). 바꾸는 걸음 가운데 맨 앞이다 —
#     뒤가 무엇으로 죽든 커밋 게이트만은 서야 한다(아래 「실행 순서」 칸)
#   배포 — 진본을 홈과 형제 저장소로 민다. 무엇이 어디로 가나의 표는 `docs/deploy-targets.md` 가 든다(여기 옮겨 적지 않는다).
#     목록의 진본은 선언 둘 — deploy.repofiles.conf(저장소로 가는 파일) · deploy.seeds.conf(홈으로 폴더째) — 이고, 어느
#     저장소 · 슬러그로 가나는 personal.conf 의 REPOS · ROOT 에서 파생한다 — 새 PC 가 적을 것 없이 선다
#   도구 홈 — 규범 · 룰 · 에이전트 · 스킬은 손 하나(`.claude/hooks/tool-homes.py`)가 갈 곳 표대로 놓는다. 이 스크립트는 손을
#     부르고 손이 바꿀 줄을 계획에 싣는다 — 놓는 손이 하나라 설치 · 배포 · 세션 훅이 따로 놓다 어긋나지 않는다
#   설치 — 전역 설치 한 번(이 저장소 훅의 `--install-global` · npm 전역 · 릴리스 바이너리 · winget · 브라우저) 다음에
#     저장소마다(각 저장소 훅의 `--install` · 프로젝트 축(venv · npm ci)과 배선). 무엇을 깔지는 훅이 알고 이 스크립트는 모른다
#   사용자 환경변수 — 이 PC 전체에 걸려야 하는 인코딩 값(아래 「사용자 환경변수」 칸)
#   남은 수동 작업 안내 (API 키 등)
#
# 이름이 같아 헷갈리는 자리 하나 — ~/.claude/settings.json 은 홈의 개인 설정(모델 · 테마 등)이라 PC 마다 달라 손으로 둔다.
#   저장소의 .claude/settings.json 은 훅 등록 파일이라 배포한다.
#
# 기본 실행이 걷는 것은 우리 것이라는 기록이 있는 것뿐이다 — 홈 씨앗 · 사내 환경 문서는 이 저장소 이력이 그 자리에서 지운 파일을
# (`Get-SeedColumn`), 규범 · 룰 · 에이전트 · 스킬은 손이 제가 놓았다고 기록한 것을(손의 머리말) 걷는다. 형제 저장소에 커밋 안 된 채
# 남아 당김을 막는 사본은 내용이 이 저장소 이력의 어느 판과 바이트로 같을 때만 되돌리거나 지운다(`Clear-PlantedCopies`). 회사 PC 의 DRM 이
# 감싸 당김을 막는 오피스 · PDF 는 감싼 판을 백업하고 커밋본으로 되돌린다(`Clear-DrmWrapped` — 판정은 세션 훅 몸통). 기록 없이 원본에만 없는
# 씨앗 · 메모리 파일은 -Prune 을 줄 때만 걷고, 기본 실행에서는 후보만 알린다.
# 이미 맞는 것은 건드리지 않아 몇 번을 돌려도 안전하다. 덮거나 걷는 파일은 ~/.claude/backups/deploy-<시각>/ 에 원본을
# 남기고, 손이 덮거나 걷는 것은 손이 제 백업 자리에 남긴다. 당김이 걷는 사본만은 안 남긴다 — 그 내용은 진본 커밋에 바이트로 있고
# `↺` 줄이 그 커밋을 댄다.

param([switch]$Yes, [switch]$Prune, [switch]$ShowUnchanged)

$ErrorActionPreference = 'Stop'

# 걸음 종류별 초(`$stepSecs`)를 재는 시계 — 기준이 실행 내내 한 자리여야 해서 머리에 둔다.
$deploySw = [Diagnostics.Stopwatch]::StartNew()

# 콘솔 출력을 UTF-8 로 고정한다 — PowerShell 5.1 기본은 시스템 코드페이지(한국은 cp949)라 이 스크립트의 한글이 깨진다.
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

#region 라이브러리 — 흐름이 부르는 함수는 다 여기 선다. 정의만 있고 도는 문장은 없다

#region 메모리 자리 손 — 경로에서 메모리 슬러그를 짓고, `memory/<이름>/` 이 이 PC 에서 갈 자리를 고른다
function ConvertTo-Slug([string]$Path) { $Path -replace '[^A-Za-z0-9]', '-' }

# memory/<이름>/ 이 이 PC 에서 갈 자리 — 받는 것: 메모리 이름 · 내는 것: 자리 하나를 든 배열이나 빈 배열 · `$memTargets` ·
#   `$dst` 를 읽는다. 딸린 폴더가 있으면 슬러그 폴더가 아직 없어도 간다(복사가 세운다 — 곁에 붙이기만 하던 저장소는
#   Claude Code 가 그 폴더를 안 세운다). `$memTargets` 에 없는 이름, 그리고 딸린 폴더도 슬러그 폴더도 없는 자리(적었지만
#   아직 안 받은 저장소)는 비운다 — 없는 저장소의 슬러그 폴더를 새로 세우지 않는다.
# ⚠ 슬러그는 실제 경로 글자(`Resolve-Path`)에서 짓는다 — 제품도 그 글자로 짓는다.
function Get-ProjectMemDst($project) {
    $home_ = $memTargets[$project]
    if (-not $home_) { return @() }
    $slug = if (Test-Path $home_) { ConvertTo-Slug (Resolve-Path $home_).Path } else { ConvertTo-Slug $home_ }
    if (-not (Test-Path $home_) -and -not (Test-Path (Join-Path $dst "projects\$slug"))) { return @() }
    @(Join-Path $dst "projects\$slug\memory")
}
#endregion 메모리 자리 손

#region 당김 손 — git 을 자식으로 띄우고 기다리고 거두는 손과, 저장소마다 판정을 내는 `Sync-Repos`. 왜 계획 앞에 도나는 흐름의 「당김」이 든다
# ⚠ `pull` 이 아니라 `fetch` + `merge --ff-only` 다 — `pull` 은 저장소당 한 장인 `FETCH_HEAD` 로 병합 대상을 정해, 같은 순간
#   다른 git(VS Code 로 연 세션의 훅 당김)이 끼면 `fatal: Cannot fast-forward to multiple branches.` 로 진다. `merge` 에 이름
#   있는 자리(추적 갈래)를 주면 남이 그 파일에 무엇을 쓰든 무관하다.
# ⚠ refspec 을 두 칸 다 적는다 — 한 갈래만 받게 클론된 저장소는 `fetch <원격> main` 이 추적 갈래를 안 옮기고 `FETCH_HEAD` 만
#   써서, 아무것도 안 전진했는데 성공으로 끝난다(훅 `sync_main` 의 같은 규율).
# fetch 는 저장소마다 동시에 띄우고 merge 는 다 끝난 뒤 차례로 한다 — 저장소가 다르면 `FETCH_HEAD` 도 다른 파일이라 fetch
#   끼리는 안 겹치고, 한 곳이 느려도 나머지를 안 막는다. 작업 나무를 옮기는 `merge` 는 차례로 둔다.
# ⚠ 리다이렉트가 곧 위험이다 — 이 스크립트는 `$ErrorActionPreference = 'Stop'` 을 들고, 그 아래에서 파워셸 5.1 은 네이티브의
#   stderr 를 파워셸이 건드릴 때만 `NativeCommandError` 로 감싸 종료 오류로 만든다 — 배포가 통째로 죽는다.
#     · 죽는다 — `2>$null` · `2>$파일` · `2>&1` · `*> $null`  (넷 다 방패가 아니다)
#     · 안 죽는다 — 리다이렉트를 아예 안 한 자리(stderr 가 콘솔로 흐른다) · `| Out-Null` 이나 값으로 받는 stdout
#   그래서 리다이렉트하는 네이티브 호출은 `try`/`catch` 로 감싸고, 당김의 git 은 자식으로 띄워 stderr 를 파이프로 받는다
#   (`Start-GitChild` — 파워셸이 볼 것이 없으니 승격될 것도 없다). `$ErrorActionPreference` 를 잠깐 내리는 길은 안 쓴다 —
#   그러면 파일에 담기는 것이 git 의 말이 아니라 파워셸이 꾸민 오류 기록이라 `Get-GitWhy` 가 `Aborting` 을 사유로 집는다.
function Get-GitWhy($file) {
    # git 의 stderr 파일 → 사유 한 줄. 첫 `fatal:`/`error:` 줄이고, 없으면 끝줄, 그것도 없으면 「사유가 안 나왔다」다(훅
    #   `git_why` 와 같은 자). 끝줄을 먼저 안 집는다 — 로컬 수정 갈래는 끝줄이 `Aborting` 이라 사유가 안 갈린다.
    #   파일은 자식이 낸 바이트 그대로라 UTF-8 로 읽는다 — 파워셸 5.1 의 기본(시스템 코드페이지)으로 읽으면 몸통의 한국어 사유가 깨진다.
    $raw   = (Get-Content $file -Raw -Encoding UTF8 -ErrorAction SilentlyContinue)
    $lines = @(("$raw" -split "`r?`n") | Where-Object { $_.Trim() })
    $why   = @($lines | Where-Object { $_ -match '^(fatal|error):' })[0]
    if (-not $why) { $why = $lines[-1] }
    if (-not $why) { $why = '사유가 안 나왔다' }
    return "$why".Trim()
}

function Start-GitChild($gitArgs, $exe) {
    # git 하나를 자식으로 띄우기만 한다 — 기다리는 꼴이 둘(fetch 는 묶음 · merge 는 하나씩)이라 기다리기는 부르는 쪽이,
    #   거두기는 `Complete-GitChild` 가 한다. 받는 것: git 인자 배열 · (선택) 실행 파일 — 주면 git 대신 그것을 같은 규율로
    #   띄운다(몸통을 부르는 Git Bash) · 내는 것: @{ Proc; Err; Out; Pump; Sink } · 못 띄웠으면
    #   @{ Why = 사유 } · 부작용: 임시 파일 둘(stdout · stderr)을 세운다.
    # ⚠ `Start-Process -PassThru` 로 띄우지 않는다 — 그것이 주는 Process 는 손잡이를 안 쥐어, 손잡이를 잡기 전에 자식이 끝나면
    #   `ExitCode` 가 빈 값이다. 할 일 없는 fetch · merge 는 그 틈 안에 끝나 거짓 「못 당김 — 사유가 안 나왔다」로 떨어진다.
    #   `Process.Start` 는 띄우는 순간의 손잡이를 쥐어 틈이 없다.
    # ⚠ `cmd /c` 로 감싸 파일로 돌리지 않는다 — `Proc` 가 cmd 가 되어 `Stop-GitChild` 가 cmd 만 죽이고 git 은 남아 돈다.
    # 두 스트림은 파이프로 받고 `CopyToAsync` 가 파일에 붓는다(파워셸 스레드 없이 돌고, 늘 읽으니 파이프가 차서 자식이 서는
    #   일도 없다). 파일은 지우기를 허락해 연다 — 시간 초과 갈래는 `Complete-GitChild` 없이 파일을 지운다.
    # 인자는 한 줄로 싼다 — 빈 낱낱과 빈칸 · 따옴표가 든 낱낱만 MSVCRT 규칙으로 감싼다. 파워셸 5.1 의 .NET Framework 에
    #   `ProcessStartInfo.ArgumentList` 가 없어서다 — 7 에서만 돌게 되면 그것으로 간다.
    $errFile = [System.IO.Path]::GetTempFileName()
    $outFile = [System.IO.Path]::GetTempFileName()
    $sink = @()
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName  = if ($exe) { $exe } else { @(Get-Command git -CommandType Application -ErrorAction Stop)[0].Source }
        $psi.Arguments = (@($gitArgs) | ForEach-Object {
            if ("$_" -ne '' -and "$_" -notmatch '[\s"]') { "$_" }
            else { '"' + (("$_" -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"' }
        }) -join ' '
        $psi.UseShellExecute        = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $sink = @([System.IO.File]::Open($outFile, 'Create', 'Write', 'ReadWrite, Delete'),
                  [System.IO.File]::Open($errFile, 'Create', 'Write', 'ReadWrite, Delete'))
        $p = [System.Diagnostics.Process]::Start($psi)
        $pump = @($p.StandardOutput.BaseStream.CopyToAsync($sink[0]),
                  $p.StandardError.BaseStream.CopyToAsync($sink[1]))
        return @{ Proc = $p; Err = $errFile; Out = $outFile; Pump = $pump; Sink = $sink }
    } catch {
        foreach ($s in $sink) { $s.Dispose() }
        Remove-Item $errFile, $outFile -Force -ErrorAction SilentlyContinue
        return @{ Why = "git 을 못 띄웠다: $($_.Exception.Message.Split([char]10)[0].Trim())" }
    }
}

function Stop-GitChild($job) {
    # 한도를 넘긴 자식을 거둔다 — `Stop-Process -Force` 를 먼저, 안 되면 `.NET Kill()`. 던지지 않는다.
    # ⚠ `taskkill.exe` 에 매지 않는다 — 보안 소프트가 그 바이너리를 막는 PC 에서는 제 자식에게도 「액세스가 거부되었습니다」로
    #   실행 자체가 거부된다(부팅 라인 `scripts/startup-pipeline.ps1` 의 거두는 자도 같은 길이다).
    # 나무째 안 내려간다 — git 이 띄운 전송 도움꾼(`git-remote-https`)은 부모가 죽으면 파이프가 끊겨 제 발로 나가고, 다음
    #   회차는 당김을 새로 띄운다.
    try { Stop-Process -Id $job.Proc.Id -Force -ErrorAction Stop }
    catch { try { $job.Proc.Kill() } catch { } }
}

function Complete-GitChild($job) {
    # 끝난 자식의 종료코드 · 사유 한 줄 · stdout 을 읽고 임시 파일을 걷는다 — 내는 것: @{ Code; Why; Out }.
    # ⚠ Code 가 $null 이면 「못 쟀다」다 — 부르는 쪽이 0 으로 접지 않는다.
    # 붓기가 끝나야 파일이 다 찬다 — 자식이 끝나도 파이프의 꼬리는 그것을 쥔 손자까지 다 나가야 오므로 기다림에 한도를
    #   둔다. 넘기면 사유에서 꼬리만 빠지고 판정은 종료코드가 든다.
    $drainMs = 5000
    $code = $null
    try { $code = $job.Proc.ExitCode } catch { $code = $null }
    try { $null = [System.Threading.Tasks.Task]::WaitAll($job.Pump, $drainMs) } catch { }
    foreach ($s in $job.Sink) { try { $s.Dispose() } catch { } }
    $why = Get-GitWhy $job.Err
    $out = ''
    try { $out = [System.IO.File]::ReadAllText($job.Out) } catch { }
    Remove-Item $job.Err, $job.Out -Force -ErrorAction SilentlyContinue
    return @{ Code = $code; Why = $why; Out = $out }
}

function Invoke-GitWait($gitArgs, $timeoutSec, $exe) {
    # git 하나(`$exe` 를 주면 그것)를 띄워 한도(초) 안에서 기다린다 — 내는 것은 `Complete-GitChild` 와 같은
    #   @{ Code; Why; Out } 이고, 못 띄웠거나 한도를 넘기면(거두고 「시간 초과」) Code 가 $null 이다.
    $job = Start-GitChild $gitArgs $exe
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

function Get-PullTarget($repo, $remote) {
    # 당김이 멈출 커밋을 세션 훅 몸통에 묻는다(`--pull-target` · fetch 가 이긴 뒤). 받는 것: 저장소 · 원격 이름 · 읽는 것: 준비의
    #   `$bash` · `$src` · 내는 것: @{ Sha; Note } — Sha 는 병합할 커밋, Note 는 원격 끝 앞에 멈췄을 때만 서는 덧말. 원격 끝을
    #   못 읽으면 `!` 줄을 내고 $null(못 당김).
    # 저장소의 손(`.claude/hooks/pull-target.sh`)에 묻고 답을 재고 판정을 `.git/claude-pull-target.last` 에 적는 규칙은 몸통 한
    #   자리에 산다 — 세션 당김 · 부팅 라인도 같은 자리를 부른다. 여기 옮겨 적으면 한쪽이 바뀌는 날 이 당김만 다른 커밋에 선다.
    # 몸통을 못 부르거나 답을 못 믿으면 원격 끝으로 가고 그 까닭을 `!` 줄로 낸다 — 손이 없을 때와 같은 자리이고 몸통의 바닥도
    #   그것이다. 문이 못 선 것을 당김을 멈추는 것으로 갚으면 그 저장소는 영영 안 받는다.
    # ⚠ 몸통의 답을 다시 잰다 — sha 꼴이고 원격 끝의 조상(같아도 된다)이어야 받는다. 손의 답을 재는 규칙의 사본이 아니라 두
    #   프로세스 사이 약속의 확인이다: 몸통이 옛 판이거나 고장 나 원격 main 밖의 커밋을 내도 빨리감기는 그 커밋을 그대로 받는다.
    $t = Invoke-GitWait @('-C', $repo, 'rev-parse', '-q', '--verify', "refs/remotes/$remote/main^{commit}") $PullMergeTimeoutSec
    $tip = "$($t.Out)".Trim()
    if ($t.Code -ne 0 -or -not $tip) {
        Write-Host "! 못 당김  $repo — $remote/main 을 못 읽었다" -ForegroundColor Red
        return $null
    }
    $why = ''
    $body = Join-Path $src '.claude\hooks\session-start-body.sh'
    if (-not $bash) { $why = 'Git Bash 를 못 찾았다' }
    elseif (-not (Test-Path $body)) { $why = "몸통이 없다 ($body)" }
    else {
        # 경로는 슬래시로 넘긴다 — 역슬래시는 bash 가 이스케이프로 먹는다
        $a = Invoke-GitWait @(($body -replace '\\', '/'), '--pull-target', ($repo -replace '\\', '/'), $remote) `
                            $PullTargetTimeoutSec $bash
        $sha = "$($a.Out)".Trim()
        # 끝 값이 없으면($null) 못 띄웠거나 한도를 넘긴 것이다 — 사유가 그것을 말한다
        if ($a.Code -ne 0) { $why = "몸통이 답을 못 냈다 (끝 값 $(if ($null -eq $a.Code) { '없음' } else { $a.Code })): $($a.Why)" }
        elseif ($sha -cnotmatch '^[0-9a-f]{40}([0-9a-f]{24})?$') { $why = "몸통의 답이 sha 꼴이 아니다: '$sha'" }
        elseif ($sha -eq $tip) { return @{ Sha = $tip; Note = '' } }
        else {
            $c = Invoke-GitWait @('-C', $repo, 'merge-base', '--is-ancestor', $sha, $tip) $PullMergeTimeoutSec
            if ($c.Code -eq 0) { return @{ Sha = $sha; Note = " · 당김 문이 원격 끝 $($tip.Substring(0, 7)) 앞에 세웠다" } }
            $why = "몸통의 답 $sha 이 $remote/main 위에 없다"
        }
    }
    Write-Host "! 당김 문을 못 물었다  $repo — $why · 원격 끝으로 간다" -ForegroundColor Red
    return @{ Sha = $tip; Note = '' }
}

function Clear-PlantedCopies($repo, $sha) {
    # 당김을 막는 파일이 배포가 전에 심은 사본뿐이면 그것을 걷는다(#209). 받는 것: 저장소 · 병합할 커밋 · 읽는 것: `$src`(진본) ·
    #   `$repoFiles`(배포 목록) · `$PullMergeTimeoutSec` · 내는 것: @{ Cleared; Why } — Cleared 는 걷은 파일마다 @{ Path; Rev }
    #   (Rev 는 그 내용이 선 진본 커밋), Why 는 막는 파일을 두고 물러선 까닭이다. merge 는 안 한다 — 부른 쪽이 그대로 한다.
    # 막는 파일 — 들어올 커밋이 건드리는 파일 가운데 작업나무에서 바뀌었거나 git 이 모르는(untracked) 것. 들어올 커밋이 안
    #   건드리는 변경은 빨리감기를 안 막으니 보지도 않는다.
    # 우리 사본 — 배포 목록에 들고, 스테이징 안 된 채(배포는 스테이징을 안 한다) 내용이 진본 이력의 어느 판과 바이트로 같은 것.
    #   사람의 손질은 진본의 어느 판과도 안 맞는다. 해시는 진본의 줄끝 규칙으로 뜬다(`hash-object --path`) — 배포가 옮기는
    #   것은 진본 작업나무의 바이트라, 같은 규칙으로 떠야 진본 이력의 blob 과 견줄 수 있다.
    # ⚠ 하나라도 우리 것이 아니면 아무것도 안 걷는다 — 남은 하나가 어차피 당김을 막아, 걷기만 하고 전진은 못 한다.
    # ⚠ 들어올 판과 같게 덮어써서는 안 풀린다 — git 은 작업나무를 들어올 내용이 아니라 인덱스와 견준다. 그래서 고친 파일은
    #   되돌리고 untracked 파일은 지운다. 어느 쪽이든 그 내용은 진본 이력(Rev)에 남아 있다.
    # ⚠ 빨리감기가 설 때(HEAD 가 그 커밋의 조상일 때)만 본다 — 갈라진 나무는 걷어도 merge 가 지고, 진 저장소에는 `copy` 걸음이
    #   안 밀어 걷은 사본이 다시 안 선다. 나무가 앞서 있으면 merge 가 할 일이 없어 막을 것도 없다.
    $a = Invoke-GitWait @('-C', $repo, 'merge-base', '--is-ancestor', 'HEAD', $sha) $PullMergeTimeoutSec
    if ($a.Code -ne 0) { return @{ Cleared = @(); Why = "HEAD 가 $($sha.Substring(0, 7)) 의 조상이 아니라 빨리감기가 안 선다" } }
    $d = Invoke-GitWait @('-C', $repo, 'diff', '--name-only', '-z', '--no-renames', 'HEAD', $sha) $PullMergeTimeoutSec
    if ($d.Code -ne 0) { return @{ Cleared = @(); Why = "들어올 파일을 못 쟀다: $($d.Why)" } }
    $incoming = @("$($d.Out)" -split "`0" | Where-Object { $_ })
    if ($incoming.Count -eq 0) { return @{ Cleared = @(); Why = '' } }
    $s = Invoke-GitWait @('-C', $repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--no-renames') $PullMergeTimeoutSec
    if ($s.Code -ne 0) { return @{ Cleared = @(); Why = "작업나무를 못 쟀다: $($s.Why)" } }
    $dirty = @{}   # 경로 -> 두 글자 상태(XY)
    foreach ($e in @("$($s.Out)" -split "`0" | Where-Object { $_ })) { $dirty[$e.Substring(3)] = $e.Substring(0, 2) }
    $blockers = @($incoming | Where-Object { $dirty.ContainsKey($_) })
    if ($blockers.Count -eq 0) { return @{ Cleared = @(); Why = '' } }

    $ours = @()
    foreach ($p in $blockers) {
        $xy = $dirty[$p]
        if ($xy -ne ' M' -and $xy -ne '??') { return @{ Cleared = @(); Why = "$p 는 배포가 남기는 꼴이 아니다(상태 '$xy')" } }
        if ($repoFiles -notcontains ($p -replace '/', '\')) { return @{ Cleared = @(); Why = "$p 는 배포 목록 밖의 파일이다" } }
        $h = Invoke-GitWait @('-C', $src, 'hash-object', "--path=$p", '--', (Join-Path $repo $p)) $PullMergeTimeoutSec
        $blob = "$($h.Out)".Trim()
        if ($h.Code -ne 0 -or -not $blob) { return @{ Cleared = @(); Why = "$p 의 내용을 못 쟀다: $($h.Why)" } }
        $l = Invoke-GitWait @('-C', $src, 'log', '--format=%H', '--raw', '--no-abbrev', '--no-renames', '--', $p) $PullMergeTimeoutSec
        if ($l.Code -ne 0) { return @{ Cleared = @(); Why = "진본에서 $p 의 이력을 못 읽었다: $($l.Why)" } }
        # 이력은 새것부터 온다 — 커밋 줄 다음에 그 커밋이 남긴 blob 줄(`:<옛 모드> <새 모드> <옛 blob> <새 blob> <상태>`)이 선다
        $rev = ''; $at = ''
        foreach ($ln in ("$($l.Out)" -split "`n")) {
            if ($ln -match '^([0-9a-f]{40})\s*$') { $at = $Matches[1] }
            elseif ($ln -match '^:\S+ \S+ \S+ ([0-9a-f]{40}) ' -and $Matches[1] -eq $blob) { $rev = $at; break }
        }
        if (-not $rev) { return @{ Cleared = @(); Why = "$p 는 진본의 어느 판과도 안 맞는다 — 사람이 고친 것으로 본다" } }
        $ours += @{ Path = $p; Rev = $rev; Untracked = ($xy -eq '??') }
    }

    $done = @($ours | Where-Object { -not $_.Untracked })
    if ($done.Count) {
        $c = Invoke-GitWait (@('-C', $repo, 'checkout', '-q', '--') + @($done | ForEach-Object { $_.Path })) $PullMergeTimeoutSec
        if ($c.Code -ne 0) { return @{ Cleared = @(); Why = "사본을 되돌리지 못했다: $($c.Why)" } }
    }
    foreach ($o in @($ours | Where-Object { $_.Untracked })) {
        try { Remove-Item -LiteralPath (Join-Path $repo $o.Path) -Force -ErrorAction Stop }
        catch { return @{ Cleared = $done; Why = "$($o.Path) 를 지우지 못했다: $($_.Exception.Message)" } }
        $done += $o
    }
    return @{ Cleared = $done; Why = '' }
}

function Clear-DrmWrapped($repo, $sha) {
    # 빨리감기를 막는 파일이 다 DRM 이 감싼 사본이면 백업하고 커밋본으로 되돌린다. 받는 것: 저장소 · 병합할 커밋 · 읽는 것: 준비의
    #   `$bash` · `$src` · `$DrmClearTimeoutSec` · 내는 것: @{ Lines; Why } — Lines 는 되돌린 파일마다 몸통이 낸 줄(`<경로> — 감싼 판:
    #   <백업 자리>`), Why 는 안 되돌린 까닭(막는 것이 없거나 다 되돌렸으면 빈 값). merge 는 안 한다 — 부른 쪽이 그대로 한다.
    # 판정 · 백업 · 되돌리기는 세션 훅 몸통 한 자리(`--clear-drm`)에 산다 — 설치기의 설정 저장소 당김도 그 자리를 불러, 두 당김이 같은
    #   파일을 같은 까닭으로 되돌린다. 여기 옮겨 적으면 한쪽이 바뀌는 날 이 당김만 다른 파일을 버린다.
    # 몸통을 못 부르면 까닭만 남기고 지나간다 — 이 손이 없을 때와 같은 자리라 merge 가 git 의 사유로 진다.
    $body = Join-Path $src '.claude\hooks\session-start-body.sh'
    if (-not $bash) { return @{ Lines = @(); Why = 'Git Bash 를 못 찾았다' } }
    if (-not (Test-Path $body)) { return @{ Lines = @(); Why = "몸통이 없다 ($body)" } }
    $a = Invoke-GitWait @(($body -replace '\\', '/'), '--clear-drm', ($repo -replace '\\', '/'), $sha) $DrmClearTimeoutSec $bash
    $lines = @("$($a.Out)" -split "`r?`n" | Where-Object { $_ })
    if ($a.Code -eq 0) { return @{ Lines = $lines; Why = '' } }
    $why = if ($null -eq $a.Code) { "몸통이 답을 못 냈다: $($a.Why)" } else { $a.Why }
    return @{ Lines = $lines; Why = $why }
}

function Sync-Repos($repos) {
    # 받는 것: 저장소 뿌리 목록 · 내는 것: 없다 — 저장소마다 판정 한 줄(`↓ 당김` · `· 당김 건너뜀` · `! 못 당김`)을 반드시
    #   찍고, `$pulledRepos[<저장소>]` 에 「이번 회차에 밀어도 되나」를 적는다(`.git` 이 없는 저장소는 안 적는다). 던지지 않는다.
    #   「안 당겼다」가 조용하면 뒤처진 저장소를 아무도 모른다.
    # 묻는 자리를 비대화로 못 박는다 — 자동 실행에는 자격증명을 넣을 사람이 없어, 토큰이 죽었거나 자격증명이 비면 git 의
    #   도움꾼(GCM)이 창을 띄우려다 영영 안 끝난다. 아래 한도가 거두기는 하지만, 안 묻게 하면 git 이 그 자리에서 지고 사유
    #   한 줄을 남긴다.
    # ⚠ 그 두 이름(`GIT_TERMINAL_PROMPT` · `GCM_INTERACTIVE`)을 이 셸에 남기지 않는다 — 뒤의 걸음(gh · 저장소 설치)은 사람의
    #   자격증명을 쓸 수 있다. 옛 값을 쥐고 끝에서 되돌리고, 없던 이름은 다시 없앤다.
    $savedPrompt = $env:GIT_TERMINAL_PROMPT
    $savedGcm    = $env:GCM_INTERACTIVE
    $env:GIT_TERMINAL_PROMPT = '0'
    $env:GCM_INTERACTIVE     = 'Never'
    try {
        $fetches = @()
        foreach ($repo in $repos) {
            if (-not (Test-Path (Join-Path $repo '.git'))) { continue }
            # ⚠ `2>$null` 은 방패가 아니라 잡아서 넘긴다(당김 손 머리의 「리다이렉트가 곧 위험이다」). HEAD 를 못 읽으면
            #   「main 이 아니다」와 같은 갈래로 떨어진다.
            try { $head = (& git -C $repo symbolic-ref --short -q HEAD 2>$null) } catch { $head = '' }
            $head = "$head".Trim()
            if ($head -ne 'main') {
                # main 이 아닌 저장소에도 안 민다(못 당긴 자리와 같은 값) — 여기 밀면 그 M 이 사람이 main 으로 돌아온 뒤의
                #   당김을 막는다. 빈 값은 분리된 HEAD(rebase · 태그 체크아웃)이거나 HEAD 를 못 읽은 자리라 따로 적는다.
                $why = if ($head) { "main 이 아니라 '$head'" } else { '분리된 HEAD 이거나 읽지 못했다' }
                Write-Host "· 당김 건너뜀  $repo  ($why)" -ForegroundColor DarkGray
                $pulledRepos[$repo] = $false
                continue
            }
            # 원격 이름을 박지 않는다 — 추적 설정에서 읽는다(훅 `pull_ff` 와 같은 자리).
            try { $remote = (& git -C $repo config --get branch.main.remote 2>$null) } catch { $remote = '' }
            $remote = "$remote".Trim()
            if (-not $remote) {
                # 추적 원격이 없으면 당길 자리가 없다 — 이 저장소에도 안 민다.
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

        # ── 다 끝나기를 기다린다 — 묶음 전체에 벽시계 한도가 있다 ───────────────────
        # 동시에 돌므로 기다림은 보통 가장 느린 하나만큼이다. 한도를 넘기면 그때까지 안 끝난 자식만 거두고 그 저장소를
        #   「시간 초과」로 적는다 — 끝난 것들의 판정은 그대로 산다.
        # ⚠ 남은 예산으로 기다린다 — 자식마다 한도를 새로 주면 걸린 저장소 수만큼 곱해져(다섯이 걸리면 다섯 배) 배선이 그만큼 늦는다.
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
            $to = Get-PullTarget $repo $f.Remote
            if (-not $to) {
                $pulledRepos[$repo] = $false
                continue
            }
            # 이 배포가 전에 심은 사본이 빨리감기를 막으면 걷는다 — 커밋 안 된 사본은 진본이 다음에 바뀌어 형제 커밋이 들어올 때마다
            #   당김을 막고, 당김이 지면 아래 `copy` 걸음도 비켜서 저절로는 안 풀린다. 걷은 것은 줄에 진본 판과 함께 남긴다.
            $planted = Clear-PlantedCopies $repo $to.Sha
            foreach ($x in $planted.Cleared) {
                $r7 = $x.Rev.Substring(0, 7)
                Write-Host "↺ 사본 걷음  $repo — $($x.Path)  (진본 $r7 판의 사본 · 그 내용: git -C `"$src`" show ${r7}:$($x.Path))" -ForegroundColor Yellow
            }
            $m = Invoke-GitWait @('-C', $repo, 'merge', '--ff-only', '-q', $to.Sha) $PullMergeTimeoutSec
            # 회사 PC 의 DRM 이 감싼 오피스 · PDF 가 빨리감기를 막았으면 백업하고 되돌린 뒤 한 번 더 merge 한다 — git 은 감싼 바이트를
            #   손질로 읽어, 원격이 그 파일을 바꾸거나 지우는 당김을 날마다 멈춘다. merge 가 진 뒤에만 묻는다 — 몸통을 띄우는 값(저장소마다
            #   1초 가까이)을 막힌 적 없는 당김마다 치르지 않는다. 되돌린 것은 줄에 백업 자리와 함께 남긴다.
            $drm = $null
            if ($m.Code -ne 0) {
                $drm = Clear-DrmWrapped $repo $to.Sha
                foreach ($l in $drm.Lines) { Write-Host "↺ 감싼 사본 되돌림  $repo — $l" -ForegroundColor Yellow }
                if (-not $drm.Why -and $drm.Lines.Count) {
                    $m = Invoke-GitWait @('-C', $repo, 'merge', '--ff-only', '-q', $to.Sha) $PullMergeTimeoutSec
                }
            }
            if ($m.Code -ne 0) {
                $kept = if ($planted.Why) { " · 사본을 안 걷었다: $($planted.Why)" } else { '' }
                if ($drm -and $drm.Why) { $kept += " · 감싼 사본을 안 되돌렸다: $($drm.Why)" }
                Write-Host "! 못 당김  $repo — $($m.Why)$kept" -ForegroundColor Red
                $pulledRepos[$repo] = $false
                continue
            }
            try { $now = (& git -C $repo rev-parse --short HEAD 2>$null) } catch { $now = '' }
            $now = "$now".Trim()
            # 전진했나를 같이 낸다 — 「당겼다」만 적으면 새 코드가 들어온 회차와 아무것도 안 온 회차가 한 줄로 같아진다.
            #   당김 문이 원격 끝 앞에 세웠으면 그것도 붙인다. 나무가 이미 그 답보다 앞이면 빨리감기는 뒤로 안 가 나무가 그 자리에
            #   남는다 — 그때는 「앞에 세웠다」 대신 그렇다고 말한다. 짝 — `scripts/startup-pipeline.ps1` 의 `Sync-Repo` 가 같은 줄을
            #   글자까지 같게 든다(0158). 고치면 둘을 같이 고친다.
            $note = $to.Note
            if ($note) {
                try { $at = (& git -C $repo rev-parse HEAD 2>$null) } catch { $at = '' }
                if ("$at".Trim() -ne $to.Sha) { $note = " · 나무가 당김 문의 답 $($to.Sha.Substring(0, 7)) 보다 앞이라 그 자리에 둔다" }
            }
            if ($now -and $f.Was -and ($now -ne $f.Was)) {
                Write-Host "↓ 당김  $repo  ($($f.Was) → $now$note)" -ForegroundColor DarkGray
            } else {
                Write-Host "↓ 당김  $repo  (이미 최신$note)" -ForegroundColor DarkGray
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
#endregion 당김 손

#region 손 부르기 — 규범 · 룰 · 에이전트 · 스킬을 도구 홈에 놓는 손(`.claude/hooks/tool-homes.py`)을 부르고, 그 줄을 계획 걸음과 할 일로 가른다
# 무엇이 어느 홈에 어떤 꼴로 가나는 갈 곳 표(`tool-homes.conf`)와 손만 안다 — 이 스크립트는 손을 부르고 그 줄을 옮겨 싣기만
#   한다. 부르는 꼴 · 출력 계약 · 종료 값 · 제작자 칸 읽기 · 백업 자리는 손의 머리말이 든다 — 여기 옮겨 적으면 손사본이 된다
function Invoke-ToolHomes {
    # 손을 한 번 부른다 — 이 저장소로 개인 층을 채우고 놓는다. `-DryRun` 이면 홈 아래 아무것도 안 쓰고 바꿀 줄만 받는다.
    # 돌려주는 것: @{ Lines; Code; Rerun } · 못 불렀으면 @{ Why } — 읽는 자는 `ConvertFrom-ToolHomesOutput` 이다
    # ⚠ `&` 로 부르고 `$LASTEXITCODE` 를 읽는다 — `Start-Process -PassThru` 는 종료 값을 잃는다(`Start-GitChild` 머리).
    # ⚠ stderr 를 리다이렉트하지 않는다(당김 손 머리의 「리다이렉트가 곧 위험이다」) — 손의 판정은 다 stdout 줄이고, stderr 는
    #   콘솔로 흐른다.
    param([string]$Src, [switch]$DryRun)
    $hand = Join-Path $Src '.claude\hooks\tool-homes.py'
    $py   = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $py) { return @{ Why = 'python 이 없어 손을 못 불렀다 — 도구 홈에 안 놓였다' } }
    if (-not (Test-Path -LiteralPath $hand -PathType Leaf)) { return @{ Why = "손이 없다 ($hand) — 도구 홈에 안 놓였다" } }
    $handArgs = @('-X', 'utf8', $hand, 'sync', '--layer', 'personal', '--from', $Src)
    if ($DryRun) { $handArgs += '--dry-run' }
    # 못 띄우는 것(보안 소프트가 실행을 막는 PC)도 할 일 한 줄로 내린다 — 여기서 던지면 계획 한가운데서 배포가 통째로 죽는다
    try { $lines = @(& $py.Source @handArgs); $code = $LASTEXITCODE }
    catch { return @{ Why = "python 을 못 띄웠다 ($($_.Exception.Message.Split([char]10)[0].Trim())) — 도구 홈에 안 놓였다" } }
    return @{ Lines = $lines; Code = $code
              Rerun = "python -X utf8 `"$hand`" sync --layer personal --from `"$Src`" --dry-run" }
}

function ConvertFrom-ToolHomesOutput {
    # `Invoke-ToolHomes` 의 답 → @{ Steps — 계획 걸음(`CHANGE=` 한 줄에 하나) · Notes — 할 일 줄 · Same — 바꿀 것이 없다고 답했나 ·
    #   Failed — 다 못 놓았거나 못 쟀다 }
    # `CHANGE=` 한 줄이 계획의 한 걸음이다 — 그래야 「바꿀 것이 없습니다」가 손도 다른 것도 바꿀 것이 없을 때만 선다. 자리는
    #   손이 낸 꼴(`~/` 로 연다) 그대로 싣는다.
    # ⚠ 끝 줄(`CHANGED=`)이 없으면 손이 중간에 죽은 것이라 못 잰 것이다 — 「바꿀 것 없음」으로 접지 않는다.
    param($Run)
    $who = '규범 · 룰 · 에이전트 · 스킬(tool-homes.py)'
    if ($Run.Why) { return @{ Steps = @(); Notes = @("$who — $($Run.Why)"); Same = $false; Failed = $true } }
    # 손의 동사 → 이 화면의 꼴(부호 · 낱말). 모르는 동사도 버리지 않고 그 낱말 그대로 싣는다
    $verbs = @{ fill = '+ 채움'; drop = '- 걷음'; write = '+ 씀'; remove = '- 제거'; backup = '~ 백업'; record = '+ 기록' }
    $steps = @(); $notes = @(); $ended = $null; $errored = $false
    foreach ($ln in @($Run.Lines)) {
        $t = "$ln".TrimEnd()
        if (-not $t) { continue }
        if ($t.StartsWith('CHANGE=')) {
            $f = @($t.Substring(7) -split "`t", 3)
            $label = if ($verbs.ContainsKey($f[0])) { $verbs[$f[0]] } else { "* $($f[0])" }
            $where = if ($f.Count -gt 1) { $f[1] } else { '' }
            $why   = if ($f.Count -gt 2 -and $f[2]) { "  ($($f[2]))" } else { '' }
            $steps += @{ Kind = 'homes'; Verb = $f[0]; Text = "$label  $where$why" }
        } elseif ($t.StartsWith('WARN=')) {
            $notes += "$who — 경고: $($t.Substring(5))"
        } elseif ($t.StartsWith('ERROR=')) {
            $errored = $true
            $notes += "$who — 오류: $($t.Substring(6))"
        } elseif ($t.StartsWith('CHANGED=')) {
            $ended = $t.Substring(8)
        } else {
            $notes += "$who — 손이 계약 밖의 줄을 냈다: $t"
        }
    }
    $odd = $true
    if ($null -eq $ended) {
        $notes += "$who — 못 쟀다: 손이 끝 줄(CHANGED=)을 안 냈다 (exit $($Run.Code)). 확인:  $($Run.Rerun)"
    } elseif ($ended -ne $(if ($steps.Count) { '1' } else { '0' })) {
        $notes += "$who — 손의 끝 줄(CHANGED=$ended)이 바꿀 줄 $($steps.Count)개와 안 맞는다. 확인:  $($Run.Rerun)"
    } elseif ($Run.Code -ne 0 -and -not $errored) {
        $notes += "$who — 손이 오류로 끝났다 (exit $($Run.Code)). 확인:  $($Run.Rerun)"
    } else { $odd = $false }
    $failed = $odd -or $errored -or ($Run.Code -ne 0)
    return @{ Steps = $steps; Notes = $notes; Same = (-not $failed -and $steps.Count -eq 0); Failed = $failed }
}
#endregion 손 부르기

#region 홈 씨앗 손 — 이 저장소가 홈 씨앗의 원본이면 홈으로 폴더째 미는 목록과 「씨앗의 판 줄」 걸음을 짓는다
function Get-SeedColumn {
    # 받는 것: 이 저장소 뿌리(`-Src`) · 홈(`-Dst`). 아무것도 안 쓴다(git 으로 판만 묻는다). 내는 것: @{ Dirs — 홈으로 폴더째
    #   미는 폴더(뿌리 기준 · `\` 로) · Notes — 할 일 줄 · Stamp — 「씨앗의 판 줄」 걸음(안 쓰면 $null) · Same — 판 줄이 이미
    #   이 판일 때의 「= 동일」 줄(아니면 $null) }
    # ⚠ 문은 「이 저장소가 홈 씨앗의 원본인가」 — 뿌리에 deploy.seeds.conf 가 있나다. 그 선언은 씨앗에 안 실려 씨앗으로 만든
    #   동료 저장소에는 없고, 그 PC 의 홈 씨앗과 판 줄은 설치기가 짐에서 깐 그대로여야 한다 — 문 없이 돌면 판 줄을 동료 저장소의
    #   커밋으로 덮는다. 문을 못 지나면 아무것도 안 하고 아무 말도 안 한다. 동료가 그 파일을 두면 그 저장소가 홈 씨앗의
    #   원본이다. 파일은 있는데 비었으면 할 일 한 줄이다(설정 결함). 세션 훅 `deploy_home_norms` 의 씨앗 칸이 같은 문을 쓴다.
    # `scripts/check-tool-homes.py` ⑳ 이 이 함수를 떼어 동료 저장소로 부른다 — 홈 씨앗의 판 줄 · 씨앗 목록을 이름 대는 문자열은
    #   이 함수 밖에 두지 않는다(그 검사가 이 함수 밖의 문자열을 잰다).
    param([string]$Src, [string]$Dst)
    # 문을 못 지난 판도 같은 열쇠를 다 든다 — `Gone` 이 없으면 흐름의 `@($seedCol.Gone)` 이 `$null` 하나를 든 배열이 되어 계획에
    #   빈 걸음이 서고, 제거 후보 칸의 `$goneSet[$g.Path]` 가 널 열쇠로 던져 배포가 죽는다.
    $col  = @{ Dirs = @(); Gone = @(); Notes = @(); Stamp = $null; Same = $null }
    $conf = Join-Path $Src 'deploy.seeds.conf'
    if (-not (Test-Path -LiteralPath $conf -PathType Leaf)) { return $col }
    $col.Dirs = @(Get-Content -LiteralPath $conf -Encoding UTF8 |
        ForEach-Object { ($_ -replace '#.*$', '').Trim() } |
        Where-Object   { $_ } |
        ForEach-Object { $_ -replace '/', '\' })
    if ($col.Dirs.Count -eq 0) {
        $col.Notes += 'deploy.seeds.conf 가 비었다 — 홈으로 폴더째 미는 씨앗·사내 환경 문서가 하나도 안 깔린다'
    }
    # ── 원본이 걷은 파일 — 기본 실행이 걷는다 (PAISetup #44 ⑭) ────────────
    # 이 저장소가 홈 씨앗의 원본인 PC 에서는 설치기가 그 폴더를 비켜선다 — 원본에서 걷은 파일을 홈에서 걷는 손은 여기 하나다. 덮어쓰기만
    #   하면 한 번 민 파일이 홈에 영영 남는다(씨앗은 새 프로젝트로 퍼지고, 사내 환경 문서는 틀린 안내가 된다).
    # 우리 것의 기록은 이 저장소의 이력이다 — 홈에만 남은 파일 가운데 이 저장소가 그 자리에서 지운 적이 있는 것(`git log --diff-filter=D`)만
    #   걷는다. 이력에 없는 파일(프록시의 `proxy.log` · `*.pid` · 시험 결과 · 사람이 둔 것)은 안 건드린다 — 그것은 `-Prune` 의 후보로 남는다.
    #   이름이 바뀐 파일은 옛 이름을 지운 것으로 센다(`--no-renames`). 걷는 걸음은 백업 자리에 원본을 뜬다(실행 단계의 `remove`).
    # 이력을 못 물으면(git 이 없다 · 얕은 클론이 그 커밋을 안 든다 · git 이 졌다) 걷지 않는다 — 못 물은 것은 할 일 한 줄이고, 얕은
    #   클론에서 못 본 이력은 안 걷힌 채 남는다(우리 것을 남의 것으로 세는 쪽으로만 진다).
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($col.Dirs.Count -and -not $git) { $col.Notes += 'git 이 없어 원본이 걷은 씨앗 · 사내 환경 문서 파일을 못 가렸다 — 홈에 남는다' }
    elseif ($col.Dirs.Count) {
        $hist = $null
        try { $hist = @(& git -C $Src -c core.quotepath=false log --no-renames --diff-filter=D --name-only --format= -- @($col.Dirs | ForEach-Object { $_ -replace '\\', '/' }) 2>$null) } catch { $hist = $null }
        if ($null -eq $hist -or $LASTEXITCODE -ne 0) {
            $col.Notes += '원본 이력을 못 물어(git log) 원본이 걷은 씨앗 · 사내 환경 문서 파일을 못 가렸다 — 홈에 남는다'
        } else {
            $deleted = @{}
            foreach ($l in $hist) { $l = "$l".Trim(); if ($l) { $deleted[($l -replace '/', '\')] = $true } }
            foreach ($sd in $col.Dirs) {
                $sSrc = Join-Path $Src $sd
                $sDst = Join-Path $Dst $sd
                if (-not (Test-Path -LiteralPath $sSrc) -or -not (Test-Path -LiteralPath $sDst)) { continue }
                $base = (Get-Item -LiteralPath $sDst -Force).FullName.TrimEnd('\')
                foreach ($f in @(Get-ChildItem -LiteralPath $base -Recurse -File -Force | Where-Object { $_.FullName -notmatch '\\__pycache__\\' })) {
                    $rel = $f.FullName.Substring($base.Length + 1)
                    if ((Test-Path -LiteralPath (Join-Path $sSrc $rel)) -or -not $deleted["$sd\$rel"]) { continue }
                    $col.Gone += @{ Kind = 'remove'; Path = $f.FullName; Text = "- 제거  $($f.FullName)  (원본이 걷었다 — $($sd -replace '\\', '/')/)" }
                }
            }
        }
    }
    # ── 씨앗의 판 줄 — 홈 사본이 어느 판에서 왔나를 그 자리에 남긴다 ────────────
    # 홈 사본을 진본으로 믿고 재는 자(`seeds/check/_check/borrowed_check.py` 의 `_stamp()`)가 판을 이 줄에서 읽는다 — 홈
    #   뿌리는 git 나무가 아니라 판을 물을 데가 없다. 파일 이름은 그쪽 `VERSION_FILE` 이 들고, 쓰는 자는 여기와 세션 훅
    #   `deploy_home_norms` 의 씨앗 칸 둘이다 — 한 낱말이라 선언 파일로 안 뽑고 곁말로 서로를 가리킨다.
    # 걸음은 여기서 짓되 계획에는 흐름의 「씨앗의 판 줄」 칸에서 싣는다 — 까닭은 그 칸이 든다.
    # 판이 그대로면 안 쓴다 — 날짜 칸은 「이 판이 홈에 깔린 날」이라, 매번 덮으면 늘 오늘이 되어 낡음을 아무것도 말하지 않는다.
    # 이 줄은 견주기 밖이다 — 세션 훅이 견주는 자리는 `seeds/<이름>/` 안이고 이 줄은 뿌리 `seeds/` 에 산다. 그래서 거기에
    #   제외를 따로 안 든다 — 안 견줄 것을 빼는 선언은 없는 것을 가리키는 손사본이 된다.
    $stampFile = Join-Path $Dst 'seeds\.version'
    $stampRev  = if (Get-Command git -ErrorAction SilentlyContinue) {
                     try { (& git -C $Src rev-parse --short HEAD 2>$null) } catch { $null }   # 버리는 것도 방패가 아니라 잡는다(당김 손 머리의 「리다이렉트가 곧 위험이다」)
                 } else { $null }
    if ($stampRev) {
        $stampRev = ([string]$stampRev).Trim()
        $stampOld = if (Test-Path $stampFile) {
                        [string](Get-Content $stampFile -TotalCount 1 -Encoding UTF8)
                    } else { '' }
        if ((($stampOld -split '\s+')[0]) -eq $stampRev) {
            $col.Same = "= 동일  $stampFile  ($stampOld)"
        } else {
            $stampLine = "$stampRev $(Get-Date -Format 'yyyy-MM-dd')"
            $col.Stamp = @{
                Kind = 'stamp'; Path = $stampFile; Line = $stampLine
                Text = "+ 판 줄  $stampFile  ($stampLine)"
            }
        }
    }
    return $col
}
#endregion 홈 씨앗 손

#region 백업 손 — 덮거나 걷기 전에 원본을 백업 자리에 뜬다
function Save-Backup($path) {
    # 받는 것: 덮거나 걷을 파일 · 부작용: `$backup` 아래에 원래 폴더 구조대로 뜬다(`$dst` · `$backup` 을 읽는다).
    #   이름만 떼어 평평하게 쌓으면 여러 씨앗의 README.md 처럼 같은 이름끼리 서로를 덮어 백업이 사라진다.
    $rel = if ($path.StartsWith($dst, [StringComparison]::OrdinalIgnoreCase)) {
        $path.Substring($dst.Length).TrimStart('\')
    } else {
        # ~/.claude 밖(저장소 배포본)은 경로 전체를 이름에 접어 유일하게 만든다 — 여러 저장소의 같은 이름끼리 안 덮는다.
        Join-Path '_outside' (($path -replace ':', '') -replace '[\\/]', '-')
    }
    $to = Join-Path $backup $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $to -Parent) | Out-Null
    Copy-Item $path $to
}
#endregion 백업 손

#region 지문 손 — 못 읽는 파일 하나가 배포를 끝내지 않게 지문을 뜬다
function Get-HashOrWhy([string]$Path) {
    # 받는 것: 파일 · 내는 것: @{ Hash } 또는 못 읽었으면 @{ Why = 까닭 한 줄 } · 던지지 않는다.
    # ⚠ 홈 사본은 다른 프로그램(백신 · 보안 에이전트)이 읽기 공유 없이 쥐고 있을 수 있다 — `Get-FileHash` 가 그 자리에서 던지면
    #   `$ErrorActionPreference = 'Stop'` 아래 배포가 통째로 죽는다. 부르는 쪽은 그 파일 하나를 포기한 것으로 빨강(`$envDown`)에
    #   이름째 남기고 다음으로 간다.
    try { return @{ Hash = (Get-FileHash -LiteralPath $Path -ErrorAction Stop).Hash } }
    catch { return @{ Why = $_.Exception.Message.Split([char]10)[0].Trim() } }
}
#endregion 지문 손

#region 파일 쓰기 손 — 씨앗 복사를 끌 수 있는 일꾼 자식 하나에 차례로 맡기고, 한도는 이 프로세스가 쥔다
# 백신의 행위 차단(실시간 감시)은 파일을 쓰는 프로세스를 통째로 멈춰 세운다 — 스레드가 다 「대기 · 중단」에 걸려 그 안의 코드는
#   다시 안 돈다. 그래서 복사는 이 프로세스가 아니라 자식(일꾼)이 하고, 한도와 판정은 멈추지 않은 이 프로세스가 든다.
# 일꾼은 한 회차에 하나를 띄워 건마다 다시 쓴다 — 복사 한 건의 값은 거의 다 자식이 뜨는 값이라, 건마다 띄우면 씨앗을 처음 다
#   까는 판이 그 수만큼 는다(`$FileOpLimitSec` 곁의 잰 값). 한도와 멈춤 살피기는 건마다 든다 — 한 건이 한도(`$FileOpLimitSec`)를
#   넘기거나 일꾼의 스레드가 다 중단에 걸린 것이 보이면 그 일꾼만 끄고(쥔 손잡이가 같이 풀린다) 그 파일을 포기하고, 다음 건은 새
#   일꾼이 받는다. 부르는 쪽은 진 파일을 빨강에 이름째 남기고 다음 파일로 간다. 일꾼은 하위 프로세스를 안 띄워 그 하나만 끄면 된다.
# 일꾼은 지금 도는 이 파워셸과 같은 실행 파일이다 — 백신의 예외는 프로그램 실행 파일로 걸려, 사람이 이 파워셸을 예외로 둔 PC 에서
#   다른 실행 파일(`cmd.exe` 같은)이 쓰면 그 예외 밖이라 같은 차단이 다시 걸린다. `Copy-Item -Force` 라 읽기 전용 대상도 덮는다.
# 대상에 바로 덮어쓴다 — 멎은 복사가 남긴 사본은 다음 회차의 지문 대조가 원본과 다르다고 보고 다시 덮는다.
# 주고받는 꼴 — 건은 일꾼의 표준 입력에 한 줄 `<번호> <원본> <대상>`, 답은 표준 출력에 한 줄 `<번호> ok` 또는 `<번호> err <까닭>`.
#   번호가 이 건과 다른 줄은 이 건의 답으로 안 읽는다.
# ⚠ 자리와 까닭은 UTF-8 바이트의 base64 로 오간다 — 줄 속의 글자를 아무 파서도 다시 안 읽어 이름 속의 따옴표 · `$` · `%` · 빈칸이
#   안 풀리고, 양쪽 콘솔 코드페이지와 무관하게 한글 까닭이 읽힌다. 일꾼은 BOM 을 알아보고 넘기며 읽는다 — 이 프로세스의 표준
#   입력 쓰개는 콘솔 입력 인코딩을 따라 BOM 을 앞에 붙일 수 있다.
# ⚠ 일꾼의 세 스트림은 파이프다(자식 프로세스의 스트림 돌리기라 파워셸이 감싸지 않는다 — 당김 손 머리의 「리다이렉트가 곧
#   위험이다」 밖이다). stderr 는 비우며 받아 두고, 일꾼이 끝나 버린 건의 까닭에 붙인다.
# ⚠ 끄는 것은 이 프로세스가 띄운 그 일꾼의 손잡이다 — PID 로 다시 찾지 않아 그 사이 같은 번호를 받은 남의 프로세스를 안 끈다.
# 고리가 끝나면 `Stop-FileWorker` 가 일꾼을 거둔다. 이 프로세스가 도중에 죽으면 일꾼은 표준 입력의 끝을 읽고 스스로 끝난다.

function Start-FileWorker {
    # 받는 것: 없다 · 내는 것: 일꾼 @{ P = 프로세스; Err = stderr 를 다 읽는 일; Seq = 0 } 또는 못 띄웠으면 @{ Why } · 던지지 않는다.
    $exe = $null
    try { $exe = (Get-Process -Id $PID).Path } catch { $exe = $null }
    if (-not $exe) { $exe = Join-Path $PSHOME 'powershell.exe' }
    $body = '$ErrorActionPreference = ''Stop''; $ProgressPreference = ''SilentlyContinue''; $u = New-Object Text.UTF8Encoding($false); $in = New-Object IO.StreamReader([Console]::OpenStandardInput(), $u, $true); $o = [Console]::OpenStandardOutput(); while ($null -ne ($l = $in.ReadLine())) { $f = $l.Trim().Split([char]32); if ($f.Count -ne 3) { continue }; try { Copy-Item -LiteralPath $u.GetString([Convert]::FromBase64String($f[1])) -Destination $u.GetString([Convert]::FromBase64String($f[2])) -Force -ErrorAction Stop; $r = $f[0] + '' ok'' } catch { $r = $f[0] + '' err '' + [Convert]::ToBase64String($u.GetBytes(($_.Exception.Message -replace ''\s+'', '' '').Trim())) }; $b = [Text.Encoding]::ASCII.GetBytes($r + [char]10); $o.Write($b, 0, $b.Length); $o.Flush() }'
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe
    $psi.Arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command `"$body`""
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = New-Object Text.UTF8Encoding($false)
    $psi.StandardErrorEncoding = New-Object Text.UTF8Encoding($false)
    try { $p = [System.Diagnostics.Process]::Start($psi) }
    catch { return @{ Why = "복사를 맡을 일꾼($exe)을 못 띄웠다: $($_.Exception.Message.Split([char]10)[0].Trim())" } }
    return @{ P = $p; Err = $p.StandardError.ReadToEndAsync(); Seq = 0 }
}

function Stop-FileWorker([switch]$Kill) {
    # 받는 것: `-Kill` 이면 끝나기를 안 기다리고 바로 끈다 · 내는 것: 없다 · 던지지 않는다.
    # 부작용: `$script:fileWorker` 를 비운다. `-Kill` 이 없으면 표준 입력을 닫아 스스로 끝나기를 5 초 기다리고, 안 끝나면 끈다.
    $w = $script:fileWorker
    $script:fileWorker = $null
    if (-not $w) { return }
    $p = $w.P
    if (-not $Kill) {
        try { $p.StandardInput.Close() } catch { }
        try { if ($p.WaitForExit(5000)) { return } } catch { }
    }
    try { if (-not $p.HasExited) { $p.Kill() } } catch { }
    try { $null = $p.WaitForExit(5000) } catch { }
}

function Invoke-FileWorker {
    # 받는 것: 원본 · 대상 · 한도(초) · 살피는 간격(밀리초) · 내는 것: @{ Ok = $true } 또는 @{ Ok = $false; Why } · 던지지 않는다.
    # 부작용: 일꾼(`$script:fileWorker`)이 없거나 끝나 있으면 새로 띄운다 · 이 건에서 멎거나 끝나 버린 일꾼은 끄고 비운다.
    # 한도는 이 건을 넘긴 때부터 센다 — 일꾼을 새로 띄운 건은 뜨는 값까지 든다.
    param([string]$From, [string]$To, [int]$LimitSec, [int]$PollMs)
    $u = New-Object Text.UTF8Encoding($false)
    $clock = [System.Diagnostics.Stopwatch]::StartNew()
    if ($script:fileWorker -and $script:fileWorker.P.HasExited) { Stop-FileWorker -Kill }
    if (-not $script:fileWorker) {
        $w = Start-FileWorker
        if ($w.Why) { return @{ Ok = $false; Why = $w.Why } }
        $script:fileWorker = $w
    }
    $w = $script:fileWorker
    $w.Seq++
    $id = [string]$w.Seq
    try {
        $w.P.StandardInput.WriteLine("$id $([Convert]::ToBase64String($u.GetBytes($From))) $([Convert]::ToBase64String($u.GetBytes($To)))")
        $w.P.StandardInput.Flush()
    } catch {
        Stop-FileWorker -Kill
        return @{ Ok = $false; Why = "복사를 맡은 일꾼에게 이 건을 못 넘겼다: $($_.Exception.Message.Split([char]10)[0].Trim())" }
    }
    $read = $w.P.StandardOutput.ReadLineAsync()
    $held = 0   # 스레드가 다 중단에 걸린 것을 잇달아 본 횟수 — 뜨는 순간의 짧은 중단을 멈춤으로 안 읽는다
    while ($true) {
        # ⚠ 읽기가 던지면(일꾼이 끝나며 파이프가 닫힌 것) 끝나 버린 것으로 읽는다 — 이 함수가 던지면 배포가 통째로 죽는다.
        $done = $false
        $line = $null
        try { $done = $read.Wait($PollMs); if ($done) { $line = $read.Result } } catch { $done = $true; $line = $null }
        if ($done) {
            if ($null -eq $line) {
                $text = ''
                try { if ($w.Err.Wait(2000)) { $text = ($w.Err.Result -replace '\s+', ' ').Trim() } } catch { }
                $code = '?'
                try { if ($w.P.WaitForExit(2000)) { $code = $w.P.ExitCode } } catch { }
                Stop-FileWorker -Kill
                return @{ Ok = $false; Why = "복사를 맡은 일꾼이 이 파일에서 끝나 버렸다 (exit $code)$(if ($text) { ": $text" })" }
            }
            $f = $line.Trim().Split([char]32)
            if ($f[0] -eq $id -and $f[1] -eq 'ok') { return @{ Ok = $true } }
            if ($f[0] -eq $id -and $f[1] -eq 'err') {
                $text = ''
                try { $text = $u.GetString([Convert]::FromBase64String($f[2])) } catch { }
                return @{ Ok = $false; Why = "복사가 졌다$(if ($text) { ": $text" })" }
            }
            $read = $w.P.StandardOutput.ReadLineAsync()
        }
        $why = $null
        try {
            $w.P.Refresh()
            $ts = @($w.P.Threads)
            $free = @($ts | Where-Object { -not ($_.ThreadState -eq 'Wait' -and $_.WaitReason -eq 'Suspended') })
            if ($ts.Count -and -not $free.Count) { $held++ } else { $held = 0 }
        } catch { $held = 0 }
        if ($held -ge 3) { $why = '백신이 이 파일에서 멈춰 세웠다 — 복사하던 일꾼의 스레드가 다 중단에 걸렸다' }
        elseif ($clock.Elapsed.TotalSeconds -gt $LimitSec) { $why = "${LimitSec}초 안에 안 끝나 포기했다 — 다른 프로그램(백신 같은)이 그 파일을 쥐었을 수 있다" }
        if ($why) {
            Stop-FileWorker -Kill
            return @{ Ok = $false; Why = $why }
        }
    }
}
#endregion 파일 쓰기 손

#region 본 작업 폴더 손 — 형제 저장소가 서는 자리는 이 저장소 본 작업 폴더의 부모다
# 받는 것: 폴더 · 내는 것: 그 저장소의 본 작업 폴더. 연결된 작업 트리(`.claude\worktrees\<이름>` — 데스크탑 앱이 세션마다
#   만든다)에서 돌면 `$src` 의 부모는 형제 자리가 아니라서 쓴다. 본 작업 폴더는 git 이 댄다 — 공통 git 폴더
#   (`--git-common-dir`)가 `<본 작업 폴더>\.git` 이다. 검사가 쓰는 `scripts/sibling_base.py` · 세션 훅 몸통의 `main_worktree` 와
#   같은 자리를 낸다(이 파일은 파이썬 · bash 없이 돌아 그것들을 못 부른다).
# git 이 없거나 · git 나무가 아니거나 · 공통 git 폴더가 `.git` 이 아니면(맨 저장소 · 따로 둔 git 폴더 · 하위 모듈) `$Dir`
#   자신이다. 본 작업 폴더에서는 받은 글자를 그대로 돌려준다.
# ⚠ `--path-format=absolute` 를 안 쓴다 — 그 옵션이 없는 git(2.31 앞)의 `rev-parse` 는 모르는 옵션을 출력에 그대로 되돌려
#   틀린 자리가 조용히 선다. 맨 꼴의 답은 상대 경로(`.git`)일 수 있어 `$Dir` 에서 푼다.
function Get-MainWorktree([string]$Dir) {
    # ⚠ `2>$null` 은 방패가 아니라 잡아서 물러선다(당김 손 머리의 「리다이렉트가 곧 위험이다」).
    try { $common = [string](& git -C $Dir rev-parse --git-common-dir 2>$null) }
    catch { return $Dir }
    if ($LASTEXITCODE -ne 0 -or -not $common -or $common -eq '.git') { return $Dir }
    $full = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($Dir, $common))
    if ((Split-Path $full -Leaf) -ne '.git') { return $Dir }
    return (Split-Path $full -Parent)
}
#endregion 본 작업 폴더 손

#endregion 라이브러리

# ============================ 준비 ============================
# 층 — 없다. 아무것도 안 바꾼다
# 하는 일 — 경로(`$src` · `$dst` · `$backup`)와 계획을 담을 통(`$plan` · `$same` · `$todo` · `$envDown` · `$prunable` ·
#   `$gateReport`)을 세운다. `personal.conf` 의 REPOS · ROOT 에서 형제 저장소 자리(`$globalRuleTargets`)와 메모리
#   자리(`$memTargets`)를 파생하고, 저장소마다 미는 파일 목록(`$repoFiles`)을 읽고, Git Bash(`$bash`)를 찾는다
# 앞에서 받는 것 — 매개변수 셋(`-Yes` · `-Prune` · `-ShowUnchanged`) · 머리의 `$ErrorActionPreference = 'Stop'` 과 UTF-8 출력
# 안 하는 것 — 저장소를 안 받는다(clone 은 세션 훅의 `--install` 이 한다) · 화면에 안 찍는다 — 걸리는 것은 `$todo` 에 쌓는다

$src    = $PSScriptRoot
$dst    = Join-Path $HOME '.claude'
$backup = Join-Path $dst ('backups\deploy-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
# 씨앗 복사 한 건의 한도 — 넘기면 그 건을 포기하고 빨강에 이름째 남긴다(`Invoke-FileWorker` 머리). 미는 파일은 몇 MB 안쪽이라
#   초당 100 KB 로 기는 디스크에서도 수십 초 안에 끝나고, 실시간 감시가 한 파일을 훑는 값은 1 초 안쪽이다 — 멀쩡한 느린 디스크는
#   안 걸리는 자리에 둔다. 낚아챈 건 하나가 배포를 이만큼 늦춘다(멈춰 세운 것이 보이면 그 자리에서 끈다).
$FileOpLimitSec = 60
$FileOpPollMs   = 50     # 복사하는 일꾼이 멎었나 살피는 간격 — 답은 오는 그 자리에서 받아, 정상 건은 이 값만큼 안 기다린다
# 복사 값은 일꾼이 뜨는 값이 거의 다다 — 일꾼은 회차마다 한 번 뜨고, 멈춰 끈 건이 있으면 그 뒤로 한 번씩 더 뜬다. 잰 값(집 PC ·
#   씨앗 · 사내 환경 문서 · 메모리 128 건): 일꾼 하나가 차례로 받으면 0.6 초(뜨는 데 0.4 초 · 건마다 2 ms 안팎)이고, 건마다 자식을
#   띄우면 32 초(건마다 0.25 초)다. 백신이 프로세스가 뜨는 것을 늦추는 PC 에서는 뜨는 몫만 그만큼 는다.
$fileWorker     = $null  # 복사 일꾼 — `Invoke-FileWorker` 가 첫 건에서 띄우고, 실행 고리 뒤 `Stop-FileWorker` 가 거둔다

$plan    = @()   # 바꿀 것
$same    = @()   # 이미 맞는 것
$todo    = @()   # 사람이 해야 할 것
# ⚠ `$envDown` 은 `$todo` 와 갈라 둔다 — `$todo` 는 사람이 손으로 할 것(키 입력 같은)이라 남아도 환경은 서 있고,
#   `$envDown` 은 실행 환경이 안 선 것이라 비지 않으면 종료 값 1 로 끝난다. 안 선 것을 `$todo` 에 넣으면 부르는 쪽이 초록으로 읽는다.
$envDown = @()   # 실행 환경이 안 선 것 — 종료코드를 가른다
$prunable = @()  # 제거 후보 — 원본에 없는 것 (-Prune 없이는 세기만 한다)
# 초록도 편다 — 통과가 화면에서 침묵하면 「재서 다 살아 있다」와 「아예 안 쟀다」가 같아진다. 이 통에 드는 것은 저장소마다
#   「마지막 CI」 한 줄이다 — 훅 진단은 계획이 안 돌리고 저장소 설치 걸음이 `--install` 끝에 낸다.
$gateReport = @()  # 저장소마다 마지막 CI 한 줄 — 초록·빨강·못 쟀다

# 배포 대상은 PC 마다 적지 않고 `personal.conf` 에서 파생한다 — 저장소 목록과 자리는 `personal.conf`(REPOS · ROOT)가 들고
#   세션 훅도 그것으로 clone 하고 슬러그 폴더를 세우므로, PC 마다 따로 적으면 같은 사실의 사본이 된다 —
#   그 사본이 없는 새 PC 는 대상이 통째로 비어 배포 · 설치가 한 번도 안 돈다
# ⚠ 슬러그는 제품의 규칙대로 짓는다 — 윈도 경로에서 영숫자가 아닌 글자를 글자마다(뭉치지 않고) `-` 로. PowerShell 의 `-replace`
#   는 UTF-16 글자로 세므로 한글 한 자가 대시 하나다(세션 훅의 같은 규율 · `C:\Users\홍길동\repos` → `C--Users-----repos`).
# 메모리 폴더와 자리의 짝은 셋이다:
#     memory/<REPOS 의 이름>/  → ROOT\<이름>
#     memory/<이 저장소 이름>/ → 이 저장소 자리
#     memory/global/           → ROOT (저장소들을 담은 폴더에서 연 세션)
$memTargets = @{}          # memory/<이름> -> 그 메모리가 딸린 폴더 경로 (슬러그는 이 경로에서 짓는다)
$globalRuleTargets = @()   # 저장소 배포본을 받고 설치 걸음이 도는 저장소 루트들
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
# 적힌 저장소가 이 PC 에 하나도 없으면 말한다 — 그때 저장소 설치 걸음도, 그에 딸린 전역 설치 걸음도 통째로 안 선다.
#   clone 은 세션 훅(`--install`)이 personal.conf 의 REPO_URL 로 한다.
if ($repoNames.Count -gt 0 -and -not ($globalRuleTargets | Where-Object { Test-Path $_ })) {
    $todo += "personal.conf 의 REPOS 가 이 PC 의 $repoRoot 에 하나도 없다 — 저장소 설치 · 전역 설치가 안 선다. 세션 훅의 --install 이 REPO_URL 로 받는다"
}
# 안 읽는 선언(`deploy.targets.d/` · `deploy.targets.conf`)이 남았으면 말한다 — 남아 있으면 「고쳤는데 안 먹는다」로 사람을
#   헤매게 한다.
if ((Test-Path (Join-Path $src 'deploy.targets.conf')) -or
    @(Get-ChildItem (Join-Path $src 'deploy.targets.d') -Filter *.conf -File -ErrorAction SilentlyContinue).Count) {
    $todo += 'deploy.targets.d/ · deploy.targets.conf 는 더 안 읽는다 — 대상은 personal.conf 의 REPOS · ROOT 에서 파생한다. 지운다'
}

# 저장소마다 한 벌씩 미는 파일 목록 — 계획이 미는 목록을 짓고, 그보다 앞서 당김이 「당김을 막는 파일이 우리 사본인가」를 가를 때
#   읽는다(`Clear-PlantedCopies`). 그래서 당김 앞인 여기서 읽는다.
# 목록은 선언이 든다 — 재는 자(scripts/check-global-copies.sh)도 같은 파일을 읽어, 배열로 박으면 두 자가 손사본이 된다.
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

# PATH 의 bash 는 WSL 일 수 있다(배포판이 없으면 진다) — git.exe 자리에서 Git Bash 를 바로 찾는다.
$bash = @(
    (Get-Command git -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path (Split-Path (Split-Path $_.Source -Parent) -Parent) 'bin\bash.exe' }),
    "$env:ProgramFiles\Git\bin\bash.exe",
    "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1


# ============================ 당김 ============================
# 층 — 저장소. 형제 저장소의 main 을 원격 쪽으로 빨리감기로 맞춘다
# 하는 일 — `.git` 을 든 형제 저장소마다 fetch 를 동시에 띄우고, 저장소마다 어디까지 갈지 세션 훅 몸통에 물은 뒤
#   (`Get-PullTarget` — 원격 끝, 저장소가 당김 문을 두었으면 그 문이 고른 커밋) `merge --ff-only` 를 차례로 한다. merge 앞에서
#   빨리감기를 막는 파일이 이 배포가 전에 심은 사본뿐이면 그것을 걷고(`Clear-PlantedCopies`), merge 가 졌는데 막은 파일이 다 DRM 이
#   감싼 사본이면 백업하고 되돌린 뒤 한 번 더 merge 한다(`Clear-DrmWrapped`). 저장소마다 판정 한 줄(`↓ 당김` · `· 당김 건너뜀` · `! 못 당김` · 문을 못 물었으면 `! 당김 문을 못
#   물었다`)을 내고 — 되돌렸으면 그 앞에 `↺ 감싼 사본 되돌림`, 걷었으면 `↺ 사본 걷음` — 그 판정을 `$pulledRepos` 에 남긴다
# 앞에서 받는 것 — 준비의 `$globalRuleTargets` · `$bash`(몸통을 부른다) · `$repoFiles`(걷을 수 있는 파일의 목록)
# 안 하는 것 — 승인을 안 묻는다 · 던지지 않고 종료코드를 안 올린다 · 밀지 않는다(실행 단계의 `copy` 걸음이 `$pulledRepos` 를
#   읽기만 한다) · 우리 사본도 감싼 사본도 아닌 변경(사람의 손질 · 목록 밖 파일 · 스테이징된 것 · 들어올 커밋과 무관한 것)은 안 건드린다 ·
#   세션 훅의 당김 표식(`.git/claude-pull-attempted`)을 안 읽고 안 쓴다

# ── 당김 — 계획을 짓기 앞에 형제 저장소를 원격까지 맞춘다 ──
# 계획(`$targets` · `$plan`)과 설치 판정(`--needs-install`)은 지금 그 저장소에 있는 파일의 지문을 본다 — 당김이 그 뒤에 서면
#   새로 들어온 선언이 이번 회차가 아니라 다음 회차에 깔린다. 밀 것이 하나도 없는 회차에도 저장소마다 판정 한 줄이 서고,
#   `$plan` 에는 안 들어 승인 밖에서 돈다(다 최신이면 안 묻는다).
# ⚠ 못 당기면 안 민다 — 뒤처진 저장소에 새 진본이 앉으면 그것이 M 이 되어 다음 당김(`merge --ff-only`)을 막는다. 이 당김은
#   막는 것이 제 사본뿐이면 걷고 지나가지만, 세션 훅 · 부팅 라인의 당김은 못 걷어 다음 배포까지 막힌다. 판정은
#   `$pulledRepos` 가 들고 `copy` 걸음은 그것을 읽기만 한다.
# 당겨도 사본이 커밋 안 된 채 남는 자리는 이 규칙이 못 막는다 — 진본이 형제 커밋보다 앞서 있으면 `copy` 걸음이 새 진본을 심고,
#   그 사본은 형제 커밋이 들어올 때 당김을 막는다. 그 자물쇠를 다음 회차의 `Clear-PlantedCopies` 가 푼다(#209).
# main 위에서만 당긴다 — 작업 중인 브랜치를 건드리지 않는다(훅 `pull_ff` 와 같은 자). 배경이 아니라 동기다 — 자동 실행 라인은
#   이 직후에 서버를 띄우므로, 당긴 것이 이번 회차에 실려야 한다.
# 져도 던지지 않고 종료코드를 안 올린다 — 한 저장소의 실패는 그 저장소의 밀기만 막고, 낡은 판으로라도 뒤가 다 돈다.
# 훅의 90초 표식은 읽지도 쓰지도 않는다 — 그 표식은 한 세션의 훅 둘이 겹치는 것을 막는 자리이고, 여기 물음은 「지금
#   최신인가」라 남이 90초 안에 시도했다는 사실로는 답이 안 된다.
# 기다림에 한도가 있다 — 이 자리가 첫 걸음이라 여기서 안 끝나면 배선 · 계획 · 배포 · 설치가 통째로 안 돈다. 걸리는 길 둘(창을
#   띄우려는 자격증명 도움꾼 · 답을 안 주는 망)을 비대화 고정(`Sync-Repos` 머리) · 묶음 전체의 벽시계 한도 · 넘긴 자식 거두기로
#   막는다. 한도는 정상 왕복(사내 망 6~7초)의 열 배를 넘는 자리라 걸린 것에만 걸린다. 배선이 늦는 폭의 최대는 묶음 한도에
#   저장소마다 문 묻기 · merge 한도를 더한 것이다 — 문 묻기와 merge 는 차례로 돈다.
# 한도는 이름 셋이 든다 — 값을 아래 고리에 박으면 화면에 찍는 초와 재는 초가 갈린다.
$PullBatchTimeoutSec = 120   # fetch 묶음 전체의 벽시계 한도. 넘긴 자식만 거둔다
$PullMergeTimeoutSec = 30    # merge 하나의 한도 — 디스크 일이라 망을 안 탄다(걸리면 잠금이다)
$PullTargetTimeoutSec = 60   # 몸통에 멈출 커밋을 묻는 한도(저장소마다) — 저장소의 손이 망(CI 조회)을 탈 수 있어 fetch 자리다
$DrmClearTimeoutSec = 60     # 몸통이 감싼 사본을 백업하고 되돌리는 한도(저장소마다) — 디스크 일이지만 몸통을 Git Bash 로 띄우는 값이 든다
$pulledRepos = @{}   # 저장소 -> 이번 회차에 그 저장소로 밀어도 되나 (당김 판정)

# 대상은 `personal.conf` 의 REPOS 중 이 PC 에 `.git` 을 든 것이다 — 목록을 여기 안 적는다. 이 저장소 자신은 대상이 아니다 —
#   부팅 라인에서 이 스크립트가 도는 것은 설치의 「설정 저장소」 걸음이 이미 그것을 당긴 뒤이고, 지금 도는 몸통이 곧 그 판이다.
Sync-Repos $globalRuleTargets


# ============================ 계획 ============================
# 층 — 없다. 홈 · 저장소 · 환경 층에서 바꿀 것을 재기만 한다
# 하는 일 — 밀 파일(`$targets`)을 지어 지문으로 견준다. 도구 홈의 규범 · 룰 · 에이전트 · 스킬은
#   손에게 `--dry-run` 으로 물어 그 바꿀 줄을 싣는다. 바꿀 것은 `$plan`, 이미 맞는 것은 `$same`, 원본에 없는 것은 `$prunable`,
#   사람이 할 일은 `$todo`, 실행 환경이 안 선 것은 `$envDown`, 저장소마다 마지막 CI 줄은 `$gateReport` 에 담는다. 계획을 굳히며
#   배선(`githooks`)을 맨 앞에 세운다
# 앞에서 받는 것 — 당긴 뒤의 형제 저장소 나무 · 준비의 자리와 통 · `-Prune`(제거 후보를 계획에 올리나)
# 안 하는 것 — 홈 · 저장소 · 환경을 안 바꾼다 · 세션 훅과 손에는 묻기만 한다
#   (`--needs-install` · `--dry-run`) — 깔기와 진단은 실행 단계가 부른 훅이, 놓기는 실행 단계가 부른 손이 한다

# --- 파일 배포 ---
$memSrc   = Join-Path $src 'memory'
$targets  = @()

# 전역 규범 · 룰은 저장소로 안 간다 — 저장소가 사본을 지면 「이 저장소 것」과 「전역 것」이 한 폴더에서 섞인다. 홈이 빈 채
#   뜨는 리모트 컨테이너는 claude-config 를 함께 붙여 받으므로 저장소가 사본을 질 까닭이 없다

# 저장소마다 한 벌씩 있어야 하는 것들은 각 저장소로 간다 — 홈이 아니라 그 저장소 안에서 읽히는 자리(훅과 그 등록)다.
#   몸통은 익명이라 저장소마다 바이트가 같다. 여기의 `.claude\settings.json` 은 저장소의 훅 등록 파일이지 홈의 개인
#   설정이 아니다(머리글). 목록(`$repoFiles`)은 준비가 읽는다
foreach ($bootFile in $repoFiles) {
    $bootSrc = Join-Path $src $bootFile
    if (-not (Test-Path $bootSrc)) { continue }
    foreach ($repoRoot in $globalRuleTargets) {
        if (-not (Test-Path $repoRoot)) { continue }
        # Repo 를 달아 둔다 — 실행 단계의 `copy` 걸음이 그 저장소의 당김 판정을 읽는 근거다(못 당긴 저장소에는 안 민다).
        #   홈 대상에는 안 단다 — ~/.claude 는 git 밖이라 당길 것도 더러워질 것도 없다.
        $targets += @{ From = $bootSrc; To = Join-Path $repoRoot $bootFile; Repo = $repoRoot }
    }
}

# ADR 색인 생성기는 저장소로 안 나른다 — 찾는 자(`claude-config-path.sh`)가 홈 스킬 · 붙은 claude-config 의 스킬로 찾고,
#   리모트는 늘 claude-config 를 붙이므로 단독 세션용 사본이 필요 없다

# 프로젝트별 메모리: memory/<project>/*.md -> ~/.claude/projects/<슬러그>/memory/
if (Test-Path $memSrc) {
    foreach ($proj in (Get-ChildItem $memSrc -Directory)) {
        $memDsts = Get-ProjectMemDst $proj.Name
        if ($memDsts.Count -eq 0) {
            # 조용히 넘어가지 않는다 — 배포된 줄 알고 있으면 어긋난 것을 나중에야 안다
            $todo += "memory/$($proj.Name)/ 배포 안 됨 — 딸린 폴더가 이 PC 에 없다(personal.conf 의 REPOS · ROOT 로 짓는다)"
            continue
        }
        foreach ($f in (Get-ChildItem $proj.FullName -Filter *.md)) {
            foreach ($d in $memDsts) {
                $targets += @{ From = $f.FullName; To = Join-Path $d $f.Name }
            }
        }
    }
}

# 씨앗 · 사내 환경 문서 — deploy.seeds.conf 에 적힌 폴더를 폴더째 ~/.claude/ 아래 같은 이름으로 민다(목록은 그 선언이 들고,
#   뿌리는 자 둘이 같은 줄을 읽는다. `seeds\config-repo` 를 안 미는 까닭도 그 선언의 머리말이 든다).
# 홈에도 두는 까닭 — 진본은 저장소이고 스킬 · 형제 저장소 문서가 그 좌표를 가리키는데, 설치본만 받은 사람에게는 저장소가
#   없다. 그래서 설치(`install.ps1` 「공용 자산」 걸음)가 홈에 깔고, 이 자리가 그 사본을 진본과 맞춘다 — 갱신을 안 하면 사본이
#   조용히 낡는다.
# 이 칸의 문 · 목록 · 할 일 · 판 줄은 `Get-SeedColumn` 이 든다 — 이 저장소가 홈 씨앗의 원본이 아니면(씨앗으로 만든 동료
#   저장소) 이 칸은 아무것도 안 하고 아무 말도 안 한다. 여기는 그 답을 계획에 싣기만 한다.
$seedCol  = Get-SeedColumn -Src $src -Dst $dst
$seedDirs = $seedCol.Dirs
$todo    += $seedCol.Notes
foreach ($sd in $seedDirs) {
    $aSrc = Join-Path $src $sd
    if (-not (Test-Path $aSrc)) { continue }
    # 파이썬이 남긴 캐시(`__pycache__\`)는 안 민다 — 씨앗의 검사를 돌리면 생기는데, git 은 무시해도 이 복사는 모른다. 그것은
    #   자산이 아니라 그 PC 의 부산물이다.
    foreach ($f in (Get-ChildItem $aSrc -Recurse -File | Where-Object { $_.FullName -notmatch '\\__pycache__\\' })) {
        $rel = $f.FullName.Substring($aSrc.Length + 1)
        $targets += @{ From = $f.FullName; To = Join-Path $dst "$sd\$rel" }
    }
}

foreach ($t in $targets) {
    # 못 읽는 쪽이 있으면 그 파일만 못 견준 것이다 — 계획에 안 싣고 빨강에 이름째 남긴다(`Get-HashOrWhy` 머리)
    $hFrom = Get-HashOrWhy $t.From
    $hTo   = if (Test-Path -LiteralPath $t.To) { Get-HashOrWhy $t.To } else { $null }
    $unread = if ($hFrom.Why) { "$($t.From) — $($hFrom.Why)" } elseif ($hTo -and $hTo.Why) { "$($t.To) — $($hTo.Why)" } else { '' }
    if ($unread) {
        $envDown += "못 견줘 안 민 파일 — $unread"
    } elseif ($hTo -and $hFrom.Hash -eq $hTo.Hash) {
        $same += "= 동일  $($t.To)"
    } else {
        $verb = if ($hTo) { '덮어씀' } else { '새로 만듦' }
        $plan += @{ Kind = 'copy'; From = $t.From; To = $t.To; Repo = $t.Repo; Text = "+ 배포  $($t.To)  ($verb)" }
    }
}

# --- 도구 홈의 규범 · 룰 · 에이전트 · 스킬 — 손 하나가 놓는다 ---
# 이 저장소로 PC 의 개인 층을 채우고 갈 곳 표대로 도구 홈에 놓는 일은 손이 한다 — 여기서는 손에게 `--dry-run` 으로 묻고 그
#   바꿀 줄을 계획에 싣는다. 승인 뒤 실행 단계의 `homes` 걸음이 같은 명령을 `--dry-run` 없이 돌린다. 무엇을 어떻게 놓고 걷고
#   백업하나, 그리고 제작자 칸(`PAISETUP_PERSONAL`)으로 어느 도구 홈에 놓나는 손의 머리말이 든다 — 이 스크립트는 그 값을 안 본다.
# 바꿀 것이 없다는 답도 한 줄 세운다(`$same`) — 못 물은 판은 할 일에 서므로, 「재서 맞다」와 「안 쟀다」가 안 섞인다.
$homes = ConvertFrom-ToolHomesOutput (Invoke-ToolHomes -Src $src -DryRun)
$plan += $homes.Steps
$todo += $homes.Notes
if ($homes.Same) { $same += '= 동일  도구 홈의 규범 · 룰 · 에이전트 · 스킬  (손이 바꿀 것이 없다고 답했다)' }

# ── 씨앗의 판 줄 — 홈 사본이 어느 판에서 왔나를 그 자리에 남긴다 ────────────
# 걸음과 그 까닭은 `Get-SeedColumn` 이 든다(위 씨앗 칸에서 지었다). 이 저장소가 홈 씨앗의 원본이 아니면 둘 다 비었다.
# ⚠ 계획에 싣는 자리는 씨앗 복사 뒤인 여기다 — 계획은 순서대로 돌아, 위 씨앗 칸에서 실으면 이 줄이 복사보다 먼저 서서 복사가
#   지거나 건너뛰어도 「그 판이 깔렸다」고 말한다.
# 원본이 걷은 파일의 걷기도 여기서 싣는다 — 민 뒤 · 판 줄 앞. 무엇을 걷나는 `Get-SeedColumn` 이 든다.
$plan += @($seedCol.Gone)
if ($seedCol.Stamp) { $plan += $seedCol.Stamp }
if ($seedCol.Same)  { $same += $seedCol.Same }

# --- git 훅 경로 ---
# 저장소가 .githooks/ 를 들고 있으면 core.hooksPath 를 거기로 맞춰야 훅이 실제로 돈다 — .git/hooks/ 는 clone 을 안 따라와,
#   이 한 줄이 없는 PC 에서는 훅 파일만 있고 아무것도 안 걸린다. 걸린 줄 알고 있으면 게이트가 없는 것보다 나쁘다.
# 대상 목록은 $globalRuleTargets 에 배포본 저장소 하나를 더한 것이다.
# ⚠ 배포본 저장소는 이 자리에만 더한다 — 그 저장소는 동료에게 가는 zip 그 자체라, 개발 파일(훅 몸통 · settings.json · 도구
#   선언)을 복사하는 $globalRuleTargets 에 넣으면 그것이 zip 에 실려 나간다. `core.hooksPath` 는 설정일 뿐 파일이 아니라 새어
#   나갈 것이 없다.
# 배포본 이름은 박지 않고 `dist.manifest.conf` 에서 읽는다(뽑는 자 · 나무 재는 자와 같은 규약) — 박으면 배포 대상이 옮겨진 날
#   이 자리만 낡는다.
$hookTargets = @($globalRuleTargets)
$distName = ''
$manifest = Join-Path $src 'dist.manifest.conf'
if (Test-Path $manifest) {
    $inSection = $false
    foreach ($line in (Get-Content $manifest -Encoding UTF8)) {
        $t = $line.Trim()
        # ⚠ `-like` 를 안 쓴다 — 대괄호가 와일드카드라 `-like '[…]'` 는 이스케이프 없이는 조용히 안 맞는다.
        if ($t.StartsWith('[') -and $t.EndsWith(']')) {
            $inSection = ($t -eq '[배포본이 서는 자리]'); continue
        }
        if (-not $inSection -or -not $t -or $t.StartsWith('#')) { continue }
        $distName = $t; break
    }
}
if ($distName) {
    # 형제 자리에서 파생한다 — 형제 자리는 이 저장소 본 작업 폴더의 곁이라 작업 트리에서 돌아도 같은 배포본을 잡는다
    #   (`Get-MainWorktree`).
    $distRoot = Join-Path (Split-Path -Parent (Get-MainWorktree $src)) $distName
    if ((Test-Path (Join-Path $distRoot '.git')) -and ($hookTargets -notcontains $distRoot)) {
        $hookTargets += $distRoot
    }
}
foreach ($repoRoot in $hookTargets) {
    if (-not (Test-Path (Join-Path $repoRoot '.githooks'))) { continue }
    # ⚠ `2>$null` 은 방패가 아니라 잡아서 넘긴다(당김 손 머리의 「리다이렉트가 곧 위험이다」). 값을 못 읽은 것과 값이 다른
    #   것은 둘 다 「맞춰야 한다」로 간다.
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
# 게이트가 부르는 도구(링크 검사기 · shellcheck · 파이썬 의존성 등 — 도구 선언이 든다)를 깐다. 이 스크립트가 `git pull`
#   다음에 늘 도는 자리라 여기서 깐다 — 도구가 없으면 게이트는 그 검사만 건너뛰고 커밋을 통과시켜, 늘어난 도구를 아무도 모른다.
#   무엇을 깔지는 각 저장소의 훅이 안다 — 도구 이름이 여기 없고, 저장소가 늘어도 이 파일은 안 고친다.
# 계획은 진단을 안 돌리고 `--needs-install` 로 「이 저장소에 깔 게 있나」만 묻는다 — 답이 예/아니오 하나라 파일만 보면 나고,
#   프로브도 망도 안 탄다. 깔 게 있는 저장소만 실행 목록에 올려 다 살아 있으면 승인을 안 묻고, 물은 것은 초록이어도 `$same`
#   개수가 아니라 화면에 한 줄 낸다(안 묻는 것과 안 재는 것은 다른 명제다). 진단은 깐 뒤의 판정이라야 진짜라 깐 저장소에서
#   설치 끝에 한 벌만 나고, 안 깐 저장소는 세션 훅이 매 세션 찍는다.
# 걸음은 둘이다 — 전역형 도구(npm 전역 · 릴리스 바이너리 · winget · 브라우저)는 아래 고리 앞에 한 번 깔고, 고리 안에서는
#   저장소 몫(프로젝트 축 · 배선)만 부른다.
# ⚠ 그래서 여기서 바로 `$plan` 에 안 쌓는다 — 전역 걸음이 저장소 걸음보다 먼저 서야 배선이 걸 물건이 이미 깔려 있고, 실행은
#   계획 순서대로다. 고리가 도는 동안 모아 두었다가 고리가 끝난 뒤 전역 하나 + 저장소들 차례로 붙인다.
$installSteps = @()
# 이 저장소 자신도 설치 대상이다 — 파일 배포 대상은 아니지만(진본이라 덮을 것이 없다) 제 도구 선언과 배선이 있고, 세션
#   훅(auto)은 지난 실패를 다시 안 깔고 알리기만 하므로 다시 까는 손이 여기다.
foreach ($repoRoot in @(@($src) + $globalRuleTargets)) {
    $boot = Join-Path $repoRoot '.claude\hooks\session-start.sh'
    if (-not (Test-Path $boot)) { continue }
    if (-not $bash) {
        $todo += "Git Bash 를 못 찾음. 직접 실행:  bash '$boot' --install"
        continue
    }
    # ⚠ `2>&1` 을 안 붙인다(당김 손 머리의 「리다이렉트가 곧 위험이다」) — 사유는 훅이 stdout 한 줄로 낸다.
    # ⚠ 묻는 훅은 그 저장소의 사본이 아니라 진본이다 — 사본은 이 배포가 덮으러 가는 낡은 판일 수 있고, 낡은 판은
    #   `--needs-install` 을 몰라 auto 갈래로 빠져 저장소마다 오래 돌고 엉뚱한 줄을 사유로 낸다. 그래서 이 저장소의 몸통
    #   (`session-start-body.sh`)을 바로 부르고 대상 저장소는 `SESSION_START_REPO` 로 넘긴다 — 문지기가 몸통을 부를 때 쓰는
    #   입구다(형제 저장소의 훅은 몸통을 부르는 문지기로 줄었다)
    $needsProbe = Join-Path $src '.claude\hooks\session-start-body.sh'
    $env:SESSION_START_REPO = $repoRoot -replace '\\', '/'
    try { $needs = & $bash ($needsProbe -replace '\\', '/') --needs-install; $needsRc = $LASTEXITCODE }
    finally { Remove-Item Env:SESSION_START_REPO -ErrorAction SilentlyContinue }
    $needsWhy = @($needs | Where-Object { "$_".Trim() }) | Select-Object -Last 1
    if (-not $needsWhy) { $needsWhy = '훅이 사유를 안 냈다' }
    # ⚠ `--needs-install` 은 그 저장소에 지금 있는 선언으로 잰다 — 이번 배포가 도구 선언(`tools.global.conf`)을 바꾸면 새
    #   선언이 아직 거기 없어 지문이 맞는 것으로 나오고, 배포를 두 번 돌려야 깔린다. 그래서 선언을 덮는 복사가 계획에 있으면
    #   판정과 무관하게 올린다 — 실행은 계획 순서라 복사(앞)가 설치(여기)보다 먼저 돈다.
    $declChanges = @($plan | Where-Object {
        $_.Kind -eq 'copy' -and $_.Repo -eq $repoRoot -and $_.To -like '*\.claude\tools.global.conf' })
    # ⚠ 2 는 「못 쟀다」라 0 으로 안 접는다 — 부재가 통과로 읽히는 자리가 거기다. 못 쟀으면 깐다.
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
    # main 에 바로 커밋하면 CI 는 PR 도 자동머지도 없이 GitHub 페이지에만 빨강을 남긴다 — 배포가 도는 자리가 곧 사람이 보는
    #   자리라 여기서 한 줄 읽는다. `GH_TOKEN` 이 Actions 읽기 없는 세밀 토큰이면 403 이 나서 키링(gh auth login)으로 한 번 더
    #   묻고, 그것도 없으면 「못 쟀다」로 남긴다 — 이 줄로 배포를 막지 않는다. 빨강이면 남은 수동 작업에 올린다.
    $slug = $null
    try { $remote = & git -C $repoRoot remote get-url origin 2>$null } catch { $remote = '' }
    if ($remote -match 'github\.com[:/]([^/\s]+/[^/\s]+?)(\.git)?$') { $slug = $Matches[1] }
    if ($slug -and (Get-Command gh -ErrorAction SilentlyContinue)) {
        $ciArgs = @('run', 'list', '--repo', $slug, '--branch', 'main', '--limit', '1',
                    '--json', 'conclusion,status,headSha,createdAt')
        # ⚠ `2>$null` 은 방패가 아니라 잡아서 넘긴다(당김 손 머리의 「리다이렉트가 곧 위험이다」) — 안 잡으면 gh 의 403 한 줄이
        #   배포를 통째로 죽인다.
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
            # 결론이 아직 없으면(돌고 있다 · 줄 서 있다) 초록도 빨강도 아니다 — 남은 작업에 안 올린다.
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

# --- 전역형 도구 — 저장소 고리 앞에 한 번 ---
# 무엇이 전역형인지도, 어느 저장소의 선언을 합칠지도 이 스크립트는 모른다 — `--install-global` 갈래가 안다. 여기는 한 번
#   부른다는 것만 든다.
# 저장소 걸음이 하나도 없으면 이 걸음도 없다 — 다 살아 있는 기계에 매번 승인을 묻지 않는다. 전역 선언(`tools.global.conf`)은
#   저장소마다 배포된 사본이라, 전역형 도구가 늘거나 바뀌면 그 저장소의 선언 지문이 같이 어긋나 위에서 걸음이 서고, 그러면
#   이 걸음도 선다.
# 「도구가 닿나」는 여기서 안 잰다 — 계획은 파일만 보므로, 선언은 그대로인데 기계에서 도구만 빠진 자리는 안 걸린다. 지난
#   설치가 진 자리는 `--needs-install` 이 실패 기록으로 들고, 그 밖의 부재는 세션 훅의 진단이 매 세션 낸다.
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

# --- 제거 후보: 원본에 없는 씨앗 파일 ---
# ⚠ 씨앗 폴더(`seeds\…`)만 센다 — `posco` 는 프록시가 제 기록(`proxy.log` · `*.pid`)을 쓰는 자리라 원본에 없는 파일이 곧
#   쓰레기가 아니다. 씨앗은 새 프로젝트가 복사해 출발하는 자리라 원본에서 걷은 부품이 홈에 남으면 계속 퍼지고, 설정 저장소를
#   든 PC 에서는 설치기가 이 폴더를 비켜서므로(PAISetup install.ps1 「공용 자산」 걸음) 걷는 손이 여기다. 원본 이력이 걷은 파일은
#   이미 기본 실행의 걸음이라(`Get-SeedColumn` 의 Gone) 여기서 다시 안 센다 — 두 번 실으면 `-Prune` 판의 둘째 걷기가 없는 파일에 진다.
$goneSet = @{}
foreach ($g in @($seedCol.Gone)) { $goneSet[$g.Path] = $true }
foreach ($sd in ($seedDirs | Where-Object { $_ -like 'seeds\*' })) {
    $sSrc = Join-Path $src $sd
    $sDst = Join-Path $dst $sd
    if (-not (Test-Path $sSrc) -or -not (Test-Path $sDst)) { continue }
    Get-ChildItem $sDst -Recurse -File | Where-Object { $_.FullName -notmatch '\\__pycache__\\' -and -not $goneSet[$_.FullName] } | ForEach-Object {
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

if ($Prune) { $plan += $prunable }

# --- 사용자 환경변수 ---
# 한국어 윈도우의 인코딩 구멍은 둘이고 서로 다른 자리다:
#   · PowerShell 5.1 은 BOM 없는 .ps1 을 ANSI(cp949)로 읽는다 → utf8-bom.sh 훅이 막는다
#   · 파이썬은 open() 기본 인코딩을 locale 에서 가져온다(역시 cp949) → 이 변수가 막는다
# PYTHONUTF8=1 은 PEP 540 UTF-8 모드다 — open() · stdio 를 UTF-8 로 고정해 파일마다 encoding= 을 적는 규율을 없앤다.
# 저장소 settings.json 의 env 로도 같은 값을 걸지만 그것은 Claude Code 세션 안에서만 산다 — 사람이 연 터미널 · 에디터에서도
#   같으려면 사용자 환경변수여야 한다. 값이 고정이라 안내가 아니라 여기서 심는다.
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

# --- 실행 순서 — 배선을 맨 앞에 세운다 ---
# `core.hooksPath` 는 로컬 `git config` 한 줄이라 질 까닭이 없다. 그런데 계획을 짓는 차례로는 배포 걸음 뒤에 서고, 실행 고리는
#   `$ErrorActionPreference = 'Stop'` 아래 하나라 앞 걸음 하나가 던지면 뒤가 통째로 안 돈다.
# ⚠ 맨 앞에 안 세우면 앞 걸음 하나가 던질 때 커밋 게이트가 없는 채로 저장소가 서고, 그 부재는 조용하다 — 훅이 안 걸렸으니
#   안 걸렸다고 말할 자도 없고, 게이트를 안 탄 커밋은 되돌릴 수 없다. 뒤가 무엇으로 죽든 게이트만은 서게 둔다.
# 화면에 내는 목록도 이 순서다 — 계획을 굳힌 뒤에 세우니 사람이 읽는 차례와 실제로 도는 차례가 같다.
# 배선보다 앞에 서는 것은 당김 하나다 — 당김은 던지지 않으므로 「뒤가 무엇으로 죽든」은 그대로 서지만, 느린 망은 배선을
#   `$PullBatchTimeoutSec` 만큼까지 늦춘다. 커밋 게이트 배선의 임자는 매 세션 거는 세션 훅이고, 이 자리는 그 뒤를 받는다
$plan = @($plan | Where-Object { $_.Kind -eq 'githooks' }) +
        @($plan | Where-Object { $_.Kind -ne 'githooks' })

# --- GitHub 토큰의 만료 ---
# 사용자 환경변수 `GH_TOKEN` 이 세밀 토큰이면 만료가 강제다(GitHub 이 1년 안에 죽인다) — 죽는 날 gh 가 조용히 선다(값이
#   있기만 하면 「있음」이라 만료된 토큰이 안 갈린다). 응답 머리글에 만료일이 실려 오므로 호출 한 번으로 잰다 — 죽었으면(401)
#   실행 환경이 안 선 것(`$envDown`), 30일 안이면 사람이 할 일(`$todo`), 멀쩡하면 날짜를 한 줄 찍는다(초록도 편다). 그 밖에
#   못 재면 「못 쟀다」 한 줄만 남기고 배포를 막지 않는다.
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
                $todo += "GH_TOKEN 만료 ${left}일 남음 ($expDay) — GitHub 에서 재발급해 심은 자리(secrets.env · setx)를 고치거나, 안 쓰면 사용자 환경변수에서 지운다"
            } else {
                Write-Host "= GH_TOKEN 만료 $expDay (${left}일 남음)" -ForegroundColor DarkGray
            }
        }
    } catch {
        $code = $null
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        if ($code -eq 401) {
            $envDown += 'GH_TOKEN 이 죽었다 (401 — 만료됐거나 회수됐다). GitHub 에서 재발급해 심은 자리(secrets.env · setx)를 고치거나, 안 쓰면 사용자 환경변수에서 지운다'
        } else {
            Write-Host "· GH_TOKEN 만료 — 못 쟀다 (api.github.com 이 안 닿는다: $($_.Exception.Message))" -ForegroundColor DarkGray
        }
    }
}

# ============================ 보고와 승인 ============================
# 층 — 없다. 화면에 내고 묻기만 한다
# 하는 일 — 이미 맞는 것의 개수(`-ShowUnchanged` 면 줄마다) · 제거 후보(`-Prune` 이 없을 때) · 마지막 CI 줄 · 바꿀 것과 백업
#   자리를 낸다. 바꿀 것이 있으면 승인을 묻는다 — `y`(또는 `Y`)로 시작하는 답만 통과하고, 빈 답(물어볼 자리가 없다)과 다른
#   답은 멈춘다. `-Yes` 면 안 묻는다. 바꿀 것이 없으면 남은 수동 작업을 내고 돌아간다
# 앞에서 받는 것 — 계획 단계의 `$plan` · `$same` · `$prunable` · `$gateReport` · `$todo`
# 안 하는 것 — 아무것도 안 바꾼다 · 바꿀 것이 없거나 승인이 안 서면 여기서 돌아가고 실행 단계는 안 돈다

# 이미 맞는 것은 개수만 낸다 — 한 줄씩 펴면 매 실행이 100줄을 넘어 정작 봐야 할 「바꿀 것」이 묻힌다. 어긋난 것을 찾을 때만
#   -ShowUnchanged 로 편다.
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

# 마지막 CI 줄들은 「바꿀 것이 없습니다」 앞에 낸다 — 뒤에 두면 바꿀 것이 없는 기계에서 그 return 에 걸려 영영 안 보인다.
if ($gateReport.Count -gt 0) {
    Write-Host ''
    $gateReport | ForEach-Object { Write-Host $_ }
}

if ($plan.Count -eq 0) {
    # 계획이 비어도 안 선 것(`$envDown` — 못 견줘 포기한 파일 같은)이 있으면 초록으로 안 끝난다 — 머리말의 종료 값 계약이다
    if ($envDown.Count -eq 0) { Write-Host "`n바꿀 것이 없습니다. 이미 최신입니다." -ForegroundColor Green }
    if ($todo.Count -gt 0) {
        Write-Host "`n남은 수동 작업:" -ForegroundColor Yellow
        $todo | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    }
    if ($envDown.Count -gt 0) {
        Write-Host "`n! 실행 환경이 안 섰습니다 — $($envDown.Count)곳:" -ForegroundColor Red
        $envDown | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        exit 1
    }
    return
}

Write-Host "`n바꿀 것 ($($plan.Count)개)" -ForegroundColor Cyan
$plan | ForEach-Object { Write-Host "  $($_.Text)" -ForegroundColor Cyan }
Write-Host "`n덮어쓰거나 치우는 파일은 먼저 여기 백업됩니다:"
Write-Host "  $backup"
# 손의 줄은 저 백업을 안 탄다 — 손이 백업하는 것은 그 줄마다 「~ 백업」 한 줄이 따로 선다(자리는 손이 정한다).
#   그 줄 없이 선 손의 「- 제거」 는 백업 없이 걷힌다는 뜻이라, 위 한 줄만 보이면 화면이 거짓말을 한다.
if (@($plan | Where-Object { $_.Kind -eq 'homes' }).Count) {
    Write-Host "  규범 · 룰 · 에이전트 · 스킬 줄은 여기가 아니다 — 손(tool-homes.py)이 백업하는 것은 「~ 백업」 줄로 따로 선다"
}

if (-not $Yes) {
    # 승인은 명시적인 y 하나만 통과시키고, 나머지는 전부 「안 함」이다.
    # ⚠ 비대화 세션(`powershell.exe -File` · 출력이 파이프로 물린 자리)에서 Read-Host 는 던지지 않고 조용히 $null 을 돌려준다.
    #   그래서 「아니라고 했나」가 아니라 「예라고 했나」를 재고, 답이 없는 것과 아니라고 한 것을 같은 값으로 둔다 — 부정을 재는
    #   관문은 침묵 앞에서 열려 무인 실행이 스스로 승인한다.
    $answer = $null
    try {
        $answer = Read-Host "`n진행할까요? (y/N)"
    } catch {
        # 던지는 호스트도 있다 — 죽게 두면 아무것도 안 바꿨는데 종료 값 1 이 나가 부르는 쪽이 배포 실패로 센다. 「안 함」으로 내린다.
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


# ============================ 실행 ============================
# 층 — 홈 · 저장소 · 환경. 기계 층(전역형 도구)과 저장소 설치는 세션 훅을 불러 맡긴다
# 하는 일 — 계획의 걸음을 차례대로 돌고 걸음마다 한 줄을 낸다. 덮거나 걷는 파일은 먼저 `$backup` 에 뜬다(판 줄은 안
#   뜬다). 도구 홈의 규범 · 룰 · 에이전트 · 스킬은 손을 계획과 같은 명령으로 한 번 불러 맡긴다(백업은 손이 제 자리에
#   뜬다). 전역 설치는 이 저장소의 세션 훅을 `--install-global` 로, 저장소 설치는 그 저장소의 세션 훅을 `--install` 로
#   부른다. 끝에 백업 자리 · 남은 수동 작업 · 판정을 내고, 실행 환경이 안 선 것(`$envDown`)이 있으면 `exit 1` 로 끝난다
# 앞에서 받는 것 — 승인을 지난 `$plan`(배선이 맨 앞) · 당김의 `$pulledRepos`(못 당긴 저장소에는 안 민다) · 계획의 `$todo` ·
#   `$envDown`(여기서 더 쌓아 끝에 낸다)
# 안 하는 것 — 계획에 없는 것은 안 바꾼다 · 당기지 않는다 · 무엇을 깔지 모른다 — 그것은 세션 훅이 안다 · 무엇이 어느 도구 홈에
#   가나 모른다 — 그것은 손이 안다

# ── 이번 실행의 표식 — 같은 배포 안에서만 통하는 인용 좌표다 ──────────────────
# 전역 걸음(`--install-global`)이 도구마다 ✅ 를 내면 훅이 그것을 홈의 명부에 이 표식과 함께 적고, 이어 도는 저장소
#   걸음(`--install`)의 진단은 표식이 같을 때만 그 줄을 인용하고 프로브를 안 띄운다 — 같은 명제를 저장소마다 다시 안 잰다.
# ⚠ 캐시가 아니라서 값이 실행마다 갈려야 한다 — 시각에 PID 를 붙여 같은 초에 둘이 돌아도 안 겹치고, 고리가 끝나면 이름을
#   걷어 지난 실행의 명부는 아무도 못 읽는다. 고리 앞에 한 번만 세운다 — 걸음마다 세우면 갈리는 순간 전역 걸음이 적은 줄을
#   저장소 걸음이 못 알아본다.
$env:CLAUDE_CONFIG_RUN = "$(Get-Date -Format 'yyyyMMddTHHmmss')-$PID"

$homesRan = $false   # 손은 한 번만 돈다 — 아래 `homes` 걸음

# ── 걸음 종류마다 걸린 초 — 줄마다 찍지 않고 종류별로 합쳐 끝에 한 번 낸다 ──────────
# 계획은 수백 줄이라 줄마다 초를 붙이면 읽을 수 없고, 가르려는 것은 「파일 붓기가 먹나 · 깔기가 먹나」라 종류가 그 물음의
#   단위다. 이 합은 걸음 안의 시간만 든다 — 계획 세우기와 당김은 고리 밖이라, 끝 줄에 그렇게 적어 합을 전체로 안 읽게 한다.
$stepSecs = @{}
Write-Host ""
foreach ($step in $plan) {
    $tStep = $deploySw.Elapsed.TotalMilliseconds
    switch ($step.Kind) {

        'copy' {
            # 저장소 배포본은 그 저장소를 당긴 뒤에 밀고, 못 당겼으면 안 민다.
            # ⚠ 여기서 당기지 않는다 — 당김은 계획 앞에서 이미 돌았고 이 걸음은 그 판정(`$pulledRepos`)을 읽기만 한다. 여기 두면
            #   밀 것이 없는 회차에는 당김도 함께 사라진다
            # 판정에 없는 저장소는 당길 것이 없던 자리(`.git` 이 없다)라 막을 까닭도 없다.
            $skip = $false
            if ($step.Repo -and $pulledRepos.ContainsKey($step.Repo) -and -not $pulledRepos[$step.Repo]) {
                Write-Host "· 건너뜀  $($step.To)  (그 저장소를 지금 못 맞춘다 — 까닭은 위 당김 줄. 밀면 다음 당김이 막힌다)" -ForegroundColor Yellow
                $skip = $true
            }
            # 계획 뒤에 다른 손(VS Code 로 연 세션의 배경 당김)이 같은 파일을 앉혔을 수 있어 한 번 더 견준다 — 같은 것을 다시
            #   쓰면 백업만 쌓인다.
            #   계획 뒤에 다른 프로그램이 그 파일을 쥐었으면 못 견준 것이라 포기한다(`Get-HashOrWhy` 머리).
            if (-not $skip -and (Test-Path -LiteralPath $step.To)) {
                $hFrom = Get-HashOrWhy $step.From
                $hTo   = Get-HashOrWhy $step.To
                $unread = if ($hFrom.Why) { "$($step.From) — $($hFrom.Why)" } elseif ($hTo.Why) { "$($step.To) — $($hTo.Why)" } else { '' }
                if ($unread) {
                    Write-Host "! 포기  $($step.To) — 못 읽어 견주지 못했다" -ForegroundColor Red
                    $envDown += "배포를 포기한 파일 — $unread"
                    $skip = $true
                } elseif ($hFrom.Hash -eq $hTo.Hash) {
                    Write-Host "= 동일  $($step.To)  (그 사이 같아졌다)" -ForegroundColor DarkGray
                    $skip = $true
                }
            }
            if (-not $skip) {
                if (Test-Path $step.To) { Save-Backup $step.To }
                # ⚠ 대상이 링크면 링크를 걷고 쓴다 — 링크를 따라 쓰면 손으로 링크를 걸어 둔 PC(대상 → 이 저장소의 진본)에서는
                #   진본을 덮는다. 내용은 위 백업이 이미 떴다.
                $toItem = Get-Item -LiteralPath $step.To -Force -ErrorAction SilentlyContinue
                if ($toItem -and $toItem.LinkType) { Remove-Item -LiteralPath $step.To -Force }
                New-Item -ItemType Directory -Force -Path (Split-Path $step.To -Parent) | Out-Null
                # 복사는 끌 수 있는 일꾼이 한다(`Invoke-FileWorker` 머리) — 진 파일은 빨강에 이름째 남기고 다음 파일로 간다
                $r = Invoke-FileWorker -From $step.From -To $step.To -LimitSec $FileOpLimitSec -PollMs $FileOpPollMs
                if ($r.Ok) {
                    Write-Host "+ 배포  $($step.To)"
                } else {
                    Write-Host "! 포기  $($step.To) — $($r.Why)" -ForegroundColor Red
                    $envDown += "배포를 포기한 파일 — $($step.To): $($r.Why)"
                }
            }
        }

        'stamp' {
            # 백업을 안 남긴다 — 지난 판 줄은 되살릴 자산이 아니라 다시 재면 나오는 값이다.
            # ⚠ BOM 없는 UTF-8 · LF 로 쓴다 — 읽는 자가 파이썬이라, BOM 이 붙으면 첫 낱말에 그 세 바이트가 딸려 판이 엉뚱한
            #   글자로 읽힌다(5.1 의 `Set-Content -Encoding UTF8` 은 BOM 을 붙인다).
            New-Item -ItemType Directory -Force -Path (Split-Path $step.Path -Parent) | Out-Null
            [System.IO.File]::WriteAllText($step.Path, $step.Line + "`n",
                                          (New-Object System.Text.UTF8Encoding($false)))
            Write-Host "+ 판 줄  $($step.Path)  ($($step.Line))"
        }

        'homes' {
            # 손의 바꿀 줄마다 걸음이 하나지만 손은 한 번 돈다 — 첫 걸음에서 계획과 같은 명령을 `--dry-run` 없이 돌리고 나머지는
            #   지나간다. 손이 실제로 한 일을 줄마다 낸다. 경고 · 오류는 할 일에 올린다 — 계획에서 올린 같은 줄은 한 번만 선다.
            if ($homesRan) { break }
            $homesRan = $true
            $homesDone = ConvertFrom-ToolHomesOutput (Invoke-ToolHomes -Src $src)
            $homesDone.Steps | ForEach-Object { Write-Host $_.Text }
            foreach ($n in $homesDone.Notes) { if ($todo -notcontains $n) { $todo += $n } }
            if ($homesDone.Failed) {
                Write-Host "! 규범 · 룰 · 에이전트 · 스킬 — 손이 다 못 놓았습니다 (까닭은 아래 남은 수동 작업)" -ForegroundColor Red
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
            # 전역형 도구를 기계에 한 번 깐다 — 저장소 걸음보다 먼저 선다. 고리 안의 배선(정션)이 걸 물건이 그때 이미 깔려
            #   있어야 한다. 고리 표식(`CLAUDE_CONFIG_DEPLOYING`)도 저장소 걸음과 같은 뜻으로 세운다 — `--install-global` 은 deploy
            #   로 되넘기지 않지만, 이 부름이 고리 안이라는 사실은 이름으로 서 있어야 한다.
            # ⚠ 종료코드를 받는다 — 전역형 도구가 안 선 채로 저장소 걸음이 초록을 내면 부재가 통과로 읽힌다. 판정은 훅이 내고
            #   여기는 받아 나르기만 한다.
            $env:CLAUDE_CONFIG_DEPLOYING = '1'
            & $bash ($step.Script -replace '\\', '/') --install-global
            if ($LASTEXITCODE -ne 0) {
                Write-Host "! 전역 설치가 오류로 끝났습니다 (exit $LASTEXITCODE)" -ForegroundColor Red
                $envDown += '전역형 도구 — 안 선 것이 남았다 (위 ❌ 줄이 곧 고칠 자리)'
                $todo += "확인:  bash '$($step.Script)' --install-global"
            }
        }

        'install' {
            # Git Bash(`$bash`)로 돌린다 — PATH 의 bash 는 WSL 일 수 있다. 경로는 슬래시로 바꿔 넘긴다 — 역슬래시는 bash 가
            #   이스케이프로 먹는다. 훅이 진단을 그대로 찍으므로 여기서 한 번 더 판정하지 않는다.
            # ⚠ 고리를 끊는 표식 — 훅은 밖(설치기 · 사람)이 `--install` 로 부르면 개인 칸을 세우고 이 스크립트에 넘긴다. 여기서
            #   부른 훅이 또 넘기면 고리라, 이 이름이 서 있으면 훅은 저장소 하나의 설치로 간다.
            $env:CLAUDE_CONFIG_DEPLOYING = '1'
            & $bash ($step.Script -replace '\\', '/') --install
            if ($LASTEXITCODE -ne 0) {
                # ⚠ 여기가 목표를 이뤘나를 아는 유일한 자리다 — 훅은 `--install` 에서도 꺼진 검사를 종료코드로 낸다. 그 신호를
                #   받아 위층까지 물고 가지 않으면 검사가 꺼진 채로 화면이 초록으로 끝난다.
                Write-Host "! 저장소 설치가 오류로 끝났습니다 (exit $LASTEXITCODE)  $($step.Repo)" -ForegroundColor Red
                $envDown += "$($step.Repo) — 꺼진 검사가 남았다 (위 진단의 ❌ 줄이 곧 고칠 자리)"
                $todo += "확인:  bash '$($step.Script)' --check"
            }
        }

        'userenv' {
            # setx 와 같은 자리(사용자 환경변수)에 쓴다 — setx.exe 는 값을 1024자에서 자르고 이 API 는 안 자른다.
            [Environment]::SetEnvironmentVariable($step.Name, $step.Value, 'User')
            Write-Host "+ 설정  사용자 환경변수 $($step.Name)=$($step.Value)"
        }

        'remove' {
            Save-Backup $step.Path
            Remove-Item $step.Path -Force
            Write-Host "- 제거  $($step.Path)"
            # 파일만 걷으면 빈 폴더가 `seeds/<이름>/scripts/` 같은 껍데기로 남아 홈 목록을 흐린다 — 비었을 때만 위로 올라가며 걷는다.
            # ⚠ 홈 바로 아래 자리(`projects` · `seeds` …)는 비어도 둔다 — 그 자리는 배포가 아니라 앱이 세운다.
            $parent = Split-Path $step.Path -Parent
            while ($parent -and
                   ((Split-Path $parent -Parent) -ne $dst) -and ($parent -ne $dst) -and
                   (Test-Path $parent) -and -not (Get-ChildItem -LiteralPath $parent -Force | Select-Object -First 1)) {
                Remove-Item -LiteralPath $parent -Force
                Write-Host "- 제거  $parent  (빈 폴더)"
                $parent = Split-Path $parent -Parent
            }
        }
    }
    $stepSecs[$step.Kind] = [double]$stepSecs[$step.Kind] + ($deploySw.Elapsed.TotalMilliseconds - $tStep)
}
# 복사 일꾼을 거둔다(`Invoke-FileWorker` 머리) — 고리 안의 마지막 복사 뒤로는 쓸 데가 없다.
Stop-FileWorker

# 걸음 종류별 초 — 큰 것부터. 0.1 초에 못 미치는 종류는 안 낸다 — 줄만 늘고 가르는 값이 없다.
# ⚠ 밀리초로 세고 초로 낸다 — 정수 초로 세면 한 걸음이 1 초 미만인 종류가 전부 0 으로 깎여, 수백 개를 밀어도 합이 0 이다.
if ($plan.Count) {
    $shown = @($stepSecs.GetEnumerator() | Where-Object { $_.Value -ge 100 } | Sort-Object Value -Descending)
    if ($shown.Count) {
        Write-Host ("`n걸음에 걸린 초 — " +
                    (($shown | ForEach-Object { "$($_.Key) $([math]::Round($_.Value / 1000, 1))" }) -join ' · ') +
                    "  (계획 세우기 · 당김은 이 고리 밖이라 안 들어 있다)") -ForegroundColor DarkGray
    }
}

# 표식 둘은 이 실행과 함께 걷는다 — `.\deploy.ps1` 로 부르면 이 셸에 남아, 같은 셸에서 손으로 부른 훅이 지난 걸음의 명부를
#   제가 잰 것으로 읽고, 손으로 부른 `--install` 이 고리 안의 부름으로 읽혀 deploy 에 안 넘기고 전역 설치도 안 한다.
Remove-Item Env:CLAUDE_CONFIG_RUN -ErrorAction SilentlyContinue
Remove-Item Env:CLAUDE_CONFIG_DEPLOYING -ErrorAction SilentlyContinue

if (Test-Path $backup) { Write-Host "`n백업: $backup" }

if ($todo.Count -gt 0) {
    Write-Host "`n남은 수동 작업:" -ForegroundColor Yellow
    $todo | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}

# ── 판정 — 환경이 안 섰으면 「완료」라고 말하지 않고 종료 값 1 로 끝난다 ─────────────────
# 이 스크립트를 부르는 자(훅 `--install` → `install.ps1` → 설치 화면)가 물어볼 데가 이 종료 값뿐이다 — 0 으로 끝나면 저장소
#   설치가 꺼진 검사를 안고 끝나도 화면이 초록이다.
if ($envDown.Count -gt 0) {
    Write-Host "`n! 실행 환경이 안 섰습니다 — $($envDown.Count)곳:" -ForegroundColor Red
    $envDown | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "`n끝내지 못했습니다. 위 진단의 까닭을 고친 뒤 다시 돌립니다." -ForegroundColor Red
    exit 1
}

# 「재시작」 한 낱말로 뭉개지 않는다 — 다시 여는 자리가 둘이다. 규범 · 룰 · 스킬은 세션이 뜰 때 읽혀 새 세션이면 되지만, 새로
#   깐 도구는 PATH 를 타서 Claude Code 를 띄운 앱이 설치 뒤에 떠야 보인다 — 앱은 뜰 때 PATH 를 한 번 복사한다.
Write-Host "`n완료. 이미 열려 있던 Claude Code 세션에는 안 들어갑니다 — 새 세션부터 적용되고, 새로 깐 도구는 Claude Code 를 띄운 앱(VS Code · 데스크탑 앱 · 터미널)을 완전히 닫았다 다시 열어야 잡힙니다." -ForegroundColor Green
