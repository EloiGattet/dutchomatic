"""State data model."""

from typing import Any, Dict, List, Optional


class State:
    """State model with default values."""

    DEFAULT_STATE = {
        'history': [],
        'last_exercise_id': None,
        'niveau_actuel': 'A1',
        'xp': 0,
        'compteur_total': 0
    }

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """Initialize state from dict or use defaults."""
        if data is None:
            data = self.DEFAULT_STATE.copy()
        self.data = data
        self._normalize()

    def _normalize(self) -> None:
        """Ensure all required fields are present with defaults."""
        for key, default_value in self.DEFAULT_STATE.items():
            if key not in self.data:
                self.data[key] = default_value

        # Ensure history is a list
        if not isinstance(self.data.get('history'), list):
            self.data['history'] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.data.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'State':
        """Create State from dictionary."""
        return cls(data)
