@echo off
chcp 65001 >nul
title ⚡ Быстрая установка

echo.
echo ⚡ БЫСТРАЯ УСТАНОВКА ЗАВИСИМОСТЕЙ
echo ════════════════════════════════════════════════════════════════
echo 🎯 Используем найденное виртуальное окружение Python 3.10.11
echo.

echo 📦 Установка python-telegram-bot через venv...
"E:\my project\app chat\.venv\Scripts\python.exe" -m pip install python-telegram-bot

if %errorlevel% equ 0 (
    echo ✅ Успешно установлено!
    echo.
    echo 🚀 Теперь можно запускать:
    echo    • start_classic_bot.bat - классический бот
    echo    • start_webapp_bot.bat - Mini App бот  
    echo    • start_server.bat - веб-сервер
    echo.
) else (
    echo ❌ Ошибка установки!
    echo 💡 Попробуйте:
    echo    py -m pip install python-telegram-bot
    echo.
)

pause