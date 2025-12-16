"""Module de dithering error diffusion pour conversion d'images en noir et blanc."""

import numpy as np
from PIL import Image
from typing import Tuple


def apply_brightness_contrast(img: Image.Image, brightness: float = 0.0, contrast: float = 1.0) -> Image.Image:
    """Applique la luminosité et le contraste à une image en niveaux de gris.
    
    Args:
        img: Image PIL en mode 'L' (niveaux de gris)
        brightness: Ajustement de luminosité (-100 à +100)
        contrast: Ajustement de contraste (0.0 à 2.0)
    
    Returns:
        Image PIL modifiée en mode 'L'
    """
    if img.mode != 'L':
        img = img.convert('L')
    
    # Convertir en numpy array
    arr = np.array(img, dtype=np.float32)
    
    # Appliquer la luminosité (-100 à +100 -> -128 à +128)
    brightness_offset = (brightness / 100.0) * 128
    arr = arr + brightness_offset
    
    # Appliquer le contraste
    arr = (arr - 128) * contrast + 128
    
    # Clamper les valeurs entre 0 et 255
    arr = np.clip(arr, 0, 255)
    
    # Reconvertir en Image PIL
    return Image.fromarray(arr.astype(np.uint8), mode='L')


def _floyd_steinberg(img: np.ndarray) -> np.ndarray:
    """Algorithme de dithering Floyd-Steinberg."""
    height, width = img.shape
    result = np.zeros((height, width), dtype=np.uint8)
    error = img.astype(np.float32)
    
    for y in range(height):
        for x in range(width):
            old_pixel = error[y, x]
            new_pixel = 255 if old_pixel >= 128 else 0
            result[y, x] = new_pixel
            
            quant_error = old_pixel - new_pixel
            
            # Propagation de l'erreur
            if x + 1 < width:
                error[y, x + 1] += quant_error * 7 / 16
            if y + 1 < height:
                if x - 1 >= 0:
                    error[y + 1, x - 1] += quant_error * 3 / 16
                error[y + 1, x] += quant_error * 5 / 16
                if x + 1 < width:
                    error[y + 1, x + 1] += quant_error * 1 / 16
    
    return result


def _atkinson(img: np.ndarray) -> np.ndarray:
    """Algorithme de dithering Atkinson."""
    height, width = img.shape
    result = np.zeros((height, width), dtype=np.uint8)
    error = img.astype(np.float32)
    
    for y in range(height):
        for x in range(width):
            old_pixel = error[y, x]
            new_pixel = 255 if old_pixel >= 128 else 0
            result[y, x] = new_pixel
            
            quant_error = old_pixel - new_pixel
            error_frac = quant_error / 8
            
            # Propagation de l'erreur (Atkinson utilise 1/8 pour chaque voisin)
            if x + 1 < width:
                error[y, x + 1] += error_frac
            if x + 2 < width:
                error[y, x + 2] += error_frac
            if y + 1 < height:
                if x - 1 >= 0:
                    error[y + 1, x - 1] += error_frac
                error[y + 1, x] += error_frac
                if x + 1 < width:
                    error[y + 1, x + 1] += error_frac
            if y + 2 < height:
                error[y + 2, x] += error_frac
    
    return result


def _atkinson_plus(img: np.ndarray) -> np.ndarray:
    """Algorithme de dithering Atkinson+ (variante améliorée)."""
    height, width = img.shape
    result = np.zeros((height, width), dtype=np.uint8)
    error = img.astype(np.float32)
    
    for y in range(height):
        for x in range(width):
            old_pixel = error[y, x]
            new_pixel = 255 if old_pixel >= 128 else 0
            result[y, x] = new_pixel
            
            quant_error = old_pixel - new_pixel
            # Atkinson+ utilise une distribution légèrement différente pour un meilleur rendu
            error_frac = quant_error / 6
            
            # Propagation avec poids légèrement différents
            if x + 1 < width:
                error[y, x + 1] += error_frac
            if x + 2 < width:
                error[y, x + 2] += error_frac * 0.5
            if y + 1 < height:
                if x - 1 >= 0:
                    error[y + 1, x - 1] += error_frac
                error[y + 1, x] += error_frac
                if x + 1 < width:
                    error[y + 1, x + 1] += error_frac * 0.5
            if y + 2 < height:
                error[y + 2, x] += error_frac * 0.5
    
    return result


