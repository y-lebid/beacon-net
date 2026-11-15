@echo off
setlocal
title Beacon Network Monitor

if exist "%~dp0beacon-windows-x64.exe" (
    "%~dp0beacon-windows-x64.exe" %*
    goto :eof
)

if exist "%~dp0beacon-windows-arm64.exe" (
    "%~dp0beacon-windows-arm64.exe" %*
    goto :eof
)

where beacon >nul 2>nul
if %errorlevel%==0 (
    beacon %*
    goto :eof
)

echo [ERROR] Beacon executable not found in current folder or PATH.
pause