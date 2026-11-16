<#
.SYNOPSIS
    DRM 환경에서 Word 문서와 PDF의 페이지를, 엑셀 통합문서의 차트·그림·도형을 그림(줄인 WebP)으로 꺼낸다.

.DESCRIPTION
    Word가 화면에 그린 페이지의 EnhMetaFileBits를 메모리에서 받아 PowerShell이 PNG로 쓰고, 씨앗의 줄이는 손으로 줄여 WebP로 낸다
    (-Width 는 그리는 폭, -MaxEdge 는 줄인 뒤의 긴 변 — 못 줄이면 PNG 그대로 나간다).
    Office의 내보내기/다른 이름으로 저장을 쓰지 않으므로 원본을 저장하거나 DRM을 해제하지 않는다.
    read-drm.ps1의 Document.Content.Text가 이미지·도형·머리글 또는 공간 배치를 놓칠 때 쓴다.

    엑셀에는 EnhMetaFileBits 같은 메모리 통로가 없다. 그림을 꺼내는 길은 파일 내보내기
    (Chart.Export)와 클립보드 복사(CopyPicture)뿐인데, DRM 필터는 Office가 디스크에 쓰는
    산출물을 가로챈다(capture_slides.ps1 머리말). 그래서 클립보드에 벡터 그림(EMF)으로 받아
    Word와 같은 변환으로 PNG를 쓴다. 시트 탭 차례대로 시트째 차트, 시트 사용 영역, 시트 위 도형마다
    한 장이다. Word 의 표도 같은 길로 한 장씩 뜬다(table-NN.w<폭>.webp — 남기지 않는 판은 table-NN.webp).
    클립보드를 쓰므로 하던 복사는 사라지고, 끝나면 보호 문서의 그림을 남기지 않게 비운다.

    -Pictures 는 문서 안의 그림만 하나씩 뜬다 — 쪽 · 장 전체의 그림에서는 사진이 작고 흐려서다. 덱(.pptx · .ppt)은 장마다의
    그림 도형을(창 없이 열어 슬라이드쇼가 없다), 워드는 그림을, 엑셀은 차트 · 그림만 뜨고, 줄여서 WebP 로 낸다. -Pages 는
    덱에서는 장 번호다. 도형으로 그린 도식과 그림 둘레의 글은 안 담긴다 — 그것은 쪽 · 장 전체의 그림이 든다. PDF 는 안 받는다.

    뜬 그림은 남긴다 — 남긴 글자 곁의 폴더에 두고, 같은 파일을 같은 부름(-Pages · -Width)으로 다시 부르면
    앱을 안 띄우고 그 그림으로 답한다(아래 「남긴 그림」). -OutDir 를 주면 그 폴더에도 한 벌 놓아 그 경로를
    낸다. -NoKeep 은 남기지도 남긴 것을 쓰지도 않고 -OutDir(없으면 임시 폴더 아래 drm-pages)에만 뜬다 — 같은 부름으로
    앞서 남긴 기록은 걷으니, 잘못 떠서 남은 그림은 -NoKeep 한 판으로 물린다.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File capture_pages.ps1 -Path report.pdf
    powershell -NoProfile -ExecutionPolicy Bypass -File capture_pages.ps1 -Path report.docx -Pages "1,3"
    powershell -NoProfile -ExecutionPolicy Bypass -File capture_pages.ps1 -Path sales.xlsx -Pages "2"
    powershell -NoProfile -ExecutionPolicy Bypass -File capture_pages.ps1 -Path deck.pptx -Pictures -Pages "3,5"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Pages,
    [string]$OutDir,
    [ValidateRange(400, 4000)][int]$Width = 1600,
    # 줄인 뒤 긴 변 픽셀 — 안 주면 줄이는 손의 기본 눈금이다. 그림의 값은 치수가 정하므로 작은 글자를 더 크게 봐야 할 때만 올린다
    [ValidateRange(0, 4000)][int]$MaxEdge = 0,
    # 문서 안의 그림만 하나씩 뜬다(쪽 · 표 · 시트 사용 영역은 안 뜬다) — 덱(.pptx · .ppt)은 이 값일 때만 받는다
    [switch]$Pictures,
    # 뜬 그림을 남기지도, 남긴 그림을 쓰지도 않는다 — 전처럼 -OutDir(없으면 임시 폴더)에만 뜬다
    [switch]$NoKeep
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'office-session.ps1')
. (Join-Path $PSScriptRoot 'office-read.ps1')      # 띄우기 · 끝내기 · 남긴 자리와 지문 · 그림 줄이기
# 낸 경고를 모아 둔다 — 남긴 그림으로 답할 때 그 판의 경고(숨겨져 건너뛴 그림 · 그림으로 안 뜬 시트)를 다시 내야 빠진 것이 보인다.
# 같은 이름의 함수가 cmdlet 보다 먼저 잡혀, 이 스크립트와 실은 부품의 경고가 다 여기를 지난다
$Warned = New-Object System.Collections.Generic.List[string]
function Write-Warning([string]$Message) { $Warned.Add($Message); Microsoft.PowerShell.Utility\Write-Warning $Message }
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing @"
using System;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
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
    const uint CF_BITMAP = 2;
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern uint RegisterClipboardFormat(string name);
    [DllImport("kernel32.dll")] static extern IntPtr GlobalLock(IntPtr memory);
    [DllImport("kernel32.dll")] static extern bool GlobalUnlock(IntPtr memory);
    [DllImport("kernel32.dll")] static extern UIntPtr GlobalSize(IntPtr memory);
    // 그림 도형을 복사한 뒤의 클립보드 그림 — PNG(오피스가 올리는 등록 형식) 먼저, 없거나 못 풀면 비트맵. 둘 다 없으면 null 이고
    // 부르는 쪽이 메타파일로 간다. 형식 하나를 못 풀어도 다음 형식으로 간다 — 감긴 문서의 PNG 를 못 푸는 PC 가 있다(상류의 난간)
    public static Bitmap Picture() {
        if (!Open()) return null;
        try {
            try {
                IntPtr memory = GetClipboardData(RegisterClipboardFormat("PNG"));
                int size = memory == IntPtr.Zero ? 0 : (int)GlobalSize(memory).ToUInt64();
                IntPtr at = size > 0 ? GlobalLock(memory) : IntPtr.Zero;
                if (at != IntPtr.Zero) {
                    try {
                        byte[] bytes = new byte[size];
                        Marshal.Copy(at, bytes, 0, size);
                        using (MemoryStream stream = new MemoryStream(bytes))
                        using (Bitmap read = new Bitmap(stream)) return new Bitmap(read);
                    } finally { GlobalUnlock(memory); }
                }
            } catch { }
            try {
                IntPtr handle = GetClipboardData(CF_BITMAP);
                if (handle != IntPtr.Zero) return Image.FromHbitmap(handle);
            } catch { }
            return null;
        } finally { CloseClipboard(); }
    }
}
"@

