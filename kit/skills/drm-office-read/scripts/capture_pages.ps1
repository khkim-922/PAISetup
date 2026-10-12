<#
.SYNOPSIS
    DRM 환경에서 Word 문서와 PDF의 페이지를, 엑셀 통합문서의 차트·그림·도형을 PNG로 꺼낸다.

.DESCRIPTION
    Word가 화면에 그린 페이지의 EnhMetaFileBits를 메모리에서 받아 PowerShell이 PNG로 쓴다.
    Office의 내보내기/다른 이름으로 저장을 쓰지 않으므로 원본을 저장하거나 DRM을 해제하지 않는다.
    read-drm.ps1의 Document.Content.Text가 이미지·도형·머리글 또는 공간 배치를 놓칠 때 쓴다.

    엑셀에는 EnhMetaFileBits 같은 메모리 통로가 없다. 그림을 꺼내는 길은 파일 내보내기
    (Chart.Export)와 클립보드 복사(CopyPicture)뿐인데, DRM 필터는 Office가 디스크에 쓰는
    산출물을 가로챈다(capture_slides.ps1 머리말). 그래서 클립보드에 벡터 그림(EMF)으로 받아
    Word와 같은 변환으로 PNG를 쓴다. 시트 탭 차례대로 시트째 차트, 시트 사용 영역, 시트 위 도형마다
    한 장이다. Word 의 표도 같은 길로 한 장씩 뜬다(table-NN.png).
    클립보드를 쓰므로 하던 복사는 사라지고, 끝나면 보호 문서의 그림을 남기지 않게 비운다.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File capture_pages.ps1 -Path report.pdf
    powershell -NoProfile -ExecutionPolicy Bypass -File capture_pages.ps1 -Path report.docx -Pages "1,3"
    powershell -NoProfile -ExecutionPolicy Bypass -File capture_pages.ps1 -Path sales.xlsx -Pages "2"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Pages,
    [string]$OutDir,
    [ValidateRange(400, 4000)][int]$Width = 1600
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'office-session.ps1')
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Threading;
public static class DrmOfficeWindow {
    [DllImport("user32.dll")]
    static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
    public static uint ProcessId(long window) {
        uint processId;
        GetWindowThreadProcessId(new IntPtr(window), out processId);
        return processId;
    }
}
// Win32 로 직접 연다 — WinForms Clipboard 는 STA 를 요구하고 EMF 를 못 꺼낸다.
public static class DrmClipboard {
    const uint CF_ENHMETAFILE = 14;
    [DllImport("user32.dll")] static extern bool OpenClipboard(IntPtr owner);
    [DllImport("user32.dll")] static extern bool CloseClipboard();
    [DllImport("user32.dll")] static extern bool EmptyClipboard();
    [DllImport("user32.dll")] static extern IntPtr GetClipboardData(uint format);
    [DllImport("gdi32.dll")] static extern uint GetEnhMetaFileBits(IntPtr metafile, uint size, byte[] buffer);
    // 다른 프로세스가 잠깐 쥐고 있을 수 있어 몇 번 다시 연다.
    static bool Open() {
        for (int i = 0; i < 20; i++) { if (OpenClipboard(IntPtr.Zero)) return true; Thread.Sleep(50); }
        return false;
    }
    public static bool Clear() {
        if (!Open()) return false;
        try { return EmptyClipboard(); } finally { CloseClipboard(); }
    }
    public static byte[] EnhMetaFileBits() {
        if (!Open()) return null;
        try {
            IntPtr handle = GetClipboardData(CF_ENHMETAFILE);
            if (handle == IntPtr.Zero) return null;
            uint size = GetEnhMetaFileBits(handle, 0, null);
            if (size == 0) return null;
            byte[] bits = new byte[size];
            GetEnhMetaFileBits(handle, size, bits);
            return bits;
        } finally { CloseClipboard(); }
    }
}
"@

