# DRM 감긴 문서에서 글자를 뽑는다 — 설치된 오피스를 태워서.
#
# 왜 이 파일이 있나: Fasoo DRM 은 파일을 통째로 자기 컨테이너로 감싼다. 머리 바이트가
# `%PDF-`·`PK` 가 아니게 되므로 어떤 파서(PDFium·pdfplumber·python-docx·openpyxl)도
# 형식 인식 단계에서 죽는다. 정식 오피스 앱은 그 보호를 복호해 주므로 그것을 태운다.
#
# 규모가 이 파일을 정당화한다 — 문서가 여러 건이고 확장자가 갈리고, 앱 인스턴스를
# 재사용해야 느려지지 않는다. 한 건이면 이 파일 없이 인라인으로 해도 된다.

[CmdletBinding()]
param(
    # 읽을 파일들. 폴더를 주면 그 안의 지원 확장자를 전부 훑는다.
    [Parameter(Mandatory = $true, Position = 0)]
    [string[]]$Path,

    # 뽑은 글자를 넣을 폴더. 생략하면 화면으로만 낸다.
    [string]$OutDir,

    # 화면에 낼 때 파일마다 보여줄 앞부분 글자 수.
    [int]$Preview = 300
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 어느 확장자를 어느 앱이 드나. PDF 는 워드가 든다 — Acrobat COM 은 이 기계에서
# 클래스 미등록(0x80040154)이라 못 탄다.
$HANDLER = @{
    '.doc'  = 'Word';  '.docx' = 'Word';  '.rtf'  = 'Word';  '.pdf' = 'Word'
    '.xls'  = 'Excel'; '.xlsx' = 'Excel'; '.xlsm' = 'Excel'; '.csv' = 'Excel'
    '.ppt'  = 'PPT';   '.pptx' = 'PPT'
}

function Get-FileHead {
    <# 파일 머리 8바이트를 눈으로 읽을 꼴로. DRM 이 감쌌으면 `. DRMONE` 처럼 나온다. #>
    param([string]$LiteralPath)
    $bytes = [System.IO.File]::ReadAllBytes($LiteralPath)
    $n = [Math]::Min(8, $bytes.Length)
    if ($n -eq 0) { return '(빈 파일)' }
    -join ($bytes[0..($n - 1)] | ForEach-Object {
        if ($_ -ge 32 -and $_ -lt 127) { [char]$_ } else { '.' }
    })
}

function Test-PlainFormat {
    <# 감기지 않은 원래 형식인가. 감겼으면 $false — 그때만 이 스크립트가 값을 낸다. #>
    param([string]$LiteralPath)
    $bytes = [System.IO.File]::ReadAllBytes($LiteralPath)
    if ($bytes.Length -lt 4) { return $false }
    $sig = -join ($bytes[0..3] | ForEach-Object { [char]$_ })
    return ($sig -eq '%PDF' -or $sig.StartsWith('PK') -or $sig.StartsWith('{\rt') -or
            ($bytes[0] -eq 0xD0 -and $bytes[1] -eq 0xCF))   # 옛 오피스 OLE
}

function New-OfficeApp {
    <# 앱 하나를 띄운다. 파일마다 띄우면 건당 수 초씩 붙으므로 앱은 재사용한다. #>
    param([string]$AppName, [ref]$SpawnedPids)
    switch ($AppName) {
        'Word' {
            $a = New-Object -ComObject Word.Application
            $a.Visible = $false
            $a.DisplayAlerts = 0          # wdAlertsNone — 변환 대화창이 뜨면 무인 실행이 멈춘다
            return $a
        }
        'Excel' {
            $a = New-Object -ComObject Excel.Application
            $a.Visible = $false
            $a.DisplayAlerts = $false
            return $a
        }
        'PPT' {
            # ⚠ 파워포인트는 Visible=$false 를 거부한다(그 앱만 그렇다).
            # Fasoo DRM 훅으로 인해 COM Quit 후에도 백그라운드에 남아 권한 오류 팝업을 띄우므로
            # 생성된 PID를 추적하여 읽기 완료 후 즉시 강제 종료한다.
            $beforePids = @(Get-Process -Name POWERPNT -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
            $a = New-Object -ComObject PowerPoint.Application
            $afterProcs = @(Get-Process -Name POWERPNT -ErrorAction SilentlyContinue)
            $newPids = @($afterProcs | Where-Object { $beforePids -notcontains $_.Id } | Select-Object -ExpandProperty Id)
            if ($SpawnedPids -and $newPids.Count -gt 0) {
                $SpawnedPids.Value += $newPids
            }
            return $a
        }
    }
}

function Read-WithWord {
    param($App, [string]$LiteralPath)
    # 인자 셋 — 경로 · ConfirmConversions=$false · ReadOnly=$true.
    # ReadOnly 를 켜야 원본에 쓰기 잠금이 안 걸리고 DRM 이 수정으로 보지 않는다.
    $doc = $App.Documents.Open($LiteralPath, $false, $true)
    try {
        try { $doc.Saved = $true } catch { }
        return [string]$doc.Content.Text
    } finally {
        try { $doc.Close($false) } catch { }   # SaveChanges=$false — 원본을 절대 안 고친다
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null } catch { }
    }
}

function Read-WithExcel {
    param($App, [string]$LiteralPath)
    $book = $App.Workbooks.Open($LiteralPath, 0, $true)   # UpdateLinks=0 · ReadOnly=$true
    try {
        try { $book.Saved = $true } catch { }
        $out = [System.Text.StringBuilder]::new()
        foreach ($sheet in $book.Sheets) {
            [void]$out.AppendLine("### 시트: $($sheet.Name)")
            $used = $sheet.UsedRange
            if ($used.Count -le 1 -and [string]::IsNullOrEmpty($used.Value2)) { continue }
            for ($r = 1; $r -le $used.Rows.Count; $r++) {
                $cells = @()
                for ($c = 1; $c -le $used.Columns.Count; $c++) {
                    $cells += [string]$used.Cells.Item($r, $c).Text
                }
                # 행으로 묶는다 — 셀마다 줄을 끊으면 표라는 것이 사라져 모델이 못 알아본다.
                [void]$out.AppendLine('| ' + ($cells -join ' | ') + ' |')
            }
        }
        return $out.ToString()
    } finally {
        try { $book.Close($false) } catch { }
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($book) | Out-Null } catch { }
    }
}

