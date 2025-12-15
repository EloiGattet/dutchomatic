#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time

PORT = "/dev/serial0"
BAUD = 9600

def esc(ser, *vals):
    ser.write(bytes(vals))

with serial.Serial(PORT, BAUD, bytesize=8, parity="N",
                   stopbits=1, timeout=1) as ser:

    # ------------------------------------------------------------------
    # RESET GLOBAL
    # ------------------------------------------------------------------
    esc(ser, 0x1B, 0x40)              # ESC @
    time.sleep(0.1)

    # ------------------------------------------------------------------
    # 1) TEST CP850 + FRANCE
    # ------------------------------------------------------------------
    esc(ser, 0x1B, 0x52, 0x01)        # ESC R 1 -> set international = France
    esc(ser, 0x1B, 0x74, 0x01)        # ESC t 1 -> codepage 850
    time.sleep(0.05)

    ser.write("Charset interne = France, codepage = 850\n".encode("cp850"))

    # Petit dump ASCII visible (32–126), 4 lignes
    for row in range(4):
        start = 32 + row * 24
        end   = min(start + 24, 127)
        line  = "".join(chr(c) for c in range(start, end))
        ser.write(line.encode("cp850") + b"\n")
        time.sleep(0.1)

    ser.write(b"\n--- Passage en PC437 pour les box drawing ---\n\n")

    # ------------------------------------------------------------------
    # 2) PC437 + CADRES / SEPARATEURS
    # ------------------------------------------------------------------
    esc(ser, 0x1B, 0x74, 0x00)        # ESC t 0 -> codepage 437
    time.sleep(0.05)

    # -- 2.a Cadre en octets bruts C9 CD BB C8 BC BA -------------------
    TOTAL_WIDTH = 32          # nb de colonnes désirées
    inner_width = TOTAL_WIDTH - 2

    texte = " DUTCH-O-MATIC "
    texte = texte[:inner_width]
    pad = inner_width - len(texte)
    left_pad = pad // 2
    right_pad = pad - left_pad

    inner_line = (
        b" " * left_pad +
        texte.encode("ascii", "ignore") +
        b" " * right_pad
    )

    # C9 = ╔, CD = ═, BB = ╗, BA = ║, C8 = ╚, BC = ╝
    top    = b"\xC9" + b"\xCD" * inner_width + b"\xBB\n"
    middle = b"\xBA" + inner_line            + b"\xBA\n"
    bottom = b"\xC8" + b"\xCD" * inner_width + b"\xBC\n"

    ser.write(b"[Cadre PC437 (octets bruts)]\n")
    ser.write(top)
    ser.write(middle)
    ser.write(bottom)
    ser.write(b"\n")
    time.sleep(0.2)

    # -- 2.b Cadre via Unicode box-drawing encodé en cp437 ------------
    # (Si ton terminal les affiche, c’est plus lisible dans le code.)
    try:
        unicode_box = "╔══════════════════════╗\n" \
                      "║  Cadre Unicode 437   ║\n" \
                      "╚══════════════════════╝\n\n"
        ser.write(unicode_box.encode("cp437"))
    except Exception:
        # Si le fichier est en ASCII pur, on évite le crash
        ser.write(b"(Impossible d'encoder les box Unicode en cp437)\n\n")

    time.sleep(0.2)

    # -- 2.c Ligne séparatrice avec F0 --------------------------------
    # F0 = bloc / pattern plein dans PC437
    length = 32
    sep_line = b"\xF0" * length + b"\n"
    ser.write(b"[Separateur F0]\n")
    ser.write(sep_line + b"\n")
    time.sleep(0.2)

    # ------------------------------------------------------------------
    # 3) CARACTERE UTILISATEUR POUR '~' (placeholder pour '€')
    # ------------------------------------------------------------------
    ser.write(b"--- Test caractere utilisateur pour '~' ---\n")

    # ESC & s n m w d1..dx
    # s = 3  -> 24 dots de haut
    # w = 3  -> 3 colonnes (3 * 3 = 9 octets)
    # n = m = 0x7E (code ASCII de '~')
    s = 3
    n = m = 0x7E
    w = 3

    # Pour l'instant: bloc plein (tu pourras remplacer par un vrai bitmap de €)
    euro_block = bytes([0xFF] * (s * w))

    ser.write(bytes([0x1B, 0x26, s, n, m, w]) + euro_block)

    # Activer les user-defined chars
    esc(ser, 0x1B, 0x25, 0x01)  # ESC % 1

    # Ici on reste en cp437 (ou cp850, peu importe, '~' = 0x7E)
    ser.write("Prix: 12,50 ~ (caractere user)\n\n".encode("cp437"))

    # Désactiver les user-defined chars -> retour à la fonte ROM normale
    esc(ser, 0x1B, 0x25, 0x00)  # ESC % 0

    ser.write(b"(Fin des tests)\n\n")
