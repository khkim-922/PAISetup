<#
    drm-office-read 의 읽는 부품 — 오피스를 태워 문서에서 글자와 「글 밖」의 셈을 뽑는 함수만 든다. 본체(인자 · 화면 · 파일 쓰기 · 끝
    정리)는 스킬의 `read-drm.ps1` 이 들고, 제 꼴로 내는 앱은 제 본체를 쓴다. 실으면 곁의 값 파일 `handler.json` 에서 확장자 표만 읽고
    (못 읽으면 던진다) 그 밖에는 아무것도 돌지 않으며 표준 출력에 아무것도 안 낸다 — 진단은 Write-Warning 이다(경고를 내는 함수는 고급
    함수라 `-WarningVariable` · `-WarningAction` 이 선다).
    점 소싱으로 싣는다 — 세션 규칙이 먼저다(Open-OwnedDocument · Assert-* 를 여기가 부른다):
        . (Join-Path $PSScriptRoot 'office-session.ps1')
        . (Join-Path $PSScriptRoot 'office-read.ps1')

    계약 — $DRM_OFFICE_READ_CONTRACT 가 든다. 부르는 쪽은 실은 뒤 이 값을 제가 아는 판과 견준다. 함수 이름 · 인자 · 내는 꼴(열쇠 포함) ·
    Job 의 뜻이 바뀌면 1 을 올린다. 함수를 더하거나 안을 고치는 것은 안 올린다.
      · 앱 이름은 'Word' | 'Excel' | 'PPT' — $HANDLER 가 확장자를 이 이름으로 보내고, office-session.ps1 의 Kind 와 같다
      · New-OfficeJob · Set-OfficeJobKill · Join-OfficeJob — 띄운 오피스를 이 프로세스의 Job(KILL_ON_JOB_CLOSE)에 묶는 손
      · Get-FileHead · Test-PlainFormat — 머리 바이트 · 감겼나
      · New-OfficeApp -AppName -SpawnedPids ([ref]해시) -Job → 앱. 이 판이 띄운 PID 만 해시(PID → 앱 이름)에 더하고 Job 에 넣는다.
        파워포인트가 원래 떠 있었나를 부르는 쪽 스크립트 범위의 $PptWasRunning 에 둔다 — 끝에서 Close-OfficeApps 에 넘긴다
      · Close-OfficeApps -AppByName (앱 이름 → 앱 개체) -SpawnedPids 해시 -Job -PptWasRunning — 판이 쓴 앱을 끝내는 한 자리다. 내는 것은
        없다. 부르기 전에 이 판이 연 문서를 닫는다(Close-OwnedDocument) — 남은 문서가 곧 판정이다
      · Get-OfficeAppPid -App -AppName — 앱 개체 뒤의 프로세스 PID. 못 물으면 0
      · Read-WithWord · Read-WithExcel · Read-WithPPT -App -LiteralPath → @{ Text = [string]; Visual = [hashtable] }
        Visual 의 열쇠는 영어다 — tables · images · shapes · formulas · charts · fields. 0 인 열쇠는 없다. 파워포인트는 글 없는
        낱 도형을 images 에 센다. 사람 말로 옮기는 것은 부르는 쪽 몫이다(read-drm.ps1 의 Format-Visual)
      · Format-Cell · Get-PptLeafShapes · Measure-*Visual · Add-Count — 위 셋이 쓰는 부품. 따로 불러도 된다
      · 남긴 글자 — Get-KeptTextDir · Get-KeptPrint -LiteralPath · Find-KeptText -Print · Save-KeptText -Name -Print -Line -Source -Text.
        자리는 $KEPT_TEXT_DIR_ENV(없으면 ~/.drm-read-text), 이름은 「파일 이름.지문.md」, 머리 두 줄 뒤 $KEPT_SPLIT 아래가 글자다.
        남긴 것을 지우지 않는다
      · 남긴 그림 — Get-KeptShotDir -Name -Print. 같은 자리 아래 폴더 「파일 이름.지문」의 경로를 낸다(짓지 않는다)
      · 그림 줄이기 — Convert-ShotsToWebp -Png 경로들 [-MaxEdge] → PNG 경로 → 나갈 경로(못 줄인 것은 PNG). Convert-ShotToWebp 는 한 장짜리
      · 번호 고름 — ConvertTo-NumberList -Value -Name
      · 문서함 받은 파일 — Get-EcmDocsRoot(환경변수 → 곁의 places.json · 모르면 $null) · Test-EcmAgentFile -LiteralPath -Root · 멈춘 말 $ECM_REFUSAL. 본체가 앱을 띄우기
        전에 가린다 — 이 부품의 읽는 함수는 안 가린다(그 함수를 바로 싣는 쪽이 제 등급 문을 든다)
      · 상수 — $HANDLER(곁의 값 파일 $HANDLER_FILE 의 $HANDLER_KEY 에서 실은 해시 — 그 파일이 없으면 싣다 던진다) · $PROCESS_OF · $MSO_AUTOMATION_FORCE_DISABLE · $OFFICE_EXIT_WAIT_MS · $OFFICE_EXIT_POLL_MS · $SHRINK_ARGS_MAX_CHARS ·
        $INV · $XL_ERROR_TEXT · $PPT_GROUP_DEPTH_MAX · $PPT_SEAT_LEGEND · $PPT_SEAT_TAG · $PPT_BREAKS · $PPT_CELL_BREAK · $PPT_CELL_SAME_PT
      · 파워포인트 글은 머리 한 줄($PPT_SEAT_LEGEND) 뒤 장마다 도형을 위→아래 · 왼→오른으로 세워 줄마다 [위 · 왼] 꼬리표를 앞세운다.
        표의 합친 칸은 첫 칸에만 글을 두고 덮인 칸은 비운다

    왜 이 길인가 · 고칠 때 깨지기 쉬운 자리는 `references/DESIGN.md` 가 든다.
