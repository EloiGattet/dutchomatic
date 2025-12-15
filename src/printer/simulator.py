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

    def print_text(self, text: str, header_images: Optional[list] = None, bonus_images: Optional[list] = None, city_images: Optional[list] = None) -> bool:
        """Print text to file.
        
        Args:
            text: Text to print
            header_images: Optional list of image paths to print before text
            bonus_images: Optional list of image paths to print in bonus section
            city_images: Optional list of image paths to print in city section
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.output_dir / f'ticket_{timestamp}.txt'
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                # Write header images info
                if header_images:
                    f.write("=== HEADER IMAGES ===\n")
                    for img_path in header_images:
                        f.write(f"[IMAGE: {img_path}]\n")
                    f.write("\n")
                
                # Write text line by line, inserting bonus and city images when needed
                lines = text.split('\n')
                bonus_printed = False
                in_city_section = False
                city_image_inserted = False
                
                for line in lines:
                    # Détecter si on entre dans la section ville
                    if '🏙️' in line and 'VILLE DU JOUR' in line:
                        in_city_section = True
                    
                    f.write(line)
                    f.write('\n')
                    
                    # Insérer l'image de ville après le titre de la section ville
                    if in_city_section and not city_image_inserted and city_images:
                        f.write("=== CITY IMAGES ===\n")
                        for img_path in city_images:
                            f.write(f"[IMAGE: {img_path}]\n")
                        f.write("\n")
                        city_image_inserted = True
                    
                    # Insert bonus images after "Photo surprise" line
                    if bonus_images and not bonus_printed and 'Photo surprise' in line:
                        f.write("=== BONUS IMAGES ===\n")
                        for img_path in bonus_images:
                            f.write(f"[IMAGE: {img_path}]\n")
                        f.write("\n")
                        bonus_printed = True
                
                f.write('\n')
            
            print(f"Simulated print: {filename}")
            if header_images:
                print(f"  Header images: {', '.join(header_images)}")
            if bonus_images:
                print(f"  Bonus images: {', '.join(bonus_images)}")
            if city_images:
                print(f"  City images: {', '.join(city_images)}")
            return True
        except Exception as e:
            print(f"Error in simulator print: {e}")
            return False
