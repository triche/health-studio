#!/usr/bin/env bash
# Health Studio CLI — Install Script (macOS / Linux)
# Installs the `hs` command via pipx or pip install --user.
# Idempotent: safe to re-run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$HOME/.health-studio"
MIN_PYTHON_VERSION="3.11"

info()  { printf '\033[1;34m[INFO]\033[0m  %s\n' "$1"; }
ok()    { printf '\033[1;32m[OK]\033[0m    %s\n' "$1"; }
warn()  { printf '\033[1;33m[WARN]\033[0m  %s\n' "$1"; }
err()   { printf '\033[1;31m[ERR]\033[0m   %s\n' "$1"; exit 1; }

# --- Check Python ≥ 3.11 ---
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        version=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        if [ -n "$version" ]; then
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
                PYTHON="$candidate"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    err "Python >= $MIN_PYTHON_VERSION is required but not found on \$PATH."
fi
info "Using $PYTHON ($("$PYTHON" --version))"

# --- Install via pipx or pip --user ---
# If inside a virtualenv, use pip install directly (--user is not supported).
IN_VENV=false
if [ -n "${VIRTUAL_ENV:-}" ] || "$PYTHON" -c "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)" 2>/dev/null; then
    IN_VENV=true
fi

if command -v pipx &>/dev/null; then
    info "Installing via pipx..."
    pipx install "$CLI_DIR" --force
elif $IN_VENV; then
    info "Virtual environment detected. Installing via pip install..."
    "$PYTHON" -m pip install "$CLI_DIR"
else
    info "pipx not found. Installing via pip install --user..."
    "$PYTHON" -m pip install --user "$CLI_DIR"
fi

# --- Verify hs is on PATH; if not, add to shell profiles ---
if command -v hs &>/dev/null; then
    ok "hs command is available: $(command -v hs)"
else
    # Determine the bin directory where pip/pipx installed the script
    BIN_DIR=""
    if $IN_VENV; then
        BIN_DIR="${VIRTUAL_ENV:-}/bin"
    else
        # Common user-local bin directories
        for dir in "$HOME/.local/bin" "$HOME/Library/Python/$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/bin"; do
            if [ -x "$dir/hs" ]; then
                BIN_DIR="$dir"
                break
            fi
        done
    fi

    if [ -n "$BIN_DIR" ]; then
        PATH_LINE="export PATH=\"$BIN_DIR:\$PATH\""
        ADDED_TO=""

        for rcfile in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
            if [ -f "$rcfile" ]; then
                if ! grep -qF "$BIN_DIR" "$rcfile" 2>/dev/null; then
                    printf '\n# Health Studio CLI\n%s\n' "$PATH_LINE" >> "$rcfile"
                    ADDED_TO="$ADDED_TO $(basename "$rcfile")"
                fi
            fi
        done

        # On macOS, ensure .zshrc exists (zsh is the default shell)
        if [[ "$(uname)" == "Darwin" ]] && [ ! -f "$HOME/.zshrc" ]; then
            printf '# Health Studio CLI\n%s\n' "$PATH_LINE" > "$HOME/.zshrc"
            ADDED_TO="$ADDED_TO .zshrc"
        fi

        if [ -n "$ADDED_TO" ]; then
            ok "Added $BIN_DIR to PATH in:$ADDED_TO"
            info "Restart your shell or run: source ~/.zshrc  (or ~/.bashrc)"
        else
            ok "$BIN_DIR already in shell profiles"
        fi
    else
        warn "hs is installed but not on your \$PATH."
        warn "You may need to add one of these to your shell profile:"
        warn "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
fi

# --- Create config directory ---
if [ ! -d "$CONFIG_DIR" ]; then
    mkdir -p "$CONFIG_DIR"
    chmod 700 "$CONFIG_DIR"
    ok "Created config directory: $CONFIG_DIR"
else
    ok "Config directory already exists: $CONFIG_DIR"
fi

echo ""
ok "Installation complete!"
info "Run 'hs config init' to connect to your Health Studio instance."
