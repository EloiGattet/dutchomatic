#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test complet pour EscposPrinter
Teste toutes les fonctionnalités: images, emojis, fonts, styles, accents, etc.

Usage:
    python test_miniescpos.py                    # Tous les tests
    python test_miniescpos.py --list              # Lister les tests disponibles
    python test_miniescpos.py --test 2,3,6       # Tests par numéro
    python test_miniescpos.py --test accents,separators  # Tests par nom
"""

import sys
import argparse
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Callable, List
from PIL import Image

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.printer.escpos import EscposPrinter
from src.core.formatter import format_exercise, _format_box


def log(msg: str):
    """Affiche un message avec timestamp."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


# ============================================================================
# DÉFINITION DES TESTS
# ============================================================================

def get_paths():
    """Retourne les chemins des ressources."""
    base = Path(__file__).parent.parent
    return {
        "logo": base / "data" / "logo_print.png",
        "font": base / "fonts" / "Roboto-Bold.ttf",
        "fonts_dir": base / "fonts",
        "exercises": base / "data" / "exercises.json",
        "daily": base / "data" / "daily.json",
    }


def test_image(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 1: Impression d'image (logo)."""
    log("\n--- TEST 1: Impression d'image (logo) ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 1: Image")
    printer.set_text_style()
    logo_path = paths["logo"]
    if logo_path.exists():
        log(f"Chargement: {logo_path}")
        img = Image.open(logo_path)
        
        printer.set_heating(n1=7, n2=180, n3=2)
        printer.set_density(density=15, breaktime=0)
        log("Réglages appliqués: heating(7, 180, 2), density(15, 0)")
        
        printer.set_align("center")
        printer.print_image(img)
        printer.lf(2)
        log("✓ Image imprimée")
    else:
        log(f"✗ Logo non trouvé: {logo_path}")
    time.sleep(0.5)


def test_separators(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 2: Séparateurs."""
    log("\n--- TEST 2: Séparateurs ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 2: Separateurs")
    printer.set_text_style()
    printer.separator(char="-", double=False)
    printer.separator(char="═", double=True)
    printer.separator(char="_", double=False)
    printer.lf(1)
    log("✓ Séparateurs testés")


def test_accents(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 3: Accents et caractères spéciaux."""
    log("\n--- TEST 3: Accents et caractères spéciaux ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 3: Accents")
    printer.set_text_style()
    printer.set_align("left")
    printer.set_text_style()  # reset style
    
    log("Test avec CP850 n=1 (R=1, t=1)...")
    printer.line("Accents FR: à é è ê ë ï ô ù ç €")
    printer.line("Majuscules: É È Ê Ë À Â Ä Ç Ù Û Ü Ô Ö Î Ï")
    printer.line("Texte avec accents: Éléoï")
    log("✓ Accents testés")


def test_fonts_ab(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 4: Fonts internes A et B (normal)."""
    log("\n--- TEST 4: Fonts internes A et B (normal) ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 4: Fonts A/B")
    printer.set_text_style()
    printer.set_text_style(font="A", size="normal")
    printer.line("Font A - Normal")
    printer.set_text_style(font="B", size="normal")
    printer.line("Font B - Normal (condensée)")
    printer.set_text_style(font="A", size="normal")
    printer.lf(1)
    log("✓ Fonts A et B testées (normal)")


def test_styles(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 5: Styles (gras, souligné)."""
    log("\n--- TEST 5: Styles (gras, souligné) ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 5: Styles")
    printer.set_text_style()
    printer.set_text_style(font="A", size="normal", bold=False, underline=False)
    printer.line("Texte normal")
    
    printer.set_text_style(bold=True)
    printer.line("Texte en GRAS")
    
    printer.set_text_style(bold=False, underline=True)
    printer.line("Texte souligné")
    
    printer.set_text_style(bold=True, underline=True)
    printer.line("Texte GRAS et souligné")
    
    printer.set_text_style(bold=False, underline=False)
    printer.lf(1)
    log("✓ Styles testés (gras, souligné)")


def test_alignment(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 6: Centrage."""
    log("\n--- TEST 6: Centrage ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 6: Alignement")
    printer.set_text_style()
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


def test_centered_text(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 7: Helper centered_text."""
    log("\n--- TEST 7: Helper centered_text ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 7: Centered text")
    printer.set_text_style()
    printer.centered_text("Titre centré avec helper")
    printer.lf(1)
    printer.centered_text("Sous-titre centré")
    printer.lf(1)
    log("✓ Helper centered_text testé")


def test_custom_font(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 8: Font custom (Roboto-Bold) - 48px."""
    log("\n--- TEST 8: Font custom (Roboto-Bold) - 48px ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 8: Font custom")
    printer.set_text_style()
    font_path = paths["font"]
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


def test_emojis(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 9: Emojis avec différentes fonts."""
    log("\n--- TEST 9: Emojis avec différentes fonts ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 9: Emojis")
    printer.set_text_style()
    emojis_text = "Emojis: 🎉 ✅ 🚀 🎯 🏆 ⭐ 💯 🔥 😄"
    
    # Utiliser la détection automatique des fonts emoji
    emoji_fonts = EscposPrinter._find_emoji_fonts(str(paths["fonts_dir"]))
    
    emoji_font_found = False
    for emoji_font_path in emoji_fonts:
        from pathlib import Path
        font_path_obj = Path(emoji_font_path)
        if font_path_obj.exists():
            log(f"Test avec: {font_path_obj.name}")
            for emoji_size in [32, 48]:
                printer.print_text_image(
                    text=f"{font_path_obj.name} {emoji_size}px\n{emojis_text}",
                    font_size=emoji_size,
                    font_path=emoji_font_path,
                    align="center"
                )
                printer.lf(1)
            emoji_font_found = True
    
    if not emoji_font_found:
        log("⚠ Aucune font emoji trouvée, test avec font par défaut")
        printer.print_text_image(
            text="Emojis (sans font spéciale): 🎉 ✅ 🚀\nLes emojis peuvent apparaître comme des carrés",
            font_size=32,
            align="center"
        )
    else:
        log("✓ Emojis testés avec toutes les fonts disponibles")


def test_helpers(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 10: Helpers haut niveau."""
    log("\n--- TEST 10: Helpers haut niveau ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 10: Helpers")
    printer.set_text_style()
    font_path = paths["font"]
    
    printer.print_title(
        "Titre avec print_title",
        font_size=28,
        font_path=str(font_path) if font_path.exists() else None,
        separator=True
    )
    
    printer.print_paragraph(
        "Ceci est un paragraphe de test\navec plusieurs lignes\npour vérifier le rendu.",
        font_size=20,
        font_path=str(font_path) if font_path.exists() else None,
        align="left"
    )
    
    printer.separator()
    printer.print_key_value("Clé 1", "Valeur 1")
    printer.print_key_value("Clé 2", "Valeur 2 avec accents: é è à")
    printer.print_key_value("Clé très longue qui devrait être tronquée", "Valeur")
    printer.lf(1)
    log("✓ Helpers haut niveau testés")


def test_notoemoji(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 11: Test spécifique NotoEmoji."""
    log("\n--- TEST 11: NotoEmoji ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 11: NotoEmoji")
    printer.set_text_style()
    emoji_font_path = paths["fonts_dir"] / "NotoEmoji-Bold.ttf"
    roboto_font_path = paths["font"]
    
    emoji_sets = [
        ("Emojis de base", "🎉 ✅ 🚀 🎯 🏆 ⭐ 💯 🔥 😄"),
        ("Emojis visages", "😀 😃 😄 😁 😆 😅 🤣 😂 🥲"),
        ("Emojis objets", "📱 💻 🖥️ ⌚ 📷 📹 🎥 📺 📻"),
        ("Emojis nourriture", "🍕 🍔 🍟 🌭 🍿 🥓 🥚 🍳"),
        ("Emojis animaux", "🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼"),
    ]
    
    if not emoji_font_path.exists():
        log(f"✗ Font NotoEmoji-Bold non trouvée: {emoji_font_path}")
        log("⚠ Aucune font NotoEmoji trouvée")
        printer.print_text_image(
            text="NotoEmoji-Bold non disponible\nLes emojis peuvent apparaître comme des carrés",
            font_size=24,
            align="center"
        )
        return
    
    log(f"Utilisation de NotoEmoji-Bold: {emoji_font_path}")
    
    # Titre principal avec Roboto
    if roboto_font_path.exists():
        printer.print_title(
            "NotoEmoji-Bold Test",
            font_size=28,
            font_path=str(roboto_font_path),
            separator=True
        )
    else:
        printer.print_title(
            "NotoEmoji-Bold Test",
            font_size=28,
            separator=True
        )
    
    # Tester différents sets d'emojis avec titre en Roboto et emojis en NotoEmoji-Bold
    for set_name, emojis in emoji_sets:
        # Titre du set en Roboto
        if roboto_font_path.exists():
            printer.print_text_image(
                text=set_name + ":",
                font_size=20,
                font_path=str(roboto_font_path),
                align="left"
            )
        else:
            printer.print_text_image(
                text=set_name + ":",
                font_size=20,
                align="left"
            )
        
        # Emojis en NotoEmoji-Bold
        printer.print_text_image(
            text=emojis,
            font_size=28,
            font_path=str(emoji_font_path),
            align="left"
        )
        printer.lf(1)
    
    # Test avec texte mixte (français en Roboto + emojis en NotoEmoji-Bold)
    # Note: Pour le texte mixte, on utilise la font emoji qui devrait gérer les deux
    printer.print_text_image(
        text="Texte mixte:\nBonjour ! 😊 Comment ça va ? 🎉\nC'est super ! 🚀",
        font_size=24,
        font_path=str(emoji_font_path),
        align="left"
    )
    printer.lf(2)
    log("✓ Test NotoEmoji-Bold terminé")


def test_emoji_support_check(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 12: Vérification des emojis supportés (sans imprimer, économise le papier)."""
    log("\n--- TEST 12: Vérification support emojis (sans impression) ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 12: Support emojis")
    printer.set_text_style()
    # Liste étendue d'emojis à tester
    emoji_list = [
        "🎉", "✅", "🚀", "🎯", "🏆", "⭐", "💯", "🔥", "😄", "😊", "😁", "😆",
        "😅", "🤣", "😂", "🥲", "📱", "💻", "🖥️", "⌚", "📷", "📹", "🎥",
        "📺", "📻", "🍕", "🍔", "🍟", "🌭", "🍿", "🥓", "🥚", "🍳", "🐶",
        "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "💡", "📝", "✓", "✗",
        "😀", "😃", "🎮", "🎲", "🎨", "🎭", "🎪", "🎬", "🎤", "🎧", "🎵",
        "🎶", "🏠", "🏡", "🏢", "🏣", "🏤", "🏥", "🏦", "🏧", "🏨", "🏩",
    ]
    
    # Tester avec toutes les fonts emoji disponibles
    emoji_fonts = EscposPrinter._find_emoji_fonts(str(paths["fonts_dir"]))
    
    if not emoji_fonts:
        log("⚠ Aucune font emoji trouvée")
        log("Test avec font par défaut...")
        results = printer.test_emoji_support(emoji_list, None, 24)
    else:
        # Tester avec la première font emoji trouvée (priorité)
        emoji_font_path = emoji_fonts[0]
        from pathlib import Path
        font_name = Path(emoji_font_path).name
        log(f"Test avec: {font_name}")
        results = printer.test_emoji_support(emoji_list, emoji_font_path, 24)
    
    # Afficher les résultats
    supported = [emoji for emoji, supported in results.items() if supported]
    unsupported = [emoji for emoji, supported in results.items() if not supported]
    
    log(f"\nRésultats:")
    log(f"  ✓ Emojis supportés: {len(supported)}/{len(emoji_list)}")
    log(f"  ✗ Emojis non supportés: {len(unsupported)}/{len(emoji_list)}")
    
    if supported:
        log(f"\nEmojis supportés: {' '.join(supported[:20])}" + 
            (f" ... (+{len(supported)-20} autres)" if len(supported) > 20 else ""))
    
    if unsupported:
        log(f"\nEmojis non supportés: {' '.join(unsupported[:20])}" + 
            (f" ... (+{len(unsupported)-20} autres)" if len(unsupported) > 20 else ""))
    
    # Imprimer un résumé compact (une seule ligne)
    if supported:
        supported_sample = ' '.join(supported[:10])
        printer.print_text_image(
            text=f"Emojis supportés ({len(supported)}): {supported_sample}" + 
                 (f" ..." if len(supported) > 10 else ""),
            font_size=18,
            font_path=emoji_fonts[0] if emoji_fonts else None,
            align="left"
        )
        printer.lf(1)
    
    log("✓ Vérification support emojis terminée")


def test_format_box(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 13: Test format_box et print_boxed_title."""
    log("\n--- TEST 13: format_box et print_boxed_title ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 13: Format box")
    printer.set_text_style()
    roboto_font_path = paths["font"]
    
    # Tester avec print_boxed_title (nouvelle méthode recommandée)
    log("Test avec print_boxed_title (méthode recommandée):")
    test_titles = [
        "EXERCICE — Les animaux (A1)",
        "CORRECTIONS — Les couleurs",
        "Titre court",
        "Titre très très très long qui devrait être tronqué automatiquement",
    ]
    
    for title in test_titles:
        log(f"Test print_boxed_title: {title[:30]}...")
        if roboto_font_path.exists():
            printer.print_boxed_title(
                text=title,
                font_size=24,
                font_path=str(roboto_font_path)
            )
        else:
            printer.print_boxed_title(
                text=title,
                font_size=24
            )
        printer.lf(1)
    
    # Tester aussi avec _format_box (ancienne méthode, améliorée)
    log("\nTest avec _format_box (amélioré avec séparateurs):")
    for title in test_titles[:2]:  # Tester seulement 2 pour économiser le papier
        boxed = _format_box(title)
        log(f"Test _format_box: {title[:30]}...")
        if roboto_font_path.exists():
            printer.print_text_image(
                text=boxed,
                font_size=20,
                font_path=str(roboto_font_path),
                align="left"
            )
        else:
            printer.print_text_image(
                text=boxed,
                font_size=20,
                align="left"
            )
        printer.lf(1)
    
    log("✓ format_box et print_boxed_title testés")


def test_format_exercise(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 14: Test format_exercise avec JSON."""
    log("\n--- TEST 14: format_exercise ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 14: Format exercise")
    printer.set_text_style()
    exercises_path = paths["exercises"]
    daily_path = paths["daily"]
    
    if not exercises_path.exists():
        log(f"✗ Fichier exercises.json non trouvé: {exercises_path}")
        return
    
    try:
        # Charger les exercices
        with open(exercises_path, 'r', encoding='utf-8') as f:
            exercises = json.load(f)
        
        if not exercises:
            log("✗ Aucun exercice dans le fichier")
            return
        
        # Prendre le premier exercice
        exercise = exercises[0]
        log(f"Test avec exercice: {exercise.get('id', 'unknown')} - {exercise.get('title', '')}")
        
        # Charger daily si disponible
        daily = None
        if daily_path.exists():
            try:
                with open(daily_path, 'r', encoding='utf-8') as f:
                    daily_data = json.load(f)
                    if daily_data and isinstance(daily_data, list) and len(daily_data) > 0:
                        daily = daily_data[0]
                        log(f"Daily bonus: {daily.get('nl', '')} → {daily.get('fr', '')}")
            except Exception as e:
                log(f"⚠ Impossible de charger daily: {e}")
        
        # Formater l'exercice
        formatted_text, header_images = format_exercise(exercise, daily)
        
        # Afficher les images d'en-tête si présentes
        if header_images:
            log(f"Images d'en-tête: {header_images}")
            for img_path in header_images:
                printer.print_image_file(str(Path(__file__).parent.parent / img_path))
        
        # Afficher le texte formaté
        log("Impression du texte formaté...")
        printer.print_text_image(
            text=formatted_text,
            font_size=18,
            align="left"
        )
        printer.lf(2)
        
        log("✓ format_exercise testé avec succès")
        
    except Exception as e:
        log(f"✗ Erreur lors du test format_exercise: {e}")
        import traceback
        traceback.print_exc()


def test_summary(printer: EscposPrinter, paths: Dict[str, Path]) -> None:
    """TEST 15: Récapitulatif."""
    log("\n--- TEST 15: Récapitulatif ---")
    printer.set_text_style(font="B", bold=True)
    printer.line("TEST 15: Resume")
    printer.set_text_style()
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
    printer.line("✓ Emojis (NotoEmoji-Bold)")
    printer.line("✓ Helpers haut niveau")
    printer.line("✓ format_box")
    printer.line("✓ format_exercise")
    printer.lf(1)
    
    printer.centered_text("Tests terminés avec succès! ✓")
    printer.lf(2)


# Dictionnaire des tests disponibles
TESTS: Dict[str, Dict[str, any]] = {
    "1": {"name": "image", "func": test_image, "desc": "Impression d'image (logo)"},
    "2": {"name": "separators", "func": test_separators, "desc": "Séparateurs"},
    "3": {"name": "accents", "func": test_accents, "desc": "Accents et caractères spéciaux"},
    "4": {"name": "fonts_ab", "func": test_fonts_ab, "desc": "Fonts internes A et B"},
    "5": {"name": "styles", "func": test_styles, "desc": "Styles (gras, souligné)"},
    "6": {"name": "alignment", "func": test_alignment, "desc": "Centrage"},
    "7": {"name": "centered_text", "func": test_centered_text, "desc": "Helper centered_text"},
    "8": {"name": "custom_font", "func": test_custom_font, "desc": "Font custom (Roboto-Bold)"},
    "9": {"name": "emojis", "func": test_emojis, "desc": "Emojis avec différentes fonts (général)"},
    "10": {"name": "helpers", "func": test_helpers, "desc": "Helpers haut niveau"},
    "11": {"name": "notoemoji", "func": test_notoemoji, "desc": "Test spécifique NotoEmoji"},
    "12": {"name": "emoji_support_check", "func": test_emoji_support_check, "desc": "Vérification support emojis (sans impression)"},
    "13": {"name": "format_box", "func": test_format_box, "desc": "Test format_box et print_boxed_title"},
    "14": {"name": "format_exercise", "func": test_format_exercise, "desc": "Test format_exercise avec JSON"},
    "15": {"name": "summary", "func": test_summary, "desc": "Récapitulatif"},
}


def list_tests():
    """Affiche la liste des tests disponibles."""
    print("\nTests disponibles:\n")
    for num, test_info in sorted(TESTS.items(), key=lambda x: int(x[0])):
        print(f"  {num:>2}. {test_info['name']:20} - {test_info['desc']}")
    print()


def parse_test_selection(test_arg: str) -> List[str]:
    """Parse l'argument --test et retourne la liste des tests à exécuter."""
    if not test_arg:
        return list(TESTS.keys())  # Tous les tests par défaut
    
    selected = []
    parts = [p.strip() for p in test_arg.split(",")]
    
    for part in parts:
        # Par numéro
        if part.isdigit():
            if part in TESTS:
                selected.append(part)
            else:
                print(f"⚠ Test {part} non trouvé, ignoré")
        # Par nom
        else:
            found = False
            for num, test_info in TESTS.items():
                if test_info["name"] == part.lower():
                    selected.append(num)
                    found = True
                    break
            if not found:
                print(f"⚠ Test '{part}' non trouvé, ignoré")
    
    return list(set(selected))  # Dédupliquer


def test_miniescpos(selected_tests: List[str] = None):
    """Exécute les tests sélectionnés."""
    
    if selected_tests is None:
        selected_tests = list(TESTS.keys())
    
    log("=" * 60)
    log(f"TEST EscposPrinter - {len(selected_tests)} test(s) sélectionné(s)")
    log("=" * 60)
    
    paths = get_paths()
    font_path = paths["font"]
    
    try:
        log("Connexion à l'imprimante...")
        printer = EscposPrinter(
            device="/dev/serial0",
            width=58,
            baudrate=9600,
            timeout=1,
            width_px=384,
            default_encoding="cp850",
            default_font_path=str(font_path) if font_path.exists() else None,
            codepage="cp850",
            international="FRANCE",
        )
        log("Imprimante connectée (CP850 + FRANCE pour accents).")
        
        # Exécuter les tests sélectionnés
        for test_num in sorted(selected_tests, key=int):
            if test_num in TESTS:
                test_info = TESTS[test_num]
                try:
                    test_info["func"](printer, paths)
                except Exception as e:
                    log(f"✗ Erreur dans test {test_num} ({test_info['name']}): {e}")
                    import traceback
                    traceback.print_exc()
        
        # Coupe du papier (sauf si seulement summary)
        if "14" not in selected_tests or len(selected_tests) > 1:
            log("\n--- Coupe du papier ---")
            printer.cut(full=True)
            log("✓ Papier coupé")
        
        printer.close()
        log("Imprimante fermée.")
        
        log("\n" + "=" * 60)
        log("TESTS TERMINÉS!")
        log("=" * 60)
        return 0
        
    except Exception as e:
        log(f"✗ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script de test pour EscposPrinter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s                    # Tous les tests
  %(prog)s --list              # Lister les tests disponibles
  %(prog)s --test 2,3,6       # Tests par numéro
  %(prog)s --test accents,separators  # Tests par nom
  %(prog)s --test 1,2,3,6,8,9  # Combinaison
        """
    )
    parser.add_argument(
        "--test", "-t",
        type=str,
        default=None,
        help="Tests à exécuter (numéros ou noms séparés par des virgules)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Lister les tests disponibles"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_tests()
        sys.exit(0)
    
    selected = parse_test_selection(args.test)
    if not selected:
        print("✗ Aucun test valide sélectionné")
        sys.exit(1)
    
    sys.exit(test_miniescpos(selected))