$WordExtensions = @('.pdf', '.docx', '.doc', '.rtf')
$ExcelExtensions = @('.xlsx', '.xlsm', '.xls')
$XL_SCREEN = 1         # CopyPicture Appearance — 화면에 보이는 대로
$XL_PICTURE = -4147    # CopyPicture Format — 벡터 그림(EMF)
$MSO_COMMENT = 4       # Shape.Type — 메모는 그림이 아니라 글이다
$MSO_FALSE = 0         # Shape.Visible — 「선택 창」에서 눈을 끈 도형
$XL_SHEET_VISIBLE = -1 # Sheet.Visible — 그 밖(0 숨김 · 2 아주 숨김)이면 시트 위 도형도 숨은 것이다
$SHEET_PICTURE_MAX_ROWS = 200   # 사용 영역이 이보다 크면 한 장에 담긴 글자가 못 읽을 만큼 작아진다 — 값은 상류를 따랐다
$SHEET_PICTURE_MAX_COLS = 40
$WD_COLLAPSE_START = 1          # Range.Collapse — 표가 시작하는 자리로 접는다
$WD_PAGE_NUMBER = 3             # Range.Information — wdActiveEndPageNumber
$MSO_CHART = 3
$MSO_LINKED_PICTURE = 11
$MSO_PICTURE = 13

function Release-Com($Object) {
    if ($null -ne $Object) {
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Object) } catch { }
    }
}

function ConvertTo-PageNumbers([string]$Value, [int]$Count, [string]$Unit = '쪽') {
    if ([string]::IsNullOrWhiteSpace($Value)) { return @(1..$Count) }
    $Numbers = @()
    foreach ($Part in ($Value -split '[,\s]+' | Where-Object { $_ })) {
        if ($Part -notmatch '^\d+$') { throw "Pages는 쉼표나 공백으로 나눈 번호여야 합니다: $Part" }
        $Number = [int]$Part
        if ($Number -lt 1 -or $Number -gt $Count) {
            Write-Warning "$Unit $Number 는 범위 밖이라 건너뜁니다(전체 $Count $Unit)."
            continue
        }
        if ($Numbers -notcontains $Number) { $Numbers += $Number }
    }
    if ($Numbers.Count -eq 0) { throw "선택한 ${Unit}이 문서 범위 안에 없습니다(전체 $Count $Unit)." }
    return $Numbers
}

# 이 스크립트가 띄운 숨은 Office 프로세스만 짚는다 — 사용자가 열어 둔 창은 건드리지 않는다.
function Get-OwnedProcess([long]$Window, [string]$Name, [int[]]$Before) {
    try {
        $Id = [int][DrmOfficeWindow]::ProcessId($Window)
        if (-not $Id -or $Before -contains $Id) { return $null }
        $Candidate = Get-Process -Id $Id -ErrorAction Stop
        if ($Candidate.ProcessName -ne $Name) { return $null }
        return [pscustomobject]@{ Id = $Id; Name = $Name; StartedUtcTicks = $Candidate.StartTime.ToUniversalTime().Ticks }
    } catch { return $null }
}

# 소유 PID와 시작 시각이 모두 같은 숨은 프로세스만 정리한다.
function Stop-OwnedHiddenProcess($Owned) {
    try { [GC]::Collect(); [GC]::WaitForPendingFinalizers() } catch { }
    Start-Sleep -Milliseconds 500
    if (-not $Owned) { return }
    $Process = Get-Process -Id $Owned.Id -ErrorAction SilentlyContinue
    if ($Process -and $Process.ProcessName -eq $Owned.Name -and
        $Process.StartTime.ToUniversalTime().Ticks -eq $Owned.StartedUtcTicks -and
        $Process.MainWindowHandle -eq [IntPtr]::Zero) {
        Stop-Process -Id $Owned.Id -Force -ErrorAction SilentlyContinue
    }
}

function ConvertFrom-MetafileBits([byte[]]$Bits, [int]$TargetWidth) {
    $Memory = New-Object System.IO.MemoryStream(, $Bits)
    try {
        $Meta = New-Object System.Drawing.Imaging.Metafile($Memory)
        try {
            if ($Meta.Width -le 0 -or $Meta.Height -le 0) { throw '페이지 그림의 치수가 비었습니다.' }
            $Height = [int][Math]::Round($TargetWidth * $Meta.Height / $Meta.Width)
            $Bitmap = New-Object System.Drawing.Bitmap($TargetWidth, $Height)
            $Graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
            try {
                $Graphics.Clear([System.Drawing.Color]::White)
                $Graphics.DrawImage($Meta, (New-Object System.Drawing.Rectangle(0, 0, $TargetWidth, $Height)))
            } finally {
                $Graphics.Dispose()
            }
            return $Bitmap
        } finally {
            $Meta.Dispose()
        }
    } finally {
        $Memory.Dispose()
    }
}