$WordExtensions = @('.pdf', '.docx', '.doc', '.rtf')
$ExcelExtensions = @('.xlsx', '.xlsm', '.xls')
$DeckExtensions = @('.pptx', '.ppt')   # 그림만 뜰 때만 받는다 — 장 전체는 capture_slides.ps1 이 찍는다
$MSO_GROUP = 6
$MSO_PLACEHOLDER = 14
$PICTURE_KINDS = @('차트', '그림')     # 엑셀에서 「그림만」이 뜨는 딱지
$PICTURE_MISS_MAX = 2   # 그림 복사가 잇달아 이만큼 지면 그 문서에서는 더 안 뜬다 — 복사가 막힌 PC 에서 그림마다 헛돈다(값은 상류를 따랐다)
$CLIPBOARD_TRIES = 5    # 복사 뒤 클립보드에서 그림을 읽어 보는 횟수 — 오피스가 그림을 늦게 올릴 때가 있다
$CLIPBOARD_WAIT_MS = 200
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
    # 고름을 번호로 푸는 것은 읽는 부품이 든다 — 번호가 아닌 낱말이면 거기서 그 낱말을 대며 던지고, 겹친 번호는 한 번만 온다
    foreach ($Number in @(ConvertTo-NumberList -Value $Value -Name 'Pages')) {
        if ($Number -lt 1 -or $Number -gt $Count) {
            Write-Warning "$Unit $Number 는 범위 밖이라 건너뜁니다(전체 $Count $Unit)."
            continue
        }
        $Numbers += $Number
    }
    if ($Numbers.Count -eq 0) { throw "선택한 ${Unit}이 문서 범위 안에 없습니다(전체 $Count $Unit)." }
    return $Numbers
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

