"""Printer module for Dutch-o-matic."""

from .printer import Printer, get_printer
from .simulator import SimulatorPrinter
from .escpos import EscposPrinter

try:
    from .visual_simulator import VisualSimulatorPrinter
    __all__ = ['Printer', 'get_printer', 'SimulatorPrinter', 'EscposPrinter', 'VisualSimulatorPrinter']
except ImportError:
    __all__ = ['Printer', 'get_printer', 'SimulatorPrinter', 'EscposPrinter']
