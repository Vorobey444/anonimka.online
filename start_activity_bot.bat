@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   🤖 Запуск бота активности для чата
echo ========================================
echo.

REM Проверка наличия Python
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Проверка .env файла
if not exist .env (
    echo ❌ Файл .env не найден!
    echo Создайте .env файл с переменными:
    echo   TELEGRAM_BOT_TOKEN=your_bot_token
    echo   VERCEL_API_URL=https://anonimka.kz
    pause
    exit /b 1
)

echo ✅ Файл .env найден
echo.

REM Установка зависимостей если нужно
echo 📦 Проверка зависимостей...
py -m pip install -q -r requirements.txt

echo.
echo 🚀 Запуск бота активности...
echo ⏹️  Для остановки нажмите Ctrl+C
echo.
echo ─────────────────────────────────────────
echo.

REM Запуск бота
py chat_activity_bot.py

pause
