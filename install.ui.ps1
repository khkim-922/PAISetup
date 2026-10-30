# 설치 창 — 값을 받고 옵션을 고르게 한 뒤 몸통(`install.ps1`)을 돌리고, 몸통이 찍는 줄로 진행을 보여 준다.
#
#   부르는 꼴  `install.cmd` · `Setup.exe` 가 `powershell -File install.ui.ps1 [-NoDevTools | -DevTools] [-PersonalFor <도구,…>]
#              [-WithPersonalConfig] [-NoUpgrade]` 로 띄운다. 나머지 스위치는 사람이 칠 것이 아니다(바로 아래).
#   내는 것    몸통을 `-Yes -EnvFile <임시 값 파일>` 로 돌려 판정을 창에 띄우고, 기록을
#              `%LOCALAPPDATA%\Claude Code Setup\logs\install-<시각>.log` 로 남긴다. 화면이 못 서면(WPF 를 못 싣는 PC ·
#              STA 가 아닌 셸) 같은 콘솔에서 몸통을 돌린다.
#   종료 값    몸통이 옆에 없으면 1 · 콘솔 갈래는 몸통의 값 · 그 밖은 0(판정은 창이 말한다).
#
# 여기에는 설치 로직이 없다 — 무엇을 어떻게 깔지는 `install.ps1` 한 자리가 든다. 로직을 여기 옮기면 화면 갈래와 콘솔
#   갈래가 서로 다른 코드를 타고 한쪽만 고쳐진다.
# ⚠ **진행 막대의 신호는 몸통이 이미 찍는 `[n/N]` 줄이다** — 통로를 따로 내면 걸음이 늘 때 한쪽만 고쳐져 막대가 조용히
#   안 찬다. 분모도 그 줄에서 받으므로(N 은 몸통의 `$Steps` 표 길이) 걸음이 늘어도 여기는 고칠 것이 없다. 읽는 줄 꼴은
#   `Step-Line` 이 든다.
# 화면은 WPF 를 인라인 XAML 로 짓는다(PAISetup #53 · claude-config 결정 0167) — .NET Framework 에 든 어셈블리 셋만 실어 남의 DLL 이
#   없고, 창이 화면 배율을 알아(시스템 DPI 인식) 125 · 150 % 에서 윈도가 늘려 흐리게 하지 않는다. 옛 윈도 폼 창은 배율을 몰라
#   (잰 DPI 인식 0) 늘려 그려졌다(PAISetup #52).

# 사람이 칠 것이 아닌 스위치 셋:
#   `-NoConsole` — 「이 프로세스에는 보여 줄 콘솔이 없다」는 상태. 이 파일이 제 자신을 숨김으로 다시 띄울 때와 `Setup.exe` 가
#     띄울 때(그쪽은 처음부터 콘솔을 안 붙인다) 넘긴다. 아래 「검은 창을 없애는 자리」가 읽는다.
#     ⚠ **사건이 아니라 상태로 묻는다.** 「다시 띄워졌나」로 물으면 exe 갈래가 그 물음에 안 걸려 콘솔이 없는데도 한 번 더
#       띄운다 — 창은 하나만 뜨니 안 보이고 0.5 초만 조용히 샌다.
#   `-Unattended` — 로그온 자동 실행이 새 판의 `Setup.exe` 를 푸는 자로만 쓸 때 넘긴다. 아래 「무인 갈래」가 든다.
#   `-PersonalNotice` — 몸통이 옛 제작자 칸을 이어받아 설치한 뒤 이 창을 한 번 띄울 때 넘긴다. 파일 끝 알림이 든다.
param([switch]$NoDevTools, [switch]$WithPersonalConfig, [string]$PersonalFor, [switch]$NoUpgrade, [switch]$NoConsole, [switch]$Unattended,
      [switch]$PersonalNotice, [switch]$DevTools)

$ErrorActionPreference = 'Stop'
# ⚠ **콘솔 인코딩은 던지게 두지 않는다.** 출력이 파일로 돌려진 채 뜨면 그 줄이 걸릴 수 있고, 위 `Stop` 이 그 자리에서
#   끝내 **한 줄도 안 찍힌 채 죽는다.** 인코딩은 편의지 조건이 아니다.
$OutputEncoding = [System.Text.Encoding]::UTF8
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$Here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Engine = Join-Path $Here 'install.ps1'
# 로컬 페이지를 기본 브라우저로 여는 손(`Open-InBrowser`)은 곁의 조각이 든다 — 설치 몸통과 같이 쓴다
$OpenPageLib = Join-Path $Here 'open-page.ps1'
if (Test-Path -LiteralPath $OpenPageLib) { . $OpenPageLib }

# ── 이 폴더가 몇 판인가 ─────────────────────────────────────────────────────────
# 진본은 곁의 `VERSION` 한 줄이고 릴리스 태그가 그 값에서 난다 — 푼 폴더가 제 판을 알아야 창 제목에 띄우고 새 판과 견준다.
# 없으면 빈 값으로 간다 — 보여 주는 값이지 설치의 조건이 아니다.
# ⚠ **BOM 을 손으로 걷는다.** 인코딩 문지기는 파워셸 · 배치 파일만 보므로 누가 `VERSION` 을 BOM 을 붙여 저장해도 안
#   걸리고, 번호 앞에 붙은 세 바이트는 화면에는 멀쩡히 찍히고 **견주는 자리에서만** 안 맞는다.
$DistVersion = ''
$VersionPath = Join-Path $Here 'VERSION'
if (Test-Path -LiteralPath $VersionPath) {
  try {
    $DistVersion = (([string](Get-Content -LiteralPath $VersionPath -TotalCount 1 -Encoding UTF8)) -replace "^\uFEFF", '').Trim()
  } catch { $DistVersion = '' }
}

# ── 콘솔에 남은 글을 사람이 읽을 틈 ────────────────────────────────────────────
# `Hold-Console [말]` — 말을 띄우고 Enter 를 기다린다. 못 읽는 콘솔이면 그냥 지난다. 내는 것 없음.
# ⚠ **`install.cmd` 에는 `pause` 가 없다** — 설치 창의 [닫기] 가 뒤의 콘솔까지 닫아야 해서다. 그래서 읽을 것이 남는 콘솔
#   갈래는 끝나기 전에 이것을 부른다 — 안 부르면 한 줄 찍고 창째로 사라져, 사람은 아무 일도 안 일어난 줄 안다.
# 화면이 선 갈래에서는 안 부른다 — 결과는 창 안에 있고 창을 닫는 것이 곧 끝내는 동작이라, 멈추면 안 닫히는 콘솔이 남는다.
function Hold-Console([string]$Said = '끝났습니다 — Enter 를 누르면 닫힙니다') {
  try { Read-Host $Said | Out-Null } catch { }
}

if (-not (Test-Path -LiteralPath $Engine)) {
  Write-Host "install.ps1 이 옆에 없다: $Here" -ForegroundColor Red
  Write-Host '폴더를 통째로 풀었는지 본다 — 압축 안에서 바로 누르면 옆 파일을 못 찾는다.'
  Hold-Console
  exit 1
}

# ── 무인 갈래 — **창을 안 띄우고 바로 나간다** ─────────────────────────────────
# ⚠ **이것은 「무인으로 설치한다」가 아니다.** 로그온 자동 실행이 새 판을 받았을 때 `Setup.exe` 를 **푸는 자로만** 쓰는
#   자리다 — exe 는 짐을 `<판>\` 에 푼 뒤 이 파일을 띄우고 **기다리지 않고 나간다**(claude-config `Setup.c` 맨 끝 곁말). 여기서
#   설치를 시작하면 부르는 쪽은 끝난 줄 알고 「완료」를 찍는다 — **거짓 초록이다.** 푸는 일은 이 줄에 닿기 전에 끝났으니 조용히
#   비키고, 새 판으로 설치하는 것은 부르는 쪽(`autorun.ps1`)이 제 로그 안에서 든다.
if ($Unattended) { exit 0 }

# ── 창이 받은 깃발 — **넘기는 줄은 이 배열 하나다** ─────────────────────────────
# 사람이 이 창에 준 깃발(파일 머리 「부르는 꼴」) 가운데 켠 것만 든다. 받는 자리가 셋이다 — 콘솔 갈래의 몸통 · 제 자신 되띄우기 ·
#   새 판 묻기가 띄우는 새 `Setup.exe`(그 exe 는 제 인자를 그대로 새 창에 붙인다). 셋이 같은 줄을 받아야 어느 길로 넘어가도 깃발이
#   안 샌다.
# ⚠ **켠 스위치 · 빈 값이 아닌 것만 넣는다** — Windows PowerShell 5.1 의 `-File` 은 `-NoDevTools:False` 를 스위치로 못 바꾸고
#   (인자 변환 오류), 빈 `-PersonalFor` 는 값이 떨어져 「인자가 없다」로 진다 — 둘 다 받는 쪽이 아예 안 뜬다.
# 사람이 칠 것이 아닌 셋(`-NoConsole` · `-Unattended` · `-PersonalNotice`)은 안 든다 — 이 프로세스의 상태 · 한 번만 띄우는 알림이라
#   받는 자리마다 따로 정한다.
$PassArgs = @(
  if ($NoDevTools)         { '-NoDevTools' }
  if ($DevTools)           { '-DevTools' }
  if ($WithPersonalConfig) { '-WithPersonalConfig' }
  if ($PersonalFor)        { '-PersonalFor'; $PersonalFor }
  if ($NoUpgrade)          { '-NoUpgrade' }
)

# ── 화면이 설 수 있나 ───────────────────────────────────────────────────────────
# 못 서면 말하고 같은 콘솔에서 몸통을 돌린다 — 화면이 안 서는 것과 설치가 안 되는 것은 다른 명제인데, 말없이 내려가면
#   사람은 「화면이 뜨는 줄 알았는데 왜」에서 멈춘다.
$uiOk = $true
try {
  # ⚠ **STA 가 아니면 화면을 안 세운다** — WPF 창은 STA 실에서만 선다. 이 파일을 띄우는 셋(`install.cmd` · `Setup.exe` · 몸통의 알림
  #   띄우기)은 다 `powershell -File` 이라 Windows PowerShell 5.1 의 기본값 STA 로 서지만, `-MTA` 로 불린 판에서 창을 지으면 그 자리에서
  #   던지고 사람은 아무것도 못 본다 — 그 판은 아래 콘솔 갈래로 간다.
  if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA') { throw 'STA 가 아닌 셸이다' }
  Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase -ErrorAction Stop
  # ⚠ **소프트웨어 그리기로 고정한다 — 창을 하나라도 짓기 전에.** 하드웨어 그리기 창은 화면 복사(사람이 찍어 보내는 화면 ·
  #   PrintWindow)에 내용이 빈 흰 판으로 찍혔다(PAISetup #52 실측). 정적인 서식이라 잃는 것이 없다.
  [Windows.Media.RenderOptions]::ProcessRenderMode = [Windows.Interop.RenderMode]::SoftwareOnly
} catch { $uiOk = $false }

if (-not $uiOk) {
  Write-Host '화면을 못 띄운다 — 콘솔로 진행한다.' -ForegroundColor Yellow
  # ⚠ **몸통을 제 프로세스로 띄운다 — 이 프로세스 안에서 부르지 않는다.** 빗장을 쥔 설치를 찾는 두 자(몸통의 `Find-EngineHolders` ·
  #   로그온 자동 실행의 가드)는 명령줄에 `install.ps1` 이 든 파워셸만 본다. 안에서 부르면 명령줄이 이 파일 이름이라 둘 다 못 보고,
  #   빗장에 막힌 다음 판이 쥔 쪽을 못 댄다. 같은 콘솔을 물려받으므로 묻는 줄 · 찍는 줄은 그대로다. 넘기는 깃발은 위 `$PassArgs` 다.
  $engineArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Engine) + $PassArgs
  & (Get-Process -Id $PID).Path @engineArgs
  # ⚠ **판정을 먼저 집는다.** `Hold-Console` 뒤에 읽으면 그 사이에 도는 것이 `$LASTEXITCODE`
  #   를 갈아치울 수 있고, 그러면 **몸통이 진 판이 0 으로 보고된다.**
  $rc = $LASTEXITCODE
  Hold-Console
  exit $rc
}

# ── 인자를 한 줄로 싸는 자 — **규칙은 이 파일에 하나다** ────────────────────────
# `Quote-Argv <인자 배열>` → 낱낱을 큰따옴표로 싼 한 줄. 이 파일이 `powershell.exe` 를 띄우는 두 자리(제 자신을 되띄우기 ·
# 몸통 띄우기)가 다 이 함수를 지난다 — 같은 꼴로 띄우므로 규칙이 둘일 수 없다(PAISetup #3).
#
# 스위치까지 다 싼다 — 따옴표는 파워셸의 인자 맞추기 **전에** 벗겨지므로 `"-NoProfile"` 도 스위치로 서고, 곧바로 띄운 판과
#   `cmd` 를 한 겹 지난 판이 같다.
# ⚠ **골라 싸면 모자란다.** 몸통 줄은 `cmd` 에 넘어가므로 `&` · `^` · 괄호가 든 경로는 안 싸면 cmd 가 거기서 명령을
#   자른다 — **빈칸이 없어도 그렇다.** 다 싸면 자리마다 다른 문자 집합을 맞출 까닭이 없어진다.
function Quote-Argv([string[]]$Argv) {
  ($Argv | ForEach-Object { '"' + $_ + '"' }) -join ' '
}

# ── 검은 창을 없애는 자리 — **제 자신을 숨김으로 다시 띄우고 빠진다** ───────────
# `install.cmd` 가 연 콘솔을 설치 화면 뒤에 남기지 않는다 — 콘솔 없이(`CreateNoWindow`) 제 자신을 `-NoConsole` 로 다시 띄우고
# 이 프로세스는 0 으로 나간다. 못 띄우면 그냥 이 창에서 간다 — 검은 창 하나 때문에 설치를 막지 않는다.
#
# ⚠ **위 `$uiOk` 갈래보다 뒤에 선다.** 화면을 못 세우는 PC 는 이 줄에 닿기 전에 콘솔로 빠지므로 안 보이는 창에 대고
#   말하는 일이 없다 — 앞에 두면 그 갈래가 숨은 창에 찍고 죽어, 사람은 아무 일도 안 일어난 줄 안다.
# ⚠ **숨김은 만들 때 준다 — 뜬 뒤에 숨기지 않는다.** Windows Terminal 이 콘솔을 들면 `GetConsoleWindow()` 는 진짜 창이
#   아니라 `PseudoConsoleWindow` 를 돌려주고, 거기 건 `ShowWindow(SW_HIDE)` 는 **참을 돌려주고 아무것도 안 한다** — 거짓 초록이다.
# ⚠ **`CreateNoWindow` 여야 한다 — `-WindowStyle Hidden` 이 아니다.** `-WindowStyle Hidden` 은 「첫 창을 숨겨라」를 프로세스
#   시작값에 박아, 그 숨김이 콘솔에서 멈추지 않고 **설치 화면까지 번진다**(창은 서는데 안 보인다). `start /min` 의 최소화도
#   같은 축이다 — 창 상태를 물려주는 자를 쓰지 않는다. `CreateNoWindow` 는 「콘솔을 붙이지 마라」라 창 상태를 안 건드리고,
#   설치 화면은 제 크기로 가운데 뜬다.
# ⚠ **숨었나는 `Visible` 로 잰다 — `WindowState` 가 아니다.** 숨은 창도 `Normal` 이라 그 값으로 재면 초록으로 읽힌다.
if (-not $NoConsole) {
  $again = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $MyInvocation.MyCommand.Path, '-NoConsole') + $PassArgs
  if ($PersonalNotice) { $again += '-PersonalNotice' }
  try {
    $psi = New-Object Diagnostics.ProcessStartInfo
    $psi.FileName         = (Get-Process -Id $PID).Path     # 지금 나를 돌린 그 파워셸
    $psi.Arguments        = Quote-Argv $again
    $psi.WorkingDirectory = $Here
    $psi.UseShellExecute  = $false
    $psi.CreateNoWindow   = $true
    [void][Diagnostics.Process]::Start($psi)
    exit 0
  } catch { }
}

# ── 값 파일을 읽는 손 — **몸통의 함수를 그대로 싣는다** ────────────────────────────
# 지시 줄(`Read-Directive`)과 값 줄(`Read-EnvFile`)을 읽는 규칙은 몸통 하나가 든다 — 여기 옮겨 적으면 규칙을 고치는 날 창과 몸통이
#   같은 파일에서 다른 값을 읽는다. `-Describe` 로 받지 않는 까닭은 값 줄에 사람이 적어 둔 키(`ANTHROPIC_AUTH_TOKEN`)가 들 수 있어서다 —
#   키가 표준 출력을 지나게 두지 않는다. 그래서 몸통 파일을 구문으로 읽어 그 두 함수의 정의만 이 창에 세운다(자동 실행 몸통이 엔진에서
#   자리 재기를 떼어 쓰는 것과 같은 꼴). 몸통을 통째로 점으로 부르면 몸통이 돌아 버린다.
# 못 세우면 빈 손으로 선다 — 지시는 없고 값 파일은 빈 표다. 그 판은 아래 `-Describe` 도 못 받아 창이 설치를 안 받는다.
$EngineFns = @('Read-Directive', 'Read-EnvFile')
try {
  $engineAst = [System.Management.Automation.Language.Parser]::ParseFile($Engine, [ref]$null, [ref]$null)
  foreach ($fnName in $EngineFns) {
    $fnAst = $engineAst.Find({ param($x) $x -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $x.Name -eq $fnName }.GetNewClosure(), $true)
    if ($fnAst) { . ([scriptblock]::Create($fnAst.Extent.Text)) }
  }
} catch { }
if (-not (Get-Command Read-Directive -CommandType Function -ErrorAction SilentlyContinue)) { function Read-Directive { return $null } }
if (-not (Get-Command Read-EnvFile -CommandType Function -ErrorAction SilentlyContinue)) { function Read-EnvFile { return @{} } }

