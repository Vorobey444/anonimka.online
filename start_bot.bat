@echo off
chcp 65001 >nul
title 🌟 Анонимная доска объявлений - Киберпанк бот

echo.
echo ████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗ ███╗   ███╗
echo ╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗████╗ ████║
echo    ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║██╔████╔██║
echo    ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║
echo    ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║
echo    ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝
echo.
echo 🎭 АНОНИМНАЯ ДОСКА ОБЪЯВЛЕНИЙ 🎭
echo 🌆 Киберпанк стиль • Неоновые эффекты • Mini App
echo.

:menu
echo ════════════════════════════════════════════════════════════════════
echo 🚀 ВЫБЕРИТЕ РЕЖИМ ЗАПУСКА:
echo ════════════════════════════════════════════════════════════════════
echo.
echo [1] 🤖 Классический бот (кнопки в Telegram)
echo [2] 🌐 Mini App бот (веб-приложение)  
echo [3] 🖥️  Запуск веб-сервера (для разработки)
echo [4] 🔧 Запуск всего (сервер + Mini App бот)
echo [5] 📦 Установка зависимостей
echo [6] 🔍 Диагностика Python
echo [7] ❌ Выход
echo.
set /p choice="Введите номер (1-7): "

if "%choice%"=="1" goto classic_bot
if "%choice%"=="2" goto webapp_bot  
if "%choice%"=="3" goto web_server
if "%choice%"=="4" goto full_stack
if "%choice%"=="5" goto install_deps
if "%choice%"=="6" goto check_python
if "%choice%"=="7" goto exit
echo ❌ Неверный выбор! Попробуйте снова.
echo.
goto menu

:install_deps
echo.
echo 📦 Установка зависимостей...
echo ════════════════════════════════════════════════════════════════
call install.bat
goto menu

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