def _sierra24a(img: np.ndarray) -> np.ndarray:
    """Algorithme de dithering Sierra24A."""
    height, width = img.shape
    result = np.zeros((height, width), dtype=np.uint8)
    error = img.astype(np.float32)
    
    for y in range(height):
        for x in range(width):
            old_pixel = error[y, x]
            new_pixel = 255 if old_pixel >= 128 else 0
            result[y, x] = new_pixel
            
            quant_error = old_pixel - new_pixel
            
            # Propagation de l'erreur (matrice Sierra24A)
            if x + 1 < width:
                error[y, x + 1] += quant_error * 2 / 4
            if x + 2 < width:
                error[y, x + 2] += quant_error * 1 / 4
            if y + 1 < height:
                if x - 2 >= 0:
                    error[y + 1, x - 2] += quant_error * 1 / 4
                if x - 1 >= 0:
                    error[y + 1, x - 1] += quant_error * 1 / 4
                error[y + 1, x] += quant_error * 1 / 4
    
    return result


def _stucki(img: np.ndarray) -> np.ndarray:
    """Algorithme de dithering Stucki (haute qualité)."""
    height, width = img.shape
    result = np.zeros((height, width), dtype=np.uint8)
    error = img.astype(np.float32)
    
    for y in range(height):
        for x in range(width):
            old_pixel = error[y, x]
            new_pixel = 255 if old_pixel >= 128 else 0
            result[y, x] = new_pixel
            
            quant_error = old_pixel - new_pixel
            
            # Propagation de l'erreur (matrice Stucki)
            if x + 1 < width:
                error[y, x + 1] += quant_error * 8 / 42
            if x + 2 < width:
                error[y, x + 2] += quant_error * 4 / 42
            if y + 1 < height:
                if x - 2 >= 0:
                    error[y + 1, x - 2] += quant_error * 2 / 42
                if x - 1 >= 0:
                    error[y + 1, x - 1] += quant_error * 4 / 42
                error[y + 1, x] += quant_error * 8 / 42
                if x + 1 < width:
                    error[y + 1, x + 1] += quant_error * 4 / 42
                if x + 2 < width:
                    error[y + 1, x + 2] += quant_error * 2 / 42
            if y + 2 < height:
                if x - 2 >= 0:
                    error[y + 2, x - 2] += quant_error * 1 / 42
                if x - 1 >= 0:
                    error[y + 2, x - 1] += quant_error * 2 / 42
                error[y + 2, x] += quant_error * 4 / 42
                if x + 1 < width:
                    error[y + 2, x + 1] += quant_error * 2 / 42
                if x + 2 < width:
                    error[y + 2, x + 2] += quant_error * 1 / 42
    
    return result


def apply_error_diffusion(
    img: Image.Image,
    algorithm: str = 'atkinson_plus',
    brightness: float = 0.0,
    contrast: float = 1.0
) -> Image.Image:
    """Applique le dithering error diffusion à une image.
    
    Args:
        img: Image PIL (n'importe quel mode, sera convertie en niveaux de gris)
        algorithm: Algorithme à utiliser ('atkinson_plus', 'atkinson', 'floyd_steinberg', 'sierra24a', 'stucki')
        brightness: Ajustement de luminosité (-100 à +100)
        contrast: Ajustement de contraste (0.0 à 2.0)
    
    Returns:
        Image PIL en mode '1' (1-bit, noir et blanc)
    """
    # Convertir en niveaux de gris si nécessaire
    if img.mode != 'L':
        img = img.convert('L')
    
    # Appliquer luminosité et contraste
    if brightness != 0.0 or contrast != 1.0:
        img = apply_brightness_contrast(img, brightness, contrast)
    
    # Convertir en numpy array
    img_array = np.array(img, dtype=np.uint8)
    
    # Appliquer l'algorithme de dithering
    algorithm = algorithm.lower()
    if algorithm == 'floyd_steinberg':
        result_array = _floyd_steinberg(img_array)
    elif algorithm == 'atkinson':
        result_array = _atkinson(img_array)
    elif algorithm == 'atkinson_plus' or algorithm == 'atkinson+':
        result_array = _atkinson_plus(img_array)
    elif algorithm == 'sierra24a' or algorithm == 'sierra24a':
        result_array = _sierra24a(img_array)
    elif algorithm == 'stucki':
        result_array = _stucki(img_array)
    else:
        raise ValueError(f"Algorithme inconnu: {algorithm}. Options: 'atkinson_plus', 'atkinson', 'floyd_steinberg', 'sierra24a', 'stucki'")
    
    # Convertir en Image PIL mode '1' (1-bit)
    result_img = Image.fromarray(result_array, mode='L')
    result_img = result_img.convert('1')
    
    return result_img