#>

$DRM_OFFICE_READ_CONTRACT = 1

# ── 남긴 글자 — 같은 바이트의 문서는 앱을 다시 안 띄우고 남긴 글자로 답한다 ──────────────────────
# 규칙은 여기 한 자리다 — read-drm.ps1 과 이 부품을 싣는 앱이 같은 자리 · 같은 꼴로 남기고 찾는다. .md 다 — Fasoo 가 .txt 는 감싼다
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
    # 그 지문으로 남긴 글자 → @{ Path; Line(읽을 때의 한 줄); Text } — 없거나 · 못 읽거나 · 머리가 없거나 · 글자가 비었으면 $null.
    # 던지지 않는다 — 부르는 쪽은 앱으로 읽으면 된다. 빈 글자를 남긴 것으로 치면 그 문서는 다시는 앱으로 안 읽힌다
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
# 자리는 남긴 글자 곁의 폴더 「파일 이름.지문」이다. 그림의 이름과 무엇을 떴나의 기록은 뜨는 손이 든다
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
    # 뜬 PNG 들을 씨앗의 줄이는 손(_shrink.py --batch)에 한 번에 넘겨 무손실 WebP 로 바꾸고, PNG 경로 → 나갈 경로(못 줄였으면 그 PNG)를
    # 낸다. 못 줄인 그림은 경고하고 PNG 그대로 둔다. ⚠ 줄였나는 WebP 가 생겼나로 가르므로 넘기기 전에 그 이름의 WebP 를 지운다
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
    <# 쉼표나 공백으로 나눈 번호 고름 → 정수 열(준 차례 · 겹친 번호는 한 번). 번호가 아닌 낱말이 있으면 그 낱말을 대며 던진다 — 조용히
       버리면 일부만 뜬다. 빈 고름은 빈 열이고 그 뜻과 범위 밖 가름은 부르는 쪽 몫이다. $Name 은 실패 문구에 대는 인자 이름이다 #>
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

# ── 문서함(ECM) 에이전트가 받은 파일 — 등급 문을 지난 길에서만 연다 ─────────────────────────────────────────────
# 이 스킬은 문서의 보안등급을 몰라, 받는 자리 밑의 파일은 부르는 쪽이 -EcmGated 를 줄 때만 연다(읽는 손 · 뜨는 손이 앱을 띄우기 전에
# 가린다). 그 깃발은 스킬 company-ecm 의 손이 등급 문을 지난 답에서만 이르고, 제 읽기에서 read-drm.ps1 을 부를 때도 준다. 받는 자리는
# 환경변수, 없으면 곁의 값 파일 places.json 의 ecm_docs_root 다 — 그 손과 DRM 길잡이 훅도 같은 파일을 읽는다. 값 파일이 이 스킬 안에
# 있어 company-ecm 이 안 깔린 홈(그 손을 안 고른 도구 홈)에서도 문이 같은 자리에 선다
$ECM_DOCS_ROOT_ENV = 'ECM_DOCS_ROOT'
$ECM_PLACES = Join-Path $PSScriptRoot 'places.json'
$ECM_PLACES_KEY = 'ecm_docs_root'
$ECM_REFUSAL = ('문서함(ECM) 에이전트가 받은 파일이다 — 이 스킬은 문서의 보안등급을 몰라 열지 않는다. 다음: 스킬 company-ecm 의 ' +
                'read <문서 열쇠> 로 받는다(기밀 · 핵심기술이면 그 손이 사람에게 묻게 멈추고, 표 · 그림을 뜰 길은 그 손의 답이 든다)')

function Get-EcmDocsRoot {
    # 문서함 에이전트가 받은 파일을 두는 자리 — company-ecm 손의 agent_docs_root 와 같은 차례(환경변수 → 값 파일)로 읽는다. 값 파일을 못
    # 읽으면 $null(거르지 않는다) — 값 파일은 이 스킬과 함께 깔리므로 깨진 설치에서만 그렇다
    $fromEnv = "$([Environment]::GetEnvironmentVariable($ECM_DOCS_ROOT_ENV))".Trim()
    if ($fromEnv) { return $fromEnv }
    try {
        $value = "$((Get-Content -LiteralPath $ECM_PLACES -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json).$ECM_PLACES_KEY)".Trim()
    } catch { return $null }
    if ($value) { return $value }
    return $null
}

