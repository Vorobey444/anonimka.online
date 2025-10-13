@echo off
chcp 65001 >nul
title 🌐 Настройка Mini App

echo.
echo ╔╦╗╦╔╗╔╦  ╔═╗╔═╗╔═╗  ╔═╗╔═╗╔╦╗╦ ╦╔═╗
echo ║║║║║║║║  ╠═╣╠═╝╠═╝  ╚═╗║╣  ║ ║ ║╠═╝
echo ╩ ╩╩╝╚╝╩  ╩ ╩╩  ╩    ╚═╝╚═╝ ╩ ╚═╝╩  
echo.
echo 🌐 Настройка Telegram Mini App
echo ════════════════════════════════════════════════════════════════

echo 📋 ПОШАГОВАЯ ИНСТРУКЦИЯ:
echo.
echo [1] 🚀 Быстрый старт с ngrok (для тестирования)
echo ────────────────────────────────────────────────────────────
echo    1. Скачайте ngrok: https://ngrok.com/download
echo    2. Запустите: start_server.bat
echo    3. В другом терминале: ngrok http 8000
echo    4. Скопируйте HTTPS URL (например: https://abc123.ngrok.io)
echo    5. Откройте webapp_bot.py в блокноте
echo    6. Замените:
echo       WEBAPP_URL = "https://your-domain.com/webapp/"
echo       на ваш ngrok URL:
echo       WEBAPP_URL = "https://abc123.ngrok.io/"
echo    7. Запустите: start_webapp_bot.bat
echo    8. Найдите вашего бота в Telegram
echo    9. Нажмите /start
echo    10. Нажмите кнопку "🚀 Открыть приложение"
echo.

echo [2] 🌍 Размещение на бесплатном хостинге
echo ────────────────────────────────────────────────────────────
echo    🔸 GitHub Pages:
echo       • Создайте репозиторий на github.com
echo       • Загрузите содержимое папки webapp/
echo       • В настройках включите Pages
echo       • URL: https://username.github.io/repo-name/
echo.
echo    🔸 Netlify:  
echo       • Перетащите папку webapp/ на netlify.com
echo       • Получите URL типа: https://random-name.netlify.app/
echo.
echo    🔸 Vercel:
echo       • Загрузите webapp/ на vercel.com
echo       • URL: https://project-name.vercel.app/
echo.

echo [3] ⚙️ Настройка бота
echo ────────────────────────────────────────────────────────────
echo    1. Откройте webapp_bot.py в любом редакторе
echo    2. Найдите строку: WEBAPP_URL = "..."  
echo    3. Замените на ваш HTTPS URL
echo    4. Сохраните файл
echo    5. Запустите: start_webapp_bot.bat
echo.

echo [4] 🎮 Использование Mini App
echo ────────────────────────────────────────────────────────────
echo    Пользователи будут:
echo    1. Находить вашего бота в Telegram
echo    2. Отправлять /start
echo    3. Видеть кнопку "🚀 Открыть приложение"
echo    4. Нажимать на неё
echo    5. Открывается киберпанк интерфейс!
echo.

echo ⚠️  ВАЖНЫЕ МОМЕНТЫ:
echo ────────────────────────────────────────────────────────────
echo • Mini App работает ТОЛЬКО по HTTPS
echo • Для ngrok нужно перезапускать при каждом использовании
echo • Для постоянной работы используйте хостинг
echo • URL должен заканчиваться на / (слэш)
echo.

echo 🔧 БЫСТРАЯ НАСТРОЙКА NGROK:
set /p setup="Хотите настроить ngrok прямо сейчас? (y/N): "
if /i "%setup%"=="y" goto setup_ngrok
if /i "%setup%"=="yes" goto setup_ngrok
goto end

:setup_ngrok
echo.
echo 🚀 Настройка ngrok...
echo ────────────────────────────────────────────────────────────
echo 1. Проверяем наличие ngrok...
ngrok version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ngrok не найден!
    echo 📥 Скачайте с: https://ngrok.com/download
    echo 💡 Или установите через chocolatey: choco install ngrok
    goto end
)

echo ✅ ngrok найден!
echo.
echo 2. Запускаем веб-сервер в фоне...
start "Web Server" cmd /c "start_server.bat"
timeout /t 3 /nobreak >nul

echo 3. Запускаем ngrok...
echo 💡 Скопируйте HTTPS URL из окна ngrok и обновите webapp_bot.py
echo.
ngrok http 8000

:end
echo.
echo ════════════════════════════════════════════════════════════════
echo 💡 Нужна помощь? 
echo    • Документация: README.md
echo    • Диагностика: check_python.bat
echo    • Установка: quick_install.bat
echo ════════════════════════════════════════════════════════════════
pause