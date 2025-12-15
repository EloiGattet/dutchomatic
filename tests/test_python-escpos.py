#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime

print("Lancement du programme de test d'impression")
print("Importation des modules...")
from escpos.printer import Serial
from PIL import Image, ImageDraw, ImageFont
print("Modules importés")

# === CONFIG GLOBALE ===
MAX_WIDTH = 384          # largeur max en pixels de l'imprimante (à adapter si besoin)
LOGO_PATH = "data/logo_print.png"
CUSTOM_FONT_PATH = "Roboto-Bold.ttf"  # à adapter selon où tu mets ta font

start_time = time.perf_counter()


def log(msg: str) -> None:
    """Log avec timestamp + temps écoulé."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elapsed = time.perf_counter() - start_time
    print(f"[{now} +{elapsed:7.3f}s] {msg}", flush=True)


def resize_for_printer(img: Image.Image, max_width: int = MAX_WIDTH) -> Image.Image:
    """Redimensionne l'image pour qu'elle tienne dans la largeur de l'imprimante."""
    w, h = img.size
    if w > max_width:
        ratio = max_width / float(w)
        new_size = (max_width, int(h * ratio))
        log(f"Redimensionnement de l'image de {w}x{h} -> {new_size[0]}x{new_size[1]}")
        img = img.resize(new_size, Image.LANCZOS)
    else:
        log(f"Aucun redimensionnement nécessaire ({w}px ≤ {max_width}px)")
    return img


def text_to_image(text: str, font: ImageFont.FreeTypeFont, padding: int = 4) -> Image.Image:
    """Rend du texte dans une image en niveaux de gris puis la renvoie."""
    # getbbox renvoie (x0, y0, x1, y1)
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    img = Image.new("L", (w + 2 * padding, h + 2 * padding), 255)
    draw = ImageDraw.Draw(img)
    draw.text((padding, padding), text, font=font, fill=0)
    return img


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Charge une font custom, ou la font par défaut en cas d'échec."""
    try:
        font = ImageFont.truetype(path, size)
        log(f"Police custom chargée: '{path}' ({size}px)")
        return font
    except Exception as e:
        log(f"⚠ Impossible de charger la police '{path}': {e}")
        log("➡ Utilisation de la police par défaut PIL.")
        return ImageFont.load_default()


def load_emoji_font(size: int) -> ImageFont.FreeTypeFont:
    """Essaie de charger une police emoji, sinon fallback sur la police par défaut."""
    candidates = [
        "NotoEmoji-Bold.ttf",
        "NotoEmoji-Regular.ttf",
        "Segoe UI Emoji.ttf",
        CUSTOM_FONT_PATH,  # en dernier recours, la même que le texte custom
    ]
    for path in candidates:
        try:
            font = ImageFont.truetype(path, size)
            log(f"Police emoji trouvée: '{path}' ({size}px)")
            return font
        except Exception:
            continue
    log("⚠ Aucune police emoji dédiée trouvée, utilisation de la police par défaut (les emojis peuvent être moches ou des carrés).")
    return ImageFont.load_default()


log("Connexion à l'imprimante...")
p = None

