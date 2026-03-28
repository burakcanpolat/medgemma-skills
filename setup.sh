#!/usr/bin/env bash
# Med-Rehber — Quick Setup
# Installs uv, syncs dependencies, and guides you to the AI-assisted setup wizard.

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
# STEP 1: Check / Install uv
# -------------------------------------------------------------------
echo "━━━ Step 1/3: uv Package Manager ━━━"
echo ""

if command -v uv &>/dev/null; then
    UV_VER=$(uv --version 2>&1)
    ok "uv is installed ($UV_VER)."
else
    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the env so uv is available in this session
    export PATH="$HOME/.local/bin:$PATH"
    if command -v uv &>/dev/null; then
        ok "uv installed successfully."
    else
        fail "Could not install uv."
        echo "  Try manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
fi

# -------------------------------------------------------------------
# STEP 2: Install project dependencies
# -------------------------------------------------------------------
echo ""
echo "━━━ Step 2/3: Project Dependencies ━━━"
echo ""

info "Running uv sync..."
uv sync
ok "Project dependencies installed."

# -------------------------------------------------------------------
# STEP 3: Install Modal CLI
# -------------------------------------------------------------------
echo ""
echo "━━━ Step 3/3: Modal CLI ━━━"
echo ""

if command -v modal &>/dev/null; then
    ok "Modal CLI is already installed."
else
    info "Installing Modal CLI..."
    uv tool install modal && ok "Modal CLI installed." || {
        fail "Could not install Modal CLI."
        echo "  Try manually: uv tool install modal"
        exit 1
    }
fi

# -------------------------------------------------------------------
# Next Steps
# -------------------------------------------------------------------
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
