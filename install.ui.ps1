# 설치 화면 — 값을 받고, 옵션을 고르고, 진행을 보여준다.
#
#   진입점은 `install.cmd` 다. 화면이 못 서면(윈도우가 아니거나 데스크탑이 없으면) 콘솔
#   갈래로 물러난다.
#
# ⚠ **여기에 설치 로직이 없다.** 무엇을 어떻게 깔지는 `install.ps1` 한 자리가 든다 — 이
#   파일은 값을 받아 그것에 넘기고, 그것이 찍는 줄을 화면에 옮긴다. 로직을 여기 옮기면
#   화면 갈래와 콘솔 갈래가 서로 다른 코드를 타고, 그러면 한쪽만 고쳐진다.
#
# ⚠ **진행 막대의 신호는 몸통이 이미 찍는 `[n/8]` 이다.** 진행률을 알리는 통로를 따로 내지
#   않는다 — 통로가 둘이면 칸이 늘 때 한쪽만 고쳐지고, 그 어긋남은 「막대가 안 찬다」는
#   조용한 꼴로만 보인다. 몸통이 사람에게 하는 말을 그대로 읽는다.
#   ⚠ **분모는 그 줄에서 받는다** — 칸이 늘어도 고칠 코드가 없다. 여덟은 지금 몸통이 찍는 수다.

# ⚠ `$NoConsole` 은 **사람이 칠 것이 아니다** — 「이 프로세스에는 보여줄 콘솔이 없다」는
#   **상태**를 넘기는 자리고, 아래 「검은 창을 없애는 자리」가 든다. 넘기는 자가 둘이다:
#   이 파일이 제 자신을 다시 띄울 때와, 진입점 exe 가 띄울 때(그쪽은 이미 콘솔을 안 붙인다).
#   ⚠ **사건이 아니라 상태로 물었다.** 「다시 띄워졌나」로 물으면 exe 갈래가 그 물음에 안 걸려
#     **콘솔이 없는데도 한 번 더 띄운다** — 창은 하나만 뜨니 안 보이고, 0.5초만 조용히 샌다.
# ⚠ `$Unattended` 도 **사람이 칠 것이 아니다** — 로그온 자동 실행이 새 판을 받았을 때
#   `Setup.exe` 를 **푸는 자로만** 쓰는 자리다. 아래 「무인 갈래」 칸이 든다.
param([switch]$NoDevTools, [switch]$WithPersonalConfig, [switch]$NoUpgrade, [switch]$NoConsole, [switch]$Unattended)

$ErrorActionPreference = 'Stop'
# ⚠ **던지게 두지 않는다.** 출력이 파일로 돌려진 채로 뜨면 이 줄이 걸릴 수 있고, 위 `Stop`
#   이 그 자리에서 끝낸다 — **한 줄도 안 찍힌 채 죽는다.** 인코딩은 편의지 조건이 아니다.
$OutputEncoding = [System.Text.Encoding]::UTF8
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$Here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Engine = Join-Path $Here 'install.ps1'

# ── 이 폴더가 몇 판인가 ─────────────────────────────────────────────────────────
# ⚠ **폴더가 제 판을 알아야 낡은 것을 알 수 있다.** 옛 판은 번호가 릴리스 태그에만 살아서
#   푼 폴더는 제가 몇 판인지 몰랐고, 그러면 「낡았다」를 잴 자리가 아예 없다. 진본은 옆의
#   `VERSION` 이고 릴리스 태그가 **그 값에서** 나온다 — 반대가 아니다.
# ⚠ **없으면 없는 대로 간다.** 이 값은 사람에게 보여 주는 것이지 설치의 조건이 아니다.
#   없다고 막으면 번호 하나 때문에 설치가 통째로 안 되는 꼴이 된다.
# ⚠ **BOM 을 손으로 걷는다.** 이 파일은 인코딩 문지기가 안 보는 종류라(`*.ps1`·`*.cmd` 만
#   본다) 누가 BOM 을 붙여 저장하면 번호 앞에 안 보이는 글자가 붙는다 — 화면에는 멀쩡히
#   찍히고 **견주는 자리에서만** 안 맞는다.
$DistVersion = ''
$VersionPath = Join-Path $Here 'VERSION'
if (Test-Path -LiteralPath $VersionPath) {
  try {
    $DistVersion = (([string](Get-Content -LiteralPath $VersionPath -TotalCount 1 -Encoding UTF8)) -replace "^\uFEFF", '').Trim()
  } catch { $DistVersion = '' }
}

# ── 콘솔에 남은 글을 사람이 읽을 틈 ────────────────────────────────────────────
# ⚠ **`install.cmd` 에는 `pause` 가 없다** — 설치 창의 [닫기] 를 누르면 뒤에 선 콘솔까지
#   같이 닫혀야 하기 때문이다. 그래서 「읽을 것이 있는 갈래」가 제 멈춤을 직접 든다.
#   여기서 안 들면 저 아래 갈래들은 **한 줄 찍고 창째로 사라진다** — 부재가 통과로
#   읽히는 것과 같은 자리다: 사람은 아무 일도 안 일어난 줄 안다.
# ⚠ **화면이 선 갈래에서는 안 부른다.** 그 판의 결과는 창 안에 찍혀 있고, 사람이 창을
#   닫는 것이 곧 끝내는 동작이다. 거기서 멈추면 닫아도 안 닫히는 콘솔이 남는다.
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
# ⚠ **이것은 「무인으로 설치한다」가 아니다.** 로그온 자동 실행이 새 판을 받았을 때
#   `Setup.exe` 를 **푸는 자로만** 쓰는 자리다 — exe 는 짐을 `<판>\` 에 푼 **뒤에** 이
#   파일을 띄우고 **기다리지 않고 나간다**(`Setup.c` 의 맨 끝 곁말). 그래서 여기서 설치를
#   시작하면 부르는 쪽은 그것이 끝난 줄 알고 「완료」를 찍는다 — **거짓 초록이다.**
#   푸는 일은 이 줄에 닿기 전에 이미 끝났으니 우리 몫은 조용히 비키는 것뿐이고,
#   **새 판으로 설치하는 것은 부르는 쪽**(`autorun.ps1`)이 제 로그 안에서 든다.
if ($Unattended) { exit 0 }

# ── 화면이 설 수 있나 ───────────────────────────────────────────────────────────
# ⚠ **물러날 때 조용하지 않는다.** 화면이 안 서는 것과 설치가 안 되는 것은 다른 명제인데,
#   말없이 콘솔로 내려가면 사람은 「화면이 뜨는 줄 알았는데 왜」에서 멈춘다.
$uiOk = $true
try {
  Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
  Add-Type -AssemblyName System.Drawing -ErrorAction Stop
  [System.Windows.Forms.Application]::EnableVisualStyles()
} catch { $uiOk = $false }

if (-not $uiOk) {
  Write-Host '화면을 못 띄운다 — 콘솔로 진행한다.' -ForegroundColor Yellow
  & $Engine -NoDevTools:$NoDevTools -WithPersonalConfig:$WithPersonalConfig -NoUpgrade:$NoUpgrade
  # ⚠ **판정을 먼저 집는다.** `Hold-Console` 뒤에 읽으면 그 사이에 도는 것이 `$LASTEXITCODE`
  #   를 갈아치울 수 있고, 그러면 **몸통이 진 판이 0 으로 보고된다.**
  $rc = $LASTEXITCODE
  Hold-Console
  exit $rc
}

# ── 인자를 한 줄로 싸는 자 — **규칙은 이 파일에 하나다** ────────────────────────
# 이 파일은 `powershell.exe` 를 두 자리에서 띄운다(제 자신을 되띄우는 자리 · 몸통을 띄우는
# 자리). 같은 꼴로 띄우므로 **규칙이 둘일 수 없다** — 둘 다 이 함수를 지난다 (#3).
#
# ⚠ **낱낱을 다 싼다 — 스위치까지.** 따옴표는 파워셸의 인자 맞추기 **전에** 벗겨지므로
#   `"-NoProfile"` 은 값이 아니라 스위치로 선다. 실측(2026-09-15): 전부 싸서 띄운 자식이
#   `Get-ExecutionPolicy -Scope Process` 로 `Bypass` 를 찍었고 `$PSBoundParameters` 도
#   제대로 섰다 — 곧바로 띄운 판과 `cmd` 를 한 겹 지난 판이 같았다.
# ⚠ **골라 싸면 모자란다.** 아래 몸통 줄은 `cmd` 에 넘어가므로 `&`·`^`·괄호가 든 경로는
#   안 싸면 cmd 가 거기서 명령을 자른다 — **빈칸이 없어도 그렇다.** 다 싸면 그 갈래가
#   통째로 없어지고, 자리마다 다른 문자 집합을 맞춰 둘 까닭도 없어진다.
function Quote-Argv([string[]]$Argv) {
  ($Argv | ForEach-Object { '"' + $_ + '"' }) -join ' '
}

# ── 검은 창을 없애는 자리 — **제 자신을 숨김으로 다시 띄우고 빠진다** ───────────
# `install.cmd` 가 든 콘솔은 설치가 끝날 때까지 설치 화면 뒤에 앉아 있었다. 그것을 없앤다.
#
# ⚠ **순서가 이 갈래의 전부다.** 위 `$uiOk` 갈래보다 **뒤**에 서야 한다 — 화면을 못 세우는
#   PC 는 이 줄에 닿기 전에 콘솔로 빠지므로, **안 보이는 창에 대고 말하는 일이 안 생긴다.**
#   앞에 두면 그 갈래가 숨은 창에 찍고 죽어, 사람은 아무 일도 안 일어난 줄 안다.
#
# ⚠ **숨김은 「만들 때」 줘야 한다 — 뜬 뒤에 숨기는 길은 죽었다.** Windows 11 의 콘솔은 대개
#   Windows Terminal 이 드는데, 그때 `GetConsoleWindow()` 는 진짜 창이 아니라
#   `PseudoConsoleWindow` 를 돌려주고 거기 건 `ShowWindow(SW_HIDE)` 는 **참을 돌려주고
#   아무것도 안 한다**(실측 2026-09-15). 거짓 초록이다.
#
# ⚠ **`CreateNoWindow` 여야 한다 — `-WindowStyle Hidden` 이 아니다.** 둘은 같아 보이는데
#   **서로 다른 것을 시킨다.**
#     · `-WindowStyle Hidden` 은 「**첫 창**을 숨겨라」를 프로세스 시작값에 박는다. 그 숨김이
#       콘솔에서 멈추지 않고 **설치 화면까지 번진다** — 창은 만들어지는데 안 보인다.
#     · `CreateNoWindow` 는 「이 프로세스에 **콘솔을 붙이지 마라**」다. 창 상태를 안 건드리니
#       설치 화면은 제 크기로 화면 가운데 뜬다.
#   실측 2026-09-15 — `-WindowStyle Hidden` 으로 띄운 판에서 창 목록을 훑었더니
#   `title='Claude Code 설치' visible=False` 였다. 같은 날 `start /min` 이 최소화를 번지게
#   한 것과 **같은 함정이고 같은 축이다**: 창 상태를 물려주는 자를 쓰면 안 된다.
#
# ⚠ **`WindowState` 로 판정하면 안 된다 — 숨은 창도 `Normal` 이다.** 이 갈래를 처음 잴 때
#   그 값만 보고 초록으로 읽었다가 놓쳤다. 재는 것은 `Visible` 이다.
#
# ⚠ **못 띄우면 그냥 이 창에서 간다.** 검은 창 하나 없애자고 설치를 못 하게 만들지 않는다.
if (-not $NoConsole) {
  $again = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $MyInvocation.MyCommand.Path, '-NoConsole')
  if ($NoDevTools)         { $again += '-NoDevTools' }
  if ($WithPersonalConfig) { $again += '-WithPersonalConfig' }
  if ($NoUpgrade)          { $again += '-NoUpgrade' }
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

