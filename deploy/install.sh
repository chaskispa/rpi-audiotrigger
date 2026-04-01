#!/bin/bash
set -e

PROJECT_DIR="/home/pi/rpi-audiotrigger"

echo "Updating system..."
sudo apt update

echo "Installing system packages..."
sudo apt install -y \
  python3 python3-full python3-venv python3-pip python3-dev \
  python3-rpi-lgpio \
  i2c-tools libi2c-dev python3-smbus \
  alsa-utils mpg123 exfatprogs udisks2

echo "Ensuring I2C is enabled..."
sudo raspi-config nonint do_i2c 0 || true

echo "Creating USB mount point..."
sudo mkdir -p /mnt/usb
sudo chown pi:pi /mnt/usb

echo "Setting up Python environment..."
cd "$PROJECT_DIR"

rm -rf .venv

python3 -m venv --system-site-packages .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel

# install only required deps (avoid broken ws281x)
pip install --no-cache-dir adafruit-blinka adafruit-circuitpython-vl53l0x --no-deps
pip install --no-cache-dir Adafruit-PlatformDetect Adafruit-PureIO

deactivate

echo "Installing systemd + udev..."
sudo cp deploy/usb-audio-mount.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/usb-audio-mount.sh

sudo cp deploy/99-usb-audio.rules /etc/udev/rules.d/
sudo cp deploy/usb-audio-player.service /etc/systemd/system/
sudo cp deploy/usb-audio-mount@.service /etc/systemd/system/

sudo udevadm control --reload-rules
sudo systemctl daemon-reload
sudo systemctl enable usb-audio-player.service

echo "Configuring audio output..."
amixer cset numid=3 1 || true
amixer sset PCM 100% || true

echo "Adding user to I2C group..."
sudo usermod -aG i2c pi || true

echo "Install complete. Reboot recommended."