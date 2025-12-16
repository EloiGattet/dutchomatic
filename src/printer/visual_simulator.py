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
        
        # Initialiser l'image du papier AVANT super() pour qu'elle existe quand _init_printer() est appelé
        if PIL_AVAILABLE:
            self.paper_image = Image.new("L", (width_px, self.max_paper_height), 255)
            self.draw = ImageDraw.Draw(self.paper_image)
        else:
            self.paper_image = None
            self.draw = None
        
        super().__init__(*args, **kwargs)
        
        # S'assurer que width_px est bien défini après super()
        if not hasattr(self, 'width_px') or self.width_px != width_px:
            self.width_px = width_px
            # Recréer l'image avec la bonne largeur si nécessaire
            if PIL_AVAILABLE and self.paper_image:
                if self.paper_image.width != width_px:
                    self.paper_image = Image.new("L", (width_px, self.max_paper_height), 255)
                    self.draw = ImageDraw.Draw(self.paper_image)
        
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
        """Override: simuler l'initialisation sans connexion série."""
        # Ne pas initialiser la connexion série
        self._ser = None
        
        # Simuler les commandes d'initialisation comme l'imprimante réelle
        # Reset
        self._handle_reset()
        
        # IMPORTANT: D'abord international (ESC R), puis codepage (ESC t)
        # L'ordre est crucial : ESC R doit être envoyé avant ESC t
        # Avec R=1 (FRANCE) + cp850, les accents français sont supportés
        self.set_international(international)
        self.set_codepage(codepage, try_alternative=False)
        
        # Appliquer les paramètres optimaux d'impression (simulation)
        self.set_heating(n1=7, n2=180, n3=2)
        self.set_density(density=15, breaktime=0)
        
        print(f"✓ Visual simulator initialized (width: {self.width_px}px, codepage={codepage}, international={international})")
    
    def text(self, s: str) -> None:
        """Override: intercepte text pour le simuler (sans vérifier self._ser)."""
        # Encoder avec le codepage configuré (gb18030 par défaut)
        try:
            data = s.encode(self.encoding, errors="replace")
        except (UnicodeEncodeError, LookupError):
            # Fallback: essayer gb18030 si l'encoding n'est pas valide
            try:
                data = s.encode("gb18030", errors="replace")
            except:
                # Dernier recours: ASCII avec remplacement
                data = s.encode("ascii", errors="replace")
        self.raw(data)
    
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
        
        # SET_CODEPAGE (ESC t n)
        elif data.startswith(b"\x1B\x74"):
            if len(data) >= 3:
                n = data[2]
                # n=0 pour cp850, n=0 pour cp437 aussi
                if n == 0:
                    self.encoding = "cp850"
                else:
                    self.encoding = "cp437"
        
        # SET_INTERNATIONAL (ESC R n)
        elif data.startswith(b"\x1B\x52"):
            if len(data) >= 3:
                n = data[2]
                # n=1 pour FRANCE, on peut l'ignorer pour la simulation visuelle
                pass
        
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
            print(f"Visual simulator: PRINT_IMAGE command detected, size={len(data)} bytes")
            self._handle_print_image(data)
        
        # TEXT (tout le reste qui est du texte)
        elif len(data) > 0 and all(32 <= b <= 126 or b in [10, 13] or 128 <= b <= 255 for b in data):
            self._handle_text(data)
    
    def _handle_reset(self):
        """Réinitialise l'état de l'imprimante et l'image."""
        self.current_y = 0
        self.current_x = 0
        self.alignment = "left"
        self.font_internal = "A"
        self.bold = False
        self.underline = False
        self.double_height = False
        self.double_width = False
        
        # Réinitialiser l'image à blanc (si elle existe déjà)
        if PIL_AVAILABLE and hasattr(self, 'paper_image') and self.paper_image:
            # Recréer une image blanche
            width_px = getattr(self, 'width_px', 384)
            self.paper_image = Image.new("L", (width_px, self.max_paper_height), 255)
            self.draw = ImageDraw.Draw(self.paper_image)
            print("Visual simulator: Image reset to blank")
    
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
            print("Visual simulator: PIL not available or paper_image not initialized for PRINT_IMAGE")
            return
        
        try:
            # Parser GS v 0 m xL xH yL yH [bitmap]
            # Format: 1D 76 30 m xL xH yL yH [data...]
            if len(data) < 9:
                print(f"Visual simulator: PRINT_IMAGE command too short: {len(data)} bytes")
                return
            
            m = data[3]  # Mode (0 = normal)
            xL = data[4]
            xH = data[5]
            yL = data[6]
            yH = data[7]
            
            width_bytes = xL + (xH << 8)
            height = yL + (yH << 8)
            
            print(f"Visual simulator: PRINT_IMAGE parsing: width_bytes={width_bytes}, height={height}, mode={m}")
            
            # Extraire les données bitmap
            bitmap_data = data[8:]
            
            expected_size = width_bytes * height
            if len(bitmap_data) < expected_size:
                print(f"Visual simulator: PRINT_IMAGE data too short: got {len(bitmap_data)} bytes, expected {expected_size}")
                return
            
            # Diagnostic: image potentiellement vide (tout blanc)
            # Si le bitmap est quasi entièrement à 0, l'image ne contiendra quasiment aucun pixel noir.
            nonzero = sum(1 for b in bitmap_data[:expected_size] if b)
            if nonzero == 0:
                print("Visual simulator: WARNING PRINT_IMAGE bitmap seems empty (all bytes are 0) -> image will look blank")
            elif nonzero / expected_size < 0.002:
                print(f"Visual simulator: NOTE PRINT_IMAGE bitmap is very light (ink_ratio={nonzero/expected_size:.4f})")
            
            print(f"Visual simulator: PRINT_IMAGE data OK: {len(bitmap_data)} bytes")
            
            # Convertir le bitmap en image PIL
            # Format ESC/POS: chaque ligne y a width_bytes bytes
            # Chaque byte contient 8 pixels horizontaux (bits)
            # width_bytes = nombre de bytes par ligne = (largeur_pixels + 7) // 8
            # height = nombre de lignes
            actual_width = width_bytes * 8
            img = Image.new("1", (actual_width, height), 1)  # 1 = blanc
            pixels = img.load()
            
            print(f"Visual simulator: Creating image {actual_width}x{height} from {len(bitmap_data)} bytes")
            
            for y in range(height):
                for x_byte in range(width_bytes):
                    byte_index = y * width_bytes + x_byte
                    if byte_index >= len(bitmap_data):
                        print(f"Visual simulator: Warning: byte_index {byte_index} >= {len(bitmap_data)} at y={y}, x_byte={x_byte}")
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
            
            print(f"Visual simulator: Image decoded successfully")
            
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
            print(f"Visual simulator: Pasting PRINT_IMAGE at ({x_offset}, {self.current_y}), size={img.size}, mode={img.mode}")
            
            # Vérifier que l'image ne dépasse pas les limites
            if self.current_y + img.height > self.max_paper_height:
                print(f"Visual simulator: Warning: Image would exceed max height ({self.current_y + img.height} > {self.max_paper_height})")
            
            # Vérifier le contenu de l'image avant de la coller (diagnostic)
            if img.mode == "L":
                img_pix = img.load()
                w_img, h_img = img.size
                black_count = sum(1 for y in range(h_img) for x in range(w_img) if img_pix[x, y] < 200)
                ink_ratio = black_count / (w_img * h_img) if (w_img * h_img) > 0 else 0
                print(f"Visual simulator: Image content check: {black_count} black pixels, ink_ratio={ink_ratio:.4f}")
                if ink_ratio < 0.001:
                    print(f"Visual simulator: WARNING: Image has very low ink_ratio ({ink_ratio:.4f}), might appear blank!")
            
            # Convertir en entiers pour PIL paste()
            x_offset_int = int(x_offset)
            current_y_int = int(self.current_y)
            self.paper_image.paste(img, (x_offset_int, current_y_int))
            
            # Vérifier que l'image a bien été collée (diagnostic)
            paper_pix = self.paper_image.load()
            check_y = current_y_int + img.height // 2  # Vérifier au milieu de l'image collée
            check_x = self.width_px // 2
            if check_y < self.paper_image.height and check_x < self.paper_image.width:
                pixel_val = paper_pix[check_x, check_y]
                print(f"Visual simulator: Verification: pixel at ({check_x}, {check_y}) = {pixel_val}")
            
            # Mettre à jour la position Y (garder en float pour précision, mais convertir lors de l'utilisation)
            self.current_y += img.height + 5  # Petit espace après l'image
            print(f"Visual simulator: PRINT_IMAGE rendered successfully, new Y={self.current_y}")
        
        except Exception as e:
            print(f"ERROR rendering PRINT_IMAGE in simulator: {e}")
            import traceback
            traceback.print_exc()
            # Ne pas retourner, continuer quand même
    
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
            
            # Coller l'image sur le papier (convertir en entiers pour PIL)
            x_offset_int = int(x_offset)
            current_y_int = int(self.current_y)
            self.paper_image.paste(img, (x_offset_int, current_y_int))
            
            # Mettre à jour la position Y
            self.current_y += img.height + 5  # Petit espace après l'image
        
        except Exception as e:
            print(f"Error rendering image in simulator: {e}")
    
    def print_text(self, text: str, header_images: Optional[list] = None, bonus_images: Optional[list] = None, city_images: Optional[list] = None) -> bool:
        """Override: intercepte print_text pour le simuler (sans vérifier self._ser)."""
        if not PIL_AVAILABLE or not self.paper_image:
            print("Error: PIL not available or paper_image not initialized")
            return False
        
        try:
            # Réinitialiser l'alignement et l'encodage au début
            self.set_align("left")
            # S'assurer que l'encodage est correct
            self.set_codepage("cp850", try_alternative=False)
            self.set_international("FRANCE")
            
            # Print header images first
            if header_images:
                print(f"Visual simulator: Printing {len(header_images)} header image(s)")
                for img_path in header_images:
                    print(f"Visual simulator: Loading header image: {img_path}")
                    success = self.print_image_file(img_path)
                    if not success:
                        print(f"Warning: Failed to load header image: {img_path}")
                    self.set_align("left")  # Réinitialiser après chaque image
            else:
                print("Visual simulator: No header images provided")
            
            # Parser le texte ligne par ligne pour insérer les images bonus et city au bon moment
            lines = text.split('\n')
            bonus_printed = False
            in_city_section = False
            city_image_inserted = False
            
            for line in lines:
                # Détecter si on entre dans la section ville
                if '🏙️' in line and 'VILLE DU JOUR' in line:
                    in_city_section = True
                
                # Détecter si la ligne est centrée (beaucoup d'espaces au début et à la fin)
                stripped_line = line.strip()
                leading_spaces = len(line) - len(line.lstrip())
                trailing_spaces = len(line) - len(line.rstrip())
                is_centered = (
                    leading_spaces > 5 and 
                    trailing_spaces > 5 and 
                    len(stripped_line) < len(line) * 0.8  # Le texte réel est beaucoup plus court que la ligne totale
                )
                
                # Détecter le marqueur pour texte en double taille
                is_double_size = False
                if stripped_line.startswith("**DOUBLE_SIZE**"):
                    is_double_size = True
                    stripped_line = stripped_line.replace("**DOUBLE_SIZE**", "", 1)
                    line = line.replace("**DOUBLE_SIZE**", "", 1)
                    # Pour le simulateur visuel, on utilisera une taille de font plus grande dans le rendu
                    # Forcer le centrage pour le nom de ville
                    is_centered = True
                    text_align = "center"
                
                # Décider si on imprime directement (font interne) ou en image (font custom/emojis)
                # Vérifier d'abord sur la ligne originale (avec espaces) pour ne pas rater les emojis
                has_emoji_original = self._has_emoji(line)
                has_emoji = self._has_emoji(stripped_line)
                if has_emoji_original and not has_emoji:
                    # Emoji détecté dans la ligne originale mais pas dans stripped
                    has_emoji = True
                    print(f"Visual simulator: Emoji detected in original line but not in stripped: {line[:50]}...")
                
                # Détecter si la ligne contient des caractères Unicode spéciaux (hors ASCII/cp850)
                # Inclure les caractères comme "—" (em dash, U+2014) qui ne sont pas dans cp850
                has_special_unicode = False
                special_chars = []
                if stripped_line:
                    try:
                        # Vérifier si la ligne contient des caractères non-ASCII (hors accents français supportés)
                        for char in stripped_line:
                            code = ord(char)
                            # ASCII: 0-127, mais on accepte aussi les accents français cp850 (128-255)
                            # Si c'est un caractère Unicode au-delà de 255, c'est spécial
                            # Aussi, certains caractères dans la plage 128-255 ne sont pas dans cp850
                            if code > 255 and char not in ['\n', '\r', '\t']:
                                has_special_unicode = True
                                special_chars.append(char)
                            elif code == 0x2014 or code == 0x2013:  # Em dash, en dash
                                has_special_unicode = True
                                special_chars.append(char)
                    except:
                        pass
                
                # Déterminer l'alignement pour le rendu
                if not is_double_size:
                    text_align = "center" if is_centered else "left"
                
                # Si pas d'emojis et pas de caractères Unicode spéciaux, utiliser les fonts internes
                if not has_emoji and not has_special_unicode:
                    # Si double_size, utiliser le rendu en image avec une taille plus grande
                    if is_double_size:
                        # Rendre en image avec une taille plus grande
                        img = self._render_text_to_image(
                            text=stripped_line,
                            font_size=32,  # Taille plus grande pour le nom de ville
                            font_path=self.default_font_path,
                            padding=(0, 0, 0, 0),
                            align="center",  # Toujours centrer pour DOUBLE_SIZE
                        )
                        if img:
                            self.set_align("center")
                            self.print_image(img)
                            self.set_align("left")
                            self.lf(1)
                        else:
                            # Fallback: utiliser les fonts internes avec Font A, double_size et centrage
                            self.set_text_style(font="A", size="ds")
                            self.set_align("center")
                            self.line(stripped_line)
                            self.set_align("left")
                            self.set_text_style(size="normal")
                            self.lf(1)
                    else:
                        # Imprimer directement avec les fonts internes de l'imprimante
                        if is_centered:
                            # Pour les lignes centrées, utiliser set_align avant d'imprimer
                            self.set_align("center")
                        self.line(stripped_line if is_centered else line)
                        if is_centered:
                            self.set_align("left")  # Réinitialiser après
                        self.lf(1)  # Interligne supplémentaire
                else:
                    # Convertir en image (emojis ou caractères spéciaux)
                    if has_emoji or special_chars:
                        print(f"Visual simulator: Converting line to image (emoji={has_emoji}, special_chars={special_chars[:3]}, centered={is_centered})")
                        print(f"Visual simulator: Line content: {repr(stripped_line[:100])}")
                    
                    # Convert line to image (handles emojis and special chars)
                    # Utiliser stripped_line pour enlever les espaces de centrage
                    if has_emoji:
                        # Utiliser _render_mixed_text_to_image pour séparer texte et emojis
                        # Font texte plus petite (16px) pour mieux s'adapter, font emoji normale (20px)
                        print(f"Visual simulator: Calling _render_mixed_text_to_image with text={repr(stripped_line[:50])}, align={text_align}")
                        img = self._render_mixed_text_to_image(
                            text=stripped_line,
                            font_size=20,  # Taille de base pour les emojis
                            text_font_size=16,  # Taille réduite pour le texte
                            text_font_path=self.default_font_path,
                            emoji_font_path=self._get_emoji_font_path(),
                            padding=(0, 0, 0, 0),
                            align=text_align,
                        )
                    else:
                        # Pas d'emojis mais caractères spéciaux, utiliser _render_text_to_image avec taille réduite
                        print(f"Visual simulator: Calling _render_text_to_image with text={repr(stripped_line[:50])}, font_path={self.default_font_path}, align={text_align}")
                        img = self._render_text_to_image(
                            text=stripped_line,
                            font_size=16,  # Taille réduite pour le texte
                            font_path=self.default_font_path,
                            padding=(0, 0, 0, 0),
                            align=text_align,
                        )
                    
                    if img:
                        print(f"Visual simulator: Rendered text image successfully: {img.size}, mode={img.mode}, align={text_align}")
                        # Définir l'alignement avant d'imprimer l'image
                        self.set_align(text_align)
                        # Print image
                        self.print_image(img)
                        self.set_align("left")  # Réinitialiser après
                        self.lf(1)
                    else:
                        print(f"Error: Image rendering returned None for line: {repr(stripped_line[:100])}")
                        print(f"Visual simulator: has_emoji={has_emoji}, PIL_AVAILABLE={PIL_AVAILABLE}")
                        # Fallback: try to print text directly
                        if is_centered:
                            self.set_align("center")
                        self.line(stripped_line if is_centered else line)
                        if is_centered:
                            self.set_align("left")
                        self.lf(1)
                
                # Insérer l'image de ville après le titre de la section ville
                if in_city_section and not city_image_inserted and city_images:
                    print(f"Visual simulator: Printing {len(city_images)} city image(s)")
                    for img_path in city_images:
                        print(f"Visual simulator: Loading city image: {img_path}")
                        success = self.print_image_file(img_path)
                        if not success:
                            print(f"Warning: Failed to load city image: {img_path}")
                        self.set_align("left")  # Réinitialiser après chaque image
                    city_image_inserted = True
                
                # Si on trouve "Photo surprise" et qu'on a des images bonus, les imprimer
                if bonus_images and not bonus_printed and 'Photo surprise' in line:
                    print(f"Visual simulator: Printing {len(bonus_images)} bonus image(s)")
                    for img_path in bonus_images:
                        print(f"Visual simulator: Loading bonus image: {img_path}")
                        success = self.print_image_file(img_path)
                        if not success:
                            print(f"Warning: Failed to load bonus image: {img_path}")
                        self.set_align("left")  # Réinitialiser après chaque image
                    bonus_printed = True
            
            # Feed and cut
            self.lf(1)
            self.cut()
            
            return True
        except Exception as e:
            print(f"Error printing text in simulator: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _render_text_to_image(
        self,
        text: str,
        font_size: int = 24,
        font_path: Optional[str] = None,
        padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
        align: str = "left",
    ) -> Optional['Image.Image']:
        """Override: intercepte _render_text_to_image pour ajouter du logging."""
        print(f"Visual simulator: _render_text_to_image called with text={repr(text[:50])}, font_size={font_size}, font_path={font_path}, align={align}")
        
        if not PIL_AVAILABLE:
            print("Visual simulator: PIL not available")
            return None
        
        font = self._load_font(font_size, font_path)
        if not font:
            print(f"Visual simulator: Failed to load font (font_size={font_size}, font_path={font_path})")
            return None
        
        print(f"Visual simulator: Font loaded successfully")
        
        # Appeler la méthode parent
        img = super()._render_text_to_image(text, font_size, font_path, padding, align)
        if img:
            print(f"Visual simulator: _render_text_to_image returned image: {img.size}, mode={img.mode}")
        else:
            print(f"Visual simulator: _render_text_to_image returned None")
        
        return img

    def _render_mixed_text_to_image(
        self,
        text: str,
        font_size: int = 24,
        text_font_size: Optional[int] = None,
        text_font_path: Optional[str] = None,
        emoji_font_path: Optional[str] = None,
        padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
        align: str = "left",
    ) -> Optional['Image.Image']:
        """Override: intercepte _render_mixed_text_to_image pour ajouter du logging."""
        print(f"Visual simulator: _render_mixed_text_to_image called with text={repr(text[:50])}, font_size={font_size}, text_font_size={text_font_size}, text_font_path={text_font_path}, emoji_font_path={emoji_font_path}, align={align}")
        
        # Appeler la méthode parent
        img = super()._render_mixed_text_to_image(text, font_size, text_font_size, text_font_path, emoji_font_path, padding, align)
        if img:
            print(f"Visual simulator: _render_mixed_text_to_image returned image: {img.size}, mode={img.mode}")
        else:
            print(f"Visual simulator: _render_mixed_text_to_image returned None")
        
        return img
    
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
            print(f"Error: PIL not available or paper_image not initialized for {image_path}")
            return False
        
        try:
            img = self._load_image(image_path)
            if img:
                print(f"Visual simulator: Image loaded successfully: {image_path}, size={img.size}, mode={img.mode}")
                self.print_image(img)
                self.lf(1)
                return True
            else:
                print(f"Warning: _load_image returned None for: {image_path}")
                return False
        except Exception as e:
            print(f"Error printing image in simulator: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"Visual simulator: get_preview_image: current_y={self.current_y}, final_height={final_height}, paper_image.height={self.paper_image.height}")
            cropped = self.paper_image.crop((0, 0, self.width_px, final_height))
            # Vérifier le contenu de l'image finale (diagnostic)
            if cropped:
                pix = cropped.load()
                w, h = cropped.size
                black = sum(1 for y in range(h) for x in range(w) if pix[x, y] < 200)
                print(f"Visual simulator: Final preview: {w}x{h}, black_pixels={black}, ratio={black/(w*h):.4f}")
            return cropped
        return None

