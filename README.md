# rpi-audioplayer

Raspberry Pi audio player that uses a VL53L0X distance sensor as a trigger.
When something enters a configured distance range, the player advances to the
next audio file on a USB drive and plays it through ALSA.

The repository includes:

- The Python player loop
- A JSON config file
- A systemd service for running on boot
- A udev rule and mount helper for automatically mounting a USB stick at
  `/mnt/usb`

## How It Works

1. The Python process reads distance values from a VL53L0X over I2C.
2. Readings are smoothed with a median window.
3. When the filtered reading enters the configured trigger zone, the next file
   in the playlist is played.
4. The trigger does not fire again until the object leaves the zone.
5. Audio files are read from the mounted USB drive and played in alphabetical
   order.

Supported file types:

- `.wav` via `aplay`
- `.mp3` via `mpg123`

Hidden files, dotfiles, and Apple resource-fork files such as `._track.mp3`
are ignored.

## Hardware / OS Assumptions

- Raspberry Pi running Raspberry Pi OS
- VL53L0X distance sensor connected over I2C
- USB audio output or ALSA-compatible output device
- USB drive formatted as `exFAT`

The deploy scripts assume:

- User: `pi`
- Project directory on the Pi: `/home/pi/rpi-audiotrigger`
- USB mountpoint: `/mnt/usb`

## Setup

### 1. Enable I2C

On the Pi:

```bash
sudo raspi-config
```

Enable I2C, then reboot if needed.

### 2. Clone the Project

The deploy scripts expect the checkout to live at:

```bash
/home/pi/rpi-audiotrigger
```

Example:

```bash
cd /home/pi
git clone https://github.com/chaskispa/rpi-audiotrigger.git rpi-audiotrigger
cd rpi-audiotrigger
```

### 3. Run the Installer

```bash
chmod +x deploy/install.sh
./deploy/install.sh
```

The installer will:

- install system packages
- create a Python virtual environment
- install Python dependencies
- copy the udev rule and systemd units
- enable `usb-audio-player.service`
- set ALSA output defaults with `amixer`

Reboot after install:

```bash
sudo reboot
```

## USB Behavior

When a USB block device partition is added, the udev rule starts
`usb-audio-mount@.service`, which runs:

```bash
/usr/local/bin/usb-audio-mount.sh /dev/<device>
```

That script:

- ensures `/mnt/usb` exists
- unmounts anything already mounted there
- mounts the new device as `exfat`
- sets ownership to `pi:pi`

Put `.wav` and/or `.mp3` files in the root of the USB drive. Files are played in
alphabetical order.

## Configuration

Runtime settings live in
[config.json](/Users/dtbmbp/Documents/code/rpi-audioplayer/config.json).

Key settings:

- `min_mm` / `max_mm`: trigger zone in millimeters
- `valid_min_mm`: discard obviously bad short readings
- `window_size`: median filter sample window
- `enter_count_required`: number of consecutive in-zone readings required to
  trigger playback
- `exit_count_required`: number of consecutive out-of-zone readings required
  before the system can trigger again
- `audio_device`: ALSA device passed to `aplay` / `mpg123`
- `usb_path`: mounted audio path, normally `/mnt/usb`
- `print_every`: debug log interval in seconds

The player watches `config.json` for changes and reloads it automatically while
running.

## Running and Monitoring

Start or restart the player:

```bash
sudo systemctl restart usb-audio-player.service
```

Check status:

```bash
sudo systemctl status usb-audio-player.service
```

Follow logs:

```bash
journalctl -u usb-audio-player.service -f
```

You should see logs like:

- `Running...`
- `Playlist:`
- `PLAY: filename.mp3`
- `raw=... filtered=... inside=True`

## Development

Create a virtual environment and install dependencies manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Run locally:

```bash
python usb_playlist_trigger.py
```

This requires Pi hardware, I2C access, the VL53L0X sensor, and a valid ALSA
audio device.

## Troubleshooting

No audio plays:

- check `audio_device` in `config.json`
- run `aplay -l` to list ALSA devices
- verify the files on the USB drive are `.wav` or `.mp3`

USB drive does not mount:

- confirm it is formatted as `exFAT`
- inspect udev and service logs:

```bash
journalctl -u usb-audio-mount@sdX1.service
```

Sensor does not trigger:

- verify I2C is enabled
- run `i2cdetect -y 1`
- inspect the player logs for `raw` and `filtered` readings
- adjust `min_mm`, `max_mm`, and debounce counts in `config.json`