# 뜬 비트맵을 PNG 로 쓰고 그 경로를 낸다. 받은 비트맵은 여기서 놓는다. 줄이기는 여기서 안 한다 — 줄이는 손은 프로세스를 띄우므로
# 앱을 다 끝낸 뒤 Complete-Shots 가 뜬 것 전부를 한 번에 줄인다
function Save-Shot($Bitmap, [string]$Target) {
    try { $Bitmap.Save($Target, [Drawing.Imaging.ImageFormat]::Png) } finally { $Bitmap.Dispose() }
    if (-not (Test-Png $Target)) { throw "PNG 머리가 아닌 결과가 생겼습니다: $Target" }
    return $Target
}

# ── 그림만 — 문서 안의 그림 도형을 하나씩 복사시켜 클립보드에서 받는다(-Pictures) ──────────────────────────
# 쪽 · 장 전체를 뜬 그림에서는 사진이 작고 흐리다. 그림 도형만 복사하면 화면에 보이는 크기 그대로 온다. 뜬 그림은 다른 갈래와 같이
# 끝에서 줄인다(Complete-Shots). 상류 office-com-read 의
# 「-What Pictures」 에서 빌렸다(references/SOURCES.md) — 덱은 Shape.Copy, 워드는 그림을 고른 뒤 Selection.CopyAsPicture 다
# (Range.CopyAsPicture 는 그림에서 클립보드를 비워 둔다).

# 그림 하나를 복사시켜($Copy) 뜬다 → 뜬 PNG 의 경로. 못 뜬 그림은 어느 걸음에서 졌나를 경고로 내고 $null 이다.
# 클립보드를 못 비우면 복사로 치지 않는다 — 안 비운 채 복사가 조용히 막히면 앞 그림이 이 이름으로 남는다(상류의 난간)
function Save-CopiedPicture([scriptblock]$Copy, [string]$Target, [string]$Label) {
    if (-not [DrmClipboard]::Clear()) { Write-Warning "$Label — 클립보드를 못 비워 건너뜁니다."; return $null }
    try { [void](& $Copy) } catch { Write-Warning "$Label — 복사하지 못해 건너뜁니다: $($_.Exception.Message)"; return $null }
    $Bitmap = $null
    for ($Try = 0; $Try -lt $CLIPBOARD_TRIES -and $null -eq $Bitmap; $Try++) {
        if ($Try) { Start-Sleep -Milliseconds $CLIPBOARD_WAIT_MS }
        $Bitmap = [DrmClipboard]::Picture()
        if ($null -eq $Bitmap) {
            $Bits = [DrmClipboard]::EnhMetaFileBits()
            if ($null -ne $Bits) { $Bitmap = ConvertFrom-MetafileBits $Bits $Width }
        }
    }
    if ($null -eq $Bitmap) { Write-Warning "$Label — 복사는 됐는데 클립보드에 읽을 그림이 없어 건너뜁니다."; return $null }
    return (Save-Shot $Bitmap $Target)
}

# 그림 도형 · 연결된 그림 · 그림이 든 개체 틀 · 묶음 안의 그림까지. 도형 하나를 읽다 져도 나머지는 낸다
function Get-PictureShapes($Shapes) {
    foreach ($Shape in @($Shapes)) {
        try {
            $Type = [int]$Shape.Type
            if ($Type -eq $MSO_PICTURE -or $Type -eq $MSO_LINKED_PICTURE) { $Shape; continue }
            if ($Type -eq $MSO_PLACEHOLDER) {
                $Held = 0
                try { $Held = [int]$Shape.PlaceholderFormat.ContainedType } catch { }
                if ($Held -eq $MSO_PICTURE -or $Held -eq $MSO_LINKED_PICTURE) { $Shape; continue }
            }
            if ($Type -eq $MSO_GROUP) { Get-PictureShapes $Shape.GroupItems }
        } catch {
            Write-Warning "도형 하나를 읽지 못해 건너뜁니다: $($_.Exception.Message)"
        }
    }
}

