@echo off
chcp 65001 >nul
title 🔧 Альтернативное решение

echo.
echo 🔧 Альтернативы для тестирования Mini App
echo ════════════════════════════════════════════════════════════════
echo.
echo ngrok требует настройки. Вот альтернативы:
echo.
echo [1] 📱 Использовать Telegram Desktop
echo     • Localhost работает в Telegram Desktop
echo     • Но не работает в мобильном приложении
echo.
echo [2] 🌐 Использовать GitHub Pages напрямую  
echo     • https://vorobey444.github.io/anonimka.online/
echo     • Стабильно, но нужно деплоить изменения
echo.
echo [3] 🔗 Настроить ngrok с аутентификацией
echo     • Нужен бесплатный аккаунт на ngrok.com
echo     • Одноразовая настройка
echo.
echo [4] ☁️ Использовать другой туннельный сервис
echo     • localtunnel: npm install -g localtunnel
echo     • serveo.net (без установки)
echo.

set /p choice="Выберите вариант (1-4): "

if "%choice%"=="1" goto telegram_desktop
if "%choice%"=="2" goto github_pages
if "%choice%"=="3" goto setup_ngrok
if "%choice%"=="4" goto alternatives
goto end

:telegram_desktop
echo.
echo 📱 ТЕСТИРОВАНИЕ В TELEGRAM DESKTOP
echo ════════════════════════════════════════════════════════════════
echo 1. Локальный сервер уже запущен: http://localhost:8000
echo 2. URL в боте: http://localhost:8000/ (уже настроен)
echo 3. Запуск бота...

python webapp_bot.py
goto end

:github_pages
echo.
echo 🌐 GITHUB PAGES (СТАБИЛЬНОЕ РЕШЕНИЕ)
echo ════════════════════════════════════════════════════════════════
powershell -Command "(Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', 'WEBAPP_URL = \"https://vorobey444.github.io/anonimka.online/\"' | Set-Content webapp_bot.py"
echo ✅ URL обновлён на GitHub Pages
echo 🚀 Запуск бота...
start "Telegram Bot" cmd /c "python webapp_bot.py && pause"
echo.
echo 💡 Для внесения изменений используйте: test_mode.bat → режим 2
goto end

:setup_ngrok
echo.
echo 🔗 НАСТРОЙКА NGROK
echo ════════════════════════════════════════════════════════════════
echo 1. Идите на: https://ngrok.com/signup
echo 2. Создайте бесплатный аккаунт
echo 3. Скопируйте authtoken
echo 4. Выполните: ngrok authtoken YOUR_TOKEN
echo 5. Запустите: ngrok http 8000
echo 6. Обновите URL в боте на ngrok HTTPS URL
echo.
start https://ngrok.com/signup
goto end

:alternatives
echo.
echo ☁️ АЛЬТЕРНАТИВНЫЕ СЕРВИСЫ
echo ════════════════════════════════════════════════════════════════
echo.
echo 🔸 LocalTunnel:
echo    npm install -g localtunnel
echo    lt --port 8000 --subdomain mybot
echo.
echo 🔸 Serveo (без установки):
echo    ssh -R 80:localhost:8000 serveo.net
echo.
echo 🔸 Bore:  
echo    cargo install bore-cli
echo    bore local 8000 --to bore.pub
echo.
echo Выберите подходящий вариант и настройте туннель
goto end

:end
echo.
echo ════════════════════════════════════════════════════════════════
echo 💡 СОВЕТ: Для продакшена используйте GitHub Pages (anonimka.online)
echo 🔧 Для разработки: локальный туннель (ngrok/localtunnel)
echo ════════════════════════════════════════════════════════════════
pause