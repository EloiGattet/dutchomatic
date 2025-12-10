#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime
from escpos.printer import Serial
from PIL import Image

MAX_WIDTH = 384
LOGO_PATH = "data/logo_print.png"

# --------------------------------------------------------------------
def log(msg: str):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

# --------------------------------------------------------------------
def resize(img):
    w, h = img.size
    if w > MAX_WIDTH:
        ratio = MAX_WIDTH / w
        img = img.resize((MAX_WIDTH, int(h * ratio)), Image.LANCZOS)
    return img.convert("1")  # N&B

# --------------------------------------------------------------------
def apply_heating_params(p, n1, n2, n3):
    """
    ESC 7 n1 n2 n3 = réglage du chauffage
    n1 = heating dots (0-255, default: 7)
    n2 = heating time (3-255, default: 80)
    n3 = heating interval (0-255, default: 2)
    """
    p._raw(b'\x1B\x37' + bytes([n1, n2, n3]))

# --------------------------------------------------------------------
def apply_density(p, density, breaktime):
    """
    DC2 # n = réglage densité et breaktime
    density: 0-31 (D4-D0)
    breaktime: 0-7 (D7-D5)
    n = (breaktime << 5) + density
    """
    n = (breaktime << 5) + density
    p._raw(b'\x12\x23' + bytes([n]))

# --------------------------------------------------------------------
def print_logo_with_settings(p, img, name, n1, n2, n3, breaktime=None, density=None):
    log(f"--- Impression {name} ---")
    log(f"Heating: n1={n1}, n2={n2}, n3={n3}")
    if breaktime is not None and density is not None:
        log(f"Density: {density}, Breaktime: {breaktime}")
    
    apply_heating_params(p, n1, n2, n3)
    if breaktime is not None and density is not None:
        apply_density(p, density, breaktime)
    
    p.text(f"\nRéglage: {name}\n")
    p.image(img)
    p.text("\n\n")

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

# Patch du profil pour éviter le warning "media.width.pixel"
# et permettre le centrage automatique
try:
    if hasattr(p, "profile") and hasattr(p.profile, "media"):
        p.profile.media.setdefault("width", {})
        p.profile.media["width"]["pixels"] = 384  # largeur utile (8 dots/mm × 48mm)
        p.profile.media["width"]["mm"] = 48
        log("Profil imprimante patché: media.width.pixel = 384")
except Exception as e:
    log(f"Impossible de patcher le profil: {e}")

log("Imprimante connectée.")

# Configuration du codepage pour supporter les accents (CP858 = européen)
try:
    p.charcode('CP858')
    log("Codepage CP858 configuré (support accents)")
except Exception as e:
    log(f"Impossible de configurer le codepage: {e}")

# Charger & préparer l'image
log("Chargement du logo...")
img = Image.open(LOGO_PATH)
img = resize(img)
log("Logo prêt.")

# --------------------------------------------------------------------
# 🔥 LES 2 MEILLEURS RÉGLAGES (basés sur les tests)
# --------------------------------------------------------------------
# Profil 1 : OPTIMAL (noir profond, qualité maximale)
#   - heating_dots=7, heating_time=80, interval=2
#   - density=15, breaktime=0
#
# Profil 2 : USINE (pour comparaison - gris moche)
#   - heating_dots=7, heating_time=80, interval=2
#   - density=31, breaktime=7

profiles = [
    ("TEST 1 ", 7, 180, 2, 0, 31),
    ("TEST 2",  7, 180, 2, 0, 15),
]

# --------------------------------------------------------------------
# Impression des 2 meilleurs profils
# --------------------------------------------------------------------

for name, n1, n2, n3, bt, de in profiles:
    print_logo_with_settings(p, img, name, n1, n2, n3, breaktime=bt, density=de)
    time.sleep(0.5)  # petite pause pour éviter surchauffe

# --------------------------------------------------------------------
log("Fin des tests — coupe du papier.")
try:
    p.cut()
except:
    log("Pas de cutter.")

p.close()
log("Fini.")