# 덱의 장마다 그림 도형을 하나씩 뜬다 → @{ Path; Label } 들. 창 없이 열어 슬라이드쇼가 없다 — 화면을 안 가져간다
function Save-DeckPictures([IO.FileInfo]$File, [string]$Selection, [string]$Out) {
    $Ppt = $null
    $Session = $null
    $Made = @()
    $Misses = 0
    try {
        $Ppt = New-OfficeApp -AppName 'PPT' -SpawnedPids ([ref]$spawnedPids) -Job $officeJob
        # 경로 · ReadOnly=$true · Untitled=$false · WithWindow=$false
        $Session = Open-OwnedDocument -Kind 'PPT' -Collection $Ppt.Presentations -Open { $Ppt.Presentations.Open($File.FullName, $true, $false, $false) }
        $Deck = $Session.Document
        $Count = [int]$Deck.Slides.Count
        if ($Count -lt 1) { throw '덱에 슬라이드가 없습니다.' }
        :Slides foreach ($Number in (ConvertTo-PageNumbers $Selection $Count '슬라이드')) {
            $Index = 0
            foreach ($Picture in @(Get-PictureShapes $Deck.Slides.Item($Number).Shapes)) {
                $Index++
                $Name = ''
                try { $Name = [string]$Picture.Name } catch { }
                $Label = "슬라이드 $Number · $Name"
                $Target = Join-Path $Out ("slide-{0:D3}-pic-{1:D2}{2}.png" -f $Number, $Index, $Tag)
                $Saved = Save-CopiedPicture { $Picture.Copy() } $Target $Label
                if ($Saved) {
                    $Misses = 0
                    $Made += [pscustomobject]@{ Path = $Saved; Label = $Label }
                } elseif (++$Misses -ge $PICTURE_MISS_MAX) {
                    Write-Warning "그림 복사가 잇달아 $PICTURE_MISS_MAX 번 져 슬라이드 $Number 뒤로는 더 뜨지 않습니다 — 같은 명령을 다시 부르지 말고 장 전체를 capture_slides.ps1 로 찍습니다."
                    break Slides
                }
            }
        }
    } finally {
        try { [void][DrmClipboard]::Clear() } catch { }
        Close-OwnedDocument $Session
        Close-OfficeApps -AppByName @{ PPT = $Ppt } -SpawnedPids $spawnedPids -Job $officeJob -PptWasRunning $PptWasRunning
    }
    if ($Made.Count -eq 0) { throw '그림을 한 장도 못 떴습니다 — 고른 장에 그림 도형이 없거나, 위 경고대로 복사가 막혔습니다.' }
    return $Made
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
            [pscustomobject]@{ Source = $Sheet; Label = "$($Sheet.Name) · 시트째 차트"; Kind = '차트'; Hidden = $SheetHidden }
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
                    [pscustomobject]@{ Source = $Used; Label = "$($Sheet.Name)!$Address · 시트"; Kind = '시트'; Hidden = $false }
                }
            } catch { }
        }
        foreach ($Shape in $Sheet.Shapes) {
            if ($Shape.Type -eq $MSO_COMMENT) { continue }
            $Hidden = $SheetHidden
            try { if ([int]$Shape.Visible -eq $MSO_FALSE) { $Hidden = $true } } catch { }
            $Kind = Get-ShapeKind $Shape.Type
            [pscustomobject]@{ Source = $Shape; Label = "$($Sheet.Name)!$($Shape.Name) · $Kind"; Kind = $Kind; Hidden = $Hidden }
        }
    }
}

