@echo off
chcp 65001 >nul
title 📦 Установка зависимостей для Neon бота

echo.
echo ════════════════════════════════════════════════════════════════════
echo 📦 УСТАНОВКА ЗАВИСИМОСТЕЙ ДЛЯ NEON БОТА
echo ════════════════════════════════════════════════════════════════════
echo.

echo 🔍 Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8 или выше.
    pause
    exit /b 1
)

echo ✅ Python установлен
echo.

echo 📦 Устанавливаем python-telegram-bot...
pip install python-telegram-bot --upgrade

echo.
echo 📦 Устанавливаем aiohttp...
pip install aiohttp

echo.
echo 📦 Устанавливаем python-dotenv (для .env файлов)...
pip install python-dotenv

echo.
echo ════════════════════════════════════════════════════════════════════
echo ✅ ВСЕ ЗАВИСИМОСТИ УСТАНОВЛЕНЫ!
echo ════════════════════════════════════════════════════════════════════
echo.
echo 💡 Следующие шаги:
echo    1. Скопируйте .env.example в .env
echo    2. Заполните TELEGRAM_BOT_TOKEN в .env
echo    3. Запустите start_bot.bat и выберите опцию [3]
echo.
pause
