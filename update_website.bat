@echo off
chcp 65001 >nul
title 🌐 Обновление anonimka.online

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║            🌐 ОБНОВЛЕНИЕ ANONIMKA.ONLINE v3.0                ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

echo 📋 ФАЙЛЫ ГОТОВЫ К ЗАГРУЗКЕ:
echo ────────────────────────────────────────────────────────────────
dir /b deploy\

echo.
echo 🚀 СПОСОБЫ ДЕПЛОЯ:
echo ────────────────────────────────────────────────────────────────
echo.
echo 1️⃣  FTP ЗАГРУЗКА (Рекомендуется):
echo   • Откройте FTP клиент (FileZilla, WinSCP)
echo   • Подключитесь к серверу anonimka.online
echo   • Загрузите все файлы из папки deploy\
echo.
echo 2️⃣  NETLIFY (Быстро):
echo   • Зайдите на netlify.com
echo   • Перетащите папку deploy\ на сайт
echo   • Настройте домен anonimka.online
echo.
echo 3️⃣  GITHUB PAGES:
echo   • Создайте репозиторий anonimka-online
echo   • Загрузите файлы из deploy\
echo   • Включите GitHub Pages
echo.

echo ⚡ НОВЫЕ ВОЗМОЖНОСТИ v3.0:
echo ────────────────────────────────────────────────────────────────
echo • 🍔 Гамбургер-меню с разделами
echo • 🌍 Автоматическое определение IP-локации
echo • 🎨 Улучшенный киберпанк дизайн
echo • 📱 Полная адаптивность
echo • 🔒 Расширенная приватность
echo.

set /p choice="Выберите действие: [1-FTP] [2-Netlify] [3-GitHub] [Enter-открыть папку]: "

if "%choice%"=="1" (
    echo 📁 Откройте папку deploy\ в FTP клиенте...
    start explorer.exe deploy\
)

if "%choice%"=="2" (
    echo 🌐 Открываю Netlify...
    start https://app.netlify.com/drop
    start explorer.exe deploy\
)

if "%choice%"=="3" (
    echo 📊 Открываю GitHub...
    start https://github.com/new
    start explorer.exe deploy\
)

if "%choice%"=="" (
    echo 📁 Открываю папку с файлами...
    start explorer.exe deploy\
)

echo.
echo ✅ Файлы подготовлены в папке: deploy\
echo 🌐 После загрузки сайт будет доступен на: https://anonimka.online
echo.
pause