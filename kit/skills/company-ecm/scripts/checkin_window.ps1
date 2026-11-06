<#
    ECM 에이전트의 「편집완료」 창에서 다음 판을 고르고 수정 내용을 적어 올린다 — 편집으로 연 문서를 저장하고 오피스를 끝낸 뒤에 부른다.

    부르는 꼴:
        powershell -NoProfile -ExecutionPolicy Bypass -File checkin_window.ps1 -ObjectId <16 hex> -Desc <수정 내용> -Current <지금 판>
            [-WaitSeconds 60] [-FindOnly]

    내는 것: 표준 출력에 JSON 한 줄({"found":…,"choices":[…],"picked":…,"saved":…,"closed":…}). 종료 값 0 올렸다(창이 닫혔다 ·
    ``-FindOnly`` 면 창이 떠 있다) · 2 시한 안에 그 문서의 창이 안 떴다 · 1 창은 떴는데 다음 판을 못 가렸거나 칸을 못 채웠다
    (``saved`` 거짓 — 아무것도 안 보냈다), 또는 저장을 보냈는데 창이 시한 안에 안 닫혔다(``saved`` 참 — 다시 누르지 않는다).

    무엇을 하나: 에이전트는 오피스 프로세스가 끝나면 편집완료 창(WinForms 안의 Internet Explorer_Server)을 띄운다. 그 웹 화면은 UI
    Automation 으로는 단추가 안 보여, 창에 WM_HTML_GETOBJECT 를 보내 문서 개체를 받는다. 창 주소의 ``MS_OBJECT_ID`` 가 맞는 창만
    다룬다 — 다른 문서의 창은 사람의 것이다. 판 고르기 라디오(``choice_version``)는 지금 판(덮어쓰기)이 기본이라 **늘 마지막 값(다음
    판)을 고른다.** 다음 판은 값으로 가린다 — 라디오 가운데 지금 판(``-Current``)보다 큰 값이 꼭 하나일 때만 그것을 누르고(클릭이라
    화면의 처리기도 돈다), 아니면 아무것도 안 보낸다. 수정 내용 칸(``version_desc``)을 채우고 그 화면의 저장 함수(``fn_save``)를 부르면
    창이 닫히며 에이전트가 올린다. 저장 함수는 창의 타이머로 부른다 — 화면이 확인 창을 띄워도 이 손이 그 자리에 묶이지 않는다.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^[0-9A-Fa-f]{16}$')][string]$ObjectId,
    [Parameter(Mandatory = $true)][string]$Desc,
    [Parameter(Mandatory = $true)][string]$Current,
    [int]$WaitSeconds = 60,
    [switch]$FindOnly
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$CHOICE_NAME = 'choice_version'
$DESC_ID = 'version_desc'
$SAVE_CALL = 'setTimeout(function(){ fn_save(); }, 0);'
$POLL_MS = 500
$CLOSE_SECONDS = 30   # 저장 함수를 부른 뒤 창이 닫히기(올리기가 끝나기)를 기다리는 시한

if (-not ('EcmSeed.IeWindows' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
namespace EcmSeed {
    public static class IeWindows {
        delegate bool EnumProc(IntPtr hwnd, IntPtr param);
        [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc proc, IntPtr param);
        [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr parent, EnumProc proc, IntPtr param);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr hwnd, StringBuilder name, int size);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern uint RegisterWindowMessage(string name);
        [DllImport("user32.dll")] static extern IntPtr SendMessageTimeout(IntPtr hwnd, uint msg, IntPtr w, IntPtr l, uint flags, uint ms, out IntPtr result);
        [DllImport("oleacc.dll")] static extern int ObjectFromLresult(IntPtr result, ref Guid iid, IntPtr w, [MarshalAs(UnmanagedType.IUnknown)] out object found);
        static string ClassOf(IntPtr hwnd) { var s = new StringBuilder(64); GetClassName(hwnd, s, 64); return s.ToString(); }
        // 이 데스크톱의 모든 Internet Explorer_Server 창의 문서 개체(IHTMLDocument2)
        public static object[] Documents() {
            var panes = new List<IntPtr>();
            EnumWindows((top, _) => {
                EnumChildWindows(top, (child, __) => { if (ClassOf(child) == "Internet Explorer_Server") panes.Add(child); return true; }, IntPtr.Zero);
                return true;
            }, IntPtr.Zero);
            var docs = new List<object>();
            uint msg = RegisterWindowMessage("WM_HTML_GETOBJECT");
            Guid iid = new Guid("626FC520-A41E-11CF-A731-00A0C9082637");
            foreach (var pane in panes) {
                IntPtr result;
                SendMessageTimeout(pane, msg, IntPtr.Zero, IntPtr.Zero, 2, 2000, out result);
                object doc;
                if (result != IntPtr.Zero && ObjectFromLresult(result, ref iid, IntPtr.Zero, out doc) == 0 && doc != null) docs.Add(doc);
            }
            return docs.ToArray();
        }
    }
}
'@
}