# ── 옆에 온 값 파일 — 회사 공통값은 이미 채워져 온다 ────────────────────────────
# 뽑는 자(`scripts/build-dist.sh`)가 자리 파일에서 파생해 넣는다. 사람은 키만 넣으면 된다.
$EnvPath = Join-Path $Here 'install.env'
$Preset  = @{}
if (Test-Path -LiteralPath $EnvPath) {
  foreach ($line in Get-Content -LiteralPath $EnvPath -Encoding UTF8) {
    $t = $line.Trim()
    if (-not $t -or $t.StartsWith('#') -or ($t -notmatch '=')) { continue }
    $k = $t.Substring(0, $t.IndexOf('=')).Trim()
    $v = $t.Substring($t.IndexOf('=') + 1).Trim()
    if ($k) { $Preset[$k] = $v }
  }
}

# ⚠ **여기로 올라온 까닭 — 창 제목이 이 함수의 답을 쓴다.** 값 파일의 지시를 읽는 자이므로
#   값 파일을 읽은 바로 다음이 제자리고, 아래 화면 칸들은 그 답 위에 선다.
# ⚠ **볼 파일을 인자로 받되 기본값이 옆에 온 값 파일이다** — 부르는 자리 대부분은 그것을 원하고,
#   판을 넘겨 사는 자리를 되돌아봐야 하는 칸만 둘째 인자를 댄다(아래 저장소 칸).
function Get-Directive([string]$Key, [string]$File = $EnvPath) {
  if (-not $File -or -not (Test-Path -LiteralPath $File)) { return $null }
  foreach ($line in Get-Content -LiteralPath $File -Encoding UTF8) {
    if ($line -match "^\s*#\s*$([regex]::Escape($Key))\s*=\s*(.+?)\s*$") { return $Matches[1] }
  }
  return $null
}

# 판을 넘겨 사는 값 파일 — **판 폴더의 한 층 위**다. 푸는 자가 판마다 새 폴더를 만들어 옆에 온
# 것은 늘 「뽑은 그대로」이고, 사람이 넣은 것은 설치기가 이 자리에 얼려 둔다(자동 실행이 읽는 그 파일).
# ⚠ **이름을 박지 않고 파생한다** — 자리를 옮기면 고칠 자리가 하나여야 한다.
# ⚠ 풀어 놓고 직접 돌리는 자리에는 이 파일이 없다 — 그러면 `$null` 이고 지금과 같이 빈 칸이다.
$KeptEnvPath = Join-Path (Split-Path -Parent $Here) 'install.env'

# ── 앱 이름 — **진본은 값 파일의 `#app-name` 한 줄이다** ─────────────────────────
# ⚠ **여기 든 글자는 진본이 아니라 울타리다.** 이름이 찍히는 자리가 이 파일에만 일곱인데
#   (창 제목 하나 · 상자 제목 여섯), 자리마다 글자를 박으면 이름을 바꾸는 날 **한 자리만
#   낡고 그 한 자리는 아무도 안 본다** — 상자 제목은 그 갈래를 밟은 사람만 본다.
# ⚠ **몸통도 같은 줄에서 판다**(`install.ps1` 의 `$AppName`). 화면과 몸통이 이름을 따로 박으면
#   창 제목과 바로가기 이름이 갈리는데, 그 둘이 갈린 것은 **둘을 같이 보는 사람만** 안다.
$AppNameDefault = 'PAI Setup Wizard'
$AppName = Get-Directive 'app-name'
if (-not $AppName) { $AppName = $AppNameDefault }

# ── 고를 제품 — **목록도 기본값도 몸통이 든다** ──────────────────────────────────
# ⚠ **여기 옮겨 적지 않는다** — 몸통에 묻는다(`-Describe`). 옮겨 적으면 제품이 늘 때 한쪽만
#   고쳐지고, 그 어긋남은 「골랐는데 안 깔린다」는 조용한 꼴로만 보인다.
# ⚠ **자식으로 띄워 묻는다.** 이 창 안에서 그 파일을 부르면 저쪽의 `exit` 가 **이 창까지**
#   끌고 나간다 — 목록 하나 얻자고 치를 값이 아니다.
$Choices = @()
try {
  $raw = & powershell -NoProfile -ExecutionPolicy Bypass -File $Engine -Describe
  foreach ($ln in @($raw)) {
    if ("$ln" -match '^\s*product\|([a-z0-9-]+)\|(.+?)\|(on|off)\s*$') {
      $Choices += ,@{ Key = $Matches[1]; Label = $Matches[2]; On = ($Matches[3] -eq 'on') }
    }
  }
} catch { }
# 데스크탑 앱을 **언제** 까나는 여전히 값 파일이 든다 — 무엇을 까나는 위 제품 칸이 든다.
$appWhen = Get-Directive 'desktop-app'
if ($appWhen -and $appWhen -match '^\s*([A-Za-z]+)\s*:') { $appWhen = $Matches[1] }
# ⚠ **칸이 없으면 아래 자리를 안 민다.** 빈 줄만큼 창이 길어지면 작은 화면에서 단추가 잘린다.
#   제품 줄 · VS Code 줄 · 안내 줄, 셋이다. **안내 줄은 늘 둔다** — 자리에 따라 있다 없다
#   하면 창 높이가 갈리는데, 그 높이는 자리를 재기 **전에** 정해진다.
$appRow = if ($Choices.Count) { 78 } else { 0 }
$optExtra = 26

# ── 화면 ────────────────────────────────────────────────────────────────────────
$F = New-Object Windows.Forms.Form
# 제목이 판을 든다 — 사람이 「내가 몇 판을 들고 있나」를 볼 자리가 여기밖에 없다.
$F.Text = if ($DistVersion) { "$AppName — $DistVersion" } else { $AppName }
# 제목줄과 작업표시줄의 얼굴. 없으면 파란 파워셸 아이콘이 서는데, 그것은 「이게 무슨 창인가」를
# 한 번 더 묻게 한다.
# ⚠ **없다고 막지 않는다** — 그림 한 장 때문에 설치가 안 서면 안 된다.
$IconPath = Join-Path $Here 'setup-icon.ico'
if (Test-Path -LiteralPath $IconPath) {
  try { $F.Icon = New-Object Drawing.Icon($IconPath) } catch { }
}
$F.Size = New-Object Drawing.Size(640, (710 + $appRow + $optExtra))
$F.StartPosition = 'CenterScreen'
$F.FormBorderStyle = 'FixedDialog'
$F.MaximizeBox = $false
$F.Font = New-Object Drawing.Font('Malgun Gothic', 9)

function New-Label($text, $x, $y, $w, $bold) {
  $l = New-Object Windows.Forms.Label
  $l.Text = $text; $l.Location = New-Object Drawing.Point($x, $y)
  $l.Size = New-Object Drawing.Size($w, 20); $l.AutoSize = $false
  if ($bold) { $l.Font = New-Object Drawing.Font($F.Font, [Drawing.FontStyle]::Bold) }
  $F.Controls.Add($l); return $l
}

# ⚠ **첫 줄은 자리를 안 가른다.** 고른 것은 어디서나 선다(결정 0045) — 자리가 가르는 것은
#   회사 키로 붙나 각자 로그인인가이고, 그것은 아래 키 칸의 안내가 든다. 옛 판은 그 반 줄을
#   첫 줄에 붙여 한 줄 칸을 넘쳤고, 넘친 글이 둘째 줄과 겹쳐 둘 다 못 읽었다.
$lTop = New-Label '고른 도구의 CLI · VS Code 확장 · 데스크탑 앱을 세웁니다.' 18 14 560 $true

# ── 값 ──────────────────────────────────────────────────────────────────────────
# ⚠ **주소는 사람이 넣을 것이 아니다.** 회사 안에서 모두 같은 값이라, 입력칸으로 두면
#   저마다 다르게 칠 자리를 열어 두는 꼴이다 — 한 글자만 달라도 안 닿는데 화면은 멀쩡해
#   보인다. 값이 같이 왔으면 **보여만 주고**, 안 왔을 때만 입력칸으로 뜬다.
#   바꿔야 하면 `install.env` 를 고친다 — 값의 진본은 거기지 이 화면이 아니다.
$urlPreset = [string]$Preset['ANTHROPIC_BASE_URL']

# ⚠ **자리가 값보다 먼저다.** 배포본은 사내용으로 뽑히므로 사내 값을 들고 오는데, 그 폴더를
#   사외 PC 에서 돌리는 일이 실제로 난다 — 그때 주소와 키를 물으면 **안 쓸 것을 넣으라고
#   하는 꼴**이고, 넣으면 안 닿는 곳을 가리킨 채 「설정됐다」로 보인다.
#   ⚠ 이름이 아니라 **닿음**으로 가른다: DNS 는 사외에서도 사내 IP 를 풀어 준다(결정 0026).
$offsite = $false
$probe = Get-Directive 'site-probe'
if ($probe -and ($probe -match '^(.+):(\d+)$')) {
  $c = New-Object Net.Sockets.TcpClient
  try { $offsite = -not ($c.ConnectAsync($Matches[1], [int]$Matches[2]).Wait(3000) -and $c.Connected) }
  catch { $offsite = $true } finally { $c.Dispose() }
}
$more = @()
if (Get-Directive 'codex-config')  { $more += 'Codex' }
if (Get-Directive 'gemini-config') { $more += 'Gemini' }
$gV = New-Object Windows.Forms.GroupBox
$noAsk = $offsite
# ⚠ **키 칸은 자리마다 줄 수가 다르다** — 사외는 「사외입니다」 한 줄뿐이고 사내는 주소·키·안내
#   셋이다. 높이를 한 값으로 박으면 사외에서 빈 칸이 크게 남는다. 줄인 만큼은 **아래를 당기고
#   로그 창이 받는다** — 창 높이와 단추 자리는 그대로라 아래가 안 흔들린다.
$gvH   = if ($noAsk) { 84 } else { 138 }   # 사외는 한 줄 + 링크 · 사내는 주소·키·안내 + 링크
$gvCut = 124 - $gvH
$gV.Text = if ($noAsk) { '키와 주소' } elseif ($urlPreset) { 'API 키' } else { '게이트웨이 (사내만)' }
$gV.Location = New-Object Drawing.Point(16, 62)
$gV.Size = New-Object Drawing.Size(592, $gvH)
$F.Controls.Add($gV)

$lUrl = New-Object Windows.Forms.Label
$lUrl.Text = '게이트웨이'; $lUrl.Location = New-Object Drawing.Point(14, 28)
$lUrl.Size = New-Object Drawing.Size(110, 20); $gV.Controls.Add($lUrl)

if ($noAsk) {
  $vUrl = New-Object Windows.Forms.Label
  $vUrl.Text = "사외입니다 ($probe 안 닿음) — 개인 구독으로 씁니다"
  $vUrl.Location = New-Object Drawing.Point(128, 28)
  $vUrl.Size = New-Object Drawing.Size(444, 20)
  $vUrl.ForeColor = [Drawing.Color]::DimGray
  $gV.Controls.Add($vUrl)
  $tUrl = $null
} elseif ($urlPreset) {
  $vUrl = New-Object Windows.Forms.Label
  $vUrl.Text = $urlPreset
  $vUrl.Location = New-Object Drawing.Point(128, 28)
  $vUrl.Size = New-Object Drawing.Size(444, 20)
  $vUrl.ForeColor = [Drawing.Color]::DimGray
  $gV.Controls.Add($vUrl)
  $tUrl = $null
} else {
  $tUrl = New-Object Windows.Forms.TextBox
  $tUrl.Location = New-Object Drawing.Point(128, 25)
  $tUrl.Size = New-Object Drawing.Size(444, 24)
  $gV.Controls.Add($tUrl)
}

