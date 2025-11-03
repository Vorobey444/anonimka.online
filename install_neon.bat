@echo off
chcp 65001 >nul 2>&1
color 0E
title Install Neon Bot

echo.
echo ========================================================
echo          INSTALL NEON BOT
echo ========================================================
echo.
echo Installing dependencies...
echo.

"E:\my project\app chat\.venv\Scripts\python.exe" -m pip install python-telegram-bot aiohttp python-dotenv

echo.
echo Done!
echo.
echo Next step: create .env file
echo.
pause
