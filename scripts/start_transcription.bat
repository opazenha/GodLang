@echo off
setlocal EnableDelayedExpansion

:: ============================================================================
:: GodLang Church Service Transcription - Volunteer Startup Script
:: ============================================================================
:: Double-click this script to start transcription for the church service.
:: The script will:
::   1. Start the broadcast session
::   2. Begin capturing audio from the mixing board
::   3. Keep running until you close the window or press Ctrl+C
:: ============================================================================

title GodLang Transcription Service

:: Configuration - Edit these values as needed
set SERVER_URL=http://localhost:7770
set LANGUAGE=zh
set AUDIO_DEVICE=Mixing Board
set CHUNK_DURATION=10
set TEMP_DIR=C:\Temp\godlang\pending

echo.
echo ============================================================
echo   GodLang Church Service Transcription
echo ============================================================
echo.
echo Server: %SERVER_URL%
echo Language: %LANGUAGE%
echo Audio Device: %AUDIO_DEVICE%
echo.

:: Check if FFmpeg is available
where ffmpeg >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] FFmpeg is not installed or not in PATH.
    echo Please install FFmpeg and add it to your system PATH.
    echo.
    pause
    exit /b 1
)

:: Check if server is reachable
echo Checking server connection...
curl -s -o nul -w "%%{http_code}" %SERVER_URL%/api/health > temp_status.txt 2>nul
set /p HTTP_STATUS=<temp_status.txt
del temp_status.txt 2>nul

if "%HTTP_STATUS%" neq "200" (
    echo [ERROR] Cannot connect to server at %SERVER_URL%
    echo Please ensure the GodLang server is running.
    echo.
    pause
    exit /b 1
)
echo [OK] Server is reachable.
echo.

:: Create temp directory if it doesn't exist
if not exist "%TEMP_DIR%" (
    echo Creating temp directory: %TEMP_DIR%
    mkdir "%TEMP_DIR%"
)

:: Start the broadcast session
echo Starting broadcast session...
curl -s -X POST "%SERVER_URL%/api/broadcast/start" -H "Content-Type: application/json" -d "{\"language\": \"%LANGUAGE%\"}" > broadcast_response.txt 2>nul

:: Check if broadcast started successfully
findstr /C:"\"success\": true" broadcast_response.txt >nul 2>&1
if %ERRORLEVEL% neq 0 (
    findstr /C:"\"success\":true" broadcast_response.txt >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to start broadcast session.
        type broadcast_response.txt
        del broadcast_response.txt 2>nul
        echo.
        pause
        exit /b 1
    )
)
del broadcast_response.txt 2>nul

echo [OK] Broadcast session started.
echo.
echo ============================================================
echo   TRANSCRIPTION IS NOW ACTIVE
echo ============================================================
echo.
echo Audio is being captured from: %AUDIO_DEVICE%
echo Translations are being streamed to connected clients.
echo.
echo Clients can connect to:
echo   %SERVER_URL%/api/sse/broadcast/%LANGUAGE%
echo.
echo ============================================================
echo   Press Ctrl+C or close this window to stop transcription
echo ============================================================
echo.

:: Start FFmpeg audio capture
:: This captures audio and saves it in chunks to the pending directory
ffmpeg -f dshow -i "audio=%AUDIO_DEVICE%" ^
    -ar 16000 -ac 1 -c:a flac ^
    -f segment -segment_time %CHUNK_DURATION% ^
    -strftime 1 -y ^
    "%TEMP_DIR%\%%Y%%m%%d_%%H%%M%%S.flac"

:: When FFmpeg exits (user closed window or pressed Ctrl+C), stop the broadcast
echo.
echo Stopping broadcast session...
curl -s -X POST "%SERVER_URL%/api/broadcast/stop" -H "Content-Type: application/json" -d "{\"language\": \"%LANGUAGE%\"}" >nul 2>&1

echo.
echo ============================================================
echo   Transcription service stopped.
echo ============================================================
echo.
pause
