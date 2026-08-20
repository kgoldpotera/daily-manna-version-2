@echo off
echo ===================================================
echo Setting up WhatsApp-Web.js Server
echo ===================================================
echo.

:: Clean up old OpenWA session files to avoid conflicts
if exist _IGNORE_session rmdir /s /q _IGNORE_session
if exist _IGNORE_CHURCH_BOT rmdir /s /q _IGNORE_CHURCH_BOT


echo Initializing Node project...
call npm init -y > nul

echo.
echo Installing whatsapp-web.js, qrcode-terminal, express, and axios...
call npm install whatsapp-web.js qrcode-terminal express axios

echo.
echo ===================================================
echo Starting the WhatsApp API Server...
echo ===================================================
node whatsapp_server.js

pause
