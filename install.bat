@echo off
chcp 65001 >nul
title 🔧 Установка зависимостей

echo.
echo ╦╔╗╔╔═╗╔╦╗╔═╗╦  ╦    
echo ║║║║╚═╗ ║ ╠═╣║  ║    
echo ╩╝╚╝╚═╝ ╩ ╩ ╩╩═╝╩═╝  
echo.
echo 🛠️ Установка зависимостей для анонимной доски объявлений
echo ════════════════════════════════════════════════════════════════

echo 🔍 Проверка Python и pip...

REM Проверяем разные варианты команды Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    echo ✅ Найден: python
    python --version
    goto python_found
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    echo ✅ Найден: python3
    python3 --version
    goto python_found
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    echo ✅ Найден: py (Python Launcher)
    py --version
    goto python_found
)

"E:\my project\app chat\.venv\Scripts\python.exe" --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD="E:\my project\app chat\.venv\Scripts\python.exe"
    echo ✅ Найден: venv Python
    "E:\my project\app chat\.venv\Scripts\python.exe" --version
    goto python_found
)

echo ❌ Python не найден ни по одной из команд!
echo 💡 Попробуйте:
echo    • Установить Python с https://python.org
echo    • Добавить Python в PATH
echo    • Использовать Python Launcher (py)
echo    • Активировать виртуальное окружение
pause
exit /b 1

:python_found

echo ✅ Python найден
echo.

echo 📦 Установка python-telegram-bot...

REM Используем найденную команду Python для установки
if "%PYTHON_CMD%"=="python" (
    python -m pip install python-telegram-bot
) else if "%PYTHON_CMD%"=="python3" (
    python3 -m pip install python-telegram-bot
) else if "%PYTHON_CMD%"=="py" (
    py -m pip install python-telegram-bot
) else (
    "E:\my project\app chat\.venv\Scripts\python.exe" -m pip install python-telegram-bot
)

if %errorlevel% neq 0 (
    echo ❌ Ошибка установки! Попробуйте:
    echo    %PYTHON_CMD% -m pip install --upgrade pip
    echo    %PYTHON_CMD% -m pip install python-telegram-bot --user
    echo    %PYTHON_CMD% -m pip install python-telegram-bot --break-system-packages
    pause
    exit /b 1
)

echo.
echo ✅ Зависимости установлены успешно!
echo.
echo 🚀 Теперь можно запускать бота:
echo    • start_bot.bat - главное меню
echo    • start_classic_bot.bat - классический бот  
echo    • start_webapp_bot.bat - Mini App бот
echo    • start_server.bat - веб-сервер
echo.
pause