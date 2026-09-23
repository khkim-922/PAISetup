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

.PARAMETER MaxEdge
    줄인 뒤 긴 변 픽셀. 기본 1280 — 글자 판독은 되고 토큰은 아끼는 자리.
    **비전 토큰은 치수가 정한다**(`⌈가로/28⌉ × ⌈세로/28⌉`) — 이 값만이 값을 줄인다.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File capture_slides.ps1 -Path out.pptx -Slides "3,8"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Slides = "1",
    [string]$OutDir = ".",
    [int]$MaxEdge = 1280,
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

    # ── 지면만 집는다 — **띠도 값이다** ───────────────────────────────────────────
    # 슬라이드쇼는 지면을 화면 복판에 비율 맞춰 놓고 남는 자리를 띠로 채운다. 화면을 통째로
    # 찍으면 그 띠에도 값이 붙는다 — 비전 토큰은 **치수로** 매겨지므로(`⌈가로/28⌉ × ⌈세로/28⌉`)
    # 띠를 옮기느라 값을 쓰고 정작 읽어야 할 글자를 깎는다. 21:9 에서 띠가 41% 다.
    # ⚠ **띠를 픽셀 색으로 찾지 않는다** — 어두운 지면과 안 갈려서 다크 표지를 잘라먹는다.
    #   그건 꼴이 아니라 뜻을 읽는 일이다. **비율로 재면 꼴이다**: 지면 치수는 파일이 들고
    #   (`PageSetup`), 놓이는 규칙은 「복판에 비율 맞춰」라 집을 자리가 곱셈 몇 번으로 나온다.
    # ⚠ **못 읽으면 화면 통째로 물러난다.** 지면을 못 재는 것과 그림을 못 내는 것은 다른
    #   명제다 — 여기서 멈추면 QA 가 통째로 선다. 대신 **물러났다는 사실을 말한다.**
    # ⚠ **「읽었나」를 결과 치수에서 역산하지 않는다.** 화면과 지면의 비율이 같으면(16:9 화면에
    #   16:9 덱) 띠가 없어 집을 자리가 화면과 **참으로 같아진다** — 그 같음을 실패로 읽으면
    #   멀쩡한 판이 매번 경고를 낸다. 상태를 따로 든다: 읽었나는 읽은 자리가 안다.
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

    # 무엇을 집었나는 **기계가 말하게 한다.** 안 찍으면 「지면만 집었나」를 눈으로 되물어야
    # 하고, 그 물음은 다음에도 똑같이 안 걸린다.
    if (-not $pageKnown) {
        Write-Warning ("지면 치수를 못 읽어 화면을 통째로 찍는다 ({0}x{1}) — 띠까지 값을 문다" -f $screen.Width, $screen.Height)
    } else {
        $band = 100.0 - (100.0 * $clip.Width * $clip.Height / ($screen.Width * $screen.Height))
        Write-Host ("  지면만 집는다 — {0}x{1} @ {2},{3}   (화면 {4}x{5} · 띠 {6:N0}%)" -f `
            $clip.Width, $clip.Height, $clip.X, $clip.Y, $screen.Width, $screen.Height, $band)
    }

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
        $bmp = New-Object System.Drawing.Bitmap $clip.Width, $clip.Height
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen($clip.Location, [System.Drawing.Point]::Empty, $clip.Size)
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

# 줄이는 손은 씨앗 부품이 든다 — 이 스킬은 제 사본을 안 든다(진본은 claude-config `seeds/check/`).
# 못 찾으면 원본 PNG 를 그대로 낸다 — 큰 그림이라고 안 내는 것보다 낫다.
$shrink = @(
    (Join-Path $HOME '.claude/seeds/check/_check/_shrink.py'),
    (Join-Path $PSScriptRoot '..\..\..\..\seeds\check\_check\_shrink.py')
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

foreach ($png in $made) {
    if ($shrink) {
        $webp = [System.IO.Path]::ChangeExtension($png, '.webp')
        python -X utf8 $shrink $png $webp --max-edge $MaxEdge | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $webp)) {
            Remove-Item -LiteralPath $png -Force
            Write-Output $webp
        } else {
            # ⚠ **진 갈래도 말한다.** 아래 「못 찾았다」는 경고하는데 여기는 조용했다 — 갈래 둘의
            #   대우가 어긋나면, 줄이기가 진 판이 **큰 그림이 그냥 나온 것**처럼 보인다.
            #   부품이 낸 오류 글은 위에 찍히지만 그것은 파이썬의 말이지 **이 스크립트의 판정이
            #   아니다.** 값을 2~3배 물고 나가는 자리라 그 판정이 한 줄 서야 한다.
            # ⚠ **흔한 까닭을 같이 둔다.** 씨앗이 PIL 을 드는데 그것을 까는 선언이 없어
            #   (claude-config #72), 부르는 쪽이 그 자리에서 깔게 둔 것이 지금의 규율이다.
            Write-Warning "줄이기가 졌다 — 원본 치수 그대로 낸다. 위 오류를 본다 (흔한 까닭은 PIL 이 없는 것: python -m pip install pillow)"
            Write-Output $png
        }
    } else {
        Write-Warning "줄이는 부품을 못 찾았다 — 원본 치수 그대로 낸다 (~/.claude/seeds/check/_check/_shrink.py)"
        Write-Output $png
    }
}