function Read-WithPPT {
    param($App, [string]$LiteralPath)
    # 인자 — 경로 · ReadOnly=$true · Untitled=$false · WithWindow=$false
    $pres = $App.Presentations.Open($LiteralPath, $true, $false, $false)
    try {
        try { $pres.Saved = $true } catch { }
        $out = [System.Text.StringBuilder]::new()
        foreach ($slide in $pres.Slides) {
            [void]$out.AppendLine("### 장 $($slide.SlideIndex)")
            foreach ($shape in $slide.Shapes) {
                if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                    [void]$out.AppendLine([string]$shape.TextFrame.TextRange.Text)
                }
                # 표(Table) 도형 내부 텍스트 추출 보강
                if ((Flag $shape.HasTable) -eq 1) {
                    try {
                        $tbl = $shape.Table
                        for ($r = 1; $r -le $tbl.Rows.Count; $r++) {
                            $rowCells = @()
                            for ($c = 1; $c -le $tbl.Columns.Count; $c++) {
                                $rowCells += [string]$tbl.Cell($r, $c).Shape.TextFrame.TextRange.Text
                            }
                            [void]$out.AppendLine('| ' + ($rowCells -join ' | ') + ' |')
                        }
                    } catch { }
                }
                # 그룹(Group) 도형 내부 텍스트 추출 보강
                if ($shape.Type -eq 6) {
                    try {
                        foreach ($sub in $shape.GroupItems) {
                            if ($sub.HasTextFrame -and $sub.TextFrame.HasText) {
                                [void]$out.AppendLine([string]$sub.TextFrame.TextRange.Text)
                            }
                        }
                    } catch { }
                }
            }
        }
        return $out.ToString()
    } finally {
        try { $pres.Close() } catch { }
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres) | Out-Null } catch { }
    }
}

# ── 대상 모으기 ────────────────────────────────────────────────────────────
$targets = [System.Collections.Generic.List[string]]::new()
foreach ($item in $Path) {
    if (Test-Path -LiteralPath $item -PathType Container) {
        Get-ChildItem -LiteralPath $item -File | Where-Object {
            $HANDLER.ContainsKey($_.Extension.ToLower())
        } | ForEach-Object { $targets.Add($_.FullName) }
    } elseif (Test-Path -LiteralPath $item) {
        $targets.Add((Resolve-Path -LiteralPath $item).Path)
    } else {
        Write-Warning "없는 경로: $item"
    }
}
if ($targets.Count -eq 0) { Write-Error '읽을 파일이 없다.'; exit 1 }

