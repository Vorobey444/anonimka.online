@echo off
chcp 65001 > nul
title Yandex Email Server - anonimka.online

echo ════════════════════════════════════════════
echo    YANDEX EMAIL SERVER - ANONIMKA.ONLINE
echo ════════════════════════════════════════════
echo.
echo 📧 Отправитель: wish.online@yandex.kz
echo 📬 Получатель: vorobey469@yandex.ru  
echo 🌐 Порт: 5000
echo.

cd /d "%~dp0"

:: Активация виртуального окружения
call "..\..\.venv\Scripts\activate.bat"

:: Проверка установки зависимостей
echo 📦 Проверка зависимостей...
python -c "import flask, flask_cors, smtplib" 2>nul
if errorlevel 1 (
    echo ⚠️  Установка недостающих зависимостей...
    pip install flask flask-cors
)

echo.
echo 🚀 Запуск Yandex Email Server...
echo ⏹️  Для остановки нажмите Ctrl+C
echo.

:: Запуск сервера
python yandex_email_server.py

echo.
echo 📧 Yandex Email Server остановлен
pause