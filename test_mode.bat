@echo off
chcp 65001 >nul
title 🔧 Режим разработки Mini App

echo.
echo ╔╦╗╔═╗╔╗╔  ╔═╗╔═╗╔═╗  ╔╦╗╔═╗╔═╗╔╦╗  ╔╦╗╔═╗╔╦╗╔═╗
echo ║║║║║║║║║  ╠═╣╠═╝╠═╝   ║ ║╣ ╚═╗ ║   ║║║║ ║ ║║║╣ 
echo ╩ ╩╩ ╩╝╚╝  ╩ ╩╩  ╩     ╩ ╚═╝╚═╝ ╩   ╩ ╩╚═╝═╩╝╚═╝
echo.
echo 🔧 Режим разработки для Telegram Mini App
echo ════════════════════════════════════════════════════════════════

if not exist "webapp\index.html" (
    echo ❌ Папка webapp не найдена!
    echo 💡 Запустите из корня проекта
    pause
    exit /b 1
)

echo 📋 РЕЖИМЫ РАБОТЫ:
echo ────────────────────────────────────────────────────────────────
echo [0] ⚡ БЫСТРЫЙ СТАРТ (рекомендуется)
echo     • Автоматический запуск всего за 30 секунд
echo     • Локальный сервер + ngrok + обновление бота  
echo     • Готово для тестирования в Telegram
echo.
echo [1] 🚀 Ручное тестирование (локальный сервер)
echo     • Запустить локальный веб-сервер на порту 8000
echo     • Использовать ngrok для HTTPS туннеля
echo     • Мгновенное обновление изменений
echo.
echo [2] 📤 Деплой изменений на GitHub Pages
echo     • Загрузить изменения в ветку gh-pages
echo     • Обновить публичный сайт anonimka.online
echo     • Время обновления: 2-3 минуты
echo.
echo [3] 🎨 Редактор интерфейса
echo     • Открыть файлы для редактирования
echo     • index.html - структура
echo     • style.css - дизайн
echo     • app.js - функциональность
echo.
echo [4] 🤖 Управление ботом
echo     • Запуск/остановка бота
echo     • Переключение URL для тестирования
echo     • Просмотр логов
echo.

set /p mode="Выберите режим (0-4): "

if "%mode%"=="0" goto quick_start
if "%mode%"=="1" goto local_dev
if "%mode%"=="2" goto deploy_changes  
if "%mode%"=="3" goto edit_files
if "%mode%"=="4" goto manage_bot
goto invalid_choice

:quick_start
echo.
echo ⚡ БЫСТРЫЙ СТАРТ
echo ════════════════════════════════════════════════════════════════
echo 🚀 Запуск автоматической настройки...
call quick_test.bat
goto end

:local_dev
echo.
echo 🚀 ЛОКАЛЬНАЯ РАЗРАБОТКА
echo ════════════════════════════════════════════════════════════════
echo.
echo 📋 Запускаем локальный сервер...
start "Web Server" cmd /c "cd /d webapp && python -m http.server 8000"
timeout /t 2 /nobreak >nul

echo 🌐 Проверяем ngrok...
ngrok version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ngrok не найден!
    echo 📥 Установите: https://ngrok.com/download
    echo 💡 Или: choco install ngrok
    pause
    exit /b 1
)

echo 🔗 Создаём HTTPS туннель...
echo ⚠️  ВНИМАНИЕ: Скопируйте HTTPS URL и обновите webapp_bot.py
echo.
start "ngrok" cmd /c "ngrok http 8000"
timeout /t 3 /nobreak >nul

echo 📝 Автоматическое обновление URL...
set /p update_bot="Обновить URL в боте автоматически? (y/N): "
if /i "%update_bot%"=="y" goto auto_update_url
if /i "%update_bot%"=="yes" goto auto_update_url

echo.
echo 💡 ИНСТРУКЦИЯ:
echo ────────────────────────────────────────────────────────────────
echo 1. Скопируйте HTTPS URL из окна ngrok
echo 2. Откройте webapp_bot.py
echo 3. Замените WEBAPP_URL на ваш ngrok URL
echo 4. Сохраните и перезапустите бота
echo 5. Изменения в webapp/ будут видны мгновенно!
goto end

:auto_update_url
timeout /t 5 /nobreak >nul
curl -s http://localhost:4040/api/tunnels > ngrok_info.tmp 2>nul
if %errorlevel% neq 0 (
    echo ❌ Не удалось получить URL ngrok
    goto end
)

for /f "tokens=*" %%i in ('findstr "https.*ngrok" ngrok_info.tmp') do set "ngrok_line=%%i"
del ngrok_info.tmp 2>nul

if defined ngrok_line (
    echo ✅ Найден ngrok URL, обновляем бота...
    powershell -Command "& {$line='%ngrok_line%'; $url=($line -split '\"')[3]; (Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', \"WEBAPP_URL = \`\"$url/\`\"\" | Set-Content webapp_bot.py; Write-Host \"URL обновлен на: $url/\"}"
) else (
    echo ❌ Не удалось извлечь URL
)
goto end

:deploy_changes
echo.
echo 📤 ДЕПЛОЙ НА GITHUB PAGES  
echo ════════════════════════════════════════════════════════════════
echo.
echo 🔄 Переключаемся на ветку gh-pages...
git stash >nul 2>&1
git checkout gh-pages >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ошибка переключения на gh-pages
    pause
    exit /b 1
)

