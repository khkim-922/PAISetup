# Review lane A — probe cap

## Part 1 findings

### 1. Critical — CONFIRMED: the new runner cannot execute PowerShell or CMD shims

Relevant code:

```powershell
# install.ps1:647-651
function Test-Runs([string]$Cmd, [string]$Arg) {
  if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) { return $false }
  $rc = Invoke-ProbeCapped $Cmd $Arg $ProbeCap
  if ($rc -eq -2) { $script:ProbeTimedOut["$Cmd $Arg"] = $ProbeCap; return $false }
  return ($rc -eq 0)
}
```

```powershell
# install.ps1:663-682
function Invoke-ProbeCapped([string]$File, [string]$Arg, [int]$CapSec) {
  $exe = $null
  try { $exe = (Get-Command $File -ErrorAction Stop).Source } catch { return -1 }
  $p = $null
  try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo $exe
    $psi.Arguments              = $Arg
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $p = [Diagnostics.Process]::Start($psi)
    ...
  } catch { return -1 }
}
```

The old invocation, `& $File @CmdArgs`, asked PowerShell to invoke a command. PowerShell understands executable files, `.cmd` shims, and `.ps1` scripts.

The replacement does something narrower:

1. `Get-Command` resolves the command.
2. `.Source` returns the path to the resolved file.
3. `Process.Start` receives that path with `UseShellExecute = $false`.
4. Windows attempts to create that file as a native process. It does not invoke PowerShell for `.ps1`, nor `cmd.exe /c` for `.cmd`.

The positive control on this machine produced:

```text
npm.ps1      ExternalScript  C:\Program Files\nodejs\npm.ps1
code.cmd     Application     ...\Microsoft VS Code\bin\code.cmd
gh.exe       Application     C:\Program Files\GitHub CLI\gh.exe
claude.ps1   ExternalScript  ...\npm\claude.ps1
codex.ps1    ExternalScript  ...\npm\codex.ps1
gemini.ps1   ExternalScript  ...\npm\gemini.ps1
copilot.ps1  ExternalScript  ...\npm\copilot.ps1
agy.exe      Application     ...\WinGet\Links\agy.exe
```

The source independently acknowledges the Claude case:

```powershell
# install.ps1:4517-4524
# PowerShell 에서 `claude`는 npm 이 만든 `claude.ps1`이 먼저 잡히지만, cmd 는
# 그 파일을 실행하지 못한다. 로그인 자리에는 cmd shim 을 정확히 집어 든다.
$cc = Get-Command claude.cmd -ErrorAction Stop
...
$login = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\cmd.exe') ...
```

For `.ps1` and `.cmd`, the observable result is not a timeout or a nonzero child exit. Process creation itself fails, normally with a `Win32Exception` such as error 193, “not a valid Win32 application.” The catch at `install.ps1:682` converts that exception to `-1`. `Test-Runs` then returns `$false`, and no entry is added to `$script:ProbeTimedOut`, because only `-2` is recorded.

Concrete failure scenario:

- Claude Code is correctly installed through npm.
- `Get-Command claude` returns `claude.ps1`.
- `Process.Start` cannot create that script as a native process.
- `Invoke-ProbeCapped` returns `-1`.
- Every affected caller concludes that Claude does not run.
- The later timeout explanation never mentions it.

Specific affected calls:

- `npm.ps1`: `install.ps1:2281` and `install.ps1:2330`.
- npm-installed `claude.ps1`, `codex.ps1`, `gemini.ps1`, and `copilot.ps1`: `install.ps1:2281`, `2283`, `2338`, `2537`, `4499`, `5924`, and `6483`, depending on the selected product.
- `code.cmd`: `install.ps1:3802`, `3858`, `4013`, and `6468`.
- `gh.exe`, `agy.exe`, `git.exe`, `node.exe`, and ordinary `python.exe` installations are directly executable and do not have this particular problem.

The silent state-changing flip is clearest for VS Code:

```powershell
# install.ps1:3802
if (Test-Runs $app.Cmd $app.Arg) {
  ...
}
...
# install.ps1:3848
$rc = Invoke-Logged 'winget' (@('install','--id',$app.Id) + $WG) $log
```

An installed `code.cmd` is reported false, so the installer invokes `winget install` over an existing VS Code installation. The post-install checks will also report false, making the eventual result loud, but the unwanted installation attempt has already occurred.

