@echo off
chcp 65001 >nul
title 🚀 Запуск Mini App

echo.
echo 🚀 Запуск Telegram Mini App
echo ════════════════════════════════════════════════════════════════
echo.

rem Останавливаем старые процессы
echo ⏹️ Остановка старых процессов...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im ngrok.exe >nul 2>&1

echo 🌐 Запуск веб-сервера...
start "Web Server" cmd /c "cd webapp && python -m http.server 8000"
timeout /t 3 /nobreak >nul

echo 🔗 Запуск ngrok туннеля...
set "NGROK_PATH=C:\Users\%USERNAME%\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
start "ngrok" cmd /c ""%NGROK_PATH%" http 8000"
timeout /t 5 /nobreak >nul

echo ⏳ Получение ngrok URL...
for /l %%i in (1,1,15) do (
    curl -s http://localhost:4040/api/tunnels 2>nul | findstr "https.*ngrok" >temp_url.txt
    if exist temp_url.txt (
        for /f "tokens=*" %%a in (temp_url.txt) do set "ngrok_response=%%a"
        del temp_url.txt
        goto parse_url
    )
    echo Попытка %%i/15...
    timeout /t 2 /nobreak >nul
)

echo ❌ Не удалось получить ngrok URL автоматически
echo 💡 Скопируйте HTTPS URL из окна ngrok и введите вручную
set /p ngrok_url="Введите ngrok HTTPS URL: "
goto update_bot

:parse_url
rem Простое извлечение URL из JSON ответа
for /f "tokens=2 delims=:" %%i in ("%ngrok_response%") do (
    for /f "tokens=1 delims=," %%j in ("%%i") do (
        set "raw_url=%%j"
    )
)
set "ngrok_url=%raw_url:"=%"
set "ngrok_url=%ngrok_url: =%"
set "ngrok_url=%ngrok_url%/"

echo ✅ ngrok URL: %ngrok_url%

:update_bot
echo 🤖 Обновление URL в боте...
powershell -Command "(Get-Content webapp_bot.py) -replace 'WEBAPP_URL = \".*\"', 'WEBAPP_URL = \"%ngrok_url%\"' | Set-Content webapp_bot.py"

echo 🚀 Запуск бота...
start "Telegram Bot" cmd /c "title Telegram Bot && "E:\my project\app chat\.venv\Scripts\python.exe" webapp_bot.py && pause"

echo.
echo ✅ ВСЁ ГОТОВО!
echo ════════════════════════════════════════════════════════════════
echo 🎮 Теперь в Telegram:
echo    1. Откройте вашего бота
echo    2. Отправьте /start  
echo    3. Нажмите "🚀 Открыть приложение"
echo.
echo 🌐 Mini App URL: %ngrok_url%
echo 📱 Локально: http://localhost:8000
echo.
echo 💡 Изменения в webapp/ видны мгновенно (F5 в Mini App)
echo ════════════════════════════════════════════════════════════════
pause