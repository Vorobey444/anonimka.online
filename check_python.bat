@echo off
chcp 65001 >nul
title 🔍 Диагностика Python

echo.
echo ╔╦╗╦╔═╗╔═╗╔╗╔╔═╗╔═╗╔╦╗╦╔═╗
echo ║║║╠═╣║ ╦║║║║ ║╚═╗ ║ ║║  
echo ═╩╝╩╩ ╩╚═╝╝╚╝╚═╝╚═╝ ╩ ╩╚═╝
echo.
echo 🔍 Диагностика установки Python
echo ════════════════════════════════════════════════════════════════

echo 🔎 Поиск Python в системе...
echo.

echo [1] Проверяем команду 'python'
python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ python найден
    where python
) else (
    echo ❌ python не найден
)

echo.
echo [2] Проверяем команду 'python3'  
python3 --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ python3 найден
    where python3
) else (
    echo ❌ python3 не найден
)

echo.
echo [3] Проверяем Python Launcher 'py'
py --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ py найден
    where py
    echo 📋 Доступные версии:
    py -0
) else (
    echo ❌ py не найден
)

echo.
echo [4] Проверяем venv Python
if exist "E:\my project\app chat\.venv\Scripts\python.exe" (
    echo ✅ venv Python найден
    "E:\my project\app chat\.venv\Scripts\python.exe" --version
    echo 📁 Путь: E:\my project\app chat\.venv\Scripts\python.exe
) else (
    echo ❌ venv Python не найден
    echo 💡 Создайте виртуальное окружение: python -m venv .venv
)

echo.
echo [5] Проверяем PATH
echo 🛤️ Переменная PATH содержит:
echo %PATH% | findstr /i python
if %errorlevel% equ 0 (
    echo ✅ Python найден в PATH
) else (
    echo ❌ Python НЕ найден в PATH
    echo 💡 Добавьте Python в PATH или используйте полный путь
)

echo.
echo [6] Поиск Python в стандартных местах
echo 🔍 Ищем в стандартных директориях...

for %%d in (
    "C:\Python*\python.exe"
    "C:\Program Files\Python*\python.exe" 
    "C:\Program Files (x86)\Python*\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python*\python.exe"
    "%APPDATA%\..\Local\Programs\Python\Python*\python.exe"
) do (
    if exist "%%d" (
        echo ✅ Найден: %%d
    )
)

echo.
echo [7] Проверяем pip
pip --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ pip найден
    where pip
) else (
    echo ❌ pip не найден
    echo 💡 Попробуйте: python -m pip --version
)

echo.
echo ════════════════════════════════════════════════════════════════
echo 🎯 РЕКОМЕНДАЦИИ:
echo ════════════════════════════════════════════════════════════════

echo 💡 Если Python установлен, но не работает:
echo    • Перезапустите командную строку
echo    • Добавьте Python в PATH
echo    • Используйте 'py' вместо 'python'
echo    • Создайте виртуальное окружение
echo.
echo 💡 Если Python не установлен:
echo    • Скачайте с https://python.org
echo    • При установке отметьте "Add to PATH"
echo    • Выберите "Install for all users"
echo.
echo 💡 Для этого проекта рекомендуем:
echo    • Использовать виртуальное окружение
echo    • Команду: py -m venv .venv
echo    • Активация: .venv\Scripts\activate
echo.
pause