Most npm CLI paths become wrong-but-loud rather than silently reinstalling because both the target CLI shim and `npm.ps1` fail the same way: the installer reaches the “npm unavailable” branch.

The capped runner must dispatch according to command type. Native applications can be started directly; `.cmd`/`.bat` require `cmd.exe /d /s /c`; `.ps1` requires the intended PowerShell host. Argument quoting must be handled separately for each host.

---

### 2. High — CONFIRMED: an npm timeout is inverted into permission to skip upgrades

Relevant line:

```powershell
# install.ps1:2281
if ((Test-Runs $Cmd '--version') -and ($NoUpgrade -or -not (Test-Runs 'npm' '--version'))) {
  Write-Host "  $Label — 있음 ($(& $ReadVer))"
}
```

Concrete failure scenario:

- Claude CLI is installed but outdated.
- Upgrades are enabled, so `$NoUpgrade` is false.
- `claude --version` succeeds.
- `npm --version` starts but exceeds 20 seconds.
- `Test-Runs 'npm' '--version'` returns false.
- `-not $false` becomes true.
- The installer prints that Claude exists and exits this function without checking or applying an upgrade.
- A later probe can succeed, allowing the overall installation to finish green.

This is wrong and silent. The Boolean design does not prevent the inversion described in the design comment; it causes that inversion at this call site.

A timeout must not authorize an absence-dependent branch. `Test-Runs` may retain a Boolean return for compatibility, but callers using `-not` to authorize work need a way to reject a timed-out result.

---

### 3. High — CONFIRMED: timeout can authorize installation over an existing tool

Relevant lines:

```powershell
# install.ps1:2283
} elseif (Test-Runs $Cmd '--version') {
  ...
# install.ps1:2330
} elseif (Test-Runs 'npm' '--version') {
  ...
  $nrc = Invoke-Logged 'npm' @('install','-g',$Pkg) $nl
```

```powershell
# install.ps1:2360-2376
if (Test-Runs $Cmd '--version') {
  ...
  return
}
...
$rc = Invoke-Logged 'winget' (@('install','--id',$Id) + $WG) $wl
```

```powershell
# install.ps1:3802-3848
if (Test-Runs $app.Cmd $app.Arg) {
  ...
  continue
}
...
$rc = Invoke-Logged 'winget' (@('install','--id',$app.Id) + $WG) $log
```

Concrete scenarios:

- At `install.ps1:2283`, an installed npm CLI exceeds the cap on both target probes. If `npm --version` then succeeds at line 2330, the installer runs `npm install -g` over the installed CLI.
- At `install.ps1:2360`, an installed `agy` has one slow `--version`. The installer runs `winget install --id Google.AntigravityCLI`.
- At `install.ps1:3802`, an installed Python, Git, Node, GitHub CLI, or VS Code has one slow probe. The installer enters `winget install`, not the existing-tool or upgrade branch.

If the subsequent probe succeeds, these paths can print a green “installed” result. Absence was never established.

This is wrong and silent. A timed-out presence check should block installation and report an unmeasured state.

---

### 4. Medium — CONFIRMED: Python timeout silently skips requested pip packages

Relevant code:

```powershell
# install.ps1:5320-5338
$pipLine = Read-Directive $EnvFile 'pip-packages'
$pipPkgs = @(if ($pipLine) { ... })
if ($pipPkgs) {
  ...
  if (-not (Test-Runs 'python' '--version')) {
    Write-Host "  파이썬 패키지($pipNames) — 건너뛴다: 이 창에서 python 이 안 선다"
  } else {
    ...
    $prc = Invoke-Logged 'python' $pipArgs $pl
  }
}
```

Concrete failure scenario:

- `install.env` requests packages through `#pip-packages`.
- Python is installed.
- `python --version` exceeds 20 seconds once.
- The package installation is skipped.
- Nothing is added to `$Fails`.
- Final verification does not check those packages.
- A later Python probe succeeds, so the installer can exit 0 despite not installing the requested packages.

This is wrong and silent under the requested definition. The local skip line exists, but the final status can still be green.

---

### 5. Medium — CONFIRMED: Python timeout can suppress cleanup of stale managed state

Relevant code:

```powershell
# install.ps1:5388-5397
$toolHomesPython = Test-Runs 'python' '--version'
$toolHomesOn     = [bool]($personalAny -or $hostClaude -or $toolHomesPython)
if (-not $toolHomesOn) {
  Write-Host '  규범 · 룰 · 에이전트 · 스킬 — 건너뜀 ...'
...
} elseif (-not $toolHomesPython) {
  ...
  $Fails.Add(...)
} else {
  $th = Invoke-ToolHomes $toolHomesHand @('sync', ...)
}
```

Concrete failure scenario:

- A previous run created PAISetup-managed tool-home entries.
- The current selection has no personal section and does not select Claude.
- Python is installed, but `python --version` times out.
- `$toolHomesPython`, `$personalAny`, and `$hostClaude` are all false.
- `$toolHomesOn` becomes false.
- `tool-homes.py sync` is not called, including its removal of managed entries for disabled or unselected products.
- No failure is added.
- Stale managed configuration remains, and the run can finish green.

This is wrong and silent.

---

### 6. Medium — CONFIRMED: repeated probes can turn the nominal 180-second login wait into about 15 minutes

The helper performs one capped probe per call:

```powershell
# install.ps1:2536-2541
function Test-ClaudeLoggedIn {
  if (-not (Test-Runs 'claude' '--version')) { return $false }
  try {
    $said = (Get-Quiet 'claude' @('auth','status') | Out-String)
    return ($said -match '"loggedIn"\s*:\s*true')
  } catch { return $false }
}
```

The login loop is:

```powershell
# install.ps1:4525-4534
for ($waited = 0; $waited -lt 180; $waited += 5) {
  Start-Sleep -Seconds 5
  if (Test-ClaudeLoggedIn) { $claudeLoggedIn = $true; break }
  if ($login.HasExited) { break }
  ...
}
if (-not $claudeLoggedIn) { $claudeLoggedIn = Test-ClaudeLoggedIn }
```

Arithmetic:

- `$waited` takes 36 values: `0, 5, 10, ... 175`.
- Each iteration sleeps for five seconds: `36 × 5 = 180` seconds.
- Each iteration then calls `Test-ClaudeLoggedIn`.
- Each helper call can spend 20 seconds in `claude --version`: `36 × 20 = 720` seconds.
- After the loop, line 4534 can perform one more capped probe: another 20 seconds.
- Total: `180 + 720 + 20 = 920` seconds, about 15 minutes 20 seconds, excluding minor overhead.

There are additional pre-loop probes at lines 4499 and 4501:

```powershell
# install.ps1:4499-4502
if (-not (Test-Runs 'claude' '--version')) {
  ...
} elseif (Test-ClaudeLoggedIn) {
```

Those cannot both time out while still reaching the login loop. To enter the loop, the line-4499 probe must succeed, and the version probe inside the line-4501 helper must also succeed far enough to determine that the user is not logged in.

The roughly 15-minute case requires an intermittent condition:

1. The initial probes respond normally, allowing the login flow to start.
2. After the login child is launched, every polling `claude --version` call exceeds the cap.
3. The login child remains running, so `$login.HasExited` does not break the loop.

This is wrong but loud. The installer eventually reports that login did not complete, but the advertised maximum of 180 seconds is not an elapsed-time bound.

The program-install retry at `install.ps1:3857-3861` has the same smaller composition problem: eight 20-second timeouts plus seven or eight 750 ms sleeps can take approximately 166 seconds.

Retry loops should use an absolute deadline rather than incrementing a counter by only the explicit sleep duration.

---

### Cap value

Twenty seconds is defensible for one `--version`-class probe.

The supplied healthy observation is 0.05 seconds. A 20-second cap leaves roughly 400 times that duration while changing a 17-minute hang into a bounded wait. I found no evidence supporting a smaller exact threshold, and a false absence result is materially dangerous at several callers, so conservatism is appropriate.

I did not measure slow corporate machines and therefore cannot call 20 seconds empirically optimal. The primary problem is not the individual value; it is that:

- `$false` conflates absence, launch failure, nonzero exit, and timeout.
- Absence-dependent branches perform state changes.
- Retry loops multiply the cap into minutes.

## All 24 `Test-Runs` source locations

There are 24 live source lines containing calls but 25 individual invocations: line 2281 contains both the target-CLI probe and the npm probe.