if ($OutDir -and -not (Test-Path -LiteralPath $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

# ── 앱별로 묶어 돈다 — 앱 생성이 비싸므로 확장자별로 모아 한 번만 띄운다 ──────
$byApp = $targets | Group-Object { $HANDLER[[System.IO.Path]::GetExtension($_).ToLower()] }
$apps = @{}
$pptSpawnedPids = [System.Collections.Generic.List[int]]::new()
$done = 0
$failed = 0

try {
    foreach ($group in $byApp) {
        $appName = $group.Name
        if (-not $appName) { continue }

        if (-not $apps.ContainsKey($appName)) {
            try {
                $apps[$appName] = New-OfficeApp -AppName $appName -SpawnedPids ([ref]$pptSpawnedPids)
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
                $text = switch ($appName) {
                    'Word'  { Read-WithWord  -App $app -LiteralPath $file }
                    'Excel' { Read-WithExcel -App $app -LiteralPath $file }
                    'PPT'   { Read-WithPPT   -App $app -LiteralPath $file }
                }
                $len = $text.Length
                Write-Output "[$mark] $name — $appName · 글자 $len · 머리 [$head]"

                if ($OutDir) {
                    $dest = Join-Path $OutDir "$name.txt"
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
    # ⚠ 여기를 건너뛰면 보이지 않는 오피스 프로세스가 쌓여 다음 실행이 느려지거나 멈춘다.
    foreach ($a in $apps.Values) {
        try { $a.Quit() } catch { }
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($a) | Out-Null } catch { }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()

    # ⚠ 파워포인트는 COM Quit 후에도 Fasoo DRM 훅이나 잔여 핸들 때문에 프로세스가 남아
    # "열람 권한이 없습니다(0x703000...)" 팝업이 무한 반복될 수 있다.
    # 스크립트가 띄운 파워포인트 프로세스는 즉시 강제 종료한다.
    if ($pptSpawnedPids.Count -gt 0) {
        foreach ($pidToKill in $pptSpawnedPids) {
            $proc = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
            }
        }
    }

    # ⚠ DocumentRecovery 트리를 통째로 지우면 사용자의 정상적인 미저장 복구 파일이 날아간다.
    # $targets 에 매칭되는 특정 항목만 선별 삭제(Targeted Cleanup)한다.
    $targetLeaves = @($targets | ForEach-Object { Split-Path -Path $_ -Leaf })
    $officeVerKeys = @(Get-ChildItem -Path "HKCU:\Software\Microsoft\Office" -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^\d+\.\d+$' })
    foreach ($ver in $officeVerKeys) {
        foreach ($appKey in @('PowerPoint', 'Word', 'Excel')) {
            $recPath = "HKCU:\Software\Microsoft\Office\$($ver.PSChildName)\$appKey\Resiliency\DocumentRecovery"
            if (Test-Path -LiteralPath $recPath) {
                try {
                    $item = Get-Item -LiteralPath $recPath -ErrorAction SilentlyContinue
                    if ($item) {
                        foreach ($valName in $item.GetValueNames()) {
                            $isMatch = $false
                            foreach ($tl in $targetLeaves) {
                                if ($valName -like "*$tl*") { $isMatch = $true; break }
                            }
                            if (-not $isMatch) {
                                try {
                                    $rawBytes = [byte[]]$item.GetValue($valName)
                                    $rawText = [System.Text.Encoding]::Unicode.GetString($rawBytes)
                                    foreach ($tl in $targetLeaves) {
                                        if ($rawText -like "*$tl*") { $isMatch = $true; break }
                                    }
                                } catch { }
                            }
                            if ($isMatch) {
                                Remove-ItemProperty -LiteralPath $recPath -Name $valName -Force -ErrorAction SilentlyContinue
                            }
                        }
                    }
                } catch { }
            }
        }
    }

    # 읽기 과정에서 생성된 임시 락 파일(~$...) 정리
    foreach ($target in $targets) {
        $parentDir = Split-Path -Path $target -Parent
        $fileName = Split-Path -Path $target -Leaf
        $lockFile = Join-Path $parentDir ("~$" + $fileName)
        if (Test-Path -LiteralPath $lockFile) {
            Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Output ''
Write-Output "읽음 $done · 실패 $failed · 전체 $($targets.Count)"
if ($OutDir) { Write-Output "글자는 여기 — $OutDir" }
if ($failed -gt 0) { exit 1 }
