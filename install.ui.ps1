# 설치 화면 — 값을 받고, 옵션을 고르고, 진행을 보여준다.
#
#   진입점은 `install.cmd` 다. 화면이 못 서면(윈도우가 아니거나 데스크탑이 없으면) 콘솔
#   갈래로 물러난다.
#
# ⚠ **여기에 설치 로직이 없다.** 무엇을 어떻게 깔지는 `install.ps1` 한 자리가 든다 — 이
#   파일은 값을 받아 그것에 넘기고, 그것이 찍는 줄을 화면에 옮긴다. 로직을 여기 옮기면
#   화면 갈래와 콘솔 갈래가 서로 다른 코드를 타고, 그러면 한쪽만 고쳐진다.
#
# ⚠ **진행 막대의 신호는 몸통이 이미 찍는 `[n/7]` 이다.** 진행률을 알리는 통로를 따로 내지
#   않는다 — 통로가 둘이면 칸이 늘 때 한쪽만 고쳐지고, 그 어긋남은 「막대가 안 찬다」는
#   조용한 꼴로만 보인다. 몸통이 사람에게 하는 말을 그대로 읽는다.

param([switch]$NoDevTools, [switch]$WithPersonalConfig, [switch]$NoUpgrade)

$ErrorActionPreference = 'Stop'
# ⚠ **던지게 두지 않는다.** 출력이 파일로 돌려진 채로 뜨면 이 줄이 걸릴 수 있고, 위 `Stop`
#   이 그 자리에서 끝낸다 — **한 줄도 안 찍힌 채 죽는다.** 인코딩은 편의지 조건이 아니다.
$OutputEncoding = [System.Text.Encoding]::UTF8
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$Here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Engine = Join-Path $Here 'install.ps1'

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

# ── 화면 ────────────────────────────────────────────────────────────────────────
$F = New-Object Windows.Forms.Form
$F.Text = 'Claude Code 설치'
$F.Size = New-Object Drawing.Size(640, 700)
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

# ⚠ **첫 줄은 자리를 안 뒤에 채운다.** 사내면 확장·CLI 가 셋(Claude · Codex · Gemini)이고 사외면 Claude
#   하나라, 자리를 모른 채 적으면 어느 한쪽에 거짓이 된다. 무엇이 더 서나는 값 파일의 틀 지시가 든다.
$lTop = New-Label '' 18 14 560 $true
New-Label '이미 깔린 것은 건너뜁니다. 여러 번 눌러도 안전합니다.' 18 34 560 $false | Out-Null

# ── 값 ──────────────────────────────────────────────────────────────────────────
# ⚠ **주소는 사람이 넣을 것이 아니다.** 회사 안에서 모두 같은 값이라, 입력칸으로 두면
#   저마다 다르게 칠 자리를 열어 두는 꼴이다 — 한 글자만 달라도 안 닿는데 화면은 멀쩡해
#   보인다. 값이 같이 왔으면 **보여만 주고**, 안 왔을 때만 입력칸으로 뜬다.
#   바꿔야 하면 `install.env` 를 고친다 — 값의 진본은 거기지 이 화면이 아니다.
$urlPreset = [string]$Preset['ANTHROPIC_BASE_URL']

function Get-Directive([string]$Key) {
  if (-not (Test-Path -LiteralPath $EnvPath)) { return $null }
  foreach ($line in Get-Content -LiteralPath $EnvPath -Encoding UTF8) {
    if ($line -match "^\s*#\s*$([regex]::Escape($Key))\s*=\s*(.+?)\s*$") { return $Matches[1] }
  }
  return $null
}

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
$lTop.Text = if ($probe -and -not $offsite -and $more.Count) {
               "VS Code 에 Claude · $($more -join ' · ') 확장과 CLI 를 세웁니다." }
             else { 'VS Code 에 Claude Code 확장과 CLI 를 세웁니다.' }
$gV = New-Object Windows.Forms.GroupBox
$noAsk = $offsite
$gV.Text = if ($noAsk) { '키와 주소' } elseif ($urlPreset) { 'API 키' } else { '게이트웨이 (사내만)' }
$gV.Location = New-Object Drawing.Point(16, 62)
$gV.Size = New-Object Drawing.Size(592, 118)
$F.Controls.Add($gV)

