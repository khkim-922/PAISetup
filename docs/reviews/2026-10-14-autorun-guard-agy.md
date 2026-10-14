# Review of PAISetup Autorun Guard and Verification Output

## Part 1: Autorun Guard Soundness

### 1. False "stalled" verdicts (CONFIRMED)
**Location:** `install.ps1:6172` (`return (($cpuAfter - $cpuBefore) -lt 0.05 -and $sizeAfter -eq $sizeBefore)`)
**Scenario:** A legitimate console-launched installer reaches a slow, silent step that delegates work to a child process (e.g., `git pull` or `npm install` over a slow network). Because it was launched from the console, there is no GUI wrapper, and thus no `claude-setup-<PID>.out` file is created. The script handles this by falling back to `$sizeBefore = -1` and `$sizeAfter = -1`, making `$sizeAfter -eq $sizeBefore` evaluate to `$true`. Meanwhile, the parent `powershell.exe` process running the script is synchronously blocked waiting for the child process to finish. The `.CPU` property tracks only the parent process's CPU time, not its children. Therefore, the parent's CPU usage over the 20-second measurement window is exactly 0.
**Outcome:** If this happens after the installer has been running for 15 minutes, the autorun script evaluates the working installation as stalled and kills it. This directly creates the half-installed state the guard was meant to prevent.

### 2. False "live" verdicts (CONFIRMED)
**Location:** `install.ps1:6167` (`$p.Refresh()`) and `install.ps1:6173-6175` (`catch { return $false }`)
**Scenario:** The autorun script queries a process in `$otherEngines`. Exactly during the 20-second `Start-Sleep` window, that process legitimately finishes its work and exits. When `$p.Refresh()` is called, it throws an `InvalidOperationException` because the process no longer exists. The `catch` block catches this exception and returns `$false` (indicating the process is "live").
**Outcome:** The dead process is added to the `$live` array. The script logs "일하고 있는 것이 1 개 있어 겹치지 않게 물러납니다" and exits (`exit 0`). The autorun backs out unnecessarily, delaying its work until the next logon, because it treated a naturally dying process as an active one.

### 3. The output-file heuristic (CONFIRMED)
**Location:** `install.ps1:6161` (`$outFile = Join-Path $env:TEMP ("claude-setup-{0}.out" -f $Proc.ParentProcessId)`)
**Scenario:** If a user runs `install.ps1` from a standard command prompt, and the script determines it needs admin rights, it launches an elevated instance of itself via `Start-Process -Verb RunAs`. The parent of this new elevated `powershell.exe` will be `svchost.exe` (the AppInfo service), not the process that originally launched it. The file `claude-setup-<svchost_PID>.out` will not exist. Additionally, due to PID recycling, a new console install's parent could reuse the PID of an old GUI wrapper, matching a stale `.out` file whose size never changes.
**Outcome:** The script treats the elevated GUI installer as a console installer (`-1 == -1`), or measures a stale file that doesn't grow. If the installer then waits on a child process for 20 seconds, it will be falsely killed based on the CPU check (same outcome as finding #1).

### 4. The reaping sequence (CONFIRMED)
**Location:** `install.ps1:6206-6210` (The `try/catch` block around `taskkill` and `Stop-Process`)
**Scenario:** The autorun task (running as a standard user) attempts to reap a stalled installer that was run elevated (as Administrator). `taskkill.exe` is an external executable, so a non-zero exit code (e.g., Access Denied) does not throw a PowerShell terminating exception. `Stop-Process` explicitly uses `-ErrorAction SilentlyContinue`, which suppresses exceptions.
**Outcome:** Both kill commands silently fail. The `catch` block is bypassed, and the script logs `"PID ... 을 거뒀다"` (Successfully reaped). Three seconds later, the script correctly detects the process is still alive and backs out, but the log file contains a lie, severely hampering any future troubleshooting.

### 5. `$orphanMin = 15` (PLAUSIBLE)
**Location:** `install.ps1:6151` (`$orphanMin = 15`)
**Scenario:** The installer includes prompts for human interaction (e.g., asking "kill orphan? [Y/N]"). If a user starts a console installation, encounters a prompt, and leaves their desk for an extended period, the process becomes older than 15 minutes. If a scheduled autorun triggers, it will see 0 CPU usage and no file output (since it's a console run waiting for input).
**Outcome:** The autorun reaps the installer while the user is simply away from their desk, abruptly terminating their session.

### 6. Error Handling
Covered in finding #2 (False "live" verdicts).

---

## Part 2: Verification Output Logic

### Verification Output Misdirection (CONFIRMED)
**Location:** `install.ps1:6773-6776` (`[X] $($c.Name)`) and `install.ps1:6800-6808` (`검증에서 $redChecks 칸이 빨갛다`)
**Scenario:** When a probe times out, it is appended to the `$checks` array with `.Ok = $false`. The display loop blindly prints this as a bright red `[X] <tool name>`. A yellow disclaimer is printed below explaining that some `[X]` marks mean "timed out," not "missing." However, immediately after this nuance, the script prints a bold red summary: `"검증에서 N 칸이 빨갛다 — 바로 위 [X] 가 그것이다"` (N checks are red — the [X] above is the cause).
**Outcome:** A person reading this will almost certainly go reinstall the tool. The visual hierarchy of a red `[X]` paired with a final red summary explicitly blaming that `[X]` for the overall failure completely overrides the sandwiched yellow text.
**Concrete Fix:** The item itself must not be printed as a failure. The display loop must check if the item timed out (e.g., checking if its name exists in `$script:ProbeTimedOut`). If it did, it should print something like `[?] <tool name> (측정 시간 초과)` in yellow, instead of `[X]` in red. Furthermore, timed-out checks must not be counted in `$redChecks`, so the final summary does not declare the run a failure because of them.

---

## Not Checked / Could Not Measure
- **Live Process States:** I did not run the installer or execute `Test-EngineStalled` against live processes to measure exact `.CPU` property behaviors under different .NET/PowerShell execution contexts.
- **WMI Permissions:** I could not measure whether the WMI query (`Get-CimInstance Win32_Process`) executed by a standard-user autorun task actually returns the `CommandLine` property for elevated processes. If it doesn't, elevated processes might not appear in `$otherEngines` at all, rendering the guard partially blind.