function Test-Png([string]$LiteralPath) {
    $Head = New-Object byte[] 8
    $Stream = [IO.File]::OpenRead($LiteralPath)
    try { [void]$Stream.Read($Head, 0, 8) } finally { $Stream.Dispose() }
    return ($Head[0] -eq 0x89 -and $Head[1] -eq 0x50 -and $Head[2] -eq 0x4E -and $Head[3] -eq 0x47)
}

function Get-ShapeKind([int]$Type) {
    if ($Type -eq $MSO_CHART) { return '차트' }
    if ($Type -eq $MSO_PICTURE -or $Type -eq $MSO_LINKED_PICTURE) { return '그림' }
    return '도형'
}

# 시트 탭 차례대로 — 시트째 차트는 그 시트 하나가 한 장이고, 일반 시트는 그 위 도형마다 한 장이다.
# 묶은 도형은 묶음 하나가 한 장이다. 숨긴 것은 복사해도 클립보드가 비므로 따로 표시한다.
function Get-ExcelVisuals($Book) {
    $ChartSheets = @{}
    foreach ($Chart in $Book.Charts) { $ChartSheets[$Chart.Name] = $true }
    foreach ($Sheet in $Book.Sheets) {
        $SheetHidden = $false
        try { $SheetHidden = ([int]$Sheet.Visible -ne $XL_SHEET_VISIBLE) } catch { }
        if ($ChartSheets.ContainsKey($Sheet.Name)) {
            [pscustomobject]@{ Source = $Sheet; Label = "$($Sheet.Name) · 시트째 차트"; Hidden = $SheetHidden }
            continue
        }
        # 시트 사용 영역 한 장 — 셀 배치 · 서식 · 병합을 본다(상류에서 빌렸다 · references/SOURCES.md)
        if (-not $SheetHidden) {
            try {
                $Used = $Sheet.UsedRange
                $Rows = [int]$Used.Rows.Count
                $Cols = [int]$Used.Columns.Count
                if ($Rows -gt $SHEET_PICTURE_MAX_ROWS -or $Cols -gt $SHEET_PICTURE_MAX_COLS) {
                    Write-Warning "시트 $($Sheet.Name) 은 사용 영역이 ${Rows}행 × ${Cols}열이라 그림으로 안 뜬다 — 글자는 read-drm.ps1 이 읽는다."
                } elseif ($Rows * $Cols -gt 1) {
                    $Address = ([string]$Used.Address()).Replace('$', '')
                    [pscustomobject]@{ Source = $Used; Label = "$($Sheet.Name)!$Address · 시트"; Hidden = $false }
                }
            } catch { }
        }
        foreach ($Shape in $Sheet.Shapes) {
            if ($Shape.Type -eq $MSO_COMMENT) { continue }
            $Hidden = $SheetHidden
            try { if ([int]$Shape.Visible -eq $MSO_FALSE) { $Hidden = $true } } catch { }
            [pscustomobject]@{ Source = $Shape; Label = "$($Sheet.Name)!$($Shape.Name) · $(Get-ShapeKind $Shape.Type)"; Hidden = $Hidden }
        }
    }
}