$lUrl = New-Object Windows.Forms.Label
$lUrl.Text = '게이트웨이'; $lUrl.Location = New-Object Drawing.Point(14, 28)
$lUrl.Size = New-Object Drawing.Size(110, 20); $gV.Controls.Add($lUrl)

if ($noAsk) {
  $vUrl = New-Object Windows.Forms.Label
  $vUrl.Text = "사외입니다 ($probe 안 닿음) — 게이트웨이를 안 씁니다"
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
if (-not $noAsk) {
  $lKey = New-Object Windows.Forms.Label
  $lKey.Text = 'API 키'; $lKey.Location = New-Object Drawing.Point(14, 60)
  $lKey.Size = New-Object Drawing.Size(110, 20); $gV.Controls.Add($lKey)
  $tKey = New-Object Windows.Forms.TextBox
  $tKey.Location = New-Object Drawing.Point(128, 57)
  $tKey.Size = New-Object Drawing.Size(444, 24)
  $tKey.UseSystemPasswordChar = $true
  $tKey.Text = [string]$Preset['ANTHROPIC_AUTH_TOKEN']
  $gV.Controls.Add($tKey)
}

$lHint = New-Object Windows.Forms.Label
$lHint.Location = New-Object Drawing.Point(128, 86)
$lHint.Size = New-Object Drawing.Size(444, 20)
$lHint.ForeColor = [Drawing.Color]::DimGray
# ⚠ **사외에서는 넣을 것이 없다.** 게이트웨이를 안 타고 구독 로그인으로 서기 때문이다 —
#   그런데 옛 판은 둘을 필수로 물어, 안 쓰는 자리에서도 넣으라 하고 안 넣으면 막았다.
$lHint.Text = if ($offsite) { '구독 로그인으로 섭니다 — 설치 뒤 claude auth login.' }
              elseif ($urlPreset) { '주소는 채워져 왔습니다 — API 키만 넣으면 됩니다.' }
              else { '사내면 주소와 키를 넣습니다. 사외면 둘 다 비워 두세요 — 구독 로그인으로 섭니다.' }
$gV.Controls.Add($lHint)

# 옵션
$gO = New-Object Windows.Forms.GroupBox
$gO.Text = '옵션'; $gO.Location = New-Object Drawing.Point(16, 190)
$gO.Size = New-Object Drawing.Size(592, 116)
$F.Controls.Add($gO)

$cDev = New-Object Windows.Forms.CheckBox
$cDev.Text = '코드를 짤 사람용 도구도 깝니다  (Git · Python · GitHub CLI)'
$cDev.Location = New-Object Drawing.Point(16, 22)
$cDev.Size = New-Object Drawing.Size(560, 22)
$cDev.Checked = -not $NoDevTools
$gO.Controls.Add($cDev)
# ⚠ GitHub CLI 는 깔려도 로그인 전에는 안 돈다 — 처음 쓰는 사람은 여기서 그것을 알 데가 없었다.
#   설정 저장소를 쓰는 사람은 훅이 토큰을 심어 로그인이 필요 없지만, 그것은 저장소 쪽 사정이다.
$lDev = New-Object Windows.Forms.Label
$lDev.Text = '설정 저장소를 쓰려면 Git 이 필요합니다. GitHub CLI 는 깔린 뒤 gh auth login 을 한 번 해야 씁니다.'
$lDev.Location = New-Object Drawing.Point(34, 44)
$lDev.Size = New-Object Drawing.Size(542, 16)
$lDev.ForeColor = [Drawing.Color]::DimGray
$gO.Controls.Add($lDev)

$cCfg = New-Object Windows.Forms.CheckBox
$cCfg.Text = '같이 온 규범 · 룰 · 스킬도 깝니다'
$cCfg.Location = New-Object Drawing.Point(16, 64)
$cCfg.Size = New-Object Drawing.Size(560, 22)
$cCfg.Checked = [bool]$WithPersonalConfig
$gO.Controls.Add($cCfg)

# ⚠ **이미 선 기계에서는 이게 이 설치의 일 전부다.** 집·회사 PC 는 프로필이 안 날아가서
#   프로그램이 이미 다 있는데, 「있으면 건너뛴다」만 두면 판이 영영 안 올라간다 —
#   낡은 줄도 모른 채 몇 달을 돈다. 비영속 VDI 는 어차피 맨바닥이라 이 칸이 안 걸린다.
$cUpg = New-Object Windows.Forms.CheckBox
$cUpg.Text = '이미 깔린 것도 최신으로 올립니다'
$cUpg.Location = New-Object Drawing.Point(16, 88)
$cUpg.Size = New-Object Drawing.Size(560, 22)
$cUpg.Checked = -not $NoUpgrade
$gO.Controls.Add($cUpg)

# ── 개인 값 저장소 (선택) ───────────────────────────────────────────────────────
# ⚠ **넣어도 위 키 칸은 그대로 산다.** 설치는 자리만 보고 전부 세우고, 저장소는 **그 뒤에** 받아
#   뿌리의 SessionStart 훅을 `--install` 로 부른다 — 그쪽이 드는 것은 사람에게 딸린 것(git 신원 ·
#   형제 저장소 · 개인 키 · 배포)뿐이다. 옛 판은 이 칸이 차면 키 칸을 껐는데, 저장소에 부트스트랩이
#   없는 사람은 키가 어디에도 안 심겼다.
# ⚠ **여러 개를 빈칸으로 가른다.** 옛 판은 하나만 받았고 까닭이 「나머지는 그 저장소의
#   훅이 데려온다」였다 — 그런데 그건 **만든 사람의 훅 사정**이지 받는 사람의
#   사정이 아니다. 남의 저장소에 그 목록이 없으면 여기 적을 수밖에 없다.
#   ⚠ 여럿을 든 사람이 **제 훅 선언에 목록을 들었으면** 여기는 그 하나만 적는 것이 맞다 —
#     두 자리에 적으면 저장소가 늘 때 한쪽이 낡는다. 어느 쪽이 맞나는 그 사람이 안다.
# ⚠ **배포본에는 이 값이 안 실려 온다.** 남에게 갈 파일에 내 저장소 주소를 박지 않기 때문이다.
#   그러니 이 칸이 비어 있는 것이 받는 사람에게는 정상이다.
$gR = New-Object Windows.Forms.GroupBox
$gR.Text = '설정 저장소 (선택) — 여러 개는 빈칸으로 가릅니다'
$gR.Location = New-Object Drawing.Point(16, 312)
$gR.Size = New-Object Drawing.Size(592, 64)
$F.Controls.Add($gR)

$tRepo = New-Object Windows.Forms.TextBox
$tRepo.Location = New-Object Drawing.Point(14, 24)
$tRepo.Size = New-Object Drawing.Size(558, 24)
$tRepo.Text = [string](Get-Directive 'config-repo')
$gR.Controls.Add($tRepo)

$lRepo = New-Object Windows.Forms.Label
$lRepo.Location = New-Object Drawing.Point(16, 50)
$lRepo.Size = New-Object Drawing.Size(556, 18)
$lRepo.ForeColor = [Drawing.Color]::DimGray
$lRepo.Text = '비우면 이 폴더 값으로만 섭니다. 여러 개를 넣으면 다 받습니다.'
$gR.Controls.Add($lRepo)

# 넣어도 위 키 칸은 그대로 산다 — 무엇이 더 서는지만 화면이 보여준다
$syncRepo = {
  $on = [bool]$tRepo.Text.Trim()
  $lRepo.Text = if ($on) { '다 세운 뒤 받아서, 뿌리의 SessionStart 훅을 --install 로 부릅니다.' }
                else { '비우면 이 폴더 값으로만 섭니다. 여러 개를 넣으면 다 받습니다.' }
}
$tRepo.Add_TextChanged($syncRepo)

# ── 후버로 긴 설명을 내린다 ──────────────────────────────────────────────────────
# ⚠ **줄 하나에 다 적을 수가 없다.** 이 칸은 규약(파일 이름 하나)과 갈래 둘과 자리
#   (`~/repos`)를 같이 말해야 하는데, 창의 안내 줄은 한 줄이고 늘리면 아래 것들이 밀린다
#   (배치가 절대좌표다). 그래서 **머무르면 펴지는 자리**에 둔다 — 안 읽어도 설치는 서고,
#   읽고 싶은 사람만 편다.
$tip = New-Object Windows.Forms.ToolTip
$tip.AutoPopDelay = 30000      # 긴 글이라 오래 띄운다
$tip.InitialDelay = 400
$tip.ReshowDelay  = 200
$tip.ShowAlways   = $true
$tipText = @'
제 저장소를 이어 붙이는 자리입니다. 비워 두는 것이 기본이고 맞는 답입니다 —
프로그램·확장·키·사내 문서·씨앗은 이 칸과 무관하게 다 깔립니다.

넣으면 ~/repos/<저장소 이름> 으로 받습니다. 여러 개는 빈칸으로 가릅니다.

받은 뒤 갈래가 둘이고 둘 다 정당합니다. 가르는 자는 파일 이름 하나입니다 —
받아온 저장소 뿌리의 .claude/hooks/session-start.sh (Claude Code 의 SessionStart 훅):

  · 든 저장소가 있으면  --install 로 부릅니다. 그 뒤는 그 저장소가 듭니다
                        (git 신원 · 형제 저장소 · 개인 키 · 규범·룰·메모리 배포)
  · 어디에도 없으면      받아 둔 것으로 끝냅니다. 저장소만 들고 다니려면 그것으로 됩니다

키·주소·프록시·확장·CLI 는 이 칸과 무관하게 위에서 다 섭니다.

여럿이 그 파일을 들고 있으면 첫 것만 부르고 나머지는 이름을 찍습니다.

자동화까지 원하면 ~/.claude/seeds/config-repo/ 에 깔리는 골든을 복사해
제 저장소 뿌리에 그 이름으로 두십시오.
'@
$tip.SetToolTip($tRepo, $tipText)
$tip.SetToolTip($lRepo, $tipText)

# 진행
$bar = New-Object Windows.Forms.ProgressBar
$bar.Location = New-Object Drawing.Point(16, 388)
$bar.Size = New-Object Drawing.Size(592, 20)
$bar.Minimum = 0; $bar.Maximum = 100
$F.Controls.Add($bar)

$lState = New-Label '' 18 412 500 $false

# 기록 — 몸통이 찍는 줄을 그대로 옮긴다
$log = New-Object Windows.Forms.TextBox
$log.Location = New-Object Drawing.Point(16, 436)
$log.Size = New-Object Drawing.Size(592, 170)
$log.Multiline = $true; $log.ReadOnly = $true
$log.ScrollBars = 'Vertical'; $log.WordWrap = $false
$log.BackColor = [Drawing.Color]::FromArgb(30, 30, 30)
$log.ForeColor = [Drawing.Color]::Gainsboro
$log.Font = New-Object Drawing.Font('Consolas', 9)
$F.Controls.Add($log)

$bGo = New-Object Windows.Forms.Button
$bGo.Text = '설치 시작'; $bGo.Location = New-Object Drawing.Point(416, 618)
$bGo.Size = New-Object Drawing.Size(100, 30)
$F.Controls.Add($bGo); $F.AcceptButton = $bGo

$bClose = New-Object Windows.Forms.Button
$bClose.Text = '닫기'; $bClose.Location = New-Object Drawing.Point(524, 618)
$bClose.Size = New-Object Drawing.Size(84, 30)
$F.Controls.Add($bClose)

# ── 돌리는 자 ───────────────────────────────────────────────────────────────────
# ⚠ **`Register-ObjectEvent -Action` 을 안 쓴다 — 그것이 여태 한 줄도 안 나오던 까닭이다.**
#   그 블록은 파워셸이 **한가할 때만** 돈다. 그런데 창이 떠 있는 동안 런스페이스는 계속
#   `ShowDialog()` 를 실행 중이라, 자식이 뱉은 줄이 큐에만 쌓이고 **창이 닫힐 때까지 핸들러가
#   한 번도 안 불린다.** 그래서 기록 칸이 비고, `[n/7]` 을 못 봐 막대 구간이 0/0 이고,
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
      'Claude Code 설치', 'OK', 'Warning') | Out-Null
    return
  }
  $bGo.Enabled = $false; $gV.Enabled = $false; $gO.Enabled = $false; $gR.Enabled = $false
  $log.Clear(); $bar.Value = 0; $lState.Text = '시작합니다…'
  # ⚠ **준비 구간을 미리 연다.** 첫 `[n/7]` 이 나오기 전에도 할 일이 있다 — winget 이 없으면
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
  if (-not $noAsk) {
    foreach ($k in $Preset.Keys) {
      if ($k -in @('ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN')) { continue }
      if ($Preset[$k]) { $lines.Add("$k=$($Preset[$k])") }
    }
  }
  # 빈 값은 안 적는다 — 적으면 몸통이 「게이트웨이를 쓴다」로 읽는다
  if ($url) { $lines.Add("ANTHROPIC_BASE_URL=$url") }
  if ($key) { $lines.Add("ANTHROPIC_AUTH_TOKEN=$key") }
  # ⚠ 지시(`#…`)를 그대로 옮긴다. 안 옮기면 몸통이 settings.json 에 밀라는 말도, 자리를
  #   가르라는 말도 못 듣는다 — 화면을 거쳤다는 이유로 갈래가 달라지면 안 된다.
  # ⚠ **`config-repo` 만은 화면이 든다.** 파일에 있던 것을 흘리면, 사람이 칸을 비워도 옛
  #   주소로 clone 이 돈다 — 지운 것이 안 지워지는 자리다.
  if (Test-Path -LiteralPath $EnvPath) {
    foreach ($line in Get-Content -LiteralPath $EnvPath -Encoding UTF8) {
      if ($line -match '^\s*#\s*config-repo\s*=') { continue }
      if ($line -match '^\s*#\s*[A-Za-z][A-Za-z0-9-]*\s*=\s*.+$') { $lines.Add($line.Trim()) }
    }
  }
  $repo = $tRepo.Text.Trim()
  if ($repo) { $lines.Add("#config-repo = $repo") }
  Set-Content -LiteralPath $script:tmpEnv -Value $lines -Encoding UTF8

  $argv = @('-NoProfile','-ExecutionPolicy','Bypass','-File', $Engine, '-Yes',
            '-EnvFile', $script:tmpEnv)
  if (-not $cDev.Checked) { $argv += '-NoDevTools' }
  if ($cCfg.Checked)      { $argv += '-WithPersonalConfig' }
  if (-not $cUpg.Checked) { $argv += '-NoUpgrade' }

  # ⚠ **경로만 따옴표로 싼다.** 스위치까지 싸면 파워셸이 제 인자를 못 읽는다 —
  #   `"-NoProfile"` 은 스위치가 아니라 값으로 들어간다.
  # ⚠ **빈칸만 보고 싸면 모자란다.** 이 줄은 아래에서 `cmd` 에 넘어가므로, `&`·`^`·괄호가
  #   든 경로는 안 싸면 cmd 가 거기서 명령을 자른다 — 빈칸이 없어도 그렇다.
  $argLine = ($argv | ForEach-Object {
      if ($_ -match '[\s&^()<>|,;=]') { '"' + $_ + '"' } else { $_ }
    }) -join ' '

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
  $timer.Start()
})

