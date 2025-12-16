#!/usr/bin/env python3
"""Script de conversion par lots d'images en noir et blanc avec dithering."""

import argparse
import sys
from pathlib import Path
from PIL import Image

# Ajouter le répertoire parent au path pour importer le module dithering
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.dithering import apply_error_diffusion

# Extensions d'images supportées
SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}


def find_images(directory: Path) -> list[Path]:
    """Trouve toutes les images dans un répertoire (récursif)."""
    images = []
    for ext in SUPPORTED_EXTENSIONS:
        images.extend(directory.rglob(f'*{ext}'))
        images.extend(directory.rglob(f'*{ext.upper()}'))
    return sorted(images)


def convert_image(
    input_path: Path,
    output_dir: Path,
    width: int = 384,
    algorithm: str = 'atkinson_plus',
    brightness: float = 0.0,
    contrast: float = 1.0
) -> tuple[bool, str]:
    """Convertit une image selon les paramètres spécifiés.
    
    Returns:
        Tuple (success, message)
    """
    try:
        # Charger l'image
        img = Image.open(input_path)
        
        # Convertir en RGB si nécessaire
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionner à 384px de large (proportionnellement)
        if img.width > width:
            ratio = width / float(img.width)
            new_height = int(img.height * ratio)
            img = img.resize((width, new_height), Image.LANCZOS)
        
        # Appliquer le dithering
        img_dithered = apply_error_diffusion(
            img,
            algorithm=algorithm,
            brightness=brightness,
            contrast=contrast
        )
        
        # Générer le nom de fichier de sortie
        output_filename = input_path.stem + '.png'
        output_path = output_dir / output_filename
        
        # Gérer les doublons
        counter = 1
        original_output_path = output_path
        while output_path.exists():
            output_filename = f"{input_path.stem}_{counter}.png"
            output_path = output_dir / output_filename
            counter += 1
        
        # Sauvegarder en PNG compressé
        img_dithered.save(str(output_path), 'PNG', optimize=True, compress_level=9)
        
        return True, f"✓ {input_path.name} -> {output_path.name}"
    
    except Exception as e:
        return False, f"✗ {input_path.name}: {str(e)}"


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description='Convertit des images en noir et blanc avec dithering error diffusion'
    )
    parser.add_argument(
        'input_dir',
        type=str,
        help='Chemin du dossier contenant les images à convertir'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Dossier de sortie (défaut: data/surprise_photos)'
    )
    parser.add_argument(
        '--width',
        type=int,
        default=384,
        help='Largeur de sortie en pixels (défaut: 384)'
    )
    parser.add_argument(
        '--algorithm',
        type=str,
        default='atkinson_plus',
        choices=['atkinson_plus', 'atkinson', 'floyd_steinberg', 'sierra24a', 'stucki'],
        help='Algorithme de dithering (défaut: atkinson_plus)'
    )
    parser.add_argument(
        '--brightness',
        type=float,
        default=0.0,
        help='Ajustement de luminosité (-100 à +100, défaut: 0.0)'
    )
    parser.add_argument(
        '--contrast',
        type=float,
        default=1.0,
        help='Ajustement de contraste (0.0 à 2.0, défaut: 1.0)'
    )
    
    args = parser.parse_args()
    
    # Vérifier le dossier d'entrée
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Erreur: Le dossier '{input_dir}' n'existe pas.", file=sys.stderr)
        sys.exit(1)
    
    if not input_dir.is_dir():
        print(f"Erreur: '{input_dir}' n'est pas un dossier.", file=sys.stderr)
        sys.exit(1)
    
    # Déterminer le dossier de sortie
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # Utiliser data/surprise_photos par défaut
        project_root = Path(__file__).parent.parent
        output_dir = project_root / 'data' / 'surprise_photos'
    
    # Créer le dossier de sortie si nécessaire
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Trouver toutes les images
    print(f"Recherche d'images dans '{input_dir}'...")
    images = find_images(input_dir)
    
    if not images:
        print(f"Aucune image trouvée dans '{input_dir}'")
        sys.exit(0)
    
    print(f"Trouvé {len(images)} image(s)")
    print(f"Dossier de sortie: {output_dir}")
    print(f"Paramètres: largeur={args.width}px, algo={args.algorithm}, "
          f"luminosité={args.brightness}, contraste={args.contrast}")
    print("-" * 60)
    
    # Convertir chaque image
    success_count = 0
    error_count = 0
    
    for i, image_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] Traitement de {image_path.name}...", end=' ')
        success, message = convert_image(
            image_path,
            output_dir,
            width=args.width,
            algorithm=args.algorithm,
            brightness=args.brightness,
            contrast=args.contrast
        )
        print(message)
        
        if success:
            success_count += 1
        else:
            error_count += 1
    
    # Résumé
    print("-" * 60)
    print(f"Terminé: {success_count} réussie(s), {error_count} erreur(s)")


if __name__ == '__main__':
    main()