# ── 옆에 온 값 파일 — 회사 공통값은 이미 채워져 온다 ────────────────────────────
# 뽑는 자(claude-config `scripts/build-dist.sh`)가 자리 파일에서 파생해 넣는다. 사람은 키만 넣으면 된다. 지난번에 고른 것은 값 파일이
#   아니라 몸통이 내준다(아래 「지난번에 고른 것」).
$EnvPath = Join-Path $Here 'install.env'
$Preset  = Read-EnvFile $EnvPath

# ── 기록이 쌓이는 자리 — **이 파일에 한 번만 적는다** ───────────────────────────
# 쓰는 자(`Save-RunLog`)와 거기로 가는 문(아래 단추 줄의 「설치기록」 링크)이 같은 자리를 가리켜야 한다 — 자리를 둘에
# 적으면 옮기는 날 한쪽만 고쳐지고, 링크는 기록이 있는데도 「아직 기록이 없습니다」로 답한다.
# 판 폴더 밖이다 — 까닭은 `Save-RunLog` 머리말이 든다.
$LogDir = Join-Path $env:LOCALAPPDATA 'Claude Code Setup\logs'

# ── 고를 제품 · 지난번에 고른 것 · 몸통만 아는 사실 — **목록도 기본값도 기록도 자리도 몸통이 든다** ─────────────────────
# 여기 옮겨 적지 않고 몸통에 묻는다 — `-Describe` 가 내는 줄(꼴과 뜻은 몸통의 「`-Describe` 갈래」 머리말이 든다). 옮겨 적으면 제품이
#   늘 때 한쪽만 고쳐져 「골랐는데 안 깔린다」로만 보이고, 기록 자리 · 꼴을 창이 다시 지으면 창을 띄운 폴더에 따라 기록을 못 찾고,
#   자리 · 규칙 · 기본값을 창이 다시 지으면 같은 PC 가 창 회차와 로그온 회차에서 다른 자리 · 다른 칸으로 돈다(PAISetup #46).
# ⚠ **자식으로 띄워 묻는다.** 이 창 안에서 그 파일을 부르면 저쪽의 `exit` 가 **이 창까지** 끌고 나간다.
$Choices = @()
# 이 자리에서 안 내놓는 제품(키 → 참) — 몸통의 `product-here|키|no`(`Test-ProductHere`). 칸은 제자리에 두고 잠근다(결정 0167).
$NotHere = @{}
# 저장소를 받는 자리 — 몸통이 내준다(바로 아래 곁말). 못 받으면 빈 값이고, 그때 아래 저장소 칸은 링크 대신 글자만 세운다.
$RepoRoot = ''
# 지난번에 고른 것 — 이름 → 값(몸통의 기록 꼴 그대로 · 「하나도 안 고름」은 `none`). 못 받으면 빈 표고 칸은 기본값으로 선다.
$Recorded = @{}
# 이 PC 에 맡겨 둔 회사 키가 있나(몸통의 회사 키 덩이 · 값은 안 온다). 있으면 사내 키 칸이 비어도 설치를 받는다 — 몸통이 그 덩이를
#   풀어 심는다. 못 받으면 없는 것으로 읽는다 — 키 칸을 비운 채 누르면 지금처럼 막는다.
$KeySaved = $false
# 이 PC 의 자리(`inside` · `outside`)와 그 프로브 — 몸통이 잰 것을 받는다. 못 받거나 몸통이 못 정했으면 자리가 빈 값이고 까닭이
#   `$SiteWhy` 에 서며, 창은 설치를 안 받는다(아래 「자리를 못 정한 판」). 창은 따로 안 잰다.
$Site = ''; $SiteWhy = '설치 몸통에 자리를 못 물었다 (install.ps1 -Describe)'; $probe = ''
# 이 자리에서 VS Code 가 필수인가 · 깃발 없는 판의 자동 실행 · 데스크탑 앱 행이 어디서 깔리나(키 → yes · outside · no)
$VsRequired = $false; $AutoRunOn = $false; $AppHere = @{}
# 제작자 칸의 도구(도구 · 제품 · 글자) · 「올리기」 칸이 드는 VC++ 런타임 판 · 앱 이름
$PersonalTools = @(); $VcRuntimeMin = ''; $AppName = ''
# 몸통이 끝까지 답했나 — 종료 값과, 칸이 기대는 줄(`site|` · `vscode|` · `autorun|`)을 받았나. 아래 묻기 끝에서 가른다.
$DescribeRc = $null; $DescribeSeen = @{}
try {
  # 지금 나를 돌린 그 파워셸로 묻는다 — 되띄우기 · 몸통 띄우기와 같은 꼴이다. 이름(`powershell`)으로 부르면 PATH 가 깨진 PC 에서 이
  #   자리만 못 띄운다.
  $raw = & (Get-Process -Id $PID).Path -NoProfile -ExecutionPolicy Bypass -File $Engine -Describe
  $DescribeRc = $LASTEXITCODE
  foreach ($ln in @($raw)) {
    if ("$ln" -match '^\s*product\|([a-z0-9-]+)\|(.+?)\|(on|off)\s*$') {
      $Choices += ,@{ Key = $Matches[1]; Label = $Matches[2]; On = ($Matches[3] -eq 'on') }
    }
    # 이 자리는 받아 쓴다 — 화면이 `~/repos` 를 제 글자로 박으면 몸통이 자리를 옮기는 날 설치는 새 데로 받는데 화면은
    #   다른 데를 연다.
    elseif ("$ln" -cmatch '^\s*product-here\|([a-z0-9-]+)\|no\s*$') { $NotHere[$Matches[1]] = $true }
    elseif ("$ln" -match '^\s*config-repo-root\|(.+?)\s*$') { $RepoRoot = $Matches[1] }
    elseif ("$ln" -match '^\s*record\|([a-z-]+)\|(.+?)\s*$') { $Recorded[$Matches[1]] = $Matches[2] }
    elseif ("$ln" -match '^\s*company-key\|(yes|no)\s*$') { $KeySaved = ($Matches[1] -eq 'yes') }
    # 몸통만 아는 사실 — 글자를 가려 맞춘다(`-cmatch`). 몸통이 내는 꼴 그대로가 아니면(대문자 · 빈 프로브) 안 받은 줄이다.
    elseif ("$ln" -cmatch '^\s*site\|(inside|outside)\|(.+?)\s*$') { $Site = $Matches[1]; $probe = $Matches[2]; $SiteWhy = ''; $DescribeSeen['site'] = $true }
    elseif ("$ln" -cmatch '^\s*site\|error\|(.+?)\s*$') { $Site = ''; $SiteWhy = $Matches[1]; $DescribeSeen['site'] = $true }
    elseif ("$ln" -cmatch '^\s*vscode\|(required|optional)\s*$') { $VsRequired = ($Matches[1] -ceq 'required'); $DescribeSeen['vscode'] = $true }
    elseif ("$ln" -cmatch '^\s*autorun\|(on|off)\s*$') { $AutoRunOn = ($Matches[1] -ceq 'on'); $DescribeSeen['autorun'] = $true }
    elseif ("$ln" -cmatch '^\s*app\|([a-z0-9-]+)\|(yes|outside|no)\s*$') { $AppHere[$Matches[1]] = $Matches[2] }
    elseif ("$ln" -cmatch '^\s*personal\|([a-z0-9-]+)\|([a-z0-9-]+)\|(.+?)\s*$') {
      $PersonalTools += ,@{ Key = $Matches[1]; Pick = $Matches[2]; Label = $Matches[3] }
    }
    elseif ("$ln" -cmatch '^\s*vcruntime-min\|(.+?)\s*$') { $VcRuntimeMin = $Matches[1] }
    elseif ("$ln" -cmatch '^\s*app-name\|(.+?)\s*$') { $AppName = $Matches[1] }
  }
  # ⚠ **몸통이 끝까지 답하지 않았으면 자리를 못 받은 판이다** — 0 으로 안 끝났거나 `site|` · `vscode|` · `autorun|` 가운데 하나라도
  #   없으면 `site|error` 와 같이 잠근다. 중간에 끊긴 답을 그대로 쓰면 못 받은 칸이 기본값(자동 실행 끔)으로 서, 그대로 누른 판이
  #   `-NoAutoRun` 을 넘겨 사람이 안 끈 자동 실행을 걷고 끈 기록까지 적는다.
  if ($DescribeRc -ne 0 -or -not ($DescribeSeen['site'] -and $DescribeSeen['vscode'] -and $DescribeSeen['autorun'])) {
    $missing = @('site', 'vscode', 'autorun' | Where-Object { -not $DescribeSeen[$_] })
    $Site = ''
    $SiteWhy = "설치 몸통의 답이 모자라다 (install.ps1 -Describe 종료 $DescribeRc$(if ($missing.Count) { ' · 없는 줄 ' + ($missing -join ', ') }))"
  }
} catch {
  # 못 띄웠거나 답을 읽다 던졌다 — 자리를 못 받은 판으로 잠그고 진 것을 한 줄로 말한다(아래 「자리를 못 정한 판」이 띄운다). 삼키면
  #   제품 목록 없이 기본값 칸이 서고, 그대로 누른 판이 `-Pick` 없이 몸통을 띄워 사람이 끈 제품을 되살린다.
  $Site = ''
  $SiteWhy = "설치 몸통에 못 물었다 (install.ps1 -Describe — $(("$($_.Exception.Message)" -split '\r?\n')[0]))"
}
# 앱 이름이 안 왔으면(몸통에 못 물은 판) 그 판은 설치를 안 받는다 — 상자 제목에만 쓰는 이름이라 일반 낱말로 선다.
if (-not $AppName) { $AppName = '설치' }

# ── 지난번에 고른 것 — 칸의 첫 상태 ─────────────────────────────────────────────
# ⚠ **칸은 이것으로 채운다 — 없을 때만 기본값이다.** 설치가 끝날 때 「다음에는 이것을 누르면 됩니다」로 보낸 사람이 창을 다시
#   열었는데 기본값이 뜨면, 그대로 누르는 순간 그 사람이 켰던 제품 · VS Code · 제작자 칸이 꺼진 채로 다시 적혀 자동 실행이 그것들을
#   조용히 안 올린다. 다 끈 제품도 기록이다(`Pick` 이 빈 목록) — 기록이 없는 것(`$null`)과 가른다.
# `-NoDevTools` 는 화면에 칸이 없다 — 기록이 끔이면 아래 [설치 시작]이 그대로 넘긴다(창을 `-DevTools` 로 띄운 판은 안 넘긴다).
$Saved = @{ Pick = $null; NoVsCode = $null; NoDevTools = ($Recorded['devtools'] -eq 'no'); Personal = @(); Repo = $null; GatewayUrl = '' }
if ($Recorded.ContainsKey('pick'))     { $Saved.Pick = @($Recorded['pick'] -split '[,\s]+' | Where-Object { $_ -and $_ -ne 'none' }) }
if ($Recorded.ContainsKey('vscode'))   { $Saved.NoVsCode = ($Recorded['vscode'] -eq 'no') }
if ($Recorded.ContainsKey('personal')) { $Saved.Personal = @($Recorded['personal'] -split '[,\s]+' | Where-Object { $_ -and $_ -ne 'none' }) }
if ($Recorded.ContainsKey('config-repo')) { $Saved.Repo = $(if ($Recorded['config-repo'] -ne 'none') { $Recorded['config-repo'] } else { '' }) }
if ($Recorded['gateway-url'] -and $Recorded['gateway-url'] -ne 'none') { $Saved.GatewayUrl = $Recorded['gateway-url'] }

