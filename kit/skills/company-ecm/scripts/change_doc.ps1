<#
    편집으로 열린 오피스 문서 하나를 그 창 안에서 고치고 저장한다 — 창은 닫지 않는다(올리기는 checkin 이 한다).

    부르는 꼴:
        powershell -NoProfile -ExecutionPolicy Bypass -File change_doc.ps1 -Path <받은 파일> -App Word|Excel|PPT -Ops <JSON 파일>
            [-WaitSeconds 30]

    ops — {"replace": [{"old": 옛 조각, "new": 새 조각}…], "insert": [평문 파일 경로…], "after": 장 · 시트 번호 | null}
      - replace — 옛 조각은 문서 글자에 **꼭 한 번** 나와야 한다(한 문단 · 한 칸 안. 빈칸 · 탭 · 줄 안 빈칸의 수는 너그럽게 맞춘다).
        바꾼 글은 그 자리 첫 글자의 서식을 따른다. 파워포인트는 장마다 글 칸 · 표 칸 · 묶음 안, 워드는 본문 · 글상자 · 머리글 같은 이야기
        모두, 엑셀은 시트마다 값 칸을 센다 — 엑셀의 수식 칸에 걸리면 안 고친다
      - insert — 평문 파일을 열린 문서로 옮긴다. 파워포인트는 그 덱의 장 모두를 ``after`` 장 뒤에(없으면 끝에, 옮긴 장은 받는 덱의
        디자인을 따른다), 엑셀은 시트 모두를 ``after`` 시트 뒤에(0 이면 맨 앞), 워드는 본문 끝에(``after`` 를 안 받는다)
      - 둘 다 비면 저장 안 된 고침이 있을 때만 저장한다(올리기 미리 보기가 창의 판을 디스크에 세운다)

    내는 것: 표준 출력에 JSON 한 줄({"found":…,"applied":[{"op":…,"where":…}…],"saved":…,"why":…}). 종료 값 0 고치고 저장했다 ·
    2 시한 안에 그 문서가 안 떴다 · 3 못 고칠 까닭이 있어 **아무것도 안 고쳤다**(why) · 1 고치다 멈췄다(applied 까지 고쳤고 저장하지
    않았다 — 창에 그 판이 떠 있다).

    못 고칠 까닭(조각이 0 번 · 여러 번 · 수식 칸 · 넣을 자리 밖)을 다 가린 뒤에야 문서를 건드린다 — 반쯤 고친 판을 안 남긴다. 조각
    바꾸기가 먼저고 끼워 넣기가 뒤다 — 조각은 원래 문서를 가리키는 말이다. 찾는 손은 곁의 office_doc.ps1 이 든다.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][ValidateSet('Word', 'Excel', 'PPT')][string]$App,
    [Parameter(Mandatory = $true)][string]$Ops,
    [int]$WaitSeconds = 30
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
. (Join-Path $PSScriptRoot 'office_doc.ps1')

$SPACE = '[ \t 　]+'      # 조각 안의 빈칸 한 무리 — 화면에 보이는 빈칸의 수 · 꼴이 달라도 맞춘다(줄은 안 건넌다)
$MSO_GROUP = 6                     # 파워포인트 도형 갈래 — 묶음
$MSO_TRUE = -1
$WD_FIND_STOP = 0
$WD_COLLAPSE_END = 0
$STORY_WORD = @{ 1 = '본문'; 2 = '각주'; 3 = '미주'; 4 = '메모'; 5 = '글상자'; 6 = '머리글'; 7 = '머리글'; 8 = '바닥글'; 9 = '바닥글';
                 10 = '머리글'; 11 = '바닥글' }

function Write-Result([bool]$Found, $Applied, [bool]$Saved, [string]$Why) {
    Write-Output (@{ found = $Found; applied = @($Applied); saved = $Saved; why = $Why } | ConvertTo-Json -Compress -Depth 4)
}

function Get-Pattern([string]$Old) {
    return ((($Old.Trim() -split $SPACE) | ForEach-Object { [regex]::Escape($_) }) -join $SPACE)
}

# ── 글이 든 자리 — 앱마다 { Where; Text; Set(새 판의 글) } 를 낸다 ─────────────────────────

function Add-ShapeSpots($Shape, [string]$Where, $Out) {
    try { if ($Shape.Type -eq $MSO_GROUP) { foreach ($s in $Shape.GroupItems) { Add-ShapeSpots $s $Where $Out }; return } } catch { }
    try {
        if ($Shape.HasTable -eq $MSO_TRUE) {
            $table = $Shape.Table
            for ($r = 1; $r -le $table.Rows.Count; $r++) {
                for ($c = 1; $c -le $table.Columns.Count; $c++) {
                    [void]$Out.Add(@{ Where = "$Where 표 $r 행 $c 열"; Range = $table.Cell($r, $c).Shape.TextFrame.TextRange })
                }
            }
            return
        }
    } catch { }
    try { if ($Shape.HasTextFrame -eq $MSO_TRUE) { [void]$Out.Add(@{ Where = $Where; Range = $Shape.TextFrame.TextRange }) } } catch { }
}

