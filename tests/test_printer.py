#!/usr/bin/env python3
"""Test script for printer connection."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.printer import get_printer


def test_printer():
    """Test printer connection and print a test ticket."""
    print("=" * 60)
    print("Test d'impression - Dutch-o-matic")
    print("=" * 60)
    print()
    
    try:
        # Get printer from config
        printer = get_printer()
        print(f"Type d'imprimante: {type(printer).__name__}")
        print()
        
        # Test text
        # Utiliser em-dash (—) pour les séparateurs (compatible GB18030)
        # Largeur: 32 caractères en Font A, 42 caractères en Font B
        # Éviter les box drawing (╔║═╝) qui s'affichent en carrés
        # Caractères accentués supportés: à é è ê ù (fonctionnent avec GB18030)
        # Utiliser chars_per_line de l'imprimante (s'adapte à la font active)
        separator_width = printer.chars_per_line if hasattr(printer, 'chars_per_line') else 42
        test_text = (
            "TEST D'IMPRESSION\n"
            "\n"
            "Ceci est un test d'impression.\n"
            "\n"
            "Si vous voyez ce ticket, l'imprimante fonctionne !\n"
            "\n"
            "Caractères accentués supportés: à é è ê ù\n"
            f"Font active: {printer._font_internal if hasattr(printer, '_font_internal') else '?'} ({separator_width} chars)\n"
            "Séparateur em-dash (—):\n"
            "\n"
            "—" * separator_width + "\n"
            "\n"
            "Ligne de test avec du texte qui peut être long et qui\n"
            "devrait être correctement formatée sur plusieurs lignes.\n"
            "\n"
            "—" * separator_width + "\n"
            "\n"
            "Test terminé avec succès!\n"
        )
        
        print("Envoi du texte à l'imprimante...")
        success = printer.print_text(test_text)
        
        if success:
            print("✓ Impression réussie!")
            return 0
        else:
            print("✗ Échec de l'impression")
            return 1
            
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(test_printer())
