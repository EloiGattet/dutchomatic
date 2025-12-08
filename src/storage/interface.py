"""Abstract storage interface for Dutch-o-matic.

This interface allows switching between JSON and SQLite backends
without changing the rest of the application code.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageInterface(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def get_exercise(self, exercise_id: str) -> Optional[Dict[str, Any]]:
        """Get a single exercise by ID."""
        pass

    @abstractmethod
    def get_all_exercises(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all exercises, optionally filtered by niveau, type, tags."""
        pass

    @abstractmethod
    def add_exercise(self, exercise: Dict[str, Any]) -> str:
        """Add a new exercise. Returns the exercise ID."""
        pass

    @abstractmethod
    def update_exercise(self, exercise_id: str, exercise: Dict[str, Any]) -> bool:
        """Update an existing exercise. Returns True if successful."""
        pass

    @abstractmethod
    def delete_exercise(self, exercise_id: str) -> bool:
        """Delete an exercise. Returns True if successful."""
        pass

    @abstractmethod
    def get_daily(self, daily_id: str) -> Optional[Dict[str, Any]]:
        """Get a single daily item by ID."""
        pass

    @abstractmethod
    def get_all_daily(self, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all daily items, optionally filtered by kind."""
        pass

    @abstractmethod
    def add_daily(self, daily: Dict[str, Any]) -> str:
        """Add a new daily item. Returns the daily ID."""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get the current state (history, last_exercise_id, niveau_actuel, xp, compteur_total)."""
        pass

    @abstractmethod
    def update_state(self, key: str, value: Any) -> bool:
        """Update a state key. Returns True if successful."""
        pass

    @abstractmethod
    def add_history_entry(self, entry: Dict[str, Any]) -> bool:
        """Add an entry to the history. Returns True if successful."""
        pass
