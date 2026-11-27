# DRM 감긴 문서에서 글자를 뽑는다 — Fasoo 에이전트가 도는 PC 의 오피스를 태워서.
#
#     powershell -NoProfile -ExecutionPolicy Bypass -File read-drm.ps1 -Path <파일 · 폴더>… [-OutDir <폴더>] [-Preview N] [-NoKeep] [-EcmGated]
#         [-Sheets "<시트>/<시트>"] [-Slides "<장>,<장>"] [-Pages "<쪽>,<쪽>"] [-MaxCells N]
#
# 본체다 — 인자 · 대상 모으기 · 남긴 글자 · 화면 · `-OutDir` 출력 · 끝 정리. 읽는 함수는 `office-read.ps1` 이 든다.
# 내는 것 — 파일마다 「[딱지] 이름 …」 한 줄과 앞부분 글자(또는 `-OutDir` 의 `.md`), 끝에 셈 한 줄. 같은 바이트의 파일은 앱을 안 띄우고
# 남긴 글자로 답한다. 종료 값 — 0 준 파일을 다 읽었다(남긴 글자로 답한 것 포함) · 1 하나라도 못 읽었거나 읽을 파일이 없다(못 읽은
# 파일은 「[딱지] 이름 — 실패…」 한 줄 — 없는 경로 · 앱이 못 연 파일 · `$HANDLER` 에 없는 확장자 · `-EcmGated` 없이 준 문서함 받은 파일이
# 다 같다).
# 왜 앱을 태우나 · 남긴 글자의 꼴은 `references/DESIGN.md` 가 든다.