function Write-Result([bool]$Found, $Choices, [string]$Picked, [bool]$Saved, [bool]$Closed) {
    Write-Output (@{ found = $Found; choices = @($Choices); picked = $Picked; saved = $Saved; closed = $Closed } | ConvertTo-Json -Compress)
}

function Find-Window {
    foreach ($doc in @([EcmSeed.IeWindows]::Documents())) {
        $url = ''
        try { $url = [string]$doc.url } catch { }
        if ($url -match 'checkoutcheckin' -and $url -match ('MS_OBJECT_ID=' + $ObjectId + '(&|$)')) { return $doc }
    }
    return $null
}

$deadline = (Get-Date).AddSeconds($WaitSeconds)
$window = $null
while ((Get-Date) -lt $deadline -and $null -eq $window) {
    try { $window = Find-Window } catch { }
    if ($null -eq $window) { Start-Sleep -Milliseconds $POLL_MS }
}
if ($null -eq $window) { Write-Result $false @() '' $false $false; exit 2 }
if ($FindOnly) { Write-Result $true @() '' $false $false; exit 0 }

# 창이 다 그려지기를 기다린다 — 칸이 없으면 다음 판에 다시 본다
$radios = @()
$descBox = $null
while ((Get-Date) -lt $deadline) {
    try {
        # IE 의 칸 모음은 PowerShell 이 펼치지 못한다(@() 가 빈다) — length · item(i) 로 꺼낸다
        $found = $window.getElementsByName($CHOICE_NAME)
        $radios = @(for ($i = 0; $i -lt $found.length; $i++) { $found.item($i) })
        $descBox = $window.getElementById($DESC_ID)
    } catch { }
    if ($radios.Count -ge 2 -and $null -ne $descBox) { break }
    Start-Sleep -Milliseconds $POLL_MS
}
$choices = @($radios | ForEach-Object { [string]$_.value })
if ($radios.Count -lt 2 -or $null -eq $descBox) { Write-Result $true $choices '' $false $false; exit 1 }

# 다음 판 — 지금 판보다 큰 값이 꼭 하나인 라디오. 판은 「큰 수.작은 수」라 수 둘로 견준다(0.10 > 0.9)
function Split-Version([string]$Text) {
    if ($Text -match '^\s*(\d+)\.(\d+)\s*$') { return @([int]$Matches[1], [int]$Matches[2]) }
    return $null
}
$now = Split-Version $Current
$larger = @($radios | Where-Object {
    $v = Split-Version ([string]$_.value)
    $null -ne $now -and $null -ne $v -and ($v[0] -gt $now[0] -or ($v[0] -eq $now[0] -and $v[1] -gt $now[1]))
})
if ($larger.Count -ne 1) { Write-Result $true $choices '' $false $false; exit 1 }
$next = $larger[0]
$next.click()
if (-not $next.checked) { Write-Result $true $choices ([string]$next.value) $false $false; exit 1 }
$descBox.value = $Desc
$window.parentWindow.execScript($SAVE_CALL, 'JavaScript')

$closeBy = (Get-Date).AddSeconds($CLOSE_SECONDS)
$closed = $false
while ((Get-Date) -lt $closeBy) {
    Start-Sleep -Milliseconds $POLL_MS
    $still = $null
    try { $still = Find-Window } catch { }
    if ($null -eq $still) { $closed = $true; break }
}
Write-Result $true $choices ([string]$next.value) $true $closed
if ($closed) { exit 0 } else { exit 1 }
