#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test complet pour miniescpos.py
Teste toutes les fonctionnalités: images, emojis, fonts, styles, accents, etc.
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from PIL import Image

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.printer.miniescpos import MiniEscpos


def log(msg: str):
    """Affiche un message avec timestamp."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def test_miniescpos():
    """Test complet de toutes les fonctionnalités de MiniEscpos."""
    
    log("=" * 60)
    log("TEST COMPLET - MiniEscpos")
    log("=" * 60)
    
    # Chemins
    logo_path = Path(__file__).parent.parent / "data" / "logo_print.png"
    font_path = Path(__file__).parent.parent / "fonts" / "Roboto-Bold.ttf"
    fonts_dir = Path(__file__).parent.parent / "fonts"
    
    # Fonts emoji à tester (comme dans test_python-escpos.py)
    emoji_fonts = [
        fonts_dir / "NotoColorEmoji.ttf",
        fonts_dir / "NotoEmoji-Regular.ttf",
        fonts_dir / "Segoe UI Emoji.ttf",
    ]
    
    try:
        # Initialisation avec codepage et international pour les accents
        log("Connexion à l'imprimante...")
        printer = MiniEscpos(
            dev="/dev/serial0",
            baudrate=9600,
            width_px=384,
            default_encoding="cp850",
            default_font_path=str(font_path) if font_path.exists() else None,
            codepage="cp850",
            international="FRANCE",
        )
        log("Imprimante connectée (CP850 + FRANCE pour accents).")
        
        # ============================================================
        # 1. TEST IMAGE (commenté - ça marche déjà)
        # ============================================================
        # log("\n--- TEST 1: Impression d'image (logo) ---")
        # if logo_path.exists():
        #     log(f"Chargement: {logo_path}")
        #     img = Image.open(logo_path)
        #     
        #     # Application des bons réglages pour les images
        #     # (TEST 2: 7, 180, 2, 0, 15)
        #     printer.set_heating(n1=7, n2=180, n3=2)
        #     printer.set_density(density=15, breaktime=0)
        #     log("Réglages appliqués: heating(7, 180, 2), density(15, 0)")
        #     
        #     printer.set_align("center")
        #     printer.print_image(img)
        #     printer.lf(2)
        #     log("✓ Image imprimée")
        # else:
        #     log(f"✗ Logo non trouvé: {logo_path}")
        # 
        # time.sleep(0.5)
        
        # ============================================================
        # 2. TEST SÉPARATEURS
        # ============================================================
        log("\n--- TEST 2: Séparateurs ---")
        printer.separator(char="-", double=False)
        printer.separator(char="═", double=True)
        printer.separator(char="_", double=False)
        printer.lf(1)
        log("✓ Séparateurs testés")
        
        # ============================================================
        # 3. TEST ACCENTS (IMPORTANT!)
        # ============================================================
        log("\n--- TEST 3: Accents et caractères spéciaux ---")
        printer.set_align("left")
        printer.set_text_style()  # reset style
        
        # Test avec n=1 (par défaut)
        log("Test avec CP850 n=1 (A2)...")
        printer.line("Accents FR (n=1): à é è ê ë ï ô ù ç €")
        printer.line("Majuscules: É È Ê Ë À Â Ä Ç Ù Û Ü Ô Ö Î Ï")
        printer.line("Texte avec accents: Éléoï")
        printer.lf(1)
        
        # Essayer aussi avec n=2 (standard ESC/POS) si n=1 ne fonctionne pas
        log("Test avec CP850 n=2 (standard ESC/POS)...")
        printer.set_codepage("cp850", try_alternative=False)  # Force n=2
        printer.line("Accents FR (n=2): à é è ê ë ï ô ù ç €")
        printer.line("Texte avec accents: Éléoï")
        printer.lf(1)
        
        # Revenir à n=1
        printer.set_codepage("cp850", try_alternative=True)
        log("✓ Accents testés (n=1 et n=2)")
        
        # ============================================================
        # 4. TEST FONTS INTERNES A et B - TAILLES (commenté)
        # ============================================================
        # log("\n--- TEST 4: Fonts internes A et B (tailles) ---")
        # 
        # # Font A - Normal
        # printer.set_text_style(font="A", size="normal")
        # printer.line("Font A - Normal")
        # 
        # # Font A - Double width
        # printer.set_text_style(font="A", size="dw")
        # printer.line("Font A - Double Width")
        # 
        # # Font A - Double height
        # printer.set_text_style(font="A", size="dh")
        # printer.line("Font A - Double Height")
        # 
        # # Font A - Double size
        # printer.set_text_style(font="A", size="ds")
        # printer.line("Font A - Double Size")
        # printer.lf(1)
        # 
        # # Font B - Normal
        # printer.set_text_style(font="B", size="normal")
        # printer.line("Font B - Normal (condensée)")
        # 
        # # Font B - Double width
        # printer.set_text_style(font="B", size="dw")
        # printer.line("Font B - Double Width")
        # 
        # # Font B - Double height
        # printer.set_text_style(font="B", size="dh")
        # printer.line("Font B - Double Height")
        # 
        # # Font B - Double size
        # printer.set_text_style(font="B", size="ds")
        # printer.line("Font B - Double Size")
        # printer.lf(1)
        # 
        # # Reset à normal
        # printer.set_text_style(font="A", size="normal")
        # log("✓ Fonts A et B testées (toutes tailles)")
        
        # Fonts A et B - Normal seulement
        log("\n--- TEST 4: Fonts internes A et B (normal) ---")
        printer.set_text_style(font="A", size="normal")
        printer.line("Font A - Normal")
        printer.set_text_style(font="B", size="normal")
        printer.line("Font B - Normal (condensée)")
        printer.set_text_style(font="A", size="normal")
        printer.lf(1)
        log("✓ Fonts A et B testées (normal)")
        
        # ============================================================
        # 5. TEST STYLES (GRAS, SOULIGNÉ) - COMMENTÉ
        # ============================================================
        # log("\n--- TEST 5: Styles (gras, souligné) ---")
        # 
        # # Normal
        # printer.set_text_style(font="A", size="normal", bold=False, underline=False)
        # printer.line("Texte normal")
        # 
        # # Gras
        # printer.set_text_style(bold=True)
        # printer.line("Texte en GRAS")
        # 
        # # Souligné
        # printer.set_text_style(bold=False, underline=True)
        # printer.line("Texte souligné")
        # 
        # # Gras + Souligné
        # printer.set_text_style(bold=True, underline=True)
        # printer.line("Texte GRAS et souligné")
        # 
        # # Reset
        # printer.set_text_style(bold=False, underline=False)
        # printer.lf(1)
        # log("✓ Styles testés (gras, souligné)")
        
        # ============================================================
        # 6. TEST CENTRAGE
        # ============================================================
        log("\n--- TEST 6: Centrage ---")
        printer.set_align("left")
        printer.line("Alignement à gauche")
        printer.lf(1)
        
        printer.set_align("center")
        printer.line("Texte centré")
        printer.lf(1)
        
        printer.set_align("right")
        printer.line("Alignement à droite")
        printer.lf(1)
        
        printer.set_align("left")
        log("✓ Centrage testé")
        
        # ============================================================
        # 7. TEST HELPER CENTERED_TEXT
        # ============================================================
        log("\n--- TEST 7: Helper centered_text ---")
        printer.centered_text("Titre centré avec helper")
        printer.lf(1)
        printer.centered_text("Sous-titre centré")
        printer.lf(1)
        log("✓ Helper centered_text testé")
        
        # ============================================================
        # 8. TEST FONT CUSTOM (Roboto-Bold) - 48px
        # ============================================================
        log("\n--- TEST 8: Font custom (Roboto-Bold) - 48px ---")
        if font_path.exists():
            printer.print_text_image(
                text="Font Custom: Roboto-Bold\nTaille 48px\n\nAvec accents: é è à ç Éléoï",
                font_size=48,
                font_path=str(font_path),
                align="center"
            )
            printer.lf(1)
            log("✓ Font custom testée (48px)")
        else:
            log(f"✗ Font custom non trouvée: {font_path}")
        
        # ============================================================
        # 9. TEST EMOJIS (toutes les fonts disponibles)
        # ============================================================
        log("\n--- TEST 9: Emojis avec différentes fonts ---")
        emojis_text = "Emojis: 🎉 ✅ 🚀 🎯 🏆 ⭐ 💯 🔥 😄"
        
        emoji_font_found = False
        for emoji_font_path in emoji_fonts:
            if emoji_font_path.exists():
                log(f"Test avec: {emoji_font_path.name}")
                # Tester avec différentes tailles pour voir si ça change
                for emoji_size in [32, 48]:
                    printer.print_text_image(
                        text=f"{emoji_font_path.name} {emoji_size}px\n{emojis_text}",
                        font_size=emoji_size,
                        font_path=str(emoji_font_path),
                        align="center"
                    )
                    printer.lf(1)
                emoji_font_found = True
            else:
                log(f"✗ Font emoji non trouvée: {emoji_font_path.name}")
        
        if not emoji_font_found:
            log("⚠ Aucune font emoji trouvée, test avec font par défaut")
            printer.print_text_image(
                text="Emojis (sans font spéciale): 🎉 ✅ 🚀\nLes emojis peuvent apparaître comme des carrés",
                font_size=32,
                align="center"
            )
        else:
            log("✓ Emojis testés avec toutes les fonts disponibles")
        
        # ============================================================
        # 10. TEST HELPERS HAUT NIVEAU
        # ============================================================
        log("\n--- TEST 10: Helpers haut niveau ---")
        
        # print_title
        printer.print_title(
            "Titre avec print_title",
            font_size=28,
            font_path=str(font_path) if font_path.exists() else None,
            separator=True
        )
        
        # print_paragraph
        printer.print_paragraph(
            "Ceci est un paragraphe de test\navec plusieurs lignes\npour vérifier le rendu.",
            font_size=20,
            font_path=str(font_path) if font_path.exists() else None,
            align="left"
        )
        
        # print_key_value
        printer.separator()
        printer.print_key_value("Clé 1", "Valeur 1")
        printer.print_key_value("Clé 2", "Valeur 2 avec accents: é è à")
        printer.print_key_value("Clé très longue qui devrait être tronquée", "Valeur")
        printer.lf(1)
        log("✓ Helpers haut niveau testés")
        
        # ============================================================
        # 11. TEST COMBINAISONS COMPLEXES (commenté - double size)
        # ============================================================
        # log("\n--- TEST 11: Combinaisons complexes ---")
        # printer.separator(char="═", double=True)
        # printer.centered_text("COMBINAISONS")
        # printer.separator(char="═", double=True)
        # printer.lf(1)
        # 
        # # Font B + Gras + Double height
        # printer.set_text_style(font="B", bold=True, size="dh")
        # printer.centered_text("Font B + Gras + Double Height")
        # printer.lf(1)
        # 
        # # Font A + Souligné + Double width
        # printer.set_text_style(font="A", underline=True, size="dw")
        # printer.centered_text("Font A + Souligné + Double Width")
        # printer.lf(1)
        # 
        # # Reset
        # printer.set_text_style(font="A", size="normal", bold=False, underline=False)
        # printer.lf(1)
        # log("✓ Combinaisons complexes testées")
        
        # ============================================================
        # 11. TEST COMBINAISONS SIMPLES (gras/souligné) - COMMENTÉ
        # ============================================================
        # log("\n--- TEST 11: Combinaisons simples ---")
        # printer.separator(char="═", double=True)
        # printer.centered_text("COMBINAISONS")
        # printer.separator(char="═", double=True)
        # printer.lf(1)
        # 
        # # Font B + Gras
        # printer.set_text_style(font="B", bold=True)
        # printer.centered_text("Font B + Gras")
        # printer.lf(1)
        # 
        # # Font A + Souligné
        # printer.set_text_style(font="A", underline=True, bold=False)
        # printer.centered_text("Font A + Souligné")
        # printer.lf(1)
        # 
        # # Reset
        # printer.set_text_style(font="A", size="normal", bold=False, underline=False)
        # printer.lf(1)
        # log("✓ Combinaisons simples testées")
        
        # ============================================================
        # 12. TEST FINAL - RÉCAPITULATIF
        # ============================================================
        log("\n--- TEST 12: Récapitulatif ---")
        printer.separator(char="═", double=True)
        printer.centered_text("RÉCAPITULATIF DES TESTS")
        printer.separator(char="═", double=True)
        printer.lf(1)
        
        printer.set_text_style(font="A", size="normal")
        printer.line("✓ Séparateurs (═══, ____)")
        printer.line("✓ Accents et caractères spéciaux (CP850 + FRANCE)")
        printer.line("✓ Fonts A et B (normal)")
        printer.line("✓ Centrage (left, center, right)")
        printer.line("✓ Font custom (Roboto-Bold 24-64px)")
        printer.line("✓ Emojis (NotoColorEmoji, NotoEmoji, Segoe UI)")
        printer.line("✓ Helpers haut niveau")
        printer.lf(2)
        
        printer.centered_text("Tests terminés avec succès! ✓")
        printer.lf(2)
        
        # ============================================================
        # COUPE DU PAPIER
        # ============================================================
        log("\n--- Coupe du papier ---")
        printer.cut(full=True)
        log("✓ Papier coupé")
        
        # Fermeture
        printer.close()
        log("Imprimante fermée.")
        
        log("\n" + "=" * 60)
        log("TOUS LES TESTS TERMINÉS AVEC SUCCÈS!")
        log("=" * 60)
        return 0
        
    except Exception as e:
        log(f"✗ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_miniescpos())
