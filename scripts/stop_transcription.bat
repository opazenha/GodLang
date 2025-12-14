@echo off
:: ============================================================================
:: GodLang Church Service Transcription - Stop Script
:: ============================================================================
:: Run this script to stop an active transcription session.
:: ============================================================================

title Stop GodLang Transcription

set SERVER_URL=http://localhost:7770
set LANGUAGE=zh

echo.
echo ============================================================
echo   Stopping GodLang Transcription Service
echo ============================================================
echo.

:: Stop the broadcast session
echo Sending stop request to server...
curl -s -X POST "%SERVER_URL%/api/broadcast/stop" -H "Content-Type: application/json" -d "{\"language\": \"%LANGUAGE%\"}"

echo.
echo.
echo Broadcast session stopped.
echo.
pause
