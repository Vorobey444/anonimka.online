@echo off
chcp 65001 >nul
title 🌐 Веб-сервер для Mini App

echo.
echo ╦ ╦╔═╗╔╗ ╔═╗╔═╗╦═╗╦  ╦╔═╗╦═╗
echo ║║║║╣ ╠╩╗╚═╗║╣ ╠╦╝╚╗╔╝║╣ ╠╦╝
echo ╚╩╝╚═╝╚═╝╚═╝╚═╝╩╚═ ╚╝ ╚═╝╩╚═
echo.
echo 🚀 Запуск HTTP сервера для Telegram Mini App
echo ════════════════════════════════════════════════════════════════

echo 📁 Папка: webapp/
echo 🌐 URL: http://localhost:8000
echo 🔗 Для публичного доступа: ngrok http 8000
echo.
echo ⚠️  Для работы с Telegram нужен HTTPS!
echo 💡 Используйте ngrok или разместите на хостинге
echo 🐍 Python: venv 3.10.11
echo.

"E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\server.py"

echo.
echo 🛑 Сервер остановлен
pause