$tKey = $null
$defaultKey = [string]$Preset['ANTHROPIC_AUTH_TOKEN']
if (-not $defaultKey) {
  # ⚠ **이미 심긴 회사 키를 읽어 온다** — 파일에 없어도 환경에 있으면 다시 칠 까닭이 없다.
  # ⚠ **같은 이름만 본다.** `OPENAI_API_KEY`·`GEMINI_API_KEY` 는 회사 키에서 **파생된 사본**
  #   이지 진본이 아니라(몸통의 5″ 칸이 한 방향으로만 심는다), 거꾸로 읽으면 제 OpenAI 키를
  #   넣어 둔 사람의 값이 이 칸에 들어온다 — 게다가 칸이 가려져 있어 **무엇이 찼는지 본인도
  #   못 본다.** 몸통이 `GOOGLE_API_KEY` 에 대고 세운 「남의 값은 안 걷는다」와 같은 축이다.
  $defaultKey = [Environment]::GetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'User')
  if (-not $defaultKey) { $defaultKey = $env:ANTHROPIC_AUTH_TOKEN }
}

if (-not $noAsk) {
  $lKey = New-Object Windows.Forms.Label
  $lKey.Text = 'API 키'; $lKey.Location = New-Object Drawing.Point(14, 60)
  $lKey.Size = New-Object Drawing.Size(110, 20); $gV.Controls.Add($lKey)
  $tKey = New-Object Windows.Forms.TextBox
  $tKey.Location = New-Object Drawing.Point(128, 57)
  $tKey.Size = New-Object Drawing.Size(444, 24)
  $tKey.UseSystemPasswordChar = $true
  $tKey.Text = [string]$defaultKey
  $gV.Controls.Add($tKey)
}

# ⚠ **사외에서는 넣을 것이 없다** — 게이트웨이를 안 타고 제 구독으로 선다. 옛 판은 둘을
#   필수로 물어, 안 쓰는 자리에서도 넣으라 하고 안 넣으면 막았다. 한 줄로 그 말만 한다.
# ⚠ **사외에서는 아예 안 만든다.** 글이 비어도 라벨은 자리를 차지하고, 뒤에 놓인 링크를
#   덮어 **클릭을 삼킨다** — 안 보이는 것과 없는 것은 다른 명제다.
if (-not $offsite) {
  $lHint = New-Object Windows.Forms.Label
  $lHint.Location = New-Object Drawing.Point(128, 86)
  $lHint.Size = New-Object Drawing.Size(444, 18)
  $lHint.ForeColor = [Drawing.Color]::DimGray
  # ⚠ **「채워져 있다」는 둘 다 찼을 때만 하는 말이다.** 주소 칸이 빈 채로 「바로 누르면
  #   된다」고 하면, 그대로 누른 사람은 주소 없이 서서 **구독 로그인으로 깔리고 초록으로
  #   끝난다** — 게이트웨이를 쓸 사람이 안 쓰게 된 것을 아무도 못 본다.
  $lHint.Text = if ($defaultKey -and $urlPreset) { '주소와 API 키가 채워져 있습니다 — 바로 [설치 시작]을 누르면 됩니다.' }
                elseif ($urlPreset)  { '주소는 채워져 왔습니다 — API 키만 넣으면 됩니다.' }
                elseif ($defaultKey) { 'API 키는 이 기계에 있던 것을 넣었습니다 — 사내면 주소를 넣습니다.' }
                else                 { '사내면 주소와 키를 넣습니다.' }
  $gV.Controls.Add($lHint)
}

# 옵션
$gO = New-Object Windows.Forms.GroupBox
$gO.Text = '옵션'; $gO.Location = New-Object Drawing.Point(16, (190 - $gvCut))
$gO.Size = New-Object Drawing.Size(592, (76 + $appRow + $optExtra))
$F.Controls.Add($gO)

$cCfg = New-Object Windows.Forms.CheckBox
$cCfg.Text = '제작자의 Claude Code 규범 · 룰 · 스킬도 깝니다'
# ⚠ **자리를 박지 않고 앱 줄만큼 민다.** 앱 줄이 없는 판(`-Describe` 가 한 줄도 안 낸 자리)에서
#   박아 둔 126 은 **칸 높이 밖**이라, 그 판에서는 이 칸이 통째로 안 보인 채 기본값으로 돈다.
$cCfg.Location = New-Object Drawing.Point(16, (48 + $appRow))
$cCfg.Size = New-Object Drawing.Size(560, 22)
$cCfg.Checked = [bool]$WithPersonalConfig
$gO.Controls.Add($cCfg)

# ⚠ **로그온할 때 자동 실행** — 작업 스케줄러(`PAISetup-AutoRun`)가 설치 몸통을 **보이는 콘솔 창**
#   으로 다시 돌려 깔린 것을 최신으로 올리고 환경을 다시 맞춘다. 설치본 자신도 `#update-repo` 의 최신
#   릴리스를 받아 지문을 대조한 뒤 그 판으로 간다(몸통 머리말).
# ⚠ **「백그라운드」라고 적지 않는다** — 창이 떠서 설치 기록이 흐른다. 옛 글자는 「백그라운드에서」였는데
#   실물은 보이는 창이라, 사람은 그 창을 보고 무엇이 도는지 몰랐다. 글자가 실물과 다르면 그만큼이
#   조용한 거짓이 된다. 보이는 창은 일부러 둔다 — 도는 것이 보이고 멈춘 걸음이 눈에 띈다.
$cAuto = New-Object Windows.Forms.CheckBox
$cAuto.Text = '로그온할 때 설치 창을 띄워 깔린 것을 최신으로 올리고 환경을 맞춥니다'
$cAuto.Location = New-Object Drawing.Point(16, (72 + $appRow))
$cAuto.Size = New-Object Drawing.Size(560, 22)
# ⚠ **못 묻는 것을 「없다」로 읽는다** — 스케줄러 모듈이 없는 판에서 나는 「그런 명령이 없다」는
#   `-ErrorAction` 으로 안 막히고, 이 줄은 창이 뜨기 **전**이라 그대로 두면 창이 아예 안 뜬다.
$hasAutoTask = $false
try { $hasAutoTask = [bool](Get-ScheduledTask -TaskName 'PAISetup-AutoRun' -ErrorAction SilentlyContinue) } catch { }
$autoDirective = Get-Directive 'autorun'
$cAuto.Checked = $hasAutoTask -or ($autoDirective -eq 'yes')
$gO.Controls.Add($cAuto)

# ⚠ **이미 선 기계에서는 이게 이 설치의 일 전부다.** 집·회사 PC 는 프로필이 안 날아가서
#   프로그램이 이미 다 있는데, 「있으면 건너뛴다」만 두면 판이 영영 안 올라간다 —
#   낡은 줄도 모른 채 몇 달을 돈다. 비영속 VDI 는 어차피 맨바닥이라 이 칸이 안 걸린다.
$cUpg = New-Object Windows.Forms.CheckBox
$cUpg.Text = '이미 깔린 것도 최신으로 올립니다'
$cUpg.Location = New-Object Drawing.Point(16, 22)
$cUpg.Size = New-Object Drawing.Size(560, 22)
$cUpg.Checked = -not $NoUpgrade
$gO.Controls.Add($cUpg)

# ⚠ **글자도 기본값도 몸통이 준 것을 그대로 쓴다** — 여기서 다시 지으면 두 벌이 된다.
# 한 칸이 그 제품의 CLI · 확장 · 데스크탑 앱을 통째로 든다. **뺀 것은 아무 데도 안 깔린다.**
$cApps = @()
$cVsc  = $null
if ($Choices.Count) {
  $lApp = New-Object Windows.Forms.Label
  $lApp.Text = '설치할 것'
  $lApp.Location = New-Object Drawing.Point(16, 50)
  $lApp.Size = New-Object Drawing.Size(84, 20)
  $gO.Controls.Add($lApp)
  $x = 104
  foreach ($choice in $Choices) {
    $c = New-Object Windows.Forms.CheckBox
    $c.Text = $choice.Label
    # ⚠ **글자를 재서 칸을 맞춘다.** 폭을 박아 두면 이름이 긴 제품에서 뒷글자가 잘리는데,
    #   잘린 줄은 **화면에서만 보이고** 아무 검사에도 안 걸린다.
    $c.AutoSize = $true
    $c.Location = New-Object Drawing.Point($x, 48)
    $c.Checked = [bool]$choice.On
    $c.Tag = $choice.Key
    $gO.Controls.Add($c)
    $cApps += ,$c
    $x += $c.Width + 14
  }

  # ⚠ **사외 기본은 끔이다** — 데스크탑 앱만으로 서는 자리라 VS Code 를 안 받아도 된다.
  #   사내는 VS Code 가 주 무대라 켜 둔다. 자리는 위에서 이미 쟀다(`$offsite`).
  $cVsc = New-Object Windows.Forms.CheckBox
  $cVsc.Text = 'VS Code 와 확장도 깝니다  (사내는 필수, 사외는 선택)'
  # ⚠ **「필수」라 적었으면 못 꺼야 한다.** 끌 수 있는데 필수라 적으면 그 글이 거짓말이 된다 —
  #   사내는 켠 채로 잠그고, 사외는 기본을 끈 채 사람에게 맡긴다.
  $cVsc.Location = New-Object Drawing.Point(16, 76)
  $cVsc.Size = New-Object Drawing.Size(560, 22)
  $cVsc.Checked = -not $offsite
  $cVsc.Enabled = $offsite
  $gO.Controls.Add($cVsc)

  # ⚠ **고르기는 자리를 안 가리는데 깔기는 가린다** — 안 적으면 사내에서 켜 놓고
  #   「왜 안 깔렸지」가 된다. 줄은 늘 두고 **글만 갈린다**(위 창 높이 ⚠).
  $lApp2 = New-Object Windows.Forms.Label
  $lApp2.Text = if ($appWhen -eq 'offsite' -and -not $offsite) {
    '켠 것의 CLI 와 확장이 깔립니다 — 데스크탑 앱은 사외에서만 깔립니다.'
  } elseif ($appWhen) {
    '켠 것의 CLI · 확장 · 데스크탑 앱이 깔립니다.'
  } else {
    '켠 것의 CLI 와 확장이 깔립니다.'
  }
  $lApp2.Location = New-Object Drawing.Point(18, 102)
  $lApp2.Size = New-Object Drawing.Size(560, 20)
  $lApp2.ForeColor = [Drawing.Color]::DimGray
  $gO.Controls.Add($lApp2)
}

