#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'auto-détection de l'encodage pour l'imprimante A2.
Teste différents encodages et configurations pour trouver celui qui fonctionne.
"""

import time
import serial

DEV = "/dev/serial0"
BAUD = 9600
DELAY = 0.2  # Réduit pour économiser le papier

# Texte de test avec accents français
TEST_TEXT = "Éléoï ça à é è ê ë ï ô ù ç É À Ç"

# Caractères à tester individuellement
TEST_CHARS = [
    "a", "e", "i", "o", "u",  # Base
    "à", "é", "è", "ê", "ë",  # Accents e
    "ï", "ô", "ù", "ç",       # Autres
    "É", "À", "Ç",            # Majuscules
]

def test_encoding(ser, name, R, t, encoding_name, test_text):
    """Test un encodage avec une configuration donnée."""
    # Reset
    ser.write(b"\x1B\x40")
    time.sleep(0.1)
    
    # Configuration
    if R is not None:
        ser.write(b"\x1B\x52" + bytes([R]))
        time.sleep(0.05)
    if t is not None:
        ser.write(b"\x1B\x74" + bytes([t]))
        time.sleep(0.1)
    
    # Header
    config_str = f"[{name}] "
    ser.write(config_str.encode("ascii"))
    
    # Texte encodé
    try:
        if encoding_name:
            payload = test_text.encode(encoding_name, errors="replace")
        else:
            payload = test_text.encode("ascii", errors="replace")
        ser.write(payload)
    except Exception as e:
        ser.write(f"<ERROR: {e}>".encode("ascii"))
    
    ser.write(b"\n")
    ser.flush()
    time.sleep(DELAY)

def main():
    print("="*60)
    print("AUTO-DÉTECTION ENCODAGE IMPRIMANTE A2")
    print("="*60)
    print(f"\nConnexion à {DEV} @ {BAUD}...")
    
    ser = serial.Serial(
        port=DEV,
        baudrate=BAUD,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1,
    )
    
    # Reset initial
    ser.write(b"\x1B\x40")
    time.sleep(0.2)
    
    ser.write(b"=== AUTO-DETECTION ===\n")
    time.sleep(0.1)
    
    # Tests systématiques - seulement les tests GB18030 qui fonctionnent partiellement
    tests = [
        # (nom, R, t, encodage)
        ("GB18030 default", None, None, "gb18030"),
        ("GB18030 R=1 t=1", 1, 1, "gb18030"),
    ]
    
    print("Lancement des tests...\n")
    for name, R, t, enc in tests:
        print(f"  Test: {name}")
        test_encoding(ser, name, R, t, enc, TEST_TEXT)
    
    # Test spécial: GB18030 caractère par caractère (mode par défaut)
    print("  Test: GB18030 individuel (default)")
    ser.write(b"\x1B\x40")
    time.sleep(0.1)
    # Pas de ESC R ni ESC t
    ser.write(b"[GB18030 individuel] ")
    for char in TEST_CHARS:
        try:
            encoded = char.encode("gb18030", errors="replace")
            ser.write(encoded)
            ser.write(b" ")
        except:
            pass
    ser.write(b"\n")
    ser.flush()
    time.sleep(DELAY)
    
    # Fin
    ser.write(b"=== FIN ===\n")
    ser.close()
    
    print("\n" + "="*60)
    print("TESTS TERMINÉS!")
    print("="*60)
    print("\nINSTRUCTIONS:")
    print("1. Regarde le ticket imprimé")
    print("2. Identifie quelle ligne affiche correctement les accents")
    print("3. Note le nom de la configuration (ex: 'GB18030 R=1 t=1')")
    print("4. Utilise cette configuration dans escpos.py")
    print("\nSi toutes les lignes montrent du chinois, l'imprimante")
    print("est probablement en mode GB18030 par défaut et il faut")
    print("utiliser GB18030 pour encoder le texte.")

if __name__ == "__main__":
    main()
