#!/bin/bash
set -e

PROJECT_DIR="/home/pi/rpi-audiotrigger"

sudo apt update
sudo apt install -y \
  python3 python3-full python3-venv python3-pip \
  i2c-tools libi2c-dev python3-smbus \
  alsa-utils mpg123 exfatprogs udisks2

sudo mkdir -p /mnt/usb
sudo chown pi:pi /mnt/usb

cd "$PROJECT_DIR"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

sudo cp deploy/usb-audio-mount.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/usb-audio-mount.sh

sudo cp deploy/99-usb-audio.rules /etc/udev/rules.d/
sudo cp deploy/usb-audio-player.service /etc/systemd/system/
sudo cp deploy/usb-audio-mount@.service /etc/systemd/system/

sudo udevadm control --reload-rules
sudo systemctl daemon-reload
sudo systemctl enable usb-audio-player.service

amixer cset numid=3 1 || true
amixer sset PCM 100% || true

echo "Done. Reboot."