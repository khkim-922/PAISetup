<#
    ECM 에이전트가 띄운 오피스 문서 하나를 닫는다 — 그 경로의 문서만 닫고, 그 앱에 남은 문서가 없을 때만 앱을 끈다.

    부르는 꼴:
        powershell -NoProfile -ExecutionPolicy Bypass -File close_view.ps1 -Path <받은 파일> -App Word|Excel|PPT [-WaitSeconds 30] [-Save]

    내는 것: 표준 출력에 JSON 한 줄({"found":…,"closed":…,"quit":…,"left":…}). 종료 값 0 닫았다 · 2 시한 안에 그 문서가
    안 떴다(또는 이미 닫혔다) · 1 닫다가 실패했다.

    왜 경로로 고르나: 에이전트는 받은 파일을 사람이 쓰던 앱에 띄울 수 있다(파워포인트는 사용자 하나에 하나만 뜨고, 워드 ·
    엑셀도 셸이 연 파일은 떠 있던 앱에 들어간다). 그 앱의 다른 문서는 사람의 것이라, 이름 · 창 제목이 아니라 받은 파일의
    전체 경로가 같은 문서 하나만 닫는다. 앱을 끄는 것은 남은 문서가 0 일 때뿐이다 — 끄면 저장 안 한 사람의 문서가 경고
    없이 사라진다. 보기로 연 읽기 전용 파일은 저장하지 않고 닫는다. ``-Save`` 는 편집으로 연 파일을 저장한 뒤 닫는다 — 에이전트는
    오피스 프로세스가 끝나야 편집완료 창을 띄우므로, 남은 문서가 0 이 아니면 그 수를 ``left`` 로 내고 앱은 그대로 둔다.

    앱을 어떻게 찾나: 셸이 띄운 오피스는 포커스를 잃기 전까지 실행 중 개체 표(ROT)에 안 올라 ``GetActiveObject`` 가 못 본다 —
    에이전트가 띄운 창이 바로 그 꼴이다. 그래서 오피스 창마다 문서 칸 창에서 ``AccessibleObjectFromWindow``(OBJID_NATIVEOM)로
    앱을 받고, ROT 의 앱도 함께 본다. 워드 · 엑셀이 둘 떠 있어도 그 문서를 든 앱을 찾는다.

    창이 뜨기를 기다린다: 에이전트는 파일을 다 받은 뒤 기본 앱을 띄우므로, 앱이 문서를 잡기까지 몇 초가 걸린다.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][ValidateSet('Word', 'Excel', 'PPT')][string]$App,
    [int]$WaitSeconds = 30,
    [switch]$Save
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$COM_NAME = @{ 'Word' = 'Word.Application'; 'Excel' = 'Excel.Application'; 'PPT' = 'PowerPoint.Application' }
# 앱의 맨 위 창 class → 그 안의 문서 칸 창 class. 문서 칸에서 받는 개체가 그 앱의 창 개체다(.Application 이 앱)
$WINDOW_CLASS = @{ 'Word' = @('OpusApp', '_WwG'); 'Excel' = @('XLMAIN', 'EXCEL7'); 'PPT' = @('PPTFrameClass', 'mdiClass') }
$POLL_MS = 500

if (-not ('EcmSeed.OfficeWindows' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
namespace EcmSeed {
    public static class OfficeWindows {
        delegate bool EnumProc(IntPtr hwnd, IntPtr param);
        [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc proc, IntPtr param);
        [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr parent, EnumProc proc, IntPtr param);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr hwnd, StringBuilder name, int size);
        [DllImport("oleacc.dll")] static extern int AccessibleObjectFromWindow(IntPtr hwnd, uint id, ref Guid iid,
            [MarshalAs(UnmanagedType.IDispatch)] out object found);
        const uint OBJID_NATIVEOM = 0xFFFFFFF0;
        static string ClassOf(IntPtr hwnd) { var s = new StringBuilder(256); GetClassName(hwnd, s, 256); return s.ToString(); }
        // 맨 위 창 class 가 frame 인 창마다, class 가 pane 인 첫 자식 창의 개체 하나
        public static object[] Find(string frame, string pane) {
            var found = new List<object>();
            EnumWindows((top, _) => {
                if (ClassOf(top) != frame) return true;
                EnumChildWindows(top, (child, __) => {
                    if (ClassOf(child) != pane) return true;
                    Guid iid = new Guid("00020400-0000-0000-C000-000000000046");   // IDispatch
                    object o;
                    if (AccessibleObjectFromWindow(child, OBJID_NATIVEOM, ref iid, out o) == 0 && o != null) { found.Add(o); return false; }
                    return true;
                }, IntPtr.Zero);
                return true;
            }, IntPtr.Zero);
            return found.ToArray();
        }
    }
}
'@
}

