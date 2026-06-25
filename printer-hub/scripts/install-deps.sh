#!/usr/bin/env bash
# Run once on the Pi as root: sudo bash scripts/install-deps.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: run as root (sudo bash $0)" >&2
    exit 1
fi

echo "==> Updating package lists"
apt-get update -q

echo "==> Installing system packages"
apt-get install -y \
    cups \
    cups-client \
    avahi-daemon \
    avahi-utils \
    python3-dev \
    python3-pip \
    python3-venv \
    libcups2-dev \
    printer-driver-gutenprint \
    foomatic-db-compressed-ppds \
    usbutils

echo "==> Enabling system services (start deferred to provision-device.sh)"
systemctl enable cups
systemctl enable avahi-daemon

echo "==> Creating Python virtual environment at $PROJECT_DIR/.venv"
python3 -m venv "$PROJECT_DIR/.venv"
"$PROJECT_DIR/.venv/bin/pip" install --upgrade pip --quiet
"$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" --quiet

echo "==> Done. Run 'sudo bash scripts/provision-device.sh' to complete first-boot setup."