try:
    # 1. Connexion à l'imprimante
    p = Serial(
        devfile='/dev/serial0',
        baudrate=9600,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=1
    )
    log("Imprimante connectée")

    # 2. Impression d'un logo depuis un fichier
    try:
        log(f"Chargement de l'image logo: {LOGO_PATH}")
        img = Image.open(LOGO_PATH)
        log(f"Image chargée: {img.size[0]}x{img.size[1]}")

        img = resize_for_printer(img, MAX_WIDTH)

        log("Conversion du logo en niveaux de gris puis noir & blanc (dithering)...")
        t0 = time.perf_counter()
        img = img.convert("L")
        img = img.convert("1")  # Floyd-Steinberg par défaut
        t1 = time.perf_counter()
        log(f"Conversion logo terminée en {t1 - t0:0.3f}s")

        log("Impression du logo...")
        t0 = time.perf_counter()
        p.image(img)
        t1 = time.perf_counter()
        log(f"Logo imprimé en {t1 - t0:0.3f}s")
        p.text("\n")
    except Exception as e:
        log(f"⚠ Erreur lors de l'impression du logo: {e}")

    # 3. Test texte brut avec accents + codepage
    log("Configuration de la page de caractères (codepage) pour les accents...")
    try:
        p.charcode('CP858')  # à adapter si ta printer préfère CP850 / CP437...
        log("Codepage définie sur CP858")
    except Exception as e:
        log(f"⚠ Impossible de changer la codepage: {e}")

    log("Impression de texte brut avec accents...")
    t0 = time.perf_counter()
    p.text("Texte brut avec accents : Éléoï — ça imprime bien ? € à ê ï ô ù\n\n")
    t1 = time.perf_counter()
    log(f"Texte brut imprimé en {t1 - t0:0.3f}s")

    # 4. Rendu de texte en font custom (via image)
    log("Rendu d'un texte avec police custom (image)...")
    custom_font = load_font(CUSTOM_FONT_PATH, 32)
    custom_text = "Hello Eloi ! Police custom"
    img_text = text_to_image(custom_text, custom_font, padding=4)
    img_text = resize_for_printer(img_text, MAX_WIDTH)

    log("Conversion texte custom en noir & blanc...")
    t0 = time.perf_counter()
    img_text = img_text.convert("1")
    t1 = time.perf_counter()
    log(f"Conversion texte custom terminée en {t1 - t0:0.3f}s")

    log("Impression du texte custom...")
    t0 = time.perf_counter()
    p.image(img_text)
    p.text("\n")
    t1 = time.perf_counter()
    log(f"Texte custom imprimé en {t1 - t0:0.3f}s")

    # 5. Test direct avec emojis dans le flux texte
    log("Impression directe de texte avec emoji (pour voir la réaction de l'imprimante)...")
    t0 = time.perf_counter()
    p.text("Texte direct avec emoji : Salut 😄🔥✨\n\n")
    t1 = time.perf_counter()
    log(f"Texte direct avec emojis envoyé en {t1 - t0:0.3f}s")

    # 6. Emoji rendus via image (font emoji si dispo)
    log("Rendu des emojis en image (via font emoji si disponible)...")
    emoji_font = load_emoji_font(40)
    emoji_text = "Emoji en image : 😄🔥✨"
    img_emoji = text_to_image(emoji_text, emoji_font, padding=4)
    img_emoji = resize_for_printer(img_emoji, MAX_WIDTH)

    log("Conversion emoji en noir & blanc...")
    t0 = time.perf_counter()
    img_emoji = img_emoji.convert("1")
    t1 = time.perf_counter()
    log(f"Conversion emoji terminée en {t1 - t0:0.3f}s")

    log("Impression des emojis en image...")
    t0 = time.perf_counter()
    p.image(img_emoji)
    p.text("\n")
    t1 = time.perf_counter()
    log(f"Emoji-image imprimés en {t1 - t0:0.3f}s")

    # 7. Ligne finale de test
    log("Impression d'une ligne finale de test...")
    t0 = time.perf_counter()
    p.text("Fin des tests — merci d'avoir imprimé 😁\n\n")
    t1 = time.perf_counter()
    log(f"Ligne finale imprimée en {t1 - t0:0.3f}s")

    # 8. Coupe du papier (si supporté)
    log("Demande de coupe du papier...")
    try:
        t0 = time.perf_counter()
        p.cut()
        t1 = time.perf_counter()
        log(f"Coupe papier exécutée en {t1 - t0:0.3f}s")
    except Exception as e:
        log(f"⚠ Erreur lors de la coupe du papier (peut être normal si non supporté): {e}")

    log("Tests d'impression terminés.")

except Exception as e:
    log(f"❌ ERREUR FATALE: {e}")

finally:
    if p is not None:
        try:
            p.close()
            log("Connexion à l'imprimante fermée proprement.")
        except Exception as e:
            log(f"⚠ Erreur lors de la fermeture de l'imprimante: {e}")