| Call site | Concrete result when the probe times out | Verdict |
|---|---|---|
| `install.ps1:2281`, target CLI | Falls through to the second target probe. Repeated timeout can eventually authorize installation over an existing CLI. | Wrong-and-silent |
| `install.ps1:2281`, npm | With the target present and upgrades enabled, `-not $false` becomes true, so the installer prints “present” and skips the upgrade. | Wrong-and-silent |
| `install.ps1:2283` | Makes an existing target look absent. If npm answers, `npm install -g` runs over it. | Wrong-and-silent |
| `install.ps1:2330` | Reports that npm is unavailable and adds `$Fails`; installation is not attempted. | Wrong-but-loud |
| `install.ps1:2338` | Reports post-install failure and adds `$Fails`, even if installation succeeded. | Wrong-but-loud |
| `install.ps1:2360` | Authorizes `winget install` for an already-installed CLI. | Wrong-and-silent |
| `install.ps1:2380` | Reports that the newly installed CLI cannot be found and adds `$Fails`. | Wrong-but-loud |
| `install.ps1:2537` | `Test-ClaudeLoggedIn` returns false; callers can initiate login for an already logged-in user or eventually report login failure. | Wrong-but-loud |
| `install.ps1:2680` | Returns `Did = nopython`; the caller leaves TOML untouched, prints red, and adds `$Fails`. | Wrong-but-loud |
| `install.ps1:2896` | `Test-GhLoggedIn` returns false; the caller may initiate login for an already authenticated user or warn that login failed. | Wrong-but-loud |
| `install.ps1:3802` | Authorizes `winget install` for an existing program. A later success can be printed green. | Wrong-and-silent |
| `install.ps1:3858` | Treats post-install verification as failed. After retries it adds `$Fails`; eight caps can cost about 160 seconds. | Wrong-but-loud |
| `install.ps1:4013` | Skips all VS Code extension work, prints red, and adds `$Fails`. | Wrong-but-loud |
| `install.ps1:4499` | Skips Claude login as if the CLI were unavailable and prints a yellow warning. | Wrong-but-loud |
| `install.ps1:4735` | Leaves existing Codex configuration unmerged, prints red, and adds `$Fails`. | Wrong-but-loud |
| `install.ps1:5324` | Skips requested pip packages without adding a failure or verifying them later. | Wrong-and-silent |
| `install.ps1:5388` | With no personal section and no Claude, skips tool-home reconciliation and can leave stale managed state without failure. In other states, it reaches a red failure branch. | Wrong-and-silent in the stated state; otherwise Wrong-but-loud |
| `install.ps1:5456` | Skips Codex-hook installation, prints red, and adds `$Fails`. | Wrong-but-loud |
| `install.ps1:5528` | Skips Agy-hook installation, prints red, and adds `$Fails`. | Wrong-but-loud |
| `install.ps1:5648` | Skips configuration-repository work, prints red, and adds `$Fails`. | Wrong-but-loud |
| `install.ps1:5686` | Skips GitHub login and prints a yellow warning. | Wrong-but-loud |
| `install.ps1:5924` | Skips requested official-document skills and prints a warning and recovery commands. Final status need not fail, but the skipped work is visible. | Wrong-but-loud |
| `install.ps1:6468` | Marks VS Code and every selected extension `[X]`; `$redChecks` makes the final exit nonzero. | Wrong-but-loud |
| `install.ps1:6483` | Marks the selected CLI `[X]`; `$redChecks` makes the final exit nonzero. | Wrong-but-loud |
| `install.ps1:6699` | Marks Codex configuration verification unmeasured/failed; the check becomes `[X]` and exit is nonzero. | Wrong-but-loud |

No timeout-producing call site is unconditionally harmless. Some failure-side checks safely avoid mutation, but they still state the wrong cause and therefore fall under Wrong-but-loud.

## Part 2 — verification does not communicate the truth adequately

Relevant rendering:

```powershell
# install.ps1:6773-6775
foreach ($c in $checks) {
  if ($c.Ok) { Write-Host "  [O] $($c.Name)" -ForegroundColor Green }
  else       { Write-Host "  [X] $($c.Name)" -ForegroundColor Red }
}
```

The later qualification is:

