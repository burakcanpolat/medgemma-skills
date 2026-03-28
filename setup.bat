@echo off
chcp 65001 >nul 2>&1
setlocal

echo.
echo ================================================
echo   Med-Rehber — Quick Setup
echo ================================================
echo.

:: -------------------------------------------------------------------
:: STEP 1: Check / Install uv
:: -------------------------------------------------------------------
echo --- Step 1/3: uv Package Manager ---
echo.

uv --version >nul 2>&1
if %errorlevel%==0 (
    echo [OK] uv is installed.
    goto :uv_ready
)

echo [!] uv is not installed.
echo.
echo Please install uv by running this command in PowerShell:
echo.
echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
echo.
echo After installing, close and reopen this terminal, then run this script again.
pause
exit /b 1

:uv_ready

:: -------------------------------------------------------------------
:: STEP 2: Install project dependencies
:: -------------------------------------------------------------------
echo.
echo --- Step 2/3: Project Dependencies ---
echo.

echo Installing dependencies...
uv sync
if %errorlevel%==0 (
    echo [OK] Project dependencies installed.
) else (
    echo [X] Could not install dependencies.
    echo     Try manually: uv sync
    pause
    exit /b 1
)

:: -------------------------------------------------------------------
:: STEP 3: Install Modal CLI
:: -------------------------------------------------------------------
echo.
echo --- Step 3/3: Modal CLI ---
echo.

modal --version >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Modal CLI is already installed.
    goto :next_steps
)

echo Installing Modal CLI...
uv tool install modal
if %errorlevel%==0 (
    echo [OK] Modal CLI installed.
) else (
    echo [X] Could not install Modal CLI.
    echo     Try manually: uv tool install modal
    pause
    exit /b 1
)

:: -------------------------------------------------------------------
:: Next Steps
:: -------------------------------------------------------------------
:next_steps
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
