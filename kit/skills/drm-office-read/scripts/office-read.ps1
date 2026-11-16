<#
    drm-office-read 의 읽는 부품 — Fasoo 에이전트가 도는 PC 의 오피스를 태워 문서에서 글자와 「글 밖」의 셈을 뽑는 함수만 든다.
    본체(인자 · 대상 모으기 · 화면 · 파일 쓰기 · 끝 정리)는 안 든다 — 스킬의 `read-drm.ps1` 이 그 본체고, 제 꼴로 내는 앱은 제 본체를
    쓰고 여기를 점 소싱한다. 실어도 아무것도 돌지 않고 표준 출력에 아무것도 안 낸다.
    점 소싱으로 싣는다 — 세션 규칙이 먼저다(Open-OwnedDocument · Assert-* 를 여기가 부른다):
        . (Join-Path $PSScriptRoot 'office-session.ps1')
        . (Join-Path $PSScriptRoot 'office-read.ps1')

    왜 앱을 태우나: Fasoo DRM 은 파일을 통째로 자기 컨테이너로 감싼다. 머리 바이트가 `%PDF-`·`PK` 가 아니게 되므로 어떤 파서
    (PDFium·pdfplumber·python-docx·openpyxl)도 형식 인식 단계에서 죽는다. 정식 오피스 앱은 그 보호를 복호해 주므로 그것을 태운다.

    계약 — $DRM_OFFICE_READ_CONTRACT 가 든다. 부르는 쪽은 실은 뒤 이 값을 제가 아는 판과 견준다.
      · 앱 이름은 'Word' | 'Excel' | 'PPT' — $HANDLER 가 확장자를 이 이름으로 보내고, office-session.ps1 의 Kind 와 같다
      · New-OfficeJob · Set-OfficeJobKill · Join-OfficeJob — 띄운 오피스를 이 프로세스의 Job(KILL_ON_JOB_CLOSE)에 묶는 손
      · Get-FileHead · Test-PlainFormat — 머리 바이트 · 감겼나
      · New-OfficeApp -AppName -SpawnedPids ([ref]해시) -Job — 앱 하나를 띄워 돌려준다. 띄우기 전에 없던 PID 가운데 이 앱의 것만
        해시(PID → 앱 이름)에 더하고 Job 에 넣는다. 워드 · 엑셀은 매크로를 끈 채 띄운다($MSO_AUTOMATION_FORCE_DISABLE). 파워포인트를 띄울 때
        $PptWasRunning 을 부르는 쪽의 스크립트 범위에 둔다(아래)
      · Close-OfficeApps -AppByName (앱 이름 → 앱 개체) -SpawnedPids 해시 -Job -PptWasRunning — 판이 쓴 앱을 끝내는 한 자리다. 앱을
        끄고(Exit-OfficeApp) · Quit 뒤에도 남은 프로세스를 끝내고 · Job 손잡이를 닫는다. 내는 것은 없다. 프로세스를 강제로 끝내는 줄은
        이 함수에만 있다. 부르기 전에 이 판이 연 문서를 닫는다(Close-OwnedDocument) — 남은 문서가 곧 판정이다
      · Get-OfficeAppPid -App -AppName — 앱 개체 뒤의 프로세스 PID. 앱의 창 손잡이로 묻고, 못 물으면 0
      · Read-WithWord · Read-WithExcel · Read-WithPPT -App -LiteralPath → @{ Text = [string]; Visual = [hashtable] }
        Visual 의 열쇠는 영어다 — tables · images · shapes · formulas · charts · fields. 0 인 열쇠는 없다. 파워포인트는 글 없는
        낱 도형(그림 · 도형을 안 가른다)을 images 에 센다. 사람 말로 옮기는 것은 부르는 쪽 몫이다(read-drm.ps1 의 Format-Visual)
      · Format-Cell · Get-PptLeafShapes · Measure-*Visual · Add-Count — 위 셋이 쓰는 부품. 따로 불러도 된다
      · 남긴 글자 — Get-KeptTextDir · Get-KeptPrint -LiteralPath · Find-KeptText -Print · Save-KeptText -Name -Print -Line -Source -Text.
        읽은 글자를 홈 아래 한 자리($KEPT_TEXT_DIR_ENV 가 없으면 ~/.drm-read-text)에 「파일 이름.지문.md」로 남기고, 같은 바이트의 파일을
        지문(SHA-256 앞 12 자)으로 알아본다 — 이름이 달라도 바이트가 같으면 같은 글자다. 남긴 파일은 머리 두 줄(읽을 때의 한 줄 · 원본과
        뽑은 때) 뒤 $KEPT_SPLIT 아래가 글자다. 이 손은 남긴 것을 지우지 않는다 — 치우는 것은 사람이다
      · 남긴 그림 — Get-KeptShotDir -Name -Print. 같은 자리 아래 폴더 「파일 이름.지문」의 경로를 낸다(짓지 않는다). 그 안의 그림 이름과
        기록은 그림을 뜨는 손(capture_slides.ps1 · capture_pages.ps1)이 든다
      · 그림 줄이기 — Convert-ShotsToWebp -Png 경로들 [-MaxEdge] → PNG 경로 → 나갈 경로. 뜬 PNG 들을 씨앗의 줄이는 손에 한 번에 넘겨
        WebP 로 바꾼다(못 줄인 것은 PNG 그대로). 앱을 다 끝낸 뒤 한 번 부른다 — 줄이는 손은 프로세스를 띄운다.
        Convert-ShotToWebp -Png [-MaxEdge] 는 한 장짜리 꼴이다
      · 번호 고름 — ConvertTo-NumberList -Value -Name. 「1,3 5」 꼴의 쪽 · 장 고름을 번호 열로 풀고, 번호가 아닌 낱말이 있으면 그 낱말을
        대며 던진다. 빈 고름의 뜻과 범위 밖 가름은 부르는 쪽 몫이다
      · 상수 — $HANDLER · $PROCESS_OF · $MSO_AUTOMATION_FORCE_DISABLE · $OFFICE_EXIT_WAIT_MS · $OFFICE_EXIT_POLL_MS · $SHRINK_ARGS_MAX_CHARS ·
        $INV · $XL_ERROR_TEXT · $PPT_GROUP_DEPTH_MAX · $PPT_SEAT_LEGEND · $PPT_SEAT_TAG · $PPT_BREAKS · $PPT_CELL_BREAK · $PPT_CELL_SAME_PT
      · 파워포인트 글은 머리 한 줄($PPT_SEAT_LEGEND) 뒤 장마다 도형을 위→아래 · 왼→오른으로 세워 줄마다 [위 · 왼] 꼬리표를 앞세운다.
        표의 합친 칸은 첫 칸에만 글을 두고 덮인 칸은 비운다
    판을 올리는 자 — 함수 이름 · 인자 · 내는 꼴(열쇠 포함) · Job 의 뜻이 바뀌면 1 을 올린다. 함수를 더하거나 안을 고치는 것은 안 올린다.

    $PptWasRunning — New-OfficeApp 이 돌려준 파워포인트가 띄우기 전부터 떠 있던 프로세스인가(붙은 자리인가)를 $script: 범위에 둔다.
    점 소싱한 함수의 $script: 는 실은 쪽의 스크립트 범위라 그 변수는 부르는 쪽 것이다 — 끝에서 Close-OfficeApps -PptWasRunning(제 끝
    정리를 쓰는 본체는 Exit-OfficeApp -WasRunning)에 넘긴다. 돌려주지 않는 까닭: 돌려주면 New-OfficeApp 의 내는 꼴이 앱 하나에서 둘로
    바뀌어 부르는 쪽이 다 풀어 받아야 한다.

    진단은 Write-Warning 으로 낸다 — 표준 출력에는 아무것도 안 낸다. 표준 출력이 제 계약인 앱(JSON 한 줄 따위)은 경고 흐름을 제 자리로
    보낸다 — 경고를 내는 함수는 고급 함수라 `-WarningVariable` · `-WarningAction` 이 선다(New-OfficeApp 은 안에서 부른 것까지 모은다).