function Get-Spots($Document) {
    <# 글이 든 자리들 — 파워포인트 · 워드는 TextRange · Range, 엑셀은 칸(시트 · 행 · 열 · 수식인가) #>
    $out = New-Object System.Collections.ArrayList
    switch ($App) {
        'PPT' {
            foreach ($slide in $Document.Slides) {
                foreach ($shape in $slide.Shapes) { Add-ShapeSpots $shape ("장 " + $slide.SlideIndex) $out }
            }
        }
        'Word' {
            foreach ($story in $Document.StoryRanges) {
                $s = $story
                while ($null -ne $s) {
                    $word = $STORY_WORD[[int]$s.StoryType]
                    [void]$out.Add(@{ Where = $(if ($word) { $word } else { '이야기 ' + $s.StoryType }); Range = $s })
                    $s = $s.NextStoryRange
                }
            }
        }
        'Excel' {
            foreach ($sheet in $Document.Worksheets) {
                $used = $sheet.UsedRange
                $formulas = $used.Formula
                $rows, $cols, $top, $left = $used.Rows.Count, $used.Columns.Count, $used.Row, $used.Column
                for ($r = 1; $r -le $rows; $r++) {
                    for ($c = 1; $c -le $cols; $c++) {
                        $value = if ($rows -eq 1 -and $cols -eq 1) { $formulas } else { $formulas[$r, $c] }
                        if ($value -is [string] -and $value) {
                            [void]$out.Add(@{ Where = $sheet.Name + '!' + $sheet.Cells.Item($top + $r - 1, $left + $c - 1).Address($false, $false);
                                              Sheet = $sheet; Row = $top + $r - 1; Col = $left + $c - 1; Text = $value;
                                              Formula = $value.StartsWith('=') })
                        }
                    }
                }
            }
        }
    }
    return , $out
}

function Get-Text($Spot) {
    if ($App -eq 'Excel') { return $Spot.Text }
    try { return [string]$Spot.Range.Text } catch { return '' }
}

function Set-Piece($Spot, [System.Text.RegularExpressions.Match]$Hit, [string]$New) {
    switch ($App) {
        'PPT' {
            $piece = $Spot.Range.Characters($Hit.Index + 1, $Hit.Length)
            $piece.Text = ($New -replace "`r?`n", "`r")
        }
        'Word' {
            # 이야기 글의 자리와 Range 의 자리는 필드 · 숨은 글에서 어긋난다 — 맞은 글 그대로를 그 이야기 안에서 찾아 간다.
            # 워드 찾기는 ^ 를 특수 글자(^p 따위)로 읽는다 — ^^ 로 풀어 글자 그대로 찾는다
            $found = $Spot.Range.Duplicate
            $found.Find.ClearFormatting()
            if (-not $found.Find.Execute(($Hit.Value -replace '\^', '^^'), $true, $false, $false, $false, $false, $true, $WD_FIND_STOP)) {
                throw "워드가 맞은 글을 다시 못 찾았다: $($Hit.Value)"
            }
            $found.Text = ($New -replace "`r?`n", "`r")
        }
        'Excel' {
            $text = $Spot.Text.Substring(0, $Hit.Index) + $New + $Spot.Text.Substring($Hit.Index + $Hit.Length)
            $Spot.Sheet.Cells.Item($Spot.Row, $Spot.Col).Formula = $text   # 사람이 칸에 친 것과 같다 — 수는 수로 선다
        }
    }
}

function Find-Pieces($Spots, $Replace) {
    <# 바꿀 조각마다 꼭 한 자리 — @{ Spot; Hit; New; Old } 들. 하나라도 0 번 · 여러 번 · 수식 칸이면 그 까닭(글자)을 낸다 #>
    $plan = @()
    foreach ($pair in $Replace) {
        $old, $new = [string]$pair.old, [string]$pair.new
        $pattern = Get-Pattern $old
        $hits = @()
        foreach ($spot in $Spots) {
            foreach ($m in [regex]::Matches((Get-Text $spot), $pattern)) { $hits += @{ Spot = $spot; Hit = $m } }
        }
        if ($hits.Count -eq 0) { return "「$old」 이 문서 글자에 없다 — 화면에 보이는 글자 그대로, 한 문단 · 한 칸 안의 조각을 준다" }
        if ($hits.Count -gt 1) {
            $where = (@($hits | ForEach-Object { $_.Spot.Where }) | Select-Object -Unique) -join ' · '
            return "「$old」 이 문서에 $($hits.Count) 번 나온다($where) — 앞뒤 글을 더 붙여 한 번만 나오는 조각을 준다"
        }
        if ($App -eq 'Excel' -and $hits[0].Spot.Formula) {
            return "「$old」 이 수식 칸($($hits[0].Spot.Where))에 있다 — 수식은 안 고친다. 사람이 그 칸을 화면에서 고친다"
        }
        $plan += @{ Spot = $hits[0].Spot; Hit = $hits[0].Hit; New = $new; Old = $old }
    }
    return , $plan
}