function Test-EcmAgentFile {
    # 그 경로가 받는 자리($Root — 부르는 쪽이 Get-EcmDocsRoot 로 한 번 읽어 준다) 밑인가. 자리를 모르거나 경로를 못 풀면 거짓
    param([Parameter(Mandatory = $true)][string]$LiteralPath, [string]$Root)
    if (-not $Root) { return $false }
    try {
        $full = [IO.Path]::GetFullPath($LiteralPath)
        $base = [IO.Path]::GetFullPath($Root).TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
    } catch { return $false }
    return $full.StartsWith($base, [StringComparison]::OrdinalIgnoreCase)
}

# 어느 확장자를 어느 앱이 드나 — 곁의 값 파일 handler.json 의 handler 가 든다. 다른 스킬과 DRM 길잡이 훅이 같은 값을 읽어 받는 꼴을
# 가리므로 표는 그 파일 한 자리다(내주는 것은 scripts/handout.py). PDF 는 워드가 든다 — Acrobat COM 은 Acrobat 이 깔린 PC 에만 있다.
# 값 파일을 못 읽거나 표가 비면 싣는 자리에서 던진다 — 표 없이는 어느 파일도 못 읽는다
$HANDLER_FILE = Join-Path $PSScriptRoot 'handler.json'
$HANDLER_KEY = 'handler'
$HANDLER = @{}
$handlerTable = (Get-Content -LiteralPath $HANDLER_FILE -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json).$HANDLER_KEY
if ($handlerTable) {
    foreach ($pair in $handlerTable.PSObject.Properties) { $HANDLER[$pair.Name] = [string]$pair.Value }
}
Remove-Variable handlerTable
if ($HANDLER.Count -eq 0) { throw "확장자 표가 없다: $HANDLER_FILE 의 $HANDLER_KEY — 스킬 drm-office-read 를 다시 깐다" }
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
# 오피스는 COM 서버라 이 프로세스의 자식이 아니다 — 끊긴 판에도 숨은 앱이 안 남게 띄운 PID 를 Job(KILL_ON_JOB_CLOSE)에 넣는다.
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
    <# 앱 하나를 띄워 돌려준다(부르는 쪽이 재사용한다). 이 판이 띄운 프로세스만 $SpawnedPids 에 더하고 Job 에 넣는다 — 못 가린
       프로세스는 안 넣는다(넣으면 사람의 문서가 함께 끝난다 · 가르는 법은 references/DESIGN.md) #>
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
    <# 판이 쓴 앱들을 끝낸다 — 프로세스를 강제로 끝내는 줄은 여기뿐이다. 부르기 전에 이 판이 연 문서를 닫는다(Close-OwnedDocument).
       받는 것 — -AppByName(앱 이름 → 앱 개체 · $null 은 건너뛴다) · -SpawnedPids · -Job(없으면 Zero) · -PptWasRunning. 내는 것은 없고,
       부른 뒤 앱 개체와 -Job 은 못 쓴다. 차례(Quit → 남은 제 프로세스 끝내기 → Job 닫기)와 까닭은 references/DESIGN.md 「끝내는 판정」.
       ⚠ 고급 함수여야 한다 — 단순 함수는 못 묶인 인자를 말없이 버려, 앱을 하나도 안 받은 판의 Job 이 사람의 문서째 끝낸다 #>
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
# 「글로 담기지 않는 것이 몇 개 있나」를 문서 자신에게 묻는다 — 0 이면 그림이 필요 없다(글자 수로 못 가르는 까닭은 references/DESIGN.md).
# 못 묻는 항목은 0 으로 둔다 — 판의 차이로 없는 속성이 있다. 열쇠는 영어(머리말의 계약)다
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
    <# 도형 모음을 묶음(msoGroup 6 · 묶음이 든 개체 틀 14) 안까지 편 낱 도형의 열 — 안 펴면 묶음 안 글과 그림이 빠진다. 깊이 상한을
       넘는 묶음은 도형 하나로 센다. 빌린 규격 — sejuone-cloud/pgpt-one-click-connect `office-com-read/scripts/read-office.ps1` 의
       `Write-PPTShape`(2ef0ddb3f65c). 손으로 따라간다 #>
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
    <# Value2 한 칸 → 사람이 읽는 글. 수는 날짜 · 시각 · 백분율 · 천 단위 · 고정 소수만 열의 서식 $Fmt 로 되살리고 나머지는 값 그대로다
       (`.Text` 를 안 쓰는 까닭은 references/DESIGN.md). 빌린 규격 — mail-secretary `secretary/office_read.ps1` 의 `Format-Cell`(9f9cf9b) ·
       오류 칸 표는 sejuone-cloud/pgpt-one-click-connect `office-com-read/scripts/read-office.ps1`(2ef0ddb3f65c). 손으로 따라간다 #>
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
