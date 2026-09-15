@echo off
rem  Claude Code setup - entry point. Double-click this file.
rem
rem  This wrapper only launches install.ui.ps1 (the screen), which hands the work
rem  to install.ps1 (the engine). Keep logic out of here.
rem
rem  *** ASCII ONLY - DO NOT PUT KOREAN TEXT IN THIS FILE. ***
rem  cmd.exe reads a batch file in the console OEM codepage (cp949 in Korea), but
rem  the file is UTF-8. Korean bytes are then misread, "rem" stops being seen as
rem  rem, and the garbled words are executed as commands. Measured on a company
rem  VDI 2026-09-09: every comment line and the powershell line broke apart.
rem  The reasoning that used to live here is in install.ps1.
rem
rem  -ExecutionPolicy Bypass is required: a downloaded .ps1 will not run without it.
setlocal
cd /d "%~dp0"

where powershell >nul 2>&1
if errorlevel 1 (
  echo PowerShell not found. This installer needs Windows PowerShell.
  pause
  exit /b 1
)

rem  "start /min", then leave at once - the black window must not sit behind the
rem  setup screen for the whole install.
rem
rem  *** The window state is stamped HERE, at creation, on purpose. ***
rem  Hiding it later from the script does not work on Windows 11, where the
rem  console is normally hosted by Windows Terminal: GetConsoleWindow() then
rem  returns a helper window of class PseudoConsoleWindow, not the real one, and
rem  ShowWindow(SW_HIDE) on it returns TRUE and changes nothing - a green that is
rem  a lie. A state given at creation time is honoured by every host.
rem  Measured 2026-09-15 on Windows 11 26100:
rem    plain                            real window visible
rem    start /min                       minimized, taskbar button only
rem    powershell -WindowStyle Hidden   minimized only - the name does not hold
rem
rem  No "start /wait": cmd must return now, so this console closes instead of
rem  waiting out the install. That drops PowerShell's exit code - a double-click
rem  has no caller to read it, and nothing in this repo calls this file. The old
rem  rule about keeping %ERRORLEVEL% intact guarded a value that no longer exists.
rem
rem  No pause either. When the GUI cannot be created, install.ui.ps1 falls back to
rem  running in this console - and because that window is now minimized, that
rem  branch pulls itself to the front before it speaks. The pause it needs lives
rem  there too, inside the branch, not here.
start "" /min powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ui.ps1" %*
exit /b 0
