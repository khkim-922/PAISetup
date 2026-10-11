<#
.SYNOPSIS
    PowerPoint 가 직접 잰 글 높이로 덱의 넘침·겹침·여백을 검사한다.

.DESCRIPTION
    덱의 배치를 PowerPoint 가 직접 잰 값으로 검사한다 — 고치는 동안 돌리는 쪽이다.
    눈으로 보는 QA 는 `capture_slides.ps1`(슬라이드쇼 화면 캡처)가 들고, 이 둘은
    잡는 결함이 다르다: 이쪽은 넘침·겹침·여백을, 저쪽은 색 대비와 활자 인상을 잡는다.

    검사 셋.
      넘침  : 글이 제 상자보다 높은가 (PowerPoint 의 자동맞춤 높이로 실측)
      겹침  : 같은 슬라이드의 두 글 덩어리가 실제로 포개지는가
      여백  : 글이 슬라이드 가장자리 0.5" 안으로 들어왔는가

    배경 장식(테두리로 흘러나가는 원 따위)은 도형이라 여백 검사에서 걸리지 않는다.

.PARAMETER Path
    검사할 .pptx 경로.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File audit_layout.ps1 -Path out.pptx
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path
)

$ErrorActionPreference = 'Stop'
$full = (Resolve-Path -LiteralPath $Path).Path
$leaf = Split-Path -Path $Path -Leaf

$before = @(Get-Process POWERPNT -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
$pp = $null
$pres = $null
$slideW = 0
$slideH = 0
$blocks = @()
$issues = 0

try {
    $pp = New-Object -ComObject PowerPoint.Application
    # ReadOnly=$true 로 열어 쓰기 잠금 방지
    $pres = $pp.Presentations.Open($full, $true, $false, $false)
    try { $pres.Saved = $true } catch { }

    $slideW = $pres.PageSetup.SlideWidth / 72
    $slideH = $pres.PageSetup.SlideHeight / 72

    foreach ($s in $pres.Slides) {
        foreach ($sh in $s.Shapes) {
            if ($sh.HasTextFrame -ne -1) { continue }
            if ($sh.TextFrame.HasText -ne -1) { continue }

            $h = $sh.Height
            $sh.TextFrame2.AutoSize = 1      # msoAutoSizeShapeToFitText — 필요한 높이를 잰다
            $need = $sh.Height
            $sh.TextFrame2.AutoSize = 0
            $sh.Height = $h                  # 잰 뒤 원래대로 되돌린다 (저장하지 않는다)

            $text = $sh.TextFrame.TextRange.Text -replace "`r", ' / '
            if ($text.Length -gt 30) { $text = $text.Substring(0, 30) }

            $blocks += [pscustomobject]@{
                Slide = $s.SlideIndex
                L = $sh.Left / 72; T = $sh.Top / 72
                W = $sh.Width / 72; H = $h / 72
                Need = $need / 72
                Text = $text
            }
        }
    }
} finally {
    if ($null -ne $pres) {
        try { $pres.Saved = $true } catch { }
        try { $pres.Close() } catch { }
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres) | Out-Null } catch { }
    }
    if ($null -ne $pp) {
        try { $pp.Quit() } catch { }
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null } catch { }
    }
    Start-Sleep -Milliseconds 500

    # 이 스크립트가 띄운 것만 강제 종료
    foreach ($p in (Get-Process POWERPNT -ErrorAction SilentlyContinue)) {
        if ($before -notcontains $p.Id) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    }

    # 복구 항목 중 이 덱에 매칭되는 것만 선별 삭제
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
}

foreach ($b in $blocks) {
    if (($b.Need - $b.H) -gt 0.03) {
        Write-Output ('S{0} 넘침    필요 {1:N2}in / 자리 {2:N2}in | {3}' -f $b.Slide, $b.Need, $b.H, $b.Text)
        $issues++
    }
    $bottom = $b.T + $b.Need
    $right = $b.L + $b.W
    if ($b.L -lt 0.5 -or $b.T -lt 0.4 -or $right -gt ($slideW - 0.5) -or $bottom -gt ($slideH - 0.5)) {
        Write-Output ('S{0} 여백    L{1:N2} R{2:N2} T{3:N2} B{4:N2} | {5}' -f $b.Slide, $b.L, $right, $b.T, $bottom, $b.Text)
        $issues++
    }
}

foreach ($g in $blocks | Group-Object Slide) {
    $arr = @($g.Group)
    for ($i = 0; $i -lt $arr.Count; $i++) {
        for ($j = $i + 1; $j -lt $arr.Count; $j++) {
            $a = $arr[$i]; $b = $arr[$j]
            $ox = [Math]::Min($a.L + $a.W, $b.L + $b.W) - [Math]::Max($a.L, $b.L)
            $oy = [Math]::Min($a.T + $a.Need, $b.T + $b.Need) - [Math]::Max($a.T, $b.T)
            if ($ox -gt 0.05 -and $oy -gt 0.03) {
                Write-Output ('S{0} 겹침    {1:N2}in x {2:N2}in | {3} <-> {4}' -f $g.Name, $ox, $oy, $a.Text, $b.Text)
                $issues++
            }
        }
    }
}

if ($issues -eq 0) {
    Write-Output '이상 없음 — 넘침 0 · 겹침 0 · 여백 위반 0'
} else {
    Write-Output ('검출 {0}건 — 글을 줄이거나 항목 수를 낮출 것' -f $issues)
}
exit ([int]($issues -gt 0))
