#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime

# Chronométrage des imports
start_import = time.time()
from escpos.printer import Serial
elapsed_escpos = time.time() - start_import
print(f"[IMPORT] escpos.printer: {elapsed_escpos:.3f}s", flush=True)

start_import = time.time()
from PIL import Image, ImageDraw
elapsed_pil = time.time() - start_import
print(f"[IMPORT] PIL: {elapsed_pil:.3f}s", flush=True)

MAX_WIDTH = 384

# --------------------------------------------------------------------
def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

# --------------------------------------------------------------------
def create_test_patch():
    """Génère une bande noire (ou presque)."""
    img = Image.new("1", (MAX_WIDTH, 40), 1)  # 1 = blanc
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, MAX_WIDTH, 40), fill=0)  # noir plein
    return img

# --------------------------------------------------------------------
def apply_heating(p, n1, n2, n3):
    """
    ESC 7 n1 n2 n3
    n1 = heating dots      (on le fait varier)
    n2 = heating time      (constant ici)
    n3 = heating interval  (on le fait varier)
    """
    p._raw(b'\x1B\x37' + bytes([n1, n2, n3]))

# --------------------------------------------------------------------
def apply_density(p, density, breaktime):
    """
    DC2 # n
    density 0–31
    breaktime 0–7
    n = (breaktime << 5) + density
    """
    n = (breaktime << 5) + density
    p._raw(b'\x12\x23' + bytes([n]))

# --------------------------------------------------------------------
def print_profile(p, patch, n1, n2, n3, breaktime, density):
    log(f"Test: dots={n1}, time={n2}, interval={n3}, break={breaktime}, density={density}")

    start_time = time.time()
    
    apply_heating(p, n1=n1, n2=n2, n3=n3)
    apply_density(p, density=density, breaktime=breaktime)

    # Texte court pour ne pas être tronqué
    p.text(f"\n[d={n1} t={n2} i={n3} br={breaktime} de={density}]\n")
    # Imprimer la bande noire
    p.image(patch)
    
    # Attendre la fin de l'impression (flush)
    p._raw(b'\x0A')  # LF pour forcer le flush
    
    elapsed = time.time() - start_time
    log(f"  → Impression terminée en {elapsed:.3f}s")
    
    time.sleep(0.5)

# --------------------------------------------------------------------

log("Connexion à l'imprimante...")

p = Serial(
    devfile='/dev/serial0',
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)

# Patch du profil pour virer le warning et permettre le centrage
try:
    if hasattr(p, "profile") and hasattr(p.profile, "media"):
        p.profile.media.setdefault("width", {})
        p.profile.media["width"]["pixels"] = 384  # largeur utile
        # si tu veux, tu peux aussi fixer en mm
        p.profile.media["width"]["mm"] = 48
        log("Profil imprimante patché: media.width.pixel = 384")
except Exception as e:
    log(f"Impossible de patcher le profil: {e}")

log("Imprimante connectée.")

# Générer la bande noire
patch = create_test_patch()

# --------------------------------------------------------------------
# PARAMÈTRES OPTIMAUX (basés sur les tests)
# --------------------------------------------------------------------
# Tests 1-7 : TOUS BONS
# Tests 8-13 : TOUS MAUVAIS
#
# CONCLUSION :
# - dots=7 (CRITIQUE - ne pas changer)
# - interval=2 (CRITIQUE - ne pas changer)
# - density=12-18 (optimal=15)
# - breaktime=0-2 (optimal=0)
# - heating_time=60-100 (optimal=80)

# Profil de référence : valeurs par défaut usine (gris moche)
log("Impression du profil de référence (valeurs par défaut usine)...")
p.text("\n=== REFERENCE USINE (gris) ===\n")
print_profile(p, patch, n1=7, n2=80, n3=2, breaktime=7, density=31)
p.text("\n")

# Profil optimal : config qui fonctionne bien
log("Impression du profil optimal...")
p.text("\n=== PROFIL OPTIMAL ===\n")
p.text("dots=7, time=80, interval=2, break=0, density=15\n")
print_profile(p, patch, n1=7, n2=80, n3=2, breaktime=0, density=15)
p.text("\n")

# Paramètres optimaux à utiliser dans votre code
OPTIMAL_PARAMS = {
    'heating_dots': 7,      # CRITIQUE - ne pas changer
    'heating_time': 80,     # Plage 60-100 OK
    'interval': 2,           # CRITIQUE - ne pas changer
    'breaktime': 0,          # Optimal (0-2 OK)
    'density': 15            # Plage 12-18 OK
}

log(f"Paramètres optimaux : {OPTIMAL_PARAMS}")

log("Tests terminés. Coupe du papier.")
try:
    p.cut()
except Exception:
    pass

p.close()
log("Fini.")
