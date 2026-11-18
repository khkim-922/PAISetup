<#
.SYNOPSIS
    DRM 환경에서 슬라이드를 화면 캡처로 취득한다 — 육안 QA 용.

.DESCRIPTION
    슬라이드쇼로 화면에 띄우고 `Graphics.CopyFromScreen()` 으로 화면 버퍼를 읽어 지면만 집고, 줄인 WebP 로 낸다(못 줄이면 PNG).
    DRM 필터가 디스크에 쓰는 산출물(`Slide.Export()` · PDF 변환)을 가로채서 디스크를 안 거친다. 찍는 동안 화면을 가져간다.
    내는 것 — 장 차례대로 그림 경로 한 줄씩. 걸리기 쉬운 자리(전경 잠금 · 화면 배율 · 띠 · 발표자 보기)는 references/DESIGN.md.

.PARAMETER Path
    캡처할 .pptx 경로.

.PARAMETER Slides
    캡처할 슬라이드 번호. 쉼표나 공백으로 여럿 준다 (예: "3,8"). 생략하면 1번만.
    번호가 아닌 낱말(범위 "3-5" 따위)이 있으면 그 낱말을 대며 멈춘다 — 읽는 부품의 ConvertTo-NumberList 가 푼다.

.PARAMETER OutDir
    이미지를 더 둘 폴더. 찍은 장은 남긴 자리(아래 「남긴 그림」)에 남고, 이 값을 주면 그 폴더에도
    `slide-<장>` 으로 한 벌 놓아 그 경로를 낸다. `-NoKeep` 일 때는 여기에만 찍고, 생략하면 임시 폴더
    아래 `drm-slides\<덱 이름>-<시각>\` 을 짓는다 — 현재 폴더로 떨구면 그 폴더가 저장소이거나
    표본 폴더일 때 산출물이 섞인다.

.PARAMETER NoKeep
    찍은 그림을 남기지도, 남긴 그림을 쓰지도 않는다. 짓는 중인 덱의 검수처럼 저장할 때마다
    바이트가 달라지는 덱은 판마다 한 벌씩 쌓이므로 이 값으로 찍는다. 같은 덱에서 앞서 남긴 그 장은
    걷으니, 잘못 찍혀 남은 그림(빈 첫 화면 · 엉뚱한 창)은 이 값 한 판으로 물린다.

.PARAMETER MaxEdge
    줄인 뒤 긴 변 픽셀. 안 주면 줄이는 손의 기본 눈금을 따른다 — 눈금의 값은 그 손이 든다(읽는 부품의 Convert-ShotsToWebp).
    비전 토큰은 치수가 정한다(`⌈가로/28⌉ × ⌈세로/28⌉`) — 작은 글자를 더 크게 봐야 할 때만 올린다.
    준 값은 남긴 그림의 이름에 붙어(`.e<긴 변>`), 눈금이 다른 판의 그림과 안 섞인다.

.PARAMETER EcmGated
    문서함(ECM) 에이전트가 받은 파일도 찍는다. 이 값 없이 그 폴더의 덱을 주면 파워포인트를 띄우기 전에 멈춘다 — 이 스킬은 문서의
    보안등급을 모른다. 스킬 company-ecm 의 손이 등급 문을 지난 답에서 이를 때만 준다(읽는 부품 office-read.ps1 「문서함」).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File capture_slides.ps1 -Path out.pptx -Slides "3,8"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Slides = "1",
    [string]$OutDir,
    [int]$MaxEdge = 0,         # 0 = 줄이는 손의 기본 눈금
    [int]$Wait = 4000,         # 첫 프레임이 늦게 그려지는 PC 에서도 빈 화면이 안 찍히게 넉넉히 기다린다
    # 찍은 그림을 남기지도, 남긴 그림을 쓰지도 않는다 — -OutDir(없으면 임시 폴더)에만 찍는다
    [switch]$NoKeep,
    [switch]$EcmGated          # 문서함 에이전트가 받은 파일도 찍는다 — 위 .PARAMETER EcmGated
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'office-session.ps1')
. (Join-Path $PSScriptRoot 'office-read.ps1')      # 띄우기 · 끝내기 · 남긴 자리와 지문 · 그림 줄이기
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Fg {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern int GetWindowThreadProcessId(IntPtr h, out int pid);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  public static int Pid() {
    int pid; GetWindowThreadProcessId(GetForegroundWindow(), out pid); return pid;
  }
}
"@
# ⚠ 화면 배율이 100 % 가 아니면 DPI 를 모르는 프로세스의 Screen.Bounds 는 논리 치수(2560 → 2048)인데 CopyFromScreen 은
# 실제 픽셀을 집어, 지면의 왼쪽 위만 찍힌다. 치수를 읽기 전에 실제 픽셀로 맞춘다
[void][Fg]::SetProcessDPIAware()

$full = (Resolve-Path -LiteralPath $Path).Path
if (-not $EcmGated -and (Test-EcmAgentFile -LiteralPath $full -Root (Get-EcmDocsRoot))) {
    throw "$([IO.Path]::GetFileName($full)) — $ECM_REFUSAL"   # 앱을 띄우기 전이다 — 등급을 모르는 문서함 받은 파일은 안 연다(office-read.ps1 「문서함」)
}
$slideList = @(ConvertTo-NumberList -Value $Slides -Name 'Slides')    # 번호가 아닌 낱말이면 그 낱말을 대며 던진다 — 앱을 띄우기 전이다
if ($slideList.Count -eq 0) { throw "Slides 에 슬라이드 번호가 없다" }

# ── 남긴 그림 — 같은 바이트의 덱에서 앞서 찍은 장은 다시 안 찍는다 ────────────────────────────
# 남긴 글자 곁의 폴더(Get-KeptShotDir)에 「slide-<장>.webp」(-MaxEdge 를 준 판은 「slide-<장>.e<긴 변>.webp」)가 있는 장은 안 찍는다.
# PNG 로 남은 장(줄이기가 졌다)은 남긴 것으로 치지 않는다 — 다시 찍어 줄이기를 한 번 더 해 본다
$keepDir = $null
if (-not $NoKeep) {
    try {
        $keepDir = Get-KeptShotDir -Name ([IO.Path]::GetFileName($full)) -Print (Get-KeptPrint -LiteralPath $full)
        [void](New-Item -ItemType Directory -Path $keepDir -Force)
    } catch {
        Write-Warning "남길 자리를 못 지었다($($_.Exception.Message)) — 이번에는 남기지 않고 찍는다"
        $keepDir = $null
    }
} else {
    # 다시 찍는 판 — 앞서 남긴 그 장을 걷는다. 안 걷으면 잘못 찍혀 남은 그림이 다음 부름에 다시 답으로 나온다
    try {
        $staleDir = Get-KeptShotDir -Name ([IO.Path]::GetFileName($full)) -Print (Get-KeptPrint -LiteralPath $full)
        if (Test-Path -LiteralPath $staleDir -PathType Container) {
            foreach ($n in $slideList) {
                # 그 장으로 남긴 것 전부 — 긴 변을 안 준 판(slide-<장>.webp)과 준 판(slide-<장>.e<긴 변>.webp). 다른 장 · 그림만 뜬 것은 안 걸린다
                $keptName = '^slide-{0}(\.e\d+)?\.webp$' -f $n
                Get-ChildItem -LiteralPath $staleDir -File | Where-Object { $_.Name -match $keptName } | Remove-Item -Force
            }
        }
    } catch {
        Write-Warning "앞서 남긴 그림을 못 걷었다($($_.Exception.Message)) — 다음 부름이 그 그림으로 답할 수 있다"
    }
}
# 그림의 이름 — 남기는 판에서 긴 변을 줬을 때만 그 값을 단다. 안 준 판은 줄이는 손의 기본 눈금이라 달 값이 없다
$edgeTag = if ($keepDir -and $MaxEdge -gt 0) { ".e$MaxEdge" } else { '' }
$stem = { param($n) "slide-{0}{1}" -f $n, $edgeTag }
$result = @{}                          # 장 번호 → 낼 그림
if ($keepDir) {
    foreach ($n in $slideList) {
        $keptShot = Join-Path $keepDir ((& $stem $n) + '.webp')
        if (Test-Path -LiteralPath $keptShot) { $result[$n] = $keptShot }
    }
}
$keptCount = $result.Count
$toShoot = @($slideList | Where-Object { -not $result.ContainsKey($_) } | Select-Object -Unique)

# 낼 그림을 장 차례대로 낸다 — 남긴 자리에서 찍었고 -OutDir 를 받았으면 그 폴더로 베껴 그 경로를 낸다
function Write-Shots {
    if ($keptCount -gt 0) {
        Write-Host ("  남긴 그림 {0}장 — 같은 덱에서 앞서 찍어 다시 안 찍었다 · {1} (다시 찍으려면 -NoKeep)" -f $keptCount, $keepDir)
    }
    $copyTo = $null
    if ($keepDir -and $OutDir) { $copyTo = (New-Item -ItemType Directory -Path $OutDir -Force).FullName }
    foreach ($n in $slideList) {
        $shot = $result[$n]
        if (-not $shot) { continue }
        if ($copyTo) {
            $copy = Join-Path $copyTo ("slide-{0}{1}" -f $n, [IO.Path]::GetExtension($shot))
            Copy-Item -LiteralPath $shot -Destination $copy -Force
            $shot = $copy
        }
        Write-Output $shot
    }
}
if ($toShoot.Count -eq 0) { Write-Shots; return }

# 앞서 죽은 PowerPoint 가 남긴 복구 항목 중 이 덱의 것만 지운다 — 남아 있으면 복구 창이 먼저 떠 슬라이드쇼가 서지 않는다
Clear-OwnedRecovery -Paths @($full)

if ($keepDir) {
    $outRoot = $keepDir
} else {
    if (-not $OutDir) {
        $OutDir = Join-Path ([IO.Path]::GetTempPath()) ("drm-slides\{0}-{1}" -f [IO.Path]::GetFileNameWithoutExtension($full), (Get-Date -Format 'yyyyMMdd-HHmmss'))
    }
    $outRoot = (New-Item -ItemType Directory -Path $OutDir -Force).FullName
}

$ws = $null
$ppt = $null
$session = $null
$pres = $null
$show = $null
$made = @()
# 파워포인트는 하나만 뜬다 — 붙은 자리가 사람이 쓰던 앱인지 New-OfficeApp 이 여기 적어, 끝에서 그 앱을 안 끈다
$PptWasRunning = $false
$spawnedPids = @{}                     # 이 판이 띄운 PID → 앱 이름
$officeJob = New-OfficeJob

try {
    $ws = New-Object -ComObject WScript.Shell
    $ppt = New-OfficeApp -AppName 'PPT' -SpawnedPids ([ref]$spawnedPids) -Job $officeJob
    # 경로 · ReadOnly=$true · Untitled=$false · WithWindow=$true — 사람이 연 덱이면 그 발표로 쇼만 띄우고 안 닫는다
    $session = Open-OwnedDocument -Kind 'PPT' -Collection $ppt.Presentations -Open { $ppt.Presentations.Open($full, $true, $false, $true) }
    $pres = $session.Document
    # 모니터가 둘이면 파워포인트가 발표자 보기를 띄워 이 창에는 잘린 슬라이드와 다음 장 미리보기가 찍힌다 — 쇼를 띄우기 전에 끈다
    $pres.SlideShowSettings.ShowPresenterView = 0
    $pres.SlideShowSettings.Run() | Out-Null

    # 슬라이드쇼 창이 설 때까지 기다린다 — 바로 물으면 null 이 온다. 지면 원인이 남게 기다린 시간 · 쇼 창 수 · 마지막 오류를 쥔다
    $showWatch = [Diagnostics.Stopwatch]::StartNew()
    $showError = $null
    for ($i = 0; $i -lt 25 -and $null -eq $show; $i++) {
        Start-Sleep -Milliseconds 300
        try { $show = $pres.SlideShowWindow } catch { $show = $null; $showError = $_.Exception.Message }
    }
    if ($null -eq $show) {
        $showCount = try { $ppt.SlideShowWindows.Count } catch { '못 읽음' }
        throw ("슬라이드쇼 창이 뜨지 않았다 — 보호된 보기로 열렸는지 본다 (기다림 {0:N1} 초 · 쇼 창 {1} · 마지막 오류: {2})" -f `
            ($showWatch.ElapsedMilliseconds / 1000.0), $showCount, $(if ($showError) { $showError } else { '없음' }))
    }

    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds

    # ── 지면만 집는다 ───────────────────────────────────────────
    # 지면 치수(`PageSetup`)와 「복판에 비율 맞춰」 규칙으로 집을 자리를 셈한다 — 못 읽으면 화면 통째로 물러나고 그렇다고 말한다.
    # ⚠ 띠를 픽셀 색으로 찾지 않는다 — 어두운 지면과 안 갈려 다크 표지를 잘라먹는다. 읽었나는 결과 치수가 아니라 $pageKnown 이 든다
    $pageKnown = $false
    $clip = [System.Drawing.Rectangle]::new($screen.X, $screen.Y, $screen.Width, $screen.Height)
    try {
        $slideW = [double]$pres.PageSetup.SlideWidth
        $slideH = [double]$pres.PageSetup.SlideHeight
        if ($slideW -gt 0 -and $slideH -gt 0) {
            $k  = [Math]::Min($screen.Width / $slideW, $screen.Height / $slideH)
            $dw = [int][Math]::Round($slideW * $k)
            $dh = [int][Math]::Round($slideH * $k)
            $clip = [System.Drawing.Rectangle]::new(
                ($screen.X + [int][Math]::Round(($screen.Width  - $dw) / 2)),
                ($screen.Y + [int][Math]::Round(($screen.Height - $dh) / 2)),
                $dw, $dh)
            $pageKnown = $true
        }
    } catch { }

    # 무엇을 집었나를 찍어 둔다 — 「지면만 집었나」를 눈으로 되묻지 않게
    if (-not $pageKnown) {
        Write-Warning ("지면 치수를 못 읽어 화면을 통째로 찍는다 ({0}x{1}) — 띠까지 값을 문다" -f $screen.Width, $screen.Height)
    } else {
        $band = 100.0 - (100.0 * $clip.Width * $clip.Height / ($screen.Width * $screen.Height))
        Write-Host ("  지면만 집는다 — {0}x{1} @ {2},{3}   (화면 {4}x{5} · 띠 {6:N0}%)" -f `
            $clip.Width, $clip.Height, $clip.X, $clip.Y, $screen.Width, $screen.Height, $band)
    }

    # 앞에 있는 창이 이 슬라이드쇼 창인가 — 쇼 창의 손잡이로 가린다(프로세스 Id 만 보면 같은 파워포인트의 다른 덱 창도 지나간다).
    # 쇼 창 손잡이가 비어 오는 판에서는 프로세스 Id 로 본다
    $showHandle = [IntPtr]::Zero
    try { $showHandle = [IntPtr][long]$show.HWND } catch { }

    foreach ($n in $toShoot) {
        $show.View.GotoSlide($n)
        # 다른 보안 맥락에서 뜬 POWERPNT 는 StartTime 을 못 읽어 정렬을 통째로 깨뜨린다 — 읽히는 것만 고른다
        $proc = Get-Process POWERPNT | Where-Object { $_.StartTime } |
            Sort-Object StartTime -Descending | Select-Object -First 1
        $showFront = {
            if ($showHandle -ne [IntPtr]::Zero) { [Fg]::GetForegroundWindow() -eq $showHandle } else { [Fg]::Pid() -eq $proc.Id }
        }

        # 전경으로 올라왔는지 **확인하고** 찍는다 — 안 올라오면 다른 창이 찍히는데 파일은 멀쩡히 생긴다
        $front = $false
        for ($try = 0; $try -lt 6 -and -not $front; $try++) {
            $ws.SendKeys('%')                   # Alt 한 번 = 전경 잠금 해제
            Start-Sleep -Milliseconds 250
            $ws.AppActivate($proc.Id) | Out-Null
            Start-Sleep -Milliseconds 350
            $ws.AppActivate($proc.Id) | Out-Null
            try { $show.Activate() } catch { }  # 프로세스 Id 로는 그 프로세스의 다른 덱 창이 올라올 수 있다 — 쇼 창을 짚어 올린다
            Start-Sleep -Milliseconds 350
            $front = (& $showFront)
            if (-not $front) { continue }
            Start-Sleep -Milliseconds $Wait      # 첫 프레임이 그려질 때까지
            $front = (& $showFront)              # 기다린 사이 다른 창이 올라왔으면 다시 올린다
        }
        if (-not $front) { throw "슬라이드쇼 창이 전경으로 오지 않았다 — 다른 창이 찍힐 자리라 멈춘다" }

        $png = Join-Path $outRoot ((& $stem $n) + '.png')
        $bmp = New-Object System.Drawing.Bitmap $clip.Width, $clip.Height
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen($clip.Location, [System.Drawing.Point]::Empty, $clip.Size)
        $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
        $g.Dispose()
        $bmp.Dispose()
        $made += [pscustomobject]@{ N = $n; Png = $png }
    }
} finally {
    if ($null -ne $show) { try { $show.View.Exit() } catch { } }
    Close-OwnedDocument $session
    # 끄고 끝내는 판정은 읽는 부품이 든다 — 찍는 사이 사람이 연 덱이 남았으면 앱을 살려 둔다
    Close-OfficeApps -AppByName @{ PPT = $ppt } -SpawnedPids $spawnedPids -Job $officeJob -PptWasRunning $PptWasRunning
}

# 찍은 장을 한 번에 줄인다(읽는 부품의 Convert-ShotsToWebp) — 못 줄인 장은 PNG 로 나가고 남긴 것으로 안 친다(위 「남긴 그림」)
$converted = Convert-ShotsToWebp -Png @($made | ForEach-Object { $_.Png }) -MaxEdge $MaxEdge
foreach ($shot in $made) { $result[$shot.N] = $converted[$shot.Png] }
Write-Shots
