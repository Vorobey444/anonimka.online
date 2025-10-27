# PowerShell скрипт для обновления GitHub
Write-Host "🚀 Обновление AnonimKa v3.0 на GitHub" -ForegroundColor Cyan

# Проверяем наличие Git Bash
$gitBash = Get-Command "git" -ErrorAction SilentlyContinue
if (-not $gitBash) {
    Write-Host "❌ Git не найден. Установите Git из https://git-scm.com/" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit
}

# Переходим в папку проекта
Set-Location "E:\my project\app chat\anon-board-bot"

Write-Host "📁 Копирую файлы webapp в корень..." -ForegroundColor Yellow

# Копируем файлы
Copy-Item "webapp\index.html" "." -Force
Copy-Item "webapp\style.css" "." -Force  
Copy-Item "webapp\app.js" "." -Force

Write-Host "✅ Файлы скопированы" -ForegroundColor Green

# Пробуем Git команды через разные методы
$env:PATH += ";C:\Program Files\Git\bin;C:\Program Files\Git\cmd"

try {
    Write-Host "📝 Добавляю файлы в Git..." -ForegroundColor Yellow
    
    # Используем Start-Process для обхода проблем совместимости
    $addProcess = Start-Process -FilePath "git" -ArgumentList "add", "index.html", "style.css", "app.js" -Wait -PassThru -NoNewWindow
    
    if ($addProcess.ExitCode -eq 0) {
        Write-Host "✅ Файлы добавлены" -ForegroundColor Green
        
        $commitProcess = Start-Process -FilePath "git" -ArgumentList "commit", "-m", "🚀 Update to AnonimKa v3.0 - hamburger menu + IP geolocation" -Wait -PassThru -NoNewWindow
        
        if ($commitProcess.ExitCode -eq 0) {
            Write-Host "✅ Коммит создан" -ForegroundColor Green
            
            $pushProcess = Start-Process -FilePath "git" -ArgumentList "push", "origin", "main" -Wait -PassThru -NoNewWindow
            
            if ($pushProcess.ExitCode -eq 0) {
                Write-Host "🌐 Успешно! Сайт обновлен на GitHub" -ForegroundColor Green
                Write-Host "📱 Проверьте: https://vorobey444.github.io/anonimka.online/" -ForegroundColor Cyan
                
                Write-Host "`n⚡ ЧТО НОВОГО В v3.0:" -ForegroundColor Magenta
                Write-Host "• 🍔 Гамбургер-меню с разделами" -ForegroundColor White
                Write-Host "• 🌍 IP-геолокация с анимацией" -ForegroundColor White
                Write-Host "• 🎨 Улучшенный киберпанк дизайн" -ForegroundColor White
                Write-Host "• 📱 Центрированные кнопки" -ForegroundColor White
                Write-Host "• 📞 Информационные страницы" -ForegroundColor White
            } else {
                throw "Push failed"
            }
        } else {
            throw "Commit failed"  
        }
    } else {
        throw "Add failed"
    }
} catch {
    Write-Host "❌ Ошибка Git: $_" -ForegroundColor Red
    Write-Host "`n🌐 Альтернативный способ:" -ForegroundColor Yellow
    Write-Host "1. Откройте https://github.com/Vorobey444/anonimka.online" -ForegroundColor White
    Write-Host "2. Перетащите файлы index.html, style.css, app.js в репозиторий" -ForegroundColor White
    Write-Host "3. Коммит: '🚀 Update to v3.0'" -ForegroundColor White
    Write-Host "4. В Settings → Pages включите GitHub Pages" -ForegroundColor White
    
    # Открываем репозиторий
    Start-Process "https://github.com/Vorobey444/anonimka.online"
}

Read-Host "`nНажмите Enter для выхода"