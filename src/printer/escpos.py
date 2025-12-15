"""ESC/POS printer implementation with low-level control."""

import serial
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Précharger PIL au niveau module pour éviter délai à chaque impression
# (PIL est lent à charger sur Raspberry Pi, ~10s)
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None

from .printer import Printer




class EscposPrinter(Printer):
    """ESC/POS printer implementation with low-level control."""

    def __init__(
        self,
        device: str = '/dev/serial0',
        width: int = 58,
        baudrate: int = 9600,
        timeout: int = 1,
        width_px: int = 384,
        default_encoding: str = "cp850",
        default_font_path: Optional[str] = None,
        codepage: str = "cp850",
        international: str = "FRANCE",
    ):
        """Initialize ESC/POS printer.
        
        L'imprimante est configurée par défaut avec :
        - International character set: FRANCE (R=1) - nécessaire pour les accents français
        - Codepage: cp850 - supporte les caractères accentués français
        
        Args:
            device: Device path (serial)
            width: Ticket width in characters
            baudrate: Serial baudrate (default: 9600)
            timeout: Serial timeout in seconds (default: 1)
            width_px: Width in pixels (default: 384 for 58mm)
            default_encoding: Default encoding (default: cp850)
            default_font_path: Optional path to default font
            codepage: Codepage to use (default: cp850)
            international: International character set (default: FRANCE)
                Doit être "FRANCE" (R=1) pour supporter les accents français.
        """
        super().__init__(width)
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout
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
        
        self._ser = None
        
        # Système de logging des commandes ESC/POS
        self._enable_logging = os.getenv('PRINTER_LOG_COMMANDS', 'true').lower() == 'true'
        self._log_file = None
        self._log_buffer = []
        if self._enable_logging:
            self._init_logging()
        
        self._init_printer(codepage, international)

    def _init_logging(self) -> None:
        """Initialise le système de logging des commandes ESC/POS."""
        try:
            # Créer le répertoire logs s'il n'existe pas
            project_root = Path(__file__).parent.parent.parent
            logs_dir = project_root / 'logs'
            logs_dir.mkdir(exist_ok=True)
            
            # Créer un fichier de log avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f'printer_commands_{timestamp}.log'
            self._log_file = logs_dir / log_filename
            
            # Écrire l'en-tête
            with open(self._log_file, 'w', encoding='utf-8') as f:
                f.write(f"# Log des commandes ESC/POS - {datetime.now().isoformat()}\n")
                f.write(f"# Device: {self.device}\n")
                f.write(f"# Baudrate: {self.baudrate}\n")
                f.write(f"# Format: [timestamp] [hex] [description]\n")
                f.write(f"#\n\n")
            
            print(f"✓ Logging des commandes ESC/POS activé: {self._log_file}")
        except Exception as e:
            print(f"⚠ Impossible d'initialiser le logging: {e}")
            self._enable_logging = False
    
    def _log_command(self, data: bytes, description: str = "") -> None:
        """Enregistre une commande ESC/POS dans le fichier de log."""
        if not self._enable_logging or not self._log_file:
            return
        
        try:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            hex_str = ' '.join(f'{b:02X}' for b in data)
            
            # Décoder les commandes ESC/POS connues
            cmd_desc = self._decode_escpos_command(data)
            if cmd_desc:
                description = f"{description} ({cmd_desc})" if description else cmd_desc
            
            # Limiter la longueur de la description pour la lisibilité
            if len(data) > 100:
                hex_str = ' '.join(f'{b:02X}' for b in data[:50]) + f" ... ({len(data)} bytes)"
            
            log_line = f"[{timestamp}] {hex_str}"
            if description:
                log_line += f" # {description}"
            log_line += "\n"
            
            # Bufferiser pour éviter trop d'écritures disque
            self._log_buffer.append(log_line)
            
            # Écrire par batch de 10 lignes ou si c'est une commande importante
            if len(self._log_buffer) >= 10 or self._is_important_command(data):
                self._flush_log_buffer()
        except Exception:
            pass  # Ne pas bloquer l'impression en cas d'erreur de logging
    
    def _decode_escpos_command(self, data: bytes) -> str:
        """Décode une commande ESC/POS en description lisible."""
        if not data:
            return ""
        
        # Commandes simples
        if data == b"\x1B\x40":
            return "RESET"
        elif data == b"\n":
            return "LF"
        elif data.startswith(b"\x1B\x52"):  # ESC R n
            n = data[2] if len(data) > 2 else 0
            regions = {0: "USA", 1: "FRANCE", 2: "GERMANY", 3: "UK", 4: "DENMARK", 
                      5: "SWEDEN", 6: "ITALY", 7: "SPAIN", 8: "JAPAN", 9: "NORWAY"}
            return f"ESC R {n} (International: {regions.get(n, 'UNKNOWN')})"
        elif data.startswith(b"\x1B\x74"):  # ESC t n
            n = data[2] if len(data) > 2 else 0
            codepages = {0: "cp437/cp850", 1: "cp437", 2: "cp850", 3: "cp860", 
                         4: "cp863", 5: "cp865", 6: "cp852", 7: "cp858"}
            return f"ESC t {n} (Codepage: {codepages.get(n, 'UNKNOWN')})"
        elif data.startswith(b"\x1B\x61"):  # ESC a n
            n = data[2] if len(data) > 2 else 0
            aligns = {0: "LEFT", 1: "CENTER", 2: "RIGHT"}
            return f"ESC a {n} (Align: {aligns.get(n, 'UNKNOWN')})"
        elif data.startswith(b"\x1B\x21"):  # ESC ! n
            n = data[2] if len(data) > 2 else 0
            flags = []
            if n & 0x01: flags.append("FONT_B")
            if n & 0x10: flags.append("DOUBLE_HEIGHT")
            if n & 0x20: flags.append("DOUBLE_WIDTH")
            if n & 0x80: flags.append("UNDERLINE")
            return f"ESC ! {n:02X} ({', '.join(flags) if flags else 'NORMAL'})"
        elif data.startswith(b"\x1B\x45"):  # ESC E n
            n = data[2] if len(data) > 2 else 0
            return f"ESC E {n} (Bold: {'ON' if n else 'OFF'})"
        elif data.startswith(b"\x1D\x56"):  # GS V m
            m = data[2] if len(data) > 2 else 0
            return f"GS V {m} (CUT: {'FULL' if m == 0 else 'PARTIAL'})"
        elif data.startswith(b"\x1B\x37"):  # ESC 7 n1 n2 n3
            if len(data) >= 5:
                n1, n2, n3 = data[2], data[3], data[4]
                return f"ESC 7 {n1} {n2} {n3} (Heating: dots={n1}, time={n2}, interval={n3})"
        elif data.startswith(b"\x12\x23"):  # DC2 # n
            if len(data) >= 3:
                n = data[2]
                density = n & 0x1F
                breaktime = (n >> 5) & 0x07
                return f"DC2 # {n:02X} (Density={density}, Breaktime={breaktime})"
        elif data.startswith(b"\x1D\x76\x30"):  # GS v 0 (Image)
            return "GS v 0 (PRINT_IMAGE)"
        elif len(data) > 0 and all(32 <= b <= 126 or b in [10, 13] for b in data):
            # Texte ASCII imprimable
            try:
                text = data.decode('ascii', errors='replace')[:50]
                return f"TEXT: {repr(text)}"
            except:
                pass
        
        return ""
    
    def _is_important_command(self, data: bytes) -> bool:
        """Détermine si une commande est importante (doit être flush immédiatement)."""
        if not data:
            return False
        # Commandes importantes: RESET, CUT, IMAGE, ALIGN, CODEPAGE, INTERNATIONAL
        important_prefixes = [b"\x1B\x40", b"\x1D\x56", b"\x1D\x76", b"\x1B\x61", 
                             b"\x1B\x52", b"\x1B\x74", b"\x1B\x37", b"\x12\x23"]
        return any(data.startswith(prefix) for prefix in important_prefixes)
    
    def _flush_log_buffer(self) -> None:
        """Écrit le buffer de log dans le fichier."""
        if not self._log_buffer or not self._log_file:
            return
        try:
            with open(self._log_file, 'a', encoding='utf-8') as f:
                f.writelines(self._log_buffer)
            self._log_buffer.clear()
        except Exception:
            pass
    
    def _init_printer(self, codepage: str, international: str) -> None:
        """Initialize printer connection and settings."""
        try:
            self._ser = serial.Serial(
                self.device,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=self.timeout
            )
            
            # Initialisation de l'imprimante (reset + codepage + international)
            self.reset()
            # IMPORTANT: D'abord international (ESC R), puis codepage (ESC t)
            # L'ordre est crucial : ESC R doit être envoyé avant ESC t
            # Avec R=1 (FRANCE) + cp850, les accents français sont supportés
            self.set_international(international)
            self.set_codepage(codepage)
            
            # Appliquer les paramètres optimaux d'impression
            # Paramètres optimaux (basés sur tests/test_reglages_imprimante.py TEST 2) :
            # - heating_dots=7 (CRITIQUE - ne pas changer)
            # - heating_time=180 (paramètre optimal du TEST 2)
            # - interval=2 (CRITIQUE - ne pas changer)
            # - density=15 (plage 12-18 acceptable)
            # - breaktime=0 (optimal, plage 0-2 acceptable)
            self.set_heating(n1=7, n2=180, n3=2)
            self.set_density(density=15, breaktime=0)
            
            # Flush le log après l'initialisation
            self._flush_log_buffer()
            
            print(f"✓ ESC/POS printer connected via serial: {self.device}")
        except Exception as e:
            print(f"Warning: Could not initialize ESC/POS printer: {e}")
            self._ser = None

    # ------------- BASE BASSE NIVEAU ---------------------------------

    def close(self) -> None:
        """Close printer connection."""
        # Flush le buffer de log avant de fermer
        self._flush_log_buffer()
        
        if self._ser:
            try:
                self._ser.close()
            except:
                pass
        
        if self._enable_logging and self._log_file:
            try:
                with open(self._log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n# Fin du log - {datetime.now().isoformat()}\n")
            except:
                pass

    def raw(self, data: bytes, description: str = "") -> None:
        """Send raw bytes to printer.
        
        Args:
            data: Bytes to send
            description: Optional description for logging
        """
        if self._ser:
            # Logger la commande avant l'envoi
            self._log_command(data, description)
            self._ser.write(data)

    # ------------- CONFIG GÉNÉRALE -----------------------------------

    def reset(self) -> None:
        """Reset basique de l'imprimante."""
        self.raw(b"\x1B\x40", description="RESET")

    def set_codepage(self, codepage: str = "cp850", try_alternative: bool = True) -> None:
        """
        ESC t n - Select character code table
        
        Configure la table de caractères (codepage) de l'imprimante.
        Le codepage cp850 supporte les caractères accentués français (à, é, è, ç, etc.)
        lorsqu'il est combiné avec international="FRANCE" (R=1).
        
        D'après tests/cp437_850.py, il faut R=1 et t=0 pour avoir l'encodage en français.
        
        Args:
            codepage: Nom du codepage ("cp850" ou "cp437")
            try_alternative: Ignoré, conservé pour compatibilité (toujours t=0 pour cp850)
        """
        name_low = codepage.lower()
        if name_low in ("cp437", "437"):
            n = 0
            self.encoding = "cp437"
        elif name_low in ("cp850", "850"):
            self.encoding = "cp850"
            # D'après tests/cp437_850.py, t=0 est nécessaire pour l'encodage français avec R=1
            n = 0
        else:
            raise ValueError(f"Codepage non supporté: {codepage}")
        # ESC t n
        self.raw(b"\x1B\x74" + bytes([n]), description=f"SET_CODEPAGE ({codepage}, n={n})")

    def set_international(self, region: str = "FRANCE") -> None:
        """
        ESC R n - International character set
        
        Configure le jeu de caractères internationaux de l'imprimante.
        IMPORTANT: Pour supporter les accents français (à, é, è, ç, etc.),
        il faut utiliser region="FRANCE" (R=1) combiné avec codepage="cp850".
        
        Valeurs supportées (d'après le manuel A2) :
          0: USA, 1: France, 2: Germany, 3: U.K., 4: Denmark I,
          5: Sweden, 6: Italy, 7: Spain I, 8: Japan, 9: Norway,
          10: Denmark II, 11: Spain II, 12: Latin America, 13: Korea
        
        Args:
            region: Nom de la région (défaut: "FRANCE" pour R=1)
        """
        mapping = {
            "USA": 0, "FRANCE": 1, "GERMANY": 2, "UK": 3,
            "DENMARK1": 4, "SWEDEN": 5, "ITALY": 6, "SPAIN1": 7,
            "JAPAN": 8, "NORWAY": 9, "DENMARK2": 10, "SPAIN2": 11,
            "LATIN": 12, "KOREA": 13,
        }
        key = region.replace(" ", "").upper()
        n = mapping.get(key, 1)  # défaut = FRANCE
        self.raw(b"\x1B\x52" + bytes([n]), description=f"SET_INTERNATIONAL ({region}, n={n})")

    def set_heating(self, n1: int = 7, n2: int = 80, n3: int = 2) -> None:
        """
        ESC 7 n1 n2 n3 - Set heating parameters.
        
        Paramètres optimaux (basés sur documents/rapport_essais_impression.md) :
        - n1 (heating_dots): 7 (CRITIQUE - ne pas changer)
        - n2 (heating_time): 80 (plage 60-100 acceptable, unit: 10µs)
        - n3 (interval): 2 (CRITIQUE - ne pas changer, unit: 10µs)
        
        Args:
            n1: Heating dots (0-255, default: 7)
            n2: Heating time (3-255, default: 80 = 800µs)
            n3: Heating interval (0-255, default: 2 = 20µs)
        """
        self.raw(b"\x1B\x37" + bytes([n1, n2, n3]), description=f"SET_HEATING (dots={n1}, time={n2}, interval={n3})")

    def set_density(self, density: int = 15, breaktime: int = 0) -> None:
        """
        DC2 # n - Set density & breaktime.
        
        Paramètres optimaux (basés sur documents/rapport_essais_impression.md) :
        - density: 15 (plage 12-18 acceptable)
          Formule: Density = 50% + 5% × density
          Exemple: density=15 → 50% + 75% = 125% (saturation optimale)
        - breaktime: 0 (optimal, plage 0-2 acceptable)
          Formule: Break time = breaktime × 250µs
        
        Args:
            density: Density level (0-31, default: 15)
            breaktime: Break time (0-7, default: 0)
        """
        n = (breaktime << 5) + density
        self.raw(b"\x12\x23" + bytes([n]), description=f"SET_DENSITY (density={density}, breaktime={breaktime})")

    # ------------- ALIGNEMENT ----------------------------------------

    def set_align(self, align: str = "left") -> None:
        """
        Alignement du texte/image :
            'left', 'center', 'right'
        """
        mapping = {"left": 0, "center": 1, "right": 2}
        val = mapping.get(align, 0)
        self.raw(b"\x1B\x61" + bytes([val]), description=f"SET_ALIGN ({align})")

    # ------------- TEXTE DIRECT ESC/POS ------------------------------

    def text(self, s: str) -> None:
        """
        Imprime du texte brut (sans ajout de \\n).
        
        Les accents français sont supportés si l'imprimante est configurée avec :
        - international="FRANCE" (R=1) - configuré par défaut
        - codepage="cp850" - configuré par défaut
        
        Le texte est encodé selon self.encoding (cp850 par défaut) qui supporte
        les caractères accentués français.
        """
        if not self._ser:
            return
        
        # Encoder avec le codepage configuré (cp850 par défaut, supporte les accents)
        try:
            data = s.encode(self.encoding, errors="replace")
        except (UnicodeEncodeError, LookupError):
            # Fallback: essayer cp850 si l'encoding n'est pas valide
            try:
                data = s.encode("cp850", errors="replace")
            except:
                # Dernier recours: ASCII avec remplacement
                data = s.encode("ascii", errors="replace")
        self.raw(data)

    def line(self, s: str = "") -> None:
        """Imprime une ligne + saut de ligne."""
        self.text(s + "\n")

    def lf(self, n: int = 1) -> None:
        """Line feed."""
        self.raw(b"\n" * n)

    def cut(self, full: bool = True) -> None:
        """Coupe le papier (si supporté)."""
        m = 0 if full else 1
        self.raw(b"\x1D\x56" + bytes([m]), description=f"CUT ({'FULL' if full else 'PARTIAL'})")

    # ------------- POLICES INTERNES & STYLES (ESC !, ESC M, ESC E, ESC -)

    def _apply_style_byte(self) -> None:
        """
        Construit et envoie le byte ESC ! n
        en fonction des flags internes :
          bit 0 : font (0 = A, 1 = B)
          bit 4 : double height
          bit 5 : double width
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

    def set_font_internal(self, font: str = "A") -> None:
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
    ) -> None:
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
        font_path: Optional[str] = None,
    ) -> None:
        """
        Imprime un séparateur avec des caractères ASCII simples ou Unicode.
        Utilise du texte simple pour les caractères ASCII, images pour Unicode complexe.
        
        Args:
            char: Caractère de séparation ('-', '─', '=', '═', '_', '━')
            width_chars: Largeur en caractères (défaut: chars_per_line)
            double: Si True, imprime deux lignes
            font_path: Chemin vers la font à utiliser (uniquement pour Unicode, défaut: default_font_path)
        """
        if not width_chars:
            width_chars = self.chars_per_line
        
        # Caractères ASCII simples qui peuvent être imprimés directement
        ascii_chars = {"-", "=", "_"}
        
        # Caractères Unicode complexes qui nécessitent une image
        unicode_chars = {"─", "═", "━"}
        
        # Si c'est un caractère ASCII simple, utiliser du texte direct
        if char in ascii_chars:
            line = (char * width_chars)[:width_chars]
            self.line(line)
            if double:
                self.line(line)
            return
        
        # Pour les caractères Unicode complexes, utiliser une image si nécessaire
        # Mapping des caractères vers leurs équivalents Unicode continus
        unicode_mapping = {
            "─": "─",      # U+2500 Box Drawings Light Horizontal
            "═": "═",      # U+2550 Box Drawings Double Horizontal
            "━": "━",      # U+2501 Box Drawings Heavy Horizontal
        }
        
        unicode_char = unicode_mapping.get(char, "─")
        
        # Utiliser la font spécifiée ou la font par défaut
        font_to_use = font_path or self.default_font_path
        font_size = 20
        
        # Calculer la largeur réelle en pixels
        if PIL_AVAILABLE and font_to_use:
            try:
                test_font = self._load_font(font_size, font_to_use)
                if test_font:
                    bbox = test_font.getbbox(unicode_char)
                    char_width = bbox[2] - bbox[0]
                    target_width_px = min(self.width_px, int(char_width * width_chars))
                else:
                    target_width_px = self.width_px
            except:
                target_width_px = self.width_px
        else:
            target_width_px = self.width_px
        
        # Créer le séparateur en répétant le caractère
        num_chars = max(200, int(target_width_px / 8))
        separator_text = unicode_char * num_chars
        
        # Rendre le séparateur en image
        img = self._render_text_to_image(
            text=separator_text,
            font_size=font_size,
            font_path=font_to_use,
            padding=(0, 0, 0, 0),
            align="left",
        )
        
        if img:
            # Tronquer l'image à la largeur cible
            w, h = img.size
            if w > target_width_px:
                img = img.crop((0, 0, target_width_px, h))
            
            self.print_image(img)
            self.lf(1)
            
            if double:
                self.print_image(img)
                self.lf(1)
        else:
            # Fallback: utiliser du texte ASCII si l'image ne peut pas être créée
            ascii_char = "-" if char in ("-", "─") else "=" if char in ("=", "═") else "_"
            line = (ascii_char * width_chars)[:width_chars]
            self.line(line)
            if double:
                self.line(line)

    def centered_text(self, s: str) -> None:
        """Print centered text."""
        self.set_align("center")
        self.line(s)
        self.set_align("left")

    # ------------- FONTS CUSTOM / PIL --------------------------------

    @staticmethod
    def _find_emoji_fonts(fonts_dir: Optional[str] = None) -> list[str]:
        """
        Détecte automatiquement les fonts emoji disponibles.
        Priorité: NotoEmoji-Bold > NotoEmoji-Regular > NotoEmoji > autres fonts emoji
        
        Args:
            fonts_dir: Répertoire où chercher les fonts (défaut: fonts/ du projet)
            
        Returns:
            Liste des chemins vers les fonts emoji trouvées, par ordre de priorité
        """
        if not PIL_AVAILABLE:
            return []
        
        from pathlib import Path
        
        # Déterminer le répertoire de fonts
        if fonts_dir:
            search_dir = Path(fonts_dir)
        else:
            # Chercher dans fonts/ du projet
            project_root = Path(__file__).parent.parent.parent
            search_dir = project_root / "fonts"
        
        if not search_dir.exists():
            return []
        
        # Ordre de priorité pour les fonts emoji
        emoji_font_priority = [
            "NotoEmoji-Bold.ttf",
            "NotoEmoji-Regular.ttf",
            "NotoEmoji.ttf",
        ]
        
        found_fonts = []
        
        # Chercher les fonts prioritaires
        for font_name in emoji_font_priority:
            font_path = search_dir / font_name
            if font_path.exists():
                found_fonts.append(str(font_path))
        
        # Chercher d'autres fonts emoji (mais pas Segoe UI Emoji - Windows uniquement)
        for font_file in search_dir.glob("*.ttf"):
            font_name_lower = font_file.name.lower()
            # Ignorer Segoe UI Emoji (Windows uniquement)
            if "segoe" in font_name_lower and "emoji" in font_name_lower:
                continue
            # Chercher d'autres fonts emoji
            if "emoji" in font_name_lower and str(font_file) not in found_fonts:
                found_fonts.append(str(font_file))
        
        return found_fonts

    def _load_font(self, size: int, font_path: Optional[str] = None):
        """
        Charge une font custom ou retourne la font par défaut.
        La font par défaut PIL a une taille fixe, donc si elle est utilisée,
        la taille demandée ne sera pas respectée.
        """
        if not PIL_AVAILABLE:
            return None
            
        path = font_path or self.default_font_path
        if path:
            from pathlib import Path
            font_file = Path(path)
            
            # Vérifier que le fichier existe
            if not font_file.exists():
                print(f"Warning: Font file not found: {path}")
            else:
                # Vérifier que c'est un vrai fichier TTF
                try:
                    with open(font_file, 'rb') as f:
                        header = f.read(12)
                        # Les fichiers TTF/OTF commencent par des magic bytes spécifiques:
                        # TTF: 0x00 0x01 0x00 0x00 ou 'OTTO' pour OTF
                        # HTML commence généralement par <!DOCTYPE ou <html
                        if header.startswith(b'<!') or header.startswith(b'<htm') or header.startswith(b'<HTML'):
                            print(f"Warning: {path} appears to be an HTML file, not a valid font file.")
                            print(f"  This usually means the file was incorrectly downloaded (e.g., a GitHub error page).")
                            print(f"  Please download the correct TTF file from the original source.")
                        elif not (header[:4] == b'\x00\x01\x00\x00' or header[:4] == b'OTTO' or 
                                 header[:4] == b'ttcf' or header[:4] == b'wOFF'):
                            # Pas un format de font reconnu
                            print(f"Warning: {path} does not appear to be a valid font file.")
                            print(f"  Expected TTF/OTF format, but file header is: {header[:4]}")
                        else:
                            # Essayer de charger la font
                            try:
                                font = ImageFont.truetype(str(path), size)
                                return font
                            except Exception as e:
                                print(f"Warning: Impossible de charger la font {path}: {e}")
                                print(f"  Le fichier existe mais n'est pas un format de font valide.")
                except Exception as e:
                    print(f"Warning: Erreur lors de la lecture du fichier font {path}: {e}")
        
        # Essayer de charger une font système courante
        import platform
        if platform.system() == "Linux":
            system_fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            ]
            for sys_font in system_fonts:
                try:
                    font = ImageFont.truetype(sys_font, size)
                    return font
                except:
                    continue
        
        # Dernier recours: font par défaut (taille fixe)
        return ImageFont.load_default()

    def _check_char_support(self, char: str, font_path: Optional[str] = None, font_size: int = 24) -> bool:
        """
        Vérifie si un caractère (ou emoji) est supporté par la font.
        
        Args:
            char: Caractère à vérifier
            font_path: Chemin vers la font (défaut: default_font_path)
            font_size: Taille de la font pour le test
            
        Returns:
            True si le caractère est supporté, False sinon
        """
        if not PIL_AVAILABLE:
            return False
        
        font = self._load_font(font_size, font_path)
        if not font:
            return False
        
        try:
            # Essayer de mesurer le caractère
            # Si la font ne supporte pas le caractère, getbbox peut retourner (0,0,0,0)
            # ou lever une exception
            bbox = font.getbbox(char)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            
            # Si la largeur et hauteur sont nulles, le caractère n'est probablement pas supporté
            if width == 0 and height == 0:
                return False
            
            # Vérifier aussi en rendant une petite image de test
            # Certaines fonts retournent un bbox mais ne rendent rien
            test_img = Image.new("L", (50, 50), 255)
            test_draw = ImageDraw.Draw(test_img)
            try:
                test_draw.text((0, 0), char, font=font, fill=0)
                # Vérifier si quelque chose a été dessiné (pixels noirs)
                pixels = test_img.load()
                has_black = False
                for y in range(50):
                    for x in range(50):
                        if pixels[x, y] < 128:  # Pixel noir ou gris
                            has_black = True
                            break
                    if has_black:
                        break
                return has_black
            except:
                return False
        except Exception:
            return False

    def test_emoji_support(
        self,
        emoji_list: Optional[list[str]] = None,
        font_path: Optional[str] = None,
        font_size: int = 24,
    ) -> dict[str, bool]:
        """
        Teste quels emojis sont supportés par la font sans les imprimer.
        Économise le papier en ne testant que la disponibilité.
        
        Args:
            emoji_list: Liste d'emojis à tester (défaut: liste courante d'emojis)
            font_path: Chemin vers la font emoji à tester
            font_size: Taille de la font pour le test
            
        Returns:
            Dictionnaire {emoji: bool} indiquant si chaque emoji est supporté
        """
        if emoji_list is None:
            # Liste d'emojis courants à tester
            emoji_list = [
                "🎉", "✅", "🚀", "🎯", "🏆", "⭐", "💯", "🔥", "😄", "😊", "😁", "😆",
                "😅", "🤣", "😂", "🥲", "📱", "💻", "🖥️", "⌚", "📷", "📹", "🎥",
                "📺", "📻", "🍕", "🍔", "🍟", "🌭", "🍿", "🥓", "🥚", "🍳", "🐶",
                "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "💡", "📝", "✓", "✗",
            ]
        
        results = {}
        for emoji in emoji_list:
            results[emoji] = self._check_char_support(emoji, font_path, font_size)
        
        return results

    def _render_text_to_image(
        self,
        text: str,
        font_size: int = 24,
        font_path: Optional[str] = None,
        padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
        align: str = "left",
    ) -> Optional['Image.Image']:
        """
        Rend du texte en image avec la font et taille spécifiées.
        Pour les emojis, il faut utiliser une font qui les supporte (NotoEmoji, etc.)
        Les accents sont conservés dans les images (comme dans le texte direct maintenant).
        """
        if not PIL_AVAILABLE:
            return None
            
        font = self._load_font(font_size, font_path)
        if not font:
            return None
            
        lines = text.split("\n")

        # Calculer les dimensions avec un espacement entre lignes
        line_spacing = int(font_size * 0.35)  # 35% de la taille de font (augmenté pour meilleure lisibilité)
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
    ) -> None:
        """Print text as image (supports emojis and accents)."""
        img = self._render_text_to_image(
            text=text,
            font_size=font_size,
            font_path=font_path,
            padding=padding,
            align=align,
        )
        if img:
            self.print_image(img)
            self.lf(1)

    # ------------- IMPRESSION D'IMAGE (GS v 0) ------------------------

    def print_image(self, img: 'Image.Image') -> None:
        """Print PIL Image using GS v 0 command.
        
        Optimisé pour les imprimantes thermiques avec :
        - Seuil de binarisation ajustable (par défaut 140 au lieu de 128 pour meilleur contraste)
        - Utilisation de LANCZOS pour meilleure qualité lors du redimensionnement
        - Conversion progressive L -> 1-bit avec seuil optimisé
        """
        if not PIL_AVAILABLE or not self._ser:
            return
            
        w, h = img.size
        if w > self.width_px:
            # Utiliser LANCZOS pour meilleure qualité lors du redimensionnement
            ratio = self.width_px / float(w)
            img = img.resize((self.width_px, int(h * ratio)), Image.LANCZOS)
            w, h = img.size

        if img.mode != "1":
            # Convertir en niveaux de gris d'abord
            img = img.convert("L")
            # Seuil optimisé pour imprimantes thermiques (140 au lieu de 128)
            # Un seuil plus élevé améliore le contraste et réduit les pixels gris indésirables
            threshold = 140
            img = img.point(lambda x: 0 if x < threshold else 255, "1")

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
        self.raw(header + bitmap, description=f"PRINT_IMAGE ({w}x{h}px, {len(bitmap)} bytes)")

    def _load_image(self, image_path: str) -> Optional['Image.Image']:
        """Load and prepare image for printing.
        
        Args:
            image_path: Path to image file (relative to project root or absolute)
            
        Returns:
            PIL Image ready for printing or None if fails
        """
        if not PIL_AVAILABLE:
            return None
        
        try:
            from pathlib import Path
            
            # Try relative path first (from project root)
            project_root = Path(__file__).parent.parent.parent
            full_path = project_root / image_path
            
            # If not found, try absolute path
            if not full_path.exists():
                full_path = Path(image_path)
            
            if not full_path.exists():
                print(f"Warning: Image not found: {image_path}")
                return None
            
            # Load image
            img = Image.open(full_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to fit printer width
            w, h = img.size
            if w > self.width_px:
                ratio = self.width_px / float(w)
                new_size = (self.width_px, int(h * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            # Convert to grayscale then 1-bit (black/white with dithering)
            img = img.convert("L")
            img = img.convert("1")
            
            return img
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None

    # ------------- HELPERS HAUT NIVEAU -------------------------------

    def print_title(
        self,
        text: str,
        font_size: int = 32,
        font_path: Optional[str] = None,
        separator: bool = True,
    ) -> None:
        """Print a title with optional separator."""
        self.print_text_image(
            text=text,
            font_size=font_size,
            font_path=font_path,
            padding=(0, 0, 0, 0),
            align="center",
        )
        if separator:
            self.separator(char="═", width_chars=self.chars_per_line, font_path=font_path)
            self.lf(1)

    def print_boxed_title(
        self,
        text: str,
        font_size: int = 28,
        font_path: Optional[str] = None,
    ) -> None:
        """
        Imprime un titre encadré avec des séparateurs doubles visibles.
        Plus visible que les caractères Unicode de boîte.
        
        Args:
            text: Texte du titre
            font_size: Taille de la font
            font_path: Chemin vers la font (défaut: default_font_path)
        """
        # Séparateur double au-dessus
        self.separator(char="═", width_chars=self.chars_per_line, double=True, font_path=font_path)
        
        # Titre centré
        self.print_text_image(
            text=text,
            font_size=font_size,
            font_path=font_path,
            padding=(0, 0, 0, 0),
            align="center",
        )
        
        # Séparateur double en-dessous
        self.separator(char="═", width_chars=self.chars_per_line, double=True, font_path=font_path)
        self.lf(1)

    def print_paragraph(
        self,
        text: str,
        font_size: int = 20,
        font_path: Optional[str] = None,
        align: str = "left",
    ) -> None:
        """Print a paragraph."""
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
    ) -> None:
        """Print key-value pair."""
        line = f"{key}{sep}{value}"
        if len(line) > self.chars_per_line:
            line = line[:self.chars_per_line]
        self.line(line)

    # ------------- INTERFACE PRINTER (COMPATIBILITÉ) ------------------

    def print_image_file(self, image_path: str) -> bool:
        """Print an image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if successful, False otherwise
        """
        if not self._ser:
            print("Error: Printer not initialized")
            return False
        
        try:
            img = self._load_image(image_path)
            if img:
                self.print_image(img)
                self.lf(1)
                return True
            return False
        except Exception as e:
            print(f"Error printing image: {e}")
            return False

    def _has_emoji(self, text: str) -> bool:
        """Check if text contains emojis.
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains emojis, False otherwise
        """
        import re
        # Pattern pour détecter les emojis (plages Unicode des emojis)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
            "\U0001F680-\U0001F6FF"  # Transport & Map
            "\U0001F1E0-\U0001F1FF"  # Flags
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251"  # Enclosed characters
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002600-\U000026FF"  # Miscellaneous Symbols
            "\U00002700-\U000027BF"  # Dingbats
            "]+"
        )
        return bool(emoji_pattern.search(text))
    
    def _get_emoji_font_path(self) -> Optional[str]:
        """Get the best available emoji font path.
        
        Returns:
            Path to emoji font or None if not found
        """
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        fonts_dir = project_root / "fonts"
        
        emoji_fonts = self._find_emoji_fonts(str(fonts_dir))
        if emoji_fonts:
            return emoji_fonts[0]  # Retourne la première (priorité)
        return None

    def print_text(self, text: str, header_images: Optional[list] = None, bonus_images: Optional[list] = None, city_images: Optional[list] = None) -> bool:
        """Print text using ESC/POS commands (compatibility method).
        
        Détecte automatiquement les emojis dans le texte et utilise la font emoji
        appropriée si nécessaire. Les images bonus sont insérées après la ligne
        contenant "Photo surprise". Les images de ville sont insérées dans la section "VILLE DU JOUR".
        
        Args:
            text: Text to print
            header_images: Optional list of image paths to print before text
            bonus_images: Optional list of image paths to print in bonus section
            city_images: Optional list of image paths to print in city section
            
        Returns:
            True if successful, False otherwise
        """
        if not self._ser:
            print("Error: Printer not initialized")
            return False
        
        try:
            # Réinitialiser l'alignement et l'encodage au début
            self.set_align("left")
            # S'assurer que l'encodage est correct (déjà fait dans _init_printer, mais on le réinitialise)
            self.set_codepage("cp850", try_alternative=False)
            self.set_international("FRANCE")
            
            # Print header images first
            if header_images:
                for img_path in header_images:
                    self.print_image_file(img_path)
                    self.set_align("left")  # Réinitialiser après chaque image
            
            # Parser le texte ligne par ligne pour insérer les images bonus et city au bon moment
            lines = text.split('\n')
            bonus_printed = False
            in_city_section = False
            city_image_inserted = False
            
            for line in lines:
                # Détecter si on entre dans la section ville
                if '🏙️' in line and 'VILLE DU JOUR' in line:
                    in_city_section = True
                
                # Décider si on imprime directement (font interne) ou en image (font custom/emojis)
                has_emoji = self._has_emoji(line)
                
                # Détecter si la ligne contient des caractères Unicode spéciaux (hors ASCII)
                has_special_unicode = False
                if line:
                    try:
                        # Vérifier si la ligne contient des caractères non-ASCII (hors accents français supportés)
                        for char in line:
                            code = ord(char)
                            # ASCII: 0-127, mais on accepte aussi les accents français cp850 (128-255)
                            # Si c'est un caractère Unicode au-delà de 255, c'est spécial
                            if code > 255 and char not in ['\n', '\r', '\t']:
                                has_special_unicode = True
                                break
                    except:
                        pass
                
                # Si pas d'emojis et pas de caractères Unicode spéciaux, utiliser les fonts internes
                # Même si default_font_path est défini, on utilise les fonts internes pour le texte simple
                if not has_emoji and not has_special_unicode:
                    # Imprimer directement avec les fonts internes de l'imprimante
                    self.line(line)
                    self.lf(1)  # Interligne supplémentaire
                else:
                    # Convertir en image (emojis ou caractères spéciaux)
                    font_path = self.default_font_path
                    if has_emoji:
                        # Utiliser la font emoji si disponible
                        emoji_font = self._get_emoji_font_path()
                        if emoji_font:
                            font_path = emoji_font
                    
                    # Convert line to image (handles emojis and special chars)
                    img = self._render_text_to_image(
                        text=line,
                        font_size=20,
                        font_path=font_path,
                        padding=(0, 0, 0, 0),
                        align="left",
                    )
                    
                    if img:
                        # Réinitialiser l'alignement après l'image
                        self.set_align("left")
                        # Print image
                        self.print_image(img)
                        self.lf(1)
                    else:
                        # Fallback: try to print text directly
                        self.line(line)
                        self.lf(1)
                
                # Insérer l'image de ville après le titre de la section ville
                if in_city_section and not city_image_inserted and city_images:
                    for img_path in city_images:
                        self.print_image_file(img_path)
                        self.set_align("left")  # Réinitialiser après chaque image
                    city_image_inserted = True
                
                # Si on trouve "Photo surprise" et qu'on a des images bonus, les imprimer
                if bonus_images and not bonus_printed and 'Photo surprise' in line:
                    for img_path in bonus_images:
                        self.print_image_file(img_path)
                        self.set_align("left")  # Réinitialiser après chaque image
                    bonus_printed = True
            
            # Feed and cut
            self.lf(1)
            self.cut()
            
            return True
        except Exception as e:
            print(f"Error printing: {e}")
            return False
