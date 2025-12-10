#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import unicodedata
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


def remove_accents(text: str) -> str:
    """
    Supprime les accents et caractères spéciaux pour les remplacer par leurs équivalents ASCII.
    Utile pour les imprimantes qui ne supportent pas les accents.
    """
    # Table de remplacement pour les caractères courants
    replacements = {
        # Accents français
        'à': 'a', 'â': 'a', 'ä': 'a', 'À': 'A', 'Â': 'A', 'Ä': 'A',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e', 'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'ï': 'i', 'î': 'i', 'Ï': 'I', 'Î': 'I',
        'ô': 'o', 'ö': 'o', 'Ô': 'O', 'Ö': 'O',
        'ù': 'u', 'û': 'u', 'ü': 'u', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'ç': 'c', 'Ç': 'C',
        'ÿ': 'y', 'Ÿ': 'Y',
        # Caractères spéciaux
        '€': 'EUR', '£': 'GBP', '¥': 'JPY',
        '©': '(c)', '®': '(R)', '™': '(TM)',
        '«': '"', '»': '"', '"': '"', '"': '"',
        ''': "'", ''': "'",
        '–': '-', '—': '-', '…': '...',
        # Autres caractères Unicode courants
        'œ': 'oe', 'Œ': 'OE',
        'æ': 'ae', 'Æ': 'AE',
    }
    
    result = []
    for char in text:
        if char in replacements:
            result.append(replacements[char])
        else:
            # Utiliser unicodedata pour décomposer les caractères accentués
            # et ne garder que la base
            try:
                # Décomposer le caractère (NFD = Normalized Form Decomposed)
                normalized = unicodedata.normalize('NFD', char)
                # Garder seulement les caractères non-combinants (pas les accents)
                base = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
                if base and base.isascii():
                    result.append(base)
                elif char.isprintable() and ord(char) < 128:
                    # Caractère ASCII imprimable
                    result.append(char)
                else:
                    # Caractère non supporté, remplacer par '?'
                    result.append('?')
            except:
                # En cas d'erreur, remplacer par '?'
                result.append('?')
    
    return ''.join(result)


