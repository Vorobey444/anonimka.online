# 🚀 Быстрый запуск Telegram Mini App
# PowerShell скрипт для тестирования

Write-Host ""
Write-Host "🚀 Запуск Telegram Mini App" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Проверка файлов
if (!(Test-Path "webapp\index.html")) {
    Write-Host "❌ Папка webapp не найдена!" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Остановка старых процессов
Write-Host "⏹️ Остановка старых процессов..." -ForegroundColor Yellow
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "ngrok" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Запуск веб-сервера
Write-Host "🌐 Запуск веб-сервера..." -ForegroundColor Green
Start-Process -FilePath "cmd" -ArgumentList "/c", "cd webapp && python -m http.server 8000" -WindowStyle Normal
Start-Sleep -Seconds 3

# Поиск ngrok
$ngrokPath = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Name "ngrok.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($ngrokPath) {
    $fullNgrokPath = Join-Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" $ngrokPath
    Write-Host "🔗 Запуск ngrok туннеля..." -ForegroundColor Green
    Start-Process -FilePath $fullNgrokPath -ArgumentList "http", "8000" -WindowStyle Normal
    Start-Sleep -Seconds 5
} else {
    Write-Host "❌ ngrok не найден!" -ForegroundColor Red
    Write-Host "💡 Установите ngrok: winget install Ngrok.Ngrok" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Получение ngrok URL
Write-Host "⏳ Получение ngrok URL..." -ForegroundColor Yellow
$ngrokUrl = $null
for ($i = 1; $i -le 15; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction SilentlyContinue
        if ($response.tunnels) {
            $httpsUrl = $response.tunnels | Where-Object { $_.public_url -like "https://*" } | Select-Object -First 1
            if ($httpsUrl) {
                $ngrokUrl = $httpsUrl.public_url + "/"
                break
            }
        }
    } catch {
        # Игнорируем ошибки и продолжаем попытки
    }
    Write-Host "Попытка $i/15..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if (!$ngrokUrl) {
    Write-Host "❌ Не удалось получить ngrok URL автоматически" -ForegroundColor Red
    $ngrokUrl = Read-Host "💡 Введите HTTPS URL из окна ngrok"
    if (!$ngrokUrl.EndsWith("/")) {
        $ngrokUrl += "/"
    }
}

Write-Host "✅ ngrok URL: $ngrokUrl" -ForegroundColor Green

# Обновление URL в боте
Write-Host "🤖 Обновление URL в боте..." -ForegroundColor Cyan
try {
    $content = Get-Content "webapp_bot.py" -Raw
    $updatedContent = $content -replace 'WEBAPP_URL = ".*"', "WEBAPP_URL = `"$ngrokUrl`""
    Set-Content "webapp_bot.py" -Value $updatedContent
    Write-Host "✅ URL обновлён успешно!" -ForegroundColor Green
} catch {
    Write-Host "❌ Ошибка обновления URL: $_" -ForegroundColor Red
}

# Запуск бота
Write-Host "🚀 Запуск бота..." -ForegroundColor Cyan
$pythonPath = "E:\my project\app chat\.venv\Scripts\python.exe"
Start-Process -FilePath "cmd" -ArgumentList "/c", "`"$pythonPath`" webapp_bot.py & pause" -WindowStyle Normal

Write-Host ""
Write-Host "✅ ВСЁ ГОТОВО!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "🎮 Теперь в Telegram:" -ForegroundColor Yellow
Write-Host "   1. Откройте вашего бота" -ForegroundColor White
Write-Host "   2. Отправьте /start" -ForegroundColor White  
Write-Host "   3. Нажмите '🚀 Открыть приложение'" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Mini App URL: $ngrokUrl" -ForegroundColor Cyan
Write-Host "📱 Локально: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Изменения в webapp/ видны мгновенно (F5 в Mini App)" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green

Read-Host "Нажмите Enter для завершения"