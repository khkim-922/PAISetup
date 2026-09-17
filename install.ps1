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
#   그 파일이 `#config-repo` 를 들면 **다 세운 뒤에** 그 저장소를 받고, 뿌리에 훅
#   (`.claude/hooks/session-start.sh`)이 있으면 `--install` 로 부른다 — 사람에게 딸린 것
#   (git 신원 · 형제 저장소 · 개인 키 · 배포)은 그쪽이 든다. 여기가 하는 일은 그 줄이
#   있든 없든 같다.
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
# ⚠ `-Describe` — **아무것도 안 깔고 고를 목록만 내주고 나간다.** 화면 껍데기가 칸을 지으려면
#   목록이 필요한데, 저쪽에 옮겨 적으면 제품이 늘 때 한쪽만 고쳐진다 — 그 어긋남은 「골랐는데
#   안 깔린다」는 조용한 꼴로만 보인다. 목록의 진본은 아래 `$Products` 하나다.
# ⚠ `-Pick claude,codex` — **고른 제품만 깐다**(안 주면 `$Products` 표의 기본값). `-NoVsCode` 는
#   VS Code 자체와 확장을 통째로 건너뛴다 — 데스크탑 앱만 쓸 사람의 자리다.
param([switch]$Yes, [switch]$NoDevTools, [switch]$WithPersonalConfig, [switch]$NoUpgrade,
      [switch]$NoLaunch, [string]$EnvFile, [switch]$Describe,
      [string]$Pick, [switch]$NoVsCode)

$ErrorActionPreference = 'Stop'

# ── 걸음마다 든 초를 잰다 — **훅이 서기 전의 시간은 여기서만 갈린다** ────────────
# ⚠ **머리줄(`[n/8]`)은 한 글자도 안 건드린다.** 화면 껍데기가 그 줄을
#   `^\[(\d+)/(\d+)\]\s*(.*)$` 로 읽어 3 번 묶음을 **칸 이름 그대로** 쓰고 막대도 그 줄로
#   민다 — 줄 끝에 초를 달면 칸 이름이 「프로그램 (37초)」가 되는데, 그 이름은 칸이 **시작될
#   때** 찍히므로 아직 안 지난 시간을 이름에 다는 꼴이 된다. 그래서 초는 **칸이 끝나는 자리에
#   따로 한 줄**로 찍는다 — `[` 로 안 시작해 그 무늬에 안 걸리고, 껍데기는 그것을 칸 안의
#   낱줄로 읽어 막대를 조금 민다.
# ⚠ **시계는 하나다.** 칸마다 새로 두면 칸과 칸 사이에 낀 시간이 어디에도 안 잡힌다.
#   누적 초의 차로 재므로 「준비」부터 끝까지가 빠짐없이 갈리고, 낱칸의 합은 끝의 총계와 맞는다.
# ⚠ **칸 이름은 머리줄과 손으로 맞춘 사본이다** — 머리줄을 고치면 그 칸의 `Write-Elapsed`
#   이름도 같이 고친다. 머리줄에서 뽑아 쓰려면 그 줄을 고쳐야 하는데, 그 줄은 껍데기가 읽는
#   규약이라 안 건드리는 쪽을 골랐다.
$Sw     = [Diagnostics.Stopwatch]::StartNew()
$SwMark = 0
function Write-Elapsed([string]$Text) {
  $now = [int]$Sw.Elapsed.TotalSeconds
  Write-Host ("  ── $Text — 마쳤다 (" + ($now - $script:SwMark) + "초)") -ForegroundColor DarkGray
  $script:SwMark = $now
}

# ⚠ **네이티브 명령의 stderr 를 성공 스트림에 합치지 않는다 (`2>&1`).** 합치면 파워셸이 그 줄을
#   오류 레코드로 감싸고, 위 `Stop` 이 **그 자리에서 스크립트를 끝낸다.** 경고 한 줄이 설치를
#   통째로 죽인다 — 실측 2026-09-09 · 사외 VDI: `code --install-extension` 이 뱉은 Node
#   deprecation 경고에 확장 칸에서 죽었다. **경고는 실패가 아니다.**
#   ⚠ 합치면 판정도 망가진다: `Get-Ver` 가 판 대신 그 경고 줄을 읽어 갱신 여부를 헛짚는다.
#
# ⚠ **그렇다고 버리지도 않는다.** 판정만 재는 자리(`Test-Runs`·`Get-Ver`)는 `Get-Quiet` 으로
#   버리되(맨 `2>$null` 은 방패가 아니다 — 그 함수 머리), **설치하는 자리는 실패했을 때 까닭이
#   유일한 단서다.** 처음엔 다 버렸다가 확장이
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

# ── 홈 아래 우리가 쓰는 자리 — **이름은 여기 한 자리다** ────────────────────────
# ⚠ **쓰는 자와 재는 자가 같은 글자를 봐야 한다.** 아래 칸들이 이 아래에 파일을 쓰고 끝의
#   검증이 같은 자리를 다시 재는데, 글자를 자리마다 박으면 한쪽만 고쳐지는 날 **재는 자가
#   딴 자리를 보고 [O] 를 찍는다** — 부재가 통과로 읽히는 그 자리다 (#3).
$homeDir = Join-Path $env:USERPROFILE '.claude'

# ── 무엇을 깔까 — **목록이 진본이다.** 늘리려면 여기 한 줄을 더한다 ────────────────
#    core = 확장이 돌기까지 없으면 안 되는 것. dev = 코드를 짤 사람에게만.
#    ⚠ Claude Code CLI 는 이 표에 없다 — winget 이 아니라 npm 이 깔아서다(아래 4칸).
# ── 고르는 축 — **제품이다.** 아래 표 셋(CLI · 확장 · 데스크탑 앱)은 같은 축의 세 단면이고,
#    한 제품이 그 셋에 한 줄씩 든다. 사람은 「어느 도구를 쓰나」로 고르지 「CLI 냐 확장이냐」로
#    안 고른다 — 클로드 확장은 쓰는데 `claude` 는 안 쓰는 사람이 없다.
# ⚠ **벤더로 묶지 않는다.** 「구글」한 칸은 Gemini 와 안티그래비티를 한 몸으로 삼키는데 그 둘은
#   짝이 다르다: Gemini 확장은 터미널의 `gemini` 에 편집기 문맥을 넘기는 **다리**고, 안티그래비티
#   확장은 제 화면을 든 **에이전트**이며 짝이 `agy` 다. 설정 파일도 갈린다. 넷으로 두면 벤더로
#   묶는 것은 칸 둘을 같이 켜면 되지만, 셋으로 묶으면 넷을 되돌릴 방법이 없다.
# ⚠ **기본값도 이 표가 든다** — 화면이 제 값을 따로 들면 두 벌이 된다. Gemini 만 꺼져 있는 것은
#   안티그래비티가 그 자리를 대신하는 물건이라 둘을 같이 깔 까닭이 없어서다(2026-09-17 사람 판단).
$Products = @(
  @{ Key='claude';      Label='Claude';      Default=$true  }
  @{ Key='codex';       Label='Codex';       Default=$true  }
  @{ Key='antigravity'; Label='구글 Antigravity'; Default=$true  }
  @{ Key='gemini';      Label='Gemini';      Default=$false }
)

$Apps = @(
  # ⚠ `Need='vscode'` 는 `core` 의 갈래다 — `-NoVsCode` 가 이 한 줄만 건너뛴다. 확장은 이것 없이
  #   설 자리가 없으므로 같이 꺼진다. Node 는 CLI 가 타므로 `core` 로 남는다.
  @{ Name='VS Code';    Id='Microsoft.VisualStudioCode'; Cmd='code';   Arg='--version'; Need='vscode' }
  @{ Name='Node.js';    Id='OpenJS.NodeJS.LTS';          Cmd='node';   Arg='--version'; Need='core' }
  @{ Name='Git';        Id='Git.Git';                    Cmd='git';    Arg='--version'; Need='dev'  }
  @{ Name='Python';     Id='Python.Python.3.14';         Cmd='python'; Arg='--version'; Need='dev'  }
  @{ Name='GitHub CLI'; Id='GitHub.cli';                 Cmd='gh';     Arg='--version'; Need='dev'  }
)

