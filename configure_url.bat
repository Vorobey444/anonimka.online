@echo off
chcp 65001 >nul
title ⚙️ Настройка URL Mini App

echo.
echo ╦ ╦╦═╗╦    ╔═╗╔╦╗╦╔╦╗╔═╗╦═╗
echo ║ ║╠╦╝║    ║╣  ║║║ ║ ║ ║╠╦╝
echo ╚═╝╩╚═╩═╝  ╚═╝═╩╝╩ ╩ ╚═╝╩╚═
echo.
echo 🔧 Настройка URL для Telegram Mini App
echo ════════════════════════════════════════════

if not exist "webapp_bot.py" (
    echo ❌ Файл webapp_bot.py не найден!
    echo 💡 Запустите этот скрипт из папки с ботом
    pause
    exit /b 1
)

echo 📋 Текущий URL в webapp_bot.py:
echo ────────────────────────────────────
findstr "WEBAPP_URL" webapp_bot.py
echo ────────────────────────────────────
echo.

echo 🌐 ПРИМЕРЫ ПОПУЛЯРНЫХ URL:
echo.
echo [1] ngrok (для тестирования):
echo     https://abc123.ngrok.io/
echo.
echo [2] GitHub Pages:
echo     https://username.github.io/repo-name/
echo.
echo [3] Netlify:
echo     https://project-name.netlify.app/
echo.
echo [4] Vercel:  
echo     https://project-name.vercel.app/
echo.
echo [5] Локальный ngrok (автоопределение):
echo     Попытается найти активный ngrok туннель
echo.

set /p choice="Выберите опцию (1-5) или введите свой URL: "

if "%choice%"=="5" goto auto_ngrok
if "%choice%"=="1" goto manual_ngrok
if "%choice%"=="2" goto github_pages
if "%choice%"=="3" goto netlify  
if "%choice%"=="4" goto vercel

rem Если введён пользовательский URL
set "new_url=%choice%"
goto validate_url

:auto_ngrok
echo 🔍 Поиск активного ngrok туннеля...
curl -s http://localhost:4040/api/tunnels > ngrok_info.tmp 2>nul
if %errorlevel% neq 0 (
    echo ❌ ngrok не запущен на порту 4040
    echo 💡 Сначала запустите: ngrok http 8000
    pause
    exit /b 1
)

rem Простое извлечение HTTPS URL из JSON
for /f "tokens=*" %%i in ('findstr "https.*ngrok" ngrok_info.tmp') do set "ngrok_line=%%i"
del ngrok_info.tmp 2>nul

if not defined ngrok_line (
    echo ❌ HTTPS туннель не найден
    echo 💡 Убедитесь что запущен: ngrok http 8000
    pause
    exit /b 1
)

rem Извлекаем URL между кавычками
for /f "tokens=2 delims=:" %%a in ("%ngrok_line%") do (
    for /f "tokens=1 delims=," %%b in ("%%a") do (
        set "raw_url=%%b"
    )
)
set "new_url=%raw_url:"=%"
set "new_url=%new_url: =%"
set "new_url=%new_url%/"
goto validate_url

:manual_ngrok
set /p ngrok_id="Введите ID вашего ngrok (например abc123): "
set "new_url=https://%ngrok_id%.ngrok.io/"
goto validate_url

:github_pages  
set /p username="Ваш GitHub username: "
set /p repo="Название репозитория: "
set "new_url=https://%username%.github.io/%repo%/"
goto validate_url

:netlify
set /p site_name="Название сайта на Netlify: "
set "new_url=https://%site_name%.netlify.app/"
goto validate_url

:vercel
set /p project_name="Название проекта на Vercel: "  
set "new_url=https://%project_name%.vercel.app/"
goto validate_url

:validate_url
echo.
echo 🔍 Проверка URL: %new_url%
echo ────────────────────────────────────

rem Проверка что URL начинается с https://
echo %new_url% | findstr /i "^https://" >nul
if %errorlevel% neq 0 (
    echo ❌ URL должен начинаться с https://
    echo 💡 Mini App работают только по HTTPS
    pause
    exit /b 1
)

rem Проверка что URL заканчивается на /
echo %new_url% | findstr "/$" >nul
if %errorlevel% neq 0 (
    set "new_url=%new_url%/"
    echo ℹ️  Добавлен завершающий слэш: %new_url%
)

echo ✅ URL валидный: %new_url%
echo.

set /p confirm="Обновить webapp_bot.py этим URL? (y/N): "
if /i not "%confirm%"=="y" if /i not "%confirm%"=="yes" (
    echo ❌ Отменено пользователем
    pause
    exit /b 0
)

echo 💾 Обновление webapp_bot.py...

rem Создаем резервную копию
copy webapp_bot.py webapp_bot.py.backup >nul
echo ✅ Создана резервная копия: webapp_bot.py.backup

rem Обновляем URL
powershell -Command "(Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', 'WEBAPP_URL = \"%new_url%\"' | Set-Content webapp_bot.py"

if %errorlevel% neq 0 (
    echo ❌ Ошибка при обновлении файла
    copy webapp_bot.py.backup webapp_bot.py >nul
    echo 🔄 Восстановлен из резервной копии
    pause
    exit /b 1
)

echo ✅ Файл webapp_bot.py обновлён!
echo.
echo 📋 Новая конфигурация:
echo ────────────────────────────────────
findstr "WEBAPP_URL" webapp_bot.py
echo ────────────────────────────────────
echo.

echo 🚀 Готово! Теперь можете:
echo   1. Запустить: start_webapp_bot.bat  
echo   2. Открыть бота в Telegram
echo   3. Нажать /start
echo   4. Нажать "🚀 Открыть приложение"
echo.

set /p run_bot="Запустить бота прямо сейчас? (y/N): "
if /i "%run_bot%"=="y" goto run_bot
if /i "%run_bot%"=="yes" goto run_bot
goto end

:run_bot
echo 🤖 Запуск webapp_bot.py...
start "Telegram Mini App Bot" cmd /c "start_webapp_bot.bat"

:end
echo.
echo ════════════════════════════════════════════
echo 💡 Подсказки:
echo    • Для ngrok: сначала запустите ngrok http 8000
echo    • Для хостинга: загрузите папку webapp/  
echo    • Проблемы: check_python.bat
echo ════════════════════════════════════════════
pause