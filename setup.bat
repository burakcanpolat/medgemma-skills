@echo off
chcp 65001 >nul 2>&1
setlocal

echo.
echo ================================================
echo   Med-Rehber — Quick Setup
echo ================================================
echo.

:: -------------------------------------------------------------------
:: STEP 1: Python Check
:: -------------------------------------------------------------------
echo --- Step 1/3: Python Check ---
echo.

set "PYTHON_CMD="

python --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=python"
    goto :python_found
)

python3 --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=python3"
    goto :python_found
)

echo [X] Python not found!
echo.
echo Install Python 3.10+ from: https://www.python.org/downloads/
echo.
echo   1. Click the big yellow "Download Python" button
echo   2. Run the downloaded file
echo   3. IMPORTANT: Check "Add Python to PATH" at the bottom!
echo   4. Click "Install Now"
echo.
echo After installing, run this script again.
pause
exit /b 1

:python_found
for /f "tokens=2" %%v in ('%PYTHON_CMD% --version 2^>^&1') do set "PY_VER=%%v"
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)
if %PY_MAJOR% LSS 3 goto :python_too_old
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 goto :python_too_old
echo [OK] Python %PY_VER% is installed.
goto :modal_check

:python_too_old
echo [X] Python %PY_VER% found but 3.10+ is required!
echo.
echo Install Python 3.10+ from: https://www.python.org/downloads/
pause
exit /b 1

:modal_check

:: -------------------------------------------------------------------
:: STEP 2: Modal CLI Check
:: -------------------------------------------------------------------
echo.
echo --- Step 2/3: Modal CLI ---
echo.

modal --version >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Modal CLI is installed.
    goto :next_steps
)

echo Installing Modal CLI...
%PYTHON_CMD% -m pip install modal >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Modal CLI installed.
) else (
    echo [!] Could not install Modal CLI.
    echo     Try manually: pip install modal
    pause
    exit /b 1
)

:: -------------------------------------------------------------------
:: STEP 3: Next Steps
:: -------------------------------------------------------------------
:next_steps
echo.
echo --- Step 3/3: Next Steps ---
echo.
echo ================================================
echo [OK] Prerequisites are ready!
echo ================================================
echo.
echo   Now open this folder in an AI editor for guided setup:
echo.
echo   Option A — Zed (recommended):
echo     1. Download from https://zed.dev/download
echo     2. Get an API key from https://openrouter.ai/keys
echo     3. Open this folder in Zed
echo     4. Open Agent Panel and type: "start setup"
echo.
echo   Option B — Cursor:
echo     1. Download from https://cursor.com
echo     2. Open this folder in Cursor
echo     3. Open Chat and type: "start setup"
echo.
echo   Option C — Claude Code:
echo     1. Install Node.js from https://nodejs.org
echo     2. Run: npm install -g @anthropic-ai/claude-code
echo     3. Run: cd "%CD%" ^&^& claude
echo     4. Type: "start setup"
echo.
echo   The AI assistant will guide you through:
echo     * Modal account creation (free, $30/month credit)
echo     * HuggingFace token setup
echo     * MedGemma deployment
echo     * First analysis
echo.
pause