#>

$DRM_OFFICE_READ_CONTRACT = 1

# ── 남긴 글자 — 같은 바이트의 문서는 앱을 다시 안 띄우고 남긴 글자로 답한다(결정 0231) ──────────────────────
# 감긴 파일은 읽을 때마다 앱을 띄워야 하고(건당 수 초 · 창이 뜬다) 같은 문서를 다시 읽는 일이 잦다. 규칙은 여기 한 자리다 — 스킬의
# read-drm.ps1 과 이 부품을 싣는 앱이 같은 자리 · 같은 꼴로 남기고 찾는다. 글자 파일은 .md 다 — Fasoo 가 .txt · .csv 는 감싸고 .md 는
# 평문으로 둔다
$KEPT_TEXT_DIR_ENV = 'DRM_READ_TEXT_DIR'
$KEPT_SPLIT = "`n---`n"                # 남긴 파일에서 머리와 글자를 가르는 줄
$KEPT_TEXT_EXT = '.md'
$KEPT_PRINT_CHARS = 12                 # 지문 — SHA-256 의 앞 몇 자

function Get-KeptTextDir {
    $fromEnv = [Environment]::GetEnvironmentVariable($KEPT_TEXT_DIR_ENV)
    if ($fromEnv) { return $fromEnv }
    return (Join-Path $HOME '.drm-read-text')
}

function Get-KeptPrint {
    # 파일 바이트의 지문. 다른 프로세스가 독점으로 쥔 파일이면 던진다 — 부르는 쪽이 「지문 없음 · 읽기만」으로 받는다
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    # ⚠ -ErrorAction Stop — Get-FileHash 는 모듈 함수라 부르는 쪽의 Stop 을 안 물려받아, 잠긴 파일에 날 오류를 화면에 찍고 $null 을 낸다
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256 -ErrorAction Stop).Hash.Substring(0, $KEPT_PRINT_CHARS).ToLower()
}

function Find-KeptText {
    # 그 지문으로 남긴 글자 → @{ Path; Line(읽을 때의 한 줄); Text } — 없거나 · 못 읽거나 · 머리가 없거나(이 손이 남긴 것이 아니다) ·
    # 글자가 비었으면 $null. 빈 글자를 남긴 것으로 치면 그 문서는 다시는 앱으로 안 읽힌다 — 비었으면 앱으로 다시 읽어 본다.
    # 던지지 않는다 — 남긴 파일을 다른 프로세스가 쥐었어도(백신 · DRM 에이전트가 훑는 동안) 부르는 쪽은 앱으로 읽으면 된다
    param([Parameter(Mandatory = $true)][string]$Print)
    try {
        $dir = Get-KeptTextDir
        if (-not (Test-Path -LiteralPath $dir -PathType Container)) { return $null }
        $hit = Get-ChildItem -LiteralPath $dir -File -Filter "*.$Print$KEPT_TEXT_EXT" -ErrorAction Stop | Sort-Object Name | Select-Object -First 1
        if (-not $hit) { return $null }
        $raw = [System.IO.File]::ReadAllText($hit.FullName, [System.Text.Encoding]::UTF8)
        $at = $raw.IndexOf($KEPT_SPLIT)
        if ($at -lt 0) { return $null }
        $text = $raw.Substring($at + $KEPT_SPLIT.Length)
        if (-not $text.Trim()) { return $null }
        return @{ Path = $hit.FullName; Line = ($raw.Substring(0, $at) -split "`n")[0].Trim(); Text = $text }
    } catch { return $null }
}

function Save-KeptText {
    # 뽑은 글자를 「이름.지문.md」로 남기고 그 경로를 낸다. 남길 자리를 못 짓거나 못 쓰면 던진다 — 부르는 쪽이 「못 남겼다」로 받고
    # 읽기는 잇는다(글자는 이미 뽑혔고, 못 남긴 것은 다음에 한 번 더 읽힐 뿐이다)
    param([Parameter(Mandatory = $true)][string]$Name, [Parameter(Mandatory = $true)][string]$Print,
          [string]$Line = '', [string]$Source = '', [string]$Text = '')
    $dir = Get-KeptTextDir
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $path = Join-Path $dir ('{0}.{1}{2}' -f $Name, $Print, $KEPT_TEXT_EXT)
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
    [System.IO.File]::WriteAllText($path, "$Line`n원본 $Source · 뽑은 때 $stamp$KEPT_SPLIT$Text", (New-Object System.Text.UTF8Encoding($false)))
    return $path
}

# ── 남긴 그림 — 같은 바이트의 문서에서 앞서 뜬 그림은 앱을 다시 안 띄우고 그 그림으로 답한다 ──────────────────
# 그림을 뜨는 것도 글자와 같은 값을 치른다(앱을 띄우고, 슬라이드쇼는 화면을 가져간다). 자리는 남긴 글자 곁의 폴더 「파일 이름.지문」
# 이다 — 한 문서의 글자와 그림이 한 자리에 서고 치울 때도 한 자리다. 그림의 이름과 무엇을 떴나의 기록은 뜨는 손이 든다
function Get-KeptShotDir {
    # 그 지문의 그림 폴더 경로 — 이미 있으면 그것(이름이 달라도 지문이 같으면 같은 문서다), 없으면 「이름.지문」 자리. 짓지는 않는다
    param([Parameter(Mandatory = $true)][string]$Name, [Parameter(Mandatory = $true)][string]$Print)
    $dir = Get-KeptTextDir
    try {
        if (Test-Path -LiteralPath $dir -PathType Container) {
            $hit = Get-ChildItem -LiteralPath $dir -Directory -Filter "*.$Print" -ErrorAction Stop | Sort-Object Name | Select-Object -First 1
            if ($hit) { return $hit.FullName }
        }
    } catch { }
    return (Join-Path $dir ('{0}.{1}' -f $Name, $Print))
}

