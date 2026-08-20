@echo off
echo ===================================================
echo Setting up Custom OpenWA Server
echo ===================================================
echo.

:: Clean up old session files if they exist
if exist _IGNORE_session rmdir /s /q _IGNORE_session
if exist CHURCH_BOT rmdir /s /q CHURCH_BOT

echo Initializing Node project...
call npm init -y > nul

echo.
echo Installing OpenWA, Express, and Axios...
call npm install @open-wa/wa-automate express axios

echo.
echo ===================================================
echo Starting the Custom OpenWA API Server...
echo ===================================================
node openwa_server.js

pause