# ── 화면 ────────────────────────────────────────────────────────────────────────
# 차례는 처음 까는 사람이 묻는 차례다 — 무엇을 하는 창인가(머리 · 「알아보기」) → 넣을 것이 있나(「연결」) → 무엇을 깔까(「설치할
#   도구」) → 더 손볼 것(접힌 「자세히 설정」 · 접혀도 지금 값을 한 줄로 보인다) → 누른다(아래 띠). 문서 링크는 「알아보기」 한 줄,
#   저장소 링크는 그 칸 곁, 기록은 아래 띠 — 링크마다 하는 일이 같은 무리에 산다(PAISetup #52 배치안 · #53).
# 칸은 스타일만으로 그린다 — 남의 테마 DLL 을 안 싣는다(claude-config 결정 0167). 다크 모드는 안 한다 — .NET Framework 의 WPF 에는
#   시스템 테마를 따르는 사전이 없어 붓을 두 벌 둬야 한다.
# ⚠ **자리 수를 박지 않는다.** 줄 · 칸은 쌓는 판(StackPanel · WrapPanel · Grid)이 자리를 잡는다 — 옛 창은 링크를 글자 폭으로 재
#   오른쪽에서 쌓고 서로 가려 앞으로 내야 했다. 글을 고치거나 링크를 더해도 셈이 없다.
[xml]$ScreenXaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Width="600" SizeToContent="Height" ResizeMode="CanMinimize" WindowStartupLocation="CenterScreen"
        Background="#F3F3F3" Foreground="#1B1B1B" FontSize="13"
        FontFamily="Segoe UI Variable Text, Segoe UI, Malgun Gothic"
        TextOptions.TextFormattingMode="Display" UseLayoutRounding="True">
  <Window.Resources>
    <SolidColorBrush x:Key="Accent" Color="#005FB8"/>
    <SolidColorBrush x:Key="Muted" Color="#5F5F5F"/>
    <SolidColorBrush x:Key="Line" Color="#E5E5E5"/>
    <Style x:Key="Card" TargetType="Border">
      <Setter Property="Background" Value="White"/><Setter Property="BorderBrush" Value="{StaticResource Line}"/>
      <Setter Property="BorderThickness" Value="1"/><Setter Property="CornerRadius" Value="8"/>
      <Setter Property="Padding" Value="16,14"/><Setter Property="Margin" Value="0,0,0,10"/>
    </Style>
    <Style x:Key="CardTitle" TargetType="TextBlock">
      <Setter Property="FontSize" Value="14"/><Setter Property="FontWeight" Value="SemiBold"/>
    </Style>
    <Style x:Key="Note" TargetType="TextBlock">
      <Setter Property="Foreground" Value="{StaticResource Muted}"/><Setter Property="FontSize" Value="12"/><Setter Property="TextWrapping" Value="Wrap"/>
    </Style>
    <Style x:Key="Glyph" TargetType="TextBlock">
      <Setter Property="FontFamily" Value="Segoe MDL2 Assets"/><Setter Property="FontSize" Value="12"/>
      <Setter Property="VerticalAlignment" Value="Center"/>
    </Style>
    <!-- 글자 링크 — 누르면 파일 · 폴더 · 페이지가 열린다 -->
    <Style x:Key="Link" TargetType="Button">
      <Setter Property="Cursor" Value="Hand"/><Setter Property="Foreground" Value="{StaticResource Accent}"/>
      <Setter Property="Template"><Setter.Value>
        <ControlTemplate TargetType="Button">
          <TextBlock x:Name="T" Text="{TemplateBinding Content}" Background="Transparent"/>
          <ControlTemplate.Triggers>
            <Trigger Property="IsMouseOver" Value="True"><Setter TargetName="T" Property="TextDecorations" Value="Underline"/></Trigger>
            <Trigger Property="IsKeyboardFocused" Value="True"><Setter TargetName="T" Property="TextDecorations" Value="Underline"/></Trigger>
            <Trigger Property="IsEnabled" Value="False"><Setter Property="Foreground" Value="{StaticResource Muted}"/><Setter Property="Cursor" Value="Arrow"/></Trigger>
          </ControlTemplate.Triggers>
        </ControlTemplate>
      </Setter.Value></Setter>
    </Style>
    <!-- 문서 한 장을 여는 알약 — 「알아보기」 줄. Tag 가 그림 글자다 -->
    <Style x:Key="Pill" TargetType="Button">
      <Setter Property="Cursor" Value="Hand"/><Setter Property="Margin" Value="0,0,6,6"/>
      <Setter Property="Template"><Setter.Value>
        <ControlTemplate TargetType="Button">
          <Border x:Name="B" Background="White" BorderBrush="#E0E0E0" BorderThickness="1" CornerRadius="14" Padding="10,4">
            <StackPanel Orientation="Horizontal">
              <TextBlock Text="{TemplateBinding Tag}" FontFamily="Segoe MDL2 Assets" FontSize="12" Foreground="#005FB8" VerticalAlignment="Center" Margin="0,0,6,0"/>
              <ContentPresenter VerticalAlignment="Center"/>
            </StackPanel>
          </Border>
          <ControlTemplate.Triggers>
            <Trigger Property="IsMouseOver" Value="True"><Setter TargetName="B" Property="BorderBrush" Value="#005FB8"/></Trigger>
            <Trigger Property="IsKeyboardFocused" Value="True"><Setter TargetName="B" Property="BorderBrush" Value="#005FB8"/></Trigger>
            <Trigger Property="IsEnabled" Value="False"><Setter Property="Opacity" Value="0.5"/><Setter Property="Cursor" Value="Arrow"/></Trigger>
          </ControlTemplate.Triggers>
        </ControlTemplate>
      </Setter.Value></Setter>
    </Style>
    <Style TargetType="CheckBox">
      <Setter Property="Margin" Value="0,4"/><Setter Property="Cursor" Value="Hand"/>
      <Setter Property="Template"><Setter.Value>
        <ControlTemplate TargetType="CheckBox">
          <!-- 칸 글이 남은 폭 안에서 접히게 DockPanel 로 둔다 — 가로 StackPanel 은 폭을 끝없이 줘 글이 잘린다 -->
          <DockPanel Background="Transparent">
            <Border x:Name="Box" DockPanel.Dock="Left" Width="18" Height="18" CornerRadius="4" BorderThickness="1" BorderBrush="#8A8A8A" Background="White" VerticalAlignment="Top" Margin="0,1,0,0">
              <TextBlock x:Name="Mark" Text="&#xE73E;" FontFamily="Segoe MDL2 Assets" FontSize="11" Foreground="White"
                         HorizontalAlignment="Center" VerticalAlignment="Center" Visibility="Collapsed"/>
            </Border>
            <ContentPresenter Margin="8,0,0,0" VerticalAlignment="Center"/>
          </DockPanel>
          <ControlTemplate.Triggers>
            <Trigger Property="IsChecked" Value="True">
              <Setter TargetName="Box" Property="Background" Value="#005FB8"/><Setter TargetName="Box" Property="BorderBrush" Value="#005FB8"/>
              <Setter TargetName="Mark" Property="Visibility" Value="Visible"/>
            </Trigger>
            <Trigger Property="IsKeyboardFocused" Value="True"><Setter TargetName="Box" Property="BorderBrush" Value="#1B1B1B"/></Trigger>
            <Trigger Property="IsEnabled" Value="False"><Setter Property="Opacity" Value="0.5"/></Trigger>
          </ControlTemplate.Triggers>
        </ControlTemplate>
      </Setter.Value></Setter>
    </Style>
    <!-- 도구 칩 — 한 칩이 그 제품의 CLI · 확장 · 데스크탑 앱을 통째로 든다 -->
    <Style x:Key="Chip" TargetType="ToggleButton">
      <Setter Property="Margin" Value="0,0,8,8"/><Setter Property="Cursor" Value="Hand"/><Setter Property="HorizontalAlignment" Value="Stretch"/>
      <Setter Property="Template"><Setter.Value>
        <ControlTemplate TargetType="ToggleButton">
          <Border x:Name="B" CornerRadius="6" BorderThickness="1" BorderBrush="#D1D1D1" Background="White" Padding="12,7">
            <StackPanel Orientation="Horizontal">
              <TextBlock x:Name="M" Text="&#xE739;" FontFamily="Segoe MDL2 Assets" FontSize="14" Foreground="#8A8A8A" VerticalAlignment="Center" Margin="0,0,8,0"/>
              <ContentPresenter VerticalAlignment="Center"/>
            </StackPanel>
          </Border>
          <ControlTemplate.Triggers>
            <Trigger Property="IsChecked" Value="True">
              <Setter TargetName="B" Property="Background" Value="#EAF3FB"/><Setter TargetName="B" Property="BorderBrush" Value="#005FB8"/>
              <Setter TargetName="M" Property="Text" Value="&#xE73A;"/><Setter TargetName="M" Property="Foreground" Value="#005FB8"/>
            </Trigger>
            <Trigger Property="IsKeyboardFocused" Value="True"><Setter TargetName="B" Property="BorderThickness" Value="2"/></Trigger>
            <Trigger Property="IsEnabled" Value="False"><Setter Property="Opacity" Value="0.55"/><Setter Property="Cursor" Value="Arrow"/></Trigger>
          </ControlTemplate.Triggers>
        </ControlTemplate>
      </Setter.Value></Setter>
    </Style>
    <!-- 접는 머리 — 「자세히 설정」 · 「기록 펼치기」 -->
    <Style x:Key="Fold" TargetType="ToggleButton">
      <Setter Property="Cursor" Value="Hand"/><Setter Property="HorizontalContentAlignment" Value="Stretch"/>
      <Setter Property="Template"><Setter.Value>
        <ControlTemplate TargetType="ToggleButton">
          <DockPanel Background="Transparent">
            <TextBlock x:Name="A" DockPanel.Dock="Left" Text="&#xE76C;" FontFamily="Segoe MDL2 Assets" FontSize="11" VerticalAlignment="Center" Margin="0,0,10,0"/>
            <ContentPresenter VerticalAlignment="Center"/>
          </DockPanel>
          <ControlTemplate.Triggers>
            <Trigger Property="IsChecked" Value="True"><Setter TargetName="A" Property="Text" Value="&#xE70D;"/></Trigger>
          </ControlTemplate.Triggers>
        </ControlTemplate>
      </Setter.Value></Setter>
    </Style>
    <Style x:Key="Primary" TargetType="Button">
      <Setter Property="Cursor" Value="Hand"/>
      <Setter Property="Template"><Setter.Value>
        <ControlTemplate TargetType="Button">
          <Border x:Name="B" Background="#005FB8" CornerRadius="4" Padding="20,7">
            <ContentPresenter HorizontalAlignment="Center" TextElement.Foreground="White" TextElement.FontWeight="SemiBold"/>
          </Border>
          <ControlTemplate.Triggers>
            <Trigger Property="IsMouseOver" Value="True"><Setter TargetName="B" Property="Background" Value="#0A6CC6"/></Trigger>
            <Trigger Property="IsKeyboardFocused" Value="True"><Setter TargetName="B" Property="Background" Value="#004C93"/></Trigger>
            <Trigger Property="IsEnabled" Value="False"><Setter TargetName="B" Property="Background" Value="#9EBFE0"/></Trigger>
          </ControlTemplate.Triggers>
        </ControlTemplate>
      </Setter.Value></Setter>
    </Style>
    <Style x:Key="Secondary" TargetType="Button">
      <Setter Property="Cursor" Value="Hand"/>
      <Setter Property="Template"><Setter.Value>
        <ControlTemplate TargetType="Button">
          <Border x:Name="B" Background="White" BorderBrush="#D1D1D1" BorderThickness="1" CornerRadius="4" Padding="18,6">
            <ContentPresenter HorizontalAlignment="Center"/>
          </Border>
          <ControlTemplate.Triggers>
            <Trigger Property="IsMouseOver" Value="True"><Setter TargetName="B" Property="Background" Value="#F5F5F5"/></Trigger>
            <Trigger Property="IsKeyboardFocused" Value="True"><Setter TargetName="B" Property="BorderBrush" Value="#1B1B1B"/></Trigger>
          </ControlTemplate.Triggers>
        </ControlTemplate>
      </Setter.Value></Setter>
    </Style>
    <!-- 잠긴 칸은 회색 바탕 — 그 자리에서 안 쓰는 칸이 제자리에 남아 있다는 것이 한눈에 보인다(결정 0167 의 한 판) -->
    <Style TargetType="TextBox"><Setter Property="Padding" Value="6,5"/><Setter Property="BorderBrush" Value="#C8C8C8"/>
      <Style.Triggers><Trigger Property="IsEnabled" Value="False"><Setter Property="Background" Value="#F0F0F0"/><Setter Property="BorderBrush" Value="#E0E0E0"/></Trigger></Style.Triggers></Style>
    <Style TargetType="PasswordBox"><Setter Property="Padding" Value="6,5"/><Setter Property="BorderBrush" Value="#C8C8C8"/>
      <Style.Triggers><Trigger Property="IsEnabled" Value="False"><Setter Property="Background" Value="#F0F0F0"/><Setter Property="BorderBrush" Value="#E0E0E0"/></Trigger></Style.Triggers></Style>
  </Window.Resources>

  <DockPanel>
    <!-- 아래 띠 — 한 줄이다. 윈도 마법사 · 대화상자의 관례대로 오른쪽은 할 일이 먼저, 그다음 닫기([설치 시작] = Enter · [닫기] = Esc).
         왼쪽 끝은 문제가 생겼을 때 가는 데(설치기록), 그 사이는 상태 칸(높이가 박힌 두 줄 · 넘치는 글은 줄임표와 툴팁 · 알림이 없으면 빈다).
         알림이 서고 걷혀도 창의 크기와 칸 자리가 안 바뀐다 -->
    <Border DockPanel.Dock="Bottom" Background="White" BorderBrush="{StaticResource Line}" BorderThickness="0,1,0,0" Padding="20,12">
      <DockPanel Height="36">
        <Button x:Name="LnkLog" DockPanel.Dock="Left" Style="{StaticResource Link}" Content="설치기록" FontSize="12" VerticalAlignment="Center" Margin="0,0,14,0"/>
        <StackPanel DockPanel.Dock="Right" Orientation="Horizontal" VerticalAlignment="Center" Margin="12,0,0,0">
          <Button x:Name="BGo" Style="{StaticResource Primary}" Content="설치 시작" IsDefault="True" Margin="0,0,8,0"/>
          <Button x:Name="BClose" Style="{StaticResource Secondary}" Content="닫기" IsCancel="True"/>
        </StackPanel>
        <TextBlock x:Name="StatusText" FontSize="12" TextWrapping="Wrap" TextTrimming="CharacterEllipsis" MaxHeight="34" VerticalAlignment="Center"/>
      </DockPanel>
    </Border>

    <!-- 몸 — 화면보다 길어지면(작은 화면 · 큰 배율에서 「자세히 설정」을 펼친 판) 이 칸만 스크롤하고 아래 띠는 늘 보인다 -->
    <ScrollViewer x:Name="Scroll" VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Disabled" Focusable="False">
      <StackPanel Margin="20,18,20,8">
        <!-- 머리 — 이름 · 판 · 자리 배지 · 한 줄 설명 · 「알아보기」 -->
        <DockPanel>
          <Border x:Name="SiteBadge" DockPanel.Dock="Right" CornerRadius="10" Padding="10,2" VerticalAlignment="Center">
            <StackPanel Orientation="Horizontal">
              <Ellipse x:Name="SiteDot" Width="7" Height="7" VerticalAlignment="Center" Margin="0,0,6,0"/>
              <TextBlock x:Name="SiteText" FontSize="12"/>
            </StackPanel>
          </Border>
          <StackPanel Orientation="Horizontal">
            <TextBlock x:Name="AppTitle" FontSize="20" FontWeight="SemiBold"/>
            <Border x:Name="VerPill" Background="#E5E5E5" CornerRadius="9" Padding="8,1" Margin="10,4,0,0" VerticalAlignment="Center">
              <TextBlock x:Name="VerText" FontSize="11" Foreground="{StaticResource Muted}"/>
            </Border>
          </StackPanel>
        </DockPanel>
        <TextBlock Text="고른 도구의 CLI 와 데스크탑 앱을, 원하면 VS Code 와 확장까지 세웁니다." Style="{StaticResource Note}" FontSize="13" Margin="0,4,0,10"/>
        <WrapPanel Margin="0,0,0,8">
          <TextBlock Text="알아보기" Style="{StaticResource Note}" VerticalAlignment="Center" Margin="0,0,10,6"/>
          <Button x:Name="LnkFeat" Style="{StaticResource Pill}" Tag="&#xE71D;" Content="제공기능"/>
          <Button x:Name="LnkFlow" Style="{StaticResource Pill}" Tag="&#xE8AB;" Content="설치흐름"/>
          <Button x:Name="LnkNews" Style="{StaticResource Pill}" Tag="&#xE81C;" Content="바뀐 것"/>
        </WrapPanel>

        <!-- 설치하는 중 — [설치 시작] 뒤에 선다. 도는 동안 아래 칸들은 접히고, 끝나면 판정을 든 채 남고 칸들이 다시 선다 -->
        <Border x:Name="RunCard" Style="{StaticResource Card}" Visibility="Collapsed">
          <StackPanel>
            <TextBlock x:Name="RunTitle" Text="설치하는 중" Style="{StaticResource CardTitle}" Margin="0,0,0,8"/>
            <ProgressBar x:Name="Bar" Height="6" Minimum="0" Maximum="100" Foreground="#005FB8" Background="#E5E5E5" BorderThickness="0"/>
            <TextBlock x:Name="State" TextWrapping="Wrap" Margin="0,8,0,10"/>
            <ToggleButton x:Name="LogFold" Style="{StaticResource Fold}">
              <TextBlock Text="기록 펼치기" Foreground="{StaticResource Accent}"/>
            </ToggleButton>
            <TextBox x:Name="Log" Visibility="Collapsed" Margin="0,8,0,0" Height="200" IsReadOnly="True" TextWrapping="NoWrap"
                     VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Auto"
                     Background="#1E1E1E" Foreground="#DCDCDC" BorderThickness="0" Padding="8,6" FontFamily="Consolas" FontSize="12"/>
          </StackPanel>
        </Border>

        <!-- 연결 — 게이트웨이 · 키(사내) · 내 저장소 주소 -->
        <Border x:Name="ConnCard" Style="{StaticResource Card}">
          <StackPanel>
            <TextBlock Text="연결" Style="{StaticResource CardTitle}" Margin="0,0,0,8"/>
            <Grid x:Name="KeyGrid">
              <Grid.ColumnDefinitions><ColumnDefinition Width="86"/><ColumnDefinition/></Grid.ColumnDefinitions>
              <Grid.RowDefinitions><RowDefinition/><RowDefinition/><RowDefinition/></Grid.RowDefinitions>
              <TextBlock x:Name="GwLabel" Text="주소" Style="{StaticResource Note}" FontSize="13" VerticalAlignment="Center" Margin="0,0,0,8" Visibility="Collapsed"/>
              <TextBox x:Name="GwBox" Grid.Column="1" Margin="0,0,0,8" Visibility="Collapsed"/>
              <TextBlock Grid.Row="1" Text="API 키" Style="{StaticResource Note}" FontSize="13" VerticalAlignment="Center"/>
              <PasswordBox x:Name="KeyBox" Grid.Row="1" Grid.Column="1"/>
              <TextBlock x:Name="KeyHint" Grid.Row="2" Grid.Column="1" Style="{StaticResource Note}" Margin="0,6,0,0" TextWrapping="NoWrap" TextTrimming="CharacterEllipsis"/>
            </Grid>
            <DockPanel Margin="0,14,0,4">
              <TextBlock x:Name="RepoLabel" Text="내 저장소 받기" DockPanel.Dock="Left"/>
              <TextBlock x:Name="RepoWhat" Style="{StaticResource Note}" VerticalAlignment="Center" Margin="10,0,0,0" TextWrapping="NoWrap" TextTrimming="CharacterEllipsis"
                         Text="적은 저장소를 받아 둡니다 — 내 설정은 설정 저장소로 옮깁니다"/>
            </DockPanel>
            <TextBox x:Name="RepoBox"/>
            <DockPanel Margin="0,4,0,0">
              <StackPanel DockPanel.Dock="Right" Orientation="Horizontal" VerticalAlignment="Center" Margin="10,0,0,0">
                <Button x:Name="LnkRepo" Style="{StaticResource Link}" Content="받는자리" FontSize="12"/>
                <TextBlock Text="  ·  " Style="{StaticResource Note}"/>
                <Button x:Name="LnkHowto" Style="{StaticResource Link}" Content="설정저장소 만드는 법" FontSize="12"/>
              </StackPanel>
              <TextBlock x:Name="RepoNote" Style="{StaticResource Note}" TextWrapping="NoWrap" TextTrimming="CharacterEllipsis" Text="저장소 주소를 붙여 넣습니다 · 여러 개는 빈칸으로"/>
            </DockPanel>
          </StackPanel>
        </Border>

        <!-- 설치할 도구 -->
        <Border x:Name="ToolsCard" Style="{StaticResource Card}">
          <StackPanel>
            <TextBlock Text="설치할 도구" Style="{StaticResource CardTitle}" Margin="0,0,0,8"/>
            <!-- 두 칸 고정 판 — 글자 폭(배지 · 긴 이름)이 줄바꿈을 정하면 자리마다 줄 수가 달라진다(결정 0167 의 한 판) -->
            <UniformGrid x:Name="AppChips" Columns="2"/>
            <TextBlock x:Name="AppNote" Style="{StaticResource Note}"/>
            <CheckBox x:Name="VscBox" Margin="0,10,0,0">
              <TextBlock TextWrapping="Wrap"><Run Text="VS Code 와 켠 것의 확장도 깝니다"/><Run x:Name="VscWhy" Foreground="#5F5F5F" FontSize="12"/></TextBlock>
            </CheckBox>
          </StackPanel>
        </Border>

        <!-- 자세히 설정 — 기본값이 맞는 손잡이들. 접혀도 머리에 지금 값을 한 줄로 보인다 -->
        <Border x:Name="AdvCard" Style="{StaticResource Card}" Padding="16,10">
          <StackPanel>
            <ToggleButton x:Name="AdvFold" Style="{StaticResource Fold}">
              <Grid>
                <Grid.ColumnDefinitions><ColumnDefinition Width="Auto"/><ColumnDefinition/></Grid.ColumnDefinitions>
                <TextBlock Text="자세히 설정" FontWeight="SemiBold" VerticalAlignment="Center"/>
                <TextBlock x:Name="AdvSummary" Grid.Column="1" Style="{StaticResource Note}" VerticalAlignment="Center" TextAlignment="Right" Margin="12,0,0,0" TextWrapping="NoWrap" TextTrimming="CharacterEllipsis"/>
              </Grid>
            </ToggleButton>
            <StackPanel x:Name="AdvBody" Visibility="Collapsed" Margin="21,10,0,4">
              <CheckBox x:Name="AutoBox">
                <TextBlock TextWrapping="Wrap" Text="로그온할 때와 밤마다 깔린 것을 최신으로 올리고 환경을 맞춥니다 (하루 한 번)"/>
              </CheckBox>
              <CheckBox x:Name="UpgBox">
                <TextBlock TextWrapping="Wrap"><Run Text="이미 깔린 것도 최신으로 올립니다"/><Run x:Name="UpgWhy" Foreground="#5F5F5F" FontSize="12"/></TextBlock>
              </CheckBox>
              <TextBlock x:Name="CfgLabel" Text="규범 · 룰 · 스킬을 받을 모델" Margin="0,12,0,2"/>
              <TextBlock x:Name="CfgSource" Style="{StaticResource Note}" Margin="0,0,0,2" Height="32" TextTrimming="CharacterEllipsis"><Run x:Name="CfgSourceText"/><Run Text="  "/><Hyperlink x:Name="LnkCfgDoc" Foreground="#005FB8" TextDecorations="{x:Null}" FontWeight="SemiBold" Cursor="Hand"><Run Text="?"/></Hyperlink></TextBlock>
              <WrapPanel x:Name="PersPanel"/>
              <!-- 늘 서는 한 줄 알림 칸(결정 0167 의 박힌 자리) -->
              <TextBlock x:Name="CfgTested" Style="{StaticResource Note}" TextWrapping="NoWrap" TextTrimming="CharacterEllipsis" Margin="0,2,0,0"
                         Text="Claude 에 최적화되어 있습니다 — Codex · agy 에서도 받아 씁니다"/>
            </StackPanel>
          </StackPanel>
        </Border>
      </StackPanel>
    </ScrollViewer>
  </DockPanel>
