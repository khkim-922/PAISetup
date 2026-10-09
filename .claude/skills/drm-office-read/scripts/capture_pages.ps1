<#
.SYNOPSIS
    DRM 환경에서 Word 문서와 PDF의 페이지를 PNG로 꺼낸다.

.DESCRIPTION
    Word가 화면에 그린 페이지의 EnhMetaFileBits를 메모리에서 받아 PowerShell이 PNG로 쓴다.
    Office의 내보내기/다른 이름으로 저장을 쓰지 않으므로 원본을 저장하거나 DRM을 해제하지 않는다.
    read-drm.ps1의 Document.Content.Text가 이미지·도형·머리글 또는 공간 배치를 놓칠 때 쓴다.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File capture_pages.ps1 -Path report.pdf
    powershell -NoProfile -ExecutionPolicy Bypass -File capture_pages.ps1 -Path report.docx -Pages "1,3"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Pages,
    [string]$OutDir,
    [ValidateRange(400, 4000)][int]$Width = 1600
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class DrmWordWindow {
    [DllImport("user32.dll")]
    static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
    public static uint ProcessId(long window) {
        uint processId;
        GetWindowThreadProcessId(new IntPtr(window), out processId);
        return processId;
    }
}
"@

function Release-Com($Object) {
    if ($null -ne $Object) {
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Object) } catch { }
    }
}

function ConvertTo-PageNumbers([string]$Value, [int]$Count) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return @(1..$Count) }
    $Numbers = @()
    foreach ($Part in ($Value -split '[,\s]+' | Where-Object { $_ })) {
        if ($Part -notmatch '^\d+$') { throw "Pages는 쉼표나 공백으로 나눈 번호여야 합니다: $Part" }
        $Number = [int]$Part
        if ($Number -lt 1 -or $Number -gt $Count) {
            Write-Warning "쪽 $Number 는 범위 밖이라 건너뜁니다(전체 $Count 쪽)."
            continue
        }
        if ($Numbers -notcontains $Number) { $Numbers += $Number }
    }
    if ($Numbers.Count -eq 0) { throw "선택한 쪽이 문서 범위 안에 없습니다(전체 $Count 쪽)." }
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

$File = Get-Item -LiteralPath $Path
$Ext = $File.Extension.ToLowerInvariant()
if ($Ext -notin '.pdf', '.docx', '.doc', '.rtf') {
    throw "페이지 캡처를 지원하지 않는 형식입니다: $Ext"
}

if (-not $OutDir) {
    $OutDir = Join-Path ([IO.Path]::GetTempPath()) ("drm-pages\{0}-{1}" -f $File.BaseName, (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
$Out = (New-Item -ItemType Directory -Path $OutDir -Force).FullName
$Before = @(Get-Process WINWORD -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
$Word = $null
$Doc = $null
$Window = $null
$Pane = $null
$Made = @()
$OwnedProcessId = 0
$OwnedStartedUtcTicks = 0

try {
    $Word = New-Object -ComObject Word.Application
    $Word.Visible = $false
    $Word.DisplayAlerts = 0
    try { $Word.AutomationSecurity = 3 } catch { }

    # ConfirmConversions=false, ReadOnly=true, AddToRecentFiles=false. 저장은 하지 않는다.
    $Doc = $Word.Documents.Open($File.FullName, $false, $true, $false)
    try { $Doc.Saved = $true } catch { }
    $Doc.Activate()
    $Window = $Doc.ActiveWindow
    try {
        $CandidateId = [int][DrmWordWindow]::ProcessId([long]$Window.Hwnd)
        if ($CandidateId -and $Before -notcontains $CandidateId) {
            $Candidate = Get-Process -Id $CandidateId -ErrorAction Stop
            if ($Candidate.ProcessName -eq 'WINWORD') {
                $OwnedProcessId = $CandidateId
                $OwnedStartedUtcTicks = $Candidate.StartTime.ToUniversalTime().Ticks
            }
        }
    } catch { }
    if ($Window.View.Type -ne 3) { $Window.View.Type = 3 } # wdPrintView
    $Pane = $Window.Panes.Item(1)
    $Count = [int]$Pane.Pages.Count
    if ($Count -lt 1) { throw 'Word가 문서 페이지를 만들지 못했습니다.' }

    foreach ($Number in (ConvertTo-PageNumbers $Pages $Count)) {
        $Bits = [byte[]]$Pane.Pages.Item($Number).EnhMetaFileBits
        $Bitmap = ConvertFrom-MetafileBits $Bits $Width
        $Target = Join-Path $Out ("page-{0:D3}.png" -f $Number)
        try { $Bitmap.Save($Target, [Drawing.Imaging.ImageFormat]::Png) } finally { $Bitmap.Dispose() }
        if (-not (Test-Png $Target)) { throw "PNG 머리가 아닌 결과가 생겼습니다: $Target" }
        $Made += $Target
    }
} finally {
    Release-Com $Pane
    Release-Com $Window
    if ($null -ne $Doc) {
        try { $Doc.Saved = $true } catch { }
        try { $Doc.Close($false) } catch { }
        Release-Com $Doc
    }
    if ($null -ne $Word) {
        try { $Word.Quit() } catch { }
        Release-Com $Word
    }
    try { [GC]::Collect(); [GC]::WaitForPendingFinalizers() } catch { }
    Start-Sleep -Milliseconds 500

    # 소유 PID와 시작 시각이 모두 같은 숨은 Word만 정리한다. 사용자가 열어 둔 Word는 건드리지 않는다.
    if ($OwnedProcessId -and $OwnedStartedUtcTicks) {
        $Process = Get-Process -Id $OwnedProcessId -ErrorAction SilentlyContinue
        if ($Process -and $Process.ProcessName -eq 'WINWORD' -and
            $Process.StartTime.ToUniversalTime().Ticks -eq $OwnedStartedUtcTicks -and
            $Process.MainWindowHandle -eq [IntPtr]::Zero) {
            Stop-Process -Id $OwnedProcessId -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Output ("페이지 {0}장 — {1}" -f $Made.Count, $Out)
$Made | ForEach-Object { Write-Output $_ }
