"""Exercise data model."""

from typing import Any, Dict, List, Optional


class Exercise:
    """Exercise model with validation."""

    REQUIRED_FIELDS = ['id', 'niveau', 'type', 'title']
    VALID_TYPES = ['vocabulary', 'grammar', 'reading', 'quiz']
    VALID_NIVEAUX = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

    def __init__(self, data: Dict[str, Any]):
        """Initialize exercise from dict."""
        self.data = data
        self._validate()

    def _validate(self) -> None:
        """Validate exercise data."""
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                raise ValueError(f"Missing required field: {field}")

        # Validate type
        if self.data['type'] not in self.VALID_TYPES:
            raise ValueError(f"Invalid type: {self.data['type']}. Must be one of {self.VALID_TYPES}")

        # Validate niveau
        if self.data['niveau'] not in self.VALID_NIVEAUX:
            raise ValueError(f"Invalid niveau: {self.data['niveau']}. Must be one of {self.VALID_NIVEAUX}")

        # Validate items if present
        if 'items' in self.data and not isinstance(self.data['items'], list):
            raise ValueError("items must be a list")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.data.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Exercise':
        """Create Exercise from dictionary."""
        return cls(data)