# ── 확장과 CLI — **목록이 진본이다.** 깔 때도 끝에 잴 때도 이 두 표에서 판다 (결정 0041 · 0045).
#    **셋 다 어디서나 깐다.** 자리가 가르는 것은 프로그램이 아니라 **그 뒤에 무엇으로 붙나**다 —
#    사내는 회사 키·설정 틀·프록시로 게이트웨이에 붙고(아래 `$wantCodex` · `$wantGemini`), 사외는
#    각자 로그인(Codex 는 ChatGPT · Gemini 는 Google)으로 쓴다. 옛 판은 프로그램까지 사내로 묶어
#    사외 PC 에 Codex·Gemini 가 통째로 안 섰다(결정 0045).
# ⚠ Codex 확장은 CLI 의 `~/.codex/config.toml` 을 같이 읽어 게이트웨이를 탄다 — 다만 사용자 정의
#   프로바이더에서 CLI 와 다르게 구는 이슈가 열려 있어(openai/codex #27695), 확장 안의
#   한 턴은 사람이 잰다. ⚠ **이슈 번호를 여럿 안 적는다** — 하나가 닫혀도 이 줄만 조용히 낡는다.
#   울타리를 드는 것은 **지금 열려 있는 하나**지 목록이 아니다. Gemini 것은 창이 없는 짝(companion)이라 터미널의 CLI 에 편집기 문맥을 넘길 뿐이다.
# ⚠ **안티그래비티 확장은 위 `$DesktopApps` 의 「Antigravity 데스크탑」과 다른 물건이다.** 저쪽은 VS Code 를
#   대신하는 별개 편집기고, 이쪽은 VS Code 에 붙어 사이드바를 내는 확장이다. 이것도 다리이긴 한데 짝이
#   터미널의 `gemini` 가 아니라 **제가 받아 오는 `agy`**(`~/.gemini/bin/agy.exe` · 188MB · 확장이
#   `AGY_ENABLE_HUB=1` 로 띄운다). **설치기가 그 바이너리를 안 심는다** — 확장이 스스로 받고, 받는 곳
#   (구글 릴리스 호스트)은 사내에서 열린다(실측 2026-09-17). 게이트웨이에 물리는 자리는 아래 5⁗ 칸이 든다.
$Extensions = @(
  @{ Key='claude';      Id='anthropic.claude-code';                  Label='클로드 확장'                }
  @{ Key='codex';       Id='openai.chatgpt';                         Label='Codex 확장'                 }
  @{ Key='antigravity'; Id='Google.google-antigravity';              Label='안티그래비티 확장'          }
  @{ Key='gemini';      Id='google.gemini-cli-vscode-ide-companion'; Label='Gemini CLI Companion 확장'  }
)
# ⚠ **한 줄만 npm 이 아니다.** 구글이 `agy` 를 npm 으로 안 내준다 — 그 이름은 2013년에 남이
#   올린 자리표시자다. 그래서 `Via` 를 둔다: 없으면 npm, `winget` 이면 `Install-WingetCli` 가
#   든다. 갈림이 표 안에 있으므로 CLI 가 늘 때 볼 자리가 한 곳이다(위 `$DesktopApps` 와 같은 꼴).
# ⚠ **벤더 스크립트를 안 탄다 — winget 이 같은 것을 낸다**(실측 2026-09-17 · `Google.AntigravityCLI`
#   1.2.4 · 게시자 Google). 옛 판은 <https://antigravity.google/cli/install.ps1> 을 받아 돌렸는데,
#   그 길은 **벤더가 해시를 안 내 지문을 못 쟀다.** winget 매니페스트는 `InstallerSha256` 을 들고
#   arm64 도 함께 든다 — 울타리 하나가 생기고 갈래 하나가 공짜로 따라온다.
#   ⚠ **한 판 뒤처지는 값을 친다** — winget 이 1.2.4, 벤더 스크립트가 주던 것이 1.2.5 였다.
#   ⚠ **옛 길로 깐 기계는 이 자리에 안 온다.** 아래 `Install-WingetCli` 가 `agy` 가 잡히면 「있음」으로
#     지나가는데, 그 `agy` 를 winget 은 모르므로 **올리기도 조용히 지나간다.** winget 으로 옮기려면
#     사람이 옛 것을 한 번 걷어야 한다 — 우리가 남의 설치본을 지우지는 않는다.
# ⚠ **VS Code 의 「안티그래비티 확장」과 다른 물건이다.** 확장은 제 몫을 스스로 받아 `~/.gemini/bin`
#   에 두고 절대 경로로 띄우는데, **PATH 에 서는 것은 이 CLI 뿐이다**(실측 2026-09-17). 그래서
#   **확장을 깐 기계도 이 걸음을 건너뛰지 않는다** — 같은 것(약 197MB)을 두 번 받는다. 줄이려면
#   제품 칸을 끄는 것이 답이고, 자리를 합치는 것은 우리가 정할 수 있는 것이 아니다.
$Clis = @(
  @{ Key='claude'; Pkg='@anthropic-ai/claude-code'; Cmd='claude'; Label='Claude Code CLI' }
  @{ Key='codex';  Pkg='@openai/codex';             Cmd='codex';  Label='Codex CLI'       }
  # ⚠ **`Cmd` 를 우리가 정하는 것이 아니다** — winget 매니페스트의 `Commands:` 가 `agy` 를 든다.
  #   winget 이 받은 `cli_windows_x64.exe` 를 **그 이름으로 세워** 제 패키지 자리에 두고, 그 자리를
  #   사용자 PATH 에 심는다(실측 2026-09-17: `…\WinGet\Packages\Google.AntigravityCLI_…\agy.exe`).
  @{ Key='antigravity'; Via='winget'; Cmd='agy';    Label='안티그래비티 CLI'
     Id='Google.AntigravityCLI' }
  @{ Key='gemini'; Pkg='@google/gemini-cli';        Cmd='gemini'; Label='Gemini CLI'      }
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
#   달렸는데 이 표는 자리를 모른다** — 사내는 게이트웨이로 서고 사외는 구독 로그인으로 선다.
#   자리를 가르는 자는 아래 프로브(`#site-probe`)이고, 이 표는 **주소가 있으면 쓰는 것, 없으면
#   안 쓰는 것**으로만 판정한다 — 자리 판별을 표에 옮겨 적으면 같은 규칙이 두 자리에 살고
#   한쪽만 낡는다.
# ── 데스크탑 앱 — **목록이 진본이다.** 아래 2′ 칸이 깔 때도, 마지막 「연다」 칸이 띄울
#    것을 찾을 때도 이 표에서 판다. 옛 판은 이름 하나가 세 자리에 박혀 있었다.
# ⚠ **셋의 설치 길이 서로 다르다**(실측 2026-09-17) — 그래서 이 표는 id 목록이 아니라
#   **길까지 든다.** id 만 들면 갈림이 2′ 칸 안으로 숨어, 앱이 늘 때 표를 고쳐도 안 걸린다.
#   · `winget` — winget 이 깔고 winget 이 잰다. `Source` 가 어느 소스인지 든다
#   · `setup`  — 제 설치본을 받아 조용히 돌린다. winget 이 모르는 앱이다
# ⚠ **띄울 이름(`App`)을 이제 따로 적는다.** 옛 판은 winget id 의 뒷칸(`만든이.앱`)에서
#   팠는데 **스토어 제품은 id 가 `9PLM9XGG6VKS` 라 팔 것이 없다** — 파생이 죽은 자리다.
#   두 값이 같은 것을 가리키는 것이 아니라(하나는 패키지, 하나는 시작 메뉴에 뜨는 글자)
#   한쪽만 낡는 꼴도 아니다.
# ⚠ **`setup` 갈래는 winget 이 못 잰다** — 종료코드로만 판정하지 않고 시작 메뉴에 묻는다.
#   그 물음은 이 파일이 이미 쓰는 자다(`Get-StartApps` · 아래 「연다」 칸의 ⚠ 참고): 스토어
#   꼴이든 예전 꼴이든 같은 답을 내므로 꼴이 늘어도 안 어긋난다.
$DesktopApps = @(
  @{ Key = 'claude'; Label = 'Claude 데스크탑'; App = 'Claude'
     Via = 'winget'; Id = 'Anthropic.Claude'; Source = 'winget' }
  # ⚠ **코덱스는 ChatGPT 앱 안에 산다** — 스토어 제품이 하나이고, 사람 눈에 닿는 이름은 전부
  #   `ChatGPT` 다: 시작 메뉴 이름 · 매니페스트 `DisplayName` · 실행 파일 `app/ChatGPT.exe`.
  #   `Codex` 가 남아 있는 자리는 꾸러미 이름(`OpenAI.Codex_…!App`) 하나뿐이라, **찾는 자에게
  #   줄 이름은 `ChatGPT` 여야 한다.** `Codex` 로 두면 97초 걸려 멀쩡히 깔아 놓고 「설치 실패」로
  #   찍는다 — 깐 뒤에 이름으로 되찾지를 못해서다(실측).
  # ⚠ **winget 의 msstore 소스로 안 간다.** TLS 를 가로채는 회선에서 winget 의 고정 인증서
  #   검사가 `0x8a15005e` 로 져 **소스를 열지도 못한다.** 같은 회선에서 스토어 제 설치 스텁은
  #   선다 — `StoreInstaller.exe /S` · 종료 `0` · 97초(실측 2026-09-17 · 사내 회선). 웹에서
  #   사람이 누르는 [다운로드] 단추가 주는 것도 이 스텁이라 **공식 길이기도 하다.**
  # ⚠ **깔린 것을 올리는 길은 이 스텁으로도 막힌다** — 갱신은 윈도우 업데이트를 타는데 그쪽이
  #   끊긴다(`0x80072EFD`). 깔기는 되고 올리기는 안 되는 것이라, 없으면 깔고 있으면 둔다.
  @{ Key = 'codex';  Label = 'Codex 데스크탑';  App = 'ChatGPT'
     Via = 'setup';  SilentArgs = @('/S')
     Url = 'https://get.microsoft.com/installer/download/9PLM9XGG6VKS' }
  # ⚠ **Gemini 데스크탑은 이 표에 없다 — 뺐다(2026-09-17).** 이 회선에서 **두 번 다 졌고 끊기는
  #   자리가 같다**: 구글 태그 서버의 스텁 11.8MB 는 다 받아지는데, 그 스텁이 **알맹이를 받으러
  #   갈 때** 끊긴다(실측 ① 갱신 요청이 `200` 에 차단 안내 HTML · ② 종료 `-2147012866` =
  #   `0x80072EFE` 연결 중단 · 그 뒤 구글 갱신기가 **제 작업을 지우고 스스로 되돌아 나간다**).
  #   ⚠ **「막힌 것은 우리가 분류하지 않는다」(결정 0052)를 어기는 것이 아니다** — 그 조항은
  #     *지는 방식을 미리 규칙표로 짓지 말라*는 말이고, 여기서 뺀 근거는 규칙표가 아니라
  #     **두 번의 실측**이다. 표에 있는 것은 여전히 시도하고, 지면 그대로 찍는다.
  #   ⚠ **집에서는 멀쩡히 깔린다** — 잃는 길이 있다는 뜻이라 적어 둔다. 필요하면 사람이
  #     <https://gemini.google.com/app> 에서 받고, **안티그래비티가 그 자리를 든다.**
  # ⚠ **판 박은 주소를 걷었다 — winget 이 판 없는 주소다**(실측 2026-09-17). `Google.Antigravity`
  #   2.14.0 의 `InstallerUrl` 이 우리가 손으로 박아 뒀던 주소와 **글자까지 같다.** 옛 곁말은
  #   「판 없는 주소를 못 찾았다 · 새 판이 나오면 이 줄을 손으로 고쳐야 한다」였는데, 못 찾은
  #   것이 아니라 **winget 을 안 재고 그렇게 적었다.** 손으로 고칠 자리가 하나 없어진다.
  #   ⚠ **설치 꼴도 winget 이 든다** — 매니페스트가 `nullsoft` 라 조용한 인자(`/S`)를 저쪽이
  #     댄다. 우리가 `Nullsoft Install System` 을 읽어 `/S` 를 고른 그 판단이 흡수된 자리다.
  #   ⚠ **한 번 깔리면 제가 따라간다** — 앱이 electron-builder 의 자동 갱신을 들고 있어
  #     (`resources/app-update.yml`) 우리는 **한 판만 넣어 주면 된다.** winget 갱신은 그 위의 보험이다.
  # ⚠ **집이 둘인데 하나는 이 회선에서 못 연다 — 그리고 winget 이 드는 것은 여는 쪽이다.** 받는
  #   자리가 둘로 갈리는데 값이 다르다: 「Antigravity 2.0」은 `storage.googleapis.com` 에서 오고
  #   **사내 회선에서 열린다**(실측 `206`) — `Google.Antigravity` 가 가리키는 데가 여기다. 같은
  #   페이지 아래쪽 「Antigravity IDE (Standalone)」은 `edgedl.me.gvt1.com` 에서 오는데 **거기는
  #   TLS 악수부터 진다**(제미나이 데스크탑의 알맹이를 막는 그 호스트다). 둘은 판 번호도 계보도
  #   다른 별개 물건이라, **패키지 이름을 바꿀 때 이 갈림을 다시 본다.**
  @{ Key = 'antigravity'; Label = 'Antigravity 데스크탑'; App = 'Antigravity'
     Via = 'winget'; Id = 'Google.Antigravity'; Source = 'winget' }
)

# 고를 목록을 한 줄씩 내준다 — `product|키|글자|기본값`. **여기까지 오는 데 부수효과가 없다**
# (위는 다 선언이다), 그래서 이 갈래는 설치를 한 톨도 안 건드리고 나간다.
if ($Describe) {
  $Products | ForEach-Object {
    'product|{0}|{1}|{2}' -f $_.Key, $_.Label, $(if ($_.Default) { 'on' } else { 'off' })
  }
  exit 0
}

# 고른 제품. **안 주면 표의 기본값** — 화면 갈래와 콘솔 갈래가 같은 자를 쓴다.
# ⚠ **모르는 이름을 삼키지 않는다.** 오타 하나로 제품이 조용히 안 깔리면 **초록으로 끝나고**
#   아무도 못 본다 — 값을 준 사람이 제일 늦게 안다.
if ($PSBoundParameters.ContainsKey('Pick')) {
  # ⚠ **쉼표만 구분자로 두지 않는다 — 공백도 받는다.** 파워셸에서 `-Pick a,b,c` 를 **따옴표 없이**
  #   넘기면 껍데기가 그것을 배열로 읽고 `[string]` 이 공백으로 이어 붙인다. 값을 준 사람은
  #   쉼표를 쳤는데 몸통에는 `a b c` 한 덩이가 온다(실측 2026-09-17). 가르는 자를 넓히면 그
  #   자리가 **아예 없어진다** — 제품 이름에는 공백이 없어 넓혀도 잃는 것이 없고, 이 파일은
  #   `#config-repo` 에서 이미 공백으로 가른다.
  $PickKeys = @($Pick -split '[,\s]+' | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
  # ⚠ **이름을 `$known` 으로 두지 않는다 — 아래 5′ 칸이 그 이름을 `$Vars` 뜻으로 쓴다**
  #   (`$known = $Vars | …` 줄). ⚠ **좌표를 줄 번호로 안 박는다** — 위가 늘면 그 숫자만 조용히
  #   낡는다(이 자리가 그랬다).
  #   오늘은 그쪽이 먼저 덮어써서 맞게 돌지만, 그 줄 **앞**에 `$known` 을 읽는 줄이 하나 붙는 날
  #   조용히 뜻이 바뀐다 — 파워셸은 대소문자도 스코프도 안 가려 준다(이 파일이 `$Planted` 에서
  #   이미 겪은 그 함정이다).
  $ProductKeys = @($Products | ForEach-Object { $_.Key })
  $unknown     = @($PickKeys | Where-Object { $ProductKeys -notcontains $_ })
  foreach ($k in $unknown) {
    Write-Host ('  ! 모르는 제품 이름 — {0} (아는 것: {1})' -f $k, ($ProductKeys -join ', ')) -ForegroundColor Yellow
  }
  # 모르는 이름은 들고 가지 않는다 — 아래 걸음마다 아무것도 안 맞는 열쇠가 섞여 다닐 까닭이 없다.
  $PickKeys = @($PickKeys | Where-Object { $ProductKeys -contains $_ })
  # ⚠ **아는 이름이 하나도 안 남으면 그것은 오타지 「아무것도 안 깔겠다」가 아니다.** 위 경고 한
  #   줄은 여덟 칸 로그에 묻히고, 설치는 **제품을 하나도 안 깐 채 초록으로 끝난다** — 이 칸의
  #   곁말이 막겠다고 한 바로 그 상태다(실측 2026-09-17: 구분자 하나가 어긋나 그렇게 끝났다).
  #   막지는 않는다(프로그램·키·씨앗은 여전히 설 자리가 있다). 대신 **끝까지 남는 자리**에 적어
  #   빨강으로 끝나게 한다 — 노란 줄과 달리 이것은 맨 끝 검증에 이름이 선다.
  if ($unknown -and -not $PickKeys) {
    Write-Host ('  ! 고른 제품이 하나도 안 섰다 — 준 값을 쉼표로 가른다: -Pick "{0}"' -f
                ($ProductKeys -join ',')) -ForegroundColor Red
    $Fails.Add(('-Pick 에 아는 제품 이름이 없다 (준 값: {0})' -f $Pick))
  }
} else {
  $PickKeys = @($Products | Where-Object { $_.Default } | ForEach-Object { $_.Key })
}
# 제품 칸을 하나도 안 켠 판 — 아래 걸음들이 다 빈 채로 지나가므로 여기서 한 번 말한다.
if (-not $PickKeys) { $PickKeys = @() }

$Vars = @(
  @{ Name='ANTHROPIC_BASE_URL';   Desc='게이트웨이 주소 — 사내는 로컬 프록시 루프백 · 끝에 /v1 을 붙이지 않는다 (CLI 가 붙인다)'; Gateway=$true }
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
#   자리에 살고(배포 묶음에 안 실린다) 설정 저장소의 훅이 민다. 자리 파일이
#   `#home-settings = overwrite` 를 드는 자리(사외 VDI)에서는 **그 덮기가 이 설치보다 나중**
#   이라 씨앗이 최종 승자다 — 여기만 늘리면 그 자리에서 조용히 잃는다.
$Features = @{
  ENABLE_TOOL_SEARCH = 'true'    # 도구를 미리 다 안 싣고 필요할 때 찾아 쓴다
}

# ── 고를 모델 목록 — **자리를 탄다. 게이트웨이에 닿는 자리에만 선다** (결정 0048) ────
# `/model` 목록에 설 줄을 우리가 선언한다. 접미사 `[1m]` 이 창을 1M 으로 연다 — 게이트웨이는
# 이미 그만큼을 주고 있었고(0047 · 상한을 넘겨 쏘면 저쪽이 `1000000` 이라고 말한다) 깎던 자는
# CLI 였다. 셋 다 쟀다: 4.6 은 792k · 4.7·5 는 576k 로 200 이 왔다.
# ⚠ **씨앗(`vdi-home-settings.json`)에 두지 않는다.** 이 이름들은 게이트웨이가 등록한 것이라
#   자리를 타는데 씨앗은 익명 층이고 포크를 따라간다(`secrets.d/posco.env` 의 모델 칸 곁말과
#   같은 축). 사외는 구독으로 돌아 이 이름이 아예 없어서, 씨앗에 두면 **사외 VDI 의 목록에
#   못 부르는 줄이 서고 고르면 그 자리에서 깨진다** — 게다가 그 자리는 씨앗 덮기가 이 설치보다
#   나중이라(위 ⚠) 여기서 안 쓴 것도 씨앗이 되살린다. 그래서 자리를 재는 이 파일이 든다.
# ⚠ **목록의 진본은 `GET /v1/models` 다.** 게이트웨이가 내는 것만 적는다 — 실측 2026-09-15 에
#   Sonnet 5 와 Haiku 는 그 목록에 **없다**(내장 줄로는 보이지만 고르면 400 이다). 그래서 아래
#   `$ModelPickerOnly` 로 내장 줄을 숨긴다: 목록이 곧 「이 자리에서 실제로 되는 것」이 된다.
# ⚠ **이름은 하이픈으로 적는다.** 게이트웨이는 점 표기(`claude-opus-4.7`)로 목록을 내지만
#   **두 표기를 다 받는다**(하이픈으로 쏘면 `model: claude-opus-4.7` 로 답한다 · 실측). 하이픈이
#   CLI 카탈로그가 아는 이름이라 표시명·접미사 판정이 걸리고, 점 표기는 「모르는 모델」로 떨어져
#   접미사가 안 붙는다.
# 줄이 늘면 여기 한 줄. 게이트웨이가 그 이름을 내는지 먼저 묻는다.
$ModelPicker = @(
  @{ model = 'claude-sonnet-4-6[1m]'; description = 'Sonnet 4.6 · 게이트웨이 · 1M 창' }
  @{ model = 'claude-opus-4-7[1m]';   description = 'Opus 4.7 · 게이트웨이 · 1M 창' }
  @{ model = 'claude-opus-5[1m]';     description = 'Opus 5 · 게이트웨이 · 1M 창' }
)
# 내장 줄(Sonnet 5 · Haiku · Custom 칸)을 숨긴다 — 이 게이트웨이가 안 내는 것들이다.
# `Default` 행은 이 값과 무관하게 남는다.
$ModelPickerOnly = $true

# ── 배선이 먼저다 ────────────────────────────────────────────────────────────────
# ⚠ winget 이 심은 PATH 는 **이 창에 안 걸린다** — 이 창이 winget 보다 먼저 떴다.
#   배선 없이 물으면 이미 깔린 것도 「없음」이 나와 재설치로 샌다. 그래서 묻기 전에도,
#   설치 직후에도 다시 태운다.
function Add-ToPath([string]$Dir) {
  if (-not $Dir) { return }
  # ⚠ **묻는 것부터 거절당하는 자리가 기계 PATH 에 섞여 있다.** 윈도우가 SYSTEM 프로필 아래에도
  #   `…\config\systemprofile\AppData\Local\Microsoft\WindowsApps` 를 두는데, 일반 사용자로는
  #   **있는지 묻는 `Test-Path` 가 UnauthorizedAccessException 을 던진다.** 이 파일 머리의
  #   `$ErrorActionPreference = 'Stop'` 아래에서 그것은 곧 **설치 전체의 죽음**이다 — 그리고
  #   이 함수는 배선 칸이라 **아무것도 묻기 전에** 걸려, 사람은 첫 화면에서 빨간 글만 보고 끝난다
  #   (실측 2026-09-17 집 PC · 기계 PATH 12번째 줄).
  # ⚠ **여기서 「못 읽는 것」과 「없는 것」을 가르지 않는다** — 둘 다 답이 같다: PATH 에 안 더한다.
  #   가를 값이 없는 자리에서 가르려 들면 예외만 늘고 얻는 것이 없다.
  try { if (-not (Test-Path -LiteralPath $Dir -ErrorAction Stop)) { return } } catch { return }
  if (($env:PATH -split ';') -contains $Dir) { return }   # 여러 번 불려도 PATH 가 안 분다
  $env:PATH = "$Dir;$env:PATH"
}

function Update-RuntimePath {
  # ⚠ **레지스트리를 먼저 태운다 — 이름 박은 목록은 보험이다.** 이 창이 뜬 뒤에 깔린 것이 심은
  #   PATH 는 레지스트리에만 있어서, 목록만 보면 **거기 이름이 없는 도구는 깔고도 영영 안 잡힌다.**
  #   `Add-ToPath` 로 덧대므로 이 창이 원래 들고 있던 자리는 안 잃고 같은 자리가 두 번 붙지도 않는다.
  # ⚠ **순서가 뜻이다 — 레지스트리가 먼저, 이름이 나중.** `Add-ToPath` 는 앞에 끼우므로 나중에
  #   부른 쪽이 앞에 선다. 윈도우는 `WindowsApps` 에 스토어로 보내는 파이썬 껍데기를 두는데,
  #   그것이 사용자 PATH 에 있어도 **진짜 파이썬이 그 앞에 서야** 한다.
  foreach ($sc in @('Machine','User')) {
    $v = [Environment]::GetEnvironmentVariable('Path', $sc)
    if ($v) { foreach ($d in ($v -split ';')) { Add-ToPath $d } }
  }
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
  # ⚠ **`agy` 자리는 여기 안 적는다.** winget 이 portable 을 깔면서 **제 자리를 사용자 PATH 에
  #   제 손으로 넣는다** — 위 레지스트리 읽기가 그것을 태운다. 이름으로 박으면 저쪽이 자리를
  #   옮길 때 조용히 어긋나고(폴더 이름에 소스 해시가 박혀 있다), **확장이 따로 둔 사본**
  #   (`~/.gemini/bin`)을 박으면 그쪽이 앞에 서서 **진짜 CLI 를 가린다**(실측 2026-09-17 —
  #   둘은 같은 크기의 다른 파일이다).
}

# ⚠ **존재로 묻지 않고 불러 본다.** 윈도우는 `WindowsApps\python` 에 스토어로 보내는
#   껍데기를 깔아 두고 `Get-Command` 가 그것을 잡아 「있음」을 낸다 — 부르면 죽는 파일이다.
#   「깔린 것과 닿는 것은 다른 명제」라, 그 오판으로 설치를 건너뛰면 뒤가 조용히 무너진다.
# 판을 한 줄로 읽는다 — 올리기 전후를 견주려면 숫자가 있어야 한다. 못 읽으면 빈 글자다.
function Get-Ver([string]$Cmd, [string]$Arg) {
  $o = Get-Quiet $Cmd $Arg | Select-Object -First 1; return ("$o").Trim()
}

# 자리를 **닿음으로** 가른다 — `#site-probe = 호스트:포트` 가 있으면 거기에 TCP 로 물어본다.
# ⚠ **이름으로 안 가른다.** DNS 는 사외에서도 사내 IP 를 풀어 주므로 이름만 봐서는 안 갈린다
#   (실측: 사외에서 사내 호스트가 사내 IP 로 풀리고 포트는 안 열렸다 · 결정 0026).
# ⚠ **규칙을 여기 옮겨 적은 것이 아니다.** 재는 대상은 값 파일이 든 그 한 줄이라, 몸통은
#   **선언**을 볼 뿐 규칙을 들지 않는다.
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
  $target = Join-Path $homeDir 'node-ca.pem'
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

# 네이티브 명령을 **판정만 하려고** 돌린다 — stdout 은 줄 배열로 돌려주고 stderr 는 버린다.
# 종료코드는 `$LASTEXITCODE` 에 남는다(못 부르면 -1).
# ⚠ **버리는 것도 `Stop` 아래서는 던진다.** `2>$null` 이 곧 「파워셸이 stderr 를 건드리는」 자리라
#   그 줄이 오류 레코드가 되고 위 `Stop` 이 거기서 끝낸다 — 실측 2026-09-15 · 사내 VDI: 로그인
#   안 된 gh 의 「로그인하라」 한 줄에 GitHub CLI 로그인 칸에서 설치가 끊겼다. 집 PC 는 gh 가 이미 서 있어
#   stderr 가 비었을 뿐이다 — **한 기계의 초록은 다른 기계의 빨강을 못 재준다.**
#   그래서 `Invoke-Logged` 와 같은 규율로 여기서만 `Stop` 을 풀고, **맨 `2>$null` 은 이 함수
#   하나에만 산다.** 다른 자리는 뽑기 검사가 막는다(`scripts/build-dist.sh`).
function Get-Quiet([string]$File, [string[]]$CmdArgs) {
  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try { return @(& $File @CmdArgs 2>$null) }
  catch { $global:LASTEXITCODE = -1; return @() }
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

# 받으러 나가기 전에 **무엇을 얼마나** 받는지 댄다 — 느린 링크에서 「멎었나 도나」를 가르는
# 것이 이 한 줄이다. 크기를 안 주는 자리도 있어 그때는 이름만 댄다.
function Say-Get($Asset) {
  $mb = 0
  try { $mb = [double]$Asset.size / 1MB } catch { }
  if ($mb -gt 0) { Write-Host ('      · 받는다 — {0} ({1:N1} MB)' -f $Asset.name, $mb) }
  else           { Write-Host ('      · 받는다 — {0}' -f $Asset.name) }
}

# 큰 것을 받는 자 — **흘려 쓰고, 가면서 말하고, 두 시계를 다 못박는다.**
# ⚠ **`Invoke-WebRequest` 를 여기서 안 쓰는 까닭 셋.** 작은 것에는 그것이 맞지만 이 자리는
#   실측 300 MB 다(본체 206.7 · 딸린 것 93.2 — v1.29.290):
#   · **몸통을 메모리에 물고 있다가 쓴다**(5.1). 200 MB 를 그렇게 받으면 그 자체로 느리다
#   · **진행을 말할 자리가 없다.** 막대를 켜면 몇 배 느려지고, 끄면 몇 분이 통째로 조용하다 —
#     조용한 몇 분은 사람이 창을 닫는 시간이다
#   · **`ReadWriteTimeout` 손잡이가 없다.** `-TimeoutSec` 는 「응답 머리가 오기까지」만 들어서,
#     몸통을 읽는 사이가 느린 링크에서 기본 300초를 넘기면 거기서 진다
# ⚠ **두 시계가 재는 자리가 다르다** — `Timeout` 은 프록시가 파일을 통째로 받아 검사하고
#   머리를 내주기까지, `ReadWriteTimeout` 은 그다음 한 번 읽는 사이. 둘 다 못박는다.
function Get-Download([string]$Url, [string]$OutFile, [int]$WaitSec = 600) {
  $req = [Net.HttpWebRequest]::Create($Url)
  $req.Timeout          = $WaitSec * 1000
  $req.ReadWriteTimeout = $WaitSec * 1000
  $req.UserAgent        = 'PAISetup'
  $res = $req.GetResponse()
  try {
    $total = 0.0
    try { $total = [double]$res.ContentLength } catch { }
    $in  = $res.GetResponseStream()
    $out = [IO.File]::Create($OutFile)
    try {
      # ⚠ **줄로 말한다 — 막대가 아니라.** 화면 껍데기가 stdout 을 **줄 단위로** 읽으므로,
      #   한 줄 안에서 덮어쓰는 꼴은 그쪽에 한 글자도 안 닿는다.
      $buf = New-Object byte[] 1048576
      $got = 0.0
      $mark = 0
      while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) {
        $out.Write($buf, 0, $n)
        $got += $n
        if ($total -gt 0) {
          # ⚠ `[int]` 는 **반올림**한다 — 99.6% 가 100% 로 찍히면서 곁의 MB 와 안 맞았다
          #   (실측: `100% · 92.8 / 93.2 MB`). 내림으로 간다.
          $pct = [Math]::Floor(($got / $total) * 100)
          if ($pct -ge ($mark + 10)) {
            $mark = $pct - ($pct % 10)
            Write-Host ('        {0}% · {1:N1} / {2:N1} MB' -f $mark, ($got / 1MB), ($total / 1MB))
          }
        } elseif ($got -ge ($mark + 1) * 25MB) {
          # 크기를 안 주는 자리 — 몇 퍼센트인지는 못 말해도 **움직이고 있다**는 말은 한다.
          $mark++
          Write-Host ('        {0:N1} MB 받았다' -f ($got / 1MB))
        }
      }
    } finally { $out.Close(); $in.Close() }
    # ⚠ **끝난 줄을 따로 댄다.** 몫을 내림으로 세니 마지막 토막에서는 100% 가 안 뜬다 —
    #   그러면 **끝나는 것을 아무도 못 본다.** 마지막 줄은 몫이 아니라 받은 양으로 말한다.
    Write-Host ('        다 받았다 — {0:N1} MB' -f ($got / 1MB))
  } finally { $res.Close() }
}

function Test-Runs([string]$Cmd, [string]$Arg) {
  if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) { return $false }
  $null = Get-Quiet $Cmd $Arg; return ($LASTEXITCODE -eq 0)
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
# **이 값이 로컬 프록시를 가리키나** — 이름이 아니라 값에서 판다.
# ⚠ **이름 목록으로 안 가른다.** 옛 판은 「게이트웨이 값인가」를 `$Vars` 표의 `Gateway` 표시가
#   들었는데, 그 표는 **「물을 것」의 표라 값 파일 전체를 안 덮는다.** 값 파일이 이름 하나를 더
#   실어 보내면 그것은 표 밖이라 두 문(아래 심는 문 · 걷는 문)을 그냥 지나갔다 — 실측
#   2026-09-17 집 PC: 「사외」를 옳게 찍고도 `GOOGLE_GEMINI_BASE_URL` 이 죽은 루프백을 가리킨
#   채 심겼다. 목록은 늘 뒤처지므로 **값에서 파생한다.**
# ⚠ **루프백이 근거가 되는 까닭은 아래 5⁵ 칸이 이미 쓰는 그것이다** — 이 설치기는 루프백이
#   아닌 주소에 프록시를 **안 세운다.** 그래서 루프백으로 박힌 주소는 이 설치기의 게이트웨이
#   갈래 말고는 나올 자리가 없고, 그 갈래는 사내에서만 선다.
# ⚠ **못 읽는 글자를 예외에 맡기지 않는다** — `[Uri]'아무 글자'` 는 상대 주소로 서고 그 위의
#   `.IsLoopback` 은 5.1 에서 오류 없이 `$null` 을 준다(5⁵ 칸의 ⚠ 와 같은 자). 절대 주소일
#   때만 묻는다.
# ⚠ **갈래(scheme)를 반드시 묻는다 — `IsLoopback` 하나로는 파일 경로가 걸린다.** `[Uri]` 는
#   `C:\Users\…\node-ca.pem` 을 `file:///C:/…` 로 세우는데 그 호스트가 비어 **`IsLoopback` 이
#   참**이다(실측 2026-09-17). 갈래를 안 물으면 이 체가 `NODE_EXTRA_CA_CERTS` 같은 경로 값까지
#   「프록시 주소」로 읽어 **CA 배선을 걷는다.** 프록시는 http 로만 선다.
function Test-ProxyValue([string]$Value) {
  if (-not $Value) { return $false }
  $u = $null
  try { $u = [Uri]$Value } catch { return $false }
  if (-not ($u -and $u.IsAbsoluteUri)) { return $false }
  if ($u.Scheme -ne 'http' -and $u.Scheme -ne 'https') { return $false }
  return [bool]$u.IsLoopback
}

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

# ── 앱 이름 — **진본은 값 파일의 `#app-name` 한 줄이다** ─────────────────────────
# ⚠ **여기 든 글자는 진본이 아니라 울타리다.** 이름이 사람에게 찍히는 자리는 여럿인데
#   (바로가기 이름 · 바로가기 설명 · 물음 상자 제목), 그 자리마다 글자를 박으면 이름을
#   바꾸는 날 **한 자리만 낡고 그 한 자리는 아무도 안 본다.** 그래서 다 여기서 판다.
# ⚠ **없어도 선다.** 값 파일이 그 줄을 안 드는 판(옛 배포본 · 이 파일만 떼어 받은 사람)에서
#   이름이 비면 바로가기가 `.lnk` 라는 이름 없는 아이콘으로 서고 상자 제목이 빈칸이 된다 —
#   그건 이름을 못 정한 것이 아니라 **못 읽은 것**인데 화면에는 똑같이 보인다. 울타리가 든다.
$AppNameDefault = 'PAI Setup Wizard'
$AppName = Read-Directive $EnvFile 'app-name'
if (-not $AppName) { $AppName = $AppNameDefault }

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

  # ⚠ **진행 막대도 여기서 끈다 — TLS 와 같은 까닭이다.** Windows PowerShell 5.1 은 막대를
  #   그리느라 내려받기가 **몇 배 느려진다.** 옛 판은 이것을 둘째 갈래 안에서만 껐다가
  #   `finally` 로 되돌려, **정작 수십 MB 를 받는 셋째 갈래는 막대를 켠 채로 받았다.**
  # ⚠ **되돌리는 손이 없어도 된다.** 함수 안에서 대입하면 **그 함수 안에서만 서고**(바깥 것을
  #   가린다) 나오면 저절로 돌아온다 — 실측(PowerShell 7.4.6): 밖 `Continue` → 안
  #   `SilentlyContinue` → 나온 뒤 다시 `Continue`. 옛 판의 `$pp` 저장·복원은 그래서 걷었다.
  $ProgressPreference = 'SilentlyContinue'

  # ⚠ **갈래를 넘기는 기준은 「깔았다」가 아니라 「불리나」다.** 갈래마다 「됐다」고 말하면서
  #   실제로는 안 잡히는 자리가 있다 — AppX 는 깔려도 이 세션의 PATH 에 안 잡힐 수 있다.
  #   그래서 밟은 뒤마다 **PATH 를 레지스트리에서 새로 읽고** 다시 묻는다.
  #   ⚠ 이 세션 PATH 만 보면 방금 깔린 것을 영영 못 본다: 창은 뜰 때 환경을 한 번 복사한다.
  $reach = {
    Update-RuntimePath      # 레지스트리 두 범위를 다시 태우는 자 — 사본을 여기 또 두지 않는다
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
  # ⚠ `-AllUsers` 는 관리자를 탄다. 안 되면 그것 없이 한 번 더 — 제 계정에만 서도 쓸 수 있다.
  try {
    Write-Host '    · PowerShell 모듈로 고쳐 본다 (PSGallery)'
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
    if (& $reach) {
      Write-Host '  되살렸다 (Repair-WinGetPackageManager)' -ForegroundColor Green
      return $true
    }
    Write-Host '    · 모듈은 돌았는데 winget 이 안 잡힌다 — 다음을 해 본다'
  } catch {
    Write-Host "    · 모듈로 안 됨 — $(Say-Why $_)"
  }

  # ③ GitHub 릴리스에서 받아 깐다
  # ⚠ **갈래 하나가 try 하나로 묶여 있어 걸음 이름이 뭉갰다.** 받기·풀기·깔기가 다 「내려받기
  #   안 됨」으로 찍혔다 — **받는 건 다 되고 깔다 졌을 때도** 그랬다. 실측 2026-09-11(사내):
  #   206.7 MB 를 다 받아 놓고 그 줄을 보고는 망을 의심하게 됐다.
  #   그래서 **걸음마다 제 실패 문장을 들고 다니고**, catch 는 그것을 그대로 쓴다. 문장을
  #   통째로 드는 까닭은 조사다 — 「묻기에서 졌다」 같은 것을 안 짓게, 각자 완성된 말을 든다.
  $step = '셋째 갈래에서 졌다'
  try {
    Write-Host '    · GitHub 릴리스에서 받아 본다'
    $step = '릴리스 목록을 못 물었다'
    # ⚠ **묻는 것은 빨리 포기한다.** 작은 JSON 하나라, 안 오는 것은 느린 것이 아니라 막힌
    #   것이다(사내 프록시). 여기를 길게 주면 **막힌 망에서 설치가 말없이 오래 멎는다.**
    $rel = Invoke-RestMethod 'https://api.github.com/repos/microsoft/winget-cli/releases/latest' `
             -UseBasicParsing -TimeoutSec 60 -ErrorAction Stop
    $step = '받을 자리를 못 만들었다'
    $work = Join-Path ([IO.Path]::GetTempPath()) "winget-$PID"
    New-Item -ItemType Directory -Path $work -Force | Out-Null

    # ⚠ **밖에서 선언한다.** 딸린 것 갈래가 통째로 안 도는 자리가 있고(그 자산이 릴리스에
    #   없다), 아래 본체 설치가 이 값을 읽는다 — 안 선언하면 그 자리에서 「없는 변수」가 된다.
    $depPaths = @()

    # 딸린 것이 먼저다 — 없으면 본체 설치가 그 자리에서 진다
    $dep = $rel.assets | Where-Object { $_.name -like '*Dependencies.zip' } | Select-Object -First 1
    if ($dep) {
      $z = Join-Path $work 'dep.zip'
      $step = '딸린 것 zip 을 못 받았다'
      Say-Get $dep
      Get-Download $dep.browser_download_url $z
      $step = '딸린 것 zip 을 못 풀었다'
      Expand-Archive -LiteralPath $z -DestinationPath (Join-Path $work 'dep') -Force
      $step = '딸린 것을 못 깔았다'
      $deps = @(Get-ChildItem (Join-Path $work 'dep') -Recurse -Filter '*.appx' |
                Where-Object { $_.FullName -match 'x64' })
      # ⚠ **하나도 못 골랐으면 그것부터 말한다.** 고를 것이 없는 것과 다 깐 것은 화면에서
      #   똑같이 조용했다 — 그리고 다음 줄의 본체 설치가 「딸린 것이 없다」로 진다.
      #   실측 2026-09-11: 이 zip 은 `x64/`·`x86/`·`arm64/` 에 `.appx` 셋씩, x64 는 VCLibs 둘과
      #   WindowsAppRuntime 하나다. 0 이 나오면 저쪽 꼴이 바뀐 것이니 사람이 봐야 한다.
      if (-not $deps.Count) {
        Write-Host '      ! 딸린 것에서 x64 를 하나도 못 골랐다 — 본체 설치가 질 수 있다' `
          -ForegroundColor Yellow
      } else {
        Write-Host "      · 딸린 것 $($deps.Count)개를 깐다"
      }
      foreach ($d in $deps) {
        # ⚠ **하나가 져도 여기서 끝내지 않는다** — 이미 더 새것이 깔린 기계는 윈도우가 무는데
        #   그건 실패가 아니라 「할 일 없음」이고, 그걸로 본체까지 막으면 멀쩡한 PC 가 진다.
        # ⚠ **그렇다고 삼키지도 않는다.** 옛 판은 `catch { }` 라 한 글자도 안 남았고, 그래서
        #   **「받았는데 설치가 안 된다」의 까닭이 화면 어디에도 없었다** — 정작 본체가 지는
        #   가장 흔한 원인이 여기인데 그랬다. 이름과 사유를 대고 다음 것으로 넘어간다.
        try { Add-AppxPackage -Path $d.FullName -ErrorAction Stop }
        catch { Write-Host "        ($($d.Name) — $(Say-Why $_))" }
      }
      $depPaths = @($deps | ForEach-Object { $_.FullName })
    }

    $pkg = $rel.assets | Where-Object { $_.name -like '*.msixbundle' } | Select-Object -First 1
    if (-not $pkg) { throw '릴리스에 msixbundle 이 없다' }
    $b = Join-Path $work $pkg.name
    $step = '본체를 못 받았다'
    Say-Get $pkg
    Get-Download $pkg.browser_download_url $b
    # ⚠ **여기도 조용한 자리다** — 206 MB 를 푸는 동안 한 글자도 안 나온다. 받기와 깔기가
    #   잇달아 조용하면 사람은 멎은 줄 알고 창을 닫는다. 들어가기 전에 말한다.
    Write-Host '      · 깐다 — 몇 분 걸린다. 멎은 것이 아니다'
    $step = '본체를 못 깔았다'
    # ⚠ **딸린 것을 같이 넘긴다 — 마이크로소프트가 적어 둔 꼴이다.** 위에서 하나씩 깐 뒤에도
    #   같이 넘기는 까닭은 **판 맞추기를 윈도우가 스스로 하게** 하려는 것이다: 따로 깔면
    #   순서와 판이 어긋날 여지가 남고, 그 어긋남은 「딸린 것을 못 찾는다」 한 줄로만 보인다.
    #   위 걸음이 다 져도 여기서 한 번 더 서는 자리이기도 하다.
    if ($depPaths.Count) { Add-AppxPackage -Path $b -DependencyPath $depPaths -ErrorAction Stop }
    else                 { Add-AppxPackage -Path $b -ErrorAction Stop }
    Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue

    if (& $reach) {
      Write-Host "  되살렸다 (GitHub 릴리스 $($rel.tag_name))" -ForegroundColor Green
      return $true
    }
    Write-Host '    · 깔았는데 winget 이 안 잡힌다 — 새 창에서는 잡힐 수 있다'
  } catch {
    Write-Host "    · $step — $(Say-Why $_)"
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
# ⚠ **소스를 뗀 칸을 따로 둔다.** 데스크탑 앱 하나가 **스토어 소스**에 살아서(위 표의
#   `Source`) 소스를 붙박이로 두면 그 앱을 부를 수가 없다. 나머지 칸은 아래 `$WG` 를 그대로
#   쓴다 — 붙이는 자리를 한 줄로 두어 둘이 안 갈리게 한다.
$WGOpts = @('--exact','--silent',
            '--accept-package-agreements','--accept-source-agreements','--disable-interactivity')
$WG = @('--source','winget') + $WGOpts

# ── 자리 — **프로그램 칸보다 앞이다.** 무엇을 깔지가 자리에 달렸기 때문이다(데스크탑 앱).
#    아래 4칸의 키 판정도 이 값을 다시 쓴다 — 한 번 재고 둘이 나눠 쓴다.
# ⚠ **자리는 셋이다 — 사내 · 사외 · 모름.** 프로브가 없으면 「사내」가 아니라 **모르는 것**이다.
#   둘로만 가르면 안 재고 사내라고 말하게 되고, 그 거짓 위에서 데스크탑 앱 같은 판정이 선다
#   (실측 2026-09-09: 프로브 없는 판이 「사내라 안 깐다」를 찍었다 — 잰 적이 없는데).
# ⚠ **화면이 이미 쟀으면 다시 안 잰다.** 같은 물음을 두 프로세스가 각각 물으면 **답이 갈릴
#   수 있고, 갈려도 아무 데도 안 찍힌다** — 프록시가 흔들리는 VDI · 무선 전환 · 회사망
#   재인증 순간이 그 자리다. 갈리면 화면이 받아 넘긴 키를 몸통이 버리거나(사내→사외), 주소가
#   빈 채로 게이트웨이를 쓴다고 서거나(사외→사내) 하는데 **둘 다 초록으로 끝난다.**
#   「규칙이 두 자리에 살면 한쪽만 낡는다」를 이 파일이 여러 곳에서 금하면서 여기서만 어겼다.
# ⚠ **넘어온 글자를 그대로 믿지 않는다** — 우리가 아는 둘 중 하나일 때만 받는다. 모르는 값을
#   받아 「사내」로 읽으면 **안 잰 것이 판정이 된다**(바로 위 ⚠ 의 「모름」이 그 자리다).
# ⚠ **콘솔 갈래에는 그 줄이 없다** — 그때는 지금처럼 여기서 잰다. 재는 자가 둘인 것이 결함이지
#   재는 자리가 둘인 것은 아니다.
$probe   = Read-Directive $EnvFile 'site-probe'
$site    = 'unknown'
$siteBy  = ''
$sitePassed = Read-Directive $EnvFile 'site'
if ($sitePassed -eq 'inside' -or $sitePassed -eq 'outside') {
  $site   = $sitePassed
  $siteBy = '화면이 쟀다'
} elseif ($probe) {
  $site   = if (Test-Reach $probe) { 'inside' } else { 'outside' }
  $siteBy = if ($site -eq 'inside') { '닿음' } else { '안 닿음' }
}
$offsite = ($site -eq 'outside')
if ($site -ne 'unknown') {
  Write-Host ("  자리 = {0}  ({1} {2})" -f
    $(if ($offsite) { '사외' } else { '사내' }), $probe, $siteBy)
  Write-Host ''
}

# ── 사내에서만 더 서는 것 셋 — 로컬 프록시 · Codex 회사 설정 · Gemini 회사 설정 (결정 0041 · 0045) ──
# ⚠ **몸통은 파일 이름도 모델 이름도 모른다.** 값 파일이 `#gateway-proxy = <프록시 파일>` ·
#   `#codex-config = <틀>` · `#gemini-config = <틀>` 로 이 폴더 안의 자리를 가리키고, 몸통은
#   **있고 사내면** 그것을 세운다. 사외는 셋 다 안 선다 — 구독·개인 로그인으로 서는 자리라서.
# ⚠ **프로그램은 이 스위치 밖이다.** Codex·Gemini 확장과 CLI 는 위 표대로 어디서나 깔린다 — 여기가
#   가르는 것은 그 프로그램을 **회사 키로 게이트웨이에 물리나**뿐이다(결정 0045).
# ⚠ **자리를 모르면 안 선다.** 프로브가 없으면 「사내」가 아니라 모르는 것이고, 모르는 자리에
#   프록시를 세우면 아무 데도 안 닿는 주소를 심은 채 초록으로 끝난다.
# ⚠ **`#config-repo` 가 있어도 여기서 세운다.** 옛 판은 그 줄이 있으면 프록시·설정을 저쪽 부트스트랩에
#   맡기고 **확장·CLI 까지 같은 스위치로 껐다** — 그런데 저쪽은 설정 파일만 쓰지 프로그램은 안 깔아,
#   그 판에서는 Codex·Gemini 를 아무도 안 깔았다(실측 2026-09-14 · 사내 VDI). 자리를 보고 세우는
#   자는 이 파일 하나고, 그 줄은 「다 세운 뒤 저장소를 더 받는다」는 뜻일 뿐이다.
$proxyRel   = Read-Directive $EnvFile 'gateway-proxy'
$codexTpl   = Read-Directive $EnvFile 'codex-config'
$geminiTpl  = Read-Directive $EnvFile 'gemini-config'
$inside     = ($site -eq 'inside')
$wantProxy  = [bool]($proxyRel  -and $inside)
$needPython = $wantProxy            # 프록시가 파이썬으로 돈다 — 개발도구를 꺼도 이것만은 깐다(1 칸)
# ⚠ **회사 설정도 제품 칸을 탄다** — 안 켠 제품에 회사 설정만 심어 두면 쓰지도 않는 파일이
#   남고, 나중에 그 파일을 보고 「깔렸나 보다」로 읽힌다.
$wantCodex  = [bool]($codexTpl  -and $inside -and ($PickKeys -contains 'codex'))
$wantGemini = [bool]($geminiTpl -and $inside -and ($PickKeys -contains 'gemini'))
# ⚠ **안티그래비티는 틀 파일이 없다** — 심을 것이 `modelProvider` 한 줄이라 틀을 실을 값이 없다.
#   그래서 무는 것은 「사내인가」와 「이 제품을 켰나」뿐이다.
# ⚠ **제미나이 칸에 안 묶는다.** 옛 판은 `$wantAgy = $wantGemini` 였는데, 제미나이를 끌 수 있게
#   되면서 그 줄이 안티그래비티까지 같이 껐다. 안티그래비티가 실제로 무는 것은 **환경변수 둘**
#   (`GEMINI_API_KEY` · `GOOGLE_GEMINI_BASE_URL`)이고 그 둘은 자리 값에서 따로 심긴다 —
#   제미나이의 **설정 파일**과는 별개다. 그래서 제미나이를 끈 자리에서도 이것은 선다.
$wantAgy    = [bool]($inside -and ($PickKeys -contains 'antigravity'))
# 회사 키의 다른 이름 표(`$KeyAliases`)의 `Need` 를 이 자리가 푼다 — 표는 이름만 들고 켜고 끄는 것은 여기다.
$wantNeed = @{ codex = $wantCodex; gemini = $wantGemini }
# ── 프록시가 밖에 남기는 자리 둘 — **이름은 여기 한 자리다** ─────────────────────
# ⚠ **심는 자와 걷는 자가 같은 이름을 봐야 한다.** 아래 5‴ 칸이 이 둘을 만들고, 사외로 갈린
#   판(5⁵ 칸)이 그것을 걷는다 — 두 자리에 글자를 따로 박으면 한쪽만 고쳐지는 날 **걷는 손이
#   딴 자리를 지우고 진짜 잔재는 그대로 돈다.** 지우는 손은 헛도는 줄도 안 남긴다.
$ProxyRunName = 'PGPTProxy'      # HKCU\...\Run 의 등록 이름
$ProxyDirName = 'PGPT-Proxy'     # %LOCALAPPDATA% 아래 실행 폴더 이름
# ── 회사 설정 둘이 앉는 자리 — **같은 까닭으로 여기 한 자리다** ─────────────────
# 아래 5⁗ 칸이 이 둘에 쓰고 끝의 검증이 이 둘을 다시 재므로, 글자를 두 자리에 박지 않는다 (#3).
$CodexCfg  = Join-Path $env:USERPROFILE '.codex\config.toml'
$GeminiCfg = Join-Path $env:USERPROFILE '.gemini\settings.json'
# ⚠ **안티그래비티는 제 파일을 따로 든다** — 위 `.gemini\settings.json` 이 아니라
#   `.gemini\antigravity-cli\settings.json` 이다. 같은 뿌리 아래 사는데 읽는 자가 달라, 한 파일로
#   묶으면 둘 중 하나가 못 읽는 열쇠를 받는다.
$AgyCfg    = Join-Path $env:USERPROFILE '.gemini\antigravity-cli\settings.json'
if ($proxyRel -or $codexTpl -or $geminiTpl) {
  $more = @()
  if ($wantProxy)  { $more += '로컬 프록시' }
  if ($wantCodex)  { $more += 'Codex 회사 설정' }
  if ($wantGemini) { $more += 'Gemini 회사 설정' }
  if ($wantAgy)    { $more += '안티그래비티 회사 설정' }
  if ($more.Count) { Write-Host ("  사내라 더 세운다 — " + ($more -join ' · ')); Write-Host '' }
  elseif (-not $inside) { Write-Host '  프록시와 Codex·Gemini 회사 설정은 사내에서만 선다 — 여기서는 프로그램만 깔고 각자 로그인으로 쓴다'; Write-Host '' }
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
# 「준비」 — 값 파일 읽기 · 자리 프로브 · winget 의 판 대조. [1/8] 앞에도 시간이 든다.
Write-Elapsed '준비'
Write-Host ''

Write-Host '[1/8] 프로그램' -ForegroundColor Cyan
foreach ($app in $Apps) {
  # ⚠ **VS Code 를 끄면 VS Code 만 안 깐다** — Node 는 CLI 가 타므로 `core` 로 남아 그대로 깔린다.
  if ($NoVsCode -and $app.Need -eq 'vscode') {
    Write-Host "  $($app.Name) — 건너뜀 (VS Code 칸을 껐다)"
    continue
  }
  if ($NoDevTools -and $app.Need -eq 'dev') {
    # ⚠ **파이썬만은 예외가 선다** — 사내 로컬 프록시가 파이썬으로 돈다(결정 0041). 개발도구를 끈
    #   사람도 프록시 없이는 Opus 5 와 Gemini 가 게이트웨이에 못 가므로, 사내면 이것만 깐다.
    if ($needPython -and $app.Cmd -eq 'python') {
      Write-Host "  $($app.Name) — 개발도구를 껐지만 깐다 (로컬 프록시가 이것으로 돈다)"
    } else {
      Write-Host "  $($app.Name) — 건너뜀 (-NoDevTools)"
      continue
    }
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
  # ⚠ **여기가 조용한 까닭을 먼저 말한다.** 아래에서 winget 이 뱉는 것을 통째로 파일로 돌리므로
  #   (바로 아래 까닭) **받고 까는 몇 분 동안 화면에 한 글자도 안 나온다.** 그 침묵은 멎은 것과
  #   구분이 안 되고, 사람은 그때 창을 닫는다 — 셋째 갈래에서 300 MB 로 이미 겪은 자리다.
  #   ⚠ **막대를 흘려서 푸는 것이 아니다.** 그러면 화면 껍데기의 기록 칸이 막대로 도배된다.
  #     조용한 것은 그대로 두고 **조용할 것이라고 미리 말한다.**
  Write-Host '    (winget 이 받아서 깐다 — 몇 분 조용하다. 멎은 것이 아니다)'
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

# ── 2′. 데스크탑 앱 — **자리가 언제를, 값 파일이 무엇을 정한다** ────────────────
# ⚠ **사내에는 쓸모가 없다 — 셋 다.** 게이트웨이를 물리는 `ANTHROPIC_BASE_URL` 을 읽는 것은
#   Claude Code CLI 뿐이고 앱에는 그 스위치가 없다 — 깔려도 제 본사로 나가려 하고 그 길이
#   막혀 있다. Codex·Gemini 앱도 각자 로그인으로 서는 자라 같은 자리다(결정 0045). 그래서
#   값 파일이 `#desktop-app = offsite` 를 들면 **사외로 판정될 때만** 깐다. `yes` 면 자리를
#   안 가리고 깐다. 없으면 안 깐다.
# ⚠ **값이 두 겹이다** — 앞은 **언제**(`offsite` · `yes`), `:` 뒤는 **무엇을**(위 표의 `Key`
#   를 쉼표로). 뒤엣것을 안 적으면 `claude` 하나다: **옛 값 파일이 한 자도 안 고치고 그대로
#   선다.** 통로를 새 스위치로 내지 않는 까닭은 머리글의 ⚠ 그대로 — 화면 갈래와 콘솔 갈래가
#   같은 줄을 타야 한쪽만 고쳐지는 자리가 안 난다.
#
#       #desktop-app = offsite                사외일 때 Claude        (옛 판과 같다)
#       #desktop-app = offsite:claude,codex   사외일 때 둘
#       #desktop-app = yes:gemini             자리를 안 가리고 Gemini
#
# ⚠ **GUI 앱이라 PATH 로 못 잰다.** `--version` 을 부를 이름이 안 생겨 다른 것들이 쓰는
#   프로브가 여기서는 안 선다 — winget 갈래는 winget 의 목록에, 제 설치본 갈래는 시작
#   메뉴에 묻는다.

# 있나 — **길마다 묻는 자가 다르다.** 종료코드를 판정으로 안 쓰는 것은 위 2 칸과 같은 결이다.
function Test-DesktopApp($A) {
  if ($A.Via -eq 'winget') {
    $tl = [IO.Path]::GetTempFileName()
    $rc = Invoke-Logged 'winget' @('list','--id',$A.Id,'--source',$A.Source) $tl
    Remove-Item $tl -ErrorAction SilentlyContinue
    return ($rc -eq 0)
  }
  # 제 설치본 갈래 — winget 이 모르는 앱이라 **윈도우에 묻는다.** 스토어 꼴이든 예전 꼴이든
  # 같은 답을 내는 자다(까닭은 아래 「연다」 칸의 ⚠ 에 적혀 있다).
  try { return [bool](@(Get-StartApps -ErrorAction Stop |
                        Where-Object { $_.Name -like "*$($A.App)*" })[0]) }
  catch { return $false }
}

# 깐다 — **실패를 우리가 분류하지 않는다.** 막히는 방식이 앱마다 다르고(소스 인증서 · 회선
# 정책 · 인자) 그 갈림을 코드표로 옮기면 **한 기계에서 본 것이 규칙 행세를 한다.** 대신 도구가
# 뱉은 끝 줄을 그대로 낸다 — 이 파일이 winget 실패에 이미 쓰는 자다.
function Install-DesktopApp($A) {
  Write-Host ''
  Write-Host "  $($A.Label)" -ForegroundColor Cyan
  if ($A.Via -eq 'winget' -and $noWinget) {
    Write-Host '  ! winget 이 없어 못 깐다' -ForegroundColor Red
    $script:Fails.Add("$($A.Label) (winget 이 없다)")
    return
  }
  if (Test-DesktopApp $A) {
    if (-not $NoUpgrade -and $A.Via -eq 'winget') {
      $ul = [IO.Path]::GetTempFileName()
      Invoke-Logged 'winget' (@('upgrade','--id',$A.Id,'--source',$A.Source) + $WGOpts) $ul | Out-Null
      Remove-Item $ul -ErrorAction SilentlyContinue
    }
    Write-Host '  있음'
    return
  }
  $al = [IO.Path]::GetTempFileName()
  $rc = $null
  if ($A.Via -eq 'winget') {
    $rc = Invoke-Logged 'winget' (@('install','--id',$A.Id,'--source',$A.Source) + $WGOpts) $al
  } else {
    # ⚠ **받는 자리와 도는 자리를 가른다.** 못 받은 것과 받았는데 진 것은 다른 명제이고,
    #   섞으면 회선이 막은 자리에서 「설치가 실패했다」만 남는다.
    $exe = Join-Path ([IO.Path]::GetTempPath()) ("{0}Setup.exe" -f $A.App)
    try {
      # ⚠ **주소의 끝마디가 아니라 받아 놓을 파일 이름을 댄다.** 주소가 파일 이름으로 끝나지
      #   않는 갈래가 있어(스토어 스텁은 제품 번호로 끝난다) 끝마디를 대면 `9PLM9XGG6VKS` 가
      #   찍힌다 — 받는 사람에게 아무 뜻이 없다.
      Write-Host ('      · 받는다 — {0}' -f (Split-Path $exe -Leaf))
      Get-Download $A.Url $exe
    } catch {
      Write-Host '  ! 설치본을 못 받았다' -ForegroundColor Red
      Say-Why $_
      $script:Fails.Add("$($A.Label) (설치본을 못 받았다)")
      Remove-Item $al -ErrorAction SilentlyContinue
      return
    }
    $pr = Start-Process -FilePath $exe -ArgumentList $A.SilentArgs -PassThru -Wait
    $rc = $pr.ExitCode
    Remove-Item $exe -ErrorAction SilentlyContinue
  }
  if (Test-DesktopApp $A) {
    Write-Host '  깔았다' -ForegroundColor Green
  } else {
    Write-Host ('  ! 설치 실패 — 낸 값 {0}' -f $rc) -ForegroundColor Red
    # 설치본이 제 로그를 남기는 갈래면 그 끝 줄을 댄다 — 회선이 막은 자리에서는 **막았다는
    # 말이 그 안에 그대로 들어 있다.**
    $log = $al
    if ($A.Log) {
      $own = [Environment]::ExpandEnvironmentVariables($A.Log)
      if (Test-Path -LiteralPath $own) { $log = $own }
    }
    Show-Log $log
    $script:Fails.Add($A.Label)
  }
  Remove-Item $al -ErrorAction SilentlyContinue
}

# ⚠ **이 줄이 드는 것은 「언제」뿐이다** — **무엇을** 깔지는 위 제품 칸(`$PickKeys`)이 든다.
#   옛 판은 `:` 뒤에 목록을 뒀는데, 고르는 축이 제품으로 서면서 그 목록은 자리를 잃었다.
#   ⚠ **들고 있으면 말하고 지나간다** — 조용히 무시하면 값 파일을 고친 사람은 제 줄이 죽은 줄 모른다.
$wantApp = Read-Directive $EnvFile 'desktop-app'
$appWhen = $wantApp
if ($wantApp -and $wantApp -match '^\s*([A-Za-z]+)\s*:\s*(.*?)\s*$') {
  $appWhen = $Matches[1]
  if ($Matches[2].Trim()) {
    Write-Host ''
    Write-Host ('  ! #desktop-app 의 : 뒤 목록은 이제 안 쓴다 — 무엇을 깔지는 제품 칸이 든다 (준 값: {0})' -f
                $Matches[2].Trim()) -ForegroundColor Yellow
  }
}
$appPicks = @($DesktopApps | Where-Object { $PickKeys -contains $_.Key })

if ($appWhen -eq 'yes' -or ($appWhen -eq 'offsite' -and $offsite)) {
  # ⚠ **빈 목록도 말한다** — 제품을 하나도 안 켠 판은 아무 일도 안 일어나고 한 줄도 안 찍혔다.
  if (-not $appPicks) {
    Write-Host ''
    Write-Host '  데스크탑 앱 — 켠 제품이 없어 안 깐다'
  }
  foreach ($da in $appPicks) { Install-DesktopApp $da }
} elseif ($appWhen -eq 'offsite') {
  Write-Host ''
  # ⚠ **안 깐 까닭을 정확히 댄다.** 「사내라」와 「자리를 몰라」는 다른 명제고, 뒤엣것은
  #   고칠 수 있는 것이다 — 값 파일에 `#site-probe` 를 넣으면 잰다.
  if ($site -eq 'inside') {
    Write-Host '  데스크탑 앱 — 사내라 안 깐다 (게이트웨이를 못 문다)'
  } else {
    Write-Host '  데스크탑 앱 — 자리를 몰라 안 깐다 (값 파일에 #site-probe 가 없다)'
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
# ⚠ **하나를 까는 걸음이 한 자리다.** 확장이 셋으로 늘면서(결정 0041) 같은 걸음을 세 번 적으면
#   한 번 겪은 사고(곧바로 물으면 아직 없다 · 인증서면 다른 병이다)가 두 사본에서 다시 난다.
# ⚠ **긴 명령 앞에 한 줄을 먼저 찍는다.** 화면 껍데기의 상태 줄은 마지막으로 나온 줄을 그대로
#   보이므로, 끝나고 나서만 찍으면 그 몇십 초 동안 **직전 칸의 결과**가 「지금 하는 일」로 서 있다
#   (실측 2026-09-15 · 사외 VDI: Codex 확장을 받는 동안 「클로드 확장 — 최신」이 떠 있었다).
# ⚠ **`code` 를 띄우는 횟수가 곧 시간이다.** 한 번 뜰 때마다 노드 프로세스가 새로 서고 마켓플레이스에
#   한 번 묻는데, 이 값이 VDI 에서는 몇 초씩이다. 옛 판은 확장 하나마다 셋(판 번호 → `--force` → 판 번호)을
#   띄워 셋이면 아홉이었다. 판 번호는 **한 번** 읽고, 깔린 것들은 `--update-extensions` **한 번**으로 올리고,
#   다시 한 번 읽어 앞뒤로 「올렸다 · 최신」을 가른다 — 셋이 다 깔린 판에서 셋으로 준다.
# ⚠ **`--force` 가 최신을 다시 받지는 않는다** — 실측 2026-09-15: 같은 판이면 `already installed` 만 찍고
#   1초에 끝난다. 옛 주석이 「다시 깐다」고 적었던 것은 틀렸고, 느렸던 까닭은 위 횟수다.
# ⚠ **`--update-extensions` 는 깔린 확장 전부를 올린다** — 우리 셋만 고르는 스위치가 없다. VS Code 가
#   스스로 하는 자동 갱신과 같은 일이라 더 하는 것은 없다.
function Get-ExtVersions {
  $m = @{}
  foreach ($l in (Get-Quiet 'code' @('--list-extensions','--show-versions'))) {
    if ($l -match '^(.+)@([^@]+)$') { $m[$Matches[1]] = $Matches[2] }
  }
  return $m
}
function Install-Extension([string]$Id, [string]$Label, [hashtable]$Before, [hashtable]$After) {
  if ($Before.ContainsKey($Id)) {
    $b = $Before[$Id]; $a = $After[$Id]
    if ($NoUpgrade)             { Write-Host "  $Label — 있음  ($b)" }
    elseif ($a -and $a -ne $b)  { Write-Host "  $Label — 올렸다  $b  ->  $a" -ForegroundColor Green }
    else                        { Write-Host "  $Label — 최신  ($b)" }
    return
  }
  Write-Host "  $Label 설치중 …"
  $xl = [IO.Path]::GetTempFileName()
  $rc = Invoke-Logged 'code' @('--install-extension',$Id,'--force') $xl
  # ⚠ **곧바로 물으면 아직 없을 수 있다.** VS Code 가 떠 있으면 설치가 그 인스턴스로 넘어가고
  #   명령은 바로 돌아온다 — 그때 목록을 물으면 「없다」가 나와 멀쩡한 설치가 실패로 찍힌다.
  #   몇 초를 두고 다시 묻는다. 없는 것을 오래 기다리지는 않는다.
  $ext = Get-Quiet 'code' '--list-extensions'
  if ($ext -notcontains $Id) {
    for ($i = 0; $i -lt 5; $i++) {
      Start-Sleep -Seconds 2
      $ext = Get-Quiet 'code' '--list-extensions'
      if ($ext -contains $Id) { break }
    }
  }
  if ($ext -contains $Id) {
    Write-Host "  $Label — 깔았다" -ForegroundColor Green
  } else {
    # ⚠ **까닭을 편다.** 「! 설치 실패」 한 줄만 내면 다음 사람이 열어 볼 자리가 없다 —
    #   이 자리에서 실제로 그랬다(실측 2026-09-09 · 사외 VDI).
    Write-Host "  ! $Label 설치 실패 (code 가 $rc 로 끝났다) — 뱉은 끝 줄:" -ForegroundColor Red
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
    Write-Host "     손으로 재려면:  code --install-extension $Id --force"
    $Fails.Add("VS Code 확장 ($Label)")
  }
  Remove-Item $xl -ErrorAction SilentlyContinue
}

Write-Elapsed '[1/8] 프로그램'
Write-Host ''
Write-Host '[2/8] VS Code 확장' -ForegroundColor Cyan
# 고른 제품의 확장만 든다 — 목록이 진본이고 고르는 축은 `$Products` 다.
$ExtPicks = @($Extensions | Where-Object { $PickKeys -contains $_.Key })
if ($NoVsCode) {
  Write-Host '  건너뜀 — VS Code 칸을 껐다 (확장은 VS Code 없이 설 자리가 없다)'
} elseif (Test-Runs 'code' '--version') {
  $extBefore = Get-ExtVersions
  $extAfter  = $extBefore
  $extHave   = @($ExtPicks | Where-Object { $extBefore.ContainsKey($_.Id) })
  if ($extHave.Count -gt 0 -and -not $NoUpgrade) {
    Write-Host "  깔린 확장 $($extHave.Count)개 — 최신인지 확인중 …"
    $xl = [IO.Path]::GetTempFileName()
    Invoke-Logged 'code' @('--update-extensions') $xl | Out-Null
    Remove-Item $xl -ErrorAction SilentlyContinue
    $extAfter = Get-ExtVersions
  }
  if (-not $ExtPicks) { Write-Host '  고른 제품이 없어 확장을 안 깐다' }
  foreach ($x in $ExtPicks) { Install-Extension $x.Id $x.Label $extBefore $extAfter }
} else {
  Write-Host '  ! code 를 못 불러 건너뛴다 — VS Code 설치부터 본다' -ForegroundColor Red
  $Fails.Add('VS Code 확장 (code 가 안 닿는다)')
}

# ── 4. CLI 셋 — 어디서나 (회사 키로 물리나는 5″·5⁗ 이 가른다) ─────────────────────
# ⚠ **npm 으로 까는 걸음이 한 자리다** — 확장 칸과 같은 까닭. 판정은 `--version` 이 도나(프로브)다.
function Install-NpmCli([string]$Pkg, [string]$Cmd, [string]$Label) {
  if ((Test-Runs $Cmd '--version') -and ($NoUpgrade -or -not (Test-Runs 'npm' '--version'))) {
    Write-Host "  $Label — 있음 ($(Get-Ver $Cmd '--version'))"
  } elseif (Test-Runs $Cmd '--version') {
    $b = Get-Ver $Cmd '--version'
    Write-Host "  $Label 판 확인중 … (지금 $b)"     # 나가는 명령 앞의 한 줄 — 확장 칸과 같은 까닭
    # ⚠ **먼저 묻고 다르면 깐다 — 판정 수단으로 설치를 돌리지 않는다.** 옛 판은 「최신인가」를
    #   알려고 `npm install` 을 돌렸다: 같은 판이어도 npm 이 풀이·다운로드·링크를 다시 밟아
    #   이 걸음이 셋 합쳐 121초였다(실측 v1.12.0 두 번째 판 · 사내 VDI · 설치기 전체의 40%).
    #   판 하나 묻는 GET 은 어느 기계에서도 1초 안팎이다. 사외 VDI 는 **로그인마다** 이 걸음을 지난다.
    # ⚠ **묻는 것도 `@latest` 로 묻는다.** install 이 보는 태그와 다른 것을 물으면 엉뚱한 판과
    #   견주게 되고, 그 어긋남은 「올렸는데 또 올린다」로만 드러나 아무도 안 잡는다.
    $rvo = Get-Quiet 'npm' @('view',"$Pkg@latest",'version') | Select-Object -First 1
    $vrc = $LASTEXITCODE
    $rv  = ("$rvo").Trim()
    # 깔린 판 문자열은 꼴이 셋이다 — `2.1.273 (Claude Code)` · `codex-cli 0.154.0` · `0.60.0`.
    # 그래서 같음을 등호로 못 재고 **「깔린 문자열이 레지스트리 판을 낱말로 품나」**로 잰다.
    # ⚠ **경계를 `\b` 로 잡지 않는다.** `\b` 는 점을 경계로 쳐서 `1.2.1.273` 이 `2.1.273` 을 품은
    #   것으로 읽힌다 — 판 문자열에서 점은 구분자가 아니라 판의 일부다. 앞뒤로 글자도 점도 오지
    #   않기를 요구해야 `2.1.2730` 과 `1.2.1.273` 이 함께 걸러진다.
    $same = $rv -and ($b -match "(?<![\w.])$([regex]::Escape($rv))(?![\w.])")
    # ⚠ **여기서 지는 둘(못 물음 · 못 올림)을 실패로 세지 않는다.** 그 CLI 는 이미 깔려 있고 옛
    #   판으로 돈다 — 저장소 `pull` 이 졌을 때와 같은 꼴이라(8 칸) 같은 규율로 든다: 말은 하되
    #   빨강으로 안 끝낸다.
    if ($vrc -ne 0 -or -not $rv) {
      # ⚠ **못 물었을 때 「최신」이라 찍지 않는다.** 사내 프록시가 `registry.npmjs.org` 를 막았거나
      #   Node 가 CA 를 몰라 죽은 판에서도 깔린 판은 그대로다 — 거기서 「최신」을 찍으면 **낡은 판이
      #   도는 것과 최신이 도는 것을 못 가른다.** install 을 돌려 보는 갈래도 안 둔다: 못 닿는
      #   레지스트리에는 install 도 못 닿는다.
      Write-Host "  ! $Label — 레지스트리에 판을 못 물었다 (npm view 가 $vrc 로 끝났다) · 옛 판 $b 로 간다" -ForegroundColor Yellow
    } elseif ($same) {
      Write-Host "  $Label — 최신  ($b)"
    } else {
      Write-Host "  $Label 갱신중 … ($b  ->  $rv)"
      $nl = [IO.Path]::GetTempFileName()
      # ⚠ **종료코드를 안 버린다 — 여기는 winget 자리가 아니다.** 저쪽(2 칸)은 「올릴 것 없음」에도
      #   0 이 아닌 값을 내서 버릴 **까닭이 적혀 있지만**, npm 은 지면 지는 값을 낸다. 버리고 판만
      #   견주면 설치가 죽은 판에서도 판이 안 바뀌었으니 아래 마지막 갈래로 새어 **「최신」이 찍힌다.**
      #   로그도 곧바로 지워 단서가 없었다.
      $nrc = Invoke-Logged 'npm' @('install','-g',"$Pkg@latest") $nl
      Update-RuntimePath
      $a = Get-Ver $Cmd '--version'
      if ($a -and $a -ne $b) { Write-Host "  $Label — 올렸다  $b  ->  $a" -ForegroundColor Green }
      elseif ($nrc -ne 0) {
        Write-Host "  ! $Label — 올리기 실패 (npm 이 $nrc 로 끝났다) · 옛 판 $b 로 간다 — 뱉은 끝 줄:" -ForegroundColor Yellow
        Show-Log $nl
      }
      else { Write-Host "  $Label — 최신  ($b)" }
      Remove-Item $nl -ErrorAction SilentlyContinue
    }
  } elseif (Test-Runs 'npm' '--version') {
    Write-Host "  $Label 설치중 …"
    $nl = [IO.Path]::GetTempFileName()
    $nrc = Invoke-Logged 'npm' @('install','-g',$Pkg) $nl
    # ⚠ **깔고 나서 한 번 더 태운다.** `%APPDATA%\npm` 은 이 설치가 **만드는** 폴더라,
    #   맨바닥 PC 에서는 앞의 배선이 조용히 지나가고 PATH 가 빈 채로 남는다. 두 번째부터는
    #   폴더가 있어 안 드러나는, 맨바닥에서만 나는 갈래다.
    Update-RuntimePath
    if (Test-Runs $Cmd '--version') {
      Write-Host "  $Label — 깔았다 ($(Get-Ver $Cmd '--version'))" -ForegroundColor Green
    } else {
      Write-Host "  ! $Label 설치 실패 (npm 이 $nrc 로 끝났다) — 뱉은 끝 줄:" -ForegroundColor Red
      Show-Log $nl
      $Fails.Add($Label)
    }
    Remove-Item $nl -ErrorAction SilentlyContinue
  } else {
    Write-Host "  ! npm 이 없어 $Label 를 못 깐다 — Node.js 설치부터 본다" -ForegroundColor Red
    $Fails.Add("$Label (npm 이 안 닿는다)")
  }
}

# winget 이 내주는 CLI. **깔렸으면 올리기만 시도한다** — npm 갈래와 달리 이 자리가 공짜다.
# ⚠ **여기서 묻는 자는 `winget list` 가 아니라 `--version` 이다.** 데스크탑 갈래는 GUI 라 PATH 로
#   못 재서 winget 의 목록에 묻지만(위 `Test-DesktopApp`), CLI 는 **사람이 쓸 이름이 실제로 서는가**가
#   판정이다. 둘은 다른 명제다 — winget 이 「깔았다」 해도 그 이름이 PATH 에 안 서면 못 쓴다.
# ⚠ **올리기가 조용히 지나가는 자리가 있다** — 옛 벤더 스크립트로 깐 기계의 `agy` 는 winget 이
#   모른다. 그때 `--version` 은 서므로 「있음」으로 지나가고 `winget upgrade` 는 아무것도 안 한다.
#   **그것을 실패로 안 찍는다**: 도구는 멀쩡히 서 있고, 걷어낼지는 사람이 정할 일이다.
function Install-WingetCli([string]$Id, [string]$Cmd, [string]$Label) {
  if (Test-Runs $Cmd '--version') {
    if (-not $NoUpgrade -and -not $noWinget) {
      $ul = [IO.Path]::GetTempFileName()
      Invoke-Logged 'winget' (@('upgrade','--id',$Id) + $WG) $ul | Out-Null
      Remove-Item $ul -ErrorAction SilentlyContinue
    }
    Write-Host "  $Label — 있음 ($(Get-Ver $Cmd '--version'))"; return
  }
  if ($noWinget) {
    Write-Host "  ! winget 이 없어 $Label 를 못 깐다" -ForegroundColor Red
    $Fails.Add("$Label (winget 이 없다)")
    return
  }
  Write-Host "  $Label 설치중 … (winget · $Id)"
  $wl = [IO.Path]::GetTempFileName()
  $rc = Invoke-Logged 'winget' (@('install','--id',$Id) + $WG) $wl
  # ⚠ **깐 직후에는 이 창이 그 자리를 모른다** — winget 이 portable 을 심으면서 손댄 PATH 는
  #   레지스트리에만 있다(실측: 이 기계의 사용자 PATH 에 winget 이 심은 자리가 셋 서 있다).
  Update-RuntimePath
  if (Test-Runs $Cmd '--version') {
    Write-Host "  $Label — 깔았다 ($(Get-Ver $Cmd '--version'))" -ForegroundColor Green
  } else {
    # ⚠ **「됐다는데 안 잡힌다」를 「안 됐다」로 안 적는다** — 다음에 어디를 팔지가 갈린다.
    #   이 갈래가 winget 이 PATH 를 안 들어 준 자리를 잡는 자다.
    Write-Host "  ! $Label — 설치가 $rc 로 끝났는데 $Cmd 가 안 잡힌다 — 뱉은 끝 줄:" -ForegroundColor Red
    Show-Log $wl
    Write-Host "     새 터미널에서 다시 보고, 그래도 없으면:  winget install --id $Id --source winget"
    $Fails.Add("CLI ($Label)")
  }
  Remove-Item $wl -ErrorAction SilentlyContinue
}

Write-Elapsed '[2/8] VS Code 확장'
Write-Host ''
Write-Host '[3/8] CLI' -ForegroundColor Cyan
$CliPicks = @($Clis | Where-Object { $PickKeys -contains $_.Key })
if (-not $CliPicks) { Write-Host '  고른 제품이 없어 CLI 를 안 깐다' }
foreach ($c in $CliPicks) {
  if ($c.Via -eq 'winget') { Install-WingetCli $c.Id  $c.Cmd $c.Label }
  else                     { Install-NpmCli    $c.Pkg $c.Cmd $c.Label }
}
# ⚠ **사외는 여기서 로그인 길을 댄다.** 회사 설정 칸(5⁗)이 안 서는 자리라 아무도 안 알려 주면
#   깔린 채로 「왜 안 되지」가 된다 — 프로그램은 섰고 자격만 사람 몫이라는 것을 한 줄로 둔다.
if (-not $inside) {
  Write-Host '  사외 — Codex 는 `codex login`(ChatGPT), Gemini 는 `gemini` 첫 실행의 Google 로그인으로 쓴다'
}

Write-Elapsed '[3/8] CLI'
# ── 5. 값 — 파일이 들면 읽고, 없으면 묻는다 ─────────────────────────────────────
# ⚠ **`#config-repo` 가 있어도 여기서 받는다.** 옛 판은 그 줄이 있으면 안 묻고 저쪽 부트스트랩이
#   제 파일로 심게 넘겼다 — 그러면 저장소에 부트스트랩이 없는 사람은 키가 어디에도 안 심긴다.
#   회사 키는 설치 창(또는 `install.env`)이 받고 이 파일이 심는다. 저쪽이 드는 것은 사람에게
#   딸린 것(개인 키 · 형제 저장소)이지 이 칸이 아니다.
Write-Host ''
Write-Host '[4/8] 키와 주소' -ForegroundColor Cyan
$fromFile  = Read-EnvFile $EnvFile
if ($fromFile.Count -gt 0) { Write-Host "  install.env 가 $($fromFile.Count)개를 든다" }

# ⚠ **주소가 곧 판정이다.** 주소가 없으면 게이트웨이를 안 쓰는 자리이고, 그러면 키도 안 묻고
#   없다고 물지도 않는다 — 사외 VDI 가 그 자리다(구독 로그인으로 선다). 옛 판은 둘을 「무조건
#   필요」로 두어, 안 쓰는 자리에서도 넣으라고 하고 안 넣으면 빨갛게 끝냈다.
$useGateway = $true
# 값 파일이 든 게이트웨이 값 — **버리기 전에 쥔다.** 아래 5⁵ 칸이 「사용자 환경에 남은 이것이
# 우리 것인가」를 이 값으로 가른다. 버린 뒤에 물으면 남의 키와 우리 키를 못 갈라, **걷어도
# 되는 것만 걷는다**는 규율이 아예 못 선다.
$ourGateway = @{}

# ⚠ **자리가 값보다 먼저다.** 값 파일이 사내 값을 들고 있어도, 사내에 안 닿는 자리라면 그 값은
#   여기서 쓸 것이 아니다 — 배포본은 사내용으로 뽑히므로 그 파일을 사외 PC 에서 돌리는 일이
#   실제로 난다. 그때 사내 주소를 심으면 안 닿는 곳을 가리킨 채 「설정됐다」로 보인다.
if ($probe) {
  if ($site -eq 'inside') {
    Write-Host "  사내다 — 게이트웨이를 쓴다"
  } else {
    Write-Host "  사외다 — 게이트웨이를 안 쓴다"
    Write-Host '    구독 로그인으로 섭니다 (claude auth login)'
    $useGateway = $false
    # 값 파일이 든 사내 값을 **버린다.** 안 버리면 아래 루프가 그대로 심는다.
    foreach ($v in $Vars) {
      if (-not $v.Gateway) { continue }
      if ($fromFile[$v.Name]) { $ourGateway[$v.Name] = $fromFile[$v.Name] }
      $fromFile.Remove($v.Name)
    }
  }
}

if ($useGateway) {
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

  if (-not $val -and -not $Yes) {
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
    if ($v.Gateway -and $useGateway) {
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
# ⚠ **여기에도 자리 게이트가 선다.** 위 표 갈래는 `Gateway` 표시로 사외를 걸러 내는데 이 칸은
#   **아무것도 안 걸러, 사외로 판정한 기계에도 프록시 주소를 심었다**(실측 2026-09-17 집 PC:
#   `GOOGLE_GEMINI_BASE_URL` 이 안 서는 `127.0.0.1:18901` 을 가리킨 채 남았다). 그 값은 조용히
#   안 진다 — **프로그램은 멀쩡히 서고 나갈 때만 죽은 포트로 나간다.**
# ⚠ **표시가 아니라 값이 가른다**(위 `Test-ProxyValue`). 값 파일은 늘어나고 표는 안 늘어난다.
$known = $Vars | ForEach-Object { $_.Name }
foreach ($k in $fromFile.Keys) {
  if ($known -contains $k) { continue }
  $val = $fromFile[$k]
  if (-not $val) { continue }
  if (-not $useGateway -and (Test-ProxyValue $val)) {
    Write-Host "  $k — 안 심는다 (사외라 프록시가 안 선다: $val)" -ForegroundColor Yellow
    continue
  }
  Plant-Var $k $val
}

# ── 5‴. 물러난 이름 — **심는 것만으로는 못 걷는다** ─────────────────────────────
# ⚠ 심기는 더하기만 한다. 진본에서 이름 하나를 걷으면 새로 깔는 기계에는 안 서지만, **한 번
#   깔았던 기계에는 그 값이 그대로 남는다** — 다시 깔아도 남는다. 옛 값이 살아 있는 채로
#   설치는 초록으로 끝나고, 어긋남은 그 사람 화면에서만 보인다(실측 2026-09-15:
#   `ANTHROPIC_CUSTOM_MODEL_OPTION` 을 진본에서 걷고 다시 뽑았는데 `/model` 목록에 그 줄이
#   그대로 섰다 — 사용자 환경에 박힌 값이 들고 있었다). 씨앗이 「없을 때만」 깔려 오래 쓴
#   기계가 뒤처지는 것($Features 곁말)과 같은 병이고, 이쪽은 **지우는 손**이 없어서 난다.
# ⚠ **값이 아니라 이름만 든다.** 무엇으로 되돌릴지가 아니라 「이 이름은 이제 우리 것이 아니다」를
#   적는 자리다 — 값을 적으면 걷은 것을 다시 심는 목록이 된다.
# ⚠ **걷는 자리가 둘이다 — 여기(사용자 환경)와 아래 홈 설정 칸(`settings.json` 의 `env`).**
#   `Plant-Var` 가 두 자리에 심으므로 걷기도 둘이어야 한다. 한쪽만 걷으면 나머지가 남아,
#   아래 「우리가 안 심은 `ANTHROPIC_` 이름」 검사가 그것을 물어 **설치가 빨강으로 끝난다**
#   (실측 2026-09-15: 사용자 PC 가 `ANTHROPIC_CUSTOM_MODEL_OPTION 이 홀로 있다` 로 안 끝났다).
# ⚠ **이름을 영영 두지 않는다.** 다 걷힌 뒤에도 남으면 남의 값을 지우는 손이 된다 — 같은 이름을
#   제 뜻으로 쓰는 사람이 있을 수 있다. 두 판쯤 지나면 지운다.
# 이름이 늘면 여기 한 줄. **`install.env` 가 그 이름을 들면 위 칸이 이기고 여기는 비켜선다** —
#   진본이 되살린 것을 이 목록이 지우면 두 자리가 싸운다.
$Retired = @(
  # 0048 — 고를 모델은 씨앗의 `modelPicker` 가 든다. 이 칸은 게이트웨이 갈래에서 창을 200k 로
  #        이고 서서 같은 모델을 1M 으로 못 냈다. 4.7 은 그 목록 줄로 산다.
  'ANTHROPIC_CUSTOM_MODEL_OPTION'
)
foreach ($k in $Retired) {
  if ($fromFile.ContainsKey($k)) { continue }   # 진본이 되살렸으면 안 건드린다
  if (-not [Environment]::GetEnvironmentVariable($k, 'User')) { continue }
  try {
    [Environment]::SetEnvironmentVariable($k, $null, 'User')
    Remove-Item -Path "Env:$k" -ErrorAction SilentlyContinue   # 이 창에서도 걷는다 (Plant-Var 와 짝)
    Write-Host "  $k — 걷었다 (이제 안 쓰는 이름)" -ForegroundColor Green
  } catch {
    Write-Host "  ! $k 걷기 실패 — $(Say-Why $_)" -ForegroundColor Red
    $Fails.Add("$k 걷기")
  }
}

# ── 5″. 회사 키의 다른 이름 둘 — **한 번 받은 것을 이름만 바꿔 심는다** ─────────────
# ⚠ 회사 키는 하나인데 읽는 이름이 셋이다 — Claude Code 는 `ANTHROPIC_AUTH_TOKEN`, Codex CLI 는
#   `config.toml` 의 `env_key` 가 가리키는 `OPENAI_API_KEY`, Gemini CLI 는 `GEMINI_API_KEY`. 사람에게
#   세 번 물으면 같은 값이 세 자리에 산다 — 한 번 받아 **파생**한다(결정 0041).
# ⚠ **필요한 것만 심는다.** 그 CLI 를 안 세우는 자리(사외 · 자리 모름)에 이 이름을 심으면, 같은
#   이름을 다른 뜻으로 쓰는 도구(구글 직결 키)가 회사 키를 집어 조용히 죽는다.
$KeyAliases = @(
  @{ Name='OPENAI_API_KEY'; Need='codex'  }
  @{ Name='GEMINI_API_KEY'; Need='gemini' }
)
if ($useGateway -and $Planted['ANTHROPIC_AUTH_TOKEN']) {
  foreach ($k in $KeyAliases) {
    if (-not $wantNeed[$k.Need]) { continue }
    Plant-Var $k.Name $Planted['ANTHROPIC_AUTH_TOKEN']
  }
  # ── 회사 키를 제치는 이름 하나 — **말은 하고 지우지는 않는다** (실측 2026-09-17 · #62) ──
  # ⚠ **이것은 부재가 아니라 잔재가 이기는 자리다.** `GOOGLE_API_KEY` 가 남아 있으면 `agy` 와
  #   Gemini 갈래가 **회사 키를 제치고 그쪽을 집는다** — 제가 그렇게 말한다:
  #     `Warning: Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY.`
  #   그러면 답은 오는데 **게이트웨이가 아니라 구글에서 온다.** 답이 왔다는 것과 게이트웨이가
  #   답했다는 것은 다른 명제고, 이 자리에서 실제로 두 판을 헛짚었다(프록시 로그에 그 호출이
  #   없는 것이 가른 자다).
  # ⚠ **그런데 안 지운다.** 이것은 우리가 심은 이름이 아니라 **구글 직결 키의 제 이름**이라,
  #   제 것을 넣어 둔 사람의 자격을 설치기가 걷으면 그 사람의 다른 일이 죽는다. 아래 5⁵ 칸이
  #   「남의 값은 안 걷는다」로 세운 그 자와 같은 자리다 — **근거가 안 서면 말만 한다.**
  #   찍어 두면 화면에 남아, 회사 키로 서야 하는데 안 서는 사람이 열어 볼 자리가 생긴다.
  if ($wantNeed['gemini'] -and [Environment]::GetEnvironmentVariable('GOOGLE_API_KEY', 'User')) {
    Write-Host '  ! GOOGLE_API_KEY 가 사용자 환경에 있다 — Gemini·안티그래비티가 회사 키 대신 이것을 집는다' -ForegroundColor Yellow
    Write-Host '     구글 직결 키의 제 이름이라 설치기가 안 걷는다. 회사 게이트웨이로 쓰려면 손으로 걷는다 (시스템 환경 변수)'
  }
}

# ── 홈 `settings.json` 에 안 미는 이름 — **키는 환경변수에만 산다** (#2) ────────────
# ⚠ **목록을 손으로 적지 않는다.** 키는 하나인데 이름이 셋이라(위 ⚠), 손으로 적으면 넷째
#   이름이 느는 날 이 목록만 안 늘어 **그 하나가 조용히 파일로 샌다.** 표에서 파생한다 —
#   비밀이라고 표가 이미 말한 것(`Secret`)과 그 비밀의 다른 이름들(`$KeyAliases`)이다.
$SettingsEnvSkip = @($Vars | Where-Object { $_.Secret } | ForEach-Object { $_.Name }) +
                   @($KeyAliases | ForEach-Object { $_.Name })

# ── 5⁵. 사외로 간 자리의 사내 잔재 — **심은 자리마다 걷는 자가 있다** ───────────────
# ⚠ **부재가 아니라 잔재가 통과로 읽히는 자리다.** 위 칸들은 *이번 판에 심을 목록*에서만
#   게이트웨이 이름을 빼는데, **이미 `HKCU\Environment` 에 박힌 옛 값은 아무도 안 건드린다.**
#   사내 VDI 에서 한 번 깐 노트북을 집에 가져와 다시 돌리면 「사외다 — 게이트웨이를 안 쓴다」를
#   찍은 뒤 그 이름들을 **검증에서까지 뺐고**(아래 `if ($useGateway)`), 화면은 전부 [O] 였다.
#   그런데 CLI 는 남은 `ANTHROPIC_BASE_URL` 을 물고 **닿지 않는 루프백으로 나간다** — 구독
#   로그인이 서 있어도 그쪽이 안 쓰인다. 5‴ 칸이 「물러난 이름」에만 쓴 규율을 여기 마저 쓴다.
# ⚠ **남의 값은 안 걷는다.** 같은 이름을 제 뜻으로 쓰는 사람이 있다 — 특히 별칭 둘은 구글·
#   오픈AI 직결 키의 이름이기도 하다(5″ 칸 ⚠ 가 심을 때 이미 든 까닭). 그래서 **우리 것이라는
#   근거가 설 때만** 걷는다:
#     · 주소 — 값 파일이 든 그 주소와 같거나, **루프백**이거나. 루프백이 근거가 되는 까닭은
#       아래 5‴ 칸이 루프백이 아닌 주소에는 프록시를 **안 세우기** 때문이다 — 루프백으로 박힌
#       `ANTHROPIC_BASE_URL` 은 이 설치기의 게이트웨이 갈래 말고는 나올 자리가 없다.
#     · 별칭 둘 — 우리가 지금 걷는 그 토큰과 값이 같을 때만. 5″ 칸이 **같은 값을 이름만 바꿔**
#       심으므로, 값이 같다는 것이 곧 「이것도 우리가 심은 것」이다.
#   ⚠ **근거가 안 서면 안 걷고 그냥 둔다.** 회사 주소가 루프백이 아니고 값 파일도 그 줄을 안
#     들고 온 판(화면 갈래의 사외)에서는 우리 것과 남의 것을 못 가른다 — 못 가르면 안 건드리는
#     쪽으로 기운다. 그때는 아래 검증이 [X] 로 남겨, 조용히 지나가지는 않는다.
if (-not $useGateway) {
  Write-Host ''
  Write-Host '  사내 잔재' -ForegroundColor Cyan
  function Remove-UserVar([string]$Name) {
    try {
      [Environment]::SetEnvironmentVariable($Name, $null, 'User')
      Remove-Item -Path "Env:$Name" -ErrorAction SilentlyContinue   # 이 창에서도 걷는다 (Plant-Var 와 짝)
      Write-Host "  $Name — 걷었다 (사외라 안 쓴다)" -ForegroundColor Green
    } catch {
      Write-Host "  ! $Name 걷기 실패 — $(Say-Why $_)" -ForegroundColor Red
      $script:Fails.Add("$Name 걷기")
    }
  }

  $oldUrl = [Environment]::GetEnvironmentVariable('ANTHROPIC_BASE_URL', 'User')
  $oldKey = [Environment]::GetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'User')
  # ⚠ **못 읽는 글자를 예외에 맡기지 않는다.** `[Uri]'아무 글자'` 는 **상대 주소로 선다** —
  #   던지지 않고, 그 위의 `.IsLoopback` 은 5.1 에서 **오류 없이 `$null` 을 준다.** 그래서
  #   `try/catch` 로 감싼 판은 한 번도 안 걸리고 판정 변수에 참·거짓이 아니라 **빈 것**이 앉았다
  #   (실측 2026-09-15 · 이 고침의 되뽑기). 지금은 거짓처럼 굴어 표가 안 나지만, 그 값을
  #   견주거나 찍는 줄이 하나 붙는 날 「모른다」가 「아니다」로 조용히 읽힌다.
  #   **닫힌 것 위에 세운다** — 루프백을 물을 수 있는 것은 절대 주소뿐이고, 나머지는 남의 것이다.
  # ⚠ **그 판정을 여기 또 적지 않는다** — 위 `Test-ProxyValue` 가 같은 물음을 든다. 옛 판은 이
  #   자리에 손으로 폈는데, 같은 규칙이 두 자리에 살면 한쪽만 낡는다(갈래 검사가 실제로 저쪽에만 붙었다).
  $oursUrl = $false
  if ($oldUrl) {
    $oursUrl = ($ourGateway['ANTHROPIC_BASE_URL'] -and $oldUrl -eq $ourGateway['ANTHROPIC_BASE_URL']) -or
               (Test-ProxyValue $oldUrl)
  }

  if (-not $oldUrl) {
    Write-Host '  ANTHROPIC_BASE_URL — 없다 (걷을 것이 없다)'
  } elseif (-not $oursUrl) {
    # ⚠ **모르는 주소를 지우지 않는다** — 다만 말은 한다. 이것이 살아 있으면 구독 로그인이
    #   서 있어도 CLI 는 이쪽으로 나간다.
    Write-Host "  ! ANTHROPIC_BASE_URL 이 우리 것이 아니다 — 안 걷는다 ($oldUrl)" -ForegroundColor Yellow
    Write-Host '     구독 로그인으로 서려면 이 이름을 손으로 걷는다 (시스템 환경 변수)'
  } else {
    Remove-UserVar 'ANTHROPIC_BASE_URL'
    if ($oldKey) { Remove-UserVar 'ANTHROPIC_AUTH_TOKEN' }
    # 별칭 둘 — 우리가 방금 걷은 토큰과 값이 같을 때만.
    foreach ($k in $KeyAliases) {
      $cur = [Environment]::GetEnvironmentVariable($k.Name, 'User')
      if (-not $cur) { continue }
      $ours = ($oldKey -and $cur -eq $oldKey) -or
              ($ourGateway['ANTHROPIC_AUTH_TOKEN'] -and $cur -eq $ourGateway['ANTHROPIC_AUTH_TOKEN'])
      if ($ours) { Remove-UserVar $k.Name }
      else { Write-Host "  $($k.Name) — 우리 키가 아니다 · 그대로 둔다" }
    }
  }

  # ⚠ **표 밖의 프록시 주소도 여기서 걷는다 — 안 심는 것만으로는 못 걷는다.** 위 5′ 칸이 이번
  #   판에 그것을 안 심어도 **사내에서 한 번 깐 기계에는 옛 값이 그대로 남는다**(5‴ 칸이 「물러난
  #   이름」에 쓴 규율이 여기도 그대로 선다). 옛 판은 이 자리가 `ANTHROPIC_` 둘과 별칭만 들어서,
  #   표 밖 이름은 **심기지도 걷히지도 않는 것이 아니라 심기기만 했다.**
  # ⚠ **이름을 손으로 안 든다.** 값 파일이 든 이름 가운데 **지금 사용자 환경에 루프백으로 박힌
  #   것**만 우리 것으로 보고 걷는다 — 근거는 `Test-ProxyValue` 의 ⚠ 그대로이고, 남의 값은
  #   루프백이 아니므로 안 걸린다.
  foreach ($k in $fromFile.Keys) {
    if ($known -contains $k) { continue }        # 표 갈래는 바로 위에서 이미 들었다
    if (Test-ProxyValue ([Environment]::GetEnvironmentVariable($k, 'User'))) { Remove-UserVar $k }
  }

  # ⚠ **자동시작을 먼저 걷는다.** 프록시 사본을 못 지우는 판이 있어도(도는 중이라 로그 파일이
  #   잡혀 있다) 등록만 걷히면 **다음 로그인부터는 안 뜬다** — 둘 중 오래 사는 쪽이 등록이다.
  $runKeyPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
  try {
    if (Get-ItemProperty -Path $runKeyPath -Name $ProxyRunName -ErrorAction SilentlyContinue) {
      Remove-ItemProperty -Path $runKeyPath -Name $ProxyRunName -ErrorAction Stop
      Write-Host "  자동시작 — 걷었다 (HKCU Run · $ProxyRunName)" -ForegroundColor Green
    }
  } catch {
    Write-Host "  ! 자동시작 걷기 실패 — $(Say-Why $_)" -ForegroundColor Red
    $Fails.Add('사내 잔재 (자동시작 걷기)')
  }

  $oldProxyDir = Join-Path $env:LOCALAPPDATA $ProxyDirName
  if (Test-Path -LiteralPath $oldProxyDir) {
    Remove-Item -LiteralPath $oldProxyDir -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $oldProxyDir) {
      # ⚠ **못 지운 것을 지웠다고 안 한다.** 도는 프록시가 제 로그를 잡고 있으면 폴더가 남는다 —
      #   그래도 가리키는 주소가 없어졌고 자동시작도 걷혔으니 **다음 로그인이면 사라진다.**
      Write-Host "  ! 프록시 사본을 못 지웠다 (도는 중일 수 있다) — $oldProxyDir" -ForegroundColor Yellow
      Write-Host '     다음 로그인부터는 안 뜬다 — 지금 끄려면 작업 관리자에서 pythonw 를 끝낸다'
    } else {
      Write-Host "  프록시 사본 — 걷었다 ($oldProxyDir)" -ForegroundColor Green
    }
  }
}

# ── 4′. 사외 Claude 구독 로그인 — **저장소와 세션 훅에 매지 않는다** ────────────
# ⚠ 로그인은 클론한 저장소의 일이 아니다. 저장소 칸을 비운 사람도 사외에서는
#   Claude CLI 자체의 자격이 필요하다. 세션 훅은 로그인한 Claude 세션이 열려야 돌므로
#   거기에 두면 순서가 뒤집힌다. 비영속 VDI 가 로그인마다 부르는 이 설치기가 든다.
# ⚠ 2026-09-14 `bootstrap-vdi.sh` 를 걷을 때 검증된 로그인 블록도 같이 사라진 회귀를
#   복구한다. 기존 로그인을 먼저 재고, 비었을 때만 브라우저 OAuth 를 띄운 뒤
#   최대 180초 동안 다시 재다. 사람이 안 누르는 것도 선택이므로 타임아웃을 설치 실패로 세지 않는다.
function Test-ClaudeLoggedIn {
  if (-not (Test-Runs 'claude' '--version')) { return $false }
  try {
    $said = (Get-Quiet 'claude' @('auth','status') | Out-String)
    return ($said -match '"loggedIn"\s*:\s*true')
  } catch { return $false }
}

$claudeLoggedIn = $false
if ($offsite) {
  Write-Host ''
  Write-Host '  Claude 구독 로그인' -ForegroundColor Cyan
  if (-not (Test-Runs 'claude' '--version')) {
    Write-Host '  ! claude CLI 가 안 닿아 로그인을 못 띄운다 — 위 CLI 설치를 본다' -ForegroundColor Yellow
  } elseif (Test-ClaudeLoggedIn) {
    $claudeLoggedIn = $true
    Write-Host '  이미 서 있다 (loggedIn=true)'
  } else {
    Write-Host '  구독 계정 로그인 브라우저를 엽니다 — 눌러 주세요 (최대 180초)' -ForegroundColor Yellow
    try {
      # PowerShell 에서 `claude`는 npm 이 만든 `claude.ps1`이 먼저 잡히지만, cmd 는
      # 그 파일을 실행할 수 없다. 같은 자리의 cmd shim 을 정확히 고른다.
      $cc = Get-Command claude.cmd -ErrorAction Stop
      # 설치 프로세스는 콘솔이 없고 stdin 도 NUL 이다. 로그인은 stdin 이 아니라
      # 브라우저 콜백으로 끝나므로 숨은 cmd 자식으로 띄워도 선다(사외 VDI 실측).
      $cmdArgs = '/d /s /c ""' + $cc.Source + '" auth login"'
      $login = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\cmd.exe') `
                 -ArgumentList $cmdArgs -WindowStyle Hidden -PassThru
      for ($waited = 0; $waited -lt 180; $waited += 5) {
        Start-Sleep -Seconds 5
        if (Test-ClaudeLoggedIn) { $claudeLoggedIn = $true; break }
        if ($login.HasExited) { break }
        $elapsed = $waited + 5
        if (($elapsed % 15) -eq 0) {
          Write-Host "  로그인을 기다리는 중 … ${elapsed}초"
        }
      }
      if (-not $claudeLoggedIn) { $claudeLoggedIn = Test-ClaudeLoggedIn }
      if ($claudeLoggedIn) {
        Write-Host '  섰다 (loggedIn=true)' -ForegroundColor Green
      } else {
        Write-Host '  ! 아직 로그인되지 않았다 — 새 터미널에서 claude auth login' -ForegroundColor Yellow
      }
    } catch {
      Write-Host "  ! 로그인을 못 띄웠다 — $(Say-Why $_)" -ForegroundColor Yellow
      Write-Host '     새 터미널에서: claude auth login'
    }
  }
}

# ── 5‴. 로컬 프록시 — **사내에서 Claude 와 Gemini 가 지나는 문** (결정 0041) ─────────────
# ⚠ **왜 프록시인가.** 게이트웨이가 Opus 5 에서 assistant prefill 을 400 으로 거절하고, Gemini CLI 는
#   http 주소를 거절한다(루프백만 예외). 둘 다 클라이언트 파일을 못 고치는 자리라 사이에 한 겹을 둔다.
#   프록시가 무엇을 고치고 무엇은 안 건드리는지는 그 폴더의 README 가 든다(`posco/pgpt-proxy/`).
# ⚠ **어디에 두나.** 프록시는 로그·pid 를 제 곁에 쓰므로 홈 사본(7 칸이 까는 `~/.claude/posco/`)에서
#   바로 띄우지 않고 실행 폴더로 복사해 띄운다. 자동시작은 사용자 Run 키 하나다 — 관리자 없이 선다.
# ⚠ **이미 도는 것을 함부로 안 죽인다.** 동료 설치본이 같은 프록시를 같은 포트에 띄워 둔 PC 가 있다.
#   `/health` 의 판이 이 판 이상이면 그대로 쓰고, 낡았으면 그 포트를 잡은 파이썬만 끄고 새로 띄운다.
#   자동시작도 같은 프록시를 이미 띄우는 등록이 있으면 우리 것을 안 건다 — 둘이 매 로그인 포트를 다툰다.
# ⚠ **포트·주소는 심은 `ANTHROPIC_BASE_URL` 에서 판다** — 파일에 못박힌 18901 을 여기 또 적으면 사본이다.
function Get-ProxyHealth([string]$Url) {
  try { return Invoke-RestMethod -Uri $Url -TimeoutSec 3 } catch { return $null }
}
# ⚠ **간헐적 502 가 멀쩡한 설치를 빨강으로 끝냈다.** 게이트웨이가 유휴 keep-alive 연결을 조용히
#   닫아 두면 프록시가 그 위에 쓰다 `RemoteDisconnected` 를 맞고 스스로 502 를 낸다 — 그쪽 재시도는
#   1번이라(`opus5_proxy.py` `range(2)`) 새로 집은 연결도 죽어 있으면 그대로 나온다. 실측 2026-09-15:
#   한 로그에 `unreachable` 88 건이 섞였는데 연속 8 회를 두드리니 8/8 이 200 이었다 — 단발로 재면
#   상류의 운이 설치 판정이 된다.
$DoorTries = 3                          # 문을 두드리는 횟수 — 상류가 끊은 것만 다시 묻는다
$DoorGapMs = 700                        # 사이 쉼 — 죽은 연결이 풀에서 빠질 만큼
# ⚠ 두 값을 **매개변수 기본값으로 받는다** — 전역만 보면 그 값이 안 선 자리에서 `-le $null` 이 되어
#   루프가 한 번도 안 돌고 요청 없이 0 이 나온다. 「못 닿았다」와 「안 물어봤다」가 같은 값이 되는
#   자리라 눈에 안 걸린다(실측: 66ms 에 0 — 나가지도 않았다). 부재가 판정이 되지 않게 여기서 막는다.
function Test-PrefillDoor([string]$Base, [string]$Token, [string]$Model,
                          [int]$Tries = $DoorTries, [int]$GapMs = $DoorGapMs) {
  if ($Tries -lt 1) { $Tries = 1 }
  $body = @{ model = $Model; max_tokens = 8
             messages = @(@{ role = 'user'; content = 'hi' }, @{ role = 'assistant'; content = 'prefill' }) } |
          ConvertTo-Json -Depth 5 -Compress
  $hdr = @{ 'x-api-key' = $Token; 'Authorization' = "Bearer $Token"; 'anthropic-version' = '2023-06-01' }
  # ⚠ **다시 묻는 자리는 횟수가 아니라 받은 것의 뜻이 정한다.** 답의 공간이 닫혀 있다 — 게이트웨이가
  #   **prefill 을 두고 판정한 것**(200 열렸다 · 4xx 거절했다)이면 그 자리에서 멈추고, **그 판정에
  #   닿지도 못한 것**(5xx 상류가 끊었다 · 0 못 갔다)만 다시 묻는다.
  #   ⚠ 4xx 를 다시 물으면 안 된다 — 400 이 이 검사가 찾는 그 결함이라(결정 0041) 그것을 재시도로
  #   덮으면 재는 자가 제가 재려던 것을 지운다. 늦게 빨강인 편이 가짜 초록보다 낫다.
  $code = 0
  for ($i = 1; $i -le $Tries; $i++) {
    if ($i -gt 1) { Start-Sleep -Milliseconds $GapMs }
    try {
      $r = Invoke-WebRequest -Uri ($Base.TrimEnd('/') + '/v1/messages') -Method Post -Headers $hdr `
             -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 120 -UseBasicParsing
      $code = [int]$r.StatusCode
    } catch {
      $code = 0
      try { $code = [int]$_.Exception.Response.StatusCode } catch { }
    }
    if (-not (($code -eq 0) -or ($code -ge 500))) { break }
  }
  return $code
}
function Stop-ProxyOnPort([int]$Port) {
  try {
    $owners = @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
                Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($o in $owners) {
      $pr = Get-Process -Id $o -ErrorAction SilentlyContinue
      if ($pr -and $pr.ProcessName -match '^pythonw?$') { Stop-Process -Id $o -Force -ErrorAction SilentlyContinue }
    }
    Start-Sleep -Milliseconds 500
  } catch { }
}
$proxyHealthUrl = $null
if ($wantProxy) {
  Write-Host ''
  Write-Host '  로컬 프록시' -ForegroundColor Cyan
  $proxySrc = Join-Path $Here $proxyRel
  $baseUrl  = $Planted['ANTHROPIC_BASE_URL']
  if (-not (Test-Path -LiteralPath $proxySrc)) {
    Write-Host "  ! 프록시 파일이 이 폴더에 없다 — $proxyRel" -ForegroundColor Red
    $Fails.Add('로컬 프록시 (파일이 없다)')
  } elseif (-not $baseUrl) {
    Write-Host '  ! ANTHROPIC_BASE_URL 이 안 심겨 프록시가 설 자리를 모른다' -ForegroundColor Red
    $Fails.Add('로컬 프록시 (주소가 없다)')
  } else {
    $u = $null
    try { $u = [Uri]$baseUrl } catch { }
    if (-not $u -or -not $u.IsLoopback) {
      # ⚠ 주소가 루프백이 아니면 프록시를 띄워도 아무도 안 지난다 — 세우지 않고 말한다.
      Write-Host "  ! ANTHROPIC_BASE_URL 이 루프백이 아니다 ($baseUrl) — 프록시를 안 세운다" -ForegroundColor Yellow
      Write-Host '     프록시를 지나려면 값 파일의 주소를 127.0.0.1 로 둔다 (결정 0041)'
    } else {
      $proxyHealthUrl = "http://$($u.Host):$($u.Port)/health"
      $py = Get-Command python -ErrorAction SilentlyContinue
      $pyw = $null
      if ($py -and $py.Source) { $pyw = Join-Path (Split-Path $py.Source -Parent) 'pythonw.exe' }
      if (-not $pyw -or -not (Test-Path -LiteralPath $pyw)) {
        Write-Host '  ! pythonw.exe 를 못 찾았다 — 위 1 칸의 파이썬 설치부터 본다' -ForegroundColor Red
        $Fails.Add('로컬 프록시 (파이썬이 없다)')
      } else {
        $proxyDir  = Join-Path $env:LOCALAPPDATA $ProxyDirName
        $proxyPath = Join-Path $proxyDir (Split-Path $proxySrc -Leaf)
        # ── 판 번호는 두 칸이다 — **상류 판과 우리 판을 안 섞는다** ─────────────────
        # ⚠ **점 찍힌 한 줄(`15.4`)을 크기로 견주지 않는다.** 문자열로 견주면 `"9" -ge "10"` 이
        #   참이 되고, `[version]` 으로 넘기면 옛 판이 낸 정수 한 칸(`18`)이 `18.0` 으로 읽혀
        #   **낡은 것이 새것으로 보인다.** 그래서 **두 수를 각각 정수로 읽어 차례로 견준다** —
        #   위 칸이 다르면 그것이 정하고, 같을 때만 아래 칸을 본다.
        # ⚠ **옛 판이 도는 자리를 받는다.** v17·v18 은 `VERSION` 한 칸만 들어 이 정규식에
        #   안 걸리는데, 그때 `$runUp` 이 0 으로 남아 **새 판이 늘 이긴다** — 갈아 끼우는 쪽으로
        #   기운다. 반대로 두면 옛 프록시가 영영 안 바뀐다(부재가 통과로 읽히는 자리).
        function Get-ProxyVer([string]$text) {
          $up = 0; $ours = 0
          $mu = [regex]::Match($text, '(?m)^VERSION_UPSTREAM\s*=\s*(\d+)')
          $mo = [regex]::Match($text, '(?m)^VERSION_OURS\s*=\s*(\d+)')
          if ($mu.Success) { $up = [int]$mu.Groups[1].Value }
          if ($mo.Success) { $ours = [int]$mo.Groups[1].Value }
          return @($up, $ours)
        }
        $ourPair = Get-ProxyVer (Get-Content -LiteralPath $proxySrc -Raw -Encoding UTF8)
        $ourVer = '{0}.{1}' -f $ourPair[0], $ourPair[1]
        New-Item -ItemType Directory -Path $proxyDir -Force | Out-Null
        Copy-Item -LiteralPath $proxySrc -Destination $proxyPath -Force
        Write-Host "  실행 폴더 — $proxyDir (v$ourVer)"

        $up = Get-ProxyHealth $proxyHealthUrl
        $start = $true
        if ($up) {
          # 도는 판이 낸 `version` — 새 판은 `15.4`, 옛 판은 정수 하나다. 둘 다 이 자리가 받는다.
          $runUp = 0; $runOurs = 0
          $runVer = [string]$up.version
          $rm = [regex]::Match($runVer, '^(\d+)(?:\.(\d+))?$')
          if ($rm.Success) {
            $runUp = [int]$rm.Groups[1].Value
            if ($rm.Groups[2].Success) { $runOurs = [int]$rm.Groups[2].Value }
            else { $runUp = 0 }   # 옛 판의 정수 한 칸은 이 축의 값이 아니다 — 갈아 끼운다
          }
          $newer = ($runUp -gt $ourPair[0]) -or (($runUp -eq $ourPair[0]) -and ($runOurs -ge $ourPair[1]))
          if ($newer) {
            Write-Host "  이미 돈다 — v$runVer · 그대로 쓴다"
            $start = $false
          } else {
            Write-Host "  낡은 프록시 v$runVer 이 돈다 — 끄고 v$ourVer 로 새로 띄운다"
            Stop-ProxyOnPort $u.Port
          }
        }
        if ($start) {
          Start-Process -FilePath $pyw -ArgumentList ('"' + $proxyPath + '"') -WindowStyle Hidden | Out-Null
          $up = $null
          for ($i = 0; $i -lt 30 -and -not $up; $i++) { Start-Sleep -Milliseconds 500; $up = Get-ProxyHealth $proxyHealthUrl }
          if ($up) { Write-Host "  띄웠다 — $($u.Host):$($u.Port) v$($up.version)" -ForegroundColor Green }
          else {
            Write-Host "  ! 안 떴다 — $proxyDir\proxy.log 를 본다 (포트를 딴 프로그램이 잡고 있을 수 있다)" -ForegroundColor Red
            $Fails.Add('로컬 프록시 (안 떴다)')
          }
        }

        $runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
        $others = @()
        try {
          $rp = Get-ItemProperty -Path $runKey -ErrorAction Stop
          foreach ($pp in $rp.PSObject.Properties) {
            if ($pp.Name -like 'PS*' -or $pp.Name -eq $ProxyRunName) { continue }
            if (([string]$pp.Value) -like ('*' + (Split-Path $proxySrc -Leaf) + '*')) { $others += $pp.Name }
          }
        } catch { }
        if ($others.Count) {
          Write-Host "  자동시작 — 다른 등록이 이미 같은 프록시를 띄운다 ($($others -join ' · ')) · 우리 것은 안 건다"
        } else {
          try {
            Set-ItemProperty -Path $runKey -Name $ProxyRunName -Value ('"' + $pyw + '" "' + $proxyPath + '"')
            Write-Host "  자동시작 — 로그인마다 띄우도록 걸었다 (HKCU Run · $ProxyRunName)" -ForegroundColor Green
          } catch {
            Write-Host "  ! 자동시작 등록 실패 — $(Say-Why $_)" -ForegroundColor Red
            $Fails.Add('로컬 프록시 (자동시작)')
          }
        }
      }
    }
  }
}

# ── 5⁗. Codex · Gemini 설정 — **틀에서 파생한다** (결정 0041) ──────────────────────────
# ⚠ **값을 여기 안 적는다.** 값 파일이 가리키는 틀(`#codex-config` · `#gemini-config`)이 곧 회사가
#   실제로 쓰는 설정의 사본이고, 여기서는 자리표(키)와 주소만 채운다. 틀을 고치면 설치가 따라온다.
# ⚠ **사람 것을 안 덮는다.** Codex 틀은 파일 하나가 통째라 있던 것을 날짜 붙여 물리고 새로 쓴다.
#   Gemini 는 JSON 이라 틀의 항목만 얹고 사람이 둔 다른 항목은 둔다 — 홈 설정 칸과 같은 규율.
if ($useGateway -and ($wantCodex -or $wantGemini)) {
  Write-Host ''
  Write-Host '  Codex · Gemini 설정' -ForegroundColor Cyan
  $key = $Planted['ANTHROPIC_AUTH_TOKEN']
  $noBom = New-Object Text.UTF8Encoding($false)
  if ($wantCodex) {
    $src = Join-Path $Here $codexTpl
    $dst = $CodexCfg
    if (-not (Test-Path -LiteralPath $src)) {
      Write-Host "  ! Codex 틀이 이 폴더에 없다 — $codexTpl" -ForegroundColor Red
      $Fails.Add('Codex 설정 (틀이 없다)')
    } else {
      $want = Get-Content -LiteralPath $src -Raw -Encoding UTF8
      New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
      $have = $null
      if (Test-Path -LiteralPath $dst) { $have = Get-Content -LiteralPath $dst -Raw -Encoding UTF8 }
      if ($have -eq $want) {
        Write-Host '  Codex config.toml — 이미 맞다'
      } else {
        if ($null -ne $have) {
          $bak = "$dst.before-pgpt-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
          Copy-Item -LiteralPath $dst -Destination $bak -Force
          Write-Host "  Codex config.toml — 있던 것을 물렸다: $bak"
        }
        [IO.File]::WriteAllText($dst, $want, $noBom)
        Write-Host '  Codex config.toml — 썼다 (키는 파일이 아니라 OPENAI_API_KEY 에서 읽는다)' -ForegroundColor Green
      }
    }
  }
  if ($wantGemini) {
    $src = Join-Path $Here $geminiTpl
    $dst = $GeminiCfg
    if (-not (Test-Path -LiteralPath $src)) {
      Write-Host "  ! Gemini 틀이 이 폴더에 없다 — $geminiTpl" -ForegroundColor Red
      $Fails.Add('Gemini 설정 (틀이 없다)')
    } else {
      $tpl = $null
      try { $tpl = Get-Content -LiteralPath $src -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
      $g = $null
      $broken = $false
      if (Test-Path -LiteralPath $dst) {
        try { $g = Get-Content -LiteralPath $dst -Raw -Encoding UTF8 | ConvertFrom-Json } catch {
          Write-Host '  ! Gemini settings.json 을 못 읽었다 (꼴이 깨졌다) — 안 건드린다' -ForegroundColor Red
          $Fails.Add('Gemini 설정 (settings.json 이 깨졌다)')
          $broken = $true
        }
      } else { $g = [pscustomobject]@{} }
      if ($broken) {
      } elseif (-not $tpl) {
        Write-Host "  ! Gemini 틀을 못 읽었다 — $geminiTpl" -ForegroundColor Red
        $Fails.Add('Gemini 설정 (틀이 깨졌다)')
      } else {
        $before = $g | ConvertTo-Json -Depth 10
        foreach ($pp in $tpl.PSObject.Properties) {
          $val = $pp.Value
          # ⚠ **키는 이 파일에 안 쓴다 — 틀의 자리표까지 같이 안 간다** (#2). Gemini CLI 는 키를
          #   `GEMINI_API_KEY` 에서 읽고(5″ 칸이 심는 그 이름), 못 찾으면 제 자격 저장소로 간다 —
          #   `settings.json` 의 `apiKey` 는 **읽는 자가 없다.** 안 읽히는 자리에 평문으로 두는
          #   것은 얻는 것 없이 새는 자리를 하나 더 여는 것뿐이다.
          if ($pp.Name -eq 'apiKey') { continue }
          if ($pp.Name -eq 'baseUrl') {
            # 주소의 진본은 심은 환경변수다 — 틀의 주소(게이트웨이 직결)는 그것이 없을 때의 낙하다.
            if ($Planted['GOOGLE_GEMINI_BASE_URL']) { $val = $Planted['GOOGLE_GEMINI_BASE_URL'] }
          }
          elseif ($g.PSObject.Properties[$pp.Name]) { continue }      # 사람 것은 둔다
          $g | Add-Member -NotePropertyName $pp.Name -NotePropertyValue $val -Force
        }
        # ⚠ **옛 판이 쓴 키는 걷는다 — 안 쓰기로 했으면 걷는 자가 선다.** 우리 값일 때만이다:
        #   제 키를 넣어 둔 사람의 것은 안 건드린다(위 「사람 것은 둔다」와 같은 자).
        if ($key -and $g.PSObject.Properties['apiKey'] -and $g.apiKey -eq $key) {
          $g.PSObject.Properties.Remove('apiKey')
          Write-Host '  Gemini settings.json — apiKey 를 걷었다 (GEMINI_API_KEY 가 든다)' -ForegroundColor Green
        }
        $after = $g | ConvertTo-Json -Depth 10
        if ($after -eq $before) {
          Write-Host '  Gemini settings.json — 이미 맞다'
        } else {
          New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
          [IO.File]::WriteAllText($dst, $after, $noBom)
          Write-Host '  Gemini settings.json — 썼다 (인증 방식 · 키 · 루프백 주소)' -ForegroundColor Green
        }
      }
    }
  }
  # ── 안티그래비티 — **로그인 대신 회사 키로 세운다** (실측 2026-09-17 · #62) ─────────
  # ⚠ **손잡이는 확장이 아니라 `agy` 가 든다.** 확장 설정에는 주소 자리가 없다(선언된 다섯 ·
  #   `serverPort`·`enableTelemetry`·`enableInlineDiff`·`autoOpenFiles`·`channel`). 그것을 보고
  #   「못 문다」로 닫으면 **한 층 아래를 안 본 것이다** — `agy` 가 제 체인지로그에 적어 놨다:
  #   `modelProvider: "gemini"` 를 두고 `GEMINI_API_KEY` 를 export 하면 **로그인 없이** 서고,
  #   `GOOGLE_GEMINI_BASE_URL` 로 주소를 돌릴 수 있다. 그 셋으로 게이트웨이가 답했다 —
  #   근거는 그것만 내는 말이다: 「모델을 찾을 수 없습니다 … 회사코드: 02」.
  # ⚠ **키를 이 파일에 안 쓴다** — 위 Gemini 칸과 같은 자(#2). `agy` 는 `GEMINI_API_KEY` 를
  #   환경에서 읽고, 5″ 칸이 그 이름을 이미 심는다. 여기 쓸 것은 **인증 방식 한 줄**뿐이다.
  # ⚠ **주소도 여기 안 쓴다 — 환경변수가 진본이다.** `GOOGLE_GEMINI_BASE_URL` 은 Gemini CLI 와
  #   **같은 이름을 공유하므로** 5″ 칸이 심은 그 값을 `agy` 도 그대로 본다. 파일에 또 적으면
  #   같은 사실이 두 자리에 살고 한쪽만 낡는다.
  # ⚠ **사람 것은 둔다.** 제 키·제 백엔드로 쓰던 사람의 다른 항목은 안 건드리고, 우리가 더하는
  #   것은 `modelProvider` 하나다. 그 줄을 지우면 로그인 갈래로 돌아간다 — 제 문서가 그렇게
  #   적었다(*"remove \"modelProvider\" from settings.json"*).
  if ($wantAgy) {
    $dst = $AgyCfg
    $a = $null
    $agyBroken = $false
    if (Test-Path -LiteralPath $dst) {
      try { $a = Get-Content -LiteralPath $dst -Raw -Encoding UTF8 | ConvertFrom-Json } catch {
        Write-Host '  ! 안티그래비티 settings.json 을 못 읽었다 (꼴이 깨졌다) — 안 건드린다' -ForegroundColor Red
        $Fails.Add('안티그래비티 설정 (settings.json 이 깨졌다)')
        $agyBroken = $true
      }
    } else { $a = [pscustomobject]@{} }
    if (-not $agyBroken) {
      $before = $a | ConvertTo-Json -Depth 10
      $a | Add-Member -NotePropertyName 'modelProvider' -NotePropertyValue 'gemini' -Force
      $after = $a | ConvertTo-Json -Depth 10
      if ($after -eq $before) {
        Write-Host '  안티그래비티 settings.json — 이미 맞다'
      } else {
        New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
        [IO.File]::WriteAllText($dst, $after, $noBom)
        Write-Host '  안티그래비티 settings.json — 썼다 (modelProvider · 키와 주소는 환경변수가 든다)' -ForegroundColor Green
      }
    }
  }
}

Write-Elapsed '[4/8] 키와 주소'
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
#
# ⚠ **그 안에서 키만은 안 민다 — `$SettingsEnvSkip`.** 이 파일은 설정 저장소가 동기화하는
#   종류라, 여기 든 값은 **평문으로 저장소까지 흘러간다.** 위 까닭이 세운 것은 「모델 고르는
#   자리가 파일을 봐야 한다」이지 「키가 파일에 있어야 한다」가 아니다 — 키를 읽는 세 이름은
#   **사용자 환경변수가 이미 들고 있고**(5″ 칸), CLI 는 거기서 읽는다. 그래서 주소·모델은
#   밀고 토큰과 그 별명 둘은 뺀다 (#2).
Write-Host ''
Write-Host '[5/8] 홈 설정' -ForegroundColor Cyan
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

  # 고를 모델 목록 — **게이트웨이에 닿는 자리에만 쓴다** (선언은 위 `$ModelPicker`).
  # ⚠ `$useGateway` 가 자리 판정을 이미 들고 있다 — 사외면 거짓이라 이 칸이 안 선다. 자리를
  #   여기서 다시 재지 않는다: 두 자리가 재면 한쪽이 낡는다.
  # ⚠ **사외에 남은 옛 줄도 걷는다.** 사내에서 쓰고 나서 사외로 간 기계(또는 이 판 전에 씨앗이
  #   깔아 준 기계)에는 그 줄이 그대로 남아, 구독으로 못 부르는 것이 목록에 선다.
  if ($useGateway) {
    $want = $ModelPicker | ForEach-Object { [pscustomobject]$_ }
    $pick = [pscustomobject]@{ options = @($want); replaceBuiltInOptions = $ModelPickerOnly }
    # 있는 것과 견준다 — 같으면 안 쓴다(매 설치마다 「썼다」가 찍히면 눈이 그 줄을 흘린다).
    $old = if ($cfg.PSObject.Properties['modelPicker']) { $cfg.modelPicker | ConvertTo-Json -Depth 10 -Compress } else { $null }
    if ($old -ne ($pick | ConvertTo-Json -Depth 10 -Compress)) {
      $cfg | Add-Member -NotePropertyName modelPicker -NotePropertyValue $pick -Force
      $dirty = $true
      Write-Host "  모델 목록 $($want.Count) 줄을 맞췄다 (다 1M · 내장 줄은 숨긴다)" -ForegroundColor Green
    } else {
      Write-Host '  모델 목록 — 이미 맞다'
    }
  } elseif ($cfg.PSObject.Properties['modelPicker']) {
    $cfg.PSObject.Properties.Remove('modelPicker')
    $dirty = $true
    Write-Host '  모델 목록 — 걷었다 (게이트웨이를 안 쓰는 자리다)' -ForegroundColor Green
  }

  if ($wantEnv -and $Planted.Count -gt 0) {
    $pushed = 0
    foreach ($k in $Planted.Keys) {
      if ($SettingsEnvSkip -contains $k) { continue }
      $pushed++
      $old = if ($cfg.env.PSObject.Properties[$k]) { $cfg.env.$k } else { $null }
      if ($old -ne $Planted[$k]) {
        $cfg.env | Add-Member -NotePropertyName $k -NotePropertyValue $Planted[$k] -Force
        $dirty = $true
      }
    }
    Write-Host "  env 에 $pushed 개를 맞췄다 (#settings-env = yes · 키는 환경변수에만 둔다)" -ForegroundColor Green
  } elseif (-not $wantEnv) {
    Write-Host '  env 는 안 민다 — 값 파일이 #settings-env 를 안 든다'
  }

  # ⚠ **안 밀기로 한 이름이 옛 판에서 남아 있으면 걷는다.** 심는 자리를 줄였으면 걷는 자리가
  #   선다 — 안 걷으면 옛 판으로 깐 기계는 키를 그대로 들고 있어 이 고침이 **새 기계에만**
  #   선다. 아래 `$Retired` 칸이 이미 쓰는 규율이고, 여기는 이름 대신 **자리**가 물러난 것뿐이다.
  # ⚠ **우리 값일 때만 걷는다.** 같은 이름에 제 값을 넣은 사람이 있을 수 있다 — 값이 우리가
  #   방금 심은 것과 같다는 것이 「이것도 우리가 넣은 것」의 근거다(5⁵ 칸이 환경변수에 쓰는 그 자).
  #   다르면 안 걷고 **문다**: 이 파일의 값이 이기므로, 남겨 두면 방금 심은 키가 가려진 채
  #   화면은 초록으로 끝난다.
  if ($cfg.PSObject.Properties['env']) {
    foreach ($k in $SettingsEnvSkip) {
      if (-not $Planted.ContainsKey($k)) { continue }          # 안 심은 이름은 아래 「홀로 있다」 칸이 든다
      if (-not $cfg.env.PSObject.Properties[$k]) { continue }
      if ($cfg.env.$k -eq $Planted[$k]) {
        $cfg.env.PSObject.Properties.Remove($k)
        $dirty = $true
        Write-Host "  $k — settings.json 에서 걷었다 (환경변수가 든다)" -ForegroundColor Green
      } else {
        Write-Host "  ! $k 이 settings.json 에 다른 값으로 있다 — 심은 값을 가린다" -ForegroundColor Red
        Write-Host "     볼 자리: $homeCfg  (env 칸)"
        $Fails.Add("$k 이 settings.json 에 다른 값으로 있다")
      }
    }
  }

  # ⚠ **우리가 안 심은 ANTHROPIC_ 이름이 남아 있으면 문다.** 사내 안내 문서가 손으로 적으라고
  #   하는 자리라, 옛 값이 남으면 그쪽이 이겨 방금 심은 것이 가려진다 — 화면은 「심었다」로
  #   찍히는데 안 먹는, 부재보다 나쁜 상태다. 지우지는 않는다: 사람이 뜻을 두고 넣었을 수 있다.
  # ⚠ **단 `$Retired` 는 먼저 걷는다.** 그 이름들은 「사람이 뜻을 두고 넣었을 수 있는 것」이 아니라
  #   **우리가 옛 판에 심어 놓고 물러난 것**이다 — 여기 남으면 위 칸이 그것을 물어 설치가 빨강으로
  #   끝난다(실측 2026-09-15: 사용자 PC 가 `ANTHROPIC_CUSTOM_MODEL_OPTION 이 홀로 있다` 로 안 끝났다).
  #   사용자 환경만 걷고 이 파일을 안 걷은 것이 그 결함이었다 — **심는 자리가 둘이면 걷는 자리도 둘**이다.
  if ($cfg.PSObject.Properties['env']) {
    foreach ($k in $Retired) {
      if ($fromFile.ContainsKey($k)) { continue }              # 진본이 되살렸으면 안 건드린다
      if (-not $cfg.env.PSObject.Properties[$k]) { continue }
      $cfg.env.PSObject.Properties.Remove($k)
      $dirty = $true
      Write-Host "  $k — settings.json 에서도 걷었다" -ForegroundColor Green
    }
  }

  # ⚠ **프록시 주소도 이 파일에서 걷는다 — 걷는 자리가 둘이라는 그 말이 여기에도 선다.** 5⁵ 칸이
  #   사용자 환경에서 걷는 값을 여기서 안 걷으면 한쪽만 걷히고 나머지가 남는다(바로 위 ⚠ 가
  #   `$Retired` 에서 겪은 그것). 실측 2026-09-17 집 PC: 환경변수는 걷혔는데 이 파일의 `env` 에
  #   `GOOGLE_GEMINI_BASE_URL` 이 **안 서는 루프백을 가리킨 채 남았다** — 밀기는 더하기만 하므로
  #   안 밀기로 한 이름은 스스로 사라지지 않고, 아래 「홀로 있다」 칸은 `ANTHROPIC_` 만 물어 못 잡는다.
  # ⚠ **이름이 아니라 값이 가른다**(`Test-ProxyValue`). 그래서 값 파일에 이름이 늘어도 이 자리는 안 낡는다.
  # ⚠ **훑는 목록을 먼저 뜬다** — 도는 중에 지우면 열거가 깨진다.
  if (-not $useGateway -and $cfg.PSObject.Properties['env']) {
    foreach ($p in @($cfg.env.PSObject.Properties)) {
      if (-not (Test-ProxyValue $p.Value)) { continue }
      $cfg.env.PSObject.Properties.Remove($p.Name)
      $dirty = $true
      Write-Host "  $($p.Name) — settings.json 에서 걷었다 (사외라 프록시가 안 선다)" -ForegroundColor Green
    }
  }

  if ($cfg.PSObject.Properties['env']) {
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

Write-Elapsed '[5/8] 홈 설정'
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

Write-Elapsed '[6/8] 개인 규범·룰·스킬'
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
Write-Host '[7/8] 사내 환경 문서 · 씨앗 셋' -ForegroundColor Cyan
# ⚠ **씨앗 셋은 거울로 깐다 — 덮어쓰기가 아니다.** `Copy-Item -Recurse -Force` 는 **원본에 없는
#   파일을 안 지운다.** 진본에서 부품 하나를 걷어도 한 번 깐 기계에는 그것이 영영 남고, 씨앗은
#   **있으면 복사되는 자리**라 걷힌 것이 계속 새 프로젝트로 퍼진다 — 5‴ 칸의 「심기는 더하기만
#   한다」와 같은 병이고, 여기도 **지우는 손**이 없어서 난다.
#   ⚠ 이 셋은 **이 zip 이 유일한 진본**이라 거울이 설 수 있다: 홈 사본에 남는 것은 우리가 옛
#     판에 깐 것뿐이고, 저쪽에서 따로 심는 자가 없다.
# ⚠ **`posco` 만은 덮어쓰기로 둔다.** 그 자리는 **진본이 둘이고 런타임 파일이 섞인다** — 설정
#   저장소의 `deploy.ps1` 이 같은 자리를 갱신하고, 프록시가 제 곁에 `opus5_proxy.pid` 와
#   `proxy.log` 를 쓴다. 거울로 걷으면 **남이 심은 것과 도는 프로세스가 쓰는 파일을 지운다** —
#   우리 것만 걷는다는 규율이 못 서는 자리라 여기서는 더하기만 한다.
$envAssets = @(
  @{ From = Join-Path $Here 'posco';         To = Join-Path $homeDir 'posco'; Mirror = $false
     Name = '사내 환경 문서'; Desc = '게이트웨이·API·오류 기록 — 붙이기 전에 읽는다' }
  @{ From = Join-Path $Here 'seeds\gateway'; To = Join-Path $homeDir 'seeds\gateway'; Mirror = $true
     Name = '게이트웨이 씨앗'; Desc = '새 프로젝트가 복사해서 출발한다' }
  @{ From = Join-Path $Here 'seeds\check';   To = Join-Path $homeDir 'seeds\check'; Mirror = $true
     Name = '검사 씨앗';       Desc = '검사 부품과 어느 저장소에서나 도는 게이트의 진본 — 받아 간 사본은 여기를 가리킨다' }
  # ⚠ **이것도 스위치를 안 둔다.** 「설정 저장소」 칸을 쓸 사람만 보지만, **볼지 말지를 고르는
  #   때가 이 설치보다 뒤다** — 칸을 채우려면 저장소가 이미 있어야 하고, 그 저장소를 만드는
  #   골든이 이것이다. 켜는 칸으로 두면 안 켠 사람은 그 칸을 채울 길을 못 찾는다.
  @{ From = Join-Path $Here 'seeds\config-repo'; To = Join-Path $homeDir 'seeds\config-repo'; Mirror = $true
     Name = '설정 저장소 씨앗'; Desc = '「설정 저장소」 칸이 기대하는 저장소를 만드는 골든' }
)
foreach ($a in $envAssets) {
  if (-not (Test-Path -LiteralPath $a.From)) { Write-Host "  $($a.Name) — 이 폴더에 없다"; continue }
  # ⚠ **못 걷었으면 덮어쓰기로 물러나지 않는다.** 걷기가 진 채로 복사하면 옛 부품이 남은
  #   자리가 「깔았다」 초록으로 덮이고, 아래 검증은 **모자란 것만 물어** 여분을 안 문다 —
  #   거울이 안 선 판이 그대로 통과한다. 까닭을 대고 실패로 센다.
  if ($a.Mirror -and (Test-Path -LiteralPath $a.To)) {
    try { Remove-Item -LiteralPath $a.To -Recurse -Force -ErrorAction Stop }
    catch {
      Write-Host "  ! $($a.Name) 옛 사본을 못 걷었다 — $(Say-Why $_)" -ForegroundColor Red
      $Fails.Add("$($a.Name) (옛 사본 걷기)")
    }
  }
  New-Item -ItemType Directory -Path $a.To -Force | Out-Null
  Copy-Item -Path (Join-Path $a.From '*') -Destination $a.To -Recurse -Force
  Write-Host "  $($a.Name) — $(if ($a.Mirror) { '거울로 깔았다' } else { '깔았다' })" -ForegroundColor Green
  Write-Host "     $($a.To)"
  Write-Host "     $($a.Desc)"
}

Write-Elapsed '[7/8] 사내 환경 문서 · 씨앗 셋'
# ── 8. 개인 값 저장소 (선택) ────────────────────────────────────────────────────
# ⚠ **주소는 이 파일에 없다.** `install.env` 가 `#config-repo` 를 들 때만 이 칸이 선다 —
#   그래야 이 스크립트가 익명으로 남아 남에게 그대로 줄 수 있다.
# ⚠ **이 칸은 갈래가 둘이고 둘 다 정당하다.** 규약은 파일 이름 하나 — 받아온 저장소 뿌리의
#   `.claude/hooks/session-start.sh`(Claude Code 의 SessionStart 훅):
#     · 있으면 → `--install` 로 부른다. 리모트 컨테이너의 Setup script 가 부르는 것과 같은 한
#                 줄이라 VDI 와 리모트가 같은 자리로 선다. 그 뒤는 그 저장소가 든다
#     · 없으면 → **받아 둔 것으로 끝낸다.** 저장소를 원한 사람에게 저장소는 왔다
#   그 이름을 받는 사람에게 알리는 것은 `README.md` 가 든다.
# ⚠ **옛 판은 없는 것을 실패로 찍었다.** 「넘길 자리가 없는 것을 성공으로 읽지 않는다」가
#   까닭이었는데, 그것은 **이 칸의 목적을 「넘기기」 하나로 좁게 본 것**이다. 저장소만 들고
#   다니려는 사람에게는 clone 이 곧 목적이고, 그 사람의 성공을 빨강으로 찍으면 **멀쩡한 PC 가
#   매번 실패로 보고된다** — 빨강이 흔해지면 진짜 빨강이 안 보인다 (사용자 확정).
#   그렇다고 조용히 넘어가지도 않는다: 훅이 **왜 안 돌았나**를 그 자리에서 말한다.
# ⚠ **여기서 넘긴 뒤 저쪽이 드는 것은 사람에게 딸린 것뿐이다** — git 신원 · 형제 저장소 · 개인 키 ·
#   규범·룰·메모리 배포. 회사 키·주소·프록시·Codex/Gemini 설정·확장·CLI 는 위 칸들이 이미 세웠다.
#   런타임을 두 번 깔지 않는다 — 무엇을 깔지는 이 파일 하나가 든다.
Write-Host ''
Write-Host '[8/8] 개인 값 저장소' -ForegroundColor Cyan
$repoUrl = Read-Directive $EnvFile 'config-repo'
if (-not $repoUrl) {
  Write-Host '  건너뜀 — install.env 에 #config-repo 가 없다'
} elseif (-not (Test-Runs 'git' '--version')) {
  Write-Host '  ! git 이 안 닿아 못 받는다' -ForegroundColor Red
  $Fails.Add('개인 값 저장소 (git 이 안 닿는다)')
} else {
  # ⚠ **자리를 고르는 칸을 두지 않는다.** 옛 판은 `#config-root` 를 읽었는데, **읽는 자가
  #   여기 하나뿐이었다** — 넘겨받는 쪽은 형제 저장소를 제 선언의 `ROOT`(`$HOME/repos`)로
  #   받고 그 칸을 안 본다. 그래서 그것을 쓰면 설치는 지정한 데로 clone 하고 저쪽은 `~/repos`
  #   에서 찾다 죽는다. **쓰는 순간 저장소가 두 갈래로 갈리는 칸**이라 걷어냈다.
  #   자리를 바꿔야 하면 고칠 자리는 둘이다: 여기와 저쪽 `ROOT`. 한쪽만 고치면 안 선다.
  $root = Join-Path $env:USERPROFILE 'repos'
  New-Item -ItemType Directory -Path $root -Force | Out-Null

  # ── 8′. GitHub CLI 로그인 — **받기 직전, 개인 계정이 서야 하는 자리** ─────────────
  # ⚠ **왜 여기인가.** 이 칸은 **개인 계정이 있어야 서는 칸**이라, 회사 환경(프로그램 · 확장 ·
  #   CLI · 키 · 프록시 · 회사 설정)이 다 선 뒤 개인 값 바로 앞이 제자리다. 옛 판은 이것을
  #   4″ 자리(Claude 로그인 뒤 · 프록시 앞)에 두어, 회사 것이 아직 반도 안 선 자리에서 개인
  #   계정을 먼저 물었다 — 거기서 멈춘 사람은 제 몫도 회사 몫도 못 받은 채로 남았다.
  # ⚠ **왜 저장소를 넣은 사람만인가.** gh 는 바로 아래가 비공개 저장소를 받을 때와 그 뒤 세션
  #   훅이 쓴다. 저장소를 안 넣은 사람은 GitHub 계정이 없을 수도 있어, 띄우면 가입부터 하라는
  #   말이 된다 — 그 사람에게 이 칸은 없는 칸이다. **그 물음은 이 자리가 이미 답한다** — 여기는
  #   `#config-repo` 가 있을 때만 도는 칸 안이라, 옛 판이 조건에 또 적던 줄이 없어졌다.
  #   개발 도구를 끈 사람도 같다(gh 가 안 깔린다) — 그 하나만 아래 조건이 든다.
  # ⚠ **토큰을 전제하지 않는다.** 모두의 길은 팝업이다 — 브라우저에 넣는 일회용 코드 하나.
  #   개인 토큰을 이미 든 사람은 아래 `Test-GhLoggedIn` 이 「이미 서 있다」로 지나간다.
  # ⚠ **일회용 코드는 팝업으로 든다.** 설치 창 기록에만 찍으면 스크롤 속에 묻히고, 브라우저는 코드를
  #   기다린 채 사람은 어디를 봐야 하는지 모른다. 창 하나가 코드 · 남은 시간 · 브라우저 열기 · 복사를
  #   들고, 로그인이 서면 스스로 닫힌다.
  # ⚠ **서면 git 자격도 같이 맡긴다**(`gh auth setup-git`) — 그래야 아래 clone 이 자격 창을 또 안 띄운다.
  # ⚠ **안 누른 것은 실패가 아니다.** 시간이 다 가거나 [건너뛰기]면 「비었다」로 두고 간다 — 아래
  #   clone 은 제 자격 창을 띄우므로 길이 막히지는 않는다. Claude 로그인 칸(4′)과 같은 규율.
  $GhLoginWait = 180                      # 초 — Claude 로그인 칸과 같은 값
  function Test-GhLoggedIn {
    if (-not (Test-Runs 'gh' '--version')) { return $false }
    $null = Get-Quiet 'gh' @('auth','status')
    return ($LASTEXITCODE -eq 0)
  }
  # 코드 창 — 코드가 나올 때까지 「기다리는 중」이고, 나오면 코드가 크게 선다. 초마다 남은 시간을
  # 줄이고 5초마다 로그인이 섰나 재서, 서면 닫는다. 돌려주는 값은 섰나(참/거짓).
  # ⚠ **손잡이는 닫힘(closure)으로 넘긴다.** 폼 이벤트의 스크립트 블록은 이 함수의 변수를 못 본다 —
  #   `GetNewClosure()` 가 그 순간의 참조를 물려주고, 상태는 해시테이블이라 안에서 고친 것이 밖에 남는다.
  function Show-GhLoginWindow([string]$OutFile, [System.Diagnostics.Process]$Proc, [int]$Wait) {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $f = New-Object Windows.Forms.Form
    $f.Text = 'GitHub 로그인'; $f.TopMost = $true; $f.StartPosition = 'CenterScreen'
    $f.FormBorderStyle = 'FixedDialog'; $f.MaximizeBox = $false; $f.MinimizeBox = $false
    $f.ClientSize = New-Object Drawing.Size(420, 190)
    $l1 = New-Object Windows.Forms.Label
    $l1.Text = '브라우저의 GitHub 창에 이 코드를 넣고 승인해 주세요.'
    $l1.Location = New-Object Drawing.Point(16, 14); $l1.Size = New-Object Drawing.Size(390, 20)
    $tCode = New-Object Windows.Forms.TextBox
    $tCode.ReadOnly = $true; $tCode.TextAlign = 'Center'
    $tCode.Font = New-Object Drawing.Font('Consolas', 22, [Drawing.FontStyle]::Bold)
    $tCode.Text = '코드를 기다리는 중 …'
    $tCode.Location = New-Object Drawing.Point(16, 40); $tCode.Size = New-Object Drawing.Size(390, 44)
    $lLeft = New-Object Windows.Forms.Label
    $lLeft.Text = "남은 시간 ${Wait}초"
    $lLeft.Location = New-Object Drawing.Point(16, 96); $lLeft.Size = New-Object Drawing.Size(390, 20)
    $bOpen = New-Object Windows.Forms.Button; $bOpen.Text = '브라우저 열기'
    $bOpen.Location = New-Object Drawing.Point(16, 140); $bOpen.Size = New-Object Drawing.Size(120, 32)
    $bCopy = New-Object Windows.Forms.Button; $bCopy.Text = '코드 복사'
    $bCopy.Location = New-Object Drawing.Point(146, 140); $bCopy.Size = New-Object Drawing.Size(120, 32)
    $bSkip = New-Object Windows.Forms.Button; $bSkip.Text = '건너뛰기'
    $bSkip.Location = New-Object Drawing.Point(286, 140); $bSkip.Size = New-Object Drawing.Size(120, 32)
    $f.Controls.AddRange(@($l1, $tCode, $lLeft, $bOpen, $bCopy, $bSkip))
    $state = @{ Code = ''; Left = $Wait; Tick = 0; Ok = $false }
    $bOpen.Add_Click({ Start-Process 'https://github.com/login/device' | Out-Null })
    $bCopy.Add_Click({ if ($state.Code) { try { Set-Clipboard -Value $state.Code } catch { } } }.GetNewClosure())
    $bSkip.Add_Click({ $f.Close() }.GetNewClosure())
    $timer = New-Object Windows.Forms.Timer; $timer.Interval = 1000
    $timer.Add_Tick({
      $state.Left--; $state.Tick++
      $lLeft.Text = "남은 시간 $($state.Left)초 — 로그인이 서면 이 창은 스스로 닫힙니다"
      if (-not $state.Code) {
        $said = ''
        foreach ($p in @($OutFile, "$OutFile.err")) {
          if (Test-Path -LiteralPath $p) { $said += (Get-Content -LiteralPath $p -Raw -ErrorAction SilentlyContinue) }
        }
        if ($said -match '([A-Z0-9]{4}-[A-Z0-9]{4})') {
          $state.Code = $Matches[1]; $tCode.Text = $state.Code; $tCode.SelectAll()
          # ⚠ **코드가 오면 브라우저를 사람 대신 연다** — gh 자신도 열려 하지만 콘솔 없는 자식이라
          #   못 여는 판이 있고, 그때 사람은 코드만 든 채 버튼을 찾는다. 코드는 클립보드에도 둔다 —
          #   GitHub 창이 붙여넣기를 받는다. 버튼 둘은 그대로 둔다(브라우저가 안 뜬 판의 손잡이다).
          try { Set-Clipboard -Value $state.Code } catch { }
          try { Start-Process 'https://github.com/login/device' | Out-Null } catch { }
        }
      }
      $done = ($Proc -and $Proc.HasExited)
      if ($done -or ($state.Tick % 5) -eq 0) {
        if (Test-GhLoggedIn) { $state.Ok = $true; $f.Close(); return }
      }
      if ($done -or $state.Left -le 0) { $f.Close() }
    }.GetNewClosure())
    $f.Add_Shown({ $f.Activate(); $timer.Start() }.GetNewClosure())
    $f.Add_FormClosed({ $timer.Stop() }.GetNewClosure())
    [void]$f.ShowDialog()
    if (-not $state.Ok) { $state.Ok = Test-GhLoggedIn }
    return $state.Ok
  }

  $ghLoggedIn = $false
  if (-not $NoDevTools) {
    Write-Host ''
    Write-Host '  GitHub CLI 로그인' -ForegroundColor Cyan
    if (-not (Test-Runs 'gh' '--version')) {
      Write-Host '  ! gh 가 안 닿아 로그인을 못 띄운다 — 위 프로그램 칸을 본다' -ForegroundColor Yellow
    } elseif (Test-GhLoggedIn) {
      $ghLoggedIn = $true
      Write-Host '  이미 서 있다'
    } else {
      Write-Host "  브라우저 로그인을 띄운다 — 코드는 팝업에 (최대 ${GhLoginWait}초)" -ForegroundColor Yellow
      $gl = [IO.Path]::GetTempFileName()
      try {
        $ghExe = (Get-Command gh -ErrorAction Stop).Source
        # gh 는 「Enter 를 누르면 브라우저를 연다」고 묻고 기다린다 — 콘솔이 없는 자식이라 `echo.` 로
        # 빈 줄 하나를 넣어 준다. 코드는 gh 가 찍는 것을 파일로 받아 창이 읽는다 — gh 는 코드를
        # 오류 스트림에 찍으므로 두 스트림을 파일 둘로 받고 창이 둘 다 읽는다(한 파일로 합치는 꼴은
        # 뽑기 검사가 막는다 — 파워셸 파일 안의 `2>&1` 은 네이티브 stderr 를 오류로 둔갑시킨다).
        $cmdArgs = '/d /s /c "echo.| "' + $ghExe + '" auth login --hostname github.com --git-protocol https --web > "' + $gl + '" 2> "' + $gl + '.err""'
        $login = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\cmd.exe') `
                   -ArgumentList $cmdArgs -WindowStyle Hidden -PassThru
        $ghLoggedIn = Show-GhLoginWindow $gl $login $GhLoginWait
        if ($ghLoggedIn) {
          Write-Host '  섰다' -ForegroundColor Green
          $null = Get-Quiet 'gh' @('auth','setup-git')
        } else {
          if ($login -and -not $login.HasExited) { try { $login.Kill() } catch { } }
          Write-Host '  ! 로그인이 안 섰다 — 새 터미널에서 gh auth login (저장소 받기는 제 자격 창을 띄운다)' -ForegroundColor Yellow
        }
      } catch {
        Write-Host "  ! 로그인을 못 띄웠다 — $(Say-Why $_)" -ForegroundColor Yellow
      }
      Remove-Item $gl, "$gl.err" -ErrorAction SilentlyContinue
    }
  }

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
      #   망이 끊긴 VDI 에서 옛 판으로라도 훅이 도는 것이 안 도는 것보다 낫다.
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
  #   뒤엣것이 앞엣것의 키·설정을 덮는데 그 순서는 사람이 정한 것이 아니다. 훅은 제 자리에서
  #   전역 저장소를 찾아 형제까지 밀므로, 하나만 불러도 나머지가 선다.
  $hookRel = '.claude\hooks\session-start.sh'
  $bootRepos = @($got | Where-Object { Test-Path -LiteralPath (Join-Path $_ $hookRel) })
  $dest = $bootRepos | Select-Object -First 1
  $boot = if ($dest) { Join-Path $dest $hookRel } else { $null }

  if (-not $got) {
    # ⚠ 실패는 위에서 까닭을 대고 이미 셌다 — 여기서 또 세면 **한 사고가 둘로 보고된다.**
    #   대신 사슬이 왜 끊겼는지는 말한다: 안 말하면 훅이 돈 줄 알 수 있다.
    Write-Host '  넘길 자리가 없어 훅을 안 부른다'
  } elseif (-not $boot) {
    # ⚠ **실패가 아니다.** 저장소는 왔고(위에서 재고 왔다) 그것이 목적인 사람이 있다.
    #   대신 **안 돈 것을 이름으로 말한다** — 훅을 기대한 사람이 조용히 속지 않게.
    Write-Host "  받아 뒀다 — $($got.Count)개" -ForegroundColor Green
    $got | ForEach-Object { Write-Host "     $_" }
    Write-Host "    어느 뿌리에도 $hookRel 가 없어 훅은 안 돌았다."
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
      Write-Host "  ! 훅을 든 저장소가 $($bootRepos.Count)개다 — 첫 것만 부른다" -ForegroundColor Yellow
      $bootRepos | Select-Object -Skip 1 | ForEach-Object { Write-Host "     안 부른 것: $_" }
    }
    Write-Host "  훅으로 넘긴다 — $boot --install" -ForegroundColor Green
    Write-Host ''
    # ⚠ `--install` 은 리모트 Setup script 가 부르는 것과 같은 갈래다 — 지문을 안 보고 깐다.
    #   맨바닥 VDI 의 첫 판(형제 저장소 clone)은 세션 훅의 시간 한도가 아니라 여기서 진다.
    & $bash ($boot -replace '\\','/') --install
    if ($LASTEXITCODE -ne 0) { $Fails.Add("훅 --install (exit $LASTEXITCODE)") }
  }
}
Write-Elapsed '[8/8] 개인 값 저장소'

# ── 넘겨받은 임시 값 파일을 여기서 지운다 — **읽기가 다 끝난 첫 자리다** ────────────
# ⚠ **화면 껍데기도 지우지만 그 손은 제 프로세스가 살아 있을 때만 돈다.** 작업 관리자로 끄거나
#   VDI 가 세션을 끊거나 그것이 죽으면 **평문 토큰이 든 파일이 `%TEMP%` 에 눌러앉고**, 다음
#   판은 PID 가 달라 같은 이름을 다시 안 써 **아무도 다시 안 지운다.** 그래서 몸통도 든다 —
#   값을 다 읽은 자가 지우는 것이 가장 이른 자리다(위 8 칸이 마지막 독자다).
# ⚠ **넘겨받은 것만 지운다.** 옆에 둔 `install.env` 는 사람 것이고 이 파일의 기본값이라, 그것을
#   지우면 다음 판이 값 없이 선다. 근거 둘이 다 서야 한다 — **`-EnvFile` 로 받았나**와
#   **임시 폴더 아래인가.** 하나만 보면 `-EnvFile .\install.env` 로 부른 사람의 파일을 지운다.
if ($PSBoundParameters.ContainsKey('EnvFile') -and $EnvFile) {
  $envFull = ''
  try { $envFull = [IO.Path]::GetFullPath($EnvFile) } catch { }
  $tmpRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
  if ($envFull -and $envFull.StartsWith($tmpRoot, [StringComparison]::OrdinalIgnoreCase) -and
      (Test-Path -LiteralPath $envFull)) {
    Remove-Item -LiteralPath $envFull -Force -ErrorAction SilentlyContinue
  }
}

# ── 바탕화면·시작 메뉴 아이콘 ───────────────────────────────────────────────────
# ⚠ **가리키는 곳은 판에 안 매인 한 자리다.** 설치본은 판마다 제 폴더를 따로 쓰는데
#   (`…\Claude Code Setup.8.0\`) 바로가기가 그 자리를 가리키면 **다음 판에서 죽는다.**
#   설치본이 제 자신을 그 위 한 자리에 복사해 두므로 여기서는 그것만 가리킨다 — 새 판을
#   누를 때마다 그 자리가 최신으로 갈린다.
# ⚠ **아이콘 경로를 안 박는다.** 바로가기가 exe 를 가리키면 윈도우가 **그 안의 아이콘**을
#   쓴다. 바로가기의 아이콘 칸은 절대 경로만 먹어 zip 을 건너면 깨지는 자리라(실측
#   2026-09-15) 안 쓰는 것이 맞다 — 가리키는 것만으로 저절로 선다.
# ⚠ **없으면 조용히 건너뛴다.** `install.cmd` 로 직접 눌러 들어온 갈래에는 그 파일이 없다.
#   아이콘 하나 때문에 그 갈래를 빨갛게 만들지 않는다.
# ⚠ **실패를 세지 않는다.** 설치는 이미 선 것이고, 바로가기는 덤이다. 여기서 `$Fails` 를
#   불리면 멀쩡히 깔린 기계가 빨갛게 보고된다 — 「연다」 칸과 같은 까닭이다.
$launcher = Join-Path $env:LOCALAPPDATA 'Claude Code Setup\Setup.exe'
if (Test-Path -LiteralPath $launcher) {
  Write-Host ''
  Write-Host '  바탕화면 · 시작 메뉴에 아이콘을 둔다'
  $made = @()
  try {
    $sh = New-Object -ComObject WScript.Shell
    # ⚠ **두 자리를 같은 자로 판다.** 옛 판은 바탕화면만 `GetFolderPath` 로 파고 시작 메뉴는
    #   경로를 박았다 — 앞엣것은 OneDrive·폴더 리다이렉션을 따라가고 **뒷것은 안 따라간다.**
    #   시작 메뉴를 리다이렉트한 사내 VDI 에서는 `Test-Path` 가 거짓이라 **조용히 건너뛰고**,
    #   여기는 실패로도 안 세므로(위 ⚠) 아무 줄도 안 남는다. 윈도우가 드는 자를 둘 다 쓴다.
    $spots = @(
      @{ Name = '바탕화면';   Dir = [Environment]::GetFolderPath('Desktop') }
      @{ Name = '시작 메뉴'; Dir = [Environment]::GetFolderPath('Programs') }
    )
    # ⚠ **옛 이름의 아이콘을 걷는다.** `.lnk` 는 **파일 이름이 곧 표시 이름**이라, 이름을 바꾸면
    #   새 것이 생길 뿐 옛 것은 그대로 남는다 — 사람 눈에는 아이콘 둘이 서고 둘 다 눌리며,
    #   둘 다 같은 `Setup.exe` 를 가리켜 **어느 쪽이 맞는지 알 길이 없다.**
    # ⚠ **이름이 바뀔 때마다 여기 한 줄이 는다** — 걷을 것은 「우리가 옛날에 쓴 이름」이지
    #   아무 `.lnk` 나가 아니다. 남이 만든 바로가기를 지우지 않으려면 목록으로 드는 수밖에 없다.
    $OldLnkNames = @('Claude Code 설치')
    foreach ($spot in $spots) {
      if (-not $spot.Dir -or -not (Test-Path -LiteralPath $spot.Dir)) { continue }
      foreach ($old in $OldLnkNames) {
        if ($old -eq $AppName) { continue }        # 이름이 안 바뀐 판에서는 방금 만든 것을 지우게 된다
        $oldLnk = Join-Path $spot.Dir "$old.lnk"
        if (Test-Path -LiteralPath $oldLnk) {
          Remove-Item -LiteralPath $oldLnk -Force -ErrorAction SilentlyContinue
        }
      }
      try {
        $lnk = $sh.CreateShortcut((Join-Path $spot.Dir "$AppName.lnk"))
        $lnk.TargetPath       = $launcher
        $lnk.WorkingDirectory = Split-Path -Parent $launcher
        $lnk.Description      = "$AppName — 누르면 새 판이 있는지도 봅니다"
        $lnk.Save()
        $made += $spot.Name
      } catch { }
    }
  } catch { }
  if ($made.Count) { Write-Host ("    " + ($made -join ' · ') + " — 다음에는 이것을 누르면 됩니다") -ForegroundColor Green }
  else { Write-Host '    ! 아이콘을 못 만들었다 — 설치에는 지장이 없다' -ForegroundColor Yellow }
}

# 나른 것을 **동봉본과 견주는 자** — 7 칸과 6 칸이 같은 자를 쓴다.
# ⚠ **폴더가 있나로 묻지 않는다.** `New-Item` 이 먼저 도니 복사가 실패해도 폴더는 남는다 —
#   빈 폴더를 [O] 로 찍으면 「깔렸는데 안 든 것」이 성공으로 보고된다. 그래서 **파일 수를 센다.**
# ⚠ **여분은 판정이 아니라 눈금이다.** 「남는 것이 있다」와 「나른 것이 모자란다」는 다른
#   명제라, 수는 찍되 [X] 는 모자랄 때만 든다 — 걷는 자리(씨앗 셋)와 안 걷는 자리(개인
#   규범·룰·스킬)가 **같은 자를 쓰면서** 서로 다른 뜻을 읽을 수 있게 하는 것이 이 갈림이다.
#   ⚠ 두 자를 따로 두면 한쪽만 낡는다 — 찍는 꼴이 두 벌이 되는 그 자리가 사본이다.
function New-CountCheck([string]$Name, [string]$From, [string]$To) {
  $isDir = Test-Path -LiteralPath $From -PathType Container
  $srcN = if ($isDir) { @(Get-ChildItem -LiteralPath $From -Recurse -File -ErrorAction SilentlyContinue).Count } else { 1 }
  $dstN = 0
  if (Test-Path -LiteralPath $To) {
    $dstN = if ($isDir) { @(Get-ChildItem -LiteralPath $To -Recurse -File -ErrorAction SilentlyContinue).Count } else { 1 }
  }
  $extra = if ($dstN -gt $srcN) { " · 여분 $($dstN - $srcN)" } else { '' }
  return @{ Name = "$Name ($dstN/$srcN$extra)"; Ok = ($srcN -gt 0 -and $dstN -ge $srcN) }
}

# ── 검증 — **재고 나서 말한다** ─────────────────────────────────────────────────
# ⚠ 안 재고 「됐다」로 끝내면 안 선 기계도 성공으로 보고된다. 부재가 통과로 읽히는 것을
#   막는 것이 이 스크립트의 규율이라, 마지막 칸이 그것을 든다.
# ⚠ 환경변수는 **레지스트리에서** 읽는다 — 이 창의 값은 방금 우리가 넣은 것이라 심겼는지를
#   못 잰다. 새 창이 볼 자리를 봐야 판정이 참이 된다.
Write-Host ''
Write-Host '=== 검증 ===' -ForegroundColor Cyan
# ⚠ **이름을 `$Planted` 와 갈라 둔다.** 파워셸 변수는 대소문자를 안 가려, 옛 판의 `$planted` 는
#   **「우리가 심은 것」을 「사용자 환경 전부」로 그 자리에서 갈아치웠다.** 지금은 읽는 자리가
#   다 이 줄 앞이라 안 터지지만, 이 파일은 칸이 계속 느는 파일이라 뒤에 `$Planted.ContainsKey(...)`
#   한 줄이 들어오는 날 **「우리가 심었나」가 「사용자 환경에 있나」로 조용히 바뀐다** — 그러면
#   위 「우리가 안 심은 `ANTHROPIC_*`」 검사가 영영 아무것도 못 문다. 이름만 갈라 두면 없어진다.
$userEnv = [Environment]::GetEnvironmentVariables('User')
# 한 번만 잰다 — 같은 물음을 두 번 물으면 두 답이 갈릴 자리가 나고, 아래 「연다」 칸도 이 값을 쓴다.
$hasCode = Test-Runs 'code' '--version'
$extList = @()
if ($hasCode) { $extList = Get-Quiet 'code' '--list-extensions' }
# ⚠ **안 고른 것은 안 잰다** — 켜지도 않은 것을 [X] 로 찍으면 **멀쩡한 설치가 빨갛게 끝난다.**
#   VS Code 도 고르는 것이 됐으므로 이 줄이 그 문 아래 있어야 한다. 사외 기본이 「끔」이라,
#   안 걸면 **기본값으로 돌린 사람마다 「끝내지 못했다 — VS Code」를 본다**(실측 2026-09-17).
# 확장과 CLI 는 **깔 때 본 표 그대로** 잰다 — 표에 한 줄을 더하면 검증도 따라온다.
$checks = @()
if (-not $NoVsCode) {
  $checks += @{ Name='VS Code'; Ok = $hasCode }
  foreach ($x in $ExtPicks) {
    $checks += @{ Name = $x.Label; Ok = ($hasCode -and ($extList -contains $x.Id)) }
  }
}
foreach ($c in $CliPicks) {
  $checks += @{ Name = $c.Label; Ok = (Test-Runs $c.Cmd '--version') }
}
# 나르는 자리 둘 — 7 칸의 자산과 6 칸의 개인 규범·룰·스킬. 재는 자는 위 `New-CountCheck` 하나다.
foreach ($a in $envAssets) {
  if (-not (Test-Path -LiteralPath $a.From)) { continue }
  $checks += New-CountCheck $a.Name $a.From $a.To
}
# ⚠ **[6/8] 도 잰다 — 옛 판은 이 칸만 아무것도 안 찍었다.** [7/8] 과 한 글자도 안 다른 무늬인데
#   `$checks` 에 한 줄도 안 들어, 「스킬 — 깔았다」 초록 한 줄로 끝나고 판정이 없었다.
# ⚠ **다만 여기는 안 걷는다.** 이 자리들의 진본은 설정 저장소이고 그쪽 배포(`deploy.ps1`)가
#   같은 자리에 민다 — 설치기가 걷으면 저쪽이 방금 심은 것을 이쪽이 지우는 꼴이 되어, 두 자가
#   한 자리를 두고 판마다 싸운다. 그래서 여분은 [X] 가 아니고 모자란 것만 문다.
#   ⚠ 그 대신 **옛 판이 깐 스킬·룰이 홈에 남는 것은 여기서 안 풀린다** — 저쪽 배포가 드는 몫이다.
if ($WithPersonalConfig -and $pairs) {
  foreach ($p in $pairs) {
    if (-not (Test-Path -LiteralPath $p.From)) { continue }
    $checks += New-CountCheck $p.Name $p.From $p.To
  }
}
# ⚠ **안 쓰기로 한 것을 [X] 로 찍지 않는다.** 그러면 멀쩡한 사외 PC 가 매번 빨갛게 보고되고,
#   빨강이 흔해지면 진짜 빨강이 안 보인다.
# ⚠ **키는 `#config-repo` 가 있어도 여기서 잰다.** 옛 판은 그 판에서 키 검사를 저쪽에 맡겼는데,
#   저장소에 부트스트랩이 없으면 **키가 어디에도 안 심긴 채 초록으로 끝났다** — 부재가 통과로
#   읽히는 자리였다. 이제 심는 자가 이 파일 하나라 재는 자도 하나다.
if ($useGateway) {
  foreach ($v in $Vars) {
    if (-not $v.Gateway) { continue }
    $checks += @{ Name = $v.Name; Ok = [bool]$userEnv[$v.Name] }
  }
  foreach ($k in $KeyAliases) {
    if (-not $wantNeed[$k.Need]) { continue }
    $checks += @{ Name = $k.Name; Ok = [bool]$userEnv[$k.Name] }
  }
  if ($wantCodex)  { $checks += @{ Name = 'Codex config.toml';    Ok = (Test-Path -LiteralPath $CodexCfg) } }
  if ($wantGemini) { $checks += @{ Name = 'Gemini settings.json'; Ok = (Test-Path -LiteralPath $GeminiCfg) } }
  if ($wantAgy)    { $checks += @{ Name = '안티그래비티 settings.json'; Ok = (Test-Path -LiteralPath $AgyCfg) } }
  # ⚠ **프록시는 「떠 있나」와 「문을 여나」를 따로 잰다.** 떠 있는 것만 보면 보정이 안 도는 판이
  #   초록이 된다. 문은 assistant 로 끝나는 본문을 프록시 너머로 보내 200 이 오는가로 잰다 — 이
  #   게이트웨이가 Opus 5 에서 그 본문을 400 으로 거절하는 것이 프록시가 있는 까닭이라(결정 0041),
  #   짧은 답이 오나가 아니라 **그 400 이 사라졌나**를 묻는다. 모델 이름은 그 결함의 이름이다.
  if ($wantProxy -and $proxyHealthUrl) {
    $h = Get-ProxyHealth $proxyHealthUrl
    $checks += @{ Name = '로컬 프록시 (/health)'; Ok = [bool]$h }
    $door = 0
    if ($h -and $userEnv['ANTHROPIC_AUTH_TOKEN']) {
      $door = Test-PrefillDoor $userEnv['ANTHROPIC_BASE_URL'] $userEnv['ANTHROPIC_AUTH_TOKEN'] 'claude-opus-5'
    }
    $checks += @{ Name = "Opus 5 문 — prefill 본문이 프록시 너머로 200 (받은 것: $door$(if ($door -ge 500) { " — 상류가 끊었다 · prefill 이 아니다" }))"; Ok = ($door -eq 200) }
  }
} else {
  Write-Host '  (게이트웨이를 안 쓴다 — 구독 로그인으로 선다)'
  # ⚠ **안 쓰기로 한 자리에서 재는 것은 「있나」가 아니라 「없나」다.** 옛 판은 이 갈래에서 그
  #   이름들을 **아예 안 쟀고**, 그래서 사내에서 한 번 깐 기계에 남은 옛 값이 검증을 그대로
  #   지나갔다 — 화면은 전부 [O] 인데 CLI 는 닿지 않는 루프백으로 나갔다(5⁵ 칸 ⚠).
  #   **부재가 아니라 잔재가 통과로 읽히는 자리라, 묻는 방향을 뒤집는다.**
  foreach ($v in $Vars) {
    if (-not $v.Gateway) { continue }
    $checks += @{ Name = "$($v.Name) 없음 (사외)"; Ok = (-not $userEnv[$v.Name]) }
  }
  # ⚠ **표 밖의 프록시 주소도 같은 방향으로 묻는다.** 위 5′·5⁵ 칸이 표가 아니라 **값**에서
  #   파생해 거르므로, 재는 자리만 표를 보면 걷기가 져도 전부 [O] 로 끝난다 — 이 칸이 막으려던
  #   바로 그 병이 표 밖 이름에서 그대로 재발한다.
  # ⚠ **묻는 것은 「이름이 없나」가 아니라 「프록시 주소가 아닌가」다.** 같은 이름을 제 주소로
  #   쓰는 사람이 있고 5⁵ 칸은 그것을 안 걷는다 — 「없나」로 물으면 안 걷기로 한 것을 빨갛게 찍는다.
  foreach ($k in $fromFile.Keys) {
    if ($known -contains $k) { continue }
    if (-not (Test-ProxyValue $fromFile[$k])) { continue }
    $checks += @{ Name = "$k — 프록시 주소 없음 (사외)"; Ok = (-not (Test-ProxyValue $userEnv[$k])) }
  }
}
foreach ($c in $checks) {
  if ($c.Ok) { Write-Host "  [O] $($c.Name)" -ForegroundColor Green }
  else       { Write-Host "  [X] $($c.Name)" -ForegroundColor Red }
}
# ⚠ **판정 목록이 둘인데 서로 몰랐다.** `$Fails` 는 「하는 걸음이 졌다」를 담고 이 `$checks` 는
#   「끝에 다시 재 봤다」를 담는데, 종료코드는 `$Fails` 만 봤다 — 그래서 **검증이 빨간데 초록으로
#   닫히는 자리**가 있었다. 바로 위 칸 머리글이 「안 재고 됐다로 끝내면 안 선 기계도 성공으로
#   보고된다」라고 적어 둔 그 일이, **재고도 결론으로 안 건너가** 그대로 났다.
#   ⚠ 새는 자리가 둘이다 — **자산 나르기**(7 칸)는 `$Fails` 에 아무것도 안 넣고, **값 심기**는
#     던졌을 때만 넣는데 **검증은 레지스트리를 다시 읽는다.** 조용히 안 남는 자리에서 「심었다」를
#     찍고도 `[X]` 가 뜬다. 나머지 칸은 하는 걸음과 검증이 **같은 프로브**라 둘이 같이 빨개진다.
# ⚠ **`$Fails` 에 합치지 않는다.** 합치면 같은 사고를 두 자가 각각 넣어 「N 개가 남았다」가
#   겹쳐 센다(`[X] VS Code` 와 `VS Code 설치`). 세는 자를 갈라 두면 **종료코드만** 바로잡힌다.
$redChecks = @($checks | Where-Object { -not $_.Ok }).Count

# ⚠ 옛 판은 여기서 **동봉 자산의 경로만 찍었다**(`posco/` · `seeds/gateway/`). 이제 그 둘은
#   7 칸이 홈에 깔고 검증도 아래가 든다 — 찍기만 하는 자리를 남겨 두면 zip 폴더를 가리키는
#   낡은 좌표가 하나 더 산다.

Write-Host ''
if ($redChecks -gt 0) {
  Write-Host "검증에서 $redChecks 칸이 빨갛다 — 바로 위 [X] 가 그것이다" -ForegroundColor Red
  Write-Host ''
}
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
#   그때는 `#config-repo` 갈래가 자리를 재는 블록을 통째로 건너뛰어 **사외인데도 `$useGateway` 가
#   참으로 남았다.** 실측 2026-09-11(집 PC): `자리 = 사외` 와 `데스크탑 앱 · 있음` 이 나란히
#   찍힌 판에서 VS Code 가 떴다 — **한 판정을 두 자가 다르게 읽은 자리다.** 그 갈래는 이제
#   없지만 「사내인가」와 「게이트웨이를 쓰나」는 여전히 다른 물음이라 자는 그대로 둔다.
#   데스크탑이 안 깔린 자리(값 파일에 `#desktop-app` 이 없다)는 VS Code 로 떨어진다 —
#   없는 것을 열려다 빈손으로 끝내지 않는다.
# ⚠ **못 열어도 실패로 안 센다.** 설치는 이미 선 것이고 창은 사람이 손으로도 연다. 여기서
#   `$Fails` 를 불리면 멀쩡히 깔린 기계가 빨갛게 보고된다.

# ⚠ **찾는 자는 「무엇을」이 아니라 「어떻게 띄우나」를 돌려준다.** 둘이 진짜로 다른 기전이라
#   그렇다 — VS Code 는 실행 파일을 직접 띄워야 **이 창이 방금 심은 값을 물고** 뜨고, 데스크탑은
#   띄울 실행 파일이 아예 없다. 그래서 `Exe` 를 든 것과 `AppId` 를 든 것이 갈려 나온다.
#   `Proc` 는 「이미 떠 있나」를 재는 이름(들)이다 — VS Code 는 실행 파일에서 하나를, 데스크탑은
#   손잡이와 앱 이름에서 후보 목록을 든다(까닭은 `Find-DesktopApp` 안에).

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
# ⚠ **찾을 이름도 안 박는다** — 위 표의 `App` 칸이 든다. 고른 것이 여럿이면 **고른 차례로**
#   묻고 처음 찾은 것을 연다: 앞문은 하나이고, 어느 것이 앞문인지는 값 파일이 적은 차례다.
function Find-DesktopApp {
  if (-not $appPicks) { return $null }          # 고른 데스크탑 앱이 없다
  try {
    $all = @(Get-StartApps -ErrorAction Stop)
  } catch { return $null }                      # 이 윈도우에 그 물음이 없다
  $a = $null; $want = $null; $label = $null
  foreach ($pick in $appPicks) {
    $hit = @($all | Where-Object { $_.Name -like "*$($pick.App)*" })[0]
    if ($hit -and $hit.AppID) { $a = $hit; $want = $pick.App; $label = $pick.Label; break }
  }
  if (-not $a) { return $null }
  # 프로세스 이름은 **후보 목록**이다 — 손잡이에서 판 것 하나와 앱 이름 하나.
  # ⚠ **손잡이 하나로는 못 판다.** 꼴이 셋이고 이름이 앉는 자리가 다 다르다 — 스토어 꼴은
  #   `앱_해시!앱` 의 `_` 앞, 바로가기 꼴은 파일 이름, claude.ai 에서 받은 일반 설치본(Squirrel)은
  #   `com.squirrel.<패키지>.<실행파일>` 의 **마지막 마디**다. 옛 판은 앞 둘만 알아서 셋째 꼴에서
  #   `com.squirrel.AnthropicClaude` 를 이름으로 들었고, 실물은 `claude` 라 **떠 있는데 「안 떠
  #   있다」로 읽었다**(실측 2026-09-15 · 사외 PC). 그래서 묻지도 끄지도 않고 손잡이로 띄웠는데,
  #   도는 앱은 그 호출에 창만 앞으로 올 뿐 새로 안 떠 — 낡은 것이 재시작한 얼굴로 남았다.
  # ⚠ **꼴을 하나 더 박는 대신 앱 이름을 후보에 더한다.** 세 꼴 다 실행 파일이 곧 앱 이름이라
  #   (`claude`) 그 하나가 셋을 덮고, 꼴이 또 늘어도 안 어긋난다. 손잡이에서 판 것은 그대로 둔다 —
  #   이름이 실행 파일과 갈리는 앱이 오면 그쪽이 든다. `Get-Process -Name` 은 목록을 받는다.
  $fromId = if ($a.AppID -match '!') { ($a.AppID -split '_')[0] }
            else { [IO.Path]::GetFileNameWithoutExtension($a.AppID) }
  $procs = @($fromId, $want) | Where-Object { $_ } | Select-Object -Unique
  return @{ Name = $label; AppId = $a.AppID; Proc = @($procs) }
}

# 그 앱이 이미 도나 — 이름은 찾는 자가 든 것을 그대로 쓴다(하나든 목록이든 `-Name` 이 받는다).
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
  # MessageBox 의 owner 는 실제로 떠 있는 창이어야 한다. 예전 코드는 보이지 않는 Form 을
  # owner 로만 넘겨서, 회사 PC/VDI 에서는 확인창이 VS Code 뒤에 숨은 채 응답을 기다렸다.
  # 작업표시줄에는 남기지 않는 1px 창을 먼저 활성화해 메시지박스를 반드시 앞으로 가져온다.
  $owner.ShowInTaskbar = $false
  $owner.StartPosition = 'Manual'
  $owner.Size = New-Object Drawing.Size(1, 1)
  $work = [Windows.Forms.Screen]::PrimaryScreen.WorkingArea
  $owner.Location = New-Object Drawing.Point(
    ($work.Left + [int]($work.Width / 2)),
    ($work.Top  + [int]($work.Height / 2)))
  $owner.Opacity = 0
  $owner.TopMost = $true
  try {
    $owner.Show()
    $owner.Activate()
    $owner.BringToFront()
    $msg = "$AppName — 이미 돌고 있습니다.`n`n" +
           "지금 껐다 새로 열까요?`n" +
           "돌던 것은 방금 깔린 것(키 · MCP 서버 · 세션 훅)을 모릅니다.`n`n" +
           "저장 안 한 것이 있으면 먼저 저장하고 눌러 주세요."
    return ([Windows.Forms.MessageBox]::Show(
      $owner, $msg, $AppName, 'YesNo', 'Warning') -eq 'Yes')
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
  # ⚠ **우리가 심은 자가 아닌 갈래가 있다.** 값 저장소로 넘긴 판에서는 훅이 개인 키를 심었고
  #   그 값은 **레지스트리에만** 있다 — 이 창의 환경에는 없다. 그대로 자식을 내면 우리가
  #   **낡은 환경을 물려주는** 꼴이 되어, 사람이 탐색기에서 직접 여는 것보다 나빠진다.
  #   그래서 띄우기 직전에 **새 창이 볼 자리**를 이 창으로 당긴다 — 검증 칸이 이미 읽어 둔
  #   값이고, 훅이 끝난 뒤에 읽은 것이라 저쪽이 심은 것까지 든다.
  # ⚠ **PATH 만은 안 당긴다.** 그 이름은 기계 값과 사용자 값이 합쳐져 서는 자리라, 사용자
  #   쪽만 덮으면 이 창이 여태 태운 배선(`Update-RuntimePath`)이 통째로 날아간다.
  foreach ($k in $userEnv.Keys) {
    if ($k -ieq 'PATH') { continue }
    [Environment]::SetEnvironmentVariable($k, $userEnv[$k], 'Process')
  }

  $app = $null
  if ($offsite) {
    $app = Find-DesktopApp
    # ⚠ **못 찾은 것을 말없이 딴 것으로 갈음하지 않는다.** 사외에서 앞문은 데스크탑이다 —
    #   못 찾았다고 조용히 VS Code 를 열면 사람은 「왜 VS Code 가 뜨지」를 혼자 헤맨다.
    #   실측 2026-09-11(집 PC): 한 줄도 안 찍힌 채 VS Code 가 떴고, 까닭을 찾는 데 몇 판이 들었다.
    #   **떨어지더라도 왜 떨어졌는지 찍고 떨어진다.**
    if (-not $app) {
      # 고른 것이 아예 없으면 못 찾은 것이 아니라 **찾을 것이 없는** 것이다 — 두 말을 가른다.
      if ($appPicks) {
        Write-Host ('  ! {0}을 못 찾았다 — 시작 메뉴에서 직접 연다' -f
                    (($appPicks | ForEach-Object { $_.Label }) -join ' · ')) -ForegroundColor Yellow
      }
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
    #   · **선언** — **이 설치가 끝이 아니다.** 뒤이어 설정 저장소의 훅이 규범·MCP 선언·세션
    #     훅을 심는다. 돌던 앱은 그 선언을 **뜰 때 한 번 읽고
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
# ⚠ **총계는 `exit` 둘보다 위에 둔다.** 아래는 진 판이 1 로 나가는 자리라, 그 뒤에 적으면
#   **진 판에서만 총계가 사라진다** — 오래 걸려서 진 판이야말로 총계가 필요한 자리다.
Write-Host ("── 설치를 마쳤다 (" + [int]$Sw.Elapsed.TotalSeconds + "초)") -ForegroundColor DarkGray
# ⚠ **둘 다 본다.** 하는 걸음이 진 것(`$Fails`)과 끝에 재서 빨간 것(`$redChecks`)은 겹치기도
#   하고 한쪽만 서기도 한다 — **어느 쪽이든 하나라도 서면 이 설치는 안 끝난 것이다.**
if ($Fails.Count -gt 0 -or $redChecks -gt 0) { exit 1 }
# ⚠ **성공 경로에도 `exit` 가 있어야 한다.** 파일 끝으로 떨어지면 화면 갈래는 성하지만
#   (`cmd /c` 가 `-File` 규약으로 0 을 낸다) **콘솔 갈래는 같은 런스페이스 안에서** 이 파일을
#   부른 뒤 `$LASTEXITCODE` 를 읽는다 — 그 값은 이 파일이 마지막으로 부른 **네이티브 명령**이
#   남긴 남의 값이다. 멀쩡히 끝난 설치가 앞선 명령의 1 을 물고 실패로 보고된다.
exit 0