echo 📋 Копируем новые файлы из main...
git checkout main -- webapp/ >nul 2>&1
move webapp\* . >nul 2>&1
rmdir webapp >nul 2>&1

echo 💾 Коммитим изменения...
git add . >nul 2>&1
set /p commit_msg="Введите описание изменений: "
if "%commit_msg%"=="" set commit_msg="Update Mini App interface"
git commit -m "%commit_msg%" >nul 2>&1

echo 🚀 Загружаем на GitHub...
git push >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Изменения загружены!
    echo 🕐 Сайт обновится через 2-3 минуты
    echo 🌐 URL: https://vorobey444.github.io/anonimka.online/
) else (
    echo ❌ Ошибка загрузки
)

echo 🔄 Возвращаемся к main...
git checkout main >nul 2>&1  
git stash pop >nul 2>&1
goto end

:edit_files
echo.
echo 🎨 РЕДАКТИРОВАНИЕ ФАЙЛОВ
echo ════════════════════════════════════════════════════════════════
echo.
echo [1] 📝 index.html - структура интерфейса
echo [2] 🎨 style.css - дизайн и анимации  
echo [3] ⚡ app.js - функциональность JavaScript
echo [4] 🤖 webapp_bot.py - логика бота
echo [5] 📁 Открыть папку webapp в проводнике
echo.

set /p edit_choice="Что редактировать (1-5): "

if "%edit_choice%"=="1" start notepad "webapp\index.html"
if "%edit_choice%"=="2" start notepad "webapp\style.css"  
if "%edit_choice%"=="3" start notepad "webapp\app.js"
if "%edit_choice%"=="4" start notepad "webapp_bot.py"
if "%edit_choice%"=="5" start explorer "webapp\"

echo.
echo 💡 ПОСЛЕ РЕДАКТИРОВАНИЯ:
echo ────────────────────────────────────────────────────────────────  
echo • Для локального тестирования: используйте режим 1
echo • Для публикации: используйте режим 2
echo • Сохраните файлы перед деплоем
goto end

:manage_bot
echo.
echo 🤖 УПРАВЛЕНИЕ БОТОМ
echo ════════════════════════════════════════════════════════════════
echo.
echo [1] ▶️  Запустить webapp_bot.py
echo [2] ⏹️  Остановить все Python процессы
echo [3] 🔄 Перезапустить бота
echo [4] 📊 Показать логи бота
echo [5] ⚙️  Сменить URL (локальный/продакшен)
echo.

set /p bot_choice="Выберите действие (1-5): "

if "%bot_choice%"=="1" goto start_bot
if "%bot_choice%"=="2" goto stop_bot
if "%bot_choice%"=="3" goto restart_bot  
if "%bot_choice%"=="4" goto show_logs
if "%bot_choice%"=="5" goto change_url
goto end

:start_bot
echo 🚀 Запуск бота...
start "Telegram Bot" cmd /c "start_webapp_bot.bat"
goto end

:stop_bot
echo ⏹️ Остановка Python процессов...
taskkill /f /im python.exe >nul 2>&1
echo ✅ Готово
goto end

:restart_bot
echo 🔄 Перезапуск...
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
start "Telegram Bot" cmd /c "start_webapp_bot.bat"
echo ✅ Бот перезапущен
goto end

:show_logs
echo 📊 Логи бота (последние):
echo ────────────────────────────────────────────────────────────────
timeout /t 1 /nobreak >nul
goto end

:change_url
echo ⚙️ СМЕНА URL
echo ────────────────────────────────────────────────────────────────
echo.
echo 📋 Текущий URL:
findstr "WEBAPP_URL" webapp_bot.py
echo.
echo [1] 🏠 Продакшен: https://anonimka.online/
echo [2] 📂 GitHub Pages: https://vorobey444.github.io/anonimka.online/
echo [3] 🔗 Локальный ngrok (введу вручную)
echo.

set /p url_choice="Выберите URL (1-3): "

if "%url_choice%"=="1" (
    powershell -Command "(Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', 'WEBAPP_URL = \"https://anonimka.online/\"' | Set-Content webapp_bot.py"
    echo ✅ URL изменён на: https://anonimka.online/
)
if "%url_choice%"=="2" (
    powershell -Command "(Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', 'WEBAPP_URL = \"https://vorobey444.github.io/anonimka.online/\"' | Set-Content webapp_bot.py"
    echo ✅ URL изменён на: https://vorobey444.github.io/anonimka.online/
)
if "%url_choice%"=="3" (
    set /p custom_url="Введите ngrok URL (с https:// и / в конце): "
    powershell -Command "(Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', 'WEBAPP_URL = \"%custom_url%\"' | Set-Content webapp_bot.py"
    echo ✅ URL изменён на: %custom_url%
)
goto end

:invalid_choice
echo ❌ Неверный выбор!
goto end

:end
echo.
echo ════════════════════════════════════════════════════════════════
echo 💡 ПОЛЕЗНЫЕ КОМАНДЫ:
echo    • F5 - обновить страницу Mini App для тестирования
echo    • Ctrl+Shift+I - открыть DevTools в браузере  
echo    • Ctrl+C - остановить процессы в терминале
echo ════════════════════════════════════════════════════════════════
pause