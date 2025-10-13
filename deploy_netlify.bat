@echo off
chcp 65001 >nul
title 🌐 Деплой на Netlify

echo.
echo ╔╗╔╔═╗╔╦╗╦  ╦╔═╗╦ ╦  ╔╦╗╔═╗╔═╗╦  ╔═╗╦ ╦
echo ║║║║╣  ║ ║  ║╠╣ ╚╦╝   ║║║╣ ╠═╝║  ║ ║╚╦╝
echo ╝╚╝╚═╝ ╩ ╩═╝╩╚   ╩   ═╩╝╚═╝╩  ╩═╝╚═╝ ╩ 
echo.
echo 🌐 Быстрый деплой на Netlify для anonimka.online
echo ════════════════════════════════════════════════════════════════

echo 📋 ИНСТРУКЦИЯ:
echo ────────────────────────────────────────────────────────────────
echo 1. Откройте: https://netlify.com
echo 2. Войдите через GitHub аккаунт
echo 3. Нажмите "New site from Git"
echo 4. Выберите репозиторий: anonimka.online
echo 5. Branch: gh-pages
echo 6. Build command: (оставьте пустым)
echo 7. Publish directory: /
echo 8. Нажмите "Deploy site"
echo.
echo 🌐 НАСТРОЙКА ДОМЕНА:
echo ────────────────────────────────────────────────────────────────
echo 1. После деплоя нажмите "Domain settings"
echo 2. "Add custom domain" → anonimka.online
echo 3. Netlify покажет DNS настройки
echo 4. Обновите DNS у регистратора домена
echo.

echo ⚡ ПРЕИМУЩЕСТВА NETLIFY:
echo ────────────────────────────────────────────────────────────────
echo • ✅ Работает с приватными репозиториями
echo • ✅ Автоматический SSL сертификат
echo • ✅ Быстрый деплой (30 секунд)
echo • ✅ Автообновление при git push
echo.

set /p deploy="Хотите открыть Netlify прямо сейчас? (y/N): "
if /i "%deploy%"=="y" start https://netlify.com
if /i "%deploy%"=="yes" start https://netlify.com

echo.
echo ════════════════════════════════════════════════════════════════
echo 💡 Или сделайте GitHub репозиторий публичным
echo    и GitHub Pages заработает автоматически!
echo ════════════════════════════════════════════════════════════════
pause