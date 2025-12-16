#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import serial

DEV = "/dev/serial0"
BAUD = 9600

CHARS = "ÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸàâäçéèêëîïôöùûüÿœŒ«»€—–•…"

def w(ser, s: str):
    ser.write(s.encode("gb18030", errors="replace"))

def main():
    ser = serial.Serial(DEV, BAUD, timeout=1)
    # Reset
    ser.write(b"\x1B\x40")
    time.sleep(0.2)

    # Font B (compact) via ESC ! n (très courant)
    ser.write(b"\x1B\x21\x01")
    time.sleep(0.05)

    # --- Test chars FR ---
    w(ser, "FR chars (gb18030):\n")
    w(ser, CHARS + "\n\n")

    # --- Règle colonnes pour mesurer la largeur en Font B ---
    # (tu comptes combien de chiffres sortent avant retour à la ligne)
    w(ser, "Regle colonnes (Font B):\n")
    w(ser, "1234567890" * 6 + "\n")  # 60 chars
    w(ser, "0....5....1....5....2....5....3....5....4....5....5....\n\n")

    # --- Cadre Unicode (box drawing) ---
    title = "Cadre Unicode"
    inner_width = 28  # largeur interne (ajuste après lecture du ticket)
    # centre le titre
    pad_left = max(0, (inner_width - len(title)) // 2)
    pad_right = max(0, inner_width - len(title) - pad_left)

    top = "╔" + ("═" * inner_width) + "╗\n"
    mid = "║" + (" " * pad_left) + title + (" " * pad_right) + "║\n"
    bot = "╚" + ("═" * inner_width) + "╝\n"

    w(ser, top + mid + bot)

    w(ser, "\n\n")
    ser.flush()
    ser.close()

if __name__ == "__main__":
    main()