```powershell
# install.ps1:6783-6789
if ($script:ProbeTimedOut.Count) {
  Write-Host ''
  Write-Host "  ! 위 [X] 가운데 $($script:ProbeTimedOut.Count) 자리는 **안 깔린 것이 아니라 못 쟀다** — 그 명령이 울타리를 넘겼다:" -ForegroundColor Yellow
  foreach ($k in $script:ProbeTimedOut.Keys) {
    Write-Host "      · $k — $($script:ProbeTimedOut[$k])초 안에 안 끝나 거뒀다" -ForegroundColor Yellow
  }
  Write-Host '      다시 깔지 말고 그 명령을 터미널에서 한 번 쳐 본다 ...' -ForegroundColor Yellow
}
```

This is not enough.

A red `[X] Python` or `[X] Claude Code CLI` states failure before the qualification appears. A person scanning the red list can reasonably reinstall the tool before reading or correctly correlating the later yellow block.

The correlation is also lossy:

- Checks use human labels such as `VS Code`, `Claude Code CLI`, or extension names.
- `$script:ProbeTimedOut` stores strings such as `code --version`.
- One timeout can affect several checks.

Concrete scenario at `install.ps1:6468-6479`:

```powershell
$hasCode = Test-Runs 'code' '--version'
...
$checks += @{ Name='VS Code'; Ok = $hasCode }
foreach ($x in $ExtPicks) {
  $checks += @{ Name = $x.Label; Ok = ($hasCode -and ...) }
}
```

One `code --version` timeout produces `[X] VS Code` and `[X]` for every selected extension. The yellow block later lists only `code --version`. It does not say that all those extension failures are consequences of one unmeasured prerequisite.

There is also a direct truth error. The timeout table is global for the entire run, but line 6785 says its entries are among the preceding `[X]` checks.

Concrete scenario:

1. `python --version` times out at `install.ps1:5324`.
2. Pip packages are skipped and the timeout is recorded.
3. A later Python probe at `install.ps1:6483` or `6699` succeeds.
4. Final checks contain no corresponding Python `[X]`.
5. The yellow block still says that one of the “above `[X]`” entries was unmeasured.

That statement is false.

The count is also misleading. `$script:ProbeTimedOut` is keyed by command and argument:

```powershell
# install.ps1:650
$script:ProbeTimedOut["$Cmd $Arg"] = $ProbeCap
```

Repeated timeouts of `python --version` overwrite the same entry. Therefore `.Count` is the number of unique command strings, not the number of timed-out call sites or `[X]` checks.

Timeout should be represented at the affected check itself:

```text
[?] Python — could not verify: `python --version` exceeded 20 seconds
    Installed or absent is unknown. Do not reinstall based on this result.
```

Use:

- `[O]` for confirmed success.
- `[X]` for confirmed failure.
- `[?]` for unmeasured state.

The check should carry structured state such as `Passed`, `Failed`, or `TimedOut`, plus the exact command and reason. Earlier operational timeouts that do not correspond to a final check should appear under a separate red “steps not completed” section naming the skipped step, for example:

```text
[?] Python packages — not attempted because `python --version` exceeded 20 seconds
```

Any `[?]` must keep the overall result non-successful. It must not be printed as `[X]`, and it must not permit an absence-dependent installation branch.

## Not checked or not measured

- I read all 24 live source locations listed above. Line 2281 contains two invocations, so I evaluated 25 distinct probe expressions.
- I traced `Test-ClaudeLoggedIn`, `Test-GhLoggedIn`, the installation/configuration branches, verification rendering, and the final exit condition at `install.ps1:7146-7151`.
- I inspected command resolution on this machine with `Get-Command`, but did not execute any of the commands.
- I did not run `install.ps1` or any fragment of it.
- I did not experimentally invoke `Process.Start` against the shims. The shim finding is based on the resolved command types and Windows process-creation semantics.
- I could not retrieve GitHub issue 26 from this environment. I used the issue context supplied in the request and the repository source.
- I did not benchmark the 20-second cap on slow corporate hardware. The cap assessment is qualitative.
- I did not exhaustively audit unrelated helpers except where necessary to establish the concrete outcomes above.

[cc-bg] ok · rc=0 · 82s · mode=read · agent=codex · model=gpt-5.6-sol · tokens in=1093504 out=16555 · web=1 · resume=codex:01a137f7-17fc-7e60-969a-f26570225e71
