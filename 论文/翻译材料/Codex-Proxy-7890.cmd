@echo off
setlocal

set "HTTP_PROXY=http://127.0.0.1:7890"
set "HTTPS_PROXY=http://127.0.0.1:7890"
set "ALL_PROXY=http://127.0.0.1:7890"
set "NO_PROXY=localhost,127.0.0.1,::1"

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "(Get-ChildItem 'C:\Program Files\WindowsApps\OpenAI.Codex_*_x64__2p2nqsd0c76g0\app\Codex.exe' | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName)"`) do set "CODEX_EXE=%%I"

if not defined CODEX_EXE (
  echo Failed to locate Codex.exe.
  exit /b 1
)

for %%I in ("%CODEX_EXE%") do set "CODEX_DIR=%%~dpI"
start "" /D "%CODEX_DIR%" "%CODEX_EXE%"