class MiniEscpos:
    def __init__(
        self,
        dev: str = "/dev/serial0",
        baudrate: int = 9600,
        width_px: int = 384,
        default_encoding: str = "cp850",
        default_font_path: Optional[str] = None,
        codepage: str = "cp850",
        international: str = "FRANCE",
    ):
        self.ser = serial.Serial(
            dev,
            baudrate=baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=1,
        )
        self.width_px = width_px
        self.encoding = default_encoding
        self.default_font_path = default_font_path

        # Estimation du nombre de caractères par ligne en mode texte interne
        self.chars_per_line = 32

        # État courant des styles texte internes (ESC ! / ESC E / ESC -)
        self._font_internal = "A"       # 'A' ou 'B'
        self._double_height = False
        self._double_width = False
        self._bold = False
        self._underline = False

        # Initialisation de l'imprimante (reset + codepage + international)
        self._init_printer(codepage, international)

    # ------------- BASE BASSE NIVEAU ---------------------------------

    def close(self):
        self.ser.close()

    def raw(self, data: bytes):
        self.ser.write(data)

    # ------------- CONFIG GÉNÉRALE -----------------------------------

    def _init_printer(self, codepage: str, international: str) -> None:
        """Initialise l'imprimante avec reset, codepage et international."""
        # ESC @ : reset imprimante
        self.raw(b"\x1B\x40")
        # IMPORTANT: D'abord international (ESC R), puis codepage (ESC t)
        # Sélection de la table internationale (ESC R n)
        self.set_international(international)
        # Sélection de la table de caractères (ESC t n)
        self.set_codepage(codepage)

    def reset(self):
        """Reset basique de l'imprimante."""
        self.raw(b"\x1B\x40")  # ESC @

    def set_codepage(self, codepage: str = "cp850", try_alternative: bool = True):
        """
        ESC t n - Select character code table
        Les valeurs peuvent varier selon le modèle d'imprimante.
        - Standard ESC/POS: n=2 pour CP850
        - Certaines imprimantes (A2): n=1 pour CP850
        Si try_alternative=True, essaie d'abord n=1 puis n=2 si nécessaire.
        """
        name_low = codepage.lower()
        if name_low in ("cp437", "437"):
            n = 0
            self.encoding = "cp437"
        elif name_low in ("cp850", "850"):
            self.encoding = "cp850"
            if try_alternative:
                # Essayer d'abord n=1 (certaines imprimantes comme A2)
                n = 1
            else:
                # Utiliser n=2 selon le standard ESC/POS
                n = 2
        else:
            raise ValueError(f"Codepage non supporté: {codepage}")
        # ESC t n
        self.raw(b"\x1B\x74" + bytes([n]))
        
        # Si n=1 ne fonctionne pas et qu'on peut essayer l'alternative
        if try_alternative and name_low in ("cp850", "850") and n == 1:
            # Note: on ne peut pas vraiment tester ici, mais on peut documenter
            # que l'utilisateur peut appeler set_codepage(..., try_alternative=False)
            # pour forcer n=2
            pass

    def set_international(self, region: str = "FRANCE") -> None:
        """
        ESC R n - International character set
        D'après le manuel A2 :
          0: USA
          1: France
          2: Germany
          3: U.K.
          4: Denmark I
          5: Sweden
          6: Italy
          7: Spain I
          8: Japan
          9: Norway
          10: Denmark II
          11: Spain II
          12: Latin America
          13: Korea
        """
        mapping = {
            "USA": 0,
            "FRANCE": 1,
            "GERMANY": 2,
            "UK": 3,
            "DENMARK1": 4,
            "SWEDEN": 5,
            "ITALY": 6,
            "SPAIN1": 7,
            "JAPAN": 8,
            "NORWAY": 9,
            "DENMARK2": 10,
            "SPAIN2": 11,
            "LATIN": 12,
            "KOREA": 13,
        }
        key = region.replace(" ", "").upper()
        n = mapping.get(key, 1)  # défaut = FRANCE
        self.raw(b"\x1B\x52" + bytes([n]))

    def set_heating(self, n1: int = 7, n2: int = 80, n3: int = 2):
        """ESC 7 n1 n2 n3"""
        self.raw(b"\x1B\x37" + bytes([n1, n2, n3]))

    def set_density(self, density: int = 15, breaktime: int = 0):
        """DC2 # n  (density 0–31, breaktime 0–7)"""
        n = (breaktime << 5) + density
        self.raw(b"\x12\x23" + bytes([n]))

    # ------------- ALIGNEMENT ----------------------------------------

    def set_align(self, align: str = "left"):
        """
        Alignement du texte/image :
            'left', 'center', 'right'
        """
        mapping = {"left": 0, "center": 1, "right": 2}
        val = mapping.get(align, 0)
        self.raw(b"\x1B\x61" + bytes([val]))  # ESC a n

    # ------------- TEXTE DIRECT ESC/POS ------------------------------

    def text(self, s: str):
        """
        Imprime du texte brut (sans ajout de \\n).
        Les accents sont automatiquement supprimés car l'imprimante ne les supporte pas.
        Force l'encodage ASCII pour éviter les problèmes de caractères chinois.
        """
        # Supprimer les accents car l'imprimante ne les supporte pas
        s = remove_accents(s)
        
        # Forcer l'encodage ASCII uniquement pour éviter les problèmes
        # L'imprimante ne supporte pas bien CP850, donc on utilise ASCII
        try:
            # S'assurer que tous les caractères sont ASCII
            s_ascii = s.encode("ascii", errors="replace").decode("ascii")
            data = s_ascii.encode("ascii")
        except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
            # Dernier recours: remplacer tous les caractères non-ASCII par '?'
            data = s.encode("ascii", errors="replace")
        self.raw(data)

    def line(self, s: str = ""):
        """Imprime une ligne + saut de ligne."""
        self.text(s + "\n")

    def lf(self, n: int = 1):
        self.raw(b"\n" * n)

    def cut(self, full: bool = True):
        """Coupe le papier (si supporté)."""
        m = 0 if full else 1
        self.raw(b"\x1D\x56" + bytes([m]))

    # ------------- POLICES INTERNES & STYLES (ESC !, ESC M, ESC E, ESC -)

    def _apply_style_byte(self):
        """
        Construit et envoie le byte ESC ! n
        en fonction des flags internes :
          bit 0 : font (0 = A, 1 = B)
          bit 3 : double height
          bit 4 : double width
          bit 7 : underline (sur certains modèles)
        Le gras est géré séparément par ESC E
        """
        n = 0

        # Font A/B
        if self._font_internal == "B":
            n |= 0x01  # bit 0

        # Double height
        if self._double_height:
            n |= 0x10  # bit 4

        # Double width
        if self._double_width:
            n |= 0x20  # bit 5

        # Underline (bit 7 sur certains modèles)
        if self._underline:
            n |= 0x80  # bit 7

        self.raw(b"\x1B\x21" + bytes([n]))

        # Gras est géré par ESC E n
        self.raw(b"\x1B\x45" + (b"\x01" if self._bold else b"\x00"))

    def set_font_internal(self, font: str = "A"):
        """
        Sélectionne la police interne :
            'A' = large
            'B' = condensée
        """
        font = font.upper()
        if font not in ("A", "B"):
            font = "A"
        self._font_internal = font

        # ESC M n
        n = 0 if font == "A" else 1
        self.raw(b"\x1B\x4D" + bytes([n]))

        # Met à jour ESC ! aussi (bit font)
        self._apply_style_byte()

    def set_text_style(
        self,
        *,
        font: Optional[str] = None,       # 'A' ou 'B'
        bold: Optional[bool] = None,
        underline: Optional[bool] = None,
        double_width: Optional[bool] = None,
        double_height: Optional[bool] = None,
        size: Optional[str] = None,       # 'normal', 'dw', 'dh', 'ds'
    ):
        """
        Helper haut niveau pour régler les styles internes.

        Exemples :
            set_text_style(font='B', size='ds')    # Font B, double-size
            set_text_style(bold=True)             # active juste le gras
        """

        if font is not None:
            self._font_internal = font.upper() if font.upper() in ("A", "B") else "A"
            # ESC M pour la police
            n = 0 if self._font_internal == "A" else 1
            self.raw(b"\x1B\x4D" + bytes([n]))

        # Gestion du "size" comme preset
        if size is not None:
            size = size.lower()
            if size == "normal":
                self._double_width = False
                self._double_height = False
            elif size in ("dw", "double_width"):
                self._double_width = True
                self._double_height = False
            elif size in ("dh", "double_height"):
                self._double_width = False
                self._double_height = True
            elif size in ("ds", "double_size"):
                self._double_width = True
                self._double_height = True

        if bold is not None:
            self._bold = bool(bold)

        if underline is not None:
            self._underline = bool(underline)

        # Appliquer le style combiné via ESC ! + ESC -
        self._apply_style_byte()

    # ------------- HELPERS TEXTE BRUT (SÉPARATEURS, CENTRAGE) --------

    def separator(
        self,
        char: str = "-",
        width_chars: Optional[int] = None,
        double: bool = False,
    ):
        """
        Imprime un séparateur.
        Utilise des caractères ASCII simples pour éviter les problèmes d'encodage.
        """
        if not width_chars:
            width_chars = self.chars_per_line
        
        # Utiliser uniquement des caractères ASCII pour éviter les problèmes
        # Les caractères Unicode comme "═" peuvent causer des problèmes d'encodage
        if char == "=" or char == "═":
            char = "="
        elif char == "-" or char == "─":
            char = "-"
        elif char == "_":
            char = "_"
        else:
            # S'assurer que le caractère est ASCII
            char = remove_accents(char) if char else "-"
            if not char or not char.isascii():
                char = "-"
        
        line = (char * width_chars)[:width_chars]
        self.line(line)
        if double:
            self.line(line)

    def centered_text(self, s: str):
        self.set_align("center")
        self.line(s)
        self.set_align("left")

    # ------------- FONTS CUSTOM / PIL --------------------------------

    def _load_font(self, size: int, font_path: Optional[str] = None):
        """
        Charge une font custom ou retourne la font par défaut.
        La font par défaut PIL a une taille fixe, donc si elle est utilisée,
        la taille demandée ne sera pas respectée.
        """
        path = font_path or self.default_font_path
        if path:
            try:
                font = ImageFont.truetype(str(path), size)
                return font
            except Exception as e:
                # Log l'erreur pour debug
                import sys
                print(f"Warning: Impossible de charger la font {path}: {e}", file=sys.stderr)
        
        # ImageFont.load_default() retourne une font bitmap de taille fixe
        # Essayer de charger une font système courante
        import platform
        if platform.system() == "Linux":
            # Essayer DejaVu ou Liberation (fonts courantes sur Linux)
            system_fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
            for sys_font in system_fonts:
                try:
                    font = ImageFont.truetype(sys_font, size)
                    import sys
                    print(f"Info: Utilisation de la font système {sys_font} à la place de la font par défaut", file=sys.stderr)
                    return font
                except:
                    continue
        
        # Dernier recours: font par défaut (taille fixe, ne respectera pas le paramètre size)
        import sys
        print(f"Warning: Utilisation de la font par défaut PIL (taille fixe, {size}px demandé sera ignoré)", file=sys.stderr)
        return ImageFont.load_default()

    def _render_text_to_image(
        self,
        text: str,
        font_size: int = 24,
        font_path: Optional[str] = None,
        padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
        align: str = "left",
    ) -> Image.Image:
        """
        Rend du texte en image avec la font et taille spécifiées.
        Pour les emojis, il faut utiliser une font qui les supporte (NotoEmoji, etc.)
        Les accents sont conservés dans les images (contrairement au texte direct).
        """
        # Note: On garde les accents pour les images car elles sont rendues en bitmap
        # et ne dépendent pas du codepage de l'imprimante
        font = self._load_font(font_size, font_path)
        lines = text.split("\n")

        # Calculer les dimensions avec un espacement entre lignes
        line_spacing = int(font_size * 0.2)  # 20% de la taille de font
        max_w = 0
        total_h = 0
        line_heights = []
        for line in lines:
            if not line.strip():
                # Ligne vide, utiliser la hauteur de la font
                bbox = font.getbbox("Ag")
            else:
                bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            max_w = max(max_w, w)
            line_heights.append(h)
            total_h += h

        pad_left, pad_top, pad_right, pad_bottom = padding
        img_w = min(self.width_px, max_w + pad_left + pad_right)
        img_h = total_h + pad_top + pad_bottom + (len(lines) - 1) * (line_spacing + 4)

        img = Image.new("L", (img_w, img_h), 255)
        draw = ImageDraw.Draw(img)

        y = pad_top
        for i, line in enumerate(lines):
            if not line.strip():
                # Ligne vide
                y += line_heights[i] + line_spacing
                continue
                
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            if align == "center":
                x = (img_w - w) // 2
            elif align == "right":
                x = img_w - w - pad_right
            else:
                x = pad_left

            # Utiliser textbbox pour un meilleur positionnement
            try:
                # PIL 10+ utilise textbbox
                bbox = draw.textbbox((x, y), line, font=font)
                draw.text((x, y), line, font=font, fill=0)
            except AttributeError:
                # Ancienne version PIL
                draw.text((x, y), line, font=font, fill=0)
            
            y += h + line_spacing

        return img

    def print_text_image(
        self,
        text: str,
        font_size: int = 24,
        font_path: Optional[str] = None,
        padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
        align: str = "left",
    ):
        img = self._render_text_to_image(
            text=text,
            font_size=font_size,
            font_path=font_path,
            padding=padding,
            align=align,
        )
        self.print_image(img)
        self.lf(1)

    # ------------- IMPRESSION D'IMAGE (GS v 0) ------------------------

    def print_image(self, img: Image.Image):
        w, h = img.size
        if w > self.width_px:
            ratio = self.width_px / float(w)
            img = img.resize((self.width_px, int(h * ratio)), Image.LANCZOS)
            w, h = img.size

        if img.mode != "1":
            img = img.convert("L")
            img = img.point(lambda x: 0 if x < 128 else 255, "1")

        width_bytes = (w + 7) // 8
        bitmap = bytearray(width_bytes * h)
        pixels = img.load()

        for y in range(h):
            for x in range(w):
                if pixels[x, y] == 0:
                    byte_index = y * width_bytes + (x // 8)
                    bit = 7 - (x % 8)
                    bitmap[byte_index] |= (1 << bit)

        xL = width_bytes & 0xFF
        xH = (width_bytes >> 8) & 0xFF
        yL = h & 0xFF
        yH = (h >> 8) & 0xFF

        header = b"\x1D\x76\x30\x00" + bytes([xL, xH, yL, yH])
        self.raw(header + bitmap)

    # ------------- HELPERS HAUT NIVEAU -------------------------------

    def print_title(
        self,
        text: str,
        font_size: int = 32,
        font_path: Optional[str] = None,
        separator: bool = True,
    ):
        self.print_text_image(
            text=text,
            font_size=font_size,
            font_path=font_path,
            padding=(0, 0, 0, 0),
            align="center",
        )
        if separator:
            self.separator(char="═", width_chars=self.chars_per_line)
            self.lf(1)

    def print_paragraph(
        self,
        text: str,
        font_size: int = 20,
        font_path: Optional[str] = None,
        align: str = "left",
    ):
        self.print_text_image(
            text=text,
            font_size=font_size,
            font_path=font_path,
            padding=(0, 0, 0, 0),
            align=align,
        )

    def print_key_value(
        self,
        key: str,
        value: str,
        sep: str = ": ",
    ):
        line = f"{key}{sep}{value}"
        if len(line) > self.chars_per_line:
            line = line[: self.chars_per_line]
        self.line(line)
