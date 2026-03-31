#!/bin/bash
set -e

DEVNAME="$1"
MOUNTPOINT="/mnt/usb"

mkdir -p "$MOUNTPOINT"

if mountpoint -q "$MOUNTPOINT"; then
    umount "$MOUNTPOINT" || true
fi

sleep 1

mount -t exfat -o uid=pi,gid=pi,umask=022 "$DEVNAME" "$MOUNTPOINT"