# ── 내 저장소 받기 (선택) ───────────────────────────────────────────────────────
# ⚠ **이 칸이 드는 일은 「받아 둔다」 하나다.** 옛 이름(「설정 저장소」)은 **훅을 든 저장소**를
#   전제로 말했는데, 보통 사람은 그런 저장소가 없고 그냥 제 저장소를 받아 두는 자리로 쓴다 —
#   이름이 전제를 깔면 안 맞는 사람이 「나는 못 쓰는 칸」으로 읽고 지나친다.
# ⚠ **넣어도 위 키 칸은 그대로 산다.** 설치는 자리만 보고 전부 세우고, 저장소는 **그 뒤에** 받는다.
#   뿌리에 SessionStart 훅이 있으면 그것을 `--install` 로 불러 **그 뒤(사람에게 딸린 것)를 잇게**
#   한다 — 없으면 받아 둔 것으로 끝난다. 둘 다 정당하다.
# ⚠ **여러 개를 빈칸으로 가른다.** 주소에는 빈칸이 없으므로 그것이 가르는 자다.
#   ⚠ 여럿을 든 사람이 **제 훅 선언에 목록을 들었으면** 여기는 그 하나만 적는 것이 맞다 —
#     두 자리에 적으면 저장소가 늘 때 한쪽이 낡는다. 어느 쪽이 맞나는 그 사람이 안다.
# ⚠ **배포본에는 이 값이 안 실려 온다.** 남에게 갈 파일에 내 저장소 주소를 박지 않기 때문이다.
#   그러니 이 칸이 비어 있는 것이 받는 사람에게는 정상이다.
$gR = New-Object Windows.Forms.GroupBox
$gR.Text = '내 저장소 받기 (선택) — git 주소, 여러 개는 빈칸으로'
$gR.Location = New-Object Drawing.Point(16, (278 + $appRow + $optExtra - $gvCut))
$gR.Size = New-Object Drawing.Size(592, 98)
$F.Controls.Add($gR)

$tRepo = New-Object Windows.Forms.TextBox
$tRepo.Location = New-Object Drawing.Point(14, 24)
$tRepo.Size = New-Object Drawing.Size(558, 24)
# ⚠ **옆에 온 값 파일에 없으면 판을 넘겨 사는 자리를 본다** — 키 칸이 환경변수로 되돌아가는 것과
#   같은 결이다(위 「비었으면 이미 심긴 것을 본다」). 이 좌표는 배포본에 안 실려 오므로
#   **한 번 넣은 사람에게만 있는 값**인데, 그것이 판 폴더에 있으면 다음 판에 조용히 사라진다.
#   그때 이 칸이 비어 뜨고 그대로 누르면 **그 판은 저장소를 안 본다** — 아래 곁말이 「화면이 든다」로
#   세운 규율이 여기서는 사슬을 끊는 쪽으로 돈다. 끊기지 않게 하는 것이 이 두 줄이다.
$tRepo.Text = [string](Get-Directive 'config-repo')
if (-not $tRepo.Text) { $tRepo.Text = [string](Get-Directive 'config-repo' $KeptEnvPath) }
$gR.Controls.Add($tRepo)

$lRepo = New-Object Windows.Forms.Label
$lRepo.Location = New-Object Drawing.Point(16, 52)
$lRepo.Size = New-Object Drawing.Size(556, 18)
$lRepo.ForeColor = [Drawing.Color]::DimGray
# ⚠ **한 줄이다** — 칸 이름이 이미 「내 저장소 받기」라, 여기서 다시 말할 것은 어디에 받나와
#   설정 저장소일 때 더 따라오는 것뿐이다.
$lRepo.Text = '~/repos/<이름> 에 받습니다 — 설정 저장소면 개인 키 · 형제 저장소 · 배포까지 이어집니다.'
$gR.Controls.Add($lRepo)

# ── 안내 한 장을 여는 링크 ──────────────────────────────────────────────────────
# ⚠ **자리를 박지 않는다.** 안내는 이 스크립트와 같은 폴더에 같이 와 있다 — 사람이 폴더를
#   어디에 풀었는지는 아무도 모르므로 `$Here` 에서 파생한다. 절대 경로를 박으면 만든 사람
#   PC 에서만 열린다.
# ⚠ **없을 때 조용히 지나가지 않는다.** 눌렀는데 아무 일도 안 나면 「내 컴퓨터가 이상한가」
#   에서 멈춘다 — 무엇이 어디에 없는지를 경로까지 대고 말한다.
$lnkRepo = New-Object Windows.Forms.LinkLabel
$lnkRepo.Text = '설정 저장소란? 만드는 법'
$lnkRepo.Location = New-Object Drawing.Point(388, 72)
$lnkRepo.Size = New-Object Drawing.Size(184, 18)
$lnkRepo.TextAlign = 'MiddleRight'
$lnkRepo.Add_LinkClicked({
  $howto = Join-Path $Here 'config-repo-howto.html'
  if (Test-Path -LiteralPath $howto) {
    try { Start-Process -FilePath $howto | Out-Null }
    catch {
      [Windows.Forms.MessageBox]::Show(
        "안내를 못 열었습니다 — $($_.Exception.Message)" + [Environment]::NewLine + $howto,
        $AppName, 'OK', 'Warning') | Out-Null
    }
  } else {
    [Windows.Forms.MessageBox]::Show(
      '안내 파일이 이 폴더에 없습니다 — ' + [Environment]::NewLine + $howto,
      $AppName, 'OK', 'Warning') | Out-Null
  }
})
$gR.Controls.Add($lnkRepo)

# 넣어도 위 키 칸은 그대로 산다 — 무엇이 더 서는지만 화면이 보여준다

# ── 후버로 조금 더 내린다 ────────────────────────────────────────────────────────
# ⚠ **여기에 긴 이력을 적지 않는다.** 자세한 것은 옆 링크가 여는 안내 한 장이 든다 —
#   툴팁과 그 문서에 같은 글을 두 벌 두면 고칠 때 한쪽만 고쳐진다. 이 자리가 드는 것은
#   「무엇을 하는 칸인가」와 갈래 둘, 그리고 **더 볼 데가 있다는 것**뿐이다.
$tip = New-Object Windows.Forms.ToolTip
$tip.AutoPopDelay = 30000      # 긴 글이라 오래 띄운다
$tip.InitialDelay = 400
$tip.ReshowDelay  = 200
$tip.ShowAlways   = $true
$tipText = @'
아무 git 저장소나 받아 두는 자리입니다 — 코드 저장소도, 설정 저장소도.
비워 두는 것이 기본이고 맞는 답입니다: 프로그램·확장·CLI·키·주소·프록시·
사내 문서·씨앗·그림 문은 이 칸과 무관하게 다 깔립니다.

넣으면 ~/repos/<저장소 이름> 으로 받습니다. 여러 개는 빈칸으로 가릅니다.
코드 저장소는 그것으로 끝입니다. 설정 저장소만 한 걸음 더 갑니다:

받은 뒤 갈래가 둘이고 둘 다 정당합니다. 가르는 자는 파일 이름 하나 —
받아온 저장소 뿌리의 .claude/hooks/session-start.sh 입니다.

  · 든 저장소가 있으면  --install 로 부릅니다. 그 뒤는 그 저장소가 잇습니다
  · 어디에도 없으면      받아 둔 것으로 끝냅니다

설정 저장소가 무엇이고 어떻게 만드나는 오른쪽 링크가 한 장으로 답합니다.
'@
$tip.SetToolTip($tRepo, $tipText)
$tip.SetToolTip($lRepo, $tipText)

# 진행
$bar = New-Object Windows.Forms.ProgressBar
$bar.Location = New-Object Drawing.Point(16, (388 + $appRow + $optExtra - $gvCut))   # 홈 안내 줄·링크 줄(420-456) 아래
$bar.Size = New-Object Drawing.Size(592, 20)
$bar.Minimum = 0; $bar.Maximum = 100
$F.Controls.Add($bar)

# ── 홈에 놓이는 것 — 스위치 없는 것일수록 누르기 전에 말한다 ─────────────────────
# ⚠ **목록을 여기 옮기지 않는다.** 무엇이 어디에 놓이나의 진본은 install.ps1 의 [7/8] 표와
#   README 「무엇이 깔리나」다 — 창은 그런 것이 놓인다는 한 줄과, 그것이 든 폴더로 가는 문만 든다.
#   씨앗 셋은 고를 것이 아니라 환경이라 스위치가 없고, 그래서 더 말해야 한다 — 동의 없이 놓인다.
# ⚠ **여는 것은 풀어 둔 이 폴더다** — README 와 홈으로 갈 씨앗의 원본이 같이 있다. 홈 쪽
#   (`~/.claude/seeds`)은 설치 뒤에야 서서 누르기 전엔 열 것이 없다.
$lnkHome = New-Object Windows.Forms.LinkLabel
$lnkHome.Text = '사내 환경 문서 위치 — 폴더 열기'
$lnkHome.Location = New-Object Drawing.Point(14, $(if ($noAsk) { 54 } else { 110 }))
$lnkHome.Size = New-Object Drawing.Size(400, 16)
$lnkHome.Add_LinkClicked({
  try { Start-Process -FilePath 'explorer.exe' -ArgumentList ('"' + $Here + '"') | Out-Null }
  catch {
    [Windows.Forms.MessageBox]::Show(
      "폴더를 못 열었습니다 — $($_.Exception.Message)" + [Environment]::NewLine + $Here,
      $AppName, 'OK', 'Warning') | Out-Null
  }
})
$gV.Controls.Add($lnkHome)

# 설치 흐름 그림 — 같은 폴더의 `install-flow.svg`(README 가 든 그 그림). 브라우저가 연다.
# ⚠ 없으면 경로를 대고 말한다 — howto 링크와 같은 까닭(눌렀는데 아무 일도 안 나면 사람은 멈춘다).
$lnkFlow = New-Object Windows.Forms.LinkLabel
$lnkFlow.Text = '설치흐름'
# ⚠ **오른쪽 끝이 담는 상자 안에 들어야 한다** — 이 링크는 창이 아니라 `$gV`(너비 592) 안에
#   산다. 옛 판은 창 기준 좌표(468)를 상자로 옮겨 오면서 그대로 뒀고, 466+140=606 이라
#   **14픽셀이 잘렸다**(실측 2026-09-17). 왼쪽 링크(`$lnkHome`)가 쓰는 여백 14 를 맞춰
#   592-14-140 = 438 에 세운다. **상자 너비를 고치면 이 수도 같이 고친다.**
$lnkFlow.Location = New-Object Drawing.Point(438, $(if ($noAsk) { 54 } else { 110 }))
$lnkFlow.Size = New-Object Drawing.Size(140, 16)
$lnkFlow.TextAlign = 'MiddleRight'
$lnkFlow.Add_LinkClicked({
  $svg = Join-Path $Here 'install-flow.svg'
  if (Test-Path -LiteralPath $svg) {
    try { Start-Process -FilePath $svg | Out-Null }
    catch {
      [Windows.Forms.MessageBox]::Show(
        "그림을 못 열었습니다 — $($_.Exception.Message)" + [Environment]::NewLine + $svg,
        $AppName, 'OK', 'Warning') | Out-Null
    }
  } else {
    [Windows.Forms.MessageBox]::Show(
      '그림 파일이 이 폴더에 없습니다 — ' + [Environment]::NewLine + $svg,
      $AppName, 'OK', 'Warning') | Out-Null
  }
})
$gV.Controls.Add($lnkFlow)

$lState = New-Label '' 18 (410 + $appRow + $optExtra - $gvCut) 500 $false

# 기록 — 몸통이 찍는 줄을 그대로 옮긴다
$log = New-Object Windows.Forms.TextBox
$log.Location = New-Object Drawing.Point(16, (432 + $appRow + $optExtra - $gvCut))
$log.Size = New-Object Drawing.Size(592, (186 + $gvCut))   # 키 칸과 링크 줄이 비운 만큼 받는다
$log.Multiline = $true; $log.ReadOnly = $true
$log.ScrollBars = 'Vertical'; $log.WordWrap = $false
$log.BackColor = [Drawing.Color]::FromArgb(30, 30, 30)
$log.ForeColor = [Drawing.Color]::Gainsboro
$log.Font = New-Object Drawing.Font('Consolas', 9)
$F.Controls.Add($log)