function Save-ExcelVisuals([IO.FileInfo]$File, [string]$Selection, [string]$Out, [int]$TargetWidth) {
    $Excel = $null
    $Book = $null
    $BookSession = $null
    $Made = @()
    $Empty = @()
    try {
        $Excel = New-OfficeApp -AppName 'Excel' -SpawnedPids ([ref]$spawnedPids) -Job $officeJob

        # UpdateLinks=0, ReadOnly=true. 저장은 하지 않는다 — 사람이 연 것을 돌려받았으면 닫지도 않는다(office-session.ps1)
        $BookSession = Open-OwnedDocument -Kind 'Excel' -Collection $Excel.Workbooks -Open { $Excel.Workbooks.Open($File.FullName, 0, $true) }
        $Book = $BookSession.Document
        $Items = @(Get-ExcelVisuals $Book)
        if ($Items.Count -lt 1) { throw '통합문서에 그림으로 뜰 시트 · 차트 · 그림 · 도형이 없습니다.' }

        foreach ($Number in (ConvertTo-PageNumbers $Selection $Items.Count '그림')) {
            $Item = $Items[$Number - 1]
            if ($Pictures -and $PICTURE_KINDS -notcontains $Item.Kind) { continue }   # 번호는 전체 차례 그대로 둔다 — 갈래가 달라도 같은 그림은 같은 번호다
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
            $Target = Join-Path $Out ("item-{0:D3}{1}.png" -f $Number, $Tag)
            $Made += [pscustomobject]@{ Path = (Save-Shot $Bitmap $Target); Label = $Item.Label }
        }
    } finally {
        # 보호 문서의 그림을 클립보드에 남기지 않는다
        try { [void][DrmClipboard]::Clear() } catch { }
        Close-OwnedDocument $BookSession
        Close-OfficeApps -AppByName @{ Excel = $Excel } -SpawnedPids $spawnedPids -Job $officeJob
    }
    if ($Made.Count -eq 0 -and $Empty.Count -gt 0) {
        throw "보이는 그림 $($Empty.Count)장이 다 복사는 됐는데 클립보드가 비었습니다 — 보호 문서의 복사를 DRM 이 막는 PC 로 보인다."
    }
    if ($Made.Count -eq 0 -and $Pictures) { throw '통합문서에 뜰 차트 · 그림이 없습니다(고른 번호 안에) — -Pictures 없이 부르면 시트 사용 영역과 도형까지 뜹니다.' }
    if ($Made.Count -eq 0) { throw '그림을 한 장도 못 떴습니다 — 위 경고를 본다.' }
    return $Made
}

$File = Get-Item -LiteralPath $Path
$Ext = $File.Extension.ToLowerInvariant()
if ($Ext -in $DeckExtensions -and -not $Pictures) {
    throw '덱의 장 전체는 capture_slides.ps1 로 찍습니다 — 이 스크립트는 -Pictures(장 안의 그림만)일 때만 덱을 받습니다.'
}
if ($Ext -eq '.pdf' -and $Pictures) {
    throw 'PDF 는 그림만 뜨는 길이 없습니다 — -Pictures 없이 쪽 그림으로 뜹니다.'
}
if ($Ext -notin ($WordExtensions + $ExcelExtensions + $DeckExtensions)) {
    throw "페이지 캡처를 지원하지 않는 형식입니다: $Ext"
}

# ── 남긴 그림 — 같은 바이트의 문서를 같은 부름(쪽 고름 · 폭)으로 앞서 떴으면 앱을 안 띄우고 그 그림으로 답한다 ──────────
# 그림은 남긴 글자 곁의 폴더(office-read.ps1 의 Get-KeptShotDir)에 폭을 이름에 달아 남기고, 끝까지 선 부름마다 기록 한 장
# 「shots-<갈래><쪽 고름>.w<폭>.txt」 을 둔다(갈래는 -Pictures 일 때 pic- · -MaxEdge 를 줬으면 .e<긴 변> 이 더 붙는다) — 첫 줄이 요약, 그 뒤가 그림 이름(탭 뒤에 딱지)과 SHOT_WARNING 으로 시작하는 그 판의 경고다.
# 낱장이 아니라 부름(갈래 · 쪽 고름 · 폭 · 준 긴 변)으로 가린다 — 쪽을 안 고른 부름은 문서를 열어야 몇 쪽인지 알고, 표와 엑셀 그림의 딱지도 열어야 나온다.
# 지문이 바이트를 재므로 문서가 바뀌면 폴더가 달라 새로 뜬다.
$SHOT_WARNING = '!'
$KeepDir = $null
$Record = $null
$Tag = ''                              # 남기는 그림의 이름에 다는 폭(과 준 긴 변) — 치수가 다른 부름의 그림과 안 겹친다
if (-not $Pages -or $Pages -match '^[\d,\s]+$') {   # 번호가 아닌 쪽 고름은 아래에서 까닭을 대며 멈춘다
    try {
        $KeepDir = Get-KeptShotDir -Name $File.Name -Print (Get-KeptPrint -LiteralPath $File.FullName)
        $Picked = ("$Pages" -replace '\D+', '_').Trim('_')
        if (-not $Picked) { $Picked = 'all' }
        $Tag = ".w$Width" + $(if ($MaxEdge) { ".e$MaxEdge" } else { '' })
        $Record = Join-Path $KeepDir ("shots-{0}{1}{2}.txt" -f $(if ($Pictures) { 'pic-' } else { '' }), $Picked, $Tag)
        if ($NoKeep) {
            # 다시 뜨는 판 — 이 부름의 기록을 걷고 남기지 않는다. 안 걷으면 잘못 떠서 남은 그림이 다음 부름에 다시 답으로 나온다
            if (Test-Path -LiteralPath $Record) { Remove-Item -LiteralPath $Record -Force }
            $KeepDir = $null; $Record = $null; $Tag = ''
        } else {
            [void](New-Item -ItemType Directory -Path $KeepDir -Force)
        }
    } catch {
        if ($NoKeep) {
            Write-Warning "앞서 남긴 기록을 못 걷었다($($_.Exception.Message)) — 다음 부름이 그 그림으로 답할 수 있다"
        } else {
            Write-Warning "남길 자리를 못 지었다($($_.Exception.Message)) — 이번에는 남기지 않고 뜬다"
        }
        $KeepDir = $null; $Record = $null; $Tag = ''
        $Warned.Clear()
    }
}

