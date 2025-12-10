#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import serial

DEV = "/dev/serial0"
BAUD = 9600
DELAY_PER_LINE = 0.5   # à ajuster si besoin

# Valeur de ESC t n à tester
T = 0  # la doc parle de PC437 → souvent ESC t 0

def main():
    print(f"Ouverture {DEV} @ {BAUD}…")
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
    time.sleep(0.3)

    # Sélection de la table ESC t T
    ser.write(b"\x1B\x74" + bytes([T]))
    time.sleep(0.1)

    # Petit en-tête très court
    header = f"\nCHAR TABLE ESC t={T}\n"
    ser.write(header.encode("ascii", "ignore"))
    time.sleep(0.2)

    # On imprime les codes 0x20..0xFF en 16 colonnes
    start = 0x20
    end = 0xFF

    for base in range(start, end + 1, 16):
        # Préfixe "A0:" etc pour repérer la ligne
        prefix = f"{base:02X}: "
        ser.write(prefix.encode("ascii", "ignore"))

        # 16 caractères bruts
        for val in range(base, min(base + 16, end + 1)):
            ser.write(bytes([val]))

        ser.write(b"\n")
        ser.flush()
        time.sleep(DELAY_PER_LINE)

    ser.write(b"\n-- END --\n\n")
    # Tentative de coupe (si supportée)
    ser.write(b"\x1D\x56\x00")
    ser.close()
    print("Terminé.")

if __name__ == "__main__":
    main()
