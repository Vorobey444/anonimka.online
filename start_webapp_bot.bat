@echo off
chcp 65001 >nul
title 🌆 Mini App Бот - Киберпанк

echo.
echo ╔╦╗╦╔╗╔╦  ╔═╗╔═╗╔═╗
echo ║║║║║║║║  ╠═╣╠═╝╠═╝
echo ╩ ╩╩╝╚╝╩  ╩ ╩╩  ╩  
echo.
echo 🎭 Анонимная доска объявлений
echo 🌐 Telegram Mini App режим
echo ════════════════════════════════════════════════════════════════

echo ⚙️  Проверка настроек...
echo.

REM Проверяем существование файла webapp_bot.py
if not exist "webapp_bot.py" (
    echo ❌ Файл webapp_bot.py не найден!
    echo 📁 Убедитесь, что вы в правильной папке
    pause
    exit /b 1
)

REM Проверяем папку webapp
if not exist "webapp\" (
    echo ❌ Папка webapp не найдена!
    echo 📁 Убедитесь, что веб-приложение создано
    pause
    exit /b 1
)

echo ✅ Файлы найдены
echo 🚀 Запуск Mini App бота...
echo.
echo ⚠️  ВАЖНО: Убедитесь что WEBAPP_URL настроен!
echo 💡 Для локального тестирования используйте ngrok:
echo    1. Запустите: start_server.bat
echo    2. В другом терминале: ngrok http 8000  
echo    3. Скопируйте HTTPS URL в webapp_bot.py
echo 🐍 Python: venv 3.10.11
echo.

"E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\webapp_bot.py"

echo.
echo 🛑 Mini App бот остановлен
pause