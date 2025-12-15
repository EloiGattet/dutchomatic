"""State management for printing operations."""

from datetime import datetime
from typing import Optional

from ..storage import StorageInterface


class StateManager:
    """Manages state updates after printing operations."""
    
    def __init__(self, storage: StorageInterface):
        """Initialize with storage interface."""
        self.storage = storage
    
    def print_exercise(self, exercise_id: str, bonus_images: Optional[list] = None, instagram_account: Optional[str] = None) -> bool:
        """Update state after printing an exercise.
        
        Args:
            exercise_id: ID of the printed exercise
            bonus_images: Optional list of bonus image paths that were printed
            instagram_account: Optional Instagram category name that was printed
        
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
            
            # Track printed photos
            if bonus_images:
                printed_photos = state.get('printed_photos', [])
                for photo_path in bonus_images:
                    if photo_path not in printed_photos:
                        printed_photos.append(photo_path)
                self.storage.update_state('printed_photos', printed_photos)
            
            # Track printed Instagram accounts
            if instagram_account:
                printed_accounts = state.get('printed_instagram_accounts', [])
                if instagram_account not in printed_accounts:
                    printed_accounts.append(instagram_account)
                self.storage.update_state('printed_instagram_accounts', printed_accounts)
            
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
