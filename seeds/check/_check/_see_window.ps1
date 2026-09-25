# 창 하나를 **그 창 손잡이로** 찍는다 — 가려져 있어도 제 모습이 찍힌다. 윈도우 전용.
#
# 왜 있나 — 화면 전체를 찍으면(CopyFromScreen · 도구 스크린샷) 그림은 **맨 위에 보이는 픽셀**이다.
#   보려던 창이 다른 창 뒤에 있으면 앞 창이 찍히고, 캡처를 막는 창(VDI 클라이언트 등 ·
#   DisplayAffinity)이 앞에 있으면 그 자리는 대체 그림이 된다. 그 빈 자리를 「창이 안 떴다 ·
#   글씨가 없다」로 읽으면 멀쩡한 것을 고치러 간다. 새 창은 사람이 쓰던 창의 초점을 못 뺏어
#   **뒤에 뜨는 것이 흔하다** — 그래서 가려진 채인 경우가 예외가 아니다.
#   그림 문(홈 PreToolUse 훅)이 화면 전체 크기 그림을 열 때 이 파일을 가리킨다.
#
# 무엇을 내나 — 판정이 아니라 재료다:
#   · 창 자리 · 층(0 = 맨 위) · 앞창인가 · 최소화인가, 그리고 **그 위에 겹친 창들**(프로세스 · 캡처 막기)
#   · window.png — 창 손잡이로 그 창만 그린 것(PrintWindow · PW_RENDERFULLCONTENT). 가려져도 찍힌다
#   · screen.png — 화면에서 그 자리를 오린 것. 둘이 다르면 **가려졌다**는 뜻이다
#
# 쓰는 법:
#   powershell -NoProfile -ExecutionPolicy Bypass -File _see_window.ps1 -Title "제목 일부"
#   powershell -NoProfile -ExecutionPolicy Bypass -File _see_window.ps1 -List      # 보이는 창 제목 목록
#
# 종료코드 — 0 찍었다 · 2 못 쟀다(창을 못 찾았다 · 최소화라 그림이 없다 · 윈도우가 아니다).
# ⚠ **최소화된 창은 손잡이로도 못 찍는다** — 창이 그림을 안 가진 상태라 빈 그림이 나온다. 그때는
#   찍지 않고 2 로 알린다. 창을 되살리는 것은 사람 창을 건드리는 일이라 이 파일이 안 한다.
# ⚠ **그림은 줄이지 않는다** — 크면 그림 문이 여는 순간 치수를 대고, 줄이는 손은 곁의 `_shrink.py` 다.
param(
  [string]$Title,
  [string]$Out = (Join-Path $env:TEMP 'see-window'),
  [switch]$List
)
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
if ($env:OS -ne 'Windows_NT') { Write-Host '윈도우가 아니다 — 못 쟀다'; exit 2 }

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class SeeWin {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool GetWindowDisplayAffinity(IntPtr h, out uint a);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint f);
  // 보이는 최상위 창 — 위층부터 아래층 차례(EnumWindows 가 층 차례로 준다)
  public static List<IntPtr> Top() { var l = new List<IntPtr>(); EnumWindows((h, x) => { if (IsWindowVisible(h)) l.Add(h); return true; }, IntPtr.Zero); return l; }
  public static string Title(IntPtr h) { var s = new StringBuilder(512); GetWindowTextW(h, s, 512); return s.ToString(); }
}
"@
# ⚠ **DPI 를 먼저 세운다** — 안 세우면 배율 걸린 화면에서 자리가 논리 좌표로 와 오림이 어긋난다.
[void][SeeWin]::SetProcessDPIAware()

function Get-ProcName([IntPtr]$h) {
  $p = 0; [void][SeeWin]::GetWindowThreadProcessId($h, [ref]$p)
  try { return (Get-Process -Id $p -ErrorAction Stop).ProcessName } catch { return "pid $p" }
}

