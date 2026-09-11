# 맨바닥 윈도우 PC 에서 **VS Code 의 Claude Code 확장이 돌게** 한다. 진입점은 `install.cmd`.
#
#   .\install.ps1                    깔고, 없는 값은 묻는다
#   .\install.ps1 -NoDevTools        git·python·gh 를 건너뛴다 (확장만 쓸 사람)
#   .\install.ps1 -WithPersonalConfig  개인 규범·룰·스킬까지 (값 파일이 저장소를 가리킬 때)
#   .\install.ps1 -NoLaunch          끝에 창을 안 띄운다 (기본은 띄운다)
#
# ⚠ **메모리는 여기가 아니다.** 세션 기록은 저장소마다 슬러그 폴더에 깔리는 것이라
#   저장소가 먼저 있어야 서고, 그 자는 `deploy.ps1` 이다. 이 파일은 기계를 세우는 층이고
#   저장소는 안 다룬다 — 층을 섞으면 저장소 없는 PC 에서 갈 곳 없는 사본이 생긴다.
#   .\install.ps1 -Yes               안 묻는다 — 값 파일이 다 들고 있을 때만 (자동화용)
#
# ⚠ **이 파일에는 값이 없다.** 드는 것은 **이름과 설명**뿐이고 값은 둘 중 하나에서 온다:
#   1) 옆에 둔 `install.env`  (`이름=값` 한 줄씩 · `secrets.env` 와 같은 꼴)
#   2) 사람이 그 자리에서 입력
#
#   그 파일이 `#config-repo` 를 들면 **키를 안 묻고** 그 저장소를 받아 부트스트랩으로
#   넘긴다 — 값의 진본이 저쪽이라 여기서 또 물으면 같은 키가 두 자리에 산다.
#   **주소도 여기 없다.** 그래서 이 파일 하나는 어느 갈래에서도 익명으로 남는다.
#
#   그래서 **한 몸통이 두 갈래를 다 든다.** 값 파일을 들고 다니는 사람은 아무것도 안 묻고
#   지나가고, 파일 없이 이것만 받은 사람은 묻는 것에 답하면 선다. 갈래마다 스크립트를
#   따로 두면 목록이 갈려 한쪽만 낡는다 — 이 저장소가 도구 선언·자리 파일에서 이미 쓰는
#   축이다(**몸통은 이름을 모른다**).
#
# ⚠ **개인 정보를 이 파일에 넣지 않는다.** 계정·저장소 이름·키·사용자명·게이트웨이 주소
#   어느 것도. 그래야 이 파일만 떼어 남에게 줄 수 있고, 그것이 이 파일이 있는 까닭이다.

# ⚠ `-EnvFile` 은 화면 껍데기(`install.ui.ps1`)가 쓴다 — 사람이 화면에 넣은 값을 임시 파일로
#   건네고 이 몸통은 평소처럼 읽는다. 값을 받는 길을 하나로 두려는 것이다: 껍데기용 통로를
#   따로 내면 화면 갈래와 콘솔 갈래가 서로 다른 코드를 타고, 한쪽만 고쳐지는 자리가 난다.
# ⚠ **`install.cmd` 는 영어만 든다.** cmd.exe 는 배치 파일을 콘솔 OEM 코드페이지(한국은
#   cp949)로 읽는데 파일은 UTF-8 이라, 한글이 어긋나 읽히면 `rem` 이 `rem` 으로 안 잡히고
#   깨진 글자가 **명령으로 실행된다**(실측 2026-09-09 · 사내 VDI: 주석 줄 전부와 powershell
#   줄이 갈라졌다). 그래서 거기 있던 설명이 이 파일로 왔다 — 여기는 BOM 이 붙은 UTF-8 이라
#   PowerShell 이 제대로 읽는다. 그 파일에 한글을 도로 넣지 않는다.

# ⚠ `-NoUpgrade` — **기본은 올린다.** 자리가 넷인데 둘(비영속 VDI)은 매번 맨바닥이고 둘(집·
#   회사 PC)은 이미 서 있다. 「있으면 건너뛴다」만 두면 뒤엣것은 **영영 안 올라간다** — 판이
#   낡은 줄도 모른 채 몇 달을 돈다. 그렇다고 자리를 물으면 이 파일이 자리를 알아야 하는데
#   그건 이 파일의 몫이 아니다. **있으면 올리고 없으면 깐다** — 프로브가 이미 아는 것으로
#   넷 다 맞춘다.
# ⚠ `-NoLaunch` — **기본은 띄운다.** 설치가 끝나고 사람에게 남는 일은 창 하나 여는 것뿐인데,
#   그 한 손이 안 가면 방금 심은 값은 **아무 데도 안 걸린 채**로 남는다 — 깔기는 다 됐는데 쓸
#   수는 없는 자리다. 그러니 마지막 손은 설치가 든다.
#   끄는 칸을 그래도 두는 까닭은 **화면 없이 부르는 갈래**가 있어서다(머리글의 쓰임 목록).
#   ⚠ **자동화로 돌릴 때는 이 칸을 꼭 준다.** 이미 떠 있는 것이 있으면 여는 자리가 **끌지
#   묻는 창**을 띄우는데, 아무도 안 보는 자리에서 그것은 영영 안 눌리는 창이다 — 설치가
#   거기서 선 채로 끝나지 않는다.
param([switch]$Yes, [switch]$NoDevTools, [switch]$WithPersonalConfig, [switch]$NoUpgrade,
      [switch]$NoLaunch, [string]$EnvFile)

$ErrorActionPreference = 'Stop'

# ⚠ **네이티브 명령의 stderr 를 성공 스트림에 합치지 않는다 (`2>&1`).** 합치면 파워셸이 그 줄을
#   오류 레코드로 감싸고, 위 `Stop` 이 **그 자리에서 스크립트를 끝낸다.** 경고 한 줄이 설치를
#   통째로 죽인다 — 실측 2026-09-09 · 사외 VDI: `code --install-extension` 이 뱉은 Node
#   deprecation 경고에 확장 칸에서 죽었다. **경고는 실패가 아니다.**
#   ⚠ 합치면 판정도 망가진다: `Get-Ver` 가 판 대신 그 경고 줄을 읽어 갱신 여부를 헛짚는다.
#
# ⚠ **그렇다고 버리지도 않는다.** 판정만 재는 자리(`Test-Runs`·`Get-Ver`)는 `2>$null` 로 버려도
#   되지만, **설치하는 자리는 실패했을 때 까닭이 유일한 단서다.** 처음엔 다 버렸다가 확장이
#   「! 설치 실패」 한 줄만 내고 왜인지 아무도 모르는 자리를 밟았다(실측 2026-09-09 · 사외 VDI).
#   그래서 파일로 **잡아 두고 실패할 때만 편다** — winget 칸이 이미 쓰던 꼴이다.

# 콘솔 UTF-8 강제. PowerShell 5.1 기본은 시스템 코드페이지(한국은 cp949)라 한글이 깨진다.
# ⚠ **던지게 두지 않는다.** 출력이 파일로 돌려진 채로 뜨면 이 줄이 걸릴 수 있고, 위 `Stop`
#   이 그 자리에서 끝낸다 — **한 줄도 안 찍힌 채 죽는다.** 인코딩은 편의지 조건이 아니다.
$OutputEncoding = [System.Text.Encoding]::UTF8
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$Here    = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $EnvFile) { $EnvFile = Join-Path $Here 'install.env' }
$Fails   = New-Object System.Collections.Generic.List[string]
$Planted = @{}

# ── 무엇을 깔까 — **목록이 진본이다.** 늘리려면 여기 한 줄을 더한다 ────────────────
#    core = 확장이 돌기까지 없으면 안 되는 것. dev = 코드를 짤 사람에게만.
#    ⚠ Claude Code CLI 는 이 표에 없다 — winget 이 아니라 npm 이 깔아서다(아래 4칸).
$Apps = @(
  @{ Name='VS Code';    Id='Microsoft.VisualStudioCode'; Cmd='code';   Arg='--version'; Need='core' }
  @{ Name='Node.js';    Id='OpenJS.NodeJS.LTS';          Cmd='node';   Arg='--version'; Need='core' }
  @{ Name='Git';        Id='Git.Git';                    Cmd='git';    Arg='--version'; Need='dev'  }
  @{ Name='Python';     Id='Python.Python.3.14';         Cmd='python'; Arg='--version'; Need='dev'  }
  @{ Name='GitHub CLI'; Id='GitHub.cli';                 Cmd='gh';     Arg='--version'; Need='dev'  }
)

# ── Node 가 말을 거는 자리 — **목록이 진본이다** ─────────────────────────────────
# 신뢰를 이을 근거를 여기서 잰다(아래 `Wire-NodeTrust`). Node 를 태우는 곳이 늘면 한 줄 더한다.
# ⚠ **이 설치가 실제로 여는 곳만 든다.** 신뢰 저장소를 통째로 훑으면 이 PC 가 믿는 CA 를 다
#   담게 되는데, 그건 신뢰를 잇는 것이 아니라 **옮겨 적는 것**이다 — 사본은 반드시 낡는다.
$TlsHosts = @(
  'marketplace.visualstudio.com'   # 확장을 받는 곳
  'update.code.visualstudio.com'   # VS Code 가 판을 묻는 곳
  'registry.npmjs.org'             # Claude Code CLI 를 받는 곳
)

# ── 무엇을 **묻고 잴까** — 이름과 설명만 든다. 값은 없다 ────────────────────────
# ⚠ **심는 목록이 아니다.** 값 파일에 있는 이름은 여기 없어도 다 심는다(아래 5칸) — 회사가
#   공통 설정을 하나 더 실어 보내도 이 표를 안 고쳐도 된다. 여기 드는 것은 **없을 때 물을
#   것**과 **끝에 재서 [O]/[X] 로 찍을 것**이다. 둘을 섞으면 표가 값 목록을 뒤쫓게 된다.
#    ⚠ 게이트웨이는 `ANTHROPIC_API_KEY`(x-api-key)와 `ANTHROPIC_AUTH_TOKEN`(Bearer)을
#      둘 다 받는다. CLI 는 AUTH_TOKEN 으로도 서므로 이름을 하나로 둔다 — 둘을 다 물으면
#      받는 사람이 어느 것이 제 키인지 판단해야 한다.
# ⚠ **`Gateway` 는 「무조건 필요」가 아니라 「게이트웨이를 쓸 때 필요」다.** 필요한지는 **자리에
#   달렸는데 이 파일은 자리를 모른다** — 사내는 게이트웨이로 서고 사외는 구독 로그인으로 선다.
#   자리를 가르는 자는 `bootstrap-vdi.sh` 이고 그것은 이 설치 뒤에 온다. 그래서 여기서는
#   **주소가 있으면 쓰는 것, 없으면 안 쓰는 것**으로 판정한다 — 자리 판별을 여기 옮겨 적으면
#   같은 규칙이 두 자리에 살고 한쪽만 낡는다.
# ── 데스크탑 앱 — **이름은 여기 한 자리다.** 아래 2′ 칸이 깔 때도, 마지막 「연다」 칸이
#    띄울 것을 찾을 때도 이 값에서 판다. 옛 판은 세 자리에 박혀 있었다.
# ⚠ **띄울 이름은 여기서 파생한다** — winget 의 id 는 `<만든 이>.<앱>` 꼴이라 뒷칸이 곧
#   시작 메뉴에 뜨는 이름이다. 둘을 따로 적으면 한쪽만 낡는다.
$DesktopApp = 'Anthropic.Claude'

$Vars = @(
  @{ Name='ANTHROPIC_BASE_URL';   Desc='게이트웨이 주소 — 끝에 /v1 을 붙이지 않는다 (CLI 가 붙인다)'; Gateway=$true }
  @{ Name='ANTHROPIC_AUTH_TOKEN'; Desc='게이트웨이 API 키';                                          Gateway=$true; Secret=$true }
  @{ Name='ANTHROPIC_MODEL';      Desc='기본 모델 이름 (비우면 CLI 기본값으로 둔다)';                Gateway=$false }
)

# ── 클라이언트 기능 스위치 — **씨앗이 아니라 늘 맞춘다** ────────────────────────
# ⚠ **씨앗은 「settings.json 이 없을 때」만 깔린다.** 그래서 한 번이라도 돌린 기계는 그 뒤에
#   늘어난 스위치를 **영영 못 받는다** — 새로 깐 기계에만 서고 오래 쓴 기계는 조용히 뒤처지고,
#   화면은 둘 다 「홈 설정 · 썼다」로 똑같이 찍힌다(실측 2026-09-09 · 사내 VDI: 씨앗에 있는
#   `ENABLE_TOOL_SEARCH` 가 안 걸린 채로 「env 에 1개를 맞췄다」만 떴다 — 그 하나는 CA 였다).
# ⚠ **게이트웨이 값과 갈린다.** 저것은 사람마다·자리마다 달라 `#settings-env` 가 물어야 하지만
#   이것은 켜거나 안 켜거나뿐이라 사람이 정할 것이 없다 — 늘 맞춰도 뺏는 것이 없다.
# 스위치가 늘면 여기 한 줄을 더한다. 이 파일 안의 씨앗에는 안 적는다 — 아래에서 늘 맞춘다.
# ⚠ **다만 저장소의 `vdi-home-settings.json` 은 같이 고쳐야 한다.** 그것은 이 파일이 못 읽는
#   자리에 살고(배포 묶음에 안 실린다) `bootstrap-vdi.sh` 가 든다. 자리 파일이
#   `#home-settings = overwrite` 를 드는 자리(사외 VDI)에서는 **그 덮기가 이 설치보다 나중**
#   이라 씨앗이 최종 승자다 — 여기만 늘리면 그 자리에서 조용히 잃는다.
$Features = @{
  ENABLE_TOOL_SEARCH = 'true'    # 도구를 미리 다 안 싣고 필요할 때 찾아 쓴다
}

# ── 배선이 먼저다 ────────────────────────────────────────────────────────────────
# ⚠ winget 이 심은 PATH 는 **이 창에 안 걸린다** — 이 창이 winget 보다 먼저 떴다.
#   배선 없이 물으면 이미 깔린 것도 「없음」이 나와 재설치로 샌다. 그래서 묻기 전에도,
#   설치 직후에도 다시 태운다.
function Add-ToPath([string]$Dir) {
  if (-not $Dir -or -not (Test-Path -LiteralPath $Dir)) { return }
  if (($env:PATH -split ';') -contains $Dir) { return }   # 여러 번 불려도 PATH 가 안 분다
  $env:PATH = "$Dir;$env:PATH"
}

function Update-RuntimePath {
  # 파이썬 폴더 이름은 선언에서 판다 — 판을 여기 또 적으면 표와 어긋난다
  $pyId  = ($Apps | Where-Object { $_.Cmd -eq 'python' }).Id
  $pyTag = if ($pyId -match '(\d+)\.(\d+)$') { "Python$($Matches[1])$($Matches[2])" } else { $null }
  Add-ToPath "$env:ProgramFiles\nodejs"
  Add-ToPath "$env:ProgramFiles\Git\cmd"
  Add-ToPath "$env:ProgramFiles\GitHub CLI"
  Add-ToPath "$env:ProgramFiles\Microsoft VS Code\bin"
  Add-ToPath "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin"
  if ($pyTag) {
    Add-ToPath "$env:LOCALAPPDATA\Programs\Python\$pyTag"
    Add-ToPath "$env:LOCALAPPDATA\Programs\Python\$pyTag\Scripts"
  }
  Add-ToPath "$env:APPDATA\npm"
}