</Window>
'@
$F = [Windows.Markup.XamlReader]::Load((New-Object System.Xml.XmlNodeReader $ScreenXaml))
function Get-El([string]$Name) { $F.FindName($Name) }
# 색 — 판정 글과 배지가 쓴다
$Brush = @{}
foreach ($kv in @{ Ok = '#0F7B0F'; Bad = '#A4262C'; Warn = '#9D5D00'; Muted = '#5F5F5F'; Ink = '#1B1B1B'
                   OkBg = '#DFF6DD'; BadBg = '#FDE7E9'; GreyBg = '#EBEBEB'; OkInk = '#0F5A0F'; Grey = '#8A8A8A' }.GetEnumerator()) {
  $Brush[$kv.Key] = (New-Object Windows.Media.BrushConverter).ConvertFromString($kv.Value)
}

# ── 칸의 낱말 — **설치 로직이 쓰는 이름은 도구를 안 탄다** ─────────────────────────
# `Add-FormFace <칸>` — 칸에 `Enabled` · `Checked`(켜고 끄는 칸) · `Text`(가린 키 칸 · 단추) 를 그 칸의 WPF 이름(`IsEnabled` ·
#   `IsChecked` · `Password` · `Content`)으로 잇는다. 내는 것 없음.
# ⚠ **[설치 시작]이 넘길 값을 모으는 문장 · 칸의 첫 상태를 짓는 문장은 이 낱말로 쓴다.** 그 문장들은 회차 기록 · 자리 · 자동 실행
#   검사(claude-config `check-dist-records` · `-site` · `-stall-guard`)가 이 파일에서 떼어 같은 낱말의 대역 칸 위에 돌린다 — WPF 이름을
#   그대로 쓰면 검사의 대역과 창이 다른 말을 해, 검사가 초록이어도 창이 무엇을 넘기는지는 아무도 안 잰 것이 된다.
function Add-FormFace($El) {
  Add-Member -InputObject $El -MemberType ScriptProperty -Name Enabled -Force `
    -Value { [bool]$this.IsEnabled } -SecondValue { param($v) $this.IsEnabled = [bool]$v }
  if ($El -is [Windows.Controls.Primitives.ToggleButton]) {
    Add-Member -InputObject $El -MemberType ScriptProperty -Name Checked -Force `
      -Value { [bool]$this.IsChecked } -SecondValue { param($v) $this.IsChecked = [bool]$v }
  }
  if ($El -is [Windows.Controls.PasswordBox]) {
    Add-Member -InputObject $El -MemberType ScriptProperty -Name Text -Force `
      -Value { [string]$this.Password } -SecondValue { param($v) $this.Password = [string]$v }
  }
  if ($El -is [Windows.Controls.Button]) {
    Add-Member -InputObject $El -MemberType ScriptProperty -Name Text -Force `
      -Value { [string]$this.Content } -SecondValue { param($v) $this.Content = [string]$v }
  }
}

# 제목이 판을 든다 — 사람이 「내가 몇 판을 들고 있나」를 볼 자리다(제목줄 · 머리의 알약).
$F.Title = if ($DistVersion) { "$AppName — $DistVersion" } else { $AppName }
(Get-El 'AppTitle').Text = $AppName
if ($DistVersion) { (Get-El 'VerText').Text = $DistVersion } else { (Get-El 'VerPill').Visibility = 'Collapsed' }
# 제목줄과 작업표시줄의 얼굴 — 없으면 파워셸 아이콘이 서서 「이게 무슨 창인가」를 한 번 더 묻게 한다. 파일이 없거나 못 읽으면 그냥
#   간다 — 그림 한 장 때문에 설치를 막지 않는다.
$IconPath = Join-Path $Here 'setup-icon.ico'
if (Test-Path -LiteralPath $IconPath) {
  try { $F.Icon = [Windows.Media.Imaging.BitmapFrame]::Create((New-Object Uri $IconPath)) } catch { }
}
# 창은 화면의 일하는 자리보다 길어지지 않는다 — 넘치면 몸만 스크롤하고 아래 띠(단추)는 늘 보인다. 「자세히 설정」을 펼쳐 창이 자라
#   아래로 넘치면 위로 올린다. 값은 WPF 단위(1/96 인치)라 배율을 따로 셈하지 않는다.
$F.MaxHeight = [Windows.SystemParameters]::WorkArea.Height
$F.Add_SizeChanged({
  $wa = [Windows.SystemParameters]::WorkArea
  if ($F.Top + $F.ActualHeight -gt $wa.Bottom) { $F.Top = [Math]::Max($wa.Top, $wa.Bottom - $F.ActualHeight) }
})

# ── 값 ──────────────────────────────────────────────────────────────────────────
# 주소는 사람이 넣을 것이 아니다 — 회사 안에서 모두 같은 값이라 입력칸으로 두면 저마다 다르게 칠 자리를 연다(한 글자만
#   달라도 안 닿는데 화면은 멀쩡하다). 값이 같이 왔으면 보여만 주고, 안 왔을 때만 입력칸으로 뜬다. 진본은 `install.env` 다.
$urlPreset = [string]$Preset['ANTHROPIC_BASE_URL']

# 자리가 값보다 먼저다 — 배포본은 사내 값을 들고 오는데 그 폴더를 사외 PC 에서 돌리기도 한다. 그때 주소와 키를 물으면 안 쓸
#   것을 넣으라는 꼴이고, 넣으면 안 닿는 곳을 가리킨 채 「설정됐다」로 보인다. 자리는 위 `-Describe` 가 준 것이다(몸통의 `Measure-Site`).
#   자리를 못 정한 판은 사외가 아니다 — 칸은 사내 꼴로 서고 설치는 안 받는다(아래 「자리를 못 정한 판」).
$offsite = ($Site -eq 'outside')
$noAsk = $offsite

# ⚠ **판은 하나다 — 자리가 칸을 세우거나 걷지 않는다**(claude-config 결정 0167). 자리가 가르는 칸은 제자리에 둔 채 잠그고 짧은
#   까닭을 단다. 자리를 말하는 것은 머리의 배지 하나다 — 칸 안에서 자리 · 주소를 다시 말하지 않는다(주소는 창 어디에도 안 띄운다).
# 머리의 자리 배지 — 몸통이 잰 판정을 그대로 보인다.
$siteBadge = Get-El 'SiteBadge'; $siteDot = Get-El 'SiteDot'; $siteText = Get-El 'SiteText'
if ($Site -eq 'inside') {
  $siteBadge.Background = $Brush.OkBg; $siteDot.Fill = $Brush.Ok; $siteText.Foreground = $Brush.OkInk
  $siteText.Text = '사내 — 회사 게이트웨이로 붙습니다'
} elseif ($offsite) {
  $siteBadge.Background = $Brush.GreyBg; $siteDot.Fill = $Brush.Grey; $siteText.Foreground = $Brush.Muted
  $siteText.Text = '사외 — 개인 구독으로 씁니다'
} else {
  $siteBadge.Background = $Brush.BadBg; $siteDot.Fill = $Brush.Bad; $siteText.Foreground = $Brush.Bad
  $siteText.Text = '자리를 못 정했습니다'
}

# 주소 칸은 짐이 주소를 안 들 때만 선다 — 자리가 아니라 짐이 가른다(사내 · 사외가 같은 판이다). 짐이 들면 보여 주지도 않는다 — 그
#   값은 이 PC 의 로컬 프록시 자리라 사람이 볼 까닭이 없다. 안 들 때 지난번에 친 주소(몸통의 기록)를 넣어 둔다 — 키 칸이 이 기계에
#   심긴 키를 넣어 두는 것과 같은 결이다. 사외는 칸을 잠그고 비운다(아래 키 칸과 같다).
$tUrl = $null
if (-not $urlPreset) {
  $gwBox = Get-El 'GwBox'
  (Get-El 'GwLabel').Visibility = 'Visible'; $gwBox.Visibility = 'Visible'
  if ($noAsk) { $gwBox.IsEnabled = $false } else { $tUrl = $gwBox; $tUrl.Text = $Saved.GatewayUrl }
}

$tKey = $null
$defaultKey = [string]$Preset['ANTHROPIC_AUTH_TOKEN']
if (-not $defaultKey) {
  # 이미 심긴 회사 키를 읽어 온다 — 파일에 없어도 환경에 있으면 다시 칠 까닭이 없다.
  # ⚠ **같은 이름만 본다.** `OPENAI_API_KEY` · `GEMINI_API_KEY` 는 회사 키에서 파생된 사본이지 진본이 아니라(몸통의 「회사
  #   키의 다른 이름 둘」 칸이 한 방향으로만 심는다), 거꾸로 읽으면 제 OpenAI 키를 넣어 둔 사람의 값이 이 칸에 들어온다 — 칸이
  #   가려져 있어 **무엇이 찼는지 본인도 못 본다.** 몸통이 `GOOGLE_API_KEY` 에 대고 세운 「남의 값은 안 걷는다」와 같은 축이다.
  $defaultKey = [Environment]::GetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'User')
  if (-not $defaultKey) { $defaultKey = $env:ANTHROPIC_AUTH_TOKEN }
}
# 키 칸은 어느 자리에서나 선다 — 사외는 잠그고 비운 채 짧은 까닭만 단다(자리를 다시 말하지 않는다 · 그 말은 배지가 든다).
$keyHint = Get-El 'KeyHint'
if ($noAsk) {
  (Get-El 'KeyBox').IsEnabled = $false
  $keyHint.Text = '사외에서는 안 씁니다'
} else {
  $tKey = Get-El 'KeyBox'
  Add-FormFace $tKey
  $tKey.Text = [string]$defaultKey
  # 「채워져 있다」는 둘 다 찼을 때만 하는 말이다 — 주소가 빈 채로 「바로 누르면 된다」고 하면, 누른 사람은 [설치 시작]의
  #   「둘 다 넣거나 둘 다 비워야」에 막혀 안내가 거짓이 된다. 맡겨 둔 회사 키(`$KeySaved`)가 있으면 키 칸이 비어도 그 막음이 안 선다.
  #   짐이 주소를 들면 주소 칸이 없으니 주소를 말하지 않는다.
  $urlShown = if ($urlPreset) { $urlPreset } else { $Saved.GatewayUrl }
  $keyHint.Text = if ($defaultKey -and $urlPreset) { 'API 키가 채워져 있습니다 — 바로 [설치 시작]을 누르면 됩니다.' }
                  elseif ($defaultKey -and $urlShown) { '주소와 API 키가 채워져 있습니다 — 바로 [설치 시작]을 누르면 됩니다.' }
                  elseif ($KeySaved -and $urlShown) { '키를 비워 두면 이 PC 에 맡겨 둔 회사 키를 씁니다 — 바로 누르면 됩니다.' }
                  elseif ($urlPreset)  { 'API 키를 넣습니다.' }
                  elseif ($urlShown)   { '주소는 채워져 있습니다 — API 키만 넣으면 됩니다.' }
                  elseif ($defaultKey) { 'API 키는 이 기계에 있던 것을 넣었습니다 — 사내면 주소를 넣습니다.' }
                  elseif ($KeySaved)   { '사내면 주소를 넣습니다 — 키는 이 PC 에 맡겨 둔 것을 씁니다.' }
                  else                 { '사내면 주소와 키를 넣습니다.' }
}
$keyHint.ToolTip = $keyHint.Text   # 한 줄 칸이라 잘린 글의 전문

# ── 내 저장소 주소 (선택) — 「연결」 칸 ─────────────────────────────────────────
# 이 칸이 드는 일은 저장소를 「받아 둔다」 하나다 — 훅을 든 설정 저장소를 전제로 이름 짓지 않는다. 보통 사람은 그런 저장소가
#   없고, 이름이 전제를 깔면 안 맞는 사람이 「나는 못 쓰는 칸」으로 읽고 지나친다.
# 넣어도 위 키 칸은 그대로 산다 — 설치는 자리만 보고 전부 세우고 저장소는 그 뒤에 받는다. 받은 뿌리에 SessionStart 훅
#   (`.claude/hooks/session-start.sh`)이 있으면 `--install` 로 불러 사람에게 딸린 것을 잇게 하고, 없으면 받아 둔 것으로 끝난다.
# 여럿은 빈칸으로 가른다 — 주소에는 빈칸이 없다. 배포본에는 이 값이 안 실려 온다 — 남에게 갈 파일에 내 저장소 주소를 박지 않는다.
# 글에 「git 주소」 · 「GitHub 주소」라 적지 않는다 — 설치는 `git clone` 을 그대로 불러 사내 GitLab 같은 주소도 받으므로
#   「GitHub」는 코드보다 좁고, `git` 은 도구 이름이라 사람이 제 주소가 그건지 못 가른다. 사람이 하는 일(저장소 페이지 주소를
#   붙여 넣기)을 적는다.
$tRepo = Get-El 'RepoBox'
# ⚠ **지난번에 넣은 주소(몸통의 기록)로 채운다 — 기록이 없을 때만 옆에 온 값 파일을 본다.** 키 칸이 환경변수로 되돌아가는 것과
#   같은 결이다. 이 주소는 배포본에 안 실려 와 한 번 넣은 사람에게만 있다. 칸이 비어 뜨고 그대로 누르면 **그 판은 저장소를 안
#   본다** — `config-repo` 는 화면이 적는 이름이라(아래 [설치 시작]) 빈 칸이 곧 「저장소 없음」이고, 몸통은 그것을 다음 회차의 기록으로 남긴다.
$tRepo.Text = if ($null -ne $Saved.Repo) { [string]$Saved.Repo } else { [string](Read-Directive $EnvPath 'config-repo') }