# 뜬 것을 낸다 — 요약 한 줄 뒤 그림마다 한 줄(딱지가 있으면 「경로  ← 딱지」). 남긴 자리에서 떴고 -OutDir 를 받았으면 그 폴더로
# 베껴 그 경로를 낸다
function Write-Shots([string]$Summary, $Shots, [string]$From) {
    $Where = $From
    if ($KeepDir -and $OutDir) {
        $Where = (New-Item -ItemType Directory -Path $OutDir -Force).FullName
        foreach ($Shot in $Shots) { Copy-Item -LiteralPath (Join-Path $From $Shot.Name) -Destination (Join-Path $Where $Shot.Name) -Force }
    }
    Write-Output ("{0} — {1}" -f $Summary, $Where)
    foreach ($Shot in $Shots) {
        $Full = Join-Path $Where $Shot.Name
        if ($Shot.Label) { Write-Output ("{0}  ← {1}" -f $Full, $Shot.Label) } else { Write-Output $Full }
    }
}

# 끝까지 선 부름을 기록한다 — 못 적어도 뜬 그림은 낸다(다음에 한 번 더 뜰 뿐이다)
function Save-ShotRecord([string]$Summary, $Shots) {
    if (-not $Record) { return }
    # 줄이기가 져서 PNG 로 나간 그림이 있으면 기록하지 않는다 — 다음에 다시 떠서 줄이기를 한 번 더 해 본다(capture_slides.ps1 과 같은 가름)
    if (@($Shots | Where-Object { $_.Name -notlike '*.webp' }).Count) { return }
    try {
        $Lines = @($Summary)
        $Lines += @($Shots | ForEach-Object { if ($_.Label) { "{0}`t{1}" -f $_.Name, $_.Label } else { $_.Name } })
        $Lines += @($Warned | ForEach-Object { $SHOT_WARNING + ($_ -replace '\s*[\r\n]+\s*', ' ') })
        [IO.File]::WriteAllLines($Record, [string[]]$Lines, (New-Object System.Text.UTF8Encoding($false)))
    } catch {
        Microsoft.PowerShell.Utility\Write-Warning "뜬 것의 기록을 못 남겼다($($_.Exception.Message)) — 다음에 한 번 더 뜬다"
    }
}