# ⚠ **존재로 묻지 않고 불러 본다.** 윈도우는 `WindowsApps\python` 에 스토어로 보내는
#   껍데기를 깔아 두고 `Get-Command` 가 그것을 잡아 「있음」을 낸다 — 부르면 죽는 파일이다.
#   「깔린 것과 닿는 것은 다른 명제」라, 그 오판으로 설치를 건너뛰면 뒤가 조용히 무너진다.
# 판을 한 줄로 읽는다 — 올리기 전후를 견주려면 숫자가 있어야 한다. 못 읽으면 빈 글자다.
function Get-Ver([string]$Cmd, [string]$Arg) {
  try { $o = (& $Cmd $Arg 2>$null | Select-Object -First 1); return ("$o").Trim() } catch { return '' }
}

# 자리를 **닿음으로** 가른다 — `#site-probe = 호스트:포트` 가 있으면 거기에 TCP 로 물어본다.
# ⚠ **이름으로 안 가른다.** DNS 는 사외에서도 사내 IP 를 풀어 주므로 이름만 봐서는 안 갈린다
#   (실측: 사외에서 사내 호스트가 사내 IP 로 풀리고 포트는 안 열렸다 · 결정 0026).
# ⚠ **규칙을 여기 옮겨 적은 것이 아니다.** 재는 대상은 값 파일이 든 그 한 줄이고, 부트스트랩도
#   같은 줄을 읽는다 — 몸통 둘이 **같은 선언**을 볼 뿐 규칙이 둘로 갈리지 않는다.
function Test-Reach([string]$HostPort, [int]$TimeoutMs = 3000) {
  if ($HostPort -notmatch '^(.+):(\d+)$') { return $false }
  $h = $Matches[1]; $p = [int]$Matches[2]
  $c = New-Object Net.Sockets.TcpClient
  try {
    if ($c.ConnectAsync($h, $p).Wait($TimeoutMs)) { return $c.Connected }
    return $false
  } catch { return $false } finally { $c.Dispose() }
}

# 한 호스트에 TLS 를 걸어 **체인의 뿌리**와 **윈도우가 그 체인을 믿는지**를 함께 낸다.
# 못 닿으면 $null — 못 닿은 것과 못 믿는 것은 다른 명제라 부르는 쪽이 갈라 쓴다.
# ⚠ **검증 콜백이 무조건 참을 낸다.** 여기는 신뢰를 정하는 자리가 아니라 상대가 무엇을 내미는지
#   **보는** 자리다 — 거절하면 볼 것도 못 본다. 신뢰 판정은 아래 `Build()` 가 든다.
# ⚠ **믿나를 저장소 조회로 묻지 않는다.** 처음엔 `Cert:\...\Root` 를 훑어 지문을 견줬는데,
#   그것은 **상태가 아니라 캐시**였다: 윈도우는 루트 CA 를 지연 로딩해서(자동 루트 업데이트)
#   맨바닥 기계에는 아직 디스크에 없고, 필요해질 때 받아 온다. 그래서 **멀쩡히 신뢰되는
#   공개 CA 를 「이 PC 가 모르는 CA」로 찍었다** — 실측 2026-09-09 · 사내 VDI: npm 설치가
#   정상으로 끝났는데 이 칸만 빨갰다. 멀쩡한 것을 빨갛게 만드는 판정은 가짜 초록보다 나쁘다.
#   진짜 상태는 「윈도우가 이 체인을 신뢰하나」이고 그 답은 `Build()` 만 든다.
# ⚠ 다만 **폐기 목록(CRL)을 못 물어본 것은 미신뢰가 아니다.** 그것 하나로도 `Build()` 는
#   거짓을 내는데, 뿌리가 저장소에 멀쩡히 있고 만료가 2040년인 자리에서 그랬다(실측
#   2026-09-10). 그래서 그 갈래만 덜어내고 나머지로 판정한다.
function Get-ChainRoot([string]$HostName, [int]$TimeoutMs = 5000) {
  $c = $null; $s = $null
  try {
    $c = New-Object Net.Sockets.TcpClient
    if (-not $c.ConnectAsync($HostName, 443).Wait($TimeoutMs)) { return $null }
    $s = New-Object Net.Security.SslStream($c.GetStream(), $false, { $true })
    $s.AuthenticateAsClient($HostName)
    if (-not $s.RemoteCertificate) { return $null }
    $leaf = New-Object Security.Cryptography.X509Certificates.X509Certificate2 $s.RemoteCertificate
    $ch = New-Object Security.Cryptography.X509Certificates.X509Chain
    $null = $ch.Build($leaf)
    if ($ch.ChainElements.Count -lt 1) { return $null }
    $blocking = @($ch.ChainStatus | Where-Object {
      $_.Status -ne 'RevocationStatusUnknown' -and $_.Status -ne 'OfflineRevocation' })
    return @{
      Root    = $ch.ChainElements[$ch.ChainElements.Count - 1].Certificate
      Trusted = ($blocking.Count -eq 0)
    }
  } catch { return $null }
  finally { if ($s) { $s.Dispose() }; if ($c) { $c.Dispose() } }
}

# 인증서 파일 한 장에서 **든 것을 다 꺼낸다.** PEM 묶음(여러 장)과 `.cer`(한 장) 둘 다 받는다.
# ⚠ **꼴을 묻지 않고 바이트를 본다.** 회사가 어느 꼴로 줄지는 우리가 못 정하고, 확장자는
#   거짓말을 한다 — `.cer` 안에 PEM 이 들어 있는 일이 흔하다.
function Read-CertFile([string]$Path) {
  $out = @()
  try {
    $bytes = [IO.File]::ReadAllBytes($Path)
    $text  = [Text.Encoding]::ASCII.GetString($bytes)
    if ($text -match '-----BEGIN CERTIFICATE-----') {
      foreach ($m in [regex]::Matches($text, '(?s)-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----')) {
        try {
          $raw = [Convert]::FromBase64String(($m.Groups[1].Value -replace '\s', ''))
          $out += New-Object Security.Cryptography.X509Certificates.X509Certificate2 -ArgumentList (,$raw)
        } catch { }   # 한 장이 깨져도 나머지는 산다
      }
    } else {
      $out += New-Object Security.Cryptography.X509Certificates.X509Certificate2 -ArgumentList (,$bytes)
    }
  } catch { }
  return $out
}

# ── Node 에 신뢰를 잇는다 — **새 신뢰를 만드는 것이 아니라 있는 것을 파생한다** ──────
# ⚠ **왜 이 칸이 있나.** 윈도우 신뢰 저장소가 이 PC 의 신뢰 진본인데 **Node 는 그것을 안 본다** —
#   제가 안고 다니는 CA 목록만 본다. 그래서 회사 장비가 TLS 를 가로채는 망에서는 브라우저·git·
#   파워셸이 다 멀쩡한데 **`code --install-extension` 과 `npm` 만 죽는다**(실측 2026-09-10 ·
#   사내 VDI: marketplace 가 사내 게이트웨이 이름으로 다시 봉해져 나왔고, 그 CA 는 윈도우
#   저장소에 이미 깔려 있었다). Node 에게 알려주는 자리가 `NODE_EXTRA_CA_CERTS` 하나다.
# ⚠ **검증을 끄는 것이 아니다.** 그 변수는 기본 목록에 **더한다** — 대체하지 않는다.
#   VS Code 의 `http.proxyStrictSSL: false` 는 반대로 검증 자체를 없애므로 안 쓴다.
# ⚠ **파이썬에서 겪은 것과 같은 병이다**(그쪽은 `truststore` 패키지가 든다 · 결정 0016).
#   런타임마다 제 신뢰 목록을 따로 드는 것이 뿌리고, 여기는 그중 Node 갈래다. git 은 이미
#   `http.sslBackend=schannel` 로 저장소를 보므로 이을 것이 없다.
# ⚠ **「가로채였나」로 판정하지 않는다.** 그것은 사건이라 끝이 없다. 판정은 상태로 한다 —
#   **잰 뿌리를 이 PC 가 이미 신뢰하나.** 신뢰하면 파생하고, 아니면 안 담고 이름을 댄다.
#   그래야 이 스크립트가 **마주친 아무 가로채기나 믿게 되는 자**가 되지 않는다.
# ⚠ 가로채인 것만 골라 담지 않는다 — Node 가 무엇을 이미 아는지는 여기서 못 재고, 그것을
#   추측으로 가르면 틀리는 날 조용히 죽는다. **더 담아도 무해하다**(더하는 목록이라 중복은
#   무시된다). 나중에 다른 호스트가 가로채여도 코드를 안 고치고 산다.
function Wire-NodeTrust {
  # 신뢰의 근거는 둘이고 **둘 다 이 PC 밖에서 정해진 것이다** — 설치기가 짓지 않는다.
  #   ① 윈도우가 그 체인을 믿는가 — 물어보는 자는 `Get-ChainRoot` 의 `Trusted` 다.
  #      **저장소를 훑어 지문을 견주지 않는다** — 그 까닭은 저 함수의 머리가 든다.
  #   ② 값 파일이 `#corp-ca` 로 가리킨 파일 — 회사가 배포 묶음에 실어 보낸 것
  # ⚠ **②가 있는 까닭 — 맨바닥 VDI 는 회사 CA 를 아직 안 받은 채로 뜬다.** ①만 보면 설치는
  #   「모르는 CA」라고 정확히 진단하고 멈추는데, **맨바닥을 세우는 것이 이 스크립트가 있는
  #   까닭**이라 거기서 멈추면 할 일을 안 한 것이다(실측 2026-09-09: 확장이 여섯 번 인증서로
  #   죽었고 그때 길에 있던 CA 는 이 PC 가 모르는 것이었다).
  $corp = @()
  $corpRel = Read-Directive $script:EnvFile 'corp-ca'
  if ($corpRel) {
    $corpPath = if ([IO.Path]::IsPathRooted($corpRel)) { $corpRel }
                else { Join-Path $script:Here $corpRel }
    if (Test-Path -LiteralPath $corpPath) {
      $corp = @(Read-CertFile $corpPath)
      if ($corp.Count) { Write-Host "  회사 CA $($corp.Count)장 — $(Split-Path -Leaf $corpPath)" }
      else {
        Write-Host "  ! 회사 CA 파일에서 인증서를 못 읽었다 — $corpPath" -ForegroundColor Red
        $script:Fails.Add('Node 신뢰 배선 (회사 CA 파일을 못 읽는다)')
      }
    } else {
      # ⚠ **조용히 넘기지 않는다.** 값 파일이 가리켰는데 없는 것은 배포가 빠뜨린 것이고,
      #   그 빠짐은 CA 가 없는 PC 에서만 드러난다 — 여기서 안 말하면 아무도 모른다.
      Write-Host "  ! 값 파일이 가리킨 회사 CA 가 없다 — $corpPath" -ForegroundColor Red
      $script:Fails.Add('Node 신뢰 배선 (회사 CA 가 없다)')
    }
  }

  # 실어 온 것의 지문 — 윈도우가 아직 모르는 CA 라도 이것에 있으면 근거가 선다.
  $corpTp = @{}
  foreach ($c in $corp) { $corpTp[$c.Thumbprint] = $true }

  # ⚠ **실어 보낸 것은 잰 뿌리와 안 맞아도 담는다.** 그 파일이 그 자리의 진본이고, 우리가
  #   다시 거르면 판단이 두 자리에 산다 — 회사가 뺀 것도 아닌데 설치기가 뺀 꼴이 된다.
  $roots   = @{}
  foreach ($c in $corp) { $roots[$c.Thumbprint] = $c }
  $unknown = @()
  foreach ($h in $script:TlsHosts) {
    $r = Get-ChainRoot $h
    if (-not $r) { continue }                       # 못 닿은 것과 못 믿는 것은 다른 명제다
    # 근거 둘 — 윈도우가 그 체인을 믿거나, 뿌리가 회사가 실어 온 목록에 있거나.
    if ($r.Trusted -or $corpTp[$r.Root.Thumbprint]) { $roots[$r.Root.Thumbprint] = $r.Root }
    else { $unknown += "$h  ->  $($r.Root.Subject)" }
  }

  if ($unknown) {
    # ⚠ **여기서 안 묻는다.** 이 PC 가 모르는 CA 를 신뢰할지는 설치기가 낼 판단이 아니다.
    Write-Host '  ! 이 PC 가 모르는 CA 가 길에 있다 — 담지 않는다:' -ForegroundColor Red
    $unknown | ForEach-Object { Write-Host "      $_" }
    Write-Host '     회사 루트 인증서가 아직 이 PC 에 없다. 배포 묶음으로 실어 보내려면'
    Write-Host '     값 파일에 `#corp-ca = <파일>` 을 두고 그 파일을 같이 넣는다.'
    $script:Fails.Add('Node 신뢰 배선 (모르는 CA)')
  }
  if ($roots.Count -eq 0) {
    Write-Host '  담을 것이 없다 (아무 데도 못 닿았다)'
    return
  }

  # PEM 으로 뽑는다. `BEGIN` 앞의 글자는 파서가 무시하므로 **무엇인지 적어 둔다** —
  # 나중에 이 파일을 연 사람이 왜 이것이 여기 있는지 알아야 한다.
  $sb = New-Object Text.StringBuilder
  [void]$sb.AppendLine('# Node 가 볼 CA 묶음 — install.ps1 이 뽑았다. 손으로 고치지 않는다.')
  [void]$sb.AppendLine('# 진본은 윈도우 신뢰 저장소다. 여기 있는 것은 이 PC 가 이미 믿는 것 중')
  [void]$sb.AppendLine('# 이 설치가 실제로 여는 자리의 체인 뿌리만 뽑아 온 사본이라, 다시 뽑으면 새로 선다.')
  foreach ($r in $roots.Values) {
    [void]$sb.AppendLine("# $($r.Subject)")
    [void]$sb.AppendLine('-----BEGIN CERTIFICATE-----')
    [void]$sb.AppendLine([Convert]::ToBase64String($r.RawData, 'InsertLineBreaks'))
    [void]$sb.AppendLine('-----END CERTIFICATE-----')
  }

  # ⚠ **BOM 을 안 찍는다.** PEM 파서는 바이트로 읽는다 — 앞에 BOM 이 붙으면 첫 줄이 어긋난다.
  $target = Join-Path $env:USERPROFILE '.claude\node-ca.pem'
  try {
    $dir = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [IO.File]::WriteAllText($target, $sb.ToString(), (New-Object Text.UTF8Encoding($false)))
  } catch {
    Write-Host "  ! CA 묶음을 못 썼다 — $(Say-Why $_)" -ForegroundColor Red
    $script:Fails.Add('Node 신뢰 배선 (파일 쓰기)')
    return
  }

  # ⚠ **남의 파일을 안 덮는다.** Node 는 이 변수 하나만 보므로 덮으면 저쪽 신뢰가 조용히 사라진다.
  #   레지스트리에서 읽는다 — 이 창의 값은 우리가 방금 넣었을 수 있어 판정이 못 선다.
  $cur = [Environment]::GetEnvironmentVariable('NODE_EXTRA_CA_CERTS', 'User')
  if ($cur -and $cur -ne $target -and (Test-Path -LiteralPath $cur)) {
    Write-Host '  ! NODE_EXTRA_CA_CERTS 가 이미 다른 파일을 가리킨다 — 안 덮는다' -ForegroundColor Red
    Write-Host "      지금 가리키는 것:  $cur"
    Write-Host "      우리가 뽑아 둔 것:  $target"
    Write-Host '     둘을 한 파일로 합치고 그것을 가리키게 한다.'
    $script:Fails.Add('Node 신뢰 배선 (이미 다른 파일을 가리킨다)')
    return
  }

  Write-Host ("  CA {0}장 — {1}" -f $roots.Count, (($roots.Values | ForEach-Object {
    if ($_.Subject -match 'CN=([^,]+)') { $Matches[1] } else { $_.Subject }
  }) -join ' · '))
  Plant-Var 'NODE_EXTRA_CA_CERTS' $target
}