# ── 옵션 칸 ─────────────────────────────────────────────────────────────────────
# 제품 칸의 글자도 기본값도 몸통이 준 것을 그대로 쓴다 — 여기서 다시 지으면 두 벌이 된다. 한 칸이 그 제품의 CLI · 확장 ·
# 데스크탑 앱을 통째로 든다 — 확장은 아래 VS Code 칸까지 켜야 선다. **뺀 것은 아무 데도 안 깔린다.** 이 자리에서 안 내놓는 제품
# (사내의 Copilot)은 몸통이 `product-here|키|no` 를 내 칸을 잠근다(아래 `$NotHere`).
$cApps = @()
$cVsc  = $null
$chips = Get-El 'AppChips'
if ($Choices.Count) {
  foreach ($choice in $Choices) {
    $c = New-Object Windows.Controls.Primitives.ToggleButton
    $c.Style = $F.FindResource('Chip')
    $c.Content = $choice.Label
    $c.Tag = $choice.Key
    Add-FormFace $c
    $c.Checked = if ($null -ne $Saved.Pick) { $Saved.Pick -contains $choice.Key } else { [bool]$choice.On }
    # 이 자리에서 안 내놓는 제품 — 칸은 제자리에 두고 잠그며 「사내 지원 전」 배지를 단다. 고른 기록은 그대로 보이고 그대로 넘어간다 —
    #   몸통이 이 자리에서는 안 깔고 기록은 둔다(`$PickHeld`). 사람이 여기서 못 바꾸는 것은 지금까지와 같다.
    if ($NotHere[$choice.Key]) {
      $c.Enabled = $false
      $face = New-Object Windows.Controls.StackPanel; $face.Orientation = 'Horizontal'
      $name = New-Object Windows.Controls.TextBlock; $name.Text = $choice.Label; $name.VerticalAlignment = 'Center'
      $badge = New-Object Windows.Controls.Border; $badge.Background = $Brush.GreyBg; $badge.CornerRadius = New-Object Windows.CornerRadius(8)
      $badge.Padding = New-Object Windows.Thickness(6, 0, 6, 1); $badge.Margin = New-Object Windows.Thickness(8, 0, 0, 0)
      $badgeText = New-Object Windows.Controls.TextBlock; $badgeText.Text = '사내 지원 전'; $badgeText.FontSize = 11; $badgeText.Foreground = $Brush.Muted
      $badge.Child = $badgeText
      [void]$face.Children.Add($name); [void]$face.Children.Add($badge)
      $c.Content = $face
      $c.ToolTip = '이 자리에서는 안 깝니다 — 고른 기록은 그대로 둡니다.'
      [Windows.Controls.ToolTipService]::SetShowOnDisabled($c, $true)
    }
    [void]$chips.Children.Add($c)
    $cApps += ,$c
  }

  # 제품 칸이 까는 것은 바로 그 줄 아래 적는다 — 확장은 빼고. 확장은 VS Code 칸이 켜졌을 때만 깔리므로 그 칸의 글이 든다.
  #   이 줄이 VS Code 칸 아래 서면 그 칸의 설명으로 읽혀 「VS Code 를 켜면 CLI · 데스크탑 앱이 깔린다」로 보인다.
  # 고르기는 자리를 안 가리는데 깔기는 가린다(데스크탑 앱을 사외에서만 까는 행) — 안 적으면 사내에서 켜 놓고 「왜 안 깔렸지」가 된다.
  # 글은 몸통이 행마다 낸 답(`-Describe` 의 `app|키|yes·outside·no` — 몸통의 `Test-DesktopAppHere`)에서 짓는다 — 짐의 `#desktop-app`
  #   과 행의 `When` 을 창이 따로 풀면 사내에서도 깔리는 행에 「사외에서만」이라 적는다(PAISetup #46 ⑤).
  # 이 자리에서 안 내놓는 제품은 세지 않는다 — 그 칸은 잠겨 아무것도 안 깔린다.
  $appYes = @($Choices | Where-Object { -not $NotHere[$_.Key] -and $AppHere[$_.Key] -eq 'yes' })
  $appOut = @($Choices | Where-Object { -not $NotHere[$_.Key] -and $AppHere[$_.Key] -eq 'outside' })
  (Get-El 'AppNote').Text = if (-not $appYes.Count -and -not $appOut.Count) {
    '켠 것의 CLI 가 깔립니다.'
  } elseif (-not $appOut.Count) {
    '켠 것의 CLI · 데스크탑 앱이 깔립니다.'
  } elseif (-not $appYes.Count) {
    '켠 것의 CLI 가 깔립니다 — 데스크탑 앱은 사외에서만 깔립니다.'
  } else {
    "켠 것의 CLI 가 깔립니다 — 데스크탑 앱은 사외에서만 ($(@($appYes | ForEach-Object { $_.Label }) -join ' · ') 만 여기서도)"
  }

  # 필수인 자리(사내)는 켠 채로 잠근다 — 몸통이 칸과 상관없이 깐다(`-Describe` 의 `vscode|required` · 몸통의 `Test-VsCodeRequired`).
  #   글에 「필수」라 적었으니 못 꺼야 그 글이 참이다. 잠근 칸은 사람의 값을 안 바꾼다 — [설치 시작]은 지난번에 고른 것을 그대로 넘겨
  #   기록이 사외에서 다시 선다.
  # 필수가 아닌 자리의 기본은 끔이다 — 데스크탑 앱만으로 서는 자리라 VS Code 를 안 받아도 된다. 지난번에 고른 것(`$Saved`)이 있으면
  #   그것을 따른다.
  $cVsc = Get-El 'VscBox'
  Add-FormFace $cVsc
  (Get-El 'VscWhy').Text = if ($VsRequired) { '  · 사내는 필수' } elseif ($offsite) { '  · 사외는 선택' } else { '  · 사내는 필수, 사외는 선택' }
  $cVsc.Checked = if ($VsRequired) { $true } elseif ($null -ne $Saved.NoVsCode) { -not $Saved.NoVsCode } else { $false }
  $cVsc.Enabled = -not $VsRequired
} else {
  (Get-El 'ToolsCard').Visibility = 'Collapsed'
}

# 로그온할 때 · 밤마다 자동 실행 — 작업 스케줄러가 로그온 때와 매일 새벽 설치 몸통을 다시 돌려(작업 이름은 몸통의
#   `$AutoRunTaskName` · `$AutoRunNightTaskName`) 깔린 것을 최신으로 올리고 환경을 다시 맞춘다 — 하루 한 번. 설치본 자신도 `#update-repo` 의 최신 릴리스를
#   받아 지문을 대조한 뒤 그 판으로 간다(몸통의 「부팅 시 자동 실행」 칸).
# 글에 「백그라운드」라고 적지 않는다 — 로그온 회차가 설치를 실제로 하면 작은 진행 창이 떠서 도는 것이 보인다.
# 칸의 첫 상태는 몸통이 깃발 없는 판에 내릴 답이다(`-Describe` 의 `autorun|on·off` — 몸통의 `Get-AutoRunDefault`) — 작업이 서
#   있나 · 짐의 `#autorun` · 사람이 끈 기록을 창이 따로 읽어 규칙을 다시 지으면 지시가 `no` 인 판에서 창은 켠 채 뜨고 로그온 회차는
#   걷는다(PAISetup #46 ③). 몸통에 못 물은 판은 꺼진 채 뜬다 — 그 판은 설치를 안 받는다.
$cAuto = Get-El 'AutoBox'
Add-FormFace $cAuto
$cAuto.Checked = $AutoRunOn

# 이미 깔린 것도 올리는 칸(기본 켬) — 집 · 회사 PC 처럼 프로필이 남는 기계는 프로그램이 이미 다 있어, 「있으면 건너뛴다」만
#   두면 판이 영영 안 올라간다. 비영속 VDI 는 늘 맨바닥이라 이 칸이 안 걸린다.
# 괄호는 이 칸이 못 막는 하나다 — 몸통의 `-NoUpgrade` 칸별 설명과 같은 말이고, 판은 몸통의 `$VcRuntimeMin` 을 `-Describe` 로 받는다.
$cUpg = Get-El 'UpgBox'
Add-FormFace $cUpg
if ($VcRuntimeMin) { (Get-El 'UpgWhy').Text = "  · 꺼도 VC++ 런타임은 $VcRuntimeMin 아래면 올립니다" }
$cUpg.Checked = -not $NoUpgrade

# 제작자 칸 — **도구마다 고른다**(결정 0099). 칸 이름은 하는 일(「규범 · 룰 · 스킬을 받을 모델」)로 박고, 무엇이 가나(출처)는 칸
#   바로 아래 한 줄이 저장소 칸을 따라 말한다(`Sync-PersonalSource`) — 같은 칸이 저장소 주소 하나로 뜻이 바뀌는데(결정 0107: 비면
#   설치 묶음의 제작자 세트, 차면 설치 끝에 그 저장소의 배포가 고른 도구 홈에 푼다) 그것이 화면에 안 보이면 숨은 설정이 된다(#53).
#   고른 것은 몸통이 사용자 환경변수 `PAISETUP_PERSONAL` 로 심어 설정 저장소의 배포 · 세션 훅도 같은 값을 따른다.
# **첫 상태 — 기록이 있으면 기록, 없으면 Claude 만 켠다**(#52 마감). Claude 가 주로 일하는 도구라 처음 온 사람도 규율을 받고,
#   가끔 맡기는 도구(Codex · agy)는 부를 때 가볍게 둔다. 다 끈 기록(`personal=none`)도 기록이다 — 기록이 없는 것과 가른다.
# 제품 칸에서 안 고른 도구는 끈다 — 깔 홈이 없다. 꺼진 칸은 켜져 있어도 넘기지 않는다.
$lCfg = Get-El 'CfgLabel'
$lSrc = Get-El 'CfgSource'
$lSrcText = Get-El 'CfgSourceText'
$personalWant = if ($PersonalFor) { @($PersonalFor -split '[,\s]+' | Where-Object { $_ }) }
                elseif ($WithPersonalConfig) { @('claude') }
                elseif ($Recorded.ContainsKey('personal')) { @($Saved.Personal) }
                else { @('claude') }
$cPers = @()
$persPanel = Get-El 'PersPanel'
# 칸은 몸통의 제작자 도구 표(`-Describe` 의 `personal|도구|제품|글자` 줄)에서 짓는다 — 도구 이름 ↔ 제품은 그 표 하나가 든다.
foreach ($pt in $PersonalTools) {
  $c = New-Object Windows.Controls.CheckBox
  $c.Content = $pt.Label
  $c.Margin = New-Object Windows.Thickness(0, 2, 18, 2)
  $c.Tag = $pt
  Add-FormFace $c
  $c.Checked = $personalWant -contains $pt.Key
  [void]$persPanel.Children.Add($c)
  $cPers += ,$c
}
# `Test-PersonalBoxLive <제작자 칸>` → 그 칸이 지금 사나: 짝 제품 칸을 골랐나(제품 칸이 없는 판이면 늘 참). 칸의 켜짐
#   (`Sync-PersonalBoxes`)과 [설치 시작]이 넘길 값이 둘 다 이 함수에 묻는다.
# ⚠ **넘길 값을 칸의 `Enabled` 로 고르지 않는다** — 칸을 잠그는 판([설치 시작]이 도는 동안)에 켜짐이 거짓으로 읽혀, 무엇을 골라도
#   빈 값이 넘어간다.
function Test-PersonalBoxLive($c) {
  $prod = @($cApps | Where-Object { [string]$_.Tag -eq $c.Tag.Pick }) | Select-Object -First 1
  return [bool]((-not $cApps.Count) -or ($prod -and $prod.Checked))
}
# 제품 칸과 묶는다 — 그 제품을 끄면 이 칸도 꺼진다(고른 값은 남아 다시 켜면 돌아온다)
function Sync-PersonalBoxes {
  foreach ($c in $cPers) { $c.Enabled = Test-PersonalBoxLive $c }
}

# `Get-RepoName <저장소 칸 글>` → 첫 주소의 저장소 이름(끝마디 · `.git` 뗌), 여럿이면 「이름 외 N개」, 비었으면 ''.
function Get-RepoName([string]$Urls) {
  $u = @("$Urls".Trim() -split '\s+' | Where-Object { $_ })
  if (-not $u.Count) { return '' }
  $n = (($u[0].TrimEnd('/') -split '[/:\\]') | Where-Object { $_ } | Select-Object -Last 1) -replace '\.git$', ''
  if ($u.Count -gt 1) { "$n 외 $($u.Count - 1)개" } else { $n }
}
# 접힌 머리의 한 줄 — 자동 실행(작업 스케줄러에 작업을 세우는 일이라 맨 앞) · 올리기 · 규범이 어느 도구에 어디서 가나.
$advSummary = Get-El 'AdvSummary'
# 제작자 세트는 Claude 에 맞춰 지었다 — 그 말은 칸 아래 한 줄이 늘 같은 색으로 든다(알림이지 경고가 아니다).
(Get-El 'CfgTested').ToolTip = (Get-El 'CfgTested').Text
function Update-AdvSummary {
  $pers = @($cPers | Where-Object { $_.Checked -and (Test-PersonalBoxLive $_) } | ForEach-Object { [string]$_.Content })
  $src  = if (Get-RepoName $tRepo.Text) { '내 저장소' } else { '제작자' }
  $advSummary.Text = @(
    $(if ($cAuto.Checked) { '자동 업데이트 켬' } else { '자동 업데이트 끔' })
    $(if ($cUpg.Checked) { '깔린 것도 올림' } else { '깔린 것은 둠' })
    $(if ($pers.Count) { "규범: $($pers -join ' · ') ← $src" } else { '규범: 안 받음' })
  ) -join '  ·  '
  $advSummary.ToolTip = $advSummary.Text
}
# 출처 줄 — 무엇이 깔리나를 한 문장으로, 저장소 칸을 따라 바뀐다. 칸 이름은 그대로다.
function Sync-PersonalSource {
  $name = Get-RepoName $tRepo.Text
  $lSrcText.Text = if ($name) { "설정 저장소를 넣었으니, 고른 모델에 내 규범 · 룰 · 스킬($name)이 깔립니다" }
               else { '설정 저장소를 넣지 않았으니, 고른 모델에 제작자의 규범 · 룰 · 스킬이 깔립니다' }
  $lSrc.ToolTip = "$($lSrcText.Text)`n`n$cfgTip"
  Update-AdvSummary
}
foreach ($a in $cApps) { $a.Add_Click({ Sync-PersonalBoxes; Update-AdvSummary }) }
foreach ($b in @($cAuto, $cUpg) + $cPers) { $b.Add_Click({ Update-AdvSummary }) }
$tRepo.Add_TextChanged({ Sync-PersonalSource })

# 접는 칸 둘
$advFold = Get-El 'AdvFold'; $advBody = Get-El 'AdvBody'
$advFold.Add_Click({ $advBody.Visibility = $(if ($advFold.IsChecked) { 'Visible' } else { 'Collapsed' }) })
$log = Get-El 'Log'; $logFold = Get-El 'LogFold'
$logFold.Add_Click({ $log.Visibility = $(if ($logFold.IsChecked) { 'Visible' } else { 'Collapsed' }) })

# ── 후버로 조금 더 내린다 ────────────────────────────────────────────────────────
# 툴팁은 「무엇을 하는 칸인가」와 갈래 둘, 그리고 더 볼 데가 있다는 것만 든다 — 자세한 것은 옆 링크의 안내 한 장이 든다. 같은
#   글을 두 벌 두면 고칠 때 한쪽만 고쳐진다. 꺼진 칸에도 뜬다(`ShowOnDisabled`).
$tipText = @'
적은 git 저장소를 이 PC 로 받습니다 — 코드 저장소도, 설정 저장소도.
저장소마다 내 폴더 아래 repos\<저장소 이름> 으로 받고, 「받는자리」가 그 폴더를
열어 보여 줍니다. 여러 개는 빈칸으로 가릅니다. 프로그램·확장·CLI·키·프록시는
이 칸과 상관없이 다 깔립니다.

코드 저장소는 받아 두는 것으로 끝입니다. 설정 저장소만 한 걸음 더 갑니다:

받은 뒤 갈래가 둘이고 둘 다 정당합니다. 가르는 자는 파일 이름 하나 —
받아온 저장소 뿌리의 .claude/hooks/session-start.sh 입니다.

  · 든 저장소가 있으면  --install 로 부릅니다. 그 뒤는 그 저장소가 잇습니다
  · 어디에도 없으면      받아 둔 것으로 끝냅니다

설정 저장소가 무엇이고 어떻게 만드나는 「설정저장소 만드는 법」이 한 장으로 답합니다.
'@
$cfgTip = @'
고른 모델의 홈에 규범 · 룰 · 스킬을 놓습니다. 「설치할 도구」에서 고른 것만 켜집니다.
설정 저장소를 넣으면 내 것이, 안 넣으면 제작자의 것이 깔립니다 — 넣었으면 설치 끝에
그 저장소의 deploy 가 고른 모델의 홈에 그 저장소의 것을 풉니다. 끈 모델에는 어느 쪽도
안 갑니다.
'@
foreach ($t in @(@{ El = $tRepo; Text = $tipText }, @{ El = (Get-El 'RepoWhat'); Text = $tipText }, @{ El = (Get-El 'RepoNote'); Text = $tipText },
                 @{ El = $lCfg; Text = $cfgTip }, @{ El = $lSrc; Text = $cfgTip })) {
  $t.El.ToolTip = $t.Text
  [Windows.Controls.ToolTipService]::SetShowDuration($t.El, 30000)   # 긴 글이라 오래 띄운다
  [Windows.Controls.ToolTipService]::SetShowOnDisabled($t.El, $true)
}

# ── 링크 — 파일 · 폴더 · 페이지를 연다 ───────────────────────────────────────────
# 링크 글은 「무엇이 있는 데인가」만 든다 — 「열기」 · 「위치」를 안 붙인다. 없으면 무엇이 어디에 없는지를 경로까지 대고 말한다 —
#   눌렀는데 아무 일도 안 나면 사람은 「내 컴퓨터가 이상한가」에서 멈춘다.
# `Open-Thing <경로> <무엇 — 이름만, 토씨 없이> [-Folder] [-Page]` — 폴더는 탐색기로, 페이지(`.html`)는 기본 브라우저(`Open-InBrowser`)로, 나머지는 그
#   파일의 기본 프로그램으로 연다. 없거나 못 열면 그 말을 경로와 함께 한다. 내는 것 없음.
function Open-Thing([string]$Path, [string]$What, [switch]$Folder, [switch]$Page) {
  if (-not (Test-Path -LiteralPath $Path)) {
    [void][Windows.MessageBox]::Show($F, "$What — 이 폴더에 없습니다" + [Environment]::NewLine + $Path, $AppName, 'OK', 'Warning')
    return
  }
  try {
    if ($Folder) { Start-Process -FilePath 'explorer.exe' -ArgumentList ('"' + $Path + '"') | Out-Null }
    elseif ($Page -and (Get-Command Open-InBrowser -ErrorAction SilentlyContinue)) { Open-InBrowser $Path }
    else { Start-Process -FilePath $Path | Out-Null }
  } catch {
    [void][Windows.MessageBox]::Show($F, "$What — 못 열었습니다: $($_.Exception.Message)" + [Environment]::NewLine + $Path,
      $AppName, 'OK', 'Warning')
  }
}