# 줄이는 손에 한 번에 넘기는 그림 이름 글자 수의 한도 — 명령 줄 하나는 cmd 를 거치면 8,191 자까지다(python 이 .cmd · .bat 껍데기로
# 깔린 PC 가 그렇다 · 바로 뜨는 exe 는 32,767 자). 줄이는 손의 경로와 인자 몫을 남긴 값이고, 그림이 많아 넘으면 묶음을 나눠 부른다
$SHRINK_ARGS_MAX_CHARS = 6000

function Convert-ShotsToWebp {
    # 뜬 PNG 들을 씨앗의 줄이는 손(_shrink.py --batch — 진본은 설정 저장소 seeds/check/)에 한 번에 넘겨 무손실 WebP 로 바꾸고,
    # PNG 경로 → 나갈 경로(줄였으면 WebP · 못 줄였으면 그 PNG)의 해시를 낸다. 긴 변은 -MaxEdge, 안 주면 그 손의 기본 눈금이다. 그림의
    # 값은 치수가 정하고 WebP 는 바이트만 줄인다. 줄이는 손을 못 찾거나 · 못 띄우거나 · 진 그림은 경고하고 PNG 그대로 둔다 — 큰
    # 그림이라고 안 내는 것보다 낫고, 값을 더 무는 판이라 그 판정이 한 줄 서야 한다.
    # 줄였나는 그림마다 WebP 가 생겼나로 가른다 — 넘기기 전에 그 이름의 WebP 를 지운다. 안 지우면 줄이는 손이 통째로 진 판(PIL 없음)에
    # 앞서 남은 그림이 이번에 줄인 것으로 세어진다.
    # 줄이는 손은 프로세스를 띄우므로 그림마다 부르지 않는다 — 뜨는 손은 앱을 다 끝낸 뒤 이 함수를 한 번 부른다
    param([string[]]$Png = @(), [int]$MaxEdge = 0)
    $converted = @{}
    foreach ($shot in $Png) { $converted[$shot] = $shot }
    if ($Png.Count -eq 0) { return $converted }
    $shrink = @(
        (Join-Path $HOME '.claude/seeds/check/_check/_shrink.py'),
        (Join-Path $PSScriptRoot '..\..\..\..\seeds\check\_check\_shrink.py')
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $shrink) {
        Write-Warning "줄이는 부품을 못 찾았다 — 원본 치수 그대로 낸다 (~/.claude/seeds/check/_check/_shrink.py)"
        return $converted
    }
    $edge = @()
    if ($MaxEdge -gt 0) { $edge = @('--max-edge', $MaxEdge) }
    $webpOf = @{}                          # 넘긴 PNG → 생겨야 할 WebP
    # 묶음 하나가 줄이는 손 한 번이다 — 한 폴더의 그림을 그 폴더에서 이름만으로 넘긴다(경로째 넘기면 명령 줄이 금세 찬다).
    # 뜨는 손은 한 폴더에 뜨므로 보통은 한 묶음이고, 폴더가 바뀌거나 글자 한도를 넘을 때만 묶음이 갈린다
    $bundles = @()                         # @{ Dir; Pairs = (PNG 이름, WebP 이름, …); Chars }
    $bundle = $null
    foreach ($shot in $Png) {
        $webp = [System.IO.Path]::ChangeExtension($shot, '.webp')
        try {
            if (Test-Path -LiteralPath $webp) { Remove-Item -LiteralPath $webp -Force }
        } catch {
            Write-Warning "앞서 남은 그림을 못 지워 줄이지 않는다($($_.Exception.Message)) — $webp"
            continue
        }
        $shotDir = [System.IO.Path]::GetDirectoryName($shot)
        if (-not $shotDir) { $shotDir = (Get-Location).ProviderPath }
        # 이름 앞의 「.\」 — 「-」 로 시작하는 이름이 줄이는 손의 인자 이름으로 읽히지 않는다
        $pair = @(('.\' + [System.IO.Path]::GetFileName($shot)), ('.\' + [System.IO.Path]::GetFileName($webp)))
        $cost = $pair[0].Length + $pair[1].Length + 6    # 짝 하나가 명령 줄에서 차지하는 글자 — 따옴표와 빈칸까지
        if ($null -eq $bundle -or $bundle.Dir -ne $shotDir -or ($bundle.Chars + $cost) -gt $SHRINK_ARGS_MAX_CHARS) {
            $bundle = @{ Dir = $shotDir; Pairs = @(); Chars = 0 }
            $bundles += $bundle
        }
        $bundle.Pairs += $pair
        $bundle.Chars += $cost
        $webpOf[$shot] = $webp
    }
    foreach ($bundle in $bundles) {
        $pairs = $bundle.Pairs
        Push-Location -LiteralPath $bundle.Dir
        # 종료 값은 안 본다 — 한 짝이 져도 남은 짝은 구워지므로 아래에서 짝마다 결과 파일로 가른다
        try { python -X utf8 $shrink --batch @pairs @edge | Out-Null }
        catch { Write-Warning "줄이는 손을 못 띄웠다: $($_.Exception.Message)" }
        finally { Pop-Location }
    }
    $lost = 0
    foreach ($shot in @($webpOf.Keys)) {
        if (Test-Path -LiteralPath $webpOf[$shot]) {
            Remove-Item -LiteralPath $shot -Force
            $converted[$shot] = $webpOf[$shot]
        } else { $lost++ }
    }
    if ($lost -gt 0) {
        Write-Warning "그림 $lost 장의 줄이기가 졌다 — 원본 치수 그대로 낸다. 위 오류를 본다 (흔한 까닭은 PIL 이 없는 것: python -m pip install pillow)"
    }
    return $converted
}

function Convert-ShotToWebp {
    # 한 장짜리 꼴 — 뜬 PNG 하나를 줄여 나갈 경로(WebP · 못 줄였으면 PNG)를 낸다. 여러 장은 Convert-ShotsToWebp 에 한 번에 넘긴다
    param([Parameter(Mandatory = $true)][string]$Png, [int]$MaxEdge = 0)
    return (Convert-ShotsToWebp -Png @($Png) -MaxEdge $MaxEdge)[$Png]
}

# ── 번호 고름 — 그림을 뜨는 손 둘(capture_pages.ps1 의 -Pages · capture_slides.ps1 의 -Slides)이 같은 꼴을 받는다 ──────────
function ConvertTo-NumberList {
    <# 쉼표나 공백으로 나눈 번호 고름 → 정수 열(준 차례 · 겹친 번호는 한 번). 번호가 아닌 낱말이 하나라도 있으면 그 낱말과 받는 꼴을
       대며 던진다 — 조용히 버리면 고른 것의 일부만 뜨고 부른 쪽은 다 뜬 줄 안다. 빈 고름은 빈 열이다 — 「안 골랐다」의 뜻(전부인가 ·
       멈추나)과 범위 밖 가름은 부르는 쪽이 정한다(끝 번호는 문서를 열어야 안다). $Name 은 실패 문구에 대는 인자 이름이다 #>
    param([string]$Value, [Parameter(Mandatory = $true)][string]$Name)
    $list = @()
    foreach ($token in ($Value -split '[,\s]+' | Where-Object { $_ })) {
        if ($token -notmatch '^\d+$') {
            throw "-$Name 는 쉼표나 공백으로 나눈 번호만 받는다(예: 1,3,5 — 범위는 번호를 낱낱이 적는다) — 번호가 아닌 낱말: $token"
        }
        $parsed = [int]$token
        if ($list -notcontains $parsed) { $list += $parsed }
    }
    return $list
}

# 어느 확장자를 어느 앱이 드나. PDF 는 워드가 든다 — Acrobat COM 은 이 기계에서
# 클래스 미등록(0x80040154)이라 못 탄다.
$HANDLER = @{
    '.doc'  = 'Word';  '.docx' = 'Word';  '.rtf'  = 'Word';  '.pdf' = 'Word'
    '.xls'  = 'Excel'; '.xlsx' = 'Excel'; '.xlsm' = 'Excel'; '.csv' = 'Excel'
    '.ppt'  = 'PPT';   '.pptx' = 'PPT'
}
$PROCESS_OF = @{ 'Word' = 'WINWORD'; 'Excel' = 'EXCEL'; 'PPT' = 'POWERPNT' }
# 띄운 워드 · 엑셀에 거는 값 — msoAutomationSecurityForceDisable. 자동화로 띄운 앱은 매크로를 다 켜는 것이 기본이라, 안 걸면 여는
# 순간 도는 매크로(AutoOpen · Workbook_Open)가 사람 확인 없이 돈다
$MSO_AUTOMATION_FORCE_DISABLE = 3
$INV = [Globalization.CultureInfo]::InvariantCulture
# 엑셀의 Value2 는 오류 칸(#N/A 등)을 음수 정수로 준다 — 그대로 적으면 -2146826246 이 진짜 값처럼 보인다
$XL_ERROR_TEXT = @{ -2146826288 = '#NULL!'; -2146826281 = '#DIV/0!'; -2146826273 = '#VALUE!'; -2146826265 = '#REF!'
                    -2146826259 = '#NAME?'; -2146826252 = '#NUM!'; -2146826246 = '#N/A' }
# 묶음 안 묶음을 어디까지 펴나 — 그 아래는 도형 하나로 센다
$PPT_GROUP_DEPTH_MAX = 20
# 파워포인트 글의 도형 꼬리표 — 읽는 모델이 나란한 칸의 머리말과 값을 같은 「왼」끼리 짝짓는 근거다.
# 만든 차례(z)대로 내면 머리말 바로 뒤에 다른 칸의 값이 서고 모델은 그것을 그 머리말의 값으로 읽는다
$PPT_SEAT_LEGEND = '(도형 앞 [위 · 왼] 은 그 도형이 장 안에 놓인 자리다 — 포인트, 왼쪽 위가 0)'
$PPT_SEAT_TAG = '[위 {0:0} · 왼 {1:0}]'
# 파워포인트 글의 문단 끝(CR)과 문단 안 줄 나눔(VT) — 꼬리표 줄 안에 남으면 읽는 도구마다 줄이 붙거나 끊긴다
$PPT_BREAKS = @([string][char]13, [string][char]11)
$PPT_CELL_BREAK = '<br>'
# 표 칸 두 개가 같은 합친 칸인지 가르는 자리 상자의 허용 차(pt) — 다른 칸은 칸 크기만큼 어긋난다
$PPT_CELL_SAME_PT = 0.5

# ── 띄운 앱은 이 프로세스에 묶는다 ───────────────────────────────────────
# 오피스는 COM 서버라 이 PowerShell 의 자식이 아니다 — 부르는 쪽이 시한으로 이 프로세스를 끊으면 본체의
# finally 가 안 돌고, 숨은 앱이 문서를 연 채 남는다. 그래서 띄운 PID 를 Job(KILL_ON_JOB_CLOSE)에 넣는다 —
# 이 프로세스가 어떻게 끝나든 Job 손잡이가 닫히며 그 앱이 함께 끝난다. 사람이 먼저 띄운 앱은 안 든다
# (New-OfficeApp 이 이 판이 띄운 프로세스만 넣는다). ⚠ 끊긴 판에서는 그 몇 초 사이 사람이 이 숨은 인스턴스로 연 문서도
# 함께 닫힌다 — 정상으로 끝나는 판은 Close-OfficeApps 가 남은 문서를 세어 그 앱을 살려 둔다.
# 한 프로세스에 두 번 실려도 선다 — 같은 이름의 형을 두 번 더하면 Add-Type 이 진다
if (-not ('DrmRead.Job' -as [type])) {
    Add-Type -Namespace DrmRead -Name Job -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true)] public static extern IntPtr CreateJobObject(IntPtr attrs, string name);
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool SetInformationJobObject(IntPtr job, int infoClass, IntPtr info, uint size);
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
[DllImport("kernel32.dll", SetLastError = true)] public static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool CloseHandle(IntPtr handle);
'@
}
if (-not ('DrmRead.Window' -as [type])) {
    Add-Type -Namespace DrmRead -Name Window -MemberDefinition @'
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
'@
}

