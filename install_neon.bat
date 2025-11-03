@echo off
chcp 65001 >nul
color 0E
title 📦 Установка Neon Bot

echo.
echo ╔═══════════════════════════════════════════════════╗
echo ║           📦 УСТАНОВКА NEON BOT 📦              ║
echo ╚═══════════════════════════════════════════════════╝
echo.

echo 🔧 Установка зависимостей...
echo.

"E:\my project\app chat\.venv\Scripts\python.exe" -m pip install python-telegram-bot aiohttp python-dotenv

echo.
echo ✅ Готово!
echo.
echo 📝 Следующий шаг: создайте файл .env
echo.
pause
