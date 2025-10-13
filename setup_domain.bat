@echo off
chcp 65001 >nul
title 🌐 Настройка домена anonimka.online

echo.
echo  ╔═╗╔╗╔╔═╗╔╗╔╦╔╦╗╦╔═╔═╗ ╔═╗╔╗╔╦  ╦╔╗╔╔═╗
echo  ╠═╣║║║║ ║║║║║║║║║╠╩╗╠═╣ ║ ║║║║║  ║║║║║╣ 
echo  ╩ ╩╝╚╝╚═╝╝╚╝╩╩ ╩╩ ╩╩ ╩o╚═╝╝╚╝╩═╝╩╝╚╝╚═╝
echo.
echo 🌐 Настройка домена anonimka.online для Telegram Mini App
echo ════════════════════════════════════════════════════════════════════

if not exist "webapp_bot.py" (
    echo ❌ Файл webapp_bot.py не найден!
    pause
    exit /b 1
)

echo 📋 ТЕКУЩАЯ КОНФИГУРАЦИЯ:
echo ────────────────────────────────────────────────────────────────────
findstr "WEBAPP_URL" webapp_bot.py
echo ────────────────────────────────────────────────────────────────────
echo.

echo 🎯 НАСТРОЙКА ДОМЕНА anonimka.online:
echo.
echo [1] 🏠 Основной домен (рекомендуется)
echo     https://anonimka.online/
echo.
echo [2] 📁 Поддомен с путём  
echo     https://anonimka.online/app/
echo.
echo [3] 🔒 WWW версия
echo     https://www.anonimka.online/
echo.
echo [4] 📂 GitHub Pages (временно)
echo     https://username.github.io/repo-name/
echo.
echo [5] ⚙️ Пользовательский URL
echo.

set /p choice="Выберите вариант (1-5): "

if "%choice%"=="1" set "new_url=https://anonimka.online/"
if "%choice%"=="2" set "new_url=https://anonimka.online/app/"
if "%choice%"=="3" set "new_url=https://www.anonimka.online/"
if "%choice%"=="4" goto github_pages
if "%choice%"=="5" goto custom_url
if not defined new_url goto invalid_choice

goto update_url

:github_pages
echo.
echo 📂 GitHub Pages (для тестирования пока настраивается домен):
set /p username="Введите ваш GitHub username: "
set /p repo="Введите название репозитория: "
set "new_url=https://%username%.github.io/%repo%/"
goto update_url

:custom_url
echo.
echo ⚙️ Пользовательский URL:
set /p new_url="Введите полный HTTPS URL (с завершающим /): "
goto update_url

:invalid_choice
echo ❌ Неверный выбор!
pause
exit /b 1

:update_url
echo.
echo 🔍 Проверка URL: %new_url%
echo ────────────────────────────────────────────────────────────────────

rem Проверка HTTPS
echo %new_url% | findstr /i "^https://" >nul
if %errorlevel% neq 0 (
    echo ❌ URL должен начинаться с https://
    pause
    exit /b 1
)

rem Добавление завершающего слэша если нужно
echo %new_url% | findstr "/$" >nul
if %errorlevel% neq 0 (
    set "new_url=%new_url%/"
    echo ℹ️  Добавлен завершающий слэш
)

echo ✅ URL корректный: %new_url%
echo.

echo 📋 ПЛАН ДЕЙСТВИЙ:
echo ────────────────────────────────────────────────────────────────────
if "%choice%"=="1" (
    echo 1. ✅ Купить домен anonimka.online ^(выполнено^)
    echo 2. 🌐 Настроить DNS записи у регистратора
    echo 3. 📂 Загрузить файлы webapp/ на хостинг
    echo 4. 🔧 Обновить webapp_bot.py ^(сейчас^)
    echo 5. 🚀 Запустить бота
)
echo.

set /p confirm="Обновить webapp_bot.py URL на %new_url%? (y/N): "
if /i not "%confirm%"=="y" if /i not "%confirm%"=="yes" (
    echo ❌ Отменено
    pause
    exit /b 0
)

echo.
echo 💾 Обновление webapp_bot.py...

rem Резервная копия
copy webapp_bot.py webapp_bot.py.backup >nul 2>&1
echo ✅ Создана резервная копия

rem Обновление URL
powershell -Command "(Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', 'WEBAPP_URL = \"%new_url%\"' | Set-Content webapp_bot.py" 2>nul

if %errorlevel% neq 0 (
    echo ❌ Ошибка обновления
    copy webapp_bot.py.backup webapp_bot.py >nul
    pause
    exit /b 1
)

echo ✅ Файл обновлён!
echo.
echo 📋 НОВАЯ КОНФИГУРАЦИЯ:
echo ────────────────────────────────────────────────────────────────────
findstr "WEBAPP_URL" webapp_bot.py
echo ────────────────────────────────────────────────────────────────────
echo.

if "%choice%"=="1" goto domain_instructions
goto success_message

:domain_instructions
echo 🌐 НАСТРОЙКА DNS для anonimka.online:
echo ════════════════════════════════════════════════════════════════════
echo.
echo 📋 Добавьте эти DNS записи у вашего регистратора домена:
echo.
echo ┌─────────┬──────┬─────────────────────────┐
echo │ Тип     │ Имя  │ Значение                │
echo ├─────────┼──────┼─────────────────────────┤
echo │ A       │ @    │ 185.199.108.153         │
echo │ A       │ @    │ 185.199.109.153         │
echo │ A       │ @    │ 185.199.110.153         │
echo │ A       │ @    │ 185.199.111.153         │
echo │ CNAME   │ www  │ anonimka.online         │
echo └─────────┴──────┴─────────────────────────┘
echo.
echo 💡 Это для GitHub Pages. Если используете другой хостинг,
echo    следуйте инструкциям вашего хостера.
echo.
echo 📂 НЕ ЗАБУДЬТЕ:
echo    1. Загрузить файлы из папки webapp/ на хостинг
echo    2. Включить HTTPS в настройках хостинга
echo    3. Проверить что сайт открывается по адресу %new_url%
echo.

:success_message
echo ✅ ГОТОВО!
echo ════════════════════════════════════════════════════════════════════
echo.
echo 🚀 СЛЕДУЮЩИЕ ШАГИ:
if "%choice%"=="1" (
    echo    1. Настройте DNS как показано выше
    echo    2. Загрузите webapp/ файлы на GitHub Pages или другой хостинг
    echo    3. Дождитесь распространения DNS ^(до 24 часов^)
    echo    4. Проверьте что %new_url% открывается в браузере
) else (
    echo    1. Убедитесь что %new_url% доступен и работает
)
echo    5. Запустите: start_webapp_bot.bat
echo    6. Протестируйте бота в Telegram!
echo.

set /p run_bot="Запустить webapp_bot.py сейчас? (y/N): "
if /i "%run_bot%"=="y" goto run_bot
if /i "%run_bot%"=="yes" goto run_bot
goto end

:run_bot
echo.
echo 🤖 Запуск Telegram Mini App бота...
start "Telegram WebApp Bot" cmd /c "start_webapp_bot.bat"
timeout /t 2 /nobreak >nul
echo ✅ Бот запущен в отдельном окне!

:end
echo.
echo ════════════════════════════════════════════════════════════════════
echo 📖 Подробная инструкция: DOMAIN_SETUP.md
echo 🔧 Диагностика: check_python.bat  
echo 💡 Помощь: setup_miniapp.bat
echo ════════════════════════════════════════════════════════════════════
pause