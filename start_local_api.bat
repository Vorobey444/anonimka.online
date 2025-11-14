@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   🧪 Локальный тестовый API сервер
echo ========================================
echo.

py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден!
    pause
    exit /b 1
)

echo ✅ Python найден
echo.
echo 🚀 Запуск локального сервера...
echo.
echo 💡 API endpoint: http://localhost:3001/api/world-chat
echo.
echo ⏹️  Для остановки нажмите Ctrl+C
echo.
echo ────────────────────────────────────────
echo.

py local_test_server.py

pause
