"""Daily data model."""

from typing import Any, Dict


class Daily:
    """Daily item model (expression, fact, quote) with validation."""

    REQUIRED_FIELDS = ['id', 'kind', 'nl', 'fr']
    VALID_KINDS = ['expression', 'fact', 'quote']

    def __init__(self, data: Dict[str, Any]):
        """Initialize daily from dict."""
        self.data = data
        self._validate()

    def _validate(self) -> None:
        """Validate daily data."""
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                raise ValueError(f"Missing required field: {field}")

        # Validate kind
        if self.data['kind'] not in self.VALID_KINDS:
            raise ValueError(f"Invalid kind: {self.data['kind']}. Must be one of {self.VALID_KINDS}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.data.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Daily':
        """Create Daily from dictionary."""
        return cls(data)
