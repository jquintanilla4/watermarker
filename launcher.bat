@echo off
REM Windows wrapper to run the Bash launcher via Git Bash.
REM Requires Git for Windows (bash.exe). If not installed, instructions are shown.

setlocal
set "SCRIPT_DIR=%~dp0"

REM Prefer bash.exe from PATH if available
for %%I in (bash.exe) do set "BASH_EXE=%%~$PATH:I"

REM Fallback to common Git for Windows install path
if not exist "%BASH_EXE%" if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%BASH_EXE%" if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"

if exist "%BASH_EXE%" (
  "%BASH_EXE%" -lc "cd \"$(cygpath -u '%SCRIPT_DIR%')\" && ./launcher.sh"
  pause
  exit /b %ERRORLEVEL%
)

echo Could not find Git Bash (bash.exe) on PATH.
echo Please install Git for Windows from https://gitforwindows.org/ and try again.
echo Alternatively, run the app directly with Python:  py -3 video_watermarker.py
pause
exit /b 1

