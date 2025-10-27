#!/bin/bash
# GitHub Update Script for AnonimKa v3.0

echo "🚀 Обновляю anonimka.online..."

# Копируем файлы webapp в корень для GitHub Pages
cp webapp/index.html ./index.html
cp webapp/style.css ./style.css  
cp webapp/app.js ./app.js

echo "✅ Файлы скопированы"

# Git команды
git add index.html style.css app.js
git commit -m "🚀 Update to AnonimKa v3.0 - Added hamburger menu, IP geolocation, improved cyberpunk design"
git push origin main

echo "🌐 Обновления отправлены на GitHub"
echo "📱 Проверьте: https://vorobey444.github.io/anonimka.online/"