function Save-ExcelVisuals([IO.FileInfo]$File, [string]$Selection, [string]$Out, [int]$TargetWidth) {
    $Before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
    $Excel = $null
    $Book = $null
    $BookSession = $null
    $Owned = $null
    $Made = @()
    $Empty = @()
    try {
        $Excel = New-Object -ComObject Excel.Application
        $Excel.Visible = $false
        $Excel.DisplayAlerts = $false
        try { $Excel.AutomationSecurity = 3 } catch { }
        $Owned = Get-OwnedProcess ([long]$Excel.Hwnd) 'EXCEL' $Before

        # UpdateLinks=0, ReadOnly=true. 저장은 하지 않는다 — 사람이 연 것을 돌려받았으면 닫지도 않는다(office-session.ps1)
        $BookSession = Open-OwnedDocument -Kind 'Excel' -Collection $Excel.Workbooks -Open { $Excel.Workbooks.Open($File.FullName, 0, $true) }
        $Book = $BookSession.Document
        $Items = @(Get-ExcelVisuals $Book)
        if ($Items.Count -lt 1) { throw '통합문서에 그림으로 뜰 시트 · 차트 · 그림 · 도형이 없습니다.' }

        foreach ($Number in (ConvertTo-PageNumbers $Selection $Items.Count '그림')) {
            $Item = $Items[$Number - 1]
            if ($Item.Hidden) {
                Write-Warning "그림 $Number ($($Item.Label)) 은 숨겨져 있어 건너뜁니다 — 숨긴 것은 그림으로 복사되지 않는다."
                continue
            }
            [void][DrmClipboard]::Clear()
            try {
                [void]$Item.Source.CopyPicture($XL_SCREEN, $XL_PICTURE)   # Range 는 값을 돌려준다 — 출력에 섞이면 그림으로 세어진다
            } catch {
                # 양식 컨트롤처럼 그림으로 못 내는 것은 건너뛴다
                Write-Warning "그림 $Number ($($Item.Label)) 을 복사하지 못해 건너뜁니다: $($_.Exception.Message)"
                continue
            }
            $Bits = [DrmClipboard]::EnhMetaFileBits()
            if ($null -eq $Bits) {
                # 한 장이 비었다고 DRM 으로 단정하지 않는다 — 보이는 것이 다 비었을 때만 그렇게 말한다(아래)
                Write-Warning "그림 $Number ($($Item.Label)) — 복사는 됐는데 클립보드에 그림이 없어 건너뜁니다."
                $Empty += $Item.Label
                continue
            }
            $Bitmap = ConvertFrom-MetafileBits $Bits $TargetWidth
            $Target = Join-Path $Out ("item-{0:D3}.png" -f $Number)
            try { $Bitmap.Save($Target, [Drawing.Imaging.ImageFormat]::Png) } finally { $Bitmap.Dispose() }
            if (-not (Test-Png $Target)) { throw "PNG 머리가 아닌 결과가 생겼습니다: $Target" }
            $Made += [pscustomobject]@{ Path = $Target; Label = $Item.Label }
        }
    } finally {
        # 보호 문서의 그림을 클립보드에 남기지 않는다
        try { [void][DrmClipboard]::Clear() } catch { }
        Close-OwnedDocument $BookSession
        [void](Exit-OfficeApp -App $Excel -Kind 'Excel')
        Stop-OwnedHiddenProcess $Owned
    }
    if ($Made.Count -eq 0 -and $Empty.Count -gt 0) {
        throw "보이는 그림 $($Empty.Count)장이 다 복사는 됐는데 클립보드가 비었습니다 — 보호 문서의 복사를 DRM 이 막는 PC 로 보인다."
    }
    if ($Made.Count -eq 0) { throw '그림을 한 장도 못 떴습니다 — 위 경고를 본다.' }
    return $Made
}

$File = Get-Item -LiteralPath $Path
$Ext = $File.Extension.ToLowerInvariant()
if ($Ext -notin ($WordExtensions + $ExcelExtensions)) {
    throw "페이지 캡처를 지원하지 않는 형식입니다: $Ext"
}