function Get-OpenDocuments($Application) {
    <# 그 앱의 열린 문서 모음(COM 개체 그대로). ⚠ 함수의 출력으로 내면 PowerShell 이 모음을 풀어 낱 문서로 바꾼다 — 문서가 하나
       남았을 때 .Count 가 비어 0 으로 읽히고, 그러면 사람의 문서가 남은 앱을 끈다. 그래서 쉼표로 감싸 모음째 낸다 #>
    switch ($App) {
        'Word'  { return , $Application.Documents }
        'Excel' { return , $Application.Workbooks }
        'PPT'   { return , $Application.Presentations }
    }
}

function Get-Applications {
    <# 그 앱의 인스턴스들 — 창에서 받은 것과 ROT 의 것. 같은 앱이 둘로 들 수 있지만 문서를 찾으면 거기서 멈춘다 #>
    $apps = @()
    $classes = $WINDOW_CLASS[$App]
    foreach ($window in @([EcmSeed.OfficeWindows]::Find($classes[0], $classes[1]))) {
        try { $apps += $window.Application } catch { }
        Release $window
    }
    try { $apps += [Runtime.InteropServices.Marshal]::GetActiveObject($COM_NAME[$App]) } catch { }
    return $apps
}

function Stop-EmptyApplication($Application) {
    <# 남은 문서가 없는 앱을 끈다. 이 판이 쥔 COM 참조가 남아 있으면 파워포인트는 Quit 을 받고도 빈 창으로 남는다 — 참조를 다
       놓은 뒤 그 앱이 아직 문서 0 으로 답하면 한 번 더 끈다. 문서가 0 인 앱만 끄므로 사람의 문서는 안 닫힌다 #>
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

function Write-Result([bool]$Found, [bool]$Closed, [bool]$Quit, [int]$Left) {
    Write-Output (@{ found = $Found; closed = $Closed; quit = $Quit; left = $Left } | ConvertTo-Json -Compress)
}

function Release($Object) {
    if ($null -ne $Object) { try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Object) } catch { } }
}

$target = [System.IO.Path]::GetFullPath($Path)
$deadline = (Get-Date).AddSeconds($WaitSeconds)

while ((Get-Date) -lt $deadline) {
    foreach ($application in @(Get-Applications)) {
        $match = $null
        $documents = $null
        try {
            $documents = Get-OpenDocuments $application
            foreach ($doc in $documents) {
                $full = ''
                try { $full = [System.IO.Path]::GetFullPath([string]$doc.FullName) } catch { }
                if ($full -and [string]::Equals($full, $target, [StringComparison]::OrdinalIgnoreCase)) { $match = $doc; break }
                Release $doc
            }
        } catch { }   # 앱이 아직 뜨는 중이면 목록이 안 선다 — 다음 판에 다시 본다
        Release $documents
        if ($null -eq $match) { Release $application; continue }
        try {
            if ($Save) { $match.Save() } else { try { $match.Saved = $true } catch { } }
            if ($App -eq 'PPT') { $match.Close() } else { $match.Close($false) }   # 저장할 것은 위에서 했다 — 닫기는 늘 묻지 않고
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
            if ($quit) { Stop-EmptyApplication $application } else { Release $application }
            Write-Result $true $true $quit $left
            exit 0
        } catch {
            Release $application
            Write-Output ('닫다가 실패했다: ' + $_.Exception.Message)
            exit 1
        }
    }
    Start-Sleep -Milliseconds $POLL_MS
}

Write-Result $false $false $false -1
exit 2
