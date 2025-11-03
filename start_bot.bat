@echo off
chcp 65001 >nul 2>&1
color 0A
title Neon Bot

cls
echo.
echo ========================================================
echo          NEON BOT - WEBAPP SYNC
echo ========================================================
echo.

REM Check .env file
if exist .env (
    echo [+] Loading .env...
    for /f "usebackq tokens=1,2 delims==" %%a in (.env) do (
        if "%%a"=="TELEGRAM_BOT_TOKEN" set TELEGRAM_BOT_TOKEN=%%b
        if "%%a"=="VERCEL_API_URL" set VERCEL_API_URL=%%b
    )
) else (
    echo [!] File .env not found
)

REM Check token
if not defined TELEGRAM_BOT_TOKEN (
    echo.
    echo [X] ERROR: TELEGRAM_BOT_TOKEN not found
    echo.
    echo Create .env file:
    echo.
    echo    TELEGRAM_BOT_TOKEN=your_token_here
    echo    VERCEL_API_URL=https://anonimka.kz
    echo.
    pause
    exit /b 1
)

REM Default URL
if not defined VERCEL_API_URL set VERCEL_API_URL=https://anonimka.kz

echo [+] Token: %TELEGRAM_BOT_TOKEN:~0,10%...
echo [+] API: %VERCEL_API_URL%
echo.
echo Starting bot...
echo.

"E:\my project\app chat\.venv\Scripts\python.exe" bot_neon.py

echo.
echo Bot stopped
pause
