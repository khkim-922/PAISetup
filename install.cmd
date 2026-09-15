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

rem  No pause after this line - pressing [Close] in the setup window must close
rem  this console with it. Nothing may run between the call and exit /b, or
rem  %ERRORLEVEL% stops being PowerShell's.
rem
rem  The pause that used to live here carried two jobs. When the GUI cannot be
rem  created, install.ui.ps1 falls back to running in this console, and that
rem  branch needs the window to stay readable. That pause now lives in install.ui.ps1
rem  inside the fallback branch itself - the only branch with output to read here.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ui.ps1" %*
exit /b %ERRORLEVEL%