# 네이티브 명령을 돌리고, **모든 스트림을 파일로 잡는다.** 종료코드를 돌려준다.
# 실패했을 때 그 파일을 펴는 것은 부르는 쪽의 몫이다 — 성공한 판의 잡소리까지 찍지 않으려고.
function Invoke-Logged([string]$File, [string[]]$CmdArgs, [string]$LogPath) {
  # ⚠ **여기서만 `Stop` 을 푼다.** 네이티브의 stderr 는 `*>` 로 파일에 돌려도 오류 레코드로
  #   올라오고, 바깥의 `Stop` 이 그 자리에서 던진다 — 「파일로 보냈으니 괜찮겠지」가 안 통한다.
  #   실측 2026-09-09: `code` 가 -1(잡힌 예외)로 끝나고 로그가 `Installing extensions...`
  #   에서 잘렸다. **경고는 실패가 아닌데 그 한 줄이 설치를 끊었다.**
  #   판정은 종료코드와 프로브가 든다 — 뱉은 글자가 아니라. 그래서 여기서는 안 던지게 하고,
  #   글자는 파일에 그대로 쌓아 실패했을 때만 편다.
  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try { & $File @CmdArgs *> $LogPath; return $LASTEXITCODE }
  catch { return -1 }
  finally { $ErrorActionPreference = $prev }
}

# 실패 사유 한 줄. **까닭을 대는 자리라 읽히게 잘라 준다.**
# ⚠ **사유가 늘 사람 말인 것은 아니다.** 가로채는 프록시는 오류를 **HTML 페이지 통째로** 준다 —
#   그대로 찍으면 `<html><body><h1>` 이 줄을 먹고 정작 아는 것(`504 Gateway Time-out`)이 묻힌다.
#   실측 2026-09-11(사내): PSGallery 자리의 사유가 그 꼴로 기록에 실려, **왜 졌는지를 아무도
#   못 읽었다.** 까닭을 대라고 둔 줄이 까닭을 덮은 자리다.
# ⚠ **줄바꿈이 없는 꼴이 더 나쁘다** — 첫 줄만 집어도 문서 전체가 한 줄이라 562자가 쏟아졌다.
#   그래서 **표시를 걷고 · 빈칸을 접고 · 길이를 문다.** 셋 다 있어야 한 줄로 선다.
# ⚠ **갈래 이름을 앞에 붙인다** — `WebException` 인지 `UnauthorizedAccessException` 인지가
#   「망이냐 권한이냐」를 그 자리에서 가른다. 글만 보고는 그게 안 갈린다.
function Say-Why($ErrorRecord) {
  $e = $null
  try { $e = $ErrorRecord.Exception } catch { }
  $t = ''
  if ($e) { $t = [string]$e.Message }
  if (-not $t) { return '(까닭을 안 준다)' }
  $t = $t -replace '<[^>]*>', ' '                 # 표시를 걷는다
  $t = ($t -replace '\s+', ' ').Trim()            # 줄바꿈·연속 빈칸을 하나로 접는다
  if ($t.Length -gt 160) { $t = $t.Substring(0, 160).TrimEnd() + '…' }
  if (-not $t) { $t = '(글자 없는 사유)' }
  $kind = ''
  if ($e) { $kind = $e.GetType().Name }
  if ($kind) { return "$kind : $t" }
  return $t
}

# ⚠ **비면 비었다고 말한다.** 부르는 자리마다 바로 앞줄이 「뱉은 끝 줄」을 약속하는데,
#   조용히 끝나면 **약속만 남고 까닭이 없다** — 읽는 사람은 화면이 잘린 줄 알고 그 자리에서
#   멈춘다. 실측 2026-09-11(사내): `! VS Code 설치 실패 — winget 이 뱉은 끝 5줄:` 다음이
#   곧바로 다음 앱 줄이었다. 「글자 없이 졌다」도 **단서다** — 그 자체가 winget 이 아예 못 떴다는
#   뜻이라, 비었다는 사실을 말해야 다음 물음이 선다.
function Show-Log([string]$LogPath, [int]$Lines = 8) {
  $t = @()
  if (Test-Path -LiteralPath $LogPath) {
    $t = @(Get-Content -LiteralPath $LogPath -Tail $Lines -ErrorAction SilentlyContinue |
           Where-Object { $_ -and $_.Trim() })
  }
  if ($t.Count) { $t | ForEach-Object { Write-Host "      $_" } }
  else { Write-Host '      (한 줄도 안 뱉었다 — 명령이 글자 없이 졌다)' }
}

function Test-Runs([string]$Cmd, [string]$Arg) {
  if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) { return $false }
  try { & $Cmd $Arg 2>$null | Out-Null; return ($LASTEXITCODE -eq 0) } catch { return $false }
}

# `#이름 = 값` 꼴 지시를 읽는다 — 값(`이름=값`)과 달리 이것은 **어디로 갈지**를 든다.
# 자리 파일이 `#site-probe`·`#home-settings` 로 쓰는 어법과 같다: 몸통은 주소를 모르고
# 파일이 든다.
function Read-Directive([string]$Path, [string]$Key) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
    if ($line -match "^\s*#\s*$([regex]::Escape($Key))\s*=\s*(.+?)\s*$") { return $Matches[1] }
  }
  return $null
}

# 사용자 환경변수로 심는다 — `HKCU\Environment` 에 써서 **새로 뜨는 프로세스부터** 걸린다.
# ⚠ `setx` 를 안 쓴다. 같은 자리에 쓰지만 **값이 1024자를 넘으면 못 쓴다** — 토큰은 그보다
#   길 수 있고, 그때 사람은 「왜 안 되지」를 키가 아니라 주소에서 찾게 된다. .NET 쪽에는
#   그 한도가 없고 설정 바뀜 알림도 똑같이 돈다.
# ⚠ **이 창에도 같이 심는다.** 저것은 새 프로세스부터라, 안 심으면 아래 검증이 방금 넣은
#   값을 「없다」로 본다.
function Plant-Var([string]$Name, [string]$Value) {
  try {
    [Environment]::SetEnvironmentVariable($Name, $Value, 'User')
    Set-Item -Path "Env:$Name" -Value $Value
    # 심은 것을 모아 둔다 — 자리가 그러라고 하면 홈 설정에도 같은 값을 민다(5칸).
    # 값을 두 번 읽지 않고 **한 번 정한 것을 두 자리로 민다** — 그것이 파생과 사본을 가른다.
    $script:Planted[$Name] = $Value
    Write-Host "  $Name — 심었다" -ForegroundColor Green
  } catch {
    Write-Host "  ! $Name 심기 실패 — $(Say-Why $_)" -ForegroundColor Red
    $script:Fails.Add("$Name 심기")
  }
}

# `이름=값` 한 줄씩. `#` 뒤는 주석. 값에 따옴표를 씌우지 않는다 (secrets.env 와 같은 꼴).
# ⚠ 줄끝 CR 을 턴다 — CRLF 로 받으면 값 끝의 CR 이 그대로 심겨 아무 데서도 안 먹히는 키가 된다.
function Read-EnvFile([string]$Path) {
  $map = @{}
  if (-not (Test-Path -LiteralPath $Path)) { return $map }
  foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
    $t = $line.Trim()
    if (-not $t -or $t.StartsWith('#') -or ($t -notmatch '=')) { continue }
    $k = $t.Substring(0, $t.IndexOf('=')).Trim()
    $v = $t.Substring($t.IndexOf('=') + 1).Trim()
    if ($k) { $map[$k] = $v }
  }
  return $map
}

Write-Host ''
Write-Host '=== Claude Code 환경 설치 ===' -ForegroundColor Cyan
Write-Host ''

