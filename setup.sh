#!/usr/bin/env bash
# Med-Rehber — Quick Setup
# Checks prerequisites and guides you to the AI-assisted setup wizard.

set -e

echo ""
echo "================================================"
echo "  Med-Rehber — Quick Setup"
echo "================================================"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# -------------------------------------------------------------------
# STEP 1: Python Check
# -------------------------------------------------------------------
echo "━━━ Step 1/3: Python Check ━━━"
echo ""

PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
fi

if [ -n "$PYTHON_CMD" ]; then
    PY_VER_FULL=$($PYTHON_CMD --version 2>&1 | sed 's/Python //')
    PY_MAJOR=$(echo "$PY_VER_FULL" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER_FULL" | cut -d. -f2)

    if [ "$PY_MAJOR" -gt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 10 ]; }; then
        ok "Python $PY_VER_FULL is installed."
    else
        fail "Python $PY_VER_FULL found but 3.10+ is required."
        PYTHON_CMD=""
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    fail "Python not found!"
    echo ""
    echo "Install Python 3.10+ from: https://www.python.org/downloads/"
    echo ""
    case "$(uname -s)" in
        Darwin*)
            echo "  Or via Homebrew: brew install python3"
            ;;
        Linux*)
            echo "  Or via apt: sudo apt update && sudo apt install python3 python3-pip -y"
            ;;
    esac
    echo ""
    echo "After installing, run this script again."
    exit 1
fi

# -------------------------------------------------------------------
# STEP 2: Modal CLI Check
# -------------------------------------------------------------------
echo ""
echo "━━━ Step 2/3: Modal CLI ━━━"
echo ""

if command -v modal &>/dev/null; then
    ok "Modal CLI is installed."
else
    info "Installing Modal CLI..."
    if command -v uv &>/dev/null; then
        uv tool install modal 2>/dev/null && ok "Modal CLI installed via uv." || {
            $PYTHON_CMD -m pip install modal && ok "Modal CLI installed via pip." || {
                fail "Could not install Modal CLI."
                echo "  Try manually: pip install modal"
                exit 1
            }
        }
    else
        $PYTHON_CMD -m pip install modal && ok "Modal CLI installed via pip." || {
            fail "Could not install Modal CLI."
            echo "  Try manually: pip install modal"
            exit 1
        }
    fi
fi

# -------------------------------------------------------------------
# STEP 3: Next Steps
# -------------------------------------------------------------------
echo ""
echo "━━━ Step 3/3: Next Steps ━━━"
echo ""
echo "================================================"
ok "Prerequisites are ready!"
echo "================================================"
echo ""
echo "  Now open this folder in an AI editor for guided setup:"
echo ""
echo "  Option A — Zed (recommended):"
echo "    1. Download from https://zed.dev/download"
echo "    2. Get an API key from https://openrouter.ai/keys"
echo "    3. Open this folder in Zed"
echo "    4. Open Agent Panel and type: \"start setup\""
echo ""
echo "  Option B — Cursor:"
echo "    1. Download from https://cursor.com"
echo "    2. Open this folder in Cursor"
echo "    3. Open Chat and type: \"start setup\""
echo ""
echo "  Option C — Claude Code:"
echo "    1. Install: npm install -g @anthropic-ai/claude-code"
echo "    2. Run: cd \"$(cd "$(dirname "$0")" && pwd)\" && claude"
echo "    3. Type: \"start setup\""
echo ""
echo "  The AI assistant will guide you through:"
echo "    • Modal account creation (free, \$30/month credit)"
echo "    • HuggingFace token setup"
echo "    • MedGemma deployment"
echo "    • First analysis"
echo ""