function New-OfficeJob {
    <# 끝내기 규칙을 켠 Job 손잡이를 낸다 — 못 만들면 Zero 를 내고 알린다(그때는 PID 로만 쫓는다) #>
    [CmdletBinding()]
    param()
    $job = [DrmRead.Job]::CreateJobObject([IntPtr]::Zero, $null)
    if ($job -eq [IntPtr]::Zero) { Write-Warning 'Job 을 못 만들었다 — 끊기면 띄운 오피스가 남을 수 있다'; return $job }
    if (-not (Set-OfficeJobKill -Job $job -On $true)) { Write-Warning 'Job 에 끝내기 규칙을 못 걸었다 — 끊기면 띄운 오피스가 남을 수 있다' }
    return $job
}

function Set-OfficeJobKill {
    <# Job 의 끝내기 규칙을 켜거나($On) 끈다 — 끈 뒤 손잡이를 닫으면 묶인 앱은 산다 #>
    param([IntPtr]$Job, [bool]$On)
    if ($Job -eq [IntPtr]::Zero) { return $false }
    # JOBOBJECT_EXTENDED_LIMIT_INFORMATION — LimitFlags 는 x64 · x86 모두 16 바이트 자리, 구조 크기는 포인터 크기가 가른다
    $size = if ([IntPtr]::Size -eq 8) { 144 } else { 112 }
    $info = [Runtime.InteropServices.Marshal]::AllocHGlobal($size)
    try {
        for ($i = 0; $i -lt $size; $i++) { [Runtime.InteropServices.Marshal]::WriteByte($info, $i, 0) }
        $flags = if ($On) { 0x2000 } else { 0 }                                  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        [Runtime.InteropServices.Marshal]::WriteInt32($info, 16, $flags)
        return [DrmRead.Job]::SetInformationJobObject($Job, 9, $info, [uint32]$size)   # JobObjectExtendedLimitInformation
    } finally { [Runtime.InteropServices.Marshal]::FreeHGlobal($info) }
}

