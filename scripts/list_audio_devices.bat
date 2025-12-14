@echo off
:: ============================================================================
:: GodLang - List Available Audio Devices
:: ============================================================================
:: Run this script to see available audio input devices on your system.
:: Use the device name in start_transcription.bat configuration.
:: ============================================================================

title List Audio Devices

echo.
echo ============================================================
echo   Available Audio Input Devices
echo ============================================================
echo.
echo Looking for audio devices...
echo.

ffmpeg -list_devices true -f dshow -i dummy 2>&1 | findstr /C:"audio"

echo.
echo ============================================================
echo   Copy the device name (without quotes) and update
echo   the AUDIO_DEVICE variable in start_transcription.bat
echo ============================================================
echo.
pause