# 「알아보기」 — 누르기 전에 읽을 것 셋(제공기능 · 설치흐름 · 바뀐 것). 스위치 없이 놓이는 것(사내 문서 · 씨앗)일수록 누르기 전에 말한다 — 그 말은 「제공기능」
#   페이지가 든다(결정 0091). 무엇이 어디에 놓이나의 진본은 install.ps1 「공용 자산」 걸음과 `INSTALLED.md` 라 목록을 여기 옮기지 않는다.
(Get-El 'LnkFeat').Add_Click({ Open-Thing (Join-Path $Here 'features.html') '안내 페이지(features.html)' -Page })
# 설치 흐름 그림 — 같은 폴더의 `install-flow.svg`(README 가 든 그 그림).
(Get-El 'LnkFlow').Add_Click({ Open-Thing (Join-Path $Here 'install-flow.svg') '설치 흐름 그림(install-flow.svg)' })
# 이 판에서 바뀐 것 — 그 판의 릴리스 노트(결정 0099). 판마다 바뀐 것은 판마다 낡으므로 「제공기능」 페이지에 안 적고 릴리스가 든다.
#   주소는 값 파일의 `#update-repo` 와 곁의 `VERSION` 에서 짓는다 — 이 파일에 저장소를 안 박는다. 둘 중 하나가 없으면 링크를 안
#   세운다 — 못 짓는 주소를 열게 두지 않는다.
# 알약은 판을 다 든 릴리스 목록을 연다 — 이 판만이 아니라 앞뒤 판에서 무엇이 바뀌었나를 한 자리에서 본다. 판 하나의 노트(`$ReleasePage`)는
#   옛 제작자 칸 알림이 「이 판에서 바뀐 것」으로 쓴다. 저장소를 모르면 알약은 제자리에서 잠그고 까닭을 단다(결정 0167 의 한 판).
$ReleasePage = $null
$relRepo = Read-Directive $EnvPath 'update-repo'
if ($relRepo -and $DistVersion) { $ReleasePage = "https://github.com/$relRepo/releases/tag/v$DistVersion" }
$ReleaseList = if ($relRepo) { "https://github.com/$relRepo/releases" } else { $null }
$lnkNews = Get-El 'LnkNews'
if ($ReleaseList) {
  $lnkNews.Add_Click({
    try { Start-Process -FilePath $ReleaseList | Out-Null }
    catch {
      [void][Windows.MessageBox]::Show($F, "릴리스 목록을 못 열었습니다 — $($_.Exception.Message)", $AppName, 'OK', 'Warning')
    }
  })
} else {
  $lnkNews.IsEnabled = $false
  $lnkNews.ToolTip = '설치 묶음의 값 파일에 #update-repo 가 없어 열 곳을 모릅니다'
  [Windows.Controls.ToolTipService]::SetShowOnDisabled($lnkNews, $true)
}

# 「받는자리」 — 경로를 글자로 띄우지 않고 눌러서 열어 보여 준다. 경로는 사람마다 길이가 달라 한 줄을 넘고, `~` · `<>` 같은 기호는
#   받는 사람이 제 PC 의 어디인지 못 읽는다. 「설치 위치」라 적지 않는다 — 여기는 저장소를 받는 폴더고, 설치가 짐을 푸는 곳
#   (`%LOCALAPPDATA%\Claude Code Setup\<판>`)은 딴 데다.
# 자리를 모르면(몸통이 `config-repo-root` 를 못 내준 판) 누를 데가 없으니 글이 자리를 말하고 링크를 잠근다.
$lnkRepo = Get-El 'LnkRepo'
if ($RepoRoot) {
  $lnkRepo.Add_Click({
    # 아직 없는 것이 정상이다(저장소를 한 번도 안 받은 PC) — 여기서 만들지 않고(설치가 제 때 만든다) 그 말을 경로와 함께 한다.
    if (Test-Path -LiteralPath $RepoRoot) { Open-Thing $RepoRoot '받는자리 폴더' -Folder }
    else {
      [void][Windows.MessageBox]::Show($F, '아직 없습니다 — 주소를 넣고 설치하면 이 자리에 만들어집니다.' + [Environment]::NewLine + $RepoRoot,
        $AppName, 'OK', 'Information')
    }
  })
} else {
  $lnkRepo.IsEnabled = $false
  $lnkRepo.ToolTip = '내 폴더 아래 repos 에 받습니다'
  [Windows.Controls.ToolTipService]::SetShowOnDisabled($lnkRepo, $true)
}
# 안내 한 장 — `config-repo-howto.html` 은 이 스크립트와 같은 폴더에 같이 온다.
(Get-El 'LnkHowto').Add_Click({ Open-Thing (Join-Path $Here 'config-repo-howto.html') '설정저장소 안내(config-repo-howto.html)' })
# 출처 줄 끝의 「?」 — 곁의 `INSTALLED.md` 를 연다. 그 글의 「설치 창의 칸 › 제작자 칸」이 이 칸을 든다. 파일 하나라 그 절로 바로
#   뛰지는 못해 절 이름은 툴팁이 말한다.
$lnkCfgDoc = Get-El 'LnkCfgDoc'
$lnkCfgDoc.ToolTip = 'INSTALLED.md 를 엽니다 — 「설치 창의 칸 › 제작자 칸」'
$lnkCfgDoc.Add_Click({ Open-Thing (Join-Path $Here 'INSTALLED.md') '설치 안내(INSTALLED.md)' })

# ── 기록 폴더로 가는 문 — 아래 띠 왼쪽 ──────────────────────────────────────────
# 창을 닫은 뒤에 물어볼 거리가 남을 때의 문이다 — 기록은 회차마다 파일로 남는데(`Save-RunLog`), `%LOCALAPPDATA%` 를 손으로
#   칠 줄 모르는 사람도 화면에서 닿게 한다. 폴더만 열지 않고 가장 최근 파일(쓴 시각)을 집어 준다 — 열어 놓고 고르게 하면 지난
#   기록을 보고 말한다. 없으면 그 말을 한다(설치를 한 번도 안 돌린 PC 에서는 폴더가 없는 것이 정상이다).
(Get-El 'LnkLog').Add_Click({
  if (Test-Path -LiteralPath $LogDir) {
    # ⚠ **`/select,` 뒤에 빈칸을 두지 않는다** — explorer 는 그 꼴 그대로를 본다.
    $latest = Get-ChildItem -LiteralPath $LogDir -Filter 'install-*.log' -File -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $argv = if ($latest) { '/select,"' + $latest.FullName + '"' } else { '"' + $LogDir + '"' }
    try { Start-Process -FilePath 'explorer.exe' -ArgumentList $argv | Out-Null }
    catch {
      [void][Windows.MessageBox]::Show($F, "기록 폴더를 못 열었습니다 — $($_.Exception.Message)" + [Environment]::NewLine + $LogDir,
        $AppName, 'OK', 'Warning')
    }
  } else {
    [void][Windows.MessageBox]::Show($F, '아직 기록이 없습니다 — 설치를 한 판 돌리면 이 폴더에 남습니다.' + [Environment]::NewLine + $LogDir,
      $AppName, 'OK', 'Information')
  }
})

# ── 설치하는 중 칸 ──────────────────────────────────────────────────────────────
$bar = Get-El 'Bar'
$lState = Get-El 'State'
$runCard = Get-El 'RunCard'; $runTitle = Get-El 'RunTitle'
# `Set-Status <글> [색]` — 아래 띠의 상태 줄. 높이가 박힌 두 줄이라 긴 글은 줄임표로 끊기고 전문은 툴팁이 든다 — 알림이 창을 안 늘린다.
$statusText = Get-El 'StatusText'
function Set-Status([string]$Text, [string]$Tone = 'Ink') {
  $statusText.Text = $Text; $statusText.Foreground = $Brush[$Tone]; $statusText.ToolTip = $(if ($Text) { $Text } else { $null })
}
# `Hide-Address <글>` → 글 속의 주소(호스트 · IP · 그 뒤 `:포트`)를 「주소」로 가린 글. 파일 이름(.ps1 · .env · .exe …)은 둔다. 몸통이 낸 까닭을
#   창에 띄울 때 지난다 — 창은 주소를 어디에도 안 띄운다(결정 0167). 원문은 설치 기록 · 콘솔이 든다.
function Hide-Address([string]$Text) {
  [regex]::Replace($Text, '(?<![\w.-])(?:\d{1,3}(?:\.\d{1,3}){3}|[A-Za-z][\w-]*(?:\.[\w-]+)+)(?::\d+)?(?![\w.-])',
    { param($m) if ($m.Value -match '\.(ps1|env|exe|md|html|svg)$') { $m.Value } else { '주소' } })
}
# `Set-State <글> [색]` — 「설치하는 중」 칸의 상태 줄. 색은 `$Brush` 의 이름(Ink · Ok · Bad · Warn).
function Set-State([string]$Text, [string]$Tone = 'Ink') { $lState.Text = $Text; $lState.Foreground = $Brush[$Tone] }
# `Show-Form <켬>` — 고르는 칸들(연결 · 도구 · 자세히)을 세우거나 접는다. 도는 동안은 접어 「설치하는 중」 칸이 앞에 서고, 끝나면
#   다시 세워 [다시 설치] 앞에 고칠 수 있게 한다.
function Show-Form([bool]$On) {
  foreach ($n in 'ConnCard', 'ToolsCard', 'AdvCard') {
    $card = Get-El $n
    if ($n -eq 'ToolsCard' -and -not $Choices.Count) { continue }
    $card.Visibility = $(if ($On) { 'Visible' } else { 'Collapsed' })
  }
}

$bGo = Get-El 'BGo'
Add-FormFace $bGo
$bClose = Get-El 'BClose'

# ── 자리를 못 정한 판 — 설치를 안 받는다 ─────────────────────────────────────────
# 몸통이 자리를 못 정했으면(`site|error|까닭`) · 몸통에 못 물었으면 그 까닭을 빨갛게 띄우고 [설치 시작]을 잠근다 — 그대로 누르면 몸통도
#   같은 까닭으로 멈추고, 창이 한 갈래를 골라 넘기면 사내 PC 의 회사 연결을 걷거나 닿지 않는 주소를 심는다(PAISetup #46).
if (-not $Site) {
  $siteErr = "자리(사내 · 사외)를 못 정해 설치를 못 합니다 — 설치 묶음(Setup.exe)을 새로 받아 다시 누릅니다. 까닭: $(Hide-Address $SiteWhy)" +
             ' · 값 파일을 손으로 만들었으면 #site-probe = 호스트:포트 줄을 넣습니다.'
  Set-Status $siteErr 'Bad'
  $bGo.Enabled = $false
}

# ── 돌리는 자 ───────────────────────────────────────────────────────────────────
# 몸통의 출력을 파일로 받고 타이머가 그 파일을 **따라 읽는다.** 타이머는 창의 디스패처가 돌리므로 `ShowDialog()` 안에서도
#   산다. 읽는 쪽은 파일을 열어 둔 채 `ReadLine()` 이 null 을 낼 때까지 읽고 다음 틱에 잇는다 — 자식이 쓰는 중인 파일이라
#   공유 열기다(`Open-Tail`).
# ⚠ **`Register-ObjectEvent -Action` 을 안 쓴다.** 그 블록은 파워셸이 한가할 때만 도는데, 창이 떠 있는 동안 런스페이스는
#   `ShowDialog()` 를 실행 중이라 **창이 닫힐 때까지 핸들러가 한 번도 안 불린다** — 기록 칸이 비고, `[n/N]` 을 못 봐 막대 구간이
#   0/0 이고, 심장박동(`segHi > segLo`)도 안 선다.
$script:segLo = 0; $script:segHi = 0   # 지금 칸이 차지하는 구간 — 그 안에서 낱줄이 민다
$script:idle  = 0                     # 조용한 틱 수 — 쌓이면 막대를 천천히 민다
$script:proc = $null; $script:tmpEnv = $null
$script:sw = $null; $script:last = ''   # 흐른 시간과 마지막 줄 — 창이 살아 있음을 보인다
$script:topic = ''                      # 상태 글의 주제 — 마지막 머리 · 항목 줄. 흐름 줄은 이것을 안 갈고 뒤에 붙는다
$script:done = ''                       # 몸통이 낸 마무리 문장 — 끝났을 때 이것을 띄운다
$script:outFile = $null; $script:errFile = $null
$script:rdOut = $null;  $script:rdErr = $null

# 기록 칸에 한 줄 — 늘 끝으로 내린다(WPF 글 칸은 스스로 안 내린다).
function Add-Log([string]$line) {
  $log.AppendText($line + "`r`n")
  $log.ScrollToEnd()
}

