#!/data/data/com.termux/files/usr/bin/bash
# Pull latest from git and reinstall.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -d .git ]]; then
    echo "[*] Pulling latest..."
    git pull --rebase
else
    echo "[!] Not a git clone. Re-download manually."
    exit 1
fi

echo "[*] Reinstalling..."
bash install.sh

echo "[+] Updated."