if ($Record -and (Test-Path -LiteralPath $Record)) {
    $Lines = @()
    try { $Lines = @([IO.File]::ReadAllLines($Record, [Text.Encoding]::UTF8)) } catch { }
    $Shots = @($Lines | Select-Object -Skip 1 | Where-Object { $_ -and -not $_.StartsWith($SHOT_WARNING) } | ForEach-Object {
        $Name, $Label = $_ -split "`t", 2
        [pscustomobject]@{ Name = $Name; Label = $Label }
    })
    $Gone = @($Shots | Where-Object { $_.Name -notlike '*.webp' -or -not (Test-Path -LiteralPath (Join-Path $KeepDir $_.Name)) })
    if ($Shots.Count -gt 0 -and $Gone.Count -eq 0) {
        Write-Output "[남긴 그림] $($File.Name) — 같은 파일을 같은 부름으로 앞서 떠 앱을 안 띄웠다(다시 뜨려면 -NoKeep)"
        $Lines | Where-Object { $_.StartsWith($SHOT_WARNING) } | ForEach-Object {
            Microsoft.PowerShell.Utility\Write-Warning ("앞서 뜰 때 — " + $_.Substring($SHOT_WARNING.Length))
        }
        Write-Shots $Lines[0] $Shots $KeepDir
        return
    }
}

if ($KeepDir) {
    $Out = $KeepDir
} else {
    if (-not $OutDir) {
        $OutDir = Join-Path ([IO.Path]::GetTempPath()) ("drm-pages\{0}-{1}" -f $File.BaseName, (Get-Date -Format 'yyyyMMdd-HHmmss'))
    }
    $Out = (New-Item -ItemType Directory -Path $OutDir -Force).FullName
}

# 뜬 것(@{ Path = PNG; Label })을 한 번에 줄이고 · 기록하고 · 낸다 — 앱을 다 끝낸 뒤 부른다. 줄이는 손은 읽는 부품의
# Convert-ShotsToWebp 가 한 번 띄운다. 못 줄인 그림은 PNG 로 나가고, 그런 그림이 있는 부름은 기록하지 않는다(Save-ShotRecord)
function Complete-Shots([string]$Summary, $Visuals) {
    $converted = Convert-ShotsToWebp -Png @($Visuals | ForEach-Object { $_.Path }) -MaxEdge $MaxEdge
    $Shots = @($Visuals | ForEach-Object { [pscustomobject]@{ Name = (Split-Path -Leaf $converted[$_.Path]); Label = $_.Label } })
    Save-ShotRecord $Summary $Shots
    Write-Shots $Summary $Shots $Out
}

# 띄우기와 끝내기는 읽는 부품이 든다(New-OfficeApp · Close-OfficeApps) — 띄운 앱은 Job 에 묶여 이 스크립트가 끊겨도 함께 끝나고,
# 뜨는 사이 사람이 연 문서가 남았으면 그 앱을 살려 둔다. 파워포인트는 하나만 떠서, 붙은 자리가 사람이 쓰던 앱인지 New-OfficeApp 이
# $PptWasRunning 에 적는다
$PptWasRunning = $false
$spawnedPids = @{}                     # 이 판이 띄운 PID → 앱 이름
$officeJob = New-OfficeJob

if ($Ext -in $DeckExtensions) {
    $Visuals = @(Save-DeckPictures $File $Pages $Out)
    Complete-Shots ("그림 {0}장" -f $Visuals.Count) $Visuals
    return
}

if ($Ext -in $ExcelExtensions) {
    $Visuals = @(Save-ExcelVisuals $File $Pages $Out $Width)
    Complete-Shots ("그림 {0}장" -f $Visuals.Count) $Visuals
    return
}

$Word = $null
$Doc = $null
$DocSession = $null
$Window = $null
$Pane = $null
$Made = @()
$Tables = @()
$ClipboardUsed = $false
$Shown = @()                           # -Pictures 로 뜬 그림 — @{ Path; Label }