function Join-OfficeJob {
    <# 띄운 PID 들을 Job 에 넣는다 — 못 넣은 것은 알린다 #>
    [CmdletBinding()]
    param([IntPtr]$Job, [int[]]$Pids)
    if ($Job -eq [IntPtr]::Zero) { return }
    foreach ($id in $Pids) {
        $h = [DrmRead.Job]::OpenProcess(0x0101, $false, $id)        # PROCESS_TERMINATE | PROCESS_SET_QUOTA
        if ($h -eq [IntPtr]::Zero -or -not [DrmRead.Job]::AssignProcessToJobObject($Job, $h)) {
            Write-Warning "띄운 오피스(PID $id)를 Job 에 못 넣었다 — 끊기면 남을 수 있다"
        }
        if ($h -ne [IntPtr]::Zero) { [void][DrmRead.Job]::CloseHandle($h) }
    }
}

function Read-HeadBytes {
    <# 파일 머리 $Count 바이트. 오피스가 열어 쥔 파일도 읽게 쓰기 · 지우기를 함께 허락해 연다 —
       `ReadAllBytes` 는 그 파일에서 공유 위반으로 진다. #>
    param([string]$LiteralPath, [int]$Count)
    $fs = [System.IO.File]::Open($LiteralPath, 'Open', 'Read', 'ReadWrite, Delete')
    try {
        $buf = New-Object byte[] $Count
        $n = 0
        while ($n -lt $Count) { $r = $fs.Read($buf, $n, $Count - $n); if ($r -le 0) { break }; $n += $r }
        if ($n -lt $Count) { $buf = if ($n -eq 0) { [byte[]]@() } else { $buf[0..($n - 1)] } }
        return ,[byte[]]$buf
    } finally { $fs.Dispose() }
}

function Get-FileHead {
    <# 파일 머리 8바이트를 눈으로 읽을 꼴로. DRM 이 감쌌으면 `. DRMONE` 처럼 나온다. #>
    param([string]$LiteralPath)
    $bytes = Read-HeadBytes $LiteralPath 8
    $n = $bytes.Length
    if ($n -eq 0) { return '(빈 파일)' }
    -join ($bytes[0..($n - 1)] | ForEach-Object {
        if ($_ -ge 32 -and $_ -lt 127) { [char]$_ } else { '.' }
    })
}

function Test-PlainFormat {
    <# 감기지 않은 원래 형식인가. 감겼으면 $false — 그때만 이 부품이 값을 낸다. #>
    param([string]$LiteralPath)
    $bytes = Read-HeadBytes $LiteralPath 4
    if ($bytes.Length -lt 4) { return $false }
    $sig = -join ($bytes[0..3] | ForEach-Object { [char]$_ })
    return ($sig -eq '%PDF' -or $sig.StartsWith('PK') -or $sig.StartsWith('{\rt') -or
            ($bytes[0] -eq 0xD0 -and $bytes[1] -eq 0xCF))   # 옛 오피스 OLE
}

function Get-OfficeAppPid {
    <# 앱 개체 뒤의 프로세스 PID — 그 앱의 창 손잡이에게 묻는다. 못 물으면 0 이다(워드는 문서 창이 열리기 전에 창 손잡이를 안 준다) #>
    param($App, [string]$AppName)
    $handle = 0
    try {
        switch ($AppName) {
            'Word'  { $handle = [long]$App.ActiveWindow.Hwnd }
            'Excel' { $handle = [long]$App.Hwnd }
            'PPT'   { $handle = [long]$App.HWND }
        }
    } catch { return 0 }
    if (-not $handle) { return 0 }
    $owner = [uint32]0
    [void][DrmRead.Window]::GetWindowThreadProcessId([IntPtr]$handle, [ref]$owner)
    return [int]$owner
}

