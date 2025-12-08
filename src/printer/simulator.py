"""Simulator printer for testing without physical printer."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .printer import Printer


class SimulatorPrinter(Printer):
    """Printer simulator that writes to files."""

    def __init__(self, output_dir: str = 'output', width: int = 58):
        """Initialize simulator printer.
        
        Args:
            output_dir: Directory to write output files
            width: Ticket width in characters
        """
        super().__init__(width)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def print_text(self, text: str) -> bool:
        """Print text to file.
        
        Args:
            text: Text to print
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.output_dir / f'ticket_{timestamp}.txt'
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
                f.write('\n')
            
            print(f"Simulated print: {filename}")
            return True
        except Exception as e:
            print(f"Error in simulator print: {e}")
            return False