try {
    $Word = New-OfficeApp -AppName 'Word' -SpawnedPids ([ref]$spawnedPids) -Job $officeJob

    # ConfirmConversions=false, ReadOnly=true, AddToRecentFiles=false. 저장은 하지 않는다 — 사람이 연 것을
    # 돌려받았으면 닫지도 않는다(office-session.ps1)
    if ($Ext -eq '.pdf') { Assert-WordPdfQuiet $Word }
    $DocSession = Open-OwnedDocument -Kind 'Word' -Collection $Word.Documents -Open { $Word.Documents.Open($File.FullName, $false, $true, $false) }
    $Doc = $DocSession.Document
    if ($Ext -eq '.pdf') { Assert-PdfConverted ([string]$Doc.Range(0, 16).Text) }
    $Doc.Activate()
    $Window = $Doc.ActiveWindow
    if ($Window.View.Type -ne 3) { $Window.View.Type = 3 } # wdPrintView
    $Pane = $Window.Panes.Item(1)
    $Count = [int]$Pane.Pages.Count
    if ($Count -lt 1) { throw 'Word가 문서 페이지를 만들지 못했습니다.' }

    $Selected = @(ConvertTo-PageNumbers $Pages $Count)
    if ($Pictures) {
        # 그림을 고르는(Select) 길이라 선택이 옮겨 간다 — 사람이 열어 둔 문서를 돌려받았으면 뜨지 않는다
        if (-not $DocSession.Owned) { throw '이 문서는 사람이 워드로 열어 두었습니다 — 그림만 뜨려면 문서 안의 선택을 옮겨야 해서 뜨지 않습니다. -Pictures 없이 쪽 그림으로 뜹니다.' }
        $Sources = @($Doc.InlineShapes | ForEach-Object { [pscustomobject]@{ Shape = $_; Place = $_.Range } })
        $Sources += @($Doc.Shapes | Where-Object { @($MSO_PICTURE, $MSO_LINKED_PICTURE) -contains [int]$_.Type } |
            ForEach-Object { [pscustomobject]@{ Shape = $_; Place = $_.Anchor } })
        $Index = 0
        $Misses = 0
        foreach ($Source in $Sources) {
            $Index++
            $Page = 0
            try { $Page = [int]$Source.Place.Information($WD_PAGE_NUMBER) } catch { }
            if ($Pages -and $Selected -notcontains $Page) { continue }
            $Label = "쪽 $Page · 그림 $Index"
            $Target = Join-Path $Out ("picture-{0:D2}{1}.png" -f $Index, $Tag)
            $Shape = $Source.Shape
            $ClipboardUsed = $true
            $Saved = Save-CopiedPicture { $Shape.Select(); $Word.Selection.CopyAsPicture() } $Target $Label
            if ($Saved) {
                $Misses = 0
                $Shown += [pscustomobject]@{ Path = $Saved; Label = $Label }
            } elseif (++$Misses -ge $PICTURE_MISS_MAX) {
                Write-Warning "그림 복사가 잇달아 $PICTURE_MISS_MAX 번 져 그림 $Index 뒤로는 더 뜨지 않습니다 — 같은 명령을 다시 부르지 말고 -Pictures 없이 쪽 그림으로 뜹니다."
                break
            }
        }
        if ($Shown.Count -eq 0) { throw '그림을 한 장도 못 떴습니다 — 문서(고른 쪽)에 그림이 없거나, 위 경고대로 복사가 막혔습니다.' }
    }
    foreach ($Number in $(if ($Pictures) { @() } else { $Selected })) {
        $Bits = [byte[]]$Pane.Pages.Item($Number).EnhMetaFileBits
        $Bitmap = ConvertFrom-MetafileBits $Bits $Width
        $Target = Join-Path $Out ("page-{0:D3}{1}.png" -f $Number, $Tag)
        $Made += (Save-Shot $Bitmap $Target)
    }

    # 표 한 장씩 — 쪽 그림보다 크게 본다(상류에서 빌렸다 · references/SOURCES.md). 표는 EnhMetaFileBits 가
    # 없어 클립보드로 받는다. -Pages 를 주면 그 쪽에서 시작하는 표만 뜬다
    $TableCount = if ($Pictures) { 0 } else { [int]$Doc.Tables.Count }
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
            $Target = Join-Path $Out ("table-{0:D2}{1}.png" -f $Index, $Tag)
            $Tables += (Save-Shot $Bitmap $Target)
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
    Close-OfficeApps -AppByName @{ Word = $Word } -SpawnedPids $spawnedPids -Job $officeJob
}

$Visuals = @(@($Made) + @($Tables) | ForEach-Object { [pscustomobject]@{ Path = $_; Label = $null } }) + @($Shown)
$Summary = if ($Pictures) { "그림 {0}장" -f $Shown.Count } elseif ($Tables.Count) { "페이지 {0}장 · 표 {1}장" -f $Made.Count, $Tables.Count } else { "페이지 {0}장" -f $Made.Count }
Complete-Shots $Summary $Visuals
