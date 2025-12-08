"""Core logic for Dutch-o-matic."""

from .selector import select_exercise
from .daily_selector import select_daily
from .formatter import format_exercise, format_answers
from .state_manager import StateManager

__all__ = [
    'select_exercise',
    'select_daily',
    'format_exercise',
    'format_answers',
    'StateManager'
]