$bGo = New-Object Windows.Forms.Button
$bGo.Text = '설치 시작'; $bGo.Location = New-Object Drawing.Point(416, (628 + $appRow + $optExtra))
$bGo.Size = New-Object Drawing.Size(100, 30)
$F.Controls.Add($bGo); $F.AcceptButton = $bGo

$bClose = New-Object Windows.Forms.Button
$bClose.Text = '닫기'; $bClose.Location = New-Object Drawing.Point(524, (628 + $appRow + $optExtra))
$bClose.Size = New-Object Drawing.Size(84, 30)
$F.Controls.Add($bClose)

# ── 돌리는 자 ───────────────────────────────────────────────────────────────────
# ⚠ **`Register-ObjectEvent -Action` 을 안 쓴다 — 그것이 여태 한 줄도 안 나오던 까닭이다.**
#   그 블록은 파워셸이 **한가할 때만** 돈다. 그런데 창이 떠 있는 동안 런스페이스는 계속
#   `ShowDialog()` 를 실행 중이라, 자식이 뱉은 줄이 큐에만 쌓이고 **창이 닫힐 때까지 핸들러가
#   한 번도 안 불린다.** 그래서 기록 칸이 비고, `[n/8]` 을 못 봐 막대 구간이 0/0 이고,
#   심장박동 조건(`segHi > segLo`)도 영영 안 선다 — 고쳐 온 것이 전부 이 아래층이었다.
#
# ⚠ **대신 파일로 받는다.** 자식 출력을 파일에 돌리고, 타이머가 그 파일을 **따라 읽는다.**
#   타이머는 창의 메시지 루프가 돌리므로 `ShowDialog()` 안에서도 산다 — 파워셸의 한가함에
#   기대지 않는다. 읽는 쪽은 파일을 열어 둔 채 `ReadLine()` 이 null 을 낼 때까지만 읽고,
#   다음 틱에 이어서 읽는다. 자식이 쓰는 중인 파일이라 **공유 열기**여야 한다.
$script:segLo = 0; $script:segHi = 0   # 지금 칸이 차지하는 구간 — 그 안에서 낱줄이 민다
$script:idle  = 0                     # 조용한 틱 수 — 쌓이면 막대를 천천히 민다
$script:proc = $null; $script:tmpEnv = $null
$script:sw = $null; $script:last = ''   # 흐른 시간과 마지막 줄 — 창이 살아 있음을 보인다
$script:done = ''                       # 몸통이 낸 마무리 문장 — 끝났을 때 이것을 띄운다
$script:outFile = $null; $script:errFile = $null
$script:rdOut = $null;  $script:rdErr = $null
$script:con = $null; $script:raise = 0   # 뒤에 서는 기록 창과, 이 창을 다시 올릴 남은 틱 수

function Add-Log([string]$line) {
  $log.AppendText($line + "`r`n")
}

$bGo.Add_Click({
  # ⚠ **비어 있는 것은 안 막는다** — 사외는 둘 다 비우는 것이 맞는 답이다. 막는 것은
  #   **반만 넣은 것** 하나다: 한쪽만 있으면 게이트웨이가 안 서는데 화면은 멀쩡해 보인다.
  $url = if ($noAsk) { '' } elseif ($tUrl) { $tUrl.Text.Trim() } else { $urlPreset }
  $key = if ($tKey) { $tKey.Text.Trim() } else { '' }
  if (-not $noAsk -and (($url -and -not $key) -or ($key -and -not $url))) {
    [Windows.Forms.MessageBox]::Show(
      '게이트웨이 주소와 API 키는 둘 다 넣거나 둘 다 비워야 합니다.' + [Environment]::NewLine +
      '사외면 둘 다 비워 두세요 — 구독 로그인으로 섭니다.',
      $AppName, 'OK', 'Warning') | Out-Null
    return
  }
  $bGo.Enabled = $false; $gV.Enabled = $false; $gO.Enabled = $false; $gR.Enabled = $false
  $log.Clear(); $bar.Value = 0; $lState.Text = '시작합니다…'
  # ⚠ **준비 구간을 미리 연다.** 첫 `[n/8]` 이 나오기 전에도 할 일이 있다 — winget 이 없으면
  #   되살리느라 수십 MB 를 받는다. 그동안 구간이 0/0 이면 심장박동이 못 뛰어 막대가 0 에
  #   못 박히고, 사람은 **아무것도 안 하는 줄 안다**(실제로 그렇게 보였다).
  $script:segLo = 0; $script:segHi = 8; $script:idle = 0
  $script:sw = [Diagnostics.Stopwatch]::StartNew()
  $script:last = '준비'
  # ⚠ **지난 판의 마무리 문장을 지운다.** 안 지우면 이번 판이 그 줄을 못 내도 옛 문장이
  #   그대로 떠, 방금 한 일과 다른 말을 한다.
  $script:done = ''

  # ⚠ **값은 임시 파일로 건넨다.** 몸통이 값을 받는 길을 하나로 두려는 것이다 — 화면용
  #   통로를 따로 내면 두 갈래가 서로 다른 코드를 탄다. 끝나면 지운다.
  $script:tmpEnv = [IO.Path]::Combine([IO.Path]::GetTempPath(), "claude-setup-$PID.env")
  $lines = New-Object System.Collections.Generic.List[string]
  # ⚠ **게이트웨이와 무관한 값은 사외에도 그대로 간다.** 옛 판은 사외로 갈리면 값 파일의 값
  #   줄을 **한 줄도 안 넘겼다** — 게이트웨이와 상관없는 `CLAUDE_CODE_EFFORT_LEVEL` ·
  #   스트림 유휴 제한 둘 · `ATELIER_SITES` · `ANTHROPIC_MODEL` 이 다 같이 떨어졌다.
  #   그래서 **같은 PC 인데** 화면으로 깐 사람만 그 값이 안 서고, 콘솔 갈래로 내려가거나
  #   `install.ps1` 을 직접 돌린 사람은 섰다 — 바로 아래 ⚠ 가 금하는 그 일이다.
  # ⚠ **몸통과 같은 갈림이어야 한다.** 몸통이 사외에서 버리는 것은 `$Vars` 의 `Gateway=$true`
  #   **둘뿐**이고, 그 둘이 여기 걸러지는 이름 둘과 같다. 거르는 자리가 둘이라 이름이 늘면
  #   두 자리를 같이 봐야 한다 — 이름을 늘리는 자는 몸통의 그 표다.
  foreach ($k in $Preset.Keys) {
    if ($k -in @('ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN')) { continue }
    if ($Preset[$k]) { $lines.Add("$k=$($Preset[$k])") }
  }
  # 빈 값은 안 적는다 — 적으면 몸통이 「게이트웨이를 쓴다」로 읽는다
  if ($url) { $lines.Add("ANTHROPIC_BASE_URL=$url") }
  if ($key) { $lines.Add("ANTHROPIC_AUTH_TOKEN=$key") }
  # ⚠ 지시(`#…`)를 그대로 옮긴다. 안 옮기면 몸통이 settings.json 에 밀라는 말도, 자리를
  #   가르라는 말도 못 듣는다 — 화면을 거쳤다는 이유로 갈래가 달라지면 안 된다.
  # ⚠ **`config-repo` 만은 화면이 든다.** 파일에 있던 것을 흘리면, 사람이 칸을 비워도 옛
  #   주소로 clone 이 돈다 — 지운 것이 안 지워지는 자리다.
  # ⚠ **`site` 도 화면이 든다.** 아래에서 우리가 잰 값을 적으므로, 파일에 있던 것을 같이
  #   흘리면 한 이름이 두 줄이 되고 **먼저 적힌 쪽(파일)이 이긴다** — 방금 잰 것이 낡은 글자에
  #   진다. 화면이 재는 이름은 화면만 적는다(`config-repo` 와 같은 결).
  if (Test-Path -LiteralPath $EnvPath) {
    foreach ($line in Get-Content -LiteralPath $EnvPath -Encoding UTF8) {
      if ($line -match '^\s*#\s*config-repo\s*=') { continue }
      if ($line -match '^\s*#\s*site\s*=')        { continue }
      if ($line -match '^\s*#\s*desktop-app\s*=')  { continue }
      if ($line -match '^\s*#\s*[A-Za-z][A-Za-z0-9-]*\s*=\s*.+$') { $lines.Add($line.Trim()) }
    }
  }
  $repo = $tRepo.Text.Trim()
  if ($repo) { $lines.Add("#config-repo = $repo") }
  # ⚠ **언제 까나(`$appWhen`)만 파일 줄로 흘린다** — 그것은 사람이 정한 것이 아니라 자리
  #   정책이다. **무엇을 까나는 아래 `-Pick` 인자가 든다** — 파일 줄로도 흘리면 한 이름이
  #   두 자리에 살고, 사람이 방금 끈 제품이 옛 글자로 되살아난다.
  if ($appWhen) { $lines.Add("#desktop-app = $appWhen") }
  # ⚠ **자리는 이 화면이 이미 쟀다 — 몸통에 넘긴다.** 같은 물음을 몸통이 또 물으면 두
  #   프로세스·두 시점이라 **답이 갈릴 수 있고, 갈려도 아무 데도 안 찍힌다**(프록시가 흔들리는
  #   VDI · 무선 전환 · 회사망 재인증). 갈리면 여기서 받은 키를 몸통이 버리거나, 주소가 빈
  #   채로 게이트웨이를 쓴다고 서거나 하는데 **둘 다 초록으로 끝난다.** 재는 자를 하나로 둔다.
  # ⚠ **못 잰 판에서는 안 넘긴다.** 프로브 줄이 없으면 위 `$offsite` 는 「사외가 아니다」지
  #   「사내다」가 아니다 — 그것을 넘기면 **안 잰 것이 「사내」라는 판정이 된다.** 자리는 셋이고
  #   (사내 · 사외 · 모름) 모름은 몸통이 제 자리에서 모름으로 들어야 한다.
  if ($probe) { $lines.Add('#site = ' + $(if ($offsite) { 'outside' } else { 'inside' })) }
  Set-Content -LiteralPath $script:tmpEnv -Value $lines -Encoding UTF8

  $argv = @('-NoProfile','-ExecutionPolicy','Bypass','-File', $Engine, '-Yes',
            '-EnvFile', $script:tmpEnv)
  # ⚠ **화면에는 칸이 없다** — Claude Code 를 깔러 온 사람에게 git 은 옵션이 아니다.
  #   인자는 남는다: 콘솔로 이 껍데기를 `-NoDevTools` 로 부른 사람의 뜻은 그대로 넘긴다.
  if ($NoDevTools) { $argv += '-NoDevTools' }
  if ($cCfg.Checked)      { $argv += '-WithPersonalConfig' }
  if (-not $cUpg.Checked) { $argv += '-NoUpgrade' }
  if ($cAuto.Checked)     { $argv += '-AutoRun' }
  else                    { $argv += '-NoAutoRun' }
  # ⚠ **하나도 안 골라도 인자를 준다.** 안 주면 몸통이 「값이 없으니 기본값」으로 읽어
  #   **사람이 방금 다 끈 것을 되살린다** — 빈 값과 부재는 다른 명제다.
  if ($cApps.Count) {
    $picked = @($cApps | Where-Object { $_.Checked } | ForEach-Object { [string]$_.Tag })
    $argv += @('-Pick', ($picked -join ','))
  }
  if ($cVsc -and -not $cVsc.Checked) { $argv += '-NoVsCode' }

  # 싸는 규칙은 위 `Quote-Argv` 하나다 — 되띄우기 자리와 같은 자를 쓴다.
  $argLine = Quote-Argv $argv

  $base = [IO.Path]::Combine([IO.Path]::GetTempPath(), "claude-setup-$PID")
  $script:outFile = "$base.out"; $script:errFile = "$base.err"
  $script:rdOut = $null; $script:rdErr = $null

  # ⚠ 나가는 것과 오류를 **한 파일에 못 돌린다** — 그래서 둘로 받고 타이머가 둘 다 읽는다.
  # ⚠ **무엇을 돌리는지 먼저 찍는다.** 자식이 한 줄도 안 뱉는 판에서 화면이 빈 채로 있으면
  #   「멈췄나 안 떴나」를 가를 자리가 없다 — 이 줄이 있으면 적어도 창은 제 일을 했다.
  Add-Log "돌립니다: $argLine"
  Add-Log ''

  # ⚠ **`Start-Process -PassThru` 로 띄우지 않는다.** 그것이 돌려주는 객체는 자식이 끝나도
  #   `ExitCode` 를 안 든다 — 값이 0 인 것이 아니라 **없다**(null). `-Wait` 를 걸면 들지만
  #   화면은 기다릴 수 없다(메시지 루프가 멈춘다). 그래서 아래 판정의 `$rc -eq 0` 이
  #   **성공한 설치에서도 거짓**이었고, 창은 늘 빨갛게 「끝내지 못했습니다 (코드 )」로
  #   끝났다 — 빈 괄호가 그 증거다 (실측 2026-09-10 · 사외 VDI · 로그에 실패가 한 줄도
  #   없는 판. 자식이 0·1·7 로 끝나는 것을 다 재봤고 셋 다 null 이었다).
  # ⚠ 그래서 **진짜 Process 객체**를 직접 띄운다 — 그것은 핸들을 쥐고 있어 종료코드를 든다.
  #   다만 진짜 Process 는 파일로 못 돌린다(파이프만 준다). `cmd /c` 를 한 겹 두고
  #   리다이렉트를 **cmd 에 시킨다** — 돌리는 자가 OS 라 `Write-Host` 줄까지 파일에 담기고,
  #   cmd 는 자식의 종료코드를 그대로 물려준다. 나가는 것과 오류는 여전히 두 파일이다.
  # ⚠ `CreateNoWindow` 는 `-NoNewWindow` 가 세우던 바로 그 값이다 — 창이 새로 안 뜬다.
  # ⚠ **들어오는 손잡이까지 준다 — `0<NUL`.** `CreateNoWindow` 로 띄운 자식은 콘솔이 없고,
  #   나가는 것만 `1>`·`2>` 로 돌렸으므로 **표준입력이 아무것도 아니게 된다.** 그 빈 손잡이가
  #   사슬을 타고 끝까지 내려가, 자식을 다시 띄우려는 자리에서 죽는다 — `python -m venv` 가
  #   pip 을 깔 때 `[WinError 6]` 으로 진 것이 그것이다 (실측 2026-09-10: 사내·사외 VDI 가
  #   똑같이, 꺼진 검사 셋을 안고 초록으로 끝났다). NUL 은 성한 손잡이라 복제가 선다.
  #   훅도 제 자리에서 같은 것을 막는다 — 여기는 파이썬 말고 다른 자식까지 같이 구하는 자리다.
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
    # ⚠ **예외를 삼키면 창이 「시작합니다」에서 굳는다.** 아무 일도 안 일어나는데 아무도
    #   까닭을 모른다 — 부재가 통과로 읽히는 것과 같은 자리다.
    Add-Log "! 못 띄웠다 — $($_.Exception.Message)"
    $lState.Text = '못 띄웠습니다 — 위 기록을 보세요.'
    $lState.ForeColor = [Drawing.Color]::Firebrick
    $bGo.Text = '다시 설치'; $bGo.Enabled = $true
    $gV.Enabled = $true; $gO.Enabled = $true; $gR.Enabled = $true
    return
  }

  # ── 뒤에 서는 큰 기록 창 (`Start-ConsoleTail` 머리말) ──
  # ⚠ **못 띄워도 설치는 간다.** 이 창의 기록 칸이 같은 줄을 이미 들고 있다 — 덤 창 하나
  #   때문에 설치를 세우지 않는다. 대신 못 띄운 것은 말한다(부재가 통과로 읽히지 않게).
  try {
    $script:con = Start-ConsoleTail $script:outFile $script:errFile $script:proc.Id
    # ⚠ **새 콘솔은 뜨면서 맨 앞을 차지한다** — 그대로 두면 이 창을 덮는다. 뜨는 데 걸리는
    #   시간이 콘솔마다 달라(옛 콘솔은 곧바로, Terminal 은 1초 남짓) 한 번이 아니라 몇 초에
    #   걸쳐 이 창을 다시 위로 올린다 — 타이머가 센다(아래 `$script:raise`).
    $script:raise = 20
  } catch {
    Add-Log "! 큰 기록 창을 못 띄웠다 — 이 창의 기록으로 그대로 본다: $($_.Exception.Message)"
  }
  $timer.Start()
})

