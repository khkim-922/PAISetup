<#
.SYNOPSIS
    PowerPoint 가 직접 잰 값으로 덱의 넘침·겹침·여백·줄간격·간격을 검사하고 정렬을 보고한다.

.DESCRIPTION
    덱의 배치를 PowerPoint 가 직접 잰 값으로 검사한다 — 고치는 동안 돌리는 쪽이다.
    눈으로 보는 QA 는 `capture_slides.ps1`(슬라이드쇼 화면 캡처)가 들고, 이 둘은
    잡는 결함이 다르다: 이쪽은 자로 잴 수 있는 것을, 저쪽은 색 대비와 활자 인상을 잡는다.

    층 — 만드는 사람의 흐름. 덱을 건네기 전에 손으로 돌리는 확인이고 게이트가 아니다.
    걷는 조건 — 덱을 .pptx 로 내지 않게 되거나, 파워포인트 없는 자리에서만 짓게 되면 걷는다.

    판정 (어긋나면 종료 코드 1)
      넘침    : 글이 제 상자보다 높은가 (PowerPoint 의 자동맞춤 높이로 실측)
      겹침    : 같은 슬라이드의 두 덩어리(글상자 · 표)가 실제로 포개지는가
      여백    : 덩어리가 슬라이드 가장자리 0.5" 안으로 들어왔는가
      줄간격  : 줄이 둘 이상인 글상자 · 표 셀에서 줄간격이 하한 아래인가 — 아래면 글줄이 서로 포개져
                글자가 깨진다. 배수 지정은 -MinLineSpacing 아래, 포인트 지정은 글꼴 크기 아래
      간격    : -Gaps 로 눈금(인치)을 주면, 이웃한 덩어리 사이가 눈금 밖(±0.015")인 자리

    보고 (판정에 안 센다)
      간격    : 슬라이드마다 이웃 덩어리 사이의 세로 · 가로 간격 값의 집합 — 눈금이 몇 개로 섞였나 본다
      정렬    : 같은 슬라이드에서 왼쪽 · 위쪽 가장자리가 0.015" 초과 0.08" 이하로 어긋난 쌍 — 들여쓰기보다 작아
                대개 손이 미끄러진 것이다. 정당한 배치에도 걸리고 캡처에서 눈에 띄므로 판정에는 안 센다
      조합    : 덱 전체의 글꼴 크기 × 줄간격 × 문단 뒤 간격 조합 — 역할 수보다 많으면 어딘가 기본값이 샌 것이다

    덩어리의 경계는 눈에 보이는 경계다 — 채움이나 테두리가 있는 도형과 표는 상자 경계로, 둘 다 없는 글상자는
    글이 실제로 차지한 높이로 잰다(넘친 글은 채움 밖으로도 보이므로 둘 중 큰 쪽). 그 글의 윗변은 상자 윗변이
    아니라 글이 실제로 앉은 자리다 — 세로 맞춤(위 · 가운데 · 아래)을 따른다. 겹침 · 여백 · 간격이 이 경계를
    쓴다. 표는 셀 단위로 본다. 파워포인트는 셀 글이 넘치면 행을 늘려 표 전체가 자라므로, 표의 넘침은 자란 표가
    아래 덩어리와 겹치거나 여백을 넘는 것으로 잡힌다. 배경 장식(테두리로 흘러나가는 원 따위)은 글이 없는
    도형이라 어느 검사에도 걸리지 않는다.

.PARAMETER Path
    검사할 .pptx 경로.

.PARAMETER Gaps
    간격 눈금(인치). 예: -Gaps 0.06,0.15. 주면 눈금 밖 간격을 어긋남으로 센다. 안 주면 간격은 보고만 한다.

.PARAMETER MinLineSpacing
    배수로 지정한 줄간격의 하한. 기본 0.9 — 맑은 고딕은 0.9 에서 줄 사이가 뜨고, 0.8 에서 윗줄 받침과 아랫줄
    머리가 닿으며, 0.7 아래에서 포개진다(파워포인트 렌더 실측).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File audit_layout.ps1 -Path out.pptx
    powershell -ExecutionPolicy Bypass -File audit_layout.ps1 -Path out.pptx -Gaps 0.06,0.15
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Gaps,
    [double]$MinLineSpacing = 0.9
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8   # 한글 판정 줄이 파이프 너머에서도 읽히게
# -File 로 부르면 배열 인자가 "0.06,0.15" 한 문자열로 오므로 글자로 받아 가른다
$gapScale = @()
if ($Gaps) { $gapScale = @($Gaps -split '[,\s]+' | Where-Object { $_ } | ForEach-Object { [double]$_ }) }
. (Join-Path $PSScriptRoot 'office-session.ps1')
$full = (Resolve-Path -LiteralPath $Path).Path
$leaf = Split-Path -Path $Path -Leaf

$before = @(Get-Process POWERPNT -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
# 파워포인트는 하나만 뜬다 — 사람이 쓰고 있었으면 끝에서 그 앱을 안 끈다(office-session.ps1)
$pptWasRunning = ($before.Count -gt 0)
$pp = $null
$session = $null
$pres = $null
$slideW = 0
$slideH = 0
$blocks = @()      # 덩어리 — 글상자와 표. 넘침 · 겹침 · 여백 · 정렬 · 간격의 단위
$paras = @()       # 문단 — 글상자와 표 셀의 문단. 줄간격 · 조합의 단위
$issues = 0

function Clip([string]$t, [int]$n = 30) {
    $t = $t -replace "`r", ' / '
    if ($t.Length -gt $n) { $t = $t.Substring(0, $n) }
    return $t
}

# 한 글틀의 문단을 훑어 줄간격 · 문단 간격을 모은다 — 글상자와 표 셀이 같은 길을 쓴다
function Read-Paragraphs($tf2, [int]$slide, [string]$where) {
    $out = @()
    $tr = $tf2.TextRange
    if (-not $tr.Text.Trim()) { return $out }
    $lines = $tr.Lines().Count
    $n = $tr.Paragraphs().Count
    for ($i = 1; $i -le $n; $i++) {
        $p = $tr.Paragraphs($i, 1)
        if (-not $p.Text.Trim()) { continue }
        $pf = $p.ParagraphFormat
        $sz = [double]$p.Runs(1, 1).Font.Size
        if ($sz -le 0) { $sz = [double]$tr.Font.Size }
        $out += [pscustomobject]@{
            Slide = $slide; Where = $where; Lines = $lines
            Size = [Math]::Round($sz, 1)
            Rule = $(if ($pf.LineRuleWithin -eq -1) { '배수' } else { 'pt' })
            Within = [Math]::Round([double]$pf.SpaceWithin, 2)
            After = [Math]::Round([double]$pf.SpaceAfter, 1)
            Text = (Clip $p.Text)
        }
    }
    return $out
}

try {
    $pp = New-Object -ComObject PowerPoint.Application
    # ReadOnly=$true 로 열어 쓰기 잠금 방지
    $session = Open-OwnedDocument -Kind 'PPT' -Collection $pp.Presentations -Open { $pp.Presentations.Open($full, $true, $false, $false) }
    $pres = $session.Document
    # 아래 재기는 도형의 자동 맞춤과 높이를 바꿨다 되돌린다 — 사람이 열어 둔 발표를 돌려받았으면 그 발표를
    # 바꾸게 되므로 재지 않는다
    if (-not $session.Owned) {
        throw "이 덱이 파워포인트에 열려 있다 — 재는 동안 도형 크기를 바꿨다 되돌리므로 사람의 발표에서는 안 잰다. 그 덱을 닫고 다시 돌린다."
    }

    $slideW = $pres.PageSetup.SlideWidth / 72
    $slideH = $pres.PageSetup.SlideHeight / 72

    foreach ($s in $pres.Slides) {
        foreach ($sh in $s.Shapes) {
            # 표 — 셀마다 문단을 읽고, 표 전체는 한 덩어리로 둔다(파워포인트가 이미 행을 늘려 둔 높이)
            if ($sh.HasTable -eq -1) {
                $tbl = $sh.Table
                $first = ''
                for ($r = 1; $r -le $tbl.Rows.Count; $r++) {
                    for ($c = 1; $c -le $tbl.Columns.Count; $c++) {
                        $cs = $tbl.Cell($r, $c).Shape
                        if ($cs.TextFrame2.HasText -ne -1) { continue }
                        if (-not $first) { $first = Clip $cs.TextFrame2.TextRange.Text 16 }
                        $paras += Read-Paragraphs $cs.TextFrame2 $s.SlideIndex ('표[' + $r + ',' + $c + '] ' + (Clip $cs.TextFrame2.TextRange.Text 16))
                    }
                }
                $blocks += [pscustomobject]@{
                    Slide = $s.SlideIndex; Kind = '표'
                    L = $sh.Left / 72; T = $sh.Top / 72
                    W = $sh.Width / 72; H = $sh.Height / 72
                    Need = $sh.Height / 72
                    VisT = $sh.Top / 72      # 표의 경계는 상자 경계
                    VisH = $sh.Height / 72
                    Text = ('표 ' + $first)
                }
                continue
            }

            if ($sh.HasTextFrame -ne -1) { continue }
            if ($sh.TextFrame.HasText -ne -1) { continue }

            # 재기 전 좌표를 넷 다 받아 둔다 — 자동맞춤은 높이만이 아니라, 가운데 정렬 도형의 위치와 줄바꿈 없는
            # 도형의 너비까지 바꾸므로 높이만 되돌리면 밀린 자리로 재인다
            $l0 = $sh.Left; $t0 = $sh.Top; $w0 = $sh.Width; $h = $sh.Height
            $anchor = $sh.TextFrame2.VerticalAnchor   # 글이 상자 안 어디에 앉나 — 1 위 · 3 가운데 · 4 아래 (2 · 5 는 기준선 판)
            $sh.TextFrame2.AutoSize = 1      # msoAutoSizeShapeToFitText — 필요한 높이를 잰다
            $need = $sh.Height
            $sh.TextFrame2.AutoSize = 0
            $sh.Left = $l0; $sh.Top = $t0; $sh.Width = $w0; $sh.Height = $h   # 잰 뒤 원래대로 (저장하지 않는다)

            # 눈에 보이는 경계 — 채움이나 테두리가 있으면 상자(넘친 글은 그 밖으로도 보이니 큰 쪽), 없으면 글 높이
            $visible = ($sh.Fill.Visible -eq -1) -or ($sh.Line.Visible -eq -1)
            $visH = $(if ($visible) { [Math]::Max($h, $need) } else { $need })
            # 눈에 보이는 윗변 — 상자가 보이면 상자 윗변. 없으면 글이 앉은 자리다: 세로 맞춤이 가운데는 남는 높이의
            # 절반만큼, 아래는 남는 높이만큼 글을 내려앉힌다. 글이 넘치면 남는 높이가 음수라, 같은 식이 위로
            # 흘러나간 만큼을 준다(파워포인트가 가운데는 위아래로 균등하게, 아래는 위로 넘긴다)
            $visT = $t0
            if (-not $visible) {
                if ($anchor -eq 3) { $visT = $t0 + ($h - $need) / 2 }
                elseif ($anchor -eq 4 -or $anchor -eq 5) { $visT = $t0 + ($h - $need) }
            }

            $text = Clip $sh.TextFrame.TextRange.Text
            $paras += Read-Paragraphs $sh.TextFrame2 $s.SlideIndex $text

            $blocks += [pscustomobject]@{
                Slide = $s.SlideIndex; Kind = $(if ($visible) { '도형' } else { '글' })
                L = $l0 / 72; T = $t0 / 72
                W = $w0 / 72; H = $h / 72
                Need = $need / 72
                VisT = $visT / 72
                VisH = $visH / 72
                Text = $text
            }
        }
    }
} finally {
    Close-OwnedDocument $session
    [void](Exit-OfficeApp -App $pp -Kind 'PPT' -WasRunning $pptWasRunning)
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

$cnt = @{ 넘침 = 0; 겹침 = 0; 여백 = 0; 줄간격 = 0; 간격 = 0 }

# ---- 넘침 · 여백 (글상자 · 도형은 필요 높이로, 여백은 보이는 경계로) ----
foreach ($b in $blocks) {
    if ($b.Kind -ne '표' -and ($b.Need - $b.H) -gt 0.03) {
        Write-Output ('S{0} 넘침    필요 {1:N2}in / 자리 {2:N2}in | {3}' -f $b.Slide, $b.Need, $b.H, $b.Text)
        $cnt.넘침++
    }
    $bottom = $b.VisT + $b.VisH
    $right = $b.L + $b.W
    if ($b.L -lt 0.5 -or $b.VisT -lt 0.4 -or $right -gt ($slideW - 0.5) -or $bottom -gt ($slideH - 0.5)) {
        Write-Output ('S{0} 여백    L{1:N2} R{2:N2} T{3:N2} B{4:N2} | {5}' -f $b.Slide, $b.L, $right, $b.VisT, $bottom, $b.Text)
        $cnt.여백++
    }
}

# ---- 겹침 ----
foreach ($g in $blocks | Group-Object Slide) {
    $arr = @($g.Group)
    for ($i = 0; $i -lt $arr.Count; $i++) {
        for ($j = $i + 1; $j -lt $arr.Count; $j++) {
            $a = $arr[$i]; $b = $arr[$j]
            $ox = [Math]::Min($a.L + $a.W, $b.L + $b.W) - [Math]::Max($a.L, $b.L)
            $oy = [Math]::Min($a.VisT + $a.VisH, $b.VisT + $b.VisH) - [Math]::Max($a.VisT, $b.VisT)
            if ($ox -gt 0.05 -and $oy -gt 0.03) {
                Write-Output ('S{0} 겹침    {1:N2}in x {2:N2}in | {3} <-> {4}' -f $g.Name, $ox, $oy, $a.Text, $b.Text)
                $cnt.겹침++
            }
        }
    }
}

# ---- 줄간격 — 줄이 둘 이상인 글틀만, 글틀마다 한 번(가장 좁은 문단으로). 한 줄짜리는 포갤 상대가 없다 ----
foreach ($g in $paras | Where-Object { $_.Lines -ge 2 } | Group-Object Slide, Where) {
    $worst = $null
    foreach ($p in $g.Group) {
        $bad = $(if ($p.Rule -eq '배수') { $p.Within -lt $MinLineSpacing } else { $p.Within -lt $p.Size })
        if ($bad -and ((-not $worst) -or $p.Within -lt $worst.Within)) { $worst = $p }
    }
    if ($worst) {
        $unit = $(if ($worst.Rule -eq '배수') { '배' } else { 'pt' })
        Write-Output ('S{0} 줄간격  {1}{2} (글꼴 {3}pt) | {4}' -f $worst.Slide, $worst.Within, $unit, $worst.Size, $worst.Where)
        $cnt.줄간격++
    }
}

# ---- 정렬 — 가장자리의 살짝 어긋남 (0.015" 초과 0.08" 이하). 상자 가장자리(L · T)로 잰다. 정당한 배치에도 걸려 판정에 안 세고 보고만 한다 ----
$alignReport = @()
foreach ($g in $blocks | Group-Object Slide) {
    foreach ($edge in 'L', 'T') {
        $vals = @($g.Group | ForEach-Object { [Math]::Round($_.$edge, 2) } | Sort-Object -Unique)
        for ($i = 1; $i -lt $vals.Count; $i++) {
            $d = $vals[$i] - $vals[$i - 1]
            if ($d -gt 0.015 -and $d -le 0.08) {
                $a = ($g.Group | Where-Object { [Math]::Round($_.$edge, 2) -eq $vals[$i - 1] } | Select-Object -First 1).Text
                $b = ($g.Group | Where-Object { [Math]::Round($_.$edge, 2) -eq $vals[$i] } | Select-Object -First 1).Text
                $name = $(if ($edge -eq 'L') { '왼쪽' } else { '위쪽' })
                $alignReport += ('· S{0} 정렬    {1} {2:N2}in 와 {3:N2}in 이 {4:N2}in 어긋남 | {5} <-> {6}' -f $g.Name, $name, $vals[$i - 1], $vals[$i], $d, $a, $b)
            }
        }
    }
}

# ---- 간격 — 이웃한 덩어리 사이 (사이에 다른 덩어리가 없는 쌍만) ----
$gapReport = @()
foreach ($g in $blocks | Group-Object Slide) {
    $arr = @($g.Group)
    $v = @(); $hz = @()
    for ($i = 0; $i -lt $arr.Count; $i++) {
        for ($j = 0; $j -lt $arr.Count; $j++) {
            if ($i -eq $j) { continue }
            $a = $arr[$i]; $b = $arr[$j]
            $ox = [Math]::Min($a.L + $a.W, $b.L + $b.W) - [Math]::Max($a.L, $b.L)
            $oy = [Math]::Min($a.VisT + $a.VisH, $b.VisT + $b.VisH) - [Math]::Max($a.VisT, $b.VisT)
            # 세로 — a 가 위, b 가 아래, 가로로 겹친다 (경계는 보이는 경계)
            if ($ox -gt 0.05) {
                $gap = $b.VisT - ($a.VisT + $a.VisH)
                if ($gap -ge -0.005 -and $gap -le 1.0) {
                    $between = $arr | Where-Object { $_ -ne $a -and $_ -ne $b -and
                        ([Math]::Min($_.L + $_.W, $a.L + $a.W) - [Math]::Max($_.L, $a.L)) -gt 0.05 -and
                        $_.VisT -ge ($a.VisT + $a.VisH - 0.005) -and ($_.VisT + $_.VisH) -le ($b.VisT + 0.005) }
                    if (-not $between) { $v += [pscustomobject]@{ Gap = [Math]::Round([Math]::Max($gap, 0), 2); A = $a.Text; B = $b.Text } }
                }
            }
            # 가로 — a 가 왼쪽, b 가 오른쪽, 세로로 겹친다
            if ($oy -gt 0.05) {
                $gap = $b.L - ($a.L + $a.W)
                if ($gap -ge -0.005 -and $gap -le 1.0) {
                    $between = $arr | Where-Object { $_ -ne $a -and $_ -ne $b -and
                        ([Math]::Min($_.VisT + $_.VisH, $a.VisT + $a.VisH) - [Math]::Max($_.VisT, $a.VisT)) -gt 0.05 -and
                        $_.L -ge ($a.L + $a.W - 0.005) -and ($_.L + $_.W) -le ($b.L + 0.005) }
                    if (-not $between) { $hz += [pscustomobject]@{ Gap = [Math]::Round([Math]::Max($gap, 0), 2); A = $a.Text; B = $b.Text } }
                }
            }
        }
    }
    $vs = @($v | ForEach-Object { $_.Gap } | Sort-Object -Unique)
    $hs = @($hz | ForEach-Object { $_.Gap } | Sort-Object -Unique)
    $gapReport += ('· S{0} 간격    세로 {{{1}}} · 가로 {{{2}}}' -f $g.Name, ($vs -join ', '), ($hs -join ', '))
    if ($gapScale.Count -gt 0) {
        foreach ($x in @($v) + @($hz)) {
            $near = $gapScale | Where-Object { [Math]::Abs($_ - $x.Gap) -le 0.015 }
            if (-not $near) {
                Write-Output ('S{0} 간격    {1:N2}in 은 눈금 밖 | {2} <-> {3}' -f $g.Name, $x.Gap, $x.A, $x.B)
                $cnt.간격++
            }
        }
    }
}

$issues = ($cnt.Values | Measure-Object -Sum).Sum

# ---- 보고 — 판정에 안 센다 ----
$gapReport | ForEach-Object { Write-Output $_ }
$alignReport | ForEach-Object { Write-Output $_ }
$combos = @($paras | ForEach-Object { '{0}pt×{1}{2}+{3}pt' -f $_.Size, $_.Within, $(if ($_.Rule -eq '배수') { '배' } else { 'pt' }), $_.After } | Sort-Object -Unique)
Write-Output ('· 조합    글꼴×줄간격+문단뒤 {0}가지: {1}' -f $combos.Count, ($combos -join ' · '))

if ($issues -eq 0) {
    Write-Output '이상 없음 — 넘침 0 · 겹침 0 · 여백 위반 0 · 줄간격 0 · 간격 0'
} else {
    Write-Output ('검출 {0}건 — 넘침 {1} · 겹침 {2} · 여백 {3} · 줄간격 {4} · 간격 {5}' -f $issues, $cnt.넘침, $cnt.겹침, $cnt.여백, $cnt.줄간격, $cnt.간격)
}
exit ([int]($issues -gt 0))
