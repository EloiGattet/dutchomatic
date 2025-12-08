"""ESC/POS printer implementation."""

from typing import Optional

from .printer import Printer


class EscposPrinter(Printer):
    """ESC/POS printer implementation."""

    def __init__(self, device: str = '/dev/usb/lp0', width: int = 58):
        """Initialize ESC/POS printer.
        
        Args:
            device: Device path (USB, serial, or network)
            width: Ticket width in characters
        """
        super().__init__(width)
        self.device = device
        self._printer = None
        self._init_printer()

    def _init_printer(self) -> None:
        """Initialize printer connection."""
        try:
            # Try to import python-escpos
            try:
                from escpos.printer import Usb, Serial, Network
                from escpos.exceptions import DeviceNotFoundError
                
                # Determine connection type from device path
                if self.device.startswith('/dev/usb') or self.device.startswith('/dev/tty'):
                    # USB or Serial
                    if 'usb' in self.device:
                        # USB printer (vendor_id:product_id format or device path)
                        # For now, try to open as file
                        self._printer = None  # Will use fallback
                    else:
                        # Serial
                        try:
                            self._printer = Serial(self.device)
                        except DeviceNotFoundError:
                            self._printer = None
                elif self.device.startswith('tcp://') or ':' in self.device:
                    # Network printer
                    try:
                        host, port = self.device.replace('tcp://', '').split(':')
                        self._printer = Network(host, port=int(port))
                    except Exception:
                        self._printer = None
                else:
                    self._printer = None
                    
            except ImportError:
                # python-escpos not available, use fallback
                self._printer = None
                
        except Exception as e:
            print(f"Warning: Could not initialize ESC/POS printer: {e}")
            self._printer = None

    def print_text(self, text: str) -> bool:
        """Print text using ESC/POS commands.
        
        Args:
            text: Text to print
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self._printer is not None:
                # Use python-escpos library
                self._printer.text(text)
                self._printer.cut()
                return True
            else:
                # Fallback: write to device file directly
                return self._print_fallback(text)
        except Exception as e:
            print(f"Error printing with ESC/POS: {e}")
            # Try fallback
            return self._print_fallback(text)

    def _print_fallback(self, text: str) -> bool:
        """Fallback printing method (direct file write).
        
        Args:
            text: Text to print
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Basic ESC/POS commands
            escpos_commands = []
            
            # Reset printer
            escpos_commands.append(b'\x1B\x40')
            
            # Convert text to bytes and add ESC/POS formatting
            for line in text.split('\n'):
                # Add line feed
                escpos_commands.append(line.encode('utf-8', errors='replace'))
                escpos_commands.append(b'\n')
            
            # Cut paper
            escpos_commands.append(b'\x1D\x56\x00')
            
            # Write to device
            with open(self.device, 'wb') as f:
                f.write(b''.join(escpos_commands))
            
            return True
        except Exception as e:
            print(f"Error in fallback print: {e}")
            return False