$all = [SeeWin]::Top()
if ($List -or -not $Title) {
  Write-Host '보이는 창 (위층부터 · 제목 있는 것만):'
  $n = 0
  foreach ($h in $all) {
    $t = [SeeWin]::Title($h); if (-not $t) { continue }
    Write-Host ("  {0,3}  {1}  ·  {2}" -f $n, $t, (Get-ProcName $h)); $n++
  }
  exit 0
}

$idx = -1
for ($i = 0; $i -lt $all.Count; $i++) { if ([SeeWin]::Title($all[$i]).Contains($Title)) { $idx = $i; break } }
if ($idx -lt 0) {
  Write-Host "제목에 '$Title' 이 든 보이는 창이 없다 — 못 쟀다. -List 로 제목을 본다"
  exit 2
}
$h = $all[$idx]
$fg = [SeeWin]::GetForegroundWindow()
$r = New-Object SeeWin+RECT; [void][SeeWin]::GetWindowRect($h, [ref]$r)
$w = $r.R - $r.L; $hh = $r.B - $r.T
Write-Host ("창: '{0}' · {1} · 자리 ({2},{3})-({4},{5}) · {6}×{7} · 층 {8}(0=맨 위) · 앞창={9}" -f `
  [SeeWin]::Title($h), (Get-ProcName $h), $r.L, $r.T, $r.R, $r.B, $w, $hh, $idx, ($h -eq $fg))

if ([SeeWin]::IsIconic($h) -or $w -le 0 -or $hh -le 0) {
  Write-Host '최소화돼 있다 — 창이 그림을 안 가져 손잡이로도 못 찍는다. 되살린 뒤 다시 — 못 쟀다'
  exit 2
}

# 위에 겹친 창 — 화면 오림이 무엇을 찍게 될지가 여기서 갈린다
$over = @()
for ($i = 0; $i -lt $idx; $i++) {
  $o = New-Object SeeWin+RECT; [void][SeeWin]::GetWindowRect($all[$i], [ref]$o)
  if ($o.L -lt $r.R -and $o.R -gt $r.L -and $o.T -lt $r.B -and $o.B -gt $r.T -and ($o.R - $o.L) -gt 1 -and ($o.B - $o.T) -gt 1) {
    $a = 0; [void][SeeWin]::GetWindowDisplayAffinity($all[$i], [ref]$a)
    $over += ("  - '{0}' · {1}{2}" -f [SeeWin]::Title($all[$i]), (Get-ProcName $all[$i]),
              $(if ($a -ne 0) { ' · 캡처를 막는다' } else { '' }))
  }
}
if ($over) { Write-Host '위에 겹친 창 — 화면 오림에는 이것들이 찍힌다:'; $over | ForEach-Object { Write-Host $_ } }
else       { Write-Host '위에 겹친 창 없다 — 두 그림이 같아야 한다' }

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$winPng = Join-Path $Out 'window.png'
$scrPng = Join-Path $Out 'screen.png'
# 2 = PW_RENDERFULLCONTENT — 합성기(DWM)가 그리는 창(터미널 · 브라우저 · 전자 앱)도 제 모습으로 온다
$bmp = New-Object System.Drawing.Bitmap $w, $hh
$g = [System.Drawing.Graphics]::FromImage($bmp); $hdc = $g.GetHdc()
$ok = [SeeWin]::PrintWindow($h, $hdc, 2)
$g.ReleaseHdc($hdc); $g.Dispose(); $bmp.Save($winPng, [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
$bmp = New-Object System.Drawing.Bitmap $w, $hh
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size); $g.Dispose()
$bmp.Save($scrPng, [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
if (-not $ok) { Write-Host "손잡이 그리기가 졌다(PrintWindow) — window.png 는 비었을 수 있다. screen.png 만 믿지 않는다 — 못 쟀다"; exit 2 }
Write-Host "찍음 — 창: $winPng · 화면 오림: $scrPng"
exit 0