# ── 한 줄을 화면에 반영하는 자 ─────────────────────────────────────────────────
# 진행률의 신호는 몸통이 사람에게 하는 말 그대로다 — 통로를 따로 안 낸다.
# ⚠ **칸 안에서도 올라가야 한다.** `[n/8]` 을 볼 때 막대를 `(n-1)/8` 에 놓고 두면 첫 칸이 곧
#   0% 인데 **첫 칸이 제일 오래 걸린다**. 칸의 시작과 끝을 잡아 두고 그 안에서
#   몸통이 한 줄 찍을 때마다 끝을 향해 조금씩 민다 — **낱줄이 곧 눈금이다.**
function Step-Line([string]$line) {
  Add-Log $line
  if ($line -match '^\[(\d+)/(\d+)\]\s*(.*)$') {
    $done = [int]$Matches[1]; $all = [int]$Matches[2]
    $script:segLo = [int](($done - 1) * 100 / $all)
    $script:segHi = [int]($done * 100 / $all)
    $bar.Value = $script:segLo
    $script:last = "$done/$all  $($Matches[3])"
  } elseif ($line -match '^=== 검증') {
    $script:segLo = 100; $script:segHi = 100
    $bar.Value = 100; $script:last = '검증'
  } elseif ($line -match '^=== 끝 ===\s*(.+)$') {
    # ⚠ **마무리 문장을 여기 또 적지 않는다.** 몸통이 갈래마다 다른 말을 한다 — 창을
    #   띄웠나 · 떠 있어서 안 띄웠나 · 못 찾았나 · 안 띄우기로 했나. 그 문장을 이쪽에 사본으로
    #   두면 갈래가 늘 때마다 **한쪽만 낡고**, 낡은 줄은 멀쩡한 설치를 딴 데로 보낸다.
    $script:done = $Matches[1].Trim()
  } elseif ($line.Trim()) {
    # 칸 안의 낱줄 — 끝의 한 칸 앞까지만 민다. 끝을 미리 채우면 다음 칸이 뒤로 가는 꼴이 된다.
    if ($script:segHi -gt $script:segLo -and $bar.Value -lt ($script:segHi - 1)) {
      $stepBy = [Math]::Max(1, [int](($script:segHi - $script:segLo) / 6))
      $bar.Value = [Math]::Min($script:segHi - 1, $bar.Value + $stepBy)
    }
    # 무엇을 하는 중인지도 같이 보여준다 — 막대만 움직이면 무슨 일인지는 여전히 모른다.
    $script:last = $line.Trim()
  }
}

