#!/usr/bin/env bash
set -euo pipefail

# Skills installer - installs skills to various AI assistant platforms
# Usage: ./install.sh [--claude|--opencode|--copilot|--all] [skill-name]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="${2:-dns-troubleshooter}"
SKILL_PATH="$SCRIPT_DIR/$SKILL_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check skill exists
[[ -d "$SKILL_PATH" ]] || error "Skill not found: $SKILL_PATH"

install_claude_code() {
    local dest="${HOME}/.claude/skills/$SKILL_NAME"
    info "Installing to Claude Code: $dest"
    mkdir -p "$(dirname "$dest")"
    cp -r "$SKILL_PATH" "$dest"
    info "Installed to Claude Code successfully"
}

install_opencode() {
    local dest="${HOME}/.config/opencode/skills/$SKILL_NAME"
    info "Installing to OpenCode: $dest"
    mkdir -p "$(dirname "$dest")"
    cp -r "$SKILL_PATH" "$dest"
    info "Installed to OpenCode successfully"
}

install_codex() {
    local dest="${CODEX_HOME:-${HOME}/.codex}/skills/$SKILL_NAME"
    info "Installing to Codex CLI: $dest"
    mkdir -p "$(dirname "$dest")"
    cp -r "$SKILL_PATH" "$dest"
    info "Installed to Codex CLI successfully"
}

install_copilot() {
    local project_root="${3:-.}"
    local dest="$project_root/.github/skills/$SKILL_NAME"
    info "Installing to GitHub Copilot: $dest"
    mkdir -p "$(dirname "$dest")"
    cp -r "$SKILL_PATH" "$dest"
    info "Installed to GitHub Copilot successfully"
}

install_claude_desktop() {
    local dest
    case "$(uname -s)" in
        Darwin) dest="${HOME}/Library/Application Support/Claude/skills/$SKILL_NAME" ;;
        Linux)  dest="${HOME}/.config/claude/skills/$SKILL_NAME" ;;
        MINGW*|MSYS*|CYGWIN*) dest="${APPDATA}/Claude/skills/$SKILL_NAME" ;;
        *) error "Unsupported platform for Claude Desktop" ;;
    esac
    info "Installing to Claude Desktop: $dest"
    mkdir -p "$(dirname "$dest")"
    cp -r "$SKILL_PATH" "$dest"
    info "Installed to Claude Desktop successfully"
}

install_all() {
    info "Installing to all platforms..."
    install_claude_code
    install_codex
    install_opencode
    install_claude_desktop
    warn "Copilot requires a project directory. Use --copilot with project path."
}

show_help() {
    cat << EOF
Skills Installer

Usage: ./install.sh [option] [skill-name] [project-path]

Options:
  --claude      Install to Claude Code (~/.claude/skills/)
  --codex       Install to Codex CLI (~/.codex/skills/)
  --opencode    Install to OpenCode (~/.config/opencode/skills/)
  --copilot     Install to GitHub Copilot (.github/skills/ in project)
  --desktop     Install to Claude Desktop (platform-specific)
  --all         Install to all global locations
  --help        Show this help message

Arguments:
  skill-name    Name of skill directory (default: dns-troubleshooter)
  project-path  Project path for Copilot install (default: current directory)

Examples:
  ./install.sh --claude
  ./install.sh --all dns-troubleshooter
  ./install.sh --copilot dns-troubleshooter /path/to/project
EOF
}

case "${1:-}" in
    --claude)  install_claude_code ;;
    --codex)   install_codex ;;
    --opencode) install_opencode ;;
    --copilot) install_copilot "$@" ;;
    --desktop) install_claude_desktop ;;
    --all)     install_all ;;
    --help|-h) show_help ;;
    "") show_help ;;
    *) error "Unknown option: $1. Use --help for usage." ;;
esac
