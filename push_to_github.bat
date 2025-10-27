@echo off
chcp 65001 >nul
title 🚀 Обновление anonimka.online

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║              🌐 ОБНОВЛЕНИЕ ANONIMKA.ONLINE v3.0                 ║
echo ║         https://github.com/Vorobey444/anonimka.online            ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

echo 📁 Копирую файлы webapp в корень для GitHub Pages...
copy /Y webapp\index.html . >nul
copy /Y webapp\style.css . >nul  
copy /Y webapp\app.js . >nul
echo ✅ Файлы скопированы

echo.
echo 🔍 Проверяю статус Git...
git status --porcelain

echo.
echo 📝 Добавляю все изменения...
git add -A
if %errorlevel% neq 0 (
    echo ❌ Ошибка при добавлении файлов
    pause
    exit /b 1
)

echo.
echo 💾 Создаю коммит...
git commit -m "🚀 Update to AnonimKa v3.0 - Added hamburger menu, IP geolocation, improved cyberpunk design"
if %errorlevel% neq 0 (
    echo ⚠️ Нет изменений для коммита или ошибка
)

echo.
echo 🌐 Отправляю на GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo ❌ Ошибка при отправке. Проверьте интернет и права доступа
    pause
    exit /b 1
)

echo.
echo ✅ УСПЕШНО! Обновления отправлены на GitHub
echo 🌐 Сайт будет обновлен в течение 1-2 минут
echo 📱 Проверьте: https://vorobey444.github.io/anonimka.online/
echo 🌍 Или: https://anonimka.online (если настроен custom domain)

echo.
echo ⚡ ЧТО НОВОГО В v3.0:
echo • 🍔 Гамбургер-меню с разделами
echo • 🌍 Автоматическое IP-определение местоположения
echo • 🎨 Улучшенный киберпанк дизайн
echo • 📱 Центрированные кнопки и элементы
echo • 📞 Контакты, правила, политика конфиденциальности
echo • ℹ️ Раздел "О приложении"

pause