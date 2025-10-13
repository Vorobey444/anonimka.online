@echo off
chcp 65001 >nul
title 🚀 Быстрый запуск Mini App с ngrok

echo.
echo ╔═╗╦ ╦╦╔═╗╦╔═  ╔╦╗╔═╗╔═╗╔╦╗
echo ║═╬╗║ ║║║  ╠╩╗   ║ ║╣ ╚═╗ ║ 
echo ╚═╝╚╚═╝╩╚═╝╩ ╩   ╩ ╚═╝╚═╝ ╩ 
echo.
echo 🚀 Быстрый запуск Mini App для тестирования
echo ════════════════════════════════════════════════════════════════

if not exist "webapp\index.html" (
    echo ❌ Файлы webapp не найдены!
    pause
    exit /b 1
)

echo 📋 ПЛАН:
echo ────────────────────────────────────────────────────────────────
echo 1. 🌐 Запустить локальный веб-сервер
echo 2. 🔗 Создать HTTPS туннель через ngrok  
echo 3. ⚡ Обновить URL в боте автоматически
echo 4. 🤖 Перезапустить бота
echo 5. 🎮 Тестировать в Telegram
echo ────────────────────────────────────────────────────────────────
echo.

echo [1] 🌐 Запуск веб-сервера...
start "Web Server" cmd /c "cd webapp && python -m http.server 8000 && pause"
timeout /t 3 /nobreak >nul

echo [2] 🔍 Проверка ngrok...
ngrok version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ngrok не установлен!
    echo.
    echo 📥 УСТАНОВКА NGROK:
    echo ────────────────────────────────────────────────────────────────
    echo Вариант 1 - Chocolatey ^(рекомендуется^):
    echo    choco install ngrok
    echo.
    echo Вариант 2 - Ручная установка:
    echo    1. Идите на: https://ngrok.com/download
    echo    2. Скачайте ngrok.exe
    echo    3. Поместите в папку с PATH или в папку проекта
    echo.
    echo Вариант 3 - Winget:
    echo    winget install ngrok
    echo.
    set /p install="Установить ngrok через Chocolatey? (y/N): "
    if /i "%install%"=="y" goto install_ngrok
    if /i "%install%"=="yes" goto install_ngrok
    
    echo 💡 После установки ngrok запустите этот скрипт снова!
    pause
    exit /b 1
)

echo ✅ ngrok найден!

echo [3] 🔗 Создание HTTPS туннеля...
start "ngrok" cmd /c "ngrok http 8000"
echo ⏳ Ждём запуска ngrok...
timeout /t 5 /nobreak >nul

echo [4] 🔄 Получение ngrok URL...
for /l %%i in (1,1,10) do (
    curl -s http://localhost:4040/api/tunnels > ngrok_info.tmp 2>nul
    if %errorlevel% equ 0 goto parse_url
    echo    Попытка %%i/10...
    timeout /t 2 /nobreak >nul
)

echo ❌ Не удалось получить ngrok URL
echo 💡 Скопируйте HTTPS URL из окна ngrok вручную
goto manual_url

:parse_url
for /f "tokens=*" %%i in ('findstr "https.*ngrok" ngrok_info.tmp') do set "ngrok_line=%%i"
del ngrok_info.tmp 2>nul

if not defined ngrok_line (
    echo ❌ HTTPS URL не найден в ответе ngrok
    goto manual_url
)

rem Извлечение URL из JSON (упрощённое)
for /f "tokens=2 delims=:" %%a in ("%ngrok_line%") do (
    for /f "tokens=1 delims=," %%b in ("%%a") do (
        set "raw_url=%%b"
    )
)

rem Очистка кавычек и пробелов
set "ngrok_url=%raw_url:"=%"
set "ngrok_url=%ngrok_url: =%"
set "ngrok_url=%ngrok_url%/"

echo ✅ Найден ngrok URL: %ngrok_url%
goto update_bot

:manual_url
echo.
echo 📝 РУЧНОЙ ВВОД URL:
echo ────────────────────────────────────────────────────────────────
set /p ngrok_url="Введите HTTPS URL из ngrok (с / в конце): "

:update_bot
echo [5] ⚙️ Обновление URL в боте...
powershell -Command "(Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', 'WEBAPP_URL = \"%ngrok_url%\"' | Set-Content webapp_bot.py"

if %errorlevel% equ 0 (
    echo ✅ URL обновлён на: %ngrok_url%
) else (
    echo ❌ Ошибка обновления URL
    pause
    exit /b 1
)

echo [6] 🤖 Перезапуск бота...
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

start "Telegram Bot" cmd /c "title Telegram Bot && "E:\my project\app chat\.venv\Scripts\python.exe" webapp_bot.py && pause"
timeout /t 3 /nobreak >nul

echo.
echo ✅ ВСЁ ГОТОВО!
echo ════════════════════════════════════════════════════════════════
echo 🎮 ТЕСТИРОВАНИЕ:
echo ────────────────────────────────────────────────────────────────
echo 1. Откройте Telegram бота
echo 2. Отправьте /start
echo 3. Нажмите "🚀 Открыть приложение"  
echo 4. Должен загрузиться киберпанк интерфейс!
echo.
echo 🔄 РАЗРАБОТКА:
echo ────────────────────────────────────────────────────────────────
echo • Изменения в webapp/ видны мгновенно
echo • F5 в Mini App для обновления
echo • Этот ngrok URL работает до перезапуска
echo.
echo 📱 URL Mini App: %ngrok_url%
echo 🌐 Локальный сервер: http://localhost:8000
echo.
goto end

:install_ngrok
echo 📦 Установка ngrok через Chocolatey...
choco install ngrok -y
if %errorlevel% equ 0 (
    echo ✅ ngrok установлен!
    echo 🔄 Перезапуск скрипта...
    timeout /t 2 /nobreak >nul
    goto :eof
    call "%~f0"
) else (
    echo ❌ Ошибка установки. Попробуйте ручную установку.
    echo 🌐 https://ngrok.com/download
)

:end
echo ════════════════════════════════════════════════════════════════
echo 💡 ПОЛЕЗНЫЕ КОМАНДЫ:
echo    • Ctrl+C в терминалах - остановить процессы
echo    • .\test_mode.bat - полное меню разработки
echo    • .\quick_install.bat - установка зависимостей
echo ════════════════════════════════════════════════════════════════
pause