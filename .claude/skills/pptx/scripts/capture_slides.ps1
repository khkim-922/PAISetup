<#
.SYNOPSIS
    DRM 환경에서 슬라이드를 화면 캡처로 취득한다 — 육안 QA 용.

.DESCRIPTION
    파일 보안(DRM) 필터 드라이버는 PowerPoint 가 **디스크에 쓰는** 산출물을 가로챈다.
    `Slide.Export()` · PDF 변환 · LibreOffice 경로가 모두 이 자리에서 막히거나 암호화된다.

    빠져나가는 길은 디스크를 거치지 않는 것이다 — 슬라이드쇼로 화면에 띄우고
    `Graphics.CopyFromScreen()` 으로 **화면 버퍼를 직접 읽는다.** DRM 은 화면에 그려진
    것을 막지 않으므로 그대로 이미지가 나온다.

    두 자리가 잘 걸린다 — 둘 다 이 스크립트가 든다.
      * 전경 잠금 : 다른 창이 활성이면 AppActivate 가 무시되어 엉뚱한 창이 찍힌다.
        Alt 를 한 번 보내 잠금을 풀고 두 번 부른다.
      * 남는 프로세스 : 캡처 뒤 PowerPoint 가 살아 있으면 덱 파일을 잠가 다음 빌드가
        PermissionError 로 죽는다. 이 스크립트가 띄운 것만 골라 끝낸다.

.PARAMETER Path
    캡처할 .pptx 경로.

.PARAMETER Slides
    캡처할 슬라이드 번호. 쉼표로 여럿 준다 (예: "3,8"). 생략하면 1번만.

.PARAMETER OutDir
    이미지를 둘 폴더. 기본값은 현재 폴더.

.PARAMETER MaxWidth
    압축 후 가로 픽셀. 기본 1280 — 글자 판독은 되고 토큰은 아끼는 자리.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File capture_slides.ps1 -Path out.pptx -Slides "3,8"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Slides = "1",
    [string]$OutDir = ".",
    [int]$MaxWidth = 1280,
    [int]$Quality = 85,
    [int]$Wait = 1000
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Fg {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern int GetWindowThreadProcessId(IntPtr h, out int pid);
  public static int Pid() {
    int pid; GetWindowThreadProcessId(GetForegroundWindow(), out pid); return pid;
  }
}
"@

# 앞서 죽은 PowerPoint 가 남긴 복구 항목 중 이 덱에 해당하는 것만 골라 지운다 (사용자 복구 자료 보존)
$leaf = Split-Path -Path $Path -Leaf
$officeVerKeys = @(Get-ChildItem -Path "HKCU:\Software\Microsoft\Office" -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^\d+\.\d+$' })
foreach ($ver in $officeVerKeys) {
    $recPath = "HKCU:\Software\Microsoft\Office\$($ver.PSChildName)\PowerPoint\Resiliency\DocumentRecovery"
    if (Test-Path -LiteralPath $recPath) {
        try {
            $item = Get-Item -LiteralPath $recPath -ErrorAction SilentlyContinue
            if ($item) {
                foreach ($valName in $item.GetValueNames()) {
                    if ($valName -like "*$leaf*") {
                        Remove-ItemProperty -LiteralPath $recPath -Name $valName -Force -ErrorAction SilentlyContinue
                    }
                }
            }
        } catch { }
    }
}

$full = (Resolve-Path -LiteralPath $Path).Path
$outRoot = (Resolve-Path -LiteralPath $OutDir).Path
$slideList = @($Slides -split '[,\s]+' | Where-Object { $_ -match '^\d+$' } | ForEach-Object { [int]$_ })
if ($slideList.Count -eq 0) { throw "Slides 에 슬라이드 번호가 없다" }

$before = @(Get-Process POWERPNT -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })

