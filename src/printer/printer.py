"""Abstract printer interface and factory."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

from ..core import format_exercise, format_answers
from ..core.state_manager import StateManager
from ..storage import StorageInterface


class Printer(ABC):
    """Abstract base class for printers."""

    def __init__(self, width: int = 58):
        """Initialize printer with ticket width."""
        self.width = width

    @abstractmethod
    def print_text(self, text: str, header_images: Optional[list] = None, bonus_images: Optional[list] = None, city_images: Optional[list] = None) -> bool:
        """Print raw text.
        
        Args:
            text: Text to print
            header_images: Optional list of image paths to print before text
            bonus_images: Optional list of image paths to print in bonus section
            city_images: Optional list of image paths to print in city section
            
        Returns:
            True if successful, False otherwise
        """
        pass

    def print_exercise(
        self,
        exercise: Dict,
        daily: Optional[Dict] = None,
        city: Optional[Dict] = None,
        course: Optional[Dict] = None,
        storage: Optional[StorageInterface] = None,
        state_manager: Optional[StateManager] = None
    ) -> bool:
        """Print an exercise with optional daily bonus, city, and course.
        
        Args:
            exercise: Exercise dict
            daily: Optional daily item dict
            city: Optional city dict for "ville du jour"
            course: Optional course dict for "cours du jour"
            storage: Storage interface (required for state update)
            state_manager: StateManager instance (required for state update)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get state for countdown and footer
            state = None
            if storage:
                state = storage.get_state()
            
            # Format exercise
            formatted_text, header_images, bonus_images, city_images, instagram_category = format_exercise(exercise, daily, city, course, state=state)
            
            # Print
            success = self.print_text(formatted_text, header_images=header_images, bonus_images=bonus_images, city_images=city_images)
            
            # Update state if storage and state_manager provided
            if success and storage and state_manager:
                state_manager.print_exercise(exercise.get('id'), bonus_images=bonus_images, instagram_account=instagram_category)
            
            return success
        except Exception as e:
            print(f"Error printing exercise: {e}")
            return False

    def print_answers(
        self,
        exercise_id: str,
        storage: StorageInterface,
        state_manager: Optional[StateManager] = None
    ) -> bool:
        """Print answers for an exercise.
        
        Args:
            exercise_id: ID of the exercise
            storage: Storage interface (required to load exercise)
            state_manager: StateManager instance (optional, for state update)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load exercise
            exercise = storage.get_exercise(exercise_id)
            if not exercise:
                print(f"Exercise {exercise_id} not found")
                return False
            
            # Format answers
            formatted_text, header_images = format_answers(exercise)
            
            # Print
            success = self.print_text(formatted_text, header_images=header_images)
            
            # Update state if state_manager provided
            if success and state_manager:
                state_manager.print_answers(exercise_id)
            
            return success
        except Exception as e:
            print(f"Error printing answers: {e}")
            return False


def get_printer(config_path: Optional[str] = None) -> Printer:
    """Factory function to create printer from config.
    
    Args:
        config_path: Path to printer config JSON (default: config/printer.json)
        
    Returns:
        Printer instance
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / 'config' / 'printer.json'
    
    # Default config
    config = {
        'type': 'simulator',
        'output_dir': 'output',
        'device': '/dev/usb/lp0',
        'width': 58
    }
    
    # Load config if exists
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load printer config: {e}")
    
    # Create printer based on type
    printer_type = config.get('type', 'simulator')
    width = config.get('width', 58)
    
    if printer_type == 'simulator':
        from .simulator import SimulatorPrinter
        output_dir = config.get('output_dir', 'output')
        return SimulatorPrinter(output_dir=output_dir, width=width)
    elif printer_type == 'visual_simulator':
        from .visual_simulator import VisualSimulatorPrinter
        width_px = config.get('width_px', 384)
        codepage = config.get('codepage', 'gb18030')
        international = config.get('international', 'FRANCE')
        default_encoding = config.get('default_encoding', 'gb18030')
        default_font_path = config.get('default_font_path')
        if not default_font_path:
            project_root = Path(__file__).parent.parent.parent
            font_path = project_root / 'fonts' / 'Roboto-Bold.ttf'
            if font_path.exists():
                default_font_path = str(font_path)
            else:
                default_font_path = None
        return VisualSimulatorPrinter(
            device='/dev/null',
            width=width,
            baudrate=9600,
            timeout=1,
            width_px=width_px,
            default_encoding=default_encoding,
            default_font_path=default_font_path,
            codepage=codepage,
            international=international
        )
    elif printer_type == 'escpos':
        from .escpos import EscposPrinter
        
        device = config.get('device', '/dev/ttyUSB0')
        baudrate = config.get('baudrate', 9600)
        timeout = config.get('timeout', 1)
        width_px = config.get('width_px', 384)  # 384px pour 58mm
        codepage = config.get('codepage', 'gb18030')
        international = config.get('international', 'FRANCE')
        default_encoding = config.get('default_encoding', 'gb18030')
        
        # Chercher la font par défaut (Roboto-Bold)
        default_font_path = config.get('default_font_path')
        if not default_font_path:
            project_root = Path(__file__).parent.parent.parent
            font_path = project_root / 'fonts' / 'Roboto-Bold.ttf'
            if font_path.exists():
                default_font_path = str(font_path)
            else:
                default_font_path = None
        
        return EscposPrinter(
            device=device,
            width=width,
            baudrate=baudrate,
            timeout=timeout,
            width_px=width_px,
            default_encoding=default_encoding,
            default_font_path=default_font_path,
            codepage=codepage,
            international=international
        )
    else:
        raise ValueError(f"Unknown printer type: {printer_type}")
