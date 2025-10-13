@echo off
chcp 65001 >nul
title 🚀 Mini App Test

echo.
echo 🚀 Telegram Mini App - Быстрый тест
echo ════════════════════════════════════════════════════════════════

rem Остановка процессов
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1

rem Запуск веб-сервера
echo 🌐 Запуск локального сервера...
start "Local Server" /min cmd /c "cd webapp && python -m http.server 8000"
timeout /t 3 /nobreak >nul

rem Запуск ngrok
echo 🔗 Запуск ngrok...
start "ngrok" cmd /c "ngrok http 8000"
timeout /t 8 /nobreak >nul

echo.
echo ✅ Сервисы запущены!
echo ════════════════════════════════════════════════════════════════
echo 📋 ИНСТРУКЦИЯ:
echo.
echo 1. 📋 Скопируйте HTTPS URL из окна ngrok
echo    Пример: https://abc123.ngrok.io
echo.
echo 2. 🔄 Обновите URL в боте:
echo    • Откройте webapp_bot.py в блокноте
echo    • Найдите строку WEBAPP_URL = 
echo    • Замените на ваш ngrok URL с / в конце
echo    • Сохраните файл
echo.
echo 3. 🤖 Запустите бота:
echo    • Откройте новое окно cmd/PowerShell
echo    • cd "E:\my project\app chat\anon-board-bot"
echo    • python webapp_bot.py
echo.
echo 4. 📱 Тестируйте в Telegram:
echo    • Найдите бота
echo    • /start
echo    • "🚀 Открыть приложение"
echo.

set /p ngrok_url="Введите ngrok HTTPS URL (или Enter для ручной настройки): "

if "%ngrok_url%"=="" (
    echo 💡 Настройте URL вручную и запустите бота
    echo 📝 Команда: python webapp_bot.py
    pause
    exit /b 0
)

rem Добавляем слэш если нужно
echo %ngrok_url% | findstr "/$" >nul
if %errorlevel% neq 0 set "ngrok_url=%ngrok_url%/"

echo 🤖 Обновление webapp_bot.py...
powershell -Command "try { (Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', 'WEBAPP_URL = \"%ngrok_url%\"' | Set-Content webapp_bot.py; Write-Host 'URL обновлен!' } catch { Write-Host 'Ошибка обновления' }"

echo 🚀 Запуск бота...
start "Telegram Bot" cmd /c "title Telegram Mini App Bot && python webapp_bot.py && pause"

echo.
echo ✅ Готово! Mini App URL: %ngrok_url%
echo 📱 Тестируйте в Telegram!
pause