# 창 없이 떠 있는 PowerPoint 는 앞선 자동화가 남긴 껍데기다 — 두면 슬라이드쇼가 서지 않는다.
# 사람이 띄워 쓰는 것(제목이 있다)은 건드리지 않는다.
foreach ($p in (Get-Process POWERPNT -ErrorAction SilentlyContinue)) {
    if ([string]::IsNullOrWhiteSpace($p.MainWindowTitle)) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        $before = @($before | Where-Object { $_ -ne $p.Id })
    }
}
if ($before.Count -ne (Get-Process POWERPNT -ErrorAction SilentlyContinue | Measure-Object).Count) {
    Start-Sleep -Seconds 2
}

$ws = $null
$ppt = $null
$pres = $null
$show = $null
$made = @()

try {
    $ws = New-Object -ComObject WScript.Shell
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open($full, $true, $false, $true)
    try { $pres.Saved = $true } catch { }
    $pres.SlideShowSettings.Run() | Out-Null

    # 슬라이드쇼 창이 설 때까지 기다린다 — 바로 물으면 null 이 온다
    for ($i = 0; $i -lt 25 -and $null -eq $show; $i++) {
        Start-Sleep -Milliseconds 300
        try { $show = $pres.SlideShowWindow } catch { $show = $null }
    }
    if ($null -eq $show) { throw "슬라이드쇼 창이 뜨지 않았다 — 보호된 보기로 열렸는지 본다" }

    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds

    foreach ($n in $slideList) {
        $show.View.GotoSlide($n)
        $proc = Get-Process POWERPNT | Sort-Object StartTime -Descending | Select-Object -First 1

        # 전경으로 올라왔는지 **확인하고** 찍는다 — 안 올라오면 다른 창이 찍히는데 파일은 멀쩡히 생긴다
        $front = $false
        for ($try = 0; $try -lt 6 -and -not $front; $try++) {
            $ws.SendKeys('%')                   # Alt 한 번 = 전경 잠금 해제
            Start-Sleep -Milliseconds 250
            $ws.AppActivate($proc.Id) | Out-Null
            Start-Sleep -Milliseconds 350
            $ws.AppActivate($proc.Id) | Out-Null
            Start-Sleep -Milliseconds 350
            $front = ([Fg]::Pid() -eq $proc.Id)
        }
        if (-not $front) { throw "PowerPoint 가 전경으로 오지 않았다 — 다른 창이 찍힐 자리라 멈춘다" }

        Start-Sleep -Milliseconds $Wait          # 첫 프레임이 그려질 때까지

        $png = Join-Path $outRoot ("slide-{0}.png" -f $n)
        $bmp = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
        $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
        $g.Dispose()
        $bmp.Dispose()
        $made += $png
    }
} finally {
    if ($null -ne $show) { try { $show.View.Exit() } catch { } }
    if ($null -ne $pres) {
        try { $pres.Saved = $true } catch { }
        try { $pres.Close() } catch { }
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres) | Out-Null } catch { }
    }
    if ($null -ne $ppt) {
        try { $ppt.Quit() } catch { }
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null } catch { }
    }
    Start-Sleep -Milliseconds 800

    # 이 스크립트가 띄운 것만 끝낸다 — 남으면 다음 빌드가 파일 잠금으로 죽는다
    foreach ($p in (Get-Process POWERPNT -ErrorAction SilentlyContinue)) {
        if ($before -notcontains $p.Id) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    }
}

# 압축은 capture_slide.py 가 든다 — 원본 PNG 는 비전 토큰을 과하게 먹는다 (Pillow 로 70% 압축)
$compressor = Join-Path $PSScriptRoot 'capture_slide.py'
foreach ($png in $made) {
    if (Test-Path -LiteralPath $compressor) {
        $jpg = [System.IO.Path]::ChangeExtension($png, '.jpg')
        python $compressor -i $png -o $jpg --max-w $MaxWidth --quality $Quality | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $jpg)) {
            Remove-Item -LiteralPath $png -Force
            Write-Output $jpg
        } else {
            Write-Output $png
        }
    } else {
        Write-Output $png
    }
}
