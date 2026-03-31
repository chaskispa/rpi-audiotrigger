import time
import subprocess
import os
import json
from collections import deque
from statistics import median

import board
import busio
import adafruit_vl53l0x

CONFIG_PATH = "config.json"
INVALID_READING = 8190

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

cfg = load_config()

MIN_MM = cfg["min_mm"]
MAX_MM = cfg["max_mm"]
VALID_MIN = cfg["valid_min_mm"]

WINDOW_SIZE = cfg["window_size"]
ENTER_COUNT_REQUIRED = cfg["enter_count_required"]
EXIT_COUNT_REQUIRED = cfg["exit_count_required"]

AUDIO_DEVICE = cfg["audio_device"]
USB_PATH = cfg["usb_path"]
PRINT_EVERY = cfg["print_every"]

def get_playlist(path):
    files = []
    for f in os.listdir(path):
        name = f.lower()
        if f.startswith(".") or f.startswith("._"):
            continue
        if not name.endswith((".wav", ".mp3")):
            continue
        files.append(f)
    files.sort()
    return [os.path.join(path, f) for f in files]

def play_file(filepath):
    lower = filepath.lower()
    if lower.endswith(".wav"):
        subprocess.run(["aplay", "-D", AUDIO_DEVICE, filepath])
    elif lower.endswith(".mp3"):
        subprocess.run(["mpg123", "-a", AUDIO_DEVICE, filepath])

i2c = busio.I2C(board.SCL, board.SDA)
vl53 = adafruit_vl53l0x.VL53L0X(i2c)

samples = deque(maxlen=WINDOW_SIZE)
inside_count = 0
outside_count = 0
in_zone = False
index = 0
last_playlist = []
last_print = 0

config_mtime = os.path.getmtime(CONFIG_PATH)

print("Running...")

while True:
    try:
        new_mtime = os.path.getmtime(CONFIG_PATH)
        if new_mtime != config_mtime:
            cfg = load_config()

            MIN_MM = cfg["min_mm"]
            MAX_MM = cfg["max_mm"]
            VALID_MIN = cfg["valid_min_mm"]

            WINDOW_SIZE = cfg["window_size"]
            ENTER_COUNT_REQUIRED = cfg["enter_count_required"]
            EXIT_COUNT_REQUIRED = cfg["exit_count_required"]

            AUDIO_DEVICE = cfg["audio_device"]
            USB_PATH = cfg["usb_path"]
            PRINT_EVERY = cfg["print_every"]

            samples = deque(maxlen=WINDOW_SIZE)
            print("Config reloaded")
            config_mtime = new_mtime
    except:
        pass

    if not os.path.ismount(USB_PATH):
        time.sleep(1)
        continue

    playlist = get_playlist(USB_PATH)
    if not playlist:
        time.sleep(1)
        continue

    if playlist != last_playlist:
        print("Playlist:")
        for p in playlist:
            print("-", os.path.basename(p))
        last_playlist = playlist
        index = 0

    raw = vl53.range
    valid = (raw != INVALID_READING and raw >= VALID_MIN)

    if valid:
        samples.append(raw)

    filtered = int(median(samples)) if samples else None
    inside_now = (filtered is not None and MIN_MM <= filtered <= MAX_MM)

    if inside_now:
        inside_count += 1
        outside_count = 0
    else:
        outside_count += 1
        inside_count = 0

    if not in_zone and inside_count >= ENTER_COUNT_REQUIRED:
        file_to_play = playlist[index]
        print("PLAY:", os.path.basename(file_to_play))
        play_file(file_to_play)
        index = (index + 1) % len(playlist)
        in_zone = True

    if in_zone and outside_count >= EXIT_COUNT_REQUIRED:
        in_zone = False

    if time.time() - last_print >= PRINT_EVERY:
        print(f"raw={raw} filtered={filtered} inside={inside_now}")
        last_print = time.time()

    time.sleep(0.05)