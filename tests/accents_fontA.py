#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import serial

DEV="/dev/serial0"
BAUD=9600

SETS = [
  ("OK_confirmes", "àéèêù€—…"),
  ("MAJ_fr",       "ÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ"),
  ("min_fr",       "àâäçéèêëîïôöùûüÿ"),
  ("ligatures",    "œŒ"),
  ("guillemets",   "«»"),
  ("tirets",       "–—"),
]

def w(ser, s: str):
    ser.write(s.encode("gb18030", errors="replace"))

def test_font(ser, label: str, esc_bang: bytes):
    ser.write(b"\x1B\x40")      # reset
    time.sleep(0.15)
    ser.write(esc_bang)         # font
    time.sleep(0.05)

    w(ser, f"\n== {label} ==\n")
    for name, chars in SETS:
        w(ser, f"{name}: ")
        w(ser, chars)
        w(ser, "\n")
        time.sleep(0.05)

def main():
    ser = serial.Serial(DEV, BAUD, timeout=1)

    # Font A puis Font B
    test_font(ser, "Font A (ESC ! 0)", b"\x1B\x21\x00")
    #test_font(ser, "Font B (ESC ! 1)", b"\x1B\x21\x01")

    ser.close()

if __name__ == "__main__":
    main()
