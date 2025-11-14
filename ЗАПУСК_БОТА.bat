@echo off
chcp 65001 >nul
cls
echo.
echo ========================================
echo   🎉 ВСЁ ГОТОВО К ЗАПУСКУ!
echo ========================================
echo.
echo ✅ API задеплоен на https://anonimka.kz
echo ✅ База данных готова
echo ✅ Бот готов к запуску
echo.
echo ═══════════════════════════════════════
echo   ВЫБЕРИ ВЕРСИЮ БОТА:
echo ═══════════════════════════════════════
echo.
echo   [1] Базовый бот (chat_activity_bot.py)
echo       - 7 персонажей (включая кринжовых)
echo       - Случайные сообщения
echo       - Простой режим
echo.
echo   [2] Умный бот (chat_activity_bot_advanced.py)
echo       - Контекстные диалоги
echo       - Память разговоров
echo       - AI-like ответы
echo.
echo   [3] Тест API (проверка работы)
echo.
echo   [0] Выход
echo.
echo ═══════════════════════════════════════
echo.
set /p choice="Выбери опцию (1-3): "

if "%choice%"=="1" goto basic
if "%choice%"=="2" goto smart
if "%choice%"=="3" goto test
if "%choice%"=="0" goto end

echo ❌ Неверный выбор!
pause
goto end

:basic
echo.
echo 🤖 Запускаю базового бота...
echo.
start_activity_bot.bat
goto end

:smart
echo.
echo 🧠 Запускаю умного бота...
echo.
start_smart_bot.bat
goto end

:test
echo.
echo 🧪 Запускаю тест API...
echo.
test_bot.bat
goto end

:end
