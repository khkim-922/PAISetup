<#
    ECM 에이전트가 띄운 오피스 문서 하나를 닫는다 — 그 경로의 문서만 닫고, 그 앱에 남은 문서가 없을 때만 앱을 끈다. 저장은 하지 않는다
    (편집의 고침은 change_doc.ps1 이 앞서 저장한다).

    부르는 꼴:
        powershell -NoProfile -ExecutionPolicy Bypass -File close_view.ps1 -Path <받은 파일> -App Word|Excel|PPT [-WaitSeconds 30]
            [-RequireClean]

    내는 것: 표준 출력에 JSON 한 줄({"found":…,"closed":…,"quit":…,"left":…,"others":[…]}). ``others`` 는 앱을 안 끈 판에 그 앱에 남은
    문서의 이름이다. 종료 값 0 닫았다 · 2 시한 안에 그 문서가 안 떴다(또는 이미 닫혔다) · 4 ``-RequireClean`` 인데 저장 안 된 고침이
    있어 안 닫았다 · 1 닫다가 실패했다.

    ``-RequireClean`` 은 올리기 앞에서 쓴다 — 미리 본 뒤 창에서 고친 것이 있으면 닫지 않고 멈춘다(없으면 닫아도 잃는 것이 없다).
    그 밖에는 저장 안 된 고침을 버리고 닫는다(보기로 받은 읽기 전용 문서다).

    ⚠ 앱은 남은 문서가 0 일 때만 끈다 — 끄면 저장 안 한 사람의 문서가 경고 없이 사라진다. 찾는 손은 곁의 office_doc.ps1 이 든다.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][ValidateSet('Word', 'Excel', 'PPT')][string]$App,
    [int]$WaitSeconds = 30,
    [switch]$RequireClean
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
. (Join-Path $PSScriptRoot 'office_doc.ps1')

function Stop-EmptyApplication($Application) {
    <# 남은 문서가 없는 앱을 끈다. 쥔 COM 참조가 남으면 파워포인트는 Quit 을 받고도 빈 창으로 남아, 참조를 다 놓은 뒤 아직
       문서 0 으로 답하는 앱을 한 번 더 끈다 #>
    try { $Application.Quit() } catch { }
    Release $Application
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    Start-Sleep -Milliseconds 1000
    foreach ($again in @(Get-Applications)) {
        $count = $null
        try { $documents = Get-OpenDocuments $again; $count = $documents.Count; Release $documents } catch { }
        if ($null -ne $count -and [int]$count -eq 0) { try { $again.Quit() } catch { } }
        Release $again
    }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}

function Write-Result([bool]$Found, [bool]$Closed, [bool]$Quit, [int]$Left, $Others = @()) {
    Write-Output (@{ found = $Found; closed = $Closed; quit = $Quit; left = $Left; others = @($Others) } | ConvertTo-Json -Compress)
}

function Get-OpenNames($Application) {
    <# 그 앱에 남은 문서의 이름 — 사람이 무엇을 닫아야 하나를 알게 낸다. 엑셀은 창이 보이는 통합 문서만 #>
    $names = @()
    try {
        $documents = Get-OpenDocuments $Application
        foreach ($doc in $documents) {
            $shown = $true
            if ($App -eq 'Excel') { $shown = $false; foreach ($w in $doc.Windows) { if ($w.Visible) { $shown = $true }; Release $w } }
            if ($shown) { $names += [string]$doc.Name }
            Release $doc
        }
        Release $documents
    } catch { }
    return , $names
}

$found = Find-OpenDocument $Path $WaitSeconds
if ($null -eq $found) { Write-Result $false $false $false -1; exit 2 }
$application, $match = $found.Application, $found.Document
if ($RequireClean -and -not (Test-Clean $match)) {
    Release $match; Release $application
    Write-Result $true $false $false -1
    exit 4
}
try {
    try { $match.Saved = $true } catch { }   # 고침은 앞서 저장됐거나 버릴 것이다 — 닫기는 늘 묻지 않고
    if ($App -eq 'PPT') { $match.Close() } else { $match.Close($false) }
    Release $match
    $count = $null
    try { $after = Get-OpenDocuments $application; $count = $after.Count; Release $after } catch { }
    # 엑셀은 숨은 통합 문서(개인 매크로 PERSONAL.XLSB 따위)도 센다 — 창이 하나도 안 보이는 통합 문서는 사람이 연 문서가 아니다
    if ($App -eq 'Excel' -and $null -ne $count) {
        try {
            $visible = 0
            foreach ($book in $application.Workbooks) {
                $shown = $false
                foreach ($w in $book.Windows) { if ($w.Visible) { $shown = $true }; Release $w }
                if ($shown) { $visible++ }
                Release $book
            }
            $count = $visible
        } catch { $count = $null }
    }
    $left = if ($null -eq $count) { -1 } else { [int]$count }
    # 못 셌으면(-1) 안 끈다 — 남은 앱은 사람이 끌 수 있지만 닫힌 사람의 문서는 못 되돌린다
    $quit = ($left -eq 0)
    $others = @()
    if (-not $quit -and $left -gt 0) { $others = Get-OpenNames $application }
    if ($quit) { Stop-EmptyApplication $application } else { Release $application }
    Write-Result $true $true $quit $left $others
    exit 0
} catch {
    Release $application
    Write-Output ('닫다가 실패했다: ' + $_.Exception.Message)
    exit 1
}