function Get-InsertPlace($Document, $After) {
    <# 끼워 넣을 자리의 끝 번호(장 · 시트 수)와 받는 ``after`` 가 맞나 — 틀리면 까닭(글자) #>
    switch ($App) {
        'PPT'   { $count = $Document.Slides.Count; $what = '장' }
        'Excel' { $count = $Document.Sheets.Count; $what = '시트' }
        'Word'  { if ($null -ne $After) { return '워드는 본문 끝에만 넣는다 — --after 를 빼고 준다' }; return $null }
    }
    if ($null -ne $After -and ([int]$After -lt 0 -or [int]$After -gt $count)) {
        return "--after $After 는 이 문서의 $what 수($count) 밖이다 — 0 부터 $count 까지"
    }
    return $null
}

function Add-FromFile($Application, $Document, [string]$File, [ref]$After) {
    switch ($App) {
        'PPT' {
            $at = if ($null -eq $After.Value) { $Document.Slides.Count } else { [int]$After.Value }
            $added = $Document.Slides.InsertFromFile($File, $at)
            $After.Value = $at + [int]$added
            return "장 $($at + 1) 부터 $added 장"
        }
        'Excel' {
            $alerts = $Application.DisplayAlerts
            $Application.DisplayAlerts = $false   # 원본 통합 문서의 링크 · 호환 물음이 이 손을 묶지 않게 — 끝나면 되돌린다
            try {
                $source = $Application.Workbooks.Open($File, 0, $true)
                try {
                    $at = if ($null -eq $After.Value) { $Document.Sheets.Count } else { [int]$After.Value }
                    $count = $source.Sheets.Count
                    if ($at -eq 0) { $source.Sheets.Copy($Document.Sheets.Item(1)) }
                    else { $source.Sheets.Copy([System.Reflection.Missing]::Value, $Document.Sheets.Item($at)) }
                    $After.Value = $at + $count
                    return "시트 $($at + 1) 부터 $count 개"
                } finally { $source.Close($false); Release $source }
            } finally { $Application.DisplayAlerts = $alerts }
        }
        'Word' {
            $end = $Document.Content
            $end.Collapse($WD_COLLAPSE_END)
            $end.InsertFile($File)
            return '본문 끝'
        }
    }
}

$spec = Get-Content -Raw -Encoding UTF8 -LiteralPath $Ops | ConvertFrom-Json
$replace = @($spec.replace | Where-Object { $null -ne $_ })
$insert = @($spec.insert | Where-Object { $_ })
$after = $spec.after

$found = Find-OpenDocument $Path $WaitSeconds
if ($null -eq $found) { Write-Result $false @() $false ''; exit 2 }
$application, $doc = $found.Application, $found.Document
$applied = @()
try {
    # 못 고칠 까닭을 다 가린다 — 하나라도 걸리면 아무것도 안 건드린다
    $plan = @()
    if ($replace.Count) {
        $plan = Find-Pieces (Get-Spots $doc) $replace
        if ($plan -is [string]) { Write-Result $true @() $false $plan; exit 3 }
    }
    if ($insert.Count) {
        $why = Get-InsertPlace $doc $after
        if ($why) { Write-Result $true @() $false $why; exit 3 }
        foreach ($file in $insert) {
            if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { Write-Result $true @() $false "넣을 파일이 없다: $file"; exit 3 }
        }
    }
    foreach ($step in $plan) {
        Set-Piece $step.Spot $step.Hit $step.New
        $applied += @{ op = 'replace'; where = $step.Spot.Where; old = $step.Old; new = $step.New }
    }
    $place = $after
    foreach ($file in $insert) {
        $where = Add-FromFile $application $doc ([string]$file) ([ref]$place)
        $applied += @{ op = 'insert'; where = $where; file = [string]$file }
    }
    $saved = $false
    if ($applied.Count -or -not (Test-Clean $doc)) { $doc.Save(); $saved = $true }
    Write-Result $true $applied $saved ''
    exit 0
} catch {
    Write-Result $true $applied $false ('고치다 멈췄다: ' + $_.Exception.Message)
    exit 1
} finally {
    Release $doc; Release $application
}
