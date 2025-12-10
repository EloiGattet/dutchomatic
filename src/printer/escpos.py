"""ESC/POS printer implementation."""

from typing import Optional

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
    """ESC/POS printer implementation."""

    def __init__(
        self,
        device: str = '/dev/serial0',
        width: int = 58,
        baudrate: int = 9600,
        timeout: int = 1
    ):
        """Initialize ESC/POS printer.
        
        Args:
            device: Device path (serial)
            width: Ticket width in characters
            baudrate: Serial baudrate (default: 9600)
            timeout: Serial timeout in seconds (default: 1)
        """
        super().__init__(width)
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout
        self._printer = None
        self._init_printer()

    def _init_printer(self) -> None:
        """Initialize printer connection."""
        try:
            from escpos.printer import Serial
            
            self._printer = Serial(
                devfile=self.device,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=self.timeout
            )
            
            # Patch du profil pour éviter le warning "media.width.pixel"
            # et permettre le centrage automatique
            # Documentation: voir documents/rapport_essais_impression.md
            try:
                if hasattr(self._printer, "profile") and hasattr(self._printer.profile, "media"):
                    self._printer.profile.media.setdefault("width", {})
                    self._printer.profile.media["width"]["pixels"] = 384  # 8 dots/mm × 48mm
                    self._printer.profile.media["width"]["mm"] = 48
            except Exception:
                pass  # Silently fail if patch doesn't work
            
            # Appliquer les paramètres optimaux d'impression
            # (basés sur les tests - voir rapport_essais_impression.md)
            try:
                # ESC 7 : heating parameters (optimal: n1=7, n2=80, n3=2)
                self._printer._raw(b'\x1B\x37' + bytes([7, 80, 2]))
                # DC2 # : density & breaktime (optimal: density=15, breaktime=0)
                n = (0 << 5) + 15  # breaktime=0, density=15
                self._printer._raw(b'\x12\x23' + bytes([n]))
            except Exception:
                pass  # Silently fail if settings don't work
            
            print(f"✓ ESC/POS printer connected via serial: {self.device}")
        except ImportError:
            print("Warning: python-escpos not available")
            self._printer = None
        except Exception as e:
            print(f"Warning: Could not initialize ESC/POS printer: {e}")
            self._printer = None

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
            
            # Resize to fit printer width (384px for 58mm thermal)
            MAX_WIDTH = 384
            w, h = img.size
            if w > MAX_WIDTH:
                ratio = MAX_WIDTH / float(w)
                new_size = (MAX_WIDTH, int(h * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            # Convert to grayscale then 1-bit (black/white with dithering)
            img = img.convert("L")
            img = img.convert("1")
            
            return img
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def _text_to_image(self, text: str) -> Optional['Image.Image']:
        """Convert text to image for printing.
        
        Args:
            text: Text to convert
            
        Returns:
            PIL Image or None if conversion fails
        """
        if not PIL_AVAILABLE:
            return None
            
        try:
            MAX_WIDTH = 384  # 58mm thermal printer width
            font_size = 20
            padding = 4
            
            # Try to load a monospace font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Split text into lines
            lines = text.split('\n')
            
            # Calculate dimensions
            line_height = int(font_size * 1.3)
            max_line_width = 0
            
            for line in lines:
                if line.strip():
                    bbox = font.getbbox(line)
                    line_width = bbox[2] - bbox[0]
                    max_line_width = max(max_line_width, line_width)
            
            # Ensure width doesn't exceed MAX_WIDTH
            img_width = min(max_line_width + 2 * padding, MAX_WIDTH)
            img_height = len(lines) * line_height + 2 * padding
            
            # Create image
            img = Image.new("L", (img_width, img_height), 255)  # White background
            draw = ImageDraw.Draw(img)
            
            # Draw text line by line
            y = padding
            for line in lines:
                if line.strip():
                    draw.text((padding, y), line, font=font, fill=0)  # Black text
                y += line_height
            
            # Resize if needed
            if img_width > MAX_WIDTH:
                ratio = MAX_WIDTH / float(img_width)
                new_size = (MAX_WIDTH, int(img_height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            # Convert to 1-bit (black/white with dithering)
            img = img.convert("1")
            
            return img
            
        except Exception as e:
            print(f"Error converting text to image: {e}")
            return None

    def print_image(self, image_path: str) -> bool:
        """Print an image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if successful, False otherwise
        """
        if self._printer is None:
            print("Error: Printer not initialized")
            return False
        
        try:
            img = self._load_image(image_path)
            if img:
                self._printer.image(img)
                self._printer.text("\n")
                return True
            return False
        except Exception as e:
            print(f"Error printing image: {e}")
            return False

    def print_text(self, text: str, header_images: Optional[list] = None) -> bool:
        """Print text using ESC/POS commands.
        
        Args:
            text: Text to print
            header_images: Optional list of image paths to print before text
            
        Returns:
            True if successful, False otherwise
        """
        if self._printer is None:
            print("Error: Printer not initialized")
            return False
        
        try:
            # Print header images first
            if header_images:
                for img_path in header_images:
                    self.print_image(img_path)
            
            # Convert text to image (handles emojis and special chars)
            img = self._text_to_image(text)
            
            if img:
                # Print image
                self._printer.image(img)
                self._printer.text("\n")
            else:
                # Fallback: try to print text directly with codepage
                try:
                    self._printer.charcode('CP858')  # European codepage
                except:
                    pass
                self._printer.text(text)
            
            # Feed and cut
            self._printer.text("\n")
            self._printer.cut()
            
            return True
        except Exception as e:
            print(f"Error printing: {e}")
            return False

    def close(self) -> None:
        """Close printer connection."""
        if self._printer:
            try:
                self._printer.close()
            except:
                pass
