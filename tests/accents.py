#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import serial

DEV = "/dev/serial0"
BAUD = 9600
DELAY = 0.35   # ← délai entre chaque ligne (à ajuster si besoin)

# Encodages à tester
encodings = [
    "cp437",
    "cp850",
    "cp852",
    "cp858",
    "cp1252",
    "latin1",
]

# Texte de test
TEST = "Éléoï ça € à é è ê ï ô ù ç"

def main():
    print(f"Ouverture série sur {DEV} @ {BAUD}…")
    ser = serial.Serial(
        port=DEV,
        baudrate=BAUD,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1,
    )

    # Reset imprimante
    ser.write(b"\x1B\x40")
    time.sleep(0.4)

    print("\nImpression bruteforce accents… "
          "Regarde quelle ligne est correcte.\n")

    for t in range(2, 9):  # ESC t 0..15
        for enc in encodings:

            # Construire la ligne
            header = f"[t={t:02d} enc={enc}] "

            try:
                payload = TEST.encode(enc, errors="replace")
            except LookupError:
                continue

            # Sélection du codepage interne ESC t n
            ser.write(b"\x1B\x74" + bytes([t]))

            # Envoi sur 1 ligne propre
            ser.write(header.encode("ascii", "ignore") + payload + b"\n")

            ser.flush()
            time.sleep(DELAY)

    # fin ticket & éventuelle coupe
    ser.write(b"\n\n")
    ser.write(b"\x1D\x56\x00")  # GS V 0 (si supporté)
    ser.close()

    print("\nFini. Cherche la ligne où les accents sont corrects.")

if __name__ == "__main__":
    main()
