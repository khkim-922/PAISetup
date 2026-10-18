# 맨바닥 윈도우 PC 에서 **VS Code 의 Claude Code 확장이 돌게** 한다 — 기계를 세우는 층이다. 진입점은 `install.cmd`.
#
#   .\install.ps1                    깔고, 없는 값은 묻는다
#   .\install.ps1 -Yes               안 묻는다 — 값 파일이 다 들고 있을 때만 (자동화용)
#   .\install.ps1 -NoDevTools        git·python·gh 를 건너뛴다 (확장만 쓸 사람)
#   .\install.ps1 -DevTools          기록에 남은 위 끔을 되돌려 git·python·gh 를 깐다
#   .\install.ps1 -PersonalFor claude,codex,agy  제작자의 규범·룰·스킬을 그 도구에 (고른 것만 · 결정 0099 ·
#                                  설정 저장소를 넣었으면 그 저장소의 것이 간다 · 결정 0107)
#   .\install.ps1 -WithPersonalConfig  위를 Claude 에만 (옛 자동 실행 기록이 드는 칸 — 아래 「옛 제작자 칸」)
#   .\install.ps1 -NoLaunch          끝에 창을 안 띄운다 (기본은 띄운다)
#   나머지 칸은 `param` 바로 위의 칸별 설명이 든다.
#
# 내는 것 — 프로그램 · VS Code 확장 · CLI · 사용자 환경변수 · 도구 홈 설정. 화면에는 걸음마다 `[n/N] 이름` 머리줄과 걸린
#   초를 찍고, 끝에 재서 [O]/[X] 를 찍는다. 메모리(세션 기록)는 안 깐다 — 저장소마다 슬러그 폴더에 서는 것이라 저장소를
#   다루는 `deploy.ps1` 의 몫이다.
#
# 값은 이 파일에 없다 — 이름과 설명만 들고, 값은 옆의 `install.env`(`이름=값` 한 줄씩 · `secrets.env` 와 같은 꼴)나 사람의
#   입력에서 온다. 그래서 한 몸통이 두 갈래를 다 든다: 값 파일을 든 사람은 아무것도 안 묻고 지나가고, 값이 모자란 사람은
#   묻는 것에 답하면 선다(**몸통은 이름을 모른다**). 다만 자리를 재는 줄(`#site-probe`)은 값 파일이 꼭 든다 — 없으면 사내 · 사외를
#   못 갈라 아무것도 안 깔고 멈춘다(「준비」의 「자리」 칸).
#   값 파일이 `#config-repo` 를 들면 다 세운 뒤 그 저장소를 받고, 뿌리에 훅(`.claude/hooks/session-start.sh` — 우리 옛 세대
#   사본이면 지금 판으로 간 뒤)이 있으면 `--install` 로 부른다 — 사람에게 딸린 것(git 신원 · 형제 저장소 · 개인 키 · 배포)은
#   그쪽이 든다.
# ⚠ **개인 정보를 이 파일에 넣지 않는다** — 계정 · 저장소 이름 · 키 · 사용자명 · 게이트웨이 주소 어느 것도. 이 파일만 떼어
#   남에게 주는 것이 이 파일이 있는 까닭이라, 하나라도 들면 그대로 따라 나간다.

# 칸별 설명
#   `-EnvFile` — 화면 껍데기(`install.ui.ps1`)가 사람이 넣은 값을 임시 파일로 건넨다. 몸통은 평소처럼 읽는다 — 값을 받는
#     길이 하나라 화면 갈래와 콘솔 갈래가 같은 코드를 탄다.
#   `-NoUpgrade` — 기본은 **있으면 올리고 없으면 깐다.** 이미 서 있는 PC(집 · 회사)는 「있으면 건너뛴다」로는 영영 안
#     올라가고, 자리를 물어 가르는 것은 이 파일의 몫이 아니다.
#     ⚠ **올리기를 꺼도 VC++ 런타임은 14.40 아래면 올린다** — 새 판을 따라가는 일이 아니라 그 판 아래에서 파이썬 확장이 죽는
#     것을 막는 일이다(`Install-VcRuntime` · claude-config 결정 0146). 설치 창의 「올리기」 칸 글자가 같은 말을 한다.
#   `-NoLaunch` — 기본은 끝에 창을 띄운다(그 한 손이 안 가면 심은 값이 아무 데도 안 걸린다). 자동화는 이 칸을 준다 — 이미
#     떠 있는 것이 있으면 여는 자리가 끌지 묻는 창을 띄우는데, 아무도 안 보는 자리에서는 영영 안 눌린다.
#     ⚠ **그 물음을 `-Yes` 에 걸지 않는다** — 화면 껍데기가 사람을 앞에 두고도 몸통을 `-Yes` 로 부르므로, 걸면 화면으로
#     깐 사람이 안 물어지게 된다. 누를 사람이 없는 자리(세션 0 · 서비스 · 스케줄러)는 `Ask-Restart` 가 잰다.
#   `-Describe` — 아무것도 안 깔고 고를 목록 · 저장소 자리 · 지난번에 고른 것 · 몸통만 아는 사실(자리 · 기본값 · 데스크탑 앱 행)만
#     내주고 나간다(라이브러리 뒤 `if ($Describe)` — 줄의 꼴은 그 머리말이 든다).
#     화면 껍데기가 칸을 짓는 목록의 진본은 `$Products` 하나다.
#   `-Pick claude,codex` — 고른 제품만 깐다. `none` 은 「하나도 안 고름」이다. `-NoVsCode` 는 VS Code 와 확장을 통째로 건너뛴다.
#     준 깃발이 먼저고 안 준 것은 지난번 기록이 채운다(「준비」의 「지난번에 고른 것」 칸). 기록도 없으면 `$Products` 의 기본값이다.
#   `-ChoicesFull` — 「고른 것을 다 넘긴다」. 설치 창이 준다 — 그 판은 안 준 스위치가 켬 · 안 준 `-PersonalFor` 가 없음 · 넘겨받은 값
#     파일에 없는 저장소 · 주소가 없음이다. 스위치의 「켬」은 글로 못 넘겨서다(파워셸 5.1 의 `-File` 은 `-NoVsCode:$false` 를 못 받는다).
#   `-DevTools` — 기록의 개발 도구 끔(`-NoDevTools` 로 깐 PC)을 되돌린다. 설치 창에는 그 칸이 없어 `Setup.exe -DevTools` 가 이 깃발을 넘긴다.
#   `-AutoRun` / `-NoAutoRun` — 로그온(보이는 콘솔 창)과 밤(숨긴 창)마다 작업 스케줄러가 이 몸통을 다시 돌려 깔린 것을
#     올리고 환경을 다시 맞춘다. 기본값은 값 파일의 `#autorun = yes|no` 인데, `-NoAutoRun` 으로 끈 PC 는 작업이 없는 한 `yes` 여도
#     안 건다(「자동 실행을 켜나」 칸). 설치본도 `#update-repo` 의 최신 릴리스로 간다(「마무리」의 「설치본 자신을 새 릴리스로 간다」 칸).
#   `-GhLoginOnly <결과 파일>` — 사람이 주는 칸이 아니다. 「프로그램」 걸음이 이 몸통을 숨은 자식으로 다시 띄울 때 넘긴다
#     (`Start-GhLoginChild`). 자식은 라이브러리만 읽고 빗장 앞에서 GitHub 로그인 창 하나를 띄운 뒤 결과를 그 파일에 적고 나간다.
# ⚠ **`install.cmd` 에 한글을 넣지 않는다.** cmd.exe 는 배치 파일을 콘솔 OEM 코드페이지(한국은 cp949)로 읽어, UTF-8 한글이
#   어긋나면 `rem` 이 안 잡히고 깨진 글자가 **명령으로 실행된다.** 그 파일의 설명은 BOM 이 붙은 이 파일이 든다.
param([switch]$Yes, [switch]$NoDevTools, [switch]$WithPersonalConfig, [string]$PersonalFor, [switch]$NoUpgrade,
      [switch]$NoLaunch, [string]$EnvFile, [switch]$Describe,
      [string]$Pick, [switch]$NoVsCode, [switch]$AutoRun, [switch]$NoAutoRun, [string]$GhLoginOnly,
      [switch]$ChoicesFull, [switch]$DevTools)

$ErrorActionPreference = 'Stop'

# ── 걸린 초 — 걸음마다 갈라 찍는다. 훅이 서기 전의 시간은 여기서만 갈린다 ────────────
# 초는 머리줄(`[n/N] 이름`)에 안 달고 걸음이 끝나는 자리에 따로 한 줄로 찍는다(`Exit-Step`) — 머리줄은 걸음이 시작될 때
#   찍히고, 화면 껍데기가 그 줄의 이름을 그대로 쓴다. 초 줄은 `[` 로 안 시작해 머리줄 무늬에 안 걸리고, 껍데기는 그것을
#   걸음 안의 낱줄로 읽어 막대를 조금 민다.
# 시계는 하나다 — 누적 초의 차로 재므로 「준비」부터 끝까지가 빠짐없이 갈리고, 걸음별 합이 끝의 총계와 맞는다.
$Sw     = [Diagnostics.Stopwatch]::StartNew()
$SwMark = 0

# ⚠ **네이티브 명령의 stderr 를 성공 스트림에 합치지 않는다 (`2>&1`).** 합치면 파워셸이 그 줄을 오류 레코드로 감싸고, 위
#   `Stop` 이 **그 자리에서 스크립트를 끝낸다** — `code --install-extension` 이 뱉는 Node deprecation 경고 한 줄이 설치를
#   통째로 죽인다. 판정도 망가진다: `Get-Ver` 가 판 대신 경고 줄을 읽는다.
# 버리지도 않는다 — 판정만 재는 자리는 버리고(`Get-Ver` 는 울타리 손 `Invoke-LoggedCapped` 가 받은 나가는 글만, 「도나」
#   `Test-Runs` · `Measure-Runs` 는 `Invoke-ProbeCapped` 가 띄운 자식의 두 스트림을 읽어 버린다), 설치하는 자리는 실패의 까닭이
#   유일한 단서라 파일로 잡아 두고 실패할 때만 편다.

# 콘솔 UTF-8 강제. PowerShell 5.1 기본은 시스템 코드페이지(한국은 cp949)라 한글이 깨진다.
# ⚠ **던지게 두지 않는다.** 출력이 파일로 돌려진 채로 뜨면 이 줄이 걸릴 수 있고, 위 `Stop` 이 그 자리에서 끝내 **한 줄도
#   안 찍힌 채 죽는다.** 인코딩은 편의지 조건이 아니다.
$OutputEncoding = [System.Text.Encoding]::UTF8
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$Here    = Split-Path -Parent $MyInvocation.MyCommand.Path
# 로컬 페이지를 기본 브라우저로 여는 손(`Open-InBrowser`)은 곁의 조각이 든다 — 설치 창과 같이 쓴다
$OpenPageLib = Join-Path $Here 'open-page.ps1'
if (Test-Path -LiteralPath $OpenPageLib) { . $OpenPageLib }
if (-not $EnvFile) { $EnvFile = Join-Path $Here 'install.env' }
# ── 짐의 사실을 읽는 값 파일 — **이 엔진 곁에 딸려 온 `install.env` 다.** 없을 때만 넘겨받은 값 파일을 읽는다 (PAISetup #45) ──
# 지시(`#이름 = 값`)와 값 줄은 뽑는 자가 진본에서 싣는 배포본의 사실이지 사람이 고른 것이 아니라, 판마다 그 판의 짐에서 읽는다.
#   넘겨받은 값 파일(`$EnvFile`)에서 읽는 것은 이 회차가 받은 것뿐이다 — 화면 · 밤 자동 실행이 넘긴 자리(`#site`) · 사람이 넣은 키와 주소 ·
#   설정 저장소 주소(「준비」의 「지난번에 고른 것」 칸 · `Read-RunValues`).
# ⚠ **줄이 아니라 파일로 물러선다.** 딸려 온 파일에 줄이 없으면 그 배포본이 그 값을 안 든 것이다 — 넘겨받은 파일의 줄로
#   메우면 새 배포본이 뺀 값이 되살아난다. 옛 자동 실행이 넘기는 얼린 사본은 지난 판 짐의 줄을 다 든다.
$DistEnvFile = Join-Path $Here 'install.env'
if (-not (Test-Path -LiteralPath $DistEnvFile)) { $DistEnvFile = $EnvFile }
$Fails   = New-Object System.Collections.Generic.List[string]
$Planted = @{}
# 도중에 멎은 칸 — 칸 열쇠(걸음은 `$Steps` 의 열쇠 · 그 밖은 칸 이름) → 던진 자리. 걸음 경계(`Write-StepFault`)가 채운다.
$StepFaults = [ordered]@{}
# 끝 검증의 칸 목록 — 「검증」 칸이 채운다. 칸 경계 밖에서 비워 둔다 — 검증이 첫 칸 앞에서 멎으면 빈 값이 끝 셈에서 빨간 칸 하나로 읽힌다.
$checks = @()

# ── 옛 제작자 칸으로 창 없이 불리면 — 설치는 그대로 가고, 끝나면 한 번만 알린다 (claude-config 결정 0099) ──────────
# 옛 자동 실행 기록(`autorun.args`)은 도구별로 갈리기 전의 `-WithPersonalConfig` 하나를 들고, 옛 자동 실행 스크립트가 그 기록으로
#   이 몸통을 창 없이(`-Yes`) 부른다. 그 칸은 Claude 로 읽고(「준비」의 「제작자 세트를 받을 도구」) 설치를 멈추지 않는다 —
#   자동 실행은 조용히 올리려고 있는 것이라, 고를 때까지 세우면 올림이 멎고 로그온마다 창이 뜬다. 대신 끝에서 기록을 새 꼴로
#   쓰고(「마무리」의 「회차를 넘기는 기록」) 설치 창을 한 번 띄운다(「옛 제작자 칸을 이어받은 판의 마무리」). 창이 부르는 판은
#   `-PersonalFor` 로 넘기므로 여기 안 걸린다.
$PersonalUpgrade = [bool]($Yes -and $WithPersonalConfig -and -not $PersonalFor -and -not $Describe)

# ── 이 배포본의 판 — **진본은 곁의 `VERSION` 한 줄이고 릴리스 태그가 그 값에서 난다.** ──
# 창(`install.ui.ps1`)도 같은 파일을 같은 꼴로 읽는다 — 무인 실행(autorun)에는 창이 없어 넘겨받을 수 없다. 없으면 빈 값으로
#   가고, 이 값을 쓰는 자리(씨앗 판 줄)가 안 적고 넘어간다.
# ⚠ **BOM 을 손으로 걷는다.** 이 파일은 인코딩 문지기가 안 보는 종류라(`*.ps1`·`*.cmd` 만 본다) BOM 이 붙어 저장되면 번호
#   앞에 안 보이는 글자가 붙고, 화면에는 멀쩡히 찍히되 **견주는 자리에서만** 안 맞는다.
$DistVersion = ''
$DistVersionPath = Join-Path $Here 'VERSION'
if (Test-Path -LiteralPath $DistVersionPath) {
  try {
    $DistVersion = (([string](Get-Content -LiteralPath $DistVersionPath -TotalCount 1 -Encoding UTF8)) `
                     -replace "^﻿", '').Trim()
  } catch { $DistVersion = '' }
}

# ── 홈 아래 우리가 쓰는 자리 — **이름은 여기 한 자리다** ────────────────────────
# 걸음들이 이 아래에 파일을 쓰고 끝의 검증이 같은 자리를 다시 잰다 — 글자를 자리마다 박으면 한쪽만 고쳐지는 날 재는 자가
#   딴 자리를 보고 [O] 를 찍는다 (#3).
$homeDir = Join-Path $env:USERPROFILE '.claude'
# 홈 씨앗 — 짐의 설정 저장소 씨앗이 「공용 자산」 걸음에서 거울로 깔리는 자리(그 걸음의 `$envAssets` 줄이 이 값을 쓴다)와 그 훅 폴더.
#   씨앗의 손 · 훅 · 예시를 부르는 자리와 끝 검증은 다 이 둘에서 잇는다(PAISetup #47 ③).
$ConfigSeedHome  = Join-Path $homeDir 'seeds\config-repo'
$ConfigSeedHooks = Join-Path $ConfigSeedHome '.claude\hooks'
# 저장소를 받는 자리 — `-Describe` 갈래가 이 값을 `config-repo-root` 줄로 내주고, 화면이 그 줄로 자리를 보여 주고 폴더를 연다.
# ⚠ **넘겨받는 쪽의 `ROOT` 와 짝이다** — 자리를 옮기면 둘을 같이 고친다. 하나만 고치면 설치는 한 데로 받고 다른 쪽은 딴
#   데서 찾는다.
$configRepoRoot = Join-Path $env:USERPROFILE 'repos'

# ── 회차를 넘기는 기록의 자리 — **사람이 고른 것만 든다** (PAISetup #45) ────────────────────────
# 설치 창 · 콘솔 · 로그온 · 밤 자동 실행이 다 이 자리를 몸통의 한 손(`Read-ChoiceRecord`)으로 읽는다 — 창은 `-Describe` 의
#   `record|이름|값` 줄로 받는다. 자동 실행의 켜짐과 상관없이 회차마다 「마무리」의 「회차를 넘기는 기록」 칸이 다시 쓴다.
#   짐의 사실(지시 · 값 줄)은 안 든다 — 판마다 그 판의 짐에서 읽는다(`$DistEnvFile`).
# 꼴은 `이름=값` 한 줄씩이다(`Read-EnvFile` 이 읽는다). 이름은 `$ChoiceKeys` 이고, 골랐는데 아무것도 없으면 `$ChoiceNone` 이다 —
#   빈 값으로 적지 않는다: 몸통의 `-Pick` · `-PersonalFor` 도 같은 글자를 받는데, 파워셸 5.1 의 `-File` 은 빈 인자를 떨궈
#   「Missing an argument」로 몸통이 안 뜬다.
# 옛 꼴 둘(선택 파일 `autorun.args` · 얼린 값 파일 `install.env`)은 새 기록이 없을 때만 읽고, 새 기록을 쓴 뒤 걷는다.
$RecordRoot       = Join-Path $env:LOCALAPPDATA 'Claude Code Setup'
$ChoiceRecord     = Join-Path $RecordRoot 'choices.env'
$LegacyChoiceArgs = Join-Path $RecordRoot 'autorun.args'
$LegacyChoiceEnv  = Join-Path $RecordRoot 'install.env'
$ChoiceKeys       = @('pick', 'vscode', 'devtools', 'personal', 'config-repo', 'gateway-url')
$ChoiceNone       = 'none'
# 사람이 끈 자동 실행의 기록 — `-Describe` 가 `record|autorun|off` 로 내고, 「자동 실행을 켜나」 칸과 「부팅 시 자동 실행」 칸이
#   읽고 쓴다. 언제 적고 지우나는 그 두 칸이 든다.
$AutoRunOffRecord = Join-Path $RecordRoot '.autorun-off'
# 자동 실행 작업 이름 둘 — 「부팅 시 자동 실행」 칸이 이 이름으로 걸고 걷고, 깃발 없는 판의 켜나(`Get-AutoRunDefault`)가 이 이름으로
#   작업이 있나 묻는다. 설치 창은 이름을 모른다 — `-Describe` 의 `autorun|on·off` 줄로 그 답만 받는다.
$AutoRunTaskName      = 'PAISetup-AutoRun'
$AutoRunNightTaskName = 'PAISetup-AutoRun-Night'
# 회사 키 덩이 — 이 사용자만 푸는 암호(DPAPI)로 둔 회사 키다. 「키와 값」이 맞추고 푼다(PAISetup #44). `-Describe` 는 풀리는 덩이가 있나만
#   `company-key|yes·no` 로 낸다 — 값은 안 낸다. 창은 그 답으로 사내 키 칸이 비어도 설치를 받는다.
$CompanyKeyBlob   = Join-Path $RecordRoot 'company-key.dpapi'
# 장부 — 설치기가 심은 것이다(사람이 고른 것이 아니다). 걸음마다 제 자리를 맞춘 뒤 다시 쓰고, 다음 판이 걷을 것을 이것으로 가른다 —
#   꼴과 읽고 쓰는 손은 라이브러리의 「장부」 칸이 든다(PAISetup #44). 이름 · 자리는 옛 판의 「Claude 홈 설정」 기록 그대로다 — 설정
#   저장소의 세션 훅이 그 permissions 줄을 읽고(claude-config 결정 0119), 옛 판이 남긴 줄을 이어 읽는다.
$ClaudePlantLedger = Join-Path $RecordRoot 'claude-settings.tsv'

# ── 고르는 축 — **제품이다.** 표 셋(CLI · 확장 · 데스크탑 앱)은 같은 축의 세 단면이고, 한 제품이 그 셋에 한 줄씩 든다 ──
# 사람은 「어느 도구를 쓰나」로 고르지 「CLI 냐 확장이냐」로 안 고른다. 기본값도 이 표가 든다 — 화면이 제 값을 따로 들면 두
#   벌이 된다.
$Products = @(
  @{ Key='claude';      Label='Claude';      Default=$true  }
  @{ Key='codex';       Label='Codex';       Default=$true  }
  @{ Key='antigravity'; Label='구글 Antigravity'; Default=$true  }
  # 기본이 꺼져 있다 — 파일럿이라 켜는 사람만 받는다(이슈 #16). 데스크탑 앱과 CLI 에 한 줄씩 들고 확장 표에는 없다.
  @{ Key='copilot';     Label='GitHub Copilot'; Default=$false }
)
# 걷은 제품 이름 — 지난 설치가 고른 값(로그온 자동 실행이 든 `-Pick`)에 남아 들어온다. 「준비」의 「고른 제품」 칸이 이 이름을
#   말없이 빼고, 「모르는 제품 이름」 노란 줄은 이 목록 밖의 이름에만 선다(claude-config 결정 0136).
$RetiredProducts = @('gemini')
# 제작자 세트를 받는 도구 — 도구 이름(`-PersonalFor` · `PAISETUP_PERSONAL` 에 드는 글자) · 그 도구의 홈이 서는 제품 · 화면 글자.
#   「제작자 세트를 받을 도구」 칸이 이 표로 고른 도구를 가르고, `-Describe` 가 `personal|도구|제품|글자` 줄로 내 설치 창이 칸을 짓는다.
$PersonalTools = @(
  @{ Tool = 'claude'; Product = 'claude';      Label = 'Claude' }
  @{ Tool = 'codex';  Product = 'codex';       Label = 'Codex' }
  @{ Tool = 'agy';    Product = 'antigravity'; Label = 'agy' }
)

# ── 공용 프로그램 — **목록이 진본이다.** 늘리려면 한 줄을 더한다 ────────────────
#    `Need` — core = 확장이 돌기까지 없으면 안 되는 것 · dev = 코드를 짤 사람에게만(`-NoDevTools` 가 건너뛴다) ·
#    vscode = core 의 갈래로 `-NoVsCode` 가 이 한 줄과 확장을 같이 건너뛴다. CLI 들은 npm 이나 winget 이 깔아 `$Clis` 가 든다.
$Apps = @(
  @{ Name='VS Code';    Id='Microsoft.VisualStudioCode'; Cmd='code';   Arg='--version'; Need='vscode' }
  # `Scope='machine'` — winget 이 이 꾸러미에 고르는 설치본이 기계 범위(MSI)라 승격이 든다. 승인 창이 뜨는 PC 의 무인 판에서는
  #   안 걸고 노란 줄로 미룬다(결정 0146 의 VC++ 규칙과 같은 자 · PAISetup #34 ③)
  @{ Name='Node.js';    Id='OpenJS.NodeJS.LTS';          Cmd='node';   Arg='--version'; Need='core'; Scope='machine' }
  @{ Name='Git';        Id='Git.Git';                    Cmd='git';    Arg='--version'; Need='dev'  }
  # 판은 이 줄에 안 적는다 — 값 파일의 `#python-version` 이 들고, 「준비」의 「파이썬 판」 칸이 이 줄의 Id 를 짓는다
  @{ Name='Python';     Id=$null;                        Cmd='python'; Arg='--version'; Need='dev'  }
  @{ Name='GitHub CLI'; Id='GitHub.cli';                 Cmd='gh';     Arg='--version'; Need='dev';  Scope='machine' }
)

# ── 확장과 CLI — **목록이 진본이다.** 깔 때도 끝에 잴 때도 이 두 표에서 판다 (결정 0041 · 0045) ──
# 어디서나 깐다 — 자리가 가르는 것은 프로그램이 아니라 그 뒤에 무엇으로 붙나다. 사내는 회사 키 · 설정 틀 · 프록시로
#   게이트웨이에 붙고(`$wantCodex` · `$wantAgy`), 사외는 각자 로그인(Codex 는 ChatGPT · 안티그래비티는 Google)으로 쓴다.
# Codex 확장은 CLI 의 `~/.codex/config.toml` 을 같이 읽어 게이트웨이를 탄다. 사용자 정의 프로바이더에서 CLI 와 다르게 구는
#   이슈(openai/codex #27695)가 열려 있는 동안 확장 안의 한 턴은 사람이 잰다 — 그 이슈가 닫히면 이 줄을 걷는다.
# 안티그래비티 확장은 `$DesktopApps` 의 「Antigravity 데스크탑」(VS Code 를 대신하는 별개 편집기)과 다른 물건이다 — VS Code 에
#   붙어 사이드바를 내고, 짝인 `agy`(`~/.gemini/bin/agy.exe` · 188MB · `AGY_ENABLE_HUB=1` 로 띄운다)를 스스로 받는다. 설치기는
#   그 바이너리를 안 심는다. 게이트웨이에 물리는 자리는 「사내 연결」의 「Codex · 안티그래비티 설정」 칸이 든다.
$Extensions = @(
  @{ Key='claude';      Id='anthropic.claude-code';                  Label='클로드 확장'                }
  @{ Key='codex';       Id='openai.chatgpt';                         Label='Codex 확장'                 }
  @{ Key='antigravity'; Id='Google.google-antigravity';              Label='안티그래비티 확장'          }
)
# `Via` — 없으면 npm, `winget` 이면 `Install-WingetCli` 가 든다. 구글이 `agy` 를 npm 으로 안 내주고(그 이름은 남이 올린
#   자리표시자다), 갈림이 표 안에 있어 CLI 가 늘 때 볼 자리가 한 곳이다.
# 안티그래비티 CLI 는 벤더 설치 스크립트가 아니라 winget(`Google.AntigravityCLI`)으로 받는다 — 매니페스트가 `InstallerSha256`
#   을 들어 지문을 잴 수 있고(벤더 스크립트는 해시를 안 낸다) arm64 도 함께 든다. winget 판이 벤더 판보다 한 판 뒤처질 수 있다.
#   ⚠ **winget 밖의 길로 깐 `agy` 는 안 올라간다** — `Install-WingetCli` 가 `agy` 가 잡히면 「있음」으로 지나가는데 그 설치본을
#   winget 은 모르므로 올리기도 조용히 지나간다. 옮기려면 사람이 그것을 한 번 걷는다 — 남의 설치본은 우리가 안 지운다.
#   VS Code 의 안티그래비티 확장이 받는 `agy` 는 PATH 에 안 서므로 확장을 깐 기계도 이 줄을 건너뛰지 않는다(같은 것을 두 번
#   받는다 — 줄이려면 제품 칸을 끈다).
$Clis = @(
  @{ Key='claude'; Pkg='@anthropic-ai/claude-code'; Cmd='claude'; Label='Claude Code CLI' }
  @{ Key='codex';  Pkg='@openai/codex';             Cmd='codex';  Label='Codex CLI'       }
  # `Cmd` 는 winget 매니페스트의 `Commands:` 가 정한다 — winget 이 받은 `cli_windows_x64.exe` 를 `agy` 로 세워 제 패키지 자리
  #   (`…\WinGet\Packages\Google.AntigravityCLI_…\agy.exe`)에 두고 그 자리를 사용자 PATH 에 심는다.
  @{ Key='antigravity'; Via='winget'; Cmd='agy';    Label='안티그래비티 CLI'
     Id='Google.AntigravityCLI' }
  # 자리를 안 가리고 깐다(결정 0045 · 0093). Codex · Copilot 맡기기가 Copilot 을 쓰나는 자리 값 `CC_BG_AGENTS` 를 읽는 래퍼의
  #   몫이다. winget 의 `GitHub.Copilot` 은 이름이 비슷한 딴 물건이라 npm 꾸러미로 받는다.
  @{ Key='copilot'; Pkg='@github/copilot';          Cmd='copilot'; Label='Copilot CLI' }
  # 브라우저 MCP 의 꾸러미 — 고른 제품이 `For` 가운데 하나라도 있으면 깐다. 그 제품들에 다는 서버(`playwright mcp`)가 이 전역
  #   꾸러미에 들어 있다(claude-config 결정 0149). 브라우저 받기와 등록은 「도구별 홈」 걸음의 「브라우저 MCP」 칸이 든다.
  @{ Key='playwright'; Pkg='playwright'; Cmd='playwright'; Label='Playwright (브라우저 MCP)'; For=@('claude','codex','antigravity') }
  # Claude Code 의 Read 가 PDF 를 열 때 페이지를 그림으로 그리는 손 — poppler 의 `pdftoppm`. 없으면 Read 가 「pdftoppm is not installed」로
  #   지고, 사내 게이트웨이는 `document` 블록을 삼키므로 PDF 가 모델에 보이는 길은 그림뿐이다(claude-config #193 ③㉡ · 회사 실측
  #   2026-10-18). winget 휴대용(zip · 사용자 범위)이라 승인이 안 들고, winget 이 패키지의 `bin` 자리를 사용자 PATH 에 심는다.
  #   ⚠ `Arg='-v'` — pdftoppm 은 `--version` 을 모르는 옵션으로 받아 0 아닌 값을 내니, 그 자로 재면 「못 쟀다」로 접혀 영영 안 깔린다.
  @{ Key='poppler'; Via='winget'; Cmd='pdftoppm'; Arg='-v'; Label='poppler (PDF 를 그림으로)'; Id='oschwartz10612.Poppler'; For=@('claude') }
  # 제작자 칸이 보내는 스킬이 부르는 도구 — 칸을 켠 PC 에만 깐다(`Maker`). `doc-coordinate-audit` 가 링크 · 경로는 lychee,
  #   마크다운 구조는 markdownlint-cli2 로 잰다(설정 저장소의 세션 훅도 둘을 까지만, 그 저장소를 안 붙인 PC 에도 서야 해서
  #   여기서도 깐다). lychee 는 winget 휴대용(zip)이라 사용자 범위에 풀리고 그 자리(`WinGet\Links`
  #   나 패키지 폴더 — winget 이 PC 마다 고른다)가 사용자 PATH 에 걸린다 — 관리자 승인이 안 든다.
  @{ Key='lychee';       Via='winget'; Cmd='lychee'; Label='lychee'; Id='lycheeverse.lychee'; Maker=$true }
  @{ Key='markdownlint'; Pkg='markdownlint-cli2'; Cmd='markdownlint-cli2'; Label='markdownlint-cli2'; Maker=$true }
)
# npm 이 전역에 깐 CLI 가 서는 자리 — 배선(`Update-RuntimePath`)이 이 창에 태우고, 마무리의 「사용자 범위 명령 자리」가 사용자
#   PATH 에 심고, 끝 검증이 사용자 PATH 에서 잰다(claude-config 결정 0143 · PAISetup #30 ②). 세 자리가 이 한 줄을 읽는다.
$NpmGlobalDir = "$env:APPDATA\npm"

# ── VC++ 런타임 — 파이썬의 C++ 확장이 싣는 `msvcp140.dll` (claude-config 결정 0146) ─────────────────────────
# markitdown → magika → onnxruntime 의 확장 모듈이 이 런타임을 싣는다 — 판이 낮으면 `import` 하는 순간 파이썬이 죽는다(PAISetup #30).
#   공식 재배포 패키지를 winget 으로 받는다. 기계 범위라 관리자 승격이 든다(`Get-ElevationGo`).
$VcRuntime = @{ Name = 'VC++ 런타임'; Id = 'Microsoft.VCRedist.2015+.x64'; Dll = 'msvcp140.dll' }
# 받아들이는 가장 낮은 판 — 14.40 에서 STL 의 `std::mutex` 꼴이 바뀌어, 그 뒤 도구로 지은 모듈을 그보다 옛 런타임에서 돌리면 초기화 중에 죽는다.
#   설치 창의 「올리기」 칸 글자는 이 값을 `-Describe` 의 `vcruntime-min|` 줄로 받는다. `-NoUpgrade` 칸별 설명은 이 판을 글자로 든다 —
#   옮기면 그것도 고친다.
$VcRuntimeMin = [version]'14.40'
# winget · 설치본이 낸 값 가운데 뜻이 정해진 것(결정 0146 — winget 「Return codes」 · Windows Installer 오류 값). 올랐나는 파일의 판이
#   가르고, 이 값들은 안 오른 까닭의 말만 고른다.
$VcRedistRcReboot    = @(3010, 1641, 0x8A150109, 0x8A15010A, 0x8A15010B)   # 다시 시작해야 끝난다 · 다시 시작한 뒤 다시 깐다
$VcRedistRcCancelled = @(1602, 1223, 0x8A15010C, 0x800704C7)                # 사람이(승인 창에서) 물렸다
$VcRedistRcNewer     = @(1638, 0x8A15002B, 0x8A150061, 0x8A15010D, 0x8A15010E)  # 같거나 더 새 판이 이미 깔렸다

# ── Node 가 말을 거는 자리 — **목록이 진본이다** ─────────────────────────────────
# 신뢰를 이을 근거를 여기서 잰다(`Wire-NodeTrust`). Node 를 태우는 곳이 늘면 한 줄 더한다.
#   이 설치가 실제로 여는 곳만 든다 — 신뢰 저장소를 통째로 훑으면 이 PC 가 믿는 CA 를 다 옮겨 적게 되고, 사본은 낡는다.
$TlsHosts = @(
  'marketplace.visualstudio.com'   # 확장을 받는 곳
  'update.code.visualstudio.com'   # VS Code 가 판을 묻는 곳
  'registry.npmjs.org'             # Claude Code CLI 를 받는 곳
)

# ── 묻고 잴 이름 표(`$Vars`)는 「준비」에 선다 — 이름과 설명만 들고 값은 없다 ────────────────────────
# 심는 목록이 아니다 — 값 파일에 있는 이름은 표에 없어도 다 심는다(「키와 값」의 「값 파일이 든 나머지 이름」 칸). 표가 드는
#   것은 없을 때 물을 것과 끝에 재서 [O]/[X] 로 찍을 것이다.
# 게이트웨이는 `ANTHROPIC_API_KEY`(x-api-key)와 `ANTHROPIC_AUTH_TOKEN`(Bearer)을 둘 다 받는다. CLI 는 AUTH_TOKEN 으로도 서므로
#   이름을 하나로 둔다 — 둘을 다 물으면 받는 사람이 어느 것이 제 키인지 판단해야 한다.
# `Gateway` 는 「게이트웨이를 쓸 때 필요」다 — 쓰나는 자리에 달렸고 자리는 프로브(`#site-probe`)가 가른다. 표는 주소가 있으면
#   쓰고 없으면 안 쓰는 것으로만 판정한다 — 자리 판별을 표에 옮겨 적으면 같은 규칙이 두 자리에 산다.

# ── 데스크탑 앱 — **목록이 진본이다.** 「프로그램」의 「데스크탑 앱 설치」 칸이 깔 때도, 「마무리」의 「연다」 칸이 띄울 것을
#    찾을 때도 이 표에서 판다 ──
# 앱마다 설치 길이 달라 표가 id 만이 아니라 길(`Via`)까지 든다 — 갈림이 설치 칸 안에 숨으면 앱이 늘 때 표만 고쳐서는 안 걸린다.
#   · `winget` — winget 이 깔고 winget 이 잰다. `Source` 가 어느 소스인지 든다
#   · `setup`  — 제 설치본을 받아 조용히 돌린다. winget 이 모르는 앱이다
# `App` — 시작 메뉴에 뜨는 이름(띄울 때 찾는 글자). 패키지 id 와 다른 것을 가리켜 따로 적는다 — 스토어 제품은 id 가
#   `9PLM9XGG6VKS` 꼴이라 거기서 팔 것이 없다.
# 「깔렸나」는 시작 메뉴 이름(`App`) → 윈도우의 설치 목록 → winget 목록 차례로 묻는다(`Measure-DesktopApp` · 결정 0145).
#   설치 목록의 자는 행이 든다:
#     · `Reg`  — 레지스트리 `Uninstall` 의 `DisplayName` 에 거는 `-like` 꼴. 「있다」만 세운다(이름은 벤더가 바꾼다)
#     · `Appx` — 스토어 꼴 앱의 꾸러미 가족. 「있다」도 「없다」도 세우고, 이 행에는 winget 목록을 안 묻는다
#   둘 다 없는 행은 시작 메뉴와 winget 목록이 잰다.
# `When` — 언제 까나는 행이 든다(이슈 #16 · 결정 0059). 게이트웨이를 물어야 쓸모가 있나는 앱의 성질이라서다. 값 파일의
#   `#desktop-app` 은 전체 스위치로 남는다(없으면 아무것도 안 깐다).
#     · `offsite` — 사외로 판정될 때만. 게이트웨이를 물어야 쓸모가 있는 앱들. 안 적으면 이 값이다
#     · `any`     — 자리를 안 가린다. 제 인증으로 서는 앱
# `Requires` — 짝으로 먼저 깔 런타임. winget 매니페스트의 `Dependencies` 가 비어 winget 이 안 챙기는 자리를 우리가 챈다.
#   공용 목록(`$Apps`)에 안 넣어 그 앱을 고른 사람만 받는다.
$DesktopApps = @(
  @{ Key = 'claude'; Label = 'Claude 데스크탑'; App = 'Claude'
     Via = 'winget'; Id = 'Anthropic.Claude'; Source = 'winget' }
  # ⚠ **코덱스는 ChatGPT 앱 안에 산다 — `App` 은 `ChatGPT` 여야 한다.** 사람 눈에 닿는 이름(시작 메뉴 · 매니페스트
  #   `DisplayName` · 실행 파일 `app/ChatGPT.exe`)이 다 `ChatGPT` 이고 `Codex` 는 꾸러미 이름(`OpenAI.Codex_…!App`)에만 남는다.
  #   `Codex` 로 두면 멀쩡히 깔아 놓고 이름으로 되찾지 못해 「설치 실패」로 찍는다.
  # 길이 둘이고 두 길이 지는 자리가 엇갈린다 — 앞길이 흔한 갈래를 들고 지면 뒷길(`Fallback`)로 간다:
  #     · winget msstore — TLS 를 가로채는 회선에서는 고정 인증서 검사가 `0x8a15005e` 로 져 소스를 못 연다 · 열린 회선에서는
  #       조용히 깐다
  #     · 스토어 설치 스텁(`StoreInstaller.exe /S` · 웹의 [다운로드] 단추가 주는 공식 길) — 스토어가 막힌 회선에서는 넘길 곳이
  #       없어 제가 조용히 깐다 · 열린 회선에서는 스토어 창으로 넘기고 빠진다
  # `NoSelfUpgrade` — 올리기는 안 한다. 스토어 앱 갱신은 윈도우 업데이트를 타는데 사내에서 그쪽이 끊긴다(`0x80072EFD`) — 없으면
  #   깔고 있으면 둔다.
  # 깔렸나는 꾸러미 가족(`Appx`)이 잰다 — msstore 의 winget 목록은 깔린 채로 「안 깔렸다」를 내고, 막힌 회선에서는 열리지도
  #   않는다. 가족 이름은 시작 메뉴 손잡이(`OpenAI.Codex_2p2nqsd0c76g0!App`)의 앞마디다.
  @{ Key = 'codex';  Label = 'Codex 데스크탑';  App = 'ChatGPT'; Appx = 'OpenAI.Codex_2p2nqsd0c76g0'
     Via = 'winget'; Id = '9PLM9XGG6VKS'; Source = 'msstore'; NoSelfUpgrade = $true
     Fallback = @{ Via = 'setup'; SilentArgs = @('/S')
                   Url = 'https://get.microsoft.com/installer/download/9PLM9XGG6VKS' } }
  # Gemini 데스크탑은 안 깐다 — 사내 회선에서 구글 스텁(11.8MB)은 받아지는데 그 스텁이 알맹이를 받으러 갈 때 끊기고
  #   (`0x80072EFE` 연결 중단), 구글 갱신기가 제 작업을 지우고 되돌아 나간다. 집에서는 깔리므로 필요하면 사람이
  #   <https://gemini.google.com/app> 에서 받는다 — 그 자리는 안티그래비티가 든다.
  # 안티그래비티는 winget 이 판 없는 주소와 설치 꼴(nullsoft · `/S`)을 댄다. 깔린 뒤에는 앱이 제 자동 갱신(electron-builder ·
  #   `resources/app-update.yml`)으로 따라가고, winget 갱신은 그 위의 보험이다.
  # ⚠ **패키지 이름을 바꿀 때 받는 호스트를 다시 본다.** `Google.Antigravity`(「Antigravity 2.0」)는 `storage.googleapis.com`
  #   에서 와 사내 회선에서 열리고, 같은 페이지의 「Antigravity IDE (Standalone)」은 `edgedl.me.gvt1.com` 에서 와 사내에서
  #   TLS 악수부터 진다 — 둘은 판 번호도 계보도 다른 별개 물건이다.
  # `Reg` — 설치 목록 이름에 판이 붙는다(`Antigravity 2.22.0` · HKCU). 곁에 같은 머리의 딴 물건 `Antigravity CLI` 가 서므로 이름
  #   뒤에 숫자가 오는 꼴만 잡는다.
  @{ Key = 'antigravity'; Label = 'Antigravity 데스크탑'; App = 'Antigravity'; Reg = 'Antigravity [0-9]*'
     Via = 'winget'; Id = 'Google.Antigravity'; Source = 'winget' }
  # `When = 'any'` — 게이트웨이를 안 타고 제 인증으로 GitHub 에 붙어 사내에서도 깔 값이 있다.
  # ⚠ **id 는 `GitHub.CopilotApp` 이다** — `GitHub.Copilot` 은 CLI 쪽 딴 물건이다. 지문은 winget 매니페스트의
  #   `InstallerSha256` 이 든다.
  # `Requires` — WebView2 를 타는데 매니페스트에 `Dependencies` 가 없어, 없는 기계(사내 VDI 이미지)에서는 설치가 그 자리에서
  #   진다. 있으면 안 깐다(레지스트리에 묻는다).
  # 로그인은 사람이 한다 — 대화형 인증(회사 IdP · MFA · 기기 조건)이라 설치기가 낄 자리가 없다. 사외 개인 PC 에서 회사 계정은
  #   조건부 액세스가 막고(기기 미등록 `53003`) 그때는 개인 계정으로 쓴다 — 설치의 실패가 아니다.
  # `Reg` — 설치 목록 이름은 `GitHub Copilot` 그대로다(HKCU). 기계 범위의 `Copilot` 은 Microsoft Copilot 이라 이름 전체로 건다.
  @{ Key = 'copilot'; Label = 'GitHub Copilot 데스크탑'; App = 'GitHub Copilot'; Reg = 'GitHub Copilot'
     Via = 'winget'; Id = 'GitHub.CopilotApp'; Source = 'winget'; When = 'any'
     Requires = @('Microsoft.EdgeWebView2Runtime') }
)

# ── 큰 걸음 — **머리줄과 걸린 초 줄이 이 표에서 난다** ─────────────────────────────────────
#    번호는 표의 차례, 분모는 표의 길이다. 흐름은 열쇠로 들고 난다(`Enter-Step` · `Exit-Step`).
$Steps = @(
  @{ Key = 'programs';   Title = '프로그램' }
  @{ Key = 'extensions'; Title = 'VS Code 확장' }
  @{ Key = 'cli';        Title = 'CLI' }
  @{ Key = 'keys';       Title = '키와 값' }
  @{ Key = 'site';       Title = '사내 연결' }
  @{ Key = 'home';       Title = 'Claude 홈 설정' }
  @{ Key = 'assets';     Title = '공용 자산' }
  @{ Key = 'tools';      Title = '도구별 홈' }
  @{ Key = 'repo';       Title = '설정 저장소' }
  @{ Key = 'register';   Title = 'Claude 플러그인' }
)

#region 라이브러리 — 흐름이 부르는 함수는 다 여기 선다. 정의만 있고 도는 문장은 없다

#region 화면 — 진행 · 걸린 시간 · 실패 까닭 · 로그 끝 줄을 찍고, 물음창을 띄운다

# 걸음 하나가 끝난 줄 — `── 글자 — 마쳤다 (N초)` 를 찍고 시계의 눈금(`SwMark`)을 지금으로 옮긴다. 걸음 경계에서만 부른다.
function Write-Elapsed([string]$Text) {
  $now = [int]$Sw.Elapsed.TotalSeconds
  Write-Host ("  ── $Text — 마쳤다 (" + ($now - $script:SwMark) + "초)") -ForegroundColor DarkGray
  $script:SwMark = $now
}

# ── 걸음 **안**의 한 구간 — 걸음 경계를 안 옮긴다 ─────────────────────────────────
# 받는 것 — 이름 · 시작 누적 초(`Get-Took`). `· 이름 — N초` 한 줄을 찍기만 하고 `SwMark` 는 안 건드린다.
# ⚠ **걸음 안에서는 `Write-Elapsed` 를 부르지 않는다** — 저쪽은 `SwMark` 를 옮기므로 그 걸음의 값이 이미 센 구간만큼 깎이고,
#   걸음별 합이 총계와 맞는다는 보증(`$Sw` 곁말)이 조용히 깨진다.
# 구간은 걸음의 부분집합이라 합이 걸음과 안 맞는 것이 정상이다 — 남는 몫이 곧 아직 안 가른 몫이다.
function Write-Took([string]$Text, [int]$From) {
  Write-Host ("    · $Text — " + ([int]$Sw.Elapsed.TotalSeconds - $From) + "초") -ForegroundColor DarkGray
}

# 지금 누적 초 — `Write-Took` 에 넘길 시작 값을 집는다. 부르는 쪽이 이름 있는 변수에 받아
# 둬야 구간이 어디서 시작했는지가 코드에 남는다.
function Get-Took { [int]$Sw.Elapsed.TotalSeconds }

# ── 물음창 — **묻는 자리가 둘이라 띄우기는 한 자리가 든다** ──────────────────────
# 받는 것 — 제목 · 본문. 예/아니요 창을 띄우고 「예」면 `$true` 를 낸다. 「누를 사람이 있나」는 부르는 쪽이 잰다.
# ⚠ **임자 없는 물음창은 뒤로 숨는다** — 안 보이는 창을 아무도 안 눌러 설치가 영영 안 끝난다(확인창이 VS Code 뒤에 숨는다).
#   작업표시줄에 안 남는 1px 창을 먼저 활성화해 메시지박스를 앞으로 가져온다.
function Show-AskDialog([string]$Title, [string]$Message) {
  Add-Type -AssemblyName System.Windows.Forms
  $owner = New-Object Windows.Forms.Form
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
    return ([Windows.Forms.MessageBox]::Show(
      $owner, $Message, $Title, 'YesNo', 'Warning') -eq 'Yes')
  } finally { $owner.Dispose() }
}

# 실패 사유 한 줄 — 오류 레코드를 받아 `갈래 : 글`(160자까지)을 낸다. 까닭을 대는 자리라 읽히게 잘라 준다.
#   가로채는 프록시는 오류를 HTML 페이지 통째로, 줄바꿈 없이 주기도 한다 — 그대로 찍으면 표시가 줄을 먹고 정작 아는 것
#   (`504 Gateway Time-out`)이 묻힌다. 그래서 표시를 걷고 · 빈칸을 접고 · 길이를 문다.
#   갈래 이름(`WebException` · `UnauthorizedAccessException`)이 「망이냐 권한이냐」를 가르므로 앞에 붙인다.
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

# 로그 파일의 끝 줄(빈 줄 빼고 `$Lines` 줄까지)을 들여 찍는다. 비면 비었다고 말한다 — 부르는 자리마다 바로 앞줄이 「뱉은 끝
#   줄」을 약속하므로, 조용히 끝나면 화면이 잘린 것처럼 읽힌다. 「글자 없이 졌다」는 명령이 아예 못 떴다는 단서다.
function Show-Log([string]$LogPath, [int]$Lines = 8) {
  $t = @()
  if (Test-Path -LiteralPath $LogPath) {
    $t = @(Get-Content -LiteralPath $LogPath -Tail $Lines -ErrorAction SilentlyContinue |
           Where-Object { $_ -and $_.Trim() })
  }
  if ($t.Count) { $t | ForEach-Object { Write-Host "      $_" } }
  else { Write-Host '      (한 줄도 안 뱉었다 — 명령이 글자 없이 졌다)' }
}

# 하는 중인 일 한 줄 — `이름 — 동작 … (곁말)`. 동작은 `$BusyVerbs` 의 열쇠이고, 표에 없으면 던진다.
function Say-Busy([string]$What, [string]$Do, [string[]]$Notes = @()) {
  if (-not $BusyVerbs.Contains($Do)) { throw "Say-Busy — 모르는 동작: $Do" }
  $n = @($Notes | Where-Object { $_ })
  $tail = if ($n.Count) { ' (' + ($n -join ' · ') + ')' } else { '' }
  Write-Host ('  {0} — {1} …{2}' -f $What, $BusyVerbs[$Do], $tail)
}

# 받으러 나가기 전에 **무엇을 얼마나** 받는지 댄다 — 느린 링크에서 「멎었나 도나」를 가르는
# 것이 이 한 줄이다. 크기를 안 주는 자리도 있어 그때는 이름만 댄다.
function Say-Get([string]$What, $Asset) {
  $mb = 0
  try { $mb = [double]$Asset.size / 1MB } catch { }
  $size = if ($mb -gt 0) { '{0:N1} MB' -f $mb } else { '' }
  Say-Busy $What 'fetch' @($Asset.name, $size)
}

# ── 걸음의 머리줄과 마침 줄 — 위 `$Steps` 표에서 짓는다 ─────────────────────────────────
# `Get-StepTitle` 은 열쇠를 받아 `[번호/분모] 이름` 을 내고, 표에 없는 열쇠는 던진다. `Enter-Step` 은 빈 줄 하나 뒤에 그 줄을
#   찍고, `Exit-Step` 은 같은 글자로 걸린 초 한 줄을 찍는다(`Write-Elapsed`).
# ⚠ **머리줄의 꼴을 바꾸지 않는다** — 화면 껍데기가 그 줄을 `^\[(\d+)/(\d+)\]\s*(.*)$` 로 읽어 막대를 밀고 셋째 묶음을
#   걸음 이름으로 쓴다. 꼴이 어긋나면 설치는 멀쩡히 돌고 막대만 멈춘다.
function Get-StepTitle([string]$Key) {
  for ($i = 0; $i -lt $Steps.Count; $i++) {
    if ($Steps[$i].Key -ceq $Key) { return ('[{0}/{1}] {2}' -f ($i + 1), $Steps.Count, $Steps[$i].Title) }
  }
  throw "걸음 표에 없는 열쇠 — $Key"
}

function Enter-Step([string]$Key) {
  $script:StepNow = $Key
  Write-Host ''
  Write-Host (Get-StepTitle $Key) -ForegroundColor Cyan
}

function Exit-Step([string]$Key) {
  Write-Elapsed (Get-StepTitle $Key)
  $script:StepNow = ''
}

# ── 칸 경계 — **한 칸 안의 던짐은 그 칸에서 끝난다** (PAISetup #49 ④) ─────────────────────────────────
# 몸통은 전역 `Stop` 아래 돈다. 경계가 없으면 칸 안의 쓰기 하나가 던질 때(사람이 읽기 전용으로 둔 파일 · 다른 프로세스가 공유 없이 쥔
#   파일 · 파일 이름이 선 폴더 자리) 그 뒤 걸음 · 마무리 · 끝 검증이 다 빠지고 몸통이 1 로 죽는다 — 자동 실행만 도는 PC 는 원인이 남는
#   동안 회차마다 같은 자리에서 멎는다. 그래서 흐름의 칸마다 `try` 하나가 그 칸의 몸을 두르고, 받은 던짐을 이 손이 그 칸의 빨간 줄과
#   `$Fails` 한 줄로 낸다. 다음 칸은 그대로 돈다. 칸은 열 걸음(`Enter-Step` 바로 뒤부터 `Exit-Step` 바로 앞까지 — 걸린 초 줄은 진 걸음도
#   찍는다)과 「마무리」 · 「검증」이다. 「준비」는 안 두른다 — 거기서 지면 뒤 칸이 설 바탕이 없다.
# ⚠ **경계는 쓰기마다가 아니라 칸마다다** — 쓰기마다 두르면 새로 붙는 쓰기가 또 빠진다. 제 꼴로 받는 손(`Write-FileSafely` · 칸 안의
#   `catch`)은 그대로 두고, 경계는 거기서 못 받은 것만 받는다. 흐름에 칸을 더하면 경계도 함께 짓는다.
# ⚠ 진 칸의 나머지는 안 돈다 — 그 칸이 반쯤 지은 값을 뒤 칸이 읽는다. 앞 걸음이 지은 값으로 걷거나 심는 걸음은 몸의 첫 문장에서
#   그 걸음이 끝났나 묻고(`Assert-StepsDone`), 멎었으면 통째로 안 한다 — 반쪽 값은 「없다」로 읽혀 걷기가 되고, 빠진 거름 목록은 걸러야
#   할 것을 민다. 장부는 걸음마다 디스크에서 다시 읽고 자리를 쓴 뒤에만 써서(`Read-RunLedger` · `Save-PlantLedger`) 진 걸음의 장부 줄은
#   안 남는다.
# 받는 것 — 받은 오류 기록 · 칸 열쇠(안 주면 지금 걸음 — `Enter-Step` 이 둔다). 줄에 던진 자리(파일:줄)를 단다 — 다음 회차도 같은
#   자리에서 지면 로그가 그 자리를 댄다. ⚠ **이 손은 안 던진다** — 경계의 `catch` 안이라 여기서 던지면 몸통이 그대로 죽는다.
function Write-StepFault($Err, [string]$Key = $script:StepNow) {
  $title = $Key
  try { $title = Get-StepTitle $Key } catch { }
  $at = ''
  try {
    $ii = $Err.InvocationInfo
    if ($ii -and $ii.ScriptName) { $at = '{0}:{1}' -f (Split-Path -Leaf $ii.ScriptName), $ii.ScriptLineNumber }
  } catch { }
  $where = if ($at) { " ($at)" } else { '' }
  Write-Host "  ! $title — 도중에 멎었다: $(Say-Why $Err)$where · 이 칸의 나머지는 안 하고 다음으로 간다" -ForegroundColor Red
  $script:Fails.Add("$title (도중에 멎었다$(if ($at) { " · $at" }))")
  $script:StepFaults[$Key] = $at
}

# 앞 걸음이 끝났나 — 받는 것: 걸음 열쇠들. 그 가운데 도중에 멎은 것이 있으면 던져, 부른 걸음의 경계가 그 걸음을 빨간 줄 · `$Fails` 로
#   끝내게 한다(아무것도 안 하고). 부르는 자리는 앞 걸음이 지은 값(자리 · 심은 값 · 안 밀 이름 목록)으로 걷거나 심는 걸음의 첫 문장이다.
function Assert-StepsDone([string[]]$Keys) {
  foreach ($k in $Keys) {
    if ($script:StepFaults -and $script:StepFaults.Contains($k)) {
      $t = $k
      try { $t = Get-StepTitle $k } catch { }
      throw "앞 걸음 「$t」이 도중에 멎어 이 걸음을 안 했다 — 그 걸음이 반쯤 지은 값으로 걷거나 심지 않는다 (다음 판이 다시 한다)"
    }
  }
}

#endregion 화면

#region 프로세스 — 네이티브 명령을 부르고, 빗장을 쥔 설치기와 작업 스케줄러의 작업을 묻는다

# 「우리 엔진인가」 — 프로세스 하나(Win32_Process)를 받아 `install`(설치 몸통) · `autorun`(자동 실행 몸통) · 빈 글자(우리 것이
#   아니다)를 낸다. **이 자는 하나다** — 몸통의 겹침 찾기(`Find-EngineHolders`)와 자동 실행 몸통의 가드(`Get-OtherEngines` — 가장 높은
#   판의 엔진에서 이 함수를 떼어 들인다)가 다 이것으로 가른다. 따로 적으면 한쪽만 고친 판이 나와 두 가드가 다른 것을 센다.
#   · 돌리는 스크립트는 `-File` 의 인자다(5.1 이 받는 줄임 `-f` · `-fi` · `-fil` 도). `-File` 이 없는 꼴(`-Command "& '…'"`)은 명령줄에서
#     두 이름으로 끝나는 첫 낱말이다. 그 스크립트 이름이 `install.ps1` · `autorun.ps1` 이 아니면 우리 것이 아니다 — 남의 스크립트가
#     우리 설치기 자리를 인자로 받는 판(검사가 `-Installer …\install.ps1` 을 넘긴다)을 안 센다
#   · 같은 이름의 남 스크립트(scoop · 사내 도구의 `install.ps1`)는 그 파일에 우리 표지(`$mark`)가 없는 것으로 가른다 — 빗장을 쥐는
#     판의 몸통과 자동 실행 몸통은 다 그 글자를 든다(빗장 이름 · 이 함수 자신)
#   · **못 가르면 우리 것으로 센다** — 상대 경로(그 프로세스의 작업 폴더를 모른다) · 못 읽는 파일(지워진 옛 판 폴더). 놓치면 겹쳐 돌아
#     반쪽 상태가 남고, 더 센 것은 기다리고 묻는 것으로 끝난다
#   · 로그인 창 자식(`-GhLoginOnly`)은 빗장 앞에서 나가 빗장을 안 쥐므로 우리 엔진으로 안 센다(`Start-GhLoginChild`). 다른 사용자
#     것은 `CommandLine` 이 비어 와 안 골라진다 — 못 본 것을 끝내지 않는다
# ⚠ **이 함수는 다른 함수에 기대지 않는다** — 자동 실행 몸통이 이름으로 떼어 혼자 세운다.
function Get-EngineKind($Proc) {
  $mark = 'PAISetup'
  $cl = [string]$Proc.CommandLine
  if (-not $cl -or $cl -like '*-GhLoginOnly*') { return '' }
  $m = [regex]::Match($cl, '(?i)(?:^|\s)-f(?:i(?:le?)?)?\s+(?:"([^"]+)"|(\S+))')
  if (-not $m.Success) {
    $m = [regex]::Match($cl, '(?i)(?:"([^"]*(?:install|autorun)\.ps1)"|''([^'']*(?:install|autorun)\.ps1)''|([^\s"'']*(?:install|autorun)\.ps1))(?=["''\s]|$)')
  }
  if (-not $m.Success) { return '' }
  $path = @(for ($g = 1; $g -lt $m.Groups.Count; $g++) { if ($m.Groups[$g].Success) { $m.Groups[$g].Value } })[0]
  $leaf = ''
  try { $leaf = [IO.Path]::GetFileName($path) } catch { return '' }
  $kind = if ($leaf -ieq 'install.ps1') { 'install' } elseif ($leaf -ieq 'autorun.ps1') { 'autorun' } else { '' }
  if (-not $kind -or -not [IO.Path]::IsPathRooted($path)) { return $kind }
  $text = $null
  try { $text = [IO.File]::ReadAllText($path) } catch { return $kind }
  if ($text.Contains($mark)) { return $kind }
  return ''
}

# 빗장을 쥔 쪽을 찾는다 — 우리 설치 몸통(`Get-EngineKind` 가 `install`)인 다른 파워셸 프로세스의 목록을 낸다(못 물으면 빈 목록).
#   이름(`powershell.exe`)만으로 고르면 치고 있는 이 창과 화면 껍데기까지 든다. 자동 실행 몸통은 안 센다 — 그것이 이 몸통을 자식으로
#   띄우므로, 세면 자동 실행이 띄운 설치가 제 부모를 겹침으로 읽고 물러난다. `install.ui.ps1` 은 빗장을 안 쥐고 그 이름에 안 걸린다.
function Find-EngineHolders {
  try {
    @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction Stop |
        Where-Object { $_.ProcessId -ne $PID -and (Get-EngineKind $_) -eq 'install' })
  } catch { @() }
}

# 쥔 쪽 한 줄 — 화면과 물음창이 같은 문장을 쓴다
function Format-EngineHolder($H) {
  '  PID {0} · {1} 시작 · {2}분째' -f
    $H.ProcessId, $H.CreationDate.ToString('HH:mm:ss'),
    [int]((Get-Date) - $H.CreationDate).TotalMinutes
}

# 판을 한 줄로 읽는다 — 명령 · 인자를 받아 나가는 글의 첫 줄을 낸다. 못 읽거나 `$ProbeCap` 을 넘기면 빈 글자이고, 넘김은
#   끝 검증의 넘김 목록에 남는다(`Add-ProbeOverflow`). 판은 화면에만 쓰므로 판정은 안 바뀐다. 「도나」가 `yes` 를 낸 뒤 같은
#   명령을 다시 부르는 자리라 울타리를 두른다(#26).
# ⚠ **파이썬은 `--version` 대신 `-c` 로 판을 찍는다**(#32). DRM(Fasoo)이 프로세스 초기화를 가로채는 PC 에서 `--version` 의
#   글자가 자주 사라지고 종료 0 만 남는다 — 까닭은 파이썬 밖이라 재설치로 안 고쳐지고, 인터프리터가 다 선 뒤의 출력은 안
#   잃는다. 종료 코드는 참이라, 종료 코드로 판정하는 다른 python 걸음(`Test-Runs` · `Measure-Runs` · 손들)은 그대로 둔다.
$PyVerCode = 'import sys;print(sys.version.split()[0])'
function Get-Ver([string]$Cmd, [string]$Arg) {
  $log = [IO.Path]::GetTempFileName()
  try {
    $rc = if ($Cmd -eq 'python') { Invoke-LoggedCapped $Cmd @('-c', $PyVerCode) $log $ProbeCap }
          else { Invoke-LoggedCapped $Cmd @($Arg) $log $ProbeCap }
    if ($rc -eq -2) { Add-ProbeOverflow "$Cmd $Arg" $ProbeCap }
    $o = @(Get-Content -LiteralPath $log -Encoding UTF8 -ErrorAction SilentlyContinue | Where-Object { "$_".Trim() })
    # 판을 stderr 로 찍는 도구(poppler 의 pdftoppm)가 있다 — stdout 이 비면 stderr 쪽을 읽는다. 판정은 종료 코드가 들고 여기는 글자만 든다
    if (-not $o.Count) { $o = @(Get-Content -LiteralPath "$log.err" -Encoding UTF8 -ErrorAction SilentlyContinue | Where-Object { "$_".Trim() }) }
  } finally { Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue }
  $v = ("$(@($o) | Select-Object -First 1)").Trim()
  # 판 칸의 꼴을 다른 도구와 맞춘다 — 저쪽은 `Python 3.14.7` 처럼 이름을 들고 온다.
  if ($v -and $Cmd -eq 'python') { $v = "Python $v" }
  return $v
}

# 판 번호를 결과 줄의 괄호에 넣는다 — 비면 `(판을 못 읽었다)` 를 낸다. 빈 괄호 `()` 는 「값만 못 읽었다」와 「판정이
#   틀렸다」를 못 갈라 사람이 고장을 의심한다(#32 · 못 잰 자리는 제 상태를 말한다 — 결정 0141). 판정은 안 바꾼다.
function Format-VerPart([string]$Ver) {
  if ("$Ver".Trim()) { return "($Ver)" }
  return '(판을 못 읽었다)'
}

# 네이티브 명령을 돌리고 모든 스트림을 `$LogPath` 에 잡는다 — 종료코드를 내고, 못 부르면 -1 이다. 실패했을 때 그 파일을
#   펴는 것은 부르는 쪽의 몫이다(성공한 판의 잡소리까지 찍지 않으려고).
function Invoke-Logged([string]$File, [string[]]$CmdArgs, [string]$LogPath) {
  # ⚠ **여기서만 `Stop` 을 푼다.** 네이티브의 stderr 는 `*>` 로 파일에 돌려도 오류 레코드로 올라와 바깥의 `Stop` 이 그
  #   자리에서 던진다 — 경고 한 줄이 설치를 끊는다. 판정은 종료코드가 들고, 글자는 파일에 쌓아 실패했을 때만 편다.
  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try { & $File @CmdArgs *> $LogPath; return $LASTEXITCODE }
  catch { return -1 }
  finally { $ErrorActionPreference = $prev }
}

# 네이티브 명령을 판정만 하려고 돌린다 — stdout 은 줄 배열로 내고 stderr 는 버린다. 종료코드는 `$LASTEXITCODE` 에 남는다
#   (못 부르면 -1). 울타리가 없어 자식을 끝까지 기다린다 — 멎을 수 있는 「도나」는 `Measure-Runs` 로 묻는다.
# ⚠ **맨 `2>$null` 은 이 함수 하나에만 산다.** 버리는 것도 파워셸이 stderr 를 건드리는 자리라 `Stop` 아래서는 그 줄이 오류
#   레코드가 되어 설치를 끊는다(로그인 안 된 gh 의 안내 한 줄로도). 다른 자리는 뽑기 검사(claude-config `scripts/build-dist.sh`)가
#   막는다.
function Get-Quiet([string]$File, [string[]]$CmdArgs) {
  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try { return @(& $File @CmdArgs 2>$null) }
  catch { $global:LASTEXITCODE = -1; return @() }
  finally { $ErrorActionPreference = $prev }
}

# 네이티브 명령을 **그 파일의 꼴대로** 띄울 채비를 짓는다 — `Process.Start` 로 띄우는 두 울타리(`Invoke-ProbeCapped` ·
#   `Invoke-LoggedCapped`)가 이것 하나를 쓴다. 이름이 안 서거나 띄울 파일이 아니면 `$null` 이다.
# ⚠ **윈도우가 프로세스로 만드는 것은 실행 파일뿐이다.** `Get-Command` 가 집은 자리를 그대로 넘기면 npm 이 깐 `.ps1`
#   껍데기(`npm` · `claude` · `codex` · `copilot`)는 띄우기부터 `Win32Exception`(193)으로 지고, 그 판정은 「없다」로 읽혀
#   깔린 것을 다시 깔러 간다. 파워셸 연산자(`&`)는 그 꼴을 알아서 돌리지만 울타리를 두를 손잡이를 안 준다. 그래서 꼴마다
#   그 꼴을 읽는 호스트에 맡긴다(claude-config 결정 0141):
#     `.ps1`        — Windows PowerShell 에 `-NoProfile -ExecutionPolicy Bypass -File` 로
#     `.cmd` `.bat` — `cmd.exe /d /s /c` 로. `/d` 는 사람이 걸어 둔 cmd 의 AutoRun 을 안 태우고, `/s` 는 바깥 따옴표
#                     한 쌍만 걷어 안의 따옴표를 그대로 둔다
#     그 밖          — 그대로
# 인자는 MSVCRT 규칙으로 싼 한 줄이다(`Join-NativeArgs` 가 짓는다) — 세 호스트가 다 그 규칙으로 낱낱을 가른다. 따옴표 안의
#   `%` 와 큰따옴표는 cmd 가 못 지켜 그 글자를 든 인자는 `.cmd` 에 못 넘긴다(지금 부르는 자리에는 없다).
# ⚠ **stdin 은 돌려 받고, 부르는 쪽이 띄운 직후 닫는다**(`$p.StandardInput.Close()`). npm 이 깐 `.ps1` 껍데기는 들어오는 것이
#   있으면(`$MyInvocation.ExpectingInput`) 끝까지 읽고서야 node 를 부른다 — 물려주면 이 설치기의 stdin 이 안 닫히는 파이프인
#   판(다른 프로그램이 부른 판)에서 `npm --version` 이 그 끝을 기다리다 울타리를 넘긴다.
function New-NativeStart([string]$File, [string]$ArgLine) {
  $c = $null
  try { $c = Get-Command $File -ErrorAction Stop | Select-Object -First 1 } catch { return $null }
  if ($c.CommandType -eq 'Alias') { $c = $c.ResolvedCommand }
  if ($c.CommandType -ne 'Application' -and $c.CommandType -ne 'ExternalScript') { return $null }
  $path = $c.Source
  $ext  = [IO.Path]::GetExtension($path).ToLowerInvariant()
  $tail = if ($ArgLine) { ' ' + $ArgLine } else { '' }
  $psi  = New-Object System.Diagnostics.ProcessStartInfo
  if ($ext -eq '.ps1') {
    $psi.FileName  = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $psi.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $path + '"' + $tail
  } elseif ($ext -eq '.cmd' -or $ext -eq '.bat') {
    $psi.FileName  = Join-Path $env:SystemRoot 'System32\cmd.exe'
    $psi.Arguments = '/d /s /c ""' + $path + '"' + $tail + '"'
  } else {
    $psi.FileName  = $path
    $psi.Arguments = $ArgLine
  }
  $psi.UseShellExecute        = $false
  $psi.RedirectStandardInput  = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  return $psi
}

# 인자 낱낱을 한 줄로 싼다 — `ProcessStartInfo.ArgumentList` 가 이 파워셸(5.1 · .NET Framework)에 없어서다. 빈칸 · 따옴표 ·
#   cmd 연산자(`& | < > ^`)가 든 낱과 빈 낱만 MSVCRT 규칙으로 감싼다. 감싸도 MSVCRT 를 따르는 쪽은 같은 낱을 받는다.
function Join-NativeArgs([string[]]$CmdArgs) {
  return (@($CmdArgs) | ForEach-Object {
    if ("$_" -ne '' -and "$_" -notmatch '[\s"&|<>^]') { "$_" }
    else { '"' + (("$_" -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"' }
  }) -join ' '
}

# `Invoke-Logged` 와 같은 일에 시간 울타리(`$CapSec`)를 두른다 — 0 이상이면 그 종료코드 · -1 은 못 불렀다 · -2 는 넘겨서 나무째
#   거뒀다. 글자는 `$LogPath`(stdout)와 `$LogPath.err`(stderr) 둘에 붓는다.
# 칸이 제 몫을 스스로 지킨다 — 갱신을 바깥 명령에 맡기는 칸은 걸리는 시간이 밀린 양에 달려, 한 호출이 부르는 쪽 울타리를
#   혼자 다 먹을 수 있다. 부르는 쪽 울타리는 어느 칸이 먹었나를 모르고 거두면 안 돈 칸까지 잃으므로, 느린 칸 하나만 포기하고
#   뒤 칸이 돌게 한다. 포기해도 되는 칸(갱신)과 안 되는 칸(설치)은 부르는 쪽이 가린다.
# ⚠ **`Start-Process -PassThru` 로 띄우지 않는다** — 그것이 주는 Process 는 손잡이를 안 쥐어, 잡기 전에 자식이 끝나면
#   `ExitCode` 가 빈 값이다(#139). `Process.Start` 는 띄우는 순간의 손잡이를 쥔다.
# 두 스트림을 파이프로 받아 `CopyToAsync` 가 파일에 붓는다(파워셸 스레드 없이 돈다) — 늘 읽으므로 파이프 버퍼가 차서 자식이
#   멈추지 않는다. `cmd /c … >` 로 감싸 파일로 돌리지 않는다 — 그러면 `Kill()` 이 자식 대신 cmd 만 죽인다.
# 나무째 거둔다 — `code` · `npm` 류는 제 자식을 띄우고 껍데기(`.cmd` · `.ps1`)는 그 호스트가 부모로 서서, 부모만 죽이면
#   손자가 남아 돈다. `Kill($true)` 는 이 파워셸(5.1 · .NET Framework)에 없어 `Stop-ProbeTree` 가 든다.
function Invoke-LoggedCapped([string]$File, [string[]]$CmdArgs, [string]$LogPath, [int]$CapSec) {
  $psi = New-NativeStart $File (Join-NativeArgs $CmdArgs)
  if (-not $psi) { return -1 }
  # 자식이 끝난 뒤 파이프의 꼬리를 다 붓기까지 기다리는 한도 — 그 끝은 파이프를 쥔 손자까지 다 나가야 온다.
  # 거둔 갈래는 안 기다린다 — 꼬리를 읽을 자리가 없고, 살아남은 손자가 울타리를 늘린다.
  $drainMs = 5000
  $sink = @()
  try {
    $sink = @([IO.File]::Open($LogPath, 'Create', 'Write', 'ReadWrite'),
              [IO.File]::Open("$LogPath.err", 'Create', 'Write', 'ReadWrite'))
    $p = [Diagnostics.Process]::Start($psi)
    $p.StandardInput.Close()
    $pump = @($p.StandardOutput.BaseStream.CopyToAsync($sink[0]),
              $p.StandardError.BaseStream.CopyToAsync($sink[1]))
    if ($p.WaitForExit($CapSec * 1000)) {
      try { $null = [Threading.Tasks.Task]::WaitAll($pump, $drainMs) } catch { }
      return $p.ExitCode
    }
    try { Stop-ProbeTree $p } catch { }
    try { if (-not $p.HasExited) { $p.Kill() } } catch { }
    return -2
  } catch { return -1 }
  finally { foreach ($s in $sink) { try { $s.Dispose() } catch { } } }
}

# 울타리를 넘긴 프로브를 나무째 거둔다 — 두 울타리 손(`Invoke-LoggedCapped` · `Invoke-ProbeCapped`)이 쓴다. 거둠의 성공은
#   기다리지 않는다. 프로세스 목록을 못 읽으면 던진다 — 부르는 쪽이 뿌리만 끈다.
# ⚠ **자손은 부모보다 늦게 선 것만 잇는다** — 부모 PID 만 따라가면(`taskkill /T`) 그 PID 를 앞서 쥐었다 죽은 프로세스의 고아
#   (먼저 선 남)까지 끈다(claude-config 결정 0142).
# 뿌리를 먼저 쥔 손잡이(`$Proc`)로 끈다 — PID 를 남이 물려받았을 틈이 없고, 자식부터 끄면 그 끝을 기다리던 뿌리가 새 자식을
#   띄운다. 자손은 끄기 직전에 손잡이를 다시 쥐고 시작 시각이 목록의 것과 같을 때만 끈다 — 그 사이 PID 가 남에게 갔을 수 있다.
function Stop-ProbeTree([Diagnostics.Process]$Proc) {
  # 프로세스 목록 묻기에도 한도를 둔다 — 멎은 WMI 하나가 거둠을 세우면 울타리가 제 몫을 못 한다. 넘기면 던지고 부르는 쪽이 뿌리만 끈다
  $all = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, CreationDate -OperationTimeoutSec 10 -ErrorAction Stop)
  $kids = @{}
  foreach ($x in $all) {
    $pp = [int]$x.ParentProcessId
    if (-not $kids.ContainsKey($pp)) { $kids[$pp] = New-Object System.Collections.ArrayList }
    [void]$kids[$pp].Add($x)
  }
  $tree = New-Object System.Collections.ArrayList
  $todo = New-Object System.Collections.Queue
  $root = @($all | Where-Object { [int]$_.ProcessId -eq $Proc.Id }) | Select-Object -First 1
  if ($root) { $todo.Enqueue($root) }
  while ($todo.Count) {
    $n = $todo.Dequeue()
    if (-not $kids.ContainsKey([int]$n.ProcessId)) { continue }
    foreach ($c in $kids[[int]$n.ProcessId]) {
      if ($c.ProcessId -ne $n.ProcessId -and $c.CreationDate -ge $n.CreationDate -and -not $tree.Contains($c)) { [void]$tree.Add($c); $todo.Enqueue($c) }
    }
  }
  try { if (-not $Proc.HasExited) { $Proc.Kill() } } catch { }
  foreach ($c in $tree) {
    $h = $null
    try {
      $h = Get-Process -Id ([int]$c.ProcessId) -ErrorAction Stop
      if ([Math]::Abs(($h.StartTime - $c.CreationDate).TotalMilliseconds) -lt 1) { $h.Kill() }
    } catch { } finally { if ($h) { $h.Dispose() } }
  }
}

# 「도나」를 묻는 한 번에 주는 한도 — `--version` 류의 즉답에 20초면 넉넉하다. 느린 기계를 재는 값이 아니라 멈춤을 가르는
#   값이다: 짧게 잡으면 멀쩡한 자리가 「못 쟀다」로 남아 설치가 성공으로 안 끝나고, 길게 잡아도 잃는 것은 멎은 한 자리의
#   그 초뿐이라 의심스러우면 길게 잡는다.
$ProbeCap = 20
# 할 일을 가르려고 「무엇이 깔렸나 · 무엇을 올릴까」를 묻는 바깥 명령의 한도 — 넘기면 「못 쟀다」다(결정 0145). 위와 같이 멈춤을 가르는 값이라
#   의심스러우면 길게 둔다.
$WingetListCap = 120   # winget 의 첫 부름은 원본을 새로 받느라 수십 초를 쓰고, 막힌 소스를 붙든 사내 회선에서는 더 쓴다
$NpmViewCap    = 60    # 레지스트리에 판 하나를 묻는 GET 이라 평소 1초 안팎이다 — 느린 프록시를 넉넉히 덮는다
$ExtListCap    = 60    # `code` 가 node 를 띄워 깔린 확장을 읽는다 — VDI 에서 몇 초씩 걸리는 자리라 `--version` 울타리보다 길게 둔다
$ClaudePluginCap = 60  # `claude plugin list` · `plugin marketplace list` — node 로 선 CLI 가 플러그인 기록을 읽는다. 첫 실행에 제 짐을 푸는 CLI 가 `--version` 에 20초 가까이 쓴 PC 가 있어(PAISetup #30) 넉넉히 둔다
# 끝 검증이 묻는 바깥 명령의 한도 — 넘기면 그 칸이 「못 쟀다」다. 위와 같이 멈춤을 가르는 값이라 의심스러우면 길게 둔다.
$ToolHomesCheckCap = 120   # 손(`tool-homes.py check`)이 도구 홈 넷의 규범 · 룰 · 에이전트 · 스킬을 표와 견준다 — 파일을 읽기만 하는데, 느린 디스크와 보안 소프트가 낀 VDI 를 넉넉히 덮는다
# 상태를 바꾸는 바깥 명령의 한도 — 넘기면 거두고 「못 했다」로 간다. 무인 판이 사람을 기다리는 창 앞에서 영영 서지 않게 한다.
$VcRedistCap   = 900   # VC++ 재배포 패키지를 받고(17.8 MB) 까는 한 번 — 사내 회선의 받기와 승인 창을 누를 사람의 몫까지 넉넉히 덮는다

# 울타리를 넘긴 프로브 — **넘김 하나가 한 줄이다.** 같은 명령이 여러 자리에서 넘기면 그 수만큼 서고, 줄마다 명령(`Probe`) ·
#   부른 자리(`Site` — 이 파일의 행) · 한도(`Cap`)를 든다. 끝 검증이 이것을 명령마다 「몇 자리 · 몇 번」으로 센다.
# ⚠ **두 목록 다 `List[hashtable]` 이다** — `List[object]` 는 `@(…)` 로 싸는 순간 이 파워셸(5.1)이 「Argument types do not
#   match」로 던진다.
$script:ProbeTimedOut = New-Object System.Collections.Generic.List[hashtable]
# 넘김 때문에 하지도 건너뛰지도 않은 걸음(`Add-UnmeasuredStep`) — 끝 검증이 「안 한 걸음」 `[?]` 로 찍는다.
$script:UnmeasuredSteps = New-Object System.Collections.Generic.List[hashtable]
# `Measure-Runs` 가 `unmeasured` 를 낸 물음(「명령 인자」 글자)마다 그 까닭 — 「``명령`` 이 …」 뒤에 이어 읽히는 꼴(`Format-ProbeWhy`).
#   못 잰 줄을 찍는 두 자리(`Add-UnmeasuredStep` · 끝 검증의 `[?]` 칸)가 `Get-ProbeWhy` 로 읽는다.
$script:ProbeWhy = @{}

# 「그 명령이 도나」를 세 값으로 잰다 — 명령 · 인자 · 부른 행(`$Site`, 없으면 이 함수를 부른 행)을 받아 `yes`(0 으로 끝났다) ·
#   `no`(그 이름이 이 창에 없다) · `unmeasured`(이름은 서는데 울타리를 넘겼거나 · 못 띄웠거나 · 0 아닌 값으로 끝났다)를 낸다.
#   넘김은 `$script:ProbeTimedOut` 에, 못 잰 까닭은 `$script:ProbeWhy` 에 남는다. 설치기의 「도나」는 다 이 자를 거친다.
# `$ProbeCap` 울타리를 두른다 — 보안 소프트가 낀 PC 에서 `--version` 하나가 안 돌아오면 울타리 없는 부름(`Get-Quiet`)은 그
#   걸음에서 설치를 영영 세운다. 멈추는 까닭은 우리 밖이라 쫓지 않고, 멈춰도 설치가 끝나게 한다(#26).
# ⚠ **「없다」는 이름이 없을 때만이다 — 선 이름이 진 것과 넘김은 「못 쟀다」다**(결정 0141 · claude-config 결정 0151). 그것을
#   「없다」로 읽으면 깔린 것 위에 `winget install` 을 건다(PAISetup #37). 부재에 기대 상태를 바꾸는 자리(깔기 · 올리기나 걷기를
#   건너뛰기)는 참 · 거짓이 아니라 이 세 값으로 묻고, `unmeasured` 면 하지도 건너뛰지도 않고 `Add-UnmeasuredStep` 으로 남긴다.
# 예외 하나 — 윈도우의 앱 실행 별칭 자리(`…\Microsoft\WindowsApps\`)에서 0 아닌 값으로 끝났거나 못 띄운 것은 「없다」다. 윈도우가
#   거기 두는 스토어행 `python` 껍데기는 진짜가 없을 때 0 아닌 값을 내라고 있는 것이고, 낡아 못 띄우는 별칭도 같다 — 못
#   쟀다로 읽으면 그 PC 에 파이썬이 영영 안 깔린다. 넘김은 거기서도 못 쟀다다. 스토어로 깐 진짜 파이썬도 그 자리에 서므로,
#   그것이 지면 winget 판을 곁에 하나 더 깐다(결정 0151).
function Measure-Runs([string]$Cmd, [string]$Arg, [int]$Site = 0) {
  if (-not $Site) { $Site = $MyInvocation.ScriptLineNumber }
  $c = Get-Command $Cmd -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $c) { return 'no' }
  $probe = "$Cmd $Arg"
  $rc = Invoke-ProbeCapped $Cmd $Arg $ProbeCap
  if ($rc -eq 0) { return 'yes' }
  if ($rc -eq -2) { $script:ProbeTimedOut.Add(@{ Probe = $probe; Site = $Site; Cap = $ProbeCap }) }
  elseif ("$($c.Source)" -like '*\Microsoft\WindowsApps\*') { return 'no' }
  $script:ProbeWhy[$probe] = Format-ProbeWhy $rc $ProbeCap
  return 'unmeasured'
}

# `Measure-Runs` 가 그 물음에 `unmeasured` 를 낸 까닭 — 남은 것이 없으면 울타리 넘김 글이다.
function Get-ProbeWhy([string]$Probe) {
  if ($script:ProbeWhy -and $script:ProbeWhy.ContainsKey($Probe)) { return $script:ProbeWhy[$Probe] }
  return "${ProbeCap}초 안에 안 끝나"
}

# 「그 명령이 도나」를 참 · 거짓으로 — `Measure-Runs` 가 `yes` 일 때만 참이다. 스무 자리 넘게 `if` 의 조건으로 쓴다.
# ⚠ **거짓은 「없다」가 아니다** — 넘김도, 선 이름이 진 것도 거짓이다. 거짓에 기대 깔거나 일을 빼는 자리는 이 자가 아니라
#   `Measure-Runs` 로 묻는다(결정 0141 · 0151). 넘긴 것은 그 자리와 함께 `$script:ProbeTimedOut` 에 남아 끝 검증이 센다.
function Test-Runs([string]$Cmd, [string]$Arg) {
  return ((Measure-Runs $Cmd $Arg $MyInvocation.ScriptLineNumber) -eq 'yes')
}

# 부재에 기대 상태를 바꾸는 자리가 `unmeasured` 를 받으면 부른다 — 그 자리에서 노란 줄을 찍고 끝 검증의 「안 한 걸음」에
#   남긴다. `$Step` 은 안 한 걸음의 이름, `$Probe` 는 못 잰 물음, `$Held` 는 무엇을 안 했나, `$Why` 는 그 물음이 어떻게 졌나다
#   (「``$Probe`` 이 …」 뒤에 이어 읽히는 꼴 — 비우면 `Measure-Runs` 가 그 물음에 남긴 까닭(`Get-ProbeWhy`)이다). 하나라도
#   남으면 설치는 성공이 아니다(끝 검증). `$Redo` 는 그 프로그램이 깨졌을 때 사람이 손으로 다시 까는 명령이다 — 아는 자리(winget
#   Id 를 든 행)만 넘기고, 끝 검증이 그 걸음 아래 찍는다.
#   넘김이 아닌 못 잼(winget 의 종료 값 · 던진 오류 · 도구가 없음)은 부르는 쪽이 제 까닭을 `$Why` 로 넘긴다 — 넘김 글로 찍으면
#   사람이 멎은 것을 찾아 헤맨다(결정 0145).
function Add-UnmeasuredStep([string]$Step, [string]$Probe, [string]$Held, [string]$Why = '', [string]$Redo = '') {
  if (-not $Why) { $Why = Get-ProbeWhy $Probe }
  $script:UnmeasuredSteps.Add(@{ Step = $Step; Probe = $Probe; Held = $Held; Why = $Why; Redo = $Redo })
  Write-Host "  ! $Step — 못 쟀다: ``$Probe`` 이 $Why $Held (없는 것이 아니다)" -ForegroundColor Yellow
}

# 울타리 손(`Invoke-LoggedCapped`)이 -2 를 낸 자리가 부른다 — 넘김 한 줄(명령 · 부른 행 · 한도)을 `$script:ProbeTimedOut` 에 남겨
#   끝 검증이 센다. `Measure-Runs` 밖에서 울타리를 두른 자리(할 일을 가르는 바깥 명령)의 몫이다.
function Add-ProbeOverflow([string]$Probe, [int]$Cap) {
  $script:ProbeTimedOut.Add(@{ Probe = $Probe; Site = $MyInvocation.ScriptLineNumber; Cap = $Cap })
}

# 울타리 손이 낸 값을 「``명령`` 이 …」 뒤에 이어 읽히는 까닭으로 — -2 넘김 · -1 못 띄움 · 그 밖은 종료 값.
function Format-ProbeWhy([int]$Rc, [int]$Cap) {
  if ($Rc -eq -2) { return "${Cap}초 안에 안 끝나" }
  if ($Rc -eq -1) { return '띄우지 못해' }
  return ('{0} (0x{0:X8}) 로 끝나' -f $Rc)
}

# `Measure-Runs` 가 쓰는 울타리 — 종료코드만 쥐고 글자는 버린다. 내는 값은 `Invoke-LoggedCapped` 와 같다(0 이상 · -1 · -2).
#   거두는 길도 같지만 판정만 재는 자리라 임시 파일을 안 연다.
# ⚠ **파워셸 연산자(`&`)로 부르지 않는다** — `&` 로 부른 자식에는 울타리를 두를 손잡이가 없다. `Process.Start` 가 쥐어 주는
#   손잡이가 `WaitForExit(ms)` 와 거둠의 전제이고, 파일의 꼴은 `New-NativeStart` 가 가른다.
# 거둠의 성공을 기다리지 않는다 — `taskkill /T /F` 도 관리자 `Stop-Process -Force` 도 못 끄는 자식이 있다. 걸어 보고 바로 -2 를
#   내고, 손잡이를 `Dispose` 로 놓아 이 프로세스가 남은 자식에 매이지 않는다.
function Invoke-ProbeCapped([string]$File, [string]$Arg, [int]$CapSec) {
  $psi = New-NativeStart $File $Arg
  if (-not $psi) { return -1 }
  $p = $null
  try {
    $p = [Diagnostics.Process]::Start($psi)
    $p.StandardInput.Close()
    # ⚠ **두 스트림을 읽어 버린다** — 안 읽으면 파이프 버퍼가 차서 자식이 멈추고, 울타리가 우리 손으로 만든 멈춤을 잰다.
    #   비동기로 걸어 두고 결과는 안 쓴다.
    $null = $p.StandardOutput.ReadToEndAsync()
    $null = $p.StandardError.ReadToEndAsync()
    if ($p.WaitForExit($CapSec * 1000)) { return $p.ExitCode }
    try { Stop-ProbeTree $p } catch { }
    try { if (-not $p.HasExited) { $p.Kill() } } catch { }
    return -2
  } catch { return -1 }
  finally { if ($p) { try { $p.Dispose() } catch { } } }
}

# 그 이름의 예약 작업이 있나 — 못 물으면 `$false` 다(못 묻는 것과 없는 것은 다른 명제지만 부르는 자리가 둘로 할 일이 같다).
# ⚠ **`Get-ScheduledTask` 를 맨손으로 안 부른다** — 스케줄러 모듈이 없는 판의 「그런 명령이 없다」는 `-ErrorAction
#   SilentlyContinue` 로 안 막혀, `Stop` 아래서 자동 실행 한 칸 때문에 설치가 통째로 죽는다. `try` 가 받는다.
function Test-ScheduledTaskExists([string]$Name) {
  try { return [bool](Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue) }
  catch { return $false }
}

# 자동 실행 작업이 있나 — `Test-ScheduledTaskExists` 를 그대로 부른다.
function Test-AutoRunTask([string]$Name) {
  return (Test-ScheduledTaskExists $Name)
}

# 깃발 없는 판의 자동 실행 — 짐의 `#autorun` 지시로 켬(`$true`) · 걷음(`$false` — 지시가 `no`) · 그대로 둠(`$null`)을 낸다. 「자동
#   실행을 켜나」 칸이 `-AutoRun` · `-NoAutoRun` 이 없을 때 이 답을 쓰고, `-Describe` 가 같은 답을 `autorun|on·off` 로 내 설치 창의 칸이
#   그대로 뜬다(그대로 둠은 작업이 있나로) — 창이 규칙을 따로 지으면 지시가 `no` 인 판에서 둘이 갈린다(PAISetup #46 ③).
# ⚠ **`yes` 여도 사람이 끈 PC 는 다시 안 켠다** — 짐이 늘 `yes` 를 실어 지시만으로는 끈 것을 못 기억한다. 끈 기록(`$AutoRunOffRecord`)이
#   있고 작업이 없으면 그대로 둠이다. 작업이 서 있으면 기록보다 작업이 이긴다. 지시가 없어도 그대로 둠이다.
function Get-AutoRunDefault([string]$Directive) {
  if ($Directive -eq 'yes') {
    if (-not (Test-Path -LiteralPath $AutoRunOffRecord) -or (Test-AutoRunTask $AutoRunTaskName) -or (Test-AutoRunTask $AutoRunNightTaskName)) { return $true }
    return $null
  }
  if ($Directive -eq 'no') { return $false }
  return $null
}

#endregion 프로세스

#region 파일 — 값 파일을 읽고, 백업 자리와 설정 저장소를 받는 자리를 잡고, 나른 파일 수를 센다

# `#이름 = 값` 꼴 지시를 읽는다 — 파일 · 이름을 받아 처음 맞는 줄의 값을 내고, 파일이나 줄이 없으면 `$null` 이다. 값(`이름=값`)과
#   달리 지시는 어디로 갈지를 든다 — 몸통은 주소를 모르고 파일이 든다.
function Read-Directive([string]$Path, [string]$Key) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
    if ($line -match "^\s*#\s*$([regex]::Escape($Key))\s*=\s*(.+?)\s*$") { return $Matches[1] }
  }
  return $null
}

# 값 파일을 이름 → 값 표로 읽는다(없으면 빈 표) — `이름=값` 한 줄씩, `#` 로 시작하는 줄은 주석, 값에 따옴표를 안 씌운다
#   (secrets.env 와 같은 꼴).
# ⚠ **줄끝 CR 을 턴다**(`Trim`) — CRLF 로 받은 값 끝의 CR 이 그대로 심기면 아무 데서도 안 먹히는 키가 된다.
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

# 회차를 넘기는 사람의 기록을 읽는다 — 설치 창(`-Describe`) · 콘솔 · 자동 실행이 다 이 손을 지난다(「회차를 넘기는 기록의 자리」).
# 받는 것 — 기록 파일 · 옛 꼴의 선택 파일(`autorun.args`) · 옛 꼴의 얼린 값 파일 · 끈 자동 실행 기록(안 주면 안 본다). 내는 것 — 이름 →
#   값 표. 이름은 `$ChoiceKeys` 에 `autorun`(끈 기록이 있으면 `off`)을 더한 것이고, 값은 적힌 글자 그대로다(빈 선택은 `$ChoiceNone`).
#   기록에 없는 이름은 표에도 없다 — 부르는 쪽이 기본값으로 간다.
# 새 기록에 값이 하나라도 서 있으면 그것만 읽는다. 없거나 값이 하나도 없으면(빈 파일 · `pick=` 만 든 파일) 없는 것으로 보고 옛 꼴을
#   읽는다 — 그것도 없으면 빈 표다:
#   · 선택 파일 — 그 판이 고른 것을 다 적은 파일이다(스위치가 없으면 켬 · `-PersonalFor` 가 없으면 없음 · `-WithPersonalConfig` 는
#     Claude). `-Pick` 은 하나도 안 고른 판에서 안 적혀, 그 줄이 없으면 제품을 모른다
#   · 얼린 값 파일 — `#config-repo` 줄(없으면 없음)과 주소 줄만 읽는다. 나머지는 그때 판의 짐이 든 줄이라 안 읽는다
function Read-ChoiceRecord([string]$Path, [string]$LegacyArgs, [string]$LegacyEnv, [string]$OffRecord) {
  $rec = @{}
  if (Test-Path -LiteralPath $Path) {
    $m = Read-EnvFile $Path
    foreach ($k in $m.Keys) { if ($m[$k]) { $rec[$k] = $m[$k] } }
  }
  if (-not $rec.Count) {
    if (Test-Path -LiteralPath $LegacyArgs) {
      $al = @(Get-Content -LiteralPath $LegacyArgs -Encoding UTF8 | ForEach-Object { $_.Trim() } | Where-Object { $_ })
      $pi = [array]::IndexOf($al, '-Pick')
      if ($pi -ge 0 -and $pi + 1 -lt $al.Count -and -not $al[$pi + 1].StartsWith('-')) { $rec['pick'] = $al[$pi + 1] }
      $rec['vscode']   = if ($al -contains '-NoVsCode')   { 'no' } else { 'yes' }
      $rec['devtools'] = if ($al -contains '-NoDevTools') { 'no' } else { 'yes' }
      $fi = [array]::IndexOf($al, '-PersonalFor')
      $rec['personal'] = if ($fi -ge 0 -and $fi + 1 -lt $al.Count -and -not $al[$fi + 1].StartsWith('-')) { $al[$fi + 1] }
                         elseif ($al -contains '-WithPersonalConfig') { 'claude' } else { $ChoiceNone }
    }
    if (Test-Path -LiteralPath $LegacyEnv) {
      $repo = Read-Directive $LegacyEnv 'config-repo'
      $rec['config-repo'] = if ($repo) { $repo } else { $ChoiceNone }
      $url = (Read-EnvFile $LegacyEnv)['ANTHROPIC_BASE_URL']
      if ($url) { $rec['gateway-url'] = $url }
    }
  }
  if ($OffRecord -and (Test-Path -LiteralPath $OffRecord)) { $rec['autorun'] = 'off' }
  return $rec
}

# 이번 회차의 값 줄 — 「키와 값」 걸음이 심을 이름 → 값 표를 짓는다.
# 받는 것 — 짐의 값 파일 · 넘겨받은 값 파일 · 사람이 친 게이트웨이 주소(없으면 빈 값). 내는 것 — 이름 → 값 표.
#   짐의 줄이 다 서고, 사람의 이름 둘에만 사람의 값을 얹는다:
#   · 키(`ANTHROPIC_AUTH_TOKEN`) — 넘겨받은 파일이 들면 그것이 이긴다. 짐 파일에 키를 적어 둔 PC(여러 대를 세우는 사람)도 창에 새로
#     친 키 · `-EnvFile` 로 준 키가 이번 뜻이다
#   · 주소(`ANTHROPIC_BASE_URL`) — 짐이 안 들 때만 사람이 친 값. 짐이 들면 짐의 사실이다
#   넘겨받은 파일의 나머지 줄은 안 읽는다 — 옛 자동 실행이 넘기는 얼린 사본은 지난 판 짐의 줄이라, 읽으면 새 판의 값이 안 서고 새 판이
#   뺀 이름이 되살아난다(PAISetup #45 ①). 그 사본은 키 줄을 안 든다.
function Read-RunValues([string]$Kit, [string]$Passed, [string]$TypedUrl) {
  $map = Read-EnvFile $Kit
  if ($Passed -and $Passed -ne $Kit) {
    $key = (Read-EnvFile $Passed)['ANTHROPIC_AUTH_TOKEN']
    if ($key) { $map['ANTHROPIC_AUTH_TOKEN'] = $key }
  }
  if ($TypedUrl -and -not $map['ANTHROPIC_BASE_URL']) { $map['ANTHROPIC_BASE_URL'] = $TypedUrl }
  return $map
}

# 맡기기 모델 표(짐의 스킬 `agent-envelope` 폴더의 `models.conf`)를 러너의 자리 값으로 옮긴다 — 표의 꼴과 칸마다 가는 자리는
#   그 표의 머리가 든다. 모델 이름은 표에만 산다.
# 받는 것 — 표의 경로. 내는 것 — @{ Agy = @{ inside = [ordered]@{<이름> = <값>}; outside = … }; Codex = (같은 꼴); Why = <못 읽은
#   까닭 · 읽었으면 $null> }. 못 읽으면 Agy · Codex 가 빈 채로 온다.
# ⚠ 한 줄이라도 꼴에 안 맞으면 표 전체를 버린다 — 틀린 줄만 빼고 옮기면 남은 줄이 다른 무게의 모델을 그 자리 값에 심는다.
function Read-ModelTable([string]$Path) {
  $sites   = @('inside', 'outside')
  $tools   = @('claude', 'codex', 'agy')
  $weights = @('deep', 'errand', 'fallback')
  $none    = '-'
  $empty   = @{ Agy = @{ inside = [ordered]@{}; outside = [ordered]@{} }; Codex = @{ inside = [ordered]@{}; outside = [ordered]@{} }; Why = $null }
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { $empty.Why = "표가 없다: $Path"; return $empty }
  try { $lines = [IO.File]::ReadAllLines($Path, [Text.Encoding]::UTF8) }
  catch { $empty.Why = "표를 못 읽었다: $($_.Exception.Message)"; return $empty }
  $cell = @{}
  $fall = @{ inside = @(); outside = @() }
  $rows = @{ inside = 0; outside = 0 }
  $why  = $null
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $t = $lines[$i].Trim()
    if (-not $t -or $t.StartsWith('#')) { continue }
    $at = "$($i + 1) 줄"
    if ($t -notmatch '^(\S+)\s+(\S+)\s+(\S+)\s+(\S.*)$') { $why = "$at — 칸이 넷이 아니다"; break }
    $site = $Matches[1]; $tool = $Matches[2]; $weight = $Matches[3]; $model = $Matches[4].Trim()
    if ($sites -cnotcontains $site)     { $why = "$at — 모르는 자리 $site"; break }
    if ($tools -cnotcontains $tool)     { $why = "$at — 모르는 도구 $tool"; break }
    if ($weights -cnotcontains $weight) { $why = "$at — 모르는 무게 $weight"; break }
    if ($model.Contains(';'))           { $why = "$at — 모델 이름에 ; 가 든다"; break }
    $rows[$site]++
    if ($weight -ceq 'fallback') {
      if ($tool -cne 'agy')    { $why = "$at — 넘길 차례는 agy 만 든다"; break }
      if ($model -ceq $none)   { $why = "$at — 넘길 차례에 - 가 든다"; break }
      $fall[$site] += $model
      continue
    }
    $key = "$site $tool $weight"
    if ($cell.ContainsKey($key)) { $why = "$at — $key 가 두 줄이다"; break }
    $cell[$key] = $model
  }
  # 줄이 하나도 없는 자리는 잘린 표다 — 어느 자리든 claude 줄은 선다
  if (-not $why) { foreach ($s in $sites) { if (-not $rows[$s]) { $why = "자리 $s 의 줄이 없다"; break } } }
  $out = @{ Agy = @{}; Codex = @{}; Why = $null }
  foreach ($s in $sites) {
    if ($why) { break }
    $delegate = $cell["$s agy deep"]; $errand = $cell["$s agy errand"]
    $agy = [ordered]@{}
    if ($errand -and ($errand -cne $none))     { $agy['AGY_DEFAULT_MODEL']  = $errand }
    if ($delegate -and ($delegate -cne $none)) { $agy['AGY_MODEL_DELEGATE'] = $delegate }
    if ($fall[$s].Count)                       { $agy['AGY_FALLBACK_MODELS'] = $fall[$s] -join ';' }
    $out.Agy[$s] = $agy
    $delegate = $cell["$s codex deep"]; $errand = $cell["$s codex errand"]
    $codex = [ordered]@{}
    if ($errand -and ($errand -cne $none))     { $codex['CC_BG_CODEX_MODEL']          = $errand }
    if ($delegate -and ($delegate -cne $none)) { $codex['CC_BG_CODEX_MODEL_DELEGATE'] = $delegate }
    $out.Codex[$s] = $codex
  }
  if ($why) { $empty.Why = $why; return $empty }
  return $out
}

# 아직 없는 자리를 낸다 — `$Path` 가 있으면 `$Path-2` · `$Path-3` … 가운데 처음 빈 것. 백업 자리는 늘 새로 잡는다 — 같은 초에
#   두 번 돌거나 앞 백업에 같은 이름이 있으면, 이미 있는 폴더로 옮기기가 그 안으로 들어가 앞 백업과 겹친다.
function Get-FreePath([string]$Path) {
  $p = $Path; $i = 2
  while (Test-Path -LiteralPath $p) { $p = "$Path-$i"; $i++ }
  return $p
}

# 바이트를 글로 — `[IO.File]::ReadAllText` 와 같은 자다(UTF-8 · 앞의 BOM 을 읽고 뺀다). 쓰는 손(`Write-FileSafely`)에 넘길 원래 바이트와
#   읽은 글이 한 번 읽은 것에서 나오게, 부르는 쪽은 바이트를 한 번 읽고 이것으로 글을 얻는다.
function Read-TextOf([byte[]]$Bytes) {
  $sr = New-Object IO.StreamReader((New-Object IO.MemoryStream(, $Bytes)), [Text.Encoding]::UTF8, $true)
  try { return $sr.ReadToEnd() } finally { $sr.Dispose() }
}

# 설정 · 장부 · 기록 파일을 갈아 끼워 쓴다 — 설치기가 사람과 같이 쓰는 파일을 쓰는 손은 이것 하나다(PAISetup #44 ⑱).
# 받는 것 — 자리 · 새 바이트 · 원래 바이트(부르는 쪽이 읽어 둔 것 · 그때 파일이 없었으면 $null) · 끼우기 전에 곁 파일을 재는 손(`$Check` —
#   곁 파일 자리를 받아 참이면 끼운다 · 안 주면 안 잰다).
# 내는 것 — @{ Did; Why }. Did — same(원래와 같아 안 썼다) · written · raced(재는 사이 다른 프로그램이 고쳤거나 지었다 — 안 썼다) ·
#   overrun(썼는데 되읽으니 다른 글이다 — 그 사이 다른 프로그램이 썼다 · 그 글을 둔다) · refused(`$Check` 가 거절했다 — 안 썼다) ·
#   linked(그 자리가 링크다 — 안 썼다) · left(못 썼다 — Why 가 까닭과 원래 파일을 되돌렸나를 든다). 화면 줄은 부르는 쪽이 든다 — 못 지운
#   임시 사본 줄만 여기서 낸다. linked 는 노란 줄이다 — 사람이 둔 꼴이라 실패가 아니고, 그 자리는 그 사람이 손으로 맞춘다.
# · 곁 파일(`<자리>.paisetup-<무작위>.new`)에 다 쓴 뒤 `File.Replace` 로 끼우고 원래 파일은 곁 사본(`….old`)으로 받는다 — 쓰다 멎어도
#   반쪽 파일이 제자리에 안 남는다. 원래 파일이 없던 판은 그 자리가 아직 비었을 때만 옮겨 놓는다
# · 끼울 때마다 원래 바이트와 다시 견준다 — 재는 사이 · 기다리는 사이 다른 프로그램(그 도구 · 사람의 편집기)이 고친 글을 말없이 덮지
#   않는다. 잠깐 붙잡힌 파일(백신 · 색인 · 동기화)은 세 번까지 다시 끼운다
# · 끼우다 지면 곁 사본을 제자리로 옮기고, 못 옮기면 쥐고 있던 원래 바이트를 쓴다(곁 사본은 둔다). 곁 사본은 제자리의 파일이 우리가
#   아는 글(원래 글 · 새 글)일 때만 걷는다 — 아니면 그것이 원래 글의 하나뿐인 사본일 수 있다
# · 링크는 안 건드린다(linked) — 재분석 지점(심볼릭 링크 · 정션)은 갈아 끼우면 링크가 끊기고, 하드 링크는 갈아 끼우면 다른 이름이 옛 글을 든 채
#   갈라진다(어느 쪽이든 말없이). `Set-CodexSandboxKey` 와 같은 자다 — 링크 자리는 그 사람이 손으로 맞춘다. 하드 링크는 파워셸이 그 파일에
#   붙이는 `LinkType`(이름이 둘 이상이면 HardLink)으로 가린다
# ⚠ **곁 사본 자리를 꼭 준다** — 안 주면 끼우기가 중간에 질 때(ERROR_UNABLE_TO_MOVE_REPLACEMENT) 원래 파일이 사라진다.
# ⚠ **원래 바이트는 메서드의 반환을 바로 받아 넘긴다** — `$x = if (…) { [IO.File]::ReadAllBytes(…) }` 처럼 파이프를 지나면 바이트 목록이
#   풀려 빈 파일은 $null(「없던 파일」)이 되고 나머지는 글자 목록이 된다.
function Write-FileSafely([string]$Path, [byte[]]$New, $Old, [scriptblock]$Check) {
  $oldB64 = if ($null -ne $Old) { [Convert]::ToBase64String([byte[]]$Old) } else { $null }
  $newB64 = [Convert]::ToBase64String($New)
  if ($null -ne $oldB64 -and $oldB64 -ceq $newB64) { return @{ Did = 'same' } }
  $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
  if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return @{ Did = 'linked'; Why = '그 자리가 링크(재분석 지점)다 — 갈아 끼우면 링크가 끊겨 안 썼다' } }
  if ($item -and -not $item.PSIsContainer -and [string]$item.LinkType -ceq 'HardLink') { return @{ Did = 'linked'; Why = '그 파일이 하드 링크다 — 갈아 끼우면 다른 이름과 갈라져 안 썼다' } }
  if ($item -and $item.PSIsContainer) { return @{ Did = 'left'; Why = '그 자리가 폴더다' } }
  $tag = "$Path.paisetup-$([guid]::NewGuid().ToString('N').Substring(0, 8))"
  $side = "$tag.new"; $bak = "$tag.old"
  $out = @{ Did = 'written' }
  try {
    New-Item -ItemType Directory -Path (Split-Path $Path -Parent) -Force | Out-Null
    [IO.File]::WriteAllBytes($side, $New)
    if ($Check -and -not (& $Check $side)) { return @{ Did = 'refused'; Why = '쓸 글을 재니 그 뜻이 아니다' } }
    for ($i = 1; ; $i++) {
      $now = $null
      if (Test-Path -LiteralPath $Path -PathType Leaf) { $now = [Convert]::ToBase64String([IO.File]::ReadAllBytes($Path)) }
      if ($now -cne $oldB64) {
        return @{ Did = 'raced'; Why = $(if ($null -eq $oldB64) { '쓰려는 사이 다른 프로그램이 그 자리에 파일을 지었다' } else { '재는 사이 다른 프로그램이 그 파일을 고쳤다' }) }
      }
      try {
        if ($null -eq $oldB64) { [IO.File]::Move($side, $Path) } else { [IO.File]::Replace($side, $Path, $bak) }
        break
      } catch [IO.IOException] {
        if ($i -ge 3 -or ($null -ne $oldB64 -and -not (Test-Path -LiteralPath $Path))) { throw }
        Start-Sleep -Milliseconds 300
      }
    }
    # 끼운 뒤에는 원래 글로 덮어쓰지 않는다 — 되읽은 글이 다르면 그 사이 다른 프로그램이 쓴 것이라 그 글을 둔다
    $back = try { [Convert]::ToBase64String([IO.File]::ReadAllBytes($Path)) } catch { $null }
    if ($null -ne $back -and $back -cne $newB64) { $out = @{ Did = 'overrun'; Why = '쓴 뒤 되읽으니 다른 글이다 — 그 사이 다른 프로그램이 썼다' } }
  } catch {
    $why = "못 썼다 ($($_.Exception.Message))"
    if ($null -ne $oldB64 -and -not (Test-Path -LiteralPath $Path)) {
      $restored = $false
      if (Test-Path -LiteralPath $bak) { try { Move-Item -LiteralPath $bak -Destination $Path; $restored = $true } catch { } }
      if (-not $restored) { try { [IO.File]::WriteAllBytes($Path, [byte[]]$Old); $restored = $true } catch { } }
      $why += $(if ($restored) { ' — 끼우다 진 자리를 원래 파일로 되돌렸다' } else { " — 원래 파일을 못 되돌렸다$(if (Test-Path -LiteralPath $bak) { " · 원래 글은 $bak 에 있다" })" })
    }
    return @{ Did = 'left'; Why = $why }
  } finally {
    $cur = try { [Convert]::ToBase64String([IO.File]::ReadAllBytes($Path)) } catch { $null }
    $known = $null -ne $cur -and ($cur -ceq $newB64 -or $cur -ceq $oldB64)
    foreach ($f in @($side) + @(if ($known) { $bak })) {
      for ($j = 0; $j -lt 3 -and (Test-Path -LiteralPath $f); $j++) {
        if ($j) { Start-Sleep -Milliseconds 300 }
        Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue
      }
      if (Test-Path -LiteralPath $f) { Write-Host "  ! 임시 사본이 남았다 — 그 파일의 글을 그대로 든 사본이라 손으로 지운다: $f" -ForegroundColor Yellow }
    }
  }
  return $out
}

# 홈 설정 씨앗을 읽는다 — 짐에 실린 `vdi-home-settings.json`(claude-config 의 그 파일을 뽑은 것). 받는 것: 자리. 내는 것 — @{ Obj = <맨 위 표 ·
#   못 읽었으면 $null>; Why = <못 읽은 까닭> }. 「Claude 홈 설정」이 그 파일이 없을 때 이것으로 짓고, 기능 스위치(`$Features`)가 그 `env` 를 읽는다.
function Read-HomeSeed([string]$Path) {
  if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) { return @{ Obj = $null; Why = "씨앗이 없다 ($Path)" } }
  $o = $null
  try { $o = [IO.File]::ReadAllText($Path) | ConvertFrom-Json } catch { return @{ Obj = $null; Why = "씨앗을 JSON 으로 못 읽었다 ($Path)" } }
  if ($o -isnot [System.Management.Automation.PSCustomObject]) { return @{ Obj = $null; Why = "씨앗의 맨 위가 표가 아니다 ($Path)" } }
  return @{ Obj = $o; Why = '' }
}

# 씨앗의 `env` 를 기능 스위치 표(이름 → 글)로 낸다 — 못 읽은 씨앗은 $null 이다(빈 표가 아니다 — 빈 표면 장부가 우리 스위치를 다 걷는다).
#   글이 아닌 값은 그 JSON 글로 옮긴다(env 의 값은 글이다).
function Get-SeedSwitches($Seed) {
  if (-not $Seed -or -not $Seed.Obj) { return $null }
  $out = [ordered]@{}
  $e = $Seed.Obj.PSObject.Properties['env']
  if ($e -and $e.Value -is [System.Management.Automation.PSCustomObject]) {
    foreach ($p in $e.Value.PSObject.Properties) { $out[$p.Name] = $(if ($p.Value -is [string]) { $p.Value } else { [string]($p.Value | ConvertTo-Json -Compress) }) }
  }
  return $out
}

# 설정 저장소를 받는 자리 — 주소의 끝 이름을 `$configRepoRoot` 아래에 붙여 낸다. 「설정 저장소」 걸음이 clone 하는 자리이자, 씨앗
#   칸이 그 저장소가 홈으로 미는 자리를 찾는 자리다 — 자리를 짓는 자를 한 벌로 둔다(「준비」의 「설정 저장소의 주소와 자리」).
function Get-ConfigRepoDir([string]$Url) {
  return (Join-Path $configRepoRoot ([IO.Path]::GetFileNameWithoutExtension($Url)))
}

# JSON 을 두 칸 들여쓰기 · `"키": 값` 꼴로 쓴다 — 씨앗 저장소 설정과 같은 꼴이다. ASCII 밖의 글자(한글 등)는 그대로 두고 따옴표 · 역슬래시 ·
#   제어 문자만 이스케이프한다. 윈도 PowerShell 5.1 의 `ConvertTo-Json` 은 ASCII 밖의 글자와 `<>&'` 를 \uXXXX 로 바꾸고 들여쓰기를 제 꼴로
#   흩어, 사람이 쓴 설정의 글자가 안 읽히고 바뀐 줄이 는다. 받는 값은 `ConvertFrom-Json` 이 낸 꼴(표 · 목록 · 글 · 수 · 참거짓 · 빈 값)이다.
#   ⚠ `ConvertFrom-Json` 은 `"\/Date(…)\/"` 꼴의 글을 날짜로 바꾸고, 날짜는 아래 값 갈래가 따옴표 없이 써 JSON 이 깨진다 — 부르는 쪽이
#   쓰기 전에 엄격하게 되읽는다(`Merge-RepoSettings`).
function ConvertTo-PlainJson($Value, [string]$Pad = '') {
  if ($null -eq $Value) { return 'null' }
  if ($Value -is [bool]) { if ($Value) { return 'true' } else { return 'false' } }
  if ($Value -is [string]) {
    $sb = New-Object Text.StringBuilder
    [void]$sb.Append('"')
    foreach ($ch in $Value.ToCharArray()) {
      $code = [int]$ch
      if ($ch -eq '"') { [void]$sb.Append('\"') }
      elseif ($ch -eq '\') { [void]$sb.Append('\\') }
      elseif ($code -eq 10) { [void]$sb.Append('\n') }
      elseif ($code -eq 13) { [void]$sb.Append('\r') }
      elseif ($code -eq 9) { [void]$sb.Append('\t') }
      elseif ($code -lt 32) { [void]$sb.Append(('\u{0:x4}' -f $code)) }
      else { [void]$sb.Append($ch) }
    }
    [void]$sb.Append('"')
    return $sb.ToString()
  }
  if ($Value -is [ValueType]) { return [Convert]::ToString($Value, [Globalization.CultureInfo]::InvariantCulture) }
  $in = $Pad + '  '
  if ($Value -is [System.Collections.IList]) {
    if (-not $Value.Count) { return '[]' }
    $items = foreach ($e in $Value) { $in + (ConvertTo-PlainJson $e $in) }
    return "[`n" + (@($items) -join ",`n") + "`n$Pad]"
  }
  $props = @($Value.PSObject.Properties)
  if (-not $props.Count) { return '{}' }
  $items = foreach ($p in $props) { $in + (ConvertTo-PlainJson $p.Name) + ': ' + (ConvertTo-PlainJson $p.Value $in) }
  return "{`n" + (@($items) -join ",`n") + "`n$Pad}"
}

# 저장소 설정(`.claude/settings.json`)에서 우리 항목만 홈 씨앗의 지금 판으로 맞춘다(claude-config 결정 0129 「저장소 설정」). 그 파일은 사람이 많이
#   고친다 — 우리 항목 밖의 키 · 값 · 훅은 안 건드린다:
#   · 엄격한 JSON 만 고친다 — Claude Code 는 엄격하지 않은 파일(작은따옴표 · 앞의 0 · 꼬리 쉼표 · 주석)을 통째로 안 읽는데, PowerShell 5.1 의
#     `ConvertFrom-Json` 은 그것을 받아들인다. 고쳐 쓰면 그동안 안 돌던 사람의 설정(권한 등)이 살아난다. 쓸 글도 엄격하게 되읽는다 —
#     `ConvertTo-PlainJson` 이 옮기지 못하는 값(날짜로 읽힌 글)이 있으면 안 쓴다
#   · 키는 대소문자를 가린다(Claude Code 와 같다). 우리가 읽거나 더하는 키(`hooks` · `env` · 씨앗의 이벤트)와 대소문자만 다른 키가 있으면
#     안 고친다 — PowerShell 의 표는 그 둘을 한 이름으로 다뤄 엉뚱한 키에 쓴다. 한 표에 대소문자만 다른 두 키가 함께 서면(`hooks` 와 `Hooks`)
#     PowerShell 5.1 의 `ConvertFrom-Json` 이 던져 못 고친다 — 그 말이 두 키 이름을 댄다. `env` 안의 키만은 대소문자를 안 가린다 — 윈도의
#     환경 변수 이름이 그렇다(사람의 `pythonutf8` 은 같은 변수다)
#   · 우리 항목 — 훅 명령 객체의 명령이 따옴표를 벗기면 `$CLAUDE_PROJECT_DIR/.claude/hooks/<이름>` 이고, 그 이름이 홈 씨앗이 싣는 훅
#     (`<씨앗>/.claude/hooks/` 의 파일)이거나 · 저장소에 그 파일이 없거나(걷은 우리 훅의 남은 등록 — Dropped 에 댄다) · 저장소의
#     그 파일이 우리 표지를 든 것. 그 파일이 있고 표지가 없으면 그 사람의 훅이라 말없이 둔다. 이름에 경로에 못 쓰는 글자가
#     들면 파일일 수 없어 우리 것이 아니다
#   · 우리 명령 객체를 제 묶음에서 걷고 — 우리 것을 걷어 비게 된 묶음과 이벤트만 걷는다(사람의 훅이 같은 묶음에 있을 수 있다) — 씨앗의
#     등록을 그 이벤트 끝에 더한다. 그래서 씨앗의 등록이 하나씩만 선다
#   · `env` — 씨앗이 든 키가 없을 때만 더한다. 사람이 정한 값은 안 덮는다(결정 0127 의 규칙). `env` 가 없으면 맨 앞에 둔다(씨앗의 차례)
#   · `permissions` 와 그 밖의 키는 안 본다 — 우리 것과 사람 것을 가를 길이 없다
# 쓸 글은 위 꼴(`ConvertTo-PlainJson`)로 다시 짓고, 원래 파일의 줄끝 · BOM 을 따른다. 뜻이 안 바뀌면(맞춘 뒤의 글과 맞추기 전 글을 같은 꼴로
#   지어 견준다) 안 쓴다.
# 내는 것 — @{ Ok; Changed; Bytes; Why; Fix; Dropped }. 못 고치면 Ok 가 거짓이고 안 쓴다 — Why · Fix 가 그 까닭과 길이다
function Merge-RepoSettings([string]$Path, [string]$SeedPath, [string]$Repo, [string]$SeedHooks) {
  $res = @{ Ok = $false; Changed = $false; Bytes = $null; Why = ''; Fix = ''; Dropped = @() }
  $jsonFix = '그 파일을 엄격한 JSON 으로 바로잡은 뒤(편집기가 문법 오류 자리를 짚는다) 설치를 다시 누른다 — 그 사이 그 파일은 그대로다'
  # 엄격한 JSON 인데 꼴이 다른 것 — 편집기는 짚을 오류가 없다
  $shapeFix = '그 자리를 Claude Code 설정의 꼴(맨 위 · hooks · env 는 표, hooks 의 이벤트는 목록)로 바로잡은 뒤 설치를 다시 누른다 — 그 사이 그 파일은 그대로다'
  $refuse = { param([string]$why, [string]$fix)
    $res.Why = "저장소 설정(.claude/settings.json)을 $why 안 고쳤다"
    $res.Fix = if ($fix) { $fix } else { $jsonFix }
    $res }
  # 엄격한 JSON 인가 — 참 · 거짓, 잴 자가 없으면 빈 값. 윈도 런타임의 `JsonValue` 가 엄격하다(PowerShell 5.1 에서 작은따옴표 · 앞의
  #   0 · 꼬리 쉼표 · 주석을 거절하고, 범위 밖의 수에는 던진다 — 던지면 거짓이다)
  $strict = { param([string]$t)
    $jv = $null
    try { $jv = [Windows.Data.Json.JsonValue, Windows.Data.Json, ContentType = WindowsRuntime] } catch { }
    if (-not $jv) { return $null }
    try { $v = $null; return [bool]$jv::TryParse($t, [ref]$v) } catch { return $false } }
  $propOf = { param($o, [string]$k) @($o.PSObject.Properties | Where-Object { $_.Name -ceq $k }) | Select-Object -First 1 }
  $twinOf = { param($o, [string]$k) @($o.PSObject.Properties | Where-Object { $_.Name -ieq $k -and $_.Name -cne $k } | ForEach-Object { $_.Name }) | Select-Object -First 1 }
  $caseFix = { param([string]$k) "그 키를 $k 로 바로잡거나 지운 뒤 설치를 다시 누른다 — Claude Code 는 대소문자가 다른 키를 안 읽는다" }
  $pso = [System.Management.Automation.PSCustomObject]
  $bytes = [IO.File]::ReadAllBytes($Path)
  $bom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
  $skip = if ($bom) { 3 } else { 0 }
  $raw = (New-Object Text.UTF8Encoding($false)).GetString($bytes, $skip, $bytes.Length - $skip)
  $nl = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
  $isStrict = & $strict $raw
  if ($null -eq $isStrict) { return (& $refuse '이 PowerShell 에서 엄격한 JSON 으로 잴 자(Windows.Data.Json)가 없어' '설치 창(Windows PowerShell 5.1)으로 설치를 다시 누른다 — 같으면 이 줄을 그대로 보낸다') }
  if (-not $isStrict) { return (& $refuse '엄격한 JSON 으로 못 읽어(Claude Code 도 그 파일을 통째로 안 읽는다)') }
  $obj = $null
  # 엄격한 JSON 을 PowerShell 5.1 이 못 읽는 자리는 한 표에 대소문자만 다른 두 키다 — 그 말에 두 키 이름이 든다
  try { $obj = $raw | ConvertFrom-Json -ErrorAction Stop }
  catch {
    $msg = ([string]$_.Exception.Message -replace '\s+', ' ').Trim()
    return (& $refuse "PowerShell 5.1 이 못 읽어($msg)" '그 말이 댄 두 키 가운데 하나를 지우거나 이름을 바로잡은 뒤 설치를 다시 누른다(Claude Code 는 대소문자가 다른 두 키를 따로 읽는다) — 다른 말이면 이 줄을 그대로 보낸다')
  }
  if ($obj -isnot $pso) { return (& $refuse '맨 위가 표가 아니라' $shapeFix) }
  foreach ($k in @('hooks', 'env')) { $tw = & $twinOf $obj $k; if ($tw) { return (& $refuse "키 $tw 가 우리 키 $k 와 대소문자만 달라" (& $caseFix $k)) } }
  $hooksProp = & $propOf $obj 'hooks'
  if ($hooksProp -and $hooksProp.Value -isnot $pso) { return (& $refuse 'hooks 가 표가 아니라' $shapeFix) }
  $seedObj = [IO.File]::ReadAllText($SeedPath) | ConvertFrom-Json
  if ($hooksProp) {
    foreach ($sev in @($seedObj.hooks.PSObject.Properties)) { $tw = & $twinOf $hooksProp.Value $sev.Name; if ($tw) { return (& $refuse "hooks.$tw 가 이벤트 $($sev.Name) 와 대소문자만 달라" (& $caseFix $sev.Name)) } }
    foreach ($ev in @($hooksProp.Value.PSObject.Properties)) { if ($ev.Value -isnot [System.Collections.IList]) { return (& $refuse "hooks.$($ev.Name) 가 목록이 아니라" $shapeFix) } }
  }
  $envProp = & $propOf $obj 'env'
  if ($envProp -and $envProp.Value -isnot $pso) { return (& $refuse 'env 가 표가 아니라' $shapeFix) }
  $before = ConvertTo-PlainJson $obj
  $shipped = @(Get-ChildItem -LiteralPath $SeedHooks -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
  # 우리 꼴의 명령이면 훅 이름, 아니면 빈 글
  $nameOf = { param($cmd)
    $c = ([string]$cmd).Trim()
    if ($c.Length -ge 2 -and (($c[0] -eq '"' -and $c[-1] -eq '"') -or ($c[0] -eq "'" -and $c[-1] -eq "'"))) { $c = $c.Substring(1, $c.Length - 2) }
    if ($c -match '^\$CLAUDE_PROJECT_DIR/\.claude/hooks/([^/\\\s"'']+)$' -and $Matches[1].IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -lt 0) { $Matches[1] } else { '' } }
  # 걷기 — 이벤트마다 우리 명령 객체를 걷고, 우리 것을 걷어 비게 된 묶음은 뺀다. 우리 것을 걷은 이벤트를 적어 둔다(비면 뒤에서 뺀다)
  $touched = @()
  if ($hooksProp) {
    foreach ($ev in @($hooksProp.Value.PSObject.Properties)) {
      $keep = @(); $removed = $false
      foreach ($grp in @($ev.Value)) {
        $hp = if ($grp -is $pso) { & $propOf $grp 'hooks' } else { $null }
        if ($hp -and $hp.Value -is [System.Collections.IList]) {
          $rest = @()
          foreach ($h in @($hp.Value)) {
            $cp = if ($h -is $pso) { & $propOf $h 'command' } else { $null }
            $n = if ($cp) { & $nameOf $cp.Value } else { '' }
            if ($n) {
              $file = Join-Path $Repo ".claude\hooks\$n"
              $gone = -not (Test-Path -LiteralPath $file -PathType Leaf)
              if (($shipped -contains $n) -or $gone -or (Test-OurMark $file ".claude/hooks/$n")) {
                $removed = $true
                if ($gone -and $shipped -notcontains $n -and $res.Dropped -notcontains $n) { $res.Dropped += $n }
                continue
              }
            }
            $rest += , $h
          }
          if ($rest.Count -lt @($hp.Value).Count) {
            if (-not $rest.Count) { continue }
            $hp.Value = $rest
          }
        }
        $keep += , $grp
      }
      $ev.Value = $keep
      if ($removed) { $touched += $ev.Name }
    }
  }
  # 더하기 — 씨앗의 등록을 그 이벤트 끝에(없으면 이벤트를 hooks 끝에) 더한다
  if ($seedObj.hooks) {
    if (-not $hooksProp) { $obj | Add-Member -NotePropertyName 'hooks' -NotePropertyValue ([pscustomobject]@{}); $hooksProp = & $propOf $obj 'hooks' }
    foreach ($sev in @($seedObj.hooks.PSObject.Properties)) {
      $cur = & $propOf $hooksProp.Value $sev.Name
      if ($cur) { $cur.Value = @(@($cur.Value) + @($sev.Value)) }
      else { $hooksProp.Value | Add-Member -NotePropertyName $sev.Name -NotePropertyValue @($sev.Value) }
    }
  }
  # 우리 것을 걷어 빈 이벤트는 뺀다 — 원래 빈 이벤트는 사람 것이라 둔다
  foreach ($name in $touched) {
    $cur = & $propOf $hooksProp.Value $name
    if ($cur -and -not @($cur.Value).Count) { $hooksProp.Value.PSObject.Properties.Remove($name) }
  }
  # env — 씨앗의 키가 없을 때만 더한다
  if ($seedObj.env) {
    if (-not $envProp) {
      $front = [pscustomobject]@{}
      $front | Add-Member -NotePropertyName 'env' -NotePropertyValue ([pscustomobject]@{})
      foreach ($p in @($obj.PSObject.Properties)) { $front | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value }
      $obj = $front; $envProp = & $propOf $obj 'env'
    }
    foreach ($sp in @($seedObj.env.PSObject.Properties)) {
      if (-not $envProp.Value.PSObject.Properties[$sp.Name]) { $envProp.Value | Add-Member -NotePropertyName $sp.Name -NotePropertyValue $sp.Value }
    }
  }
  $after = ConvertTo-PlainJson $obj
  if ($after -ceq $before) { $res.Ok = $true; return $res }
  if (-not (& $strict $after)) { return (& $refuse '맞춘 글이 엄격한 JSON 으로 안 읽혀(그 파일의 어느 값을 설치기가 그대로 못 옮긴다)' '설치를 다시 누른다 — 같으면 이 줄을 그대로 보낸다') }
  $res.Ok = $true
  $res.Changed = $true
  $body = (New-Object Text.UTF8Encoding($false)).GetBytes((($after + "`n") -replace "`n", $nl))
  $res.Bytes = if ($bom) { [byte[]](@([byte]0xEF, [byte]0xBB, [byte]0xBF) + @($body)) } else { $body }
  return $res
}

# 우리 파일인가 — 머리 12 줄 안의 주석 줄(`#` · `//`)이 우리 표지 문구로 그 파일의 원본 좌표를 대나(claude-config 결정 0129 「우리 표지」).
#   문구는 둘이다: 「진본은|원본은 claude-config/<저장소 상대 경로> 다」 · 「(진본: claude-config/<저장소 상대 경로>)」. 배포가 뿌린 우리
#   파일의 머리말이 이 꼴이다. 문구로 좁힌다 — 주석이나 코드 줄에서 그 경로를 부르기만 하는 사람의 감싸개는 우리 것이 아니다.
#   못 읽으면 거짓이다.
function Test-OurMark([string]$Path, [string]$Rel) {
  $at = [regex]::Escape('claude-config/' + ($Rel -replace '\\', '/'))
  $mark = '^\s*(#|//).*(?:(?:진본|원본)은 ' + $at + ' 다|\(진본: ' + $at + '\))'
  try {
    foreach ($ln in @(Get-Content -LiteralPath $Path -TotalCount 12 -Encoding UTF8 -ErrorAction Stop)) {
      if ($ln -match $mark) { return $true }
    }
  } catch { }
  return $false
}

# 받은 저장소의 세션 훅을 가른다 — 우리 것인가 · 저장소의 꼴 · 이 설치기와 같은 세대인가. 「설정 저장소」 걸음이 넘기기 전에, 작업 루트
#   훑기가 갈기 전에 묻는다(claude-config 결정 0129). 이 설치기의 세대는 홈의 규범 · 룰 · 에이전트 · 훅 놓기를 손(`tool-homes.py`)에 맡긴다.
#   그보다 옛 세대의 우리 훅 · 몸통 · 배포는 그것을 제 사본으로 붓는다 — 넘기면 「도구별 홈」 걸음이 손으로 놓은 것이 덮이고 끝 검증의 손 줄이
#   빨개진다.
# 가르는 글자는 그 `--install` 이 실제로 돌릴 것의 글이다:
#   · 우리 것인가 — 훅의 머리말 주석이 우리 표지 문구를 대나(`Test-OurMark`). 아니면 그 사람의 훅이라 가르지 않는다 — 붙인 저장소의 훅은
#     누구 것이든 부른다(결정 0115)
#   · 꼴(안 쓸 자리를 가른다) — 몸통(`session-start-body.sh`)을 곁에 들거나 뿌리에 `deploy.ps1` · `deploy.repofiles.conf` 를 든 저장소는
#     설정 저장소 꼴이다(claude-config 클론 · 씨앗을 떠 만든 저장소 · 그 밖에 제 배포를 든 저장소). 둘은 배포가 형제에 미는 묶음에 없어
#     형제에는 안 선다. 그 밖은 형제 꼴이고, 거기 든 우리 파일은 배포가 형제에 미는 묶음(`deploy.repofiles.conf`)이다
#   · 세대 — 훅이 몸통으로 넘기는 문지기인가(그 이름이 없으면 그 파일이 곧 몸통인 옛 세대다) · 곁의 몸통이 손을 부르나 · 제 설정 저장소면
#     그 `deploy.ps1` 이 손을 부르나. 제 설정 저장소는 찾는 자(`claude-config-path.sh`)의 지문 — 뿌리의 `deploy.ps1` 과 `memory/` — 이고, 몸통이
#     `deploy.ps1` 을 부르는 것은 그때뿐이라 지문이 없는 저장소의 `deploy.ps1`(팀의 배포 스크립트 등)은 세대를 안 가른다. 손의 이름이 없으면
#     옛 세대다
# 내는 것 — 훅이 없으면 `$null`. 있으면 @{ Repo; Ours; Shape(sibling | config); Current; Why; Fix; Refreshed; Overwrote; Edited; Kept;
#   SettingsNote; Dropped; Blocked }:
#   Fix — 손으로 고치는 길 한 줄. 설정 저장소 꼴만 여기서 짓고, 형제 꼴은 갈기(`Invoke-HookRefresh`)나 작업 루트 훑기가 그 결과대로 짓는다
#   그 밖은 비어 나온다. 갈기와 넘길 자리를 고르는 줄이 채운다 — 쓴 파일 · 그 가운데 덮은 파일 · 우리 항목만 고친 파일 · 우리 표지가 없어 둔
#     파일 · 저장소 설정을 못 고친 까닭 · 저장소 설정에서 걷은 파일 없는 우리 꼴 등록 · 설정 저장소 때문에 못 넘기는 까닭
function Get-SessionHookGen([string]$Repo) {
  $hooks = Join-Path $Repo '.claude\hooks'
  $hook = Join-Path $hooks 'session-start.sh'
  if (-not (Test-Path -LiteralPath $hook -PathType Leaf)) { return $null }
  $r = @{ Repo = $Repo; Ours = $false; Shape = 'sibling'; Current = $true; Why = ''; Fix = ''; Refreshed = @(); Overwrote = @(); Edited = @(); Kept = @()
          SettingsNote = ''; Dropped = @(); Blocked = '' }
  # 훅을 못 읽으면 표지도 못 읽어 그 사람의 훅으로 본다(계약대로 부른다)
  if (-not (Test-OurMark $hook '.claude/hooks/session-start.sh')) { return $r }
  $r.Ours = $true
  # 못 읽은 몸통 · 배포는 빈 글로 본다 — 손을 부르는지 모르니 안 넘긴다
  $read = { param([string]$p) try { [IO.File]::ReadAllText($p) } catch { '' } }
  $body = Join-Path $hooks 'session-start-body.sh'
  $deploy = Join-Path $Repo 'deploy.ps1'
  $hasBody = Test-Path -LiteralPath $body -PathType Leaf
  $hasDeploy = Test-Path -LiteralPath $deploy -PathType Leaf
  $ownRoot = $hasDeploy -and (Test-Path -LiteralPath (Join-Path $Repo 'memory') -PathType Container)
  if ($hasBody -or $hasDeploy -or (Test-Path -LiteralPath (Join-Path $Repo 'deploy.repofiles.conf') -PathType Leaf)) { $r.Shape = 'config' }
  if (-not (& $read $hook).Contains('session-start-body.sh')) {
    $r.Current = $false
    $r.Why = '몸통을 제 안에 든 옛 판 훅이다 — 넘기면 「도구별 홈」이 손으로 놓은 규범 · 룰을 제 사본으로 덮는다'
  } elseif ($hasBody -and -not (& $read $body).Contains('tool-homes.py')) {
    $r.Current = $false
    $r.Why = '곁의 몸통(session-start-body.sh)이 손(tool-homes.py)을 안 부르는 옛 판이다 — 넘기면 「도구별 홈」이 손으로 놓은 것을 제 손으로 덮는다'
  } elseif ($ownRoot -and -not (& $read $deploy).Contains('tool-homes.py')) {
    $r.Current = $false
    $r.Why = '이 저장소의 deploy.ps1 이 손(tool-homes.py)을 안 부르는 옛 판이다 — 넘기면 몸통이 그것을 불러 「도구별 홈」이 손으로 놓은 것을 덮는다'
  }
  if ($r.Current) { return $r }
  if ($r.Shape -eq 'config') {
    $r.Fix = '설정 저장소 꼴이라 설치기가 안 고친다 — 원본에서 받은 저장소면 당기고(git pull), 씨앗으로 만든 저장소면 ~/.claude/seeds/config-repo/ 의 지금 판으로 손수 올린다 · 그 훅을 안 쓰면 그 파일과 .claude/settings.json 의 SessionStart 줄을 함께 걷는다'
  }
  return $r
}

# 저장소 안의 자리까지 가는 길에 저장소 밖으로 이어진 갈래(정션 · 링크 폴더)가 있나 — 있으면 그 갈래의 자리를 내고, 없으면 빈 글.
#   갈래의 끝을 못 풀어도 그 자리를 낸다(안 쓴다). 그 갈래를 지나 쓰면 새 파일이 저장소 밖에 앉는다.
function Get-OutsideHop([string]$Root, [string]$Path) {
  $parts = @($Path.Substring($Root.Length).TrimStart('\') -split '\\')
  $cur = $Root
  for ($i = 0; $i -lt $parts.Count - 1; $i++) {
    $cur = Join-Path $cur $parts[$i]
    $it = Get-Item -LiteralPath $cur -Force -ErrorAction SilentlyContinue
    if (-not $it) { break }
    if (-not ($it.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }
    $tg = [string](@($it.Target) | Select-Object -First 1)
    if (-not $tg) { return $cur }
    if (-not [IO.Path]::IsPathRooted($tg)) { $tg = Join-Path (Split-Path $cur -Parent) $tg }
    $full = [IO.Path]::GetFullPath($tg).TrimEnd('\')
    if (-not ($full -ieq $Root -or $full.StartsWith("$Root\", [StringComparison]::OrdinalIgnoreCase))) { return $cur }
  }
  return ''
}

# 형제 꼴 저장소에 든 우리 파일을 홈 씨앗의 지금 판으로 간다(claude-config 결정 0129). 묶음은 씨앗의 `deploy.repofiles.conf` — 배포가
#   형제에 미는 것과 같은 목록이고, 씨앗과 바이트가 다른 것만 덮는다. 묶음 밖의 파일은 안 건드린다 — 배포도 덮어쓰기만 한다.
# git 은 읽기만 한다 — 커밋 · 스테이징 · 되돌리기를 안 한다. 바뀐 파일은 작업 나무에 남고 그 사람이 보고 커밋한다.
# 안 쓰는 자리 — 아래 하나라도 걸리면 아무것도 안 쓴다(읽다 진 것도 같다). 까닭(Why)과 그 까닭에 맞는 고치는 길(Fix)을 함께 낸다:
#   · git 저장소가 아닌 폴더 — 고치는 길은 비어 나온다(설치가 가리킬 길이 없다)
#   · 저장소 밖으로 이어진 갈래를 지나는 자리(`Get-OutsideHop`) — 그 갈래를 걷는다
#   ⚠ 덮을 파일의 작업 나무가 git 인덱스의 것과 다르다 — `git hash-object --path` 가 그 자리의 걸러짐(줄끝 등)을 입혀 지은 값이 인덱스의
#     값과 같아야 덮는다. 상태(`status`)로 묻지 않는다 — 건너뛰기 · 안 바뀐 셈 표시(skip-worktree · assume-unchanged)가 서면 바뀐 파일도
#     깨끗하게 나와, 덮은 손질을 되돌릴 길이 없다. 고치는 길은 셋으로 갈린다: 커밋 안 한 손질(커밋 · stash) · 표시 아래 손질(표시를 걷고
#     커밋 · stash — 표시가 서 있으면 둘 다 그 손질을 못 본다) · git 밖의 파일(지우거나 옮긴다 — 무시된 파일에 「커밋」은 안 맞는다)
#   · 표시 아래 손질은 덮을 파일만이 아니라 저장소에 있는 우리 파일 전부(저장소 설정 포함 · 표지가 없어 둔 파일은 빼고)에서 본다 — 그런
#     손질이 든 저장소는 하나도 안 간다. 저장소 설정의 합치기를 거절해 그 파일을 안 쓰는 판도 같다
# 있는 파일은 머리말이 우리 표지를 댈 때만 덮고(`Test-OurMark`), 아니면 그 사람의 것이라 두고 Kept 에 댄다. 사람이 고쳐 커밋한 우리
#   파일도 덮는다(결정 0129 — 사용자가 받아들인 위험). 저장소 설정(`.claude/settings.json`)은 덮지 않고 우리 항목만 고친다(`Merge-RepoSettings`) —
#   뜻이 안 바뀌면 안 쓰고, JSON 으로 못 읽으면 그 파일만 두고 SettingsNote 에 까닭과 길을 댄다(다른 파일은 간다 — 위 표시 아래 손질이
#   없을 때).
# 훅(`.claude/hooks/session-start.sh`)은 맨 뒤에 쓴다 — 쓰다 지면 옛 훅이 남아 다음 실행이 다시 옛 세대로 읽고 이어 간다. 먼저 쓴 것은
#   씨앗과 같아 그때 건너뛴다.
# 내는 것 — @{ Ok; Why; Fix; Files; Overwrote; Edited; Kept; SettingsNote; Dropped }. Files 는 쓴 파일(저장소 상대 경로) · Overwrote 는 그
#   가운데 있던 파일을 덮은 것 · Edited 는 우리 항목만 고친 것(저장소 설정) · Dropped 는 저장소 설정에서 걷은 파일 없는 우리 꼴 등록 — 쓰다 졌으면
#   그때까지 쓴 것
function Update-OurRepoFiles([string]$Repo, [string]$Seed) {
  $out = @{ Ok = $false; Why = ''; Fix = ''; Files = @(); Overwrote = @(); Edited = @(); Kept = @(); SettingsNote = ''; Dropped = @() }
  $hookRel = '.claude/hooks/session-start.sh'
  $again = '설치를 다시 누른다'
  try {
    $conf = Join-Path $Seed 'deploy.repofiles.conf'
    if (-not (Test-Path -LiteralPath $conf -PathType Leaf)) {
      $out.Why = "홈 씨앗에 묶음 목록이 없어 안 갈았다 ($conf)"
      $out.Fix = "$again — 같으면 이 줄을 그대로 보낸다(홈 씨앗이 덜 깔렸다)"
      return $out
    }
    $root = [IO.Path]::GetFullPath($Repo).TrimEnd('\')
    # git 저장소가 아닌 폴더(풀어 놓은 사본 등)는 덮기 전 판을 들 자가 없다 — 안 쓰고, 고치는 길도 안 댄다(설치가 가리킬 길이 없다)
    $inTree = [string](@(Get-Quiet 'git' @('-C', $root, 'rev-parse', '--is-inside-work-tree')) | Select-Object -Last 1)
    if ($LASTEXITCODE -ne 0 -or $inTree -ne 'true') {
      $out.Why = 'git 저장소가 아닌 폴더라 안 갈았다 — 덮으면 되돌릴 길이 없다'
      return $out
    }
    $todo = @(); $present = @()
    foreach ($rel in @(Get-Content -LiteralPath $conf -Encoding UTF8 | ForEach-Object { ($_ -replace '#.*$', '').Trim() } | Where-Object { $_ })) {
      $from = Join-Path $Seed ($rel -replace '/', '\')
      if (-not (Test-Path -LiteralPath $from -PathType Leaf)) { continue }
      $to = Join-Path $root ($rel -replace '/', '\')
      $hop = Get-OutsideHop $root $to
      if ($hop) {
        $out.Why = "저장소 밖으로 이어진 갈래($hop)를 지나야 해서 안 갈았다 — 쓰면 저장소 밖에 앉는다"
        $out.Fix = "그 갈래($hop)를 걷거나 저장소 안의 진짜 폴더로 바꾼 뒤 $again"
        return $out
      }
      $has = Test-Path -LiteralPath $to -PathType Leaf
      if ($has) { $present += @{ Rel = $rel; From = $from; To = $to } }
      if ($has -and (Get-FileHash -LiteralPath $from).Hash -eq (Get-FileHash -LiteralPath $to).Hash) { continue }
      if ($has -and $rel -eq '.claude/settings.json') {
        $m = Merge-RepoSettings $to $from $root (Join-Path $Seed '.claude\hooks')
        $out.Dropped = @($m.Dropped)
        if (-not $m.Ok) { $out.SettingsNote = "$($m.Why) · 고치는 길: $($m.Fix)"; continue }
        if ($m.Changed) { $todo += @{ Rel = $rel; To = $to; Has = $true; Bytes = $m.Bytes } }
        continue
      }
      if ($has -and -not (Test-OurMark $to $rel)) { $out.Kept += $rel; continue }
      $todo += @{ Rel = $rel; From = $from; To = $to; Has = $has }
    }
    $todo = @(@($todo | Where-Object { $_.Rel -ne $hookRel }) + @($todo | Where-Object { $_.Rel -eq $hookRel }))
    $over = @($todo | Where-Object { $_.Has })
    $overRels = @($over | ForEach-Object { $_.Rel })
    # 표시 아래 손질은 갈 목록 밖의 우리 파일에서도 막는다 — 계약이 저장소 단위다(표시 아래 손질이 든 저장소는 하나도 안 간다).
    #   합치기를 거절했거나 뜻이 같아 안 쓰는 저장소 설정 · 씨앗과 같은 파일이 그 자리다. 표지가 없어 둔 파일(Kept)은 그 사람의 것이라 안 본다.
    #   ⚠ **바이트가 지금 씨앗과 같은 파일은 표시 아래 달라도 그 사람의 손질로 안 친다** — 표시가 선 파일을 설치기가 갈았으면 그 쓴
    #   것이 인덱스와 다르게 남는데(표시 탓에 `git add` 가 안 담는다), 그것을 손질로 치면 그 저장소는 다른 우리 파일이 바뀔 때마다 막힌다.
    #   그 파일은 안 쓰므로 잃는 것도 없다
    $watch = @($present | Where-Object { $overRels -notcontains $_.Rel -and $out.Kept -notcontains $_.Rel })
    $guard = if ($todo.Count) { @($over) + @($watch) } else { @() }
    if ($guard.Count) {
      $listed = @(Get-Quiet 'git' (@('-C', $root, 'ls-files', '-s', '--') + @($guard | ForEach-Object { $_.Rel })))
      if ($LASTEXITCODE -ne 0) {
        $out.Why = 'git 에 우리 파일의 인덱스를 못 물어 안 갈았다'
        $out.Fix = "그 폴더가 git 저장소로 서는지 본다(git -C `"$root`" status) — 고친 뒤 $again"
        return $out
      }
      $index = @{}
      foreach ($ln in $listed) { if ($ln -match '^\d+ ([0-9a-f]+) \d+\t(.+)$') { $index[$Matches[2]] = $Matches[1] } }
      $outside = @(); $differ = @()
      foreach ($t in $guard) {
        $blob = $index[$t.Rel]
        # git 밖의 파일은 덮을 것만 막는다 — 안 쓰는 파일에는 표시가 설 자리가 없다
        if (-not $blob) { if ($overRels -contains $t.Rel) { $outside += $t.Rel }; continue }
        if ($overRels -notcontains $t.Rel -and (Get-FileHash -LiteralPath $t.From).Hash -eq (Get-FileHash -LiteralPath $t.To).Hash) { continue }
        $now = [string](@(Get-Quiet 'git' @('-C', $root, 'hash-object', "--path=$($t.Rel)", '--', $t.To)) | Select-Object -Last 1)
        if ($LASTEXITCODE -ne 0 -or $now -cne $blob) { $differ += $t.Rel }
      }
      # 인덱스와 다른 것 가운데 표시가 선 것 — `ls-files -v` 의 꼬리표가 S(건너뛰기) · 작은 글자(안 바뀐 셈)다
      $flagged = @()
      if ($differ.Count) {
        foreach ($ln in @(Get-Quiet 'git' (@('-C', $root, 'ls-files', '-v', '--') + $differ))) {
          if ($ln -match '^(\S) (.+)$' -and @('S', 's', 'h') -ccontains $Matches[1]) { $flagged += $Matches[2] }
        }
      }
      # 안 쓰는 파일의 표시 없는 손질은 막지 않는다 — git 이 그대로 보이고 우리가 안 건드린다
      $differ = @($differ | Where-Object { $flagged -contains $_ -or $overRels -contains $_ })
      if ($outside.Count -or $differ.Count) {
        $plain = @($differ | Where-Object { $flagged -notcontains $_ })
        $whyParts = @(); $fixParts = @()
        if ($plain.Count) {
          $whyParts += "커밋 안 한 손질: $($plain -join ' · ')"
          $fixParts += "커밋 안 한 손질($($plain -join ' · '))은 커밋하거나 stash 하고"
        }
        if ($flagged.Count) {
          $whyParts += "건너뛰기 · 안 바뀐 셈 표시 아래 손질: $($flagged -join ' · ')"
          $fixParts += "표시를 걷고(git -C `"$root`" update-index --no-skip-worktree --no-assume-unchanged -- $($flagged -join ' ')) 그 손질을 커밋하거나 stash 하고"
        }
        if ($outside.Count) {
          $whyParts += "git 밖의 파일(추적 안 됨 · 무시됨): $($outside -join ' · ')"
          $fixParts += "git 밖의 파일($($outside -join ' · '))은 지워도 되면 지우고 둘 것이면 다른 이름으로 옮기고"
        }
        $out.Why = "우리 파일의 작업 나무가 git 에 든 것과 달라 안 갈았다 — 덮으면 되돌릴 길이 없다 ($($whyParts -join ' / '))"
        $out.Fix = ($fixParts -join ' · ') + " 그 뒤 $again"
        return $out
      }
    }
  } catch {
    $out.Why = "우리 파일을 못 읽어 안 갈았다 — $($_.Exception.Message)"
    $out.Fix = "그 저장소의 파일을 쥔 프로그램(편집기 · 동기화 · 백신)을 닫고 $again"
    return $out
  }
  foreach ($t in $todo) {
    try {
      # 대상이 링크면 링크를 걷고 쓴다 — 복사가 링크를 따라가 가리키는 원본을 덮는다(배포의 저장소 칸과 같은 까닭)
      $it = Get-Item -LiteralPath $t.To -Force -ErrorAction SilentlyContinue
      if ($it -and $it.LinkType) { Remove-Item -LiteralPath $t.To -Force }
      [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($t.To))
      if ($t.Bytes) { [IO.File]::WriteAllBytes($t.To, [byte[]]$t.Bytes); $out.Edited += $t.Rel }
      else { Copy-Item -LiteralPath $t.From -Destination $t.To -Force; if ($t.Has) { $out.Overwrote += $t.Rel } }
      $out.Files += $t.Rel
    } catch {
      $out.Why = "쓰다 졌다 — $($t.Rel): $($_.Exception.Message)$(if ($out.Files.Count) { " · 먼저 쓴 것: $($out.Files -join ' · ')" }) · 훅은 맨 뒤라 옛 판 그대로다"
      $out.Fix = "그 파일을 쥔 프로그램(편집기 · 동기화 · 백신)을 닫고 $again — 다음 실행이 이어서 간다"
      return $out
    }
  }
  $out.Ok = $true
  return $out
}

# 형제 꼴 옛 사본 하나를 간다 — `Update-OurRepoFiles` 를 부르고 다시 가른다. 가른 표(`Get-SessionHookGen` 의 꼴)의 Refreshed · Overwrote ·
#   Edited · Kept · SettingsNote · Dropped · Current · Why · Fix 를 그 결과로 채운다(claude-config 결정 0129). 칸에서 받은 저장소와 작업 루트
#   훑기가 같은 자를 쓴다.
function Invoke-HookRefresh([hashtable]$g, [string]$Seed) {
  $u = Update-OurRepoFiles $g.Repo $Seed
  $g.Refreshed = @($u.Files); $g.Overwrote = @($u.Overwrote); $g.Edited = @($u.Edited); $g.Kept = @($u.Kept)
  $g.SettingsNote = $u.SettingsNote; $g.Dropped = @($u.Dropped)
  if (-not $u.Ok) { $g.Why = $u.Why; $g.Fix = $u.Fix; return }
  $now = Get-SessionHookGen $g.Repo
  if ($now -and $now.Current) { $g.Current = $true; $g.Why = ''; $g.Fix = ''; return }
  $g.Why = "지금 판으로 갈았는데도 옛 판으로 읽힌다 — 홈 씨앗($Seed)이 이 설치기의 판이 아닐 수 있다$(if ($g.Refreshed.Count) { " · 쓴 것: $($g.Refreshed -join ' · ')" })"
  $g.Fix = '설치를 다시 누른다 — 같으면 이 줄을 그대로 보낸다'
}

# 간 저장소의 줄 — 「우리 파일을 지금 판으로 갈았다」 한 줄에 덮은 파일 · 우리 항목만 고친 파일(저장소 설정) · 새로 둔 파일 · 우리 표지가 없어
#   둔 파일과, 바뀐 파일 하나를 보고 되돌리는 명령을 댄다. 사람이 고쳐 커밋한 우리 파일도 덮인다(결정 0129 — 사용자가 받아들인 위험)라 덮은 것은
#   하나하나 이름을 댄다. 작업 나무에만 썼으니 그 사람이 보고 커밋해야 선다. 저장소 설정을 못 고쳤거나 우리 것인지 모르는 등록을 뒀으면 그 줄이
#   하나씩 뒤따른다.
function Write-RefreshLine([hashtable]$g) {
  $changed = @(@($g.Overwrote) + @($g.Edited))
  $added = @($g.Refreshed | Where-Object { $changed -notcontains $_ })
  $parts = @("우리 파일을 지금 판으로 갈았다 — $($g.Repo)")
  if ($g.Overwrote.Count) { $parts += "덮은 것: $($g.Overwrote -join ' · ')" }
  if ($g.Edited.Count) { $parts += "우리 항목만 고쳤다: $($g.Edited -join ' · ')$(if ($g.Dropped.Count) { " (파일이 없는 우리 훅 등록을 걷었다: $($g.Dropped -join ' · '))" })" }
  if ($added.Count) { $parts += "새로 둔 것: $($added -join ' · ')" }
  if ($g.Kept.Count) { $parts += "우리 표지가 없어 둔 것: $($g.Kept -join ' · ')" }
  if ($changed.Count) { $parts += "바뀐 파일 하나 보기 git -C `"$($g.Repo)`" diff -- <파일> · 되돌리기 git -C `"$($g.Repo)`" checkout -- <파일>" }
  $parts += '그 저장소에서 보고 커밋한다'
  Write-Host ('  ' + ($parts -join ' · ')) -ForegroundColor Green
  if ($g.SettingsNote) { Write-Host "     $($g.SettingsNote)" }
}

# 못 갈았거나 못 넘기는 저장소의 세 줄 — 머리 · 까닭 · 고치는 길(설치가 가리킬 길이 없으면 — git 저장소가 아닌 폴더 — 고치는 길 줄은 없다).
#   실패로 세지 않는다 — 이 설치기의 몫은 다 섰고 남은 것은 그 저장소의 사본이나 곁의 설정 저장소다. 빨강으로 세면 멀쩡한 설치가 빨갛게 끝난다.
function Write-HookNotice([hashtable]$o, [string]$Head) {
  Write-Host "  ! $Head — $($o.Repo)" -ForegroundColor Yellow
  Write-Host "     $(if ($o.Blocked) { $o.Blocked } else { $o.Why })"
  if ($o.Fix) { Write-Host "     고치는 길: $($o.Fix)" }
}

# 작업 루트를 훑는다 — 바로 아래 저장소 가운데 칸에서 받지 않은 것의 옛 우리 사본을 다룬다(claude-config 결정 0129 · PAISetup#25 사용자
#   결정 ①). 칸에 저장소를 안 넣은 동료도 옛 설치 · 배포가 놓은 우리 훅을 작업 저장소에 든다. 작업 루트는 칸의 저장소를 받는 그
#   자리(`$configRepoRoot`)다 — 배포가 형제를 두는 자리(`ROOT`)와 찾는 자가 형제를 보는 자리가 그 바로 아래다.
#   · 형제 꼴 옛 사본 — 제작자 칸을 켰으면 칸에서 받은 것과 같은 지킴으로 간다(`Invoke-HookRefresh`). 끄면 알리기만 한다
#   · 작업 루트 밖으로 이어진 갈래(정션 · 링크 폴더)인 아이 — 그 너머에 안 쓰고 알린다(`Get-OutsideHop` 과 같은 까닭 — 쓰면 작업 루트 밖에 앉는다)
#   · 설정 저장소 꼴 옛 사본 — 안 쓰고 알린다
#   · 넘기지 않는다 — 그 사람이 그 저장소의 훅에 설치를 맡긴 적이 없다
#   우리 것이 아니거나 지금 판이면 말없이 지나간다. 갈래는 끝까지 따라가 실제 자리로 견준다 — 칸에서 받은 저장소나 앞서 본 아이를 다른 이름으로
#   가리키는 갈래는 두 번 안 본다(진짜 폴더를 먼저 본다).
# 받는 것 — 작업 루트 · 칸에서 받은 저장소(그 자리에서 이미 다뤘다 — 두 번 안 본다) · 제작자 칸을 켰나 · 홈 씨앗
# 내는 것 — 찾은 옛 사본의 가른 표 목록. 간 것은 「갈았다」 줄(`Write-RefreshLine`), 못 간 것 · 알릴 것은 `Write-HookNotice` 로 그 자리에서 낸다
function Invoke-WorkRootScan([string]$Root, [string[]]$Handled, [bool]$CreatorOn, [string]$Seed) {
  $found = @()
  if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return , $found }
  $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\')
  # 실제 자리 — 갈래를 끝까지 따라간 전체 경로. 끝을 못 풀면 빈 글
  $realOf = { param([string]$p)
    $cur = [IO.Path]::GetFullPath($p).TrimEnd('\')
    for ($i = 0; $i -lt 16; $i++) {
      $it = Get-Item -LiteralPath $cur -Force -ErrorAction SilentlyContinue
      if (-not $it -or -not ($it.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return $cur }
      $tg = [string](@($it.Target) | Select-Object -First 1)
      if (-not $tg) { return '' }
      if (-not [IO.Path]::IsPathRooted($tg)) { $tg = Join-Path (Split-Path $cur -Parent) $tg }
      $cur = [IO.Path]::GetFullPath($tg).TrimEnd('\')
    }
    return '' }
  $seen = @($Handled | Where-Object { $_ } | ForEach-Object { & $realOf $_ } | Where-Object { $_ })
  $kids = @(Get-ChildItem -LiteralPath $Root -Directory -Force -ErrorAction SilentlyContinue |
            Sort-Object -Property @{ Expression = { [bool]($_.Attributes -band [IO.FileAttributes]::ReparsePoint) } }, Name)
  foreach ($d in $kids) {
    $real = & $realOf $d.FullName
    if ($real -and $seen -contains $real) { continue }
    if ($real) { $seen += $real }
    $g = Get-SessionHookGen $d.FullName
    if (-not $g -or -not $g.Ours -or $g.Current) { continue }
    if ($g.Shape -eq 'sibling') {
      if (-not ($real -and $real.StartsWith("$rootFull\", [StringComparison]::OrdinalIgnoreCase))) {
        $g.Why = "$($g.Why) · 이 자리는 작업 루트 밖($(if ($real) { $real } else { '끝을 못 푼 갈래' }))으로 이어진 갈래라 설치가 그 너머에 안 쓴다"
        $g.Fix = '그 저장소를 작업 루트 안으로 옮기면 다음 설치가 같은 지킴으로 간다 · 이 훅을 안 쓰면 그 저장소의 .claude/hooks/session-start.sh 와 .claude/settings.json 의 SessionStart 줄을 걷는다'
      } elseif ($CreatorOn) { Invoke-HookRefresh $g $Seed }
      else { $g.Fix = '제작자 칸을 켜고 설치를 다시 누르면 설치가 같은 지킴으로 지금 판으로 간다 · 그 저장소에서 이 훅을 안 쓰면 .claude/hooks/session-start.sh 와 .claude/settings.json 의 SessionStart 줄을 걷는다' }
    }
    $found += $g
  }
  foreach ($g in @($found | Where-Object { $_.Refreshed.Count -and $_.Current })) { Write-RefreshLine $g }
  foreach ($o in @($found | Where-Object { -not $_.Current })) { Write-HookNotice $o '작업 루트의 옛 우리 훅 — 칸에 안 든 저장소' }
  return , $found
}

# 우리 훅을 넘기면 그 몸통이 잡을 설정 저장소(`CONFIG_ROOT`)가 이 설치기와 같은 세대인가(claude-config 결정 0129). 문지기는 그 저장소의
#   몸통을 홈 씨앗보다 먼저 부르고, 몸통은 PC 에서 `--install` 이면 그 저장소의 `deploy.ps1` 에 넘긴다. 손 이전 판의 몸통과
#   `deploy.ps1` 은 홈 규범을 제 손으로 붓는다 — 받은 저장소가 지금 판이어도 곁에 낡은 claude-config 클론이 서 있으면 넘기는 순간 덮인다.
# 찾기는 홈 씨앗의 찾는 자(`.githooks/claude-config-path.sh` — 문지기와 몸통이 읽는 그 자)를 Git Bash 로 불러 맡긴다 — 후보를 여기
#   옮겨 적지 않는다. 답은 파일로 받아 UTF-8 로 읽는다 — 자식의 표준 출력은 이 창의 콘솔 코드 페이지로 풀려, 그것이 UTF-8 이 아니면
#   한글 자리가 깨진다.
# 내는 것 — @{ Root; Current; Why; Fix }. 설정 저장소가 없거나 그 저장소 자신이면 Current 다(자신의 판은 `Get-SessionHookGen` 이 쟀다).
#   못 잰 것은 Current 가 아니다 — Git Bash · 찾는 자가 없다 · 찾는 자가 졌다 · 찾은 자리가 있는 폴더가 아니다 · 읽다 졌다
function Get-ConfigRootGen([string]$Repo, [string]$Bash, [string]$Finder) {
  $r = @{ Root = ''; Current = $true; Why = ''; Fix = '' }
  $unmeasured = { param([string]$why)
    $r.Current = $false
    $r.Why = "넘기면 잡힐 곁의 설정 저장소를 못 쟀다 — $why"
    $r.Fix = '설치를 다시 누른다 — 같으면 이 줄을 그대로 보낸다'
    $r }
  $tag = [guid]::NewGuid().ToString('N')
  $probe = Join-Path ([IO.Path]::GetTempPath()) "paisetup-config-root-$tag.sh"
  $answer = Join-Path ([IO.Path]::GetTempPath()) "paisetup-config-root-$tag.txt"
  $saveLc = $env:LC_ALL
  try {
    if (-not $Bash) { return (& $unmeasured 'Git Bash 가 없다') }
    if (-not (Test-Path -LiteralPath $Finder -PathType Leaf)) { return (& $unmeasured "찾는 자가 없다 ($Finder)") }
    # 찾는 자를 점으로 읽고 찾은 자리를 윈도 꼴로 파일에 쓰는 세 줄 — 파일로 넘긴다. `-c` 로 넘기면 파워셸 5.1 이 글 안의 큰따옴표를 안
    #   감싸 깨진다. 로캘을 UTF-8 로 세워 인자와 답이 UTF-8 로 오간다
    [IO.File]::WriteAllText($probe, ('PROJECT_DIR="$1"' + "`n" + '. "$2"' + "`n" + '[ -z "$CONFIG_ROOT" ] || cygpath -w "$CONFIG_ROOT" > "$3"' + "`n"),
                            (New-Object Text.UTF8Encoding($false)))
    $env:LC_ALL = 'C.UTF-8'
    $null = Get-Quiet $Bash @(($probe -replace '\\', '/'), ($Repo -replace '\\', '/'), ($Finder -replace '\\', '/'), ($answer -replace '\\', '/'))
    if ($LASTEXITCODE -ne 0) { return (& $unmeasured "찾는 자가 exit $LASTEXITCODE 로 끝났다") }
    $root = if (Test-Path -LiteralPath $answer -PathType Leaf) { [IO.File]::ReadAllText($answer, [Text.Encoding]::UTF8).Trim() } else { '' }
    if (-not $root) { return $r }
    $r.Root = $root
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { return (& $unmeasured "찾은 자리가 있는 폴더가 아니다 ($root)") }
    if ([IO.Path]::GetFullPath($root).TrimEnd('\') -ieq [IO.Path]::GetFullPath($Repo).TrimEnd('\')) { return $r }
    $read = { param([string]$p) try { [IO.File]::ReadAllText($p) } catch { '' } }
    $old = @()
    foreach ($f in @('.claude\hooks\session-start-body.sh', 'deploy.ps1')) {
      $p = Join-Path $root $f
      if ((Test-Path -LiteralPath $p -PathType Leaf) -and -not (& $read $p).Contains('tool-homes.py')) { $old += ($f -replace '\\', '/') }
    }
    if ($old.Count) {
      $r.Current = $false
      $r.Why = "넘기면 곁의 설정 저장소($root)의 $($old -join ' · ') 가 도는데 손(tool-homes.py)을 안 부르는 옛 판이다 — 「도구별 홈」이 손으로 놓은 것을 덮는다"
      $r.Fix = "그 설정 저장소를 지금 판으로 당긴 뒤(git -C `"$root`" pull --ff-only) 설치를 다시 누른다"
    }
    return $r
  } catch {
    return (& $unmeasured $_.Exception.Message)
  } finally {
    $env:LC_ALL = $saveLc
    Remove-Item -LiteralPath $probe, $answer -Force -ErrorAction SilentlyContinue
  }
}

# 나른 것을 동봉본과 견주는 자 — 이름 · 원본 · 나른 자리를 받아 @{ Name = '이름 (나른 수/원본 수 · 여분 N)'; Ok } 를 낸다.
#   「공용 자산」 걸음의 자산이 다 이 자를 쓴다.
# ⚠ **폴더가 있나로 묻지 않고 파일 수를 센다** — `New-Item` 이 먼저 도니 복사가 실패해도 폴더는 남아, 빈 폴더를 [O] 로 찍으면
#   「깔렸는데 안 든 것」이 성공으로 보고된다.
# 여분은 판정이 아니라 눈금이다 — 수는 찍되 [X] 는 모자랄 때만 든다. 그래서 거울로 까는 자리(씨앗)와 덮어쓰기로 두는 자리(사내
#   환경 문서)가 같은 자를 쓴다.
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

# 한 폴더 아래 파일 — 상대 자리(`\` 로 · 대소문자를 안 가리는 표의 열쇠) → 온 자리. `__pycache__` 아래는 안 센다 — 파이썬이 남긴 그 PC 의
#   부산물이지 자산이 아니다(설정 저장소의 배포 · 세션 훅도 안 민다). 폴더가 없으면 빈 표다.
function Get-AssetFiles([string]$Dir) {
  $out = @{}
  if (-not (Test-Path -LiteralPath $Dir -PathType Container)) { return $out }
  $base = (Get-Item -LiteralPath $Dir -Force).FullName.TrimEnd('\')
  foreach ($f in @(Get-ChildItem -LiteralPath $base -Recurse -File -Force -ErrorAction SilentlyContinue)) {
    $rel = $f.FullName.Substring($base.Length + 1)
    if (('\' + $rel) -match '[\\]__pycache__[\\]') { continue }
    $out[$rel] = $f.FullName
  }
  return $out
}

# 놓은 자리가 원본과 같은가 — 원본의 파일마다 그 자리에 바이트까지 같은 파일이 있나(모자람 · 다름), 그 자리에만 있는 파일(여분)이 있나.
#   여분은 `-ExtraOk` 면 판정에 안 든다 — 남이 쓰는 파일이 같이 사는 자리(사내 환경 문서)다. 내는 것 — @{ Ok; Say(어긋난 것을 짧게) }.
#   `-Only` 를 주면 원본은 그 상대 자리의 파일뿐이다 — 원본 폴더에 원본이 아닌 파일(git 이 무시하는 런타임 기록)이 같이 사는 자리다.
function Compare-AssetTree([string]$From, [string]$To, [switch]$ExtraOk, [string[]]$Only) {
  $src = Get-AssetFiles $From
  if ($PSBoundParameters.ContainsKey('Only')) {
    $keep = @{}; foreach ($k in @($Only)) { $keep[$k] = $true }
    foreach ($k in @($src.Keys)) { if (-not $keep.ContainsKey($k)) { $src.Remove($k) } }
  }
  $dst = Get-AssetFiles $To
  $miss = @(); $diff = @()
  foreach ($k in $src.Keys) {
    if (-not $dst.ContainsKey($k)) { $miss += $k; continue }
    if ((Get-FileHash -LiteralPath $src[$k] -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $dst[$k] -Algorithm SHA256).Hash) { $diff += $k }
  }
  $extra = @($dst.Keys | Where-Object { -not $src.ContainsKey($_) })
  $say = @()
  if (-not $src.Count) { $say += '원본이 비었다' }
  if ($miss.Count)  { $say += "모자람 $($miss.Count): $((@($miss | Sort-Object | Select-Object -First 3)) -join ', ')" }
  if ($diff.Count)  { $say += "다름 $($diff.Count): $((@($diff | Sort-Object | Select-Object -First 3)) -join ', ')" }
  if ($extra.Count) { $say += "여분 $($extra.Count)$(if (-not $ExtraOk) { ': ' + ((@($extra | Sort-Object | Select-Object -First 3)) -join ', ') })" }
  return @{ Ok = ($src.Count -gt 0 -and -not $miss.Count -and -not $diff.Count -and ($ExtraOk -or -not $extra.Count)); Say = ($say -join ' · ')
            N = $src.Count }
}

# 남의 파일이 같이 사는 공용 자산(사내 환경 문서)을 장부로 맞춘다 (PAISetup #44 ⑭) — 원본을 덮어 깐 뒤 부른다. 받는 것: 「공용 자산」의
#   자산 한 줄(@{ From; To; Name }). 내는 것: 걷은 파일 수. 장부 줄의 꼴은 「장부」 칸이 든다 — 자리 `file` · 그 안의 자리는 그 폴더 ·
#   이름은 폴더 안의 상대 자리 · 심은 손 `assets` · 값은 놓은 바이트의 SHA256.
#   · 우리 것은 장부의 그 자리 줄에 든 파일뿐이다 — 프록시의 기록(`proxy.log` · `*.pid`) · 시험 결과 · 사람이 둔 파일은 줄이 없어 안
#     건드린다. 런타임 파일 이름을 여기 따로 적지 않는 까닭이다
#   · 줄에 있는데 원본에서 빠진 파일은 놓은 바이트 그대로면 지우고, 바뀌었으면 사람 것으로 두고 노란 줄로 알린다(줄은 뺀다 — 다시
#     안 알린다). 못 지웠으면 빨간 줄 · `$Fails` 이고 줄을 둔다 — 다음 판이 다시 걷는다
#   · 그 자리 줄이 하나도 없으면(장부 앞에 깐 판) 원본에 없는 파일을 노란 줄로 한 번 알리고 둔다 — 우리가 깐 것인지 알 길이 없다
#   · 그 뒤 원본의 파일마다 놓인 바이트로 줄을 갈아 쓴다. `-Drop` 이면 걷지도 놓지도 않고 그 자리 줄만 뺀다(설정 저장소가 든 판)
#   · 장부를 못 읽었으면 걷지 않고 쓰지 않는다 — 노란 줄
function Sync-AssetLedger($Asset, [switch]$Drop) {
  $L = Read-RunLedger $ClaudePlantLedger
  if ($L.Why) {
    if (-not $Drop) { Write-Host "  ! $($Asset.Name) — 장부를 못 읽어 원본에서 빠진 파일을 안 걷었다 ($($L.Why) · $($L.Path))" -ForegroundColor Yellow }
    return 0
  }
  $at = ConvertTo-LedgerAt $Asset.To
  $rows = @(Find-LedgerRows $L 'file' $at 'assets')
  if ($Drop) {
    if ($rows.Count) { foreach ($r in $rows) { [void]$L.Rows.Remove($r) }; $null = Save-PlantLedger $L }
    return 0
  }
  $src = Get-AssetFiles $Asset.From
  $swept = 0; $kept = @(); $fail = @()
  foreach ($r in $rows) {
    if ($src.ContainsKey($r.Name)) { continue }
    $p = Join-Path $Asset.To $r.Name
    if (Test-Path -LiteralPath $p -PathType Leaf) {
      if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -cne $r.Value) { $kept += $r.Name }
      else {
        try { Remove-Item -LiteralPath $p -Force -ErrorAction Stop; $swept++ } catch { $fail += $r.Name; continue }
        # 걷은 파일의 빈 폴더를 위로 걷는다 — 그 자산 폴더 자체는 둔다
        $up = Split-Path $p -Parent
        while ($up.Length -gt $Asset.To.Length -and -not (Get-ChildItem -LiteralPath $up -Force -ErrorAction SilentlyContinue | Select-Object -First 1)) {
          Remove-Item -LiteralPath $up -Force -ErrorAction SilentlyContinue
          $up = Split-Path $up -Parent
        }
      }
    }
    [void]$L.Rows.Remove($r)
  }
  if (-not $rows.Count) {
    $odd = @((Get-AssetFiles $Asset.To).Keys | Where-Object { -not $src.ContainsKey($_) } | Sort-Object)
    if ($odd.Count) {
      Write-Host "  ! $($Asset.Name) — 원본에 없는 파일 $($odd.Count)개가 있다 · 장부 앞에 깔린 자리라 우리 것인지 몰라 둔다(한 번만 알린다): $((@($odd | Select-Object -First 5)) -join ' · ')$(if ($odd.Count -gt 5) { ' …' })" -ForegroundColor Yellow
      Write-Host "     $($Asset.To)"
    }
  }
  if ($kept.Count) { Write-Host "  ! $($Asset.Name) — 원본에서 빠졌는데 우리가 놓은 뒤 바뀐 파일이라 둔다: $($kept -join ' · ')" -ForegroundColor Yellow }
  if ($fail.Count) {
    Write-Host "  ! $($Asset.Name) — 원본에서 빠진 파일을 못 걷었다: $($fail -join ' · ')" -ForegroundColor Red
    $Fails.Add("$($Asset.Name) (원본에서 빠진 파일 걷기)")
  }
  foreach ($k in $src.Keys) {
    $p = Join-Path $Asset.To $k
    if (Test-Path -LiteralPath $p -PathType Leaf) { Set-LedgerRow $L 'file' $at $k 'assets' (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
  }
  $null = Save-PlantLedger $L
  return $swept
}

#endregion 파일

#region 장부 — 설치기가 심은 것을 적고, 선언 · 장부 · 지금 값으로 그 자리를 맞추고(심기 · 걷기 · 사람 값은 두고 알리기), 끝 검증이 장부와 실물을 견준다

# 장부의 꼴(`$ClaudePlantLedger` · PAISetup #44) — UTF-8(BOM 없음) · 첫 줄은 머리(`Read-PlantLedger` 의 Head · 첫 쓰기가 세운다 —
#   `Save-PlantLedger` 의 ⚠), 그 뒤 한 줄에 하나씩 `자리<탭>그 안의 자리<탭>이름<탭>심은 손<탭>값`.
#   · 자리 — user-env(사용자 환경) · settings-env(홈 settings.json 의 env) · settings(홈 settings.json 의 맨 위 키와 permissions) ·
#     tool(도구 설정 파일의 키)
#   · 그 안의 자리 — 사용자 환경은 `HKCU`, 파일은 그 자리(홈 아래면 `~\…`)에 표가 있으면 `|표이름`
#   · 심은 손 — 그 줄을 선언하는 무리: agy-model · ccbg · values(「키와 값」) · env-push · features · model-picker · permissions
#     (「Claude 홈 설정」) · autorun · codex-sandbox(「도구별 홈」). `seen` 은 우리가 알린 사람 값이다 — 같은 값을 판마다 다시 알리지 않으려고 적는다
#   · 값 — 그 자리에 심은 글(JSON 칸의 표 · 참거짓은 압축 JSON 글). 탭 · 줄바꿈이 든 값은 안 적는다 — 그 값은 우리 것으로 못 알아본다
# ⚠ **permissions 의 두 줄(`defaultMode` · `allow`)은 옛 꼴 `키<탭>값` 으로 쓴다** — 설정 저장소의 세션 훅(`home_settings_seed`)이 그 꼴을 읽어
#   홈을 씨앗으로 덮을 때 우리 권한을 넘겨 준다(claude-config 결정 0119). 머리 없는 파일은 옛 판의 기록이다 — 두 칸 줄을 permissions
#   줄로 읽고, 이 판이 장부를 처음 세우는 판(`Migrating`)으로 본다.
# ⚠ **비밀은 안 적는다** — 회사 키와 그 별칭(`$SettingsEnvSkip`)은 값으로 임자를 가른다(`Test-CompanyKey`). 적으면 평문이 하나 더 는다.
# 장부 손(`Sync-Planted`)은 값으로 임자를 가르는 손(회사 키 · 우리 주소 · 오늘 표 · 오늘 값 파일 — 첫 물결)이 그 판에 이미 가른 이름에는
#   기록만 잇는다(`-Owned`) — 그 손이 못 보는 것(표 · 값 파일에서 빠진 이름 · 바뀐 값 · 끈 자리)을 장부가 든다.

# 두 글이 글자까지 같은가 — 순서 견줌(ordinal)이다. 빈 값($null)은 빈 값과만 같다. `-ceq` 는 문화권 견줌이라 앞에 붙은 BOM(U+FEFF) 같은
#   빈 글자를 건너뛴다(`Read-CompanyKeyBlob` 의 ⚠).
function Test-SameText($A, $B) {
  if ($null -eq $A -or $null -eq $B) { return ($null -eq $A -and $null -eq $B) }
  return [string]::Equals([string]$A, [string]$B, [StringComparison]::Ordinal)
}

# 장부의 「그 안의 자리」 — 파일 자리를 홈(`USERPROFILE`) 아래면 `~\…` 로 적고, 표가 있으면 `|표` 를 붙인다(`|` 는 윈도 경로에 못 선다).
#   `ConvertFrom-LedgerAt` 이 거꾸로 푼다 — @{ Path; Under }.
function ConvertTo-LedgerAt([string]$Path, [string]$Table) {
  if (-not $Path) { return '' }
  $h = [IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd('\') + '\'
  $p = try { [IO.Path]::GetFullPath($Path) } catch { $Path }
  if ($p.StartsWith($h, [StringComparison]::OrdinalIgnoreCase)) { $p = '~\' + $p.Substring($h.Length) }
  if ($Table) { return "$p|$Table" }
  return $p
}
function ConvertFrom-LedgerAt([string]$At) {
  $under = ''
  $i = $At.IndexOf('|')
  if ($i -ge 0) { $under = $At.Substring($i + 1); $At = $At.Substring(0, $i) }
  if ($At.StartsWith('~\')) { $At = Join-Path $env:USERPROFILE $At.Substring(2) }
  return @{ Path = $At; Under = $under }
}

# 장부를 읽는다 — 받는 것: 자리. 내는 것 — @{ Path; Head; Rows(줄 목록 — @{ Place; At; Name; By; Value }); Bytes(읽은 바이트 · 없으면 $null);
#   Migrating(머리가 없다 — 이 판이 처음 세운다); Why(못 읽은 까닭 · 읽었으면 빈 글) }. 꼴에 안 맞는 줄은 버린다(다음 쓰기에 사라진다).
#   못 읽은 장부(Why)는 쓰지 않는다(`Save-PlantLedger`) — 쓰면 그 줄들이 사라진다. 그 판은 기록 없이 심기만 한다.
function Read-PlantLedger([string]$Path) {
  $L = @{ Path = $Path; Rows = New-Object System.Collections.Generic.List[hashtable]; Bytes = $null; Migrating = $true; Why = ''
          Head = '# PAISetup 장부 2 — 설치기가 심은 것: 자리 · 그 안의 자리 · 이름 · 심은 손 · 값 (탭으로 가른다 · 설치기가 판마다 다시 쓴다 · 손으로 고치지 않는다)' }
  if (-not $Path) { $L.Why = '장부 자리가 안 섰다'; return $L }
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $L }
  try { $L.Bytes = [IO.File]::ReadAllBytes($Path) } catch { $L.Why = Say-Why $_; return $L }
  $mark = $L.Head.Substring(0, $L.Head.IndexOf(' —'))
  $homeAt = ConvertTo-LedgerAt (Join-Path $homeDir 'settings.json')
  foreach ($ln in @((Read-TextOf $L.Bytes) -split "`r?`n")) {
    if (-not $ln) { continue }
    if ($ln.StartsWith('#')) { if ($ln.StartsWith($mark)) { $L.Migrating = $false }; continue }
    $f = $ln.Split("`t")
    if ($f.Count -eq 5 -and $f[0] -and $f[2] -and $f[3]) {
      $L.Rows.Add(@{ Place = $f[0]; At = $f[1]; Name = $f[2]; By = $f[3]; Value = $f[4] })
    } elseif ($f.Count -eq 2 -and $f[0] -and $f[1]) {
      $L.Rows.Add(@{ Place = 'settings'; At = $homeAt; Name = "permissions.$($f[0])"; By = 'permissions'; Value = $f[1] })
    }
  }
  return $L
}

# 이 판의 장부를 읽는다 — 처음 세우는 판인가(Migrating)는 판의 첫 읽기(「키와 값」 · `$script:LedgerMigrating` 를 세운다)가 한 번 정하고, 뒤
#   걸음은 머리가 선 장부를 읽어도 그 판정을 잇는다 — 첫 쓰기가 머리를 세우므로(`Save-PlantLedger` 의 ⚠) 판정을 걸음마다 다시 하면 같은 판의
#   뒤 걸음이 옛 판이 심은 값을 안 받는다. 첫 읽기가 없는 판(걸음 하나만 떼어 돌린 판)은 그 장부의 머리로 가른다.
function Read-RunLedger([string]$Path) {
  $L = Read-PlantLedger $Path
  if ($null -ne $script:LedgerMigrating) { $L.Migrating = [bool]$script:LedgerMigrating }
  return $L
}

# 장부를 쓴다 — 받는 것: 장부. 머리를 세우고 줄을 한 차례로 늘어 쓴다(같으면 안 쓴다). 내는 것 — 썼거나 같으면 $true.
#   못 쓰면 노란 줄과 $false 다 — 이 판에 심은 것을 다음 판이 사람 값으로 읽어 안 걷을 수 있다(우리 것을 남의 것으로 세는 쪽으로만 진다).
# ⚠ **머리는 첫 쓰기가 세운다** — 머리가 곧 「처음 세우는 판이 지났다」는 표지다. 판이 중간에 져도 그 앞 걸음이 쓴 줄은 우리가 심은 것이라,
#   다음 판이 다시 처음 세우는 판이 되면 그 사이 사람이 고친 값을 옛 판의 값으로 받아 덮는다(PAISetup #44 끝 조건 「앞 판이 중간에 진 뒤」).
#   같은 판의 뒤 걸음은 머리가 선 장부를 읽어도 그 판의 판정을 잇는다(`Read-RunLedger`).
function Save-PlantLedger($Ledger) {
  if ($Ledger.Why) { return $false }
  $homeAt = ConvertTo-LedgerAt (Join-Path $homeDir 'settings.json')
  $lines = foreach ($r in @($Ledger.Rows | Sort-Object -CaseSensitive -Property @{ Expression = { "$($_.Place)`t$($_.At)`t$($_.Name)`t$($_.By)`t$($_.Value)" } })) {
    if ($r.Place -ceq 'settings' -and $r.At -ceq $homeAt -and $r.By -ceq 'permissions' -and $r.Name -cmatch '^permissions\.(defaultMode|allow)$') {
      "$($Matches[1])`t$($r.Value)"
    } else {
      "$($r.Place)`t$($r.At)`t$($r.Name)`t$($r.By)`t$($r.Value)"
    }
  }
  $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes(((@($Ledger.Head) + @($lines)) -join "`n") + "`n")
  $w = Write-FileSafely $Ledger.Path $bytes $Ledger.Bytes
  if ($w.Did -ceq 'written' -or $w.Did -ceq 'same') { $Ledger.Bytes = $bytes; return $true }
  if ($w.Did -ceq 'overrun') { try { $Ledger.Bytes = [IO.File]::ReadAllBytes($Ledger.Path) } catch { } }
  Write-Host "  ! 장부를 못 썼다 — $($w.Why) · 다음 판은 이번에 심은 것을 사람 값으로 읽어 안 걷을 수 있다 ($($Ledger.Path))" -ForegroundColor Yellow
  $script:LedgerSaveWhy = $w.Why
  return $false
}

# 장부 줄을 다룬다 — 한 자리 · 그 안의 자리 · 심은 손의 줄을 고르고(`Find-LedgerRows`), 한 이름의 줄을 갈고(`Set-LedgerRow` — 목록 칸이 아닌
#   이름), 줄을 더한다(`Add-LedgerRow` — 같은 줄이 있으면 안 더한다). 탭 · 줄바꿈이 든 값은 안 적고 그렇다고 말한다.
#   `Get-LedgerSlice` · `Set-LedgerSlice` 는 한 자리의 줄을 떠 두고 되돌린다 — 그 자리를 못 썼으면 장부가 실물보다 앞서지 않게 한다.
function Find-LedgerRows($Ledger, [string]$Place, [string]$At, [string]$By) {
  return @($Ledger.Rows | Where-Object { $_.Place -ceq $Place -and $_.At -ceq $At -and $_.By -ceq $By })
}
function Add-LedgerRow($Ledger, [string]$Place, [string]$At, [string]$Name, [string]$By, [string]$Value) {
  if ($Value -match "[`t`r`n]" -or $Name -match "[`t`r`n]") { Write-Host "  ($Name — 탭 · 줄바꿈이 든 값이라 장부에 못 적는다 · 다음 판은 이 값을 우리 것으로 못 알아본다)" -ForegroundColor DarkGray; return }
  foreach ($r in $Ledger.Rows) {
    if ($r.Place -ceq $Place -and $r.At -ceq $At -and $r.Name -ceq $Name -and $r.By -ceq $By -and (Test-SameText $r.Value $Value)) { return }
  }
  $Ledger.Rows.Add(@{ Place = $Place; At = $At; Name = $Name; By = $By; Value = $Value })
}
function Set-LedgerRow($Ledger, [string]$Place, [string]$At, [string]$Name, [string]$By, [string]$Value) {
  foreach ($r in @($Ledger.Rows | Where-Object { $_.Place -ceq $Place -and $_.At -ceq $At -and $_.Name -ceq $Name -and $_.By -ceq $By })) { [void]$Ledger.Rows.Remove($r) }
  Add-LedgerRow $Ledger $Place $At $Name $By $Value
}
function Get-LedgerSlice($Ledger, [string[]]$Places, [string]$At) {
  return @($Ledger.Rows | Where-Object { $Places -ccontains $_.Place -and (-not $At -or $_.At -ceq $At) } | ForEach-Object { $_.Clone() })
}
function Set-LedgerSlice($Ledger, [string[]]$Places, [string]$At, [object[]]$Rows) {
  foreach ($r in @($Ledger.Rows | Where-Object { $Places -ccontains $_.Place -and (-not $At -or $_.At -ceq $At) })) { [void]$Ledger.Rows.Remove($r) }
  foreach ($r in @($Rows)) { $Ledger.Rows.Add($r) }
}

# 자리마다 표가 준 값 — 받는 것: 자리마다 `[ordered]@{<이름> = <값>}` 인 표들(`$AgyModelVarsBySite` 꼴). 내는 것 — 이름 → 어느 자리든 그 이름에
#   준 값 목록. 맡기기 러너 값이 오늘 표의 값인가를 묻는 자리(걷는 손 · settings.json 의 러너 사본 · 장부 손의 `-Owned`)가 이것 하나로 묻는다.
function Get-SiteValues([object[]]$Tables) {
  $vals = @{}
  foreach ($bySite in @($Tables)) {
    if (-not $bySite) { continue }
    foreach ($s in @($bySite.Keys | Sort-Object)) {
      foreach ($k in @($bySite[$s].Keys)) {
        if (-not $vals.ContainsKey($k)) { $vals[$k] = @() }
        $vals[$k] += [string]$bySite[$s][$k]
      }
    }
  }
  return $vals
}

# 장부 손 — 한 자리 · 한 손(`$By`)의 선언 · 장부 · 지금 값으로 그 자리를 맞춘다.
# 받는 것 —
#   · 장부(`Read-PlantLedger`) · 자리(`$Place` · `$At` — 장부 칸 그대로) · 심은 손 이름 · 선언(`$Want` — 이름 → 값 글 · `-List` 면 이름 → 값 글 목록)
#   · 자리를 읽고 쓰는 손 셋 — `$Get`(이름 → $null 없음 · 글 · `@{ Unread = 까닭 }` 못 읽음 · `-List` 면 `@{ List = 글 목록 }`) · `$Set`(이름 · 값 →
#     참이면 섰다) · `$Remove`(이름 · 값 → 참이면 걷었다)
#   · 맞추는 꼴(`$Mode`) — overwrite 는 선언이 이긴다(지금 값이 달라도 덮는다 · 같은 값은 우리 것으로 적는다), guard 는 사람 값이 이긴다(장부의
#     우리 값 그대로일 때만 바꾸고, 다른 값은 두고 알린다)
#   · `$Plant`(거짓이면 없는 이름을 안 심는다 — 심는 손이 따로 있는 자리) · `$Adopt`(guard 꼴에서 같은 값을 우리 것으로 적을 이름 — 이 판이
#     방금 심었거나, 장부를 처음 세우는 판) · `$Complete`(선언이 이 손의 전부인가 — 거짓이면 아무것도 안 걷는다) · `$Hold`(이번 판에 못 가른
#     이름 — 안 걷는다) · `$Owned`(이름 · 지금 값 → 참이면 값으로 가르는 손이 이 판에 이미 가른 이름 — 장부는 기록만 잇는다) ·
#     `$Names`(주면 이 이름들의 줄만 본다 — 한 손의 줄을 칸마다 나눠 맞출 때)
#   · 화면 — `$Label`(이름 → 글) · `$Where`(줄 끝 괄호) · `-Speak`(심고 걷은 줄을 여기서 찍는다 — 안 주면 쓰는 손이 찍는다) ·
#     `-SayKept`(사람 값이라 둔 줄을 판마다 찍는다) · `-ShowValue`(그 줄에 사람 값을 찍는다 — 비밀이 아닌 자리만)
# 내는 것 — @{ Planted; Replaced; Removed; Kept; Failed; Unread }(이름 목록). 장부는 메모리에서만 고친다 — 쓰는 것은 부르는 쪽이 그 자리를
#   다 쓴 뒤 `Save-PlantLedger` 로 한다(자리보다 장부가 앞서지 않게).
# 규칙 — 선언에 든 이름: 지금 값이 선언과 같으면 둔다(overwrite 꼴 · `$Adopt` 이름은 우리 것으로 적는다) · 없으면 심고 적는다 · 다르면 장부의
#   우리 값 그대로일 때 바꾸고 적는다 — 아니면 overwrite 꼴은 덮고 적고, guard 꼴은 사람 값으로 두고 알린다. 장부에만 든 이름(선언이 전부일
#   때만): 지금 값이 장부의 값 그대로면 걷는다 · 다르면 사람이 바꾼 것이라 두고 그 이름을 한 번 대고 장부에서 뺀다 · 없으면 장부에서만 뺀다.
# ⚠ **넘기는 손 안에서 이 함수의 이름을 쓰지 않는다** — 손은 부르는 쪽의 변수를 그대로 본다(동적 범위). 이 함수의 지역 이름은 `sp` 로 시작한다.
function Sync-Planted {
  param($Ledger, [string]$Place, [string]$At, [string]$By, [System.Collections.IDictionary]$Want,
        [scriptblock]$Get, [scriptblock]$Set, [scriptblock]$Remove,
        [ValidateSet('overwrite', 'guard')][string]$Mode = 'overwrite', [bool]$Plant = $true, [string[]]$Adopt = @(),
        [bool]$Complete = $true, [string[]]$Hold = @(), [scriptblock]$Owned, [switch]$List, [string[]]$Names,
        [System.Collections.IDictionary]$Label = @{}, [string]$Where = '', [switch]$Speak, [switch]$SayKept, [switch]$ShowValue)
  $spRes = @{ Planted = @(); Replaced = @(); Removed = @(); Kept = @(); Failed = @(); Unread = @() }
  $spTail = if ($Where) { " ($Where)" } else { '' }
  $spMine = @(Find-LedgerRows $Ledger $Place $At $By)
  if ($Names) { $spMine = @($spMine | Where-Object { $Names -ccontains $_.Name }) }
  if ($List) {
    foreach ($spN in @($Want.Keys)) {
      $spNm = if ($Label.Contains($spN)) { $Label[$spN] } else { $spN }
      foreach ($spD in @($Want[$spN])) {
        $spCur = & $Get $spN
        if ($spCur -and $spCur.Unread) { $spRes.Unread += $spN; Write-Host "  ! $spNm — $($spCur.Unread) · 안 건드렸다$spTail" -ForegroundColor Yellow; break }
        $spHave = @(if ($spCur) { $spCur.List })
        $spRow = @($spMine | Where-Object { $_.Name -ceq $spN -and (Test-SameText $_.Value $spD) }) | Select-Object -First 1
        if ($spHave -ccontains $spD) {
          if (-not $spRow -and ($Mode -ceq 'overwrite' -or $Adopt -ccontains $spN)) { Add-LedgerRow $Ledger $Place $At $spN $By $spD }
          continue
        }
        if (-not $Plant) { continue }
        if (& $Set $spN $spD) {
          Add-LedgerRow $Ledger $Place $At $spN $By $spD
          $spRes.Planted += $spN
          if ($Speak) { Write-Host "  $spNm — 심었다 ($spD)$spTail" -ForegroundColor Green }
        } else { $spRes.Failed += $spN }
      }
    }
    if ($Complete) {
      foreach ($spRow in $spMine) {
        if ($Want.Contains($spRow.Name) -and @($Want[$spRow.Name]) -ccontains $spRow.Value) { continue }
        if ($Hold -ccontains $spRow.Name) { continue }
        $spNm = if ($Label.Contains($spRow.Name)) { $Label[$spRow.Name] } else { $spRow.Name }
        $spCur = & $Get $spRow.Name
        if ($spCur -and $spCur.Unread) { $spRes.Unread += $spRow.Name; continue }
        if (@(if ($spCur) { $spCur.List }) -ccontains $spRow.Value) {
          if (& $Remove $spRow.Name $spRow.Value) {
            [void]$Ledger.Rows.Remove($spRow); $spRes.Removed += $spRow.Name
            if ($Speak) { Write-Host "  $spNm — 걷었다 (우리가 심은 $($spRow.Value) · 이번에는 안 심는다)$spTail" -ForegroundColor Green }
          } else { $spRes.Failed += $spRow.Name }
        } else {
          [void]$Ledger.Rows.Remove($spRow)
          Write-Host "  $spNm — 사람이 걷어 둔다 (우리 기록에서만 뺐다)$spTail"
        }
      }
    }
    return $spRes
  }
  foreach ($spN in @($Want.Keys)) {
    $spNm = if ($Label.Contains($spN)) { $Label[$spN] } else { $spN }
    $spD = [string]$Want[$spN]
    $spC = & $Get $spN
    if ($spC -is [hashtable]) { $spRes.Unread += $spN; Write-Host "  ! $spNm — $($spC.Unread) · 안 건드렸다$spTail" -ForegroundColor Yellow; continue }
    $spRow = @($spMine | Where-Object { $_.Name -ceq $spN }) | Select-Object -First 1
    $spOurs = [bool]($spRow -and $null -ne $spC -and (Test-SameText $spRow.Value $spC))
    if ($null -ne $spC -and (Test-SameText $spC $spD)) {
      if ($spRow -and (Test-SameText $spRow.Value $spD)) { continue }
      if ($Mode -ceq 'overwrite' -or $Adopt -ccontains $spN) { Set-LedgerRow $Ledger $Place $At $spN $By $spD }
      elseif ($spRow) { [void]$Ledger.Rows.Remove($spRow) }
      continue
    }
    if ($null -eq $spC -and -not $Plant) { if ($spRow) { [void]$Ledger.Rows.Remove($spRow) }; continue }   # 심는 손이 따로다 — 사라진 값은 장부에서만 뺀다
    if ($null -ne $spC -and -not $spOurs -and ($Mode -ceq 'guard' -or -not $Plant)) {
      $spRes.Kept += $spN
      if ($SayKept) { Write-Host "  $spNm — 사람이 정한 값$(if ($ShowValue) { "($spC)" })이라 둔다$spTail" }
      if ($spRow) { [void]$Ledger.Rows.Remove($spRow) }
      continue
    }
    if (& $Set $spN $spD) {
      Set-LedgerRow $Ledger $Place $At $spN $By $spD
      if ($null -eq $spC) { $spRes.Planted += $spN } else { $spRes.Replaced += $spN }
      if ($Speak) {
        $spDid = if ($null -eq $spC) { '심었다' } elseif ($spOurs) { '우리가 심은 옛 값을 새 값으로 바꿨다' } else { '맞췄다' }
        Write-Host "  $spNm — $spDid$spTail" -ForegroundColor Green
      }
    } else { $spRes.Failed += $spN }
  }
  if ($Complete) {
    foreach ($spRow in $spMine) {
      if ($Want.Contains($spRow.Name) -or $Hold -ccontains $spRow.Name) { continue }
      $spNm = if ($Label.Contains($spRow.Name)) { $Label[$spRow.Name] } else { $spRow.Name }
      $spC = & $Get $spRow.Name
      if ($spC -is [hashtable]) { $spRes.Unread += $spRow.Name; continue }
      if ($null -eq $spC) { [void]$Ledger.Rows.Remove($spRow); continue }
      $spSame = Test-SameText $spC $spRow.Value
      if ($Owned -and (& $Owned $spRow.Name $spC)) { if (-not $spSame) { [void]$Ledger.Rows.Remove($spRow) }; continue }
      if ($spSame) {
        if (& $Remove $spRow.Name $spRow.Value) {
          [void]$Ledger.Rows.Remove($spRow); $spRes.Removed += $spRow.Name
          if ($Speak) { Write-Host "  $spNm — 걷었다 (우리가 심은 값 · 이번에는 안 심는다)$spTail" -ForegroundColor Green }
        } else { $spRes.Failed += $spRow.Name }
      } else {
        $spRes.Kept += $spRow.Name
        Write-Host "  $spNm — 우리가 심은 뒤 사람이 바꾼 값이라 둔다 (우리 기록에서만 뺐다)$spTail"
        [void]$Ledger.Rows.Remove($spRow)
      }
    }
  }
  return $spRes
}

# 홈 settings.json 의 한 칸을 장부 손의 꼴로 읽는다 — 받는 것: 읽은 표 · 자리(settings-env 면 `env` 의 이름, settings 면 `modelPicker` ·
#   `permissions.defaultMode` · `permissions.allow`) · 이름. 내는 것 — 없음 $null · 값 글(글이 아닌 값은 압축 JSON) · `permissions.allow` 는
#   `@{ List = 글 목록 }` · 꼴이 틀린 칸은 `@{ Unread = 까닭 }`. 키 이름은 설치기의 다른 칸처럼 대소문자를 안 가린다.
function Get-SettingsSlot($Cfg, [string]$Place, [string]$Name) {
  $text = { param($v) if ($v -is [string]) { $v } else { [string]($v | ConvertTo-Json -Depth 10 -Compress) } }
  if ($Place -ceq 'settings-env') {
    $e = $Cfg.PSObject.Properties['env']
    if (-not $e) { return $null }
    if ($e.Value -isnot [System.Management.Automation.PSCustomObject]) { return @{ Unread = 'env 가 표가 아니다' } }
    $p = $e.Value.PSObject.Properties[$Name]
    if (-not $p) { return $null }
    return (& $text $p.Value)
  }
  if ($Name -ceq 'modelPicker') {
    $p = $Cfg.PSObject.Properties['modelPicker']
    if (-not $p) { return $null }
    return (& $text $p.Value)
  }
  if ($Name -cmatch '^permissions\.(.+)$') {
    $key = $Matches[1]
    $perm = $Cfg.PSObject.Properties['permissions']
    if (-not $perm) { return $null }
    if ($perm.Value -isnot [System.Management.Automation.PSCustomObject]) { return @{ Unread = 'permissions 가 표 꼴이 아니다' } }
    $p = $perm.Value.PSObject.Properties[$key]
    if ($key -ceq 'allow') {
      if (-not $p -or $null -eq $p.Value) { return @{ List = @() } }
      if ($p.Value -isnot [array]) { return @{ Unread = 'permissions.allow 가 목록 꼴이 아니다' } }
      return @{ List = @($p.Value | Where-Object { $null -ne $_ } | ForEach-Object { [string]$_ }) }
    }
    if (-not $p) { return $null }
    return (& $text $p.Value)
  }
  return @{ Unread = "모르는 칸 $Name" }
}

# 도구 설정 파일 하나를 장부 손이 읽고 고치는 꼴로 연다 — 받는 것: 파일 자리 · 표 이름(맨 위면 빈 글) · TOML 인가 · 읽을 키(TOML 만 —
#   파이썬 `tomllib` 로 읽는다 · `Read-TomlTopKeys`).
# 내는 것 — @{ Path; Under; Toml; Bytes(원래 바이트 · 없으면 $null); Obj(JSON 의 맨 위 표 · 없는 파일은 빈 표); Text(TOML 글); Now(TOML 의 그 표 —
#   맨 위면 읽은 키들); Edits(TOML 고침 목록); Why(못 읽은 까닭 · 읽었으면 빈 글); Changed }. 못 읽은 파일은 Why 가 서고 장부 손이 안 건드린다
#   (`Get-ToolDocValue` 가 못 읽음으로 낸다). 고친 것은 `Save-ToolDoc` 이 쓴다.
# ⚠ TOML 의 키는 대소문자를 가린다 — `Get-PropExact` 로 찾는다(`Set-CodexSandboxKey` 와 같은 자).
function Get-PropExact($Obj, [string]$Name) {
  if ($null -eq $Obj) { return $null }
  return (@($Obj.PSObject.Properties | Where-Object { $_.Name -ceq $Name }) | Select-Object -First 1)
}
function Open-ToolDoc([string]$Path, [string]$Under, [bool]$Toml, [string[]]$Keys) {
  $d = @{ Path = $Path; Under = $Under; Toml = $Toml; Bytes = $null; Obj = $null; Text = ''; Now = $null
          Edits = New-Object System.Collections.Generic.List[object]; Why = ''; Changed = $false }
  if (Test-Path -LiteralPath $Path -PathType Leaf) {
    try { $d.Bytes = [IO.File]::ReadAllBytes($Path) } catch { $d.Why = "못 읽었다 ($(Say-Why $_))"; return $d }
  }
  if ($Toml) {
    $d.Now = [pscustomobject]@{}
    if ($null -eq $d.Bytes) { return $d }
    $d.Text = Read-TextOf $d.Bytes
    $timed = $script:ProbeTimedOut.Count
    $now = Read-TomlTopKeys $Path $(if ($Under) { @($Under) } else { @($Keys) })
    if ($null -eq $now) {
      $d.Why = if ($script:ProbeTimedOut.Count -gt $timed) { 'TOML 을 읽는 파이썬이 울타리 안에 안 끝났다' } else { 'TOML 로 못 읽었다(깨진 파일이거나 파이썬 3.11 이상이 안 선다)' }
      return $d
    }
    if ($Under) {
      $u = Get-PropExact $now $Under
      if ($u -and $u.Value -isnot [System.Management.Automation.PSCustomObject]) { $d.Why = "$Under 가 표가 아니다"; return $d }
      if ($u) { $d.Now = $u.Value }
    } else { $d.Now = $now }
    return $d
  }
  $obj = $null
  if ($null -ne $d.Bytes) {
    $text = Read-TextOf $d.Bytes
    if ($text.Trim()) {
      try { $obj = $text | ConvertFrom-Json } catch { $d.Why = 'JSON 으로 못 읽었다'; return $d }
      if ($obj -isnot [System.Management.Automation.PSCustomObject]) { $d.Why = '맨 위가 표가 아니다'; return $d }
    }
  }
  if ($null -eq $obj) { $obj = [pscustomobject]@{} }
  $d.Obj = $obj
  if ($Under) {
    $u = $obj.PSObject.Properties[$Under]
    if ($u -and $u.Value -isnot [System.Management.Automation.PSCustomObject]) { $d.Why = "$Under 가 표가 아니다" }
  }
  return $d
}
# 그 문서의 한 키 — 장부 손의 `$Get` 꼴(없음 $null · 압축 JSON 글 · 못 읽음 `@{ Unread }`).
function Get-ToolDocValue($Doc, [string]$Name) {
  if ($Doc.Why) { return @{ Unread = $Doc.Why } }
  if ($Doc.Toml) { $p = Get-PropExact $Doc.Now $Name }
  else {
    $at = $Doc.Obj
    if ($Doc.Under) { $u = $Doc.Obj.PSObject.Properties[$Doc.Under]; $at = if ($u) { $u.Value } else { $null } }
    $p = if ($at) { $at.PSObject.Properties[$Name] } else { $null }
  }
  if (-not $p) { return $null }
  return [string]($p.Value | ConvertTo-Json -Depth 32 -Compress)
}
# 그 문서의 한 키를 바꾸거나(`Set-ToolDocValue` — 값은 압축 JSON 글) 걷는다(`Remove-ToolDocValue`). 내는 것 — 참이면 메모리에서 고쳤다.
#   TOML 은 글 값만 · 그 키가 이미 선 줄만 고친다(`Edit-TomlLine`) — 줄을 못 찾거나 꼴이 겹치면 거짓이고 안 고친다.
function Set-ToolDocValue($Doc, [string]$Name, [string]$Value) {
  if ($Doc.Why) { return $false }
  $v = $Value | ConvertFrom-Json
  if ($Doc.Toml) {
    $p = Get-PropExact $Doc.Now $Name
    if (-not $p -or $p.Value -isnot [string] -or $v -isnot [string]) { return $false }
    $t = Edit-TomlLine $Doc.Text $Doc.Under $Name $p.Value $v
    if ($null -eq $t) { return $false }
    $Doc.Text = $t; $p.Value = $v
    $Doc.Edits.Add(@('set', $(if ($Doc.Under) { $Doc.Under } else { '-' }), $Name, $v))
    $Doc.Changed = $true
    return $true
  }
  $at = $Doc.Obj
  if ($Doc.Under) {
    if (-not $Doc.Obj.PSObject.Properties[$Doc.Under]) { $Doc.Obj | Add-Member -NotePropertyName $Doc.Under -NotePropertyValue ([pscustomobject]@{}) }
    $at = $Doc.Obj.($Doc.Under)
  }
  $at | Add-Member -NotePropertyName $Name -NotePropertyValue $v -Force
  $Doc.Changed = $true
  return $true
}
function Remove-ToolDocValue($Doc, [string]$Name) {
  if ($Doc.Why) { return $false }
  if ($Doc.Toml) {
    $p = Get-PropExact $Doc.Now $Name
    if (-not $p -or $p.Value -isnot [string]) { return $false }
    $t = Edit-TomlLine $Doc.Text $Doc.Under $Name $p.Value $null
    if ($null -eq $t) { return $false }
    $Doc.Text = $t; $Doc.Now.PSObject.Properties.Remove($p.Name)
    $Doc.Edits.Add(@('del', $(if ($Doc.Under) { $Doc.Under } else { '-' }), $Name, '-'))
    $Doc.Changed = $true
    return $true
  }
  $at = $Doc.Obj
  if ($Doc.Under) { $u = $Doc.Obj.PSObject.Properties[$Doc.Under]; if (-not $u) { return $true }; $at = $u.Value }
  $at.PSObject.Properties.Remove($Name)
  $Doc.Changed = $true
  return $true
}
# TOML 글에서 한 키의 줄(`키 = "값"` · `키 = '값'` — 한 줄짜리 글 값)을 바꾸거나 걷는다 — 받는 것: 글 · 표 이름(맨 위면 빈 글) · 키 · 지금 값 ·
#   새 값($null 이면 걷는다). 그 구역(맨 위면 첫 표 머리 앞 · 표면 그 머리 다음부터 다음 머리 앞)에 그 줄이 꼭 하나일 때만 고친다 — 아니면 $null.
#   고친 줄 밖의 글은 바이트째 그대로다 — 줄마다 제 줄끝(CRLF · LF)을 든 채 나누고 이어 붙인다. 바꾼 줄은 `=` 앞뒤 꼴 · 따옴표 · 줄 끝 주석을 지킨다.
#   표에서 걷어 그 구역에 빈 줄만 남고 머리가 맨 `[표]` 면 머리와 그 빈 줄을 함께 걷는다 — 머리만 남으면 `Set-CodexSandboxKey` 가 그 표를 사람이
#   둔 것으로 읽어 다시 안 심는다. 구역에 주석이 남았거나 머리 줄에 주석이 붙었으면 사람의 글이라 머리째 둔다(빈 표로 남는다) — 머리만 걷으면
#   그 주석이 앞 표 밑으로 넘어간다. 뜻은 쓰기 앞에 파이썬이 잰다(`Save-ToolDoc`) — 여기는 글자만 고친다. 따옴표 · 역슬래시가 든 새 값은 안 다룬다.
function Edit-TomlLine([string]$Text, [string]$Table, [string]$Key, [string]$Old, $New) {
  if ($null -ne $New -and ([string]$New).IndexOfAny([char[]]@('"', "'", '\', "`r", "`n")) -ge 0) { return $null }
  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($ln in [regex]::Split($Text, '(?<=\n)')) { if ($ln.Length) { $lines.Add($ln) } }
  $headPat = "^\[\s*$([regex]::Escape($Table))\s*\]"
  $from = 0; $head = -1
  if ($Table) {
    for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].TrimEnd("`n").TrimEnd("`r") -cmatch "$headPat\s*(#.*)?$") { $head = $i; break } }
    if ($head -lt 0) { return $null }
    $from = $head + 1
  }
  $to = $lines.Count
  for ($i = $from; $i -lt $lines.Count; $i++) { if ($lines[$i] -cmatch '^\[') { $to = $i; break } }
  $o = [regex]::Escape($Old)
  $pat = "^(\s*$([regex]::Escape($Key))\s*=\s*)(`"$o`"|'$o')(\s*(#.*)?)$"
  $hit = @(for ($i = $from; $i -lt $to; $i++) { if ($lines[$i].TrimEnd("`n").TrimEnd("`r") -cmatch $pat) { $i } })
  if ($hit.Count -ne 1) { return $null }
  $at = $hit[0]
  if ($null -ne $New) {
    $b = $lines[$at].TrimEnd("`n").TrimEnd("`r")
    $m = [regex]::Match($b, $pat)
    $q = $m.Groups[2].Value.Substring(0, 1)
    $lines[$at] = $m.Groups[1].Value + $q + $New + $q + $m.Groups[3].Value + $lines[$at].Substring($b.Length)
  } else {
    $lines.RemoveAt($at); $to--
    if ($Table) {
      $rest = @(for ($i = $from; $i -lt $to; $i++) { if ($lines[$i].Trim()) { $i } })
      if (-not $rest.Count -and $lines[$head].Trim() -cmatch "$headPat$") {
        for ($i = $to - 1; $i -ge $head; $i--) { $lines.RemoveAt($i) }
      }
    }
  }
  return (-join $lines)
}
# 고친 문서를 쓴다 — 바이트는 갈아 끼우는 손(`Write-FileSafely`)이 쓴다. JSON 은 `Set-ToolAutoRun` 과 같은 꼴(`-Depth 32` · BOM 없음)로 다시 짓고,
#   TOML 은 고친 글을 원래 파일과 견줘 파이썬이 그 고침만 든 뜻인가를 잰 뒤에만 끼운다(못 재면 안 쓴다). 내는 것 — `Write-FileSafely` 의 꼴
#   (안 고쳤으면 same).
function Save-ToolDoc($Doc) {
  if (-not $Doc.Changed) { return @{ Did = 'same' } }
  $utf8 = New-Object Text.UTF8Encoding($false)
  if (-not $Doc.Toml) { return (Write-FileSafely $Doc.Path ($utf8.GetBytes(($Doc.Obj | ConvertTo-Json -Depth 32))) $Doc.Bytes) }
  # 큰따옴표 없이 적는다 — 값은 글로 받고(`set`), 걷어 빈 표가 그 글에서 사라졌으면 그것도 뜻이 같다
  $code = "import sys,tomllib`na=tomllib.load(open(sys.argv[1],'rb'));b=tomllib.load(open(sys.argv[2],'rb'));e=sys.argv[3:]`n" +
          "for i in range(0,len(e),4):`n  op,t,k,v=e[i:i+4]`n  d=a if t=='-' else a.setdefault(t,{})`n" +
          "  if op=='set':`n    d[k]=v`n  else:`n    d.pop(k,None)`n    if t!='-' and not d and t not in b: a.pop(t,None)`n" +
          "sys.exit(0 if a==b else 3)"
  $orig = $Doc.Path
  $edits = @($Doc.Edits | ForEach-Object { $_ })
  $check = {
    param($side)
    $tl = [IO.Path]::GetTempFileName()
    try { $rc = Invoke-LoggedCapped 'python' (@('-I', '-X', 'utf8', '-c', $code, $orig, $side) + $edits) $tl $ProbeCap }
    finally { Remove-Item -LiteralPath $tl, "$tl.err" -ErrorAction SilentlyContinue }
    if ($rc -eq -2) { Add-ProbeOverflow $TomlReadProbe $ProbeCap }
    return ($rc -eq 0)
  }
  return (Write-FileSafely $Doc.Path ($utf8.GetBytes($Doc.Text)) $Doc.Bytes -Check $check)
}

# 끝 검증 — 장부에 든 우리 값이 실물에 그대로 섰나를 자리마다 한 칸씩 잰다. 받는 것: 장부 · 사용자 환경(레지스트리에서 읽은 표) · 홈
#   settings.json 자리. 내는 것 — 검증 칸 목록(@{ Name; Ok } · 못 잰 자리는 State unmeasured). 어긋난 칸은 자리와 이름만 댄다 — 값은 안 찍는다.
#   알린 사람 값(`seen`)은 우리 것이 아니라 안 잰다. 이 판에 장부를 못 썼으면(`$script:LedgerSaveWhy`) 그것도 한 칸이다.
function Get-PlantLedgerChecks($Ledger, [System.Collections.IDictionary]$UserEnv, [string]$HomeCfg) {
  $out = @()
  if ($Ledger.Why) { return @(@{ Name = "장부 (못 읽었다 — $($Ledger.Why) · $($Ledger.Path))"; Ok = $false }) }
  if ($script:LedgerSaveWhy) { $out += @{ Name = "장부 (이 판에 못 썼다 — $($script:LedgerSaveWhy) · $($Ledger.Path))"; Ok = $false } }
  $rows = @($Ledger.Rows | Where-Object { $_.By -cne 'seen' })
  $say = { param([string]$what, [int]$n, [string[]]$bad) "장부와 실물 — $what ($n 줄$(if ($bad.Count) { ' · 어긋남: ' + ($bad -join ' · ') }))" }
  $u = @($rows | Where-Object { $_.Place -ceq 'user-env' })
  if ($u.Count) {
    $bad = @($u | Where-Object { -not (Test-SameText $(if ($UserEnv.Contains($_.Name)) { [string]$UserEnv[$_.Name] } else { $null }) $_.Value) } | ForEach-Object { $_.Name })
    $out += @{ Name = (& $say '사용자 환경' $u.Count $bad); Ok = (-not $bad.Count) }
  }
  $s = @($rows | Where-Object { $_.Place -ceq 'settings-env' -or $_.Place -ceq 'settings' })
  if ($s.Count) {
    $cfg = $null; $why = ''
    try { $t = [IO.File]::ReadAllText($HomeCfg); $cfg = if ($t.Trim()) { $t | ConvertFrom-Json } else { [pscustomobject]@{} } } catch { $why = '못 읽었다' }
    $bad = @(foreach ($r in $s) {
      if ($why) { "$($r.Name)($why)"; continue }
      $c = Get-SettingsSlot $cfg $r.Place $r.Name
      if ($r.Name -ceq 'permissions.allow') { if (-not ($c -and $c.List -and (@($c.List) -ccontains $r.Value))) { $r.Name } }
      elseif ($c -is [hashtable] -or -not (Test-SameText $c $r.Value)) { $(if ($r.Place -ceq 'settings-env') { "env.$($r.Name)" } else { $r.Name }) }
    })
    $out += @{ Name = (& $say "홈 settings.json ($HomeCfg)" $s.Count $bad); Ok = (-not $bad.Count) }
  }
  foreach ($g in @($rows | Where-Object { $_.Place -ceq 'tool' } | Group-Object { $_.At })) {
    $at = ConvertFrom-LedgerAt $g.Name
    $toml = $at.Path -like '*.toml'
    $doc = Open-ToolDoc $at.Path $at.Under $toml @($g.Group | ForEach-Object { $_.Name })
    if ($doc.Why -and $toml -and $doc.Why.Contains('울타리')) {
      $out += @{ Name = "장부와 실물 — $($g.Name)"; State = 'unmeasured'; Probe = $TomlReadProbe; Why = (Format-ProbeWhy -2 $ProbeCap) }
      continue
    }
    $bad = @($g.Group | Where-Object { $c = Get-ToolDocValue $doc $_.Name; $c -is [hashtable] -or -not (Test-SameText $c $_.Value) } | ForEach-Object { $_.Name })
    $out += @{ Name = (& $say $g.Name $g.Count $bad); Ok = (-not $bad.Count) }
  }
  return $out
}

#endregion 장부

#region 환경 — 사용자 환경변수를 심고 걷고, 걷어도 되는 값인지 가리고(회사 키는 값으로), 회사 키를 이 사용자만 푸는 암호로 두고, PATH 를 태우고 사용자 PATH 에 덧대고(pip 사용자 자리를 묻는다), 워드의 PDF 변환 안내를 끈다

# ── 배선이 먼저다 ────────────────────────────────────────────────────────────────
# ⚠ **winget 이 심은 PATH 는 이 창에 안 걸린다** — 이 창이 winget 보다 먼저 떴다. 배선 없이 물으면 깔린 것도 「없음」이
#   나와 재설치로 새므로, 묻기 전에도 설치 직후에도 다시 태운다(`Update-RuntimePath`).
# 이 창의 PATH 앞에 그 자리를 끼운다 — 있는 폴더이고 아직 안 든 자리만. 여러 번 불려도 PATH 가 안 분다.
function Add-ToPath([string]$Dir) {
  if (-not $Dir) { return }
  # ⚠ **재기 전에 편다.** 레지스트리 읽기는 `REG_EXPAND_SZ` 만 펴 주므로 `REG_SZ` 로 앉은 PATH 는 `%USERPROFILE%\…` 를 원문
  #   그대로 넘기고, `Test-Path -LiteralPath` 는 그 글자를 그대로 찾아 멀쩡한 폴더를 조용히 버린다 — 「깔았는데 안 잡힌다」로만
  #   보인다.
  $Dir = [Environment]::ExpandEnvironmentVariables($Dir)
  # ⚠ **묻는 것부터 거절당하는 자리가 기계 PATH 에 섞여 있다** — SYSTEM 프로필 아래의 `…\WindowsApps` 는 일반 사용자의
  #   `Test-Path` 에 UnauthorizedAccessException 을 던지고, `Stop` 아래서 그것은 아무것도 묻기 전에 설치 전체를 죽인다. 못
  #   읽는 것과 없는 것은 답이 같다 — PATH 에 안 더한다.
  try { if (-not (Test-Path -LiteralPath $Dir -ErrorAction Stop)) { return } } catch { return }
  if (($env:PATH -split ';') -contains $Dir) { return }   # 여러 번 불려도 PATH 가 안 분다
  $env:PATH = "$Dir;$env:PATH"
}

# 이 창의 PATH 를 다시 태운다 — 기계 · 사용자 PATH(레지스트리)를 덧대고, 아는 설치 자리를 이름으로 덧댄다. 레지스트리가
#   본이고 이름 박은 목록은 보험이다 — 이 창이 뜬 뒤 깔린 것의 PATH 는 레지스트리에만 있다. 덧대기라 이 창이 들고 있던 자리는 안
#   잃는다.
function Update-RuntimePath {
  # ⚠ **순서가 뜻이다 — 레지스트리가 먼저, 이름이 나중.** `Add-ToPath` 는 앞에 끼우므로 나중에 부른 쪽이 앞에 선다 — 사용자
  #   PATH 의 `WindowsApps` 에 스토어행 파이썬 껍데기가 있어도 진짜 파이썬이 그 앞에 서야 한다.
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
  # npm 전역 자리 — 여기서는 이 창만 태운다. 새 터미널이 보게 사용자 PATH 에 심는 것은 마무리의 「사용자 범위 명령 자리」다.
  Add-ToPath $NpmGlobalDir
  # ⚠ **`agy` 자리는 여기 안 적는다** — winget 이 portable 을 깔며 제 자리를 사용자 PATH 에 넣고 위 레지스트리 읽기가 태운다.
  #   이름으로 박으면 저쪽이 자리를 옮길 때(폴더 이름에 소스 해시가 든다) 조용히 어긋나고, 확장이 따로 둔 사본(`~/.gemini/bin`)을
  #   박으면 그쪽이 앞에 서서 진짜 CLI 를 가린다.
}

# ── 영구 사용자 PATH — **새 터미널이 볼 자리에 한 자리를 덧댄다** (claude-config 결정 0143) ─────────────────
# 위 배선은 이 창의 `$env:PATH` 만 고친다 — 설치가 끝나면 그 자리는 사라진다. 이 설치가 깐 것을 새 터미널이 이름만으로
#   부르려면 그 자리가 사용자 PATH(`HKCU\Environment` 의 `Path`)에 서 있어야 한다. 아래 넷이 그 값을 읽고 · 재고 · 알리고 ·
#   덧댄다. 기계 PATH 는 안 쓴다 — 관리자 권한이 들고 그 PC 의 다른 사용자에게 번진다.

# 사용자 PATH 의 원문과 값의 꼴 — `@{ Raw; Kind }`, 값이 없으면 둘 다 `$null` 이다. 덧대는 손과 끝 검증이 같이 읽는다.
# ⚠ **글자 그대로 읽는다**(`DoNotExpandEnvironmentNames`). 펴서 읽은 것을 되쓰면 남의 `%USERPROFILE%\…` 가 지금 이 PC 의
#   경로로 굳는다.
function Get-UserPath([string]$SubKey = 'Environment') {
  $k = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($SubKey, $false)
  if (-not $k) { return @{ Raw = $null; Kind = $null } }
  try {
    if (@($k.GetValueNames()) -notcontains 'Path') { return @{ Raw = $null; Kind = $null } }
    return @{ Raw  = $k.GetValue('Path', $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
              Kind = $k.GetValueKind('Path') }
  } finally { $k.Close() }
}

# 목록(`;` 로 이은 PATH 글자)에 그 자리가 서 있나 — 자리마다 **펴서** 견준다. 대소문자를 안 가리고 앞뒤 빈칸과 끝의
#   `\` · `/` 를 뗀다 — `%APPDATA%\npm` 과 `C:\Users\…\AppData\Roaming\npm\` 은 같은 자리다.
function Test-PathListHas([string]$List, [string]$Dir) {
  $norm = { param([string]$p) [Environment]::ExpandEnvironmentVariables($p).Trim().TrimEnd('\', '/') }
  $want = & $norm $Dir
  if (-not $want) { return $false }
  foreach ($e in ($List -split ';')) {
    if ($e.Trim() -and ((& $norm $e) -ieq $want)) { return $true }
  }
  return $false
}

# 열린 프로그램에 「환경이 바뀌었다」를 알린다 — 탐색기가 이 알림을 받아 제 환경을 레지스트리에서 다시 짓고, 그 뒤 시작
#   메뉴 · 작업 표시줄에서 여는 터미널이 새 PATH 를 받는다. 레지스트리에 쓰기만 하면 다음 로그온까지 아무도 모른다.
# ⚠ **`[Environment]::SetEnvironmentVariable` 로 알리지 않는다** — 그 손은 알리기 앞에 값을 `REG_SZ` 로 되써서
#   `REG_EXPAND_SZ` 의 `%…%` 자리를 깬다. 알림만 따로 보내고, 멎은 창은 건너뛴다.
# 알렸으면 참이다. 못 알렸어도(정책이 `Add-Type` 을 막는 PC 등) 쓴 값은 다음 로그온부터 선다.
function Send-EnvChanged {
  $broadcast     = [IntPtr]0xffff   # HWND_BROADCAST — 모든 최상위 창
  $settingChange = 0x1a             # WM_SETTINGCHANGE
  $skipHung      = 0x2              # SMTO_ABORTIFHUNG — 멎은 창은 안 기다린다
  $waitMs        = 1000             # 창 하나를 기다리는 한도
  try {
    if (-not ('PAISetup.EnvNotice' -as [type])) {
      Add-Type -Namespace PAISetup -Name EnvNotice -MemberDefinition @'
[DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint msg, UIntPtr wParam, string lParam, uint flags, uint timeout, out UIntPtr result);
'@
    }
    $res = [UIntPtr]::Zero
    return ([PAISetup.EnvNotice]::SendMessageTimeout($broadcast, $settingChange, [UIntPtr]::Zero, 'Environment', $skipHung, $waitMs, [ref]$res) -ne [IntPtr]::Zero)
  } catch { return $false }
}

# 환경변수 하나의 한도 — 윈도우 API 가 받는 끝 널까지의 글자 수다. 사용자 PATH 에 덧댈 때 새 프로세스의 PATH 가 이것을 못 넘는다.
$EnvVarMax = 32767

# 사용자 PATH 끝에 그 자리를 **없을 때만** 덧댄다 — `@{ Did = 'kept' | 'added' | 'toolong' | 'failed'; Notified; Len; Err }`.
#   · 남의 자리는 한 글자도 안 바꾼다 — 원문 끝에 `;<자리>` 를 붙여 되쓸 뿐이라 빈 자리 · 겹친 자리 · 차례가 그대로다. 값이
#     없으면 지어 쓴다
#   · 편 경로로 심는다(`C:\Users\…\npm` — `%APPDATA%\npm` 이 아니다). 값이 `REG_SZ` 인 PC 에서도 서고, 로그온 때 `APPDATA` 가
#     서 있나에 기대지 않는다(결정 0143)
#   · 길이 — 새 프로세스가 받는 PATH 는 기계 PATH 와 사용자 PATH 를 이어 편 것이고 `$EnvVarMax` 를 못 넘는다. 덧대면 넘는 PC
#     에서는 안 쓰고 `toolong` 을 낸다
# ⚠ **값의 꼴을 지킨다** — `REG_EXPAND_SZ` 는 `REG_EXPAND_SZ` 로, `REG_SZ` 는 `REG_SZ` 로 되쓴다(바꾸면 남의 `%…%` 자리가
#   깨지거나 굳는다). 지을 때는 윈도우가 사용자 PATH 에 쓰는 꼴인 `REG_EXPAND_SZ` 로 짓는다.
# 쓰고 나면 알린다(`$Notify` — 기본은 `Send-EnvChanged`). `$SubKey` · `$MachinePath` · `$Notify` 는 검사가 버릴 자리와 대역을
#   넣는 손잡이다 — 설치는 기본값으로 부른다.
function Add-ToUserPath([string]$Dir,
                        [string]$SubKey = 'Environment',
                        [string]$MachinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine'),
                        [scriptblock]$Notify = { Send-EnvChanged }) {
  try {
    $entry = [Environment]::ExpandEnvironmentVariables($Dir).Trim().TrimEnd('\', '/')
    if (-not $entry) { throw '덧댈 자리가 비었다' }
    $now = Get-UserPath $SubKey
    $raw = [string]$now.Raw
    if (Test-PathListHas $raw $entry) { return @{ Did = 'kept' } }
    $new = if (-not $raw) { $entry } elseif ($raw.EndsWith(';')) { $raw + $entry } else { "$raw;$entry" }
    $len = [Environment]::ExpandEnvironmentVariables("$MachinePath;$new").Length
    if ($len -ge $EnvVarMax) { return @{ Did = 'toolong'; Len = $len } }
    $kind = if ($now.Kind) { $now.Kind } else { [Microsoft.Win32.RegistryValueKind]::ExpandString }
    $k = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($SubKey)
    try { $k.SetValue('Path', $new, $kind) } finally { $k.Close() }
    return @{ Did = 'added'; Notified = [bool](& $Notify) }
  } catch {
    return @{ Did = 'failed'; Err = $_ }
  }
}

# pip 가 사용자 자리에 까는 명령의 폴더 — 이 설치와 넘긴 훅이 쓰는 그 `python`(PATH 의 것)에 `sysconfig` 의 사용자 꼴(`nt_user`)로 묻는다.
#   `@{ State = yes · no · unmeasured; Dir; Probe; Why }`(`Add-UnmeasuredStep` 의 꼴) — python 이 이 창에 없으면 `no` 다. 띄우는 것은 python
#   하나이고 울타리를 두른다. 폴더가 아직 없어도 그 자리를 낸다 — 있나는 부르는 쪽이 본다.
#   글자는 인터프리터가 선 뒤의 출력이라 DRM 이 끼는 PC 에서도 안 잃는다(#32 · 결정 0144 — `Get-Ver` 곁말).
# ⚠ **작업 폴더의 같은 이름 모듈을 안 집는다** — `-c` 는 작업 폴더(`''`)를 `sys.path` 맨 앞에 둬, 그 폴더의 `sysconfig.py` 가 돈다.
#   `-I` 는 `PYTHONUSERBASE` 까지 버려 다른 답을 내고 `-P` 는 3.11 앞 판이 못 받으므로, 빈 자리를 지운 뒤 가져온다(`sys` 는 내장이라 안 집힌다).
$PipUserScriptsCode = "import sys;sys.path[:]=[p for p in sys.path if p];import sysconfig;print(sysconfig.get_path('scripts','nt_user'))"
function Measure-PipUserScripts {
  $runs = Measure-Runs 'python' '--version'
  if ($runs -eq 'no') { return @{ State = 'no'; Dir = ''; Probe = ''; Why = '' } }
  if ($runs -ne 'yes') { return @{ State = 'unmeasured'; Dir = ''; Probe = 'python --version'; Why = '' } }
  $probe = "python -c `"$PipUserScriptsCode`""
  $log = [IO.Path]::GetTempFileName()
  try {
    $rc = Invoke-LoggedCapped 'python' @('-c', $PipUserScriptsCode) $log $ProbeCap
    if ($rc -eq -2) { Add-ProbeOverflow $probe $ProbeCap; return @{ State = 'unmeasured'; Dir = ''; Probe = $probe; Why = '' } }
    if ($rc -ne 0)  { return @{ State = 'unmeasured'; Dir = ''; Probe = $probe; Why = (Format-ProbeWhy $rc $ProbeCap) } }
    $dir = ("$(@(Get-Content -LiteralPath $log -Encoding UTF8 -ErrorAction SilentlyContinue | Where-Object { "$_".Trim() })[0])").Trim()
    if (-not $dir)  { return @{ State = 'unmeasured'; Dir = ''; Probe = $probe; Why = '글자를 안 내' } }
    return @{ State = 'yes'; Dir = $dir; Probe = ''; Why = '' }
  } finally { Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue }
}

# 이 값이 로컬 프록시를 가리키나 — 이름이 아니라 값에서 판다: 절대 주소이고 갈래가 http(s) 이고 호스트가 루프백이면 참이다.
#   「무엇을 걷나」만 답한다 — 「누구 것인가」까지 합쳐 「걷어도 되나」를 내는 것은 `Test-OurProxyEntry` 이고, 걷는 자리는 그것만
#   부른다. 이름 표(`$Vars`)로는 안 가른다 — 그 표는 물을 것의 표라 값 파일이 더 실어 보낸 이름을 못 덮는다.
#   루프백이 근거인 까닭 — 이 설치기는 루프백이 아닌 주소에 프록시를 안 세우고, 루프백 게이트웨이 갈래는 사내에서만 선다
#   (「키와 값」의 「사외로 간 자리의 사내 잔재」 칸과 같은 근거).
#   못 읽는 글자를 예외에 맡기지 않는다 — `[Uri]'아무 글자'` 는 상대 주소로 서고 그 위의 `.IsLoopback` 은 5.1 에서 오류 없이
#   `$null` 을 준다. 절대 주소일 때만 묻는다.
# ⚠ **갈래(scheme)를 반드시 묻는다** — `[Uri]` 는 `C:\Users\…\node-ca.pem` 을 호스트가 빈 `file:///C:/…` 로 세워 `IsLoopback` 이
#   참이다. 안 물으면 `NODE_EXTRA_CA_CERTS` 같은 경로 값까지 프록시 주소로 읽어 CA 배선을 걷는다.
function Test-ProxyValue([string]$Value) {
  if (-not $Value) { return $false }
  $u = $null
  try { $u = [Uri]$Value } catch { return $false }
  if (-not ($u -and $u.IsAbsoluteUri)) { return $false }
  if ($u.Scheme -ne 'http' -and $u.Scheme -ne 'https') { return $false }
  return [bool]$u.IsLoopback
}

# 이 이름 · 값 쌍을 우리가 걷어도 되나 — 프록시 걷기가 묻는 것 전부가 여기 산다. 걷는 자리(사용자 환경 · `settings.json` 의
#   `env`)는 다 이 함수를 부른다 — 판정이 한 자리에 살아야 새 걷는 자리가 생겨도 울타리를 빠뜨리지 않는다.
# ⚠ **묻는 것이 둘이고 둘 다 서야 한다 — 값 하나로는 못 걷는다.**
#     · 무엇을 걷나 → 값이 루프백 http 인가 (`Test-ProxyValue`)
#     · 누구 것인가 → 값 파일이 그 이름을 드는가 (`$FromFile`)
#   값만 물으면 사람이 넣어 둔 `HTTP_PROXY = http://127.0.0.1:3128` 이나 제 로컬 개발 서버 주소가 사외 판정 한 번에 되돌릴
#   자리 없이 사라진다.
# 값 파일이 비면 아무것도 안 걷는다 — 우리가 실은 이름을 모르면 누구 것인지를 못 판다(`install.env` 없이 이 파일만 떼어 돌리는
#   갈래). 재는 자리(끝 검증)는 이 문을 안 부른다 — 그쪽은 틀려도 판정이 틀릴 뿐이고, 여기는 틀리면 값이 죽는다.
function Test-OurProxyEntry([string]$Name, [string]$Value, [hashtable]$FromFile) {
  if (-not $FromFile) { return $false }
  if (-not $FromFile.ContainsKey($Name)) { return $false }
  return (Test-ProxyValue $Value)
}

# 사내 전용 이름을 우리가 걷어도 되나 — 이름이 `$InsideOnly`(「준비」)에 들고 값 파일이 그 이름을 들면 참이다. 값 파일이 비면
#   거짓이다(`Test-OurProxyEntry` 와 같은 까닭).
function Test-OurInsideOnlyEntry([string]$Name, [hashtable]$FromFile) {
  if (-not $FromFile) { return $false }
  if ($InsideOnly -notcontains $Name) { return $false }
  return $FromFile.ContainsKey($Name)
}

# 이 게이트웨이 주소가 우리 것인가 — 받는 것: 주소 · 우리 주소들(`$OurGatewayUrls` · 「키와 값」의 「회사 키」 칸이 모은다). 그 가운데
#   하나와 글자까지 같을 때만 참이다. ⚠ 루프백이라는 것은 근거가 아니다 — 사람이 제 로컬 프록시(LiteLLM 따위)와 그 키를 같은 이름에
#   두므로, 루프백을 우리 것으로 보면 사외에서 그 짝을 걷고 그 키를 회사 키로 세워 사내 판이 회사 키 이름 셋에 심는다.
#   사용자 환경(「사외로 간 자리의 사내 잔재」)과 홈 `settings.json` 의 `env`(「회사 키」 칸 · 「Claude 홈 설정」)가 이 함수 하나로 묻는다 —
#   판정이 두 자리에 살면 한쪽만 낡는다.
function Test-OurGatewayUrl([string]$Value, [string[]]$OurUrls) {
  if (-not $Value) { return $false }
  return [bool](@($OurUrls | Where-Object { $_ -and $_ -ceq $Value }).Count)
}

# 회사 키 — 이 판이 회사 키로 아는 값(`$script:CompanyKeys`)을 모으고, 어떤 값이 그 가운데 하나인가를 묻는다. 회사 키는 남이 같은 값을
#   가질 수 없어, 값이 같다는 것이 곧 우리 것이라는 근거다 — 걷는 자리(사용자 환경 · 홈 `settings.json` 의 `env`)는 다 이 물음
#   하나로 가른다. 무엇을 아는 값으로 세우나는 「키와 값」의 「회사 키」 칸이 든다. 빈 값은 안 세운다 · 글자까지 같아야 같다.
function Add-CompanyKey([string]$Key) {
  if (-not $Key) { return }
  if ($null -eq $script:CompanyKeys) { $script:CompanyKeys = New-Object System.Collections.Generic.List[string] }
  if (-not $script:CompanyKeys.Contains($Key)) { $script:CompanyKeys.Add($Key) }
}
function Test-CompanyKey([string]$Value) {
  return [bool]($Value -and $null -ne $script:CompanyKeys -and $script:CompanyKeys.Contains($Value))
}

# 안티그래비티 설정의 인증 방식 줄이 우리가 심은 회사 연결인가 — 받는 것: 그 설정을 읽은 것(`ConvertFrom-Json` 의 결과 · 빈 파일이면
#   $null). 내는 것: 회사 연결이면 $true. 값이 회사 값(`$AgyProvider`)이라는 것만으로는 안 선다 — 그 값은 agy 의 API 키 갈래라 제 Gemini
#   키를 둔 사람도 같은 줄을 쓴다(claude-config 결정 0085). 그래서 키가 가른다: 남은 `GEMINI_API_KEY`(사용자 환경 · 없으면 머신 환경)가
#   회사 키이거나(`Test-CompanyKey`) 아예 없으면 회사 연결이고, 다른 키면 사람의 갈래다. 사외 갈래가 걷기 앞에서, 끝 검증이 같은 자로
#   묻는다 — 「사외로 간 자리의 사내 잔재」가 회사 키 사본을 걷은 뒤라야 「남은」 키다.
function Test-AgyCompanyLink($Settings) {
  if (-not $Settings) { return $false }
  $mp = $Settings.PSObject.Properties['modelProvider']
  if (-not ($mp -and $mp.Value -is [string] -and $mp.Value -ceq $AgyProvider)) { return $false }
  $k = [Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')
  if (-not $k) { $k = [Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'Machine') }
  return [bool]((-not $k) -or (Test-CompanyKey $k))
}

# 회사 키 덩이의 꼴 — 이 사용자만 푸는 Windows DPAPI(`ProtectedData` · CurrentUser)로 싸거나(`-Protect`) 푼다. 쓰는 손과 읽는 손이 이
#   함수 하나로 같은 꼴을 쓴다 — 목적 글(entropy)이 두 자리에 살면 한쪽만 바뀐 날 덩이가 안 풀린다. 못 풀면 던진다.
function Convert-CompanyKeyBlob([byte[]]$Bytes, [switch]$Protect) {
  Add-Type -AssemblyName System.Security
  $purpose = [Text.Encoding]::UTF8.GetBytes('PAISetup company key')
  $scope = [Security.Cryptography.DataProtectionScope]::CurrentUser
  if ($Protect) { return , [Security.Cryptography.ProtectedData]::Protect($Bytes, $purpose, $scope) }
  return , [Security.Cryptography.ProtectedData]::Unprotect($Bytes, $purpose, $scope)
}

# 회사 키 덩이를 읽는다 — 받는 것: 덩이 자리. 내는 것: @{ Key = <푼 키 · 없으면 ''>; Why = <못 푼 까닭 · 풀었거나 없으면 ''> }.
#   다른 사용자 · 다른 PC 의 덩이나 깨진 덩이처럼 **못 푸는 덩이와 풀어도 키가 아닌 덩이는 지운다** — 남기면 판마다 같은 줄이 서고
#   다시 쓸 자리도 막힌다. 파일을 못 읽은 것(잠김)은 안 지우고 까닭만 낸다. 지우기도 못 하면 넘어간다. 평문 바이트는 다 쓰면 지운다.
function Read-CompanyKeyBlob([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return @{ Key = ''; Why = '' } }
  $plain = $null
  try {
    $enc = [IO.File]::ReadAllBytes($Path)
  } catch { return @{ Key = ''; Why = (Say-Why $_) } }
  try {
    $plain = Convert-CompanyKeyBlob $enc
    $key = [Text.Encoding]::UTF8.GetString($plain)
    # 키가 아닌 평문 — 빈 것 · 빈칸뿐인 것 · 앞에 BOM(U+FEFF)이 붙은 것. ⚠ BOM 은 순서 견줌(ordinal)으로 찾는다 — 문화권 견줌은 그
    #   글자를 건너뛰어 아무 글에나 「붙었다」고 답하고, `-ceq` 도 `<BOM>키` 를 키와 같다고 본다.
    if ($key.Trim().Length -and -not $key.StartsWith([string][char]0xFEFF, [StringComparison]::Ordinal)) { return @{ Key = $key; Why = '' } }
    $why = '키가 아닌 덩이(비었거나 빈칸뿐이거나 앞에 BOM 이 붙었다)'
  } catch { $why = Say-Why $_ } finally { if ($plain) { [Array]::Clear($plain, 0, $plain.Length) } }
  try { Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue } catch { }
  return @{ Key = ''; Why = $why }
}

# 회사 키 덩이를 이 키로 맞춘다 — 받는 것: 덩이 표(`Read-CompanyKeyBlob` 이 낸 것 · 쓰면 그 `Key` 를 고친다) · 덩이 자리 · 키 · 쓴 줄의
#   덧말. 덩이가 이미 그 키면 안 쓴다. 디스크에 닿는 것은 암호문뿐이다 — 곁 파일(`.new`)에 쓴 뒤 갈아 끼운다. 내는 것: 맞췄으면 $true.
#   진 것은 노란 줄이다 — 키는 아직 사용자 환경에 있어 이 판은 안 진다. 진 판의 곁 파일 치우기도 못 하면 넘어간다(다음 판이 덮어쓴다).
# ⚠ **갈아 끼우기의 곁 사본 자리는 `[NullString]::Value` 다** — 5.1 은 .NET 의 `string` 자리에 넘긴 `$null` 을 빈 글로 바꿔,
#   `File.Replace` 가 「The path is not of a legal form」으로 진다. 그러면 덩이가 처음 쓴 키에 묶여 새 키를 못 받는다.
function Save-CompanyKeyBlob([hashtable]$Blob, [string]$Path, [string]$Key, [string]$Said) {
  if (-not $Key) { return $false }
  if ($Key -ceq $Blob.Key) { return $true }
  $plain = $null
  $side = "$Path.new"
  try {
    $plain = [Text.Encoding]::UTF8.GetBytes($Key)
    $enc = Convert-CompanyKeyBlob $plain -Protect
    New-Item -ItemType Directory -Path (Split-Path $Path -Parent) -Force | Out-Null
    [IO.File]::WriteAllBytes($side, $enc)
    if (Test-Path -LiteralPath $Path) { [IO.File]::Replace($side, $Path, [NullString]::Value) } else { [IO.File]::Move($side, $Path) }
    $Blob.Key = $Key
    Write-Host "  회사 키 — $Said ($Path)" -ForegroundColor Green
    return $true
  } catch {
    $err = $_
    try { Remove-Item -LiteralPath $side -Force -ErrorAction SilentlyContinue } catch { }
    Write-Host "  ! 회사 키를 설치기 폴더에 못 두었다 — $(Say-Why $err) · 사외에서 걷히면 사내로 돌아와 다시 넣는다" -ForegroundColor Yellow
    return $false
  } finally { if ($plain) { [Array]::Clear($plain, 0, $plain.Length) } }
}

# 사용자 환경변수로 심는다 — `HKCU\Environment` 에 써서 새로 뜨는 프로세스부터 걸리고, 이 창에도 심어 끝 검증이 방금 넣은 값을
#   본다. 심은 것은 `$script:Planted` 에 모이고, 진 것은 빨간 줄과 `$Fails` 다.
#   `setx` 를 안 쓴다 — 값이 1024자를 넘으면 못 쓰는데 토큰은 그보다 길 수 있다. .NET 쪽에는 그 한도가 없고 설정 바뀜 알림도 돈다.
function Plant-Var([string]$Name, [string]$Value) {
  try {
    [Environment]::SetEnvironmentVariable($Name, $Value, 'User')
    Set-Item -Path "Env:$Name" -Value $Value
    # 자리가 그러라고 하면 「Claude 홈 설정」 걸음이 이 표의 값을 홈 설정에도 민다 — 한 번 정한 값을 두 자리로 민다(키와 맡기기
    #   러너 값은 빼고 — 그 걸음의 `env` 칸).
    $script:Planted[$Name] = $Value
    Write-Host "  $Name — 심었다" -ForegroundColor Green
  } catch {
    Write-Host "  ! $Name 심기 실패 — $(Say-Why $_)" -ForegroundColor Red
    $script:Fails.Add("$Name 심기")
  }
}

# 사용자 환경변수를 걷는다(이 창에서도) — 받는 것: 이름 · 걷은 줄에 붙일 까닭(없으면 사외라 안 쓴다). 진 것은 빨간 줄과 `$Fails` 다.
function Remove-UserVar([string]$Name, [string]$Why = '사외라 안 쓴다') {
  try {
    [Environment]::SetEnvironmentVariable($Name, $null, 'User')
    Remove-Item -Path "Env:$Name" -ErrorAction SilentlyContinue   # 이 창에서도 걷는다 (Plant-Var 와 짝)
    Write-Host "  $Name — 걷었다 ($Why)" -ForegroundColor Green
  } catch {
    Write-Host "  ! $Name 걷기 실패 — $(Say-Why $_)" -ForegroundColor Red
    $script:Fails.Add("$Name 걷기")
  }
}

# 사용자 환경의 이 이름이 회사 키를 들면 걷는다 — 우리 것인가는 이름이 아니라 값으로 가른다(`Test-CompanyKey`). 다른 값은 사람이 둔
#   것이라 두고 그 이름을 댄다. 받는 것: 이름 · 걷은 줄에 붙일 까닭. 진 것은 `Remove-UserVar` 가 든다.
function Remove-CompanyKeyCopy([string]$Name, [string]$Why) {
  $cur = [Environment]::GetEnvironmentVariable($Name, 'User')
  if (-not $cur) { return }
  if (Test-CompanyKey $cur) { Remove-UserVar $Name $Why }
  else { Write-Host "  $Name — 우리 키가 아니다 · 그대로 둔다" }
}

# 다른 자리의 값을 걷는다 — 받는 것: 자리마다 `[ordered]@{<이름> = <값>}` 인 표 · 이 자리. 이 자리 표에 없는 이름이 다른 자리
#   표의 값과 글자까지 같게 사용자 환경에 남았을 때만 걷는다 — 자리를 옮긴 PC(노트북)에 앞 자리의 값이 남으면 러너가 안 잰
#   길로 나간다. 값이 다르면 사람이 고친 것이라 안 건드린다. 진 것은 빨간 줄과 `$Fails` 다.
function Remove-OtherSiteVars([hashtable]$BySite, [string]$Site) {
  foreach ($s in $BySite.Keys) {
    if ($s -eq $Site) { continue }
    foreach ($k in $BySite[$s].Keys) {
      if ($BySite[$Site].Contains($k)) { continue }
      if ([Environment]::GetEnvironmentVariable($k, 'User') -ne $BySite[$s][$k]) { continue }
      try {
        [Environment]::SetEnvironmentVariable($k, $null, 'User')
        Remove-Item -Path "Env:$k" -ErrorAction SilentlyContinue   # 이 창에서도 걷는다 (Plant-Var 와 짝)
        Write-Host "  $k — 걷었다 (다른 자리의 값)" -ForegroundColor Green
      } catch {
        Write-Host "  ! $k 걷기 실패 — $(Say-Why $_)" -ForegroundColor Red
        $script:Fails.Add("$k 걷기")
      }
    }
  }
}

# 이번 판이 세우지 않는 맡기기의 러너 값을 걷는다 — 받는 것: 자리마다 `[ordered]@{<이름> = <값>}` 인 표 · 걷은 줄에 붙일 까닭. 어느
#   자리 표의 그 이름 값과 글자까지 같게 사용자 환경에 남았을 때만 걷고, 다른 값은 사람이 둔 것이라 두고 그 이름을 댄다. 진 것은
#   `Remove-UserVar` 가 든다.
function Remove-OurRunnerVars([hashtable]$BySite, [string]$Why) {
  $vals = Get-SiteValues @(, $BySite)
  foreach ($k in @($vals.Keys | Sort-Object)) {
    $cur = [Environment]::GetEnvironmentVariable($k, 'User')
    if (-not $cur) { continue }
    if ($vals[$k] -ccontains $cur) { Remove-UserVar $k $Why }
    else { Write-Host "  $k — 우리 값이 아니다 · 그대로 둔다" }
  }
}

# ── 워드의 PDF 변환 안내 — 스킬 `drm-office-read` 의 숨은 워드가 그 창에 갇히지 않게 ─────────────
# 워드로 PDF 를 열면 「PDF 를 편집할 수 있는 문서로 바꾼다」 안내창이 뜬다. 그 스킬은 워드를 숨겨 띄우므로 창이 아무도
#   못 누르는 자리에 떠, 워드가 멈춘 채 RPC 가 끊긴다(`0x800706BE`). `DisplayAlerts` · `ConfirmConversions` 로는 이 창이
#   안 눌리고, 끄는 것은 창의 「이 메시지를 다시 표시 안 함」이 쓰는 값 하나다(claude-config #143 · 판 16.0).
# 사람이 PDF 를 워드로 열 때도 그 안내가 안 뜨게 되므로, 심는 자리가 설치 기록에 그 뜻을 한 줄로 밝힌다. 값 자리
#   (`$WordPdfQuiet`)는 「키와 값」 걸음이 들고, 심는 손과 끝 검증이 그 한 자리를 본다.

# 깔린 워드의 판 목록(`16.0` 따위) — 오피스가 HKCU 에 판마다 설정을 두는 자리의 이름이고, 워드가 제 `Version` 으로 내는 값이기도
#   하다(스킬이 그 값으로 이 자리를 찾는다). 뿌리 넷(64비트 · 32비트 `WOW6432Node` · 클릭 투 런의 가상 레지스트리 둘)에서 판마다
#   `Word\InstallRoot` 의 `Path` 를 읽고, 그 자리에 WINWORD.EXE 가 있는 판만 센다 — 지운 오피스는 판 키를 남긴다.
# ⚠ **`Word.Application.N` 이름으로 세지 않는다** — 요즘 오피스도 옛 이름 `Word.Application.8` 을 같이 둔다.
function Get-WordVersions([string[]]$Bases = @(
    'HKLM:\SOFTWARE\Microsoft\Office',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Office',
    'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\REGISTRY\MACHINE\Software\Microsoft\Office',
    'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\REGISTRY\MACHINE\Software\Wow6432Node\Microsoft\Office')) {
  $found = @()
  foreach ($b in $Bases) {
    foreach ($k in @(Get-ChildItem -LiteralPath $b -ErrorAction SilentlyContinue)) {
      if ($k.PSChildName -notmatch '^\d+\.\d+$') { continue }
      $dir = $null
      try { $dir = [string](Get-ItemProperty -LiteralPath (Join-Path $k.PSPath 'Word\InstallRoot') -Name Path -ErrorAction Stop).Path } catch { continue }
      if ($dir -and (Test-Path -LiteralPath (Join-Path $dir 'WINWORD.EXE') -PathType Leaf)) { $found += $k.PSChildName }
    }
  }
  @($found | Sort-Object -Unique)
}

# 한 판의 값 자리와 지금 값 — 심는 손과 재는 손이 같이 쓴다. 값이 없으면 `Now` 가 `$null` 이다.
function Get-WordPdfQuietAt([string]$Version) {
  $key = Join-Path $WordPdfQuiet.Office "$Version\Word\Options"
  $now = $null
  try { $now = (Get-ItemProperty -LiteralPath $key -Name $WordPdfQuiet.Name -ErrorAction Stop).($WordPdfQuiet.Name) } catch { }
  @{ Key = $key; Now = $now }
}

# 판마다 끈다 — 판마다 `@{ Version; Did = 'set' | 'kept' | 'failed'; Err }` 하나를 돌려준다. 판이 없으면 아무것도 안 쓴다.
#   1 이면 안 쓰고(기록이 「이미 꺼져 있다」를 참으로 말한다), 없거나 다른 값이면 1(DWORD)로 둔다 — 1 이 아닌 값은 모두 「안내가
#   뜬다」이고, 0 은 대개 갓 선 기본값이다.
# ⚠ **키는 없을 때만 짓는다** — `New-Item -Force` 는 이미 있는 레지스트리 키를 비우고 다시 지어 그 자리의 워드 설정이 다 날아간다.
#   없는 윗 키는 같은 줄이 같이 짓는다.
function Set-WordPdfQuiet([string[]]$Versions) {
  foreach ($v in $Versions) {
    $at = Get-WordPdfQuietAt $v
    if ($at.Now -eq 1) { @{ Version = $v; Did = 'kept' }; continue }
    try {
      if (-not (Test-Path -LiteralPath $at.Key)) { New-Item -Path $at.Key -Force | Out-Null }
      New-ItemProperty -LiteralPath $at.Key -Name $WordPdfQuiet.Name -PropertyType DWord -Value 1 -Force | Out-Null
      @{ Version = $v; Did = 'set' }
    } catch {
      @{ Version = $v; Did = 'failed'; Err = $_ }
    }
  }
}

# 끝 검증의 한 줄 — 판마다 지금 값을 되읽어 다 1 이면 [O]. **판이 없으면 줄을 안 낸다** — 워드가 없는 PC 는 고칠 것이
#   없는데, [X] 로 찍으면 멀쩡한 설치가 빨갛게 끝난다.
function Get-WordPdfQuietCheck([string[]]$Versions) {
  if (-not $Versions -or -not $Versions.Count) { return }
  $on = @($Versions | Where-Object { (Get-WordPdfQuietAt $_).Now -ne 1 })
  @{ Name = ("워드 PDF 변환 안내 끔 ($($WordPdfQuiet.Name) = 1 · 워드 $($Versions -join ' · ')" +
             $(if ($on.Count) { ' — 1 이 아닌 판: ' + ($on -join ' · ') } else { '' }) + ')')
     Ok   = ($on.Count -eq 0) }
}

#endregion 환경

#region 망 — 닿는지 묻고, 큰 것을 받고, 이 PC 가 믿는 TLS 뿌리를 Node 에 잇는다

# `호스트:포트` 에 TCP 로 물어 한도 안에 붙으면 참, 못 붙으면 거짓이다. 꼴이 `호스트:포트` 가 아니면 `$null` 이다 — 못 붙은 것과 못 묻는
#   것은 다른 명제라, 자리를 가르는 자(`Measure-Site`)가 뒤엣것을 「사외」로 읽지 않게 갈라 낸다. 호스트는 이름이나 IPv4 이고(ASCII
#   글자 · 숫자 · `.` · `-` · `_`) 포트는 1–65535 다. `-ShapeOnly` 는 망에 안 묻고 꼴만 잰다 — 꼴이 맞으면 참이다.
# 꼴의 진본은 이 함수 하나다 — 배포본을 뽑는 자(claude-config `scripts/build-dist.sh`)가 이 함수를 `-ShapeOnly` 로 떼어 불러 틀린
#   `#site-probe` 가 실려 나가지 않게 막는다. 자동 실행 몸통도 이름으로 떼어 쓰므로 다른 함수에 기대지 않는다.
# ⚠ **글자 묶음은 `[0-9]` · `[A-Za-z]` 로 쓰고 대소문자를 가려 맞춘다(`-cnotmatch`).** `\d` 는 전각 숫자(`８０`)도 물어 아래 `[int]` 가
#   잡히지 않는 오류로 몸통을 죽이고, 대소문자를 안 가리는 맞춤은 `[A-Za-z]` 에 켈빈 기호(U+212A) 같은 글자를 들인다.
# ⚠ **이름으로 안 가른다** — DNS 는 사외에서도 사내 호스트를 사내 IP 로 풀어 주고 포트만 안 열린다(결정 0026).
function Test-Reach([string]$HostPort, [int]$TimeoutMs = 3000, [switch]$ShapeOnly) {
  if ($HostPort -cnotmatch '^([A-Za-z0-9._-]+):([0-9]{1,5})$') { return $null }
  $h = $Matches[1]; $p = [int]$Matches[2]
  if ($p -lt 1 -or $p -gt 65535) { return $null }
  if ($ShapeOnly) { return $true }
  $c = New-Object Net.Sockets.TcpClient
  try {
    if ($c.ConnectAsync($h, $p).Wait($TimeoutMs)) { return $c.Connected }
    return $false
  } catch { return $false } finally { $c.Dispose() }
}

# 이 PC 의 자리 — 짐의 `#site-probe` 에 닿으면 `inside`, 안 닿으면 `outside` 다. 자리는 이 둘뿐이고 재는 자는 `Test-Reach` 하나다 —
#   몸통(「준비」의 「자리」 칸) · 설치 창(`-Describe` 의 `site|` 줄) · 자동 실행(엔진에서 이 함수를 떼어 쓴다)이 다 이 손을 지난다.
# 받는 것 — 프로브 값(`Read-Directive … 'site-probe'` 의 답 · 없으면 빈 값). 내는 것 — @{ Site = inside · outside · `$null`; Why = 못
#   정한 까닭 }. 프로브가 없거나 꼴이 틀리면 `Site` 가 `$null` 이다 — 부르는 쪽은 그것을 빨강으로 말하고 어느 갈래로도 안 간다. 안 재고
#   한 갈래를 고르면 같은 PC 가 회차마다 다른 자리로 돌아 키와 주소를 잃는다(PAISetup #46).
function Measure-Site([string]$Probe) {
  if (-not $Probe) { return @{ Site = $null; Why = '짐의 값 파일(install.env)에 #site-probe 가 없다' } }
  $r = Test-Reach $Probe
  if ($null -eq $r) { return @{ Site = $null; Why = "짐의 값 파일의 #site-probe 가 호스트:포트 꼴이 아니다 ($Probe)" } }
  return @{ Site = $(if ($r) { 'inside' } else { 'outside' }); Why = $null }
}

# 이 자리에서 VS Code 가 필수인가 — 사내는 VS Code 가 주 무대라 참이다. 「준비」의 「자리」 칸이 참이면 VS Code 칸을 꺼도 깔고(기록은
#   사람이 고른 값 그대로 둔다), `-Describe` 가 `vscode|required` 로 내 설치 창의 칸을 켠 채 잠근다(PAISetup #46 ④).
function Test-VsCodeRequired([string]$Site) {
  return ($Site -eq 'inside')
}

# 한 호스트(443)에 TLS 를 걸어 @{ Root = 체인의 뿌리; Trusted = 윈도우가 그 체인을 믿나 } 를 낸다. 못 닿으면 `$null` — 못 닿은
#   것과 못 믿는 것은 다른 명제라 부르는 쪽이 갈라 쓴다.
#   검증 콜백은 무조건 참을 낸다 — 여기는 신뢰를 정하는 자리가 아니라 상대가 내미는 것을 보는 자리다(거절하면 볼 것도 못 본다).
#   폐기 목록(CRL)을 못 물어본 것은 미신뢰가 아니라 그 갈래만 덜고 판정한다.
# ⚠ **믿나는 `Build()` 로 묻고 저장소(`Cert:\...\Root`)를 훑지 않는다** — 윈도우는 루트 CA 를 필요할 때 받아 오므로 저장소는
#   상태가 아니라 캐시라, 맨바닥 기계에서 멀쩡히 신뢰되는 공개 CA 를 「모르는 CA」로 찍는다.
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

# 인증서 파일 한 장에서 든 것을 다 꺼내 목록으로 낸다(못 읽으면 빈 목록) — PEM 묶음(여러 장)과 `.cer`(한 장) 둘 다 받는다.
#   확장자가 아니라 바이트로 꼴을 가른다 — `.cer` 안에 PEM 이 든 일이 흔하다.
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
# 윈도우 신뢰 저장소가 이 PC 의 신뢰 진본인데 Node 는 제가 안고 다니는 CA 목록만 본다 — TLS 를 가로채는 망에서 브라우저 · git ·
#   파워셸은 멀쩡한데 `code --install-extension` 과 `npm` 만 죽는다. Node 에게 알려주는 자리가 `NODE_EXTRA_CA_CERTS` 하나다
#   (런타임마다 제 신뢰 목록을 드는 같은 병의 Node 갈래 — 파이썬은 `truststore` 가 든다 · 결정 0016, git 은
#   `http.sslBackend=schannel` 로 저장소를 본다).
# 검증을 끄지 않는다 — 그 변수는 기본 목록에 더한다. VS Code 의 `http.proxyStrictSSL: false` 는 검증 자체를 없애므로 안 쓴다.
# 판정은 사건(「가로채였나」)이 아니라 상태로 한다 — 잰 뿌리를 이 PC 가 이미 신뢰하나. 신뢰하면 담고, 아니면 안 담고 이름을 대
#   마주친 아무 가로채기나 믿는 자가 되지 않는다. 가로채인 것만 골라 담지 않는다 — Node 가 이미 아는 것을 여기서 못 재고, 더
#   담아도 무해하다(더하는 목록이다).
# 받는 것 — `$TlsHosts` · 값 파일의 `#corp-ca`. 내는 것 — 홈의 `node-ca.pem` 과 사용자 환경변수 `NODE_EXTRA_CA_CERTS`. 진 것은
#   빨간 줄과 `$Fails` 다.
function Wire-NodeTrust {
  # 신뢰의 근거는 둘이고 둘 다 이 PC 밖에서 정해진 것이다 — 설치기가 짓지 않는다.
  #   ① 윈도우가 그 체인을 믿는가 — `Get-ChainRoot` 의 `Trusted`
  #   ② 값 파일이 `#corp-ca` 로 가리킨 파일 — 회사가 배포 묶음에 실어 보낸 것. 맨바닥 VDI 는 회사 CA 를 아직 안 받은 채로 떠, ①만
  #      보면 「모르는 CA」로 멈추고 맨바닥을 못 세운다
  $corp = @()
  $corpRel = Read-Directive $script:DistEnvFile 'corp-ca'
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
      # 값 파일이 가리켰는데 없는 것은 배포가 빠뜨린 것이고, 그 빠짐은 CA 가 없는 PC 에서만 드러난다 — 빨강으로 말한다.
      Write-Host "  ! 값 파일이 가리킨 회사 CA 가 없다 — $corpPath" -ForegroundColor Red
      $script:Fails.Add('Node 신뢰 배선 (회사 CA 가 없다)')
    }
  }

  # 실어 온 것의 지문 — 윈도우가 아직 모르는 CA 라도 이것에 있으면 근거가 선다.
  $corpTp = @{}
  foreach ($c in $corp) { $corpTp[$c.Thumbprint] = $true }

  # 실어 보낸 것은 잰 뿌리와 안 맞아도 담는다 — 그 파일이 그 자리의 진본이고, 다시 거르면 판단이 두 자리에 산다.
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
    # 여기서 안 묻는다 — 이 PC 가 모르는 CA 를 신뢰할지는 설치기가 낼 판단이 아니다.
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

  # PEM 으로 뽑는다. `BEGIN` 앞의 글자는 파서가 무시하므로 무엇인지 적어 둔다 — 이 파일을 연 사람이 왜 여기 있는지 알게.
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

  # ⚠ **BOM 을 안 찍는다** — PEM 파서는 바이트로 읽어, 앞에 BOM 이 붙으면 첫 줄이 어긋난다.
  $target = Join-Path $homeDir 'node-ca.pem'
  # 갈아 끼워 쓴다(`Write-FileSafely`) — 쓰다 멎어도 반쪽 묶음이 남지 않는다. 같으면 안 쓴다.
  $pemOld = $null
  try { if (Test-Path -LiteralPath $target -PathType Leaf) { $pemOld = [IO.File]::ReadAllBytes($target) } } catch { }
  $pemWrote = Write-FileSafely $target ((New-Object Text.UTF8Encoding($false)).GetBytes($sb.ToString())) $pemOld
  if ($pemWrote.Did -ceq 'linked') { Write-Host "  ! CA 묶음 — $($pemWrote.Why) · 안 심었다 ($target)" -ForegroundColor Yellow; return }
  if ($pemWrote.Did -cne 'written' -and $pemWrote.Did -cne 'same') {
    Write-Host "  ! CA 묶음을 못 썼다 — $($pemWrote.Why)" -ForegroundColor Red
    $script:Fails.Add('Node 신뢰 배선 (파일 쓰기)')
    return
  }

  # ⚠ **남의 파일을 안 덮는다** — Node 는 이 변수 하나만 보므로 덮으면 저쪽 신뢰가 조용히 사라진다. 레지스트리에서 읽는다 —
  #   이 창의 값은 우리가 방금 넣었을 수 있다.
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

# 큰 것을 받는 자 — 주소를 `$OutFile` 로 흘려 쓰고, 가면서 10% 마다(크기를 안 주면 25MB 마다) 한 줄씩 말한다. 실패는 던진다.
#   `Invoke-WebRequest` 를 안 쓰는 까닭 셋 — 이 자리는 수백 MB 다:
#   · 몸통을 메모리에 물고 있다가 쓴다(5.1) — 그렇게 받으면 그 자체로 느리다
#   · 진행을 말할 자리가 없다 — 막대를 켜면 몇 배 느려지고, 끄면 몇 분이 통째로 조용하다(사람이 창을 닫는 시간이다)
#   · `ReadWriteTimeout` 손잡이가 없다 — `-TimeoutSec` 는 응답 머리가 오기까지만 들어, 느린 링크에서 몸통을 읽다 진다
#   두 시계를 다 못박는다 — `Timeout` 은 프록시가 파일을 통째로 받아 검사하고 머리를 내주기까지, `ReadWriteTimeout` 은 그다음 한 번
#   읽는 사이다.
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
      # ⚠ **줄로 말한다 — 막대가 아니라.** 화면 껍데기가 stdout 을 줄 단위로 읽어, 한 줄 안에서 덮어쓰는 꼴은 그쪽에 한 글자도
      #   안 닿는다.
      $buf = New-Object byte[] 1048576
      $got = 0.0
      $mark = 0
      while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) {
        $out.Write($buf, 0, $n)
        $got += $n
        if ($total -gt 0) {
          # 내림으로 센다 — `[int]` 는 반올림해 99.6% 가 곁의 MB 와 안 맞는 100% 로 찍힌다.
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
    # 끝난 줄을 따로 댄다 — 몫을 내림으로 세니 마지막 토막에서는 100% 가 안 뜬다. 마지막 줄은 받은 양으로 말한다.
    Write-Host ('        다 받았다 — {0:N1} MB' -f ($got / 1MB))
  } finally { $res.Close() }
}

#endregion 망

#region 깔기 — winget 을 되살리고, 프로그램 · VS Code 확장 · CLI · VC++ 런타임이 있나 묻고 깔고 올린다

# ── winget 을 되살려 본다 — 없다고 바로 물러나기 전에 ────────────────────────────
# 되살아나 불리면 `$true`, 세 갈래가 다 지면 무엇을 시도했고 무엇에 걸렸는지 적고 `$false` 를 낸다(정책이 사이드로딩을 막은
#   기계는 우리가 넘을 자리가 아니다). 갈래는 싼 것부터다:
#   ① 이 프로필에 다시 등록 — 가장 흔한 자리는 「안 깔림」이 아니라 「이 프로필에 등록 안 됨」이다. winget 은 AppX(App
#      Installer)라 기계에는 프로비저닝돼 있어도 사용자 프로필에는 등록이 안 될 수 있고, 비영속 VDI 는 로그인마다 늘 그 꼴이다.
#      네트워크 없이 선다
#   ② 마이크로소프트가 문서에 적어 둔 길 — PSGallery 의 WinGet 모듈로 `Repair-WinGetPackageManager` 를 돌린다(사내 VDI 에서 선다)
#   ③ GitHub 릴리스에서 내려받기 — 사내 환경 문서가 GitHub HTTPS 는 열려 있다고 적는다
function Restore-Winget {
  Write-Host '  winget 이 없다 — 되살려 본다.' -ForegroundColor Yellow
  # ⚠ **TLS 1.2 는 함수 머리에서 세운다 — 세 갈래가 다 HTTPS 를 탄다.** 5.1 의 기본은 기계에 따라 아직 SSL3/TLS1.0 이고 PSGallery
  #   는 TLS 1.2 아래로 안 받아, 한 갈래에서만 세우면 다른 갈래가 「망이 죽었다」로 진다. 덮어쓰지 않고 더한다 — 대입하면 그
  #   기계가 쓰던 더 높은 판(TLS 1.3)을 지운다.
  try {
    [Net.ServicePointManager]::SecurityProtocol =
      [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
  } catch { }

  # 진행 막대도 같은 까닭으로 함수 머리에서 끈다 — 5.1 은 막대를 그리느라 내려받기가 몇 배 느려진다. 함수 안의 대입은 그 함수
  #   안에서만 서고 나오면 저절로 돌아오므로 되돌리는 손이 없다.
  $ProgressPreference = 'SilentlyContinue'

  # 갈래를 넘기는 기준은 「깔았다」가 아니라 「불리나」다 — AppX 는 깔려도 이 세션의 PATH 에 안 잡힐 수 있고, 창은 뜰 때 환경을
  #   한 번 복사하므로 밟은 뒤마다 PATH 를 레지스트리에서 새로 읽고 다시 묻는다.
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
    # 「됐다는데 안 잡힌다」는 「안 됐다」와 다른 명제라 따로 말한다 — 그 차이가 다음에 어디를 팔지를 정한다.
    Write-Host '    · 재등록은 됐는데 winget 이 안 잡힌다 — 다음을 해 본다'
  } catch {
    Write-Host "    · 재등록 안 됨 — $(Say-Why $_)"
  }

  # ② 마이크로소프트가 적어 둔 길 — PSGallery 의 WinGet 모듈이 스스로 고친다. `-AllUsers` 는 관리자를 타므로, 안 되면 그것 없이
  #   한 번 더 — 제 계정에만 서도 쓸 수 있다.
  try {
    Write-Host '    · PowerShell 모듈로 고쳐 본다 (PSGallery)'
    # 있으면 안 받는다 — 깔린 모듈을 `-Force` 로 다시 깔면 윈도우가 「쓰는 중이라 못 바꾼다」로 문다.
    if (Get-Module -ListAvailable -Name Microsoft.WinGet.Client) {
      Write-Host '      (모듈이 이미 있다 — 안 받는다)'
    } else {
      # 받기가 져도 Repair 로 간다 — Repair 는 모듈만 있으면 서므로, 준비의 실패(프록시의 504 등)가 본 걸음을 막지 않게 갈래를
      #   끊는다.
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
  # 걸음마다 제 실패 문장(`$step`)을 들고 catch 가 그것을 그대로 쓴다 — 받기 · 풀기 · 깔기가 한 문장으로 뭉개지면 다 받고 깔다 진
  #   것도 망 탓으로 읽힌다. 문장을 통째로 드는 것은 조사를 붙여 짓지 않게 하려는 것이다.
  $step = '셋째 갈래에서 졌다'
  try {
    Write-Host '    · GitHub 릴리스에서 받아 본다'
    $step = '릴리스 목록을 못 물었다'
    # 묻는 것은 빨리 포기한다 — 작은 JSON 하나라 안 오는 것은 느린 것이 아니라 막힌 것이고, 길게 주면 막힌 망에서 설치가 말없이
    #   오래 멎는다.
    $rel = Invoke-RestMethod 'https://api.github.com/repos/microsoft/winget-cli/releases/latest' `
             -UseBasicParsing -TimeoutSec 60 -ErrorAction Stop
    $step = '받을 자리를 못 만들었다'
    $work = Join-Path ([IO.Path]::GetTempPath()) "winget-$PID"
    New-Item -ItemType Directory -Path $work -Force | Out-Null

    # 갈래 밖에서 비워 둔다 — 딸린 것 자산이 릴리스에 없어 아래 갈래가 통째로 안 도는 판에도 본체 설치가 이 값을 읽는다.
    $depPaths = @()

    # 딸린 것이 먼저다 — 없으면 본체 설치가 그 자리에서 진다
    $dep = $rel.assets | Where-Object { $_.name -like '*Dependencies.zip' } | Select-Object -First 1
    if ($dep) {
      $z = Join-Path $work 'dep.zip'
      $step = '딸린 것 zip 을 못 받았다'
      Say-Get 'winget 딸린 것' $dep
      Get-Download $dep.browser_download_url $z
      $step = '딸린 것 zip 을 못 풀었다'
      Expand-Archive -LiteralPath $z -DestinationPath (Join-Path $work 'dep') -Force
      $step = '딸린 것을 못 깔았다'
      $deps = @(Get-ChildItem (Join-Path $work 'dep') -Recurse -Filter '*.appx' |
                Where-Object { $_.FullName -match 'x64' })
      # 하나도 못 골랐으면 그것부터 말한다 — 고를 것이 없는 것과 다 깐 것은 화면에서 똑같이 조용하고, 본체 설치가 「딸린 것이
      #   없다」로 진다. zip 은 `x64/` · `x86/` · `arm64/` 에 `.appx` 를 든다 — 0 이면 저쪽 꼴이 바뀐 것이니 사람이 본다.
      if (-not $deps.Count) {
        Write-Host '      ! 딸린 것에서 x64 를 하나도 못 골랐다 — 본체 설치가 질 수 있다' `
          -ForegroundColor Yellow
      } else {
        Say-Busy 'winget 딸린 것' 'install' @("$($deps.Count)개")
      }
      foreach ($d in $deps) {
        # 하나가 져도 다음 것으로 간다 — 더 새것이 깔린 기계는 윈도우가 무는데 그건 「할 일 없음」이다. 삼키지는 않고 이름과
        #   사유를 댄다 — 본체가 지는 가장 흔한 원인이 여기다.
        try { Add-AppxPackage -Path $d.FullName -ErrorAction Stop }
        catch { Write-Host "        ($($d.Name) — $(Say-Why $_))" }
      }
      $depPaths = @($deps | ForEach-Object { $_.FullName })
    }

    $pkg = $rel.assets | Where-Object { $_.name -like '*.msixbundle' } | Select-Object -First 1
    if (-not $pkg) { throw '릴리스에 msixbundle 이 없다' }
    $b = Join-Path $work $pkg.name
    $step = '본체를 못 받았다'
    Say-Get 'winget' $pkg
    Get-Download $pkg.browser_download_url $b
    # 깔기는 수백 MB 를 푸는 동안 한 글자도 안 내므로 들어가기 전에 말한다 — 조용하면 사람은 멎은 줄 알고 창을 닫는다.
    Say-Busy 'winget' 'install' @('몇 분 걸릴 수 있다')
    $step = '본체를 못 깔았다'
    # 딸린 것을 같이 넘긴다(마이크로소프트가 적어 둔 꼴) — 위에서 하나씩 깐 뒤에도 판 맞추기를 윈도우가 하게 하고, 위 걸음이 다
    #   져도 여기서 한 번 더 선다.
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

# 「올릴 것」 표의 글(`$Text`)에 그 앱(`$App` 의 Id · Name)이 걸리나 — 참 · 거짓. Id 가 표에서 잘릴 수 있어 Id 든 이름이든 걸리면
#   참이다(헛되게 한 번 더 묻는 값은 시간뿐이고, 안 물어 낡은 판이 서는 값은 고장이다).
# ⚠ **낱말째 건다 — 글자 조각으로 걸지 않는다.** `-like "*Git*"` 꼴은 `Logitech Options` 한 줄에도 걸려 최신인 Git 을 매번
#   「올릴 것」으로 세운다. 셋 중 하나면 센다:
#   · Id 가 통째로 — 앞뒤가 Id 글자(영숫자·점)가 아니다. `Git.Git` 이 `Git.GitLFS` 에 안 걸린다
#   · 잘린 Id — 표가 `Microsoft.VisualStud…` 처럼 줄였으면 그 앞토막이 우리 Id 의 머리다
#   · 이름 칸 — 줄 첫머리에 이름이 서고 **칸 간격(빈칸 둘 이상)이나 줄임표가 뒤따른다.** 그래서
#     `Git` 은 `GitHub CLI` 에, `Python` 은 `Python Launcher` 에 안 걸린다
function Test-UpgradeRow([string]$Text, [hashtable]$App) {
  $id   = [regex]::Escape($App.Id)
  $name = [regex]::Escape($App.Name)
  if ($Text -match "(?<![\w.])$id(?![\w.])") { return $true }
  if ($Text -match "(?m)^\s*$name(\s{2,}|…|\s*$)") { return $true }
  foreach ($m in [regex]::Matches($Text, '(?<![\w.])([\w.\-+]{8,})…')) {
    if ($App.Id.StartsWith($m.Groups[1].Value, [StringComparison]::OrdinalIgnoreCase)) { return $true }
  }
  return $false
}

# 할 일을 가른다 — 설치 갈래(프로그램 · 데스크탑 앱 · npm CLI · winget CLI · VS Code 확장)가 다 이 한 자리에 묻는다. 갈래마다
#   다른 것은 재는 손과 하는 손뿐이다(claude-config 결정 0145).
#   받는 것 — `$Installed` 깔렸나(`yes` · `no` · `unmeasured`) · `$Current` 깔린 판 · `$Latest` 최신 판(빈 글자는 「모른다」) ·
#     `$Listed` 맨 앞에서 한 번에 받은 「올릴 것」 목록의 답(`$true` 목록에 있다 · `$false` 목록을 받았는데 없다 · `$null` 못 받았거나
#     그 목록에 안 묻는 갈래) · `$CanAsk` 판을 모를 때 그 도구에 올리기를 물어도 되나(winget `upgrade` 와 `code --update-extensions`
#     는 판을 안 내린다 · npm 은 묻는 것이 곧 다시 받기다) · `$NoUpgrade` 올리기를 안 하는 판(`-NoUpgrade` · 올릴 도구가 없다 · 그 행이
#     안 올린다)
#   내는 것 — `hold` 손대지 않는다(「안 한 걸음」 · 결정 0141) · `install` 깐다 · `present` 있음 · `latest` 최신 · `upgrade` 올린다 ·
#     `upcheck` 올릴 것이 있는지 모르는 채 묻는다 · `keep` 깔린 것을 두고 노란 줄로 말한다
# ⚠ **`install` 은 `no` 에서만 난다.** 깔린 것 위에 새로 깔면 그 도구 목록의 판으로 간다 — 그 판은 앱이 스스로 올린 판보다 늦을 수
#   있어 앱을 내린다. 모르는 값도 `hold` 다.
# ⚠ **판을 모르는 것은 「다르다」가 아니다.** 빈 판을 다르다로 읽으면 npm 은 매 실행 다시 받는다 — 두 판을 다 알 때만 견준다.
function Get-InstallAction([string]$Installed, [string]$Current, [string]$Latest, $Listed, [bool]$CanAsk, [bool]$NoUpgrade) {
  if ($Installed -eq 'no')  { return 'install' }
  if ($Installed -ne 'yes') { return 'hold' }
  if ($NoUpgrade)           { return 'present' }
  if ($null -ne $Listed)    { if ($Listed) { return 'upgrade' } else { return 'latest' } }
  if ($Current -and $Latest) {
    # 깔린 판 글자는 꼴이 셋이다 — `2.1.273 (Claude Code)` · `codex-cli 0.154.0` · `0.60.0`. 그래서 등호로 못 재고 「깔린 글자가
    #   최신 판을 낱말로 품나」로 잰다. 경계를 `\b` 로 안 잡는다 — 점을 경계로 쳐서 `1.2.1.273` 이 `2.1.273` 을 품은 것이 된다.
    if ($Current -match "(?<![\w.])$([regex]::Escape($Latest))(?![\w.])") { return 'latest' }
    return 'upgrade'
  }
  if ($CanAsk) { return 'upcheck' }
  return 'keep'
}

# 맨 앞에서 한 번에 받은 「올릴 것」 목록(`$upgradable`)의 답 — `$null` 은 목록을 못 받았다는 뜻이라 「없다」로 안 읽는다.
function Get-Listed([string]$Id) {
  if ($null -eq $upgradable) { return $null }
  return ($upgradable -contains $Id)
}

# winget 으로 올린다 — 할 일이 `upgrade` · `upcheck` 일 때 winget 갈래(프로그램 · 데스크탑 앱 · winget CLI)가 부른다. `$Act` 가
#   걸음 줄의 낱말이다. `upgrade` 만 부르고 `install` 은 안 부른다 — winget `upgrade` 는 깔린 판보다 낮은 판으로 안 간다.
# ⚠ **종료코드를 판정에 안 쓴다** — 올릴 것이 없어도 winget 은 0 이 아닌 값을 낸다. 올랐나는 앞뒤 판이 가른다(`Write-UpgradeResult`).
function Invoke-WingetUpgrade([string]$Label, [string]$Id, [string]$Source, [string]$Act, [string[]]$Notes = @()) {
  Say-Busy $Label $Act (@('winget') + $Notes)
  $log = [System.IO.Path]::GetTempFileName()
  Invoke-Logged 'winget' (@('upgrade','--id',$Id,'--source',$Source) + $WGOpts) $log | Out-Null
  Remove-Item $log -ErrorAction SilentlyContinue
}

# winget 으로 올리기를 물은 뒤의 한 줄 — 프로그램 · 데스크탑 앱 · winget CLI 가 이 한 자리를 쓴다.
# ⚠ **앞 판을 못 읽었으면 「올렸다」로 안 찍는다** — 빈 글자와 읽힌 판은 늘 다르므로 그 비교가 참이 되어, 올린 적 없는 자리에
#   ` -> 3.14.7` 이 선다(#32 처럼 앞 판이 삼켜진 회차). 둘 다 읽혔을 때만 견주고, 한쪽이라도 비면 「최신」에 읽힌 판을 대거나
#   못 읽음을 말한다(`Format-VerPart`).
function Write-UpgradeResult([string]$Name, [string]$before, [string]$after) {
  if ($after -and $before -and $after -ne $before) {
    Write-Host "  $Name — 올렸다  $before  ->  $after" -ForegroundColor Green
  } else {
    $shown = if ($after) { $after } else { $before }
    Write-Host "  $Name — 최신  $(Format-VerPart $shown)"
  }
}

# 윈도우 설치 목록(제어판 「앱」 · 레지스트리 `Uninstall`)의 항목 — `@{ Name = DisplayName; Ver = DisplayVersion }` 를 다 낸다.
#   사용자 범위(HKCU)와 기계 범위(HKLM), 64 · 32 비트 두 보기를 다 본다 — 32 비트 파워셸에서도 64 비트 보기를 열도록 경로가
#   아니라 `RegistryView` 로 연다. 못 여는 가지는 건너뛴다.
function Get-UninstallEntries {
  $out = @()
  foreach ($hive in 'CurrentUser', 'LocalMachine') {
    foreach ($view in 'Registry64', 'Registry32') {
      $base = $null; $k = $null
      try {
        $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey($hive, $view)
        $k = $base.OpenSubKey('SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall')
        if ($k) {
          foreach ($n in $k.GetSubKeyNames()) {
            $s = $null
            try {
              $s = $k.OpenSubKey($n)
              if ($s) {
                $dn = [string]$s.GetValue('DisplayName')
                if ($dn) { $out += @{ Name = $dn; Ver = [string]$s.GetValue('DisplayVersion') } }
              }
            } catch { } finally { if ($s) { $s.Close() } }
          }
        }
      } catch { } finally { if ($k) { $k.Close() }; if ($base) { $base.Close() } }
    }
  }
  return $out
}

# 짐의 데스크탑 앱 스위치를 읽는다 — 받는 것은 `#desktop-app` 의 값(없으면 빈 값), 내는 것은 @{ When = `:` 앞 낱말(offsite · yes ·
#   그 밖은 아무것도 안 깐다); Extra = `:` 뒤 목록(이제 안 쓴다 — 「데스크탑 앱 설치」 칸이 그것을 말하고 지나간다) }.
function Read-DesktopAppSwitch([string]$Directive) {
  if ($Directive -and $Directive -match '^\s*([A-Za-z]+)\s*:\s*(.*?)\s*$') { return @{ When = $Matches[1]; Extra = $Matches[2].Trim() } }
  return @{ When = [string]$Directive; Extra = '' }
}

# 데스크탑 앱 행이 이 자리에서 깔리나 — 받는 것은 `$DesktopApps` 의 행 · 스위치(`Read-DesktopAppSwitch` 의 `When`) · 사외인가, 내는
#   것은 참 · 거짓. 스위치 `yes` 는 행을 안 보고 깔고, `offsite` 는 행의 `When`(안 적으면 `offsite`)을 따른다 — `any` 는 늘, `offsite`
#   는 사외에서만. 「데스크탑 앱 설치」 칸과 `-Describe` 의 `app|` 줄이 이 한 자를 쓴다(설치 창의 안내 줄이 그 줄로 선다).
function Test-DesktopAppHere($Row, [string]$When, [bool]$Offsite) {
  $rowWhen = if ($Row.When) { $Row.When } else { 'offsite' }
  return [bool]($When -eq 'yes' -or ($When -eq 'offsite' -and ($rowWhen -eq 'any' -or $Offsite)))
}

# 데스크탑 앱이 깔렸나를 세 값으로 잰다 — `@{ State = yes · no · unmeasured; Ver = 깔린 판(모르면 빈 글자); Probe = 못 잰 물음;
#   Why = 그 물음이 어떻게 졌나(`Add-UnmeasuredStep` 의 꼴) }`.
#   묻는 차례 — 시작 메뉴(`App`) → 윈도우의 설치 목록(`Reg` — `Uninstall` 의 `DisplayName` · `Appx` — 꾸러미 가족) → winget 목록.
#   하나라도 찾으면 `yes` 다. GUI 앱이라 `--version` 을 부를 이름이 없어 `Measure-Runs` 를 못 쓴다.
# ⚠ **이름은 「있다」만 세운다.** 시작 메뉴 이름과 `DisplayName` 은 벤더가 바꾸는 글자라, 못 찾은 것이 없는 것이 아니다. 「없다」는
#   꾸러미의 정체가 세운다 — `Appx` 행은 그 가족(게시자에 묶인 이름이고 그 행의 꼴이 그것뿐이다)이, 나머지는 `winget list --exact`
#   가 「깔린 꾸러미가 없다」(`$WingetNotInstalled`)로 답할 때만이다. winget 이 없거나 다른 값으로 지면 `unmeasured` 다 — 소스
#   인증서(`0x8A15005E`) · 인덱싱 지연이 흔하다(claude-config 결정 0145).
#   `Appx` 행에는 winget 목록을 안 묻는다 — msstore 소스는 깔린 스토어 꼴 앱에 「안 깔렸다」를 내고, 막힌 회선에서는 열리지도 않는다.
# ⚠ **winget 에는 `--exact` 를 준다** — 없으면 Id 가 글자 조각으로 걸려 `Google.Antigravity` 가 `Google.AntigravityCLI` 에 「있음」을
#   낸다. 같은 까닭으로 `Reg` 는 이름 전체에 거는 `-like` 꼴이다 — `Antigravity CLI` 가 데스크탑 앱 곁에 선다.
function Measure-DesktopApp($A) {
  $hit = $false; $ver = ''
  try {
    $s = @(Get-StartApps -ErrorAction Stop | Where-Object { $_.Name -like "*$($A.App)*" })[0]
    if ($s) {
      $hit = $true
      # 스토어 꼴 손잡이(`가족!앱`)면 그 꾸러미의 판을 읽는다 — 판을 못 읽어도 「있다」는 그대로다.
      if ("$($s.AppID)" -match '^([^!]+)!') {
        $fam = $Matches[1]
        try { $ver = [string](@(Get-AppxPackage -Name ($fam -replace '_[^_]+$', '') -ErrorAction Stop |
                                Where-Object { $_.PackageFamilyName -eq $fam })[0].Version) } catch { }
      }
    }
  } catch { }
  if ($A.Reg) {
    $e = @(Get-UninstallEntries | Where-Object { $_.Name -like $A.Reg })[0]
    if ($e) { $hit = $true; if (-not $ver) { $ver = $e.Ver } }
  }
  if ($hit) { return @{ State = 'yes'; Ver = $ver; Probe = ''; Why = '' } }
  if ($A.Appx) {
    $probe = "Get-AppxPackage $($A.Appx)"
    try {
      $pkg = @(Get-AppxPackage -Name ($A.Appx -replace '_[^_]+$', '') -ErrorAction Stop |
               Where-Object { $_.PackageFamilyName -eq $A.Appx })[0]
    } catch { return @{ State = 'unmeasured'; Ver = ''; Probe = $probe; Why = '오류를 던져' } }
    if ($pkg) { return @{ State = 'yes'; Ver = [string]$pkg.Version; Probe = ''; Why = '' } }
    return @{ State = 'no'; Ver = ''; Probe = ''; Why = '' }
  }
  $probe = "winget list --id $($A.Id) --exact --source $($A.Source)"
  if ($A.Via -ne 'winget' -or $noWinget) { return @{ State = 'unmeasured'; Ver = ''; Probe = $probe; Why = 'winget 이 없어 안 불려' } }
  # `$WingetListCap` 울타리를 두른다 — 멎은 `winget list` 하나가 설치를 영구히 세우지 않게(#26). 넘기면 「못 쟀다」다.
  $tl = [IO.Path]::GetTempFileName()
  $rc = Invoke-LoggedCapped 'winget' @('list','--id',$A.Id,'--exact','--source',$A.Source) $tl $WingetListCap
  $txt = "$(Get-Content -LiteralPath $tl -Raw -Encoding UTF8 -ErrorAction SilentlyContinue)"
  Remove-Item -LiteralPath $tl, "$tl.err" -ErrorAction SilentlyContinue
  if ($rc -eq -2) { Add-ProbeOverflow $probe $WingetListCap }
  if ($rc -eq 0) {
    # 판은 표에서 Id 바로 뒤 칸이다 — 이름 칸은 빈칸을 품을 수 있어 Id 로 줄을 잡는다. Id 가 잘려 찍혔으면 판을 모른다.
    $m = [regex]::Match($txt, "(?m)(?<![\w.])$([regex]::Escape($A.Id))\s+(\S+)")
    return @{ State = 'yes'; Ver = $(if ($m.Success) { $m.Groups[1].Value } else { '' }); Probe = ''; Why = '' }
  }
  if ($rc -eq $WingetNotInstalled) { return @{ State = 'no'; Ver = ''; Probe = ''; Why = '' } }
  return @{ State = 'unmeasured'; Ver = ''; Probe = $probe; Why = (Format-ProbeWhy $rc $WingetListCap) }
}

# 깔렸나를 참 · 거짓으로 — 깐 뒤 「섰나」를 다시 묻는 자리가 쓴다. 못 잰 것은 거짓이다.
function Test-DesktopApp($A) {
  return ((Measure-DesktopApp $A).State -eq 'yes')
}

# WebView2 런타임의 판 — EdgeUpdate 의 `Clients\<$WebView2Guid>` 세 자리(기계 32 · 64 비트 보기 · 사용자)에서 `pv` 를 읽어 처음
#   것을 내고, 없으면 빈 글자다.
function Test-WebView2 {
  foreach ($p in @("HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\$WebView2Guid",
                   "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$WebView2Guid",
                   "HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients\$WebView2Guid")) {
    try {
      $pv = (Get-ItemProperty -LiteralPath $p -Name pv -ErrorAction Stop).pv
      if ($pv) { return $pv }
    } catch { }
  }
  return ''
}

# 앱의 짝(`Requires`)을 winget 으로 먼저 세운다 — 다 있거나 섰으면 `$true`, 하나라도 못 세우면 빨간 줄 · `$Fails` 와 함께 `$false`.
function Install-Requires($A) {
  foreach ($id in @($A.Requires)) {
    if (-not $id) { continue }
    # 재는 자는 짝마다 다르다 — 짝이 늘면 여기에 한 갈래를 더한다.
    # ⚠ **모르는 id 는 재지 않고 깐다** — 「못 쟀다」를 「있다」로 접으면 설치가 조용히 안 서고, 그 실패는 앱 쪽에서 엉뚱한
    #   사유로 나타난다.
    if ($id -eq 'Microsoft.EdgeWebView2Runtime') {
      $pv = Test-WebView2
      if ($pv) { Write-Host ('      · WebView2 런타임 — 있음 {0}' -f (Format-VerPart $pv)); continue }
      $what = 'WebView2 런타임'
    } else {
      $what = $id
    }
    if ($noWinget) {
      Write-Host '      ! winget 이 없어 짝을 못 깐다 — 이 앱도 안 선다' -ForegroundColor Red
      $script:Fails.Add("$($A.Label) (짝 $id — winget 이 없다)")
      return $false
    }
    Say-Busy $what 'install' @('winget', "$($A.Label) 이 먼저 요구한다")
    $rl = [IO.Path]::GetTempFileName()
    $rc = Invoke-Logged 'winget' (@('install','--id',$id) + $WG) $rl
    if ($rc -ne 0) {
      # 사유를 우리가 분류하지 않는다 — 뱉은 끝 줄을 그대로 낸다(`Show-Log`).
      Write-Host ("      ! 짝을 못 깔았다 (winget 이 $rc 로 끝났다) — 뱉은 끝 줄:") -ForegroundColor Red
      Show-Log $rl 5
      $script:Fails.Add("$($A.Label) (짝 $id)")
      Remove-Item $rl -ErrorAction SilentlyContinue
      return $false
    }
    Remove-Item $rl -ErrorAction SilentlyContinue
    Write-Host '      · 짝이 섰다'
  }
  return $true
}

# 데스크탑 앱 한 행(`$DesktopApps`)을 재고 할 일대로 깔거나 올린다 — 섰거나 이미 있으면 `$script:InstalledAppRows` 에, 이번에 깔았으면
#   `$script:JustInstalledApps` 에 남기고, 못 깔면 빨간 줄 · `$Fails`, 못 쟀으면 `Add-UnmeasuredStep` 이다.
#   실패를 우리가 분류하지 않는다 — 막히는 방식이 앱마다 다르고(소스 인증서 · 회선 정책 · 인자) 코드표로 옮기면 한 기계에서 본
#   것이 규칙 행세를 한다. 도구가 뱉은 끝 줄을 그대로 낸다(`Show-Log`).
function Install-DesktopApp($A) {
  Write-Host ''
  Write-Host "  $($A.Label)" -ForegroundColor Cyan
  $m = Measure-DesktopApp $A
  # 올리기는 winget 길의 행만 한다 — `NoSelfUpgrade` 행(스토어 앱)은 있으면 둔다.
  $deskAct = Get-InstallAction $m.State $m.Ver '' (Get-Listed $A.Id) $true `
               ($NoUpgrade -or $noWinget -or $A.Via -ne 'winget' -or [bool]$A.NoSelfUpgrade)
  # 뒷길이 있으면 winget 이 없어도 여기서 안 끝낸다 — 뒷길은 winget 을 안 탄다. 깔린 앱은 winget 없이도 「있음」이다.
  if (($deskAct -eq 'install' -or $deskAct -eq 'hold') -and $A.Via -eq 'winget' -and $noWinget -and -not $A.Fallback) {
    Write-Host '  ! winget 이 없어 못 깐다' -ForegroundColor Red
    $script:Fails.Add("$($A.Label) (winget 이 없다)")
    return
  }
  # ⚠ **못 쟀으면 깔지도 올리지도 않는다** — 못 잰 것을 「없다」로 읽으면 깔린 앱 위에 `winget install` 을 돌려 winget 목록의 판으로
  #   내린다(결정 0145).
  if ($deskAct -eq 'hold') {
    Add-UnmeasuredStep $A.Label $m.Probe '깔지도 올리지도 않았다' $m.Why
    return
  }
  if ($deskAct -ne 'install') {
    if ($deskAct -eq 'present')    { Write-Host "  있음  $(Format-VerPart $m.Ver)" }
    elseif ($deskAct -eq 'latest') { Write-Host "  최신  $(Format-VerPart $m.Ver)" }
    elseif ($deskAct -eq 'upgrade' -or $deskAct -eq 'upcheck') {
      Invoke-WingetUpgrade $A.Label $A.Id $A.Source $deskAct
      Write-UpgradeResult $A.Label $m.Ver (Measure-DesktopApp $A).Ver
    }
    $script:InstalledAppRows[$A.Label] = $A
    return
  }
  # 짝이 먼저다 — 앱이 없을 때만 온다(앱이 섰으면 짝도 선 것이라 위에서 나갔다). 짝이 지면 앱을 시도하지 않는다 — 시도하면
  #   실패가 앱 이름으로 찍혀 까닭이 한 겹 숨는다.
  if ($A.Requires -and -not (Install-Requires $A)) { return }
  # 길이 둘일 수 있다 — 앞길부터, 지면 뒷길. 뒷길은 제 몫(`Via`·`Url`·`SilentArgs`)만 들고 이름 둘(`App`·`Label`)은 앞길에서
  #   물려받는다.
  $ways = @($A)
  if ($A.Fallback) { $ways += (@{ App = $A.App; Label = $A.Label } + $A.Fallback) }

  $al = $null
  $rc = $null
  foreach ($W in $ways) {
   if ($al) { Remove-Item $al -ErrorAction SilentlyContinue }
   $al = [IO.Path]::GetTempFileName()
   if ($W.Via -eq 'winget') {
    if ($noWinget) { Write-Host '      · winget 이 없다 — 다음 길로'; continue }
    # 오래 걸리는 걸음은 들어가기 전에 말한다 — winget 은 `--silent` 로 수백 MB 를 받는 1~2분 동안 화면을 안 바꿔, 「도는 중」과
    #   「멈췄다」가 같은 화면이 된다. 소스는 기본(`winget`)이 아닐 때만 댄다(「winget · winget」이 안 찍히게).
    $via = if ($W.Source -and $W.Source -ne 'winget') { "winget · $($W.Source)" } else { 'winget' }
    Say-Busy $A.Label 'install' @($via, '수백 MB · 1~2분 걸릴 수 있다')
    $rc = Invoke-Logged 'winget' (@('install','--id',$W.Id,'--source',$W.Source) + $WGOpts) $al
   } else {
    # 받기와 돌리기를 가른다 — 못 받은 것과 받았는데 진 것은 다른 명제라, 섞으면 회선이 막은 자리에서 「설치가 실패했다」만 남는다.
    $exe = Join-Path ([IO.Path]::GetTempPath()) ("{0}Setup.exe" -f $W.App)
    try {
      # 받아 놓을 파일 이름을 댄다 — 주소의 끝마디는 제품 번호(`9PLM9XGG6VKS`)일 수 있어 받는 사람에게 뜻이 없다.
      Say-Busy $A.Label 'fetch' @((Split-Path $exe -Leaf))
      Get-Download $W.Url $exe
    } catch {
      Write-Host '  ! 설치본을 못 받았다' -ForegroundColor Red
      Say-Why $_
      $script:Fails.Add("$($A.Label) (설치본을 못 받았다)")
      Remove-Item $al -ErrorAction SilentlyContinue
      return
    }
    Say-Busy $A.Label 'install' @('설치본', '몇 분 걸릴 수 있다')
    $pr = Start-Process -FilePath $exe -ArgumentList $W.SilentArgs -PassThru -Wait
    $rc = $pr.ExitCode
    Remove-Item $exe -ErrorAction SilentlyContinue
   }
   if (Test-DesktopApp $A) { break }
   if ($W -ne $ways[-1]) { Write-Host ('      · 이 길이 졌다 (낸 값 {0}) — 다음 길로' -f $rc) }
  }
  if (Test-DesktopApp $A) {
    Write-Host '  깔았다' -ForegroundColor Green
    $script:JustInstalledApps[$A.App] = $true
    $script:InstalledAppRows[$A.Label] = $A
  } elseif ($rc -eq 0) {
    # 종료 0 인데 앱이 없다 = 설치본이 제 일을 남에게 넘긴 것이다(스토어 스텁이 스토어 창을 띄우고 빠지는 갈래). 「설치 실패」로
    #   찍으면 거짓이고 사람이 눌러야 할 일 때문에 설치가 빨갛게 끝난다 — 진짜 실패는 0 이 아닌 값을 낸다.
    Write-Host '  · 창이 열렸다 — 거기서 [다운로드]를 누르면 깔린다' -ForegroundColor Yellow
    Write-Host '     설치기는 그것을 못 기다린다(넘긴 프로세스가 이미 끝났다). 깔린 뒤 다시 누르면 「있음」으로 지나간다.'
  } else {
    Write-Host ('  ! 설치 실패 — 낸 값 {0}' -f $rc) -ForegroundColor Red
    # 설치본이 제 로그를 남기는 갈래면 그 끝 줄을 댄다 — 회선이 막은 자리에서는 막았다는 말이 그 안에 그대로 들어 있다.
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

# 깔린 확장과 그 판 — `@{ Vers = @{ Id = 판 }; Why = '' }`. 못 읽었으면 `Vers` 가 `$null` 이고 `Why` 가 그 까닭이다
#   (`Add-UnmeasuredStep` 의 꼴): 못 읽은 목록을 빈 목록으로 읽으면 깔린 확장을 「없다」로 보고 다시 깐다(결정 0145).
#   `$ExtListCap` 울타리를 두른다 — 멎은 `code` 하나가 설치를 영구히 세우지 않게(#26). 넘기면 「못 쟀다」다.
function Get-ExtVersions {
  $log = [IO.Path]::GetTempFileName()
  try {
    $rc = Invoke-LoggedCapped 'code' @('--list-extensions','--show-versions') $log $ExtListCap
    if ($rc -eq -2) { Add-ProbeOverflow 'code --list-extensions --show-versions' $ExtListCap }
    if ($rc -ne 0) { return @{ Vers = $null; Why = (Format-ProbeWhy $rc $ExtListCap) } }
    $m = @{}
    foreach ($l in @(Get-Content -LiteralPath $log -Encoding UTF8 -ErrorAction SilentlyContinue)) {
      if ($l -match '^(.+)@([^@]+)$') { $m[$Matches[1]] = $Matches[2] }
    }
    return @{ Vers = $m; Why = '' }
  } finally { Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue }
}

# 고른 확장을 까는 한 자리 — 확장마다 같은 걸음을 적으면 함정(곧바로 물으면 아직 없다 · 인증서면 다른 병이다)을 사본마다
#   따로 지켜야 한다(결정 0041). 할 일이 `hold` 인 행은 「안 한 걸음」(`Add-UnmeasuredStep`), 그 밖에 `install` 이 아닌 행은 결과
#   줄만 찍고, 못 깐 확장은 빨간 줄 · `$Fails` 다.
# 빠진 확장은 `code` 한 번에 넘긴다(`--install-extension` 여럿 · PAISetup #35 B) — `code` 를 띄울 때마다 node 가 새로 서고
#   마켓플레이스에 한 번 묻는 값이 VDI 에서 몇 초씩이라 확장 수만큼 쌓인다. 깔았나도 목록 한 번으로 잰다. `--force` 는 같은 판을
#   다시 받지 않는다(`already installed` 만 찍는다) — 느린 것은 `code` 를 띄우는 횟수다.
#   묶음이 지면 하나씩 다시 깐다 — 묶음의 종료 값 하나로는 어느 확장이 졌는지 몰라서다. 하나만 넘긴 묶음은 다시 안 깐다.
#   긴 명령 앞에 한 줄을 먼저 찍는다 — 화면 껍데기의 상태 줄은 마지막으로 나온 줄이라, 안 찍으면 그동안 직전 칸의 결과가 「지금
#   하는 일」로 서 있다.
# `$Rows` 는 고른 확장의 행(`Id` · `Label`), `$Acts` 는 「VS Code 확장」 걸음이 행마다 `Get-InstallAction` 에서 받은 할 일이다
#   (`Id` → 할 일) — 올리기(`upcheck`)는 그 걸음이 깔린 확장을 한 번에 묻고(`--update-extensions`) 여기는 앞뒤 판(`$Before` · `$After`)으로
#   결과만 찍는다. `$Probe` · `$Why` 는 못 쟀을 때 댈 물음과 그 까닭이다(`Add-UnmeasuredStep` 의 꼴).
function Install-Extension($Rows, [hashtable]$Acts, [hashtable]$Before, [hashtable]$After, [string]$Probe, [string]$Why) {
  $todo = @()
  foreach ($x in @($Rows)) {
    $Id = $x.Id; $Label = $x.Label; $Act = $Acts[$Id]
    if ($Act -eq 'hold') {
      Add-UnmeasuredStep $Label $Probe '깔지도 올리지도 않았다' $Why
      continue
    }
    if ($Act -ne 'install') {
      $b = $Before[$Id]; $a = if ($After) { $After[$Id] } else { '' }
      if ($Act -eq 'present')     { Write-Host "  $Label — 있음  $(Format-VerPart $b)" }
      elseif ($a -and $a -ne $b)  { Write-Host "  $Label — 올렸다  $b  ->  $a" -ForegroundColor Green }
      else                        { Write-Host "  $Label — 최신  $(Format-VerPart $b)" }
      continue
    }
    $todo += ,$x
  }
  if (-not $todo.Count) { return }
  $ids = @($todo | ForEach-Object { $_.Id })
  Say-Busy (@($todo | ForEach-Object { $_.Label }) -join ' · ') 'install' @('code')
  $xl = [IO.Path]::GetTempFileName()
  $xa = @(); foreach ($i in $ids) { $xa += '--install-extension', $i }
  $rc = Invoke-Logged 'code' ($xa + '--force') $xl
  $rcs = @{}; $logs = @{}
  if ($rc -ne 0 -and $todo.Count -gt 1) {
    Write-Host "  (확장 $($todo.Count)개를 한 번에 깔다가 code 가 $rc 로 끝났다 — 하나씩 다시 깐다)"
    foreach ($x in $todo) {
      Say-Busy $x.Label 'install' @('code')
      $logs[$x.Id] = [IO.Path]::GetTempFileName()
      $rcs[$x.Id]  = Invoke-Logged 'code' @('--install-extension',$x.Id,'--force') $logs[$x.Id]
    }
  } else {
    foreach ($x in $todo) { $rcs[$x.Id] = $rc; $logs[$x.Id] = $xl }
  }
  # ⚠ **곧바로 물으면 아직 없을 수 있다** — VS Code 가 떠 있으면 설치가 그 인스턴스로 넘어가고 명령은 바로 돌아와, 그때 목록을
  #   물으면 멀쩡한 설치가 실패로 찍힌다. 몇 초를 두고 다시 묻는다.
  # 묻는 한 번마다 `$ExtListCap` 울타리를 두른다(#26). 목록을 못 읽었으면(넘김 · 0 아닌 값) 더 안 묻고 「깔았나를 못 쟀다」로
  #   남긴다 — 못 읽은 목록은 빈 목록이 아니다(결정 0141 · 0145).
  $listExt = {
    $ll = [IO.Path]::GetTempFileName()
    try {
      $lrc = Invoke-LoggedCapped 'code' @('--list-extensions') $ll $ExtListCap
      @{ Rc = $lrc; Ids = @(Get-Content -LiteralPath $ll -Encoding UTF8 -ErrorAction SilentlyContinue | ForEach-Object { "$_".Trim() }) }
    } finally { Remove-Item -LiteralPath $ll, "$ll.err" -ErrorAction SilentlyContinue }
  }
  #   다시 묻기는 깐 확장이 다 뜰 때까지 다섯 번 · 2초 틈이다 — 느린 `code` 에서도 그 횟수는 묻는다(끝 시각으로 자르면 한 번이 몇 초 걸리는
  #   PC 에서 다시 묻기가 한두 번으로 줄어 늦게 뜬 확장을 「설치 실패」로 찍는다). 목록을 못 읽은 물음이 하나라도 나면 그 자리에서 멈춘다 —
  #   넘김이 횟수의 곱으로 쌓이지 않는다(결정 0141).
  $ls = & $listExt
  $missing = { @($ids | Where-Object { $ls.Ids -notcontains $_ }).Count }
  for ($i = 0; $i -lt 5 -and (& $missing) -and $ls.Rc -eq 0; $i++) {
    Start-Sleep -Seconds 2
    $ls = & $listExt
  }
  # 넘김은 물음 하나에 한 줄이다 — 목록은 확장 모두가 한 번에 물었다.
  if ($ls.Rc -eq -2 -and (& $missing)) { Add-ProbeOverflow 'code --list-extensions' $ExtListCap }
  foreach ($x in $todo) {
    $Id = $x.Id; $Label = $x.Label; $rc = $rcs[$Id]; $xlog = $logs[$Id]
    if ($ls.Ids -notcontains $Id -and $ls.Rc -ne 0) {
      Add-UnmeasuredStep $Label 'code --list-extensions' '깔았나를 못 쟀다' (Format-ProbeWhy $ls.Rc $ExtListCap)
    } elseif ($ls.Ids -contains $Id) {
      Write-Host "  $Label — 깔았다" -ForegroundColor Green
    } else {
      # 까닭을 편다 — 「! 설치 실패」 한 줄만 내면 다음 사람이 열어 볼 자리가 없다.
      Write-Host "  ! $Label 설치 실패 (code 가 $rc 로 끝났다) — 뱉은 끝 줄:" -ForegroundColor Red
      Show-Log $xlog
      Write-Host '     10초를 기다려도 목록에 안 떴다.'
      # 인증서면 다른 병이다 — 「self signed certificate」 는 VS Code 의 흠이 아니라 길에 TLS 를 가로채는 장비가 있는데 Node 가
      #   그 CA 를 모른다는 말이다. 안 짚으면 사람은 VS Code 를 다시 깔러 간다.
      $said = (Get-Content -LiteralPath $xlog -ErrorAction SilentlyContinue) -join "`n"
      if ($said -match 'self.signed certificate|unable to (verify|get local issuer)|UNABLE_TO_|CERT_') {
        Write-Host '     ↑ 인증서 문제다 — 길에 TLS 를 가로채는 장비가 있는데 Node 가 그 CA 를 모른다.' -ForegroundColor Yellow
        Write-Host '        VS Code 를 다시 깔아도 안 낫는다. 위 「Node 신뢰 배선」 칸을 먼저 본다.'
      }
      Write-Host '     VS Code 가 열려 있으면 전부 닫고 다시 눌러 본다.'
      Write-Host "     손으로 재려면:  code --install-extension $Id --force"
      $Fails.Add("VS Code 확장 ($Label)")
    }
  }
  Remove-Item -LiteralPath (@($xl) + @($logs.Values) | Select-Object -Unique) -ErrorAction SilentlyContinue
}

# npm 이 제 기록에 적은 그 패키지들 — 패키지 이름마다 `@{ State = yes · no · unmeasured; Ver = 깔린 판(모르면 빈 글자); Probe; Why }`
#   (`Add-UnmeasuredStep` 의 꼴)를 든 표. `npm ls -g <pkg…> --depth=0 --json` 의 `dependencies.<pkg>` 가 있으면 `yes`, JSON 을 냈는데
#   없으면 `no` 다. npm 으로 깐 CLI 가 깔렸나와 그 판은 이 자 하나가 잰다 — 「CLI」 걸음과 끝 검증이 같이 쓴다(PAISetup #30 ③).
# 고른 패키지를 한 번에 묻는다(PAISetup #35 C) — npm 을 띄울 때마다 node 가 새로 서는 값이 패키지 수만큼 쌓인다. 이름을 넘겨
#   거르는 것은 하나씩 물을 때와 같다: 넘긴 이름의 꼴(있는 것만 `dependencies` 에 · 맨바닥의 `ENOENT`)이 하나씩 물을 때와 같고
#   (npm 11), 넘긴 이름 밖의 전역 패키지는 이 물음에 안 든다. 물음이 지면 넘긴 패키지가 다 그 하나에 걸린 못 잼이다.
# ⚠ **그 CLI 를 띄워 재지 않는다** — 첫 실행에 제 짐을 푸는 CLI 는 첫 `--version` 이 울타리(`$ProbeCap`)를 넘겨, npm 이 성공한
#   설치가 「설치 실패」 · 끝 검증 `[?]` 로 선다(PAISetup #30). 이 기록의 글자는 node 가 다 선 뒤에 나와 DRM 이 끼는 PC 에서도 안
#   잃는다(#32).
# ⚠ **종료코드로 안 가른다** — npm 은 그 패키지가 없거나 전역 폴더에 군더더기가 있으면 1 로 끝나면서도 JSON 은 온전히 낸다. 넘겼거나
#   못 띄웠거나 JSON 을 못 읽었거나 npm 이 오류를 적었으면 `unmeasured` 다 — 「없다」가 아니다(결정 0141). 넘김의 `Why` 는 비운다
#   (`Add-UnmeasuredStep` 이 `$ProbeCap` 넘김 글로 채운다).
# 맨바닥 PC 의 `ENOENT` 는 「없다」다 — 전역 폴더(`%APPDATA%\npm`)는 첫 `npm install -g` 가 만들어, 그 전에는 npm 이 그 자리를 못
#   읽고 `error.code = ENOENT` 를 적는다. 그때 `npm root -g` 로 전역 패키지가 사는 폴더를 묻고, 그 폴더가 정말 없으면 깔린 것이
#   없다는 잰 값이다. 폴더가 있는데 `ENOENT` 거나 그 물음이 졌으면 그대로 못 쟀다다.
function Measure-NpmGlobal([string[]]$Pkgs) {
  $probe = "npm ls -g $($Pkgs -join ' ') --depth=0 --json"
  # 물음 하나가 낸 값을 넘긴 패키지마다 — 판은 없다
  $each = { param([string]$State, [string]$P, [string]$W) $m = @{}; foreach ($k in $Pkgs) { $m[$k] = @{ State = $State; Ver = ''; Probe = $P; Why = $W } }; $m }
  $log = [IO.Path]::GetTempFileName()
  try {
    $rc = Invoke-LoggedCapped 'npm' (@('ls','-g') + $Pkgs + @('--depth=0','--json')) $log $ProbeCap
    if ($rc -eq -2) { Add-ProbeOverflow "npm ls -g $($Pkgs -join ' ')" $ProbeCap; return (& $each 'unmeasured' $probe '') }
    if ($rc -eq -1) { return (& $each 'unmeasured' $probe (Format-ProbeWhy $rc $ProbeCap)) }
    $j = $null
    try { $j = Get-Content -LiteralPath $log -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json } catch { }
    if (-not $j)   { return (& $each 'unmeasured' $probe 'JSON 을 안 내') }
    if ($j.error) {
      if ("$($j.error.code)" -eq 'ENOENT') {
        $rl = [IO.Path]::GetTempFileName()
        try {
          $rrc  = Invoke-LoggedCapped 'npm' @('root','-g') $rl $ProbeCap
          $root = ("$(@(Get-Content -LiteralPath $rl -Encoding UTF8 -ErrorAction SilentlyContinue | Where-Object { "$_".Trim() })[0])").Trim()
        } finally { Remove-Item -LiteralPath $rl, "$rl.err" -ErrorAction SilentlyContinue }
        if ($rrc -eq -2) { Add-ProbeOverflow 'npm root -g' $ProbeCap; return (& $each 'unmeasured' 'npm root -g' '') }
        if ($rrc -eq 0 -and $root -and -not (Test-Path -LiteralPath $root)) { return (& $each 'no' '' '') }
      }
      return (& $each 'unmeasured' $probe '오류를 적어')
    }
    $m = @{}
    foreach ($k in $Pkgs) {
      $d = if ($j.dependencies) { $j.dependencies.$k } else { $null }
      $m[$k] = if (-not $d) { @{ State = 'no'; Ver = ''; Probe = ''; Why = '' } }
               else { @{ State = 'yes'; Ver = ("$($d.version)").Trim(); Probe = ''; Why = '' } }
    }
    return $m
  } finally { Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue }
}

# npm 으로 까는 한 자리 — 확장과 같은 까닭이다. `$Rows` 는 고른 npm CLI 의 행(`Pkg` · `Cmd` · `Label`)이다. 깔렸나 · 깔린 판은 npm 의
#   기록(`Measure-NpmGlobal`)이 재고 그 CLI 를 띄우지 않는다(PAISetup #30 ③). 할 일은 CLI 마다 한 표(`Get-InstallAction`)가 가른다.
#   못 깐 CLI 는 빨간 줄 · `$Fails`, 못 올린 CLI 는 노란 줄이다.
# 할 일이 같은 CLI 는 npm 한 번에 넘긴다(PAISetup #35 C) — npm 을 띄울 때마다 node 가 새로 서고 레지스트리를 풀이하는 값이 CLI
#   마다 쌓인다. 묻기도 한 번씩이다: `npm --version` 하나 · 기록 읽기는 깔기 앞뒤로 하나씩. 최신 판을 묻는 `npm view` 는 패키지 하나만
#   받아 깔린 CLI 마다 묻는다.
#   묶음이 지면 하나씩 다시 깐다 — npm 은 묶음 안의 하나가 지면 묶음을 다 되돌린다. 하나씩 깔아야 진 CLI 가 제 이름 · 제 종료 값 ·
#   제 끝 줄로 서고 나머지는 깔린다. 하나만 넘긴 묶음은 다시 안 깐다.
function Install-NpmCli($Rows) {
  # ⚠ **npm 을 못 쟀으면 손대지 않는다**(결정 0141) — 기록을 못 읽은 채 깔면 깔린 것 위에 다시 깔고, 「있음」으로 끝내면 올리기가
  #   조용히 빠진다. 하지도 건너뛰지도 않고 끝 검증에 남긴다.
  $npmRuns = Measure-Runs 'npm' '--version'
  if ($npmRuns -eq 'unmeasured') {
    foreach ($r in @($Rows)) { Add-UnmeasuredStep $r.Label 'npm --version' '깔렸나 안 묻고 깔지도 올리지도 않았다' }
    return
  }
  if ($npmRuns -ne 'yes') {
    # npm 이 없으면 기록도 깔 길도 없다 — 그 이름이 서 있으면(npm 밖에서 깐 것) 있음으로 두고, 없으면 못 깐다. 이름은 찾기만 하고 안 띄운다.
    foreach ($r in @($Rows)) {
      if (Get-Command $r.Cmd -ErrorAction SilentlyContinue) {
        Write-Host "  $($r.Label) — 있음 $(Format-VerPart '') — npm 이 안 서 그 기록을 못 읽었다"
      } else {
        Write-Host "  ! npm 이 없어 $($r.Label) 를 못 깐다 — Node.js 설치부터 본다" -ForegroundColor Red
        $Fails.Add("$($r.Label) (npm 이 안 닿는다)")
      }
    }
    return
  }
  $recs = Measure-NpmGlobal @($Rows | ForEach-Object { $_.Pkg })
  $todo = @{ upgrade = @(); install = @() }
  foreach ($r in @($Rows)) {
    $Pkg = $r.Pkg; $Label = $r.Label
    $rec = $recs[$Pkg]
    $b = $rec.Ver; $rv = ''; $vrc = 0
    if ($rec.State -eq 'yes' -and -not $NoUpgrade) {
      Say-Busy $Label 'upcheck' @('npm', "지금 $(Format-VerPart $b)")     # 나가는 명령 앞의 한 줄 — 확장 칸과 같은 까닭
      # 먼저 묻고 다르면 깐다 — 판정하려고 `npm install` 을 돌리면 같은 판이어도 풀이 · 받기 · 링크를 다시 밟고, 판 하나 묻는 GET 은
      #   1초 안팎이다(사외 VDI 는 로그인마다 이 걸음을 지난다). `$NpmViewCap` 울타리를 두르고(#26), 넘기면 최신 판을 「못 쟀다」다.
      # ⚠ **묻는 것도 `@latest` 로 묻는다** — install 이 보는 태그와 다른 것을 물으면 엉뚱한 판과 견주게 되고, 그 어긋남은 「올렸는데
      #   또 올린다」로만 드러난다.
      $vl  = [IO.Path]::GetTempFileName()
      $vrc = Invoke-LoggedCapped 'npm' @('view',"$Pkg@latest",'version') $vl $NpmViewCap
      $rvo = @(Get-Content -LiteralPath $vl -Encoding UTF8 -ErrorAction SilentlyContinue | Where-Object { "$_".Trim() })[0]
      Remove-Item -LiteralPath $vl, "$vl.err" -ErrorAction SilentlyContinue
      if ($vrc -eq -2) { Add-ProbeOverflow "npm view $Pkg@latest version" $NpmViewCap }
      $rv  = if ($vrc -eq 0) { ("$rvo").Trim() } else { '' }
    }
    $cliAct = Get-InstallAction $rec.State $b $rv $null $false ([bool]$NoUpgrade)
    if ($cliAct -eq 'hold') {
      Add-UnmeasuredStep $Label $rec.Probe '깔지도 올리지도 않았다' $rec.Why
    } elseif ($cliAct -eq 'present') {
      Write-Host "  $Label — 있음 $(Format-VerPart $b)"
    } elseif ($cliAct -eq 'latest') {
      Write-Host "  $Label — 최신  $(Format-VerPart $b)"
    } elseif ($cliAct -eq 'keep') {
      # 여기서 지는 것을 실패로 세지 않는다 — 그 CLI 는 이미 깔려 깔린 판으로 돈다(저장소 `pull` 이 졌을 때와 같은 규율: 말은 하되
      #   빨강으로 안 끝낸다). 「최신」이라고도 안 찍는다 — 낡은 판이 도는 것과 못 가른다. 판을 모르면 다시 받지 않는다 — 못 닿는
      #   레지스트리에는 install 도 못 닿는다.
      if ($vrc -eq -2) {
        Write-Host "  $Label — 있음 $(Format-VerPart $b)"
        Add-UnmeasuredStep "$Label 올리기" "npm view $Pkg@latest version" '최신인지 모른 채 올리지도 않았다' (Format-ProbeWhy $vrc $NpmViewCap)
      } elseif (-not $b) {
        Write-Host "  ! $Label — 깔린 판을 못 읽었다 (``npm ls -g`` 기록에 판이 없다) · 깔린 그대로 간다" -ForegroundColor Yellow
      } else {
        Write-Host "  ! $Label — 레지스트리에 판을 못 물었다 (npm view 가 $vrc 로 끝났다) · 옛 판 $b 로 간다" -ForegroundColor Yellow
      }
    } elseif ($cliAct -eq 'upgrade' -or $cliAct -eq 'install') {
      # 깔기는 `install` 일 때만이다 — 이 갈래가 안 내는 할 일이 와도 깔린 것 위에 다시 깔지 않는다. 올리기는 묻은 태그(`@latest`)를
      #   그대로 받는다 — 위 `npm view` 와 같은 까닭.
      $spec = if ($cliAct -eq 'upgrade') { "$Pkg@latest" } else { $Pkg }
      $todo[$cliAct] += ,@{ Pkg = $Pkg; Cmd = $r.Cmd; Label = $Label; Spec = $spec; Before = $b; Latest = $rv }
    }
  }

  # 할 일마다 npm 한 번 — 묶음이 지면 하나씩. 낸 값과 뱉은 글은 CLI 마다 든다(묶음이 섰으면 묶음의 것).
  # ⚠ **종료코드를 안 버린다 — 여기는 winget 자리가 아니다.** winget 은 「올릴 것 없음」에도 0 이 아닌 값을 내지만 npm 은 지면
  #   지는 값을 낸다. 버리고 판만 견주면 설치가 죽은 판에서도 판이 안 바뀌었으니 「최신」이 찍힌다.
  $ran = @()
  foreach ($act in 'upgrade', 'install') {
    $grp = @($todo[$act])
    if (-not $grp.Count) { continue }
    $notes = @('npm')
    if ($act -eq 'upgrade') {
      $notes += @($grp | ForEach-Object { if ($grp.Count -gt 1) { "$($_.Label) $($_.Before) → $($_.Latest)" } else { "$($_.Before) → $($_.Latest)" } })
    }
    Say-Busy (@($grp | ForEach-Object { $_.Label }) -join ' · ') $act $notes
    $nl  = [IO.Path]::GetTempFileName()
    $nrc = Invoke-Logged 'npm' (@('install','-g') + @($grp | ForEach-Object { $_.Spec })) $nl
    if ($nrc -ne 0 -and $grp.Count -gt 1) {
      Write-Host "  (CLI $($grp.Count)개를 한 번에 깔다가 npm 이 $nrc 로 끝났다 — 하나씩 다시 깐다)"
      foreach ($g in $grp) {
        Say-Busy $g.Label $act @('npm')
        $g.Log = [IO.Path]::GetTempFileName()
        $g.Rc  = Invoke-Logged 'npm' @('install','-g',$g.Spec) $g.Log
      }
    } else {
      foreach ($g in $grp) { $g.Rc = $nrc; $g.Log = $nl }
    }
    foreach ($g in $grp) { $g.Act = $act }
    $ran += $grp
    if ($grp[0].Log -ne $nl) { Remove-Item -LiteralPath $nl -ErrorAction SilentlyContinue }
  }
  if (-not $ran.Count) { return }
  # ⚠ **깔고 나서 한 번 더 태운다** — `%APPDATA%\npm` 은 첫 설치가 만드는 폴더라, 맨바닥 PC 에서는 앞의 배선이 조용히 지나가고
  #   PATH 가 빈 채로 남는다. 두 번째부터는 폴더가 있어 안 드러난다.
  Update-RuntimePath
  $after = Measure-NpmGlobal @($ran | ForEach-Object { $_.Pkg })
  foreach ($g in $ran) {
    $Pkg = $g.Pkg; $Label = $g.Label; $b = $g.Before; $nrc = $g.Rc; $nl = $g.Log
    if ($g.Act -eq 'upgrade') {
      $a = $after[$Pkg].Ver
      if ($a -and $a -ne $b) { Write-Host "  $Label — 올렸다  $b  ->  $a" -ForegroundColor Green }
      elseif ($nrc -ne 0) {
        Write-Host "  ! $Label — 올리기 실패 (npm 이 $nrc 로 끝났다) · 옛 판 $b 로 간다 — 뱉은 끝 줄:" -ForegroundColor Yellow
        Show-Log $nl
      }
      else { Write-Host "  $Label — 최신  $(Format-VerPart $b)" }
      continue
    }
    # 깔렸나는 npm 이 0 으로 끝났고 그 기록에 섰나다. 판을 못 쟀으면 깔린 것은 그대로 깔린 것이다 — 「설치 실패」로 안 찍는다.
    $got = $after[$Pkg]
    if ($nrc -eq 0 -and $got.State -eq 'yes' -and $got.Ver) {
      Write-Host "  $Label — 깔았다 $(Format-VerPart $got.Ver)" -ForegroundColor Green
    } elseif ($nrc -eq 0 -and $got.State -ne 'no') {
      $gotWhy = if ($got.State -eq 'yes') { 'npm 기록에 판이 없다' }
                else { "``$($got.Probe)`` 이 $(if ($got.Why) { $got.Why } else { "${ProbeCap}초 안에 안 끝나" })서" }
      Write-Host "  $Label — 깔았다 · 판을 못 쟀다 ($gotWhy) — npm 은 0 으로 끝났다" -ForegroundColor Yellow
    } else {
      $failWhy = if ($nrc -ne 0) { "npm 이 $nrc 로 끝났다" } else { 'npm 은 0 으로 끝났는데 그 기록에 없다' }
      Write-Host "  ! $Label 설치 실패 ($failWhy) — 뱉은 끝 줄:" -ForegroundColor Red
      Show-Log $nl
      $Fails.Add($Label)
    }
  }
  Remove-Item -LiteralPath (@($ran | ForEach-Object { $_.Log }) | Select-Object -Unique) -ErrorAction SilentlyContinue
}

# winget 이 내주는 CLI(`$Clis` 의 `Via='winget'` 행)를 재고 할 일대로 깔거나 올린다. 깔렸으면 프로그램처럼 「올릴 것」 목록이
#   가른다(`Get-InstallAction`). 깔고도 이름이 안 서면 빨간 줄 · `$Fails` 다.
#   재는 자는 `winget list` 가 아니라 행의 `Arg`(없으면 `--version`)다 — CLI 는 사람이 쓸 이름이 실제로 서는가가 판정이라(winget 이 「깔았다」 해도
#   PATH 에 안 서면 못 쓴다), GUI 라 PATH 로 못 재는 데스크탑 앱(`Measure-DesktopApp`)과 다르다. winget 밖의 길로 깐 `agy` 는
#   winget 목록에 안 올라 「최신」으로 지나간다 — 도구는 멀쩡히 서 있으니 실패로 안 찍는다(`$Clis` 곁말).
function Install-WingetCli([string]$Id, [string]$Cmd, [string]$Label, [string]$Arg = '--version') {
  if (-not $Arg) { $Arg = '--version' }
  # ⚠ **못 쟀으면 깔지 않는다** — 넘김이나 선 이름의 실패를 「없다」로 읽으면 깔린 것 위에 `winget install` 을 돌린다(결정 0141 · 0145 · 0151).
  $cliRuns = Measure-Runs $Cmd $Arg
  $b = if ($cliRuns -eq 'yes') { Get-Ver $Cmd $Arg } else { '' }
  $cliAct = Get-InstallAction $cliRuns $b '' (Get-Listed $Id) $true ($NoUpgrade -or $noWinget)
  if ($cliAct -eq 'hold') {
    Add-UnmeasuredStep $Label "$Cmd $Arg" '깔지도 올리지도 않았다' '' "winget install --id $Id --force"
    return
  }
  if ($cliAct -eq 'present') { Write-Host "  $Label — 있음 $(Format-VerPart $b)"; return }
  if ($cliAct -eq 'latest')  { Write-Host "  $Label — 최신  $(Format-VerPart $b)"; return }
  if ($cliAct -eq 'upgrade' -or $cliAct -eq 'upcheck') {
    Invoke-WingetUpgrade $Label $Id 'winget' $cliAct @("지금 $b")
    Update-RuntimePath
    Write-UpgradeResult $Label $b (Get-Ver $Cmd $Arg)
    return
  }
  if ($cliAct -ne 'install') { return }
  if ($noWinget) {
    Write-Host "  ! winget 이 없어 $Label 를 못 깐다" -ForegroundColor Red
    $Fails.Add("$Label (winget 이 없다)")
    return
  }
  Say-Busy $Label 'install' @('winget')
  $wl = [IO.Path]::GetTempFileName()
  $rc = Invoke-Logged 'winget' (@('install','--id',$Id) + $WG) $wl
  # 깐 직후에는 이 창이 그 자리를 모른다 — winget 이 portable 을 심으며 손댄 PATH 는 레지스트리에만 있다.
  Update-RuntimePath
  if (Test-Runs $Cmd $Arg) {
    Write-Host "  $Label — 깔았다 $(Format-VerPart (Get-Ver $Cmd $Arg))" -ForegroundColor Green
  } else {
    # 「됐다는데 안 잡힌다」를 「안 됐다」와 갈라 적는다 — winget 이 PATH 를 안 들어 준 자리이고, 다음에 어디를 팔지가 갈린다.
    Write-Host "  ! $Label — 설치가 $rc 로 끝났는데 $Cmd 가 안 잡힌다 — 뱉은 끝 줄:" -ForegroundColor Red
    Show-Log $wl
    Write-Host "     새 터미널에서 다시 보고, 그래도 없으면:  winget install --id $Id --source winget"
    $Fails.Add("CLI ($Label)")
  }
  Remove-Item $wl -ErrorAction SilentlyContinue
}

# VC++ 런타임 파일의 자리 — 64 비트 `System32` 의 `msvcp140.dll`.
# ⚠ **32 비트 파워셸은 `System32` 를 `SysWOW64`(32 비트 런타임)로 돌려 읽는다** — 그 판에서는 `Sysnative` 로 64 비트 자리를 연다.
function Get-VcRuntimeDll {
  $sys = if ([Environment]::Is64BitOperatingSystem -and -not [Environment]::Is64BitProcess) { 'Sysnative' } else { 'System32' }
  return (Join-Path (Join-Path $env:SystemRoot $sys) $VcRuntime.Dll)
}

# 깔린 VC++ 런타임의 판을 그 파일에서 읽는다 — 아무것도 안 띄운다. `@{ State; Ver; Probe; Why }`(`Add-UnmeasuredStep` 의 꼴) — 파일이
#   없으면 `no`, 판을 읽으면 `yes`, 파일이 있는데 판을 못 읽으면 `unmeasured` 다. `$Path` 는 검사가 대역 파일을 넣는 손잡이다.
function Measure-VcRuntime([string]$Path = (Get-VcRuntimeDll)) {
  $probe = "$Path 의 파일 판"
  try {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf -ErrorAction Stop)) { return @{ State = 'no'; Ver = ''; Probe = ''; Why = '' } }
    $v = [Diagnostics.FileVersionInfo]::GetVersionInfo($Path)
    if ($v.FileMajorPart -le 0) { return @{ State = 'unmeasured'; Ver = ''; Probe = $probe; Why = '판 칸이 비어' } }
    return @{ State = 'yes'; Ver = ('{0}.{1}.{2}.{3}' -f $v.FileMajorPart, $v.FileMinorPart, $v.FileBuildPart, $v.FilePrivatePart); Probe = ''; Why = '' }
  } catch { return @{ State = 'unmeasured'; Ver = ''; Probe = $probe; Why = '오류를 던져' } }
}

# 관리자 승격이 이 PC 에서 어떻게 나나를 읽는다 — 상태만 읽고 아무것도 안 띄운다. `@{ Token; Lua; AdminPrompt; UserPrompt; AdminMode }`.
#   `Token` — `elevated`(이미 승격된 토큰) · `filtered`(관리자인데 걸러진 토큰 — 관리자 그룹이 거부 전용으로 든다) · `standard`(관리자
#   그룹이 없다) · 빈 글자(못 읽었다). 나머지 넷은 `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System` 의 `EnableLUA` ·
#   `ConsentPromptBehaviorAdmin` · `ConsentPromptBehaviorUser` · `TypeOfAdminApprovalMode` 값이고 없으면 `$null` 이다. 하나라도 던지면
#   `Token` 을 비운다 — 못 읽은 것은 창이 뜨는 판으로 친다(`Get-ElevationGo`).
function Read-ElevationState {
  $s = @{ Token = ''; Lua = $null; AdminPrompt = $null; UserPrompt = $null; AdminMode = $null }
  $base = $null; $k = $null
  try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $admins = 'S-1-5-32-544'   # BUILTIN\Administrators
    $token = if ((New-Object Security.Principal.WindowsPrincipal $id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { 'elevated' }
             elseif (@($id.Claims | Where-Object { $_.Type -eq [Security.Claims.ClaimTypes]::DenyOnlySid -and $_.Value -eq $admins }).Count) { 'filtered' }
             else { 'standard' }
    $s.Token = $token
    $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey('LocalMachine', 'Registry64')
    $k = $base.OpenSubKey('SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', $false)
    if (-not $k) { return $s }   # 키가 없으면 값이 다 없는 것이다 — 기본값으로 읽힌다
    $s.Lua         = $k.GetValue('EnableLUA', $null)
    $s.AdminPrompt = $k.GetValue('ConsentPromptBehaviorAdmin', $null)
    $s.UserPrompt  = $k.GetValue('ConsentPromptBehaviorUser', $null)
    $s.AdminMode   = $k.GetValue('TypeOfAdminApprovalMode', $null)
  } catch {
    $s.Token = ''
  } finally { if ($k) { $k.Close() }; if ($base) { $base.Close() } }
  return $s
}

# 기계 범위 설치(관리자 승격)를 이 판에서 걸어도 되나 — `go`(건다) · `later`(승인 창이 뜨는데 누를 사람이 없다 — 사람이 있는 판으로
#   미룬다) · `denied`(이 PC 에서는 승격이 안 선다). `$State` 는 `Read-ElevationState` 의 꼴, `$Attended` 는 승인 창을 눌러 줄 사람이 있는
#   판인가다.
# 창이 뜨나는 상태로 가른다 — 무인 판인가 하나로 안 가른다. 관리자를 정책이 묻지 않고 올리는 PC(`ConsentPromptBehaviorAdmin` 0)는
#   무인 판에서도 승격이 조용히 서고, 창이 뜨는 PC 의 무인 판만 그 창 앞에서 사람을 기다리며 선다(PAISetup #34 ③). 못 읽었으면
#   창이 뜨는 판으로 친다 — 무인 판을 세우는 것보다 한 판 미루는 것이 싸다.
# 값의 뜻(결정 0146 — Microsoft 「User Account Control settings and configuration」 · 「Administrator protection」 · Policy CSP):
#   `ConsentPromptBehaviorAdmin` 0 은 관리자를 묻지 않고 올린다 · 1~5 는 묻는다 · 없으면 5
#   `ConsentPromptBehaviorUser` 0 은 표준 사용자의 승격을 자동으로 거절한다 · 1 · 3 은 관리자 자격을 묻는다 · 없으면 3
#   `EnableLUA` 0 은 승인 모드가 꺼진 PC 다 — 관리자는 늘 승격된 토큰이고(`elevated`) 표준 사용자는 승격할 길이 없다 · 없으면 1
#   `TypeOfAdminApprovalMode` 2 는 관리자 보호 — 승격마다 사람이 확인한다(자동 승격이 없다) · 없으면 1
function Get-ElevationGo($State, [bool]$Attended) {
  $way = 'prompt'
  if ($State.Token -eq 'elevated') { $way = 'silent' }
  elseif ($State.Token -eq 'filtered') { if ($State.AdminMode -ne 2 -and $State.AdminPrompt -eq 0) { $way = 'silent' } }
  elseif ($State.Token -eq 'standard') { if ($State.Lua -eq 0 -or $State.UserPrompt -eq 0) { $way = 'denied' } }
  if ($way -eq 'silent') { return 'go' }
  if ($way -eq 'denied') { return 'denied' }
  if ($Attended) { return 'go' }
  return 'later'
}

# VC++ 런타임을 `$VcRuntimeMin` 이상으로 세운다 — 판은 그 파일에서 읽고(`Measure-VcRuntime`), 할 일은 한 표(`Get-InstallAction`)가 가르고,
#   승격은 `Get-ElevationGo` 가 가른다. `$Attended` 는 승인 창을 눌러 줄 사람이 있는 판인가다. 오르면 초록 한 줄, 못 올리면 그 까닭 ·
#   그대로 서는 것 · 사람이 할 일을 한 줄로 말하고 `$Fails` 에 하나를 넣는다 — 승인 창이 뜨는데 사람이 없는 판은 노란 줄만 낸다(끝 검증의
#   `[X]` 가 그 판의 빨강을 든다).
# ⚠ **올랐나는 파일이 가른다 — winget 이 낸 값이 아니다.** 낸 값은 안 오른 까닭의 말만 고른다(`$VcRedistRc*`).
# ⚠ **`-NoUpgrade` 로 안 건너뛴다** — 새 판을 따라가는 일이 아니라 그 판 아래에서 죽는 것을 막는 일이다(Node 신뢰 배선과 같은 규율).
function Install-VcRuntime([bool]$Attended) {
  $L = $VcRuntime.Name
  $hand = "winget install --id $($VcRuntime.Id) --exact --source winget"
  $m = Measure-VcRuntime
  # 「올릴 것인가」의 답은 winget 목록이 아니라 문턱이 든다
  $below = if ($m.State -eq 'yes') { [version]$m.Ver -lt $VcRuntimeMin } else { $null }
  $act = Get-InstallAction $m.State $m.Ver '' $below $false $false
  if ($act -eq 'hold') { Add-UnmeasuredStep $L $m.Probe '깔지도 올리지도 않았다' $m.Why; return }
  if ($act -eq 'latest') { Write-Host "  $L — 있음  $(Format-VerPart $m.Ver) · $VcRuntimeMin 이상"; return }
  if ($act -ne 'install' -and $act -ne 'upgrade') { return }
  $now = if ($m.Ver) { "지금 $($m.Ver)" } else { '없다' }
  $still = '나머지 설치는 그대로 간다 · 이 런타임에 기대는 파이썬 패키지(markitdown · PPT 검수)만 이 PC 에서 import 하다 죽는다'
  if ($noWinget) {
    Write-Host "  ! $L — $now · $VcRuntimeMin 보다 낮은데 winget 이 없어 못 올린다 · $still · IT 에 「Microsoft Visual C++ 재배포 가능 패키지(x64) $VcRuntimeMin 이상」을 요청한다" -ForegroundColor Red
    $Fails.Add("$L (winget 이 없다)")
    return
  }
  $elevGo = Get-ElevationGo (Read-ElevationState) $Attended
  if ($elevGo -eq 'denied') {
    Write-Host "  ! $L — $now · $VcRuntimeMin 보다 낮은데 이 PC 는 관리자 승격이 안 선다 · $still · IT 에 「Microsoft Visual C++ 재배포 가능 패키지(x64) $VcRuntimeMin 이상」을 요청한다" -ForegroundColor Red
    $Fails.Add("$L (관리자 승격이 안 서는 PC — IT 에 요청)")
    return
  }
  if ($elevGo -eq 'later') {
    Write-Host "  ! $L — $now · $VcRuntimeMin 보다 낮다 · 관리자 승인 창이 뜨는 PC 인데 누를 사람이 없는 판이라 안 올렸다 · 설치 창으로 다시 누르면 승인 창이 한 번 뜬다 (손으로: $hand)" -ForegroundColor Yellow
    return
  }
  Say-Busy $L $act @('winget', $now, '관리자 승인이 들 수 있다')
  $log = [IO.Path]::GetTempFileName()
  $rc = Invoke-LoggedCapped 'winget' (@('install','--id',$VcRuntime.Id) + $WG) $log $VcRedistCap
  if ($rc -eq -2) { Add-ProbeOverflow "winget install --id $($VcRuntime.Id)" $VcRedistCap }
  $after = Measure-VcRuntime
  if ($after.State -eq 'yes' -and [version]$after.Ver -ge $VcRuntimeMin) {
    if ($m.Ver) { Write-Host "  $L — 올렸다  $($m.Ver)  ->  $($after.Ver)" -ForegroundColor Green }
    else        { Write-Host "  $L — 깔았다 $(Format-VerPart $after.Ver)" -ForegroundColor Green }
  } else {
    $fileNow = if ($after.State -eq 'yes') { "파일은 $($after.Ver)" } elseif ($after.State -eq 'no') { '파일이 없다' } else { '파일의 판을 못 읽었다' }
    if ($rc -eq -2) {
      Write-Host "  ! $L — 올리지 못했다: winget 이 $(Format-ProbeWhy $rc $VcRedistCap)서 거뒀다(승인 창이 사람을 기다렸을 수 있다) · $fileNow · $still · 설치 창으로 다시 누르거나 손으로: $hand" -ForegroundColor Red
      $Fails.Add("$L (winget 이 ${VcRedistCap}초 안에 안 끝났다)")
    } elseif ($VcRedistRcReboot -contains $rc) {
      Write-Host "  ! $L — winget 이 PC 를 다시 시작해야 끝난다고 했다($(Format-ProbeWhy $rc 0)서) · $fileNow · 다시 시작한 뒤 설치를 다시 누르면 선다 · $still" -ForegroundColor Red
      $Fails.Add("$L (PC 를 다시 시작해야 선다)")
    } elseif ($VcRedistRcCancelled -contains $rc) {
      Write-Host "  ! $L — 관리자 승인이 안 나서 못 올렸다($now) · $still · 승인할 수 있을 때 설치를 다시 누르거나 손으로: $hand" -ForegroundColor Red
      $Fails.Add("$L (관리자 승인이 안 났다)")
    } elseif ($VcRedistRcNewer -contains $rc) {
      Write-Host "  ! $L — winget 은 같거나 더 새 판이 이미 깔렸다고 하는데 $fileNow — 다시 시작이 남았을 수 있다 · 다시 시작해도 그대로면 「설정 → 앱」에서 Microsoft Visual C++ 2015-2022 재배포 가능 패키지(x64)를 「수정」한다 · $still" -ForegroundColor Red
      $Fails.Add("$L (winget 은 깔렸다는데 파일이 옛 판이다)")
    } else {
      Write-Host "  ! $L — 올리지 못했다(winget 이 $(Format-ProbeWhy $rc 0)서) · $fileNow · $still — 뱉은 끝 줄:" -ForegroundColor Red
      Show-Log $log
      Write-Host "     손으로:  $hand"
      $Fails.Add("$L (winget 이 $rc 로 끝났다)")
    }
  }
  Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue
}

#endregion 깔기

#region 칸 없이 까는 스킬 — 제작자 칸에 안 든 도구의 홈에 고른 제품이 부르는 스킬을 깔고, 우리 기록에서 이번에 안 까는 것을 걷는다

# 짐의 갈 곳 표(`tool-homes.conf`)에서 칸 없이 까는 걸음이 쓰는 두 사실을 읽는다 — 도구마다 스킬 홈과 기록 자리(`was <대상> <기록>
#   shared` 줄 · 그 대상으로 가는 `route <항목> <도구> copy <대상>` 줄이 도구 이름을 댄다)와, 그 홈에 안 놓는 이름(`not <항목> <이름>
#   <도구 | *>`). 두 사실은 손(`tool-homes.py`)이 칸을 켠 홈에서 같은 줄로 쓴다 — 칸을 켜고 끌 때 손과 이 걸음이 같은 기록을 넘겨받고,
#   받는 쪽 홈에 러너가 안 가는 것이 두 손에서 같다. 그래서 여기 다시 적지 않고 표에서 짓는다(PAISetup #47 ⑤).
# 표의 꼴(주석은 `#` 로 여는 줄 전체 · 칸은 빈칸으로 가른다)은 표 머리가 든다. 여기는 세 낱말의 줄만 읽고 나머지 줄은 안 본다 —
#   표의 다른 줄을 가르는 것은 손의 몫이다. 파이썬을 안 부른다 — 칸 없이 까는 걸음은 Codex · agy 만 고른 PC(파이썬이 안 깔릴 수
#   있다)에서도 돈다.
# 내는 것 — @{ Homes = @{ <도구> = @{ Skills; Ledger; Root; Not } }; Why }. Root 는 기록이 든 폴더(백업의 뿌리)다. 표가 없거나 못
#   읽으면 Homes 가 비고 Why 가 까닭이다 — 그 홈은 부르는 쪽이 빨간 줄로 댄다.
function Read-FreeSkillTable([string]$Table) {
  $t = @{ Homes = @{}; Why = '' }
  $lines = $null
  try { $lines = [IO.File]::ReadAllLines($Table, [Text.Encoding]::UTF8) } catch { $t.Why = "갈 곳 표를 못 읽었다 ($Table · $(Say-Why $_))"; return $t }
  $expand = { param([string]$p)
    $p = $p.TrimEnd('/')
    if ($p.StartsWith('~/')) { $p = Join-Path $env:USERPROFILE ($p.Substring(2).Replace('/', '\')) }
    $p }
  $routes = @(); $wases = @(); $nots = @()
  foreach ($ln in $lines) {
    $s = $ln.Trim()
    if (-not $s -or $s.StartsWith('#')) { continue }
    $f = @($s -split '\s+')
    if ($f[0] -ceq 'route' -and $f.Count -ge 6 -and $f[3] -ceq 'copy') { $routes += @{ Item = $f[1]; Tool = $f[2]; At = $f[4].TrimEnd('/') } }
    elseif ($f[0] -ceq 'was' -and $f.Count -ge 4 -and $f[3] -ceq 'shared') { $wases += @{ At = $f[1].TrimEnd('/'); Ledger = $f[2] } }
    elseif ($f[0] -ceq 'not' -and $f.Count -ge 4) { $nots += @{ Item = $f[1]; Name = $f[2]; Tool = $f[3] } }
  }
  foreach ($w in $wases) {
    $r = @($routes | Where-Object { $_.At -ceq $w.At }) | Select-Object -First 1
    if (-not $r) { continue }
    $ledger = & $expand $w.Ledger
    $t.Homes[$r.Tool] = @{ Skills = (& $expand $w.At); Ledger = $ledger; Root = (Split-Path $ledger -Parent)
                           Not = @($nots | Where-Object { $_.Item -ceq $r.Item -and ($_.Tool -ceq $r.Tool -or $_.Tool -ceq '*') } | ForEach-Object { $_.Name }) }
  }
  if (-not $t.Homes.Count) { $t.Why = "갈 곳 표에 칸 없이 까는 걸음이 쓸 기록 줄(was … shared)이 없다 ($Table)" }
  return $t
}

# 그 도구 홈에 깔 이름 — `$FreeSkills` 의 그 도구 칸(`Claude` · `Codex` · `Agy`)이 참이고, 갈 곳 표가 그 홈에 안 놓는다고 하지 않은
#   것. 까는 칸과 끝 검증이 같은 목록을 쓴다.
function Get-FreeSkillNames([string]$Tool) {
  $not = @($FreeSkillHomes[$Tool].Place.Not)
  return @($FreeSkills.Keys | Where-Object { $FreeSkills[$_].$Tool -and $not -notcontains $_ })
}

# 한 도구 홈의 칸 없이 까는 걸음 — 고르기(`Get-FreeSkillNames`) · 깔기 · 기록 맞추기. 홈의 자리는 `$FreeSkillHomes` 의 `Place`(갈 곳
#   표에서 지었다)가 든다. 짐에 없는 스킬 · 표에 자리가 없는 홈은 빨간 줄 · `$Fails` 다.
# ⚠ **한 스킬 폴더에 쓰는 자는 하나다.** 그 도구가 제작자 칸에 들면(`Box`) 손(`tool-homes.py`)이 짐 · 저장소의 스킬을 다 놓으므로
#   이 함수는 그 홈을 안 건드린다 — 안 깔고 · 안 걷고 · 기록을 안 쓴다. 칸에 안 들면 이 함수만 그 홈에 스킬을 쓴다.
#   · 우리 것은 이 설치기의 기록(`.paisetup-skills`)에 든 이름뿐이다 — 그 홈에는 사람이나 다른 도구가 둔 스킬이 섞여 산다. 깔
#     자리에 기록에 없는 같은 이름의 폴더가 있으면 통째로 백업 자리(`<Root>/backups/install-aside-<시각>/`)로 옮긴 뒤 깔고(그 위에
#     복사하면 남의 파일과 섞인다) 노란 줄로 알린다. 기록이 없는 홈에는 우리 것이 없다 — 깔 이름이 아닌 폴더는 이름이 무엇이든
#     안 건드린다
#   · 우리 폴더는 거울로 깐다 — 짐의 그 스킬에서 빠진 파일은 홈의 그 폴더에서도 빠진다(`__pycache__` 는 안 본다). 덧붙이기만 하면
#     짐이 스킬 안의 파일을 걷은 날부터 낡은 파일이 그 스킬에 남는다(PAISetup #44 ⑮). 못 걷은 파일은 빨간 줄 · `$Fails` 다
#   · 남길 목록은 이번에 깔 목록뿐이다 — 기록에 있는데 이번 목록에 없는 이름(짐에서 빠진 것 · 지난 판이 짐에서 깐 제작자 스킬 ·
#     고른 제품이 더는 안 부르는 것)은 `<Root>/backups/install-skills-<시각>/` 로 옮긴다. 지우지 않는다 — 같은 이름을 사람이 손수
#     두었을 수도 있다. 깔 것이 없는 판도 기록을 맞추고, 기록도 깔 것도 없는 홈은 안 건드린다(그 도구를 안 쓰는 PC 에 홈을 안 짓는다)
# 기록에 적는 것 — 이번에 깐 이름 더하기, 앞 기록 가운데 이번 목록에 남은 이름(짐에 없어 못 깐 이름도 빠지지 않는다). BOM
#   없는 UTF-8 · 한 줄에 이름 하나(이름이 한글이어도 읽힌다). 백업 자리는 매번 새로 잡는다(`Get-FreePath`) — 같은 초에 두 번
#   돌아도 앞 백업 안으로 옮겨 들어가지 않는다.
# 짝 — 설정 저장소 `scripts/check-free-skills.ps1` 이 이 함수를 떼어 가짜 홈에 부른다.
function Install-FreeSkills([string]$Tool) {
  $h = $FreeSkillHomes[$Tool]
  if ($h.Box) { return }
  $names = @(Get-FreeSkillNames $Tool)
  $p     = $h.Place
  if (-not $p) {
    if ($names.Count) {
      $why = if ($FreeSkillTable.Why) { $FreeSkillTable.Why } else { '갈 곳 표에 이 홈의 기록 줄(was … shared)이 없다' }
      Write-Host "  ! $($h.Label) — 스킬 자리를 몰라 못 깐다: $why" -ForegroundColor Red
      $Fails.Add("$($h.Label) 스킬 (갈 곳 표에 자리가 없음)")
    }
    return
  }
  $ledger    = $p.Ledger
  $hasLedger = Test-Path -LiteralPath $ledger -PathType Leaf
  if (-not $hasLedger -and -not $names.Count) { return }
  $ours    = @(if ($hasLedger) { [IO.File]::ReadAllLines($ledger) | ForEach-Object { $_.Trim() } | Where-Object { $_ } })
  $backups = Join-Path $p.Root 'backups'
  $aside   = $null
  $done    = @()
  foreach ($n in $names) {
    $from = Join-Path $KitSkills $n
    if (-not (Test-Path -LiteralPath (Join-Path $from 'SKILL.md'))) {
      Write-Host "  ! $($h.Label) 스킬 $n — 짐에 없다" -ForegroundColor Red
      $Fails.Add("$($h.Label) 스킬 $n (짐에 없음)")
      continue
    }
    $to = Join-Path $p.Skills $n
    if ((Test-Path -LiteralPath $to) -and ($ours -notcontains $n)) {
      if (-not $aside) {
        $aside = Get-FreePath (Join-Path $backups ('install-aside-' + (Get-Date -Format 'yyyyMMdd-HHmmss')))
        New-Item -ItemType Directory -Path $aside -Force | Out-Null
      }
      Move-Item -LiteralPath $to -Destination (Join-Path $aside $n) -Force
      Write-Host "  ! $($h.Label) 스킬 $n — 같은 이름의 폴더가 우리 기록에 없어 통째로 옮겨 두고 깐다 (옮긴 자리: $aside)" -ForegroundColor Yellow
    }
    New-Item -ItemType Directory -Path $to -Force | Out-Null
    Copy-Item -Path (Join-Path $from '*') -Destination $to -Recurse -Force
    # 거울 — 여기까지 온 폴더는 우리 것이다(없었다 · 기록에 들었다 · 방금 비켜 두고 새로 지었다)
    $toFull = (Get-Item -LiteralPath $to).FullName.TrimEnd('\')
    $stale = @(Get-ChildItem -LiteralPath $toFull -Recurse -File -Force -ErrorAction SilentlyContinue |
               Where-Object { $_.FullName -notmatch '[\\]__pycache__[\\]' -and
                              -not (Test-Path -LiteralPath (Join-Path $from $_.FullName.Substring($toFull.Length + 1)) -PathType Leaf) })
    $staleFail = @()
    foreach ($x in $stale) {
      try { Remove-Item -LiteralPath $x.FullName -Force -ErrorAction Stop }
      catch { $staleFail += $x.FullName.Substring($toFull.Length + 1) }
    }
    foreach ($d in @(Get-ChildItem -LiteralPath $toFull -Recurse -Directory -Force -ErrorAction SilentlyContinue | Sort-Object { $_.FullName.Length } -Descending)) {
      if (-not (Get-ChildItem -LiteralPath $d.FullName -Force -ErrorAction SilentlyContinue | Select-Object -First 1)) {
        Remove-Item -LiteralPath $d.FullName -Force -ErrorAction SilentlyContinue
      }
    }
    if ($staleFail.Count) {
      Write-Host "  ! $($h.Label) 스킬 $n — 짐에서 빠진 파일을 못 걷었다: $($staleFail -join ' · ')" -ForegroundColor Red
      $Fails.Add("$($h.Label) 스킬 $n (짐에서 빠진 파일 걷기)")
    }
    $swept = $stale.Count - $staleFail.Count
    Write-Host "  $($h.Label) 스킬 $n — 깔았다$(if ($swept) { " (짐에서 빠진 파일 $swept 개를 걷었다)" })" -ForegroundColor Green
    $done += $n
  }
  $gone = @($ours | Where-Object { $names -notcontains $_ } |
            Where-Object { Test-Path -LiteralPath (Join-Path $p.Skills $_) -PathType Container })
  if ($gone.Count) {
    $bk = Get-FreePath (Join-Path $backups ('install-skills-' + (Get-Date -Format 'yyyyMMdd-HHmmss')))
    New-Item -ItemType Directory -Path $bk -Force | Out-Null
    foreach ($n in $gone) {
      Move-Item -LiteralPath (Join-Path $p.Skills $n) -Destination (Join-Path $bk $n) -Force
      Write-Host "  $($h.Label) 스킬 $n — 이번에 깔 목록에 없어 걷었다 (옮긴 자리: $bk)" -ForegroundColor Green
    }
  }
  $keep = @(@($ours | Where-Object { $names -contains $_ }) + $done | Select-Object -Unique)
  New-Item -ItemType Directory -Path $p.Root -Force | Out-Null
  [IO.File]::WriteAllLines($ledger, [string[]]$keep, (New-Object Text.UTF8Encoding($false)))
}

#endregion 칸 없이 까는 스킬

#region 도구 홈의 규범 · 룰 · 스킬 — 손(`tool-homes.py`)을 부르고, 뱉은 줄을 화면과 끝 검증의 꼴로 옮긴다

# 무엇이 어느 도구 홈에 어떤 꼴로 가나는 짐의 표(`tool-homes.conf`)와 손(`tool-homes.py`)만 안다(claude-config 결정 0112).
#   이 설치기는 그 사실을 안 들고 손을 부를 뿐이다. 줄의 꼴(`CHANGE=` · `WARN=` · `ERROR=` · `CHANGED=`)과 종료 값의 뜻은
#   손의 머리말이 들고, 그 꼴을 읽는 자리는 이 절의 세 함수뿐이다.

# 손을 한 번 부른다 — 돌려주는 것은 종료 값(`Rc` · 못 불렀으면 -1) · 뱉은 줄 전부(`Lines`) · `CHANGE=` 줄(`Changes`) ·
#   `ERROR=` 의 까닭(`Errors`). 판정이 종료 값에 서므로 `Invoke-Logged` 로 부른다(`Start-Process -PassThru` 가 아니다).
# `$CapSec` 를 주면 울타리 손(`Invoke-LoggedCapped`)으로 부른다 — 읽기만 하는 `check` 의 몫이다. 넘기면 `Rc` 가 -2 다. 홈을 쓰는 부름에는
#   안 준다 — 쓰다 거두면 반쯤 놓인 홈이 남는다.
function Invoke-ToolHomes([string]$Hand, [string[]]$HandArgs, [int]$CapSec = 0) {
  $log = [IO.Path]::GetTempFileName()
  if ($CapSec -gt 0) {
    $rc = Invoke-LoggedCapped 'python' (@('-X', 'utf8', $Hand) + $HandArgs) $log $CapSec
    # 갈라 받은 오류 줄을 한 파일 꼴로 잇는다 — 꼴 밖의 줄(파이썬이 못 뜬 까닭)이 까닭으로 쓰인다. 자식이 쓴 바이트 그대로라(`-X utf8`)
    #   UTF-8 로 읽는다 — `*>` 가 짓는 파일과 달리 BOM 이 없어 이 파워셸의 기본(ANSI)으로 읽으면 한글이 깨진다
    $lines = @(@(Get-Content -LiteralPath $log, "$log.err" -Encoding UTF8 -ErrorAction SilentlyContinue) | ForEach-Object { "$_".TrimEnd() } | Where-Object { $_ })
  } else {
    $rc = Invoke-Logged 'python' (@('-X', 'utf8', $Hand) + $HandArgs) $log
    $lines = @(Get-Content -LiteralPath $log -ErrorAction SilentlyContinue | ForEach-Object { "$_".TrimEnd() } | Where-Object { $_ })
  }
  Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue
  return @{
    Rc      = $rc
    Lines   = $lines
    Changes = @($lines | Where-Object { $_ -like 'CHANGE=*' })
    Errors  = @($lines | Where-Object { $_ -like 'ERROR=*' } | ForEach-Object { $_.Substring('ERROR='.Length) })
  }
}

# 손의 줄을 이 설치기의 꼴로 찍는다 — `CHANGE=` 은 칸 셋(동사 · 자리 · 까닭)을 한 줄로, `WARN=` 은 노랑, `ERROR=` 은 빨강,
#   꼴 밖의 줄(파이썬이 못 뜬 까닭 같은)은 그대로. 초록 · 빨강 판정은 부르는 자리가 종료 값과 `Errors` 로 내린다.
function Show-ToolHomesLines([string[]]$Lines) {
  foreach ($ln in @($Lines)) {
    if ($ln -like 'CHANGED=*') { continue }
    if ($ln -like 'CHANGE=*') {
      $f = @($ln.Substring('CHANGE='.Length).Split("`t"))
      $where = if ($f.Count -gt 1) { " $($f[1])" } else { '' }
      $why = if ($f.Count -gt 2) { " — $($f[2])" } else { '' }
      Write-Host "     $($f[0])$where$why"
    } elseif ($ln -like 'WARN=*') {
      Write-Host "     ! $($ln.Substring('WARN='.Length))" -ForegroundColor Yellow
    } elseif ($ln -like 'ERROR=*') {
      Write-Host "     ! $($ln.Substring('ERROR='.Length))" -ForegroundColor Red
    } else {
      Write-Host "     $ln"
    }
  }
}

# 끝 검증 한 칸 — 손의 `check` 를 한 번 부르고 `$checks` 의 꼴로 돌려준다. 0 홈이 표대로다 · 1 다르다(바꿀 자리와 막힌
#   까닭을 댄다) · 그 밖은 못 쟀다(짐에 손이 없다 · 층이나 표가 없다 · 손이 못 떴다) — 못 잰 것도 [X] 다. 울타리를 넘긴 것만 [?] 다
#   (그 칸이 든 물음이 멎었을 뿐 홈은 모른다 — 결정 0141).
function Get-ToolHomesCheck([string]$Hand) {
  $name = '규범 · 룰 · 에이전트 · 스킬'
  if (-not (Test-Path -LiteralPath $Hand -PathType Leaf)) { return @{ Name = "$name (못 쟀다 — 짐에 손이 없다: $Hand)"; Ok = $false } }
  # 울타리 안에서 묻는다(`$ToolHomesCheckCap`) — 멎은 python 하나가 검증을 영구히 세운다(#26 과 같은 꼴). 넘기면 「못 쟀다」 칸이다
  $Result = Invoke-ToolHomes $Hand @('check') $ToolHomesCheckCap
  if ($Result.Rc -eq -2) {
    Add-ProbeOverflow 'python tool-homes.py check' $ToolHomesCheckCap
    return @{ Name = $name; State = 'unmeasured'; Probe = 'python tool-homes.py check'; Why = (Format-ProbeWhy -2 $ToolHomesCheckCap) }
  }
  if ($Result.Rc -eq 0) { return @{ Name = "$name (홈이 tool-homes.conf 대로다)"; Ok = $true } }
  if ($Result.Rc -eq 1) {
    $places = @($Result.Changes | ForEach-Object { @($_.Split("`t"))[1] } | Where-Object { $_ } | Select-Object -Unique)
    $shown = @($places) + @($Result.Errors)
    return @{ Name = "$name (홈이 tool-homes.conf 와 다르다 — $($shown -join ' · '))"; Ok = $false }
  }
  $other = @($Result.Lines | Where-Object { $_ -notmatch '^(CHANGE|CHANGED|WARN|ERROR)=' })
  $why = if ($Result.Errors.Count) { $Result.Errors[-1] }
         elseif ($Result.Rc -eq -1) { 'python 을 못 불렀다' }
         elseif ($other.Count) { $other[0].Trim() }
         else { "종료 $($Result.Rc)" }
  return @{ Name = "$name (못 쟀다 — $why)"; Ok = $false }
}

#endregion 도구 홈의 규범 · 룰 · 스킬

#region 도구별 · Claude — 구독 로그인을 재고, 끝 검증이 Claude 홈 설정의 훅 등록을 되읽는다

# Claude 구독 로그인이 섰나 — `claude auth status` 가 `"loggedIn": true` 를 내면 참이다. CLI 가 안 서거나 넘기면 거짓이다.
#   `--version` 이 선 뒤 다시 부르는 자리라 `$ProbeCap` 울타리를 두르고(#26), 넘김은 `$script:ProbeTimedOut` 에 남아 부르는 자리가
#   그 수로 「못 쟀다」를 가른다 — 거짓을 「로그인 안 됨」으로 읽어 창을 띄우지 않게.
function Test-ClaudeLoggedIn {
  if (-not (Test-Runs 'claude' '--version')) { return $false }
  $log = [IO.Path]::GetTempFileName()
  try {
    $rc = Invoke-LoggedCapped 'claude' @('auth','status') $log $ProbeCap
    if ($rc -eq -2) { Add-ProbeOverflow 'claude auth status' $ProbeCap; return $false }
    $said = (Get-Content -LiteralPath $log -Encoding UTF8 -ErrorAction SilentlyContinue | Out-String)
    return ($said -match '"loggedIn"\s*:\s*true')
  } catch { return $false }
  finally { Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue }
}

# Claude 훅 껍데기의 등록 머리말 — {열쇠: 값}. 파일을 못 읽으면 $null.
# 꼴과 뜻은 짐의 갈 곳 표(`tool-homes.conf`) 머리의 hook 꼴이 든다 — 맨 위(셔뱅 줄 다음)에 잇달아 선 `# <열쇠> = <값>` 줄들이고, 그
#   꼴이 아닌 줄에서 끝난다. 등록을 짓는 것은 손(`tool-homes.py`)이고, 여기는 끝 검증이 그 등록을 손과 따로 재려고 읽는다.
function Get-HookHead([string]$Path) {
  $lines = $null
  try { $lines = [IO.File]::ReadAllLines($Path) } catch { return $null }
  $head = @{}
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($i -eq 0 -and $lines[0].StartsWith('#!')) { continue }
    $m = [regex]::Match($lines[$i], '^# ([A-Za-z]+(?:\.[A-Za-z]+)?) = (\S.*?)\s*$')
    if (-not $m.Success) { break }
    $head[$m.Groups[1].Value] = $m.Groups[2].Value
  }
  return $head
}

# 껍데기 하나의 등록을 홈 설정에서 되읽는다 — 끝 검증의 배선 · matcher 줄이 쓴다. 머리말의 이벤트마다 우리 꼴의 훅이 있고 그 훅이
#   가리키는 폴더에 이 껍데기가 있나, 우리 항목의 matcher 가 머리말과 같나를 잰다.
#   머리말은 등록이 가리키는 폴더의 껍데기에서 읽는다 — 이긴 층(사용자 PC 는 개인 층)의 머리말로 놓였기 때문이다. 가리키는
#   껍데기가 없으면 짐의 사본(`$KitShell`)에서 읽는다.
#   우리 꼴은 표 머리의 hook 명령 꼴이다 — `<변수>="<폴더>"; [ -f "$<변수>/<껍데기>" ] || exit 0; . "$<변수>/<껍데기>"`(가드와 끝
#   주석은 없어도 된다). 같은 항목에 든 남의 훅은 안 센다.
# ⚠ **UserPromptSubmit 항목에는 matcher 키가 없어야 한다** — 그 이벤트는 matcher 를 안 받고, 키가 있으면 거는 자가 항목째
#   걸러낸다(claude-config #120). 손이 고정으로 드는 규칙이라 머리말에 안 든다.
# `$Cfg` 는 `ConvertFrom-Json` 으로 읽은 홈 설정(못 읽었으면 $null)이다. 돌려주는 것 — Events(머리말의 이벤트) · Missing(우리 훅이
#   없거나 그 훅이 껍데기 없는 폴더를 가리키는 이벤트) · BadMatcher(어긋난 matcher 의 까닭) · Why(머리말을 못 읽은 까닭).
function Get-ClaudeHookWiring($Cfg, [string]$Shell, [string]$KitShell) {
  $form = '^\s*([A-Za-z_][A-Za-z0-9_]*)="([^"]*)";\s*(?:\[ -f "\$\1/([^"/]+)" \] \|\| exit 0;\s*)?\.\s+"\$\1/([^"/]+)"\s*(?:#.*)?$'
  $ours = @()
  if ($Cfg -and $Cfg.PSObject.Properties['hooks'] -and $Cfg.hooks) {
    foreach ($ev in @($Cfg.hooks.PSObject.Properties)) {
      foreach ($entry in @($ev.Value)) {
        if (-not $entry -or -not $entry.PSObject.Properties['hooks']) { continue }
        foreach ($h in @($entry.hooks)) {
          if (-not $h -or -not $h.PSObject.Properties['command']) { continue }
          $m = [regex]::Match([string]$h.command, $form)
          if (-not $m.Success -or $m.Groups[4].Value -cne $Shell) { continue }
          if ($m.Groups[3].Success -and $m.Groups[3].Value -cne $Shell) { continue }
          # 문자열로 잇는다 — `Join-Path` 는 없는 드라이브(`Q:/…`)에서 던지고, 전역 Stop 아래라 설치가 통째로 선다.
          $there = $false
          try { $there = Test-Path -LiteralPath "$($m.Groups[2].Value)/$Shell" -PathType Leaf } catch { $there = $false }
          $ours += @{ Event = $ev.Name; Entry = $entry; Folder = $m.Groups[2].Value; There = $there }
        }
      }
    }
  }
  $live = @($ours | Where-Object { $_.There })
  $headAt = if ($live.Count) { "$($live[0].Folder)/$Shell" } else { $KitShell }
  $head = Get-HookHead $headAt
  $out = @{ Events = @(); Missing = @(); BadMatcher = @(); Why = '' }
  if (-not $head -or -not $head.ContainsKey('events')) {
    $out.Why = "껍데기 $Shell 의 등록 머리말을 못 읽었다 ($headAt)"
    return $out
  }
  $out.Events = @($head['events'].Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  foreach ($ev in $out.Events) {
    if (-not @($live | Where-Object { $_.Event -ceq $ev }).Count) { $out.Missing += $ev }
    foreach ($o in @($ours | Where-Object { $_.Event -ceq $ev })) {
      $hasKey = [bool]$o.Entry.PSObject.Properties['matcher']
      if ($ev -ceq 'UserPromptSubmit') {
        if ($hasKey) { $out.BadMatcher += "$ev 에 matcher 가 달렸다" }
        continue
      }
      $want = if ($head.ContainsKey("matcher.$ev")) { $head["matcher.$ev"] } else { $head['matcher'] }
      $got = if ($hasKey) { [string]$o.Entry.matcher } else { '<키 없음>' }
      if ($got -cne $want) { $out.BadMatcher += "$ev matcher 가 '$got' — 머리말은 '$want'" }
    }
  }
  return $out
}

#endregion 도구별 · Claude

#region 도구별 · Codex · agy 훅 — 고르지 않은 도구에서 우리 훅을 걷는다

# 걷는 손은 씨앗의 Codex 병합기 · agy 어댑터의 걷기 판이다 — 무엇이 우리 것이고 남의 훅과 그 자리를 어떻게 지키나는 그 파일의
#   머리말이 든다. 여기는 부를지 가르고 뱉은 줄을 화면에 옮긴다. `$Parts` 는 있어야 부르는 씨앗 파일이고 맨 앞이 걷는 손이다.
#   · 설정 파일(`$Config`)이 없으면 안 부른다 — 걷을 것이 없고, 그 도구를 안 쓰는 PC 에 그 도구의 파일을 짓지 않는다
#   · 파이썬은 걷는 손이 드는 판으로 묻는다(`$Probe` — `python` 에 줄 인자 · 0 으로 끝나야 선다). 안 서면 노랑 한 줄로 건너뛴다 —
#     고르지 않은 도구라 이 칸 때문에 파이썬을 깔지 않고, 남은 우리 훅은 그 도구를 다시 고르면 그대로 쓰인다
#   · 못 걷으면 빨강 · `$Fails` 로 세고 설치는 잇는다 — 걷는 손은 못 걷으면 파일을 안 고친다(`ERROR=` · 종료 1)
function Remove-UnpickedHooks([string]$Label, [string]$Config, [string[]]$Parts, [string[]]$HandArgs, [string[]]$Probe,
                              [string]$ProbeWhat) {
  if (-not (Test-Path -LiteralPath $Config -PathType Leaf)) { return }
  $gone = @($Parts | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
  if ($gone.Count) {
    Write-Host "  ! $Label — 고르지 않았는데 씨앗에 걷는 손이 없어 못 걷었다 ($($gone -join ' · '))" -ForegroundColor Red
    $script:Fails.Add("$Label 걷기 (씨앗이 없다)")
    return
  }
  # 파이썬을 묻는 한 번에도 울타리를 두른다 — 멎으면 그 판을 못 잰 것이라 걷지도 건너뛰지도 않고 「안 한 걸음」으로 남긴다(결정 0141).
  #   걷는 손(아래 `Invoke-Logged`)에는 안 두른다 — 쓰다 거두면 반쯤 고친 설정이 남는다
  $pl = [IO.Path]::GetTempFileName()
  try { $prc = Invoke-LoggedCapped 'python' $Probe $pl $ProbeCap } finally { Remove-Item -LiteralPath $pl, "$pl.err" -ErrorAction SilentlyContinue }
  if ($prc -eq -2) {
    Add-ProbeOverflow "python $($Probe -join ' ')" $ProbeCap
    Add-UnmeasuredStep "$Label 걷기" "python $($Probe -join ' ')" '걷지도 건너뛰지도 않았다'
    return
  }
  if ($prc -ne 0) {
    Write-Host "  ! $Label — 고르지 않았는데 $ProbeWhat 안 서서 못 걷었다 · 우리 훅이 $Config 에 남았을 수 있다" -ForegroundColor Yellow
    return
  }
  $log = [IO.Path]::GetTempFileName()
  $rc = Invoke-Logged 'python' (@('-X', 'utf8', $Parts[0]) + $HandArgs) $log
  $said = @(Get-Content -LiteralPath $log -ErrorAction SilentlyContinue | ForEach-Object { "$_".Trim() } | Where-Object { $_ })
  if ($rc -ne 0 -or @($said | Where-Object { $_ -like 'ERROR=*' }).Count) {
    Write-Host "  ! $Label — 고르지 않아 우리 훅을 걷으려 했는데 못 걷었다(종료 $rc) · $Config 는 그대로다. 걷는 손이 뱉은 끝 줄:" -ForegroundColor Red
    Show-Log $log
    $script:Fails.Add("$Label 걷기 (못 걷었다)")
  } else {
    if ($said -contains 'CHANGED=1') {
      Write-Host "  $Label — 고르지 않아 우리 훅을 걷었다" -ForegroundColor Green
      $bak = @($said | Where-Object { $_ -like 'BACKUP=*' }) | Select-Object -First 1
      if ($bak) { Write-Host "     고치기 전 것은 $($bak.Substring('BACKUP='.Length)) 에 떠 뒀다" }
    } else {
      Write-Host "  $Label — 고르지 않았다 · 걷을 우리 훅이 없다"
    }
    $skipped = @($said | Where-Object { $_ -like 'SKIP=*' })
    if ($skipped.Count) {
      Write-Host "  ! $Label — 못 알아보는 꼴로 적힌 이벤트는 안 건드렸다: $($skipped -join ' ') · 그 안의 우리 훅은 남았을 수 있다" -ForegroundColor Yellow
    }
  }
  Remove-Item -LiteralPath $log -ErrorAction SilentlyContinue
}

#endregion 도구별 · Codex · agy 훅

#region 도구별 · 브라우저 MCP — 고른 도구에 우리 크로미움을 물린 playwright MCP 를 달고 안 고른 도구에서 걷는다 (claude-config 결정 0149)

# 고른 제품 키 → 어댑터(`browser-mcp.py`)의 도구 이름. 표 밖의 제품은 브라우저 MCP 와 무관하다.
$BrowserMcpHosts = [ordered]@{ claude = 'claude'; codex = 'codex'; antigravity = 'agy' }
# 브라우저 받기(`get-browser.sh`)의 울타리(초) — 받는 것이 크로미움 스냅숏 하나(수백 MB)라 느린 회선에서도 끝나는 값이다.
#   넘기면 노랑으로 남기고 잇는다 — 어댑터는 브라우저가 없으면 안 단다.
$BrowserGetCap = 900
# 끝 검증의 어댑터 `check` 의 울타리(초) — 그 안에서 도는 실행기 확인 판이 제 울타리 120 초를 들고, 넘기면 나무째 끊는 데 15 초를
#   더 쓴다. 등록 파일 읽기는 순간이다. 넘기면 [?] 다(결정 0141).
$BrowserMcpCheckCap = 240

# Git Bash — 짐의 bash 몸통(브라우저 받기 · 「설정 저장소」 걸음의 심기)을 부르는 자리들이 같이 찾는다. 못 찾으면 빈 값.
function Find-GitBash {
  @("$env:ProgramFiles\Git\bin\bash.exe", "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe") |
    Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

# 어댑터를 한 번 부른다 — `@{ Rc; Lines }`(-2 는 `$CapSec` 을 넘겨 나무째 거뒀다). 줄 계약은 어댑터의 머리말이 든다.
#   install · remove 는 어댑터가 도구 CLI 마다 제 울타리를 두르므로 울타리 없이 부른다.
function Invoke-BrowserMcp([string]$Adapter, [string[]]$AdapterArgs, [int]$CapSec = 0) {
  $log = [IO.Path]::GetTempFileName()
  $pyArgs = @('-X', 'utf8', $Adapter) + $AdapterArgs
  $rc = if ($CapSec -gt 0) { Invoke-LoggedCapped 'python' $pyArgs $log $CapSec } else { Invoke-Logged 'python' $pyArgs $log }
  $lines = @(Get-Content -LiteralPath $log -Encoding UTF8 -ErrorAction SilentlyContinue | ForEach-Object { "$_".Trim() } | Where-Object { $_ })
  Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue
  return @{ Rc = $rc; Lines = $lines }
}

# 어댑터의 install · remove 줄을 이 설치기의 꼴로 찍고, ERROR 가 있으면 `$Fails` 에 센다. SKIP 은 노랑 — 꾸러미나 브라우저가
#   없어 안 단 것이라, 그 까닭(「CLI」 걸음의 playwright 줄 · 위 브라우저 받기 줄)이 이미 찍혔다.
function Show-BrowserMcpLines([string]$Label, $Result) {
  foreach ($ln in @($Result.Lines)) {
    if ($ln -like 'CHANGE=*')    { Write-Host "  $Label — $($ln.Substring('CHANGE='.Length))" -ForegroundColor Green }
    elseif ($ln -like 'WARN=*')  { Write-Host "  ! $Label — $($ln.Substring('WARN='.Length))" -ForegroundColor Yellow }
    elseif ($ln -like 'SKIP=*')  { Write-Host "  ! $Label — 안 달았다: $($ln.Substring('SKIP='.Length))" -ForegroundColor Yellow }
    elseif ($ln -like 'ERROR=*') { Write-Host "  ! $Label — $($ln.Substring('ERROR='.Length))" -ForegroundColor Red }
  }
  if ($Result.Rc -ne 0 -or @($Result.Lines | Where-Object { $_ -like 'ERROR=*' }).Count) {
    $script:Fails.Add("$Label (종료 $($Result.Rc))")
  } elseif ($Result.Lines -contains 'CHANGED=0' -and -not @($Result.Lines | Where-Object { $_ -match '^(WARN|SKIP)=' }).Count) {
    Write-Host "  $Label — 이미 맞다"
  }
}

# 끝 검증 한 칸 — 어댑터의 `check` 를 한 번 부른다: 고른 도구의 등록 꼴 · 안 고른 도구에 우리 등록이 없나 · 실행기를 MCP 로
#   띄워 이동 · 그림 한 장(「우리 크로미움이 여기서 뜨나」). 0 맞다 `[O]` · 1 어긋났다 `[X]` · 2 못 쟀다 `[?]`(결정 0141).
function Get-BrowserMcpCheck([string]$Adapter, [string[]]$Picked, [string[]]$Unpicked) {
  $name = '브라우저 MCP'
  if (-not (Test-Path -LiteralPath $Adapter -PathType Leaf)) { return @{ Name = "$name (씨앗에 어댑터가 없다: $Adapter)"; Ok = $false } }
  $hostArgs = @()
  foreach ($h in $Picked)   { $hostArgs += @('--host', $h) }
  foreach ($h in $Unpicked) { $hostArgs += @('--gone', $h) }
  $r = Invoke-BrowserMcp $Adapter (@('check') + $hostArgs) $BrowserMcpCheckCap
  if ($r.Rc -eq -2) {
    Add-ProbeOverflow 'browser-mcp.py check' $BrowserMcpCheckCap
    return @{ Name = $name; State = 'unmeasured'; Probe = 'browser-mcp.py check'; Why = "${BrowserMcpCheckCap}초 안에 안 끝나" }
  }
  $said = @($r.Lines | Where-Object { $_ -match '^(DIFF|UNMEASURED)=' -or $_ -like 'LIVE=fail*' } | ForEach-Object { $_ -replace '^[A-Z]+=', '' })
  $live = @($r.Lines | Where-Object { $_ -like 'LIVE=ok*' } | ForEach-Object { $_.Substring('LIVE=ok '.Length) }) | Select-Object -First 1
  if ($r.Rc -eq 0) { return @{ Name = "$name (등록이 맞고 브라우저가 뜬다$(if ($live) { " — $live" }))"; Ok = $true } }
  if ($r.Rc -eq 2) { return @{ Name = "$name ($($said -join ' · '))"; State = 'unmeasured'; Probe = 'browser-mcp.py check'; Why = '끝까지 못 재' } }
  $why = if ($said.Count) { $said -join ' · ' } elseif ($r.Rc -eq -1) { 'python 을 못 불렀다' } else { "종료 $($r.Rc)" }
  return @{ Name = "$name ($why)"; Ok = $false }
}

#endregion 도구별 · 브라우저 MCP

#region 도구별 · 묻지 않고 돌기 — 고른 도구의 제 승인 설정을 사람 값을 안 덮고 심고, 끝 검증이 되읽는다

# 표 한 줄(`$ToolAutoRun` — 「도구별 홈」 걸음)이 받는 꼴 — Label · Want · Path(설정 파일) · Under(그 안의 표 이름 · 맨 위면 빈 글) ·
#   Set(심을 키와 값 · 순서대로) · Guard(있으면 사람이 정한 것으로 보는 키 · 없으면 Set 의 키) · Toml(참이면 TOML 맨 위 키) ·
#   Need(심기 전에 그 자리에 그 값으로 서 있어야 하는 키 · JSON 줄만 — 표의 앞 줄이 심은 뒤에 재므로 같은 파일의 앞 줄을 먼저 둔다).
# 심는 규칙은 하나다 — **Guard 의 키가 하나라도 서 있으면 그 줄을 통째로 둔다.** 한 줄의 키들은 그 도구의 스위치 하나라, 사람이
#   하나만 정해 둔 자리에 나머지를 채우면 그 사람이 고른 적 없는 조합이 선다(claude-config 결정 0127).
# 내는 것 — @{ Did = set · kept · skipped(Need 가 안 섰다) · broken · nopython · unmeasured(파이썬 물음이 울타리를 넘겼다 — 안 건드렸다) ·
#   raced(쓰는 사이 다른 프로그램이 그 파일을 고쳤다 — 그 글을 둔다 · `Write-FileSafely`) · linked(그 파일이 링크다 — 안 썼다);
#   Have = 서 있던 Guard 키와 값(「키 = 값」 글) · Why = skipped · broken · unmeasured 의 까닭 · Probe = unmeasured 의 물음 }.
#   화면 · 실패 줄은 부르는 쪽이 든다. 파일을 못 읽으면 안 건드린다 — 사람이 손댄 것이 거기 들어 있을 수 있다.
# ⚠ 표인가는 `[System.Management.Automation.PSCustomObject]` 로 가른다 — `[pscustomobject]` 는 `[psobject]` 라 파이프에서 온 글 · 목록도
#   그 꼴로 읽혀, 맨 위가 목록인 파일을 표로 보고 덮는다.
function Set-ToolAutoRun($Row) {
  $guard = if ($Row.Guard) { @($Row.Guard) } else { @($Row.Set.Keys) }
  if ($Row.Toml) {
    # 「python 이 서나」는 세 값으로 묻는다 — 못 잰 것(넘김 · 선 이름이 짐)을 「없다」로 읽지 않는다(결정 0141 · `Test-Runs` 곁말)
    $tpy = Measure-Runs 'python' '--version'
    if ($tpy -eq 'unmeasured') { return @{ Did = 'unmeasured'; Probe = 'python --version'; Why = (Get-ProbeWhy 'python --version') } }
    if ($tpy -ne 'yes') { return @{ Did = 'nopython'; Why = 'python 이 안 선다' } }
    # `--version` 이 선 뒤 다시 부르는 자리라 울타리를 두른다 — 넘기면 못 잰 것이라 심지도 건너뛰지도 않는다(결정 0141)
    $tl = [IO.Path]::GetTempFileName()
    # `-I` — 작업 폴더의 `tomllib.py` 를 안 집는다(3.11 이 전제라 받는다)
    try { $trc = Invoke-LoggedCapped 'python' @('-I', '-c', 'import tomllib') $tl $ProbeCap } finally { Remove-Item -LiteralPath $tl, "$tl.err" -ErrorAction SilentlyContinue }
    if ($trc -eq -2) {
      Add-ProbeOverflow 'python -c import tomllib' $ProbeCap
      return @{ Did = 'unmeasured'; Probe = 'python -c import tomllib'; Why = (Format-ProbeWhy -2 $ProbeCap) }
    }
    if ($trc -ne 0) { return @{ Did = 'nopython'; Why = '파이썬 3.11 이상(tomllib)이 안 선다' } }
    $tomlTimed = $script:ProbeTimedOut.Count
    $old = ''
    $oldBytes = $null
    if (Test-Path -LiteralPath $Row.Path -PathType Leaf) {
      $oldBytes = [IO.File]::ReadAllBytes($Row.Path)
      $old = Read-TextOf $oldBytes
      $now = Read-TomlTopKeys $Row.Path $guard
      if ($null -eq $now -and $script:ProbeTimedOut.Count -gt $tomlTimed) { return @{ Did = 'unmeasured'; Probe = $TomlReadProbe; Why = (Format-ProbeWhy -2 $ProbeCap) } }
      if ($null -eq $now) { return @{ Did = 'broken'; Why = 'TOML 로 못 읽었다' } }
      $have = @($guard | Where-Object { $now.PSObject.Properties[$_] } | ForEach-Object { "$_ = $($now.$_ | ConvertTo-Json -Compress)" })
      if ($have.Count) { return @{ Did = 'kept'; Have = $have } }
    }
    # TOML 의 맨 위 키는 첫 표 머리 앞에 서야 한다 — 파일 머리에 얹으면 늘 그 자리다. 값은 따옴표 · 역슬래시가 없는 글자뿐이다.
    $nl = if ($old.Contains("`r`n")) { "`r`n" } else { "`n" }
    $head = (@($Row.Set.Keys | ForEach-Object { "$_ = `"$($Row.Set[$_])`"" }) -join $nl) + $nl
    $probe = [IO.Path]::GetTempFileName()
    try {
      [IO.File]::WriteAllText($probe, $head + $old, (New-Object Text.UTF8Encoding($false)))
      # 얹은 결과를 다시 읽어 뜻을 잰 뒤에만 쓴다 — 같은 키가 둘이 되면 Codex 가 설정째 못 읽고 뜬다.
      $after = Read-TomlTopKeys $probe @($Row.Set.Keys)
      if ($null -eq $after -and $script:ProbeTimedOut.Count -gt $tomlTimed) { return @{ Did = 'unmeasured'; Probe = $TomlReadProbe; Why = (Format-ProbeWhy -2 $ProbeCap) } }
      $miss = @($Row.Set.Keys | Where-Object { -not ($after -and $after.PSObject.Properties[$_] -and $after.$_ -ceq $Row.Set[$_]) })
      if ($miss.Count) { return @{ Did = 'broken'; Why = "얹은 결과가 그 뜻으로 안 읽힌다 ($($miss -join ' · '))" } }
      $w = Write-FileSafely $Row.Path ((New-Object Text.UTF8Encoding($false)).GetBytes($head + $old)) $oldBytes
    } finally { Remove-Item -LiteralPath $probe -ErrorAction SilentlyContinue }
    if ($w.Did -ceq 'linked') { return @{ Did = 'linked'; Why = $w.Why } }
    if ($w.Did -ceq 'raced' -or $w.Did -ceq 'overrun') { return @{ Did = 'raced'; Why = $w.Why } }
    if ($w.Did -cne 'written') { return @{ Did = 'broken'; Why = $w.Why } }
    return @{ Did = 'set' }
  }
  $obj = $null
  $oldBytes = $null
  if (Test-Path -LiteralPath $Row.Path -PathType Leaf) {
    $oldBytes = [IO.File]::ReadAllBytes($Row.Path)
    $text = Read-TextOf $oldBytes
    if ($text.Trim()) {
      try { $obj = $text | ConvertFrom-Json } catch { return @{ Did = 'broken'; Why = 'JSON 으로 못 읽었다' } }
      if ($obj -isnot [System.Management.Automation.PSCustomObject]) { return @{ Did = 'broken'; Why = '맨 위가 표가 아니다' } }
    }
  }
  if ($null -eq $obj) { $obj = [pscustomobject]@{} }
  $at = $obj
  if ($Row.Under) {
    $u = $obj.PSObject.Properties[$Row.Under]
    if ($u -and $u.Value -isnot [System.Management.Automation.PSCustomObject]) { return @{ Did = 'broken'; Why = "$($Row.Under) 가 표가 아니다" } }
    if (-not $u) { $obj | Add-Member -NotePropertyName $Row.Under -NotePropertyValue ([pscustomobject]@{}) }
    $at = $obj.($Row.Under)
  }
  $have = @($guard | Where-Object { $at.PSObject.Properties[$_] } | ForEach-Object { "$_ = $($at.$_ | ConvertTo-Json -Compress)" })
  if ($have.Count) { return @{ Did = 'kept'; Have = $have } }
  if ($Row.Need) {
    $unmet = @($Row.Need.Keys | Where-Object { -not ($at.PSObject.Properties[$_] -and $at.$_ -ceq $Row.Need[$_]) })
    if ($unmet.Count) { return @{ Did = 'skipped'; Why = (@($unmet | ForEach-Object { "$_ 가 $($Row.Need[$_] | ConvertTo-Json -Compress) 가 아니다" }) -join ' · ') } }
  }
  foreach ($k in $Row.Set.Keys) { $at | Add-Member -NotePropertyName $k -NotePropertyValue $Row.Set[$k] }
  # ⚠ `-Depth` 를 준다 — 5.1 의 기본 깊이는 2 라 사람이 둔 깊은 표가 글자로 뭉개진다.
  $w = Write-FileSafely $Row.Path ((New-Object Text.UTF8Encoding($false)).GetBytes(($obj | ConvertTo-Json -Depth 32))) $oldBytes
  if ($w.Did -ceq 'linked') { return @{ Did = 'linked'; Why = $w.Why } }
  if ($w.Did -ceq 'raced' -or $w.Did -ceq 'overrun') { return @{ Did = 'raced'; Why = $w.Why } }
  if ($w.Did -cne 'written') { return @{ Did = 'broken'; Why = $w.Why } }
  return @{ Did = 'set' }
}

# TOML 파일의 맨 위 키 가운데 `$Keys` 에 든 것을 표로 낸다(못 읽으면 $null). 판정은 파이썬 `tomllib` 이 든다 — 첫 표 머리가 어디인가 ·
#   여러 줄 배열과 글 안의 `[` 는 글자로는 못 가른다.
# ⚠ **파이썬에 줄 코드에 큰따옴표를 안 쓴다** — 5.1 은 네이티브 인자 안의 큰따옴표를 깨뜨려 넘긴다.
#   `$ProbeCap` 울타리를 두른다 — 넘기면 $null 이고 그 넘김이 `$script:ProbeTimedOut` 에 남아, 부르는 자리가 그 수로 「못 읽었다」와
#   「못 쟀다」를 가른다.
$TomlReadProbe = 'python -c tomllib.load'
function Read-TomlTopKeys([string]$Path, [string[]]$Keys) {
  $code = "import sys,json,tomllib;d=tomllib.load(open(sys.argv[1],'rb'));print(json.dumps({k:d[k] for k in sys.argv[2:] if k in d},default=str))"
  $tl = [IO.Path]::GetTempFileName()
  try {
    $rc = Invoke-LoggedCapped 'python' (@('-I', '-X', 'utf8', '-c', $code, $Path) + $Keys) $tl $ProbeCap
    if ($rc -eq -2) { Add-ProbeOverflow $TomlReadProbe $ProbeCap; return $null }
    if ($rc -ne 0) { return $null }
    $out = @(Get-Content -LiteralPath $tl -Encoding UTF8 -ErrorAction SilentlyContinue)
  } finally { Remove-Item -LiteralPath $tl, "$tl.err" -ErrorAction SilentlyContinue }
  try { return (($out -join "`n") | ConvertFrom-Json) } catch { return $null }
}

# 끝 검증 한 줄 — 심은 뒤의 파일을 되읽어, Guard 의 키가 하나라도 서 있으면 [O] 다(사람이 정한 값은 그 사람의 기본값이라 안
#   덮었고 줄에 그 값을 적는다 · 기본 권한 모드 줄과 같은 자). Need 의 키가 다른 값으로 서 있으면 안 심은 것이 맞아 [O] 고, 그 키가
#   없으면 앞 줄이 못 심은 것이라 [X] 다.
function Get-ToolAutoRunCheck($Row) {
  $guard = if ($Row.Guard) { @($Row.Guard) } else { @($Row.Set.Keys) }
  $at = $null
  if (Test-Path -LiteralPath $Row.Path -PathType Leaf) {
    if ($Row.Toml) {
      $tomlTimed = $script:ProbeTimedOut.Count
      $at = Read-TomlTopKeys $Row.Path $guard
      if ($null -eq $at -and $script:ProbeTimedOut.Count -gt $tomlTimed) {
        return @{ Name = "묻지 않고 돌기 · $($Row.Label) ($($Row.Path))"; State = 'unmeasured'; Probe = $TomlReadProbe; Why = (Format-ProbeWhy -2 $ProbeCap) }
      }
    } else {
      try { $at = [IO.File]::ReadAllText($Row.Path) | ConvertFrom-Json } catch { $at = $null }
      if ($at -and $Row.Under) { $at = if ($at.PSObject.Properties[$Row.Under]) { $at.($Row.Under) } else { $null } }
    }
  }
  $have = @()
  if ($at -is [System.Management.Automation.PSCustomObject]) { $have = @($guard | Where-Object { $at.PSObject.Properties[$_] } | ForEach-Object { "$_ = $($at.$_ | ConvertTo-Json -Compress)" }) }
  $waived = @()
  if (-not $have.Count -and $Row.Need -and $at -is [System.Management.Automation.PSCustomObject]) {
    $waived = @($Row.Need.Keys | Where-Object { $at.PSObject.Properties[$_] -and $at.$_ -cne $Row.Need[$_] } | ForEach-Object { "$_ = $($at.$_ | ConvertTo-Json -Compress)" })
  }
  $where = $Row.Path + $(if ($Row.Under) { " 의 $($Row.Under)" } else { '' })
  $shown = if ($have.Count) { $have -join ' · ' } elseif ($waived.Count) { "안 심는다 — $($waived -join ' · ')" } else { '없다' }
  @{ Name = "묻지 않고 돌기 · $($Row.Label) ($where — $shown)"; Ok = [bool]($have.Count -or $waived.Count) }
}

#endregion 도구별 · 묻지 않고 돌기

#region 도구별 · 로컬 프록시 — 살았나 · 문을 여나 재고, 끄고, 돌릴 파이썬과 판 번호를 가린다

# 로컬 프록시의 건강 답(JSON)을 3초 안에 받아 낸다 — 못 받으면 `$null`.
function Get-ProxyHealth([string]$Url) {
  try { return Invoke-RestMethod -Uri $Url -TimeoutSec 3 } catch { return $null }
}

# 게이트웨이가 prefill(assistant 로 끝나는 메시지)을 받아 주나 — `<Base>/v1/messages` 에 보내 HTTP 코드를 낸다(못 갔으면 0).
# ⚠ **횟수 · 틈은 매개변수로 받고(기본값은 `$DoorTries` · `$DoorGapMs`) 한 번 아래로 안 내린다** — 값이 안 선 자리에서 루프가 한
#   번도 안 돌면 요청 없이 0 이 나와, 「못 닿았다」와 「안 물어봤다」가 같은 값이 된다.
function Test-PrefillDoor([string]$Base, [string]$Token, [string]$Model,
                          [int]$Tries = $DoorTries, [int]$GapMs = $DoorGapMs) {
  if ($Tries -lt 1) { $Tries = 1 }
  $body = @{ model = $Model; max_tokens = 8
             messages = @(@{ role = 'user'; content = 'hi' }, @{ role = 'assistant'; content = 'prefill' }) } |
          ConvertTo-Json -Depth 5 -Compress
  $hdr = @{ 'x-api-key' = $Token; 'Authorization' = "Bearer $Token"; 'anthropic-version' = '2023-06-01' }
  # 다시 묻나는 받은 것의 뜻이 정한다 — 게이트웨이가 prefill 을 두고 판정한 것(200 열렸다 · 4xx 거절했다)이면 멈추고, 그 판정에
  #   닿지도 못한 것(5xx 상류가 끊었다 · 0 못 갔다)만 다시 묻는다.
  # ⚠ **4xx 를 다시 묻지 않는다** — 400 이 이 검사가 찾는 그 결함이라(결정 0041) 재시도로 덮으면 재는 자가 제가 재려던 것을
  #   지운다. 늦게 빨강인 편이 가짜 초록보다 낫다.
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

# 로컬 프록시를 끈다 — 그 포트(루프백)를 듣는 파이썬 프로세스와 명령줄에 그 프록시 파일 이름(`$Leaf` — 값 파일의 `#gateway-proxy`
#   에서 지은 `$ProxyFile`)을 든 남은 파이썬 프로세스를 끄고 0.5초 기다린다. 못 하는 것은 조용히 넘긴다.
function Stop-ProxyOnPort([int]$Port, [string]$Leaf) {
  try {
    $owners = @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
                Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($o in $owners) {
      $pr = Get-Process -Id $o -ErrorAction SilentlyContinue
      if ($pr -and $pr.ProcessName -match '^pythonw?$') { Stop-Process -Id $o -Force -ErrorAction SilentlyContinue }
    }
    # 포트를 안 듣는 남은 프로세스(죽은 자식의 부모 껍데기 등)도 끈다 (#21)
    if ($Leaf) {
      Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' or Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*$Leaf*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    }
    Start-Sleep -Milliseconds 500
  } catch { }
}

# 와치독이 띄울 진짜 `pythonw.exe` 자리를 낸다(못 찾으면 `$null`) — 파이썬은 존재가 아니라 불러 보고 고른다(결정 0028 · #51 · #75 ·
#   PAISetup#21). 후보마다 해석기에게 `sys.executable` 을 물어 런처 · 심볼릭 링크 뒤의 진짜 자리를 따고, 그 곁의 pythonw.exe 가
#   있고 WindowsApps 껍데기가 아닐 때만 고른다.
# ⚠ **런처 곁의 pythonw.exe 를 와치독에 박지 않는다** — `Get-Command` 가 잡는 첫 번째는 스토어 껍데기나 Python Manager 런처일 수
#   있고, 런처는 진짜 해석기를 자식으로 띄우고 자신도 남아 두 겹으로 선다 — 자식이 죽어도 껍데기가 남아 와치독이 안 되살린다.
function Get-RealPythonW {
  $candidates = @()
  $pyCmds = @(Get-Command python, python3, py -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -Unique)
  if ($pyCmds) { $candidates += $pyCmds }
  $candidates += @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  $candidates += @(Get-ChildItem "$env:ProgramFiles\Python3*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
  $candidates += @(Get-ChildItem "$env:LOCALAPPDATA\Python\*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)

  foreach ($c in ($candidates | Select-Object -Unique)) {
    if (-not $c -or -not (Test-Path -LiteralPath $c)) { continue }
    $real = $null
    try { $out = & $c -c "import sys; print(sys.executable)" 2>$null } catch { }
    if ($LASTEXITCODE -eq 0 -and $out) {
      $real = ($out | Select-Object -First 1).Trim()
    }

    if ($real -and (Test-Path -LiteralPath $real)) {
      $candPyw = Join-Path (Split-Path $real -Parent) 'pythonw.exe'
      if ((Test-Path -LiteralPath $candPyw) -and ($candPyw -notlike '*\Microsoft\WindowsApps\*')) {
        return $candPyw
      }
    }
  }
  return $null
}

# ── 판 번호는 두 칸이다 — **상류 판과 우리 판을 안 섞는다** ─────────────────
# 프록시 파일의 글에서 `VERSION_UPSTREAM` · `VERSION_OURS` 를 정수 둘 `@(상류, 우리)` 로 낸다 — 없는 칸은 0 이다. `VERSION` 한 칸만
#   든 옛 프록시는 0 · 0 이 되어 새 판이 늘 이긴다 — 갈아 끼우는 쪽으로 기운다(반대로 두면 옛 프록시가 영영 안 바뀐다).
# ⚠ **점 찍힌 한 줄(`15.4`)을 크기로 견주지 않는다** — 문자열로 견주면 `"9" -ge "10"` 이 참이고, `[version]` 으로 넘기면 정수 한
#   칸(`18`)이 `18.0` 으로 읽혀 낡은 것이 새것으로 보인다. 두 수를 각각 정수로 읽어 위 칸부터 차례로 견준다.
function Get-ProxyVer([string]$text) {
  $up = 0; $ours = 0
  $mu = [regex]::Match($text, '(?m)^VERSION_UPSTREAM\s*=\s*(\d+)')
  $mo = [regex]::Match($text, '(?m)^VERSION_OURS\s*=\s*(\d+)')
  if ($mu.Success) { $up = [int]$mu.Groups[1].Value }
  if ($mo.Success) { $ours = [int]$mo.Groups[1].Value }
  return @($up, $ours)
}

#endregion 도구별 · 로컬 프록시

#region 도구별 · gh — GitHub CLI 자격을 한 번 써 보고, 로그인 코드 창을 띄운다

# gh 자격이 쓸 수 있게 섰나 — 그 자격으로 `gh api user` 한 번을 보내 0 으로 끝나면 참이다. gh 가 안 서거나 `$GhStatusCap` 을
#   넘기면 거짓이고, 넘김은 `$script:ProbeTimedOut` 에 남아 부르는 자리가 그 수로 「못 쟀다」를 가른다(`Test-ClaudeLoggedIn` 과
#   같은 규율). 환경변수 토큰(`$GhEnvTokens`)이 서 있으면 gh 는 그것을 쓰므로 이 판정도 그것을 잰다 — 그 토큰이 가린 키링
#   로그인의 생사는 `Get-GhKeyringState` 가 따로 잰다(끝 검증).
# ⚠ **`gh auth status` 의 종료코드로 묻지 않는다** — 그 코드는 「하나라도 쓸 수 있나」가 아니라 「계정 목록이 다 멀쩡한가」에
#   가까워, 곁에 자격 깨진 항목이 하나 있으면 쓸 수 있는 자격이 서 있어도 0 이 아니다. 알고 싶은 것은 clone 과 세션 훅이 쓸
#   자격이 있나이고, 답하는 자는 그 자격으로 보내는 실제 요청이다(규범 [State Over Event]).
# 망이 끊긴 자리는 「없다」와 갈라 적는다 — 「로그인하라」는 말을 망 끊긴 사람에게 하면 엉뚱한 데를 고치러 간다. `gh api` 는
#   자격 없이는 어떤 길도(`rate_limit` 도) 안 열어 줘 망과 자격이 같은 코드로 오므로, 가르는 자는 `Test-Reach` 다(`Get-GhLoginGo`).
function Test-GhLoggedIn {
  if (-not (Test-Runs 'gh' '--version')) { return $false }
  $log = [IO.Path]::GetTempFileName()
  try {
    $rc = Invoke-LoggedCapped 'gh' @('api', 'user', '--jq', '.login') $log $GhStatusCap
    if ($rc -eq -2) { Add-ProbeOverflow 'gh api user' $GhStatusCap }
    return ($rc -eq 0)
  } finally { Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue }
}

# gh 가 키링의 로그인보다 먼저 쓰는 환경변수 토큰 — 이것이 선 셸에서는 `gh auth login` 이 로그인을 안 받는다.
$GhEnvTokens = @('GH_TOKEN', 'GITHUB_TOKEN')

# 키링을 재는 한 번(`gh auth status` — GitHub 에 한 번 묻는다)에 주는 한도. 즉답 프로브(`$ProbeCap`)보다 길다 — 망을 한 번 탄다.
$GhStatusCap = 30

# gh 키링 로그인 하나만 잰다 — 개인 쪽 gh · git 과 Copilot CLI 가 쓰는 로그인이다(claude-config 결정 0137). Copilot 러너는
#   환경변수 토큰을 빼고 띄우므로 그 토큰이 있어도 키링이 죽으면 Copilot 이 진다 — 그래서 `$GhEnvTokens` 를 이 호출 동안만
#   이 프로세스에서 빼고 묻고 되돌린다(사용자 · 기계 범위의 값은 안 건드린다).
# 내는 것 — @{ State = 'ok' | 'invalid' | 'none' | 'unmeasured'; Why = 까닭 }. 판정은 gh 의 JSON(`gh auth status --json hosts`)
#   의 `state` 가 든다 — `success` 면 산다. `error` 는 gh 가 「The token in keyring is invalid」를 내는 상태인데 망이 끊겨도
#   나므로, GitHub 가 토큰을 401 로 거절했을 때(`error` 칸)만 무효로 친다. 로그인이 없으면 hosts 가 빈다.
function Get-GhKeyringState {
  if (-not (Test-Runs 'gh' '--version')) { return @{ State = 'unmeasured'; Why = 'gh 가 안 닿는다' } }
  $saved = @{}
  foreach ($n in $GhEnvTokens) {
    $saved[$n] = [Environment]::GetEnvironmentVariable($n, 'Process')
    [Environment]::SetEnvironmentVariable($n, $null, 'Process')
  }
  # 울타리를 두른 손(`Invoke-LoggedCapped`)으로 부른다 — 멎은 gh 하나가 설치를 끝없이 세우지 않게 한다(`Test-Runs` 머리말).
  $log = [IO.Path]::GetTempFileName()
  try {
    $rc = Invoke-LoggedCapped 'gh' @('auth', 'status', '--hostname', 'github.com', '--active', '--json', 'hosts') $log $GhStatusCap
    $said = @(Get-Content -LiteralPath $log -Encoding UTF8 -ErrorAction SilentlyContinue)
  } finally {
    foreach ($n in $GhEnvTokens) { [Environment]::SetEnvironmentVariable($n, $saved[$n], 'Process') }
    Remove-Item -LiteralPath $log, "$log.err" -ErrorAction SilentlyContinue
  }
  if ($rc -eq -2) { return @{ State = 'unmeasured'; Why = "gh auth status 가 ${GhStatusCap}초 안에 안 끝나 거뒀다" } }
  if ($rc -ne 0) { return @{ State = 'unmeasured'; Why = "gh auth status 가 $rc 로 끝났다" } }
  try { $hosts = (($said -join "`n") | ConvertFrom-Json).hosts } catch { return @{ State = 'unmeasured'; Why = 'gh 의 답을 JSON 으로 못 읽었다' } }
  $acct = @($hosts.'github.com') | Select-Object -First 1
  if (-not $acct) { return @{ State = 'none'; Why = '' } }
  if ($acct.state -eq 'success') { return @{ State = 'ok'; Why = '' } }
  if ($acct.state -eq 'error' -and "$($acct.error)" -match '\b401\b') { return @{ State = 'invalid'; Why = '' } }
  $err = "$($acct.error)" -replace '\s+', ' '
  if ($err.Length -gt 120) { $err = $err.Substring(0, 120) + ' …' }
  return @{ State = 'unmeasured'; Why = "gh 가 GitHub 에 못 물었다 — $($acct.state)$(if ($err) { ": $err" })" }
}

# 끝 검증의 gh 로그인 줄 — `Get-GhKeyringState` 의 답을 사람이 읽을 줄로 옮긴다. 받는 것 — 그 답 · 사용자 · 기계 범위에
#   선 환경변수 토큰의 이름들. 내는 것 — @{ Ok = 살아 있나; Lines = 줄들 }. 무효 · 없음이면 되살리는 명령을 붙이고, 이름이
#   있으면 그 셸에서 먼저 비우는 명령을 더한다(값은 안 싣는다).
function Get-GhKeyringLines($St, [string[]]$TokenVars) {
  $fix = @('    새 터미널에서 gh auth login 한 번이면 된다')
  if (@($TokenVars).Count) {
    $fix += ("    환경변수 토큰($(@($TokenVars) -join ' · '))이 선 셸에서는 gh 가 로그인을 안 받는다 — 그 셸에서 먼저 비운다" +
             "(PowerShell: Remove-Item $((@($TokenVars) | ForEach-Object { "Env:$_" }) -join ', '))")
  }
  switch ($St.State) {
    'ok'      { return @{ Ok = $true;  Lines = @('  [O] gh 로그인 (키링 — 환경변수 토큰을 뺀 채로 쟀다)') } }
    'invalid' { return @{ Ok = $false; Lines = @('  ! gh 로그인이 무효다 — 키링의 토큰이 죽었다 (대개 다른 기기에서 같은 범위로 gh 에 로그인한 탓이다)') + $fix } }
    'none'    { return @{ Ok = $false; Lines = @('  ! gh 로그인이 없다 — gh · git · Copilot CLI 가 쓰는 로그인이다') + $fix } }
    default   { return @{ Ok = $false; Lines = @("  ! gh 로그인 — 못 쟀다 ($($St.Why))") } }
  }
}

# 코드 창 — 코드가 나올 때까지 「기다리는 중」이고, 나오면 코드가 크게 선다. 남은 시간을 초마다 고쳐 찍고 5초마다 로그인이
# 섰나 재서, 서면 닫는다. 돌려주는 값은 섰나(참/거짓).
# ⚠ **남은 시간은 벽시계로 센다** — 틱을 세면 틱 사이에 낀 일만큼 창이 한도보다 오래 산다. 앞당겨 띄운 자식은 부모가 벽시계로
#   거두므로(`Wait-GhLoginChild`), 창이 그보다 늦게 닫히면 사람이 코드를 넣는 중에 거둬진다.
# 틱 안에서 로그인을 기다리지 않는다 — 재기(`gh api user`)는 틱이 띄우고 다음 틱들이 끝을 본다(`Start-GhLoginProbe`). 기다리면
#   그동안 창이 얼고 남은 시간도 안 준다. 판정은 `Test-GhLoggedIn` 과 같다(0 으로 끝나면 섰다) · 한도는 `$GhStatusCap`.
# 손잡이는 닫힘(closure)으로 넘긴다 — 폼 이벤트의 스크립트 블록은 이 함수의 변수를 못 보므로 `GetNewClosure()` 가 그 순간의 참조를
#   물려주고, 상태는 해시테이블이라 안에서 고친 것이 밖에 남는다.
# ⚠ **닫힘 안에서 이 몸통의 함수를 이름으로 부르지 않는다** — 닫힘의 부모는 전역 범위라, 몸통이 `-Command "& { & … }"` 로
#   뜬 자리(로그인 자식 · `Invoke-GhLoginChild`)에서는 스크립트 범위의 함수가 안 보여 틱마다 「인식되지 않습니다」로 진다.
#   함수 블록(`${function:…}`)을 변수로 잡아 넘기면 그 블록은 몸통의 범위에서 돈다.
# `-Raised` — 가운데 위쪽에 선다. 설치가 같은 때 띄우는 물음창(`Show-AskDialog`)은 화면 한가운데에 서므로, 앞당겨 띄운 창(`Invoke-GhLoginChild`)이
#   그 자리를 덮지 않고 둘이 다 보이게 한다. 둘 다 맨 위(TopMost) 창이라 어느 것도 다른 창 뒤로 숨지 않는다.
function Show-GhLoginWindow([string]$OutFile, [System.Diagnostics.Process]$Proc, [int]$Wait, [switch]$Raised) {
  Add-Type -AssemblyName System.Windows.Forms
  Add-Type -AssemblyName System.Drawing
  $f = New-Object Windows.Forms.Form
  $f.Text = 'GitHub 로그인'; $f.TopMost = $true; $f.StartPosition = 'CenterScreen'
  $f.FormBorderStyle = 'FixedDialog'; $f.MaximizeBox = $false; $f.MinimizeBox = $false
  $f.ClientSize = New-Object Drawing.Size(420, 190)
  if ($Raised) {
    # 창 아래 끝을 화면 가운데보다 `$GhLoginRaise` 만큼 위에 둔다 — 작은 화면에서는 작업 영역 위 끝에 붙는다
    $work = [Windows.Forms.Screen]::PrimaryScreen.WorkingArea
    $top  = $work.Top + [int]($work.Height / 2) - $f.Height - $GhLoginRaise
    $f.StartPosition = 'Manual'
    $f.Location = New-Object Drawing.Point(($work.Left + [int](($work.Width - $f.Width) / 2)), [Math]::Max($work.Top + 8, $top))
  }
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
  $state = @{ Code = ''; Ok = $false; Clock = [Diagnostics.Stopwatch]::StartNew(); NextProbe = 5; Probe = $null; ProbeClock = $null }
  $probeCap = $GhStatusCap
  $startProbe = ${function:Start-GhLoginProbe}
  $stopProbe  = ${function:Stop-GhLoginProbe}
  $bOpen.Add_Click({ Start-Process 'https://github.com/login/device' | Out-Null })
  $bCopy.Add_Click({ if ($state.Code) { try { Set-Clipboard -Value $state.Code } catch { } } }.GetNewClosure())
  $bSkip.Add_Click({ $f.Close() }.GetNewClosure())
  $timer = New-Object Windows.Forms.Timer; $timer.Interval = 1000
  $timer.Add_Tick({
    $left = $Wait - [int][Math]::Floor($state.Clock.Elapsed.TotalSeconds)
    $lLeft.Text = "남은 시간 $([Math]::Max(0, $left))초 — 로그인이 서면 이 창은 스스로 닫힙니다"
    if (-not $state.Code) {
      $said = ''
      foreach ($p in @($OutFile, "$OutFile.err")) {
        if (Test-Path -LiteralPath $p) { $said += (Get-Content -LiteralPath $p -Raw -ErrorAction SilentlyContinue) }
      }
      if ($said -match '([A-Z0-9]{4}-[A-Z0-9]{4})') {
        $state.Code = $Matches[1]; $tCode.Text = $state.Code; $tCode.SelectAll()
        # 코드가 오면 브라우저를 사람 대신 열고 코드를 클립보드에도 둔다 — gh 자신은 콘솔 없는 자식이라 못 여는 판이 있다. 버튼
        #   둘은 브라우저가 안 뜬 판의 손잡이로 남긴다.
        try { Set-Clipboard -Value $state.Code } catch { }
        try { Start-Process 'https://github.com/login/device' | Out-Null } catch { }
      }
    }
    if ($state.Probe) {
      if ($state.Probe.HasExited) {
        $ok = ($state.Probe.ExitCode -eq 0)
        $state.Probe.Dispose(); $state.Probe = $null
        if ($ok) { $state.Ok = $true; $f.Close(); return }
      } elseif ($state.ProbeClock.Elapsed.TotalSeconds -ge $probeCap) {
        & $stopProbe $state.Probe
        $state.Probe = $null
      }
    } elseif ($state.Clock.Elapsed.TotalSeconds -ge $state.NextProbe) {
      $state.NextProbe = $state.Clock.Elapsed.TotalSeconds + 5
      $state.Probe = & $startProbe
      $state.ProbeClock = [Diagnostics.Stopwatch]::StartNew()
    }
    # 로그인 프로세스가 끝났으면(섰든 졌든) 닫는다 — 섰나는 닫은 뒤 한 번 더 잰다
    if (($Proc -and $Proc.HasExited) -or $left -le 0) { $f.Close() }
  }.GetNewClosure())
  $f.Add_Shown({ $f.Activate(); $timer.Start() }.GetNewClosure())
  $f.Add_FormClosed({ $timer.Stop() }.GetNewClosure())
  [void]$f.ShowDialog()
  if ($state.Probe) {
    Stop-GhLoginProbe $state.Probe
    $state.Probe = $null
  }
  if (-not $state.Ok) { $state.Ok = Test-GhLoggedIn }
  return $state.Ok
}

# 창의 틱이 띄우는 「로그인이 섰나」 한 번 — `gh api user` 를 띄우고 기다리지 않고 돌려준다(끝은 부르는 쪽이 `HasExited` 로 본다).
#   못 띄우면 `$null`. 글자는 버린다 — 판정은 종료 코드다. 두 스트림을 끝까지 비워 자식이 파이프 버퍼에 막히지 않게 한다.
function Start-GhLoginProbe {
  $psi = New-NativeStart 'gh' (Join-NativeArgs @('api', 'user', '--jq', '.login'))
  if (-not $psi) { return $null }
  try {
    $p = [Diagnostics.Process]::Start($psi)
    $p.StandardInput.Close()
    $null = $p.StandardOutput.BaseStream.CopyToAsync([IO.Stream]::Null)
    $null = $p.StandardError.BaseStream.CopyToAsync([IO.Stream]::Null)
    return $p
  } catch { return $null }
}

# 창의 재기 하나를 거두고 놓는다 — 나무째(`Stop-ProbeTree`), 프로세스 목록을 못 읽어 그것이 던지면 뿌리만 끈다(그 머리말이 부르는 쪽에 맡긴 몫).
#   뿌리만 끄면 껍데기(`.cmd` · `.ps1`)로 선 gh 의 손자가 남는다. 창의 스레드에서 돌아 목록 묻기가 멎으면 창이 그 한도
#   (`Stop-ProbeTree` 의 10초)만큼 어는데, 거두는 것은 재기가 `$GhStatusCap` 을 넘겼거나 창이 닫힐 때뿐이라 그 값을 받는다.
function Stop-GhLoginProbe([Diagnostics.Process]$Probe) {
  if (-not $Probe) { return }
  try {
    if (-not $Probe.HasExited) {
      try { Stop-ProbeTree $Probe } catch { try { if (-not $Probe.HasExited) { $Probe.Kill() } } catch { } }
    }
  } finally { $Probe.Dispose() }
}

# 코드 창이 사람을 기다리는 한도(초) — Claude 로그인 칸과 같은 값
$GhLoginWait = 180
# 앞당겨 띄운 자식에게 창의 한도 위로 더 주는 초 — 창은 자식이 뜬 때부터 벽시계로 `$GhLoginWait` 에 닫히고(`Invoke-GhLoginChild`),
#   그 뒤 남는 것은 로그인을 한 번 더 재는 몫(`Test-GhLoggedIn` — `$ProbeCap` + `$GhStatusCap`)과 끝나는 몫이다. 이것까지 넘기면
#   「설정 저장소」 걸음이 자식을 거둔다.
$GhLoginGrace = 90
# `-Raised` 창의 아래 끝과 화면 가운데 사이(픽셀) — 화면 한가운데 선 물음창의 위쪽 절반을 비켜 선다
$GhLoginRaise = 140

# 로그인 창을 띄울 판인가 — 「설정 저장소」 걸음의 로그인 칸과 「프로그램」 걸음의 앞당긴 띄우기가 같은 자를 쓴다.
# 내는 것 — `open`(띄운다) · `nogh`(gh 가 안 닿는다) · `already`(이미 서 있다) · `unmeasured`(섰나를 울타리 안에 못 쟀다) ·
#   `night`(밤 자동 실행 · 창을 안 띄운다) · `noreach`(github.com 에 못 닿는다). 그 칸 바깥의 조건(`#config-repo` · git · 개발 도구)은
#   부르는 쪽이 든다.
#   못 쟀으면 · 망이 막혔으면 창을 안 띄운다 — 로그인이 선 PC 에 창을 띄우거나 못 열릴 브라우저를 사람에게 기다리게 하는 꼴이고,
#   거짓인 까닭이 망이면 사람은 엉뚱한 데를 고치러 간다(결정 0141 · Claude 로그인 칸과 같은 규율).
function Get-GhLoginGo {
  if (-not (Test-Runs 'gh' '--version')) { return 'nogh' }
  $timedBefore = $script:ProbeTimedOut.Count
  if (Test-GhLoggedIn) { return 'already' }
  if ($script:ProbeTimedOut.Count -gt $timedBefore) { return 'unmeasured' }
  if ($NightRun) { return 'night' }
  if (-not (Test-Reach 'github.com:443')) { return 'noreach' }
  return 'open'
}

# `gh auth login` 을 숨은 cmd 자식으로 띄운다 — 코드 창(`Show-GhLoginWindow`)이 `$OutFile` 과 `$OutFile.err` 에서 코드를 읽는다.
# ⚠ **gh 는 「Enter 를 누르면 브라우저를 연다」고 묻고 기다린다** — 콘솔이 없는 자식이라 `echo.` 로 빈 줄 하나를 넣어 준다(안 넣으면
#   영영 선다). gh 는 코드를 오류 스트림에 찍으므로 두 스트림을 파일 둘로 받는다(한 파일로 합치는 꼴은 뽑기 검사가 막는다 —
#   파워셸 파일 안의 `2>&1` 은 네이티브 stderr 를 오류로 둔갑시킨다).
function Start-GhLoginProcess([string]$OutFile) {
  $ghExe = (Get-Command gh -ErrorAction Stop).Source
  $cmdArgs = '/d /s /c "echo.| "' + $ghExe + '" auth login --hostname github.com --git-protocol https --web > "' + $OutFile + '" 2> "' + $OutFile + '.err""'
  $p = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\cmd.exe') -ArgumentList $cmdArgs -WindowStyle Hidden -PassThru
  # 손잡이를 지금 쥔다 — 쥐고 있는 동안 이 PID 는 남에게 안 간다(`Stop-GhLoginProcess` 가 끝남을 믿고 나무를 따라갈 자리)
  $null = $p.Handle
  $p
}

# 로그인이 띄우는 것 가운데 거둘 이름 — 앞당긴 자식(powershell) · cmd · gh · 그 콘솔 호스트(창이 재려고 띄운 gh 와 그 껍데기도 든다)
$GhLoginKillNames = @('powershell.exe', 'cmd.exe', 'gh.exe', 'conhost.exe')

# 안 선 로그인을 거둔다 — 뿌리와, 그 아래 `$GhLoginKillNames` 에 든 이름만 나무를 따라 끈다. 목록을 못 읽으면 뿌리만 끈다.
# ⚠ **브라우저는 안 끈다.** 창(코드가 오면 연다)과 gh(`--web`)가 브라우저를 띄우고, 브라우저가 안 떠 있던 PC 에서는 그 브라우저가
#   이 나무 안에서 선다. 나무째 끄면 사람이 쓰던 브라우저 창까지 닫힌다. 이름 목록 밖의 것은 끄지도 그 아래로 내려가지도 않는다.
#   자손은 부모보다 늦게 선 것만 잇고, 뿌리를 먼저 끄고, 자손은 끄기 직전에 시작 시각을 다시 본다 — `Stop-ProbeTree` 와 같은 까닭이다.
#   끝난 뿌리는 나무를 안 따라간다 — 그 PID 는 이미 남의 것일 수 있다. cmd 는 gh 가 끝나야 끝나고(`cmd /c` 의 파이프), 앞당긴 자식은
#   제 로그인을 거두고 끝나므로 끝난 뿌리 아래 거둘 것이 없다. 뿌리는 손잡이를 쥔 Process 로 받는다(`Start-GhLoginProcess` ·
#   `Start-GhLoginChild`) — 쥔 동안은 `HasExited` 가 참이고 PID 가 안 간다.
function Stop-GhLoginProcess([System.Diagnostics.Process]$Proc) {
  if (-not $Proc) { return }
  try { if ($Proc.HasExited) { return } } catch { return }
  $tree = New-Object System.Collections.ArrayList
  try {
    $all = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, CreationDate, Name -OperationTimeoutSec 10 -ErrorAction Stop)
    $kids = @{}
    foreach ($x in $all) {
      $pp = [int]$x.ParentProcessId
      if (-not $kids.ContainsKey($pp)) { $kids[$pp] = New-Object System.Collections.ArrayList }
      [void]$kids[$pp].Add($x)
    }
    $todo = New-Object System.Collections.Queue
    $root = @($all | Where-Object { [int]$_.ProcessId -eq $Proc.Id }) | Select-Object -First 1
    if ($root) { $todo.Enqueue($root) }
    while ($todo.Count) {
      $n = $todo.Dequeue()
      if (-not $kids.ContainsKey([int]$n.ProcessId)) { continue }
      foreach ($c in $kids[[int]$n.ProcessId]) {
        if ($c.ProcessId -ne $n.ProcessId -and $c.CreationDate -ge $n.CreationDate -and
            $GhLoginKillNames -contains "$($c.Name)".ToLowerInvariant() -and -not $tree.Contains($c)) {
          [void]$tree.Add($c); $todo.Enqueue($c)
        }
      }
    }
  } catch { }
  try { if (-not $Proc.HasExited) { $Proc.Kill() } } catch { }
  foreach ($c in $tree) {
    $h = $null
    try {
      $h = Get-Process -Id ([int]$c.ProcessId) -ErrorAction Stop
      if ([Math]::Abs(($h.StartTime - $c.CreationDate).TotalMilliseconds) -lt 1) { $h.Kill() }
    } catch { } finally { if ($h) { $h.Dispose() } }
  }
}

# 자식 쪽 — 이 몸통이 `-GhLoginOnly` 로 떴을 때 하는 일의 전부다. 창 하나를 띄우고 답 한 줄을 결과 파일에 적는다:
#   `ok`(창 안에서 섰다) · `no`(시간이 다 갔거나 [건너뛰기]) · `err <까닭>`(창을 못 세웠다 — 부모가 제 자리에서 다시 띄운다).
# ⚠ **답을 다 쓴 뒤 이름을 옮긴다** — 부모는 파일이 있으면 답이 다 섰다고 읽는다. 반쯤 쓴 파일을 읽지 않게 한다.
#   `gh auth setup-git` 은 부모가 한다 — 자격을 맡기는 일은 저장소를 받는 자리 바로 앞이 제자리다.
function Invoke-GhLoginChild([string]$ResultFile) {
  $said  = 'err 까닭을 못 적었다'
  $gl    = [IO.Path]::GetTempFileName()
  $login = $null
  try {
    $login = Start-GhLoginProcess $gl
    # 창의 한도는 부모가 이 자식을 띄운 때부터 센다 — 부모가 그때부터 UTC 로 재어 거두므로(`Start-GhLoginChild` 의 `Deadline`),
    #   라이브러리를 읽느라 늦게 선 몫만큼 창이 짧아져야 둘이 같은 끝을 본다
    # 두 시각을 다 UTC 로 견준다 — 지역 시각은 서머타임 · 시간대가 바뀌면 그 차만큼 어긋난다
    $age   = [int]([DateTime]::UtcNow - (Get-Process -Id $PID).StartTime.ToUniversalTime()).TotalSeconds
    $said  = if (Show-GhLoginWindow $gl $login ([Math]::Max(1, $GhLoginWait - $age)) -Raised) { 'ok' } else { 'no' }
  } catch {
    $said = 'err ' + (Say-Why $_)
  } finally {
    if ($said -ne 'ok') { Stop-GhLoginProcess $login }
    Remove-Item -LiteralPath $gl, "$gl.err" -ErrorAction SilentlyContinue
  }
  [IO.File]::WriteAllText("$ResultFile.tmp", $said, (New-Object Text.UTF8Encoding($false)))
  Move-Item -LiteralPath "$ResultFile.tmp" -Destination $ResultFile -Force
}

# 부모 쪽 — 이 몸통(`$Engine` · 부르는 쪽이 제 파일 경로를 넘긴다)을 `-GhLoginOnly <결과 파일>` 로 숨겨 띄운다. 내는 것 —
#   @{ Proc; Result; Deadline; Why } — `Deadline` 은 UTC 다(자식이 제 나이를 UTC 로 재는 것과 같은 자). 못 띄웠으면 `Proc` 이 비고 `Why` 가
#   까닭을 든다.
# ⚠ **손잡이를 하나도 안 물려준다**(`CreateProcess` 의 상속 끔 · 표준 손잡이 셋은 비움). 물려주면 이 설치의 출력 파이프를 자식이
#   제 수명 동안 쥐어, 이 설치가 끝나도 읽는 쪽(자동 실행의 `… | ForEach-Object` · 화면 껍데기)이 끝을 못 받고 자식이 끝날 때까지 선다.
#   그래서 자식의 글자는 자식 파워셸이 스스로 결과 파일 곁의 `.log` 에 쓴다(`*>`) — 답이 안 섰을 때 까닭으로 편다.
# ⚠ **콘솔 없이 띄운다**(`CREATE_NO_WINDOW`) — 숨김 창(`-WindowStyle Hidden`)은 Windows Terminal 이 기본 터미널인 PC 에서 번쩍 뜬다(결정 0150).
function Start-GhLoginChild([string]$Engine) {
  $result = Join-Path ([IO.Path]::GetTempPath()) ('paisetup-gh-login-' + [guid]::NewGuid().ToString('N') + '.txt')
  try {
    if (-not ('PAISetupGh.Spawn' -as [type])) {
      Add-Type -Namespace PAISetupGh -Name Spawn -MemberDefinition @'
[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential, CharSet = System.Runtime.InteropServices.CharSet.Unicode)]
public struct SI { public int cb; public string r; public string d; public string t; public int x; public int y; public int xs; public int ys; public int xc; public int yc; public int fa; public int flags; public short show; public short r2; public System.IntPtr r3; public System.IntPtr i; public System.IntPtr o; public System.IntPtr e; }
[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
public struct PI { public System.IntPtr hp; public System.IntPtr ht; public int pid; public int tid; }
[System.Runtime.InteropServices.DllImport("kernel32.dll", SetLastError = true, CharSet = System.Runtime.InteropServices.CharSet.Unicode)]
static extern bool CreateProcess(string app, System.Text.StringBuilder cmd, System.IntPtr pa, System.IntPtr ta, bool inherit, uint flags, System.IntPtr env, string dir, ref SI si, out PI pi);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern bool CloseHandle(System.IntPtr h);
// 손잡이를 안 물려주고(상속 끔 · STARTF_USESTDHANDLES 에 빈 손잡이 셋) 콘솔 없이(CREATE_NO_WINDOW) 띄운다. 내는 것 — 프로세스 손잡이(부르는 쪽이 닫는다). 못 띄우면 던진다.
public static System.IntPtr StartBare(string app, string cmd, out int pid) {
  SI si = new SI(); si.cb = System.Runtime.InteropServices.Marshal.SizeOf(si); si.flags = 0x100;
  PI pi;
  if (!CreateProcess(app, new System.Text.StringBuilder(cmd), System.IntPtr.Zero, System.IntPtr.Zero, false, 0x08000000, System.IntPtr.Zero, null, ref si, out pi))
    throw new System.ComponentModel.Win32Exception(System.Runtime.InteropServices.Marshal.GetLastWin32Error());
  CloseHandle(pi.ht); pid = pi.pid; return pi.hp;
}
'@
    }
    $ps  = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    # 파워셸은 ' 말고도 U+2018 ~ U+201B 를 작은따옴표로 읽는다 — 겹치기는 파워셸 자신의 손에 맡긴다
    $q   = { param($t) "'" + [Management.Automation.Language.CodeGeneration]::EscapeSingleQuotedStringContent($t) + "'" }
    # 던진 것(구문 오류 · 잡히지 않은 예외)은 `*>` 를 비켜 나가므로 잡아서 글로 남긴다
    $cmd = '"' + $ps + '" -NoProfile -ExecutionPolicy Bypass -Command "& { try { & ' + (& $q $Engine) + ' -GhLoginOnly ' + (& $q $result) +
           ' } catch { $_.ToString() } } *> ' + (& $q "$result.log") + '"'
    $childPid = 0
    $hp = [PAISetupGh.Spawn]::StartBare($ps, $cmd, [ref]$childPid)
    # 손잡이를 쥔 채 Process 를 잡는다 — 그 사이 끝나 PID 가 남에게 가는 틈이 없다
    try { $p = [Diagnostics.Process]::GetProcessById($childPid); $null = $p.Handle }
    finally { $null = [PAISetupGh.Spawn]::CloseHandle($hp) }
    return @{ Proc = $p; Result = $result; Why = ''; Deadline = [DateTime]::UtcNow.AddSeconds($GhLoginWait + $GhLoginGrace) }
  } catch {
    return @{ Proc = $null; Why = (Say-Why $_) }
  }
}

# 앞당겨 띄운 자식의 답을 받는다 — 남은 시간(`Deadline` 까지)만 기다리고, 넘기면 거둔다(`-Now` 면 안 기다리고 바로). 내는 것 —
#   @{ Said; Err }: `Said` 는 자식이 적은 답(`ok` · `no` · `err …`), 거뒀으면 `late`, 답 없이 끝났으면 빈 글자. `Err` 는 자식이
#   제 `.log` 에 낸 첫 줄(답이 안 섰을 때의 까닭 — 파워셸 오류 기록은 첫 줄이 말이다). 결과 파일과 곁 파일은 지운다.
function Wait-GhLoginChild($C, [switch]$Now) {
  $said = ''
  if (-not $C.Proc.HasExited) {
    $left = if ($Now) { 0 } else { [int][Math]::Ceiling(($C.Deadline - [DateTime]::UtcNow).TotalSeconds) }
    if ($left -gt 0) {
      Say-Busy 'GitHub 로그인 창' 'wait' @('앞서 띄운 창', "남은 최대 ${left}초")
      $null = $C.Proc.WaitForExit($left * 1000)
    }
    if (-not $C.Proc.HasExited) {
      Stop-GhLoginProcess $C.Proc; $said = 'late'
      # 끝이 와야 자식이 쥔 `.log` 가 풀려 아래에서 지워진다
      $null = $C.Proc.WaitForExit(5000)
    }
  }
  if (Test-Path -LiteralPath $C.Result) {
    $said = ([string](Get-Content -LiteralPath $C.Result -Raw -Encoding UTF8 -ErrorAction SilentlyContinue)).Trim()
  }
  # `*>` 가 쓴 파일이라 BOM 이 인코딩을 댄다 — 읽는 쪽이 인코딩을 박지 않는다
  $err = @(Get-Content -LiteralPath "$($C.Result).log" -ErrorAction SilentlyContinue | Where-Object { "$_".Trim() }) | Select-Object -First 1
  Remove-Item -LiteralPath $C.Result, "$($C.Result).tmp", "$($C.Result).log" -ErrorAction SilentlyContinue
  return @{ Said = $said; Err = "$err".Trim() }
}

#endregion 도구별 · gh

#region 앱 열기 — 끝에 띄울 앱을 찾고, 이미 돌고 있으면 끌지 묻고 끈다

# VS Code 를 띄울 손잡이 — @{ Name; Exe; Dir; Proc }, 못 찾으면 `$null`. PATH 의 `code` 는 `…\bin\code.cmd` 라 띄우면 콘솔이 번쩍여,
#   한 층 올라가 `Code.exe` 를 판다. 자리를 이름으로 박지 않는다 — 박으면 배선(`Update-RuntimePath`)의 목록과 사본이 되고, 부르는
#   쪽이 `code` 가 도는 판(`$hasCode`)에만 오므로 PATH 에서 못 파는 갈래에는 닿지 않는다.
function Find-VSCode {
  $c = Get-Command code -ErrorAction SilentlyContinue
  if (-not $c -or -not $c.Source) { return $null }
  # ⚠ **빈 것을 `Join-Path` 에 넘기지 않는다** — `Stop` 이 그 자리에서 던지는데, 여기는 설치의 마지막 칸이라 멀쩡히 끝난 설치가
  #   실패로 보고된다.
  $vsRoot = Split-Path (Split-Path $c.Source -Parent) -Parent
  if (-not $vsRoot) { return $null }
  $exe = Join-Path $vsRoot 'Code.exe'
  if (-not (Test-Path -LiteralPath $exe)) { return $null }
  return @{ Name = 'VS Code'; Exe = $exe; Dir = $vsRoot
            Proc = [IO.Path]::GetFileNameWithoutExtension($exe) }
}

# 데스크탑 앱을 띄울 손잡이 — 이 판에서 선 앱(`$script:InstalledAppRows`) 가운데 시작 메뉴에서 찾은 것마다 @{ Name; AppId;
#   Proc = 프로세스 이름 후보; App; Dir = 설치 폴더(못 팠으면 빈 값) } 를 다 낸다(하나만 고르지 않는다 — 고르면 그 차례가 표 행
#   순서에 숨는다).
#   자리를 묻지 않고 윈도우에 앱을 묻는다(`Get-StartApps` — 띄울 수 있는 앱과 그 손잡이를 꼴과 상관없이 같은 답으로 낸다). 스토어
#   꼴(MSIX)로 깔리면 실행 파일도 `Uninstall` 등록도 시작 메뉴 `.lnk` 도 안 생기고 실물 자리(`WindowsApps`)는 권한으로 막혀 경로로는
#   못 찾는다. 찾을 이름은 표의 `App` 칸이 든다.
#   고른 것이 아니라 이 판에서 선 것을 훑는다(0059) — 고른 것으로 훑으면 사내에서 안 깐 앱(`When = offsite`)을 「못 찾았다」로
#   찍는다. 부르는 쪽도 같은 자에 묻는다.
function Find-DesktopApps {
  $rows = @($script:InstalledAppRows.Values)
  if (-not $rows) { return @() }                # 이 판에서 선 데스크탑 앱이 없다
  # 막 깐 앱은 시작 메뉴에 늦게 설 수 있다 — 다 찾으면 바로 나가고, 못 찾은 것이 남을 때만 2초 틈으로 다섯 번까지 묻는다(이미 선
  #   기계는 기다리지 않는다).
  $all = @()
  for ($try = 0; $try -lt 5; $try++) {
    try {
      $all = @(Get-StartApps -ErrorAction Stop)
    } catch { return @() }                      # 이 윈도우에 그 물음이 없다
    $lack = @($rows | Where-Object { $w = $_.App; -not @($all | Where-Object { $_.Name -like "*$w*" })[0] })
    if (-not $lack) { break }
    Start-Sleep -Seconds 2
  }
  # 바로가기 꼴의 대상 실행 파일 — 시작 메뉴가 손잡이마다 안다. 스토어 꼴은 바로가기가 아니라 비어 있다.
  $linkTarget = @{}
  try {
    foreach ($i in (New-Object -ComObject Shell.Application).NameSpace('shell:AppsFolder').Items()) {
      $t = [string]$i.ExtendedProperty('System.Link.TargetParsingPath')
      if ($t -and $t.EndsWith('.exe', [StringComparison]::OrdinalIgnoreCase)) { $linkTarget[[string]$i.Path] = $t }
    }
  } catch { }
  $out = @()
  foreach ($appPick in $rows) {
    $a = @($all | Where-Object { $_.Name -like "*$($appPick.App)*" })[0]
    if (-not ($a -and $a.AppID)) { continue }
    $want = $appPick.App; $label = $appPick.Label
    # 프로세스 이름은 후보 목록이다 — 손잡이에서 판 것 하나와 앱 이름 하나(`Get-Process -Name` 은 목록을 받는다). 손잡이의 꼴이
    #   셋이라(스토어 꼴 `앱_해시!앱` 의 `_` 앞 · 바로가기 꼴의 파일 이름 · Squirrel 설치본 `com.squirrel.<패키지>.<실행파일>` 의
    #   마지막 마디) 손잡이 하나로는 못 판다 — 세 꼴 다 실행 파일이 곧 앱 이름(`claude`)이라 앱 이름을 더하면 셋이 덮인다. 떠 있는
    #   앱을 「안 떴다」로 읽으면 묻지도 끄지도 않고 띄워, 도는 앱은 창만 앞으로 올 뿐 낡은 채로 남는다.
    $fromId = if ($a.AppID -match '!') { ($a.AppID -split '_')[0] }
              else { [IO.Path]::GetFileNameWithoutExtension($a.AppID) }
    $procs = @($fromId, $want) | Where-Object { $_ } | Select-Object -Unique
    # ⚠ **이름만으로는 그 앱인지 못 가른다 — 설치 폴더를 같이 든다.** `claude` 라는 이름에는 데스크탑 앱 말고도 VS Code 확장이
    #   띄우는 CLI(`…\resources\native-binary\claude.exe`)와 데스크탑이 품은 Claude Code(`%APPDATA%\Claude\claude-code\…\claude.exe`)가
    #   걸린다. 이름만 물으면 VS Code 가 떠 있는 것만으로 방금 깐 데스크탑이 「이미 실행되었다」로 빠져 안 뜨고, 「끈다」를 누르면
    #   확장과 터미널의 Claude Code 세션까지 죽인다. 폴더를 못 판 꼴은 `Dir` 가 비고, 그때는 이름으로만 묻는다.
    $dir = $null
    if ($a.AppID -match '^([^!]+)!') {
      # 스토어 꼴 — 손잡이 앞마디가 패키지 가족 이름이다. 그 패키지의 설치 자리를 윈도우에 묻는다.
      $fam = $Matches[1]
      try {
        $pkg = @(Get-AppxPackage -Name ($fam -replace '_[^_]+$', '') -ErrorAction Stop |
                 Where-Object { $_.PackageFamilyName -eq $fam })[0]
        if ($pkg) { $dir = [string]$pkg.InstallLocation }
      } catch { }
    } elseif ($a.AppID -match '^com\.squirrel\.([^.]+)\.') {
      # Squirrel 꼴 — `%LOCALAPPDATA%\<패키지>\app-<판>\` 아래에서 돈다(위 곁말의 셋째 꼴).
      $dir = Join-Path $env:LOCALAPPDATA $Matches[1]
    } elseif ($linkTarget[$a.AppID]) {
      # 바로가기 꼴 — 바로가기가 가리키는 실행 파일이 곧 그 앱이라 이름도 폴더도 그 파일에서 읽는다. 손잡이 · 앱 이름에서 짐작하지
      #   않는다 — GitHub Copilot 은 손잡이가 `com.github.githubapp` 이고 실물이 `github.exe` 라 어느 쪽에서도 안 나온다.
      $exe = $linkTarget[$a.AppID]
      $procs = @([IO.Path]::GetFileNameWithoutExtension($exe))
      $dir = Split-Path -Parent $exe
    }
    $out += @{ Name = $label; AppId = $a.AppID; Proc = @($procs); App = $want; Dir = $dir }
  }
  return @($out)
}

# 그 앱의 프로세스 — 이름으로 모으고, 설치 폴더를 알면 **그 아래에서 도는 것만** 남긴다(까닭은
# `Find-DesktopApps` 의 `Dir` 곁말). 경로를 못 읽는 프로세스(다른 권한)는 그 앱이라고 치지 않는다.
function Get-AppProcs($App) {
  if (-not $App -or -not $App.Proc) { return @() }
  $ps = @(Get-Process -Name $App.Proc -ErrorAction SilentlyContinue)
  if (-not $App.Dir) { return $ps }
  $root = ([string]$App.Dir).TrimEnd('\') + '\'
  return @($ps | Where-Object {
    $p = $null
    try { $p = $_.Path } catch { }
    $p -and $p.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)
  })
}

# 그 앱이 이미 도나.
function Test-AppUp($App) {
  return (@(Get-AppProcs $App).Count -gt 0)
}

# 이미 돌고 있는 앱을 끌지 사람에게 묻는다 — 「끈다」면 참이다. 이 창에는 콘솔이 없어(화면 껍데기가 `CreateNoWindow` 로 띄우고
#   표준입력을 NUL 로 돌린다) `Read-Host` 가 못 서므로 물음창(`Show-AskDialog` · #17)으로 묻는다.
function Ask-Restart([string]$AppName) {
  # ⚠ **묻는 자리를 가르는 것은 `-Yes` 가 아니라 「누를 사람이 있나」다** — 화면 껍데기는 사람을 앞에 두고도 몸통을 늘 `-Yes` 로
  #   부른다. `-Yes` 로 이 물음을 지우면 화면으로 깐 사람이 안 물어지고, 떠 있던 낡은 창이 남는데 사람은 재시작한 줄 안다.
  # 세션 0(서비스 · 「로그온하지 않아도 실행」 스케줄러 · CI)에는 누를 사람이 없어 모달 앞에서 설치가 선다 — `UserInteractive` 가
  #   그 둘을 가른다(껍데기는 사람 데스크탑 위라 참). 안 묻는 쪽의 답은 「안 끈다」다 — 설치가 제 손으로 끄면 사람이 띄워 둔 창과
  #   저장 안 한 것이 말없이 날아간다.
  if (-not [Environment]::UserInteractive) {
    Write-Host '  물을 자리가 없다 (세션 0 · 서비스 · 스케줄러) — 안 묻고 그대로 둔다'
    return $false
  }
  Write-Host '  끌지 묻는다 — 창이 뜬다'
  $msg = "$AppName — 이미 돌고 있습니다.`n`n" +
         "지금 껐다 새로 열까요?`n" +
         "돌던 것은 방금 깔린 것(키 · 세션 훅)을 모릅니다.`n`n" +
         "저장 안 한 것이 있으면 먼저 저장하고 눌러 주세요."
  return (Show-AskDialog $AppName $msg)
}

# 그 앱을 끈다 — 곱게 먼저(창 닫기 · 5초까지), 안 나가면 세게(Kill). 다 나갔으면 참이다.
#   곱게가 먼저인 까닭 — VS Code 는 창을 닫으라 하면 저장을 묻는다. 세게가 있는 까닭 — 데스크탑은 창을 닫아도 트레이로 내려갈 뿐
#   안 나간다. 이름이 같은 자식들(VS Code 의 창 · 확장 · GPU, 데스크탑의 프로세스 여럿)까지 다 들되, 그 앱의 것만 끈다 — 이름이
#   같은 남(확장이 띄운 CLI 등)은 `Get-AppProcs` 가 걸러 준다.
function Stop-App($App) {
  foreach ($p in @(Get-AppProcs $App)) {
    if ($p.MainWindowHandle -ne 0) { $null = $p.CloseMainWindow() }
  }
  # 5초까지 기다리되 나가면 바로 넘어간다 — 안 기다려도 될 때 기다리지 않는다.
  for ($i = 0; $i -lt 10 -and (Test-AppUp $App); $i++) { Start-Sleep -Milliseconds 500 }
  foreach ($p in @(Get-AppProcs $App)) {
    try { $p.Kill() } catch { }
  }
  for ($i = 0; $i -lt 6 -and (Test-AppUp $App); $i++) { Start-Sleep -Milliseconds 500 }
  return (-not (Test-AppUp $App))
}

#endregion 앱 열기

#region 심기 · 제공기능 — 홈 씨앗 몸통의 `--plant` 를 부르고, 새 작은 판을 처음 깐 PC 에서 설치 끝에 「제공기능」을 한 번 연다

# 심기만 — 홈 씨앗의 세션 훅을 `--plant <작업 루트>` 로 부른다(claude-config 결정 0134 · 부르는 자리와 차례는 결정 0135). 저장소를
#   받았든 안 받았든 같은 홈 씨앗을 부른다 — 홈 씨앗은 늘 서 있고, 몸통은 거기서 홈 훅 · 고른 도구의 폴더 신뢰 · 데스크탑 상태를 심는다.
# 작업 루트는 저장소를 받는 자리(`$configRepoRoot` — `Get-ConfigRepoDir` 가 받는 자리를 짓는 그 값)를 그대로 받는다. 몸통은 받은 글자를
#   `pwd` 로만 굳혀(대소문자 · 짧은 이름은 그대로) 홈 훅 명령에 박으므로, 받은 저장소의 `--install` 이 제 자리에서 잡는 루트와 글자가
#   다르면 두 부름이 설치마다 그 명령을 번갈아 갈아 심는다(결정 0032). 없으면 부르는 동안만 짓는다 — 몸통은 없는 루트에 아무것도 안
#   심는다(2로 끝난다). 이 부름이 지은 루트가 끝에 비어 있으면 걷는다 — 칸이 빈 PC 에 빈 `~/repos` 를 남기지 않는다(claude-config 결정
#   0138). 심은 홈 훅은 그 자리가 없어도 0 으로 끝나고, 사람이 그 자리에 저장소를 두면 그때부터 훑는다.
# ⚠ **루트는 `/` 꼴로 끝의 구분자 없이 넘긴다** — 5.1 은 빈칸이 든 인자를 따옴표로 싸는데 끝의 `\` 가 닫는 따옴표를 글자로 만들어
#   bash 에 `…\"` 가 간다(그러면 몸통이 그 자리로 못 들어가 2로 끝난다). 훅 자리도 `--install` 처럼 `/` 꼴로 넘긴다.
# 내는 것 — @{ Ran = 불렀나; Ok = 0 으로 끝났나; Why = 안 불렀거나 0 이 아닌 까닭 }. 실패로 셀지는 부르는 쪽이 든다.
function Invoke-Plant([string]$Bash, [string]$Root) {
  $hook = Join-Path $ConfigSeedHooks 'session-start.sh'
  if (-not $Bash) { return @{ Ran = $false; Ok = $false; Why = 'Git Bash 가 없다' } }
  if (-not (Test-Path -LiteralPath $hook -PathType Leaf)) { return @{ Ran = $false; Ok = $false; Why = "홈 씨앗에 훅이 없다 ($hook)" } }
  $rootArg = ($Root -replace '\\', '/').TrimEnd('/')
  $t = Get-Took
  $made = -not (Test-Path -LiteralPath $Root)
  try {
    New-Item -ItemType Directory -Path $Root -Force | Out-Null
    Write-Host "  심기만 — $hook --plant $rootArg" -ForegroundColor Green
    Write-Host ''
    # ⚠ 몸통의 줄은 `Out-Host` 로 화면에 낸다 — 함수 안에서 그냥 부르면 bash 의 stdout 이 이 함수가 내는 값에 섞여, 설치 화면 ·
    #   자동 실행 로그에 한 줄도 안 남는다(심었다 · 미뤘다 · 진 까닭). 종료값은 그대로 `$LASTEXITCODE` 가 든다.
    & $Bash ($hook -replace '\\', '/') --plant $rootArg | Out-Host
    $rc = $LASTEXITCODE
  } catch {
    return @{ Ran = $true; Ok = $false; Why = (Say-Why $_) }
  } finally {
    # 지은 루트를 비었을 때만 걷는다 — 폴더 하나만 지우는 `Directory.Delete` 는 무엇이 들었으면 던지고 아무것도 안 지운다
    if ($made) { try { [IO.Directory]::Delete($Root) } catch { } }
  }
  Write-Took '심기 --plant' $t
  @{ Ran = $true; Ok = ($rc -eq 0); Why = "exit $rc" }
}

# 「제공기능」(곁의 `features.html`)을 작은 판(`VERSION` 의 앞 두 수 — `큰.작은`)마다 한 번 연다 — 설치 창 · 콘솔 · 로그온 자동 실행 어느
#   판이든 설치 끝에서다(claude-config 결정 0147 — 0135 의 그 갈래를 대신한다). SemVer 의 가운데 자리가 기능이 더해진 판이라, 다시 깔면
#   새것이 오는 판이 거기서 오른다. 옛 제작자 칸 알림 창을 띄운 판(`$NoticeShown`)은 그 창이 닫힐 때 연다(결정 0099) — 두 번 안 연다.
# 기록은 설치본 자리(`%LOCALAPPDATA%\Claude Code Setup`)의 한 줄 — 본 작은 판(`큰.작은`)이다. 알림 창을 띄운 판도 적는다 — 본 것은 같아,
#   다음 설치가 또 열지 않는다. 열지 못했으면 안 적는다 — 다음 설치가 다시 연다. 옛 기록(본 큰 판의 수 하나 · 0135)은 그 큰 판의 .0 을
#   본 것으로 읽고, 못 읽는 기록은 없는 것으로 본다. 파일 이름(`features.major`)은 옛 기록을 이어 읽으려고 그대로 둔다.
# 내는 것 — 한 낱말: opened · notice · seen · nopage · failed · nover. 화면 줄은 부르는 쪽이 든다.
function Open-FeaturesOnce([string]$Version, [bool]$NoticeShown, [string]$Record, [string]$Page) {
  if ($Version -notmatch '^(\d+)\.(\d+)') { return 'nover' }
  $now = [version]"$($Matches[1]).$($Matches[2])"
  $seen = $null
  try {
    if (Test-Path -LiteralPath $Record -PathType Leaf) {
      $txt = ([IO.File]::ReadAllText($Record) -replace "^$([char]0xFEFF)", '').Trim()
      if ($txt -match '^\d+\.\d+$') { $seen = [version]$txt }
      elseif ($txt -match '^\d+$')  { $seen = [version]"$txt.0" }
    }
  } catch { $seen = $null }
  if ($seen -and $seen -ge $now) { return 'seen' }
  $how = 'notice'
  if (-not $NoticeShown) {
    if (-not (Test-Path -LiteralPath $Page -PathType Leaf)) { return 'nopage' }
    try { Open-InBrowser $Page; $how = 'opened' } catch { return 'failed' }
  }
  try {
    New-Item -ItemType Directory -Path (Split-Path -Parent $Record) -Force | Out-Null
    [IO.File]::WriteAllText($Record, "$($now.Major).$($now.Minor)", (New-Object Text.UTF8Encoding($false)))
  } catch { }
  $how
}

#endregion 심기 · 제공기능

#endregion 라이브러리

# ── 앱 이름 — **진본은 값 파일의 `#app-name` 한 줄이다** ─────────────────────────
# 이름이 찍히는 자리(바로가기 이름 · 바로가기 설명 · 물음 상자 제목 · 설치 창의 제목)는 다 `$AppName` 에서 판다 — 자리마다 글자를
#   박으면 이름을 바꾸는 날 한 자리만 낡는다. 설치 창은 `-Describe` 의 `app-name|` 줄로 받으므로 그 갈래보다 앞에 선다.
#   여기 든 글자는 진본이 아니라 울타리다: 값 파일이 그 줄을 안 들면(이전 배포본 · 이 파일만 떼어 받은 사람) 바로가기가 `.lnk` 라는
#   이름 없는 아이콘으로 서고 상자 제목이 빈칸이 된다.
$AppNameDefault = 'PAI Setup Wizard'
$AppName = Read-Directive $DistEnvFile 'app-name'
if (-not $AppName) { $AppName = $AppNameDefault }

# ── `-Describe` 갈래 — 고를 목록 · 저장소 자리 · 지난번에 고른 것 · 몸통만 아는 사실을 내주고 나간다 ──────────────────────
# 내는 줄 — `product|키|글자|기본값`(제품마다) · `config-repo-root|자리` · `record|이름|값`(기록에 든 것마다 · `Read-ChoiceRecord`) ·
#   `company-key|yes·no`(이 사용자가 풀 수 있는 회사 키 덩이가 있나 · 값은 안 낸다), 그 뒤에 몸통만 아는 사실(PAISetup #46):
#     · `app-name|이름` · `vcruntime-min|판` · `personal|도구|제품|글자`(`$PersonalTools` 마다) — 설치 창의 제목 · 「올리기」 칸 글자 ·
#       제작자 칸
#     · `site|inside·outside|프로브` 나 `site|error|까닭` — 이 PC 의 자리(`Measure-Site`). `error` 면 창은 설치를 안 받는다
#     · `vscode|required·optional` — 이 자리에서 VS Code 가 필수인가(`Test-VsCodeRequired`)
#     · `autorun|on·off` — 깃발 없는 판의 자동 실행(`Get-AutoRunDefault` · 그대로 둠은 작업이 있나로)
#     · `app|키|yes·outside·no` — 데스크탑 앱 행이 이 자리에서 깔리나 · 사외에서만 깔리나 · 안 깔리나(`Test-DesktopAppHere`)
#   종료 0. 여기까지는 선언과 함수 정의뿐이라 부수효과가 없다 — 빗장 앞이라 다른 설치가 돌아도 답한다.
#   이것들을 내주는 것은 화면이 몸통의 자리 · 규칙 · 기본값 · 기록 자리 · 기록 꼴을 제 글자로 다시 짓지 않게 하려는 것이다 — 다시
#   지으면 같은 PC 가 창 회차와 로그온 회차에서 다른 자리 · 다른 칸으로 돈다(`$configRepoRoot` · 「회차를 넘기는 기록의 자리」 곁말).
# 덩이는 「키와 값」과 같은 손(`Convert-CompanyKeyBlob`)으로 풀어 보고, 풀려 빈 키가 아닐 때만 `yes` 다 — 다른 사용자 · 다른 PC 의
#   덩이나 깨진 덩이에 `yes` 라 하면 창이 빈 키 칸을 받고 그 판은 「미입력」 빨강으로 끝난다. 푼 바이트는 바로 지운다. 못 푸는 덩이를
#   여기서 지우지 않는다 — 지우는 것은 그 덩이를 다시 쓸 수 있는 「키와 값」의 몫이다(`Read-CompanyKeyBlob`).
if ($Describe) {
  $Products | ForEach-Object {
    'product|{0}|{1}|{2}' -f $_.Key, $_.Label, $(if ($_.Default) { 'on' } else { 'off' })
  }
  'config-repo-root|{0}' -f $configRepoRoot
  $described = Read-ChoiceRecord $ChoiceRecord $LegacyChoiceArgs $LegacyChoiceEnv $AutoRunOffRecord
  foreach ($k in @($described.Keys | Sort-Object)) { 'record|{0}|{1}' -f $k, $described[$k] }
  $keySaved = $false
  $keyPlain = $null
  try {
    if (Test-Path -LiteralPath $CompanyKeyBlob -PathType Leaf) {
      $keyPlain = Convert-CompanyKeyBlob ([IO.File]::ReadAllBytes($CompanyKeyBlob))
      $keySaved = [bool]($keyPlain -and $keyPlain.Length)
    }
  } catch { $keySaved = $false } finally { if ($keyPlain) { [Array]::Clear($keyPlain, 0, $keyPlain.Length) } }
  'company-key|{0}' -f $(if ($keySaved) { 'yes' } else { 'no' })
  'app-name|{0}' -f $AppName
  'vcruntime-min|{0}' -f $VcRuntimeMin
  $PersonalTools | ForEach-Object { 'personal|{0}|{1}|{2}' -f $_.Tool, $_.Product, $_.Label }
  $descProbe = Read-Directive $DistEnvFile 'site-probe'
  $descSite  = Measure-Site $descProbe
  if ($descSite.Site) { 'site|{0}|{1}' -f $descSite.Site, $descProbe } else { 'site|error|{0}' -f $descSite.Why }
  'vscode|{0}' -f $(if (Test-VsCodeRequired $descSite.Site) { 'required' } else { 'optional' })
  $descAuto = Get-AutoRunDefault (Read-Directive $DistEnvFile 'autorun')
  if ($null -eq $descAuto) { $descAuto = (Test-AutoRunTask $AutoRunTaskName) -or (Test-AutoRunTask $AutoRunNightTaskName) }
  'autorun|{0}' -f $(if ($descAuto) { 'on' } else { 'off' })
  $descApp = Read-DesktopAppSwitch (Read-Directive $DistEnvFile 'desktop-app')
  foreach ($da in $DesktopApps) {
    $here = if (Test-DesktopAppHere $da $descApp.When ($descSite.Site -eq 'outside')) { 'yes' }
            elseif (Test-DesktopAppHere $da $descApp.When $true) { 'outside' } else { 'no' }
    'app|{0}|{1}' -f $da.Key, $here
  }
  exit 0
}

# ── GitHub 로그인 창만 띄우는 자식 — 「프로그램」 걸음이 띄운다(`Start-GhLoginChild`) ───────────────────────
# 라이브러리를 다 읽은 뒤 · 빗장 **앞에서** 나간다. 빗장을 쥐면 저를 띄운 설치와 겹침으로 읽혀 물러나고, 아래 준비는 사람 환경을
#   만진다 — 이 자식이 할 일은 창 하나와 답 한 줄뿐이다(`Invoke-GhLoginChild`).
if ($GhLoginOnly) {
  Invoke-GhLoginChild $GhLoginOnly
  exit 0
}

# ══ 준비 ═══════════════════════════════════════════════════════════════════════════════════════
#   층 — 없음(걸음 앞)
#   하는 일 — 겹쳐 도는 것을 막는 빗장 · 고른 제품 · 묻고 잴 이름 표 · winget 되살리기 · 자리 재기 · 조건 값 ·
#     설정 저장소 주소 · 올릴 것 훑기
#   앞에서 받는 것 — 매개변수 · 값 파일 · 위의 표와 라이브러리
#   안 하는 것 — 고른 제품을 안 깔고, 사용자 환경과 홈을 안 만진다. winget 되살리기만 깔 도구 자체를 세운다

# ── 단일 실행 빗장 (Mutex) — **겹쳐 도는 것을 뿌리에서 막는다** ────────────────
# 부팅 자동화 · 로그온 자동 실행 · 사람의 실행이 겹치면 같은 환경변수와 설정 파일을 동시에 덮어써 반쪽 상태가 남는다(PAISetup #13).
# 막힌 쪽에는 쥔 쪽의 번호와 경과를 댄다 — 「진행 중」만으로는 정상 진행과 멎은 고아를 못 가른다. 사람이 있으면 끝내고 이어갈
#   길을 준다 — 고아는 기다려서 안 풀린다(PAISetup #17).
# 밤 자동 실행이 부른 설치인가(`$NightRun`) — 자동 실행 몸통이 이 프로세스에만 넘기는 환경변수로 안다. 값 파일의 줄로 안 넘긴다 —
#   그 파일은 자동 실행용 사본으로 얼려져 다음 로그온 회차까지 따라간다. 밤 회차는 어떤 창도 안 띄운다 — 겹침 물음(아래) · 로그인
#   브라우저 · 알림 창 · 「제공기능」이 이 값을 보고 건너뛰거나 물러난다(PAISetup #36).
$NightRun = ($env:PAISETUP_AUTORUN_NIGHT -eq '1')

$script:EngineMutex = $null
$script:HasEngineMutex = $false
try {
  $script:EngineMutex = New-Object System.Threading.Mutex($false, "Local\PAISetup-Engine-Lock")
  $script:HasEngineMutex = $script:EngineMutex.WaitOne(0, $false)
} catch {
  $script:HasEngineMutex = $true
}

$holders = @(Find-EngineHolders)
if (-not $script:HasEngineMutex -or $holders.Count -gt 0) {
  Write-Host ''
  Write-Host '  이미 다른 설치 또는 자동 실행이 진행 중입니다.' -ForegroundColor Yellow
  foreach ($h in $holders) { Write-Host ('  ' + (Format-EngineHolder $h)) }
  if (-not $holders) {
    Write-Host '    · 쥔 프로세스를 못 찾았다 — 방금 끝났거나 다른 사용자 것이다'
  }

  # ⚠ **묻는 자리를 가르는 것은 `-Yes` 가 아니라 「누를 사람이 있나」다**(`Ask-Restart` 와 같은 자) — 화면 껍데기는 사람을 앞에
  #   두고도 몸통을 늘 `-Yes` 로 부르므로, `-Yes` 에 걸면 화면으로 깐 사람은 영영 안 물어본다. 누를 사람이 없는 것은 세션 0
  #   (서비스 · 「로그온하지 않아도 실행」 스케줄러 · CI)뿐이고 `UserInteractive` 가 그것을 가른다.
  if (-not [Environment]::UserInteractive) {
    Write-Host '  물을 자리가 없다 (세션 0 · 서비스 · 스케줄러) — 겹치지 않게 물러납니다.' -ForegroundColor Yellow
    exit 1
  }
  if ($NightRun) {
    Write-Host '  밤 자동 실행이라 묻지도 기다리지도 않고 물러납니다 — 다음 회차가 잇는다.' -ForegroundColor Yellow
    exit 1
  }

  Write-Host '  잠시 기다립니다 (최대 60초)...'
  # ⚠ **버려진 빗장은 잡힌 것이다.** 기다리는 동안 쥔 쪽이 죽으면 `WaitOne` 이 던지는데, 그때 소유권은 이쪽에 넘어와 있다 —
  #   삼키고 거짓으로 두면 방금 얻은 것을 못 쓴다. 세션이 다른 프로세스(S4U 등)는 Mutex 로 안 잡혀 `Find-EngineHolders` 도 함께 잰다.
  $swWait = [Diagnostics.Stopwatch]::StartNew()
  while ($swWait.Elapsed.TotalSeconds -lt 60) {
    Start-Sleep -Seconds 2
    try {
      if (-not $script:HasEngineMutex) {
        $script:HasEngineMutex = $script:EngineMutex.WaitOne(1000, $false)
      }
    } catch { $script:HasEngineMutex = $true }
    $holders = @(Find-EngineHolders)
    if ($holders.Count -eq 0 -and $script:HasEngineMutex) { break }
  }

  if (-not $script:HasEngineMutex -or $holders.Count -gt 0) {
    # 기본값은 「안 끝낸다」다 — 일하는 중인 것을 끝내면 빗장이 막으려던 반쪽 상태를 우리가 만든다. 무엇을 끝내는지 대고
    #   사람이 예라고 할 때만 끝낸다. 쥔 쪽을 못 찾았으면 끝낼 것을 못 대므로 묻지 않는다.
    $holders = @(Find-EngineHolders)
    if ($holders) {
      $msg = "이미 돌고 있는 설치가 있습니다.`n`n" +
             (($holders | ForEach-Object { Format-EngineHolder $_ }) -join "`n") + "`n`n" +
             "그것을 끝내고 새로 시작할까요?`n`n" +
             "아직 일하는 중이면 반쯤 깔린 상태가 남을 수 있습니다."
      if (Show-AskDialog '설치가 겹쳤습니다' $msg) {
        foreach ($h in $holders) {
          try {
            Stop-Process -Id $h.ProcessId -Force -ErrorAction Stop
            Write-Host ('  PID {0} 을 끝냈다' -f $h.ProcessId)
          } catch {
            Write-Host ('  ! PID {0} 을 못 끝냈다 — {1}' -f $h.ProcessId, $_.Exception.Message) `
              -ForegroundColor Yellow
          }
        }
        # 주인이 죽으면 윈도우가 빗장을 놓는다 — 그 버려진 빗장을 여기서 받는다(위 「버려진 빗장」과 같다).
        try { $script:HasEngineMutex = $script:EngineMutex.WaitOne(10000, $false) }
        catch { $script:HasEngineMutex = $true }
      }
    }
  }

  $holders = @(Find-EngineHolders)
  if (-not $script:HasEngineMutex -or $holders.Count -gt 0) {
    Write-Host '  ! 다른 설치 프로세스가 끝나지 않아 물러납니다.' -ForegroundColor Red
    exit 1
  }
}

# ── 남은 임시 값 파일을 치운다 — 빗장을 쥔 첫 자리 (PAISetup #49 ⑩) ─────────────────────────────
# 설치 창이 몸통에 값을 건네는 `%TEMP%\claude-setup-<창 PID>.env` 에는 평문 키가 든다. 창과 몸통(「마무리」)이 다 지우지만 둘 다 멎은
#   판(전원 · 강제 종료)에는 남고, 다음 창은 PID 가 달라 그 이름을 다시 안 써 아무도 안 지운다. 여기서 이름의 PID 가 살아 있지 않은
#   것을 지운다 — 산 창의 파일은 그 창이 아직 쓰는 중이다(이 회차가 받은 파일도 그렇고, 「마무리」가 지운다). PID 를 남이 물려받았으면
#   한 회차 더 남을 뿐이다. 못 훑으면 조용히 넘긴다 — 설치를 막을 일이 아니다.
# ⚠ **이 회차가 받은 값 파일(`-EnvFile`)은 안 지운다** — 그 창이 이미 죽었어도(PID 가 안 산다) 몸통은 이 뒤 걸음에서 그 파일을 읽는다.
try {
  $liveIds = @{}
  foreach ($lp in @(Get-Process -ErrorAction SilentlyContinue)) { $liveIds["$($lp.Id)"] = $true }
  $ownEnv = ''
  try { if ($EnvFile) { $ownEnv = [IO.Path]::GetFullPath($EnvFile) } } catch { $ownEnv = '' }
  Get-ChildItem -LiteralPath ([IO.Path]::GetTempPath()) -Filter 'claude-setup-*.env' -File -ErrorAction Stop |
    Where-Object { $_.Name -match '^claude-setup-(\d+)\.env$' -and -not $liveIds.ContainsKey($Matches[1]) -and
                   -not [string]::Equals($_.FullName, $ownEnv, [StringComparison]::OrdinalIgnoreCase) } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue }
} catch { }

# ── 지난번에 고른 것 — 이번 회차의 사람 값을 정한다 (PAISetup #45) ──────────────────────────────
# 준 깃발과 넘겨받은 값 파일의 줄이 먼저고, 안 준 것은 기록(`Read-ChoiceRecord`)이 채운다 — `-Pick` 을 준 판도 그렇다. 콘솔에서
#   `-Pick claude` 만 친 사람이 껐던 VS Code · 개발 도구 · 제작자 칸 · 저장소를 잃지 않는다. 기록에도 없으면 기본값이다.
# 고른 것을 다 넘긴 판은 `-ChoicesFull` 로 그렇다고 말한다(설치 창) — 준 그대로가 이번 선택이다: 안 준 스위치는 켬 · 안 준
#   `-PersonalFor` 는 없음 · 넘겨받은 값 파일에 `#config-repo` 줄이나 주소 줄이 없으면 없음. 창에서 켠 VS Code · 끈 제작자 칸 · 비운
#   저장소가 기록으로 되살아나지 않게 하는 길은 이것뿐이다 — 스위치는 「켬」을 글로 못 넘긴다.
# 옛 자동 실행(옛 선택 파일의 줄을 인자로 넘긴다)은 이 깃발을 모르지만, 그 판이 채우러 읽는 기록이 같은 옛 선택 파일 · 얼린 사본이라
#   결과가 다 넘긴 판과 같다(`Read-ChoiceRecord` 의 옛 꼴).
# `-DevTools` 는 기록의 개발 도구 끔을 되돌린다 — 설치 창에는 그 칸이 없어 한 번 끈 PC 가 다시 켤 길이 이것이다.
# 사람이 친 게이트웨이 주소는 짐이 주소를 안 들 때만 사람의 값이다 — 짐이 주소를 들면 창은 칸을 안 열고, 그 주소는 짐의 사실이다.
# 기록은 다 넘긴 판에서도 읽어 둔다 — 「회차를 넘기는 기록」 칸이 이번 회차가 못 정한 제품(오타뿐인 `-Pick`)을 그 값으로 잇는다.
$ChoicesGiven = [bool]$ChoicesFull
$Recorded     = Read-ChoiceRecord $ChoiceRecord $LegacyChoiceArgs $LegacyChoiceEnv
$PickSet      = $PSBoundParameters.ContainsKey('Pick')
if (-not $ChoicesGiven) {
  if (-not $PickSet -and $Recorded['pick']) { $Pick = $Recorded['pick']; $PickSet = $true }
  if ($Recorded['vscode'] -eq 'no')   { $NoVsCode = $true }
  if ($Recorded['devtools'] -eq 'no') { $NoDevTools = $true }
  if (-not $PersonalFor -and -not $WithPersonalConfig -and $Recorded['personal']) { $PersonalFor = $Recorded['personal'] }
}
if ($DevTools) { $NoDevTools = $false }
# 사람이 고른 VS Code 끔 — 「회차를 넘기는 기록」 칸이 이 값을 적는다. 깔 때의 `$NoVsCode` 는 「자리」 칸이 사내에서 내린다(사내는 필수).
$NoVsCodeChosen = [bool]$NoVsCode
$repoChoice = Read-Directive $EnvFile 'config-repo'
if ($null -eq $repoChoice -and -not $ChoicesGiven) { $repoChoice = $Recorded['config-repo'] }
$TypedGatewayUrl = ''
if (-not (Read-EnvFile $DistEnvFile)['ANTHROPIC_BASE_URL']) {
  $TypedGatewayUrl = [string](Read-EnvFile $EnvFile)['ANTHROPIC_BASE_URL']
  if (-not $TypedGatewayUrl -and -not $ChoicesGiven -and $Recorded['gateway-url'] -ne $ChoiceNone) {
    $TypedGatewayUrl = [string]$Recorded['gateway-url']
  }
}

# 고른 제품. **안 주면 지난번 기록, 그것도 없으면 표의 기본값** — 화면 갈래와 콘솔 갈래가 같은 자를 쓴다. `$ChoiceNone` 은
#   「하나도 안 고름」이다.
# 모르는 이름은 삼키지 않고 경고한다 — 오타 하나로 제품이 조용히 안 깔리면 초록으로 끝나 값을 준 사람이 제일 늦게 안다.
$PickUnreadable = $false
if ($PickSet) {
  # ⚠ **쉼표만 구분자로 두지 않는다 — 공백도 받는다.** 파워셸에서 `-Pick a,b,c` 를 따옴표 없이 넘기면 껍데기가 배열로 읽고
  #   `[string]` 이 공백으로 이어 붙여, 몸통에는 `a b c` 한 덩이가 온다. 제품 이름에는 공백이 없어 넓혀도 잃는 것이 없다.
  $PickKeys = @($Pick -split '[,\s]+' | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
  # ⚠ **이름을 `$known` 으로 두지 않는다 — 아래 「값 파일이 든 나머지 이름」 칸이 그 이름을 `$Vars` 뜻으로 쓴다.** 지금은 그쪽이
  #   먼저 덮어써서 맞게 돌지만, 그 대입 앞에 `$known` 을 읽는 줄이 붙으면 조용히 뜻이 바뀐다 — 파워셸은 대소문자도 스코프도
  #   안 가려 준다.
  $ProductKeys = @($Products | ForEach-Object { $_.Key })
  # 걷은 제품 이름(`$RetiredProducts`)은 오타가 아니라 이전 배포본이 고른 값이라 말없이 빠진다 — 그 이름만 든 값은 빈 값과 같다.
  $unknown     = @($PickKeys | Where-Object { $ProductKeys -notcontains $_ -and $RetiredProducts -notcontains $_ -and $_ -ne $ChoiceNone })
  foreach ($k in $unknown) {
    Write-Host ('  ! 모르는 제품 이름 — {0} (아는 것: {1})' -f $k, ($ProductKeys -join ', ')) -ForegroundColor Yellow
  }
  # 모르는 이름은 들고 가지 않는다 — 아래 걸음마다 아무것도 안 맞는 열쇠가 섞여 다닐 까닭이 없다.
  $PickKeys = @($PickKeys | Where-Object { $ProductKeys -contains $_ })
  # 아는 이름이 하나도 안 남으면 그것은 오타지 「아무것도 안 깔겠다」가 아니다 — 위 경고 줄은 걸음 로그에 묻혀, 제품을 하나도
  #   안 깐 채 초록으로 끝난다. 막지는 않고(프로그램 · 키 · 씨앗은 설 자리가 있다) `$Fails` 에 적어 맨 끝 검증을 빨갛게 한다.
  if ($unknown -and -not $PickKeys) {
    Write-Host ('  ! 고른 제품이 하나도 안 섰다 — 준 값을 쉼표로 가른다: -Pick "{0}" (하나도 안 깔려면 -Pick {1})' -f
                ($ProductKeys -join ','), $ChoiceNone) -ForegroundColor Red
    $Fails.Add(('-Pick 에 아는 제품 이름이 없다 (준 값: {0})' -f $Pick))
    $PickUnreadable = $true
  }
} else {
  $PickKeys = @($Products | Where-Object { $_.Default } | ForEach-Object { $_.Key })
}
# 제품을 하나도 안 고른 판에도 `$PickKeys` 는 빈 배열로 선다 — 아래 걸음들은 `$null` 이 아닌 빈 목록을 돈다.
if (-not $PickKeys) { $PickKeys = @() }

$Vars = @(
  @{ Name='ANTHROPIC_BASE_URL';   Desc='게이트웨이 주소 — 사내는 로컬 프록시 루프백 · 끝에 /v1 을 붙이지 않는다 (CLI 가 붙인다)'; Gateway=$true }
  @{ Name='ANTHROPIC_AUTH_TOKEN'; Desc='게이트웨이 API 키';                                          Gateway=$true; Secret=$true }
  @{ Name='ANTHROPIC_MODEL';      Desc='기본 모델 이름 (비우면 CLI 기본값으로 둔다)';                Gateway=$false }
)

# ── 클라이언트 기능 스위치 — **씨앗이 아니라 늘 맞춘다 · 진본은 홈 설정 씨앗의 `env` 다** (PAISetup #47 ⑦) ────────────────────────
# 씨앗은 settings.json 이 없을 때만 깔려, 한 번 돌린 기계는 그 뒤에 늘어난 스위치를 씨앗으로는 못 받는다 — 그래서 「Claude 홈 설정」이
#   판마다 맞추고, 씨앗에서 뺀 스위치는 장부로 걷는다. 게이트웨이 값(`#settings-env` 가 묻는다)과 달리 켜거나 안 켜거나뿐이라 늘 맞춰도
#   사람에게서 뺏는 것이 없다.
# 진본은 짐에 실린 홈 설정 씨앗(`$HomeSeed` — claude-config 의 `vdi-home-settings.json` 을 뽑은 것)이다. 사외 VDI 의 세션 훅이 홈을 덮는
#   바탕도 그 씨앗이라, 여기 또 적으면 두 저장소가 같은 사실을 따로 들어 한쪽만 는다. 스위치가 늘면 그 씨앗의 `env` 에 한 줄을 더한다.
#   「Claude 홈 설정」이 settings.json 이 없을 때 짓는 바탕도 이 씨앗이다(그 걸음 머리).
# 씨앗을 못 읽으면 `$Features` 는 `$null` 이다 — 그 판은 스위치를 안 건드리고 노란 줄을 낸다(빈 표로 읽으면 장부가 우리 스위치를 다 걷는다).
$HomeSeed = Read-HomeSeed (Join-Path $Here 'seeds\config-repo\vdi-home-settings.json')
$Features = Get-SeedSwitches $HomeSeed

# ── 고를 모델 목록 — **자리를 탄다. 게이트웨이에 닿는 자리에만 선다** (결정 0047 · 0048) ────
# `/model` 목록에 설 줄을 우리가 선언한다. 접미사 `[1m]` 이 창을 1M 으로 연다 — 게이트웨이는 그만큼을 주고 CLI 가 깎는다.
# ⚠ **씨앗(`vdi-home-settings.json`)에 두지 않는다.** 이 이름들은 게이트웨이가 등록한 것이라 자리를 타는데 씨앗은 익명 층이고
#   포크를 따라간다. 사외는 구독으로 돌아 이 이름이 없어서, 씨앗에 두면 사외 VDI 목록에 못 부르는 줄이 서고 고르면 깨진다 —
#   그 자리는 씨앗 덮기가 이 설치보다 나중이라(위 「클라이언트 기능 스위치」) 여기서 안 쓴 것도 씨앗이 되살린다.
# 목록의 진본은 게이트웨이의 `GET /v1/models` 다 — 거기 없는 Sonnet 5 · Haiku 는 내장 줄로 보여도 고르면 400 이라
#   `$ModelPickerOnly` 로 내장 줄을 숨긴다. 줄이 늘면 여기 한 줄을 더하되, 게이트웨이가 그 이름을 내는지 먼저 묻는다.
# ⚠ **이름은 하이픈으로 적는다.** 게이트웨이는 점 표기(`claude-opus-4.7`)로 목록을 내지만 두 표기를 다 받는다. 하이픈이 CLI
#   카탈로그가 아는 이름이라 표시명 · 접미사 판정이 걸리고, 점 표기는 「모르는 모델」로 떨어져 `[1m]` 이 조용히 안 붙는다.
$ModelPicker = @(
  @{ model = 'claude-sonnet-4-6[1m]'; description = 'Sonnet 4.6 · 게이트웨이 · 1M 창' }
  @{ model = 'claude-opus-4-7[1m]';   description = 'Opus 4.7 · 게이트웨이 · 1M 창' }
  @{ model = 'claude-opus-5[1m]';     description = 'Opus 5 · 게이트웨이 · 1M 창' }
)
# 내장 줄(Sonnet 5 · Haiku · Custom 칸)을 숨긴다 — 이 게이트웨이가 안 내는 것들이다.
# `Default` 행은 이 값과 무관하게 남는다.
$ModelPickerOnly = $true

# 「도는 중」 한 줄(`Say-Busy`)이 고르는 동작 낱말 표 — 줄의 꼴 `  <대상> — <동작>중 … (<수단> · <덧말>)` 은 그 함수 하나가 든다.
# 설치 창은 몸통이 찍은 마지막 한 줄을 「지금 하는 일」로 띄운다(`install.ui.ps1` 의 `Step-Line`) — 안 찍는 자리는 직전 결과
#   줄이 걸린 채 오래 돌아 멎은 것과 구분이 안 된다. 그래서 시간이 드는 걸음은 들어가기 전에 `Say-Busy` 를 부르고, 동작 낱말은
#   이 표에서만 고른다. 결과 줄(`— 깔았다 · 있음 · 최신 · 올렸다`)은 자리마다 까닭이 달라 제 자리가 찍는다.
$BusyVerbs = [ordered]@{
  install = '설치중'
  upgrade = '갱신중'
  upcheck = '갱신 확인중'
  fetch   = '받는중'
  wait    = '기다리는 중'
}

# 사내에서만 뜻이 있는 이름 — **값이 주소가 아니라 프록시 걷기(`Test-OurProxyEntry`)가 못 가른다.** 저쪽은 「값이 죽은 포트를
#   가리키나」를, 이쪽은 「이 이름이 사외에서 뜻이 있나」를 묻는다 — 값으로만 재면 `ATELIER_SITES=posco` 같은 사내 전용 값이 사외로
#   새어 아뜰리에의 갈래가 다 막힌다. 값은 안 보고, 이름 울타리(`Test-OurInsideOnlyEntry` · 값 파일이 그 이름을 드는가)로 우리가
#   실어 보낸 이름만 건드린다. 이름이 늘면 여기 한 줄.
# 끄기 셋도 사내 전용이다 — 회사망이 막는 곳으로 안 가려고 끄는 것이라 사외에서는 끌 까닭이 없고, 끄면 잃는다:
#   `DISABLE_TELEMETRY` 는 원격 제어가 기대는 기능 플래그 평가까지 꺼 켤 때마다 「Remote Control initialization failed」로 진다
#   (공식 문서 remote-control 요구 조건). 값 파일이 늘 이 이름을 들어 울타리를 넘으므로, 사용자가 손수 넣은 값도 사외에서는 걷힌다.
# 모델 고정 둘도 사내 전용이다 — 게이트웨이가 설정 `model` 키의 `[1m]` 을 벗겨 1M 창을 환경변수로 여는 우회라(claude-config 결정
#   0049), 구독 로그인으로 서는 사외에서는 열 것이 없다. 남으면 시작 모델이 그 값에 묶여 `/model` 로 고른 것이 새 창마다 밀린다.
#   `ANTHROPIC_MODEL` 은 위 `$Vars` 표에도 있어 표 루프도 이 목록을 묻는다.
$InsideOnly = @('ATELIER_SITES', 'DISABLE_TELEMETRY', 'DISABLE_ERROR_REPORTING', 'CLAUDE_CODE_DISABLE_FAST_MODE',
                'ANTHROPIC_MODEL', 'ANTHROPIC_DEFAULT_OPUS_MODEL')

Write-Host ''
Write-Host '=== Claude Code 환경 설치 ===' -ForegroundColor Cyan
Write-Host ''

# ── 자리 — **무엇이든 깔기 전이다** — 무엇을 깔지가 자리에 달렸고(데스크탑 앱), 못 정한 판은 아무것도 안 깔아야 한다 ──
#    아래 걸음들의 갈래가 다 이 한 값에서 난다 — 게이트웨이를 쓰나(`$useGateway`) · 주소 심기 · 프록시와 감시 작업 · Codex · agy 회사
#    설정 · 구독 로그인 · WebFetch · 모델 목록 · 사외 잔재 걷기 · 「사내는 VS Code 필수」. 한 번 재고 다 나눠 쓴다. winget 되살리기보다
#    앞에 서는 까닭은 못 정한 판이 그것도 안 깔게 하려는 것이다.
# ⚠ **자리는 둘이다 — 사내 · 사외.** 재는 자는 `Measure-Site`(짐의 `#site-probe` 에 닿나) 하나고, 프로브가 없거나 꼴이 틀리면 어느
#   갈래로도 안 가고 빨강으로 멈춘다 — 안 재고 한 갈래를 고르면 같은 PC 가 회차마다 다른 자리로 돌아, 사내 PC 의 회사 연결을 걷거나
#   사외 PC 에 닿지 않는 주소를 심은 채 초록으로 끝난다(PAISetup #46).
# ⚠ **넘겨받은 자리(`#site`)가 있어도 회차마다 다시 잰다 — 다르면 아무것도 안 심고 멈춘다.** 넘기는 자는 설치 창(`-Describe` 로 연
#   때 잰 자리)과 밤 자동 실행(잰 자리를 박는다)이다. 창을 연 뒤 망이 바뀌면(무선 전환 · 회사망 재인증 · 집에 가져간 노트북) 창이
#   보여 준 칸과 지금 자리가 갈려, 그대로 가면 창이 받은 키를 버리거나(사내→사외) 사외 칸이 안 받은 주소 없이 게이트웨이를 쓴다
#   (사외→사내). 밤 회차는 자리를 안 바꾸므로 그 회차도 멈춘다. 프로브의 있음 · 꼴도 넘겨받은 판에서 같이 잰다(`Measure-Site`).
# 프로브는 짐의 사실이라 짐에서, `#site` 는 이 회차가 받은 것이라 넘겨받은 값 파일에서 읽는다.
$probe      = Read-Directive $DistEnvFile 'site-probe'
$sitePassed = Read-Directive $EnvFile 'site'
$siteFact   = Measure-Site $probe
if (-not $siteFact.Site) {
  Write-Host "  ! 자리를 못 정했다 — $($siteFact.Why)" -ForegroundColor Red
  Write-Host '    아무것도 안 깔고 멈춘다 — 사내인지 사외인지 모르고 깔면 회사 연결을 걷거나 닿지 않는 주소를 심는다'
  Write-Host '    설치 묶음(Setup.exe)을 새로 받아 다시 누른다 · 값 파일을 손으로 만들었으면 #site-probe = 호스트:포트 줄을 넣는다'
  exit 1
}
$site    = $siteFact.Site
$offsite = ($site -eq 'outside')
$siteSaid = @{ inside = '사내'; outside = '사외' }
if ($sitePassed -and $sitePassed -cne $site) {
  $passedSaid = if ($siteSaid.ContainsKey($sitePassed)) { $siteSaid[$sitePassed] } else { $sitePassed }
  if ($NightRun) {
    Write-Host "  ! 밤 회차가 잰 뒤 자리가 바뀌었다 — 밤 회차는 $passedSaid · 지금은 $($siteSaid[$site]) ($probe)" -ForegroundColor Red
    Write-Host '    밤 회차는 자리를 안 바꾼다 — 아무것도 안 깔고 멈춘다 (다음 로그온 회차 · 설치 창이 잇는다)'
  } else {
    Write-Host "  ! 창을 연 뒤 자리가 바뀌었다 — 창을 다시 연다 (창은 $passedSaid · 지금은 $($siteSaid[$site]) · $probe)" -ForegroundColor Red
    Write-Host '    아무것도 안 깔고 멈춘다 — 창이 보여 준 칸(주소 · 키)과 지금 자리가 다르면 받은 키를 버리거나 닿지 않는 주소를 심는다'
  }
  exit 1
}
$siteBy = if ($offsite) { '안 닿음' } else { '닿음' }
if ($sitePassed) { $siteBy += ' · 넘겨받은 자리와 같다' }
Write-Host ("  자리 = {0}  ({1} {2})" -f $siteSaid[$site], $probe, $siteBy)
# 사내는 VS Code 가 필수다(`Test-VsCodeRequired`) — 칸을 꺼도 깐다. 기록은 사람이 고른 값(`$NoVsCodeChosen`) 그대로 둔다 — 사외로
#   나가면 그 값이 다시 선다.
if ($NoVsCode -and (Test-VsCodeRequired $site)) {
  $NoVsCode = $false
  Write-Host '  VS Code — 사내는 필수라 칸을 껐어도 깐다 (고른 「끔」은 기록에 그대로 둔다)'
}
Write-Host ''

# ── 파이썬 판 — **진본은 설정 저장소의 전역 도구 선언이고, 뽑는 자가 값 파일의 `#python-version` 으로 싣는다** ──
# 그 값으로 `$Apps` 의 Python 줄 Id(`Python.Python.<판>`)를 짓는다 — winget 에는 판 없는 CPython id 가 없다. 배선
#   (`Update-RuntimePath`)의 파이썬 폴더 이름도 이 Id 에서 판다.
# ⚠ **못 정하면 Python 줄을 빼고 실패로 적는다** — 판을 박은 기본값을 두면 그것이 선언의 손사본이라 판을 올리는 날 조용히 갈린다.
$PyVersion = Read-Directive $DistEnvFile 'python-version'
if ($PyVersion -match '^\d+\.\d+$') {
  ($Apps | Where-Object { $_.Cmd -eq 'python' }).Id = "Python.Python.$PyVersion"
} else {
  $Apps = @($Apps | Where-Object { $_.Cmd -ne 'python' })
  Write-Host "  ! Python — 값 파일의 #python-version 이 없거나 꼴(예: 3.14)이 아니라 판을 못 정했다 — 깔지도 올리지도 않는다" -ForegroundColor Yellow
  $Fails.Add('Python (값 파일에 #python-version 이 없어 판을 못 정했다)')
}

# ── winget ────────────────────────────────────────────────────────────────────
# 없다고 여기서 죽지 않는다 — winget 이 없으면 못 까는 것이지, 확장 · CLI · 키 심기 · 홈 설정은 winget 없이 다 선다. 사내 PC 에는
#   런타임이 이미 깔린 일이 흔하다. 조용히 넘기지도 않는다 — 못 깐 것은 아래에서 이름을 대고 실패로 적힌다.

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

# ── 앱 ────────────────────────────────────────────────────────────────────────
# ⚠ `--source winget` 을 박는다 — 사내에서 빼면 인증서 검증에 걸린다.
# 판정은 종료코드가 아니라 프로브다 — winget 은 이미 깔려 있으면 「올릴 것이 없다」로 0 이 아닌 값을 낸다.
# 소스를 뗀 옵션(`$WGOpts`)을 따로 둔다 — 데스크탑 앱 하나가 스토어 소스에 살아서(위 표의 `Source`) 소스를 붙박이로 두면 그 앱을
#   못 부른다. 나머지는 `$WG` 를 쓴다 — 붙이는 자리를 한 줄로 두어 둘이 안 갈린다.
$WGOpts = @('--exact','--silent',
            '--accept-package-agreements','--accept-source-agreements','--disable-interactivity')
$WG = @('--source','winget') + $WGOpts
# winget 이 「입력 조건과 일치하는 설치된 패키지를 찾을 수 없다」로 끝난 값(`APPINSTALLER_CLI_ERROR_NO_APPLICATIONS_FOUND`). `winget list`
#   의 0 아닌 값 가운데 이것만 「없다」다 —소스를 못 열었거나(인증서 `0x8A15005E`) 그 밖으로 진 값은 「못 쟀다」다(결정 0145).
$WingetNotInstalled = 0x8A150014

# ── 자동 실행을 켜나 · 자동 실행이 읽는 「지난 설치의 자리」 (PAISetup #36) ─────────────────────────────────
# 켜나(`$wantAutoRun`)는 `-AutoRun` · `-NoAutoRun` 이 먼저고, 없으면 짐의 `#autorun = yes|no` 를 `Get-AutoRunDefault` 가 푼다. 「부팅 시
#   자동 실행」 칸이 이 값을 쓴다.
# 끈 기록(`$AutoRunOffRecord`)은 「부팅 시 자동 실행」 칸이 `-NoAutoRun`(설치 창의 꺼진 칸)으로 걷을 때 적고, 다시 걸 때 지운다. 깃발
#   없는 판(로그온 · 밤 자동 실행 · 손으로 친 `-Yes -NoLaunch` · 화면이 못 선 콘솔)은 설치 창이 칸을 그대로 두고 누른 판과 같게 간다 —
#   설치 창의 칸이 같은 손의 답(`-Describe` 의 `autorun|` 줄)으로 서기 때문이다. `yes` 인데 끈 기록이 있고 작업이 없는 PC 는 「꺼 두었다」
#   한 줄만 남기고 그대로 둔다(`$autoKeptOff`).
# 밤 자동 실행은 자리 기록이 지금 잰 자리와 같은 `inside` · `outside` 일 때만 돈다(자동 실행 몸통의 「하루 한 번 · 자리」 칸). 이
#   설치가 자리를 바꾸는 판이면 자리에 기대는 걸음(프로그램 · 키와 값 · 사내 연결 · Claude 홈 설정 · 도구별 홈)보다 먼저 `switching`
#   을 적는다 — 반쯤 돌다 지면 그 값이 남아 밤 회차는 건너뛴다. 기록과 같은 자리면 안 적는다(자리를 박은 밤 회차가 그렇다) — 바꾸지
#   않는 설치가 지며 `switching` 을 남기면 다시 부팅하지 않는 PC 는 밤 회차가 영영 선다. 끝 값은 그 걸음들을 다 지난 「부팅 시 자동
#   실행」 칸이 적는다. 자동 실행을 켜는 설치만 적고, 설치본 폴더가 없는 자리(저장소에서 바로 돌린 콘솔)는 안 적는다. 못 적으면
#   지운다 — 앞선 값이 남으면 밤 회차가 자리를 바꾼 설치를 못 알아본다.
# 작업 이름 둘(`$AutoRunTaskName` · `$AutoRunNightTaskName`)은 파일 머리의 「회차를 넘기는 기록의 자리」 칸이 든다.
$autoDirective = Read-Directive $DistEnvFile 'autorun'
$wantAutoRun   = $null
$autoKeptOff   = $false
if ($AutoRun) { $wantAutoRun = $true }
elseif ($NoAutoRun) { $wantAutoRun = $false }
else {
  $wantAutoRun = Get-AutoRunDefault $autoDirective
  $autoKeptOff = [bool]($autoDirective -eq 'yes' -and $null -eq $wantAutoRun)
}

$AutoRunSiteFile   = '.autorun-site'
$AutoRunSiteRecord = Join-Path (Join-Path $env:LOCALAPPDATA 'Claude Code Setup') $AutoRunSiteFile
$siteRecorded = ''
if (Test-Path -LiteralPath $AutoRunSiteRecord) {
  try { $siteRecorded = (Get-Content -LiteralPath $AutoRunSiteRecord -Raw -Encoding UTF8 -ErrorAction Stop).Trim() } catch { $siteRecorded = '' }
}
if ($wantAutoRun -eq $true -and $siteRecorded -ne $site -and (Test-Path -LiteralPath (Split-Path -Parent $AutoRunSiteRecord))) {
  try {
    Set-Content -LiteralPath $AutoRunSiteRecord -Value 'switching' -Encoding UTF8 -ErrorAction Stop
  } catch {
    Remove-Item -LiteralPath $AutoRunSiteRecord -Force -ErrorAction SilentlyContinue
    Write-Host "  ! 자동 실행이 읽을 자리 기록을 못 적었다 — $(Say-Why $_) (밤 자동 실행은 다음 설치까지 건너뛴다)" -ForegroundColor Yellow
  }
}

# ── 사내에서만 더 서는 것 — 로컬 프록시 · Codex 회사 설정 · 안티그래비티 회사 설정 (결정 0041 · 0045 · 0136) ──
# 몸통은 파일 이름도 모델 이름도 모른다 — 짐의 값 파일이 `#gateway-proxy = <프록시 파일>` · `#codex-config = <틀>` 로 이 폴더 안의
#   자리를 가리키고, 몸통은 있고 사내면 그것을 세운다. 안티그래비티는 틀이 없다(아래 `$wantAgy`). 사외는 다 안 선다 — 구독 · 개인 로그인으로 서는
#   자리다.
# 프로그램은 이 스위치 밖이다 — Codex · 안티그래비티 확장과 CLI 는 위 표대로 어디서나 깔린다. 여기가 가르는 것은 그 프로그램을
#   회사 키로 게이트웨이에 물리나뿐이다(결정 0045).
# ⚠ **`#config-repo` 가 있어도 여기서 세운다.** 그 저장소의 부트스트랩은 설정 파일만 쓰고 프로그램은 안 깔아, 이 스위치를 그 줄에
#   걸면 확장 · CLI 를 아무도 안 깐다. 그 줄은 「다 세운 뒤 저장소를 더 받는다」는 뜻일 뿐이다.
$proxyRel   = Read-Directive $DistEnvFile 'gateway-proxy'
# 프록시 파일 이름 — 실행 폴더의 파일 · 끄기 · 끝 검증의 「단일 프로세스」가 다 이 값으로 그 프로세스를 가린다(값 파일의 줄이 진본이다).
$ProxyFile  = if ($proxyRel) { Split-Path $proxyRel -Leaf } else { '' }
$codexTpl   = Read-Directive $DistEnvFile 'codex-config'
$inside     = ($site -eq 'inside')
# 맡기기 모델 표에서 읽는 자리 줄 — 「키와 값」이 그 줄로 러너의 자리 값을 심고, 「도구별 홈」이 `PAISETUP_SITE` 로 남겨 맡기는
#   세션이 같은 줄을 읽는다(claude-config 결정 0086).
$ModelSite  = if ($inside) { 'inside' } else { 'outside' }
$wantProxy  = [bool]($proxyRel  -and $inside)
# 회사 설정도 제품 칸을 탄다 — 안 켠 제품에 회사 설정만 심으면 쓰지도 않는 파일이 남아 「깔렸나 보다」로 읽힌다.
$wantCodex  = [bool]($codexTpl  -and $inside -and ($PickKeys -contains 'codex'))
# ── agy 묶음 — agy 모델 값 (claude-config 결정 0083 · 0086 · 0088 · 0123 · claude-config #117) ──────
# Claude Code 가 agy 에게 일을 맡기는 길은 백그라운드 래퍼(스킬 `agy-background`) 하나다 — 그 래퍼가 고를 모델이
#   `$AgyModelVars` 다. 자리는 안 가리고 모델 값만 갈린다 — 사내 agy 는 회사 키로 게이트웨이를 타서 서는 모델 이름이 다르다
#   (「키와 값」이 맡기기 모델 표의 자리 줄에서 `$AgyModelVars` 를 짓는다).
# 다리(MCP `agy-bridge`)는 안 깐다(결정 0088) — 다리는 끝날 때까지 대화를 붙잡아, 맡겨 두고 딴 일을 하라는 이 묶음의 뜻과 어긋난다.
# 조건이 갈린다(결정 0089 · 0091).
#   * 맡기기(`$wantAgyDelegate`) — 모델 값 · 래퍼 스킬 · 래퍼가 도는 파이썬. 「자리 × Claude 또는 Codex 와 안티그래비티를
#     골랐나」의 사실이라 그 둘만 탄다. 래퍼는 누구의 규범과도 무관하게 agy 를 띄우고 넘기는 도구다.
#   * 일하는 도구 스킬 · 훅(`$hostAgy`)은 칸 없이 안티그래비티를 고르면 선다(결정 0099) — 아래 「칸 없이 까는 스킬」 ·
#     「agy 훅」 칸.
#   * agy 가 규범 · 룰을 읽게 하는 설정 둘은 이 설치기가 짓지 않는다 — 손(`tool-homes.py`)이 제작자 칸의 agy 칸을 보고
#     놓는다(「도구별 홈」 · claude-config 결정 0112).
$hostAgy         = [bool]($PickKeys -contains 'antigravity')
# ── 설정 저장소의 주소와 자리 — 씨앗 칸(비켜선다) · 제작자 칸(끝의 안내) · 「설정 저장소」 걸음(받는다)이 같이 쓴다 ──
# ⚠ **자리를 짓는 자를 한 벌로 둔다**(`Get-ConfigRepoDir`). 씨앗 칸이 저장소를 찾는 자리와 「설정 저장소」 걸음이 clone 하는 자리가
#   갈리면, 씨앗 칸이 없는 폴더를 보고 비켜서지 않아 저장소와 겹쳐 깐다.
# 여러 개를 빈칸으로 가른다 — 까닭은 「설정 저장소」 걸음 곁말이 든다. 주소에는 빈칸이 없다. 이번 회차의 주소는 「지난번에 고른 것」
#   칸이 정했다(`$repoChoice` — 안 골랐으면 `$ChoiceNone`).
$repoUrl = if ($repoChoice -and $repoChoice -ne $ChoiceNone) { $repoChoice } else { $null }
$configRepoUrls = @($repoUrl -split '\s+' | Where-Object { $_ })

# ── 제작자 세트를 받을 도구 — 도구마다 고른다 (결정 0099) ───────────────────────────────────────
# `-PersonalFor claude,codex,agy` 가 고른다. `-WithPersonalConfig` 만 주면 Claude 다 — 이전 판의 단일 칸이라, 그 칸으로 자동 실행이
#   오면 Claude 로 깔고 끝에 설치 창을 한 번 띄운다. 고른 제품이 아닌 도구는 빠진다 — 깔 홈이 없다. 고른 것은 사용자 환경변수
#   `PAISETUP_PERSONAL` 로도 심어, 설정 저장소의 배포 · 세션 훅이 같은 값을 읽는다(「도구별 홈」 걸음). 아무것도 안 골랐으면
#   `none` — 비운 값은 「이 설치기를 안 돌렸다」와 갈라야 한다.
# 칸 하나가 스위치다 — 설정 저장소를 넣어도 그대로다(결정 0107). 규범 · 룰 · 에이전트 · 스킬은 비켜서지 않는다 — 이 설치는 짐으로
#   표준 층을 채우고, 저장소의 배포가 채운 개인 층이 항목마다(스킬은 스킬 하나마다) 이긴다(손 `tool-homes.py` · claude-config 결정
#   0112). 칸에 안 든 도구의 홈에는 손이 스킬을 안 놓고, 이 설치가 칸 없이 까는 스킬만 깐다(아래 `$FreeSkills`). 끈 도구는 저장소가
#   있어도 우리 것을 걷는다 — 손은 제 기록에 든 것을, 칸 없이 까는 걸음은 제 기록에 든 것 가운데 이번에 안 까는 것을.
#   `$personal*` 은 고른 값이고, `$personalByRepo` 는 설정 저장소를 넣었나다(끝의 안내 한 줄이 가른다).
$personalAsked  = if ($PersonalFor) { @($PersonalFor -split '[,\s]+' | Where-Object { $_ } | ForEach-Object { $_.ToLower() }) }
                  elseif ($WithPersonalConfig) { @('claude') } else { @() }
# 칸이 사는 도구 — 고른 도구 가운데 그 도구의 홈이 서는 제품(`$PersonalTools` 의 `Product`)도 고른 것만. 도구 ↔ 제품은 그 표 하나가 든다.
$personalOn     = @($PersonalTools | Where-Object { ($personalAsked -contains $_.Tool) -and ($PickKeys -contains $_.Product) } | ForEach-Object { $_.Tool })
$personalClaude = [bool]($personalOn -contains 'claude')
$personalCodex  = [bool]($personalOn -contains 'codex')
$personalAgy    = [bool]($personalOn -contains 'agy')
$personalAny    = [bool]($personalClaude -or $personalCodex -or $personalAgy)
# ⚠ **값은 표를 지나 고른다 — `$(if …)` 를 늘어놓아 배열을 짓지 않는다.** 아무것도 안 낸 `$()` 둘이 앞자리에 서면 5.1 의 파이프가
#   뒤의 값까지 삼켜, agy 하나만 고른 판이 빈 값(→ `none`)이 된다. 아래 `$PickValue` 도 같다.
$PersonalValue  = @(([ordered]@{ claude = $personalClaude; codex = $personalCodex; agy = $personalAgy }).GetEnumerator() |
                    Where-Object { $_.Value } | ForEach-Object { $_.Key }) -join ','
if (-not $PersonalValue) { $PersonalValue = 'none' }
$personalByRepo = [bool]$configRepoUrls.Count
# ── 고른 제품 — 갈 곳 표의 도구 이름으로 (결정 0102 · claude-config #133 「훅」 걸음 · claude-config 결정 0122) ──────
# 손(`tool-homes.py`)의 조건 `pick` 이 읽는 값이라 표의 도구 이름(claude · codex · agy)으로 짓고, 표에 길은 없지만 세션 훅이
#   폴더 신뢰를 거는 Copilot(`copilot`)도 싣는다 — 손은 그 이름을 아는 제품으로 넘긴다. 사용자 환경변수
#   `PAISETUP_PICK` 으로 심어(「도구별 홈」) 설정 저장소의 배포 · 세션 훅이 부르는 손도 같은 값을 읽는다 — 고른 제품에만 우리
#   Claude 훅이 서고, 빼면 우리 것이 걷힌다. 넷 다 안 골랐으면 `none` — 빈 값은 손이 「설치기가 안 돈 자리」로 읽어 claude 로 본다.
$PickValue = @(([ordered]@{ claude = 'claude'; codex = 'codex'; antigravity = 'agy'; copilot = 'copilot' }).GetEnumerator() |
               Where-Object { $PickKeys -contains $_.Key } | ForEach-Object { $_.Value }) -join ','
if (-not $PickValue) { $PickValue = 'none' }
$wantAgentHost   = [bool](($PickKeys -contains 'claude') -or ($PickKeys -contains 'codex'))
$wantAgyDelegate = [bool]($wantAgentHost -and $hostAgy)
# ── Codex · Copilot 맡기기 — 스킬 `codex-copilot-background` · 그 래퍼가 도는 파이썬 · 자리 값 (claude-config 결정 0092 · 0093) ──
# Codex 에게 일을 뒤에서 맡기고(맡긴 쪽은 읽기 전용 샌드박스), 자리가 허락하면 Codex 한도에서 Copilot 이 받는다.
# 맡기는 쪽과 받는 쪽(Codex)이 다 있어야 선다 — 맡기는 쪽 조건은 아래 `$wantCcBg*` 가 든다. 사내는 Codex 를 회사 게이트웨이에
#   물린 자리(`$wantCodex`)에서만 받는다 — 사내 Codex 는 ChatGPT 로그인이 아니라 회사 설정 틀로 게이트웨이를 타서, 틀이 안 심긴
#   사내 PC 에서는 붙을 데가 없다(결정 0086). Copilot 은 조건에 안 든다 — 받는 쪽일 뿐이라, 래퍼는 Copilot
#   CLI 가 없으면 Codex 만으로 돈다.
# 자리마다 다른 값은 래퍼가 읽는 사용자 환경변수로 심는다 — 래퍼는 자리를 모르고 이 값만 읽는다(agy 의 `$AgyModelVarsBySite` 와
#   같은 꼴). 받는 값은 래퍼 머리말이 들고, 래퍼 검사(claude-config `scripts/check-codex-copilot-bg.py`)가 이 표를 읽어 두 자리
#   값이 래퍼에서 서는지 잰다.
#   * `CC_BG_AGENTS` — 차례이자 쓸 수 있는 쪽. 사내는 Codex 만 —Copilot 은 GitHub(회사 밖)로 가고, 사내에서 개인
#     구독은 막혀 보이며 회사 계정으로 CLI 를 쓰는 정책은 정해진 것이 없다. 이 값은 래퍼가 무엇을 띄우나만 가른다 —
#     Copilot CLI 는 이 값과 무관하게 Copilot 제품을 고르면 두 자리에 깔린다(제품 표 `$Clis`)
#   * `CC_BG_CODEX_WEB_SEARCH` — Codex 의 `web_search`. 두 자리 다 `live`(실시간 검색) —사내는 회사 설정 틀이 Codex 를
#     로컬 프록시에 물리고, 프록시가 그 검색을 게이트웨이 Responses 로 잇는다(claude-config #121). 래퍼가 이 값을 `-c` 로
#     넘겨 틀의 값보다 앞서므로, 검색을 끌 자리는 여기서 `disabled` 로 끈다(`cached` 도 검색 도구를 싣는다)
#   * `CC_BG_CODEX_WIN_SANDBOX` — Codex 의 `windows.sandbox`. 두 자리 다 `unelevated` —관리자 승인 설정이 안 드는
#     값이라 뒤에서 띄운 래퍼가 승인 창을 안 띄운다. `elevated` 는 그 설정이 없는 PC 에서 설정부터 하려 들고, 값이
#     없으면(새 PC) 읽기 전용을 지키는 OS 샌드박스가 아예 안 선다
# 사내 게이트웨이의 180초 벽은 무게로 넘는다 — 벽은 요청 하나의 실행 시계라(`posco/ENV-posco.md`) 래퍼의 시간 한도로는 못 넘는다.
#   사내 Codex 의 추론 깊이는 회사 설정 틀이 든다(`model_reasoning_effort = "low"`).
# 모델 둘(`CC_BG_CODEX_MODEL_DELEGATE` 깊은 판단, `CC_BG_CODEX_MODEL` 심부름)은 이 표에 없다 — 맡기기 모델 표가 그 자리에 이름을 줄
#   때만 「키와 값」이 이 표에 더해 심고, 표가 `-` 거나 줄이 없으면 안 심는다. 둘 다 없으면 래퍼가 모델을 안 넘겨 Codex 설정의
#   `model`(사내는 회사 설정 틀이 쓴 대화형 기본값)로 뜬다(claude-config 결정 0123).
# 심는 값은 매번 덮는다 — 두 자리가 같은 이름을 들어, 자리를 옮긴 PC 도 이 자리 값으로 바뀐다.
$CcBgVarsBySite = @{
  inside  = [ordered]@{
    CC_BG_AGENTS            = 'codex'
    CC_BG_CODEX_WEB_SEARCH  = 'live'
    CC_BG_CODEX_WIN_SANDBOX = 'unelevated'
  }
  outside = [ordered]@{
    CC_BG_AGENTS            = 'codex,copilot'
    CC_BG_CODEX_WEB_SEARCH  = 'live'
    CC_BG_CODEX_WIN_SANDBOX = 'unelevated'
  }
}
$CcBgVars       = $CcBgVarsBySite[$ModelSite]
# 맡기는 쪽은 Claude 나 agy 다 — 래퍼가 읽는 자리 값과 파이썬은 둘 가운데 하나라도 서면 선다(결정 0099). Codex 가 받는 쪽으로
#   서는 자리는 사외이거나, 사내에서 Codex 회사 설정이 서는 자리다.
$codexReceives  = [bool](($PickKeys -contains 'codex') -and ((-not $inside) -or $wantCodex))
$wantCcBgClaude = [bool](($PickKeys -contains 'claude') -and $codexReceives)
$wantCcBgAgy    = [bool]($hostAgy -and $codexReceives)
$wantCcBg       = [bool]($wantCcBgClaude -or $wantCcBgAgy)
# ── Claude 맡기기 — 스킬 `claude-background` (claude-config 결정 0098) ──────────────────────────────
# 위 Codex · Copilot 맡기기의 거울이다 — Codex 나 agy 가 맡기는 쪽이고 Claude 가 받는다. 받는 Claude 는 읽기 도구만 열고 뜬다.
# Codex 쪽 조건은 위와 같은 사실이라(두 CLI 가 다 서는 자리에서 서로에게 맡긴다) 따로 짓지 않고 가리킨다. agy 쪽은 Claude 와
#   안티그래비티를 같이 고르면 선다(결정 0099).
$wantClaudeBgCodex = $wantCcBgClaude
$wantClaudeBgAgy   = [bool](($PickKeys -contains 'claude') -and $hostAgy)
$wantClaudeBg      = [bool]($wantClaudeBgCodex -or $wantClaudeBgAgy)
# ── 도구 홈 짐 — `kit/` (claude-config 결정 0101) ────────────────────────────────────────────
# 받는 PC 의 도구 홈 여럿에 나눠 깔 것(규범 · 룰 · 스킬)과 그것을 놓는 손(`tool-homes.py` · 그 표 `tool-homes.conf`)이 한
# 폴더에 산다. 도구가 스스로 읽는 자리 이름(`.claude/skills` · `.agents/skills`)에 안 두는 것이 요점이다 — 이 폴더를
# Claude Code · Codex 로 열면 그 자리가 그 세션의 스킬로 실린다.
$Kit = Join-Path $Here 'kit'
$KitSkills = Join-Path $Kit 'skills'
# ── 칸 없이 까는 스킬 — 일하는 환경에 딸린 도구라 제작자의 사유 방식과 갈린다 (결정 0091 · 0097) ──────
# 키는 스킬 이름, 값은 홈마다 까는 조건이다 — 도구마다 제 홈을 든다(아래 `$FreeSkillHomes`). Codex 나 안티그래비티를
# 고르면 Claude 를 고른 자리와 같은 기본기를 받는다(결정 0097 · 0099). 맡기기 러너만 홈이 갈린다 — 러너의 칸은 맡기는 쪽의
# 조건만 든다. 받는 쪽 홈에 안 가는 것은 갈 곳 표의 `not` 줄이 정하고(받는 쪽 홈에 서면 그 도구가 제게 맡기는 길을 든다 · 결정
# 0097), 이 걸음은 그 줄을 따른다(`Get-FreeSkillNames`). 홈을 같이 쓰면 이 갈림을 못 하므로 홈을 도구마다 둔다. 모두 규범을 안
# 읽어도 홀로 선다.
# 이 표는 제작자 칸에 안 든 도구의 홈에서만 일을 한다(`Install-FreeSkills`) — 칸에 든 도구의 홈은 손(`tool-homes.py`)이 짐 ·
#   저장소의 스킬을 다 놓는다(이 표의 스킬 포함 · 러너는 같은 `not` 줄로 받는 쪽 홈에서 빠진다).
$hostClaude = [bool]($PickKeys -contains 'claude')
$hostCodex  = [bool]($PickKeys -contains 'codex')
$FreeSkills = [ordered]@{
  # 회사 DRM 이 감싼 오피스 · PDF 를 읽는다
  'drm-office-read'          = @{ Claude = $hostClaude; Codex = $hostCodex; Agy = $hostAgy }
  # 사내 앱 · 게이트웨이 · 회사 코딩 기준(씨앗 vibecoding)
  'inhouse-app'              = @{ Claude = $hostClaude; Codex = $hostCodex; Agy = $hostAgy }
  # 맡기기의 앞문 — 누구에게 맡기나 · 작업 지시서(0095)
  'agent-envelope'           = @{ Claude = $hostClaude; Codex = $hostCodex; Agy = $hostAgy }
  # agy 에게 맡기고 한도에서 넘긴다 — 맡기는 쪽은 Claude · Codex
  'agy-background'           = @{ Claude = [bool]($hostClaude -and $wantAgyDelegate); Codex = [bool]($hostCodex -and $wantAgyDelegate) }
  # Codex 에게 맡기고 한도면 Copilot 이 받는다 — 맡기는 쪽은 Claude · agy
  'codex-copilot-background' = @{ Claude = $wantCcBgClaude; Agy = $wantCcBgAgy }
  # Claude 에게 읽기만 하는 일을 맡긴다 — 맡기는 쪽은 Codex · agy
  'claude-background'        = @{ Codex = $wantClaudeBgCodex; Agy = $wantClaudeBgAgy }
}
# 칸 없이 까는 스킬의 홈 — 위 표의 칸 이름마다 화면의 이름(`Label`) · 그 도구가 제작자 칸에 드나(`Box` — 들면 그 홈은 손이
#   쓴다) · 자리(`Place` — 스킬 홈 · 기록 · 기록이 든 폴더 · 안 놓는 이름). 자리는 짐의 갈 곳 표에서 짓는다(`Read-FreeSkillTable`) —
#   칸을 켜면 손이 같은 기록을 넘겨받으므로 그 자리의 원본은 그 표 하나다. Codex 홈이 Codex 공식 문서 「Build skills」의 사용자 범위
#   자리이고 agy 홈이 agy 가 목록 없이 싣는 기본 전역 스킬 자리라는 것도 표가 든다(claude-config 결정 0111).
$FreeSkillTable = Read-FreeSkillTable (Join-Path $Kit 'tool-homes.conf')
$FreeSkillHomes = [ordered]@{
  Claude = @{ Label = 'Claude 홈'; Box = $personalClaude; Place = $FreeSkillTable.Homes['claude'] }
  Codex  = @{ Label = 'Codex 홈'; Box = $personalCodex; Place = $FreeSkillTable.Homes['codex'] }
  Agy    = @{ Label = 'agy 홈'; Box = $personalAgy; Place = $FreeSkillTable.Homes['agy'] }
}
# 개발도구 칸을 꺼도 파이썬을 까는 까닭들 — 「프로그램」 걸음이 곁말로 그대로 찍는다.
$needPythonWhy = @()
if ($wantProxy)       { $needPythonWhy += '로컬 프록시가 이것으로 돈다' }
if ($wantAgyDelegate) { $needPythonWhy += 'agy 백그라운드 래퍼가 pythonw 로 돈다' }
if ($wantCcBg)        { $needPythonWhy += 'Codex · Copilot 맡기기 래퍼가 파이썬으로 돈다' }
if ($wantClaudeBg)    { $needPythonWhy += 'Claude 맡기기 래퍼가 python 으로 돈다' }
if ($PickKeys -contains 'codex') { $needPythonWhy += 'Codex 훅이 파이썬으로 돈다' }
if ($hostAgy)                    { $needPythonWhy += 'agy DRM · BOM 훅이 파이썬으로 돈다' }
if ($PickKeys -contains 'claude') { $needPythonWhy += 'DRM 길잡이 훅이 감긴 첨부를 파이썬으로 잰다' }
if ($PickKeys -contains 'claude') { $needPythonWhy += 'Claude 훅 등록을 놓는 손(tool-homes.py)이 파이썬으로 돈다' }
# 제작자 칸을 켰으면 고른 기능이 손(`tool-homes.py`)으로 선다 — 칸을 켠 도구가 위 까닭을 이미 들어도 이 까닭은 따로 적는다
if ($personalAny) { $needPythonWhy += '제작자 칸의 규범 · 룰 · 스킬을 놓는 손(tool-homes.py)이 파이썬으로 돈다' }
if (@($BrowserMcpHosts.Keys | Where-Object { $PickKeys -contains $_ }).Count) { $needPythonWhy += '브라우저 MCP 를 다는 어댑터(browser-mcp.py)가 파이썬으로 돈다' }
$needPython = [bool]$needPythonWhy.Count
# 안티그래비티는 틀 파일이 없다 — 심을 것이 `modelProvider` 한 줄이라, 무는 것은 「사내인가」와 「이 제품을 켰나」뿐이다.
$wantAgy    = [bool]($inside -and ($PickKeys -contains 'antigravity'))
# 회사 키의 다른 이름 표(`$KeyAliases`)의 `Need` 를 이 자리가 푼다 — 표는 이름만 들고 켜고 끄는 것은 여기다.
# ⚠ **`gemini` 칸은 안티그래비티의 것이다 — 이름만 구글이 정한 키 이름을 따른다.** `agy` 는 `modelProvider: "gemini"` 아래에서
#   `GEMINI_API_KEY` 를 읽는다. 설치기만 돌린 기계에는 세션 훅의 `secrets.d/<자리>.env` 가 없어 이 칸 말고는 그 키를 심는 자가
#   없다 — 안 심기면 `agy` 가 «GEMINI_API_KEY environment variable is not set» 으로 안 뜬다.
# 이 한 칸이 세 자리(심는 문 `$KeyAliases` 고리 · `GOOGLE_API_KEY` 충돌 경고 · 끝 검증)를 문다 — 조건은 여기 하나만 고친다.
$wantNeed = @{ codex = $wantCodex; gemini = $wantAgy }
# ── 프록시가 밖에 남기는 자리 둘 — **이름은 여기 한 자리다** ─────────────────────
# ⚠ **심는 자와 걷는 자가 같은 이름을 봐야 한다.** 아래 「로컬 프록시」 칸이 이 자리들을 만들고 「사외로 간 자리의 사내 잔재」 칸이
#   걷는다 — 두 자리에 글자를 따로 박으면 한쪽만 고쳐지는 날 걷는 손이 딴 자리를 지우고 진짜 잔재는 그대로 돈다. 지우는 손은 헛도는
#   줄도 안 남긴다.
$ProxyRunName  = 'PGPTProxy'          # HKCU\...\Run 의 등록 이름 (이전 판 잔재 정리용)
$ProxyTaskName = 'PGPTProxy-Watchdog' # 작업 스케줄러의 프록시 감시 작업 이름
$ProxyDirName  = 'PGPT-Proxy'         # %LOCALAPPDATA% 아래 실행 폴더 이름

# ── 회사 설정 둘이 앉는 자리 — **같은 까닭으로 여기 한 자리다** ─────────────────
# 아래 「Codex · 안티그래비티 설정」 칸이 이 둘에 쓰고 끝의 검증이 이 둘을 다시 재므로, 글자를 두 자리에 박지 않는다 (PAISetup #3).
$CodexCfg  = Join-Path $env:USERPROFILE '.codex\config.toml'
# ⚠ **안티그래비티는 `.gemini\antigravity-cli\settings.json` 이다 — 같은 뿌리의 `.gemini\settings.json` 이 아니다.**
#   그 파일은 Gemini CLI 의 것이라 `agy` 가 안 읽고, 이 설치기도 안 쓴다(결정 0136).
$AgyCfg    = Join-Path $env:USERPROFILE '.gemini\antigravity-cli\settings.json'
# 회사 연결을 가르는 자 둘 — 그 칸이 사내에서 심고 사외에서 걷고 끝 검증이 다시 재는 같은 자다. Codex 는 틀의 자리를 병합기가 알고
#   (맞추기 판 · 걷기 판), 안티그래비티는 인증 방식 한 줄(`modelProvider`)의 회사 값이다(사외에서 걷나는 그 키까지 — `Test-AgyCompanyLink`).
#   병합기는 씨앗이 홈에 깔리기 전이라 이 폴더의 씨앗 자리에서 부른다.
$CodexCfgMerge = Join-Path $Here 'seeds\config-repo\.claude\hooks\codex-config-merge.py'
$AgyProvider   = 'gemini'
if ($proxyRel -or $codexTpl) {
  $more = @()
  if ($wantProxy)  { $more += '로컬 프록시' }
  if ($wantCodex)  { $more += 'Codex 회사 설정' }
  if ($wantAgy)    { $more += '안티그래비티 회사 설정' }
  if ($more.Count) { Write-Host ("  사내라 더 세운다 — " + ($more -join ' · ')); Write-Host '' }
  elseif (-not $inside) { Write-Host '  프록시와 Codex·안티그래비티 회사 설정은 사내에서만 선다 — 여기서는 프로그램만 깔고 각자 로그인으로 쓴다'; Write-Host '' }
}

# ── 올릴 것이 있는 앱을 **한 번에** 묻는다 ─────────────────────────────────────
# 앱마다 `winget upgrade --id` 를 부르지 않는다 — winget 은 뜰 때마다 원본을 새로 훑어 앱 수만큼 그 값을 낸다.
#   `list --upgrade-available` 은 그 훑기를 한 번에 끝낸다.
# ⚠ **못 읽으면 앱마다 묻는 길로 물러선다.** 이 출력은 표라서 로케일 · 콘솔 너비 · 잘린 Id 에 흔들린다. 못 읽은 것을 「올릴 것
#   없음」으로 읽으면 판이 낡은 채로 초록이 된다 — 그래서 `$upgradable` 의 `$null` 은 「못 쟀다」다.
# ⚠ **winget 이 올리는 갈래는 다 이 목록에 묻는다** — 프로그램 · 고른 데스크탑 앱 · winget CLI. 목록에 없는 Id 를 「올릴 것
#   없음」으로 읽으므로(`Get-Listed`), 여기서 안 물은 갈래는 목록을 받은 판에서 영영 안 올라간다(결정 0145).
$upgradable = $null
# CLI 표에서 이번 설치가 깔 줄 — 고른 제품의 CLI 와, 제작자 칸을 켰을 때 그 칸의 스킬이 부르는 도구(`Maker`), 고른 제품이 쓰는
#   꾸러미(`For`). 올리기를 묻는 이 덩어리와 「CLI」 걸음이 같은 목록을 쓴다.
$CliPicks = @($Clis | Where-Object { ($PickKeys -contains $_.Key) -or ($_.Maker -and $personalAny) -or
                                     ($_.For -and @($_.For | Where-Object { $PickKeys -contains $_ }).Count) })
if (-not ($NoUpgrade -or $noWinget)) {
  Say-Busy '프로그램 판' 'upcheck' @('winget · 한 번에')
  # 시간 울타리를 두른다 — 멎은 winget 하나가 설치를 영구히 세운다(PAISetup #26 과 같은 꼴). 넘기면 목록을 못 받은 것(`$null`)이라 앱마다 묻는다.
  $ulog = [System.IO.Path]::GetTempFileName()
  $urc = Invoke-LoggedCapped 'winget' @('list','--upgrade-available','--accept-source-agreements','--disable-interactivity') $ulog $WingetListCap
  $utxt = ''
  if (Test-Path $ulog) { $utxt = (Get-Content $ulog -Raw -Encoding UTF8 -ErrorAction SilentlyContinue) }
  Remove-Item -LiteralPath $ulog, "$ulog.err" -ErrorAction SilentlyContinue
  if ($urc -eq -2) { Add-ProbeOverflow 'winget list --upgrade-available' $WingetListCap }
  if ($urc -eq 0 -and $utxt -and $utxt.Length -gt 40) {
    # 이름 칸은 데스크탑 앱이 시작 메뉴 이름(`App`), winget CLI 가 제 글자(`Label`)다 — 판정은 Id 가 든다.
    $asked = @($Apps) +
             @($DesktopApps | Where-Object { ($PickKeys -contains $_.Key) -and $_.Via -eq 'winget' -and -not $_.NoSelfUpgrade } |
               ForEach-Object { @{ Name = $_.App; Id = $_.Id } }) +
             @($CliPicks | Where-Object { $_.Via -eq 'winget' } |
               ForEach-Object { @{ Name = $_.Label; Id = $_.Id } })
    $hits = @()
    foreach ($a in $asked) {
      if (Test-UpgradeRow $utxt $a) { $hits += $a.Id }
    }
    $upgradable = $hits
    if ($hits.Count) {
      Write-Host ('  올릴 것 ' + $hits.Count + '개 — ' + ($hits -join ' · '))
    } else {
      Write-Host '  올릴 것 없음 — 판 대조를 한 번에 끝냈다'
    }
  } else {
    # 까닭을 댄다 — 넘김이면 그 한도를, 졌으면 그 값을. 표를 못 읽은 것과 winget 이 진 것은 다음에 볼 자리가 다르다.
    $uwhy = if ($urc -eq 0) { '표를 못 읽어' } else { '`winget list --upgrade-available` 이 ' + (Format-ProbeWhy $urc $WingetListCap) }
    Write-Host "  (올릴 목록을 한 번에 못 받았다 — $uwhy 앱마다 묻는다)"
  }
}
# 「준비」 — 값 파일 읽기 · 자리 프로브 · winget 의 판 대조. 「프로그램」 걸음 앞에도 시간이 든다.
Write-Elapsed '준비'

# ══ 걸음 「프로그램」 ═══════════════════════════════════════════════════════════════════════════
#   층 — 기계
#   하는 일 — winget 앱(VS Code · Node · Git · Python · gh) · VC++ 런타임(파이썬이 서는 판) · 데스크탑 앱 · Node 신뢰
#   앞에서 받는 것 — 준비의 고른 제품 · 자리 · 올릴 것 목록 · winget 유무 · 파이썬이 필요한 까닭
#   안 하는 것 — 홈 파일 · 키. 예외 하나 — Node 신뢰가 CA 경로(`NODE_EXTRA_CA_CERTS`)를 사용자 환경에 심는다.
#     뒤의 확장 · CLI 가 그 값을 물고 받으므로 이 걸음에 선다
Enter-Step 'programs'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)
foreach ($app in $Apps) {
  # VS Code 를 끄면 VS Code 만 안 깐다 — Node 는 CLI 가 타므로 `core` 로 남아 그대로 깔린다.
  if ($NoVsCode -and $app.Need -eq 'vscode') {
    Write-Host "  $($app.Name) — 건너뜀 (VS Code 칸을 껐다)"
    continue
  }
  if ($NoDevTools -and $app.Need -eq 'dev') {
    # 파이썬만은 예외가 선다 — 개발도구를 꺼도 파이썬으로 도는 것(사내 로컬 프록시 · 맡기기 래퍼 · 훅 · 손)을 고른 판이면
    #   이것만 깐다(결정 0041). 까닭은 `$needPythonWhy` 가 든다.
    if ($needPython -and $app.Cmd -eq 'python') {
      Write-Host "  $($app.Name) — 개발도구를 껐지만 깐다 ($($needPythonWhy -join ' · '))"
    } else {
      Write-Host "  $($app.Name) — 건너뜀 (-NoDevTools)"
      continue
    }
  }
  # 할 일은 한 자리(`Get-InstallAction`)가 가른다 — 올릴지는 맨 앞에서 한 번에 받은 목록이, 못 받았으면 앱마다 묻는다.
  #   판(`Get-Ver`)은 화면에만 쓴다 — 견주기는 winget 이 제 기록으로 한다.
  # ⚠ **못 쟀으면 깔지도 올리지도 않는다** — 넘김이나 선 이름의 실패를 「없다」로 읽으면 깔린 것 위에 `winget install` 을 돌린다(결정 0141 ·
  #   0145 · 0151 · PAISetup #37).
  $appRuns = Measure-Runs $app.Cmd $app.Arg
  $before  = if ($appRuns -eq 'yes') { Get-Ver $app.Cmd $app.Arg } else { '' }
  $appAct  = Get-InstallAction $appRuns $before '' (Get-Listed $app.Id) $true ($NoUpgrade -or $noWinget)
  if ($appAct -eq 'hold') {
    Add-UnmeasuredStep $app.Name "$($app.Cmd) $($app.Arg)" '깔지도 올리지도 않았다' '' "winget install --id $($app.Id) --force"
    continue
  }
  if ($appAct -eq 'present') { Write-Host "  $($app.Name) — 있음  $(Format-VerPart $before)"; continue }
  if ($appAct -eq 'latest')  { Write-Host "  $($app.Name) — 최신  $(Format-VerPart $before)"; continue }
  # 기계 범위 행 — 승인 창이 뜨는 PC 인데 누를 사람이 없는 판이면 걸지 않는다(사람을 기다리며 서지 않게 · 누를 사람이 있나는 결정 0146 과 같은 자)
  if ($app.Scope -eq 'machine' -and -not $noWinget -and
      (Get-ElevationGo (Read-ElevationState) ([bool]((-not ($Yes -and $NoLaunch)) -and [Environment]::UserInteractive))) -eq 'later') {
    Write-Host "  ! $($app.Name) — 관리자 승인 창이 뜨는 PC 인데 누를 사람이 없는 판이라 안 $(if ($appAct -eq 'install') { '깔았다' } else { '올렸다' }) · 설치 창으로 다시 누르면 승인 창이 한 번 뜬다" -ForegroundColor Yellow
    continue
  }
  if ($appAct -eq 'upgrade' -or $appAct -eq 'upcheck') {
    Invoke-WingetUpgrade $app.Name $app.Id 'winget' $appAct @("지금 $before")
    Update-RuntimePath
    Write-UpgradeResult $app.Name $before (Get-Ver $app.Cmd $app.Arg)
    continue
  }
  if ($appAct -ne 'install') { continue }

  if ($noWinget) {
    Write-Host "  ! $($app.Name) — 없는데 winget 이 없어 못 깐다" -ForegroundColor Red
    $Fails.Add("$($app.Name) (winget 이 없다)")
    continue
  }

  # 받고 까는 몇 분 동안 화면이 조용하다 — winget 출력을 통째로 파일로 돌린다(진행 막대가 로그를 덮어, 실패할 때만 편다). 그 침묵은
  #   멎은 것과 구분이 안 돼 사람이 창을 닫으므로, 조용할 것이라고 미리 말한다. 막대를 화면으로 흘리지 않는다 — 화면 껍데기의 기록
  #   칸이 막대로 도배된다.
  Say-Busy $app.Name 'install' @('winget', '몇 분 조용할 수 있다')
  $log = [System.IO.Path]::GetTempFileName()
  # ⚠ **종료코드를 안 버린다.** 판정은 프로브가 들지만(winget 은 「올릴 것 없음」에도 0 이 아닌 값을 낸다), 프로브가 끝내 못 잡았을
  #   때 「깔렸는데 이 창이 못 잡는다」와 「진짜 못 깔았다」를 가르는 자가 이것뿐이다.
  $rc = Invoke-Logged 'winget' (@('install','--id',$app.Id) + $WG) $log
  Update-RuntimePath
  # 한 번 재고 포기하지 않는다 — winget 이 일을 떼어 놓고 먼저 돌아오는 자리가 있어, 곧바로 물으면 아직 안 선 것을 「실패」로
  #   찍는다. 이미 선 기계는 첫 물음에 서므로 느려지지 않는다. 기다리는 동안 배선을 다시 태운다 — 그 폴더는 설치가 끝나면서 생긴다.
  # ⚠ **끝 시각으로 센다 — 묻는 횟수로 세지 않는다.** 한 번 묻는 데 울타리(`$ProbeCap`)까지 걸릴 수 있어, 횟수로 세면
  #   기다림이 그 곱으로 는다. 끝 시각을 넘긴 뒤에는 더 묻지 않으므로 넘는 몫은 한 번의 물음뿐이다(결정 0141).
  #   10초는 즉답하는 물음을 0.75초 틈으로 여남은 번 되풀이할 길이다 — 먼저 돌아온 설치가 서기를 기다리는 「몇 초」다.
  $ok = $false
  $waitEnd = (Get-Date).AddSeconds(10)
  while ($true) {
    if (Test-Runs $app.Cmd $app.Arg) { $ok = $true; break }
    if ((Get-Date) -ge $waitEnd) { break }
    Start-Sleep -Milliseconds 750
    Update-RuntimePath
  }
  if ($ok) {
    Write-Host "  $($app.Name) — 깔았다" -ForegroundColor Green
  } elseif ($rc -eq 0) {
    # 거짓 빨강을 덜되 초록으로 넘기지는 않는다 — winget 이 성공이라 했는데 이 창이 못 잡는 것은 흔히 PATH 가 새 프로세스부터
    #   서기 때문이다. 못 잡은 것은 남기고 사유만 바꾼다 — 「설치 실패」로 적으면 멀쩡히 깔린 것을 찾아 헤맨다.
    Write-Host "  ! $($app.Name) — winget 은 깔았다는데 이 창이 못 잡는다 (새 창에서 잡힌다)" -ForegroundColor Yellow
    $Fails.Add("$($app.Name) (깔렸는데 이 창에서 안 잡힌다 — 새 창에서 본다)")
  } else {
    Write-Host "  ! $($app.Name) 설치 실패 (winget 이 $rc 로 끝났다) — 뱉은 끝 줄:" -ForegroundColor Red
    Show-Log $log 5
    $Fails.Add("$($app.Name) 설치")
  }
  Remove-Item $log -ErrorAction SilentlyContinue
}

# ── GitHub 로그인 창을 앞당겨 띄운다 — gh 가 선 바로 뒤, 숨은 자식에 (PAISetup #35 A) ─────────────────────
# 코드 창은 사람을 기다리는 동안 제 프로세스를 세운다(`ShowDialog()`). 「설정 저장소」 걸음에서 이 프로세스로 열면 그 사이 설치가 멎으므로,
#   이 몸통을 `-GhLoginOnly` 로 다시 띄워 그 안에서 열고 설치는 잇는다. 답은 「설정 저장소」 걸음의 로그인 칸이 받는다.
# gh 는 위 `$Apps` 의 마지막 줄이라 이보다 앞은 없고, 뒤로 남은 걸음(VC++ · 데스크탑 앱 · 확장 · CLI …)이 창의 한도를 덮는다.
# 띄우는 조건은 그 칸과 같다 — `#config-repo` 가 있고 · git 이 닿고 · 개발 도구를 켰고 · 창을 띄울 판(`Get-GhLoginGo`)일 때. 안
#   띄운 판은 그 칸이 제 자리에서 다시 잰다.
$script:GhLoginChild = $null
if ($repoUrl -and -not $NoDevTools -and (Test-Runs 'git' '--version') -and (Get-GhLoginGo) -eq 'open') {
  $script:GhLoginChild = Start-GhLoginChild $MyInvocation.MyCommand.Path
  if ($script:GhLoginChild.Proc) {
    Write-Host "  GitHub 로그인 — 창을 띄웠다 · 코드는 팝업에 (최대 ${GhLoginWait}초) · 설치는 그대로 잇는다" -ForegroundColor Yellow
  }
}

# ── VC++ 런타임 — 파이썬이 서는 판이면 그 C++ 확장이 싣는 런타임을 `$VcRuntimeMin` 이상으로 세운다 (claude-config 결정 0146) ──
# 파이썬 칸과 같은 문이다 — 개발도구를 끄고 파이썬이 필요한 까닭도 없는 판에는 이 런타임을 실을 것이 없고, 기계 범위 설치라 관리자
#   승격이 드는 걸음을 괜히 걸지 않는다. 끝 검증의 그 줄도 이 값을 읽는다.
# 승인 창을 눌러 줄 사람이 있나는 이 설치기가 이미 쓰는 두 자로 가른다 — 창 없이 돈 판(로그온 자동 실행이 늘 넘기는 `-Yes -NoLaunch` ·
#   끝의 「제공기능」 칸과 같은 가름)과 누를 사람이 없는 세션(`UserInteractive` · `Ask-Restart` 와 같은 자).
$wantVcRuntime = [bool](-not $NoDevTools -or $needPython)
if ($wantVcRuntime) {
  Install-VcRuntime ([bool]((-not ($Yes -and $NoLaunch)) -and [Environment]::UserInteractive))
}

# ── 데스크탑 앱 설치 — **켤지는 값 파일이, 언제는 행이, 무엇을은 제품 칸이 정한다** ──────
# 「사내에 쓸모가 없다」는 앱마다 다르다(결정 0059). 게이트웨이를 물리는 `ANTHROPIC_BASE_URL` 은 Claude Code CLI 만 읽고 앱에는
#   그 스위치가 없어, 게이트웨이를 물어야 쓸모가 있는 앱(Claude · Codex · Antigravity — 결정 0045)은 사내에서 깔려도 막힌 제 본사로
#   나가려 한다. 게이트웨이를 안 타는 앱은 제 인증으로 붙어 사내에서도 선다. 그래서 그 판정을 행(`$DesktopApps` 의 `When`)이 들고,
#   안 적은 행은 `offsite` 다.
# `#desktop-app` 은 전체 스위치다 — 없으면 아무것도 안 깐다. 이 줄이 드는 것은 「언제」뿐이고 무엇을 깔지는 제품 칸(`$PickKeys`)이
#   든다. `:` 뒤 목록을 든 값 파일은 말하고 지나간다 — 조용히 무시하면 고친 사람이 제 줄이 죽은 줄 모른다.
#
#       #desktop-app = offsite   행마다 갈린다 — offsite 행은 사외에서만, any 행은 늘
#       #desktop-app = yes       행의 `When` 도 안 보고 켠 제품 전부 — 사람이 「자리 안 가리고 깔아라」를 명시한 자리다
#
# GUI 앱이라 PATH 로 못 잰다 — `--version` 을 부를 이름이 안 생긴다. winget 갈래는 winget 의 목록에, 제 설치본 갈래는 시작 메뉴에
#   묻는다. 짝으로 딸린 런타임은 그 둘로도 못 재 레지스트리가 든다(`Test-WebView2`).

# 이번 판에 인스톨러가 새로 깐 데스크탑 앱(`Install-DesktopApp` 이 채운다 · 키는 행의 `App`). 있나는 길마다 묻는 자가 다르고,
#   종료코드를 판정으로 안 쓰는 것은 위 「앱」 칸과 같은 결이다.
$script:JustInstalledApps = @{}
# ── 이 판에서 **깔거나 이미 서 있던** 데스크탑 앱 — 끝의 「연다」 칸이 이것에 묻는다 (결정 0059) ──
# 자리로 묻지 않는다 — 「언제」가 행에 있어 사내에서도 깔리는 앱이 있고, 자리로 물으면 방금 깐 것을 안 띄운다.
# ⚠ **`JustInstalledApps` 와 다른 자다.** 저쪽은 이번에 깐 것만 들어(인스톨러가 제 손으로 띄웠나를 가른다) 이미 있던 앱은 안 든다.
#   여기는 이 판에서 선 것 전부라야 한다 — 어제 깐 앱도 오늘 띄운다. 키는 `Label`(화면에 쓰는 이름), 값은 표의 행이다.
$script:InstalledAppRows = @{}

# ── 짝으로 먼저 서야 하는 런타임 — **있으면 안 깐다** (PAISetup #16 · 결정 0059) ──────────────────
# ⚠ **`Test-DesktopApp` 으로 못 잰다 — 레지스트리에 묻는다.** WebView2 는 GUI 앱이 아니라 런타임이라 시작 메뉴(`Get-StartApps`)에
#   안 서고, `winget list` 는 찾기는 하는데 이름과 판을 Edge 의 것으로 낸다. 레지스트리가 WebView2 를 찾는 앱이 실제로 보는
#   자리다. 기계 자리와 사용자 자리를 둘 다 본다(설치 갈래가 둘이다).
# 판을 안 견주고 「있나」만 본다 — 하한을 벤더가 안 내(매니페스트에 `Dependencies` 가 없다) 숫자를 박으면 근거 없는 규칙표가 된다.
#   이 런타임은 Edge 채널을 타는 Evergreen 이라 한 번 서면 저절로 따라간다.
# ⚠ **`--source winget` 을 박는다.** 안 박으면 msstore 까지 훑다가 그쪽 인증서 오류(`0x8a15005e`)로 설치가 시작도 못 하는데,
#   종료코드는 0 이라 성공으로 보인다.
$WebView2Guid = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'

# 짐의 `#desktop-app` 을 읽는다(`Read-DesktopAppSwitch` — `-Describe` 의 `app|` 줄도 같은 손을 지난다). `:` 뒤 목록은 위 머리말대로
#   말하고 지나간다.
$wantApp   = Read-Directive $DistEnvFile 'desktop-app'
$appSwitch = Read-DesktopAppSwitch $wantApp
$appWhen   = $appSwitch.When
if ($appSwitch.Extra) {
  Write-Host ''
  Write-Host ('  ! #desktop-app 의 : 뒤 목록은 이제 안 쓴다 — 무엇을 깔지는 제품 칸이 든다 (준 값: {0})' -f
              $appSwitch.Extra) -ForegroundColor Yellow
}
$appPicks = @($DesktopApps | Where-Object { $PickKeys -contains $_.Key })

# ── Codex 데스크탑의 샌드박스 키 — 데스크탑을 깔기 **앞에** `config.toml` 에 `[windows]` 의 `sandbox` 를 둔다 (claude-config 결정 0127) ──
# 데스크탑의 앱 서버는 뜰 때 이 키를 한 번 읽어 샌드박스 판을 굳힌다. 키 없이 뜨면 앱은 샌드박스 「첫 설정」 길을 타고, 그 길 끝에서
#   새 대화의 기본 권한을 「승인 요청」(`auto`)으로 덮어 설치가 심는 「나 대신 승인」이 사라진다. 키가 있으면 「업데이트」 길이라 권한을
#   안 쓴다(배너를 누르고 관리자 승인 한 번은 같다). 데스크탑은 깔리자마자 스스로 떠 그 서버를 세우므로 설치 앞이다.
# 값은 `elevated` — 앱이 고르는 기본이고 회사 틀의 `[windows]` 표와 같다. `unelevated` 는 승인 창이 없는 대신 샌드박스가 약하다.
# 사람의 것을 지킨다 — 파일이 없으면 그 두 줄로 짓고, `windows.sandbox` 가 이미 서 있으면 둔다(TOML 처럼 대소문자를 가린다). `[windows]` 가
#   있는데 `sandbox` 가 없거나, 파일을 못 읽거나(깨진 TOML · 파이썬 3.11 이상이 안 선다), 파일이 링크이거나, `CODEX_HOME` 이 다른 자리를
#   가리키면(앱이 그 자리의 설정을 읽는다) 안 건드린다. 그 밖은 원래 바이트 뒤에 그 표를 붙이되, 붙인 글을 임시 파일에서 TOML 로 읽어 원래
#   키가 뜻 그대로이고 더해진 것이 그 표 하나일 때만, 그 사이 원래 파일이 안 바뀌었을 때만 곁 사본을 두고 갈아 끼운다.
# ⚠ 점 키(`windows.sandbox = …`)로 쓰지 않고 파일 머리에 얹지도 않는다 — 회사 틀과 사람이 쓰는 꼴이 `[windows]` 표라 한 파일에 두 꼴이
#   서면 TOML 이 설정째 거절하고, 표 머리를 앞에 얹으면 그 뒤의 맨 위 키가 그 표로 들어간다.
# 짓기 · 붙이기는 갈아 끼우는 손(`Write-FileSafely`)이 든다 — 곁 사본 · 다시 견주기 · 진 판의 되돌리기는 그 손의 머리가 든다.
# 내는 것 — @{ Did = made · added · kept · raced(쓴 뒤 다른 프로그램이 고쳤다 — 그 글을 둔다) · left(안 건드렸다) · unmeasured(파이썬
#   물음이 울타리를 넘겼다 — 안 건드렸다); Have = kept 의 그 값; Why = left · raced · unmeasured 의 까닭; Probe = unmeasured 의 물음 }.
#   화면 줄은 부르는 쪽이 든다 — 못 지운 임시 사본(원래 설정을 그대로 든다) 줄만 갈아 끼우는 손이 낸다. 무엇을 심었나의 장부는 「도구별 홈」의
#   「Codex 데스크탑의 샌드박스 키의 장부」 칸이 이 결과(`$sbx`)로 맞춘다.
$CodexSandboxMode = 'elevated'
function Set-CodexSandboxKey([string]$Path) {
  $utf8 = New-Object Text.UTF8Encoding($false)
  $block = "[windows]`nsandbox = `"$CodexSandboxMode`"`n"
  if ($env:CODEX_HOME) {
    $there = try { [IO.Path]::GetFullPath($env:CODEX_HOME).TrimEnd('\') } catch { $env:CODEX_HOME }
    if ($there -ne [IO.Path]::GetFullPath((Split-Path $Path -Parent)).TrimEnd('\')) {
      return @{ Did = 'left'; Why = "CODEX_HOME($env:CODEX_HOME) 이 서 있어 앱은 그 자리의 설정을 읽는다" }
    }
  }
  # 링크는 짓기 앞에서 가린다 — 끊긴 링크는 「없는 파일」로 읽혀 짓기가 링크 너머에 쓴다
  $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
  if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    return @{ Did = 'left'; Why = '설정 파일이 링크다 — 갈아 끼우면 링크가 끊긴다' }
  }
  if (-not (Test-Path -LiteralPath $Path)) {
    $w = Write-FileSafely $Path ($utf8.GetBytes($block)) $null
    if ($w.Did -ceq 'written') { return @{ Did = 'made' } }
    if ($w.Did -ceq 'overrun') { return @{ Did = 'left'; Why = '지은 파일을 되읽으니 그 두 줄이 아니다' } }
    return @{ Did = 'left'; Why = $w.Why }
  }
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return @{ Did = 'left'; Why = '그 자리가 파일이 아니다' } }
  $timed = $script:ProbeTimedOut.Count
  $now = Read-TomlTopKeys $Path @('windows')
  if ($null -eq $now) {
    if ($script:ProbeTimedOut.Count -gt $timed) { return @{ Did = 'unmeasured'; Probe = $TomlReadProbe; Why = (Format-ProbeWhy -2 $ProbeCap) } }
    return @{ Did = 'left'; Why = 'TOML 로 못 읽었다(깨진 파일이거나 파이썬 3.11 이상이 안 선다)' }
  }
  $w = $now.PSObject.Properties['windows']
  if ($w) {
    if ($w.Value -is [System.Management.Automation.PSCustomObject] -and @($w.Value.PSObject.Properties | Where-Object { $_.Name -ceq 'sandbox' }).Count) {
      return @{ Did = 'kept'; Have = "windows.sandbox = $($w.Value.sandbox | ConvertTo-Json -Compress)" }
    }
    return @{ Did = 'left'; Why = $(if ($w.Value -is [System.Management.Automation.PSCustomObject]) { '[windows] 표에 sandbox 가 없다' } else { 'windows 가 표가 아니다' }) }
  }
  $old = [IO.File]::ReadAllBytes($Path)
  $nl = if ($utf8.GetString($old).Contains("`r`n")) { "`r`n" } else { "`n" }
  $lead = if (-not $old.Length) { '' } elseif ($old[-1] -eq 10) { $nl } else { $nl + $nl }
  $new = [byte[]]($old + $utf8.GetBytes($lead + $block.Replace("`n", $nl)))
  # 붙인 글의 뜻 — 원래 표에서 `windows` 하나만 늘었나. 큰따옴표 없이 적는다(5.1 이 네이티브 인자 안의 큰따옴표를 깨뜨린다).
  $same = "import sys,tomllib;a=tomllib.load(open(sys.argv[1],'rb'));b=tomllib.load(open(sys.argv[2],'rb'));w=b.pop('windows',None);sys.exit(0 if a==b and w=={'sandbox':sys.argv[3]} else 3)"
  # 붙인 글은 곁의 임시 파일에 먼저 써 뜻을 잰 뒤에만 갈아 끼운다(`Write-FileSafely` — 끼우기 바로 앞에 원래 바이트와 다시 견주고, 지면
  #   원래 파일로 되돌린다). 쓰다 져도 원래 파일이 반쯤 잘린 채 남지 않는다.
  $probe = "$Path.paisetup-$([guid]::NewGuid().ToString('N').Substring(0, 8)).probe"
  $tl = [IO.Path]::GetTempFileName()
  try {
    [IO.File]::WriteAllBytes($probe, $new)
    # `-I` — 작업 폴더의 같은 이름 모듈(`tomllib.py` · `json.py`)을 안 집는다
    $rc = Invoke-LoggedCapped 'python' @('-I', '-X', 'utf8', '-c', $same, $Path, $probe, $CodexSandboxMode) $tl $ProbeCap
    if ($rc -eq -2) { Add-ProbeOverflow $TomlReadProbe $ProbeCap; return @{ Did = 'unmeasured'; Probe = $TomlReadProbe; Why = (Format-ProbeWhy -2 $ProbeCap) } }
    if ($rc -ne 0) { return @{ Did = 'left'; Why = "붙인 결과가 그 뜻으로 안 읽힌다 (python $rc)" } }
  } finally {
    Remove-Item -LiteralPath $tl, "$tl.err", $probe -ErrorAction SilentlyContinue
  }
  # 재는 사이 다른 프로그램(Codex CLI · 확장)이 고쳤으면 안 끼우고(left), 끼운 뒤 되읽은 글이 다르면 그 글을 둔다(raced)
  $w = Write-FileSafely $Path $new $old
  if ($w.Did -ceq 'written') { return @{ Did = 'added' } }
  if ($w.Did -ceq 'overrun') { return @{ Did = 'raced'; Why = $w.Why } }
  return @{ Did = 'left'; Why = $w.Why }
}
# ── 자리 판정 — **행마다 묻는다** (PAISetup #16 · 결정 0059) ──────────────────────────────────
# 스위치의 두 값은 위 「데스크탑 앱 설치」 머리말이 든다. 안 깐 까닭을 행마다 댄다 — 같은 판에서 어떤 행은 깔리고 어떤 행은
#   안 깔려, 안 깔린 줄이 침묵하면 고른 사람이 제 선택이 죽은 줄 모른다.
if ($appWhen -eq 'yes' -or $appWhen -eq 'offsite') {
  # 빈 목록도 말한다 — 제품을 하나도 안 켠 판이 한 줄도 없이 지나가지 않게.
  if (-not $appPicks) {
    Write-Host ''
    Write-Host '  데스크탑 앱 — 켠 제품이 없어 안 깐다'
  }
  foreach ($da in $appPicks) {
    # 행이 「언제」를 안 적으면 `offsite` 다 — 그 자는 `Test-DesktopAppHere` 하나가 든다(설치 창의 안내 줄도 그 답으로 선다).
    if (Test-DesktopAppHere $da $appWhen $offsite) {
      # Codex 는 데스크탑의 앱 서버가 처음 뜨기 전에 샌드박스 키가 서야 한다(위 `Set-CodexSandboxKey`)
      if ($da.Key -eq 'codex') {
        $sbx = Set-CodexSandboxKey $CodexCfg
        $sbxName = 'Codex 데스크탑 · 샌드박스 키'
        switch ($sbx.Did) {
          'made'       { Write-Host "  $sbxName — 데스크탑보다 먼저 지었다 ([windows] sandbox = `"$CodexSandboxMode`")" -ForegroundColor Green }
          'added'      { Write-Host "  $sbxName — 데스크탑보다 먼저 설정 끝에 더했다 ([windows] sandbox = `"$CodexSandboxMode`")" -ForegroundColor Green }
          'kept'       { Write-Host "  $sbxName — 이미 서 있어 둔다 ($($sbx.Have))" }
          'raced'      { Write-Host "  ! $sbxName — 설정 끝에 더했는데 $($sbx.Why) · 그 글을 둔다 ($CodexCfg)" -ForegroundColor Yellow }
          'unmeasured' { Add-UnmeasuredStep $sbxName $sbx.Probe '쓰지도 건너뛰지도 않았다' $sbx.Why }
          default {
            Write-Host "  ! $sbxName — $($sbx.Why) · 안 건드렸다 ($CodexCfg) — 앱의 샌드박스 첫 설정이 새 대화 권한을 「승인 요청」으로 덮을 수 있다" -ForegroundColor Yellow
          }
        }
      }
      Install-DesktopApp $da
      continue
    }
    Write-Host ''
    Write-Host "  $($da.Label)" -ForegroundColor Cyan
    # 자리는 둘뿐이라(「준비」의 「자리」 칸) 안 깐 까닭은 사내 하나다.
    Write-Host '      · 사내라 안 깐다 (게이트웨이를 못 문다)'
  }
}

# ── Node 신뢰 배선 — **「VS Code 확장」 걸음보다 앞이다** ─────────────────────────────────
# 뒤의 두 걸음(「VS Code 확장」 · 「CLI」)이 둘 다 Node 로 내려받는다 — 뒤에 두면 이미 진 뒤에 신뢰를 잇는다.
# ⚠ **`-NoUpgrade` 로 안 건너뛴다.** 이것은 올리는 일이 아니라 서게 하는 일이고, 비영속 VDI 는 로그인마다 사용자 환경변수가 새로
#   나서 매번 다시 심어야 한다.
Write-Host ''
Write-Host '  Node 신뢰 배선' -ForegroundColor Cyan
Wire-NodeTrust

} catch { Write-StepFault $_ }
Exit-Step 'programs'

# ══ 걸음 「VS Code 확장」 ═══════════════════════════════════════════════════════════════════════
#   층 — 기계
#   하는 일 — 깔린 확장을 한 번에 올리고, 고른 제품의 확장을 깐다
#   앞에서 받는 것 — 「프로그램」의 VS Code(`code`) · Node 신뢰
#   안 하는 것 — 사용자 환경 · 홈
# 확장만으로는 안 돈다 — 확장은 Claude Code CLI 를 자식으로 부른다. 그래서 「CLI」 걸음이 붙어 있고, 둘 중 하나만 서면 VS Code 는
#   열리는데 아무 일도 안 일어난다.
# `code` 를 띄우는 횟수가 곧 시간이다 — 한 번 뜰 때마다 노드 프로세스가 서고 마켓플레이스에 한 번 묻는다(VDI 에서 몇 초씩). 그래서
#   판 번호는 한 번 읽고, 깔린 것은 `--update-extensions` 한 번으로 올리고, 다시 한 번 읽어 앞뒤로 「올렸다 · 최신」을 가른다. 빠진
#   확장도 `code` 한 번에 넘기고 목록 한 번으로 잰다(`Install-Extension`).
# `--update-extensions` 는 깔린 확장 전부를 올린다 — 우리 것만 고르는 스위치가 없다. VS Code 가 스스로 하는 자동 갱신과 같은 일이다.

Enter-Step 'extensions'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)
# 확장 갱신 한 호출에 두르는 울타리 — 초. **갱신은 곁일이라 포기할 수 있다**(까닭은 아래 호출 자리).
# 평소 1~14초지만 밀린 회차는 수백 초를 써 정상이 꽤 느릴 수 있는 자리다 — 넉넉히 두되 부르는 쪽 울타리(10분)를 혼자 다 먹지
#   못하게 그 절반 아래로 둔다.
$ExtUpdateCap  = 240
# 이보다 오래 걸렸으면 걸린 시간을 적는다 — 평소치를 넘은 회차만 기록에 남게.
$ExtUpdateSlow = 30
# 고른 제품의 확장만 든다 — 목록이 진본이고 고르는 축은 `$Products` 다.
$ExtPicks = @($Extensions | Where-Object { $PickKeys -contains $_.Key })
# 할 일은 확장마다 `Get-InstallAction` 이 가른다 — 깔렸나는 `code --list-extensions` 가 재고, 최신 판은 묻지 않는다(마켓플레이스 판을
#   따로 물을 손이 없다). 그래서 깔린 확장은 `upcheck` 이고, 그 묻기는 아래 한 호출(`--update-extensions`)이 한꺼번에 한다.
# ⚠ **`code` 를 못 쟀으면 확장도 못 잰 것이다** — 「안 선다」로 읽어 빨갛게 끝내지 않고 확장마다 안 한 걸음으로 남긴다(결정 0141 · 0145).
$extCodeRuns = if ($NoVsCode) { '' } else { Measure-Runs 'code' '--version' }
if ($NoVsCode) {
  Write-Host '  건너뜀 — VS Code 칸을 껐다 (확장은 VS Code 없이 설 자리가 없다)'
} elseif ($extCodeRuns -ne 'no') {
  # `code --version` 을 못 쟀으면 `Measure-Runs` 가 남긴 그 까닭(넘김 · 못 띄움 · 종료 값)이 확장마다의 까닭이다 — `Why` 를 비워
  #   `Add-UnmeasuredStep` 이 `Get-ProbeWhy` 로 찍게 한다.
  $extRead   = if ($extCodeRuns -eq 'yes') { Get-ExtVersions } else { @{ Vers = $null; Why = '' } }
  $extBefore = $extRead.Vers
  $extProbe  = if ($extCodeRuns -eq 'yes') { 'code --list-extensions --show-versions' } else { 'code --version' }
  $extActs   = @{}
  foreach ($x in $ExtPicks) {
    $xHas = if ($null -eq $extBefore) { 'unmeasured' } elseif ($extBefore.ContainsKey($x.Id)) { 'yes' } else { 'no' }
    $xVer = if ($xHas -eq 'yes') { $extBefore[$x.Id] } else { '' }
    $extActs[$x.Id] = Get-InstallAction $xHas $xVer '' $null $true ([bool]$NoUpgrade)
  }
  $extAfter  = $extBefore
  $extHave   = @($ExtPicks | Where-Object { $extActs[$_.Id] -eq 'upcheck' })
  if ($extHave.Count -gt 0) {
    Say-Busy "깔린 확장 $($extHave.Count)개" 'upcheck' @('code')
    $xl = [IO.Path]::GetTempFileName()
    $t0 = Get-Date
    $rc = Invoke-LoggedCapped 'code' @('--update-extensions') $xl $ExtUpdateCap
    $took = [int]((Get-Date) - $t0).TotalSeconds
    Remove-Item $xl, "$xl.err" -ErrorAction SilentlyContinue
    # 넘긴 것은 실패가 아니다 — 확장은 이미 깔려 있어 본일(세우기)이 안 깨지고, 못 올린 판은 VS Code 가 제 자동 갱신으로 올린다.
    #   그래서 `$Fails` 에 안 넣고 말만 하고 간다.
    if ($rc -eq -2) {
      Write-Host "  ! 확장 갱신이 ${ExtUpdateCap}초를 넘겨 거뒀다 — 깔린 판 그대로 간다 (VS Code 가 스스로 올린다)" -ForegroundColor Yellow
    }
    # 걸린 시간을 적는다 — 이 호출은 확장별 소요를 안 뱉어, 느렸을 때 뒤에 남는 자리가 이것뿐이다. 걸음 전체를 재는
    #   `Write-Elapsed` 로는 이 호출 몫이 안 갈린다.
    elseif ($took -ge $ExtUpdateSlow) {
      Write-Host "  (확장 갱신에 ${took}초 걸렸다 — 밀린 양이 많았다)" -ForegroundColor DarkGray
    }
    $extAfter = (Get-ExtVersions).Vers
  }
  if (-not $ExtPicks) { Write-Host '  고른 제품이 없어 확장을 안 깐다' }
  Install-Extension $ExtPicks $extActs $extBefore $extAfter $extProbe $extRead.Why
} else {
  Write-Host '  ! code 가 이 창의 PATH 에 없어 건너뛴다 — VS Code 설치부터 본다' -ForegroundColor Red
  $Fails.Add('VS Code 확장 (code 가 안 닿는다)')
}

} catch { Write-StepFault $_ }
Exit-Step 'extensions'

# ══ 걸음 「CLI」 ═══════════════════════════════════════════════════════════════════════════════
#   층 — 기계
#   하는 일 — 고른 제품의 CLI(npm · winget) · 사외 로그인 안내
#   앞에서 받는 것 — 「프로그램」의 Node · Node 신뢰
#   안 하는 것 — 사용자 환경변수. 맡기기 값은 「키와 값」이 심는다. 자리를 안 가리고 깔며, 회사 키로 물리나는 「회사 키의 다른
#     이름 둘」 · 「Codex · 안티그래비티 설정」 칸이 가른다

Enter-Step 'cli'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)
if (-not $CliPicks) { Write-Host '  고른 제품이 없어 CLI 를 안 깐다' }
# npm CLI 는 함께 넘긴다 — 할 일이 같은 것끼리 npm 한 번에 깐다(`Install-NpmCli` · PAISetup #35 C). winget CLI 는 하나씩이다.
$npmCliPicks = @($CliPicks | Where-Object { $_.Via -ne 'winget' })
if ($npmCliPicks.Count) { Install-NpmCli $npmCliPicks }
foreach ($c in @($CliPicks | Where-Object { $_.Via -eq 'winget' })) { Install-WingetCli $c.Id $c.Cmd $c.Label $c.Arg }

# 사외는 여기서 로그인 길을 댄다 — 프로그램은 섰고 자격만 사람 몫이라는 것을 한 줄로 둔다. 사내에서 심은 회사 연결이 남아 있으면 그
#   로그인이 안 서는데, 그 연결은 「사내 연결」 걸음의 「Codex · 안티그래비티 설정」 칸이 걷고 못 걷으면 그 칸이 제 줄을 세운다.
if (-not $inside) {
  Write-Host '  사외 — Codex 는 `codex login`(ChatGPT), 안티그래비티는 `agy` 첫 실행의 Google 로그인으로 쓴다 · 사내에서 심은 회사 연결은 「사내 연결」이 걷는다'
}
# Copilot CLI 는 따로 로그인하지 않고 gh 로그인을 쓴다(claude-config 결정 0137) — 그 로그인이 서 있나는 끝 검증의 gh 로그인
#   줄이 잰다(`Get-GhKeyringLines`).

} catch { Write-StepFault $_ }
Exit-Step 'cli'

# ══ 걸음 「키와 값」 ═══════════════════════════════════════════════════════════════════════════
#   층 — 환경
#   하는 일 — 맡기기 모델 값(agy · Codex — 맡기기 모델 표에서 · 안 세우는 맡기기는 우리 값을 걷는다) · Codex · Copilot 맡기기 값 ·
#     회사 키로 아는 값과 설치기 폴더의 회사 키 덩이 · 값 파일의 이름들(게이트웨이 키 · 남은 이름) · 회사 키의 다른
#     이름(안 세우는 이름의 회사 키는 걷는다) · 사외로 간 자리의 사내 잔재 걷기 · 심은 것의 장부와 장부로 걷기(표 · 값 파일에서 빠진
#     이름) · 워드의 PDF 변환 안내 끄기(워드가 깔린 PC) · 사외 Claude 구독 로그인
#   앞에서 받는 것 — 준비의 자리(`$ModelSite`) · 맡기기 조건 · 짐(`$KitSkills` · 우리 주소를 든 `$DistEnvFile`) · 값 파일, 「CLI」의
#     `claude`(구독 로그인). 사외 판은 홈 settings.json 의 env 를 읽기만 한다(회사 키 짝 — 「회사 키」 칸)
#   안 하는 것 — 도구 홈 파일 쓰기 · 사용자 PATH(마무리의 「사용자 범위 명령 자리」가 든다 — 뒤 걸음들이 그 폴더를 채운 뒤라야 한다)
#   ⚠ 「Claude 홈 설정」이 홈 settings.json 의 env 로 미는 것은 그 걸음 앞에서 심은 값(`$Planted`)에서 키와 맡기기 러너 값을 뺀
#     것뿐이다 — 심는 자리를 그 걸음 뒤로 옮기면 settings.json 이 바뀐다
Enter-Step 'keys'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)
# 맡기기 모델 — agy · Codex 러너가 고를 모델을 맡기기 모델 표(짐의 스킬 `agent-envelope` 폴더의 `models.conf`)에서 옮겨
#   사용자 환경변수로 심는다(claude-config 결정 0123). 자리 · 도구 · 무게마다 무엇을 대나와 그 까닭은 표가 들고, 여기는 이
#   자리(`$ModelSite`)의 줄을 러너의 자리 값으로 옮기기만 한다(`Read-ModelTable`). 표는 이 설치가 홈에 놓는 그 스킬의 것이다.
# 표를 못 읽으면 모델 값을 안 건드리고 빨갛게 끝낸다 — 말없이 지나가면 러너가 이전 값으로 돌고 설치는 초록이다.
# 맡기기를 안 세우는 판도 표를 읽는다 — 그 판은 `Remove-OurRunnerVars` 가 표의 값으로 앞 판이 심은 우리 값을 가려 걷고, 「Claude
#   홈 설정」이 같은 표로 settings.json 의 러너 사본을 가른다. 그 판에서 못 읽은 것은 노란 줄이다 — 심을 것이 없고 걷을 것만 못 가린다.
# ⚠ **다른 자리의 값은 우리가 심은 글자 그대로일 때만 걷는다**(`Remove-OtherSiteVars`).
$ModelTable = Read-ModelTable (Join-Path $KitSkills 'agent-envelope\models.conf')
if ($ModelTable.Why -and ($wantAgyDelegate -or $wantCcBg)) {
  Write-Host "  ! 맡기기 모델 표를 못 읽었다 — agy · Codex 모델 값을 안 건드렸다 ($($ModelTable.Why))" -ForegroundColor Red
  $Fails.Add("맡기기 모델 표 ($($ModelTable.Why))")
} elseif ($ModelTable.Why) {
  Write-Host "  ! 맡기기 모델 표를 못 읽었다 — 안 세우는 맡기기의 옛 모델 값을 못 가려 안 걷는다 ($($ModelTable.Why))" -ForegroundColor Yellow
}
# agy — 래퍼(스킬 `agy-background`)가 읽는다
$AgyModelVarsBySite = $ModelTable.Agy
$AgyModelVars       = $AgyModelVarsBySite[$ModelSite]
if ($wantAgyDelegate) {
  foreach ($k in $AgyModelVars.Keys) {
    if ([Environment]::GetEnvironmentVariable($k, 'User') -eq $AgyModelVars[$k]) {
      Write-Host "  $k — 이미 맞다"
    } else {
      Plant-Var $k $AgyModelVars[$k]
    }
  }
  Remove-OtherSiteVars $AgyModelVarsBySite $ModelSite
} else {
  # 안 세우는 맡기기 — 끈 기능의 값도 심은 손이 걷는다(우리 값 그대로인 것만 · 사람 값은 둔다)
  Remove-OurRunnerVars $AgyModelVarsBySite 'agy 맡기기를 안 세운다'
}

# Codex · Copilot — 위 `$CcBgVars`(이 자리의 것)에 표가 이 자리에 준 Codex 모델(맡기기 · 기본)을 더해 심는다. 래퍼(스킬
#   `codex-copilot-background`)가 읽는다. 두 자리가 다 드는 이름은 덮으면 끝이고, 한 자리에만 선 Codex 모델은 agy 와 같은 손이
#   걷는다.
foreach ($s in @($ModelTable.Codex.Keys)) {
  foreach ($k in $ModelTable.Codex[$s].Keys) { $CcBgVarsBySite[$s][$k] = $ModelTable.Codex[$s][$k] }
}
if ($wantCcBg) {
  foreach ($k in $CcBgVars.Keys) {
    if ([Environment]::GetEnvironmentVariable($k, 'User') -eq $CcBgVars[$k]) {
      Write-Host "  $k — 이미 맞다"
    } else {
      Plant-Var $k $CcBgVars[$k]
    }
  }
  Remove-OtherSiteVars $CcBgVarsBySite $ModelSite
} else {
  Remove-OurRunnerVars $CcBgVarsBySite 'Codex · Copilot 맡기기를 안 세운다'
}

# ── 맡기기 러너 값의 장부 — 표에서 빠지거나 `-` 가 된 이름 · 값이 바뀐 이름은 장부로 걷는다 (PAISetup #44 ⑤) ─────────────────
# 위 두 손은 오늘 표의 값으로만 우리 것을 가른다 — 표에서 빠진 이름과 표가 값을 바꾼 이름의 옛 값은 그 손이 못 본다. 장부 손이 그 몫을
#   든다: 오늘 표의 어느 자리 값과 같은 것은 위 손의 몫으로 두고(`-Owned`), 장부의 우리 값 그대로인 나머지를 걷는다. 심는 것은 위 고리가
#   이미 했다 — 장부 손은 그것을 적고, 대소문자만 다른 값을 맞춘다(그 고리는 대소문자를 안 가려 「이미 맞다」로 지난다). 표를 못 읽은
#   판은 안 걷는다 — 그 판의 선언이 반쪽이다.
# 사용자 환경을 읽고 쓰는 손 셋 — 「값 파일 이름의 장부」 칸도 쓴다. 심기 · 걷기는 `Plant-Var` · `Remove-UserVar` 가 들고 줄도 그 둘이 찍는다.
$Ledger = Read-PlantLedger $ClaudePlantLedger
$script:LedgerMigrating = $Ledger.Migrating   # 이 판이 장부를 처음 세우나 — 판에 한 번 정한다(`Read-RunLedger`)
if ($Ledger.Why) { Write-Host "  ! 장부를 못 읽었다 ($($Ledger.Why)) — 이번 판은 심기만 하고 장부로 걷지 않는다 ($ClaudePlantLedger)" -ForegroundColor Yellow }
$UserEnvGet    = { param($n) $v = [Environment]::GetEnvironmentVariable($n, 'User'); if ($v) { $v } else { $null } }
$UserEnvSet    = { param($n, $v) $f0 = $script:Fails.Count; Plant-Var $n $v; $script:Fails.Count -eq $f0 }
$UserEnvRemove = { param($n, $v) $f0 = $script:Fails.Count; Remove-UserVar $n '장부의 우리 값 · 이번 판은 안 심는다'; $script:Fails.Count -eq $f0 }
foreach ($g in @(@{ By = 'agy-model'; On = $wantAgyDelegate; Want = $AgyModelVars; Known = (Get-SiteValues @(, $AgyModelVarsBySite)) },
                 @{ By = 'ccbg';      On = $wantCcBg;        Want = $CcBgVars;     Known = (Get-SiteValues @(, $CcBgVarsBySite)) })) {
  $RunnerKnown = $g.Known
  $null = Sync-Planted -Ledger $Ledger -Place 'user-env' -At 'HKCU' -By $g.By -Want $(if ($g.On -and $g.Want) { $g.Want } else { [ordered]@{} }) `
            -Complete (-not $ModelTable.Why) -Get $UserEnvGet -Set $UserEnvSet -Remove $UserEnvRemove `
            -Owned { param($n, $c) @($RunnerKnown[$n]) -ccontains $c }
}

# ── 값 — 파일이 들면 읽고, 없으면 묻는다 ─────────────────────────────────────
# ⚠ **`#config-repo` 가 있어도 여기서 받는다.** 회사 키는 설치 창(또는 `install.env`)이 받고 이 파일이 심는다 — 저장소에 넘기면
#   설치 몸통이 없는 저장소를 쓰는 사람은 키가 어디에도 안 심긴다. 저장소가 드는 것은 사람에게 딸린 것(개인 키 · 형제 저장소)이다.
# 값 줄은 짐의 것이고, 사람이 넣은 키 · 주소만 얹는다(`Read-RunValues`).
$fromFile  = Read-RunValues $DistEnvFile $EnvFile $TypedGatewayUrl
if ($fromFile.Count -gt 0) { Write-Host "  install.env 가 $($fromFile.Count)개를 든다" }

# 게이트웨이를 쓰나 — **자리에서 난다**(「준비」의 `$inside`). 사내면 쓰고, 사외면 값 파일이 주소를 들어도 안 쓴다.
# ⚠ **주소로 가르지 않는다.** 사내인데 주소가 없는 판(집에서 처음 깐 노트북의 회사 회차)을 「게이트웨이를 안 쓰는 자리」로 읽으면
#   아래 「사외로 간 자리의 사내 잔재」 칸이 회사 PC 의 감시 작업 · 프록시를 걷고 구독 로그인도 안 서서, 아무 데도 못 붙은 채
#   끝난다(PAISetup #46 ①). 그 판은 아래 표 갈래가 주소를 묻고(콘솔) · 비었으면 「미입력」 빨강으로 끝난다. 감시 작업을 심는
#   문(`$wantProxy`)과 걷는 문(「사외로 간 자리의 사내 잔재」)이 이 한 사실을 묻는다.
# ⚠ **자리가 값보다 먼저다.** 배포본은 사내용으로 뽑혀 그 값 파일을 사외 PC 에서 돌리는 일이 난다 — 사내에 안 닿는 자리에 사내
#   주소를 심으면 안 닿는 곳을 가리킨 채 「설정됐다」로 보인다.
$useGateway = $inside
# 값 파일이 든 게이트웨이 값 — **버리기 전에 쥔다.** 아래 「사외로 간 자리의 사내 잔재」 칸이 「사용자 환경에 남은 이것이 우리
#   것인가」를 이 값으로 가른다 — 버린 뒤에는 남의 키와 우리 키를 못 갈라 걷어도 되는 것만 걷을 수 없다.
$ourGateway = @{}
if ($useGateway) {
  Write-Host "  사내다 — 게이트웨이를 쓴다"
} else {
  Write-Host "  사외다 — 게이트웨이를 안 쓴다"
  Write-Host '    구독 로그인으로 섭니다 (claude auth login)'
  # 값 파일이 든 사내 값을 버린다 — 안 버리면 아래 루프가 그대로 심는다.
  foreach ($v in $Vars) {
    if (-not $v.Gateway) { continue }
    if ($fromFile[$v.Name]) { $ourGateway[$v.Name] = $fromFile[$v.Name] }
    $fromFile.Remove($v.Name)
  }
}

# ── 회사 키 — 이 판이 회사 키로 아는 값 · 우리 게이트웨이 주소 · 설치기 폴더에 둔 덩이 (PAISetup #44 · #45) ─────────────────
# 걷는 자리(아래 「안 세우는 회사 키 이름」 · 「사외로 간 자리의 사내 잔재」 칸 · 「Claude 홈 설정」의 `env`)는 이름도 「이번 판에
#   심었나」도 「주소가 있나」도 아니라 값으로 우리 것을 가른다(`Test-CompanyKey`). 아는 값은 값 파일이 든 키 · 덩이의 키 · 게이트웨이를
#   쓰는 판의 사용자 환경 키와 이번에 심은 키 · 사외 판에서 우리 주소와 짝으로 선 키다(사용자 환경의 짝은 「사외로 간 자리의 사내 잔재」
#   칸이, 홈 settings.json 의 짝은 이 칸 끝이 더한다).
# 덩이(`$CompanyKeyBlob`)는 자리를 오가는 노트북이 키를 잃지 않게 둔다 — 키를 심은 사내 판이 맞추고, 사외 판이 사용자 환경에서 키를
#   걷기 바로 앞에 쓰고, 값 파일에도 환경에도 키가 없는 사내 판이 풀어 심는다. 이 사용자만 푸는 암호라 평문은 디스크에 안 닿는다.
$script:CompanyKeys = New-Object System.Collections.Generic.List[string]
$keyBlob = Read-CompanyKeyBlob $CompanyKeyBlob
if ($keyBlob.Why) {
  Write-Host "  ! 설치기 폴더에 둔 회사 키를 못 풀었다 ($($keyBlob.Why)) — 사내에서 키가 없으면 설치 창에 다시 넣는다" -ForegroundColor Yellow
}
Add-CompanyKey $fromFile['ANTHROPIC_AUTH_TOKEN']
Add-CompanyKey $ourGateway['ANTHROPIC_AUTH_TOKEN']
Add-CompanyKey $keyBlob.Key
if ($useGateway) { Add-CompanyKey ([Environment]::GetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'User')) }

# 우리 게이트웨이 주소(`Test-OurGatewayUrl` 이 견주는 것) — 이번 값 파일이 든 주소(사외면 버리기 전에 쥔 `$ourGateway`)와 이 판 짐의 값
#   파일(`$DistEnvFile`)이 든 주소다. 짐을 같이 보는 것은 사외 창이 주소를 안 넘기기 때문이다. 그 밖의 주소는 루프백이어도 사람 것이다.
$OurGatewayUrls = @(@($ourGateway['ANTHROPIC_BASE_URL'], (Read-EnvFile $DistEnvFile)['ANTHROPIC_BASE_URL']) | Where-Object { $_ })

# 사외 판은 홈 settings.json 의 `env` 에서 우리 주소와 짝으로 선 키(v1.x 가 그 파일에 민 짝)도 회사 키로 세운다 — 사용자 환경의 별칭을
#   가르는 「사외로 간 자리의 사내 잔재」 칸보다 앞에 알아야 한 판으로 걷힌다(그 파일을 걷는 「Claude 홈 설정」은 그 뒤에 돈다). 덩이가
#   비었으면 여기서 둔다 — 사용자 환경의 키가 이미 걷힌 PC 는 그 파일이 키를 든 마지막 자리다. 읽기만 하고, 못 읽으면 넘어간다(그 걸음이
#   빨갛게 문다).
if (-not $useGateway) {
  $homePair = $null
  try { $homePair = (Get-Content -LiteralPath (Join-Path $homeDir 'settings.json') -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json).env } catch { }
  if ($homePair -and $homePair.PSObject.Properties['ANTHROPIC_AUTH_TOKEN'] -and $homePair.PSObject.Properties['ANTHROPIC_BASE_URL'] -and
      (Test-OurGatewayUrl ([string]$homePair.ANTHROPIC_BASE_URL) $OurGatewayUrls)) {
    $pairKey = [string]$homePair.ANTHROPIC_AUTH_TOKEN
    Add-CompanyKey $pairKey
    if (-not $keyBlob.Key) { $null = Save-CompanyKeyBlob $keyBlob $CompanyKeyBlob $pairKey '걷기 전에 설치기 폴더에 이 사용자만 푸는 암호로 두었다 · 사내로 돌아오면 다시 심는다' }
  }
}

foreach ($v in $Vars) {
  $val = $fromFile[$v.Name]

  # 파일에 없는 비밀은 환경변수에 이미 심긴 값을 쓴다 — 사람이 매번 다시 칠 까닭이 없고, 자동 실행이 키 없는 값 파일로 서는 것도
  #   이 줄 덕이다. 묻는 것은 `Secret` 이다 — 환경에서 되읽는 것은 사람마다 다른 키뿐이고, 주소는 짐의 사실이라(`Read-RunValues`) 환경에 남은 옛 주소로 메우지 않는다.
  # ⚠ **같은 이름만 본다 — 별칭은 안 본다.** `OPENAI_API_KEY` · `GEMINI_API_KEY` 는 회사 키에서 파생된 사본이다(아래 「회사 키의
  #   다른 이름 둘」 칸이 한 방향으로만 심는다). 거꾸로 읽으면 제 OpenAI 키를 넣어 둔 사람의 값이 회사 키 자리에 심기는데, 칸이
  #   가려져 있어 무엇이 들어갔는지 아무도 못 본다.
  if (-not $val -and $v.Secret -and $useGateway) {
    $envVal = [Environment]::GetEnvironmentVariable($v.Name, 'User')
    if (-not $envVal) { $envVal = [Environment]::GetEnvironmentVariable($v.Name, 'Process') }
    if ($envVal) {
      $val = $envVal
      Write-Host "  $($v.Name) — 환경변수에 있는 값을 쓴다" -ForegroundColor Cyan
    } elseif ($v.Name -ceq 'ANTHROPIC_AUTH_TOKEN' -and $keyBlob.Key) {
      # 사외 판이 걷고 덩이로 둔 키 — 다시 묻지 않고 심는다. 별칭 둘은 아래 칸이 심은 키에서 다시 짓는다.
      $val = $keyBlob.Key
      Write-Host "  $($v.Name) — 설치기 폴더에 이 사용자만 푸는 암호로 둔 회사 키를 쓴다" -ForegroundColor Cyan
    }
  }

  # 게이트웨이를 안 쓰는 자리에서는 그쪽 이름을 아예 안 본다
  if ($v.Gateway -and -not $useGateway) { continue }
  # 사내 전용 이름도 같다 — 아래 「값 파일이 든 나머지 이름」 칸과 같은 문(`$InsideOnly`)을 묻는다
  if (-not $useGateway -and ($InsideOnly -contains $v.Name)) {
    if ($val) { Write-Host "  $($v.Name) — 안 심는다 (사외에서는 뜻이 없는 이름)" -ForegroundColor Yellow }
    continue
  }

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

# ── 값 파일이 든 나머지 이름 — **몸통이 모르는 것도 심는다** ────────────────
# 위 표(`$Vars`)는 「물을 것」이라 회사 공통 설정을 다 들지 않는다 — 표에 있는 것만 심으면 파일이 실어 보낸 나머지가 조용히
#   버려진다. 그래서 표를 안 보고 파일을 본다.
# ⚠ **여기에도 자리 게이트가 선다.** 위 표 갈래는 `Gateway` 표시로 사외를 거르지만 이 칸에는 그 표시가 없다 — 사외로 판정한
#   기계에 프록시 주소(`GOOGLE_GEMINI_BASE_URL` 등)를 심으면 프로그램은 멀쩡히 서고 나갈 때만 죽은 포트로 나간다. 가르는 것은
#   표시가 아니라 값이다(`Test-ProxyValue`) — 값 파일은 늘어나고 표는 안 늘어난다.
$known = $Vars | ForEach-Object { $_.Name }
foreach ($k in $fromFile.Keys) {
  if ($known -contains $k) { continue }
  $val = $fromFile[$k]
  if (-not $val) { continue }
  if (-not $useGateway -and (Test-ProxyValue $val)) {
    Write-Host "  $k — 안 심는다 (사외라 프록시가 안 선다: $val)" -ForegroundColor Yellow
    continue
  }
  if (-not $useGateway -and ($InsideOnly -contains $k)) {
    Write-Host "  $k — 안 심는다 (사외에서는 뜻이 없는 이름)" -ForegroundColor Yellow
    continue
  }
  Plant-Var $k $val
}

# ── 회사 키의 다른 이름 둘 — **한 번 받은 것을 이름만 바꿔 심는다** ─────────────
# 회사 키는 하나인데 읽는 이름이 셋이다 — Claude Code 는 `ANTHROPIC_AUTH_TOKEN`, Codex CLI 는 `config.toml` 의 `env_key` 가 가리키는
#   `OPENAI_API_KEY`, 안티그래비티(`agy`)는 `GEMINI_API_KEY`. 세 번 묻지 않고 한 번 받아 파생한다(결정 0041).
# ⚠ **필요한 것만 심는다.** 그 CLI 를 안 세우는 자리(사외)에 이 이름을 심으면, 같은
#   이름을 다른 뜻으로 쓰는 도구(구글 직결 키)가 회사 키를 집어 조용히 죽는다.
$KeyAliases = @(
  @{ Name='OPENAI_API_KEY'; Need='codex';  Tool='Codex' }
  @{ Name='GEMINI_API_KEY'; Need='gemini'; Tool='안티그래비티' }
)
if ($useGateway -and $Planted['ANTHROPIC_AUTH_TOKEN']) {
  # 심은 키를 회사 키로 세우고 덩이를 맞춘다 — 사외로 나가 사용자 환경에서 걷힌 뒤 돌아온 판이 이 덩이에서 받는다.
  Add-CompanyKey $Planted['ANTHROPIC_AUTH_TOKEN']
  $null = Save-CompanyKeyBlob $keyBlob $CompanyKeyBlob $Planted['ANTHROPIC_AUTH_TOKEN'] '설치기 폴더에 이 사용자만 푸는 암호로 두었다 · 사외에서 걷혀도 사내로 돌아오면 다시 심는다'
  foreach ($k in $KeyAliases) {
    if (-not $wantNeed[$k.Need]) { continue }
    Plant-Var $k.Name $Planted['ANTHROPIC_AUTH_TOKEN']
  }
  # ── 회사 키를 제치는 이름 하나 — **말은 하고 지우지는 않는다** (claude-config #62) ──
  # `GOOGLE_API_KEY` 가 남아 있으면 `agy` 가 회사 키를 제치고 그쪽을 집는다
  #   («Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY.») — 답은 오는데 게이트웨이가 아니라 구글에서 온다.
  # 지우지는 않는다 — 우리가 심은 이름이 아니라 구글 직결 키의 제 이름이라, 걷으면 그 사람의 다른 일이 죽는다(「사외로 간 자리의
  #   사내 잔재」 칸의 「남의 값은 안 걷는다」와 같은 자). 화면에 찍어 두어, 회사 키로 안 서는 사람이 열어 볼 자리를 남긴다.
  if ($wantNeed['gemini'] -and [Environment]::GetEnvironmentVariable('GOOGLE_API_KEY', 'User')) {
    Write-Host '  ! GOOGLE_API_KEY 가 사용자 환경에 있다 — 안티그래비티가 회사 키 대신 이것을 집는다' -ForegroundColor Yellow
    Write-Host '     구글 직결 키의 제 이름이라 설치기가 안 걷는다. 회사 게이트웨이로 쓰려면 손으로 걷는다 (시스템 환경 변수)'
  }
}

# ── 안 세우는 회사 키 이름 — **그 도구를 회사 키로 안 세우면 회사 키 사본을 걷는다** ────────────
# 위 칸은 필요한 이름에만 심어, 그 제품을 끄거나 회사 설정 틀(`#codex-config`)이 빠진 판에는 앞 판이 심은 사본이 그대로 남는다 —
#   남은 회사 키를 OpenAI · 구글이 정한 그 이름으로 그 회사에 바로 붙는 도구가 집는다. 우리 것인가는 값으로 가른다(`Test-CompanyKey`) —
#   사람이 그 이름에 둔 제 키는 두고 이름을 댄다. 사외 판은 아래 「사외로 간 자리의 사내 잔재」 칸이 든다(그 칸이 우리 주소와 짝인
#   키를 회사 키로 세운 뒤에 걷어야 한다).
if ($useGateway) {
  foreach ($k in $KeyAliases) {
    if ($wantNeed[$k.Need]) { continue }
    Remove-CompanyKeyCopy $k.Name "회사 키 사본 · 이번 판은 $($k.Tool) 를 회사 키로 안 세운다"
  }
}

# ── 홈 `settings.json` 에 안 미는 이름 — **키는 환경변수에만 산다** (PAISetup #2) ────────────
# ⚠ **목록을 손으로 적지 않는다.** 키는 하나인데 이름이 셋이라(위 「회사 키의 다른 이름 둘」), 손으로 적으면 넷째 이름이 느는 날
#   이 목록만 안 늘어 그 하나가 조용히 파일로 샌다. 표에서 파생한다 — 비밀이라고 표가 말한 것(`Secret`)과 그 다른 이름들(`$KeyAliases`)이다.
$SettingsEnvSkip = @($Vars | Where-Object { $_.Secret } | ForEach-Object { $_.Name }) +
                   @($KeyAliases | ForEach-Object { $_.Name })

# ── 사외로 간 자리의 사내 잔재 — **심은 자리마다 걷는 자가 있다** ───────────────
# 위 칸들은 이번 판에 심을 목록에서만 게이트웨이 이름을 빼서, 이미 `HKCU\Environment` 에 박힌 값은 안 건드린다 — 사내에서 깐
#   노트북을 사외에서 다시 돌리면 검증은 그 이름들을 빼고(끝 검증의 `if ($useGateway)`) [O] 인데, CLI 는 남은 `ANTHROPIC_BASE_URL`
#   을 물고 닿지 않는 루프백으로 나간다. 심은 자리마다 걷는 자가 있어야 한다는 「값 파일 이름의 장부」 칸의 규율을 여기 마저 쓴다.
# ⚠ **남의 값은 안 걷는다 — 우리 것이라는 근거가 설 때만 걷는다.** 같은 이름을 제 뜻으로 쓰는 사람이 있고(제 로컬 프록시와 그 키를
#   두는 사람도), 별칭 둘은 구글 · 오픈AI 직결 키의 이름이기도 하다.
#     · 주소 — 우리 주소와 글자까지 같을 때만(`Test-OurGatewayUrl` · `$OurGatewayUrls`). 루프백이라는 것은 근거가 아니다.
#     · 키와 별칭 둘 — 주소와 떼어 값으로 가른다(`Test-CompanyKey`). 우리 주소와 짝으로 선 키는 회사 키로 세운다 — 그 짝은 이
#       설치기의 게이트웨이 갈래가 함께 심었다. 그래서 주소가 이미 없는 판(사람이 주소만 걷었거나 앞 판이 키 걷기만 졌다)도 덩이 ·
#       값 파일의 키와 같으면 걷힌다.
#   근거가 안 서면(우리 주소가 아닌 주소와 그 짝의 키 · 덩이가 없는 PC 의 홀로 남은 키) 안 걷고 그 이름을 댄다 — 끝 검증이 [X] 로
#   남겨 조용히 지나가지는 않는다.
if (-not $useGateway) {
  Write-Host ''
  Write-Host '  사내 잔재' -ForegroundColor Cyan

  # 사내 전용 이름도 여기서 걷는다 — 「값 파일이 든 나머지 이름」 칸은 이번 판에 심을 목록에서만 빼서, 사내에서 한 번 깐 기계에
  #   박힌 값은 다시 깔아도 산다(「값 파일 이름의 장부」 칸이 든 그 병). 이 값들은 프로그램을 안 죽이고 화면만 좁혀 조용하다.
  foreach ($k in $InsideOnly) {
    if (-not (Test-OurInsideOnlyEntry $k $fromFile)) { continue }
    if (-not [Environment]::GetEnvironmentVariable($k, 'User')) { continue }
    Remove-UserVar $k
  }

  $oldUrl = [Environment]::GetEnvironmentVariable('ANTHROPIC_BASE_URL', 'User')
  $oldKey = [Environment]::GetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'User')
  $oursUrl = Test-OurGatewayUrl $oldUrl $OurGatewayUrls

  if (-not $oldUrl) {
    Write-Host '  ANTHROPIC_BASE_URL — 없다 (걷을 것이 없다)'
  } elseif (-not $oursUrl) {
    # 모르는 주소를 지우지 않되 말은 한다 — 이것이 살아 있으면 구독 로그인이 서 있어도 CLI 는 이쪽으로 나간다.
    Write-Host "  ! ANTHROPIC_BASE_URL 이 우리 것이 아니다 — 안 걷는다 ($oldUrl)" -ForegroundColor Yellow
    Write-Host '     구독 로그인으로 서려면 이 이름을 손으로 걷는다 (시스템 환경 변수)'
  } else {
    Remove-UserVar 'ANTHROPIC_BASE_URL'
  }

  if ($oursUrl) { Add-CompanyKey $oldKey }
  if ($oldKey -and (Test-CompanyKey $oldKey)) {
    # ⚠ **걷기 바로 앞에 덩이로 둔다** — 사용자 환경이 이 PC 에서 그 키를 든 마지막 자리라, 그냥 걷으면 사내로 돌아온 판이 다시 묻는다.
    $null = Save-CompanyKeyBlob $keyBlob $CompanyKeyBlob $oldKey '걷기 전에 설치기 폴더에 이 사용자만 푸는 암호로 두었다 · 사내로 돌아오면 다시 심는다'
    Remove-UserVar 'ANTHROPIC_AUTH_TOKEN'
  } elseif ($oldKey) {
    Write-Host '  ! ANTHROPIC_AUTH_TOKEN 이 우리 키인지 못 가린다 — 안 걷는다' -ForegroundColor Yellow
    Write-Host '     구독 로그인으로 서려면 이 이름을 손으로 걷는다 (시스템 환경 변수)'
  }
  foreach ($k in $KeyAliases) { Remove-CompanyKeyCopy $k.Name '사외라 안 쓴다 · 회사 키 사본' }

  # 표 밖의 프록시 주소도 여기서 걷는다 — 「값 파일이 든 나머지 이름」 칸이 이번 판에 안 심어도 사내에서 한 번 깐 기계에는 그 값이
  #   남는다. 걷어도 되나는 이름을 손으로 들지 않고 `Test-OurProxyEntry` 가 판다 — 두 물음(무엇을 · 누구 것인지)이 다 거기 있고,
  #   `settings.json` 칸도 같은 문을 부른다.
  foreach ($k in $fromFile.Keys) {
    if ($known -contains $k) { continue }        # 표 갈래는 바로 위에서 이미 들었다
    if (Test-OurProxyEntry $k ([Environment]::GetEnvironmentVariable($k, 'User')) $fromFile) { Remove-UserVar $k }
  }

  # ⚠ **감시 작업과 기존 자동시작을 먼저 걷는다.** 작업 스케줄러의 감시 작업(`$ProxyTaskName`)을 먼저 멈추고 지워야, 프록시
  #   프로세스를 죽였을 때 감시자가 다시 되살리지 않는다.
  try {
    if (Test-ScheduledTaskExists $ProxyTaskName) {
      Stop-ScheduledTask -TaskName $ProxyTaskName -ErrorAction SilentlyContinue
      Unregister-ScheduledTask -TaskName $ProxyTaskName -Confirm:$false -ErrorAction Stop
      Write-Host "  감시 작업 — 걷었다 (작업 스케줄러 · $ProxyTaskName)" -ForegroundColor Green
    }
  } catch {
    Write-Host "  ! 감시 작업 걷기 실패 — $(Say-Why $_)" -ForegroundColor Red
    $Fails.Add('사내 잔재 (감시 작업 걷기)')
  }

  $runKeyPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
  try {
    if (Get-ItemProperty -Path $runKeyPath -Name $ProxyRunName -ErrorAction SilentlyContinue) {
      Remove-ItemProperty -Path $runKeyPath -Name $ProxyRunName -ErrorAction Stop
      Write-Host "  기존 자동시작 — 걷었다 (HKCU Run · $ProxyRunName)" -ForegroundColor Green
    }
  } catch {
    Write-Host "  ! 기존 자동시작 걷기 실패 — $(Say-Why $_)" -ForegroundColor Red
    $Fails.Add('사내 잔재 (자동시작 걷기)')
  }

  $oldProxyDir = Join-Path $env:LOCALAPPDATA $ProxyDirName
  if (Test-Path -LiteralPath $oldProxyDir) {
    Remove-Item -LiteralPath $oldProxyDir -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $oldProxyDir) {
      # 못 지운 것을 지웠다고 안 한다 — 도는 프록시가 제 로그를 잡고 있으면 폴더가 남는다. 가리키는 주소와 자동시작은 걷혔으니
      #   다음 로그인부터는 안 뜬다.
      Write-Host "  ! 프록시 사본을 못 지웠다 (도는 중일 수 있다) — $oldProxyDir" -ForegroundColor Yellow
      Write-Host '     다음 로그인부터는 안 뜬다 — 지금 끄려면 작업 관리자에서 pythonw 를 끝낸다'
    } else {
      Write-Host "  프록시 사본 — 걷었다 ($oldProxyDir)" -ForegroundColor Green
    }
  }
}

# ── 값 파일 이름의 장부 — 값 파일 · 표에서 빠진 이름은 장부로 걷는다 (PAISetup #44 ⑧) ─────────────────
# 심기는 더하기만 한다 — 진본이 이름 하나를 걷어도 한 번 깐 기계에는 그 값이 남아, 설치는 초록인데 어긋남은 그 사람 화면에서만 보인다.
#   그래서 이번 판에 심은 이름(`$Vars` · 값 파일의 이름 — 키와 그 별칭은 값으로 가르는 몫이라 장부 밖)을 장부에 적고, 장부에만 남은 이름을
#   걷는다 — 장부의 우리 값 그대로일 때만이고, 사람이 바꾼 값은 두고 이름을 댄다. 홈 settings.json 쪽은 「Claude 홈 설정」의 env 칸이 같은 자로 걷는다.
# 사외 판에서 오늘 짐의 값 파일이 들었는데 이 자리가 안 심는 이름(게이트웨이 · 프록시 · 사내 전용)은 위 「사외로 간 자리의 사내 잔재」 칸이
#   값으로 가른다 — 장부는 기록만 잇는다(`-Owned`). 짐의 값 파일이 없는 판은 걷지 않는다 — 그 판의 선언이 반쪽이다.
# ⚠ **우리 것은 짐의 값 파일이 든 값 그대로 심은 이름뿐이다** — 물음에 사람이 친 값(`Read-Host` · 창이 넘긴 주소)은 사람 값이라 장부에 안
#   적는다. 적으면 그 이름이 없는 값 파일로 도는 다음 판(`-Yes` · 자동 실행)이 그 값을 우리 것으로 걷는다. 그 이름은 「Claude 홈 설정」의
#   env 로도 안 민다(`$HumanValueNames`) — 밀면 우리가 적지 않은 사본이 그 파일에 남아 다음 판의 「홀로 있다」가 판마다 문다.
# 「Claude 홈 설정」도 이 값들(`$DistNames` · `$DistComplete` · `$HumanValueNames`)로 settings.json 의 env 를 가른다.
$DistComplete    = Test-Path -LiteralPath $DistEnvFile -PathType Leaf
$DistValues      = Read-EnvFile $DistEnvFile
$DistNames       = @($DistValues.Keys)
$valueNames      = @($Vars | ForEach-Object { $_.Name }) + @($fromFile.Keys)
$valuesWant      = [ordered]@{}
$HumanValueNames = @()
foreach ($k in @($Planted.Keys | Sort-Object)) {
  if ($valueNames -notcontains $k -or $SettingsEnvSkip -contains $k) { continue }
  if ($DistValues.ContainsKey($k) -and (Test-SameText $DistValues[$k] $Planted[$k])) { $valuesWant[$k] = $Planted[$k] } else { $HumanValueNames += $k }
}
$null = Sync-Planted -Ledger $Ledger -Place 'user-env' -At 'HKCU' -By 'values' -Want $valuesWant -Complete $DistComplete `
          -Get $UserEnvGet -Set $UserEnvSet -Remove $UserEnvRemove `
          -Owned { param($n, $c) (-not $useGateway) -and ($DistNames -contains $n) -and -not $Planted.ContainsKey($n) }
$null = Save-PlantLedger $Ledger

# ── 워드의 PDF 변환 안내 — **워드가 깔린 PC 면 자리 · 고른 제품과 상관없이 끈다** ────────────────
# 왜 끄나 · 무엇이 바뀌나는 라이브러리의 「워드의 PDF 변환 안내」 칸이 든다. 판은 깔린 워드에서 읽고(`Get-WordVersions`), 끝 검증이
#   같은 판 목록(`$WordVersions`)으로 되읽는다 — 묻는 것은 한 번이다.
# 설치 창에 칸을 두지 않는다 — 고를 것을 늘리지 않고, 심었으면 기록 한 줄이 그 뜻(사람이 PDF 를 열 때도 안내가 안 뜬다)을 밝힌다.
$WordPdfQuiet = @{ Office = 'HKCU:\Software\Microsoft\Office'; Name = 'DisableConvertPdfWarning' }
$WordVersions = @(Get-WordVersions)
if (-not $WordVersions.Count) {
  Write-Host '  워드 PDF 변환 안내 — 워드가 없어 안 건드린다'
} else {
  $wordDid  = @(Set-WordPdfQuiet $WordVersions)
  $wordSet  = @($wordDid | Where-Object { $_.Did -eq 'set' }  | ForEach-Object { $_.Version })
  $wordKept = @($wordDid | Where-Object { $_.Did -eq 'kept' } | ForEach-Object { $_.Version })
  $wordSaid = @()
  if ($wordSet.Count)  { $wordSaid += "껐다 ($($wordSet -join ' · '))" }
  if ($wordKept.Count) { $wordSaid += "이미 꺼져 있다 ($($wordKept -join ' · '))" }
  if ($wordSet.Count) {
    Write-Host ('  워드 PDF 변환 안내 — ' + ($wordSaid -join ' · ') +
                ' — DRM 스킬이 숨은 워드로 PDF 를 열다 그 창에 갇히지 않게. 사람이 PDF 를 워드로 열 때도 그 안내가 더는 안 뜬다') -ForegroundColor Green
  } elseif ($wordKept.Count) {
    Write-Host ('  워드 PDF 변환 안내 — ' + ($wordSaid -join ' · '))
  }
  foreach ($wordFail in @($wordDid | Where-Object { $_.Did -eq 'failed' })) {
    Write-Host "  ! 워드 PDF 변환 안내 끄기 실패 ($($wordFail.Version)) — $(Say-Why $wordFail.Err)" -ForegroundColor Red
    $Fails.Add("워드 PDF 변환 안내 끄기 ($($wordFail.Version))")
  }
}

# ── 사외 Claude 구독 로그인 — **저장소와 세션 훅에 매지 않는다** ────────────
# 로그인은 클론한 저장소의 일이 아니다 — 저장소 칸을 비운 사람도 사외에서는 Claude CLI 자체의 자격이 필요하다. 세션 훅은 로그인한
#   Claude 세션이 열려야 돌므로 거기 두면 순서가 뒤집힌다. 비영속 VDI 가 로그인마다 부르는 이 설치기가 든다.
# 기존 로그인을 먼저 재고, 비었을 때만 브라우저 OAuth 를 띄운 뒤 최대 180초 동안 다시 잰다. 사람이 안 누르는 것도 선택이라 시간
#   넘김을 설치 실패로 세지 않는다.

$claudeLoggedIn = $false
if ($offsite) {
  Write-Host ''
  Write-Host '  Claude 구독 로그인' -ForegroundColor Cyan
  $loginTimedBefore = $script:ProbeTimedOut.Count
  if (-not (Test-Runs 'claude' '--version')) {
    Write-Host '  ! claude CLI 가 안 닿아 로그인을 못 띄운다 — 위 CLI 설치를 본다' -ForegroundColor Yellow
  } elseif (Test-ClaudeLoggedIn) {
    $claudeLoggedIn = $true
    Write-Host '  이미 서 있다 (loggedIn=true)'
  } elseif ($script:ProbeTimedOut.Count -gt $loginTimedBefore) {
    # ⚠ **못 쟀으면 로그인 창을 안 띄운다** — 로그인이 선 PC 에 브라우저를 띄우게 된다(결정 0141 · 아래 gh 칸과 같은 규율).
    Write-Host '  ! 로그인이 섰나를 못 쟀다 — 그 물음이 울타리 안에 안 끝났다 · 브라우저를 안 띄운다' -ForegroundColor Yellow
    Write-Host '     새 터미널에서 claude auth status 로 보고, 비었으면 claude auth login'
  } elseif ($NightRun) {
    Write-Host '  ! 밤 자동 실행이라 로그인 브라우저를 안 띄운다 — 다음 로그온 · 설치 창이 띄운다' -ForegroundColor Yellow
  } elseif (-not (Test-Reach 'claude.ai:443')) {
    # 닿는지 먼저 잰다 — 막힌 자리에서 3분을 서 있지 않는다. 로그인은 브라우저 콜백으로 끝나, 그 페이지에 못 닿으면 CLI 는 죽지
    #   않고 기다려 아래 루프의 `HasExited` 조기 탈출이 안 걸린다. 닿는다고 열린다는 보장은 없지만 못 닿으면 확실히 못 연다 —
    #   그 한쪽만으로 3분을 아낀다. 막혔다고 실패로 안 센다 — 로그인은 사람이 안 눌러도 되는 자리다.
    Write-Host '  ! claude.ai 에 못 닿는다 — 브라우저를 안 띄우고 지나간다 (회선이 막았다)' -ForegroundColor Yellow
    Write-Host '     닿는 자리에서 새 터미널에 claude auth login'
  } else {
    Write-Host '  구독 계정 로그인 브라우저를 엽니다 — 눌러 주세요 (최대 180초)' -ForegroundColor Yellow
    try {
      # PowerShell 에서 `claude`는 npm 이 만든 `claude.ps1`이 먼저 잡히지만, cmd 는
      # 그 파일을 실행할 수 없다. 같은 자리의 cmd shim 을 정확히 고른다.
      $cc = Get-Command claude.cmd -ErrorAction Stop
      # 설치 프로세스는 콘솔이 없고 stdin 도 NUL 이다. 로그인은 stdin 이 아니라
      # 브라우저 콜백으로 끝나므로 숨은 cmd 자식으로 띄워도 선다.
      $cmdArgs = '/d /s /c ""' + $cc.Source + '" auth login"'
      $login = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\cmd.exe') `
                 -ArgumentList $cmdArgs -WindowStyle Hidden -PassThru
      # ⚠ **180초는 끝 시각으로 센다 — 도는 횟수로 세지 않는다.** 한 번 재는 데 울타리(`$ProbeCap`)까지 걸릴 수 있어,
      #   횟수에 제 쉬는 틈만 더해 세면 「최대 180초」가 그 곱으로 분을 넘긴다. 끝 시각을 넘긴 뒤에는 더 안 재므로
      #   넘는 몫은 한 번의 재기와 아래 마지막 재기뿐이다(결정 0141).
      $loginStart = Get-Date
      $loginEnd   = $loginStart.AddSeconds(180)
      $nextSay    = 15
      while ((Get-Date) -lt $loginEnd) {
        Start-Sleep -Seconds 5
        if (Test-ClaudeLoggedIn) { $claudeLoggedIn = $true; break }
        if ($login.HasExited) { break }
        $elapsed = [int]((Get-Date) - $loginStart).TotalSeconds
        if ($elapsed -ge $nextSay) {
          Say-Busy 'Claude 구독 로그인' 'wait' @("${elapsed}초")
          $nextSay += 15
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

} catch { Write-StepFault $_ }
Exit-Step 'keys'

# ══ 걸음 「사내 연결」 ═════════════════════════════════════════════════════════════════════════
#   층 — 환경
#   하는 일 — 로컬 프록시와 그 감시 작업 · Codex · agy 회사 설정. 게이트웨이를 안 쓰는 자리에서는 사내에서 심은 Codex · agy 회사
#     연결을 걷는다
#   앞에서 받는 것 — 「키와 값」이 심은 주소 · 키(`$Planted`) · 게이트웨이를 쓰나(`$useGateway`) · 회사 설정 자리와 그 자
#     (`$CodexCfg` · `$AgyCfg` · `$CodexCfgMerge` · `$AgyProvider`)
#   안 하는 것 — Claude 홈 · 스킬
Enter-Step 'site'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)
Assert-StepsDone 'keys'   # 자리(`$useGateway`)와 심은 주소 · 키(`$Planted`)로 회사 설정을 심고 걷는다
# ── 로컬 프록시 — **사내에서 Claude 와 안티그래비티가 지나는 문** (결정 0041) ─────────────
# 왜 프록시인가 — 게이트웨이가 Opus 5 에서 assistant prefill 을 400 으로 거절하고, 안티그래비티는 곁 호출에 게이트웨이에 없는 모델
#   이름을 못박아 둔다. 둘 다 클라이언트 파일을 못 고치는 자리라 사이에 한 겹을 둔다. 프록시가 무엇을 고치고 무엇은 안 건드리는지는
#   그 폴더의 README 가 든다(`posco/pgpt-proxy/`).
# 프록시는 로그 · pid 를 제 곁에 쓰므로 홈 사본(「공용 자산」 걸음이 까는 `~/.claude/posco/`)에서 바로 띄우지 않고 실행 폴더로
#   복사해 띄운다. 로그인마다 띄우는 것은 작업 스케줄러의 감시 작업(`$ProxyTaskName`)이고, 사용자 Run 키 등록은 걷는다.
# ⚠ **이미 도는 것을 함부로 안 죽인다.** 동료 설치본이 같은 프록시를 같은 포트에 띄워 둔 PC 가 있다. `/health` 의 판이 이 판
#   이상이면 그대로 쓰고, 낡았으면 그 포트를 잡은 파이썬만 끄고 새로 띄운다.
# 포트 · 주소는 심은 `ANTHROPIC_BASE_URL` 에서 판다 — 파일에 못박힌 18901 을 여기 또 적으면 사본이다.
# 문은 여러 번 두드린다 — 게이트웨이가 유휴 keep-alive 연결을 조용히 닫아 두면 프록시가 그 위에 쓰다 `RemoteDisconnected` 를 맞고
#   스스로 502 를 내고, 그쪽 재시도(`opus5_proxy.py` 의 `range(2)`)는 새로 집은 연결도 죽어 있으면 그대로 나온다. 단발로 재면
#   상류의 운이 설치 판정이 된다.
$DoorTries = 3                          # 문을 두드리는 횟수 — 상류가 끊은 것만 다시 묻는다
$DoorGapMs = 700                        # 사이 쉼 — 죽은 연결이 풀에서 빠질 만큼

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
      # 주소가 루프백이 아니면 프록시를 띄워도 아무도 안 지난다 — 세우지 않고 말한다.
      Write-Host "  ! ANTHROPIC_BASE_URL 이 루프백이 아니다 ($baseUrl) — 프록시를 안 세운다" -ForegroundColor Yellow
      Write-Host '     프록시를 지나려면 값 파일의 주소를 127.0.0.1 로 둔다 (결정 0041)'
    } else {
      $proxyHealthUrl = "http://$($u.Host):$($u.Port)/health"
      $pyw = Get-RealPythonW
      if (-not $pyw -or -not (Test-Path -LiteralPath $pyw)) {
        Write-Host '  ! pythonw.exe 를 못 찾았다 — 위 「프로그램」 걸음의 파이썬 설치부터 본다' -ForegroundColor Red
        $Fails.Add('로컬 프록시 (파이썬이 없다)')
      } else {
        $proxyDir  = Join-Path $env:LOCALAPPDATA $ProxyDirName
        $proxyPath = Join-Path $proxyDir $ProxyFile
        $ourPair = Get-ProxyVer (Get-Content -LiteralPath $proxySrc -Raw -Encoding UTF8)
        $ourVer = '{0}.{1}' -f $ourPair[0], $ourPair[1]
        $watchdogSrc = Join-Path (Split-Path $proxySrc -Parent) 'watchdog.ps1'
        $watchdogPath = Join-Path $proxyDir 'watchdog.ps1'

        # ⚠ **판을 쓰기 앞에 견준다** — 실행 폴더에 둘 것은 그 폴더의 파일과 이 짐의 것 가운데 새 판이다. 견주기 전에 베끼면, 더 옛
        #   짐(남은 zip · 옛 바탕화면 폴더)을 직접 돌린 PC 에서 실행 폴더가 옛 판으로 덮여 감시자가 다음에 띄우는 것이 옛 판이 된다.
        #   도는 판은 끌지만 가른다 — 실행 폴더에 남을 판보다 낡았을 때만 끄고 그 판으로 새로 띄운다. 도는 판이 더 새로워도 실행 폴더는
        #   이 가름대로 둔다(감시자가 다시 띄울 것은 실행 폴더의 파일이다). 프록시와 감시자는 한 짐에서 온 짝이라 함께 둔다 — 실행 폴더의
        #   판을 두는 판은 감시자가 없을 때만 이 짐의 것을 놓는다.
        $keepPair = $null
        if (Test-Path -LiteralPath $proxyPath -PathType Leaf) {
          $diskPair = $null
          try { $diskPair = Get-ProxyVer (Get-Content -LiteralPath $proxyPath -Raw -Encoding UTF8) } catch { $diskPair = $null }
          if ($diskPair -and (($diskPair[0] -gt $ourPair[0]) -or (($diskPair[0] -eq $ourPair[0]) -and ($diskPair[1] -gt $ourPair[1])))) {
            $keepPair = $diskPair
          }
        }
        $setPair = if ($keepPair) { $keepPair } else { $ourPair }
        $setVer  = '{0}.{1}' -f $setPair[0], $setPair[1]
        $up = Get-ProxyHealth $proxyHealthUrl
        $start = $true
        if ($up) {
          # 도는 판이 낸 `version` — `15.4` 꼴이거나, 이전 프록시 판의 정수 하나다. 둘 다 이 자리가 받는다.
          $runUp = 0; $runOurs = 0
          $runVer = [string]$up.version
          $rm = [regex]::Match($runVer, '^(\d+)(?:\.(\d+))?$')
          if ($rm.Success) {
            $runUp = [int]$rm.Groups[1].Value
            if ($rm.Groups[2].Success) { $runOurs = [int]$rm.Groups[2].Value }
            else { $runUp = 0 }   # 정수 한 칸은 이 축의 값이 아니다 — 갈아 끼운다
          }
          $newer = ($runUp -gt $setPair[0]) -or (($runUp -eq $setPair[0]) -and ($runOurs -ge $setPair[1]))
          if ($newer) {
            Write-Host "  이미 돈다 — v$runVer · 그대로 쓴다"
            $start = $false
          } else {
            Write-Host "  낡은 프록시 v$runVer 이 돈다 — 끄고 v$setVer 로 새로 띄운다"
            Stop-ProxyOnPort $u.Port $ProxyFile
          }
        }
        New-Item -ItemType Directory -Path $proxyDir -Force | Out-Null
        if ($keepPair) {
          Write-Host "  실행 폴더 — $proxyDir (실행 폴더의 판 v$setVer 이 이 짐의 v$ourVer 보다 새로워 안 덮었다)"
          if (-not (Test-Path -LiteralPath $watchdogPath) -and (Test-Path -LiteralPath $watchdogSrc)) {
            Copy-Item -LiteralPath $watchdogSrc -Destination $watchdogPath -Force
          }
        } else {
          Copy-Item -LiteralPath $proxySrc -Destination $proxyPath -Force
          if (Test-Path -LiteralPath $watchdogSrc) {
            Copy-Item -LiteralPath $watchdogSrc -Destination $watchdogPath -Force
          }
          Write-Host "  실행 폴더 — $proxyDir (v$ourVer)"
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

        # 기존 HKCU\Run\PGPTProxy 일회성 등록은 제거하고, 작업 스케줄러 감시 작업으로 승격한다.
        $runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
        try {
          if (Get-ItemProperty -Path $runKey -Name $ProxyRunName -ErrorAction SilentlyContinue) {
            Remove-ItemProperty -Path $runKey -Name $ProxyRunName -ErrorAction SilentlyContinue
            Write-Host "  기존 자동시작 — 걷었다 (HKCU Run · $ProxyRunName)"
          }
        } catch { }

        try {
          # ── 이 감시자는 **창을 받을 자리 없이** 선다 ──────────────────────────────
          # ⚠ **`-WindowStyle Hidden` 은 이 자리에서 안 먹는다 — 숨기지 않고 창이 날 자리를 없앤다(`S4U`).** `powershell.exe` 는
          #   콘솔 프로그램이라 띄우는 자리에 콘솔이 붙고, 로그온 와중에는 숨기기가 그 붙임을 못 따라잡는다. `S4U` 는 그 세션에
          #   데스크톱이 없어 콘솔이 붙을 데가 없다(부팅 라인 `AtelierServer` 가 같은 꼴로 돈다).
          # ⚠ **창 핸들을 세어 재지 않는다.** 콘솔 창은 그 프로세스의 `MainWindowHandle` 로 안 올라오는 자리가 있어, 창 집합의
          #   차이로 보면 보이는 창이 떠 있는데도 「새 창 없음」이 나온다. 재려면 자식에게 `GetConsoleWindow` · `IsWindowVisible` 을
          #   직접 묻는다.
          # 이 감시자는 화면에 쓸 것이 없다 — 5초마다 프록시 생존만 보고 사유는 `watchdog.log` 에 적는다. 창이 남으면 내용 없이 안
          #   닫히는 창이 되어, 로그아웃까지 끝나기를 기다리는 창으로 읽힌다.
          $action = New-ScheduledTaskAction -Execute "powershell.exe" `
                      -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$watchdogPath`" -ProxyPath `"$proxyPath`" -PythonPath `"$pyw`""
          $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
          $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited
          $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
                        -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)

          Register-ScheduledTask -TaskName $ProxyTaskName -Action $action -Trigger $trigger `
                                 -Principal $principal -Settings $settings `
                                 -Description "PGPT proxy watchdog supervisor" -Force | Out-Null
          # ⚠ **이미 도는 회차를 거절하는 것은 결함이 아니다 — 그 코드를 보고 작업을 다시 걸지 않는다.** 이 작업은 수명이 무한
          #   (`ExecutionTimeLimit` 0)이고 겹침 정책이 `IgnoreNew` 라, 앞 회차가 사는 중에 부르면 「요청을 거부했습니다」
          #   (`0x800710E0`)가 마지막 결과로 남는다 — 규칙대로 물러난 것이고 감시자는 멀쩡히 돈다.
          Start-ScheduledTask -TaskName $ProxyTaskName -ErrorAction SilentlyContinue
          Write-Host "  감시 작업 — 로그인마다 창 없이 띄우도록 걸고 시작했다 (작업 스케줄러 · $ProxyTaskName)" -ForegroundColor Green
        } catch {
          Write-Host "  ! 감시 작업 스케줄러 등록 실패 — $(Say-Why $_)" -ForegroundColor Red
          $Fails.Add('로컬 프록시 (감시 작업)')
        }
      }
    }
  }
}

# ── Codex · 안티그래비티 설정 — **Codex 는 틀에서 파생한다** (결정 0041 · 0136) ─────────────
# 값을 여기 안 적는다 — 값 파일이 가리키는 틀(`#codex-config`)이 회사가 실제로 쓰는 설정의 사본이라, 틀을 고치면 설치가 따라온다.
# ⚠ **사람 것을 안 덮는다.** Codex 는 틀의 자리만 틀의 값으로 맞춘다(씨앗의 `codex-config-merge.py` — 무엇을 어떻게
#   맞추나는 그 머리말이 든다). 그 파일에는 Codex 가 적는 훅 · 폴더 신뢰와 사람 키도 살아, 통째로 갈면 그것이 사라진다.
#   파일이 없을 때만 틀을 그대로 쓴다.
# ⚠ **문에 두 제품을 다 적는다 — 안티그래비티가 이 칸 안에 산다.** 문이 Codex 만 물으면 안티그래비티만 켠
#   자리에서 칸이 통째로 건너뛰어지는데, 끝의 검증은 `$wantAgy` 로 따로 물어 그 항목이 늘 빨갛게 끝난다.
# 게이트웨이를 안 쓰는 자리는 사내에서 심은 연결을 걷는다 — 아래 `elseif` 갈래가 까닭을 든다.
if ($useGateway -and ($wantCodex -or $wantAgy)) {
  Write-Host ''
  # 제목은 이번에 실제로 서는 것만 든다 — 안 켠 제품 이름을 부르면 그것도 깔린 줄로 읽힌다.
  $cfgWho = @()
  if ($wantCodex)  { $cfgWho += 'Codex' }
  if ($wantAgy)    { $cfgWho += '안티그래비티' }
  Write-Host ('  ' + ($cfgWho -join ' · ') + ' 설정') -ForegroundColor Cyan
  $noBom = New-Object Text.UTF8Encoding($false)
  if ($wantCodex) {
    $src = Join-Path $Here $codexTpl
    $dst = $CodexCfg
    # python 은 병합기를 부를 갈래에서만 세 값으로 묻는다 — 못 잰 것을 「python 없음」 빨강으로 읽지 않는다(결정 0141)
    $cmPython = if ((Test-Path -LiteralPath $src) -and (Test-Path -LiteralPath $dst) -and (Test-Path -LiteralPath $CodexCfgMerge)) { Measure-Runs 'python' '--version' } else { '' }
    if (-not (Test-Path -LiteralPath $src)) {
      Write-Host "  ! Codex 틀이 이 폴더에 없다 — $codexTpl" -ForegroundColor Red
      $Fails.Add('Codex 설정 (틀이 없다)')
    } elseif (-not (Test-Path -LiteralPath $dst)) {
      $w = Write-FileSafely $dst ($noBom.GetBytes([string](Get-Content -LiteralPath $src -Raw -Encoding UTF8))) $null
      if ($w.Did -ceq 'written') { Write-Host '  Codex config.toml — 틀로 썼다 (키는 파일이 아니라 OPENAI_API_KEY 에서 읽는다)' -ForegroundColor Green }
      elseif ($w.Did -ceq 'raced' -or $w.Did -ceq 'overrun' -or $w.Did -ceq 'linked') { Write-Host "  ! Codex config.toml — $($w.Why) · 그 글을 둔다 (다음 판이 틀의 자리를 맞춘다)" -ForegroundColor Yellow }
      else { Write-Host "  ! Codex config.toml — 틀로 못 썼다 ($($w.Why))" -ForegroundColor Red; $Fails.Add('Codex 설정 (틀로 못 썼다)') }
    } elseif (-not (Test-Path -LiteralPath $CodexCfgMerge)) {
      Write-Host "  ! Codex config.toml — 틀 병합기가 이 폴더에 없어 안 건드렸다 ($CodexCfgMerge)" -ForegroundColor Red
      $Fails.Add('Codex 설정 (틀 병합기가 없다)')
    } elseif ($cmPython -eq 'unmeasured') {
      Add-UnmeasuredStep 'Codex config.toml 틀 맞추기' 'python --version' '맞추지도 건너뛰지도 않았다'
    } elseif ($cmPython -ne 'yes') {
      Write-Host '  ! Codex config.toml — python 이 안 서서 틀을 못 맞췄다 (안 건드렸다)' -ForegroundColor Red
      $Fails.Add('Codex 설정 (python 없음)')
    } else {
      $cmLog = [IO.Path]::GetTempFileName()
      $cmRc = Invoke-Logged 'python' @('-X', 'utf8', $CodexCfgMerge, '--config', $dst, '--template', $src) $cmLog
      $cmOut = @(Get-Content -LiteralPath $cmLog -Encoding UTF8 -ErrorAction SilentlyContinue |
                 ForEach-Object { "$_".Trim() } | Where-Object { $_ })
      if ($cmRc -ne 0) {
        Write-Host '  ! Codex config.toml — 틀을 못 맞췄다 · 파일은 그대로다. 병합기가 뱉은 끝 줄:' -ForegroundColor Red
        Show-Log $cmLog
        $Fails.Add('Codex 설정 (틀 병합 실패)')
      } elseif ($cmOut -contains 'CHANGED=1') {
        $cmSet = @($cmOut | Where-Object { $_ -like 'SET=*' } | ForEach-Object { $_.Substring('SET='.Length) })
        Write-Host "  Codex config.toml — 틀의 자리를 맞췄다 ($($cmSet -join ' · ')) · 다른 키 · 표는 그대로다" -ForegroundColor Green
        $cmBak = @($cmOut | Where-Object { $_ -like 'BACKUP=*' }) | Select-Object -First 1
        if ($cmBak) { Write-Host "     고치기 전 것은 $($cmBak.Substring('BACKUP='.Length)) 에 떠 뒀다" }
      } else {
        Write-Host '  Codex config.toml — 이미 맞다'
      }
      Remove-Item -LiteralPath $cmLog -ErrorAction SilentlyContinue
    }
  }
  # ── 안티그래비티 — **로그인 대신 회사 키로 세운다** (claude-config #62) ─────────
  # 손잡이는 확장이 아니라 `agy` 가 든다 — 확장 설정에는 주소 자리가 없고, `agy` 는 `modelProvider: "gemini"` 를 두고
  #   `GEMINI_API_KEY` 를 환경에 두면 로그인 없이 서며 `GOOGLE_GEMINI_BASE_URL` 로 주소를 돌린다(`agy` 체인지로그).
  # ⚠ **키를 이 파일에 안 쓴다**(PAISetup #2) — 평문 키는 새는 자리만 늘린다. `agy` 는 `GEMINI_API_KEY` 를 환경에서 읽고,
  #   「회사 키의 다른 이름 둘」 칸이 그 이름을 이미 심는다. 여기 쓸 것은 인증 방식 한 줄뿐이다.
  # 주소도 여기 안 쓴다 — `agy` 는 `GOOGLE_GEMINI_BASE_URL` 을 환경에서 읽어 「값 파일이 든 나머지 이름」 칸이 심은 값을 그대로
  #   본다. 파일에 또 적으면 같은 사실이 두 자리에 산다.
  # 사람 것은 둔다 — 우리가 더하는 것은 `modelProvider` 하나다. 그 줄을 지우면 로그인 갈래로 돌아간다(`agy` 문서).
  if ($wantAgy) {
    $dst = $AgyCfg
    $a = $null
    $agyOld = $null
    $agyBroken = $false
    if (Test-Path -LiteralPath $dst) {
      try { $agyOld = [IO.File]::ReadAllBytes($dst); $agyText = Read-TextOf $agyOld; if ($agyText.Trim()) { $a = $agyText | ConvertFrom-Json } } catch {
        Write-Host '  ! 안티그래비티 settings.json 을 못 읽었다 (꼴이 깨졌다) — 안 건드린다' -ForegroundColor Red
        $Fails.Add('안티그래비티 설정 (settings.json 이 깨졌다)')
        $agyBroken = $true
      }
    } else { $a = [pscustomobject]@{} }
    if (-not $agyBroken) {
      # 맞나는 그 키 하나를 보고 가른다 — 통째 JSON 글을 견주지 않는다. `Add-Member -Force` 는 있던 키를 지우고 끝에 다시 붙여, 값이
      #   같아도 그 키가 끝이 아니면 글이 달라져 매번 다시 쓰게 된다(PAISetup #38). 있으면 그 자리에서 값만 고쳐 사람 키의 차례를 둔다.
      if ($null -eq $a) { $a = [pscustomobject]@{} }   # 빈 파일은 `ConvertFrom-Json` 이 아무것도 안 낸다
      $mp = $a.PSObject.Properties['modelProvider']
      if ($mp -and $mp.Value -is [string] -and $mp.Value -ceq $AgyProvider) {
        Write-Host '  안티그래비티 settings.json — 이미 맞다'
      } else {
        if ($mp) { $mp.Value = $AgyProvider } else { $a | Add-Member -NotePropertyName 'modelProvider' -NotePropertyValue $AgyProvider }
        $after = $a | ConvertTo-Json -Depth 10
        $w = Write-FileSafely $dst ($noBom.GetBytes($after)) $agyOld
        if ($w.Did -ceq 'written') { Write-Host '  안티그래비티 settings.json — 썼다 (modelProvider · 키와 주소는 환경변수가 든다)' -ForegroundColor Green }
        elseif ($w.Did -ceq 'raced' -or $w.Did -ceq 'overrun' -or $w.Did -ceq 'linked') { Write-Host "  ! 안티그래비티 settings.json — $($w.Why) · 그 글을 둔다 (다음 판이 맞춘다)" -ForegroundColor Yellow }
        else { Write-Host "  ! 안티그래비티 settings.json 을 못 썼다 — $($w.Why)" -ForegroundColor Red; $Fails.Add('안티그래비티 설정 (못 썼다)') }
      }
    }
  }
} elseif (-not $useGateway) {
  # ── 사외 — **사내에서 심은 회사 연결을 걷는다** (PAISetup #44) ─────────
  # 이 자리에는 그 연결이 가리키는 루프백 프록시도 그것이 읽는 회사 키도 없다(「사외로 간 자리의 사내 잔재」 칸이 걷는다). 남으면
  #   Codex 는 닿지 않는 주소로 가고 agy 는 키가 없어 안 떠, 로그인을 해도 안 선다.
  # ⚠ **우리 값 그대로인 것만 걷는다** — 무엇을 심었나의 기록이 없어 값이 회사 값과 같다는 것이 근거다. Codex 는 병합기의 걷기 판
  #   (`--remove-provider` — 무엇을 걷고 무엇을 두나는 그 머리말)이, agy 는 `modelProvider` 가 회사 값이고 남은 키가 회사 키이거나 없을
  #   때만(`Test-AgyCompanyLink` — 그 값은 사람의 API 키 갈래이기도 하다). 사람이 고친 값은 두고 그 이름을 댄다.
  # 고른 제품을 안 묻는다 — 연결은 파일에 남아 그 도구를 다시 띄우는 날 살아난다. 파일이 없으면 짓지 않는다. 사내로 돌아오면 위
  #   갈래가 다시 심는다.
  $offCodex = [bool]($codexTpl -and (Test-Path -LiteralPath $CodexCfg -PathType Leaf))
  $offAgy   = Test-Path -LiteralPath $AgyCfg -PathType Leaf
  if ($offCodex -or $offAgy) {
    Write-Host ''
    Write-Host '  Codex · 안티그래비티 회사 연결 (사외)' -ForegroundColor Cyan
  }
  if ($offCodex) {
    $src = Join-Path $Here $codexTpl
    $ocPython = if ((Test-Path -LiteralPath $src) -and (Test-Path -LiteralPath $CodexCfgMerge)) { Measure-Runs 'python' '--version' } else { '' }
    if (-not (Test-Path -LiteralPath $src)) {
      Write-Host "  ! Codex config.toml — 회사 틀이 이 폴더에 없어 회사 연결이 남았나 못 가렸다 · 안 건드렸다 ($codexTpl)" -ForegroundColor Yellow
    } elseif (-not (Test-Path -LiteralPath $CodexCfgMerge)) {
      Write-Host "  ! Codex config.toml — 틀 병합기가 이 폴더에 없어 회사 연결을 못 걷었다 ($CodexCfgMerge)" -ForegroundColor Red
      $Fails.Add('Codex 설정 (틀 병합기가 없다)')
    } elseif ($ocPython -eq 'unmeasured') {
      Add-UnmeasuredStep 'Codex 회사 연결 걷기' 'python --version' '걷지도 건너뛰지도 않았다'
    } elseif ($ocPython -ne 'yes') {
      Write-Host '  ! Codex config.toml — python 이 안 서서 회사 연결을 못 걷었다 · 남았으면 Codex 가 닿지 않는 주소로 간다' -ForegroundColor Yellow
    } else {
      $cmLog = [IO.Path]::GetTempFileName()
      $cmRc = Invoke-Logged 'python' @('-X', 'utf8', $CodexCfgMerge, '--config', $CodexCfg, '--template', $src, '--remove-provider') $cmLog
      $cmOut = @(Get-Content -LiteralPath $cmLog -Encoding UTF8 -ErrorAction SilentlyContinue |
                 ForEach-Object { "$_".Trim() } | Where-Object { $_ })
      if ($cmRc -ne 0) {
        Write-Host '  ! Codex config.toml — 회사 연결을 못 걷었다 · 파일은 그대로다. 병합기가 뱉은 끝 줄:' -ForegroundColor Red
        Show-Log $cmLog
        $Fails.Add('Codex 설정 (회사 연결 걷기 실패)')
      } else {
        if ($cmOut -contains 'CHANGED=1') {
          $cmUnset = @($cmOut | Where-Object { $_ -like 'UNSET=*' } | ForEach-Object { $_.Substring('UNSET='.Length) })
          Write-Host "  Codex config.toml — 회사 연결을 걷었다 ($($cmUnset -join ' · ')) · 다른 키 · 표는 그대로다" -ForegroundColor Green
          $cmBak = @($cmOut | Where-Object { $_ -like 'BACKUP=*' }) | Select-Object -First 1
          if ($cmBak) { Write-Host "     고치기 전 것은 $($cmBak.Substring('BACKUP='.Length)) 에 떠 뒀다" }
        } else {
          Write-Host '  Codex config.toml — 회사 연결이 없다'
        }
        $cmKept = @($cmOut | Where-Object { $_ -like 'KEPT=*' } | ForEach-Object { $_.Substring('KEPT='.Length) })
        # 틀과 다른 표는 사람이 고친 것만이 아니다 — 옛 판의 틀이 심은 표도 틀의 값이 바뀐 뒤에는 다르다. 그래서 고친 사람을 단정하지
        #   않고 한 판에 한 줄로만 댄다.
        if ($cmKept.Count) {
          Write-Host "  ! Codex config.toml — 회사 제공자 표가 틀과 다른 키를 들어 표는 두었다 ($($cmKept -join ' · ')) · 사람이 고쳤거나 옛 판의 틀이다. 맨 위의 회사 고르기(model_provider)는 걷는다 — 그 표를 고르는 프로필이 있으면 그 프로필은 손으로 고친다" -ForegroundColor Yellow
        }
      }
      Remove-Item -LiteralPath $cmLog -ErrorAction SilentlyContinue
    }
  }
  if ($offAgy) {
    $a = $null
    $agyOld = $null
    $agyBroken = $false
    try { $agyOld = [IO.File]::ReadAllBytes($AgyCfg); $agyText = Read-TextOf $agyOld; if ($agyText.Trim()) { $a = $agyText | ConvertFrom-Json } } catch {
      Write-Host '  ! 안티그래비티 settings.json 을 못 읽었다 (꼴이 깨졌다) — 안 건드린다' -ForegroundColor Red
      $Fails.Add('안티그래비티 설정 (settings.json 이 깨졌다)')
      $agyBroken = $true
    }
    $mp = if ($a) { $a.PSObject.Properties['modelProvider'] } else { $null }
    if (Test-AgyCompanyLink $a) {
      $a.PSObject.Properties.Remove('modelProvider')
      $w = Write-FileSafely $AgyCfg ((New-Object Text.UTF8Encoding($false)).GetBytes(($a | ConvertTo-Json -Depth 10))) $agyOld
      if ($w.Did -ceq 'written') { Write-Host '  안티그래비티 settings.json — 회사 연결(modelProvider)을 걷었다 · 처음 실행할 때 Google 로그인으로 쓴다' -ForegroundColor Green }
      elseif ($w.Did -ceq 'raced' -or $w.Did -ceq 'overrun' -or $w.Did -ceq 'linked') { Write-Host "  ! 안티그래비티 settings.json — $($w.Why) · 그 글을 둔다 (다음 판이 걷는다)" -ForegroundColor Yellow }
      else { Write-Host "  ! 안티그래비티 settings.json — 회사 연결을 못 걷었다 ($($w.Why))" -ForegroundColor Red; $Fails.Add('안티그래비티 설정 (회사 연결 걷기 실패)') }
    } elseif ($mp -and $mp.Value -is [string] -and $mp.Value -ceq $AgyProvider) {
      Write-Host '  안티그래비티 settings.json — modelProvider 는 둔다 · GEMINI_API_KEY 가 회사 키가 아니라 그 사람의 API 키 갈래로 본다'
    } elseif (-not $agyBroken) {
      Write-Host '  안티그래비티 settings.json — 회사 연결이 없다'
    }
  }
}

} catch { Write-StepFault $_ }
Exit-Step 'site'

# ══ 걸음 「Claude 홈 설정」 ═════════════════════════════════════════════════════════════════════
#   층 — 홈
#   하는 일 — `~/.claude/settings.json` 의 기능 스위치 · 모델 목록 · WebFetch 검증 건너뛰기 · 기본 권한 모드와 허용 규칙(러너 허락 포함) ·
#     env 밀기와 걷기 · 걷힌 Tavily 안내 걷기. 심은 것은 장부(`$ClaudePlantLedger`)에 적고, 선언에서 빠진 우리 것은 장부로 걷는다
#   앞에서 받는 것 — 「키와 값」의 심은 값(`$Planted`) · 값 파일(`$fromFile` · 짐의 값 파일 이름 `$DistNames` · 그 파일이 있나 `$DistComplete`) ·
#     게이트웨이를 쓰나 · settings 에 안 밀 이름 · 회사 키로 아는 값(`Test-CompanyKey`) · 우리 게이트웨이 주소(`$OurGatewayUrls`) · 고른 제품
#     (`$hostClaude`) · 칸 없이 까는 스킬 표(`$FreeSkills`) · 맡기기 러너 값의 두 자리 표(`$AgyModelVarsBySite` · `$CcBgVarsBySite`) ·
#     기능 스위치와 홈 설정 씨앗(`$Features` · `$HomeSeed`)
#   안 하는 것 — 스킬 · 규범 · 훅 등록. 훅 등록은 「도구별 홈」의 손(`tool-homes.py`)이 이 걸음이 쓴 파일 위에 놓는다
#   ⚠ **이 설치기가 이 파일을 쓰는 자리는 이 걸음 하나다** — 손이 놓은 뒤에 이 걸음의 `$cfg`(손 앞에서 읽은 것)로 다시 쓰면 손이
#     놓은 등록이 그 앞 판으로 되돌아간다. 이 파일을 고칠 일은 여기서 하고 손 앞에서 한 번 쓴다
# 씨앗은 없을 때만 깐다 — 사람이 앱에서 바꾼 값을 재실행이 지우면 안 된다. 담는 것도 공용으로 서는 것뿐이다 — `permissions` 는
#   특정 저장소의 스크립트 이름을 들어 씨앗에서 안 옮긴다. 이 걸음이 `permissions` 에 심는 것은 아래 `$ClaudeHomePlants` 표뿐이다 —
#   러너는 이 설치기가 까는 스킬이라 그 이름은 배포본이 낸 길이다.
# `env` 칸은 다르다 — 값 파일이 `#settings-env` 를 들면 있는 파일에도 민다(몸통은 자리 이름을 모른다). 사내에서는 환경변수와 이
#   파일을 둘 다 봐야 한다 — 환경변수만 두면 모델 고르는 자리가 엉뚱한 값으로 서고, 파일만 두면 같은 변수를 읽는 다른 앱이 키를
#   잃는다. 값의 진본은 `install.env` 하나고 여기로는 파생해 밀려온다.
# ⚠ **그 안에서 키는 안 민다 — `$SettingsEnvSkip`.** 이 파일은 설정 저장소가 동기화하는 종류라, 여기 든 값은 평문으로 저장소까지
#   흘러간다. 키를 읽는 세 이름은 사용자 환경변수가 이미 들고(「회사 키의 다른 이름 둘」 칸) CLI 는 거기서 읽는다 — 주소 · 모델은
#   밀고 토큰과 그 별명 둘은 뺀다(PAISetup #2).
# 맡기기 러너 값(두 자리 표 `$AgyModelVarsBySite` · `$CcBgVarsBySite` 의 이름)도 안 민다 — 러너는 사용자 환경변수를 읽어 여기 둘
#   까닭이 없고, 여기 든 값은 CLI · VS Code 세션에서 물려받은 값을 이겨 그 세션이 띄운 러너가 이 사본으로 나간다. 장부가 서기 전 판이
#   민 사본은 장부 밖이라, 아래 「러너 값 사본」 칸이 오늘 표의 값으로 가른다(PAISetup #41).
Enter-Step 'home'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)
Assert-StepsDone 'keys'   # 자리 · 심은 값 · 안 밀 이름 목록(키 · 러너 값 · 사람이 친 값)으로 settings.json 에 밀고 걷는다
$homeCfg = Join-Path $homeDir 'settings.json'
$homeAt  = ConvertTo-LedgerAt $homeCfg
New-Item -ItemType Directory -Path $homeDir -Force | Out-Null
$Ledger = Read-RunLedger $ClaudePlantLedger

# 읽기 — 바이트를 한 번 읽어 그 글을 고치고, 쓸 때 그 바이트와 다시 견준다(`Write-FileSafely`). 빈 파일은 빈 표로 읽는다 — 반쪽 쓰기의
#   가장 흔한 끝이 빈 파일이라, 「있음」으로 읽고 이 칸을 건너뛰면 사람이 둔 것을 잃은 자리가 그대로 남는다(PAISetup #44 ⑱).
$cfg = $null
$homeOld = $null
$homeBlank = $false
if (Test-Path -LiteralPath $homeCfg) {
  try {
    $homeOld = [IO.File]::ReadAllBytes($homeCfg)
    $homeText = Read-TextOf $homeOld
    if ($homeText.Trim()) { $cfg = $homeText | ConvertFrom-Json } else { $cfg = [pscustomobject]@{}; $homeBlank = $true }
    if ($cfg -isnot [System.Management.Automation.PSCustomObject]) { throw '맨 위가 표가 아니다' }
    if ($homeBlank) { Write-Host '  ! 비어 있다 — 빈 설정으로 읽고 필요한 것을 민다' -ForegroundColor Yellow }
    else { Write-Host '  있음 — 그대로 두고 필요한 것만 민다' }
  } catch {
    $cfg = $null
    # ⚠ **깨진 파일을 덮지 않는다.** 사람이 손댄 것이 거기 들어 있을 수 있고, 지우면 무엇을 잃었는지 물을 자리가 없다. 말하고 물러난다.
    Write-Host '  ! settings.json 을 못 읽었다 (꼴이 깨졌다) — 안 건드린다' -ForegroundColor Red
    $Fails.Add('홈 settings.json 을 못 읽었다')
  }
} else {
  # 새 파일에 옮기는 것은 이 걸음이 고른 씨앗의 맨 위 키뿐이다(`$HomeSeedKeys` — 이름은 여기, 값은 씨앗 `$HomeSeed` · PAISetup #47 ⑦). 씨앗은
  #   사외 VDI 의 홈을 통째로 덮는 바탕이라 그 사람 취향의 키(테마 따위)도 들어, 다 옮기면 이 설치가 고른 적 없는 값을 심는다. `env` 는
  #   아래 기능 스위치 칸이 장부에 적으며 심고, `permissions` 는 아래 표(`$ClaudeHomePlants`)가 심는다 — 씨앗의 허용 줄은 설정 저장소의
  #   배포 스크립트를 여는 것이라 그 저장소의 세션 훅이 든다.
  $HomeSeedKeys = @('agentPushNotifEnabled', 'inputNeededNotifEnabled')
  $cfg = [pscustomobject]@{}
  if ($HomeSeed -and $HomeSeed.Obj) {
    foreach ($p in $HomeSeed.Obj.PSObject.Properties) {
      if ($HomeSeedKeys -ccontains $p.Name) { $cfg | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value }
    }
  } elseif ($HomeSeed) {
    Write-Host "  ! 홈 설정 씨앗을 못 읽었다 — $($HomeSeed.Why) · 빈 설정으로 짓는다" -ForegroundColor Yellow
  }
  Write-Host '  없어서 씨앗을 깐다'
}

# ── 기본 권한 모드 · 허용 규칙 — 심는 표 (claude-config #147 · claude-config #142 ㉲ · PAISetup #50)─────────────────────────────────────────
# 기본 권한 모드(`permissions.defaultMode = auto` — 자동 모드)는 Claude 를 고르면 심는다. 서브에이전트가 묻지 않고 돌려면 이 모드가
#   기본이어야 한다 — 편집 자동 승인(`acceptEdits`)은 허락 목록 밖 셸 명령마다 사람에게 물어 레인이 거기서 멈춘다. 회사 게이트웨이에서
#   분류기 판정이 가끔 끊기는 값은 그보다 작다고 보았다(claude-config #180). 판이 값을 바꾸면 장부에 든 옛 우리 값 그대로인 것만 새 값으로
#   간다. 러너를 부르는 Bash 명령의 허락은 그 러너 스킬이 Claude 홈에 서는 조건(`$FreeSkills` 의 Claude 칸)에서 심는다 — 허락이 없으면
#   스킬이 시킨 호출마다 묻거나(편집 자동 승인) 분류기가 막는다(자동 모드 · claude-config #142).
# ⚠ **스킬이 Claude 에게 시키는 꼴(`pythonw "<스킬 폴더>/scripts/<러너>" …`)만 연다** — `python` 꼴을 열면 `python -c "…" agy_bg.py`
#   처럼 러너가 아닌 명령까지 분류기를 건너뛴다. 스킬 폴더는 홈마다 달라 `*` 로 파일 이름만 문다.
# 끝의 일곱 줄(`허용 규칙 — …`)은 러너와 상관없이 Claude 를 고른 모든 PC 에 심는다 — 자동 모드는 허용 목록에 안 맞는 도구 호출마다 분류기를 타는데
#   좁은 허용 규칙은 분류기 앞에서 풀려 그 시간을 던다. 연 것은 읽기 전용이거나 로컬에서 멱등인 꼴(이슈 읽기 · 원격 추적 참조만 바꾸는 `git fetch` ·
#   별표 없는 버전 · 도움말 명령 · 임시 폴더 읽기)뿐이고, 도구가 없는 PC 에서는 맞는 호출이 없어 해롭지 않으니 조건은 Claude 를 고른 것 하나다.
# ⚠ **쓰기 동사와 해석기 와일드카드는 이 표에 안 든다** — `gh issue comment` · `git push` · `python -c` 꼴을 규칙으로 열면 분류기를 건너뛰어 그대로
#   돈다. 접두 규칙이 못 막는 깃발(`git fetch --upload-pack=<명령>`)이 남는 줄은 알고 연다. `Label` 은 설치 창과 끝 검증이 그 줄을 부르는 이름이다.
# ⚠ **우리 것은 장부에 든 것뿐이다** — 사람이 그 모드를 고르면 Claude 도 같은 값을 적어, 값이 같다는 것으로는 못 가른다. 그래서 없을
#   때만 심고 그때 적는다(guard 꼴 · 같은 값을 우리 것으로 안 받는다). 조건이 빠지면 장부에 든 것 가운데 지금 값이 우리 값 그대로인 것만
#   걷고, 사람이 바꾼 것은 값을 두고 장부에서만 뺀다. 장부에 있는데 이 표에 없는 줄(물러난 것)도 같은 자로 걷는다. 지워진 것은 다음
#   설치가 다시 심는다 — 끄는 길은 다른 `defaultMode` 값이나 `permissions.deny` 다.
# 장부는 설치기 제 자리(자동 실행 기록 · 값 파일이 사는 폴더)에 둔다 — 중립 한 벌은 갈 곳 표의 손 몫이라 설치기가 그 자리를
#   들면 안 된다(결정 0112 · 갈 곳 표 손 검사 ⑰).
$ClaudeHomePlants = @(
  @{ Label = '기본 권한 모드';            Key = 'defaultMode'; Value = 'auto'; Want = [bool]$hostClaude }
  @{ Label = 'agy 러너 허락';             Key = 'allow';       Value = 'Bash(pythonw *agy_bg.py *)'
     Want = [bool]($FreeSkills -and $FreeSkills['agy-background'].Claude) }
  @{ Label = 'Codex · Copilot 러너 허락'; Key = 'allow';       Value = 'Bash(pythonw *codex_copilot_bg.py *)'
     Want = [bool]($FreeSkills -and $FreeSkills['codex-copilot-background'].Claude) }
  @{ Label = '허용 규칙 — gh issue view (읽기)';     Key = 'allow'; Value = 'Bash(gh issue view *)';           Want = [bool]$hostClaude }
  @{ Label = '허용 규칙 — git fetch (원격 추적만)';  Key = 'allow'; Value = 'Bash(git fetch *)';               Want = [bool]$hostClaude }
  @{ Label = '허용 규칙 — codex --version';          Key = 'allow'; Value = 'Bash(codex --version)';           Want = [bool]$hostClaude }
  @{ Label = '허용 규칙 — agy --version';            Key = 'allow'; Value = 'Bash(agy --version)';             Want = [bool]$hostClaude }
  @{ Label = '허용 규칙 — agy --help';               Key = 'allow'; Value = 'Bash(agy --help)';                Want = [bool]$hostClaude }
  @{ Label = '허용 규칙 — Git Bash 임시 폴더 읽기';  Key = 'allow'; Value = 'Read(//tmp/**)';                  Want = [bool]$hostClaude }
  @{ Label = '허용 규칙 — 윈도 임시 폴더 읽기';      Key = 'allow'; Value = 'Read(~/AppData/Local/Temp/**)';   Want = [bool]$hostClaude }
)

# 맡기기 러너 값 — 이름마다 두 자리 표가 그 이름에 준 값들(이름 → 값 목록 · `Get-SiteValues`). 아래 「env 밀기」가 이 이름들을 안 밀고,
#   「러너 값 사본」이 이 값으로 우리 것을 가른다. ⚠ 손 목록으로 적지 않는다 — 표에 이름이 느는 날 손 목록만 안 늘어 그 이름이 다시
#   밀린다. 맡기기 모델 표는 맡기기를 안 고른 판에도 읽는다(「키와 값」) — 못 읽은 판에만 그 표의 이름이 비어 온다.
$RunnerEnvValues = Get-SiteValues @($AgyModelVarsBySite, $CcBgVarsBySite)

$homeWrote = $null
if ($cfg) {
  $wantEnv = (Read-Directive $DistEnvFile 'settings-env') -eq 'yes'
  $dirty = $homeBlank

  # env 칸을 먼저 세운다 — 아래 둘(기능 스위치 · 게이트웨이 값)이 같은 자리에 쓴다.
  if (-not $cfg.PSObject.Properties['env']) {
    $cfg | Add-Member -NotePropertyName env -NotePropertyValue ([pscustomobject]@{}) -Force
  }
  # 이 파일의 칸을 읽고 쓰는 손 — 장부 손이 부른다. 메모리의 `$cfg` 만 고치고 파일은 이 걸음 끝에서 한 번 쓴다. 장부 손이 무엇을 바꿨으면
  #   그 파일을 쓴다(`$HomeChanged`).
  $EnvGet    = { param($n) Get-SettingsSlot $cfg 'settings-env' $n }
  $EnvSet    = { param($n, $v) $cfg.env | Add-Member -NotePropertyName $n -NotePropertyValue $v -Force; $true }
  $EnvRemove = { param($n, $v) $cfg.env.PSObject.Properties.Remove($n); $true }
  $HomeChanged = { param($r) [bool]($r.Planted.Count + $r.Replaced.Count + $r.Removed.Count) }

  # 클라이언트 기능 스위치 — 자리도 값 파일도 안 탄다. 선언은 홈 설정 씨앗의 `env`(`$Features`)이고, 씨앗에서 뺀 스위치는 장부로 걷는다(PAISetup #44 ⑨).
  #   씨앗을 못 읽은 판은 안 건드린다 — 그 판의 선언이 없다.
  if ($null -eq $Features) {
    Write-Host "  ! 기능 스위치 — 홈 설정 씨앗을 못 읽어 안 건드렸다$(if ($HomeSeed -and $HomeSeed.Why) { " ($($HomeSeed.Why))" })" -ForegroundColor Yellow
  }
  $fx = Sync-Planted -Ledger $Ledger -Place 'settings-env' -At $homeAt -By 'features' -Want $(if ($null -ne $Features) { $Features } else { [ordered]@{} }) `
          -Complete ($null -ne $Features) -Get $EnvGet -Set $EnvSet -Remove $EnvRemove -Where '기능 스위치 · env' -Speak
  if (& $HomeChanged $fx) { $dirty = $true }

  # 고를 모델 목록 — **게이트웨이에 닿는 자리에만 선다** (선언은 위 `$ModelPicker`). 사외면 선언이 비어 우리가 둔 목록을 걷는다 — 사내에서
  #   쓰고 사외로 간 기계에 그 줄이 남으면 구독으로 못 부르는 것이 목록에 선다.
  # `$useGateway` 가 자리 판정을 이미 들고 있다 — 두 자리가 재면 한쪽이 낡아 여기서 다시 안 잰다.
  # ⚠ **사람이 둔 목록은 안 덮고 안 걷는다** — 우리 것은 장부에 든 목록 그대로인 것뿐이다(PAISetup #44 ⑫). 판이 목록을 바꾸면 장부의 옛 목록
  #   그대로인 것만 새 목록으로 간다. 장부를 처음 세우는 판은 옛 판처럼 덮고 적는다 — 옛 판이 둔 목록은 기록이 없어 사람 것과 못 가르고,
  #   그대로 두면 옛 판의 목록이 사람 것으로 굳는다.
  $pickWant = [ordered]@{}
  if ($useGateway) {
    $want = $ModelPicker | ForEach-Object { [pscustomobject]$_ }
    $pickerObj = [pscustomobject]@{ options = @($want); replaceBuiltInOptions = $ModelPickerOnly }
    $pickWant['modelPicker'] = [string]($pickerObj | ConvertTo-Json -Depth 10 -Compress)
  }
  $pick = Sync-Planted -Ledger $Ledger -Place 'settings' -At $homeAt -By 'model-picker' -Want $pickWant `
            -Mode $(if ($Ledger.Migrating) { 'overwrite' } else { 'guard' }) `
            -Get { param($n) Get-SettingsSlot $cfg 'settings' $n } `
            -Set { param($n, $v) $cfg | Add-Member -NotePropertyName modelPicker -NotePropertyValue ($v | ConvertFrom-Json) -Force; $true } `
            -Remove { param($n, $v) $cfg.PSObject.Properties.Remove('modelPicker'); $true } `
            -Label @{ modelPicker = '모델 목록' } -Where 'modelPicker' -Speak -SayKept
  if (& $HomeChanged $pick) { $dirty = $true }
  elseif ($useGateway -and -not $pick.Kept.Count -and -not $pick.Unread.Count) { Write-Host '  모델 목록 — 이미 맞다' }

  # WebFetch 검증 건너뛰기 — **사내 자리에만 켠다** (claude-config #118 · 결정 0087).
  # 사내 망이 `api.anthropic.com` 을 SNI 로 끊어, WebFetch 가 가져오기 전에 묻는 Anthropic 차단 목록 조회
  # (`/api/web/domain_info`)가 늘 져 열리는 주소도 못 가져온다. 이 키가 그 조회를 건너뛴다(Claude Code 설정 스키마의 키 · 2.1.293 에서 확인).
  # ⚠ **망 자리로 가른다 — 게이트웨이가 아니다.** 끊는 것은 사내 망 장비라 `$inside` 를 본다.
  # 잃는 것은 Anthropic 의 페치 차단 목록 검사다 — 그래서 사외에서는 안 켜고, 우리가 켠 값(참)이 남았으면 걷는다(거짓이나 다른 값은 사람이
  #   둔 것이라 안 건드린다).
  $skipOn = $cfg.PSObject.Properties['skipWebFetchPreflight'] -and ($cfg.skipWebFetchPreflight -eq $true)
  if ($inside) {
    if ($skipOn) {
      Write-Host '  WebFetch 검증 건너뛰기 — 이미 켜져 있다'
    } else {
      $cfg | Add-Member -NotePropertyName skipWebFetchPreflight -NotePropertyValue $true -Force
      $dirty = $true
      Write-Host '  WebFetch 검증 건너뛰기 — 켰다 (사내 망이 그 조회를 끊는다)' -ForegroundColor Green
    }
  } elseif ($skipOn) {
    $cfg.PSObject.Properties.Remove('skipWebFetchPreflight')
    $dirty = $true
    Write-Host '  WebFetch 검증 건너뛰기 — 걷었다 (사외는 그 검사가 선다)' -ForegroundColor Green
  }

  # 기본 권한 모드 · 허용 규칙 — 위 표(`$ClaudeHomePlants`)대로 장부 손이 심고 장부에 든 우리 것만 걷는다(guard 꼴 · 표의 값이 바뀌면
  #   장부의 옛 우리 값 그대로인 것만 새 값으로 간다). `permissions` 가 표가 아니거나 `allow` 가 목록이 아니면 그 칸을 안 건드리고 장부는
  #   잇는다 — 사람이 고친 뒤 다음 설치가 맞춘다. 장부는 설정을 쓴 뒤에 쓴다(이 걸음 끝).
  $permWant = [ordered]@{}; $allowWant = [ordered]@{}
  foreach ($p in @($ClaudeHomePlants | Where-Object { $_.Want })) {
    if ($p.Key -ceq 'allow') {
      if (-not $allowWant.Contains('permissions.allow')) { $allowWant['permissions.allow'] = @() }
      $allowWant['permissions.allow'] += $p.Value
    } else { $permWant["permissions.$($p.Key)"] = $p.Value }
  }
  $PermGet = { param($n) Get-SettingsSlot $cfg 'settings' $n }
  $PermBox = {
    if (-not $cfg.PSObject.Properties['permissions']) { $cfg | Add-Member -NotePropertyName permissions -NotePropertyValue ([pscustomobject]@{}) -Force }
    $cfg.permissions
  }
  $PermTidy = { if ($cfg.PSObject.Properties['permissions'] -and -not @($cfg.permissions.PSObject.Properties).Count) { $cfg.PSObject.Properties.Remove('permissions') } }
  $pm = Sync-Planted -Ledger $Ledger -Place 'settings' -At $homeAt -By 'permissions' -Names @('permissions.defaultMode') -Want $permWant -Mode 'guard' `
          -Get $PermGet -Set { param($n, $v) (& $PermBox) | Add-Member -NotePropertyName defaultMode -NotePropertyValue $v -Force; $true } `
          -Remove { param($n, $v) $cfg.permissions.PSObject.Properties.Remove('defaultMode'); & $PermTidy; $true } `
          -Label @{ 'permissions.defaultMode' = '기본 권한 모드' } -Where 'permissions.defaultMode' -Speak -SayKept -ShowValue
  # 허용 줄은 줄마다 표의 `Label` 로 알린다 — `Sync-Planted` 의 이름표는 이름(`permissions.allow`) 하나뿐이라 줄을 못 가른다. 그래서 `-Speak` 를
  #   빼고 심고 걷는 손이 찍는다. 표에 없는 줄(물러난 것)과 칸 전체의 말(못 읽음 · 사람이 걷어 둠)은 이름표 `Claude 허용 규칙` 이다.
  $AllowSay = {
    param([string]$v, [bool]$planted)
    $row = @($ClaudeHomePlants | Where-Object { $_.Key -ceq 'allow' -and $_.Value -ceq $v }) | Select-Object -First 1
    $what = if ($planted) { "심었다 ($v)" } else { "걷었다 (우리가 심은 $v · 이번에는 안 심는다)" }
    Write-Host "  $(if ($row) { $row.Label } else { 'Claude 허용 규칙' }) — $what (permissions.allow)" -ForegroundColor Green
  }
  $pa = Sync-Planted -Ledger $Ledger -Place 'settings' -At $homeAt -By 'permissions' -Names @('permissions.allow') -Want $allowWant -Mode 'guard' -List `
          -Get $PermGet `
          -Set { param($n, $v) $box = & $PermBox; $box | Add-Member -NotePropertyName allow -NotePropertyValue @(@($box.allow | Where-Object { $null -ne $_ }) + $v) -Force; & $AllowSay $v $true; $true } `
          -Remove {
            param($n, $v)
            $left = @(@($cfg.permissions.allow) | Where-Object { $null -ne $_ -and $_ -cne $v })
            if ($left.Count) { $cfg.permissions | Add-Member -NotePropertyName allow -NotePropertyValue $left -Force }
            else { $cfg.permissions.PSObject.Properties.Remove('allow') }
            & $PermTidy; & $AllowSay $v $false; $true } `
          -Label @{ 'permissions.allow' = 'Claude 허용 규칙' } -Where 'permissions.allow' -SayKept
  if ((& $HomeChanged $pm) -or (& $HomeChanged $pa)) { $dirty = $true }
  elseif (@($ClaudeHomePlants | Where-Object { $_.Want }).Count -and -not ($pm.Kept.Count + $pm.Unread.Count + $pa.Unread.Count)) {
    Write-Host '  기본 권한 모드 · 허용 규칙 — 이미 맞다'
  }

  # 러너 값 사본 — 이 파일에 맡기기 러너 이름(`$RunnerEnvValues`)이 있으면 판마다 맞춘다. 이 칸은 그 이름을 안 밀지만, 그 이름을
  #   밀던 판(장부가 서기 전)이 남긴 줄이나 사람이 넣은 줄이 있을 수 있다.
  # ⚠ **`$Planted` 도 `#settings-env` 도 안 묻는다.** 사용자 환경이 이미 맞는 재설치는 아무것도 안 심어, 심은 이름만 훑는 꼴로는 바로
  #   그 판에 사본이 그대로 남는다.
  # 우리 것이라는 근거는 값이다 — 두 자리 표 어느 쪽이든 그 이름의 값과 글자까지 같으면 걷는다. 다르면 사람이 고른 값으로 보고 둔 채
  #   알린다 — 사람의 선택이 이기고 실패가 아니다. 이 파일의 값이 이기므로 그 세션의 러너가 그 값으로 나간다는 것까지 말한다.
  # ⚠ **알리는 것은 한 번이다(PAISetup #44 ②)** — 알린 값은 장부에 `seen` 으로 적고, 그 값 그대로면 다음 판은 다시 안 알린다. 값이
  #   바뀌거나 사라지면 그 기록을 뺀다(다시 서면 다시 알린다).
  if ($cfg.PSObject.Properties['env']) {
    $seenRows = @(Find-LedgerRows $Ledger 'settings-env' $homeAt 'seen')
    foreach ($p in @($cfg.env.PSObject.Properties)) {
      if (-not $RunnerEnvValues.ContainsKey($p.Name)) { continue }
      if ($p.Value -is [string] -and $RunnerEnvValues[$p.Name] -ccontains $p.Value) {
        $cfg.env.PSObject.Properties.Remove($p.Name)
        $dirty = $true
        Write-Host "  $($p.Name) — settings.json 에서 걷었다 (맡기기 러너 값은 사용자 환경변수가 든다)" -ForegroundColor Green
      } else {
        $shown = Get-SettingsSlot $cfg 'settings-env' $p.Name
        if (@($seenRows | Where-Object { $_.Name -ceq $p.Name -and (Test-SameText $_.Value $shown) }).Count) { continue }
        Write-Host "  ! $($p.Name) 이 settings.json 에 우리 표에 없는 값($($p.Value))으로 있다 — 사람이 고른 값으로 보고 둔다" -ForegroundColor Yellow
        Write-Host "     CLI · VS Code 세션이 띄운 러너는 이 값으로 나간다. 우리 값으로 돌리려면 이 줄을 지운다 — 볼 자리: $homeCfg  (env 칸)"
        Set-LedgerRow $Ledger 'settings-env' $homeAt $p.Name 'seen' $shown
      }
    }
    foreach ($r in $seenRows) {
      if (-not (Test-SameText (Get-SettingsSlot $cfg 'settings-env' $r.Name) $r.Value)) { [void]$Ledger.Rows.Remove($r) }
    }
  }

  # 안 밀기로 한 이름(`$SettingsEnvSkip` — 회사 키와 그 별칭 둘)이 남아 있으면 걷는다 — 심는 자리를 줄였으면 걷는 자리가 선다. 안
  #   걷으면 그 이름을 밀던 배포본으로 깐 기계는 키를 그대로 든다. 여기는 이름 대신 자리가 물러난 것이다.
  # ⚠ **회사 키일 때만 걷고, 이번 판에 심었나는 안 묻는다.** 우리 것인가는 값이 가른다(`Test-CompanyKey` · 「키와 값」의 「회사 키」
  #   칸) — 심은 이름만 훑으면 그 도구를 안 세우는 판과 사외 판에 회사 키가 이 파일에 남는다. 다른 값은 사람 것이다. 이번에 심은
  #   이름이면 이 파일의 값이 이겨 방금 심은 키를 가리므로 빨갛게 문다. 안 심은 이름은 두고 이름을 댄다(`ANTHROPIC_` 는 아래 「홀로
  #   있다」 칸이 든다). 키는 장부 밖이다 — 평문을 하나 더 두지 않는다.
  # 이 파일에서 우리 주소와 짝으로 선 키(사외 판)는 「키와 값」의 「회사 키」 칸이 이미 회사 키로 세우고 덩이에 두었다.
  if ($cfg.PSObject.Properties['env']) {
    foreach ($k in $SettingsEnvSkip) {
      if (-not $cfg.env.PSObject.Properties[$k]) { continue }
      if (Test-CompanyKey ([string]$cfg.env.$k)) {
        $cfg.env.PSObject.Properties.Remove($k)
        $dirty = $true
        Write-Host "  $k — settings.json 에서 걷었다 (회사 키는 이 파일에 안 둔다)" -ForegroundColor Green
      } elseif ($Planted.ContainsKey($k)) {
        Write-Host "  ! $k 이 settings.json 에 다른 값으로 있다 — 심은 값을 가린다" -ForegroundColor Red
        Write-Host "     볼 자리: $homeCfg  (env 칸)"
        $Fails.Add("$k 이 settings.json 에 다른 값으로 있다")
      } elseif ($k -notlike 'ANTHROPIC_*') {
        Write-Host "  $k — settings.json 에 우리 키가 아닌 값이 있다 · 그대로 둔다"
      }
    }
  }

  # 사외면 프록시 주소와 사내 전용 이름도 이 파일에서 걷는다 — 걷는 자리가 둘이라는 말이 여기에도 선다. 밀기는 더하기만 해서
  #   안 밀기로 한 이름은 스스로 사라지지 않고, 아래 「홀로 있다」는 `ANTHROPIC_` 만 물어 `GOOGLE_GEMINI_BASE_URL` 같은 것을 못 잡는다.
  # ⚠ **걷어도 되나는 `Test-OurGatewayUrl` · `Test-OurProxyEntry` · `Test-OurInsideOnlyEntry` 가 판다 — 「사외로 간 자리의 사내 잔재」
  #   칸과 같은 문이다.** 판정을 여기 따로 적으면 이름 울타리가 한쪽에서 빠져 남의 값을 지운다. 왜 그 물음인지는 그 함수 머리가 든다.
  #   게이트웨이 주소는 「키와 값」이 사외에서 값 파일 표(`$fromFile`)에서 버린 이름이라 `Test-OurProxyEntry` 로는 못 가르고, 「회사 키」
  #   칸이 모은 우리 주소(`$OurGatewayUrls`)와 글자로 견준다. 다른 주소는 루프백이어도 두고, 아래 「홀로 있다」가 그 이름을 댄다.
  #   이 칸이 든 이름(짐의 값 파일이 든 이름 가운데 이 자리가 안 심은 것)은 아래 「env 밀기」의 장부 손이 기록만 잇는다.
  # ⚠ **훑는 목록을 먼저 뜬다** — 도는 중에 지우면 열거가 깨진다.
  if (-not $useGateway -and $cfg.PSObject.Properties['env']) {
    foreach ($p in @($cfg.env.PSObject.Properties)) {
      # 까닭마다 말이 다르다 — 로그를 읽는 사람이 주소가 죽어서인지, 이름이 사외에서 뜻이 없어서인지 가른다.
      $why = ''
      if ($p.Name -ceq 'ANTHROPIC_BASE_URL') {
        if (-not (Test-OurGatewayUrl ([string]$p.Value) $OurGatewayUrls)) { continue }
        $why = '사외라 게이트웨이를 안 쓴다'
      }
      elseif (Test-OurProxyEntry $p.Name $p.Value $fromFile)  { $why = '사외라 프록시가 안 선다' }
      elseif (Test-OurInsideOnlyEntry $p.Name $fromFile)  { $why = '사외에서는 뜻이 없는 이름' }
      else { continue }
      $cfg.env.PSObject.Properties.Remove($p.Name)
      $dirty = $true
      Write-Host "  $($p.Name) — settings.json 에서 걷었다 ($why)" -ForegroundColor Green
    }
  }

  # env 밀기 — 선언은 이번 판에 사용자 환경에 심은 값(`$Planted`)에서 키 · 맡기기 러너 값 · 물음에 사람이 친 값을 뺀 것이다(`#settings-env = yes` 일 때만 ·
  #   PAISetup #44 ①). 장부 손이 민 것을 적고, 선언에서 빠진 우리 값(값 파일 · 표에서 걷힌 이름 · `#settings-env` 를 뺀 판 · 이 자리가 안
  #   심는 이름)을 장부의 그 값 그대로일 때 걷는다(⑦ ⑧). 사외 판에서 짐의 값 파일이 든 이름인데 이 자리가 안 심은 것은 바로 위 칸이 값으로
  #   가른다 — 장부는 기록만 잇는다(`-Owned`). 짐의 값 파일이 없는 판은 걷지 않는다(`$DistComplete`).
  # 게이트웨이에서 그 값이 세션에 실제로 이기나는 사내 PC 에서 사람이 한 판 잰다(PAISetup #44 가-1 끝).
  $pushWant = [ordered]@{}
  if ($wantEnv) {
    foreach ($k in @($Planted.Keys | Sort-Object)) {
      if ($SettingsEnvSkip -contains $k) { continue }
      if ($RunnerEnvValues.ContainsKey($k)) { continue }
      if ($HumanValueNames -contains $k) { continue }   # 물음에 사람이 친 값 — 「값 파일 이름의 장부」의 ⚠
      $pushWant[$k] = $Planted[$k]
    }
  }
  $push = Sync-Planted -Ledger $Ledger -Place 'settings-env' -At $homeAt -By 'env-push' -Want $pushWant -Complete ([bool]$DistComplete) `
            -Get $EnvGet -Set $EnvSet -Remove $EnvRemove -Where 'settings.json 의 env' `
            -Owned { param($n, $c) (-not $useGateway) -and ($DistNames -contains $n) -and -not $Planted.ContainsKey($n) }
  if (& $HomeChanged $push) { $dirty = $true }
  if ($pushWant.Count) { Write-Host "  env 에 $($pushWant.Count) 개를 맞췄다 (#settings-env = yes · 키와 맡기기 러너 값은 환경변수에만 둔다)" -ForegroundColor Green }
  elseif (-not $wantEnv) { Write-Host '  env 는 안 민다 — 값 파일이 #settings-env 를 안 든다 · 앞 판이 민 우리 값은 걷는다' }
  foreach ($k in $push.Removed) { Write-Host "  $k — settings.json 에서 걷었다 (앞 판이 민 우리 값 · 이번 판은 안 민다)" -ForegroundColor Green }

  # 우리가 안 민 `ANTHROPIC_` 이름이 남아 있으면 문다(「홀로 있다」) — 사내 안내 문서가 손으로 적으라고 하는 자리라, 앞선 값이 남으면 그쪽이
  #   이겨 방금 심은 것이 가려진다. 지우지는 않는다 — 사람이 뜻을 두고 넣었을 수 있다. 우리 것은 장부에 든 밀기 줄이다(바로 위 칸이 이번
  #   판에 민 것을 적었다).
  if ($cfg.PSObject.Properties['env']) {
    $pushedNow = @(Find-LedgerRows $Ledger 'settings-env' $homeAt 'env-push' | ForEach-Object { $_.Name })
    foreach ($p in $cfg.env.PSObject.Properties) {
      if ($p.Name -notlike 'ANTHROPIC_*') { continue }
      if ($pushedNow -contains $p.Name) { continue }
      Write-Host "  ! $($p.Name) 이 settings.json 에만 있다 — 우리가 심은 값을 가릴 수 있다" -ForegroundColor Red
      Write-Host "     볼 자리: $homeCfg  (env 칸)"
      $Fails.Add("$($p.Name) 이 settings.json 에 홀로 있다")
    }
  }

  # ── 걷힌 Tavily 키 안내 — 이전 배포본이 홈 SessionStart 에 심은 한 줄을 걷는다 ──────────────────────
  # 웹 검색 · 웹 가져오기가 대부분 서서 Tavily 키가 여는 덤(사이트 지도 · 크롤 · 리서치)의 값이 작고, 웹이 못 닿은 자리는
  #   「웹 다시 찾기」 훅이 다른 길을 결과 곁에 붙인다. 그래서 안내는 안 심는다.
  # ⚠ **우리가 심은 항목만 걷는다** — 그 명령 끝의 표지(`tavily-key-hint`)로 알아본다. 표지가 없는 SessionStart 항목은
  #   사람 것이거나 설정 저장소 훅의 것이라 안 건드린다.
  if ($cfg.hooks -and $cfg.hooks.SessionStart) {
    $hintKept = @(); $hintDropped = 0
    foreach ($entry in @($cfg.hooks.SessionStart)) {
      if (-not $entry) { continue }
      $c = @($entry.hooks | Where-Object { $_ } | ForEach-Object { [string]$_.command })
      if (@($c | Where-Object { $_ -cmatch '#\s*tavily-key-hint\s*$' }).Count) { $hintDropped++ } else { $hintKept += $entry }
    }
    if ($hintDropped) {
      $cfg.hooks | Add-Member -NotePropertyName SessionStart -NotePropertyValue $hintKept -Force
      Write-Host '  Tavily 키 안내(SessionStart) — 더 안 쓰는 안내라 걷었다' -ForegroundColor Green
      $dirty = $true
    }
  }

  if ($dirty -or -not (Test-Path -LiteralPath $homeCfg)) {
    # ⚠ **BOM 없이 쓴다.** PowerShell 5.1 의 `Set-Content -Encoding UTF8` 은 BOM 을 붙이는데,
    #   JSON 을 읽는 쪽이 그 세 바이트에 걸릴 수 있다. 설정이 통째로 안 읽히면 고장이 조용하다.
    # 갈아 끼워 쓴다(`Write-FileSafely`) — 읽은 뒤 Claude · 사람이 그 파일을 고쳤으면(raced) 이 판은 안 쓰고, 다음 판이 그 글 위에서 맞춘다.
    $json = $cfg | ConvertTo-Json -Depth 10
    $homeWrote = Write-FileSafely $homeCfg ((New-Object Text.UTF8Encoding($false)).GetBytes($json)) $homeOld
    switch ($homeWrote.Did) {
      'written' { Write-Host '  썼다' -ForegroundColor Green }
      'raced'   { Write-Host "  ! settings.json — $($homeWrote.Why) · 이 판은 안 썼다 (다음 판이 맞춘다 · $homeCfg)" -ForegroundColor Yellow }
      'linked'  { Write-Host "  ! settings.json — $($homeWrote.Why) · 그 자리는 손으로 맞춘다 ($homeCfg)" -ForegroundColor Yellow }
      'overrun' { Write-Host "  ! settings.json — $($homeWrote.Why) · 그 글을 둔다 ($homeCfg)" -ForegroundColor Yellow }
      default {
        Write-Host "  ! settings.json 을 못 썼다 — $($homeWrote.Why) ($homeCfg)" -ForegroundColor Red
        $Fails.Add('홈 settings.json 을 못 썼다')
      }
    }
  } else {
    Write-Host '  이미 맞다 — 안 건드림'
  }

  # 장부 — 설정을 쓴 뒤에만 이 걸음의 줄을 쓴다(못 썼으면 디스크의 장부 그대로다 — 장부가 설정보다 앞서지 않게).
  if (-not $homeWrote -or $homeWrote.Did -ceq 'written' -or $homeWrote.Did -ceq 'same') { $null = Save-PlantLedger $Ledger }
}

} catch { Write-StepFault $_ }
Exit-Step 'home'

# ══ 걸음 「공용 자산」 ═════════════════════════════════════════════════════════════════════════
#   층 — 홈
#   하는 일 — 사내 환경 문서 · 씨앗 넷(거울로 깔거나, 설정 저장소가 들면 비켜선다) · 씨앗 판 줄 · 씨앗이 드는 파이썬 패키지
#   앞에서 받는 것 — 준비의 설정 저장소 주소 · 배포본 판(`$DistVersion`), 「프로그램」의 파이썬
#   안 하는 것 — 도구별 홈
# 고를 것이 아니라 환경이라 스위치가 없다 — 사내 게이트웨이의 배선 · 오류 명세와, 복사해 출발하는 씨앗은 누가 받아도 쓴다.
# 홈에 깐다 — zip 이 풀린 자리는 바탕화면 폴더를 지우면 사라지고, 스킬과 형제 저장소 문서가 가리키는 `claude-config/posco/` 는
#   저장소가 없는 기계에 없다. 규범 · 룰 · 스킬과 같은 꼴이다 — 진본은 저장소, 로드 자리는 홈. 저장소를 든 사람은 `deploy.ps1` 이
#   이 자리를 갱신하고 `check-global-copies.sh` 가 바이트로 잰다 — 재는 자가 붙은 사본이라 조용히 안 낡는다.
Enter-Step 'assets'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)
# ⚠ **씨앗 넷은 거울로 깐다 — 덮어쓰기가 아니다.** `Copy-Item -Recurse -Force` 는 원본에 없는 파일을 안 지운다. 진본에서 부품
#   하나를 걷어도 한 번 깐 기계에는 영영 남고, 씨앗은 있으면 복사되는 자리라 걷힌 것이 계속 새 프로젝트로 퍼진다(「값 파일 이름의 장부」
#   칸의 「심기는 더하기만 한다」와 같은 병).
# ⚠ **설정 저장소가 미는 자리에서는 비켜선다.** 그 저장소의 배포(`deploy.ps1`)와 세션 훅이 `deploy.seeds.conf` 에 적힌 폴더를 저장소
#   최신판으로 같은 자리에 민다 — 둘 다 깔면 이 칸이 릴리스 판으로 되돌리고 저쪽이 다시 미는 일이 자동 실행마다 되풀이되어, 매번
#   「덮어씀」과 백업 폴더가 쌓이고 판 줄(`seeds/.version`)이 튄다. 무엇을 미나는 저장소의 선언(`deploy.seeds.conf` — 배포 · 세션 훅이
#   같은 줄을 읽는다)을 읽는다 — 목록을 따로 들면 저쪽이 폴더를 더하거나 뺀 날 조용히 어긋난다. 홈 자리가 비었으면 비켜서지 않는다 —
#   우리가 깔고, 뒤따르는 배포가 새 판으로 덮는다. 비켜선 자리에서 원본이 걷은 파일을 걷는 손은 저쪽 배포다(`deploy.ps1` 씨앗 칸).
# ⚠ **`posco` 는 거울이 아니라 장부로 맞춘다** (PAISetup #44 ⑭). 그 자리에는 남의 파일이 같이 산다 — 프록시가 제 곁에
#   `opus5_proxy.pid` 와 `proxy.log` 를 쓰고, 시험이 제 결과를 쓴다. 거울로 걷으면 그 파일을 지운다. 그래서 덮어 깔고, 우리가 놓았다고
#   장부에 적은 파일 가운데 원본에서 빠진 것만 걷는다(`Sync-AssetLedger`).
$envAssets = @(
  @{ From = Join-Path $Here 'posco';         To = Join-Path $homeDir 'posco'; Mirror = $false; Ledger = $true
     Name = '사내 환경 문서'; Desc = '게이트웨이·API·오류 기록 — 붙이기 전에 읽는다' }
  @{ From = Join-Path $Here 'seeds\gateway'; To = Join-Path $homeDir 'seeds\gateway'; Mirror = $true
     Name = '게이트웨이 씨앗'; Desc = '새 프로젝트가 복사해서 출발한다' }
  @{ From = Join-Path $Here 'seeds\check';   To = Join-Path $homeDir 'seeds\check'; Mirror = $true
     Name = '검사 씨앗';       Desc = '검사 부품과 어느 저장소에서나 도는 게이트의 진본 — 받아 간 사본은 여기를 가리킨다' }
  # 이것도 스위치를 안 둔다 — 설치 창의 「설정 저장소」 칸을 쓸 사람만 보지만, 칸을 채우려면 저장소가 이미 있어야 하고 그 저장소를
  #   만드는 골든이 이것이다. 켜는 칸으로 두면 안 켠 사람은 그 칸을 채울 길을 못 찾는다.
  @{ From = Join-Path $Here 'seeds\config-repo'; To = $ConfigSeedHome; Mirror = $true
     Name = '설정 저장소 씨앗'; Desc = '「설정 저장소」 칸이 기대하는 저장소를 만드는 골든' }
  # 회사가 쓴 사내 FastAPI 코딩 기준 — 스킬 `inhouse-app`(제작자 칸을 켠 사람)이 이 자리의 장을 연다.
  # 스킬을 안 켠 사람에게도 깐다 — 사내 환경 문서(`posco/README.md`)와 이 씨앗의 `SEED.md` 가 이 자리를 가리키므로, 그 좌표가
  #   가리킬 자리가 홈에 서야 한다(claude-config 결정 0074 · 0075).
  @{ From = Join-Path $Here 'seeds\vibecoding'; To = Join-Path $homeDir 'seeds\vibecoding'; Mirror = $true
     Name = '사내 코딩 기준 씨앗'; Desc = '사내 앱을 회사 방식으로 배포할 때 스킬 inhouse-app 이 여는 회사 기준 본문 — 들머리는 SEED.md' }
)
# ── 홈 씨앗의 임자 — 찾는 자 하나가 정한다 (PAISetup #48 ①) ──────────────────────────────────
# 임자는 설정 저장소 찾는 자(`.githooks/claude-config-path.sh` 의 `CONFIG_ROOT`)가 찾은 저장소이고, 그 저장소가 그 폴더를 선언했을 때만이다
#   — 세션 훅과 그 훅이 넘기는 `deploy.ps1` 이 같은 자를 쓴다. 값 파일의 주소(`#config-repo`)로 가르면 주소 없는 판(콘솔로 깐 판)이 씨앗을
#   릴리스 판으로 되돌리고, 세션 훅은 바뀐 파일만 밀어 다음 통째 판까지 일부가 옛 판에 머문다.
# 찾는 자는 이 짐의 것을 부른다(`Get-ConfigRootGen` — 「설정 저장소」 걸음이 넘길 자리를 재는 그 손) — 홈 사본은 이 걸음이 바로 아래에서
#   같은 판으로 깐다. 묻는 자리는 세션이 열릴 자리다 — 받을 저장소마다, 그리고 작업 루트(`$configRepoRoot`) 아래 아무 자리(찾는 자는 그
#   자리 곁의 저장소를 본다 · 그 자리는 없어도 된다). 처음 까는 판은 저장소가 아직 없어 임자가 없고, 뒤따르는 배포가 새 판으로 덮는다.
# Git Bash 가 없으면 묻지 않는다 — 세션 훅도 bash 라 그 PC 에서는 밀 자가 없다. 묻다 졌으면 노란 줄을 내고 설치 묶음 판으로 깐다 —
#   비켜서면 임자 없는 PC 의 씨앗이 영영 안 바뀐다.
$ownerBash  = Find-GitBash
$ownerRoots = @(); $ownerWhy = ''
if ($ownerBash) {
  $ownerFinder = Join-Path $Here 'seeds\config-repo\.githooks\claude-config-path.sh'
  foreach ($pd in @(@($configRepoUrls | ForEach-Object { Get-ConfigRepoDir $_ }) + @(Join-Path $configRepoRoot '.paisetup-owner-probe'))) {
    $c = Get-ConfigRootGen $pd $ownerBash $ownerFinder
    if ($c.Root -and (Test-Path -LiteralPath $c.Root -PathType Container)) {
      if (-not @($ownerRoots | Where-Object { $_ -ieq $c.Root }).Count) { $ownerRoots += $c.Root }
    } elseif (-not $c.Current -and -not $ownerWhy) { $ownerWhy = $c.Why }
  }
}
if ($ownerWhy -and -not $ownerRoots.Count) { Write-Host "  ! 씨앗의 임자(설정 저장소)를 못 가렸다 — 설치 묶음 판으로 깐다 ($ownerWhy)" -ForegroundColor Yellow }
# 임자가 홈으로 미는 자리 — `seeds\gateway` 꼴의 홈 상대 경로 → 그것을 든 저장소. 세션 훅의 문과 같다: 선언에 든 줄이고 그 저장소에 그 폴더가 있다.
$ownedHome = @{}
foreach ($d in $ownerRoots) {
  $conf = Join-Path $d 'deploy.seeds.conf'
  if (-not (Test-Path -LiteralPath $conf -PathType Leaf)) { continue }
  foreach ($ln in (Get-Content -LiteralPath $conf -Encoding UTF8)) {
    $rel = (($ln -replace '#.*$', '').Trim()) -replace '/', '\'
    if ($rel -and -not $ownedHome.ContainsKey($rel) -and (Test-Path -LiteralPath (Join-Path $d $rel))) {
      $ownedHome[$rel] = $d
    }
  }
}
foreach ($a in $envAssets) {
  if (-not (Test-Path -LiteralPath $a.From)) { Write-Host "  $($a.Name) — 이 폴더에 없다"; continue }
  $a.Rel = $a.To.Substring($homeDir.Length).TrimStart('\')
  $owner = $ownedHome[$a.Rel]
  if ($owner -and @(Get-ChildItem -LiteralPath $a.To -Recurse -File -ErrorAction SilentlyContinue).Count) {
    $a.Owner = $owner
    # 장부의 그 자리 줄은 걷는다 — 그 자리는 이제 저쪽이 미는 판이라, 줄을 두면 임자가 사라진 뒤의 판이 저쪽이 고친 파일을 사람 것으로 읽는다
    if ($a.Ledger) { $null = Sync-AssetLedger $a -Drop }
    Write-Host "  $($a.Name) — 설정 저장소가 들고 있어 비켜선다" -ForegroundColor Green
    Write-Host "     $owner"
    continue
  }
  # ⚠ **못 걷었으면 실패로 센다.** 복사는 그대로 해 모자란 것은 채우지만, 걷기가 진 자리에는 걷힌 부품이 남고 끝 검증은 모자란
  #   것만 물어 여분을 안 문다 — `$Fails` 에 안 적으면 거울이 안 선 판이 초록으로 통과한다.
  if ($a.Mirror -and (Test-Path -LiteralPath $a.To)) {
    try { Remove-Item -LiteralPath $a.To -Recurse -Force -ErrorAction Stop }
    catch {
      Write-Host "  ! $($a.Name) 옛 사본을 못 걷었다 — $(Say-Why $_)" -ForegroundColor Red
      $Fails.Add("$($a.Name) (옛 사본 걷기)")
    }
  }
  New-Item -ItemType Directory -Path $a.To -Force | Out-Null
  Copy-Item -Path (Join-Path $a.From '*') -Destination $a.To -Recurse -Force
  $swept = if ($a.Ledger) { Sync-AssetLedger $a } else { 0 }
  Write-Host "  $($a.Name) — $(if ($a.Mirror) { '거울로 깔았다' } elseif ($swept) { "깔았다 (원본에서 빠진 파일 $swept 개를 걷었다)" } else { '깔았다' })" -ForegroundColor Green
  Write-Host "     $($a.To)"
  Write-Host "     $($a.Desc)"
}

# ── 씨앗의 판 줄 — 홈 사본이 **어느 판에서 왔나**를 그 자리에 남긴다 ──────────────
# 홈 사본을 진본으로 믿고 재는 자가 있다(`seeds/check/_check/borrowed_check.py`) — 홈 뿌리는 git 나무가 아니라 판을 물을 데가
#   없어, 이 줄이 없으면 그 자는 오늘 날짜를 내고 낡은 홈과 견준 초록이 최신처럼 읽힌다.
# 여기가 적는 것은 릴리스 판이다 — 설정 저장소를 든 사람 자리에서는 같은 파일에 세션 훅 몸통(`session-start-body.sh`) ·
#   `deploy.ps1` 이 커밋 해시를 적는다. 값은 둘이어도 묻는 물음(「이 홈 사본이 어디서 왔나」)은 같다.
# ⚠ **판이 그대로면 안 쓴다.** 날짜 칸은 「이 판이 홈에 깔린 날」이고 돌린 날이 아니다 — 자동 실행이 매일 도는 자리라, 매번
#   덮으면 그 날짜가 늘 오늘이라 낡음을 말하지 않는다. 씨앗을 민 뒤에 적어야 「그 판이 깔렸다」가 참이다.
# ⚠ **씨앗 하나라도 설정 저장소가 들면 안 쓴다** — 그 자리의 판 줄은 저쪽 배포가 커밋 해시로 적는다. 여기서 판 번호로 덮으면
#   위 비켜서기를 해도 이 한 줄이 매번 튄다.
$seedRoot = Join-Path $homeDir 'seeds'
$seedOwned = [bool]@($envAssets | Where-Object { $_.Owner -and $_.To -like "$seedRoot\*" }).Count
if ((Test-Path -LiteralPath $seedRoot) -and $DistVersion -and -not $seedOwned) {
  $seedVerFile = Join-Path $seedRoot '.version'
  $seedVerNow = ''
  if (Test-Path -LiteralPath $seedVerFile) {
    try {
      $seedVerNow = (([string](Get-Content -LiteralPath $seedVerFile -TotalCount 1 -Encoding UTF8)) `
                      -replace "^﻿", '').Trim().Split(' ')[0]
    } catch { $seedVerNow = '' }
  }
  if ($seedVerNow -ne $DistVersion) {
    # ⚠ **BOM 없이 쓴다** — 읽는 자가 파이썬이고, 그 세 바이트가 판 번호 앞에 붙으면
    #   화면에는 멀쩡히 찍히고 견주는 자리에서만 안 맞는다.
    $seedVerLine = "$DistVersion $(Get-Date -Format 'yyyy-MM-dd')`n"
    [IO.File]::WriteAllText($seedVerFile, $seedVerLine, (New-Object Text.UTF8Encoding($false)))
    Write-Host "  씨앗 판 줄 — $DistVersion" -ForegroundColor Green
  }
}

# ── 씨앗이 드는 파이썬 패키지 — **부품이 오는 자리에 의존성도 온다** (claude-config #72) ──────
# 검사 씨앗의 그림 줄이기(`_shrink.py`)가 PIL 을 든다. 부르는 자는 모델이지만 그 길을 여는 것은
# 위 그림 문이다 — 그림이 크면 누구의 PC 에서든 「줄여서 연다」로 돌려보낸다. 그래서 규범·룰·
# 스킬 칸이 아니라 여기 선다: 부품도 문도 스위치를 안 타니 의존성도 안 탄다.
# 이름은 이 파일에 없다 — 값 파일의 `#pip-packages = 이름 …` 이 들고, 몸통은 까는 법만 안다(`#gateway-proxy` · `#codex-config` 와
#   같은 결). 읽는 값 파일은 배포본의 것이다(`$DistEnvFile` 곁말).
# ⚠ **`pip` 가 아니라 `python -m pip` 로 깐다.** `pip` 를 따로 부르면 어느 파이썬의 것인지 PATH 가 따로 정해, 부품을 부르는
#   `python` 과 갈릴 수 있다.
# 못 깔아도 빨강으로 안 끝낸다 — 회사망이 패키지 저장소를 막는 자리가 있고, 없으면 줄이기가 「PIL 이 없다」와 까는 명령을 대며
#   원본 치수로 물러나 조용히 무너지지 않는다. 말은 하고 뱉은 끝 줄을 편다. 막힌 망에 오래 붙잡히지 않게 기다림과 되풀이를 줄인다.
#   이미 있으면 pip 가 망에 안 묻고 끝나 로그온 자동 실행이 매번 불러도 된다.
$pipLine = Read-Directive $DistEnvFile 'pip-packages'
$pipPkgs = @(if ($pipLine) { $pipLine -split '[,\s]+' | Where-Object { $_ } })
if ($pipPkgs) {
  $pipNames = $pipPkgs -join ' · '
  # ⚠ **못 쟀으면 건너뛰지 않는다** — 넘김을 「없다」로 읽고 건너뛰면 값 파일이 청한 패키지가 끝 검증에도 안 잡힌 채
  #   초록으로 끝난다. 「안 한 걸음」으로 남긴다(결정 0141).
  $pipPython = Measure-Runs 'python' '--version'
  if ($pipPython -eq 'unmeasured') {
    Add-UnmeasuredStep "파이썬 패키지($pipNames)" 'python --version' '깔지 않았다'
  } elseif ($pipPython -ne 'yes') {
    Write-Host "  파이썬 패키지($pipNames) — 건너뛴다: 이 창에서 python 이 안 선다"
  } else {
    $pl = [IO.Path]::GetTempFileName()
    $pipArgs = @('-m', 'pip', 'install', '--disable-pip-version-check', '--no-input',
                 '--timeout', '15', '--retries', '1') + $pipPkgs
    # ⚠ **빈 작업 폴더에서 부른다** — `-m` 은 작업 폴더를 `sys.path` 맨 앞에 둬, 그 폴더의 `pip.py` · `pip/` 가 돈다. `-P` 는 3.11 앞
    #   판이 못 받고 `-I` 는 사용자 자리(`--user` 꼴 설치의 자리)를 버리므로, 이 회차가 지은 빈 폴더로 옮겨 부른다.
    $pipCwd = Join-Path ([IO.Path]::GetTempPath()) ("claude-setup-pip-$PID")
    $prc = -1
    try {
      New-Item -ItemType Directory -Path $pipCwd -Force | Out-Null
      Push-Location -LiteralPath $pipCwd
      try { $prc = Invoke-Logged 'python' $pipArgs $pl } finally { Pop-Location }
    } catch {
      # 빈 폴더를 못 지었거나 못 옮겼다 — 작업 폴더째 부르지 않고 못 깐 것으로 남긴다(아래 노란 줄이 종료 -1 로 말한다).
      [IO.File]::WriteAllText($pl, "빈 작업 폴더를 못 지어 안 불렀다 ($pipCwd) — $($_.Exception.Message)")
    } finally { Remove-Item -LiteralPath $pipCwd -Recurse -Force -ErrorAction SilentlyContinue }
    if ($prc -eq 0) {
      Write-Host "  파이썬 패키지 — $pipNames 섰다" -ForegroundColor Green
    } else {
      Write-Host "  ! 파이썬 패키지($pipNames) — 못 깔았다(종료 $prc). 그림 줄이기는 원본 치수로 물러난다 · pip 가 뱉은 끝 줄:" -ForegroundColor Yellow
      Show-Log $pl
    }
    Remove-Item $pl -ErrorAction SilentlyContinue
  }
}

} catch { Write-StepFault $_ }
Exit-Step 'assets'

# ══ 걸음 「도구별 홈」 ═════════════════════════════════════════════════════════════════════════
#   층 — 홈
#   하는 일 — 제작자 칸 값 · 고른 제품 값 · 자리 값 · 규범 · 룰 · 에이전트 · 스킬 · Claude 훅 등록(짐의 손 `tool-homes.py` 를 부른다 —
#     표준 층과 세 도구 홈) · 칸 없이 까는 스킬(제작자 칸에 안 든 도구의 홈) · Claude(걷힌 룰) · agy(훅 — 안 골랐으면 걷기) ·
#     Codex(훅 병합과 신뢰 — 안 골랐으면 걷기) · 묻지 않고 돌기(고른 agy · Copilot · Codex 의 제 승인 설정) · 그 값과 Codex 데스크탑 샌드박스
#     키의 장부(안 고르게 되면 장부의 우리 값만 걷는다) · 이 판의 마지막 장부 쓰기
#   앞에서 받는 것 — 준비의 짐(`$Kit` — 손과 그 표가 뿌리에 실린다), 「공용 자산」의 씨앗(훅 몸통 · 병합기 · 어댑터)
#   안 하는 것 — 설정 저장소를 안 받는다 · 홈 `settings.json` 을 쓰지 않는다(손만 쓴다 — 「Claude 홈 설정」 머리의 ⚠)
#   ⚠ 제작자 칸 값(`PAISETUP_PERSONAL`)과 고른 제품 값(`PAISETUP_PICK`)은 사용자 환경에 심지만 이 걸음에 선다 — 「Claude 홈
#     설정」 뒤라 settings.json 의 env 로 안 밀리고, 손이 그 값을 읽으며, 「설정 저장소」의 배포가 이 프로세스에서 그 값을 물려받는다
# 제작자 세트(개인 규범 · 룰 · 에이전트 · 스킬)는 기본으로 안 깐다 — 한 사람의 사유 방식이라 제작자 칸에서 그 도구를 켤 때만
#   선다. 손이 칸을 읽어 도구마다 놓는다.

Enter-Step 'tools'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)
# 고른 도구와 고른 제품 — 손(`tool-homes.py`) · 설정 저장소의 배포(`deploy.ps1`) · 세션 훅이 같은 값을 읽는다. 제작자 칸은 어느
# 도구 홈을 개인화할지를(결정 0107 · 0112), 고른 제품은 어느 도구에 우리 훅을 놓을지를(결정 0102) 정한다.
foreach ($pv in @(@{ Name = 'PAISETUP_PERSONAL'; Value = $PersonalValue }, @{ Name = 'PAISETUP_PICK'; Value = $PickValue })) {
  if ([Environment]::GetEnvironmentVariable($pv.Name, 'User') -eq $pv.Value) {
    # ⚠ **이 프로세스의 값도 맞춘다** — 뒤의 설정 저장소 배포(「설정 저장소」 걸음)는 이 프로세스의 자식이라 그 값을 물려받는다.
    #   지금의 배포는 사용자 값을 먼저 읽지만, 포크한 설정 저장소는 사람이 당기기 전까지 프로세스 값을 먼저 읽는 판을 든다 — 오래
    #   떠 있던 앱에서 부르면 프로세스에 앞선 값이 남아, 그 판의 배포가 끈 도구로 읽고 개인화를 걷는다. 그런 포크가 남는 동안 든다.
    Set-Item -Path "Env:$($pv.Name)" -Value $pv.Value
    Write-Host "  $($pv.Name) — 이미 맞다 ($($pv.Value))"
  } else {
    Plant-Var $pv.Name $pv.Value
  }
}
# 자리 — 맡기는 세션이 맡기기 모델 표(스킬 `agent-envelope`)에서 읽을 자리 줄(claude-config 결정 0123). 「키와 값」이 러너의
#   자리 값을 고른 그 줄이다. 위 두 값처럼 이 걸음에 심어 settings.json 의 env 로 안 밀린다 — 밀리면 자리를 옮긴 PC 에서 앞선
#   자리가 그 파일에 남아 사용자 값을 가린다.
if ([Environment]::GetEnvironmentVariable('PAISETUP_SITE', 'User') -eq $ModelSite) {
  Set-Item -Path 'Env:PAISETUP_SITE' -Value $ModelSite
  Write-Host "  PAISETUP_SITE — 이미 맞다 ($ModelSite)"
} else {
  Plant-Var 'PAISETUP_SITE' $ModelSite
}
# ── 규범 · 룰 · 에이전트 · 스킬 · Claude 훅 등록 — 짐의 손(`tool-homes.py`)이 표준 층을 채우고 도구 홈에 놓는다 (claude-config 결정 0112) ──
# 무엇이 어느 홈에 어떤 꼴로 가나 · 칸을 끈 도구와 뺀 제품에서 무엇을 걷나는 손과 그 표(`tool-homes.conf`)가 든다 — 손의 머리말.
# 설정 저장소를 넣었어도 비켜서지 않는다 — 그 저장소의 배포가 채운 개인 층이 항목마다 이기고, 놓기는 이긴 층의 손이 한다.
# ⚠ **두 값을 심은 뒤에 부른다** — 손은 사용자 환경의 `PAISETUP_PERSONAL` · `PAISETUP_PICK`(바로 위에서 심었다)을 읽는다.
# 손이 짐에 없으면 빨강이다 — 짐이 깨졌다는 뜻이라, 건너뛰고 초록으로 끝나면 아무도 모른다.
# 켠 칸이 없고 Claude 를 안 골랐고 python 이 안 서면 건너뛴다 — 그때 손이 할 일은 끈 칸 · 뺀 제품의 우리 것 걷기뿐이다. 칸을 켰거나
#   Claude 를 골랐으면 python 은 「프로그램」 걸음이 `-NoDevTools` 여도 깔았으므로(`$needPythonWhy`), 여기서 안 서면 빨강이다.
# ⚠ **python 을 못 쟀으면 건너뛰지 않는다** — 넘김을 「없다」로 읽고 건너뛰면 끈 칸 · 뺀 제품의 우리 것이 안 걷힌 채
#   초록으로 끝난다. 손을 부르지도 건너뛰지도 않고 「안 한 걸음」으로 남긴다(결정 0141).
$toolHomesHand   = Join-Path $Kit 'tool-homes.py'
$toolHomesProbe  = Measure-Runs 'python' '--version'
$toolHomesPython = ($toolHomesProbe -eq 'yes')
$toolHomesOn     = [bool]($personalAny -or $hostClaude -or $toolHomesPython)
if (-not $toolHomesOn -and $toolHomesProbe -ne 'unmeasured') {
  Write-Host '  규범 · 룰 · 에이전트 · 스킬 — 건너뜀 (python 이 안 서고, 켠 제작자 칸도 고른 Claude 도 없다)'
} elseif (-not (Test-Path -LiteralPath $toolHomesHand -PathType Leaf)) {
  Write-Host "  ! 규범 · 룰 · 에이전트 · 스킬 — 짐에 없다 ($toolHomesHand)" -ForegroundColor Red
  $Fails.Add('규범 · 룰 · 에이전트 · 스킬 (짐에 없음)')
} elseif ($toolHomesProbe -eq 'unmeasured') {
  Add-UnmeasuredStep '규범 · 룰 · 에이전트 · 스킬' 'python --version' '손을 안 불렀다 — 놓기도, 끈 칸 · 뺀 제품의 우리 것 걷기도 안 했다'
} elseif (-not $toolHomesPython) {
  Write-Host '  ! 규범 · 룰 · 에이전트 · 스킬 — python 이 안 서서 손을 못 댔다' -ForegroundColor Red
  $Fails.Add('규범 · 룰 · 에이전트 · 스킬 (python 없음)')
} else {
  $th = Invoke-ToolHomes $toolHomesHand @('sync', '--layer', 'standard', '--from', $Kit)
  if ($th.Rc -ne 0 -or $th.Errors.Count) {
    Write-Host "  ! 규범 · 룰 · 에이전트 · 스킬 — 손이 다 못 놓았다 (종료 $($th.Rc))" -ForegroundColor Red
    $Fails.Add('규범 · 룰 · 에이전트 · 스킬 (손이 다 못 놓았다)')
  } elseif ($th.Changes.Count) {
    Write-Host "  규범 · 룰 · 에이전트 · 스킬 — 맞췄다 (제작자 칸 $PersonalValue · 고른 제품 $PickValue)" -ForegroundColor Green
  } else {
    Write-Host "  규범 · 룰 · 에이전트 · 스킬 — 이미 맞다 (제작자 칸 $PersonalValue · 고른 제품 $PickValue)"
  }
  Show-ToolHomesLines $th.Lines
}

# ── 칸 없이 까는 스킬 — 위 `$FreeSkills` · `$FreeSkillHomes` (결정 0091 · 0097 · 0099) ─────────────────────────
# 도구 홈마다 `Install-FreeSkills` 한 번 — 그 도구가 제작자 칸에 들면 아무것도 안 한다(그 홈은 위 손이 쓴다). 무엇을 깔고
#   걷나 · 우리 것이 무엇인가는 그 함수의 곁말이 든다.
# ⚠ **손 다음에 돈다** — 칸은 설치 창이 바꾸므로 넘겨받기가 이 한 판 안에서 끝난다: 끈 홈은 손이 제 것을 걷은 뒤 여기서
#   칸 없이 까는 것을 깔고, 켠 홈은 손이 이 걸음의 사본을 처음 만남으로 받아 그 기록을 옮긴다.
foreach ($t in $FreeSkillHomes.Keys) { Install-FreeSkills $t }

# ── 걷힌 회사 기준 룰을 홈에서 걷는다 ─────────────────────────────────────────
# 회사 코딩 기준에서 구운 룰 `futurem-*.md`(1.30.0 이 영역 룰로 깐 것)는 스킬 `inhouse-app` 으로 바뀌었다(claude-config 결정 0075).
#   룰을 놓는 손(`tool-homes.py`)은 제 기록(`placed.tsv`)에 든 파일만 걷어, 기록이 서기 전에 깐 그 룰은 홈에 남아 사내 앱의 폴더를
#   만질 때마다 실린다 — 그것을 여기서 걷는다. 1.30.0 으로 깐 홈이 남는 동안 든다.
# ⚠ **구운 표식이 머리에 있는 것만 걷는다 — 앞 20줄을 본다.** 같은 이름을 사람이 손수 두었을 수 있다. 표식은 굽는 자가 머리말
#   바로 뒤 주석에 박던 문장이고, 공통 규약 룰은 머리말의 경로가 여섯 줄이라 표식이 11번째 줄에 선다 — 앞 몇 줄만 읽으면 그 한 장이
#   안 걷힌다.
# 제작자 칸을 안 켠 판에서도 돈다 — 켜고 깐 사람이 이번에 끄고 돌려도 걷혀야 한다. 지우지 않고 옮긴다
#   (`~/.claude/backups/install-rules-<시각>/`) — 스킬 걷기와 같은 까닭이다.
$retiredRuleMark = '생성물 — scripts/pull-vibecoding.sh 가 씨앗의'
$ruleHome = Join-Path $homeDir 'rules'
$staleRules = @(Get-ChildItem -LiteralPath $ruleHome -Filter 'futurem-*.md' -File -ErrorAction SilentlyContinue |
  Where-Object {
    -not (Test-Path -LiteralPath (Join-Path $Kit "norms\rules\$($_.Name)")) -and
    (@(Get-Content -LiteralPath $_.FullName -TotalCount 20 -Encoding UTF8 -ErrorAction SilentlyContinue) -join "`n").Contains($retiredRuleMark)
  })
if ($staleRules.Count -gt 0) {
  $bk = Join-Path (Join-Path $homeDir 'backups') ("install-rules-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
  New-Item -ItemType Directory -Path $bk -Force | Out-Null
  foreach ($r in $staleRules) {
    Move-Item -LiteralPath $r.FullName -Destination (Join-Path $bk $r.Name) -Force
    Write-Host "  룰 $($r.Name) — 스킬로 바뀌어 걷었다 (옮긴 자리: $bk)" -ForegroundColor Green
  }
}

# ── Codex 훅 — 씨앗 예시의 우리 훅을 config.toml 에 병합한다 ─────────
# 무엇을 거나는 예시(`codex-hooks.example.toml`)가 든다 — 여기 이름을 늘어놓지 않는다. 늘어놓으면 예시에 훅이 는 날 이 글만 낡는다.
# 두 자리 다 돈다 — 사내는 위 틀이 이미 같은 블록을 들어 고칠 것이 없고, 사외는 사람이 쓴 설정에 우리 항목만
# 얹는다. 병합 규칙의 진본은 씨앗의 `codex-hook-install.py` · `codex-hooks.example.toml` 이다 — 우리 항목만
# 갈고 남의 훅 · 다른 표는 뜻 그대로 두며, 결과가 그 뜻으로 다시 읽힐 때만 쓴다. 못 알아보는 꼴로 적힌
# 이벤트는 건너뛰고(SKIP), 끝 검증이 그 빠진 배선을 [X] 로 알린다.
# ⚠ **stderr 를 합치지 않는다** — 맨 위 규칙(`2>&1`). 글자는 `Invoke-Logged` 가 파일로 받고, 실패했을 때만 편다.
if ($PickKeys -contains 'codex') {
  $codexHookDir = $ConfigSeedHooks
  $codexHookPlant = Join-Path $codexHookDir 'codex-hook-install.py'
  $codexHookExample = Join-Path $ConfigSeedHome 'codex-hooks.example.toml'
  if (-not (Test-Path -LiteralPath $codexHookPlant) -or -not (Test-Path -LiteralPath $codexHookExample)) {
    Write-Host '  ! Codex 훅 — 씨앗의 병합기나 예시가 없어 안 심는다' -ForegroundColor Red
    $Fails.Add('Codex 훅 (씨앗이 없다)')
  } elseif (($codexHookPython = Measure-Runs 'python' '--version') -eq 'unmeasured') {
    Add-UnmeasuredStep 'Codex 훅' 'python --version' '심지도 건너뛰지도 않았다'
  } elseif ($codexHookPython -ne 'yes') {
    Write-Host '  ! Codex 훅 — python 이 안 서서 안 심는다' -ForegroundColor Red
    $Fails.Add('Codex 훅 (python 없음)')
  } else {
    $codexHookLog = [IO.Path]::GetTempFileName()
    try {
      $codexHookRc = Invoke-Logged 'python' @('-X', 'utf8', $codexHookPlant, '--config', $CodexCfg, '--example', $codexHookExample) $codexHookLog
      $codexHookOut = @(Get-Content -LiteralPath $codexHookLog -ErrorAction SilentlyContinue |
                        ForEach-Object { "$_".Trim() } | Where-Object { $_ })
      if ($codexHookRc -ne 0) {
        Write-Host '  ! Codex 훅 병합 실패 — config.toml 은 그대로다. 병합기가 뱉은 끝 줄:' -ForegroundColor Red
        Show-Log $codexHookLog
        $Fails.Add('Codex 훅 (config.toml 병합 실패)')
      } else {
        $skipped = @($codexHookOut | Where-Object { $_ -like 'SKIP=*' })
        if ($skipped.Count) {
          Write-Host "  ! Codex 훅 — 못 알아보는 꼴로 적힌 이벤트는 안 건드렸다: $($skipped -join ' ')" -ForegroundColor Yellow
        } elseif ($codexHookOut -contains 'CHANGED=1') {
          Write-Host '  Codex 훅 — 씨앗 예시(codex-hooks.example.toml)의 우리 훅을 config.toml 에 심었다' -ForegroundColor Green
          $codexHookBak = @($codexHookOut | Where-Object { $_ -like 'BACKUP=*' }) | Select-Object -First 1
          if ($codexHookBak) { Write-Host "     고치기 전 것은 $($codexHookBak.Substring(7)) 에 떠 뒀다" }
        } else {
          Write-Host '  Codex 훅 — 이미 맞다'
        }
      }
    } finally { Remove-Item -LiteralPath $codexHookLog -ErrorAction SilentlyContinue }
    # ── 신뢰 — Codex 를 고르면 우리 훅에 신뢰까지 적는다 (claude-config 결정 0106) ──
    # Codex 는 신뢰한 사용자 훅만 돌린다 — 대화형 시작은 묻지만 `codex exec`(다른 도구가 Codex 에 일을 맡기는 길)는
    # 말없이 건너뛴다. 배선만 세우면 고른 기능이 반쯤 죽은 채 끝나서, 신뢰 적기까지가 이 칸의 일이다. 씨앗의
    # `codex-hook-trust.py` 가 Codex 제 설정 쓰기로 우리 훅에만 적는다 — 남의 훅 · 사람이 끈 우리 훅은 둔다.
    # 해시는 Codex 가 낸 값을 그대로 되돌려 적을 뿐이다. 적은 명령은 아래에 그대로 찍어 기록에 남긴다.
    # 홈은 Codex 가 고르는 차례(`CODEX_HOME` → `~/.codex`)를 그대로 따른다 — Codex 가 실제로 읽는 설정에 적는다.
    # 끝 검증이 같은 손(`status`)으로 Codex 가 읽은 상태를 다시 잰다 — 여기서 못 적었으면 거기서 [X] 로 남는다.
    $codexTrustPlant = Join-Path $codexHookDir 'codex-hook-trust.py'
    if (-not (Test-Path -LiteralPath $codexTrustPlant)) {
      Write-Host '  ! Codex 훅 신뢰 — 씨앗에 신뢰 도우미가 없어 못 적었다' -ForegroundColor Red
      $Fails.Add('Codex 훅 신뢰 (씨앗이 없다)')
    } else {
      $codexTrustLog = [IO.Path]::GetTempFileName()
      try {
        $codexTrustRc = Invoke-Logged 'python' @('-X', 'utf8', $codexTrustPlant, 'trust', '--example', $codexHookExample) $codexTrustLog
        $codexTrustOut = @(Get-Content -LiteralPath $codexTrustLog -Encoding UTF8 -ErrorAction SilentlyContinue |
                           ForEach-Object { "$_".Trim() } | Where-Object { $_ })
      } finally { Remove-Item -LiteralPath $codexTrustLog -ErrorAction SilentlyContinue }
      $codexTrustNow = @($codexTrustOut | Where-Object { $_ -like 'TRUSTED_NOW=*' })
      foreach ($ln in $codexTrustNow) {
        Write-Host "  Codex 훅 신뢰 — 적었다: $($ln.Substring('TRUSTED_NOW='.Length))" -ForegroundColor Green
      }
      if ($codexTrustRc -eq 0) {
        if (-not $codexTrustNow.Count) { Write-Host '  Codex 훅 신뢰 — 이미 맞다' }
      } else {
        $codexTrustWhy = @($codexTrustOut | Where-Object { $_ -like 'UNMEASURED=*' -or $_ -like 'ERROR=*' }) | Select-Object -Last 1
        Write-Host "  ! Codex 훅 신뢰 — 못 적었다 ($(if ($codexTrustWhy) { $codexTrustWhy } else { "종료 $codexTrustRc" })). Codex 를 열어 새 훅을 한 번 신뢰한다" -ForegroundColor Red
        $Fails.Add('Codex 훅 신뢰 (못 적었다)')
      }
    }
  }
} else {
  # 안 골랐으면 우리 훅만 걷는다 — 병합기의 걷기 판이 뒤 항목의 자리(신뢰 열쇠)를 그대로 두고(결정 0103), Codex 가 적은 신뢰
  #   (`[hooks.state]`)는 안 건드린다. 병합기는 고친 결과를 TOML 로 다시 읽어 뜻을 잰 뒤에만 써서 파이썬 3.11(`tomllib`)이 든다.
  Remove-UnpickedHooks 'Codex 훅' $CodexCfg @((Join-Path $ConfigSeedHooks 'codex-hook-install.py')) `
                       @('--config', $CodexCfg, '--remove') @('-I', '-c', 'import tomllib') '파이썬 3.11 이상(tomllib)이'
}

# ── agy 훅 — 씨앗 어댑터의 우리 훅을 ~/.gemini/config/hooks.json 에 얹는다 (결정 0099) ─────────────────
# 안티그래비티를 고르면 선다 — 자리는 안 가린다(사내 agy CLI 도 같은 홈 설정을 읽는다 · 결정 0086). 배선의 진본은 씨앗의
# `agy-hooks.py` 다: 우리 이름(`paisetup-…`)의 항목만 얹고 남의 항목은 두며, 사람이 끈 우리 항목은 꺼진 채 둔다.
# ⚠ **씨앗 자리의 것을 부른다** — 배선 명령에 부른 파일의 절대 경로가 박힌다. 이 폴더의 사본을 부르면 내려받은
#   임시 폴더를 가리키게 된다.
# 홈 훅 가운데 무엇이 agy 에 가고 나머지가 왜 안 가나는 어댑터의 머리말(`wanted()`)이 든다 — 여기 이름을 늘어놓지 않는다.
$agyHookPlant = Join-Path $ConfigSeedHooks 'agy-hooks.py'
$AgyHooksCfg  = Join-Path $env:USERPROFILE '.gemini\config\hooks.json'
if ($hostAgy) {
  if (-not (Test-Path -LiteralPath $agyHookPlant)) {
    Write-Host '  ! agy 훅 — 씨앗의 어댑터가 없어 안 심는다' -ForegroundColor Red
    $Fails.Add('agy 훅 (씨앗이 없다)')
  } elseif (($agyHookPython = Measure-Runs 'python' '--version') -eq 'unmeasured') {
    Add-UnmeasuredStep 'agy 훅' 'python --version' '심지도 건너뛰지도 않았다'
  } elseif ($agyHookPython -ne 'yes') {
    Write-Host '  ! agy 훅 — python 이 안 서서 안 심는다' -ForegroundColor Red
    $Fails.Add('agy 훅 (python 없음)')
  } else {
    $agyHookLog = [IO.Path]::GetTempFileName()
    try {
      $agyHookRc = Invoke-Logged 'python' @('-X', 'utf8', $agyHookPlant, 'install', '--config', $AgyHooksCfg) $agyHookLog
      $agyHookOut = @(Get-Content -LiteralPath $agyHookLog -ErrorAction SilentlyContinue |
                      ForEach-Object { "$_".Trim() } | Where-Object { $_ })
      if ($agyHookRc -ne 0) {
        Write-Host '  ! agy 훅 — hooks.json 은 그대로다. 어댑터가 뱉은 끝 줄:' -ForegroundColor Red
        Show-Log $agyHookLog
        $Fails.Add('agy 훅 (hooks.json 병합 실패)')
      } elseif ($agyHookOut -contains 'CHANGED=1') {
        Write-Host '  agy 훅 — 씨앗 어댑터(agy-hooks.py)의 우리 훅을 hooks.json 에 심었다' -ForegroundColor Green
        $agyHookBak = @($agyHookOut | Where-Object { $_ -like 'BACKUP=*' }) | Select-Object -First 1
        if ($agyHookBak) { Write-Host "     고치기 전 것은 $($agyHookBak.Substring(7)) 에 떠 뒀다" }
      } else {
        Write-Host '  agy 훅 — 이미 맞다'
      }
    } finally { Remove-Item -LiteralPath $agyHookLog -ErrorAction SilentlyContinue }
  }
} else {
  # 안 골랐으면 우리 이름(`paisetup-…`)의 항목만 걷는다 — 어댑터의 걷기 판. 고치기 전 원본을 떠 두는 손은 곁의 Codex 병합기라
  #   둘 다 있어야 부른다.
  Remove-UnpickedHooks 'agy 훅' $AgyHooksCfg @($agyHookPlant, (Join-Path $ConfigSeedHooks 'codex-hook-install.py')) `
                       @('remove', '--config', $AgyHooksCfg) @('--version') 'python 이'
}

# ── 브라우저 MCP — 고른 도구에 `playwright` 서버를 달고, 안 고른 도구에서 우리 것만 걷는다 (claude-config 결정 0149) ─────────
# 서버는 「CLI」 걸음이 깐 전역 playwright 에 들어 있고, 브라우저는 씨앗의 `get-browser.sh`(구글 스냅숏)가 받는다. 무엇을 어떻게
#   다나 · 우리 것을 무엇으로 가리나 · 꾸러미나 브라우저가 없으면 안 다는 것은 씨앗의 어댑터 `browser-mcp.py` 의 머리말이 든다.
# ⚠ **씨앗 자리의 것을 부른다** — 등록에 곁의 실행기(`browser-mcp.mjs`)의 절대 경로가 박힌다. 이 폴더의 사본을 부르면 내려받은
#   임시 폴더를 가리키게 된다(agy 훅과 같은 까닭).
# 브라우저를 못 받아도 설치는 잇는다 — 노랑 한 줄을 남기고, 어댑터가 브라우저가 없으면 안 달고 SKIP 을 낸다.
# 개발 도구를 끈 PC(`-NoDevTools`)에 Git Bash 가 없으면 받기를 건너뛴다 — 받는 손이 Git Bash 로 도는데 Git 을 안 까는 것은 그
#   사람이 고른 몫이다. 그래서 어댑터가 브라우저가 없어 안 단 것(SKIP)은 건너뜀으로 찍고 끝 검증 칸도 안 세운다
#   (`$browserMcpSkipped`). 브라우저가 이미 있으면 어댑터가 그대로 달고 끝 검증도 그대로 잰다.
$browserMcpSkipped = $false
$browserGetSkipped = $false
$browserMcpPlant = Join-Path $ConfigSeedHooks 'browser-mcp.py'
$browserGet      = Join-Path $ConfigSeedHome '.claude\get-browser.sh'
$browserMcpOn    = @($BrowserMcpHosts.Keys | Where-Object { $PickKeys -contains $_ }    | ForEach-Object { $BrowserMcpHosts[$_] })
$browserMcpOff   = @($BrowserMcpHosts.Keys | Where-Object { $PickKeys -notcontains $_ } | ForEach-Object { $BrowserMcpHosts[$_] })
# python 은 `Measure-Runs` 로 묻는다 — 넘김을 「없다」로 읽으면 멀쩡한 PC 가 빨강이 된다(결정 0141).
$browserMcpPython = Measure-Runs 'python' '--version'
if ($browserMcpOn.Count) {
  $gitBash = Find-GitBash
  if (-not $gitBash -and $NoDevTools) {
    Write-Host '  브라우저(크로미움) — 건너뜀 (-NoDevTools · 받는 손이 Git Bash 로 돈다)'
    $browserGetSkipped = $true
  } elseif (-not $gitBash) {
    Write-Host '  ! 브라우저(크로미움) — Git Bash 가 없어 못 받았다' -ForegroundColor Yellow
  } elseif (-not (Test-Path -LiteralPath $browserGet)) {
    Write-Host "  ! 브라우저(크로미움) — 씨앗에 받는 손이 없다 ($browserGet)" -ForegroundColor Red
    $Fails.Add('브라우저 받기 (씨앗이 없다)')
  } else {
    Say-Busy '브라우저(크로미움)' 'fetch' @('get-browser.sh · 없을 때만')
    $gbLog = [IO.Path]::GetTempFileName()
    $gbRc = Invoke-LoggedCapped $gitBash @(($browserGet -replace '\\', '/')) $gbLog $BrowserGetCap
    $gbLast = @(Get-Content -LiteralPath $gbLog -Encoding UTF8 -ErrorAction SilentlyContinue | Where-Object { "$_".Trim() }) | Select-Object -Last 1
    if ($gbRc -eq 0) {
      Write-Host "  $("$gbLast".Trim())"
    } elseif ($gbRc -eq -2) {
      Write-Host "  ! 브라우저(크로미움) — ${BrowserGetCap}초 안에 못 받아 거뒀다" -ForegroundColor Yellow
    } else {
      Write-Host "  ! 브라우저(크로미움) — 못 받았다 (종료 $gbRc) — 뱉은 끝 줄:" -ForegroundColor Yellow
      Show-Log $gbLog
    }
    Remove-Item -LiteralPath $gbLog, "$gbLog.err" -ErrorAction SilentlyContinue
  }
}
if (-not (Test-Path -LiteralPath $browserMcpPlant)) {
  if ($browserMcpOn.Count) {
    Write-Host '  ! 브라우저 MCP — 씨앗의 어댑터가 없어 안 단다' -ForegroundColor Red
    $Fails.Add('브라우저 MCP (씨앗이 없다)')
  }
} elseif ($browserMcpPython -eq 'unmeasured') {
  if ($browserMcpOn.Count)      { Add-UnmeasuredStep '브라우저 MCP' 'python --version' '달지도 걷지도 않았다' }
  elseif ($browserMcpOff.Count) { Add-UnmeasuredStep '브라우저 MCP 걷기' 'python --version' '우리 등록을 안 걷었다' }
} elseif ($browserMcpPython -ne 'yes') {
  if ($browserMcpOn.Count) {
    Write-Host '  ! 브라우저 MCP — python 이 안 서서 안 단다' -ForegroundColor Red
    $Fails.Add('브라우저 MCP (python 없음)')
  } else {
    Write-Host '  ! 브라우저 MCP — 고르지 않았는데 python 이 안 서서 우리 등록을 못 걷었다' -ForegroundColor Yellow
  }
} else {
  if ($browserMcpOn.Count) {
    $bmInstall = Invoke-BrowserMcp $browserMcpPlant (@('install') + @($browserMcpOn | ForEach-Object { '--host', $_ }))
    $browserMcpSkipped = $browserGetSkipped -and $bmInstall.Rc -eq 0 -and @($bmInstall.Lines | Where-Object { $_ -like 'SKIP=*' }).Count -gt 0
    if ($browserMcpSkipped) { Write-Host '  브라우저 MCP — 건너뜀 (-NoDevTools · 브라우저를 안 받아 안 달았다)' }
    else                    { Show-BrowserMcpLines '브라우저 MCP' $bmInstall }
  }
  if ($browserMcpOff.Count) { Show-BrowserMcpLines '브라우저 MCP 걷기' (Invoke-BrowserMcp $browserMcpPlant (@('remove') + @($browserMcpOff | ForEach-Object { '--host', $_ }))) }
}

# ── 묻지 않고 돌기 — 고른 도구마다 그 도구 제 승인 설정을 심는다 (claude-config #158 · 결정 0127) ─────────────────────
# 설치 창에 칸이 없다 — 그 도구를 고르면 선다(Codex 만 아직 사외에서만). Claude 의 기본 권한 모드는 「Claude 홈 설정」의 표가 든다.
# 무엇을 심나 — 그 도구가 대화형에서 사람에게 묻는 대신 스스로 진행하게 하는 제 설정 하나씩이다. 폴더 신뢰(세션 훅) · 러너 허락
#   (Claude 홈 설정) · 헤드리스의 건너뛰기 깃발(부르는 쪽)과는 다른 층이다. 값마다 무엇을 여나는 결정 0127 이 든다.
#   * agy CLI — `toolPermission = always-proceed`. 앱의 값은 CLI 에 안 먹어 둘 다 심는다
#   * agy 앱 — Turbo 의 세 칸. 셋이 한 스위치라 한 줄이다
#   * Copilot CLI — `defaultPermissionMode = allow-all`, 그 위에 `defaultMode = autopilot`. 대화형 시작에만 먹고 `-p` 맡기기에는 안 간다
#   * Codex CLI — `approvals_reviewer = auto_review`(「Approve for me」). 샌드박스를 넘는 요청을 사람 대신 검토자가
#     가른다. 샌드박스 모드는 안 심는다 — 사용자 단에 두면 신뢰하지 않은 폴더까지 열린다. `approval_policy` 가 서 있으면 사람이
#     승인 층을 정한 것이라 둔다. 데스크탑 앱에는 앱이 권한을 저장하기 전, 곧 첫 샌드박스 설정이 `auto` 를 적기 전까지만 먹는다 —
#     데스크탑의 「나 대신 승인」은 Codex 가 닫힌 채 도는 심기(「설정 저장소」 걸음의 `--install` · `--plant`, 끝의 다시 띄우기
#     동의 뒤의 `--plant`)가 그 상태 파일에 쓴다(결정 0127 · 0135)
# 심은 값은 장부(`$ClaudePlantLedger`)에 적는다 — 사람이 같은 값을 둔 것과 글자로는 안 갈려, 우리 것은 장부에 든 값 그대로인 것뿐이다
#   (결정 0127 의 고침 · PAISetup #44 ⑬). 판이 `Set` 값을 바꾸면 장부의 옛 값 그대로인 키만 새 값으로 가고(심는 손 앞에서 — 그래야 그 손이
#   「이미 맞다」로 읽는다), 그 도구를 빼거나 그 자리가 안 심게 되면(사내의 Codex 줄) 장부의 값 그대로인 키를 걷는다. 사람이 바꾼 값은
#   두고 이름을 댄다. 장부를 처음 세우는 판은 지금 값이 이 표의 값 그대로인 키를 우리 것으로 받는다 — 그 앞 판들이 기록 없이 심었다.
#   끄는 길은 그 도구의 설정에서 다른 값을 고르는 것이다(다음 설치가 그 값을 안 덮는다).
# Copilot 홈은 Copilot 이 고르는 차례(`COPILOT_HOME` → `~/.copilot`)를 따른다 — 세션 훅이 폴더 신뢰를 거는 자리와 같다(결정 0122).
$CopilotCfg = Join-Path $(if ($env:COPILOT_HOME) { $env:COPILOT_HOME } else { Join-Path $env:USERPROFILE '.copilot' }) 'settings.json'
$ToolAutoRun = @(
  @{ Label = 'agy CLI'; Want = [bool]$hostAgy; Path = $AgyCfg; Under = ''
     Set = [ordered]@{ toolPermission = 'always-proceed' } }
  @{ Label = 'agy 앱(Turbo)'; Want = [bool]$hostAgy; Path = (Join-Path $env:USERPROFILE '.gemini\config\config.json'); Under = 'userSettings'
     Set = [ordered]@{ autoExecutionPolicy          = 'CASCADE_COMMANDS_AUTO_EXECUTION_EAGER'
                       enableTerminalSandbox        = $false
                       nonWorkspaceFileAccessPolicy = 'AGENT_SETTING_POLICY_ALLOW' } }
  @{ Label = 'Copilot CLI'; Want = [bool]($PickKeys -contains 'copilot'); Path = $CopilotCfg; Under = ''
     Set = [ordered]@{ defaultPermissionMode = 'allow-all' } }
  # Autopilot — 새 대화형 세션이 첫 프롬프트에서 일을 끝까지 스스로 잇는 모드다(`-p` · 서버 · ACP 실행에는 안 먹는다). 승인이
  #   `allow-all` 일 때만 심는다 — 사람이 `manual` 을 골랐는데 Autopilot 이면 새 세션마다 그 확인이 뜬다. 바로 위 줄이 심은 뒤에
  #   재므로 그 줄 뒤에 선다. 모드는 승인 층이 아니라 승인 줄을 안 막는다(결정 0127).
  @{ Label = 'Copilot CLI(Autopilot)'; Want = [bool]($PickKeys -contains 'copilot'); Path = $CopilotCfg; Under = ''
     Set = [ordered]@{ defaultMode = 'autopilot' }; Need = [ordered]@{ defaultPermissionMode = 'allow-all' } }
  # Codex 는 사외에서만 심는다 — 사내 Codex 는 게이트웨이로 가 검토자가 쓸 모델이 그 목록에 없을 수 있고, 그러면 샌드박스를 넘는
  #   요청마다 검토가 져 묻는 것보다 나쁘다. 사내 PC 에서 검토가 서는 것을 재면 `-not $inside` 를 걷는다(결정 0127).
  @{ Label = 'Codex'; Want = [bool]($hostCodex -and -not $inside); Path = $CodexCfg; Under = ''; Toml = $true
     Set = [ordered]@{ approvals_reviewer = 'auto_review' }; Guard = @('approval_policy', 'approvals_reviewer') }
)
# 도구 설정 파일 하나(`$ToolDoc` — `Open-ToolDoc`)를 장부 손이 읽고 고치는 손 셋 — 아래 세 칸이 같이 쓴다. 파일은 그 칸이 다 고친 뒤 한 번 쓴다
#   (`Save-ToolDoc`). 못 쓰면 그 자리의 장부 줄을 고치기 앞으로 되돌린다 — 장부가 실물보다 앞서지 않게.
$ToolDocGet    = { param($n) Get-ToolDocValue $ToolDoc $n }
$ToolDocSet    = { param($n, $v) Set-ToolDocValue $ToolDoc $n $v }
$ToolDocRemove = { param($n, $v) Remove-ToolDocValue $ToolDoc $n }
$Ledger = Read-RunLedger $ClaudePlantLedger
$autoWant = @{}   # 그 안의 자리 → 이번 판에 선 키 → 장부 칸 글(압축 JSON)
$autoHold = @{}   # 그 안의 자리 → 이번 판에 못 가른 키(안 걷는다 — 못 읽었거나 조건이 안 섰다)
foreach ($r in @($ToolAutoRun | Where-Object { $_.Want })) {
  $at = ConvertTo-LedgerAt $r.Path $r.Under
  if (-not $autoWant.ContainsKey($at)) { $autoWant[$at] = [ordered]@{}; $autoHold[$at] = @() }
  $vals = [ordered]@{}
  foreach ($k in $r.Set.Keys) { $vals[$k] = [string]($r.Set[$k] | ConvertTo-Json -Compress) }
  # 판이 값을 바꿨으면 장부의 옛 우리 값 그대로인 키를 새 값으로 — 심는 손 앞에서. 처음 세우는 장부는 이 표의 값 그대로인 키를 받는다
  $snap = Get-LedgerSlice $Ledger @('tool') $at
  # 처음 세우는 장부가 받는 것은 이 줄의 값 그대로인 키뿐이고, `Set` 밖의 지키는 키(Codex 의 `approval_policy`)가 서 있으면 아무것도 안 받는다 —
  #   그 키는 사람이 승인 층을 정했다는 표지라, 곁의 우리 값과 같은 키도 그 사람이 고른 것으로 본다(`Set-ToolAutoRun` 의 「한 줄은 한 스위치」)
  $guardOut = @(@($r.Guard) | Where-Object { $_ -and $r.Set.Keys -notcontains $_ })
  $ToolDoc = Open-ToolDoc $r.Path $r.Under ([bool]$r.Toml) (@($r.Set.Keys) + $guardOut)
  if (-not $ToolDoc.Why) {
    $guardSet = @($guardOut | Where-Object { $null -ne (Get-ToolDocValue $ToolDoc $_) })
    $null = Sync-Planted -Ledger $Ledger -Place 'tool' -At $at -By 'autorun' -Want $vals -Names @($vals.Keys) -Mode 'guard' -Plant $false -Complete $false `
              -Adopt $(if ($Ledger.Migrating -and -not $guardSet.Count) { @($vals.Keys) } else { @() }) -Get $ToolDocGet -Set $ToolDocSet -Remove $ToolDocRemove `
              -Where "묻지 않고 돌기 · $($r.Label)" -Speak
    $sv = Save-ToolDoc $ToolDoc
    if ($sv.Did -cne 'same' -and $sv.Did -cne 'written') {
      Set-LedgerSlice $Ledger @('tool') $at $snap
      Write-Host "  ! 묻지 않고 돌기 · $($r.Label) — 장부의 옛 우리 값을 새 값으로 못 바꿨다 ($($sv.Why)) · 안 건드렸다 ($($r.Path))" -ForegroundColor Yellow
    }
  }
  $res = Set-ToolAutoRun $r
  $ours = @($r.Set.Keys | ForEach-Object { "$_ = $($r.Set[$_] | ConvertTo-Json -Compress)" }) -join ' · '
  switch ($res.Did) {
    'set'  { Write-Host "  묻지 않고 돌기 · $($r.Label) — 심었다 ($ours)" -ForegroundColor Green }
    'kept' {
      if ((@($res.Have) -join ' · ') -ceq $ours) { Write-Host "  묻지 않고 돌기 · $($r.Label) — 이미 맞다" }
      else { Write-Host "  묻지 않고 돌기 · $($r.Label) — 사람이 정한 값($($res.Have -join ' · '))이라 둔다" }
    }
    'skipped' { Write-Host "  묻지 않고 돌기 · $($r.Label) — 안 심는다 ($($res.Why))" }
    'raced'   { Write-Host "  ! 묻지 않고 돌기 · $($r.Label) — $($res.Why) · 이 판은 안 썼다 ($($r.Path))" -ForegroundColor Yellow }
    'linked'  { Write-Host "  ! 묻지 않고 돌기 · $($r.Label) — $($res.Why) · 그 자리는 손으로 맞춘다 ($($r.Path))" -ForegroundColor Yellow }
    'unmeasured' { Add-UnmeasuredStep "묻지 않고 돌기 · $($r.Label)" $res.Probe '심지도 건너뛰지도 않았다' $res.Why }
    default {
      Write-Host "  ! 묻지 않고 돌기 · $($r.Label) — $($res.Why) · 안 건드렸다 ($($r.Path))" -ForegroundColor Red
      $Fails.Add("묻지 않고 돌기 · $($r.Label) ($($res.Why))")
    }
  }
  if ($res.Did -eq 'set') { foreach ($k in $vals.Keys) { Set-LedgerRow $Ledger 'tool' $at $k 'autorun' $vals[$k] } }
  if ($res.Did -eq 'set' -or $res.Did -eq 'kept') { foreach ($k in $vals.Keys) { $autoWant[$at][$k] = $vals[$k] } }
  else { $autoHold[$at] += @($vals.Keys) }
}
# 안 고른 줄 · 그 자리가 안 심는 줄 · 표에서 빠진 키 — 장부에 든 우리 값 그대로면 걷는다(사람이 바꾼 값은 두고 이름을 댄다).
$autoAts = @(@($autoWant.Keys) + @($Ledger.Rows | Where-Object { $_.Place -ceq 'tool' -and $_.By -ceq 'autorun' } | ForEach-Object { $_.At }) | Sort-Object -Unique)
foreach ($at in $autoAts) {
  $want = if ($autoWant.ContainsKey($at)) { $autoWant[$at] } else { [ordered]@{} }
  $hold = if ($autoHold.ContainsKey($at)) { @($autoHold[$at]) } else { @() }
  $gone = @(Find-LedgerRows $Ledger 'tool' $at 'autorun' | Where-Object { -not $want.Contains($_.Name) -and $hold -cnotcontains $_.Name } | ForEach-Object { $_.Name })
  if (-not $gone.Count) { continue }
  $where = ConvertFrom-LedgerAt $at
  $snap = Get-LedgerSlice $Ledger @('tool') $at
  $ToolDoc = Open-ToolDoc $where.Path $where.Under ($where.Path -like '*.toml') $gone
  $res = Sync-Planted -Ledger $Ledger -Place 'tool' -At $at -By 'autorun' -Want ([ordered]@{}) -Names $gone -Mode 'guard' -Plant $false -Complete $true `
           -Get $ToolDocGet -Set $ToolDocSet -Remove $ToolDocRemove -Where "묻지 않고 돌기 · $($where.Path)" -Speak
  if ($res.Unread.Count -or $res.Failed.Count) {
    Write-Host "  ! 묻지 않고 돌기 — 우리가 심은 값($(@($res.Unread) + @($res.Failed) -join ' · '))을 못 걷었다$(if ($ToolDoc.Why) { " ($($ToolDoc.Why))" }) · 다음 판이 다시 본다 ($($where.Path))" -ForegroundColor Yellow
  }
  $sv = Save-ToolDoc $ToolDoc
  if ($sv.Did -cne 'same' -and $sv.Did -cne 'written') {
    Set-LedgerSlice $Ledger @('tool') $at $snap
    Write-Host "  ! 묻지 않고 돌기 — 우리가 심은 값을 못 걷었다 ($($sv.Why)) · 안 건드렸다 ($($where.Path))" -ForegroundColor Yellow
  }
}

# ── Codex 데스크탑의 샌드박스 키의 장부 (PAISetup #44 ⑳) ─────────────────────────────────────
# 심는 손은 「프로그램」 걸음의 데스크탑 칸(`Set-CodexSandboxKey` · 그 칸이 낸 `$sbx`)이다 — 데스크탑을 깔기 앞이라 거기 산다. 여기서는 그 결과로
#   장부를 맞춘다: 이번 판에 지었거나 더했으면 우리 것으로 적고, 판이 `$CodexSandboxMode` 를 바꿨으면 장부의 옛 값 그대로일 때 새 값으로 간다.
#   Codex 를 안 고르게 되면 장부의 값 그대로인 그 키를 걷는다(그 표에 남은 키가 없으면 머리째). 사람이 바꾼 값은 둔다.
# 고른 채 이번 판에 데스크탑을 안 깐 자리(사내)는 심지도 걷지도 않고 장부만 실물에 맞춘다(guard · 걷기 없음) — 키는 이미 깐 데스크탑이 읽고,
#   앱 · 사람이 바꾼 값을 장부에 그대로 두면 끝 검증이 판마다 거짓 빨강을 낸다. 그래서 바뀐 값 · 사라진 값은 장부에서만 뺀다.
$sbxAt   = ConvertTo-LedgerAt $CodexCfg 'windows'
$sbxDid  = if ($sbx) { [string]$sbx.Did } else { '' }
$sbxOn   = ($sbxDid -ceq 'made' -or $sbxDid -ceq 'added' -or $sbxDid -ceq 'kept')
$sbxGone = -not ($PickKeys -contains 'codex')
$sbxRows = @(Find-LedgerRows $Ledger 'tool' $sbxAt 'codex-sandbox').Count
if ($sbxOn -or $sbxRows) {
  $snap = Get-LedgerSlice $Ledger @('tool') $sbxAt
  $ToolDoc = Open-ToolDoc $CodexCfg 'windows' $true @('sandbox')
  $sbxWant = [ordered]@{}
  if (-not $sbxGone) { $sbxWant['sandbox'] = [string]($CodexSandboxMode | ConvertTo-Json -Compress) }
  $res = Sync-Planted -Ledger $Ledger -Place 'tool' -At $sbxAt -By 'codex-sandbox' -Want $sbxWant -Mode 'guard' -Plant $false -Complete ($sbxOn -or $sbxGone) `
           -Adopt $(if ($sbxDid -ceq 'made' -or $sbxDid -ceq 'added' -or ($sbxOn -and $Ledger.Migrating)) { @('sandbox') } else { @() }) `
           -Get $ToolDocGet -Set $ToolDocSet -Remove $ToolDocRemove -Label @{ sandbox = 'Codex 데스크탑 · 샌드박스 키' } -Where "$CodexCfg 의 [windows]" -Speak
  if ($res.Failed.Count) { Write-Host "  ! Codex 데스크탑 · 샌드박스 키 — 장부의 우리 값을 못 고쳤다 (그 줄의 꼴이 우리가 쓴 꼴이 아니다) · 안 건드렸다 ($CodexCfg)" -ForegroundColor Yellow }
  $sv = Save-ToolDoc $ToolDoc
  if ($sv.Did -cne 'same' -and $sv.Did -cne 'written') {
    Set-LedgerSlice $Ledger @('tool') $sbxAt $snap
    Write-Host "  ! Codex 데스크탑 · 샌드박스 키 — 못 썼다 ($($sv.Why)) · 안 건드렸다 ($CodexCfg)" -ForegroundColor Yellow
  }
}
$null = Save-PlantLedger $Ledger

} catch { Write-StepFault $_ }
Exit-Step 'tools'

# ══ 걸음 「설정 저장소」 ═══════════════════════════════════════════════════════════════════════
#   층 — 저장소
#   하는 일 — GitHub CLI 로그인 · 설정 저장소 받기 · 옛 우리 사본을 갈고 그 저장소 훅을 `--install` 로 부르기 · 작업 루트의 옛 우리 사본
#     훑기(claude-config 결정 0129) · PC 마다 홈 씨앗의 `--plant`(claude-config 결정 0134 · 0135)
#   앞에서 받는 것 — 준비의 주소 · 자리(`$configRepoUrls` · `$configRepoRoot`), 제작자 칸(`$personalAny`), 「도구별 홈」이 이 프로세스에 둔 `PAISETUP_PERSONAL` ·
#     `PAISETUP_PICK`, 「공용 자산」이 깐 홈 씨앗
#   안 하는 것 — 그 뒤의 개인화. 그 저장소의 배포가 든다
# ── 개인 값 저장소 (선택) ────────────────────────────────────────────────────
# 주소는 이 파일에 없다 — `install.env` 가 `#config-repo` 를 들 때만 이 칸이 선다. 그래야 이 스크립트가 익명으로 남아 남에게
#   그대로 간다.
# 갈래는 둘이고 둘 다 정당하다. 규약은 받아 온 저장소 뿌리의 `.claude/hooks/session-start.sh`(Claude Code 의 SessionStart 훅) 하나다:
#   · 있으면 → `--install` 로 부른다. 리모트 컨테이너의 Setup script 가 부르는 것과 같은 한 줄이라 VDI 와 리모트가 같은 자리로
#     선다. 그 뒤는 그 저장소가 든다. 이 설치기보다 옛 세대의 우리 사본이면 지금 판으로 갈고 부르거나, 못 갈면 안 부른다(아래
#     넘길 자리를 고르는 줄)
#   · 없으면 → 받아 둔 것으로 끝낸다 — 실패가 아니다. 저장소만 들고 다니는 사람에게는 clone 이 곧 목적이라, 빨강으로 찍으면
#     멀쩡한 PC 가 매번 실패로 보고된다. 대신 훅이 왜 안 돌았나를 그 자리에서 말한다
#   그 파일 이름을 받는 사람에게 알리는 것은 `INSTALLED.md` 「내 저장소 받기를 채우면」이 든다.
# 넘긴 뒤 저쪽이 드는 것은 사람에게 딸린 것뿐이다 — git 신원 · 형제 저장소 · 개인 키 · 규범·룰·메모리 배포. 회사 키·주소·프록시·
#   Codex/안티그래비티 설정·확장·CLI 는 앞 걸음들이 이미 세웠고, 무엇을 깔지는 이 파일 하나가 든다(런타임을 두 번 깔지 않는다).
Enter-Step 'repo'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)
# 옛 판 훅을 든 받은 저장소 — 아래 넘길 자리를 고르는 줄이 채우고, 끝의 요약이 그 가운데 세션마다 도는 것을 알린다. 받은 저장소(`$got`)는
#   걸음 끝의 작업 루트 훑기가 건너뛸 목록이라 칸이 비어도 서 있어야 한다.
$oldHooks = @(); $got = @()
# 받은 저장소의 훅으로 넘기나 — 넘길 자리를 고르는 줄 끝에서 선다. 부름은 칸 밖에 선다.
$handOff = $false
# 훅은 bash 몸통이라 Git Bash 로 부른다. 칸이 비어도 찾는다 — 걸음 끝의 `--plant` 가 쓴다.
$bash = Find-GitBash
# 주소(`$repoUrl` · `$configRepoUrls`)와 자리(`Get-ConfigRepoDir`)는 「설정 저장소의 주소와 자리」 칸에서 한 벌로 섰다.
if (-not $repoUrl) {
  Write-Host '  건너뜀 — install.env 에 #config-repo 가 없다'
} elseif (-not (Test-Runs 'git' '--version')) {
  Write-Host '  ! git 이 안 닿아 못 받는다' -ForegroundColor Red
  $Fails.Add('개인 값 저장소 (git 이 안 닿는다)')
} else {
  # ⚠ **받는 자리를 값 파일로 고르게 하지 않는다** — 넘겨받는 쪽은 형제 저장소를 제 선언의 `ROOT`(`$HOME/repos`)로 찾고 값
  #   파일을 안 보므로, 여기만 딴 데로 받으면 저쪽이 `~/repos` 에서 찾다 죽는다. 자리를 옮기는 법은 「홈 아래 우리가 쓰는 자리」
  #   칸이 든다.
  New-Item -ItemType Directory -Path $configRepoRoot -Force | Out-Null

  # ── GitHub CLI 로그인 — **받기 직전, 개인 계정이 서야 하는 자리** ─────────────
  # 로그인의 답은 개인 값을 받기 바로 앞에서 받는다 — 이 칸이 개인 계정이 있어야 서는 칸이라서다. 창은 「프로그램」 걸음이 gh 가
  #   선 바로 뒤 숨은 자식에 앞당겨 띄우고(`Start-GhLoginChild` · PAISetup #35 A) 이 칸은 그 답을 받는다 — 이 프로세스에서 창을
  #   열면 사람을 기다리는 동안 회사 환경(확장 · CLI · 키 · 프록시 · 회사 설정)까지 멎는다. 앞서 안 띄운 판(조건이 그때 안 섰다)과
  #   자식이 창을 못 세운 판만 이 자리에서 띄운다. 창의 한도는 `$GhLoginWait` 하나다.
  # 저장소를 넣은 사람만 묻는다 — gh 는 바로 아래 비공개 저장소 받기와 그 뒤 세션 훅이 쓰고, 저장소를 안 넣은 사람에게 띄우면
  #   GitHub 가입부터 하라는 말이 된다. 그 조건은 이 칸이 `#config-repo` 가 있을 때만 돌아 이미 섰고, 아래 조건은 개발 도구를 끈
  #   사람(gh 가 안 깔린다) 하나만 든다.
  # 토큰을 전제하지 않는다 — 모두의 길은 브라우저에 넣는 일회용 코드 하나이고, 개인 토큰을 이미 든 사람은 「이미 서 있다」로
  #   지나간다. 코드는 팝업이 든다 — 설치 창 기록에만 찍으면 스크롤에 묻힌다. 창 하나가 코드 · 남은 시간 · 브라우저 열기 · 복사를
  #   들고, 로그인이 서면 스스로 닫힌다.
  # 서면 git 자격도 같이 맡긴다(`gh auth setup-git`) — 그래야 아래 clone 이 자격 창을 또 안 띄운다.
  # 안 누른 것은 실패가 아니다 — 시간이 다 가거나 [건너뛰기]면 「비었다」로 두고 간다. 아래 clone 이 제 자격 창을 띄우므로 길은
  #   안 막힌다(「사외 Claude 구독 로그인」 칸과 같은 규율).

  $ghLoggedIn = $false
  if (-not $NoDevTools) {
    # 이 구간을 따로 잰다 — 이 자리에서 창을 띄운 판은 사람이 코드를 누를 때까지 멎어, 안 가르면 그 대기가 「저장소 걸음이
    #   느리다」로 읽힌다. 앞당겨 띄운 판은 남은 기다림만 든다.
    $tGh = Get-Took
    Write-Host ''
    Write-Host '  GitHub CLI 로그인' -ForegroundColor Cyan
    # 이 자리에서 창을 띄울 판을 잴까 — 앞서 띄운 창이 답을 냈으면(섰든 안 섰든) 다시 안 띄운다
    $ghHere = $true
    if ($script:GhLoginChild -and $script:GhLoginChild.Proc) {
      $ghAns = Wait-GhLoginChild $script:GhLoginChild
      $script:GhLoginChild = $null
      if (@('ok', 'no', 'late') -contains $ghAns.Said) {
        $ghHere = $false
        if ($ghAns.Said -eq 'late') {
          Write-Host "  ! 앞서 띄운 로그인 창이 한도(${GhLoginWait}초 + ${GhLoginGrace}초) 안에 안 끝나 거뒀다" -ForegroundColor Yellow
        }
        $ghTimedBefore = $script:ProbeTimedOut.Count
        if (Test-GhLoggedIn) {
          $ghLoggedIn = $true
          Write-Host '  섰다' -ForegroundColor Green
          $null = Get-Quiet 'gh' @('auth','setup-git')
        } elseif ($script:ProbeTimedOut.Count -gt $ghTimedBefore) {
          Write-Host "  ! 로그인이 섰나를 못 쟀다 — gh api user 가 ${GhStatusCap}초 안에 안 끝났다" -ForegroundColor Yellow
        } else {
          Write-Host '  ! 로그인이 안 섰다 — 새 터미널에서 gh auth login (저장소 받기는 제 자격 창을 띄운다)' -ForegroundColor Yellow
        }
      } else {
        $why = if ($ghAns.Said -like 'err *') { $ghAns.Said.Substring(4) } elseif ($ghAns.Err) { $ghAns.Err } else { '답 없이 끝났다' }
        Write-Host "  ! 앞서 띄운 로그인 창이 못 섰다 — $why · 이 자리에서 다시 잰다" -ForegroundColor Yellow
      }
    } elseif ($script:GhLoginChild) {
      Write-Host "  ! 로그인 창을 앞서 못 띄웠다 — $($script:GhLoginChild.Why) · 이 자리에서 잰다" -ForegroundColor Yellow
      $script:GhLoginChild = $null
    }
    # 「프로그램」 걸음에서 잰 답을 다시 쓰지 않고 여기서 잰다 — 그 사이 「키와 값」 걸음이 이 프로세스의 환경변수(`$GhEnvTokens` 도
    #   값 파일에 들면 든다)를 심거나 걷어, 그때의 「이미 섰다」가 지금도 참인지 모른다.
    if ($ghHere) {
      switch (Get-GhLoginGo) {
        'nogh' {
          Write-Host '  ! gh 가 안 닿아 로그인을 못 띄운다 — 위 프로그램 칸을 본다' -ForegroundColor Yellow
        }
        'already' {
          $ghLoggedIn = $true
          Write-Host '  이미 서 있다'
          $null = Get-Quiet 'gh' @('auth','setup-git')
        }
        'unmeasured' {
          # 아래 clone 은 제 자격 창을 띄운다
          Write-Host "  ! 로그인이 섰나를 못 쟀다 — gh api user 가 ${GhStatusCap}초 안에 안 끝났다 · 창을 안 띄운다" -ForegroundColor Yellow
        }
        'night' {
          Write-Host '  ! 밤 자동 실행이라 로그인 창을 안 띄운다 — 다음 로그온 · 설치 창이 띄운다' -ForegroundColor Yellow
        }
        'noreach' {
          # 창을 아끼고 말만 한다 — 아래 clone 은 제 자격 창을 띄우므로 길이 막히지는 않는다(안 누른 것과 같은 규율)
          Write-Host '  ! github.com 에 못 닿아 로그인이 섰나를 못 쟀다 — 자격 문제가 아니라 망 문제다' -ForegroundColor Yellow
        }
        default {
          Write-Host "  브라우저 로그인을 띄운다 — 코드는 팝업에 (최대 ${GhLoginWait}초)" -ForegroundColor Yellow
          $gl = [IO.Path]::GetTempFileName()
          $login = $null
          try {
            $login = Start-GhLoginProcess $gl
            $ghLoggedIn = Show-GhLoginWindow $gl $login $GhLoginWait
            if ($ghLoggedIn) {
              Write-Host '  섰다' -ForegroundColor Green
              $null = Get-Quiet 'gh' @('auth','setup-git')
            } else {
              Stop-GhLoginProcess $login
              Write-Host '  ! 로그인이 안 섰다 — 새 터미널에서 gh auth login (저장소 받기는 제 자격 창을 띄운다)' -ForegroundColor Yellow
            }
          } catch {
            Stop-GhLoginProcess $login
            Write-Host "  ! 로그인을 못 띄웠다 — $(Say-Why $_)" -ForegroundColor Yellow
          }
          Remove-Item $gl, "$gl.err" -ErrorAction SilentlyContinue
        }
      }
    }
    # 갈래(앞서 띄운 창의 답 · gh 없음 · 이미 섬 · 못 잼 · 망 못 닿음 · 이 자리의 팝업)가 다 지나는 자리라 여기 하나면 된다.
    Write-Took 'GitHub CLI 로그인' $tGh
  }

  # 주소를 여럿 받는다(빈칸으로 가른다) — 받을 저장소 목록의 진본이 받는 사람 저장소에 없으면 여기 적을 수밖에 없다. 주소에는
  #   빈칸이 없어 가르는 자로 안전하다. 가르는 줄은 「설정 저장소의 주소와 자리」 칸(`$configRepoUrls`)에 있다.

  # 받기의 실패는 받기의 실패로 낸다 — 계정 · 인증 · 주소가 틀려 못 받은 것을 「훅이 없다」로 내면 사람은 받아진 적도 없는
  #   저장소를 뒤진다.
  # ⚠ git 의 말은 버리지도 합치지도 않고 파일에 잡아 질 때만 편다 — 합치면 `Stop` 이 던지고, 버리면 단서가 사라진다.
  # 하나가 져도 나머지를 계속 받는다 — 첫 실패로 멈추면 성한 저장소까지 못 받고 까닭도 하나만 본다.
  $got = @()
  foreach ($u in $configRepoUrls) {
    $dest = Get-ConfigRepoDir $u
    $log = [IO.Path]::GetTempFileName()
    # 저장소마다 가른다 — 받는 양이 저장소마다 크게 달라, 합만 보면 어느 것이 먹는지 안 보인다.
    $tRepo = Get-Took
    if (Test-Path -LiteralPath (Join-Path $dest '.git')) {
      Say-Busy (Split-Path $dest -Leaf) 'upgrade' @('git pull', $dest)
      $rc = Invoke-Logged 'git' @('-C', $dest, 'pull', '--ff-only') $log
      # pull 이 져도 실패로 세지 않는다 — 저장소는 이미 있어 넘길 자리가 살아 있고, 망이 끊긴 VDI 에서 받아 둔 판으로라도 훅이
      #   도는 것이 낫다. 이 설치기보다 옛 세대면 아래 넘길 자리를 고르는 줄이 가른다(`Get-SessionHookGen`). 진 것은 줄로 말한다.
      $got += $dest
      if ($rc -ne 0) {
        Write-Host '  ! pull 이 졌다 — 이미 받아 둔 판으로 간다' -ForegroundColor Yellow
        Show-Log $log
      }
      Write-Took ((Split-Path $dest -Leaf) + ' 당김') $tRepo
    } else {
      Say-Busy (Split-Path $dest -Leaf) 'fetch' @('git clone', $dest)
      # 이 안내는 우리가 찍는다 — 자격 관리자의 「브라우저에서 마치라」는 줄은 아래 `Invoke-Logged` 가 파일로 잡아 화면에 안 나와,
      #   안 찍으면 사람은 창이 왜 떴는지 모른 채 설치가 멈춘 줄 안다.
      Write-Host '    GitHub 로그인 창이 뜰 수 있습니다 — 브라우저에서 눌러 주세요' -ForegroundColor Yellow
      $rc = Invoke-Logged 'git' @('clone', $u, $dest) $log
      # ⚠ 종료코드만 믿지 않는다 — 0 으로 끝났는데 `.git` 이 안 선 판을 여기서 거른다.
      if ($rc -eq 0 -and (Test-Path -LiteralPath (Join-Path $dest '.git'))) {
        $got += $dest
      } else {
        Write-Host "  ! 못 받았다 — 주소 · 계정 · 망을 본다  ($u)" -ForegroundColor Red
        Show-Log $log
        $Fails.Add("개인 값 저장소 (못 받았다: $u)")
      }
      # 받기는 자격 창이 뜰 수 있어 여기도 사람 대기가 섞인다 — 진 판도 찍는다(진 데 든 시간도 시간이다).
      Write-Took ((Split-Path $dest -Leaf) + ' 받기') $tRepo
    }
    Remove-Item $log -ErrorAction SilentlyContinue
  }

  # 넘길 자리는 순서가 아니라 훅으로 찾는다 — 받아 온 것 가운데 넘겨도 되는 훅을 든 첫 저장소다. 「첫째가 설정 저장소」 같은
  #   규칙은 사람이 순서를 기억해야 하고, 기억해야 하는 것은 그 순간에 안 걸린다.
  # 이 설치기보다 옛 세대의 우리 사본은 그대로는 넘길 자리가 아니다 — 넘기면 「도구별 홈」이 손으로 놓은 것을 제 사본으로
  #   덮는다(결정 0129). 그래서 넘기기 전에 셋을 한다:
  #   · 가른다 — 훅마다 우리 것인가 · 꼴 · 세대(`Get-SessionHookGen`)
  #   · 간다 — 형제 꼴의 옛 사본은 이 실행이 깐 홈 씨앗의 지금 판으로 간다(`Invoke-HookRefresh` → `Update-OurRepoFiles`). 그 사본은
  #     옛 설치 · 배포가 놓은 우리 파일이고, 저장소를 이 칸에 넣은 사람은 거기 우리 설정을 맡긴 것이다. 설정 저장소 꼴은 그 사람이
  #     씨앗을 떠 만든 저장소거나 claude-config 클론이라 안 간다(결정 0115)
  #   · 본다 — 우리 훅이면 넘겼을 때 잡힐 설정 저장소가 지금 판인가(`Get-ConfigRootGen`)
  #   못 넘기는 것은 건너 그 뒤의 넘겨도 되는 훅으로 넘긴다.
  # ⚠ **한 실행에 훅 하나만 부르고 나머지는 이름으로 말한다** — 둘을 잇달아 부르면 뒤엣것이 앞엣것의 키 · 설정을 사람이 안 정한
  #   순서로 덮는다. 훅은 제 자리에서 전역 저장소를 찾아 형제까지 밀므로 하나만 불러도 나머지가 선다.
  $hookRel = '.claude\hooks\session-start.sh'
  $seedDir = $ConfigSeedHome
  $hookGen = @($got | ForEach-Object { Get-SessionHookGen $_ } | Where-Object { $_ })
  foreach ($g in @($hookGen | Where-Object { $_.Ours -and -not $_.Current -and $_.Shape -eq 'sibling' })) { Invoke-HookRefresh $g $seedDir }
  if ($bash) {
    foreach ($g in @($hookGen | Where-Object { $_.Ours -and $_.Current })) {
      $c = Get-ConfigRootGen $g.Repo $bash (Join-Path $seedDir '.githooks\claude-config-path.sh')
      if (-not $c.Current) { $g.Blocked = $c.Why; $g.Fix = $c.Fix }
    }
  }
  $bootRepos = @($hookGen | Where-Object { -not $_.Ours -or ($_.Current -and -not $_.Blocked) } | ForEach-Object { $_.Repo })
  $oldHooks = @($hookGen | Where-Object { $_.Ours -and (-not $_.Current -or $_.Blocked) })
  $dest = $bootRepos | Select-Object -First 1
  $boot = if ($dest) { Join-Path $dest $hookRel } else { $null }

  # 간 저장소마다 「갈았다」 줄 — 쓰다 져 옛 판으로 남은 것은 안 댄다(그것은 아래 「넘기지 않는다」 줄이 든다).
  foreach ($g in @($hookGen | Where-Object { $_.Refreshed.Count -and $_.Current })) { Write-RefreshLine $g }
  # 못 넘긴 것은 실패로 세지 않는다(`Write-HookNotice`) — 저장소와 까닭과 그 까닭에 맞는 고치는 길을 댄다.
  foreach ($o in $oldHooks) { Write-HookNotice $o '이 저장소의 훅으로 넘기지 않는다' }

  if (-not $got) {
    # 실패는 위에서 까닭과 함께 이미 셌다 — 또 세면 한 사고가 둘로 보고된다. 사슬이 끊긴 것만 말한다(안 말하면 훅이 돈 줄 안다).
    Write-Host '  넘길 자리가 없어 훅을 안 부른다'
  } elseif (-not $boot) {
    # 실패가 아니다(칸 머리의 「없으면」) — 훅을 기대한 사람이 속지 않게 안 돈 것을 이름으로 말한다.
    Write-Host "  받아 뒀다 — $($got.Count)개" -ForegroundColor Green
    $got | ForEach-Object { Write-Host "     $_" }
    if ($oldHooks) { Write-Host '    넘겨도 되는 훅을 든 뿌리가 없어 훅은 안 돌았다 — 까닭은 위 「이 저장소의 훅으로 넘기지 않는다」 줄이 든다.' }
    else           { Write-Host "    어느 뿌리에도 $hookRel 가 없어 훅은 안 돌았다." }
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
      Write-Host "  ! 넘겨도 되는 훅을 든 저장소가 $($bootRepos.Count)개다 — 첫 것만 부른다" -ForegroundColor Yellow
      $bootRepos | Select-Object -Skip 1 | ForEach-Object { Write-Host "     안 부른 것: $_" }
    }
    $handOff = $true
  }
}
# Codex 데스크탑은 여기서 닫지 않는다 — 이번 실행이 띄운 창에서 사람이 로그인하는 중일 수 있고, 마치기 전에 닫으면 그 로그인이 날아가
#   다시 띄운 창이 또 묻는다(#164). 그 앱이 떠 있으면 아래 두 부름(넘긴 훅의 `--install` · 홈 씨앗의 `--plant`)은 그 상태 파일
#   (`~/.codex/.codex-global-state.json` — 작업 루트 저장소 0126 · 새 대화 기본 권한 0127)을 미루고, 「연다」 칸이 로그인이 선 것을 본
#   뒤에만 닫고 심고 다시 띄운다(claude-config 결정 0135).
if ($handOff) {
  Write-Host "  훅으로 넘긴다 — $boot --install" -ForegroundColor Green
  Write-Host ''
  # `--install` 은 리모트 Setup script 가 부르는 것과 같은 갈래다 — 지문을 안 보고 깐다. 맨바닥 VDI 의 첫 판(형제 저장소 clone)은
  #   세션 훅의 시간 한도가 아니라 여기서 진다. 이 한 부름에 형제 clone · 전역 도구 · 배포 · 저장소 설치 · 진단이 다 들어 있고,
  #   저쪽이 제 안을 가르는 줄을 내므로 여기는 그 전체를 감싼 값 하나만 잰다.
  $tHook = Get-Took
  & $bash ($boot -replace '\\','/') --install
  if ($LASTEXITCODE -ne 0) { $Fails.Add("훅 --install (exit $LASTEXITCODE)") }
  Write-Took '훅 --install 전체' $tHook
}
# ── 작업 루트 훑기 — 칸에서 안 받은 저장소의 옛 우리 사본(claude-config 결정 0129 · PAISetup #25 사용자 결정 ①) ──────────────
# 칸이 비어도 돈다 — 칸에 저장소를 안 넣은 동료도 옛 설치 · 배포가 놓은 우리 훅을 작업 저장소에 든다. 칸에서 받은 저장소는 위에서 다뤘다.
#   넘긴 훅의 배포가 형제를 먼저 맞추도록 넘기기 뒤에 선다 — 배포가 맞춘 형제는 지금 판으로 읽혀 지나간다. 무엇을 하고 안 하나는
#   `Invoke-WorkRootScan` 이 든다.
$scanHooks = Invoke-WorkRootScan $configRepoRoot $got $personalAny $ConfigSeedHome
# ── 심기만 — PC 마다 홈 씨앗의 `--plant` (claude-config 결정 0134 · 부르는 차례는 결정 0135) ──────────────────────────────────
# 칸이 비어도 돈다 — 설정 저장소를 안 받은 PC 는 이 부름 말고는 홈 SessionStart 훅 · 폴더 신뢰 · 데스크탑 상태를 심는 길이 없다.
#   넘긴 훅의 `--install` 이 이미 심었어도 또 부른다 — 같은 값을 다시 쓸 뿐이고(겹쳐 안 쌓인다), 넘긴 훅이 남의 것이거나 중간에 져도
#   심긴다. 훑기 뒤에 선다 — 훑기가 간 옛 사본이 지금 판의 표지를 든 뒤라야 거는 대상에 든다(결정 0133).
# 못 부른 것(Git Bash · 홈 씨앗의 훅이 없다)은 노란 줄로만 낸다 — Git Bash 가 없는 것은 「프로그램」 걸음이 셌거나 개발 도구를
#   끈 PC(`-NoDevTools`)가 고른 몫이고, 홈 씨앗이 모자라면 끝 검증의 씨앗 줄이 [X] 다. 불렀는데 0 이 아니면 센다. 0 은 「다
#   심었다」가 아니다 — 미룬 칸과 걸 저장소가 없는 루트도 0 이다. 무엇을 심고 미뤘나는 몸통이 찍는 줄이 든다.
$plant = Invoke-Plant $bash $configRepoRoot
if (-not $plant.Ran) { Write-Host "  ! 심기 — $($plant.Why) · 홈 훅 · 신뢰 · 데스크탑 상태를 못 심었다" -ForegroundColor Yellow }
elseif (-not $plant.Ok) { $Fails.Add("심기 --plant ($($plant.Why))") }
} catch { Write-StepFault $_ } finally {
# ── 앞당겨 띄운 로그인 창을 거둔다 — 로그인 칸에 안 닿은 판(그 사이 git 이 안 닿았다 · 이 걸음이 도중에 멎었다)의 자리 ──────────────────
# 로그인 칸이 답을 받았으면 비어 있어 아무것도 안 한다. 남았으면 저장소를 받을 길이 이미 끊긴 판이라 기다리지 않고 거두고 곁 파일을 지운다.
# 걸음 경계의 `finally` 에 선다 — 걸음이 도중에 멎어도 숨은 자식이 띄운 로그인 창이 사람 앞에 남지 않는다.
if ($script:GhLoginChild) {
  if ($script:GhLoginChild.Proc) { $null = Wait-GhLoginChild $script:GhLoginChild -Now }
  $script:GhLoginChild = $null
}
}
Exit-Step 'repo'

# ══ 걸음 「Claude 플러그인」 ═══════════════════════════════════════════════════════════════════
#   층 — 등록
#   하는 일 — Anthropic 공식 스킬 플러그인 둘 · agy 로그인 안내 한 줄(agy 회사 설정이 안 서는 자리)
#   앞에서 받는 것 — 「키와 값」의 구독 로그인
#   안 하는 것 — 꺼진 플러그인 켜기(사람 몫)
Enter-Step 'register'
try {  # 걸음 경계 — 아래 catch 까지가 이 걸음이다(`Write-StepFault`)

# ── Anthropic 공식 스킬 — **자격이 설 자리가 다 선 뒤에 돈다** ────────────────────────
# 「CLI」 걸음이 아니라 여기서 돈다 — CLI 를 깔자마자 붙이면 사외는 「사외 Claude 구독 로그인」 칸 전이고 사내는 「로컬 프록시」
#   칸 · 「Claude 홈 설정」 걸음 전이라 「Not logged in」으로 질 수 있다. 원인이 로그인 하나인지는 못 박지 않는다 — 자격이 끼어들
#   수 있는 칸을 다 지난 뒤에 두면 어느 쪽이어도 선다.
# 공식 마켓플레이스 `anthropics/skills` 의 플러그인 둘을 각자 받는다 — `document-skills`(pptx · docx · xlsx · pdf)와
#   `example-skills`(skill-creator · frontend-design · mcp-builder · webapp-testing 등 열둘). 같은 마켓의 나머지 셋은 안 받는다 —
#   `claude-api` 는 Claude Code 바이너리에 같은 스킬이 묶여 받으면 어느 PC 에서나 두 벌이 되고, `academy-guide` ·
#   `discernment-nudge` 는 답의 끝에 끼어든다(결정 0157).
# ⚠ **배포본에 싣지 않는다** — 문서 스킬의 라이선스는 복제 · 파생 · 제3자 배포를 막고(상업 여부와 상관없다), 이 배포본은 공개
#   저장소라 실으면 누구나 받는 자리에 올라간다.
# 같은 스킬이 다른 통로로도 온다 — claude.ai 구독 로그인 PC 는 계정 동기화가 문서 넷과 skill-creator 를 `anthropic-skills:<이름>`
#   으로 싣는다. 겹쳐도 깔고, 끄지도 건너뛰지도 않는다 — 동기화본은 로그인한 Claude Code 가 돌 때 생겨 설치 시점에 못 가르고,
#   사내 PC 는 이 플러그인이 유일한 통로다.
# 먼저 묻고 없는 것만 깐다 — 자동 실행이 날마다 이 걸음을 지나므로 판정은 `plugin list --json` 한 번이다. 행마다 `id` 와
#   `enabled` 를 읽는다. ⚠ **꺼진 플러그인은 켜지 않는다** — 켜는 명령만 찍는다. 사람이 끈 것을 날마다 되살리면 그 사람의 결정을
#   설치기가 뒤집는다.
# ⚠ **`-y` 를 안 넘긴다** — 그 스위치는 마켓플레이스가 선언한 명령을 대신 승인한다. 이 플러그인들은 git 에서 받는 꼴이라 필요
#   없고, 모르는 명령을 대신 승인하는 손을 두지 않는다.
# 지면 실패로 세지 않는다 — 공식 스킬 없이도 Claude Code 는 돈다. 사내망이 GitHub 을 막는 자리에서 날 수 있어 말은 하고 빨강으로
#   안 끝낸다.
$OfficialSkills = @{ Source = 'anthropics/skills'; Market = 'anthropic-agent-skills'; Plugins = @('document-skills', 'example-skills') }
$officialIds = @($OfficialSkills.Plugins | ForEach-Object { "$_@$($OfficialSkills.Market)" })
$officialHand = "     손으로:  claude plugin marketplace add $($OfficialSkills.Source)  →  " +
                (@($officialIds | ForEach-Object { "claude plugin install $_" }) -join '  →  ')
# ⚠ **두 문을 한 `-and` 로 묶지 않는다** — 묶으면 「Claude 를 안 골랐다」와 「골랐는데 `claude` 가 안 선다」가 똑같이 한 글자
#   없이 지나간다. 앞엣것은 조용해야 맞지만 뒤엣것은 깔 것을 못 깐 자리라 말해야 한다.
$wantOfficialSkills = $PickKeys -contains 'claude'
# 머리는 고른 판에만 선다 — 안 고른 판에 빈 머리만 찍히면 「왜 비었나」를 찾게 된다.
if ($wantOfficialSkills) {
  Write-Host ''
  Write-Host 'Anthropic 공식 스킬' -ForegroundColor Cyan
}
# ⚠ **못 쟀으면 그 명령을 다시 부르지 않는다** — 까닭(넘김 · 종료 값)은 `Measure-Runs` 가 남긴 것을 찍는다. 울타리 없는 손으로 다시
#   부르면 넘긴 명령이 거기서 설치를 세운다. 건너뛰지도 않고 「안 한 걸음」으로 남긴다(결정 0141 · 0151).
$officialClaude = if ($wantOfficialSkills) { Measure-Runs 'claude' '--version' } else { '' }
if ($officialClaude -eq 'unmeasured') {
  Add-UnmeasuredStep 'Anthropic 공식 스킬' 'claude --version' '있는지 안 묻고 깔지도 않았다'
  Write-Host $officialHand
  $wantOfficialSkills = $false
} elseif ($wantOfficialSkills -and $officialClaude -ne 'yes') {
  # `no` 는 그 이름이 이 창에 없다는 것뿐이다 — 이름이 서는데 진 판은 위 갈래가 그 종료 값과 함께 든다(결정 0151).
  Write-Host '  ! Anthropic 공식 스킬 — 건너뛴다: claude 가 이 창의 PATH 에 없다 · 위 CLI 줄을 먼저 본다' -ForegroundColor Yellow
  Write-Host $officialHand
  $wantOfficialSkills = $false
}
if ($wantOfficialSkills) {
  # 목록을 묻는 두 물음(`plugin list` · `plugin marketplace list`)에 울타리를 두른다 — `--version` 이 선 뒤 다시 부르는 자리라 멎으면
  #   PAISetup #26 의 멈춤이 돌아온다. 넘기면 못 잰 것이라 깔지도 건너뛰지도 않고 「안 한 걸음」으로 남긴다(결정 0141).
  #   받아 까는 두 부름(`marketplace add` · `plugin install`)에는 안 두른다 — 받다 거두면 반쯤 놓인 플러그인 자리가 남는다.
  $askClaude = { param([string[]]$A)
    $cl = [IO.Path]::GetTempFileName()
    try {
      $crc = Invoke-LoggedCapped 'claude' $A $cl $ClaudePluginCap
      if ($crc -eq -2) { Add-ProbeOverflow "claude $($A -join ' ')" $ClaudePluginCap }
      @{ Rc = $crc; Text = (@(Get-Content -LiteralPath $cl -Encoding UTF8 -ErrorAction SilentlyContinue) -join "`n") }
    } finally { Remove-Item -LiteralPath $cl, "$cl.err" -ErrorAction SilentlyContinue }
  }
  # 깔린 플러그인 표 — `plugin list --json` 이 0 으로 끝나 낸 글에서 `id` → 켜졌나. 못 읽으면 $null(못 잰 것)이다.
  # ⚠ **빈 글은 못 잰 것이다** — PowerShell 5.1 의 `ConvertFrom-Json` 은 빈 글에 던지지 않고 빈 값을 내, 그대로 두면 「아무것도
  #   안 깔렸다」로 읽혀 목록을 못 받은 판에 다 다시 깐다. 깔린 것이 없는 목록은 `[]` 로 온다.
  # ⚠ **배열을 파이프로 한 번 더 풀어 센다** — 같은 판의 `ConvertFrom-Json` 은 JSON 배열을 한 덩어리로 내, 그대로 돌면 행이
  #   아니라 배열 하나를 돈다.
  $readPlugins = { param($Ask)
    if ($Ask.Rc -ne 0) { return $null }
    try { $parsed = ConvertFrom-Json -InputObject $Ask.Text -ErrorAction Stop } catch { return $null }
    if ($null -eq $parsed) { return $null }
    $t = @{}
    foreach ($r in @($parsed | ForEach-Object { $_ })) { if ($r -and $r.id) { $t[[string]$r.id] = ($r.enabled -eq $true) } }
    $t
  }
  $plWhy = { param($Ask) if ($Ask.Rc -eq 0) { '낸 글이 JSON 으로 안 읽혀' } else { Format-ProbeWhy $Ask.Rc $ClaudePluginCap } }
  $pl = & $askClaude @('plugin','list','--json')
  $have = & $readPlugins $pl
  if ($null -eq $have) {
    Add-UnmeasuredStep 'Anthropic 공식 스킬' 'claude plugin list --json' '있는지 못 재 깔지도 않았다' (& $plWhy $pl)
    Write-Host $officialHand
  } else {
    foreach ($id in $officialIds) {
      if (-not $have.ContainsKey($id)) { continue }
      if ($have[$id]) { Write-Host "  Anthropic 공식 스킬 — 있음: $id" }
      else { Write-Host "  Anthropic 공식 스킬 — 깔렸는데 꺼져 있다: $id · 켜려면  claude plugin enable $id" }
    }
    $missing = @($officialIds | Where-Object { -not $have.ContainsKey($_) })
    if ($missing.Count) {
      $mk = & $askClaude @('plugin','marketplace','list')
      if ($mk.Rc -eq -2) {
        Add-UnmeasuredStep 'Anthropic 공식 스킬' 'claude plugin marketplace list' '깔지 않았다' (Format-ProbeWhy -2 $ClaudePluginCap)
        Write-Host $officialHand
      } else {
        Say-Busy 'Anthropic 공식 스킬' 'install' @('claude plugin', ($missing -join ' · '))
        # 부름마다 제 로그 — `Invoke-Logged` 는 로그를 덮어써, 하나에 모으면 앞서 진 것의 끝 줄이 뒤엣것에 지워진다.
        $logs = @{}
        $rc = 0
        if (-not $mk.Text.Contains($OfficialSkills.Market)) {
          $logs['market'] = [IO.Path]::GetTempFileName()
          $rc = Invoke-Logged 'claude' @('plugin','marketplace','add',$OfficialSkills.Source) $logs['market']
        }
        if ($rc -eq 0) {
          foreach ($id in $missing) {
            $logs[$id] = [IO.Path]::GetTempFileName()
            $irc = Invoke-Logged 'claude' @('plugin','install',$id) $logs[$id]
            if ($irc -ne 0) { $rc = $irc }
          }
        }
        $pl = & $askClaude @('plugin','list','--json')
        $have = & $readPlugins $pl
        if ($null -eq $have) {
          Add-UnmeasuredStep 'Anthropic 공식 스킬' 'claude plugin list --json' '깔았나를 못 쟀다' (& $plWhy $pl)
        } else {
          foreach ($id in @($missing | Where-Object { $have.ContainsKey($_) })) { Write-Host "  Anthropic 공식 스킬 — 깔았다: $id" -ForegroundColor Green }
          $still = @($missing | Where-Object { -not $have.ContainsKey($_) })
          if ($still.Count) {
            Write-Host "  ! Anthropic 공식 스킬 — 못 깔았다 ($rc): $($still -join ' · ') · Claude Code 는 그대로 돈다 — 뱉은 끝 줄:" -ForegroundColor Yellow
            foreach ($k in @(@('market') + $still)) { if ($logs.ContainsKey($k)) { Show-Log $logs[$k] } }
            Write-Host $officialHand
          }
        }
        foreach ($f in $logs.Values) { Remove-Item -LiteralPath $f -ErrorAction SilentlyContinue }
      }
    }
  }
}

# agy 의 Google 로그인은 회사 설정이 안 서는 자리의 몫이다 — 사내는 회사 키로 게이트웨이를 타서(`$wantAgy` · 「Codex · 안티그래비티
#   설정」 칸) 로그인 없이 agy 맡기기가 선다.
if ($wantAgyDelegate -and -not $wantAgy) {
  Write-Host '  agy 가 로그인 전이면 터미널에서 agy 를 한 번 띄워 Google 계정으로 로그인한다'
}

} catch { Write-StepFault $_ }
Exit-Step 'register'

# ══ 마무리 ═════════════════════════════════════════════════════════════════════════════════════
#   층 — 없음(걸음 뒤)
#   하는 일 — 넘겨받은 임시 값 파일 지우기 · 회차를 넘기는 기록 · 사용자 범위 명령 자리를 사용자 PATH 에 · 바로가기 · 로그온 자동
#     실행 · 끝 검증 · 앱 열기 · 끝 줄 · 종료 코드
#   앞에서 받는 것 — 앞 걸음 전부
#   안 하는 것 — 없음
#   경계 — 끝 검증 앞까지(임시 값 파일 · 기록 · 사용자 PATH · 아이콘 · 자동 실행)가 칸 「마무리」, 끝 검증의 재기가 칸 「검증」이다.
#     둘 다 걸음과 같은 경계(`Write-StepFault`)를 둘러 마무리에서 진 것도 끝 검증을 안 빼고, 검증에서 진 것도 끝 줄 · 종료 코드를 안 뺀다
try {  # 칸 경계 「마무리」 — 아래 catch 까지가 이 칸이다(`Write-StepFault`)
# ── 넘겨받은 임시 값 파일을 여기서 지운다 — **읽기가 다 끝난 첫 자리다** ────────────
# 화면 껍데기도 지우지만 그 손은 제 프로세스가 살아 있을 때만 돈다 — 껍데기가 죽으면 평문 토큰이 든 파일이 `%TEMP%` 에
#   눌러앉고, 다음 판은 PID 가 달라 그 이름을 다시 안 써 아무도 안 지운다. 그래서 몸통도 지운다 — 값을 다 읽은 자리가 가장
#   이르다(그 파일에서 읽는 것은 「준비」와 「키와 값」이 다 읽었다).
# ⚠ **넘겨받은 것만 지운다** — 옆에 둔 `install.env` 는 사람 것이고 이 파일의 기본값이라, 지우면 다음 판이 값 없이 선다. 근거
#   둘이 다 서야 한다 — `-EnvFile` 로 받았나와 임시 폴더 아래인가. 하나만 보면 `-EnvFile .\install.env` 로 부른 사람의 파일을 지운다.
if ($PSBoundParameters.ContainsKey('EnvFile') -and $EnvFile) {
  $envFull = ''
  try { $envFull = [IO.Path]::GetFullPath($EnvFile) } catch { }
  $tmpRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
  if ($envFull -and $envFull.StartsWith($tmpRoot, [StringComparison]::OrdinalIgnoreCase) -and
      (Test-Path -LiteralPath $envFull)) {
    Remove-Item -LiteralPath $envFull -Force -ErrorAction SilentlyContinue
  }
}

# ── 회차를 넘기는 기록 — **사람이 고른 것만, 회차마다 쓴다** (PAISetup #45) ─────────────────────────
# 자리 · 꼴 · 읽는 손은 파일 머리의 「회차를 넘기는 기록의 자리」 칸이 든다. 이번 회차의 사람 값(「준비」의 「지난번에 고른 것」 칸이
#   정한 것)을 적는다 — 자동 실행을 켰나 · 밤 회차인가와 상관없다. 짐의 줄 · `#site` · 키는 안 적는다(키는 사용자 환경에만 산다).
# 오타뿐인 `-Pick`(「고른 제품」 칸이 빨강으로 센 판)은 제품을 못 정한 판이라 지난 기록의 제품과 그에 매인 제작자 칸을 잇는다 — 제작자
#   칸은 고른 제품에서만 서서, 그 판의 값(`none`)을 적으면 오타 한 번에 제작자 칸이 지워진다.
# VS Code 는 사람이 고른 값(`$NoVsCodeChosen`)을 적는다 — 사내에서 필수라 깐 판(「준비」의 「자리」 칸)도 사람의 「끔」을 지우지 않는다.
# 새 기록을 쓴 뒤 옛 꼴 둘을 걷는다 — 남겨 두면 그 꼴을 읽는 옛 자동 실행 스크립트가 지난 판 짐의 줄과 낡은 선택을 다시 넘긴다.
#   못 쓰면 옛 꼴을 두고 말한다 — 다음 회차가 그것을 다시 읽는다.
$recValue = @{
  'pick'        = $(if ($PickUnreadable -and $Recorded['pick']) { $Recorded['pick'] }
                    elseif ($PickKeys.Count) { $PickKeys -join ',' } else { $ChoiceNone })
  'vscode'      = $(if ($NoVsCodeChosen) { 'no' } else { 'yes' })
  'devtools'    = $(if ($NoDevTools) { 'no' } else { 'yes' })
  'personal'    = $(if ($PickUnreadable -and $Recorded['personal']) { $Recorded['personal'] } else { $PersonalValue })
  'config-repo' = $(if ($configRepoUrls.Count) { $configRepoUrls -join ' ' } else { $ChoiceNone })
  'gateway-url' = $(if ($TypedGatewayUrl) { $TypedGatewayUrl } else { $ChoiceNone })
}
try {
  if (-not (Test-Path -LiteralPath $RecordRoot)) { New-Item -ItemType Directory -Path $RecordRoot -Force -ErrorAction Stop | Out-Null }
  $recLines = @('# PAISetup — 사람이 고른 것. 설치기가 회차마다 다시 쓴다 (설치 창 · 자동 실행이 읽는다)') +
              @($ChoiceKeys | ForEach-Object { '{0}={1}' -f $_, $recValue[$_] })
  # 갈아 끼워 쓴다(`Write-FileSafely`) — 쓰다 멎으면(전원 · 잠금 · 디스크) 반쪽 기록 대신 지난 기록이 그대로 남는다. 바이트 꼴은 옛 판이
  #   `Set-Content -Encoding UTF8` 로 쓰던 그대로다(BOM · CRLF · 끝 줄바꿈).
  $recOld = $null
  if (Test-Path -LiteralPath $ChoiceRecord -PathType Leaf) { $recOld = [IO.File]::ReadAllBytes($ChoiceRecord) }
  $recBytes = [byte[]]((New-Object Text.UTF8Encoding($true)).GetPreamble() + (New-Object Text.UTF8Encoding($false)).GetBytes((($recLines -join "`r`n") + "`r`n")))
  $recWrote = Write-FileSafely $ChoiceRecord $recBytes $recOld
  if ($recWrote.Did -cne 'written' -and $recWrote.Did -cne 'same') { throw $recWrote.Why }
  Remove-Item -LiteralPath $LegacyChoiceArgs, $LegacyChoiceEnv -Force -ErrorAction SilentlyContinue
} catch {
  Write-Host "  ! 고른 것을 다음 회차에 남기지 못했다 — $(Say-Why $_) (다음 회차는 지난 기록으로 간다)" -ForegroundColor Yellow
}

# ── 사용자 범위 명령 자리 — **사용자 PATH 에 심어야 설치가 끝난 뒤에도 선다** (claude-config 결정 0143 · PAISetup #30 ②) ─────────────
# 이 설치와 넘긴 훅이 사용자 범위에 깐 명령은 두 폴더에 선다 — npm 전역 자리(`$NpmGlobalDir` · 고른 CLI 와 훅의 npm 전역 도구)와 pip 의
#   사용자 자리(`Measure-PipUserScripts` · 훅의 `pip install --user` 와, 기본 자리에 못 쓰는 파이썬에서 물러선 이 설치의 파이썬
#   패키지). npm 도 pip 도 그 자리를 PATH 에 안 심고 배선(`Update-RuntimePath`)은 이 창만 태워서, 심지 않으면 새 터미널에서 깔린 명령이
#   이름으로 안 잡힌다(PAISetup #29 · PAISetup #30 — 공식 pptx 스킬이 `markitdown` 명령을 부른다).
# ⚠ **두 폴더를 채우는 걸음이 다 지난 여기서 심는다** — 「CLI」 · 「공용 자산」(파이썬 패키지) · 「설정 저장소」(넘긴 훅의 전역 도구)가
#   채운다. 그 앞에서 심으면 맨바닥 PC 의 첫 설치는 폴더가 아직 없어 못 심고 다음 로그온까지 비어 있다.
# 폴더가 있을 때만 심는다 — 무엇이든 깔아야 생기는 폴더다. 걷는 손은 없다 — 같은 자리를 다른 설치나 사람이 넣었을 수 있다(결정 0143).
$PipUser = Measure-PipUserScripts
if ($PipUser.State -eq 'unmeasured') { Add-UnmeasuredStep 'pip 사용자 자리' $PipUser.Probe '사용자 PATH 에 안 더했다' $PipUser.Why }
foreach ($ud in @(@{ Label = 'npm 전역 자리'; Dir = $NpmGlobalDir; What = 'npm 으로 깐 CLI 가' },
                  @{ Label = 'pip 사용자 자리'; Dir = $PipUser.Dir; What = 'pip 가 사용자 자리에 깐 명령이' })) {
  if (-not $ud.Dir -or -not (Test-Path -LiteralPath $ud.Dir)) { continue }
  $udPath = Add-ToUserPath $ud.Dir
  switch ($udPath.Did) {
    'kept'  { Write-Host "  $($ud.Label) — 사용자 PATH 에 이미 있다 ($($ud.Dir))" }
    'added' {
      Write-Host "  $($ud.Label) — 사용자 PATH 에 더했다 ($($ud.Dir)) · 새로 여는 터미널부터 $($ud.What) 이름만으로 선다" -ForegroundColor Green
      if (-not $udPath.Notified) {
        Write-Host '    ! 열린 프로그램에 바뀐 것을 못 알렸다 — 다음 로그온부터 새 터미널이 본다' -ForegroundColor Yellow
      }
    }
    'toolong' {
      Write-Host ("  ! {0} — 사용자 PATH 에 안 더했다: 더하면 PATH 가 {1:N0} 자로 환경변수 한도({2:N0})를 넘는다 · 안 쓰는 자리를 걷고 다시 누른다" -f $ud.Label, $udPath.Len, $EnvVarMax) -ForegroundColor Red
      $Fails.Add("$($ud.Label) (PATH 길이 한도)")
    }
    default {
      Write-Host "  ! $($ud.Label) — 사용자 PATH 에 못 더했다 — $(Say-Why $udPath.Err)" -ForegroundColor Red
      $Fails.Add("$($ud.Label) (사용자 PATH)")
    }
  }
}

# ── 바탕화면·시작 메뉴 아이콘 ───────────────────────────────────────────────────
# ⚠ **가리키는 곳은 판에 안 매인 한 자리(`…\Claude Code Setup\Setup.exe`)다** — 판마다 제 폴더(`…\Claude Code Setup\<판>\`)를
#   가리키면 다음 판에서 죽는다. 설치본이 제 자신을 그 위 한 자리에 복사해 두어, 새 판을 누를 때마다 그 자리가 최신으로 갈린다.
# ⚠ 아이콘 칸은 안 쓴다 — 바로가기가 exe 를 가리키면 윈도우가 그 안의 아이콘을 쓰고, 아이콘 칸은 절대 경로만 먹어 zip 을 건너면
#   깨진다.
# `Setup.exe` 가 없으면 건너뛴다 — `install.cmd` 로 직접 들어온 갈래에는 그 파일이 없다. 진 것도 실패로 세지 않는다 — 바로가기는
#   덤이라 빨강으로 세면 멀쩡히 깔린 기계가 빨갛게 보고된다(「연다」 칸과 같은 까닭).
$launcher = Join-Path $env:LOCALAPPDATA 'Claude Code Setup\Setup.exe'
if (Test-Path -LiteralPath $launcher) {
  Write-Host ''
  Write-Host '  바탕화면 · 시작 메뉴에 아이콘을 둔다'
  $made = @()
  try {
    $sh = New-Object -ComObject WScript.Shell
    # ⚠ **두 자리 다 `GetFolderPath` 로 판다** — 경로를 박으면 OneDrive · 폴더 리다이렉션을 안 따라가, 시작 메뉴를 리다이렉트한
    #   사내 VDI 에서 `Test-Path` 가 거짓이라 조용히 건너뛰고 아무 줄도 안 남는다.
    $spots = @(
      @{ Name = '바탕화면';   Dir = [Environment]::GetFolderPath('Desktop') }
      @{ Name = '시작 메뉴'; Dir = [Environment]::GetFolderPath('Programs') }
    )
    # 우리가 예전에 쓴 이름의 아이콘을 걷는다 — `.lnk` 는 파일 이름이 곧 표시 이름이라, 이름을 바꾸면 옛 것이 그대로 남아 같은
    #   `Setup.exe` 를 가리키는 아이콘이 둘 선다.
    # ⚠ **값 파일의 `#app-name` 을 바꾸는 판에 지금 이름을 이 목록에 더한다** — 지금 이름은 그 줄이 진본이고(`$AppName`), 옛 이름은
    #   어느 원본에도 안 남는 이력이라 여기만 든다. 남이 만든 바로가기를 안 지우려고 아무 `.lnk` 가 아니라 목록으로 걷는다.
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

# ── 부팅 시 자동 실행 (작업 스케줄러) ─────────────────────────────────────────
# **로그온할 때와 밤마다 이 몸통을 다시 돌린다** — 깔린 것을 최신으로 올리고 환경을 다시 맞춘다. 둘 다 창 없이
#   시작하고, 로그온 회차가 설치를 실제로 할 때만 기록 창을 띄운다(아래 「문지기 · 머리 없는 콘솔」).
#   `-AutoRun` 이나 값 파일의 `#autorun = yes` 가 켜고, `-NoAutoRun` 이나 `no` 가 걷는다. `-NoAutoRun` 으로 걷으면 끈 기록을 적어
#   `yes` 가 다시 켜지 못하게 한다(위 「자동 실행을 켜나」 칸).
# 설치본 자체도 새 릴리스로 간다 — 아래 스크립트 본문의 「설치본 자신을 새 릴리스로 간다」 칸이 `#update-repo` 의 최신 릴리스를
#   받아 `update-check.ps1` 로 지문을 대조하고, 맞으면 `Setup.exe -Unattended` 로 풀어 그 판의 엔진으로 설치를 잇는다. 설치 창의
#   자가 갱신(「새 판이 있습니다」 물음)과 같은 자를 쓴다.

# 작업은 둘이다 — 로그온 작업과 밤 작업. 로그온은 다시 부팅할 때만 나서, 절전 · 화면 잠금으로 며칠을 잇는 PC 는 로그온
#   하나로는 그 사이 한 번도 안 돈다(PAISetup #36). 밤 작업이 그 PC 를 날마다 한 번 돌리고, 그 시각에 꺼져 있거나 절전이면
#   `StartWhenAvailable` 이 켜진 뒤 따라 돌린다. 깨우지는 않는다.
#   · 작업을 가르는 까닭 — 작업 스케줄러는 어느 트리거가 불렀는지 실행에 안 넘긴다. 밤 회차는 자리(사내 · 사외)를 안
#     바꾸고 창도 안 띄워야 하므로, 제 인자(`-Night`)와 제 창 모양을 든 작업을 따로 둔다
#   · 밤 시각 — 부팅해 로그온 회차를 이미 받은 사람이 낮에 자동 실행 창을 다시 안 보게 사람이 고른 값이다
#   · 흩는 폭 — 로그온은 사람마다 시각이 갈리지만 달력은 PC 전부를 한 분에 띄운다. 한 출구 주소를 같이 쓰는 회사 PC 들이
#     같은 분에 릴리스를 묻지 않게 흩되, 이른 출근 전(05시)에 끝나는 폭으로 둔다. 잰 값이 아니라 판단이다
#   · 문지기 · 머리 없는 콘솔 — 두 작업은 몸통을 바로 부르지 않고 곁의 문지기(`$AutoRunGate`)를 머리 없는 콘솔로 부른다.
#     건너뛰는 회차는 아무 창도 안 띄우고, 로그온 회차가 설치를 실제로 할 때만 몸통이 기록 창을 띄운다. 밤 회차는 몸통이 밤
#     회차를 아는 판(`$AutoRunNightMarker` 를 든다)일 때만 `-Night` 로 부르고, 아니면 밤 작업을 걷는다 — 옛 판 설치기가 몸통을
#     다시 쓰면 그 몸통은 `-Night` 를 버리고 로그온 회차처럼 돌아 자리를 바꿀 수 있다
# 하루 한 번 · 밤 회차의 자리는 몸통(아래 `autorun.ps1`)의 「하루 한 번 · 자리」 칸이 가른다. 그 칸이 읽는 지난 설치의 자리는
#   위 「자동 실행을 켜나」 칸과 아래 「지난 설치의 자리」 줄(`$AutoRunSiteRecord`)이 적는다.
# 작업 이름 둘(`$AutoRunTaskName` · `$AutoRunNightTaskName`)과 끈 기록의 자리(`$AutoRunOffRecord`)는 파일 머리의 「회차를 넘기는 기록의
#   자리」 칸이 든다 — `-Describe` 와 「자동 실행을 켜나」 칸이 먼저 읽는다.
# 사람이 고른 것의 기록은 자동 실행의 몫이 아니다 — 켜든 끄든 「회차를 넘기는 기록」 칸이 쓰고, 몸통이 회차마다 그 기록을 읽는다.
$AutoRunNightAt       = [datetime]::Today.AddHours(3)
$AutoRunNightSpread   = New-TimeSpan -Hours 2
$AutoRunGate          = 'autorun-gate.ps1'
$AutoRunNightMarker   = 'param([switch]$Night)'

# 켤지 걷을지(`$wantAutoRun`)는 위 「자동 실행을 켜나」 칸이 정했다.
if ($null -ne $wantAutoRun) {
  Write-Host ''
  if ($wantAutoRun) {
    $setupRoot = Join-Path $env:LOCALAPPDATA 'Claude Code Setup'
    if (-not (Test-Path -LiteralPath $setupRoot)) { New-Item -ItemType Directory -Path $setupRoot -Force | Out-Null }
    # 거는 판은 끈 기록을 지운다 — 사람이 다시 켰다(깃발 없는 판이 여기 오는 것도 작업이 서 있거나 기록이 없을 때뿐이다).
    Remove-Item -LiteralPath $AutoRunOffRecord -Force -ErrorAction SilentlyContinue
    $autoScript = Join-Path $setupRoot 'autorun.ps1'

    $autoScriptBody = @'
# `-Night` — 밤 작업이 부른 회차다. 아래 「하루 한 번 · 자리」 칸이 자리를 안 바꾸게 다룬다. 없으면 로그온 회차다.
param([switch]$Night)
$ErrorActionPreference = 'SilentlyContinue'

# ⚠ **이 창의 빠른 편집(QuickEdit)을 끈다** — 켜져 있으면 창을 한 번 누르는 것만으로 선택 모드가 되어(제목에 「선택」) 이 창에
#   글을 쓰는 쪽이 전부 멈춘다. 사람이 안 지켜보는 창이라 멎은 줄도 모르고, 로그도 그 줄에서 끊긴다.
#   입력 모드에서 그 비트 하나만 내리고 나머지는 그대로 둔다. 창 없이 돌아 콘솔이 아니면 모드를 못 읽으므로 그냥 지나간다 — 이
#   칸이 져도 설치는 간다.
try {
  Add-Type -Namespace PAISetup -Name ConsoleMode -MemberDefinition @"
[DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int n);
[DllImport("kernel32.dll")] public static extern bool GetConsoleMode(IntPtr h, out uint m);
[DllImport("kernel32.dll")] public static extern bool SetConsoleMode(IntPtr h, uint m);
"@
  $conIn = [PAISetup.ConsoleMode]::GetStdHandle(-10)
  $conMode = [uint32]0
  if ([PAISetup.ConsoleMode]::GetConsoleMode($conIn, [ref]$conMode)) {
    # 0x40 = ENABLE_QUICK_EDIT_MODE. 0x80(ENABLE_EXTENDED_FLAGS) 이 서 있어야 이 비트를 내린 값이 먹는다.
    if ($conMode -band 0x40) { $conMode = $conMode - 0x40 }
    [void][PAISetup.ConsoleMode]::SetConsoleMode($conIn, ($conMode -bor 0x80))
  }
} catch { }

$setupRoot = Join-Path $env:LOCALAPPDATA 'Claude Code Setup'
$logDir    = Join-Path $setupRoot 'logs'
if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
# 이름에 PID 를 넣는다 — 부팅 뒤 밤 회차와 로그온 회차는 같은 초에 설 수 있고, 그러면 두 회차가 한 기록에 섞인다.
$logFile   = Join-Path $logDir ("autorun-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + "-$PID.log")

function Log([string]$msg) {
  $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
  Write-Host $line
  Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8
}

# 첫 줄에 제 PID 를 적는다 — 뒤 회차의 가드가 이 기록을 이 회차가 글자를 내는 자리로 찾는다(아래 `Find-RunOutput`).
$runKind = if ($Night) { '밤 작업' } else { '로그온 작업' }
Log "=== PAISetup 자동 실행 시작 (PID $PID) · $runKind ==="

# 기록은 최근 것만 둔다 — 건너뛰는 회차도 기록을 하나씩 남기므로 시작마다 거둔다. 지금 회차의 기록은 가장 새것이라 남는다.
#   이름의 PID 가 아직 살아 있는 기록은 안 거둔다 — 아래 가드는 멎은 회차를 그 기록으로 가르므로(`Find-RunOutput`), 지우면 그
#   회차를 영영 못 거둔다. PID 를 남이 물려받았으면 한 벌 더 남을 뿐이다.
$keepLogs = 15
try {
  $livePids = @{}
  foreach ($lp in @(Get-Process -ErrorAction SilentlyContinue)) { $livePids[[int]$lp.Id] = $true }
  Get-ChildItem -LiteralPath $logDir -Filter 'autorun-*.log' -File -ErrorAction Stop | Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $keepLogs |
    Where-Object { -not ($_.Name -match '-(\d+)\.log$' -and $livePids.ContainsKey([int]$Matches[1])) } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue }
} catch { }

# 지난 회차의 끝을 이 기록에 옮긴다 — 머리 없는 콘솔은 종료 코드를 작업 스케줄러에 안 넘겨, 작업의 「마지막 실행 결과」는 진 회차도
#   0 이다. 진 것은 다음 회차의 기록(로그온 회차면 기록 창)에서 보인다.
$lastFile = Join-Path $setupRoot '.autorun-last'
if (Test-Path -LiteralPath $lastFile) {
  try {
    $prevSaid = (Get-Content -LiteralPath $lastFile -Raw -Encoding UTF8 -ErrorAction Stop).Trim()
    if ($prevSaid -match '\s(\S+)$' -and $Matches[1] -ne '0') { Log "! 지난 회차가 성공으로 안 끝났다 — $prevSaid" }
    else { Log "지난 회차 — $prevSaid" }
  } catch { }
}

# 「오늘 끝났다」 — 자동 실행이 설치를 0 으로 끝내고 적은 `.autorun-stamp` 의 날짜가 이 PC 의 오늘인 것이다. 사람이 누른 설치는 이
#   몸통을 안 지나므로 이 가름 없이 늘 돈다. 밤 회차는 여기서 바로 물러난다 — 가드도 자리 재기도 안 거친다. 로그온 회차의 가름은
#   아래 「하루 한 번 · 자리」 칸이 든다.
$stampFile = Join-Path $setupRoot '.autorun-stamp'
$doneAt = $null
if (Test-Path -LiteralPath $stampFile) {
  try { $doneAt = [datetime]((Get-Content -LiteralPath $stampFile -Raw -Encoding UTF8 -ErrorAction Stop).Trim()) } catch { $doneAt = $null }
}
$doneToday = [bool]($doneAt -and $doneAt.Date -eq (Get-Date).Date)
if ($Night -and $doneToday) {
  Log "오늘 이미 자동 실행이 끝났습니다 ($($doneAt.ToString('HH:mm'))). 밤 회차는 건너뜁니다."
  exit 0
}

function Normalize-Version([string]$v) {
  $v = ($v -replace '^[vV]', '').Trim()
  $parts = $v -split '\.'
  while ($parts.Count -lt 4) { $parts += '0' }
  return [version]($parts[0..3] -join '.')
}

# 판 폴더 — 몸통과 짐(`install.env`)이 다 선 것만 센다. 반만 풀린 폴더를 가장 높은 판으로 고르면 `#update-repo` · `#site-probe` 를
#   못 읽어 새 판을 영영 안 묻고, 몸통도 짐 없이 돈다. 아래 가드가 엔진의 자를 떼어 오려고 먼저 부른다.
function Find-Versions {
  return @(Get-ChildItem -Path $setupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^\d+(\.\d+)+' -and (Test-Path (Join-Path $_.FullName 'install.ps1')) -and (Test-Path (Join-Path $_.FullName 'install.env')) } |
    Sort-Object { Normalize-Version $_.Name } -Descending)
}

# 엔진에서 그 이름들의 함수 정의 글을 이름 차례로 낸다. 하나라도 못 찾으면 빈 목록. 가드(엔진 알아보기)와 「하루 한 번 · 자리」 칸이 쓴다.
function Get-EngineFunctionText([string]$Engine, [string[]]$Names) {
  $tk = $null; $er = $null
  $ast = [System.Management.Automation.Language.Parser]::ParseFile($Engine, [ref]$tk, [ref]$er)
  $texts = New-Object System.Collections.ArrayList
  foreach ($n in $Names) {
    $fn = $ast.Find({ param($x) $x -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $x.Name -eq $n }.GetNewClosure(), $true)
    if (-not $fn) { return }
    [void]$texts.Add($fn.Extent.Text)
  }
  $texts
}

# ── 단일 실행 가드 및 쿨다운 (겹침 방지) ───────────────────────────
# 로그온 · 밤 작업과 밖의 부팅 자동화가 연달아 돌거나 겹치면 같은 설치를 두 번 하거나 설치기의 빗장(Mutex)에 걸린다(PAISetup #13).
# 1) 다른 autorun 또는 install 프로세스가 있으면 멎었나 잰다 — 멎었다고 가르지 못한 것이 하나라도 있으면 즉시 종료한다.
# 2) 다 멎었으면 거두고 제 일을 잇는다.
# 3) 최근 10분 내에 이미 성공적으로 완료되었으면 건너뛴다.
# ⚠ **「도는 것」과 「멎은 것」을 가른다** — 있나만 보면 설치 하나가 멎을 때 이 PC 의 자동 실행이 영구히 물러난다. 스케줄 작업은
#   `State: Ready` · `LastTaskResult: 0` 으로 초록이라 작업 쪽을 봐도 단서가 없다(PAISetup #27).
# 여기는 물을 사람이 없어 기계가 가린다(설치기의 빗장 칸은 PID 와 경과를 대고 사람에게 묻는다). 가르는 자는 둘이다 — 그 회차가
#   낸 글자가 한도를 넘게 안 자랐나, 그 프로세스와 자손이 CPU 를 쓰나. 둘 다 섰으면 멎은 것이다.
# ⚠ 기본값은 「안 거둔다」다 — 의심스러운 것을 거두면 빗장이 막으려던 반쪽 상태를 우리가 만든다. 그래서 가르지 못한 것은
#   물러난다. 글자를 내는 자리가 없는 회차(콘솔로 깐 설치)는 CPU 하나로 가르지 않고 늘 둔다(claude-config 결정 0142).
$myPid = $PID
$myProc = Get-CimInstance Win32_Process -Filter "ProcessId = $myPid" -ErrorAction SilentlyContinue
$parentPid = if ($myProc) { $myProc.ParentProcessId } else { 0 }
# 「우리 엔진인가」는 엔진의 자(`Get-EngineKind`)를 떼어 와 가른다 — 설치 몸통의 겹침 찾기와 같은 자다(같은 규칙을 여기 옮겨 적으면
#   한쪽만 낡는다). 그 자가 우리 설치 몸통과 자동 실행 몸통을 다 알아보고, 같은 이름의 남 스크립트와 로그인 창 자식(`-GhLoginOnly`)은
#   뺀다. 떼어 올 엔진은 가장 높은 판 폴더의 몸통이다(아래 새 판 받기가 돌릴 그 몸통).
# ⚠ 못 들였으면 넓게 센다 — 명령줄에 두 이름(`install.ps1` · `autorun.ps1`)을 든 것을 다 우리 것으로 본다. 못 가른 것을 세는 쪽이
#   가드의 기본값(물러난다)과 같고, 그 판은 기록에 그렇다고 남는다.
# 거둔 뒤 다시 재는 자리도 같은 자로 잰다.
$engineRuleOk = $false
try {
  $ruleEngine = @(Find-Versions)[0]
  if ($ruleEngine) {
    $ruleNames = @('Get-EngineKind')
    $ruleDef = @(Get-EngineFunctionText (Join-Path $ruleEngine.FullName 'install.ps1') $ruleNames)
    if ($ruleDef.Count -eq 1) { . ([scriptblock]::Create($ruleDef[0])); $engineRuleOk = $true }
  }
} catch { $engineRuleOk = $false }
if (-not $engineRuleOk) { Log "! 엔진을 알아보는 자(Get-EngineKind)를 가장 높은 판의 몸통에서 못 들였다 — 명령줄에 install.ps1 · autorun.ps1 을 든 것을 다 센다" }
function Get-OtherEngines {
  @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $myPid -and $_.ProcessId -ne $parentPid -and $(
      if ($engineRuleOk) { [bool](Get-EngineKind $_) }
      else { "$($_.CommandLine)" -match '(?i)(install|autorun)\.ps1' -and "$($_.CommandLine)" -notlike '*-GhLoginOnly*' }) })
}
$otherEngines = @(Get-OtherEngines)

# 멎었다고 보는 한도 — 그 회차의 글자가 이 분을 넘게 안 자랐어야 고아로 본다. 사람이 묻는 창 앞에서
#   자리를 비운 설치를 멎은 것과 가를 길이 없어(관리자 승인 창은 그 프로세스 나무 밖에 뜬다) 점심 ·
#   회의만큼 비워도 안 걸리게 넉넉히 둔다(결정 0142).
$orphanMin = 180
# 한 번 재는 창과, 그 사이 프로세스 나무가 쓴 CPU 가 이 초를 넘으면 「움직였다」로 보는 값.
#   두 번 재어 견준다 — 한 번의 사진으로는 느린 것과 멎은 것이 같아 보인다.
$stallWindowSec = 20
$stallCpuSec    = 0.05
$taskkillExe    = Join-Path $env:SystemRoot 'System32\taskkill.exe'

# 지금 도는 프로세스 전부를 PID 로 찾는 표. 못 읽으면 던진다(부르는 쪽이 「못 쟀다」로 받는다).
function Get-ProcTable {
  $t = @{}
  foreach ($x in @(Get-CimInstance Win32_Process -ErrorAction Stop)) { $t[[int]$x.ProcessId] = $x }
  return $t
}

# 그 프로세스와 자손 — 자식은 부모보다 늦게 선 것만 잇는다. 부모 PID 만 따라가면 그 PID 를 앞서 쓴
#   죽은 부모의 자식(먼저 선 남)이 끼어, 재기에도 거두기에도 남이 든다.
# 내는 것 — Win32_Process 목록, 뿌리가 맨 앞. 뿌리가 표에 없으면 빈 목록.
function Get-Tree($Table, [int]$RootId) {
  $kids = @{}
  foreach ($x in $Table.Values) {
    $pp = [int]$x.ParentProcessId
    if (-not $kids.ContainsKey($pp)) { $kids[$pp] = New-Object System.Collections.ArrayList }
    [void]$kids[$pp].Add($x)
  }
  $tree = New-Object System.Collections.ArrayList
  $seen = @{}
  $todo = New-Object System.Collections.Queue
  if ($Table.ContainsKey($RootId)) { $todo.Enqueue($Table[$RootId]) }
  while ($todo.Count) {
    $n = $todo.Dequeue()
    $key = '{0}@{1}' -f $n.ProcessId, $n.CreationDate.Ticks
    if ($seen.ContainsKey($key)) { continue }
    $seen[$key] = $true
    [void]$tree.Add($n)
    if ($kids.ContainsKey([int]$n.ProcessId)) {
      foreach ($c in $kids[[int]$n.ProcessId]) {
        if ($c.ProcessId -ne $n.ProcessId -and $c.CreationDate -ge $n.CreationDate) { $todo.Enqueue($c) }
      }
    }
  }
  return @($tree)
}

# 그 프로세스와 자손의 CPU 초 — 설치는 일을 자식(git · npm · winget)에 맡기고 그 끝을 기다리므로,
#   제 CPU 만 보면 일하는 설치가 멎은 것으로 보인다.
# 내는 것 — @{ "<PID>@<시작 시각>" = CPU 초 }. 두 번 잰 것의 열쇠가 다르면 그 사이 자식이 서거나 졌다.
function Get-TreeCpu($Table, [int]$RootId) {
  $cpu = @{}
  foreach ($n in (Get-Tree $Table $RootId)) {
    # Win32_Process 의 두 시간은 100 나노초 단위다.
    $cpu['{0}@{1}' -f $n.ProcessId, $n.CreationDate.Ticks] = ([double]$n.KernelModeTime + [double]$n.UserModeTime) / 1e7
  }
  return $cpu
}

# 그 회차가 글자를 내는 자리 — 제 자리와 부모를 본다.
#   · 화면 껍데기는 몸통을 cmd 로 띄우며 출력을 `claude-setup-<번호>.out` 로 돌린다 — 그 경로는 cmd 의 명령줄에 든다
#   · 자동 실행은 설치의 출력을 제 기록에 받아 적고, 그 기록의 첫 줄에 제 PID 를 적는다(위 「시작」 줄)
# 그 프로세스가 서기 전에 쓰인 파일은 안 집는다 — 그 PID 를 앞서 쓴 남의 것이다.
# 내는 것 — 파일 경로, 없으면 $null(그 회차는 멎음을 가를 축이 없다).
function Find-RunOutput($Proc, $Table) {
  $logsByPid = @{}
  foreach ($l in @(Get-ChildItem -LiteralPath $logDir -Filter 'autorun-*.log' -File -ErrorAction SilentlyContinue)) {
    $head = Get-Content -LiteralPath $l.FullName -TotalCount 1 -Encoding UTF8 -ErrorAction SilentlyContinue
    if ("$head" -match '\(PID (\d+)\)') { $logsByPid[[int]$Matches[1]] = @($logsByPid[[int]$Matches[1]]) + $l.FullName }
  }
  $cur = $Proc
  for ($up = 0; $up -lt 2 -and $cur; $up++) {
    $files = @($logsByPid[[int]$cur.ProcessId])
    if ("$($cur.CommandLine)" -match '"([^"]*\\claude-setup-\d+\.out)"') { $files += $Matches[1] }
    foreach ($f in $files) {
      if (-not $f) { continue }
      $it = Get-Item -LiteralPath $f -ErrorAction SilentlyContinue
      if ($it -and $it.LastWriteTime -ge $cur.CreationDate) { return $it.FullName }
    }
    $next = $Table[[int]$cur.ParentProcessId]
    if (-not $next -or $next.CreationDate -gt $cur.CreationDate) { break }
    $cur = $next
  }
  return $null
}

# 한 프로세스를 재어 판정한다 — 「멎었다」는 그 회차의 글자가 한도를 넘게 안 자랐고, 재는 창 동안
#   프로세스 나무가 그대로이며 CPU 도 안 움직였을 때뿐이다. 나머지는 다 「둔다」다.
# 내는 것 — @{ Verdict = 'stalled' | 'hold' | 'gone'; Why = 로그에 적을 까닭 }. 'gone' 은 재는 사이에
#   끝난 것이다 — 일하는 것으로 세지 않고 목록에서 뺀다.
function Measure-Engine($Proc) {
  try {
    $id = [int]$Proc.ProcessId
    if (((Get-Date) - $Proc.CreationDate).TotalMinutes -lt $orphanMin) {
      return @{ Verdict = 'hold'; Why = "한도(${orphanMin}분)가 안 됐다 — 안 잰다" }
    }
    $t1 = Get-ProcTable
    $r1 = $t1[$id]
    if (-not $r1 -or $r1.CreationDate -ne $Proc.CreationDate) { return @{ Verdict = 'gone'; Why = '재기 전에 끝났다 (목록에서 뺀다)' } }
    $out = Find-RunOutput $r1 $t1
    if (-not $out) { return @{ Verdict = 'hold'; Why = '글자를 내는 자리가 없어 멎었나를 못 가른다 — 안 거둔다' } }
    $f1 = Get-Item -LiteralPath $out -ErrorAction Stop
    $quietMin = ((Get-Date) - $f1.LastWriteTime).TotalMinutes
    if ($quietMin -lt $orphanMin) {
      return @{ Verdict = 'hold'; Why = ('글자가 {0}분 전에 자랐다 — 안 거둔다' -f [int]$quietMin) }
    }
    $c1 = Get-TreeCpu $t1 $id
    Start-Sleep -Seconds $stallWindowSec
    $t2 = Get-ProcTable
    $r2 = $t2[$id]
    if (-not $r2 -or $r2.CreationDate -ne $Proc.CreationDate) { return @{ Verdict = 'gone'; Why = '재는 사이에 끝났다 (목록에서 뺀다)' } }
    $f2 = Get-Item -LiteralPath $out -ErrorAction Stop
    if ($f2.Length -ne $f1.Length -or $f2.LastWriteTime -ne $f1.LastWriteTime) {
      return @{ Verdict = 'hold'; Why = '재는 사이에 글자가 자랐다 — 일하고 있다' }
    }
    $c2 = Get-TreeCpu $t2 $id
    $moved = 0.0
    $changed = $c1.Count -ne $c2.Count
    foreach ($k in $c1.Keys) {
      if ($c2.ContainsKey($k)) { $moved += $c2[$k] - $c1[$k] } else { $changed = $true }
    }
    if ($changed) { return @{ Verdict = 'hold'; Why = '재는 사이에 자식이 서거나 졌다 — 일하고 있다' } }
    if ($moved -ge $stallCpuSec) {
      return @{ Verdict = 'hold'; Why = ('재는 사이에 프로세스 나무의 CPU 가 {0:N2}초 움직였다 — 일하고 있다' -f $moved) }
    }
    return @{ Verdict = 'stalled'; Why = ('글자가 {0}분째 안 자라고 프로세스 나무({1}개)의 CPU 도 안 움직인다 (멎은 것으로 본다)' -f [int]$quietMin, $c2.Count) }
  } catch {
    # 못 재면 안 거둔다 — 못 본 것을 끝내지 않는다(사람용 가드와 같은 규율).
    return @{ Verdict = 'hold'; Why = "못 쟀다 — 안 거둔다 ($(($_.Exception.Message -split '\r?\n')[0]))" }
  }
}

# 그것이 아직 있나 — 같은 PID 에 같은 시작 시각이어야 그것이다. 못 재면 있는 것으로 본다.
function Test-Alive($Proc) {
  try {
    $now = Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$Proc.ProcessId)" -ErrorAction Stop
    return [bool]($now -and $now.CreationDate -eq $Proc.CreationDate)
  } catch { return $true }
}

# 멎은 것 하나를 나무째 거두고, 끄는 명령의 답이 아니라 **다시 잰 것**으로 답한다.
# ⚠ 끄는 명령의 성공을 믿지 않는다 — `Stop-Process -Force` 가 성공을 돌려주고도 프로세스가 목록에 남을 수 있다. `taskkill` 은
#   져도 안 던지므로 종료코드를 읽는다.
# ⚠ 끄는 것은 지금 재어 시작 시각으로 확인한 나무(`Get-Tree`)의 PID 하나하나다 — `taskkill /T` 는 부모 PID 만
#   따라가 그 PID 를 앞서 쓴 죽은 부모의 자식(먼저 선 남)까지 끈다. 뿌리를 먼저 끈다 — 자식부터 끄면 그 끝을
#   기다리던 뿌리가 다음 걸음으로 가 새 자식을 띄운다. 하나마다 끄기 직전에 아직 그것인지 다시 본다.
# 내는 것 — @{ Gone = 다시 쟀을 때 뿌리가 없나; Why = 진 명령과 그 말의 첫 줄 }. 다시 재지 못하면 남은 것으로 본다.
function Stop-Engine($Proc) {
  # 먼저 거둔 나무에 딸려 이미 끝났으면 끄지 않는다 — 그 PID 를 남이 물려받았을 수 있다.
  if (-not (Test-Alive $Proc)) { return @{ Gone = $true; Why = '끄기 전에 이미 없었다' } }
  $why = @()
  $tree = @()
  try { $tree = @(Get-Tree (Get-ProcTable) ([int]$Proc.ProcessId)) } catch { $why += "나무를 못 읽어 뿌리만 끈다 — $(($_.Exception.Message -split '\r?\n')[0])" }
  if (-not $tree) { $tree = @($Proc) }
  foreach ($n in $tree) {
    if (-not (Test-Alive $n)) { continue }
    $nid = [int]$n.ProcessId
    try { & $taskkillExe /PID $nid /F 2>$null | Out-Null; if ($LASTEXITCODE -ne 0) { $why += "taskkill 이 $LASTEXITCODE 로 끝났다 (PID $nid)" } } catch { $why += "taskkill 을 못 불렀다 (PID $nid) — $(($_.Exception.Message -split '\r?\n')[0])" }
    if (Test-Alive $n) {
      try { Stop-Process -Id $nid -Force -ErrorAction Stop } catch { $why += "Stop-Process (PID $nid) — $(($_.Exception.Message -split '\r?\n')[0])" }
    }
  }
  $gone = $false
  for ($i = 0; $i -lt 6; $i++) {
    if (-not (Test-Alive $Proc)) { $gone = $true; break }
    Start-Sleep -Milliseconds 500
  }
  return @{ Gone = $gone; Why = ($why -join ' · ') }
}

# ── 밤 회차와 로그온 회차가 겹치면 한쪽으로 기운다 (PAISetup #36) ──────────────────────────────
# 밤 회차는 고아 한도(`$orphanMin`)보다 어린 것이 돌고 있으면 재지도 거두지도 않고 물러난다 — 그날 몫은 다른 회차가 든다. 그보다
#   늙은 것만 있으면 아래 가드로 가 멎었나 재고 거둔다 — 안 그러면 다시 부팅하지 않는 PC 에서 멎은 설치를 아무도 안 거둔다
#   (작업이 시간 한도로 끝나도 머리 없는 콘솔 밑의 손자는 남는다).
# 로그온 회차가 막 선 밤 회차만 만나면 그것이 끝나기를 잠깐 기다린다. 부팅 뒤에는 놓친 밤 회차와 로그온 회차가 몇 초 사이로
#   서는데, 밤 회차는 자리가 다르면 몇 초 안에 건너뛰고 자리를 바꿀 수 있는 것은 로그온 회차뿐이다 — 둘 다 물러나면 그날 아무도
#   안 돈다. 기다려도 남아 있으면 밤 회차가 설치를 하는 중이고, 아래 가드가 로그온 회차를 물린다.
$nightYoungSec = 120
$nightWaitSec  = 30
$youngOthers = @($otherEngines | Where-Object { ((Get-Date) - $_.CreationDate).TotalMinutes -lt $orphanMin })
if ($Night -and $youngOthers) {
  Log "다른 자동 실행 또는 설치가 돌고 있어 밤 회차는 물러납니다 ($($youngOthers.ProcessId -join ', '))."
  exit 0
}
if ($otherEngines) {
  $youngNight = @($otherEngines | Where-Object {
    "$($_.CommandLine)" -match '\s-Night(\s|$)' -and ((Get-Date) - $_.CreationDate).TotalSeconds -lt $nightYoungSec })
  if ($youngNight.Count -eq $otherEngines.Count) {
    Log "막 선 밤 회차가 있습니다 ($($youngNight.ProcessId -join ', ')) — 끝나기를 최대 ${nightWaitSec}초 기다립니다."
    $waitUntil = (Get-Date).AddSeconds($nightWaitSec)
    while ((Get-Date) -lt $waitUntil -and @($youngNight | Where-Object { Test-Alive $_ }).Count) { Start-Sleep -Milliseconds 500 }
    $otherEngines = @(Get-OtherEngines)
  }
}

if ($otherEngines) {
  Log "다른 자동 실행 또는 설치 프로세스가 있습니다 ($($otherEngines.ProcessId -join ', ')). 멎었나 잽니다..."
  $stalled = @()
  $held    = @()
  foreach ($e in $otherEngines) {
    $m = Measure-Engine $e
    $ageMin = [int]((Get-Date) - $e.CreationDate).TotalMinutes
    Log "  PID $($e.ProcessId) · $($e.CreationDate.ToString('HH:mm:ss')) 시작 · ${ageMin}분째 — $($m.Why)"
    if ($m.Verdict -eq 'stalled') { $stalled += $e }
    elseif ($m.Verdict -ne 'gone') { $held += $e }
  }

  # 멎었다고 가르지 못한 것이 하나라도 있으면 물러난다 — 겹치면 반쪽 상태가 남는다.
  if ($held) {
    Log "멎었다고 가르지 못한 것이 $($held.Count) 개 있어 겹치지 않게 물러납니다 ($($held.ProcessId -join ', '))."
    exit 0
  }

  if ($stalled) {
    # 다 멎었으면 거두고 잇는다. 「거뒀다」는 다시 재어 없을 때만 적는다(위 `Stop-Engine`).
    foreach ($e in $stalled) {
      $k = Stop-Engine $e
      $said = if ($k.Why) { " ($($k.Why))" } else { '' }
      if ($k.Gone) { Log "  PID $($e.ProcessId) 을 거뒀다 — 다시 재니 없다$said" }
      else { Log "  ! PID $($e.ProcessId) 을 못 거뒀다 — 다시 재도 있다$said" }
    }
    # 거둔 뒤 가드가 보는 것 전부를 다시 잰다 — 거두는 사이 새로 선 것도 여기서 걸린다.
    $stillThere = @(Get-OtherEngines)
    if ($stillThere) {
      Log "! 거두고 다시 쟀는데 $($stillThere.Count) 개가 남았습니다 ($($stillThere.ProcessId -join ', ')). 물러납니다 — 다음 자동 실행 때 다시 잽니다."
      exit 0
    }
    Log "멎은 것을 다 거뒀습니다. 자동 실행을 잇습니다."
  } else {
    Log "재는 사이에 다 끝났습니다. 자동 실행을 잇습니다."
  }
}

if (Test-Path -LiteralPath $stampFile) {
  try {
    $lastRun = [datetime](Get-Content -LiteralPath $stampFile -Encoding UTF8 -ErrorAction Stop)
    $elapsed = (Get-Date) - $lastRun
    if ($elapsed.TotalMinutes -ge 0 -and $elapsed.TotalMinutes -lt 10) {
      Log "최근 $([int]$elapsed.TotalMinutes)분 전에 이미 자동 실행이 완료되었습니다. 건너뜁니다."
      exit 0
    }
  } catch { }
}

$versionDirs = Find-Versions

if (-not $versionDirs) {
  Log "! 설치본 폴더를 찾지 못했습니다"
  exit 1
}

# 새 판을 받기 **전에** 지금 가장 높은 판의 짐을 한 번 짚는다 — 아래 갱신 칸이 `#update-repo` 를 여기서 읽는다. 그 줄은 짐의
#   사실이라 짐에서 읽는다 — 뿌리에는 사람이 고른 것의 기록만 산다(설치기의 「회차를 넘기는 기록의 자리」 · PAISetup #45).
$targetEnvProbe = Join-Path $versionDirs[0].FullName 'install.env'

# ── 하루 한 번 · 자리 — 밤 회차는 자리를 안 바꾼다 (PAISetup #36) ────────────────────────────
# 「지난 설치의 자리」는 설치가 남긴 `.autorun-site` 다 — `inside` · `outside`, 자리에 기대는 걸음을 도는 동안은 `switching`. 사람이
#   누른 설치도 적는다.
# 「지금 자리」는 다음에 돌 엔진의 자리 재기(`Read-Directive` · `Test-Reach` · `Measure-Site`)를 떼어 와 잰다 — 설치 · 설치 창과 같은
#   자다(같은 규칙을 여기 옮겨 적으면 한쪽만 낡는다). 떼어 온 셋은 알려진 답으로 먼저 시험하고, 못 들였거나 시험에 지면 `unmeasured` 다.
#   짐의 `#site-probe` 가 없거나 꼴이 틀리면 `broken` 이고 그 까닭을 빨간 줄로 남긴다 — 그 짐의 설치도 같은 까닭으로 멈춘다.
# 가름 —
#   · 밤 회차: 지금 자리가 잰 값(`inside` · `outside`)이고 지난 설치와 같을 때만 잇고, 그 자리를 박는다(아래 「자리를 박는다」).
#     나머지는 아무것도 안 바꾸고 건너뛴다 — 집에서 깨어 있는 회사 노트북이 사외로 읽어 게이트웨이 값을 걷으면 다음 날 회사에서 그
#     값 없이 서기 때문이다
#   · 로그온 회차: 오늘 끝났으면 건너뛰되, 지금 자리를 재어 지난 설치와 다를 때만 다시 돈다 — 자리를 바꾸는 것은 로그온 회차와
#     사람이 누른 설치의 몫이다. 못 쟀으면 건너뛴다
$siteFile = Join-Path $setupRoot '.autorun-site'
$siteWord = @{ inside = '사내'; outside = '사외'; switching = '바꾸는 중에 멎음'; unmeasured = '못 쟀다'; broken = '못 정함' }

$siteLast = ''
if (Test-Path -LiteralPath $siteFile) {
  try { $siteLast = (Get-Content -LiteralPath $siteFile -Raw -Encoding UTF8 -ErrorAction Stop).Trim() } catch { $siteLast = '' }
}

# 재는 값 파일은 지금 가장 높은 판의 짐(`install.env`)이다 — 설치(그 판의 몸통)도 프로브를 제 짐에서 읽는다. 아래 새 판 받기가
#   판을 바꾸면 설치는 새 짐의 프로브를 읽고, 밤 회차는 여기서 잰 자리를 박아 넘긴다(`#site`) — 설치는 다시 재고, 박은 자리와 다르면
#   아무것도 안 심고 멈춘다(밤 회차는 자리를 안 바꾼다). 파일을 못 읽으면 못 잰 것이다.
$siteEnv = Join-Path $versionDirs[0].FullName 'install.env'
$siteNow = ''
if ($Night -or $doneToday) {
  $siteNow = 'unmeasured'
  $siteWhy = ''
  $defs = $null
  try { $defs = @(Get-EngineFunctionText (Join-Path $versionDirs[0].FullName 'install.ps1') @('Read-Directive', 'Test-Reach', 'Measure-Site')) } catch { $defs = $null }
  if ($defs.Count -eq 3) {
    # 이 스크립트 범위에 선다 — 함수 안에서 세우면 그 함수가 끝날 때 같이 사라진다.
    foreach ($d in $defs) { try { . ([scriptblock]::Create($d)) } catch { } }
    $selfOk = $false
    $selfFile = Join-Path $setupRoot ".autorun-selftest-$PID.env"
    $selfL = $null
    try {
      Set-Content -LiteralPath $selfFile -Value @('#autorun-selftest = ok') -Encoding UTF8 -ErrorAction Stop
      $selfL = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback, 0)
      $selfL.Start()
      $selfAt = '127.0.0.1:' + $selfL.LocalEndpoint.Port
      $selfOk = ((Read-Directive $selfFile 'autorun-selftest') -eq 'ok') -and ((Test-Reach $selfAt) -eq $true) -and
                ((Measure-Site $selfAt).Site -eq 'inside')
    } catch { $selfOk = $false } finally {
      if ($selfL) { $selfL.Stop() }
      Remove-Item -LiteralPath $selfFile -Force -ErrorAction SilentlyContinue
    }
    if ($selfOk) {
      $fact = $null
      try { $fact = Measure-Site (Read-Directive $siteEnv 'site-probe') } catch { $fact = $null }
      if ($fact -and $fact.Site) { $siteNow = $fact.Site }
      elseif ($fact) { $siteNow = 'broken'; $siteWhy = $fact.Why }
    }
  }
  $nowSaid  = if ($siteWord[$siteNow]) { $siteWord[$siteNow] } else { $siteNow }
  $lastSaid = if ($siteWord[$siteLast]) { $siteWord[$siteLast] } elseif ($siteLast) { $siteLast } else { '기록 없음' }
  Log "자리 — 지금 $nowSaid · 지난 설치 $lastSaid"
  if ($siteWhy) { Log "! 자리를 못 정했다 — $siteWhy · 이 짐의 설치도 같은 까닭으로 멈춘다 (설치 묶음을 새로 받는다)" }
}
$measured = ($siteNow -eq 'inside' -or $siteNow -eq 'outside')
$sameSite = $measured -and ($siteNow -eq $siteLast)

$pinSite = ''
if ($doneToday -and -not ($measured -and -not $sameSite)) {
  Log "오늘 이미 자동 실행이 끝났습니다 ($($doneAt.ToString('HH:mm'))). 건너뜁니다."
  exit 0
}
if ($Night) {
  if (-not $sameSite) {
    Log "밤 회차는 자리를 안 바꿉니다 — 지금 자리가 지난 설치와 같다고 확인되지 않아 아무것도 안 바꾸고 건너뜁니다 (자리는 로그온 · 설치 창이 바꿉니다)."
    exit 0
  }
  if ($siteNow -eq 'inside' -or $siteNow -eq 'outside') { $pinSite = $siteNow }
}

# 기록 창 — 머리 없는 콘솔로 뜬 로그온 회차(문지기가 `PAISETUP_AUTORUN_VIEWER=1` 을 넘긴다)는 제 창이 없다. 설치를 실제로 할 때만
#   — 가드 · 하루 한 번 · 자리를 다 지난 여기서, 새 판을 받기 전에 — 이 회차의 기록을 따라 읽는 창을 하나 띄우고, 끝나면 그 창
#   하나만 닫는다. 건너뛰는 회차는 아무 창도 안 띄운다. 창의 명령 줄에는 `autorun.ps1` · `install.ps1` 이 없다 — 있으면 가드들이
#   그 창을 설치로 센다. 창을 멈춰도(빠른 편집) 설치는 안 멈춘다 — 따로 도는 프로세스다.
# 창은 **최소화한 채 앞으로 안 가져오며** 띄운다(`SW_SHOWMINNOACTIVE`) — 일하는 사람의 입력을 빼앗지 않는다. `Start-Process` 로는 못
#   한다: `-WindowStyle Minimized` 는 최소화하면서도 그 창을 앞 창으로 만들어 치던 글자가 그 창으로 간다. 그래서
#   `CreateProcess` 에 보이기 값을 직접 넘긴다.
# 알려진 한계 — 이 몸통이 중간에 죽으면(작업 시간 한도 · 로그오프) 아래 닫기 칸에 안 닿아 이 창이 기록을 따라 읽은 채 남는다.
#   사람이 닫으면 된다.
$viewer = $null
$viewerStart = $null
if (-not $Night -and $env:PAISETUP_AUTORUN_VIEWER -eq '1') {
  try {
    Add-Type -Namespace PAISetup -Name Viewer -MemberDefinition @"
[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential, CharSet = System.Runtime.InteropServices.CharSet.Unicode)]
public struct SI { public int cb; public string r; public string d; public string t; public int x; public int y; public int xs; public int ys; public int xc; public int yc; public int fa; public int flags; public short show; public short r2; public System.IntPtr r3; public System.IntPtr i; public System.IntPtr o; public System.IntPtr e; }
[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)]
public struct PI { public System.IntPtr hp; public System.IntPtr ht; public int pid; public int tid; }
[System.Runtime.InteropServices.DllImport("kernel32.dll", SetLastError = true, CharSet = System.Runtime.InteropServices.CharSet.Unicode)]
static extern bool CreateProcess(string app, System.Text.StringBuilder cmd, System.IntPtr pa, System.IntPtr ta, bool inherit, uint flags, System.IntPtr env, string dir, ref SI si, out PI pi);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] static extern bool CloseHandle(System.IntPtr h);
// 새 콘솔(CREATE_NEW_CONSOLE)로, 최소화한 채 앞으로 안 가져오며(STARTF_USESHOWWINDOW · SW_SHOWMINNOACTIVE) 띄운다. 내는 것 — PID, 못 띄우면 0.
public static int StartQuiet(string app, string cmd) {
  SI si = new SI(); si.cb = System.Runtime.InteropServices.Marshal.SizeOf(si); si.flags = 1; si.show = 7;
  PI pi;
  if (!CreateProcess(app, new System.Text.StringBuilder(cmd), System.IntPtr.Zero, System.IntPtr.Zero, false, 0x10, System.IntPtr.Zero, null, ref si, out pi)) return 0;
  CloseHandle(pi.ht); CloseHandle(pi.hp); return pi.pid;
}
"@
    $viewExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $viewCmd = "`$host.UI.RawUI.WindowTitle = 'PAISetup 자동 실행'; Get-Content -LiteralPath '$($logFile.Replace("'", "''"))' -Encoding UTF8 -Wait -Tail 200"
    $viewPid = [PAISetup.Viewer]::StartQuiet($viewExe, ('"' + $viewExe + '" -NoProfile -ExecutionPolicy Bypass -Command "' + $viewCmd.Replace('"', '\"') + '"'))
    if ($viewPid) {
      $viewer = Get-Process -Id $viewPid -ErrorAction Stop
      $viewerStart = $viewer.StartTime
    }
  } catch { $viewer = $null }
}
Remove-Item Env:PAISETUP_AUTORUN_VIEWER -ErrorAction SilentlyContinue

# ── 설치본 자신을 새 릴리스로 간다 ───────────────────────────────────────────
# 제품만 올리고 설치본은 그대로 두면 한 번 깐 기계가 그 판에 영영 묶인다 — 사람이 `Setup.exe` 를 누르기 전까지(PAISetup #18).
# ⚠ **`Setup.exe` 를 「푸는 자」로만 쓴다** — 그것은 짐을 `<판>\` 에 푼 뒤에 설치 화면을 띄우고 기다리지 않고 나간다(`Setup.c`
#   맨 끝 곁말). 설치를 맡기면 이 스크립트는 끝난 줄 알고 「완료」를 찍는다 — 거짓 초록이다. `-Unattended` 가 화면을 창 없이 바로
#   나가게 하고, 그 판으로 설치하는 것은 아래 원래 걸음이 든다.
# 못 물은 것을 최신으로 읽지 않는다 — 막힌 망에서는 조용히 지나가되 로그에는 적는다. 아무도 안 보는 자리라 여기 안 적으면
#   어디에도 안 남는다.
$updRepo = ''
if (Test-Path -LiteralPath $targetEnvProbe) {
  foreach ($ln in (Get-Content -LiteralPath $targetEnvProbe -Encoding UTF8 -ErrorAction SilentlyContinue)) {
    if ($ln -match '^\s*#update-repo\s*=\s*(\S+)') { $updRepo = $Matches[1]; break }
  }
}
$updLib = Join-Path $versionDirs[0].FullName 'update-check.ps1'
if ($updRepo -and (Test-Path -LiteralPath $updLib)) {
  $mine = $versionDirs[0].Name
  try { . $updLib } catch { }
  $found = $null
  try { $found = Find-NewerRelease -Repo $updRepo -Mine $mine } catch { }
  if (-not $found) {
    Log "설치본은 그대로 간다 ($mine) — 새 판이 없거나 못 물었다"
  } else {
    Log "새 판 $($found.Ver) 을 받는다 (지금 $mine · 릴리스 $($found.Rel))"
    $v = $null
    try { $v = Get-VerifiedSetup -Found $found } catch { }
    if (-not $v -or -not $v.Ok) {
      $why = '알 수 없다'
      if ($v) { $why = "$($v.Status) — $($v.Detail)" }
      Log "! 새 판을 안 깔았다: $why"
    } else {
      Log "지문이 맞다 ($($v.Have)) — 짐을 푼다"
      try {
        $pr = Start-Process -FilePath $v.Path -ArgumentList '-Unattended' -Wait -PassThru -ErrorAction Stop
        if ($pr.ExitCode -ne 0) { Log "! 푸는 자가 $($pr.ExitCode) 로 나갔다 — 옛 판으로 간다" }
      } catch { Log "! 푸는 자를 못 띄웠다: $($_.Exception.Message)" }
      Remove-Item -LiteralPath $v.Path, "$($v.Path).sha256" -Force -ErrorAction SilentlyContinue
      # 푼 판이 섰나는 **다시 세어** 안다 — 「띄웠다」와 「풀렸다」는 다른 명제다.
      $versionDirs = Find-Versions
      if (-not $versionDirs) { Log "! 설치본 폴더를 찾지 못했습니다"; exit 1 }
      if ($versionDirs[0].Name -eq $mine) { Log "! 새 판이 안 풀렸다 — $mine 으로 간다" }
      else { Log "새 판으로 간다: $($versionDirs[0].Name)" }
    }
  }
}

$targetEngine = Join-Path $versionDirs[0].FullName 'install.ps1'

# 설치에 넘기는 것은 밤 회차가 박은 자리뿐이다. 짐의 줄은 설치가 제 짐에서 읽고, 사람이 고른 것은 설치가 기록에서 읽는다(설치기의
#   「회차를 넘기는 기록의 자리」 · PAISetup #45) — 여기서 넘기면 넘긴 판의 사본이 다음 판에도 따라간다.
# 밤 회차가 잰 자리를 박는다 — `#site` 한 줄만 든 값 파일을 넘긴다. 설치는 그 줄과 제가 다시 잰 자리가 다르면 멈춘다. 못 박으면
#   자리를 바꿀 수 있으므로 건너뛴다.
$runArgs = @()
$pinned  = ''
if ($pinSite) {
  try {
    $pinned = Join-Path $setupRoot '.autorun-night.env'
    Set-Content -LiteralPath $pinned -Value @("#site = $pinSite") -Encoding UTF8 -ErrorAction Stop
    $runArgs = @('-EnvFile', $pinned)
    Log "자리를 $($siteWord[$pinSite])로 박고 잇습니다."
  } catch {
    Log "! 자리를 박은 값 파일을 못 만들었다 — 자리를 바꿀 수 있어 건너뜁니다 ($(($_.Exception.Message -split '\r?\n')[0]))"
    exit 0
  }
}

# `-NoUpgrade` 를 안 준다 — 올리는 것이 이 자동 실행이 사는 까닭이다.
# ⚠ **`*>>` 로 안 붙인다** — 그 리다이렉션은 UTF-16 으로 써서 UTF-8 인 `Log` 줄과 한 파일에 섞이고 설치 출력만 깨진다. 한 줄씩
#   받아 같은 자로 적는다.
# ⚠ **자식의 말을 받는 인코딩을 UTF-8 로 세운다**(`$OutputEncoding` · `[Console]::OutputEncoding`) — 파워셸은 자식이 보낸 바이트를
#   `[Console]::OutputEncoding`(한국어 윈도우에서 CP949)으로 풀어 문자열을 만드는데, 자식(`install.ps1`)은 UTF-8 로 말해 첫 바이트가
#   그 자리에서 `?` 로 바뀌고 되살릴 수 없다. 파일은 UTF-8 로 멀쩡히 저장돼 글자만 죽는다 — 창이 닫힌 뒤 남는 것은 이 로그뿐이다.
$OutputEncoding = [System.Text.Encoding]::UTF8
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

Log "install.ps1 실행: $($versionDirs[0].Name)  $($runArgs -join ' ')"
# 밤 회차라는 것은 이 프로세스의 환경변수로만 넘긴다 — 설치가 사람을 부르는 걸음(로그인 · 알림 창 · 「제공기능」)을 이 값으로 건너뛴다.
#   git · gh 도 묻지 않게 한다 — 자격 창(Git Credential Manager)이나 묻는 줄에서 사람 없이 멎지 않고 바로 지게 한다.
if ($Night) {
  $env:PAISETUP_AUTORUN_NIGHT = '1'
  $env:GIT_TERMINAL_PROMPT    = '0'
  $env:GCM_INTERACTIVE        = 'never'
  $env:GH_PROMPT_DISABLED     = '1'
}
# ⚠ **자식의 stderr 도 같은 줄로 받는다(`2>&1`)** — 잡히지 않은 예외로 죽은 설치는 그 글을 stderr 로만 내므로, 안 받으면 로그에
#   종료 코드만 남는다. 이 부름만 `Continue` 아래서 돈다 — 이 몸통의 `SilentlyContinue` 아래서는 `2>&1` 이 stderr 줄을 로그에도
#   창에도 안 남기고 버린다. 그 줄은 오류 레코드로 오지만 `Stop` 이 아니라 회차를 안 끊는다(설치기의 `2>&1` 금지는 `Stop` 아래 이야기다).
& {
  $ErrorActionPreference = 'Continue'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $targetEngine -Yes -NoLaunch @runArgs 2>&1
} | ForEach-Object {
    Write-Host $_
    Add-Content -LiteralPath $logFile -Value ([string]$_) -Encoding UTF8
  }
$rc = $LASTEXITCODE
if ($pinned) { Remove-Item -LiteralPath $pinned -Force -ErrorAction SilentlyContinue }
foreach ($ev in 'PAISETUP_AUTORUN_NIGHT', 'GIT_TERMINAL_PROMPT', 'GCM_INTERACTIVE', 'GH_PROMPT_DISABLED') {
  if ($Night) { Remove-Item "Env:$ev" -ErrorAction SilentlyContinue }
}
Log "=== PAISetup 자동 실행 완료 (코드 $rc) ==="
try { [IO.File]::WriteAllText($lastFile, ("{0} {1} 코드 {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm'), $runKind, $rc), [System.Text.Encoding]::UTF8) } catch { }

if ($rc -eq 0) {
  try { [IO.File]::WriteAllText($stampFile, (Get-Date -Format 'o'), [System.Text.Encoding]::UTF8) } catch { }
}

if ($viewer) {
  Log 'PAISetup 자동 동기화가 끝났습니다. 3초 후 창이 닫힙니다...'
  Start-Sleep -Seconds 3
  # 띄운 그 프로세스만 닫는다 — 같은 번호에 같은 시작 시각일 때만 끈다(번호를 남이 물려받았으면 안 끈다).
  try {
    $viewNow = Get-Process -Id $viewer.Id -ErrorAction Stop
    if ($viewNow.StartTime -eq $viewerStart) { $viewNow.Kill() }
  } catch { }
} elseif ([Environment]::UserInteractive) {
  Write-Host ''
  Write-Host '  PAISetup 자동 동기화가 완료되었습니다. 3초 후 창이 닫힙니다...' -ForegroundColor Green
  Start-Sleep -Seconds 3
}

# 옛 판 폴더를 거둔다 — 푸는 자는 새 폴더만 만들고 옛 것을 안 지워, 안 거두면 판마다 쌓인다.
# ⚠ **다 끝난 뒤에 지운다** — 앞에 두면 방금 부를 판을 지울 수 있다.
# 셋을 남긴다 — 새 판이 깨졌을 때 손으로 옛 판을 부를 자리다.
# ⚠ 방금 돈 판은 이름이 아니라 자리로 뺀다 — 새 판을 푼 뒤 다시 센 목록에서 그것이 첫째라고 믿지 않는다.
try {
  $keepVersions = 3
  $stale = Find-Versions | Select-Object -Skip $keepVersions |
           Where-Object { $_.FullName -ne $versionDirs[0].FullName }
  foreach ($d in $stale) {
    Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $d.FullName) { Log "! 옛 판을 못 지웠다 (쓰는 중일 수 있다): $($d.Name)" }
    else { Log "옛 판을 거뒀다: $($d.Name)" }
  }
} catch { }
'@
    [IO.File]::WriteAllText($autoScript, $autoScriptBody, [System.Text.Encoding]::UTF8)

    # 지난 설치의 자리 — 자리에 기대는 걸음을 다 지난 여기서 끝 값을 적는다(그 앞은 「자동 실행을 켜나」 칸이 `switching` 을
    #   적었다). 사람이 누른 설치도 여기를 지난다.
    try {
      Set-Content -LiteralPath $AutoRunSiteRecord -Value $site -Encoding UTF8 -ErrorAction Stop
    } catch {
      Remove-Item -LiteralPath $AutoRunSiteRecord -Force -ErrorAction SilentlyContinue
      Write-Host "  ! 이번 설치의 자리를 못 남겼다 — $(Say-Why $_) (밤 자동 실행은 다음 설치까지 건너뛴다)" -ForegroundColor Yellow
    }

    # 두 작업 다 사용자 권한 그대로 돈다(`Interactive` · 승격 없음) — 사람이 로그온해 있을 때만 서고, 잠긴 세션에서도 선다.
    # 한 작업이 아직 돌고 있으면 그 작업의 새 회차는 안 뜬다(`IgnoreNew`). 두 작업이 겹치면 몸통의 가드가 가른다.
    # `-Force` 로 통째로 덮으므로, 옛 판이 건 로그온 작업도 다음 설치(자동 실행 포함)에서 이 꼴로 갈린다.
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
                  -MultipleInstances IgnoreNew
    $psExe   = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $conhost = Join-Path $env:SystemRoot 'System32\conhost.exe'

    # 문지기 — 두 작업이 다 이것을 부른다. 로그온 회차는 몸통을 그대로 부르되 기록 창을 띄우라고 넘기고(`PAISETUP_AUTORUN_VIEWER`),
    #   밤 회차는 몸통이 밤 회차를 아는 판일 때만 `-Night` 로 부른다. 몸통이 없거나 표지가 없으면 밤 작업을 걷는다. 몸통을 못
    #   읽었으면(백신 · 백업의 잠금, 다시 쓰는 중) 걷지 않고 진 것으로 남기고 나간다 — 멀쩡한 PC 의 밤 작업이 저절로 사라지면 안 된다.
    # 알려진 한계 — 이 문지기 뒤에 옛 판 몸통(기록 창을 모른다)이 놓이면 로그온 회차는 머리 없는 콘솔에서 창 없이 돈다. 옛 판
    #   설치기는 로그온 작업을 제 꼴로 다시 걸므로 그 판을 다시 누른 PC 에서는 안 생긴다.
    $gateOk = $false
    try {
      $gateText = @'
# PAISetup 자동 실행의 문지기 — 작업 스케줄러의 로그온 · 밤 작업이 부르고, 설치기가 쓴다.
param([switch]$Night)
$ErrorActionPreference = 'SilentlyContinue'
$body  = Join-Path $PSScriptRoot 'autorun.ps1'
$psExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
if (-not $Night) {
  if (-not (Test-Path -LiteralPath $body)) { exit 0 }
  $env:PAISETUP_AUTORUN_VIEWER = '1'
  & $psExe -NoProfile -ExecutionPolicy Bypass -File $body
  exit $LASTEXITCODE
}
if (Test-Path -LiteralPath $body) {
  $text = $null
  try { $text = [IO.File]::ReadAllText($body) } catch {
    $why = (($_.Exception.Message -split "`r?`n")[0]) -replace '\s+', ' '
    try { [IO.File]::WriteAllText((Join-Path $PSScriptRoot '.autorun-last'), ((Get-Date -Format 'yyyy-MM-dd HH:mm') + " 밤 문지기 — 몸통을 못 읽어 건너뜀 ($why) 코드 unreadable"), [Text.Encoding]::UTF8) } catch { }
    exit 1
  }
  if ($text.Contains('@@MARKER@@')) {
    & $psExe -NoProfile -ExecutionPolicy Bypass -File $body -Night
    exit $LASTEXITCODE
  }
}
Unregister-ScheduledTask -TaskName '@@TASK@@' -Confirm:$false
exit 0
'@
      $autoGate = Join-Path $setupRoot $AutoRunGate
      [IO.File]::WriteAllText($autoGate, $gateText.Replace('@@MARKER@@', $AutoRunNightMarker).Replace('@@TASK@@', $AutoRunNightTaskName),
                              [System.Text.Encoding]::UTF8)
      $gateOk = $true
    } catch {
      Write-Host "  ! 자동 실행 문지기를 못 썼다 — $(Say-Why $_)" -ForegroundColor Yellow
    }

    # 창 없이 띄운다 — 머리 없는 콘솔(`conhost --headless`)은 창을 안 만든다. `powershell -WindowStyle Hidden` 은 기본 터미널이
    #   Windows Terminal 인 PC 에서 창을 잠깐 띄운 뒤 작업 표시줄에 남는다. 이 PC 의 conhost 가 그 깃발을 아는지는 이름이 아니라
    #   **돌려서** 본다 — 그 아래 자식이 파일을 쓰면 안다. 모르면 로그온 작업은 지금까지의 보이는 콘솔로, 밤 작업은
    #   `-WindowStyle Hidden` 으로 간다(창이 잠깐 보일 수 있다). 밤 회차는 시험을 안 돌린다 — 그 깃발을 모르는 conhost 는 시험
    #   중에 창을 띄울 수 있다. 지금 걸린 밤 작업의 꼴을 그대로 잇는다.
    $headless = $false
    $hf = Join-Path ([IO.Path]::GetTempPath()) "paisetup-headless-$PID.txt"
    $hc = Join-Path ([IO.Path]::GetTempPath()) "paisetup-headless-$PID.ps1"
    try {
      if ($NightRun) {
        $curNight = Get-ScheduledTask -TaskName $AutoRunNightTaskName -ErrorAction SilentlyContinue
        $headless = [bool]($curNight -and "$($curNight.Actions[0].Execute)" -like '*\conhost.exe')
      } elseif (Test-Path -LiteralPath $conhost) {
        # 자식이 제 콘솔 창이 없는지(`GetConsoleWindow()` 가 0) 적는다 — 「돌았다」만 보면 깃발을 버리고 보이는 콘솔로 돈 conhost 도
        #   지난다.
        Set-Content -LiteralPath $hc -Encoding UTF8 -Value @(
          'param([string]$Out)',
          'Add-Type -Namespace PAISetupHead -Name K -MemberDefinition ''[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern System.IntPtr GetConsoleWindow();''',
          'Set-Content -LiteralPath $Out -Value ([string]([PAISetupHead.K]::GetConsoleWindow() -eq [IntPtr]::Zero))')
        $hp = Start-Process -FilePath $conhost -WindowStyle Hidden -PassThru -ArgumentList @(
                '--headless', "`"$psExe`"", '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$hc`"", '-Out', "`"$hf`"")
        if (-not $hp.WaitForExit(20000)) { try { $hp.Kill() } catch { } }
        $headless = (Test-Path -LiteralPath $hf) -and ((Get-Content -LiteralPath $hf -Raw).Trim() -eq 'True')
      }
    } catch { $headless = $false } finally { Remove-Item -LiteralPath $hf, $hc -Force -ErrorAction SilentlyContinue }
    $headless = $headless -and $gateOk
    $gateArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$(Join-Path $setupRoot $AutoRunGate)`""

    try {
      $action = if ($headless) {
        New-ScheduledTaskAction -Execute $conhost -Argument "--headless `"$psExe`" $gateArgs"
      } else {
        New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$autoScript`""
      }
      $onLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
      $onLogon.Delay = "PT1M"
      Register-ScheduledTask -TaskName $AutoRunTaskName -Action $action -Trigger $onLogon `
                             -Principal $principal -Settings $settings `
                             -Description "PAISetup background auto-update & environment sync on logon" -Force | Out-Null
      Write-Host ("  부팅 시 자동 실행 — 걸었다 (작업 스케줄러 · $AutoRunTaskName · 로그온 1분 뒤 · " +
                  $(if ($headless) { '설치할 때만 기록 창' } else { '보이는 콘솔 창' }) + ')') -ForegroundColor Green
    } catch {
      Write-Host "  ! 자동 실행 스케줄러 등록 실패 — $(Say-Why $_)" -ForegroundColor Yellow
    }

    try {
      if (-not $gateOk) { throw '문지기가 없어 밤 작업을 안 건다' }
      $nightAction = if ($headless) {
        New-ScheduledTaskAction -Execute $conhost -Argument "--headless `"$psExe`" $gateArgs -Night"
      } else {
        New-ScheduledTaskAction -Execute $psExe -Argument "-WindowStyle Hidden $gateArgs -Night"
      }
      $onNight = New-ScheduledTaskTrigger -Daily -At $AutoRunNightAt -RandomDelay $AutoRunNightSpread
      Register-ScheduledTask -TaskName $AutoRunNightTaskName -Action $nightAction -Trigger $onNight `
                             -Principal $principal -Settings $settings `
                             -Description "PAISetup nightly auto-update & environment sync (never switches site)" -Force | Out-Null
      Write-Host ("  밤 자동 실행 — 걸었다 (작업 스케줄러 · $AutoRunNightTaskName · 매일 $($AutoRunNightAt.ToString('HH:mm')) 무렵 · 놓치면 켜진 뒤 · " +
                  $(if ($headless) { '창 없이' } else { '숨긴 창 — 잠깐 보일 수 있다' }) + ')') -ForegroundColor Green
    } catch {
      Write-Host "  ! 밤 자동 실행 스케줄러 등록 실패 — $(Say-Why $_)" -ForegroundColor Yellow
    }
  } else {
    # 작업마다 따로 걷는다 — 하나를 못 걷어도 다른 하나는 걷는다.
    $gone = @()
    foreach ($tn in @($AutoRunTaskName, $AutoRunNightTaskName)) {
      try {
        if (Test-AutoRunTask $tn) {
          Unregister-ScheduledTask -TaskName $tn -Confirm:$false -ErrorAction Stop
          $gone += $tn
        }
      } catch {
        Write-Host "  ! 자동 실행 스케줄러 등록 해제 실패 ($tn) — $(Say-Why $_)" -ForegroundColor Yellow
      }
    }
    if ($gone) {
      # 걷으면 저것이 쓰던 파일도 같이 걷는다 — 남겨 두면 다음에 켤 때 지난 회차의 표지(「오늘 끝났다」 · 지난 자리)를 물려받는다.
      #   사람이 고른 것의 기록(`$ChoiceRecord`)은 자동 실행의 것이 아니라 안 걷는다 — 다음 설치 창 · 콘솔이 그것을 읽는다(PAISetup #45).
      $setupRoot = Join-Path $env:LOCALAPPDATA 'Claude Code Setup'
      foreach ($f in @('autorun.ps1', '.autorun-stamp', '.autorun-night.env', '.autorun-last', $AutoRunGate, (Split-Path -Leaf $AutoRunSiteRecord))) {
        Remove-Item -LiteralPath (Join-Path $setupRoot $f) -Force -ErrorAction SilentlyContinue
      }
      Write-Host "  부팅 시 자동 실행 — 걷었다 (작업 스케줄러 · $($gone -join ' · '))" -ForegroundColor Green
    } elseif (-not (Test-AutoRunTask $AutoRunTaskName) -and -not (Test-AutoRunTask $AutoRunNightTaskName)) {
      Write-Host "  부팅 시 자동 실행 — 등록되어 있지 않다"
    }
    # 사람이 끈 판(`-NoAutoRun`)이면 끈 것을 적는다 — 작업을 못 걷었어도 적는다(끈 것은 사람의 뜻이다). 값 파일의 `no` 로 걷은 판은
    #   안 적는다 — 그것은 짐의 기본값이지 이 PC 에서 고른 것이 아니다. 위 걷기가 지우는 목록에 이 기록을 넣지 않는다.
    if ($NoAutoRun) {
      try {
        $offDir = Split-Path -Parent $AutoRunOffRecord
        if (-not (Test-Path -LiteralPath $offDir)) { New-Item -ItemType Directory -Path $offDir -Force | Out-Null }
        Set-Content -LiteralPath $AutoRunOffRecord -Encoding UTF8 -ErrorAction Stop `
          -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm') + ' 자동 실행을 껐다 — 설치 창에서 칸을 켜고 설치하면 이 파일을 지우고 다시 건다')
      } catch {
        Write-Host "  ! 끈 것을 못 적었다 — $(Say-Why $_) (다음 설치 창은 자동 실행 칸을 켜진 채로 띄울 수 있다)" -ForegroundColor Yellow
      }
    }
  }
} elseif ($autoKeptOff) {
  Write-Host ''
  Write-Host '  부팅 시 자동 실행 — 이 PC 에서 꺼 두었다 (설치 창에서 칸을 켜고 설치하면 다시 건다)'
}

} catch { Write-StepFault $_ '마무리' }

# ── 검증 — **재고 나서 말한다** ─────────────────────────────────────────────────
# 안 재고 「됐다」로 끝내면 안 선 기계도 성공으로 보고된다 — 부재가 통과로 읽히는 것을 막는 것이 이 스크립트의 규율이라,
#   마지막 칸이 그것을 든다.
# ⚠ **환경변수는 레지스트리에서 읽는다** — 이 창의 값은 방금 우리가 넣은 것이라 심겼는지를 못 잰다. 새 창이 볼 자리를 봐야
#   판정이 참이 된다.
Write-Host ''
Write-Host '=== 검증 ===' -ForegroundColor Cyan
try {  # 칸 경계 「검증」 — 아래 catch 까지가 재는 칸이다. 그 뒤의 셈 · 남은 것 줄 · 종료 코드는 진 판에도 돈다(`Write-StepFault`)
# ⚠ **이름을 `$Planted` 와 갈라 둔다** — 파워셸 변수는 대소문자를 안 가려, 여기서 `$planted` 를 쓰면 「우리가 심은 것」이 「사용자
#   환경 전부」로 갈리고, 그 뒤에 `$Planted` 를 읽는 줄이 들어오는 날 「우리가 심었나」가 「사용자 환경에 있나」로 조용히 바뀐다.
$userEnv = [Environment]::GetEnvironmentVariables('User')
# 한 번만 잰다 — 같은 물음을 두 번 물으면 두 답이 갈릴 자리가 나고, 아래 「연다」 칸도 이 값을 쓴다.
# 칸은 셋 가운데 하나다 — 섰다 · 졌다 · 못 쟀다(결정 0141). 섰다 · 졌다는 `@{ Name; Ok }` 로 들고, 못 잰 칸은
#   `State = 'unmeasured'` 와 넘긴 명령(`Probe`)을 든다. 그 넘김에 딸린 칸은 전제의 이름(`Premise`)도 들어 **한 전제의 결과**로
#   찍힌다 — `code --version` 하나를 못 쟀으면 VS Code 와 고른 확장이 다 그 하나에 걸린다.
$codeRuns = Measure-Runs 'code' '--version'
$hasCode = ($codeRuns -eq 'yes')
$extList = @()
# 깔린 확장 목록도 울타리 안에서 묻는다(`$ExtListCap`) — 못 읽었으면(넘김 · 0 아닌 값) 고른 확장 칸이 다 그 물음 하나에 걸린 「못 쟀다」다
#   (못 읽은 목록은 빈 목록이 아니다 — 결정 0145).
$extListRc = 0
if ($hasCode) {
  $el = [IO.Path]::GetTempFileName()
  try {
    $extListRc = Invoke-LoggedCapped 'code' @('--list-extensions') $el $ExtListCap
    if ($extListRc -eq -2) { Add-ProbeOverflow 'code --list-extensions' $ExtListCap }
    $extList = @(Get-Content -LiteralPath $el -Encoding UTF8 -ErrorAction SilentlyContinue | ForEach-Object { "$_".Trim() })
  } finally { Remove-Item -LiteralPath $el, "$el.err" -ErrorAction SilentlyContinue }
}
# 안 고른 것은 안 잰다 — 켜지도 않은 것을 [X] 로 찍으면 멀쩡한 설치가 빨갛게 끝난다. VS Code 도 고르는 것이라(사외 기본은
#   「끔」) 그 문(`-not $NoVsCode`) 아래에서 잰다.
# 확장과 CLI 는 깔 때 본 표 그대로 잰다 — 표에 한 줄을 더하면 검증도 따라온다. 칸 목록(`$checks`)은 파일 머리가 비워 둔다.
if (-not $NoVsCode) {
  if ($codeRuns -eq 'unmeasured') {
    $checks += @{ Name = 'VS Code'; State = 'unmeasured'; Probe = 'code --version' }
    foreach ($x in $ExtPicks) {
      $checks += @{ Name = $x.Label; State = 'unmeasured'; Probe = 'code --version'; Premise = 'VS Code' }
    }
  } else {
    $checks += @{ Name='VS Code'; Ok = $hasCode }
    foreach ($x in $ExtPicks) {
      if ($extListRc -ne 0) { $checks += @{ Name = $x.Label; State = 'unmeasured'; Probe = 'code --list-extensions'; Why = (Format-ProbeWhy $extListRc $ExtListCap) } }
      else                   { $checks += @{ Name = $x.Label; Ok = ($hasCode -and ($extList -contains $x.Id)) } }
    }
  }
}
# npm 으로 깐 CLI 는 「CLI」 걸음과 같은 자(npm 의 기록)로 잰다 — 띄우지 않고(PAISetup #30 ③) 기록은 한 번에 읽는다
#   (PAISetup #35 C). winget CLI 는 이름이 서나를 띄워 잰다.
$npmCheckPkgs = @($CliPicks | Where-Object { $_.Via -ne 'winget' } | ForEach-Object { $_.Pkg })
$npmCheckRecs = if ($npmCheckPkgs.Count) { Measure-NpmGlobal $npmCheckPkgs } else { @{} }
foreach ($c in $CliPicks) {
  if ($c.Via -ne 'winget') {
    $rec = $npmCheckRecs[$c.Pkg]
    if ($rec.State -eq 'unmeasured') { $checks += @{ Name = $c.Label; State = 'unmeasured'; Probe = $rec.Probe; Why = $rec.Why } }
    else                             { $checks += @{ Name = $c.Label; Ok = ($rec.State -eq 'yes') } }
    continue
  }
  $cliArg = if ($c.Arg) { $c.Arg } else { '--version' }
  $cliRuns = Measure-Runs $c.Cmd $cliArg
  if ($cliRuns -eq 'unmeasured') { $checks += @{ Name = $c.Label; State = 'unmeasured'; Probe = "$($c.Cmd) $cliArg" } }
  else                           { $checks += @{ Name = $c.Label; Ok = ($cliRuns -eq 'yes') } }
}
# 나르는 자리 — 「공용 자산」 걸음의 자산. 재는 자는 위 `New-CountCheck` 하나다. 규범 · 룰 · 에이전트 · 스킬은 손의 `check` 가, 칸 없이
#   까는 스킬은 아래에서 이름마다 잰다.
foreach ($a in $envAssets) {
  if (-not (Test-Path -LiteralPath $a.From)) { continue }
  # 비켜선 자리는 동봉본이 아니라 임자의 그 폴더와 견준다 — 거기 든 것은 설정 저장소의 최신판이라, 동봉본과 견주면 저쪽이 부품을
  #   걷은 날 멀쩡한 자리가 [X] 로 선다. 여분은 판정에 안 든다 — 저쪽 배포는 원본 이력이 걷은 파일만 걷고, 프록시 기록 같은 남의
  #   파일은 둔다(`deploy.ps1` 씨앗 칸).
  # ⚠ **원본은 그 저장소가 추적하는 파일이다** — 저장소의 그 폴더에도 git 이 무시하는 런타임 기록(`posco/pgpt-proxy/proxy.log`)이 살고, 홈의
  #   같은 이름 파일은 도는 프록시가 따로 덧쓴다. 작업 나무 전부와 견주면 그 한 파일로 판마다 [X] 다. git 이 답을 못 내면 못 잰 것이다.
  if ($a.Owner) {
    $ownDir = Join-Path $a.Owner $a.Rel
    $tracked = $null
    $saveOut = [Console]::OutputEncoding
    try {
      [Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
      $tracked = @(& git -C $ownDir -c core.quotepath=false ls-files 2>$null)
      if ($LASTEXITCODE -ne 0) { $tracked = $null }
    } catch { $tracked = $null } finally { [Console]::OutputEncoding = $saveOut }
    if ($null -eq $tracked) {
      $checks += @{ Name = "$($a.Name) (설정 저장소가 든다 · $($a.Owner))"; State = 'unmeasured'; Probe = "git -C `"$ownDir`" ls-files"
                    Why = '그 저장소가 추적하는 파일을 git 이 못 댔다' }
      continue
    }
    $cmp = Compare-AssetTree $ownDir $a.To -ExtraOk -Only @($tracked | Where-Object { $_ } | ForEach-Object { $_.Replace('/', '\') })
    $checks += @{ Name = "$($a.Name) (설정 저장소가 든다 · 원본 $($cmp.N) 파일$(if ($cmp.Say) { ' · ' + $cmp.Say }) · $($a.Owner))"; Ok = $cmp.Ok }
    continue
  }
  # 장부로 맞추는 자리 — 원본의 파일이 바이트까지 섰나와, 장부에 든 우리 파일 가운데 원본에서 빠졌는데 놓은 그대로 남은 것이 없나를
  #   잰다. 여분(남의 파일)은 판정에 안 든다.
  if ($a.Ledger) {
    $cmp = Compare-AssetTree $a.From $a.To -ExtraOk
    $srcNames = Get-AssetFiles $a.From
    $lgr = Read-PlantLedger $ClaudePlantLedger
    $left = @(Find-LedgerRows $lgr 'file' (ConvertTo-LedgerAt $a.To) 'assets' | Where-Object { -not $srcNames.ContainsKey($_.Name) } | Where-Object {
      $p = Join-Path $a.To $_.Name
      (Test-Path -LiteralPath $p -PathType Leaf) -and ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ceq $_.Value) } | ForEach-Object { $_.Name })
    $say = @(@($cmp.Say) + @($(if ($left.Count) { "원본에서 빠진 우리 파일 $($left.Count): $((@($left | Select-Object -First 3)) -join ', ')" })) +
             @($(if ($lgr.Why) { "장부를 못 읽었다 — $($lgr.Why)" })) | Where-Object { $_ })
    $checks += @{ Name = "$($a.Name) (원본 $($cmp.N) 파일$(if ($say.Count) { ' · ' + ($say -join ' · ') }))"; Ok = ($cmp.Ok -and -not $left.Count -and -not $lgr.Why) }
    continue
  }
  $checks += New-CountCheck $a.Name $a.From $a.To
}
# ── Claude 훅 — **놓았다는 초록과 섰다는 것은 다른 명제다** ──────────────────────────
# 되읽어서 잰다 — 등록은 손이 놓고 「도구별 홈」 걸음이 그 줄을 찍었지만, 파일에 실제로 그 항목이 서 있나는 다른 물음이다.
#   설정 저장소의 훅(「설정 저장소」 걸음)이 개인 층에서 등록을 다시 놓았으면 그것까지 여기서 본다.
# ⚠ **놓는 조건 그대로 잰다** — Claude 를 골랐을 때만(결정 0102). 한쪽만 조건을 타면 안 고른 사람 자리에서 놓였는데 안 재지거나
#   그 반대가 된다.
# ⚠ **배선은 등록이 가리키는 폴더로 잰다** — 껍데기 머리말의 이벤트마다 우리 훅이 있고 그 훅이 가리키는 폴더에 그 껍데기가
#   있어야 선 것이다. 한 이벤트만 빠져도 그 갈래(오류로 끝난 꼴 · 첨부 쪽 따위)를 조용히 놓친다(`Get-ClaudeHookWiring`).
# 씨앗의 몸통 · 껍데기 줄은 씨앗을 잰다 — Claude 등록이 부르는 사본은 배선 줄이 재고, 이 줄들은 설정 저장소 씨앗이 그 부품을
#   실었나를 잰다(씨앗으로 만든 저장소는 제 훅 폴더로 개인 층을 채워 통째로 이기므로, 씨앗에 빠진 껍데기는 그 PC 에서 안 심긴다).
#   고칠 자리가 다르다(뽑기 선언 · 손).
# ⚠ **잴 껍데기 목록은 짐의 훅 폴더에서 짓는다 — 손으로 적지 않는다.** 등록 머리말(`events`)을 든 껍데기마다 한 벌이고, 씨앗 줄은 그
#   껍데기와 그것이 제 변수로 부르는 곁 파일(주석 밖 `"$<변수>/<이름>"`)이다 — 손(`tool-homes.py`)이 등록을 짓고 층에 싣는 것과 같은
#   자다(꼴은 표 `tool-homes.conf` 의 hook 꼴). 적어 둔 목록은 원본에 훅이 는 날 안 따라와, 심긴 훅이 끝 검증에 없다(PAISetup #47 ②).
#   껍데기를 하나도 못 찾으면 그것이 [X] 다 — 빈 목록을 초록으로 지나가지 않는다.
if ($hostClaude) {
  $gc = $null; $gcWhy = ''
  try { $gc = Get-Content -LiteralPath $homeCfg -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $gcWhy = '홈 설정을 못 읽었다' }
  $seedHooks = $ConfigSeedHooks
  $kitHooks = Join-Path $Kit 'hooks'
  $hookShells = @(Get-ChildItem -LiteralPath $kitHooks -Filter '*.sh' -File -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
      $hh = Get-HookHead $_.FullName
      if ($hh -and $hh.ContainsKey('events')) { @{ Shell = $_.Name; Path = $_.FullName; Var = $hh['var'] } } })
  if (-not $hookShells.Count) { $checks += @{ Name = "Claude 훅 목록 (짐의 훅 폴더에 등록 머리말을 든 껍데기가 없다 — $kitHooks)"; Ok = $false } }
  foreach ($w in $hookShells) {
    $label = "Claude 훅 $($w.Shell)"
    $seedFiles = @($w.Shell)
    if ($w.Var) {
      $reach = '"\$' + [regex]::Escape($w.Var) + '/([^"/]+)"'
      $shLines = @()
      try { $shLines = [IO.File]::ReadAllLines($w.Path) } catch { }
      foreach ($ln in $shLines) {
        if ($ln.TrimStart().StartsWith('#')) { continue }
        foreach ($rm in [regex]::Matches($ln, $reach)) { if ($seedFiles -notcontains $rm.Groups[1].Value) { $seedFiles += $rm.Groups[1].Value } }
      }
    }
    foreach ($f in $seedFiles) {
      $kind = if ($f -ceq $w.Shell) { '껍데기' } else { '곁 파일' }
      $checks += @{ Name = "$label $kind (씨앗의 $f)"; Ok = (Test-Path -LiteralPath (Join-Path $seedHooks $f)) }
    }
    $wr = Get-ClaudeHookWiring $gc $w.Shell $w.Path
    $wrWhy = if ($gcWhy) { $gcWhy } else { $wr.Why }
    if ($wrWhy) {
      $checks += @{ Name = "$label 배선 (홈 settings.json — $wrWhy)"; Ok = $false }
    } else {
      $miss = if ($wr.Missing.Count) { " — 빠진 이벤트 $($wr.Missing -join ' · ')" } else { '' }
      $checks += @{ Name = "$label 배선 (홈 settings.json 의 $($wr.Events -join ' · ')$miss)"; Ok = ($wr.Missing.Count -eq 0) }
    }
    $bad = @($wr.BadMatcher) + @($(if ($wrWhy) { $wrWhy }))
    $checks += @{ Name = ("$label matcher (이벤트마다 진본과 같다" + $(if ($bad.Count) { ' — ' + ($bad -join ' · ') } else { '' }) + ')')
                  Ok = ($bad.Count -eq 0) }
  }
}
# 워드의 PDF 변환 안내 — 「키와 값」 걸음이 읽은 판 목록 그대로 되읽는다. 워드가 없으면 줄이 없다.
$wordCheck = Get-WordPdfQuietCheck $WordVersions
if ($wordCheck) { $checks += $wordCheck }
# WebFetch 검증 건너뛰기 — 사내에서만 잰다. 위 심는 칸의 「켰다」는 메모리의 객체를 고쳤다는 말이라 되읽는다.
if ($inside) {
  $skipSet = $false
  try { $skipSet = ((Get-Content -LiteralPath $homeCfg -Raw -Encoding UTF8 | ConvertFrom-Json).skipWebFetchPreflight -eq $true) } catch { }
  $checks += @{ Name = 'WebFetch 검증 건너뛰기 (홈 settings.json 의 skipWebFetchPreflight · 사내)'; Ok = $skipSet }
}
# 기본 권한 모드 · 허용 규칙 — 「Claude 홈 설정」의 표(`$ClaudeHomePlants`)에서 이번에 심을 것을 되읽는다. 기본 권한 모드는 키가 서 있으면
#   [O] 다 — 사람이 정한 값은 그 사람의 기본값이라 안 덮고, 줄에 그 값을 적는다.
$planCfg = $null
try { $planCfg = Get-Content -LiteralPath $homeCfg -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
$planPerm = $null
if ($planCfg -and $planCfg.PSObject.Properties['permissions']) { $planPerm = $planCfg.permissions }
foreach ($p in @($ClaudeHomePlants | Where-Object { $_.Want })) {
  $pv = $null
  if ($planPerm -and $planPerm.PSObject.Properties[$p.Key]) { $pv = $planPerm.($p.Key) }
  if ($p.Key -ceq 'allow') {
    $checks += @{ Name = "$($p.Label) (홈 settings.json 의 permissions.allow 에 $($p.Value))"; Ok = (@($pv) -ccontains $p.Value) }
  } else {
    $pvShow = if ($null -eq $pv) { '없다' } elseif ($pv -ceq $p.Value) { $pv } else { "$pv · 사람이 정한 값이라 안 덮었다" }
    $checks += @{ Name = "$($p.Label) (홈 settings.json 의 permissions.$($p.Key) = $pvShow)"; Ok = ($null -ne $pv) }
  }
}
# 묻지 않고 돌기 — 「도구별 홈」의 표(`$ToolAutoRun`)에서 이번에 심을 것을 파일에서 되읽는다.
foreach ($r in @($ToolAutoRun | Where-Object { $_.Want })) { $checks += Get-ToolAutoRunCheck $r }
# 장부와 실물 — 장부에 든 우리 값이 자리마다 그대로 섰나를 디스크에서 다시 읽어 잰다(PAISetup #44 가-1 · `Get-PlantLedgerChecks`). 어긋나면
#   쓰기가 안 닿았거나 다른 손이 고친 것이다 — 그 칸은 자리와 이름만 대고 값(비밀일 수 있다)은 안 찍는다.
$checks += @(Get-PlantLedgerChecks (Read-PlantLedger $ClaudePlantLedger) $userEnv $homeCfg)
# agy 묶음 — 맡기기(모델 값). 심는 조건 그대로 잰다(위 `$wantAgyDelegate` 곁말). agy 설정 둘은 손의 `check` 가 잰다.
# ⚠ 맡기기 모델 표를 못 읽은 판은 [X] 다 — 견줄 값이 비어 그대로 재면 빈 목록이 [O] 로 찍힌다.
if ($wantAgyDelegate) {
  $checks += @{ Name = $(if ($ModelTable.Why) { 'agy 모델 (맡기기 모델 표를 못 읽었다)' } else { "agy 모델 ($($AgyModelVars.Keys -join ' · '))" })
                Ok = ((-not $ModelTable.Why) -and
                      @($AgyModelVars.Keys | Where-Object { $userEnv[$_] -ne $AgyModelVars[$_] }).Count -eq 0) }
}
# Codex · Copilot 맡기기의 자리 값 — 이 자리 값과 글자까지 같은가(`$CcBgVars` — 맡기기 모델 표가 Codex 모델을 주면 그것도).
if ($wantCcBg) {
  $checks += @{ Name = "Codex · Copilot 맡기기 값 ($($CcBgVars.Keys -join ' · '))"
                Ok = (@($CcBgVars.Keys | Where-Object { $userEnv[$_] -ne $CcBgVars[$_] }).Count -eq 0) }
}
# Codex 훅 — 부품(설정 저장소 씨앗) · config.toml 배선 · Codex 가 읽은 신뢰. Codex 를 골랐을 때만 잰다.
if ($PickKeys -contains 'codex') {
  $codexHookText = ''
  if (Test-Path -LiteralPath $CodexCfg) {
    try { $codexHookText = Get-Content -LiteralPath $CodexCfg -Raw -Encoding UTF8 } catch { $codexHookText = '' }
  }
  # 무엇을 거나는 씨앗의 예시(`codex-hooks.example.toml`)가 든다 — 여기 이름을 적지 않고 예시의 명령(`command = "… hooks/<파일> [<판>]"`)에서
  #   짓는다. 부품은 그 명령이 부르는 파일과 병합기 · 신뢰 도우미 · 예시 자신이고, 배선은 그 명령 글이 config.toml 에 다 섰나다. 예시를
  #   못 읽거나 명령이 하나도 안 잡히면 두 줄 다 [X] 다.
  $codexEx = Join-Path $ConfigSeedHome 'codex-hooks.example.toml'
  $codexExText = ''
  try { $codexExText = [IO.File]::ReadAllText($codexEx) } catch { $codexExText = '' }
  $codexExCmds = @([regex]::Matches($codexExText, '(?m)^\s*\{[^\r\n]*?\bcommand\s*=\s*"[^"\r\n]*?/\.claude/hooks/([^"\s/]+)((?: [^"\s]+)*)"') |
                   ForEach-Object { @{ File = $_.Groups[1].Value; Said = ($_.Groups[1].Value + $_.Groups[2].Value) } })
  $codexHookParts = @(@($codexExCmds | ForEach-Object { $_.File } | Select-Object -Unique) + @('codex-hook-install.py', 'codex-hook-trust.py') |
                      ForEach-Object { Join-Path $ConfigSeedHooks $_ }) + @($codexEx)
  $codexPartsGone = @($codexHookParts | Where-Object { -not (Test-Path -LiteralPath $_) } | ForEach-Object { Split-Path $_ -Leaf })
  $checks += @{ Name = ("Codex 훅 부품 (예시가 부르는 $(@($codexExCmds | ForEach-Object { $_.File } | Select-Object -Unique).Count) 개 · 병합기 · 신뢰 도우미 · 예시" +
                       $(if ($codexPartsGone.Count) { ' — 없는 것 ' + ($codexPartsGone -join ' · ') } else { '' }) + ')')
                Ok = ($codexExCmds.Count -gt 0 -and $codexPartsGone.Count -eq 0) }
  $codexUnwired = @($codexExCmds | Where-Object { -not $codexHookText.Contains($_.Said) } | ForEach-Object { $_.Said })
  $checks += @{ Name = ("Codex 훅 배선 (예시의 명령 $($codexExCmds.Count) 개가 config.toml 에" + $(if ($codexUnwired.Count) { ' — 빠진 것 ' + ($codexUnwired -join ' · ') } else { '' }) + ')')
                Ok = ($codexExCmds.Count -gt 0 -and $codexUnwired.Count -eq 0) }
  # 신뢰 — 설정의 글자가 아니라 **Codex 가 읽은 상태**를 잰다(claude-config 결정 0106). 배선이 다 서도 신뢰가 없으면
  #   `codex exec` 가 그 훅을 말없이 건너뛴다 — 글자만 보면 그 판이 [O] 로 지나간다. 분모는 예시가 싣는 우리 훅 수다.
  # ⚠ **못 잰 것은 [?] 가 아니라 [X] 다** — Codex 에 못 물었으면 훅이 도는지 모른다. 그 줄이 까닭과 손으로 신뢰하는 길을 댄다.
  # 사람이 끈 우리 훅은 그 사람의 뜻이라 모자람으로 안 센다 — 줄에 따로 적는다.
  $codexTrustPlant = Join-Path $ConfigSeedHooks 'codex-hook-trust.py'
  $codexTrustExample = $codexEx
  if ((Test-Path -LiteralPath $codexTrustPlant) -and (Test-Path -LiteralPath $codexTrustExample)) {
    $ctLog = [IO.Path]::GetTempFileName()
    try {
      $ctRc = Invoke-Logged 'python' @('-X', 'utf8', $codexTrustPlant, 'status', '--example', $codexTrustExample) $ctLog
      $ctOut = @(Get-Content -LiteralPath $ctLog -Encoding UTF8 -ErrorAction SilentlyContinue |
                 ForEach-Object { "$_".Trim() } | Where-Object { $_ })
    } finally { Remove-Item -LiteralPath $ctLog -ErrorAction SilentlyContinue }
    $ctVal = @{}
    foreach ($ln in $ctOut) { if ($ln -match '^(EXPECTED|WIRED|TRUSTED|NONE_LISTED|UNMEASURED|ERROR)=(.*)$') { $ctVal[$Matches[1]] = $Matches[2] } }
    $ctOff = @($ctOut | Where-Object { $_ -like 'HOOK=*' -and $_ -like '*|disabled' }).Count
    if ($ctRc -ne 0 -or -not $ctVal.ContainsKey('EXPECTED') -or -not $ctVal.ContainsKey('TRUSTED')) {
      $ctWhy = if ($ctVal['UNMEASURED']) { $ctVal['UNMEASURED'] } elseif ($ctVal['ERROR']) { $ctVal['ERROR'] } else { "종료 $ctRc" }
      $checks += @{ Name = "Codex 훅 신뢰 (못 잼 — $ctWhy · Codex 를 열어 새 훅을 한 번 신뢰한다)"; Ok = $false }
    } else {
      $ctExp = [int]$ctVal['EXPECTED']; $ctWired = [int]$ctVal['WIRED']; $ctTrusted = [int]$ctVal['TRUSTED']
      $ctNote = @()
      if ($ctOff) { $ctNote += "사람이 끈 것 $ctOff" }
      if ($ctVal['NONE_LISTED']) { $ctNote += "Codex 가 안 싣는다: $($ctVal['NONE_LISTED'])" }
      $checks += @{ Name = "Codex 훅 신뢰 (Codex 가 읽은 것 — 배선 $ctWired/$ctExp · 신뢰 $ctTrusted/$ctExp$(if ($ctNote.Count) { ' · ' + ($ctNote -join ' · ') }))"
                    Ok = ($ctExp -gt 0 -and $ctWired -eq $ctExp -and ($ctTrusted + $ctOff) -eq $ctExp) }
    }
  }
}
# 칸 없이 까는 스킬 — 제작자 칸에 안 든 도구의 홈만 잰다(칸에 든 홈은 손의 `check` 가 잰다). 까는 칸과 같은 목록
#   (`Get-FreeSkillNames`)으로 잰다 — 따로 지으면 까는 것과 재는 것이 갈린다. 스킬마다 짐의 그 스킬과 파일 묶음 · 바이트가 같은가를
#   잰다(거울 — `Compare-AssetTree`) — SKILL.md 가 있나만 보면 짐에서 빠진 파일이 남은 판이 초록이다.
foreach ($t in $FreeSkillHomes.Keys) {
  $fh = $FreeSkillHomes[$t]
  $freeWant = @(Get-FreeSkillNames $t)
  if ($fh.Box -or -not $freeWant.Count) { continue }
  if (-not $fh.Place) { $checks += @{ Name = "칸 없이 까는 스킬 — $($fh.Label) (갈 곳 표에 자리가 없다)"; Ok = $false }; continue }
  $freeBad = @(foreach ($n in $freeWant) {
    $cmp = Compare-AssetTree (Join-Path $KitSkills $n) (Join-Path $fh.Place.Skills $n)
    if (-not $cmp.Ok) { "$n($($cmp.Say))" }
  })
  $checks += @{ Name = "칸 없이 까는 스킬 — $($fh.Label) ($($freeWant -join ' · ')$(if ($freeBad.Count) { ' · 어긋남: ' + ($freeBad -join ' · ') }))"; Ok = ($freeBad.Count -eq 0) }
}
# agy — 훅 셋이 우리 어댑터로 걸렸나 (결정 0099 · 컨텍스트 알림은 claude-config #173)
if ($hostAgy) {
  $agyHooksNow = $null
  try { $agyHooksNow = Get-Content -LiteralPath (Join-Path $env:USERPROFILE '.gemini\config\hooks.json') -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
  $agyWired = @('paisetup-drm-guide', 'paisetup-utf8-bom', 'paisetup-context-alert' | Where-Object {
    $agyHooksNow -and $agyHooksNow.$_ -and (($agyHooksNow.$_ | ConvertTo-Json -Depth 8 -Compress) -match 'agy-hooks\.py')
  })
  # ⚠ **이름이 있다고 선 것이 아니다** — 명령의 따옴표 하나로 훅이 다 지는데 이름은 그대로 있다(claude-config #126). 그래서
  #   agy 가 돌리는 꼴 그대로 한 번씩 돌린다: cmd.exe 에 Go 식 인자(명령을 큰따옴표로 싸고 안의 큰따옴표는 `\"`)로 넘기고,
  #   일하는 자리는 hooks.json 의 폴더다. 아무 일 없는 입력(없는 파일)을 줘 0 으로 끝나나만 본다.
  $agyRan = @()
  if ($agyWired.Count -eq 3) {
    foreach ($probe in @(
        @{ Name = 'paisetup-drm-guide'; Ev = 'PreToolUse'
           In = '{"toolCall":{"name":"view_file","args":{"AbsolutePath":"C:/paisetup-probe/none.txt"}}}' }
        @{ Name = 'paisetup-utf8-bom'; Ev = 'PostToolUse'
           In = '{"toolCall":{"name":"write_to_file","args":{"TargetFile":"C:/paisetup-probe/none.txt"}}}' }
        # PreInvocation 은 matcher 없는 납작한 꼴이다(항목 바로 아래 명령) — agy 문서 · claude-config #173
        @{ Name = 'paisetup-context-alert'; Ev = 'PreInvocation'; Flat = $true
           In = '{"invocationNum":1,"conversationId":"paisetup-probe","transcriptPath":"C:/paisetup-probe/none.jsonl"}' })) {
      try {
        $psi = New-Object Diagnostics.ProcessStartInfo
        $psi.FileName = 'cmd.exe'
        $entry = @($agyHooksNow.($probe.Name).($probe.Ev))[0]
        $cmd = if ($probe.Flat) { [string]$entry.command } else { [string]$entry.hooks[0].command }
        $psi.Arguments = '/c "' + ($cmd -replace '"', '\"') + '"'
        $psi.WorkingDirectory = Join-Path $env:USERPROFILE '.gemini\config'
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
        $pr = [Diagnostics.Process]::Start($psi)
        $pr.StandardInput.Write($probe.In); $pr.StandardInput.Close()
        $null = $pr.StandardOutput.ReadToEnd(); $null = $pr.StandardError.ReadToEnd()
        if ($pr.WaitForExit(20000) -and $pr.ExitCode -eq 0) { $agyRan += $probe.Name }
      } catch { }
    }
  }
  $checks += @{ Name = 'agy 훅 배선 (~/.gemini/config/hooks.json 의 PreToolUse · PostToolUse · PreInvocation · agy 가 돌리는 꼴로 돌려 본다)'
                Ok = ($agyWired.Count -eq 3 -and $agyRan.Count -eq 3) }
}
# 고른 도구 값 · 고른 제품 값 — 손 · 설정 저장소의 배포 · 세션 훅이 읽는다(결정 0102 · 0107 · 0112)
$checks += @{ Name = "제작자 세트 도구 값 (PAISETUP_PERSONAL = $PersonalValue)"
              Ok = ([Environment]::GetEnvironmentVariable('PAISETUP_PERSONAL', 'User') -eq $PersonalValue) }
$checks += @{ Name = "고른 제품 값 (PAISETUP_PICK = $PickValue)"
              Ok = ([Environment]::GetEnvironmentVariable('PAISETUP_PICK', 'User') -eq $PickValue) }
# 자리 값 — 맡기는 세션이 맡기기 모델 표의 자리 줄을 고른다(결정 0123)
$checks += @{ Name = "자리 값 (PAISETUP_SITE = $ModelSite)"
              Ok = ([Environment]::GetEnvironmentVariable('PAISETUP_SITE', 'User') -eq $ModelSite) }
# 규범 · 룰 · 에이전트 · 스킬 — 손의 `check` 한 번(claude-config 결정 0112). 「설정 저장소」 걸음의 배포가 개인 층을 채웠으면 그 층의
#   손이 잰다. 부르는 조건은 「도구별 홈」의 부름과 같다(`$toolHomesOn`).
if ($toolHomesOn) { $checks += Get-ToolHomesCheck $toolHomesHand }
# 브라우저 MCP — 어댑터의 `check` 한 번(claude-config 결정 0149). 고른 도구가 셋 가운데 없으면 칸을 안 세운다 —
#   안 쓰기로 한 것을 [X] 로 찍지 않는다. python 이 안 서면 「도구별 홈」이 이미 빨강으로 셌고, 못 쟀으면 [?] 다. 개발 도구를 꺼
#   브라우저를 안 받아 안 단 판(`$browserMcpSkipped`)도 칸을 안 세운다 — 안 깔기로 한 것이다.
if ($browserMcpOn.Count -and $browserMcpPython -eq 'yes' -and -not $browserMcpSkipped) {
  $checks += Get-BrowserMcpCheck $browserMcpPlant $browserMcpOn $browserMcpOff
} elseif ($browserMcpOn.Count -and $browserMcpPython -eq 'unmeasured') {
  $checks += @{ Name = '브라우저 MCP'; State = 'unmeasured'; Probe = 'python --version' }
}
# 게이트웨이 값은 쓰기로 한 자리에서만 「있나」를 잰다 — 안 쓰기로 한 것을 [X] 로 찍으면 멀쩡한 사외 PC 가 매번 빨갛게
#   보고되고, 빨강이 흔해지면 진짜 빨강이 안 보인다.
# ⚠ **키는 `#config-repo` 가 있어도 여기서 잰다** — 심는 자가 이 파일 하나라 재는 자도 하나다. 저쪽에 맡기면 저장소에 설치
#   몸통이 없을 때 키가 안 심긴 채 초록으로 끝난다.
if ($useGateway) {
  foreach ($v in $Vars) {
    if (-not $v.Gateway) { continue }
    $checks += @{ Name = $v.Name; Ok = [bool]$userEnv[$v.Name] }
  }
  foreach ($k in $KeyAliases) {
    if (-not $wantNeed[$k.Need]) { continue }
    $checks += @{ Name = $k.Name; Ok = [bool]$userEnv[$k.Name] }
  }
  if ($wantCodex) {
    # 틀의 자리가 서 있나 — 「Codex · 안티그래비티 설정」 칸의 병합기(`$CodexCfgMerge`)를 판정만 하는 꼴로 부른다. 병합기가 졌거나 python 이 없는 것은 [X] 다 —
    #   `python --version` 을 못 잰 것(넘김 · 못 띄움 · 이름은 서는데 0 아닌 끝)만 [?] 다(결정 0141 · 0151).
    $cmWhy = '파일이 없다'
    $cmOk = $false
    $cmPython = if ((Test-Path -LiteralPath $CodexCfg) -and (Test-Path -LiteralPath $CodexCfgMerge)) { Measure-Runs 'python' '--version' } else { '' }
    if (-not (Test-Path -LiteralPath $CodexCfg)) {
      # 위 「파일이 없다」 그대로
    } elseif ($cmPython -ne 'yes') {
      $cmWhy = '못 잼 — 틀 병합기나 python 이 안 선다'
    } else {
      $cmLog = [IO.Path]::GetTempFileName()
      $cmRc = Invoke-Logged 'python' @('-X', 'utf8', $CodexCfgMerge, '--config', $CodexCfg, '--template', (Join-Path $Here $codexTpl), '--check') $cmLog
      $cmOut = @(Get-Content -LiteralPath $cmLog -Encoding UTF8 -ErrorAction SilentlyContinue |
                 ForEach-Object { "$_".Trim() } | Where-Object { $_ })
      Remove-Item -LiteralPath $cmLog -ErrorAction SilentlyContinue
      $cmOk = ($cmRc -eq 0 -and $cmOut -contains 'CHANGED=0')
      $cmWhy = if ($cmOk) { '틀의 자리가 다 틀의 값이다' }
               elseif ($cmRc -eq 0) { '틀과 다른 자리 — ' + (@($cmOut | Where-Object { $_ -like 'SET=*' } | ForEach-Object { $_.Substring('SET='.Length) }) -join ' · ') }
               else { '못 잼 — ' + (@($cmOut | Where-Object { $_ -like 'ERROR=*' }) + @("종료 $cmRc") | Select-Object -First 1) }
    }
    if ($cmPython -eq 'unmeasured') { $checks += @{ Name = 'Codex config.toml'; State = 'unmeasured'; Probe = 'python --version' } }
    else                            { $checks += @{ Name = "Codex config.toml ($cmWhy)"; Ok = $cmOk } }
  }
  if ($wantAgy)    { $checks += @{ Name = '안티그래비티 settings.json'; Ok = (Test-Path -LiteralPath $AgyCfg) } }
  # ⚠ **프록시는 「떠 있나」와 「문을 여나」를 따로 잰다** — 떠 있는 것만 보면 보정이 안 도는 판이 초록이 된다. 문은 assistant 로
  #   끝나는 본문을 프록시 너머로 보내 200 이 오는가로 잰다 — 이 게이트웨이가 Opus 5 에서 그 본문을 400 으로 거절하는 것이 프록시가
  #   있는 까닭이라(결정 0041), 짧은 답이 오나가 아니라 그 400 이 사라졌나를 묻는다. 모델 이름은 그 결함의 이름이다.
  if ($wantProxy -and $proxyHealthUrl) {
    $h = Get-ProxyHealth $proxyHealthUrl
    $checks += @{ Name = '로컬 프록시 (/health)'; Ok = [bool]$h }
    $door = 0
    if ($h -and $userEnv['ANTHROPIC_AUTH_TOKEN']) {
      $door = Test-PrefillDoor $userEnv['ANTHROPIC_BASE_URL'] $userEnv['ANTHROPIC_AUTH_TOKEN'] 'claude-opus-5'
    }
    $checks += @{ Name = "Opus 5 문 — prefill 본문이 프록시 너머로 200 (받은 것: $door$(if ($door -ge 500) { " — 상류가 끊었다 · prefill 이 아니다" }))"; Ok = ($door -eq 200) }

    # ⚠ **프록시 프로세스는 하나여야 하고 껍데기가 아니어야 한다**(PAISetup #21) — 런처(WindowsApps\pythonw.exe)가 박히면 부모-자식
    #   두 프로세스가 뜨고, 자식이 죽어도 껍데기가 남아 와치독이 눈먼다.
    $proxyProcs = @(Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' or Name='python.exe'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -like "*$ProxyFile*" })
    $singleProc = ($proxyProcs.Count -eq 1)
    $notShell = $false
    if ($singleProc) {
      $procPath = $proxyProcs[0].ExecutablePath
      $notShell = (-not [string]::IsNullOrEmpty($procPath)) -and ($procPath -notlike '*\Microsoft\WindowsApps\*')
    }
    $checks += @{ Name = "로컬 프록시 단일 프로세스 (중복 껍데기 없음 — $($proxyProcs.Count)개)"; Ok = ($singleProc -and $notShell) }

    $taskArgs = (Get-ScheduledTask -TaskName $ProxyTaskName -ErrorAction SilentlyContinue).Actions | Select-Object -ExpandProperty Arguments
    $taskOk = ($taskArgs -and ($taskArgs -notlike '*WindowsApps\pythonw.exe*'))
    $checks += @{ Name = "와치독 감시 등록 (실행형 인터프리터 경로)"; Ok = [bool]$taskOk }
  }
} else {
  Write-Host '  (게이트웨이를 안 쓴다 — 구독 로그인으로 선다)'
  # ⚠ **안 쓰기로 한 자리에서는 「없나」를 잰다** — 안 재면 사내에서 한 번 깐 기계에 남은 값이 검증을 지나가고, 화면은 전부 [O]
  #   인데 CLI 는 닿지 않는 루프백으로 나간다(「사외로 간 자리의 사내 잔재」 칸).
  foreach ($v in $Vars) {
    if (-not $v.Gateway) { continue }
    $checks += @{ Name = "$($v.Name) 없음 (사외)"; Ok = (-not $userEnv[$v.Name]) }
  }
  # ⚠ **표 밖의 프록시 주소도 잰다** — 「값 파일이 든 나머지 이름」 · 「사외로 간 자리의 사내 잔재」 칸이 표가 아니라 값에서
  #   파생해 거르므로, 여기서 표만 보면 걷기가 져도 [O] 로 끝난다.
  # 묻는 것은 「이름이 비었나」가 아니라 「우리 프록시 주소가 남았나」다 — 사람이 제 주소(루프백이 아닌)를 넣어 둘 수 있고, 걷는
  #   문(`Test-OurProxyEntry`)은 값이 루프백일 때만 건다. 「없나」로 물으면 안 걷기로 한 것을 빨갛게 찍는다.
  foreach ($k in $fromFile.Keys) {
    if ($known -contains $k) { continue }
    if (-not (Test-ProxyValue $fromFile[$k])) { continue }
    $checks += @{ Name = "$k — 프록시 주소 없음 (사외)"; Ok = (-not (Test-ProxyValue $userEnv[$k])) }
  }
  # Codex · 안티그래비티 — 사내에서 심은 회사 연결이 걷혔나(「Codex · 안티그래비티 설정」 칸의 사외 갈래). 걷는 자와 같은 자(병합기의
  #   걷기 판 · `Test-AgyCompanyLink`)로 「걷을 것이 남았나」를 묻는다 — 틀과 다른 제공자 표는 맨 위 고르기가 걷혀 남아도 [O] 다(그 표를
  #   고르는 프로필은 사람 몫이다) · 사람의 API 키 갈래로 둔 `modelProvider` 도 [O] 다. 파일이 없으면 칸을 안 세운다. python 을 못
  #   쟀으면 [?], 병합기나 python 이 안 서면 [X] 다(사내 칸과 같은 자).
  if ($codexTpl -and (Test-Path -LiteralPath $CodexCfg -PathType Leaf)) {
    $ocPython = if (Test-Path -LiteralPath $CodexCfgMerge) { Measure-Runs 'python' '--version' } else { '' }
    if ($ocPython -eq 'unmeasured') {
      $checks += @{ Name = 'Codex config.toml — 회사 연결 없음 (사외)'; State = 'unmeasured'; Probe = 'python --version' }
    } else {
      $ocOk = $false
      $ocWhy = '못 잼 — 틀 병합기나 python 이 안 선다'
      if ($ocPython -eq 'yes') {
        $ocLog = [IO.Path]::GetTempFileName()
        $ocRc = Invoke-Logged 'python' @('-X', 'utf8', $CodexCfgMerge, '--config', $CodexCfg, '--template', (Join-Path $Here $codexTpl), '--remove-provider', '--check') $ocLog
        $ocOut = @(Get-Content -LiteralPath $ocLog -Encoding UTF8 -ErrorAction SilentlyContinue |
                   ForEach-Object { "$_".Trim() } | Where-Object { $_ })
        Remove-Item -LiteralPath $ocLog -ErrorAction SilentlyContinue
        $ocOk = ($ocRc -eq 0 -and $ocOut -contains 'CHANGED=0')
        $ocWhy = if ($ocOk) { '회사 연결 없음' }
                 elseif ($ocRc -eq 0) { '회사 연결이 남았다 — ' + (@($ocOut | Where-Object { $_ -like 'UNSET=*' } | ForEach-Object { $_.Substring('UNSET='.Length) }) -join ' · ') }
                 else { '못 잼 — ' + (@($ocOut | Where-Object { $_ -like 'ERROR=*' }) + @("종료 $ocRc") | Select-Object -First 1) }
      }
      $checks += @{ Name = "Codex config.toml (사외 — $ocWhy)"; Ok = $ocOk }
    }
  }
  if (Test-Path -LiteralPath $AgyCfg -PathType Leaf) {
    $oaOk = $true
    $oaWhy = '회사 연결 없음'
    try {
      $oa = Get-Content -LiteralPath $AgyCfg -Raw -Encoding UTF8 | ConvertFrom-Json
      if (Test-AgyCompanyLink $oa) { $oaOk = $false; $oaWhy = '회사 연결이 남았다 — modelProvider' }
      elseif ($oa -and $oa.PSObject.Properties['modelProvider']) { $oaWhy = '회사 연결 없음 — modelProvider 는 사람의 갈래' }
    } catch { $oaOk = $false; $oaWhy = '못 읽었다' }
    $checks += @{ Name = "안티그래비티 settings.json (사외 — $oaWhy)"; Ok = $oaOk }
  }
}
# npm 전역 자리 — 새 터미널이 볼 사용자 PATH 에 섰나(claude-config 결정 0143). 이 창의 PATH 는 배선이 태워 늘 서 있으므로
#   검증 칸 머리대로 레지스트리를 읽는다. npm 으로 까는 CLI 를 골랐을 때만 잰다.
if (@($CliPicks | Where-Object { $_.Via -ne 'winget' }).Count) {
  $checks += @{ Name = "npm 전역 자리 — 사용자 PATH ($NpmGlobalDir)"; Ok = (Test-PathListHas ([string](Get-UserPath).Raw) $NpmGlobalDir) }
}
# pip 사용자 자리 — 그 폴더가 섰으면(pip 가 그 자리에 무엇을 깔았으면) 새 터미널이 볼 사용자 PATH 에 섰나. 마무리의 「사용자 범위 명령
#   자리」가 물은 그 자리를 같은 자로 레지스트리에서 잰다(PAISetup #30 ②).
if ($PipUser.Dir -and (Test-Path -LiteralPath $PipUser.Dir)) {
  $checks += @{ Name = "pip 사용자 자리 — 사용자 PATH ($($PipUser.Dir))"; Ok = (Test-PathListHas ([string](Get-UserPath).Raw) $PipUser.Dir) }
}
# VC++ 런타임 — 「프로그램」 걸음과 같은 문 · 같은 자(파일의 판)로 문턱 위인가를 잰다(결정 0146).
if ($wantVcRuntime) {
  $vcNow = Measure-VcRuntime
  if ($vcNow.State -eq 'unmeasured') {
    $checks += @{ Name = "$($VcRuntime.Name) ($($VcRuntime.Dll) · $VcRuntimeMin 이상)"; State = 'unmeasured'; Probe = $vcNow.Probe; Why = $vcNow.Why }
  } else {
    $vcSaid = if ($vcNow.State -eq 'yes') { $vcNow.Ver } else { '없다' }
    $checks += @{ Name = "$($VcRuntime.Name) ($($VcRuntime.Dll) $vcSaid · $VcRuntimeMin 이상)"
                  Ok = [bool]($vcNow.State -eq 'yes' -and [version]$vcNow.Ver -ge $VcRuntimeMin) }
  }
}
if ($wantAutoRun -eq $true) {
  # 두 작업이 다 서야 선 것이다 — 로그온 작업만 서면 안 끄는 PC 는 여전히 날마다 안 돈다.
  $checks += @{ Name = "부팅 시 자동 실행 ($AutoRunTaskName · $AutoRunNightTaskName)"
                Ok   = ((Test-AutoRunTask $AutoRunTaskName) -and (Test-AutoRunTask $AutoRunNightTaskName)) }
}
# 칸을 찍는다 — 섰다 `[O]` · 졌다 `[X]` · 못 쟀다 `[?]`(결정 0141).
# ⚠ **못 쟀다를 `[X]` 로 찍지 않는다** — 사람은 `[X]` 를 「그 제품이 없다」로 읽고 이미 깔린 것을 다시 깔러 간다. `[X]` 밑에
#   덧댄 노란 줄로는 못 막는다 — 바로 다음에 서는 빨간 요약이 그 줄을 덮는다. 초록으로도 안 올린다 — 못 쟀으면 선 것도 아니라,
#   올리면 안 선 기계가 성공으로 보고된다(검증 칸 머리의 규율).
# 못 잰 칸의 까닭은 그 칸이 든 것(`Why` — 「``명령`` 이 …」 뒤에 이어 읽히는 꼴 · 결정 0145)이고, 없으면 `Measure-Runs` 가 그 물음에
#   남긴 까닭(`Get-ProbeWhy` — 넘김 · 못 띄움 · 종료 값)이다.
foreach ($c in $checks) {
  if ($c.State -eq 'unmeasured') {
    $over = "``$($c.Probe)`` 이 $(if ($c.Why) { $c.Why } else { Get-ProbeWhy $c.Probe })서"
    $why  = if ($c.Premise) { "$($c.Premise) 와 한 전제 — $over" } else { $over }
    Write-Host "  [?] $($c.Name) — 못 쟀다: $why" -ForegroundColor Yellow
  }
  elseif ($c.Ok) { Write-Host "  [O] $($c.Name)" -ForegroundColor Green }
  else           { Write-Host "  [X] $($c.Name)" -ForegroundColor Red }
}
# 안 한 걸음 — 못 재서 하지도 건너뛰지도 않은 걸음(`Add-UnmeasuredStep`). 끝 검증에 짝 칸이 없어 여기서 따로 찍는다. 까닭은 걸음이
#   든 것(`Why` — 넘김 · 종료 값 · 던진 오류)을 그대로 찍는다.
foreach ($s in $script:UnmeasuredSteps) {
  Write-Host "  [?] 안 한 걸음 · $($s.Step) — 못 쟀다: ``$($s.Probe)`` 이 $($s.Why) $($s.Held)" -ForegroundColor Yellow
  if ($s.Redo) { Write-Host "      새 터미널에서도 오류로 끝나면 깨진 것이다 — 손으로 다시 깐다:  $($s.Redo)" -ForegroundColor Yellow }
}
# 이 설치에서 울타리를 넘긴 프로브 — 명령마다 몇 자리에서 몇 번인가. 칸에 안 걸린 넘김(그 자리가 「안 선다 · 없음」을 적고
#   지나간 것)도 여기서 보인다. 세기에는 안 든다 — 칸 · 걸음 · `$Fails` 가 제 몫으로 이미 셌다.
if ($script:ProbeTimedOut.Count) {
  Write-Host ''
  Write-Host "  ! 울타리를 넘긴 프로브 — 그 탓에 「안 선다 · 없음 · 안 닿는다」로 적힌 줄은 없는 것이 아니라 못 잰 것이다:" -ForegroundColor Yellow
  # 한도는 자리마다 다르다 — `--version` 류는 `$ProbeCap`, 할 일을 가르는 바깥 명령은 제 한도(결정 0145). 넘김이 든 값을 찍는다.
  foreach ($g in @($script:ProbeTimedOut | Group-Object { $_.Probe })) {
    $gSites = @($g.Group | ForEach-Object { $_.Site } | Sort-Object -Unique).Count
    $gCap   = @($g.Group | ForEach-Object { $_.Cap } | Sort-Object -Unique) -join '/'
    Write-Host "      · ``$($g.Name)`` — $gSites 자리 · $($g.Count)번 (한도 ${gCap}초)" -ForegroundColor Yellow
  }
}
# gh 로그인 — 설정 저장소를 받는 PC 와 사외에서 Copilot 을 고른 PC 만 잰다. 그 둘이 이 로그인을 쓴다(개인 쪽 gh · git ·
#   Copilot CLI · claude-config 결정 0137). 사내 Copilot 은 쓰임이 아직 정해지지 않아 안 잰다.
# `$checks` 에 안 넣는다 — 무효 · 없음은 노란 줄이다. 다른 기기의 gh 로그인에 밀려 죽은 토큰은 이 설치가 못 세운 것이
#   아니고 되살리는 것은 사람의 명령 한 번이라, 빨강으로 세면 멀쩡히 깔린 PC 가 실패로 끝난다.
if ($repoUrl -or ((-not $inside) -and ($PickKeys -contains 'copilot'))) {
  $ghTokVars = @($GhEnvTokens | Where-Object {
    [Environment]::GetEnvironmentVariable($_, 'User') -or [Environment]::GetEnvironmentVariable($_, 'Machine') })
  $ghKr = Get-GhKeyringLines (Get-GhKeyringState) $ghTokVars
  foreach ($l in $ghKr.Lines) { Write-Host $l -ForegroundColor $(if ($ghKr.Ok) { 'Green' } else { 'Yellow' }) }
}
} catch { Write-StepFault $_ '검증' }
# 판정 목록은 둘이다 — `$Fails` 는 「하는 걸음이 졌다」, `$checks` 는 「끝에 다시 재 봤다」. 종료코드는 둘 다 본다(맨 끝).
# ⚠ **`$checks` 의 빨강을 종료코드에서 빼지 않는다** — `$Fails` 로 안 새는 자리가 있다: 자산 나르기(「공용 자산」 걸음)는 `$Fails` 에
#   아무것도 안 넣고, 값 심기는 던졌을 때만 넣는데 검증은 레지스트리를 다시 읽는다. 그 자리는 검증만 빨개지므로, 빼면 빨간 검증이
#   초록으로 닫힌다.
# `$Fails` 에 합치지는 않는다 — 합치면 같은 사고를 두 자가 각각 넣어 「N 개가 남았다」가 겹쳐 센다(`[X] VS Code` 와 `VS Code 설치`).
# 못 잰 칸은 빨강으로 안 세고 따로 센다 — 칸의 `[?]` 와 안 한 걸음을 합친 수다. 하나라도 서면 이 설치는 안 끝난 것이다(맨 끝
#   종료코드 · 결정 0141).
$redChecks = @($checks | Where-Object { -not $_.Ok -and $_.State -ne 'unmeasured' }).Count
$unmeasuredChecks = @($checks | Where-Object { $_.State -eq 'unmeasured' }).Count + $script:UnmeasuredSteps.Count

Write-Host ''
if ($redChecks -gt 0) {
  Write-Host "검증에서 $redChecks 칸이 빨갛다 — 바로 위 [X] 가 그것이다" -ForegroundColor Red
  Write-Host ''
}
if ($unmeasuredChecks -gt 0) {
  Write-Host "검증에서 $unmeasuredChecks 칸을 못 쟀다 — 바로 위 [?] 가 그것이다. 없는 것이 아니라 그 명령이 답을 못 냈다(한도 · 까닭은 줄마다 위에 적혔다)" -ForegroundColor Yellow
  # 세 갈래는 배포본 안내 `TROUBLESHOOTING.md` 「노란 물음표는 못 쟀다는 뜻이다」(진본은 claude-config `docs/TROUBLESHOOTING.md`)와 같은 말이다 — 한쪽을 고치면 다른 쪽도 고친다.
  Write-Host '  설치기는 그 위에 다시 깔지 않았다. 그 명령을 새 터미널에서 한 번 쳐 본다 —' -ForegroundColor Yellow
  Write-Host '    · 멎으면 그 도구 · 보안 소프트 쪽이다' -ForegroundColor Yellow
  Write-Host '    · 바로 답하면 설치를 다시 누른다' -ForegroundColor Yellow
  Write-Host '    · 오류로 끝나면 그 프로그램이 깨진 것이라 손으로 다시 깐다 — winget install --id <Id> --force 나 그 벤더의 설치본(Id 를 아는 걸음은 그 줄 아래 명령을 적었다)' -ForegroundColor Yellow
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
# 못 갈고 남은 옛 판 훅을 든 저장소(칸에서 받은 것 · 작업 루트에서 찾은 것) — 거기서 세션을 열면 그 훅이 「설정 저장소」 걸음 밖에서 돌아,
#   판에 따라 홈의 규범 · 룰을 제 사본으로 덮는다(결정 0129). 저장소 설정이 그 훅을 안 걸어도 돈다 — 홈의 SessionStart 훅이 저장소 설정에 안
#   걸린 저장소 훅을 바로 부른다. 간 저장소와 곁의 설정 저장소 때문에 못 넘긴 저장소는 지금 판 문지기가 서 있어 여기 안 든다.
# 검증 칸에 넣지 않는다 — 이 실행이 놓은 것은 지금 다 서 있어 [X] 는 거짓이고, 빨강이면 멀쩡한 설치가 빨갛게 끝난다.
$sessionOld = @(@($oldHooks) + @($scanHooks) | Where-Object { $_ -and -not $_.Current })
if ($sessionOld.Count) {
  Write-Host "옛 판 세션 훅이 남은 저장소 — $($sessionOld.Count)개: 거기서 Claude 세션을 열면 그 훅이 돌아 홈의 규범 · 룰을 제 사본으로 덮을 수 있다" -ForegroundColor Yellow
  foreach ($o in $sessionOld) {
    Write-Host "  - $($o.Repo)"
    Write-Host "    $(if ($o.Fix) { $o.Fix } else { $o.Why })"
  }
  Write-Host ''
}
if (-not $personalAny -and -not $personalByRepo) {
  Write-Host '  제작자의 규범·룰·스킬까지 원하면:  설치 창의 제작자 칸에서 도구를 고른다 (.\install.ps1 -PersonalFor claude,codex,agy)'
  Write-Host ''
}

# ── 연다 — **깐 것을, 이 창의 자식으로** ───────────────────────────────────────
# 안내로 끝내지 않고 여기서 띄운다 — 창은 뜰 때 PATH 와 환경변수를 한 번 복사하고 그 뒤에 바뀐 것은 안 따라온다. 이 창은 심은
#   값을 제 프로세스에도 들고 있어(`Plant-Var`), 여기서 난 자식은 로그아웃 없이 그 값을 문다.
# 무엇을 띄우나는 자리가 아니라 깐 것이 정한다(아래 「열 것을 모은다」). 자리(`$offsite`)는 끝 줄의 기본값만 고른다 — 사외는 구독
#   로그인이라 데스크탑 앱 · VS Code 를, 사내는 방금 심은 키를 물게 VS Code 를 새로 열라고 한다.
# 못 열어도 실패로 안 센다 — 설치는 이미 선 것이고 창은 사람이 손으로도 연다. 빨강으로 세면 멀쩡히 깔린 기계가 빨갛게 보고된다.

# 찾는 자(`Find-DesktopApps` · `Find-VSCode`)는 「무엇을」이 아니라 「어떻게 띄우나」를 돌려준다 — VS Code 는 실행 파일을 직접
#   띄워야 이 창이 방금 심은 값을 물고 뜨고, 데스크탑은 띄울 실행 파일이 아예 없다. 그래서 `Exe` 를 든 것과 `AppId` 를 든 것이
#   갈려 나온다. `Proc` 는 「이미 떠 있나」를 재는 이름(들)이다(까닭은 `Find-DesktopApps` 안에).

# ⚠ **화면 껍데기의 완료 문구는 마지막 `=== 끝 ===` 줄에서 난다** — 저쪽에 같은 문장을 또 적으면 갈래가 늘 때마다 한쪽만 낡는다.
# 이 줄만 사람에게 건네는 말이라 「…하세요」로 적는다 — 위는 다 기록이다.
$tail = if ($offsite) {
  '구독 로그인으로 섭니다 — Claude 데스크탑이나 VS Code 를 새로 여세요'
} else {
  '열려 있는 VS Code 를 전부 닫고 새로 여세요 — 낡은 창은 방금 심은 키를 못 봅니다'
}

# ── 이번 실행이 깐 Codex 데스크탑 — 로그인이 서 있을 때만 닫고 · 심고 · 다시 띄운다 (claude-config 결정 0135) ──────────────────────
# 데스크탑의 로그인은 앱 서버 안에서 돌아, 마치기 전에 닫으면 날아가 다시 띄운 창이 또 묻는다(#164). 그래서 설치 중에는 안 닫고, 아래
#   띄우기 칸에서 로그인이 자격 저장소에 섰을 때만 닫고 심기(`--plant` — 작업 루트 저장소 0126 · 새 대화 기본 권한 0127)를 부르며,
#   닫은 것은 그 칸의 띄우기 고리가 다시 띄운다. 로그인 전이거나 그것을 못 쟀으면 안 닫는다 — 그 앱의 심기는 다음 설치(사람이 다시
#   띄우기에 동의한 판)가 한다. 창을 안 띄우는 판(`-NoLaunch`)도 안 닫는다 — 닫고 다시 못 띄우면 방금 로그인한 앱이 사라진다.
# 섰는지는 데스크탑과 같은 꾸러미의 Codex 실행 파일에 `login status` 로 묻는다 — 데스크탑과 같은 홈(`CODEX_HOME` → `~/.codex`)의 같은
#   자격을 읽어, 0 이면 다시 띄운 앱도 로그인을 안 묻는다. 1 은 「안 섰다」다(자격을 못 읽은 것도 1 이고, 그때는 다시 띄운 앱도 묻는다).
#   표준입력으로 말을 주고받지 않아 5.1 이 자식의 표준입력에 넣는 BOM 에 안 걸린다.
# 내는 것 — @{ State = in · out · unmeasured; Why = 화면 줄에 이어 읽히는 까닭 }.
$CodexDesktopCli = 'app\resources\codex.exe'
function Get-CodexDesktopLogin($App) {
  $exe = if ($App.Dir) { Join-Path $App.Dir $CodexDesktopCli } else { '' }
  if (-not $exe -or -not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    return @{ State = 'unmeasured'; Why = "로그인을 못 재(꾸러미에서 $CodexDesktopCli 를 못 찾아)" }
  }
  $rc = Invoke-ProbeCapped $exe 'login status' $ProbeCap
  if ($rc -eq 0) { return @{ State = 'in'; Why = '' } }
  if ($rc -eq 1) { return @{ State = 'out'; Why = '로그인 전이라' } }
  return @{ State = 'unmeasured'; Why = "로그인을 못 재(``codex.exe login status`` 이 $(Format-ProbeWhy $rc $ProbeCap))" }
}

# ⚠ **이 칸은 무엇을 던져도 설치를 못 끝낸다** — `Stop` 아래에서 한 줄이 던지면 마지막 `exit` 까지 못 가고, 화면 껍데기는
#   종료코드를 못 읽어 멀쩡한 설치를 빨갛게 낸다. 창을 여는 것은 덤이라 여기서 진 것은 여기서 삼킨다.
try {

if ($NoLaunch) {
  Write-Host '  창은 안 띄운다 (-NoLaunch)'
} else {
  # ⚠ **띄우기 직전에 새 창이 볼 자리(사용자 환경)를 이 창으로 당긴다** — 저장소의 훅으로 넘긴 판에서는 훅이 개인 키를 심었고
  #   그 값은 레지스트리에만 있어, 그대로 자식을 내면 낡은 환경을 물려준다. 검증 칸이 훅이 끝난 뒤에 읽어 둔 값(`$userEnv`)이다.
  # ⚠ **PATH 만은 안 당긴다** — 그 이름은 기계 값과 사용자 값이 합쳐져 서는 자리라, 사용자 쪽만 덮으면 이 창이 여태 태운
  #   배선(`Update-RuntimePath`)이 통째로 날아간다.
  foreach ($k in $userEnv.Keys) {
    if ($k -ieq 'PATH') { continue }
    [Environment]::SetEnvironmentVariable($k, $userEnv[$k], 'Process')
  }

  # 열 것을 모은다 — 깔았으면 띄운다. 자리가 아니라 깐 목록(`$script:InstalledAppRows`)에 묻는다 — 사내에서도 깔리는 앱이 있어
  #   (결정 0059) 자리로 물으면 방금 깐 앱이 안 뜨고 로그만 초록이다.
  $apps = @()
  if ($script:InstalledAppRows.Count) {
    $apps = @(Find-DesktopApps)
    # 깐 것 가운데 못 찾은 것을 이름으로 댄다 — 말없이 넘어가면 사람은 「왜 안 뜨지」를 혼자 헤맨다. 막힌 회선에서 한 제품만 안
    #   깔린 자리가 이 줄에서 보인다.
    # ⚠ **견줄 자는 「고른 것」이 아니라 「깐 것」이다** — 사내에서 안 깐 앱(`When = offsite`)을 세면 깔지도 않은 것을 「못
    #   찾았다」로 찍는다. 깐 것이 하나도 없으면 이 칸을 안 지난다(위 `if`) — 못 찾은 것과 찾을 것이 없는 것은 다른 말이다.
    $found = @($apps | ForEach-Object { $_.Name })
    $miss  = @($script:InstalledAppRows.Keys | Where-Object { $found -notcontains $_ })
    # ⚠ **`$miss` 는 이미 이름(`InstalledAppRows` 의 열쇠)이다** — `$_.Label` 로 한 겹 더 꺼내면 `$null` 이 되어 이름이 빈
    #   「! — 못 찾았다」만 찍힌다.
    if ($miss) {
      Write-Host ('  ! {0} — 못 찾았다. 시작 메뉴에서 직접 연다' -f
                  ($miss -join ' · ')) -ForegroundColor Yellow
    }
  }
  # VS Code 도 늘 같이 연다 — 데스크탑이 있어도 설치한 것은 끝에 다 연다. 목록 끝에 두므로 먼저 떠서 아래에 깔리고 데스크탑이
  #   그 위에 선다(아래 「역순으로 띄운다」 — 보장은 못 한다). `-NoVsCode` 로 뺀 자리는 안 연다.
  # ⚠ **`$null` 을 배열에 담지 않는다** — `Find-VSCode` 는 못 찾으면 `$null` 을 내는데 `@($null)` 은 빈 배열이 아니라 원소
  #   하나짜리라, 아래 고리들이 그 `$null` 을 든다.
  if ($hasCode -and -not $NoVsCode) { $apps = @($apps) + @(Find-VSCode | Where-Object { $_ }) }

  $skip = @()
  if (-not $apps) {
    Write-Host '  ! 열 것을 못 찾았다 — 시작 메뉴에서 직접 연다' -ForegroundColor Yellow
  } else {
    # 이번 실행이 깐 Codex 데스크탑 — 로그인이 서 있으면 닫고 심는다(위 `Get-CodexDesktopLogin` 머리말). 닫은 것은 아래 고리가 다시
    #   띄우고, 안 닫은 것은 아래 「이미 실행되었다」 줄로 지나간다. 여기서 진 것은 실패로 안 센다(이 칸의 규율).
    if ($bash) {
      $codexRow = $DesktopApps | Where-Object { $_.Key -eq 'codex' }
      if ($codexRow -and $script:JustInstalledApps.ContainsKey($codexRow.App)) {
        $codexApp = @($apps | Where-Object { $_.App -eq $codexRow.App }) | Select-Object -First 1
        if ($codexApp -and (Test-AppUp $codexApp)) {
          $codexLogin = Get-CodexDesktopLogin $codexApp
          if ($codexLogin.State -eq 'in') {
            if (Stop-App $codexApp) {
              $codexPlant = Invoke-Plant $bash $configRepoRoot
              if ($codexPlant.Ok) { Write-Host '  Codex 데스크탑 — 로그인이 서 있어 닫고 심기를 불렀다(무엇을 심었나는 위 몸통 줄) · 다시 띄운다' -ForegroundColor Green }
              else { Write-Host "  ! 심기 — $($codexPlant.Why) · Codex 데스크탑의 프로젝트 · 기본 권한은 다음 설치가 적는다 · 다시 띄운다" -ForegroundColor Yellow }
            } else {
              Write-Host '  ! Codex 데스크탑 — 못 닫았다 · 프로젝트 · 기본 권한은 다음 설치가 적는다' -ForegroundColor Yellow
            }
          } else {
            Write-Host "  Codex 데스크탑 — $($codexLogin.Why) 안 닫는다 · 프로젝트 · 기본 권한은 다음 설치가 적는다"
          }
        }
      }
    }
    # 방금 깐 앱을 인스톨러(스토어 스텁 · Squirrel 등)가 제 손으로 띄우기도 한다 — 또 띄우면 창이 두세 번 뜬다.
    # ⚠ **「방금 깔았다」는 「떠 있다」가 아니다** — 무인 설치(`SilentArgs`)로 깐 갈래는 창을 안 띄우는 것이 정상이라, 깐 것만으로
    #   빼면 로그는 초록인데 화면에는 아무것도 안 뜬다. `Test-AppUp` 으로 정말 떠 있는 것만 빼고, 나머지는 아래 고리가 띄운다.
    $newlyLaunched = @()
    foreach ($a in $apps) {
      if ($a.App -and $script:JustInstalledApps.ContainsKey($a.App) -and (Test-AppUp $a)) {
        $newlyLaunched += $a.Name
      }
    }
    if ($newlyLaunched) {
      Write-Host ('  ' + ($newlyLaunched -join ' · ') + ' — 설치 완료 후 이미 실행되었다') -ForegroundColor Green
      $skip += $newlyLaunched
    }

    # ⚠ **떠 있는 것은 그대로 다시 띄우지 않는다** — 돌던 것은 뒤에 온 것을 모른다:
    #   · 환경 — 창은 뜰 때 환경을 한 번 복사한다. VS Code 는 `code` 를 다시 불러도 돌던 그 프로세스가 창을 내므로 방금 심은 키를
    #     못 본다. `--new-window` 도 창만 새로 낼 뿐 프로세스를 안 가르고, 가르는 레버인 `--user-data-dir` 는 설정 · 상태가 통째로
    #     딴 자리가 된다
    #   · 선언 — 이 설치와 설정 저장소의 훅이 규범 · 세션 훅을 심었는데, 돌던 앱은 그 선언을 뜰 때 한 번 읽고 말았다
    #   창을 앞으로 불러 주지도 않는다 — 트레이에 내려간 것을 다시 띄우면 새로 뜬 것처럼 보여도 안에 든 것은 그대로다.
    # ⚠ **떠 있는 것을 설치가 묻지 않고 죽이지 않는다** — 저장 안 한 것이 날아간다. 끌지는 사람이 정한다(`Ask-Restart`).
    # 모아서 한 번만 묻는다 — 앱마다 물으면 모달 창이 연달아 뜬다. 묻는 값은 하나로 묶고 답은 다 같이 든다.
    $up = @($apps | Where-Object { $skip -notcontains $_.Name -and (Test-AppUp $_) })
    if ($up) {
      $names = ($up | ForEach-Object { $_.Name }) -join ' · '
      Write-Host "  $names — 이미 떠 있다"
      if (Ask-Restart $names) {
        Write-Host '  끈다 — 창을 닫으라고 보내고, 안 나가면 세게 끝낸다'
        foreach ($u in $up) {
          if (Stop-App $u) { Write-Host "  $($u.Name) — 껐다" -ForegroundColor Green }
          else {
            # ⚠ **못 껐으면 「껐다」로 안 넘어간다** — 안 끄고 띄우면 돌던 그 프로세스가 창을 내므로, 사람은 재시작한 줄 알고 낡은
            #   것을 그대로 쓴다.
            Write-Host "  ! $($u.Name) — 안 꺼졌다. 직접 끄고 연다" -ForegroundColor Yellow
            $skip += $u.Name
          }
        }
        # 끈 것이 있으면 다시 띄우기 전에 심는다 — 떠 있던 앱 때문에 「설정 저장소」 걸음의 심기가 미룬 칸(Codex 데스크탑의 권한 ·
        #   프로젝트 · agy 데스크탑 · VS Code 신뢰)이 닫힌 지금 선다(claude-config 결정 0135). 기다리지 않는다 — 심고 바로 띄운다.
        # 여기서 진 것은 실패로 안 센다 — 이 칸의 규율(위 「못 열어도 실패로 안 센다」)이고, 같은 심기는 「설정 저장소」 걸음이 이미
        #   셌다. 줄로만 낸다.
        if (@($up | Where-Object { $skip -notcontains $_.Name }).Count) {
          $replant = Invoke-Plant $bash $configRepoRoot
          if (-not $replant.Ok) { Write-Host "  ! 심기 — $($replant.Why) · 다시 띄운 앱의 미룬 칸은 다음 설치가 심는다" -ForegroundColor Yellow }
        }
      } else {
        Write-Host '  안 끈다 — 떠 있는 것은 안 띄운다'
        $skip += @($up | ForEach-Object { $_.Name })
      }
    }

    $go = @($apps | Where-Object { $skip -notcontains $_.Name })
    $opened = @()
    if ($go) {
      # 띄우기 전에 한 박자 둔다 — 새 창은 설치 창을 덮으므로, 바로 띄우면 이 설치의 결론인 검증 칸의 `[O]/[X]` 를 아무도 못 읽는다.
      Write-Host '  3초 뒤에 엽니다 — 위 검증 칸을 먼저 읽는다' -ForegroundColor Yellow
      Start-Sleep -Seconds 3
      # ⚠ **`Start-Process` 로 띄운다** — 이 창의 나가는 손잡이는 화면 껍데기가 따라 읽는 파일로 돌려져 있어, 그것을 물려주면
      #   자식이 그 파일을 붙들고 껍데기의 뒷정리가 막힌다. `-Wait` 는 안 건다 — 걸면 사람이 그 창을 닫을 때까지 설치가 안 끝난다.
      # 띄우는 길은 둘이다 — 실행 파일이 있으면 이 창의 자식으로 띄워 방금 심은 값을 물게 하고, 없으면(스토어 꼴) 앱 손잡이로
      #   껍데기에 맡긴다.
      # 역순으로 띄운다 — 표에서 앞선 것이 마지막에 떠 위에 서게. 앱마다 뜨는 속도가 달라 보장은 못 한다.
      # ⚠ **「띄웠다」는 떴다는 말이다** — 방금 끈 앱은 아직 내려가는 중이라 새로 보낸 것이 죽어 가는 프로세스에 넘겨지고 끝날 수
      #   있다. 보낸 뒤 떴는지 재고(`Test-AppUp` · 그 앱 폴더의 프로세스), 안 떴으면 한 번 더 보내고, 그래도 안 뜨면 노란 줄로
      #   사람에게 넘긴다(실패로 안 센다).
      $sendApp = {
        param($one)
        try {
          if ($one.Exe) { Start-Process -FilePath $one.Exe | Out-Null }
          else          { Start-Process "shell:AppsFolder\$($one.AppId)" | Out-Null }
          return $true
        } catch {
          # 조사를 안 붙인다 — 여기는 이름이 여럿 지나는 자리다.
          Write-Host "  ! 못 띄웠다 ($($one.Name)) — $(Say-Why $_)" -ForegroundColor Yellow
          return $false
        }
      }
      # 보낸 것들이 뜨기를 기다린다 — 다 뜨면 바로 나간다. 돌려주는 것은 아직 안 뜬 것이다.
      $waitUp = {
        param($list, [int]$sec)
        for ($t = 0; $t -lt $sec; $t++) {
          $left = @($list | Where-Object { -not (Test-AppUp $_) })
          if (-not $left) { return @() }
          Start-Sleep -Seconds 1
        }
        return @($list | Where-Object { -not (Test-AppUp $_) })
      }
      $sent = @()
      for ($i = $go.Count - 1; $i -ge 0; $i--) {
        if (& $sendApp $go[$i]) { $sent += $go[$i] }
      }
      $late = @(& $waitUp $sent 20)
      if ($late) {
        Write-Host ('  ' + (($late | ForEach-Object { $_.Name }) -join ' · ') + ' — 아직 안 떴다. 한 번 더 띄운다')
        $resent = @($late | Where-Object { & $sendApp $_ })
        $late = @(& $waitUp $resent 15) + @($late | Where-Object { $resent -notcontains $_ })
      }
      foreach ($one in $sent) {
        if ($late -contains $one) {
          Write-Host "  ! $($one.Name) — 안 떴다. 시작 메뉴에서 직접 연다" -ForegroundColor Yellow
        } else {
          Write-Host "  $($one.Name) — 띄웠다" -ForegroundColor Green
          $opened += $one.Name
        }
      }
      # VS Code 는 저장소를 처음 열 때 제 작업 영역 신뢰를 따로 묻고, 그 전에는 제한 모드라 확장이 다 꺼진다 — 한 번 신뢰하면
      #   Claude · Codex · agy 확장이 함께 풀린다. 설정 저장소 훅이 작업 루트 저장소를 VS Code 의 신뢰 목록에 미리 적되(claude-config
      #   결정 0130) VS Code 가 떠 있었으면 미루므로, 「Trust 한 번」 줄은 심은 기록이 하나도 없을 때만 낸다. 기록의 자리와 꼴은
      #   씨앗의 도우미가 들고 여기는 그 `status` 를 묻는다 — 못 물으면 줄을 낸다. 끝 줄은 창의 한 줄 칸에 떠 길게 못 붙이므로
      #   기록 칸 한 줄에 드는 길이로 따로 낸다.
      if ($opened -contains 'VS Code') {
        $vsTrust = Join-Path $ConfigSeedHooks 'vscode-trust.py'
        # 묻는 한 번에 울타리를 두른다 — 넘기면 「못 물었다」라 줄을 낸다
        $vsSeen = @()
        if (Test-Path -LiteralPath $vsTrust) {
          $vl = [IO.Path]::GetTempFileName()
          try {
            $vrc = Invoke-LoggedCapped 'python' @('-X', 'utf8', $vsTrust, 'status') $vl $ProbeCap
            if ($vrc -eq -2) { Add-ProbeOverflow 'python vscode-trust.py status' $ProbeCap }
            else { $vsSeen = @(@(Get-Content -LiteralPath $vl -Encoding UTF8 -ErrorAction SilentlyContinue) -match '^SEEN=[1-9]') }
          } finally { Remove-Item -LiteralPath $vl, "$vl.err" -ErrorAction SilentlyContinue }
        }
        if (-not $vsSeen) {
          Write-Host '  VS Code 가 이 폴더를 믿느냐고 물으면 Trust 한 번 — 확장이 함께 풀린다' -ForegroundColor Yellow
        }
      }
    }

    # 끝 줄은 실제로 무슨 일이 났나로 갈린다 — 띄운 것 · 안 띄운 것 · 아무것도 아닌 것.
    # 이름 뒤에 조사를 안 붙인다 — 여럿이면 받침도 띄어쓰기도 이름마다 갈려, 한 틀에 밀어 넣으면 사람이 마지막에 읽는 줄에서 하나가
    #   어긋난다.
    $shown = @($go | Where-Object { $opened -contains $_.Name } | ForEach-Object { $_.Name })
    if ($shown.Count -eq 1 -and $shown[0] -eq 'VS Code') {
      $tail = 'VS Code 를 열었습니다 — Ctrl+Shift+P → Claude 로 확장을 엽니다'
    } elseif ($shown) {
      $tail = '연 창에서 각각 로그인합니다 — ' + ($shown -join ' · ')
    } elseif ($skip) {
      $tail = ($skip -join ' · ') + ' — 트레이(시계 옆)에서 완전히 끄고 새로 여세요. 창만 닫으면 안 꺼집니다'
    }
  }
}

} catch {
  Write-Host "  ! 여는 자리에서 졌다 — $(Say-Why $_)" -ForegroundColor Yellow
}

# ── 옛 제작자 칸을 이어받은 판의 마무리 — 알림 창을 한 번 띄운다 (결정 0099) ──────────
# 기록은 「회차를 넘기는 기록」 칸이 이미 새 꼴(`personal=claude`)로 썼다 — 다음 회차는 옛 칸으로 안 와 다시 안 묻는다.
# 창은 기다리지 않는다 — 따로 띄우고 이 몸통은 끝난다. 닫으면 그대로(Claude), 고르고 누르면 그 선택이 새 기록이 된다.
# 알림 창을 띄웠나(`$noticeShown`) — 그 창이 닫힐 때 「제공기능」을 열므로 아래 「제공기능」 칸이 안 연다.
$noticeShown = $false
# 밤 자동 실행은 창을 안 띄운다. 그 회차가 기록을 새 꼴로 쓰면 이 알림은 안 뜬다 — 밤 작업이 선 PC 는 그 작업을 건 판(v2.2.0 뒤의
#   로그온 회차나 설치 창)이 이미 옛 칸을 이어받았다(이어받기는 v2.0.0 부터다 · PAISetup #45 ⑧).
if ($PersonalUpgrade -and -not $NightRun) {
  $uiScript = Join-Path $Here 'install.ui.ps1'
  if (Test-Path -LiteralPath $uiScript) {
    try {
      Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                                                              ('"' + $uiScript + '"'), '-PersonalNotice') | Out-Null
      $noticeShown = $true
      Write-Host '  제작자 칸이 도구마다로 바뀌었다 — 옛 칸을 Claude 로 이어받아 깔았고, 바꿀 수 있게 설치 창을 한 번 띄웠다' -ForegroundColor Yellow
    } catch {
      Write-Host "  ! 알림 창을 못 띄웠다 — $(Say-Why $_). 바꾸려면 설치 창을 열어 제작자 칸을 고른다" -ForegroundColor Yellow
    }
  }
}

# ── 「제공기능」 — 새 작은 판을 처음 깐 PC 에서 설치 끝에 한 번 연다 (claude-config 결정 0147) ──────────
# 설치 창 · 콘솔 · 로그온 자동 실행 어느 판이든 같다 — 창의 「제공기능」 링크는 다시 볼 때의 길로 남는다. 옛 제작자 칸 알림 창을 띄운
#   판은 그 창이 연다(위 `$noticeShown`).
# ⚠ **무엇을 던져도 설치를 못 끝낸다** — 안내 페이지는 덤이다(「연다」 칸과 같은 규율).
# 밤 자동 실행은 열지도 적지도 않는다 — 적으면 그 판을 본 것으로 남아 다음 로그온 · 설치 창이 안 연다.
if ($NightRun) {
  Write-Host '  제공기능 — 밤 자동 실행이라 안 연다 (다음 로그온 · 설치 창이 연다)'
} else {
  try {
    $featHow = Open-FeaturesOnce $DistVersion $noticeShown `
                                 (Join-Path (Join-Path $env:LOCALAPPDATA 'Claude Code Setup') 'features.major') (Join-Path $Here 'features.html')
    switch ($featHow) {
      'opened' { Write-Host "  제공기능 — 이 판($DistVersion)의 앞 두 자리를 처음 깐 설치라 브라우저로 열었다" -ForegroundColor Green }
      'nopage' { Write-Host '  ! 제공기능 — 이 폴더에 features.html 이 없어 못 열었다 (다음 설치 · 로그온에 다시 본다)' -ForegroundColor Yellow }
      'failed' { Write-Host '  ! 제공기능 — 브라우저로 못 열었다 (다음 설치 · 로그온에 다시 연다)' -ForegroundColor Yellow }
    }
  } catch {
    Write-Host "  ! 제공기능 — $(Say-Why $_)" -ForegroundColor Yellow
  }
}

Write-Host ''
Write-Host "=== 끝 === $tail" -ForegroundColor Yellow
Write-Host ''
# ⚠ **총계는 `exit` 둘보다 위에 둔다** — 아래는 진 판이 1 로 나가는 자리라, 그 뒤에 적으면 진 판에서만 총계가 사라진다.
Write-Host ("── 설치를 마쳤다 (" + [int]$Sw.Elapsed.TotalSeconds + "초)") -ForegroundColor DarkGray
# ── 빗장 해제 ────────────────────────────────────────────────────────────────
try { if ($script:HasEngineMutex -and $script:EngineMutex) { $script:EngineMutex.ReleaseMutex(); $script:EngineMutex.Dispose() } } catch { }

# ⚠ **셋 다 본다** — 하는 걸음이 진 것(`$Fails`) · 끝에 재서 빨간 것(`$redChecks`) · 못 잰 것(`$unmeasuredChecks`)은 겹치기도 하고
#   한쪽만 서기도 한다. 어느 쪽이든 하나라도 서면 이 설치는 안 끝난 것이다 — 못 잰 것은 빨강이 아니지만 선 것도 아니다(결정 0141).
if ($Fails.Count -gt 0 -or $redChecks -gt 0 -or $unmeasuredChecks -gt 0) { exit 1 }
# ⚠ **성공 경로에도 `exit` 가 있어야 한다** — 파일 끝으로 떨어지면 화면 갈래는 성하지만(`cmd /c` 가 `-File` 규약으로 0 을 낸다),
#   콘솔 갈래는 같은 런스페이스 안에서 이 파일을 부른 뒤 `$LASTEXITCODE` 를 읽는다. 그 값은 이 파일이 마지막으로 부른 네이티브
#   명령이 남긴 남의 값이라, 멀쩡히 끝난 설치가 앞선 명령의 1 을 물고 실패로 보고된다.
exit 0
