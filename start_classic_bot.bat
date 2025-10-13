@echo off
chcp 65001 >nul
title 🤖 Классический бот

echo.
echo ╔═╗╦  ╔═╗╔═╗╔═╗╦╔═╗  ╔╗ ╔═╗╔╦╗
echo ║  ║  ╠═╣╚═╗╚═╗║║     ╠╩╗║ ║ ║ 
echo ╚═╝╩═╝╩ ╩╚═╝╚═╝╩╚═╝  ╚═╝╚═╝ ╩ 
echo.
echo 🎭 Анонимная доска объявлений  
echo 🔘 Классический режим (кнопки)
echo ════════════════════════════════════════════════════════════════

echo ⚙️  Проверка настроек...

REM Проверяем существование файла bot.py
if not exist "bot.py" (
    echo ❌ Файл bot.py не найден!
    pause
    exit /b 1
)

echo ✅ Файлы найдены
echo 🚀 Запуск классического бота...
echo.
echo 💡 Этот бот использует обычные кнопки Telegram
echo 🎮 Функции: создание объявлений, просмотр, анонимный чат
echo 🐍 Python: venv 3.10.11
echo.

"E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\bot.py"

echo.
echo 🛑 Классический бот остановлен
pause