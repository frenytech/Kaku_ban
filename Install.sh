#!/data/data/com.termux/files/usr/bin/bash
# Kaku WA Checker — Termux installer.

set -e

INSTALL_DIR="$HOME/.kaku_wa"
LAUNCHER="$PREFIX/bin/kaku-wa"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "================================================"
echo "  KAKU WA CHECKER — Termux Install"
echo "================================================"
echo ""

# --- deps ---
echo "[*] Updating package lists..."
pkg update -y >/dev/null 2>&1 || true

echo "[*] Installing python + pip..."
pkg install -y python python-pip >/dev/null 2>&1

echo "[*] Installing requests..."
pip install --quiet requests 2>/dev/null || pip install --quiet requests --break-system-packages

# --- tool dir ---
mkdir -p "$INSTALL_DIR"

# --- copy checker ---
if [[ -f "$SCRIPT_DIR/kaku_wa_checker.py" ]]; then
    cp "$SCRIPT_DIR/kaku_wa_checker.py" "$INSTALL_DIR/kaku_wa_checker.py"
else
    echo "[!] kaku_wa_checker.py not found next to install.sh"
    exit 1
fi
chmod +x "$INSTALL_DIR/kaku_wa_checker.py"

# --- launcher ---
cat > "$LAUNCHER" <<'LAUNCHEREOF'
#!/data/data/com.termux/files/usr/bin/bash
TOOL_DIR="$HOME/.kaku_wa"
cd "$TOOL_DIR" || exit 1

if [[ $# -eq 0 ]]; then
    cat <<HELP
Kaku WA Checker
---------------
Usage:
  kaku-wa <numbers.txt>              # default 8 workers
  kaku-wa <numbers.txt> -w 4 -d 1.0  # slower, stealthier
  kaku-wa --help                     # full options

Input format (numbers.txt):
  +14155552671
  +447700900123

Results land in: $TOOL_DIR/
HELP
    exit 0
fi

exec python3 "$TOOL_DIR/kaku_wa_checker.py" "$@"
LAUNCHEREOF
chmod +x "$LAUNCHER"

# --- sample input ---
if [[ ! -f "$INSTALL_DIR/numbers.txt" ]]; then
    cat > "$INSTALL_DIR/numbers.txt" <<'EOF'
+14155552671
+14155552672
+447700900123
EOF
fi

echo ""
echo "[+] Installed."
echo "[+] Tool dir : $INSTALL_DIR"
echo "[+] Launcher : kaku-wa"
echo ""
echo "Next:"
echo "  1. Edit numbers:  nano $INSTALL_DIR/numbers.txt"
echo "  2. Run it:        kaku-wa $INSTALL_DIR/numbers.txt"
echo ""
