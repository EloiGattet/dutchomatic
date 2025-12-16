#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import serial

DEV = "/dev/serial0"
BAUD = 9600
DELAY = 0.5   # Délai entre chaque ligne

# Caractères à tester individuellement (selon doc A2 PC850)
# D'après la doc: PC850 contient: Ç, ü, é, â, ä, à, ç, ê, ë, è, i, Ä, Â, É, etc.
TEST_CHARS = [
    "a", "e", "i", "o", "u",  # Base
    "à", "é", "è", "ê", "ë",  # Accents e
    "ï", "ô", "ù", "ç",       # Autres
    "É", "À", "Ç",            # Majuscules
]

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

    # Reset initial
    ser.write(b"\x1B\x40")
    time.sleep(0.5)
    
    ser.write(b"\n=== TEST ACCENTS SELON DOC A2 ===\n\n")
    time.sleep(0.2)

    # D'après la doc A2:
    # ESC R n: 0=USA, 1=France, 2=Germany, etc.
    # ESC t n: 0=437, 1=850
    
    # Tests 1 à 9 commentés - ne fonctionnent pas (que du chinois)
    # # Test 1: R=1 (France) + t=1 (PC850) + encodage cp850
    # print("Test 1: R=1 (France) + t=1 (PC850) + cp850")
    # ser.write(b"\x1B\x40")  # Reset
    # time.sleep(0.1)
    # ser.write(b"\x1B\x52\x01")  # ESC R 1 (France)
    # time.sleep(0.05)
    # ser.write(b"\x1B\x74\x01")  # ESC t 1 (PC850)
    # time.sleep(0.1)
    # 
    # ser.write(b"[R=1 t=1 cp850] ")
    # for char in TEST_CHARS:
    #     try:
    #         encoded = char.encode("cp850", errors="replace")
    #         ser.write(encoded)
    #         ser.write(b" ")
    #     except:
    #         pass
    # ser.write(b"\n")
    # ser.flush()
    # time.sleep(DELAY)
    # 
    # # Test 2: R=1 (France) + t=0 (PC437) + encodage cp437
    # print("Test 2: R=1 (France) + t=0 (PC437) + cp437")
    # ser.write(b"\x1B\x40")  # Reset
    # time.sleep(0.1)
    # ser.write(b"\x1B\x52\x01")  # ESC R 1 (France)
    # time.sleep(0.05)
    # ser.write(b"\x1B\x74\x00")  # ESC t 0 (PC437)
    # time.sleep(0.1)
    # 
    # ser.write(b"[R=1 t=0 cp437] ")
    # for char in TEST_CHARS:
    #     try:
    #         encoded = char.encode("cp437", errors="replace")
    #         ser.write(encoded)
    #         ser.write(b" ")
    #     except:
    #         pass
    # ser.write(b"\n")
    # ser.flush()
    # time.sleep(DELAY)
    # 
    # # Test 3: R=0 (USA) + t=1 (PC850) + encodage cp850
    # print("Test 3: R=0 (USA) + t=1 (PC850) + cp850")
    # ser.write(b"\x1B\x40")  # Reset
    # time.sleep(0.1)
    # ser.write(b"\x1B\x52\x00")  # ESC R 0 (USA)
    # time.sleep(0.05)
    # ser.write(b"\x1B\x74\x01")  # ESC t 1 (PC850)
    # time.sleep(0.1)
    # 
    # ser.write(b"[R=0 t=1 cp850] ")
    # for char in TEST_CHARS:
    #     try:
    #         encoded = char.encode("cp850", errors="replace")
    #         ser.write(encoded)
    #         ser.write(b" ")
    #     except:
    #         pass
    # ser.write(b"\n")
    # ser.flush()
    # time.sleep(DELAY)
    # 
    # # Test 4: Test avec texte complet
    # print("Test 4: Texte complet avec R=1 t=1 cp850")
    # ser.write(b"\x1B\x40")  # Reset
    # time.sleep(0.1)
    # ser.write(b"\x1B\x52\x01")  # ESC R 1 (France)
    # time.sleep(0.05)
    # ser.write(b"\x1B\x74\x01")  # ESC t 1 (PC850)
    # time.sleep(0.1)
    # 
    # test_text = "Accents: a e i o u a e e e e i o u c E A C"
    # ser.write(b"[Texte] ")
    # ser.write(test_text.encode("ascii"))
    # ser.write(b"\n")
    # ser.flush()
    # time.sleep(DELAY)
    # 
    # # Test 5: Test avec bytes bruts PC850 (selon table doc)
    # print("Test 5: Bytes bruts PC850 (selon table doc)")
    # ser.write(b"\x1B\x40")  # Reset
    # time.sleep(0.1)
    # ser.write(b"\x1B\x52\x01")  # ESC R 1 (France)
    # time.sleep(0.05)
    # ser.write(b"\x1B\x74\x01")  # ESC t 1 (PC850)
    # time.sleep(0.1)
    # 
    # # D'après la doc PC850:
    # # 0x82 = é, 0x85 = à, 0x87 = ç, 0x88 = è, 0x89 = ê, 0x8A = ë
    # # 0x8B = ï, 0x93 = ô, 0x97 = ù
    # # 0x90 = É, 0xB7 = À, 0x80 = Ç
    # ser.write(b"[Bytes bruts] ")
    # ser.write(bytes([0x82]))  # é
    # ser.write(b" ")
    # ser.write(bytes([0x85]))  # à
    # ser.write(b" ")
    # ser.write(bytes([0x87]))  # ç
    # ser.write(b" ")
    # ser.write(bytes([0x88]))  # è
    # ser.write(b" ")
    # ser.write(bytes([0x89]))  # ê
    # ser.write(b" ")
    # ser.write(bytes([0x8A]))  # ë
    # ser.write(b" ")
    # ser.write(bytes([0x8B]))  # ï
    # ser.write(b" ")
    # ser.write(bytes([0x93]))  # ô
    # ser.write(b" ")
    # ser.write(bytes([0x97]))  # ù
    # ser.write(b" ")
    # ser.write(bytes([0x90]))  # É
    # ser.write(b" ")
    # ser.write(bytes([0xB7]))  # À
    # ser.write(b" ")
    # ser.write(bytes([0x80]))  # Ç
    # ser.write(b"\n")
    # ser.flush()
    # time.sleep(DELAY)
    # 
    # # Test 6: GB18030 (hypothèse: l'imprimante interprète en chinois)
    # print("Test 6: GB18030 (test si mode chinois actif)")
    # ser.write(b"\x1B\x40")  # Reset
    # time.sleep(0.1)
    # ser.write(b"\x1B\x52\x01")  # ESC R 1 (France)
    # time.sleep(0.05)
    # ser.write(b"\x1B\x74\x01")  # ESC t 1 (PC850)
    # time.sleep(0.1)
    # 
    # ser.write(b"[GB18030] ")
    # test_text_gb = "Éléoï ça à é è ê ë ï ô ù ç"
    # try:
    #     payload_gb = test_text_gb.encode("gb18030", errors="replace")
    #     ser.write(payload_gb)
    # except:
    #     pass
    # ser.write(b"\n")
    # ser.flush()
    # time.sleep(DELAY)
    # 
    # # Test 7: Test si octet >= 0x80 bascule en mode chinois
    # print("Test 7: Test bascule mode chinois (octets 0x80-0xFF)")
    # ser.write(b"\x1B\x40")  # Reset
    # time.sleep(0.1)
    # ser.write(b"\x1B\x52\x01")  # ESC R 1 (France)
    # time.sleep(0.05)
    # ser.write(b"\x1B\x74\x01")  # ESC t 1 (PC850)
    # time.sleep(0.1)
    # 
    # ser.write(b"[Test bascule] ASCII OK? ")
    # # Envoyer d'abord ASCII pur
    # ser.write(b"ABC ")
    # # Puis un octet haut-bit isolé (0x82 = é en CP850)
    # ser.write(b"->")
    # ser.write(bytes([0x82]))
    # ser.write(b"<- ")
    # # Puis plusieurs octets haut-bit
    # ser.write(b"->")
    # ser.write(bytes([0x82, 0x85, 0x87]))  # é à ç en CP850
    # ser.write(b"<-")
    # ser.write(b"\n")
    # ser.flush()
    # time.sleep(DELAY)
    # 
    # # Test 8: Test avec seulement ASCII pour vérifier que le header est lisible
    # print("Test 8: ASCII pur (vérification header)")
    # ser.write(b"\x1B\x40")  # Reset
    # time.sleep(0.1)
    # ser.write(b"\x1B\x52\x01")  # ESC R 1 (France)
    # time.sleep(0.05)
    # ser.write(b"\x1B\x74\x01")  # ESC t 1 (PC850)
    # time.sleep(0.1)
    # 
    # ser.write(b"[ASCII only] Accents: a e i o u (sans accents)\n")
    # ser.flush()
    # time.sleep(DELAY)
    # 
    # # Test 9: Test GB18030 avec R=1 t=1 (même config que CP850)
    # print("Test 9: GB18030 avec R=1 t=1")
    # ser.write(b"\x1B\x40")  # Reset
    # time.sleep(0.1)
    # ser.write(b"\x1B\x52\x01")  # ESC R 1 (France)
    # time.sleep(0.05)
    # ser.write(b"\x1B\x74\x01")  # ESC t 1 (PC850) - même si on encode en GB18030
    # time.sleep(0.1)
    # 
    # ser.write(b"[R=1 t=1 GB18030] ")
    # try:
    #     payload_gb2 = test_text_gb.encode("gb18030", errors="replace")
    #     ser.write(payload_gb2)
    # except:
    #     pass
    # ser.write(b"\n")
    # ser.flush()
    # time.sleep(DELAY)
    
    # Test 10: Test GB18030 sans config R/t (mode par défaut)
    print("Test 10: GB18030 mode par défaut (sans R/t)")
    ser.write(b"\x1B\x40")  # Reset
    time.sleep(0.1)
    # Pas de ESC R ni ESC t
    
    ser.write(b"[Default GB18030] ")
    try:
        payload_gb3 = test_text_gb.encode("gb18030", errors="replace")
        ser.write(payload_gb3)
    except:
        pass
    ser.write(b"\n")
    ser.flush()
    time.sleep(DELAY)
    
    # Test 11: Test GB18030 caractère par caractère (mode par défaut)
    print("Test 11: GB18030 caractère par caractère (mode par défaut)")
    ser.write(b"\x1B\x40")  # Reset
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

    # fin ticket
    ser.write(b"\n\n=== FIN DES TESTS ===\n\n")
    ser.close()

    print("\n" + "="*60)
    print("TESTS TERMINÉS!")
    print("="*60)
    print("\nVérifie sur le ticket:")
    print("1. Le Test 10 (GB18030 default) affiche-t-il des accents corrects?")
    print("2. Le Test 11 (GB18030 individuel) montre quels caractères fonctionnent?")
    print("\nSi GB18030 fonctionne partiellement, c'est que l'imprimante")
    print("interprète en mode chinois par défaut.")

if __name__ == "__main__":
    main()