$bGo.Add_Click({
  # 자리를 못 정한 판은 안 받는다 — 단추는 이미 잠겼고(위 「자리를 못 정한 판」), 여기는 그 잠금이 풀린 자리의 마지막 울타리다.
  if (-not $Site) { return }
  # ⚠ **비어 있는 것은 안 막는다** — 사외는 둘 다 비우는 것이 맞는 답이다. 막는 것은
  #   **반만 넣은 것** 하나다: 한쪽만 있으면 게이트웨이가 안 서는데 화면은 멀쩡해 보인다.
  #   주소만 있고 키 칸이 빈 것은 이 PC 에 맡겨 둔 회사 키(`$KeySaved`)가 있으면 반이 아니다 — 몸통이 그 키를 풀어 심는다.
  $url = if ($noAsk) { '' } elseif ($tUrl) { $tUrl.Text.Trim() } else { $urlPreset }
  $key = if ($tKey) { $tKey.Text.Trim() } else { '' }
  if (-not $noAsk -and (($url -and -not $key -and -not $KeySaved) -or ($key -and -not $url))) {
    [void][Windows.MessageBox]::Show($F,
      $(if ($urlPreset) { 'API 키를 넣습니다 — 키가 없으면 붙지 못합니다.' } else { '주소와 API 키는 둘 다 넣거나 둘 다 비워야 합니다.' }),
      $AppName, 'OK', 'Warning')
    return
  }
  # 도는 동안 고르는 칸들은 접고 「설치하는 중」 칸이 앞에 선다 — 접힌 칸은 못 만지므로 따로 잠그지 않는다.
  $bGo.Enabled = $false
  Show-Form $false
  $runCard.Visibility = 'Visible'; $runTitle.Text = '설치하는 중'
  $log.Clear(); $bar.Value = 0; Set-State '시작합니다…'
  # 준비 구간(0–8)을 미리 연다 — 첫 `[n/N]` 이 나오기 전에도 할 일이 있다(winget 이 없으면 되살리느라 수십 MB 를 받는다).
  #   그동안 구간이 0/0 이면 심장박동이 못 뛰어 막대가 0 에 박히고, 사람은 아무것도 안 하는 줄 안다.
  $script:segLo = 0; $script:segHi = 8; $script:idle = 0
  $script:sw = [Diagnostics.Stopwatch]::StartNew()
  $script:last = '준비'; $script:topic = '준비'
  # ⚠ **지난 회차의 마무리 문장을 지운다** — [다시 설치] 에서 이번 회차가 그 줄을 못 내면 지난 문장이 그대로 떠, 방금 한
  #   일과 다른 말을 한다.
  $script:done = ''

  # 값은 임시 파일로 건넨다(`-EnvFile`) — 몸통이 값을 받는 길을 하나로 둔다. 화면용 통로를 따로 내면 두 갈래가 서로 다른
  #   코드를 탄다. 키가 들어 있어 끝나면 지운다(타이머 · 창 닫기).
  $script:tmpEnv = [IO.Path]::Combine([IO.Path]::GetTempPath(), "claude-setup-$PID.env")
  $lines = New-Object System.Collections.Generic.List[string]
  # 넘기는 것은 이 회차에 사람이 넣은 것과 화면이 잰 것뿐이다 — 주소 · 키 · 저장소 주소 · 자리(`#site`). 짐의 값 줄과 지시는 몸통이
  #   제 짐(이 폴더의 `install.env`)에서 읽어 옮기지 않는다 — 화면으로 깐 사람과 `install.ps1` 을 직접 돌린 사람이 같은 짐의 값으로
  #   선다(파일 머리 「여기에는 설치 로직이 없다」 · 몸통 머리 「짐의 사실을 읽는 값 파일」).
  # 사외에도 칸 값을 그대로 넘긴다 — 무엇을 버릴지는 몸통이 가른다(몸통의 `$Vars` 표 `Gateway=$true` · `$InsideOnly` 목록).
  # 빈 값은 안 적는다 — 줄이 없는 것이 「안 넣었다」다. 저장소 칸을 비운 것은 몸통이 「저장소 없음」으로 기록한다(`-Pick` 을 준 판).
  if ($url) { $lines.Add("ANTHROPIC_BASE_URL=$url") }
  if ($key) { $lines.Add("ANTHROPIC_AUTH_TOKEN=$key") }
  $repo = $tRepo.Text.Trim()
  if ($repo) { $lines.Add("#config-repo = $repo") }
  # ⚠ **이 창이 칸을 지은 자리를 몸통에 넘긴다(`#site`).** 몸통은 다시 재고, 이 값과 다르면 아무것도 안 심고 「창을 연 뒤 자리가
  #   바뀌었다」로 멈춘다 — 창을 연 뒤 망이 바뀌면(무선 전환 · 회사망 재인증) 여기서 받은 키를 몸통이 버리거나 사외 칸이 안 받은
  #   주소 없이 게이트웨이를 써, **둘 다 초록으로 끝나기 때문이다.**
  if ($Site) { $lines.Add('#site = ' + $Site) }
  Set-Content -LiteralPath $script:tmpEnv -Value $lines -Encoding UTF8

  $argv = @('-NoProfile','-ExecutionPolicy','Bypass','-File', $Engine, '-Yes',
            '-EnvFile', $script:tmpEnv)
  # `-NoDevTools` 는 화면에 칸이 없다 — Claude Code 를 깔러 온 사람에게 git · python · gh 는 옵션이 아니다. 이 껍데기를
  #   `-NoDevTools` 로 부른 사람의 뜻과, 지난번 기록의 끔(`$Saved.NoDevTools`)을 그대로 넘긴다 — 안 넘기면 바탕화면 아이콘처럼
  #   깃발 없이 띄운 창이 git · gh 를 깔고 그 기록을 지운다. 되돌리는 길은 이 껍데기를 `-DevTools` 로 부르는 것이다(`Setup.exe -DevTools`)
  #   — 그 판은 기록의 끔을 안 넘긴다.
  if ($DevTools) { $argv += '-DevTools' }
  elseif ($NoDevTools -or $Saved.NoDevTools) { $argv += '-NoDevTools' }
  # 제작자 칸 — 산 칸 가운데 고른 것만. 하나도 없으면 안 넘긴다(`-ChoicesFull` 을 준 판에서 몸통은 안 준 것을 「없음」으로 읽는다)
  $persPicked = @($cPers | Where-Object { $_.Checked -and (Test-PersonalBoxLive $_) } | ForEach-Object { $_.Tag.Key })
  if ($persPicked.Count) { $argv += @('-PersonalFor', ($persPicked -join ',')) }
  if (-not $cUpg.Checked) { $argv += '-NoUpgrade' }
  if ($cAuto.Checked)     { $argv += '-AutoRun' }
  else                    { $argv += '-NoAutoRun' }
  # ⚠ **하나도 안 골라도 인자를 준다 — `-Pick none`.** 안 주면 몸통이 「이번 판은 고른 것을 안 넘겼다」로 읽어 지난 기록이나 표의
  #   기본값으로 **사람이 방금 다 끈 것을 되살린다** — 빈 값과 부재는 다른 명제다. 빈 글자로 넘기지 않는다 — 파워셸 5.1 의 `-File` 은
  #   빈 인자를 떨궈 「Missing an argument for parameter 'Pick'」으로 몸통이 안 뜬다. `none` 은 몸통의 `$ChoiceNone` 이다.
  # `-ChoicesFull` — 이 판은 칸에서 고른 것을 다 넘긴다. 안 주면 몸통이 안 넘긴 것(켠 VS Code · 끈 제작자 칸 · 비운 저장소)을 지난
  #   기록으로 채운다. 제품 칸이 선 판에서만 준다 — 몸통이 기록을 못 내준 판(제품 칸이 없다)은 칸이 기록이 아닌 기본값이라 기록과 합친다.
  if ($cApps.Count) {
    $picked = @($cApps | Where-Object { $_.Checked } | ForEach-Object { [string]$_.Tag })
    $argv += @('-Pick', $(if ($picked.Count) { $picked -join ',' } else { 'none' }), '-ChoicesFull')
  }
  # VS Code — 잠근 칸(사내 필수)은 사람의 값이 아니라 지난번에 고른 것을 넘긴다. 몸통은 사내면 칸과 상관없이 깔고 넘긴 값을 기록에 둔다.
  if ($cVsc -and $(if ($VsRequired) { [bool]$Saved.NoVsCode } else { -not $cVsc.Checked })) { $argv += '-NoVsCode' }

  # 싸는 규칙은 위 `Quote-Argv` 하나다 — 되띄우기 자리와 같은 자를 쓴다.
  $argLine = Quote-Argv $argv

  $base = [IO.Path]::Combine([IO.Path]::GetTempPath(), "claude-setup-$PID")
  $script:outFile = "$base.out"; $script:errFile = "$base.err"
  $script:rdOut = $null; $script:rdErr = $null

  # 나가는 것과 오류는 두 파일로 받고 타이머가 둘 다 읽는다 — `Save-RunLog` 는 둘 사이에 경계를 박는다.
  # 무엇을 돌리는지 먼저 찍는다 — 자식이 한 줄도 안 뱉는 판에서 「멈췄나 안 떴나」를 가를 자리가 된다.
  Add-Log "돌립니다: $argLine"
  Add-Log ''

  # ⚠ **`Start-Process -PassThru` 로 띄우지 않는다.** `-Wait` 없이 받은 그 객체는 자식이 끝나도 `ExitCode` 가 0 이 아니라
  #   **없다**(null) — 아래 `$rc -eq 0` 이 성공한 설치에서도 거짓이 되어 창이 「끝내지 못했습니다 (코드 )」로 끝난다. `-Wait` 는
  #   메시지 루프를 세우므로 화면은 못 건다.
  # 그래서 `Diagnostics.Process` 를 직접 띄운다 — 핸들을 쥐어 종료코드를 든다. 그 객체는 파일로 못 돌리므로(파이프만 준다)
  #   `cmd /c` 를 한 겹 두고 리다이렉트를 cmd 에 시킨다 — OS 가 돌려 `Write-Host` 줄까지 파일에 담기고, cmd 는 자식의 종료코드를
  #   그대로 물려준다. `CreateNoWindow` 라 창은 새로 안 뜬다.
  # ⚠ **표준입력까지 준다 — `0<NUL`.** `CreateNoWindow` 로 띄운 자식은 콘솔이 없고 나가는 것만 `1>` · `2>` 로 돌렸으므로
  #   표준입력이 빈 손잡이가 된다. 그것이 사슬을 타고 끝까지 내려가 자식을 다시 띄우는 자리에서 진다 — `python -m venv` 가 pip 을
  #   깔 때 `[WinError 6]` 으로 지고, 설치는 그것을 안은 채 초록으로 끝난다. NUL 은 성한 손잡이라 복제가 선다. 훅도 제 자리에서
  #   같은 것을 막는다 — 여기는 파이썬 밖의 자식까지 같이 구한다.
  try {
    $psExe   = (Get-Process -Id $PID).Path
    $cmdLine = '/d /s /c ""' + $psExe + '" ' + $argLine +
               ' 0<NUL 1>"' + $script:outFile + '" 2>"' + $script:errFile + '""'
    $psi = New-Object Diagnostics.ProcessStartInfo
    $psi.FileName        = (Join-Path $env:SystemRoot 'System32\cmd.exe')
    $psi.Arguments       = $cmdLine
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow  = $true
    $script:proc = [Diagnostics.Process]::Start($psi)
  } catch {
    # 예외를 삼키지 않고 말한다 — 삼키면 창이 「시작합니다」에서 굳고 아무도 까닭을 모른다.
    Add-Log "! 못 띄웠다 — $($_.Exception.Message)"
    $runTitle.Text = '못 띄웠습니다'
    Set-State '못 띄웠습니다 — 기록을 펼쳐 봅니다.' 'Bad'
    $bGo.Text = '다시 설치'; $bGo.Enabled = $true
    Show-Form $true
    return
  }

  # 기록은 이 창의 「설치하는 중」 칸이 든다 — 몸통은 콘솔 없이 돌고(`CreateNoWindow`), 같은 캡처를 따로 흘리는 창을 더 띄우지
  #   않는다. 끝난 뒤의 기록은 「설치기록」이 집어 준다(결정 0167).
  $timer.Start()
})

# ── 한 줄을 화면에 반영하는 자 ─────────────────────────────────────────────────
# `Step-Line <줄>` — 몸통이 찍은 한 줄을 기록 칸에 옮기고 막대 · 상태 글을 민다. 내는 것 없음. 줄 꼴은 몸통이 사람에게 찍는
#   그대로다(파일 머리): `[n/N] 이름` 은 걸음 구간을, `=== 검증` 은 100 을, `=== 끝 === <문장>` 은 마무리 문장을, 나머지 낱줄은
#   구간 안의 한 눈금을 준다.
# 걸음 안에서도 올라간다 — 막대를 `(n-1)/N` 에 두기만 하면 제일 오래 걸리는 첫 걸음 내내 0% 다. 걸음의 시작과 끝을 잡아 두고
#   낱줄마다 끝을 향해 조금씩 민다.
function Step-Line([string]$line) {
  Add-Log $line
  if ($line -match '^\[(\d+)/(\d+)\]\s*(.*)$') {
    $done = [int]$Matches[1]; $all = [int]$Matches[2]
    $script:segLo = [int](($done - 1) * 100 / $all)
    $script:segHi = [int]($done * 100 / $all)
    $bar.Value = $script:segLo
    $script:last = "$done/$all  $($Matches[3])"; $script:topic = $script:last
  } elseif ($line -match '^=== 검증') {
    $script:segLo = 100; $script:segHi = 100
    $bar.Value = 100; $script:last = '검증'; $script:topic = '검증'
  } elseif ($line -match '^=== 끝 ===\s*(.+)$') {
    # 마무리 문장은 몸통의 것을 그대로 쓴다 — 몸통이 갈래마다 다른 말을 한다(창을 띄웠나 · 떠 있어서 안 띄웠나 · 못 찾았나 ·
    #   안 띄우기로 했나). 사본을 두면 갈래가 늘 때 한쪽만 낡고, 낡은 줄은 멀쩡한 설치를 딴 데로 보낸다.
    $script:done = $Matches[1].Trim()
  } elseif ($line.Trim()) {
    # 칸 안의 낱줄 — 끝의 한 칸 앞까지만 민다. 끝을 미리 채우면 다음 칸이 뒤로 가는 꼴이 된다.
    if ($script:segHi -gt $script:segLo -and $bar.Value -lt ($script:segHi - 1)) {
      $stepBy = [Math]::Max(1, [int](($script:segHi - $script:segLo) / 6))
      $bar.Value = [Math]::Min($script:segHi - 1, $bar.Value + $stepBy)
    }
    # 무엇을 하는 중인지도 같이 보여준다 — 막대만 움직이면 무슨 일인지는 여전히 모른다. 앞 공백이 셋 이상인 줄은 흐름 줄(자식이 낸 줄 ·
    #   받는 진행 · 세부 줄)이라 주제를 갈지 않고 그 뒤에 붙인다 — 「설치 성공」만 떠 어느 프로그램인지 잃지 않게. 붙일 때 주제는 끝의
    #   괄호 곁말을 떼고 40자에서 자른다 — 상태 칸은 줄바꿈하는 칸이라 긴 주제가 흐름 줄을 밀어내고 칸을 키운다. 들여쓰기 꼴은 몸통의
    #   `Show-ChildLine` 머리말이 든다.
    if ($line -match '^\s{3,}\S' -and $script:topic) {
      $head = $script:topic -replace '\s*\([^()]*\)\s*$', ''
      if ($head.Length -gt 40) { $head = $head.Substring(0, 40) + '…' }
      $script:last = "$head — $($line.Trim())"
    }
    else { $script:topic = $line.Trim(); $script:last = $script:topic }
  }
}

