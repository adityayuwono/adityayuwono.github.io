@echo off
setlocal
cd /d "%~dp0"

echo Packaging Cozy Sushi for GitHub Pages...
echo.

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0tools\package_webgl.py" pack
    goto result
)

where python >nul 2>nul
if not errorlevel 1 (
    python "%~dp0tools\package_webgl.py" pack
    goto result
)

echo Python was not found. Install Python 3.11 or newer and try again.
echo Enable "Add Python to PATH" during installation.
pause
exit /b 1

:result
set "packageExitCode=%errorlevel%"
echo.
if "%packageExitCode%"=="0" (
    echo Packaging finished. Commit and push the updated website files.
) else (
    echo Packaging failed. Review the error above before committing.
)
pause
exit /b %packageExitCode%