# ── 1. winget ────────────────────────────────────────────────────────────────────
# ⚠ **없다고 여기서 죽지 않는다.** winget 이 없으면 **못 까는 것**이지 아무것도 못 하는 것이
#   아니다 — 확장·CLI·키 심기·홈 설정은 winget 없이 다 선다. 그리고 사내 PC 에는 런타임이
#   이미 깔려 있는 일이 흔하다(사내 환경 문서가 Node·Python·Git 판을 적고 있다). 죽으면
#   **다 있는 기계에서도 아무것도 안 되고**, 사람은 못 여는 스토어만 쳐다보게 된다.
#   ⚠ 그렇다고 조용히 넘기지도 않는다: 못 깐 것은 아래에서 이름을 대고 실패로 적힌다.
# ── winget 을 되살려 본다 — 없다고 바로 물러나기 전에 ────────────────────────────
# ⚠ **가장 흔한 자리는 「안 깔림」이 아니라 「이 프로필에 등록 안 됨」이다.** winget 은 AppX
#   (App Installer)라 기계에는 프로비저닝돼 있는데 사용자 프로필에는 등록이 안 되는 일이
#   있고, **비영속 VDI 는 로그인마다 프로필이 새로 나서 늘 그 꼴**이다. 그건 네트워크 없이
#   재등록만으로 선다 — 먼저 그것부터 해 본다. 공짜인 것을 뒤에 두면 안 된다.
# ⚠ 그다음이 **마이크로소프트가 문서에 적어 둔 길**이다 — PSGallery 에서 WinGet 모듈을 받아
#   `Repair-WinGetPackageManager` 로 스스로 고치게 한다. **사내 VDI 에서 실제로 됐다**
#   (사용자 확인 2026-09-09). 되는 것이 먼저라 내가 지은 내려받기보다 앞에 세운다.
# ⚠ 마지막이 내려받기다. 사내 환경 문서가 **GitHub HTTPS 는 열려 있다**고 적고 있어 그 길로
#   간다 — 스토어는 막혀 있어도 이쪽은 열린 자리가 있다.
# ⚠ **정책이 막으면 조용히 지지 않는다.** 사이드로딩을 막아 둔 기계가 있고, 그건 우리가
#   넘을 자리가 아니다 — 무엇을 시도했고 무엇에 걸렸는지 적고 물러난다.
function Restore-Winget {
  Write-Host '  winget 이 없다 — 되살려 본다.' -ForegroundColor Yellow
  # ⚠ **TLS 1.2 를 여기서 세운다 — 세 갈래가 다 HTTPS 를 탄다.** 옛 판은 이 줄이 셋째
  #   갈래(GitHub) 안에만 있어, **PSGallery 를 부르는 둘째 갈래가 기본값으로 돌았다.**
  #   Windows PowerShell 5.1 의 기본은 기계에 따라 아직 SSL3/TLS1.0 이고 PSGallery 는 TLS 1.2
  #   아래로는 안 받으므로, 그 자리에서 지면 「망이 죽었다」로 보인다 — 죽은 것은 우리 손이다.
  # ⚠ **덮어쓰지 않고 더한다.** 그냥 대입하면 그 기계가 쓰던 더 높은 판(TLS 1.3)을 지운다.
  try {
    [Net.ServicePointManager]::SecurityProtocol =
      [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
  } catch { }

  # ⚠ **갈래를 넘기는 기준은 「깔았다」가 아니라 「불리나」다.** 갈래마다 「됐다」고 말하면서
  #   실제로는 안 잡히는 자리가 있다 — AppX 는 깔려도 이 세션의 PATH 에 안 잡힐 수 있다.
  #   그래서 밟은 뒤마다 **PATH 를 레지스트리에서 새로 읽고** 다시 묻는다.
  #   ⚠ 이 세션 PATH 만 보면 방금 깔린 것을 영영 못 본다: 창은 뜰 때 환경을 한 번 복사한다.
  $reach = {
    foreach ($sc in @('Machine','User')) {
      $v = [Environment]::GetEnvironmentVariable('Path', $sc)
      if ($v) { foreach ($d in ($v -split ';')) { Add-ToPath $d } }
    }
    [bool](Get-Command winget -ErrorAction SilentlyContinue)
  }

  # ① 이 프로필에 다시 등록한다 (네트워크 없음)
  try {
    Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe `
      -ErrorAction Stop
    if (& $reach) {
      Write-Host '  되살렸다 (프로필에 다시 등록)' -ForegroundColor Green
      return $true
    }
    # ⚠ **조용히 다음으로 넘어가지 않는다.** 「됐다는데 안 잡힌다」는 「안 됐다」와 다른
    #   명제이고, 그 차이가 다음에 어디를 팔지를 정한다.
    Write-Host '    · 재등록은 됐는데 winget 이 안 잡힌다 — 다음을 해 본다'
  } catch {
    Write-Host "    · 재등록 안 됨 — $(Say-Why $_)"
  }

  # ② 마이크로소프트가 적어 둔 길 — PSGallery 의 WinGet 모듈이 스스로 고친다
  # ⚠ **이것이 실측으로 되는 것이 확인된 갈래다**(사용자 확인 2026-09-09 · 사내 VDI).
  #   그래서 내려받기(③)보다 앞에 선다 — 되는 것이 먼저다.
  # ⚠ `$ProgressPreference` 를 끈다. 진행 막대를 그리느라 몇 배가 느려지는 자리다.
  # ⚠ `-AllUsers` 는 관리자를 탄다. 안 되면 그것 없이 한 번 더 — 제 계정에만 서도 쓸 수 있다.
  try {
    Write-Host '    · PowerShell 모듈로 고쳐 본다 (PSGallery)'
    $pp = $ProgressPreference; $ProgressPreference = 'SilentlyContinue'
    try {
      # ⚠ **있으면 안 받는다.** 이미 깔린 모듈을 `-Force` 로 다시 깔면 윈도우가
      #   「쓰는 중이라 못 바꾼다」로 문다 — 실측 2026-09-11(사내): *「현재 'Microsoft.WinGet.Client'
      #   모듈의 '1.29.280' 버전을 사용 중입니다」*. 받을 까닭이 없는 걸음이었다.
      if (Get-Module -ListAvailable -Name Microsoft.WinGet.Client) {
        Write-Host '      (모듈이 이미 있다 — 안 받는다)'
      } else {
        # ⚠ **받기가 져도 여기서 끝내지 않는다.** 옛 판은 이 둘을 `-ErrorAction Stop` 으로
        #   묶어 두어, **준비 걸음 하나가 막히면 본 걸음까지 못 갔다** — 정작 `Repair` 는
        #   모듈만 있으면 서는데. 사내에서 진 자리가 그것이다: 받으러 나간 길이 504 를 내자
        #   그 줄에서 끝났고, 같은 명령을 사람이 손으로 돌리면 경고만 내고 넘어가 Repair 가 섰다.
        #   **준비의 실패가 본 걸음을 막지 않게** 갈래를 끊는다.
        try {
          Install-PackageProvider -Name NuGet -Force -ErrorAction Stop | Out-Null
          Install-Module -Name Microsoft.WinGet.Client -Force -Repository PSGallery `
            -ErrorAction Stop | Out-Null
        } catch {
          Write-Host "      (모듈을 못 받았다 — $(Say-Why $_)) — 있는 것으로 해 본다"
        }
      }
      try { Repair-WinGetPackageManager -AllUsers -ErrorAction Stop }
      catch { Repair-WinGetPackageManager -ErrorAction Stop }
    } finally { $ProgressPreference = $pp }
    if (& $reach) {
      Write-Host '  되살렸다 (Repair-WinGetPackageManager)' -ForegroundColor Green
      return $true
    }
    Write-Host '    · 모듈은 돌았는데 winget 이 안 잡힌다 — 다음을 해 본다'
  } catch {
    Write-Host "    · 모듈로 안 됨 — $(Say-Why $_)"
  }

  # ③ GitHub 릴리스에서 받아 깐다
  try {
    Write-Host '    · GitHub 릴리스에서 받아 본다'
    $rel = Invoke-RestMethod 'https://api.github.com/repos/microsoft/winget-cli/releases/latest' `
             -UseBasicParsing -ErrorAction Stop
    $work = Join-Path ([IO.Path]::GetTempPath()) "winget-$PID"
    New-Item -ItemType Directory -Path $work -Force | Out-Null

    # 딸린 것이 먼저다 — 없으면 본체 설치가 그 자리에서 진다
    $dep = $rel.assets | Where-Object { $_.name -like '*Dependencies.zip' } | Select-Object -First 1
    if ($dep) {
      $z = Join-Path $work 'dep.zip'
      Invoke-WebRequest $dep.browser_download_url -OutFile $z -UseBasicParsing -ErrorAction Stop
      Expand-Archive -LiteralPath $z -DestinationPath (Join-Path $work 'dep') -Force
      Get-ChildItem (Join-Path $work 'dep') -Recurse -Filter '*.appx' |
        Where-Object { $_.FullName -match 'x64' } |
        ForEach-Object { try { Add-AppxPackage -Path $_.FullName -ErrorAction Stop } catch { } }
    }

    $pkg = $rel.assets | Where-Object { $_.name -like '*.msixbundle' } | Select-Object -First 1
    if (-not $pkg) { throw '릴리스에 msixbundle 이 없다' }
    $b = Join-Path $work $pkg.name
    Invoke-WebRequest $pkg.browser_download_url -OutFile $b -UseBasicParsing -ErrorAction Stop
    Add-AppxPackage -Path $b -ErrorAction Stop
    Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue

    if (& $reach) {
      Write-Host "  되살렸다 (GitHub 릴리스 $($rel.tag_name))" -ForegroundColor Green
      return $true
    }
    Write-Host '    · 깔았는데 winget 이 안 잡힌다 — 새 창에서는 잡힐 수 있다'
  } catch {
    Write-Host "    · 내려받기 안 됨 — $(Say-Why $_)"
  }

  return $false
}

$noWinget = -not (Get-Command winget -ErrorAction SilentlyContinue)
if ($noWinget) {
  if (Restore-Winget) { $noWinget = $false; Update-RuntimePath }
}
if ($noWinget) {
  Write-Host '  winget 을 못 되살렸다 — 프로그램을 새로 깔지는 못한다.' -ForegroundColor Yellow
  Write-Host '  이미 깔린 것으로 진행한다. 모자란 것은 끝에 이름을 댄다.'
  Write-Host '  (사내 PC 면 스토어가 막혔을 수 있다 — 모자란 것은 IT 에 요청한다)'
  Write-Host ''
}

Update-RuntimePath

# ── 2. 앱 ────────────────────────────────────────────────────────────────────────
# ⚠ `--source winget` 을 박는다 — 사내에서 빼면 인증서 검증에 걸린다.
# ⚠ **판정은 종료코드가 아니라 프로브다.** winget 은 이미 깔려 있으면 「올릴 것이 없다」로
#   0 이 아닌 값을 내는데, 그것을 실패로 읽으면 멀쩡한 PC 가 매번 빨갛게 보고된다.
$WG = @('--source','winget','--exact','--silent',
        '--accept-package-agreements','--accept-source-agreements','--disable-interactivity')

# ── 자리 — **프로그램 칸보다 앞이다.** 무엇을 깔지가 자리에 달렸기 때문이다(데스크탑 앱).
#    아래 4칸의 키 판정도 이 값을 다시 쓴다 — 한 번 재고 둘이 나눠 쓴다.
# ⚠ **자리는 셋이다 — 사내 · 사외 · 모름.** 프로브가 없으면 「사내」가 아니라 **모르는 것**이다.
#   둘로만 가르면 안 재고 사내라고 말하게 되고, 그 거짓 위에서 데스크탑 앱 같은 판정이 선다
#   (실측 2026-09-09: 프로브 없는 판이 「사내라 안 깐다」를 찍었다 — 잰 적이 없는데).
$probe   = Read-Directive $EnvFile 'site-probe'
$site    = 'unknown'
if ($probe) { $site = if (Test-Reach $probe) { 'inside' } else { 'outside' } }
$offsite = ($site -eq 'outside')
if ($probe) {
  Write-Host ("  자리 = {0}  ({1} {2})" -f
    $(if ($offsite) { '사외' } else { '사내' }), $probe,
    $(if ($offsite) { '안 닿음' } else { '닿음' }))
  Write-Host ''
}

# ── 올릴 것이 있는 앱을 **한 번에** 묻는다 ─────────────────────────────────────
# ⚠ 옛 판은 앱마다 `winget upgrade --id` 를 불렀다. 그 명령은 이미 최신이면 아무것도 안 하지만
#   **winget 은 뜰 때마다 원본을 새로 훑는다** — 앱 수만큼 그 값을 낸다. `list
#   --upgrade-available` 은 그 훑기를 한 번에 끝낸다.
# ⚠ **못 읽으면 옛 길로 물러선다.** 이 출력은 표라서 로케일·콘솔 너비·잘린 Id 에 흔들린다.
#   못 읽은 것을 「올릴 것 없음」으로 읽으면 **판이 낡은 채로 초록이 된다** — 부재보다 나쁘다.
#   그래서 `$null` 은 「못 쟀다」이고, 그때는 앱마다 묻는 옛 길로 간다.
# ⚠ **기울기를 한쪽으로만 준다.** Id 가 표에서 잘릴 수 있어 **Id 든 이름이든 걸리면 올린다** —
#   헛되게 한 번 더 묻는 값은 시간뿐이고, 안 물어 낡은 판이 서는 값은 고장이다.
$upgradable = $null
if (-not ($NoUpgrade -or $noWinget)) {
  $ulog = [System.IO.Path]::GetTempFileName()
  $urc = Invoke-Logged 'winget' @('list','--upgrade-available','--accept-source-agreements','--disable-interactivity') $ulog
  $utxt = ''
  if (Test-Path $ulog) { $utxt = (Get-Content $ulog -Raw -ErrorAction SilentlyContinue) }
  Remove-Item $ulog -ErrorAction SilentlyContinue
  if ($urc -eq 0 -and $utxt -and $utxt.Length -gt 40) {
    $hits = @()
    foreach ($a in $Apps) {
      if (($utxt -like "*$($a.Id)*") -or ($utxt -like "*$($a.Name)*")) { $hits += $a.Id }
    }
    $upgradable = $hits
    if ($hits.Count) {
      Write-Host ('  올릴 것 ' + $hits.Count + '개 — ' + ($hits -join ' · '))
    } else {
      Write-Host '  올릴 것 없음 — 판 대조를 한 번에 끝냈다'
    }
  } else {
    Write-Host '  (올릴 목록을 한 번에 못 받았다 — 앱마다 묻는다)'
  }
}

Write-Host '[1/8] 프로그램' -ForegroundColor Cyan
foreach ($app in $Apps) {
  if ($NoDevTools -and $app.Need -eq 'dev') {
    Write-Host "  $($app.Name) — 건너뜀 (-NoDevTools)"
    continue
  }
  if (Test-Runs $app.Cmd $app.Arg) {
    $before = Get-Ver $app.Cmd $app.Arg
    if ($NoUpgrade -or $noWinget) {
      Write-Host "  $($app.Name) — 있음  ($before)"
      continue
    }
    # ⚠ **판정은 winget 의 종료코드가 아니라 판 번호다.** 올릴 것이 없으면 winget 은 0 이 아닌
    #   값을 내는데, 그걸 실패로 읽으면 최신인 PC 가 매번 빨갛게 보고된다.
    # 한 번에 받은 목록에 없으면 안 묻는다. **`$null`(못 쟀다)일 때는 물어본다.**
    if (($null -ne $upgradable) -and ($upgradable -notcontains $app.Id)) {
      Write-Host "  $($app.Name) — 최신  ($before)"
      continue
    }
    $log = [System.IO.Path]::GetTempFileName()
    Invoke-Logged 'winget' (@('upgrade','--id',$app.Id) + $WG) $log | Out-Null
    Remove-Item $log -ErrorAction SilentlyContinue
    Update-RuntimePath
    $after = Get-Ver $app.Cmd $app.Arg
    if ($after -and $after -ne $before) {
      Write-Host "  $($app.Name) — 올렸다  $before  ->  $after" -ForegroundColor Green
    } else {
      Write-Host "  $($app.Name) — 최신  ($before)"
    }
    continue
  }

  if ($noWinget) {
    Write-Host "  ! $($app.Name) — 없는데 winget 이 없어 못 깐다" -ForegroundColor Red
    $Fails.Add("$($app.Name) (winget 이 없다)")
    continue
  }

  Write-Host "  $($app.Name) — 설치 ($($app.Id))"
  $log = [System.IO.Path]::GetTempFileName()
  # 진행 막대가 로그를 덮는다. 실패할 때만 편다
  # ⚠ **종료코드를 안 버린다.** 판정은 여전히 프로브가 든다(winget 은 「올릴 것 없음」에도
  #   0 이 아닌 값을 내므로 그것만으로는 못 믿는다). 다만 프로브가 끝내 못 잡았을 때
  #   **「깔렸는데 이 창이 못 잡는다」와 「진짜 못 깔았다」를 가르는 자가 이것뿐이다.**
  $rc = Invoke-Logged 'winget' (@('install','--id',$app.Id) + $WG) $log
  Update-RuntimePath
  # ⚠ **한 번 재고 포기하지 않는다.** winget 이 일을 떼어 놓고 먼저 돌아오는 자리가 있어,
  #   곧바로 물으면 아직 안 선 것을 「실패」로 찍는다 — 실측 2026-09-11(사내 PC): VS Code 가
  #   제어판에 **「새로 설치됨」**으로 앉았는데 우리 기록은 `설치 실패` 였고, winget 로그는
  #   **한 줄도 없었으며**, 설치기 창이 한참 **뒤에** 떴다. 셋 다 「먼저 돌아왔다」의 자국이다.
  #   그래서 몇 초를 더 준다. **이미 선 기계는 첫 물음에 서므로 느려지는 값이 없다.**
  # ⚠ 기다리는 동안 배선을 다시 태운다 — 설치가 끝나면서 그 폴더가 **그때 생긴다.**
  $ok = $false
  for ($i = 0; $i -lt 8; $i++) {
    if (Test-Runs $app.Cmd $app.Arg) { $ok = $true; break }
    Start-Sleep -Milliseconds 750
    Update-RuntimePath
  }
  if ($ok) {
    Write-Host "  $($app.Name) — 깔았다" -ForegroundColor Green
  } elseif ($rc -eq 0) {
    # ⚠ **거짓 빨강을 덜되 초록으로 넘기지는 않는다.** winget 이 성공이라 했는데 이 창이
    #   못 잡는 것은 흔히 PATH 가 **새 프로세스부터** 서기 때문이다. 그래도 못 잡은 것은 못 잡은
    #   것이라 남긴다 — 바꾸는 것은 **사유**뿐이다. 「설치 실패」라고 적으면 멀쩡히 깔린 것을
    #   찾아 헤매게 되고, 오늘 그 자리에서 한참을 썼다.
    Write-Host "  ! $($app.Name) — winget 은 깔았다는데 이 창이 못 잡는다 (새 창에서 잡힌다)" -ForegroundColor Yellow
    $Fails.Add("$($app.Name) (깔렸는데 이 창에서 안 잡힌다 — 새 창에서 본다)")
  } else {
    Write-Host "  ! $($app.Name) 설치 실패 (winget 이 $rc 로 끝났다) — 뱉은 끝 줄:" -ForegroundColor Red
    Show-Log $log 5
    $Fails.Add("$($app.Name) 설치")
  }
  Remove-Item $log -ErrorAction SilentlyContinue
}

# ── 2′. Claude 데스크탑 앱 — **자리가 정한다** ──────────────────────────────────
# ⚠ **사내에는 쓸모가 없다.** 게이트웨이를 물리는 `ANTHROPIC_BASE_URL` 을 읽는 것은 Claude
#   Code CLI 뿐이고 앱에는 그 스위치가 없다 — 깔려도 앤트로픽 본사로 나가려 하고 그 길이
#   막혀 있다. 그래서 값 파일이 `#desktop-app = offsite` 를 들면 **사외로 판정될 때만** 깐다.
#   `yes` 면 자리를 안 가리고 깐다. 없으면 안 깐다.
# ⚠ **GUI 앱이라 PATH 로 못 잰다.** `--version` 을 부를 이름이 안 생겨 다른 것들이 쓰는
#   프로브가 여기서는 안 선다 — winget 의 목록에 묻는다. 닿을 이름이 아예 없는 자리다.
$wantApp = Read-Directive $EnvFile 'desktop-app'
if ($wantApp -eq 'yes' -or ($wantApp -eq 'offsite' -and $offsite)) {
  Write-Host ''
  Write-Host '  Claude 데스크탑 앱' -ForegroundColor Cyan
  if ($noWinget) {
    Write-Host '  ! winget 이 없어 못 깐다' -ForegroundColor Red
    $Fails.Add('Claude 데스크탑 앱 (winget 이 없다)')
  } else {
    $there = {
      $tl = [IO.Path]::GetTempFileName()
      $rc = Invoke-Logged 'winget' @('list','--id',$DesktopApp,'--source','winget') $tl
      Remove-Item $tl -ErrorAction SilentlyContinue
      $rc -eq 0
    }
    if (& $there) {
      if (-not $NoUpgrade) {
        $al = [IO.Path]::GetTempFileName()
        Invoke-Logged 'winget' (@('upgrade','--id',$DesktopApp) + $WG) $al | Out-Null
        Remove-Item $al -ErrorAction SilentlyContinue
      }
      Write-Host '  있음'
    } else {
      $al = [IO.Path]::GetTempFileName()
      Invoke-Logged 'winget' (@('install','--id',$DesktopApp) + $WG) $al | Out-Null
      if (& $there) {
        Write-Host '  깔았다' -ForegroundColor Green
      } else {
        Write-Host '  ! 설치 실패 — winget 이 뱉은 끝 줄:' -ForegroundColor Red
        Show-Log $al
        $Fails.Add('Claude 데스크탑 앱')
      }
      Remove-Item $al -ErrorAction SilentlyContinue
    }
  }
} elseif ($wantApp -eq 'offsite') {
  Write-Host ''
  # ⚠ **안 깐 까닭을 정확히 댄다.** 「사내라」와 「자리를 몰라」는 다른 명제고, 뒤엣것은
  #   고칠 수 있는 것이다 — 값 파일에 `#site-probe` 를 넣으면 잰다.
  if ($site -eq 'inside') {
    Write-Host '  Claude 데스크탑 앱 — 사내라 안 깐다 (게이트웨이를 못 문다)'
  } else {
    Write-Host '  Claude 데스크탑 앱 — 자리를 몰라 안 깐다 (값 파일에 #site-probe 가 없다)'
  }
}

# ── 2″. Node 신뢰 배선 — **확장 칸보다 앞이다** ─────────────────────────────────
# ⚠ 앞에 있는 까닭: 뒤의 두 칸(확장·CLI)이 **둘 다 Node 로 내려받는다.** 뒤에 두면 이미 죽은
#   뒤에 신뢰를 잇게 되고, 그 판은 다시 돌려야 한다.
# ⚠ **`-NoUpgrade` 로 안 건너뛴다.** 이것은 올리는 일이 아니라 **서게 하는 일**이고, 비영속
#   VDI 는 로그인마다 사용자 환경변수가 새로 나서 매번 다시 심어야 한다.
Write-Host ''
Write-Host '  Node 신뢰 배선' -ForegroundColor Cyan
Wire-NodeTrust

# ── 3. VS Code 확장 — **이 스크립트가 있는 까닭** ────────────────────────────────
# ⚠ 확장만으로는 안 돈다. 확장은 Claude Code CLI 를 **자식으로 부른다** — 그래서 다음 칸이
#   붙어 있고, 둘 중 하나만 서면 VS Code 는 열리는데 아무 일도 안 일어난다.
Write-Host ''
Write-Host '[2/8] VS Code 클로드 확장' -ForegroundColor Cyan
if (Test-Runs 'code' '--version') {
  $ext = (& code --list-extensions 2>$null)
  if (($ext -contains 'anthropic.claude-code') -and $NoUpgrade) {
    Write-Host '  있음'
  } elseif ($ext -contains 'anthropic.claude-code') {
    # ⚠ `--force` 는 이미 있어도 **최신으로 다시 깐다.** 확장에는 올리는 명령이 따로 없다.
    $b = (& code --list-extensions --show-versions 2>$null |
          Where-Object { $_ -like 'anthropic.claude-code@*' } | Select-Object -First 1)
    $xl = [IO.Path]::GetTempFileName()
    Invoke-Logged 'code' @('--install-extension','anthropic.claude-code','--force') $xl | Out-Null
    Remove-Item $xl -ErrorAction SilentlyContinue
    $a = (& code --list-extensions --show-versions 2>$null |
          Where-Object { $_ -like 'anthropic.claude-code@*' } | Select-Object -First 1)
    if ($a -and $a -ne $b) { Write-Host "  올렸다  $b  ->  $a" -ForegroundColor Green }
    else { Write-Host "  최신  ($b)" }
  } else {
    $xl = [IO.Path]::GetTempFileName()
    $rc = Invoke-Logged 'code' @('--install-extension','anthropic.claude-code','--force') $xl
    # ⚠ **곧바로 물으면 아직 없을 수 있다.** VS Code 가 떠 있으면 설치가 그 인스턴스로 넘어가고
    #   명령은 바로 돌아온다 — 그때 목록을 물으면 「없다」가 나와 멀쩡한 설치가 실패로 찍힌다.
    #   몇 초를 두고 다시 묻는다. 없는 것을 오래 기다리지는 않는다.
    $ext = (& code --list-extensions 2>$null)
    if ($ext -notcontains 'anthropic.claude-code') {
      for ($i = 0; $i -lt 5; $i++) {
        Start-Sleep -Seconds 2
        $ext = (& code --list-extensions 2>$null)
        if ($ext -contains 'anthropic.claude-code') { break }
      }
    }
    if ($ext -contains 'anthropic.claude-code') {
      Write-Host '  깔았다' -ForegroundColor Green
    } else {
      # ⚠ **까닭을 편다.** 「! 설치 실패」 한 줄만 내면 다음 사람이 열어 볼 자리가 없다 —
      #   이 자리에서 실제로 그랬다(실측 2026-09-09 · 사외 VDI).
      Write-Host "  ! 설치 실패 (code 가 $rc 로 끝났다) — 뱉은 끝 줄:" -ForegroundColor Red
      Show-Log $xl
      Write-Host '     10초를 기다려도 목록에 안 떴다.'
      # ⚠ **인증서면 다른 병이다.** 「self signed certificate」 는 VS Code 의 흠이 아니라
      #   길에 TLS 를 가로채는 장비가 있는데 **Node 가 그 CA 를 모른다**는 말이다. 안 짚으면
      #   사람은 영문 오류를 들고 VS Code 를 다시 깔러 간다 — 아무 상관 없는 자리다.
      $said = (Get-Content -LiteralPath $xl -ErrorAction SilentlyContinue) -join "`n"
      if ($said -match 'self.signed certificate|unable to (verify|get local issuer)|UNABLE_TO_|CERT_') {
        Write-Host '     ↑ 인증서 문제다 — 길에 TLS 를 가로채는 장비가 있는데 Node 가 그 CA 를 모른다.' -ForegroundColor Yellow
        Write-Host '        VS Code 를 다시 깔아도 안 낫는다. 위 「Node 신뢰 배선」 칸을 먼저 본다.'
      }
      Write-Host '     VS Code 가 열려 있으면 전부 닫고 다시 눌러 본다.'
      Write-Host '     손으로 재려면:  code --install-extension anthropic.claude-code --force'
      $Fails.Add('VS Code 확장')
    }
    Remove-Item $xl -ErrorAction SilentlyContinue
  }
} else {
  Write-Host '  ! code 를 못 불러 건너뛴다 — VS Code 설치부터 본다' -ForegroundColor Red
  $Fails.Add('VS Code 확장 (code 가 안 닿는다)')
}

# ── 4. Claude Code CLI ───────────────────────────────────────────────────────────
Write-Host ''
Write-Host '[3/8] Claude Code CLI' -ForegroundColor Cyan
if ((Test-Runs 'claude' '--version') -and ($NoUpgrade -or -not (Test-Runs 'npm' '--version'))) {
  Write-Host "  있음 — $(Get-Ver 'claude' '--version')"
} elseif (Test-Runs 'claude' '--version') {
  $b = Get-Ver 'claude' '--version'
  $nl = [IO.Path]::GetTempFileName()
  Invoke-Logged 'npm' @('install','-g','@anthropic-ai/claude-code@latest') $nl | Out-Null
  Remove-Item $nl -ErrorAction SilentlyContinue
  Update-RuntimePath
  $a = Get-Ver 'claude' '--version'
  if ($a -and $a -ne $b) { Write-Host "  올렸다  $b  ->  $a" -ForegroundColor Green }
  else { Write-Host "  최신  ($b)" }
} elseif (Test-Runs 'npm' '--version') {
  $nl = [IO.Path]::GetTempFileName()
  $nrc = Invoke-Logged 'npm' @('install','-g','@anthropic-ai/claude-code') $nl
  # ⚠ **깔고 나서 한 번 더 태운다.** `%APPDATA%\npm` 은 이 설치가 **만드는** 폴더라,
  #   맨바닥 PC 에서는 앞의 배선이 조용히 지나가고 PATH 가 빈 채로 남는다. 두 번째부터는
  #   폴더가 있어 안 드러나는, 맨바닥에서만 나는 갈래다.
  Update-RuntimePath
  if (Test-Runs 'claude' '--version') {
    Write-Host "  깔았다 — $(& claude --version)" -ForegroundColor Green
  } else {
    Write-Host "  ! 설치 실패 (npm 이 $nrc 로 끝났다) — 뱉은 끝 줄:" -ForegroundColor Red
    Show-Log $nl
    $Fails.Add('Claude Code CLI')
  }
  Remove-Item $nl -ErrorAction SilentlyContinue
} else {
  Write-Host '  ! npm 이 없어 못 깐다 — Node.js 설치부터 본다' -ForegroundColor Red
  $Fails.Add('Claude Code CLI (npm 이 안 닿는다)')
}

# ── 5. 값 — 파일이 들면 읽고, 없으면 묻는다 ─────────────────────────────────────
# ⚠ **값 저장소를 가리키면 여기서 안 묻는다.** `#config-repo` 가 있다는 것은 값의 진본이
#   저쪽에 있다는 말이고, 저쪽 부트스트랩이 제 파일(`secrets.env`·`secrets.d/`)로 심는다.
#   여기서도 물으면 같은 키가 두 자리에 살아 한쪽만 낡는다 — 그 어긋남은 **조용하다**:
#   낡은 값이 심겨도 「설정된 것처럼 보이고」, 부재보다 나쁜 그 상태를 이 저장소가 이미
#   결정 0026 에서 밟았다. 그러니 가리키는 갈래에서는 묻지 말고 **넘긴다.**
Write-Host ''
Write-Host '[4/8] 키와 주소' -ForegroundColor Cyan
$fromFile  = Read-EnvFile $EnvFile
$handsOff  = [bool](Read-Directive $EnvFile 'config-repo')
if ($fromFile.Count -gt 0) { Write-Host "  install.env 가 $($fromFile.Count)개를 든다" }
if ($handsOff) { Write-Host '  값의 진본은 #config-repo 가 가리키는 저장소다 — 여기서 안 묻는다' }

# ⚠ **주소가 곧 판정이다.** 주소가 없으면 게이트웨이를 안 쓰는 자리이고, 그러면 키도 안 묻고
#   없다고 물지도 않는다 — 사외 VDI 가 그 자리다(구독 로그인으로 선다). 옛 판은 둘을 「무조건
#   필요」로 두어, 안 쓰는 자리에서도 넣으라고 하고 안 넣으면 빨갛게 끝냈다.
$useGateway = $true

# ⚠ **자리가 값보다 먼저다.** 값 파일이 사내 값을 들고 있어도, 사내에 안 닿는 자리라면 그 값은
#   여기서 쓸 것이 아니다 — 배포본은 사내용으로 뽑히므로 그 파일을 사외 PC 에서 돌리는 일이
#   실제로 난다. 그때 사내 주소를 심으면 안 닿는 곳을 가리킨 채 「설정됐다」로 보인다.
if ($probe -and -not $handsOff) {
  if ($site -eq 'inside') {
    Write-Host "  사내다 — 게이트웨이를 쓴다"
  } else {
    Write-Host "  사외다 — 게이트웨이를 안 쓴다"
    Write-Host '    구독 로그인으로 섭니다 (claude auth login)'
    $useGateway = $false
    # 값 파일이 든 사내 값을 **버린다.** 안 버리면 아래 루프가 그대로 심는다.
    foreach ($v in $Vars) { if ($v.Gateway) { $fromFile.Remove($v.Name) } }
  }
}

if (-not $handsOff -and $useGateway) {
  $u = $fromFile['ANTHROPIC_BASE_URL']
  if (-not $u -and -not $Yes) {
    Write-Host ''
    Write-Host '  게이트웨이를 씁니까?' -ForegroundColor Yellow
    Write-Host '    사내면 주소를 넣습니다. 사외면 그냥 Enter — 구독 로그인으로 섭니다.'
    Write-Host '    (끝에 /v1 을 붙이지 않습니다. CLI 가 붙입니다)'
    $u = (Read-Host '    >').Trim()
    if ($u) { $fromFile['ANTHROPIC_BASE_URL'] = $u }
  }
  if (-not $u) {
    $useGateway = $false
    Write-Host '  게이트웨이를 안 씁니다 — 구독 로그인으로 섭니다 (claude auth login)'
  }
}

foreach ($v in $Vars) {
  $val = $fromFile[$v.Name]

  # 게이트웨이를 안 쓰는 자리에서는 그쪽 이름을 아예 안 본다
  if ($v.Gateway -and -not $useGateway) { continue }

  if (-not $val -and -not $Yes -and -not $handsOff) {
    Write-Host ''
    Write-Host "  $($v.Name)" -ForegroundColor Yellow
    Write-Host "    $($v.Desc)"
    if (-not $v.Gateway) { Write-Host '    (없으면 그냥 Enter)' }
    if ($v.Secret) {
      $sec = Read-Host '    >' -AsSecureString
      $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
      $val  = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
      [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    } else {
      $val = Read-Host '    >'
    }
    if ($val) { $val = $val.Trim() }
  }

  # ⚠ **빈 값은 안 심는다.** 심으면 판정이 「있다」로 뒤집혀 부재가 조용해진다.
  if (-not $val) {
    if ($v.Gateway -and $useGateway -and -not $handsOff) {
      Write-Host "  ! $($v.Name) 이 비었다 — 이게 없으면 확장이 게이트웨이로 못 간다" -ForegroundColor Red
      $Fails.Add("$($v.Name) 미입력")
    }
    continue
  }

  Plant-Var $v.Name $val
}

# ── 5′. 값 파일이 든 나머지 이름 — **몸통이 모르는 것도 심는다** ────────────────
# ⚠ 위 표는 「물을 것」이라 회사 공통 설정을 다 들지 않는다. 파일이 실어 보낸 이름을 표에
#   있는 것만 심으면 나머지는 **조용히 버려진다** — 파일에는 있는데 기계에는 없는 그 상태가
#   제일 찾기 어렵다. 그래서 표를 안 보고 파일을 본다.
$known = $Vars | ForEach-Object { $_.Name }
foreach ($k in $fromFile.Keys) {
  if ($known -contains $k) { continue }
  $val = $fromFile[$k]
  if (-not $val) { continue }
  Plant-Var $k $val
}

# ── 6. 홈 설정 ──────────────────────────────────────────────────────────────────
# ⚠ **씨앗은 없을 때만 깐다.** 사람이 앱에서 바꾼 값을 재실행이 지우면 안 된다. 담는 것도
#   취향이 아니라 공용으로 서는 것뿐이다 — `permissions` 를 안 담는 까닭이 그것이다: 그
#   목록은 특정 저장소의 스크립트 이름을 들어, 담는 순간 이 파일이 그 저장소의 것이 된다.
#
# ⚠ **`env` 칸은 다르다 — 자리가 그러라고 하면 있는 파일에도 민다.** 사내에서는 환경변수와
#   이 파일을 둘 다 봐야 한다: 환경변수만 두면 모델 고르는 자리가 엉뚱한 값으로 서고, 파일만
#   두면 같은 변수를 읽는 다른 앱이 키를 잃는다. **사본이 아니라 파생이다** — 값의 진본은
#   `install.env` 하나고 여기로 밀려올 뿐이다.
#   어느 자리가 이것을 드나는 **값 파일이 `#settings-env` 로 든다.** 몸통은 자리 이름을 모른다.
Write-Host ''
Write-Host '[5/8] 홈 설정' -ForegroundColor Cyan
$homeDir = Join-Path $env:USERPROFILE '.claude'
$homeCfg = Join-Path $homeDir 'settings.json'
New-Item -ItemType Directory -Path $homeDir -Force | Out-Null

$cfg = $null
if (Test-Path -LiteralPath $homeCfg) {
  try {
    $cfg = Get-Content -LiteralPath $homeCfg -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Host '  있음 — 그대로 두고 필요한 것만 민다'
  } catch {
    # ⚠ **깨진 파일을 덮지 않는다.** 사람이 손댄 것이 거기 들어 있을 수 있고, 지우면
    #   무엇을 잃었는지 물을 자리가 없다. 말하고 물러난다.
    Write-Host '  ! settings.json 을 못 읽었다 (꼴이 깨졌다) — 안 건드린다' -ForegroundColor Red
    $Fails.Add('홈 settings.json 을 못 읽었다')
  }
} else {
  # ⚠ **env 를 여기 안 적는다.** 스위치의 진본은 위 `$Features` 하나이고 아래에서 늘 맞춘다 —
  #   씨앗에도 적으면 두 자리가 되고, 하나만 늘어난 날 새 기계와 헌 기계가 갈린다.
  $cfg = [pscustomobject]@{
    agentPushNotifEnabled   = $true
    inputNeededNotifEnabled = $true
  }
  Write-Host '  없어서 씨앗을 깐다'
}

if ($cfg) {
  $wantEnv = (Read-Directive $EnvFile 'settings-env') -eq 'yes'
  $dirty = $false

  # env 칸을 먼저 세운다 — 아래 둘(기능 스위치 · 게이트웨이 값)이 같은 자리에 쓴다.
  if (-not $cfg.PSObject.Properties['env']) {
    $cfg | Add-Member -NotePropertyName env -NotePropertyValue ([pscustomobject]@{}) -Force
  }

  # 클라이언트 기능 스위치 — 자리도 값 파일도 안 탄다. 없으면 넣고 다르면 맞춘다.
  $fx = 0
  foreach ($k in $Features.Keys) {
    $old = if ($cfg.env.PSObject.Properties[$k]) { $cfg.env.$k } else { $null }
    if ($old -ne $Features[$k]) {
      $cfg.env | Add-Member -NotePropertyName $k -NotePropertyValue $Features[$k] -Force
      $dirty = $true; $fx++
    }
  }
  if ($fx) { Write-Host "  기능 스위치 $fx 개를 맞췄다 ($($Features.Keys -join ' · '))" -ForegroundColor Green }

  if ($wantEnv -and $Planted.Count -gt 0) {
    foreach ($k in $Planted.Keys) {
      $old = if ($cfg.env.PSObject.Properties[$k]) { $cfg.env.$k } else { $null }
      if ($old -ne $Planted[$k]) {
        $cfg.env | Add-Member -NotePropertyName $k -NotePropertyValue $Planted[$k] -Force
        $dirty = $true
      }
    }
    Write-Host "  env 에 $($Planted.Count)개를 맞췄다 (#settings-env = yes)" -ForegroundColor Green
  } elseif (-not $wantEnv) {
    Write-Host '  env 는 안 민다 — 값 파일이 #settings-env 를 안 든다'
  }

  # ⚠ **우리가 안 심은 ANTHROPIC_ 이름이 남아 있으면 문다.** 사내 안내 문서가 손으로 적으라고
  #   하는 자리라, 옛 값이 남으면 그쪽이 이겨 방금 심은 것이 가려진다 — 화면은 「심었다」로
  #   찍히는데 안 먹는, 부재보다 나쁜 상태다. 지우지는 않는다: 사람이 뜻을 두고 넣었을 수 있다.
  # ⚠ **다만 handsOff 면 이 자를 못 댄다.** 그 판에서는 설치가 아무것도 안 심으므로
  #   ($Planted 가 빈다) 저쪽 저장소가 제대로 밀어 넣은 값까지 전부 「홀로」로 잡힌다 —
  #   구조적으로 **거짓 빨강만 나오는 자리**다. 프로필이 남는 PC 에서 매번 그랬다
  #   (실측 2026-09-09 · 사내 PC · 실패 2 건이 전부 이것이었다). 비영속 VDI 는 매 부팅
  #   settings.json 이 새것이라 안 걸려서, 이 거짓 빨강이 한 기계에서만 보였다.
  #   검증 칸이 같은 판에서 이미 비켜서는 것과 같은 갈래다 — 값의 진본이 저쪽이면 여기서 안 잰다.
  if ($handsOff) {
    Write-Host '  (settings.json 의 값은 #config-repo 가 가리키는 저장소가 든다 — 여기서 안 잰다)'
  } elseif ($cfg.PSObject.Properties['env']) {
    foreach ($p in $cfg.env.PSObject.Properties) {
      if ($p.Name -notlike 'ANTHROPIC_*') { continue }
      if ($Planted.ContainsKey($p.Name)) { continue }
      Write-Host "  ! $($p.Name) 이 settings.json 에만 있다 — 우리가 심은 값을 가릴 수 있다" -ForegroundColor Red
      Write-Host "     볼 자리: $homeCfg  (env 칸)"
      $Fails.Add("$($p.Name) 이 settings.json 에 홀로 있다")
    }
  }

  if ($dirty -or -not (Test-Path -LiteralPath $homeCfg)) {
    # ⚠ **BOM 없이 쓴다.** PowerShell 5.1 의 `Set-Content -Encoding UTF8` 은 BOM 을 붙이는데,
    #   JSON 을 읽는 쪽이 그 세 바이트에 걸릴 수 있다. 설정이 통째로 안 읽히면 고장이 조용하다.
    $json = $cfg | ConvertTo-Json -Depth 10
    [IO.File]::WriteAllText($homeCfg, $json, (New-Object Text.UTF8Encoding($false)))
    Write-Host '  썼다' -ForegroundColor Green
  } else {
    Write-Host '  이미 맞다 — 안 건드림'
  }
}

# ── 7. 개인 규범·룰·스킬 (선택) ─────────────────────────────────────────────────
# ⚠ **기본은 안 깐다.** 이것들은 한 사람의 사유 방식이라, 받는 사람이 원할 때만 선다.
#   `-WithPersonalConfig` 를 줄 때만, 그리고 이 폴더에 실제로 있을 때만 깐다.
Write-Host ''
Write-Host '[6/8] 개인 규범·룰·스킬' -ForegroundColor Cyan
if (-not $WithPersonalConfig) {
  Write-Host '  건너뜀 — 원하면 -WithPersonalConfig 로 다시 돌린다'
} else {
  $pairs = @(
    @{ From = Join-Path $Here '.claude\CLAUDE.global.md'; To = Join-Path $homeDir 'CLAUDE.md';  Name='전역 규범' }
    @{ From = Join-Path $Here '.claude\rules.global';     To = Join-Path $homeDir 'rules';       Name='영역 룰'   }
    @{ From = Join-Path $Here '.claude\skills';           To = Join-Path $homeDir 'skills';      Name='스킬'      }
    @{ From = Join-Path $Here 'agents';                   To = Join-Path $homeDir 'agents';      Name='에이전트'  }
  )
  foreach ($p in $pairs) {
    if (-not (Test-Path -LiteralPath $p.From)) { Write-Host "  $($p.Name) — 이 폴더에 없다"; continue }
    if (Test-Path -LiteralPath $p.From -PathType Container) {
      New-Item -ItemType Directory -Path $p.To -Force | Out-Null
      Copy-Item -Path (Join-Path $p.From '*') -Destination $p.To -Recurse -Force
    } else {
      Copy-Item -LiteralPath $p.From -Destination $p.To -Force
    }
    Write-Host "  $($p.Name) — 깔았다" -ForegroundColor Green
  }
}

# ── 7. 사내 환경 문서 · 씨앗 둘 ─────────────────────────────────────────────────
# ⚠ **이건 고를 것이 아니라 환경이다.** 그래서 위 칸과 달리 스위치가 없다 — 사내 게이트웨이의
#   배선·실측·오류 명세와, 복사해 출발하는 씨앗 둘(배관 · 설정 저장소)은 **누가 받아도 쓴다.**
# ⚠ 옛 판은 이것을 안 깔고 **경로만 찍었다.** 그런데 그 경로는 이 zip 이 풀린 자리였다 —
#   설정 저장소를 안 넣은 사람에게는 그것이 유일한 사본이고, 바탕화면 폴더를 지우면 사라진다.
#   게다가 스킬과 형제 저장소 문서가 가리키는 자리는 `claude-config/posco/` 인데, 저장소가
#   없는 기계에는 그 좌표가 **아예 없다** — 시키는 대로 찾으면 없는 경로를 뒤진다.
# ⚠ 그래서 홈에 깐다 — 규범·룰·스킬이 이미 쓰는 꼴이다: **진본은 저장소, 로드 자리는 홈.**
#   저장소를 든 사람은 `deploy.ps1` 이 이 자리를 갱신하고 `check-global-copies.sh` 가
#   바이트로 잰다. 사본이 하나 더 늘지만, **재는 자가 붙은 사본**이라 조용히 안 낡는다.
Write-Host ''
Write-Host '[7/8] 사내 환경 문서 · 씨앗 둘' -ForegroundColor Cyan
$envAssets = @(
  @{ From = Join-Path $Here 'posco';         To = Join-Path $homeDir 'posco'
     Name = '사내 환경 문서'; Desc = '게이트웨이·API·오류 기록 — 붙이기 전에 읽는다' }
  @{ From = Join-Path $Here 'seeds\gateway'; To = Join-Path $homeDir 'seeds\gateway'
     Name = '게이트웨이 씨앗'; Desc = '새 프로젝트가 복사해서 출발한다' }
  # ⚠ **이것도 스위치를 안 둔다.** 「설정 저장소」 칸을 쓸 사람만 보지만, **볼지 말지를 고르는
  #   때가 이 설치보다 뒤다** — 칸을 채우려면 저장소가 이미 있어야 하고, 그 저장소를 만드는
  #   골든이 이것이다. 켜는 칸으로 두면 안 켠 사람은 그 칸을 채울 길을 못 찾는다.
  @{ From = Join-Path $Here 'seeds\config-repo'; To = Join-Path $homeDir 'seeds\config-repo'
     Name = '설정 저장소 씨앗'; Desc = '「설정 저장소」 칸이 기대하는 저장소를 만드는 골든' }
)
foreach ($a in $envAssets) {
  if (-not (Test-Path -LiteralPath $a.From)) { Write-Host "  $($a.Name) — 이 폴더에 없다"; continue }
  New-Item -ItemType Directory -Path $a.To -Force | Out-Null
  Copy-Item -Path (Join-Path $a.From '*') -Destination $a.To -Recurse -Force
  Write-Host "  $($a.Name) — 깔았다" -ForegroundColor Green
  Write-Host "     $($a.To)"
  Write-Host "     $($a.Desc)"
}

# ── 8. 개인 값 저장소 (선택) ────────────────────────────────────────────────────
# ⚠ **주소는 이 파일에 없다.** `install.env` 가 `#config-repo` 를 들 때만 이 칸이 선다 —
#   그래야 이 스크립트가 익명으로 남아 남에게 그대로 줄 수 있다.
# ⚠ **이 칸은 갈래가 둘이고 둘 다 정당하다.** 규약은 파일 이름 하나 — 받아온 저장소 뿌리의
#   `bootstrap-vdi.sh`:
#     · 있으면 → 그것에 넘긴다. 그 뒤는 그 저장소가 든다
#     · 없으면 → **받아 둔 것으로 끝낸다.** 저장소를 원한 사람에게 저장소는 왔다
#   그 이름을 받는 사람에게 알리는 것은 `README.md` 가 든다.
# ⚠ **옛 판은 없는 것을 실패로 찍었다.** 「넘길 자리가 없는 것을 성공으로 읽지 않는다」가
#   까닭이었는데, 그것은 **이 칸의 목적을 「넘기기」 하나로 좁게 본 것**이다. 저장소만 들고
#   다니려는 사람에게는 clone 이 곧 목적이고, 그 사람의 성공을 빨강으로 찍으면 **멀쩡한 PC 가
#   매번 실패로 보고된다** — 빨강이 흔해지면 진짜 빨강이 안 보인다 (사용자 확정).
#   그렇다고 조용히 넘어가지도 않는다: 부트스트랩이 **왜 안 돌았나**를 그 자리에서 말한다.
# ⚠ 여기서 넘긴 뒤 저쪽이 저장소·자리·키·배포를 든다. 런타임을 두 번 깔지 않는다 —
#   저쪽 런타임 칸은 **확인만** 하고, 무엇을 깔지는 이 파일 하나가 든다.
Write-Host ''
Write-Host '[8/8] 개인 값 저장소' -ForegroundColor Cyan
# ⚠ **밖에서 선언한다.** 이 칸이 통째로 안 도는 갈래(git 이 없다 · 주소가 없다)가 있고,
#   아래 검증이 이 값을 읽는다 — 안 선언하면 그 자리에서 「없는 변수」가 거짓으로 읽힌다.
$handedOff = $false
$repoUrl = Read-Directive $EnvFile 'config-repo'
if (-not $repoUrl) {
  Write-Host '  건너뜀 — install.env 에 #config-repo 가 없다'
} elseif (-not (Test-Runs 'git' '--version')) {
  Write-Host '  ! git 이 안 닿아 못 받는다' -ForegroundColor Red
  $Fails.Add('개인 값 저장소 (git 이 안 닿는다)')
} else {
  # ⚠ **자리를 고르는 칸을 두지 않는다.** 옛 판은 `#config-root` 를 읽었는데, **읽는 자가
  #   여기 하나뿐이었다** — 넘겨받는 `bootstrap-vdi.sh` 는 `$HOME/repos` 를 제 몸통에 박고
  #   그 칸을 안 본다. 그래서 그것을 쓰면 설치는 지정한 데로 clone 하고 부트스트랩은
  #   `~/repos` 로 형제 저장소를 받은 뒤, 거기 없는 `~/repos/claude-config/deploy.ps1` 을
  #   찾다 죽는다. **쓰는 순간 저장소가 두 갈래로 갈리는 칸**이라 걷어냈다 —
  #   문서에도 없어서 아무도 모르는 채로 있었다.
  #   자리를 바꿔야 하면 고칠 자리는 둘이다: 여기와 저쪽 `ROOT`. 한쪽만 고치면 안 선다.
  $root = Join-Path $env:USERPROFILE 'repos'
  New-Item -ItemType Directory -Path $root -Force | Out-Null

  # ⚠ **여러 개를 빈칸으로 가른다.** 옛 판은 하나만 받았고, 그 까닭은 「나머지는 그 저장소의
  #   부트스트랩이 데려온다」였다 — 그런데 그건 **만든 사람의 부트스트랩 사정**이지 받는
  #   사람의 사정이 아니다. 남은 목록의 진본이 제 저장소에 없으면 여기 적을 수밖에 없다.
  #   주소에는 빈칸이 없으므로 가르는 자로 빈칸이 안전하다.
  $repoUrls = @($repoUrl -split '\s+' | Where-Object { $_ })

  # ⚠ **받은 것과 넘길 자리가 있는 것은 다른 명제다.** 옛 판은 clone 의 실패를 `2>$null` 과
  #   빈 `catch` 로 삼키고, 그 결과를 아래에서 **「저장소에 bootstrap-vdi.sh 가 없다」**로 냈다.
  #   그런데 계정이 없거나 인증이 거부됐거나 주소가 틀렸어도 같은 문구가 나온다 — 저장소는
  #   받아진 적조차 없는데 **사람은 없는 파일을 찾아 그 저장소를 뒤진다.** 부재를 엉뚱한
  #   이름으로 보고하는 자리라 걷었다.
  # ⚠ 까닭은 git 이 이미 말하고 있었다. 버리지 말고 **파일에 잡아 실패할 때만 편다** —
  #   위 규율 그대로다(합치면 `Stop` 이 던지고, 버리면 단서가 사라진다).
  # ⚠ **하나가 져도 나머지를 계속 받는다.** 여럿을 준 사람에게 첫 실패로 멈추면, 성한
  #   저장소까지 못 받고 까닭도 하나만 본다.
  $got = @()
  foreach ($u in $repoUrls) {
    $dest = Join-Path $root ([IO.Path]::GetFileNameWithoutExtension($u))
    $log = [IO.Path]::GetTempFileName()
    if (Test-Path -LiteralPath (Join-Path $dest '.git')) {
      Write-Host "  있음 — pull ($dest)"
      $rc = Invoke-Logged 'git' @('-C', $dest, 'pull', '--ff-only') $log
      # ⚠ **pull 이 져도 실패로 세지 않는다.** 저장소는 이미 있어 넘길 자리가 살아 있다 —
      #   망이 끊긴 VDI 에서 옛 판으로라도 부트스트랩이 도는 것이 안 도는 것보다 낫다.
      #   다만 조용히 넘어가지는 않는다: 옛 판으로 간다는 사실을 말한다.
      $got += $dest
      if ($rc -ne 0) {
        Write-Host '  ! pull 이 졌다 — 이미 받아 둔 판으로 넘긴다' -ForegroundColor Yellow
        Show-Log $log
      }
    } else {
      Write-Host "  clone ($dest)"
      # ⚠ **이 안내를 우리가 찍는다.** 자격 관리자가 뱉는 「브라우저에서 마치라」는 줄은 위
      #   `Invoke-Logged` 가 파일로 잡아 화면에 안 나온다 — 안 찍으면 사람은 창이 왜 떴는지
      #   모른 채 기다리고, 그 사이 설치가 멈춘 것처럼 보인다.
      Write-Host '    GitHub 로그인 창이 뜰 수 있습니다 — 브라우저에서 눌러 주세요' -ForegroundColor Yellow
      $rc = Invoke-Logged 'git' @('clone', $u, $dest) $log
      # ⚠ **종료코드만 믿지 않는다.** 0 으로 끝났는데 자리가 안 선 판을 재는 자가 여기다.
      if ($rc -eq 0 -and (Test-Path -LiteralPath (Join-Path $dest '.git'))) {
        $got += $dest
      } else {
        Write-Host "  ! 못 받았다 — 주소 · 계정 · 망을 본다  ($u)" -ForegroundColor Red
        Show-Log $log
        $Fails.Add("개인 값 저장소 (못 받았다: $u)")
      }
    }
    Remove-Item $log -ErrorAction SilentlyContinue
  }

  # ⚠ **Git Bash 로 부른다.** 저쪽은 bash 몸통이고, PowerShell 에서 직접 못 부른다.
  $bash = @("$env:ProgramFiles\Git\bin\bash.exe",
            "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe") |
          Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

  # ⚠ **넘길 자리를 순서로 정하지 않고 찾는다.** 「첫째가 설정 저장소」 같은 규칙을 두면
  #   사람이 그 순서를 기억해야 하고, 기억해야 하는 것은 그 순간에 안 걸린다. 받아 온
  #   것들 중 **그 이름의 파일을 든 첫 저장소**가 넘길 자리다.
  # ⚠ **여럿이 들고 있으면 하나만 부르고 나머지를 이름으로 말한다.** 둘을 잇달아 부르면
  #   뒤엣것이 앞엣것의 키·설정을 덮는데 그 순서는 사람이 정한 것이 아니다.
  $bootRepos = @($got | Where-Object { Test-Path -LiteralPath (Join-Path $_ 'bootstrap-vdi.sh') })
  $dest = $bootRepos | Select-Object -First 1
  $boot = if ($dest) { Join-Path $dest 'bootstrap-vdi.sh' } else { $null }

  if (-not $got) {
    # ⚠ 실패는 위에서 까닭을 대고 이미 셌다 — 여기서 또 세면 **한 사고가 둘로 보고된다.**
    #   대신 사슬이 왜 끊겼는지는 말한다: 안 말하면 부트스트랩이 돈 줄 알 수 있다.
    Write-Host '  넘길 자리가 없어 부트스트랩을 안 부른다'
  } elseif (-not $boot) {
    # ⚠ **실패가 아니다.** 저장소는 왔고(위에서 재고 왔다) 그것이 목적인 사람이 있다.
    #   대신 **안 돈 것을 이름으로 말한다** — 부트스트랩을 기대한 사람이 조용히 속지 않게.
    Write-Host "  받아 뒀다 — $($got.Count)개" -ForegroundColor Green
    $got | ForEach-Object { Write-Host "     $_" }
    Write-Host '    어느 뿌리에도 bootstrap-vdi.sh 가 없어 부트스트랩은 안 돌았다.'
    Write-Host '    자동화까지 원하면 ~/.claude/seeds/config-repo/ 를 복사해 그 이름으로 둔다.'
  } elseif (-not $bash) {
    Write-Host '  ! Git Bash 를 못 찾았다' -ForegroundColor Red
    $Fails.Add('개인 값 저장소 (Git Bash 가 없다)')
  } else {
    if ($got.Count -gt 1) {
      Write-Host "  받아 뒀다 — $($got.Count)개" -ForegroundColor Green
      $got | ForEach-Object { Write-Host "     $_" }
    }
    if ($bootRepos.Count -gt 1) {
      Write-Host "  ! bootstrap-vdi.sh 를 든 저장소가 $($bootRepos.Count)개다 — 첫 것만 부른다" -ForegroundColor Yellow
      $bootRepos | Select-Object -Skip 1 | ForEach-Object { Write-Host "     안 부른 것: $_" }
    }
    Write-Host "  부트스트랩으로 넘긴다 — $dest" -ForegroundColor Green
    Write-Host ''
    & $bash ($boot -replace '\\','/')
    # ⚠ **판정을 여기서 세운다.** 아래 검증이 「키를 저쪽이 든다」로 넘어가려면 저쪽이
    #   실제로 돌았어야 한다 — 주소를 넣었다는 사실만으로는 아무것도 안 선다.
    $handedOff = $true
    if ($LASTEXITCODE -ne 0) { $Fails.Add("부트스트랩 (exit $LASTEXITCODE)") }
  }
}

# ── 검증 — **재고 나서 말한다** ─────────────────────────────────────────────────
# ⚠ 안 재고 「됐다」로 끝내면 안 선 기계도 성공으로 보고된다. 부재가 통과로 읽히는 것을
#   막는 것이 이 스크립트의 규율이라, 마지막 칸이 그것을 든다.
# ⚠ 환경변수는 **레지스트리에서** 읽는다 — 이 창의 값은 방금 우리가 넣은 것이라 심겼는지를
#   못 잰다. 새 창이 볼 자리를 봐야 판정이 참이 된다.
Write-Host ''
Write-Host '=== 검증 ===' -ForegroundColor Cyan
$planted = [Environment]::GetEnvironmentVariables('User')
# 한 번만 잰다 — 같은 물음을 두 번 물으면 두 답이 갈릴 자리가 나고, 아래 「연다」 칸도 이 값을 쓴다.
$hasCode = Test-Runs 'code' '--version'
$checks = @(
  @{ Name='VS Code';          Ok = $hasCode }
  @{ Name='클로드 확장';      Ok = ($hasCode -and ((& code --list-extensions 2>$null) -contains 'anthropic.claude-code')) }
  @{ Name='Claude Code CLI';  Ok = (Test-Runs 'claude' '--version') }
)
# ⚠ **폴더가 있나로 묻지 않는다.** `New-Item` 이 먼저 도니 복사가 실패해도 폴더는 남는다 —
#   빈 폴더를 [O] 로 찍으면 「깔렸는데 안 든 것」이 성공으로 보고된다. 그래서 **동봉본과
#   견준다**: 홈 사본의 파일 수가 원본보다 적으면 [X] 다.
foreach ($a in $envAssets) {
  if (-not (Test-Path -LiteralPath $a.From)) { continue }
  $srcN = @(Get-ChildItem -LiteralPath $a.From -Recurse -File -ErrorAction SilentlyContinue).Count
  $dstN = 0
  if (Test-Path -LiteralPath $a.To) {
    $dstN = @(Get-ChildItem -LiteralPath $a.To -Recurse -File -ErrorAction SilentlyContinue).Count
  }
  $checks += @{ Name = "$($a.Name) ($dstN/$srcN)"; Ok = ($srcN -gt 0 -and $dstN -ge $srcN) }
}
# ⚠ **안 쓰기로 한 것을 [X] 로 찍지 않는다.** 그러면 멀쩡한 사외 PC 가 매번 빨갛게 보고되고,
#   빨강이 흔해지면 진짜 빨강이 안 보인다.
# ⚠ **「넘겼다」가 아니라 「넘어갔다」로 가른다.** 옛 판은 `$handsOff`(= 주소를 넣었나)만 보고
#   키 검사를 통째로 건너뛰었다. 그런데 저장소 뿌리에 부트스트랩이 없으면 **아무것도 안 넘어가고**
#   위 칸도 키를 안 물어, **키가 어디에도 안 심긴 채 초록으로 끝난다** — 부재가 통과로 읽히는
#   바로 그 자리다. 「받아 두기만 하는 것도 정당한 결과」로 갈래를 넓히면서 난 구멍이다.
#   그래서 **부트스트랩이 실제로 돌았을 때만** 저쪽에 맡긴다.
if ($handsOff -and $handedOff) {
  Write-Host '  (키와 주소는 넘겨받은 저장소가 든다 — 여기서 안 잰다)'
} elseif ($handsOff -and -not $handedOff) {
  Write-Host '  ! 저장소를 넣었지만 부트스트랩이 안 돌아, 키를 심은 자가 없다' -ForegroundColor Red
  Write-Host '    저장소 뿌리에 bootstrap-vdi.sh 를 두거나, 칸을 비우고 다시 눌러 키를 직접 넣는다.'
  $Fails.Add('키 (넘겨받을 자가 없었다)')
} elseif ($useGateway) {
  foreach ($v in $Vars) {
    if (-not $v.Gateway) { continue }
    $checks += @{ Name = $v.Name; Ok = [bool]$planted[$v.Name] }
  }
} else {
  Write-Host '  (게이트웨이를 안 쓴다 — 구독 로그인으로 선다)'
}
foreach ($c in $checks) {
  if ($c.Ok) { Write-Host "  [O] $($c.Name)" -ForegroundColor Green }
  else       { Write-Host "  [X] $($c.Name)" -ForegroundColor Red }
}

# ⚠ 옛 판은 여기서 **동봉 자산의 경로만 찍었다**(`posco/` · `seeds/gateway/`). 이제 그 둘은
#   7 칸이 홈에 깔고 검증도 아래가 든다 — 찍기만 하는 자리를 남겨 두면 zip 폴더를 가리키는
#   낡은 좌표가 하나 더 산다.

Write-Host ''
if ($Fails.Count -gt 0) {
  Write-Host "끝내지 못했다 — $($Fails.Count)개가 남았다:" -ForegroundColor Red
  $Fails | ForEach-Object { Write-Host "  - $_" }
  if ($noWinget) {
    Write-Host ''
    Write-Host '  winget 이 없어 못 깐 것은 IT 에 이름을 대고 요청한다:' -ForegroundColor Yellow
    Write-Host '    Microsoft Store 의 "앱 설치 관리자"(App Installer) — 그것이 winget 이다.'
    Write-Host '    또는 모자란 프로그램을 직접 (VS Code · Node.js · Git · Python).'
    Write-Host '    ※ 재등록 · PowerShell 모듈 · GitHub 내려받기를 이미 다 시도했다 —'
    Write-Host '       위 · 줄이 각각 무엇에 걸렸는지 든다.'
  }
  Write-Host ''
}
if (-not $WithPersonalConfig) {
  Write-Host '  개인 규범·룰·스킬까지 원하면:  .\install.ps1 -WithPersonalConfig'
  Write-Host ''
}

# ── 연다 — **자리가 정한 것을, 이 창의 자식으로** ───────────────────────────────
# ⚠ 「재시작할 것」만으로는 모자랐다. 창은 뜰 때 PATH 와 환경변수를 **한 번 복사**하고 그 뒤에
#   바뀐 것은 안 따라온다 — 그래서 안내로 끝내지 않고 여기서 띄운다. 이 창은 심은 값을 제
#   프로세스에도 같이 들고 있어(`Plant-Var`), 여기서 난 자식은 **로그아웃 없이** 그 값을 문다.
# ⚠ **앞문을 정하는 잣대는 「자리」다 — `$offsite` 하나.** 사내는 게이트웨이라 그 주소로 말이
#   통하는 것이 확장·CLI 뿐이라 **VS Code** 이고, 사외는 구독 로그인이라 **데스크탑 앱**이
#   앞문이다. 자리를 모르면 잰 적이 없다는 뜻이라 데스크탑도 안 깔렸으므로 VS Code 로 간다.
#   **위 2′ 칸이 데스크탑을 깔지 가른 잣대가 바로 이것이다** — 깔 때 쓴 자로 열어야 둘이 안 어긋난다.
# ⚠ **`$useGateway` 를 쓰면 안 된다 — 그 값은 자리가 아니다.** 옛 판이 그걸 썼다가 졌다:
#   값 저장소로 넘기는 갈래(`#config-repo`)에서는 자리를 재는 블록을 통째로 건너뛰므로
#   **사외인데도 `$useGateway` 가 참으로 남는다.** 그 값의 뜻은 「키를 저쪽이 든다」이지
#   「사내다」가 아니다. 실측 2026-09-11(집 PC): `자리 = 사외` 와 `데스크탑 앱 · 있음` 이 나란히
#   찍힌 판에서 VS Code 가 떴다 — **한 판정을 두 자가 다르게 읽은 자리다.**
#   데스크탑이 안 깔린 자리(값 파일에 `#desktop-app` 이 없다)는 VS Code 로 떨어진다 —
#   없는 것을 열려다 빈손으로 끝내지 않는다.
# ⚠ **못 열어도 실패로 안 센다.** 설치는 이미 선 것이고 창은 사람이 손으로도 연다. 여기서
#   `$Fails` 를 불리면 멀쩡히 깔린 기계가 빨갛게 보고된다.

# ⚠ **찾는 자는 「무엇을」이 아니라 「어떻게 띄우나」를 돌려준다.** 둘이 진짜로 다른 기전이라
#   그렇다 — VS Code 는 실행 파일을 직접 띄워야 **이 창이 방금 심은 값을 물고** 뜨고, 데스크탑은
#   띄울 실행 파일이 아예 없다. 그래서 `Exe` 를 든 것과 `AppId` 를 든 것이 갈려 나온다.
#   `Proc` 는 「이미 떠 있나」를 재는 이름이고, **둘 다 제가 든 손잡이에서 판다.**

# VS Code — PATH 에 걸린 `code` 는 `…\bin\code.cmd` 라 그것을 띄우면 콘솔이 한 번 번쩍인다.
# 한 층 올라가 실행 파일을 판다.
# ⚠ **자리를 여기 안 적는다.** 적으면 위 배선(`Update-RuntimePath`)이 든 목록과 사본이 둘
#   되고 한쪽만 낡는다. 부르는 쪽이 `$hasCode`(= `code` 가 실제로 돌더라)일 때만 여기 오므로,
#   PATH 에서 못 파는 갈래는 **도달할 수 없는 길**이다 — 옛 판이 그 자리에 박아 두었던 경로 둘을
#   걷었다.
function Find-VSCode {
  $c = Get-Command code -ErrorAction SilentlyContinue
  if (-not $c -or -not $c.Source) { return $null }
  # ⚠ **빈 것을 `Join-Path` 에 넘기지 않는다** — 위 `Stop` 이 그 자리에서 던지는데, 여기는
  #   설치의 마지막 칸이라 **종료코드째 날아간다.** 멀쩡히 끝난 설치가 실패로 보고된다.
  $vsRoot = Split-Path (Split-Path $c.Source -Parent) -Parent
  if (-not $vsRoot) { return $null }
  $exe = Join-Path $vsRoot 'Code.exe'
  if (-not (Test-Path -LiteralPath $exe)) { return $null }
  return @{ Name = 'VS Code'; Exe = $exe
            Proc = [IO.Path]::GetFileNameWithoutExtension($exe) }
}

# 데스크탑 앱 — **자리를 묻지 않고 윈도우에 앱을 묻는다.**
# ⚠ **경로로 찾는 길은 막혀 있다.** 이 앱은 스토어 꼴(MSIX)로 깔릴 수 있고, 그러면 실행 파일도
#   `Uninstall` 등록 정보도 시작 메뉴 `.lnk` 도 **하나도 안 생긴다.** 실측 2026-09-11(집 PC):
#   그 셋이 다 빈손인데 winget 은 「있음」이었고, 경로를 훑던 옛 판이 빈손으로 돌아와 **말없이
#   VS Code 를 열었다.** 실물은 `Program Files\WindowsApps\...` 인데 그 자리는 권한으로 막혀
#   훑어도 못 본다.
# ⚠ **그러니 자리를 하나 더 박는 것은 답이 아니다** — 꼴이 바뀌면 또 어긋난다. `Get-StartApps`
#   는 **띄울 수 있는 앱과 그 손잡이**를 돌려주고, 스토어 꼴이든 예전 꼴이든 같은 답을 낸다.
# ⚠ **찾을 이름도 안 박는다** — 위 `$DesktopApp` 에서 판다.
function Find-ClaudeApp {
  $want = ($DesktopApp -split '\.')[-1]        # `만든이.앱` → `앱`
  try {
    $a = @(Get-StartApps -ErrorAction Stop |
           Where-Object { $_.Name -like "*$want*" })[0]
  } catch { return $null }                      # 이 윈도우에 그 물음이 없다
  if (-not $a -or -not $a.AppID) { return $null }
  # 프로세스 이름도 손잡이에서 판다. 스토어 꼴은 `앱_해시!앱` 이라 `_` 앞이 이름이고,
  # 예전 꼴은 바로가기 경로라 파일 이름이 그 자리다.
  $proc = if ($a.AppID -match '!') { ($a.AppID -split '_')[0] }
          else { [IO.Path]::GetFileNameWithoutExtension($a.AppID) }
  return @{ Name = 'Claude 데스크탑'; AppId = $a.AppID; Proc = $proc }
}

# 그 앱이 이미 도나 — 이름은 찾는 자가 제 손잡이에서 판 것을 그대로 쓴다.
function Test-AppUp($App) {
  if (-not $App -or -not $App.Proc) { return $false }
  return [bool](Get-Process -Name $App.Proc -ErrorAction SilentlyContinue)
}

# 끌지 사람에게 묻는다.
# ⚠ **이 창에는 콘솔이 없다.** 화면 껍데기가 `CreateNoWindow` 로 띄우고 표준입력을 NUL 로
#   돌리므로 `Read-Host` 가 못 선다 — 물어도 아무도 못 답한다. 그래서 GUI 로 묻는다.
# ⚠ **임자를 세워 준다.** 임자 없는 물음창은 설치 창 **뒤로 갈 수 있고**, 그러면 설치가
#   멈춘 것처럼 보인다 — 안 보이는 창을 아무도 안 눌러 영영 안 끝난다.
function Ask-Restart([string]$AppName) {
  Add-Type -AssemblyName System.Windows.Forms
  $owner = New-Object Windows.Forms.Form
  $owner.TopMost = $true
  try {
    $msg = "$AppName — 이미 돌고 있습니다.`n`n" +
           "지금 껐다 새로 열까요?`n" +
           "돌던 것은 방금 깔린 것(키 · MCP 서버 · 세션 훅)을 모릅니다.`n`n" +
           "저장 안 한 것이 있으면 먼저 저장하고 눌러 주세요."
    return ([Windows.Forms.MessageBox]::Show(
      $owner, $msg, 'Claude Code 설치', 'YesNo', 'Warning') -eq 'Yes')
  } finally { $owner.Dispose() }
}

# 끈다 — **곱게 먼저, 안 나가면 세게.**
# ⚠ **곱게가 먼저인 까닭** — VS Code 는 창을 닫으라 하면 저장을 묻고, 사람이 답하면 스스로
#   나간다. 처음부터 죽이면 그 물음이 안 뜬다.
# ⚠ **세게가 있는 까닭** — 데스크탑은 창을 닫아도 **트레이로 내려갈 뿐 안 나간다.**
#   곱게만 두면 「껐다」가 거짓이 되고, 그 위에서 「새로 띄웠다」가 또 거짓이 된다.
# ⚠ **이름이 같은 자식들까지 다 든다.** 둘 다 여럿으로 돈다 — VS Code 는 창·확장·GPU 가
#   다 `Code.exe` 이고, 데스크탑도 프로세스 셋이 같은 이름으로 떠 있었다(실측 2026-09-11).
#   하나만 닫으면 남은 것이 살아 「아직 돈다」로 읽힌다.
function Stop-App($App) {
  foreach ($p in @(Get-Process -Name $App.Proc -ErrorAction SilentlyContinue)) {
    if ($p.MainWindowHandle -ne 0) { $null = $p.CloseMainWindow() }
  }
  # 5초까지 기다리되 나가면 바로 넘어간다 — 안 기다려도 될 때 기다리지 않는다.
  for ($i = 0; $i -lt 10 -and (Test-AppUp $App); $i++) { Start-Sleep -Milliseconds 500 }
  foreach ($p in @(Get-Process -Name $App.Proc -ErrorAction SilentlyContinue)) {
    try { $p.Kill() } catch { }
  }
  for ($i = 0; $i -lt 6 -and (Test-AppUp $App); $i++) { Start-Sleep -Milliseconds 500 }
  return (-not (Test-AppUp $App))
}

# ⚠ **마지막 한 줄은 `=== 끝 ===` 이 든다.** 화면 껍데기의 완료 문구가 이 줄에서 난다 — 저쪽에
#   같은 문장을 또 적으면 갈래가 늘 때마다 한쪽만 낡는다. 갈래마다 할 말이 다른 자리라 더 그렇다.
# ⚠ **이 줄만 사람에게 건네는 말이다.** 위는 다 기록이라 「…했다」로 적혔지만, 여기는 끝에서
#   사람을 보고 하는 말이라 말투가 갈린다. 화면 껍데기가 이것을 그대로 띄우는 것도 같은 까닭이다.
$tail = if ($offsite) {
  '구독 로그인으로 섭니다 — Claude 데스크탑이나 VS Code 를 새로 여세요'
} else {
  '열려 있는 VS Code 를 전부 닫고 새로 여세요 — 낡은 창은 방금 심은 키를 못 봅니다'
}

# ⚠ **이 칸은 무엇을 던져도 설치를 못 끝낸다.** 위 `Stop` 아래에서 한 줄이 던지면 마지막
#   `exit` 까지 못 가고, 화면 껍데기는 종료코드를 못 읽어 **멀쩡한 설치를 빨갛게** 낸다.
#   창을 여는 것은 덤이지 설치의 성패가 아니라, 여기서 진 것은 여기서 삼킨다.
try {

if ($NoLaunch) {
  Write-Host '  창은 안 띄운다 (-NoLaunch)'
} else {
  # ⚠ **우리가 심은 자가 아닌 갈래가 있다.** 값 저장소로 넘긴 판에서는 부트스트랩이 심었고
  #   그 값은 **레지스트리에만** 있다 — 이 창의 환경에는 없다. 그대로 자식을 내면 우리가
  #   **낡은 환경을 물려주는** 꼴이 되어, 사람이 탐색기에서 직접 여는 것보다 나빠진다.
  #   그래서 띄우기 직전에 **새 창이 볼 자리**를 이 창으로 당긴다 — 검증 칸이 이미 읽어 둔
  #   값이고, 부트스트랩이 끝난 뒤에 읽은 것이라 저쪽이 심은 것까지 든다.
  # ⚠ **PATH 만은 안 당긴다.** 그 이름은 기계 값과 사용자 값이 합쳐져 서는 자리라, 사용자
  #   쪽만 덮으면 이 창이 여태 태운 배선(`Update-RuntimePath`)이 통째로 날아간다.
  foreach ($k in $planted.Keys) {
    if ($k -ieq 'PATH') { continue }
    [Environment]::SetEnvironmentVariable($k, $planted[$k], 'Process')
  }

  $app = $null
  if ($offsite) {
    $app = Find-ClaudeApp
    # ⚠ **못 찾은 것을 말없이 딴 것으로 갈음하지 않는다.** 사외에서 앞문은 데스크탑이다 —
    #   못 찾았다고 조용히 VS Code 를 열면 사람은 「왜 VS Code 가 뜨지」를 혼자 헤맨다.
    #   실측 2026-09-11(집 PC): 한 줄도 안 찍힌 채 VS Code 가 떴고, 까닭을 찾는 데 몇 판이 들었다.
    #   **떨어지더라도 왜 떨어졌는지 찍고 떨어진다.**
    if (-not $app) {
      Write-Host '  ! Claude 데스크탑을 못 찾았다 — 시작 메뉴에서 직접 연다' -ForegroundColor Yellow
    }
  }
  if (-not $app -and $hasCode) { $app = Find-VSCode }

  $go = $false
  if (-not $app) {
    Write-Host '  ! 열 것을 못 찾았다 — 시작 메뉴에서 직접 연다' -ForegroundColor Yellow
  } elseif (Test-AppUp $app) {
    # ⚠ **떠 있으면 안 띄운다 — 둘 다.** 까닭이 둘이고, 둘 다 「돌던 것은 뒤에 온 것을
    #   모른다」다.
    #   · **환경** — 창은 뜰 때 환경을 한 번 복사하고 그 뒤에 바뀐 것은 안 따라온다.
    #     VS Code 는 `code` 를 다시 불러도 **돌던 그 프로세스**가 창을 내므로 방금 심은 키를
    #     못 본다. `--new-window` 도 창만 새로 낼 뿐 프로세스를 안 가르고, 가르는 레버인
    #     `--user-data-dir` 는 설정·상태가 통째로 딴 자리가 되어 처음 깐 것처럼 뜬다 —
    #     키 하나 물리자고 치를 값이 아니다.
    #   · **선언** — **이 설치가 끝이 아니다.** 뒤이어 부트스트랩이 `deploy.ps1` 을 부르고
    #     거기서 MCP 서버가 등록되고 세션 훅이 심긴다. 돌던 앱은 그 선언을 **뜰 때 한 번 읽고
    #     말았다.** 그래서 데스크탑도 닫을 까닭이 선다 — 게이트웨이 주소를 안 읽는 것과는
    #     다른 축이다.
    # ⚠ **그래서 창을 앞으로 불러 주지도 않는다.** 트레이에 내려간 것을 다시 띄우면 창이
    #   새로 뜬 것처럼 보이는데 **안에 든 것은 그대로다** — 재시작한 것처럼 보이는 것이
    #   재시작 안 한 것보다 나쁘다. 안 띄우는 대신 **어떻게 끄는지를 댄다.**
    # ⚠ **떠 있는 것을 설치가 죽이지 않는다** — 저장 안 한 것이 날아간다. 끄는 것은 사람이 든다.
    Write-Host "  $($app.Name) — 이미 떠 있다. 끌지 묻는다"
    # 사람이 아니라고 했거나 안 꺼졌을 때 낼 말. 한 번 세워 두고 두 갈래가 나눠 쓴다.
    $tail = if ($app.Name -eq 'VS Code') {
      '열려 있는 VS Code 를 전부 닫고 새로 여세요 — 돌던 창은 방금 깔린 것을 모릅니다'
    } else {
      "$($app.Name)을 트레이(시계 옆)에서 완전히 끄고 새로 여세요 — 창만 닫으면 안 꺼집니다"
    }
    if (Ask-Restart $app.Name) {
      Write-Host '  끈다 — 창을 닫으라고 보내고, 안 나가면 세게 끝낸다'
      if (Stop-App $app) {
        Write-Host "  $($app.Name) — 껐다" -ForegroundColor Green
        $go = $true
      } else {
        # ⚠ **못 껐으면 「껐다」로 안 넘어간다.** 안 끄고 띄우면 돌던 그 프로세스가 창을
        #   내므로, 사람은 재시작한 줄 알고 낡은 것을 그대로 쓰게 된다.
        Write-Host "  ! 안 꺼졌다 — 직접 끄고 연다" -ForegroundColor Yellow
      }
    } else {
      Write-Host '  안 끈다고 했다 — 안 띄운다'
    }
  } else {
    $go = $true
  }

  if ($go) {
    # ⚠ **띄우기 전에 한 박자 둔다.** 새 창은 설치 창을 덮으므로, 바로 띄우면 위 검증 칸의
    #   `[O]/[X]` 를 아무도 못 읽고 지나간다 — 그 판정이 이 설치의 결론인데 그렇다.
    Write-Host '  3초 뒤에 엽니다 — 위 검증 칸을 먼저 읽는다' -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    # ⚠ **`Start-Process` 로 띄운다.** 이 창의 나가는 손잡이는 화면 껍데기가 따라 읽는 파일로
    #   돌려져 있어, 그것을 물려주면 자식이 그 파일을 붙들고 껍데기의 뒷정리가 막힌다.
    #   `Start-Process` 는 껍데기 실행이라 손잡이를 안 물려주고 **환경은 물려준다** — 방금 심은
    #   값이 그 길로 간다. `-Wait` 는 안 건다: 걸면 사람이 그 창을 닫을 때까지 설치가 안 끝난다.
    try {
      # ⚠ **띄우는 길이 둘이다.** 실행 파일이 있으면 **이 창의 자식으로** 띄운다 — 그래야
      #   방금 심은 값을 물고 뜬다. 없으면(스토어 꼴) 앱 손잡이로 껍데기에 맡긴다. 그 길은
      #   이 창의 환경이 안 가지만, 그렇게 뜨는 앱은 그 값을 안 읽으므로 잃는 것이 없다.
      if ($app.Exe) { Start-Process -FilePath $app.Exe | Out-Null }
      else          { Start-Process "shell:AppsFolder\$($app.AppId)" | Out-Null }
      Write-Host "  $($app.Name) — 띄웠다" -ForegroundColor Green
      # ⚠ **이름 뒤에 조사를 붙일 때 갈래를 본다.** 「데스크탑이」는 붙여 쓰고 「VS Code 를」은
      #   띄어 쓴다 — 받침도 띄어쓰기도 이름마다 갈린다. 한 틀에 두 이름을 밀어 넣으면 둘 중
      #   하나가 반드시 어긋나고, 그 어긋남은 사람이 마지막에 읽는 한 줄에서 난다.
      $tail = if ($app.Name -eq 'VS Code') {
        'VS Code 를 열었습니다 — Ctrl+Shift+P → Claude 로 확장을 엽니다'
      } else {
        "$($app.Name)을 열었습니다 — 처음이면 구독 계정으로 로그인합니다"
      }
    } catch {
      # 조사를 안 붙인다 — 여기는 이름 둘이 다 지나는 자리다.
      Write-Host "  ! 못 띄웠다 ($($app.Name)) — $(Say-Why $_)" -ForegroundColor Yellow
    }
  }
}

} catch {
  Write-Host "  ! 여는 자리에서 졌다 — $(Say-Why $_)" -ForegroundColor Yellow
}

Write-Host ''
Write-Host "=== 끝 === $tail" -ForegroundColor Yellow
Write-Host ''
if ($Fails.Count -gt 0) { exit 1 }
