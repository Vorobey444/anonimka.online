@echo off
chcp 65001 >nul

echo ======================================================
echo    UPDATE ANONIMKA.ONLINE v3.0 TO GITHUB
echo ======================================================

echo Copying webapp files to root...
copy /Y webapp\index.html . >nul 2>&1
copy /Y webapp\style.css . >nul 2>&1
copy /Y webapp\app.js . >nul 2>&1
echo Files copied successfully

echo.
echo Adding files to Git...
git add index.html style.css app.js
if %errorlevel% neq 0 goto :error

echo Creating commit...
git commit -m "Update to AnonimKa v3.0 - hamburger menu and IP geolocation"
if %errorlevel% neq 0 goto :error_commit

echo Pushing to GitHub...
git push origin main
if %errorlevel% neq 0 goto :error_push

echo.
echo ======================================================
echo SUCCESS! Site updated on GitHub
echo Check: https://vorobey444.github.io/anonimka.online/
echo ======================================================
echo.
echo NEW IN v3.0:
echo - Hamburger menu with sections
echo - IP geolocation with radar animation  
echo - Improved cyberpunk design
echo - Centered buttons and elements
echo - Contact and privacy pages
echo ======================================================
goto :end

:error
echo ERROR: Git add failed. Check Git installation.
goto :manual

:error_commit  
echo No changes to commit or commit error.
goto :push_only

:error_push
echo ERROR: Push failed. Check internet and permissions.
goto :manual

:push_only
echo Trying to push existing changes...
git push origin main
goto :end

:manual
echo.
echo MANUAL UPDATE REQUIRED:
echo 1. Open: https://github.com/Vorobey444/anonimka.online
echo 2. Drag and drop: index.html, style.css, app.js
echo 3. Commit message: "Update to v3.0"
echo 4. Go to Settings > Pages > Enable GitHub Pages
start https://github.com/Vorobey444/anonimka.online

:end
echo.
pause