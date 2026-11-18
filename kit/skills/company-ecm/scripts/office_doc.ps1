<#
    오피스 앱에 열린 문서 하나를 전체 경로로 찾는 손 — close_view.ps1 · change_doc.ps1 이 점으로 싣는다.

    부르는 꼴(싣는 쪽 스크립트 안에서):
        . (Join-Path $PSScriptRoot 'office_doc.ps1')      # 싣기 전에 $App(Word · Excel · PPT)을 둔다
        $found = Find-OpenDocument $target $WaitSeconds   # 없으면 $null · 있으면 @{ Application = …; Document = … }

    ⚠ 에이전트는 받은 파일을 사람이 쓰던 앱에 띄울 수 있다 — 그 앱의 다른 문서는 사람의 것이라 전체 경로가 같은 문서 하나만
    다룬다. 셸이 띄운 오피스는 포커스를 잃기 전까지 ROT 에 안 올라 ``GetActiveObject`` 가 못 본다 — 그래서 오피스 창마다
    ``AccessibleObjectFromWindow``(OBJID_NATIVEOM)로 앱을 받고 ROT 의 앱도 함께 본다.
#>

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

function Release($Object) {
    if ($null -ne $Object) { try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Object) } catch { } }
}

function Get-OpenDocuments($Application) {
    <# 그 앱의 열린 문서 모음(COM 개체 그대로). ⚠ 쉼표로 감싸 모음째 낸다 — 풀려 나가면 문서가 하나 남았을 때 .Count 가
       0 으로 읽혀 사람의 문서가 남은 앱을 끈다 #>
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

function Find-OpenDocument([string]$Target, [int]$WaitSeconds) {
    <# 전체 경로가 ``Target`` 인 열린 문서를 ``WaitSeconds`` 안에 찾는다 — 찾으면 @{ Application; Document }, 못 찾으면 $null.
       찾지 못한 앱 · 문서의 참조는 놓는다 #>
    $full = [System.IO.Path]::GetFullPath($Target)
    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    while ($true) {
        foreach ($application in @(Get-Applications)) {
            $match = $null
            $documents = $null
            try {
                $documents = Get-OpenDocuments $application
                foreach ($doc in $documents) {
                    $name = ''
                    try { $name = [System.IO.Path]::GetFullPath([string]$doc.FullName) } catch { }
                    if ($name -and [string]::Equals($name, $full, [StringComparison]::OrdinalIgnoreCase)) { $match = $doc; break }
                    Release $doc
                }
            } catch { }   # 앱이 아직 뜨는 중이면 목록이 안 선다 — 다음 판에 다시 본다
            Release $documents
            if ($null -ne $match) { return @{ Application = $application; Document = $match } }
            Release $application
        }
        if ((Get-Date) -ge $deadline) { return $null }
        Start-Sleep -Milliseconds $POLL_MS
    }
}

function Test-Clean($Document) {
    <# 저장 안 된 고침이 없나 — 파워포인트는 MsoTriState(-1 참)로 답한다. 못 읽으면 고침이 있는 것으로 본다(안전한 쪽) #>
    try { return [bool]$Document.Saved } catch { return $false }
}