function New-OfficeApp {
    <# 앱 하나를 띄운다. 파일마다 띄우면 건당 수 초씩 붙으므로 앱은 재사용한다.
       이 판이 띄운 프로세스만 $SpawnedPids 에 더하고 Job 에 넣는다 — 사람이 쓰던 프로세스는 안 든다. 어느 프로세스가 이 앱인가는
       앱의 창 손잡이가 답한다(Get-OfficeAppPid). 못 물으면 띄우기 전에 없던 PID 가 하나일 때만 그것으로 친다 — 둘 이상이면 띄우는
       사이 사람이 연 앱이 섞였다는 뜻이라 어느 것도 이 판의 것으로 안 친다(못 가린 프로세스를 Job 에 넣으면 사람의 문서가 함께 끝난다) #>
    [CmdletBinding()]
    param([string]$AppName, [ref]$SpawnedPids, [IntPtr]$Job)
    $beforePids = @(Get-Process -Name $PROCESS_OF[$AppName] -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    switch ($AppName) {
        'Word' {
            $a = New-Object -ComObject Word.Application
            $a.Visible = $false
            $a.DisplayAlerts = 0          # wdAlertsNone — 변환 대화창이 뜨면 무인 실행이 멈춘다
            try { $a.AutomationSecurity = $MSO_AUTOMATION_FORCE_DISABLE } catch { }
        }
        'Excel' {
            $a = New-Object -ComObject Excel.Application
            $a.Visible = $false
            $a.DisplayAlerts = $false
            try { $a.AutomationSecurity = $MSO_AUTOMATION_FORCE_DISABLE } catch { }
        }
        'PPT' {
            # ⚠ 파워포인트는 Visible=$false 를 거부하고 하나만 뜬다(그 앱만 그렇다) — 떠 있었으면 그 앱에 붙는다.
            $a = New-Object -ComObject PowerPoint.Application
            # 매크로 끔은 여기 안 건다 — 붙은 자리가 사람의 앱이면 건 값이 그 앱에 남는다
        }
    }
    $newPids = @(Get-Process -Name $PROCESS_OF[$AppName] -ErrorAction SilentlyContinue |
                 Where-Object { $beforePids -notcontains $_.Id } | Select-Object -ExpandProperty Id)
    $appPid = Get-OfficeAppPid -App $a -AppName $AppName
    if ($appPid) {
        $newPids = @($newPids | Where-Object { $_ -eq $appPid })
    } elseif ($newPids.Count -gt 1) {
        Write-Warning "$AppName 를 띄우는 사이 같은 앱이 더 떴다 — 어느 것이 이 판의 것인지 못 가려 Job 에 안 넣는다(끊기면 띄운 앱이 남을 수 있다)"
        $newPids = @()
    }
    if ($AppName -eq 'PPT') {
        # 붙은 자리가 띄우기 전부터 있던 프로세스인가 — 부르는 쪽의 스크립트 범위에 둔다(머리말). 끝에서 그 앱을 안 끄는 근거다.
        # 프로세스 이름만 세지 않는다 — Quit 뒤에도 남은 껍데기 프로세스가 있으면 새로 띄운 앱까지 「사람의 것」으로 읽혀 안 꺼진다
        $script:PptWasRunning = if ($appPid) { $beforePids -contains $appPid } else { $beforePids.Count -gt 0 }
    }
    foreach ($id in $newPids) { $SpawnedPids.Value[$id] = $AppName }
    if ($newPids.Count -gt 0) { Join-OfficeJob -Job $Job -Pids $newPids }
    return $a
}

# Quit 한 앱이 스스로 끝나기를 기다리는 한도와 그 사이 다시 보는 틈(ms) — 한도를 넘겨 남은 프로세스만 강제로 끝낸다
$OFFICE_EXIT_WAIT_MS = 800
$OFFICE_EXIT_POLL_MS = 100

function Close-OfficeApps {
    <# 판이 쓴 앱들을 끝낸다 — 앱을 끄고 프로세스를 끝내는 판정은 이 함수 하나다(프로세스를 강제로 끝내는 줄은 여기뿐이다).
       받는 것 — -AppByName(앱 이름 → 앱 개체 · $null 은 건너뛴다) · -SpawnedPids(New-OfficeApp 이 채운 PID → 앱 이름) · -Job(없으면 Zero) ·
       -PptWasRunning(New-OfficeApp 이 둔 값). 부르기 전에 이 판이 연 문서를 닫는다(Close-OwnedDocument).
       판정은 PID 가 아니라 앱에게 묻는다 — 「이 판의 것이 아닌 문서가 열려 있나」:
         1. 앱마다 Exit-OfficeApp — 남은 문서가 없고 붙은 자리(사람이 쓰던 파워포인트)가 아니면 Quit 한다. 문서가 남았으면 판이 도는
            사이 사람이 이 인스턴스로 연 것이라 앱을 살려 둔다
         2. Quit 한 앱의 프로세스(이 판이 띄운 것)가 $OFFICE_EXIT_WAIT_MS 안에 스스로 안 끝나면 강제로 끝낸다 — 파워포인트는 Fasoo
            DRM 훅이 Quit 뒤에도 프로세스를 붙잡아 권한 경고창이 되풀이되고, 남은 프로세스는 문서 파일을 쥐어 다음 읽기 · 빌드를 막는다.
            Quit 을 안 한 앱은 끝내지 않는다 — 그때 남는 것은 숨은 앱이지 닫힌 사람의 문서가 아니다
         3. Job 손잡이를 닫는다 — Quit 을 안 한 채 살아 있는 프로세스(이 판이 띄운 것)가 하나라도 있으면 끝내기 규칙을 먼저 끈다
            (안 끄면 손잡이가 닫히며 그 앱이 함께 끝난다). 없으면 켠 채 닫아 남은 것을 거둔다. 끊긴 판은 여기 안 닿으니 Job 이
            그대로 끝낸다
       내는 것은 없다. 부른 뒤 -AppByName 의 앱 개체와 -Job 은 못 쓴다.
       ⚠ 고급 함수여야 한다 — 인자가 어긋나 못 묶인 값(이름과 값이 붙은 「-AppByName@{…}」)을 단순 함수는 말없이 버리고, 그러면 앱을
         하나도 안 받은 판이 되어 Job 이 사람의 문서째 끝낸다. 고급 함수는 그 자리에서 던진다 #>
    [CmdletBinding()]
    param([hashtable]$AppByName = @{}, [hashtable]$SpawnedPids = @{}, [IntPtr]$Job = [IntPtr]::Zero, [bool]$PptWasRunning = $false)
    $quitOf = @{}                          # 앱 이름 → Quit 했나. 거짓이면 문서가 남아(또는 못 세어) 살려 둔 것
    foreach ($kind in @($AppByName.Keys)) {
        if ($null -eq $AppByName[$kind]) { continue }
        $quitOf[$kind] = [bool](Exit-OfficeApp -App $AppByName[$kind] -Kind $kind -WasRunning (($kind -eq 'PPT') -and $PptWasRunning))
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()

    $quitPids = @{}                        # Quit 한 앱의, 이 판이 띄운 PID → 프로세스 이름
    foreach ($entry in @($SpawnedPids.GetEnumerator())) {
        if ($quitOf[[string]$entry.Value]) { $quitPids[[int]$entry.Key] = $PROCESS_OF[[string]$entry.Value] }
    }
    # 그 PID 가 아직 그 앱인가 — 끝난 PID 를 다른 프로세스가 물려받았으면 이름이 다르다
    $alive = {
        @($quitPids.Keys | Where-Object {
            $left = Get-Process -Id $_ -ErrorAction SilentlyContinue
            $left -and $left.ProcessName -eq $quitPids[$_]
        })
    }
    $watch = [Diagnostics.Stopwatch]::StartNew()
    while (@(& $alive).Count -gt 0 -and $watch.ElapsedMilliseconds -lt $OFFICE_EXIT_WAIT_MS) {
        Start-Sleep -Milliseconds $OFFICE_EXIT_POLL_MS
    }
    foreach ($id in @(& $alive)) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }

    if ($Job -ne [IntPtr]::Zero) {
        $keptAlive = $false                # Quit 을 안 한 앱의 프로세스가 살아 있나 — 앱을 못 받은 판(인자가 빈 판)도 여기 걸려 안 끝낸다
        foreach ($entry in @($SpawnedPids.GetEnumerator())) {
            if ($quitOf[[string]$entry.Value]) { continue }
            $left = Get-Process -Id ([int]$entry.Key) -ErrorAction SilentlyContinue
            if ($left -and $left.ProcessName -eq $PROCESS_OF[[string]$entry.Value]) { $keptAlive = $true }
        }
        if ($keptAlive -and -not (Set-OfficeJobKill -Job $Job -On $false)) {
            Write-Warning 'Job 의 끝내기 규칙을 못 껐다 — 살려 둔 앱이 이 프로세스와 함께 끝날 수 있다'
        }
        [void][DrmRead.Job]::CloseHandle($Job)
    }
}

# ── 글 밖에 있는 것을 센다 ────────────────────────────────────────────────
# 글자만 뽑으면 표 · 그림 · 수식 · 차트는 뽑히지 않거나 평탄해진다. 그래서 「글로 담기지 않는
# 것이 이 문서에 몇 개 있나」를 문서 자신에게 묻는다 — 셀 수 있는 값이라 0 이면 그림이 필요
# 없다고 단정할 수 있다. 글자 수로는 못 가른다: 몇 자부터 짧은가는 문서마다 달라 답이 없고,
# 셀 값만으로 완결된 시트와 수식 하나가 전부인 문서가 같은 길이로 나온다.
# 묻는 이름은 앱마다 다르다. 못 묻는 항목은 0 으로 둔다 — 판의 차이로 없는 속성이 있다.
# 열쇠는 영어(머리말의 계약) — 사람 말로 옮기는 것은 부르는 쪽이 한다.
function Add-Count {
    param([hashtable]$Into, [string]$Key, [scriptblock]$Get)
    try {
        $v = [int](& $Get)
        if ($v -gt 0) { $Into[$Key] = [int]$Into[$Key] + $v }
    } catch { }
}

function Measure-WordVisual {
    param($Doc)
    $c = @{}
    Add-Count $c 'tables'   { $Doc.Tables.Count }
    Add-Count $c 'images'   { $Doc.InlineShapes.Count }
    Add-Count $c 'shapes'   { $Doc.Shapes.Count }
    Add-Count $c 'formulas' { $Doc.OMaths.Count }
    Add-Count $c 'fields'   { $Doc.Fields.Count }
    return $c
}

function Measure-ExcelVisual {
    param($Book)
    $c = @{}
    foreach ($sheet in $Book.Sheets) {
        $charts = 0; $pictures = 0; $shapes = 0
        try { $charts = [int]$sheet.ChartObjects().Count } catch { }
        try { $pictures = [int]$sheet.Pictures().Count } catch { }
        try { $shapes = [int]$sheet.Shapes.Count } catch { }
        # Shapes 는 차트 · 그림까지 든다 — 빼지 않으면 한 차트가 「차트」와 「도형」으로 두 번 선다
        Add-Count $c 'shapes' { $shapes - $charts - $pictures }
        Add-Count $c 'charts' { $charts }
        Add-Count $c 'images' { $pictures }
    }
    Add-Count $c 'charts' { $Book.Charts.Count }   # 시트째 차트 — 위 고리가 안 센다
    return $c
}

function Get-PptLeafShapes {
    <# 도형 모음을 묶음 안까지 편 낱 도형의 열 — 묶음(msoGroup 6)과 묶음이 든 개체 틀(msoPlaceholder 14)은 제 글이
       없고 GroupItems 가 글을 든다. 안 펴면 묶음 안 글은 안 나오고 묶음 안 그림은 「글 밖」에 안 세어져, 「글 밖이
       0 이면 글자가 전부다」가 거짓이 된다. 깊이 상한을 넘는 묶음은 그 자리에서 도형 하나로 센다.
       빌린 규격 — 동료 저장소 sejuone-cloud/pgpt-one-click-connect `office-com-read/scripts/read-office.ps1` 의
       `Write-PPTShape`(2ef0ddb3f65c): 묶음이 든 개체 틀 · 깊이 상한. 손으로 따라간다 #>
    param($Shapes, [int]$Depth = 0)
    foreach ($shape in $Shapes) {
        $isGroup = $false
        try {
            $isGroup = ($shape.Type -eq 6)
            if (-not $isGroup -and $shape.Type -eq 14) { $isGroup = ([int]$shape.PlaceholderFormat.ContainedType -eq 6) }
        } catch { }
        if ($isGroup -and $Depth -lt $PPT_GROUP_DEPTH_MAX) {
            $items = $null
            try { $items = $shape.GroupItems } catch { }
            if ($items) { Get-PptLeafShapes -Shapes $items -Depth ($Depth + 1); continue }
        }
        $shape
    }
}

function Measure-PptVisual {
    param($Pres)
    # 장마다 글 없는 낱 도형을 센다 — 글이 든 도형과 표는 글자 추출이 이미 담았다. 그림과 도형을 안 가르고 images 하나에 센다
    $c = @{}
    foreach ($slide in $Pres.Slides) {
        foreach ($shape in (Get-PptLeafShapes -Shapes $slide.Shapes)) {
            try {
                if ($shape.HasTable -ne 0) { continue }
                if ($shape.HasTextFrame -and $shape.TextFrame.HasText) { continue }
            } catch { }
            $c['images'] = [int]$c['images'] + 1
        }
    }
    return $c
}

function Read-WithWord {
    param($App, [string]$LiteralPath)
    # 인자 셋 — 경로 · ConfirmConversions=$false · ReadOnly=$true.
    # ReadOnly 를 켜야 원본에 쓰기 잠금이 안 걸리고 DRM 이 수정으로 보지 않는다.
    # 사람이 같은 파일을 열어 두었으면 그 문서를 돌려받는다 — 읽기만 하고 닫지 않는다(office-session.ps1)
    $isPdf = ([System.IO.Path]::GetExtension($LiteralPath).ToLower() -eq '.pdf')
    if ($isPdf) { Assert-WordPdfQuiet $App }
    $session = Open-OwnedDocument -Kind 'Word' -Collection $App.Documents -Open { $App.Documents.Open($LiteralPath, $false, $true) }
    $doc = $session.Document
    try {
        $text = [string]$doc.Content.Text
        if ($isPdf) { Assert-PdfConverted $text }
        return @{ Text = $text; Visual = (Measure-WordVisual $doc) }
    } finally {
        Close-OwnedDocument $session    # SaveChanges=$false — 원본을 절대 안 고친다
    }
}

function Get-Decimals([string]$Fmt) {
    if ($Fmt -match '\.(0+)') { return $Matches[1].Length }
    return 0
}

function Format-Cell {
    <# Value2 한 칸 → 사람이 읽는 글. 수는 날짜 · 시각 · 백분율 · 천 단위 · 고정 소수만 열의 서식으로 되살리고
       나머지는 값 그대로다 — 보이는 글자(.Text)는 칸이 좁으면 날짜 대신 `########` 이 오고 칸마다 묻는 것이라,
       값을 한 번에 받고 뜻이 갈리는 꼴만 되살린다. 통화 기호 · 사용자 꼴 · 칸마다 다른 꼴은 날값으로 온다 —
       열마다 서식 하나만 묻기 때문이다.
       빌린 규격 — mail-secretary `secretary/office_read.ps1` 의 `Format-Cell`(9f9cf9b) · 오류 칸 표는 동료 저장소
       sejuone-cloud/pgpt-one-click-connect `office-com-read/scripts/read-office.ps1`(2ef0ddb3f65c). 손으로 따라간다 #>
    param($Value, [string]$Fmt)
    if ($null -eq $Value) { return '' }
    if ($Value -is [int]) { $e = $XL_ERROR_TEXT[$Value]; if ($e) { return $e } }
    if ($Value -isnot [double]) { return [string]$Value }
    $f = ($Fmt -replace '"[^"]*"', '' -replace '\[[^\]]*\]', '').ToLower()   # 따옴표 글 · [$-412] 꼴은 서식의 뜻이 아니다
    try {
        if ($f -match '[yd]') {
            $d = [DateTime]::FromOADate($Value)
            if ($f -match 'h') { return $d.ToString('yyyy-MM-dd HH:mm', $INV) }
            return $d.ToString('yyyy-MM-dd', $INV)
        }
        if ($f -match 'h' -and $f -match ':') { return [DateTime]::FromOADate($Value).ToString('HH:mm', $INV) }
    } catch { return $Value.ToString('R', $INV) }
    if ($f -match '%') { return ($Value * 100).ToString('F' + (Get-Decimals $f), $INV) + '%' }
    if ($f -match '#,##0') { return $Value.ToString('N' + (Get-Decimals $f), $INV) }
    if ($f -match '^0\.0+$') { return $Value.ToString('F' + (Get-Decimals $f), $INV) }
    return $Value.ToString('R', $INV)
}

function Read-WithExcel {
    param($App, [string]$LiteralPath)
    # UpdateLinks=0 · ReadOnly=$true
    $session = Open-OwnedDocument -Kind 'Excel' -Collection $App.Workbooks -Open { $App.Workbooks.Open($LiteralPath, 0, $true) }
    $book = $session.Document
    try {
        $out = [System.Text.StringBuilder]::new()
        foreach ($sheet in $book.Sheets) {
            [void]$out.AppendLine("### 시트: $($sheet.Name)")
            $used = $sheet.UsedRange
            $rows = [int]$used.Rows.Count; $cols = [int]$used.Columns.Count
            # 시트의 값을 한 번에 받는다 — 칸마다 COM 을 넘으면 칸 수만큼 프로세스를 오가 큰 시트 한 장이 몇 분이다
            $vals = $used.Value2
            if ($null -eq $vals) { continue }
            if ($vals -isnot [Array]) { $one = New-Object 'object[,]' 1, 1; $one[0, 0] = $vals; $vals = $one; $rows = 1; $cols = 1 }
            $lo1 = $vals.GetLowerBound(0); $lo2 = $vals.GetLowerBound(1)
            $sample = [Math]::Min(2, $rows)          # 첫 자료 줄의 서식 — 머리 줄은 대개 글이라 서식이 「일반」이다
            $fmts = @()
            for ($k = 1; $k -le $cols; $k++) {
                $f = ''
                try { $f = [string]$used.Cells.Item($sample, $k).NumberFormat } catch { }
                $fmts += $f
            }
            for ($r = 0; $r -lt $rows; $r++) {
                $cells = New-Object string[] $cols
                for ($k = 0; $k -lt $cols; $k++) { $cells[$k] = Format-Cell -Value $vals[($r + $lo1), ($k + $lo2)] -Fmt $fmts[$k] }
                # 행으로 묶는다 — 셀마다 줄을 끊으면 표라는 것이 사라져 모델이 못 알아본다.
                [void]$out.AppendLine('| ' + ($cells -join ' | ') + ' |')
            }
        }
        return @{ Text = $out.ToString(); Visual = (Measure-ExcelVisual $book) }
    } finally {
        Close-OwnedDocument $session
    }
}

function Get-PptCellBox {
    <# 표 칸 도형의 자리 상자 @(왼, 위, 너비, 높이)(pt). 못 읽으면 $null — 그 칸은 합친 칸으로 안 가른다 #>
    param($CellShape)
    try { return , @([double]$CellShape.Left, [double]$CellShape.Top, [double]$CellShape.Width, [double]$CellShape.Height) }
    catch { return $null }
}

function Test-PptSameBox {
    <# 두 상자가 $PPT_CELL_SAME_PT 안으로 같나 — 파워포인트 개체 모형에는 합침 여부 속성이 없어, 같은 상자가 곧 같은 합친 칸이다 #>
    param($A, $B)
    if ($null -eq $A -or $null -eq $B) { return $false }
    for ($i = 0; $i -lt 4; $i++) { if ([Math]::Abs($A[$i] - $B[$i]) -gt $PPT_CELL_SAME_PT) { return $false } }
    return $true
}

function Read-WithPPT {
    param($App, [string]$LiteralPath)
    # 사람이 같은 파일을 열어 두었으면 그 발표를 돌려받는다 — 읽기만 하고 닫지 않는다(office-session.ps1)
    # 경로 · ReadOnly=$true · Untitled=$false · WithWindow=$false
    $session = Open-OwnedDocument -Kind 'PPT' -Collection $App.Presentations -Open { $App.Presentations.Open($LiteralPath, $true, $false, $false) }
    $pres = $session.Document
    try {
        $out = [System.Text.StringBuilder]::new()
        [void]$out.AppendLine($PPT_SEAT_LEGEND)
        foreach ($slide in $pres.Slides) {
            [void]$out.AppendLine("### 장 $($slide.SlideIndex)")
            # 묶음 안 도형도 슬라이드 자리를 주므로 편 뒤 한 번에 세운다 — 위→아래 · 왼→오른, 같은 자리면 만든 차례
            $z = 0
            $seated = foreach ($leaf in (Get-PptLeafShapes -Shapes $slide.Shapes)) {
                $z++
                $top = 0.0; $left = 0.0
                try { $top = [double]$leaf.Top; $left = [double]$leaf.Left } catch { }
                [pscustomobject]@{ Shape = $leaf; Top = $top; Left = $left; Z = $z }
            }
            foreach ($seat in @($seated | Sort-Object Top, Left, Z)) {
                $shape = $seat.Shape
                $tag = $PPT_SEAT_TAG -f $seat.Top, $seat.Left
                if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                    $text = [string]$shape.TextFrame.TextRange.Text
                    foreach ($b in $PPT_BREAKS) { $text = $text.Replace($b, [Environment]::NewLine) }
                    [void]$out.AppendLine("$tag $text")
                }
                if ($shape.HasTable -ne 0) {
                    [void]$out.AppendLine("$tag 표")
                    try {
                        $tbl = $shape.Table
                        $boxes = @{}
                        for ($r = 1; $r -le $tbl.Rows.Count; $r++) {
                            $rowCells = @()
                            for ($c = 1; $c -le $tbl.Columns.Count; $c++) {
                                $cellShape = $tbl.Cell($r, $c).Shape
                                $box = Get-PptCellBox $cellShape
                                $boxes["$r,$c"] = $box
                                # 합친 칸의 덮인 자리는 첫 칸과 같은 글 · 같은 상자를 돌려준다 — 비워 두어야 값이 칸 수만큼 안 더해진다
                                if ((Test-PptSameBox $box $boxes["$r,$($c - 1)"]) -or (Test-PptSameBox $box $boxes["$($r - 1),$c"])) {
                                    $rowCells += ''
                                    continue
                                }
                                $cell = [string]$cellShape.TextFrame.TextRange.Text
                                foreach ($b in $PPT_BREAKS) { $cell = $cell.Replace($b, $PPT_CELL_BREAK) }
                                $rowCells += $cell
                            }
                            [void]$out.AppendLine('| ' + ($rowCells -join ' | ') + ' |')
                        }
                    } catch { }
                }
            }
        }
        return @{ Text = $out.ToString(); Visual = (Measure-PptVisual $pres) }
    } finally {
        Close-OwnedDocument $session
    }
}
