@echo off
chcp 65001 >nul
echo.
echo =======================================
echo   🧪 Тестирование бота активности
echo =======================================
echo.

py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден!
    pause
    exit /b 1
)

if not exist .env (
    echo ❌ Файл .env не найден!
    pause
    exit /b 1
)

echo 📦 Установка зависимостей...
py -m pip install -q aiohttp python-dotenv

echo.
echo 🚀 Запуск теста...
echo.

py test_bot.py

echo.
pause
