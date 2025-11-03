@echo off@echo off

chcp 65001 >nulchcp 65001 >nul

color 0Atitle 🌟 Анонимная доска объявлений - Киберпанк бот

title 🚀 Neon Bot

echo.

clsecho ████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗ ███╗   ███╗

echo.echo ╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗████╗ ████║

echo ╔═══════════════════════════════════════════════════╗echo    ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║██╔████╔██║

echo ║        🔥 NEON BOT - WEBAPP SYNC 🔥              ║echo    ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║

echo ╚═══════════════════════════════════════════════════╝echo    ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║

echo.echo    ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝

echo.

REM Проверка .env файлаecho 🎭 АНОНИМНАЯ ДОСКА ОБЪЯВЛЕНИЙ 🎭

if exist .env (echo 🌆 Киберпанк стиль • Неоновые эффекты • Mini App

    echo ✅ Загрузка .env...echo.

    for /f "usebackq tokens=1,2 delims==" %%a in (.env) do (

        if "%%a"=="TELEGRAM_BOT_TOKEN" set TELEGRAM_BOT_TOKEN=%%b:menu

        if "%%a"=="VERCEL_API_URL" set VERCEL_API_URL=%%becho ════════════════════════════════════════════════════════════════════

    )echo 🚀 ВЫБЕРИТЕ РЕЖИМ ЗАПУСКА:

) else (echo ════════════════════════════════════════════════════════════════════

    echo ⚠️  Файл .env не найденecho.

)echo [1] 🤖 Классический бот (кнопки в Telegram)

echo [2] 🌐 Mini App бот (веб-приложение)  

REM Проверка токенаecho [3] � НОВЫЙ: Neon бот (синхронизация с WebApp)

if not defined TELEGRAM_BOT_TOKEN (echo [4] �🖥️  Запуск веб-сервера (для разработки)

    echo.echo [5] 🔧 Запуск всего (сервер + Mini App бот)

    echo ❌ ОШИБКА: Не найден TELEGRAM_BOT_TOKENecho [6] 📦 Установка зависимостей

    echo.echo [7] 🔍 Диагностика Python

    echo 📝 Создайте файл .env:echo [8] ❌ Выход

    echo.echo.

    echo    TELEGRAM_BOT_TOKEN=your_token_hereset /p choice="Введите номер (1-8): "

    echo    VERCEL_API_URL=https://anonimka.kz

    echo.if "%choice%"=="1" goto classic_bot

    pauseif "%choice%"=="2" goto webapp_bot  

    exit /b 1if "%choice%"=="3" goto neon_bot

)if "%choice%"=="4" goto web_server

if "%choice%"=="5" goto full_stack

REM URL по умолчаниюif "%choice%"=="6" goto install_deps

if not defined VERCEL_API_URL set VERCEL_API_URL=https://anonimka.kzif "%choice%"=="7" goto check_python

if "%choice%"=="8" goto exit

echo ✅ Token: %TELEGRAM_BOT_TOKEN:~0,10%...echo ❌ Неверный выбор! Попробуйте снова.

echo ✅ API: %VERCEL_API_URL%echo.

echo.goto menu

echo 🚀 Запуск...

echo.:install_deps

echo.

"E:\my project\app chat\.venv\Scripts\python.exe" bot_neon.pyecho 📦 Установка зависимостей...

echo ════════════════════════════════════════════════════════════════

echo.call install.bat

echo 🛑 Остановленgoto menu

pause

:check_python
echo.
echo 🔍 Диагностика Python...
echo ════════════════════════════════════════════════════════════════
call check_python.bat
goto menu

:classic_bot
echo.
echo 🤖 Запуск классического бота...
echo ════════════════════════════════════════════════════════════════════
"E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\bot.py"
goto end

:webapp_bot
echo.
echo 🌐 Запуск Mini App бота...
echo ════════════════════════════════════════════════════════════════════
echo ⚠️  Убедитесь, что WEBAPP_URL настроен в webapp_bot.py
echo 💡 Для локального тестирования используйте ngrok
echo.
"E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\webapp_bot.py"
goto end

:neon_bot
echo.
echo 🔥 Запуск Neon бота (с синхронизацией WebApp)...
echo ════════════════════════════════════════════════════════════════════
echo ✅ Работает с Neon PostgreSQL
echo 💬 Синхронизация чатов с WebApp
echo 🔔 Уведомления о новых сообщениях
echo 📱 Команды: /start, /my_chats
echo.
echo 🔑 Проверка переменных окружения...
if not defined TELEGRAM_BOT_TOKEN (
    echo ❌ TELEGRAM_BOT_TOKEN не установлен!
    echo 💡 Установите: set TELEGRAM_BOT_TOKEN=your_token
    pause
    goto menu
)
echo ✅ TELEGRAM_BOT_TOKEN: установлен
echo.
if not defined VERCEL_API_URL (
    echo ⚠️  VERCEL_API_URL не установлен, используем https://anonimka.kz
    set VERCEL_API_URL=https://anonimka.kz
)
echo ✅ VERCEL_API_URL: %VERCEL_API_URL%
echo.
echo 🚀 Запускаем бота...
echo.
"E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\bot_neon.py"
goto end

:web_server
echo.
echo 🖥️ Запуск веб-сервера...
echo ════════════════════════════════════════════════════════════════════
echo 🌐 Сервер будет доступен по адресу: http://localhost:8000
echo 💡 Для публичного доступа используйте: ngrok http 8000
echo.
"E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\server.py"
goto end

:full_stack
echo.
echo 🚀 Запуск полного стека (сервер + бот)...
echo ════════════════════════════════════════════════════════════════════
echo 🔄 Запускаем веб-сервер в фоновом режиме...
start "Web Server" "E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\server.py"
timeout /t 3 /nobreak >nul
echo 🤖 Запускаем Mini App бота...
echo.
"E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\webapp_bot.py"
goto end

:exit
echo.
echo 👋 До свидания! Увидимся в киберпространстве...
echo.
exit /b 0

:end
echo.
echo ════════════════════════════════════════════════════════════════════
echo 🛑 Бот остановлен
echo 💫 Спасибо за использование анонимной доски объявлений!
echo ════════════════════════════════════════════════════════════════════
echo.
pause
