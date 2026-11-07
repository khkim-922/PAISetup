<#
    ECM 에이전트가 띄운 pdf 하나를 Adobe Reader · Acrobat 에서 닫는다 — 그 탭만 닫고, 남은 문서가 없을 때만 앱을 끈다.

    부르는 꼴:
        powershell -NoProfile -ExecutionPolicy Bypass -File close_acrobat.ps1 -Path <받은 파일> [-WaitSeconds 30]

    내는 것: 표준 출력에 JSON 한 줄({"found":…,"closed":…,"quit":…,"left":…}) — close_view.ps1 과 같은 꼴이다. ``left`` 는
    남은 문서가 있으면 1(몇 개인지는 못 센다) · 없으면 0. 종료 값 0 닫았다 · 2 시한 안에 그 문서가 안 떴다 · 3 다른 pdf 가 앞 탭이라
    안 건드렸다 · 1 닫다가 실패했다.

    어떻게 닫나: Reader DC 는 문서 목록을 주는 COM 이 없고, DDE(AcroViewR21)는 붙기는 해도 명령을 다 거절한다(DMLERR_NOTPROCESSED ·
    Reader DC 21.11 에서 잼). 탭도 UI Automation 에 안 드러난다. 그래서 앞 탭만 다룬다 — 창 제목이 「<받은 파일 이름> - Adobe …」면
    받은 pdf 가 앞 탭이라, 창을 앞에 세우고 Ctrl+W 로 그 탭 하나만 닫는다. 에이전트는 받은 파일을 마지막에 띄우므로 읽기 판에서는
    이 꼴이다. 다른 pdf 가 앞 탭이면 아무것도 안 하고 3 으로 낸다. 닫은 뒤 제목에 문서 이름이 없으면(「Adobe Acrobat Reader DC …」)
    남은 문서가 0 이라 창을 닫아 앱을 끈다. 다른 문서 이름이 서면 사람의 문서라 앱은 둔다.

    ⚠ 받은 파일을 셸로 다시 열어 그 탭을 앞에 세우지 않는다 — 떠 있는 Reader 에 파일을 넘기는 길이 DDE 라, 이 PC 에서는 Reader 가
    「Acrobat failed to send a DDE command」 오류 창을 띄우고 멈춘다.

    ⚠ 키를 보내기 직전에 앞 창이 Reader 인가를 다시 본다 — 사람이 그 사이 다른 창을 누르면 Ctrl+W 가 그 창으로 간다. 앞 창이
    아니면 안 보내고 실패(1)로 낸다. 받은 파일은 보기로 연 읽기 전용이라 닫을 때 저장을 묻지 않는다.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [int]$WaitSeconds = 30
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PROCESS_NAMES = @('AcroRd32', 'Acrobat')     # Reader · Acrobat(Pro) — 둘 다 ProgId AcroExch.Document.*
$TITLE_TAIL = ' - Adobe '                      # 창 제목 「<문서 이름> - Adobe Acrobat …」의 이음매
$POLL_MS = 500
$SETTLE_MS = 2000                              # Ctrl+W · 창 닫기 뒤 제목이 바뀔 때까지

if (-not ('EcmSeed.Foreground' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace EcmSeed {
    public static class Foreground {
        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
        [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hwnd, int cmd);
        [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hwnd);
        [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, IntPtr pid);
        [DllImport("user32.dll")] static extern bool AttachThreadInput(uint from, uint to, bool attach);
        [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
        // 앞 창을 쥔 스레드에 입력을 잠깐 붙여 앞을 넘겨받는다 — 붙지 않으면 Windows 가 남이 띄운 창을 앞에 못 세우게 막는다
        public static bool Bring(IntPtr hwnd) {
            uint me = GetCurrentThreadId(), front = GetWindowThreadProcessId(GetForegroundWindow(), IntPtr.Zero);
            bool attached = front != 0 && front != me && AttachThreadInput(me, front, true);
            try { BringWindowToTop(hwnd); SetForegroundWindow(hwnd); }
            finally { if (attached) AttachThreadInput(me, front, false); }
            return GetForegroundWindow() == hwnd;
        }
        [DllImport("user32.dll")] static extern bool BringWindowToTop(IntPtr hwnd);
    }
}
'@
}
Add-Type -AssemblyName System.Windows.Forms

function Get-ReaderWindow {
    <# 앱의 맨 위 창 하나 — Reader 는 사용자 하나에 창 하나로 뜨고 문서는 그 안의 탭이다 #>
    foreach ($name in $PROCESS_NAMES) {
        $p = Get-Process -Name $name -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } |
            Select-Object -First 1
        if ($p) { return $p }
    }
    return $null
}

function Get-Title($Process) { $Process.Refresh(); return [string]$Process.MainWindowTitle }

function Write-Result([bool]$Found, [bool]$Closed, [bool]$Quit, [int]$Left) {
    Write-Output (@{ found = $Found; closed = $Closed; quit = $Quit; left = $Left } | ConvertTo-Json -Compress)
}

$target = [System.IO.Path]::GetFullPath($Path)
$head = [System.IO.Path]::GetFileName($target) + $TITLE_TAIL
$deadline = (Get-Date).AddSeconds($WaitSeconds)

# 에이전트가 띄운 창이 서기를 기다린다 — 받은 pdf 가 앞 탭이 될 때까지. 다른 pdf 가 앞이면 시한 끝에 3 으로 낸다
$reader = $null
$other = $false
while ((Get-Date) -lt $deadline) {
    $reader = Get-ReaderWindow
    if ($reader -and (Get-Title $reader).StartsWith($head, [StringComparison]::OrdinalIgnoreCase)) { break }
    $other = [bool]($reader -and (Get-Title $reader).Contains($TITLE_TAIL))
    $reader = $null
    Start-Sleep -Milliseconds $POLL_MS
}
if (-not $reader -and $other) { Write-Result $true $false $false 1; exit 3 }
if (-not $reader) { Write-Result $false $false $false -1; exit 2 }

try {
    $hwnd = $reader.MainWindowHandle
    if ([EcmSeed.Foreground]::IsIconic($hwnd)) { [void][EcmSeed.Foreground]::ShowWindow($hwnd, 9) }   # SW_RESTORE
    [void][EcmSeed.Foreground]::Bring($hwnd)
    Start-Sleep -Milliseconds $POLL_MS
    if ([EcmSeed.Foreground]::GetForegroundWindow() -ne $hwnd) {
        Write-Output '닫다가 실패했다: Reader 창을 앞에 세우지 못해 키를 안 보냈다'
        exit 1
    }
    [System.Windows.Forms.SendKeys]::SendWait('^w')
    Start-Sleep -Milliseconds $SETTLE_MS
    $after = Get-Title $reader
    if ($after.StartsWith($head, [StringComparison]::OrdinalIgnoreCase)) {
        Write-Output '닫다가 실패했다: Ctrl+W 뒤에도 그 문서가 앞 탭이다'
        exit 1
    }
    # 제목에 문서 이름이 없으면 남은 탭이 없다 — 창을 닫아 앱을 끈다. 문서 이름이 서면 사람의 문서라 둔다
    $left = if ($after.Contains($TITLE_TAIL)) { 1 } else { 0 }
    $quit = $false
    if ($left -eq 0) {
        $quit = $reader.CloseMainWindow()
        if ($quit) { $quit = $reader.WaitForExit($SETTLE_MS * 5) }
    }
    Write-Result $true $true $quit $left
    exit 0
} catch {
    Write-Output ('닫다가 실패했다: ' + $_.Exception.Message)
    exit 1
}