# `Open-Tail <경로>` → 공유 열기한 UTF-8 StreamReader, 파일이 없거나 못 열면 `$null`. 자식이 **쓰는 중인** 파일을 읽으므로
#   쓰기를 막지 않게 연다.
# ⚠ **지우기까지 열어 준다(`Delete`).** 읽개가 아직 쥐고 있어도 캡처를 지우는 자리(타이머 끝 · 창 닫기)가 지지 않게 한다 — 지우기는
#   조용히 지는 자리라(`-ErrorAction SilentlyContinue`) 지면 캡처가 임시 폴더에 눌러앉는다. 이 창은 지우기 전에 늘 닫는다.
function Open-Tail([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  try {
    $fs = New-Object IO.FileStream($Path, [IO.FileMode]::Open,
            [IO.FileAccess]::Read, ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
    return New-Object IO.StreamReader($fs, [Text.Encoding]::UTF8)
  } catch { return $null }
}

# `Pump-Tail <읽개>` → 읽은 줄 수(읽개가 없으면 0). 열린 만큼 읽어 줄마다 `Step-Line` 에 넘기고, 읽을 것이 없으면 다음 틱에
#   이어 읽는다.
function Pump-Tail($Reader) {
  $n = 0
  if (-not $Reader) { return 0 }
  while ($true) {
    $line = $Reader.ReadLine()
    if ($null -eq $line) { break }
    Step-Line $line; $n++
  }
  return $n
}

# ── 창이 닫혀도 사는 기록 ───────────────────────────────────────────────────────
# `Save-RunLog` → 쓴 기록 파일 경로, 옮길 것이 없거나 못 쓰면 ''. 몸통의 두 캡처를 지우기 **전에** `$LogDir\install-<시각>.log`
#   한 파일로 옮긴다(로그 폴더가 없으면 만든다) — 화면에 뜬 줄은 창과 함께 죽으므로, 끝난 뒤 어느 걸음에서 무슨 일이 있었나를
#   물을 물건이 이것이다.
# ⚠ **키는 이 파일에 안 들어온다 — 옮기는 것은 나가는 것 · 오류 둘뿐이다.** 값을 나르는 것은 임시 env 파일 하나고, 몸통이 값을
#   찍는 자리는 이름만 든다(`Plant-Var` 는 `"  $Name — 심었다"`). 비밀 칸은 화면 갈래에서 아예 안 물어지고(`-Yes`), 콘솔 갈래에서도
#   `-AsSecureString` 이라 되울리지 않는다. 키가 든 임시 env 는 무조건 지운다.
# 못 써도 닫는 길을 막지 않는다 — 통째로 `try` 안에 두고, 지면 빈 값을 돌려준다.
# 자리는 판 폴더 밖이다 — 판마다 새 폴더가 나므로(`…\Claude Code Setup\<판>\`) 그 안에 두면 다음 판이 지난 기록을 못 보고, 판
#   폴더를 지우라는 안내가 기록까지 같이 지운다.
function Save-RunLog {
  # 남길 것이 **실제로 있는** 판만 쓴다 — 이미 지운 뒤 다시 불려도 빈 파일을 안 만든다.
  $any = $false
  foreach ($tmpFile in @($script:outFile, $script:errFile)) {
    if ($tmpFile -and (Test-Path -LiteralPath $tmpFile)) { $any = $true }
  }
  if (-not $any) { return '' }
  try {
    $dir = $LogDir
    if (-not (Test-Path -LiteralPath $dir)) {
      New-Item -ItemType Directory -Path $dir -Force -ErrorAction Stop | Out-Null
    }
    $path = Join-Path $dir ('install-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
    # 여는 법은 `Open-Tail` 하나다 — 자식이 방금까지 쥐고 있던 파일이라 공유 열기여야 하고, 그 조건을 여기 다시 적으면
    #   한쪽만 고쳐진다.
    $body = ''
    if ($script:outFile) {
      $r = Open-Tail $script:outFile
      if ($r) { try { $body = $r.ReadToEnd() } finally { try { $r.Dispose() } catch { } } }
    }
    # 둘을 한 파일에 담되 경계를 글자로 박는다 — 파일이 둘이면 이름도 둘이라 안내도 둘이 되고, 읽는 사람이 둘을 손으로
    #   맞춰야 한다.
    $body += "`r`n──────── 여기부터 오류 통로(stderr) ────────`r`n"
    if ($script:errFile) {
      $r = Open-Tail $script:errFile
      if ($r) { try { $body += $r.ReadToEnd() } finally { try { $r.Dispose() } catch { } } }
    }
    Set-Content -LiteralPath $path -Value $body -Encoding UTF8 -NoNewline -ErrorAction Stop
    return $path
  } catch {
    return ''
  }
}


# ── 파일을 따라 읽는 타이머 — 화면 실에서만 화면을 만진다 ──────────────────────
$timer = New-Object Windows.Threading.DispatcherTimer
$timer.Interval = [TimeSpan]::FromMilliseconds(150)
$timer.Add_Tick({
  if (-not $script:rdOut) { $script:rdOut = Open-Tail $script:outFile }
  if (-not $script:rdErr) { $script:rdErr = Open-Tail $script:errFile }
  $got = (Pump-Tail $script:rdOut) + (Pump-Tail $script:rdErr)

  # 줄이 안 나오는 동안에도 막대가 산다 — winget 이 도는 몇 분은 한 줄도 안 나와, 낱줄만 눈금으로 쓰면 사람은 멈춘 줄 안다.
  #   조용하면 천천히 민다. 미는 끝은 이 걸음의 끝 한 칸 앞이라 다음 걸음을 침범하지 않는다.
  if ($got -gt 0) {
    $script:idle = 0
  } else {
    $script:idle++
    # ⚠ 밀고 나서 `idle` 을 0 으로 되돌리지 않는다 — 아래 「오래 걸리는 중」 줄이 그 값으로 얼마나 조용했나를 센다. 12 틱마다
    #   한 칸씩 미는 것은 나머지로 가른다.
    if (($script:idle % 12) -eq 0 -and $script:segHi -gt $script:segLo -and
        $bar.Value -lt ($script:segHi - 1)) {
      $bar.Value = $bar.Value + 1
    }
  }

  if ($script:sw) {
    $sec = [int]$script:sw.Elapsed.TotalSeconds
    $lState.Text = "{0}초 · {1}" -f $sec, $script:last
    # 오래 조용하면 그 사실을 말한다 — 「멈춘 것 같다」를 사람이 혼자 판정하지 않게.
    if ($script:idle -ge 400 -and $script:proc) {   # 400틱 ≈ 60초
      $lState.Text = "{0}초 · {1}  (오래 걸리는 중 — winget 이 받는 중일 수 있습니다)" -f $sec, $script:last
    }
  }

  if ($script:proc -and $script:proc.HasExited) {
    Start-Sleep -Milliseconds 150      # 마지막 쓰기가 파일에 닿을 틈
    Pump-Tail $script:rdOut | Out-Null
    Pump-Tail $script:rdErr | Out-Null
    $timer.Stop()
    $rc = $script:proc.ExitCode
    foreach ($r in @($script:rdOut, $script:rdErr)) {
      if ($r) { try { $r.Dispose() } catch { } }
    }
    $script:rdOut = $null; $script:rdErr = $null
    # 지우기 전에 옮긴다 — 나가는 것·오류는 여기가 마지막 독자다 (`Save-RunLog` 머리말).
    Save-RunLog | Out-Null
    # ⚠ **키가 든 임시 파일을 반드시 지운다.** 남기면 사람 임시 폴더에 평문으로 눌러앉는다.
    # ⚠ 고리 이름을 `$f` 로 두지 않는다 — 파워셸 이름은 대소문자를 안 가려 이 손 안에서 창(`$F`)을 가리고, 뒤의 `Show-Form` 이 창 대신
    #   글자를 받아 손째 던진다.
    foreach ($tmpFile in @($script:tmpEnv, $script:outFile, $script:errFile)) {
      if ($tmpFile -and (Test-Path -LiteralPath $tmpFile)) {
        Remove-Item -LiteralPath $tmpFile -Force -ErrorAction SilentlyContinue
      }
    }
    $script:proc = $null
    if ($script:sw) { $script:sw.Stop() }

    # ⚠ **끝났다고 됐다고 하지 않는다.** 몸통이 하나라도 못 세우면 0 이 아닌 값으로 끝나고,
    #   그것을 안 재고 「완료」를 찍으면 안 선 기계가 성공으로 보고된다.
    # 「못 읽었다」를 「실패했다」로 뭉치지 않는다 — 종료코드가 없는 것은 실패가 아니라 재는 자가 고장났다는 뜻이라, 같은
    #   문장으로 말하면 멀쩡한 설치가 실패로 보고된다.
    if ($null -eq $rc) {
      $runTitle.Text = '끝났는데 판정을 못 읽었습니다'
      Set-State '끝났는데 종료코드를 못 읽었습니다 — 기록의 마지막 줄로 판단하세요.' 'Warn'
    } elseif ($rc -eq 0) {
      $bar.Value = 100
      $runTitle.Text = '끝났습니다'
      # 마무리 문장을 못 받았으면(몸통이 `=== 끝 ===` 줄 전에 끊긴 판) 지어 내지 않고 기록을 보라고 한다 — 안 한 일을 했다고
      #   말하지 않게.
      Set-State $(if ($script:done) { $script:done } else { '됐습니다 — 기록의 마지막 줄을 보세요.' }) 'Ok'
    } else {
      $runTitle.Text = '끝내지 못했습니다'
      Set-State "끝내지 못했습니다 (코드 $rc) — 기록을 펼쳐 ! 줄을 보세요." 'Bad'
    }
    $bGo.Text = '다시 설치'; $bGo.Enabled = $true
    Show-Form $true
  }
})

# 창을 닫을 때 도는 자식을 두고 가지 않는다 — 물어서 「예」면 나무째 끄고, 기록을 옮긴 뒤 임시 파일을 지운다.
$F.Add_Closing({
  if ($script:proc -and -not $script:proc.HasExited) {
    $ans = [Windows.MessageBox]::Show($F, '설치가 도는 중입니다. 멈추고 닫을까요?', $AppName, 'YesNo', 'Warning')
    if ($ans -ne 'Yes') { $_.Cancel = $true; return }
    # ⚠ **나무째 끈다.** `$script:proc` 는 몸통이 아니라 그것을 감싼 `cmd.exe` 라, 그것만 죽이면 **몸통 PowerShell 과 그
    #   자식(winget · npm)이 남아 계속 돈다** — 창은 사라졌는데 뒤에서 설치가 이어지고, 다음 판은 빗장에 막힌다.
    # `taskkill /T` 를 안 쓴다 — 실행 파일을 하나 더 부르는 길은 정책이 막는 PC 가 있다(「Access is denied」로 안 뜬다). 자식
    #   목록을 윈도우에 물어 나무를 다 뜬 뒤 아래부터 끈다 — 끄는 사이 부모가 사라져도 이미 뜬 목록으로 간다.
    $tree = New-Object System.Collections.Generic.List[int]
    $walk = New-Object System.Collections.Generic.Queue[int]
    $walk.Enqueue($script:proc.Id)
    try {
      $allProcs = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId -ErrorAction Stop)
      while ($walk.Count) {
        $p = $walk.Dequeue(); $tree.Add($p)
        foreach ($c in $allProcs) { if ($c.ParentProcessId -eq $p -and $c.ProcessId -ne $p) { $walk.Enqueue([int]$c.ProcessId) } }
      }
    } catch { }
    for ($i = $tree.Count - 1; $i -ge 0; $i--) {
      try { Stop-Process -Id $tree[$i] -Force -ErrorAction Stop } catch { }
    }
    try { if (-not $script:proc.HasExited) { $script:proc.Kill() } } catch { }
  }
  # 끝까지 못 간 판이야말로 기록이 필요하다 — 여기서도 지우기 전에 옮긴다. 위 갈래가 이미
  # 옮겼으면 파일이 없어 `Save-RunLog` 가 빈 자리를 돌려주고 만다(빈 파일을 안 만든다).
  Save-RunLog | Out-Null
  foreach ($tmpFile in @($script:tmpEnv, $script:outFile, $script:errFile)) {
    if ($tmpFile -and (Test-Path -LiteralPath $tmpFile)) {
      Remove-Item -LiteralPath $tmpFile -Force -ErrorAction SilentlyContinue
    }
  }
})
# ── 새 판이 있나 — 창이 뜬 뒤에 배경으로 물어본다 ──────────────────────────────
# 앞을 막지 않는다 — 묻는 데 몇 초가 들 수 있어(사내 프록시가 막으면 시간이 다 갈 때까지) 창이 먼저 서고 이것은 딴 실에서
#   돈다. 답은 타이머(`upTimer`)가 화면 실에서 집는다.
#   ⚠ **딴 실에서 창을 만지면 그 자리에서 죽는다** — 창은 타이머 안에서만 만진다.
# 「못 물었다」를 「최신이다」로 읽지 않는다 — 못 물었으면 머리의 알약이 「새 판 확인 못 함」을 들고, 「최신」은 물어서 그렇다는
#   답을 받았을 때만 단다. 막힌 망에서 조용히 최신이라고 하면 낡은 판을 든 사람이 낡은 줄 모른 채 간다.
# 자리를 여기 안 박는다 — 값 파일의 `#update-repo` 가 든다. 박으면 이 파일이 특정 저장소의 것이 되어 남에게 그대로 못 준다
#   (`#site-probe` · `#config-repo` 와 같은 결).
$script:upPs = $null
$script:upHandle = $null
$UpdateRepo = Read-Directive $EnvPath 'update-repo'
# 묻고 재는 손은 곁의 조각(`update-check.ps1`)이 든다 — 자동 실행도 같은 자를 부른다. 여기 붙박이로 두면 그쪽이 베껴 손사본
# 둘이 된다. 조각이 없으면 안 묻는다 — 새 판을 못 보는 것보다 창이 안 서는 것이 값이 크다.
$UpdateLib = Join-Path $Here 'update-check.ps1'

if ($UpdateRepo -and $DistVersion -and (Test-Path -LiteralPath $UpdateLib)) {
  try {
    $script:upPs = [powershell]::Create()
    # ⚠ **딴 실이라 이 파일의 함수를 모른다** — 그 실 안에서 조각을 제 손으로 읽는다. 바로 부르면 `catch` 가 삼켜 새 판을
    #   조용히 못 본다.
    [void]$script:upPs.AddScript({
      param($lib, $repo, $mine)
      try { . $lib; return Measure-NewerRelease -Repo $repo -Mine $mine } catch { return $null }
    })
    [void]$script:upPs.AddArgument($UpdateLib)
    [void]$script:upPs.AddArgument($UpdateRepo)
    [void]$script:upPs.AddArgument($DistVersion)
    $script:upHandle = $script:upPs.BeginInvoke()
  } catch { $script:upPs = $null; $script:upHandle = $null }
}

# `$script:upFound` — 거둔 새 판(`Measure-NewerRelease` 의 `Found`). 물을 때까지 든다 — 설치가 도는 동안 온 답은 여기서 기다린다.
$script:upFound = $null
$script:upTimer = New-Object Windows.Threading.DispatcherTimer
$script:upTimer.Interval = [TimeSpan]::FromMilliseconds(400)
$script:upTimer.Add_Tick({
  # 답을 한 번 거둔다 — 머리의 알약은 거둔 그 틱에 단다(설치가 도는 중이어도)
  if ($script:upHandle) {
    if (-not $script:upHandle.IsCompleted) { return }
    $probe = $null
    try { $probe = @($script:upPs.EndInvoke($script:upHandle))[0] } catch { }
    try { $script:upPs.Dispose() } catch { }
    $script:upPs = $null; $script:upHandle = $null
    # 머리의 알약이 답을 든다 — 물음창은 새 판일 때만 뜨므로, 못 물은 판은 여기서만 보인다
    $verText = Get-El 'VerText'
    if ($probe -and $probe.State -eq 'latest') { $verText.Text = "$DistVersion · 최신" }
    elseif (-not $probe -or $probe.State -ne 'newer') {
      $why = if ($probe -and $probe.Why) { $probe.Why } else { '묻는 손을 못 불렀다' }
      $verText.Text = "$DistVersion · 새 판 확인 못 함"
      (Get-El 'VerPill').ToolTip = "새 판이 있나 확인하지 못했습니다 — $why`n「바뀐 것」에서 최신 판 번호를 볼 수 있습니다."
    }
    if ($probe -and $probe.State -eq 'newer') {
      $script:upFound = $probe.Found
      $verText.Text = "$DistVersion · 새 판 $($script:upFound.Ver) 있음"
    }
  }
  if (-not $script:upFound) { $script:upTimer.Stop(); return }
  # ⚠ **설치 회차가 열려 있는 동안은 안 묻는다 — 타이머는 돌려 둔 채 기다린다.** 도는 중에 물으면 「예」가 새 `Setup.exe` 를 띄우고
  #   이 창을 닫으려다 닫기 손의 「멈추고 닫을까요」에 걸린다 — 아니오면 창이 둘 서고 새 몸통은 빗장에 막힌다. 회차가 닫히는 것은
  #   파일을 따라 읽는 타이머의 끝 갈래가 `$script:proc` 를 비울 때라(끝 판정 · 기록 옮기기 뒤), 끝난 화면이 선 다음 틱에 묻는다.
  #   그 전에 창을 닫으면 다음 실행이 다시 묻는다.
  if ($script:proc) { return }
  $script:upTimer.Stop()
  $found = $script:upFound
  $script:upFound = $null

  $ans = [Windows.MessageBox]::Show($F,
    "새 판 $($found.Ver) 이 나와 있습니다. 지금 것은 $DistVersion 입니다.`n`n" +
    "새 판으로 설치할까요?`n받는 동안 이 창은 잠깐 멈춥니다 — 2MB 남짓입니다.",
    $AppName, 'YesNo', 'Question')
  if ($ans -ne 'Yes') { return }

  # 받아서 재는 손은 곁의 조각이 든다(`update-check.ps1`) — **왜 해시가 이 자리를 드는지**도
  # 거기 곁말이 든다. 여기가 드는 것은 **진 까닭마다 사람에게 뭐라 할까** 하나다.
  $F.Cursor = [Windows.Input.Cursors]::Wait
  $F.IsEnabled = $false
  try { . $UpdateLib } catch { }
  $v = $null
  try { $v = Get-VerifiedSetup -Found $found }
  catch { $v = @{ Ok = $false; Status = 'download-failed'; Detail = $_.Exception.Message } }
  $F.IsEnabled = $true
  $F.Cursor = $null

  if (-not $v.Ok) {
    # 「못 쟀다」와 「다르다」를 한 말로 묶지 않는다 — 앞은 대조할 값이 릴리스에 없거나 못 읽은 것이고(`no-hash-asset` ·
    #   `hash-unreadable`) 뒤는 받은 것이 어긋난 것이다(`hash-mismatch`). 사람이 할 일이 서로 다르다.
    $say = "새 판을 못 받았습니다. 지금 것으로 계속 하셔도 됩니다.`n`n$($v.Detail)"
    $ico = 'Warning'
    if ($v.Status -eq 'no-hash-asset' -or $v.Status -eq 'hash-unreadable') {
      $say = "새 판을 못 쟀습니다 — $($v.Detail).`n`n" +
             "받은 것이 맞는지 대조할 자가 없어 띄우지 않았습니다. 지금 것으로 계속 하셔도 됩니다."
    } elseif ($v.Status -eq 'hash-mismatch') {
      $ico = 'Error'
      $say = "받은 파일이 릴리스에 오른 값과 다릅니다 — 띄우지 않았습니다.`n`n" +
             "파일: $($v.Path)`n릴리스가 든 값: $($v.Want)`n받은 것의 값: $($v.Have)`n`n" +
             "지금 것으로 계속 하셔도 됩니다."
    }
    [void][Windows.MessageBox]::Show($F, $say, $AppName, 'OK', $ico)
    return
  }

  # 이 창이 받은 깃발을 새 판에 그대로 넘긴다(`$PassArgs`) — 새 `Setup.exe` 는 제 인자를 새 창에 붙이므로, 안 넘기면 `-DevTools` ·
  #   `-PersonalFor` 같은 사람의 뜻이 판을 건너며 사라진다. 싸는 규칙은 `Quote-Argv` 하나다. 넘길 것이 없으면 인자를 안 준다 —
  #   `Start-Process` 는 빈 `-ArgumentList` 를 받지 않는다.
  $relaunch = @{ FilePath = $v.Path }
  if ($PassArgs.Count) { $relaunch.ArgumentList = Quote-Argv $PassArgs }
  Start-Process @relaunch | Out-Null
  # 이 창을 닫는다 — 새 판이 제 화면을 띄우므로 둘이 같이 서 있으면 어느 것에 값을 넣었는지가 흐려진다.
  $F.Close()
})

# 닫기는 `IsCancel` 하나로 닫는다 — 클릭에서 또 닫으면 `ShowDialog` 의 취소 명령이 한 번 더 닫아 「멈추고 닫을까요」가 두 번 뜬다

# 몸통이 옛 제작자 칸(`-WithPersonalConfig`)을 이어받아 설치한 뒤 이 창을 `-PersonalNotice` 로 한 번 띄운 판 — 무엇이 바뀌었나를
#   먼저 알린다(몸통 끝의 「옛 제작자 칸을 이어받은 판의 마무리」 · 결정 0099). 몸통의 그 칸을 걷을 때 같이 걷는다.
function Show-PersonalNotice {
  $ans = [Windows.MessageBox]::Show($F,
    ('이번 판부터 제작자의 규범 · 룰 · 스킬을 도구마다 고릅니다 — Claude · Codex · agy.' + [Environment]::NewLine + [Environment]::NewLine +
     '자동 실행이 예전 칸을 Claude 로 이어받아 방금 설치했습니다. 그대로 두려면 이 창을 닫으면 됩니다 — 다시 묻지 않습니다.' +
     [Environment]::NewLine + [Environment]::NewLine +
     '바꾸려면 「자세히 설정」의 「규범 · 룰 · 스킬을 받을 모델」을 고르고 [설치 시작]을 누릅니다. 예전 칸은 agy 를 같이 고른 PC 의 ' +
     'agy 에도 규범을 깔았는데, 이번 설치에서 그것은 백업 자리로 옮겨졌습니다 — agy 에서도 받으려면 agy 칸을 켭니다.' + [Environment]::NewLine + [Environment]::NewLine +
     '주로 일하는 도구에만 켜면 가끔 맡기는 도구는 부를 때 가볍습니다. 무엇이 깔리는지는 이 상자를 닫으면 여는 「제공기능」 페이지에 있습니다.' +
     $(if ($ReleasePage) { [Environment]::NewLine + [Environment]::NewLine + '이 판에서 바뀐 것을 릴리스 노트에서 자세히 볼까요?' } else { '' })),
    $AppName, $(if ($ReleasePage) { 'YesNo' } else { 'OK' }), 'Information')
  if ($ReleasePage -and $ans -eq 'Yes') { try { Start-Process -FilePath $ReleasePage | Out-Null } catch { } }
  # 「제공기능」도 같이 연다(결정 0099) — 못 열면 창의 링크가 그대로 남는다
  $featPage = Join-Path $Here 'features.html'
  if (Test-Path -LiteralPath $featPage) { try { Open-InBrowser $featPage } catch { } }
}

# 처음 그려진 뒤 한 번 — 새 판 묻기를 집는 타이머를 켜고, 빈 칸으로 손을 보내고, 알림 판이면 알린다.
$script:shown = $false
$F.Add_ContentRendered({
  if ($script:shown) { return }
  $script:shown = $true
  if ($script:upHandle) { $script:upTimer.Start() }
  # 빈 칸이 있으면 거기로 간다 — 주소 칸이 먼저다. 키가 채워져 왔다고 곧장 단추로 보내면, 비어 있는 주소 칸을 건너뛴 채 손이
  #   [설치 시작] 위에 놓인다.
  if ($tUrl -and $tUrl.IsEnabled -and -not $tUrl.Text.Trim())     { [void]$tUrl.Focus() }
  elseif ($tKey -and $tKey.IsEnabled -and -not $tKey.Text.Trim()) { [void]$tKey.Focus() }
  else { [void]$bGo.Focus() }
  if ($PersonalNotice) { Show-PersonalNotice }
})
Sync-PersonalBoxes    # 제작자 칸의 켜짐을 제품 칸 첫 상태에 맞춘다
Sync-PersonalSource   # 출처 줄 · 접힌 머리의 한 줄을 저장소 칸 첫 값에 맞춘다
[void]$F.ShowDialog()
