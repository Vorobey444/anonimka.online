@echo off
echo =====================================
echo   EMAIL SERVER FOR ANONIMKA.ONLINE
echo =====================================
echo.
echo Starting email server on port 5000...
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
call "%~dp0..\.venv\Scripts\activate.bat"
python email_server.py

pause