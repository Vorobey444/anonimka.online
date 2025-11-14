@echo off
echo ========================================================
echo          ADMIN MODERATION BOT
echo ========================================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

echo [+] Запуск админ-бота для модерации...
echo.

python admin_moderation_bot.py

pause
