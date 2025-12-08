"""State management for printing operations."""

from datetime import datetime
from typing import Optional

from ..storage import StorageInterface


class StateManager:
    """Manages state updates after printing operations."""
    
    def __init__(self, storage: StorageInterface):
        """Initialize with storage interface."""
        self.storage = storage
    
    def print_exercise(self, exercise_id: str) -> bool:
        """Update state after printing an exercise.
        
        Args:
            exercise_id: ID of the printed exercise
        
        Returns:
            True if successful
        """
        try:
            # Update last_exercise_id
            self.storage.update_state('last_exercise_id', exercise_id)
            
            # Increment counters
            state = self.storage.get_state()
            compteur = state.get('compteur_total', 0) + 1
            xp = state.get('xp', 0) + 1
            
            self.storage.update_state('compteur_total', compteur)
            self.storage.update_state('xp', xp)
            
            # Add history entry
            entry = {
                'exercise_id': exercise_id,
                'printed_at': datetime.utcnow().isoformat() + 'Z',
                'with_answers': False
            }
            self.storage.add_history_entry(entry)
            
            return True
        except Exception:
            return False
    
    def print_answers(self, exercise_id: Optional[str] = None) -> bool:
        """Update state after printing answers.
        
        Args:
            exercise_id: ID of exercise (if None, uses last_exercise_id)
        
        Returns:
            True if successful
        """
        try:
            if exercise_id is None:
                state = self.storage.get_state()
                exercise_id = state.get('last_exercise_id')
                if not exercise_id:
                    return False
            
            # Add history entry
            entry = {
                'exercise_id': exercise_id,
                'printed_at': datetime.utcnow().isoformat() + 'Z',
                'with_answers': True
            }
            self.storage.add_history_entry(entry)
            
            return True
        except Exception:
            return False
