#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time

PORT = "/dev/serial0"
BAUD = 9600

DELAY_LINE = 0.05   # délai entre chaque ligne imprimée
DELAY_BLOCK = 0.15  # délai entre deux combinaisons (R, t)

def set_charsets(ser, R, t):
    """Configure l'internal character set (ESC R) et la code table (ESC t)."""
    ser.write(b"\x1B\x52" + bytes([R]))  # ESC R n
    ser.write(b"\x1B\x74" + bytes([t]))  # ESC t n
    time.sleep(0.02)

with serial.Serial(
    PORT,
    BAUD,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=1,
) as ser:
    # Reset imprimante
    ser.write(b"\x1B\x40")  # ESC @
    time.sleep(0.1)

    ser.write(b"\n=== SCAN COMPLET DES TABLES DE CARACTERES ===\n\n")

    # R = internal character set (0..13 doc, on s'arrête là) Français = 1
    for R in [1]:
        ser.write(f"\n==== ESC R {R} ====\n".encode("ascii"))
        time.sleep(0.1)

        # t = code page (0..7 pour chercher d'éventuelles tables cachées)
        for t in [1]:
            set_charsets(ser, R, t)
            ser.write(f"[R={R} t={t}]\n".encode("ascii"))

            # Valeurs 0x20..0xFF (on évite 0x00..0x1F qui sont des contrôles)
            for base in range(0x20, 0x100, 16):
                # préfixe: adresse hex de la ligne
                line_prefix = f"{base:02X}: ".encode("ascii")
                ser.write(line_prefix)

                # 16 caractères bruts
                for val in range(base, min(base + 16, 0x100)):
                    ser.write(bytes([val]))

                ser.write(b"\n")
                ser.flush()
                time.sleep(DELAY_LINE)

            ser.write(b"\n")
            time.sleep(DELAY_BLOCK)

    ser.write(b"\n*** FIN DU SCAN DES CHARSETS ***\n\n")
