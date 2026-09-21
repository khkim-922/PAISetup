# 새 판이 있나 묻고, 받은 것이 릴리스에 오른 것이 맞는지 잰다.
#
# ⚠ **여기에 「그래서 어떻게 할까」가 없다.** 이 파일은 묻고 재기만 하고, 물러설지 띄울지
#   풀지는 부르는 쪽이 정한다 — 부르는 자가 둘이고 서로 다르게 굴기 때문이다:
#     * `install.ui.ps1` — 사람이 보는 창. 「예」를 받고, 진 까닭을 말로 띄운다
#     * `autorun.ps1`    — 아무도 안 보는 자리. 진 까닭을 로그에 한 줄로 적고 그냥 간다
#   판단을 여기 넣으면 그 둘이 갈릴 때 한쪽이 남의 규칙을 탄다.
#
# ⚠ **진 까닭을 문자열 하나로 뭉치지 않는다.** 「자산이 없다」와 「값이 다르다」는 부르는
#   쪽이 서로 다르게 다뤄야 하는 명제라 `Status` 로 갈라 낸다 — 말로만 주면 부르는 쪽이
#   그 말을 다시 파싱하게 되고, 문구를 고치는 날 조용히 어긋난다.
#
# ⚠ **망을 못 타는 것과 최신인 것은 다른 명제다.** 못 물었으면 `$null` 이고, 그것을
#   「최신이다」로 읽지 않는다 — 막힌 망에서 낡은 판을 든 사람이 낡은 줄 모른 채 간다.

Set-StrictMode -Off

function Find-NewerRelease {
    <#
      `$Repo` 의 최신 릴리스가 `$Mine` 보다 높으면 그 자리를 돌려준다. 아니면 `$null`.
      못 물어도 `$null` 이다 — 위 ⚠ 대로 부르는 쪽이 그 둘을 안 섞는다.
    #>
    param([string]$Repo, [string]$Mine, [int]$TimeoutSec = 8)

    if (-not $Repo -or -not $Mine) { return $null }
    try {
        $r = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest" `
               -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
        $new = ([string]$r.tag_name) -replace '^[vV]', ''
        if ([version]$new -le [version]$Mine) { return $null }

        # ⚠ **자산이 있어야 뜻이 있다.** 설치본 파일이 안 붙은 릴리스는 받을 것이 없다 —
        #   그때 「새 판이 있다」고만 말하면 사람이 받을 데를 못 찾고 헤맨다.
        $a = @($r.assets | Where-Object { $_.name -eq 'Setup.exe' })[0]
        if (-not $a) { return $null }

        # 곁의 해시 자산도 같이 집어 온다 — 받은 것을 대조할 자가 이 줄 하나다. 없으면 없는
        # 대로 들고 간다: 「없다」와 「다르다」를 아래가 서로 다른 말로 해야 한다.
        $s = @($r.assets | Where-Object { $_.name -eq 'Setup.exe.sha256' })[0]
        $shaUrl = ''
        if ($s) { $shaUrl = [string]$s.browser_download_url }

        $rel = [string]$r.tag_name
        if ($r.name) { $rel = [string]$r.name }
        return @{ Ver = $new; Url = [string]$a.browser_download_url; ShaUrl = $shaUrl; Rel = $rel }
    } catch { return $null }
}

function Get-VerifiedSetup {
    <#
      `Find-NewerRelease` 가 준 자리에서 설치본을 받아 **릴리스에 오른 지문과 대조한다.**
      맞을 때만 `Ok` 다. 돌려주는 것: `@{ Ok; Status; Detail; Path; Want; Have }`

      `Status` — ok · no-hash-asset · hash-unreadable · hash-mismatch · download-failed

      ⚠ **우리가 받으면 윈도우의 「인터넷에서 온 파일」 표시가 안 붙는다** — 브라우저로 받을
        때만 붙는다. 그래서 브라우저로 받았으면 SmartScreen 이 한 번 섰을 자리가 여기엔 없다.
      ⚠ **그 자리를 해시가 든다.** 대조 없이 띄우면 `#update-repo` 저장소에 쓸 수 있게 된
        자가 민 임의의 exe 가 경고 없이 돌고, 이 설치기가 전제하는 「TLS 를 가로채는 회사
        장비」가 그 연결도 가로챌 수 있다 (claude-config #33).
      ⚠ **자산이 없으면 「못 쟀다」다 — 「맞다」가 아니다.** 부재가 통과로 읽히는 그 자리라,
        옛 릴리스는 자동으로 안 띄우고 릴리스 이름을 대며 물러난다.
    #>
    param([hashtable]$Found, [string]$Dest)

    if (-not $Dest) { $Dest = Join-Path ([IO.Path]::GetTempPath()) ("ClaudeCodeSetup-" + $Found.Ver + ".exe") }
    $sha = "$Dest.sha256"

    if (-not $Found.ShaUrl) {
        return @{ Ok = $false; Status = 'no-hash-asset'; Path = $Dest
                  Detail = "릴리스 $($Found.Rel) 에 Setup.exe.sha256 이 없다 — 대조할 자가 없다" }
    }
    try {
        Invoke-WebRequest -Uri $Found.Url    -OutFile $Dest -UseBasicParsing -TimeoutSec 180 -ErrorAction Stop
        Invoke-WebRequest -Uri $Found.ShaUrl -OutFile $sha  -UseBasicParsing -TimeoutSec 30  -ErrorAction Stop
    } catch {
        return @{ Ok = $false; Status = 'download-failed'; Path = $Dest; Detail = $_.Exception.Message }
    }

    # 자산은 `sha256sum` 한 줄이다 — 앞의 64 글자만 든다. 대소문자는 안 가린다.
    $want = $null
    try {
        $txt = Get-Content -LiteralPath $sha -Raw -Encoding UTF8
        if ($txt -match '([0-9a-fA-F]{64})') { $want = $Matches[1].ToLowerInvariant() }
    } catch { $want = $null }
    if (-not $want) {
        return @{ Ok = $false; Status = 'hash-unreadable'; Path = $Dest
                  Detail = "릴리스 $($Found.Rel) 의 Setup.exe.sha256 을 읽지 못했다" }
    }

    $have = (Get-FileHash -LiteralPath $Dest -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($want -ne $have) {
        return @{ Ok = $false; Status = 'hash-mismatch'; Path = $Dest; Want = $want; Have = $have
                  Detail = "받은 것이 릴리스에 오른 값과 다르다" }
    }
    return @{ Ok = $true; Status = 'ok'; Path = $Dest; Want = $want; Have = $have; Detail = '' }
}