# ── 한 줄을 화면에 반영하는 자 ─────────────────────────────────────────────────
# 진행률의 신호는 몸통이 사람에게 하는 말 그대로다 — 통로를 따로 안 낸다.
# ⚠ **칸 안에서도 올라가야 한다.** 옛 판은 `[n/7]` 을 볼 때 `(n-1)/7` 로 놓아 첫 칸이 곧
#   0% 였다 — 그런데 **첫 칸이 제일 오래 걸린다**. 칸의 시작과 끝을 잡아 두고 그 안에서
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
function Open-Tail([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  try {
    $fs = New-Object IO.FileStream($Path, [IO.FileMode]::Open,
            [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
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

# ── 파일을 따라 읽는 타이머 — 화면 실에서만 화면을 만진다 ──────────────────────
$timer = New-Object Windows.Forms.Timer
$timer.Interval = 150
$timer.Add_Tick({
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
    & $syncRepo
  }
})

# ⚠ 창을 닫을 때 도는 자식을 두고 가지 않는다 — 두면 임시 파일도 안 지워진다.
$F.Add_FormClosing({
  if ($script:proc -and -not $script:proc.HasExited) {
    $ans = [Windows.Forms.MessageBox]::Show('설치가 도는 중입니다. 멈추고 닫을까요?',
      'Claude Code 설치', 'YesNo', 'Warning')
    if ($ans -ne 'Yes') { $_.Cancel = $true; return }
    try { $script:proc.Kill() } catch { }
  }
  foreach ($f in @($script:tmpEnv, $script:outFile, $script:errFile)) {
    if ($f -and (Test-Path -LiteralPath $f)) {
      Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue
    }
  }
})
$bClose.Add_Click({ $F.Close() })

$F.Add_Shown({
  & $syncRepo
  if ($tKey -and $tKey.Enabled -and -not $tRepo.Text.Trim()) { $tKey.Focus() | Out-Null }
  else { $bGo.Focus() | Out-Null }
})
[void]$F.ShowDialog()