# 아직 안 열렸으면 연다. 자식이 **쓰는 중인** 파일이라 공유 열기여야 한다.
# ⚠ **지우기까지 열어 준다(`Delete`).** 이 함수는 뒤에 서는 기록 창(`Start-ConsoleTail`)에도
#   글자째 실려 가는데, 그 창은 이 창과 **따로 사는 프로세스**라 이 창이 캡처 파일을 지우는
#   순간에도 쥐고 있을 수 있다. 그때 `Delete` 가 없으면 지우기가 조용히 지고
#   (`-ErrorAction SilentlyContinue`) **키 없는 캡처라도 임시 폴더에 눌러앉는다.** 이 창 자신은
#   지우기 전에 늘 닫으므로 덤이지만, 여는 법은 한 자리라 여기서 푼다.
function Open-Tail([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  try {
    $fs = New-Object IO.FileStream($Path, [IO.FileMode]::Open,
            [IO.FileAccess]::Read, ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
    return New-Object IO.StreamReader($fs, [Text.Encoding]::UTF8)
  } catch { return $null }
}

# 열린 만큼 읽어 화면에 민다. 읽을 것이 없으면 그대로 두고 다음 틱에 이어 읽는다.
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

# ── 뒤에 서는 큰 기록 창 — **같은 캡처를 따로 한 번 더 읽을 뿐이다** ───────────────
# 이 창은 막대와 마지막 한 줄만 보여 준다. 로그온 자동 실행처럼 몸통이 찍는 줄을 **통째로,
# 큰 글씨로** 흘려 주는 창을 이 창 뒤에 하나 세운다 — 무엇을 하는 중인지, 어디서 멈췄는지가
# 사람 눈에 바로 보이게.
#
# ⚠ **출력을 새로 만들지 않는다.** 몸통은 여태처럼 숨은 채 두 캡처 파일에 쓰고, 이 창은 위
#   `Open-Tail` 로 **같은 파일을 따로 따라 읽어** 제 콘솔에 옮길 뿐이다. 통로를 하나 더 내면
#   (몸통을 보이게 띄우거나 `Tee` 로 갈라 쓰거나) 두 갈래가 서로 다른 것을 보여 주는 날이 온다.
#   ⚠ 여는 법도 글자째 실어 간다(`${function:Open-Tail}`) — 공유 깃발을 두 벌 두지 않는다.
#
# ⚠ **빈 창이 뜨는 자리를 안 밟는다.** 콘솔 창이 떴는데 한 줄도 안 나오는 것은, 창을 가진
#   프로세스의 출력이 **파일로 돌려져** 창이 아니라 파일에 쓰기 때문이다 — 몸통을 보이게 띄우면
#   `1>` 가 걸려 있어 꼭 그렇게 된다(몸통이 숨은 채 도는 까닭). 이 창은 **아무것도 안 돌린 제
#   콘솔**에 `Write-Host` 로 쓴다: `Start-Process`(셸 실행) 는 새 콘솔을 따로 붙여 주고, 여기에는
#   `-NoNewWindow` 도 `-Redirect*` 도 없다. 부모인 이 창은 콘솔이 없어도 상관없다.
#
# ⚠ **읽는 쪽이 느려져도 설치는 안 멈춘다.** 몸통은 파일에 쓰므로, 사람이 콘솔 안을 끌어
#   선택하는 바람에(빠른 편집) 이 창의 쓰기가 멈춰도 몸통은 모른다. 몸통의 출력을 이 창에
#   **파이프로** 잇지 않는 까닭이 그것이다 — 파이프는 읽는 쪽이 멈추면 쓰는 쪽까지 세운다.
#
# ⚠ **명령 줄에 스크립트 이름이 드러나면 안 된다 — `-EncodedCommand` 로 싣는다.** 몸통의 겹침
#   검사(`Find-EngineHolders`)와 자동 실행의 겹침 가드는 `powershell.exe` 의 명령 줄에서
#   `install.ps1` 을 **글자로** 찾는다. 이 창은 설치가 끝나도 이 창이 닫힐 때까지 사므로,
#   명령 줄에 그 이름이 비치면 다음 설치나 로그온 자동 실행이 **이 창을 설치 중으로 읽고 물러난다.**
#   base64 로 실으면 이름이 명령 줄에 안 서고, 지울 임시 .ps1 도 안 생긴다.
#
# ⚠ **언제 죽나 — 이 창보다 오래 살지 않는다.** 사람이 손으로 닫을 일이 없어야 한다.
#   · 설치 창(`$UiPid`)이 사라지면 곧바로 나간다 — 다 끝나고 [닫기] 든, X 든, 도는 중에 멈춤이든,
#     죽어서든 **모두 이 프로세스가 끝나는 한 사건으로 모인다.** 그래서 이것 하나를 본다.
#   · 몸통(`$EnginePid`)이 끝나면 흘리기를 멈추고 끝났다는 줄을 찍은 뒤, **설치 창이 닫힐 때까지
#     남는다** — 사람이 마지막 줄을 읽을 틈이다. 몇 초 뒤 제풀에 닫는 길은 안 골랐다: 읽는 속도는
#     사람마다 다르고, 설치 창을 닫는 것이 곧 「다 봤다」는 동작이라 신호가 이미 하나 있다.
#     `install.cmd` 에 `pause` 를 안 둔 것과 같은 결이다(위 「콘솔에 남은 글」 머리말).
#   · [다시 설치] 면 옛 창은 비킨다 — 이 창이 끝에 지운 캡처 파일이 **다시 서면** 새 판이 시작된
#     것이고, 그 판은 새 창이 든다. 신호를 따로 안 낸다: 같은 이름을 다시 쓰는 것이 곧 신호다.
#   ⚠ **끝낼 때 죽이지 않고 제풀에 나가게 한다.** Windows 11 은 새 콘솔을 대개 Windows Terminal
#     에 띄우는데, 그쪽은 **0 이 아닌 코드로 끝난 탭을 닫지 않고 남긴다** — `Kill()` 로 끝내면
#     「프로세스가 코드 1 로 끝났다」는 빈 탭을 사람이 손으로 닫아야 한다. 그래서 주 길은 저쪽이
#     스스로 `exit 0` 하는 것이고, 이 창이 닫힐 때 거는 것은 `CloseMainWindow()`(창에 닫으라는 말)
#     뿐이다 — 옛 콘솔 창에서는 바로 닫히고, Terminal 에서는 창이 없다고 거짓을 내며 아무것도
#     안 하므로 위 PID 감시가 맡는다.
#
# ⚠ **글씨 크기는 안 만진다.** 콘솔 글꼴은 `SetCurrentConsoleFontEx` 를 P/Invoke 로 불러야
#   하고 Windows Terminal 은 그것을 무시한다 — 크기는 사람이 고른 터미널 설정을 따른다.
#   창 크기(120×40)도 옛 콘솔에서만 먹고 Terminal 에서는 조용히 안 먹는다. 둘 다 편의지 조건이 아니다.
function Start-ConsoleTail([string]$Out, [string]$Err, [int]$EnginePid, [int]$UiPid = $PID) {
  # 값은 머리 줄에 작은따옴표 글자로 박는다 — 경로에 작은따옴표가 들면 둘로 늘린다.
  $lit  = { param($s) "'" + ([string]$s -replace "'", "''") + "'" }
  $head = '$Out = {0}; $Err = {1}; $UiPid = {2}; $EnginePid = {3}; $Title = {4}' -f `
            (& $lit $Out), (& $lit $Err), $UiPid, $EnginePid, (& $lit "$AppName — 설치 기록")
  $body = @'
$ErrorActionPreference = 'Continue'
# ⚠ 캡처는 UTF-8 이다(몸통이 제 머리에서 세운다). 읽기는 `Open-Tail` 이 UTF-8 로 하고,
#   쓰기 쪽 코드 페이지도 맞춘다 — 못 맞춰도 흘리기는 간다.
$OutputEncoding = [Text.Encoding]::UTF8
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
try { $Host.UI.RawUI.WindowTitle = $Title } catch { }
try {
  $raw = $Host.UI.RawUI
  $w = [Math]::Min(120, $raw.MaxPhysicalWindowSize.Width)
  $h = [Math]::Min(40,  $raw.MaxPhysicalWindowSize.Height)
  # 창 너비는 버퍼 너비를 못 넘는다 — 줄일 때는 창을 먼저, 늘릴 때는 버퍼를 먼저.
  if ($raw.WindowSize.Width -gt $w) {
    $raw.WindowSize = New-Object Management.Automation.Host.Size($w, $raw.WindowSize.Height)
  }
  $raw.BufferSize = New-Object Management.Automation.Host.Size($w, 9999)
  $raw.WindowSize = New-Object Management.Automation.Host.Size($w, $h)
} catch { }

# 손잡이를 쥐어 둔다 — PID 가 딴 프로세스에 다시 쓰여도 끝난 것을 끝난 것으로 본다.
function Get-Watched([int]$Id) {
  try { $p = [Diagnostics.Process]::GetProcessById($Id) } catch { return $null }
  try { $null = $p.Handle } catch { }
  return $p
}
function Test-Gone($P) {
  if (-not $P) { return $true }
  try { return $P.HasExited }
  catch { return -not (Get-Process -Id $P.Id -ErrorAction SilentlyContinue) }
}
function Show-Lines($Reader, [bool]$IsErr) {
  if (-not $Reader) { return 0 }
  $n = 0
  while ($null -ne ($line = $Reader.ReadLine())) {
    $n++
    if ($IsErr)                      { Write-Host $line -ForegroundColor Red }
    elseif ($line -match '^\[\d+/\d+\]') { Write-Host $line -ForegroundColor Cyan }
    elseif ($line -match '^===')     { Write-Host $line -ForegroundColor Yellow }
    else                             { Write-Host $line }
  }
  return $n
}

$ui = Get-Watched $UiPid; $eng = Get-Watched $EnginePid
$rdOut = $null; $rdErr = $null; $shown = 0
while ($true) {
  if (Test-Gone $ui) { exit 0 }
  if (-not $rdOut) { $rdOut = Open-Tail $Out }
  if (-not $rdErr) { $rdErr = Open-Tail $Err }
  $shown += (Show-Lines $rdOut $false) + (Show-Lines $rdErr $true)
  if (Test-Gone $eng) {
    Start-Sleep -Milliseconds 300      # 마지막 쓰기가 파일에 닿을 틈 — 설치 창과 같은 자리
    if (-not $rdOut) { $rdOut = Open-Tail $Out }
    if (-not $rdErr) { $rdErr = Open-Tail $Err }
    $shown += (Show-Lines $rdOut $false) + (Show-Lines $rdErr $true)
    break
  }
  Start-Sleep -Milliseconds 200
}
# 다 읽었으면 곧바로 놓는다 — 설치 창이 곧 지운다.
foreach ($r in @($rdOut, $rdErr)) { if ($r) { try { $r.Dispose() } catch { } } }

# ⚠ 됐나 안 됐나는 여기서 말하지 않는다 — 판정은 설치 창 한 자리가 든다(종료코드를 쥔 쪽).
Write-Host ''
if ($shown -eq 0) {
  Write-Host '기록을 한 줄도 못 읽었습니다 — 설치 창의 기록을 보세요.' -ForegroundColor DarkYellow
}
Write-Host '설치가 끝났습니다 — 결과는 설치 창에 있습니다. 이 창은 설치 창을 닫으면 같이 닫힙니다.' -ForegroundColor Green

$wasGone = $false
while (-not (Test-Gone $ui)) {
  if (-not (Test-Path -LiteralPath $Out)) { $wasGone = $true }
  elseif ($wasGone) { break }          # 캡처가 다시 섰다 — [다시 설치], 새 창이 든다
  Start-Sleep -Milliseconds 250
}
exit 0
'@
  $code = $head + "`n" + "function Open-Tail {`n" + ${function:Open-Tail} + "`n}`n" + $body
  $enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($code))
  $psExe = (Get-Process -Id $PID).Path
  return Start-Process -FilePath $psExe -PassThru -WindowStyle Normal `
           -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', $enc)
}

# ── 창이 닫혀도 사는 기록 ───────────────────────────────────────────────────────
# ⚠ **화면에 뜬 줄은 창과 함께 죽는다.** 몸통이 낸 것을 받아 두던 두 파일까지 닫을 때 같이
#   지워, 설치가 끝난 뒤에는 **어느 걸음에서 무슨 일이 있었나를 물을 물건이 아무 데도 없었다.**
#   그래서 지우기 **전에** 한 파일로 옮긴다 — 화면은 그대로 두고 남는 것만 는다.
# ⚠ **키는 이 파일에 안 들어온다.** 값을 나르는 것은 임시 env 파일 하나뿐이고, 몸통이 값을
#   찍는 자리는 이름만 든다(`Plant-Var` 는 `"  $Name — 심었다"`). 비밀 칸은 화면 갈래에서
#   아예 안 물어지고(`-Yes`), 콘솔 갈래에서도 `-AsSecureString` 이라 되울리지 않는다.
#   **키가 든 임시 env 는 여전히 무조건 지운다** — 옮기는 것은 나가는 것·오류 둘뿐이다.
# ⚠ **못 써도 닫는 길을 막지 않는다.** 기록을 남기려다 창이 안 닫히면 그게 더 나쁘다 —
#   통째로 `try` 안에 두고, 실패하면 빈 자리를 돌려주고 만다.
# ⚠ **자리는 판 폴더 밖이다.** 판마다 새 폴더가 나므로(`…\Claude Code Setup\<판>\`) 그 안에
#   두면 다음 판이 옛 기록을 못 보고, 판 폴더를 지우라는 안내가 기록까지 같이 지운다.
function Save-RunLog {
  # 남길 것이 **실제로 있는** 판만 쓴다 — 이미 지운 뒤 다시 불려도 빈 파일을 안 만든다.
  $any = $false
  foreach ($f in @($script:outFile, $script:errFile)) {
    if ($f -and (Test-Path -LiteralPath $f)) { $any = $true }
  }
  if (-not $any) { return '' }
  try {
    $dir = Join-Path $env:LOCALAPPDATA 'Claude Code Setup\logs'
    if (-not (Test-Path -LiteralPath $dir)) {
      New-Item -ItemType Directory -Path $dir -Force -ErrorAction Stop | Out-Null
    }
    $path = Join-Path $dir ('install-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
    # ⚠ **여는 법은 `Open-Tail` 하나다.** 자식이 방금까지 쥐고 있던 파일이라 공유 열기여야
    #   하는데, 그 조건을 여기 다시 적으면 한쪽만 고쳐진다 — 이미 있는 것을 부른다.
    $body = ''
    if ($script:outFile) {
      $r = Open-Tail $script:outFile
      if ($r) { try { $body = $r.ReadToEnd() } finally { try { $r.Dispose() } catch { } } }
    }
    # ⚠ 둘을 한 파일에 담되 **경계를 글자로 박는다** — 파일이 둘이면 이름도 둘이라 안내도
    #   둘이 되고, 읽는 사람이 둘을 손으로 맞춰야 한다.
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
$timer = New-Object Windows.Forms.Timer
$timer.Interval = 150
$timer.Add_Tick({
  # ⚠ **앞에 세우기는 `TopMost` 를 켰다 끄는 것으로 한다 — `Activate()` 가 아니다.** 콘솔이 뜨며
  #   포그라운드를 가져간 뒤라, `Activate()` 는 포그라운드 잠금에 걸려 작업표시줄만 깜빡이고 안
  #   올라올 수 있다. 맨 위 띠로 옮겼다 되돌리는 것은 그 잠금과 무관하게 z-순서를 바꾸고, 되돌린
  #   뒤에는 **보통 창들 중 맨 위**에 선다 — 콘솔 위, 그러나 맨 위 띠 아래.
  # ⚠ **몸통의 물음창을 가리지 않는다.** `Show-AskDialog` 는 맨 위 띠의 창을 임자로 세우므로 늘
  #   이 창보다 위다 — 확인창이 다른 창 뒤에 숨어 설치가 멈춘 듯 보였던 자리를 다시 안 만든다.
  #   켜 둔 한순간만 그 위로 겹칠 뿐이다. 600ms 마다 한 번, 3초 동안.
  if ($script:raise -gt 0) {
    $script:raise--
    if (($script:raise % 4) -eq 0) { $F.TopMost = $true; $F.TopMost = $false }
  }
  if (-not $script:rdOut) { $script:rdOut = Open-Tail $script:outFile }
  if (-not $script:rdErr) { $script:rdErr = Open-Tail $script:errFile }
  $got = (Pump-Tail $script:rdOut) + (Pump-Tail $script:rdErr)

  # ⚠ **줄이 안 나오는 동안에도 살아 있어야 한다.** winget 이 도는 몇 분은 한 줄도 안 나온다 —
  #   낱줄만 눈금으로 쓰면 그동안 막대가 못 박히고, 사람은 멈춘 줄 안다. 조용하면 천천히
  #   민다. 미는 끝은 여전히 이 칸의 끝 한 칸 앞이라 다음 칸을 침범하지는 않는다.
  if ($got -gt 0) {
    $script:idle = 0
  } else {
    $script:idle++
    # ⚠ 밀고 나서 `idle` 을 0 으로 되돌리지 않는다 — 되돌리면 「얼마나 조용했나」를 못 센다.
    #   12 틱마다 한 칸씩 미는 것은 나머지로 가른다.
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
    foreach ($f in @($script:tmpEnv, $script:outFile, $script:errFile)) {
      if ($f -and (Test-Path -LiteralPath $f)) {
        Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue
      }
    }
    $script:proc = $null
    if ($script:sw) { $script:sw.Stop() }

    # ⚠ **끝났다고 됐다고 하지 않는다.** 몸통이 하나라도 못 세우면 0 이 아닌 값으로 끝나고,
    #   그것을 안 재고 「완료」를 찍으면 안 선 기계가 성공으로 보고된다.
    # ⚠ **「못 읽었다」를 「실패했다」로 뭉치지 않는다.** 빈 괄호는 실패가 아니라 **재는 자가
    #   고장났다는 뜻**인데, 둘이 같은 문장으로 나오면 아무도 못 가른다 — 옛 판이 그래서
    #   멀쩡한 설치를 실패로 보고했고, 그 사실이 한 판 내내 안 보였다.
    if ($null -eq $rc) {
      $lState.Text = '끝났는데 종료코드를 못 읽었습니다 — 위 기록의 마지막 줄로 판단하세요.'
      $lState.ForeColor = [Drawing.Color]::DarkOrange
    } elseif ($rc -eq 0) {
      $bar.Value = 100
      # ⚠ **못 받았으면 아는 척하지 않는다.** 몸통이 그 줄을 못 낸 판(옛 판·중간에 끊긴 판)에서
      #   그럴듯한 문장을 지어 내면, 안 한 일을 했다고 말하게 된다 — 기록을 보라고 한다.
      $lState.Text = if ($script:done) { $script:done }
                     else { '됐습니다 — 아래 기록의 마지막 줄을 보세요.' }
      $lState.ForeColor = [Drawing.Color]::ForestGreen
    } else {
      $lState.Text = "끝내지 못했습니다 (코드 $rc) — 위 기록의 ! 줄을 보세요."
      $lState.ForeColor = [Drawing.Color]::Firebrick
    }
    $bGo.Text = '다시 설치'; $bGo.Enabled = $true
    $gV.Enabled = $true; $gO.Enabled = $true; $gR.Enabled = $true
    }
})

# ⚠ 창을 닫을 때 도는 자식을 두고 가지 않는다 — 두면 임시 파일도 안 지워진다.
$F.Add_FormClosing({
  if ($script:proc -and -not $script:proc.HasExited) {
    $ans = [Windows.Forms.MessageBox]::Show('설치가 도는 중입니다. 멈추고 닫을까요?',
      $AppName, 'YesNo', 'Warning')
    if ($ans -ne 'Yes') { $_.Cancel = $true; return }
    # ⚠ **나무째 끈다.** `$script:proc` 는 몸통이 아니라 그것을 감싼 `cmd.exe` 라, 그것만 죽이면
    #   **몸통 PowerShell 과 그 자식(winget · npm)이 남아 계속 돈다** — 사람은 「멈추고 닫았다」로
    #   알고 창도 사라졌는데 뒤에서 설치가 이어지고, 다음 판은 빗장에 막힌다.
    # ⚠ **`taskkill /T` 를 안 쓴다** — 실행 파일 하나를 더 부르는 길은 정책이 막는 자리가 있다
    #   (실측 2026-09-25: 「Access is denied」로 아예 안 떴다). 자식 목록을 윈도우에 물어 **아래부터**
    #   끈다 — 위를 먼저 끄면 아래가 부모 없는 고아가 되어 목록에서 못 찾는다.
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
  foreach ($f in @($script:tmpEnv, $script:outFile, $script:errFile)) {
    if ($f -and (Test-Path -LiteralPath $f)) {
      Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue
    }
  }
})
# ⚠ **뒤의 기록 창도 같이 닫는다 — 닫힘이 확정된 뒤(`FormClosed`)에만.** `FormClosing` 은 위에서
#   「아니오」로 무를 수 있어, 거기서 닫으면 설치 창은 남고 기록 창만 사라진다. 주 길은 저쪽이
#   이 프로세스가 사라진 것을 보고 제풀에 나가는 것이고, 여기는 옛 콘솔 창에서 그것을 앞당기는
#   덧줄이다 — **`Kill()` 이 아니다**(`Start-ConsoleTail` 머리말: Terminal 이 빈 탭을 남긴다).
$F.Add_FormClosed({
  if ($script:con -and -not $script:con.HasExited) {
    try { [void]$script:con.CloseMainWindow() } catch { }
  }
})
# ── 새 판이 있나 — 창이 뜬 뒤에 배경으로 물어본다 ──────────────────────────────
# ⚠ **앞을 막지 않는다.** 물어보는 데 몇 초가 들 수 있는데(사내 프록시가 막으면 시간이 다
#   갈 때까지), 그동안 창이 안 뜨면 사람은 아무 일도 안 일어난 줄 안다. 그래서 창이 먼저
#   서고 이것은 뒤에서 돈다. 답이 오면 타이머가 화면 실에서 집는다 —
#   **딴 실에서 창을 만지면 그 자리에서 죽는다.**
# ⚠ **「못 물었다」를 「최신이다」로 읽지 않는다.** 막힌 망에서 조용히 최신이라고 하면
#   낡은 판을 든 사람이 낡은 줄 모른 채 간다 — 부재가 통과로 읽히는 그 자리다.
#   그래서 못 물었으면 **아무 말도 안 한다**: 모르는 것은 모르는 것으로 둔다.
# ⚠ **자리를 여기 안 박는다** — 값 파일의 `#update-repo` 가 든다. 박으면 이 파일이 특정
#   저장소의 것이 되어 남에게 그대로 못 준다(`#site-probe`·`#config-repo` 와 같은 결).
$script:upPs = $null
$script:upHandle = $null
$UpdateRepo = Get-Directive 'update-repo'
# 묻고 재는 손은 곁의 조각이 든다 — **자동 실행도 같은 자를 부른다.** 여기 붙박이로 두면
# 그쪽이 베껴야 하고, 그러면 손사본 둘이 되어 한쪽만 고쳐진다.
# ⚠ **없으면 아예 안 묻는다.** 옛 판이 푼 폴더에는 이 파일이 없다 — 그때 부르면 창이
#   그 자리에서 죽는다. 새 판을 못 보는 것과 창이 안 서는 것은 값이 다르다.
$UpdateLib = Join-Path $Here 'update-check.ps1'

if ($UpdateRepo -and $DistVersion -and (Test-Path -LiteralPath $UpdateLib)) {
  try {
    $script:upPs = [powershell]::Create()
    # ⚠ **딴 실이라 이 파일의 함수를 모른다** — 그 실 안에서 조각을 제 손으로 읽는다.
    [void]$script:upPs.AddScript({
      param($lib, $repo, $mine)
      try { . $lib; return Find-NewerRelease -Repo $repo -Mine $mine } catch { return $null }
    })
    [void]$script:upPs.AddArgument($UpdateLib)
    [void]$script:upPs.AddArgument($UpdateRepo)
    [void]$script:upPs.AddArgument($DistVersion)
    $script:upHandle = $script:upPs.BeginInvoke()
  } catch { $script:upPs = $null; $script:upHandle = $null }
}

$script:upTimer = New-Object Windows.Forms.Timer
$script:upTimer.Interval = 400
$script:upTimer.Add_Tick({
  if (-not $script:upHandle -or -not $script:upHandle.IsCompleted) { return }
  $script:upTimer.Stop()
  $found = $null
  try { $found = @($script:upPs.EndInvoke($script:upHandle))[0] } catch { }
  try { $script:upPs.Dispose() } catch { }
  $script:upPs = $null; $script:upHandle = $null
  if (-not $found) { return }

  $ans = [Windows.Forms.MessageBox]::Show(
    "새 판 $($found.Ver) 이 나와 있습니다. 지금 것은 $DistVersion 입니다.`n`n" +
    "새 판으로 설치할까요?`n받는 동안 이 창은 잠깐 멈춥니다 — 2MB 남짓입니다.",
    $AppName, 'YesNo', 'Question')
  if ($ans -ne 'Yes') { return }

  # 받아서 재는 손은 곁의 조각이 든다(`update-check.ps1`) — **왜 해시가 이 자리를 드는지**도
  # 거기 곁말이 든다. 여기가 드는 것은 **진 까닭마다 사람에게 뭐라 할까** 하나다.
  $F.Cursor = [Windows.Forms.Cursors]::WaitCursor
  $F.Enabled = $false
  try { . $UpdateLib } catch { }
  $v = $null
  try { $v = Get-VerifiedSetup -Found $found }
  catch { $v = @{ Ok = $false; Status = 'download-failed'; Detail = $_.Exception.Message } }
  $F.Enabled = $true
  $F.Cursor = [Windows.Forms.Cursors]::Default

  if (-not $v.Ok) {
    # ⚠ **「못 쉄다」와 「다르다」를 한 말로 묶지 않는다.** 앞은 옛 릴리스라 대조할 자가
    #   없는 것이고 뒤는 받은 것이 어긋난 것이다 — 사람이 할 일이 서로 다르다.
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
    [void][Windows.Forms.MessageBox]::Show($say, $AppName, 'OK', $ico)
    return
  }

  Start-Process -FilePath $v.Path | Out-Null
  # ⚠ **이 창을 닫는다.** 새 판이 제 화면을 띄우므로 둘이 같이 서 있으면 어느 것에 값을
  #   넣었는지가 흐려진다.
  $F.Close()
})

$bClose.Add_Click({ $F.Close() })

$F.Add_Shown({
  if ($script:upHandle) { $script:upTimer.Start() }
  # ⚠ **빈 칸이 있으면 거기로 간다 — 주소 칸이 먼저다.** 키가 채워져 왔다고 곧장 버튼으로
  #   보내면, 아직 비어 있는 주소 칸을 건너뛴 채 손이 [설치 시작] 위에 놓인다.
  if ($tUrl -and $tUrl.Enabled -and -not $tUrl.Text.Trim())      { $tUrl.Focus() | Out-Null }
  elseif ($tKey -and $tKey.Enabled -and -not $tKey.Text.Trim())  { $tKey.Focus() | Out-Null }
  else { $bGo.Focus() | Out-Null }
})
[void]$F.ShowDialog()
