"""Visual simulator that generates bitmap from ESC/POS commands."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None

from .escpos import EscposPrinter


class VisualSimulatorPrinter(EscposPrinter):
    """Visual simulator that intercepts ESC/POS commands and generates a bitmap preview."""
    
    def __init__(self, *args, **kwargs):
        """Initialize visual simulator.
        
        Args are the same as EscposPrinter, but device is ignored.
        """
        # Ne pas initialiser la connexion série
        kwargs['device'] = '/dev/null'  # Device fictif
        
        # État du simulateur (avant super() pour éviter les erreurs)
        width_px = kwargs.get('width_px', 384)
        self.max_paper_height = 10000  # Hauteur maximale (10m)
        self.current_y = 0  # Position Y actuelle
        self.current_x = 0  # Position X actuelle
        self.alignment = "left"  # left, center, right
        self.font_internal = "A"  # A ou B
        self.bold = False
        self.underline = False
        self.double_height = False
        self.double_width = False
        
        super().__init__(*args, **kwargs)
        
        # Initialiser l'image du papier après super()
        if PIL_AVAILABLE:
            self.paper_image = Image.new("L", (self.width_px, self.max_paper_height), 255)
            self.draw = ImageDraw.Draw(self.paper_image)
        else:
            self.paper_image = None
            self.draw = None
        
        # Fonts pour le rendu
        self._init_fonts()
        
        # Buffer pour les commandes
        self.command_buffer = []
        
    def _init_fonts(self):
        """Initialise les fonts pour le rendu."""
        if not PIL_AVAILABLE:
            return
        
        try:
            # Font par défaut (monospace pour simuler l'imprimante)
            self.font_a = ImageFont.load_default()
            self.font_b = ImageFont.load_default()  # Font B est plus petite
            
            # Essayer de charger une font monospace système
            import platform
            if platform.system() == "Linux":
                system_fonts = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                ]
                for font_path in system_fonts:
                    try:
                        self.font_a = ImageFont.truetype(font_path, 12)
                        self.font_b = ImageFont.truetype(font_path, 10)
                        break
                    except:
                        continue
        except:
            pass
    
    def _init_printer(self, codepage: str, international: str) -> None:
        """Override: ne pas initialiser la connexion série."""
        # Ne rien faire - on simule seulement
        self._ser = None
        print(f"✓ Visual simulator initialized (width: {self.width_px}px)")
    
    def raw(self, data: bytes, description: str = "") -> None:
        """Override: intercepte les commandes et les simule visuellement."""
        if not data:
            return
        
        # Parser la commande
        self._parse_and_render_command(data)
        
        # Garder aussi le comportement de logging si activé
        if self._enable_logging:
            self._log_command(data, description)
    
    def _parse_and_render_command(self, data: bytes) -> None:
        """Parse une commande ESC/POS et la rend visuellement."""
        if not PIL_AVAILABLE:
            return
        
        # RESET (ESC @)
        if data == b"\x1B\x40":
            self._handle_reset()
        
        # SET_ALIGN (ESC a n)
        elif data.startswith(b"\x1B\x61"):
            if len(data) >= 3:
                n = data[2]
                align_map = {0: "left", 1: "center", 2: "right"}
                self.alignment = align_map.get(n, "left")
        
        # SET_STYLE (ESC ! n)
        elif data.startswith(b"\x1B\x21"):
            if len(data) >= 3:
                n = data[2]
                self.font_internal = "B" if (n & 0x01) else "A"
                self.double_height = bool(n & 0x10)
                self.double_width = bool(n & 0x20)
                self.underline = bool(n & 0x80)
        
        # SET_BOLD (ESC E n)
        elif data.startswith(b"\x1B\x45"):
            if len(data) >= 3:
                self.bold = bool(data[2])
        
        # LINE_FEED (\n ou \r\n)
        elif data == b"\n" or data == b"\r\n" or data == b"\r":
            self.current_y += self._get_line_height()
            self.current_x = 0
        
        # LF command (ESC d n)
        elif data.startswith(b"\x1B\x64"):
            if len(data) >= 3:
                n = data[2]
                self.current_y += self._get_line_height() * n
                self.current_x = 0
        
        # PRINT_IMAGE (GS v 0)
        elif data.startswith(b"\x1D\x76\x30"):
            self._handle_print_image(data)
        
        # TEXT (tout le reste qui est du texte)
        elif len(data) > 0 and all(32 <= b <= 126 or b in [10, 13] or 128 <= b <= 255 for b in data):
            self._handle_text(data)
    
    def _handle_reset(self):
        """Réinitialise l'état de l'imprimante."""
        self.current_y = 0
        self.current_x = 0
        self.alignment = "left"
        self.font_internal = "A"
        self.bold = False
        self.underline = False
        self.double_height = False
        self.double_width = False
    
    def _handle_text(self, data: bytes) -> None:
        """Rend du texte sur l'image."""
        if not PIL_AVAILABLE:
            return
        
        try:
            # Décoder le texte (cp850 par défaut)
            text = data.decode(self.encoding, errors='replace')
            # Enlever les retours à la ligne (gérés séparément)
            text = text.replace('\r', '').replace('\n', '')
            
            if not text:
                return
            
            # Choisir la font
            font = self.font_b if self.font_internal == "B" else self.font_a
            
            # Calculer la taille avec les styles
            font_size_mult = 1.0
            if self.double_height:
                font_size_mult *= 2.0
            if self.double_width:
                font_size_mult *= 2.0
            
            # Mesurer le texte
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculer la position X selon l'alignement
            if self.alignment == "center":
                x = (self.width_px - text_width * font_size_mult) // 2
            elif self.alignment == "right":
                x = self.width_px - text_width * font_size_mult
            else:
                x = self.current_x
            
            # Dessiner le texte
            y = self.current_y
            
            # Si double width/height, on doit redimensionner
            if font_size_mult != 1.0:
                # Créer une image temporaire pour le texte
                temp_img = Image.new("L", (int(text_width * font_size_mult), int(text_height * font_size_mult)), 255)
                temp_draw = ImageDraw.Draw(temp_img)
                temp_draw.text((0, 0), text, font=font, fill=0)
                # Redimensionner si nécessaire
                if font_size_mult != 1.0:
                    new_size = (int(text_width * font_size_mult), int(text_height * font_size_mult))
                    temp_img = temp_img.resize(new_size, Image.NEAREST)
                self.paper_image.paste(temp_img, (int(x), int(y)))
            else:
                self.draw.text((int(x), int(y)), text, font=font, fill=0)
            
            # Mettre à jour la position
            self.current_x = x + text_width * font_size_mult
            if self.current_x >= self.width_px:
                self.current_x = 0
                self.current_y += text_height * font_size_mult
        
        except Exception as e:
            print(f"Error rendering text in simulator: {e}")
    
    def _handle_print_image(self, data: bytes) -> None:
        """Rend une image bitmap sur le papier."""
        if not PIL_AVAILABLE or not self.paper_image:
            return
        
        try:
            # Parser GS v 0 m xL xH yL yH [bitmap]
            # Format: 1D 76 30 m xL xH yL yH [data...]
            if len(data) < 9:
                return
            
            m = data[3]  # Mode (0 = normal)
            xL = data[4]
            xH = data[5]
            yL = data[6]
            yH = data[7]
            
            width_bytes = xL + (xH << 8)
            height = yL + (yH << 8)
            
            # Extraire les données bitmap
            bitmap_data = data[8:]
            
            if len(bitmap_data) < width_bytes * height:
                return
            
            # Convertir le bitmap en image PIL
            # Format ESC/POS: chaque byte contient 8 pixels verticaux (bits)
            # width_bytes = nombre de bytes par ligne
            # height = nombre de lignes
            img = Image.new("1", (width_bytes * 8, height), 1)  # 1 = blanc
            pixels = img.load()
            
            for y in range(height):
                for x_byte in range(width_bytes):
                    byte_index = y * width_bytes + x_byte
                    if byte_index >= len(bitmap_data):
                        break
                    byte_val = bitmap_data[byte_index]
                    
                    # Chaque bit du byte représente un pixel horizontal
                    # Bit 7 (MSB) = pixel le plus à gauche
                    for bit in range(8):
                        x = x_byte * 8 + (7 - bit)  # Bit 7 = x, bit 0 = x+7
                        if x < width_bytes * 8:
                            # Extraire le bit (0 ou 1)
                            pixel_val = (byte_val >> bit) & 1
                            # Dans ESC/POS: 1 = noir, 0 = blanc
                            # Dans PIL mode "1": 0 = noir, 1 = blanc
                            pixels[x, y] = 0 if pixel_val == 1 else 1
            
            # Convertir en niveaux de gris
            img = img.convert("L")
            
            # Redimensionner si nécessaire
            if img.width > self.width_px:
                ratio = self.width_px / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.width_px, new_height), Image.LANCZOS)
            
            # Centrer si alignement center
            x_offset = 0
            if self.alignment == "center":
                x_offset = (self.width_px - img.width) // 2
            elif self.alignment == "right":
                x_offset = self.width_px - img.width
            
            # Coller l'image sur le papier
            self.paper_image.paste(img, (x_offset, self.current_y))
            
            # Mettre à jour la position Y
            self.current_y += img.height + 5  # Petit espace après l'image
        
        except Exception as e:
            print(f"Error rendering image in simulator: {e}")
    
    def print_image(self, img: 'Image.Image') -> None:
        """Override: intercepte print_image pour le simuler."""
        if not PIL_AVAILABLE or not self.paper_image:
            return
        
        try:
            # Redimensionner si nécessaire
            if img.width > self.width_px:
                ratio = self.width_px / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.width_px, new_height), Image.LANCZOS)
            
            # Convertir en niveaux de gris si nécessaire
            if img.mode != "L":
                img = img.convert("L")
            
            # Centrer si alignement center
            x_offset = 0
            if self.alignment == "center":
                x_offset = (self.width_px - img.width) // 2
            elif self.alignment == "right":
                x_offset = self.width_px - img.width
            
            # Coller l'image sur le papier
            self.paper_image.paste(img, (x_offset, self.current_y))
            
            # Mettre à jour la position Y
            self.current_y += img.height + 5  # Petit espace après l'image
        
        except Exception as e:
            print(f"Error rendering image in simulator: {e}")
    
    def print_text_image(self, text: str, font_size: int = 24, font_path: Optional[str] = None, padding: Tuple[int, int, int, int] = (0, 0, 0, 0), align: str = "left") -> None:
        """Override: intercepte print_text_image pour le simuler."""
        if not PIL_AVAILABLE or not self.paper_image:
            return
        
        # Utiliser la méthode parent pour générer l'image
        img = self._render_text_to_image(text, font_size, font_path, padding, align)
        if img:
            self.print_image(img)
            self.lf(1)
    
    def print_image_file(self, image_path: str) -> bool:
        """Override: intercepte print_image_file pour le simuler."""
        if not PIL_AVAILABLE or not self.paper_image:
            return False
        
        try:
            img = self._load_image(image_path)
            if img:
                self.print_image(img)
                self.lf(1)
                return True
            return False
        except Exception as e:
            print(f"Error printing image in simulator: {e}")
            return False
    
    def _get_line_height(self) -> int:
        """Retourne la hauteur d'une ligne selon la font et les styles."""
        font = self.font_b if self.font_internal == "B" else self.font_a
        bbox = font.getbbox("Ag")
        height = bbox[3] - bbox[1]
        
        if self.double_height:
            height *= 2
        
        return int(height * 1.2)  # Ajouter un peu d'espace
    
    def close(self) -> None:
        """Ferme le simulateur et sauvegarde l'image."""
        # Flush le buffer de log si activé
        if hasattr(self, '_flush_log_buffer'):
            self._flush_log_buffer()
        
        # Récupérer l'image finale (tronquer à la hauteur utilisée)
        if PIL_AVAILABLE and self.paper_image and self.current_y > 0:
            final_height = min(self.current_y + 50, self.max_paper_height)  # Ajouter un peu de marge
            final_image = self.paper_image.crop((0, 0, self.width_px, final_height))
            
            # Sauvegarder l'image
            self._save_preview(final_image)
    
    def _save_preview(self, image: Image.Image) -> None:
        """Sauvegarde l'aperçu de l'impression."""
        try:
            project_root = Path(__file__).parent.parent.parent
            output_dir = project_root / 'output'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = output_dir / f'preview_{timestamp}.png'
            
            # Convertir en RGB pour sauvegarder en PNG
            rgb_image = image.convert("RGB")
            rgb_image.save(filename, "PNG")
            
            print(f"✓ Preview saved: {filename}")
            self.preview_path = str(filename)
        except Exception as e:
            print(f"Error saving preview: {e}")
            self.preview_path = None
    
    def get_preview_path(self) -> Optional[str]:
        """Retourne le chemin de l'aperçu généré."""
        return getattr(self, 'preview_path', None)
    
    def get_preview_image(self) -> Optional[Image.Image]:
        """Retourne l'image de l'aperçu (sans la sauvegarder)."""
        if PIL_AVAILABLE and self.paper_image and self.current_y > 0:
            final_height = min(self.current_y + 50, self.max_paper_height)
            return self.paper_image.crop((0, 0, self.width_px, final_height))
        return None