[CmdletBinding()]
param(
    # 읽을 파일들. 폴더를 주면 그 안의 지원 확장자를 전부 훑는다. 여럿은 이어 적거나(-File 의 남은 인자를 다 받는다) 쉼표로 잇는다.
    [Parameter(Mandatory = $true, Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Path,

    # 뽑은 글자를 넣을 폴더. 생략하면 화면으로만 낸다.
    [string]$OutDir,

    # 화면에 낼 때 파일마다 보여줄 앞부분 글자 수.
    [int]$Preview = 300,

    # 글자를 남기지도, 남긴 글자를 쓰지도 않는다 — 사람이 남기지 말라고 한 문서이거나, 제 자리에 글자를 따로 남기는 손이 부를 때.
    [switch]$NoKeep,

    # 문서함(ECM) 에이전트가 받은 파일도 연다 — 스킬 company-ecm 의 손이 등급 문을 지난 답에서 이를 때만 준다(office-read.ps1 「문서함」).
    [switch]$EcmGated,

    # 엑셀에서 읽을 시트 — 이름을 / 로 잇는다(엑셀 시트 이름에 못 드는 글자다 · 쉼표 · | 는 든다). 비면 전부. 글 맨 위 「목차」 표의 이름
    # 그대로 준다 — 앞뒤 빈칸까지 같아야 한다(목차는 이름 안의 | 를 \| 로 적는다)
    [string]$Sheets = '',

    # 파워포인트에서 읽을 장 번호 — 쉼표 · 공백으로 나눈다. 비면 전부
    [string]$Slides = '',

    # 워드 · PDF 에서 읽을 쪽 번호 — 쉼표 · 공백으로 나눈다. 비면 전부
    [string]$Pages = '',

    # 엑셀 한 부름에 값을 받는 칸 수의 한도 — 0 이면 한도 없음. 안 주면 읽는 부품의 기본값($XL_READ_CELLS_MAX)
    [int]$MaxCells = -1
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
. (Join-Path $PSScriptRoot 'office-session.ps1')
. (Join-Path $PSScriptRoot 'office-read.ps1')
# 파워포인트는 하나만 뜬다 — 띄우기 전에 사람이 쓰고 있었는지 New-OfficeApp 이 여기 적어, 끝에서 그 앱을 안 끈다
$PptWasRunning = $false
# 고름(시트 · 장 · 한도)을 준 부름은 남긴 글자를 쓰지도 남기지도 않는다 — 남긴 글자는 파일의 지문 하나로 찾아, 고른 일부를 남기면 다음의
# 온 판 부름이 그 일부를 받는다
$SheetList = @($Sheets -split '/' | Where-Object { $_ })
$SlideList = @(ConvertTo-NumberList -Value $Slides -Name 'Slides')
$PageList = @(ConvertTo-NumberList -Value $Pages -Name 'Pages')
$Picked = $SheetList.Count -gt 0 -or $SlideList.Count -gt 0 -or $PageList.Count -gt 0 -or $MaxCells -ge 0
if ($MaxCells -lt 0) { $MaxCells = $XL_READ_CELLS_MAX }

# 부품이 센 「글 밖」의 영어 열쇠 → 화면의 한국어. 파워포인트는 그림과 도형을 안 갈라 하나로 센다
$VISUAL_WORD = @{ tables = '표'; images = '그림'; shapes = '도형'; formulas = '수식'; charts = '차트'; fields = '필드' }
$VISUAL_WORD_PPT = @{ images = '그림·도형' }

# 센 것을 한 줄로 — 0 이면 빈 글이다(부를 것이 없다)
function Format-Visual {
    param([hashtable]$Counts, [string]$AppName)
    if (-not $Counts -or $Counts.Count -eq 0) { return '' }
    $words = @{}
    foreach ($key in $Counts.Keys) {
        $word = if ($AppName -eq 'PPT' -and $VISUAL_WORD_PPT.ContainsKey($key)) { $VISUAL_WORD_PPT[$key] } else { $VISUAL_WORD[$key] }
        if (-not $word) { $word = $key }
        $words[$word] = $Counts[$key]
    }
    return ' · 글 밖 ' + (($words.Keys | Sort-Object | ForEach-Object { "$_ $($words[$_])" }) -join ' · ')
}

# 목차를 한 줄로 — 엑셀 · 파워포인트만 낸다. 다 못 읽은 시트가 있으면 그 수를 함께 대어, 부르는 쪽이 이 줄만 보고도 고를 일이 있음을 안다
function Format-Outline($Read) {
    if ($Read.ContainsKey('Sheets')) {
        $cut = if ($Read.Partial) { " · 다 못 읽은 시트 $($Read.Partial) — 글 맨 위 목차를 보고 -Sheets 로 고른다" } else { '' }
        return " · 목차 시트 $($Read.Sheets)$cut"
    }
    if ($Read.ContainsKey('Slides')) { return " · 목차 장 $($Read.Slides)" }
    if ($Read.ContainsKey('Pages')) {
        if ($Read.Empty) { return " · 목차 쪽 $($Read.Pages) · $EMPTY_WORD" }
        return " · 목차 쪽 $($Read.Pages)"
    }
    return ''
}

# 바이트는 있는데 글이 빈 문서에 붙이는 말 — 스캔본인지는 쪽마다 떠야 알 수 있어 다 뜨지 않고 사람에게 묻는다
$EMPTY_WORD = '글이 비었다 — 스캔본이냐고 사람에게 묻고, 그렇다면 볼 쪽을 받아 그 쪽만 capture_pages.ps1 -Pages 로 뜬다'

# 끝 셈을 낸다 — 읽음 · 남긴 글자 · 실패 · 전체 한 줄과 글자가 놓인 자리. $KeptHint 는 남긴 자리 줄의 꼬리말이고, 비면 그 줄을 안 낸다
function Write-Tally([string]$KeptHint) {
    Write-Output ''
    if ($NoKeep) {
        Write-Output "읽음 $done · 실패 $failed · 전체 $allCount"
    } else {
        Write-Output "읽음 $done · 남긴 글자 $keptCount · 실패 $failed · 전체 $allCount"
        if ($KeptHint) { Write-Output "남긴 글자는 여기 — $KeepDir (머리 두 줄 뒤 --- 아래가 글자다 · $KeptHint)" }
    }
    if ($OutDir) { Write-Output "글자는 여기 — $OutDir" }
}

# ── 대상 모으기 ────────────────────────────────────────────────────────────
# -File 로 부르면 「-Path a,b」 가 배열이 아니라 글 하나("a,b")로 온다 — 그 글이 그대로 있는 경로가 아니면 쉼표로 가른다(이름에 쉼표가
# 든 파일 · 폴더는 그대로 둔다)
$Path = @(foreach ($item in $Path) {
    if ($item.Contains(',') -and -not (Test-Path -LiteralPath $item)) {
        $item -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
    } else { $item }
})
$done = 0
$failed = 0                            # 못 읽은 것 — 없는 경로 · 받는 확장자가 아닌 파일 · 앱이 못 연 파일
$targets = [System.Collections.Generic.List[string]]::new()
foreach ($item in $Path) {
    if (Test-Path -LiteralPath $item -PathType Container) {
        Get-ChildItem -LiteralPath $item -File | Where-Object {
            $HANDLER.ContainsKey($_.Extension.ToLower())
        } | ForEach-Object { $targets.Add($_.FullName) }
    } elseif (Test-Path -LiteralPath $item) {
        $targets.Add((Resolve-Path -LiteralPath $item).Path)
    } else {
        # 없는 경로도 못 읽은 것이다 — 경고만 하고 넘기면 나머지를 읽은 판이 종료 0 으로 끝나 다 읽은 것으로 보인다
        Write-Output "[없는 경로] $item — 실패: 그 경로에 파일이 없다"
        $failed++
    }
}
if ($targets.Count -eq 0) { Write-Error '읽을 파일이 없다.'; exit 1 }
$allCount = $targets.Count + $failed   # 없는 경로도 준 것으로 센다

# ── 문서함 받은 파일 — 등급 문을 지난 길(-EcmGated)이 아니면 앱을 띄우기 전에 이름을 대며 실패로 센다 ─────────────────────
if (-not $EcmGated) {
    $ecmRoot = Get-EcmDocsRoot
    $open = [System.Collections.Generic.List[string]]::new()
    foreach ($file in $targets) {
        if (Test-EcmAgentFile -LiteralPath $file -Root $ecmRoot) {
            Write-Output "[문서함 받은 파일] $([System.IO.Path]::GetFileName($file)) — 실패: $ECM_REFUSAL"
            $failed++
            continue
        }
        $open.Add($file)
    }
    $targets = $open
}

# ── 못 읽는 꼴 — 읽는 부품의 표($HANDLER)에 없는 확장자는 앱을 띄우기 전에 이름을 대며 실패로 센다 ────────────────
# 건너뛰기만 하면 「읽음 0 · 실패 0」에 종료 0 이라 부른 쪽이 읽은 줄 안다. 실패 줄은 앱이 못 연 파일과 같은 꼴이다 — 부르는 손이 집는다
$readable = [System.Collections.Generic.List[string]]::new()
foreach ($file in $targets) {
    $suffix = [System.IO.Path]::GetExtension($file).ToLower()
    if ($HANDLER.ContainsKey($suffix)) { $readable.Add($file); continue }
    $suffixWord = if ($suffix) { $suffix } else { '확장자 없음' }
    Write-Output "[못 읽는 꼴] $([System.IO.Path]::GetFileName($file)) — 실패: 읽는 손이 받는 확장자가 아니다($suffixWord) · 받는 것: $(($HANDLER.Keys | Sort-Object) -join ' ')"
    $failed++
}
$targets = $readable                   # 아래는 읽는 부품이 받는 것만 본다

if ($OutDir -and -not (Test-Path -LiteralPath $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

# ── 남긴 글자 — 같은 바이트의 파일은 앱을 안 띄우고 남긴 글자로 답한다(자리 · 꼴 · 지문은 읽는 부품의 Find-KeptText · Save-KeptText) ──
$KeepDir = Get-KeptTextDir
$TEXT_EXT = $KEPT_TEXT_EXT             # -OutDir 의 글자 파일도 남긴 것과 같은 꼴 — Fasoo 가 감싸지 않는 꼴이어야 한다
$keptPrint = @{}                       # 읽을 파일 → 지문. 지문을 못 낸 파일(다른 프로세스가 쥔 파일)은 안 들고, 읽기만 한다
$keptCount = 0
if ($Picked) { $NoKeep = $true }
if (-not $NoKeep) {
    # 남길 자리를 못 지으면 남기지 않고 읽기만 한다 — 이 스크립트는 Stop 으로 돌아, 여기서 지면 읽기까지 죽는다
    try {
        if (-not (Test-Path -LiteralPath $KeepDir)) { New-Item -ItemType Directory -Path $KeepDir -Force | Out-Null }
    } catch {
        Write-Output "남길 자리를 못 지었다 — 남기지 않고 읽기만 한다: $($_.Exception.Message)"
        $NoKeep = $true
    }
}
if (-not $NoKeep) {
    $toRead = [System.Collections.Generic.List[string]]::new()
    foreach ($file in $targets) {
        $name = [System.IO.Path]::GetFileName($file)
        try {
            $keptPrint[$file] = Get-KeptPrint -LiteralPath $file
        } catch {
            $toRead.Add($file)
            continue
        }
        $kept = Find-KeptText -Print $keptPrint[$file] -Name $file
        if (-not $kept) { $toRead.Add($file); continue }      # 없거나 · 못 읽거나 · 머리가 없으면(이 손이 남긴 것이 아니다) 새로 읽어 남긴다
        $text = $kept.Text
        Write-Output "[남긴 글자] $name — 같은 파일을 앞서 읽어 앱을 안 띄웠다 · $($kept.Path)"
        Write-Output "    읽을 때의 한 줄: $($kept.Line)"
        if ($OutDir) {
            $text | Out-File -LiteralPath (Join-Path $OutDir "$name$TEXT_EXT") -Encoding utf8
        } elseif ($Preview -gt 0 -and $text.Length -gt 0) {
            $cut = $text.Substring(0, [Math]::Min($Preview, $text.Length)) -replace '\s+', ' '
            Write-Output "    $cut"
        }
        $keptCount++
    }
    $targets = $toRead                 # 아래는 앱으로 읽을 것만 본다 — 끝 정리도 이 판이 연 파일만 건드린다
}
if ($targets.Count -eq 0) {
    # 남긴 글자로 답한 것이 없으면 -NoKeep 안내를 안 낸다 — 받는 확장자가 아닌 파일은 -NoKeep 으로 다시 불러도 같다
    Write-Tally $(if ($keptCount -gt 0) { '앱으로 다시 읽으려면 -NoKeep' })
    if ($failed -gt 0) { exit 1 }
    exit 0
}

# ── 앱별로 묶어 돈다 — 앱 생성이 비싸므로 확장자별로 모아 한 번만 띄운다 ──────
$byApp = $targets | Group-Object { $HANDLER[[System.IO.Path]::GetExtension($_).ToLower()] }
$apps = @{}
$spawnedPids = @{}                     # 이 판이 띄운 PID → 앱 이름
$officeJob = New-OfficeJob

try {
    foreach ($group in $byApp) {
        $appName = $group.Name

        if (-not $apps.ContainsKey($appName)) {
            try {
                $apps[$appName] = New-OfficeApp -AppName $appName -SpawnedPids ([ref]$spawnedPids) -Job $officeJob
            } catch {
                Write-Warning "$appName 를 못 띄웠다: $($_.Exception.Message)"
                $failed += $group.Count
                continue
            }
        }
        $app = $apps[$appName]

        foreach ($file in $group.Group) {
            $name = [System.IO.Path]::GetFileName($file)
            $head = Get-FileHead -LiteralPath $file
            $wrapped = -not (Test-PlainFormat -LiteralPath $file)
            $mark = if ($wrapped) { 'DRM' } else { '평문' }

            try {
                if ($SheetList.Count -and $appName -ne 'Excel') { throw "-Sheets 는 엑셀만 받는다 — 이 파일은 $appName 다" }
                if ($SlideList.Count -and $appName -ne 'PPT') { throw "-Slides 는 파워포인트만 받는다 — 이 파일은 $appName 다" }
                if ($PageList.Count -and $appName -ne 'Word') { throw "-Pages 는 워드 · PDF 만 받는다 — 이 파일은 $appName 다" }
                $read = switch ($appName) {
                    'Word'  { Read-WithWord  -App $app -LiteralPath $file -Pages $PageList }
                    'Excel' { Read-WithExcel -App $app -LiteralPath $file -Sheets $SheetList -MaxCells $MaxCells }
                    'PPT'   { Read-WithPPT   -App $app -LiteralPath $file -Slides $SlideList }
                }
                $text = [string]$read.Text
                $len = $text.Length
                $bytes = (Get-Item -LiteralPath $file).Length
                $kb = if ($bytes -lt 1KB) { '<1' } else { [Math]::Round($bytes / 1KB) }
                $line = "[$mark] $name — $appName · $kb KB · 글자 $len$(Format-Visual -Counts $read.Visual -AppName $appName)$(Format-Outline $read) · 머리 [$head]"
                Write-Output $line

                if ($keptPrint.ContainsKey($file)) {
                    # 남기기가 져도 읽기는 선다 — 글자는 이미 뽑혔고, 못 남긴 것은 다음에 한 번 더 읽힐 뿐이다
                    try {
                        $saved = Save-KeptText -Name $name -Print $keptPrint[$file] -Line $line -Source $file -Text $text
                        Write-Output "    남겼다 — $saved"
                    } catch {
                        Write-Output "    못 남겼다 — $($_.Exception.Message)"
                    }
                }

                if ($OutDir) {
                    $dest = Join-Path $OutDir "$name$TEXT_EXT"
                    $text | Out-File -LiteralPath $dest -Encoding utf8
                } elseif ($Preview -gt 0 -and $len -gt 0) {
                    $cut = $text.Substring(0, [Math]::Min($Preview, $len)) -replace '\s+', ' '
                    Write-Output "    $cut"
                }
                $done++
            } catch {
                # 실패를 삼키지 않는다 — 어느 파일이 왜 안 됐는지가 다음 판단의 근거다.
                Write-Output "[$mark] $name — 실패($appName): $($_.Exception.Message)"
                $failed++
            }
        }
    }
} finally {
    # ⚠ 여기를 건너뛰면 보이지 않는 오피스 프로세스가 쌓여 다음 실행이 느려지거나 멈춘다(끄는 판정은 Close-OfficeApps 가 든다)
    Close-OfficeApps -AppByName $apps -SpawnedPids $spawnedPids -Job $officeJob -PptWasRunning $PptWasRunning

    # 이 판이 연 파일의 복구 항목만 걷는다 — 사람의 복구 자료는 둔다(office-session.ps1 의 Clear-OwnedRecovery)
    Clear-OwnedRecovery -Paths $targets

    # 오피스가 죽으며 못 지운 잠금 파일(~$이름)을 걷는다 — 남으면 다음에 그 파일을 열 때 「다른 사람이 쓰는 중」으로 열린다
    foreach ($target in $targets) {
        $parentDir = Split-Path -Path $target -Parent
        $fileName = Split-Path -Path $target -Leaf
        $lockFile = Join-Path $parentDir ("~$" + $fileName)
        if (Test-Path -LiteralPath $lockFile) {
            Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Tally '같은 파일을 다시 읽으면 앱을 안 띄우고 이 글자로 답한다'
if ($failed -gt 0) { exit 1 }
