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
# ⚠ **망을 못 타는 것과 최신인 것은 다른 명제다.** 못 물었으면 `unmeasured` 이고, 그것을
#   「최신이다」로 읽지 않는다 — 막힌 망에서 낡은 판을 든 사람이 낡은 줄 모른 채 간다.
#
# ⚠ **GitHub API 를 안 탄다.** 로그인 없는 API 는 출구 IP 하나에 시간당 60 번이라, 출구를
#   여럿이 같이 쓰는 회사망 · VDI 에서는 남이 쓴 몫에 걸려 403 이 난다. 웹의 받는 주소가
#   태그 주소로 넘기는 자리(`releases/latest/download/<자산>` → `releases/download/<태그>/<자산>`)
#   에서 태그를 읽고, 자산이 있나는 그 태그의 받는 주소가 넘기나(3xx) · 404 냐로 잰다.
#   최신 주소의 넘김은 자산이 있나를 안 보고 서므로 자산은 태그 주소에서 따로 묻는다.

Set-StrictMode -Off

# 받는 주소 하나를 넘김을 따라가지 않고 묻는다(HEAD) — 넘기는 곳이 답이다.
# 내는 것 — `@{ Code; Location; Why }`. `Code` 는 상태 번호이고 못 닿았으면 0 이다(`Why` 가 까닭).
function Get-ReleaseHop([string]$Url, [int]$TimeoutSec) {
    $res = $null
    try {
        $q = [Net.HttpWebRequest]::Create($Url)
        $q.Method = 'HEAD'
        $q.AllowAutoRedirect = $false
        $q.Timeout = $TimeoutSec * 1000
        $res = $q.GetResponse()
        return @{ Code = [int]$res.StatusCode; Location = [string]$res.Headers['Location']; Why = '' }
    } catch [Net.WebException] {
        # 4xx · 5xx 는 응답을 든 채 던진다 — 번호는 거기서 읽는다
        $res = $_.Exception.Response
        if ($res) { return @{ Code = [int]$res.StatusCode; Location = ''; Why = "$([int]$res.StatusCode)" } }
        return @{ Code = 0; Location = ''; Why = $_.Exception.Message }
    } catch {
        return @{ Code = 0; Location = ''; Why = $_.Exception.Message }
    } finally {
        if ($res) { $res.Close() }
    }
}

function Measure-NewerRelease {
    <#
      `$Repo` 의 최신 릴리스를 `$Mine` 과 견준다. 내는 것: `@{ State; Ver; Found; Why }`

      `State` — newer      더 높은 판에 Setup.exe 가 붙었다. `Found` 가 받을 자리(`Ver · Url · ShaUrl · Rel`)를 든다
                latest     더 높은 판이 없다
                no-asset   더 높은 판이 있는데 Setup.exe 가 안 붙었다
                unmeasured 못 물었다 — 망이 막혔거나 답의 꼴이 낯설다. `Why` 가 까닭

      ⚠ **자산이 있어야 뜻이 있다.** 설치본 파일이 안 붙은 릴리스는 받을 것이 없다 — 그때
        「새 판이 있다」고만 말하면 사람이 받을 데를 못 찾고 헤맨다.
      ⚠ **해시 자산이 없으면 `ShaUrl` 을 비운 채 `newer` 다.** 「없다」와 「다르다」를
        `Get-VerifiedSetup` 이 서로 다른 말로 해야 한다.
    #>
    param([string]$Repo, [string]$Mine, [int]$TimeoutSec = 8)

    if (-not $Repo -or -not $Mine) { return @{ State = 'unmeasured'; Why = '저장소나 지금 판을 모른다' } }
    $site = "https://github.com/$Repo/releases"

    $hop = Get-ReleaseHop "$site/latest/download/Setup.exe" $TimeoutSec
    if ($hop.Code -eq 0) { return @{ State = 'unmeasured'; Why = "github.com 에 못 닿았다 — $($hop.Why)" } }
    if ($hop.Code -lt 300 -or $hop.Code -ge 400 -or $hop.Location -notmatch '/releases/download/([^/]+)/') {
        return @{ State = 'unmeasured'; Why = "최신 릴리스 주소가 $($hop.Code) 로 답했다" }
    }
    $tag = $Matches[1]
    $new = $tag -replace '^[vV]', ''
    $newV = $null
    $mineV = $null
    if (-not [version]::TryParse($new, [ref]$newV) -or -not [version]::TryParse($Mine, [ref]$mineV)) {
        return @{ State = 'unmeasured'; Why = "판 번호를 못 읽었다 (최신 $tag · 지금 $Mine)" }
    }
    if ($newV -le $mineV) { return @{ State = 'latest'; Ver = $new; Why = '' } }

    $url = "$site/download/$tag/Setup.exe"
    $a = Get-ReleaseHop $url $TimeoutSec
    if ($a.Code -eq 404) { return @{ State = 'no-asset'; Ver = $new; Why = "릴리스 $tag 에 Setup.exe 가 없다" } }
    if ($a.Code -lt 300 -or $a.Code -ge 400) {
        return @{ State = 'unmeasured'; Ver = $new; Why = "릴리스 $tag 의 Setup.exe 를 못 물었다 — $($a.Why)" }
    }

    $shaUrl = "$url.sha256"
    $s = Get-ReleaseHop $shaUrl $TimeoutSec
    if ($s.Code -eq 404) { $shaUrl = '' }
    elseif ($s.Code -lt 300 -or $s.Code -ge 400) {
        return @{ State = 'unmeasured'; Ver = $new; Why = "릴리스 $tag 의 Setup.exe.sha256 을 못 물었다 — $($s.Why)" }
    }

    return @{ State = 'newer'; Ver = $new; Why = ''
              Found = @{ Ver = $new; Url = $url; ShaUrl = $shaUrl; Rel = $tag } }
}

function Find-NewerRelease {
    <#
      `Measure-NewerRelease` 가 `newer` 면 그 받을 자리(`Found`)를, 아니면 `$null` 을 낸다 —
      못 물은 것과 최신인 것을 못 가르니 까닭이 드는 자리는 `Measure-NewerRelease` 를 부른다.
      이 꼴을 남기는 까닭: 자동 실행 몸통은 그것을 쓴 판의 것이고 이 조각은 가장 높은 판에서
      읽어, 낮은 판이 쓴 몸통이 높은 판의 조각을 부를 수 있다.
    #>
    param([string]$Repo, [string]$Mine, [int]$TimeoutSec = 8)

    $m = Measure-NewerRelease -Repo $Repo -Mine $Mine -TimeoutSec $TimeoutSec
    if ($m.State -eq 'newer') { return $m.Found }
    return $null
}

function Get-VerifiedSetup {
    <#
      `Measure-NewerRelease` 의 `Found` 가 준 자리에서 설치본을 받아 **릴리스에 오른 지문과 대조한다.**
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