if (-not $OutDir) {
    $OutDir = Join-Path ([IO.Path]::GetTempPath()) ("drm-pages\{0}-{1}" -f $File.BaseName, (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
$Out = (New-Item -ItemType Directory -Path $OutDir -Force).FullName

if ($Ext -in $ExcelExtensions) {
    $Visuals = @(Save-ExcelVisuals $File $Pages $Out $Width)
    Write-Output ("그림 {0}장 — {1}" -f $Visuals.Count, $Out)
    $Visuals | ForEach-Object { Write-Output ("{0}  ← {1}" -f $_.Path, $_.Label) }
    return
}

$Before = @(Get-Process WINWORD -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
$Word = $null
$Doc = $null
$DocSession = $null
$Window = $null
$Pane = $null
$Made = @()
$Tables = @()
$Owned = $null
$ClipboardUsed = $false

try {
    $Word = New-Object -ComObject Word.Application
    $Word.Visible = $false
    $Word.DisplayAlerts = 0
    try { $Word.AutomationSecurity = 3 } catch { }

    # ConfirmConversions=false, ReadOnly=true, AddToRecentFiles=false. 저장은 하지 않는다 — 사람이 연 것을
    # 돌려받았으면 닫지도 않는다(office-session.ps1)
    if ($Ext -eq '.pdf') { Assert-WordPdfQuiet $Word }
    $DocSession = Open-OwnedDocument -Kind 'Word' -Collection $Word.Documents -Open { $Word.Documents.Open($File.FullName, $false, $true, $false) }
    $Doc = $DocSession.Document
    if ($Ext -eq '.pdf') { Assert-PdfConverted ([string]$Doc.Range(0, 16).Text) }
    $Doc.Activate()
    $Window = $Doc.ActiveWindow
    $Owned = Get-OwnedProcess ([long]$Window.Hwnd) 'WINWORD' $Before
    if ($Window.View.Type -ne 3) { $Window.View.Type = 3 } # wdPrintView
    $Pane = $Window.Panes.Item(1)
    $Count = [int]$Pane.Pages.Count
    if ($Count -lt 1) { throw 'Word가 문서 페이지를 만들지 못했습니다.' }

    $Selected = @(ConvertTo-PageNumbers $Pages $Count)
    foreach ($Number in $Selected) {
        $Bits = [byte[]]$Pane.Pages.Item($Number).EnhMetaFileBits
        $Bitmap = ConvertFrom-MetafileBits $Bits $Width
        $Target = Join-Path $Out ("page-{0:D3}.png" -f $Number)
        try { $Bitmap.Save($Target, [Drawing.Imaging.ImageFormat]::Png) } finally { $Bitmap.Dispose() }
        if (-not (Test-Png $Target)) { throw "PNG 머리가 아닌 결과가 생겼습니다: $Target" }
        $Made += $Target
    }

    # 표 한 장씩 — 쪽 그림보다 크게 본다(상류에서 빌렸다 · references/SOURCES.md). 표는 EnhMetaFileBits 가
    # 없어 클립보드로 받는다. -Pages 를 주면 그 쪽에서 시작하는 표만 뜬다
    $TableCount = [int]$Doc.Tables.Count
    for ($Index = 1; $Index -le $TableCount; $Index++) {
        $Table = $Doc.Tables.Item($Index)
        try {
            if ($Pages) {
                $Start = $Table.Range.Duplicate
                $Start.Collapse($WD_COLLAPSE_START)
                if ($Selected -notcontains [int]$Start.Information($WD_PAGE_NUMBER)) { continue }
            }
            $ClipboardUsed = $true
            [void][DrmClipboard]::Clear()
            [void]$Table.Range.CopyAsPicture()
            $Bits = [DrmClipboard]::EnhMetaFileBits()
            if ($null -eq $Bits) { Write-Warning "표 $Index — 복사는 됐는데 클립보드에 그림이 없어 건너뜁니다."; continue }
            $Bitmap = ConvertFrom-MetafileBits $Bits $Width
            $Target = Join-Path $Out ("table-{0:D2}.png" -f $Index)
            try { $Bitmap.Save($Target, [Drawing.Imaging.ImageFormat]::Png) } finally { $Bitmap.Dispose() }
            if (-not (Test-Png $Target)) { throw "PNG 머리가 아닌 결과가 생겼습니다: $Target" }
            $Tables += $Target
        } catch {
            Write-Warning "표 $Index 를 그림으로 못 떠 건너뜁니다: $($_.Exception.Message)"
        } finally {
            Release-Com $Table
        }
    }
} finally {
    # 보호 문서의 그림을 클립보드에 남기지 않는다
    if ($ClipboardUsed) { try { [void][DrmClipboard]::Clear() } catch { } }
    Release-Com $Pane
    Release-Com $Window
    Close-OwnedDocument $DocSession
    [void](Exit-OfficeApp -App $Word -Kind 'Word')
    Stop-OwnedHiddenProcess $Owned
}

if ($Tables.Count) {
    Write-Output ("페이지 {0}장 · 표 {1}장 — {2}" -f $Made.Count, $Tables.Count, $Out)
} else {
    Write-Output ("페이지 {0}장 — {1}" -f $Made.Count, $Out)
}
$Made + $Tables | ForEach-Object { Write-Output $_ }
